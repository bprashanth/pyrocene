# Stage 2: what was decided and why

## Isolation

`pyrocene.netlify.app` builds from `main` and publishes `web/`. Stage 2 lives
entirely under `stage2/`, with `engine/` and `terminal/render.py` copied in as a
frozen snapshot. `tests/test_isolation.py` fails if anything under `engine/`,
`terminal/`, `web/` or `game/` differs from the merge base, and parses every
Stage 2 file to prove none of them import the live packages. `netlify.toml` has
a `[context.branch-deploy]` no-op so a push of this branch cannot rebuild the
live site.

## Rendering

The projector runs the copied `render.py` server-side and pushes ANSI frames
over server-sent events to xterm.js. The map is therefore byte-identical to the
game people already played, and animation is just a sequence of frames. There is
no second renderer to drift.

Two things went wrong here and are worth remembering. Scaling the terminal with
a CSS transform clipped the left edge of every frame, because `#term` stretches
to the flex line and is much wider than the glyph grid inside it. The fix is to
pick a font size that fits instead of scaling: crisper on a projector and no
centring maths. Second, xterm needs `[hidden]` respected explicitly on the game
master page, since `display:flex` beats the user agent's rule.

## The fire line, which is the point of the stage

Getting fire to visibly run into a fresh line and stop took four passes.

1. The line was placed around the **lantana**. The brief says to place it around
   **the thing being protected**. Placing it around the asset is what makes
   repeated resilience nights extend one ring instead of chasing whichever stand
   is worst tonight.
2. A straight line off the cluster's bounding box fell off the map when the
   cluster sat on an edge, so no trench was dug at all.
3. The run from the fuel to the line was a greedy walk that gave up at the
   river. It is a breadth-first search now, so the fire goes around water.
4. The forced run was queued behind the ordinary spread and hit the cell cap
   before it ever arrived. It burns first now, out of the same budget.

That last point was also a bug in the other direction: the forced run had been
given extra cells, so digging a trench *increased* the burn. Sheltering made
things worse, which is exactly backwards.

Reachability now outranks how much sits behind a line when choosing a side, so
the room never pays for a trench the fire cannot reach. Across 40 seeds the fire
runs into a freshly dug line in 38 of them.

## Balance, and one judgement call

`sim.py` plays whole games in memory; 250 games take about five seconds. Every
number below came from that rather than from playing.

Room policies, 250 games, 12 players, a room that finds a real lantana 35% of
the time it hunts:

| Policy | Win | Nights | End health | Lost the village |
|---|---|---|---|---|
| hunter, never shelters | 74% | 5.4 | 65% | 12% |
| warden, shelters when the homes are threatened | 68% | 5.8 | 64% | 2% |
| turtle, only shelters | 0% | 8.0 | 51% | — |

**Hunting dominates, and I left it that way.** Removing a lantana player takes
their whole stand of fuel out permanently; a trench protects ten cells once. No
amount of tuning makes sheltering the better strategy without breaking the
ecology, and the ecology is the thesis the whole project rests on: you cannot
fight the fire, you fight the weed that feeds it.

So resilience is not a rival strategy here, it is insurance. The village rule is
what gives it teeth: fire reaching the homes ends the game immediately, so a
room that never looks up loses the village one game in eight, and a room that
spends a night defending it almost never does. That is a real decision without
pretending trenches beat uprooting.

Things that were tried and rejected: making fires bigger (fire is capped by the
spread search long before the cell count binds), raising the health loss line
(hunters are *healthier*, so it punishes the careful room), and making
resilience free (the exclusive choice is the whole tension and the brief is
explicit about it).

Worth revisiting with real players: whether 74% is too kind, and whether early
warning earns its slot given it changes nothing mechanically.

## Rules changed from STAGE_2.md, and why

- **Losing both the ecologist and the ranger no longer ends the game.** It was
  ending 40% of games in three or four nights, before the map had a story. The
  room plays on blind. `team_loss` in config turns the original rule back on.
- **A lantana player's ground goes bare, not straight to forest.** Bare ground
  then goes to whatever is beside it. `bare_on_removal: False` restores the
  simpler rule from the doc.
- **Losing a native infests a core of their stand, not all of it.** Whole-patch
  conversion made the Mafia kill, not fire, the main driver of forest health,
  which drowned out everything the stage is about.
- **Fire reaching the homes ends the game.** New. See above.
- **Lantana starts as a small core inside a larger territory.** The doc has
  lantana growing outward to simulate infestation; starting with the whole
  territory infested meant severity 2 fires from night one.

## Pacing

Target was five or six nights and about twenty minutes. Games run 5.4 nights on
average, 8 at the outside. Beat holds are in `config.py` under `hold_ms` and
`STAGE2_FAST=1` zeroes them, so the tests run the whole suite in 34 seconds.
