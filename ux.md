# Pyrocene UX guide — changing the look & feel

This is the map for anyone reworking how the game **looks and reads** without
touching how it **plays**. The dynamics live behind a wall; you work on this side
of it.

## Direction: the terminal UI is the front end (on purpose)

We tried a full **web UI** — a browser build with rounded tile art, springy
animations, procedural sound, cute character bubbles. It works end to end and
respects the same wall. We **rejected it**: polished that way, it reads too much
like *Candy Crush* — exactly the "juicy casual puzzler" feel we want to avoid.
This is meant to be a **learning tool** with a **novel take on gameplay**, and the
sparse, deliberate, text-forward terminal presentation serves both better: it
keeps attention on the ecology and the one-move-a-night decisions instead of on
juice. So for now the **terminal UI is the primary and only front end.**

The web experiment is parked on the **`webui-experiment`** branch as a reference
for *what not to do* — not to be merged or revived without a deliberate rethink
of that concern. If you re-explore a graphical UI, the goal is a distinctive,
calm, novel look, **not** casual-game candy.

## The one rule

**The UX only consumes two things from the engine and never imports its rules:**

1. `observable(state, role="team") -> dict` — the current frame ("the view").
2. the `events` list returned by `apply(state, action) -> (state, events)`.

The view schema and event list are documented in **`ENGINE_SPEC.md`** (read it
before touching rendering, everything you draw comes from there). Never
`import engine.rules`, never read hidden cell truth, never change a number that
affects balance (those are `engine/content.py::DEFAULT_CONFIG`). If you find
yourself wanting game data the view doesn't expose, that's an engine change (add
a field to `observable`), not a UX hack.

## Where things live

```
terminal/render.py   PURE rendering. view -> coloured strings. No I/O, no logic.
                     Given the same view it always returns the same frame.
terminal/play.py     The loop: input, the game loop, character narration, help,
                     animations, screen composition (draw()), argparse (main()).
```

Rule of thumb: **anything that decides *what a pixel looks like* is in `render.py`;
anything about *timing, input, or which words a character says* is in `play.py`.**

Run it: `python3 -m terminal.play` · `--demo` (watch a bot) · `--no-color` ·
`--seed N` · `--level 0..5`.

## Colour system

Colours are **xterm-256** codes via two helpers in `render.py`:

```python
fg(n)  # foreground  -> "\x1b[38;5;{n}m"
bg(n)  # background  -> "\x1b[48;5;{n}m"
RESET  # "\x1b[0m"   ends a run (always close your runs)
STRIKE # "\x1b[9m"   strike-through (used for locked commands)
```

**`set_color(False)`** (called by `main()` for `--no-color` or a non-tty) makes
`fg/bg/RESET/STRIKE` return `""` and turns `CLEAR` into a newline, so every string
degrades to plain text automatically. Because of this, **always build colour
through `fg()`/`bg()`/`RESET`** — never hard-code a raw `\x1b[` escape, or it
won't respect `--no-color`.

### Semantic palette (what each code means today)

Recolour the game by changing these consistently. Meaning first, number second:

| Role | Code | Where |
|---|---|---|
| brand / title | `fg 208` | `draw()` header |
| good / healthy / at-target | `fg 40` | bars, streak dots, "you win" |
| warning / amber | `fg 214` | bars below target, prompts |
| danger / red | `fg 196` | bars near collapse, escaped burn |
| target line marker | `fg 220` | `_bar` `│` |
| value text (numbers) | `fg 255` | percentages, counts |
| label text | `fg 250` | status labels |
| dim label / category | `fg 245` | legend categories, hints |
| stale / muted | `fg 240`/`238` | dimmed characters, empty bar |
| Ivy / data | `fg 45` | character + DSS line + water |
| Rocky / ranger | `fg 208` | character + crew |
| Elder / wisdom | `fg 114` | character |
| Ember / fire | `fg 203` | character + effect tags |

Character colours are also in `CHAR_META` (below) — keep the two in sync if you
recolour a persona.

## The board tile language (`cell_str`)

Every board cell is **exactly 2 display columns** (so the grid stays aligned).
`cell_str(cell_dict)` decides the tile. The design language:

- **Base covers** are solid 2-wide colour blocks: forest `bg22`, water `bg24 ~ `,
  bare `bg137 ░`, village `bg131 HH`, unknown/fog `bg236`.
- **Invasion** by stage: seedling `bg100 vv`, established `bg130 **`, dense `bg90 ##`.
- **Resolution language (important):** a cell seen only by **satellite** (`detail==1`)
  renders as a dim **haze** `▒▒` (rough, "could be hiding seedlings"); a cell seen
  by **drone/ground** (`detail>=2`) renders **solid**. So droning always visibly
  changes the map. Keep this if you re-skin: haze = uncertain, solid = confirmed.
- **Overlays** (`_clear_tile`) sit on clear ground and are drawn *hollow* (no fill)
  so they read as "on top of" a cover: hill `^^`, road `==`, and the DSS **risk
  zone** `::` on `bg52` (glows red). Fire line `++`.
- Fire animation frames paint burning cells `bg196 ##` (in `render_board(..., fire=...)`).

To restyle the board you edit `cell_str` and `_clear_tile` **only** — change the
glyph strings and colour codes. Two hard constraints: the return must be **2
display columns wide**, and it must still work under `--no-color` (i.e. the glyph
alone should be legible, since colour vanishes).

## Screen anatomy (`draw()` in play.py)

`draw(view, chars)` composes one frame, top to bottom:

```
  P Y R O C E N E — Night 4/16 · game 4: sat drone ask DSS   <- title + tools row
  <render_status(view)>                                       <- 5 aligned stat rows
  ☀ DROUGHT incoming (...) — 2 nights                         <- if view["incoming"]
  in effect: DROUGHT                                          <- if view["effects"]
  DSS ► C5 is going dense, uproot it now (...)                <- if view["dss_advice"]
  <board (render_board)>  <char panel (render_char_panel)>   <- composed side by side
  <render_legend()>
  <render_job(view)>                                          <- if a burn/crew job runs
```

The board and character panel are **composed side by side** in `draw()` by
zipping their lines (board is `bw = 4 + cols*2` wide; the panel follows after two
spaces). If you widen the board or panel, keep the total under **80 columns** (the
whole UI is built for an 80-col terminal — see Guardrails).

## Function reference (render.py)

| Function | Controls | Notes |
|---|---|---|
| `cell_str` / `_clear_tile` | one board tile | 2 cols wide; glyph + colour |
| `render_board(view, fire, overlay)` | the grid + row/col labels | `overlay` = `{idx: str}` to override cells |
| `_bar(pct, width, target)` | a meter | draws a `│` target line; green above / amber / red |
| `render_status(view)` | the 5 stat rows | Forest, Wildlife, Wind, Fire, Win goal |
| `render_legend()` | the key | categorised: LANDSCAPE / INVASIVE / HUMAN / OTHER |
| `render_job(view)` | burn/crew progress | the multi-night "BURN PLAN" tracker |
| `render_char_panel(chars)` | the 4-character sidebar | reads the `chars` dict from play.py |

Labels in `render_status` are padded to a fixed width (`{label:<11}`) so the
column aligns — keep that if you rename them.

## Characters & narration

Two halves:

**Look** — `CHAR_META` in `render.py`:
```python
CHAR_META = {
  "ivy":   {"name": "IVY",   "tag": "data",   "color": 45,  "fig": ["(o)", "/|\\"]},
  "rocky": {"name": "ROCKY", "tag": "ranger", "color": 208, "fig": ["[o]", "/|\\"]},
  "elder": {"name": "ELDER", "tag": "wisdom", "color": 114, "fig": ["<o>", "/|\\"]},
  "ember": {"name": "EMBER", "tag": "fire",   "color": 203, "fig": ["{^}", "^^^"]},
}
```
`fig` is the 2-line ASCII figure; `color` is their voice colour; `tag` is the grey
subtitle. A speaking character lights up in `color`; a quiet one dims to `240`.
`CHAR_ORDER` sets the top-to-bottom order.

**Voice** — `update_chars(chars, events, view)` in `play.py`. It reads the turn's
`events` and routes short lines to channels via `say("ivy", "...")`. This is where
you reword what characters say, add reactions to new event types, or change tone.
The `chars` dict is `{key: {"text": str, "fresh": bool}}`; `initial_chars()` sets
the opening lines. Keep lines short — the panel wraps at width 24 and truncates to
3 lines with `…`.

## Animations (play.py)

- `animate_fire(view, cells, delay)` — sweeps the burn across the board.
- `animate_remove(view, reclaimed, reinvaded, delay)` — the green-fills / purple-
  reinvades flash after clearing saplings.
- `announce_event(ev_type, note, demo)` — the full-screen "field note" card when a
  disaster lands.

All respect `--no-color`. In `--demo` they `time.sleep`; interactively some wait
for Enter. Change `delay` values or the frame glyphs here to retune pacing/feel.

## Help & commands (`help_text(view)` in play.py)

The command list is **colour-coded by operator** (`IVY=45`, `ROCKY=208`,
`ELDER=114`) and **locked commands are struck through** (via `R.STRIKE`) until the
level unlocks them (`view["unlocks"]`). To change command colours/labels/order,
edit `help_text`. Commands themselves are parsed in `turn_prompt` — targeting is
plain typed cells (`drone D4`); there is intentionally no cursor/mouse layer.

## Recipes (common look-and-feel changes)

- **Re-skin the whole palette:** change the codes in the semantic table above,
  consistently, in `render.py` (and mirror character colours in `CHAR_META`).
- **Change board glyphs** (e.g. emoji instead of `vv`/`##`): edit `cell_str` and
  `_clear_tile`; keep every tile 2 display columns and legible without colour.
- **Rename / recolour / reorder characters:** edit `CHAR_META` + `CHAR_ORDER`
  (and their colours in the palette table if you want the help to match).
- **Reword a character or react to a new event:** edit `update_chars` /
  `initial_chars` in `play.py`.
- **Rearrange the screen:** edit `draw()` — it's the single place the frame is
  composed. The status block, incoming banner, DSS line, board+panel, legend and
  job tracker are independent pieces you can reorder or drop.
- **Change the meters / target line:** `_bar` (marker glyph, colours, width) and
  the rows in `render_status`.
- **Retune animation pacing:** the `delay` args and `time.sleep` calls in the
  `animate_*` / `announce_event` functions.
- **Force plain text:** run with `--no-color`, or call `render.set_color(False)`.

## Guardrails

- **80 columns.** The whole layout (board 48 + gap + panel) is tuned for an
  80-col terminal. After any width change, verify no rendered line exceeds 80
  *display* columns — remember block chars like `█ ▒ ░` are width-1 but true
  emoji (`🐄 ☀ 🌧`) are width-2.
- **Both themes.** Everything must read under `--no-color`; never hard-code
  escapes, and don't rely on colour alone to carry meaning (glyphs must
  distinguish states too).
- **Two columns per tile.** The board grid only aligns if every `cell_str`
  result is exactly 2 display columns.
- **Don't cross the wall.** No `import engine.rules`, no reading hidden truth, no
  editing `content.py` balance numbers. If the UX needs new data, add it to
  `observable()` (an engine change) and document it in `ENGINE_SPEC.md`.
- **Stay pure in render.py.** Functions there take a view and return a string;
  they don't print, sleep, or read input. Side effects live in `play.py`.
