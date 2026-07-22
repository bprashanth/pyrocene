"""Playable terminal front end for Pyrocene.

    python3 -m terminal.play                 # play it
    python3 -m terminal.play --seed 42        # fixed map
    python3 -m terminal.play --demo           # watch the informed bot play
    python3 -m terminal.play --no-color       # plain text

The whole loop: show the fog-of-war view, take ONE team command, call the
engine, animate the events it returns, narrate, repeat. Cost is the turn.
"""
from __future__ import annotations
import argparse
import select
import sys
import termios
import time
import tty

from engine import new_game, apply, observable
from engine.engine import area
from engine.model import INVASIVE, BARE, NATIVE, GROUND, SEEDLING, ESTABLISHED, DENSE
from . import render as R
from .text import T, has, lines as tlines

FG = R.fg


def clear():
    print(R.CLEAR, end="")


def parse_cell(tok: str, view: dict):
    """'D4' -> cell index (col letter + 1-based row)."""
    tok = tok.strip().upper()
    if len(tok) < 2 or not tok[0].isalpha() or not tok[1:].isdigit():
        return None
    c = ord(tok[0]) - 65
    r = int(tok[1:]) - 1
    if 0 <= r < view["rows"] and 0 <= c < view["cols"]:
        return r * view["cols"] + c
    return None


def cell_name(i: int, view: dict) -> str:
    return f"{chr(65 + i % view['cols'])}{i // view['cols'] + 1}"


IVY, ROCKY, ELDER = 45, 208, 114   # who owns each command (blue / orange / green)


def help_text(view: dict) -> str:
    """Colour-coded by who runs it; locked commands are struck through until they
    unlock, then light up in their operator's colour."""
    u = view.get("unlocks", {"satellite": True, "drone": True, "survey": True,
                             "translator": True, "dss": True})

    def line(color, unlocked, name, desc):
        if unlocked:
            return f"  {FG(color)}{name:<11}{R.RESET}{FG(250)}{desc}{R.RESET}"
        return f"  {R.STRIKE}{FG(240)}{name:<11}{desc}{R.RESET}"

    rows = [
        f"{FG(255)}{T('help', 'header')}{R.RESET} {FG(245)}{T('help', 'header_note')}{R.RESET}",
        line(IVY, u.get("satellite", True), "sat", T("help", "sat")),
        line(IVY, u.get("drone", True), "drone D4", T("help", "drone")),
        line(IVY, u.get("survey", True), "survey D4", T("help", "survey")),
        line(IVY, u.get("dss", True), "dss", T("help", "dss")),
        line(ELDER, u.get("translator", True), "ask D4", T("help", "ask")),
        line(ROCKY, True, "remove D4", T("help", "remove")),
        line(ROCKY, True, "restore D4", T("help", "restore")),
        line(ELDER, True, "burn D4", T("help", "burn")),
        line(ELDER, True, "crew D4", T("help", "crew")),
        line(ROCKY, True, "pass", T("help", "pass")),
        f"  {FG(245)}{T('help', 'footer')}{R.RESET}",
    ]
    return "\n".join(rows)


def initial_chars() -> dict:
    return {
        "ivy":   {"text": T("characters", "intro.ivy"), "fresh": True},
        "rocky": {"text": T("characters", "intro.rocky"), "fresh": False},
        "elder": {"text": T("characters", "intro.elder"), "fresh": False},
        "ember": {"text": T("characters", "intro.ember"), "fresh": False},
    }


def update_chars(chars: dict, events: list, view: dict):
    """Route this night's events to the four character channels. Each channel
    keeps its last line (dimmed) until that character has something new to say."""
    for c in chars.values():
        c["fresh"] = False
    ev = {e["type"]: e for e in events}

    def say(who, key, **kw):
        chars[who] = {"text": T("characters", key, **kw), "fresh": True}

    # EMBER: nature and threats
    if "burn_escape" in ev:
        say("ember", "ember.burn_escape", n=len(ev["burn_escape"]["cells"]))
    elif "village_fire" in ev:
        say("ember", "ember.village_fire")
    elif "fire" in ev:
        say("ember", "ember.fire", n=len(ev["fire"]["cells"]))
    else:
        spread = sum(1 for e in events if e["type"] in ("spread", "regrow"))
        if spread:
            say("ember", "ember.spread", n=spread)

    # IVY: data and detection
    if "scan" in ev:
        sc = ev["scan"]
        det = sc.get("detected")
        if det:
            say("ivy", "ivy.drone_found", n=len(det))
        elif sc.get("source") == "drone":
            say("ivy", "ivy.drone_clean")
        elif sc.get("source") == "survey":
            say("ivy", "ivy.survey")
        elif sc.get("source") == "satellite":
            say("ivy", "ivy.sat_drone" if view.get("unlocks", {}).get("drone", True) else "ivy.sat_only")

    # ROCKY: action and the job chain
    if "controlled_burn" in ev:
        say("rocky", "rocky.controlled_burn")
    elif "crew_done" in ev:
        say("rocky", "rocky.crew_done")
    elif "lines_ready" in ev:
        say("rocky", "rocky.lines_ready")
    elif "lining" in ev:
        say("rocky", "rocky.lining", n=ev["lining"]["left"])
    elif "waiting_wind" in ev:
        say("rocky", "rocky.wait_wind" if view["wind_str"] > 1 else "rocky.wind_calm")
    elif "job_start" in ev:
        say("rocky", "rocky.start_burn" if ev["job_start"]["job"] == "burn" else "rocky.start_crew")
    elif "job_abort" in ev:
        say("rocky", "rocky.abort")
    elif "crew_work" in ev:
        say("rocky", "rocky.crew_work", cleared=ev["crew_work"]["cleared"], remaining=ev["crew_work"]["remaining"])
    elif ev.get("remove", {}).get("removed"):
        rm = ev["remove"]
        if rm["reinvaded"] and not rm["reclaimed"]:
            say("rocky", "rocky.reinvaded_all")
        elif rm["reinvaded"]:
            say("rocky", "rocky.reinvaded_some", n=len(rm["reinvaded"]))
        elif rm["reclaimed"] and not rm["bared"]:
            say("rocky", "rocky.reclaimed")
        else:
            say("rocky", "rocky.bared")
    elif ev.get("restore", {}).get("planted"):
        say("rocky", "rocky.planted", n=ev["restore"]["planted"])

    # disasters and boons
    if "event" in ev:
        et = ev["event"]
        if et == "work_party":
            say("elder", "event.work_party")
        elif et in ("drought", "monsoon", "grazing"):
            say("ember", f"event.{et}")

    # ELDER: community advice (the clue text itself comes from the engine)
    if "clue" in ev:
        chars["elder"] = {"text": ev["clue"]["text"], "fresh": True}

    if "wasted" in ev and not any(k in ev for k in ("scan", "clue", "remove", "restore")):
        say("ivy", "ivy.wasted", reason=ev["wasted"]["reason"])

    # Fire and wind are off the HUD now, so Ember keeps an eye on them for you.
    if not chars["ember"]["fresh"]:
        risk = view.get("fire_risk")
        strong = view.get("wind_str", 1) >= 2
        if risk == "high":
            say("ember", "ember.risk_high_wind" if strong else "ember.risk_high")
        elif risk == "med":
            say("ember", "ember.risk_med")


class Coach:
    """Watch the mix of actions and, when the player is one-dimensional (say, only
    restoring), have Ivy nudge them toward what they are neglecting: also look
    around, also remove lantana, also restore the ground they clear. Each nudge
    fires once; once all three are tried, a single 'you've got the loop' note."""
    CAT = {"satellite": "look", "drone": "look", "survey": "look", "ask": "look",
           "clue": "look", "remove": "remove", "burn": "remove", "crew": "remove",
           "restore": "restore"}
    # after doing X, which neglected thing to point at next (in priority order)
    NEXT = {"restore": ["remove", "look"], "remove": ["restore", "look"],
            "look": ["remove", "restore"]}
    KEY = {"look": "coach.try_look", "remove": "coach.try_remove", "restore": "coach.try_restore"}

    def __init__(self):
        self.counts = {"look": 0, "remove": 0, "restore": 0}
        self.last = None
        self.nudged = set()
        self.praised = False

    def observe(self, action_type):
        cat = self.CAT.get(action_type)
        if cat:
            self.counts[cat] += 1
            self.last = cat

    def nudge_key(self, view):
        """The text key for Ivy's nudge this turn, or None. She only points at
        things that are actually on screen and available: no 'remove lantana'
        when none is visible, no 'restore' with no bare ground, no 'use a drone'
        before it is unlocked."""
        if all(self.counts[c] > 0 for c in ("look", "remove", "restore")):
            if not self.praised:
                self.praised = True
                return "coach.balanced"
            return None
        if self.last is None:
            return None
        for cat in self.NEXT.get(self.last, []):
            if self.counts[cat] == 0 and cat not in self.nudged and self._relevant(cat, view):
                self.nudged.add(cat)
                return self._key(cat, view)
        return None

    @staticmethod
    def _relevant(cat, view):
        cells = view.get("cells", [])
        if cat == "remove":
            return any(c.get("cover") == "invasive" for c in cells)   # visible lantana
        if cat == "restore":
            return any(c.get("cover") == "bare" for c in cells)       # visible bare ground
        if cat == "look":
            return any(c.get("detail", 3) < 2 for c in cells)         # something left to reveal
        return True

    def _key(self, cat, view):
        if cat == "look":
            has_drone = view.get("unlocks", {}).get("drone", True)
            return "coach.try_look" if has_drone else "coach.try_look_sat"
        return self.KEY[cat]


def draw(view: dict, chars: dict, overlay: dict = None, show_dss: bool = True):
    clear()
    u = view.get("unlocks", {})
    if u.get("level", 0) == 0:
        tools = f"{FG(40)}all tools (sandbox){R.RESET}"
    else:
        names = [("satellite", "sat"), ("drone", "drone"), ("translator", "ask"), ("dss", "DSS")]
        have = [lbl for k, lbl in names if u.get(k)]
        tools = f"{FG(245)}game {u['level']}: {FG(255)}{' '.join(have)}{R.RESET}"
    print(f"{FG(208)}  P Y R O C E N E {R.RESET}{FG(245)}  Night {view['turn']}/{view['max_turns']}   {R.RESET}{tools}\n")
    print(R.render_status(view))
    inc = view.get("incoming")
    if inc:
        icon = {"drought": "☀", "monsoon": "🌧", "grazing": "🐄", "work_party": "🤝"}.get(inc["type"], "!")
        cue = {"drought": "dry days, fire rises", "monsoon": "seeds wash to the banks",
               "grazing": "a new outbreak on churned ground",
               "work_party": "volunteers will uproot a stand"}.get(inc["type"], "")
        when = "TONIGHT" if inc["nights"] == 0 else f"{inc['nights']} night" + ("s" if inc["nights"] != 1 else "")
        col = 40 if inc["type"] == "work_party" else 214
        label = inc["type"].upper().replace("_", " ")
        print(f"{FG(col)}  {icon} {label} incoming ({cue}) {FG(255)}in {when}{R.RESET}")
    eff = view.get("effects") or {}
    if eff:
        tags = "  ".join(f"{FG(203)}{k.upper()}{R.RESET}" for k in eff)
        print(f"  {FG(245)}in effect:{R.RESET} {tags}")
    adv = view.get("dss_advice")
    if adv and show_dss:
        import textwrap
        wrapped = textwrap.wrap(adv, 68)
        print(f"{FG(45)}  DSS >{R.RESET} {FG(51)}{wrapped[0]}{R.RESET}")
        for w in wrapped[1:]:
            print(f"{FG(51)}       {w}{R.RESET}")
    print()
    board = R.render_board(view, overlay=overlay).split("\n")
    panel = R.render_char_panel(chars)
    bw = 4 + view["cols"] * 2
    for i in range(max(len(board), len(panel))):
        left = board[i] if i < len(board) else " " * bw
        right = panel[i] if i < len(panel) else ""
        print(left + "  " + right)
    print()
    print(R.render_legend())
    job = R.render_job(view)
    if job:
        print("\n" + job)


def animate_fire(view: dict, cells: list, delay: float):
    order = list(cells)
    shown = set()
    for i in order:
        shown.add(i)
        clear()
        print(f"{FG(196)}  *** WILDFIRE ***{R.RESET}\n")
        print(R.render_status(view))
        print()
        print(R.render_board(view, fire=frozenset(shown)))
        time.sleep(delay)


def announce_event(ev_type: str, note: str, demo: bool):
    """A disaster (or boon) lands: a framed card with the real-ecology field note."""
    import textwrap
    label = {"drought": "DROUGHT", "monsoon": "MONSOON", "grazing": "CATTLE DRIVE",
             "work_party": "COMMUNITY WORK PARTY"}.get(ev_type, ev_type.upper())
    col = 40 if ev_type == "work_party" else 208
    clear()
    print(f"\n{FG(col)}  ═══════  {label}  ═══════{R.RESET}\n")
    for line in textwrap.wrap(note, 58):
        print(f"  {FG(250)}{line}{R.RESET}")
    print(f"\n  {FG(45)}FIELD NOTE{R.RESET} {FG(245)}(real lantana ecology){R.RESET}")
    if demo:
        time.sleep(1.9)
    else:
        try:
            input(f"\n  {FG(245)}press Enter{R.RESET}")
        except (EOFError, KeyboardInterrupt):
            pass


def animate_remove(view: dict, reclaimed: list, reinvaded: list, delay: float):
    """Brief flash after pulling saplings: green fills the ones native forest
    reclaims; purple sweeps back into the ones an invasive source sits beside."""
    if not (reclaimed or reinvaded):
        return
    header = (f"{FG(203)}  weeds sweep back in...{R.RESET}" if reinvaded
              else f"{FG(40)}  natives fill in...{R.RESET}")
    for frame in range(4):
        on = frame % 2 == 0
        ov = {}
        for i in reinvaded:
            ov[i] = R.bg(90) + R.fg(219) + ("><" if on else "vv") + R.RESET
        for i in reclaimed:
            ov[i] = R.bg(22) + R.fg(120) + (r"\/" if on else "  ") + R.RESET
        clear()
        print(header + "\n")
        print(R.render_status(view))
        print()
        print(R.render_board(view, overlay=ov))
        time.sleep(delay)


def turn_prompt(view: dict) -> dict | None:
    job = view.get("job")
    ready = bool(job and job["type"] == "burn" and job["ready"])
    if ready:
        wind = ["still", "a breeze", "strong"][view["wind_str"]]
        if view["wind_str"] > 1:
            print(f"\n{FG(214)}Fire lines are ready. The wind is {FG(196)}{wind}{FG(214)}.{R.RESET}")
            print(f"{FG(245)}Light the fire?  {FG(196)}[Enter] lights it now (risky!){R.RESET}"
                  f"   {FG(245)}'w' = wait for calm   'a' = abort{R.RESET}")
        else:
            print(f"\n{FG(40)}Fire lines are ready and the wind is {wind}, safe to burn.{R.RESET}")
            print(f"{FG(245)}Light the fire?  {FG(40)}[Enter] = light{R.RESET}"
                  f"   {FG(245)}'w' = wait   'a' = abort{R.RESET}")
    elif job:
        print(f"\n{FG(245)}(the crew is committed. press Enter to keep working, or 'a' to abort){R.RESET}")
    else:
        print(f"\n{FG(245)}(type 'help' for commands){R.RESET}")
    while True:
        try:
            raw = input(f"{FG(208)}night {view['turn']} >{R.RESET} ")
        except (EOFError, KeyboardInterrupt):
            return None
        cmd = raw.strip().lower()
        if cmd in ("quit", "q", "exit"):
            return None
        if cmd in ("help", "h", "?"):
            print(help_text(view))
            continue
        # while a job runs: Enter advances it; the light decision is an explicit yes/no
        if job:
            if cmd in ("a", "abort", "cancel", "stop"):
                return {"type": "abort"}
            if ready:
                if cmd == "" or cmd in ("light", "l", "yes", "y"):
                    return {"type": "ignite"}
                if cmd in ("w", "wait", "n", "no", "hold"):
                    return {"type": "continue"}
                print(f"{FG(214)}Press Enter to light, 'w' to wait, or 'a' to abort.{R.RESET}")
                continue
            if cmd == "" or cmd in ("go", "continue", "c"):
                return {"type": "continue"}
            print(f"{FG(214)}Press Enter to keep working, or 'a' to abort.{R.RESET}")
            continue
        if cmd == "":
            continue
        parts = raw.split()
        cmd = parts[0].lower()
        unlocks = view.get("unlocks", {})
        if cmd in ("sat", "satellite"):
            return {"type": "satellite"}
        if cmd == "pass":
            return {"type": "pass"}
        if cmd in ("drone", "survey") and not unlocks.get(cmd, True):
            print(f"{FG(214)}{cmd} isn't unlocked yet (unlocks at level 2){R.RESET}")
            continue
        if cmd in ("drone", "survey", "remove", "rm", "restore", "burn", "crew",
                   "ask", "elders", "clue"):
            if len(parts) < 2:
                print(f"{FG(214)}need a cell, e.g. {cmd} D4{R.RESET}")
                continue
            tgt = parse_cell(parts[1], view)
            if tgt is None:
                print(f"{FG(214)}'{parts[1]}' is not a cell on the board{R.RESET}")
                continue
            t = {"rm": "remove", "ask": "clue", "elders": "clue"}.get(cmd, cmd)
            return {"type": t, "target": tgt}
        print(f"{FG(214)}unknown command '{cmd}'. type help{R.RESET}")


def end_screen(view: dict, state, delay_ok: bool, show_lesson: bool = True):
    st = view["status"]
    need = view.get("resilience", {}).get("need", 3)
    target = view["thresholds"]["win"]
    color = {"gold": 46, "win": 40, "lose": 196}[st]
    title = T("endings", f"{st}.title")
    if st == "win":
        sub = T("endings", "win.sub", target=target, need=need)
    elif st == "gold":
        sub = T("endings", "gold.sub")
    else:
        sub = view["lose_reason"] or T("endings", "lose.default")
    print(f"\n{FG(color)}  ====== {title} ======{R.RESET}")
    print(f"  {FG(250)}{sub}{R.RESET}")
    print(f"  {FG(250)}{T('endings', 'stats', health=view['health'], wildlife=view['wildlife'], turn=view['turn'])}{R.RESET}")
    if show_lesson:
        print(f"\n  {FG(45)}{T('endings', 'lesson_label')}:{R.RESET} {FG(250)}{T('endings', 'lesson')}{R.RESET}\n")


# harder tiers for "true fans" / real ecologists: the field notes stop being
# flavour and become the strategy (know the ecology, or the disasters bury you).
LEVEL_PRESETS = {
    # level 5 = level-4 game PLUS more variables: the telegraphed disasters
    # (grazing/drought/monsoon) and a richer, staler landscape. Harder, not brutal.
    5: {"obs_decay_turns": 2, "hill_blobs": 3, "roads": 2, "max_turns": 16,
        "events_on": True, "event_types": ["grazing", "drought", "monsoon"],
        "event_gap": (2, 3), "first_event_night": 4},
}


# ---- the office (pokeflow) phases: full-screen, flicker-free, between levels --
# The campaign alternates OFFICE phases (full-screen pokeflow, here) with FIELD
# phases (the ordinary game + text character panel). The host owns the terminal
# and the loop; pokeflow is pumped (tick / feed_key / render_lines). See
# ../pokeflow/HOST-RUNTIME.md. Field play is unchanged, no jitter there.
_HUB_GREETINGS = {
    "ivy": "I'm your eyes. Satellite, drone, surveys, I find where the invasive lantana hides.",
    "rocky": "I'm the hands. Point me at a patch and I clear it. But I can't act on what I can't see.",
    "ember": "I watch the threats. Wildfire feeds on the dry invasive growth, get ahead of it or it spreads.",
    "elder": "The families here have watched this valley for generations. Ask, and we point the way.",
}


class _raw_terminal:
    """Put the tty in cbreak mode for per-keystroke reads; restore on exit."""
    def __enter__(self):
        self.fd = sys.stdin.fileno()
        self.old = termios.tcgetattr(self.fd)
        tty.setcbreak(self.fd)
        return self

    def __exit__(self, *a):
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old)


def _read_key(timeout=0.05):
    """One normalized key ('up'/'down'/'left'/'right'/'interact'/'cancel'/'quit'),
    or None if nothing arrives within `timeout`."""
    if not select.select([sys.stdin], [], [], timeout)[0]:
        return None
    ch = sys.stdin.read(1)
    if ch == "\x1b":  # an arrow escape sequence, or a bare Esc
        if select.select([sys.stdin], [], [], 0.002)[0]:
            rest = sys.stdin.read(2)
            return {"[A": "up", "[B": "down", "[C": "right", "[D": "left"}.get(rest, "cancel")
        return "cancel"
    return {"w": "up", "s": "down", "a": "left", "d": "right",
            "z": "interact", "\r": "interact", "\n": "interact", " ": "interact",
            "q": "quit"}.get(ch)


# flicker-free full-screen drawing: home the cursor and overwrite in place,
# rather than clearing the whole screen each frame (which flashes).
_CLS = "\x1b[2J\x1b[H"      # full clear, once, on entering the office
_HOME = "\x1b[H"           # cursor to top-left (no clear), the anti-flicker move
_HIDE = "\x1b[?25l"
_SHOW = "\x1b[?25h"
_EOL = "\x1b[K"            # clear to end of line (in case a line got shorter)
_EOS = "\x1b[J"            # clear to end of screen (below the frame)


def _office_frame(lines: list, header: str = ""):
    rows = [f"{FG(208)}  P Y R O C E N E{R.RESET}", ""]
    if header:
        rows += [f"  {FG(245)}{header}{R.RESET}", ""]
    rows += ["  " + ln for ln in lines]
    sys.stdout.write(_HOME + "".join(r + _EOL + "\n" for r in rows) + _EOS)
    sys.stdout.flush()


def _office_pump(panel, header: str, fps: int = 30):
    """Play a walk-up / grant / entrance to completion, flicker-free."""
    dt = 1.0 / fps
    guard = 0
    while not panel.pf.is_idle() and guard < fps * 12:
        panel.tick(int(dt * 1000))
        _office_frame(panel.render(), header)
        time.sleep(dt)
        guard += 1
    _office_frame(panel.render(), header)


def _office_roam(panel, hint: str, fps: int = 30) -> str:
    """Hand the office to the player until they walk to the exit. Movement and
    talk are pokeflow's; the host only reads keys and forwards them."""
    panel.focus_hub()
    panel.drain()
    with _raw_terminal():
        while True:
            _office_frame(panel.render(), hint)
            k = _read_key(1.0 / fps)
            if k == "quit":
                return "quit"
            if k:
                panel.feed(k)
            panel.tick(int(1000 / fps))
            for e in panel.drain():
                if e["evt"] == "intent.proceed":
                    return "proceed"
                if e["evt"] == "actor.talk_requested":
                    panel.pf.send({"cmd": "actor.speak", "actor": e["actor"],
                                   "text": _HUB_GREETINGS.get(e["actor"], "...")})


def _apply_office_step(panel, step: dict):
    pf = panel.pf
    if "present" in step:
        cmd = {"cmd": "actor.present", "actor": step["present"]}
        if "at" in step:
            cmd["at"] = step["at"]
        pf.send(cmd)
    elif "say" in step:
        who, txt = step["say"]
        pf.send({"cmd": "actor.speak", "actor": who, "text": txt})
    elif "dismiss" in step:
        pf.send({"cmd": "actor.dismiss", "actor": step["dismiss"]})
    elif "grant" in step:
        gid, frm = step["grant"]
        pf.send({"cmd": "grant.deliver", "grant": gid, "from": frm})


def office_phase(panel, steps: list) -> str:
    """Run one full-screen office scene: scripted beats and/or free roam.
    Returns 'proceed' or 'quit'."""
    if not sys.stdin.isatty():
        return "proceed"          # non-interactive: skip the office
    panel.focus_hub()
    panel.drain()
    sys.stdout.write(_CLS + _HIDE)
    header = ""
    try:
        for step in steps:
            if "note" in step:
                header = step["note"]
                _office_frame(panel.render(), header)
            elif "roam" in step:
                if _office_roam(panel, step["roam"]) == "quit":
                    return "quit"
            else:
                _apply_office_step(panel, step)
                _office_pump(panel, header)
                time.sleep(0.6)   # a beat between lines so it doesn't rush
    finally:
        sys.stdout.write(_SHOW)
    return "proceed"


# ---- the campaign: office <-> field, learning-by-losing until the DSS wins ---
# Each office scene is a list of steps: {"note": header} | {"roam": hint} |
# {"say": (actor, text)} | {"present": actor} | {"dismiss": actor} |
# {"grant": (grant_id, from_actor)}. Field level N maps to the game's unlock
# level N (1 satellite, 2 +drone, 3 +translator, 4 +DSS, 5 +disasters).
_OFFICE_INTRO = [
    {"note": "Your first night at the field station. Meet the team, then head out."},
    {"roam": "walk: arrows/WASD  ·  talk: z (stand next to someone)  ·  leave: walk onto >>"},
]
_OFFICE_AFTER_L1 = [
    {"note": "Back at the station. Ivy ran a full ground survey of where you worked."},
    {"say": ("ivy", "Look, fresh seedlings everywhere the satellite called 'clean'.")},
    {"say": ("ivy", "Satellite only resolves the big dense stands. The young growth slips right past it.")},
    {"present": "manager"},
    {"say": ("manager", "Rough season. But the budget came through, here's a drone. Ivy, put it to use.")},
    {"grant": ("drone", "ivy")},
    {"dismiss": "manager"},
    {"say": ("ivy", "Now we can confirm the haze. Next run, drone the suspect cells before you clear.")},
]
_OFFICE_AFTER_L2 = [
    {"note": "Another hard season. The drone helped, but the sources keep reseeding."},
    {"say": ("ivy", "We found real patches this time. We just can't keep up with the hidden sources alone.")},
    {"say": ("ivy", "The families here know where trouble always returns. Let me introduce someone.")},
    {"present": "elder"},
    {"say": ("elder", "(a greeting in an old dialect you can't quite follow)")},
    {"say": ("ivy", "Here, a translator. Now you can ask the elders, and understand the answer.")},
    {"grant": ("ask", "ivy")},
    {"say": ("elder", "Ask, and I will point you to the old strongholds.")},
    {"dismiss": "elder"},
]
_OFFICE_AFTER_L3 = [
    {"note": "You're losing by less each time. Ivy has been building something."},
    {"say": ("ivy", "Drone, the elders, Rocky's field notes, Ember's fire watch, alone, none of it holds.")},
    {"say": ("ivy", "So I put them together: a decision support system. It names the one hotspot to cut each night.")},
    {"say": ("rocky", "Finally. Point me right and I'll hold the line.")},
    {"say": ("ember", "And I'll flag the fire risk before it can jump.")},
    {"grant": ("dss", "ivy")},
    {"say": ("ivy", "This run, follow the DSS. I think we can actually hold it.")},
]
_OFFICE_AFTER_L4 = [
    {"note": "You held the line. The valley is recovering."},
    {"say": ("rocky", "We did it. Native forest's coming back, and holding.")},
    {"say": ("ivy", "The numbers agree. First real win.")},
    {"present": "manager"},
    {"say": ("manager", "Good work. But don't pack up, there's a storm building. Flood alert for the low banks.")},
    {"dismiss": "manager"},
    {"say": ("ember", "Monsoon washes seeds down to the water's edge; drought before it feeds my fire. This is the real test.")},
]
_OFFICE_END = [
    {"note": "End of the season."},
    {"say": ("ivy", "Whatever the season threw at us, you read the land and acted on it.")},
    {"say": ("rocky", "That's the job. See you next season.")},
]

CAMPAIGN = [
    ("office", _OFFICE_INTRO),
    ("field", 1),
    ("office", _OFFICE_AFTER_L1),
    ("field", 2),
    ("office", _OFFICE_AFTER_L2),
    ("field", 3),
    ("office", _OFFICE_AFTER_L3),
    ("field", 4),
    ("office", _OFFICE_AFTER_L4),
    ("field", 5),
    ("office", _OFFICE_END),
]


def _enter_field(level: int):
    tools = {1: "satellite only", 2: "satellite + drone", 3: "+ ask the elders",
             4: "+ the DSS advisor", 5: "the DSS, and a storm coming"}[level]
    clear()
    print(f"\n{FG(208)}  Into the field, night falls.{R.RESET}\n")
    print(f"  {FG(245)}This run you have: {FG(255)}{tools}{R.RESET}")
    print(f"  {FG(245)}(type 'help' for commands){R.RESET}")
    try:
        input(f"\n  {FG(245)}press Enter to begin{R.RESET}")
    except (EOFError, KeyboardInterrupt):
        pass


def _field_result(final, level: int):
    v = observable(final)
    clear()
    if v["status"] in ("win", "gold"):
        print(f"\n{FG(40)}  You held the line, native forest {v['health']}%.{R.RESET}")
    else:
        print(f"\n{FG(203)}  The season ended. The forest didn't hold ({v['health']}%).{R.RESET}")
        if v.get("lose_reason"):
            print(f"  {FG(245)}{v['lose_reason']}{R.RESET}")
    try:
        input(f"\n  {FG(245)}press Enter, back to the station{R.RESET}")
    except (EOFError, KeyboardInterrupt):
        pass


def run_campaign(seed, demo=False):
    if not sys.stdin.isatty():
        print("The campaign needs an interactive terminal (arrow keys to walk the office).")
        return
    if seed is None:
        seed = 7
    from .pokeflow_panel import PokeflowPanel
    panel = PokeflowPanel(color=R.USE_COLOR)
    for kind, payload in CAMPAIGN:
        if kind == "office":
            if office_phase(panel, payload) == "quit":
                print("\nYou left the station. The valley waits.")
                return
        else:
            level = payload
            _enter_field(level)
            config = {"unlock_level": level}
            config.update(LEVEL_PRESETS.get(level, {}))
            state = new_game(seed=seed, config=config)
            final = _play_field(state, demo=False)
            if final is None:
                print("\nYou left the field. The forest remembers.")
                return
            _field_result(final, level)
    print(f"\n{FG(40)}  end of the season{R.RESET}")


def _demo_bot(s):
    # clear the most-grown weeds you can see (stop them spreading), then scan
    v = observable(s)
    vis = [c for c in v["cells"] if c["cover"] == "invasive"]
    if vis:
        return {"type": "remove", "target": max(vis, key=lambda c: c["stage"])["index"]}
    if not any(c["detail"] >= 1 for c in v["cells"]):
        return {"type": "satellite"}
    cand = [c for c in v["cells"] if c["cover"] not in ("water", "village") and c["detail"] < 2]
    cand.sort(key=lambda c: (c["last_seen"], c["index"]))
    return {"type": "drone", "target": cand[0]["index"]} if cand else {"type": "pass"}


# ---- field notes: the real world behind a tool the player just used ---------
# Shown once per run, the first time a tool is used. Text lives in text/learn.txt
# so the wording and the case studies can be changed without touching this file.
_SEEN_NOTES = set()


def _typeout(text: str, indent: str, color: int, cps: float = 0.018):
    """Print text a character at a time, so it reads as someone speaking."""
    for line in R._wrap(text, 62):
        print(f"{indent}{FG(color)}", end="", flush=True)
        for ch in line:
            print(ch, end="", flush=True)
            time.sleep(cps)
        print(R.RESET, flush=True)


def field_note(topic: str) -> str:
    """Ivy explains why a tool matters, then the player pages through real cases.
    Returns 'ok' or 'quit'."""
    meta = R.CHAR_META["ivy"]
    col = meta["color"]
    clear()
    print()
    print(f"   {FG(col)}{meta['fig'][0]}{R.RESET}   {FG(col)}{meta['name']}{R.RESET}  {FG(240)}{meta['tag']}{R.RESET}")
    print(f"   {FG(col)}{meta['fig'][1]}{R.RESET}")
    print()
    _typeout(T("learn", f"{topic}.intro"), "     ", 250)
    print()

    n = 1
    while has("learn", f"{topic}.case{n}.title"):
        last = not has("learn", f"{topic}.case{n + 1}.title")
        try:
            input(f"\n   {FG(245)}{T('learn', 'nav.more')}{R.RESET}")
        except (EOFError, KeyboardInterrupt):
            return "quit"
        clear()
        print(f"\n   {FG(220)}{T('learn', f'{topic}.case{n}.title')}{R.RESET}\n")
        for para in T("learn", f"{topic}.case{n}.body").split("\n\n"):
            for line in R._wrap(para, 62):
                print(f"   {FG(250)}{line}{R.RESET}")
            print()
        for line in tlines("learn", f"{topic}.case{n}.source"):
            print(f"   {FG(240)}{line}{R.RESET}")
        n += 1
        if last:
            try:
                input(f"\n   {FG(245)}{T('learn', 'nav.done')}{R.RESET}")
            except (EOFError, KeyboardInterrupt):
                return "quit"
    return "ok"


def _play_field(state, demo, delay=0.14):
    """The field game loop, with the original text character panel. Returns the
    final state, or None if the player quit. Unchanged from the standalone game
   , this is deliberately the same low-refresh rendering (no jitter)."""
    chars = initial_chars()
    coach = Coach()
    while state.status == "playing":
        view = observable(state)
        draw(view, chars)
        if demo:
            time.sleep(0.7)
            action = _demo_bot(state)
            print(f"\n{FG(208)}night {view['turn']} > {R.RESET}{action['type']}"
                  + (f" {cell_name(action['target'], view)}" if action.get("target") is not None else ""))
            time.sleep(0.4)
        else:
            action = turn_prompt(view)
            if action is None:
                return None
        state, events = apply(state, action)
        ev_hit = next((e for e in events if e["type"] == "event"), None)
        if ev_hit:
            announce_event(ev_hit["event"], ev_hit["note"], demo)
        rm_ev = next((e for e in events if e["type"] == "remove"), None)
        if rm_ev and (rm_ev["reclaimed"] or rm_ev["reinvaded"]):
            animate_remove(observable(state), rm_ev["reclaimed"], rm_ev["reinvaded"], 0.16)
        fire_ev = next((e for e in events if e["type"] == "fire"), None)
        if fire_ev:
            animate_fire(observable(state), fire_ev["cells"], delay)
            time.sleep(0.4)
        post = observable(state)
        update_chars(chars, events, post)
        # Ivy coaches breadth: if the player is neglecting an action, she nudges,
        # but only about things that are actually on screen and unlocked.
        coach.observe(action.get("type"))
        nudge = coach.nudge_key(post)
        if nudge:
            chars["ivy"] = {"text": T("characters", nudge), "fresh": True}
        # The first satellite scan is the moment the point lands, so let them see
        # what it revealed, then hand them the real-world version of it.
        if not demo and action.get("type") == "satellite" and "sat" not in _SEEN_NOTES:
            _SEEN_NOTES.add("sat")
            draw(post, chars)
            time.sleep(1.1)
            if field_note("sat") == "quit":
                return None
    draw(observable(state), chars)
    return state


def run_interactive(seed, demo, level=0):
    if demo and seed is None:
        seed = 1  # a curated showcase: DSS-guided win by night 9
    config = {"unlock_level": level}
    config.update(LEVEL_PRESETS.get(level, {}))
    state = new_game(seed=seed, config=config)
    final = _play_field(state, demo)
    if final is None:
        print("left the field. the forest remembers.")
        return
    end_screen(observable(final), final, not demo)


# ---- the story: levels threaded together with character talk screens ---------
# A briefing before each level and a debrief after it, delivered by the team as
# simple talk screens (figure + name + words). Text lives in text/story.txt.
def talk_screen(speech: list, highlight=None) -> str:
    """speech: list of (character_key, text). highlight: a set of keys to
    emphasise (the rest dim). Returns 'ok' or 'quit'."""
    import textwrap
    hl = highlight or set()
    clear()
    print()
    for who, text in speech:
        meta = R.CHAR_META.get(who, {"name": who.upper(), "color": 250,
                                     "fig": ["( )", "/|\\"], "tag": ""})
        col = meta["color"]
        fig = meta["fig"]
        mark = f"{FG(220)}> {R.RESET}" if who in hl else "  "
        wrapped = textwrap.wrap(text, 58) or [""]
        print(f"   {FG(col)}{fig[0]}{R.RESET}   {mark}{FG(col)}{meta['name']}{R.RESET}  {FG(240)}{meta.get('tag', '')}{R.RESET}")
        print(f"   {FG(col)}{fig[1]}{R.RESET}     {FG(250)}{wrapped[0]}{R.RESET}")
        for w in wrapped[1:]:
            print(f"           {FG(250)}{w}{R.RESET}")
        print()
    try:
        input(f"   {FG(245)}press Enter{R.RESET}")
    except (EOFError, KeyboardInterrupt):
        return "quit"
    return "ok"


# level -> ([(speaker, story_key), ...], highlight_set)
_STORY_BRIEF = {
    1: ([("ivy", "l1.brief.ivy")], None),
    2: ([("ivy", "l2.brief.ivy")], None),
    3: ([("ivy", "l3.brief.ivy"), ("rocky", "l3.brief.rocky")], {"rocky"}),
    4: ([("ivy", "l4.brief.ivy")], None),
    5: ([("ivy", "l5.brief.ivy")], None),
}
_STORY_DEBRIEF = {
    1: ([("ivy", "l1.debrief.ivy")], None),
    2: ([("ivy", "l2.debrief.ivy"), ("rocky", "l2.debrief.rocky")], None),
    3: ([("ivy", "l3.debrief.ivy")], None),
    4: ([("rocky", "l4.debrief.rocky"), ("ivy", "l4.debrief.ivy")], None),
    5: ([], None),
}


def _talk(beat) -> str:
    speech, highlight = beat
    resolved = [(who, T("story", key)) for who, key in speech]
    return talk_screen(resolved, highlight) if resolved else "ok"


def run_story(seed):
    """Play the levels in sequence, with a briefing before each and a debrief
    after. Losing does not end the run; the team explains and hands you the next
    tool, exactly the intended learning curve."""
    if seed is None:
        seed = 7
    for level in (1, 2, 3, 4, 5):
        if _talk(_STORY_BRIEF[level]) == "quit":
            return
        config = {"unlock_level": level}
        config.update(LEVEL_PRESETS.get(level, {}))
        state = new_game(seed=seed, config=config)
        final = _play_field(state, demo=False)
        if final is None:
            print("left the field. the forest remembers.")
            return
        end_screen(observable(final), final, True, show_lesson=False)
        try:
            input(f"\n  {FG(245)}press Enter to proceed{R.RESET}")
        except (EOFError, KeyboardInterrupt):
            return
        if _talk(_STORY_DEBRIEF[level]) == "quit":
            return
    clear()
    print(f"\n\n  {FG(40)}{T('story', 'end')}{R.RESET}\n")


# ---- start menu + tutorial ("learn the game") -------------------------------
def start_menu() -> str:
    """The opening choice. Returns 'learn', 'play', or 'quit'."""
    clear()
    print(f"\n\n{FG(208)}          {T('menu', 'title')}{R.RESET}\n")
    print(f"       {FG(245)}{T('menu', 'tagline')}{R.RESET}\n\n")
    print(f"          {FG(114)}[ 1 ]  {T('menu', 'learn')}{R.RESET}")
    print(f"          {FG(45)}[ 2 ]  {T('menu', 'play')}{R.RESET}\n")
    while True:
        try:
            raw = input(f"       {FG(245)}{T('menu', 'prompt')}{R.RESET} ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return "quit"
        if raw in ("1", "learn", "l"):
            return "learn"
        if raw in ("2", "play", "p"):
            return "play"
        if raw in ("q", "quit"):
            return "quit"


def _tut_screen(title_key: str, body_key: str) -> str:
    clear()
    print(f"\n{FG(208)}  {T('tutorial', title_key)}{R.RESET}\n")
    for ln in tlines("tutorial", body_key):
        print(f"  {FG(250)}{ln}{R.RESET}")
    try:
        input(f"\n  {FG(245)}{T('tutorial', 'continue')}{R.RESET}")
    except (EOFError, KeyboardInterrupt):
        return "quit"
    return "ok"


def _tutorial_state():
    """A fully-revealed practice landscape (no fog) so the learner can see and
    act on everything."""
    state = new_game(seed=31337, config={"unlock_level": 0, "max_turns": 30})
    for c in state.cells:
        c.obs = GROUND
        c.last_seen = state.turn
    return state


def _place_bare_patch(state, r: int, c: int, size: int = 2) -> list:
    """Turn a small square of land to bare ground; return the cell indices."""
    cols = state.cols
    idxs = []
    for dr in range(size):
        for dc in range(size):
            rr, cc = r + dr, c + dc
            if 0 <= rr < state.rows and 0 <= cc < cols:
                cell = state.cells[rr * cols + cc]
                if cell.cover in (NATIVE, INVASIVE):
                    cell.cover, cell.stage, cell.stage_age, cell.seedbank = BARE, 0, 0, False
                    idxs.append(rr * cols + cc)
    return idxs


def _highlight(cells) -> dict:
    """Mark the tutorial target cells: keep the bare-ground look, but blink and
    brighten so they read as 'the same tiles, pay attention to these'."""
    glyph = R.BLINK + R.bg(137) + R.fg(231) + "░░" + R.RESET
    return {i: glyph for i in cells}


def _walk_step(title: str, body_lines: list, cap_key: str) -> str:
    """One walkthrough screen: show ONLY one piece of the UI, with its caption."""
    import textwrap
    clear()
    print(f"\n{FG(208)}  {title}{R.RESET}\n")
    for ln in body_lines:
        print("  " + ln)
    print()
    for w in textwrap.wrap(T("tutorial", cap_key), 68):
        print(f"  {FG(220)}{w}{R.RESET}")
    try:
        input(f"\n  {FG(245)}{T('tutorial', 'enter')}{R.RESET}")
    except (EOFError, KeyboardInterrupt):
        return "quit"
    return "ok"


def _tut_walkthrough(state) -> str:
    """Introduce the screen one piece at a time: render only the score, then only
    the team, then only the map, then only the legend."""
    view = observable(state)
    chars = initial_chars()
    steps = [
        ("Your score", R.render_status(view).split("\n"), "cap.score"),
        ("Your team", R.render_char_panel(chars), "cap.friends"),
        ("The map", R.render_board(view).split("\n"), "cap.map"),
        ("The legend", R.render_legend().split("\n"), "cap.legend"),
    ]
    for title, body, cap in steps:
        if _walk_step(title, body, cap) == "quit":
            return "quit"
    return "ok"


def _tut_task_restore(state) -> str:
    chars = initial_chars()
    r, c = state.rows // 2, state.cols // 2
    patch = _place_bare_patch(state, r, c, 2)
    center = patch[0] if patch else r * state.cols + c
    while True:
        view = observable(state)
        name = cell_name(center, view)
        draw(view, chars, overlay=_highlight(patch), show_dss=False)
        print(f"\n  {FG(114)}{T('tutorial', 'task1.header')}{R.RESET}")
        print(f"  {FG(250)}{T('tutorial', 'task1.prompt', name=name)}{R.RESET}")
        print(f"  {FG(45)}{T('tutorial', 'task1.hint', name=name)}{R.RESET}")
        try:
            raw = input("  > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return "quit"
        if raw in ("skip", "s"):
            return "ok"
        parts = raw.split()
        if parts and parts[0] in ("restore", "remove", "rm") and len(parts) >= 2:
            tgt = parse_cell(parts[1], view)
            if tgt is None:
                print(f"  {FG(214)}{T('tutorial', 'task1.badcell', tok=parts[1], name=name)}{R.RESET}")
                continue
            t = "remove" if parts[0] in ("remove", "rm") else "restore"
            before = view["health"]
            state, _ = apply(state, {"type": t, "target": tgt})
            after = observable(state)["health"]
            if after > before:
                draw(observable(state), chars, show_dss=False)
                print(f"\n  {FG(40)}{T('tutorial', 'task1.success', before=before, after=after)}{R.RESET}")
                try:
                    input(f"  {FG(245)}{T('tutorial', 'enter')}{R.RESET}")
                except (EOFError, KeyboardInterrupt):
                    return "quit"
                return "ok"
            print(f"  {FG(214)}{T('tutorial', 'task1.nochange', name=name)}{R.RESET}")
        else:
            print(f"  {FG(214)}{T('tutorial', 'task1.retype', name=name)}{R.RESET}")


def _tut_task_watch(state) -> str:
    chars = initial_chars()
    # make the decline vivid: mature the existing lantana and let it rip
    dense = 0
    for cell in state.cells:
        if cell.cover == INVASIVE:
            if cell.stage < ESTABLISHED:
                cell.stage = ESTABLISHED
            if dense < 5:
                cell.stage, dense = DENSE, dense + 1
    state.config.update({"spread_established": 0.45, "spread_dense": 0.55,
                         "seedbank_regrow": 0.5, "hotspot_reseed": 0.5,
                         "fire_per_dense": 0.10})
    start = observable(state)["health"]
    for _ in range(6):
        view = observable(state)
        if view["status"] != "playing":
            break
        draw(view, chars, show_dss=False)
        print(f"\n  {FG(203)}{T('tutorial', 'task2.header')}{R.RESET}")
        print(f"  {FG(250)}{T('tutorial', 'task2.prompt', turn=view['turn'], health=view['health'])}{R.RESET}")
        try:
            input(f"  {FG(245)}{T('tutorial', 'task2.pass')}{R.RESET}")
        except (EOFError, KeyboardInterrupt):
            return "quit"
        state, events = apply(state, {"type": "pass"})
        fire_ev = next((e for e in events if e["type"] == "fire"), None)
        if fire_ev:
            animate_fire(observable(state), fire_ev["cells"], 0.12)
            update_chars(chars, events, observable(state))
            break   # the first fire makes the point; end the round here
        update_chars(chars, events, observable(state))
    end = observable(state)["health"]
    draw(observable(state), chars, show_dss=False)
    print(f"\n  {FG(203)}{T('tutorial', 'task2.result', start=start, end=end)}{R.RESET}")
    try:
        input(f"\n  {FG(245)}{T('tutorial', 'enter')}{R.RESET}")
    except (EOFError, KeyboardInterrupt):
        return "quit"
    return "ok"


def run_tutorial():
    if _tut_screen("welcome.title", "welcome.body") == "quit":
        return
    if _tut_walkthrough(_tutorial_state()) == "quit":
        return
    if _tut_screen("raise.title", "raise.body") == "quit":
        return
    if _tut_task_restore(_tutorial_state()) == "quit":
        return
    if _tut_screen("lose.title", "lose.body") == "quit":
        return
    if _tut_task_watch(_tutorial_state()) == "quit":
        return
    _tut_screen("end.title", "end.body")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--no-color", action="store_true")
    ap.add_argument("--level", type=int, default=None,
                    help="jump straight into a level: 1 satellite · 2 +drone · 3 +translator · 4 +DSS · 5 hard · 0 sandbox")
    ap.add_argument("--learn", action="store_true", help="run the tutorial")
    ap.add_argument("--campaign", action="store_true",
                    help="play the full office->field story campaign (levels 1-5)")
    args = ap.parse_args()
    R.set_color(not (args.no_color or not sys.stdout.isatty()))
    try:
        if args.learn:
            run_tutorial()
        elif args.campaign:
            run_campaign(args.seed, args.demo)
        elif args.demo:
            run_interactive(args.seed, True, args.level or 0)
        elif args.level is not None:
            run_interactive(args.seed, False, args.level)
        elif not sys.stdin.isatty():
            run_interactive(args.seed, False, 0)   # piped/non-interactive: just run
        else:
            choice = start_menu()
            if choice == "learn":
                run_tutorial()
            elif choice == "play":
                run_story(args.seed)
    finally:
        print(R.RESET, end="")


if __name__ == "__main__":
    main()
