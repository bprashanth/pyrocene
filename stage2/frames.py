"""Turn a beat from game.resolve() into one full projector frame (ANSI text).

Uses the frozen copy of the live game's renderer, so the map is byte-for-byte
the look players already know. Only the status line and Ember's block are new.
"""
from __future__ import annotations
from . import render as R
from .text import T, lines as tlines

FG = R.fg
WIDTH = 80
EMBER_COL = 203

_ART = None

def _ember_fig():
    return ["{^}", "^^^"]


def status_lines(view: dict) -> list:
    h = view["health"]
    bar = R._bar(h, 22, None)
    col = 40 if h >= 60 else 214 if h >= 40 else 196
    return [
        f"{FG(250)}{'Forest':<9}{R.RESET}{bar} {FG(col)}{h:>3}%{R.RESET}",
    ]


def header(view: dict, subtitle: str = "") -> str:
    left = f"{FG(208)}  {T('ui', 'projector.title')} {R.RESET}"
    mid = f"{FG(245)}  {T('ui', 'projector.round', r=view['round'], max=view['max_rounds'])}{R.RESET}"
    return left + mid + (f"   {FG(245)}{subtitle}{R.RESET}" if subtitle else "")


def ember_block(text: str, col: int = EMBER_COL, width: int = 70) -> list:
    if not text:
        return []
    fig = _ember_fig()
    wrapped = R._wrap(text, width)
    out = [f"  {FG(col)}{fig[0]}{R.RESET}  {FG(col)}EMBER{R.RESET}",
           f"  {FG(col)}{fig[1]}{R.RESET}  {FG(252)}{wrapped[0]}{R.RESET}"]
    for w in wrapped[1:]:
        out.append(f"       {FG(252)}{w}{R.RESET}")
    return out


def render_beat(beat: dict) -> str:
    view = beat["view"]
    kind = beat["kind"]
    fire = frozenset(beat.get("fire") or [])
    # The cells where the fire met a line: the one moment the room must not miss,
    # so they blink bright white against the fire rather than sitting in the
    # ordinary fire-line cyan.
    held = beat.get("held") or []
    overlay = {i: R.BLINK + R.bg(51) + R.fg(17) + "++" + R.RESET for i in held}
    sub = {"ignite": "fire", "spread": "fire", "burn": "fire"}.get(kind, "")
    subtitle = f"{FG(196)}*** WILDFIRE ***{R.RESET}" if sub else ""
    lines = [header(view, subtitle), ""]
    lines += status_lines(view)
    lines.append("")
    lines.append(R.render_board(view, fire=fire, overlay=overlay or None))
    lines.append("")
    lines.append(R.render_legend())
    lines.append("")
    if kind == "ending":
        big = beat["text"]
        lines.append(f"  {FG(220)}{'THE SEASON ENDS':<}{R.RESET}")
        lines += ember_block(big, col=220)
    else:
        lines += ember_block(beat.get("text", ""))
    return "\n".join(lines)


def render_lobby(n_players: int, seed: int) -> str:
    v = {"round": 0, "max_rounds": 0}
    lines = [f"{FG(208)}  {T('ui', 'projector.title')} {R.RESET}", "", "",
             f"  {FG(250)}{T('ui', 'projector.lobby', n=n_players)}{R.RESET}", "",
             f"  {FG(240)}map seed {seed}{R.RESET}"]
    return "\n".join(lines)


def frame_bytes(text: str) -> str:
    """Home the cursor, paint, clear whatever was below. No full clear, so the
    projector never flickers between beats."""
    return "\x1b[H" + text.replace("\n", "\x1b[K\n") + "\x1b[K\x1b[J"
