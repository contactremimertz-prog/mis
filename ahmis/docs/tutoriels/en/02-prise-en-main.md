# 2. Getting started: roles, navigation, electronic signature

**Account: `admin`, then `meca`**

## The dashboard

1. Log in with `admin`.
2. The dashboard displays 8 indicators. Each one is clickable and opens the corresponding filtered list:
    - overdue (including within tolerance) and to-plan due items;
    - open defects and out-of-limit deferrals;
    - AD/SB to be assessed;
    - active work packages and task cards awaiting inspection;
    - part requests, quarantine, tooling out of calibration and authorisations about to expire.
3. The **Fleet** table gives, for each aircraft, its counters, ARC validity and number of due items.

**To check**: the F-HDMB line shows overdue due items; F-HDMD is "In maintenance".

## Navigation

- The left-hand menu is organised by area: CAMO, Part-145, Logistics, Quality, Help.
- The **global search** (at the top) finds a registration, a P/N, an S/N, a WP, a task card, an AD. Try `DEMO-S3502`: you go straight to the record of the F-HDMB rotor hub.
- Each list has a search and filters.

## Roles

1. Log out and log in again with `meca`.
2. Open **Fleet**, then F-HDMA: the record can be viewed, but the "Edit" and "Configuration take-over" buttons no longer appear.
3. Type `/flotte/aeronefs/1/modifier/` in the address bar: AHMIS answers "403 Forbidden".

Roles limit access to screens. Tutorial 21 shows the second barrier: individual signing authorisations.

## The electronic signature

Every regulatory action (task card step, performance, inspection, defect deferral, CRS) requires you to **re-enter your password**. AHMIS then records:

- the identity and licence of the signatory;
- the timestamp;
- the signed statement;
- a **SHA-256 digest**, which makes it possible to detect any later alteration ("✓ intact" badge).

A signature can be neither modified nor deleted. A wrong password refuses the signature.

## Nothing is erased

Airworthiness records cannot be deleted, even by the administrator. Statuses are used instead ("cancelled", "withdrawn", "scrapped"). Every change is traced field by field in the **audit trail** (tutorial 22).
