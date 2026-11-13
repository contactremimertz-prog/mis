# 20. Outillage et étalonnage

**Comptes : `magasin`, `meca`**

## Le parc d'outillage

Menu **Outillage** : référence, statut, dernier étalonnage, échéance et indicateur « Étalonnage OK ».

Dans la démo, la clé dynamométrique **CLE-DYN-02** a un étalonnage **échu** (indicateur tableau de bord « Outillage hors étalonnage »).

## 1. Un outil non étalonné ne peut pas sortir

1. Compte `meca` → une task card **en cours**, par exemple **Visite 100 h / 12 mois** de F-HDMD (si vous l'avez déjà clôturée au tutoriel 12, démarrez-en une autre, comme « Contrôle capacité batterie »).
2. Cadre **Outillage** → choisissez `CLE-DYN-02` → **Sortir l'outil**.
3. Refus : « étalonnage échu ou non renseigné, sortie interdite ».

## 2. Enregistrer un étalonnage

1. Compte `magasin` → **Outillage** → `CLE-DYN-02`.
2. « Enregistrer un étalonnage » : date du jour, laboratoire `Laboratoire de métrologie démo`, certificat `MET-2026-118`, résultat « Conforme » → **Enregistrer**.

L'échéance est recalculée (dernier étalonnage + 365 jours).

## 3. Sortir puis restituer

1. Compte `meca` → même task card → sortez `CLE-DYN-02`.
2. Elle passe à « Sorti », rattachée à la task card et à votre nom, avec sa **date de validité d'étalonnage** mémorisée.
3. **Restituer** quand le travail est fini. Rappel : la task card ne peut pas être signée tant qu'un outil reste sorti.

## Traçabilité en cas d'outil non conforme

Si un étalonnage revient **non conforme**, l'outil passe hors service. La fiche outil liste toutes les **utilisations** (task card, personne, dates), ce qui identifie les travaux à réévaluer depuis le dernier étalonnage valide.
