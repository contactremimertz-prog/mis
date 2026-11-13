# 23. Das Datenbanksystem wechseln (DBMS)

AHMIS **hängt von keinem DBMS ab**: Die gesamte Persistenz läuft über den Django-ORM, ohne spezifische SQL-Abfragen. Dieselbe Anwendung läuft auf:

| DBMS | `AHMIS_DB_ENGINE` | Zu installierender Treiber |
|---|---|---|
| SQLite (Demo, Standard) | `sqlite` | keiner |
| PostgreSQL | `postgresql` | `psycopg[binary]` |
| MySQL / MariaDB | `mysql` | `mysqlclient` |
| Oracle | `oracle` | `oracledb` |
| Microsoft SQL Server | `mssql` | `mssql-django` |

## Konfiguration

Über Umgebungsvariablen:

```
AHMIS_DB_ENGINE=postgresql
AHMIS_DB_NAME=ahmis
AHMIS_DB_USER=ahmis
AHMIS_DB_PASSWORD=********
AHMIS_DB_HOST=srv-bdd.local
AHMIS_DB_PORT=5432
```

## Beispiel: von SQLite auf PostgreSQL umsteigen

1. Legen Sie die Datenbank und den Benutzer in PostgreSQL an.
2. Installieren Sie den Treiber: `pip install "psycopg[binary]"`.
3. Exportieren Sie die Daten aus der aktuellen SQLite-Datenbank (ohne `AHMIS_DB_*`-Variablen): `python manage.py dumpdata --natural-foreign --exclude contenttypes --exclude auth.permission -o ahmis_export.json`
4. Setzen Sie die `AHMIS_DB_*`-Variablen für PostgreSQL und erstellen Sie dann die Tabellen: `python manage.py migrate`
5. Importieren Sie: `python manage.py loaddata ahmis_export.json`
6. Prüfen Sie mit `python manage.py test apps` (die Tests erstellen ihre eigene temporäre Datenbank) und durch Öffnen der Anwendung.

## Übergang in den Produktivbetrieb: Pflichtpunkte

Die Demo ist für einen lokalen Arbeitsplatz konfiguriert. Vor jeder realen Nutzung:

- `AHMIS_DEBUG=0` und ein langer, geheimer Schlüssel `AHMIS_SECRET_KEY`;
- `AHMIS_ALLOWED_HOSTS` = der Servername;
- ein Anwendungsserver (gunicorn, uWSGI oder IIS) hinter HTTPS: niemals `runserver`;
- Sicherungen der Datenbank und des Ordners `media/` (Zertifikatsscans), durch Wiederherstellung getestet;
- personenbezogene Konten, starke Passwörter und Löschung der Demokonten;
- `AHMIS_ORGANISATION`, `AHMIS_APPROVAL_145`, `AHMIS_APPROVAL_CAMO` ausgefüllt: Sie erscheinen auf den Task Cards und den CRS.

## Weitere Parameter

| Variable | Standard | Funktion |
|---|---|---|
| `AHMIS_ALERT_DAYS` | 30 | Fenster „Zu planen“ |
| `AHMIS_FORECAST_DAYS` | 365 | Standardhorizont der Prognose |
| `AHMIS_TIME_ZONE` | Europe/Paris | Zeitzone der Signaturen |
