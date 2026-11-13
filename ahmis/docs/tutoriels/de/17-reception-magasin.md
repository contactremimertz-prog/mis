# 17. Wareneingang und Freigabezertifikate

**Konto: `magasin`**

Jedes Teil gelangt über den **Wareneingang** mit seinem Freigabezertifikat in AHMIS.

## 1. Ein Verbrauchsmaterial annehmen

Menü **Wareneingang**:

- P/N `DEMO-OIL-T2` (Turbinenöl), Chargennr. `LOT-OIL-2701`, Menge `24`, Lagerort `MAG-PRINC`, Ablaufdatum in 2 Jahren (für diesen Artikel Pflicht);
- Zertifikat: Art „Konformitätsbescheinigung“, Nr. `COC-5521`, Aussteller `Distributeur agréé démo`, heutiges Datum;
- haken Sie die **3 Eingangsprüfungen** an → **Speichern**.

**Ergebnis**: Die Charge erscheint im **Verbrauchsmateriallager**, „Verwendbar“, mit einer Zugangsbewegung.

## 2. Ein seriennummerngeführtes Teil annehmen

- P/N `DEMO-SG-150` (Starter-Generator), S/N `DEMO-G1700`, Menge 1, Zustand „Repariert“, TSN `850`, CSN `2400`, TSO `0`, CSO `0`;
- Zertifikat: EASA Form 1, Nr. `F1-778`, Aussteller `Atelier équipements agréé`, Genehmigungsnr. `FR.145.DEMO-Y`, Status „Repariert“;
- 3 Prüfungen angehakt → **Speichern**.

**Ergebnis**: Die Komponentenakte öffnet sich, mit ihrem akzeptierten Zertifikat. Das Teil kann ausgegeben und eingebaut werden.

## 3. Nicht konformer Wareneingang → automatische Quarantäne

Wiederholen Sie einen Wareneingang (S/N `DEMO-G1701`) **ohne** „Zertifikat vollständig, unterschrieben, genehmigter Aussteller“ anzuhaken.

**Ergebnis**: „in QUARANTÄNE gestellt“. Das Teil wird in `QUAR` gelagert, sein Zertifikat wird als abgelehnt markiert, und es kann weder ausgegeben noch eingebaut werden.

## Prüfungen bei der Eingabe

- S/N ist für ein seriennummerngeführtes Teil Pflicht; Menge 1.
- Ein bereits bekanntes Paar P/N + S/N wird abgelehnt: „Dublette oder verdächtiges Teil“.
- Das Ablaufdatum ist für Artikel mit begrenzter Lagerdauer Pflicht.
- Ein zukünftiges Zertifikatsdatum wird abgelehnt.
- **Artikelklasse** (P/N-Akte, 145.A.42): Eine **Komponente** (component) erfordert ein zulässiges Freigabezertifikat (EASA Form 1, FAA 8130-3, Doppelfreigabe, TCCA Form One). Eine Konformitätsbescheinigung (CoC) wird nur für ein Normteil, ein Rohmaterial oder ein Verbrauchsmaterial akzeptiert. Siehe Tutorial 31.

## Zertifikate

Menü **Freigabezertifikate**: alle Form 1, 8130-3 und CoC. Der Scan des Zertifikats kann angehängt werden (Feld „Scan des Zertifikats“).
