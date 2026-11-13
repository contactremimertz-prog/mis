from apps.core.crud import AhmisModelForm

from .models import OccurrenceReport

DECLARATION_FIELDS = ["title", "category", "severity", "phase", "occurred_at", "aware_at", "location", "aircraft", "component",
                      "defect", "task_card", "description", "immediate_actions", "reporter_name", "confidential"]


class DeclarationForm(AhmisModelForm):
    """Déclaration : ouverte à tout le personnel (culture juste)."""

    class Meta:
        model = OccurrenceReport
        fields = DECLARATION_FIELDS


class ProcessingForm(AhmisModelForm):
    """Traitement par le responsable qualité / sécurité : notification, suivi, clôture."""

    class Meta:
        model = OccurrenceReport
        fields = DECLARATION_FIELDS + [
            "status", "authority", "authority_reference", "submitted_at", "late_reason", "design_holder_notified",
            "design_holder_reference", "customer_notified", "not_reportable_reason", "analysis", "corrective_actions",
            "follow_up_at", "closed_on"]
