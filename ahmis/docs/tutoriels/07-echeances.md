# 7. Les échéances (butées)

**Compte : `camo`**

Menu **Échéances** : la liste consolidée de tout ce qui arrive à échéance sur la flotte.

## Les natures d'échéances

| Nature | Origine |
|---|---|
| Tâche | Programme d'entretien (cellule) |
| Tâche composant | Tâche suivie sur les compteurs d'un composant |
| LLP / TBO | Limites des composants installés |
| ARC | Expiration de l'examen de navigabilité |
| Défaut reporté | Limite MEL/CDL d'un défaut reporté |
| Consigne | AD/SB à évaluer, ou applicable sans tâche de suivi |

## Les statuts

| Statut | Signification |
|---|---|
| **Dépassé** (rouge) | Butée dépassée au-delà de la tolérance |
| **En tolérance** | Butée dépassée mais dans la tolérance autorisée |
| **À planifier** (orange) | Date prévue dans les 30 jours (paramètre `AHMIS_ALERT_DAYS`) |
| **OK** | Plus tard |

## Lire une ligne

- **Dernière réalisation** : date et compteurs.
- **Butée** FH / cycles / date.
- **Reste** FH / cycles (négatif en rouge).
- **Date prévue** : la plus proche des dates obtenues pour chaque critère, en projetant l'utilisation prévue.
- **Critère** : celui qui déclenche (FH, cycles ou calendrier).

## Exercices

1. Filtre **Aéronef = F-HDMB**.
    - `DEMO-AD-2026-0101` : **Dépassé**, −27,6 FH. L'AD est entrée en vigueur il y a 200 jours avec un délai de 50 FH, et n'a jamais été réalisée.
    - `125-05-100` : **En tolérance** (−6 FH sur une tolérance de 10 FH).
    - LLP Starflex : **À planifier**.
2. Filtre **Nature = LLP**, puis **Statut = À planifier**.
3. Filtre **Échéant sous = 90 jours**, puis **Export CSV** : le fichier s'ouvre dans Excel (séparateur « ; »).

## Planifier depuis les échéances

**Compte : `planif`** (la CAMO identifie les besoins, le planificateur les place dans un work package). Quand un aéronef est sélectionné, des cases à cocher apparaissent :

1. Filtre **F-HDMB**.
2. Cochez `DEMO-AD-2026-0101`, `125-05-100` et la LLP Starflex.
3. Work package : choisissez **WP … Visite 100 h** (déjà planifié dans 5 jours).
4. **Créer les task cards**.

**Résultat** : vous arrivez sur le work package avec 3 task cards générées : les étapes de la tâche, et une task card « dépose/repose » pour la LLP. La suite est au tutoriel 11.
