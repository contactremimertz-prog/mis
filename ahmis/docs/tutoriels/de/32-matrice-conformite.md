# 32. Regulatorische Konformitätsmatrix

Diese Matrix ordnet die wichtigsten Anforderungen der EASA den Funktionen von AHMIS zu. Sie dient als Grundlage für die Unterlagen zur Vorlage bei der Behörde.

> **Wichtig**: Eine Software ist nicht für sich allein „konform“. Es ist die Organisation (CAMO, Part-145), die der Behörde (in Frankreich der DSAC) ihre Konformität nachweist. Sie tut dies, indem sie das Werkzeug und seine Nutzung in ihren Verfahren (CAME, MOE) beschreibt, es validiert und auditiert. Die Spalte „Von der Organisation zu erledigen“ listet auf, was in Ihrer Verantwortung bleibt. Die nachstehenden regulatorischen Referenzen sind Richtwerte: Prüfen Sie sie in den geltenden Texten.

## Lufttüchtigkeit (Part-CAMO / Part-M)

| Anforderung | AHMIS-Funktion | Abdeckung | Von der Organisation zu erledigen |
|---|---|---|---|
| Genehmigtes Instandhaltungsprogramm | Programm je Muster, Intervalle FH/Zyklen/Kalender, Schwellen, Toleranzen, Effektivität, AMP-Revision, Revisionshistorie | ✅ | Das genehmigte Programm (MSM/MPD) erfassen, Kontrolle der Erfassung durch eine 2. Person |
| Nicht kumulative Toleranzen | Durchführung in der Toleranz: nächste Fälligkeit ab der theoretischen Grenze gezählt; außerhalb der Toleranz protokolliert; Toleranz bei ALS/CMR verboten, bei AD mit Referenz (Tutorial 25) | ✅ | Die im Programm zulässigen Toleranzen festlegen |
| Regelmäßige Programmüberprüfung (M.A.302(g)) | Überprüfung je Muster mindestens alle 12 Monate, Prüfung von Zuverlässigkeit und neuen Anweisungen, genehmigte Änderung, Warnung in der Übersicht, Historie (Tutorial 27) | ✅ | Verfahren für Überprüfung und indirekte Genehmigung in der CAME |
| Verfolgung der Lufttüchtigkeitsanweisungen | AD/SB-Register, Bewertung je Luftfahrzeug mit Begründung, Folgeaufgaben, Frist ab Inkrafttreten, Status bei Durchführung aktualisiert | ✅ | AD-Überwachung (EASA, FAA, Hersteller) und Erfassung |
| Lufttüchtigkeitsbegrenzungen, LLP | Lebensdauergrenzen FH/Zyklen/Tage, „Back-to-birth“-Rückverfolgbarkeit, LLP-Fälligkeiten, Einbauverweigerung an der Grenze | ✅ | Die vollständige LLP-Historie bei der Aufnahme in die Flotte übernehmen |
| Potenziale (TBO) | TBO-Fälligkeiten, Zähler TSO/CSO | ✅ | — |
| Lufttüchtigkeitsaufzeichnungen | Stunden/Zyklen protokolliert, Durchführungen, Konfiguration, Komponenten, CRS, keine Löschung möglich | ✅ | Sicherungen |
| Aufbewahrungsfristen (M.A.305(h), 145.A.55(c)) | Aufbewahrungsregeln je Art, Datum der Ausmusterung des Luftfahrzeugs, Bericht der abgelaufenen Aufzeichnungen, Massenlöschung gesperrt, solange die Frist nicht erreicht ist (Tutorial 30) | ✅ | Dokumentiertes Archivierungs- / Löschverfahren |
| Status der Änderungen und Reparaturen (M.A.305) | Eigenes Register: Klassifizierung, Genehmigungsgrundlage, Durchführung, ICA und Übernahme ins Programm, Wägung und Flughandbuch, Warnungen in den Fälligkeiten (Tutorial 26) | ✅ | Klassifizierung und Genehmigung der Änderungen (Part-21) |
| Übergabe der Aufzeichnungen (M.A.307) | Vollständiges Aktenarchiv (HTML-Zusammenfassung, JSON, CSV, SHA-256-Manifest), Empfangsbestätigung, Integritätsprüfung einer empfangenen Akte (Tutorial 30) | ✅ | Übergabeverfahren mit der neuen Organisation |
| Lufttüchtigkeitsprüfung / ARC | ARC-Register, Ablaufwarnung, synthetische Luftfahrzeugakte | ✅ | Prüfverfahren, berechtigtes ARS-Personal |
| Zurückgestellte Mängel | Signierte MEL/CDL-Rückstellung, Grenzen, in die Fälligkeiten integriert | ✅ | Die MEL des Betreibers erfassen |
| Verlängerung von Rückstellungen (RIE) | Nur eine Verlängerung, Kategorien B und C, von der CAMO vor Fristablauf genehmigt und signiert, Dauer ≤ ursprüngliches Intervall, Behörde informiert (Tutorial 31) | ✅ | Von der Behörde akzeptiertes RIE-Verfahren |

## Instandhaltung (Part-145)

| Anforderung | AHMIS-Funktion | Abdeckung | Von der Organisation zu erledigen |
|---|---|---|---|
| Instandhaltungsdaten | Aus dem Programm erzeugte Task Cards, mit Schritten und Referenzen | ✅ | Technischer Inhalt aus den lizenzierten Herstellerdaten |
| Arbeitskarten, Signatur jedes Schritts | Einzeln signierte Schritte, gemessene Werte, N/A | ✅ | — |
| Freigabeberechtigtes Personal und Berechtigungen | Part-66-Lizenz, Berechtigungen je Muster, Kategorie und Gültigkeit, Aussetzung, Prüfung bei jeder Signatur | ✅ | Verwaltung der Berechtigungen (MOE-Verfahren) |
| Unabhängige Prüfung (kritische Aufgaben) | Zweite Signatur zwingend durch eine andere freigabeberechtigte Person | ✅ | Die kritischen Aufgaben im Programm identifizieren |
| Freigabebescheinigung | Elektronisch signiertes CRS, automatische Sperren, Erwähnung der Rückstellungen, Kategorie C für einen großen Check | ✅ | CRS-Text an die MOE angleichen |
| Kalibriertes Werkzeug | Kalibrierung, Ausgabe bei Ablauf verboten, Rückverfolgbarkeit der Verwendungen | ✅ | — |
| Annahme von Komponenten | Wareneingang mit Zertifikat, Eingangsprüfung, automatische Quarantäne, verdächtige Teile | ✅ | — |
| Artikelklassen (145.A.42(a)) | Klasse je P/N (Komponente, Normteil, Material, Verbrauchsmaterial); Form 1 für eine Komponente gefordert, Norm für ein Normteil oder ein Material gefordert (Tutorial 31) | ✅ | Den P/N-Katalog klassifizieren |
| Nicht verwertbare Teile (145.A.42(d)) | Signierte Verschrottung mit Unbrauchbarmachung und Zeugen, endgültiger Status (Tutorial 31) | ✅ | Verfahren zur Unbrauchbarmachung |
| Aktuelle Erfahrung (145.A.35) | 6 Monate in 24, berechnet aus den AHMIS-Signaturen und den erklärten Erfahrungen, für freigabeberechtigtes Personal sperrend (Tutorial 28) | ✅ | Die frühere Erfahrung neuer Mitarbeiter erklären |
| Human Factors, Schulungen | Schulungen je Kategorie, sperrende Pflichtkategorien (Human Factors, Fortbildung), sonstige Ablaufdaten gekennzeichnet | ✅ | Fortbildungsprogramm |
| Ereignismeldung (376/2014, 145.A.60) | Meldung durch das gesamte Personal, Vertraulichkeit, 72-h-Frist, 30-Tage-Folgemeldung, Inhaber der Entwurfsgenehmigung (Design Holder), Abschluss, Warnungen (Tutorial 29) | ✅ | Meldung an die Behörde (ECCAIRS) und Analyse; AHMIS übermittelt nicht automatisch |

## IT-Systeme, elektronische Aufzeichnungen, Informationssicherheit

| Anforderung | AHMIS-Funktion | Abdeckung | Von der Organisation zu erledigen |
|---|---|---|---|
| Integrität und Rückverfolgbarkeit der Aufzeichnungen | Nur schreibender Audit-Trail, feldweise, Löschung verboten | ✅ | — |
| Elektronische Signatur | Erneute Passworteingabe, Identität und Lizenz, Zeitstempel, SHA-256-Hashwert, nicht änderbar | ✅ | Das Signaturverfahren von der Behörde akzeptieren lassen |
| Zugriffskontrolle | Rollen je Aufgabenbereich + individuelle Berechtigungen | ✅ | Personenbezogene Konten, regelmäßige Überprüfung der Rechte |
| Informationssicherheit (Part-IS) | Technische Basis: Authentifizierung, Rückverfolgbarkeit | ⚠️ teilweise | Risikoanalyse, sicheres Hosting (HTTPS), Sicherungen, Kontinuitätsplan, Vorfallmanagement |
| Validierung der Software | 89 automatische Tests der kritischen Regeln | ⚠️ teilweise | Formaler Validierungsplan, Abnahme durch Lufttüchtigkeitsexperten, Versionsverwaltung |

## Bekannte Einschränkungen dieser Version

- **Nur eine Zykleneinheit** je Luftfahrzeug (Zyklen oder Landungen). Spezifische Triebwerkszyklen (NG/NF, Starts) werden nicht getrennt verfolgt.
- Keine Erfassung Flug für Flug: Die Stunden werden je Bericht erfasst (täglich oder je Flug).
- Kein automatischer Import der Herstellerdaten (MSM, MRI, IPC) noch der AD: Die Erfassung erfolgt manuell.
- Qualifikation der Kategorie (A/B1/B2) der Task Card: Richtwert, für die Durchführung nicht sperrend. Die Berechtigung für das Muster und die Freigaberechte sind dagegen sperrend.
- Kein Finanzmodul (Kosten, Abrechnung, Lieferanteneinkauf).
- Demodaten nur auf Französisch (Benutzeroberfläche und Tutorials gibt es auch auf Englisch, Spanisch und Deutsch).

Diese Punkte sind Entwicklungsansätze, die nach Ihrem Bedarf zu priorisieren sind.
