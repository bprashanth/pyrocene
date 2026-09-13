# Pyrocene Stage 2: Ignition

The in-person Mafia game with a forest map behind it. The room plays as they
already do. This mirrors the room onto a projected map, and adds fire.

Nothing here touches the live game at pyrocene.netlify.app. Stage 2 keeps its
own frozen copy of the engine under `stage2/engine/` and imports only that.

## Index

| Component | Where | What it is |
|---|---|---|
| Server | `server.py` | One HTTP server: phones, game master, projector, SSE, the replay routes |
| Game | `game.py`, `config.py`, `text/` | Board, spread, fire, trenches, the event log, every tunable, every sentence |
| Engine | `engine/` | Frozen copy of the live game's physics. Never re-pointed at the original |
| Projector drawing | `render.py`, `frames.py`, `maps/` | Live board rendering; six map styles with their own [readme](maps/README.md) |
| Pages | `static/` | `gm.html`, `phone.html`, `projector.html`, vendored xterm |
| Balance | `sim.py` | Whole games in memory, for tuning. Never runs at event time |
| Tests | `tests/` | 51 tests; `test_isolation.py` guards the live game |
| Event log | `logs/` | One JSON per game, written as it is played; the input to every replay |
| Post-game replay | `simulation/` | Two independent builds, not wired to a button at the moment. [Contract](simulation/SPEC.md), [fixture](simulation/sample-game.json), [`claude`](simulation/claude/README.md), [`codex`](simulation/codex/NOTES.md) |
| History | `../chronology/` | Dated notes on what was built, what went wrong and what is untested |

## Run it in a room

```bash
python3 -m stage2.server --stage 1     # plain Mafia, the map kept back
python3 -m stage2.server               # stage 2: fire and the one choice a night
python3 -m stage2.server --help        # --host --port --style --stage --seed --fast
```

It prints every address it answers on. Hand out the wifi one for phones in the
room; the others are for you.

1. Open the **projector** address on the big screen, full screen the browser.
2. Open the **game master** address on your own laptop.
3. Read out the **players** address. Everyone joins and types their name.
4. Press **Start game**. Roles appear on phones. Nobody else sees them.
5. Run the night as you always do. If lantana took someone, mark them, then
   press **Finish night**.
6. The projector puts up one card explaining what happened. Read it out, then
   press **Show what happened**. The board greys out except the squares that
   change, they turn over, and the whole map comes back. About four seconds.
7. Ask the room for their one choice: **hunt lantana** or **resilience**. Mark
   the vote if they hunted, then press **Finish vote**.
8. Card, show, card, show, through the vote, the spread and the fire. Repeat.

Rehearsing alone: press **Seed** to add fake players, then Start.

No internet needed. xterm.js is vendored, the rest is the standard library.

## Stage 1 first

`--stage 1` is the room's first evening. Plain Mafia, nothing else: no fire and
no nightly choice. The room plays as it would with a deck of cards and this app
only keeps score.

**The projector holds the night number and nothing else.** The board is kept
back on purpose, so the replay at the end lands as a reveal rather than as a
recap. After each night and each vote the console offers two buttons:

| Button | |
|---|---|
| Continue | Applies the round and shows nothing. Press this to keep the room moving. |
| Show what happened | Puts the card and the animation up, the same as stage 2. |

**It ends as plain Mafia ends.** Every lantana out, or every native out, or both
the ecologist and the ranger out. That last one is stage 1 only: with no fire
there is no way back, so the game stops rather than play out a foregone
conclusion. Stage 2 keeps going in the same spot, because a fire can burn
lantana back and turn a hopeless board around.

When it ends, press **Replay the map** and then **Next night** to walk the
forest forward one night at a time. No cards, no narration, just the land.

Through the whole of stage 1 the map draws a faint dashed boundary around the
ground each player started with. Those boundaries never move, so the room can
watch one shape change hands over the evening. That is the frame for the
explanation: a lantana patch cleared leaves bare ground, which can be taken
again, and a lantana patch left alone spreads past its own boundary into the
forest.

**In the replay, and only there, the night that took somebody puts their name
over their ground.** So when the room reaches night three and a stand has gone
bare, the name of whoever was voted out on night three is sitting on it. The
ecologist and the ranger own no ground and are never named. During play no name
is ever drawn, because that is the thing the room is there to work out.

## The round

Every night the room makes exactly one choice. That is the whole tension.

| Choice | What it does |
|---|---|
| Hunt lantana | The room votes. Mark the elimination. |
| Resilience | No vote. The crew prepares for fire instead. |

The night and the day are separate moments. Each change gets one card the room
reads and then one animation, and the game master presses through them, so
nothing important flashes past.

**Water is a break.** Lantana creeps outward from ground it already holds, and a
creeping front cannot cross a river. Its seed is carried by birds, which is how
new patches appear at a distance, but that is a jump to somewhere else rather
than a front advancing, and the game does not model it. So the river stops
spread, stops bare ground being taken from the far bank, and splits what counts
as one stand when fire severity is worked out.

**Eliminations.** A lantana player out leaves their ground bare, and bare
ground goes to whatever is next to it. A native player out lets lantana take
hold in their stand and spread from there. The ecologist or ranger going out
changes nothing on the map.

**Resilience.** The room never picks which one. The game master either picks or
presses Resolve and lets the system choose.

| Action | What it does |
|---|---|
| Fire line | A permanent trench hugging the homes, or the biggest block of forest. Repeated nights extend the same ring. |
| Water | Tonight's fire is held to a few squares whatever the fuel. |
| Early warning | A forecast of tomorrow night. Changes nothing tonight. |

**Fire.** Severity comes from the largest connected stand of thick lantana,
fixed against the map the room debated over, so what Ember says and what the map
does always agree. Early nights are small sparks. By the middle of the game
separate patches have met, and one fire runs through all of them.

**What the animations say.** Every change greys out the rest of the board and
holds on the squares that are about to move, so a room knows where to look on a
22 by 12 grid. Then those squares turn over a few at a time and the full map
comes back. A fire starts at one square, spreads wave by wave, and shows the
bare ground it left. If it meets a trench, those cells flash and the ground
behind them is untouched.

**The cards never name anyone.** They say what happened to the land, not who
went out or what they were. A night that changes nothing on the map reads the
same whether the ranger saved someone or a specialist was taken, so the room
keeps guessing and lantana can lie about it.

## How it ends

| Ending | |
|---|---|
| Every lantana out | The room wins. Forest health is the score. |
| Fire reaches the homes | Loss, immediately. |
| Forest below 35% | Loss. |
| No native forest left | Loss. |
| Night 8 with lantana still in | Loss. A room that only shelters never wins. |

## Changing the words

Every line the players see is in `stage2/text/`. Grep the sentence, edit it,
restart. No Python involved.

## Changing how it looks

The projector draws the terminal board by default. `stage2/maps/` holds six
other cartographic treatments, and any of them can drive a whole game:

```bash
python3 -m stage2.maps.gallery      # build the comparison page, then open
                                    # stage2/maps/out/gallery.html
STAGE2_STYLE=drawn python3 -m stage2.server
```

See `stage2/maps/README.md`. Nothing there changes the game or the shipped
board; `STAGE2_STYLE` defaults to `ansi`.

## Changing the game

Everything tunable is in `stage2/config.py`.

| Setting | Default | What it changes |
|---|---|---|
| `max_rounds` | 8 | Nights before the season ends as a loss |
| `loss_health` | 35 | Forest percentage that loses the game |
| `village_loss` | True | Fire reaching the homes ends it |
| `village_clearance` | 5 | How far homes start from the first infestation |
| `lantana_ratio` | 4 | One lantana per this many players, minimum two |
| `lantana_core` | 4 | Cells of a lantana player's ground that start infested |
| `native_loss_core` | 4 | Cells lantana takes at once when a native is out |
| `owned_fraction` | 0.66 | Share of land split into patches; the rest is commons |
| `growth_established` / `growth_dense` | 0.30 / 0.42 | How fast lantana spreads per neighbour |
| `reinvade_p` / `regen_p` | 0.55 / 0.22 | What bare ground becomes |
| `sev_t1` / `sev_t2` | 7 / 13 | Thick-stand sizes that push fire to severity 2 and 3 |
| `fire_cells` | 3 / 12 / 38 | Squares a fire of each severity can take |
| `fire_round_ramp` | 0.22 | Extra reach per night as the season dries |
| `line_cells` | 10 | Trench dug per resilience night |
| `bare_on_removal` | True | False turns a cleared lantana patch straight to forest |
| `team_loss` | False | True ends the game when ecologist and ranger are both out. Forced on in stage 1 |
| `village_defend_range` | 8 | Only trench the homes if fuel is this close |
| `stage` | 2 | 1 is plain Mafia with a replay at the end; 2 adds fire |
| `hold_ms` | various | How long the projector holds each animation frame |

## Testing

```bash
python3 -m unittest stage2.tests.test_isolation      # the live game must not move
python3 -m unittest stage2.tests.e2e.test_journeys   # the game and the console
python3 -m unittest stage2.tests.e2e.test_stages     # stage 1, Continue, the replay, the SVG map
python3 -m unittest stage2.tests.test_styles         # every map style renders
python3 -m unittest stage2.tests.test_rules         # water as a break, replay names
SHOTS=1 SHOT_DIR=/tmp/shots python3 -m unittest stage2.tests.e2e.test_journeys
python3 -m stage2.sim --games 250                    # balance, whole games in memory
python3 -m stage2.sim --trace 7
```

`STAGE2_FAST=1` removes every animation delay, which is what the tests use.

## The event log

Every round is written to `stage2/logs/game-<when>-seed<n>.json` as it happens,
and `stage2/logs/index.json` names the latest. One record per round: who went
out, every square that changed and what it changed from and to, the resilience
action and its cells, and the fire with its ignition square, cause, severity,
burned squares and the trench edges it pushed against. Enough to build a
post-game sequence without reading any of this code.

## What is where

| | |
|---|---|
| `server.py` | The whole HTTP server. Routes, SSE, the room's state machine. |
| `game.py` | Board, resolution, spread, fire, trenches, animation frames, the log. |
| `config.py` | Every tunable. Nothing else holds a number that matters. |
| `text.py`, `text/` | Every sentence a player or the projector ever shows. |
| `render.py`, `frames.py` | Turning game state into what the projector paints. |
| `maps/` | Six cartographic styles and the geometry they share. Own readme. |
| `static/` | `gm.html`, `phone.html`, `projector.html`, and vendored xterm. |
| `engine/` | Frozen copy of the live game's engine. Do not re-point at the original. |
| `sim.py` | Plays whole games in memory. Used for balance, never at runtime. |
| `tests/` | 39 tests. `test_isolation.py` is the one that guards the live game. |
| `logs/` | Written as games are played. `index.json` names the latest. |
| `simulation/` | Post-game replays. Not owned by the game, and no console button right now. |

## Keeping the live game out of this

The single-player game at pyrocene.netlify.app is live, and stage 2 must not be
able to affect it, including by accident.

- `stage2/engine/` is a snapshot taken once. Stage 2 imports only from there.
- `tests/test_isolation.py` parses every file under `stage2/` with `ast` and
  fails if any of them imports `engine`, `terminal`, `game` or `web`. Reading the
  syntax tree catches an import anywhere in a file, which grepping the top of it
  would not.
- `netlify.toml` has a `[context.branch-deploy]` block whose build command does
  nothing, so pushing this branch does not rebuild the site.
- `git diff --stat main -- engine terminal web game` must come back empty.

The cost is that a fix in the live engine does not reach stage 2 until somebody
copies it across. That is the intended trade. Stage 2 is a different game that
happens to share physics.
