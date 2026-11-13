"""Contrôles communs des fichiers joints : extensions autorisées, taille, signature binaire."""
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _

MAX_UPLOAD_MB = 20
DOC_EXTENSIONS = ["pdf", "docx", "xlsx", "odt", "ods"]
SCAN_EXTENSIONS = ["pdf", "png", "jpg", "jpeg"]

# Signatures binaires attendues (début de fichier)
MAGIC = {
    "pdf": [b"%PDF-"],
    "png": [b"\x89PNG\r\n\x1a\n"],
    "jpg": [b"\xff\xd8\xff"],
    "jpeg": [b"\xff\xd8\xff"],
    "docx": [b"PK\x03\x04"], "xlsx": [b"PK\x03\x04"], "odt": [b"PK\x03\x04"], "ods": [b"PK\x03\x04"],
}


@deconstructible
class FileContentValidator:
    """Refuse un fichier trop volumineux ou dont le contenu ne correspond pas à l'extension."""

    def __init__(self, max_mb=MAX_UPLOAD_MB):
        self.max_mb = max_mb

    def __call__(self, f):
        size = getattr(f, "size", 0) or 0
        if size > self.max_mb * 1024 * 1024:
            raise ValidationError(_("Fichier trop volumineux (%(n)s Mo au maximum).") % {"n": self.max_mb})
        ext = f.name.rsplit(".", 1)[-1].lower() if "." in f.name else ""
        expected = MAGIC.get(ext)
        if not expected:
            return
        try:
            pos = f.tell()
            f.seek(0)
            head = f.read(16)
            f.seek(pos)
        except Exception:  # fichier déjà enregistré et absent : rien à contrôler
            return
        if isinstance(head, str):
            head = head.encode("latin-1", "ignore")
        if not any(head.startswith(m) for m in expected):
            raise ValidationError(_("Le contenu du fichier ne correspond pas à son extension."))

    def __eq__(self, other):
        return isinstance(other, FileContentValidator) and other.max_mb == self.max_mb


def doc_validators():
    return [FileExtensionValidator(DOC_EXTENSIONS), FileContentValidator()]


def scan_validators():
    return [FileExtensionValidator(SCAN_EXTENSIONS), FileContentValidator()]
