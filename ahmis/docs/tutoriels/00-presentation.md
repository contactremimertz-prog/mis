# 0. Présentation d'AHMIS

AHMIS (**A**ircraft & **H**elicopter **M**aintenance **I**nformation **S**ystem) couvre trois métiers sur une base de données unique :

| Module | Pour qui | Fonctions principales |
|---|---|---|
| **Navigabilité (CAMO)** | Ingénieur CAMO | Flotte, configuration, heures de vol, programme d'entretien et sa revue annuelle, AD/SB, modifications et réparations, LLP/TBO, échéances, forecast, ARC, prorogation de report, transfert de dossiers |
| **Entretien (Part-145)** | Planificateur, mécaniciens, certifiants | Planning, work packages, task cards, signatures, contrôle indépendant, défauts/MEL, changement de composant, CRS, expérience récente et formations bloquantes, comptes rendus d'événements |
| **Logistique** | Magasinier | Réception avec Form 1 selon la classe d'article, stock, péremption, quarantaine, rebut et mutilation, demandes de pièces, outillage et étalonnage |
| **Qualité** | Responsable qualité | Journal d'audit, signatures électroniques, personnel et autorisations, comptes rendus d'événements, conservation des enregistrements |

## Les données de démonstration

La démo charge une flotte mixte de 6 aéronefs exploités, à dominante **Airbus Helicopters**, plus un hélicoptère retiré du service :

| Immat. | Type | Situation de départ (pour les tutoriels) |
|---|---|---|
| F-HDMA | NH90 | Visite 100 h et AD à planifier, BTP proche de son TBO |
| F-HDMB | NH90 | **AD dépassée**, visite 100 h en tolérance, moyeu rotor (LLP) proche de sa limite, WP planifié vide |
| F-HDMC | H135 (HEMS) | Défaut reporté MEL cat. C, bulletin ASB ouvert, moyeu rotor (LLP) suivi en cycles |
| F-HDMD | H145 (HEMS) | **En maintenance** : work package en cours avec task cards à tous les stades |
| F-HDME | Super Puma | ARC qui expire dans 20 jours |
| F-HDMF | ATR 72-600 | AD à évaluer, tâche calendaire dépassée |
| F-HDMZ | NH90 | **Retiré du service** il y a 20 mois, dossier transféré à l'acquéreur (tutoriel 30) |

Elle contient aussi : des revues du programme dans tous les états (tutoriel 27), trois comptes rendus d'événements (tutoriel 29), une pièce rebutée (tutoriel 31) et un ancien salarié dont le dossier est arrivé en fin de conservation (tutoriel 30).

> ⚠️ **Toutes les références (tâches, P/N, AD, intervalles, limites) sont fictives** et préfixées « DEMO ». Elles servent uniquement à illustrer le logiciel. En exploitation, les données viennent des documents constructeur (MSM, MRI, ALS…) et des autorités.

## Comptes de démonstration

Mot de passe commun : **`Ahmis2026!`**

| Identifiant | Personne | Rôle | Peut signer |
|---|---|---|---|
| `admin` | — | Administrateur (tous droits) | Non (pas de fiche personnel) |
| `camo` | Julien MOREAU | Ingénieur CAMO | — |
| `planif` | Nadia ROUX | Planificateur | — |
| `meca` | Lucas MARTIN | Mécanicien non certifiant | Exécution (hélicoptères) |
| `b1` | Claire DUBOIS | Certifiant B1 | Exécution, contrôle, CRS, report de défaut |
| `b2` | Karim BENALI | Certifiant B2 | Idem (hélicoptères) |
| `certc` | Sophie LAMBERT | Certifiant C | Idem + CRS de grande visite |
| `magasin` | Thomas PETIT | Magasinier | — |
| `qualite` | Isabelle GARNIER | Responsable qualité | — |

Les droits d'**accès aux écrans** dépendent du rôle. Les droits de **signature** dépendent en plus des autorisations individuelles de la personne (type d'aéronef, catégorie, validité) : AHMIS les vérifie à chaque signature.

## Ordre conseillé des tutoriels

1. Installation (tutoriel 1), puis prise en main (2).
2. Côté CAMO : 3 à 10.
3. Côté atelier : 11 à 16.
4. Côté magasin : 17 à 20.
5. Qualité et technique : 21 à 23.
6. Le **tutoriel 24** enchaîne tout dans un scénario complet, de l'échéance au CRS.
7. Règles de gestion réglementaires : **25 à 31** (tolérances, modifications, revue du programme, expérience récente, comptes rendus d'événements, conservation et transfert, prorogation de report, rebut, classes d'articles).
8. La **matrice de conformité** (32) relie chaque exigence EASA aux fonctions d'AHMIS.

Astuce : pour repartir de zéro à tout moment, lancez `reinitialiser_demo` (voir tutoriel 1).
