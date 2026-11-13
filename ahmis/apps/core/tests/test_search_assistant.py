from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.assistant import engine
from apps.assistant.kb import KB, LANGS
from apps.core.search import global_search
from apps.core.tests.factories import make_world


class SearchTests(TestCase):
    def setUp(self):
        self.w = make_world()

    def test_min_length_and_match(self):
        self.assertEqual(global_search(self.w["u_camo"], "F"), [])
        labels = [str(r[0]) for r in global_search(self.w["u_camo"], "F-TEST")]
        self.assertIn("Aéronef", labels)

    def test_permissions_respected(self):
        nobody = get_user_model().objects.create_user("nobody", password="x")
        self.assertEqual(global_search(nobody, "F-TEST"), [])

    def test_view_redirects_on_single_result(self):
        self.client.force_login(self.w["u_camo"])
        r = self.client.get("/recherche/", {"q": "F-TEST"})
        self.assertIn(r.status_code, (200, 302))


class AssistantTests(TestCase):
    def setUp(self):
        self.w = make_world()

    def test_kb_complete(self):
        self.assertEqual(len(KB), 20)
        for e in KB:
            for lang in LANGS:
                self.assertTrue(e[lang]["q"] and e[lang]["a"], (e["id"], lang))

    def test_matching_each_language(self):
        u = self.w["u_camo"]
        for q, lang, expected in [("comment saisir les heures de vol", "fr", "hours"),
                                  ("how do I record flight hours", "en", "hours"),
                                  ("commande d'achat fournisseur", "fr", "po"),
                                  ("Wie melde ich ein Ereignis", "de", "occurrence")]:
            best, _ = engine.answer(q, lang, u)
            self.assertIsNotNone(best, q)
            self.assertEqual(best["id"], expected, q)

    def test_unknown_question(self):
        best, sugg = engine.answer("xyzzy plugh", "fr", self.w["u_camo"])
        self.assertIsNone(best)
        self.assertEqual(sugg, [])

    def test_json_view(self):
        self.client.force_login(self.w["u_camo"])
        r = self.client.get("/assistant/", {"q": "<script>alert(1)</script>"})
        self.assertEqual(r["Content-Type"], "application/json")
        data = r.json()
        self.assertIsNone(data["answer"])
        self.assertTrue(data["fallback"])
        r = self.client.get("/assistant/", {"q": "AD SB à évaluer"})
        self.assertIsNotNone(r.json()["answer"])

    def test_assistant_requires_login(self):
        r = self.client.get("/assistant/", {"q": "x"})
        self.assertEqual(r.status_code, 302)
