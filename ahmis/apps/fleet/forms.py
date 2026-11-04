from django import forms
from django.utils import timezone

from apps.core.crud import AhmisModelForm

from .models import Aircraft, AircraftType, Component, PartNumber
from django.utils.translation import gettext, gettext_lazy


class AircraftTypeForm(AhmisModelForm):
    class Meta:
        model = AircraftType
        fields = ["code", "manufacturer", "model", "category", "regulatory_frame", "engine_count", "engine_model", "cycle_label", "mtow_kg", "notes"]


class AircraftForm(AhmisModelForm):
    class Meta:
        model = Aircraft
        fields = [
            "registration", "msn", "aircraft_type", "status", "operator", "owner", "base",
            "manufacture_date", "entry_into_service", "total_fh", "total_fc", "counters_date",
            "planned_daily_fh", "planned_daily_fc", "cofa_number", "withdrawn_on", "notes",
        ]
        help_texts = {
            "total_fh": gettext_lazy("Heures cellule à la date « compteurs à jour au ». Ensuite, utilisez la saisie des heures de vol."),
            "planned_daily_fh": gettext_lazy("Sert au calcul des dates prévisionnelles et au forecast."),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # Les compteurs ne se modifient plus directement : traçabilité via les saisies d'utilisation.
            for f in ("total_fh", "total_fc", "counters_date"):
                self.fields[f].disabled = True
                self.fields[f].help_text = gettext("Modifiable uniquement par une saisie d'heures de vol.")


class UtilisationForm(forms.Form):
    aircraft = forms.ModelChoiceField(Aircraft.objects.exclude(status="retired"), label=gettext_lazy("Aéronef"))
    date = forms.DateField(label=gettext_lazy("Date"), widget=forms.DateInput(attrs={"type": "date"}), initial=timezone.localdate)
    fh = forms.DecimalField(label="Heures de vol (décimal, ex. 1.5 = 1 h 30)", min_value=0, max_digits=7, decimal_places=2)
    fc = forms.IntegerField(label=gettext_lazy("Cycles / atterrissages"), min_value=0)
    reference = forms.CharField(label=gettext_lazy("Référence (page techlog, CRM…)"), required=False, max_length=60)

    def clean(self):
        data = super().clean()
        if data.get("fh") is not None and data["fh"] > 24:
            self.add_error("fh", gettext("Plus de 24 h sur une journée : vérifiez la saisie."))
        if data.get("date") and data["date"] > timezone.localdate():
            self.add_error("date", gettext("La date ne peut pas être dans le futur."))
        return data


class PartNumberForm(AhmisModelForm):
    class Meta:
        model = PartNumber
        fields = [
            "pn", "description", "category", "specification", "manufacturer", "ata", "unit", "is_serialized", "is_rotable", "is_llp", "is_tool",
            "shelf_life_controlled", "life_limit_fh", "life_limit_fc", "life_limit_days", "tbo_fh", "tbo_fc", "tbo_days",
            "applicable_types", "alternates", "notes",
        ]
        widgets = {"applicable_types": forms.CheckboxSelectMultiple, "alternates": forms.SelectMultiple(attrs={"size": 6})}


class ComponentForm(AhmisModelForm):
    class Meta:
        model = Component
        fields = [
            "part_number", "serial_number", "condition", "manufacture_date", "last_overhaul_date",
            "tsn_fh", "csn", "tso_fh", "cso", "location", "notes",
        ]
        help_texts = {"location": gettext_lazy("Les composants sont créés en stock. La pose se fait depuis une task card (changement de composant).")}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["part_number"].queryset = PartNumber.objects.filter(is_serialized=True)
        if self.instance.pk:
            for f in ("part_number", "serial_number", "tsn_fh", "csn", "tso_fh", "cso"):
                self.fields[f].disabled = True

    def save(self, commit=True):
        obj = super().save(commit=False)
        if not obj.pk:
            obj.status = "quarantine" if not obj.location_id else "serviceable"
            if obj.status == "quarantine":
                obj.status_reason = gettext("Création sans emplacement : en attente de réception")
        if commit:
            obj.save()
            self.save_m2m()
        return obj
