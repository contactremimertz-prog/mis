# 6. The maintenance programme (tasks)

**Account: `camo`**

## Viewing

Menu **Maintenance programme**: 33 demonstration tasks. Filter by type (`H145`) or by origin (MSM/MPD, ALS, AD, SB, operator).

Open **145-05-100 100 h / 12 months check**:

- **Interval** `100 FH / 1 year`: the **first criterion reached** triggers the due item.
- **Tolerance** `10 FH / 30 d`: beyond the limit but within the tolerance, the status is "Within tolerance" (dark orange). Beyond the tolerance, it is "Overdue" (red).
- **Steps**: each line becomes a step to be signed on the task card.
- **Required parts**: they feed the forecast (monthly parts requirements).
- **Status per aircraft**: last accomplishment, limits, remaining values, planned date for each H145.

## Creating a task

1. **+ Create** (or from the NH90 type record: "Add a task").
2. Example:
    - Reference `N90-25-180`, title `Contrôle du kit de flottaison`, type NH90
    - Type: Functional check; ATA `25`
    - Interval: `180` days; tolerance: `15` days
    - Workload: `2` man-hours; qualification B1
    - Steps: `Déplier le kit` / `Contrôler la pression des bouteilles` / `Replier et plomber` (one per line)
3. **Save**, then add a required part (e.g. `DEMO-ORING-12` × 2).

**Result**: the task immediately applies to all NH90s (F-HDMA, F-HDMB). Leave "effectivity" empty for all aircraft of the type, or tick specific registrations.

## Threshold (first due item)

A threshold different from the interval is entered in "FH/cycles/days threshold". Example: first inspection at 1,200 FH, then every 500 FH.

## Task tracked on a component

Filling in "component P/N" attaches the task to the **component's** counters rather than those of the airframe. See **N90-72-500** (RTM322 borescope inspection): the due item follows the engine, even if it changes helicopter.

## Task with independent inspection

Tick "independent inspection required" for critical tasks (flight controls, BTP fasteners, etc.). The task card will then require a second signature by another certifying person (tutorial 13).

## Programme revisions

Every change is traced: **Revision history** button on the task record. Also fill in "AMP revision". A task cannot be deleted: untick "active".
