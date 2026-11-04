from django import forms
from django.db.models import Q
from django.utils import timezone

from apps.core.crud import AhmisModelForm
from apps.fleet.models import Component
from apps.logistics.models import PartRequest, Tool

from .models import Authorization, Defect, ExperienceRecord, Qualification, Staff, TaskCard, WorkPackage
from django.utils.translation import gettext, gettext_lazy


class WorkPackageForm(AhmisModelForm):
    class Meta:
        model = WorkPackage
        fields = ["aircraft", "title", "check_type", "station", "planned_start", "planned_end", "status", "ordered_by", "customer_order", "notes"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Le CRS se signe depuis la fiche : le statut « remis en service » n'est pas saisissable.
        self.fields["status"].choices = [c for c in WorkPackage.STATUSES if c[0] != "released"]
        if self.instance.pk:
            self.fields["aircraft"].disabled = True


class AdhocCardForm(AhmisModelForm):
    class Meta:
        model = TaskCard
        fields = ["title", "ata", "zone", "access", "instructions", "skill", "requires_independent_inspection", "estimated_mh"]


class AddTaskForm(forms.Form):
    task = forms.ModelChoiceField(queryset=None, label=gettext_lazy("Tâche du programme"))

    def __init__(self, wp, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.camo.models import MaintenanceTask

        self.fields["task"].queryset = MaintenanceTask.objects.filter(aircraft_type=wp.aircraft.aircraft_type, active=True, part_number__isnull=True)


class SignForm(forms.Form):
    password = forms.CharField(label=gettext_lazy("Mot de passe ou code de signature"), widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}))


class PerformForm(SignForm):
    work_done = forms.CharField(label=gettext_lazy("Compte rendu des travaux"), widget=forms.Textarea(attrs={"rows": 3}))
    actual_mh = forms.DecimalField(label=gettext_lazy("Temps passé (h.h)"), min_value=0, max_digits=6, decimal_places=2)
    field_order = ["work_done", "actual_mh", "password"]


class StepForm(SignForm):
    measured_value = forms.CharField(label=gettext_lazy("Valeur relevée"), required=False, max_length=100)
    not_applicable = forms.BooleanField(label="N/A", required=False)


class ReasonForm(SignForm):
    reason = forms.CharField(label=gettext_lazy("Motif"), max_length=200)
    field_order = ["reason", "password"]


class DefectForm(AhmisModelForm):
    class Meta:
        model = Defect
        fields = ["aircraft", "reported_on", "reported_by", "source", "techlog_ref", "ata", "description"]


class DeferForm(SignForm):
    mel_reference = forms.CharField(label=gettext_lazy("Référence MEL / CDL"), max_length=40, required=False)
    category = forms.ChoiceField(label=gettext_lazy("Catégorie"), choices=Defect.CATEGORIES)
    limit_date = forms.DateField(label=gettext_lazy("Limite (date)"), required=False, widget=forms.DateInput(attrs={"type": "date"}),
                                 help_text="Vide = délai standard de la catégorie (B 3 j, C 10 j, D 120 j)")
    limit_fh = forms.DecimalField(label=gettext_lazy("Limite (FH aéronef)"), required=False, max_digits=10, decimal_places=2)
    limit_fc = forms.IntegerField(label=gettext_lazy("Limite (cycles aéronef)"), required=False, min_value=0)
    procedure = forms.CharField(label=gettext_lazy("Procédures (O)/(M) appliquées, placards"), required=False, widget=forms.Textarea(attrs={"rows": 2}))
    field_order = ["mel_reference", "category", "limit_date", "limit_fh", "limit_fc", "procedure", "password"]


class ExtendDeferralForm(SignForm):
    new_date = forms.DateField(label=gettext_lazy("Nouvelle limite (date)"), required=False, widget=forms.DateInput(attrs={"type": "date"}))
    new_fh = forms.DecimalField(label=gettext_lazy("Nouvelle limite (FH aéronef)"), required=False, max_digits=10, decimal_places=2)
    new_fc = forms.IntegerField(label=gettext_lazy("Nouvelle limite (cycles aéronef)"), required=False, min_value=0)
    reference = forms.CharField(label=gettext_lazy("Référence RIE"), max_length=40)
    reason = forms.CharField(label=gettext_lazy("Justification"), widget=forms.Textarea(attrs={"rows": 2}))
    authority_notified = forms.BooleanField(label=gettext_lazy("Autorité informée"), required=False)
    field_order = ["new_date", "new_fh", "new_fc", "reference", "reason", "authority_notified", "password"]


class StaffForm(AhmisModelForm):
    class Meta:
        model = Staff
        fields = ["user", "employee_number", "first_name", "last_name", "role", "stamp", "licence_number", "licence_categories", "licence_expiry", "active", "left_on"]


class AuthorizationForm(AhmisModelForm):
    class Meta:
        model = Authorization
        fields = ["number", "aircraft_type", "category", "certifying", "scope", "valid_from", "valid_until", "suspended"]


class QualificationForm(AhmisModelForm):
    class Meta:
        model = Qualification
        fields = ["category", "name", "obtained", "expiry"]


class ExperienceForm(AhmisModelForm):
    class Meta:
        model = ExperienceRecord
        fields = ["start", "end", "aircraft_type", "organisation", "description", "evidence"]


class PartRequestForm(AhmisModelForm):
    class Meta:
        model = PartRequest
        fields = ["part_number", "quantity", "priority", "note"]


class ToolCheckoutForm(forms.Form):
    tool = forms.ModelChoiceField(Tool.objects.none(), label=gettext_lazy("Outillage disponible"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tool"].queryset = Tool.objects.filter(status="available")


class ComponentChangeForm(SignForm):
    removed = forms.ModelChoiceField(Component.objects.none(), label=gettext_lazy("Composant déposé"), required=False)
    removal_reason = forms.CharField(label=gettext_lazy("Motif de dépose"), max_length=200, required=False)
    removal_type = forms.ChoiceField(label=gettext_lazy("Type de dépose"), choices=[("unscheduled", gettext_lazy("Non programmée (panne)")), ("scheduled", gettext_lazy("Programmée (butée)")), ("convenience", gettext_lazy("Commodité / robbery"))])
    removed_status = forms.ChoiceField(label=gettext_lazy("Statut du composant déposé"), choices=[("unserviceable", gettext_lazy("Non utilisable (U/S)")), ("quarantine", gettext_lazy("Quarantaine")), ("serviceable", gettext_lazy("Utilisable (dépose de commodité)"))])
    installed = forms.ModelChoiceField(Component.objects.none(), label=gettext_lazy("Composant posé"), required=False)
    position = forms.CharField(label=gettext_lazy("Position"), max_length=40, required=False)

    def __init__(self, card, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ac = card.aircraft
        self.fields["removed"].queryset = ac.components.filter(status="installed").select_related("part_number")
        self.fields["installed"].queryset = Component.objects.filter(
            Q(status="serviceable") | Q(status="reserved", reserved_for=card)
        ).select_related("part_number")

    def clean(self):
        data = super().clean()
        if not data.get("removed") and not data.get("installed"):
            raise forms.ValidationError(gettext("Indiquez au moins un composant déposé ou posé."))
        if data.get("removed") and not data.get("removal_reason"):
            self.add_error("removal_reason", gettext("Motif obligatoire."))
        if data.get("installed") and not data.get("removed") and not data.get("position"):
            self.add_error("position", gettext("Position obligatoire pour une pose seule."))
        return data


class PlanForm(forms.Form):
    title = forms.CharField(label=gettext_lazy("Intitulé"), max_length=150)
    planned_start = forms.DateField(label=gettext_lazy("Début"), widget=forms.DateInput(attrs={"type": "date"}), initial=timezone.localdate)
    planned_end = forms.DateField(label=gettext_lazy("Fin"), widget=forms.DateInput(attrs={"type": "date"}))
