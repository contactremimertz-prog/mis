"""Initialise une installation AHMIS (hors démo) : rôles et compte administrateur.

    python manage.py ahmis_init --admin-user admin --admin-password '...' [--admin-email x@y]

Le mot de passe peut aussi être fourni par la variable AHMIS_ADMIN_PASSWORD.
Commande idempotente : relancée, elle met à jour les rôles sans toucher aux comptes existants.
"""
import os

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management import BaseCommand, CommandError

from apps.core.roles import setup_roles


class Command(BaseCommand):
    help = "Crée les rôles AHMIS et le compte administrateur initial."

    def add_arguments(self, parser):
        parser.add_argument("--admin-user", default="admin")
        parser.add_argument("--admin-password", default=None)
        parser.add_argument("--admin-email", default="")

    def handle(self, *args, **opts):
        groups = setup_roles()
        self.stdout.write(f"Rôles à jour : {', '.join(g.name for g in groups)}")
        User = get_user_model()
        username = opts["admin_user"]
        if User.objects.filter(username=username).exists():
            self.stdout.write(f"Le compte « {username} » existe déjà : inchangé.")
            return
        password = opts["admin_password"] or os.environ.get("AHMIS_ADMIN_PASSWORD")
        if not password:
            raise CommandError("Mot de passe administrateur requis (--admin-password ou AHMIS_ADMIN_PASSWORD).")
        user = User(username=username, email=opts["admin_email"], is_staff=True, is_superuser=True)
        try:
            validate_password(password, user)
        except ValidationError as e:
            raise CommandError("Mot de passe refusé : " + " ".join(e.messages))
        user.set_password(password)
        user.save()
        self.stdout.write(self.style.SUCCESS(f"Compte administrateur « {username} » créé."))
