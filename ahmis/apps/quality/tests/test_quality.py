from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.core.middleware import set_current_user
from apps.core.models import SignatureRecord
from apps.core.tests.factories import PASSWORD, make_world, today
from apps.quality import services
from apps.quality.models import AuditFinding, ControlledDocument, DocumentRevision, InternalAudit


class AuditTests(TestCase):
    def setUp(self):
        self.w = make_world()
        self.audit = InternalAudit.objects.create(title="Magasin", scope="part145", area="Magasin", planned_on=today(),
                                                  auditor=self.w["u_camo"])

    def test_numbering_and_default_due_dates(self):
        self.assertTrue(self.audit.number.startswith("AUD"))
        f1 = AuditFinding.objects.create(audit=self.audit, level="level1", requirement="145.A.42", description="x")
        f2 = AuditFinding.objects.create(audit=self.audit, level="level2", requirement="145.A.42", description="x")
        f3 = AuditFinding.objects.create(audit=self.audit, level="observation", requirement="MOE", description="x")
        self.assertEqual(f1.due_date, today())
        self.assertEqual(f2.due_date, today() + timedelta(days=90))
        self.assertEqual(f3.due_date, today() + timedelta(days=30))

    def test_auditor_must_be_independent_to_start(self):
        self.audit.status = "in_progress"
        with self.assertRaises(ValidationError) as cm:
            self.audit.full_clean()
        self.assertIn("auditor_independent", cm.exception.message_dict)

    def test_report_requires_summary_and_date(self):
        self.audit.auditor_independent = True
        self.audit.status = "reported"
        with self.assertRaises(ValidationError) as cm:
            self.audit.full_clean()
        self.assertIn("summary", cm.exception.message_dict)
        self.assertIn("performed_on", cm.exception.message_dict)

    def test_cannot_close_with_open_findings(self):
        AuditFinding.objects.create(audit=self.audit, level="level2", requirement="145.A.42", description="x")
        a = self.audit
        a.auditor_independent, a.status, a.summary, a.performed_on, a.closed_on = True, "closed", "Synthèse", today(), today()
        with self.assertRaises(ValidationError) as cm:
            a.full_clean()
        self.assertIn("status", cm.exception.message_dict)

    def test_close_finding_requires_cause_and_action_and_signs(self):
        f = AuditFinding.objects.create(audit=self.audit, level="level2", requirement="145.A.42", description="x")
        with self.assertRaises(ValidationError):
            services.close_finding(f, self.w["u_camo"], "", "")
        f.refresh_from_db()
        self.assertEqual(f.status, "open")
        services.close_finding(f, self.w["u_camo"], "Étiquetage oublié", "Formation et contrôle mensuel")
        f.refresh_from_db()
        self.assertEqual(f.status, "closed")
        self.assertTrue(SignatureRecord.objects.filter(action="finding_close", object_id=str(f.pk)).exists())
        with self.assertRaises(ValidationError):
            services.close_finding(f, self.w["u_camo"], "Encore", "Encore")

    def test_close_view_rejects_wrong_password(self):
        from django.contrib.auth.models import Group

        q = self.w["u_camo"]
        q.groups.add(Group.objects.get(name="Responsable qualité"))
        f = AuditFinding.objects.create(audit=self.audit, level="level2", requirement="145.A.42", description="x")
        self.client.force_login(q)
        url = f"/qualite/constats/{f.pk}/cloturer/"
        self.client.post(url, {"root_cause": "Cause racine", "corrective_action": "Action corrective", "password": "faux"})
        f.refresh_from_db()
        self.assertEqual(f.status, "open")
        self.client.post(url, {"root_cause": "Cause racine", "corrective_action": "Action corrective", "password": PASSWORD})
        f.refresh_from_db()
        self.assertEqual(f.status, "closed")

    def test_no_finding_on_closed_audit(self):
        a = self.audit
        a.auditor_independent, a.status, a.summary, a.performed_on, a.closed_on = True, "closed", "Synthèse", today(), today()
        a.full_clean()
        a.save()
        with self.assertRaises(ValidationError):
            AuditFinding(audit=a, level="level2", requirement="x", description="x").full_clean()


class DocumentTests(TestCase):
    def setUp(self):
        self.w = make_world()
        self.doc = ControlledDocument.objects.create(reference="PRO-1", title="Réception", review_months=12)

    def _rev(self, author, **kw):
        set_current_user(author)
        try:
            return DocumentRevision.objects.create(document=self.doc, revision=kw.pop("revision", "A"), change_summary="x", **kw)
        finally:
            set_current_user(None)

    def test_four_eyes(self):
        rev = self._rev(self.w["u_mag"])
        with self.assertRaises(ValidationError):
            services.approve_revision(rev, self.w["u_mag"])
        services.approve_revision(rev, self.w["u_camo"])
        self.doc.refresh_from_db()
        self.assertEqual((self.doc.status, self.doc.current_revision), ("current", "A"))
        self.assertTrue(SignatureRecord.objects.filter(action="doc_approve", object_id=str(rev.pk)).exists())

    def test_previous_revision_superseded(self):
        a = self._rev(self.w["u_mag"], revision="A")
        services.approve_revision(a, self.w["u_camo"])
        b = self._rev(self.w["u_mag"], revision="B")
        services.approve_revision(b, self.w["u_camo"])
        a.refresh_from_db()
        self.assertEqual(a.status, "superseded")
        self.doc.refresh_from_db()
        self.assertEqual(self.doc.current_revision, "B")

    def test_authority_reference_required(self):
        self.doc.authority_approval = True
        self.doc.save()
        rev = self._rev(self.w["u_mag"])
        with self.assertRaises(ValidationError):
            services.approve_revision(rev, self.w["u_camo"])
        rev.authority_reference = "DSAC-123"
        rev.save()
        services.approve_revision(rev, self.w["u_camo"])

    def test_reject_and_withdraw(self):
        rev = self._rev(self.w["u_mag"])
        with self.assertRaises(ValidationError):
            services.withdraw_document(self.doc, self.w["u_camo"])
        with self.assertRaises(ValidationError):
            services.reject_revision(rev, self.w["u_camo"], " ")
        services.reject_revision(rev, self.w["u_camo"], "Incomplet")
        services.withdraw_document(self.doc, self.w["u_camo"])
        self.doc.refresh_from_db()
        self.assertEqual(self.doc.status, "obsolete")

    def test_review_due_alert(self):
        rev = self._rev(self.w["u_mag"])
        services.approve_revision(rev, self.w["u_camo"])
        ControlledDocument.objects.filter(pk=self.doc.pk).update(current_since=today() - timedelta(days=400))
        self.doc.refresh_from_db()
        self.assertEqual(self.doc.alert, "overdue")
