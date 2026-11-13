# 23. Changer de base de données (SGBD)

AHMIS **ne dépend d'aucun SGBD** : toute la persistance passe par l'ORM Django, sans requête SQL spécifique. La même application fonctionne sur :

| SGBD | `AHMIS_DB_ENGINE` | Pilote à installer |
|---|---|---|
| SQLite (démo, défaut) | `sqlite` | aucun |
| PostgreSQL | `postgresql` | `psycopg[binary]` |
| MySQL / MariaDB | `mysql` | `mysqlclient` |
| Oracle | `oracle` | `oracledb` |
| Microsoft SQL Server | `mssql` | `mssql-django` |

## Configuration

Par variables d'environnement :

```
AHMIS_DB_ENGINE=postgresql
AHMIS_DB_NAME=ahmis
AHMIS_DB_USER=ahmis
AHMIS_DB_PASSWORD=********
AHMIS_DB_HOST=srv-bdd.local
AHMIS_DB_PORT=5432
```

## Exemple : passer de SQLite à PostgreSQL

1. Créez la base et l'utilisateur dans PostgreSQL.
2. Installez le pilote : `pip install "psycopg[binary]"`.
3. Exportez les données depuis la base SQLite actuelle (sans variables `AHMIS_DB_*`) : `python manage.py dumpdata --natural-foreign --exclude contenttypes --exclude auth.permission -o ahmis_export.json`
4. Définissez les variables `AHMIS_DB_*` pour PostgreSQL, puis créez les tables : `python manage.py migrate`
5. Importez : `python manage.py loaddata ahmis_export.json`
6. Vérifiez avec `python manage.py test apps` (les tests créent leur propre base temporaire) et en ouvrant l'application.

## Passage en production : points obligatoires

La démo est configurée pour un poste local. Avant toute utilisation réelle :

- `AHMIS_DEBUG=0` et une clé `AHMIS_SECRET_KEY` longue et secrète ;
- `AHMIS_ALLOWED_HOSTS` = le nom du serveur ;
- un serveur d'application (gunicorn, uWSGI ou IIS) derrière HTTPS : jamais `runserver` ;
- sauvegardes de la base et du dossier `media/` (scans des certificats), testées par restauration ;
- comptes nominatifs, mots de passe forts, et suppression des comptes de démonstration ;
- `AHMIS_ORGANISATION`, `AHMIS_APPROVAL_145`, `AHMIS_APPROVAL_CAMO` renseignés : ils figurent sur les task cards et les CRS.

## Autres paramètres

| Variable | Défaut | Rôle |
|---|---|---|
| `AHMIS_ALERT_DAYS` | 30 | Fenêtre « À planifier » |
| `AHMIS_FORECAST_DAYS` | 365 | Horizon par défaut du forecast |
| `AHMIS_TIME_ZONE` | Europe/Paris | Fuseau horaire des signatures |
