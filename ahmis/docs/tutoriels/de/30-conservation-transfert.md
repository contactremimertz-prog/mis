# 30. Aufbewahrung und Übergabe von Akten

**Konten: `qualite`, `camo`**

## Teil A: Aufbewahrung der Aufzeichnungen

Aufzeichnungen haben Mindestaufbewahrungsfristen:

| Aufzeichnungen | Mindestdauer | Referenz |
|---|---|---|
| Arbeitspakete, Task Cards, CRS, Mängel | 36 Monate nach der Freigabe | 145.A.55(c), M.A.305(h) |
| Aufgabendurchführungen | 36 Monate und bis zur Ersetzung durch eine neuere Durchführung | M.A.305(h) |
| Gesamtzeiten, Stand der AD, LLP, Änderungen, Ein- / Ausbauten | 12 Monate nach der endgültigen Ausmusterung des Luftfahrzeugs (oder der Komponente) | M.A.305(h)(1) |
| Personalakte | 3 Jahre nach dem Ausscheiden | 145.A.35(j) |
| ARC, Programmüberprüfungen, Kalibrierungen, Ereignismeldungen | 36 Monate | CAMO.A.220, 145.A.55 |

**AHMIS löscht nie automatisch etwas.** Es lehnt jede Einzellöschung ab und lehnt auch eine Massenlöschung (Administration, Skript) eines noch aufbewahrungspflichtigen Datensatzes ab.

### 1. Aufbewahrungsbericht

Konto `qualite` → Menü **Aufbewahrung der Aufzeichnungen**. Für jede Art von Aufzeichnung zeigt der Bericht die Gesamtzahl, dann drei Zähler:

- **ohne Frist**: aufzubewahren, zum Beispiel bei einem noch betriebenen Luftfahrzeug;
- **laufend**: Mindestdauer nicht erreicht;
- **abgelaufen**: archivierbar, auf dokumentierte Entscheidung gemäß MOE oder CAME.

Ein CSV-Export ist je Zeile verfügbar. In der Demo sind abgelaufen: der Hubschrauber **F-HDMZ** (vor 20 Monaten ausgemustert) und seine Flugstunden sowie der ehemalige Mitarbeiter **Paul ANCIEN** (vor 4 Jahren ausgeschieden).

### 2. Ein Luftfahrzeug aus dem Dienst nehmen

Luftfahrzeugakte → **Bearbeiten** → Status „Ausgemustert“ und **endgültig außer Dienst gestellt am**. Das Datum ist für ein ausgemustertes Luftfahrzeug Pflicht und sonst verboten. Es lässt die Frist von 12 Monaten beginnen. Das Luftfahrzeug verschwindet aus den Fälligkeiten und der Übersicht, und seine Akte zeigt das Ende der Aufbewahrungsfrist an.

Bei einem Personalabgang: Personalakte → Haken bei „aktiv“ entfernen und **aus der Organisation ausgeschieden am** ausfüllen.

## Teil B: Übergabe der Akte eines Luftfahrzeugs (M.A.307)

Wechselt ein Luftfahrzeug die CAMO oder den Eigentümer, werden seine Lufttüchtigkeitsaufzeichnungen an die neue Organisation übergeben.

### 3. Ausgehende Übergabe

1. Konto `camo` → Akte **F-HDMA** → **Akte exportieren**.
2. Richtung „Ausgehende Übergabe“, Organisation `CAMO Héli Nord (DEMO)`, Genehmigung `FR.CAMO.0999`, Grund `Changement de gestionnaire de navigabilité` → **Speichern**.

**Ergebnis**: AHMIS erzeugt das Archiv `dossier-F-HDMA-TR-....zip` und bewahrt es mit seinem SHA-256-Hashwert auf:

- `synthese.html`: druckbarer Lufttüchtigkeitsstatus (Gesamtzeiten, Fälligkeiten, Komponenten, LLP und TBO, AD, Änderungen, zurückgestellte Mängel);
- `dossier.json` und `csv/`: alle Daten (Stunden, Durchführungen, Ein- / Ausbauten, Zertifikate, Arbeitspakete, Task Cards, Signaturen mit ihrem Hashwert);
- `manifest.json`: Hashwert jeder Datei.

Bestätigt die neue Organisation den Empfang, erfassen Sie in der Übergabeakte **Empfangsbestätigung erfassen**. Die Demo enthält die Übergabe von F-HDMZ an den Erwerber der Zelle, bereits bestätigt.

### 4. Eingehende Übergabe

Menü **Aktenübergaben** → **+ Anlegen** → Richtung „Eingehende Übergabe“, dann hängen Sie das erhaltene Archiv an. AHMIS prüft die Hashwerte des Manifests:

- intaktes Archiv: grüner Banner;
- geänderte, fehlende oder hinzugefügte Datei oder Akte einer anderen MSN: Banner **ANOMALIE** mit Detail.

Die Übernahme der Daten erfolgt anschließend durch Erfassung (Tutorial 3).

Die Übergabearchive können nur mit dem Recht „Übergaben ansehen“ (CAMO, Qualität) heruntergeladen werden, nie über den generischen Link für Anhänge.
