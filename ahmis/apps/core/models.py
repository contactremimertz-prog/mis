import hashlib
import json
from datetime import timezone as dt_timezone

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone


class TrackedModel(models.Model):
    """Base de tous les enregistrements métier : qui a créé / modifié, et quand.

    Le détail champ par champ des modifications est conservé dans AuditLog.
    """

    created_at = models.DateTimeField("créé le", auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="créé par", null=True, blank=True,
        on_delete=models.PROTECT, related_name="+", editable=False,
    )
    updated_at = models.DateTimeField("modifié le", auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="modifié par", null=True, blank=True,
        on_delete=models.PROTECT, related_name="+", editable=False,
    )

    # Les enregistrements de navigabilité ne sont jamais supprimés physiquement.
    ahmis_no_delete = True

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        from .middleware import get_current_user

        user = get_current_user()
        if user is not None:
            if self._state.adding and not self.created_by_id:
                self.created_by = user
            self.updated_by = user
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if getattr(self, "ahmis_no_delete", False):
            raise ValidationError(
                "Suppression interdite : cet enregistrement doit être conservé "
                "(utilisez le statut « annulé » ou « retiré »)."
            )
        return super().delete(*args, **kwargs)


class AuditLog(models.Model):
    ACTIONS = [("create", "Création"), ("update", "Modification"), ("delete", "Suppression")]

    timestamp = models.DateTimeField("horodatage", default=timezone.now, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, verbose_name="utilisateur")
    username = models.CharField("identifiant", max_length=150, blank=True)
    action = models.CharField(max_length=10, choices=ACTIONS)
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.CharField(max_length=64, db_index=True)
    object_repr = models.CharField("objet", max_length=255)
    changes = models.TextField("modifications (JSON)", blank=True)

    class Meta:
        ordering = ["-timestamp", "-id"]
        verbose_name = "entrée d'audit"
        verbose_name_plural = "journal d'audit"
        indexes = [models.Index(fields=["content_type", "object_id"])]

    def __str__(self):
        return f"{self.timestamp:%d/%m/%Y %H:%M} {self.username} {self.get_action_display()} {self.object_repr}"

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("Le journal d'audit est en écriture seule.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Le journal d'audit ne peut pas être supprimé.")

    @property
    def changes_list(self):
        try:
            data = json.loads(self.changes or "{}")
        except ValueError:
            return []
        return [(k, v.get("old"), v.get("new")) for k, v in data.items()]


class SignatureRecord(models.Model):
    """Signature électronique : utilisateur authentifié + ressaisie du mot de passe,
    horodatage, déclaration signée et empreinte SHA-256 pour détecter toute altération."""

    ACTIONS = [
        ("perform", "Exécution"),
        ("inspect", "Inspection / contrôle indépendant"),
        ("crs", "Certificat de remise en service (CRS)"),
        ("defer", "Report de défaut"),
        ("extend", "Prorogation de report (RIE)"),
        ("scrap", "Mise au rebut / mutilation"),
        ("accept_part", "Réception pièce"),
        ("camo_review", "Revue CAMO"),
        ("step", "Étape de task card"),
        ("finding_close", "Clôture de constat d'audit"),
        ("doc_approve", "Approbation de révision documentaire"),
    ]

    signed_at = models.DateTimeField("signé le", default=timezone.now)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name="utilisateur")
    signer_name = models.CharField("nom du signataire", max_length=150)
    signer_licence = models.CharField("licence / autorisation", max_length=150, blank=True)
    action = models.CharField(max_length=20, choices=ACTIONS)
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.CharField(max_length=64, db_index=True)
    object_repr = models.CharField("objet", max_length=255)
    statement = models.TextField("déclaration signée")
    digest = models.CharField("empreinte SHA-256", max_length=64, editable=False)

    class Meta:
        ordering = ["-signed_at"]
        verbose_name = "signature électronique"
        verbose_name_plural = "signatures électroniques"

    def __str__(self):
        return f"{self.get_action_display()} – {self.signer_name} – {self.signed_at:%d/%m/%Y %H:%M}"

    def compute_digest(self):
        # Identifiants stables (indépendants des clés techniques du SGBD) pour que
        # l'empreinte reste vérifiable après une migration vers une autre base.
        ct = ContentType.objects.get_for_id(self.content_type_id)
        payload = "|".join([
            self.user.get_username(), self.signer_name, self.signer_licence, self.action,
            f"{ct.app_label}.{ct.model}", str(self.object_id), self.statement,
            self.signed_at.astimezone(dt_timezone.utc).replace(microsecond=0).isoformat(),
        ])
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @property
    def is_intact(self):
        return self.digest == self.compute_digest()

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("Une signature ne peut pas être modifiée.")
        self.signed_at = self.signed_at.replace(microsecond=0)  # précision : la seconde
        self.digest = self.compute_digest()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Une signature ne peut pas être supprimée.")

    @classmethod
    def sign(cls, user, obj, action, statement, licence=""):
        from apps.part145.models import Staff  # import tardif

        staff = Staff.objects.filter(user=user).first()
        name = staff.full_name if staff else (user.get_full_name() or user.username)
        if not licence and staff:
            licence = staff.licence_summary
        return cls.objects.create(
            user=user, signer_name=name, signer_licence=licence, action=action,
            content_type=ContentType.objects.get_for_model(obj), object_id=str(obj.pk),
            object_repr=str(obj)[:255], statement=statement,
        )

    @classmethod
    def for_object(cls, obj):
        return cls.objects.filter(
            content_type=ContentType.objects.get_for_model(obj), object_id=str(obj.pk)
        )


class Sequence(models.Model):
    """Numérotation séquentielle annuelle (WP-2026-0001, TC-2026-00001...)."""

    prefix = models.CharField(max_length=10)
    year = models.PositiveIntegerField()
    last_value = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [("prefix", "year")]

    @classmethod
    def next(cls, prefix, width=4):
        year = timezone.localdate().year
        with transaction.atomic():
            seq, _ = cls.objects.select_for_update().get_or_create(prefix=prefix, year=year)
            seq.last_value += 1
            seq.save(update_fields=["last_value"])
        return f"{prefix}-{year}-{seq.last_value:0{width}d}"


class ExternalIdentity(models.Model):
    """Lien entre un compte AHMIS et un annuaire d'entreprise (Active Directory, SSO OpenID Connect)."""

    PROVIDERS = [("ldap", "Active Directory (LDAP)"), ("oidc", "SSO OpenID Connect")]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="external_identities", verbose_name="utilisateur")
    provider = models.CharField("fournisseur", max_length=10, choices=PROVIDERS)
    subject = models.CharField("identifiant externe", max_length=255, help_text="objectGUID AD, ou émetteur|sub OpenID Connect")
    login_name = models.CharField("identifiant de connexion", max_length=255, blank=True, help_text="sAMAccountName ou UPN, utilisé pour revérifier le mot de passe à la signature")
    groups = models.TextField("groupes reçus à la dernière connexion", blank=True)
    first_seen = models.DateTimeField("première connexion", default=timezone.now)
    last_login = models.DateTimeField("dernière connexion", default=timezone.now)

    class Meta:
        unique_together = [("provider", "subject")]
        verbose_name = "identité d'entreprise"
        verbose_name_plural = "identités d'entreprise (AD / SSO)"

    def __str__(self):
        return f"{self.get_provider_display()} – {self.login_name or self.subject}"


class SignaturePin(models.Model):
    """Code de signature personnel : pour les comptes SSO dont le mot de passe n'est pas vérifiable par AHMIS."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="signature_pin")
    pin_hash = models.CharField(max_length=255)
    updated_at = models.DateTimeField(auto_now=True)
    failed_attempts = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = "code de signature"
        verbose_name_plural = "codes de signature"

    def set_pin(self, raw):
        from django.contrib.auth.hashers import make_password

        self.pin_hash = make_password(raw)
        self.failed_attempts = 0

    def check_pin(self, raw):
        from django.contrib.auth.hashers import check_password

        return check_password(raw, self.pin_hash)
