# AHMIS – Aircraft & Helicopter Maintenance Information System

Système d'information de maintenance couvrant la **CAMO**, le **Part-145** et la **logistique**, indépendant du SGBD.

## Démarrage rapide (démo)

- **Windows** : double-cliquer sur `demarrer.bat`
- **macOS / Linux** : `./demarrer.sh`

Prérequis : Python 3.10+. Le navigateur s'ouvre sur http://127.0.0.1:8000.
Comptes de démonstration : `admin`, `camo`, `planif`, `meca`, `b1`, `b2`, `certc`, `magasin`, `qualite`, mot de passe `Ahmis2026!`.

Remise à zéro de la démo : `reinitialiser_demo.bat` / `./reinitialiser_demo.sh`.

## Tutoriels

33 tutoriels pas à pas dans `docs/tutoriels/`, également consultables dans l'application (menu **Aide > Tutoriels**). Commencez par `00-presentation.md`. Le tutoriel `24-scenario-complet.md` enchaîne tous les modules, les tutoriels 25 à 31 détaillent les règles de gestion réglementaires, et `32-matrice-conformite.md` relie les exigences EASA aux fonctions.

## Fonctions

| CAMO | Part-145 | Logistique | Qualité |
|---|---|---|---|
| Flotte, types, configuration | Planning hangar | Réception avec Form 1 / 8130-3 | Journal d'audit (champ par champ) |
| Heures de vol et cycles | Work packages | Stock, péremption, stock mini | Signatures électroniques (SHA-256) |
| Programme d'entretien | Task cards générées avec étapes | Quarantaine, pièces suspectes | Personnel, licences, autorisations |
| AD / SB par aéronef | Signature des étapes et des travaux | Demandes de pièces | Formations obligatoires, expérience récente |
| LLP, TBO, back-to-birth | Contrôle indépendant | Outillage et étalonnage | Comptes rendus d'événements (376/2014) |
| Échéances, forecast, ARC, tolérances non cumulatives | Défauts, MEL, constatations | Classes d'articles (145.A.42) | Conservation des enregistrements |
| Modifications et réparations, revue du programme | Changement de composant, CRS | Rebut et mutilation | |
| Prorogation de report (RIE), transfert de dossiers | | Fournisseurs acceptés, commandes d'achat, réception rattachée au certificat | Audits internes et constats (niveaux 1 / 2, observation) |
| Dossiers Part-21 (STC, DOA, EASA) | | | Documents maîtrisés (révision signée, double regard) |

Transverse : interface en **français, anglais, espagnol et allemand** (sélecteur en en-tête), **recherche globale** filtrée par les droits, **assistant** (bouton « ? ») limité à 20 réponses validées, sans génération de texte.

## Architecture

- **Python / Django 5.2**. Persistance exclusivement par l'ORM : SQLite, PostgreSQL, MySQL/MariaDB, Oracle ou SQL Server, au choix par variables d'environnement (voir `docs/tutoriels/23-changer-de-sgbd.md`).
- Aucune dépendance web externe (CSS local) : fonctionne hors ligne.
- Applications :
  - `apps/core` : audit, signatures, rôles, numérotation, tableau de bord, aide
  - `apps/fleet` : types, aéronefs, utilisation, P/N, composants, montages
  - `apps/camo` : programme, AD/SB, réalisations, ARC, **moteur de calcul des échéances et du forecast** (`apps/camo/services.py`)
  - `apps/part145` : personnel, autorisations, WP, task cards, défauts, **règles de signature** (`apps/part145/services.py`)
  - `apps/logistics` : magasins, certificats, stock, demandes, outillage, fournisseurs et commandes (`apps/logistics/purchasing.py`)
  - `apps/quality` : audits internes, constats, documents maîtrisés et révisions
  - `apps/assistant` : base de 20 réponses validées en 4 langues (`apps/assistant/kb.py`)
  - `locale/` : catalogues de traduction EN / ES / DE (régénérer avec `makemessages`, puis `compilemessages`)

## Tests

```
python manage.py test apps
```

121 tests couvrent les règles critiques : calcul « premier critère atteint », tolérances non cumulatives, seuils, délais d'AD, compteurs des composants, LLP/TBO, forecast, autorisations, contrôle indépendant, CRS, contrôles de pose, quarantaine, outillage, péremption, audit, intégrité des signatures, le parcours web avec ressaisie du mot de passe, l'expérience récente, la revue du programme, la conservation, les comptes rendus d'événements, le transfert de dossiers, la prorogation de report, le rebut et les classes d'articles, les audits internes, les documents maîtrisés, les dossiers Part-21, les commandes d'achat, la recherche, l'assistant, et un parcours de toutes les pages dans les quatre langues pour chaque rôle de démonstration.

## Avertissement

Les données de démonstration (tâches, P/N, AD, intervalles, limites) sont **fictives**. AHMIS est un outil : la conformité réglementaire est démontrée par l'organisme qui l'utilise (procédures CAME/MOE, validation, acceptation par l'autorité). Voir la matrice de conformité.
