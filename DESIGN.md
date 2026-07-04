> **Note (v0.2 pivot):** the implemented terminal engine is **invasives-first**, not
> fire-first. Fire is now a rare, dramatic consequence of letting invasives go dense;
> the star metric is native cover, the cost is one team action per turn (no money), and
> hindcast/ANR are cut. The authoritative spec for the built engine is
> [ENGINE_SPEC.md](ENGINE_SPEC.md). The notes below are kept for the earlier fire-first
> framing and general philosophy.

# PYROCENE — Design & Playtest Spec (v0.1)

A cooperative ecological-resilience game. This doc supersedes the thesis in `PLAN.md`
and pins the numbers so the game is actually playable and testable. First build target:
an **online single-session version with a deterministic rule agent** standing in for the AI /
game master. Audience for v0.1: teens and adults (get the dynamics right, "quantize" for
younger kids later).

---

## 1. Thesis (what the game teaches)

Ordered by importance — the design must make #1 the thing players *feel*:

1. **Neither role wins alone.** The Ranger is blind without the Ecologist's data; the
   Ecologist is unreliable on a single data source and must **cross-correlate** community
   knowledge + remote sensing + history before the Ranger can act cheaply and correctly.
2. **Data collection has real cost, and it competes with action.** One shared budget funds
   both learning and doing. Spend it all learning and the score bleeds; spend it all acting
   blindly and you go bankrupt.
3. **Urgency forces holding actions.** Fire lines / suppression / evacuation buy *time* but
   never fix the cause. They are a clock, not a strategy. The escape hatch is converting data
   into cheap systemic fixes (invasive clearing, ANR restoration).
4. **Fire is a hazard, not the moral.** Fire is just the most legible way to pull the
   Ecological Health Score down. The named *causes* players must uncover are **fuel load**
   (fallen leaves/deadwood), **invasive species** (volatile), **moisture**, and **weather**
   (wind). Floods etc. can be added later as new hazards reading the same landscape variables.
5. **"Good fire" is one ironic turning point** — important, but not the headline.

Design constraint from #1: **no single data source may ever be sufficient to act well under
budget.** Each source has a blind spot only another fills (see §4).

---

## 2. Architecture (kept modular for future hazards)

Four separable layers:

- **Landscape variables** (hidden): fuel, vegetation, moisture, asset, ridge-trait.
- **Hazards** that read those variables: *fire* now (reads fuel + invasive + moisture + wind).
  Flood later would read moisture + slope + drainage — a new hazard, not a rewrite.
- **Data sources** (Ecologist): how variables get revealed.
- **Actions** (Ranger): how variables get changed.

---

## 3. Board & core numbers

- **Grid:** 6×6 = 36 squares.
- **Session:** fixed **6 turns**. (Full/classroom mode can use the sustain-90 rule later.)
- **Ecological Health Score (EHS):** starts **75**.
  - **Lose (Collapse):** EHS < **50** at any time.
  - **Win (Resilience):** finish turn 6 with EHS ≥ **75**. **Gold (True Resilience):** ≥ **90**.
- **Budget:** **10 per turn**, shared. Unspent budget does **not** carry (use it or lose it).
- **Community clue:** once per turn.

Per-square hidden variables:

| Variable   | Values           | Role in engine |
|------------|------------------|----------------|
| fuel       | 0–3              | drives ignition + spread |
| vegetation | native / invasive / barren | invasive = +volatility; native = worth protecting |
| moisture   | 0–3              | resists ignition + spread |
| asset      | village / none   | ~3 villages; burning one is catastrophic |
| ridge      | true / false     | hidden trait tied to the community clue (wind exposure) |

Rough generation: ~7 invasive squares, ~6 ridge squares, ~3 villages, fuel/moisture random.

---

## 4. Data sources (Ecologist) — each has a blind spot

| Source        | Cost | Reveals | Blind spot |
|---------------|------|---------|------------|
| Satellite     | 1 | Coarse **risk** rating over a 3×3 region | no specifics, no *why* |
| Drone         | 2 | **Fuel + vegetation** for a 2×2 cluster | no moisture, no timing |
| Forest Survey | 3 | **Everything** on one square | expensive; one square |
| Community     | 1 (1×/turn) | A causal **rule** ("ridge squares ignite on a north wind") | not *which* squares, not current load. **Rarely untranslatable** — recoverable later via a community-relationship investment (planned) |
| Hindcast      | 2 | One square's **history**; if invasive, the native that belongs there → **unlocks ANR** | history only |

The intended "aha": **community tells you *when/why*, sensing tells you *where/how-bad*,
history tells you *what to restore*.** A weather **forecast** is shown at each dawn so the
community rule becomes actionable next turn — triangulate forecast + community + sensing.

Flags: the Ecologist may flag/unflag any square (free) as a shared annotation.
(Two-player rule, deferred in solo build: the Ranger must spend an action — "radio
consultation" — to learn *why* a square is flagged.)

---

## 5. Actions (Ranger)

Holding actions (expensive, buy time):

| Action | Cost | Effect |
|--------|------|--------|
| Fire line | 3 | Blocks fire spread into/out of a square |
| Suppress / Evacuate | 4 | Protects a village from active fire this night |

Systemic actions (cheap, fix the cause — but require data):

| Action | Cost | Requires | Effect |
|--------|------|----------|--------|
| Prescribed ("good") fire | 2 | — | Burns off fuel. **Contained** (all neighbors are fire-line/edge/low-fuel/water) → **Good Fire: +10 EHS + budget bonus**. Not contained → it escapes like a wildfire. |
| Invasive clearing | 2 | vegetation identified as invasive on that square | Removes invasive → lowers ignition permanently |
| ANR restoration | 2, over **2 turns** | hindcast done on that square | Converts to resilient native patch → **+15 EHS** |

---

## 6. Night simulation (the rule agent)

Deterministic given a seed + turn (reproducible for tuning), escalates gently:

1. **Weather:** wind direction (N/E/S/W) + strength (0–2), rain (occasional). Rain suppresses
   ignition and temporarily raises moisture. Next night's forecast is shown at dawn.
2. **Ignition:** the agent ignites the highest-risk *unprotected* square, plus ridge squares
   whose exposed side faces the wind (this is exactly what the community clue describes).
   `risk = fuel + invasiveVolatility + windExposure − moisture`.
3. **Spread:** each burning square spreads to a neighbor when
   `spread = fuelₙ + invasiveₙ(2) + windAlign(0–2) − moistureₙ − fireLine(block) ≥ threshold`.
   Runs a few iterations, capped.
4. **Prescribed burns** resolve here (contained → good fire; else escapes).

### Dawn scoring (EHS deltas)

| Event | Δ EHS |
|-------|-------|
| Village burned | −20 |
| Native patch burned | −10 |
| Barren burned | −3 |
| Uncleared invasive present | −1 each / turn (cap −6) |
| Good Fire (contained prescribed burn) | +10 (+budget bonus next turn) |
| ANR completed | +15 |

Budget bonus from a Good Fire: **+4** next turn.

---

## 7. The provocateur's job

The agent doesn't optimize to win; it surfaces lessons. It preferentially ignites
**unmonitored** sectors (punishing pure reaction) and lets **unmanaged invasives** spread and
raise risk (punishing blind action). Early turns are mild; wind builds later so a team that
banked data and did ANR is rewarded, and a team that only dug fire lines runs out of money.

---

## 8. Turning-Point debrief

On win or loss, replay the run and name the single decision that mattered most (e.g. "Turn 3:
a north-wind night was forecast and the ridge was flagged, but no fire line went in") and tie
it to the real-world lesson. Generated from actual board events, not a fixed script.

---

## 9. Build status

- **v0.1 (this build):** online, solo, deterministic rule agent. One player operates both role
  consoles sharing one budget — enough to test thesis #1–#4. Cute/teen visual identity.
- **Next:** GM (human) mode reusing the same board/rules; then two-player comms barrier; then
  additional hazards (flood); then "quantize" copy + difficulty for younger kids.
