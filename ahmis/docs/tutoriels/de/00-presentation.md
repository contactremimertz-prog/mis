# 0. Einführung in AHMIS

AHMIS (**A**ircraft & **H**elicopter **M**aintenance **I**nformation **S**ystem) deckt drei Aufgabenbereiche auf einer gemeinsamen Datenbank ab:

| Modul | Für wen | Hauptfunktionen |
|---|---|---|
| **Lufttüchtigkeit (CAMO)** | CAMO-Ingenieur | Flotte, Konfiguration, Flugstunden, Instandhaltungsprogramm und dessen jährliche Überprüfung, AD/SB, Änderungen und Reparaturen, LLP/TBO, Fälligkeiten, Prognose, ARC, Verlängerung von Rückstellungen, Aktenübergabe |
| **Instandhaltung (Part-145)** | Planer, Mechaniker, freigabeberechtigtes Personal | Planung, Arbeitspakete, Task Cards, Signaturen, unabhängige Prüfung, Mängel/MEL, Komponentenwechsel, CRS, aktuelle Erfahrung und sperrende Schulungen, Ereignismeldungen |
| **Logistik** | Lagerist | Wareneingang mit Form 1 je nach Artikelklasse, Lager, Ablaufdatum, Quarantäne, Verschrottung und Unbrauchbarmachung, Teileanforderungen, Werkzeug und Kalibrierung |
| **Qualität** | Qualitätsverantwortlicher | Audit-Trail, elektronische Signaturen, Personal und Berechtigungen, Ereignismeldungen, Aufbewahrung der Aufzeichnungen |

## Die Demodaten

Die Demo lädt eine gemischte Flotte aus 6 betriebenen Luftfahrzeugen, überwiegend von **Airbus Helicopters**, sowie einen aus dem Dienst genommenen Hubschrauber:

| Kennzeichen | Muster | Ausgangslage (für die Tutorials) |
|---|---|---|
| F-HDMA | NH90 | 100-h-Check und AD zu planen, Hauptgetriebe nahe an der TBO |
| F-HDMB | NH90 | **AD überfällig**, 100-h-Check in der Toleranz, Rotornabe (LLP) nahe an der Grenze, leeres geplantes WP |
| F-HDMC | H135 (HEMS) | Zurückgestellter Mangel MEL-Kat. C, offenes ASB, Rotornabe (LLP) in Zyklen überwacht |
| F-HDMD | H145 (HEMS) | **In Instandhaltung**: laufendes Arbeitspaket mit Task Cards in allen Bearbeitungsständen |
| F-HDME | Super Puma | ARC läuft in 20 Tagen ab |
| F-HDMF | ATR 72-600 | AD zu bewerten, kalendarische Aufgabe überfällig |
| F-HDMZ | NH90 | Vor 20 Monaten **aus dem Dienst genommen**, Akte an den Erwerber übergeben (Tutorial 30) |

Sie enthält außerdem: Programmüberprüfungen in allen Zuständen (Tutorial 27), drei Ereignismeldungen (Tutorial 29), ein verschrottetes Teil (Tutorial 31) und einen ehemaligen Mitarbeiter, dessen Akte das Ende der Aufbewahrungsfrist erreicht hat (Tutorial 30).

> ⚠️ **Alle Referenzen (Aufgaben, P/N, AD, Intervalle, Grenzen) sind fiktiv** und mit „DEMO“ präfixiert. Sie dienen ausschließlich der Veranschaulichung der Software. Im Betrieb stammen die Daten aus den Herstellerdokumenten (MSM, MRI, ALS …) und von den Behörden.

## Demokonten

Gemeinsames Passwort: **`Ahmis2026!`**

| Benutzername | Person | Rolle | Darf signieren |
|---|---|---|---|
| `admin` | — | Administrator (alle Rechte) | Nein (keine Personalakte) |
| `camo` | Julien MOREAU | CAMO-Ingenieur | — |
| `planif` | Nadia ROUX | Planer | — |
| `meca` | Lucas MARTIN | Mechaniker ohne Freigabeberechtigung | Durchführung (Hubschrauber) |
| `b1` | Claire DUBOIS | Freigabeberechtigte B1 | Durchführung, Prüfung, CRS, Rückstellung von Mängeln |
| `b2` | Karim BENALI | Freigabeberechtigter B2 | Wie oben (Hubschrauber) |
| `certc` | Sophie LAMBERT | Freigabeberechtigte C | Wie oben + CRS für großen Check |
| `magasin` | Thomas PETIT | Lagerist | — |
| `qualite` | Isabelle GARNIER | Qualitätsverantwortliche | — |

Die Rechte für den **Zugriff auf Bildschirme** hängen von der Rolle ab. Die **Signaturrechte** hängen zusätzlich von den individuellen Berechtigungen der Person ab (Luftfahrzeugmuster, Kategorie, Gültigkeit): AHMIS prüft sie bei jeder Signatur.

## Empfohlene Reihenfolge der Tutorials

1. Installation (Tutorial 1), dann Einstieg (2).
2. CAMO-Seite: 3 bis 10.
3. Werkstattseite: 11 bis 16.
4. Lagerseite: 17 bis 20.
5. Qualität und Technik: 21 bis 23.
6. **Tutorial 24** verbindet alles in einem vollständigen Szenario, von der Fälligkeit bis zum CRS.
7. Regulatorische Verwaltungsregeln: **25 bis 31** (Toleranzen, Änderungen, Programmüberprüfung, aktuelle Erfahrung, Ereignismeldungen, Aufbewahrung und Übergabe, Verlängerung von Rückstellungen, Verschrottung, Artikelklassen).
8. Die **Konformitätsmatrix** (32) ordnet jede EASA-Anforderung den Funktionen von AHMIS zu.

Tipp: Um jederzeit bei null neu zu beginnen, starten Sie `reinitialiser_demo` (siehe Tutorial 1).
