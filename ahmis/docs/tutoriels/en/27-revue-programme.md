# 27. Annual review of the maintenance programme

**Account: `camo`**

M.A.302(g) requires each maintenance programme to be reviewed periodically (at least once a year) and amended if necessary: effectiveness (reliability, repetitive defects), new instructions (MSM/MPD revisions, AD, SB, ICA of modifications).

## 1. Status of the reviews

The **dashboard** displays a "Maintenance programme review" banner for each operated type whose review is missing, overdue or due within 30 days. Menu **Programme review**:

| Type | Demo situation |
|---|---|
| ATR72-600 | No review recorded |
| Super Puma | Review overdue (last review 13 months ago) |
| H135 | Review due within 30 days |
| NH90, H145 | Up to date (NH90 amended to "DEMO rev. 4") |

The **aircraft type** record (Fleet → Types & configuration) also shows the status and the latest reviews.

## 2. Recording a review without change

1. **Super Puma** line → **New review**. The programme and the reviewed revision are taken from the previous review.
2. Performed by `Julien MOREAU (CAMO)`. Tick **both** review boxes (reliability and new instructions).
3. Findings `Aucun défaut répétitif, pas de nouvelle révision MSM`; result "Programme confirmed without change" → **Save**.

**Result**: Super Puma changes to "Up to date", next review in 12 months.

## 3. Recording an amendment

1. **ATR72-600** line → **New review**: programme `AMP-ATR72-DEMO`, reviewed revision `DEMO rév. 3`.
2. Result "Programme amended", new revision `DEMO rév. 4`, changes `Ajout des ICA de la modification MOD-...`.
3. Approval method "Indirect approval", reference `PAI-2026-020`, date → **Save**.

**Result**: all the active tasks of the type change to "AMP revision: DEMO rév. 4".

## 4. Checks

- Incomplete review (reliability or instructions not reviewed): refused.
- Amendment without a new revision, with an identical revision, without a description of the changes or without approval: refused.
- Next review set beyond 12 months: refused. The interval is set with `AHMIS_AMP_REVIEW_MONTHS`.
- Review dated in the future: refused.
