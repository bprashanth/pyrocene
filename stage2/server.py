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
from .maps import render as mapstyle

HERE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(HERE, "static")
FAST = os.environ.get("STAGE2_FAST") == "1"
# Which map the projector draws. "ansi" is the terminal board the game
# shipped with; the rest live in stage2/maps and are drawn as SVG.
STYLE = os.environ.get("STAGE2_STYLE", "drawn")


class Room:
    """Holds the game and walks the projector through it.

    A round arrives as a list of steps. Each step is an explanation the room
    reads, then one animation. The game master presses through them, so the
    pace is theirs and nothing important flashes past.
    """

    def __init__(self, seed=None, stage=2):
        self.lock = threading.RLock()
        self.stage = stage
        self.game = Game(seed=seed, config={"stage": stage})
        self.subs: list[tuple[str, str, queue.Queue]] = []
        self.steps: list = []
        self.cursor = 0
        self.replay: list = []        # the map, round by round, for the walk-through
        self.replay_at = 0
        self.mode = "idle"            # idle | explain | playing | replay
        self.frame = (frames.render_lobby(0, self.game.seed) if STYLE == "ansi"
                      else mapstyle.lobby_svg(0, STYLE))

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

    # --- state fan-out ------------------------------------------------------
    def broadcast_state(self):
        g = self.game
        self.push("gm", "state", self.gm_payload())
        for p in g.players.values():
            self.push("phone", "me", self.me_payload(p), token=p.token)

    def gm_payload(self):
        d = self.game.gm_state()
        d["mode"] = self.mode
        d["step"] = self.game.step
        d["steps_left"] = max(0, len(self.steps) - self.cursor)
        cur = self.steps[self.cursor] if self.cursor < len(self.steps) else None
        d["current"] = {"title": cur["title"], "text": cur["text"]} if cur else None
        d["actions"] = list(ACTIONS)
        d["fast"] = FAST
        d["style"] = STYLE
        d["stage"] = self.game.cfg["stage"]
        d["can_replay"] = len(self.game.snapshots) > 1
        d["replay_at"] = self.replay_at
        d["replay_total"] = len(self.replay)
        return d

    def me_payload(self, p):
        return {"id": p.id, "name": p.name, "role": p.role or None, "alive": p.alive,
                "phase": self.game.phase, "round": self.game.round,
                "out_round": p.out_round}

    # --- the projector ------------------------------------------------------
    def paint(self, frame: str, **extra):
        self.frame = frame
        self.push("projector", "frame", dict({"frame": frame}, **extra))

    # --- drawing, in whichever style the room is running -------------------
    def draw_frame(self, beat) -> str:
        if STYLE == "ansi":
            return frames.render_beat(beat)
        return mapstyle.frame_svg(beat, STYLE)

    def draw_card(self, step) -> str:
        if STYLE == "ansi":
            return frames.render_card(step["title"], step["text"], self.game.view(),
                                      step.get("cells"))
        return mapstyle.card_svg(step["title"], step["text"], self.game.view(), STYLE)

    def show_card(self):
        step = self.steps[self.cursor]
        self.mode = "explain"
        self.paint(self.draw_card(step), kind="card")
        self.broadcast_state()

    def show_map(self):
        self.mode = "idle"
        g = self.game
        if g.state:
            self.paint(self.draw_frame(g._frame("settle", "")), kind="map")
        elif STYLE == "ansi":
            self.paint(frames.render_lobby(len(g.players), g.seed), kind="lobby")
        else:
            self.paint(mapstyle.lobby_svg(len(g.players), STYLE), kind="lobby")
        self.broadcast_state()

    def begin(self, steps: list):
        self.steps = steps
        self.cursor = 0
        if not steps:
            return self.show_map()
        self.show_card()

    # --- the replay -----------------------------------------------------------
    def start_replay(self):
        """Walk the map forward one round at a time, with no cards and no
        narration. For the end of a stage 1 game, when the room has played all
        night without seeing what their voting did to the forest."""
        self.replay = self.game.replay_beats()
        if not self.replay:
            return
        self.replay_at = 0
        self.mode = "replay"
        self.paint(self.draw_frame(self.replay[0]), kind="replay")
        self.broadcast_state()

    def step_replay(self):
        if self.mode != "replay":
            return
        self.replay_at += 1
        if self.replay_at >= len(self.replay):
            self.replay = []
            self.replay_at = 0
            return self.show_map()
        self.paint(self.draw_frame(self.replay[self.replay_at]), kind="replay")
        self.broadcast_state()

    def advance(self):
        """Play the animation for the card on screen, then put up the next card."""
        if self.mode == "replay":
            return self.step_replay()
        if self.mode != "explain" or self.cursor >= len(self.steps):
            return
        step = self.steps[self.cursor]
        self.mode = "playing"
        self.broadcast_state()

        def run():
            for f in step["beats"]:
                self.paint(self.draw_frame(f), kind=f["kind"])
                if not FAST:
                    time.sleep(f["hold_ms"] / 1000)
            with self.lock:
                self.cursor += 1
                if self.cursor < len(self.steps):
                    self.show_card()
                else:
                    self.steps = []
                    self.cursor = 0
                    self.show_map()
        threading.Thread(target=run, daemon=True).start()

    def map_facts(self) -> dict:
        g = self.game
        if not g.state:
            return {}
        cov: dict = {}
        for c in g.state.cells:
            cov[c.cover] = cov.get(c.cover, 0) + 1
        return {
            "native": cov.get("native", 0), "invasive": cov.get("invasive", 0),
            "bare": cov.get("bare", 0), "water": cov.get("water", 0),
            "village": cov.get("village", 0),
            "fireline": sum(1 for c in g.state.cells if c.fireline),
            "commons": sum(1 for c in g.state.cells
                           if c.cover in ("native", "bare", "invasive")
                           and c.index not in g.owner),
            "owners": len(set(g.owner.values())),
            "native_players": sum(1 for p in g.players.values() if p.role == "native"),
            "clusters": len(getattr(g, "_starting_clusters", [])),
            "health": g.view()["health"],
        }


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
        if p == "/api/steps":           # tests and screenshots
            out = []
            for st in ROOM.steps:
                out.append({"key": st["key"], "title": st["title"], "text": st["text"],
                            "cells": st["cells"],
                            "kinds": [b["kind"] for b in st["beats"]],
                            "card": ROOM.draw_card(st),
                            "frames": [ROOM.draw_frame(b) for b in st["beats"]],
                            "fire": [b["fire"] for b in st["beats"]],
                            "held": [b.get("held") or [] for b in st["beats"]],
                            "hold_ms": [b["hold_ms"] for b in st["beats"]]})
            return self._json(200, {"steps": out, "cursor": ROOM.cursor, "mode": ROOM.mode})
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
                    ROOM.show_map()
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
                if p == "/api/gm/night":
                    if ROOM.mode != "idle":
                        return self._json(409, {"error": "finish what is on screen first"})
                    ROOM.begin(g.resolve_night())
                    return self._json(200, ROOM.gm_payload())
                if p == "/api/gm/vote":
                    if ROOM.mode != "idle":
                        return self._json(409, {"error": "finish what is on screen first"})
                    ROOM.begin(g.resolve_vote())
                    return self._json(200, ROOM.gm_payload())
                if p == "/api/gm/advance":
                    ROOM.advance()
                    return self._json(200, ROOM.gm_payload())
                if p == "/api/gm/replay":
                    if ROOM.mode in ("explain", "playing"):
                        return self._json(409, {"error": "finish what is on screen first"})
                    if ROOM.mode == "replay":
                        ROOM.step_replay()
                    else:
                        ROOM.start_replay()
                    return self._json(200, ROOM.gm_payload())
                if p == "/api/gm/replay_stop":
                    ROOM.replay, ROOM.replay_at = [], 0
                    ROOM.show_map()
                    return self._json(200, ROOM.gm_payload())
                if p == "/api/gm/reset":
                    seed = body.get("seed")
                    ROOM.game = Game(seed=int(seed) if seed else None,
                                     config={"stage": ROOM.stage})
                    ROOM.steps, ROOM.cursor = [], 0
                    ROOM.replay, ROOM.replay_at = [], 0
                    ROOM.show_map()
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


def addresses() -> list:
    """Every address this machine can be reached on, best guess first.

    A room needs a URL to hand out and the answer differs by situation: the wifi
    address for phones in the room, a Tailscale address for someone testing from
    another network. Printing one guess sent people to the wrong one.
    """
    out = []
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        out.append((s.getsockname()[0], "this machine's default route"))
        s.close()
    except OSError:
        pass
    try:
        import subprocess
        raw = subprocess.run(["ip", "-4", "-o", "addr", "show"], capture_output=True,
                             text=True, timeout=3).stdout
        for line in raw.splitlines():
            parts = line.split()
            if len(parts) < 4:
                continue
            dev, ip = parts[1], parts[3].split("/")[0]
            if ip.startswith("127.") or dev.startswith(("docker", "br-", "veth")):
                continue
            note = ("tailscale, reachable from your other devices"
                    if ip.startswith("100.") else
                    "wifi or ethernet, for phones in the room")
            if ip not in [a for a, _ in out]:
                out.append((ip, note))
            else:
                out = [(a, note if a == ip else n) for a, n in out]
    except (OSError, ValueError, subprocess.SubprocessError):
        pass
    return out or [("127.0.0.1", "this machine only")]


def lan_ip() -> str:
    return addresses()[0][0]


def main():
    """Flags beat environment variables when someone is trying to get a room
    working. The environment still wins nothing: a flag overrides it."""
    import argparse
    ap = argparse.ArgumentParser(prog="python3 -m stage2.server",
                                 description="Run the Stage 2 room server.")
    ap.add_argument("--host", default=os.environ.get("STAGE2_HOST", "0.0.0.0"),
                    help="address to bind (default 0.0.0.0, every interface)")
    ap.add_argument("--port", type=int, default=int(os.environ.get("STAGE2_PORT", "8020")),
                    help="port to listen on (default 8020)")
    ap.add_argument("--style", default=os.environ.get("STAGE2_STYLE", "drawn"),
                    choices=list(mapstyle.STYLES),
                    help="what the projector draws (default drawn; ansi is the terminal board)")
    ap.add_argument("--stage", type=int, default=int(os.environ.get("STAGE2_STAGE", "2")),
                    choices=(1, 2),
                    help="1 is plain Mafia with the map kept back for a replay at "
                         "the end; 2 adds fire and the one choice a night (default)")
    ap.add_argument("--seed", type=int, default=None, help="fix the map")
    ap.add_argument("--fast", action="store_true", help="no animation delays")
    args = ap.parse_args()

    global STYLE, FAST, ROOM
    STYLE = args.style
    if args.fast:
        FAST = True
    if args.seed is not None or args.stage != 2:
        ROOM = Room(seed=args.seed, stage=args.stage)

    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    srv.daemon_threads = True
    addrs = addresses()
    ip = addrs[0][0]
    print(f"pyrocene stage {args.stage}   map style: {STYLE}")
    print()
    print(f"  players      http://{ip}:{args.port}/")
    print(f"  game master  http://{ip}:{args.port}/gm")
    print(f"  projector    http://{ip}:{args.port}/projector")
    if len(addrs) > 1:
        print()
        print("  also reachable on:")
        for a, note in addrs[1:]:
            print(f"    http://{a}:{args.port}/      {note}")
    if args.host not in ("0.0.0.0", "::"):
        print()
        print(f"  bound only to {args.host}: nothing else on the network can reach it")
    if FAST:
        print("  (fast mode: no animation delays)")
    sys.stdout.flush()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
