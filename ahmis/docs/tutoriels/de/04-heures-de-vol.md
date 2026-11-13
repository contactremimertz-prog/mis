# 4. Flugstunden und Zyklen erfassen

**Konto: `planif` (oder `b1`)**

Die Stunden und Landungen (Zyklen) stammen aus den Bordbuchberichten (Techlog / CRM).

## Erfassung

1. Übersicht → **Flugstunden erfassen** (oder Menü **Flugstunden** → **+ Anlegen**).
2. Luftfahrzeug `F-HDMA`, Datum heute, Stunden `1.8`, Zyklen `5`, Referenz `CRM MA-TEST`.
3. **Speichern**.

Eine Meldung zeigt die neuen Summen an.

## Was AHMIS tut

- Es erhöht die Zähler der **Zelle**.
- Es erhöht die Zähler **aller eingebauten Komponenten**: TSN/CSN (seit neu) und TSO/CSO (seit Überholung).
- Es berechnet die Fälligkeiten sofort neu.

**Zu prüfen**:

1. Öffnen Sie F-HDMA: Die Gesamtstunden sind um 1,8 gestiegen.
2. Unter „Eingebaute Konfiguration“ ist auch das TSO des Hauptgetriebes um 1,8 gestiegen, und seine „verbleibende TBO“ ist entsprechend gesunken.
3. In den Fälligkeiten ist der „FH verbleibend“-Wert des 100-h-Checks um 1,8 gesunken.

## Eingabeprüfungen

- Mehr als 24 h an einem Tag werden abgelehnt.
- Ein zukünftiges Datum wird abgelehnt.
- Eine Erfassung ist nie änderbar: Ein Fehler wird durch eine neue, begründete Erfassung korrigiert, und die Historie bleibt vollständig (Menü **Flugstunden**).

## Geplante Nutzung und voraussichtliche Daten

In der Luftfahrzeugakte dient die „geplante Nutzung“ (FH/Tag, Zyklen/Tag) dazu, die verbleibenden Stunden in ein **geplantes Datum** umzurechnen. Beispiel: 12 verbleibende FH bei 1,6 FH/Tag ergeben eine Fälligkeit in 7 Tagen. Ändern Sie diesen Wert (Schaltfläche **Bearbeiten** des Luftfahrzeugs, Konto `camo`), um zu sehen, wie sich die geplanten Daten verschieben.
