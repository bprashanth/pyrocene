# Pyrocene — event build, narratives, and roadmap

## Where the game is now (branch `dss-unlock`)

The game is an **invasives (lantana) management** game. You inherit a degraded
landscape and a few persistent **hotspots** (seed sources that keep reseeding).
The win is a **restored landscape**: get **native forest cover back above the
target (default 84%) and hold it for N consecutive nights** — one number on the
Forest bar, ecologically sound (you can't eradicate lantana; you keep its
strongholds cut back so the forest recovers and holds). You lose if cover
collapses (<40%), wildlife hits zero, or the season ends before you hold it.

The hotspots are the *strategy* (where to cut, revealed by the DSS), not the win
itself — an earlier "control the hotspot cells" win was scrapped because you could
satisfy it while the wider landscape stayed invaded.

### Level design (the intended arc)

The levels are a deliberate learning curve — **you progressively lose by less**
until the DSS lets you win, then disasters raise the ceiling:

| Level | You get | Intended outcome |
|---|---|---|
| 1 | satellite only | **lose** — blind to seedlings, but you glimpse the shape of it |
| 2 | + drone / survey | **lose by less** — you can find some, but not keep up |
| 3 | + translator (ask elders) | **lose by less** — advice helps, still can't hold |
| 4 | + **DSS** | **win** — the DSS tells you which hotspot to clear each night |
| 5 | + **telegraphed disasters** | **the real test** — extra variables to juggle |
| 0 | everything (sandbox / testing) | — |

So 1→3 teach the value of each data layer by making you feel its absence; **level
4 is where people win, via the DSS**; **level 5 introduces disasters** on top.

**Telegraphed disasters are level-5 only** (config: `events_on`, gated in the
level-5 preset). Restricted for now to **grazing, drought, monsoon** — announced
1–2 nights ahead, each grounded in real lantana ecology with a field-note card:
- **grazing** → a new outbreak on churned ground
- **drought** → more fire, no regeneration, harder reseeding
- **monsoon** → seeds wash onto the banks (but dampens fire)

The monsoon/drought field notes double as **strategy** — knowing the ecology is
the edge that separates casual play from a true fan. (The `work_party` boon is
built but held out of the level-5 deck for now; revisit whether to add more
variables — floods, fire-as-tool, invasive-as-livelihood — after playtesting.)

Balance (bots, restore-and-hold win): levels 1–3 ~27% (mostly lose); level 4 ~60%
(the win level, via the DSS); level 5 ~46% (harder — same game + disasters).
Passive ~11%. Caveat: the bot is a fixed strategy, so 1–3 look flat and win a bit
by luck; a *human* who can't drone (L1) or can't track everything (L2–3) fares
worse, and the DSS at L4 is what makes it reliably winnable. The engine now
enforces the unlock gates (drone/survey/dss), so the levels are real.

## Field-note sources (verify before any public display)

The in-game field notes are drawn from these; keep them accurate for the event.

- Lantana has invaded **>40% of India's tiger range (~300,000 km²)**; Shivaliks,
  Central India, Southern Western Ghats worst hit — [Mongabay India](https://india.mongabay.com/2020/08/lantana-invasion-threatens-40-percent-of-indias-tiger-habitat-reports-study/)
- **Drought (2000) → intense fire (2002) → lantana boom**; disturbance (mild fire,
  cutting, pruning, grazing) triggers it, and it in turn feeds fire; management is
  **cut-rootstock / uprooting + weeding + restoration** — [GBPIHED/Springer, "Ecology and Use of Lantana camara in India"](https://gbpihed.gov.in/PDF/Publication/Springer_Use_of_lantana_camara.pdf), [Corbett restoration case](https://www.academia.edu/4215825/Ecological_Restoration_of_Lantana_infested_area_Corbett_Tiger_Reserve)
- **Keystone Foundation** (Kotagiri, Nilgiris, since 1993): works with Adivasi
  communities; field-tested control = uprooting woody invasives (lantana, Acacia
  mearnsii, etc.), community-made organic weedicides, weed mats, traditional
  controlled fire; native-species nurseries — [Keystone Foundation](https://keystone-foundation.org/evaluating-local-practices-for-invasive-plant-control-in-the-nilgiris/)
- **Farmers for Forests** (Pune, 2019): pays farmers to keep/restore native tree
  cover, **tracks tree health with drones** (ties straight to the game's drone) — [farmersforforests.org](https://www.farmersforforests.org/)
- **NCF** native-tree restoration with local farmers — [ncf-india.org](https://www.ncf-india.org/eastern-himalaya/growing-native-tree-species-for-forest-restoration-in-north-east-india)

Lantana-as-livelihood (craft/furniture) and "The Lantana Collective" are further
real threads worth a future event/boon.

## Roadmap (deferred, in priority order)

1. **AI game master (true-fan layer).** The engine already exposes a clean
   **event stream + `observable()` view** — the seam an LLM would consume. An LLM
   could generate dynamic, situation-specific narration, an adaptive difficulty
   "provocateur", and the original "turning-point debrief". *Not wired up* (no
   live model calls in this build); a good local Cursor-agent task. Keep it as a
   layer that reads events and writes narration, never touching the dynamics.
2. **Expanded board for level 5+.** Real ecologists want a bigger map. The blocker
   is the terminal layout: the character panel sits *beside* the 22-wide board and
   a bigger board overflows 80 cols. Fix = a width-aware layout that stacks the
   panel *below* the map on large boards, then crank `cols`/`rows`.
3. **Two-player co-op.** Most sacrificable, but scaffolded: the ecologist/ranger
   split and `observable(state, role)` already exist. Needs a per-role view (each
   sees their own info) and a turn/comms protocol.
4. **More disasters + real orthomosaic.** Storm (wind-burst spread), fire-as-tool
   season, invasive-as-livelihood boon; and binding a real drone orthomosaic to
   `map_meta` (the reveal/detection mechanic is built for it).

## Checkpoints

- `main` — the pre-DSS working game (known-good fallback).
- `dss-unlock` — DSS + resilience win + disasters + level 5 (this build).
