"""Teste la connexion Active Directory d'un utilisateur, sans rien modifier dans AHMIS.

    python manage.py ahmis_test_ldap jdupont
"""
import getpass

from django.conf import settings
from django.core.management import BaseCommand, CommandError

from apps.core.auth_ldap import LdapUnavailable, ldap_lookup
from apps.core.identity import parse_role_map, roles_for_groups


class Command(BaseCommand):
    help = "Teste l'authentification Active Directory et affiche les rôles AHMIS qui seraient attribués."

    def add_arguments(self, parser):
        parser.add_argument("username")

    def handle(self, *args, **opts):
        cfg = settings.AHMIS_AUTH
        if not cfg["LDAP_ENABLED"]:
            raise CommandError("AHMIS_LDAP_ENABLED=1 n'est pas défini dans ahmis.env.")
        self.stdout.write(f"Serveurs : {', '.join(cfg['LDAP_SERVERS'])} · base : {cfg['LDAP_BASE_DN']}")
        mapping = parse_role_map()
        self.stdout.write(f"Correspondances groupes -> rôles : {len(mapping)}")
        for k, v in mapping.items():
            self.stdout.write(f"  {k}  ->  {v}")
        password = getpass.getpass(f"Mot de passe de {opts['username']} : ")
        try:
            info = ldap_lookup(opts["username"], password)
        except LdapUnavailable as e:
            raise CommandError(f"Annuaire injoignable : {e}")
        if info is None:
            raise CommandError("Identifiants refusés, compte désactivé ou introuvable sous la base de recherche.")
        self.stdout.write(self.style.SUCCESS("Authentification réussie."))
        for k in ("username", "upn", "first_name", "last_name", "email", "staff_key", "dn", "subject"):
            self.stdout.write(f"  {k:11}: {info[k]}")
        self.stdout.write(f"  groupes    : {len(info['groups'])}")
        for g in info["groups"]:
            self.stdout.write(f"    {g}")
        roles = roles_for_groups(info["groups"], mapping)
        if roles:
            self.stdout.write(self.style.SUCCESS(f"Rôles AHMIS attribués : {', '.join(sorted(roles))}"))
        else:
            self.stdout.write(self.style.WARNING("Aucun rôle AHMIS : la connexion serait refusée (AHMIS_AUTH_REQUIRE_ROLE=1)."))
