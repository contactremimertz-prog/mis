"""Achats : fournisseurs acceptés, commandes d'achat (PO) et réception rattachée au certificat libératoire."""
from decimal import Decimal

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _l
from django.views.decorators.http import require_POST

from apps.core.crud import AhmisCreateView, AhmisListView, AhmisModelForm, AhmisUpdateView, error_messages

from .models import PurchaseOrder, PurchaseOrderLine, PurchaseReceipt, ReleaseCertificate, Supplier


# ---------------------------------------------------------------- règles
@transaction.atomic
def send_order(po):
    if po.status != "draft":
        raise ValidationError(_("Seule une commande en brouillon peut être émise."))
    if not po.supplier.approved:
        raise ValidationError(_("Fournisseur non accepté : évaluez-le avant d'émettre la commande (145.A.42)."))
    if not po.lines.exists():
        raise ValidationError(_("Ajoutez au moins une ligne avant d'émettre la commande."))
    po.status = "sent"
    po.ordered_on = po.ordered_on or timezone.localdate()
    po.save()
    return po


@transaction.atomic
def cancel_order(po):
    if po.status in ("received", "cancelled"):
        raise ValidationError(_("Cette commande ne peut plus être annulée."))
    if PurchaseReceipt.objects.filter(line__order=po).exists():
        raise ValidationError(_("Des pièces ont déjà été reçues : la commande ne peut pas être annulée."))
    po.status = "cancelled"
    po.save()
    return po


@transaction.atomic
def receive_line(line, quantity, certificate=None, received_on=None):
    po = PurchaseOrder.objects.select_for_update().get(pk=line.order_id)
    line = PurchaseOrderLine.objects.select_for_update().get(pk=line.pk)
    if po.status not in ("sent", "partial"):
        raise ValidationError(_("La commande doit être émise pour enregistrer une réception."))
    if quantity is None or quantity <= 0:
        raise ValidationError(_("La quantité reçue doit être positive."))
    if quantity > line.remaining:
        raise ValidationError(_("Quantité reçue supérieure au reste à recevoir (%(r)s).") % {"r": f"{line.remaining.normalize():f}"})
    if line.part_number.requires_release_certificate and certificate is None:
        raise ValidationError(_("Élément : un certificat libératoire (EASA Form 1 ou équivalent) accepté en réception est obligatoire."))
    if certificate is not None:
        if certificate.part_number_id != line.part_number_id:
            raise ValidationError(_("Le certificat porte sur un autre P/N."))
        if line.part_number.requires_release_certificate and certificate.cert_type == "coc":
            raise ValidationError(_("Un certificat de conformité ne suffit pas pour un élément : EASA Form 1 ou équivalent requis."))
        if not certificate.is_valid:
            raise ValidationError(_("Ce certificat a été rejeté en réception."))
        used = sum((r.quantity for r in certificate.po_receipts.all()), Decimal("0"))
        if used + quantity > certificate.quantity:
            raise ValidationError(_("La quantité dépasse celle couverte par le certificat."))
    receipt = PurchaseReceipt.objects.create(line=line, quantity=quantity, certificate=certificate,
                                             received_on=received_on or timezone.localdate())
    line.received_quantity += quantity
    line.save(update_fields=["received_quantity", "updated_at"])
    po.refresh_status()
    return receipt


# ---------------------------------------------------------------- formulaires
class SupplierForm(AhmisModelForm):
    class Meta:
        model = Supplier
        fields = ["name", "kind", "approval_reference", "approved", "evaluated_on", "contact"]


class OrderForm(AhmisModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ["supplier", "expected_on", "notes"]


class LineForm(AhmisModelForm):
    class Meta:
        model = PurchaseOrderLine
        fields = ["part_number", "quantity", "part_request"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import PartRequest

        self.fields["part_request"].queryset = PartRequest.objects.filter(status="requested").select_related("part_number")


class ReceiveForm(forms.Form):
    quantity = forms.DecimalField(label=_l("Quantité reçue"), min_value=Decimal("0.01"), max_digits=10, decimal_places=2)
    certificate = forms.ModelChoiceField(label=_l("Certificat libératoire"), required=False, queryset=ReleaseCertificate.objects.none())
    received_on = forms.DateField(label=_l("Reçu le"), widget=forms.DateInput(attrs={"type": "date"}), required=False)

    def __init__(self, line=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if line is not None:
            self.fields["certificate"].queryset = ReleaseCertificate.objects.filter(part_number=line.part_number, is_valid=True).order_by("-issue_date")


# ---------------------------------------------------------------- vues
class SupplierList(AhmisListView):
    model = Supplier
    columns = [(_l("Fournisseur"), "name"), (_l("Type"), "kind"), (_l("N° d'agrément"), "approval_reference"),
               (_l("Accepté"), "approved"), (_l("Évalué le"), "evaluated_on")]
    search_fields = ["name", "approval_reference"]
    filter_fields = ["kind", "approved"]
    create_url = reverse_lazy("logistics:supplier_create")
    title = _l("Fournisseurs")
    subtitle = _l("Seuls les fournisseurs acceptés après évaluation peuvent recevoir une commande.")


class SupplierCreate(AhmisCreateView):
    model = Supplier
    form_class = SupplierForm


class SupplierUpdate(AhmisUpdateView):
    model = Supplier
    form_class = SupplierForm


class OrderList(AhmisListView):
    model = PurchaseOrder
    queryset = PurchaseOrder.objects.select_related("supplier")
    columns = [(_l("N°"), "number"), (_l("Fournisseur"), "supplier"), (_l("Commandée le"), "ordered_on"),
               (_l("Livraison prévue"), "expected_on"), (_l("Statut"), "status")]
    search_fields = ["number", "supplier__name", "notes", "lines__part_number__pn"]
    filter_fields = ["status", "supplier"]
    create_url = reverse_lazy("logistics:po_create")
    title = _l("Commandes d'achat")
    subtitle = _l("Commande à un fournisseur accepté, réception rattachée au certificat libératoire contrôlé.")

    def get_queryset(self):
        return super().get_queryset().distinct()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["extra_actions"] = [(_("Fournisseurs"), reverse_lazy("logistics:supplier_list"))]
        return ctx


class OrderCreate(AhmisCreateView):
    model = PurchaseOrder
    form_class = OrderForm
    title = _l("Nouvelle commande d'achat")


class OrderUpdate(AhmisUpdateView):
    model = PurchaseOrder
    form_class = OrderForm

    def get_queryset(self):
        return PurchaseOrder.objects.filter(status="draft")


@permission_required("logistics.view_purchaseorder", raise_exception=True)
def po_detail(request, pk):
    po = get_object_or_404(PurchaseOrder.objects.select_related("supplier"), pk=pk)
    lines = list(po.lines.select_related("part_number", "part_request"))
    for line in lines:
        line.receive_form = ReceiveForm(line, prefix=f"l{line.pk}")
        line.receipts_list = list(line.receipts.select_related("certificate"))
    return render(request, "logistics/po_detail.html", {"po": po, "lines": lines, "line_form": LineForm()})


@require_POST
@permission_required("logistics.change_purchaseorder", raise_exception=True)
def po_line_add(request, pk):
    po = get_object_or_404(PurchaseOrder, pk=pk)
    if po.status != "draft":
        messages.error(request, _("Lignes modifiables uniquement en brouillon."))
        return redirect(po.get_absolute_url())
    form = LineForm(request.POST, instance=PurchaseOrderLine(order=po))
    if form.is_valid():
        form.save()
        messages.success(request, _("Ligne ajoutée."))
    else:
        for errs in form.errors.values():
            for e in errs:
                messages.error(request, e)
    return redirect(po.get_absolute_url())


@require_POST
@permission_required("logistics.change_purchaseorder", raise_exception=True)
def po_action(request, pk, action):
    po = get_object_or_404(PurchaseOrder.objects.select_related("supplier"), pk=pk)
    fn = {"send": send_order, "cancel": cancel_order}.get(action)
    if fn is None:
        return redirect(po.get_absolute_url())
    try:
        fn(po)
    except ValidationError as e:
        error_messages(request, e)
    else:
        messages.success(request, _("Commande %(n)s : %(s)s.") % {"n": po.number, "s": po.get_status_display()})
    return redirect(po.get_absolute_url())


@require_POST
@permission_required("logistics.add_purchasereceipt", raise_exception=True)
def po_receive(request, line_pk):
    line = get_object_or_404(PurchaseOrderLine.objects.select_related("order", "part_number"), pk=line_pk)
    form = ReceiveForm(line, request.POST, prefix=f"l{line.pk}")
    if form.is_valid():
        d = form.cleaned_data
        try:
            receive_line(line, d["quantity"], d["certificate"], d["received_on"])
        except ValidationError as e:
            error_messages(request, e)
        else:
            messages.success(request, _("Réception enregistrée sur %(n)s.") % {"n": line.order.number})
    else:
        for errs in form.errors.values():
            for e in errs:
                messages.error(request, e)
    return redirect(line.order.get_absolute_url())
