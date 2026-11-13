# 11. Planning and work packages

**Account: `planif`**

A **work package (WP)** groups the work on one aircraft for one downtime: dates, station, type of check and task cards.

## The hangar planning

Menu **Planning**: one row per aircraft, one column per day (8 weeks).

- The **bars** are the WPs: blue = planned, orange = in progress, green = released to service.
- The **dots** are the due items: red = overdue, orange = to plan, grey = scheduled.
- Hover over a dot or a bar for details; click to open.
- "← 4 weeks / 4 weeks →" buttons to navigate.

**Spot**: the F-HDMD WP in progress, the F-HDMB WP planned in 5 days, and the red dots of F-HDMB (overdue AD).

## Creating a work package

1. **New work package**.
2. Aircraft `F-HDMA`, title `Visite 100 h`, type "Periodic check", station `Base Alpes`, from next Monday to Tuesday, status "Planned".
3. **Save**: the number `WP-YYYY-NNNN` is assigned automatically.

## Filling the work package

On the WP record:

1. **Add due items**: the list offers the aircraft's due items up to 30 days after the end of the WP, except those already planned. Tick `N90-05-100`, `DEMO-AD-2026-0101` and `N90-24-365` → **Create the selected task cards**.
2. **Add a programme task**: choose a task that is not due, for example `N90-63-200`, to bring it forward.
3. **Additional work**: an out-of-programme task card, for example `Remplacement ampoule phare d'atterrissage`, ATA `33`, 0.5 man-hours.

**Result**:

- each task card takes over the task's title, ATA, zone, qualification, workload and **steps**;
- the WP's "Planned workload" card totals the man-hours;
- the added items disappear from the "due items" list (no duplicates).

## Printing

**Print the work package**: the WP summary and the CRS on paper. Each task card also has its own **Print** button, for workshops that work on paper.

## Statuses of a WP

| Status | Transition |
|---|---|
| Draft / Planned | At creation |
| In progress | Automatically when the 1st task card is started (the aircraft becomes "In maintenance") |
| Released to service | When the CRS is signed (tutorial 16): the WP is then **locked** |
| Cancelled | Manually, via "Edit" |
