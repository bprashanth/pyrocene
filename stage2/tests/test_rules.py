"""Rules that hold no matter who is playing. Pure logic, no server, no browser.

    python3 -m unittest stage2.tests.test_rules
"""
from __future__ import annotations
import random
import unittest

from stage2.game import (Game, across_water, LANTANA, NATIVE_P, ECOLOGIST,
                         RANGER, WATER, INVASIVE)
from stage2.engine.rules import neighbors8


def play(seed: int, rounds: int = 99, stage: int = 2, hook=None):
    """One scripted game. `hook` runs after each growth step with the game."""
    rng = random.Random(seed * 7919)
    g = Game(seed=seed, config={"stage": stage})
    for i in range(12):
        g.add_player(f"P{i + 1}")
    g.start()
    n = 0
    while g.phase == "playing" and n < rounds:
        n += 1
        prey = [p for p in g.players.values()
                if p.alive and p.role in (NATIVE_P, ECOLOGIST, RANGER)]
        if prey and rng.random() > 0.25:
            g.eliminate(rng.choice(prey).id)
        g.resolve_night()
        if hook:
            hook(g)
        if g.phase != "playing":
            break
        pool = [p for p in g.players.values() if p.alive]
        g.eliminate(rng.choice(pool).id)
        g.choose("hunt", None)
        g.resolve_vote()
        if hook:
            hook(g)
    return g


class Water(unittest.TestCase):
    """A river is a break for fire and for a trench, so it has to be a break for
    lantana too. Diagonal neighbours let a stand step around the corner of a
    one-cell channel and appear on the far bank with nothing joining it."""

    def test_the_corner_case_is_recognised(self):
        g = Game(seed=3)
        for i in range(12):
            g.add_player(f"P{i + 1}")
        g.start()
        s = g.state
        # Build a corner of water by hand and check both diagonals of it.
        r, c = 4, 6
        a = r * s.cols + c
        b = (r + 1) * s.cols + (c + 1)
        s.cells[(r + 1) * s.cols + c].cover = WATER
        s.cells[r * s.cols + (c + 1)].cover = WATER
        self.assertTrue(across_water(s, a, b))
        s.cells[r * s.cols + (c + 1)].cover = "native"
        self.assertFalse(across_water(s, a, b),
                         "one dry side is enough to walk around")

    def test_spread_never_crosses_it(self):
        """Every square lantana takes must touch a square it already held, by a
        step that does not cut a water corner."""
        seen = {"grown": 0, "crossed": 0}
        original = Game._grow

        def watched(self, rng):
            s = self.state
            before = {c.index for c in s.cells if c.cover == INVASIVE}
            new, cand = original(self, rng)
            for i in new:
                seen["grown"] += 1
                if not any(j in before and not across_water(s, j, i)
                           for j, _ in neighbors8(s, i)):
                    seen["crossed"] += 1
            return new, cand

        Game._grow = watched
        try:
            for seed in range(1, 13):
                play(seed)
        finally:
            Game._grow = original
        self.assertGreater(seen["grown"], 400, "the sample has to be worth something")
        self.assertEqual(seen["crossed"], 0)

    def test_bare_ground_is_not_taken_across_it(self):
        seen = {"taken": 0, "crossed": 0}
        original = Game._leak

        def watched(self, rng):
            s = self.state
            before = {c.index for c in s.cells if c.cover == INVASIVE}
            touched = original(self, rng)
            for i in touched:
                if s.cells[i].cover != INVASIVE:
                    continue
                seen["taken"] += 1
                if not any(j in before and not across_water(s, j, i)
                           for j, _ in neighbors8(s, i)):
                    seen["crossed"] += 1
            return touched

        Game._leak = watched
        try:
            for seed in range(1, 13):
                play(seed)
        finally:
            Game._leak = original
        self.assertGreater(seen["taken"], 40)
        self.assertEqual(seen["crossed"], 0)

    def test_one_stand_does_not_span_a_channel(self):
        """Fire severity comes from the biggest connected stand of thick lantana.
        If that count reaches over water, a fire is rated for fuel it can never
        actually run through."""
        for seed in range(1, 13):
            g = play(seed)
            s = g.state
            for comp in g.dense_clusters():
                inside = set(comp)
                for i in comp:
                    for j, _ in neighbors8(s, i):
                        if j in inside:
                            self.assertFalse(
                                across_water(s, i, j) and not any(
                                    k in inside and not across_water(s, i, k)
                                    for k, _ in neighbors8(s, i)),
                                f"seed {seed}: a stand joined across water")


class ReplayNames(unittest.TestCase):
    """The replay names whoever went out, because that is what lets a room put a
    night in the game against a change on the ground. Nothing else may."""

    def test_only_people_who_went_out_and_owned_ground(self):
        g = play(5, stage=1)
        beats = g.replay_beats()
        self.assertGreater(len(beats), 1)
        self.assertEqual(beats[0]["badges"], [], "the opening board names nobody")
        for k, beat in enumerate(beats):
            for b in beat["badges"]:
                p = next(x for x in g.players.values() if x.name == b["name"])
                self.assertFalse(p.alive)
                self.assertEqual(p.out_round, k)
                self.assertIn(p.role, (LANTANA, NATIVE_P),
                              "the specialists own no ground, so they get no badge")
                self.assertTrue(b["cells"])

    def test_every_landowner_who_went_out_is_named_once(self):
        g = play(8, stage=1)
        named = [b["name"] for beat in g.replay_beats() for b in beat["badges"]]
        expected = [p.name for p in g.players.values()
                    if not p.alive and p.role in (LANTANA, NATIVE_P) and p.patch]
        self.assertEqual(sorted(named), sorted(expected))
        self.assertEqual(len(named), len(set(named)), "nobody is named twice")

    def test_play_frames_carry_no_names(self):
        g = play(11, stage=1, rounds=3)
        for step in g.last_steps or []:
            for f in step.get("beats", []):
                self.assertFalse(f.get("badges"),
                                 "a frame shown during play must not name anyone")


if __name__ == "__main__":
    unittest.main()
