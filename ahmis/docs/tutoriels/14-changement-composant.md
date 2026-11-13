# 14. Changer un composant (dépose / pose)

**Comptes : `planif`, puis `b1`**

Situation de départ : sur F-HDMD (H145), le défaut « Vibrations anormales ressenties au palonnier » a une task card de rectification. Le magasin a déjà **réservé** pour elle une boîte Fenestron révisée, `DEMO-145FEN-01` S/N `DEMO-F1459` (demande AOG délivrée).

## 1. Démarrer la task card

1. Compte `b1` → menu **Task cards** → **Rectification DEF-… : Vibrations anormales…**.
2. **Démarrer la task card**.

## 2. Essayer une pièce non conforme

Dans le cadre **Changement de composant** :

- Composant déposé : `DEMO-145FEN-01 S/N DEMO-F1451` (position BTA)
- Motif : `Vibrations – dépose pour expertise`
- Composant posé : `DEMO-350TGB-01 S/N DEMO-T3599` (une BTA de **NH90**)
- Mot de passe → **Enregistrer le changement**

AHMIS refuse : « Pose refusée : P/N non applicable au type H145 ». **Rien n'a été modifié** : la boîte d'origine est toujours en place.

## 3. Changement conforme

Recommencez avec composant posé : `DEMO-145FEN-01 S/N DEMO-F1459`, la pièce réservée. La position reste vide : AHMIS reprend celle du composant déposé.

**Résultat** :

- **Configuration** de F-HDMD : en position BTA, la boîte S/N DEMO-F1459 est installée, avec son TSO et son TBO restant.
- **Fiche de la boîte déposée** (DEMO-F1451) : statut « Non utilisable (U/S) », motif de dépose, et dans sa traçabilité « back-to-birth » les dates et compteurs aéronef de pose **et** de dépose, avec la task card.
- **Fiche de la boîte posée** : un nouveau montage, avec les compteurs de pose.
- Une signature électronique décrit le mouvement.

## 4. Clôturer

Compte rendu `Remplacement de la boîte Fenestron, essais vibratoires conformes`, temps passé `5` → **Signer les travaux**.

Le défaut passe à **Rectifié**, avec l'action corrective reprise du compte rendu.

## Contrôles réalisés à chaque pose

| Contrôle | Exemple de refus |
|---|---|
| Statut de la pièce | Pièce en quarantaine, U/S ou réservée pour une autre task card |
| Certificat libératoire accepté | Pièce sans EASA Form 1 / 8130-3 |
| Potentiel restant | Limite de vie ou TBO atteinte |
| Applicabilité | P/N non applicable au type |
| Position libre | Position déjà occupée par le même P/N |

La pièce déposée peut repartir « U/S » (panne), « Quarantaine » (expertise) ou « Utilisable » (dépose de commodité). Elle garde tous ses compteurs.
