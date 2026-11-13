from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from apps.core.views import DOCS_DIR, TRANSLATED_DOCS


class HelpTranslationTests(TestCase):
    def setUp(self):
        self.c = Client()
        self.c.force_login(get_user_model().objects.create_user("lecteur", password="x"))

    def test_every_tutorial_is_translated(self):
        slugs = sorted(p.stem for p in DOCS_DIR.glob("*.md"))
        for lang in TRANSLATED_DOCS:
            missing = [s for s in slugs if not (DOCS_DIR / lang / f"{s}.md").is_file()]
            self.assertEqual(missing, [], lang)

    def test_page_follows_site_language(self):
        slug = sorted(DOCS_DIR.glob("*.md"))[0].stem
        for lang in TRANSLATED_DOCS:
            self.c.cookies[settings.LANGUAGE_COOKIE_NAME] = lang
            title = (DOCS_DIR / lang / f"{slug}.md").read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()
            r = self.c.get(f"/aide/{slug}/")
            self.assertContains(r, title)
            self.assertNotContains(r, "pas encore traduit")
        self.c.cookies[settings.LANGUAGE_COOKIE_NAME] = "fr"
        fr_title = (DOCS_DIR / f"{slug}.md").read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()
        self.assertContains(self.c.get(f"/aide/{slug}/"), fr_title)

    def test_unknown_slug_is_404(self):
        self.assertEqual(self.c.get("/aide/en/").status_code, 404)
        self.assertEqual(self.c.get("/aide/inconnu/").status_code, 404)
