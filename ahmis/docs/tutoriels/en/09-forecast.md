# 9. The forecast (maintenance forecast)

**Account: `camo` or `planif`**

Menu **Forecast**.

## Principle

The forecast **unrolls** all the due items over a given horizon:

- a repetitive task generates several occurrences (e.g. the 50 FH lubrication of an H145 at 2 FH/day comes round every 25 days);
- LLP, TBO, ARC and deferred defects appear once;
- items already overdue are placed at today's date, with the "overdue" badge.

## Reading

- Indicators: number of due items, **total workload in man-hours**, number of removals at limit.
- **Monthly workload**: a histogram per month, with the breakdown by aircraft.
- The detail of each month opens on click: occurrences, driver, workload, **planned parts** and the month's parts requirement (taken from the tasks' "required parts").

## Exercises

1. Horizon `365` days, whole fleet → **Compute**. Spot the month of the **ATR C check** (600 man-hours): a workload peak to be anticipated.
2. Aircraft `F-HDMD`, horizon `180` days: the H145's own workload.
3. **Simulation**: whole fleet, utilisation `130` % → **Compute**. Due items in hours and cycles come closer; calendar ones do not move. Compare with 100 %.
4. **CSV export**: the complete list of occurrences, for a spreadsheet or a planning tool.

> The forecast is a projection based on the "planned utilisation" of each aircraft. Keep these values up to date (aircraft record) for a reliable forecast.
