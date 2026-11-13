# 2. Prise en main : rôles, navigation, signature électronique

**Compte : `admin`, puis `meca`**

## Le tableau de bord

1. Connectez-vous avec `admin`.
2. Le tableau de bord affiche 8 indicateurs. Chacun est cliquable et ouvre la liste filtrée correspondante :
    - échéances dépassées (dont en tolérance) et à planifier ;
    - défauts ouverts et reports hors délai ;
    - AD/SB à évaluer ;
    - work packages actifs et task cards en attente de contrôle ;
    - demandes de pièces, quarantaine, outillage hors étalonnage et autorisations qui expirent.
3. Le tableau **Flotte** donne pour chaque aéronef ses compteurs, la validité de l'ARC et le nombre d'échéances.

**À vérifier** : la ligne F-HDMB montre des échéances dépassées ; F-HDMD est « En maintenance ».

## Navigation

- Le menu de gauche est organisé par métier : CAMO, Part-145, Logistique, Qualité, Aide.
- La **recherche globale** (en haut) trouve une immatriculation, un P/N, un S/N, un WP, une task card, une AD. Essayez `DEMO-S3502` : vous arrivez directement sur la fiche du Starflex de F-HDMB.
- Chaque liste a une recherche et des filtres.

## Les rôles

1. Déconnectez-vous et reconnectez-vous avec `meca`.
2. Ouvrez **Flotte**, puis F-HDMA : la fiche est consultable, mais les boutons « Modifier » et « Reprise de configuration » n'apparaissent plus.
3. Tapez dans la barre d'adresse `/flotte/aeronefs/1/modifier/` : AHMIS répond « 403 Interdit ».

Les rôles limitent l'accès aux écrans. Le tutoriel 21 montre la seconde barrière : les autorisations individuelles de signature.

## La signature électronique

Toute action réglementaire (étape de task card, exécution, contrôle, report de défaut, CRS) exige de **ressaisir son mot de passe**. AHMIS enregistre alors :

- l'identité et la licence du signataire ;
- l'horodatage ;
- la déclaration signée ;
- une **empreinte SHA-256**, qui permet de détecter toute altération ultérieure (badge « ✓ intègre »).

Une signature ne peut être ni modifiée ni supprimée. Un mauvais mot de passe refuse la signature.

## Rien ne s'efface

Les enregistrements de navigabilité ne peuvent pas être supprimés, même par l'administrateur. On utilise des statuts (« annulé », « retiré », « rebuté »). Chaque modification est tracée champ par champ dans le **journal d'audit** (tutoriel 22).
