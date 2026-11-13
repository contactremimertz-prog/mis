from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class QualityConfig(AppConfig):
    name = "apps.quality"
    label = "quality"
    verbose_name = _("Qualité : audits et documents")
