# 14. Eine Komponente wechseln (Ausbau / Einbau)

**Konten: `planif`, dann `b1`**

Ausgangslage: Bei F-HDMD (H145) hat der Mangel „Vibrations anormales ressenties au palonnier“ eine Task Card zur Behebung. Das Lager hat dafür bereits ein überholtes Fenestron-Getriebe `DEMO-145FEN-01` S/N `DEMO-F1459` **reserviert** (AOG-Anforderung ausgegeben).

## 1. Die Task Card starten

1. Konto `b1` → Menü **Task Cards** → **Rectification DEF-… : Vibrations anormales…**.
2. **Task Card starten**.

## 2. Ein nicht konformes Teil ausprobieren

Im Feld **Komponentenwechsel**:

- Ausgebaute Komponente: `DEMO-145FEN-01 S/N DEMO-F1451` (Position BTA)
- Grund: `Vibrations – dépose pour expertise`
- Eingebaute Komponente: `DEMO-350TGB-01 S/N DEMO-T3599` (ein BTA einer **NH90**)
- Passwort → **Wechsel erfassen**

AHMIS lehnt ab: „Einbau abgelehnt: P/N für das Muster H145 nicht anwendbar“. **Es wurde nichts geändert**: Das ursprüngliche Getriebe ist weiterhin eingebaut.

## 3. Konformer Wechsel

Wiederholen Sie den Vorgang mit der eingebauten Komponente `DEMO-145FEN-01 S/N DEMO-F1459`, dem reservierten Teil. Die Position bleibt leer: AHMIS übernimmt die der ausgebauten Komponente.

**Ergebnis**:

- **Konfiguration** von F-HDMD: In Position BTA ist das Getriebe S/N DEMO-F1459 eingebaut, mit seinem TSO und seiner verbleibenden TBO.
- **Akte des ausgebauten Getriebes** (DEMO-F1451): Status „Nicht verwendbar (U/S)“, Ausbaugrund, und in seiner „Back-to-birth“-Rückverfolgbarkeit die Daten und Luftfahrzeugzähler beim Einbau **und** beim Ausbau, mit der Task Card.
- **Akte des eingebauten Getriebes**: eine neue Montage, mit den Zählern beim Einbau.
- Eine elektronische Signatur beschreibt die Bewegung.

## 4. Abschließen

Arbeitsbericht `Remplacement de la boîte Fenestron, essais vibratoires conformes`, aufgewendete Zeit `5` → **Arbeiten signieren**.

Der Mangel wechselt auf **Behoben**, mit der aus dem Arbeitsbericht übernommenen Korrekturmaßnahme.

## Bei jedem Einbau durchgeführte Prüfungen

| Prüfung | Beispiel einer Ablehnung |
|---|---|
| Status des Teils | Teil in Quarantäne, U/S oder für eine andere Task Card reserviert |
| Akzeptiertes Freigabezertifikat | Teil ohne EASA Form 1 / 8130-3 |
| Restpotenzial | Lebensdauergrenze oder TBO erreicht |
| Anwendbarkeit | P/N für das Muster nicht anwendbar |
| Freie Position | Position bereits durch dieselbe P/N belegt |

Das ausgebaute Teil kann als „U/S“ (Defekt), „Quarantäne“ (Begutachtung) oder „Verwendbar“ (Ausbau aus Zweckmäßigkeit) weitergehen. Es behält alle seine Zähler.
