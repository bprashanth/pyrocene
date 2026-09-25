# Recap II income correction and Recap III trial

## Rollback and scope

Annotated tag `stage4-before-recap-three-20260925` preserves `29e21c0`, the
previous Recap I/II version. The earlier tradeoff checkpoint remains available.
User-owned narrative drafts and `stage4/v2_recap.md` are untouched.

This change is limited to the read-only Cooperation recaps. Recap I's scores,
room budgets, choices, map projection, fire, Combined and archived Negligence
are unchanged. Existing static modules only; no server restart or new route.

## Recap II: what the income line means

The old chart plotted accumulated group earnings. A flat line meant money
retained, but looked like a continuing nursery income. The user asked for a
large initial nursery order followed by smaller replacement orders, while
later coffee harvests eventually earn more than keeping only the nursery.

The upper chart now explicitly plots **annual community operating income**,
after routine care but before one-off set-up costs. Those costs are written
below the graph. This is not the group's balance, nor a claim that a payment
from ecologists creates new money for the group. The lower chart keeps the
existing forest-health comparison. No Year slider; all ten years are visible.

Illustrative curves in `timeOutcome()`, with year y clamped to 0..10:

- Nursery income: `0.35 + 5.65 * exp(-0.48*y)`. Initial income 6; year ten 0.4.
  The smaller follow-up orders require buyers, rather than assuming the first
  order supports constant income forever. Set-up costs 2 credits.
- Coffee: three years without harvest, then a gradual rise towards a
  shelter-dependent yield, less 0.3 credits annual care. Set-up costs 6.
  Year ten operating income is about 2.6 credits/year in this fixed scenario.
- Nursery then coffee: nursery orders continue to taper; plant coffee in B
  at year three for a further 6 credits. Coffee care starts then, harvest
  begins after year six. Year ten income is about 2.7 credits/year.

These are authored comparison curves, not an empirically calibrated forecast,
an end-to-end cashflow ledger or a new promise of buyers in the playable game.
They deliberately do not change `beforeFire()`, which underlies Recap I and
the live game. Set-up costs are not silently deducted again as annual costs.
The comparison does not prove the staged option repays its investment sooner.
All alternatives assume ongoing care and exclude wildfire/failed harvests.

The left column has an overhead rendering of the same measured forest points,
with A/B/C boundaries and labels. It is a baseline orientation map, not a second
projection or a camera change to the playable forest. It uses either loaded
GPU geometry or CPU source points and needs no additional asset download.

## Recap III: possibilities through time

Next from Recap II opens a rotatable spatial chart, not a LiDAR scene:

- Horizontal: net group earnings, using Recap I's existing accounting.
- Vertical: forest-health change.
- Depth: start, year five, year ten, marked by three outline planes.
- All 21 allowed fixed plans appear at those anchors. Only the selected plan
  has a continuous path, avoiding 21 crossing lines. It returns exactly to
  its Recap I position at year ten.
- Colours group plans by one, two or three **field plots to coordinate**.
  This is a coordination cue, not a labour penalty or travel-time calculation.
  Nursery production is off-map and is not counted as a third field plot.
- Click a point or select a plan from the dropdown. Drag to rotate. Arrow
  keys rotate too; Home restores the initial angle. The dropdown makes
  overlapping points reachable without precise depth selection.

This third page compares the fixed plans, not every possible sequence of
changing land use. Recap II remains the explicit staged nursery/coffee example.
The copy links the three-plot exercise to Combined's many selectable plots
without claiming Community is already integrated into Combined.

The chart uses SVG with orthographic projection and no animation loop, so it
does not require WebGL or add a second 3D renderer. Only the selected path is
drawn through intermediate years; muted dots are time anchors, not uncertainty
samples. Rotating changes the view, not values. Read-only recap interactions
must not change room proposals, projection year or fire time.

## Review and tests

The browser skill found no connected browser; used the repo Playwright suite.
First laptop screenshot review caught an 11px overflow in Recap III. Reduced
the chart's maximum height and fitted its box at all allowed rotation angles.
Recap II's map, annual-income labels, declining nursery curve and coffee rise
were checked in screenshots. Screenshots live outside git under
`/mnt/seagate/models/pyrocene/stage4/qa-cooperation-integrated/`:
`recap-time-{nursery,coffee,sequence}.png`, `recap-space-{initial,AAA,CCB,ABC,turned}.png`
and software-rendered variants.

Regression coverage: all three time comparisons, no slider, measured minimap
pixels, all 21 spatial choices, one highlighted trail, plot-count labels,
pointer rotation, pointer selection, keyboard selection, return navigation,
laptop overflow and unchanged room/year/fire state. Pure tests check tapering
positive nursery income, coffee delay and care costs, investment timing,
late income crossover, field-site counts and existing Recap I rankings.

Commands:

```
node --test stage4/test_cooperation_projection.mjs stage4/test_round_model.mjs stage4/community_cooperation/test_model.mjs
python3 -m unittest stage4.test_cooperation -q
python3 -m unittest stage4.test_delivery stage4.test_shared_round stage4.community_cooperation.test_store -q
```

To remove this trial, restore the recap UI/model/CSS/Sources and associated
tests from the tag as a scoped change. Do not reset unrelated user files.

Final verification: 19 full main-game browser tests passed; the two focused
recap tests passed again after adding extreme-angle clipping checks and fixing
text selection during drag. The 18 JS model tests and 19 delivery/store/archived
room tests passed. Live port 8024 was played through commit, Recap II, Recap III,
plan selection and return to map with unchanged room/year/fire state and no page
errors. Inspected the live and software screenshots. No server restart.
