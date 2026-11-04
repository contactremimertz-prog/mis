from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.camo import services as camo_services
from apps.core.crud import AhmisCreateView, AhmisListView, AhmisUpdateView, error_messages
from apps.core.models import SignatureRecord
from apps.fleet.models import Aircraft

from . import services
from .forms import (AddTaskForm, AdhocCardForm, AuthorizationForm, ComponentChangeForm, DeferForm, DefectForm, ExperienceForm, ExtendDeferralForm,
                    PartRequestForm, PerformForm, QualificationForm, ReasonForm, SignForm, StaffForm, StepForm,
                    ToolCheckoutForm, WorkPackageForm)
from .models import Defect, Staff, TaskCard, TaskCardStep, WorkPackage


def _check_password(request, form):
    """Revérification d'identité à la signature : mot de passe local, mot de passe AD ou code de signature."""
    from apps.core.identity import verify_signature_secret

    if not verify_signature_secret(request.user, form.cleaned_data["password"]):
        raise ValidationError("Mot de passe ou code de signature incorrect : signature refusée.")


def _run(request, fn, success, *args, **kwargs):
    """Exécute une action métier ; affiche les erreurs réglementaires à l'utilisateur."""
    try:
        with transaction.atomic():
            fn(*args, **kwargs)
    except ValidationError as e:
        error_messages(request, e)
        return False
    messages.success(request, success)
    return True


# ---------------------------------------------------------------- Work packages
class WorkPackageList(AhmisListView):
    model = WorkPackage
    queryset = WorkPackage.objects.select_related("aircraft")
    columns = [("N°", "number"), ("Aéronef", "aircraft.registration"), ("Intitulé", "title"), ("Type", "check_type"),
               ("Station", "station"), ("Début", "planned_start"), ("Fin", "planned_end"), ("Statut", "status"), ("Avancement %", "progress")]
    search_fields = ["number", "title", "aircraft__registration", "customer_order"]
    filter_fields = ["status", "aircraft", "check_type"]
    create_url = reverse_lazy("part145:wp_create")
    title = "Work packages"


class WorkPackageCreate(AhmisCreateView):
    model = WorkPackage
    form_class = WorkPackageForm
    title = "Nouveau work package"

    def get_initial(self):
        init = super().get_initial()
        if self.request.GET.get("aircraft"):
            init["aircraft"] = self.request.GET["aircraft"]
        today = timezone.localdate()
        init.update({"planned_start": today, "planned_end": today + timedelta(days=2), "status": "planned"})
        return init


class WorkPackageUpdate(AhmisUpdateView):
    model = WorkPackage
    form_class = WorkPackageForm

    def dispatch(self, request, *args, **kwargs):
        wp = self.get_object()
        if wp.is_locked:
            messages.error(request, "Work package verrouillé : remis en service ou annulé.")
            return redirect(wp.get_absolute_url())
        return super().dispatch(request, *args, **kwargs)


@permission_required("part145.view_workpackage", raise_exception=True)
def wp_detail(request, pk):
    wp = get_object_or_404(WorkPackage.objects.select_related("aircraft__aircraft_type", "crs_by"), pk=pk)
    cards = wp.task_cards.select_related("task", "performed_by", "inspected_by", "defect").prefetch_related("steps")
    due_items = [i for i in camo_services.aircraft_due_list(wp.aircraft) if i.status != "ok" or (i.projected_date and i.projected_date <= wp.planned_end + timedelta(days=30))]
    planned_keys = set()
    for c in cards:
        if c.task_id:
            planned_keys.add(f"task:{c.task_id}:{c.component_id or 0}")
        if c.defect_id:
            planned_keys.add(f"defect:{c.defect_id}")
    due_items = [i for i in due_items if i.key not in planned_keys and i.kind in ("task", "component_task", "llp", "tbo", "defect")]
    return render(request, "part145/wp_detail.html", {
        "wp": wp,
        "cards": cards,
        "due_items": due_items,
        "blockers": wp.crs_blockers() if not wp.is_locked else [],
        "add_task_form": AddTaskForm(wp),
        "adhoc_form": AdhocCardForm(),
        "sign_form": SignForm(),
        "crs_signature": SignatureRecord.for_object(wp).filter(action="crs").first(),
        "open_defects": wp.aircraft.defects.filter(status__in=["open", "deferred"]),
    })


@permission_required("part145.view_workpackage", raise_exception=True)
def wp_print(request, pk):
    wp = get_object_or_404(WorkPackage, pk=pk)
    return render(request, "part145/wp_print.html", {
        "wp": wp, "cards": wp.task_cards.all(),
        "crs_signature": SignatureRecord.for_object(wp).filter(action="crs").first(),
    })


@require_POST
@permission_required("part145.add_taskcard", raise_exception=True)
def wp_add_items(request, pk):
    wp = get_object_or_404(WorkPackage, pk=pk)
    keys = request.POST.getlist("keys")
    if request.POST.get("task"):
        form = AddTaskForm(wp, request.POST)
        if form.is_valid():
            keys.append(f"task:{form.cleaned_data['task'].pk}:0")
    if not keys:
        messages.warning(request, "Aucun élément sélectionné.")
        return redirect(wp.get_absolute_url())
    try:
        created = services.add_due_items_to_wp(wp, keys)
    except ValidationError as e:
        error_messages(request, e)
    else:
        messages.success(request, f"{len(created)} task card(s) créée(s).")
    return redirect(wp.get_absolute_url())


@require_POST
@permission_required("part145.add_taskcard", raise_exception=True)
def wp_add_adhoc(request, pk):
    wp = get_object_or_404(WorkPackage, pk=pk)
    if wp.is_locked:
        messages.error(request, "Work package verrouillé.")
        return redirect(wp.get_absolute_url())
    form = AdhocCardForm(request.POST)
    if form.is_valid():
        card = form.save(commit=False)
        card.work_package = wp
        card.origin = "adhoc"
        card.save()
        messages.success(request, f"Task card {card.number} créée.")
        return redirect(card.get_absolute_url())
    messages.error(request, "Formulaire incomplet : " + "; ".join(f"{k} : {', '.join(v)}" for k, v in form.errors.items()))
    return redirect(wp.get_absolute_url())


@require_POST
@permission_required("part145.sign_crs", raise_exception=True)
def wp_crs(request, pk):
    wp = get_object_or_404(WorkPackage, pk=pk)
    form = SignForm(request.POST)
    if form.is_valid():
        try:
            _check_password(request, form)
        except ValidationError as e:
            error_messages(request, e)
            return redirect(wp.get_absolute_url())
        _run(request, services.issue_crs, f"CRS signé : {wp.aircraft.registration} remis en service.", wp, request.user)
    return redirect(wp.get_absolute_url())


@require_POST
@permission_required("part145.add_workpackage", raise_exception=True)
def plan_from_due(request, aircraft_pk):
    """Depuis l'écran Échéances : crée les task cards dans un WP existant ou nouveau."""
    ac = get_object_or_404(Aircraft, pk=aircraft_pk)
    keys = request.POST.getlist("keys")
    if not keys:
        messages.warning(request, "Cochez au moins un élément à planifier.")
        return redirect(reverse("camo:due") + f"?aircraft={ac.pk}")
    target = request.POST.get("wp", "new")
    with transaction.atomic():
        if target == "new":
            today = timezone.localdate()
            wp = WorkPackage.objects.create(
                aircraft=ac, title="Visite programmée", check_type="periodic", status="draft",
                planned_start=today + timedelta(days=7), planned_end=today + timedelta(days=9), station=ac.base,
            )
        else:
            wp = get_object_or_404(WorkPackage, pk=target, aircraft=ac)
        try:
            created = services.add_due_items_to_wp(wp, keys)
        except ValidationError as e:
            transaction.set_rollback(True)
            error_messages(request, e)
            return redirect(reverse("camo:due") + f"?aircraft={ac.pk}")
    messages.success(request, f"{len(created)} task card(s) créée(s) dans {wp.number}. Complétez les dates et l'intitulé du work package.")
    return redirect(wp.get_absolute_url())


# ---------------------------------------------------------------- Task cards
class TaskCardList(AhmisListView):
    model = TaskCard
    queryset = TaskCard.objects.select_related("work_package__aircraft", "performed_by")
    columns = [("N°", "number"), ("Intitulé", "title"), ("WP", "work_package.number"), ("Aéronef", "work_package.aircraft.registration"),
               ("ATA", "ata"), ("Origine", "origin"), ("Statut", "status"), ("Exécuté par", "performed_by.full_name"), ("h.h prévues", "estimated_mh")]
    search_fields = ["number", "title", "work_package__number", "work_package__aircraft__registration"]
    filter_fields = ["status", "origin"]
    title = "Task cards"


@permission_required("part145.view_taskcard", raise_exception=True)
def card_detail(request, pk):
    card = get_object_or_404(TaskCard.objects.select_related("work_package__aircraft__aircraft_type", "task", "component", "defect"), pk=pk)
    staff = Staff.objects.filter(user=request.user).first()
    ac_type = card.aircraft.aircraft_type
    return render(request, "part145/card_detail.html", {
        "card": card,
        "steps": card.steps.select_related("done_by"),
        "signatures": SignatureRecord.for_object(card),
        "staff": staff,
        "can_perform": bool(staff and staff.can_perform(ac_type)),
        "perform_blockers": staff.signing_blockers(ac_type) if staff else [],
        "can_certify": bool(staff and staff.can_certify(ac_type)),
        "perform_form": PerformForm(initial={"actual_mh": card.estimated_mh}),
        "step_form": StepForm(),
        "reason_form": ReasonForm(),
        "sign_form": SignForm(),
        "request_form": PartRequestForm(),
        "tool_form": ToolCheckoutForm(),
        "change_form": ComponentChangeForm(card),
        "requests": card.part_requests.select_related("part_number", "issued_component", "issued_stock"),
        "tool_usages": card.tool_usages.select_related("tool", "staff"),
        "installs": card.installation_records.select_related("component__part_number"),
        "findings": card.findings.all(),
        "stock_movements": card.stock_movements.select_related("stock_item__part_number"),
    })


@permission_required("part145.view_taskcard", raise_exception=True)
def card_print(request, pk):
    card = get_object_or_404(TaskCard, pk=pk)
    return render(request, "part145/card_print.html", {
        "card": card, "steps": card.steps.select_related("done_by"),
        "signatures": SignatureRecord.for_object(card),
        "requests": card.part_requests.all(), "tool_usages": card.tool_usages.select_related("tool"),
    })


@require_POST
@permission_required("part145.execute_taskcard", raise_exception=True)
def card_action(request, pk, action):
    card = get_object_or_404(TaskCard, pk=pk)
    user = request.user
    if action == "start":
        _run(request, services.start_card, "Task card démarrée.", card, user)
        return redirect(card.get_absolute_url())

    form_class = {"perform": PerformForm, "defer": ReasonForm, "cancel": ReasonForm, "inspect": ReasonForm}.get(action)
    if form_class is None:
        messages.error(request, "Action inconnue.")
        return redirect(card.get_absolute_url())
    data = request.POST.copy()
    if action == "inspect" and not data.get("reason"):
        data["reason"] = "Conforme"
    form = form_class(data)
    if not form.is_valid():
        for field, errs in form.errors.items():
            for e in errs:
                messages.error(request, f"{form.fields[field].label if field in form.fields else ''} : {e}")
        return redirect(card.get_absolute_url())
    try:
        _check_password(request, form)
    except ValidationError as e:
        error_messages(request, e)
        return redirect(card.get_absolute_url())
    d = form.cleaned_data
    if action == "perform":
        _run(request, services.perform_card, "Travaux signés.", card, user, d["work_done"], d["actual_mh"])
    elif action == "inspect":
        if not user.has_perm("part145.certify_taskcard"):
            messages.error(request, "Vous n'avez pas le droit de contrôle.")
        else:
            _run(request, services.inspect_card, "Contrôle indépendant signé : task card clôturée.", card, user, d["reason"])
    elif action == "defer":
        _run(request, services.defer_card, "Task card reportée.", card, user, d["reason"])
    elif action == "cancel":
        _run(request, services.cancel_card, "Task card annulée.", card, user, d["reason"])
    return redirect(card.get_absolute_url())


@require_POST
@permission_required("part145.execute_taskcard", raise_exception=True)
def step_sign(request, pk):
    step = get_object_or_404(TaskCardStep, pk=pk)
    form = StepForm(request.POST)
    if form.is_valid():
        try:
            _check_password(request, form)
        except ValidationError as e:
            error_messages(request, e)
        else:
            _run(request, services.sign_step, f"Étape {step.order} signée.", step, request.user,
                 form.cleaned_data["measured_value"], form.cleaned_data["not_applicable"])
    else:
        messages.error(request, "Mot de passe requis pour signer.")
    return redirect(step.card.get_absolute_url() + f"#step-{step.pk}")


@require_POST
@permission_required("part145.execute_taskcard", raise_exception=True)
def card_component_change(request, pk):
    card = get_object_or_404(TaskCard, pk=pk)
    form = ComponentChangeForm(card, request.POST)
    if not form.is_valid():
        for field, errs in form.errors.items():
            for e in errs:
                messages.error(request, e)
        return redirect(card.get_absolute_url())
    try:
        _check_password(request, form)
    except ValidationError as e:
        error_messages(request, e)
        return redirect(card.get_absolute_url())
    d = form.cleaned_data
    _run(request, services.change_component, "Changement de composant enregistré (configuration et historique mis à jour).",
         card, request.user, d["removed"], d["installed"], d["position"], d["removal_reason"], d["removal_type"], d["removed_status"])
    return redirect(card.get_absolute_url())


@require_POST
@permission_required("part145.add_taskcard", raise_exception=True)
def card_finding(request, pk):
    """Constatation en cours de visite : crée un défaut et une task card de rectification liée."""
    card = get_object_or_404(TaskCard, pk=pk)
    text = request.POST.get("description", "").strip()
    if not text:
        messages.error(request, "Décrivez la constatation.")
        return redirect(card.get_absolute_url())
    staff = Staff.objects.filter(user=request.user).first()
    with transaction.atomic():
        defect = Defect.objects.create(
            aircraft=card.aircraft, reported_by=staff.full_name if staff else request.user.username,
            source="finding", ata=card.ata, description=text, techlog_ref=card.number,
        )
        new = services.card_from_defect(card.work_package, defect)
        new.origin = "finding"
        new.parent = card
        new.save()
    messages.success(request, f"Constatation {defect.number} et task card {new.number} créées.")
    return redirect(new.get_absolute_url())


# ---------------------------------------------------------------- Défauts
class DefectList(AhmisListView):
    model = Defect
    queryset = Defect.objects.select_related("aircraft")
    columns = [("N°", "number"), ("Aéronef", "aircraft.registration"), ("Signalé le", "reported_on"), ("ATA", "ata"),
               ("Description", "description"), ("Source", "source"), ("Statut", "status"), ("MEL", "mel_reference"), ("Limite", "deferral_limit_date")]
    search_fields = ["number", "description", "aircraft__registration", "mel_reference"]
    filter_fields = ["status", "aircraft", "source"]
    create_url = reverse_lazy("part145:defect_create")
    title = "Défauts et reports (MEL/CDL)"


class DefectCreate(AhmisCreateView):
    model = Defect
    form_class = DefectForm
    title = "Signaler un défaut"

    def get_initial(self):
        init = super().get_initial()
        if self.request.GET.get("aircraft"):
            init["aircraft"] = self.request.GET["aircraft"]
        staff = Staff.objects.filter(user=self.request.user).first()
        init["reported_by"] = staff.full_name if staff else self.request.user.username
        init["reported_on"] = timezone.localdate()
        return init


@permission_required("part145.view_defect", raise_exception=True)
def defect_detail(request, pk):
    d = get_object_or_404(Defect.objects.select_related("aircraft"), pk=pk)
    return render(request, "part145/defect_detail.html", {
        "d": d,
        "defer_form": DeferForm(),
        "extend_form": ExtendDeferralForm(),
        "extension_blockers": d.extension_blockers(check_values=False) if d.status == "deferred" and not d.extended else [],
        "wps": d.aircraft.work_packages.filter(status__in=["draft", "planned", "in_progress"]),
        "cards": d.task_cards.select_related("work_package"),
        "signatures": SignatureRecord.for_object(d),
    })


@require_POST
@permission_required("part145.defer_defect", raise_exception=True)
def defect_defer(request, pk):
    d = get_object_or_404(Defect, pk=pk)
    form = DeferForm(request.POST)
    if form.is_valid():
        try:
            _check_password(request, form)
        except ValidationError as e:
            error_messages(request, e)
            return redirect(d.get_absolute_url())
        c = form.cleaned_data
        _run(request, services.defer_defect, "Défaut reporté : il apparaît désormais dans les échéances.", d, request.user,
             c["mel_reference"], c["category"], c["limit_date"], c["limit_fh"], c["limit_fc"], c["procedure"])
    else:
        messages.error(request, "Formulaire de report incomplet.")
    return redirect(d.get_absolute_url())


@require_POST
@permission_required("part145.extend_deferral", raise_exception=True)
def defect_extend(request, pk):
    d = get_object_or_404(Defect, pk=pk)
    form = ExtendDeferralForm(request.POST)
    if form.is_valid():
        try:
            _check_password(request, form)
        except ValidationError as e:
            error_messages(request, e)
            return redirect(d.get_absolute_url())
        c = form.cleaned_data
        _run(request, services.extend_deferral, "Prorogation unique approuvée et signée : la nouvelle limite est prise en compte dans les échéances.",
             d, request.user, c["reason"], c["reference"], c["new_date"], c["new_fh"], c["new_fc"], c["authority_notified"])
    else:
        messages.error(request, "Formulaire de prorogation incomplet.")
    return redirect(d.get_absolute_url())


@require_POST
@permission_required("part145.add_taskcard", raise_exception=True)
def defect_to_wp(request, pk):
    d = get_object_or_404(Defect, pk=pk)
    target = request.POST.get("wp")
    with transaction.atomic():
        if target == "new":
            today = timezone.localdate()
            wp = WorkPackage.objects.create(aircraft=d.aircraft, title=f"Rectification {d.number}", check_type="unscheduled",
                                            status="planned", planned_start=today, planned_end=today, station=d.aircraft.base)
        else:
            wp = get_object_or_404(WorkPackage, pk=target, aircraft=d.aircraft)
        try:
            card = services.card_from_defect(wp, d)
        except ValidationError as e:
            error_messages(request, e)
            return redirect(d.get_absolute_url())
    messages.success(request, f"Task card {card.number} créée dans {wp.number}.")
    return redirect(card.get_absolute_url())


# ---------------------------------------------------------------- Personnel
class StaffList(AhmisListView):
    model = Staff
    columns = [("Matricule", "employee_number"), ("Nom", "full_name"), ("Fonction", "role"), ("Visa", "stamp"),
               ("Licence", "licence_number"), ("Catégories", "licence_categories"), ("Validité licence", "licence_expiry"), ("Compte", "user"), ("Actif", "active")]
    search_fields = ["last_name", "first_name", "employee_number", "licence_number"]
    filter_fields = ["role", "active"]
    create_url = reverse_lazy("part145:staff_create")
    title = "Personnel et autorisations"


class StaffCreate(AhmisCreateView):
    model = Staff
    form_class = StaffForm
    title = "Nouvelle fiche personnel"


class StaffUpdate(AhmisUpdateView):
    model = Staff
    form_class = StaffForm


@permission_required("part145.view_staff", raise_exception=True)
def staff_detail(request, pk):
    s = get_object_or_404(Staff, pk=pk)
    return render(request, "part145/staff_detail.html", {
        "s": s,
        "auths": s.authorizations.select_related("aircraft_type"),
        "quals": s.qualifications.all(),
        "auth_form": AuthorizationForm(initial={"valid_from": timezone.localdate(), "valid_until": timezone.localdate() + timedelta(days=730)}),
        "qual_form": QualificationForm(),
        "exp_form": ExperienceForm(),
        "experiences": s.experience_records.select_related("aircraft_type"),
        "recency": {
            "months": len(s.experience_months()), "need": settings.AHMIS["RECENCY_MONTHS"],
            "window": settings.AHMIS["RECENCY_WINDOW_MONTHS"], "enforced": settings.AHMIS["RECENCY_ENFORCE"],
        },
        "missing_all": s.missing_trainings(False),
        "missing_cert": s.missing_trainings(True),
        "type_status": [(a.aircraft_type, s.signing_blockers(a.aircraft_type, certifying=a.certifying))
                        for a in s.authorizations.select_related("aircraft_type") if a.is_valid],
        "recent_cards": TaskCard.objects.filter(performed_by=s).order_by("-performed_at")[:10],
        "recent_inspections": TaskCard.objects.filter(inspected_by=s).order_by("-inspected_at")[:10],
    })


@require_POST
@permission_required("part145.add_authorization", raise_exception=True)
def staff_add_authorization(request, pk):
    s = get_object_or_404(Staff, pk=pk)
    form = AuthorizationForm(request.POST)
    if form.is_valid():
        a = form.save(commit=False)
        a.staff = s
        try:
            a.full_clean()
            a.save()
        except ValidationError as e:
            error_messages(request, e)
        else:
            messages.success(request, f"Autorisation {a} ajoutée.")
    else:
        messages.error(request, "Autorisation incomplète : " + "; ".join(f"{k} : {', '.join(v)}" for k, v in form.errors.items()))
    return redirect(s.get_absolute_url())


@require_POST
@permission_required("part145.add_experiencerecord", raise_exception=True)
def staff_add_experience(request, pk):
    s = get_object_or_404(Staff, pk=pk)
    form = ExperienceForm(request.POST)
    if form.is_valid():
        e = form.save(commit=False)
        e.staff = s
        try:
            e.full_clean()
            e.save()
        except ValidationError as exc:
            error_messages(request, exc)
        else:
            messages.success(request, "Expérience enregistrée.")
    else:
        messages.error(request, "Expérience incomplète : " + "; ".join(f"{k} : {', '.join(v)}" for k, v in form.errors.items()))
    return redirect(s.get_absolute_url())


@require_POST
@permission_required("part145.add_qualification", raise_exception=True)
def staff_add_qualification(request, pk):
    s = get_object_or_404(Staff, pk=pk)
    form = QualificationForm(request.POST)
    if form.is_valid():
        q = form.save(commit=False)
        q.staff = s
        q.save()
        messages.success(request, f"Formation {q.name} ajoutée.")
    else:
        messages.error(request, "Formation incomplète.")
    return redirect(s.get_absolute_url())


# ---------------------------------------------------------------- Planning
@permission_required("part145.view_workpackage", raise_exception=True)
def planning(request):
    today = timezone.localdate()
    try:
        weeks = max(2, min(26, int(request.GET.get("weeks", 8))))
    except ValueError:
        weeks = 8
    try:
        offset = int(request.GET.get("offset", 0))
    except ValueError:
        offset = 0
    start = today - timedelta(days=today.weekday()) + timedelta(weeks=offset)
    days = [start + timedelta(days=i) for i in range(weeks * 7)]
    end = days[-1]
    fleet = list(Aircraft.objects.exclude(status="retired").select_related("aircraft_type"))
    wps = WorkPackage.objects.exclude(status="cancelled").filter(planned_end__gte=start, planned_start__lte=end).select_related("aircraft")
    due = [i for i in camo_services.fleet_due_list(fleet) if i.projected_date and i.status != "ok" or (i.projected_date and start <= i.projected_date <= end)]
    rows = []
    for ac in fleet:
        cells = []
        ac_wps = [w for w in wps if w.aircraft_id == ac.pk]
        ac_due = [i for i in due if i.aircraft.pk == ac.pk]
        for d in days:
            wp = next((w for w in ac_wps if w.planned_start <= d <= w.planned_end), None)
            dots = [i for i in ac_due if (i.projected_date == d) or (d == days[0] and i.projected_date and i.projected_date < days[0])]
            cells.append({"day": d, "wp": wp, "wp_start": bool(wp and (wp.planned_start == d or d == days[0])), "dots": dots})
        rows.append({"ac": ac, "cells": cells})
    return render(request, "part145/planning.html", {
        "days": days, "rows": rows, "today": today, "weeks": weeks, "offset": offset,
        "wps": wps.order_by("planned_start"),
    })
