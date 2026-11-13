# 24. Scénario complet : de l'AD dépassée au CRS (F-HDMB)

Ce scénario enchaîne les rôles sur un cas réaliste. Durée : 20 minutes environ. Partez d'une démo réinitialisée.

**Situation** : sur le NH90 F-HDMB, l'AD `DEMO-AD-2026-0101` (barres de suspension BTP) est **dépassée** et la visite 100 h est **en tolérance**.

## Étape 1 – CAMO : constater et immobiliser (`camo`)

1. Tableau de bord → ligne F-HDMB → échéances dépassées.
2. **Échéances**, filtre F-HDMB : notez l'AD dépassée et la visite 100 h en tolérance.
3. Une AD dépassée interdit le vol : ouvrez F-HDMB → **Modifier** → statut **AOG (au sol)** → **Enregistrer**. La modification est tracée dans l'historique.

## Étape 2 – Planification (`planif`)

1. **Échéances**, filtre F-HDMB.
2. Cochez l'AD, la visite 100 h et la lubrification `N90-62-050`.
3. Work package : le WP existant **Visite 100 h** → **Créer les task cards**.
4. Sur le WP → **Modifier** : début aujourd'hui, fin demain, statut « Planifié ».

## Étape 3 – Exécution de la visite (`meca`)

1. Task card **Visite 100 h / 12 mois** → **Démarrer**.
2. Signez les 6 étapes (mot de passe à chaque fois).
3. Sortez l'outil `TENS-01` (tensiomètre), puis restituez-le.
4. Compte rendu `Visite 100 h effectuée, RAS`, 7 h.h → **Signer les travaux** : la task card est clôturée.
5. Faites de même pour la **lubrification**.

## Étape 4 – Exécution de l'AD (`b1`)

1. Task card **Inspection des barres de suspension BTP (AD)** → **Démarrer**, puis signez les 4 étapes.
2. Pendant l'inspection, une anomalie : cadre **Signaler une constatation**, `Trace de frottement sur barre avant gauche, dans les tolérances du manuel`. Un défaut et une task card de rectification sont créés.
3. Revenez sur la task card AD → compte rendu `Inspection conforme à l'AD, constatation traitée sur task card dédiée` → **Signer les travaux**. Elle passe en « attente contrôle » : la tâche est critique.

## Étape 5 – Constatation (`b1`)

Ouvrez la task card de rectification → **Démarrer** → compte rendu `Mesure de la trace : conforme, protection appliquée` → **Signer les travaux**. Le défaut est **rectifié**.

## Étape 6 – Contrôle indépendant (`certc`)

Task card AD → **Signer le contrôle** (observations `Conforme`). Elle est clôturée.

**À vérifier** (compte `camo`) :

- **AD / SB** → `DEMO-AD-2026-0101` → F-HDMB : statut **« Applicable – répétitive en cours »**, avec la date et les compteurs de conformité ;
- **Échéances** F-HDMB : l'AD est « OK », prochaine butée dans 110 FH ; la visite 100 h est « OK ».

## Étape 7 – CRS (`b1`)

WP → cadre CRS : plus aucun blocage → mot de passe → **Signer le CRS**. Le WP est **Remis en service** et verrouillé.

## Étape 8 – Retour en exploitation (`camo`)

Le CRS a remis F-HDMB **En exploitation** automatiquement (il le fait pour un aéronef « En maintenance » ou « AOG »). Vérifiez le **tableau de bord** : F-HDMB n'a plus d'échéance dépassée, mais le moyeu rotor (LLP) reste à planifier.

## Étape 9 – Contrôle qualité (`qualite`)

- **Signatures électroniques** : toutes les signatures du scénario, chacune « ✓ intègre ».
- **Journal d'audit**, recherche `F-HDMB` : la mise au sol, la création du WP, les task cards, les statuts…
- **Imprimer le dossier** du WP : le dossier papier complet avec le CRS.

Bravo, vous avez parcouru toute la chaîne CAMO → Part-145 → logistique → qualité.
