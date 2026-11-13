# 11. Planung und Arbeitspakete

**Konto: `planif`**

Ein **Arbeitspaket (WP)** fasst die Arbeiten an einem Luftfahrzeug für eine Standzeit zusammen: Termine, Station, Check-Art und Task Cards.

## Die Hangarplanung

Menü **Planung**: eine Zeile je Luftfahrzeug, eine Spalte je Tag (8 Wochen).

- Die **Balken** sind die WP: blau = geplant, orange = laufend, grün = freigegeben.
- Die **Punkte** sind die Fälligkeiten: rot = überfällig, orange = zu planen, grau = vorgesehen.
- Fahren Sie über einen Punkt oder Balken für das Detail; klicken Sie zum Öffnen.
- Schaltflächen „← 4 Wochen / 4 Wochen →“ zum Navigieren.

**Suchen Sie**: das laufende WP von F-HDMD, das in 5 Tagen geplante WP von F-HDMB und die roten Punkte von F-HDMB (überfällige AD).

## Ein Arbeitspaket anlegen

1. **Neues Arbeitspaket**.
2. Luftfahrzeug `F-HDMA`, Bezeichnung `Visite 100 h`, Art „Periodischer Check“, Station `Base Alpes`, von nächstem Montag bis Dienstag, Status „Geplant“.
3. **Speichern**: Die Nummer `WP-JJJJ-NNNN` wird automatisch vergeben.

## Das Arbeitspaket füllen

In der WP-Akte:

1. **Fällige Positionen hinzufügen**: Die Liste bietet die Fälligkeiten des Luftfahrzeugs bis 30 Tage nach Ende des WP an, außer den bereits eingeplanten. Haken Sie `N90-05-100`, `DEMO-AD-2026-0101` und `N90-24-365` an → **Ausgewählte Task Cards anlegen**.
2. **Eine Programmaufgabe hinzufügen**: Wählen Sie eine nicht fällige Aufgabe, zum Beispiel `N90-63-200`, um sie vorzuziehen.
3. **Zusätzliche Arbeit**: eine Task Card außerhalb des Programms, zum Beispiel `Remplacement ampoule phare d'atterrissage`, ATA `33`, 0,5 h.h.

**Ergebnis**:

- Jede Task Card übernimmt Bezeichnung, ATA, Zone, Qualifikation, Aufwand und die **Schritte** der Aufgabe;
- die Karte „Geplanter Aufwand“ des WP summiert die Mannstunden;
- die hinzugefügten Positionen verschwinden aus der Liste der „fälligen Positionen“ (keine Doppelung).

## Drucken

**Akte drucken**: die Zusammenfassung des WP und das CRS in Papierform. Jede Task Card hat außerdem ihre Schaltfläche **Drucken**, für Werkstätten, die auf Papier arbeiten.

## Status eines WP

| Status | Übergang |
|---|---|
| Entwurf / Geplant | Bei der Anlage |
| Laufend | Automatisch beim Start der 1. Task Card (das Luftfahrzeug wechselt auf „In Instandhaltung“) |
| Freigegeben | Bei Signatur des CRS (Tutorial 16): Das WP ist dann **gesperrt** |
| Storniert | Manuell, über „Bearbeiten“ |
