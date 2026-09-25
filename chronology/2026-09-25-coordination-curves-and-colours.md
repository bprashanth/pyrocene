# Prelude: nursery turning points, shared work and consistent colours

Rollback tag: `stage4-before-coordination-curves-20260925` at `64866ae`.
User narrative drafts and `stage4/v2_recap.md` remain outside this checkpoint.

## What changed

Explanations describe the cause of a change directly. Returning clearance earns
credits while damaging native growth. Recovering canopy raises health while
continued care uses money. The all-A plan explicitly warns that untreated fuel
in C still exposes its recovery to fire. The graphs remain before-fire comparisons.

All plan labels now read **Remove X, restore Y, livelihood Z**. In particular,
Remove C, restore C, coffee B explains how the first clearance contributes to
planting and coffee investment, then recovery in C shelters B. This describes
the initial work order; it does not add a sequential cash-flow simulator or
promise that the first removal funds the whole investment. Debt remains possible.

## Projection accounting

The previous flat nursery line showed accumulated earnings, not recurring
income. However, ending all tree-care charges at year four made later maintenance
invisible. Tree care now continues: 0.4 credits/year through year four, followed
by an annual rate easing from 0.3 to 0.1 by year ten. Early all-A shared-care
savings remain unchanged. This costs another 1.2 credits over years four to ten.

Matched seed purchases still retain 4 credits within the group during the first
two years. Later replacement orders are internal transfers, not free new group
revenue. Hence the all-A group curve rises during the first supply, then declines
gently while tending continues. Prelude II separately shows annual community
income with shrinking replacement orders. Do not add that income to group totals.

Coffee waits three years and then ramps up smoothly. Prelude II's annual harvest
and Prelude I/III's accumulated harvest now use the same helper. The annual rate
approaches 4.3 times the shelter score with a two-year timescale; its integral
supplies cumulative income. Coffee care remains 0.3/year. This replaces two
different coffee-yield assumptions across the pages. These are fictional game
coefficients, not calibrated agronomic or economic measurements.

Example net group earnings, excluding the grant:

| Plan (remove / restore / community) | Start | Year 2 | Year 5 | Year 10 | Health change at 10 |
| --- | ---: | ---: | ---: | ---: | ---: |
| A / A / nursery A | 3.0 | 6.8 | 6.3 | 5.4 | +17.0 |
| C / C / coffee B | -6.0 | -7.4 | -6.7 | 6.7 | +13.0 |
| A / C / coffee B | -3.0 | -4.4 | -3.7 | 17.5 | +7.5 |

All-A remains healthiest before fire. C/C/coffee-B balances health and later
earnings. Separate recurring clearance in A earns more but loses native growth.
Health weights, actual upfront room costs, grant, land-use conflicts, wildfire,
point clouds and the single-player game rules are unchanged. Projected earnings
in the shared flow and Prelude do change, as described above.

## Colour semantics

- Green: matched removal/restoration plus a matching nursery or sheltered coffee.
- Blue: some shared work, such as matching nursery/restoration with removal elsewhere.
- Pink: recurring removal separate from planting and livelihood support.

This replaces colouring by the count of field sites. The site count remains
separate text. Categories derive from the plan, not its year or an arbitrary
health threshold. Both graphs share the classifier. A yellow ring marks the
committed plan in Prelude I and the followed path's three anchors in Prelude III.

Translucent overlapping points previously washed out colours. Points now have
opaque fills; the followed plan is drawn last at Start, Year 5 and Year 10 in its
same category colour, with the same-coloured connecting path. Numbered annotation
badges sit beside the path so they cannot replace its time-anchor colours.

## Verification

Browser skill discovery reported no connected browser, so the repo's Playwright
fallback was used. Visible UI checks select plans, click turning points, rotate
the graph, use keyboard navigation and check the underlying room stays unchanged.
Regression assertions cover each selected anchor's colour and opacity, including
the reported C/B/nursery-A pink path, plus background colours at all three years.

Screenshots inspected at 1280x800 under
`/mnt/seagate/models/pyrocene/stage4/qa-cooperation-integrated/`:

- `recap-tradeoff-AAA.png`
- `recap-space-CCB.png`
- `recap-space-CBA.png`
- `prelude-nursery-order-filled.png`

No new endpoints or static runtime files. Existing `run.sh` serves these changes;
an already running server needs only a page refresh. Large screenshots stay out
of git.

Final checks passed: 24 JS model tests, 21 main browser tests (including
WebGL-disabled mode), and 19 delivery/store/archived-room tests. The focused
Prelude interaction test also passed against live port 8024 without restarting
the server. Its screenshots carry the `live-` prefix; the committed-plan ring
was checked after removing the old white focus-colour override. The existing
user-owned recap draft has trailing whitespace and was deliberately left alone;
the scoped implementation/doc diff is clean.
