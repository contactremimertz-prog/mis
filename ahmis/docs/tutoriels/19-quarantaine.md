# 19. Quarantaine, pièces suspectes et péremption

**Compte : `magasin`**

Menu **Quarantaine** : toutes les pièces bloquées.

## Ce que contient la démo

| Pièce | Situation |
|---|---|
| Démarreur-génératrice `DEMO-G1666` | **Pièce suspecte (SUP)** : plaque d'identification non conforme, certificat rejeté |
| Moteur RTM322 `DEMO-E21099` | **U/S** : déposé pour dépassement de température |
| Lot d'huile `LOT-OIL-2502` (magasin ligne) | Utilisable mais **périmé** : listé dans l'encadré orange |

## 1. Tenter de libérer une pièce suspecte

1. Ouvrez `DEMO-G1666` → cadre « Changer le statut » : nouveau statut « En stock – utilisable », emplacement `MAG-PRINC`, motif `Test` → **Changer le statut**.
2. AHMIS refuse : « Remise en stock utilisable impossible sans certificat libératoire accepté ».

Une pièce suspecte reste en quarantaine jusqu'à la décision qualité. Si la décision est le rebut, passez le statut à **Rebuté** avec le motif `SUP confirmée – déclaration à l'autorité`. La pièce reste dans AHMIS pour la traçabilité, mais ne peut plus jamais être utilisée.

## 2. Envoyer un moteur en révision

`DEMO-E21099` → statut « En réparation / révision », motif `Envoyé à l'atelier moteur, BL 4471`. À son retour, réceptionnez-le avec son nouveau Form 1 (tutoriel 17).

## 3. Traiter un lot périmé

Dans l'encadré orange, cliquez `LOT-OIL-2502` → statut « Périmé », motif `Date dépassée` → **Enregistrer**. Le lot n'est plus proposé à la délivrance, ce qui était déjà le cas : AHMIS refuse toute délivrance d'un lot dont la date est dépassée.

## 4. Mettre une pièce en quarantaine

Sur n'importe quel composant en stock, choisissez le statut « Quarantaine » : sans emplacement précisé, il est rangé automatiquement en `QUAR`.
