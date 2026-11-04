"""Audit trail automatique : chaque création / modification d'un TrackedModel
est journalisée champ par champ (ancienne et nouvelle valeur, utilisateur, horodatage)."""
import json

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import post_delete, post_save, pre_save

from .middleware import get_current_user
from .models import AuditLog, TrackedModel

IGNORED = {"created_at", "created_by", "updated_at", "updated_by"}


def _value(instance, field):
    value = field.value_from_object(instance)
    if field.is_relation and value is not None:
        try:
            related = getattr(instance, field.name)
            return f"{related} (#{value})"
        except Exception:  # objet lié introuvable
            return f"#{value}"
    if field.choices and value not in (None, ""):
        return f"{dict(field.flatchoices).get(value, value)}"
    if value is None:
        return None
    if isinstance(field, models.FileField):
        return getattr(value, "name", None) or None
    return str(value)


def _snapshot(instance):
    # Libellés enregistrés dans la langue de référence (français), quelle que soit la langue de
    # l'utilisateur : le journal reste homogène ; l'écran le traduit à l'affichage.
    from django.conf import settings
    from django.utils import translation

    data = {}
    with translation.override(settings.LANGUAGE_CODE):
        for field in instance._meta.concrete_fields:
            if field.name in IGNORED or field.primary_key:
                continue
            data[str(field.verbose_name)] = _value(instance, field)
    return data


def _on_pre_save(sender, instance, **kwargs):
    if not issubclass(sender, TrackedModel) or instance._state.adding or not instance.pk:
        instance._ahmis_old = None
        return
    try:
        old = sender.objects.get(pk=instance.pk)
        instance._ahmis_old = _snapshot(old)
    except sender.DoesNotExist:
        instance._ahmis_old = None


def _log(instance, action, changes):
    user = get_current_user()
    AuditLog.objects.create(
        user=user,
        username=user.username if user else "système",
        action=action,
        content_type=ContentType.objects.get_for_model(instance.__class__),
        object_id=str(instance.pk),
        object_repr=str(instance)[:255],
        changes=json.dumps(changes, ensure_ascii=False, default=str),
    )


def _on_post_save(sender, instance, created, raw=False, **kwargs):
    if raw or not issubclass(sender, TrackedModel):
        return
    new = _snapshot(instance)
    if created:
        changes = {k: {"old": None, "new": v} for k, v in new.items() if v not in (None, "")}
        _log(instance, "create", changes)
        return
    old = getattr(instance, "_ahmis_old", None) or {}
    changes = {k: {"old": old.get(k), "new": v} for k, v in new.items() if old.get(k) != v}
    if changes:
        _log(instance, "update", changes)


def _on_post_delete(sender, instance, **kwargs):
    if issubclass(sender, TrackedModel):
        _log(instance, "delete", {k: {"old": v, "new": None} for k, v in _snapshot(instance).items()})


def connect():
    pre_save.connect(_on_pre_save, dispatch_uid="ahmis_audit_pre")
    post_save.connect(_on_post_save, dispatch_uid="ahmis_audit_post")
    post_delete.connect(_on_post_delete, dispatch_uid="ahmis_audit_del")
