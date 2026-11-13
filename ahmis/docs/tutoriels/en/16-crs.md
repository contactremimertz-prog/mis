# 16. Certificate of release to service (CRS)

**Accounts: `b1`, `b2`, `planif`**

The CRS is signed at **work package** level, when all the work is complete.

## 1. Seeing what blocks

Open the F-HDMD WP ("100 h check + engine borescope inspection") → **Certificate of release to service** frame. AHMIS lists everything that prevents the CRS, for example:

- task card not closed (and its status);
- tooling not returned;
- part reserved but neither installed nor returned to the stores.

The **Sign the CRS** button stays greyed out as long as the list is not empty.

## 2. Completing the work

If you have followed tutorials 12 to 14, at most the following remains:

- **Battery capacity check** (B2 qualification): account `b2` → start, sign the 3 steps, sign the work;
- any task card you may have created as an exercise: close it, or **defer it** with a reason (a deferral does not prevent the CRS, it is mentioned in it).

## 3. Signing the CRS

Account `b1` → WP → password → **Sign the CRS**.

**Result**:

- the WP changes to **Released to service (CRS signed)** and becomes **non-modifiable**;
- F-HDMD returns to **In service**;
- the CRS statement is recorded with the name, licence, date, organisation's approval reference, aircraft counters, deferred work and current deferred defects;
- **Print the work package** shows the CRS with its SHA-256 digest reference.

## Rules applied

| Rule | Detail |
|---|---|
| Valid certifying authorisation on the type | B1, B2, B3 or C, not suspended, within its dates |
| Valid Part-66 licence | Validity date not exceeded |
| Heavy check ("Heavy check" as WP type) | CRS reserved to **category C** (try with `b1` then `certc`) |
| Non-certifying mechanic | Access refused (403) |
