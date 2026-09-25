# Recap I tradeoffs and Recap II time trial

## Checkpoint and scope

Before editing, created annotated tag `stage4-before-recap-tradeoffs-20260925`
at `4d0e7b7`. The user's dirty narrative files were not included. This is the
accepted graph-first recap/two-cycle baseline, available for a scoped rollback.

Main Cooperation gets the new recap trial. Combined and archived Negligence are
untouched. No new land-use choices: nursery A, coffee B, grazing C. The adjacent
example is restore C plus coffee B. Coffee C/restore B is not silently added to
the actual game. Recap II is a separate comparison, not a fourth room proposal.

## Recap I

Click or keyboard-focus a dot to change the explanation on the left. Selection
persists when the pointer leaves; white outline means the selected comparison,
yellow remains the committed plan. The caption names that comparison. No proposal,
room revision, map projection year, fire time or credits are changed by browsing.
All 21 compatible plans remain visible on tightly framed linear axes.

Stories explain matching nursery orders, careful clearing, nearby shelter,
unmatched orders, debt, grazing and profitable repeated removal in A. The all-A
story also says C remains an exposed connection: high health without fire is not
the same as protection from the scenario fire. Restoring C beside coffee B has
a young-tree fire caveat. Both graphs explicitly exclude wildfire.

### Revised model, not merely moved dots

`cooperation-projection.mjs` adds explicit, inspectable cooperation assumptions:

- Nursery A with restoration A retains 4 credits of plant purchases in the
  group over two years. This refunds an internal portion of the planting expense
  already charged, not new money from selling plants to oneself.
- With all three teams in A, careful clearing preserves 4 native-health points,
  shared tending saves 0.3 credits/year for four years, and establishment adds
  10 recovery points over ten years. The initial removal damage was 5 points.
- Matched nursery/restoration without removal in A adds 3 establishment points
  instead. Clearing and planting still need separate visits.
- Restoring C beside coffee B adds 5 shelter-related health points by year ten.
- Existing income, repeated-clearance damage, coffee costs/harvest timing and
  grant remain. Credits and forest-health points are still separate units.

These are authored scenario assumptions to make cooperation's consequences
legible, not empirical effect sizes. They assume appropriate planting and
continued care, not that every nursery automatically produces these outcomes.
They are disclosed in Sources and tested. `beforeFire()` is shared by Recap I
and the main projection's health display, so the new health scores are not
limited to a misleading graph. Fire propagation and point geometry are unchanged.
Upfront server budgets are unchanged; the savings accrue in the projection.

Ten-year illustrative outcomes:

| Plan | Net group earnings | Health change before fire |
| --- | ---: | ---: |
| Restore A, remove A, nursery A | 6.6 | +17 |
| Restore C, remove C, coffee B | 1.3 | +13 |
| Restore C, remove B, coffee B | 0.3 | +13 |
| Restore C, remove A, coffee B | 12.1 | +7.5 |

Thus coordinated A is healthiest and profitable, but repeated removal in the
native-rich plot still earns more. The nearby restoration/coffee plans come next
on health, while their early fire exposure is deliberately not in the graph.

## Recap II: time

Open with **Recap II: time** from Recap I. The page holds removal and restoration
in A fixed, and compares three named paths on two line graphs: group net earnings
and forest-health change. One Year slider moves both cursors and the explanation.

1. Keep the nursery: supply A's restoration order, then assume no new order.
2. Coffee from the start: plant coffee in B immediately, with a three-year wait
   before harvest; there is no matching nursery support for A.
3. Nursery, then coffee: start with the matched nursery order, invest 6 credits
   in coffee B at year 3, pay 0.3/year care, and wait until year 6 for harvest.

The latter retains A's restoration and its care. It does not replace native
planting with crops. The nursery is off-map; coffee is in B. The selected Recap I
dot need not be all-A, so the fixed-A comparison is stated explicitly on page II.
Back restores that selected dot, and Back to map closes without any game write.

At year ten, nursery-only retains 6.6 net credits / +17 health; early coffee
has 2.1 / +6; nursery then coffee has 2.9 / +19.1. This is not a forced winner:
waiting defers investment and harvest, while nursery-only keeps more money
unspent through year ten. No new nursery orders, wildfire, harvest failure,
interest/default or unconstrained crop relocation are simulated.

Implementation is contained in existing `cooperation-projection.mjs` (pure
support/story/time functions), `cooperation-recap.mjs` (two-page read-only UI),
the recap CSS and Sources copy. No route or server changes, and no restart
needed. Recap II can be disabled by removing its navigation button/handler while
retaining Recap I; it has no persisted state or independent engine dependencies.

## Verification

Model tests check rankings, internal purchase accounting, the six-credit
investment at year three, delayed harvest, and absence of world mutations.
Browser play clicks the all-A, adjacent-coffee and high-return dots, scrubs time,
switches all three comparisons, returns to the prior dot, and verifies room,
year and fire state stayed unchanged. Both WebGL and software paths are covered.

The browser skill reported no available browser; repo Playwright was used.
Screenshots outside git in `/mnt/seagate/models/pyrocene/stage4/qa-cooperation-integrated/`:
`recap-tradeoff-AAA.png`, `recap-tradeoff-CCB.png`, `recap-tradeoff-CAB.png`,
`recap-time-year-zero.png`, `recap-time-coffee-investment.png`,
`recap-time-year-ten.png`, and per-comparison/software variants.
Laptop screenshots at 1280 x 800 were inspected for legibility and overflow.

Final checks: 19 main-game browser tests passed (including WebGL-disabled
coverage), 17 JS model tests passed, and 19 store/delivery/archived-room checks
passed. Live 8024 dot selection, the time comparison and return to an unchanged
room passed without browser errors. No server process was restarted.
