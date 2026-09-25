# Consistent stage menu, Prelude reference maps and turning points

Rollback: annotated tag `stage4-before-prelude-hinges-20260925` at `1bf6ff3`.
User narrative drafts and `stage4/v2_recap.md` are not part of this checkpoint.

## Navigation

`fillStageMenu()` supplies Start Here / The Players / Prelude / The Game / Recap
to both the shared flow and the single-player game. No special “Back to The
Players” menu replaces it. Archived Negligence remains flag-gated.

Inside The Game, Prelude opens in place. It reads the originating shared room's
committed plan if available. Direct entry without a committed room uses a clearly
labelled all-A example. Closing Prelude or clicking its Play game button returns
to the current single-player run, without resetting it. The Players retains the
shared-room URL/capability; Start Here opens Expedition. A room still on its
expedition screen is entered normally when selecting The Players. No new routes
or server APIs; the single-player rules and saves are unchanged.

## Prelude pages

All three comparison pages now say Prelude I/II/III, including navigation and
accessible labels. The closing environmental Recap keeps its distinct name.
All three pages show the same measured overhead A/B/C reference map under their
left-column content. This is orientation, not a second projected forest.

Prelude III returns to “How much can we keep tending?” General instructions and
the distinction between yearly community income and accumulated group earnings
are under a closed **About this graph** disclosure. Prelude I also puts its
general chart instructions there to make room for the map.

## Turning-point trial

The selected 3D trajectory has three numbered markers and matching year buttons.
One short note is shown at a time. Markers are clickable and keyboard-operable.
Numbers stay linked to the selected plan when the graph rotates.

`planHinges()` derives the applicable events from the existing model:

1. Matched nursery order paid by year two; coffee harvest begins after year
   three; grazing's first-year feed saving; or an unmatched nursery order.
2. Early tending charges end after year four in the projection. This does not
   imply real forest care becomes unnecessary.
3. A second clearance at year 7.5 when removal is not followed by planting,
   otherwise the recovery achieved at year ten.

For restore A / remove B / nursery A, the second clearance adds **5.2 credits**
and removes **0.3 native-health points**. The annotation explains both, rather
than pretending a downward-looking 3D segment is only a fall in returns. The
path now samples immediately before the clearance to show its discrete payment
accurately. The underlying finance, forest-health and fire rules are unchanged.

Prelude II retains its whole-trajectory explanation of the nursery decline,
coffee investment at year three, care costs and harvest after year six. No new
slider or extra control stack there.

## Closing Recap map

The “How fire reaches the forest” page now uses `projectedFire(null, 0)`, exactly
the current Players untreated-landscape simulation: fine fuel, C ignition and
the same weather. It replaces the legacy `runFire()` scar. The artificial
square-centre polyline is gone. Yellow points highlight high invasive fuel
inside the actual simulated scar. Orange points retain the scar aesthetic.

This is a reference scar before treatment, not the last player's saved result
or historical NBR. That distinction is stated in Sources. Forest Stewards' edge
mark and the other closing Recap pages remain unchanged.

## Verification

The browser skill found no connected browser; repo Playwright fallback used.
Main suite: 21 tests passed including WebGL-disabled coverage. Model tests verify
the ABA clearance annotation against actual money/health deltas, all 21 plans'
event timing, and exact recap/current-fire arrival arrays with no world mutation.
Laptop screenshots were inspected; reference maps were enlarged to match page II
and the focused layout/interaction test passed again.

Additional checks cover direct Game entry, example Prelude, return to the same
run, full stage-menu text, Start Here and The Players navigation, current-room
Prelude, closing Recap return, and existing single-player controls/contrast.
19 delivery/store/archived-room checks passed. New screenshots remain outside git:

- `qa-cooperation-integrated/prelude-hinge-returning-crew.png`
- `qa-cooperation-integrated/recap-new-fuel-corridor.png`
- `qa-cooperation-integrated/recap-tradeoff-AAA.png`
- `qa-expedition/game-prelude-menu.png`

All are under `/mnt/seagate/models/pyrocene/stage4/`, with software variants in
the main QA folder. Existing static files only; no server restart required.

Final checks: 21 JS model tests passed. Live port 8024 passed the full Players
to Game flow, the identical menu, room-based Prelude, return to an unchanged
single-player run, updated closing scar and return to the same committed room.
Direct-entry example/navigation and existing Game controls passed as well.
