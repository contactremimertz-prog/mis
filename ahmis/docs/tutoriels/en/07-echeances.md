# 7. Due items (limits)

**Account: `camo`**

Menu **Due items**: the consolidated list of everything falling due across the fleet.

## Types of due items

| Type | Origin |
|---|---|
| Task | Maintenance programme (airframe) |
| Component task | Task tracked on a component's counters |
| LLP / TBO | Limits of installed components |
| ARC | Expiry of the airworthiness review |
| Deferred defect | MEL/CDL limit of a deferred defect |
| Directive | AD/SB to be assessed, or applicable without a follow-up task |

## Statuses

| Status | Meaning |
|---|---|
| **Overdue** (red) | Limit exceeded beyond the tolerance |
| **Within tolerance** | Limit exceeded but within the permitted tolerance |
| **To plan** (orange) | Planned date within 30 days (`AHMIS_ALERT_DAYS` setting) |
| **OK** | Later |

## Reading a line

- **Last accomplishment**: date and counters.
- **Limit** FH / cycles / date.
- **Remaining** FH / cycles (negative in red).
- **Planned date**: the nearest of the dates obtained for each criterion, by projecting the planned utilisation.
- **Driver**: the one that triggers (FH, cycles or calendar).

## Exercises

1. Filter **Aircraft = F-HDMB**.
    - `DEMO-AD-2026-0101`: **Overdue**, −27.6 FH. The AD came into force 200 days ago with a compliance time of 50 FH, and has never been accomplished.
    - `N90-05-100`: **Within tolerance** (−6 FH on a tolerance of 10 FH).
    - Rotor hub LLP: **To plan**.
2. Filter **Type = LLP**, then **Status = To plan**.
3. Filter **Due within = 90 days**, then **CSV export**: the file opens in Excel (";" separator).

## Planning from the due items

**Account: `planif`** (the CAMO identifies the needs, the planner places them in a work package). When an aircraft is selected, tick boxes appear:

1. Filter **F-HDMB**.
2. Tick `DEMO-AD-2026-0101`, `N90-05-100` and the rotor hub LLP.
3. Work package: choose **WP … 100 h check** (already planned in 5 days).
4. **Create the task cards**.

**Result**: you arrive at the work package with 3 task cards generated: the task steps, and a "removal/installation" task card for the LLP. The next steps are in tutorial 11.
