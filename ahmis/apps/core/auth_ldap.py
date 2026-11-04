"""Authentification Active Directory par LDAP (bibliothèque ldap3, 100 % Python : Windows et Linux).

Principe : AHMIS se lie à l'annuaire avec l'identifiant et le mot de passe saisis par l'utilisateur
(aucun compte de service nécessaire), lit sa fiche et ses groupes (y compris imbriqués), puis
crée ou met à jour le compte AHMIS et ses rôles selon AHMIS_ROLE_MAP.
"""
import logging
import ssl
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.core.exceptions import ImproperlyConfigured, PermissionDenied

log = logging.getLogger("ahmis.auth")

ACCOUNTDISABLE = 0x2
IN_CHAIN = "1.2.840.113556.1.4.1941"  # LDAP_MATCHING_RULE_IN_CHAIN (groupes imbriqués AD)


class LdapUnavailable(Exception):
    pass


def cfg():
    return settings.AHMIS_AUTH


def normalize_username(raw):
    """« CORP\\jdupont », « jdupont@corp.local » ou « jdupont » -> « jdupont »."""
    name = (raw or "").strip()
    if "\\" in name:
        name = name.split("\\", 1)[1]
    if "@" in name:
        name = name.split("@", 1)[0]
    return name


def _bind_name(username):
    c = cfg()
    fmt = c["LDAP_BIND_FORMAT"] or ("{username}@" + c["LDAP_DOMAIN"] if c["LDAP_DOMAIN"] else "")
    if not fmt:
        raise ImproperlyConfigured("AHMIS_LDAP_DOMAIN ou AHMIS_LDAP_BIND_FORMAT est requis.")
    return fmt.format(username=username)


def _server_pool():
    import ldap3

    c = cfg()
    if not c["LDAP_SERVERS"]:
        raise ImproperlyConfigured("AHMIS_LDAP_SERVERS est requis.")
    tls = ldap3.Tls(validate=ssl.CERT_REQUIRED, ca_certs_file=c["LDAP_CA_FILE"] or None, version=ssl.PROTOCOL_TLS_CLIENT)
    servers = []
    for url in c["LDAP_SERVERS"]:
        secure = url.lower().startswith("ldaps://")
        if not secure and not c["LDAP_START_TLS"] and not c["LDAP_ALLOW_PLAIN"]:
            raise ImproperlyConfigured(
                f"{url} : connexion non chiffrée refusée. Utilisez ldaps://, AHMIS_LDAP_START_TLS=1, "
                "ou AHMIS_LDAP_ALLOW_PLAIN=1 pour un test."
            )
        servers.append(ldap3.Server(url, use_ssl=secure, tls=tls, get_info=ldap3.NONE, connect_timeout=c["LDAP_TIMEOUT"]))
    return ldap3.ServerPool(servers, ldap3.FIRST, active=1, exhaust=True)


def make_connection(bind_user, password):
    """Ouvre une connexion liée avec les identifiants de l'utilisateur. Point d'injection pour les tests."""
    import ldap3

    conn = ldap3.Connection(_server_pool(), user=bind_user, password=password, authentication=ldap3.SIMPLE,
                            receive_timeout=cfg()["LDAP_TIMEOUT"], raise_exceptions=False, read_only=True)
    if cfg()["LDAP_START_TLS"]:
        conn.open()
        conn.start_tls()
    return conn


def _bind(username, password):
    """Retourne une connexion liée, None si identifiants refusés, LdapUnavailable si l'annuaire ne répond pas."""
    import ldap3
    from ldap3.core.exceptions import LDAPException

    if not password:  # un bind sans mot de passe est un bind anonyme : toujours refuser
        return None
    try:
        conn = make_connection(_bind_name(username), password)
        if not conn.bind():
            result = (conn.result or {}).get("description", "")
            if result in ("invalidCredentials",) or (conn.result or {}).get("result") == 49:
                return None
            raise LdapUnavailable(f"Liaison LDAP refusée : {conn.result}")
        return conn
    except LDAPException as e:
        raise LdapUnavailable(str(e)) from e


def _attr(entry, name):
    value = entry.get("attributes", {}).get(name)
    if isinstance(value, list):
        value = value[0] if value else ""
    return value if value is not None else ""


def _groups(conn, user_dn, member_of):
    from ldap3.utils.conv import escape_filter_chars

    groups = list(member_of or [])
    if cfg()["LDAP_NESTED_GROUPS"]:
        try:
            ok = conn.search(cfg()["LDAP_BASE_DN"], f"(&(objectClass=group)(member:{IN_CHAIN}:={escape_filter_chars(user_dn)}))",
                             attributes=["distinguishedName", "cn", "objectGUID"])
            if ok:
                for e in conn.response:
                    if e.get("type") != "searchResEntry":
                        continue
                    groups.append(e.get("dn", ""))
                    guid = _attr(e, "objectGUID")
                    if guid:
                        groups.append(str(guid).strip("{}"))
        except Exception:  # annuaire ne supportant pas la règle « in chain » : memberOf direct
            log.warning("Recherche des groupes imbriqués impossible, utilisation de memberOf seul", exc_info=True)
    return sorted(set(g for g in groups if g))


def ldap_lookup(username, password):
    """Authentifie et lit la fiche AD. Retourne un dict ou None si identifiants invalides / compte désactivé."""
    from ldap3.utils.conv import escape_filter_chars

    sam = normalize_username(username)
    if not sam:
        return None
    conn = _bind(sam, password)
    if conn is None:
        return None
    try:
        flt = cfg()["LDAP_USER_FILTER"].format(username=escape_filter_chars(sam))
        attrs = ["sAMAccountName", "userPrincipalName", "givenName", "sn", "mail", "objectGUID",
                 "memberOf", "userAccountControl", cfg()["LDAP_STAFF_ATTR"]]
        conn.search(cfg()["LDAP_BASE_DN"], flt, attributes=[a for a in attrs if a])
        entries = [e for e in conn.response if e.get("type") == "searchResEntry"]
        if len(entries) != 1:
            log.warning("AD : %d fiche(s) trouvée(s) pour %s", len(entries), sam)
            return None
        e = entries[0]
        uac = _attr(e, "userAccountControl")
        if uac and int(uac) & ACCOUNTDISABLE:
            log.warning("AD : compte désactivé %s", sam)
            return None
        member_of = e.get("attributes", {}).get("memberOf") or []
        if isinstance(member_of, str):
            member_of = [member_of]
        guid = _attr(e, "objectGUID")
        try:
            guid = str(uuid.UUID(str(guid).strip("{}")))
        except ValueError:
            guid = str(guid) or e.get("dn", "")
        return {
            "subject": guid or e.get("dn", ""),
            "dn": e.get("dn", ""),
            "username": str(_attr(e, "sAMAccountName") or sam),
            "upn": str(_attr(e, "userPrincipalName")),
            "first_name": str(_attr(e, "givenName")),
            "last_name": str(_attr(e, "sn")),
            "email": str(_attr(e, "mail")),
            "staff_key": str(_attr(e, cfg()["LDAP_STAFF_ATTR"])) if cfg()["LDAP_STAFF_ATTR"] else "",
            "groups": _groups(conn, e.get("dn", ""), member_of),
        }
    finally:
        conn.unbind()


def verify_password(login_name, password):
    """Revérifie un mot de passe AD (signature électronique)."""
    conn = _bind(normalize_username(login_name), password)
    if conn is None:
        return False
    conn.unbind()
    return True


class ActiveDirectoryBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not cfg()["LDAP_ENABLED"] or not username or not password:
            return None
        try:
            info = ldap_lookup(username, password)
        except LdapUnavailable as e:
            log.error("Active Directory injoignable : %s", e)
            if request is not None:
                request.ahmis_auth_error = "L'annuaire Active Directory est injoignable. Réessayez ou contactez l'administrateur."
            return None
        if info is None:
            return None
        from .identity import sync_user

        try:
            return sync_user("ldap", info["subject"], info["username"], info["first_name"], info["last_name"],
                             info["email"], info["groups"], info["staff_key"], login_name=info["username"])
        except PermissionDenied as e:
            if request is not None:
                request.ahmis_auth_error = str(e)
            return None

    def get_user(self, user_id):
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
