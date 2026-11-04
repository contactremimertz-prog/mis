"""
Configuration AHMIS.

Indépendance vis-à-vis du SGBD : toute la persistance passe par l'ORM Django.
Aucune requête SQL spécifique n'est utilisée dans le code applicatif.

Toute la configuration se fait par variables AHMIS_*, lues :
  1. dans l'environnement du processus (prioritaire) ;
  2. puis dans le fichier désigné par AHMIS_ENV_FILE, ou à défaut « ahmis.env » à la racine du projet.

Principales variables (voir deploy/ahmis.env.exemple) :
    AHMIS_DEBUG, AHMIS_SECRET_KEY, AHMIS_ALLOWED_HOSTS, AHMIS_CSRF_TRUSTED_ORIGINS, AHMIS_HTTPS
    AHMIS_DATA_DIR (base SQLite, pièces jointes, journaux), AHMIS_DEMO
    AHMIS_DB_ENGINE (sqlite | postgresql | mysql | oracle | mssql), AHMIS_DB_NAME, AHMIS_DB_USER,
    AHMIS_DB_PASSWORD, AHMIS_DB_HOST, AHMIS_DB_PORT

Sans aucune variable, AHMIS démarre en mode démo locale : SQLite dans db/ahmis.sqlite3.
"""
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def _env_file_candidates():
    if os.environ.get("AHMIS_ENV_FILE"):
        return [Path(os.environ["AHMIS_ENV_FILE"])]
    found = [BASE_DIR / "ahmis.env"]
    if os.name == "nt":
        found.append(Path(os.environ.get("ProgramData", r"C:\ProgramData")) / "AHMIS" / "ahmis.env")
    else:
        found.append(Path("/etc/ahmis/ahmis.env"))
    return found


def _load_env_file():
    """Charge le premier fichier de configuration trouvé (les variables d'environnement restent prioritaires)."""
    path = next((p for p in _env_file_candidates() if p.is_file()), None)
    if path is None:
        return None
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ.setdefault(key.strip(), value)
    return path


ENV_FILE = _load_env_file()


def env(name, default=""):
    return os.environ.get(name, default)


def env_list(name, default=""):
    return [x.strip() for x in env(name, default).split(",") if x.strip()]


DEBUG = env("AHMIS_DEBUG", "1") == "1"
_DEFAULT_KEY = "demo-uniquement-a-remplacer-en-production-0c5f2b8e7a"
SECRET_KEY = env("AHMIS_SECRET_KEY", _DEFAULT_KEY)
if not DEBUG and SECRET_KEY == _DEFAULT_KEY:
    raise ImproperlyConfigured("AHMIS_SECRET_KEY doit être défini quand AHMIS_DEBUG=0 (voir ahmis.env).")
ALLOWED_HOSTS = env_list("AHMIS_ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = env_list("AHMIS_CSRF_TRUSTED_ORIGINS")

# Dossier des données (base SQLite, pièces jointes, journaux)
DATA_DIR = Path(env("AHMIS_DATA_DIR", str(BASE_DIR)))

try:  # WhiteNoise sert les fichiers statiques sans serveur web frontal (Windows, Linux sans nginx)
    import whitenoise  # noqa: F401

    HAS_WHITENOISE = True
except ImportError:
    HAS_WHITENOISE = False

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "apps.core",
    "apps.fleet",
    "apps.camo",
    "apps.part145",
    "apps.logistics",
    "apps.api",
    "apps.safety",
    "rest_framework",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    *(["whitenoise.middleware.WhiteNoiseMiddleware"] if HAS_WHITENOISE and not DEBUG else []),
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.CurrentUserMiddleware",
    "django.contrib.auth.middleware.LoginRequiredMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.ahmis",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


def _database_config():
    engine = env("AHMIS_DB_ENGINE", "sqlite").lower()
    if engine == "sqlite":
        name = env("AHMIS_DB_NAME", str(DATA_DIR / "db" / "ahmis.sqlite3"))
        Path(name).parent.mkdir(parents=True, exist_ok=True)
        return {"ENGINE": "django.db.backends.sqlite3", "NAME": name}
    backends = {
        "postgresql": "django.db.backends.postgresql",
        "mysql": "django.db.backends.mysql",
        "oracle": "django.db.backends.oracle",
        "mssql": "mssql",  # paquet mssql-django
    }
    if engine not in backends:
        raise RuntimeError(f"AHMIS_DB_ENGINE inconnu : {engine}")
    return {
        "ENGINE": backends[engine],
        "NAME": os.environ.get("AHMIS_DB_NAME", "ahmis"),
        "USER": os.environ.get("AHMIS_DB_USER", ""),
        "PASSWORD": os.environ.get("AHMIS_DB_PASSWORD", ""),
        "HOST": os.environ.get("AHMIS_DB_HOST", ""),
        "PORT": os.environ.get("AHMIS_DB_PORT", ""),
        "ATOMIC_REQUESTS": True,
    }


DATABASES = {"default": _database_config()}
DATABASES["default"]["ATOMIC_REQUESTS"] = True

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
]

LANGUAGE_CODE = "fr"
LANGUAGES = [("fr", "Français"), ("en", "English")]
LOCALE_PATHS = [BASE_DIR / "locale"]
TIME_ZONE = os.environ.get("AHMIS_TIME_ZONE", "Europe/Paris")
USE_I18N = True
USE_TZ = True
USE_THOUSAND_SEPARATOR = False

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = Path(env("AHMIS_STATIC_ROOT", str(BASE_DIR / "staticfiles")))
MEDIA_URL = "media/"
MEDIA_ROOT = DATA_DIR / "media"
if HAS_WHITENOISE and not DEBUG:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
    }

# Sécurité en exploitation
if env("AHMIS_HTTPS", "0") == "1":
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# Journaux : console + fichier dans AHMIS_DATA_DIR/logs en exploitation
LOG_DIR = DATA_DIR / "logs"
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"std": {"format": "%(asctime)s %(levelname)s %(name)s : %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "std"}},
    "root": {"handlers": ["console"], "level": "WARNING"},
}
if not DEBUG:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LOGGING["handlers"]["file"] = {
        "class": "logging.handlers.RotatingFileHandler", "filename": str(LOG_DIR / "ahmis.log"),
        "maxBytes": 5 * 1024 * 1024, "backupCount": 10, "formatter": "std", "encoding": "utf-8",
    }
    LOGGING["root"]["handlers"].append("file")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "login"
SESSION_COOKIE_AGE = 60 * 60 * 10  # 10 h, une vacation

# Paramètres métier AHMIS
AHMIS = {
    # Fenêtre d'alerte : une échéance prévue dans ce délai passe en « À planifier »
    "ALERT_DAYS": int(os.environ.get("AHMIS_ALERT_DAYS", "30")),
    # Horizon par défaut du forecast (jours)
    "FORECAST_DAYS": int(os.environ.get("AHMIS_FORECAST_DAYS", "365")),
    # Nom de l'organisme affiché sur les task cards et CRS
    "ORGANISATION": os.environ.get("AHMIS_ORGANISATION", "Organisme de démonstration"),
    "APPROVAL_REF_145": os.environ.get("AHMIS_APPROVAL_145", "FR.145.DEMO"),
    "APPROVAL_REF_CAMO": os.environ.get("AHMIS_APPROVAL_CAMO", "FR.CAMO.DEMO"),
    # Personnel (145.A.30/35) : expérience récente et formations obligatoires bloquantes
    "RECENCY_ENFORCE": env("AHMIS_RECENCY_ENFORCE", "1") == "1",
    "RECENCY_MONTHS": int(env("AHMIS_RECENCY_MONTHS", "6")),
    "RECENCY_WINDOW_MONTHS": int(env("AHMIS_RECENCY_WINDOW_MONTHS", "24")),
    "TRAINING_REQUIRED_ALL": env_list("AHMIS_TRAINING_REQUIRED_ALL", "human_factors"),
    "TRAINING_REQUIRED_CERTIFYING": env_list("AHMIS_TRAINING_REQUIRED_CERTIFYING", "human_factors,continuation"),
    # Périodicité maximale de la revue du programme d'entretien (M.A.302(g))
    "AMP_REVIEW_MONTHS": int(env("AHMIS_AMP_REVIEW_MONTHS", "12")),
    # Mode démonstration : affiche les comptes de démo sur la page de connexion
    "DEMO": env("AHMIS_DEMO", "1" if DEBUG else "0") == "1",
}

# Tests automatiques : hachage rapide des mots de passe (jamais utilisé en exploitation)
import sys as _sys  # noqa: E402

if "test" in _sys.argv:
    PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
    LOGGING["root"]["level"] = "CRITICAL"


# ---------------------------------------------------------------------------
# API externe (voir docs/integration/api.md)
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["apps.api.auth.TokenAuthentication", "apps.api.auth.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["apps.api.auth.AhmisPermission"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"]
    + (["rest_framework.renderers.BrowsableAPIRenderer"] if DEBUG else []),
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 100,
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.UserRateThrottle", "rest_framework.throttling.AnonRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {"user": env("AHMIS_API_RATE", "600/min"), "anon": "30/min"},
    "EXCEPTION_HANDLER": "apps.api.views.api_exception_handler",
    "DATETIME_FORMAT": "iso-8601",
    "COERCE_DECIMAL_TO_STRING": False,
    "DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.openapi.AutoSchema",
    "UNAUTHENTICATED_USER": "django.contrib.auth.models.AnonymousUser",
}
# Désactiver complètement l'API : AHMIS_API_ENABLED=0
API_ENABLED = env("AHMIS_API_ENABLED", "1") == "1"

# ---------------------------------------------------------------------------
# Authentification d'entreprise : Active Directory (LDAP) et SSO (OpenID Connect)
# Voir docs/tutoriels/27-active-directory-sso.md
# ---------------------------------------------------------------------------
AHMIS_AUTH = {
    # Correspondance groupes d'entreprise -> rôles AHMIS, commune à l'AD et au SSO.
    # Format : « groupe:rôle;groupe:rôle ». Le groupe peut être un nom (CN), un DN complet ou un identifiant
    # (objectGUID AD, Object ID Entra). Le rôle spécial « admin » donne les droits d'administration.
    "ROLE_MAP": env("AHMIS_ROLE_MAP"),
    # 1 = refuser la connexion d'un utilisateur d'entreprise qui n'appartient à aucun groupe AHMIS
    "REQUIRE_ROLE": env("AHMIS_AUTH_REQUIRE_ROLE", "1") == "1",
    # 1 = autoriser le rattachement à un compte local existant de même identifiant (désactivé par sécurité)
    "LINK_EXISTING": env("AHMIS_AUTH_LINK_EXISTING", "0") == "1",
    # 0 = interdire la connexion par mot de passe local (sauf superutilisateurs : compte de secours)
    "LOCAL_LOGIN": env("AHMIS_LOCAL_LOGIN", "1") == "1",
    # --- Active Directory ---
    "LDAP_ENABLED": env("AHMIS_LDAP_ENABLED", "0") == "1",
    "LDAP_SERVERS": env_list("AHMIS_LDAP_SERVERS"),          # ex. ldaps://dc1.corp.local,ldaps://dc2.corp.local
    "LDAP_START_TLS": env("AHMIS_LDAP_START_TLS", "0") == "1",
    "LDAP_CA_FILE": env("AHMIS_LDAP_CA_FILE"),               # certificat de l'AC interne (PEM)
    "LDAP_ALLOW_PLAIN": env("AHMIS_LDAP_ALLOW_PLAIN", "0") == "1",  # ldap:// sans chiffrement (tests uniquement)
    "LDAP_DOMAIN": env("AHMIS_LDAP_DOMAIN"),                 # ex. corp.local (suffixe UPN)
    "LDAP_BIND_FORMAT": env("AHMIS_LDAP_BIND_FORMAT"),       # défaut : {username}@<domaine>
    "LDAP_BASE_DN": env("AHMIS_LDAP_BASE_DN"),               # ex. DC=corp,DC=local
    "LDAP_USER_FILTER": env("AHMIS_LDAP_USER_FILTER", "(&(objectCategory=person)(objectClass=user)(sAMAccountName={username}))"),
    "LDAP_NESTED_GROUPS": env("AHMIS_LDAP_NESTED_GROUPS", "1") == "1",
    "LDAP_STAFF_ATTR": env("AHMIS_LDAP_STAFF_ATTR", "employeeID"),  # attribut AD = matricule de la fiche personnel
    "LDAP_TIMEOUT": int(env("AHMIS_LDAP_TIMEOUT", "5")),
    # --- SSO OpenID Connect (Entra ID, ADFS, Keycloak, Okta...) ---
    "OIDC_ENABLED": env("AHMIS_OIDC_ENABLED", "0") == "1",
    "OIDC_PROVIDER": env("AHMIS_OIDC_PROVIDER", "generic"),  # entra | adfs | generic
    "OIDC_BUTTON_LABEL": env("AHMIS_OIDC_BUTTON_LABEL", "Se connecter avec le compte de l'entreprise"),
    "OIDC_AUTO_REDIRECT": env("AHMIS_OIDC_AUTO_REDIRECT", "0") == "1",
    "OIDC_GROUPS_CLAIMS": env_list("AHMIS_OIDC_GROUPS_CLAIMS", "groups,roles"),
    "OIDC_USERNAME_CLAIMS": env_list("AHMIS_OIDC_USERNAME_CLAIMS", "preferred_username,upn,email"),
    "OIDC_STAFF_CLAIM": env("AHMIS_OIDC_STAFF_CLAIM", "employeeid"),
}

AUTHENTICATION_BACKENDS = ["apps.core.auth_backends.LocalBackend"]
if AHMIS_AUTH["LDAP_ENABLED"]:
    AUTHENTICATION_BACKENDS.insert(0, "apps.core.auth_ldap.ActiveDirectoryBackend")

if AHMIS_AUTH["OIDC_ENABLED"]:
    INSTALLED_APPS.append("mozilla_django_oidc")
    AUTHENTICATION_BACKENDS.append("apps.core.auth_oidc.AhmisOIDCBackend")
    OIDC_RP_CLIENT_ID = env("AHMIS_OIDC_CLIENT_ID")
    OIDC_RP_CLIENT_SECRET = env("AHMIS_OIDC_CLIENT_SECRET")
    OIDC_RP_SIGN_ALGO = env("AHMIS_OIDC_SIGN_ALGO", "RS256")
    OIDC_RP_SCOPES = env("AHMIS_OIDC_SCOPES", "openid email profile")
    _provider = AHMIS_AUTH["OIDC_PROVIDER"]
    if _provider == "entra":
        _tenant = env("AHMIS_OIDC_TENANT_ID")
        _base = f"https://login.microsoftonline.com/{_tenant}"
        _defaults = {
            "authorization": f"{_base}/oauth2/v2.0/authorize",
            "token": f"{_base}/oauth2/v2.0/token",
            "userinfo": "https://graph.microsoft.com/oidc/userinfo",
            "jwks": f"{_base}/discovery/v2.0/keys",
        }
    elif _provider == "adfs":
        _host = env("AHMIS_OIDC_ADFS_HOST").rstrip("/")
        _defaults = {
            "authorization": f"https://{_host}/adfs/oauth2/authorize/",
            "token": f"https://{_host}/adfs/oauth2/token/",
            "userinfo": f"https://{_host}/adfs/userinfo",
            "jwks": f"https://{_host}/adfs/discovery/keys",
        }
    else:
        _defaults = {"authorization": "", "token": "", "userinfo": "", "jwks": ""}
    OIDC_OP_AUTHORIZATION_ENDPOINT = env("AHMIS_OIDC_AUTHORIZATION_ENDPOINT", _defaults["authorization"])
    OIDC_OP_TOKEN_ENDPOINT = env("AHMIS_OIDC_TOKEN_ENDPOINT", _defaults["token"])
    OIDC_OP_USER_ENDPOINT = env("AHMIS_OIDC_USERINFO_ENDPOINT", _defaults["userinfo"])
    OIDC_OP_JWKS_ENDPOINT = env("AHMIS_OIDC_JWKS_ENDPOINT", _defaults["jwks"])
    if not all([OIDC_RP_CLIENT_ID, OIDC_OP_AUTHORIZATION_ENDPOINT, OIDC_OP_TOKEN_ENDPOINT, OIDC_OP_JWKS_ENDPOINT]):
        raise ImproperlyConfigured("SSO activé mais incomplet : AHMIS_OIDC_CLIENT_ID et les points de terminaison (ou AHMIS_OIDC_PROVIDER + TENANT/ADFS_HOST) sont requis.")
    LOGIN_REDIRECT_URL_FAILURE = "/connexion/?sso=echec"
    OIDC_USE_NONCE = True
    OIDC_STORE_ID_TOKEN = False
    OIDC_TIMEOUT = 10
