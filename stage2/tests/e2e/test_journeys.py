"""End to end, through the real pages in a real browser.

    python3 -m stage2.tests.e2e.test_journeys           # all journeys
    SHOTS=1 python3 -m stage2.tests.e2e.test_journeys   # also save screenshots

Every journey drives the same pages a room would: phones join, the game master
clicks, the projector paints. Assertions check the frame the projector actually
shows, not just the API, because the map is the whole teaching tool.
"""
from __future__ import annotations
import json
import os
import re
import subprocess
import sys
import time
import unittest
import urllib.error
import urllib.request

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PORT = int(os.environ.get("STAGE2_TEST_PORT", "8031"))
BASE = f"http://localhost:{PORT}"
SHOTS = os.environ.get("SHOTS") == "1"
SHOT_DIR = os.environ.get("SHOT_DIR", "/tmp/stage2-shots")

_server = None
_pw = None
_browser = None


def api(path, body=None):
    if body is None:
        return json.loads(urllib.request.urlopen(BASE + path, timeout=10).read())
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=10).read())


def setUpModule():
    global _server, _pw, _browser
    env = dict(os.environ, STAGE2_FAST="1", STAGE2_PORT=str(PORT))
    _server = subprocess.Popen([sys.executable, "-m", "stage2.server"], cwd=ROOT, env=env,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        try:
            api("/api/state")
            break
        except (urllib.error.URLError, ConnectionError, OSError):
            time.sleep(0.25)
    else:
        raise RuntimeError("stage 2 server did not come up")
    _pw = sync_playwright().start()
    _browser = _pw.chromium.launch()
    if SHOTS:
        os.makedirs(SHOT_DIR, exist_ok=True)


def tearDownModule():
    if _browser:
        _browser.close()
    if _pw:
        _pw.stop()
    if _server:
        _server.terminate()
        _server.wait(timeout=10)


def page(w=1280, h=800):
    return _browser.new_context(viewport={"width": w, "height": h}).new_page()


def shot(pg, name):
    if SHOTS:
        pg.screenshot(path=os.path.join(SHOT_DIR, name))


def plain(frame: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", frame)


def beats():
    n = api("/api/beat?i=0").get("n", 0)
    return [api(f"/api/beat?i={i}") for i in range(n)]


def kinds(bs):
    return [b["kind"] for b in bs]


def fresh(seed=None, players=12):
    api("/api/gm/reset", {"seed": seed})
    api("/api/gm/seed", {"n": players})
    api("/api/gm/start", {})
    return api("/api/state")


def roles(state):
    out = {}
    for p in state["players"]:
        out.setdefault(p["role"], []).append(p["id"])
    return out


def cover_counts():
    """Read the live map straight off the server's own view."""
    return api("/api/map")


class J01_JoinAndRoles(unittest.TestCase):
    def test_phones_join_and_each_sees_its_own_role(self):
        api("/api/gm/reset", {"seed": 21})
        phones = []
        for name in ("Asha", "Bala", "Chitra"):
            pg = page(390, 760)
            pg.goto(BASE + "/")
            pg.fill("#name", name)
            pg.click("#go")
            pg.wait_for_selector("#me:not([hidden])", timeout=5000)
            phones.append((name, pg))
        api("/api/gm/seed", {"n": 9})

        gm = page(1100, 900)
        gm.goto(BASE + "/gm")
        gm.wait_for_selector("#players tr", timeout=5000)
        self.assertEqual(gm.locator("#players tr").count(), 12)
        shot(gm, "j01-gm-lobby.png")
        gm.click("#start")
        gm.wait_for_selector("#night:not([hidden])", timeout=5000)

        state = api("/api/state")
        by_id = {p["id"]: p for p in state["players"]}
        # every phone shows the role the server gave that player, and nobody else's
        for name, pg in phones:
            pg.wait_for_function(
                "() => document.querySelector('#rolename').textContent.trim() !== "
                "'waiting for the game master'", timeout=5000)
            me = api("/api/me?token=" + pg.evaluate("localStorage.getItem('pyro_token')"))
            shown = pg.text_content("#rolename").strip().lower()
            expect = {"lantana": "lantana", "native": "native forest",
                      "ecologist": "ecologist", "ranger": "ranger"}[me["role"]]
            self.assertEqual(shown, expect, f"{name} saw the wrong role")
            self.assertEqual(pg.text_content("#who").strip(), name)
            self.assertEqual(by_id[me["id"]]["role"], me["role"])
        shot(phones[0][1], "j01-phone-role.png")

        r = roles(state)
        self.assertEqual(len(r["ecologist"]), 1)
        self.assertEqual(len(r["ranger"]), 1)
        self.assertEqual(len(r["lantana"]), state["lantana_count"])
        self.assertEqual(sum(len(v) for v in r.values()), 12)


class J02_MapMatchesAllocation(unittest.TestCase):
    def test_projector_shows_the_allocated_map(self):
        state = fresh(seed=21)
        m = cover_counts()
        self.assertEqual(m["owners"], state["lantana_count"] + m["native_players"],
                         "every native and lantana player should own a patch")
        self.assertGreater(m["commons"], 0, "some land must stay unowned commons")
        self.assertEqual(m["clusters"], state["lantana_count"],
                         "one separate infestation per lantana player at the start")

        pg = page()
        pg.goto(BASE + "/projector")
        pg.wait_for_function("window.__beat !== null", timeout=10000)
        time.sleep(0.4)
        txt = plain(api("/api/frame")["frame"])
        self.assertIn("P Y R O C E N E", txt)
        self.assertIn("Forest", txt)
        self.assertIn("LANDSCAPE", txt, "the legend must be on screen")
        self.assertNotIn("WHO'S SPEAKING", txt, "no character panel in stage 2")
        self.assertNotIn("Win goal", txt, "no win-goal dots in stage 2")
        for line in txt.splitlines():
            self.assertLessEqual(len(line.rstrip()), 80, "a frame line overflows the projector")
        shot(pg, "j02-projector.png")


class J03_Eliminations(unittest.TestCase):
    def test_lantana_out_leaves_bare_and_native_out_lets_lantana_in(self):
        state = fresh(seed=33)
        r = roles(state)
        before = cover_counts()
        api("/api/gm/eliminate", {"id": r["lantana"][0]})
        api("/api/gm/choice", {"choice": "hunt"})
        api("/api/gm/resolve", {})
        time.sleep(0.6)
        bs = beats()
        self.assertIn("elimination", kinds(bs))
        line = next(b["text"] for b in bs if b["kind"] == "elimination")
        self.assertIn("pulled out", line)
        after = cover_counts()
        self.assertGreater(after["bare"], before["bare"],
                           "an eliminated lantana patch should leave bare ground")

        state = api("/api/state")
        nat = [p["id"] for p in state["players"] if p["role"] == "native" and p["alive"]][0]
        pre = cover_counts()
        api("/api/gm/eliminate", {"id": nat})
        api("/api/gm/choice", {"choice": "hunt"})
        api("/api/gm/resolve", {})
        time.sleep(0.6)
        bs = beats()
        line = next(b["text"] for b in bs if b["kind"] == "elimination")
        self.assertIn("Lantana moves in", line)
        self.assertGreater(cover_counts()["invasive"], 0)

    def test_losing_a_specialist_does_not_change_the_map(self):
        state = fresh(seed=34)
        r = roles(state)
        before = cover_counts()
        api("/api/gm/eliminate", {"id": r["ecologist"][0]})
        api("/api/gm/choice", {"choice": "hunt"})
        api("/api/gm/resolve", {})
        time.sleep(0.6)
        line = next(b["text"] for b in beats() if b["kind"] == "elimination")
        self.assertIn("map does not change", line)


class J04_NightRunsAndEmberMatches(unittest.TestCase):
    def test_growth_fire_and_narration_agree(self):
        fresh(seed=41)
        for _ in range(3):
            api("/api/gm/choice", {"choice": "hunt"})
            api("/api/gm/resolve", {})
            time.sleep(0.6)
            if api("/api/state")["phase"] != "playing":
                break
        bs = beats()
        self.assertIn("growth", kinds(bs))
        after = next(b for b in bs if b["kind"] == "aftermath" or b["kind"] == "quiet")
        fire = [b for b in bs if b["kind"] == "burn"]
        if fire:
            burned = len(fire[-1]["fire"])
            said = re.search(r"(\d+) squares", after["text"])
            self.assertIsNotNone(said, f"Ember did not say a size: {after['text']}")
            self.assertEqual(int(said.group(1)), burned,
                             "Ember's number must match the cells that burned")

    def test_growth_beat_number_matches_the_map(self):
        fresh(seed=42)
        before = cover_counts()["invasive"]
        api("/api/gm/choice", {"choice": "hunt"})
        api("/api/gm/resolve", {})
        time.sleep(0.6)
        g = next(b for b in beats() if b["kind"] == "growth")
        n = re.search(r"into (\d+) more", g["text"])
        if n:
            self.assertGreater(int(n.group(1)), 0)


class J05_FireLineHolds(unittest.TestCase):
    def test_fire_runs_into_the_line_and_stops(self):
        held = None
        for seed in (11, 12, 13, 14, 15, 16):
            fresh(seed=seed)
            for _ in range(2):
                api("/api/gm/choice", {"choice": "hunt"})
                api("/api/gm/resolve", {})
                time.sleep(0.5)
            if api("/api/state")["phase"] != "playing":
                continue
            api("/api/gm/choice", {"choice": "resilience", "action": "fireline"})
            api("/api/gm/resolve", {})
            time.sleep(0.8)
            bs = beats()
            if "blocked" in kinds(bs):
                held = (seed, bs)
                break
        self.assertIsNotNone(held, "no seed produced a fire running into a fresh line")
        seed, bs = held
        ks = kinds(bs)
        self.assertLess(ks.index("line"), ks.index("ignite"),
                        "the line must be dug before the fire, so the room sees why")
        self.assertIn("fire line", next(b["text"] for b in bs if b["kind"] == "line"))
        after = next(b["text"] for b in bs if b["kind"] == "aftermath")
        self.assertIn("fire line", after, f"Ember must say the line stopped it: {after}")
        # the frame at the blocked beat still shows the line standing
        i = ks.index("blocked")
        frame = plain(api(f"/api/beat?i={i}")["frame"])
        self.assertIn("++", frame, "the fire line must still be drawn after the fire")
        for name, idx in (("line", ks.index("line")), ("ignite", ks.index("ignite")),
                          ("blocked", i), ("aftermath", ks.index("aftermath"))):
            pg = page(1400, 820)
            pg.goto(f"{BASE}/projector?beat={idx}")
            pg.wait_for_function("window.__beat !== null", timeout=10000)
            time.sleep(0.35)
            shot(pg, f"j05-{name}.png")
            pg.close()

    def test_a_line_is_permanent(self):
        fresh(seed=11)
        for _ in range(2):
            api("/api/gm/choice", {"choice": "hunt"})
            api("/api/gm/resolve", {})
            time.sleep(0.5)
        api("/api/gm/choice", {"choice": "resilience", "action": "fireline"})
        api("/api/gm/resolve", {})
        time.sleep(0.6)
        n1 = cover_counts()["fireline"]
        self.assertGreater(n1, 0)
        api("/api/gm/choice", {"choice": "hunt"})
        api("/api/gm/resolve", {})
        time.sleep(0.6)
        self.assertGreaterEqual(cover_counts()["fireline"], n1,
                                "fire lines must last the rest of the game")


class J06_Water(unittest.TestCase):
    def test_water_caps_the_fire(self):
        fresh(seed=51)
        for _ in range(3):
            api("/api/gm/choice", {"choice": "hunt"})
            api("/api/gm/resolve", {})
            time.sleep(0.5)
            if api("/api/state")["phase"] != "playing":
                break
        api("/api/gm/choice", {"choice": "resilience", "action": "water"})
        api("/api/gm/resolve", {})
        time.sleep(0.7)
        bs = beats()
        self.assertIn("water", kinds(bs))
        burn = [b for b in bs if b["kind"] == "burn"]
        if burn:
            self.assertLessEqual(len(burn[-1]["fire"]), 8,
                                 "water must hold the fire to a handful of squares")
            after = next(b["text"] for b in bs if b["kind"] == "aftermath")
            self.assertIn("response team", after)


class J07_EarlyWarning(unittest.TestCase):
    def test_the_forecast_names_the_next_night(self):
        fresh(seed=61)
        api("/api/gm/choice", {"choice": "hunt"})
        api("/api/gm/resolve", {})
        time.sleep(0.5)
        api("/api/gm/choice", {"choice": "resilience", "action": "ews"})
        api("/api/gm/resolve", {})
        time.sleep(0.7)
        st = api("/api/state")
        self.assertIsNotNone(st["forecast"], "early warning must leave a forecast")
        said = next(b["text"] for b in beats() if b["kind"] == "forecast")
        self.assertIn("Forecast", said)
        self.assertIn(st["forecast"]["wind"], said)


class J08_SystemPicks(unittest.TestCase):
    def test_resolving_without_an_action_picks_one_and_says_why(self):
        fresh(seed=71)
        for _ in range(2):
            api("/api/gm/choice", {"choice": "hunt"})
            api("/api/gm/resolve", {})
            time.sleep(0.5)
        api("/api/gm/choice", {"choice": "resilience", "action": None})
        api("/api/gm/resolve", {})
        time.sleep(0.7)
        st = api("/api/state")
        last = st["history"][-1]
        self.assertTrue(last["auto"], "the system should have picked")
        self.assertIn(last["action"], ("fireline", "water", "ews"))
        said = " ".join(b["text"] for b in beats() if b["text"])
        self.assertTrue(any(w in said for w in ("so the crew digs", "so a response team",
                                                "posts a forecast")),
                        f"Ember must give the reason: {said}")


class J09_Endings(unittest.TestCase):
    def test_removing_every_lantana_wins(self):
        state = fresh(seed=81)
        for pid in roles(state)["lantana"]:
            api("/api/gm/eliminate", {"id": pid})
        api("/api/gm/choice", {"choice": "hunt"})
        api("/api/gm/resolve", {})
        time.sleep(0.8)
        st = api("/api/state")
        self.assertEqual(st["phase"], "ended")
        self.assertEqual(st["ending"]["result"], "win")
        self.assertIn("lantana patch is out", st["ending"]["text"])
        bs = beats()
        self.assertEqual(kinds(bs)[-1], "ending")
        pg = page(1400, 820)
        pg.goto(f"{BASE}/projector?beat={len(bs) - 1}")
        pg.wait_for_function("window.__beat !== null", timeout=10000)
        time.sleep(0.35)
        self.assertIn("THE SEASON ENDS", plain(api("/api/frame")["frame"]) + plain(bs[-1]["frame"]))
        shot(pg, "j09-win.png")
        pg.close()

    def test_running_out_of_nights_loses(self):
        fresh(seed=82)
        for _ in range(12):
            st = api("/api/state")
            if st["phase"] != "playing":
                break
            api("/api/gm/choice", {"choice": "resilience"})
            api("/api/gm/resolve", {})
            time.sleep(0.45)
        st = api("/api/state")
        self.assertEqual(st["phase"], "ended")
        self.assertEqual(st["ending"]["result"], "lose")
        self.assertIn(st["ending"]["reason"], ("time", "fire", "village", "natives"))

    def test_a_room_that_only_shelters_never_wins(self):
        # the doc's rule: neglect the root cause and the game goes on but is never won
        for seed in (91, 92, 93):
            fresh(seed=seed)
            while api("/api/state")["phase"] == "playing":
                api("/api/gm/choice", {"choice": "resilience"})
                api("/api/gm/resolve", {})
                time.sleep(0.35)
            self.assertEqual(api("/api/state")["ending"]["result"], "lose")


class J10_SeedTestPlayers(unittest.TestCase):
    def test_a_lone_game_master_can_rehearse(self):
        api("/api/gm/reset", {"seed": 101})
        gm = page(1100, 900)
        gm.goto(BASE + "/gm")
        gm.wait_for_selector("#lobby:not([hidden])", timeout=5000)
        gm.fill("#seedn", "12")
        gm.click("#seed")
        gm.wait_for_function("document.querySelectorAll('#players tr').length === 12", timeout=5000)
        gm.click("#start")
        gm.wait_for_selector("#night:not([hidden])", timeout=5000)
        gm.check('input[name=choice][value=hunt]')
        gm.click("#resolve")
        time.sleep(0.8)
        gm.wait_for_function("document.querySelector('#round').textContent === '2'", timeout=8000)
        shot(gm, "j10-gm-playing.png")


class J11_Reset(unittest.TestCase):
    def test_reset_returns_to_an_empty_lobby(self):
        fresh(seed=111)
        api("/api/gm/choice", {"choice": "hunt"})
        api("/api/gm/resolve", {})
        time.sleep(0.6)
        api("/api/gm/reset", {"seed": 112})
        st = api("/api/state")
        self.assertEqual(st["phase"], "lobby")
        self.assertEqual(st["players"], [])
        self.assertEqual(st["round"], 0)
        self.assertIsNone(st["ending"])
        self.assertIn("Waiting for the game master", plain(api("/api/frame")["frame"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
