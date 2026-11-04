# 30. Conservation et transfert des dossiers

**Comptes : `qualite`, `camo`**

## Partie A : conservation des enregistrements

Les enregistrements ont des durées minimales de conservation :

| Enregistrements | Durée minimale | Référence |
|---|---|---|
| Work packages, task cards, CRS, défauts | 36 mois après la remise en service | 145.A.55(c), M.A.305(h) |
| Réalisations de tâches | 36 mois, et jusqu'au remplacement par une réalisation plus récente | M.A.305(h) |
| Temps totaux, état des AD, LLP, modifications, poses / déposes | 12 mois après le retrait définitif de l'aéronef (ou du composant) | M.A.305(h)(1) |
| Dossier du personnel | 3 ans après le départ | 145.A.35(j) |
| ARC, revues du programme, étalonnages, comptes rendus d'événements | 36 mois | CAMO.A.220, 145.A.55 |

**AHMIS ne supprime jamais rien automatiquement.** Il refuse toute suppression unitaire, et refuse aussi une suppression en masse (administration, script) d'un enregistrement encore sous obligation de conservation.

### 1. Rapport de conservation

Compte `qualite` → menu **Conservation des enregistrements**. Pour chaque nature d'enregistrement, le rapport affiche le total, puis trois comptes :

- **sans échéance** : à conserver, par exemple pour un aéronef encore exploité ;
- **en cours** : durée minimale non atteinte ;
- **échus** : archivables, sur décision documentée selon la MOE ou la CAME.

Un export CSV est disponible par ligne. Dans la démo, sont échus : l'hélicoptère **F-HDMZ** (retiré il y a 20 mois) et ses heures de vol, ainsi que l'ancien salarié **Paul ANCIEN** (parti il y a 4 ans).

### 2. Retirer un aéronef du service

Fiche aéronef → **Modifier** → statut « Retiré » et **retrait définitif du service le**. La date est obligatoire pour un aéronef retiré, et interdite sinon. Elle fait partir le délai de 12 mois. L'aéronef sort des échéances et du tableau de bord, et sa fiche affiche la date de fin de conservation.

Pour un départ de personnel : fiche personnel → décochez « actif » et renseignez **départ de l'organisme le**.

## Partie B : transfert du dossier d'un aéronef (M.A.307)

Quand un aéronef change de CAMO ou de propriétaire, ses enregistrements de navigabilité sont transférés au nouvel organisme.

### 3. Transfert sortant

1. Compte `camo` → fiche **F-HDMA** → **Exporter le dossier**.
2. Sens « Transfert sortant », organisme `CAMO Héli Nord (DEMO)`, agrément `FR.CAMO.0999`, motif `Changement de gestionnaire de navigabilité` → **Enregistrer**.

**Résultat** : AHMIS génère l'archive `dossier-F-HDMA-TR-....zip` et la conserve avec son empreinte SHA-256 :

- `synthese.html` : état de navigabilité imprimable (temps totaux, échéances, composants, LLP et TBO, AD, modifications, défauts reportés) ;
- `dossier.json` et `csv/` : toutes les données (heures, réalisations, poses / déposes, certificats, work packages, task cards, signatures avec leur empreinte) ;
- `manifest.json` : empreinte de chaque fichier.

Quand le nouvel organisme confirme la réception, renseignez **Enregistrer l'accusé de réception** sur la fiche du transfert. La démo contient le transfert de F-HDMZ à l'acquéreur de la cellule, déjà accusé.

### 4. Transfert entrant

Menu **Transferts de dossiers** → **+ Créer** → sens « Transfert entrant », puis joignez l'archive reçue. AHMIS contrôle les empreintes du manifeste :

- archive intègre : bandeau vert ;
- fichier modifié, manquant ou ajouté, ou dossier d'un autre MSN : bandeau **ANOMALIE** avec le détail.

La reprise des données se fait ensuite par la saisie (tutoriel 3).

Les archives de transfert ne sont téléchargeables qu'avec le droit « voir les transferts » (CAMO, qualité), jamais par le lien générique des pièces jointes.
