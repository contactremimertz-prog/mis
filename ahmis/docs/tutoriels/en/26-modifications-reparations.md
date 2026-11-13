# 26. Register of modifications and repairs

**Accounts: `camo`, `b1`**

M.A.305 requires the status of the modifications and repairs of each aircraft to be known at all times, with their approval basis and the resulting instructions for continued airworthiness (ICA).

## 1. Recording a modification

1. Account `camo` → menu **Modifications & repairs** → **+ Create**.
2. Aircraft `F-HDMA`, type "Modification", classification "Minor", title `Installation d'un kit caméra externe`, ATA `25`.
3. Approval basis "DOA / Part-21J approval", reference `DOA-MIN-2026-118 (DEMO)`.
4. Status "Embodied", embodied on: today's date, ICA: `Supplément MSM 25-10 (DEMO)`. Tick "affects mass and balance" → **Save**.

**Result**: the modification receives a number `MOD-YYYY-NNNN`. Its record shows two **items to close**: "ICA not yet included in the maintenance programme" and "weight and balance report to be updated". They also appear in the **Due items** of F-HDMA, type "Modification / repair".

## 2. Closing the follow-up

1. **Edit** the modification: tick "ICA included in the maintenance programme" and "follow-up actions done".
2. **Save**: the items to close disappear from the due items.

To include the ICA, create the corresponding task in the programme (tutorial 6), then trace the new revision in the programme review (tutorial 27).

## 3. From a task card

Account `b1` → a task card → link **+ Record a modification or repair performed on this task card**. The form is pre-filled (aircraft, component, title, ATA, date), and the task card is linked.

## 4. Checks

| Rule | Message |
|---|---|
| Major: EASA approval, STC or DOA | "A major modification or repair requires an EASA approval, an STC or a DOA approval." |
| Standard change: CS-STAN | "A standard change must refer to CS-STAN." |
| Embodied: date mandatory | "Embodiment date is mandatory." |
| Embodied: ICA or "no associated ICA" | "Enter the ICA, or tick “no associated ICA”." |
| Removed / cancelled: reason | "Reason is mandatory." |

A modification cannot be deleted: change it to the status "Removed / cancelled" with a reason.
