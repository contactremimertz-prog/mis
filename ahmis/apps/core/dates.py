"""Petits utilitaires de dates partagés."""
import calendar
from datetime import date, datetime


def add_months(d, months):
    """Ajoute ``months`` mois (négatif = retire) à une date, en bornant le jour à la fin du mois."""
    if isinstance(d, datetime):
        d = d.date()
    m = d.month - 1 + months
    y, m = d.year + m // 12, m % 12 + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))
