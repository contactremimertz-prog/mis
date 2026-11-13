# 0. Introducing AHMIS

AHMIS (**A**ircraft & **H**elicopter **M**aintenance **I**nformation **S**ystem) covers three areas of activity on a single database:

| Module | For whom | Main functions |
|---|---|---|
| **Airworthiness (CAMO)** | CAMO engineer | Fleet, configuration, flight hours, maintenance programme and its annual review, AD/SB, modifications and repairs, LLP/TBO, due items, forecast, ARC, deferral extension, records transfer |
| **Maintenance (Part-145)** | Planner, mechanics, certifying staff | Planning, work packages, task cards, signatures, independent inspection, defects/MEL, component change, CRS, blocking recent experience and training, occurrence reports |
| **Logistics** | Storekeeper | Receipt with Form 1 according to the article class, stock, expiry, quarantine, scrapping and mutilation, part requests, tooling and calibration |
| **Quality** | Quality manager | Audit trail, electronic signatures, staff and authorisations, occurrence reports, records retention |

## The demonstration data

The demo loads a mixed fleet of 6 operated aircraft, mostly **Airbus Helicopters**, plus one helicopter withdrawn from service:

| Reg. | Type | Starting situation (for the tutorials) |
|---|---|---|
| F-HDMA | NH90 | 100 h check and AD to be planned, BTP close to its TBO |
| F-HDMB | NH90 | **AD overdue**, 100 h check within tolerance, rotor hub (LLP) close to its limit, empty planned WP |
| F-HDMC | H135 (HEMS) | MEL cat. C deferred defect, ASB open, rotor hub (LLP) tracked in cycles |
| F-HDMD | H145 (HEMS) | **In maintenance**: work package in progress with task cards at every stage |
| F-HDME | Super Puma | ARC expiring in 20 days |
| F-HDMF | ATR 72-600 | AD to be assessed, calendar task overdue |
| F-HDMZ | NH90 | **Withdrawn from service** 20 months ago, records transferred to the buyer (tutorial 30) |

It also contains: programme reviews in every state (tutorial 27), three occurrence reports (tutorial 29), one scrapped part (tutorial 31) and a former employee whose file has reached the end of its retention period (tutorial 30).

> ⚠️ **All references (tasks, P/N, AD, intervals, limits) are fictitious** and prefixed "DEMO". They are used only to illustrate the software. In operation, the data come from the manufacturer's documents (MSM, MRI, ALS, etc.) and from the authorities.

## Demonstration accounts

Common password: **`Ahmis2026!`**

| Username | Person | Role | Can sign |
|---|---|---|---|
| `admin` | — | Administrator (all rights) | No (no staff record) |
| `camo` | Julien MOREAU | CAMO engineer | — |
| `planif` | Nadia ROUX | Planner | — |
| `meca` | Lucas MARTIN | Non-certifying mechanic | Performance (helicopters) |
| `b1` | Claire DUBOIS | B1 certifying staff | Performance, inspection, CRS, defect deferral |
| `b2` | Karim BENALI | B2 certifying staff | Same (helicopters) |
| `certc` | Sophie LAMBERT | C certifying staff | Same + heavy check CRS |
| `magasin` | Thomas PETIT | Storekeeper | — |
| `qualite` | Isabelle GARNIER | Quality manager | — |

Rights of **access to screens** depend on the role. **Signing** rights also depend on the person's individual authorisations (aircraft type, category, validity): AHMIS checks them at every signature.

## Recommended order of the tutorials

1. Installation (tutorial 1), then getting started (2).
2. CAMO side: 3 to 10.
3. Workshop side: 11 to 16.
4. Stores side: 17 to 20.
5. Quality and technical: 21 to 23.
6. **Tutorial 24** chains everything together in a complete scenario, from the due item to the CRS.
7. Regulatory business rules: **25 to 31** (tolerances, modifications, programme review, recent experience, occurrence reports, retention and transfer, deferral extension, scrapping, article classes).
8. The **compliance matrix** (32) links each EASA requirement to AHMIS functions.

Tip: to start again from scratch at any time, run `reinitialiser_demo` (see tutorial 1).
