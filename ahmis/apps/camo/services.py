"""Moteur de calcul des échéances (butées) et du forecast.

Règle « le premier atteint » (whichever comes first) entre heures, cycles et calendrier.
Les dates prévisionnelles sont obtenues en projetant les compteurs avec l'utilisation
prévue de chaque aéronef (FH/jour, cycles/jour).
"""
import math
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from apps.fleet.models import Aircraft

from .models import DirectiveApplicability, MaintenanceTask, TaskAccomplishment
from django.utils.translation import gettext, gettext_lazy

STATUS_ORDER = {"overdue": 0, "tolerance": 1, "due_soon": 2, "ok": 3}
STATUS_LABELS = {
    "overdue": gettext_lazy("Dépassé"),
    "tolerance": gettext_lazy("En tolérance"),
    "due_soon": gettext_lazy("À planifier"),
    "ok": "OK",
}


def alert_days():
    return settings.AHMIS["ALERT_DAYS"]


@dataclass
class DueItem:
    aircraft: Aircraft
    kind: str  # task | component_task | llp | tbo | arc | defect | directive
    reference: str
    label: str
    status: str = "ok"
    task: Optional[MaintenanceTask] = None
    component: object = None
    defect: object = None
    directive: object = None
    last_date: Optional[date] = None
    last_fh: Optional[Decimal] = None
    last_fc: Optional[int] = None
    due_fh: Optional[Decimal] = None
    due_fc: Optional[int] = None
    due_date: Optional[date] = None
    remaining_fh: Optional[Decimal] = None
    remaining_fc: Optional[int] = None
    remaining_days: Optional[int] = None
    projected_date: Optional[date] = None
    driver: str = ""
    estimated_mh: Decimal = Decimal("0")
    interval_days_equiv: Optional[float] = None
    url: str = ""
    notes: str = ""
    parts: list = field(default_factory=list)

    @property
    def status_label(self):
        return STATUS_LABELS.get(self.status, self.status)

    @property
    def key(self):
        """Identifiant stable pour sélectionner l'élément dans le planning."""
        if self.kind in ("task", "component_task"):
            return f"task:{self.task.pk}:{self.component.pk if self.component else 0}"
        if self.kind in ("llp", "tbo"):
            return f"{self.kind}:{self.component.pk}"
        if self.kind == "defect":
            return f"defect:{self.defect.pk}"
        if self.kind == "directive":
            return f"directive:{self.directive.pk}"
        if self.kind == "modification":
            return f"modification:{self.reference}"
        return f"{self.kind}:{self.aircraft.pk}"

    @property
    def kind_label(self):
        return {
            "task": gettext("Tâche"), "component_task": gettext("Tâche composant"), "llp": "LLP", "tbo": "TBO",
            "arc": "ARC", "defect": gettext("Défaut reporté"), "directive": gettext("Consigne"), "modification": gettext("Modification / réparation"),
        }.get(self.kind, self.kind)


def _rates(aircraft, utilisation_factor=1.0):
    f = Decimal(str(utilisation_factor))
    return aircraft.planned_daily_fh * f, aircraft.planned_daily_fc * f


def _project(item, aircraft, cur_fh, cur_fc, today, utilisation_factor=1.0):
    """Calcule restants, date projetée, critère directeur."""
    rate_fh, rate_fc = _rates(aircraft, utilisation_factor)
    ref_date = aircraft.counters_date or today
    candidates = []
    if item.due_fh is not None:
        item.remaining_fh = (Decimal(item.due_fh) - Decimal(cur_fh)).quantize(Decimal("0.01"))
        if rate_fh > 0:
            days = math.floor(float(item.remaining_fh / rate_fh))
            candidates.append((ref_date + timedelta(days=days), "FH"))
        elif item.remaining_fh <= 0:
            candidates.append((today, "FH"))
    if item.due_fc is not None:
        item.remaining_fc = int(item.due_fc) - int(cur_fc)
        if rate_fc > 0:
            days = math.floor(item.remaining_fc / float(rate_fc))
            candidates.append((ref_date + timedelta(days=days), "cycles"))
        elif item.remaining_fc <= 0:
            candidates.append((today, "cycles"))
    if item.due_date is not None:
        candidates.append((item.due_date, "calendrier"))
    if candidates:
        item.projected_date, item.driver = min(candidates, key=lambda c: c[0])
        item.remaining_days = (item.projected_date - today).days


def _status(item, today, tol_fh=None, tol_fc=None, tol_days=None):
    over, beyond = False, False
    if item.remaining_fh is not None and item.remaining_fh < 0:
        over = True
        if tol_fh is None or -item.remaining_fh > tol_fh:
            beyond = True
    if item.remaining_fc is not None and item.remaining_fc < 0:
        over = True
        if tol_fc is None or -item.remaining_fc > tol_fc:
            beyond = True
    if item.due_date is not None and item.due_date < today:
        over = True
        if tol_days is None or (today - item.due_date).days > tol_days:
            beyond = True
    if over:
        item.status = "overdue" if beyond else "tolerance"
    elif item.projected_date and item.projected_date <= today + timedelta(days=alert_days()):
        item.status = "due_soon"
    else:
        item.status = "ok"


def _interval_equiv(task, aircraft, utilisation_factor=1.0):
    rate_fh, rate_fc = _rates(aircraft, utilisation_factor)
    vals = []
    if task.interval_fh and rate_fh > 0:
        vals.append(float(task.interval_fh / rate_fh))
    if task.interval_fc and rate_fc > 0:
        vals.append(task.interval_fc / float(rate_fc))
    if task.interval_days:
        vals.append(float(task.interval_days))
    return max(1.0, min(vals)) if vals else None


def next_base(acc):
    """Point de départ de l'intervalle suivant, critère par critère (règle de tolérance non cumulative).

    - Réalisée avant ou à la butée : l'intervalle repart de la réalisation (aucun gain possible).
    - Réalisée après la butée (dans la tolérance) : l'intervalle repart de la butée théorique ;
      la tolérance consommée n'est jamais reportée sur l'intervalle suivant.
    """
    fh = acc.counter_fh if acc.counter_fh is not None else Decimal("0")
    fc = acc.counter_fc if acc.counter_fc is not None else 0
    d = acc.date
    if acc.due_fh_at_done is not None and fh > acc.due_fh_at_done:
        fh = acc.due_fh_at_done
    if acc.due_fc_at_done is not None and fc > acc.due_fc_at_done:
        fc = acc.due_fc_at_done
    if acc.due_date_at_done is not None and d > acc.due_date_at_done:
        d = acc.due_date_at_done
    return fh, fc, d


def theoretical_due(task, aircraft, component=None, previous=None):
    """Butée théorique (FH, cycles, date) applicable à une nouvelle réalisation, d'après la réalisation précédente."""
    acc = {(task.pk, component.pk if component else None): previous}
    item = task_due(task, aircraft, component, accomplishments=acc)
    if item is None:
        return None, None, None
    return item.due_fh, item.due_fc, item.due_date


def task_due(task, aircraft, component=None, today=None, utilisation_factor=1.0, accomplishments=None):
    """Échéance d'une tâche pour un aéronef (ou un composant installé). None si clôturée."""
    today = today or timezone.localdate()
    if accomplishments is None:
        qs = TaskAccomplishment.objects.filter(task=task, aircraft=aircraft) if component is None else TaskAccomplishment.objects.filter(task=task, component=component)
        last = qs.order_by("-date", "-id").first()
    else:
        last = accomplishments.get((task.pk, component.pk if component else None))
    if component is not None:
        cur_fh, cur_fc = component.tsn_fh, component.csn
        birth = component.manufacture_date or aircraft.manufacture_date
    else:
        cur_fh, cur_fc = aircraft.total_fh, aircraft.total_fc
        birth = aircraft.manufacture_date

    item = DueItem(
        aircraft=aircraft, kind="component_task" if component else "task", task=task, component=component,
        reference=task.reference,
        label=task.title + (f" – {component.part_number.pn} S/N {component.serial_number}" if component else ""),
        estimated_mh=task.estimated_mh,
        url=reverse("camo:task_detail", args=[task.pk]),
    )
    if last:
        if not task.is_repetitive:
            return None  # tâche unique déjà réalisée
        item.last_date = last.date
        item.last_fh = last.comp_fh if component is not None else last.fh
        item.last_fc = last.comp_fc if component is not None else last.fc
        base_fh, base_fc, base_date = next_base(last)
        if task.interval_fh:
            item.due_fh = base_fh + task.interval_fh
        if task.interval_fc:
            item.due_fc = base_fc + task.interval_fc
        if task.interval_days:
            item.due_date = base_date + timedelta(days=task.interval_days)
        if last.used_tolerance:
            item.notes = gettext("Réalisée en tolérance : prochaine échéance comptée depuis la butée théorique.")
    else:
        has_threshold = any([task.threshold_fh, task.threshold_fc, task.threshold_days])
        fh = task.threshold_fh if has_threshold else task.interval_fh
        fc = task.threshold_fc if has_threshold else task.interval_fc
        days = task.threshold_days if has_threshold else task.interval_days
        base_fh, base_fc = Decimal("0"), 0
        if task.directive_id and task.directive:
            # Consigne : le délai de conformité court à partir de la date d'entrée en vigueur
            # (compteurs de l'aéronef ou du composant à cette date).
            eff = task.directive.effective_date
            birth = max(birth, eff)
            ac_fh, ac_fc = aircraft.counters_at(eff)
            if component is not None:
                base_fh = max(Decimal("0"), component.tsn_fh - (aircraft.total_fh - ac_fh))
                base_fc = max(0, component.csn - (aircraft.total_fc - ac_fc))
            else:
                base_fh, base_fc = ac_fh, ac_fc
            if not (fh or fc or days):
                item.due_date = eff  # applicable immédiatement
        if fh:
            item.due_fh = base_fh + fh
        if fc:
            item.due_fc = base_fc + fc
        if days:
            item.due_date = birth + timedelta(days=days)
    _project(item, aircraft, cur_fh, cur_fc, today, utilisation_factor)
    _status(item, today, task.tolerance_fh, task.tolerance_fc, task.tolerance_days)
    item.interval_days_equiv = _interval_equiv(task, aircraft, utilisation_factor) if task.is_repetitive else None
    item.parts = [(rp.part_number, rp.quantity) for rp in task.required_parts.all()]
    return item


def component_limit_items(aircraft, today=None, utilisation_factor=1.0):
    today = today or timezone.localdate()
    items = []
    for comp in aircraft.components.filter(status="installed").select_related("part_number"):
        rows = comp.life_status(today)
        for kind in ("llp", "tbo"):
            krows = [r for r in rows if r["kind"] == kind]
            if not krows:
                continue
            item = DueItem(
                aircraft=aircraft, kind=kind, component=comp,
                reference=f"{comp.part_number.pn} S/N {comp.serial_number}",
                label=f"{gettext('Limite de vie') if kind == 'llp' else gettext('Révision (TBO)')} – {comp.part_number.description}"
                      + (f" ({comp.position})" if comp.position else ""),
                url=reverse("fleet:component_detail", args=[comp.pk]),
            )
            cur_fh = comp.tsn_fh if kind == "llp" else comp.tso_fh
            cur_fc = comp.csn if kind == "llp" else comp.cso
            pn = comp.part_number
            lim_fh = pn.life_limit_fh if kind == "llp" else pn.tbo_fh
            lim_fc = pn.life_limit_fc if kind == "llp" else pn.tbo_fc
            lim_days = pn.life_limit_days if kind == "llp" else pn.tbo_days
            item.due_fh = lim_fh
            item.due_fc = lim_fc
            if lim_days:
                ref = comp.manufacture_date if kind == "llp" else (comp.last_overhaul_date or comp.manufacture_date)
                if ref:
                    item.due_date = ref + timedelta(days=lim_days)
            _project(item, aircraft, cur_fh, cur_fc, today, utilisation_factor)
            _status(item, today)
            items.append(item)
    return items


def arc_item(aircraft, today=None):
    today = today or timezone.localdate()
    if not aircraft.arc_expiry:
        return None
    item = DueItem(
        aircraft=aircraft, kind="arc", reference="ARC", label=gettext("Expiration du certificat d'examen de navigabilité (ARC)"),
        due_date=aircraft.arc_expiry, url=reverse("fleet:aircraft_detail", args=[aircraft.pk]),
    )
    item.projected_date = aircraft.arc_expiry
    item.remaining_days = (aircraft.arc_expiry - today).days
    item.driver = "calendrier"
    _status(item, today)
    return item


def defect_items(aircraft, today=None):
    from apps.part145.models import Defect

    today = today or timezone.localdate()
    items = []
    for d in Defect.objects.filter(aircraft=aircraft, status="deferred"):
        item = DueItem(
            aircraft=aircraft, kind="defect", defect=d, reference=d.number,
            label=gettext("Défaut reporté {or_} cat. {or_2} : {description}").format(or_=d.mel_reference or '', or_2=d.deferral_category or '-', description=d.description[:80]),
            url=reverse("part145:defect_detail", args=[d.pk]), estimated_mh=Decimal("1"),
        )
        item.due_date = d.deferral_limit_date
        if d.deferral_limit_fh is not None:
            item.due_fh = d.deferral_limit_fh
        if d.deferral_limit_fc is not None:
            item.due_fc = d.deferral_limit_fc
        if d.extended:
            item.notes = gettext("Délai prorogé une fois ({extension_reference}) : aucune nouvelle prorogation possible.").format(extension_reference=d.extension_reference)
        _project(item, aircraft, aircraft.total_fh, aircraft.total_fc, today)
        _status(item, today)
        items.append(item)
    return items


def directive_items(aircraft, today=None):
    """Consignes à évaluer ou ouvertes sans tâche de suivi : alerte CAMO."""
    today = today or timezone.localdate()
    items = []
    for app in DirectiveApplicability.objects.filter(aircraft=aircraft, status__in=["to_assess", "open"]).select_related("directive"):
        if app.status == "open" and app.directive.tasks.filter(aircraft_type=aircraft.aircraft_type, active=True).exists():
            continue  # suivie par une tâche
        d = app.directive
        item = DueItem(
            aircraft=aircraft, kind="directive", directive=d, reference=d.number,
            label=(gettext("À évaluer : ") if app.status == "to_assess" else gettext("Sans tâche de suivi : ")) + d.title,
            url=reverse("camo:directive_detail", args=[d.pk]),
        )
        item.due_date = d.effective_date
        item.projected_date = d.effective_date
        item.remaining_days = (d.effective_date - today).days
        item.status = "overdue" if d.effective_date <= today else "due_soon"
        items.append(item)
    return items


def modification_items(aircraft, today=None):
    """Modifications / réparations appliquées dont le suivi n'est pas soldé (ICA, pesée, manuel de vol)."""
    from .models import ModificationRepair

    today = today or timezone.localdate()
    items = []
    for m in ModificationRepair.objects.filter(aircraft=aircraft, status="embodied"):
        issues = m.compliance_issues
        if not issues:
            continue
        item = DueItem(aircraft=aircraft, kind="modification", reference=m.number,
                       label=f"{m.title} : " + " ; ".join(issues), url=reverse("camo:mod_detail", args=[m.pk]))
        item.due_date = m.embodied_on
        item.projected_date = m.embodied_on
        item.remaining_days = (m.embodied_on - today).days if m.embodied_on else None
        item.status = "due_soon"
        items.append(item)
    return items


def _accomplishment_index(aircraft_list):
    """Dernière réalisation par (tâche, composant) pour limiter les requêtes."""
    idx_ac, idx_comp = {}, {}
    qs = TaskAccomplishment.objects.filter(aircraft__in=aircraft_list).order_by("date", "id")
    for acc in qs:
        idx_ac.setdefault(acc.aircraft_id, {})
        if acc.component_id:
            idx_comp[(acc.task_id, acc.component_id)] = acc
        else:
            idx_ac[acc.aircraft_id][(acc.task_id, None)] = acc
    return idx_ac, idx_comp


def aircraft_due_list(aircraft, today=None, utilisation_factor=1.0, include_ok=True):
    return fleet_due_list([aircraft], today, utilisation_factor, include_ok)


def fleet_due_list(aircraft_list=None, today=None, utilisation_factor=1.0, include_ok=True):
    today = today or timezone.localdate()
    if aircraft_list is None:
        aircraft_list = list(Aircraft.objects.exclude(status="retired").select_related("aircraft_type"))
    idx_ac, idx_comp = _accomplishment_index(aircraft_list)
    tasks_by_type = {}
    for t in MaintenanceTask.objects.filter(active=True).select_related("directive", "part_number").prefetch_related("effectivity", "required_parts__part_number"):
        tasks_by_type.setdefault(t.aircraft_type_id, []).append(t)
    items = []
    for ac in aircraft_list:
        acc_ac = idx_ac.get(ac.pk, {})
        installed = list(ac.components.filter(status="installed").select_related("part_number"))
        for task in tasks_by_type.get(ac.aircraft_type_id, []):
            eff = list(task.effectivity.all())
            if eff and ac not in eff:
                continue
            if task.part_number_id:
                for comp in [c for c in installed if c.part_number_id == task.part_number_id]:
                    it = task_due(task, ac, comp, today, utilisation_factor, {(task.pk, comp.pk): idx_comp.get((task.pk, comp.pk))})
                    if it:
                        items.append(it)
            else:
                it = task_due(task, ac, None, today, utilisation_factor, acc_ac)
                if it:
                    items.append(it)
        items.extend(component_limit_items(ac, today, utilisation_factor))
        a = arc_item(ac, today)
        if a:
            items.append(a)
        items.extend(defect_items(ac, today))
        items.extend(directive_items(ac, today))
        items.extend(modification_items(ac, today))
    if not include_ok:
        items = [i for i in items if i.status != "ok"]
    items.sort(key=lambda i: (STATUS_ORDER.get(i.status, 9), i.projected_date or date.max, i.aircraft.registration))
    return items


@dataclass
class ForecastEvent:
    date: date
    item: DueItem
    occurrence: int
    overdue: bool = False


def forecast(aircraft_list=None, horizon_days=None, today=None, utilisation_factor=1.0):
    """Occurrences prévisionnelles sur l'horizon (les tâches répétitives sont déroulées)."""
    today = today or timezone.localdate()
    horizon_days = horizon_days or settings.AHMIS["FORECAST_DAYS"]
    end = today + timedelta(days=horizon_days)
    events = []
    for item in fleet_due_list(aircraft_list, today, utilisation_factor):
        if not item.projected_date:
            continue
        first = item.projected_date
        overdue = first < today
        d = max(first, today)
        n = 1
        while d <= end:
            events.append(ForecastEvent(date=d, item=item, occurrence=n, overdue=overdue and n == 1))
            if item.kind not in ("task", "component_task") or not item.interval_days_equiv:
                break
            d = d + timedelta(days=math.floor(item.interval_days_equiv))
            n += 1
            if n > 400:
                break
    events.sort(key=lambda e: (e.date, e.item.aircraft.registration, e.item.reference))
    return events


def forecast_summary(events):
    """Agrégats mensuels : nombre d'échéances, charge (h.h), pièces."""
    months = {}
    for e in events:
        key = (e.date.year, e.date.month)
        m = months.setdefault(key, {"year": e.date.year, "month": e.date.month, "count": 0, "mh": Decimal("0"), "parts": {}, "removals": 0, "by_aircraft": {}})
        m["count"] += 1
        m["mh"] += e.item.estimated_mh or 0
        reg = e.item.aircraft.registration
        m["by_aircraft"][reg] = m["by_aircraft"].get(reg, 0) + 1
        if e.item.kind in ("llp", "tbo"):
            m["removals"] += 1
        for pn, qty in e.item.parts:
            m["parts"][pn.pn] = m["parts"].get(pn.pn, Decimal("0")) + qty
    return [months[k] for k in sorted(months)]
