# 13. Die unabhängige Prüfung (kritische Aufgaben)

**Konten: `b1`, dann `b2`**

Bestimmte Aufgaben (Flugsteuerung, kritische Befestigungen, Boroskopie-Inspektionen …) erfordern eine **zweite Signatur** durch eine **andere** Person als die ausführende, die eine **Freigabeberechtigung** für das Muster besitzt.

Ausgangslage: Bei F-HDMD wurde die Task Card **Contrôle boroscopique moteurs Arriel 2E** von Claire DUBOIS (`b1`) durchgeführt. Sie hat den Status „Durchgeführt – wartet auf Prüfung“.

## 1. Der Ausführende kann sich nicht selbst prüfen

1. Melden Sie sich mit `b1` an und öffnen Sie die Task Card (Menü **Task Cards**, Filter „Durchgeführt – wartet auf Prüfung“).
2. Das Feld Durchführung zeigt: „Sie haben diese Arbeiten durchgeführt: Die Prüfung muss eine andere Person signieren.“ Es wird keine Prüfschaltfläche angeboten.

## 2. Ein Mechaniker ohne Freigabeberechtigung kann nicht prüfen

Mit `meca` erscheint das Prüfformular nicht: Seine Berechtigung als „Mechaniker ohne Freigabeberechtigung“ erlaubt keine Prüfung.

## 3. Prüfung durch eine andere freigabeberechtigte Person

1. Melden Sie sich mit `b2` an (Karim BENALI, B2 freigabeberechtigt H145).
2. Öffnen Sie die Task Card → Feld **Unabhängige Prüfung**: Bemerkungen `Images boroscopiques revues, conforme`, Passwort → **Prüfung signieren**.

**Ergebnis**:

- Die Task Card ist **Abgeschlossen**;
- beide Signaturen (Durchführung und Prüfung) erscheinen mit ihrem Badge „✓ intakt“;
- die Fälligkeit der Komponentenaufgabe `145-72-500` des Triebwerks MOT 1 wird auf Basis der Zähler **des Triebwerks** neu berechnet.

## Eine Aufgabe „kritisch“ machen

Haken Sie im Instandhaltungsprogramm „unabhängige Prüfung erforderlich“ bei der Aufgabe an (Tutorial 6). Für eine Task Card außerhalb des Programms haken Sie dasselbe Kästchen bei ihrer Anlage an.
