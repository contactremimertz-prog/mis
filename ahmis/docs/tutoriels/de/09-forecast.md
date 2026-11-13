# 9. Die Prognose (Instandhaltungsvorschau)

**Konto: `camo` oder `planif`**

Menü **Prognose**.

## Prinzip

Die Prognose **rollt** alle Fälligkeiten über einen vorgegebenen Zeithorizont **ab**:

- eine wiederkehrende Aufgabe erzeugt mehrere Vorkommen (z. B. kehrt die 50-FH-Schmierung einer H145 bei 2 FH/Tag alle 25 Tage wieder);
- LLP, TBO, ARC und zurückgestellte Mängel erscheinen einmal;
- bereits überfällige Positionen werden auf heute gesetzt, mit dem Badge „überfällig“.

## Lesen

- Kennzahlen: Anzahl der Fälligkeiten, **gesamter Aufwand in Mannstunden**, Anzahl der Ausbauten an der Grenze.
- **Monatlicher Aufwand**: ein Histogramm je Monat, mit Aufteilung nach Luftfahrzeug.
- Das Detail jedes Monats öffnet sich per Klick: Vorkommen, Kriterium, Aufwand, **vorgesehene Teile** und Teilebedarf des Monats (abgeleitet aus den „benötigten Teilen“ der Aufgaben).

## Übungen

1. Horizont `365` Tage, gesamte Flotte → **Berechnen**. Suchen Sie den Monat des **C-Checks der ATR** (600 h.h): eine Aufwandsspitze, die vorab zu berücksichtigen ist.
2. Luftfahrzeug `F-HDMD`, Horizont `180` Tage: der H145-spezifische Aufwand.
3. **Simulation**: gesamte Flotte, Nutzung `130` % → **Berechnen**. Die Fälligkeiten in Stunden und Zyklen rücken näher; die kalendarischen verschieben sich nicht. Vergleichen Sie mit 100 %.
4. **CSV-Export**: die vollständige Liste der Vorkommen, für eine Tabellenkalkulation oder ein Planungswerkzeug.

> Die Prognose ist eine Projektion auf Basis der „geplanten Nutzung“ jedes Luftfahrzeugs. Halten Sie diese Werte aktuell (Luftfahrzeugakte), damit die Vorhersage verlässlich bleibt.
