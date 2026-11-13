# 23. Cambiar de base de datos (SGBD)

AHMIS **no depende de ningún SGBD**: toda la persistencia pasa por el ORM de Django, sin consultas SQL específicas. La misma aplicación funciona sobre:

| SGBD | `AHMIS_DB_ENGINE` | Controlador a instalar |
|---|---|---|
| SQLite (demo, por defecto) | `sqlite` | ninguno |
| PostgreSQL | `postgresql` | `psycopg[binary]` |
| MySQL / MariaDB | `mysql` | `mysqlclient` |
| Oracle | `oracle` | `oracledb` |
| Microsoft SQL Server | `mssql` | `mssql-django` |

## Configuración

Mediante variables de entorno:

```
AHMIS_DB_ENGINE=postgresql
AHMIS_DB_NAME=ahmis
AHMIS_DB_USER=ahmis
AHMIS_DB_PASSWORD=********
AHMIS_DB_HOST=srv-bdd.local
AHMIS_DB_PORT=5432
```

## Ejemplo: pasar de SQLite a PostgreSQL

1. Cree la base de datos y el usuario en PostgreSQL.
2. Instale el controlador: `pip install "psycopg[binary]"`.
3. Exporte los datos desde la base SQLite actual (sin variables `AHMIS_DB_*`): `python manage.py dumpdata --natural-foreign --exclude contenttypes --exclude auth.permission -o ahmis_export.json`
4. Defina las variables `AHMIS_DB_*` para PostgreSQL y, a continuación, cree las tablas: `python manage.py migrate`
5. Importe: `python manage.py loaddata ahmis_export.json`
6. Verifique con `python manage.py test apps` (las pruebas crean su propia base de datos temporal) y abriendo la aplicación.

## Paso a producción: puntos obligatorios

La demo está configurada para un puesto local. Antes de cualquier uso real:

- `AHMIS_DEBUG=0` y una clave `AHMIS_SECRET_KEY` larga y secreta;
- `AHMIS_ALLOWED_HOSTS` = el nombre del servidor;
- un servidor de aplicaciones (gunicorn, uWSGI o IIS) detrás de HTTPS: nunca `runserver`;
- copias de seguridad de la base de datos y de la carpeta `media/` (escaneados de los certificados), probadas mediante restauración;
- cuentas nominativas, contraseñas robustas y eliminación de las cuentas de demostración;
- `AHMIS_ORGANISATION`, `AHMIS_APPROVAL_145`, `AHMIS_APPROVAL_CAMO` cumplimentados: figuran en las task cards y los CRS.

## Otros parámetros

| Variable | Valor por defecto | Función |
|---|---|---|
| `AHMIS_ALERT_DAYS` | 30 | Ventana «Por planificar» |
| `AHMIS_FORECAST_DAYS` | 365 | Horizonte por defecto de la previsión |
| `AHMIS_TIME_ZONE` | Europe/Paris | Zona horaria de las firmas |
