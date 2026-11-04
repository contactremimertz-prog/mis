from datetime import date, datetime
from decimal import Decimal

from django import template
from django.db.models import Model
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()

STATUS_CLASSES = {
    # génériques
    "overdue": "bad", "tolerance": "tolerance", "due_soon": "warn", "ok": "ok",
    # aéronefs
    "active": "ok", "maintenance": "warn", "aog": "bad", "stored": "", "retired": "",
    # composants / stock
    "installed": "info", "serviceable": "ok", "reserved": "info", "unserviceable": "bad",
    "quarantine": "bad", "repair": "warn", "scrapped": "", "expired": "bad",
    # 145
    "draft": "", "planned": "info", "in_progress": "warn", "completed": "ok", "released": "ok",
    "cancelled": "", "open": "info", "performed": "warn", "closed": "ok", "deferred": "warn",
    "rectified": "ok",
    # AD
    "to_assess": "bad", "not_applicable": "", "recurring": "info", "complied": "ok",
    # demandes
    "requested": "warn", "issued": "ok", "returned": "",
    # outillage
    "embodied": "ok", "removed": "", "calibration": "warn", "available": "ok", "checked_out": "info",
    "aog_prio": "bad", "urgent": "warn", "routine": "",
    # comptes rendus d'événements
    "submitted": "warn", "follow_up": "info", "not_reportable": "",
}


@register.filter
def status_class(value):
    return STATUS_CLASSES.get(value, "")


@register.simple_tag
def badge(obj, field="status"):
    value = getattr(obj, field)
    label = getattr(obj, f"get_{field}_display")()
    return format_html('<span class="badge {}">{}</span>', STATUS_CLASSES.get(value, ""), label)


@register.simple_tag
def status_badge(value, label):
    return format_html('<span class="badge {}">{}</span>', STATUS_CLASSES.get(value, ""), label)


def fmt(value):
    if value is None or value == "":
        return "—"
    if isinstance(value, bool):
        return "Oui" if value else "Non"
    if isinstance(value, datetime):
        return timezone.localtime(value).strftime("%d/%m/%Y %H:%M")
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, Decimal):
        return f"{value.normalize():f}" if value == value.to_integral() else f"{value:.2f}".rstrip("0").rstrip(".")
    return value


@register.filter(name="fmt")
def fmt_filter(value):
    return fmt(value)


@register.filter
def hours(value):
    """Heures décimales affichées avec 1 décimale."""
    if value is None or value == "":
        return "—"
    return f"{Decimal(value):.1f}"


@register.simple_tag
def cell(obj, accessor):
    """Valeur d'une colonne de liste : chemin pointé, *_display automatique pour les choix."""
    value = obj
    parts = accessor.split(".")
    for i, part in enumerate(parts):
        if value is None:
            break
        if i == len(parts) - 1 and isinstance(value, Model):
            try:
                f = value._meta.get_field(part)
                if f.choices and part == "status":
                    return status_badge(getattr(value, part), getattr(value, f"get_{part}_display")())
                if f.choices:
                    return fmt(getattr(value, f"get_{part}_display")())
                if f.many_to_many:
                    return ", ".join(str(o) for o in getattr(value, part).all()) or "—"
            except Exception:
                pass
        value = getattr(value, part, None)
        if callable(value) and not isinstance(value, Model) and not hasattr(value, "get_queryset"):
            value = value()
    return fmt(value)


@register.simple_tag(takes_context=True)
def qs_replace(context, **kwargs):
    params = context["request"].GET.copy()
    for k, v in kwargs.items():
        if v is None:
            params.pop(k, None)
        else:
            params[k] = v
    return params.urlencode()


@register.inclusion_tag("core/_field.html")
def field(bound_field, wide=False):
    return {"f": bound_field, "wide": wide}


@register.inclusion_tag("core/_signature.html")
def signature(sig, label=""):
    return {"sig": sig, "label": label}


@register.filter
def get_item(d, key):
    return d.get(key) if d else None


@register.filter
def has_group(user, name):
    return user.is_superuser or user.groups.filter(name=name).exists()


@register.filter
def remaining_class(value):
    if value is None:
        return ""
    return "neg" if value < 0 else ""


@register.simple_tag
def yesno_badge(value, yes="Oui", no="Non"):
    return mark_safe(f'<span class="badge {"ok" if value else ""}">{yes if value else no}</span>')


@register.filter
def absval(value):
    try:
        return abs(value)
    except TypeError:
        return value


@register.filter
def pct_used(limit_row):
    """Pourcentage consommé d'une limite (pour les barres de potentiel)."""
    try:
        lim = Decimal(str(limit_row["limit"]))
        used = Decimal(str(limit_row["used"]))
        return max(0, min(100, int(used * 100 / lim))) if lim else 0
    except Exception:
        return 0
