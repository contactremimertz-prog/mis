from django.urls import path

from . import views as v

app_name = "camo"

urlpatterns = [
    path("echeances/", v.due, name="due"),
    path("echeances/export.csv", v.due_csv, name="due_csv"),
    path("forecast/", v.forecast, name="forecast"),
    path("programme/", v.TaskList.as_view(), name="task_list"),
    path("programme/nouvelle/", v.TaskCreate.as_view(), name="task_create"),
    path("programme/<int:pk>/", v.task_detail, name="task_detail"),
    path("programme/<int:pk>/modifier/", v.TaskUpdate.as_view(), name="task_update"),
    path("programme/<int:pk>/realisation/", v.task_record, name="task_record"),
    path("programme/<int:pk>/pieces/", v.task_add_part, name="task_add_part"),
    path("programme/<int:pk>/pieces/<int:part_pk>/retirer/", v.task_remove_part, name="task_remove_part"),
    path("consignes/", v.DirectiveList.as_view(), name="directive_list"),
    path("consignes/nouvelle/", v.DirectiveCreate.as_view(), name="directive_create"),
    path("consignes/<int:pk>/", v.directive_detail, name="directive_detail"),
    path("consignes/<int:pk>/modifier/", v.DirectiveUpdate.as_view(), name="directive_update"),
    path("consignes/statuts/", v.ApplicabilityList.as_view(), name="directive_status_list"),
    path("consignes/statuts/<int:pk>/", v.applicability_update, name="applicability_update"),
    path("modifications/", v.ModificationList.as_view(), name="mod_list"),
    path("modifications/nouvelle/", v.ModificationCreate.as_view(), name="mod_create"),
    path("modifications/<int:pk>/", v.mod_detail, name="mod_detail"),
    path("modifications/<int:pk>/modifier/", v.ModificationUpdate.as_view(), name="mod_update"),
    path("revue-programme/", v.amp_review_list, name="amp_review_list"),
    path("revue-programme/nouvelle/", v.AmpReviewCreate.as_view(), name="amp_review_create"),
    path("revue-programme/<int:pk>/", v.amp_review_detail, name="amp_review_detail"),
    path("transferts/", v.TransferList.as_view(), name="transfer_list"),
    path("transferts/nouveau/", v.TransferCreate.as_view(), name="transfer_create"),
    path("transferts/<int:pk>/", v.transfer_detail, name="transfer_detail"),
    path("transferts/<int:pk>/archive.zip", v.transfer_download, name="transfer_download"),
    path("arc/", v.ArcList.as_view(), name="arc_list"),
    path("arc/nouveau/", v.ArcCreate.as_view(), name="arc_create"),
]
