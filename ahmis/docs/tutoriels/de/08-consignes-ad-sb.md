# 8. Lufttüchtigkeitsanweisungen (AD) und Service Bulletins (SB)

**Konto: `camo`**

## Der Lebenszyklus einer Anweisung

1. Die Anweisung **erfassen**: Nummer, Herausgeber, Datum des Inkrafttretens, betroffene Muster und/oder P/N.
2. AHMIS legt automatisch einen Status **„Zu bewerten“** für jedes potenziell betroffene Luftfahrzeug an (gleiches Muster oder betroffene P/N eingebaut).
3. Die CAMO **bewertet** jedes Luftfahrzeug:
    - **Nicht anwendbar**: Die Begründung ist Pflicht;
    - **Anwendbar – durchzuführen**: Es ist eine **Folgeaufgabe** erforderlich;
    - **Durchgeführt**: Das Durchführungsdatum ist Pflicht.
4. Die Folgeaufgabe erscheint in den Fälligkeiten. Die Frist zählt **ab dem Datum des Inkrafttretens**.
5. Beim Abschluss der Task Card wechselt der Status auf **Durchgeführt** (einmalige Anweisung) oder **Wiederkehrend laufend**.

## Übung 1: Die ATR-AD bewerten

1. Menü **AD / SB** → `DEMO-AD-2026-0177` (ATR 72, Klappenbeschläge).
2. Zeile F-HDMF: Status **Zu bewerten** → **Bewerten**.
3. Status „Anwendbar – durchzuführen“, Begründung `MSN 1801 dans la plage d'applicabilité` → **Speichern**.
4. Schaltfläche **Folgeaufgabe anlegen (ATR72-600)**: Referenz, Bezeichnung und erforderliche Maßnahme sind vorausgefüllt.
5. Tragen Sie die **Schwelle Zyklen** `3000` (Frist ab Inkrafttreten) und den Aufwand `4` ein und speichern Sie.

**Ergebnis**: Unter **Fälligkeiten** hat F-HDMF eine neue Zeile mit einer Zyklengrenze, die den Zyklen beim Inkrafttreten + 3.000 entspricht.

## Übung 2: Eine Nichtanwendbarkeit erklären

1. `DEMO-SB-145-24-010` (optionales SB H145) → F-HDMD → **Bewerten**.
2. Wählen Sie „Nicht anwendbar“ **ohne** Begründung → **Speichern**: abgelehnt.
3. Fügen Sie `SB optionnel non retenu par l'exploitant – décision CAMO du jj/mm` hinzu → **Speichern**.

## Übung 3: Eine wiederkehrende AD verfolgen

`DEMO-AD-2026-0101` (Aufhängungsstreben des Hauptgetriebes NH90) wird durch eine Aufgabe mit einer Schwelle von 50 FH und einem Intervall von 110 FH verfolgt:

- bei **F-HDMA** wurde sie durchgeführt: Status „Wiederkehrend laufend“, nächste Fälligkeit 110 FH später;
- bei **F-HDMB** wurde sie nie durchgeführt: **Überfällig**. Tutorial 24 behandelt sie.

## Gesamtübersicht

Schaltfläche **Status je Luftfahrzeug** in der AD/SB-Liste: alle Bewertungen, mit Filtern nach Status und nach Luftfahrzeug. Das ist das Grunddokument der Lufttüchtigkeitsprüfung.
