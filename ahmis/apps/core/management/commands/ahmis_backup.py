"""Sauvegarde AHMIS (Windows et Linux) : base de données + pièces jointes, avec rotation.

    python manage.py ahmis_backup                 # dans AHMIS_DATA_DIR/backups
    python manage.py ahmis_backup --dest D:\\Sauvegardes --keep 60

- SQLite : copie à chaud cohérente (API de sauvegarde SQLite), pas besoin d'arrêter AHMIS.
- Autres SGBD : export JSON portable (dumpdata) ; utilisez EN PLUS les outils natifs du SGBD (pg_dump, RMAN...).
"""
import shutil
import sqlite3
import zipfile
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand, call_command
from django.db import connection


class Command(BaseCommand):
    help = "Sauvegarde la base et les pièces jointes AHMIS."

    def add_arguments(self, parser):
        parser.add_argument("--dest", default=None, help="Dossier de destination")
        parser.add_argument("--keep", type=int, default=30, help="Nombre de sauvegardes conservées")

    def handle(self, *args, **opts):
        dest = Path(opts["dest"] or Path(settings.DATA_DIR) / "backups")
        dest.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        target = dest / f"ahmis-{stamp}.zip"
        work = dest / f".tmp-{stamp}"
        work.mkdir()
        try:
            db = settings.DATABASES["default"]
            if db["ENGINE"].endswith("sqlite3"):
                src = sqlite3.connect(db["NAME"])
                out = sqlite3.connect(work / "ahmis.sqlite3")
                with out:
                    src.backup(out)
                src.close()
                out.close()
            else:
                connection.ensure_connection()
            # Export JSON portable dans tous les cas (restauration vers un autre SGBD possible)
            with open(work / "ahmis.json", "w", encoding="utf-8") as fh:
                call_command("dumpdata", natural_foreign=True, exclude=["contenttypes", "auth.permission", "sessions"],
                             indent=None, stdout=fh)
            with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
                for f in work.iterdir():
                    z.write(f, f.name)
                media = Path(settings.MEDIA_ROOT)
                if media.is_dir():
                    for f in media.rglob("*"):
                        if f.is_file():
                            z.write(f, Path("media") / f.relative_to(media))
        finally:
            shutil.rmtree(work, ignore_errors=True)
        old = sorted(dest.glob("ahmis-*.zip"))[:-opts["keep"]] if opts["keep"] > 0 else []
        for f in old:
            f.unlink()
        size = target.stat().st_size / 1024 / 1024
        self.stdout.write(self.style.SUCCESS(f"Sauvegarde : {target} ({size:.1f} Mo), {len(old)} ancienne(s) supprimée(s)."))
