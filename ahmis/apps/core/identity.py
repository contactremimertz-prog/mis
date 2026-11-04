"""Identités d'entreprise : correspondance groupes -> rôles, création / mise à jour des comptes,
vérification du secret de signature électronique.

Commun à l'Active Directory (auth_ldap) et au SSO OpenID Connect (auth_oidc).
"""
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from .models import ExternalIdentity, SignaturePin
from .roles import ROLES

log = logging.getLogger("ahmis.auth")
ADMIN_ROLE = "admin"


def auth_settings():
    return settings.AHMIS_AUTH


def parse_role_map(raw=None):
    """« GG-AHMIS-CAMO:Ingénieur CAMO;GG-AHMIS-ADMIN:admin » -> {clé normalisée: rôle}."""
    raw = auth_settings()["ROLE_MAP"] if raw is None else raw
    mapping = {}
    for entry in (raw or "").replace("\n", ";").split(";"):
        if ":" not in entry:
            continue
        key, role = entry.rsplit(":", 1)
        key, role = key.strip(), role.strip()
        if not key or not role:
            continue
        if role != ADMIN_ROLE and role not in ROLES:
            log.error("AHMIS_ROLE_MAP : rôle inconnu « %s » (rôles valides : %s, admin)", role, ", ".join(ROLES))
            continue
        mapping[key.lower()] = role
    return mapping


def roles_for_groups(groups, mapping=None):
    """Retourne l'ensemble des rôles AHMIS correspondant à une liste d'identifiants de groupes.

    Chaque groupe peut être fourni sous plusieurs formes (DN, CN, GUID) : on teste toutes les variantes.
    """
    mapping = parse_role_map() if mapping is None else mapping
    roles = set()
    for g in groups or []:
        g = str(g).strip()
        variants = {g.lower()}
        if "=" in g and "," in g:  # DN : CN=GG-AHMIS-CAMO,OU=Groupes,DC=corp,DC=local
            first = g.split(",", 1)[0]
            if "=" in first:
                variants.add(first.split("=", 1)[1].strip().lower())
        for v in variants:
            if v in mapping:
                roles.add(mapping[v])
    return roles


@transaction.atomic
def sync_user(provider, subject, username, first_name="", last_name="", email="", groups=(), staff_key="", login_name=""):
    """Crée ou met à jour le compte AHMIS d'un utilisateur d'entreprise. Lève PermissionDenied si refusé."""
    cfg = auth_settings()
    User = get_user_model()
    username = (username or "").strip().lower()[:150]
    if not subject or not username:
        raise PermissionDenied("Identité d'entreprise incomplète.")
    roles = roles_for_groups(groups)
    if cfg["REQUIRE_ROLE"] and not roles:
        log.warning("Connexion %s refusée pour %s : aucun groupe AHMIS (%s)", provider, username, ", ".join(map(str, groups))[:500])
        raise PermissionDenied("Votre compte n'appartient à aucun groupe donnant accès à AHMIS.")

    identity = ExternalIdentity.objects.select_related("user").filter(provider=provider, subject=subject).first()
    if identity:
        user = identity.user
    else:
        user = User.objects.filter(username=username).first()
        if user is not None:
            already_external = user.external_identities.exists()
            if not already_external and not cfg["LINK_EXISTING"]:
                log.error("Connexion %s refusée : le compte local « %s » existe déjà (AHMIS_AUTH_LINK_EXISTING=0)", provider, username)
                raise PermissionDenied("Un compte local porte déjà cet identifiant : contactez l'administrateur AHMIS.")
        else:
            user = User(username=username)
            user.set_unusable_password()
        identity = ExternalIdentity(user=user, provider=provider, subject=subject)

    user.first_name = (first_name or user.first_name)[:150]
    user.last_name = (last_name or user.last_name)[:150]
    user.email = (email or user.email)[:254]
    user.is_active = True
    user.is_superuser = ADMIN_ROLE in roles
    user.is_staff = user.is_superuser
    user.save()
    identity.user = user
    identity.login_name = login_name or username
    identity.groups = "\n".join(map(str, groups))[:10000]
    identity.last_login = timezone.now()
    identity.save()

    # Rôles : seuls les groupes AHMIS sont gérés, d'autres groupes ajoutés à la main sont conservés.
    managed = Group.objects.filter(name__in=list(ROLES))
    user.groups.remove(*managed)
    user.groups.add(*Group.objects.filter(name__in=[r for r in roles if r != ADMIN_ROLE]))

    if staff_key:
        _link_staff(user, staff_key)
    log.info("Connexion %s : %s (rôles : %s)", provider, username, ", ".join(sorted(roles)) or "aucun")
    return user


def _link_staff(user, key):
    from apps.part145.models import Staff

    if Staff.objects.filter(user=user).exists():
        return
    staff = Staff.objects.filter(employee_number=str(key).strip(), user__isnull=True).first()
    if staff:
        staff.user = user
        staff.save()
        log.info("Fiche personnel %s rattachée au compte %s", staff.employee_number, user.username)


# ---------------------------------------------------------------------------------------------- signature
def signature_methods(user):
    """Moyens de signature disponibles pour ce compte (pour l'affichage)."""
    methods = []
    if user.has_usable_password():
        methods.append("password")
    if auth_settings()["LDAP_ENABLED"] and user.external_identities.filter(provider="ldap").exists():
        methods.append("ldap")
    if SignaturePin.objects.filter(user=user).exists():
        methods.append("pin")
    return methods


def verify_signature_secret(user, secret):
    """Revérifie l'identité au moment d'une signature ; 5 échecs en 15 minutes bloquent la signature 15 minutes."""
    from . import throttle

    key = f"sign:{user.pk}"
    if not secret or throttle.is_locked(key):
        return False
    if _verify_signature_secret(user, secret):
        throttle.reset(key)
        return True
    throttle.register_failure(key)
    return False


def _verify_signature_secret(user, secret):
    if user.has_usable_password() and user.check_password(secret):
        return True
    if auth_settings()["LDAP_ENABLED"]:
        ident = user.external_identities.filter(provider="ldap").first()
        if ident:
            from .auth_ldap import verify_password

            try:
                if verify_password(ident.login_name, secret):
                    return True
            except Exception:  # annuaire injoignable : on tente le code de signature
                log.exception("Vérification AD impossible pour %s", user.username)
    from django.db import transaction
    from django.db.models import F

    with transaction.atomic():
        pin = SignaturePin.objects.select_for_update().filter(user=user).first()
        if pin:
            if pin.failed_attempts >= 5:
                log.warning("Code de signature bloqué pour %s", user.username)
                return False
            if pin.check_pin(secret):
                if pin.failed_attempts:
                    SignaturePin.objects.filter(pk=pin.pk).update(failed_attempts=0)
                return True
            SignaturePin.objects.filter(pk=pin.pk).update(failed_attempts=F("failed_attempts") + 1)
    return False
