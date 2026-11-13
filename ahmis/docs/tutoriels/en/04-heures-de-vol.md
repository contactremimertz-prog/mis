# 4. Entering flight hours and cycles

**Account: `planif` (or `b1`)**

Hours and landings (cycles) come from the technical log reports (techlog / CRM).

## Entry

1. Dashboard → **Enter flight hours** (or menu **Flight hours** → **+ Create**).
2. Aircraft `F-HDMA`, date today, hours `1.8`, cycles `5`, reference `CRM MA-TEST`.
3. **Save**.

A message displays the new totals.

## What AHMIS does

- It increments the counters of the **airframe**.
- It increments the counters of **all installed components**: TSN/CSN (since new) and TSO/CSO (since overhaul).
- It immediately recalculates the due items.

**To check**:

1. Open F-HDMA: the total hours have increased by 1.8.
2. In "Installed configuration", the TSO of the BTP has also increased by 1.8, and its "Remaining TBO" has decreased by the same amount.
3. In the due items, the "FH left" of the 100 h check has dropped by 1.8.

## Entry checks

- More than 24 h in one day is refused.
- A future date is refused.
- An entry can never be modified: an error is corrected by a new, justified entry, and the history remains complete (menu **Flight hours**).

## Planned utilisation and forecast dates

On the aircraft record, "planned utilisation" (FH/day, cycles/day) is used to convert remaining hours into a **planned date**. Example: 12 FH remaining at 1.6 FH/day gives a due date in 7 days. Change this value (**Edit** button of the aircraft, account `camo`) to see the planned dates move.
