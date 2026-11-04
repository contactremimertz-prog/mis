# 29. Comptes rendus d'événements (règlement 376/2014)

**Comptes : `meca`, `qualite`, `camo`**

Tout événement qui compromet ou pourrait compromettre la sécurité doit être notifié à l'autorité **dans les 72 heures** après que l'organisme en a eu connaissance (règlement (UE) 376/2014, 145.A.60, CAMO.A.160). Une analyse de suivi est transmise **dans les 30 jours**. Le détenteur de la conception est informé si l'état de l'aéronef ou d'un composant est en cause.

AHMIS applique la **culture juste** : tout le personnel peut déclarer, mais seuls la qualité et la CAMO voient l'ensemble des comptes rendus. L'identité d'un déclarant confidentiel n'est visible que du responsable qualité.

## 1. Déclarer (tout le personnel)

1. Compte `meca` → menu **Comptes rendus d'événements** → **+ Créer**. Autre accès : bouton **Déclarer un événement** sur un défaut ou une task card, qui préremplit le formulaire.
2. Intitulé `Lampe torche retrouvée en zone moteur`, catégorie « Corps étranger (FOD) / objet oublié », phase « En maintenance », aéronef `F-HDMD`.
3. Dates de l'événement et de prise de connaissance : maintenant. Description factuelle, mesures immédiates `Zone inspectée, inventaire outillage`. Cochez **déclaration confidentielle** → **Enregistrer**.

**Résultat** : le compte rendu `OCC-AAAA-NNNN` est en **Brouillon**, avec l'échéance de 72 h affichée. Le mécanicien ne voit que ses propres déclarations.

## 2. Suivre les délais (qualité)

Compte `qualite` → **tableau de bord** : bandeau « Comptes rendus d'événements : N ouvert(s), dont N à notifier ». Il passe en rouge s'il y a un dépassement. La démo contient :

| N° | Situation |
|---|---|
| Vibrations palonnier (F-HDMD) | Brouillon : reste environ 20 h sur 72 |
| Frein d'écrou non posé (F-HDMB) | Notifié il y a 40 jours : **suivi à 30 jours en retard** |
| Pièce sans certificat libératoire | Clôturé |

Sur le compte rendu confidentiel, le déclarant (Sophie LAMBERT) est visible pour `qualite`, mais affiché « Confidentiel » pour `camo`.

## 3. Notifier, suivre, clôturer

Compte `qualite` → ouvrez le compte rendu → **Traiter** :

1. **Notification** : statut « Notifié à l'autorité », autorité `DSAC / ECCAIRS 2`, référence ECCAIRS, date de notification. Au-delà de 72 h, le **motif du retard** est obligatoire. Cochez « détenteur de la conception informé » si nécessaire.
2. **Suivi** : statut « Suivi transmis », analyse (causes, facteurs humains), date de transmission.
3. **Clôture** : actions correctives et date de clôture.

Un événement hors liste du règlement 2015/1018 peut être « Classé non notifiable », avec une justification. Un incident grave ou un accident ne peut pas l'être.

## 4. Conservation

Les comptes rendus clôturés sont conservés au moins 36 mois (tutoriel 30). Ils ne sont pas inclus dans les dossiers de transfert d'aéronef.
