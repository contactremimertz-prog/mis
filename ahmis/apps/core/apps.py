from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Socle AHMIS"

    def ready(self):
        from . import audit

        audit.connect()

        from . import retention

        retention.connect_guards()

        from django.contrib.auth.signals import user_logged_in, user_login_failed

        def _on_login(sender, request, user, **kwargs):
            if request is not None and hasattr(request, "session"):
                from django.utils import timezone

                request.session["ahmis_login_at"] = timezone.now().timestamp()

        def _on_failed(sender, credentials, request=None, **kwargs):
            import logging

            logging.getLogger("ahmis.auth").warning("Échec de connexion pour « %s »", credentials.get("username", "?"))

        user_logged_in.connect(_on_login, dispatch_uid="ahmis_login_at")
        user_login_failed.connect(_on_failed, dispatch_uid="ahmis_login_failed")
