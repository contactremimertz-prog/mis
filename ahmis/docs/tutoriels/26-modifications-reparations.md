# 26. Registre des modifications et réparations

**Comptes : `camo`, `b1`**

M.A.305 exige de connaître à tout moment l'état des modifications et réparations de chaque aéronef, avec leur base d'approbation et les instructions de maintien de la navigabilité (ICA) qui en découlent.

## 1. Enregistrer une modification

1. Compte `camo` → menu **Modifications & réparations** → **+ Créer**.
2. Aéronef `F-HDMA`, nature « Modification », classification « Mineure », intitulé `Installation d'un kit caméra externe`, ATA `25`.
3. Base d'approbation « Approbation DOA / Part-21J », référence `DOA-MIN-2026-118 (DEMO)`.
4. Statut « Appliquée », appliquée le : date du jour, ICA : `Supplément MSM 25-10 (DEMO)`. Cochez « modifie la masse et le centrage » → **Enregistrer**.

**Résultat** : la modification reçoit un numéro `MOD-AAAA-NNNN`. Sa fiche signale deux **points à solder** : « ICA non encore intégrées au programme d'entretien » et « fiche de pesée / centrage à mettre à jour ». Ils apparaissent aussi dans les **Échéances** de F-HDMA, nature « Modification / réparation ».

## 2. Solder le suivi

1. **Modifier** la modification : cochez « ICA intégrées au programme d'entretien » et « actions de suivi réalisées ».
2. **Enregistrer** : les points à solder disparaissent des échéances.

Pour intégrer les ICA, créez la tâche correspondante dans le programme (tutoriel 6), puis tracez la nouvelle révision dans la revue du programme (tutoriel 27).

## 3. Depuis une task card

Compte `b1` → une task card → lien **+ Enregistrer une modification ou une réparation réalisée sur cette task card**. Le formulaire est prérempli (aéronef, composant, intitulé, ATA, date), et la task card est liée.

## 4. Contrôles

| Règle | Message |
|---|---|
| Majeure : approbation EASA, STC ou DOA | « Une modification ou réparation majeure exige une approbation EASA, un STC ou une approbation DOA. » |
| Changement standard : CS-STAN | « Un changement standard doit se référer à CS-STAN. » |
| Appliquée : date obligatoire | « Date d'application obligatoire. » |
| Appliquée : ICA ou « pas d'ICA associées » | « Indiquez les ICA, ou cochez « pas d'ICA associées ». » |
| Déposée / annulée : motif | « Motif obligatoire. » |

Une modification ne se supprime pas : passez-la au statut « Déposée / annulée » avec un motif.
