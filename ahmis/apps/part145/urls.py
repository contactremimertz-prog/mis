from django.urls import path

from . import views as v

app_name = "part145"

urlpatterns = [
    path("planning/", v.planning, name="planning"),
    path("work-packages/", v.WorkPackageList.as_view(), name="wp_list"),
    path("work-packages/nouveau/", v.WorkPackageCreate.as_view(), name="wp_create"),
    path("work-packages/<int:pk>/", v.wp_detail, name="wp_detail"),
    path("work-packages/<int:pk>/modifier/", v.WorkPackageUpdate.as_view(), name="wp_update"),
    path("work-packages/<int:pk>/imprimer/", v.wp_print, name="wp_print"),
    path("work-packages/<int:pk>/ajouter/", v.wp_add_items, name="wp_add_items"),
    path("work-packages/<int:pk>/travail-additionnel/", v.wp_add_adhoc, name="wp_add_adhoc"),
    path("work-packages/<int:pk>/crs/", v.wp_crs, name="wp_crs"),
    path("planifier/<int:aircraft_pk>/", v.plan_from_due, name="plan_from_due"),
    path("task-cards/", v.TaskCardList.as_view(), name="card_list"),
    path("task-cards/<int:pk>/", v.card_detail, name="card_detail"),
    path("task-cards/<int:pk>/imprimer/", v.card_print, name="card_print"),
    path("task-cards/<int:pk>/action/<str:action>/", v.card_action, name="card_action"),
    path("task-cards/<int:pk>/changement-composant/", v.card_component_change, name="card_component_change"),
    path("task-cards/<int:pk>/constatation/", v.card_finding, name="card_finding"),
    path("etapes/<int:pk>/signer/", v.step_sign, name="step_sign"),
    path("defauts/", v.DefectList.as_view(), name="defect_list"),
    path("defauts/nouveau/", v.DefectCreate.as_view(), name="defect_create"),
    path("defauts/<int:pk>/", v.defect_detail, name="defect_detail"),
    path("defauts/<int:pk>/reporter/", v.defect_defer, name="defect_defer"),
    path("defauts/<int:pk>/proroger/", v.defect_extend, name="defect_extend"),
    path("defauts/<int:pk>/vers-wp/", v.defect_to_wp, name="defect_to_wp"),
    path("personnel/", v.StaffList.as_view(), name="staff_list"),
    path("personnel/nouveau/", v.StaffCreate.as_view(), name="staff_create"),
    path("personnel/<int:pk>/", v.staff_detail, name="staff_detail"),
    path("personnel/<int:pk>/modifier/", v.StaffUpdate.as_view(), name="staff_update"),
    path("personnel/<int:pk>/autorisation/", v.staff_add_authorization, name="staff_add_authorization"),
    path("personnel/<int:pk>/formation/", v.staff_add_qualification, name="staff_add_qualification"),
    path("personnel/<int:pk>/experience/", v.staff_add_experience, name="staff_add_experience"),
]
