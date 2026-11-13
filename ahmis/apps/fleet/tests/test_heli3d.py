"""Vue 3D : rattachement ATA des échéances aux zones et affichage sur la fiche aéronef."""
import io
import tempfile
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, SimpleTestCase, TestCase, override_settings

from apps.fleet.heli3d import fleet_counts, heli_texts, item_ata, model_for, neighbours, outside_zones, zone_states
from apps.fleet.models import Aircraft


def due(status, ata="", pn_ata="", days=10, ac=None):
    comp = SimpleNamespace(part_number=SimpleNamespace(ata=pn_ata)) if pn_ata else None
    task = SimpleNamespace(ata=ata) if ata else None
    return SimpleNamespace(status=status, task=task, defect=None, directive=None, component=comp, remaining_days=days, aircraft=ac)


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


class FleetCountsTests(SimpleTestCase):
    def test_counts_per_helicopter_and_no_counts_for_aeroplanes(self):
        heli = SimpleNamespace(pk=1, aircraft_type=SimpleNamespace(category="helicopter"))
        plane = SimpleNamespace(pk=2, aircraft_type=SimpleNamespace(category="aeroplane"))
        items = [due("overdue", "63", ac=heli), due("ok", "63", ac=heli), due("due_soon", "72", ac=heli),
                 due("ok", "62", ac=heli), due("overdue", "32", ac=plane)]
        counts = fleet_counts([heli, plane], items)
        self.assertNotIn(2, counts)
        self.assertEqual([z["id"] for z in counts[1]["crit"]], ["bte"])
        self.assertEqual([z["id"] for z in counts[1]["warn"]], ["engine"])
        self.assertEqual([z["id"] for z in counts[1]["none"]], ["tail", "gear"])
        self.assertEqual(counts[1]["crit"][0]["first"].status, "overdue")

    def test_urgent_items_outside_zones_are_reported_in_the_fleet_list(self):
        heli = SimpleNamespace(pk=1, aircraft_type=SimpleNamespace(category="helicopter"))
        counts = fleet_counts([heli], [due("overdue", "05", ac=heli), due("due_soon", ac=heli), due("ok", "62", ac=heli)])
        self.assertEqual(counts[1]["crit"], [])
        self.assertEqual(counts[1]["outside"], {"crit": 1, "warn": 1})


class ModelChoiceTests(SimpleTestCase):
    def test_reference_models_by_type_code(self):
        self.assertEqual(model_for("H135")["id"], "h135")
        self.assertEqual(model_for("h145")["id"], "h145")
        self.assertEqual(model_for("NH90")["id"], "nh90")
        self.assertEqual(model_for("Super Puma")["id"], "super-puma")
        self.assertTrue(model_for("AS332")["exact"])

    def test_closest_model_is_flagged(self):
        m = model_for("H125")
        self.assertEqual((m["id"], m["exact"]), ("h135", False))
        self.assertFalse(model_for("H160")["exact"])

    def test_unknown_type_uses_generic_model(self):
        self.assertIsNone(model_for("R44"))
        self.assertIsNone(model_for(""))

    def test_model_files_are_shipped(self):
        from django.contrib.staticfiles import finders
        for code in ("H135", "H145", "NH90", "Super Puma"):
            self.assertIsNotNone(finders.find(model_for(code)["file"]), code)
        self.assertIsNotNone(finders.find("ahmis/vendor/GLTFLoader.js"))

    def test_texts_for_the_script(self):
        t = heli_texts()
        self.assertIn("{n}", t["rev_rem"])
        self.assertEqual(set(t["zone"]), {"cellule", "portes", "feux", "interieur"})
        self.assertIn("sim", t)


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

    def test_helicopter_page_loads_its_reference_model(self):
        ac = Aircraft.objects.filter(aircraft_type__code="H135").first()
        r = self.c.get(ac.get_absolute_url())
        self.assertContains(r, 'data-model="/static/ahmis/models/h135.glb"')
        self.assertContains(r, "ahmis/vendor/GLTFLoader.js")
        self.assertContains(r, 'id="heli-texts"')
        self.assertContains(r, "data-heli-focusbar")
        self.assertContains(r, "modèle H135")

    def test_csp_lets_the_model_textures_load(self):
        ac = Aircraft.objects.filter(aircraft_type__category="helicopter").first()
        csp = self.c.get(ac.get_absolute_url())["Content-Security-Policy"]
        self.assertIn("connect-src 'self' blob:", csp)
        self.assertIn("img-src 'self' data: blob:", csp)
        self.assertNotIn("unsafe-eval", csp)

    def test_3d_texts_are_translated(self):
        from django.utils import translation
        with translation.override("de"):
            self.assertEqual(heli_texts()["xray"], "Röntgen")
        with translation.override("en"):
            self.assertEqual(heli_texts()["iso"], "Isolated view")

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

    def test_fleet_list_shows_counters_and_zone_links(self):
        r = self.c.get("/flotte/aeronefs/")
        self.assertContains(r, "Urgence haute")
        self.assertContains(r, "data-heli-count=")
        self.assertContains(r, "?zone=")
        self.assertContains(r, "avion : pas de vue 3D")
        self.assertContains(r, "Hors éléments")
        self.assertContains(r, "ahmis/fleet_counts.js")

    def test_other_lists_are_unchanged(self):
        r = self.c.get("/flotte/composants/")
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, "heli-count")

    def test_navigation_between_helicopters(self):
        helis = list(Aircraft.objects.filter(aircraft_type__category="helicopter").exclude(status="retired").order_by("registration"))
        self.assertGreaterEqual(len(helis), 2)
        nav = neighbours(helis[0])
        self.assertEqual(nav["next"], helis[1])
        self.assertEqual(nav["prev"], helis[-1])
        self.assertNotIn("aeroplane", {a.aircraft_type.category for a in nav["all"]})
        r = self.c.get(helis[0].get_absolute_url())
        self.assertContains(r, "data-heli-select")
        self.assertContains(r, f'href="{helis[1].get_absolute_url()}#vue-3d"')
        r = self.c.get(helis[0].get_absolute_url() + "?zone=engine")
        self.assertContains(r, f'href="{helis[1].get_absolute_url()}?zone=engine#vue-3d"')
        r = self.c.get(helis[0].get_absolute_url() + "?zone=%3Cscript%3E")
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, "?zone=")
        self.assertContains(r, 'data-label="')

    def test_retired_helicopter_is_only_listed_on_its_own_page(self):
        retired = Aircraft.objects.filter(aircraft_type__category="helicopter", status="retired").first()
        if retired is None:
            self.skipTest("pas d'hélicoptère retiré dans la démo")
        self.assertIn(retired, neighbours(retired)["all"])
        other = Aircraft.objects.filter(aircraft_type__category="helicopter").exclude(status="retired").first()
        self.assertNotIn(retired, neighbours(other)["all"])

    def test_empty_fleet_list_spans_all_columns(self):
        r = self.c.get("/flotte/aeronefs/?q=aucun-appareil-de-ce-nom")
        self.assertContains(r, 'colspan="14"')
        r = self.c.get("/flotte/composants/?q=aucun-composant-de-ce-nom")
        self.assertNotContains(r, 'colspan="0"')


class DashboardPhotoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("load_demo", verbosity=0, stdout=io.StringIO())

    def test_photo_for_exact_types_only(self):
        from apps.fleet.heli3d import photo_for
        for code, mid in (("NH90", "nh90"), ("Super Puma", "super-puma"), ("H135", "h135"), ("H145", "h145")):
            p = photo_for(code)
            self.assertEqual(p["file"], f"ahmis/photos/{mid}.jpg")
            self.assertTrue(p["credit"] and p["url"].startswith("https://commons.wikimedia.org/"))
        self.assertIsNone(photo_for("H125"))
        self.assertIsNone(photo_for("A320"))

    def test_dashboard_shows_type_photo_with_credit(self):
        c = Client()
        c.force_login(get_user_model().objects.get(username="admin"))
        r = c.get("/")
        self.assertContains(r, "hero-photo")
        self.assertContains(r, "ahmis/photos/")
        self.assertContains(r, "commons.wikimedia.org")
