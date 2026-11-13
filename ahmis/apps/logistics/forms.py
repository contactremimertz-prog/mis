from django import forms

from apps.core.uploads import scan_validators
from django.utils import timezone

from apps.core.crud import AhmisModelForm
from apps.fleet.models import Component, PartNumber

from .models import ReleaseCertificate, StockItem, StoreLocation, Tool, ToolCalibration
from django.utils.translation import gettext, gettext_lazy


class ReceiveForm(forms.Form):
    """Réception magasin : pièce + certificat libératoire + contrôle à réception."""

    part_number = forms.ModelChoiceField(PartNumber.objects.filter(is_tool=False), label=gettext_lazy("P/N reçu"))
    serial_number = forms.CharField(label=gettext_lazy("S/N (pièce sérialisée)"), max_length=60, required=False)
    batch = forms.CharField(label=gettext_lazy("N° de lot (consommable)"), max_length=60, required=False)
    quantity = forms.DecimalField(label=gettext_lazy("Quantité"), min_value=0.01, max_digits=10, decimal_places=2, initial=1)
    location = forms.ModelChoiceField(StoreLocation.objects.filter(is_quarantine=False), label=gettext_lazy("Emplacement de rangement"))
    supplier = forms.CharField(label=gettext_lazy("Fournisseur"), max_length=120, required=False)
    shelf_life_expiry = forms.DateField(label=gettext_lazy("Date de péremption"), required=False, widget=forms.DateInput(attrs={"type": "date"}))
    condition = forms.ChoiceField(label=gettext_lazy("État"), choices=Component.CONDITIONS, initial="new")
    manufacture_date = forms.DateField(label=gettext_lazy("Date de fabrication"), required=False, widget=forms.DateInput(attrs={"type": "date"}))
    tsn_fh = forms.DecimalField(label=gettext_lazy("TSN (h)"), required=False, max_digits=10, decimal_places=2, initial=0)
    csn = forms.IntegerField(label="CSN", required=False, min_value=0, initial=0)
    tso_fh = forms.DecimalField(label=gettext_lazy("TSO (h)"), required=False, max_digits=10, decimal_places=2, initial=0)
    cso = forms.IntegerField(label="CSO", required=False, min_value=0, initial=0)
    # Certificat
    cert_type = forms.ChoiceField(label=gettext_lazy("Type de certificat"), choices=ReleaseCertificate.TYPES)
    tracking_number = forms.CharField(label=gettext_lazy("N° de suivi du certificat"), max_length=60)
    issuer = forms.CharField(label=gettext_lazy("Organisme émetteur"), max_length=120)
    issuer_approval = forms.CharField(label=gettext_lazy("N° d'agrément émetteur"), max_length=60, required=False)
    issue_date = forms.DateField(label=gettext_lazy("Date du certificat"), widget=forms.DateInput(attrs={"type": "date"}))
    work_status = forms.ChoiceField(label=gettext_lazy("Statut / travaux (case 11)"), choices=ReleaseCertificate.STATUSES)
    document = forms.FileField(label=gettext_lazy("Scan du certificat"), required=False, validators=scan_validators())
    # Contrôle à réception
    check_identity = forms.BooleanField(label=gettext_lazy("P/N, S/N / lot et quantité conformes au certificat"), required=False)
    check_certificate = forms.BooleanField(label=gettext_lazy("Certificat complet, signé, émetteur agréé"), required=False)
    check_condition = forms.BooleanField(label=gettext_lazy("Aucun dommage, conditionnement correct"), required=False)
    remarks = forms.CharField(label=gettext_lazy("Remarques de réception"), required=False, widget=forms.Textarea(attrs={"rows": 2}))

    def clean(self):
        d = super().clean()
        pn = d.get("part_number")
        if not pn:
            return d
        if pn.is_serialized:
            if not d.get("serial_number"):
                self.add_error("serial_number", gettext("S/N obligatoire pour une pièce sérialisée."))
            elif Component.objects.filter(part_number=pn, serial_number=d["serial_number"]).exists():
                self.add_error("serial_number", gettext("Ce couple P/N – S/N existe déjà : doublon ou pièce suspecte."))
            if d.get("quantity") and d["quantity"] != 1:
                self.add_error("quantity", gettext("Une pièce sérialisée se réceptionne à l'unité."))
        if d.get("cert_type") and pn.requires_release_certificate and d["cert_type"] not in PartNumber.RELEASE_CERTS:
            self.add_error("cert_type", f"{pn.pn} est un élément (component) : un certificat libératoire autorisé (EASA Form 1 "
                                        "ou équivalent) est exigé, un certificat de conformité ne suffit pas (145.A.42).")
        if pn.shelf_life_controlled and not d.get("shelf_life_expiry"):
            self.add_error("shelf_life_expiry", gettext("Date de péremption obligatoire pour cet article."))
        if d.get("issue_date") and d["issue_date"] > timezone.localdate():
            self.add_error("issue_date", gettext("Date de certificat dans le futur."))
        return d

    @property
    def checks_ok(self):
        d = self.cleaned_data
        return all(d.get(k) for k in ("check_identity", "check_certificate", "check_condition"))


class CertificateForm(AhmisModelForm):
    class Meta:
        model = ReleaseCertificate
        fields = ["cert_type", "tracking_number", "issuer", "issuer_approval", "issue_date", "work_status", "part_number",
                  "serial_or_batch", "quantity", "component", "stock_item", "remarks", "document", "is_valid", "rejection_reason"]


class ComponentStatusForm(forms.Form):
    status = forms.ChoiceField(label=gettext_lazy("Nouveau statut"), choices=[c for c in Component.STATUSES if c[0] not in ("installed", "reserved", "scrapped")])
    location = forms.ModelChoiceField(StoreLocation.objects.all(), label=gettext_lazy("Emplacement"), required=False)
    reason = forms.CharField(label=gettext_lazy("Motif"), max_length=200)


class ScrapForm(forms.Form):
    scrapped_on = forms.DateField(label=gettext_lazy("Date"), widget=forms.DateInput(attrs={"type": "date"}))
    scrap_reason = forms.ChoiceField(label=gettext_lazy("Motif"), choices=Component.SCRAP_REASONS)
    mutilation_method = forms.CharField(label=gettext_lazy("Méthode de mutilation"), max_length=150)
    mutilation_witness = forms.CharField(label=gettext_lazy("Mutilation constatée par"), max_length=120)
    scrap_reference = forms.CharField(label=gettext_lazy("Réf. certificat de destruction"), max_length=60, required=False)
    password = forms.CharField(label=gettext_lazy("Mot de passe ou code de signature"), widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}))


class StockItemForm(AhmisModelForm):
    class Meta:
        model = StockItem
        fields = ["part_number", "batch", "location", "min_quantity", "shelf_life_expiry", "status", "status_reason", "supplier"]


class StockAdjustForm(forms.Form):
    quantity = forms.DecimalField(label=gettext_lazy("Quantité (+ entrée / − sortie)"), max_digits=10, decimal_places=2)
    note = forms.CharField(label=gettext_lazy("Justification"), max_length=200)


class StoreForm(AhmisModelForm):
    class Meta:
        model = StoreLocation
        fields = ["code", "name", "station", "is_quarantine", "is_bonded"]


class ToolForm(AhmisModelForm):
    class Meta:
        model = Tool
        fields = ["reference", "description", "part_number", "serial_number", "location", "status", "calibration_required", "calibration_interval_days", "last_calibration"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["status"].choices = [c for c in Tool.STATUSES if c[0] != "checked_out"]
        if self.instance.pk and self.instance.status == "checked_out":
            self.fields["status"].disabled = True
            self.fields["status"].choices = Tool.STATUSES
        if self.instance.pk:
            self.fields["last_calibration"].disabled = True
            self.fields["last_calibration"].help_text = gettext("Mis à jour par l'enregistrement d'un étalonnage.")


class CalibrationForm(AhmisModelForm):
    class Meta:
        model = ToolCalibration
        fields = ["date", "provider", "certificate_ref", "result"]


class FulfilForm(forms.Form):
    component = forms.ModelChoiceField(Component.objects.none(), label=gettext_lazy("Composant à délivrer"), required=False)
    stock_item = forms.ModelChoiceField(StockItem.objects.none(), label=gettext_lazy("Lot à délivrer"), required=False)

    def __init__(self, request_obj, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pns = request_obj.acceptable_part_numbers()
        self.fields["component"].queryset = Component.objects.filter(part_number__in=pns, status="serviceable").select_related("part_number", "location")
        self.fields["stock_item"].queryset = StockItem.objects.filter(part_number__in=pns, status="serviceable", quantity__gt=0).select_related("part_number", "location")

    def clean(self):
        d = super().clean()
        if bool(d.get("component")) == bool(d.get("stock_item")):
            raise forms.ValidationError(gettext("Choisissez soit un composant, soit un lot."))
        return d
