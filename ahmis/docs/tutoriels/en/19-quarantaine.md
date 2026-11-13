# 19. Quarantine, suspected parts and expiry

**Account: `magasin`**

Menu **Quarantine**: all blocked parts.

## What the demo contains

| Part | Situation |
|---|---|
| Starter-generator `DEMO-G1666` | **Suspected part (SUP)**: non-compliant identification plate, certificate rejected |
| RTM322 engine `DEMO-E21099` | **U/S**: removed for over-temperature |
| Oil batch `LOT-OIL-2502` (line store) | Serviceable but **expired**: listed in the orange box |

## 1. Trying to release a suspected part

1. Open `DEMO-G1666` → "Change the status" frame: new status "In stock – serviceable", location `MAG-PRINC`, reason `Test` → **Change the status**.
2. AHMIS refuses: "Return to serviceable stock not possible without an accepted release certificate".

A suspected part stays in quarantine until the quality decision. If the decision is scrapping, change the status to **Scrapped** with the reason `SUP confirmée – déclaration à l'autorité`. The part stays in AHMIS for traceability, but can never be used again.

## 2. Sending an engine for overhaul

`DEMO-E21099` → status "In repair / overhaul", reason `Envoyé à l'atelier moteur, BL 4471`. On its return, receive it with its new Form 1 (tutorial 17).

## 3. Handling an expired batch

In the orange box, click `LOT-OIL-2502` → status "Expired", reason `Date dépassée` → **Save**. The batch is no longer offered for issue, which was already the case: AHMIS refuses any issue of a batch whose date has passed.

## 4. Placing a part in quarantine

On any component in stock, choose the status "Quarantine": if no location is specified, it is automatically stored in `QUAR`.
