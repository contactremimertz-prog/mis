# 31. Prorogation de report, pièces non récupérables, classes d'articles

## A. Prorogation unique d'un report (RIE)

**Compte : `camo`**

La MEL permet, pour les catégories **B et C**, une **seule** prorogation de l'intervalle de rectification (RIE). Elle est approuvée par la CAMO **avant l'échéance**, pour une durée au plus égale à l'intervalle initial, et l'autorité en est informée.

1. Menu **Défauts & reports** → **DEF-...-0002** (F-HDMC, éclairage cabine, cat. C, limite J+10).
2. Cadre **Proroger le délai (RIE)** : nouvelle limite (date) J+20, référence RIE `RIE-2026-001`, justification `Ampoule en commande, livraison J+12`. Cochez « autorité informée » si c'est fait. Mot de passe → **Approuver et signer la prorogation**.

**Résultat** : la nouvelle limite est utilisée partout (échéances, planning, tableau de bord). La fiche affiche la limite initiale, l'approbateur et la référence, et une signature « Prorogation de report (RIE) » est ajoutée.

**Contrôles** :

| Cas | Résultat |
|---|---|
| Nouvelle limite au-delà de J+20 (intervalle initial 10 j) | Refus : « Prorogation (date) supérieure à l'intervalle initial » |
| Ajouter un critère absent du report initial (ex. FH) | Refus |
| Seconde prorogation | Refus : « une seconde prorogation est interdite » |
| Limite déjà atteinte | Refus : « doit être approuvée avant l'échéance » |
| Catégorie A, D ou hors MEL | Refus |
| Utilisateur non CAMO (ex. `b2`) | Cadre non affiché, action refusée |

## B. Pièce non récupérable : mise au rebut

**Compte : `magasin`**

Une pièce non récupérable (LLP en butée, non réparable, endommagée, traçabilité insuffisante) doit être **mutilée** pour qu'elle ne puisse jamais revenir dans le circuit d'approvisionnement (145.A.42(d), M.A.504(d)).

1. Menu **Composants** → un composant déposé, au statut « Non utilisable » ou « Quarantaine ».
2. Cadre **Mettre au rebut (pièce non récupérable)** : date, motif, méthode de mutilation (`Découpe`), témoin (`Isabelle GARNIER (qualité)`), réf. certificat de destruction. Mot de passe → **Signer la mise au rebut définitive**.

**Résultat** : statut **Rebuté**, définitif. Le statut ne peut plus changer, ni par l'écran, ni par l'administration, ni par l'API. Exemple dans la démo : l'étoile Starflex `DEMO-S3399`, en butée de vie.

Une pièce installée ou réservée ne peut pas être rebutée.

## C. Classes d'articles (145.A.42(a))

**Compte : `magasin`**

Chaque référence P/N a une **classe**, qui détermine le justificatif exigé à la réception :

| Classe | Justificatif accepté | Exemple démo |
|---|---|---|
| Élément (component) | EASA Form 1, FAA 8130-3, double libération, TCCA Form One | Moteurs, BTP, filtre à huile, bouchon magnétique |
| Pièce standard | Certificat de conformité (CoC), norme obligatoire | Joint torique `AS568-012` |
| Matière première | CoC, spécification obligatoire | Fil à freiner `MS20995C32` |
| Consommable | CoC | Huile, graisse |

**Test** : menu **Réception** → P/N `DEMO-350FLT-01` (filtre, élément) avec un certificat « Certificat de conformité » → refus : « un certificat libératoire autorisé … est exigé ». Le même essai avec `DEMO-OIL-T2` (consommable) est accepté.

Une référence sérialisée, rotable ou à vie limitée est forcément un élément.
