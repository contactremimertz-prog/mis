"""Vue 3D : rattachement ATA des échéances aux zones et affichage sur la fiche aéronef."""
import io
import tempfile
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, SimpleTestCase, TestCase, override_settings

from apps.fleet.heli3d import item_ata, outside_zones, zone_states
from apps.fleet.models import Aircraft


def due(status, ata="", pn_ata="", days=10):
    comp = SimpleNamespace(part_number=SimpleNamespace(ata=pn_ata)) if pn_ata else None
    task = SimpleNamespace(ata=ata) if ata else None
    return SimpleNamespace(status=status, task=task, defect=None, directive=None, component=comp, remaining_days=days)


class ZoneRulesTests(SimpleTestCase):
    def test_ata_from_task_then_component(self):
        self.assertEqual(item_ata(due("ok", ata="63-21")), "63")
        self.assertEqual(item_ata(due("ok", pn_ata="72")), "72")
        self.assertEqual(item_ata(due("ok")), "")
        self.assertEqual(item_ata(due("ok", ata="6", pn_ata="72-00")), "72")
        self.assertEqual(item_ata(due("ok", ata="xx")), "")

    def test_rotor_flight_controls_in_rotor_zone(self):
        self.assertEqual(zone_states([due("overdue", "67-10")])[0]["level"], "crit")

    def test_items_outside_zones_are_counted(self):
        items = [due("ok", "62"), due("overdue", "05"), due("tolerance"), due("due_soon", "29")]
        self.assertEqual(zone_states(items)[0]["level"], "ok")
        self.assertEqual(outside_zones(items), {"crit": 2, "warn": 1})

    def test_worst_status_wins(self):
        z = {s["id"]: s for s in zone_states([due("ok", "62"), due("due_soon", "62"), due("tolerance", "72"), due("ok", "32")])}
        self.assertEqual(z["rotor"]["level"], "warn")
        self.assertEqual(z["engine"]["level"], "crit")
        self.assertEqual(z["gear"]["level"], "ok")
        self.assertEqual(z["bte"]["level"], "none")
        self.assertEqual(z["tail"]["items"], [])

    def test_most_urgent_listed_first(self):
        z = zone_states([due("ok", "63", days=5), due("overdue", "63", days=-3)])[1]
        self.assertEqual([i.status for i in z["items"]], ["overdue", "ok"])


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="ahmis-test-media-"))
class AircraftPageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("load_demo", verbosity=0, stdout=io.StringIO())

    def setUp(self):
        self.c = Client()
        self.c.force_login(get_user_model().objects.get(username="admin"))

    def test_helicopter_page_shows_3d_view(self):
        ac = Aircraft.objects.filter(aircraft_type__category="helicopter").first()
        self.assertIsNotNone(ac)
        r = self.c.get(ac.get_absolute_url())
        self.assertContains(r, "data-heli3d")
        self.assertContains(r, "ahmis/heli3d.js")
        self.assertContains(r, 'data-zone="engine"')

    def test_aeroplane_page_has_no_3d_view(self):
        ac = Aircraft.objects.filter(aircraft_type__category="aeroplane").first()
        if ac is None:
            self.skipTest("pas d'avion dans la démo")
        r = self.c.get(ac.get_absolute_url())
        self.assertNotContains(r, "data-heli3d")
        self.assertNotContains(r, "three.min.js")

    def test_outside_alert_shown_when_urgent_items_have_no_zone(self):
        from apps.camo.services import aircraft_due_list
        for ac in Aircraft.objects.filter(aircraft_type__category="helicopter"):
            out = outside_zones(aircraft_due_list(ac))
            r = self.c.get(ac.get_absolute_url())
            if out["crit"] or out["warn"]:
                self.assertContains(r, "Hors de ces zones")
                return
        self.skipTest("aucun hélicoptère de la démo avec échéance urgente hors zone")
