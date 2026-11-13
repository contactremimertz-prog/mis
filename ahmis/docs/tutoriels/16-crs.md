# 16. Certificat de remise en service (CRS)

**Comptes : `b1`, `b2`, `planif`**

Le CRS se signe au niveau du **work package**, quand tous les travaux sont terminés.

## 1. Voir ce qui bloque

Ouvrez le WP de F-HDMD (« Visite 100 h + boroscopie moteurs ») → cadre **Certificat de remise en service**. AHMIS liste tout ce qui empêche le CRS, par exemple :

- task card non clôturée (et son statut) ;
- outillage non restitué ;
- pièce réservée ni posée ni rendue au magasin.

Le bouton **Signer le CRS** reste grisé tant que la liste n'est pas vide.

## 2. Terminer les travaux

Si vous avez suivi les tutoriels 12 à 14, il reste au plus :

- **Contrôle capacité batterie** (qualification B2) : compte `b2` → démarrer, signer les 3 étapes, signer les travaux ;
- toute task card que vous auriez créée en exercice : clôturez-la, ou **reportez-la** avec un motif (un report n'empêche pas le CRS, il y est mentionné).

## 3. Signer le CRS

Compte `b1` → WP → mot de passe → **Signer le CRS**.

**Résultat** :

- le WP passe à **Remis en service (CRS signé)** et devient **non modifiable** ;
- F-HDMD repasse **En exploitation** ;
- la déclaration CRS est enregistrée avec le nom, la licence, la date, l'agrément de l'organisme, les compteurs de l'aéronef, les travaux reportés et les défauts reportés en cours ;
- **Imprimer le dossier** montre le CRS avec la référence de son empreinte SHA-256.

## Règles appliquées

| Règle | Détail |
|---|---|
| Autorisation certifiante valide sur le type | B1, B2, B3 ou C, non suspendue, dans ses dates |
| Licence Part-66 valide | Date de validité non dépassée |
| Grande visite (« Grande visite » en type de WP) | CRS réservé à la **catégorie C** (essayez avec `b1` puis `certc`) |
| Mécanicien non certifiant | Accès refusé (403) |
