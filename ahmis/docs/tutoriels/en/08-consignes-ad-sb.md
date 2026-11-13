# 8. Airworthiness directives (AD) and service bulletins (SB)

**Account: `camo`**

## The life cycle of a directive

1. **Record** the directive: number, issuer, effective date, applicable types and/or P/Ns.
2. AHMIS automatically creates a **"To assess"** status for each potentially affected aircraft (same type, or applicable P/N installed).
3. The CAMO **assesses** each aircraft:
    - **Not applicable**: the justification is mandatory;
    - **Applicable – to be done**: a **follow-up task** is required;
    - **Embodied**: the compliance date is mandatory.
4. The follow-up task appears in the due items. The compliance time counts **from the effective date**.
5. When the task card is closed, the status changes to **Embodied** (one-time directive) or **Repetitive in progress**.

## Exercise 1: assessing the ATR AD

1. Menu **AD / SB** → `DEMO-AD-2026-0177` (ATR 72, flap fittings).
2. F-HDMF line: status **To assess** → **Assess**.
3. Status "Applicable – to be done", justification `MSN 1801 dans la plage d'applicabilité` → **Save**.
4. **Create the follow-up task (ATR72-600)** button: the reference, title and required action are pre-filled.
5. Enter the **cycle threshold** `3000` (compliance time from the effective date) and the workload `4`, then save.

**Result**: in **Due items**, F-HDMF has a new line with a cycle limit equal to the cycles at the effective date + 3,000.

## Exercise 2: declaring non-applicability

1. `DEMO-SB-145-24-010` (optional SB H145) → F-HDMD → **Assess**.
2. Choose "Not applicable" **without** a justification → **Save**: refused.
3. Add `SB optionnel non retenu par l'exploitant – décision CAMO du jj/mm` → **Save**.

## Exercise 3: following a repetitive AD

`DEMO-AD-2026-0101` (NH90 BTP suspension bars) is tracked by a task with a threshold of 50 FH and an interval of 110 FH:

- on **F-HDMA**, it has been accomplished: status "Repetitive in progress", next due item 110 FH later;
- on **F-HDMB**, it has never been done: **Overdue**. Tutorial 24 deals with it.

## Overview

**Status per aircraft** button in the AD/SB list: all the assessments, with filters by status and by aircraft. This is the basic document for the airworthiness review.
