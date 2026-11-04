# 6. Le programme d'entretien (tâches)

**Compte : `camo`**

## Consulter

Menu **Programme d'entretien** : 33 tâches de démonstration. Filtrez par type (`H145`) ou par origine (MSM/MPD, ALS, AD, SB, exploitant).

Ouvrez **145-05-100 Visite 100 h / 12 mois** :

- **Intervalle** `100 FH / 1 an` : le **premier critère atteint** déclenche l'échéance.
- **Tolérance** `10 FH / 30 j` : au-delà de la butée mais dans la tolérance, le statut est « En tolérance » (orange foncé). Au-delà de la tolérance, il est « Dépassé » (rouge).
- **Étapes** : chaque ligne devient une étape à signer sur la task card.
- **Pièces requises** : elles alimentent le forecast (besoins mensuels en pièces).
- **Situation par aéronef** : dernière réalisation, butées, restes, date prévue pour chaque H145.

## Créer une tâche

1. **+ Créer** (ou depuis la fiche du type H125 : « Ajouter une tâche »).
2. Exemple :
    - Référence `125-25-180`, intitulé `Contrôle du kit de flottaison`, type H125
    - Nature : Contrôle fonctionnel ; ATA `25`
    - Intervalle : `180` jours ; tolérance : `15` jours
    - Charge : `2` h.h ; qualification B1
    - Étapes : `Déplier le kit` / `Contrôler la pression des bouteilles` / `Replier et plomber` (une par ligne)
3. **Enregistrer**, puis ajoutez une pièce requise (ex. `DEMO-ORING-12` × 2).

**Résultat** : la tâche s'applique immédiatement à tous les H125 (F-HDMA, F-HDMB). Laissez « effectivité » vide pour tous les aéronefs du type, ou cochez des immatriculations précises.

## Seuil (première échéance)

Un seuil différent de l'intervalle se renseigne dans « seuil FH/cycles/jours ». Exemple : première inspection à 1 200 FH, puis toutes les 500 FH.

## Tâche suivie sur un composant

Renseigner « P/N composant » rattache la tâche aux compteurs **du composant** et non à ceux de la cellule. Voir **125-72-500** (boroscopie Arriel 2D) : l'échéance suit le moteur, même s'il change d'hélicoptère.

## Tâche à contrôle indépendant

Cochez « contrôle indépendant requis » pour les tâches critiques (commandes de vol, fixations BTP…). La task card exigera alors une seconde signature par une autre personne certifiante (tutoriel 13).

## Révisions du programme

Chaque modification est tracée : bouton **Historique des révisions** sur la fiche tâche. Renseignez aussi « révision AMP ». Une tâche ne se supprime pas : décochez « active ».
