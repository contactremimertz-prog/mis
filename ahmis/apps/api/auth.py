"""Authentification et autorisations de l'API.

- ``TokenAuthentication`` : en-tête ``Authorization: Bearer ahm_...`` (ou ``Token ahm_...``).
- ``AhmisPermission`` : chaque vue déclare les permissions Django requises en lecture et en écriture ;
  un jeton en lecture seule ne peut jamais écrire, quel que soit le rôle de son compte.
"""
import hmac

from django.utils import timezone
from rest_framework import authentication, exceptions, permissions

from apps.core.middleware import set_current_user

from .models import ApiToken, hash_key


def client_ip(request):
    """Adresse IP du client (REMOTE_ADDR : ne jamais faire confiance à X-Forwarded-For sans proxy maîtrisé)."""
    return request.META.get("REMOTE_ADDR", "")


class TokenAuthentication(authentication.BaseAuthentication):
    keywords = ("bearer", "token")

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).decode("latin-1").strip()
        if not header:
            return None
        parts = header.split()
        if len(parts) != 2 or parts[0].lower() not in self.keywords:
            return None
        raw = parts[1]
        candidate = ApiToken.objects.select_related("user").filter(key_hash=hash_key(raw)).first()
        # Comparaison en temps constant de l'empreinte (défense en profondeur)
        if candidate is None or not hmac.compare_digest(candidate.key_hash, hash_key(raw)):
            raise exceptions.AuthenticationFailed("Jeton API invalide.")
        if not candidate.is_valid:
            raise exceptions.AuthenticationFailed("Jeton API révoqué ou expiré.")
        ip = client_ip(request)
        if not candidate.ip_allowed(ip):
            raise exceptions.AuthenticationFailed("Adresse IP non autorisée pour ce jeton.")
        now = timezone.now()
        if not candidate.last_used_at or (now - candidate.last_used_at).total_seconds() > 60:
            ApiToken.objects.filter(pk=candidate.pk).update(last_used_at=now, last_used_ip=ip or None)
        # Le journal d'audit attribue les écritures au compte du jeton
        set_current_user(candidate.user)
        return candidate.user, candidate

    def authenticate_header(self, request):
        return 'Bearer realm="AHMIS"'


class SessionAuthentication(authentication.SessionAuthentication):
    """Session web (navigateur déjà connecté à AHMIS) : utile pour explorer l'API ; CSRF exigé en écriture."""


class AhmisPermission(permissions.BasePermission):
    """Vérifie ``view.read_perms`` (GET/HEAD/OPTIONS) ou ``view.write_perms`` (POST/PUT/PATCH/DELETE)."""

    message = "Droits insuffisants pour cette opération."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            needed = getattr(view, "read_perms", [])
        else:
            if isinstance(request.auth, ApiToken) and request.auth.scope != "write":
                self.message = "Ce jeton API est en lecture seule."
                return False
            needed = getattr(view, "write_perms", None)
            if needed is None:
                return False
        return user.has_perms(needed)
