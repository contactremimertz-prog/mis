# 26. Register der Änderungen und Reparaturen

**Konten: `camo`, `b1`**

M.A.305 verlangt, jederzeit den Stand der Änderungen und Reparaturen jedes Luftfahrzeugs zu kennen, mit ihrer Genehmigungsgrundlage und den daraus folgenden Anweisungen zur Aufrechterhaltung der Lufttüchtigkeit (ICA).

## 1. Eine Änderung erfassen

1. Konto `camo` → Menü **Änderungen & Reparaturen** → **+ Anlegen**.
2. Luftfahrzeug `F-HDMA`, Art „Änderung“, Klassifizierung „Klein“, Bezeichnung `Installation d'un kit caméra externe`, ATA `25`.
3. Genehmigungsgrundlage „DOA- / Part-21J-Genehmigung“, Referenz `DOA-MIN-2026-118 (DEMO)`.
4. Status „Durchgeführt“, durchgeführt am: heutiges Datum, ICA: `Supplément MSM 25-10 (DEMO)`. Haken Sie „ändert Masse und Schwerpunkt“ an → **Speichern**.

**Ergebnis**: Die Änderung erhält eine Nummer `MOD-JJJJ-NNNN`. Ihre Akte meldet zwei **offene Punkte**: „ICA noch nicht in das Instandhaltungsprogramm übernommen“ und „Wäge- und Schwerpunktbericht zu aktualisieren“. Sie erscheinen auch in den **Fälligkeiten** von F-HDMA, Art „Änderung / Reparatur“.

## 2. Die Nachverfolgung abschließen

1. **Bearbeiten** Sie die Änderung: Haken Sie „ICA in das Instandhaltungsprogramm übernommen“ und „Folgemaßnahmen durchgeführt“ an.
2. **Speichern**: Die offenen Punkte verschwinden aus den Fälligkeiten.

Um die ICA zu übernehmen, legen Sie die entsprechende Aufgabe im Programm an (Tutorial 6) und halten Sie dann die neue Revision in der Programmüberprüfung fest (Tutorial 27).

## 3. Aus einer Task Card

Konto `b1` → eine Task Card → Link **+ Eine an dieser Task Card durchgeführte Änderung oder Reparatur erfassen**. Das Formular ist vorausgefüllt (Luftfahrzeug, Komponente, Bezeichnung, ATA, Datum), und die Task Card wird verknüpft.

## 4. Prüfungen

| Regel | Meldung |
|---|---|
| Größere Änderung: EASA-Genehmigung, STC oder DOA | „Eine größere Änderung oder Reparatur erfordert eine EASA-Genehmigung, ein STC oder eine DOA-Genehmigung.“ |
| Standardänderung: CS-STAN | „Eine Standardänderung muss sich auf CS-STAN beziehen.“ |
| Durchgeführt: Datum Pflicht | „Durchführungsdatum ist Pflicht.“ |
| Durchgeführt: ICA oder „keine zugehörigen ICA“ | „ICA angeben oder „keine zugehörigen ICA“ ankreuzen.“ |
| Ausgebaut / storniert: Grund | „Grund ist Pflicht.“ |

Eine Änderung wird nicht gelöscht: Setzen Sie sie mit einem Grund auf den Status „Ausgebaut / storniert“.
