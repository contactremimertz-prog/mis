"""Comptes rendus d'événements (règlement (UE) 376/2014, 145.A.60, CAMO.A.160).

Tout événement susceptible de compromettre la sécurité (liste du règlement (UE) 2015/1018) est notifié
à l'autorité dans les 72 heures après que l'organisme en a eu connaissance (art. 4 et 6), ainsi qu'au
détenteur de la conception lorsque l'état de l'aéronef ou d'un composant est en cause. L'organisme
transmet une analyse de suivi dans les 30 jours (art. 13(4)) puis les conclusions définitives.

Culture juste : tout le personnel peut déclarer ; seuls les rôles habilités voient l'ensemble des
comptes rendus, et l'identité du déclarant n'est visible que des personnes habilitées.
"""
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone

from apps.core.models import TrackedModel
from apps.fleet.models import Aircraft, Component
from django.utils.translation import gettext, gettext_lazy

REPORT_HOURS = 72
FOLLOW_UP_DAYS = 30


class OccurrenceReport(TrackedModel):
    CATEGORIES = [
        ("structure", gettext_lazy("Dommage ou défaillance structurale")),
        ("system", gettext_lazy("Défaillance ou dysfonctionnement d'un système")),
        ("powerplant", gettext_lazy("Moteur, transmission ou rotor")),
        ("maintenance_error", gettext_lazy("Erreur de maintenance (montage, oubli, procédure)")),
        ("suspected_unapproved_part", gettext_lazy("Pièce suspecte / non approuvée")),
        ("tooling", gettext_lazy("Outillage, données ou documentation incorrects")),
        ("ground_damage", gettext_lazy("Dommage au sol / manutention")),
        ("fod", gettext_lazy("Corps étranger (FOD) / objet oublié")),
        ("other", gettext_lazy("Autre")),
    ]
    PHASES = [("maintenance", gettext_lazy("En maintenance")), ("flight", gettext_lazy("En vol")), ("ground", gettext_lazy("Au sol (hors maintenance)")), ("storage", gettext_lazy("Stockage / magasin"))]
    SEVERITIES = [("low", gettext_lazy("Faible")), ("medium", gettext_lazy("Significative")), ("high", gettext_lazy("Grave")), ("serious_incident", gettext_lazy("Incident grave / accident"))]
    STATUSES = [
        ("draft", gettext_lazy("Brouillon")),
        ("submitted", gettext_lazy("Notifié à l'autorité")),
        ("follow_up", gettext_lazy("Suivi transmis (≤ 30 j)")),
        ("closed", gettext_lazy("Clôturé")),
        ("not_reportable", gettext_lazy("Classé non notifiable")),
    ]

    number = models.CharField(gettext_lazy("n° compte rendu"), max_length=20, unique=True, editable=False)
    title = models.CharField(gettext_lazy("intitulé"), max_length=200)
    category = models.CharField(gettext_lazy("catégorie"), max_length=26, choices=CATEGORIES)
    severity = models.CharField(gettext_lazy("gravité estimée"), max_length=16, choices=SEVERITIES, default="medium")
    phase = models.CharField(gettext_lazy("phase"), max_length=12, choices=PHASES, default="maintenance")
    occurred_at = models.DateTimeField(gettext_lazy("date et heure de l'événement"))
    aware_at = models.DateTimeField(gettext_lazy("connaissance par l'organisme le"), default=timezone.now,
                                    help_text=gettext_lazy("Point de départ du délai de 72 h (art. 4 du règlement 376/2014)"))
    location = models.CharField(gettext_lazy("lieu"), max_length=120, blank=True)
    aircraft = models.ForeignKey(Aircraft, on_delete=models.PROTECT, null=True, blank=True, related_name="occurrences", verbose_name=gettext_lazy("aéronef"))
    component = models.ForeignKey(Component, on_delete=models.PROTECT, null=True, blank=True, related_name="occurrences", verbose_name=gettext_lazy("composant"))
    defect = models.ForeignKey("part145.Defect", on_delete=models.PROTECT, null=True, blank=True, related_name="occurrences", verbose_name=gettext_lazy("défaut lié"))
    task_card = models.ForeignKey("part145.TaskCard", on_delete=models.PROTECT, null=True, blank=True, related_name="occurrences", verbose_name=gettext_lazy("task card liée"))
    description = models.TextField(gettext_lazy("description factuelle"))
    immediate_actions = models.TextField(gettext_lazy("mesures immédiates"), blank=True)
    reporter_name = models.CharField(gettext_lazy("déclarant"), max_length=120, blank=True)
    confidential = models.BooleanField(gettext_lazy("déclaration confidentielle"), default=False,
                                       help_text=gettext_lazy("L'identité du déclarant n'est visible que du responsable qualité / sécurité"))
    # Notification
    status = models.CharField(gettext_lazy("statut"), max_length=16, choices=STATUSES, default="draft")
    authority = models.CharField(gettext_lazy("autorité notifiée"), max_length=80, blank=True, help_text=gettext_lazy("ex. DSAC / ECCAIRS 2"))
    authority_reference = models.CharField(gettext_lazy("référence autorité (ECCAIRS)"), max_length=60, blank=True)
    submitted_at = models.DateTimeField(gettext_lazy("notifié le"), null=True, blank=True)
    late_reason = models.TextField(gettext_lazy("motif du dépassement de 72 h"), blank=True)
    design_holder_notified = models.BooleanField(gettext_lazy("détenteur de la conception informé (145.A.60)"), default=False)
    design_holder_reference = models.CharField(gettext_lazy("référence détenteur de la conception"), max_length=60, blank=True)
    customer_notified = models.BooleanField(gettext_lazy("exploitant / CAMO client informé"), default=False)
    not_reportable_reason = models.TextField(gettext_lazy("justification du classement non notifiable"), blank=True)
    # Suivi
    analysis = models.TextField(gettext_lazy("analyse (causes, facteurs humains)"), blank=True)
    corrective_actions = models.TextField(gettext_lazy("actions correctives / préventives"), blank=True)
    follow_up_at = models.DateTimeField(gettext_lazy("suivi transmis le"), null=True, blank=True)
    closed_on = models.DateField(gettext_lazy("clôturé le"), null=True, blank=True)

    class Meta:
        ordering = ["-aware_at"]
        verbose_name = gettext_lazy("compte rendu d'événement")
        verbose_name_plural = gettext_lazy("comptes rendus d'événements")
        permissions = [("view_all_occurrences", gettext_lazy("Voir tous les comptes rendus d'événements")),
                       ("view_reporter_identity", gettext_lazy("Voir l'identité des déclarants confidentiels"))]

    def audit_masked_fields(self):
        """Champs jamais écrits en clair au journal d'audit (culture juste, 376/2014 art. 16)."""
        return ("reporter_name",) if self.confidential else ()

    def __str__(self):
        return f"{self.number} {self.title}"

    def get_absolute_url(self):
        return reverse("safety:detail", args=[self.pk])

    # ---------------------------------------------------------------- délais
    @property
    def report_deadline(self):
        return self.aware_at + timedelta(hours=REPORT_HOURS) if self.aware_at else None

    @property
    def follow_up_deadline(self):
        return self.submitted_at + timedelta(days=FOLLOW_UP_DAYS) if self.submitted_at else None

    @property
    def report_late(self):
        """True si la notification a été (ou sera) faite après 72 h."""
        if self.status == "not_reportable" or not self.report_deadline:
            return False
        ref = self.submitted_at or timezone.now()
        return ref > self.report_deadline

    @property
    def follow_up_late(self):
        if self.status not in ("submitted",) or not self.follow_up_deadline:
            return False
        return timezone.now() > self.follow_up_deadline

    @property
    def hours_left(self):
        if self.status != "draft" or not self.report_deadline:
            return None
        return int((self.report_deadline - timezone.now()).total_seconds() // 3600)

    @property
    def alert(self):
        """overdue / due_soon / ok pour les tableaux de bord."""
        if self.status == "draft":
            h = self.hours_left
            return "overdue" if h < 0 else ("due_soon" if h <= 24 else "ok")
        if self.follow_up_late:
            return "overdue"
        return "ok"

    def clean(self):
        errors = {}
        now = timezone.now()
        if self.occurred_at and self.aware_at and self.aware_at < self.occurred_at:
            errors["aware_at"] = gettext("L'organisme ne peut avoir eu connaissance de l'événement avant qu'il se produise.")
        if self.occurred_at and self.occurred_at > now + timedelta(minutes=5):
            errors["occurred_at"] = gettext("Date dans le futur.")
        if self.component_id and self.aircraft_id is None and self.component.aircraft_id:
            self.aircraft_id = self.component.aircraft_id
        if self.defect_id and self.aircraft_id and self.defect.aircraft_id != self.aircraft_id:
            errors["defect"] = gettext("Le défaut lié concerne un autre aéronef.")
        if self.status in ("submitted", "follow_up", "closed"):
            if not self.authority:
                errors["authority"] = gettext("Indiquez l'autorité notifiée.")
            if not self.submitted_at:
                errors["submitted_at"] = gettext("Indiquez la date de notification.")
            elif self.aware_at and self.submitted_at < self.aware_at:
                errors["submitted_at"] = gettext("La notification ne peut précéder la connaissance de l'événement.")
            elif self.report_deadline and self.submitted_at > self.report_deadline and not self.late_reason:
                errors["late_reason"] = gettext("Notification au-delà de 72 h : motif obligatoire.")
        if self.status in ("follow_up", "closed"):
            if not self.analysis:
                errors["analysis"] = gettext("L'analyse de suivi est obligatoire (art. 13(4)).")
            if not self.follow_up_at:
                errors["follow_up_at"] = gettext("Indiquez la date de transmission du suivi.")
            elif self.submitted_at and self.follow_up_at < self.submitted_at:
                errors["follow_up_at"] = gettext("Le suivi ne peut précéder la notification.")
        if self.status == "closed":
            if not self.corrective_actions:
                errors["corrective_actions"] = gettext("Décrivez les actions correctives avant clôture.")
            if not self.closed_on:
                errors["closed_on"] = gettext("Date de clôture obligatoire.")
        if self.status == "not_reportable" and not self.not_reportable_reason:
            errors["not_reportable_reason"] = gettext("Justifiez le classement (événement hors liste du règlement 2015/1018).")
        if self.severity == "serious_incident" and self.status == "not_reportable":
            errors["status"] = gettext("Un incident grave ou un accident est toujours notifiable.")
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if not self.number:
            from apps.core.models import Sequence

            self.number = Sequence.next("OCC")
        super().save(*args, **kwargs)
