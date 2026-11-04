"""Recherche globale (en-tête) : un seul champ pour retrouver tout enregistrement.

Chaque source n'est interrogée que si l'utilisateur a le droit de consulter le type d'objet
correspondant ; les comptes rendus d'événements respectent la confidentialité (culture juste).
"""
from django.apps import apps
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

MIN_LENGTH = 2
LIMIT = 15

# (libellé, modèle, champs interrogés, select_related)
SOURCES = [
    (_("Aéronef"), "fleet.Aircraft", ["registration", "msn"], []),
    (_("Composant"), "fleet.Component", ["serial_number", "part_number__pn"], ["part_number"]),
    (_("Référence P/N"), "fleet.PartNumber", ["pn", "description"], []),
    (_("Work package"), "part145.WorkPackage", ["number", "title"], ["aircraft"]),
    (_("Task card"), "part145.TaskCard", ["number", "title"], []),
    (_("Défaut"), "part145.Defect", ["number", "description"], []),
    (_("Personnel"), "part145.Staff", ["employee_number", "last_name", "first_name", "licence_number"], []),
    (_("AD / SB"), "camo.Directive", ["number", "title"], []),
    (_("Tâche programme"), "camo.MaintenanceTask", ["reference", "title"], []),
    (_("Modification / réparation"), "camo.ModificationRepair", ["number", "title", "approval_reference", "part21_reference"], ["aircraft"]),
    (_("Demande de pièce"), "logistics.PartRequest", ["number", "part_number__pn"], []),
    (_("Outillage"), "logistics.Tool", ["reference", "description", "serial_number"], []),
    (_("Certificat libératoire"), "logistics.ReleaseCertificate", ["tracking_number", "serial_or_batch"], ["part_number"]),
    (_("Commande d'achat"), "logistics.PurchaseOrder", ["number", "supplier__name"], ["supplier"]),
    (_("Fournisseur"), "logistics.Supplier", ["name", "approval_reference"], []),
    (_("Audit interne"), "quality.InternalAudit", ["number", "title", "area"], []),
    (_("Constat d'audit"), "quality.AuditFinding", ["number", "requirement", "description"], ["audit"]),
    (_("Document maîtrisé"), "quality.ControlledDocument", ["reference", "title"], []),
]


def global_search(user, q):
    """Liste de (libellé, objet, url), limitée par source et filtrée par les droits."""
    q = (q or "").strip()[:100]
    if len(q) < MIN_LENGTH:
        return []
    results = []
    for label, path, fields, related in SOURCES:
        model = apps.get_model(path)
        meta = model._meta
        if not user.has_perm(f"{meta.app_label}.view_{meta.model_name}"):
            continue
        cond = Q()
        for f in fields:
            cond |= Q(**{f"{f}__icontains": q})
        qs = model.objects.filter(cond)
        if related:
            qs = qs.select_related(*related)
        for obj in qs.distinct()[:LIMIT]:
            if hasattr(obj, "get_absolute_url"):
                results.append((label, obj, obj.get_absolute_url()))
    # Comptes rendus d'événements : seulement ceux que l'utilisateur peut voir
    if user.has_perm("safety.add_occurrencereport"):
        from apps.safety.views import visible_reports

        for r in visible_reports(user).filter(Q(number__icontains=q) | Q(title__icontains=q))[:LIMIT]:
            results.append((_("Compte rendu d'événement"), r, r.get_absolute_url()))
    return results
