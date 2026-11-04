"""Rôles AHMIS (groupes Django) et permissions associées.

Les permissions de l'application contrôlent l'accès aux écrans. Les signatures
sont en plus soumises aux autorisations individuelles du personnel (type, catégorie,
validité), vérifiées par les règles métier.
"""
from django.contrib.auth.models import Group, Permission

VIEW_ALL = [
    f"{app}.view_{m}" for app, models in {
        "fleet": ["aircrafttype", "aircraft", "utilisationrecord", "partnumber", "component", "installationrecord"],
        "camo": ["directive", "directiveapplicability", "maintenancetask", "taskrequiredpart", "taskaccomplishment", "airworthinessreview", "modificationrepair", "ampreview"],
        "part145": ["staff", "authorization", "qualification", "experiencerecord", "workpackage", "taskcard", "taskcardstep", "defect"],
        "safety": [],
        "quality": ["internalaudit", "auditfinding", "controlleddocument", "documentrevision"],
        "logistics": ["storelocation", "releasecertificate", "stockitem", "stockmovement", "partrequest", "tool", "toolusage", "toolcalibration",
                      "supplier", "purchaseorder", "purchaseorderline", "purchasereceipt"],
    }.items() for m in models
]


# Culture juste (376/2014 art. 16) : tout le personnel peut déclarer un événement.
REPORT = ["safety.add_occurrencereport"]
SAFETY_MANAGER = ["safety.add_occurrencereport", "safety.change_occurrencereport", "safety.view_occurrencereport",
                            "safety.view_all_occurrences"]


def _crud(app, *models, delete=False):
    acts = ["add", "change", "view"] + (["delete"] if delete else [])
    return [f"{app}.{a}_{m}" for m in models for a in acts]


ROLES = {
    "Ingénieur CAMO": VIEW_ALL
    + _crud("fleet", "aircrafttype", "aircraft", "utilisationrecord", "partnumber", "component")
    + _crud("camo", "directive", "directiveapplicability", "maintenancetask", "taskrequiredpart", "taskaccomplishment", "airworthinessreview", "modificationrepair", "ampreview", "transferrecord")
    + ["core.view_auditlog", "core.view_signaturerecord", "part145.extend_deferral"] + SAFETY_MANAGER,
    "Planificateur": VIEW_ALL + REPORT
    + _crud("part145", "workpackage", "taskcard", "defect")
    + ["core.view_signaturerecord"]
    + _crud("fleet", "utilisationrecord")
    + ["logistics.add_partrequest", "logistics.change_partrequest"],
    "Mécanicien": VIEW_ALL + REPORT
    + ["part145.add_defect", "part145.execute_taskcard", "part145.add_taskcard", "logistics.add_partrequest", "fleet.add_utilisationrecord"],
    "Certifiant": VIEW_ALL + REPORT
    + ["part145.add_defect", "part145.change_defect", "part145.execute_taskcard", "part145.certify_taskcard", "part145.add_taskcard",
       "part145.sign_crs", "part145.defer_defect", "logistics.add_partrequest", "camo.add_modificationrepair",
       "fleet.add_utilisationrecord", "core.view_signaturerecord"],
    "Magasinier": VIEW_ALL + REPORT
    + _crud("logistics", "storelocation", "releasecertificate", "stockitem", "stockmovement", "partrequest", "tool", "toolusage", "toolcalibration",
            "purchaseorder", "purchaseorderline", "purchasereceipt")
    + _crud("fleet", "component", "partnumber"),
    "Responsable qualité": VIEW_ALL
    + _crud("part145", "staff", "authorization", "qualification", "experiencerecord")
    + ["core.view_auditlog", "core.view_signaturerecord"] + SAFETY_MANAGER + ["safety.view_reporter_identity", "camo.view_transferrecord"]
    + _crud("quality", "internalaudit", "auditfinding", "controlleddocument", "documentrevision") + ["quality.approve_documentrevision"]
    + _crud("logistics", "supplier"),
}


def setup_roles():
    created = []
    for name, codes in ROLES.items():
        group, _ = Group.objects.get_or_create(name=name)
        perms = []
        for code in set(codes):
            app, codename = code.split(".")
            perm = Permission.objects.filter(content_type__app_label=app, codename=codename).first()
            if perm is None:
                raise RuntimeError(f"Permission inconnue : {code}")
            perms.append(perm)
        group.permissions.set(perms)
        created.append(group)
    return created
