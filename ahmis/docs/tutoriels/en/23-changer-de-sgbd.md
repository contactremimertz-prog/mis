# 23. Changing the database (DBMS)

AHMIS **does not depend on any DBMS**: all persistence goes through the Django ORM, with no specific SQL queries. The same application runs on:

| DBMS | `AHMIS_DB_ENGINE` | Driver to install |
|---|---|---|
| SQLite (demo, default) | `sqlite` | none |
| PostgreSQL | `postgresql` | `psycopg[binary]` |
| MySQL / MariaDB | `mysql` | `mysqlclient` |
| Oracle | `oracle` | `oracledb` |
| Microsoft SQL Server | `mssql` | `mssql-django` |

## Configuration

By environment variables:

```
AHMIS_DB_ENGINE=postgresql
AHMIS_DB_NAME=ahmis
AHMIS_DB_USER=ahmis
AHMIS_DB_PASSWORD=********
AHMIS_DB_HOST=srv-bdd.local
AHMIS_DB_PORT=5432
```

## Example: moving from SQLite to PostgreSQL

1. Create the database and the user in PostgreSQL.
2. Install the driver: `pip install "psycopg[binary]"`.
3. Export the data from the current SQLite database (without `AHMIS_DB_*` variables): `python manage.py dumpdata --natural-foreign --exclude contenttypes --exclude auth.permission -o ahmis_export.json`
4. Set the `AHMIS_DB_*` variables for PostgreSQL, then create the tables: `python manage.py migrate`
5. Import: `python manage.py loaddata ahmis_export.json`
6. Check with `python manage.py test apps` (the tests create their own temporary database) and by opening the application.

## Going into production: mandatory points

The demo is configured for a local workstation. Before any real use:

- `AHMIS_DEBUG=0` and a long, secret `AHMIS_SECRET_KEY`;
- `AHMIS_ALLOWED_HOSTS` = the server name;
- an application server (gunicorn, uWSGI or IIS) behind HTTPS: never `runserver`;
- backups of the database and of the `media/` folder (certificate scans), tested by restoration;
- named accounts, strong passwords, and removal of the demonstration accounts;
- `AHMIS_ORGANISATION`, `AHMIS_APPROVAL_145`, `AHMIS_APPROVAL_CAMO` filled in: they appear on the task cards and CRSs.

## Other settings

| Variable | Default | Role |
|---|---|---|
| `AHMIS_ALERT_DAYS` | 30 | "To plan" window |
| `AHMIS_FORECAST_DAYS` | 365 | Default forecast horizon |
| `AHMIS_TIME_ZONE` | Europe/Paris | Time zone of signatures |
