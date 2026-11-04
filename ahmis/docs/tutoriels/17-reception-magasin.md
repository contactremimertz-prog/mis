# 17. Réception magasin et certificats libératoires

**Compte : `magasin`**

Toute pièce entre dans AHMIS par la **réception**, avec son certificat libératoire.

## 1. Réceptionner un consommable

Menu **Réception** :

- P/N `DEMO-OIL-T2` (huile turbine), n° de lot `LOT-OIL-2701`, quantité `24`, emplacement `MAG-PRINC`, date de péremption dans 2 ans (obligatoire pour cet article) ;
- certificat : type « Certificat de conformité », n° `COC-5521`, émetteur `Distributeur agréé démo`, date du jour ;
- cochez les **3 contrôles à réception** → **Enregistrer**.

**Résultat** : le lot apparaît dans **Stock consommables**, « Utilisable », avec un mouvement d'entrée.

## 2. Réceptionner une pièce sérialisée

- P/N `DEMO-SG-150` (démarreur-génératrice), S/N `DEMO-G1700`, quantité 1, état « Réparé », TSN `850`, CSN `2400`, TSO `0`, CSO `0` ;
- certificat : EASA Form 1, n° `F1-778`, émetteur `Atelier équipements agréé`, n° d'agrément `FR.145.DEMO-Y`, statut « Réparé » ;
- 3 contrôles cochés → **Enregistrer**.

**Résultat** : la fiche composant s'ouvre, avec son certificat accepté. La pièce peut être délivrée et posée.

## 3. Réception non conforme → quarantaine automatique

Recommencez une réception (S/N `DEMO-G1701`) **sans cocher** « Certificat complet, signé, émetteur agréé ».

**Résultat** : « placé en QUARANTAINE ». La pièce est stockée en `QUAR`, son certificat est marqué rejeté, et elle ne peut être ni délivrée ni posée.

## Contrôles à la saisie

- S/N obligatoire pour une pièce sérialisée ; quantité 1.
- Un couple P/N + S/N déjà connu est refusé : « doublon ou pièce suspecte ».
- Date de péremption obligatoire pour les articles à durée de stockage limitée.
- Date de certificat future refusée.
- **Classe de l'article** (fiche P/N, 145.A.42) : un **élément** (component) exige un certificat libératoire autorisé (EASA Form 1, FAA 8130-3, double libération, TCCA Form One). Un certificat de conformité (CoC) n'est accepté que pour une pièce standard, une matière première ou un consommable. Voir le tutoriel 31.

## Certificats

Menu **Certificats libératoires** : tous les Form 1, 8130-3 et CoC. Le scan du certificat peut être joint (champ « Scan du certificat »).
