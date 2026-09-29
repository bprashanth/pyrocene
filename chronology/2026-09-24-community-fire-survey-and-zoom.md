# Community: height colours, survey fuel, fire review and Close-view labels

Rollback baseline: `fb94232` (three-role prototype). This is a refinement of
that isolated prototype, not a merge into Cooperation or Combined.

## User feedback implemented

- Restored the original pink/blue/green height palette. Hidden fuel must not
  turn low vegetation green. Species and survey clues reveal fuel instead.
- C and the openings ahead contain invasive grass and higher fuel. Its two
  immediate side neighbours have no invasives and substantially lower fuel.
  Any map square remains available for survey, not just A/B/C.
- Removed the hard fuel cutoff at side-square boundaries. Fuel is interpolated
  and uneven. Treatment effects also fade across their boundaries. Native
  litter can carry a small lateral spill even in a mostly damp neighbour.
- A fixed northward scenario wind and a 20-minute run favour forward spread,
  with less backward expansion. This remains a designed educational scenario,
  not a measured ignition, calibrated fire forecast or historical scar.
- Added Review fire on `/community/` and `/community-cooperation/`. It opens
  `/community-cooperation/#fire=1` in a separate tab. No role proposals, room
  creation or server mutation are required. Compare Current forest / Restored C
  at the same ignition and wind. Ignition can be C or the neighbouring field.
- Fixed the label stilts shown in `/tmp/bizzare.png`: stop collision stacking
  labels upwards, keep fixed-size text and 12px leaders, hide overlaps at wide
  zoom. Existing plant lists remain available. This inherited rendering fix
  also applies to the main Expedition, Round and Combined views.

## Verification and observed outcomes

Played real browser controls through role proposals, conflicts, affordability,
nursery/no-order, grazing and shaded-fruit cases. All 11 Playwright tests passed,
including software rendering with WebGL disabled, 1280px laptop layout, shared
team sessions, standalone fire review, `/community/` review link, and wheel zoom
out in both prototype and main Expedition. Inspected resulting screenshots.

Model tests cover intact flank inventory, gradual ignition, recovery effects,
room finances, smooth fuel boundaries, limited lateral spill and forward bias.
The existing six Round model tests still pass with the default wind unchanged.

Current 20-minute example: ecology C / removal A / community B burns 4.88 ha at
year 10 versus 20.00 ha without work, and 18.97 ha at year zero. Grazing ignition
in C with ecology/removal A burns 17.87 ha. These are deterministic scenario
outputs, not real-world effectiveness estimates. See the prototype README for
accounts, source limitations and earlier checkpoint comparisons.

Screenshots (not committed):
`/mnt/seagate/models/pyrocene/stage4/qa-community-cooperation/`.
See `choice-C.png`, `grazing-spread.png`, `review-current-forest.png`,
`review-restored-C.png`, `expedition-wide-no-stilts.png` and
`close-wide-no-stilts.png`.

Preview is served on port 8036. The existing 8024 process was left untouched.
A fresh `run.sh` includes the prototype routes on 8024; static label changes
are available to the existing server on refresh. User edits to recap/concept
notes are not part of this checkpoint.
