"""The room server. One process on the game master's laptop, LAN only.

    python3 -m stage2.server            # http://<this-laptop>:8020
    STAGE2_FAST=1 python3 -m stage2.server   # no beat delays (tests)

Pages:  /            phone: join, then your role card
        /gm          game master console
        /projector   the map, full screen
Stdlib only: HTTP plus server-sent events. No websockets, no packages.
"""
from __future__ import annotations
import json
import os
import queue
import socket
import sys
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .game import Game, ACTIONS
from . import frames

HERE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(HERE, "static")
FAST = os.environ.get("STAGE2_FAST") == "1"


class Room:
    def __init__(self, seed=None):
        self.lock = threading.RLock()
        self.game = Game(seed=seed)
        self.subs: list[tuple[str, str, queue.Queue]] = []   # (channel, token, q)
        self.frame = frames.render_lobby(0, self.game.seed)
        self.playing = False
        self.beats: list = []

    # --- sse ---------------------------------------------------------------
    def subscribe(self, channel: str, token: str) -> queue.Queue:
        q: queue.Queue = queue.Queue()
        with self.lock:
            self.subs.append((channel, token, q))
        return q

    def unsubscribe(self, q):
        with self.lock:
            self.subs = [s for s in self.subs if s[2] is not q]

    def push(self, channel: str, event: str, data, token: str | None = None):
        with self.lock:
            for ch, tok, q in self.subs:
                if ch == channel and (token is None or tok == token):
                    q.put((event, data))

    # --- state fan-out ---------------------------------------------------------
    def broadcast_state(self):
        g = self.game
        self.push("gm", "state", self.gm_payload())
        for p in g.players.values():
            self.push("phone", "me", self.me_payload(p), token=p.token)
        if g.phase == "lobby":
            self.frame = frames.render_lobby(len(g.players), g.seed)
            self.push("projector", "frame", {"frame": self.frame})

    def gm_payload(self):
        d = self.game.gm_state()
        d["playing"] = self.playing
        d["actions"] = list(ACTIONS)
        d["fast"] = FAST
        return d

    def me_payload(self, p):
        return {"id": p.id, "name": p.name, "role": p.role or None, "alive": p.alive,
                "phase": self.game.phase, "round": self.game.round, "out_round": p.out_round,
                "ending": self.game.ending}

    # --- the projector plays the beats ------------------------------------------
    def play(self, beats: list):
        self.beats = beats
        self.playing = True
        self.push("gm", "state", self.gm_payload())

        def run():
            for i, b in enumerate(beats):
                self.frame = frames.render_beat(b)
                self.push("projector", "frame", {"frame": self.frame, "beat": i, "kind": b["kind"]})
                if not FAST:
                    time.sleep(b["hold_ms"] / 1000)
            self.playing = False
            self.broadcast_state()
        threading.Thread(target=run, daemon=True).start()

    def map_facts(self) -> dict:
        """Plain counts off the live map, so tests can assert on what is drawn
        rather than on the game's own bookkeeping."""
        g = self.game
        if not g.state:
            return {}
        cov: dict = {}
        for c in g.state.cells:
            cov[c.cover] = cov.get(c.cover, 0) + 1
        owned = set(g.owner.values())
        return {
            "native": cov.get("native", 0), "invasive": cov.get("invasive", 0),
            "bare": cov.get("bare", 0), "water": cov.get("water", 0),
            "village": cov.get("village", 0),
            "fireline": sum(1 for c in g.state.cells if c.fireline),
            "commons": sum(1 for c in g.state.cells
                           if c.cover in ("native", "bare", "invasive")
                           and c.index not in g.owner),
            "owners": len(owned),
            "native_players": sum(1 for p in g.players.values() if p.role == "native"),
            "clusters": len([c for c in g._starting_clusters]) if hasattr(g, "_starting_clusters") else 0,
            "health": g.view()["health"],
        }

    def show_now(self):
        """The current map, no story, for the projector after a start or reset."""
        g = self.game
        if g.state:
            self.frame = frames.render_beat({"kind": "round", "text": "", "fire": [], "view": g.view()})
        else:
            self.frame = frames.render_lobby(len(g.players), g.seed)
        self.push("projector", "frame", {"frame": self.frame})


ROOM = Room(seed=int(os.environ["STAGE2_SEED"]) if os.environ.get("STAGE2_SEED") else None)


class Handler(BaseHTTPRequestHandler):
    server_version = "pyrocene-stage2"

    def log_message(self, fmt, *args):
        if os.environ.get("STAGE2_LOG"):
            super().log_message(fmt, *args)

    # helpers ----------------------------------------------------------------
    def _json(self, code: int, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _file(self, name: str, ctype: str):
        path = os.path.join(STATIC, name)
        if not os.path.isfile(path):
            return self._json(404, {"error": "not found"})
        with open(path, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b""
        try:
            return json.loads(raw or b"{}")
        except json.JSONDecodeError:
            return {}

    # routes -------------------------------------------------------------------
    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(u.query)
        p = u.path
        if p in ("/", "/index.html"):
            return self._file("phone.html", "text/html; charset=utf-8")
        if p == "/gm":
            return self._file("gm.html", "text/html; charset=utf-8")
        if p == "/projector":
            return self._file("projector.html", "text/html; charset=utf-8")
        if p.startswith("/static/"):
            name = p[len("/static/"):]
            ctype = ("text/css" if name.endswith(".css") else
                     "application/javascript" if name.endswith(".js") else "application/octet-stream")
            return self._file(name, ctype)
        if p == "/events":
            return self._sse(qs.get("ch", ["projector"])[0], qs.get("token", [""])[0])
        if p == "/api/state":
            return self._json(200, ROOM.gm_payload())
        if p == "/api/me":
            pl = ROOM.game.by_token(qs.get("token", [""])[0])
            return self._json(200, ROOM.me_payload(pl)) if pl else self._json(404, {"error": "no such player"})
        if p == "/api/beat":            # tests and the projector's ?beat= debug view
            i = int(qs.get("i", ["0"])[0])
            if 0 <= i < len(ROOM.beats):
                b = ROOM.beats[i]
                return self._json(200, {"frame": frames.render_beat(b), "kind": b["kind"],
                                        "text": b["text"], "fire": b["fire"], "n": len(ROOM.beats)})
            return self._json(200, {"frame": ROOM.frame, "kind": "current", "n": len(ROOM.beats)})
        if p == "/api/frame":
            return self._json(200, {"frame": ROOM.frame})
        if p == "/api/map":
            return self._json(200, ROOM.map_facts())
        return self._json(404, {"error": "not found"})

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        p = u.path
        body = self._body()
        g = ROOM.game
        try:
            with ROOM.lock:
                if p == "/api/join":
                    pl = g.add_player(body.get("name", ""))
                    ROOM.broadcast_state()
                    return self._json(200, {"token": pl.token, "id": pl.id, "name": pl.name})
                if p == "/api/gm/seed":
                    n = int(body.get("n", 12))
                    names = ["Asha", "Bala", "Chitra", "Dev", "Esha", "Farid", "Gita", "Hari",
                             "Indu", "Jai", "Kavya", "Lakshmi", "Manu", "Nila", "Om", "Priya",
                             "Ravi", "Sita", "Tara", "Uma"]
                    made = [g.add_player(names[len(g.players) % len(names)]) for _ in range(n)]
                    ROOM.broadcast_state()
                    return self._json(200, {"added": [m.public() for m in made]})
                if p == "/api/gm/start":
                    if body.get("lantana"):
                        g.lantana_override = int(body["lantana"])
                    g.start()
                    ROOM.broadcast_state()
                    ROOM.show_now()
                    return self._json(200, ROOM.gm_payload())
                if p == "/api/gm/eliminate":
                    g.eliminate(body["id"])
                    ROOM.broadcast_state()
                    return self._json(200, ROOM.gm_payload())
                if p == "/api/gm/uneliminate":
                    g.uneliminate(body["id"])
                    ROOM.broadcast_state()
                    return self._json(200, ROOM.gm_payload())
                if p == "/api/gm/choice":
                    g.choose(body.get("choice"), body.get("action"))
                    ROOM.broadcast_state()
                    return self._json(200, ROOM.gm_payload())
                if p == "/api/gm/resolve":
                    if ROOM.playing:
                        return self._json(409, {"error": "still playing the last night"})
                    if g.pending["choice"] is None:
                        return self._json(400, {"error": "choose hunt or resilience first"})
                    beats = g.resolve()
                    ROOM.play(beats)
                    return self._json(200, ROOM.gm_payload())
                if p == "/api/gm/replay":
                    if ROOM.beats and not ROOM.playing:
                        ROOM.play(list(ROOM.beats))
                    return self._json(200, ROOM.gm_payload())
                if p == "/api/gm/reset":
                    seed = body.get("seed")
                    ROOM.game = Game(seed=int(seed) if seed else None)
                    ROOM.beats = []
                    ROOM.playing = False
                    ROOM.broadcast_state()
                    ROOM.show_now()
                    return self._json(200, ROOM.gm_payload())
        except (ValueError, KeyError) as e:
            return self._json(400, {"error": str(e)})
        return self._json(404, {"error": "not found"})

    def _sse(self, channel: str, token: str):
        q = ROOM.subscribe(channel, token)
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        try:
            # first message: where things stand right now
            if channel == "projector":
                self._sse_write("frame", {"frame": ROOM.frame})
            elif channel == "gm":
                self._sse_write("state", ROOM.gm_payload())
            elif channel == "phone":
                pl = ROOM.game.by_token(token)
                if pl:
                    self._sse_write("me", ROOM.me_payload(pl))
            while True:
                try:
                    event, data = q.get(timeout=15)
                    self._sse_write(event, data)
                except queue.Empty:
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            ROOM.unsubscribe(q)

    def _sse_write(self, event: str, data):
        self.wfile.write(f"event: {event}\ndata: {json.dumps(data)}\n\n".encode())
        self.wfile.flush()


def lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


def main():
    port = int(os.environ.get("STAGE2_PORT", "8020"))
    srv = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    srv.daemon_threads = True
    ip = lan_ip()
    print(f"pyrocene stage 2")
    print(f"  players   http://{ip}:{port}/")
    print(f"  game master  http://{ip}:{port}/gm")
    print(f"  projector    http://{ip}:{port}/projector")
    if FAST:
        print("  (fast mode: no beat delays)")
    sys.stdout.flush()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
