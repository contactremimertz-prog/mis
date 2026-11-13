# 28. Expérience récente et formations obligatoires

**Comptes : `qualite`, `b1`**

145.A.35 impose au personnel certifiant au moins **6 mois d'expérience** d'entretien sur les **24 derniers mois**, ainsi qu'une formation continue. Les facteurs humains sont exigés de tout le personnel. AHMIS bloque la signature si l'une de ces conditions manque.

## 1. Panneau « Aptitude à signer »

Compte `qualite` → **Personnel & autorisations** → **Claire DUBOIS**. Le panneau indique :

- **Expérience récente** : nombre de mois, sur les 24 derniers, avec au moins une task card exécutée ou contrôlée dans AHMIS, ou couverts par une expérience déclarée. Il en faut au moins 6 ;
- **Formations (tout personnel)** et **Formations (certifiant)** : à jour, ou la liste de ce qui manque ;
- pour chaque type autorisé : « peut signer », ou les raisons du blocage.

## 2. Déclarer une expérience hors AHMIS

Pour une personne qui arrive d'un autre organisme, son expérience passée n'est pas dans AHMIS. Cadre **Expériences déclarées** :

1. Du `01/01/2026` au `30/06/2026`, organisme `Atelier précédent (DEMO)`, travaux `Entretien en ligne H125`, justificatif `Attestation employeur`.
2. **Ajouter** : les mois couverts comptent dans l'expérience récente.

Une expérience dans le futur, ou dont la fin précède le début, est refusée.

## 3. Formations obligatoires

Chaque formation a une **catégorie** : facteurs humains, formation continue (145.A.35), EWIS, sécurité réservoirs, formation type, sûreté, autre. Par défaut :

| Personnel | Catégories exigées |
|---|---|
| Tout le personnel | Facteurs humains |
| Personnel certifiant | Facteurs humains, formation continue |

Seules ces catégories bloquent. Les autres formations expirées sont signalées en rouge sans bloquer.

## 4. Vérifier le blocage

1. Compte `qualite` → fiche **Claire DUBOIS** → formation « Formation continue 145.A.35 » : notez sa date d'expiration.
2. Pour tester, ajoutez une fiche personnel de test avec une autorisation certifiante H125 mais **sans** formation continue.
3. Rattachez-la à un compte, puis ouvrez une task card H125 avec ce compte : le cadre « Signature impossible » liste « formation obligatoire absente ou expirée : Formation continue (145.A.35) ».

## 5. Paramétrage

Dans le fichier de configuration :

| Variable | Défaut | Rôle |
|---|---|---|
| `AHMIS_RECENCY_ENFORCE` | `1` | `0` désactive le contrôle d'expérience récente |
| `AHMIS_RECENCY_MONTHS` | `6` | Mois d'expérience exigés |
| `AHMIS_RECENCY_WINDOW_MONTHS` | `24` | Fenêtre glissante |
| `AHMIS_TRAINING_REQUIRED_ALL` | `human_factors` | Catégories exigées de tous |
| `AHMIS_TRAINING_REQUIRED_CERTIFYING` | `human_factors,continuation` | Catégories exigées du personnel certifiant |
