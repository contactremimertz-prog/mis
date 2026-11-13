# Cahier de tests fonctionnels (V2.7)

Ce cahier s'adresse aux testeurs fonctionnels. Chaque cas indique le profil, les étapes et le résultat attendu. Noter pour chaque cas : **OK**, **KO** (avec capture et étapes exactes) ou **Bloqué**.

## 0. Préparation

| Élément | Valeur |
|---|---|
| Adresse | https://contactremimertz-prog.github.io/mis/ (ou `index.html` ouvert en local) |
| Navigateurs | Chrome ou Edge (référence), Firefox, Safari ; un passage sur mobile (largeur 390 px) |
| Codes personnels | Remis séparément par l'équipe Dev (fichier privé `codes-demo-mis.md`). Ils ne figurent ni dans ce dépôt ni sur le site. Les tirets et les majuscules sont facultatifs à la saisie. |
| Données | Toutes fictives. Pour repartir de zéro, utiliser une **fenêtre de navigation privée** neuve (la base et le journal sont stockés dans le navigateur). |

**Attention au verrouillage.** 5 codes faux en 10 minutes sur un même profil (connexion ou signature) bloquent ce profil 5 minutes, même après rechargement de la page. Faire les cas de verrouillage (section 2) avec le profil **Yanis Torres**, en dernier, ou dans une fenêtre privée dédiée. Fermer la fenêtre privée efface tout, y compris le blocage.

Profils : Sophie Durand (Responsable CAMO), Paul Garnier (Planificateur), Nadia Benali et Yanis Torres (Techniciens), Claire Morand B1 et Hugo Lefèvre B2 (Certificateurs), Inès Roche (Magasinier), Rémi Quentel (Responsable qualité), Alex Martin (Administrateur).

## 1. Connexion et profils

| N° | Profil | Étapes | Résultat attendu |
|---|---|---|---|
| C-01 | aucun | Ouvrir le site. | Écran « Connexion » seul : menu vide, sélecteur de profil de l'en-tête masqué. |
| C-02 | aucun | Saisir l'adresse suivie de `#users`. | L'écran de connexion reste affiché, aucune donnée visible. |
| C-03 | Alex Martin | Choisir le profil, saisir un code faux, « Se connecter ». | Message « Code personnel incorrect. Tentative enregistrée. », champ vidé. |
| C-04 | Alex Martin | Saisir le bon code. | Message « Profil : Alex Martin (Administrateur) », tableau de bord affiché. |
| C-05 | Alex Martin | Saisir le bon code en minuscules et sans tirets (nouvelle fenêtre privée). | Connexion acceptée. |
| C-06 | Alex Martin → Hugo Lefèvre | Dans l'en-tête, choisir Hugo Lefèvre. | Fenêtre « Changer de profil : Hugo Lefèvre » ; l'en-tête affiche toujours Alex Martin tant que le code n'est pas validé. |
| C-07 | Hugo Lefèvre | « Annuler » dans cette fenêtre. | On reste connecté en Alex Martin. |
| C-08 | Hugo Lefèvre | Refaire C-06 avec le bon code. | Profil Hugo Lefèvre actif, fenêtre fermée. |
| C-09 | tous | Rechargement de la page (F5). | Retour à l'écran de connexion (chaque chargement démarre déconnecté). |

## 2. Verrouillage après échecs (profil Yanis Torres)

| N° | Étapes | Résultat attendu |
|---|---|---|
| V-01 | Saisir 5 fois un code faux pour Yanis Torres. | Au 5e essai : « Trop d'échecs. Réessayez dans 300 s. » |
| V-02 | Recharger la page, saisir le **bon** code de Yanis Torres. | Toujours refusé avec le même message (le blocage survit au rechargement). |
| V-03 | Se connecter avec un autre profil (ex. Nadia Benali). | Connexion acceptée : le blocage ne concerne que Yanis Torres. |
| V-04 | Attendre 5 minutes, se connecter avec Yanis Torres. | Connexion acceptée. Le compteur repart à zéro après une connexion réussie. |
| V-05 | Connecté en Yanis Torres, ouvrir une signature (cas S-02 sur un autre OT, ou une carte) et saisir 5 codes faux. | Au 5e essai : « Trop d'échecs… » ; le bon code est aussi refusé pendant 5 minutes, et la connexion de Yanis Torres est bloquée après rechargement. |

## 3. Droits par rôle

| N° | Profil | Étapes | Résultat attendu |
|---|---|---|---|
| D-01 | Inès Roche | Regarder le menu. | Pas de groupes CAMO ni Part-21 (pas de « Programme d'entretien », « Consignes de navigabilité (AD) », « Modifications et Form 1 »). |
| D-02 | Inès Roche | Saisir l'adresse suivie de `#part21`, puis `#directives`. | « Accès refusé » : « Le rôle « Magasinier » n'a pas accès à cet écran ». |
| D-03 | Rémi Quentel | Journal d'audit. | Les deux refus de D-02 apparaissent (« Écran refusé »). |
| D-04 | chaque profil | Parcourir le menu. | Chaque rôle ne voit que ses écrans : voir la matrice « Accès aux écrans par rôle » de l'écran Utilisateurs et rôles (profil Alex Martin ou Rémi Quentel). |

## 4. Signatures et parcours de maintenance

| N° | Profil | Étapes | Résultat attendu |
|---|---|---|---|
| S-01 | Nadia Benali | Ordres de travail, WO-2026-0418, « Signer » une carte ; saisir un code faux. | « Code personnel incorrect. Tentative enregistrée. » ; carte non signée. |
| S-02 | Nadia Benali | Même carte, bon code. | « Signature enregistrée. » ; la carte attend la contresignature du certificateur. |
| S-03 | Nadia Benali | Dans WO-2026-0418, « Installer une pièce ». | Seules les pièces en stock avec Form 1 valide et non périmées sont proposées ; « Pièce installée et tracée. » |
| S-04 | Hugo Lefèvre | WO-2026-0415, « Émettre le CRS », bon code. | CRS-2026-0089 émis, « Ordre de travail clôturé » ; le CRS s'affiche et ne montre jamais le code (masque ••••••). |
| S-05 | Hugo Lefèvre | Dans le CRS, « Télécharger le CRS (PDF) ». | PDF lisible : agrément FR.145.DEMO, catégorie du certificateur (B2), mention « signature électronique simulée », aucun code personnel. |
| S-06 | Paul Garnier | « Nouvel ordre de travail » sur F-XXXA, tâche planifiée, puis « Affecter ». | « WO-2026-04xx créé. », affectation enregistrée. |
| S-07 | Nadia Benali | Ouvrir cet OT, « Démarrer les travaux », signer une carte. | OT démarré, carte signée. |
| S-08 | Claire Morand | Même OT, « Contresigner » la carte, bon code. | Signature enregistrée. |
| S-09 | Sophie Durand | Flotte, F-XXXA, « Enregistrer un vol » (ex. 1,5 h, 2 cycles). | « Vol enregistré sur F-XXXA. » ; heures et échéances mises à jour. |
| S-10 | tous | Tableau de bord. | Alerte rouge des échéances dépassées (F-XXXD visite 100 h, F-XXXK batterie ELT). |

## 5. Stock, Form 1 et qualité

| N° | Profil | Étapes | Résultat attendu |
|---|---|---|---|
| Q-01 | Inès Roche | Stock, pièce LGT-90017 (quarantaine), « Rattacher un EASA Form 1 » avec `ABC`. | « Référence Form 1 invalide (format F1-ORG-AA-NNNNN). » |
| Q-02 | Inès Roche | Même pièce : `F1-DEMO-26-13001`, émetteur `FR.21G.DEMO`, date du jour. | « Pièce libérée. », fenêtre fermée. |
| Q-03 | Inès Roche | « Réceptionner une pièce » sans Form 1. | « Pièce placée en quarantaine (Form 1 manquant). » |
| Q-04 | Inès Roche | Sur cette nouvelle pièce, « Rattacher un EASA Form 1 » avec la référence de Q-02. | « Ce Form 1 est déjà rattaché à une autre pièce. » |
| Q-05 | Inès Roche | Commandes, « Nouvelle commande », puis « Marquer reçue ». | « Commande PO-2026-01xx créée. », puis « Commande reçue. » |
| Q-06 | Rémi Quentel | Non-conformités, NC-2026-029 : compléter l'analyse des causes et l'action corrective, « Clôturer », bon code. | « NC-2026-029 clôturée. » |
| Q-07 | Rémi Quentel | « Ouvrir une non-conformité », puis tenter de la « Clôturer » sans analyse ni action. | « Renseignez l'analyse des causes et l'action corrective avant de clôturer. » |
| Q-08 | Rémi Quentel | Documents qualité, DOC-AMM-NH90 « Approuver R19 », bon code. | « DOC-AMM-NH90 à jour. », révision R19 applicable. |

## 6. Exports

| N° | Profil | Étapes | Résultat attendu |
|---|---|---|---|
| E-01 | Rémi Quentel | Journal d'audit, « Export CSV ». | Fichier `journal-d-audit-AAAA-MM-JJ.csv`, séparateur « ; », dernière ligne « Empreinte de tête SHA-256 : … ». |
| E-02 | Rémi Quentel | Journal d'audit, « Export PDF ». | PDF lisible avec l'empreinte de tête en fin de document. |
| E-03 | tout profil | Sur un écran tableau (Flotte, Stock…), « Export CSV » et « Export PDF ». | Le fichier contient exactement le tableau affiché (filtres compris). |
| E-04 | Rémi Quentel | Ouvrir une NC dont la description commence par `=` (créer au besoin : `=HYPERLINK("http://x","clic") test`), exporter en CSV, ouvrir dans Excel. | La cellule commence par une apostrophe : aucune formule exécutée. |
| E-05 | tout profil | Fiche d'un appareil, d'un OT ou d'une pièce, « Fiche PDF ». | PDF de la fiche, sans code personnel. |
| E-06 | tous | Chaque export. | Une entrée « Export » apparaît au journal. |

## 7. Journal d'audit

| N° | Profil | Étapes | Résultat attendu |
|---|---|---|---|
| J-01 | Rémi Quentel | Journal d'audit. | Les actions des sections précédentes sont présentes : connexions, « Échec de connexion », « Échec de signature », signatures, CRS, refus, exports. Chaque ligne a date, profil, rôle, action et empreinte. |
| J-02 | Rémi Quentel | « Vérifier l'intégrité ». | « Chaîne intègre : N entrées vérifiées. » |
| J-03 | Rémi Quentel | Bloc « Empreinte de tête du journal », « Copier ». | « Empreinte copiée. » (ou sélection à copier avec Ctrl+C / Cmd+C). |
| J-04 | Alex Martin | Utilisateurs et rôles, « Base de démonstration », « Réinitialiser », confirmer, code faux puis bon code. | Code faux refusé et journalisé ; puis « Données d'exemple restaurées. » |
| J-05 | Rémi Quentel | Journal d'audit après J-04. | Le journal est **conservé** (même nombre d'entrées + la réinitialisation) et toujours intègre. |
| J-06 | Alex Martin | Changer le rôle d'un utilisateur (ex. Yanis Torres), le « Suspendre » puis le « Réactiver ». | « Enregistré. » à chaque fois, entrées au journal. Sa propre ligne n'est pas modifiable (« vous »). |

## 8. Langues et affichage

| N° | Étapes | Résultat attendu |
|---|---|---|
| L-01 | Changer la langue (FR, EN, ES, DE) sur plusieurs écrans, une fenêtre de signature et un export. | Tous les textes, messages, journaux et exports sont traduits ; aucun texte manquant. |
| L-02 | Recherche : saisir `F-XXXB` puis Entrée. | Écran « Recherche » avec les résultats liés à F-XXXB. |
| L-03 | Mobile (390 px) : tableau de bord, flotte, OT, stock, journal. | Lisible, sans défilement horizontal de la page. |
| L-04 | Ouvrir `index.html` en local (double-clic). | Le site démarre (mode asm.js, plus lent) et les cas C-01 à C-04 passent. |

## 9. Assistant MIS (chatbot)

| N° | Profil | Étapes | Résultat attendu |
|---|---|---|---|
| A-01 | aucun | Écran de connexion. | Pas de bouton « ? » tant que personne n'est connecté. |
| A-02 | Hugo Lefèvre | Cliquer le bouton « ? » en bas à droite. | Le panneau s'ouvre, le bouton devient « × », le curseur est dans la zone de saisie. Avertissement visible en haut du panneau. |
| A-03 | Hugo Lefèvre | Regarder les questions fréquentes. | 4 questions du Certificateur (CRS, contresignature, conservation d'un CRS, clôture de NC). |
| A-04 | Hugo Lefèvre | Cliquer « Comment émettre un CRS ? ». | Réponse avec sources (dont Part-145, 145.A.50) et lien « Ouvrir l'écran Ordres de travail ». |
| A-05 | Hugo Lefèvre | « Oui, réponse utile ». | Bouton marqué, « Merci pour votre retour. » |
| A-06 | Hugo Lefèvre | Taper `conservation crs` puis Entrée. | Réponse sur la conservation d'un CRS (145.A.55(c)). |
| A-07 | Hugo Lefèvre | Taper `signer`. | « Votre question est un peu large. Voulez-vous dire : » avec des questions à choisir. |
| A-08 | Hugo Lefèvre | Taper `xyzzy`. | Aucune réponse validée : message d'orientation et questions proposées. |
| A-09 | Hugo Lefèvre | Taper `Peux-tu clôturer la NC pour moi ?`. | Badge « Hors périmètre » : l'assistant n'agit pas sur les données. |
| A-10 | Hugo Lefèvre | Taper `who can close a finding` (en anglais, site en français). | Réponse en français sur la clôture des non-conformités. |
| A-11 | Hugo Lefèvre | Boutons FR / EN / ES / DE du panneau. | Le panneau, l'historique et tout le site passent dans la langue choisie. |
| A-12 | Hugo Lefèvre | Maj+Entrée dans la zone de saisie, puis Échap. | Retour à la ligne sans envoi ; Échap ferme le panneau. |
| A-13 | Hugo Lefèvre | Cliquer un lien « Ouvrir l'écran … ». | L'écran s'ouvre, le panneau reste ouvert avec l'historique. |
| A-14 | Inès Roche | Changer de profil, ouvrir l'assistant. | Historique effacé ; questions du Magasinier. Une réponse ne propose pas de lien vers un écran interdit au rôle. |
| A-15 | Rémi Quentel | Journal d'audit après les cas A-04 à A-13. | Aucune entrée créée par l'assistant (les questions ne sont pas journalisées). |
| A-16 | tous | Mobile (390 px). | Le panneau occupe la largeur de l'écran, sans défilement horizontal. |

## 10. Limites connues (à ne pas remonter comme anomalies)

- Le contrôle d'accès, le verrouillage et le journal s'exécutent dans le navigateur : effacer les données du site ou modifier le code avec les outils du navigateur les contourne. C'est une limite assumée de la démonstration statique (voir « Limites » dans le README).
- La signature électronique est simulée (code personnel, sans certificat).
- L'horodatage vient de l'horloge du poste.
