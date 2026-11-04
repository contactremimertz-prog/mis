from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.core.crud import AhmisModelForm
from apps.fleet.models import Aircraft, Component

from .models import AmpReview, TransferRecord, AirworthinessReview, Directive, ModificationRepair, DirectiveApplicability, MaintenanceTask, TaskAccomplishment, TaskRequiredPart


class MaintenanceTaskForm(AhmisModelForm):
    class Meta:
        model = MaintenanceTask
        fields = [
            "reference", "title", "aircraft_type", "source", "directive", "task_type", "ata", "part_number", "effectivity",
            "interval_fh", "interval_fc", "interval_days", "threshold_fh", "threshold_fc", "threshold_days",
            "tolerance_fh", "tolerance_fc", "tolerance_days", "tolerance_reference", "estimated_mh", "zone", "access", "skill",
            "requires_independent_inspection", "amp_revision", "active", "description", "steps",
        ]
        widgets = {"effectivity": forms.CheckboxSelectMultiple}
        help_texts = {
            "interval_days": "Ex. 365 = 12 mois. Le premier critère atteint (FH, cycles, jours) détermine l'échéance.",
            "threshold_fh": "Première échéance depuis neuf si différente de l'intervalle. Pour une tâche liée à une consigne, seuils et intervalle comptent depuis la date d'entrée en vigueur.",
            "steps": "Une étape par ligne : elles deviennent les étapes à signer sur la task card.",
        }

    def clean(self):
        data = super().clean()
        t = data.get("aircraft_type")
        eff = data.get("effectivity")
        if t and eff:
            wrong = [a.registration for a in eff if a.aircraft_type_id != t.pk]
            if wrong:
                raise ValidationError(f"Aéronefs hors type dans l'effectivité : {', '.join(wrong)}")
        return data


class RequiredPartForm(AhmisModelForm):
    class Meta:
        model = TaskRequiredPart
        fields = ["part_number", "quantity"]


class AccomplishmentForm(AhmisModelForm):
    """Reprise d'historique (entrée en flotte) ou travaux réalisés hors AHMIS."""

    class Meta:
        model = TaskAccomplishment
        fields = ["aircraft", "component", "date", "fh", "fc", "comp_fh", "comp_fc", "source", "reference", "certified_by", "notes"]

    def __init__(self, *args, task=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.task = task
        if task is not None:
            self.instance.task = task  # nécessaire au contrôle chronologique (clean du modèle)
        self.fields["source"].choices = [c for c in TaskAccomplishment.SOURCES if c[0] != "taskcard"]
        self.fields["reference"].required = True
        self.fields["certified_by"].required = True
        if task:
            self.fields["aircraft"].queryset = Aircraft.objects.filter(aircraft_type=task.aircraft_type)
            if task.part_number_id:
                self.fields["component"].queryset = Component.objects.filter(part_number=task.part_number)
                self.fields["component"].required = True
            else:
                del self.fields["component"]
                del self.fields["comp_fh"]
                del self.fields["comp_fc"]

    def clean(self):
        data = super().clean()
        ac = data.get("aircraft")
        if ac and data.get("fh") is not None and data["fh"] > ac.total_fh:
            self.add_error("fh", f"Supérieur aux heures actuelles de l'aéronef ({ac.total_fh}).")
        if ac and data.get("fc") is not None and data["fc"] > ac.total_fc:
            self.add_error("fc", f"Supérieur aux cycles actuels de l'aéronef ({ac.total_fc}).")
        if data.get("date") and data["date"] > timezone.localdate():
            self.add_error("date", "Date future interdite.")
        comp = data.get("component")
        if comp and ac and comp.aircraft_id and comp.aircraft_id != ac.pk:
            self.add_error("component", "Ce composant est installé sur un autre aéronef.")
        return data


class DirectiveForm(AhmisModelForm):
    class Meta:
        model = Directive
        fields = ["number", "kind", "authority", "revision", "title", "effective_date", "aircraft_types", "part_numbers",
                  "applicability_text", "required_action", "is_recurring", "related_sb", "supersedes", "document"]
        widgets = {"aircraft_types": forms.CheckboxSelectMultiple, "part_numbers": forms.SelectMultiple(attrs={"size": 6})}


class ApplicabilityForm(AhmisModelForm):
    class Meta:
        model = DirectiveApplicability
        fields = ["status", "justification", "compliance_date", "compliance_fh", "compliance_fc"]
        help_texts = {"status": "Une consigne applicable doit être suivie par une tâche du programme (bouton « Créer la tâche de suivi »)."}


class ArcForm(AhmisModelForm):
    class Meta:
        model = AirworthinessReview
        fields = ["aircraft", "review_type", "reference", "review_date", "expiry_date", "reviewer", "physical_survey", "findings"]


class AmpReviewForm(AhmisModelForm):
    class Meta:
        model = AmpReview
        fields = ["aircraft_type", "review_date", "amp_reference", "revision_before", "reviewer", "reliability_reviewed",
                  "instructions_reviewed", "findings", "outcome", "revision_after", "changes", "approval_type",
                  "approval_reference", "approval_date", "next_review_due"]


class ForecastForm(forms.Form):
    aircraft = forms.ModelChoiceField(Aircraft.objects.exclude(status="retired"), required=False, label="Aéronef", empty_label="Toute la flotte")
    horizon = forms.IntegerField(label="Horizon (jours)", min_value=7, max_value=1825, initial=365)
    util = forms.IntegerField(label="Utilisation (% du prévu)", min_value=10, max_value=300, initial=100,
                              help_text="Simulation : 120 = 20 % d'heures de vol en plus que prévu")


class ModificationForm(AhmisModelForm):
    class Meta:
        model = ModificationRepair
        fields = ["aircraft", "component", "kind", "classification", "title", "ata", "approval_basis", "approval_reference",
                  "directive", "description", "status", "embodied_on", "fh_at_embodiment", "fc_at_embodiment",
                  "ica_reference", "ica_none", "ica_in_amp", "affects_mass_balance", "affects_flight_manual", "follow_up_done",
                  "removed_on", "removal_reason"]
        help_texts = {
            "fh_at_embodiment": "Vide = compteurs actuels de l'aéronef.",
            "ica_in_amp": "Cochez quand les tâches issues des ICA ont été ajoutées au programme d'entretien.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["aircraft"].disabled = True

    def save(self, commit=True):
        obj = super().save(commit=False)
        if obj.status == "embodied" and obj.fh_at_embodiment is None:
            obj.fh_at_embodiment, obj.fc_at_embodiment = obj.aircraft.counters_at(obj.embodied_on)
        if commit:
            obj.save()
        return obj


class TransferForm(AhmisModelForm):
    class Meta:
        model = TransferRecord
        fields = ["aircraft", "direction", "transfer_date", "counterparty", "counterparty_approval", "reason", "archive", "notes"]
        help_texts = {"archive": "Transfert entrant uniquement : archive ZIP reçue. Pour un transfert sortant ou une copie, "
                                 "AHMIS génère l'archive complète du dossier."}

    def clean(self):
        data = super().clean()
        if data.get("direction") == "in" and not data.get("archive"):
            self.add_error("archive", "Joignez l'archive reçue de l'organisme précédent.")
        if data.get("direction") in ("out", "copy") and data.get("archive"):
            self.add_error("archive", "L'archive d'un transfert sortant est générée par AHMIS : ne joignez pas de fichier.")
        f = data.get("archive")
        if f and f.size > 500 * 1024 * 1024:
            self.add_error("archive", "Archive trop volumineuse (500 Mo maximum).")
        return data


class TransferAckForm(forms.Form):
    acknowledged_on = forms.DateField(label="Réception confirmée le", widget=forms.DateInput(attrs={"type": "date"}))
    acknowledged_by = forms.CharField(label="Par (nom, fonction, organisme)", max_length=120)
