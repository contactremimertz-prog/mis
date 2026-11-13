# 12. Performing a task card

**Account: `meca`**

Starting situation: on F-HDMD (H145), the **100 h / 12 months check** task card is in progress. 3 steps out of 6 are signed, a torque wrench is checked out, and a request for a magnetic plug is waiting at the stores.

## 1. Opening the task card

Menu **Task cards** → filter Status "In progress" → **100 h / 12 months check** (WP "100 h check + engine borescope inspection").

## 2. Signing the remaining steps

For steps 4, 5 and 6:

1. Enter a measured value if needed (e.g. `Niveau OK`); tick N/A if the step does not apply.
2. Enter your password → **Sign**.

Each signed step displays your name, your stamp (`LM1`) and the timestamp.

**Try** a wrong password: "Wrong password or signature code: signature refused".

## 3. Trying to sign the work

Work report `Visite effectuée, RAS`, time spent `7.5`, password → **Sign the work**.

AHMIS **refuses**: "Part requests are still pending". This is intentional: a task is not closed with a part still pending.

## 4. Unblocking

1. **Part**: the storekeeper issues the request (tutorial 18). If you do not need it, ask the stores to cancel it.
2. **Tooling**: in the Tooling frame, click **Return** on `CLE-DYN-01`. As long as a tool is checked out, signing is also blocked.

## 5. Signing the work

Repeat step 3. The task card changes to **Closed**, because this task does not require an independent inspection.

## What AHMIS does on closure

- It records the task's **accomplishment** at the aircraft's current counters.
- It **recalculates** the due item: the F-HDMD 100 h check returns to "OK", with 100 FH ahead (check in **Due items**).
- If the task tracks an AD, it updates the directive's status (tutorial 8).
- If the task card rectifies a defect, it closes the defect (tutorial 15).

## Automatic checks at signature

| Rule | Message |
|---|---|
| Staff record linked to the account | "Your account is not linked to any staff record" |
| Valid authorisation on the type | "… has no valid authorisation on type H145" |
| All steps signed | "3 unsigned step(s)" |
| Work report filled in | "The work report is mandatory" |
| No part request pending | "Part requests are still pending" |
| Tooling returned | "Tooling not returned: CLE-DYN-01" |

## Finding during a check

The **Report a finding** frame creates in one click a **defect** and a **rectification task card** in the same WP, linked to the originating task card. Try: `Légère corrosion sur ferrure de capot BTP`.

## Deferring or cancelling

- **Defer** (reason mandatory): the task card is deferred, and the deferral appears in the CRS.
- **Cancel**: only if no step is signed.
