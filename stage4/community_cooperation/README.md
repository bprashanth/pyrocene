# Community cooperation prototype

**Latest recap refinement:** Recap II shows annual community income with declining
nursery orders and later coffee harvests. No slider; A/B/C orientation map under
the copy. Recap III adds a rotatable time-anchored view of the same 21 plans,
colour-grouped by field plots to coordinate. Main game mechanics are unchanged.
See [income and possibilities](../../chronology/2026-09-25-recap-income-and-possibilities.md).
Rollback: `stage4-before-recap-three-20260925` at `29e21c0`.

**Recap trial:** main Recap I now ranks explicit cooperation benefits and shows
a story for each clicked dot. Recap II compares nursery-only, coffee immediately,
and nursery then coffee at year three. Both are read-only comparisons without
wildfire. See [the 25 September checkpoint](../../chronology/2026-09-25-recap-tradeoffs-and-time.md).
Combined is unchanged; the pre-trial tag is `stage4-before-recap-tradeoffs-20260925`.

**Current main Room flow:** open Room, edit the three role dropdowns, Commit.
No Reveal gate or With/Without controls. Revise reopens the choices. The main
projection fades invasives through two smooth clearance/return cycles in ten years.
Recap I uses a paragraph beside a larger, tightly framed interactive graph.
See [the latest checkpoint](../../chronology/2026-09-24-cooperation-graph-space-and-two-cycles.md).
The prototype workflow described below retains its Reveal/comparison controls.

**Latest main-game update:** [Debt, Projection and Recap I](../../chronology/2026-09-24-cooperation-debt-and-projection.md).
Main `/round.html` now has per-role room dropdowns, debt permission and one
committed landscape projection. Native restoration, repeated unplanted removal
and coffee growth all move together. Grazing includes first-season fire; other
choices have a Fire slider. Every main ignition is C. Recap I plots ten-year
earnings versus forest-health change before fire. The comparison endpoint keeps
its old controls. Historical play findings below refer to the earlier prototype.

Originally an isolated experiment. Now integrated into main Cooperation at
`/round.html`, using the main game’s unmodified RoundForest renderer. The separate
page keeps its prototype renderer for comparison. Combined is unchanged.
Negligence is hidden by default; `?negligence=1` restores the archived two-team
sequence. See [integration notes](../../chronology/2026-09-24-cooperation-community-integration.md).
Baseline before this prototype: `67ee3fb` on `stage4_recap`.

Open **http://100.82.28.38:8024/round.html** for the integrated game.
The comparison preview remains at **http://100.82.28.38:8036/community-cooperation/**.
Both Stage 4 processes were refreshed for the integration; other stages were
left running. The normal `./run.sh` includes the integrated game and routes.

## Play

The default page is a host session starting in the Community role. Choose A,
B or C and Propose. Use the Role dropdown to play Ecologist and Removal.
Finally choose Shared plan, Reveal plans, resolve any disagreement and Commit.

For a room, open Teams and give each group its role-specific link. Proposals
remain private until the host reveals them. Each group can revise its own
proposal during discussion. The host cannot commit incompatible land uses.
Debt is now permitted. Revise plan reopens discussion after the fire comparison.
New room makes an independent session; it does not erase other teams' rooms.
Rooms live in server memory, expire on restart, and are limited to 64.

For fire review without proposals, open **`/community-cooperation/#fire=1`**.
The **Review fire** link in `/community/` and in the prototype opens it in a
separate tab. Scrub the fire slider or Run fire. Compare Current forest with
Restored C, and choose an ignition in C or the neighbouring field. This review
creates no server room and cannot change an existing proposal. Recovery assumes
continued care, not an immediate fire barrier after planting.

No extra livelihood menu: each of the same three squares has one community
opportunity. Investment is numeric; return and forest health are qualitative.

| Square | Community proposal | Dependency |
| --- | --- | --- |
| A | Native nursery, investment 2 | Raise the planting mix for A. High return only if restoration is ordered for A. Nursery production is off-map, not a competing land use on the restored square. |
| B | Coffee under mixed shade, investment 6 | Low early return. Later prospects depend on surrounding shelter. B cannot simultaneously be native restoration and a coffee plot. |
| C | Existing pasture grazing, investment 1 | Burn old pasture growth; regrowth replaces bought cattle feed during the season. C cannot simultaneously remain pasture and become native restoration. |

No cattle purchase, lease system, prescribed-burn menu, additional mission,
sensor layer or new Combined mechanic was added. Grazing benefit is avoided
feed expenditure, not instant livestock sales. It is a fixed short-scenario
benefit, not a promise about real pasture performance.

## Accounts and consequences

The shared pot starts at 4 credits: the existing 2-credit project grant plus
the community's 2 credits. Removal retains the original candidate costs and
returns. Restoration retains original costs and the shared-clearing saving.
The community investment is then charged. Negative balance is debt, not a block.

Nursery payment is part of the restoration purchase, not new money minted for
the shared pot. An unmatched nursery order can be committed but is explicitly
shown to have no buyer or return. Feed savings and future coffee earnings do not
fund today's planting. Returns are not turned into a second wallet in this v0.

Coffee prospects improve if neighbouring C is restored; removal in C without
restoration exposes B. Its establishment has no harvest income before scenario
year 3. These are qualitative dependencies, not calibrated yield estimates.
Fire entering B changes the harvest explanation to warn that it is at risk.

Shared review shows numerical project accounts and a forest-health score.
The community's own survey screen never shows numerical return or health.
Health is the existing restoration/removal score minus 0.8 per simulated hectare
burned. This penalty is a game balance choice, not a measured ecosystem response.

## Fire and visual consistency

`model.mjs` builds a 60 x 60 fuel field from a coarse scenario invasion front,
interpolated cover and fixed spatial variation. Measured canopy heights make a
small shelter adjustment. There is no narrow ellipse or drawn fire path.
The scenario is still deliberately designed so C is an important connection.
It is not an inference that the scanned real landscape contains this corridor.

C's west/east neighbours, E3/E5 (ids 26/28), have no invasive species in the
prototype inventory. Ground moisture, plant lists, the Pokedex dispersal map
and the fire field agree about these flanks. Other openings carry the invasion
northward. Players can click surrounding plots, not just the A/B/C buttons.

The renderer retains dense measured airborne/TLS fragments and the normal
point-cloud navigation. Original height colours are preserved: pink low, blue
middle, green high. Fuel does not recolour the LiDAR. Close inspection, the plant
inventory and short survey clues reveal the fuel differences instead.
The old RoundForest narrow notch is disabled in this subclass. A small ignition
grows into an irregular front; bright points cool to a muted scar. Both WebGL
and software Canvas paths support exploration, close view, recovery and fire.
TLS still uses modelled arrangements of scan fragments, not a surveyed pasture
or species-resolved scan. Coffee is an economic/ground-fuel treatment here;
this prototype does not claim to render a measured coffee plantation.

Grazing starts the scenario ignition in C. Other choices are tested against an
ignition at a nearby field, id 33. Within each Without work / Shared plan pair,
the ignition and weather are identical. Across community choices the ignition
location differs, so those outcomes do not isolate vegetation effects alone.
The recovery slider changes fuel/moisture and recomputes spread, not only visuals.
The model is the existing educational Rothermel-style propagation on a new field,
not a historical NBR scar or a predictive wildfire tool. Maturity assumes care.

The revised run lasts 20 simulated minutes with a fixed northward wind. Fuel
and treatment effects blend across plot edges; there is no hard square-shaped
fuel cap. Damp flanks can carry a little native-litter fire without containing
invasive grass. Forward spread dominates, with limited lateral and backward
spread. The wind parameter is opt-in; other missions retain their old wind rule.

Close-view labels now keep fixed-size text and short leaders in all inherited
views. Crowded labels hide rather than stack into tall poles as the camera pulls
away. The existing plant list still contains every species available to inspect.

## Findings from actual UI play

1. Community C + ecology C conflicts immediately. This gives the room a concrete
   land-use decision instead of letting incompatible benefits stack.
2. Removal A + ecology C + community B is affordable with **1 credit left**.
   At year 10 the paired fire is **4.88 ha**, versus **20.00 ha** without work.
   At year 0 more burns: choosing restoration does not instantly create shelter.
3. All A funds a nursery order and leaves **7 credits**, but fails to interrupt
   the edge connection. Its year-10 fire is **20.00 ha**.
4. Ecology A + removal B + shade B has a shortfall. The original prototype
   blocked commitment; the latest version permits debt instead.
5. Ecology B + nursery A can be affordable but produces no nursery order.
6. Ecology/removal A + grazing C leaves **8 credits** but the fire escapes C;
   projected burn area is **17.87 ha**. Feed savings do not protect the forest.

These are deterministic scenario comparisons, not effectiveness estimates or
evidence that people find the game fun. Browser play makes the intended dilemma
legible; a facilitated group session is still needed to judge discussion quality.
No multi-agent player session or human workshop is claimed for this prototype.
These figures use the revised 20-minute scenario. The original 32-minute trial
and its previous figures remain recorded at checkpoint `fb94232`.

Iterations after screen inspection/play:

- Fixed simultaneous independent proposals so a stale room revision is refreshed
  and safely retried only when that team's choice and the phase are unchanged.
- Changed a fully orange burn footprint to a bright front with muted older scar.
- Made forest health fall with burned area and fruit prospects respond to fire.
- Fixed Without work narration so it does not claim planned shelter exists.
- Passed the local inventory into the existing Pokedex grid hook; no shared
  species-panel code needed alteration.
- Checked 1280 x 800 and 1440 x 1000 layouts, private team links, reloads and the
  software-rendered path with WebGL disabled.

Screenshots are outside git in
`/mnt/seagate/models/pyrocene/stage4/qa-community-cooperation/`.
Useful captures: `choice-B.png`, `choice-C.png`, `land-conflict.png`,
`pasture-close.png`, `flank-survey.png`, `grazing-small-ignition.png`,
`grazing-spread.png`, `without-work-fire.png`, `restored-connection-fire.png`,
`software-close.png`, `software-fire.png`.
Latest review/zoom captures: `review-current-forest.png`, `review-restored-C.png`,
`close-wide-no-stilts.png`, `expedition-wide-no-stilts.png`.

## Verification

```sh
python3 -m unittest stage4.community_cooperation.test_store stage4.community_cooperation.test_play -v
node --test stage4/community_cooperation/test_model.mjs
python3 -m unittest stage4.test_delivery stage4.test_shared_round -v
python3 -m stage4.serve --check
python3 -m stage4.serve --host 0.0.0.0 --port 8036
```

Most implementation stays in this directory. Shared changes are server routing,
the independent room store instance, portable-package inclusion, the optional
wind argument and the Close-view label fix. The old Community page also links
to fire review. The three-role controller now powers main Cooperation through `cooperation.mjs`.
The main shell retains role briefings, structure, Recap and A/B/C previews.
Old two-role rooms remain in their original store; no saved-game migration is
performed. Revert scoped commits to remove this experiment;
never reset unrelated user edits.

## Sources and limits

- [Embrapa: pasture management and fire](https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/403419/1/OrientalDoc83.pdf).
  Supports the pasture-maintenance story and repeated-burning/escape concerns,
  not guaranteed fodder savings or safe burning in this setting.
- [WeForest and IDESAM: coffee with native trees](https://www.weforest.org/programmes/special-projects/apui/).
  Supports the specific crop and degraded-pasture restoration setting. The
  cost, year-3 threshold and neighbouring-C effect are scenario choices.
- [Amazon Fund: Sementes do Portal](https://www.fundoamazonia.gov.br/pt/projeto/Sementes-do-Portal/).
  Supports seed/seedling purchases and dependence on restoration demand.
- [Silvério et al.: grass invasion and Amazon fire](https://pmc.ncbi.nlm.nih.gov/articles/PMC3638439/).
  Supports the grass/fire/edge feedback, not these exact plot assignments.
