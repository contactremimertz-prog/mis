# 25. Tolérances : réalisation en tolérance, non cumulative

**Compte : `camo`**

Une tolérance permet de réaliser une tâche un peu après son échéance (par exemple +10 FH ou +30 jours sur une visite 100 h). Elle n'est **pas cumulative** : quand une tâche est faite en tolérance, l'échéance suivante se compte depuis la **butée théorique**, pas depuis la date ou les heures réelles. On ne « gagne » donc jamais d'heures en utilisant la tolérance.

## 1. Situation de départ

Menu **Échéances** → aéronef **F-HDMB** : la tâche `125-05-100 Visite 100 h / 12 mois` est **En tolérance**. Butée théorique `3 881,6 FH`, compteur actuel `3 887,6 FH`, soit 6 FH de dépassement sur une tolérance de 10 FH.

## 2. Enregistrer la réalisation

1. Cliquez `125-05-100` → **Enregistrer une réalisation (historique)**.
2. Aéronef `F-HDMB`, date du jour, FH `3887.6`, cycles `11623`, origine « Organisme externe », référence `CRS-EXT-001`, certifié par `Atelier externe` → **Enregistrer**.

**Résultat** :

- sur la fiche tâche, la réalisation porte le badge **en tolérance** ;
- dans les échéances, la prochaine butée est **3 981,6 FH** (3 881,6 + 100), et non 3 987,6. La note « Réalisée en tolérance : prochaine échéance comptée depuis la butée théorique » le rappelle ;
- pour la date, la réalisation n'était pas en retard : la prochaine échéance calendaire se compte depuis la date réelle (+12 mois).

Chaque critère (FH, cycles, date) est traité séparément : la base retenue est la plus petite valeur entre la réalisation réelle et la butée.

## 3. Réalisation hors tolérance

Si la réalisation dépasse la tolérance, elle est marquée **hors tolérance**. L'échéance suivante repart alors de la réalisation réelle, et le dépassement reste visible dans l'historique pour l'analyse de la CAMO.

## 4. Règles de saisie

- Les réalisations d'une même tâche doivent être saisies dans l'ordre chronologique.
- Une tolérance est **interdite** sur une tâche ALS ou CMR (limitations de navigabilité).
- Une tolérance sur une tâche AD exige une **référence** (paragraphe de l'AD qui l'autorise).
