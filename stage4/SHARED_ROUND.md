# One shared plan

Open `/round.html`, or More / Shared plan in the accepted expedition. The old
forest page stays intact. Before this trial: `211c4db`, tagged
`stage4-before-shared-round`.

## Play

On one laptop, start in Removal. Inspect a lettered patch in Close view, optionally
open Structure, then Propose. The view switches to Ecology. Submit its proposal
and the view switches to Room. Reveal, discuss, optionally change a proposal
using the team selector, and commit once. The selector is only available to the
facilitator. No assistant, additional missions or species-mix calculator.

For two teams, the facilitator opens Teams and shares the separate Removal and
Ecology links. Each team opens its link on its own laptop. Both laptops must
reach the same running server. Internet access is not required. The Room view
reveals and commits. Until reveal, a team sees only its own proposal and whether
the other team is ready. These are capability links, not named accounts. Anyone
given a team link can act for that team; do not share the facilitator URL.

Teams can revise proposals after reveal but not after commitment. Independent
surveys and proposals can arrive together. A stale shared commitment is rejected.
Proposals are held in server memory, survive browser reloads and end when the
server restarts. Replay the same forest resets the proposals on the same room,
retains survey checkmarks and uses the same starting conditions. At most 128
rooms are retained. Recovery/fire playback is local to each screen; decisions
and committed plans are shared, not each user's camera or playback position.

## Deliberately small rules

Two proposals: remove one patch and restore one patch. One fixed processing
facility is assumed off-map. No route, equipment or kiln-placement choices.
The room begins with 2 game credits. Removal earnings are already net of its
assumed operating costs. They are not biochar yield or carbon-credit revenue.

| Patch | Map sector | Removal earnings | Native cover lost during removal | Planting/care cost |
|---|---|---:|---:|---:|
| A, mixed growth | C2 | 12 | 18% of A | 7 |
| B, open ground | D5 | 8 | 4% of B | 6 |
| C, narrow link | E4 | 6 | 2% of C | 6 |

Restoration costs another 3 credits for selective clearing unless removal is
already proposed in the same patch. Overlap never clears twice. The restoration
crew's separately paid selective clearing has no added native-loss penalty in
this toy model. Damage percentages are authored local-area indicators, not
measured mortality or deductions from a combined health score.

For removal/restore pairs AA AB AC BA BB BC CA CB CC, money remaining is
7, 5, 5, 0, 4, 1, -2, -1, 2 respectively. CA and CB cannot be committed.
Changing CA to CC makes the proposal affordable. AA earns more than CC but
damages more native cover and leaves more of the simulated fire route intact.
The fixed native mixes are in `round-config.json` and the optional Structure
comparison's About section. No mix is reconstructed botanically from a scan.

## What changes in the points

The trial reuses the accepted airborne scan and ground-scan neighbourhoods.
Its B opening and C narrow gap are authored visibility masks. They do not edit
the source files or the old expedition renderer. The structure lab uses matching
qualitative profiles: mixed cover at A, larger opening at B, a smaller opening
at C. Neither the scan nor the fictional plot assignment proves fire risk.

Removal fades low vegetation. Its native-damage strip fades some taller points.
Projected recovery copies measured upper-canopy returns from the reference
tile, relocates them into the chosen patch and grows their height/visibility.
There are no generated cone meshes or static forest panels. The 10-year slider
is an illustrative transition, not a species-specific growth forecast. Recovered
close views show the fixed native names, rather than retaining invasive labels.
Original structure remains available, explicitly labelled as original during
the outcome preview. The optional species records remain reference descriptions.

Fire uses the existing educational Rothermel arrival solver on a 60 by 60 grid
of 15 m cells. A fixed ignition in F4, the same wind and a 20-minute horizon
apply to both runs. Fuel, moisture and exposure are authored at 15 m resolution.
Irregular fuel bands cross plot boundaries, so the scar follows a path rather
than filling whole squares. The corridor through C contrasts with wetter
surroundings. The separate memory lab retains its original field by default. The
future restoration scenario assumes successful establishment and damp litter;
it is not a guarantee that planting makes a forest fireproof. Removal without
restoration retains a lower but nonzero future fuel load. No historical fire
is reproduced, no ignition probability is estimated, and this is not ForeFire.

The front colours the existing points and adds a small rising point layer.
Brown points retain the scar. Without plan / With plan switches the arrival
field at the same camera and playback time. The displayed hectares count fine
cells reached within the teaching horizon, not empirically predicted loss.

The no-WebGL path uses the same geometry, masks and arrival arrays in Canvas2D,
with fewer points and a capped redraw rate. It has no rising ember layer.
GPU and CPU views remain rotatable, zoomable and selectable. The model is
computed on decisions, not continuously while dragging.

## Verification

`test_round_model.mjs`: all nine budgets, overlap, deterministic fire, different
outcomes and no mutation of the separate memory lab's world.
`test_shared_round.py`: funds, role permissions, private proposals, stale
commitments, concurrent independent actions, replay and commit-once behaviour.
`test_round.py`: solo play, two isolated team sessions, revising an unaffordable
plan, shared commit, browser reload, point-image changes, structure lab,
mobile/no-WebGL, rotation during outcomes, restored close view and recovery/fire comparison.
`test_portable.py`: runs the trial from the extracted offline archive.

Screenshots are external under `stage4/qa-expedition/round-*.png`. They are QA
captures, not game assets. Browser playthroughs test usability and mechanics,
not whether a room of participants will find the negotiation enjoyable.
