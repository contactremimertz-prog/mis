# 25. Toleranzen: Durchführung in der Toleranz, nicht kumulativ

**Konto: `camo`**

Eine Toleranz erlaubt es, eine Aufgabe etwas nach ihrer Fälligkeit durchzuführen (zum Beispiel +10 FH oder +30 Tage bei einem 100-h-Check). Sie ist **nicht kumulativ**: Wird eine Aufgabe in der Toleranz durchgeführt, zählt die nächste Fälligkeit ab der **theoretischen Grenze**, nicht ab dem tatsächlichen Datum oder den tatsächlichen Stunden. Man „gewinnt“ also durch die Nutzung der Toleranz nie Stunden.

## 1. Ausgangslage

Menü **Fälligkeiten** → Luftfahrzeug **F-HDMB**: Die Aufgabe `N90-05-100 Visite 100 h / 12 mois` ist **In der Toleranz**. Theoretische Grenze `3.881,6 FH`, aktueller Zähler `3.887,6 FH`, also 6 FH Überschreitung bei einer Toleranz von 10 FH.

## 2. Die Durchführung erfassen

1. Klicken Sie auf `N90-05-100` → **Durchführung erfassen (Historie)**.
2. Luftfahrzeug `F-HDMB`, heutiges Datum, FH `3887.6`, Zyklen `11623`, Herkunft „Externe Organisation“, Referenz `CRS-EXT-001`, bescheinigt durch `Atelier externe` → **Speichern**.

**Ergebnis**:

- In der Aufgabenakte trägt die Durchführung das Badge **in der Toleranz**;
- in den Fälligkeiten lautet die nächste Grenze **3.981,6 FH** (3.881,6 + 100) und nicht 3.987,6. Der Hinweis „In der Toleranz durchgeführt: nächste Fälligkeit ab der theoretischen Grenze gezählt“ erinnert daran;
- beim Datum war die Durchführung nicht verspätet: Die nächste kalendarische Fälligkeit zählt ab dem tatsächlichen Datum (+12 Monate).

Jedes Kriterium (FH, Zyklen, Datum) wird getrennt behandelt: Als Basis dient der kleinere Wert aus tatsächlicher Durchführung und Grenze.

## 3. Durchführung außerhalb der Toleranz

Überschreitet die Durchführung die Toleranz, wird sie als **außerhalb der Toleranz** gekennzeichnet. Die nächste Fälligkeit beginnt dann ab der tatsächlichen Durchführung, und die Überschreitung bleibt für die Analyse der CAMO in der Historie sichtbar.

## 4. Eingaberegeln

- Die Durchführungen derselben Aufgabe müssen in chronologischer Reihenfolge erfasst werden.
- Eine Toleranz ist bei einer ALS- oder CMR-Aufgabe (Lufttüchtigkeitsbegrenzungen) **verboten**.
- Eine Toleranz bei einer AD-Aufgabe erfordert eine **Referenz** (Absatz der AD, der sie erlaubt).
