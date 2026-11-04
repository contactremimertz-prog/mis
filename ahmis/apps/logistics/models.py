from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone

from apps.core.models import TrackedModel


class StoreLocation(TrackedModel):
    code = models.CharField("code", max_length=30, unique=True)
    name = models.CharField("désignation", max_length=100)
    station = models.CharField("base / station", max_length=60, blank=True)
    is_quarantine = models.BooleanField("zone de quarantaine", default=False)
    is_bonded = models.BooleanField("magasin sous douane / contrôlé", default=True)

    class Meta:
        ordering = ["code"]
        verbose_name = "emplacement magasin"
        verbose_name_plural = "emplacements magasin"

    def __str__(self):
        return f"{self.code} – {self.name}"


class ReleaseCertificate(TrackedModel):
    """Certificat libératoire : EASA Form 1, FAA 8130-3, CoC fabricant..."""

    TYPES = [
        ("easa_form1", "EASA Form 1"),
        ("faa_8130", "FAA Form 8130-3"),
        ("dual", "Double libération EASA/FAA"),
        ("tcca_one", "TCCA Form One"),
        ("coc", "Certificat de conformité (standard parts / matières)"),
    ]
    STATUSES = [("new", "Neuf"), ("overhauled", "Révisé"), ("repaired", "Réparé"), ("inspected", "Inspecté / testé"), ("modified", "Modifié")]

    cert_type = models.CharField("type", max_length=12, choices=TYPES, default="easa_form1")
    tracking_number = models.CharField("n° de suivi (case 3)", max_length=60)
    issuer = models.CharField("organisme émetteur", max_length=120)
    issuer_approval = models.CharField("n° d'agrément émetteur", max_length=60, blank=True)
    issue_date = models.DateField("date d'émission")
    work_status = models.CharField("statut / travaux (case 11)", max_length=12, choices=STATUSES, default="new")
    part_number = models.ForeignKey("fleet.PartNumber", on_delete=models.PROTECT, verbose_name="P/N", related_name="certificates")
    serial_or_batch = models.CharField("S/N ou n° de lot", max_length=60, blank=True)
    quantity = models.DecimalField("quantité", max_digits=10, decimal_places=2, default=Decimal("1"))
    component = models.ForeignKey("fleet.Component", on_delete=models.PROTECT, null=True, blank=True, related_name="release_certificates", verbose_name="composant")
    stock_item = models.ForeignKey("StockItem", on_delete=models.PROTECT, null=True, blank=True, related_name="certificates", verbose_name="lot de stock")
    remarks = models.TextField("remarques (case 12)", blank=True)
    document = models.FileField("scan du certificat", upload_to="certificats/%Y/", blank=True)
    is_valid = models.BooleanField("accepté en réception", default=True)
    rejection_reason = models.CharField("motif de rejet", max_length=200, blank=True)

    class Meta:
        ordering = ["-issue_date", "-id"]
        verbose_name = "certificat libératoire"
        verbose_name_plural = "certificats libératoires"

    def __str__(self):
        return f"{self.get_cert_type_display()} {self.tracking_number}"

    def clean(self):
        if self.component_id and self.component.part_number_id != self.part_number_id:
            raise ValidationError("Le P/N du certificat ne correspond pas au composant.")
        if self.component_id and self.serial_or_batch and self.serial_or_batch != self.component.serial_number:
            raise ValidationError("Le S/N du certificat ne correspond pas au composant.")


class StockItem(TrackedModel):
    """Lot de pièces non sérialisées (consommables, standard parts, ingrédients)."""

    STATUSES = [("serviceable", "Utilisable"), ("quarantine", "Quarantaine"), ("expired", "Périmé"), ("scrapped", "Rebuté")]

    part_number = models.ForeignKey("fleet.PartNumber", on_delete=models.PROTECT, verbose_name="P/N", related_name="stock_items")
    batch = models.CharField("n° de lot", max_length=60, blank=True)
    location = models.ForeignKey(StoreLocation, on_delete=models.PROTECT, verbose_name="emplacement", related_name="stock_items")
    quantity = models.DecimalField("quantité", max_digits=10, decimal_places=2, default=Decimal("0"))
    min_quantity = models.DecimalField("stock mini", max_digits=10, decimal_places=2, default=Decimal("0"))
    shelf_life_expiry = models.DateField("date de péremption", null=True, blank=True)
    status = models.CharField("statut", max_length=12, choices=STATUSES, default="serviceable")
    status_reason = models.CharField("motif du statut", max_length=200, blank=True)
    received_on = models.DateField("réceptionné le", default=timezone.localdate)
    supplier = models.CharField("fournisseur", max_length=120, blank=True)

    class Meta:
        ordering = ["part_number__pn", "shelf_life_expiry"]
        verbose_name = "lot de stock"
        verbose_name_plural = "stock (lots)"

    def __str__(self):
        return f"{self.part_number.pn} lot {self.batch or '-'} ({self.quantity} {self.part_number.unit})"

    @property
    def is_expired(self):
        return bool(self.shelf_life_expiry and self.shelf_life_expiry < timezone.localdate())

    @property
    def is_below_min(self):
        return self.quantity <= self.min_quantity

    @property
    def is_issuable(self):
        return self.status == "serviceable" and not self.is_expired and self.quantity > 0 and self.certificates.filter(is_valid=True).exists()

    @transaction.atomic
    def issue(self, quantity, task_card=None, note=""):
        quantity = Decimal(str(quantity))
        if not self.is_issuable:
            raise ValidationError("Lot non délivrable (statut, péremption, quantité ou certificat).")
        if quantity <= 0 or quantity > self.quantity:
            raise ValidationError(f"Quantité invalide (disponible : {self.quantity}).")
        self.quantity -= quantity
        self.save()
        return StockMovement.objects.create(stock_item=self, quantity=-quantity, kind="issue", task_card=task_card, note=note)


class StockMovement(TrackedModel):
    KINDS = [("receipt", "Réception"), ("issue", "Sortie"), ("return", "Retour"), ("adjust", "Ajustement inventaire"), ("scrap", "Rebut")]

    stock_item = models.ForeignKey(StockItem, on_delete=models.PROTECT, related_name="movements", verbose_name="lot")
    kind = models.CharField("type", max_length=10, choices=KINDS)
    quantity = models.DecimalField("quantité (+/-)", max_digits=10, decimal_places=2)
    task_card = models.ForeignKey("part145.TaskCard", on_delete=models.PROTECT, null=True, blank=True, related_name="stock_movements", verbose_name="task card")
    note = models.CharField("note", max_length=200, blank=True)
    date = models.DateTimeField("date", default=timezone.now)

    class Meta:
        ordering = ["-date"]
        verbose_name = "mouvement de stock"
        verbose_name_plural = "mouvements de stock"

    def __str__(self):
        return f"{self.get_kind_display()} {self.quantity} {self.stock_item.part_number.pn}"


class PartRequest(TrackedModel):
    STATUSES = [("requested", "Demandée"), ("reserved", "Réservée"), ("issued", "Délivrée"), ("cancelled", "Annulée")]
    PRIORITIES = [("aog", "AOG"), ("urgent", "Urgent"), ("routine", "Normal")]

    number = models.CharField("n° demande", max_length=20, unique=True, editable=False)
    task_card = models.ForeignKey("part145.TaskCard", on_delete=models.PROTECT, related_name="part_requests", verbose_name="task card")
    part_number = models.ForeignKey("fleet.PartNumber", on_delete=models.PROTECT, verbose_name="P/N")
    quantity = models.DecimalField("quantité", max_digits=10, decimal_places=2, default=Decimal("1"))
    priority = models.CharField("priorité", max_length=8, choices=PRIORITIES, default="routine")
    status = models.CharField("statut", max_length=10, choices=STATUSES, default="requested")
    issued_component = models.ForeignKey("fleet.Component", on_delete=models.PROTECT, null=True, blank=True, verbose_name="composant délivré", related_name="part_requests")
    issued_stock = models.ForeignKey(StockItem, on_delete=models.PROTECT, null=True, blank=True, verbose_name="lot délivré", related_name="part_requests")
    note = models.CharField("note", max_length=200, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "demande de pièce"
        verbose_name_plural = "demandes de pièces"

    def __str__(self):
        return f"{self.number} {self.part_number.pn} x{self.quantity}"

    def save(self, *args, **kwargs):
        if not self.number:
            from apps.core.models import Sequence

            self.number = Sequence.next("DP")
        super().save(*args, **kwargs)

    def acceptable_part_numbers(self):
        pns = [self.part_number]
        pns += list(self.part_number.alternates.all())
        return pns

    @transaction.atomic
    def fulfil_with_component(self, component):
        if self.status not in ("requested",):
            raise ValidationError("Demande déjà traitée.")
        if component.part_number not in self.acceptable_part_numbers():
            raise ValidationError("P/N non conforme à la demande (ni interchangeable).")
        if component.status != "serviceable":
            raise ValidationError("Le composant n'est pas utilisable.")
        if not component.has_valid_certificate:
            raise ValidationError("Composant sans certificat libératoire valide.")
        if component.is_life_expired:
            raise ValidationError("Composant en butée de vie / TBO.")
        component.status = "reserved"
        component.reserved_for = self.task_card
        component.save()
        self.issued_component = component
        self.status = "issued"
        self.save()

    @transaction.atomic
    def fulfil_with_stock(self, stock_item):
        if self.status not in ("requested",):
            raise ValidationError("Demande déjà traitée.")
        if stock_item.part_number not in self.acceptable_part_numbers():
            raise ValidationError("P/N non conforme à la demande.")
        stock_item.issue(self.quantity, task_card=self.task_card, note=self.number)
        self.issued_stock = stock_item
        self.status = "issued"
        self.save()


class Tool(TrackedModel):
    STATUSES = [("available", "Disponible"), ("checked_out", "Sorti"), ("calibration", "En étalonnage"), ("unserviceable", "Hors service")]

    reference = models.CharField("référence interne", max_length=40, unique=True)
    description = models.CharField("désignation", max_length=150)
    part_number = models.CharField("P/N outillage", max_length=60, blank=True)
    serial_number = models.CharField("S/N", max_length=60, blank=True)
    location = models.ForeignKey(StoreLocation, on_delete=models.PROTECT, null=True, blank=True, verbose_name="emplacement")
    status = models.CharField("statut", max_length=14, choices=STATUSES, default="available")
    calibration_required = models.BooleanField("étalonnage requis", default=True)
    calibration_interval_days = models.PositiveIntegerField("périodicité d'étalonnage (jours)", null=True, blank=True)
    last_calibration = models.DateField("dernier étalonnage", null=True, blank=True)
    checked_out_to = models.ForeignKey("part145.TaskCard", on_delete=models.PROTECT, null=True, blank=True, related_name="tools_out", verbose_name="sorti pour")
    checked_out_by = models.ForeignKey("part145.Staff", on_delete=models.PROTECT, null=True, blank=True, related_name="+", verbose_name="sorti par")

    class Meta:
        ordering = ["reference"]
        verbose_name = "outillage"
        verbose_name_plural = "outillages"

    def __str__(self):
        return f"{self.reference} – {self.description}"

    def get_absolute_url(self):
        return reverse("logistics:tool_detail", args=[self.pk])

    @property
    def calibration_due(self):
        if not self.calibration_required or not self.calibration_interval_days or not self.last_calibration:
            return None
        return self.last_calibration + timedelta(days=self.calibration_interval_days)

    @property
    def calibration_ok(self):
        if not self.calibration_required:
            return True
        due = self.calibration_due
        return bool(due and due >= timezone.localdate())

    @transaction.atomic
    def check_out(self, task_card, staff):
        if self.status != "available":
            raise ValidationError(f"Outillage {self.reference} non disponible ({self.get_status_display()}).")
        if not self.calibration_ok:
            raise ValidationError(f"Outillage {self.reference} : étalonnage échu ou non renseigné, sortie interdite.")
        self.status = "checked_out"
        self.checked_out_to = task_card
        self.checked_out_by = staff
        self.save()
        ToolUsage.objects.create(tool=self, task_card=task_card, staff=staff, calibration_due=self.calibration_due)

    @transaction.atomic
    def check_in(self):
        usage = self.usages.filter(returned_at__isnull=True).first()
        if usage:
            usage.returned_at = timezone.now()
            usage.save()
        self.status = "available"
        self.checked_out_to = None
        self.checked_out_by = None
        self.save()


class ToolUsage(TrackedModel):
    """Traçabilité : quel outil (et dans quel état d'étalonnage) a servi sur quelle task card."""

    tool = models.ForeignKey(Tool, on_delete=models.PROTECT, related_name="usages", verbose_name="outillage")
    task_card = models.ForeignKey("part145.TaskCard", on_delete=models.PROTECT, related_name="tool_usages", verbose_name="task card")
    staff = models.ForeignKey("part145.Staff", on_delete=models.PROTECT, null=True, blank=True, verbose_name="utilisateur")
    checked_out_at = models.DateTimeField("sorti le", default=timezone.now)
    returned_at = models.DateTimeField("rendu le", null=True, blank=True)
    calibration_due = models.DateField("étalonnage valide jusqu'au", null=True, blank=True)

    class Meta:
        ordering = ["-checked_out_at"]
        verbose_name = "utilisation d'outillage"
        verbose_name_plural = "utilisations d'outillage"

    def __str__(self):
        return f"{self.tool.reference} → {self.task_card.number}"


class ToolCalibration(TrackedModel):
    tool = models.ForeignKey(Tool, on_delete=models.PROTECT, related_name="calibrations", verbose_name="outillage")
    date = models.DateField("date d'étalonnage")
    provider = models.CharField("laboratoire", max_length=120)
    certificate_ref = models.CharField("n° certificat d'étalonnage", max_length=60)
    result = models.CharField("résultat", max_length=10, choices=[("pass", "Conforme"), ("fail", "Non conforme")], default="pass")

    class Meta:
        ordering = ["-date"]
        verbose_name = "étalonnage"
        verbose_name_plural = "étalonnages"

    def __str__(self):
        return f"{self.tool.reference} {self.date:%d/%m/%Y}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        tool = self.tool
        if self.result == "pass" and (not tool.last_calibration or self.date >= tool.last_calibration):
            tool.last_calibration = self.date
            if tool.status == "calibration":
                tool.status = "available"
            tool.save()
        elif self.result == "fail":
            tool.status = "unserviceable"
            tool.save()
