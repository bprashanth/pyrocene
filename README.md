# Pyrocene

A cooperative game about holding back an **invasive-species** invasion with good
data and timely action. You play a two-person field team (an ecologist who *sees*
and a ranger who *acts*) sharing **one action per night** against a landscape
where invasives spread on their own, mature, and, if neglected, feed a rare and
devastating wildfire.

The lesson is embedded in the mechanics, not lectured: you cannot fight the fire,
you fight the weed that feeds it, and you can only fight what you took the time to
see. Every turn spent scanning is a turn not spent clearing, while the invasion
grows.

This repo is a **terminal prototype** of the v0.2 engine. Fire is now a rare,
dramatic consequence of letting invasives go dense, not the main event.

## Run it

Requires Python 3.10+ (no dependencies). From the repo root:

```bash
python3 -m terminal.play              # play (random map)
python3 -m terminal.play --seed 42    # fixed map, reproducible
python3 -m terminal.play --demo       # watch the built-in bot play
python3 -m terminal.play --no-color   # plain text
```

Use a color terminal. Over SSH it just works; no ports needed.

### How to play

You get **one command per night**. Type `help` to list them.

- Look: `sat`, `drone D4`, `survey D4`, `ask D4` (elders advise a method for that patch)
- Act: `remove D4`, `restore D4`, `pass`

Cells are `<column letter><row number>`, e.g. `drone K6`. Area actions anchor
their block at that cell. Start by scanning the **river banks** (`:.`), where
invasives run fastest, find the three hidden outbreaks, clear them while they are
seedlings, then **restore** the bare ground so they cannot return. Keep native
cover at 60%+ for 14 nights to win; 80%+ (with a living ecosystem) is gold.

## Structure: dynamics are separate from UX

The game core knows nothing about pixels. A UX (this terminal one, or a future web
map with real drone imagery) only talks to the engine's API and event stream. See
**[ENGINE_SPEC.md](ENGINE_SPEC.md)** — that's the handoff document for building a
different front end without touching the dynamics.

```
engine/            pure game logic (no I/O, no colours)
  model.py         data types + JSON serialization
  content.py       DEFAULT_CONFIG (all tunables) + map generation
  rules.py         nature's turn: spread, maturation, fire, scoring
  engine.py        public API: new_game / legal_actions / apply / observable
  cli.py           headless harness: --demo, --json, --auto
terminal/          the UX layer (consumes the engine's view + events only)
  render.py        view -> coloured strings
  play.py          the interactive loop + animations
ENGINE_SPEC.md     the engine<->UX contract
DESIGN.md          design notes (see note at top re: the invasives-first pivot)
```

Headless engine (no UI), useful for tuning and for UX agents:

```bash
python3 -m engine.cli --demo --seed 7     # scripted auto-play, prints events
python3 -m engine.cli --json --seed 1     # dump a fresh State + view as JSON
```

## Status

v0.2 terminal prototype. Balance is measured (neglect loses ~100%, informed play
~65%). Next: bind a real orthomosaic to `map_meta` and hand `ENGINE_SPEC.md` to a
UX model for the map + animations.
