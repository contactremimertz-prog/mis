# 18. Teileanforderungen

**Konten: `meca`, dann `magasin`**

## 1. Ein Teil von einer Task Card anfordern

1. Konto `meca` → Task Card **Visite 100 h / 12 mois** von F-HDMD.
2. Feld **Teile** → „Teil anfordern“: P/N `DEMO-ORING-12`, Menge `2`, Priorität „Dringend“ → **Anfordern**.

Eine Anforderung `DP-JJJJ-NNNN` wird mit dem Status **Angefordert** angelegt. Sie erscheint in der Übersicht („Teileanforderungen“) und im Menü **Teileanforderungen**.

## 2. Ausgeben (Lager)

1. Konto `magasin` → Menü **Teileanforderungen** → Filter „Angefordert“.
2. Öffnen Sie die Anforderung für den **Magnetstopfen** `DEMO-CHIP-01` (von der Demo angelegt).
3. Auszugebende Charge: `LOT-CH-09` → **Ausgeben**.

**Ergebnis**:

- Die Anforderung ist **Ausgegeben**;
- der Bestand der Charge sinkt um 1, mit einer an die Task Card gebundenen Abgangsbewegung;
- auf der Task Card erscheint die Zeile „Verbraucht“ (Rückverfolgbarkeit Teil → Arbeiten).

Bei einem **seriennummerngeführten Teil** wechselt die Komponente auf „Reserviert (Task Card)“. Sie kann dann nur durch diese Task Card eingebaut werden (Tutorial 14).

## Prüfungen bei der Ausgabe

Angeboten werden nur **verwendbare** Teile der angeforderten P/N oder einer **austauschbaren** P/N. Bei der Ausgabe prüft AHMIS erneut:

- das akzeptierte Zertifikat;
- das Ablaufdatum (eine abgelaufene Charge wird abgelehnt);
- das Restpotenzial (bei einem seriennummerngeführten Teil);
- die verfügbare Menge.

## Stornieren

Eine nicht benötigte Anforderung wird über ihre Akte storniert (**Anforderung stornieren**). Eine Task Card kann nicht signiert werden, solange eine Anforderung „Angefordert“ bleibt.

## Mindestbestand

Im **Verbrauchsmateriallager** wird eine Menge, die kleiner oder gleich dem Mindestbestand ist, rot angezeigt (z. B. O-Ringe `LOT-OR-077`). Die **Inventur** ermöglicht eine begründete Anpassung (+/−), die als Lagerbewegung protokolliert wird.
