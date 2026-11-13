# 1. Installation and start-up

## Prerequisites

- **Python 3.10 or later**: [python.org/downloads](https://www.python.org/downloads/). On Windows, tick "Add python.exe to PATH" during installation.
- An internet connection on first launch (download of Django).
- No database server: the demo uses **SQLite**, a simple file (`db/ahmis.sqlite3`).

## Starting

**Windows**: double-click `demarrer.bat`.

**macOS / Linux**: in a terminal, from the AHMIS folder:

```
./demarrer.sh
```

On first launch, the script:

1. creates an isolated Python environment (`.venv` folder);
2. installs the dependencies (`requirements.txt`);
3. creates the database;
4. loads the demonstration data;
5. opens the browser at **http://127.0.0.1:8000**.

Subsequent launches reuse the existing database: your tests are kept.

**Stopping**: close the window (Windows) or press `Ctrl+C` in the terminal.

## Resetting the demo

- Windows: `reinitialiser_demo.bat`
- macOS / Linux: `./reinitialiser_demo.sh`

The database is emptied and then reloaded with the starting situation described in tutorial 0.

> The demo dates are calculated from the day of loading. If you reopen the demo several weeks later, the due items will have "aged": reset to get back the situations described in the tutorials.

## Logging in

The login page displays the list of demonstration accounts. Start with `admin` / `Ahmis2026!` to see everything.

## Running the automated tests

The business rules (calculation of limits, signatures, installation checks, etc.) are covered by tests:

```
python manage.py test apps
```

(to be run after activating the environment: `.venv\Scripts\activate` on Windows, `. .venv/bin/activate` on macOS/Linux).

## In case of problems

| Symptom | Solution |
|---|---|
| "Python 3.10+ est requis" | Install Python then relaunch the script |
| Port 8000 is in use | Run `python manage.py runserver 127.0.0.1:8001` and open http://127.0.0.1:8001 |
| "Server error" page | Relaunch; if it persists, reset the demo |
