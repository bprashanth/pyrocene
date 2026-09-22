# Stage 4 handoff, 22 September 2026

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
