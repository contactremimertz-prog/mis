# 10. Airworthiness review (ARC)

**Account: `camo`**

The ARC (airworthiness review certificate) is valid for one year. AHMIS tracks its due date like a limit.

## Starting situation

F-HDME (Super Puma) has an ARC that expires in 20 days: it appears as "To plan" in the due items and in orange on the aircraft record.

## Recording a new review

1. Open **F-HDME** → "ARC valid until" card → **Record a review**.
2. Fill in:
    - type: ARC issue;
    - ARC no. `ARC-DEMO-1601-B`;
    - review date: today;
    - valid until: in 1 year minus 1 day;
    - review staff: `Julien MOREAU (ARS)`;
    - tick "physical survey performed".
3. **Save**.

**Result**: the expiry date of F-HDME is updated and the ARC due item returns to "OK".

## Checks

- An expiry date earlier than the review date is refused.
- A validity of more than one year is refused.

## Preparing a review with AHMIS

For the airworthiness review, the aircraft record gathers what the ARS must verify: hours and cycles, due items, status of directives ("See all"), component configuration and potentials, current defects, latest work packages and CRS.
