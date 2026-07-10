"""Host-side adapter: drive the pokeflow side panel from game events.

This is the only host-aware glue. It maps the game's four narration channels to
pokeflow actor ids and unlocks to grant ids, and reuses the existing
`update_chars` narration so the panel says exactly what the game already says.
pokeflow itself knows none of this.
"""
from __future__ import annotations

import json
import os
import sys

_POKEFLOW = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "pokeflow"))
if _POKEFLOW not in sys.path:
    sys.path.insert(0, _POKEFLOW)

from pokeflow import Pokeflow  # noqa: E402

_BUNDLE = os.path.join(os.path.dirname(__file__), "pokeflow_bundle.json")

# game channel -> pokeflow actor id (here they coincide, but the mapping is
# explicit so the game's vocabulary and pokeflow's ids stay independent).
CHANNEL_TO_ACTOR = {"ivy": "ivy", "rocky": "rocky", "ember": "ember", "elder": "elder"}
VISITORS = {"elder"}
# game unlock -> pokeflow grant id
UNLOCK_TO_GRANT = {"drone": "drone", "translator": "ask", "dss": "dss"}


class PokeflowPanel:
    def __init__(self, color: bool = True, scene: str = "station"):
        with open(_BUNDLE) as f:
            bundle = json.load(f)
        # Use pokeflow's built-in event queue (poll_events) rather than an
        # on_event callback bound to a list we later rebind.
        self.pf = Pokeflow(bundle, color=color)
        self.pf.send({"cmd": "scene.enter", "scene": scene, "focus": "hub"})

    # -- output -------------------------------------------------------------
    def render(self) -> list:
        return self.pf.render_lines()

    # -- focus --------------------------------------------------------------
    def focus_field(self):
        self.pf.send({"cmd": "focus.set", "panel": "field"})

    def focus_hub(self):
        self.pf.send({"cmd": "focus.set", "panel": "hub"})

    # -- narration ----------------------------------------------------------
    def route(self, game_events: list, view: dict):
        """Translate this turn's game events into speech on the panel, reusing
        the game's own `update_chars` to decide who says what."""
        from terminal.play import update_chars
        tmp = {k: {"text": "", "fresh": False} for k in CHANNEL_TO_ACTOR}
        update_chars(tmp, game_events, view)
        for chan, cell in tmp.items():
            if not cell["fresh"]:
                continue
            actor = CHANNEL_TO_ACTOR[chan]
            text = cell["text"]
            if chan in VISITORS:
                # a visitor cameo: enter, speak, leave
                self.pf.send({"cmd": "actor.present", "actor": actor})
                self.pf.send({"cmd": "actor.speak", "actor": actor, "text": text})
                self.pf.send({"cmd": "actor.dismiss", "actor": actor})
            else:
                self.pf.send({"cmd": "actor.speak", "actor": actor, "text": text})

    def interlude(self, dialogue_id: str):
        self.pf.send({"cmd": "dialogue.play", "id_ref": dialogue_id})

    # -- loop pumping -------------------------------------------------------
    def feed(self, key: str):
        self.pf.feed_key(key)

    def tick(self, dt_ms: int = 50):
        self.pf.tick(dt_ms)

    def pump(self, dt_ms: int = 50, max_ticks: int = 4000, redraw=None):
        """Advance until nothing is animating. `redraw` (if given) is called
        each tick so a real host can show frames; here it's optional."""
        n = 0
        while not self.pf.is_idle() and n < max_ticks:
            self.pf.tick(dt_ms)
            if redraw:
                redraw()
            n += 1
        return n

    def drain(self) -> list:
        return self.pf.poll_events()
