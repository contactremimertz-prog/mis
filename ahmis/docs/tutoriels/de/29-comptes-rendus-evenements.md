# 29. Ereignismeldungen (Verordnung 376/2014)

**Konten: `meca`, `qualite`, `camo`**

Jedes Ereignis, das die Sicherheit gefährdet oder gefährden könnte, muss der Behörde **innerhalb von 72 Stunden** gemeldet werden, nachdem die Organisation davon Kenntnis erlangt hat (Verordnung (EU) 376/2014, 145.A.60, CAMO.A.160). Eine Folgeanalyse wird **innerhalb von 30 Tagen** übermittelt. Der Inhaber der Musterzulassung wird informiert, wenn der Zustand des Luftfahrzeugs oder einer Komponente betroffen ist.

AHMIS wendet die **Just Culture** an: Das gesamte Personal kann melden, aber nur Qualität und CAMO sehen alle Meldungen. Die Identität eines vertraulichen Meldenden ist nur für den Qualitätsverantwortlichen sichtbar.

## 1. Melden (gesamtes Personal)

1. Konto `meca` → Menü **Ereignismeldungen** → **+ Anlegen**. Anderer Zugang: Schaltfläche **Ereignis melden** an einem Mangel oder einer Task Card, die das Formular vorausfüllt.
2. Bezeichnung `Lampe torche retrouvée en zone moteur`, Kategorie „Fremdkörper (FOD) / vergessener Gegenstand“, Phase „In Instandhaltung“, Luftfahrzeug `F-HDMD`.
3. Daten des Ereignisses und der Kenntnisnahme: jetzt. Sachliche Beschreibung, Sofortmaßnahmen `Zone inspectée, inventaire outillage`. Haken Sie **vertrauliche Meldung** an → **Speichern**.

**Ergebnis**: Die Meldung `OCC-JJJJ-NNNN` ist im Status **Entwurf**, mit angezeigter 72-h-Frist. Der Mechaniker sieht nur seine eigenen Meldungen.

## 2. Fristen verfolgen (Qualität)

Konto `qualite` → **Übersicht**: Banner „Ereignismeldungen: N offen, davon N zu melden“. Er wird rot, wenn eine Frist überschritten ist. Die Demo enthält:

| Nr. | Situation |
|---|---|
| Vibrationen Pedale (F-HDMD) | Entwurf: noch etwa 20 h von 72 |
| Nicht montierte Mutternsicherung (F-HDMB) | Vor 40 Tagen gemeldet: **Folgemeldung nach 30 Tagen überfällig** |
| Teil ohne Freigabezertifikat | Abgeschlossen |

Bei der vertraulichen Meldung ist der Meldende (Sophie LAMBERT) für `qualite` sichtbar, für `camo` aber als „Vertraulich“ angezeigt.

## 3. Melden, nachverfolgen, abschließen

Konto `qualite` → öffnen Sie die Meldung → **Bearbeiten**:

1. **Meldung**: Status „Der Behörde gemeldet“, Behörde `DSAC / ECCAIRS 2`, ECCAIRS-Referenz, Meldedatum. Nach mehr als 72 h ist der **Grund der Verspätung** Pflicht. Haken Sie „Inhaber der Musterzulassung informiert“ an, falls erforderlich.
2. **Folgemaßnahmen**: Status „Folgemeldung übermittelt“, Analyse (Ursachen, Human Factors), Übermittlungsdatum.
3. **Abschluss**: Korrekturmaßnahmen und Abschlussdatum.

Ein Ereignis außerhalb der Liste der Verordnung 2015/1018 kann mit einer Begründung „Als nicht meldepflichtig eingestuft“ werden. Ein schwerer Vorfall oder ein Unfall kann es nicht.

## 4. Aufbewahrung

Abgeschlossene Meldungen werden mindestens 36 Monate aufbewahrt (Tutorial 30). Sie sind nicht in den Übergabeakten eines Luftfahrzeugs enthalten.
