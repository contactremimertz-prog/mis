"""Vue 3D d'un hélicoptère : urgence de chaque zone d'après les échéances CAMO.

Chaque échéance est rattachée à une zone par son chapitre ATA (tâche, P/N du
composant, défaut ou consigne). La zone prend le niveau le plus urgent :
dépassé ou en tolérance = haute, à planifier = moyenne, sinon « aucune échéance proche »
(jamais « conforme » : la vue ne se prononce pas sur la navigabilité).
Les autres chapitres (visites ATA 05, ARC, 29 hydraulique, 49 APU…) ne sont
rattachés à aucune zone : outside_zones() les compte et la carte les signale.
Le modèle 3D est l'un des quatre modèles de référence (H135, H145, NH90, Super Puma),
choisi d'après le type de l'appareil ; à défaut, un modèle générique. Il sert à situer
les zones, pas à représenter l'appareil réel.
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


# Modèles 3D de référence (static/ahmis/models/) : [id, libellé, codes de type servis exactement].
MODELS = [
    ("h135", "H135", ("H135", "EC135")),
    ("h145", "H145", ("H145", "BK117", "EC145")),
    ("nh90", "NH90", ("NH90",)),
    ("super-puma", "Super Puma", ("SUPERPUMA", "H215", "H225", "AS332", "EC225")),
]
# Types sans modèle propre : modèle de référence le plus proche (signalé comme approchant).
_NEAREST = {"H125": "h135", "AS350": "h135", "H130": "h135", "EC130": "h135", "H160": "h145", "H175": "super-puma"}


def model_for(type_code):
    """Modèle 3D d'un type d'appareil : {id, label, file, exact} ou None (modèle générique)."""
    code = re.sub(r"[\s_-]+", "", str(type_code or "")).upper()
    for mid, label, codes in MODELS:
        if code in codes:
            return {"id": mid, "label": label, "file": f"ahmis/models/{mid}.glb", "exact": True}
    mid = _NEAREST.get(code)
    if mid:
        label = next(m[1] for m in MODELS if m[0] == mid)
        return {"id": mid, "label": label, "file": f"ahmis/models/{mid}.glb", "exact": False}
    return None


# Photos du carrousel du tableau de bord (static/ahmis/photos/<id>.jpg), par modèle de référence.
# Crédit affiché sous la photo : à renseigner pour chaque fichier ajouté.
# Photos sous licence libre (Wikimedia Commons), redimensionnées ; détail dans static/ahmis/photos/CREDITS.md.
PHOTO_CREDITS = {
    "nh90": ("Ibex73, CC BY 4.0", "https://commons.wikimedia.org/wiki/File:NHIndustries_NH90_at_Paris_Air_Show_2025_(5).jpg"),
    "super-puma": ("Peter Gronemann, CC BY 2.0", "https://commons.wikimedia.org/wiki/File:AS332_Super_Puma_Heliweekend_(6847077680).jpg"),
    "h145": ("Asticoco, CC BY-SA 4.0 (recadrée)", "https://commons.wikimedia.org/wiki/File:H%C3%A9licopt%C3%A8re_Airbus_H145_-_S%C3%A9curit%C3%A9_civile_F-ZBPI_-_Hauts-de-Seine_(1).jpg"),
    "h135": ("Chme82, CC BY-SA 4.0", "https://commons.wikimedia.org/wiki/File:Airbus_Helicopters_H135_HB-ZUE.jpg"),
}


def photo_for(type_code):
    """Photo du type pour le carrousel : {file, credit} si le fichier existe, sinon None (dessin)."""
    from django.contrib.staticfiles import finders

    m = model_for(type_code)
    if not m or not m["exact"]:
        return None
    path = f"ahmis/photos/{m['id']}.jpg"
    if not finders.find(path):
        return None
    credit, url = PHOTO_CREDITS.get(m["id"], ("", ""))
    return {"file": path, "credit": credit, "url": url, "label": m["label"]}


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


def heli_texts():
    """Textes de la vue 3D lus par heli3d.js (traduits dans la langue de la requête)."""
    from django.utils.translation import gettext as _
    return {
        "zone": {"cellule": _("Cellule"), "portes": _("Portes et vitrages"), "feux": _("Feux et antennes"), "interieur": _("Intérieur")},
        "rev": {"gearbox": _("Contrôle de la boîte de transmission"), "dyn": _("Inspection des éléments dynamiques"),
                "engine": _("Inspection moteur"), "gear": _("Inspection du train"), "door": _("Contrôle des portes et verrous"),
                "glass": _("Inspection des vitrages"), "light": _("Contrôle des feux"), "avionics": _("Contrôle des équipements et antennes"),
                "cabin": _("Inspection de la cabine"), "struct": _("Inspection de structure")},
        "lvl": {"crit": _("Haute"), "warn": _("Moyenne"), "ok": _("Aucune échéance proche")},
        "rev_every": _("Intervalle : {n} h de vol"),
        "rev_rem": _("Reste {n} h"),
        "rev_over": _("Dépassée de {n} h"),
        "part_none": _("Aucune révision simulée sur cette pièce."),
        "sim": _("Révision simulée pour la démonstration : sans valeur de navigabilité. Seules les échéances CAMO font foi."),
        "summary": _("{n} pièces avec révision simulée : {c} dépassée(s), {w} à planifier."),
        "urgent": _("Pièces à traiter (simulé)"),
        "zone_of": _("Zone : {z}"),
        "zone_camo": _("Échéances CAMO de la zone : {l}"),
        "iso": _("Vue isolée"),
        "xray": _("Rayons X"),
        "back": _("Retour à la vue globale"),
        "loading": _("Chargement du modèle 3D…"),
        "model_error": _("Le modèle 3D n'a pas pu être chargé : modèle générique affiché."),
        "pick": _("Cliquez une pièce pour voir sa révision ; double-cliquez pour l'isoler."),
    }
