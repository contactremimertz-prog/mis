"""Tests Active Directory (annuaire simulé ldap3 MOCK_SYNC) et SSO OpenID Connect (claims simulés)."""
from unittest import mock

import ldap3
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import PermissionDenied
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.core.identity import parse_role_map, roles_for_groups, sync_user, verify_signature_secret
from apps.core.models import ExternalIdentity, SignaturePin
from apps.core.roles import setup_roles
from apps.part145.models import Staff

BASE = "DC=corp,DC=local"
ROLE_MAP = "GG-AHMIS-CAMO:Ingénieur CAMO;GG-AHMIS-CERT:Certifiant;3f2a0c1e-0000-4000-8000-000000000001:Magasinier;GG-AHMIS-ADMIN:admin"

AD_USERS = {
    "jdupont": dict(pw="Secret-AD-1", groups=["CN=GG-AHMIS-CAMO,OU=Groupes,DC=corp,DC=local"], emp="C042", uac=512, given="Jean", sn="Dupont"),
    "mcurie": dict(pw="Secret-AD-2", groups=["CN=GG-AHMIS-CERT,OU=Groupes,DC=corp,DC=local", "CN=Tout-le-monde,OU=Groupes,DC=corp,DC=local"], emp="", uac=512, given="Marie", sn="Curie"),
    "inactif": dict(pw="Secret-AD-3", groups=["CN=GG-AHMIS-CAMO,OU=Groupes,DC=corp,DC=local"], emp="", uac=514, given="Ex", sn="Salarié"),
    "sansrole": dict(pw="Secret-AD-4", groups=["CN=Compta,OU=Groupes,DC=corp,DC=local"], emp="", uac=512, given="Paul", sn="Compta"),
    "admin": dict(pw="Secret-AD-5", groups=["CN=GG-AHMIS-ADMIN,OU=Groupes,DC=corp,DC=local"], emp="", uac=512, given="Faux", sn="Admin"),
}


def fake_connection(bind_user, password):
    server = ldap3.Server("fake-dc")
    conn = ldap3.Connection(server, user=bind_user, password=password, client_strategy=ldap3.MOCK_SYNC)
    for sam, u in AD_USERS.items():
        conn.strategy.add_entry(f"CN={sam},OU=Utilisateurs,{BASE}", {
            "objectClass": ["top", "person", "user"], "objectCategory": "person", "sAMAccountName": sam,
            "userPrincipalName": f"{sam}@corp.local", "givenName": u["given"], "sn": u["sn"], "mail": f"{sam}@corp.local",
            "userPassword": u["pw"], "memberOf": u["groups"], "employeeID": u["emp"] or "none", "userAccountControl": str(u["uac"]),
            "objectGUID": f"guid-{sam}",
        })
    return conn


def auth_cfg(**over):
    cfg = dict(settings.AHMIS_AUTH)
    cfg.update({
        "ROLE_MAP": ROLE_MAP, "LDAP_ENABLED": True, "LDAP_SERVERS": ["ldaps://fake-dc"], "LDAP_DOMAIN": "corp.local",
        "LDAP_BIND_FORMAT": "CN={username},OU=Utilisateurs," + BASE, "LDAP_BASE_DN": BASE, "LDAP_NESTED_GROUPS": False,
        "LDAP_STAFF_ATTR": "employeeID",
    })
    cfg.update(over)
    return cfg


BACKENDS = ["apps.core.auth_ldap.ActiveDirectoryBackend", "apps.core.auth_backends.LocalBackend"]


@override_settings(AHMIS_AUTH=auth_cfg(), AUTHENTICATION_BACKENDS=BACKENDS)
@mock.patch("apps.core.auth_ldap.make_connection", side_effect=fake_connection)
class ActiveDirectoryTests(TestCase):
    def setUp(self):
        setup_roles()
        self.staff = Staff.objects.create(employee_number="C042", first_name="Jean", last_name="Dupont", role="camo")

    def test_login_creates_account_with_roles_and_staff_link(self, _m):
        user = authenticate(username="CORP\\jdupont", password="Secret-AD-1")
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "jdupont")
        self.assertEqual(user.first_name, "Jean")
        self.assertFalse(user.has_usable_password())
        self.assertEqual([g.name for g in user.groups.all()], ["Ingénieur CAMO"])
        self.assertEqual(ExternalIdentity.objects.get(user=user).provider, "ldap")
        self.staff.refresh_from_db()
        self.assertEqual(self.staff.user, user)

    def test_upn_form_and_second_login_reuses_account(self, _m):
        u1 = authenticate(username="mcurie@corp.local", password="Secret-AD-2")
        u2 = authenticate(username="mcurie", password="Secret-AD-2")
        self.assertEqual(u1.pk, u2.pk)
        self.assertEqual([g.name for g in u2.groups.all()], ["Certifiant"])

    def test_wrong_password_refused(self, _m):
        self.assertIsNone(authenticate(username="jdupont", password="mauvais"))

    def test_empty_password_never_binds_anonymously(self, _m):
        self.assertIsNone(authenticate(username="jdupont", password=""))

    def test_disabled_account_refused(self, _m):
        self.assertIsNone(authenticate(username="inactif", password="Secret-AD-3"))

    def test_user_without_ahmis_group_refused(self, _m):
        self.assertIsNone(authenticate(username="sansrole", password="Secret-AD-4"))
        self.assertFalse(get_user_model().objects.filter(username="sansrole").exists())

    def test_existing_local_account_not_hijacked(self, _m):
        get_user_model().objects.create_superuser("admin", password="Local-secours-1")
        # Un utilisateur AD nommé « admin » ne doit pas prendre le contrôle du compte local de secours
        self.assertIsNone(authenticate(username="admin", password="Secret-AD-5"))
        local = authenticate(username="admin", password="Local-secours-1")
        self.assertIsNotNone(local)
        self.assertFalse(local.external_identities.exists())

    def test_role_removed_when_group_removed(self, _m):
        authenticate(username="jdupont", password="Secret-AD-1")
        AD_USERS["jdupont"]["groups"] = ["CN=GG-AHMIS-CERT,OU=Groupes,DC=corp,DC=local"]
        try:
            user = authenticate(username="jdupont", password="Secret-AD-1")
            self.assertEqual([g.name for g in user.groups.all()], ["Certifiant"])
        finally:
            AD_USERS["jdupont"]["groups"] = ["CN=GG-AHMIS-CAMO,OU=Groupes,DC=corp,DC=local"]

    def test_signature_checked_against_ad(self, _m):
        user = authenticate(username="jdupont", password="Secret-AD-1")
        self.assertTrue(verify_signature_secret(user, "Secret-AD-1"))
        self.assertFalse(verify_signature_secret(user, "faux"))

    def test_login_page_with_ad(self, _m):
        r = self.client.post(reverse("login"), {"username": "CORP\\jdupont", "password": "Secret-AD-1"})
        self.assertEqual(r.status_code, 302)
        r = self.client.get(reverse("my_account"))
        self.assertContains(r, "Active Directory")
        self.assertContains(r, "mot de passe Windows")


@override_settings(AHMIS_AUTH=auth_cfg(LDAP_ENABLED=False, OIDC_ENABLED=True,
                                        OIDC_GROUPS_CLAIMS=["groups", "roles"], OIDC_USERNAME_CLAIMS=["preferred_username", "upn", "email"],
                                        OIDC_STAFF_CLAIM="employeeid"))
class OidcTests(TestCase):
    def setUp(self):
        setup_roles()

    def claims(self, **over):
        c = {"iss": "https://login.microsoftonline.com/tenant/v2.0", "sub": "abc", "oid": "11111111-2222",
             "preferred_username": "Sophie.Lambert@corp.fr", "given_name": "Sophie", "family_name": "Lambert",
             "groups": ["3f2a0c1e-0000-4000-8000-000000000001"], "roles": ["GG-AHMIS-CERT"], "employeeid": "M004"}
        c.update(over)
        return c

    def test_claims_mapping_and_account_creation(self):
        from apps.core.auth_oidc import claims_to_identity

        info = claims_to_identity(self.claims())
        self.assertEqual(info["username"], "Sophie.Lambert")
        self.assertEqual(info["subject"], "https://login.microsoftonline.com/tenant/v2.0|11111111-2222")
        Staff.objects.create(employee_number="M004", first_name="Sophie", last_name="Lambert")
        user = sync_user("oidc", info["subject"], info["username"], info["first_name"], info["last_name"], info["email"],
                         info["groups"], info["staff_key"], login_name=info["login_name"])
        self.assertEqual(user.username, "sophie.lambert")
        self.assertEqual(sorted(g.name for g in user.groups.all()), ["Certifiant", "Magasinier"])
        self.assertEqual(user.email, "Sophie.Lambert@corp.fr")
        self.assertEqual(Staff.objects.get(employee_number="M004").user, user)

    def test_admin_role_and_no_role(self):
        user = sync_user("oidc", "iss|x", "chef", groups=["GG-AHMIS-ADMIN"])
        self.assertTrue(user.is_superuser)
        with self.assertRaises(PermissionDenied):
            sync_user("oidc", "iss|y", "visiteur", groups=["Autre"])

    def test_sso_user_signs_with_personal_code(self):
        user = sync_user("oidc", "iss|z", "pilote", groups=["GG-AHMIS-CERT"])
        self.assertFalse(verify_signature_secret(user, "123456"))
        self.client.force_login(user)
        r = self.client.post(reverse("my_account"), {"pin": "48a1x9", "pin_confirm": "48a1x9"})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(verify_signature_secret(user, "48a1x9"))
        self.assertFalse(verify_signature_secret(user, "48a1x8"))

    def test_code_locked_after_five_errors(self):
        user = sync_user("oidc", "iss|w", "bloque", groups=["GG-AHMIS-CERT"])
        pin = SignaturePin(user=user)
        pin.set_pin("code-perso")
        pin.save()
        for _ in range(5):
            self.assertFalse(verify_signature_secret(user, "faux"))
        self.assertFalse(verify_signature_secret(user, "code-perso"))


class RoleMapTests(TestCase):
    def test_parse_and_match_variants(self):
        m = parse_role_map(ROLE_MAP + ";GG-INCONNU:Rôle bidon")
        self.assertNotIn("gg-inconnu", m)
        self.assertEqual(roles_for_groups(["CN=gg-ahmis-camo,OU=X,DC=corp,DC=local"], m), {"Ingénieur CAMO"})
        self.assertEqual(roles_for_groups(["3F2A0C1E-0000-4000-8000-000000000001"], m), {"Magasinier"})


@override_settings(AHMIS_AUTH=auth_cfg(LDAP_ENABLED=False, LOCAL_LOGIN=False))
class LocalLoginPolicyTests(TestCase):
    def test_only_superuser_can_use_local_password(self):
        User = get_user_model()
        User.objects.create_user("meca", password="Meca-pass-123")
        User.objects.create_superuser("secours", password="Secours-pass-123")
        self.assertIsNone(authenticate(username="meca", password="Meca-pass-123"))
        self.assertIsNotNone(authenticate(username="secours", password="Secours-pass-123"))
