"""Conservation réglementaire des enregistrements (M.A.305(h), 145.A.55(c), 145.A.35(j))."""
from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import ProtectedError
from django.test import TestCase

from apps.camo.models import MaintenanceTask, TaskAccomplishment
from apps.core import retention
from apps.core.dates import add_months
from apps.core.tests.factories import make_world, today
from apps.logistics.models import Tool, ToolCalibration
from apps.part145.models import Staff


class AddMonthsTests(TestCase):
    def test_end_of_month(self):
        self.assertEqual(add_months(date(2026, 1, 31), 1), date(2026, 2, 28))
        self.assertEqual(add_months(date(2026, 11, 15), 3), date(2027, 2, 15))
        self.assertEqual(add_months(date(2026, 3, 15), -3), date(2025, 12, 15))


class RetentionTests(TestCase):
    def setUp(self):
        self.w = make_world()
        self.ac = self.w["ac"]

    def test_aircraft_in_service_kept_indefinitely(self):
        self.assertIsNone(retention.retained_until(self.ac))

    def test_retired_aircraft_needs_withdrawal_date(self):
        self.ac.status = "retired"
        with self.assertRaises(ValidationError):
            self.ac.full_clean()
        self.ac.withdrawn_on = today() - timedelta(days=500)
        self.ac.full_clean()
        self.ac.save()
        self.assertEqual(retention.retained_until(self.ac), add_months(self.ac.withdrawn_on, 12))

    def test_accomplishment_superseded_and_36_months(self):
        t = MaintenanceTask.objects.create(aircraft_type=self.w["type"], reference="T1", title="t", interval_fh=Decimal("100"))
        old = TaskAccomplishment.objects.create(task=t, aircraft=self.ac, date=today() - timedelta(days=1500), fh=Decimal("100"), fc=1, source="initial")
        self.assertIsNone(retention.retained_until(old))  # dernier état connu
        TaskAccomplishment.objects.create(task=t, aircraft=self.ac, date=today() - timedelta(days=1400), fh=Decimal("190"), fc=2, source="external")
        until = retention.retained_until(old)
        self.assertEqual(until, add_months(today() - timedelta(days=1400), 36))
        self.assertLess(until, today())
        rows, counts = retention.evaluate(retention.RULES_BY_KEY["accomplishments"])
        self.assertEqual(counts["eligible"], 1)
        self.assertEqual(counts["open"], 1)

    def test_ad_accomplishment_kept_for_aircraft_life(self):
        t = MaintenanceTask.objects.create(aircraft_type=self.w["type"], reference="AD1", title="ad", source="AD", interval_fh=Decimal("100"))
        old = TaskAccomplishment.objects.create(task=t, aircraft=self.ac, date=today() - timedelta(days=1500), fh=Decimal("100"), fc=1, source="initial")
        TaskAccomplishment.objects.create(task=t, aircraft=self.ac, date=today() - timedelta(days=1400), fh=Decimal("190"), fc=2, source="external")
        self.assertIsNone(retention.retained_until(old))

    def test_staff_kept_three_years_after_leaving(self):
        s = Staff(employee_number="X1", first_name="a", last_name="b", active=True, left_on=today() - timedelta(days=10))
        with self.assertRaises(ValidationError):
            s.full_clean()
        s.active = False
        s.save()
        self.assertEqual(retention.retained_until(s), add_months(s.left_on, 36))

    def test_delete_refused_while_retained(self):
        tool = Tool.objects.create(**self._tool_kwargs())
        cal = ToolCalibration.objects.create(tool=tool, date=today() - timedelta(days=30), provider="Lab", certificate_ref="C1")
        with self.assertRaises(ValidationError):  # suppression unitaire toujours refusée (TrackedModel)
            cal.delete()
        with self.assertRaises(ProtectedError), transaction.atomic():  # suppression en masse (admin, script)
            ToolCalibration.objects.filter(pk=cal.pk).delete()
        old = ToolCalibration.objects.create(tool=tool, date=today() - timedelta(days=4 * 366), provider="Lab", certificate_ref="C0")
        ToolCalibration.objects.filter(pk=old.pk).delete()  # durée minimale échue : purge documentée possible
        self.assertFalse(ToolCalibration.objects.filter(pk=old.pk).exists())

    def _tool_kwargs(self):
        return {"reference": "T-1", "description": "Clé dynamométrique", "calibration_interval_days": 365}

    def test_report_page(self):
        from django.test import Client
        c = Client()
        c.force_login(self.w["u_camo"])
        r = c.get("/qualite/conservation/")
        self.assertEqual(r.status_code, 200)
        r = c.get("/qualite/conservation/accomplishments.csv")
        self.assertEqual(r.status_code, 200)
        c.force_login(self.w["u_meca"])
        self.assertEqual(c.get("/qualite/conservation/").status_code, 403)
