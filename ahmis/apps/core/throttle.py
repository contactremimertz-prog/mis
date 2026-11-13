"""Limitation des tentatives d'authentification : après MAX_FAILURES échecs dans WINDOW, la clé
(compte ou adresse IP) est bloquée pendant LOCK. Compteur en base, incrément atomique : il tient
avec plusieurs processus serveur."""
import logging
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone

from .models import AuthThrottle

log = logging.getLogger("ahmis.security")

MAX_FAILURES = 5
IP_MAX_FAILURES = 20
WINDOW = timedelta(minutes=15)
LOCK = timedelta(minutes=15)


def client_ip(request):
    return (request.META.get("REMOTE_ADDR") or "")[:64]


def is_locked(key):
    row = AuthThrottle.objects.filter(key=key).only("locked_until").first()
    return bool(row and row.locked_until and row.locked_until > timezone.now())


def register_failure(key, limit=MAX_FAILURES):
    now = timezone.now()
    with transaction.atomic():
        try:
            with transaction.atomic():
                row, _ = AuthThrottle.objects.select_for_update().get_or_create(key=key)
        except IntegrityError:
            row = AuthThrottle.objects.select_for_update().get(key=key)
        if not row.first_failure_at or now - row.first_failure_at > WINDOW:
            AuthThrottle.objects.filter(pk=row.pk).update(failures=1, first_failure_at=now)
            failures = 1
        else:
            AuthThrottle.objects.filter(pk=row.pk).update(failures=F("failures") + 1)
            failures = row.failures + 1
        if failures >= limit:
            AuthThrottle.objects.filter(pk=row.pk).update(locked_until=now + LOCK)
            log.warning("Authentification bloquée pour %s après %s échecs", key, failures)
    return failures


def reset(key):
    AuthThrottle.objects.filter(key=key).delete()
