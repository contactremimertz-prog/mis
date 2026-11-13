# 27. Revue annuelle du programme d'entretien

**Compte : `camo`**

M.A.302(g) demande de revoir périodiquement chaque programme d'entretien (au moins une fois par an) et de l'amender si nécessaire : efficacité (fiabilité, défauts répétitifs), nouvelles instructions (révisions MSM/MPD, AD, SB, ICA des modifications).

## 1. État des revues

Le **tableau de bord** affiche un bandeau « Revue du programme d'entretien » pour chaque type exploité dont la revue est absente, dépassée ou à faire sous 30 jours. Menu **Revue du programme** :

| Type | Situation de la démo |
|---|---|
| ATR72-600 | Aucune revue enregistrée |
| Super Puma | Revue dépassée (dernière revue il y a 13 mois) |
| H135 | Revue à faire sous 30 jours |
| NH90, H145 | À jour (NH90 amendé en « DEMO rév. 4 ») |

La fiche **type d'aéronef** (Flotte → Types & configuration) montre aussi l'état et les dernières revues.

## 2. Enregistrer une revue sans changement

1. Ligne **Super Puma** → **Nouvelle revue**. Programme et révision examinée sont repris de la revue précédente.
2. Réalisée par `Julien MOREAU (CAMO)`. Cochez **les deux** cases d'examen (fiabilité et nouvelles instructions).
3. Constatations `Aucun défaut répétitif, pas de nouvelle révision MSM` ; résultat « Programme confirmé sans changement » → **Enregistrer**.

**Résultat** : Super Puma passe « À jour », prochaine revue dans 12 mois.

## 3. Enregistrer un amendement

1. Ligne **ATR72-600** → **Nouvelle revue** : programme `AMP-ATR72-DEMO`, révision examinée `DEMO rév. 3`.
2. Résultat « Programme amendé », nouvelle révision `DEMO rév. 4`, changements `Ajout des ICA de la modification MOD-...`.
3. Mode d'approbation « Approbation indirecte », référence `PAI-2026-020`, date → **Enregistrer**.

**Résultat** : toutes les tâches actives du type passent en « révision AMP : DEMO rév. 4 ».

## 4. Contrôles

- Revue incomplète (fiabilité ou instructions non examinées) : refusée.
- Amendement sans nouvelle révision, avec une révision identique, sans description des changements ou sans approbation : refusé.
- Prochaine revue fixée au-delà de 12 mois : refusée. La périodicité se règle avec `AHMIS_AMP_REVIEW_MONTHS`.
- Revue datée dans le futur : refusée.
