"""Serveur d'application AHMIS pour l'exploitation (Windows, ou Linux sans gunicorn).

    python serve.py                    # écoute sur AHMIS_BIND (défaut 0.0.0.0:8000)

Utilise Waitress, serveur WSGI pur Python adapté à la production sous Windows.
Sous Linux, l'installeur utilise plutôt gunicorn derrière nginx.
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


def main():
    try:
        from waitress import serve
    except ImportError:
        sys.exit("Waitress n'est pas installé : pip install -r requirements-server.txt")
    from django.conf import settings
    from django.core.wsgi import get_wsgi_application

    application = get_wsgi_application()
    settings.DEBUG  # charge la configuration (ahmis.env) avant de lire AHMIS_BIND
    bind = os.environ.get("AHMIS_BIND", "0.0.0.0:8000")
    threads = int(os.environ.get("AHMIS_THREADS", "8"))
    print(f"AHMIS en service sur http://{bind.replace('0.0.0.0', 'localhost')}  ({threads} threads)", flush=True)
    options = {"listen": bind, "threads": threads, "ident": "AHMIS"}
    proxy = os.environ.get("AHMIS_TRUSTED_PROXY")
    if proxy:  # AHMIS derrière IIS / un proxy HTTPS : faire confiance à X-Forwarded-Proto de ce proxy uniquement
        options.update(trusted_proxy=proxy, trusted_proxy_headers={"x-forwarded-proto", "x-forwarded-for"})
    serve(application, **options)


if __name__ == "__main__":
    main()
