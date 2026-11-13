# 20. Tooling and calibration

**Accounts: `magasin`, `meca`**

## The tooling pool

Menu **Tooling**: reference, status, last calibration, due date and "Calibration OK" indicator.

In the demo, the torque wrench **CLE-DYN-02** has an **expired** calibration ("Tooling out of calibration" dashboard indicator).

## 1. An uncalibrated tool cannot be checked out

1. Account `meca` → a task card **in progress**, for example **100 h / 12 months check** of F-HDMD (if you have already closed it in tutorial 12, start another one, such as "Battery capacity check").
2. **Tooling** frame → choose `CLE-DYN-02` → **Check out the tool**.
3. Refusal: "calibration expired or not recorded, check-out not allowed".

## 2. Recording a calibration

1. Account `magasin` → **Tooling** → `CLE-DYN-02`.
2. "Record a calibration": today's date, laboratory `Laboratoire de métrologie démo`, certificate `MET-2026-118`, result "Pass" → **Save**.

The due date is recalculated (last calibration + 365 days).

## 3. Checking out then returning

1. Account `meca` → same task card → check out `CLE-DYN-02`.
2. It changes to "Checked out", attached to the task card and to your name, with its **calibration validity date** stored.
3. **Return** when the work is finished. Reminder: the task card cannot be signed as long as a tool remains checked out.

## Traceability in case of a non-compliant tool

If a calibration comes back **non-compliant**, the tool goes out of service. The tool record lists all the **uses** (task card, person, dates), which identifies the work to be reassessed since the last valid calibration.
