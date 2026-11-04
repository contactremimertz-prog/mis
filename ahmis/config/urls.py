from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_not_required
from django.urls import include, path

from apps.core import views as core

admin.site.site_header = "AHMIS – administration"
admin.site.site_title = "AHMIS"

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
    path("", core.dashboard, name="dashboard"),
    path("connexion/", login_not_required(core.LoginView.as_view()), name="login"),
    path("deconnexion/", auth_views.LogoutView.as_view(), name="logout"),
    path("recherche/", core.search, name="search"),
    path("mon-compte/", core.my_account, name="my_account"),
    path("qualite/audit/", core.audit_list, name="audit_list"),
    path("qualite/signatures/", core.signature_list, name="signature_list"),
    path("qualite/conservation/", core.retention_report, name="retention_report"),
    path("qualite/conservation/<slug:key>.csv", core.retention_csv, name="retention_csv"),
    path("aide/", core.help_index, name="help_index"),
    path("aide/<slug:slug>/", core.help_page, name="help_page"),
    path("flotte/", include("apps.fleet.urls")),
    path("camo/", include("apps.camo.urls")),
    path("part145/", include("apps.part145.urls")),
    path("logistique/", include("apps.logistics.urls")),
    path("evenements/", include("apps.safety.urls")),
    path("admin/", admin.site.urls),
    # Pièces jointes (scans de certificats, consignes) : réservées aux utilisateurs connectés
    path("media/<path:path>", core.protected_media, name="protected_media"),
]

if settings.API_ENABLED:
    from apps.api import token_views

    urlpatterns += [
        path("api/v1/", include("apps.api.urls")),
        path("administration/api/", token_views.token_list, name="api_tokens"),
        path("administration/api/<int:pk>/revoquer/", token_views.token_revoke, name="api_token_revoke"),
    ]

if settings.AHMIS_AUTH["OIDC_ENABLED"]:
    urlpatterns += [
        path("sso/connexion/", core.oidc_init, name="oidc_authentication_init"),
        path("sso/retour/", core.oidc_callback, name="oidc_authentication_callback"),
    ]
