"""Parcours de toutes les pages, sur le jeu de démonstration, dans les quatre langues et pour chaque rôle."""
import tempfile
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase, override_settings

from apps.core.demo_accounts import DEMO_ACCOUNTS

from .crawl import crawl, object_urls, static_urls


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="ahmis-test-media-"))
class SmokeCrawlTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("load_demo", verbosity=0, stdout=open("/dev/null", "w"))

    def test_all_pages_all_languages_all_roles(self):
        urls = static_urls() + object_urls()
        self.assertGreater(len(urls), 80)
        for username, *_ in DEMO_ACCOUNTS:
            c = Client(raise_request_exception=False)
            c.force_login(get_user_model().objects.get(username=username))
            errors = crawl(c, urls)
            self.assertEqual(errors, [], f"{username} : {errors[:5]}")

    def test_dashboard_is_translated(self):
        c = Client()
        c.force_login(get_user_model().objects.get(username="admin"))
        for lang, title in [("fr", "Tableau de bord"), ("en", "Dashboard"), ("es", "Panel de control"), ("de", "Übersicht")]:
            c.cookies[settings.LANGUAGE_COOKIE_NAME] = lang
            self.assertContains(c.get("/"), f'<h1 class="sr-only">{title}</h1>', html=False)

    def test_quality_alert_on_dashboard(self):
        c = Client()
        c.force_login(get_user_model().objects.get(username="qualite"))
        r = c.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertRegex(r.content.decode(), r'class="todo-item[^>]*><span class="l">Qualité</span>\s*<b>\d+ constats? ')
