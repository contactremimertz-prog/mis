# 13. Independent inspection (critical tasks)

**Accounts: `b1`, then `b2`**

Some tasks (flight controls, critical fasteners, borescope inspections, etc.) require a **second signature**, by a person **different** from the person who performed the work and holding a **certifying authorisation** on the type.

Starting situation: on F-HDMD, the task card **Arriel 2E engine borescope inspection** has been performed by Claire DUBOIS (`b1`). It has the status "Performed – awaiting inspection".

## 1. The performer cannot inspect their own work

1. Log in with `b1` and open the task card (menu **Task cards**, filter "Performed – awaiting inspection").
2. The Performance frame states: "You performed this work: the inspection must be signed by another person." No inspection button is offered.

## 2. A non-certifying mechanic cannot inspect

With `meca`, the inspection form does not appear: their "non-certifying mechanic" authorisation does not permit inspection.

## 3. Inspection by another certifying person

1. Log in with `b2` (Karim BENALI, certifying B2 on H145).
2. Open the task card → **Independent inspection** frame: remarks `Images boroscopiques revues, conforme`, password → **Sign the inspection**.

**Result**:

- the task card is **Closed**;
- both signatures (performance and inspection) appear with their "✓ intact" badge;
- the due item of the component task `145-72-500` of engine MOT 1 is recalculated on **the engine's** counters.

## Making a task "critical"

In the maintenance programme, tick "independent inspection required" on the task (tutorial 6). For an out-of-programme task card, tick the same box when creating it.
