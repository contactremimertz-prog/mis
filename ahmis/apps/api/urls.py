"""Routes de l'API v1 (préfixe /api/v1/).

Les vues sont marquées « login_not_required » : la redirection vers la page de connexion du site
ne s'applique pas à l'API, qui authentifie elle-même chaque requête (jeton ou session).
"""
from django.contrib.auth.decorators import login_not_required
from django.urls import path
from rest_framework.schemas import get_schema_view

from . import views as v

app_name = "api"


def p(route, view_cls, name):
    return path(route, login_not_required(view_cls.as_view()), name=name)


schema_view = get_schema_view(
    title="AHMIS API", version=v.API_VERSION,
    description="API externe d'AHMIS : flotte, heures de vol, échéances, forecast, consignes, défauts, work packages, logistique.",
)

urlpatterns = [
    p("", v.ApiRoot, "root"),
    path("schema/", login_not_required(schema_view), name="schema"),
    p("aircraft/", v.AircraftList, "aircraft"),
    p("aircraft/<str:registration>/", v.AircraftDetail, "aircraft_detail"),
    p("aircraft/<str:registration>/configuration/", v.AircraftConfiguration, "aircraft_configuration"),
    p("aircraft/<str:registration>/utilisation/", v.AircraftUtilisation, "aircraft_utilisation"),
    p("aircraft/<str:registration>/due/", v.DueList, "aircraft_due"),
    p("utilisation/", v.UtilisationList, "utilisation"),
    p("due/", v.DueList, "due"),
    p("forecast/", v.ForecastView, "forecast"),
    p("components/", v.ComponentList, "components"),
    p("components/<int:pk>/", v.ComponentDetail, "component_detail"),
    p("part-numbers/", v.PartNumberList, "part_numbers"),
    p("tasks/", v.TaskList, "tasks"),
    p("directives/", v.DirectiveList, "directives"),
    p("directives/<str:number>/", v.DirectiveDetail, "directive_detail"),
    p("defects/", v.DefectList, "defects"),
    p("defects/<str:number>/", v.DefectDetail, "defect_detail"),
    p("work-packages/", v.WorkPackageList, "work_packages"),
    p("work-packages/<str:number>/", v.WorkPackageDetail, "work_package_detail"),
    p("work-packages/<str:number>/items/", v.WorkPackageAddItems, "work_package_items"),
    p("task-cards/", v.TaskCardList, "task_cards"),
    p("task-cards/<str:number>/", v.TaskCardDetail, "task_card_detail"),
    p("part-requests/", v.PartRequestList, "part_requests"),
    p("stock/", v.StockList, "stock"),
    p("tools/", v.ToolList, "tools"),
    p("staff/", v.StaffList, "staff"),
]
