# 28. Recent experience and mandatory training

**Accounts: `qualite`, `b1`**

145.A.35 requires certifying staff to have at least **6 months of maintenance experience** within the **last 24 months**, as well as continuation training. Human factors training is required of all staff. AHMIS blocks signing if any of these conditions is missing.

## 1. The "Ability to sign" panel

Account `qualite` → **Staff & authorisations** → **Claire DUBOIS**. The panel shows:

- **Recent experience**: number of months, within the last 24, with at least one task card performed or inspected in AHMIS, or covered by a declared experience record. At least 6 are required;
- **Training (all staff)** and **Training (certifying)**: up to date, or the list of what is missing;
- for each authorised type: "can sign", or the reasons for the block.

## 2. Declaring experience outside AHMIS

For a person arriving from another organisation, their past experience is not in AHMIS. **Declared experience records** frame:

1. From `01/01/2026` to `30/06/2026`, organisation `Atelier précédent (DEMO)`, work `Entretien en ligne NH90`, supporting document `Attestation employeur`.
2. **Add**: the months covered count towards recent experience.

An experience in the future, or one whose end precedes its start, is refused.

## 3. Mandatory training

Each training has a **category**: human factors, continuation training (145.A.35), EWIS, fuel tank safety, type training, security, other. By default:

| Staff | Categories required |
|---|---|
| All staff | Human factors |
| Certifying staff | Human factors, continuation training |

Only these categories block. Other expired training is flagged in red without blocking.

## 4. Checking the block

1. Account `qualite` → **Claire DUBOIS** record → training "Formation continue 145.A.35": note its expiry date.
2. To test, add a test staff record with a certifying NH90 authorisation but **without** continuation training.
3. Link it to an account, then open an NH90 task card with that account: the "Signing impossible" frame lists "mandatory training missing or expired: Continuation training (145.A.35)".

## 5. Settings

In the configuration file:

| Variable | Default | Role |
|---|---|---|
| `AHMIS_RECENCY_ENFORCE` | `1` | `0` disables the recent experience check |
| `AHMIS_RECENCY_MONTHS` | `6` | Months of experience required |
| `AHMIS_RECENCY_WINDOW_MONTHS` | `24` | Sliding window |
| `AHMIS_TRAINING_REQUIRED_ALL` | `human_factors` | Categories required of everyone |
| `AHMIS_TRAINING_REQUIRED_CERTIFYING` | `human_factors,continuation` | Categories required of certifying staff |
