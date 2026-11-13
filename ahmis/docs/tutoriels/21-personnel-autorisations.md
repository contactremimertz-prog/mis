# 21. Personnel, licences et autorisations

**Compte : `qualite`**

AHMIS distingue deux choses :

- le **compte utilisateur**, avec son rôle, qui détermine les écrans accessibles ;
- la **fiche personnel**, avec sa licence Part-66 et ses autorisations, qui détermine ce que la personne peut **signer**.

## 1. Consulter une fiche

Menu **Personnel & autorisations** → **Claire DUBOIS** :

- licence `FR.66.DEMO.0002`, catégories B1.3 / B1.1, date de validité ;
- **autorisations** de l'organisme Part-145 : n°, type, catégorie, certifiante ou non, portée, validité, état ;
- **formations** à validité limitée : facteurs humains, EWIS… ;
- ses derniers travaux signés et contrôles.

**À vérifier** : son autorisation **Super Puma** expire dans 45 jours. Elle est comptée dans l'indicateur « autorisation(s) expirant sous 60 j » du tableau de bord.

## 2. Suspendre une autorisation

1. Ajoutez à Claire DUBOIS une autorisation (formulaire en bas de page) : n° `AUT-TEST`, type `ATR72-600`, catégorie B2, certifiante, dates du jour à +1 an, cochez **suspendue** → **Ajouter**. Elle apparaît « Suspendue ».
2. Pour une suspension réelle, modifiez l'autorisation existante depuis l'administration (compte `admin` → Administration → Autorisations) et cochez « suspendue ». La personne ne peut alors plus signer sur ce type, immédiatement.

## 3. Ce que vérifie chaque signature

| Action | Exigence |
|---|---|
| Démarrer, signer une étape, signer les travaux | Autorisation valide (toute catégorie) sur le type + formations obligatoires de tout le personnel à jour |
| Contrôle indépendant | Autorisation **certifiante** valide + licence valide + personne différente de l'exécutant + formations du personnel certifiant + expérience récente |
| Report de défaut | Autorisation certifiante valide + formations + expérience récente |
| CRS | Autorisation certifiante B1/B2/B3/C (C seule pour une grande visite) + licence valide + formations + expérience récente |

Toutes les raisons qui empêchent une signature sont listées en une fois, sur la task card et sur la fiche personnel (tutoriel 28).

## 4. Créer une personne

1. Compte `admin` → **Administration** → Utilisateurs → créez le compte et ajoutez-le au groupe voulu (« Mécanicien », « Certifiant »…).
2. Compte `qualite` → **Personnel** → **+ Créer** : rattachez le compte, saisissez matricule, nom, visa, licence.
3. Ajoutez ses autorisations et formations.

> Seules les formations des **catégories obligatoires** bloquent la signature (par défaut : facteurs humains pour tous, plus la formation continue pour le personnel certifiant). Une autre formation expirée, comme « Sûreté / zones réservées » de Lucas MARTIN, est signalée en rouge sans bloquer. Le tutoriel 28 détaille l'expérience récente et les formations obligatoires.
