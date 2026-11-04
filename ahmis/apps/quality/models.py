"""Qualité : audits internes (145.A.65(c), CAMO.A.200(a)(6)) et gestion documentaire.

Audits : un programme d'audits indépendants vérifie la conformité de l'organisme. Chaque constat
est classé (niveau 1, niveau 2, observation), reçoit un délai de correction, puis est clôturé
par une signature électronique une fois la cause et l'action corrective documentées.

Documents : les documents maîtrisés (MOE, CAME, procédures, formulaires) n'entrent en vigueur
qu'après approbation signée d'une révision par une personne distincte de son rédacteur.
"""
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _g
from django.utils.translation import gettext_lazy as _

from apps.core.models import TrackedModel

# Délais de correction par niveau de constat (jours). Niveau 1 : action immédiate ;
# niveau 2 : jusqu'à 3 mois (145.A.95(b), CAMO.B.350) ; observation : délai interne.
FINDING_DAYS = {"level1": 0, "level2": 90, "observation": 30}

AUDIT_SCOPES = [
    ("part145", "Part-145"),
    ("camo", "Part-CAMO"),
    ("partm", "Part-M"),
    ("part21", "Part-21"),
    ("stores", _("Magasin et logistique")),
    ("supplier", _("Fournisseur / sous-traitant")),
]


class InternalAudit(TrackedModel):
    KINDS = [("system", _("Audit système")), ("process", _("Audit de processus")), ("product", _("Audit produit")),
             ("unannounced", _("Audit inopiné"))]
    STATUSES = [("planned", _("Planifié")), ("in_progress", _("En cours")), ("reported", _("Rapport émis")),
                ("closed", _("Clôturé")), ("cancelled", _("Annulé"))]

    number = models.CharField(_("n° d'audit"), max_length=20, unique=True, editable=False)
    title = models.CharField(_("objet"), max_length=200)
    scope = models.CharField(_("référentiel"), max_length=10, choices=AUDIT_SCOPES)
    kind = models.CharField(_("type"), max_length=12, choices=KINDS, default="process")
    area = models.CharField(_("activité ou service audité"), max_length=150)
    planned_on = models.DateField(_("date prévue"))
    performed_on = models.DateField(_("réalisé le"), null=True, blank=True)
    auditor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+", verbose_name=_("auditeur"))
    auditor_independent = models.BooleanField(
        _("auditeur indépendant de l'activité auditée"), default=False,
        help_text=_("L'auditeur ne doit pas être responsable de l'activité qu'il audite (145.A.65(c))."))
    summary = models.TextField(_("synthèse du rapport"), blank=True)
    status = models.CharField(_("statut"), max_length=12, choices=STATUSES, default="planned")
    closed_on = models.DateField(_("clôturé le"), null=True, blank=True)

    class Meta:
        ordering = ["-planned_on", "-number"]
        verbose_name = _("audit interne")
        verbose_name_plural = _("audits internes")

    def __str__(self):
        return f"{self.number} {self.title}"

    def get_absolute_url(self):
        return reverse("quality:audit_detail", args=[self.pk])

    @property
    def open_findings(self):
        return self.findings.exclude(status="closed")

    @property
    def overdue(self):
        return self.status == "planned" and self.planned_on < timezone.localdate()

    def clean(self):
        errors = {}
        if self.status in ("in_progress", "reported", "closed") and not self.auditor_independent:
            errors["auditor_independent"] = _g("Un audit ne peut démarrer que si l'auditeur est indépendant de l'activité auditée.")
        if self.status in ("reported", "closed"):
            if not self.performed_on:
                errors["performed_on"] = _g("Indiquez la date de réalisation.")
            if not self.summary.strip():
                errors["summary"] = _g("La synthèse du rapport est obligatoire.")
        if self.performed_on and self.performed_on > timezone.localdate():
            errors["performed_on"] = _g("Date dans le futur.")
        if self.status == "closed":
            if not self.closed_on:
                errors["closed_on"] = _g("Date de clôture obligatoire.")
            if self.pk and self.open_findings.exists():
                errors["status"] = _g("Clôture impossible : des constats sont encore ouverts.")
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if not self.number:
            from apps.core.models import Sequence

            self.number = Sequence.next("AUD")
        super().save(*args, **kwargs)


class AuditFinding(TrackedModel):
    LEVELS = [("level1", _("Niveau 1 (action immédiate)")), ("level2", _("Niveau 2 (≤ 3 mois)")),
              ("observation", _("Observation"))]
    STATUSES = [("open", _("Ouvert")), ("closed", _("Clôturé"))]

    number = models.CharField(_("n° de constat"), max_length=20, unique=True, editable=False)
    audit = models.ForeignKey(InternalAudit, on_delete=models.PROTECT, related_name="findings", verbose_name=_("audit"))
    level = models.CharField(_("niveau"), max_length=12, choices=LEVELS, default="level2")
    requirement = models.CharField(_("exigence concernée"), max_length=120, help_text=_("ex. 145.A.42, procédure MOE 2.3"))
    description = models.TextField(_("constat"))
    due_date = models.DateField(_("à corriger avant le"), null=True, blank=True,
                                help_text=_("Vide : calculé selon le niveau (niveau 1 immédiat, niveau 2 sous 90 jours, observation sous 30 jours)."))
    root_cause = models.TextField(_("cause racine"), blank=True)
    corrective_action = models.TextField(_("action corrective"), blank=True)
    status = models.CharField(_("statut"), max_length=8, choices=STATUSES, default="open")
    closed_on = models.DateField(_("clôturé le"), null=True, blank=True)

    class Meta:
        ordering = ["status", "due_date", "number"]
        verbose_name = _("constat d'audit")
        verbose_name_plural = _("constats d'audit")

    def __str__(self):
        return f"{self.number} ({self.get_level_display()})"

    def get_absolute_url(self):
        return reverse("quality:audit_detail", args=[self.audit_id]) + f"#f{self.pk}"

    @property
    def alert(self):
        if self.status == "closed" or not self.due_date:
            return "ok"
        today = timezone.localdate()
        if self.due_date < today:
            return "overdue"
        return "due_soon" if self.due_date <= today + timedelta(days=14) else "ok"

    def clean(self):
        errors = {}
        if self.audit_id and self.audit.status in ("closed", "cancelled") and self._state.adding:
            errors["audit"] = _g("Cet audit est clôturé ou annulé.")
        if self.status == "closed":
            if len(self.root_cause.strip()) < 5:
                errors["root_cause"] = _g("Décrivez la cause racine avant clôture.")
            if len(self.corrective_action.strip()) < 5:
                errors["corrective_action"] = _g("Décrivez l'action corrective avant clôture.")
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if not self.number:
            from apps.core.models import Sequence

            self.number = Sequence.next("CST")
        if not self.due_date:
            base = self.audit.performed_on or timezone.localdate()
            self.due_date = base + timedelta(days=FINDING_DAYS.get(self.level, 30))
        super().save(*args, **kwargs)


class ControlledDocument(TrackedModel):
    TYPES = [("moe", _("Manuel de l'organisme d'entretien (MOE)")), ("came", _("Exposé de gestion de navigabilité (CAME)")),
             ("procedure", _("Procédure")), ("form", _("Formulaire")), ("manual", _("Manuel / instruction de travail")),
             ("other", _("Autre"))]
    STATUSES = [("draft", _("En préparation")), ("current", _("En vigueur")), ("obsolete", _("Retiré"))]

    reference = models.CharField(_("référence"), max_length=40, unique=True)
    title = models.CharField(_("intitulé"), max_length=200)
    doc_type = models.CharField(_("type"), max_length=10, choices=TYPES, default="procedure")
    owner = models.CharField(_("service responsable"), max_length=120, blank=True)
    authority_approval = models.BooleanField(
        _("approbation de l'autorité requise"), default=False,
        help_text=_("MOE et CAME : les modifications sont soumises à l'autorité, sauf procédure de modification indirecte."))
    current_revision = models.CharField(_("révision en vigueur"), max_length=20, blank=True, editable=False)
    current_since = models.DateField(_("en vigueur depuis"), null=True, blank=True, editable=False)
    review_months = models.PositiveSmallIntegerField(_("revue périodique (mois)"), default=24)
    status = models.CharField(_("statut"), max_length=10, choices=STATUSES, default="draft", editable=False)

    class Meta:
        ordering = ["reference"]
        verbose_name = _("document maîtrisé")
        verbose_name_plural = _("documents maîtrisés")

    def __str__(self):
        rev = f" rév. {self.current_revision}" if self.current_revision else ""
        return f"{self.reference}{rev} – {self.title}"

    def get_absolute_url(self):
        return reverse("quality:doc_detail", args=[self.pk])

    @property
    def pending_revision(self):
        return self.revisions.filter(status="pending").first()

    @property
    def review_due(self):
        if not self.current_since or self.status != "current":
            return None
        d = self.current_since
        months = d.month - 1 + self.review_months
        year, month = d.year + months // 12, months % 12 + 1
        import calendar

        return d.replace(year=year, month=month, day=min(d.day, calendar.monthrange(year, month)[1]))

    @property
    def alert(self):
        due = self.review_due
        if not due:
            return "ok"
        today = timezone.localdate()
        return "overdue" if due < today else ("due_soon" if due <= today + timedelta(days=30) else "ok")


class DocumentRevision(TrackedModel):
    STATUSES = [("pending", _("En attente d'approbation")), ("approved", _("Approuvée")), ("superseded", _("Remplacée")),
                ("rejected", _("Refusée"))]

    document = models.ForeignKey(ControlledDocument, on_delete=models.PROTECT, related_name="revisions", verbose_name=_("document"))
    revision = models.CharField(_("révision"), max_length=20)
    change_summary = models.TextField(_("objet de la révision"))
    file = models.FileField(_("fichier"), upload_to="documents/%Y/", blank=True,
                            validators=[FileExtensionValidator(["pdf", "docx", "xlsx", "odt", "ods"])])
    authority_reference = models.CharField(_("référence d'approbation de l'autorité"), max_length=80, blank=True)
    status = models.CharField(_("statut"), max_length=10, choices=STATUSES, default="pending", editable=False)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+",
                                    verbose_name=_("approuvée par"), editable=False)
    approved_at = models.DateTimeField(_("approuvée le"), null=True, blank=True, editable=False)
    rejection_reason = models.CharField(_("motif du refus"), max_length=200, blank=True, editable=False)

    class Meta:
        ordering = ["document", "-created_at"]
        unique_together = [("document", "revision")]
        verbose_name = _("révision de document")
        verbose_name_plural = _("révisions de documents")
        permissions = [("approve_documentrevision", _("Approuver une révision de document"))]

    def __str__(self):
        return f"{self.document.reference} rév. {self.revision}"

    def get_absolute_url(self):
        return self.document.get_absolute_url()

    def clean(self):
        if self._state.adding and self.document_id and self.document.revisions.filter(status="pending").exists():
            raise ValidationError(_g("Une révision est déjà en attente d'approbation pour ce document."))
