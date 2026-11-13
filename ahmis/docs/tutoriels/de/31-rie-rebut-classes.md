# 31. Verlängerung von Rückstellungen, nicht verwertbare Teile, Artikelklassen

## A. Einmalige Verlängerung einer Rückstellung (RIE)

**Konto: `camo`**

Die MEL erlaubt für die Kategorien **B und C** **eine einzige** Verlängerung des Behebungsintervalls (RIE). Sie wird von der CAMO **vor Fristablauf** genehmigt, für eine Dauer von höchstens dem ursprünglichen Intervall, und die Behörde wird informiert.

1. Menü **Mängel & Rückstellungen** → **DEF-...-0002** (F-HDMC, Kabinenbeleuchtung, Kat. C, Grenze T+10).
2. Feld **Frist verlängern (RIE)**: neue Grenze (Datum) T+20, RIE-Referenz `RIE-2026-001`, Begründung `Ampoule en commande, livraison J+12`. Haken Sie „Behörde informiert“ an, falls erledigt. Passwort → **Verlängerung genehmigen und signieren**.

**Ergebnis**: Die neue Grenze wird überall verwendet (Fälligkeiten, Planung, Übersicht). Die Akte zeigt die ursprüngliche Grenze, den Genehmigenden und die Referenz, und eine Signatur „Verlängerung der Rückstellung (RIE)“ wird hinzugefügt.

**Prüfungen**:

| Fall | Ergebnis |
|---|---|
| Neue Grenze über T+20 hinaus (ursprüngliches Intervall 10 T) | Ablehnung: „Verlängerung (Datum) größer als das ursprüngliche Intervall“ |
| Ein in der ursprünglichen Rückstellung nicht vorhandenes Kriterium hinzufügen (z. B. FH) | Ablehnung |
| Zweite Verlängerung | Ablehnung: „eine zweite Verlängerung ist verboten“ |
| Grenze bereits erreicht | Ablehnung: „muss vor Fristablauf genehmigt werden“ |
| Kategorie A, D oder außerhalb der MEL | Ablehnung |
| Nicht-CAMO-Benutzer (z. B. `b2`) | Feld nicht angezeigt, Aktion abgelehnt |

## B. Nicht verwertbares Teil: Verschrottung

**Konto: `magasin`**

Ein nicht verwertbares Teil (LLP an der Grenze, nicht reparierbar, beschädigt, unzureichende Rückverfolgbarkeit) muss **unbrauchbar gemacht** werden, damit es nie wieder in den Versorgungskreislauf gelangen kann (145.A.42(d), M.A.504(d)).

1. Menü **Komponenten** → eine ausgebaute Komponente im Status „Nicht verwendbar“ oder „Quarantäne“.
2. Feld **Verschrotten (nicht verwertbares Teil)**: Datum, Grund, Methode der Unbrauchbarmachung (`Découpe`), Zeuge (`Isabelle GARNIER (qualité)`), Ref. Vernichtungsbescheinigung. Passwort → **Endgültige Verschrottung signieren**.

**Ergebnis**: Status **Verschrottet**, endgültig. Der Status kann weder über den Bildschirm noch über die Administration noch über die API geändert werden. Beispiel in der Demo: die Rotornabe `DEMO-S3399`, an der Lebensdauergrenze.

Ein eingebautes oder reserviertes Teil kann nicht verschrottet werden.

## C. Artikelklassen (145.A.42(a))

**Konto: `magasin`**

Jede P/N-Referenz hat eine **Klasse**, die den beim Wareneingang geforderten Nachweis bestimmt:

| Klasse | Akzeptierter Nachweis | Beispiel in der Demo |
|---|---|---|
| Komponente (component) | EASA Form 1, FAA 8130-3, Doppelfreigabe, TCCA Form One | Triebwerke, Hauptgetriebe, Ölfilter, Magnetstopfen |
| Normteil | Konformitätsbescheinigung (CoC), Norm Pflicht | O-Ring `AS568-012` |
| Rohmaterial | CoC, Spezifikation Pflicht | Sicherungsdraht `MS20995C32` |
| Verbrauchsmaterial | CoC | Öl, Fett |

**Test**: Menü **Wareneingang** → P/N `DEMO-350FLT-01` (Filter, Komponente) mit einem Zertifikat „Konformitätsbescheinigung“ → Ablehnung: „ein zulässiges Freigabezertifikat … ist erforderlich“. Derselbe Versuch mit `DEMO-OIL-T2` (Verbrauchsmaterial) wird akzeptiert.

Eine seriennummerngeführte, austauschbare (rotable) oder lebensdauerbegrenzte Referenz ist zwingend eine Komponente.
