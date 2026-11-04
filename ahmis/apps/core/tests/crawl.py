"""Parcours automatique des pages (utilisé par test_smoke_i18n) : toutes les pages sans paramètre
et la fiche de chaque enregistrement ayant une URL, dans chaque langue."""
from django.apps import apps
from django.conf import settings
from django.urls import URLPattern, URLResolver, get_resolver, reverse
from django.utils import translation

SKIP_PREFIXES = ("/admin/", "/api/", "/static/", "/media/", "/logout", "/deconnexion", "/i18n/", "/auth/")


def _walk(patterns, prefix=""):
    for p in patterns:
        if isinstance(p, URLResolver):
            ns = f"{p.namespace}:" if p.namespace else prefix
            yield from _walk(p.url_patterns, ns if p.namespace else prefix)
        elif isinstance(p, URLPattern) and p.name and not p.pattern.converters:
            yield prefix + p.name


def static_urls():
    out = set()
    for name in _walk(get_resolver().url_patterns):
        try:
            url = reverse(name)
        except Exception:
            continue
        if not url.startswith(SKIP_PREFIXES) and "export" not in name and "download" not in name:
            out.add(url)
    return sorted(out)


def object_urls(per_model=2):
    out = set()
    for model in apps.get_models():
        if model._meta.app_label not in ("camo", "fleet", "logistics", "part145", "quality", "safety", "core"):
            continue
        if not hasattr(model, "get_absolute_url"):
            continue
        for obj in model.objects.all()[:per_model]:
            try:
                out.add(obj.get_absolute_url().split("#")[0])
            except Exception:
                pass
    return sorted(out)


def crawl(client, urls, langs=None):
    """Retourne la liste des (langue, url, code) en erreur (5xx ou exception)."""
    errors = []
    for lang in langs or [l for l, _ in settings.LANGUAGES]:
        client.cookies[settings.LANGUAGE_COOKIE_NAME] = lang
        for url in urls:
            try:
                with translation.override(lang):
                    r = client.get(url, HTTP_ACCEPT_LANGUAGE=lang)
                if r.status_code >= 500:
                    errors.append((lang, url, r.status_code))
            except Exception as e:  # noqa: BLE001
                errors.append((lang, url, f"{type(e).__name__}: {e}"[:200]))
    return errors
