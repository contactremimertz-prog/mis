# 30. Records retention and transfer

**Accounts: `qualite`, `camo`**

## Part A: records retention

Records have minimum retention periods:

| Records | Minimum period | Reference |
|---|---|---|
| Work packages, task cards, CRS, defects | 36 months after release to service | 145.A.55(c), M.A.305(h) |
| Task accomplishments | 36 months, and until replaced by a more recent accomplishment | M.A.305(h) |
| Total times, AD status, LLP, modifications, installations / removals | 12 months after permanent withdrawal of the aircraft (or component) | M.A.305(h)(1) |
| Staff record | 3 years after leaving | 145.A.35(j) |
| ARC, programme reviews, calibrations, occurrence reports | 36 months | CAMO.A.220, 145.A.55 |

**AHMIS never deletes anything automatically.** It refuses any individual deletion, and also refuses a mass deletion (administration, script) of a record still subject to a retention obligation.

### 1. Retention report

Account `qualite` → menu **Records retention**. For each type of record, the report displays the total, then three counts:

- **no deadline**: to be retained, for example for an aircraft still in operation;
- **in progress**: minimum period not reached;
- **expired**: can be archived, on a documented decision in accordance with the MOE or CAME.

A CSV export is available per line. In the demo, the following have expired: the helicopter **F-HDMZ** (withdrawn 20 months ago) and its flight hours, and the former employee **Paul ANCIEN** (left 4 years ago).

### 2. Withdrawing an aircraft from service

Aircraft record → **Edit** → status "Withdrawn" and **permanently withdrawn from service on**. The date is mandatory for a withdrawn aircraft, and prohibited otherwise. It starts the 12-month period. The aircraft leaves the due items and the dashboard, and its record displays the end-of-retention date.

For a staff departure: staff record → untick "active" and fill in **left the organisation on**.

## Part B: transfer of an aircraft's records (M.A.307)

When an aircraft changes CAMO or owner, its airworthiness records are transferred to the new organisation.

### 3. Outgoing transfer

1. Account `camo` → **F-HDMA** record → **Export the records**.
2. Direction "Outgoing transfer", organisation `CAMO Héli Nord (DEMO)`, approval `FR.CAMO.0999`, reason `Changement de gestionnaire de navigabilité` → **Save**.

**Result**: AHMIS generates the archive `dossier-F-HDMA-TR-....zip` and retains it with its SHA-256 digest:

- `synthese.html`: printable airworthiness status (total times, due items, components, LLP and TBO, AD, modifications, deferred defects);
- `dossier.json` and `csv/`: all the data (hours, accomplishments, installations / removals, certificates, work packages, task cards, signatures with their digest);
- `manifest.json`: digest of each file.

When the new organisation confirms receipt, fill in **Record the acknowledgement of receipt** on the transfer record. The demo contains the transfer of F-HDMZ to the airframe's buyer, already acknowledged.

### 4. Incoming transfer

Menu **Records transfers** → **+ Create** → direction "Incoming transfer", then attach the archive received. AHMIS checks the digests in the manifest:

- archive intact: green banner;
- file modified, missing or added, or records of another MSN: **ANOMALY** banner with details.

The data are then taken over by manual entry (tutorial 3).

Transfer archives can be downloaded only with the "view transfers" right (CAMO, Quality), never through the generic attachment link.
