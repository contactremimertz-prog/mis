# 12. Eine Task Card durchführen

**Konto: `meca`**

Ausgangslage: Bei F-HDMD (H145) ist die Task Card **Visite 100 h / 12 mois** in Bearbeitung. 3 von 6 Schritten sind signiert, ein Drehmomentschlüssel ist ausgegeben, eine Anforderung für einen Magnetstopfen wartet auf das Lager.

## 1. Die Task Card öffnen

Menü **Task Cards** → Filter Status „Laufend“ → **Visite 100 h / 12 mois** (WP „Visite 100 h + boroscopie moteurs“).

## 2. Die verbleibenden Schritte signieren

Für die Schritte 4, 5 und 6:

1. Geben Sie bei Bedarf einen gemessenen Wert ein (z. B. `Niveau OK`); haken Sie N/A an, wenn der Schritt nicht zutrifft.
2. Geben Sie Ihr Passwort ein → **Signieren**.

Jeder signierte Schritt zeigt Ihren Namen, Ihr Kürzel (`LM1`) und den Zeitstempel.

**Probieren Sie** ein falsches Passwort: „Falsches Passwort oder falscher Signaturcode: Signatur abgelehnt.“

## 3. Versuchen, die Arbeiten zu signieren

Arbeitsbericht `Visite effectuée, RAS`, aufgewendete Zeit `7.5`, Passwort → **Arbeiten signieren**.

AHMIS **lehnt ab**: „Es stehen noch Teileanforderungen aus“. Das ist gewollt: Eine Aufgabe wird nicht mit einem ausstehenden Teil abgeschlossen.

## 4. Die Sperre aufheben

1. **Teil**: Der Lagerist gibt die Anforderung aus (Tutorial 18). Wenn Sie es nicht benötigen, bitten Sie das Lager um Stornierung.
2. **Werkzeug**: Klicken Sie im Feld Werkzeug auf **Zurückgeben** bei `CLE-DYN-01`. Solange ein Werkzeug ausgegeben ist, ist die Signatur ebenfalls gesperrt.

## 5. Die Arbeiten signieren

Wiederholen Sie Schritt 3. Die Task Card wechselt auf **Abgeschlossen**, da diese Aufgabe keine unabhängige Prüfung erfordert.

## Was AHMIS beim Abschluss tut

- Es erfasst die **Durchführung** der Aufgabe mit den aktuellen Zählern des Luftfahrzeugs.
- Es **berechnet** die Fälligkeit **neu**: Der 100-h-Check von F-HDMD steht wieder auf „OK“, mit 100 FH vor sich (prüfen Sie unter **Fälligkeiten**).
- Folgt die Aufgabe einer AD, aktualisiert es den Status der Anweisung (Tutorial 8).
- Behebt die Task Card einen Mangel, schließt es den Mangel (Tutorial 15).

## Automatische Prüfungen bei der Signatur

| Regel | Meldung |
|---|---|
| Personalakte mit dem Konto verknüpft | „Ihr Konto ist keiner Personalakte zugeordnet“ |
| Gültige Berechtigung für das Muster | „… hat keine gültige Berechtigung für das Muster H145“ |
| Alle Schritte signiert | „3 Schritt(e) nicht signiert“ |
| Arbeitsbericht ausgefüllt | „Der Arbeitsbericht ist Pflicht“ |
| Keine ausstehende Teileanforderung | „Es stehen noch Teileanforderungen aus“ |
| Werkzeug zurückgegeben | „Werkzeug nicht zurückgegeben: CLE-DYN-01“ |

## Feststellung während des Checks

Das Feld **Feststellung melden** erzeugt mit einem Klick einen **Mangel** und eine **Task Card zur Behebung** im selben WP, verknüpft mit der ursprünglichen Task Card. Probieren Sie: `Légère corrosion sur ferrure de capot BTP`.

## Zurückstellen oder stornieren

- **Zurückstellen** (Grund erforderlich): Die Task Card wird zurückgestellt, und die Rückstellung erscheint im CRS.
- **Abbrechen**: nur, wenn kein Schritt signiert ist.
