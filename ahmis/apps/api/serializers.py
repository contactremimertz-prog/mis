"""Représentations JSON exposées par l'API (v1).

Les champs sont listés explicitement : un champ ajouté à un modèle n'est jamais exposé par accident.
Les références entre objets utilisent des identifiants métier (immatriculation, P/N, numéro de WP)
plutôt que des clés techniques, pour être stables d'une base à l'autre.
"""
from decimal import Decimal

from rest_framework import serializers

from apps.camo.models import Directive, DirectiveApplicability, MaintenanceTask
from apps.fleet.models import Aircraft, AircraftType, Component, PartNumber, UtilisationRecord
from apps.logistics.models import PartRequest, StockItem, Tool
from apps.part145.models import Defect, Staff, TaskCard, WorkPackage


class AircraftTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AircraftType
        fields = ["code", "manufacturer", "model", "category", "regulatory_frame", "engine_count", "engine_model", "cycle_label"]


class AircraftSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source="aircraft_type.code")
    manufacturer = serializers.CharField(source="aircraft_type.manufacturer")
    category = serializers.CharField(source="aircraft_type.category")

    class Meta:
        model = Aircraft
        fields = ["registration", "msn", "type", "manufacturer", "category", "status", "operator", "owner", "base",
                  "manufacture_date", "entry_into_service", "total_fh", "total_fc", "counters_date",
                  "planned_daily_fh", "planned_daily_fc", "arc_expiry"]


class UtilisationSerializer(serializers.ModelSerializer):
    aircraft = serializers.CharField(source="aircraft.registration", read_only=True)

    class Meta:
        model = UtilisationRecord
        fields = ["id", "aircraft", "date", "fh", "fc", "reference", "external_id", "source", "fh_after", "fc_after", "created_at"]
        read_only_fields = ["id", "aircraft", "source", "fh_after", "fc_after", "created_at"]


class UtilisationInputSerializer(serializers.Serializer):
    date = serializers.DateField()
    fh = serializers.DecimalField(max_digits=7, decimal_places=2, min_value=Decimal("0"), max_value=Decimal("24"))
    fc = serializers.IntegerField(min_value=0, max_value=500)
    reference = serializers.CharField(max_length=60, required=False, allow_blank=True, default="")
    external_id = serializers.CharField(max_length=80, required=False, allow_blank=True, default="",
                                        help_text="Identifiant unique côté émetteur : un renvoi n'est pas recompté")


class PartNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartNumber
        fields = ["pn", "description", "manufacturer", "ata", "unit", "is_serialized", "is_rotable", "is_llp",
                  "life_limit_fh", "life_limit_fc", "life_limit_days", "tbo_fh", "tbo_fc", "tbo_days"]


class ComponentSerializer(serializers.ModelSerializer):
    pn = serializers.CharField(source="part_number.pn")
    description = serializers.CharField(source="part_number.description")
    aircraft = serializers.CharField(source="aircraft.registration", default=None)
    location = serializers.CharField(source="location.code", default=None)
    limits = serializers.SerializerMethodField()

    class Meta:
        model = Component
        fields = ["id", "pn", "serial_number", "description", "status", "condition", "aircraft", "position", "location",
                  "tsn_fh", "csn", "tso_fh", "cso", "manufacture_date", "last_overhaul_date", "limits"]

    def get_limits(self, obj):
        return [{"kind": r["kind"], "label": r["label"], "limit": _num(r["limit"]), "used": _num(r["used"]),
                 "remaining": _num(r["remaining"]), "unit": r["unit"]} for r in obj.life_status()]


class DirectiveApplicabilitySerializer(serializers.ModelSerializer):
    aircraft = serializers.CharField(source="aircraft.registration")

    class Meta:
        model = DirectiveApplicability
        fields = ["aircraft", "status", "justification", "compliance_date", "compliance_fh", "compliance_fc", "reviewed_by", "reviewed_on"]


class DirectiveSerializer(serializers.ModelSerializer):
    aircraft_types = serializers.SlugRelatedField(many=True, read_only=True, slug_field="code")
    part_numbers = serializers.SlugRelatedField(many=True, read_only=True, slug_field="pn")
    applicability = DirectiveApplicabilitySerializer(source="applicabilities", many=True, read_only=True)

    class Meta:
        model = Directive
        fields = ["number", "kind", "authority", "revision", "title", "effective_date", "aircraft_types", "part_numbers",
                  "applicability_text", "required_action", "is_recurring", "related_sb", "applicability"]


class MaintenanceTaskSerializer(serializers.ModelSerializer):
    aircraft_type = serializers.CharField(source="aircraft_type.code")
    part_number = serializers.CharField(source="part_number.pn", default=None)
    directive = serializers.CharField(source="directive.number", default=None)

    class Meta:
        model = MaintenanceTask
        fields = ["id", "reference", "title", "aircraft_type", "source", "directive", "task_type", "ata", "part_number",
                  "interval_fh", "interval_fc", "interval_days", "threshold_fh", "threshold_fc", "threshold_days",
                  "tolerance_fh", "tolerance_fc", "tolerance_days", "estimated_mh", "skill", "requires_independent_inspection",
                  "amp_revision", "active"]


class DefectSerializer(serializers.ModelSerializer):
    aircraft = serializers.SlugRelatedField(slug_field="registration", queryset=Aircraft.objects.all())

    class Meta:
        model = Defect
        fields = ["number", "aircraft", "reported_on", "reported_by", "source", "techlog_ref", "ata", "description", "status",
                  "mel_reference", "deferral_category", "deferral_limit_date", "deferral_limit_fh", "deferral_limit_fc",
                  "rectification", "rectified_on"]
        read_only_fields = ["number", "status", "mel_reference", "deferral_category", "deferral_limit_date", "deferral_limit_fh",
                            "deferral_limit_fc", "rectification", "rectified_on"]


class TaskCardSerializer(serializers.ModelSerializer):
    work_package = serializers.CharField(source="work_package.number")
    aircraft = serializers.CharField(source="work_package.aircraft.registration")
    task = serializers.CharField(source="task.reference", default=None)
    component = serializers.CharField(source="component.__str__", default=None)
    defect = serializers.CharField(source="defect.number", default=None)
    performed_by = serializers.CharField(source="performed_by.full_name", default=None)
    inspected_by = serializers.CharField(source="inspected_by.full_name", default=None)
    steps = serializers.CharField(source="steps_progress")

    class Meta:
        model = TaskCard
        fields = ["number", "work_package", "aircraft", "origin", "task", "component", "defect", "title", "ata", "skill",
                  "requires_independent_inspection", "estimated_mh", "actual_mh", "status", "steps", "work_done",
                  "performed_by", "performed_at", "inspected_by", "inspected_at", "deferral_reason"]


class WorkPackageSerializer(serializers.ModelSerializer):
    aircraft = serializers.SlugRelatedField(slug_field="registration", queryset=Aircraft.objects.all())
    progress = serializers.IntegerField(read_only=True)
    crs_by = serializers.CharField(source="crs_by.full_name", default=None, read_only=True)

    class Meta:
        model = WorkPackage
        fields = ["number", "aircraft", "title", "check_type", "station", "planned_start", "planned_end", "status",
                  "ordered_by", "customer_order", "progress", "fh_at_check", "fc_at_check", "crs_by", "crs_date", "crs_statement"]
        read_only_fields = ["number", "progress", "fh_at_check", "fc_at_check", "crs_by", "crs_date", "crs_statement"]

    def validate_status(self, value):
        if value == "released":
            raise serializers.ValidationError("Le CRS ne peut être signé que dans AHMIS (signature électronique personnelle).")
        return value

    def validate(self, data):
        start, end = data.get("planned_start"), data.get("planned_end")
        if start and end and end < start:
            raise serializers.ValidationError("La fin prévue précède le début.")
        return data


class WorkPackageDetailSerializer(WorkPackageSerializer):
    task_cards = TaskCardSerializer(many=True, read_only=True)

    class Meta(WorkPackageSerializer.Meta):
        fields = WorkPackageSerializer.Meta.fields + ["task_cards"]


class PartRequestSerializer(serializers.ModelSerializer):
    task_card = serializers.SlugRelatedField(slug_field="number", queryset=TaskCard.objects.all())
    part_number = serializers.SlugRelatedField(slug_field="pn", queryset=PartNumber.objects.all())
    issued_component = serializers.CharField(source="issued_component.__str__", default=None, read_only=True)
    issued_stock = serializers.CharField(source="issued_stock.__str__", default=None, read_only=True)

    class Meta:
        model = PartRequest
        fields = ["number", "task_card", "part_number", "quantity", "priority", "status", "note", "issued_component", "issued_stock", "created_at"]
        read_only_fields = ["number", "status", "issued_component", "issued_stock", "created_at"]

    def validate_task_card(self, card):
        if not card.is_editable:
            raise serializers.ValidationError("Task card non modifiable (clôturée ou WP verrouillé).")
        return card

    def validate_quantity(self, q):
        if q <= 0:
            raise serializers.ValidationError("La quantité doit être positive.")
        return q


class StockSerializer(serializers.ModelSerializer):
    pn = serializers.CharField(source="part_number.pn")
    description = serializers.CharField(source="part_number.description")
    unit = serializers.CharField(source="part_number.unit")
    location = serializers.CharField(source="location.code")

    class Meta:
        model = StockItem
        fields = ["id", "pn", "description", "batch", "location", "quantity", "unit", "min_quantity", "shelf_life_expiry", "status"]


class ToolSerializer(serializers.ModelSerializer):
    calibration_due = serializers.DateField(read_only=True)
    calibration_ok = serializers.BooleanField(read_only=True)
    checked_out_to = serializers.CharField(source="checked_out_to.number", default=None)

    class Meta:
        model = Tool
        fields = ["reference", "description", "part_number", "serial_number", "status", "calibration_required",
                  "last_calibration", "calibration_due", "calibration_ok", "checked_out_to"]


class StaffSerializer(serializers.ModelSerializer):
    authorizations = serializers.SerializerMethodField()

    class Meta:
        model = Staff
        fields = ["employee_number", "first_name", "last_name", "role", "licence_number", "licence_categories",
                  "licence_expiry", "active", "authorizations"]

    def get_authorizations(self, obj):
        return [{"number": a.number, "aircraft_type": a.aircraft_type.code, "category": a.category, "certifying": a.certifying,
                 "valid_from": a.valid_from, "valid_until": a.valid_until, "valid": a.is_valid}
                for a in obj.authorizations.select_related("aircraft_type")]


def _num(v):
    """Décimal -> nombre JSON (entier si possible)."""
    if v is None:
        return None
    if isinstance(v, Decimal):
        return int(v) if v == v.to_integral() else float(v)
    return v


def due_item_to_dict(i):
    """Échéance calculée (apps.camo.services.DueItem) -> dictionnaire JSON."""
    return {
        "aircraft": i.aircraft.registration, "kind": i.kind, "reference": i.reference, "label": i.label,
        "status": i.status, "status_label": i.status_label, "key": i.key,
        "last_date": i.last_date, "last_fh": _num(i.last_fh), "last_fc": _num(i.last_fc),
        "due_fh": _num(i.due_fh), "due_fc": _num(i.due_fc), "due_date": i.due_date,
        "remaining_fh": _num(i.remaining_fh), "remaining_fc": _num(i.remaining_fc), "remaining_days": i.remaining_days,
        "projected_date": i.projected_date, "driver": i.driver, "estimated_mh": _num(i.estimated_mh),
        "parts": [{"pn": pn.pn, "quantity": _num(q)} for pn, q in i.parts],
    }
