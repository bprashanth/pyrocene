"""Pure rendering: turn an engine `observable()` view into coloured strings.

No game logic here. Given the same view it always produces the same frame.
"""
from __future__ import annotations

USE_COLOR = True


def _sgr(*codes):
    return f"\x1b[{';'.join(str(c) for c in codes)}m" if USE_COLOR else ""


def bg(n): return _sgr(48, 5, n)
def fg(n): return _sgr(38, 5, n)
RESET = _sgr(0)
STRIKE = _sgr(9)      # strike-through (for locked commands)
CLEAR = "\x1b[2J\x1b[H"


def set_color(on: bool):
    """Toggle colour + screen-clear codes. Must run before rendering."""
    global USE_COLOR, RESET, STRIKE, CLEAR
    USE_COLOR = on
    RESET = _sgr(0)
    STRIKE = _sgr(9)
    CLEAR = "\x1b[2J\x1b[H" if on else "\n"

# 2-char tile per cell: colour block + a small severity glyph.
# Resolution language: satellite reads (detail 1) render as a dim HAZE on a dark
# ground (rough, unconfirmed, could hide seedlings); drone/ground reads (detail
# 2-3) render as SOLID colour (confirmed). So a drone always visibly changes the
# map: haze snaps to solid, or hidden invasion pops into view.
def cell_str(c: dict) -> str:
    cov = c.get("cover")
    st = c.get("stage", 0)
    detail = c.get("detail", 3)
    if c.get("fireline"):
        return bg(236) + fg(51) + "++" + RESET          # dug fire line
    if cov == "village":
        return bg(131) + fg(231) + "HH" + RESET
    if cov == "water":
        return bg(24) + fg(45) + "~ " + RESET
    if cov == "unknown":
        # fogged land; a bank cell still shows the river's edge as a faint tick
        return bg(236) + fg(240) + (". " if c.get("bank") else "  ") + RESET
    hazy = detail == 1  # satellite only: a rough, low-confidence read for invasion
    if cov == "invasive":
        if st >= 3:  # dense stands are the only invasion satellite can resolve
            return bg(236) + fg(133) + "▒▒" + RESET if hazy else bg(90) + fg(219) + "##" + RESET
        if st == 2:
            return bg(130) + fg(214) + "**" + RESET     # established (drone+ only)
        return bg(100) + fg(191) + "vv" + RESET         # seedling (drone+ only)
    return _clear_tile(c, hazy, is_bare=(cov == "bare"))


def _clear_tile(c: dict, hazy: bool, is_bare: bool) -> str:
    """Clear ground. Landscape covariates and the DSS risk zone are revealed by
    satellite, so they take priority over the plain 'unconfirmed' haze."""
    if c.get("risk", 0) >= 2:                                   # DSS risk zone (glows red)
        mark = "^^" if c.get("hill") else "==" if c.get("road") else "::"
        return bg(52) + fg(210) + mark + RESET
    if c.get("road"):
        return bg(240) + fg(250) + "==" + RESET                 # a track
    if c.get("hill"):
        return (bg(137) if is_bare else bg(22)) + fg(101) + "^^" + RESET
    if hazy:                                                    # plain, unconfirmed for invasion
        return bg(236) + fg(137 if is_bare else 65) + "▒▒" + RESET
    if is_bare:
        return bg(137) + fg(223) + "░ " + RESET
    return bg(22) + fg(65) + (":." if c.get("bank") else "  ") + RESET


def render_board(view: dict, fire: frozenset = frozenset(), overlay: dict = None) -> str:
    cols, rows = view["cols"], view["rows"]
    grid = {c["index"]: c for c in view["cells"]}
    lines = [fg(245) + "    " + "".join(f"{chr(65 + c)} " for c in range(cols)) + RESET]
    for r in range(rows):
        row = fg(245) + f"{r + 1:>3} " + RESET
        for c in range(cols):
            i = r * cols + c
            if i in fire:
                row += bg(196) + fg(226) + "##" + RESET
            elif overlay and i in overlay:
                row += overlay[i]
            else:
                row += cell_str(grid[i])
        lines.append(row)
    return "\n".join(lines)


def _bar(pct: int, width: int = 22, target: int = None) -> str:
    filled = round(pct / 100 * width)
    tcol = round(target / 100 * width) if target is not None else -1
    # green when at/above the target line, amber below, red near collapse
    color = 40 if (target is None or pct >= target) else 214 if pct >= 40 else 196
    out = []
    for i in range(width):
        if i == tcol:
            out.append(fg(220) + "│" + RESET)                 # the target line to stay above
        else:
            out.append((fg(color) + "█") if i < filled else (fg(238) + "░"))
    return "".join(out) + RESET


def render_status(view: dict) -> str:
    winds = {"N": "↑ N", "S": "↓ S", "E": "→ E", "W": "← W"}
    risk_c = {"low": 40, "med": 214, "high": 196}[view["fire_risk"]]
    res = view.get("resilience", {"streak": 0, "need": 3})
    need, streak = res["need"], res["streak"]
    target = view["thresholds"]["win"]
    left = need - streak
    dots = fg(40) + "●" * streak + fg(238) + "○" * (need - streak) + RESET
    if left <= 0:
        goal = f"{fg(40)}restored — you win!{RESET}"
    else:
        goal = f"{fg(250)}hold native forest above {fg(255)}{target}%{fg(250)} — {fg(255)}{streak} of {need}{fg(250)} nights{RESET}"
    wind_s = ["still", "breeze", "strong"][view.get("wind_str", 1)]

    def row(label, body):
        return f"{fg(250)}{label:<11}{RESET}{body}"

    return "\n".join([
        row("Forest", f"{_bar(view['health'], 16, target)} {fg(255)}{view['health']:>3}%{RESET}"),
        row("Wildlife", f"{_bar(view['wildlife'], 16)} {fg(255)}{view['wildlife']:>3}%{RESET}"),
        row("Wind", f"{fg(45)}{winds[view['wind']]}  {wind_s}{RESET}"),
        row("Fire", f"{fg(risk_c)}{view['fire_risk'].upper()}{RESET}"),
        row("Win goal", f"{dots}  {goal}"),
    ])


def render_legend() -> str:
    """Categorised, aligned. Base covers are solid 2-wide squares; overlays (hill,
    road, risk) are hollow (no fill) since they sit on top of a base cover."""
    def item(square, label):
        return f"{square} {fg(250)}{label:<12}{RESET}"

    def cat(name):
        return f"{fg(245)}{name:<9}{RESET}{fg(240)}│{RESET} "

    covers = {
        "forest": bg(22) + fg(65) + "  ", "water": bg(24) + fg(45) + "~~",
        "bare": bg(137) + fg(223) + "░░", "unknown": bg(236) + fg(240) + "  ",
        "sapling": bg(100) + fg(191) + "vv", "established": bg(130) + fg(214) + "**",
        "dense": bg(90) + fg(219) + "##", "village": bg(131) + fg(231) + "HH",
        "fire line": bg(236) + fg(51) + "++",
    }
    overlays = {"hill": fg(101) + "^^", "road": fg(250) + "==", "risk zone": bg(52) + fg(210) + "::"}
    C = {k: v + RESET for k, v in {**covers, **overlays}.items()}
    return "\n".join([
        cat("LANDSCAPE") + "".join(item(C[k], k) for k in ("forest", "hill", "water", "bare")),
        cat("INVASIVE") + "".join(item(C[k], k) for k in ("sapling", "established", "dense")),
        cat("HUMAN") + "".join(item(C[k], k) for k in ("village", "road", "fire line")),
        cat("OTHER") + "".join(item(C[k], k) for k in ("unknown", "risk zone")),
    ])


def _step(n: int, label: str, cur: int) -> str:
    if n < cur:
        return f"{fg(40)}{n} {label} ✓{RESET}"
    if n == cur:
        return f"{fg(214)}[{n} {label}]{RESET}"          # you are here
    return f"{fg(240)}{n} {label}{RESET}"


def render_job(view: dict) -> str:
    """Show WHERE you are in the multi-night chain so you never lose the thread."""
    job = view.get("job")
    if not job:
        return ""
    if job["type"] == "burn":
        ready = job["ready"]
        calm = view["wind_str"] <= 1
        # phase: 1 dig, 2 wait-for-calm, 3 light, 4 restore-next-turn
        cur = 3 if (ready and calm) else 2 if ready else 1
        plan = "  ".join([_step(1, "dig lines", cur), _step(2, "wait calm", cur),
                          _step(3, "light", cur), f"{fg(240)}4 restore next turn{RESET}"])
        if not ready:
            done = job["lining_total"] - job["lining_left"] + 1
            status = (f"Laying fire line, night {fg(255)}{done}/{job['lining_total']}{RESET}. "
                      f"{fg(245)}Press Enter to keep digging.{RESET}")
        elif calm:
            status = f"{fg(40)}Lines ready and the wind is calm. Press Enter to LIGHT IT.{RESET}"
        else:
            wind = ["still", "a breeze", "STRONG"][view["wind_str"]]
            status = (f"{fg(196)}Lines ready, but wind is {wind}.{RESET} "
                      f"Enter lights it anyway (it will jump the lines!) — or 'w' to wait.")
        return f"{fg(214)}BURN PLAN{RESET}   {plan}\n           {status}"
    return (f"{fg(202)}CREW{RESET}   clearing by hand, {fg(255)}{job['remaining']}{RESET} invasive cell(s) left.  "
            f"{fg(245)}Press Enter to keep working.{RESET}")


# ---- the 4-character panel: one persistent channel each ----
CHAR_ORDER = ["ivy", "rocky", "elder", "ember"]
CHAR_META = {
    "ivy":   {"name": "IVY",   "tag": "data",   "color": 45,  "fig": ["(o)", "/|\\"]},
    "rocky": {"name": "ROCKY", "tag": "ranger", "color": 208, "fig": ["[o]", "/|\\"]},
    "elder": {"name": "ELDER", "tag": "wisdom", "color": 114, "fig": ["<o>", "/|\\"]},
    "ember": {"name": "EMBER", "tag": "fire",   "color": 203, "fig": ["{^}", "^^^"]},
}


def _wrap(text: str, w: int):
    words, lines, cur = text.split(), [], ""
    for word in words:
        if len(cur) + len(word) + 1 <= w:
            cur = (cur + " " + word).strip()
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines or [""]


def render_char_panel(chars: dict, width: int = 24) -> list:
    out = [f"{fg(245)}WHO'S SPEAKING{RESET}", ""]
    for key in CHAR_ORDER:
        m = CHAR_META[key]
        e = chars.get(key, {"text": "", "fresh": False})
        col = m["color"] if e["fresh"] else 240      # fresh = spoke this night
        tcol = col if e["fresh"] else 240
        spk = _wrap(e["text"], width)
        if len(spk) > 3:                              # keep 3 lines, mark the cut
            spk = spk[:3]
            spk[2] = spk[2][:width - 1].rstrip() + "…"
        while len(spk) < 2:
            spk.append("")
        out.append(f"{fg(col)}{m['fig'][0]} {m['name']}{RESET} {fg(240)}{m['tag']}{RESET}")
        out.append(f"{fg(col)}{m['fig'][1]}{RESET} {fg(tcol)}{spk[0]}{RESET}")
        out.append(f"    {fg(tcol)}{spk[1]}{RESET}")
        if len(spk) > 2 and spk[2]:
            out.append(f"    {fg(tcol)}{spk[2]}{RESET}")
    return out
