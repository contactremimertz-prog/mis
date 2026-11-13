# 6. Das Instandhaltungsprogramm (Aufgaben)

**Konto: `camo`**

## Einsehen

Menü **Instandhaltungsprogramm**: 33 Demoaufgaben. Filtern Sie nach Muster (`H145`) oder nach Herkunft (MSM/MPD, ALS, AD, SB, Betreiber).

Öffnen Sie **145-05-100 Visite 100 h / 12 mois**:

- **Intervall** `100 FH / 1 an`: Das **zuerst erreichte Kriterium** löst die Fälligkeit aus.
- **Toleranz** `10 FH / 30 j`: Jenseits der Grenze, aber innerhalb der Toleranz lautet der Status „In der Toleranz“ (dunkles Orange). Jenseits der Toleranz lautet er „Überfällig“ (rot).
- **Schritte**: Jede Zeile wird zu einem Schritt, der auf der Task Card zu signieren ist.
- **Benötigte Teile**: Sie speisen die Prognose (monatlicher Teilebedarf).
- **Lage je Luftfahrzeug**: letzte Durchführung, Grenzen, Reste, geplantes Datum für jede H145.

## Eine Aufgabe anlegen

1. **+ Anlegen** (oder aus der Akte des Musters NH90: „Aufgabe hinzufügen“).
2. Beispiel:
    - Referenz `N90-25-180`, Bezeichnung `Contrôle du kit de flottaison`, Muster NH90
    - Art: Funktionsprüfung; ATA `25`
    - Intervall: `180` Tage; Toleranz: `15` Tage
    - Aufwand: `2` h.h; Qualifikation B1
    - Schritte: `Déplier le kit` / `Contrôler la pression des bouteilles` / `Replier et plomber` (einer pro Zeile)
3. **Speichern**, dann ein benötigtes Teil hinzufügen (z. B. `DEMO-ORING-12` × 2).

**Ergebnis**: Die Aufgabe gilt sofort für alle NH90 (F-HDMA, F-HDMB). Lassen Sie „Effektivität“ leer für alle Luftfahrzeuge des Musters, oder haken Sie bestimmte Kennzeichen an.

## Schwelle (erste Fälligkeit)

Eine vom Intervall abweichende Schwelle wird unter „Schwelle FH/Zyklen/Tage“ eingetragen. Beispiel: erste Inspektion bei 1.200 FH, danach alle 500 FH.

## An einer Komponente geführte Aufgabe

Wird „Komponenten-P/N“ ausgefüllt, so bezieht sich die Aufgabe auf die Zähler **der Komponente** und nicht auf die der Zelle. Siehe **N90-72-500** (Boroskopie RTM322): Die Fälligkeit folgt dem Triebwerk, auch wenn es den Hubschrauber wechselt.

## Aufgabe mit unabhängiger Prüfung

Haken Sie „unabhängige Prüfung erforderlich“ für kritische Aufgaben an (Flugsteuerung, Befestigungen des Hauptgetriebes …). Die Task Card verlangt dann eine zweite Signatur durch eine andere freigabeberechtigte Person (Tutorial 13).

## Revisionen des Programms

Jede Änderung wird protokolliert: Schaltfläche **Revisionshistorie** in der Aufgabenakte. Füllen Sie auch „AMP-Revision“ aus. Eine Aufgabe wird nicht gelöscht: Entfernen Sie den Haken bei „aktiv“.
