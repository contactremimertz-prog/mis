# 18. Demandes de pièces

**Comptes : `meca`, puis `magasin`**

## 1. Demander une pièce depuis une task card

1. Compte `meca` → task card **Visite 100 h / 12 mois** de F-HDMD.
2. Cadre **Pièces** → « Demander une pièce » : P/N `DEMO-ORING-12`, quantité `2`, priorité « Urgent » → **Demander**.

Une demande `DP-AAAA-NNNN` est créée au statut **Demandée**. Elle apparaît dans le tableau de bord (« Demandes de pièces ») et dans le menu **Demandes de pièces**.

## 2. Délivrer (magasin)

1. Compte `magasin` → menu **Demandes de pièces** → filtre « Demandée ».
2. Ouvrez la demande de **bouchon magnétique** `DEMO-CHIP-01` (créée par la démo).
3. Lot à délivrer : `LOT-CH-09` → **Délivrer**.

**Résultat** :

- la demande est **Délivrée** ;
- le stock du lot baisse de 1, avec un mouvement de sortie rattaché à la task card ;
- sur la task card, la ligne « Consommé » apparaît (traçabilité pièce → travaux).

Pour une **pièce sérialisée**, le composant passe à « Réservé (task card) ». Il ne peut alors être posé que par cette task card (tutoriel 14).

## Contrôles à la délivrance

Seules sont proposées les pièces **utilisables** du P/N demandé ou d'un P/N **interchangeable**. À la délivrance, AHMIS revérifie :

- le certificat accepté ;
- la péremption (un lot périmé est refusé) ;
- le potentiel restant (pour une pièce sérialisée) ;
- la quantité disponible.

## Annuler

Une demande inutile s'annule depuis sa fiche (**Annuler la demande**). Une task card ne peut pas être signée tant qu'une demande reste « Demandée ».

## Stock mini

Dans **Stock consommables**, une quantité inférieure ou égale au stock mini s'affiche en rouge (ex. joints toriques `LOT-OR-077`). **Inventaire** permet un ajustement justifié (+/−), tracé comme mouvement de stock.
