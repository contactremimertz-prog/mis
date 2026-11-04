from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone

from apps.core.dates import add_months as _add_months
from apps.core.models import TrackedModel
from apps.fleet.models import Aircraft, AircraftType, Component, PartNumber

SKILLS = [
    ("A", "Cat. A"), ("B1", "Cat. B1"), ("B2", "Cat. B2"), ("B3", "Cat. B3"), ("C", "Cat. C"),
]


class Directive(TrackedModel):
    """Consigne de navigabilité (AD) ou bulletin service (SB / ASB)."""

    KINDS = [("AD", "Consigne de navigabilité (AD)"), ("EAD", "AD d'urgence (EAD)"), ("ASB", "Bulletin service d'alerte (ASB)"), ("SB", "Bulletin service (SB)"), ("SIL", "Lettre d'information (SIL/IN)")]
    AUTHORITIES = [("EASA", "EASA"), ("FAA", "FAA"), ("DGAC", "DGAC"), ("TCCA", "TCCA"), ("OEM", "Constructeur")]

    number = models.CharField("numéro", max_length=40, unique=True)
    kind = models.CharField("type", max_length=4, choices=KINDS, default="AD")
    authority = models.CharField("émetteur", max_length=5, choices=AUTHORITIES, default="EASA")
    revision = models.CharField("révision", max_length=10, blank=True)
    title = models.CharField("objet", max_length=200)
    effective_date = models.DateField("date d'entrée en vigueur")
    aircraft_types = models.ManyToManyField(AircraftType, blank=True, verbose_name="types concernés", related_name="directives")
    part_numbers = models.ManyToManyField(PartNumber, blank=True, verbose_name="P/N concernés", related_name="directives")
    applicability_text = models.TextField("applicabilité (texte de la consigne)", blank=True)
    required_action = models.TextField("action requise", blank=True)
    is_recurring = models.BooleanField("action répétitive", default=False)
    related_sb = models.CharField("SB associé", max_length=60, blank=True)
    supersedes = models.ForeignKey("self", on_delete=models.PROTECT, null=True, blank=True, verbose_name="remplace", related_name="superseded_by")
    document = models.FileField("document", upload_to="consignes/", blank=True)

    class Meta:
        ordering = ["-effective_date", "number"]
        verbose_name = "consigne / bulletin"
        verbose_name_plural = "consignes et bulletins (AD/SB)"

    def __str__(self):
        return f"{self.number} – {self.title}"

    def get_absolute_url(self):
        return reverse("camo:directive_detail", args=[self.pk])

    def potentially_affected_aircraft(self):
        qs = Aircraft.objects.exclude(status="retired")
        types = list(self.aircraft_types.all())
        pns = list(self.part_numbers.all())
        result = set()
        if types:
            result |= set(qs.filter(aircraft_type__in=types))
        if pns:
            result |= set(qs.filter(components__part_number__in=pns, components__status="installed"))
        return sorted(result, key=lambda a: a.registration)


class DirectiveApplicability(TrackedModel):
    STATUSES = [
        ("to_assess", "À évaluer"),
        ("open", "Applicable – à réaliser"),
        ("recurring", "Applicable – répétitive en cours"),
        ("complied", "Appliquée (terminée)"),
        ("not_applicable", "Non applicable"),
    ]

    directive = models.ForeignKey(Directive, on_delete=models.PROTECT, related_name="applicabilities", verbose_name="consigne")
    aircraft = models.ForeignKey(Aircraft, on_delete=models.PROTECT, related_name="directive_status", verbose_name="aéronef")
    status = models.CharField("statut", max_length=16, choices=STATUSES, default="to_assess")
    justification = models.TextField("justification / méthode de conformité", blank=True)
    compliance_date = models.DateField("date de conformité", null=True, blank=True)
    compliance_fh = models.DecimalField("FH à la conformité", max_digits=10, decimal_places=2, null=True, blank=True)
    compliance_fc = models.PositiveIntegerField("cycles à la conformité", null=True, blank=True)
    reviewed_by = models.CharField("évalué par", max_length=120, blank=True)
    reviewed_on = models.DateField("évalué le", null=True, blank=True)

    class Meta:
        unique_together = [("directive", "aircraft")]
        ordering = ["directive__number", "aircraft__registration"]
        verbose_name = "statut de consigne par aéronef"
        verbose_name_plural = "statuts de consignes par aéronef"

    def __str__(self):
        return f"{self.directive.number} / {self.aircraft.registration} : {self.get_status_display()}"

    def get_absolute_url(self):
        return reverse("camo:applicability_update", args=[self.pk])

    def clean(self):
        if self.status == "not_applicable" and not self.justification.strip():
            raise ValidationError({"justification": "Une non-applicabilité doit être justifiée."})
        if self.status == "complied" and not self.compliance_date:
            raise ValidationError({"compliance_date": "Date de conformité obligatoire."})


class MaintenanceTask(TrackedModel):
    """Tâche du programme d'entretien (AMP) : MSM/MPD, ALS, AD, SB..."""

    SOURCES = [
        ("AMP", "Programme d'entretien (MSM/MPD)"),
        ("ALS", "Limitations de navigabilité (ALS / ch. 4)"),
        ("AD", "Consigne de navigabilité"),
        ("SB", "Bulletin service"),
        ("CMR", "CMR"),
        ("OPS", "Exigence exploitant / opérationnelle"),
    ]
    TASK_TYPES = [
        ("INSP", "Inspection / visite"), ("DET", "Inspection détaillée"), ("GVI", "Inspection visuelle générale"),
        ("LUB", "Lubrification"), ("SVC", "Entretien courant / servicing"), ("OPC", "Contrôle opérationnel"),
        ("FNC", "Contrôle fonctionnel"), ("NDT", "Contrôle non destructif"), ("RST", "Restauration"),
        ("DIS", "Remplacement / dépose (HT)"), ("MOD", "Modification"),
    ]

    reference = models.CharField("référence tâche", max_length=50)
    title = models.CharField("intitulé", max_length=200)
    aircraft_type = models.ForeignKey(AircraftType, on_delete=models.PROTECT, verbose_name="type", related_name="tasks")
    source = models.CharField("origine", max_length=4, choices=SOURCES, default="AMP")
    directive = models.ForeignKey(Directive, on_delete=models.PROTECT, null=True, blank=True, related_name="tasks", verbose_name="consigne liée")
    task_type = models.CharField("nature", max_length=4, choices=TASK_TYPES, default="INSP")
    ata = models.CharField("ATA", max_length=10, blank=True)
    part_number = models.ForeignKey(
        PartNumber, on_delete=models.PROTECT, null=True, blank=True, related_name="tasks", verbose_name="P/N composant",
        help_text="Renseigner pour une tâche suivie sur le composant (compteurs du composant)",
    )
    effectivity = models.ManyToManyField(
        Aircraft, blank=True, related_name="specific_tasks", verbose_name="effectivité (aéronefs)",
        help_text="Laisser vide = applicable à tous les aéronefs du type",
    )
    description = models.TextField("description / référence documentaire", blank=True)
    steps = models.TextField("étapes (une par ligne)", blank=True)
    # Intervalles (le premier atteint)
    interval_fh = models.DecimalField("intervalle FH", max_digits=9, decimal_places=2, null=True, blank=True)
    interval_fc = models.PositiveIntegerField("intervalle cycles", null=True, blank=True)
    interval_days = models.PositiveIntegerField("intervalle jours", null=True, blank=True)
    # Première échéance (seuil) depuis neuf / mise en service
    threshold_fh = models.DecimalField("seuil FH", max_digits=9, decimal_places=2, null=True, blank=True)
    threshold_fc = models.PositiveIntegerField("seuil cycles", null=True, blank=True)
    threshold_days = models.PositiveIntegerField("seuil jours", null=True, blank=True)
    # Tolérances autorisées
    tolerance_fh = models.DecimalField("tolérance FH", max_digits=7, decimal_places=2, null=True, blank=True)
    tolerance_fc = models.PositiveIntegerField("tolérance cycles", null=True, blank=True)
    tolerance_days = models.PositiveIntegerField("tolérance jours", null=True, blank=True)
    # Exécution
    estimated_mh = models.DecimalField("charge estimée (h.h)", max_digits=6, decimal_places=2, default=Decimal("1"))
    zone = models.CharField("zone", max_length=40, blank=True)
    access = models.CharField("accès / panneaux", max_length=120, blank=True)
    skill = models.CharField("qualification requise", max_length=3, choices=SKILLS, default="B1")
    requires_independent_inspection = models.BooleanField("contrôle indépendant requis (tâche critique)", default=False)
    amp_revision = models.CharField("révision AMP", max_length=20, blank=True)
    tolerance_reference = models.CharField(
        "référence autorisant la tolérance", max_length=120, blank=True,
        help_text="Obligatoire pour une tolérance sur une tâche issue d'une consigne (AD) : paragraphe de l'AD qui l'autorise.",
    )
    active = models.BooleanField("active", default=True)

    class Meta:
        ordering = ["aircraft_type__code", "ata", "reference"]
        unique_together = [("aircraft_type", "reference")]
        verbose_name = "tâche d'entretien"
        verbose_name_plural = "programme d'entretien (tâches)"

    def __str__(self):
        return f"{self.reference} – {self.title}"

    def get_absolute_url(self):
        return reverse("camo:task_detail", args=[self.pk])

    @property
    def is_repetitive(self):
        return bool(self.interval_fh or self.interval_fc or self.interval_days)

    @property
    def interval_display(self):
        parts = []
        if self.interval_fh:
            parts.append(f"{self.interval_fh.normalize():f} FH")
        if self.interval_fc:
            parts.append(f"{self.interval_fc} cyc")
        if self.interval_days:
            parts.append(_days_label(self.interval_days))
        return " / ".join(parts) or "Unique"

    @property
    def threshold_display(self):
        parts = []
        if self.threshold_fh:
            parts.append(f"{self.threshold_fh.normalize():f} FH")
        if self.threshold_fc:
            parts.append(f"{self.threshold_fc} cyc")
        if self.threshold_days:
            parts.append(_days_label(self.threshold_days))
        return " / ".join(parts)

    @property
    def steps_list(self):
        return [s.strip() for s in self.steps.splitlines() if s.strip()]

    @property
    def has_tolerance(self):
        return bool(self.tolerance_fh or self.tolerance_fc or self.tolerance_days)

    def clean(self):
        if not any([self.interval_fh, self.interval_fc, self.interval_days, self.threshold_fh, self.threshold_fc, self.threshold_days]):
            raise ValidationError("Renseigner au moins un intervalle ou un seuil (FH, cycles ou jours).")
        if self.has_tolerance and self.source in ("ALS", "CMR"):
            raise ValidationError("Aucune tolérance n'est admise sur une limitation de navigabilité (ALS) ou une CMR.")
        if self.has_tolerance and self.source == "AD" and not self.tolerance_reference.strip():
            raise ValidationError({"tolerance_reference": "Une tolérance sur une consigne doit être autorisée par la consigne elle-même : indiquez la référence."})

    def applies_to(self, aircraft):
        if not self.active or aircraft.aircraft_type_id != self.aircraft_type_id:
            return False
        if self.pk and self.effectivity.exists():
            return self.effectivity.filter(pk=aircraft.pk).exists()
        return True


def _days_label(days):
    if days % 365 == 0:
        n = days // 365
        return f"{n} an{'s' if n > 1 else ''}"
    if days % 30 == 0:
        return f"{days // 30} mois"
    return f"{days} j"


class TaskRequiredPart(TrackedModel):
    task = models.ForeignKey(MaintenanceTask, on_delete=models.CASCADE, related_name="required_parts", verbose_name="tâche")
    part_number = models.ForeignKey(PartNumber, on_delete=models.PROTECT, verbose_name="P/N")
    quantity = models.DecimalField("quantité", max_digits=8, decimal_places=2, default=Decimal("1"))

    ahmis_no_delete = False

    class Meta:
        verbose_name = "pièce requise"
        verbose_name_plural = "pièces requises"

    def __str__(self):
        return f"{self.part_number.pn} x{self.quantity}"


class TaskAccomplishment(TrackedModel):
    """Enregistrement de réalisation d'une tâche (base du calcul des prochaines échéances)."""

    SOURCES = [("initial", "Reprise historique"), ("taskcard", "Task card AHMIS"), ("external", "Organisme externe")]

    task = models.ForeignKey(MaintenanceTask, on_delete=models.PROTECT, related_name="accomplishments", verbose_name="tâche")
    aircraft = models.ForeignKey(Aircraft, on_delete=models.PROTECT, related_name="accomplishments", verbose_name="aéronef")
    component = models.ForeignKey(Component, on_delete=models.PROTECT, null=True, blank=True, related_name="accomplishments", verbose_name="composant")
    date = models.DateField("date de réalisation")
    fh = models.DecimalField("FH aéronef", max_digits=10, decimal_places=2)
    fc = models.PositiveIntegerField("cycles aéronef")
    comp_fh = models.DecimalField("TSN composant", max_digits=10, decimal_places=2, null=True, blank=True)
    comp_fc = models.PositiveIntegerField("CSN composant", null=True, blank=True)
    source = models.CharField("origine", max_length=10, choices=SOURCES, default="taskcard")
    task_card = models.ForeignKey("part145.TaskCard", on_delete=models.PROTECT, null=True, blank=True, related_name="accomplishments", verbose_name="task card")
    reference = models.CharField("référence (CRS, WO externe...)", max_length=80, blank=True)
    certified_by = models.CharField("certifié par", max_length=120, blank=True)
    notes = models.TextField("notes", blank=True)
    # Butée théorique au moment de la réalisation (règle de tolérance non cumulative).
    # Mêmes compteurs que comp_fh/comp_fc pour une tâche composant, fh/fc sinon.
    due_fh_at_done = models.DecimalField("butée FH au moment de la réalisation", max_digits=10, decimal_places=2, null=True, blank=True, editable=False)
    due_fc_at_done = models.PositiveIntegerField("butée cycles au moment de la réalisation", null=True, blank=True, editable=False)
    due_date_at_done = models.DateField("butée date au moment de la réalisation", null=True, blank=True, editable=False)
    used_tolerance = models.BooleanField("réalisée en tolérance", default=False, editable=False)
    done_overdue = models.BooleanField("réalisée hors tolérance (échéance dépassée)", default=False, editable=False)

    class Meta:
        ordering = ["-date", "-id"]
        verbose_name = "réalisation de tâche"
        verbose_name_plural = "réalisations de tâches"

    def __str__(self):
        return f"{self.task.reference} sur {self.aircraft.registration} le {self.date:%d/%m/%Y}"

    @property
    def counter_fh(self):
        return self.comp_fh if self.component_id else self.fh

    @property
    def counter_fc(self):
        return self.comp_fc if self.component_id else self.fc

    def clean(self):
        prev = self.previous()
        if prev and self.date < prev.date:
            raise ValidationError(
                f"Une réalisation plus récente existe déjà ({prev.date:%d/%m/%Y}) : les réalisations se saisissent dans l'ordre chronologique."
            )

    def previous(self):
        qs = TaskAccomplishment.objects.filter(task_id=self.task_id)
        qs = qs.filter(component_id=self.component_id) if self.component_id else qs.filter(aircraft_id=self.aircraft_id, component__isnull=True)
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        return qs.order_by("-date", "-id").first()

    def save(self, *args, **kwargs):
        """À la création, mémorise la butée théorique en vigueur, base du calcul de la prochaine échéance.

        - Pas de réalisation précédente et reprise d'historique : aucune butée connue, l'intervalle
          repart de la réalisation.
        - Réalisée après la butée mais dans la tolérance : ``used_tolerance`` ; la prochaine échéance
          repart de la butée théorique (tolérance non cumulative).
        - Réalisée au-delà de la tolérance : ``done_overdue`` (constat à traiter par la qualité) ;
          l'intervalle repart de la réalisation.
        """
        if self._state.adding and self.due_fh_at_done is None and self.due_fc_at_done is None and self.due_date_at_done is None:
            prev = self.previous()
            if prev is not None or self.source != "initial":
                from .services import theoretical_due

                self._apply_theoretical_due(*theoretical_due(self.task, self.aircraft, self.component, prev))
        super().save(*args, **kwargs)

    def _apply_theoretical_due(self, due_fh, due_fc, due_date):
        t = self.task
        checks = [
            (due_fh, self.counter_fh, t.tolerance_fh),
            (due_fc, self.counter_fc, t.tolerance_fc),
            (due_date, self.date, timedelta(days=t.tolerance_days) if t.tolerance_days else None),
        ]
        late, beyond = False, False
        for due, actual, tol in checks:
            if due is None or actual is None or actual <= due:
                continue
            late = True
            if tol is None or actual - due > tol:
                beyond = True
        if beyond:
            self.done_overdue = True
            return  # base = réalisation
        self.used_tolerance = late
        self.due_fh_at_done, self.due_fc_at_done, self.due_date_at_done = due_fh, due_fc, due_date


class AirworthinessReview(TrackedModel):
    TYPES = [("issue", "Émission ARC"), ("extension", "Prorogation ARC")]

    aircraft = models.ForeignKey(Aircraft, on_delete=models.PROTECT, related_name="airworthiness_reviews", verbose_name="aéronef")
    review_type = models.CharField("type", max_length=10, choices=TYPES, default="issue")
    reference = models.CharField("n° ARC", max_length=60)
    review_date = models.DateField("date de la revue")
    expiry_date = models.DateField("valable jusqu'au")
    reviewer = models.CharField("personnel de revue de navigabilité", max_length=120)
    physical_survey = models.BooleanField("visite physique de l'aéronef réalisée", default=True)
    findings = models.TextField("constatations", blank=True)

    class Meta:
        ordering = ["-review_date"]
        verbose_name = "revue de navigabilité (ARC)"
        verbose_name_plural = "revues de navigabilité (ARC)"

    def __str__(self):
        return f"{self.reference} {self.aircraft.registration} → {self.expiry_date:%d/%m/%Y}"

    def clean(self):
        if self.expiry_date and self.review_date and self.expiry_date <= self.review_date:
            raise ValidationError("La date d'expiration doit suivre la date de revue.")
        if self.expiry_date and self.review_date and self.expiry_date > self.review_date + timedelta(days=366):
            raise ValidationError("Un ARC est valable un an au maximum.")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        ac = self.aircraft
        if not ac.arc_expiry or self.expiry_date > ac.arc_expiry:
            ac.arc_expiry = self.expiry_date
            ac.save()


class AmpReview(TrackedModel):
    """Revue périodique du programme d'entretien d'un type (M.A.302(g), AMC : au moins annuelle).

    La revue examine l'efficacité du programme (fiabilité, constatations, défauts répétitifs) et
    l'intégration des nouvelles instructions (révisions MSM/MPD, AD, SB, ICA des modifications).
    Toute modification du programme est approuvée par l'autorité ou par procédure d'approbation indirecte.
    """
    OUTCOMES = [("no_change", "Programme confirmé sans changement"), ("amended", "Programme amendé")]
    APPROVALS = [("indirect", "Approbation indirecte (procédure CAME/CAE)"), ("authority", "Approbation par l'autorité")]

    aircraft_type = models.ForeignKey(AircraftType, on_delete=models.PROTECT, related_name="amp_reviews", verbose_name="type d'aéronef")
    review_date = models.DateField("date de la revue")
    amp_reference = models.CharField("référence du programme (AMP)", max_length=60)
    revision_before = models.CharField("révision examinée", max_length=20)
    reviewer = models.CharField("revue réalisée par", max_length=120)
    reliability_reviewed = models.BooleanField("données de fiabilité / défauts répétitifs analysés", default=False)
    instructions_reviewed = models.BooleanField("nouvelles instructions examinées (MSM/MPD, AD, SB, ICA)", default=False)
    findings = models.TextField("constatations et analyse", blank=True)
    outcome = models.CharField("résultat", max_length=10, choices=OUTCOMES, default="no_change")
    revision_after = models.CharField("nouvelle révision", max_length=20, blank=True)
    changes = models.TextField("changements apportés", blank=True)
    approval_type = models.CharField("mode d'approbation", max_length=10, choices=APPROVALS, blank=True)
    approval_reference = models.CharField("référence d'approbation", max_length=80, blank=True)
    approval_date = models.DateField("date d'approbation", null=True, blank=True)
    next_review_due = models.DateField("prochaine revue avant le", blank=True, null=True,
                                       help_text="Vide = date de revue + périodicité configurée (12 mois par défaut)")

    class Meta:
        ordering = ["-review_date"]
        verbose_name = "revue du programme d'entretien"
        verbose_name_plural = "revues du programme d'entretien"

    def __str__(self):
        return f"Revue AMP {self.aircraft_type.code} du {self.review_date:%d/%m/%Y}"

    def get_absolute_url(self):
        return reverse("camo:amp_review_detail", args=[self.pk])

    def clean(self):
        from django.conf import settings

        errors = {}
        if self.review_date and self.review_date > timezone.localdate():
            errors["review_date"] = "La revue ne peut pas être datée dans le futur."
        if not (self.reliability_reviewed and self.instructions_reviewed):
            errors["instructions_reviewed"] = ("Une revue n'est complète que si la fiabilité et les nouvelles instructions "
                                               "ont été examinées (M.A.302(g)).")
        if self.outcome == "amended":
            if not self.revision_after:
                errors["revision_after"] = "Indiquez la nouvelle révision du programme."
            elif self.revision_after == self.revision_before:
                errors["revision_after"] = "La nouvelle révision doit différer de la révision examinée."
            if not self.changes:
                errors["changes"] = "Décrivez les changements apportés."
            if not self.approval_type or not self.approval_reference:
                errors["approval_reference"] = "Un amendement doit être approuvé (autorité ou approbation indirecte) : mode et référence obligatoires."
        if self.approval_date and self.review_date and self.approval_date < self.review_date:
            errors["approval_date"] = "L'approbation ne peut précéder la revue."
        months = settings.AHMIS.get("AMP_REVIEW_MONTHS", 12)
        if self.next_review_due and self.review_date and self.next_review_due > _add_months(self.review_date, months):
            errors["next_review_due"] = f"La prochaine revue doit intervenir au plus tard {months} mois après celle-ci."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        from django.conf import settings

        if not self.next_review_due and self.review_date:
            self.next_review_due = _add_months(self.review_date, settings.AHMIS.get("AMP_REVIEW_MONTHS", 12))
        super().save(*args, **kwargs)
        if self.outcome == "amended" and self.revision_after:
            # Trace la révision en vigueur sur les tâches actives du type
            for t in MaintenanceTask.objects.filter(aircraft_type=self.aircraft_type, active=True).exclude(amp_revision=self.revision_after):
                t.amp_revision = self.revision_after
                t.save()


def amp_review_status(aircraft_type, on_date=None):
    """État de la revue du programme d'un type : dict(last, due, status) avec status none/overdue/due_soon/ok."""
    from django.conf import settings

    on_date = on_date or timezone.localdate()
    last = aircraft_type.amp_reviews.order_by("-review_date", "-pk").first()
    if last is None:
        return {"last": None, "due": None, "status": "none"}
    due = last.next_review_due
    if due < on_date:
        status = "overdue"
    elif (due - on_date).days <= settings.AHMIS["ALERT_DAYS"]:
        status = "due_soon"
    else:
        status = "ok"
    return {"last": last, "due": due, "status": status}


class ModificationRepair(TrackedModel):
    """Registre des modifications et réparations (M.A.305 : statut des modifications et réparations).

    Une modification ou réparation n'est conforme que si elle repose sur des données approuvées
    (Part-21 : STC, approbation DOA, SB constructeur, SRM…) et que ses instructions de maintien de la
    navigabilité (ICA) sont intégrées au programme d'entretien.
    """

    KINDS = [("mod", "Modification"), ("repair", "Réparation")]
    CLASSES = [("major", "Majeure"), ("minor", "Mineure"), ("standard", "Changement / réparation standard (CS-STAN)")]
    BASES = [
        ("stc", "STC (certificat de type supplémentaire)"),
        ("doa", "Approbation DOA / Part-21J"),
        ("easa", "Approbation EASA directe"),
        ("oem_sb", "Bulletin service constructeur"),
        ("srm", "Manuel de réparations structurales (SRM)"),
        ("cs_stan", "CS-STAN"),
        ("other", "Autre donnée approuvée"),
    ]
    STATUSES = [("planned", "Prévue"), ("embodied", "Appliquée"), ("removed", "Déposée / annulée")]
    # Dossier Part-21 : données de conception approuvées obtenues auprès du titulaire (DOA, TC/STC) ou de l'EASA.
    PART21_BASES = ("stc", "doa", "easa")
    PART21_STATUSES = [
        ("not_required", "Sans objet (données déjà approuvées)"),
        ("to_request", "Demande à émettre"),
        ("requested", "Demande transmise"),
        ("approved", "Données de conception approuvées reçues"),
        ("refused", "Refusée par le titulaire / l'EASA"),
    ]

    number = models.CharField("n° interne", max_length=20, unique=True, editable=False)
    aircraft = models.ForeignKey(Aircraft, on_delete=models.PROTECT, related_name="modifications", verbose_name="aéronef")
    component = models.ForeignKey(Component, on_delete=models.PROTECT, null=True, blank=True, related_name="modifications",
                                  verbose_name="composant concerné", help_text="Vide = cellule")
    kind = models.CharField("nature", max_length=6, choices=KINDS, default="mod")
    classification = models.CharField("classification", max_length=8, choices=CLASSES, default="minor")
    title = models.CharField("intitulé", max_length=200)
    description = models.TextField("description", blank=True)
    approval_basis = models.CharField("base d'approbation", max_length=8, choices=BASES)
    approval_reference = models.CharField("référence d'approbation", max_length=120,
                                          help_text="N° STC, n° d'approbation DOA, SB, chapitre SRM…")
    directive = models.ForeignKey(Directive, on_delete=models.PROTECT, null=True, blank=True, related_name="modifications", verbose_name="SB / AD liée")
    ata = models.CharField("ATA", max_length=10, blank=True)
    status = models.CharField("statut", max_length=8, choices=STATUSES, default="planned")
    embodied_on = models.DateField("appliquée le", null=True, blank=True)
    fh_at_embodiment = models.DecimalField("FH aéronef à l'application", max_digits=10, decimal_places=2, null=True, blank=True)
    fc_at_embodiment = models.PositiveIntegerField("cycles aéronef à l'application", null=True, blank=True)
    task_card = models.ForeignKey("part145.TaskCard", on_delete=models.PROTECT, null=True, blank=True, related_name="modifications", verbose_name="task card")
    ica_reference = models.CharField("instructions de maintien de navigabilité (ICA)", max_length=200, blank=True)
    ica_none = models.BooleanField("pas d'ICA associées", default=False)
    ica_in_amp = models.BooleanField("ICA intégrées au programme d'entretien", default=False)
    affects_mass_balance = models.BooleanField("modifie la masse et le centrage", default=False)
    affects_flight_manual = models.BooleanField("modifie le manuel de vol (supplément)", default=False)
    follow_up_done = models.BooleanField("actions de suivi réalisées (pesée, supplément manuel de vol)", default=False)
    removed_on = models.DateField("déposée le", null=True, blank=True)
    removal_reason = models.CharField("motif de dépose / annulation", max_length=200, blank=True)
    # Part-21
    design_holder = models.CharField("titulaire de la conception (DOA, TC / STC)", max_length=150, blank=True)
    design_approval_number = models.CharField("n° d'agrément du titulaire", max_length=60, blank=True, help_text="ex. EASA.21J.123")
    part21_status = models.CharField("dossier Part-21", max_length=12, choices=PART21_STATUSES, default="not_required")
    part21_requested_on = models.DateField("demande transmise le", null=True, blank=True)
    part21_approved_on = models.DateField("approbation obtenue le", null=True, blank=True)
    part21_reference = models.CharField("référence de l'approbation de conception", max_length=120, blank=True,
                                        help_text="n° d'approbation EASA, de STC ou de la fiche d'approbation DOA")

    class Meta:
        ordering = ["aircraft__registration", "-embodied_on", "-number"]
        verbose_name = "modification / réparation"
        verbose_name_plural = "registre des modifications et réparations"

    def __str__(self):
        return f"{self.number} {self.aircraft.registration} – {self.title}"

    def get_absolute_url(self):
        return reverse("camo:mod_detail", args=[self.pk])

    def save(self, *args, **kwargs):
        if not self.number:
            from apps.core.models import Sequence

            self.number = Sequence.next("MR" if self.kind == "repair" else "MOD")
        super().save(*args, **kwargs)

    def clean(self):
        errors = {}
        if self.classification == "major" and self.approval_basis in ("srm", "cs_stan", "other"):
            errors["approval_basis"] = "Une modification ou réparation majeure exige une approbation EASA, un STC ou une approbation DOA."
        if self.classification == "standard" and self.approval_basis != "cs_stan":
            errors["approval_basis"] = "Un changement standard doit se référer à CS-STAN."
        if self.status == "embodied":
            if not self.embodied_on:
                errors["embodied_on"] = "Date d'application obligatoire."
            if not (self.ica_none or self.ica_reference.strip()):
                errors["ica_reference"] = "Indiquez les ICA, ou cochez « pas d'ICA associées »."
        if self.status == "removed" and not self.removal_reason.strip():
            errors["removal_reason"] = "Motif obligatoire."
        if self.needs_part21:
            if self.part21_status == "not_required":
                errors["part21_status"] = "Modification majeure ou base STC / DOA / EASA : un dossier Part-21 est requis."
            if self.part21_status in ("requested", "approved", "refused") and not self.design_holder.strip():
                errors["design_holder"] = "Indiquez le titulaire de la conception."
            if self.part21_status in ("requested", "approved") and not self.part21_requested_on:
                errors["part21_requested_on"] = "Indiquez la date de la demande."
            if self.part21_status == "approved":
                if not self.part21_approved_on:
                    errors["part21_approved_on"] = "Indiquez la date d'approbation."
                if not self.part21_reference.strip():
                    errors["part21_reference"] = "Indiquez la référence de l'approbation de conception."
                if self.part21_requested_on and self.part21_approved_on and self.part21_approved_on < self.part21_requested_on:
                    errors["part21_approved_on"] = "L'approbation ne peut précéder la demande."
            if self.status == "embodied":
                if self.part21_status != "approved":
                    errors["status"] = "Application impossible : les données de conception ne sont pas encore approuvées (Part-21)."
                elif self.part21_approved_on and self.embodied_on and self.embodied_on < self.part21_approved_on:
                    errors["embodied_on"] = "Application antérieure à l'approbation de conception."
        if self.component_id and self.component.aircraft_id not in (None, self.aircraft_id) and self.status == "planned":
            errors["component"] = "Ce composant est installé sur un autre aéronef."
        if errors:
            raise ValidationError(errors)

    @property
    def needs_part21(self):
        """Modification majeure, ou fondée sur un STC, une approbation DOA ou une approbation EASA directe."""
        return self.classification == "major" or self.approval_basis in self.PART21_BASES

    @property
    def compliance_issues(self):
        """Points à traiter par la CAMO (affichés sur la fiche aéronef et dans les échéances)."""
        issues = []
        if self.status == "planned" and self.needs_part21 and self.part21_status in ("to_request", "not_required"):
            issues.append("dossier Part-21 : demande d'approbation de conception à émettre")
        if self.task_card_id and self.status == "embodied" and self.task_card.status not in ("performed", "closed"):
            issues.append("task card liée non encore clôturée")
        if self.status == "embodied":
            if not self.ica_none and not self.ica_in_amp:
                issues.append("ICA non encore intégrées au programme d'entretien")
            if self.affects_mass_balance and not self.follow_up_done:
                issues.append("fiche de pesée / centrage à mettre à jour")
            if self.affects_flight_manual and not self.follow_up_done:
                issues.append("supplément au manuel de vol à insérer")
        return issues


class TransferRecord(TrackedModel):
    """Transfert des enregistrements de navigabilité d'un aéronef (M.A.307, CAMO.A.315(c)).

    Sortant : AHMIS génère l'archive complète du dossier (voir ``apps.camo.dossier``) et la conserve avec son
    empreinte SHA-256 ; l'accusé de réception du nouvel organisme est enregistré ensuite.
    Entrant : l'archive reçue est jointe et son intégrité contrôlée (manifeste AHMIS) ; la reprise des données
    se fait ensuite par les écrans de saisie ou d'import.
    """
    DIRECTIONS = [("out", "Transfert sortant (nouvel organisme / propriétaire)"), ("in", "Transfert entrant (dossier reçu)"),
                  ("copy", "Copie / archivage (autorité, propriétaire, audit)")]

    number = models.CharField("n° de transfert", max_length=20, unique=True, editable=False)
    aircraft = models.ForeignKey(Aircraft, on_delete=models.PROTECT, related_name="transfers", verbose_name="aéronef")
    direction = models.CharField("sens", max_length=4, choices=DIRECTIONS, default="out")
    transfer_date = models.DateField("date du transfert", default=timezone.localdate)
    counterparty = models.CharField("organisme / destinataire", max_length=150,
                                    help_text="CAMO, CAO ou propriétaire qui reçoit (ou qui a envoyé) le dossier")
    counterparty_approval = models.CharField("agrément de l'organisme", max_length=60, blank=True, help_text="ex. FR.CAMO.0123")
    reason = models.TextField("motif", blank=True)
    archive = models.FileField("archive du dossier", upload_to="transferts/%Y/", blank=True)
    archive_sha256 = models.CharField("empreinte SHA-256 de l'archive", max_length=64, blank=True, editable=False)
    archive_size = models.PositiveIntegerField("taille (octets)", null=True, blank=True, editable=False)
    manifest = models.JSONField("manifeste", null=True, blank=True, editable=False)
    verification = models.TextField("contrôle d'intégrité", blank=True, editable=False)
    acknowledged_on = models.DateField("réception confirmée le", null=True, blank=True)
    acknowledged_by = models.CharField("réception confirmée par", max_length=120, blank=True)
    notes = models.TextField("notes", blank=True)

    class Meta:
        ordering = ["-transfer_date", "-pk"]
        verbose_name = "transfert de dossier"
        verbose_name_plural = "transferts de dossiers"

    def __str__(self):
        return f"{self.number} {self.aircraft.registration} → {self.counterparty}"

    def get_absolute_url(self):
        return reverse("camo:transfer_detail", args=[self.pk])

    @property
    def integrity_ok(self):
        return bool(self.archive_sha256) and not self.verification.startswith("ANOMALIE")

    def clean(self):
        errors = {}
        if self.transfer_date and self.transfer_date > timezone.localdate():
            errors["transfer_date"] = "La date de transfert ne peut être dans le futur."
        if self.acknowledged_on and self.direction == "in":
            errors["acknowledged_on"] = "L'accusé de réception concerne un transfert sortant."
        if self.acknowledged_on and not self.acknowledged_by:
            errors["acknowledged_by"] = "Indiquez qui a confirmé la réception."
        if self.acknowledged_on and self.transfer_date and self.acknowledged_on < self.transfer_date:
            errors["acknowledged_on"] = "La réception ne peut précéder l'envoi."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if not self.number:
            from apps.core.models import Sequence

            self.number = Sequence.next("TR")
        super().save(*args, **kwargs)
