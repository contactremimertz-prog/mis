# 24. Vollständiges Szenario: von der überfälligen AD zum CRS (F-HDMB)

Dieses Szenario verkettet die Rollen an einem realistischen Fall. Dauer: etwa 20 Minuten. Beginnen Sie mit einer zurückgesetzten Demo.

**Lage**: Bei der NH90 F-HDMB ist die AD `DEMO-AD-2026-0101` (Aufhängungsstreben des Hauptgetriebes) **überfällig** und der 100-h-Check **in der Toleranz**.

## Schritt 1 – CAMO: feststellen und am Boden halten (`camo`)

1. Übersicht → Zeile F-HDMB → überfällige Fälligkeiten.
2. **Fälligkeiten**, Filter F-HDMB: Beachten Sie die überfällige AD und den 100-h-Check in der Toleranz.
3. Eine überfällige AD verbietet den Flug: Öffnen Sie F-HDMB → **Bearbeiten** → Status **AOG (am Boden)** → **Speichern**. Die Änderung wird in der Historie protokolliert.

## Schritt 2 – Planung (`planif`)

1. **Fälligkeiten**, Filter F-HDMB.
2. Haken Sie die AD, den 100-h-Check und die Schmierung `N90-62-050` an.
3. Arbeitspaket: das bestehende WP **Visite 100 h** → **Task Cards anlegen**.
4. Im WP → **Bearbeiten**: Beginn heute, Ende morgen, Status „Geplant“.

## Schritt 3 – Durchführung des Checks (`meca`)

1. Task Card **Visite 100 h / 12 mois** → **Starten**.
2. Signieren Sie die 6 Schritte (jedes Mal mit Passwort).
3. Geben Sie das Werkzeug `TENS-01` (Spannungsmesser) aus und geben Sie es dann zurück.
4. Arbeitsbericht `Visite 100 h effectuée, RAS`, 7 h.h → **Arbeiten signieren**: Die Task Card wird abgeschlossen.
5. Verfahren Sie ebenso mit der **Schmierung**.

## Schritt 4 – Durchführung der AD (`b1`)

1. Task Card **Inspection des barres de suspension BTP (AD)** → **Starten**, dann die 4 Schritte signieren.
2. Während der Inspektion tritt eine Auffälligkeit auf: Feld **Feststellung melden**, `Trace de frottement sur barre avant gauche, dans les tolérances du manuel`. Ein Mangel und eine Task Card zur Behebung werden angelegt.
3. Kehren Sie zur AD-Task-Card zurück → Arbeitsbericht `Inspection conforme à l'AD, constatation traitée sur task card dédiée` → **Arbeiten signieren**. Sie wechselt auf „wartet auf Prüfung“: Die Aufgabe ist kritisch.

## Schritt 5 – Feststellung (`b1`)

Öffnen Sie die Task Card zur Behebung → **Starten** → Arbeitsbericht `Mesure de la trace : conforme, protection appliquée` → **Arbeiten signieren**. Der Mangel ist **behoben**.

## Schritt 6 – Unabhängige Prüfung (`certc`)

AD-Task-Card → **Prüfung signieren** (Bemerkungen `Conforme`). Sie wird abgeschlossen.

**Zu prüfen** (Konto `camo`):

- **AD / SB** → `DEMO-AD-2026-0101` → F-HDMB: Status **„Anwendbar – wiederkehrend laufend“**, mit Datum und Zählern der Durchführung;
- **Fälligkeiten** F-HDMB: Die AD steht auf „OK“, nächste Grenze in 110 FH; der 100-h-Check steht auf „OK“.

## Schritt 7 – CRS (`b1`)

WP → Feld CRS: keine Sperre mehr → Passwort → **CRS signieren**. Das WP ist **Freigegeben** und gesperrt.

## Schritt 8 – Rückkehr in den Betrieb (`camo`)

Das CRS hat F-HDMB automatisch wieder auf **In Betrieb** gesetzt (es tut dies für ein Luftfahrzeug „In Instandhaltung“ oder „AOG“). Prüfen Sie die **Übersicht**: F-HDMB hat keine überfällige Fälligkeit mehr, aber die Rotornabe (LLP) bleibt zu planen.

## Schritt 9 – Qualitätskontrolle (`qualite`)

- **Elektronische Signaturen**: alle Signaturen des Szenarios, jede „✓ intakt“.
- **Audit-Trail**, Suche `F-HDMB`: die Stilllegung am Boden, die Anlage des WP, die Task Cards, die Status …
- **Akte drucken** des WP: die vollständige Papierakte mit dem CRS.

Bravo, Sie haben die gesamte Kette CAMO → Part-145 → Logistik → Qualität durchlaufen.
