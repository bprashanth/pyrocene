"""Balance runs. Plays whole games in memory, no server, no browser.

    python3 -m stage2.sim              # the three room policies, 200 games each
    python3 -m stage2.sim --games 500
    python3 -m stage2.sim --trace 7    # one game, round by round

Tune against this, never by playing 20-minute games.
"""
from __future__ import annotations
import argparse
import random
import statistics as st
from collections import Counter

from .game import Game, LANTANA, NATIVE_P, ECOLOGIST, RANGER


def play(seed: int, policy: str, n_players: int = 12, skill: float = 0.35) -> dict:
    """One whole game. `policy` is how the room behaves:
       balanced  hunts, and shelters about a third of the time
       hunter    always hunts, never shelters
       turtle    always shelters, never hunts
    A hunt finds a lantana with probability `skill`; otherwise the room votes out
    a native, which is what a real room does when it guesses wrong.
    """
    rng = random.Random(seed * 7919)
    g = Game(seed=seed)
    for i in range(n_players):
        g.add_player(f"P{i + 1}")
    g.start()
    while g.phase == "playing":
        r = g.round
        if policy == "warden":
            # Hunt, unless the fire is close enough to the homes to take them.
            # Losing the village ends the game outright, so this is the one
            # threat worth spending a night on.
            near = g.village_at_risk()
            shelter = near
        elif policy == "triage":
            # Hunt relentlessly, but when the next fire would take the forest
            # below the line, spend the night saving it instead. This is the
            # call the stage is actually teaching.
            sev, _ = g.severity()
            land = sum(1 for c in g.state.cells if c.cover != "water")
            ramp = 1 + g.cfg["fire_round_ramp"] * (r - 1)
            cost = 100 * g.cfg["fire_cells"].get(sev, 0) * ramp / max(land, 1)
            shelter = sev >= 2 and (g.view()["health"] - cost) <= g.cfg["loss_health"] + 4
        elif policy == "guard":
            # Hunt almost always, but drop everything when the fuel is about to
            # carry a catastrophic fire. This is the habit the stage is teaching.
            sev, _ = g.severity()
            shelter = sev >= 3
        elif policy == "reader":
            # What the room is meant to learn: spend the turn on whichever threat
            # is bigger tonight. Shelter when the fuel has built up enough to
            # carry a real fire, hunt the rest of the time.
            sev, _ = g.severity()
            shelter = sev >= 2
        else:
            shelter = {"balanced": r % 3 == 0, "hunter": False, "turtle": True}[policy]
        # every night lantana takes someone, unless the ranger guesses right
        alive = [p for p in g.players.values() if p.alive]
        prey = [p for p in alive if p.role in (NATIVE_P, ECOLOGIST, RANGER)]
        if prey and rng.random() > 0.25:
            g.eliminate(rng.choice(prey).id)
        if shelter:
            g.choose("resilience", None)
        else:
            pool = [p for p in g.players.values() if p.alive]
            lant = [p for p in pool if p.role == LANTANA]
            if lant and rng.random() < skill:
                g.eliminate(rng.choice(lant).id)
            elif pool:
                g.eliminate(rng.choice(pool).id)
            g.choose("hunt", None)
        g.resolve()
    e = g.ending or {}
    return {"rounds": len(g.history), "result": e.get("result"), "reason": e.get("reason"),
            "health": e.get("health"), "lows": min(h["health"] for h in g.history),
            "burned": sum(len(h["fire"]["cells"]) for h in g.history),
            "sev": [h["fire"]["severity"] for h in g.history]}


def report(policy: str, games: int, players: int, skill: float):
    runs = [play(s, policy, players, skill) for s in range(games)]
    wins = sum(r["result"] == "win" for r in runs)
    reasons = Counter(r["reason"] for r in runs)
    rounds = [r["rounds"] for r in runs]
    health = [r["health"] for r in runs if r["health"] is not None]
    sev1 = st.mean([r["sev"][0] for r in runs if r["sev"]])
    sevlate = st.mean([max(r["sev"][3:]) for r in runs if len(r["sev"]) > 3] or [0])
    print(f"{policy:9s} win {100*wins/games:5.1f}%  rounds {st.mean(rounds):4.1f} "
          f"(min {min(rounds)} max {max(rounds)})  end health {st.mean(health):4.1f}  "
          f"sev r1 {sev1:.1f} late {sevlate:.1f}  " + " ".join(f"{k}:{v}" for k, v in reasons.most_common()))
    return runs


def trace(seed: int, policy: str, players: int):
    g = Game(seed=seed)
    for i in range(players):
        g.add_player(f"P{i + 1}")
    g.start()
    print(f"seed {seed}  players {players}  lantana {g.lantana_count()}")
    r = play(seed, policy, players)
    print(r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=200)
    ap.add_argument("--players", type=int, default=12)
    ap.add_argument("--trace", type=int)
    ap.add_argument("--skill", type=float, default=0.35,
                    help="chance a hunt round finds a real lantana")
    args = ap.parse_args()
    if args.trace is not None:
        return trace(args.trace, "balanced", args.players)
    print(f"{args.games} games, {args.players} players, room skill {args.skill}")
    for pol in ("warden", "triage", "hunter", "turtle"):
        report(pol, args.games, args.players, args.skill)


if __name__ == "__main__":
    main()
