# 16. Freigabebescheinigung (CRS)

**Konten: `b1`, `b2`, `planif`**

Das CRS wird auf Ebene des **Arbeitspakets** signiert, wenn alle Arbeiten abgeschlossen sind.

## 1. Sehen, was blockiert

Öffnen Sie das WP von F-HDMD („Visite 100 h + boroscopie moteurs“) → Feld **Freigabebescheinigung**. AHMIS listet alles auf, was das CRS verhindert, zum Beispiel:

- nicht abgeschlossene Task Card (und ihr Status);
- nicht zurückgegebenes Werkzeug;
- reserviertes Teil, das weder eingebaut noch an das Lager zurückgegeben wurde.

Die Schaltfläche **CRS signieren** bleibt ausgegraut, solange die Liste nicht leer ist.

## 2. Die Arbeiten beenden

Wenn Sie die Tutorials 12 bis 14 durchlaufen haben, bleibt höchstens:

- **Contrôle capacité batterie** (Qualifikation B2): Konto `b2` → starten, die 3 Schritte signieren, die Arbeiten signieren;
- jede Task Card, die Sie als Übung angelegt haben: Schließen Sie sie ab oder **stellen Sie sie zurück** mit einem Grund (eine Rückstellung verhindert das CRS nicht, sie wird darin erwähnt).

## 3. Das CRS signieren

Konto `b1` → WP → Passwort → **CRS signieren**.

**Ergebnis**:

- Das WP wechselt auf **Freigegeben (CRS signiert)** und ist **nicht mehr änderbar**;
- F-HDMD wechselt wieder auf **In Betrieb**;
- die CRS-Erklärung wird gespeichert mit Name, Lizenz, Datum, Genehmigung des Betriebs, Zählern des Luftfahrzeugs, zurückgestellten Arbeiten und laufenden zurückgestellten Mängeln;
- **Akte drucken** zeigt das CRS mit der Referenz seines SHA-256-Hashwerts.

## Angewandte Regeln

| Regel | Detail |
|---|---|
| Gültige Freigabeberechtigung für das Muster | B1, B2, B3 oder C, nicht ausgesetzt, innerhalb ihrer Gültigkeitsdaten |
| Gültige Part-66-Lizenz | Gültigkeitsdatum nicht überschritten |
| Großer Check („Großer Check“ als WP-Art) | CRS der **Kategorie C** vorbehalten (probieren Sie es mit `b1`, dann `certc`) |
| Mechaniker ohne Freigabeberechtigung | Zugriff verweigert (403) |
