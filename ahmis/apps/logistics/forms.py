from django import forms
from django.utils import timezone

from apps.core.crud import AhmisModelForm
from apps.fleet.models import Component, PartNumber

from .models import ReleaseCertificate, StockItem, StoreLocation, Tool, ToolCalibration


class ReceiveForm(forms.Form):
    """Réception magasin : pièce + certificat libératoire + contrôle à réception."""

    part_number = forms.ModelChoiceField(PartNumber.objects.filter(is_tool=False), label="P/N reçu")
    serial_number = forms.CharField(label="S/N (pièce sérialisée)", max_length=60, required=False)
    batch = forms.CharField(label="N° de lot (consommable)", max_length=60, required=False)
    quantity = forms.DecimalField(label="Quantité", min_value=0.01, max_digits=10, decimal_places=2, initial=1)
    location = forms.ModelChoiceField(StoreLocation.objects.filter(is_quarantine=False), label="Emplacement de rangement")
    supplier = forms.CharField(label="Fournisseur", max_length=120, required=False)
    shelf_life_expiry = forms.DateField(label="Date de péremption", required=False, widget=forms.DateInput(attrs={"type": "date"}))
    condition = forms.ChoiceField(label="État", choices=Component.CONDITIONS, initial="new")
    manufacture_date = forms.DateField(label="Date de fabrication", required=False, widget=forms.DateInput(attrs={"type": "date"}))
    tsn_fh = forms.DecimalField(label="TSN (h)", required=False, max_digits=10, decimal_places=2, initial=0)
    csn = forms.IntegerField(label="CSN", required=False, min_value=0, initial=0)
    tso_fh = forms.DecimalField(label="TSO (h)", required=False, max_digits=10, decimal_places=2, initial=0)
    cso = forms.IntegerField(label="CSO", required=False, min_value=0, initial=0)
    # Certificat
    cert_type = forms.ChoiceField(label="Type de certificat", choices=ReleaseCertificate.TYPES)
    tracking_number = forms.CharField(label="N° de suivi du certificat", max_length=60)
    issuer = forms.CharField(label="Organisme émetteur", max_length=120)
    issuer_approval = forms.CharField(label="N° d'agrément émetteur", max_length=60, required=False)
    issue_date = forms.DateField(label="Date du certificat", widget=forms.DateInput(attrs={"type": "date"}))
    work_status = forms.ChoiceField(label="Statut / travaux (case 11)", choices=ReleaseCertificate.STATUSES)
    document = forms.FileField(label="Scan du certificat", required=False)
    # Contrôle à réception
    check_identity = forms.BooleanField(label="P/N, S/N / lot et quantité conformes au certificat", required=False)
    check_certificate = forms.BooleanField(label="Certificat complet, signé, émetteur agréé", required=False)
    check_condition = forms.BooleanField(label="Aucun dommage, conditionnement correct", required=False)
    remarks = forms.CharField(label="Remarques de réception", required=False, widget=forms.Textarea(attrs={"rows": 2}))

    def clean(self):
        d = super().clean()
        pn = d.get("part_number")
        if not pn:
            return d
        if pn.is_serialized:
            if not d.get("serial_number"):
                self.add_error("serial_number", "S/N obligatoire pour une pièce sérialisée.")
            elif Component.objects.filter(part_number=pn, serial_number=d["serial_number"]).exists():
                self.add_error("serial_number", "Ce couple P/N – S/N existe déjà : doublon ou pièce suspecte.")
            if d.get("quantity") and d["quantity"] != 1:
                self.add_error("quantity", "Une pièce sérialisée se réceptionne à l'unité.")
        if d.get("cert_type") and pn.requires_release_certificate and d["cert_type"] not in PartNumber.RELEASE_CERTS:
            self.add_error("cert_type", f"{pn.pn} est un élément (component) : un certificat libératoire autorisé (EASA Form 1 "
                                        "ou équivalent) est exigé, un certificat de conformité ne suffit pas (145.A.42).")
        if pn.shelf_life_controlled and not d.get("shelf_life_expiry"):
            self.add_error("shelf_life_expiry", "Date de péremption obligatoire pour cet article.")
        if d.get("issue_date") and d["issue_date"] > timezone.localdate():
            self.add_error("issue_date", "Date de certificat dans le futur.")
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
    status = forms.ChoiceField(label="Nouveau statut", choices=[c for c in Component.STATUSES if c[0] not in ("installed", "reserved", "scrapped")])
    location = forms.ModelChoiceField(StoreLocation.objects.all(), label="Emplacement", required=False)
    reason = forms.CharField(label="Motif", max_length=200)


class ScrapForm(forms.Form):
    scrapped_on = forms.DateField(label="Date", widget=forms.DateInput(attrs={"type": "date"}))
    scrap_reason = forms.ChoiceField(label="Motif", choices=Component.SCRAP_REASONS)
    mutilation_method = forms.CharField(label="Méthode de mutilation", max_length=150)
    mutilation_witness = forms.CharField(label="Mutilation constatée par", max_length=120)
    scrap_reference = forms.CharField(label="Réf. certificat de destruction", max_length=60, required=False)
    password = forms.CharField(label="Mot de passe ou code de signature", widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}))


class StockItemForm(AhmisModelForm):
    class Meta:
        model = StockItem
        fields = ["part_number", "batch", "location", "min_quantity", "shelf_life_expiry", "status", "status_reason", "supplier"]


class StockAdjustForm(forms.Form):
    quantity = forms.DecimalField(label="Quantité (+ entrée / − sortie)", max_digits=10, decimal_places=2)
    note = forms.CharField(label="Justification", max_length=200)


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
            self.fields["last_calibration"].help_text = "Mis à jour par l'enregistrement d'un étalonnage."


class CalibrationForm(AhmisModelForm):
    class Meta:
        model = ToolCalibration
        fields = ["date", "provider", "certificate_ref", "result"]


class FulfilForm(forms.Form):
    component = forms.ModelChoiceField(Component.objects.none(), label="Composant à délivrer", required=False)
    stock_item = forms.ModelChoiceField(StockItem.objects.none(), label="Lot à délivrer", required=False)

    def __init__(self, request_obj, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pns = request_obj.acceptable_part_numbers()
        self.fields["component"].queryset = Component.objects.filter(part_number__in=pns, status="serviceable").select_related("part_number", "location")
        self.fields["stock_item"].queryset = StockItem.objects.filter(part_number__in=pns, status="serviceable", quantity__gt=0).select_related("part_number", "location")

    def clean(self):
        d = super().clean()
        if bool(d.get("component")) == bool(d.get("stock_item")):
            raise forms.ValidationError("Choisissez soit un composant, soit un lot.")
        return d
