"""Vue 3D d'un hélicoptère : urgence de chaque zone d'après les échéances CAMO.

Chaque échéance est rattachée à une zone par son chapitre ATA (tâche, P/N du
composant, défaut ou consigne). La zone prend le niveau le plus urgent :
dépassé ou en tolérance = haute, à planifier = moyenne, sinon conforme.
Les autres chapitres (visites ATA 05, ARC, 29 hydraulique, 49 APU…) ne sont
rattachés à aucune zone : outside_zones() les compte et la carte les signale.
Le modèle 3D est générique : il sert à situer les zones, pas à représenter l'appareil réel.
"""
import re

from django.utils.translation import gettext_lazy, pgettext_lazy

ZONES = [
    ("rotor", gettext_lazy("Rotor principal et commandes rotor"), ("62", "67")),
    ("bte", gettext_lazy("Boîte de transmission principale"), ("63",)),
    ("tail", gettext_lazy("Rotor anticouple et transmission arrière"), ("64", "65")),
    ("engine", gettext_lazy("Moteur(s)"), tuple(str(n) for n in range(71, 81))),
    ("gear", gettext_lazy("Train d'atterrissage"), ("32",)),
]
LEVELS = {
    "crit": gettext_lazy("Urgence haute"),
    "warn": gettext_lazy("Urgence moyenne"),
    "ok": pgettext_lazy("vue 3D", "Conforme"),
    "none": gettext_lazy("Aucune échéance rattachée"),
}
_LEVEL_OF = {"overdue": "crit", "tolerance": "crit", "due_soon": "warn", "ok": "ok"}
_RANK = {"crit": 0, "warn": 1, "ok": 2, "none": 3}


def item_ata(item):
    """Chapitre ATA (2 chiffres) d'une échéance, ou chaîne vide.

    Sources dans l'ordre : tâche, défaut, consigne, P/N du composant. Une valeur
    non exploitable est ignorée et la source suivante est essayée.
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
