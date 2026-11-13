from django import forms
from django.utils.translation import gettext_lazy as _

from apps.core.crud import AhmisModelForm
from apps.part145.forms import SignForm

from .models import AuditFinding, ControlledDocument, DocumentRevision, InternalAudit


class AuditForm(AhmisModelForm):
    class Meta:
        model = InternalAudit
        fields = ["title", "scope", "kind", "area", "planned_on", "auditor", "auditor_independent", "performed_on", "summary",
                  "status", "closed_on"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.contrib.auth import get_user_model

        self.fields["auditor"].queryset = get_user_model().objects.filter(is_active=True).order_by("username")


class FindingForm(AhmisModelForm):
    class Meta:
        model = AuditFinding
        fields = ["level", "requirement", "description", "due_date"]


class FindingCloseForm(SignForm):
    root_cause = forms.CharField(label=_("Cause racine"), widget=forms.Textarea(attrs={"rows": 3}), min_length=5)
    corrective_action = forms.CharField(label=_("Action corrective"), widget=forms.Textarea(attrs={"rows": 3}), min_length=5)
    field_order = ["root_cause", "corrective_action", "password"]


class DocumentForm(AhmisModelForm):
    class Meta:
        model = ControlledDocument
        fields = ["reference", "title", "doc_type", "owner", "authority_approval", "review_months"]


class RevisionForm(AhmisModelForm):
    class Meta:
        model = DocumentRevision
        fields = ["revision", "change_summary", "file", "authority_reference"]


class RejectForm(forms.Form):
    reason = forms.CharField(label=_("Motif du refus"), max_length=200)
