from django.urls import path

from . import views as v

app_name = "fleet"

urlpatterns = [
    path("aeronefs/", v.AircraftList.as_view(), name="aircraft_list"),
    path("aeronefs/nouveau/", v.AircraftCreate.as_view(), name="aircraft_create"),
    path("aeronefs/<int:pk>/", v.aircraft_detail, name="aircraft_detail"),
    path("aeronefs/<int:pk>/modifier/", v.AircraftUpdate.as_view(), name="aircraft_update"),
    path("aeronefs/<int:pk>/reprise-configuration/", v.component_attach, name="component_attach"),
    path("types/", v.TypeList.as_view(), name="type_list"),
    path("types/nouveau/", v.TypeCreate.as_view(), name="type_create"),
    path("types/<int:pk>/", v.type_detail, name="type_detail"),
    path("types/<int:pk>/modifier/", v.TypeUpdate.as_view(), name="type_update"),
    path("heures-de-vol/", v.UtilisationList.as_view(), name="utilisation_list"),
    path("heures-de-vol/saisie/", v.utilisation_create, name="utilisation_create"),
    path("pn/", v.PartNumberList.as_view(), name="pn_list"),
    path("pn/nouveau/", v.PartNumberCreate.as_view(), name="pn_create"),
    path("pn/<int:pk>/", v.pn_detail, name="pn_detail"),
    path("pn/<int:pk>/modifier/", v.PartNumberUpdate.as_view(), name="pn_update"),
    path("composants/", v.ComponentList.as_view(), name="component_list"),
    path("composants/nouveau/", v.ComponentCreate.as_view(), name="component_create"),
    path("composants/<int:pk>/", v.component_detail, name="component_detail"),
    path("composants/<int:pk>/modifier/", v.ComponentUpdate.as_view(), name="component_update"),
    path("historique/<str:model>/<int:pk>/", v.object_history, name="history"),
]
