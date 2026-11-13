# 5. Komponenten, lebensdauerbegrenzte Teile (LLP) und TBO

**Konto: `camo`**

## Artikelreferenzen (P/N)

Menü **P/N-Referenzen** → klicken Sie auf `DEMO-350STR-01` (Hauptrotornabe NH90). Eine Referenz enthält:

- die Verfolgung nach Seriennummer (Pflicht für ein LLP oder ein Teil mit TBO);
- die **Lebensdauergrenzen** (LLP), seit neu: Stunden, Zyklen und/oder Tage;
- die **TBO**, Potenzial zwischen Überholungen: Stunden, Zyklen und/oder Tage;
- die anwendbaren Luftfahrzeugmuster (ein Einbau in einem anderen Muster wird abgelehnt);
- die austauschbaren P/N (werden bei einer Teileanforderung akzeptiert).

AHMIS lehnt ein LLP ohne Grenze sowie ein nicht seriennummerngeführtes LLP oder Teil mit TBO ab.

## Komponentenakte: die Rotornabe von F-HDMB

1. Globale Suche: `DEMO-S3502`.
2. Die Akte zeigt:
    - die Zähler TSN / CSN / TSO / CSO;
    - **Restpotenziale und Lebensdauergrenzen**: Grenze, verbraucht, verbleibend und einen Balken, der bei 90 % orange wird;
    - die Freigabezertifikate;
    - die **„Back-to-birth“-Rückverfolgbarkeit**: jede Montage (Luftfahrzeug, Position, Zähler beim Einbau und beim Ausbau, Grund, Task Card).

**Zu prüfen**: Von der Grenze von 5.000 FH verbleiben etwa 40 FH. Unter **Fälligkeiten** steht die Zeile „LLP“ von F-HDMB auf „Zu planen“.

## Konfiguration eines Luftfahrzeugs lesen

Öffnen Sie F-HDMA, Abschnitt **Eingebaute Konfiguration**: für jede Position (MOT 1, MOT 2, BTP, BTA, MRH, PALE 1-4 …) die Komponente, ihre Zähler und was ihr bei jeder Grenze verbleibt.

## LLP und TBO in den Fälligkeiten

AHMIS erzeugt automatisch eine Fälligkeit:

- **LLP** für jedes eingebaute lebensdauerbegrenzte Teil (zuerst erreichtes Kriterium aus Stunden, Zyklen und Kalender);
- **TBO** für jedes Teil mit Potenzial.

Sie erscheinen in den Fälligkeiten, in der Prognose und in der Planung und können einem Arbeitspaket hinzugefügt werden: Dabei wird eine Task Card „Aus-/Einbau“ erzeugt.

## Ein Teil an seiner Grenze ist unbrauchbar

Ein Teil, dessen Grenze erreicht ist, kann weder eingebaut noch ausgegeben noch wieder als „verwendbar“ gesetzt werden. Der automatische Test `test_expired_life_part_refused` prüft das.
