# Community player findings

CLI smoke tests (2026-09-21, read-only):

- Cursor `agent --print --mode ask --model gpt-5.3-codex-low` authenticated and ran. It checked the workspace and reported that the Community engine was not yet present at that time, so it made no play trace.
- Claude Code `claude-sonnet-5-low` was rejected as unavailable. The `haiku` alias is accepted for a one-sentence read-only smoke test, but the requested playtest invocation hung without output (stopped after the timeout). No Claude play trace is claimed.

Engine play traces below are an **early model snapshot** (after the owner corrected the initial inactive-forest fixture), not the tuned browser build. They used seeds 113, 227, and 991 with Shade enterprise. The scenario was E9/F9 buffer, E8/F8 native restoration, E10/F10 boundary ignition.

- impatient expander: restore/expand quickly, then partner buffers only when forced;
- steward: partner the E9/F9 buffer, tend manually, and preserve a care buffer.

Agroforestry shade/tending is treated as risk reduction, not a firebreak or guaranteed restoration; nursery income remains local care funding rather than infinite player credits.

### Actual legal policy traces — early snapshot

All actions below were executed through `quote` → `act`; each action advances six months.

| persona/policy | 113 | 227 | 991 |
| --- | --- | --- | --- |
| wait every turn | 0/2 target closures, 77 burned, 23 fires | 0/2, 57 burned, 11 fires | 0/2, 71 burned, 23 fires |
| manual native care (`remove:E8/F8` alternating; then wait after invalidation) | 1/2, 74 burned, 0 credits | 0/2, 46 burned, 0 credits | 1/2, 69 burned, 0 credits |
| steward buffer (`partner:E9`, `partner:F9`, then native care) | 1/2, 1 active buffer, 33.75 local care, 76 burned | 0/2, 2 active buffers, 58.05 care, 41 burned | 1/2, 0 active buffers after fire loss, 54 care, 68 burned |
| impatient expander (repeated legal `remove:E10`, then wait) | 0/2, 73 burned | 0/2, 48 burned | 1/2, 69 burned |

The steward policy did not dominate: it reduced burned plots on seed 227, but both targets still failed there; seed 991 lost both community partnerships to fire. Shade reached canopy cap on surviving buffers, yet those plots remained agroforestry rather than native closure.

The same steward action sequence with the nursery enterprise produced target closures `1/2`, `0/2`, `1/2` on seeds 113/227/991, with 70/39/66 burned plots and 2/2/2 active buffers at the end. Nursery’s lower canopy cap still reduced some burn totals, but it did not make the native goal reliable in that snapshot.

### CLI persona interaction

Cursor `gpt-5.3-codex-low` did return choices when given observation summaries (no tool access in ask mode). Its impatient-expander choices on seed 113 were `[remove:E10, remove:F10, partner:E9, partner:F9]`; `remove:F10` was rejected at the occupied-commitment cap, while the other three were legal. Feeding back the resulting state, it chose `[remove:F10, remove:E10, wait, wait]`; `remove:F10` remained rejected, `remove:E10` was legal but only weeded the already-cleared plot, and the two waits let E8/F8 reinvade. At turn 6: 0/2 targets, 50 burned plots, 4 fires, 2 active buffers. This is a concrete early-snapshot warning: chasing boundary clearance and waiting spends seasons while native care is deferred.

Claude Code’s `haiku` alias is recognized (a one-sentence smoke test succeeded), but both the full steward prompt and a minimal JSON-only choice prompt timed out after 20 seconds with no response. No Claude action choices are claimed; the deterministic steward traces above are the fallback.

### Rules/feedback findings

- The initial observation exposes only six scenario plots (E8–E10/F8–F10); all other plots are `unseen` and say “Crew cost 1; return unknown.” A novice can identify the marked strip without inspecting the full map, but the generic unseen rows make the occupied landscape feel larger than the actionable scenario.
- The starting ledger has four open commitments (cap five). A legal `remove:E10` opens a fifth commitment; the immediate legal quote for `remove:F10` then says: “Five open commitments already exist. Restore or wait for one to resolve.” This is a clear occupied-slot pressure point, but the UI should explain why the four preloaded commitments consume capacity.
- At turn 0, `restore:E8` is invalid (“RESTORE only plants a cleared plot.”) because E8/F8 are already young native plantings. The useful care verb is `remove`, which costs one credit and returns zero; this is easy to misread as destructive removal.
- Waiting burns the scenario quickly (seed 113: E9/F9 reinvade by turn 4; target 0). Partnering improves some runs, but buffer failure and target failure remain possible. The copy should keep saying “slows/reduces risk,” never “protects” or “firebreak.”

## Resolved construction blocker (for provenance)

The first direct engine probe found a construction error before any action could be legal:

```text
TypeError: Cannot convert undefined or null to object
    at prepareFixture (stage4/community/model.mjs:178:12)
```

The first engine revision tried to assign inactive E11/F11 (`[58,70]`) and threw before any action. The owner changed the fixture to active forest-side shelter E7/F7 (`[54,66]`); `newGame(113,{enterprise:'shade'})` then constructed and the early-snapshot traces ran. Cursor’s low-model persona also supplied two legal action batches from observation summaries; those choices and outcomes are recorded above.

## Current tuned-build check

The parent’s browser play on the current tuned build (seed 991) found a successful buffer route: both paid buffers were visible with grass at least 30%, local care recovered, and both native targets closed by year 3.5; 5 credits remained. This is a browser result, not a CLI trace. A matched native-care-without-buffers route reached only 1/2 after year 12 with 3 credits, because F8 repeatedly burned.

Changes reflected in the tuned UI/mechanics:

- Native care is labeled **Weed**, clarifying that it is tending rather than destructive removal.
- Working buffers stay on the ledger until established, making the commitment state legible.
- Local enterprise income pays local care first; it is not an unlimited player-credit source.
- Completion offers avoid forcing roughly 17 empty turns after both targets are already closed.
