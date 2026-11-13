# 2. Einstieg: Rollen, Navigation, elektronische Signatur

**Konto: `admin`, dann `meca`**

## Die Übersicht

1. Melden Sie sich mit `admin` an.
2. Die Übersicht zeigt 8 Kennzahlen. Jede ist anklickbar und öffnet die entsprechend gefilterte Liste:
    - überfällige Fälligkeiten (davon in der Toleranz) und zu planende;
    - offene Mängel und überschrittene Rückstellungen;
    - zu bewertende AD/SB;
    - aktive Arbeitspakete und Task Cards, die auf Prüfung warten;
    - Teileanforderungen, Quarantäne, Werkzeug ohne gültige Kalibrierung und ablaufende Berechtigungen.
3. Die Tabelle **Flotte** zeigt für jedes Luftfahrzeug seine Zähler, die Gültigkeit des ARC und die Anzahl der Fälligkeiten.

**Zu prüfen**: Die Zeile F-HDMB zeigt überfällige Fälligkeiten; F-HDMD ist „In Instandhaltung“.

## Navigation

- Das Menü links ist nach Aufgabenbereichen gegliedert: CAMO, Part-145, Logistik, Qualität, Hilfe.
- Die **globale Suche** (oben) findet ein Kennzeichen, eine P/N, eine S/N, ein WP, eine Task Card, eine AD. Probieren Sie `DEMO-S3502`: Sie gelangen direkt zur Akte der Rotornabe von F-HDMB.
- Jede Liste hat eine Suche und Filter.

## Die Rollen

1. Melden Sie sich ab und mit `meca` wieder an.
2. Öffnen Sie **Flotte**, dann F-HDMA: Die Akte kann eingesehen werden, aber die Schaltflächen „Bearbeiten“ und „Konfigurationsübernahme“ erscheinen nicht mehr.
3. Geben Sie in der Adressleiste `/flotte/aeronefs/1/modifier/` ein: AHMIS antwortet „403 Verboten“.

Die Rollen beschränken den Zugriff auf Bildschirme. Tutorial 21 zeigt die zweite Schranke: die individuellen Signaturberechtigungen.

## Die elektronische Signatur

Jede regulatorische Handlung (Task-Card-Schritt, Durchführung, Prüfung, Rückstellung eines Mangels, CRS) erfordert die **erneute Eingabe des eigenen Passworts**. AHMIS speichert dann:

- die Identität und die Lizenz des Signierenden;
- den Zeitstempel;
- die signierte Erklärung;
- einen **SHA-256-Hashwert**, mit dem jede spätere Veränderung erkannt werden kann (Badge „✓ intakt“).

Eine Signatur kann weder geändert noch gelöscht werden. Bei falschem Passwort wird die Signatur abgelehnt.

## Nichts wird gelöscht

Lufttüchtigkeitsaufzeichnungen können nicht gelöscht werden, auch nicht vom Administrator. Stattdessen werden Status verwendet („storniert“, „ausgemustert“, „verschrottet“). Jede Änderung wird feldweise im **Audit-Trail** protokolliert (Tutorial 22).
