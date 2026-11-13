# 19. Quarantäne, verdächtige Teile und Ablaufdatum

**Konto: `magasin`**

Menü **Quarantäne**: alle gesperrten Teile.

## Was die Demo enthält

| Teil | Situation |
|---|---|
| Starter-Generator `DEMO-G1666` | **Verdächtiges Teil (SUP)**: Typenschild nicht konform, Zertifikat abgelehnt |
| Triebwerk RTM322 `DEMO-E21099` | **U/S**: wegen Übertemperatur ausgebaut |
| Ölcharge `LOT-OIL-2502` (Lager Linie) | Verwendbar, aber **abgelaufen**: im orangefarbenen Kasten aufgeführt |

## 1. Versuchen, ein verdächtiges Teil freizugeben

1. Öffnen Sie `DEMO-G1666` → Feld „Status ändern“: neuer Status „Im Lager – verwendbar“, Lagerort `MAG-PRINC`, Grund `Test` → **Status ändern**.
2. AHMIS lehnt ab: „Rückführung ins verwendbare Lager ohne akzeptiertes Freigabezertifikat nicht möglich“.

Ein verdächtiges Teil bleibt bis zur Qualitätsentscheidung in Quarantäne. Lautet die Entscheidung Verschrottung, setzen Sie den Status auf **Verschrottet** mit dem Grund `SUP confirmée – déclaration à l'autorité`. Das Teil bleibt zur Rückverfolgbarkeit in AHMIS, kann aber nie wieder verwendet werden.

## 2. Ein Triebwerk zur Überholung schicken

`DEMO-E21099` → Status „In Reparatur / Überholung“, Grund `Envoyé à l'atelier moteur, BL 4471`. Bei der Rückkehr nehmen Sie es mit seinem neuen Form 1 an (Tutorial 17).

## 3. Eine abgelaufene Charge behandeln

Klicken Sie im orangefarbenen Kasten auf `LOT-OIL-2502` → Status „Abgelaufen“, Grund `Date dépassée` → **Speichern**. Die Charge wird bei der Ausgabe nicht mehr angeboten, was bereits der Fall war: AHMIS lehnt jede Ausgabe einer Charge ab, deren Datum überschritten ist.

## 4. Ein Teil in Quarantäne setzen

Wählen Sie bei einer beliebigen Komponente im Lager den Status „Quarantäne“: Ohne angegebenen Lagerort wird sie automatisch in `QUAR` eingelagert.
