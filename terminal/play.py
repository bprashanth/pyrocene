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
import sys
import time

from engine import new_game, apply, observable
from engine.engine import area
from engine.model import INVASIVE, BARE
from . import render as R

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
        f"{FG(255)}COMMANDS{R.RESET} {FG(245)}(one per night){R.RESET}",
        line(IVY, u.get("satellite", True), "sat", "scan the whole map, rough"),
        line(IVY, u.get("drone", True), "drone D4", "reveal a 4x4 cluster in detail"),
        line(IVY, u.get("survey", True), "survey D4", "one cell, full truth"),
        line(IVY, u.get("dss", True), "dss", "(auto) advises you each night"),
        line(ELDER, u.get("translator", True), "ask D4", "elders advise on a patch"),
        line(ROCKY, True, "remove D4", "clear invasive, pull saplings early!"),
        line(ROCKY, True, "restore D4", "replant natives on bare ground"),
        line(ELDER, True, "burn D4", "controlled burn of a big stand, multi-night"),
        line(ELDER, True, "crew D4", "clear a big stand by hand, multi-night"),
        line(ROCKY, True, "pass", "do nothing; nature still moves"),
        f"  {FG(245)}commands take a cell, e.g. drone D4 · help · quit{R.RESET}",
    ]
    return "\n".join(rows)


def initial_chars() -> dict:
    return {
        "ivy":   {"text": "Goal: get native forest back above the line and hold it. Scan to find the weeds.", "fresh": True},
        "rocky": {"text": "Point me at a problem and I'll deal with it.", "fresh": False},
        "elder": {"text": "Ask me about a patch: 'ask D4'.", "fresh": False},
        "ember": {"text": "Every night, I spread. Hehe.", "fresh": False},
    }


def update_chars(chars: dict, events: list, view: dict):
    """Route this night's events to the four character channels. Each channel
    keeps its last line (dimmed) until that character has something new to say."""
    for c in chars.values():
        c["fresh"] = False
    ev = {e["type"]: e for e in events}

    def say(who, text):
        chars[who] = {"text": text, "fresh": True}

    # EMBER — nature and threats
    if "burn_escape" in ev:
        say("ember", f"Your fire jumped the lines! An inferno now, {len(ev['burn_escape']['cells'])} cells gone.")
    elif "village_fire" in ev:
        say("ember", "The fire reached the homes. The worst has happened.")
    elif "fire" in ev:
        say("ember", f"WHOOSH! A dense stand caught, {len(ev['fire']['cells'])} cells lost.")
    else:
        spread = sum(1 for e in events if e["type"] in ("spread", "regrow"))
        if spread:
            say("ember", f"{spread} new outbreak(s) tonight. Hehe.")

    # IVY — data and detection
    if "scan" in ev:
        sc = ev["scan"]
        det = sc.get("detected")
        if det:
            say("ivy", f"Drone: {len(det)} invasive cell(s) in that cluster.")
        elif sc.get("source") == "drone":
            say("ivy", "That cluster's clean, confirmed. Solid green now.")
        elif sc.get("source") == "survey":
            say("ivy", "Surveyed that cell. Full picture now.")
        elif sc.get("source") == "satellite":
            if view.get("unlocks", {}).get("drone", True):
                say("ivy", "Satellite's rough. Drone the haze to be sure.")
            else:
                say("ivy", "Satellite's all I've got, and it's rough. It misses the young growth.")

    # ROCKY — action and the job chain
    if "controlled_burn" in ev:
        say("rocky", "Clean burn! Bare ground now. Restore it next turn.")
    elif "crew_done" in ev:
        say("rocky", "Crew's finished, stand cleared. Replant the bare ground.")
    elif "lines_ready" in ev:
        say("rocky", "Lines are dug. Light it on a calm night: press Enter.")
    elif "lining" in ev:
        say("rocky", f"Laying fire line. {ev['lining']['left']} night(s) left. Press Enter.")
    elif "waiting_wind" in ev:
        say("rocky", "Lines holding. Waiting for the wind to drop."
            if view["wind_str"] > 1 else "Wind's calm now. Press Enter to light.")
    elif "job_start" in ev:
        say("rocky", "Starting the burn. Digging lines, can't do anything else."
            if ev["job_start"]["job"] == "burn" else
            "Crew's in. We're clearing by hand for a few nights.")
    elif "job_abort" in ev:
        say("rocky", "Called it off. That effort's lost.")
    elif "crew_work" in ev:
        say("rocky", f"Crew cleared {ev['crew_work']['cleared']}; {ev['crew_work']['remaining']} left.")
    elif ev.get("remove", {}).get("removed"):
        rm = ev["remove"]
        if rm["reinvaded"] and not rm["reclaimed"]:
            say("rocky", "Pulled them, but the weeds swept right back. Clear the source first!")
        elif rm["reinvaded"]:
            say("rocky", f"Some held, but {len(rm['reinvaded'])} got reinvaded. Source's still near.")
        elif rm["reclaimed"] and not rm["bared"]:
            say("rocky", "Pulled the young growth. Natives filled in clean.")
        else:
            say("rocky", "Cleared it. Bare ground now, restore it next.")
    elif ev.get("restore", {}).get("planted"):
        say("rocky", f"Planted {ev['restore']['planted']} patch(es). Ours again.")

    # disasters and boons
    if "event" in ev:
        et = ev["event"]
        if et == "work_party":
            say("elder", "A work party came through and uprooted a whole stand. Ours again.")
        elif et == "drought":
            say("ember", "Drought! The land dries and I grow bolder. Hehe.")
        elif et == "monsoon":
            say("ember", "Monsoon! My seeds ride the water down to the banks.")
        elif et == "grazing":
            say("ember", "Cattle churned fresh soil, a brand-new hotspot for me!")

    # ELDER — community advice
    if "clue" in ev:
        say("elder", ev["clue"]["text"])

    if "wasted" in ev and not any(k in ev for k in ("scan", "clue", "remove", "restore")):
        say("ivy", f"That did nothing: {ev['wasted']['reason']}.")


def draw(view: dict, chars: dict):
    clear()
    u = view.get("unlocks", {})
    if u.get("level", 0) == 0:
        tools = f"{FG(40)}all tools (sandbox){R.RESET}"
    else:
        names = [("satellite", "sat"), ("drone", "drone"), ("translator", "ask"), ("dss", "DSS")]
        have = [lbl for k, lbl in names if u.get(k)]
        tools = f"{FG(245)}game {u['level']}: {FG(255)}{' '.join(have)}{R.RESET}"
    print(f"{FG(208)}  P Y R O C E N E {R.RESET}{FG(245)} — Night {view['turn']}/{view['max_turns']} · {R.RESET}{tools}\n")
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
        print(f"{FG(col)}  {icon} {label} incoming ({cue}) {FG(255)}— {when}{R.RESET}")
    eff = view.get("effects") or {}
    if eff:
        tags = "  ".join(f"{FG(203)}{k.upper()}{R.RESET}" for k in eff)
        print(f"  {FG(245)}in effect:{R.RESET} {tags}")
    adv = view.get("dss_advice")
    if adv:
        import textwrap
        wrapped = textwrap.wrap(adv, 68)
        print(f"{FG(45)}  DSS ►{R.RESET} {FG(51)}{wrapped[0]}{R.RESET}")
        for w in wrapped[1:]:
            print(f"{FG(51)}       {w}{R.RESET}")
    print()
    board = R.render_board(view).split("\n")
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
    print(f"\n  {FG(45)}FIELD NOTE{R.RESET} {FG(245)}— real lantana ecology{R.RESET}")
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
            print(f"\n{FG(40)}Fire lines are ready and the wind is {wind} — safe to burn.{R.RESET}")
            print(f"{FG(245)}Light the fire?  {FG(40)}[Enter] = light{R.RESET}"
                  f"   {FG(245)}'w' = wait   'a' = abort{R.RESET}")
    elif job:
        print(f"\n{FG(245)}(the crew is committed — press Enter to keep working, or 'a' to abort){R.RESET}")
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
        print(f"{FG(214)}unknown command '{cmd}' — type help{R.RESET}")


def end_screen(view: dict, state, delay_ok: bool):
    st = view["status"]
    need = view.get("resilience", {}).get("need", 3)
    target = view["thresholds"]["win"]
    banners = {
        "gold": (46, "GOLD — THRIVING", "You restored the forest to full health and held it. A landscape that lasts."),
        "win": (40, "RESTORED — YOU WIN", f"You brought native forest back above {target}% and held it {need} nights running."),
        "lose": (196, "DEFEAT", view["lose_reason"] or "The forest never recovered."),
    }
    color, title, sub = banners[st]
    print(f"\n{FG(color)}  ══════ {title} ══════{R.RESET}")
    print(f"  {FG(250)}{sub}{R.RESET}")
    print(f"  {FG(250)}Final native forest {FG(255)}{view['health']}%{R.RESET}"
          f"  {FG(250)}wildlife {FG(255)}{view['wildlife']}%{R.RESET}"
          f"  {FG(250)}after {view['turn']} nights.{R.RESET}")
    lesson = ("You can't wipe lantana out — the seed banks always return. You win by keeping "
              "its strongholds cut back so the native forest recovers and holds. The DSS finds them.")
    print(f"\n  {FG(45)}LESSON:{R.RESET} {lesson}\n")


# harder tiers for "true fans" / real ecologists: the field notes stop being
# flavour and become the strategy (know the ecology, or the disasters bury you).
LEVEL_PRESETS = {
    # level 5 = level-4 game PLUS more variables: the telegraphed disasters
    # (grazing/drought/monsoon) and a richer, staler landscape. Harder, not brutal.
    5: {"obs_decay_turns": 2, "hill_blobs": 3, "roads": 2, "max_turns": 16,
        "events_on": True, "event_types": ["grazing", "drought", "monsoon"],
        "event_gap": (2, 3), "first_event_night": 4},
}


def run_interactive(seed, demo, level=0):
    if demo and seed is None:
        seed = 1  # a curated showcase: DSS-guided win by night 9
    config = {"unlock_level": level}
    config.update(LEVEL_PRESETS.get(level, {}))
    state = new_game(seed=seed, config=config)
    delay = 0.14
    if demo:
        def bot(s):
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

    chars = initial_chars()
    while state.status == "playing":
        view = observable(state)
        draw(view, chars)
        if demo:
            time.sleep(0.7)
            action = bot(state)
            print(f"\n{FG(208)}night {view['turn']} > {R.RESET}{action['type']}"
                  + (f" {cell_name(action['target'], view)}" if action.get("target") is not None else ""))
            time.sleep(0.4)
        else:
            action = turn_prompt(view)
            if action is None:
                print("left the field. the forest remembers.")
                return
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
        update_chars(chars, events, observable(state))

    draw(observable(state), chars)
    end_screen(observable(state), state, not demo)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--no-color", action="store_true")
    ap.add_argument("--level", type=int, default=0,
                    help="0 all (default) · 1 satellite · 2 +drone · 3 +translator · 4 +DSS · 5 hard mode")
    args = ap.parse_args()
    R.set_color(not (args.no_color or not sys.stdout.isatty()))
    try:
        run_interactive(args.seed, args.demo, args.level)
    finally:
        print(R.RESET, end="")


if __name__ == "__main__":
    main()
