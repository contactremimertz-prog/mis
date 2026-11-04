from datetime import timedelta
from decimal import Decimal

from django.test import TestCase

from apps.camo.models import Directive, MaintenanceTask, TaskAccomplishment
from apps.camo.services import fleet_due_list, forecast, task_due
from apps.core.tests.factories import make_component, make_world, today
from apps.fleet.models import install_component

D = Decimal


class DueComputationTests(TestCase):
    def setUp(self):
        self.w = make_world()
        self.ac = self.w["ac"]

    def task(self, **kw):
        defaults = dict(aircraft_type=self.w["type"], reference="T-1", title="Visite")
        defaults.update(kw)
        return MaintenanceTask.objects.create(**defaults)

    def done(self, task, fh, fc, days_ago, component=None):
        return TaskAccomplishment.objects.create(task=task, aircraft=self.ac, component=component, date=today() - timedelta(days=days_ago),
                                                 fh=D(fh), fc=fc, source="initial")

    def test_whichever_first_hours(self):
        t = self.task(interval_fh=D("100"), interval_days=365)
        self.done(t, "940", 2900, 10)  # 40 FH restantes = 20 jours ; calendrier = 355 jours
        it = task_due(t, self.ac)
        self.assertEqual(it.remaining_fh, D("40"))
        self.assertEqual(it.driver, "FH")
        self.assertEqual(it.projected_date, today() + timedelta(days=20))
        self.assertEqual(it.status, "due_soon")

    def test_whichever_first_calendar(self):
        t = self.task(interval_fh=D("1000"), interval_days=365)
        self.done(t, "990", 2990, 360)
        it = task_due(t, self.ac)
        self.assertEqual(it.driver, "calendrier")
        self.assertEqual(it.due_date, today() + timedelta(days=5))

    def test_tolerance_then_overdue(self):
        t = self.task(interval_fh=D("100"), tolerance_fh=D("10"))
        self.done(t, "895", 2900, 30)  # dépassé de 5 FH
        self.assertEqual(task_due(t, self.ac).status, "tolerance")
        t2 = self.task(reference="T-2", interval_fh=D("100"), tolerance_fh=D("10"))
        self.done(t2, "880", 2900, 30)  # dépassé de 20 FH
        self.assertEqual(task_due(t2, self.ac).status, "overdue")

    def test_threshold_used_when_never_done(self):
        t = self.task(threshold_fh=D("1200"), interval_fh=D("500"))
        it = task_due(t, self.ac)
        self.assertEqual(it.due_fh, D("1200"))
        self.assertEqual(it.status, "ok")

    def test_one_time_task_disappears_once_done(self):
        t = self.task(threshold_fh=D("1500"))
        self.assertIsNotNone(task_due(t, self.ac))
        self.done(t, "999", 2999, 1)
        self.assertIsNone(task_due(t, self.ac))

    def test_ad_compliance_counted_from_effective_date(self):
        # 100 FH saisies après l'entrée en vigueur : l'AD « dans les 150 FH » laisse 50 FH
        d = Directive.objects.create(number="AD-X", title="Test", effective_date=today() - timedelta(days=5))
        self.ac.counters_date = today() - timedelta(days=10)
        self.ac.total_fh = D("900")
        self.ac.total_fc = 2800
        self.ac.save()
        self.ac.record_utilisation(today() - timedelta(days=6), "0", 0)
        self.ac.record_utilisation(today() - timedelta(days=1), "100", 200)
        t = self.task(reference="AD-X", source="AD", directive=d, threshold_fh=D("150"))
        it = task_due(t, self.ac)
        self.assertEqual(it.due_fh, D("1050"))
        self.assertEqual(it.remaining_fh, D("50"))

    def test_component_task_uses_component_counters(self):
        c = make_component(self.w, tsn_fh=D("400"), csn=100, tso_fh=D("400"), cso=100)
        install_component(c, self.ac, "MOT", today())
        t = self.task(reference="BORO", part_number=self.w["pn_engine"], interval_fh=D("500"))
        items = [i for i in fleet_due_list([self.ac]) if i.kind == "component_task"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].remaining_fh, D("100"))  # 500 - 400 (compteur composant, pas cellule)

    def test_llp_and_tbo_items(self):
        c = make_component(self.w, tsn_fh=D("2950"), csn=10, tso_fh=D("2950"), cso=10)
        install_component(c, self.ac, "MOT", today())
        llp = make_component(self.w, pn=self.w["pn_llp"], sn="LLP1", csn=4990)
        install_component(llp, self.ac, "MRH", today())
        items = {i.kind: i for i in fleet_due_list([self.ac]) if i.kind in ("tbo", "llp")}
        self.assertEqual(items["tbo"].remaining_fh, D("50"))
        self.assertEqual(items["llp"].remaining_fc, 10)
        self.assertEqual(items["llp"].projected_date, today() + timedelta(days=2))

    def test_utilisation_updates_installed_components(self):
        c = make_component(self.w)
        install_component(c, self.ac, "MOT", today())
        self.ac.record_utilisation(today(), "2.5", 4)
        c.refresh_from_db()
        self.ac.refresh_from_db()
        self.assertEqual(self.ac.total_fh, D("1002.5"))
        self.assertEqual(c.tsn_fh, D("2.5"))
        self.assertEqual(c.cso, 4)

    def test_forecast_unrolls_repetitive_tasks(self):
        t = self.task(interval_days=30)
        self.done(t, "990", 2990, 0)
        events = [e for e in forecast([self.ac], horizon_days=95) if e.item.task == t]
        self.assertEqual([e.date for e in events], [today() + timedelta(days=30 * k) for k in (1, 2, 3)])

    def test_arc_expiry_item(self):
        self.ac.arc_expiry = today() + timedelta(days=10)
        self.ac.save()
        arc = [i for i in fleet_due_list([self.ac]) if i.kind == "arc"][0]
        self.assertEqual(arc.status, "due_soon")


class NonCumulativeToleranceTests(TestCase):
    """Règle de tolérance non cumulative : la tolérance consommée n'allonge jamais l'intervalle suivant."""

    def setUp(self):
        self.w = make_world()
        self.ac = self.w["ac"]
        self.task = MaintenanceTask.objects.create(aircraft_type=self.w["type"], reference="T-TOL", title="Visite 100 h",
                                                   interval_fh=D("100"), tolerance_fh=D("10"))

    def acc(self, fh, days_ago=0):
        return TaskAccomplishment.objects.create(task=self.task, aircraft=self.ac, date=today() - timedelta(days=days_ago),
                                                 fh=D(fh), fc=0, source="initial")

    def test_late_within_tolerance_restarts_from_theoretical_due(self):
        self.acc("800", 30)            # butée suivante : 900
        late = self.acc("908", 1)      # réalisée 8 FH en retard (tolérance 10)
        self.assertTrue(late.used_tolerance)
        self.assertEqual(late.due_fh_at_done, D("900"))
        self.assertEqual(task_due(self.task, self.ac).due_fh, D("1000"))  # et non 1008

    def test_early_restarts_from_actual(self):
        self.acc("800", 30)
        early = self.acc("880", 1)     # 20 FH en avance
        self.assertFalse(early.used_tolerance)
        self.assertEqual(task_due(self.task, self.ac).due_fh, D("980"))

    def test_calendar_tolerance_non_cumulative(self):
        t = MaintenanceTask.objects.create(aircraft_type=self.w["type"], reference="T-CAL", title="Annuelle",
                                           interval_days=365, tolerance_days=30)
        TaskAccomplishment.objects.create(task=t, aircraft=self.ac, date=today() - timedelta(days=380), fh=D("1"), fc=0)
        late = TaskAccomplishment.objects.create(task=t, aircraft=self.ac, date=today(), fh=D("2"), fc=0)
        self.assertTrue(late.used_tolerance)
        self.assertEqual(task_due(t, self.ac).due_date, today() - timedelta(days=15) + timedelta(days=365))

    def test_no_tolerance_on_als_and_ad_requires_reference(self):
        from django.core.exceptions import ValidationError

        als = MaintenanceTask(aircraft_type=self.w["type"], reference="ALS-1", title="ALS", source="ALS", interval_fh=D("100"), tolerance_fh=D("5"))
        with self.assertRaises(ValidationError):
            als.full_clean()
        ad = MaintenanceTask(aircraft_type=self.w["type"], reference="AD-1", title="AD", source="AD", interval_fh=D("100"), tolerance_fh=D("5"))
        with self.assertRaises(ValidationError):
            ad.full_clean()
        ad.tolerance_reference = "AD 2026-0001 §(g)"
        ad.full_clean()

    def test_out_of_order_entry_refused(self):
        from django.core.exceptions import ValidationError

        self.acc("800", 10)
        older = TaskAccomplishment(task=self.task, aircraft=self.ac, date=today() - timedelta(days=20), fh=D("790"), fc=0)
        with self.assertRaises(ValidationError):
            older.full_clean()


class AmpReviewTests(TestCase):
    """M.A.302(g) : revue périodique du programme d'entretien."""

    def setUp(self):
        from apps.core.tests.factories import make_world
        self.w = make_world()

    def _review(self, days_ago, **kw):
        from apps.camo.models import AmpReview
        from datetime import timedelta
        from django.utils import timezone
        data = dict(aircraft_type=self.w["type"], review_date=timezone.localdate() - timedelta(days=days_ago), amp_reference="AMP-1",
                    revision_before="R1", reviewer="X", reliability_reviewed=True, instructions_reviewed=True)
        data.update(kw)
        r = AmpReview(**data)
        r.full_clean()
        r.save()
        return r

    def test_status_cycle(self):
        from apps.camo.models import amp_review_status
        self.assertEqual(amp_review_status(self.w["type"])["status"], "none")
        self._review(400)
        self.assertEqual(amp_review_status(self.w["type"])["status"], "overdue")
        self._review(350)
        self.assertEqual(amp_review_status(self.w["type"])["status"], "due_soon")
        r = self._review(10)
        self.assertEqual(amp_review_status(self.w["type"])["status"], "ok")
        self.assertEqual((r.next_review_due - r.review_date).days in (365, 366), True)

    def test_incomplete_review_refused(self):
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            self._review(1, instructions_reviewed=False)

    def test_amendment_needs_revision_and_approval(self):
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            self._review(1, outcome="amended", revision_after="R2", changes="x")
        with self.assertRaises(ValidationError):
            self._review(1, outcome="amended", revision_after="R1", changes="x", approval_type="indirect", approval_reference="P1")
        from apps.camo.models import MaintenanceTask
        t = MaintenanceTask.objects.create(aircraft_type=self.w["type"], reference="T1", title="t", interval_fh=100, amp_revision="R1")
        self._review(1, outcome="amended", revision_after="R2", changes="x", approval_type="indirect", approval_reference="P1")
        t.refresh_from_db()
        self.assertEqual(t.amp_revision, "R2")

    def test_next_due_cannot_exceed_period(self):
        from datetime import timedelta
        from django.core.exceptions import ValidationError
        from django.utils import timezone
        with self.assertRaises(ValidationError):
            self._review(1, next_review_due=timezone.localdate() + timedelta(days=500))


class AmpReviewListTests(TestCase):
    def test_type_with_a_retired_aircraft_still_listed(self):
        from apps.fleet.models import Aircraft
        w = make_world()
        Aircraft.objects.create(registration="F-OLD", msn="0", aircraft_type=w["type"], manufacture_date=today() - timedelta(days=9000),
                                status="retired", withdrawn_on=today() - timedelta(days=10))
        self.client.force_login(w["u_camo"])
        r = self.client.get("/camo/revue-programme/")
        self.assertContains(r, ">H125<")
