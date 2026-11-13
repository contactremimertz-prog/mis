# 5. Composants, pièces à vie limitée (LLP) et TBO

**Compte : `camo`**

## Références articles (P/N)

Menu **Références P/N** → cliquez `DEMO-350STR-01` (moyeu rotor principal NH90). Une référence porte :

- le suivi au numéro de série (obligatoire pour une LLP ou une pièce à TBO) ;
- les **limites de vie** (LLP), depuis neuf : heures, cycles et/ou jours ;
- le **TBO**, potentiel entre révisions : heures, cycles et/ou jours ;
- les types d'aéronefs applicables (une pose sur un autre type est refusée) ;
- les P/N interchangeables (acceptés lors d'une demande de pièce).

AHMIS refuse une LLP sans limite, et une LLP ou pièce à TBO non sérialisée.

## Fiche composant : le moyeu rotor de F-HDMB

1. Recherche globale : `DEMO-S3502`.
2. La fiche affiche :
    - les compteurs TSN / CSN / TSO / CSO ;
    - **Potentiels et limites de vie** : limite, consommé, restant, et une barre qui passe à l'orange à 90 % ;
    - les certificats libératoires ;
    - la **traçabilité « back-to-birth »** : chaque montage (aéronef, position, compteurs à la pose et à la dépose, motif, task card).

**À vérifier** : il reste environ 40 FH sur la limite de 5 000 FH. Dans **Échéances**, la ligne « LLP » de F-HDMB est « À planifier ».

## Lecture de la configuration d'un aéronef

Ouvrez F-HDMA, section **Configuration installée** : pour chaque position (MOT 1, MOT 2, BTP, BTA, MRH, PALE 1-4…), le composant, ses compteurs et ce qui lui reste sur chaque limite.

## LLP et TBO dans les échéances

AHMIS génère automatiquement une échéance :

- **LLP** pour chaque pièce à vie limitée installée (premier critère atteint entre heures, cycles et calendrier) ;
- **TBO** pour chaque pièce à potentiel.

Elles apparaissent dans les échéances, le forecast et le planning, et peuvent être ajoutées à un work package : une task card « dépose/repose » est alors générée.

## Une pièce en butée est inutilisable

Une pièce dont une limite est atteinte ne peut être ni posée, ni délivrée, ni remise « utilisable ». Le test automatique `test_expired_life_part_refused` le vérifie.
