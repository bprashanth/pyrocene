# Pyrocene Stage 2: Ignition

The in-person Mafia game with a forest map behind it. The room plays as they
already do. This mirrors the room onto a projected map, and adds fire.

Nothing here touches the live game at pyrocene.netlify.app. Stage 2 keeps its
own frozen copy of the engine under `stage2/engine/` and imports only that.

## Run it in a room

```bash
python3 -m stage2.server          # prints the three addresses
```

1. Open the **projector** address on the big screen, full screen the browser.
2. Open the **game master** address on your own laptop.
3. Read out the **players** address. Everyone joins and types their name.
4. Press **Start game**. Roles appear on phones. Nobody else sees them.
5. Run the night as you always do. Mark who was eliminated in the table.
6. Ask the room for their one choice: **hunt lantana** or **resilience**.
7. Press **Resolve night**. The projector plays it out. Repeat.

Rehearsing alone: press **Seed** to add fake players, then Start.

No internet needed. xterm.js is vendored, the rest is the standard library.

## The round

Every night the room makes exactly one choice. That is the whole tension.

| Choice | What it does |
|---|---|
| Hunt lantana | The room votes. Mark the elimination. |
| Resilience | No vote. The crew prepares for fire instead. |

Then, in order, visible on the projector: eliminations land on the map, the
resilience action happens, lantana grows, fire runs, Ember explains.

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

**Fire.** Severity comes from the largest connected stand of dense lantana, so
what Ember says and what the map does always agree. Early nights are small
sparks. Later nights, an unchecked map carries fire a long way.

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
| `growth_established` / `growth_dense` | 0.20 / 0.28 | How fast lantana spreads per neighbour |
| `reinvade_p` / `regen_p` | 0.55 / 0.22 | What bare ground becomes |
| `sev_t1` / `sev_t2` | 6 / 14 | Dense cluster sizes that push fire to severity 2 and 3 |
| `fire_cells` | 3 / 12 / 38 | Squares a fire of each severity can take |
| `fire_round_ramp` | 0.22 | Extra reach per night as the season dries |
| `line_cells` | 10 | Trench dug per resilience night |
| `bare_on_removal` | True | False turns a cleared lantana patch straight to forest |
| `team_loss` | False | True ends the game when ecologist and ranger are both out |
| `hold_ms` | various | How long the projector holds each beat |

## Testing

```bash
python3 -m unittest stage2.tests.test_isolation      # the live game must not move
python3 -m unittest stage2.tests.e2e.test_journeys   # eleven journeys in a browser
SHOTS=1 SHOT_DIR=/tmp/shots python3 -m unittest stage2.tests.e2e.test_journeys
python3 -m stage2.sim --games 250                    # balance, whole games in memory
python3 -m stage2.sim --trace 7
```

`STAGE2_FAST=1` removes every beat delay, which is what the tests use.
