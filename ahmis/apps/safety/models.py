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

REPORT_HOURS = 72
FOLLOW_UP_DAYS = 30


class OccurrenceReport(TrackedModel):
    CATEGORIES = [
        ("structure", "Dommage ou défaillance structurale"),
        ("system", "Défaillance ou dysfonctionnement d'un système"),
        ("powerplant", "Moteur, transmission ou rotor"),
        ("maintenance_error", "Erreur de maintenance (montage, oubli, procédure)"),
        ("suspected_unapproved_part", "Pièce suspecte / non approuvée"),
        ("tooling", "Outillage, données ou documentation incorrects"),
        ("ground_damage", "Dommage au sol / manutention"),
        ("fod", "Corps étranger (FOD) / objet oublié"),
        ("other", "Autre"),
    ]
    PHASES = [("maintenance", "En maintenance"), ("flight", "En vol"), ("ground", "Au sol (hors maintenance)"), ("storage", "Stockage / magasin")]
    SEVERITIES = [("low", "Faible"), ("medium", "Significative"), ("high", "Grave"), ("serious_incident", "Incident grave / accident")]
    STATUSES = [
        ("draft", "Brouillon"),
        ("submitted", "Notifié à l'autorité"),
        ("follow_up", "Suivi transmis (≤ 30 j)"),
        ("closed", "Clôturé"),
        ("not_reportable", "Classé non notifiable"),
    ]

    number = models.CharField("n° compte rendu", max_length=20, unique=True, editable=False)
    title = models.CharField("intitulé", max_length=200)
    category = models.CharField("catégorie", max_length=26, choices=CATEGORIES)
    severity = models.CharField("gravité estimée", max_length=16, choices=SEVERITIES, default="medium")
    phase = models.CharField("phase", max_length=12, choices=PHASES, default="maintenance")
    occurred_at = models.DateTimeField("date et heure de l'événement")
    aware_at = models.DateTimeField("connaissance par l'organisme le", default=timezone.now,
                                    help_text="Point de départ du délai de 72 h (art. 4 du règlement 376/2014)")
    location = models.CharField("lieu", max_length=120, blank=True)
    aircraft = models.ForeignKey(Aircraft, on_delete=models.PROTECT, null=True, blank=True, related_name="occurrences", verbose_name="aéronef")
    component = models.ForeignKey(Component, on_delete=models.PROTECT, null=True, blank=True, related_name="occurrences", verbose_name="composant")
    defect = models.ForeignKey("part145.Defect", on_delete=models.PROTECT, null=True, blank=True, related_name="occurrences", verbose_name="défaut lié")
    task_card = models.ForeignKey("part145.TaskCard", on_delete=models.PROTECT, null=True, blank=True, related_name="occurrences", verbose_name="task card liée")
    description = models.TextField("description factuelle")
    immediate_actions = models.TextField("mesures immédiates", blank=True)
    reporter_name = models.CharField("déclarant", max_length=120, blank=True)
    confidential = models.BooleanField("déclaration confidentielle", default=False,
                                       help_text="L'identité du déclarant n'est visible que du responsable qualité / sécurité")
    # Notification
    status = models.CharField("statut", max_length=16, choices=STATUSES, default="draft")
    authority = models.CharField("autorité notifiée", max_length=80, blank=True, help_text="ex. DSAC / ECCAIRS 2")
    authority_reference = models.CharField("référence autorité (ECCAIRS)", max_length=60, blank=True)
    submitted_at = models.DateTimeField("notifié le", null=True, blank=True)
    late_reason = models.TextField("motif du dépassement de 72 h", blank=True)
    design_holder_notified = models.BooleanField("détenteur de la conception informé (145.A.60)", default=False)
    design_holder_reference = models.CharField("référence détenteur de la conception", max_length=60, blank=True)
    customer_notified = models.BooleanField("exploitant / CAMO client informé", default=False)
    not_reportable_reason = models.TextField("justification du classement non notifiable", blank=True)
    # Suivi
    analysis = models.TextField("analyse (causes, facteurs humains)", blank=True)
    corrective_actions = models.TextField("actions correctives / préventives", blank=True)
    follow_up_at = models.DateTimeField("suivi transmis le", null=True, blank=True)
    closed_on = models.DateField("clôturé le", null=True, blank=True)

    class Meta:
        ordering = ["-aware_at"]
        verbose_name = "compte rendu d'événement"
        verbose_name_plural = "comptes rendus d'événements"
        permissions = [("view_all_occurrences", "Voir tous les comptes rendus d'événements"),
                       ("view_reporter_identity", "Voir l'identité des déclarants confidentiels")]

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
            errors["aware_at"] = "L'organisme ne peut avoir eu connaissance de l'événement avant qu'il se produise."
        if self.occurred_at and self.occurred_at > now + timedelta(minutes=5):
            errors["occurred_at"] = "Date dans le futur."
        if self.component_id and self.aircraft_id is None and self.component.aircraft_id:
            self.aircraft_id = self.component.aircraft_id
        if self.defect_id and self.aircraft_id and self.defect.aircraft_id != self.aircraft_id:
            errors["defect"] = "Le défaut lié concerne un autre aéronef."
        if self.status in ("submitted", "follow_up", "closed"):
            if not self.authority:
                errors["authority"] = "Indiquez l'autorité notifiée."
            if not self.submitted_at:
                errors["submitted_at"] = "Indiquez la date de notification."
            elif self.aware_at and self.submitted_at < self.aware_at:
                errors["submitted_at"] = "La notification ne peut précéder la connaissance de l'événement."
            elif self.report_deadline and self.submitted_at > self.report_deadline and not self.late_reason:
                errors["late_reason"] = "Notification au-delà de 72 h : motif obligatoire."
        if self.status in ("follow_up", "closed"):
            if not self.analysis:
                errors["analysis"] = "L'analyse de suivi est obligatoire (art. 13(4))."
            if not self.follow_up_at:
                errors["follow_up_at"] = "Indiquez la date de transmission du suivi."
            elif self.submitted_at and self.follow_up_at < self.submitted_at:
                errors["follow_up_at"] = "Le suivi ne peut précéder la notification."
        if self.status == "closed":
            if not self.corrective_actions:
                errors["corrective_actions"] = "Décrivez les actions correctives avant clôture."
            if not self.closed_on:
                errors["closed_on"] = "Date de clôture obligatoire."
        if self.status == "not_reportable" and not self.not_reportable_reason:
            errors["not_reportable_reason"] = "Justifiez le classement (événement hors liste du règlement 2015/1018)."
        if self.severity == "serious_incident" and self.status == "not_reportable":
            errors["status"] = "Un incident grave ou un accident est toujours notifiable."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if not self.number:
            from apps.core.models import Sequence

            self.number = Sequence.next("OCC")
        super().save(*args, **kwargs)
