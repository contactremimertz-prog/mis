"""Lit la configuration publique d'un fournisseur OpenID Connect et affiche les lignes à copier dans ahmis.env.

    python manage.py ahmis_oidc_discover https://login.microsoftonline.com/<tenant>/v2.0
    python manage.py ahmis_oidc_discover https://adfs.corp.local/adfs
    python manage.py ahmis_oidc_discover https://sso.corp.local/realms/aero
"""
import json
import urllib.request

from django.core.management import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Découvre les points de terminaison OpenID Connect d'un fournisseur (issuer)."

    def add_arguments(self, parser):
        parser.add_argument("issuer")

    def handle(self, *args, **opts):
        url = opts["issuer"].rstrip("/") + "/.well-known/openid-configuration"
        try:
            with urllib.request.urlopen(url, timeout=10) as r:
                conf = json.load(r)
        except Exception as e:
            raise CommandError(f"Impossible de lire {url} : {e}")
        self.stdout.write(f"# Fournisseur : {conf.get('issuer')}")
        self.stdout.write("AHMIS_OIDC_ENABLED=1")
        self.stdout.write("AHMIS_OIDC_PROVIDER=generic")
        self.stdout.write(f"AHMIS_OIDC_AUTHORIZATION_ENDPOINT={conf.get('authorization_endpoint', '')}")
        self.stdout.write(f"AHMIS_OIDC_TOKEN_ENDPOINT={conf.get('token_endpoint', '')}")
        self.stdout.write(f"AHMIS_OIDC_USERINFO_ENDPOINT={conf.get('userinfo_endpoint', '')}")
        self.stdout.write(f"AHMIS_OIDC_JWKS_ENDPOINT={conf.get('jwks_uri', '')}")
        algs = conf.get("id_token_signing_alg_values_supported") or ["RS256"]
        self.stdout.write(f"AHMIS_OIDC_SIGN_ALGO={'RS256' if 'RS256' in algs else algs[0]}")
        self.stdout.write("AHMIS_OIDC_CLIENT_ID=<identifiant de l'application enregistrée>")
        self.stdout.write("AHMIS_OIDC_CLIENT_SECRET=<secret de l'application>")
