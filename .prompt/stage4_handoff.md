# Stage 4 handoff, 22 September 2026

## Latest: Recap I cooperation stories and Recap II time

Checkpoint tag `stage4-before-recap-tradeoffs-20260925` points to `4d0e7b7`.
Read [this trial](../chronology/2026-09-25-recap-tradeoffs-and-time.md) before changing
the graph. All-A now ranks highest for health through explicit careful-clearing,
matched nursery and care assumptions, used in both the graph and projected
health display. Restore C / coffee B follows. Repeated removal in A earns more
but damages native growth. Click/focus dots for relevant prose; white is the
selected comparison, yellow is the room's committed plan.

Recap II: time is reached by a button in Recap I. It compares nursery-only,
coffee now, and nursery then coffee at year three, fixing removal/restoration
in A and coffee in B. Two graphs and one year slider, no room writes. Back
preserves the selected dot. Costs, delayed earnings and limitations are in the
chronology and Sources. Both pages exclude wildfire. Recap II does not change
the map or commit a new plan. No server restart needed. Combined stays untouched.

## Latest: graph-first recap and two removal cycles

Baseline `962f16b`; see [graph/cycle checkpoint](../chronology/2026-09-24-cooperation-graph-space-and-two-cycles.md).
Recap I now has one explanatory paragraph and a roughly two-thirds-width graph.
Linear bounds hug all outcomes with 6% padding, rather than excess negative-axis
space. Unplanted removal shows two smooth five-year clearance/return cycles,
cleared at 2.5/7.5 and reinvaded at 5/10. Initial cut plus one later paid cut
keeps the same ten-year recap accounting as before. Static refresh only.
Combined remains unchanged. Next discussion: how Community could enter Combined.

## Latest refinement: direct Room editing

See [room simplification](../chronology/2026-09-24-cooperation-room-simplification.md),
baseline `506e5ac`. Room now starts with editable per-role dropdowns and Commit;
there is no Reveal gate in main Cooperation. Backend permits host commit from
survey when all choices are complete and compatible. Main With/Without buttons
are gone. Recap I uses four plain-language bullets. It still plots ten-year
outcomes for plans chosen at the start, excluding wildfire. Unplanted removal
now fades through one slow eight-year return/clearance cycle, with matching
fuel and completed-cut accounting. All earlier three-year-cycle notes below
are historical. Combined and the prototype comparison controls remain unchanged.

## Latest: shared debt, Projection and Recap I

Read [this checkpoint](../chronology/2026-09-24-cooperation-debt-and-projection.md)
first; it supersedes funding/preview notes below. Baseline `5ac5bb6`. Main
Cooperation permits debt but not conflicting land uses. Room has one dropdown
per role, one commit, then Recap I (earnings/health before fire) and a Projection
slider for all chosen plots. Unplanted removal cycles; native/coffee canopies
grow; nursery stays off-map. Grazing includes first-season fire in Projection.
Other choices get a Fire slider at the selected projection year. All main fires
ignite at C. Existing Recap and Combined are unchanged. Header controls stay
top right. Review the explicit simulation assumptions before changing them.

New modules: `cooperation-{projection,growth,recap}.mjs`. Tests:
`stage4.test_cooperation`, `stage4/test_cooperation_projection.mjs`. New files
are on server/package allowlists; restart Stage 4 to pick up allowlist changes.
Rooms live in memory, so restart expires room links. `run.sh` uses latest files.
No need to restart any other stage. Preserve untracked user docs
`narrative/CONCEPT_NOTE.md`, `narrative/RECAP.md`, `stage4/partner_note.md`
and modified `stage4/v2_recap.md`.

## Update, 24 September: Community integrated into Cooperation

This update supersedes the older current-state notes below. Main `/round.html`
now offers Removal, Ecologist and Community. Nursery A, shade-grown coffee B,
pasture C. Three private proposals, land-use conflict resolution and shared
funding before commitment. Main RoundForest map/fire styling is unchanged;
the tested prototype supplies inventory/fuel conditions and spread direction.
Negligence is hidden by default. `?negligence=1` explicitly restores the archived
two-team Cooperation -> Negligence flow. Combined is unchanged: wait for review
before integrating anything there. Prototype routes are retained until review.

Read [the integration chronology](../chronology/2026-09-24-cooperation-community-integration.md)
for files, test commands and rollback baseline `f45226e`. Use fresh main links;
old two-team rooms are not silently converted. New server/package allowlists
include the integration entry modules. All current stages can run on 8024 with
`run.sh`; the historic companion ports below are no longer required.

Read this before changing anything. Latest task: finish Recap integration, then
wait for the user to design the final stewardship mission. Do not redesign the
accepted gameplay, replace the point clouds, or implement a new final mission
without discussion.

## Accepted game and live servers

- Main game: http://100.82.28.38:8024/ (Expedition, Cooperation, Negligence).
- Combined: http://100.82.28.38:8033/strategy.html . Main menu already routes here
  when the older shared server cannot serve Combined directly.
- Separate experiment/recap entry: http://100.82.28.38:8035/community/ . Old
  Community gameplay is deliberately parked behind `#prototype=1`.
- Do not restart 8024 or 8033 casually: shared sessions live in process memory.
  Modified existing static files are served from disk, but new allowlist entries
  require a restart. Recap therefore uses existing main-game static filenames.

## What is now implemented

Recap is in each main stage dropdown. It opens a modal on the current forest.
Three pages: why exposed land keeps burning; fuel connectivity/fire lines;
Forest Stewards. No Hazel portrait. Keep the green/yellow point-cloud aesthetic.
Finish closes the modal and returns to the current map, not a new game. Funds,
turns, proposals, credentials and saves must not change.

The final page marks the exposed forest edge and uses shade-grown coffee in the
Nilgiris (Aadhimalai/Keystone) and Amazon coffee agroforestry in Apuí
(IDESAM/WeForest) as parallel examples. The argument is continuing livelihoods
and land care, not a company advertisement. Last Forest was removed.

Canonical code:
- `stage4/play-briefing.mjs`: original role BRIEFINGS plus PRELUDE copy, per-page
  sources, map drawing and createPrelude. PRELUDE is a legacy variable name.
- `stage4/play-flow.mjs`: bindRecap intercepts the Recap dropdown change without
  triggering the ordinary stage-reset handler. Binding is lazy until first use.
- `stage4/play-flow.css`: recap layout and typing styles.
- `stage4/round.mjs`, `expedition.mjs`, `strategy.mjs`: bind to current renderer.
- `stage4/community/prelude.mjs`: compatibility re-export only, not canonical.

Do not create another copy of recap text in the prototype. The map draws from
already-loaded measured scan points. Page 2 uses Cooperation runFire() baseline
and the authored corridor overlay, not historical NBR or a player's actual scar.
Page 1 ignitions and page 3 edge marker are illustrative. Source disclosures say
so. Read the new chronology and narrative/GAME_DESIGN.md for the integration.

## Main game mechanics to preserve

Cooperation: removal and ecology teams survey three candidates and propose.
The room chooses a shared plan, commits, then explores recovery and fire. The
small connector C demonstrates breaking a fuel corridor, not maximising removed
biomass. Negligence revisits after six months: care among saplings earns little
but protects recovery; lucrative new clearance can leave prior work to reinvade.
Species records provide dispersal and germination information in every stage.

Combined: both roles in one private 12x12 board, 108 active 75m squares. Starting
12 credits, 24 six-month turns, five Unstable plots capacity. Remove/restore/weed;
no Skip or separate Structure button. Close view is free. Empty removal still
costs 1. Canopy closure ends instability; fire can kill unfinished planting and
re-invasion can end a commitment badly. Forest health and credits are separate.
Local sporadic fires can spread across several plots; they need not resemble
Cooperation's long corridor fire. User explicitly said NOT to retune this now.

## Parked Community prototype: not accepted as final mission

Read stage4/community/README.md and player-findings.md, not just the screenshots.
Its model adapts strategy-model.mjs without modifying it. Four starting open
plots: native E8/F8, buffer gaps E9/F9; fuel E10/F10; forest E7/F7. 18 credits,
partnership cost 5, local nursery/shade-crop earnings pay local tending and
reserves can fund rebuilding. Buffers reduce risk, can burn, and are not counted
as restored native forest. This fixture/economics/extra boundary ignition was
an experiment the user wants to work through piecemeal. Do not merge it wholesale.
Its selected seed 991 and simple policy probes are not field-effectiveness data.

The intended NEXT discussion is who protects the edge while restoration takes
hold: community livelihoods, shade crops, seed nurseries, continuing tending.
There is no agreed final loop. For now Recap ends at Forest Stewards and Finish
returns to the map. Later the final stage may be attached there.

## Evidence and writing constraints

- Roughly 95% human-caused Indian fires is a cited historical estimate, not proof
  most are livelihood-related. Use “many”.
- F4F publicly describes fire-free Mahua collection support. Do not claim F4F
  promotes burning. Mahua/tendu fire uses have separate documentary sources.
- Healthy forest, agroforestry and fire lines are not absolutely fireproof.
  Avoid promises of income “forever” or that NTFPs/agroforestry are identical.
- Aadhimalai coffee: https://aadhimalai.in/coffee/ . WeForest/IDESAM:
  https://www.weforest.org/blog/special-projects/coffee-helping-reforest-amazon/ .
- Plain adult prose, no em dashes, no grand metaphors, minimal controls.
  Keep close/forest/overhead and dense immersive point clouds. No cone trees,
  slideshow replacement, extra assistant buttons or sprawling missions.

## Tests, screenshots, commits and user work

Run `python3 -m unittest stage4.test_community stage4.test_strategy -q`.
Main Recap has an unchanged-state browser regression in test_community.py.
Use existing test_round.py helpers for shared phase/role coverage. Model tests:
`node --test stage4/test_round_model.mjs stage4/test_strategy_model.mjs`.
Screenshots outside git: /mnt/seagate/models/pyrocene/stage4/qa-community/,
including main-recap-stewards.png. Never commit large PNGs.

The in-app browser repeatedly returned no available browser; skill-approved
fallback was Python Playwright using SwiftShader, with disabled-WebGL checks.
Read the browser skill before browser work. Cursor CLI model
gpt-5.3-codex-low can be used for bounded grinding; its latest read-only review
timed out after 120s. Claude Haiku previously authenticated but play prompts
timed out. Do not claim their review/play succeeded without actual output.

Branch: stage4_recap. Baselines: b8f50f8 accepted Combined, c4e5ac5 community-v0,
b030523 two-page Hazel, 355dae3 three-page Recap. Tags stage4-before-community
and stage4-community-v0 preserve prior checkpoints. Read latest git log for the
main integration commit. Prefer scoped revert over reset.

USER-OWNED DIRTY WORK: stage4/v2_recap.md modified; narrative/RECAP.md untracked.
These were present throughout and deliberately left out of our commits. Preserve
them. Do not stage all. No push was requested; commits are local.
