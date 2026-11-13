"""Transfert des enregistrements (M.A.307) : archive complète, intégrité, contrôle d'un dossier reçu."""
import io
import json
import shutil
import tempfile
import zipfile

from django.test import TestCase, override_settings

from apps.camo import dossier
from apps.camo.models import TransferRecord
from apps.core.tests.factories import make_world

MEDIA = tempfile.mkdtemp(prefix="ahmis-test-media-")


@override_settings(MEDIA_ROOT=MEDIA)
class TransferTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        self.w = make_world()

    def test_archive_contents_and_integrity(self):
        raw, digest, manifest = dossier.build_archive(self.w["ac"])
        z = zipfile.ZipFile(io.BytesIO(raw))
        names = set(z.namelist())
        for n in ("manifest.json", "dossier.json", "synthese.html", "csv/heures_cycles.csv", "csv/consignes_navigabilite.csv"):
            self.assertIn(n, names)
        data = json.loads(z.read("dossier.json"))
        self.assertEqual(data["sections"]["aeronef"][0]["registration"], "F-TEST")
        self.assertIn("F-TEST", z.read("synthese.html").decode())
        m, problems = dossier.verify_archive(io.BytesIO(raw))
        self.assertEqual(problems, [])

    def test_tampered_archive_detected(self):
        raw, _, _ = dossier.build_archive(self.w["ac"])
        src = zipfile.ZipFile(io.BytesIO(raw))
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w") as z:
            for n in src.namelist():
                content = src.read(n)
                if n == "dossier.json":
                    content = content.replace(b"F-TEST", b"F-FAKE")
                z.writestr(n, content)
        _, problems = dossier.verify_archive(io.BytesIO(out.getvalue()))
        self.assertTrue(any("dossier.json" in p for p in problems))
        _, problems = dossier.verify_archive(io.BytesIO(b"pas un zip"))
        self.assertTrue(problems)

    def test_outgoing_transfer_via_ui(self):
        self.client.force_login(self.w["u_camo"])
        r = self.client.post("/camo/transferts/nouveau/", {"aircraft": self.w["ac"].pk, "direction": "out",
                                                          "transfer_date": "2026-01-10", "counterparty": "CAMO Nouvelle", "reason": "Vente"})
        self.assertEqual(r.status_code, 302, r.content[:800])
        t = TransferRecord.objects.get()
        self.assertTrue(t.archive_sha256 and t.archive)
        dl = self.client.get(f"/camo/transferts/{t.pk}/archive.zip")
        self.assertEqual(dl.status_code, 200)
        self.assertEqual(self.client.get(f"/media/{t.archive.name}").status_code, 404)  # jamais via le média générique
        # Accusé de réception
        r = self.client.post(t.get_absolute_url(), {"acknowledged_on": "2026-01-12", "acknowledged_by": "M. Dupont, CAMO Nouvelle"})
        self.assertEqual(r.status_code, 302)
        t.refresh_from_db()
        self.assertEqual(str(t.acknowledged_on), "2026-01-12")
        # Un mécanicien n'a pas accès aux dossiers de transfert
        self.client.force_login(self.w["u_meca"])
        self.assertEqual(self.client.get(f"/camo/transferts/{t.pk}/archive.zip").status_code, 403)

    def test_incoming_transfer_verified(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        raw, _, _ = dossier.build_archive(self.w["ac"])
        self.client.force_login(self.w["u_camo"])
        r = self.client.post("/camo/transferts/nouveau/", {"aircraft": self.w["ac"].pk, "direction": "in", "transfer_date": "2026-01-10",
                                                          "counterparty": "Ancienne CAMO", "archive": SimpleUploadedFile("d.zip", raw)})
        self.assertEqual(r.status_code, 302, r.content[:800])
        t = TransferRecord.objects.get()
        self.assertTrue(t.integrity_ok, t.verification)
        # Archive sans fichier pour un entrant : refusée
        r = self.client.post("/camo/transferts/nouveau/", {"aircraft": self.w["ac"].pk, "direction": "in", "transfer_date": "2026-01-10",
                                                          "counterparty": "X"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(TransferRecord.objects.count(), 1)
