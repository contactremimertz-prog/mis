# 14. Changing a component (removal / installation)

**Accounts: `planif`, then `b1`**

Starting situation: on F-HDMD (H145), the defect "Vibrations anormales ressenties au palonnier" has a rectification task card. The stores have already **reserved** for it an overhauled Fenestron gearbox, `DEMO-145FEN-01` S/N `DEMO-F1459` (AOG request issued).

## 1. Starting the task card

1. Account `b1` → menu **Task cards** → **Rectification DEF-… : Vibrations anormales…**.
2. **Start the task card**.

## 2. Trying a non-compliant part

In the **Component change** frame:

- Component removed: `DEMO-145FEN-01 S/N DEMO-F1451` (position BTA)
- Reason: `Vibrations – dépose pour expertise`
- Component installed: `DEMO-350TGB-01 S/N DEMO-T3599` (a BTA from an **NH90**)
- Password → **Record the change**

AHMIS refuses: "Installation refused: P/N not applicable to type H145". **Nothing has been modified**: the original gearbox is still in place.

## 3. Compliant change

Repeat with component installed: `DEMO-145FEN-01 S/N DEMO-F1459`, the reserved part. Leave the position empty: AHMIS takes the position of the removed component.

**Result**:

- **Configuration** of F-HDMD: in position BTA, gearbox S/N DEMO-F1459 is installed, with its TSO and remaining TBO.
- **Record of the removed gearbox** (DEMO-F1451): status "Unserviceable (U/S)", removal reason, and in its "back-to-birth" traceability the aircraft dates and counters at installation **and** removal, with the task card.
- **Record of the installed gearbox**: a new installation, with the counters at installation.
- An electronic signature describes the movement.

## 4. Closing

Work report `Remplacement de la boîte Fenestron, essais vibratoires conformes`, time spent `5` → **Sign the work**.

The defect changes to **Rectified**, with the corrective action taken from the work report.

## Checks performed at every installation

| Check | Example of refusal |
|---|---|
| Part status | Part in quarantine, U/S or reserved for another task card |
| Accepted release certificate | Part without EASA Form 1 / 8130-3 |
| Remaining potential | Life limit or TBO reached |
| Applicability | P/N not applicable to the type |
| Free position | Position already occupied by the same P/N |

The removed part can go back as "U/S" (failure), "Quarantine" (investigation) or "Serviceable" (removal for convenience). It keeps all its counters.
