from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone

from apps.camo.models import SKILLS, MaintenanceTask
from apps.core.models import Sequence, TrackedModel
from apps.fleet.models import Aircraft, AircraftType, Component
from django.utils.translation import gettext, gettext_lazy


class Staff(TrackedModel):
    ROLES = [
        ("mechanic", gettext_lazy("Mécanicien")),
        ("certifying", gettext_lazy("Personnel certifiant")),
        ("inspector", gettext_lazy("Contrôleur / inspecteur")),
        ("planner", gettext_lazy("Planificateur")),
        ("camo", gettext_lazy("Ingénieur navigabilité (CAMO)")),
        ("storekeeper", gettext_lazy("Magasinier")),
        ("manager", gettext_lazy("Responsable")),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="staff", verbose_name=gettext_lazy("compte utilisateur"))
    employee_number = models.CharField(gettext_lazy("matricule"), max_length=20, unique=True)
    first_name = models.CharField(gettext_lazy("prénom"), max_length=60)
    last_name = models.CharField(gettext_lazy("nom"), max_length=60)
    role = models.CharField(gettext_lazy("fonction"), max_length=12, choices=ROLES, default="mechanic")
    stamp = models.CharField(gettext_lazy("tampon / visa"), max_length=10, blank=True)
    licence_number = models.CharField(gettext_lazy("n° licence Part-66"), max_length=40, blank=True)
    licence_categories = models.CharField(gettext_lazy("catégories de licence"), max_length=60, blank=True, help_text=gettext_lazy("ex. B1.3, B2"))
    licence_expiry = models.DateField(gettext_lazy("validité de la licence"), null=True, blank=True)
    active = models.BooleanField(gettext_lazy("actif"), default=True)
    left_on = models.DateField(gettext_lazy("départ de l'organisme le"), null=True, blank=True,
                               help_text=gettext_lazy("Le dossier est conservé 3 ans après le départ (145.A.35(j))"))

    class Meta:
        ordering = ["last_name", "first_name"]
        verbose_name = "personnel"
        verbose_name_plural = "personnel"

    def clean(self):
        if self.left_on and self.active:
            raise ValidationError({"left_on": gettext("Une personne partie de l'organisme doit être marquée inactive.")})
        if self.left_on and self.left_on > timezone.localdate():
            raise ValidationError({"left_on": gettext("La date de départ ne peut être dans le futur.")})

    def __str__(self):
        return f"{self.full_name} ({self.employee_number})"

    def get_absolute_url(self):
        return reverse("part145:staff_detail", args=[self.pk])

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name.upper()}"

    @property
    def licence_valid(self):
        return bool(self.licence_number) and (self.licence_expiry is None or self.licence_expiry >= timezone.localdate())

    @property
    def licence_summary(self):
        if not self.licence_number:
            return f"Matricule {self.employee_number}"
        return gettext("Licence {licence_number} ({licence_categories})").format(licence_number=self.licence_number, licence_categories=self.licence_categories)

    def valid_authorizations(self, aircraft_type=None, on_date=None):
        on_date = on_date or timezone.localdate()
        qs = self.authorizations.filter(valid_from__lte=on_date, valid_until__gte=on_date, suspended=False)
        if aircraft_type is not None:
            qs = qs.filter(aircraft_type=aircraft_type)
        return qs

    # ------------------------------------------------------------------ aptitude à signer
    def experience_months(self, on_date=None, window_months=None):
        """Mois calendaires d'expérience pratique sur la fenêtre glissante (145.A.35 : 6 mois sur 2 ans).

        Sources : task cards exécutées ou contrôlées dans AHMIS, et expériences déclarées (autre organisme,
        période antérieure à AHMIS) dans « ExperienceRecord ».
        """
        on_date = on_date or timezone.localdate()
        window = window_months or settings.AHMIS["RECENCY_WINDOW_MONTHS"]
        start = _months_back(on_date, window)
        months = set()
        for field in ("performed_at", "inspected_at"):
            filt = {f"{field}__date__gte": start, f"{field}__date__lte": on_date}
            who = "performed_by" if field == "performed_at" else "inspected_by"
            for dt in TaskCard.objects.filter(**{who: self}, **filt).values_list(field, flat=True):
                d = timezone.localtime(dt).date()
                months.add((d.year, d.month))
        for rec in self.experience_records.filter(start__lte=on_date, end__gte=start):
            d = max(rec.start, start).replace(day=1)
            last = min(rec.end, on_date)
            while d <= last:
                months.add((d.year, d.month))
                d = _months_back(d, -1)
        return months

    def missing_trainings(self, certifying=False, on_date=None):
        """Catégories de formation obligatoires absentes ou expirées."""
        on_date = on_date or timezone.localdate()
        required = list(settings.AHMIS["TRAINING_REQUIRED_ALL"])
        if certifying:
            required += [c for c in settings.AHMIS["TRAINING_REQUIRED_CERTIFYING"] if c not in required]
        labels = dict(Qualification.CATEGORIES)
        missing = []
        for cat in required:
            ok = self.qualifications.filter(category=cat, obtained__lte=on_date).filter(
                models.Q(expiry__isnull=True) | models.Q(expiry__gte=on_date)).exists()
            if not ok:
                missing.append(str(labels.get(cat, cat)))
        return missing

    def signing_blockers(self, aircraft_type, certifying=False, categories=("B1", "B2", "B3", "C"), on_date=None):
        """Raisons réglementaires empêchant cette personne de signer (liste vide = signature possible)."""
        on_date = on_date or timezone.localdate()
        problems = []
        if not self.active:
            problems.append(gettext("{full_name} : fiche personnel inactive.").format(full_name=self.full_name))
            return problems
        auths = self.valid_authorizations(aircraft_type, on_date)
        if certifying:
            if not self.licence_valid:
                problems.append(gettext("{full_name} : licence Part-66 absente ou expirée.").format(full_name=self.full_name))
            if not auths.filter(certifying=True, category__in=categories).exists():
                problems.append(gettext("{full_name} : pas d'autorisation certifiante valide ({categories}) sur le type {code}.").format(full_name=self.full_name, categories='/'.join(categories), code=aircraft_type.code))
            if settings.AHMIS["RECENCY_ENFORCE"]:
                n = len(self.experience_months(on_date))
                need = settings.AHMIS["RECENCY_MONTHS"]
                if n < need:
                    problems.append(f"{self.full_name} : expérience récente insuffisante ({n} mois sur les "
                                    f"{settings.AHMIS['RECENCY_WINDOW_MONTHS']} derniers, {need} requis – 145.A.35).")
        elif not auths.exists():
            problems.append(gettext("{full_name} n'a pas d'autorisation valide sur le type {code}.").format(full_name=self.full_name, code=aircraft_type.code))
        missing = self.missing_trainings(certifying, on_date)
        if missing:
            problems.append(gettext("{full_name} : formation obligatoire absente ou expirée : {missing}.").format(full_name=self.full_name, missing=', '.join(missing)))
        return problems

    def can_perform(self, aircraft_type):
        return not self.signing_blockers(aircraft_type)

    def can_certify(self, aircraft_type, categories=("B1", "B2", "B3", "C")):
        return not self.signing_blockers(aircraft_type, certifying=True, categories=categories)

    def missing_qualifications(self):
        today = timezone.localdate()
        return self.qualifications.filter(expiry__lt=today)


def _months_back(d, months):
    """Date décalée de ``months`` mois en arrière (négatif = en avant), au 1er du mois."""
    y, m = d.year, d.month - months
    while m < 1:
        m += 12
        y -= 1
    while m > 12:
        m -= 12
        y += 1
    return d.replace(year=y, month=m, day=1)


class ExperienceRecord(TrackedModel):
    """Expérience pratique déclarée hors AHMIS (autre organisme, période antérieure) pour le calcul de récence."""

    staff = models.ForeignKey(Staff, on_delete=models.PROTECT, related_name="experience_records", verbose_name=gettext_lazy("personnel"))
    aircraft_type = models.ForeignKey(AircraftType, on_delete=models.PROTECT, null=True, blank=True, verbose_name=gettext_lazy("type"))
    start = models.DateField(gettext_lazy("du"))
    end = models.DateField(gettext_lazy("au"))
    organisation = models.CharField(gettext_lazy("organisme"), max_length=120)
    description = models.CharField(gettext_lazy("travaux réalisés"), max_length=200)
    evidence = models.CharField(gettext_lazy("justificatif"), max_length=120, blank=True, help_text=gettext_lazy("Attestation, carnet de travaux…"))

    class Meta:
        ordering = ["staff", "-end"]
        verbose_name = gettext_lazy("expérience déclarée")
        verbose_name_plural = gettext_lazy("expériences déclarées")

    def __str__(self):
        return f"{self.staff.full_name} {self.start:%m/%Y}–{self.end:%m/%Y} {self.organisation}"

    def clean(self):
        if self.end and self.start and self.end < self.start:
            raise ValidationError(gettext("Période incohérente."))
        if self.end and self.end > timezone.localdate():
            raise ValidationError(gettext("Une expérience ne peut pas être déclarée dans le futur."))


class Authorization(TrackedModel):
    """Autorisation délivrée par l'organisme Part-145 (portée type / catégorie)."""

    CATEGORIES = SKILLS + [("MECH", gettext_lazy("Mécanicien non certifiant"))]

    staff = models.ForeignKey(Staff, on_delete=models.PROTECT, related_name="authorizations", verbose_name=gettext_lazy("personnel"))
    number = models.CharField(gettext_lazy("n° d'autorisation"), max_length=30)
    aircraft_type = models.ForeignKey(AircraftType, on_delete=models.PROTECT, verbose_name=gettext_lazy("type"), related_name="authorizations")
    category = models.CharField(gettext_lazy("catégorie"), max_length=4, choices=CATEGORIES)
    certifying = models.BooleanField(gettext_lazy("certifiante (CRS)"), default=False)
    scope = models.CharField(gettext_lazy("portée / limitations"), max_length=200, blank=True)
    valid_from = models.DateField(gettext_lazy("valide du"))
    valid_until = models.DateField(gettext_lazy("valide jusqu'au"))
    suspended = models.BooleanField(gettext_lazy("suspendue"), default=False)

    class Meta:
        ordering = ["staff__last_name", "aircraft_type__code"]
        verbose_name = "autorisation"
        verbose_name_plural = "autorisations"

    def __str__(self):
        return f"{self.number} {self.aircraft_type.code} {self.category}{' certifiant' if self.certifying else ''}"

    @property
    def is_valid(self):
        today = timezone.localdate()
        return not self.suspended and self.valid_from <= today <= self.valid_until

    def clean(self):
        if self.certifying and self.category == "MECH":
            raise ValidationError(gettext("Une autorisation « mécanicien non certifiant » ne peut pas être certifiante."))
        if self.valid_until and self.valid_from and self.valid_until < self.valid_from:
            raise ValidationError(gettext("Dates de validité incohérentes."))


class Qualification(TrackedModel):
    """Formations à validité limitée : facteurs humains, formation continue, EWIS, CDCCL..."""

    CATEGORIES = [
        ("human_factors", gettext_lazy("Facteurs humains")),
        ("continuation", gettext_lazy("Formation continue (145.A.35)")),
        ("ewis", "EWIS"),
        ("fuel_tank", gettext_lazy("Sécurité réservoirs / CDCCL")),
        ("type", gettext_lazy("Formation type / différences")),
        ("safety", gettext_lazy("Sûreté / zones réservées")),
        ("other", gettext_lazy("Autre")),
    ]

    staff = models.ForeignKey(Staff, on_delete=models.PROTECT, related_name="qualifications", verbose_name=gettext_lazy("personnel"))
    category = models.CharField(gettext_lazy("catégorie"), max_length=15, choices=CATEGORIES, default="other")
    name = models.CharField(gettext_lazy("formation"), max_length=100)
    obtained = models.DateField(gettext_lazy("obtenue le"))
    expiry = models.DateField(gettext_lazy("expire le"), null=True, blank=True)

    class Meta:
        ordering = ["staff", "name"]
        verbose_name = gettext_lazy("formation / qualification")
        verbose_name_plural = gettext_lazy("formations / qualifications")

    def __str__(self):
        return f"{self.name} – {self.staff.full_name}"

    @property
    def is_valid(self):
        return self.expiry is None or self.expiry >= timezone.localdate()


class WorkPackage(TrackedModel):
    STATUSES = [
        ("draft", gettext_lazy("Brouillon")),
        ("planned", gettext_lazy("Planifié")),
        ("in_progress", gettext_lazy("En cours")),
        ("released", gettext_lazy("Remis en service (CRS signé)")),
        ("cancelled", gettext_lazy("Annulé")),
    ]
    CHECK_TYPES = [
        ("line", gettext_lazy("Entretien en ligne")), ("daily", gettext_lazy("Visite journalière / avant vol")),
        ("periodic", gettext_lazy("Visite périodique")), ("major", gettext_lazy("Grande visite")), ("unscheduled", gettext_lazy("Non programmé / dépannage")),
        ("component", gettext_lazy("Changement de composant")),
    ]

    number = models.CharField(gettext_lazy("n° WP"), max_length=20, unique=True, editable=False)
    aircraft = models.ForeignKey(Aircraft, on_delete=models.PROTECT, related_name="work_packages", verbose_name=gettext_lazy("aéronef"))
    title = models.CharField(gettext_lazy("intitulé"), max_length=150)
    check_type = models.CharField(gettext_lazy("type de visite"), max_length=12, choices=CHECK_TYPES, default="periodic")
    station = models.CharField(gettext_lazy("station / hangar"), max_length=60, blank=True)
    planned_start = models.DateField(gettext_lazy("début prévu"))
    planned_end = models.DateField(gettext_lazy("fin prévue"))
    status = models.CharField(gettext_lazy("statut"), max_length=12, choices=STATUSES, default="draft")
    ordered_by = models.CharField(gettext_lazy("commandé par (CAMO / client)"), max_length=120, blank=True)
    customer_order = models.CharField(gettext_lazy("n° de commande / contrat"), max_length=60, blank=True)
    fh_at_check = models.DecimalField(gettext_lazy("FH aéronef à la visite"), max_digits=10, decimal_places=2, null=True, blank=True)
    fc_at_check = models.PositiveIntegerField(gettext_lazy("cycles aéronef à la visite"), null=True, blank=True)
    crs_by = models.ForeignKey(Staff, on_delete=models.PROTECT, null=True, blank=True, related_name="crs_issued", verbose_name=gettext_lazy("CRS signé par"))
    crs_date = models.DateTimeField(gettext_lazy("date du CRS"), null=True, blank=True)
    crs_statement = models.TextField(gettext_lazy("déclaration CRS"), blank=True)
    notes = models.TextField(gettext_lazy("notes"), blank=True)

    class Meta:
        ordering = ["-planned_start", "-number"]
        verbose_name = gettext_lazy("work package")
        verbose_name_plural = gettext_lazy("work packages")
        permissions = [("sign_crs", gettext_lazy("Signer le certificat de remise en service"))]

    def __str__(self):
        return f"{self.number} {self.aircraft.registration} – {self.title}"

    def get_absolute_url(self):
        return reverse("part145:wp_detail", args=[self.pk])

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = Sequence.next("WP")
        super().save(*args, **kwargs)

    def clean(self):
        if self.planned_end and self.planned_start and self.planned_end < self.planned_start:
            raise ValidationError(gettext("La fin prévue précède le début."))

    @property
    def is_locked(self):
        return self.status in ("released", "cancelled")

    @property
    def total_estimated_mh(self):
        return sum((c.estimated_mh or 0) for c in self.task_cards.exclude(status="cancelled"))

    @property
    def total_actual_mh(self):
        return sum((c.actual_mh or 0) for c in self.task_cards.exclude(status="cancelled"))

    @property
    def progress(self):
        cards = self.task_cards.exclude(status="cancelled")
        n = cards.count()
        if not n:
            return 0
        return round(100 * cards.filter(status__in=["closed", "deferred"]).count() / n)

    def crs_blockers(self):
        problems = []
        if self.status in ("released", "cancelled"):
            problems.append(gettext("Work package déjà remis en service ou annulé."))
        cards = self.task_cards.all()
        if not cards.exists():
            problems.append(gettext("Aucune task card dans le work package."))
        for c in cards.exclude(status__in=["closed", "deferred", "cancelled"]):
            problems.append(gettext("Task card {number} non clôturée ({get_status_display}).").format(number=c.number, get_status_display=c.get_status_display()))
        for c in cards.filter(status="deferred"):
            if not c.deferral_reason:
                problems.append(gettext("Task card {number} reportée sans justification.").format(number=c.number))
        from apps.logistics.models import Tool

        for t in Tool.objects.filter(checked_out_to__work_package=self):
            problems.append(gettext("Outillage {reference} non restitué (task card {number}).").format(reference=t.reference, number=t.checked_out_to.number))
        for comp in Component.objects.filter(reserved_for__work_package=self, status="reserved"):
            problems.append(gettext("Pièce {comp} réservée non posée ni retournée au magasin.").format(comp=comp))
        for d in self.aircraft.defects.filter(status="deferred"):
            if d.deferral_expired:
                problems.append(gettext("Défaut {number} : limite de report dépassée, rectification ou prorogation requise "
                                        "avant remise en service.").format(number=d.number))
        return problems


class TaskCard(TrackedModel):
    STATUSES = [
        ("open", gettext_lazy("Ouverte")),
        ("in_progress", gettext_lazy("En cours")),
        ("performed", gettext_lazy("Exécutée – attente contrôle")),
        ("closed", gettext_lazy("Clôturée")),
        ("deferred", gettext_lazy("Reportée")),
        ("cancelled", gettext_lazy("Annulée")),
    ]
    ORIGINS = [("task", gettext_lazy("Programme d'entretien")), ("defect", gettext_lazy("Défaut")), ("finding", gettext_lazy("Constatation")), ("adhoc", gettext_lazy("Travail additionnel"))]

    number = models.CharField(gettext_lazy("n° task card"), max_length=20, unique=True, editable=False)
    work_package = models.ForeignKey(WorkPackage, on_delete=models.PROTECT, related_name="task_cards", verbose_name=gettext_lazy("work package"))
    origin = models.CharField(gettext_lazy("origine"), max_length=8, choices=ORIGINS, default="task")
    task = models.ForeignKey(MaintenanceTask, on_delete=models.PROTECT, null=True, blank=True, related_name="task_cards", verbose_name=gettext_lazy("tâche AMP"))
    component = models.ForeignKey(Component, on_delete=models.PROTECT, null=True, blank=True, related_name="task_cards", verbose_name=gettext_lazy("composant concerné"))
    defect = models.ForeignKey("Defect", on_delete=models.PROTECT, null=True, blank=True, related_name="task_cards", verbose_name=gettext_lazy("défaut"))
    parent = models.ForeignKey("self", on_delete=models.PROTECT, null=True, blank=True, related_name="findings", verbose_name=gettext_lazy("task card d'origine"))
    title = models.CharField(gettext_lazy("intitulé"), max_length=200)
    ata = models.CharField(gettext_lazy("ATA"), max_length=10, blank=True)
    zone = models.CharField(gettext_lazy("zone"), max_length=40, blank=True)
    access = models.CharField(gettext_lazy("accès"), max_length=120, blank=True)
    instructions = models.TextField(gettext_lazy("instructions / références"), blank=True)
    skill = models.CharField(gettext_lazy("qualification requise"), max_length=3, choices=SKILLS, default="B1")
    requires_independent_inspection = models.BooleanField(gettext_lazy("contrôle indépendant requis"), default=False)
    estimated_mh = models.DecimalField(gettext_lazy("charge estimée (h.h)"), max_digits=6, decimal_places=2, default=Decimal("1"))
    actual_mh = models.DecimalField(gettext_lazy("temps passé (h.h)"), max_digits=6, decimal_places=2, null=True, blank=True)
    status = models.CharField(gettext_lazy("statut"), max_length=12, choices=STATUSES, default="open")
    work_done = models.TextField(gettext_lazy("compte rendu des travaux"), blank=True)
    performed_by = models.ForeignKey(Staff, on_delete=models.PROTECT, null=True, blank=True, related_name="cards_performed", verbose_name=gettext_lazy("exécuté par"))
    performed_at = models.DateTimeField(gettext_lazy("exécuté le"), null=True, blank=True)
    inspected_by = models.ForeignKey(Staff, on_delete=models.PROTECT, null=True, blank=True, related_name="cards_inspected", verbose_name=gettext_lazy("contrôlé par"))
    inspected_at = models.DateTimeField(gettext_lazy("contrôlé le"), null=True, blank=True)
    deferral_reason = models.CharField(gettext_lazy("motif de report"), max_length=200, blank=True)
    sequence = models.PositiveIntegerField(gettext_lazy("ordre"), default=10)

    class Meta:
        ordering = ["work_package", "sequence", "number"]
        verbose_name = gettext_lazy("task card")
        verbose_name_plural = gettext_lazy("task cards")
        permissions = [("execute_taskcard", gettext_lazy("Exécuter une task card")), ("certify_taskcard", gettext_lazy("Contrôler une task card (inspection indépendante)"))]

    def __str__(self):
        return f"{self.number} – {self.title}"

    def get_absolute_url(self):
        return reverse("part145:card_detail", args=[self.pk])

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = Sequence.next("TC", width=5)
        super().save(*args, **kwargs)

    @property
    def aircraft(self):
        return self.work_package.aircraft

    @property
    def steps_progress(self):
        steps = list(self.steps.all())
        if not steps:
            return "—"
        return f"{sum(1 for s in steps if s.done_at)}/{len(steps)}"

    @property
    def is_editable(self):
        return self.status in ("open", "in_progress") and not self.work_package.is_locked

    @classmethod
    def from_task(cls, wp, task, component=None):
        card = cls.objects.create(
            work_package=wp, origin="task", task=task, component=component,
            title=task.title + (f" – {component.part_number.pn} S/N {component.serial_number}" if component else ""),
            ata=task.ata, zone=task.zone, access=task.access,
            instructions=gettext("Réf. {reference} (AMP {or_})\n{description}").format(reference=task.reference, or_=task.amp_revision or '-', description=task.description).strip(),
            skill=task.skill, requires_independent_inspection=task.requires_independent_inspection,
            estimated_mh=task.estimated_mh,
        )
        for i, text in enumerate(task.steps_list, start=1):
            TaskCardStep.objects.create(card=card, order=i, text=text)
        return card


class TaskCardStep(TrackedModel):
    card = models.ForeignKey(TaskCard, on_delete=models.PROTECT, related_name="steps", verbose_name=gettext_lazy("task card"))
    order = models.PositiveIntegerField(gettext_lazy("n°"))
    text = models.TextField(gettext_lazy("étape"))
    measured_value = models.CharField(gettext_lazy("valeur relevée"), max_length=100, blank=True)
    done_by = models.ForeignKey(Staff, on_delete=models.PROTECT, null=True, blank=True, related_name="+", verbose_name=gettext_lazy("réalisé par"))
    done_at = models.DateTimeField(gettext_lazy("réalisé le"), null=True, blank=True)
    not_applicable = models.BooleanField(gettext_lazy("N/A"), default=False)

    class Meta:
        ordering = ["card", "order"]
        verbose_name = gettext_lazy("étape")
        verbose_name_plural = gettext_lazy("étapes")

    def __str__(self):
        return f"{self.card.number} étape {self.order}"


class Defect(TrackedModel):
    STATUSES = [("open", gettext_lazy("Ouvert")), ("deferred", gettext_lazy("Reporté (MEL/CDL)")), ("rectified", gettext_lazy("Rectifié")), ("cancelled", gettext_lazy("Annulé"))]
    SOURCES = [("techlog", gettext_lazy("Compte-rendu équipage (techlog)")), ("finding", gettext_lazy("Constat en maintenance")), ("inspection", gettext_lazy("Inspection")), ("other", gettext_lazy("Autre"))]
    CATEGORIES = [("A", gettext_lazy("A (selon MEL)")), ("B", gettext_lazy("B (3 jours)")), ("C", gettext_lazy("C (10 jours)")), ("D", gettext_lazy("D (120 jours)")), ("NM", gettext_lazy("Hors MEL (limite définie)"))]
    CATEGORY_DAYS = {"B": 3, "C": 10, "D": 120}

    number = models.CharField(gettext_lazy("n° défaut"), max_length=20, unique=True, editable=False)
    aircraft = models.ForeignKey(Aircraft, on_delete=models.PROTECT, related_name="defects", verbose_name=gettext_lazy("aéronef"))
    reported_on = models.DateField(gettext_lazy("signalé le"), default=timezone.localdate)
    reported_by = models.CharField(gettext_lazy("signalé par"), max_length=120)
    source = models.CharField(gettext_lazy("source"), max_length=10, choices=SOURCES, default="techlog")
    techlog_ref = models.CharField(gettext_lazy("réf. techlog"), max_length=40, blank=True)
    ata = models.CharField(gettext_lazy("ATA"), max_length=10, blank=True)
    description = models.TextField(gettext_lazy("description"))
    status = models.CharField(gettext_lazy("statut"), max_length=10, choices=STATUSES, default="open")
    # Report
    mel_reference = models.CharField(gettext_lazy("réf. MEL / CDL"), max_length=40, blank=True)
    deferral_category = models.CharField(gettext_lazy("catégorie de report"), max_length=2, choices=CATEGORIES, blank=True)
    deferral_limit_date = models.DateField(gettext_lazy("limite de report (date)"), null=True, blank=True)
    deferral_limit_fh = models.DecimalField(gettext_lazy("limite de report (FH aéronef)"), max_digits=10, decimal_places=2, null=True, blank=True)
    deferral_limit_fc = models.PositiveIntegerField(gettext_lazy("limite de report (cycles aéronef)"), null=True, blank=True)
    operational_procedure = models.TextField(gettext_lazy("procédures (O) / (M) appliquées"), blank=True)
    deferred_by = models.ForeignKey(Staff, on_delete=models.PROTECT, null=True, blank=True, related_name="+", verbose_name=gettext_lazy("reporté par"))
    deferred_at = models.DateTimeField(gettext_lazy("reporté le"), null=True, blank=True)
    fh_at_deferral = models.DecimalField(gettext_lazy("FH aéronef au report"), max_digits=10, decimal_places=2, null=True, blank=True)
    fc_at_deferral = models.PositiveIntegerField(gettext_lazy("cycles aéronef au report"), null=True, blank=True)
    # Extension unique de l'intervalle de rectification (RIE, MEL cat. B et C)
    extended = models.BooleanField(gettext_lazy("délai prorogé (RIE)"), default=False)
    original_limit_date = models.DateField(gettext_lazy("limite initiale (date)"), null=True, blank=True)
    original_limit_fh = models.DecimalField(gettext_lazy("limite initiale (FH)"), max_digits=10, decimal_places=2, null=True, blank=True)
    original_limit_fc = models.PositiveIntegerField(gettext_lazy("limite initiale (cycles)"), null=True, blank=True)
    extension_reference = models.CharField(gettext_lazy("référence RIE"), max_length=40, blank=True)
    extension_reason = models.TextField(gettext_lazy("justification de la prorogation"), blank=True)
    extended_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+",
                                    verbose_name=gettext_lazy("prorogation approuvée par"))
    extended_at = models.DateTimeField(gettext_lazy("prorogé le"), null=True, blank=True)
    authority_notified = models.BooleanField(gettext_lazy("autorité informée de l'utilisation de la RIE"), default=False)
    # Rectification
    rectification = models.TextField(gettext_lazy("action corrective"), blank=True)
    rectified_on = models.DateField(gettext_lazy("rectifié le"), null=True, blank=True)

    class Meta:
        ordering = ["-reported_on", "-number"]
        verbose_name = gettext_lazy("défaut")
        verbose_name_plural = gettext_lazy("défauts")
        permissions = [("defer_defect", gettext_lazy("Reporter un défaut (MEL/CDL)")),
                       ("extend_deferral", gettext_lazy("Approuver une prorogation de report (RIE) – CAMO"))]

    def __str__(self):
        return f"{self.number} {self.aircraft.registration} – {self.description[:50]}"

    def get_absolute_url(self):
        return reverse("part145:defect_detail", args=[self.pk])

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = Sequence.next("DEF")
        super().save(*args, **kwargs)

    EXTENDABLE_CATEGORIES = ("B", "C")

    @property
    def deferral_expired(self):
        """Report échu : date dépassée, ou FH / cycles de l'aéronef atteints."""
        if self.status != "deferred":
            return False
        ac = self.aircraft
        return bool((self.deferral_limit_date and timezone.localdate() > self.deferral_limit_date)
                    or (self.deferral_limit_fh is not None and ac.total_fh >= self.deferral_limit_fh)
                    or (self.deferral_limit_fc is not None and ac.total_fc >= self.deferral_limit_fc))

    def extension_blockers(self, new_date=None, new_fh=None, new_fc=None, on_date=None, check_values=True):
        """Conditions d'une prorogation (RIE) : catégorie B ou C, une seule fois, demandée avant l'échéance,
        durée de la prorogation au plus égale à l'intervalle initial, sur les seuls critères existants."""
        on_date = on_date or timezone.localdate()
        ac = self.aircraft
        problems = []
        if self.status != "deferred":
            return [gettext("Seul un défaut reporté peut faire l'objet d'une prorogation.")]
        if self.extended:
            return [gettext("Le délai a déjà été prorogé une fois : une seconde prorogation est interdite.")]
        if self.deferral_category not in self.EXTENDABLE_CATEGORIES:
            return [gettext("La catégorie {or_} n'admet pas de prorogation (catégories B et C uniquement).").format(or_=self.deferral_category or '—')]
        if (self.deferral_limit_date and on_date > self.deferral_limit_date) or \
                (self.deferral_limit_fh is not None and ac.total_fh >= self.deferral_limit_fh) or \
                (self.deferral_limit_fc is not None and ac.total_fc >= self.deferral_limit_fc):
            problems.append(gettext("La limite de report est atteinte : la prorogation doit être approuvée avant l'échéance."))
        if not check_values:
            return problems
        if new_date is None and new_fh is None and new_fc is None:
            problems.append(gettext("Indiquez la nouvelle limite."))
        start = self.deferred_at.date() if self.deferred_at else None
        for label, new, cur, base in (
            ("date", new_date, self.deferral_limit_date, start),
            ("FH", new_fh, self.deferral_limit_fh, self.fh_at_deferral),
            ("cycles", new_fc, self.deferral_limit_fc, self.fc_at_deferral),
        ):
            if new is None:
                continue
            if cur is None:
                problems.append(gettext("Le report initial n'a pas de limite en {label} : elle ne peut être ajoutée par prorogation.").format(label=label))
                continue
            if new <= cur:
                problems.append(gettext("La nouvelle limite ({label}) doit être postérieure à la limite actuelle.").format(label=label))
                continue
            if base is not None and (new - cur) > (cur - base):
                problems.append(gettext("Prorogation ({label}) supérieure à l'intervalle initial : maximum {base}.").format(label=label, base=cur + (cur - base)))
        return problems

    def default_limit_date(self, start=None):
        days = self.CATEGORY_DAYS.get(self.deferral_category)
        start = start or timezone.localdate()
        return start + timedelta(days=days) if days else None
