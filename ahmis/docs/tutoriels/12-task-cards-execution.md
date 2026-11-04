# 12. Exécuter une task card

**Compte : `meca`**

Situation de départ : sur F-HDMD (H145), la task card **Visite 100 h / 12 mois** est en cours. 3 étapes sur 6 sont signées, une clé dynamométrique est sortie, une demande de bouchon magnétique attend le magasin.

## 1. Ouvrir la task card

Menu **Task cards** → filtre Statut « En cours » → **Visite 100 h / 12 mois** (WP « Visite 100 h + boroscopie moteurs »).

## 2. Signer les étapes restantes

Pour les étapes 4, 5 et 6 :

1. Saisissez une valeur relevée si besoin (ex. `Niveau OK`) ; cochez N/A si l'étape ne s'applique pas.
2. Saisissez votre mot de passe → **Signer**.

Chaque étape signée affiche votre nom, votre visa (`LM1`) et l'horodatage.

**Essayez** un mauvais mot de passe : « Mot de passe ou code de signature incorrect : signature refusée ».

## 3. Tenter de signer les travaux

Compte rendu `Visite effectuée, RAS`, temps passé `7.5`, mot de passe → **Signer les travaux**.

AHMIS **refuse** : « Des demandes de pièces sont encore en attente ». C'est voulu : on ne clôture pas une tâche avec une pièce en attente.

## 4. Débloquer

1. **Pièce** : le magasinier délivre la demande (tutoriel 18). Si vous n'en avez pas besoin, demandez son annulation au magasin.
2. **Outillage** : dans le cadre Outillage, cliquez **Restituer** sur `CLE-DYN-01`. Tant qu'un outil est sorti, la signature est également bloquée.

## 5. Signer les travaux

Recommencez l'étape 3. La task card passe à **Clôturée**, car cette tâche ne demande pas de contrôle indépendant.

## Ce qu'AHMIS fait à la clôture

- Il enregistre la **réalisation** de la tâche aux compteurs actuels de l'aéronef.
- Il **recalcule** l'échéance : la visite 100 h de F-HDMD redevient « OK », avec 100 FH devant elle (vérifiez dans **Échéances**).
- Si la tâche suit une AD, il met à jour le statut de la consigne (tutoriel 8).
- Si la task card rectifie un défaut, il clôture le défaut (tutoriel 15).

## Contrôles automatiques à la signature

| Règle | Message |
|---|---|
| Fiche personnel liée au compte | « Votre compte n'est rattaché à aucune fiche personnel » |
| Autorisation valide sur le type | « … n'a pas d'autorisation valide sur le type H145 » |
| Toutes les étapes signées | « 3 étape(s) non signée(s) » |
| Compte rendu renseigné | « Le compte rendu des travaux est obligatoire » |
| Pas de demande de pièce en attente | « Des demandes de pièces sont encore en attente » |
| Outillage restitué | « Outillage non restitué : CLE-DYN-01 » |

## Constatation en cours de visite

Le cadre **Signaler une constatation** crée en un clic un **défaut** et une **task card de rectification** dans le même WP, liée à la task card d'origine. Essayez : `Légère corrosion sur ferrure de capot BTP`.

## Reporter ou annuler

- **Reporter** (motif obligatoire) : la task card est reportée, et le report apparaît dans le CRS.
- **Annuler** : seulement si aucune étape n'est signée.
