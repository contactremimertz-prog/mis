from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone

from apps.core.models import TrackedModel
from django.utils.translation import gettext, gettext_lazy

D0 = Decimal("0")


class AircraftType(TrackedModel):
    CATEGORIES = [("helicopter", gettext_lazy("Hélicoptère")), ("aeroplane", gettext_lazy("Avion"))]
    FRAMES = [
        ("part-camo", gettext_lazy("Part-CAMO (transport commercial / complexe)")),
        ("part-cao", gettext_lazy("Part-CAO / Part-ML (non complexe)")),
    ]

    code = models.CharField(gettext_lazy("code type"), max_length=30, unique=True, help_text=gettext_lazy("ex. H135, H145-D3, ATR72-600"))
    manufacturer = models.CharField(gettext_lazy("constructeur"), max_length=80)
    model = models.CharField(gettext_lazy("modèle / variante"), max_length=80)
    category = models.CharField(gettext_lazy("catégorie"), max_length=12, choices=CATEGORIES)
    regulatory_frame = models.CharField(gettext_lazy("cadre réglementaire"), max_length=12, choices=FRAMES, default="part-camo")
    engine_count = models.PositiveSmallIntegerField(gettext_lazy("nombre de moteurs"), default=1)
    engine_model = models.CharField(gettext_lazy("motorisation"), max_length=80, blank=True)
    cycle_label = models.CharField(
        gettext_lazy("libellé des cycles"), max_length=40, default=gettext_lazy("Cycles"),
        help_text=gettext_lazy("ex. « Atterrissages » pour un hélicoptère, « Cycles » pour un avion"),
    )
    mtow_kg = models.PositiveIntegerField(gettext_lazy("MTOW (kg)"), null=True, blank=True)
    notes = models.TextField(gettext_lazy("notes"), blank=True)

    class Meta:
        ordering = ["manufacturer", "code"]
        verbose_name = gettext_lazy("type d'aéronef")
        verbose_name_plural = gettext_lazy("types d'aéronefs")

    def __str__(self):
        return f"{self.manufacturer} {self.code}"


class Aircraft(TrackedModel):
    STATUSES = [
        ("active", gettext_lazy("En exploitation")),
        ("maintenance", gettext_lazy("En maintenance")),
        ("aog", gettext_lazy("AOG (au sol)")),
        ("stored", gettext_lazy("Stocké")),
        ("retired", gettext_lazy("Retiré")),
    ]

    registration = models.CharField(gettext_lazy("immatriculation"), max_length=12, unique=True)
    msn = models.CharField(gettext_lazy("numéro de série (MSN)"), max_length=30)
    aircraft_type = models.ForeignKey(AircraftType, on_delete=models.PROTECT, verbose_name=gettext_lazy("type"), related_name="aircraft")
    status = models.CharField(gettext_lazy("statut"), max_length=12, choices=STATUSES, default="active")
    operator = models.CharField(gettext_lazy("exploitant"), max_length=120, blank=True)
    owner = models.CharField(gettext_lazy("propriétaire"), max_length=120, blank=True)
    base = models.CharField(gettext_lazy("base"), max_length=60, blank=True)
    manufacture_date = models.DateField(gettext_lazy("date de fabrication"))
    entry_into_service = models.DateField(gettext_lazy("mise en service"), null=True, blank=True)
    # Compteurs cellule
    total_fh = models.DecimalField(gettext_lazy("heures totales (FH)"), max_digits=10, decimal_places=2, default=D0)
    total_fc = models.PositiveIntegerField(gettext_lazy("cycles / atterrissages totaux"), default=0)
    counters_date = models.DateField(gettext_lazy("compteurs à jour au"), default=timezone.localdate)
    # Hypothèses d'utilisation pour le forecast
    planned_daily_fh = models.DecimalField(gettext_lazy("utilisation prévue (FH/jour)"), max_digits=6, decimal_places=2, default=Decimal("1.50"))
    planned_daily_fc = models.DecimalField(gettext_lazy("utilisation prévue (cycles/jour)"), max_digits=6, decimal_places=2, default=Decimal("2.00"))
    # Navigabilité
    arc_expiry = models.DateField(gettext_lazy("expiration ARC (revue de navigabilité)"), null=True, blank=True)
    cofa_number = models.CharField(gettext_lazy("n° certificat de navigabilité"), max_length=40, blank=True)
    withdrawn_on = models.DateField(
        gettext_lazy("retrait définitif du service le"), null=True, blank=True,
        help_text=gettext_lazy("Point de départ de la conservation des enregistrements d'état (12 mois, M.A.305(h))"),
    )
    notes = models.TextField(gettext_lazy("notes"), blank=True)

    class Meta:
        ordering = ["registration"]
        verbose_name = gettext_lazy("aéronef")
        verbose_name_plural = gettext_lazy("aéronefs")

    def __str__(self):
        return f"{self.registration} ({self.aircraft_type.code} MSN {self.msn})"

    def get_absolute_url(self):
        return reverse("fleet:aircraft_detail", args=[self.pk])

    def clean(self):
        errors = {}
        if self.entry_into_service and self.manufacture_date and self.entry_into_service < self.manufacture_date:
            errors["entry_into_service"] = gettext("La mise en service ne peut précéder la fabrication.")
        if self.status == "retired" and not self.withdrawn_on:
            errors["withdrawn_on"] = gettext("Date de retrait définitif obligatoire pour un aéronef retiré.")
        if self.withdrawn_on and self.status != "retired":
            errors["withdrawn_on"] = gettext("Une date de retrait n'est permise que pour un aéronef au statut « Retiré ».")
        if self.withdrawn_on and self.withdrawn_on > timezone.localdate():
            errors["withdrawn_on"] = gettext("La date de retrait ne peut être dans le futur.")
        if errors:
            raise ValidationError(errors)

    @property
    def retention_until(self):
        """Fin de la conservation minimale des enregistrements d'état (None = aéronef non retiré)."""
        from apps.core.retention import aircraft_life

        return aircraft_life(self)

    @property
    def installed_components(self):
        return self.components.filter(status="installed")

    def counters_at(self, on_date):
        """Compteurs cellule à une date donnée, reconstitués à partir des saisies d'utilisation."""
        if on_date >= self.counters_date:
            return self.total_fh, self.total_fc
        before = self.utilisation.filter(date__lte=on_date).order_by("-date", "-id").first()
        if before:
            return before.fh_after, before.fc_after
        first = self.utilisation.order_by("date", "id").first()
        if first:
            return first.fh_after - first.fh, first.fc_after - first.fc
        return self.total_fh, self.total_fc

    @transaction.atomic
    def record_utilisation(self, date, fh, fc, reference="", source="techlog", external_id=None):
        """Ajoute des heures / cycles : incrémente la cellule et tous les composants installés.

        Si ``external_id`` est fourni et déjà connu, la saisie existante est renvoyée sans rien recompter
        (idempotence : un système externe peut renvoyer le même vol sans double comptage).
        """
        if external_id:
            existing = UtilisationRecord.objects.filter(external_id=external_id).first()
            if existing:
                if existing.aircraft_id != self.pk:
                    raise ValidationError(gettext("L'identifiant externe {external_id} est déjà utilisé pour un autre aéronef.").format(external_id=external_id))
                return existing
        fh = Decimal(str(fh))
        fc = int(fc)
        if fh < 0 or fc < 0:
            raise ValidationError(gettext("Les heures et cycles saisis doivent être positifs."))
        if self.status == "retired":
            raise ValidationError(gettext("Aéronef retiré : saisie impossible."))
        rec = UtilisationRecord.objects.create(
            aircraft=self, date=date, fh=fh, fc=fc, reference=reference, source=source, external_id=external_id or None,
            fh_after=self.total_fh + fh, fc_after=self.total_fc + fc,
        )
        self.total_fh += fh
        self.total_fc += fc
        if date > self.counters_date:
            self.counters_date = date
        self.save()
        for comp in self.components.filter(status="installed").select_for_update():
            comp.tsn_fh += fh
            comp.csn += fc
            comp.tso_fh += fh
            comp.cso += fc
            comp.save()
        return rec


class UtilisationRecord(TrackedModel):
    SOURCES = [("techlog", gettext_lazy("Compte-rendu matériel / techlog")), ("manual", gettext_lazy("Saisie manuelle")), ("import", gettext_lazy("Import")), ("api", gettext_lazy("API externe"))]

    aircraft = models.ForeignKey(Aircraft, on_delete=models.PROTECT, related_name="utilisation", verbose_name=gettext_lazy("aéronef"))
    external_id = models.CharField(
        gettext_lazy("identifiant externe"), max_length=80, null=True, blank=True, unique=True,
        help_text=gettext_lazy("Identifiant de la saisie dans le système émetteur (vol, CRM) : empêche les doublons en cas de renvoi"),
    )
    date = models.DateField(gettext_lazy("date"))
    fh = models.DecimalField(gettext_lazy("heures de vol"), max_digits=7, decimal_places=2)
    fc = models.PositiveIntegerField(gettext_lazy("cycles / atterrissages"))
    reference = models.CharField(gettext_lazy("référence (n° page techlog...)"), max_length=60, blank=True)
    source = models.CharField(gettext_lazy("source"), max_length=10, choices=SOURCES, default="techlog")
    fh_after = models.DecimalField(gettext_lazy("total FH après saisie"), max_digits=10, decimal_places=2)
    fc_after = models.PositiveIntegerField(gettext_lazy("total cycles après saisie"))

    class Meta:
        ordering = ["-date", "-id"]
        verbose_name = gettext_lazy("saisie d'utilisation")
        verbose_name_plural = gettext_lazy("saisies d'utilisation")

    def __str__(self):
        return f"{self.aircraft.registration} {self.date:%d/%m/%Y} +{self.fh} FH +{self.fc} cyc"


class PartNumber(TrackedModel):
    """Référence article (P/N) : catalogue commun CAMO / 145 / magasin."""

    # Classement 145.A.42(a) / M.A.501 : détermine le justificatif exigé à réception
    CATEGORIES = [
        ("component", gettext_lazy("Élément / équipement (component)")),
        ("standard_part", gettext_lazy("Pièce standard (norme)")),
        ("raw_material", gettext_lazy("Matière première")),
        ("consumable", gettext_lazy("Ingrédient / consommable")),
    ]
    RELEASE_CERTS = ("easa_form1", "faa_8130", "dual", "tcca_one")

    pn = models.CharField(gettext_lazy("P/N"), max_length=60, unique=True)
    category = models.CharField(gettext_lazy("classe (145.A.42)"), max_length=14, choices=CATEGORIES, default="component",
                                help_text=gettext_lazy("Élément : certificat libératoire (EASA Form 1 ou équivalent) exigé. Pièce standard, "
                                          "matière, consommable : certificat de conformité acceptable."))
    specification = models.CharField(gettext_lazy("norme / spécification"), max_length=80, blank=True,
                                     help_text=gettext_lazy("ex. NAS1611-012, MS20995C32, AMS 4911 – obligatoire pour une pièce standard ou une matière"))
    description = models.CharField(gettext_lazy("désignation"), max_length=150)
    manufacturer = models.CharField(gettext_lazy("constructeur"), max_length=80, blank=True)
    ata = models.CharField(gettext_lazy("chapitre ATA"), max_length=10, blank=True)
    is_serialized = models.BooleanField(gettext_lazy("suivi au numéro de série"), default=False)
    is_rotable = models.BooleanField(gettext_lazy("rotable / réparable"), default=False)
    is_llp = models.BooleanField(gettext_lazy("pièce à vie limitée (LLP)"), default=False)
    is_tool = models.BooleanField(gettext_lazy("outillage"), default=False)
    shelf_life_controlled = models.BooleanField(gettext_lazy("durée de stockage limitée"), default=False)
    unit = models.CharField(gettext_lazy("unité"), max_length=10, default="EA")
    # Limites de vie (LLP) – depuis neuf
    life_limit_fh = models.DecimalField(gettext_lazy("limite de vie (FH)"), max_digits=10, decimal_places=2, null=True, blank=True)
    life_limit_fc = models.PositiveIntegerField(gettext_lazy("limite de vie (cycles)"), null=True, blank=True)
    life_limit_days = models.PositiveIntegerField(gettext_lazy("limite de vie calendaire (jours)"), null=True, blank=True)
    # Potentiel entre révisions (TBO) – depuis révision
    tbo_fh = models.DecimalField(gettext_lazy("TBO (FH)"), max_digits=10, decimal_places=2, null=True, blank=True)
    tbo_fc = models.PositiveIntegerField(gettext_lazy("TBO (cycles)"), null=True, blank=True)
    tbo_days = models.PositiveIntegerField(gettext_lazy("TBO calendaire (jours)"), null=True, blank=True)
    applicable_types = models.ManyToManyField(AircraftType, blank=True, verbose_name=gettext_lazy("types applicables"), related_name="part_numbers")
    alternates = models.ManyToManyField("self", blank=True, verbose_name=gettext_lazy("P/N interchangeables"))
    notes = models.TextField(gettext_lazy("notes"), blank=True)

    class Meta:
        ordering = ["pn"]
        verbose_name = gettext_lazy("référence article (P/N)")
        verbose_name_plural = gettext_lazy("références articles (P/N)")

    def __str__(self):
        return f"{self.pn} – {self.description}"

    def get_absolute_url(self):
        return reverse("fleet:pn_detail", args=[self.pk])

    def clean(self):
        if self.is_llp and not (self.life_limit_fh or self.life_limit_fc or self.life_limit_days):
            raise ValidationError(gettext("Une LLP doit avoir au moins une limite de vie (FH, cycles ou jours)."))
        if (self.is_llp or self.tbo_fh or self.tbo_fc or self.tbo_days) and not self.is_serialized:
            raise ValidationError(gettext("Une pièce à vie limitée ou à TBO doit être suivie au numéro de série."))
        if (self.is_serialized or self.is_llp or self.is_rotable) and self.category != "component" and not self.is_tool:
            raise ValidationError({"category": gettext("Une pièce sérialisée, rotable ou à vie limitée est un élément (component).")})
        if self.category in ("standard_part", "raw_material") and not self.specification:
            raise ValidationError({"specification": gettext("Norme ou spécification obligatoire pour une pièce standard ou une matière.")})

    @property
    def requires_release_certificate(self):
        """Élément : seul un certificat libératoire autorisé (EASA Form 1 ou équivalent) est acceptable."""
        return self.category == "component" and not self.is_tool


class Component(TrackedModel):
    """Article sérialisé (moteur, BTP, moyeu, équipement...) avec ses compteurs."""

    STATUSES = [
        ("installed", gettext_lazy("Installé")),
        ("serviceable", gettext_lazy("En stock – utilisable")),
        ("reserved", gettext_lazy("Réservé (task card)")),
        ("unserviceable", gettext_lazy("Non utilisable (U/S)")),
        ("quarantine", gettext_lazy("Quarantaine")),
        ("repair", gettext_lazy("En réparation / révision")),
        ("scrapped", gettext_lazy("Rebuté")),
    ]
    CONDITIONS = [("new", gettext_lazy("Neuf")), ("overhauled", gettext_lazy("Révisé")), ("repaired", gettext_lazy("Réparé")), ("inspected", gettext_lazy("Inspecté/testé")), ("used", gettext_lazy("Usagé"))]

    part_number = models.ForeignKey(PartNumber, on_delete=models.PROTECT, verbose_name=gettext_lazy("P/N"), related_name="components")
    serial_number = models.CharField(gettext_lazy("S/N"), max_length=60)
    status = models.CharField(gettext_lazy("statut"), max_length=14, choices=STATUSES, default="serviceable")
    condition = models.CharField(gettext_lazy("état"), max_length=12, choices=CONDITIONS, default="new")
    manufacture_date = models.DateField(gettext_lazy("date de fabrication"), null=True, blank=True)
    last_overhaul_date = models.DateField(gettext_lazy("date dernière révision"), null=True, blank=True)
    # Compteurs
    tsn_fh = models.DecimalField(gettext_lazy("TSN (heures depuis neuf)"), max_digits=10, decimal_places=2, default=D0)
    csn = models.PositiveIntegerField(gettext_lazy("CSN (cycles depuis neuf)"), default=0)
    tso_fh = models.DecimalField(gettext_lazy("TSO (heures depuis révision)"), max_digits=10, decimal_places=2, default=D0)
    cso = models.PositiveIntegerField(gettext_lazy("CSO (cycles depuis révision)"), default=0)
    # Localisation
    aircraft = models.ForeignKey(Aircraft, on_delete=models.PROTECT, null=True, blank=True, related_name="components", verbose_name=gettext_lazy("aéronef"))
    position = models.CharField(gettext_lazy("position"), max_length=40, blank=True, help_text=gettext_lazy("ex. MOT 1, BTP, MRH, BTA"))
    location = models.ForeignKey("logistics.StoreLocation", on_delete=models.PROTECT, null=True, blank=True, verbose_name=gettext_lazy("emplacement magasin"), related_name="components")
    reserved_for = models.ForeignKey("part145.TaskCard", on_delete=models.PROTECT, null=True, blank=True, related_name="reserved_components", verbose_name=gettext_lazy("réservé pour"))
    status_reason = models.CharField(gettext_lazy("motif du statut"), max_length=200, blank=True)
    notes = models.TextField(gettext_lazy("notes"), blank=True)
    # Pièce non récupérable (145.A.42(d), M.A.504(d)) : statut définitif, mutilation avant élimination
    SCRAP_REASONS = [("life_limit", gettext_lazy("Limite de vie atteinte (LLP)")), ("beyond_repair", gettext_lazy("Non réparable / hors tolérances")),
                     ("beyond_economic", gettext_lazy("Réparation non économique")), ("damage", gettext_lazy("Endommagée (accident, incendie, corrosion)")),
                     ("no_traceability", gettext_lazy("Traçabilité insuffisante / origine inconnue")), ("other", gettext_lazy("Autre"))]
    scrapped_on = models.DateField(gettext_lazy("rebuté le"), null=True, blank=True)
    scrap_reason = models.CharField(gettext_lazy("motif du rebut"), max_length=16, choices=SCRAP_REASONS, blank=True)
    mutilation_method = models.CharField(gettext_lazy("méthode de mutilation"), max_length=150, blank=True,
                                         help_text=gettext_lazy("ex. découpe, écrasement, perçage – rendant la pièce inutilisable et non réparable"))
    mutilation_witness = models.CharField(gettext_lazy("mutilation constatée par"), max_length=120, blank=True)
    scrap_reference = models.CharField(gettext_lazy("réf. certificat de destruction"), max_length=60, blank=True)

    class Meta:
        ordering = ["part_number__pn", "serial_number"]
        unique_together = [("part_number", "serial_number")]
        verbose_name = "composant"
        verbose_name_plural = "composants"

    def __str__(self):
        return f"{self.part_number.pn} S/N {self.serial_number}"

    def get_absolute_url(self):
        return reverse("fleet:component_detail", args=[self.pk])

    def clean(self):
        if self.status == "installed" and not self.aircraft_id:
            raise ValidationError(gettext("Un composant installé doit être rattaché à un aéronef."))
        if self.status != "installed" and self.aircraft_id:
            raise ValidationError(gettext("Seul un composant installé peut être rattaché à un aéronef."))
        if self.pk and self.status != "scrapped" and Component.objects.filter(pk=self.pk, status="scrapped").exists():
            raise ValidationError(gettext("Pièce rebutée : statut définitif, elle ne peut réintégrer le stock ni être posée (145.A.42)."))
        if self.status == "scrapped":
            missing = [label for f, label in (("scrapped_on", "date"), ("scrap_reason", "motif"), ("mutilation_method", gettext("méthode de mutilation")),
                                              ("mutilation_witness", gettext("témoin de la mutilation"))) if not getattr(self, f)]
            if missing:
                raise ValidationError(gettext("Mise au rebut incomplète : {missing}.").format(missing=', '.join(missing)))

    def save(self, *args, **kwargs):
        # Garde-fou indépendant des écrans : une pièce rebutée ne change plus de statut
        if self.pk and self.status != "scrapped" and Component.objects.filter(pk=self.pk, status="scrapped").exists():
            raise ValidationError(gettext("Pièce rebutée : statut définitif (145.A.42)."))
        super().save(*args, **kwargs)

    # --- Limites -------------------------------------------------------
    def life_status(self, on_date=None):
        """Retourne une liste de dicts {critère, limite, consommé, restant} (LLP et TBO)."""
        pn = self.part_number
        today = on_date or timezone.localdate()
        rows = []

        def add(kind, label, limit, used, unit):
            if limit is None:
                return
            remaining = Decimal(str(limit)) - Decimal(str(used))
            rows.append({"kind": kind, "label": label, "limit": limit, "used": used, "remaining": remaining, "unit": unit})

        if pn.is_llp:
            add("llp", gettext("Vie (heures)"), pn.life_limit_fh, self.tsn_fh, "FH")
            add("llp", gettext("Vie (cycles)"), pn.life_limit_fc, self.csn, "cyc")
            if pn.life_limit_days and self.manufacture_date:
                add("llp", gettext("Vie (jours)"), pn.life_limit_days, (today - self.manufacture_date).days, "j")
        add("tbo", gettext("TBO (heures)"), pn.tbo_fh, self.tso_fh, "FH")
        add("tbo", gettext("TBO (cycles)"), pn.tbo_fc, self.cso, "cyc")
        if pn.tbo_days:
            ref = self.last_overhaul_date or self.manufacture_date
            if ref:
                add("tbo", gettext("TBO (jours)"), pn.tbo_days, (today - ref).days, "j")
        return rows

    @property
    def is_life_expired(self):
        return any(r["remaining"] <= 0 for r in self.life_status())

    @property
    def certificates(self):
        return self.release_certificates.all()

    @property
    def has_valid_certificate(self):
        return self.release_certificates.filter(is_valid=True).exists()


class InstallationRecord(TrackedModel):
    """Historique de montage / dépose : traçabilité « back-to-birth »."""

    component = models.ForeignKey(Component, on_delete=models.PROTECT, related_name="installations", verbose_name=gettext_lazy("composant"))
    aircraft = models.ForeignKey(Aircraft, on_delete=models.PROTECT, related_name="installation_records", verbose_name=gettext_lazy("aéronef"))
    position = models.CharField(gettext_lazy("position"), max_length=40, blank=True)
    installed_on = models.DateField(gettext_lazy("posé le"))
    ac_fh_at_install = models.DecimalField(gettext_lazy("FH aéronef à la pose"), max_digits=10, decimal_places=2)
    ac_fc_at_install = models.PositiveIntegerField(gettext_lazy("cycles aéronef à la pose"))
    comp_tsn_at_install = models.DecimalField(gettext_lazy("TSN composant à la pose"), max_digits=10, decimal_places=2)
    comp_csn_at_install = models.PositiveIntegerField(gettext_lazy("CSN composant à la pose"))
    removed_on = models.DateField(gettext_lazy("déposé le"), null=True, blank=True)
    ac_fh_at_removal = models.DecimalField(gettext_lazy("FH aéronef à la dépose"), max_digits=10, decimal_places=2, null=True, blank=True)
    ac_fc_at_removal = models.PositiveIntegerField(gettext_lazy("cycles aéronef à la dépose"), null=True, blank=True)
    removal_reason = models.CharField(gettext_lazy("motif de dépose"), max_length=200, blank=True)
    removal_type = models.CharField(
        gettext_lazy("type de dépose"), max_length=12, blank=True,
        choices=[("scheduled", gettext_lazy("Programmée (butée)")), ("unscheduled", gettext_lazy("Non programmée (panne)")), ("convenience", gettext_lazy("Commodité / robbery"))],
    )
    task_card = models.ForeignKey("part145.TaskCard", on_delete=models.PROTECT, null=True, blank=True, related_name="installation_records", verbose_name=gettext_lazy("task card"))

    class Meta:
        ordering = ["-installed_on", "-id"]
        verbose_name = gettext_lazy("historique de montage")
        verbose_name_plural = gettext_lazy("historiques de montage")

    def __str__(self):
        return f"{self.component} sur {self.aircraft.registration} {self.position} ({self.installed_on:%d/%m/%Y})"


@transaction.atomic
def remove_component(component, date, reason, removal_type="unscheduled", new_status="unserviceable", task_card=None):
    if component.status != "installed":
        raise ValidationError(gettext("{component} n'est pas installé.").format(component=component))
    aircraft = component.aircraft
    rec = component.installations.filter(removed_on__isnull=True).first()
    if rec:
        rec.removed_on = date
        rec.ac_fh_at_removal = aircraft.total_fh
        rec.ac_fc_at_removal = aircraft.total_fc
        rec.removal_reason = reason
        rec.removal_type = removal_type
        if task_card and not rec.task_card_id:
            rec.task_card = task_card
        rec.save()
    component.status = new_status
    component.status_reason = reason
    component.aircraft = None
    component.position = ""
    component.save()
    return rec


def installation_errors(component, aircraft, position, task_card=None, replacing=None):
    """Contrôles de navigabilité avant pose. `replacing` : composant déposé dans le même mouvement."""
    errors = []
    if component.status not in ("serviceable", "reserved"):
        errors.append(gettext("statut « {get_status_display} » : seule une pièce utilisable peut être posée").format(get_status_display=component.get_status_display()))
    if component.status == "reserved" and component.reserved_for_id not in (None, getattr(task_card, "pk", None)):
        errors.append(gettext("pièce réservée pour une autre task card"))
    if not component.has_valid_certificate:
        errors.append(gettext("aucun certificat libératoire valide (EASA Form 1 / FAA 8130-3)"))
    if component.is_life_expired:
        errors.append(gettext("limite de vie ou TBO atteinte"))
    types = component.part_number.applicable_types.all()
    if types and aircraft.aircraft_type not in types:
        errors.append(gettext("P/N non applicable au type {code}").format(code=aircraft.aircraft_type.code))
    if position:
        occupied = aircraft.components.filter(status="installed", position=position, part_number=component.part_number)
        if replacing is not None:
            occupied = occupied.exclude(pk=replacing.pk)
        if occupied.exists():
            errors.append(gettext("position {position} déjà occupée par un {pn}").format(position=position, pn=component.part_number.pn))
    return [gettext("Pose refusée : ") + e for e in errors]


@transaction.atomic
def install_component(component, aircraft, position, date, task_card=None, force=False):
    """Pose d'un composant : contrôles de navigabilité de la pièce."""
    errors = installation_errors(component, aircraft, position, task_card)
    if errors and not force:
        raise ValidationError(errors)
    component.status = "installed"
    component.aircraft = aircraft
    component.position = position
    component.location = None
    component.reserved_for = None
    component.status_reason = ""
    component.save()
    return InstallationRecord.objects.create(
        component=component, aircraft=aircraft, position=position, installed_on=date,
        ac_fh_at_install=aircraft.total_fh, ac_fc_at_install=aircraft.total_fc,
        comp_tsn_at_install=component.tsn_fh, comp_csn_at_install=component.csn, task_card=task_card,
    )
