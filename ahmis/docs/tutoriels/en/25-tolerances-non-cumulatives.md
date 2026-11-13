# 25. Tolerances: accomplishment within tolerance, non-cumulative

**Account: `camo`**

A tolerance allows a task to be accomplished a little after its limit (for example +10 FH or +30 days on a 100 h check). It is **not cumulative**: when a task is done within tolerance, the next due item is counted from the **theoretical limit**, not from the actual date or hours. Hours are therefore never "gained" by using the tolerance.

## 1. Starting situation

Menu **Due items** → aircraft **F-HDMB**: the task `N90-05-100 100 h / 12 months check` is **Within tolerance**. Theoretical limit `3,881.6 FH`, current counter `3,887.6 FH`, i.e. 6 FH overrun on a tolerance of 10 FH.

## 2. Recording the accomplishment

1. Click `N90-05-100` → **Record an accomplishment (history)**.
2. Aircraft `F-HDMB`, today's date, FH `3887.6`, cycles `11623`, origin "External organisation", reference `CRS-EXT-001`, certified by `Atelier externe` → **Save**.

**Result**:

- on the task record, the accomplishment carries the **within tolerance** badge;
- in the due items, the next limit is **3,981.6 FH** (3,881.6 + 100), and not 3,987.6. The note "Accomplished within tolerance: next due item counted from the theoretical limit" reminds you of this;
- for the date, the accomplishment was not late: the next calendar due item is counted from the actual date (+12 months).

Each criterion (FH, cycles, date) is treated separately: the base used is the smaller value between the actual accomplishment and the limit.

## 3. Accomplishment outside tolerance

If the accomplishment exceeds the tolerance, it is marked **outside tolerance**. The next due item then restarts from the actual accomplishment, and the overrun remains visible in the history for the CAMO's analysis.

## 4. Entry rules

- The accomplishments of a given task must be entered in chronological order.
- A tolerance is **prohibited** on an ALS or CMR task (airworthiness limitations).
- A tolerance on an AD task requires a **reference** (paragraph of the AD that permits it).
