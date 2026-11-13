from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone

from apps.core.models import TrackedModel
from apps.core.uploads import scan_validators
from django.utils.translation import gettext, gettext_lazy


class StoreLocation(TrackedModel):
    code = models.CharField(gettext_lazy("code"), max_length=30, unique=True)
    name = models.CharField(gettext_lazy("désignation"), max_length=100)
    station = models.CharField(gettext_lazy("base / station"), max_length=60, blank=True)
    is_quarantine = models.BooleanField(gettext_lazy("zone de quarantaine"), default=False)
    is_bonded = models.BooleanField(gettext_lazy("magasin sous douane / contrôlé"), default=True)

    class Meta:
        ordering = ["code"]
        verbose_name = gettext_lazy("emplacement magasin")
        verbose_name_plural = gettext_lazy("emplacements magasin")

    def __str__(self):
        return f"{self.code} – {self.name}"


class ReleaseCertificate(TrackedModel):
    """Certificat libératoire : EASA Form 1, FAA 8130-3, CoC fabricant..."""

    TYPES = [
        ("easa_form1", gettext_lazy("EASA Form 1")),
        ("faa_8130", gettext_lazy("FAA Form 8130-3")),
        ("dual", gettext_lazy("Double libération EASA/FAA")),
        ("tcca_one", gettext_lazy("TCCA Form One")),
        ("coc", gettext_lazy("Certificat de conformité (standard parts / matières)")),
    ]
    STATUSES = [("new", gettext_lazy("Neuf")), ("overhauled", gettext_lazy("Révisé")), ("repaired", gettext_lazy("Réparé")), ("inspected", gettext_lazy("Inspecté / testé")), ("modified", gettext_lazy("Modifié"))]

    cert_type = models.CharField(gettext_lazy("type"), max_length=12, choices=TYPES, default="easa_form1")
    tracking_number = models.CharField(gettext_lazy("n° de suivi (case 3)"), max_length=60)
    issuer = models.CharField(gettext_lazy("organisme émetteur"), max_length=120)
    issuer_approval = models.CharField(gettext_lazy("n° d'agrément émetteur"), max_length=60, blank=True)
    issue_date = models.DateField(gettext_lazy("date d'émission"))
    work_status = models.CharField(gettext_lazy("statut / travaux (case 11)"), max_length=12, choices=STATUSES, default="new")
    part_number = models.ForeignKey("fleet.PartNumber", on_delete=models.PROTECT, verbose_name=gettext_lazy("P/N"), related_name="certificates")
    serial_or_batch = models.CharField(gettext_lazy("S/N ou n° de lot"), max_length=60, blank=True)
    quantity = models.DecimalField(gettext_lazy("quantité"), max_digits=10, decimal_places=2, default=Decimal("1"))
    component = models.ForeignKey("fleet.Component", on_delete=models.PROTECT, null=True, blank=True, related_name="release_certificates", verbose_name=gettext_lazy("composant"))
    stock_item = models.ForeignKey("StockItem", on_delete=models.PROTECT, null=True, blank=True, related_name="certificates", verbose_name=gettext_lazy("lot de stock"))
    remarks = models.TextField(gettext_lazy("remarques (case 12)"), blank=True)
    document = models.FileField(gettext_lazy("scan du certificat"), upload_to="certificats/%Y/", blank=True, validators=scan_validators())
    is_valid = models.BooleanField(gettext_lazy("accepté en réception"), default=True)
    rejection_reason = models.CharField(gettext_lazy("motif de rejet"), max_length=200, blank=True)

    class Meta:
        ordering = ["-issue_date", "-id"]
        verbose_name = gettext_lazy("certificat libératoire")
        verbose_name_plural = gettext_lazy("certificats libératoires")

    def __str__(self):
        return f"{self.get_cert_type_display()} {self.tracking_number}"

    def clean(self):
        if self.component_id and self.component.part_number_id != self.part_number_id:
            raise ValidationError(gettext("Le P/N du certificat ne correspond pas au composant."))
        if self.component_id and self.serial_or_batch and self.serial_or_batch != self.component.serial_number:
            raise ValidationError(gettext("Le S/N du certificat ne correspond pas au composant."))


class StockItem(TrackedModel):
    """Lot de pièces non sérialisées (consommables, standard parts, ingrédients)."""

    STATUSES = [("serviceable", gettext_lazy("Utilisable")), ("quarantine", gettext_lazy("Quarantaine")), ("expired", gettext_lazy("Périmé")), ("scrapped", gettext_lazy("Rebuté"))]

    part_number = models.ForeignKey("fleet.PartNumber", on_delete=models.PROTECT, verbose_name=gettext_lazy("P/N"), related_name="stock_items")
    batch = models.CharField(gettext_lazy("n° de lot"), max_length=60, blank=True)
    location = models.ForeignKey(StoreLocation, on_delete=models.PROTECT, verbose_name=gettext_lazy("emplacement"), related_name="stock_items")
    quantity = models.DecimalField(gettext_lazy("quantité"), max_digits=10, decimal_places=2, default=Decimal("0"))
    min_quantity = models.DecimalField(gettext_lazy("stock mini"), max_digits=10, decimal_places=2, default=Decimal("0"))
    shelf_life_expiry = models.DateField(gettext_lazy("date de péremption"), null=True, blank=True)
    status = models.CharField(gettext_lazy("statut"), max_length=12, choices=STATUSES, default="serviceable")
    status_reason = models.CharField(gettext_lazy("motif du statut"), max_length=200, blank=True)
    received_on = models.DateField(gettext_lazy("réceptionné le"), default=timezone.localdate)
    supplier = models.CharField(gettext_lazy("fournisseur"), max_length=120, blank=True)

    class Meta:
        ordering = ["part_number__pn", "shelf_life_expiry"]
        verbose_name = gettext_lazy("lot de stock")
        verbose_name_plural = gettext_lazy("stock (lots)")

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
            raise ValidationError(gettext("Lot non délivrable (statut, péremption, quantité ou certificat)."))
        if quantity <= 0 or quantity > self.quantity:
            raise ValidationError(gettext("Quantité invalide (disponible : {quantity}).").format(quantity=self.quantity))
        self.quantity -= quantity
        self.save()
        return StockMovement.objects.create(stock_item=self, quantity=-quantity, kind="issue", task_card=task_card, note=note)


class StockMovement(TrackedModel):
    KINDS = [("receipt", gettext_lazy("Réception")), ("issue", gettext_lazy("Sortie")), ("return", gettext_lazy("Retour")), ("adjust", gettext_lazy("Ajustement inventaire")), ("scrap", gettext_lazy("Rebut"))]

    stock_item = models.ForeignKey(StockItem, on_delete=models.PROTECT, related_name="movements", verbose_name=gettext_lazy("lot"))
    kind = models.CharField(gettext_lazy("type"), max_length=10, choices=KINDS)
    quantity = models.DecimalField(gettext_lazy("quantité (+/-)"), max_digits=10, decimal_places=2)
    task_card = models.ForeignKey("part145.TaskCard", on_delete=models.PROTECT, null=True, blank=True, related_name="stock_movements", verbose_name=gettext_lazy("task card"))
    note = models.CharField(gettext_lazy("note"), max_length=200, blank=True)
    date = models.DateTimeField(gettext_lazy("date"), default=timezone.now)

    class Meta:
        ordering = ["-date"]
        verbose_name = gettext_lazy("mouvement de stock")
        verbose_name_plural = gettext_lazy("mouvements de stock")

    def __str__(self):
        return f"{self.get_kind_display()} {self.quantity} {self.stock_item.part_number.pn}"


class PartRequest(TrackedModel):
    STATUSES = [("requested", gettext_lazy("Demandée")), ("reserved", gettext_lazy("Réservée")), ("issued", gettext_lazy("Délivrée")), ("cancelled", gettext_lazy("Annulée"))]
    PRIORITIES = [("aog", "AOG"), ("urgent", gettext_lazy("Urgent")), ("routine", gettext_lazy("Normal"))]

    number = models.CharField(gettext_lazy("n° demande"), max_length=20, unique=True, editable=False)
    task_card = models.ForeignKey("part145.TaskCard", on_delete=models.PROTECT, related_name="part_requests", verbose_name=gettext_lazy("task card"))
    part_number = models.ForeignKey("fleet.PartNumber", on_delete=models.PROTECT, verbose_name=gettext_lazy("P/N"))
    quantity = models.DecimalField(gettext_lazy("quantité"), max_digits=10, decimal_places=2, default=Decimal("1"))
    priority = models.CharField(gettext_lazy("priorité"), max_length=8, choices=PRIORITIES, default="routine")
    status = models.CharField(gettext_lazy("statut"), max_length=10, choices=STATUSES, default="requested")
    issued_component = models.ForeignKey("fleet.Component", on_delete=models.PROTECT, null=True, blank=True, verbose_name=gettext_lazy("composant délivré"), related_name="part_requests")
    issued_stock = models.ForeignKey(StockItem, on_delete=models.PROTECT, null=True, blank=True, verbose_name=gettext_lazy("lot délivré"), related_name="part_requests")
    note = models.CharField(gettext_lazy("note"), max_length=200, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = gettext_lazy("demande de pièce")
        verbose_name_plural = gettext_lazy("demandes de pièces")

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
            raise ValidationError(gettext("Demande déjà traitée."))
        if component.part_number not in self.acceptable_part_numbers():
            raise ValidationError(gettext("P/N non conforme à la demande (ni interchangeable)."))
        if component.status != "serviceable":
            raise ValidationError(gettext("Le composant n'est pas utilisable."))
        if not component.has_valid_certificate:
            raise ValidationError(gettext("Composant sans certificat libératoire valide."))
        if component.is_life_expired:
            raise ValidationError(gettext("Composant en butée de vie / TBO."))
        component.status = "reserved"
        component.reserved_for = self.task_card
        component.save()
        self.issued_component = component
        self.status = "issued"
        self.save()

    @transaction.atomic
    def fulfil_with_stock(self, stock_item):
        if self.status not in ("requested",):
            raise ValidationError(gettext("Demande déjà traitée."))
        if stock_item.part_number not in self.acceptable_part_numbers():
            raise ValidationError(gettext("P/N non conforme à la demande."))
        stock_item.issue(self.quantity, task_card=self.task_card, note=self.number)
        self.issued_stock = stock_item
        self.status = "issued"
        self.save()


class Tool(TrackedModel):
    STATUSES = [("available", gettext_lazy("Disponible")), ("checked_out", gettext_lazy("Sorti")), ("calibration", gettext_lazy("En étalonnage")), ("unserviceable", gettext_lazy("Hors service"))]

    reference = models.CharField(gettext_lazy("référence interne"), max_length=40, unique=True)
    description = models.CharField(gettext_lazy("désignation"), max_length=150)
    part_number = models.CharField(gettext_lazy("P/N outillage"), max_length=60, blank=True)
    serial_number = models.CharField(gettext_lazy("S/N"), max_length=60, blank=True)
    location = models.ForeignKey(StoreLocation, on_delete=models.PROTECT, null=True, blank=True, verbose_name=gettext_lazy("emplacement"))
    status = models.CharField(gettext_lazy("statut"), max_length=14, choices=STATUSES, default="available")
    calibration_required = models.BooleanField(gettext_lazy("étalonnage requis"), default=True)
    calibration_interval_days = models.PositiveIntegerField(gettext_lazy("périodicité d'étalonnage (jours)"), null=True, blank=True)
    last_calibration = models.DateField(gettext_lazy("dernier étalonnage"), null=True, blank=True)
    checked_out_to = models.ForeignKey("part145.TaskCard", on_delete=models.PROTECT, null=True, blank=True, related_name="tools_out", verbose_name=gettext_lazy("sorti pour"))
    checked_out_by = models.ForeignKey("part145.Staff", on_delete=models.PROTECT, null=True, blank=True, related_name="+", verbose_name=gettext_lazy("sorti par"))

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
            raise ValidationError(gettext("Outillage {reference} non disponible ({get_status_display}).").format(reference=self.reference, get_status_display=self.get_status_display()))
        if not self.calibration_ok:
            raise ValidationError(gettext("Outillage {reference} : étalonnage échu ou non renseigné, sortie interdite.").format(reference=self.reference))
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

    tool = models.ForeignKey(Tool, on_delete=models.PROTECT, related_name="usages", verbose_name=gettext_lazy("outillage"))
    task_card = models.ForeignKey("part145.TaskCard", on_delete=models.PROTECT, related_name="tool_usages", verbose_name=gettext_lazy("task card"))
    staff = models.ForeignKey("part145.Staff", on_delete=models.PROTECT, null=True, blank=True, verbose_name=gettext_lazy("utilisateur"))
    checked_out_at = models.DateTimeField(gettext_lazy("sorti le"), default=timezone.now)
    returned_at = models.DateTimeField(gettext_lazy("rendu le"), null=True, blank=True)
    calibration_due = models.DateField(gettext_lazy("étalonnage valide jusqu'au"), null=True, blank=True)

    class Meta:
        ordering = ["-checked_out_at"]
        verbose_name = gettext_lazy("utilisation d'outillage")
        verbose_name_plural = gettext_lazy("utilisations d'outillage")

    def __str__(self):
        return f"{self.tool.reference} → {self.task_card.number}"


class ToolCalibration(TrackedModel):
    tool = models.ForeignKey(Tool, on_delete=models.PROTECT, related_name="calibrations", verbose_name=gettext_lazy("outillage"))
    date = models.DateField(gettext_lazy("date d'étalonnage"))
    provider = models.CharField(gettext_lazy("laboratoire"), max_length=120)
    certificate_ref = models.CharField(gettext_lazy("n° certificat d'étalonnage"), max_length=60)
    result = models.CharField(gettext_lazy("résultat"), max_length=10, choices=[("pass", gettext_lazy("Conforme")), ("fail", gettext_lazy("Non conforme"))], default="pass")

    class Meta:
        ordering = ["-date"]
        verbose_name = gettext_lazy("étalonnage")
        verbose_name_plural = gettext_lazy("étalonnages")

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


# ---------------------------------------------------------------- Achats (fournisseurs et commandes)
class Supplier(TrackedModel):
    """Fournisseur évalué : seules les commandes à un fournisseur accepté peuvent être émises (145.A.42(a))."""

    KINDS = [("part145", gettext_lazy("Organisme Part-145")), ("part21g", gettext_lazy("Organisme de production Part-21 G")),
             ("distributor", gettext_lazy("Distributeur")), ("other", gettext_lazy("Autre"))]

    name = models.CharField(gettext_lazy("raison sociale"), max_length=150, unique=True)
    kind = models.CharField(gettext_lazy("type"), max_length=12, choices=KINDS, default="distributor")
    approval_reference = models.CharField(gettext_lazy("n° d'agrément"), max_length=60, blank=True, help_text=gettext_lazy("ex. FR.145.0123, FR.21G.0045"))
    approved = models.BooleanField(gettext_lazy("fournisseur accepté"), default=False)
    evaluated_on = models.DateField(gettext_lazy("évalué le"), null=True, blank=True)
    contact = models.CharField(gettext_lazy("contact"), max_length=150, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "fournisseur"
        verbose_name_plural = "fournisseurs"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("logistics:supplier_update", args=[self.pk])

    def clean(self):
        if self.approved and not self.evaluated_on:
            raise ValidationError({"evaluated_on": gettext("Indiquez la date d'évaluation du fournisseur accepté.")})
        if self.approved and self.kind in ("part145", "part21g") and not self.approval_reference.strip():
            raise ValidationError({"approval_reference": gettext("Indiquez le n° d'agrément de l'organisme.")})


class PurchaseOrder(TrackedModel):
    STATUSES = [("draft", gettext_lazy("Brouillon")), ("sent", gettext_lazy("Émise")), ("partial", gettext_lazy("Reçue partiellement")), ("received", gettext_lazy("Reçue")),
                ("cancelled", gettext_lazy("Annulée"))]

    number = models.CharField(gettext_lazy("n° de commande"), max_length=20, unique=True, editable=False)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="orders", verbose_name=gettext_lazy("fournisseur"))
    ordered_on = models.DateField(gettext_lazy("date de commande"), null=True, blank=True)
    expected_on = models.DateField(gettext_lazy("livraison prévue le"), null=True, blank=True)
    status = models.CharField(gettext_lazy("statut"), max_length=10, choices=STATUSES, default="draft", editable=False)
    notes = models.TextField(gettext_lazy("observations"), blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = gettext_lazy("commande d'achat")
        verbose_name_plural = gettext_lazy("commandes d'achat")

    def __str__(self):
        return f"{self.number} {self.supplier}"

    def get_absolute_url(self):
        return reverse("logistics:po_detail", args=[self.pk])

    @property
    def late(self):
        return self.status in ("sent", "partial") and self.expected_on and self.expected_on < timezone.localdate()

    def refresh_status(self):
        lines = list(self.lines.all())
        if self.status in ("draft", "cancelled") or not lines:
            return
        if all(line.received_quantity >= line.quantity for line in lines):
            self.status = "received"
        elif any(line.received_quantity > 0 for line in lines):
            self.status = "partial"
        else:
            self.status = "sent"
        self.save(update_fields=["status", "updated_at"])

    def save(self, *args, **kwargs):
        if not self.number:
            from apps.core.models import Sequence

            self.number = Sequence.next("PO")
        super().save(*args, **kwargs)


class PurchaseOrderLine(TrackedModel):
    order = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT, related_name="lines", verbose_name=gettext_lazy("commande"))
    part_number = models.ForeignKey("fleet.PartNumber", on_delete=models.PROTECT, verbose_name=gettext_lazy("P/N"))
    quantity = models.DecimalField(gettext_lazy("quantité commandée"), max_digits=10, decimal_places=2, default=Decimal("1"),
                                   validators=[MinValueValidator(Decimal("0.01"))])
    received_quantity = models.DecimalField(gettext_lazy("quantité reçue"), max_digits=10, decimal_places=2, default=Decimal("0"), editable=False)
    part_request = models.ForeignKey(PartRequest, on_delete=models.PROTECT, null=True, blank=True, related_name="po_lines",
                                     verbose_name=gettext_lazy("demande de pièce liée"))

    class Meta:
        ordering = ["order", "pk"]
        verbose_name = gettext_lazy("ligne de commande")
        verbose_name_plural = gettext_lazy("lignes de commande")

    def __str__(self):
        return f"{self.order.number} – {self.part_number.pn} × {self.quantity}"

    def get_absolute_url(self):
        return self.order.get_absolute_url()

    @property
    def remaining(self):
        return max(self.quantity - self.received_quantity, Decimal("0"))

    def clean(self):
        if self.quantity is not None and self.quantity <= 0:
            raise ValidationError({"quantity": gettext("La quantité doit être positive.")})
        if self.part_request_id and self.part_request.part_number_id != self.part_number_id:
            raise ValidationError({"part_request": gettext("La demande liée porte sur un autre P/N.")})


class PurchaseReceipt(TrackedModel):
    """Réception d'une ligne de commande : rattachée au certificat libératoire contrôlé en réception."""

    line = models.ForeignKey(PurchaseOrderLine, on_delete=models.PROTECT, related_name="receipts", verbose_name=gettext_lazy("ligne"))
    quantity = models.DecimalField(gettext_lazy("quantité reçue"), max_digits=10, decimal_places=2)
    certificate = models.ForeignKey(ReleaseCertificate, on_delete=models.PROTECT, null=True, blank=True, related_name="po_receipts",
                                    verbose_name=gettext_lazy("certificat libératoire"))
    received_on = models.DateField(gettext_lazy("reçu le"), default=timezone.localdate)

    class Meta:
        ordering = ["-received_on", "-pk"]
        verbose_name = gettext_lazy("réception sur commande")
        verbose_name_plural = gettext_lazy("réceptions sur commande")

    def __str__(self):
        return f"{self.line} : {self.quantity}"
