# 28. Aktuelle Erfahrung und Pflichtschulungen

**Konten: `qualite`, `b1`**

145.A.35 verlangt vom freigabeberechtigten Personal mindestens **6 Monate Instandhaltungserfahrung** in den **letzten 24 Monaten** sowie eine Fortbildung. Human Factors werden vom gesamten Personal verlangt. AHMIS sperrt die Signatur, wenn eine dieser Bedingungen fehlt.

## 1. Das Panel „Signaturfähigkeit“

Konto `qualite` → **Personal & Berechtigungen** → **Claire DUBOIS**. Das Panel zeigt:

- **Aktuelle Erfahrung**: Anzahl der Monate innerhalb der letzten 24, mit mindestens einer in AHMIS durchgeführten oder geprüften Task Card oder durch eine erklärte Erfahrung abgedeckt. Es sind mindestens 6 erforderlich;
- **Schulungen (gesamtes Personal)** und **Schulungen (freigabeberechtigt)**: aktuell, oder die Liste dessen, was fehlt;
- für jedes berechtigte Muster: „kann signieren“ oder die Gründe der Sperre.

## 2. Eine Erfahrung außerhalb von AHMIS erklären

Bei einer Person, die aus einer anderen Organisation kommt, ist die frühere Erfahrung nicht in AHMIS. Feld **Erklärte Erfahrungen**:

1. Vom `01/01/2026` bis `30/06/2026`, Organisation `Atelier précédent (DEMO)`, Arbeiten `Entretien en ligne NH90`, Nachweis `Attestation employeur`.
2. **Hinzufügen**: Die abgedeckten Monate zählen zur aktuellen Erfahrung.

Eine Erfahrung in der Zukunft oder mit einem Ende vor dem Beginn wird abgelehnt.

## 3. Pflichtschulungen

Jede Schulung hat eine **Kategorie**: Human Factors, Fortbildung (145.A.35), EWIS, Kraftstofftanksicherheit, Mustereinweisung, Sicherheit, sonstige. Standardmäßig:

| Personal | Geforderte Kategorien |
|---|---|
| Gesamtes Personal | Human Factors |
| Freigabeberechtigtes Personal | Human Factors, Fortbildung |

Nur diese Kategorien sperren. Andere abgelaufene Schulungen werden rot gekennzeichnet, ohne zu sperren.

## 4. Die Sperre prüfen

1. Konto `qualite` → Akte **Claire DUBOIS** → Schulung „Fortbildung (145.A.35)“: Beachten Sie ihr Ablaufdatum.
2. Legen Sie zum Testen eine Test-Personalakte mit einer freigabeberechtigten NH90-Berechtigung, aber **ohne** Fortbildung an.
3. Verknüpfen Sie sie mit einem Konto und öffnen Sie dann mit diesem Konto eine NH90-Task Card: Das Feld „Signatur unmöglich“ listet „Pflichtschulung fehlt oder ist abgelaufen: Fortbildung (145.A.35)“.

## 5. Parametrierung

In der Konfigurationsdatei:

| Variable | Standard | Funktion |
|---|---|---|
| `AHMIS_RECENCY_ENFORCE` | `1` | `0` deaktiviert die Prüfung der aktuellen Erfahrung |
| `AHMIS_RECENCY_MONTHS` | `6` | Geforderte Erfahrungsmonate |
| `AHMIS_RECENCY_WINDOW_MONTHS` | `24` | Gleitendes Fenster |
| `AHMIS_TRAINING_REQUIRED_ALL` | `human_factors` | Von allen geforderte Kategorien |
| `AHMIS_TRAINING_REQUIRED_CERTIFYING` | `human_factors,continuation` | Vom freigabeberechtigten Personal geforderte Kategorien |
