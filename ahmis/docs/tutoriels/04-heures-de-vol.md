# 4. Saisir les heures de vol et les cycles

**Compte : `planif` (ou `b1`)**

Les heures et atterrissages (cycles) viennent des comptes rendus matériel (techlog / CRM).

## Saisie

1. Tableau de bord → **Saisir des heures de vol** (ou menu **Heures de vol** → **+ Créer**).
2. Aéronef `F-HDMA`, date aujourd'hui, heures `1.8`, cycles `5`, référence `CRM MA-TEST`.
3. **Enregistrer**.

Un message affiche les nouveaux totaux.

## Ce que fait AHMIS

- Il incrémente les compteurs de la **cellule**.
- Il incrémente les compteurs de **tous les composants installés** : TSN/CSN (depuis neuf) et TSO/CSO (depuis révision).
- Il recalcule immédiatement les échéances.

**À vérifier** :

1. Ouvrez F-HDMA : les heures totales ont augmenté de 1,8.
2. Dans « Configuration installée », le TSO de la BTP a aussi augmenté de 1,8, et son « TBO restant » a diminué d'autant.
3. Dans les échéances, le « Reste FH » de la visite 100 h a baissé de 1,8.

## Contrôles de saisie

- Plus de 24 h dans une journée est refusé.
- Une date future est refusée.
- Une saisie n'est jamais modifiable : une erreur se corrige par une nouvelle saisie justifiée, et l'historique reste complet (menu **Heures de vol**).

## Utilisation prévue et dates prévisionnelles

Sur la fiche aéronef, « utilisation prévue » (FH/jour, cycles/jour) sert à convertir les heures restantes en **date prévue**. Exemple : 12 FH restantes à 1,6 FH/jour donnent une échéance dans 7 jours. Modifiez cette valeur (bouton **Modifier** de l'aéronef, compte `camo`) pour voir les dates prévues se déplacer.
