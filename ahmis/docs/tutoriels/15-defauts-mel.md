# 15. Défauts et reports (MEL / CDL)

**Comptes : `meca`, `b2`, `planif`**

## 1. Signaler un défaut

1. Compte `meca` → ouvrez **F-HDMA** → **Signaler un défaut**.
2. Source « Compte-rendu équipage (techlog) », réf. techlog `CRM MA-150`, ATA `33`, description `Feu anticollision inférieur inopérant`.
3. **Enregistrer** : le défaut reçoit un numéro `DEF-AAAA-NNNN`, au statut **Ouvert**.

## 2. Reporter selon la MEL

Le report exige une **autorisation certifiante** sur le type.

1. Compte `b2` → menu **Défauts & reports** → ouvrez le défaut.
2. Cadre **Reporter selon la MEL / CDL** :
    - Référence MEL `MEL 33-40-01 (DEMO)`
    - Catégorie `C (10 jours)` ; laissez la limite vide pour le délai standard
    - Procédures `Placard INOP apposé, vol de jour uniquement`
    - Mot de passe → **Signer le report**

**Résultat** :

- le défaut est **Reporté**, limite = aujourd'hui + 10 jours ;
- il apparaît dans les **Échéances** de F-HDMA (nature « Défaut reporté ») et sur le planning ;
- s'il est encore reporté au moment d'un CRS, il est **cité dans la déclaration du CRS**.

Délais standard : B = 3 jours, C = 10 jours, D = 120 jours. Pour la catégorie A ou hors MEL, saisissez la limite (date, heures ou cycles).

**Contrôles** : sans référence MEL, ou sans aucune limite, le report est refusé. Le formulaire de report n'est pas proposé à un mécanicien non certifiant.

Une **prorogation unique** du délai (RIE) peut ensuite être approuvée par la CAMO, avant l'échéance : voir le tutoriel 31.

## 3. Rectifier

1. Compte `planif` → ouvrez le défaut → **Créer la task card de rectification** dans un WP existant ou « + Nouveau WP de dépannage ».
2. Exécutez la task card (tutoriel 12). À sa clôture, le défaut passe à **Rectifié**.

## Exemple déjà chargé

F-HDMC (H135) a un défaut **reporté** catégorie C (éclairage cabine) : voyez-le dans ses échéances et sur sa fiche.
