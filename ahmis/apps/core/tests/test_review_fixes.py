"""Corrections issues des revues EASA et cybersécurité de la fusion."""
import json
import tempfile
from datetime import timedelta
from decimal import Decimal as D

from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.camo.models import ModificationRepair
from apps.core.identity import verify_signature_secret
from apps.core.models import AuditLog
from apps.core.tests.factories import PASSWORD, make_world, today
from apps.core.uploads import FileContentValidator
from apps.logistics.models import PurchaseOrder, PurchaseOrderLine, Supplier
from apps.logistics.purchasing import receive_line, send_order
from apps.part145 import services as p145
from apps.part145.models import Defect, WorkPackage
from apps.quality.models import AuditFinding, ControlledDocument, DocumentRevision, InternalAudit
from apps.quality.services import approve_revision
from apps.safety.models import OccurrenceReport

MEDIA = tempfile.mkdtemp(prefix="ahmis-test-media-")


class EasaFixTests(TestCase):
    def setUp(self):
        self.w = make_world()

    def test_crs_blocked_by_expired_deferral(self):
        d = Defect.objects.create(aircraft=self.w["ac"], reported_by="Pilote", description="Feu INOP")
        p145.defer_defect(d, self.w["u_b1"], "MEL 33", "C")
        wp = WorkPackage.objects.create(aircraft=self.w["ac"], title="Ligne", planned_start=today(), planned_end=today())
        self.assertFalse(any(d.number in p for p in wp.crs_blockers()))
        Defect.objects.filter(pk=d.pk).update(deferral_limit_date=today() - timedelta(days=1))
        self.assertTrue(any(d.number in p for p in wp.crs_blockers()))

    def test_moe_always_needs_authority(self):
        doc = ControlledDocument.objects.create(reference="MOE", title="MOE", doc_type="moe", authority_approval=False)
        self.assertTrue(doc.authority_approval)

    @override_settings(MEDIA_ROOT=MEDIA)
    def test_revision_needs_file(self):
        doc = ControlledDocument.objects.create(reference="P1", title="P")
        rev = DocumentRevision.objects.create(document=doc, revision="A", change_summary="x")
        with self.assertRaises(ValidationError):
            approve_revision(rev, self.w["u_camo"])

    def test_finding_due_date_bounded(self):
        a = InternalAudit.objects.create(title="A", scope="part145", area="x", planned_on=today(), auditor=self.w["u_camo"])
        f = AuditFinding(audit=a, level="level1", requirement="x", description="x", due_date=today() + timedelta(days=90))
        with self.assertRaises(ValidationError):
            f.full_clean()

    def test_reported_audit_locked(self):
        a = InternalAudit.objects.create(title="A", scope="part145", area="x", planned_on=today(), auditor=self.w["u_camo"],
                                         auditor_independent=True, status="reported", summary="S", performed_on=today())
        a.summary = "Autre synthèse"
        with self.assertRaises(ValidationError):
            a.full_clean()
        a.refresh_from_db()
        a.status, a.closed_on = "closed", today()
        a.full_clean()
        a.save()
        a.title = "Changé"
        with self.assertRaises(ValidationError):
            a.full_clean()

    def test_embodied_modification_locked(self):
        m = ModificationRepair.objects.create(aircraft=self.w["ac"], title="Treuil", classification="major", approval_basis="stc",
                                              approval_reference="STC-1", part21_status="approved", design_holder="DOA",
                                              part21_requested_on=today() - timedelta(days=5), part21_approved_on=today() - timedelta(days=2),
                                              part21_reference="STC-1", status="embodied", embodied_on=today(), ica_none=True)
        m.classification, m.approval_basis = "minor", "other"
        with self.assertRaises(ValidationError):
            m.full_clean()

    def test_receipt_refused_when_supplier_withdrawn(self):
        sup = Supplier.objects.create(name="F", approved=True, evaluated_on=today())
        po = PurchaseOrder.objects.create(supplier=sup)
        from apps.fleet.models import PartNumber

        line = PurchaseOrderLine.objects.create(order=po, part_number=PartNumber.objects.create(pn="C1", description="c", category="consumable"),
                                                quantity=D("2"))
        send_order(po)
        Supplier.objects.filter(pk=sup.pk).update(approved=False)
        with self.assertRaises(ValidationError):
            receive_line(line, D("1"))

    def test_negative_quantity_refused(self):
        sup = Supplier.objects.create(name="F2")
        po = PurchaseOrder.objects.create(supplier=sup)
        line = PurchaseOrderLine(order=po, part_number=self.w["pn_engine"], quantity=D("-1"))
        with self.assertRaises(ValidationError):
            line.full_clean()


@override_settings(MEDIA_ROOT=MEDIA)
class CyberFixTests(TestCase):
    def setUp(self):
        self.w = make_world()

    def test_upload_content_must_match_extension(self):
        v = FileContentValidator()
        v(SimpleUploadedFile("ok.pdf", b"%PDF-1.4 x"))
        with self.assertRaises(ValidationError):
            v(SimpleUploadedFile("scan.pdf", b"<html><script>alert(1)</script>"))
        from apps.logistics.models import ReleaseCertificate

        field = ReleaseCertificate._meta.get_field("document")
        with self.assertRaises(ValidationError):
            field.run_validators(SimpleUploadedFile("scan.html", b"<script>alert(1)</script>"))

    def test_media_requires_object_permission_and_is_sandboxed(self):
        import os
        from django.conf import settings

        os.makedirs(os.path.join(settings.MEDIA_ROOT, "documents", "2026"), exist_ok=True)
        with open(os.path.join(settings.MEDIA_ROOT, "documents", "2026", "rev.pdf"), "wb") as f:
            f.write(b"%PDF-1.4")
        from django.contrib.auth import get_user_model

        nobody = get_user_model().objects.create_user("nobody", password=PASSWORD)
        self.client.force_login(nobody)
        self.assertEqual(self.client.get("/media/documents/2026/rev.pdf").status_code, 403)
        self.assertEqual(self.client.get("/media/TRANSFERTS/x.zip").status_code, 404)
        self.assertEqual(self.client.get("/media/TRANSF~1/x.zip").status_code, 404)
        self.client.force_login(self.w["u_camo"])
        r = self.client.get("/media/documents/2026/rev.pdf")
        self.assertEqual(r.status_code, 200)
        self.assertIn("sandbox", r["Content-Security-Policy"])

    def test_login_locked_after_five_failures(self):
        url = reverse("login")
        for _ in range(5):
            self.client.post(url, {"username": "camo", "password": "faux"})
        r = self.client.post(url, {"username": "camo", "password": PASSWORD})
        self.assertContains(r, "Trop de tentatives")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_signature_password_locked_after_five_failures(self):
        u = self.w["u_camo"]
        for _ in range(5):
            self.assertFalse(verify_signature_secret(u, "faux"))
        self.assertFalse(verify_signature_secret(u, PASSWORD))

    def test_confidential_reporter_masked_in_audit_log(self):
        from django.utils import timezone

        r = OccurrenceReport.objects.create(title="Erreur", category="maintenance_error", severity="low", phase="maintenance",
                                            occurred_at=timezone.now(), aware_at=timezone.now(), description="x",
                                            reporter_name="Jean SECRET", confidential=True)
        log = AuditLog.objects.filter(object_id=str(r.pk), content_type__model="occurrencereport").first()
        self.assertNotIn("SECRET", log.changes)
        self.assertIn("[confidentiel]", json.loads(log.changes)["déclarant"]["new"])

    def test_pin_change_requires_current_secret(self):
        from apps.core.models import SignaturePin

        u = self.w["u_camo"]
        pin = SignaturePin(user=u)
        pin.set_pin("ancien1")
        pin.save()
        self.client.post(reverse("login"), {"username": "camo", "password": PASSWORD})
        self.client.post(reverse("my_account"), {"pin": "nouveau9", "pin_confirm": "nouveau9", "current": "mauvais"})
        pin.refresh_from_db()
        self.assertTrue(pin.check_pin("ancien1"))
        self.client.post(reverse("my_account"), {"pin": "nouveau9", "pin_confirm": "nouveau9", "current": "ancien1"})
        pin.refresh_from_db()
        self.assertTrue(pin.check_pin("nouveau9"))

    def test_csp_header_on_pages(self):
        self.client.force_login(self.w["u_camo"])
        self.assertIn("frame-ancestors 'none'", self.client.get("/")["Content-Security-Policy"])
