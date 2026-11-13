# 18. Part requests

**Accounts: `meca`, then `magasin`**

## 1. Requesting a part from a task card

1. Account `meca` → task card **100 h / 12 months check** of F-HDMD.
2. **Parts** frame → "Request a part": P/N `DEMO-ORING-12`, quantity `2`, priority "Urgent" → **Request**.

A request `DP-YYYY-NNNN` is created with the status **Requested**. It appears on the dashboard ("Part requests") and in the **Part requests** menu.

## 2. Issuing (stores)

1. Account `magasin` → menu **Part requests** → filter "Requested".
2. Open the request for the **magnetic plug** `DEMO-CHIP-01` (created by the demo).
3. Batch to issue: `LOT-CH-09` → **Issue**.

**Result**:

- the request is **Issued**;
- the batch stock goes down by 1, with an outgoing movement attached to the task card;
- on the task card, the "Consumed" line appears (part → work traceability).

For a **serialised part**, the component changes to "Reserved (task card)". It can then be installed only by that task card (tutorial 14).

## Checks at issue

Only **serviceable** parts of the requested P/N or of an **interchangeable** P/N are offered. At issue, AHMIS re-checks:

- the accepted certificate;
- the expiry (an expired batch is refused);
- the remaining potential (for a serialised part);
- the available quantity.

## Cancelling

An unnecessary request is cancelled from its record (**Cancel the request**). A task card cannot be signed as long as a request remains "Requested".

## Minimum stock

In **Consumables stock**, a quantity less than or equal to the minimum stock is shown in red (e.g. O-rings `LOT-OR-077`). **Inventory** allows a justified adjustment (+/−), traced as a stock movement.
