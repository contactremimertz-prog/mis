# 3. Ein Muster und ein Luftfahrzeug anlegen, Konfiguration übernehmen

**Konto: `camo`**

Ziel: eine neue NH90, F-HDMX, mit ihrem ersten Triebwerk in die Flotte aufnehmen.

## 1. Das Luftfahrzeugmuster

Das Muster NH90 existiert bereits. So sehen Sie, wie ein Muster definiert ist:

1. Menü **Muster & Konfiguration** → klicken Sie auf **NH90**.
2. Die Akte zeigt die Luftfahrzeuge des Musters, das **Instandhaltungsprogramm** (aktive Aufgaben), das berechtigte Personal und die anwendbaren P/N.

Um ein neues Muster anzulegen: Schaltfläche **+ Anlegen** in der Liste. Mit dem Feld „Bezeichnung der Zyklen“ kann für einen Hubschrauber „Landungen“ angezeigt werden.

## 2. Das Luftfahrzeug anlegen

1. Menü **Flotte** → **+ Anlegen**.
2. Geben Sie ein:
    - Kennzeichen: `F-HDMX`
    - Seriennummer: `9199`
    - Muster: `NHIndustries NH90`
    - Herstellungsdatum: vor 3 Jahren
    - Gesamtstunden: `1250`; Zyklen: `3800`; Zähler aktuell zum: heute
    - Geplante Nutzung: `1.5` FH/Tag und `4` Zyklen/Tag
3. **Speichern**.

**Ergebnis**: Die Akte öffnet sich. Alle Aufgaben des NH90-Programms erscheinen bereits unter **Fälligkeiten**. Da keine Historie vorhanden ist, werden die meisten ab der Herstellung berechnet und erscheinen als **„Überfällig“**. Das ist gewollt: AHMIS nimmt nie an, dass eine Aufgabe durchgeführt wurde.

> Die Zähler können nur bei der Anlage eingegeben werden. Danach ändern sie sich ausschließlich durch die Erfassung von Flugstunden (Tutorial 4), damit die Rückverfolgbarkeit lückenlos bleibt.

## 3. Die Aufgabenhistorie übernehmen

Erfassen Sie für jede Aufgabe die letzte bekannte Durchführung (aus dem Logbuch entnommen):

1. Klicken Sie in der Fälligkeitstabelle von F-HDMX auf die Aufgabe **N90-05-100 Visite 100 h / 12 mois**.
2. Klicken Sie unter „Lage je Luftfahrzeug“ in der Zeile F-HDMX auf **historisch**.
3. Geben Sie ein: Datum vor 2 Monaten, FH `1190`, Zyklen `3620`, Herkunft „Historische Erfassung“, Referenz `Logbook p.42`, bescheinigt durch `Atelier X – CRS 1234`.
4. **Speichern**.

**Ergebnis**: Der 100-h-Check von F-HDMX ist nun bei 1.290 FH fällig (1.190 + 100), also noch 40 FH verbleibend.

## 4. Die Konfiguration übernehmen (eingebaute Komponenten)

Die Komponente kommt zuerst mit ihrem Zertifikat ins Lager, dann ordnet die CAMO sie dem Luftfahrzeug zu:

1. Konto **`magasin`** → Menü **Wareneingang**: P/N `DEMO-ARR2D-0001` (RTM322), S/N `DEMO-E2X99`, Menge 1, Lagerort `MAG-PRINC`, Zustand „Überholt“, TSN `1250`, CSN `3800`, TSO `1250`, CSO `3800`. Zertifikat: EASA Form 1, Nr. `F1-TEST-01`, Aussteller `Atelier moteur agréé`, heutiges Datum, Status „Überholt“. Haken Sie die 3 Eingangsprüfungen an → **Speichern**.
2. Konto **`camo`** → öffnen Sie F-HDMX → **Konfigurationsübernahme**: Komponente `DEMO-E2X99`, Position `MOT 1`, Datum = Indienststellung, Referenz `Relevé de configuration d'entrée en flotte` → **Speichern**.

**Ergebnis**: Das Triebwerk erscheint unter „Eingebaute Konfiguration“ mit seiner verbleibenden TBO (4.000 − 1.250 = 2.750 FH). Die Komponentenaufgabe **N90-72-500** (Boroskopie des Triebwerks) erscheint in den Fälligkeiten, „Überfällig“, solange ihre letzte Durchführung nicht übernommen wurde. Gehen Sie dazu wie in Schritt 3 vor, wählen Sie die Komponente `DEMO-E2X99` und ihre Zähler (TSN/CSN) zum Datum der letzten Boroskopie.

> Die Konfigurationsübernahme dient ausschließlich der Aufnahme in die Flotte. Im Betrieb läuft jede Komponentenbewegung über eine Task Card (Tutorial 14).
