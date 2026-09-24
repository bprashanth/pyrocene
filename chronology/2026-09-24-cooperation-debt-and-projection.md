# Cooperation: debt, one landscape projection and Recap I

Baseline: `5ac5bb6` on `stage4_recap`. This extends main `/round.html`, not
Combined or the archived two-role Cooperation/Negligence game. Preserve the
user's unrelated narrative notes. Revert this scoped checkpoint to undo it;
do not reset the working tree.

## Room flow

Three private proposals still lead to discussion. The host now edits one A/B/C
dropdown per role instead of clicking a disconnected preview selector. Funds
update immediately. Negative funds are labelled Debt and do not block commitment.
Coffee B/native restoration B and grazing C/native restoration C still conflict.
Nursery A and restoration A remain compatible because production is off-map.

There is one commit. Before it, the room says “Discuss and commit the plan.”
After it, Recap I opens, then “Simulation: choices on the map over time.” A single
Projection slider changes every selected plot. Revise plan returns to discussion
so another combination can be chosen and committed. Team links retain privacy
before reveal, and only the host can change other teams' proposals.

Stage/team selectors now stay on the right in Expedition and Cooperation.

## Projection and fire

- Native restoration uses the accepted canopy-growth renderer.
- Unplanted removal clears again at years 3, 6 and 9. Grass grows between cuts.
  The fuel field follows this same cycle. Planting or coffee on that square
  suppresses the unplanted-removal cycle.
- Nursery production has no new on-map geometry.
- Coffee B adds a low crop layer and taller shade crowns using transformed
  measured point fragments. Coffee reaches 2 m, shade reaches 12 m by year ten.
  These timings and shade height are illustrative, not measured growth curves.
- Grazing C includes a first-season burn in Projection (0–0.5 years). Later
  projection positions retain its scar rather than restarting fire each year.
- Other community choices expose Fire after commit. It tests the landscape at
  the current projection year. There is no Run fire button. Every main plan
  ignites at C with the same northward wind, including nursery/coffee choices.
- The model spreads for 20 minutes; the slider extends to 24 so the last front
  can cool. The accepted main fire material and height palette remain intact.

This is a scenario comparison, not a coupled ten-year post-fire ecosystem model.
The grazing burn uses first-season fuel. Native growth is the intended planting
trajectory; later fire mortality and recovery of each individual tree are not
modelled. Fire changes the score and surface scar. Do not describe this as a
historical NBR reconstruction or a calibrated prediction.

## Recap I

A green/yellow modal plots all 21 compatible plans: net group earnings against
forest-health change at ten years, **without fire**. The chosen plan is yellow.
Point hover, click or keyboard focus explains that combination without editing
the room. Reopen it from Recap I in the stage menu after commitment. The existing
three-page Recap is unchanged.

Earnings exclude the grant. Nursery payments are internal transfers, not added
group revenue. Coffee starts earning after year three, with shelter affecting
returns. Grazing benefits are saved feed expenditure, not cattle sales. Later
cuts return 65% of the first net removal margin and add 30% of its native damage.
Tree tending costs 0.4 credits/year for four years; coffee care 0.3/year; coffee
earns 2/year times shelter after year three; grazing saves 2 in the first year.
These are explicit game assumptions recorded in Sources, not real prices. Debt
has no interest/default mechanic. Recap is a forecast, not a second cash wallet.

FAO supports pruning coffee to 1.5–2 m, not these growth/yield assumptions:
https://www.fao.org/4/ad219e/ad219e06.htm . Existing WeForest/IDESAM, Amazon Fund
and Embrapa sources remain. Community survey cards keep qualitative returns and
health; only the room combines them into numerical scenario accounts.

## Implementation and isolation

- `cooperation-projection.mjs`: shared point/fuel/accounting assumptions.
- `cooperation-growth.mjs`: installs projected coffee and removal succession on
  the main RoundForest instance. New growth inherits its fire material.
- `cooperation-recap.mjs`: accessible modal/SVG graph; no room writes.
- `community_cooperation/app.mjs`: room dropdowns, phase flow and timelines.
- `community_cooperation/store.py`: permits debt, still enforces land use.
- `round-render.mjs`: opt-in lighter, non-blocky regrowth sampling. Only this
  integration enables it; other missions retain their original point rendering.
- Server/package allowlists include all three new modules. `run.sh` serves them.

The old `/community-cooperation/` comparison page shares the debt backend but
keeps its old renderer and projection/fire controls. Its separate fire-review
mode still permits the neighbouring-field ignition. Main always uses C.

## Verification

Played with actual clicks and keyboard range controls in Python Playwright.
The in-app browser reported no available browser, so the browser skill's
fallback was used. WebGL and disabled-WebGL runs cover debt, conflict, private
links, revise/reset, direct room edits, coffee growth, clearance/regrowth,
grazing fire, restoration-dependent spread, species/structure, and old flags.
Recap dot interaction is checked not to mutate proposals. Header positions are
checked across Expedition and Cooperation. Model/store/delivery tests also run.

Screenshots outside git: `/mnt/seagate/models/pyrocene/stage4/qa-cooperation-integrated/`.
Key captures: `debt-review.png`, `debt-recap.png`, `joint-projection-year-two.png`,
`joint-projection-year-three.png`, `joint-projection-year-ten.png`,
`laptop-grazing-spread.png`, `restored-C-original-fire.png`, `young-C-fire.png`,
and corresponding `software-` captures. Screen review prompted removal of
blocky/opaque weed tiles; the terrain and original fire styling were retained.

Commands:

```sh
python3 -m unittest stage4.test_cooperation -v
python3 -m unittest stage4.community_cooperation.test_store stage4.community_cooperation.test_play stage4.test_delivery -q
node --test stage4/test_cooperation_projection.mjs stage4/community_cooperation/test_model.mjs stage4/test_round_model.mjs
```

No new Combined mechanics, autonomous strategies or human-workshop findings
are claimed. The user will judge the discussion flow in the main game.

Final verification: 15 main browser tests, 11 prototype browser tests, 14 JS
model tests and 18 store/delivery/archived-room tests passed. Asset preflight
passed. Live 8024 was played through debt commitment, projection, fire, revision
and a nursery recommit with no browser errors. Stage 4 ports 8024 and 8036 were
refreshed for the new allowlists; their prior in-memory rooms expired. Other
stage servers were not restarted.
