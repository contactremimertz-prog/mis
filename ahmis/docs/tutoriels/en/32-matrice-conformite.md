# 32. Regulatory compliance matrix

This matrix links the main EASA requirements to AHMIS functions. It serves as the basis for the presentation file to the authority.

> **Important**: software is not "compliant" on its own. It is the organisation (CAMO, Part-145) that demonstrates its compliance to the authority (in France, the DSAC). It does so by describing the tool and its use in its procedures (CAME, MOE), by validating it and by auditing it. The "To be done by the organisation" column lists what remains your responsibility. The regulatory references below are indicative: check them in the texts in force.

## Airworthiness (Part-CAMO / Part-M)

| Requirement | AHMIS function | Coverage | To be done by the organisation |
|---|---|---|---|
| Approved maintenance programme | Programme by type, FH/cycles/calendar intervals, thresholds, tolerances, effectivity, AMP revision, revision history | ✅ | Enter the approved programme (MSM/MPD), check of the entry by a second person |
| Non-cumulative tolerances | Accomplishment within tolerance: next due item counted from the theoretical limit; outside tolerance traced; tolerance prohibited on ALS/CMR, referenced on AD (tutorial 25) | ✅ | Define the tolerances permitted in the programme |
| Periodic programme review (M.A.302(g)) | Review by type at least every 12 months, reliability review and new instructions, approved amendment, dashboard alert, history (tutorial 27) | ✅ | Review and indirect approval procedure in the CAME |
| Monitoring of airworthiness directives | AD/SB register, assessment per aircraft with justification, follow-up tasks, compliance time from the effective date, status updated on accomplishment | ✅ | AD monitoring (EASA, FAA, manufacturer) and entry |
| Airworthiness limitations, LLP | Life limits FH/cycles/days, "back-to-birth" traceability, LLP due items, installation refused at limit | ✅ | Take over the complete LLP history on entry into the fleet |
| Potentials (TBO) | TBO due items, TSO/CSO counters | ✅ | — |
| Airworthiness records | Hours/cycles traced, accomplishments, configuration, components, CRS, no deletion possible | ✅ | Backups |
| Retention periods (M.A.305(h), 145.A.55(c)) | Retention rules by type of record, aircraft withdrawal date, report of expired records, mass deletion blocked until the period is reached (tutorial 30) | ✅ | Documented archiving / purge procedure |
| Status of modifications and repairs (M.A.305) | Dedicated register: classification, approval basis, embodiment, ICA and integration into the programme, weighing and flight manual, alerts in the due items (tutorial 26) | ✅ | Classification and approval of modifications (Part-21) |
| Transfer of records (M.A.307) | Complete records archive (HTML summary, JSON, CSV, SHA-256 manifest), acknowledgement of receipt, integrity check of received records (tutorial 30) | ✅ | Transfer procedure with the new organisation |
| Airworthiness review / ARC | ARC register, expiry alert, summary aircraft record | ✅ | Review procedure, authorised ARS staff |
| Deferred defects | Signed MEL/CDL deferral, limits, integrated into the due items | ✅ | Enter the operator's MEL |
| Deferral extension (RIE) | Single extension, categories B and C, approved and signed by the CAMO before the limit, duration ≤ initial interval, authority informed (tutorial 31) | ✅ | RIE procedure accepted by the authority |

## Maintenance (Part-145)

| Requirement | AHMIS function | Coverage | To be done by the organisation |
|---|---|---|---|
| Maintenance data | Task cards generated from the programme, with steps and references | ✅ | Technical content from licensed manufacturer data |
| Work cards, signature of each step | Individually signed steps, recorded values, N/A | ✅ | — |
| Certifying staff and authorisations | Part-66 licence, authorisations by type, category and validity, suspension, check at every signature | ✅ | Management of authorisations (MOE procedure) |
| Independent inspection (critical tasks) | Mandatory second signature by another certifying person | ✅ | Identify the critical tasks in the programme |
| Certificate of release to service | Electronically signed CRS, automatic blocks, mention of deferrals, category C for a heavy check | ✅ | CRS text to be aligned with the MOE |
| Calibrated tooling | Calibration, check-out prohibited if expired, traceability of uses | ✅ | — |
| Acceptance of components | Receipt with certificate, receiving inspection, automatic quarantine, suspected parts | ✅ | — |
| Article classes (145.A.42(a)) | Class by P/N (component, standard part, material, consumable); Form 1 required for a component, standard required for a standard part or a material (tutorial 31) | ✅ | Classify the P/N catalogue |
| Non-recoverable parts (145.A.42(d)) | Signed scrapping with mutilation and witness, final status (tutorial 31) | ✅ | Mutilation procedure |
| Recent experience (145.A.35) | 6 months out of 24 calculated from AHMIS signatures and declared experience, blocking for certifying staff (tutorial 28) | ✅ | Declare the prior experience of new arrivals |
| Human factors, training | Training by category, mandatory categories blocking (human factors, continuation training), other expirations flagged | ✅ | Continuation training programme |
| Occurrence reporting (376/2014, 145.A.60) | Reporting by all staff, confidentiality, 72 h deadline, 30-day follow-up, design holder, closure, alerts (tutorial 29) | ✅ | Notification to the authority (ECCAIRS) and analysis; AHMIS does not transmit automatically |

## IT systems, electronic records, information security

| Requirement | AHMIS function | Coverage | To be done by the organisation |
|---|---|---|---|
| Integrity and traceability of records | Write-only audit trail, field by field, deletion prohibited | ✅ | — |
| Electronic signature | Password re-entry, identity and licence, timestamp, SHA-256 digest, non-modifiable | ✅ | Have the signature method accepted by the authority |
| Access control | Roles by area + individual authorisations | ✅ | Named accounts, periodic review of rights |
| Information security (Part-IS) | Technical basis: authentication, traceability | ⚠️ partial | Risk analysis, secure hosting (HTTPS), backups, continuity plan, incident management |
| Software validation | 89 automated tests on the critical rules | ⚠️ partial | Formal validation plan, acceptance by airworthiness experts, version management |

## Known limitations of this version

- **A single cycle unit** per aircraft (cycles or landings). Specific engine cycles (NG/NF, starts) are not tracked separately.
- No flight-by-flight entry: hours are entered per report (daily or per flight).
- No automatic import of manufacturer data (MSM, MRI, IPC) or of ADs: entry is manual.
- Category qualification (A/B1/B2) of the task card: indicative, not blocking for execution. The authorisation on the type and the certification rights, on the other hand, are blocking.
- No financial module (costs, invoicing, supplier purchasing).
- Demo data in French only (the interface and tutorials are also available in English, Spanish and German).

These points are possible areas for development, to be prioritised according to your needs.
