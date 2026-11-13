# 5. Components, life-limited parts (LLP) and TBO

**Account: `camo`**

## Article references (P/N)

Menu **P/N references** → click `DEMO-350STR-01` (NH90 main rotor hub). A reference carries:

- serial number tracking (mandatory for an LLP or a part with a TBO);
- the **life limits** (LLP), since new: hours, cycles and/or days;
- the **TBO**, potential between overhauls: hours, cycles and/or days;
- the applicable aircraft types (installation on another type is refused);
- the interchangeable P/Ns (accepted when a part is requested).

AHMIS refuses an LLP without a limit, and an LLP or a part with a TBO that is not serialised.

## Component record: the F-HDMB rotor hub

1. Global search: `DEMO-S3502`.
2. The record displays:
    - the TSN / CSN / TSO / CSO counters;
    - **Remaining potential and life limits**: limit, consumed, remaining, and a bar that turns orange at 90%;
    - the release certificates;
    - the **"back-to-birth" traceability**: every installation (aircraft, position, counters at installation and removal, reason, task card).

**To check**: about 40 FH remain on the 5,000 FH limit. In **Due items**, the "LLP" line of F-HDMB is "To plan".

## Reading an aircraft's configuration

Open F-HDMA, **Installed configuration** section: for each position (MOT 1, MOT 2, BTP, BTA, MRH, PALE 1-4…), the component, its counters and what remains on each limit.

## LLP and TBO in the due items

AHMIS automatically generates a due item:

- **LLP** for every installed life-limited part (first criterion reached among hours, cycles and calendar);
- **TBO** for every part with a potential.

They appear in the due items, the forecast and the planning, and can be added to a work package: a "removal/installation" task card is then generated.

## A part at its limit is unusable

A part that has reached a limit can be neither installed, nor issued, nor returned to "serviceable". The automated test `test_expired_life_part_refused` checks this.
