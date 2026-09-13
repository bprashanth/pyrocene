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


class Connectivity(unittest.TestCase):
    """The lesson stage 2 exists to deliver: scattered patches are a nuisance,
    one joined-up band is a different problem."""

    def test_severity_follows_the_band_not_the_thickest_patch(self):
        g = play(4, rounds=3)
        bands = g.bands()
        self.assertTrue(bands)
        sev, cluster = g.severity()
        self.assertEqual(sorted(cluster), sorted(bands[0]),
                         "severity must be read off the biggest connected band")
        load = g.band_load(bands[0])
        want = 1 if load < g.cfg["sev_t1"] else 2 if load < g.cfg["sev_t2"] else 3
        self.assertEqual(sev, want)

    def test_a_band_never_spans_open_water(self):
        for seed in (2, 6, 10, 14):
            g = play(seed)
            s = g.state
            for band in g.bands():
                inside = set(band)
                for i in band:
                    joins = [j for j, _ in neighbors8(s, i)
                             if j in inside and not across_water(s, i, j)]
                    if not joins and len(band) > 1:
                        self.fail(f"seed {seed}: a band held together only across water")

    def test_the_evening_builds(self):
        """Small scattered fires first, one big connected run later. If this
        inverts, the game teaches that early action does not matter."""
        early, late = [], []
        for seed in range(1, 31):
            g = play(seed)
            for k, h in enumerate(g.history, start=1):
                f = h.get("fire") or {}
                n = len(f.get("burned_cells") or [])
                (early if k <= 2 else late).append(n)
        self.assertGreater(len(early), 40)
        self.assertGreater(len(late), 30)
        mean_early = sum(early) / len(early)
        mean_late = sum(late) / len(late)
        self.assertLess(mean_early, 10, f"early fires should be small, got {mean_early:.1f}")
        self.assertGreater(mean_late, 2.5 * mean_early,
                           f"late fires should dwarf early ones: {mean_early:.1f} then {mean_late:.1f}")

    def test_the_room_is_told_once_when_it_joins_up(self):
        seen = 0
        for seed in range(1, 21):
            rng = random.Random(seed * 7919)
            g = Game(seed=seed)
            for i in range(12):
                g.add_player(f"P{i + 1}")
            g.start()
            calls = 0
            while g.phase == "playing":
                prey = [p for p in g.players.values()
                        if p.alive and p.role in (NATIVE_P, ECOLOGIST, RANGER)]
                if prey and rng.random() > 0.25:
                    g.eliminate(rng.choice(prey).id)
                g.resolve_night()
                if g.phase != "playing":
                    break
                pool = [p for p in g.players.values() if p.alive]
                g.eliminate(rng.choice(pool).id)
                g.choose("hunt", None)
                calls += sum(1 for st in g.resolve_vote() if st["key"] == "network")
            self.assertLessEqual(calls, 1, f"seed {seed}: said it more than once")
            seen += calls
        self.assertGreaterEqual(seen, 15, "most games should reach the turn")

    def test_stage_one_never_says_it(self):
        g = Game(seed=3, config={"stage": 1})
        for i in range(12):
            g.add_player(f"P{i + 1}")
        g.start()
        rng = random.Random(3)
        while g.phase == "playing":
            pool = [p for p in g.players.values() if p.alive]
            g.eliminate(rng.choice(pool).id)
            g.resolve_night()
            if g.phase != "playing":
                break
            pool = [p for p in g.players.values() if p.alive]
            g.eliminate(rng.choice(pool).id)
            g.choose("hunt", None)
            for st in g.resolve_vote():
                self.assertNotEqual(st["key"], "network",
                                    "stage 1 has no fire, so the band means nothing there")

    def test_the_automatic_choice_does_not_hide_the_big_fire(self):
        """Water holds a fire to a few squares. Picking it the moment a band has
        formed is exactly when it must not be picked, or the room never sees the
        run they have been building towards all evening."""
        picks = []
        for seed in range(1, 26):
            g = play(seed, rounds=4)
            if g.phase != "playing":
                continue
            if g.bands() and g.connected():
                g.locked_sev, g.locked_cluster = g.severity()
                picks.append(g._auto_action()[0])
        self.assertGreater(len(picks), 8, "need a real sample")
        self.assertNotIn("water", picks)


class ReplayNames(unittest.TestCase):
    """The replay names whoever went out, because that is what lets a room put a
    night in the game against a change on the ground. Nothing else may."""

    def test_only_people_who_went_out_and_owned_ground(self):
        g = play(5, stage=1)
        beats = g.replay_beats()
        self.assertGreaterEqual(len(beats), 1)
        for k, beat in enumerate(beats, start=1):
            for b in beat["badges"]:
                p = next(x for x in g.players.values() if x.name == b["name"])
                self.assertFalse(p.alive)
                self.assertEqual(p.out_round, k)
                self.assertIn(p.role, (LANTANA, NATIVE_P),
                              "the specialists own no ground, so they get no badge")
                self.assertTrue(b["cells"])
                self.assertIn(b["by"], ("night", "vote"))

    def test_every_landowner_who_went_out_is_named_once(self):
        g = play(8, stage=1)
        named = [b["name"] for beat in g.replay_beats() for b in beat["badges"]]
        expected = [p.name for p in g.players.values()
                    if not p.alive and p.role in (LANTANA, NATIVE_P) and p.patch]
        self.assertEqual(sorted(named), sorted(expected))
        self.assertEqual(len(named), len(set(named)), "nobody is named twice")

    def test_the_two_kinds_of_removal_are_told_apart(self):
        """Most nights two people go out, one taken by lantana and one voted out
        by the room. The replay has to say which is which or it is only telling
        the room that two people are gone."""
        g = play(6, stage=1)
        kinds = {b["by"] for beat in g.replay_beats() for b in beat["badges"]}
        self.assertTrue(kinds, "somebody must have gone out")
        for p in g.players.values():
            if not p.alive:
                self.assertIn(p.out_by, ("night", "vote"))

    def test_play_frames_carry_no_names(self):
        g = play(11, stage=1, rounds=3)
        for step in g.last_steps or []:
            for f in step.get("beats", []):
                self.assertFalse(f.get("badges"),
                                 "a frame shown during play must not name anyone")


if __name__ == "__main__":
    unittest.main()
