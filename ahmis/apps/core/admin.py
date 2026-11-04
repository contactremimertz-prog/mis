"""Administration : réservée au paramétrage. Les enregistrements de navigabilité
ne peuvent pas être supprimés, et le journal d'audit / les signatures sont en lecture seule."""
from django.apps import apps
from django.contrib import admin

from .models import AuditLog, ExternalIdentity, SignaturePin, SignatureRecord, TrackedModel


class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AuditLog)
class AuditLogAdmin(ReadOnlyAdmin):
    list_display = ["timestamp", "username", "action", "content_type", "object_repr"]
    list_filter = ["action", "content_type"]
    search_fields = ["object_repr", "username"]


@admin.register(SignatureRecord)
class SignatureAdmin(ReadOnlyAdmin):
    list_display = ["signed_at", "signer_name", "action", "object_repr"]
    list_filter = ["action"]


class NoDeleteAdmin(admin.ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        return not getattr(self.model, "ahmis_no_delete", False)

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields if not f.editable]


for label in ("fleet", "camo", "part145", "logistics"):
    for model in apps.get_app_config(label).get_models():
        if issubclass(model, TrackedModel):
            admin.site.register(model, NoDeleteAdmin)


@admin.register(ExternalIdentity)
class ExternalIdentityAdmin(admin.ModelAdmin):
    list_display = ["user", "provider", "login_name", "last_login"]
    list_filter = ["provider"]
    search_fields = ["user__username", "login_name", "subject"]
    readonly_fields = ["user", "provider", "subject", "login_name", "groups", "first_seen", "last_login"]

    def has_add_permission(self, request):
        return False


@admin.register(SignaturePin)
class SignaturePinAdmin(admin.ModelAdmin):
    """Seule action utile : débloquer ou supprimer un code (l'utilisateur en redéfinit un)."""

    list_display = ["user", "updated_at", "failed_attempts"]
    readonly_fields = ["user", "pin_hash", "updated_at"]
    fields = ["user", "failed_attempts", "updated_at"]

    def has_add_permission(self, request):
        return False
