# 9. Le forecast (prévision de maintenance)

**Compte : `camo` ou `planif`**

Menu **Forecast**.

## Principe

Le forecast **déroule** toutes les échéances sur un horizon donné :

- une tâche répétitive génère plusieurs occurrences (ex. la lubrification 50 FH d'un H145 à 2 FH/jour revient tous les 25 jours) ;
- LLP, TBO, ARC et défauts reportés apparaissent une fois ;
- les éléments déjà dépassés sont placés à aujourd'hui, avec le badge « dépassé ».

## Lecture

- Indicateurs : nombre d'échéances, **charge totale en heures-homme**, nombre de déposes en butée.
- **Charge mensuelle** : un histogramme par mois, avec la répartition par aéronef.
- Le détail de chaque mois s'ouvre au clic : occurrences, critère, charge, **pièces prévues** et besoin en pièces du mois (issu des « pièces requises » des tâches).

## Exercices

1. Horizon `365` jours, toute la flotte → **Calculer**. Repérez le mois de la **visite C de l'ATR** (600 h.h) : un pic de charge à anticiper.
2. Aéronef `F-HDMD`, horizon `180` jours : la charge propre à l'H145.
3. **Simulation** : toute la flotte, utilisation `130` % → **Calculer**. Les échéances en heures et en cycles se rapprochent ; les calendaires ne bougent pas. Comparez avec 100 %.
4. **Export CSV** : la liste complète des occurrences, pour un tableur ou un outil de planification.

> Le forecast est une projection fondée sur l'« utilisation prévue » de chaque aéronef. Maintenez ces valeurs à jour (fiche aéronef) pour une prévision fiable.
