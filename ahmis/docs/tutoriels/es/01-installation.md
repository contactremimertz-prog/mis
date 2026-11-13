# 1. Instalación y puesta en marcha

## Requisitos previos

- **Python 3.10 o posterior**: [python.org/downloads](https://www.python.org/downloads/). En Windows, marque «Add python.exe to PATH» durante la instalación.
- Una conexión a internet en el primer arranque (descarga de Django).
- Ningún servidor de base de datos: la demo utiliza **SQLite**, un simple archivo (`db/ahmis.sqlite3`).

## Arrancar

**Windows**: haga doble clic en `demarrer.bat`.

**macOS / Linux**: en un terminal, desde la carpeta AHMIS:

```
./demarrer.sh
```

En el primer arranque, el script:

1. crea un entorno Python aislado (carpeta `.venv`);
2. instala las dependencias (`requirements.txt`);
3. crea la base de datos;
4. carga los datos de demostración;
5. abre el navegador en **http://127.0.0.1:8000**.

Los arranques posteriores reutilizan la base de datos existente: se conservan sus pruebas.

**Detener**: cierre la ventana (Windows) o pulse `Ctrl+C` en el terminal.

## Restablecer la demo

- Windows: `reinitialiser_demo.bat`
- macOS / Linux: `./reinitialiser_demo.sh`

La base de datos se vacía y se vuelve a cargar con la situación de partida descrita en el tutorial 0.

> Las fechas de la demo se calculan a partir del día de la carga. Si vuelve a abrir la demo varias semanas después, los vencimientos habrán «envejecido»: restablezca la demo para recuperar las situaciones descritas en los tutoriales.

## Iniciar sesión

La página de inicio de sesión muestra la lista de cuentas de demostración. Empiece con `admin` / `Ahmis2026!` para verlo todo.

## Ejecutar las pruebas automáticas

Las reglas de negocio (cálculo de límites, firmas, comprobaciones de montaje…) están cubiertas por pruebas:

```
python manage.py test apps
```

(se ejecuta tras activar el entorno: `.venv\Scripts\activate` en Windows, `. .venv/bin/activate` en macOS/Linux).

## En caso de problema

| Síntoma | Solución |
|---|---|
| «Python 3.10+ est requis» | Instalar Python y volver a ejecutar el script |
| El puerto 8000 está ocupado | Ejecutar `python manage.py runserver 127.0.0.1:8001` y abrir http://127.0.0.1:8001 |
| Página «Erreur de serveur» | Volver a arrancar; si persiste, restablecer la demo |
