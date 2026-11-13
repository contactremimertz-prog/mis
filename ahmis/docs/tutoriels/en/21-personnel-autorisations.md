# 21. Staff, licences and authorisations

**Account: `qualite`**

AHMIS distinguishes two things:

- the **user account**, with its role, which determines the screens that can be accessed;
- the **staff record**, with its Part-66 licence and authorisations, which determines what the person can **sign**.

## 1. Viewing a record

Menu **Staff & authorisations** → **Claire DUBOIS**:

- licence `FR.66.DEMO.0002`, categories B1.3 / B1.1, validity date;
- Part-145 organisation **authorisations**: no., type, category, certifying or not, scope, validity, status;
- **training** with limited validity: human factors, EWIS, etc.;
- her latest signed work and inspections.

**To check**: her **Super Puma** authorisation expires in 45 days. It is counted in the "authorisation(s) expiring within 60 d" dashboard indicator.

## 2. Suspending an authorisation

1. Add an authorisation to Claire DUBOIS (form at the bottom of the page): no. `AUT-TEST`, type `ATR72-600`, category B2, certifying, dates from today to +1 year, tick **suspended** → **Add**. It appears as "Suspended".
2. For a real suspension, edit the existing authorisation from the administration (account `admin` → Administration → Authorisations) and tick "suspended". The person can then no longer sign on this type, immediately.

## 3. What each signature checks

| Action | Requirement |
|---|---|
| Start, sign a step, sign the work | Valid authorisation (any category) on the type + mandatory training of all staff up to date |
| Independent inspection | Valid **certifying** authorisation + valid licence + person different from the performer + certifying staff training + recent experience |
| Defect deferral | Valid certifying authorisation + training + recent experience |
| CRS | Certifying authorisation B1/B2/B3/C (C only for a heavy check) + valid licence + training + recent experience |

All the reasons that prevent a signature are listed at once, on the task card and on the staff record (tutorial 28).

## 4. Creating a person

1. Account `admin` → **Administration** → Users → create the account and add it to the desired group ("Mechanic", "Certifying"…).
2. Account `qualite` → **Staff** → **+ Create**: link the account, enter staff number, name, stamp, licence.
3. Add their authorisations and training.

> Only training in the **mandatory categories** blocks signing (by default: human factors for everyone, plus continuation training for certifying staff). Another expired training, such as "Security / restricted areas" for Lucas MARTIN, is flagged in red without blocking. Tutorial 28 details recent experience and mandatory training.
