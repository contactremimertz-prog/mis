"""SSO OpenID Connect : Microsoft Entra ID (Azure AD), ADFS, Keycloak, Okta...

Repose sur mozilla-django-oidc (signature du jeton vérifiée par les clés publiques du fournisseur).
Les groupes / rôles reçus dans le jeton sont convertis en rôles AHMIS par AHMIS_ROLE_MAP.
"""
import logging

from django.conf import settings
from django.core.exceptions import PermissionDenied
from mozilla_django_oidc.auth import OIDCAuthenticationBackend

from .identity import sync_user

log = logging.getLogger("ahmis.auth")


def claims_to_identity(claims):
    """Extrait l'identité AHMIS des claims OIDC (fonction pure, testable sans fournisseur)."""
    cfg = settings.AHMIS_AUTH
    sub = claims.get("oid") or claims.get("sub")  # Entra : oid stable entre applications
    iss = claims.get("iss", "")
    username = ""
    for name in cfg["OIDC_USERNAME_CLAIMS"]:
        if claims.get(name):
            username = str(claims[name])
            break
    login = username
    if "@" in username:
        username = username.split("@", 1)[0]
    groups = []
    for name in cfg["OIDC_GROUPS_CLAIMS"]:
        value = claims.get(name)
        if isinstance(value, str):
            value = [value]
        groups.extend(str(v) for v in (value or []))
    return {
        "subject": f"{iss}|{sub}" if iss else str(sub or ""),
        "username": username,
        "login_name": login,
        "first_name": claims.get("given_name", ""),
        "last_name": claims.get("family_name", ""),
        "email": claims.get("email") or (login if "@" in login else ""),
        "groups": groups,
        "staff_key": str(claims.get(cfg["OIDC_STAFF_CLAIM"], "") or ""),
    }


class AhmisOIDCBackend(OIDCAuthenticationBackend):
    def get_userinfo(self, access_token, id_token, payload):
        # Les claims du jeton d'identité (vérifié) contiennent les groupes ; le userinfo les complète.
        claims = dict(payload or {})
        if self.OIDC_OP_USER_ENDPOINT:
            try:
                extra = super().get_userinfo(access_token, id_token, payload) or {}
                for k, v in extra.items():
                    claims.setdefault(k, v)
            except Exception:
                log.warning("Point userinfo OIDC indisponible, utilisation du seul jeton d'identité", exc_info=True)
        return claims

    def get_or_create_user(self, access_token, id_token, payload):
        claims = self.get_userinfo(access_token, id_token, payload)
        info = claims_to_identity(claims)
        if not info["subject"] or not info["username"]:
            log.error("SSO : claims insuffisants (%s)", ", ".join(sorted(claims)))
            return None
        try:
            return sync_user("oidc", info["subject"], info["username"], info["first_name"], info["last_name"],
                             info["email"], info["groups"], info["staff_key"], login_name=info["login_name"])
        except PermissionDenied as e:
            if self.request is not None:
                self.request.session["ahmis_sso_error"] = str(e)
            return None
