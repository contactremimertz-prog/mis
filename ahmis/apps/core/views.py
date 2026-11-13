from datetime import timedelta
from pathlib import Path

import markdown
from django.conf import settings
from django.contrib.auth import views as auth_views
from django.contrib import messages
from django.contrib.auth.decorators import login_not_required, permission_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.camo.models import DirectiveApplicability
from apps.camo.services import fleet_due_list
from apps.fleet.models import Aircraft, Component, PartNumber
from apps.logistics.models import PartRequest, StockItem, Tool
from apps.part145.models import Authorization, Defect, TaskCard, WorkPackage

from .models import AuditLog, SignatureRecord
from django.utils.translation import get_language, gettext

DOCS_DIR = Path(settings.BASE_DIR) / "docs" / "tutoriels"


class LoginView(auth_views.LoginView):
    def post(self, request, *args, **kwargs):
        from . import throttle

        username = (request.POST.get("username") or "").strip().lower()[:150]
        keys = [f"login:user:{username}", f"login:ip:{throttle.client_ip(request)}"]
        if any(throttle.is_locked(k) for k in keys):
            request.ahmis_auth_error = gettext("Trop de tentatives échouées : réessayez dans 15 minutes.")
            return self.form_invalid(self.get_form())
        response = super().post(request, *args, **kwargs)
        if request.user.is_authenticated:
            throttle.reset(keys[0])
        else:
            throttle.register_failure(keys[0])
            throttle.register_failure(keys[1], limit=throttle.IP_MAX_FAILURES)
        return response

    def get(self, request, *args, **kwargs):
        auth = settings.AHMIS_AUTH
        if auth["OIDC_ENABLED"] and auth["OIDC_AUTO_REDIRECT"] and "local" not in request.GET and "sso" not in request.GET:
            from django.urls import reverse
            from urllib.parse import urlencode

            nxt = request.GET.get("next")
            return redirect(reverse("oidc_authentication_init") + (("?" + urlencode({"next": nxt})) if nxt else ""))
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        from django.contrib.auth import get_user_model

        from .demo_accounts import DEMO_ACCOUNTS, DEMO_PASSWORD

        ctx = super().get_context_data(**kwargs)
        auth = settings.AHMIS_AUTH
        if settings.AHMIS["DEMO"] and get_user_model().objects.filter(username="camo").exists():
            ctx["demo_accounts"] = [(u, role) for u, role, *_ in DEMO_ACCOUNTS]
            ctx["demo_password"] = DEMO_PASSWORD
        ctx["ldap_enabled"] = auth["LDAP_ENABLED"]
        ctx["ldap_domain"] = auth["LDAP_DOMAIN"]
        ctx["oidc_enabled"] = auth["OIDC_ENABLED"]
        ctx["oidc_label"] = auth["OIDC_BUTTON_LABEL"]
        ctx["auth_error"] = getattr(self.request, "ahmis_auth_error", "")
        if self.request.GET.get("sso") == "echec":
            ctx["auth_error"] = self.request.session.pop("ahmis_sso_error", "") or gettext("La connexion par SSO a échoué.")
        return ctx


@login_not_required
def oidc_init(request):
    from mozilla_django_oidc.views import OIDCAuthenticationRequestView

    return OIDCAuthenticationRequestView.as_view()(request)


@login_not_required
def oidc_callback(request):
    from mozilla_django_oidc.views import OIDCAuthenticationCallbackView

    return OIDCAuthenticationCallbackView.as_view()(request)


SIGNATURE_PIN_MAX_AGE = 15 * 60  # le code ne se modifie que dans les 15 min suivant la connexion


def my_account(request):
    from .identity import signature_methods
    from .models import SignaturePin

    user = request.user
    login_at = request.session.get("ahmis_login_at", 0)
    fresh = (timezone.now().timestamp() - login_at) < SIGNATURE_PIN_MAX_AGE
    pin = SignaturePin.objects.filter(user=user).first()
    if request.method == "POST":
        new, confirm = request.POST.get("pin", ""), request.POST.get("pin_confirm", "")
        current = request.POST.get("current", "")
        if not fresh:
            messages.error(request, gettext("Pour des raisons de sécurité, reconnectez-vous avant de modifier votre code de signature."))
        elif pin and not (pin.check_pin(current) or (user.has_usable_password() and user.check_password(current))):
            messages.error(request, gettext("Code de signature actuel (ou mot de passe) incorrect."))
        elif len(new) < 6 or len(set(new)) < 3:
            messages.error(request, gettext("Le code doit contenir au moins 6 caractères, dont 3 différents."))
        elif new != confirm:
            messages.error(request, gettext("Les deux saisies ne correspondent pas."))
        elif user.has_usable_password() and user.check_password(new):
            messages.error(request, gettext("Le code de signature doit être différent de votre mot de passe."))
        else:
            pin = pin or SignaturePin(user=user)
            pin.set_pin(new)
            pin.save()
            from .models import AuditLog
            from django.contrib.contenttypes.models import ContentType

            AuditLog.objects.create(user=user, username=user.username, action="update",
                                    content_type=ContentType.objects.get_for_model(user), object_id=str(user.pk),
                                    object_repr=gettext("Code de signature de {username}").format(username=user.username), changes='{"code de signature": {"old": "***", "new": "défini"}}')
            messages.success(request, gettext("Code de signature enregistré."))
            return redirect("my_account")
    from apps.part145.models import Staff

    return render(request, "core/my_account.html", {
        "identities": user.external_identities.all(),
        "methods": signature_methods(user),
        "has_pin": bool(pin),
        "pin_locked": bool(pin and pin.failed_attempts >= 5),
        "fresh": fresh,
        "staff": Staff.objects.filter(user=user).first(),
        "groups": user.groups.all(),
    })


def dashboard(request):
    today = timezone.localdate()
    items = fleet_due_list()
    aircraft = list(Aircraft.objects.exclude(status="retired").select_related("aircraft_type"))
    by_ac = {}
    for i in items:
        s = by_ac.setdefault(i.aircraft.pk, {"overdue": 0, "tolerance": 0, "due_soon": 0})
        if i.status in s:
            s[i.status] += 1
    fleet_rows = []
    for ac in sorted(aircraft, key=lambda a: a.registration):
        fleet_rows.append({"ac": ac, "counts": by_ac.get(ac.pk, {"overdue": 0, "tolerance": 0, "due_soon": 0})})
    from apps.fleet.heli3d import photo_for

    photos = {}
    for row in fleet_rows:  # photo du type (hélicoptères), sinon dessin
        code = row["ac"].aircraft_type.code
        if code not in photos:
            photos[code] = photo_for(code) if row["ac"].aircraft_type.category == "helicopter" else None
        row["photo"] = photos[code]
    for n, row in enumerate(fleet_rows):  # appareil annoncé « Suivant » dans le carrousel
        row["next"] = fleet_rows[(n + 1) % len(fleet_rows)]
    from apps.camo.models import amp_review_status

    amp_alerts = []
    for t in {ac.aircraft_type for ac in aircraft}:
        st = amp_review_status(t, today)
        if st["status"] != "ok":
            amp_alerts.append({"type": t, **st})
    amp_alerts.sort(key=lambda r: r["type"].code)
    from apps.quality.views import dashboard_kpi as quality_kpi
    from apps.safety.views import dashboard_kpi

    ctx = {
        "occ": dashboard_kpi(request.user),
        "qual": quality_kpi(request.user),
        "amp_alerts": amp_alerts,
        "amp_bad": any(r["status"] in ("none", "overdue") for r in amp_alerts),
        "today": today,
        "kpi": {
            "aircraft": len(aircraft),
            "overdue": sum(1 for i in items if i.status in ("overdue", "tolerance")),
            "tolerance": sum(1 for i in items if i.status == "tolerance"),
            "due_soon": sum(1 for i in items if i.status == "due_soon"),
            "open_defects": Defect.objects.filter(status="open").count(),
            "deferred": Defect.objects.filter(status="deferred").count(),
            "deferred_overdue": Defect.objects.filter(status="deferred", deferral_limit_date__lt=today).count(),
            "ad_to_assess": DirectiveApplicability.objects.filter(status="to_assess").count(),
            "wp_active": WorkPackage.objects.filter(status__in=["planned", "in_progress"]).count(),
            "cards_waiting_inspection": TaskCard.objects.filter(status="performed").count(),
            "requests": PartRequest.objects.filter(status="requested").count(),
            "quarantine": Component.objects.filter(status="quarantine").count() + StockItem.objects.filter(status="quarantine").count(),
            "tools_expired": sum(1 for t in Tool.objects.exclude(status="unserviceable") if not t.calibration_ok),
            "auth_expiring": Authorization.objects.filter(suspended=False, valid_until__gte=today, valid_until__lte=today + timedelta(days=60)).count(),
        },
        "top_items": [i for i in items if i.status != "ok"][:12],
        "fleet_rows": fleet_rows,
        "active_wps": WorkPackage.objects.filter(status__in=["planned", "in_progress"]).select_related("aircraft").order_by("planned_start")[:8],
    }
    return render(request, "core/dashboard.html", ctx)


def search(request):
    from .search import MIN_LENGTH, global_search

    q = request.GET.get("q", "").strip()
    results = global_search(request.user, q)
    if len(results) == 1:
        return redirect(results[0][2])
    groups = {}
    for kind, obj, url in results:
        groups.setdefault(str(kind), []).append((obj, url))
    return render(request, "core/search.html", {"q": q, "results": results, "groups": groups.items(), "too_short": 0 < len(q) < MIN_LENGTH})


@permission_required("core.view_auditlog", raise_exception=True)
def audit_list(request):
    qs = AuditLog.objects.select_related("content_type", "user")
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(Q(object_repr__icontains=q) | Q(username__icontains=q) | Q(changes__icontains=q))
    ct = request.GET.get("type")
    if ct:
        qs = qs.filter(content_type_id=ct)
    obj = request.GET.get("object")
    if obj:
        qs = qs.filter(object_id=obj)
    page = Paginator(qs, 50).get_page(request.GET.get("page"))
    types = ContentType.objects.filter(pk__in=AuditLog.objects.values("content_type").distinct())
    return render(request, "core/audit_list.html", {"page": page, "types": types})


@permission_required("core.view_signaturerecord", raise_exception=True)
def signature_list(request):
    qs = SignatureRecord.objects.select_related("content_type")
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(Q(object_repr__icontains=q) | Q(signer_name__icontains=q) | Q(statement__icontains=q))
    action = request.GET.get("action")
    if action:
        qs = qs.filter(action=action)
    page = Paginator(qs, 50).get_page(request.GET.get("page"))
    return render(request, "core/signature_list.html", {"page": page, "actions": SignatureRecord.ACTIONS})


TRANSLATED_DOCS = ("en", "es", "de")


def _tutorial_path(slug):
    """Chemin du tutoriel dans la langue active, sinon la version française de référence."""
    lang = (get_language() or "fr")[:2]
    if lang in TRANSLATED_DOCS:
        localized = DOCS_DIR / lang / f"{slug}.md"
        if localized.is_file():
            return localized
    return DOCS_DIR / f"{slug}.md"


def _tutorials():
    files = sorted(DOCS_DIR.glob("*.md"))
    result = []
    for f in files:
        path = _tutorial_path(f.stem)
        first = path.read_text(encoding="utf-8").splitlines()[0] if path.stat().st_size else f.stem
        result.append({"slug": f.stem, "title": first.lstrip("# ").strip()})
    return result


def help_index(request):
    return help_page(request, None)


def help_page(request, slug):
    tutorials = _tutorials()
    if slug is None:
        slug = tutorials[0]["slug"] if tutorials else None
    if slug is None:
        raise Http404
    if slug not in [t["slug"] for t in tutorials]:
        raise Http404
    path = _tutorial_path(slug)
    html = markdown.markdown(path.read_text(encoding="utf-8"), extensions=["tables", "fenced_code", "sane_lists", "toc"])
    idx = [t["slug"] for t in tutorials].index(slug)
    return render(request, "core/help.html", {
        "tutorials": tutorials, "slug": slug, "content": html,
        "fallback": path.parent == DOCS_DIR and (get_language() or "fr")[:2] in TRANSLATED_DOCS,
        "prev": tutorials[idx - 1] if idx > 0 else None,
        "next": tutorials[idx + 1] if idx + 1 < len(tutorials) else None,
    })


def protected_media(request, path):
    """Sert un fichier joint à un utilisateur connecté qui a le droit de consulter l'objet propriétaire.

    Seuls les dossiers listés dans MEDIA_PERMISSIONS sont servis ; tout autre chemin (dont les
    dossiers de transfert, servis par leur vue dédiée) répond 404. Le fichier est servi avec une
    CSP « sandbox » : un contenu actif téléversé ne peut pas s'exécuter sur l'origine de l'application.
    """
    from django.core.exceptions import PermissionDenied
    from django.http import FileResponse
    from django.utils._os import safe_join

    parts = Path(path).parts
    folder = parts[0].lower() if parts else ""
    if "~" in path or "\\" in path or folder not in MEDIA_PERMISSIONS:
        raise Http404
    if not request.user.has_perm(MEDIA_PERMISSIONS[folder]):
        raise PermissionDenied
    try:
        full = Path(safe_join(settings.MEDIA_ROOT, path))
    except Exception:
        raise Http404
    if not full.is_file():
        raise Http404
    inline = full.suffix.lower() in INLINE_MEDIA and request.GET.get("dl") != "1"
    response = FileResponse(open(full, "rb"), as_attachment=not inline, filename=full.name)
    response["Content-Security-Policy"] = "default-src 'none'; img-src 'self'; style-src 'unsafe-inline'; sandbox"
    response["X-Content-Type-Options"] = "nosniff"
    return response


# Dossier de MEDIA_ROOT -> permission requise. Les transferts n'y figurent pas : vue dédiée.
MEDIA_PERMISSIONS = {
    "consignes": "camo.view_directive",
    "certificats": "logistics.view_releasecertificate",
    "documents": "quality.view_controlleddocument",
}
INLINE_MEDIA = {".pdf", ".png", ".jpg", ".jpeg"}


# ---------------------------------------------------------------- Conservation des enregistrements
@permission_required("core.view_auditlog", raise_exception=True)
def retention_report(request):
    from . import retention

    today = timezone.localdate()
    rows = []
    for rule in retention.RULES:
        items, counts = retention.evaluate(rule, today)
        eligible = sorted((x for x in items if x[1] is not None and x[1] <= today), key=lambda x: x[1])
        rows.append({"rule": rule, "counts": counts, "sample": eligible[:10]})
    withdrawn = Aircraft.objects.filter(status="retired").order_by("-withdrawn_on")
    return render(request, "core/retention.html", {"rows": rows, "today": today, "withdrawn": withdrawn,
                                                    "months": {"work": retention.work_months(), "life": retention.life_months(),
                                                               "staff": retention.staff_months()}})


@permission_required("core.view_auditlog", raise_exception=True)
def retention_csv(request, key):
    import csv

    from django.http import Http404, HttpResponse

    from . import retention

    rule = retention.RULES_BY_KEY.get(key)
    if rule is None:
        raise Http404
    today = timezone.localdate()
    items, _ = retention.evaluate(rule, today)
    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="conservation-{key}-{today:%Y%m%d}.csv"'
    resp.write("\ufeff")
    w = csv.writer(resp, delimiter=";")
    w.writerow(["id", "enregistrement", gettext("conserver jusqu'au"), gettext("état")])
    for obj, until in items:
        state = gettext("sans échéance") if until is None else (gettext("échue – archivable") if until <= today else gettext("en cours"))
        label = str(obj)
        if label[:1] in ("=", "+", "-", "@", "\t", "\r"):
            label = "'" + label
        w.writerow([obj.pk, label, until.isoformat() if until else "", state])
    return resp
