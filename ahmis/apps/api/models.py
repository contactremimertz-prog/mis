"""Jetons d'accès à l'API externe.

Un jeton est rattaché à un compte AHMIS (de préférence un compte de service dédié) : l'API applique
exactement les droits du rôle de ce compte. La clé n'est jamais stockée en clair (empreinte SHA-256),
elle n'est affichée qu'une seule fois, à la création.
"""
import hashlib
import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone

KEY_PREFIX = "ahm_"


def hash_key(raw):
    """Empreinte SHA-256 d'une clé API (la clé est aléatoire et longue : un sel est inutile)."""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class ApiToken(models.Model):
    SCOPES = [("read", "Lecture seule"), ("write", "Lecture et écriture")]

    name = models.CharField("nom du système appelant", max_length=100, help_text="ex. Logiciel d'exploitation, SAP PI, Power BI")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="api_tokens", verbose_name="compte AHMIS")
    scope = models.CharField("portée", max_length=5, choices=SCOPES, default="read")
    prefix = models.CharField("préfixe", max_length=12, editable=False, db_index=True)
    key_hash = models.CharField(max_length=64, unique=True, editable=False)
    allowed_ips = models.CharField("adresses IP autorisées", max_length=500, blank=True,
                                   help_text="Séparées par des virgules ; vide = toutes")
    expires_at = models.DateTimeField("expire le", null=True, blank=True)
    active = models.BooleanField("actif", default=True)
    created_at = models.DateTimeField("créé le", default=timezone.now)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+", verbose_name="créé par")
    last_used_at = models.DateTimeField("dernière utilisation", null=True, blank=True)
    last_used_ip = models.GenericIPAddressField("dernière adresse IP", null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "jeton API"
        verbose_name_plural = "jetons API"

    def __str__(self):
        return f"{self.name} ({self.prefix}…)"

    @classmethod
    def issue(cls, name, user, scope="read", created_by=None, expires_at=None, allowed_ips=""):
        """Crée un jeton et retourne (jeton, clé en clair). La clé en clair n'est plus récupérable ensuite."""
        raw = KEY_PREFIX + secrets.token_urlsafe(32)
        token = cls.objects.create(name=name, user=user, scope=scope, prefix=raw[:12], key_hash=hash_key(raw),
                                   created_by=created_by, expires_at=expires_at, allowed_ips=allowed_ips)
        return token, raw

    @property
    def is_valid(self):
        return self.active and self.user.is_active and (self.expires_at is None or self.expires_at > timezone.now())

    def ip_allowed(self, ip):
        allowed = [x.strip() for x in self.allowed_ips.split(",") if x.strip()]
        return not allowed or ip in allowed
