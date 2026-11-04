from decimal import Decimal as D

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.core.tests.factories import make_world, today
from apps.fleet.models import PartNumber
from apps.logistics.models import PurchaseOrder, PurchaseOrderLine, ReleaseCertificate, Supplier
from apps.logistics.purchasing import cancel_order, receive_line, send_order


class PurchasingTests(TestCase):
    def setUp(self):
        self.w = make_world()
        self.sup = Supplier.objects.create(name="Fournisseur", approved=True)
        self.po = PurchaseOrder.objects.create(supplier=self.sup)
        self.consumable = PartNumber.objects.create(pn="P-OIL", description="Huile", category="consumable")
        self.line = PurchaseOrderLine.objects.create(order=self.po, part_number=self.w["pn_engine"], quantity=D("2"))

    def cert(self, pn=None, qty=D("1"), **kw):
        return ReleaseCertificate.objects.create(cert_type=kw.pop("cert_type", "easa_form1"), tracking_number="T", issuer="X",
                                                 issue_date=today(), part_number=pn or self.w["pn_engine"], quantity=qty, **kw)

    def test_unapproved_supplier_cannot_be_ordered(self):
        self.sup.approved = False
        self.sup.save()
        with self.assertRaises(ValidationError):
            send_order(self.po)

    def test_order_without_lines_refused(self):
        po = PurchaseOrder.objects.create(supplier=self.sup)
        with self.assertRaises(ValidationError):
            send_order(po)

    def test_receipt_rules(self):
        with self.assertRaises(ValidationError):  # commande non émise
            receive_line(self.line, D("1"), self.cert())
        send_order(self.po)
        with self.assertRaises(ValidationError):  # élément sans certificat
            receive_line(self.line, D("1"))
        with self.assertRaises(ValidationError):  # autre P/N
            receive_line(self.line, D("1"), self.cert(pn=self.w["pn_llp"]))
        with self.assertRaises(ValidationError):  # CoC insuffisant
            receive_line(self.line, D("1"), self.cert(cert_type="coc"))
        with self.assertRaises(ValidationError):  # certificat rejeté
            receive_line(self.line, D("1"), self.cert(is_valid=False))
        with self.assertRaises(ValidationError):  # au-delà de la commande
            receive_line(self.line, D("3"), self.cert(qty=D("3")))
        c = self.cert(qty=D("1"))
        receive_line(self.line, D("1"), c)
        with self.assertRaises(ValidationError):  # certificat déjà épuisé
            receive_line(self.line, D("1"), c)
        self.po.refresh_from_db()
        self.assertEqual(self.po.status, "partial")
        receive_line(self.line, D("1"), self.cert())
        self.po.refresh_from_db()
        self.assertEqual(self.po.status, "received")

    def test_cancel_blocked_after_receipt(self):
        send_order(self.po)
        receive_line(self.line, D("1"), self.cert())
        with self.assertRaises(ValidationError):
            cancel_order(self.po)

    def test_consumable_without_certificate(self):
        line = PurchaseOrderLine.objects.create(order=self.po, part_number=self.consumable, quantity=D("5"))
        send_order(self.po)
        receive_line(line, D("5"))
        line.refresh_from_db()
        self.assertEqual(line.received_quantity, D("5"))
        with self.assertRaises(ValidationError):
            receive_line(line, D("0"))
