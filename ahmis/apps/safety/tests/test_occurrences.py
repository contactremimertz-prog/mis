"""Comptes rendus d'événements : délais 72 h / 30 j, contrôles de statut, visibilité restreinte."""
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.core.tests.factories import PASSWORD, make_world
from apps.safety.models import OccurrenceReport


def report(**kw):
    now = timezone.now()
    data = dict(title="Évt", category="system", occurred_at=now - timedelta(hours=10), aware_at=now - timedelta(hours=10),
                description="desc")
    data.update(kw)
    r = OccurrenceReport(**data)
    r.full_clean()
    r.save()
    return r


class OccurrenceRulesTests(TestCase):
    def setUp(self):
        self.w = make_world()

    def test_72h_deadline_and_alert(self):
        r = report()
        self.assertEqual(r.report_deadline, r.aware_at + timedelta(hours=72))
        self.assertEqual(r.alert, "ok")
        t = timezone.now() - timedelta(hours=80)
        late = report(aware_at=t, occurred_at=t)
        self.assertEqual(late.alert, "overdue")
        self.assertTrue(late.report_late)

    def test_submission_requires_authority_and_late_reason(self):
        now = timezone.now()
        with self.assertRaises(ValidationError):
            report(status="submitted")
        with self.assertRaises(ValidationError) as cm:
            report(status="submitted", authority="DSAC", submitted_at=now, aware_at=now - timedelta(hours=100),
                   occurred_at=now - timedelta(hours=100))
        self.assertIn("late_reason", cm.exception.message_dict)
        r = report(status="submitted", authority="DSAC", submitted_at=now, aware_at=now - timedelta(hours=100),
                   occurred_at=now - timedelta(hours=100), late_reason="Découverte lors d'un audit")
        self.assertTrue(r.report_late)

    def test_follow_up_30_days(self):
        now = timezone.now()
        r = report(status="submitted", authority="DSAC", submitted_at=now - timedelta(days=31), aware_at=now - timedelta(days=32),
                   occurred_at=now - timedelta(days=32))
        self.assertTrue(r.follow_up_late)
        self.assertEqual(r.alert, "overdue")
        r.status = "follow_up"
        with self.assertRaises(ValidationError):
            r.full_clean()  # analyse obligatoire
        r.analysis, r.follow_up_at = "Cause identifiée", now
        r.full_clean()

    def test_closure_and_not_reportable(self):
        with self.assertRaises(ValidationError):
            report(status="not_reportable")
        with self.assertRaises(ValidationError):
            report(status="not_reportable", not_reportable_reason="x", severity="serious_incident")
        report(status="not_reportable", not_reportable_reason="Hors liste 2015/1018")

    def test_aware_before_occurrence_refused(self):
        now = timezone.now()
        with self.assertRaises(ValidationError):
            report(occurred_at=now - timedelta(hours=1), aware_at=now - timedelta(hours=2))


class OccurrenceVisibilityTests(TestCase):
    def setUp(self):
        self.w = make_world()
        from django.contrib.auth.models import Group
        from django.contrib.auth import get_user_model
        self.q = get_user_model().objects.create_user("qual", password=PASSWORD)
        self.q.groups.add(Group.objects.get(name="Responsable qualité"))

    def _declare(self, user, **extra):
        self.client.force_login(user)
        now = timezone.localtime().strftime("%Y-%m-%dT%H:%M")
        data = {"title": "Outil oublié", "category": "fod", "severity": "medium", "phase": "maintenance", "occurred_at": now,
                "aware_at": now, "description": "Lampe retrouvée en zone moteur", "reporter_name": "Moi"}
        data.update(extra)
        return self.client.post("/evenements/declarer/", data)

    def test_everyone_can_declare_but_sees_only_own(self):
        r = self._declare(self.w["u_meca"], confidential="on")
        self.assertEqual(r.status_code, 302, r.content[:500])
        occ = OccurrenceReport.objects.get()
        self.assertEqual(self.client.get(occ.get_absolute_url()).status_code, 200)
        self.assertContains(self.client.get("/evenements/"), occ.number)
        # Un autre mécanicien / certifiant ne le voit pas
        self.client.force_login(self.w["u_b1"])
        self.assertEqual(self.client.get(occ.get_absolute_url()).status_code, 403)
        self.assertNotContains(self.client.get("/evenements/"), occ.number)
        self.assertEqual(self.client.get(f"/evenements/{occ.pk}/traiter/").status_code, 403)
        # CAMO : voit et traite, mais pas l'identité du déclarant confidentiel
        self.client.force_login(self.w["u_camo"])
        page = self.client.get(occ.get_absolute_url())
        self.assertEqual(page.status_code, 200)
        self.assertNotContains(page, "Moi</dd>")
        # Qualité : voit l'identité
        self.client.force_login(self.q)
        self.assertContains(self.client.get(occ.get_absolute_url()), "Moi")

    def test_dashboard_kpi_only_for_safety_roles(self):
        self._declare(self.w["u_meca"])
        self.client.force_login(self.q)
        self.assertContains(self.client.get("/"), "Comptes rendus d'événements")
        self.client.force_login(self.w["u_meca"])
        self.assertNotContains(self.client.get("/"), "ouvert(s), dont")
