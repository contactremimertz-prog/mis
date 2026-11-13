# 29. Occurrence reports (Regulation 376/2014)

**Accounts: `meca`, `qualite`, `camo`**

Any occurrence that endangers or could endanger safety must be notified to the authority **within 72 hours** of the organisation becoming aware of it (Regulation (EU) 376/2014, 145.A.60, CAMO.A.160). A follow-up analysis is submitted **within 30 days**. The design holder is informed if the condition of the aircraft or of a component is involved.

AHMIS applies **just culture**: all staff can report, but only Quality and the CAMO see all the reports. The identity of a confidential reporter is visible only to the quality manager.

## 1. Reporting (all staff)

1. Account `meca` → menu **Occurrence reports** → **+ Create**. Another route: **Report an occurrence** button on a defect or a task card, which pre-fills the form.
2. Title `Lampe torche retrouvée en zone moteur`, category "Foreign object (FOD) / item left behind", phase "In maintenance", aircraft `F-HDMD`.
3. Dates of the occurrence and of becoming aware: now. Factual description, immediate measures `Zone inspectée, inventaire outillage`. Tick **confidential report** → **Save**.

**Result**: the report `OCC-YYYY-NNNN` is in **Draft**, with the 72 h deadline displayed. The mechanic sees only their own reports.

## 2. Monitoring deadlines (Quality)

Account `qualite` → **dashboard**: banner "Occurrence reports: N open, of which N to be notified". It turns red if a deadline is exceeded. The demo contains:

| No. | Situation |
|---|---|
| Rudder pedal vibrations (F-HDMD) | Draft: about 20 h left out of 72 |
| Nut locking device not fitted (F-HDMB) | Notified 40 days ago: **30-day follow-up late** |
| Part without release certificate | Closed |

On the confidential report, the reporter (Sophie LAMBERT) is visible to `qualite`, but displayed as "Confidential" to `camo`.

## 3. Notifying, following up, closing

Account `qualite` → open the report → **Process**:

1. **Notification**: status "Notified to the authority", authority `DSAC / ECCAIRS 2`, ECCAIRS reference, notification date. Beyond 72 h, the **reason for delay** is mandatory. Tick "design holder informed" if necessary.
2. **Follow-up**: status "Follow-up sent", analysis (causes, human factors), date sent.
3. **Closure**: corrective actions and closure date.

An occurrence not on the list of Regulation 2015/1018 can be "Classified as not reportable", with a justification. A serious incident or an accident cannot be.

## 4. Retention

Closed reports are retained for at least 36 months (tutorial 30). They are not included in aircraft transfer records.
