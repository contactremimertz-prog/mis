# 32. Matrice de conformité réglementaire

Cette matrice relie les principales exigences de l'EASA aux fonctions d'AHMIS. Elle sert de base au dossier de présentation à l'autorité.

> **Important** : un logiciel n'est pas « conforme » à lui seul. C'est l'organisme (CAMO, Part-145) qui démontre sa conformité à l'autorité (en France, la DSAC). Il le fait en décrivant l'outil et son usage dans ses procédures (CAME, MOE), en le validant et en l'auditant. La colonne « À faire par l'organisme » liste ce qui reste à votre charge. Les références réglementaires ci-dessous sont indicatives : vérifiez-les dans les textes en vigueur.

## Navigabilité (Part-CAMO / Part-M)

| Exigence | Fonction AHMIS | Couverture | À faire par l'organisme |
|---|---|---|---|
| Programme d'entretien approuvé | Programme par type, intervalles FH/cycles/calendrier, seuils, tolérances, effectivité, révision AMP, historique des révisions | ✅ | Saisir le programme approuvé (MSM/MPD), contrôle de la saisie par une 2e personne |
| Tolérances non cumulatives | Réalisation en tolérance : échéance suivante comptée depuis la butée théorique ; hors tolérance tracé ; tolérance interdite sur ALS/CMR, référencée sur AD (tutoriel 25) | ✅ | Définir les tolérances autorisées dans le programme |
| Revue périodique du programme (M.A.302(g)) | Revue par type au moins tous les 12 mois, examen fiabilité et nouvelles instructions, amendement approuvé, alerte tableau de bord, historique (tutoriel 27) | ✅ | Procédure de revue et d'approbation indirecte dans la CAME |
| Suivi des consignes de navigabilité | Registre AD/SB, évaluation par aéronef avec justification, tâches de suivi, délai à partir de l'entrée en vigueur, statut mis à jour à la réalisation | ✅ | Veille AD (EASA, FAA, constructeur) et saisie |
| Limitations de navigabilité, LLP | Limites de vie FH/cycles/jours, traçabilité « back-to-birth », échéances LLP, refus de pose en butée | ✅ | Reprendre l'historique complet des LLP à l'entrée en flotte |
| Potentiels (TBO) | Échéances TBO, compteurs TSO/CSO | ✅ | — |
| Enregistrements de navigabilité | Heures/cycles tracés, réalisations, configuration, composants, CRS, aucune suppression possible | ✅ | Sauvegardes |
| Durées de conservation (M.A.305(h), 145.A.55(c)) | Règles de conservation par nature, date de retrait de l'aéronef, rapport des enregistrements échus, suppression en masse bloquée tant que la durée n'est pas atteinte (tutoriel 30) | ✅ | Procédure d'archivage / purge documentée |
| Statut des modifications et réparations (M.A.305) | Registre dédié : classification, base d'approbation, application, ICA et intégration au programme, pesée et manuel de vol, alertes dans les échéances (tutoriel 26) | ✅ | Classification et approbation des modifications (Part-21) |
| Transfert des enregistrements (M.A.307) | Archive complète du dossier (synthèse HTML, JSON, CSV, manifeste SHA-256), accusé de réception, contrôle d'intégrité d'un dossier reçu (tutoriel 30) | ✅ | Procédure de transfert avec le nouvel organisme |
| Revue de navigabilité / ARC | Registre ARC, alerte d'expiration, fiche aéronef synthétique | ✅ | Procédure de revue, personnel ARS habilité |
| Défauts reportés | Report MEL/CDL signé, limites, intégré aux échéances | ✅ | Saisir la MEL de l'exploitant |
| Prorogation de report (RIE) | Une seule prorogation, catégories B et C, approuvée et signée par la CAMO avant l'échéance, durée ≤ intervalle initial, autorité informée (tutoriel 31) | ✅ | Procédure RIE acceptée par l'autorité |

## Entretien (Part-145)

| Exigence | Fonction AHMIS | Couverture | À faire par l'organisme |
|---|---|---|---|
| Données d'entretien | Task cards générées depuis le programme, avec étapes et références | ✅ | Contenu technique issu des données constructeur sous licence |
| Fiches de travail, signature de chaque étape | Étapes signées individuellement, valeurs relevées, N/A | ✅ | — |
| Personnel certifiant et autorisations | Licence Part-66, autorisations par type, catégorie et validité, suspension, contrôle à chaque signature | ✅ | Gestion des autorisations (procédure MOE) |
| Contrôle indépendant (tâches critiques) | Seconde signature obligatoire par une autre personne certifiante | ✅ | Identifier les tâches critiques dans le programme |
| Certificat de remise en service | CRS signé électroniquement, blocages automatiques, mention des reports, catégorie C pour une grande visite | ✅ | Texte du CRS à aligner sur la MOE |
| Outillage étalonné | Étalonnage, sortie interdite si échu, traçabilité des utilisations | ✅ | — |
| Acceptation des composants | Réception avec certificat, contrôle à réception, quarantaine automatique, pièces suspectes | ✅ | — |
| Classes d'articles (145.A.42(a)) | Classe par P/N (élément, pièce standard, matière, consommable) ; Form 1 exigé pour un élément, norme exigée pour une pièce standard ou une matière (tutoriel 31) | ✅ | Classer le catalogue P/N |
| Pièces non récupérables (145.A.42(d)) | Mise au rebut signée avec mutilation et témoin, statut définitif (tutoriel 31) | ✅ | Procédure de mutilation |
| Expérience récente (145.A.35) | 6 mois sur 24 calculés depuis les signatures AHMIS et les expériences déclarées, bloquant pour le personnel certifiant (tutoriel 28) | ✅ | Déclarer l'expérience antérieure des nouveaux arrivants |
| Facteurs humains, formations | Formations par catégorie, catégories obligatoires bloquantes (facteurs humains, formation continue), autres expirations signalées | ✅ | Programme de formation continue |
| Compte rendu d'événements (376/2014, 145.A.60) | Déclaration par tout le personnel, confidentialité, délai 72 h, suivi 30 jours, détenteur de la conception, clôture, alertes (tutoriel 29) | ✅ | Notification à l'autorité (ECCAIRS) et analyse ; AHMIS ne transmet pas automatiquement |

## Systèmes informatiques, enregistrements électroniques, sûreté de l'information

| Exigence | Fonction AHMIS | Couverture | À faire par l'organisme |
|---|---|---|---|
| Intégrité et traçabilité des enregistrements | Journal d'audit en écriture seule, champ par champ, suppression interdite | ✅ | — |
| Signature électronique | Ressaisie du mot de passe, identité et licence, horodatage, empreinte SHA-256, non modifiable | ✅ | Faire accepter le procédé de signature par l'autorité |
| Contrôle d'accès | Rôles par métier + autorisations individuelles | ✅ | Comptes nominatifs, revue périodique des droits |
| Sûreté de l'information (Part-IS) | Base technique : authentification, traçabilité | ⚠️ partiel | Analyse de risques, hébergement sécurisé (HTTPS), sauvegardes, plan de continuité, gestion des incidents |
| Validation du logiciel | 89 tests automatiques sur les règles critiques | ⚠️ partiel | Plan de validation formel, recette par les experts navigabilité, gestion des versions |

## Limites connues de cette version

- **Une seule unité de cycles** par aéronef (cycles ou atterrissages). Les cycles moteur spécifiques (NG/NF, démarrages) ne sont pas suivis séparément.
- Pas de saisie vol par vol : les heures sont saisies par compte rendu (journalier ou par vol).
- Pas d'import automatique des données constructeur (MSM, MRI, IPC) ni des AD : la saisie est manuelle.
- Qualification de catégorie (A/B1/B2) de la task card : indicative, non bloquante pour l'exécution. L'autorisation sur le type et les droits de certification sont, eux, bloquants.
- Pas de module financier (coûts, facturation, achats fournisseurs).
- Données de démonstration en français uniquement (l'interface et les tutoriels existent aussi en anglais, espagnol et allemand).

Ces points sont des pistes d'évolution, à prioriser selon vos besoins.
