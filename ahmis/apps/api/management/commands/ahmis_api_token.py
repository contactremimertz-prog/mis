"""Crée un jeton API en ligne de commande (scripts de déploiement).

    python manage.py ahmis_api_token --name "Logiciel OPS" --user svc_ops --scope write --days 365
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management import BaseCommand, CommandError
from django.utils import timezone

from apps.api.models import ApiToken


class Command(BaseCommand):
    help = "Crée un jeton d'accès à l'API externe et affiche la clé (une seule fois)."

    def add_arguments(self, parser):
        parser.add_argument("--name", required=True)
        parser.add_argument("--user", required=True, help="Compte AHMIS dont les droits s'appliquent")
        parser.add_argument("--scope", choices=["read", "write"], default="read")
        parser.add_argument("--days", type=int, default=365, help="Validité en jours (0 = sans limite)")
        parser.add_argument("--ips", default="", help="Adresses IP autorisées, séparées par des virgules")

    def handle(self, *args, **o):
        user = get_user_model().objects.filter(username=o["user"]).first()
        if not user:
            raise CommandError(f"Compte « {o['user']} » introuvable.")
        if user.is_superuser:
            raise CommandError("Un jeton ne peut pas être lié à un compte administrateur.")
        expires = timezone.now() + timedelta(days=o["days"]) if o["days"] else None
        token, key = ApiToken.issue(o["name"], user, o["scope"], expires_at=expires, allowed_ips=o["ips"])
        self.stdout.write(self.style.SUCCESS(f"Jeton « {token.name} » créé (portée {token.scope})."))
        self.stdout.write(key)
