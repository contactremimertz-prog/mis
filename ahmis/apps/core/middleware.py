"""Mémorise l'utilisateur de la requête courante pour l'audit trail."""
import contextvars

_current_user = contextvars.ContextVar("ahmis_current_user", default=None)


def get_current_user():
    user = _current_user.get()
    if user is not None and getattr(user, "is_authenticated", False):
        return user
    return None


def set_current_user(user):
    return _current_user.set(user)


class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = _current_user.set(getattr(request, "user", None))
        try:
            return self.get_response(request)
        finally:
            _current_user.reset(token)


CSP = ("default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; "
       "object-src 'none'; base-uri 'self'; frame-ancestors 'none'")


class SecurityHeadersMiddleware:
    """En-têtes de sécurité communs : CSP (sauf si la vue en fixe une, ex. fichiers joints) et Referrer-Policy."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.headers.setdefault("Content-Security-Policy", CSP)
        response.headers.setdefault("Referrer-Policy", "same-origin")
        return response
