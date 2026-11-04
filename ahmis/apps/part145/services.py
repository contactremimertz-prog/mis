"""Règles métier Part-145 : exécution, contrôle, report, CRS, changements de composants.

Chaque action réglementaire crée une SignatureRecord (signature électronique horodatée).
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.camo.models import DirectiveApplicability, MaintenanceTask, TaskAccomplishment
from apps.core.models import SignatureRecord
from apps.fleet.models import Component, install_component, installation_errors, remove_component

from .models import Defect, Staff, TaskCard, TaskCardStep
from django.utils.translation import gettext, gettext_lazy

CRS_STATEMENT = (
    gettext_lazy("Certifie que les travaux spécifiés, sauf indication contraire, ont été effectués conformément "
    "à la Partie 145 et que, en ce qui concerne ces travaux, l'aéronef est considéré comme apte à être "
    "remis en service. Organisme agréé {approval}.")
)


def staff_for(user):
    staff = Staff.objects.filter(user=user, active=True).first()
    if not staff:
        raise ValidationError(gettext("Votre compte n'est rattaché à aucune fiche personnel active : signature impossible."))
    return staff


def require_signing(staff, aircraft_type, certifying=False, categories=("B1", "B2", "B3", "C")):
    """Lève une ValidationError listant toutes les raisons qui empêchent la signature."""
    problems = staff.signing_blockers(aircraft_type, certifying=certifying, categories=categories)
    if problems:
        raise ValidationError(problems)


def _require_editable(card):
    if card.work_package.is_locked:
        raise ValidationError(gettext("Le work package est verrouillé (CRS signé ou annulé)."))


@transaction.atomic
def start_card(card, user):
    staff = staff_for(user)
    _require_editable(card)
    if card.status != "open":
        raise ValidationError(gettext("Seule une task card ouverte peut être démarrée."))
    require_signing(staff, card.aircraft.aircraft_type)
    card.status = "in_progress"
    card.save()
    wp = card.work_package
    if wp.status in ("draft", "planned"):
        wp.status = "in_progress"
        if wp.fh_at_check is None:
            wp.fh_at_check = wp.aircraft.total_fh
            wp.fc_at_check = wp.aircraft.total_fc
        wp.save()
        ac = wp.aircraft
        if ac.status == "active":
            ac.status = "maintenance"
            ac.save()


@transaction.atomic
def sign_step(step, user, measured_value="", not_applicable=False):
    staff = staff_for(user)
    card = step.card
    _require_editable(card)
    if card.status != "in_progress":
        raise ValidationError(gettext("Démarrez la task card avant de signer les étapes."))
    if step.done_at:
        raise ValidationError(gettext("Étape déjà signée."))
    require_signing(staff, card.aircraft.aircraft_type)
    step.done_by = staff
    step.done_at = timezone.now()
    step.measured_value = measured_value
    step.not_applicable = not_applicable
    step.save()
    SignatureRecord.sign(user, step, "step", gettext("Étape {order} {e} : {text}").format(order=step.order, e='N/A' if not_applicable else 'réalisée', text=step.text)
                         + (gettext(" | valeur relevée : {measured_value}").format(measured_value=measured_value) if measured_value else ""))


@transaction.atomic
def perform_card(card, user, work_done, actual_mh):
    staff = staff_for(user)
    _require_editable(card)
    if card.status != "in_progress":
        raise ValidationError(gettext("La task card doit être en cours."))
    require_signing(staff, card.aircraft.aircraft_type)
    missing = card.steps.filter(done_at__isnull=True).count()
    if missing:
        raise ValidationError(gettext("{missing} étape(s) non signée(s).").format(missing=missing))
    if not work_done.strip():
        raise ValidationError(gettext("Le compte rendu des travaux est obligatoire."))
    if card.part_requests.filter(status__in=["requested", "reserved"]).exists():
        raise ValidationError(gettext("Des demandes de pièces sont encore en attente : délivrez-les ou annulez-les."))
    if card.tools_out.exists():
        refs = ", ".join(t.reference for t in card.tools_out.all())
        raise ValidationError(gettext("Outillage non restitué : {refs}.").format(refs=refs))
    card.work_done = work_done
    card.actual_mh = actual_mh
    card.performed_by = staff
    card.performed_at = timezone.now()
    SignatureRecord.sign(user, card, "perform", gettext("Travaux exécutés : {title}. Compte rendu : {work_done}").format(title=card.title, work_done=work_done))
    if card.requires_independent_inspection:
        card.status = "performed"
        card.save()
    else:
        card.status = "closed"
        card.save()
        _on_card_closed(card)


@transaction.atomic
def inspect_card(card, user, remark=""):
    staff = staff_for(user)
    _require_editable(card)
    if card.status != "performed":
        raise ValidationError(gettext("La task card n'attend pas de contrôle."))
    if card.performed_by_id == staff.pk:
        raise ValidationError(gettext("Contrôle indépendant : l'inspecteur doit être différent de l'exécutant."))
    require_signing(staff, card.aircraft.aircraft_type, certifying=True)
    card.inspected_by = staff
    card.inspected_at = timezone.now()
    card.status = "closed"
    card.save()
    SignatureRecord.sign(user, card, "inspect", gettext("Contrôle indépendant réalisé sur {number}. {remark}").format(number=card.number, remark=remark).strip())
    _on_card_closed(card)


def _on_card_closed(card):
    ac = card.aircraft
    when = timezone.localdate()
    if card.task_id:
        task = card.task
        comp = card.component
        TaskAccomplishment.objects.create(
            task=task, aircraft=ac, component=comp, date=when, fh=ac.total_fh, fc=ac.total_fc,
            comp_fh=comp.tsn_fh if comp else None, comp_fc=comp.csn if comp else None,
            source="taskcard", task_card=card, reference=card.work_package.number,
            certified_by=(card.inspected_by or card.performed_by).full_name if (card.inspected_by or card.performed_by) else "",
        )
        if task.directive_id:
            app, _ = DirectiveApplicability.objects.get_or_create(directive=task.directive, aircraft=ac)
            app.status = "recurring" if task.is_repetitive else "complied"
            app.compliance_date = when
            app.compliance_fh = ac.total_fh
            app.compliance_fc = ac.total_fc
            app.justification = (app.justification + "\n" if app.justification else "") + gettext("Réalisée par task card {number}.").format(number=card.number)
            app.save()
    if card.defect_id:
        d = card.defect
        d.status = "rectified"
        d.rectified_on = when
        d.rectification = card.work_done
        d.save()


@transaction.atomic
def defer_card(card, user, reason):
    staff_for(user)
    _require_editable(card)
    if not reason.strip():
        raise ValidationError(gettext("Le motif de report est obligatoire."))
    if card.status not in ("open", "in_progress"):
        raise ValidationError(gettext("Cette task card ne peut pas être reportée."))
    if card.tools_out.exists():
        raise ValidationError(gettext("Restituez l'outillage avant de reporter la task card."))
    card.status = "deferred"
    card.deferral_reason = reason
    card.save()
    SignatureRecord.sign(user, card, "defer", gettext("Task card reportée : {reason}").format(reason=reason))


@transaction.atomic
def cancel_card(card, user, reason):
    _require_editable(card)
    if card.status in ("closed", "performed"):
        raise ValidationError(gettext("Une task card exécutée ne peut pas être annulée."))
    if card.steps.filter(done_at__isnull=False).exists():
        raise ValidationError(gettext("Des étapes sont déjà signées : reportez la task card au lieu de l'annuler."))
    for pr in card.part_requests.filter(status="requested"):
        pr.status = "cancelled"
        pr.save()
    card.status = "cancelled"
    card.deferral_reason = reason
    card.save()


@transaction.atomic
def defer_defect(defect, user, mel_reference, category, limit_date=None, limit_fh=None, limit_fc=None, procedure=""):
    staff = staff_for(user)
    if defect.status not in ("open",):
        raise ValidationError(gettext("Seul un défaut ouvert peut être reporté."))
    require_signing(staff, defect.aircraft.aircraft_type, certifying=True)
    if not mel_reference.strip() and category != "NM":
        raise ValidationError(gettext("Référence MEL/CDL obligatoire."))
    defect.mel_reference = mel_reference
    defect.deferral_category = category
    defect.deferral_limit_date = limit_date or defect.default_limit_date()
    defect.deferral_limit_fh = limit_fh
    defect.deferral_limit_fc = limit_fc
    if not (defect.deferral_limit_date or limit_fh or limit_fc):
        raise ValidationError(gettext("Une limite de report (date, heures ou cycles) est obligatoire."))
    defect.operational_procedure = procedure
    defect.status = "deferred"
    defect.deferred_by = staff
    defect.deferred_at = timezone.now()
    defect.fh_at_deferral, defect.fc_at_deferral = defect.aircraft.total_fh, defect.aircraft.total_fc
    defect.save()
    SignatureRecord.sign(user, defect, "defer", gettext("Report {mel_reference} cat. {category} jusqu'au {or_} – {description}").format(mel_reference=mel_reference, category=category, or_=defect.deferral_limit_date or '-', description=defect.description))


@transaction.atomic
def extend_deferral(defect, user, reason, reference, new_date=None, new_fh=None, new_fc=None, authority_notified=False):
    """Prorogation unique de l'intervalle de rectification (RIE), approuvée par la CAMO avant l'échéance."""
    if not user.has_perm("part145.extend_deferral"):
        raise ValidationError(gettext("Seul le personnel CAMO habilité peut approuver une prorogation de report."))
    defect = type(defect).objects.select_for_update().get(pk=defect.pk)
    problems = defect.extension_blockers(new_date, new_fh, new_fc)
    if not (reason or "").strip():
        problems.append(gettext("Justification obligatoire (pièce en commande, moyens indisponibles...)."))
    if not (reference or "").strip():
        problems.append(gettext("Référence de la RIE obligatoire."))
    if problems:
        raise ValidationError(problems)
    defect.original_limit_date, defect.original_limit_fh, defect.original_limit_fc = (
        defect.deferral_limit_date, defect.deferral_limit_fh, defect.deferral_limit_fc)
    if new_date is not None:
        defect.deferral_limit_date = new_date
    if new_fh is not None:
        defect.deferral_limit_fh = new_fh
    if new_fc is not None:
        defect.deferral_limit_fc = new_fc
    defect.extended = True
    defect.extension_reason, defect.extension_reference = reason, reference
    defect.extended_by, defect.extended_at = user, timezone.now()
    defect.authority_notified = authority_notified
    defect.save()
    limits = " / ".join(x for x in (
        f"{defect.deferral_limit_date:%d/%m/%Y}" if new_date else "", f"{new_fh} FH" if new_fh is not None else "",
        f"{new_fc} cycles" if new_fc is not None else "") if x)
    SignatureRecord.sign(user, defect, "extend", f"Prorogation unique {reference} du report {defect.mel_reference} cat. "
                                                 f"{defect.deferral_category} jusqu'à {limits} – {reason}")
    return defect


@transaction.atomic
def issue_crs(wp, user):
    staff = staff_for(user)
    blockers = wp.crs_blockers()
    if blockers:
        raise ValidationError(blockers)
    # Grande visite (entretien en base) : CRS par personnel de catégorie C ; sinon B1/B2/B3 (ou C).
    categories = ("C",) if wp.check_type == "major" else ("B1", "B2", "B3", "C")
    require_signing(staff, wp.aircraft.aircraft_type, certifying=True, categories=categories)
    statement = CRS_STATEMENT.format(approval=settings.AHMIS["APPROVAL_REF_145"])
    deferred = wp.task_cards.filter(status="deferred")
    if deferred.exists():
        statement += gettext(" Travaux reportés : ") + "; ".join(f"{c.number} ({c.deferral_reason})" for c in deferred) + "."
    open_defects = wp.aircraft.defects.filter(status="deferred")
    if open_defects.exists():
        statement += gettext(" Défauts reportés en cours : ") + ", ".join(f"{d.number} {d.mel_reference}" for d in open_defects) + "."
    wp.crs_by = staff
    wp.crs_date = timezone.now()
    wp.crs_statement = statement
    wp.status = "released"
    wp.save()
    ac = wp.aircraft
    if ac.status in ("maintenance", "aog"):
        ac.status = "active"
        ac.save()
    SignatureRecord.sign(user, wp, "crs", statement + gettext(" Aéronef {registration} à {total_fh} FH / {total_fc} cycles.").format(registration=ac.registration, total_fh=ac.total_fh, total_fc=ac.total_fc))


@transaction.atomic
def add_due_items_to_wp(wp, keys):
    """Crée les task cards à partir d'éléments sélectionnés dans la liste des échéances."""
    if wp.is_locked:
        raise ValidationError(gettext("Work package verrouillé."))
    created = []
    for key in keys:
        parts = key.split(":")
        kind = parts[0]
        if kind == "task":
            task = MaintenanceTask.objects.get(pk=int(parts[1]))
            comp = Component.objects.get(pk=int(parts[2])) if parts[2] != "0" else None
            if task.aircraft_type_id != wp.aircraft.aircraft_type_id:
                raise ValidationError(gettext("Tâche {reference} non applicable au type de l'aéronef.").format(reference=task.reference))
            if wp.task_cards.filter(task=task, component=comp).exclude(status="cancelled").exists():
                continue
            created.append(TaskCard.from_task(wp, task, comp))
        elif kind in ("llp", "tbo"):
            comp = Component.objects.get(pk=int(parts[1]))
            if wp.task_cards.filter(component=comp, origin="adhoc", task__isnull=True).exclude(status="cancelled").exists():
                continue
            card = TaskCard.objects.create(
                work_package=wp, origin="adhoc", component=comp,
                title=gettext("Dépose/repose {description} {pn} S/N {serial_number} ({TBO})").format(description=comp.part_number.description, pn=comp.part_number.pn, serial_number=comp.serial_number, TBO='limite de vie' if kind == 'llp' else 'TBO'),
                ata=comp.part_number.ata, skill="B1", requires_independent_inspection=True, estimated_mh=4,
                instructions=gettext("Remplacement en butée. Utiliser l'action « Changement de composant » de la task card."),
            )
            for i, text in enumerate([
                gettext("Vérifier la conformité de la pièce de rechange (P/N, S/N, Form 1, potentiel)"),
                gettext("Déposer le composant selon le manuel de maintenance"),
                gettext("Poser le composant de rechange et réaliser les contrôles associés"),
                gettext("Effectuer les essais requis"),
            ], start=1):
                TaskCardStep.objects.create(card=card, order=i, text=text)
            created.append(card)
        elif kind == "defect":
            d = Defect.objects.get(pk=int(parts[1]))
            created.append(card_from_defect(wp, d))
    return created


def card_from_defect(wp, defect):
    if defect.aircraft_id != wp.aircraft_id:
        raise ValidationError(gettext("Le défaut ne concerne pas l'aéronef du work package."))
    existing = defect.task_cards.exclude(status="cancelled").filter(work_package=wp).first()
    if existing:
        return existing
    return TaskCard.objects.create(
        work_package=wp, origin="defect", defect=defect,
        title=gettext("Rectification {number} : {description}").format(number=defect.number, description=defect.description[:120]), ata=defect.ata,
        instructions=gettext("Défaut signalé le {reported_on:%d/%m/%Y} par {reported_by}.\n{description}").format(reported_on=defect.reported_on, reported_by=defect.reported_by, description=defect.description),
        skill="B1", estimated_mh=1,
    )


@transaction.atomic
def change_component(card, user, removed=None, installed=None, position="", reason="", removal_type="unscheduled", removed_status="unserviceable"):
    staff = staff_for(user)
    _require_editable(card)
    if card.status != "in_progress":
        raise ValidationError(gettext("Démarrez la task card avant le changement de composant."))
    require_signing(staff, card.aircraft.aircraft_type)
    ac = card.aircraft
    today = timezone.localdate()
    if removed:
        removed.refresh_from_db()
        if removed.aircraft_id != ac.pk or removed.status != "installed":
            raise ValidationError(gettext("Le composant à déposer n'est pas installé sur cet aéronef."))
        position = position or removed.position
    if installed:
        installed.refresh_from_db()
        errors = installation_errors(installed, ac, position, task_card=card, replacing=removed)
        if errors:
            raise ValidationError(errors)  # rien n'a encore été modifié
    if removed:
        remove_component(removed, today, reason or gettext("Dépose"), removal_type, removed_status, card)
    if installed:
        install_component(installed, ac, position, today, task_card=card)
    SignatureRecord.sign(
        user, card, "perform",
        f"Changement de composant sur {ac.registration} position {position or '-'} : "
        f"déposé {removed or '-'} ({reason}) ; posé {installed or '-'}.",
    )
