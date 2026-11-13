# 27. Jährliche Überprüfung des Instandhaltungsprogramms

**Konto: `camo`**

M.A.302(g) verlangt, jedes Instandhaltungsprogramm regelmäßig (mindestens einmal jährlich) zu überprüfen und bei Bedarf zu ändern: Wirksamkeit (Zuverlässigkeit, wiederkehrende Mängel), neue Anweisungen (MSM/MPD-Revisionen, AD, SB, ICA aus Änderungen).

## 1. Stand der Überprüfungen

Die **Übersicht** zeigt für jedes betriebene Muster, dessen Überprüfung fehlt, überfällig ist oder innerhalb von 30 Tagen ansteht, einen Banner „Überprüfung des Instandhaltungsprogramms“. Menü **Programmüberprüfung**:

| Muster | Situation in der Demo |
|---|---|
| ATR72-600 | Keine Überprüfung erfasst |
| Super Puma | Überprüfung überfällig (letzte Überprüfung vor 13 Monaten) |
| H135 | Überprüfung innerhalb von 30 Tagen fällig |
| NH90, H145 | Aktuell (NH90 geändert auf „DEMO rév. 4“) |

Die Akte des **Luftfahrzeugmusters** (Flotte → Muster & Konfiguration) zeigt ebenfalls den Stand und die letzten Überprüfungen.

## 2. Eine Überprüfung ohne Änderung erfassen

1. Zeile **Super Puma** → **Neue Überprüfung**. Programm und geprüfte Revision werden von der vorherigen Überprüfung übernommen.
2. Durchgeführt von `Julien MOREAU (CAMO)`. Haken Sie **beide** Prüfkästchen an (Zuverlässigkeit und neue Anweisungen).
3. Feststellungen `Aucun défaut répétitif, pas de nouvelle révision MSM`; Ergebnis „Programm ohne Änderung bestätigt“ → **Speichern**.

**Ergebnis**: Super Puma wechselt auf „Aktuell“, nächste Überprüfung in 12 Monaten.

## 3. Eine Änderung des Programms erfassen

1. Zeile **ATR72-600** → **Neue Überprüfung**: Programm `AMP-ATR72-DEMO`, geprüfte Revision `DEMO rév. 3`.
2. Ergebnis „Programm geändert“, neue Revision `DEMO rév. 4`, Änderungen `Ajout des ICA de la modification MOD-...`.
3. Genehmigungsart „Indirekte Genehmigung“, Referenz `PAI-2026-020`, Datum → **Speichern**.

**Ergebnis**: Alle aktiven Aufgaben des Musters wechseln auf „AMP-Revision: DEMO rév. 4“.

## 4. Prüfungen

- Unvollständige Überprüfung (Zuverlässigkeit oder Anweisungen nicht geprüft): abgelehnt.
- Änderung ohne neue Revision, mit identischer Revision, ohne Beschreibung der Änderungen oder ohne Genehmigung: abgelehnt.
- Nächste Überprüfung über 12 Monate hinaus festgelegt: abgelehnt. Die Periodizität wird mit `AHMIS_AMP_REVIEW_MONTHS` eingestellt.
- Überprüfung mit Datum in der Zukunft: abgelehnt.
