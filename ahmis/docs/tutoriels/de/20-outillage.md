# 20. Werkzeug und Kalibrierung

**Konten: `magasin`, `meca`**

## Der Werkzeugpark

Menü **Werkzeug**: Referenz, Status, letzte Kalibrierung, Fälligkeit und Anzeige „Kalibrierung OK“.

In der Demo hat der Drehmomentschlüssel **CLE-DYN-02** eine **abgelaufene** Kalibrierung (Kennzahl „Outillage hors étalonnage“ der Übersicht).

## 1. Ein nicht kalibriertes Werkzeug darf nicht ausgegeben werden

1. Konto `meca` → eine **laufende** Task Card, zum Beispiel **Visite 100 h / 12 mois** von F-HDMD (wenn Sie sie in Tutorial 12 bereits abgeschlossen haben, starten Sie eine andere, etwa „Contrôle capacité batterie“).
2. Feld **Werkzeug** → wählen Sie `CLE-DYN-02` → **Werkzeug ausgeben**.
3. Ablehnung: „Kalibrierung abgelaufen oder nicht eingetragen, Ausgabe nicht zulässig“.

## 2. Eine Kalibrierung erfassen

1. Konto `magasin` → **Werkzeug** → `CLE-DYN-02`.
2. „Kalibrierung erfassen“: heutiges Datum, Labor `Laboratoire de métrologie démo`, Zertifikat `MET-2026-118`, Ergebnis „Bestanden“ → **Speichern**.

Die Fälligkeit wird neu berechnet (letzte Kalibrierung + 365 Tage).

## 3. Ausgeben, dann zurückgeben

1. Konto `meca` → dieselbe Task Card → geben Sie `CLE-DYN-02` aus.
2. Es wechselt auf „Ausgegeben“, gebunden an die Task Card und an Ihren Namen, mit gespeichertem **Gültigkeitsdatum der Kalibrierung**.
3. **Zurückgeben**, sobald die Arbeit beendet ist. Zur Erinnerung: Die Task Card kann nicht signiert werden, solange ein Werkzeug ausgegeben bleibt.

## Rückverfolgbarkeit bei nicht konformem Werkzeug

Fällt eine Kalibrierung **nicht bestanden** aus, wird das Werkzeug außer Betrieb gesetzt. Die Werkzeugakte listet alle **Verwendungen** (Task Card, Person, Daten) auf, womit die Arbeiten identifiziert werden, die seit der letzten gültigen Kalibrierung neu zu bewerten sind.
