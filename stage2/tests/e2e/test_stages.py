"""Stage 1, the replay, and the SVG projector, end to end in a browser.

    python3 -m unittest stage2.tests.e2e.test_stages

Stage 1 is plain Mafia: no fire, no choice, and the map kept back until the game
master replays it at the end. These run against a second server so the main
journey tests can stay on the terminal board.
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
import time
import unittest
import urllib.error
import urllib.request

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PORT = int(os.environ.get("STAGE1_TEST_PORT", "8033"))
BASE = f"http://localhost:{PORT}"

_server = _pw = _browser = None


def api(path, body=None):
    if body is None:
        return json.loads(urllib.request.urlopen(BASE + path, timeout=10).read())
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=10).read())


def setUpModule():
    global _server, _pw, _browser
    env = dict(os.environ, STAGE2_FAST="1")
    _server = subprocess.Popen(
        [sys.executable, "-m", "stage2.server", "--stage", "1",
         "--style", "drawn", "--port", str(PORT), "--fast"],
        cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        try:
            api("/api/state")
            break
        except (urllib.error.URLError, ConnectionError, OSError):
            time.sleep(0.25)
    else:
        raise RuntimeError("stage 1 server did not come up")
    _pw = sync_playwright().start()
    _browser = _pw.chromium.launch()


def tearDownModule():
    if _browser:
        _browser.close()
    if _pw:
        _pw.stop()
    if _server:
        _server.terminate()
        _server.wait(timeout=10)


def page(w=1280, h=820):
    return _browser.new_context(viewport={"width": w, "height": h}).new_page()


def drain(limit=40):
    for _ in range(limit):
        s = api("/api/state")
        if s["mode"] == "explain":
            api("/api/gm/advance", {})
        elif s["mode"] == "playing":
            time.sleep(0.05)
        else:
            return
    raise AssertionError("the projector never went idle")


def fresh(seed=5, players=12):
    api("/api/gm/reset", {"seed": seed})
    api("/api/gm/seed", {"n": players})
    api("/api/gm/start", {})
    return api("/api/state")


def play_round(kill_role=None):
    st = api("/api/state")
    if kill_role:
        who = next((p["id"] for p in st["players"]
                    if p["alive"] and p["role"] == kill_role), None)
        if who:
            api("/api/gm/eliminate", {"id": who})
    api("/api/gm/night", {})
    out = api("/api/steps")["steps"]
    drain()
    if api("/api/state")["phase"] != "playing":
        return out
    api("/api/gm/vote", {})
    out += api("/api/steps")["steps"]
    drain()
    return out


class StageOne(unittest.TestCase):
    def test_no_fire_and_no_choice(self):
        fresh()
        self.assertEqual(api("/api/state")["stage"], 1)
        for _ in range(3):
            if api("/api/state")["phase"] != "playing":
                break
            keys = [s["key"] for s in play_round("native")]
            self.assertNotIn("fire", keys, "stage 1 must not run a fire")
            self.assertNotIn("line", keys)
            self.assertNotIn("water", keys)
            self.assertNotIn("ews", keys)
        for rec in api("/api/state")["history"]:
            self.assertIsNone(rec.get("fire") or None,
                              "no fire should be recorded in stage 1")

    def test_the_vote_needs_no_choice(self):
        """In stage 1 there is nothing to shelter from, so Finish vote must work
        without the game master picking anything."""
        fresh(seed=9)
        api("/api/gm/night", {})
        drain()
        api("/api/gm/vote", {})      # deliberately no /api/gm/choice first
        drain()
        self.assertEqual(api("/api/state")["round"], 2)

    def test_the_console_hides_the_choice(self):
        fresh(seed=11)
        gm = page(1100, 950)
        errors = []
        gm.on("pageerror", lambda e: errors.append(str(e)))
        gm.goto(BASE + "/gm")
        gm.wait_for_selector("#night:not([hidden])", timeout=8000)
        gm.click("#finishnight")
        gm.wait_for_selector("#advance:not([hidden])", timeout=8000)
        gm.click("#advance")
        gm.wait_for_selector("#day:not([hidden])", timeout=15000)
        self.assertTrue(gm.locator("#choicebox").is_hidden(),
                        "stage 1 has no hunt-or-shelter choice")
        self.assertFalse(gm.locator("#finishvote").is_disabled(),
                         "Finish vote must be live without a choice")
        self.assertEqual(errors, [])


class Replay(unittest.TestCase):
    def test_it_walks_the_map_one_night_at_a_time(self):
        fresh(seed=5)
        for _ in range(3):
            if api("/api/state")["phase"] != "playing":
                break
            play_round("native")
        st = api("/api/state")
        self.assertTrue(st["can_replay"])
        rounds = st["round"]

        api("/api/gm/replay", {})
        s = api("/api/state")
        self.assertEqual(s["mode"], "replay")
        self.assertEqual(s["replay_at"], 0)
        total = s["replay_total"]
        self.assertGreaterEqual(total, rounds, "one frame per night, plus the start")

        seen = [s["replay_at"]]
        for _ in range(total + 2):
            if api("/api/state")["mode"] != "replay":
                break
            api("/api/gm/replay", {})
            s = api("/api/state")
            if s["mode"] == "replay":
                seen.append(s["replay_at"])
        self.assertEqual(seen, list(range(total)), "every night, in order, once")
        self.assertEqual(api("/api/state")["mode"], "idle", "it hands the game back")

    def test_the_forest_visibly_declines_across_the_replay(self):
        """The whole point of the replay is the room seeing what their voting
        cost. If the health never moves there is nothing to show them."""
        fresh(seed=5)
        for _ in range(4):
            if api("/api/state")["phase"] != "playing":
                break
            play_round("native")
        api("/api/gm/replay", {})
        healths = []
        while api("/api/state")["mode"] == "replay":
            frame = api("/api/frame")["frame"]
            healths.append(frame)
            api("/api/gm/replay", {})
        self.assertGreater(len(healths), 2)
        self.assertNotEqual(healths[0], healths[-1], "the map never changed")

    def test_stop_hands_the_game_back(self):
        fresh(seed=7)
        play_round("native")
        api("/api/gm/replay", {})
        self.assertEqual(api("/api/state")["mode"], "replay")
        api("/api/gm/replay_stop", {})
        self.assertEqual(api("/api/state")["mode"], "idle")


class SvgProjector(unittest.TestCase):
    def test_the_projector_draws_the_map_style(self):
        fresh(seed=5)
        self.assertEqual(api("/api/state")["style"], "drawn")
        self.assertTrue(api("/api/frame")["frame"].startswith("<svg"))

        pg = page()
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(BASE + "/projector")
        pg.wait_for_function("window.__beat !== null", timeout=10000)
        pg.wait_for_selector("#svg svg", timeout=8000)
        self.assertTrue(pg.locator("#svg").is_visible(), "the SVG map should be showing")
        self.assertTrue(pg.locator(".screen").is_hidden(), "the terminal should be put away")
        self.assertEqual(errors, [])

    def test_cards_draw_in_the_same_hand(self):
        fresh(seed=5)
        api("/api/gm/night", {})
        card = api("/api/frame")["frame"]
        self.assertTrue(card.startswith("<svg"))
        self.assertIn("THE NIGHT", card)
        drain()


if __name__ == "__main__":
    unittest.main(verbosity=2)
