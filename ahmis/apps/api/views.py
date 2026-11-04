"""Points d'accès de l'API externe AHMIS v1.

Toutes les règles métier passent par les mêmes services que l'interface web (aucune logique dupliquée).
Volontairement, AUCUNE signature réglementaire n'est possible par l'API (exécution, contrôle, report de
défaut, CRS) : elles exigent une personne authentifiée qui ressaisit son secret dans AHMIS.
"""
from datetime import date as date_cls

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import exceptions, generics, status
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView, exception_handler

from apps.camo import services as camo
from apps.camo.models import Directive, MaintenanceTask
from apps.fleet.models import Aircraft, Component, PartNumber, UtilisationRecord
from apps.logistics.models import PartRequest, StockItem, Tool
from apps.part145 import services as p145
from apps.part145.models import Defect, Staff, TaskCard, WorkPackage

from . import serializers as s

API_VERSION = "1.0"


def api_exception_handler(exc, context):
    """Convertit les refus métier (ValidationError Django) en réponses 400 lisibles."""
    if isinstance(exc, DjangoValidationError):
        exc = exceptions.ValidationError({"detail": exc.messages})
    return exception_handler(exc, context)


def _int_param(request, name, default, lo, hi):
    try:
        value = int(request.query_params.get(name, default))
    except (TypeError, ValueError):
        raise exceptions.ValidationError({name: "Entier attendu."})
    if not lo <= value <= hi:
        raise exceptions.ValidationError({name: f"Valeur entre {lo} et {hi} attendue."})
    return value


def _date_param(request, name):
    raw = request.query_params.get(name)
    if not raw:
        return None
    try:
        return date_cls.fromisoformat(raw)
    except ValueError:
        raise exceptions.ValidationError({name: "Date AAAA-MM-JJ attendue."})


def _aircraft(registration):
    return get_object_or_404(Aircraft.objects.select_related("aircraft_type"), registration__iexact=registration)


class ApiRoot(APIView):
    """Point d'entrée : version et liste des ressources."""

    read_perms = []

    def get(self, request):
        names = ["aircraft", "due", "forecast", "utilisation", "components", "part-numbers", "tasks", "directives",
                 "defects", "work-packages", "task-cards", "part-requests", "stock", "tools", "staff"]
        return Response({
            "name": "AHMIS API", "version": API_VERSION, "user": request.user.get_username(),
            "resources": {n: reverse(f"api:{n.replace('-', '_')}", request=request) for n in names},
            "schema": reverse("api:schema", request=request),
        })


# ---------------------------------------------------------------------------------------------- flotte
class AircraftList(generics.ListAPIView):
    """Aéronefs. Filtres : ``type`` (code), ``status``."""

    serializer_class = s.AircraftSerializer
    read_perms = ["fleet.view_aircraft"]

    def get_queryset(self):
        qs = Aircraft.objects.select_related("aircraft_type").order_by("registration")
        if self.request.query_params.get("type"):
            qs = qs.filter(aircraft_type__code__iexact=self.request.query_params["type"])
        if self.request.query_params.get("status"):
            qs = qs.filter(status=self.request.query_params["status"])
        return qs


class AircraftDetail(generics.RetrieveAPIView):
    """Un aéronef, par immatriculation."""

    serializer_class = s.AircraftSerializer
    read_perms = ["fleet.view_aircraft"]

    def get_object(self):
        return _aircraft(self.kwargs["registration"])


class AircraftConfiguration(generics.ListAPIView):
    """Composants installés sur l'aéronef, avec leurs potentiels restants."""

    serializer_class = s.ComponentSerializer
    read_perms = ["fleet.view_aircraft", "fleet.view_component"]
    pagination_class = None

    def get_queryset(self):
        ac = _aircraft(self.kwargs["registration"])
        return ac.components.filter(status="installed").select_related("part_number", "aircraft", "location").order_by("position")


class AircraftUtilisation(APIView):
    """GET : saisies d'heures de l'aéronef. POST : nouvelle saisie (vol ou journée), idempotente via ``external_id``."""

    read_perms = ["fleet.view_utilisationrecord"]
    write_perms = ["fleet.add_utilisationrecord"]

    def get(self, request, registration):
        ac = _aircraft(registration)
        qs = ac.utilisation.all()
        since = _date_param(request, "since")
        if since:
            qs = qs.filter(date__gte=since)
        return Response(s.UtilisationSerializer(qs[:1000], many=True).data)

    def post(self, request, registration):
        ac = _aircraft(registration)
        data = s.UtilisationInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        d = data.validated_data
        if d["date"] > timezone.localdate():
            raise exceptions.ValidationError({"date": "Date future interdite."})
        existed = bool(d["external_id"]) and UtilisationRecord.objects.filter(external_id=d["external_id"]).exists()
        with transaction.atomic():
            rec = ac.record_utilisation(d["date"], d["fh"], d["fc"], d["reference"], source="api", external_id=d["external_id"] or None)
        return Response(s.UtilisationSerializer(rec).data, status=status.HTTP_200_OK if existed else status.HTTP_201_CREATED)


class UtilisationList(generics.ListAPIView):
    """Toutes les saisies d'heures. Filtres : ``aircraft``, ``since`` (date)."""

    serializer_class = s.UtilisationSerializer
    read_perms = ["fleet.view_utilisationrecord"]

    def get_queryset(self):
        qs = UtilisationRecord.objects.select_related("aircraft").order_by("-date", "-id")
        if self.request.query_params.get("aircraft"):
            qs = qs.filter(aircraft__registration__iexact=self.request.query_params["aircraft"])
        since = _date_param(self.request, "since")
        if since:
            qs = qs.filter(date__gte=since)
        return qs


class ComponentList(generics.ListAPIView):
    """Composants sérialisés. Filtres : ``pn``, ``sn``, ``status``, ``aircraft``."""

    serializer_class = s.ComponentSerializer
    read_perms = ["fleet.view_component"]

    def get_queryset(self):
        p = self.request.query_params
        qs = Component.objects.select_related("part_number", "aircraft", "location").order_by("part_number__pn", "serial_number")
        if p.get("pn"):
            qs = qs.filter(part_number__pn__iexact=p["pn"])
        if p.get("sn"):
            qs = qs.filter(serial_number__iexact=p["sn"])
        if p.get("status"):
            qs = qs.filter(status=p["status"])
        if p.get("aircraft"):
            qs = qs.filter(aircraft__registration__iexact=p["aircraft"])
        return qs


class ComponentDetail(generics.RetrieveAPIView):
    serializer_class = s.ComponentSerializer
    read_perms = ["fleet.view_component"]
    queryset = Component.objects.select_related("part_number", "aircraft", "location")


class PartNumberList(generics.ListAPIView):
    """Références articles. Filtre : ``q`` (P/N ou désignation)."""

    serializer_class = s.PartNumberSerializer
    read_perms = ["fleet.view_partnumber"]

    def get_queryset(self):
        qs = PartNumber.objects.order_by("pn")
        q = self.request.query_params.get("q")
        if q:
            qs = qs.filter(Q(pn__icontains=q) | Q(description__icontains=q))
        return qs


# ---------------------------------------------------------------------------------------------- CAMO
class DueList(APIView):
    """Échéances calculées (tâches, LLP, TBO, ARC, défauts reportés, consignes).

    Filtres : ``aircraft``, ``status`` (overdue, tolerance, due_soon, ok), ``kind``, ``within`` (jours).
    """

    read_perms = ["camo.view_maintenancetask"]

    def get(self, request, registration=None):
        reg = registration or request.query_params.get("aircraft")
        fleet = [_aircraft(reg)] if reg else None
        items = camo.fleet_due_list(fleet)
        st, kind = request.query_params.get("status"), request.query_params.get("kind")
        if st:
            items = [i for i in items if i.status == st]
        if kind:
            items = [i for i in items if i.kind == kind]
        if request.query_params.get("within"):
            limit = timezone.localdate().toordinal() + _int_param(request, "within", 30, 0, 3650)
            items = [i for i in items if i.projected_date and i.projected_date.toordinal() <= limit]
        return Response({"count": len(items), "generated_at": timezone.now(), "results": [s.due_item_to_dict(i) for i in items]})


class ForecastView(APIView):
    """Forecast : occurrences prévisionnelles et synthèse mensuelle. Paramètres : ``aircraft``, ``horizon`` (jours), ``util`` (%)."""

    read_perms = ["camo.view_maintenancetask"]

    def get(self, request):
        reg = request.query_params.get("aircraft")
        horizon = _int_param(request, "horizon", 365, 7, 1825)
        util = _int_param(request, "util", 100, 10, 300)
        events = camo.forecast([_aircraft(reg)] if reg else None, horizon, utilisation_factor=util / 100)
        summary = camo.forecast_summary(events)
        return Response({
            "horizon_days": horizon, "utilisation_pct": util,
            "months": [{"year": m["year"], "month": m["month"], "count": m["count"], "man_hours": s._num(m["mh"]),
                        "removals": m["removals"], "by_aircraft": m["by_aircraft"],
                        "parts": {k: s._num(v) for k, v in m["parts"].items()}} for m in summary],
            "events": [{"date": e.date, "occurrence": e.occurrence, "overdue": e.overdue, **s.due_item_to_dict(e.item)} for e in events],
        })


class TaskList(generics.ListAPIView):
    """Programme d'entretien. Filtres : ``type``, ``source``, ``active`` (0/1)."""

    serializer_class = s.MaintenanceTaskSerializer
    read_perms = ["camo.view_maintenancetask"]

    def get_queryset(self):
        p = self.request.query_params
        qs = MaintenanceTask.objects.select_related("aircraft_type", "part_number", "directive").order_by("aircraft_type__code", "reference")
        if p.get("type"):
            qs = qs.filter(aircraft_type__code__iexact=p["type"])
        if p.get("source"):
            qs = qs.filter(source=p["source"])
        if p.get("active") in ("0", "1"):
            qs = qs.filter(active=p["active"] == "1")
        return qs


class DirectiveList(generics.ListAPIView):
    """Consignes et bulletins, avec leur statut par aéronef. Filtres : ``kind``, ``status`` (statut d'applicabilité)."""

    serializer_class = s.DirectiveSerializer
    read_perms = ["camo.view_directive"]

    def get_queryset(self):
        qs = Directive.objects.prefetch_related("aircraft_types", "part_numbers", "applicabilities__aircraft").order_by("-effective_date")
        if self.request.query_params.get("kind"):
            qs = qs.filter(kind=self.request.query_params["kind"])
        if self.request.query_params.get("status"):
            qs = qs.filter(applicabilities__status=self.request.query_params["status"]).distinct()
        return qs


class DirectiveDetail(generics.RetrieveAPIView):
    serializer_class = s.DirectiveSerializer
    read_perms = ["camo.view_directive"]
    queryset = Directive.objects.all()
    lookup_field = "number"


# ---------------------------------------------------------------------------------------------- Part-145
class DefectList(generics.ListCreateAPIView):
    """GET : défauts (filtres ``aircraft``, ``status``). POST : signaler un défaut (compte rendu équipage, constat)."""

    serializer_class = s.DefectSerializer
    read_perms = ["part145.view_defect"]
    write_perms = ["part145.add_defect"]

    def get_queryset(self):
        qs = Defect.objects.select_related("aircraft").order_by("-reported_on", "-number")
        if self.request.query_params.get("aircraft"):
            qs = qs.filter(aircraft__registration__iexact=self.request.query_params["aircraft"])
        if self.request.query_params.get("status"):
            qs = qs.filter(status=self.request.query_params["status"])
        return qs

    def perform_create(self, serializer):
        serializer.save(status="open")


class DefectDetail(generics.RetrieveAPIView):
    serializer_class = s.DefectSerializer
    read_perms = ["part145.view_defect"]
    queryset = Defect.objects.select_related("aircraft")
    lookup_field = "number"


class WorkPackageList(generics.ListCreateAPIView):
    """GET : work packages (filtres ``aircraft``, ``status``). POST : créer un WP (statut brouillon ou planifié)."""

    serializer_class = s.WorkPackageSerializer
    read_perms = ["part145.view_workpackage"]
    write_perms = ["part145.add_workpackage"]

    def get_queryset(self):
        qs = WorkPackage.objects.select_related("aircraft", "crs_by").order_by("-planned_start")
        if self.request.query_params.get("aircraft"):
            qs = qs.filter(aircraft__registration__iexact=self.request.query_params["aircraft"])
        if self.request.query_params.get("status"):
            qs = qs.filter(status=self.request.query_params["status"])
        return qs


class WorkPackageDetail(generics.RetrieveAPIView):
    serializer_class = s.WorkPackageDetailSerializer
    read_perms = ["part145.view_workpackage"]
    queryset = WorkPackage.objects.select_related("aircraft", "crs_by")
    lookup_field = "number"


class WorkPackageAddItems(APIView):
    """POST ``{"keys": [...]}`` : crée les task cards à partir des clés d'échéances (champ ``key`` de /due/)."""

    read_perms = ["part145.view_workpackage"]
    write_perms = ["part145.add_taskcard"]

    def post(self, request, number):
        wp = get_object_or_404(WorkPackage, number=number)
        keys = request.data.get("keys")
        if not isinstance(keys, list) or not keys or not all(isinstance(k, str) for k in keys):
            raise exceptions.ValidationError({"keys": "Liste non vide de clés attendue."})
        allowed = {i.key for i in camo.aircraft_due_list(wp.aircraft)}
        unknown = [k for k in keys if k not in allowed]
        if unknown:
            raise exceptions.ValidationError({"keys": f"Clés inconnues pour {wp.aircraft.registration} : {', '.join(unknown[:10])}"})
        with transaction.atomic():
            created = p145.add_due_items_to_wp(wp, keys)
        return Response({"created": s.TaskCardSerializer(created, many=True).data}, status=status.HTTP_201_CREATED)


class TaskCardList(generics.ListAPIView):
    """Task cards. Filtres : ``work_package``, ``aircraft``, ``status``."""

    serializer_class = s.TaskCardSerializer
    read_perms = ["part145.view_taskcard"]

    def get_queryset(self):
        p = self.request.query_params
        qs = TaskCard.objects.select_related("work_package__aircraft", "task", "component__part_number", "defect",
                                             "performed_by", "inspected_by").prefetch_related("steps").order_by("-id")
        if p.get("work_package"):
            qs = qs.filter(work_package__number=p["work_package"])
        if p.get("aircraft"):
            qs = qs.filter(work_package__aircraft__registration__iexact=p["aircraft"])
        if p.get("status"):
            qs = qs.filter(status=p["status"])
        return qs


class TaskCardDetail(generics.RetrieveAPIView):
    serializer_class = s.TaskCardSerializer
    read_perms = ["part145.view_taskcard"]
    queryset = TaskCard.objects.select_related("work_package__aircraft", "task", "defect", "performed_by", "inspected_by")
    lookup_field = "number"


class StaffList(generics.ListAPIView):
    """Personnel et autorisations (données personnelles : réserver ce droit aux systèmes RH / qualité)."""

    serializer_class = s.StaffSerializer
    read_perms = ["part145.view_staff", "part145.view_authorization"]
    queryset = Staff.objects.order_by("last_name", "first_name")


# ---------------------------------------------------------------------------------------------- logistique
class PartRequestList(generics.ListCreateAPIView):
    """GET : demandes de pièces (filtres ``status``, ``priority``). POST : demander une pièce pour une task card."""

    serializer_class = s.PartRequestSerializer
    read_perms = ["logistics.view_partrequest"]
    write_perms = ["logistics.add_partrequest"]

    def get_queryset(self):
        qs = PartRequest.objects.select_related("task_card", "part_number", "issued_component__part_number", "issued_stock__part_number").order_by("-created_at")
        if self.request.query_params.get("status"):
            qs = qs.filter(status=self.request.query_params["status"])
        if self.request.query_params.get("priority"):
            qs = qs.filter(priority=self.request.query_params["priority"])
        return qs


class StockList(generics.ListAPIView):
    """Stock consommables. Filtres : ``pn``, ``status``, ``below_min`` (1)."""

    serializer_class = s.StockSerializer
    read_perms = ["logistics.view_stockitem"]

    def get_queryset(self):
        p = self.request.query_params
        qs = StockItem.objects.select_related("part_number", "location").order_by("part_number__pn")
        if p.get("pn"):
            qs = qs.filter(part_number__pn__iexact=p["pn"])
        if p.get("status"):
            qs = qs.filter(status=p["status"])
        if p.get("below_min") == "1":
            from django.db.models import F

            qs = qs.filter(quantity__lte=F("min_quantity"))
        return qs


class ToolList(generics.ListAPIView):
    """Outillage et état d'étalonnage."""

    serializer_class = s.ToolSerializer
    read_perms = ["logistics.view_tool"]
    queryset = Tool.objects.select_related("checked_out_to").order_by("reference")
