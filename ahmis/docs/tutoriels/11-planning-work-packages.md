# 11. Planning et work packages

**Compte : `planif`**

Un **work package (WP)** regroupe les travaux d'un aéronef pour une immobilisation : dates, station, type de visite et task cards.

## Le planning hangar

Menu **Planning** : une ligne par aéronef, une colonne par jour (8 semaines).

- Les **barres** sont les WP : bleu = planifié, orange = en cours, vert = remis en service.
- Les **points** sont les échéances : rouge = dépassée, orange = à planifier, gris = prévue.
- Survolez un point ou une barre pour le détail ; cliquez pour ouvrir.
- Boutons « ← 4 semaines / 4 semaines → » pour naviguer.

**Repérez** : le WP en cours de F-HDMD, le WP planifié de F-HDMB dans 5 jours, et les points rouges de F-HDMB (AD dépassée).

## Créer un work package

1. **Nouveau work package**.
2. Aéronef `F-HDMA`, intitulé `Visite 100 h`, type « Visite périodique », station `Base Alpes`, du lundi prochain au mardi, statut « Planifié ».
3. **Enregistrer** : le numéro `WP-AAAA-NNNN` est attribué automatiquement.

## Remplir le work package

Sur la fiche du WP :

1. **Ajouter des éléments dus** : la liste propose les échéances de l'aéronef jusqu'à 30 jours après la fin du WP, sauf celles déjà planifiées. Cochez `N90-05-100`, `DEMO-AD-2026-0101` et `N90-24-365` → **Créer les task cards sélectionnées**.
2. **Ajouter une tâche du programme** : choisissez une tâche non due, par exemple `N90-63-200`, pour l'anticiper.
3. **Travail additionnel** : une task card hors programme, par exemple `Remplacement ampoule phare d'atterrissage`, ATA `33`, 0,5 h.h.

**Résultat** :

- chaque task card reprend l'intitulé, l'ATA, la zone, la qualification, la charge et les **étapes** de la tâche ;
- la carte « Charge prévue » du WP fait le total des heures-homme ;
- les éléments ajoutés disparaissent de la liste « éléments dus » (pas de doublon).

## Imprimer

**Imprimer le dossier** : le récapitulatif du WP et le CRS au format papier. Chaque task card a aussi son bouton **Imprimer**, pour les ateliers qui travaillent sur papier.

## Statuts d'un WP

| Statut | Passage |
|---|---|
| Brouillon / Planifié | À la création |
| En cours | Automatiquement au démarrage de la 1re task card (l'aéronef passe « En maintenance ») |
| Remis en service | À la signature du CRS (tutoriel 16) : le WP est alors **verrouillé** |
| Annulé | Manuellement, par « Modifier » |
