# 1. Installation und Start

## Voraussetzungen

- **Python 3.10 oder neuer**: [python.org/downloads](https://www.python.org/downloads/). Unter Windows aktivieren Sie bei der Installation „Add python.exe to PATH“.
- Eine Internetverbindung beim ersten Start (Download von Django).
- Kein Datenbankserver: Die Demo verwendet **SQLite**, eine einfache Datei (`db/ahmis.sqlite3`).

## Starten

**Windows**: Doppelklick auf `demarrer.bat`.

**macOS / Linux**: in einem Terminal, im AHMIS-Ordner:

```
./demarrer.sh
```

Beim ersten Start führt das Skript Folgendes aus:

1. Es erstellt eine isolierte Python-Umgebung (Ordner `.venv`);
2. es installiert die Abhängigkeiten (`requirements.txt`);
3. es erstellt die Datenbank;
4. es lädt die Demodaten;
5. es öffnet den Browser auf **http://127.0.0.1:8000**.

Bei späteren Starts wird die vorhandene Datenbank weiterverwendet: Ihre Eingaben bleiben erhalten.

**Beenden**: Schließen Sie das Fenster (Windows) oder drücken Sie `Ctrl+C` im Terminal.

## Demo zurücksetzen

- Windows: `reinitialiser_demo.bat`
- macOS / Linux: `./reinitialiser_demo.sh`

Die Datenbank wird geleert und mit der in Tutorial 0 beschriebenen Ausgangslage neu geladen.

> Die Daten der Demo werden ab dem Tag des Ladens berechnet. Wenn Sie die Demo mehrere Wochen später wieder öffnen, sind die Fälligkeiten „gealtert“: Setzen Sie die Demo zurück, um die in den Tutorials beschriebenen Situationen wiederherzustellen.

## Anmelden

Die Anmeldeseite zeigt die Liste der Demokonten. Beginnen Sie mit `admin` / `Ahmis2026!`, um alles zu sehen.

## Automatische Tests ausführen

Die Fachregeln (Berechnung der Grenzen, Signaturen, Einbauprüfungen …) sind durch Tests abgedeckt:

```
python manage.py test apps
```

(nach Aktivierung der Umgebung auszuführen: `.venv\Scripts\activate` unter Windows, `. .venv/bin/activate` unter macOS/Linux).

## Bei Problemen

| Symptom | Lösung |
|---|---|
| „Python 3.10+ ist erforderlich“ | Python installieren, dann das Skript erneut starten |
| Port 8000 ist belegt | `python manage.py runserver 127.0.0.1:8001` starten und http://127.0.0.1:8001 öffnen |
| Seite „Serverfehler“ | Neu starten; falls das Problem bestehen bleibt, die Demo zurücksetzen |
