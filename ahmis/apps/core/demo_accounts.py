"""Comptes de démonstration (créés par « python manage.py load_demo »)."""

DEMO_PASSWORD = "Ahmis2026!"

# (identifiant, rôle affiché, groupe, superutilisateur)
DEMO_ACCOUNTS = [
    ("admin", "Administrateur (tous droits)", None, True),
    ("camo", "Ingénieur CAMO", "Ingénieur CAMO", False),
    ("planif", "Planificateur", "Planificateur", False),
    ("meca", "Mécanicien non certifiant", "Mécanicien", False),
    ("b1", "Certifiant B1", "Certifiant", False),
    ("b2", "Certifiant B2", "Certifiant", False),
    ("certc", "Certifiant C (base)", "Certifiant", False),
    ("magasin", "Magasinier", "Magasinier", False),
    ("qualite", "Responsable qualité", "Responsable qualité", False),
]
