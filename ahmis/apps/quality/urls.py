from django.urls import path

from . import views as v

app_name = "quality"

urlpatterns = [
    path("audits/", v.AuditList.as_view(), name="audit_list"),
    path("audits/nouveau/", v.AuditCreate.as_view(), name="audit_create"),
    path("audits/<int:pk>/", v.audit_detail, name="audit_detail"),
    path("audits/<int:pk>/modifier/", v.AuditUpdate.as_view(), name="audit_update"),
    path("audits/<int:pk>/constat/", v.finding_add, name="finding_add"),
    path("constats/", v.FindingList.as_view(), name="finding_list"),
    path("constats/<int:pk>/cloturer/", v.finding_close, name="finding_close"),
    path("documents/", v.DocumentList.as_view(), name="doc_list"),
    path("documents/nouveau/", v.DocumentCreate.as_view(), name="doc_create"),
    path("documents/<int:pk>/", v.doc_detail, name="doc_detail"),
    path("documents/<int:pk>/modifier/", v.DocumentUpdate.as_view(), name="doc_update"),
    path("documents/<int:pk>/revision/", v.revision_add, name="revision_add"),
    path("documents/<int:pk>/retirer/", v.doc_withdraw, name="doc_withdraw"),
    path("revisions/<int:pk>/approuver/", v.revision_approve, name="revision_approve"),
    path("revisions/<int:pk>/refuser/", v.revision_reject, name="revision_reject"),
]
