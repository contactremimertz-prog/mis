# 15. Mängel und Rückstellungen (MEL / CDL)

**Konten: `meca`, `b2`, `planif`**

## 1. Einen Mangel melden

1. Konto `meca` → öffnen Sie **F-HDMA** → **Mangel melden**.
2. Quelle „Besatzungsmeldung (Techlog)“, Techlog-Ref. `CRM MA-150`, ATA `33`, Beschreibung `Feu anticollision inférieur inopérant`.
3. **Speichern**: Der Mangel erhält eine Nummer `DEF-JJJJ-NNNN` mit dem Status **Offen**.

## 2. Gemäß MEL zurückstellen

Die Rückstellung erfordert eine **Freigabeberechtigung** für das Muster.

1. Konto `b2` → Menü **Mängel & Rückstellungen** → öffnen Sie den Mangel.
2. Feld **Gemäß MEL / CDL zurückstellen**:
    - MEL-Referenz `MEL 33-40-01 (DEMO)`
    - Kategorie `C (10 jours)`; lassen Sie die Grenze für die Standardfrist leer
    - Verfahren `Placard INOP apposé, vol de jour uniquement`
    - Passwort → **Rückstellung signieren**

**Ergebnis**:

- Der Mangel ist **Zurückgestellt**, Grenze = heute + 10 Tage;
- er erscheint in den **Fälligkeiten** von F-HDMA (Art „Zurückgestellter Mangel“) und in der Planung;
- ist er bei einem CRS noch zurückgestellt, wird er **in der CRS-Erklärung genannt**.

Standardfristen: B = 3 Tage, C = 10 Tage, D = 120 Tage. Für Kategorie A oder außerhalb der MEL geben Sie die Grenze ein (Datum, Stunden oder Zyklen).

**Prüfungen**: Ohne MEL-Referenz oder ohne jegliche Grenze wird die Rückstellung abgelehnt. Das Rückstellungsformular wird einem Mechaniker ohne Freigabeberechtigung nicht angeboten.

Eine **einmalige Verlängerung** der Frist (RIE) kann anschließend von der CAMO vor Fristablauf genehmigt werden: siehe Tutorial 31.

## 3. Beheben

1. Konto `planif` → öffnen Sie den Mangel → **Task Card zur Behebung anlegen** in einem bestehenden WP oder „+ Neues WP zur Fehlerbehebung“.
2. Führen Sie die Task Card durch (Tutorial 12). Bei ihrem Abschluss wechselt der Mangel auf **Behoben**.

## Bereits geladenes Beispiel

F-HDMC (H135) hat einen **zurückgestellten** Mangel der Kategorie C (Kabinenbeleuchtung): Sehen Sie ihn in seinen Fälligkeiten und in seiner Akte.
