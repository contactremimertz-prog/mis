# 22. Audit-Trail und elektronische Signaturen

**Konto: `qualite`**

## Audit-Trail

Menü **Audit-Trail**: Jede Anlage, Änderung oder technische Löschung wird protokolliert mit:

- Zeitstempel und Benutzer;
- dem betroffenen Datensatz;
- **jedem geänderten Feld**, mit altem und neuem Wert.

Das Protokoll ist **nur schreibend**: Kein Eintrag kann geändert oder gelöscht werden, auch nicht vom Administrator.

**Übungen**

1. Suche `F-HDMA`: alle Vorgänge an diesem Luftfahrzeug, einschließlich der Zählererhöhungen.
2. Filter „Datensatzart = Instandhaltungsaufgabe“: die Revisionshistorie des Programms.
3. In einer Akte (Luftfahrzeug, Komponente, Task Card, WP, Mangel) zeigt die Schaltfläche **Historie** die Änderungen **und** die Signaturen dieses Datensatzes.

## Elektronische Signaturen

Menü **Elektronische Signaturen**: alle Signaturen, filterbar nach Handlung (Durchführung, Prüfung, CRS, Rückstellung …).

Jede Signatur enthält den Namen, die Lizenz zum Zeitpunkt der Signatur, die signierte Erklärung, den Zeitstempel und einen über das Ganze berechneten **SHA-256-Hashwert**.

Das Badge **„✓ intakt“** bedeutet, dass der neu berechnete Hashwert übereinstimmt. Würde eine Angabe direkt in der Datenbank außerhalb von AHMIS geändert, würde das Badge zu **„⚠ verändert“**. Der automatische Test `test_signature_is_immutable_and_tamper_evident` demonstriert das.

## Was aufbewahrt wird

- Keine Lufttüchtigkeitsaufzeichnung kann gelöscht werden: Luftfahrzeuge, Komponenten, Aufgaben, Durchführungen, Task Cards, WP, Mängel, Zertifikate, Stundenerfassungen …
- Stattdessen werden Status verwendet: storniert, ausgemustert, verschrottet, inaktiv.
- Die regulatorischen Aufbewahrungsfristen sind Sache Ihrer Verfahren (CAME / MOE) und der Sicherung der Datenbank (Tutorial 23).
