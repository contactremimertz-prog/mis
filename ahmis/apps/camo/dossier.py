"""Dossier complet de navigabilité d'un aéronef, pour transfert vers un autre organisme (M.A.307, CAMO.A.315(c)).

Lors d'un changement de CAMO / CAO ou de propriétaire, les enregistrements de maintien de la navigabilité
sont transférés au nouvel organisme. ``build_archive`` produit une archive ZIP autoportante :

* ``manifest.json``  : aéronef, émetteur, date, liste des fichiers et empreinte SHA-256 de chacun ;
* ``dossier.json``   : toutes les sections, lisibles par un autre système ;
* ``csv/<section>.csv`` : les mêmes données pour un tableur (séparateur « ; », UTF-8 avec BOM) ;
* ``synthese.html``  : état de navigabilité lisible et imprimable (temps totaux, LLP, AD, échéances, reports).

``verify_archive`` contrôle une archive reçue (empreintes du manifeste) sans rien importer en base.
Les comptes rendus d'événements (376/2014) ne sont pas inclus : ils relèvent du système de sécurité de l'organisme.
"""
import csv
import hashlib
import io
import json
import zipfile
from datetime import date, datetime
from decimal import Decimal

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.template.loader import render_to_string
from django.utils import timezone

FORMAT_VERSION = "1.0"
SKIP_FIELDS = {"created_by", "updated_by"}


def _value(obj, f):
    if isinstance(f, models.ForeignKey):
        rel = getattr(obj, f.name)
        return None if rel is None else str(rel)
    v = getattr(obj, f.attname)
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return str(v)
    if isinstance(v, models.fields.files.FieldFile):
        return v.name or ""
    if f.choices:
        return getattr(obj, f"get_{f.name}_display")()
    return v


def serialize(qs):
    """Liste de dicts (champs concrets ; clés étrangères en libellé lisible, choix en libellé)."""
    model = qs.model
    fields = [f for f in model._meta.concrete_fields if f.name not in SKIP_FIELDS]
    out = []
    for obj in qs:
        row = {"id": obj.pk}
        for f in fields:
            if f.primary_key:
                continue
            row[f.name] = _value(obj, f)
        out.append(row)
    return out


def _due_snapshot(aircraft):
    from .services import aircraft_due_list

    rows = []
    for i in aircraft_due_list(aircraft):
        rows.append({
            "nature": i.kind_label, "reference": i.reference, "libelle": i.label, "statut": i.status_label,
            "derniere_date": i.last_date.isoformat() if i.last_date else None,
            "dernier_fh": str(i.last_fh) if i.last_fh is not None else None, "dernier_fc": i.last_fc,
            "echeance_fh": str(i.due_fh) if i.due_fh is not None else None, "echeance_fc": i.due_fc,
            "echeance_date": i.due_date.isoformat() if i.due_date else None,
            "reste_fh": str(i.remaining_fh) if i.remaining_fh is not None else None, "reste_fc": i.remaining_fc,
            "reste_jours": i.remaining_days, "notes": i.notes,
        })
    return rows


def collect(aircraft):
    """Toutes les sections du dossier d'un aéronef (dict section -> liste de lignes)."""
    from apps.core.models import SignatureRecord
    from apps.fleet.models import Aircraft, Component, InstallationRecord
    from apps.logistics.models import ReleaseCertificate
    from apps.part145.models import Defect, TaskCard, TaskCardStep, WorkPackage

    from .models import AirworthinessReview, DirectiveApplicability, ModificationRepair, TaskAccomplishment

    ac = aircraft
    comp_ids = set(ac.components.values_list("pk", flat=True)) | set(ac.installation_records.values_list("component_id", flat=True))
    wps = WorkPackage.objects.filter(aircraft=ac)
    cards = TaskCard.objects.filter(work_package__in=wps)
    sig_q = models.Q()
    for qs in (wps, cards, Defect.objects.filter(aircraft=ac)):
        ct = ContentType.objects.get_for_model(qs.model)
        sig_q |= models.Q(content_type=ct, object_id__in=[str(pk) for pk in qs.values_list("pk", flat=True)])
    signatures = []
    for s in SignatureRecord.objects.filter(sig_q).order_by("signed_at"):
        signatures.append({"id": s.pk, "signe_le": s.signed_at.isoformat(), "signataire": s.signer_name, "licence": s.signer_licence,
                           "action": s.get_action_display(), "objet": s.object_repr, "declaration": s.statement,
                           "empreinte_sha256": s.digest, "integre": s.is_intact})
    return {
        "aeronef": serialize(Aircraft.objects.filter(pk=ac.pk)),
        "composants_installes": serialize(ac.components.filter(status="installed").select_related("part_number")),
        "composants_historique": serialize(Component.objects.filter(pk__in=comp_ids).exclude(aircraft=ac, status="installed")),
        "poses_deposes": serialize(InstallationRecord.objects.filter(aircraft=ac).order_by("installed_on")),
        "certificats_liberatoires": serialize(ReleaseCertificate.objects.filter(component_id__in=comp_ids)),
        "heures_cycles": serialize(ac.utilisation.order_by("date", "pk")),
        "realisations_taches": serialize(TaskAccomplishment.objects.filter(aircraft=ac).select_related("task").order_by("date", "pk")),
        "consignes_navigabilite": serialize(DirectiveApplicability.objects.filter(aircraft=ac).select_related("directive")),
        "modifications_reparations": serialize(ModificationRepair.objects.filter(aircraft=ac)),
        "examens_navigabilite": serialize(AirworthinessReview.objects.filter(aircraft=ac)),
        "defauts": serialize(Defect.objects.filter(aircraft=ac)),
        "work_packages": serialize(wps),
        "task_cards": serialize(cards),
        "task_card_etapes": serialize(TaskCardStep.objects.filter(card__in=cards)),
        "signatures": signatures,
        "echeances": _due_snapshot(ac),
    }


def _csv(rows):
    buf = io.StringIO()
    buf.write("﻿")
    if rows:
        cols = list(rows[0].keys())
        w = csv.DictWriter(buf, fieldnames=cols, delimiter=";", extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if v is None else v) for k, v in r.items()})
    return buf.getvalue().encode("utf-8")


def build_archive(aircraft, user=None, recipient="", purpose=""):
    """Construit l'archive ZIP du dossier. Retourne (octets, sha256 de l'archive, manifeste)."""
    from .services import aircraft_due_list

    data = collect(aircraft)
    generated = timezone.now().replace(microsecond=0)
    files = {
        "dossier.json": json.dumps({"format": "AHMIS-dossier", "version": FORMAT_VERSION, "sections": data},
                                   ensure_ascii=False, indent=1).encode("utf-8"),
    }
    for name, rows in data.items():
        files[f"csv/{name}.csv"] = _csv(rows)
    due = aircraft_due_list(aircraft)
    files["synthese.html"] = render_to_string("camo/dossier_synthese.html", {
        "ac": aircraft, "generated": generated, "organisation": settings.AHMIS["ORGANISATION"],
        "approval": settings.AHMIS["APPROVAL_REF_CAMO"], "recipient": recipient, "purpose": purpose,
        "due_alerts": [i for i in due if i.status != "ok"], "llp": [i for i in due if i.kind in ("llp", "tbo")],
        "directives": aircraft.directive_status.select_related("directive"),
        "mods": aircraft.modifications.all(), "deferred": aircraft.defects.filter(status__in=["open", "deferred"]),
        "components": aircraft.components.filter(status="installed").select_related("part_number"),
        "counts": {k: len(v) for k, v in data.items()},
        "signatures_broken": sum(1 for s in data["signatures"] if not s["integre"]),
    }).encode("utf-8")
    manifest = {
        "format": "AHMIS-dossier", "version": FORMAT_VERSION,
        "aeronef": {"immatriculation": aircraft.registration, "msn": aircraft.msn, "type": aircraft.aircraft_type.code},
        "emetteur": {"organisme": settings.AHMIS["ORGANISATION"], "agrement": settings.AHMIS["APPROVAL_REF_CAMO"],
                     "utilisateur": user.get_username() if user else ""},
        "destinataire": recipient, "objet": purpose, "genere_le": generated.isoformat(),
        "fichiers": {name: hashlib.sha256(content).hexdigest() for name, content in sorted(files.items())},
        "effectifs": {k: len(v) for k, v in data.items()},
    }
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=1))
        for name, content in files.items():
            z.writestr(name, content)
    raw = buf.getvalue()
    return raw, hashlib.sha256(raw).hexdigest(), manifest


def verify_archive(fileobj):
    """Contrôle une archive reçue : retourne (manifeste ou None, liste d'anomalies)."""
    problems = []
    try:
        z = zipfile.ZipFile(fileobj)
    except zipfile.BadZipFile:
        return None, ["Fichier illisible : ce n'est pas une archive ZIP."]
    with z:
        names = set(z.namelist())
        if "manifest.json" not in names:
            return None, ["manifest.json absent : archive non conforme au format AHMIS."]
        try:
            manifest = json.loads(z.read("manifest.json").decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return None, ["manifest.json illisible."]
        declared = manifest.get("fichiers", {})
        if not isinstance(declared, dict):
            return None, ["manifest.json : liste des fichiers invalide."]
        for name, digest in declared.items():
            if name not in names:
                problems.append(f"Fichier manquant : {name}")
                continue
            info = z.getinfo(name)
            if info.file_size > 500 * 1024 * 1024:
                problems.append(f"Fichier anormalement volumineux : {name}")
                continue
            if hashlib.sha256(z.read(name)).hexdigest() != digest:
                problems.append(f"Empreinte SHA-256 différente (fichier altéré) : {name}")
        extra = names - set(declared) - {"manifest.json"}
        for name in sorted(extra):
            problems.append(f"Fichier non déclaré dans le manifeste : {name}")
    return manifest, problems
