"""Prorogation de report (RIE), pièces non récupérables, classes d'articles (145.A.42)."""
from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.core.models import SignatureRecord
from apps.core.tests.factories import PASSWORD, make_component, make_world, today
from apps.fleet.models import Component, PartNumber
from apps.part145 import services
from apps.part145.models import Defect

D = Decimal


class DeferralExtensionTests(TestCase):
    def setUp(self):
        self.w = make_world()
        self.ac = self.w["ac"]
        self.d = Defect.objects.create(aircraft=self.ac, reported_by="Pilote", description="Feu INOP")
        services.defer_defect(self.d, self.w["u_b1"], "MEL 33", "C")  # 10 jours
        self.d.refresh_from_db()

    def test_only_camo_can_extend(self):
        with self.assertRaises(ValidationError):
            services.extend_deferral(self.d, self.w["u_b1"], "Pièce en commande", "RIE-1", new_date=today() + timedelta(days=15))

    def test_extension_rules(self):
        camo = self.w["u_camo"]
        self.assertEqual(self.d.fh_at_deferral, self.ac.total_fh)
        # Au-delà de l'intervalle initial (10 j) : refus
        with self.assertRaises(ValidationError):
            services.extend_deferral(self.d, camo, "Pièce en commande", "RIE-1", new_date=today() + timedelta(days=21))
        # Critère absent du report initial : refus
        with self.assertRaises(ValidationError):
            services.extend_deferral(self.d, camo, "Pièce en commande", "RIE-1", new_fh=D("2000"))
        services.extend_deferral(self.d, camo, "Pièce en commande", "RIE-1", new_date=today() + timedelta(days=20), authority_notified=True)
        self.d.refresh_from_db()
        self.assertTrue(self.d.extended)
        self.assertEqual(self.d.original_limit_date, today() + timedelta(days=10))
        self.assertEqual(self.d.deferral_limit_date, today() + timedelta(days=20))
        self.assertTrue(SignatureRecord.for_object(self.d).filter(action="extend").exists())
        # Une seule prorogation
        with self.assertRaises(ValidationError):
            services.extend_deferral(self.d, camo, "Encore", "RIE-2", new_date=today() + timedelta(days=25))
        # Échéances : la limite prorogée est utilisée
        from apps.camo.services import aircraft_due_list
        item = next(i for i in aircraft_due_list(self.ac) if i.kind == "defect")
        self.assertEqual(item.due_date, today() + timedelta(days=20))
        self.assertIn("prorogé", item.notes)

    def test_must_be_requested_before_expiry_and_category(self):
        camo = self.w["u_camo"]
        Defect.objects.filter(pk=self.d.pk).update(deferral_limit_date=today() - timedelta(days=1))
        self.d.refresh_from_db()
        with self.assertRaises(ValidationError):
            services.extend_deferral(self.d, camo, "Trop tard", "RIE-1", new_date=today() + timedelta(days=3))
        d2 = Defect.objects.create(aircraft=self.ac, reported_by="Pilote", description="x")
        services.defer_defect(d2, self.w["u_b1"], "MEL 21", "D")
        d2.refresh_from_db()
        self.assertTrue(d2.extension_blockers(new_date=today() + timedelta(days=130)))

    def test_ui(self):
        self.client.force_login(self.w["u_camo"])
        r = self.client.post(f"/part145/defauts/{self.d.pk}/proroger/", {
            "new_date": (today() + timedelta(days=15)).isoformat(), "reference": "RIE-9", "reason": "AOG pièce", "password": PASSWORD})
        self.assertEqual(r.status_code, 302)
        self.d.refresh_from_db()
        self.assertTrue(self.d.extended)
        self.assertContains(self.client.get(self.d.get_absolute_url()), "prorogé une fois")
        self.client.force_login(self.w["u_b1"])
        self.assertEqual(self.client.post(f"/part145/defauts/{self.d.pk}/proroger/", {}).status_code, 403)


class ScrapTests(TestCase):
    def setUp(self):
        self.w = make_world()

    def test_scrap_is_terminal_and_signed(self):
        c = make_component(self.w, sn="U1", status="unserviceable")
        self.client.force_login(self.w["u_mag"])
        # Incomplet : refus
        self.client.post(f"/logistique/composants/{c.pk}/rebut/", {"scrapped_on": today().isoformat(), "scrap_reason": "beyond_repair",
                                                                   "password": PASSWORD})
        c.refresh_from_db()
        self.assertNotEqual(c.status, "scrapped")
        r = self.client.post(f"/logistique/composants/{c.pk}/rebut/", {
            "scrapped_on": today().isoformat(), "scrap_reason": "beyond_repair", "mutilation_method": "Découpe",
            "mutilation_witness": "Contrôleur", "password": PASSWORD})
        self.assertEqual(r.status_code, 302)
        c.refresh_from_db()
        self.assertEqual(c.status, "scrapped")
        self.assertTrue(SignatureRecord.for_object(c).filter(action="scrap").exists())
        # Statut définitif : aucune remise en stock possible
        c.status = "serviceable"
        with self.assertRaises(ValidationError):
            c.save()
        self.client.post(f"/logistique/composants/{c.pk}/statut/", {"status": "serviceable", "reason": "erreur", "location": self.w["store"].pk})
        self.assertEqual(Component.objects.get(pk=c.pk).status, "scrapped")

    def test_installed_part_cannot_be_scrapped(self):
        from apps.fleet.models import install_component
        c = make_component(self.w, sn="I1")
        install_component(c, self.w["ac"], "MOT", today())
        self.client.force_login(self.w["u_mag"])
        self.client.post(f"/logistique/composants/{c.pk}/rebut/", {
            "scrapped_on": today().isoformat(), "scrap_reason": "beyond_repair", "mutilation_method": "Découpe",
            "mutilation_witness": "Contrôleur", "password": PASSWORD})
        self.assertEqual(Component.objects.get(pk=c.pk).status, "installed")


class PartCategoryTests(TestCase):
    def setUp(self):
        self.w = make_world()

    def test_category_rules(self):
        pn = PartNumber(pn="X1", description="Vis", category="standard_part")
        with self.assertRaises(ValidationError):
            pn.full_clean()
        pn.specification = "NAS1351-3"
        pn.full_clean()
        serial = PartNumber(pn="X2", description="Pompe", is_serialized=True, category="consumable")
        with self.assertRaises(ValidationError):
            serial.full_clean()

    def test_component_needs_release_certificate_at_reception(self):
        from apps.logistics.forms import ReceiveForm
        pn = PartNumber.objects.create(pn="FLT-1", description="Filtre", category="component")
        base = {"part_number": pn.pk, "batch": "L1", "quantity": "2", "location": self.w["store"].pk, "condition": "new",
                "tracking_number": "C-1", "issuer": "Distributeur", "issue_date": today().isoformat(), "work_status": "new",
                "check_identity": "on", "check_certificate": "on", "check_condition": "on"}
        f = ReceiveForm({**base, "cert_type": "coc"})
        self.assertFalse(f.is_valid())
        self.assertIn("cert_type", f.errors)
        self.assertTrue(ReceiveForm({**base, "cert_type": "easa_form1"}).is_valid())
        cons = PartNumber.objects.create(pn="OIL-1", description="Huile", category="consumable")
        self.assertTrue(ReceiveForm({**base, "part_number": cons.pk, "cert_type": "coc"}).is_valid())
