# 21. Personal, Lizenzen und Berechtigungen

**Konto: `qualite`**

AHMIS unterscheidet zwei Dinge:

- das **Benutzerkonto** mit seiner Rolle, das bestimmt, welche Bildschirme zugänglich sind;
- die **Personalakte** mit ihrer Part-66-Lizenz und ihren Berechtigungen, die bestimmt, was die Person **signieren** darf.

## 1. Eine Akte einsehen

Menü **Personal & Berechtigungen** → **Claire DUBOIS**:

- Lizenz `FR.66.DEMO.0002`, Kategorien B1.3 / B1.1, Gültigkeitsdatum;
- **Berechtigungen** der Part-145-Organisation: Nr., Art, Kategorie, freigabeberechtigt oder nicht, Umfang, Gültigkeit, Zustand;
- **Schulungen** mit begrenzter Gültigkeit: Human Factors, EWIS …;
- ihre zuletzt signierten Arbeiten und Prüfungen.

**Zu prüfen**: Ihre **Super Puma**-Berechtigung läuft in 45 Tagen ab. Sie wird in der Kennzahl „autorisation(s) expirant sous 60 j“ der Übersicht mitgezählt.

## 2. Eine Berechtigung aussetzen

1. Fügen Sie Claire DUBOIS eine Berechtigung hinzu (Formular am Seitenende): Nr. `AUT-TEST`, Art `ATR72-600`, Kategorie B2, freigabeberechtigt, Daten von heute bis +1 Jahr, haken Sie **ausgesetzt** an → **Hinzufügen**. Sie erscheint als „Ausgesetzt“.
2. Für eine echte Aussetzung ändern Sie die bestehende Berechtigung in der Administration (Konto `admin` → Administration → Berechtigungen) und haken „ausgesetzt“ an. Die Person kann dann sofort nicht mehr für dieses Muster signieren.

## 3. Was jede Signatur prüft

| Handlung | Anforderung |
|---|---|
| Starten, einen Schritt signieren, die Arbeiten signieren | Gültige Berechtigung (beliebige Kategorie) für das Muster + Pflichtschulungen des gesamten Personals aktuell |
| Unabhängige Prüfung | Gültige **Freigabeberechtigung** + gültige Lizenz + andere Person als der Ausführende + Schulungen des freigabeberechtigten Personals + aktuelle Erfahrung |
| Rückstellung eines Mangels | Gültige Freigabeberechtigung + Schulungen + aktuelle Erfahrung |
| CRS | Freigabeberechtigung B1/B2/B3/C (nur C für einen großen Check) + gültige Lizenz + Schulungen + aktuelle Erfahrung |

Alle Gründe, die eine Signatur verhindern, werden auf einmal aufgelistet, auf der Task Card und in der Personalakte (Tutorial 28).

## 4. Eine Person anlegen

1. Konto `admin` → **Administration** → Benutzer → legen Sie das Konto an und fügen Sie es der gewünschten Gruppe hinzu („Mechaniker“, „Freigabeberechtigter“ …).
2. Konto `qualite` → **Personal** → **+ Anlegen**: verknüpfen Sie das Konto, geben Sie Personalnummer, Name, Kürzel und Lizenz ein.
3. Fügen Sie ihre Berechtigungen und Schulungen hinzu.

> Nur Schulungen der **Pflichtkategorien** sperren die Signatur (standardmäßig: Human Factors für alle, plus Fortbildung für das freigabeberechtigte Personal). Eine andere abgelaufene Schulung, wie „Sicherheit / Sicherheitsbereiche“ von Lucas MARTIN, wird rot gekennzeichnet, ohne zu sperren. Tutorial 28 beschreibt die aktuelle Erfahrung und die Pflichtschulungen im Detail.
