from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.core.crud import AhmisCreateView, AhmisListView, AhmisUpdateView, back, error_messages
from apps.fleet.models import Component
from apps.part145.models import Staff, TaskCard

from .forms import (CalibrationForm, CertificateForm, ComponentStatusForm, ScrapForm, FulfilForm, ReceiveForm, StockAdjustForm,
                    StockItemForm, StoreForm, ToolForm)
from .models import PartRequest, ReleaseCertificate, StockItem, StockMovement, StoreLocation, Tool
from django.utils.translation import gettext, gettext_lazy


# ---------------------------------------------------------------- Réception
@permission_required("logistics.add_releasecertificate", raise_exception=True)
def receive(request):
    form = ReceiveForm(request.POST or None, request.FILES or None, initial={"issue_date": timezone.localdate()})
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        pn = d["part_number"]
        accepted = form.checks_ok
        quarantine = StoreLocation.objects.filter(is_quarantine=True).first()
        with transaction.atomic():
            cert = ReleaseCertificate(
                cert_type=d["cert_type"], tracking_number=d["tracking_number"], issuer=d["issuer"],
                issuer_approval=d["issuer_approval"], issue_date=d["issue_date"], work_status=d["work_status"],
                part_number=pn, serial_or_batch=d["serial_number"] or d["batch"], quantity=d["quantity"],
                remarks=d["remarks"], is_valid=accepted,
                rejection_reason="" if accepted else gettext("Contrôle à réception non conforme"),
            )
            if d.get("document"):
                cert.document = d["document"]
            if pn.is_serialized:
                obj = Component.objects.create(
                    part_number=pn, serial_number=d["serial_number"], condition=d["condition"],
                    manufacture_date=d["manufacture_date"], tsn_fh=d["tsn_fh"] or 0, csn=d["csn"] or 0,
                    tso_fh=d["tso_fh"] or 0, cso=d["cso"] or 0,
                    status="serviceable" if accepted else "quarantine",
                    location=d["location"] if accepted else (quarantine or d["location"]),
                    status_reason="" if accepted else gettext("Réception non conforme – en attente d'analyse"),
                )
                cert.component = obj
                cert.save()
            else:
                obj = StockItem.objects.create(
                    part_number=pn, batch=d["batch"], location=d["location"] if accepted else (quarantine or d["location"]),
                    quantity=d["quantity"], shelf_life_expiry=d["shelf_life_expiry"], supplier=d["supplier"],
                    status="serviceable" if accepted else "quarantine",
                    status_reason="" if accepted else gettext("Réception non conforme – en attente d'analyse"),
                )
                cert.stock_item = obj
                cert.save()
                StockMovement.objects.create(stock_item=obj, kind="receipt", quantity=d["quantity"], note=gettext("Réception {cert}").format(cert=cert))
        if accepted:
            messages.success(request, gettext("{obj} réceptionné et rangé en {location}.").format(obj=obj, location=obj.location))
        else:
            messages.warning(request, gettext("{obj} placé en QUARANTAINE : contrôle à réception incomplet.").format(obj=obj))
        return redirect(obj.get_absolute_url() if hasattr(obj, "get_absolute_url") else "logistics:stock_list")
    return render(request, "logistics/receive.html", {"form": form})


# ---------------------------------------------------------------- Certificats
class CertificateList(AhmisListView):
    model = ReleaseCertificate
    queryset = ReleaseCertificate.objects.select_related("part_number", "component")
    columns = [(gettext_lazy("Type"), "cert_type"), (gettext_lazy("N° de suivi"), "tracking_number"), ("P/N", "part_number.pn"), (gettext_lazy("S/N / lot"), "serial_or_batch"),
               (gettext_lazy("Émetteur"), "issuer"), (gettext_lazy("Date"), "issue_date"), (gettext_lazy("Statut"), "work_status"), (gettext_lazy("Accepté"), "is_valid")]
    search_fields = ["tracking_number", "part_number__pn", "serial_or_batch", "issuer"]
    filter_fields = ["cert_type", "is_valid"]
    create_url = reverse_lazy("logistics:certificate_create")
    title = gettext_lazy("Certificats libératoires")
    link_column = -1


class CertificateCreate(AhmisCreateView):
    model = ReleaseCertificate
    form_class = CertificateForm
    title = gettext_lazy("Enregistrer un certificat libératoire")

    def get_initial(self):
        init = super().get_initial()
        c = Component.objects.filter(pk=self.request.GET.get("component")).first() if self.request.GET.get("component") else None
        if c:
            init.update({"component": c, "part_number": c.part_number, "serial_or_batch": c.serial_number})
        init["issue_date"] = timezone.localdate()
        return init

    def form_valid(self, form):
        try:
            form.instance.full_clean()
        except ValidationError as e:
            for m in e.messages:
                form.add_error(None, m)
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self):
        if self.object.component_id:
            return self.object.component.get_absolute_url()
        return str(reverse_lazy("logistics:certificate_list"))


# ---------------------------------------------------------------- Statut / quarantaine
@require_POST
@permission_required("fleet.change_component", raise_exception=True)
def component_status(request, pk):
    c = get_object_or_404(Component, pk=pk)
    form = ComponentStatusForm(request.POST)
    if not form.is_valid():
        messages.error(request, gettext("Statut et motif obligatoires."))
        return redirect(c.get_absolute_url())
    d = form.cleaned_data
    if c.status == "installed":
        messages.error(request, gettext("Composant installé : passez par une task card pour le déposer."))
        return redirect(c.get_absolute_url())
    if c.status == "scrapped":
        messages.error(request, gettext("Pièce rebutée : statut définitif."))
        return redirect(c.get_absolute_url())
    if d["status"] == "serviceable":
        if not c.has_valid_certificate:
            messages.error(request, gettext("Remise en stock utilisable impossible sans certificat libératoire accepté."))
            return redirect(c.get_absolute_url())
        if c.is_life_expired:
            messages.error(request, gettext("Potentiel épuisé : la pièce ne peut pas redevenir utilisable sans révision."))
            return redirect(c.get_absolute_url())
        if not (d["location"] or c.location) or (d["location"] or c.location).is_quarantine:
            messages.error(request, gettext("Indiquez un emplacement de rangement hors quarantaine."))
            return redirect(c.get_absolute_url())
    if d["status"] == "quarantine" and not d["location"]:
        d["location"] = StoreLocation.objects.filter(is_quarantine=True).first()
    c.status = d["status"]
    c.status_reason = d["reason"] if d["status"] != "serviceable" else ""
    if d["location"]:
        c.location = d["location"]
    c.reserved_for = None
    c.save()
    messages.success(request, f"{c} : {c.get_status_display()}.")
    return redirect(c.get_absolute_url())


@require_POST
@permission_required("fleet.change_component", raise_exception=True)
def component_scrap(request, pk):
    """Mise au rebut définitive d'une pièce non récupérable, avec mutilation et signature (145.A.42(d), M.A.504(d))."""
    from apps.core.identity import verify_signature_secret
    from apps.core.models import SignatureRecord

    c = get_object_or_404(Component, pk=pk)
    form = ScrapForm(request.POST)
    if not form.is_valid():
        messages.error(request, gettext("Formulaire de mise au rebut incomplet : date, motif, méthode et témoin de la mutilation sont obligatoires."))
        return redirect(c.get_absolute_url())
    if c.status in ("installed", "reserved", "scrapped"):
        messages.error(request, gettext("Seule une pièce déposée, non réservée et non déjà rebutée peut être mise au rebut."))
        return redirect(c.get_absolute_url())
    if not verify_signature_secret(request.user, form.cleaned_data["password"]):
        messages.error(request, gettext("Mot de passe ou code de signature incorrect : signature refusée."))
        return redirect(c.get_absolute_url())
    d = form.cleaned_data
    if d["scrapped_on"] > timezone.localdate():
        messages.error(request, gettext("La date de mise au rebut ne peut être dans le futur."))
        return redirect(c.get_absolute_url())
    quarantine_loc = StoreLocation.objects.filter(is_quarantine=True).first()
    with transaction.atomic():
        for f in ("scrapped_on", "scrap_reason", "mutilation_method", "mutilation_witness", "scrap_reference"):
            setattr(c, f, d[f])
        c.status = "scrapped"
        c.status_reason = gettext("Rebuté : {get_scrap_reason_display}").format(get_scrap_reason_display=c.get_scrap_reason_display())
        c.location = quarantine_loc or c.location
        try:
            c.full_clean()
        except ValidationError as e:
            error_messages(request, e)
            return redirect(c.get_absolute_url())
        c.save()
        SignatureRecord.sign(request.user, c, "scrap", f"Mise au rebut définitive de {c} ({c.get_scrap_reason_display()}) le "
                                                     f"{c.scrapped_on:%d/%m/%Y} – mutilation : {c.mutilation_method}, constatée par "
                                                     f"{c.mutilation_witness}{gettext(' – certificat ') + c.scrap_reference if c.scrap_reference else ''}.")
    messages.success(request, gettext("{c} rebuté définitivement ; il ne peut plus réintégrer le circuit d'approvisionnement.").format(c=c))
    return redirect(c.get_absolute_url())


@permission_required("fleet.view_component", raise_exception=True)
def quarantine(request):
    return render(request, "logistics/quarantine.html", {
        "components": Component.objects.filter(status__in=["quarantine", "unserviceable"]).select_related("part_number", "location"),
        "stock": StockItem.objects.filter(status__in=["quarantine", "expired"]).select_related("part_number", "location"),
        "expired": [s for s in StockItem.objects.filter(status="serviceable", shelf_life_expiry__lt=timezone.localdate()).select_related("part_number")],
    })


# ---------------------------------------------------------------- Stock
class StockList(AhmisListView):
    model = StockItem
    queryset = StockItem.objects.select_related("part_number", "location")
    columns = [("P/N", "part_number.pn"), (gettext_lazy("Désignation"), "part_number.description"), (gettext_lazy("Lot"), "batch"), (gettext_lazy("Emplacement"), "location.code"),
               (gettext_lazy("Quantité"), "quantity"), (gettext_lazy("Mini"), "min_quantity"), (gettext_lazy("Péremption"), "shelf_life_expiry"), (gettext_lazy("Statut"), "status")]
    search_fields = ["part_number__pn", "part_number__description", "batch"]
    filter_fields = ["status", "location"]
    title = gettext_lazy("Stock consommables et standard parts")
    subtitle = gettext_lazy("Les entrées se font par la réception (avec certificat) ; les sorties par les demandes de pièces des task cards.")
    link_column = -1

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["extra_actions"] = [(gettext("Réceptionner"), str(reverse_lazy("logistics:receive")))]
        return ctx

    template_name = "logistics/stock_list.html"


class StockUpdate(AhmisUpdateView):
    model = StockItem
    form_class = StockItemForm

    def get_success_url(self):
        return str(reverse_lazy("logistics:stock_list"))


@permission_required("logistics.change_stockitem", raise_exception=True)
def stock_adjust(request, pk):
    s = get_object_or_404(StockItem, pk=pk)
    form = StockAdjustForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        q = form.cleaned_data["quantity"]
        if s.quantity + q < 0:
            messages.error(request, gettext("Le stock ne peut pas devenir négatif."))
        else:
            with transaction.atomic():
                s.quantity += q
                s.save()
                StockMovement.objects.create(stock_item=s, kind="adjust", quantity=q, note=form.cleaned_data["note"])
            messages.success(request, gettext("Inventaire ajusté : {s}.").format(s=s))
            return redirect("logistics:stock_list")
    return render(request, "core/form.html", {"form": form, "title": f"Ajustement d'inventaire – {s}", "cancel_url": "/logistique/stock/"})


# ---------------------------------------------------------------- Demandes de pièces
class RequestList(AhmisListView):
    model = PartRequest
    queryset = PartRequest.objects.select_related("part_number", "task_card__work_package__aircraft")
    columns = [("N°", "number"), (gettext_lazy("Priorité"), "priority"), ("P/N", "part_number.pn"), (gettext_lazy("Désignation"), "part_number.description"), (gettext_lazy("Qté"), "quantity"),
               (gettext_lazy("Task card"), "task_card.number"), (gettext_lazy("Aéronef"), "task_card.work_package.aircraft.registration"), (gettext_lazy("Statut"), "status"), (gettext_lazy("Demandé le"), "created_at")]
    search_fields = ["number", "part_number__pn", "task_card__number"]
    filter_fields = ["status", "priority"]
    title = gettext_lazy("Demandes de pièces")


@require_POST
@permission_required("logistics.add_partrequest", raise_exception=True)
def request_create(request, card_pk):
    from apps.part145.forms import PartRequestForm

    card = get_object_or_404(TaskCard, pk=card_pk)
    if not card.is_editable:
        messages.error(request, gettext("Task card non modifiable."))
        return redirect(card.get_absolute_url())
    form = PartRequestForm(request.POST)
    if form.is_valid():
        pr = form.save(commit=False)
        pr.task_card = card
        pr.save()
        messages.success(request, gettext("Demande {number} transmise au magasin.").format(number=pr.number))
    else:
        messages.error(request, gettext("Demande incomplète."))
    return redirect(card.get_absolute_url())


@permission_required("logistics.view_partrequest", raise_exception=True)
def request_detail(request, pk):
    pr = get_object_or_404(PartRequest.objects.select_related("task_card__work_package__aircraft", "part_number"), pk=pk)
    form = FulfilForm(pr, request.POST or None)
    if request.method == "POST":
        if not request.user.has_perm("logistics.change_partrequest"):
            messages.error(request, gettext("Droit magasin requis."))
        elif request.POST.get("cancel"):
            if pr.status == "requested":
                pr.status = "cancelled"
                pr.save()
                messages.success(request, gettext("Demande annulée."))
        elif form.is_valid():
            try:
                if form.cleaned_data["component"]:
                    pr.fulfil_with_component(form.cleaned_data["component"])
                else:
                    pr.fulfil_with_stock(form.cleaned_data["stock_item"])
            except ValidationError as e:
                error_messages(request, e)
            else:
                messages.success(request, gettext("Demande {number} délivrée.").format(number=pr.number))
                return redirect("logistics:request_detail", pk=pr.pk)
    return render(request, "logistics/request_detail.html", {"pr": pr, "form": form})


# ---------------------------------------------------------------- Outillage
class ToolList(AhmisListView):
    model = Tool
    queryset = Tool.objects.select_related("location", "checked_out_to")
    columns = [(gettext_lazy("Référence"), "reference"), (gettext_lazy("Désignation"), "description"), ("S/N", "serial_number"), (gettext_lazy("Emplacement"), "location.code"),
               (gettext_lazy("Statut"), "status"), (gettext_lazy("Dernier étalonnage"), "last_calibration"), (gettext_lazy("Échéance"), "calibration_due"), (gettext_lazy("Étalonnage OK"), "calibration_ok"), (gettext_lazy("Sorti pour"), "checked_out_to.number")]
    search_fields = ["reference", "description", "serial_number", "part_number"]
    filter_fields = ["status"]
    create_url = reverse_lazy("logistics:tool_create")
    title = gettext_lazy("Outillage")


class ToolCreate(AhmisCreateView):
    model = Tool
    form_class = ToolForm
    title = gettext_lazy("Nouvel outillage")


class ToolUpdate(AhmisUpdateView):
    model = Tool
    form_class = ToolForm


@permission_required("logistics.view_tool", raise_exception=True)
def tool_detail(request, pk):
    t = get_object_or_404(Tool, pk=pk)
    form = CalibrationForm(request.POST or None, initial={"date": timezone.localdate()})
    if request.method == "POST":
        if not request.user.has_perm("logistics.add_toolcalibration"):
            messages.error(request, gettext("Droit requis."))
        elif form.is_valid():
            cal = form.save(commit=False)
            cal.tool = t
            cal.save()
            messages.success(request, gettext("Étalonnage enregistré."))
            return redirect(t.get_absolute_url())
    return render(request, "logistics/tool_detail.html", {
        "t": t, "form": form, "calibrations": t.calibrations.all(), "usages": t.usages.select_related("task_card", "staff")[:30],
    })


@require_POST
@permission_required("part145.execute_taskcard", raise_exception=True)
def tool_checkout(request, card_pk):
    card = get_object_or_404(TaskCard, pk=card_pk)
    tool = get_object_or_404(Tool, pk=request.POST.get("tool"))
    staff = Staff.objects.filter(user=request.user).first()
    if card.status != "in_progress":
        messages.error(request, gettext("La task card doit être en cours."))
    else:
        try:
            tool.check_out(card, staff)
        except ValidationError as e:
            error_messages(request, e)
        else:
            messages.success(request, gettext("{reference} sorti pour {number}.").format(reference=tool.reference, number=card.number))
    return redirect(card.get_absolute_url())


@require_POST
@permission_required("part145.execute_taskcard", raise_exception=True)
def tool_checkin(request, pk):
    tool = get_object_or_404(Tool, pk=pk)
    tool.check_in()
    messages.success(request, gettext("{reference} restitué.").format(reference=tool.reference))
    return back(request, "logistics:tool_list")


# ---------------------------------------------------------------- Magasins
class StoreList(AhmisListView):
    model = StoreLocation
    columns = [(gettext_lazy("Code"), "code"), (gettext_lazy("Désignation"), "name"), (gettext_lazy("Station"), "station"), (gettext_lazy("Quarantaine"), "is_quarantine"), (gettext_lazy("Magasin contrôlé"), "is_bonded")]
    create_url = reverse_lazy("logistics:store_create")
    title = gettext_lazy("Emplacements magasin")
    link_column = -1


class StoreCreate(AhmisCreateView):
    model = StoreLocation
    form_class = StoreForm
    title = gettext_lazy("Nouvel emplacement")

    def get_success_url(self):
        return str(reverse_lazy("logistics:store_list"))
