# 3. Créer un type et un aéronef, reprendre sa configuration

**Compte : `camo`**

Objectif : faire entrer en flotte un nouvel H125, F-HDMX, avec son moteur.

## 1. Le type d'aéronef

Le type H125 existe déjà. Pour voir comment un type est défini :

1. Menu **Types & configuration** → cliquez **H125**.
2. La fiche montre les aéronefs du type, le **programme d'entretien** (tâches actives), le personnel autorisé et les P/N applicables.

Pour créer un nouveau type : bouton **+ Créer** dans la liste. Le champ « libellé des cycles » permet d'afficher « Atterrissages » pour un hélicoptère.

## 2. Créer l'aéronef

1. Menu **Flotte** → **+ Créer**.
2. Renseignez :
    - Immatriculation : `F-HDMX`
    - Numéro de série : `9199`
    - Type : `Airbus Helicopters H125`
    - Date de fabrication : il y a 3 ans
    - Heures totales : `1250` ; cycles : `3800` ; compteurs à jour au : aujourd'hui
    - Utilisation prévue : `1.5` FH/jour et `4` cycles/jour
3. **Enregistrer**.

**Résultat** : la fiche s'ouvre. Toutes les tâches du programme H125 apparaissent déjà dans **Échéances**. Comme aucun historique n'existe, la plupart sont calculées depuis la fabrication et ressortent **« Dépassé »**. C'est voulu : AHMIS ne suppose jamais qu'une tâche a été faite.

> Les compteurs ne sont saisissables qu'à la création. Ensuite, ils évoluent uniquement par les saisies d'heures de vol (tutoriel 4), pour garder une traçabilité complète.

## 3. Reprendre l'historique des tâches

Pour chaque tâche, enregistrez la dernière réalisation connue (relevée dans le logbook) :

1. Dans le tableau des échéances de F-HDMX, cliquez la tâche **125-05-100 Visite 100 h / 12 mois**.
2. Dans « Situation par aéronef », cliquez **reprise** sur la ligne F-HDMX.
3. Saisissez : date il y a 2 mois, FH `1190`, cycles `3620`, origine « Reprise historique », référence `Logbook p.42`, certifié par `Atelier X – CRS 1234`.
4. **Enregistrer**.

**Résultat** : la visite 100 h de F-HDMX est maintenant due à 1 290 FH (1 190 + 100), soit 40 FH restantes.

## 4. Reprendre la configuration (composants installés)

Le composant entre d'abord en stock avec son certificat, puis la CAMO le rattache à l'aéronef :

1. Compte **`magasin`** → menu **Réception** : P/N `DEMO-ARR2D-0001` (Arriel 2D), S/N `DEMO-E2X99`, quantité 1, emplacement `MAG-PRINC`, état « Révisé », TSN `1250`, CSN `3800`, TSO `1250`, CSO `3800`. Certificat : EASA Form 1, n° `F1-TEST-01`, émetteur `Atelier moteur agréé`, date du jour, statut « Révisé ». Cochez les 3 contrôles à réception → **Enregistrer**.
2. Compte **`camo`** → ouvrez F-HDMX → **Reprise de configuration** : composant `DEMO-E2X99`, position `MOT`, date = mise en service, référence `Relevé de configuration d'entrée en flotte` → **Enregistrer**.

**Résultat** : le moteur apparaît dans « Configuration installée » avec son TBO restant (4 000 − 1 250 = 2 750 FH). La tâche composant **125-72-500** (boroscopie moteur) apparaît dans les échéances, « Dépassé » tant que sa dernière réalisation n'est pas reprise. Faites-le comme à l'étape 3, en choisissant le composant `DEMO-E2X99` et ses compteurs (TSN/CSN) à la date de la dernière boroscopie.

> La reprise de configuration sert uniquement à l'entrée en flotte. En exploitation, tout mouvement de composant passe par une task card (tutoriel 14).
