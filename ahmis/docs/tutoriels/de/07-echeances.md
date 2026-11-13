# 7. Die Fälligkeiten (Grenzen)

**Konto: `camo`**

Menü **Fälligkeiten**: die konsolidierte Liste von allem, was in der Flotte fällig wird.

## Die Arten von Fälligkeiten

| Art | Herkunft |
|---|---|
| Aufgabe | Instandhaltungsprogramm (Zelle) |
| Komponentenaufgabe | An den Zählern einer Komponente geführte Aufgabe |
| LLP / TBO | Grenzen der eingebauten Komponenten |
| ARC | Ablauf der Lufttüchtigkeitsprüfung |
| Zurückgestellter Mangel | MEL/CDL-Grenze eines zurückgestellten Mangels |
| Anweisung | Zu bewertende AD/SB oder anwendbar ohne Folgeaufgabe |

## Die Status

| Status | Bedeutung |
|---|---|
| **Überfällig** (rot) | Grenze über die Toleranz hinaus überschritten |
| **In der Toleranz** | Grenze überschritten, aber innerhalb der zulässigen Toleranz |
| **Zu planen** (orange) | Geplantes Datum innerhalb von 30 Tagen (Parameter `AHMIS_ALERT_DAYS`) |
| **OK** | Später |

## Eine Zeile lesen

- **Letzte Durchführung**: Datum und Zähler.
- **Grenze** FH / Zyklen / Datum.
- **Rest** FH / Zyklen (negativ in Rot).
- **Geplantes Datum**: das früheste der für jedes Kriterium ermittelten Daten, unter Projektion der geplanten Nutzung.
- **Kriterium**: das auslösende (FH, Zyklen oder Kalender).

## Übungen

1. Filter **Luftfahrzeug = F-HDMB**.
    - `DEMO-AD-2026-0101`: **Überfällig**, −27,6 FH. Die AD ist vor 200 Tagen mit einer Frist von 50 FH in Kraft getreten und wurde nie durchgeführt.
    - `N90-05-100`: **In der Toleranz** (−6 FH bei einer Toleranz von 10 FH).
    - LLP Rotornabe: **Zu planen**.
2. Filter **Art = LLP**, dann **Status = Zu planen**.
3. Filter **Fällig innerhalb = 90 Tage**, dann **CSV-Export**: Die Datei öffnet sich in Excel (Trennzeichen „;“).

## Aus den Fälligkeiten planen

**Konto: `planif`** (die CAMO ermittelt den Bedarf, der Planer ordnet ihn einem Arbeitspaket zu). Sobald ein Luftfahrzeug ausgewählt ist, erscheinen Kontrollkästchen:

1. Filter **F-HDMB**.
2. Haken Sie `DEMO-AD-2026-0101`, `N90-05-100` und das LLP Rotornabe an.
3. Arbeitspaket: Wählen Sie **WP … Visite 100 h** (bereits in 5 Tagen geplant).
4. **Task Cards anlegen**.

**Ergebnis**: Sie gelangen zum Arbeitspaket mit 3 erzeugten Task Cards: die Schritte der Aufgabe und eine Task Card „Aus-/Einbau“ für das LLP. Weiter geht es in Tutorial 11.
