# 24. Complete scenario: from the overdue AD to the CRS (F-HDMB)

This scenario chains the roles together on a realistic case. Duration: about 20 minutes. Start from a reset demo.

**Situation**: on NH90 F-HDMB, AD `DEMO-AD-2026-0101` (BTP suspension bars) is **overdue** and the 100 h check is **within tolerance**.

## Step 1 – CAMO: noting and grounding (`camo`)

1. Dashboard → F-HDMB line → overdue due items.
2. **Due items**, filter F-HDMB: note the overdue AD and the 100 h check within tolerance.
3. An overdue AD prohibits flight: open F-HDMB → **Edit** → status **AOG (grounded)** → **Save**. The change is traced in the history.

## Step 2 – Planning (`planif`)

1. **Due items**, filter F-HDMB.
2. Tick the AD, the 100 h check and the lubrication `N90-62-050`.
3. Work package: the existing WP **100 h check** → **Create the task cards**.
4. On the WP → **Edit**: start today, end tomorrow, status "Planned".

## Step 3 – Performing the check (`meca`)

1. Task card **100 h / 12 months check** → **Start**.
2. Sign the 6 steps (password each time).
3. Check out tool `TENS-01` (tension meter), then return it.
4. Work report `Visite 100 h effectuée, RAS`, 7 man-hours → **Sign the work**: the task card is closed.
5. Do the same for the **lubrication**.

## Step 4 – Performing the AD (`b1`)

1. Task card **BTP suspension bars inspection (AD)** → **Start**, then sign the 4 steps.
2. During the inspection, an anomaly: **Report a finding** frame, `Trace de frottement sur barre avant gauche, dans les tolérances du manuel`. A defect and a rectification task card are created.
3. Go back to the AD task card → work report `Inspection conforme à l'AD, constatation traitée sur task card dédiée` → **Sign the work**. It changes to "awaiting inspection": the task is critical.

## Step 5 – Finding (`b1`)

Open the rectification task card → **Start** → work report `Mesure de la trace : conforme, protection appliquée` → **Sign the work**. The defect is **rectified**.

## Step 6 – Independent inspection (`certc`)

AD task card → **Sign the inspection** (remarks `Conforme`). It is closed.

**To check** (account `camo`):

- **AD / SB** → `DEMO-AD-2026-0101` → F-HDMB: status **"Applicable – repetitive in progress"**, with the compliance date and counters;
- F-HDMB **Due items**: the AD is "OK", next limit in 110 FH; the 100 h check is "OK".

## Step 7 – CRS (`b1`)

WP → CRS frame: no more blocking items → password → **Sign the CRS**. The WP is **Released to service** and locked.

## Step 8 – Return to service (`camo`)

The CRS automatically put F-HDMB back **In service** (it does so for an aircraft "In maintenance" or "AOG"). Check the **dashboard**: F-HDMB no longer has an overdue due item, but the rotor hub (LLP) remains to be planned.

## Step 9 – Quality control (`qualite`)

- **Electronic signatures**: all the signatures of the scenario, each "✓ intact".
- **Audit trail**, search `F-HDMB`: the grounding, the creation of the WP, the task cards, the statuses, etc.
- **Print the work package**: the complete paper file with the CRS.

Well done, you have gone through the entire chain CAMO → Part-145 → logistics → quality.
