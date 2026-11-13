# 15. Defects and deferrals (MEL / CDL)

**Accounts: `meca`, `b2`, `planif`**

## 1. Reporting a defect

1. Account `meca` → open **F-HDMA** → **Report a defect**.
2. Source "Crew report (techlog)", techlog ref. `CRM MA-150`, ATA `33`, description `Feu anticollision inférieur inopérant`.
3. **Save**: the defect receives a number `DEF-YYYY-NNNN`, with the status **Open**.

## 2. Deferring per the MEL

Deferral requires a **certifying authorisation** on the type.

1. Account `b2` → menu **Defects & deferrals** → open the defect.
2. **Defer per the MEL / CDL** frame:
    - MEL reference `MEL 33-40-01 (DEMO)`
    - Category `C (10 days)`; leave the limit empty for the standard time limit
    - Procedures `Placard INOP apposé, vol de jour uniquement`
    - Password → **Sign the deferral**

**Result**:

- the defect is **Deferred**, limit = today + 10 days;
- it appears in the **Due items** of F-HDMA (type "Deferred defect") and on the planning;
- if it is still deferred at the time of a CRS, it is **cited in the CRS statement**.

Standard time limits: B = 3 days, C = 10 days, D = 120 days. For category A or outside the MEL, enter the limit (date, hours or cycles).

**Checks**: without a MEL reference, or without any limit, the deferral is refused. The deferral form is not offered to a non-certifying mechanic.

A **single extension** of the time limit (RIE) can then be approved by the CAMO, before the limit: see tutorial 31.

## 3. Rectifying

1. Account `planif` → open the defect → **Create the rectification task card** in an existing WP or "+ New troubleshooting WP".
2. Perform the task card (tutorial 12). When it is closed, the defect changes to **Rectified**.

## Example already loaded

F-HDMC (H135) has a category C **deferred** defect (cabin lighting): see it in its due items and on its record.
