"""Vue 3D d'un hélicoptère : urgence de chaque zone d'après les échéances CAMO.

Chaque échéance est rattachée à une zone par son chapitre ATA (tâche, P/N du
composant, défaut ou consigne). La zone prend le niveau le plus urgent :
dépassé ou en tolérance = haute, à planifier = moyenne, sinon « aucune échéance proche »
(jamais « conforme » : la vue ne se prononce pas sur la navigabilité).
Les autres chapitres (visites ATA 05, ARC, 29 hydraulique, 49 APU…) ne sont
rattachés à aucune zone : outside_zones() les compte et la carte les signale.
Le modèle 3D est générique : il sert à situer les zones, pas à représenter l'appareil réel.
"""
import re

from django.db.models import Q
from django.utils.translation import gettext_lazy

from .models import Aircraft

ZONES = [
    ("rotor", gettext_lazy("Rotor principal et commandes rotor"), ("62", "67")),
    ("bte", gettext_lazy("Boîte de transmission principale"), ("63",)),
    ("tail", gettext_lazy("Rotor anticouple et transmission arrière"), ("64", "65")),
    ("engine", gettext_lazy("Moteur(s)"), tuple(str(n) for n in range(71, 81))),
    ("gear", gettext_lazy("Train d'atterrissage"), ("32",)),
]
ZONE_IDS = frozenset(z[0] for z in ZONES)
LEVELS = {
    "crit": gettext_lazy("Urgence haute"),
    "warn": gettext_lazy("Urgence moyenne"),
    "ok": gettext_lazy("Aucune échéance proche"),
    "none": gettext_lazy("Aucune échéance rattachée"),
}
_LEVEL_OF = {"overdue": "crit", "tolerance": "crit", "due_soon": "warn", "ok": "ok"}
_RANK = {"crit": 0, "warn": 1, "ok": 2, "none": 3}


def item_ata(item):
    """Chapitre ATA (2 chiffres) d'une échéance, ou chaîne vide.

    Sources dans l'ordre : tâche, défaut, consigne, P/N du composant. Une valeur
    qui ne commence pas par deux chiffres est ignorée et la source suivante est essayée.
    """
    comp = item.component
    sources = [getattr(o, "ata", "") for o in (item.task, item.defect, item.directive) if o is not None]
    if comp is not None:
        sources.append(comp.part_number.ata)
    for value in sources:
        chapter = _chapter(value or "")
        if chapter:
            return chapter
    return ""


def _chapter(ata):
    """« 62-11 » ou « 6211 » → « 62 » ; vide si la valeur ne commence pas par deux chiffres."""
    m = re.match(r"\s*(\d{2})", str(ata))
    return m.group(1) if m else ""


def zone_states(items):
    """Liste des zones avec leur niveau et les échéances qui les alimentent (les plus urgentes d'abord)."""
    out = []
    for zid, label, chapters in ZONES:
        rows = sorted((i for i in items if item_ata(i) in chapters), key=lambda i: (_RANK[_LEVEL_OF.get(i.status, "ok")], i.remaining_days if i.remaining_days is not None else 10**6))
        level = min((_LEVEL_OF.get(i.status, "ok") for i in rows), key=_RANK.get, default="none")
        out.append({"id": zid, "label": label, "chapters": ", ".join(chapters if len(chapters) < 3 else (chapters[0] + "–" + chapters[-1],)),
                    "level": level, "level_label": LEVELS[level], "items": rows})
    return out


def outside_zones(items):
    """Échéances urgentes qui ne relèvent d'aucune zone de la vue (visites, ARC, autres chapitres)."""
    chapters = {c for _, _, cs in ZONES for c in cs}
    rest = [i for i in items if item_ata(i) not in chapters]
    return {"crit": sum(1 for i in rest if _LEVEL_OF.get(i.status) == "crit"),
            "warn": sum(1 for i in rest if _LEVEL_OF.get(i.status) == "warn")}


def fleet_counts(aircraft_list, items):
    """Par hélicoptère : zones en urgence haute, en urgence moyenne et sans échéance rattachée.

    `items` est la liste des échéances de ces aéronefs (fleet_due_list). Renvoie
    {pk: {"crit": [zone…], "warn": [zone…], "none": [zone…], "outside": {"crit": n, "warn": n}}} ;
    « outside » compte les échéances urgentes hors zone (visites, ARC…) pour que la liste
    ne laisse pas croire qu'un appareil n'a rien d'urgent. Les avions sont absents.
    Les zones dont toutes les échéances sont lointaines ne figurent dans aucune liste.
    """
    by_ac = {}
    for i in items:
        by_ac.setdefault(i.aircraft.pk, []).append(i)
    out = {}
    for ac in aircraft_list:
        if ac.aircraft_type.category != "helicopter":
            continue
        groups = {"crit": [], "warn": [], "none": []}
        for z in zone_states(by_ac.get(ac.pk, [])):
            if z["level"] in groups:
                z["first"] = z["items"][0] if z["items"] else None
                groups[z["level"]].append(z)
        groups["outside"] = outside_zones(by_ac.get(ac.pk, []))
        out[ac.pk] = groups
    return out


def neighbours(aircraft):
    """Hélicoptères de la flotte (hors retirés, plus l'appareil affiché), avec le précédent et le suivant."""
    qs = Aircraft.objects.filter(aircraft_type__category="helicopter").filter(~Q(status="retired") | Q(pk=aircraft.pk))
    everyone = list(qs.select_related("aircraft_type").order_by("registration"))
    idx = next((n for n, a in enumerate(everyone) if a.pk == aircraft.pk), None)
    if idx is None or len(everyone) < 2:
        return {"all": everyone, "others": False, "prev": None, "next": None}
    return {"all": everyone, "others": True, "prev": everyone[idx - 1], "next": everyone[(idx + 1) % len(everyone)]}
