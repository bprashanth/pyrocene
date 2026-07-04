# Pyrocene Engine Contract (v0.2, invasives-first)

This is everything a **UX layer** (human-built or agent-built) needs. The engine
owns all dynamics; the UX owns all presentation. They meet at four functions and
three JSON schemas. **A UX must never import `engine.rules` or read hidden cell
truth. It only calls the API below and renders what `observable()` returns.**

```
        ┌─────────────────────────┐        ┌──────────────────────────┐
        │  engine/ (pure logic)   │        │  ux/ (any language/tech) │
        │  rules, spread, fire,   │  JSON  │  terminal, web, mobile…  │
        │  scoring, fog of war    │◀──────▶│  render view + events    │
        └─────────────────────────┘        └──────────────────────────┘
             new_game / apply / observable / legal_actions
```

## The one rule that makes it a game

**One team action per turn. Applying that action also runs nature's turn.** The
turn *is* the cost. There is no money. Looking (satellite/drone/survey/clue) and
acting (remove/restore) draw from the same single-action budget, so every turn is
a choice between seeing and doing while the invasion spreads on its own.

## Public API (`from engine import ...`)

| Function | Signature | Notes |
|---|---|---|
| `new_game` | `(config: dict\|None, seed: int\|None) -> State` | `config` overrides `content.DEFAULT_CONFIG`. Deterministic per `seed`. |
| `legal_actions` | `(State) -> list[dict]` | The action catalogue (empty once the game ends). Render these as buttons/menu. |
| `apply` | `(State, action: dict) -> (State, list[event])` | Runs the team action **and** nature's turn. Returns a **new** state (input unmutated) plus the events to animate. |
| `observable` | `(State, role="team") -> dict` | The fog-of-war view. **This is the only thing the UX renders.** |
| `to_dict` / `from_dict` | `(State) <-> dict` | JSON round-trip for saving / sending over a wire. |

`role` is reserved for the two-player split (`"ecologist"` / `"ranger"` can each
get a filtered view later); `"team"` returns the shared view used by the solo
build.

## Action schema

```json
{ "type": "drone", "target": 87 }
```

`target` is a **cell index** (`r * cols + c`) for `target: "cell"|"area"` actions,
and absent for `target: "none"`. Area actions anchor a square at that index
(clamped to the board).

| type | kind | target | effect |
|---|---|---|---|
| `satellite` | look | none | Whole map to obs level 1. Cannot resolve seedlings/established (they read as native). |
| `drone` | look | area | `drone_size`² block to obs 2. Exact stage, including seedlings. |
| `survey` | look | cell | One cell to obs 3 (full truth incl. corridor). |
| `clue` | look | cell | Ask the elders about a patch. Emits a `clue` event with **method advice** (or points to the nearest outbreak with a compass bearing). Returns `nonsense: true` until the translator is unlocked. Persisted in `journal`. |
| `dss` | look | none | Run the DSS: emits a `dss` event translating landscape covariates into **risk zones** with an explanation. Unlocks at level 4. |
| `remove` | act | area | `work_size`² block: invasive → bare. Dense leaves a seed bank. |
| `restore` | act | area | `work_size`² block: bare → native (clears seed bank). |
| `burn` | job | area | **Starts** a controlled burn on a `burn_region`² stand. Illegal next to a village / with no invasive. |
| `crew` | job | area | **Starts** a multi-night hand-clear of a `crew_region`² stand. |
| `pass` | act | none | Do nothing; nature still moves. |

**Multi-turn jobs.** `burn` and `crew` occupy the team's single action for several
nights (the whole point: while committed you can't respond elsewhere, and the
invasion keeps moving). While a job is active, `legal_actions` returns **only**
`continue` (carry on / dig lines / wait), `ignite` (light a lined burn — only when
`job.ready`; safe when `wind_str <= burn_safe_wind`, otherwise it escapes into a
wildfire), and `abort` (cancel, losing progress). Any other action sent while a
job runs is coerced to `continue`.

## Event stream (what `apply` returns for the UX to animate)

Events are plain dicts, ordered. The UX decides how to show each; the engine
never assumes a renderer.

| event | fields | meaning |
|---|---|---|
| `scan` | `source`, `area`, `detected?` | A look happened. `detected` lists `{cell, stage}` for drones — draw the detection markers. |
| `clue` | `text` | Qualitative clue to surface. |
| `remove` | `area`, `removed` | Cells cleared (0 ⇒ wasted turn). |
| `restore` | `area`, `planted` | Cells replanted. |
| `advance` | `cell`, `stage` | An invasive matured (seedling→established→dense). |
| `spread` / `regrow` | `cell` | A new outbreak (fresh spread / seed-bank resprout). |
| `fire` | `igniter`, `cells` | A wildfire; `cells` is the burn set — animate the sweep, then they become bare. |
| `job_start` | `job`, `cells` | A burn or crew job began. |
| `lining` / `lines_ready` | `left?` | Burn: digging fire lines / lines complete, ready to ignite. |
| `waiting_wind` | `wind_str` | Burn is lined and holding, waiting for a calm night. |
| `controlled_burn` | `cells` | A successful prescribed burn (stand → bare, modest cost). |
| `burn_escape` | `cells` | A burn jumped its lines and became a wildfire. |
| `crew_work` / `crew_done` | `cleared`, `remaining` | Crew progress / stand fully cleared. |
| `job_abort` | `job` | A job was cancelled. |
| `village_fire` | `villages` | Fire reached homes — heavy wildlife hit. |
| `wasted` | `reason` | The action accomplished nothing. |
| `score` | `health`, `wildlife` | End-of-turn readout. |

## View schema (`observable` output — the render target)

```jsonc
{
  "cols": 22, "rows": 12, "turn": 3, "max_turns": 14,
  "status": "playing",           // playing | win | gold | lose
  "lose_reason": "",
  "wind": "N",                    // N|S|E|W, biases spread + fire
  "wind_str": 1,                  // 0 still · 1 breeze · 2 strong (gates safe burns)
  "health": 84,                   // NATIVE COVER % — the star metric
  "wildlife": 71,                 // secondary consequence; gates the gold ending
  "fire_risk": "low",            // low|med|high, from KNOWN dense outbreaks
  "known_invasive": 5,
  "thresholds": { "win": 60, "gold": 80, "collapse": 40 },
  "unlocks": { "level": 4, "satellite": true, "drone": true, "survey": true, "translator": true, "dss": true },
  "job": { "type": "burn", "cells": [..], "lining_left": 1, "ready": false },  // or crew {..,"remaining":n}, or null
  "journal": [ { "turn": 3, "text": "The elders point toward the north-east: ..." } ],
  "map_meta": { "orthomosaic": null, "bounds": null },   // orthomosaic hook (below)
  "cells": [
    { "index": 0, "r": 0, "c": 0,
      "known": false,             // false ⇒ unscanned land (fog)
      "cover": "unknown",         // unknown | native | invasive | bare | water | village
      "stage": 0,                 // 1 seedling · 2 established · 3 dense (invasive only)
      "detail": 0,                // observation level: 0 unseen · 1 satellite (rough) · 2 drone · 3 ground. Render 1 as low-confidence.
      "bank": true,               // river-bank / corridor cell (fast spread), visible from the map
      "fireline": false,          // a dug fire break (visible; blocks fire, not weeds)
      "hill": false, "road": false, // landscape covariates, revealed once satellite-scanned
      "risk": 0,                  // DSS risk score (>0 only when DSS unlocked + scanned); >=2 is a risk zone
      "monitored": false,         // DSS is surveilling this risk zone (sees through the satellite blind spot)
      "last_seen": -1 }
  ]
}
```

**Fog model the UX must respect (it's already applied in the view):**
- Terrain is a basemap: `water`, `village`, `bank`, and `fireline` are always visible.
- Land cover is hidden until scanned (`known: false`, `cover: "unknown"`).
- Satellite's blind spot is baked in: a satellite-only cell reports seedling/
  established invasion as `native`. Only a drone/survey reveals early stages.
  This is the whole lesson, one cheap coarse look is not enough.

## Extending without touching dynamics

- **New map / real orthomosaic:** produce a `State` with your own `cells` and set
  `map_meta = {"orthomosaic": "<tile ref>", "bounds": [...]}`. Cell `(r,c)` maps
  to an image tile; the UX overlays detection circles from `scan.detected`. The
  engine already ignores imagery, so a web UX can bind pixels to `cell.index`.
- **New hazard (e.g. flood):** add a step function in `engine/rules.py` reading
  existing cell fields and emit a new event type. UX renders the new event; no
  API change.
- **Tuning:** every number lives in `engine/content.py::DEFAULT_CONFIG`. Pass a
  partial `config` to `new_game` to override. Balance target (measured): neglect
  loses ~100%, informed play ~65%, perfect play ~100%; fires ≈0 when well managed.

## Determinism

`apply` derives its RNG from `(seed, turn)`, so a `(seed, action-sequence)` pair
always reproduces the same game. Good for tests, replays, and shared puzzles.
