import csv

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone

from apps.core.crud import AhmisCreateView, AhmisListView, AhmisUpdateView, error_messages
from apps.fleet.models import Aircraft

from . import services
from .forms import TransferAckForm, TransferForm, AmpReviewForm, AccomplishmentForm, ModificationForm, ApplicabilityForm, ArcForm, DirectiveForm, ForecastForm, MaintenanceTaskForm, RequiredPartForm
from .models import TransferRecord, AmpReview, amp_review_status, ModificationRepair, AirworthinessReview, Directive, DirectiveApplicability, MaintenanceTask, TaskRequiredPart
from django.utils.translation import gettext, gettext_lazy

MONTHS = ["", "janvier", gettext_lazy("février"), "mars", "avril", "mai", "juin", "juillet", gettext_lazy("août"), "septembre", "octobre", "novembre", gettext_lazy("décembre")]


# ---------------------------------------------------------------- Échéances
def _due_filters(request):
    aircraft = None
    if request.GET.get("aircraft"):
        aircraft = get_object_or_404(Aircraft, pk=request.GET["aircraft"])
    return aircraft, request.GET.get("status", ""), request.GET.get("kind", ""), request.GET.get("within", "")


def _filtered_due(request):
    aircraft, status, kind, within = _due_filters(request)
    items = services.fleet_due_list([aircraft] if aircraft else None)
    if status:
        items = [i for i in items if i.status == status or (status == "overdue" and i.status == "tolerance")]
    if kind:
        items = [i for i in items if i.kind == kind or (kind == "task" and i.kind == "component_task")]
    if within:
        limit = timezone.localdate().toordinal() + int(within)
        items = [i for i in items if i.projected_date and i.projected_date.toordinal() <= limit]
    return aircraft, items


@permission_required("camo.view_maintenancetask", raise_exception=True)
def due(request):
    aircraft, items = _filtered_due(request)
    from apps.part145.models import WorkPackage

    open_wps = WorkPackage.objects.filter(aircraft=aircraft, status__in=["draft", "planned", "in_progress"]) if aircraft else []
    return render(request, "camo/due.html", {
        "items": items,
        "aircraft": aircraft,
        "fleet": Aircraft.objects.exclude(status="retired"),
        "statuses": list(services.STATUS_LABELS.items()),
        "kinds": [("task", "Tâches"), ("llp", "LLP"), ("tbo", "TBO"), ("arc", "ARC"), ("defect", "Défauts reportés"), ("directive", "Consignes")],
        "open_wps": open_wps,
        "can_plan": request.user.has_perm("part145.add_taskcard"),
        "counts": {s: sum(1 for i in items if i.status == s) for s in services.STATUS_LABELS},
    })


@permission_required("camo.view_maintenancetask", raise_exception=True)
def due_csv(request):
    aircraft, items = _filtered_due(request)
    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="echeances_{timezone.localdate():%Y%m%d}.csv"'
    resp.write("﻿")
    w = csv.writer(resp, delimiter=";")
    w.writerow([gettext("Statut"), gettext("Aéronef"), gettext("Nature"), gettext("Référence"), gettext("Libellé"), gettext("Dernière réalisation"), gettext("Butée FH"), gettext("Butée cycles"),
                gettext("Butée date"), gettext("Reste FH"), gettext("Reste cycles"), gettext("Date prévue"), gettext("Jours restants"), gettext("Critère"), gettext("Charge h.h")])
    for i in items:
        w.writerow([i.status_label, i.aircraft.registration, i.kind_label, i.reference, i.label,
                    i.last_date.strftime("%d/%m/%Y") if i.last_date else "", _n(i.due_fh), _n(i.due_fc),
                    i.due_date.strftime("%d/%m/%Y") if i.due_date else "", _n(i.remaining_fh), _n(i.remaining_fc),
                    i.projected_date.strftime("%d/%m/%Y") if i.projected_date else "", _n(i.remaining_days), i.driver, _n(i.estimated_mh)])
    return resp


def _n(v):
    return "" if v is None else str(v).replace(".", ",")


# ---------------------------------------------------------------- Forecast
@permission_required("camo.view_maintenancetask", raise_exception=True)
def forecast(request):
    form = ForecastForm(request.GET or None, initial={"horizon": 365, "util": 100})
    aircraft, horizon, util = None, 365, 100
    if form.is_bound and form.is_valid():
        aircraft = form.cleaned_data["aircraft"]
        horizon = form.cleaned_data["horizon"] or 365
        util = form.cleaned_data["util"] or 100
    elif request.GET.get("aircraft"):
        aircraft = Aircraft.objects.filter(pk=request.GET["aircraft"]).first()
        form = ForecastForm(initial={"aircraft": aircraft, "horizon": 365, "util": 100})
    events = services.forecast([aircraft] if aircraft else None, horizon, utilisation_factor=util / 100)
    summary = services.forecast_summary(events)
    max_mh = max((m["mh"] for m in summary), default=0) or 1
    for m in summary:
        m["label"] = f"{MONTHS[m['month']]} {m['year']}"
        m["pct"] = int(m["mh"] * 100 / max_mh)
        m["events"] = [e for e in events if e.date.year == m["year"] and e.date.month == m["month"]]
        m["parts_list"] = sorted(m["parts"].items())
    if request.GET.get("format") == "csv":
        resp = HttpResponse(content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = f'attachment; filename="forecast_{timezone.localdate():%Y%m%d}.csv"'
        resp.write("﻿")
        w = csv.writer(resp, delimiter=";")
        w.writerow([gettext("Date prévue"), gettext("Aéronef"), gettext("Nature"), gettext("Référence"), gettext("Libellé"), gettext("Occurrence"), gettext("Critère"), gettext("Charge h.h"), gettext("Pièces")])
        for e in events:
            w.writerow([e.date.strftime("%d/%m/%Y"), e.item.aircraft.registration, e.item.kind_label, e.item.reference, e.item.label,
                        e.occurrence, e.item.driver, _n(e.item.estimated_mh), ", ".join(f"{p.pn} x{q}" for p, q in e.item.parts)])
        return resp
    return render(request, "camo/forecast.html", {
        "form": form, "events": events, "summary": summary, "aircraft": aircraft, "horizon": horizon, "util": util,
        "total_mh": sum((m["mh"] for m in summary), 0), "total_events": len(events),
        "total_removals": sum(m["removals"] for m in summary),
    })


# ---------------------------------------------------------------- Programme d'entretien
class TaskList(AhmisListView):
    model = MaintenanceTask
    queryset = MaintenanceTask.objects.select_related("aircraft_type", "part_number")
    columns = [(gettext_lazy("Référence"), "reference"), (gettext_lazy("Intitulé"), "title"), (gettext_lazy("Type"), "aircraft_type.code"), ("ATA", "ata"),
               (gettext_lazy("Origine"), "source"), (gettext_lazy("Nature"), "task_type"), (gettext_lazy("Intervalle"), "interval_display"), (gettext_lazy("Seuil"), "threshold_display"),
               (gettext_lazy("Composant"), "part_number.pn"), ("h.h", "estimated_mh"), (gettext_lazy("Active"), "active")]
    search_fields = ["reference", "title", "ata", "description"]
    filter_fields = ["aircraft_type", "source", "task_type"]
    create_url = reverse_lazy("camo:task_create")
    title = gettext_lazy("Programme d'entretien")
    subtitle = gettext_lazy("Tâches MSM/MPD, limitations de navigabilité (ALS), consignes et bulletins suivis.")


class TaskCreate(AhmisCreateView):
    model = MaintenanceTask
    form_class = MaintenanceTaskForm
    title = gettext_lazy("Nouvelle tâche d'entretien")

    def get_initial(self):
        init = super().get_initial()
        for k in ("aircraft_type", "directive", "source"):
            if self.request.GET.get(k):
                init[k] = self.request.GET[k]
        if self.request.GET.get("directive"):
            d = Directive.objects.filter(pk=self.request.GET["directive"]).first()
            if d:
                init.update({"reference": d.number, "title": d.title, "source": "AD" if d.kind in ("AD", "EAD") else "SB",
                             "description": d.required_action})
        return init


class TaskUpdate(AhmisUpdateView):
    model = MaintenanceTask
    form_class = MaintenanceTaskForm


@permission_required("camo.view_maintenancetask", raise_exception=True)
def task_detail(request, pk):
    task = get_object_or_404(MaintenanceTask.objects.select_related("aircraft_type", "directive", "part_number"), pk=pk)
    rows = []
    for ac in Aircraft.objects.filter(aircraft_type=task.aircraft_type).exclude(status="retired"):
        if not task.applies_to(ac):
            continue
        if task.part_number_id:
            for comp in ac.components.filter(status="installed", part_number=task.part_number):
                it = services.task_due(task, ac, comp)
                rows.append({"ac": ac, "comp": comp, "item": it})
        else:
            rows.append({"ac": ac, "comp": None, "item": services.task_due(task, ac)})
    return render(request, "camo/task_detail.html", {
        "task": task,
        "rows": rows,
        "accomplishments": task.accomplishments.select_related("aircraft", "component", "task_card")[:50],
        "required_parts": task.required_parts.select_related("part_number"),
        "part_form": RequiredPartForm(),
    })


@permission_required("camo.change_maintenancetask", raise_exception=True)
def task_add_part(request, pk):
    task = get_object_or_404(MaintenanceTask, pk=pk)
    form = RequiredPartForm(request.POST)
    if form.is_valid():
        rp = form.save(commit=False)
        rp.task = task
        rp.save()
        messages.success(request, gettext("Pièce {rp} ajoutée à la tâche.").format(rp=rp))
    else:
        messages.error(request, gettext("Saisie invalide."))
    return redirect(task.get_absolute_url())


@permission_required("camo.change_maintenancetask", raise_exception=True)
def task_remove_part(request, pk, part_pk):
    rp = get_object_or_404(TaskRequiredPart, pk=part_pk, task_id=pk)
    if request.method == "POST":
        rp.delete()
        messages.success(request, gettext("Pièce retirée."))
    return redirect(rp.task.get_absolute_url())


@permission_required("camo.add_taskaccomplishment", raise_exception=True)
def task_record(request, pk):
    task = get_object_or_404(MaintenanceTask, pk=pk)
    initial = {"date": timezone.localdate(), "source": "initial"}
    if request.GET.get("aircraft"):
        initial["aircraft"] = request.GET["aircraft"]
    form = AccomplishmentForm(request.POST or None, task=task, initial=initial)
    if request.method == "POST" and form.is_valid():
        acc = form.save(commit=False)
        acc.task = task
        acc.save()
        messages.success(request, gettext("Réalisation enregistrée : {acc}.").format(acc=acc))
        return redirect(task.get_absolute_url())
    return render(request, "core/form.html", {
        "form": form, "title": f"Enregistrer une réalisation – {task.reference}",
        "subtitle": "Reprise d'historique ou travaux réalisés par un organisme externe (avec référence du CRS). "
                    "Les travaux réalisés dans AHMIS sont enregistrés automatiquement à la clôture de la task card.",
        "cancel_url": task.get_absolute_url(),
    })


# ---------------------------------------------------------------- Consignes
class DirectiveList(AhmisListView):
    model = Directive
    columns = [(gettext_lazy("Numéro"), "number"), (gettext_lazy("Type"), "kind"), (gettext_lazy("Émetteur"), "authority"), (gettext_lazy("Objet"), "title"),
               (gettext_lazy("En vigueur le"), "effective_date"), (gettext_lazy("Types"), "aircraft_types"), (gettext_lazy("Répétitive"), "is_recurring")]
    search_fields = ["number", "title", "applicability_text"]
    filter_fields = ["kind", "authority"]
    create_url = reverse_lazy("camo:directive_create")
    title = gettext_lazy("Consignes de navigabilité et bulletins service")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["extra_actions"] = [(gettext("Statut par aéronef"), reverse("camo:directive_status_list"))]
        return ctx


class DirectiveCreate(AhmisCreateView):
    model = Directive
    form_class = DirectiveForm
    title = gettext_lazy("Nouvelle consigne / bulletin")

    def form_valid(self, form):
        resp = super().form_valid(form)
        n = _create_applicabilities(self.object)
        if n:
            messages.info(self.request, f"{n} aéronef(s) potentiellement concerné(s) : statut « À évaluer » créé.")
        return resp


class DirectiveUpdate(AhmisUpdateView):
    model = Directive
    form_class = DirectiveForm

    def form_valid(self, form):
        resp = super().form_valid(form)
        _create_applicabilities(self.object)
        return resp


def _create_applicabilities(directive):
    n = 0
    for ac in directive.potentially_affected_aircraft():
        _, created = DirectiveApplicability.objects.get_or_create(directive=directive, aircraft=ac)
        n += created
    return n


@permission_required("camo.view_directive", raise_exception=True)
def directive_detail(request, pk):
    d = get_object_or_404(Directive, pk=pk)
    _create_applicabilities(d)
    return render(request, "camo/directive_detail.html", {
        "d": d,
        "apps": d.applicabilities.select_related("aircraft__aircraft_type"),
        "tasks": d.tasks.select_related("aircraft_type"),
    })


@permission_required("camo.change_directiveapplicability", raise_exception=True)
def applicability_update(request, pk):
    app = get_object_or_404(DirectiveApplicability.objects.select_related("directive", "aircraft"), pk=pk)
    form = ApplicabilityForm(request.POST or None, instance=app)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        staff = getattr(request.user, "staff", None)
        obj.reviewed_by = staff.full_name if staff else request.user.get_username()
        obj.reviewed_on = timezone.localdate()
        try:
            obj.full_clean()
            obj.save()
        except ValidationError as e:
            error_messages(request, e)
        else:
            messages.success(request, gettext("Statut enregistré : {obj}.").format(obj=obj))
            return redirect(app.directive.get_absolute_url())
    return render(request, "core/form.html", {
        "form": form, "title": f"Évaluation {app.directive.number} – {app.aircraft.registration}",
        "subtitle": app.directive.title, "cancel_url": app.directive.get_absolute_url(),
    })


class ApplicabilityList(AhmisListView):
    model = DirectiveApplicability
    queryset = DirectiveApplicability.objects.select_related("directive", "aircraft")
    columns = [(gettext_lazy("Consigne"), "directive.number"), (gettext_lazy("Objet"), "directive.title"), (gettext_lazy("Aéronef"), "aircraft.registration"),
               (gettext_lazy("Statut"), "status"), (gettext_lazy("Conformité le"), "compliance_date"), (gettext_lazy("Évalué par"), "reviewed_by"), (gettext_lazy("Évalué le"), "reviewed_on")]
    search_fields = ["directive__number", "directive__title", "aircraft__registration"]
    filter_fields = ["status", "aircraft"]
    title = gettext_lazy("Statut des consignes par aéronef")


# ---------------------------------------------------------------- ARC
class ArcList(AhmisListView):
    model = AirworthinessReview
    queryset = AirworthinessReview.objects.select_related("aircraft")
    columns = [(gettext_lazy("Aéronef"), "aircraft.registration"), (gettext_lazy("Type"), "review_type"), (gettext_lazy("N° ARC"), "reference"), (gettext_lazy("Revue le"), "review_date"),
               (gettext_lazy("Valable jusqu'au"), "expiry_date"), (gettext_lazy("Revue par"), "reviewer"), (gettext_lazy("Visite physique"), "physical_survey")]
    filter_fields = ["aircraft"]
    create_url = reverse_lazy("camo:arc_create")
    title = gettext_lazy("Examens de navigabilité (ARC)")
    link_column = -1


class ArcCreate(AhmisCreateView):
    model = AirworthinessReview
    form_class = ArcForm
    title = gettext_lazy("Enregistrer un examen de navigabilité")

    def get_initial(self):
        init = super().get_initial()
        if self.request.GET.get("aircraft"):
            init["aircraft"] = self.request.GET["aircraft"]
        init["review_date"] = timezone.localdate()
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
        return self.object.aircraft.get_absolute_url()


# ---------------------------------------------------------------- Modifications et réparations
class ModificationList(AhmisListView):
    model = ModificationRepair
    queryset = ModificationRepair.objects.select_related("aircraft", "component__part_number")
    columns = [("N°", "number"), (gettext_lazy("Aéronef"), "aircraft.registration"), (gettext_lazy("Nature"), "kind"), (gettext_lazy("Classe"), "classification"),
               (gettext_lazy("Intitulé"), "title"), (gettext_lazy("Approbation"), "approval_reference"), (gettext_lazy("Statut"), "status"), (gettext_lazy("Appliquée le"), "embodied_on"),
               (gettext_lazy("ICA au programme"), "ica_in_amp")]
    search_fields = ["number", "title", "approval_reference", "aircraft__registration"]
    filter_fields = ["aircraft", "kind", "classification", "status"]
    create_url = reverse_lazy("camo:mod_create")
    title = gettext_lazy("Registre des modifications et réparations")
    subtitle = gettext_lazy("Statut des modifications et réparations exigé par M.A.305 : base d'approbation, application, ICA.")


class Part21List(ModificationList):
    """Dossiers Part-21 : modifications majeures ou fondées sur un STC, une approbation DOA ou EASA."""

    columns = [("N°", "number"), (gettext_lazy("Aéronef"), "aircraft.registration"), (gettext_lazy("Intitulé"), "title"), (gettext_lazy("Classe"), "classification"),
               (gettext_lazy("Titulaire de la conception"), "design_holder"), (gettext_lazy("Dossier Part-21"), "part21_status"),
               (gettext_lazy("Demande le"), "part21_requested_on"), (gettext_lazy("Approuvé le"), "part21_approved_on"), (gettext_lazy("Statut"), "status")]
    filter_fields = ["aircraft", "part21_status", "status"]
    title = gettext_lazy("Dossiers Part-21")
    subtitle = gettext_lazy("Modifications et réparations qui exigent des données de conception approuvées (DOA, STC, EASA) avant application.")

    def get_queryset(self):
        from django.db.models import Q

        return super().get_queryset().filter(Q(classification="major") | Q(approval_basis__in=ModificationRepair.PART21_BASES))


class ModificationCreate(AhmisCreateView):
    model = ModificationRepair
    form_class = ModificationForm
    title = gettext_lazy("Enregistrer une modification ou une réparation")

    def get_initial(self):
        init = super().get_initial()
        from apps.part145.models import TaskCard

        card = TaskCard.objects.filter(pk=self.request.GET.get("task_card")).first() if self.request.GET.get("task_card") else None
        if card:
            init.update({"aircraft": card.aircraft, "component": card.component, "status": "embodied",
                         "embodied_on": timezone.localdate(), "title": card.title, "ata": card.ata})
        elif self.request.GET.get("aircraft"):
            init["aircraft"] = self.request.GET["aircraft"]
        return init

    def form_valid(self, form):
        from apps.part145.models import TaskCard

        card = TaskCard.objects.filter(pk=self.request.GET.get("task_card")).first() if self.request.GET.get("task_card") else None
        if card and card.aircraft.pk == form.cleaned_data["aircraft"].pk:
            form.instance.task_card = card
        return super().form_valid(form)


class ModificationUpdate(AhmisUpdateView):
    model = ModificationRepair
    form_class = ModificationForm


@permission_required("camo.view_modificationrepair", raise_exception=True)
def mod_detail(request, pk):
    m = get_object_or_404(ModificationRepair.objects.select_related("aircraft", "component__part_number", "directive", "task_card"), pk=pk)
    return render(request, "camo/mod_detail.html", {"m": m})


# ---------------------------------------------------------------- Revue du programme d'entretien
@permission_required("camo.view_ampreview", raise_exception=True)
def amp_review_list(request):
    from apps.fleet.models import AircraftType

    types = AircraftType.objects.filter(aircraft__status__in=[s for s, _ in Aircraft.STATUSES if s != "retired"]).distinct()
    rows = [{"type": t, **amp_review_status(t)} for t in types]
    order = {"none": 0, "overdue": 1, "due_soon": 2, "ok": 3}
    rows.sort(key=lambda r: (order[r["status"]], r["type"].code))
    reviews = AmpReview.objects.select_related("aircraft_type")[:100]
    return render(request, "camo/amp_review_list.html", {"rows": rows, "reviews": reviews})


class AmpReviewCreate(AhmisCreateView):
    model = AmpReview
    form_class = AmpReviewForm
    title = gettext_lazy("Enregistrer une revue du programme d'entretien")

    def get_initial(self):
        init = super().get_initial()
        init["review_date"] = timezone.localdate()
        from apps.fleet.models import AircraftType

        t = AircraftType.objects.filter(pk=self.request.GET.get("aircraft_type")).first() if self.request.GET.get("aircraft_type") else None
        if t:
            init["aircraft_type"] = t
            last = t.amp_reviews.order_by("-review_date", "-pk").first()
            if last:
                init["amp_reference"] = last.amp_reference
                init["revision_before"] = last.revision_after or last.revision_before
        return init

    def form_valid(self, form):
        try:
            form.instance.full_clean()
        except ValidationError as e:
            for m in e.messages:
                form.add_error(None, m)
            return self.form_invalid(form)
        return super().form_valid(form)


@permission_required("camo.view_ampreview", raise_exception=True)
def amp_review_detail(request, pk):
    r = get_object_or_404(AmpReview.objects.select_related("aircraft_type"), pk=pk)
    history = r.aircraft_type.amp_reviews.exclude(pk=r.pk)
    return render(request, "camo/amp_review_detail.html", {"r": r, "history": history})


# ---------------------------------------------------------------- Transfert des enregistrements (M.A.307)
class TransferList(AhmisListView):
    model = TransferRecord
    queryset = TransferRecord.objects.select_related("aircraft")
    columns = [("N°", "number"), (gettext_lazy("Aéronef"), "aircraft.registration"), (gettext_lazy("Sens"), "direction"), (gettext_lazy("Date"), "transfer_date"),
               (gettext_lazy("Organisme"), "counterparty"), (gettext_lazy("Agrément"), "counterparty_approval"), (gettext_lazy("Réception confirmée"), "acknowledged_on")]
    search_fields = ["number", "counterparty", "aircraft__registration"]
    filter_fields = ["aircraft", "direction"]
    create_url = reverse_lazy("camo:transfer_create")
    title = gettext_lazy("Transferts de dossiers")
    subtitle = gettext_lazy("M.A.307 / CAMO.A.315 : transfert des enregistrements de maintien de la navigabilité au nouvel organisme.")


class TransferCreate(AhmisCreateView):
    model = TransferRecord
    form_class = TransferForm
    title = gettext_lazy("Transférer ou archiver le dossier d'un aéronef")

    def get_initial(self):
        init = super().get_initial()
        if self.request.GET.get("aircraft"):
            init["aircraft"] = self.request.GET["aircraft"]
        return init

    def form_valid(self, form):
        import hashlib

        from django.core.files.base import ContentFile

        from . import dossier

        t = form.instance
        try:
            t.full_clean(exclude=["archive"])
        except ValidationError as e:
            for m in e.messages:
                form.add_error(None, m)
            return self.form_invalid(form)
        with transaction.atomic():
            if t.direction in ("out", "copy"):
                raw, digest, manifest = dossier.build_archive(t.aircraft, self.request.user, recipient=t.counterparty, purpose=t.reason)
                t.manifest, t.archive_sha256, t.archive_size = manifest, digest, len(raw)
                t.verification = gettext("Archive générée par AHMIS ; empreintes de chaque fichier dans manifest.json.")
                t.save()
                t.archive.save(f"dossier-{t.aircraft.registration}-{t.number}.zip", ContentFile(raw), save=True)
            else:
                upload = form.cleaned_data["archive"]
                h = hashlib.sha256()
                for chunk in upload.chunks():
                    h.update(chunk)
                upload.seek(0)
                manifest, problems = dossier.verify_archive(upload)
                upload.seek(0)
                if manifest and manifest.get("aeronef", {}).get("msn") not in (None, t.aircraft.msn):
                    problems.append(gettext("Le dossier concerne le MSN {msn}, pas {msn2}.").format(msn=manifest['aeronef'].get('msn'), msn2=t.aircraft.msn))
                t.manifest, t.archive_sha256, t.archive_size = manifest, h.hexdigest(), upload.size
                if manifest is None:
                    t.verification = gettext("ANOMALIE – ") + " ".join(problems) + gettext(" Contrôle manuel du dossier requis.")
                elif problems:
                    t.verification = gettext("ANOMALIE – ") + " ; ".join(problems)
                else:
                    t.verification = gettext("Archive AHMIS intègre : {fichiers} fichier(s) conformes au manifeste.").format(fichiers=len(manifest.get('fichiers', {})))
                t.save()
        self.object = t
        messages.success(self.request, gettext("Transfert {number} enregistré.").format(number=t.number))
        if t.verification.startswith("ANOMALIE"):
            messages.warning(self.request, t.verification)
        return redirect(t.get_absolute_url())


@permission_required("camo.view_transferrecord", raise_exception=True)
def transfer_detail(request, pk):
    t = get_object_or_404(TransferRecord.objects.select_related("aircraft"), pk=pk)
    ack_form = TransferAckForm(initial={"acknowledged_on": timezone.localdate()})
    if request.method == "POST" and request.user.has_perm("camo.change_transferrecord"):
        ack_form = TransferAckForm(request.POST)
        if ack_form.is_valid():
            t.acknowledged_on = ack_form.cleaned_data["acknowledged_on"]
            t.acknowledged_by = ack_form.cleaned_data["acknowledged_by"]
            try:
                t.full_clean()
                t.save()
                messages.success(request, gettext("Accusé de réception enregistré."))
                return redirect(t.get_absolute_url())
            except ValidationError as e:
                error_messages(request, e)
                t.refresh_from_db()
    return render(request, "camo/transfer_detail.html", {"t": t, "ack_form": ack_form})


@permission_required("camo.view_transferrecord", raise_exception=True)
def transfer_download(request, pk):
    from django.http import FileResponse, Http404

    t = get_object_or_404(TransferRecord, pk=pk)
    if not t.archive:
        raise Http404
    return FileResponse(t.archive.open("rb"), as_attachment=True, filename=t.archive.name.rsplit("/", 1)[-1])
