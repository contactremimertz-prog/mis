# 3. Creating a type and an aircraft, taking over its configuration

**Account: `camo`**

Objective: bring a new NH90, F-HDMX, into the fleet with its first engine.

## 1. The aircraft type

The NH90 type already exists. To see how a type is defined:

1. Menu **Types & configuration** → click **NH90**.
2. The record shows the aircraft of the type, the **maintenance programme** (active tasks), the authorised staff and the applicable P/Ns.

To create a new type: **+ Create** button in the list. The "Cycle label" field allows "Landings" to be displayed for a helicopter.

## 2. Creating the aircraft

1. Menu **Fleet** → **+ Create**.
2. Fill in:
    - Registration: `F-HDMX`
    - Serial number: `9199`
    - Type: `NHIndustries NH90`
    - Manufacture date: 3 years ago
    - Total hours: `1250`; cycles: `3800`; counters up to date as of: today
    - Planned utilisation: `1.5` FH/day and `4` cycles/day
3. **Save**.

**Result**: the record opens. All the tasks of the NH90 programme already appear in **Due items**. As there is no history, most are calculated from manufacture and come out as **"Overdue"**. This is intentional: AHMIS never assumes that a task has been done.

> Counters can only be entered at creation. Afterwards, they change only through flight hours entries (tutorial 4), to keep full traceability.

## 3. Taking over the task history

For each task, record the last known accomplishment (taken from the logbook):

1. In the due items table of F-HDMX, click the task **N90-05-100 100 h / 12 months check**.
2. In "Status per aircraft", click **historical** on the F-HDMX line.
3. Enter: date 2 months ago, FH `1190`, cycles `3620`, origin "Historical entry", reference `Logbook p.42`, certified by `Atelier X – CRS 1234`.
4. **Save**.

**Result**: the 100 h check of F-HDMX is now due at 1,290 FH (1,190 + 100), i.e. 40 FH remaining.

## 4. Taking over the configuration (installed components)

The component first enters stock with its certificate, then the CAMO attaches it to the aircraft:

1. Account **`magasin`** → menu **Receipt**: P/N `DEMO-ARR2D-0001` (RTM322), S/N `DEMO-E2X99`, quantity 1, location `MAG-PRINC`, condition "Overhauled", TSN `1250`, CSN `3800`, TSO `1250`, CSO `3800`. Certificate: EASA Form 1, no. `F1-TEST-01`, issuer `Atelier moteur agréé`, today's date, status "Overhauled". Tick the 3 receiving inspections → **Save**.
2. Account **`camo`** → open F-HDMX → **Configuration take-over**: component `DEMO-E2X99`, position `MOT 1`, date = entry into service, reference `Relevé de configuration d'entrée en flotte` → **Save**.

**Result**: the engine appears in "Installed configuration" with its remaining TBO (4,000 − 1,250 = 2,750 FH). The component task **N90-72-500** (engine borescope inspection) appears in the due items, "Overdue" until its last accomplishment is taken over. Do it as in step 3, choosing the component `DEMO-E2X99` and its counters (TSN/CSN) at the date of the last borescope inspection.

> The configuration take-over is used only for entry into the fleet. In operation, every component movement goes through a task card (tutorial 14).
