# Fire at the selected year and explicit prelude entry

Rollback tag: `stage4-before-prelude-flow-20260925` at `452225f`.
User-owned narrative drafts and `stage4/v2_recap.md` remain untouched.

## UI flow

- Commit stays on the shared map. It no longer opens Recap I automatically.
- Projection and Fire remain together for every community choice, with a
  Recap button below them to start the three-page comparison.
- Navigation labels are now Start Here / The Players / Prelude / The Game /
  Recap. Internal values, URLs and saved room capabilities are unchanged.
  Prelude stays disabled until a plan is committed. The closing Recap is still
  the separate edge-fire / Forest Stewards sequence.
- Recap III title: “How much can place-neutral actors keep tending?” A slightly
  smaller title fits without widening the text column. Removed the “In Combined”
  paragraph. Play game enters the existing single-player game using its usual
  fresh-board navigation, with the shared-room return URL preserved.
- Single-player menu/title use The Game. No single-player mechanics changed.
- Tightened the committed panel's spacing so both sliders and Recap are visible
  together at laptop size, rather than placing Recap below the scroll boundary.

## Fire semantics

Moving Projection with grazing C still shows the accepted first-season burn.
It is one historical event within that projection, not another burn every year.

Moving Fire now tests a **fresh ignition at the selected projection year**, for
any plan including grazing. It reads current fuel, invasive regrowth, restoration
and shade. For a grazing plan, moving Projection again restores the first-season
burn view. The ignition note explicitly says first season or the tested year.
For nursery/coffee plans, Projection changes the fuel landscape while Fire can
test it at any year. The spark remains at pasture C: work elsewhere does not mean
grazing ignitions stop at an untended edge. Same wind, source and fire renderer.

These are alternative previews, not cumulative fires that repeatedly change
the saved forest. There are no new persistent game states or extra controls.
`projectedFire(plan, year, {atProjectionYear:true})` implements the independent
test. The old default preserves grazing's first-season projection. The client
cache distinguishes the two modes, and a phase change resets the local mode.

Fuel cycles already affected spread, so no fire tuning was needed. With restore
A / remove C / nursery A, the fixed ignition burns 14.5125 ha at year 2.5 after
clearance versus 17.37 ha at year five after regrowth. The cycle repeats at 7.5
and 10. This checks the real simulation, not just pink point opacity. The high
cover note now says “invasives cover the ground” rather than suggesting a fully
regrown plot has already been cleared.

## Verification

Browser skill found no browser connection; repo Playwright fallback used.
Main browser suite: 21 tests passed, including WebGL-disabled coverage. New
coverage checks no auto-recap after commit, visible sliders, low/high fuel fire
extent, manual grazing ignition versus automatic first-season burn, all menu
labels, explicit Recap entry and Play game navigation. The focused laptop flow
was replayed after spacing changes and its screenshots inspected.
Both focused WebGL/software flows passed again after adding a check that Recap
fits inside the visible panel. The same full flow passed on live port 8024,
including fresh-game entry. The single-player controls/contrast browser check
also passed after the title rename.

19 JS model tests passed; 19 delivery/store/archived-room tests passed. Test
expectations for renamed single-player title and archived stage label were
updated. Fire timing and scores for default Projection remain covered by the
existing tests.

Screenshots are outside git in
`/mnt/seagate/models/pyrocene/stage4/qa-cooperation-integrated/`:
`fire-current-fuel-2.5.png`, `fire-current-fuel-5.png`,
`prelude-play-game.png` and software variants.

Existing files only. No restart, route changes, loss of rooms or changes to the
look of the forest/fire. Refresh the page to load the new client.
