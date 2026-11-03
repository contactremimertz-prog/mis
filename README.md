# MIS Hélicoptères : démonstration EASA (V2.4)

Site statique de démonstration d'un MIS (Management Information System) pour une flotte d'hélicoptères fictive, couvrant Part-M / Part-CAMO, Part-145, Part-21, la logistique et la qualité.

## Lancer la démo en local

Ouvrir `index.html` dans Chrome, Edge ou Firefox (double-clic). Aucune installation, aucun serveur, aucune connexion requise (seules les polices Google sont chargées si Internet est disponible).

Sur un serveur web (GitHub Pages ou `python3 -m http.server`), la base utilise WebAssembly, plus rapide. En ouverture directe du fichier, elle passe automatiquement en version asm.js.

## Contenu

| Dossier | Rôle |
|---|---|
| `index.html` | Page unique, avec politique de sécurité du contenu (CSP) |
| `js/boot.js` | Chargeur des scripts avec contrôle d'intégrité SRI (sha384) en http(s) |
| `js/core/` | Socle : état partagé, langues, droits, base SQLite, journal d'audit, règles de navigabilité |
| `js/ui/` | Interface : composants, écrans, fiches, signature simulée |
| `js/actions/` | Actions métier : OT et CRS, stock et Form 1, qualité, administration |
| `js/export/` | Exports CSV et PDF |
| `js/main.js` | Point d'entrée : affichage, navigation, événements, démarrage |
| `js/seed.js` | Schéma SQLite et données de démonstration fictives |
| `js/i18n/fr.js`, `en.js`, `es.js`, `de.js` | Un fichier de traduction par langue (566 textes chacun) |
| `css/app.css` | Styles, thèmes clair et sombre, responsive |
| `tools/update-sri.py` | Recalcule les empreintes SRI : à lancer après toute modification d'un fichier JS |
| `docs/ARCHITECTURE.md` | Architecture interne (en anglais) : modules, flux de données, fonctions publiques |
| `vendor/` | sql.js 1.10.3, jsPDF 4.2.1, jsPDF-AutoTable 5.0.9, hébergés localement (licences incluses) |

Le code est commenté en anglais (en-tête de chaque module et description des fonctions). Voir [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Profils de démonstration

Choisir le profil en haut à droite. Pour signer, saisir de mémoire le numéro d'habilitation du profil (tableau ci-dessous). Il sert de secret de signature : l'application ne l'affiche jamais, il est entièrement masqué (••••••, longueur fixe) sur tous les écrans et exports, CRS compris. Il reste enregistré, figé, dans chaque CRS.

| Profil | Rôle | N° d'habilitation |
|---|---|---|
| Sophie Durand | Responsable CAMO | CAM-0310 |
| Paul Garnier | Planificateur maintenance | PLN-0207 |
| Nadia Benali, Yanis Torres | Technicien certifié | TEC-1140, TEC-1187 |
| Claire Morand (B1), Hugo Lefèvre (B2) | Certificateur (CRS) | CRS-0872, CRS-0915 |
| Inès Roche | Magasinier | MAG-0451 |
| Rémi Quentel | Responsable qualité | QA-001 |
| Alex Martin | Administrateur | ADM-0001 |

## Scénario de démo conseillé (critères d'acceptation)

1. **Échéance dépassée** : le tableau de bord affiche une alerte rouge (F-XXXD visite 100 h, F-XXXK batterie ELT).
2. **OT clos → CRS + journal** : profil Hugo Lefèvre, Ordres de travail, WO-2026-0415, « Émettre le CRS », signer avec CRS-0915. Le CRS est généré (PDF téléchargeable) et tracé dans le journal d'audit.
3. **Traçabilité pièce** : Stock, pièce SG-55188 : réception, sortie magasin, installation sur F-XXXB via WO-2026-0415.
4. **Séparation des rôles et signature rejetée** : profil Nadia Benali, WO-2026-0418 : signer une carte. Profil Hugo Lefèvre, WO-2026-0415, « Émettre le CRS » : saisir un mauvais numéro, la signature est refusée et l'échec est journalisé ; puis saisir CRS-0915.
5. **Droits par rôle** : profil Inès Roche (magasinier) : les écrans CAMO et Part-21 sont absents, et l'accès direct est refusé et journalisé.
6. **Quarantaine et Form 1** : la pièce LGT-90017 sans Form 1 bloque WO-2026-0421. Profil Inès Roche : « Rattacher un EASA Form 1 » exige une référence au format F1-ORG-AA-NNNNN (ex. F1-DEMO-26-13001), unique, l'organisme émetteur (ex. FR.21G.DEMO) et une date non future. À l'installation, le Form 1, la date de péremption et la limite de vie sont revérifiés.
7. **4 langues** : sélecteur en haut, tous les écrans, messages, journaux et exports sont traduits.

## Limites (démonstration)

- **Journal d'audit (modifiable sur le poste)** : stocké dans le navigateur (IndexedDB). Il est protégé par des déclencheurs SQL (ni modification ni suppression) et chaîné en **SHA-256** (implémentation contrôlée au démarrage contre WebCrypto). La réinitialisation des données de démo **conserve le journal** et y est tracée. Un utilisateur du poste peut toutefois effacer les données du navigateur : la production exige un serveur avec journal scellé.
- **Réinitialisation** : réservée à l'administrateur et protégée par une ré-authentification (numéro d'habilitation). Le journal est conservé.
- **Empreinte de tête du journal** : affichée dans l'écran Journal d'audit (bouton Copier) et ajoutée à la fin des exports CSV et PDF du journal. La conserver hors du poste permet de détecter une réécriture complète du journal, que le navigateur seul ne peut pas empêcher.
- **Exports CSV** : les cellules commençant par =, +, -, @, tabulation ou retour chariot sont neutralisées (préfixe ') contre l'injection de formules.
- **Intégrité des scripts** : en http(s) (GitHub Pages), chaque script est chargé avec un contrôle SRI sha384 ; un fichier modifié bloque le démarrage. En ouverture directe du fichier, le navigateur n'applique pas le SRI.
- **Horodatage** : horloge du poste client. En production : horodatage serveur (source de temps fiable).
- **Signature électronique simulée** : saisie du numéro d'habilitation, sans certificat ni authentification forte.
- **Contrôle d'accès côté navigateur** : les droits par rôle sont contrôlés uniquement dans le navigateur, et le profil se choisit librement. Acceptable en démonstration, à remplacer par une authentification et des contrôles côté serveur.
- **Numéro d'habilitation sur le CRS** : Part-145 demande que le CRS porte la référence d'habilitation du certificateur. En démo, ce numéro sert aussi de secret de signature, il est donc masqué. En production : signature par authentification forte distincte, et référence d'habilitation imprimée en clair sur le CRS.
- **Polices** : les polices Inter et JetBrains Mono sont chargées depuis Google Fonts (seule ressource externe, sans script). Hors connexion, les polices système sont utilisées. En production : polices hébergées sur le serveur.
- **CRS** : la référence d'agrément de l'organisme, le numéro d'habilitation et la catégorie du certificateur sont figés dans chaque CRS au moment de l'émission.
- **Conservation des enregistrements** : en démo, durée illimitée dans le navigateur. En production, à confirmer par le contrôleur EASA (au minimum 3 ans après la remise en service pour Part-145, et durées propres à Part-CAMO / Part-M pour le dossier de navigabilité).
- **Données** : toutes fictives (immatriculations F-XXXA à F-XXXM, MSN, P/N, AD-DEMO, Form 1 DEMO). Aucun logo ni marque Airbus n'est reproduit ; seuls les noms de modèles sont cités.
- **Stockage** : propre à chaque navigateur et à chaque poste. Les sauvegardes de la V2 sont remplacées par les données d'exemple au premier lancement de la V2.1 (nouveau schéma).

## Historique

- **V2.4** : code découpé en 17 modules (socle, interface, actions, exports), fonctions courtes, commentaires en anglais, document d'architecture interne. Correctif : à la clôture d'une NC, la cause et l'action saisies sans enregistrer préalable sont conservées.
- **V2.3** : corrections des tests (favicon, fermeture des fenêtres après CRS et libération Form 1, fiche pièce PDF sans mouvement) et de la revue Cybersécurité (numéro d'habilitation entièrement masqué, limites documentées).
- **V2.2** : corrections de la revue Cybersécurité (numéros d'habilitation masqués, CSV protégé contre l'injection de formules, empreinte de tête du journal, ré-authentification avant réinitialisation, jsPDF 4.2.1 et SRI).
- **V2.1** : corrections du rapport d'écarts EASA (P1 : numéro d'habilitation masqué, journal conservé à la réinitialisation, chaînage SHA-256 ; P2 : mention des droits côté navigateur, agrément et habilitation figés dans le CRS, contrôle du Form 1, revérification à l'installation, conservation documentée ; P3 : horodatage et scénario de signature rejetée documentés).
- **V2** : première version complète.

## Mise en ligne (GitHub Pages)

Copier le contenu de ce dossier à la racine d'un dépôt, puis activer GitHub Pages (branche `main`, dossier racine). Adresse prévue : https://contactremimertz-prog.github.io/mis/
