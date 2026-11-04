"""Conservation réglementaire des enregistrements (M.A.305(h), CAMO.A.305, 145.A.55(c), 145.A.35(j)).

Chaque règle calcule, pour un enregistrement, la date jusqu'à laquelle il doit au minimum être conservé :

* ``None``  : conservation sans échéance pour l'instant (aéronef encore exploité, dossier ouvert,
  dernier état connu d'une tâche...) ;
* une date : durée minimale atteinte à cette date ; au-delà, l'enregistrement *peut* être archivé.

AHMIS ne supprime jamais rien automatiquement : le rapport « Conservation » liste les enregistrements
dont la durée minimale est échue, et la décision d'archivage ou de purge reste humaine (procédure MOE/CAME).
Deux protections se cumulent : ``TrackedModel.delete()`` refuse toute suppression unitaire depuis
l'application, et ``guard_delete`` (signal pre_delete) bloque les suppressions en masse (admin Django,
scripts) d'enregistrements encore sous obligation de conservation.
"""
from collections import defaultdict
from dataclasses import dataclass, field

from django.apps import apps
from django.conf import settings
from django.db.models import ProtectedError
from django.utils import timezone

from .dates import add_months


def _cfg(key, default):
    return settings.AHMIS.get(key, default)


def work_months():
    """Dossiers de travaux et CRS : 36 mois après la remise en service (145.A.55(c), M.A.305(h))."""
    return _cfg("RETENTION_WORK_MONTHS", 36)


def life_months():
    """Enregistrements d'état (heures, AD, LLP, modifications) : 12 mois après retrait définitif."""
    return _cfg("RETENTION_AFTER_WITHDRAWAL_MONTHS", 12)


def staff_months():
    """Dossier du personnel : 3 ans après le départ (145.A.35(j))."""
    return _cfg("RETENTION_STAFF_MONTHS", 36)


def _later(*dates):
    """Date la plus tardive ; ``None`` (sans échéance) l'emporte toujours."""
    if any(d is None for d in dates):
        return None
    return max(dates)


# ------------------------------------------------------------------ calculs par nature
def aircraft_life(aircraft):
    if aircraft is None or not aircraft.withdrawn_on:
        return None
    return add_months(aircraft.withdrawn_on, life_months())


def component_life(component):
    if component is None:
        return None
    withdrawn = getattr(component, "scrapped_on", None)
    if component.status != "scrapped" or not withdrawn:
        return None
    return add_months(withdrawn, life_months())


def work_package_until(wp):
    if wp.status == "released" and wp.crs_date:
        return add_months(wp.crs_date, work_months())
    if wp.status == "cancelled":
        return add_months(wp.updated_at, work_months())
    return None


def task_card_until(card):
    return work_package_until(card.work_package)


def defect_until(d):
    if d.status == "rectified" and d.rectified_on:
        return add_months(d.rectified_on, work_months())
    if d.status == "cancelled":
        return add_months(d.updated_at, work_months())
    return None


_LOOKUP = object()


def accomplishment_until(acc, superseded_by=_LOOKUP):
    """Une réalisation est conservée tant qu'elle n'est pas remplacée par une réalisation équivalente,
    et au moins 36 mois. Pour les AD, ALS et CMR, elle constitue l'état de conformité : conservée
    jusqu'à 12 mois après le retrait de l'aéronef (ou du composant)."""
    if acc.task.source in ("AD", "ALS", "CMR"):
        return aircraft_life(acc.aircraft) if acc.component_id is None else _later(aircraft_life(acc.aircraft), component_life(acc.component))
    if superseded_by is _LOOKUP:
        superseded_by = (acc.__class__.objects.filter(task=acc.task, aircraft=acc.aircraft, component=acc.component, date__gt=acc.date)
                         .order_by("date").first())
    if superseded_by is None:
        return aircraft_life(acc.aircraft)
    return add_months(max(acc.date, superseded_by.date), work_months())


def installation_until(rec):
    return _later(aircraft_life(rec.aircraft), component_life(rec.component))


def staff_until(s):
    if s.active or not s.left_on:
        return None
    return add_months(s.left_on, staff_months())


def amp_review_until(r):
    newer = r.__class__.objects.filter(aircraft_type=r.aircraft_type, review_date__gt=r.review_date).exists()
    return add_months(r.review_date, work_months()) if newer else None


# ------------------------------------------------------------------ catalogue des règles
@dataclass
class Rule:
    key: str
    label: str
    model: str  # "app_label.Model"
    reference: str
    until: object
    period: str
    select_related: list = field(default_factory=list)

    @property
    def model_class(self):
        return apps.get_model(self.model)


RULES = [
    Rule("aircraft", "Dossiers aéronefs", "fleet.Aircraft", "M.A.305(h)(1)",
         aircraft_life, "12 mois après retrait définitif", ["aircraft_type"]),
    Rule("components", "Fiches composants (TSN/CSN, LLP)", "fleet.Component", "M.A.305(h)(1)",
         component_life, "12 mois après retrait définitif (rebut)", ["part_number"]),
    Rule("work_packages", "Work packages et CRS", "part145.WorkPackage", "145.A.55(c), M.A.305(h)",
         work_package_until, "36 mois après le CRS", ["aircraft"]),
    Rule("task_cards", "Task cards (comptes rendus détaillés)", "part145.TaskCard", "145.A.55(c), M.A.305(h)",
         task_card_until, "36 mois après le CRS du work package", ["work_package"]),
    Rule("defects", "Défauts et rectifications", "part145.Defect", "145.A.55(c), M.A.305(h)",
         defect_until, "36 mois après la rectification", ["aircraft"]),
    Rule("accomplishments", "Réalisations de tâches", "camo.TaskAccomplishment", "M.A.305(h)",
         accomplishment_until, "36 mois et jusqu'au remplacement ; AD/ALS/CMR : 12 mois après retrait de l'aéronef",
         ["task", "aircraft", "component"]),
    Rule("utilisation", "Heures et cycles (temps totaux)", "fleet.UtilisationRecord", "M.A.305(h)(1)",
         lambda r: aircraft_life(r.aircraft), "12 mois après retrait définitif de l'aéronef", ["aircraft"]),
    Rule("directives", "État des consignes de navigabilité", "camo.DirectiveApplicability", "M.A.305(h)(1)",
         lambda r: aircraft_life(r.aircraft), "12 mois après retrait définitif de l'aéronef", ["aircraft"]),
    Rule("modifications", "Modifications et réparations", "camo.ModificationRepair", "M.A.305(h)(1)",
         lambda r: aircraft_life(r.aircraft), "12 mois après retrait définitif de l'aéronef", ["aircraft"]),
    Rule("installations", "Historique de pose / dépose (LLP, back-to-birth)", "fleet.InstallationRecord", "M.A.305(h)(1)",
         installation_until, "12 mois après retrait définitif de l'aéronef et du composant", ["aircraft", "component"]),
    Rule("arc", "Examens de navigabilité (ARC)", "camo.AirworthinessReview", "CAMO.A.220, M.A.714",
         lambda r: add_months(r.review_date, work_months()), "36 mois après l'examen", ["aircraft"]),
    Rule("amp_reviews", "Revues du programme d'entretien", "camo.AmpReview", "CAMO.A.220",
         amp_review_until, "36 mois après remplacement par une revue plus récente", ["aircraft_type"]),
    Rule("staff", "Dossiers du personnel", "part145.Staff", "145.A.35(j)",
         staff_until, "3 ans après le départ", []),
    Rule("occurrences", "Comptes rendus d'événements", "safety.OccurrenceReport", "376/2014, 145.A.60, 145.A.55",
         lambda r: add_months(r.closed_on or r.updated_at, work_months()) if r.status in ("closed", "not_reportable") else None,
         "36 mois après la clôture", ["aircraft"]),
    Rule("calibrations", "Étalonnages d'outillage", "logistics.ToolCalibration", "145.A.40, 145.A.55",
         lambda r: add_months(r.date, work_months()), "36 mois après l'étalonnage", ["tool"]),
]
RULES_BY_KEY = {r.key: r for r in RULES}
RULES_BY_MODEL = {r.model.lower(): r for r in RULES}


def rule_for(obj):
    return RULES_BY_MODEL.get(obj._meta.label_lower)


def retained_until(obj):
    rule = rule_for(obj)
    return rule.until(obj) if rule else None


def evaluate(rule, on_date=None):
    """Évalue une règle sur toute la base : liste de (obj, date_limite) et compteurs."""
    on_date = on_date or timezone.localdate()
    qs = rule.model_class.objects.select_related(*rule.select_related)
    rows = []
    if rule.key == "accomplishments":
        # Calcul en lot : la réalisation suivante d'une même tâche/aéronef/composant la remplace
        by_key = defaultdict(list)
        for a in qs.order_by("date", "pk"):
            by_key[(a.task_id, a.aircraft_id, a.component_id)].append(a)
        for accs in by_key.values():
            for i, a in enumerate(accs):
                nxt = next((x for x in accs[i + 1:] if x.date > a.date), None)
                rows.append((a, accomplishment_until(a, superseded_by=nxt)))
    else:
        rows = [(o, rule.until(o)) for o in qs]
    counts = {"total": len(rows), "open": 0, "running": 0, "eligible": 0}
    for _, until in rows:
        if until is None:
            counts["open"] += 1
        elif until > on_date:
            counts["running"] += 1
        else:
            counts["eligible"] += 1
    return rows, counts


def guard_delete(sender, instance, **kwargs):
    """Signal pre_delete : interdit la suppression d'un enregistrement encore sous obligation de conservation."""
    if not _cfg("RETENTION_GUARD", True):
        return
    rule = rule_for(instance)
    if rule is None:
        return
    until = rule.until(instance)
    if until is None or until > timezone.localdate():
        when = "sans échéance pour l'instant" if until is None else f"jusqu'au {until:%d/%m/%Y}"
        raise ProtectedError(
            f"Suppression refusée : {rule.label.lower()} à conserver {when} ({rule.reference}).", {instance})


def connect_guards():
    from django.db.models.signals import pre_delete

    for rule in RULES:
        pre_delete.connect(guard_delete, sender=rule.model_class, dispatch_uid=f"ahmis-retention-{rule.key}")
