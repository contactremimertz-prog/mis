# 13. Le contrôle indépendant (tâches critiques)

**Comptes : `b1`, puis `b2`**

Certaines tâches (commandes de vol, fixations critiques, inspections boroscopiques…) exigent une **seconde signature**, par une personne **différente** de l'exécutant et titulaire d'une **autorisation certifiante** sur le type.

Situation de départ : sur F-HDMD, la task card **Contrôle boroscopique moteurs Arriel 2E** a été exécutée par Claire DUBOIS (`b1`). Elle est au statut « Exécutée – attente contrôle ».

## 1. L'exécutant ne peut pas se contrôler

1. Connectez-vous avec `b1` et ouvrez la task card (menu **Task cards**, filtre « Exécutée – attente contrôle »).
2. Le cadre Exécution indique : « Vous avez exécuté ces travaux : le contrôle doit être signé par une autre personne. » Aucun bouton de contrôle n'est proposé.

## 2. Un mécanicien non certifiant ne peut pas contrôler

Avec `meca`, le formulaire de contrôle n'apparaît pas : son autorisation « mécanicien non certifiant » ne permet pas le contrôle.

## 3. Contrôle par une autre personne certifiante

1. Connectez-vous avec `b2` (Karim BENALI, B2 certifiant H145).
2. Ouvrez la task card → cadre **Contrôle indépendant** : observations `Images boroscopiques revues, conforme`, mot de passe → **Signer le contrôle**.

**Résultat** :

- la task card est **Clôturée** ;
- les deux signatures (exécution et contrôle) apparaissent avec leur badge « ✓ intègre » ;
- l'échéance de la tâche composant `145-72-500` du moteur MOT 1 est recalculée sur les compteurs **du moteur**.

## Rendre une tâche « critique »

Dans le programme d'entretien, cochez « contrôle indépendant requis » sur la tâche (tutoriel 6). Pour une task card hors programme, cochez la même case à sa création.
