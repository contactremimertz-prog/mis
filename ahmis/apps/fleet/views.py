from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone

from apps.camo.models import DirectiveApplicability, TaskAccomplishment
from apps.camo.services import aircraft_due_list, fleet_due_list
from apps.core.crud import AhmisCreateView, AhmisListView, AhmisUpdateView, error_messages
from apps.core.models import AuditLog, SignatureRecord

from .forms import AircraftForm, AircraftTypeForm, ComponentForm, PartNumberForm, UtilisationForm
from .heli3d import ZONE_IDS, fleet_counts, heli_texts, model_for, neighbours, outside_zones, zone_states
from .models import Aircraft, AircraftType, Component, InstallationRecord, PartNumber, UtilisationRecord, install_component
from django.utils.translation import gettext, gettext_lazy


# ---------------------------------------------------------------- Types
class TypeList(AhmisListView):
    model = AircraftType
    columns = [(gettext_lazy("Code"), "code"), (gettext_lazy("Constructeur"), "manufacturer"), (gettext_lazy("Modèle"), "model"), (gettext_lazy("Catégorie"), "category"),
               (gettext_lazy("Cadre"), "regulatory_frame"), (gettext_lazy("Moteurs"), "engine_model"), (gettext_lazy("Aéronefs"), "aircraft.count")]
    search_fields = ["code", "manufacturer", "model"]
    filter_fields = ["category"]
    create_url = reverse_lazy("fleet:type_create")


class TypeCreate(AhmisCreateView):
    model = AircraftType
    form_class = AircraftTypeForm


class TypeUpdate(AhmisUpdateView):
    model = AircraftType
    form_class = AircraftTypeForm

    def get_success_url(self):
        return reverse("fleet:type_detail", args=[self.object.pk])


@permission_required("fleet.view_aircrafttype", raise_exception=True)
def type_detail(request, pk):
    from apps.camo.models import amp_review_status

    t = get_object_or_404(AircraftType, pk=pk)
    return render(request, "fleet/type_detail.html", {
        "t": t,
        "aircraft": t.aircraft.all(),
        "tasks": t.tasks.filter(active=True).order_by("ata", "reference"),
        "pns": t.part_numbers.all(),
        "authorizations": t.authorizations.filter(suspended=False).select_related("staff"),
        "amp_status": amp_review_status(t),
        "amp_reviews": t.amp_reviews.all()[:5],
    })


# ---------------------------------------------------------------- Aéronefs
class AircraftList(AhmisListView):
    model = Aircraft
    queryset = Aircraft.objects.select_related("aircraft_type")
    columns = [(gettext_lazy("Immatriculation"), "registration"), (gettext_lazy("Type"), "aircraft_type.code"), ("MSN", "msn"), (gettext_lazy("Statut"), "status"),
               (gettext_lazy("Exploitant"), "operator"), (gettext_lazy("Base"), "base"), ("FH", "total_fh"), (gettext_lazy("Cycles"), "total_fc"),
               (gettext_lazy("Compteurs au"), "counters_date"), (gettext_lazy("ARC jusqu'au"), "arc_expiry")]
    search_fields = ["registration", "msn", "operator"]
    filter_fields = ["aircraft_type", "status"]
    create_url = reverse_lazy("fleet:aircraft_create")
    title = gettext_lazy("Flotte")
    template_name = "fleet/aircraft_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        page = list(ctx["object_list"])
        helis = [a for a in page if a.aircraft_type.category == "helicopter"]
        counts = fleet_counts(helis, fleet_due_list(helis) if helis else [])
        for a in page:
            a.heli_counts = counts.get(a.pk)
            a.heli_zone_groups = [(k, a.heli_counts[k]) for k in ("crit", "warn", "none")] if a.heli_counts else []
        ctx["object_list"] = page
        ctx["extra_cols"] = 4
        return ctx


class AircraftCreate(AhmisCreateView):
    model = Aircraft
    form_class = AircraftForm
    title = gettext_lazy("Créer un aéronef")


class AircraftUpdate(AhmisUpdateView):
    model = Aircraft
    form_class = AircraftForm


@permission_required("fleet.view_aircraft", raise_exception=True)
def aircraft_detail(request, pk):
    ac = get_object_or_404(Aircraft.objects.select_related("aircraft_type"), pk=pk)
    items = aircraft_due_list(ac)
    is_heli = ac.aircraft_type.category == "helicopter"
    today = timezone.localdate()
    components = []
    for c in ac.components.filter(status="installed").select_related("part_number").order_by("position", "part_number__ata"):
        limits = c.life_status(today)
        worst = min((r["remaining"] for r in limits), default=None)
        components.append({"c": c, "limits": limits, "worst": worst})
    ctx = {
        "ac": ac,
        "today": today,
        "items": items,
        "counts": {s: sum(1 for i in items if i.status == s) for s in ("overdue", "tolerance", "due_soon", "ok")},
        "components": components,
        "directives": DirectiveApplicability.objects.filter(aircraft=ac).select_related("directive").order_by("status", "directive__number"),
        "wps": ac.work_packages.order_by("-planned_start")[:10],
        "defects": ac.defects.exclude(status__in=["rectified", "cancelled"]),
        "utilisation": ac.utilisation.all()[:15],
        "accomplishments": TaskAccomplishment.objects.filter(aircraft=ac).select_related("task", "component__part_number")[:20],
        "installs": InstallationRecord.objects.filter(aircraft=ac).select_related("component__part_number")[:20],
        "reviews": ac.airworthiness_reviews.all()[:5],
        "modifications": ac.modifications.select_related("component__part_number").order_by("-embodied_on"),
        "util_form": UtilisationForm(initial={"aircraft": ac}),
        "heli_zones": zone_states(items) if is_heli else None,
        "heli_outside": outside_zones(items) if is_heli else None,
        "heli_nav": neighbours(ac) if is_heli else None,
        "heli_model": model_for(ac.aircraft_type.code) if is_heli else None,
        "heli_texts": heli_texts() if is_heli else None,
        "heli_zone": request.GET.get("zone") if request.GET.get("zone") in ZONE_IDS else "",
    }
    return render(request, "fleet/aircraft_detail.html", ctx)


# ---------------------------------------------------------------- Utilisation
class UtilisationList(AhmisListView):
    model = UtilisationRecord
    queryset = UtilisationRecord.objects.select_related("aircraft")
    columns = [(gettext_lazy("Date"), "date"), (gettext_lazy("Aéronef"), "aircraft.registration"), ("FH", "fh"), (gettext_lazy("Cycles"), "fc"),
               (gettext_lazy("Total FH après"), "fh_after"), (gettext_lazy("Total cycles après"), "fc_after"), (gettext_lazy("Référence"), "reference"),
               (gettext_lazy("Source"), "source"), (gettext_lazy("Saisi par"), "created_by")]
    search_fields = ["aircraft__registration", "reference"]
    filter_fields = ["aircraft"]
    title = gettext_lazy("Heures de vol et cycles")
    subtitle = gettext_lazy("Chaque saisie incrémente les compteurs de la cellule et de tous les composants installés.")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.user.has_perm("fleet.add_utilisationrecord"):
            ctx["create_url"] = reverse("fleet:utilisation_create")
        return ctx


@permission_required("fleet.add_utilisationrecord", raise_exception=True)
def utilisation_create(request):
    initial = {}
    if request.GET.get("aircraft"):
        initial["aircraft"] = request.GET["aircraft"]
    form = UtilisationForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        try:
            rec = d["aircraft"].record_utilisation(d["date"], d["fh"], d["fc"], d["reference"], source="techlog")
        except ValidationError as e:
            error_messages(request, e)
        else:
            messages.success(request, gettext("{rec} enregistré. Nouveaux totaux : {fh_after} FH / {fc_after} cycles.").format(rec=rec, fh_after=rec.fh_after, fc_after=rec.fc_after))
            if request.POST.get("next"):
                return redirect(request.POST["next"])
            return redirect("fleet:utilisation_create")
    return render(request, "fleet/utilisation_form.html", {"form": form})


# ---------------------------------------------------------------- P/N
class PartNumberList(AhmisListView):
    model = PartNumber
    columns = [("P/N", "pn"), (gettext_lazy("Désignation"), "description"), (gettext_lazy("Constructeur"), "manufacturer"), ("ATA", "ata"),
               (gettext_lazy("Sérialisé"), "is_serialized"), ("LLP", "is_llp"), ("TBO FH", "tbo_fh"), (gettext_lazy("Vie FH"), "life_limit_fh"), (gettext_lazy("Vie cycles"), "life_limit_fc")]
    search_fields = ["pn", "description", "manufacturer"]
    filter_fields = ["is_serialized", "is_llp", "is_rotable"]
    create_url = reverse_lazy("fleet:pn_create")
    title = gettext_lazy("Références articles (P/N)")

    def get_queryset(self):
        qs = super(AhmisListView, self).get_queryset()
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(Q(pn__icontains=q) | Q(description__icontains=q) | Q(manufacturer__icontains=q))
        for f in self.filter_fields:
            v = self.request.GET.get(f)
            if v in ("0", "1"):
                qs = qs.filter(**{f: v == "1"})
        return qs


class PartNumberCreate(AhmisCreateView):
    model = PartNumber
    form_class = PartNumberForm
    title = gettext_lazy("Nouvelle référence article")


class PartNumberUpdate(AhmisUpdateView):
    model = PartNumber
    form_class = PartNumberForm


@permission_required("fleet.view_partnumber", raise_exception=True)
def pn_detail(request, pk):
    pn = get_object_or_404(PartNumber, pk=pk)
    return render(request, "fleet/pn_detail.html", {
        "pn": pn,
        "components": pn.components.select_related("aircraft", "location").order_by("status", "serial_number"),
        "stock": pn.stock_items.select_related("location"),
        "tasks": pn.tasks.select_related("aircraft_type"),
        "directives": pn.directives.all(),
    })


# ---------------------------------------------------------------- Composants
class ComponentList(AhmisListView):
    model = Component
    queryset = Component.objects.select_related("part_number", "aircraft", "location")
    columns = [("P/N", "part_number.pn"), ("S/N", "serial_number"), (gettext_lazy("Désignation"), "part_number.description"),
               (gettext_lazy("Statut"), "status"), (gettext_lazy("Aéronef"), "aircraft.registration"), (gettext_lazy("Position"), "position"),
               (gettext_lazy("Emplacement"), "location.code"), ("TSN", "tsn_fh"), ("CSN", "csn"), ("TSO", "tso_fh")]
    search_fields = ["serial_number", "part_number__pn", "part_number__description", "aircraft__registration"]
    filter_fields = ["status", "aircraft"]
    create_url = reverse_lazy("fleet:component_create")
    title = gettext_lazy("Composants sérialisés")


class ComponentCreate(AhmisCreateView):
    model = Component
    form_class = ComponentForm
    title = gettext_lazy("Nouveau composant")


class ComponentUpdate(AhmisUpdateView):
    model = Component
    form_class = ComponentForm


@permission_required("fleet.view_component", raise_exception=True)
def component_detail(request, pk):
    c = get_object_or_404(Component.objects.select_related("part_number", "aircraft", "location"), pk=pk)
    from apps.logistics.forms import ComponentStatusForm, ScrapForm

    return render(request, "fleet/component_detail.html", {
        "c": c,
        "limits": c.life_status(),
        "certs": c.release_certificates.all(),
        "installs": c.installations.select_related("aircraft", "task_card").order_by("installed_on", "id"),
        "accomplishments": c.accomplishments.select_related("task"),
        "cards": c.task_cards.select_related("work_package"),
        "status_form": ComponentStatusForm(initial={"status": c.status}),
        "scrap_form": ScrapForm(initial={"scrapped_on": timezone.localdate(), "scrap_reason": "life_limit" if c.is_life_expired else "beyond_repair"}),
    })


class AttachForm(forms.Form):
    component = forms.ModelChoiceField(Component.objects.none(), label=gettext_lazy("Composant"))
    position = forms.CharField(label=gettext_lazy("Position"), max_length=40)
    date = forms.DateField(label=gettext_lazy("Date de pose (historique)"), widget=forms.DateInput(attrs={"type": "date"}))
    note = forms.CharField(label=gettext_lazy("Référence documentaire de la reprise"), max_length=150,
                           help_text=gettext_lazy("ex. relevé de configuration, logbook, dossier de transfert"))


@permission_required("fleet.change_aircraft", raise_exception=True)
def component_attach(request, pk):
    """Reprise de configuration initiale (entrée en flotte d'un aéronef) : pose « historique » sans task card."""
    ac = get_object_or_404(Aircraft, pk=pk)
    form = AttachForm(request.POST or None)
    form.fields["component"].queryset = Component.objects.exclude(status__in=["installed", "scrapped"]).select_related("part_number")
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        try:
            install_component(d["component"], ac, d["position"], d["date"], force=True)
            comp = d["component"]
            comp.notes = (comp.notes + "\n" if comp.notes else "") + gettext("Reprise de configuration {registration} : {note}").format(registration=ac.registration, note=d['note'])
            comp.save()
        except ValidationError as e:
            error_messages(request, e)
        else:
            messages.success(request, gettext("{component} rattaché à {registration} ({position}).").format(component=d['component'], registration=ac.registration, position=d['position']))
            return redirect(ac.get_absolute_url())
    return render(request, "core/form.html", {
        "form": form, "title": f"Reprise de configuration – {ac.registration}",
        "subtitle": "À utiliser uniquement à l'entrée en flotte. En exploitation, passez par une task card (changement de composant).",
        "cancel_url": ac.get_absolute_url(),
    })


@permission_required("core.view_auditlog", raise_exception=True)
def object_history(request, model, pk):
    from django.contrib.contenttypes.models import ContentType

    app_label, model_name = model.split(".")
    ct = get_object_or_404(ContentType, app_label=app_label, model=model_name)
    obj = get_object_or_404(ct.model_class(), pk=pk)
    return render(request, "fleet/history.html", {
        "obj": obj,
        "entries": AuditLog.objects.filter(content_type=ct, object_id=str(pk)),
        "signatures": SignatureRecord.objects.filter(content_type=ct, object_id=str(pk)),
    })
