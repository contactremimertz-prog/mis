# 22. Journal d'audit et signatures électroniques

**Compte : `qualite`**

## Journal d'audit

Menu **Journal d'audit** : chaque création, modification ou suppression technique est enregistrée avec :

- l'horodatage et l'utilisateur ;
- l'enregistrement concerné ;
- **chaque champ modifié**, avec son ancienne et sa nouvelle valeur.

Le journal est en **écriture seule** : aucune entrée ne peut être modifiée ou supprimée, même par l'administrateur.

**Exercices**

1. Recherche `F-HDMA` : toutes les opérations sur cet aéronef, y compris les incréments de compteurs.
2. Filtre « Type d'enregistrement = tâche d'entretien » : l'historique des révisions du programme.
3. Sur une fiche (aéronef, composant, task card, WP, défaut), le bouton **Historique** affiche les modifications **et** les signatures de cet enregistrement.

## Signatures électroniques

Menu **Signatures électroniques** : toutes les signatures, filtrables par action (exécution, contrôle, CRS, report…).

Chaque signature contient le nom, la licence au moment de la signature, la déclaration signée, l'horodatage et une **empreinte SHA-256** calculée sur l'ensemble.

Le badge **« ✓ intègre »** signifie que l'empreinte recalculée correspond. Si une donnée était modifiée directement en base, en dehors d'AHMIS, le badge deviendrait **« ⚠ altérée »**. Le test automatique `test_signature_is_immutable_and_tamper_evident` le démontre.

## Ce qui est conservé

- Aucun enregistrement de navigabilité ne peut être supprimé : aéronefs, composants, tâches, réalisations, task cards, WP, défauts, certificats, saisies d'heures…
- On utilise des statuts : annulé, retiré, rebuté, inactif.
- Les durées de conservation réglementaires relèvent de vos procédures (CAME / MOE) et de la sauvegarde de la base (tutoriel 23).
