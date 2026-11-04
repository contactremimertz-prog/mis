# 8. Consignes de navigabilité (AD) et bulletins service (SB)

**Compte : `camo`**

## Le cycle de vie d'une consigne

1. **Enregistrer** la consigne : numéro, émetteur, date d'entrée en vigueur, types et/ou P/N concernés.
2. AHMIS crée automatiquement un statut **« À évaluer »** pour chaque aéronef potentiellement concerné (même type, ou P/N concerné installé).
3. La CAMO **évalue** chaque aéronef :
    - **Non applicable** : la justification est obligatoire ;
    - **Applicable – à réaliser** : il faut une **tâche de suivi** ;
    - **Appliquée** : la date de conformité est obligatoire.
4. La tâche de suivi apparaît dans les échéances. Le délai compte **à partir de la date d'entrée en vigueur**.
5. À la clôture de la task card, le statut passe à **Appliquée** (consigne unique) ou **Répétitive en cours**.

## Exercice 1 : évaluer l'AD ATR

1. Menu **AD / SB** → `DEMO-AD-2026-0177` (ATR 72, ferrures de volet).
2. Ligne F-HDMF : statut **À évaluer** → **Évaluer**.
3. Statut « Applicable – à réaliser », justification `MSN 1801 dans la plage d'applicabilité` → **Enregistrer**.
4. Bouton **Créer la tâche de suivi (ATR72-600)** : la référence, l'intitulé et l'action requise sont pré-remplis.
5. Renseignez le **seuil cycles** `3000` (délai depuis l'entrée en vigueur) et la charge `4`, puis enregistrez.

**Résultat** : dans **Échéances**, F-HDMF a une nouvelle ligne avec une butée de cycles égale aux cycles à l'entrée en vigueur + 3 000.

## Exercice 2 : déclarer une non-applicabilité

1. `DEMO-SB-145-24-010` (SB optionnel H145) → F-HDMD → **Évaluer**.
2. Choisissez « Non applicable » **sans** justification → **Enregistrer** : refusé.
3. Ajoutez `SB optionnel non retenu par l'exploitant – décision CAMO du jj/mm` → **Enregistrer**.

## Exercice 3 : suivre une AD répétitive

`DEMO-AD-2026-0101` (barres de suspension BTP H125) est suivie par une tâche avec un seuil de 50 FH et un intervalle de 110 FH :

- sur **F-HDMA**, elle a été réalisée : statut « Répétitive en cours », prochaine échéance 110 FH plus tard ;
- sur **F-HDMB**, elle n'a jamais été faite : **Dépassé**. Le tutoriel 24 la traite.

## Vue d'ensemble

Bouton **Statut par aéronef** dans la liste AD/SB : toutes les évaluations, avec filtres par statut et par aéronef. C'est le document de base de la revue de navigabilité.
