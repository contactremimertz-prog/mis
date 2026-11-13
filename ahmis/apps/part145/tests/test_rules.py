from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from apps.camo.models import Directive, DirectiveApplicability, MaintenanceTask, TaskAccomplishment
from apps.core.models import AuditLog, SignatureRecord
from apps.core.tests.factories import PASSWORD, make_component, make_world, today
from apps.fleet.models import install_component
from apps.logistics.models import PartRequest, StockItem, Tool
from apps.part145 import services
from apps.part145.models import Defect, TaskCard, WorkPackage

D = Decimal


class Part145RuleTests(TestCase):
    def setUp(self):
        self.w = make_world()
        self.ac = self.w["ac"]
        self.task = MaintenanceTask.objects.create(
            aircraft_type=self.w["type"], reference="T-100", title="Visite 100 h", interval_fh=D("100"),
            steps="Étape A\nÉtape B", requires_independent_inspection=True,
        )
        self.wp = WorkPackage.objects.create(aircraft=self.ac, title="Visite", planned_start=today(), planned_end=today())
        self.card = services.add_due_items_to_wp(self.wp, [f"task:{self.task.pk}:0"])[0]

    def perform(self, user):
        services.start_card(self.card, user)
        for st in self.card.steps.all():
            services.sign_step(st, user)
        services.perform_card(self.card, user, "Travaux faits", D("1"))
        self.card.refresh_from_db()

    def test_card_generated_with_steps(self):
        self.assertEqual(self.card.steps.count(), 2)
        self.assertTrue(self.card.requires_independent_inspection)

    def test_staff_without_type_authorization_cannot_start(self):
        self.ac.aircraft_type = self.w["other_type"]
        self.ac.save()
        with self.assertRaises(ValidationError):
            services.start_card(self.card, self.w["u_meca"])

    def test_perform_requires_all_steps(self):
        services.start_card(self.card, self.w["u_meca"])
        with self.assertRaises(ValidationError):
            services.perform_card(self.card, self.w["u_meca"], "x", D("1"))

    def test_independent_inspection_rules(self):
        self.perform(self.w["u_b1"])
        self.assertEqual(self.card.status, "performed")
        with self.assertRaises(ValidationError):  # même personne
            services.inspect_card(self.card, self.w["u_b1"])
        with self.assertRaises(ValidationError):  # non certifiant
            services.inspect_card(self.card, self.w["u_meca"])
        services.inspect_card(self.card, self.w["u_b1bis"])
        self.card.refresh_from_db()
        self.assertEqual(self.card.status, "closed")
        acc = TaskAccomplishment.objects.get(task_card=self.card)
        self.assertEqual(acc.fh, self.ac.total_fh)
        self.assertEqual(SignatureRecord.for_object(self.card).filter(action__in=["perform", "inspect"]).count(), 2)

    def test_crs_blocked_until_cards_closed_then_released(self):
        with self.assertRaises(ValidationError):
            services.issue_crs(self.wp, self.w["u_b1"])
        self.perform(self.w["u_meca"])
        services.inspect_card(self.card, self.w["u_b1"])
        with self.assertRaises(ValidationError):  # mécanicien non certifiant
            services.issue_crs(self.wp, self.w["u_meca"])
        services.issue_crs(self.wp, self.w["u_b1"])
        self.wp.refresh_from_db()
        self.assertEqual(self.wp.status, "released")
        sig = SignatureRecord.for_object(self.wp).get(action="crs")
        self.assertTrue(sig.is_intact)
        with self.assertRaises(ValidationError):
            services.start_card(TaskCard.objects.create(work_package=self.wp, title="tardive"), self.w["u_meca"])

    def test_major_check_crs_requires_category_c(self):
        self.wp.check_type = "major"
        self.wp.save()
        self.perform(self.w["u_meca"])
        services.inspect_card(self.card, self.w["u_b1"])
        with self.assertRaises(ValidationError):
            services.issue_crs(self.wp, self.w["u_b1"])
        services.issue_crs(self.wp, self.w["u_certc"])

    def test_one_time_ad_marked_complied(self):
        d = Directive.objects.create(number="AD-1", title="AD", effective_date=today())
        t = MaintenanceTask.objects.create(aircraft_type=self.w["type"], reference="AD-1", title="AD", directive=d, source="AD", threshold_fh=D("50"))
        card = services.add_due_items_to_wp(self.wp, [f"task:{t.pk}:0"])[0]
        services.start_card(card, self.w["u_b1"])
        services.perform_card(card, self.w["u_b1"], "Fait", D("1"))
        self.assertEqual(DirectiveApplicability.objects.get(directive=d, aircraft=self.ac).status, "complied")

    def test_defect_deferral_and_rectification(self):
        d = Defect.objects.create(aircraft=self.ac, reported_by="Pilote", description="Feu INOP")
        with self.assertRaises(ValidationError):
            services.defer_defect(d, self.w["u_meca"], "MEL 33", "C")
        services.defer_defect(d, self.w["u_b1"], "MEL 33", "C")
        d.refresh_from_db()
        self.assertEqual(d.deferral_limit_date, today() + timedelta(days=10))
        card = services.card_from_defect(self.wp, d)
        services.start_card(card, self.w["u_b1"])
        services.perform_card(card, self.w["u_b1"], "Ampoule remplacée", D("0.5"))
        d.refresh_from_db()
        self.assertEqual(d.status, "rectified")

    def test_component_change_checks(self):
        old = make_component(self.w, sn="OLD")
        install_component(old, self.ac, "MOT", today())
        no_cert = make_component(self.w, sn="NOCERT", cert=False)
        services.start_card(self.card, self.w["u_b1"])
        with self.assertRaises(ValidationError):
            services.change_component(self.card, self.w["u_b1"], old, no_cert, "MOT", "Panne")
        good = make_component(self.w, sn="GOOD")
        services.change_component(self.card, self.w["u_b1"], old, good, "MOT", "Panne")
        old.refresh_from_db()
        good.refresh_from_db()
        self.assertEqual(old.status, "unserviceable")
        self.assertEqual(good.aircraft, self.ac)
        self.assertEqual(old.installations.first().removal_reason, "Panne")

    def test_expired_life_part_refused(self):
        llp = make_component(self.w, pn=self.w["pn_llp"], sn="LLPX", csn=5000)
        with self.assertRaises(ValidationError):
            install_component(llp, self.ac, "MRH", today())

    def test_quarantined_part_refused(self):
        c = make_component(self.w, sn="Q", status="quarantine")
        with self.assertRaises(ValidationError):
            install_component(c, self.ac, "MOT", today())

    def test_tool_with_expired_calibration_blocked(self):
        tool = Tool.objects.create(reference="CLE", description="Clé", calibration_interval_days=365, last_calibration=today() - timedelta(days=400))
        with self.assertRaises(ValidationError):
            tool.check_out(self.card, self.w["s_meca"])

    def test_tool_must_be_returned_before_signing(self):
        tool = Tool.objects.create(reference="CLE2", description="Clé", calibration_interval_days=365, last_calibration=today())
        services.start_card(self.card, self.w["u_b1"])
        tool.check_out(self.card, self.w["s_b1"])
        for st in self.card.steps.all():
            services.sign_step(st, self.w["u_b1"])
        with self.assertRaises(ValidationError):
            services.perform_card(self.card, self.w["u_b1"], "ok", D("1"))
        tool.check_in()
        services.perform_card(self.card, self.w["u_b1"], "ok", D("1"))

    def test_stock_issue_and_expiry(self):
        from apps.fleet.models import PartNumber
        from apps.logistics.models import ReleaseCertificate

        pn = PartNumber.objects.create(pn="OIL", description="Huile", unit="L")
        lot = StockItem.objects.create(part_number=pn, batch="L1", location=self.w["store"], quantity=D("10"))
        ReleaseCertificate.objects.create(cert_type="coc", tracking_number="C1", issuer="X", issue_date=today(), part_number=pn, stock_item=lot)
        pr = PartRequest.objects.create(task_card=self.card, part_number=pn, quantity=D("3"))
        pr.fulfil_with_stock(lot)
        lot.refresh_from_db()
        self.assertEqual(lot.quantity, D("7"))
        lot.shelf_life_expiry = today() - timedelta(days=1)
        lot.save()
        pr2 = PartRequest.objects.create(task_card=self.card, part_number=pn, quantity=D("1"))
        with self.assertRaises(ValidationError):
            pr2.fulfil_with_stock(lot)


class TraceabilityTests(TestCase):
    def setUp(self):
        self.w = make_world()

    def test_audit_log_records_changes(self):
        ac = self.w["ac"]
        ac.base = "Nouvelle base"
        ac.save()
        log = AuditLog.objects.filter(object_id=str(ac.pk), action="update").first()
        self.assertIn(("base", "", "Nouvelle base"), log.changes_list)

    def test_records_cannot_be_deleted(self):
        with self.assertRaises(ValidationError):
            self.w["ac"].delete()
        log = AuditLog.objects.first()
        with self.assertRaises(ValidationError):
            log.delete()

    def test_signature_is_immutable_and_tamper_evident(self):
        sig = SignatureRecord.sign(self.w["u_b1"], self.w["ac"], "camo_review", "Revue")
        self.assertTrue(sig.is_intact)
        with self.assertRaises(ValidationError):
            sig.save()
        SignatureRecord.objects.filter(pk=sig.pk).update(statement="Falsifié")
        sig.refresh_from_db()
        self.assertFalse(sig.is_intact)


class WebFlowTests(TestCase):
    """Parcours via l'interface : signature avec ressaisie du mot de passe."""

    def setUp(self):
        self.w = make_world()
        task = MaintenanceTask.objects.create(aircraft_type=self.w["type"], reference="T-L", title="Lubrification", interval_fh=D("50"), steps="Graisser")
        self.wp = WorkPackage.objects.create(aircraft=self.w["ac"], title="Ligne", planned_start=today(), planned_end=today())
        self.card = services.add_due_items_to_wp(self.wp, [f"task:{task.pk}:0"])[0]
        self.client.login(username="b1", password=PASSWORD)

    def test_full_cycle_through_views(self):
        r = self.client.post(reverse("part145:card_action", args=[self.card.pk, "start"]))
        self.assertEqual(r.status_code, 302)
        step = self.card.steps.first()
        self.client.post(reverse("part145:step_sign", args=[step.pk]), {"password": "faux"})
        step.refresh_from_db()
        self.assertIsNone(step.done_at)  # mauvais mot de passe : refusé
        self.client.post(reverse("part145:step_sign", args=[step.pk]), {"password": PASSWORD, "measured_value": "OK"})
        step.refresh_from_db()
        self.assertIsNotNone(step.done_at)
        self.client.post(reverse("part145:card_action", args=[self.card.pk, "perform"]), {"password": PASSWORD, "work_done": "Graissé", "actual_mh": "0.5"})
        self.card.refresh_from_db()
        self.assertEqual(self.card.status, "closed")
        self.client.post(reverse("part145:wp_crs", args=[self.wp.pk]), {"password": PASSWORD})
        self.wp.refresh_from_db()
        self.assertEqual(self.wp.status, "released")
        r = self.client.get(reverse("part145:wp_print", args=[self.wp.pk]))
        self.assertContains(r, "Certifie que les travaux")

    def test_mechanic_cannot_sign_crs(self):
        self.client.login(username="meca", password=PASSWORD)
        r = self.client.post(reverse("part145:wp_crs", args=[self.wp.pk]), {"password": PASSWORD})
        self.assertEqual(r.status_code, 403)

    def test_utilisation_entry_view(self):
        self.client.login(username="planif", password=PASSWORD)
        r = self.client.post(reverse("fleet:utilisation_create"), {"aircraft": self.w["ac"].pk, "date": today().isoformat(), "fh": "1.5", "fc": "3", "reference": "CRM 1"})
        self.assertEqual(r.status_code, 302)
        self.w["ac"].refresh_from_db()
        self.assertEqual(self.w["ac"].total_fh, D("1001.5"))


class RecencyTrainingTests(TestCase):
    """145.A.35 : expérience récente (6 mois / 24) et formations obligatoires bloquent la signature."""

    def setUp(self):
        from apps.core.tests.factories import make_world
        self.w = make_world()

    def test_ok_when_all_current(self):
        s = self.w["s_b1"]
        self.assertEqual(s.signing_blockers(self.w["type"], certifying=True), [])

    def test_recency_blocks_certifying_only(self):
        s = self.w["s_b1"]
        s.experience_records.all().delete()
        problems = s.signing_blockers(self.w["type"], certifying=True)
        self.assertTrue(any("expérience récente" in p for p in problems))
        self.assertFalse(any("expérience récente" in p for p in s.signing_blockers(self.w["type"])))

    def test_recency_can_be_disabled(self):
        from django.conf import settings
        from django.test import override_settings
        s = self.w["s_b1"]
        s.experience_records.all().delete()
        with override_settings(AHMIS={**settings.AHMIS, "RECENCY_ENFORCE": False}):
            self.assertEqual(s.signing_blockers(self.w["type"], certifying=True), [])

    def test_expired_training_blocks(self):
        from datetime import timedelta
        from django.utils import timezone
        s = self.w["s_meca"]
        s.qualifications.filter(category="human_factors").update(expiry=timezone.localdate() - timedelta(days=1))
        self.assertFalse(s.can_perform(self.w["type"]))
        # La formation continue n'est exigée que du personnel certifiant
        b = self.w["s_b1"]
        b.qualifications.filter(category="continuation").delete()
        self.assertTrue(b.can_perform(self.w["type"]))
        self.assertFalse(b.can_certify(self.w["type"]))

    def test_require_signing_raises(self):
        from django.core.exceptions import ValidationError
        from apps.part145.services import require_signing
        s = self.w["s_b1"]
        s.qualifications.all().delete()
        with self.assertRaises(ValidationError):
            require_signing(s, self.w["type"], certifying=True)
