"""Headless engine harness. No UI, proves the core stands alone.

    python3 -m engine.cli --demo            # auto-play a scripted game, print events
    python3 -m engine.cli --json --seed 7   # dump a fresh game state as JSON
    python3 -m engine.cli --auto --turns 12 # greedy auto-player, print final result
"""
from __future__ import annotations
import argparse
import json

from . import new_game, apply, observable, to_dict
from .engine import area
from .model import INVASIVE, BARE
from .rules import health_pct, count_cover


def _find_invasive_topleft(state):
    """Greedy helper: a cell whose work-block contains the most invasive cells."""
    best, best_n = None, 0
    for c in state.cells:
        n = sum(1 for i in area(state, c.index, state.config["work_size"])
                if state.cells[i].cover == INVASIVE)
        if n > best_n:
            best, best_n = c.index, n
    return best


def _find_bare_topleft(state):
    for c in state.cells:
        if c.cover == BARE:
            return c.index
    return None


def auto_policy(state):
    """A simple 'look then act' policy used to sanity-check the dynamics."""
    if state.turn % 3 == 1:
        # look: drone the densest-looking quadrant (cheat via truth for the harness)
        tgt = _find_invasive_topleft(state) or 0
        return {"type": "drone", "target": tgt}
    inv = _find_invasive_topleft(state)
    if inv is not None:
        return {"type": "remove", "target": inv}
    bare = _find_bare_topleft(state)
    if bare is not None:
        return {"type": "restore", "target": bare}
    return {"type": "pass"}


def run_demo(seed):
    state = new_game(seed=seed)
    print(f"seed={state.seed} board={state.cols}x{state.rows} wind={state.wind}")
    while state.status == "playing":
        action = auto_policy(state)
        state, events = apply(state, action)
        tags = [e["type"] for e in events]
        cc = count_cover(state)
        print(f"T{state.turn:>2} act={action['type']:<9} "
              f"health={health_pct(state):>3} wild={round(state.wildlife):>3} "
              f"nat={cc['native']:>3} inv={cc['invasive']:>3} bare={cc['bare']:>3} "
              f"events={sorted(set(tags))}")
    print(f"RESULT: {state.status.upper()}  {state.lose_reason}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--auto", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--turns", type=int, default=None)
    args = ap.parse_args()

    if args.json:
        state = new_game(seed=args.seed)
        if args.turns:
            state.max_turns = args.turns
        print(json.dumps({"state": to_dict(state), "view": observable(state)}, indent=2))
        return
    run_demo(args.seed)


if __name__ == "__main__":
    main()
