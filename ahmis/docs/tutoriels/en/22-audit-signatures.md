# 22. Audit trail and electronic signatures

**Account: `qualite`**

## Audit trail

Menu **Audit trail**: every creation, modification or technical deletion is recorded with:

- the timestamp and the user;
- the record concerned;
- **each modified field**, with its old and new value.

The trail is **write-only**: no entry can be modified or deleted, even by the administrator.

**Exercises**

1. Search `F-HDMA`: all the operations on this aircraft, including counter increments.
2. Filter "Record type = maintenance task": the history of programme revisions.
3. On a record (aircraft, component, task card, WP, defect), the **History** button shows the modifications **and** the signatures of that record.

## Electronic signatures

Menu **Electronic signatures**: all the signatures, filterable by action (performance, inspection, CRS, deferral, etc.).

Each signature contains the name, the licence at the time of signing, the signed statement, the timestamp and a **SHA-256 digest** calculated over the whole.

The **"✓ intact"** badge means that the recalculated digest matches. If data were modified directly in the database, outside AHMIS, the badge would become **"⚠ altered"**. The automated test `test_signature_is_immutable_and_tamper_evident` demonstrates this.

## What is retained

- No airworthiness record can be deleted: aircraft, components, tasks, accomplishments, task cards, WPs, defects, certificates, flight hours entries, etc.
- Statuses are used: cancelled, withdrawn, scrapped, inactive.
- The regulatory retention periods are a matter for your procedures (CAME / MOE) and for the database backup (tutorial 23).
