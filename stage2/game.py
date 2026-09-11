"""Stage 2 game: the room's Mafia state mirrored onto a Pyrocene map, with fire.

Pure logic, no I/O. The server owns a Game, feeds it what the game master
records, and turns the beats that resolve() returns into projector frames.

Round order (see .prompt/stage2.md section 3):
  eliminations -> resilience -> lantana growth -> fire -> Ember -> ending check
"""
from __future__ import annotations
import datetime
import os
import random
import secrets
from copy import deepcopy
from dataclasses import dataclass, field
from collections import deque

from .engine import content as C
from .engine.model import (State, NATIVE, INVASIVE, BARE, WATER, VILLAGE,
                           SEEDLING, ESTABLISHED, DENSE, GROUND)
from .engine.rules import neighbors, neighbors8, health_pct, advance
from .config import CONFIG
from .text import T

LANTANA, NATIVE_P, ECOLOGIST, RANGER = "lantana", "native", "ecologist", "ranger"
FIRELINE, WATER_ACT, EWS = "fireline", "water", "ews"
ACTIONS = (FIRELINE, WATER_ACT, EWS)


@dataclass
class Player:
    id: str
    name: str
    token: str
    role: str = ""
    alive: bool = True
    patch: list = field(default_factory=list)   # cells owned at the start
    out_round: int = 0

    def public(self) -> dict:
        return {"id": self.id, "name": self.name, "alive": self.alive,
                "role": self.role, "out_round": self.out_round}


class Game:
    def __init__(self, seed: int | None = None, config: dict | None = None):
        self.cfg = deepcopy(CONFIG)
        if config:
            self.cfg.update(config)
        self.seed = seed if seed is not None else random.randrange(1_000_000_000)
        self.players: dict[str, Player] = {}
        self.phase = "lobby"          # lobby | playing | ended
        self.round = 0
        self.state: State | None = None
        self.owner: dict[int, str] = {}       # cell -> player id
        self.line_round: dict[int, int] = {}  # fireline cell -> round it was dug
        # The room's night and its day are two separate moments, and each one
        # gets its own explanation and its own animation on the projector.
        self.pending = {"night_kill": None, "vote": None, "choice": None, "action": None}
        self.step = "night"          # night -> day -> night ...
        self.forecast = None
        self.water_round = 0
        self.last_line = None          # {"round", "cluster", "dir"} of the newest fire line
        self.locked_sev, self.locked_cluster = 0, []   # tonight's fire, fixed at the top
        self.village_lost = False
        self.history: list = []
        self.events: list = []         # the event log, one record per round
        self._log_rec = None
        started = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        self.log_meta = {"started": started, "seed": self.seed, "ending": None,
                         "file": f"game-{started}-seed{self.seed}.json",
                         "cols": 0, "rows": 0, "players": []}
        self.ending = None
        self.last_steps: list = []
        self.lantana_override: int | None = None

    # ---- lobby -----------------------------------------------------------
    def add_player(self, name: str) -> Player:
        if self.phase != "lobby":
            raise ValueError("the game has started")
        name = (name or "").strip()[:24] or f"Player {len(self.players) + 1}"
        pid = f"p{len(self.players) + 1:02d}"
        p = Player(id=pid, name=name, token=secrets.token_hex(8))
        self.players[pid] = p
        return p

    def by_token(self, token: str) -> Player | None:
        return next((p for p in self.players.values() if p.token == token), None)

    def lantana_count(self, n: int | None = None) -> int:
        n = len(self.players) if n is None else n
        if self.lantana_override:
            return max(1, min(self.lantana_override, n - 3))
        return max(2, n // self.cfg["lantana_ratio"])

    def start(self):
        n = len(self.players)
        if n < self.cfg["min_players"]:
            raise ValueError(f"need at least {self.cfg['min_players']} players, have {n}")
        rng = random.Random(self.seed)
        k = self.lantana_count()
        ids = list(self.players)
        rng.shuffle(ids)
        roles = [ECOLOGIST, RANGER] + [LANTANA] * k + [NATIVE_P] * (n - 2 - k)
        for pid, role in zip(ids, roles):
            self.players[pid].role = role

        ecfg = dict(self.cfg["engine"])
        self.state = C.new_state(ecfg, self.seed)
        for c in self.state.cells:
            c.obs = GROUND            # the projector shows the whole map
            c.last_seen = 0
        self._allocate(rng)
        self.log_meta["cols"] = self.state.cols
        self.log_meta["rows"] = self.state.rows
        self.log_meta["players"] = [{"player_id": p.id, "name": p.name, "role": p.role}
                                    for p in self.players.values()]
        self.phase = "playing"
        self.round = 1
        self.step = "night"
        self.pending = {"night_kill": None, "vote": None, "choice": None, "action": None}

    def _allocate(self, rng: random.Random):
        """Split about two thirds of the land into contiguous patches, one per
        native and lantana player, and leave the rest as commons. Lantana patches
        are chosen to be far apart so early fires stay small and separate."""
        s = self.state
        land = [c.index for c in s.cells if c.cover in (NATIVE, BARE)]
        owners = [p for p in self.players.values() if p.role in (NATIVE_P, LANTANA)]
        P = len(owners)
        size = max(4, int(len(land) * self.cfg["owned_fraction"]) // P)

        # farthest-point seeds so patches are spread over the map
        seeds = [rng.choice(land)]
        pos = {i: (s.cells[i].r, s.cells[i].c) for i in land}
        while len(seeds) < P:
            best = max(land, key=lambda i: min(abs(pos[i][0] - pos[q][0]) + abs(pos[i][1] - pos[q][1])
                                               for q in seeds) + rng.random() * 0.5)
            seeds.append(best)

        claimed: dict[int, int] = {}
        queues = [deque([q]) for q in seeds]
        patches = [[] for _ in seeds]
        for k, q in enumerate(seeds):
            claimed[q] = k
        grew = True
        while grew:
            grew = False
            for k, q in enumerate(queues):
                if len(patches[k]) >= size:
                    continue
                while q:
                    i = q.popleft()
                    if claimed.get(i) != k or i in patches[k]:
                        continue
                    patches[k].append(i)
                    grew = True
                    nb = [ni for ni, _ in neighbors(s, i) if ni in pos and ni not in claimed]
                    rng.shuffle(nb)
                    for ni in nb:
                        claimed[ni] = k
                        q.append(ni)
                    break

        # which patches are lantana: farthest-first among patch centroids
        cent = [(sum(pos[i][0] for i in p) / len(p), sum(pos[i][1] for i in p) / len(p))
                for p in patches]
        k_l = sum(1 for p in owners if p.role == LANTANA)

        def dist(a, b):
            return abs(cent[a][0] - cent[b][0]) + abs(cent[a][1] - cent[b][1])

        # Random patches that keep a minimum separation, so lantana is spread out
        # but not always in the same corners. Relax the gap until it fits.
        picked: list = []
        for sep in (8, 7, 6, 5, 4, 0):
            for _ in range(200):
                order = list(range(P))
                rng.shuffle(order)
                trial: list = []
                for j in order:
                    if all(dist(j, q) >= sep for q in trial):
                        trial.append(j)
                    if len(trial) == k_l:
                        break
                if len(trial) == k_l:
                    picked = trial
                    break
            if picked:
                break
        lant_players = [p for p in owners if p.role == LANTANA]
        nat_players = [p for p in owners if p.role == NATIVE_P]
        rng.shuffle(nat_players)
        rest = [j for j in range(P) if j not in picked]
        # A lantana player owns a territory but starts with only a small core of
        # it infested. The rest is forest they grow into, so night one has small
        # separate fires and the later nights have big connected ones.
        core_n = self.cfg["lantana_core"]
        lo, hi = self.cfg["initial_stage_age"]
        self._starting_clusters = []
        for pl, j in zip(lant_players, picked):
            cells = patches[j]
            self._give(pl, cells)
            centre = s.cells[cells[0]]
            core = sorted(cells, key=lambda i: (abs(s.cells[i].r - centre.r)
                                                + abs(s.cells[i].c - centre.c)))[:core_n]
            for i in cells:
                c = s.cells[i]
                if c.cover == BARE:
                    c.cover = NATIVE
            for i in core:
                c = s.cells[i]
                c.cover, c.stage, c.stage_age = INVASIVE, ESTABLISHED, rng.randint(lo, hi)
            self._starting_clusters.append(list(core))
        # Homes must not start next to an infestation: the threat to them has to
        # build over the game, so the room has time to see it and act.
        cores = [c.index for c in s.cells if c.cover == INVASIVE]
        safe = self.cfg["village_clearance"]
        for c in s.cells:
            if c.cover != VILLAGE:
                continue
            if all(abs(c.r - s.cells[k].r) + abs(c.c - s.cells[k].c) > safe for k in cores):
                continue
            far = [x for x in s.cells
                   if x.cover == NATIVE and not self.owner.get(x.index)
                   and all(abs(x.r - s.cells[k].r) + abs(x.c - s.cells[k].c) > safe for k in cores)]
            if far:
                new_home = max(far, key=lambda x: min(
                    abs(x.r - s.cells[k].r) + abs(x.c - s.cells[k].c) for k in cores))
                new_home.cover = VILLAGE
                c.cover = NATIVE

        for pl, j in zip(nat_players, rest):
            self._give(pl, patches[j])
            for i in patches[j]:
                c = s.cells[i]
                if c.cover == BARE:
                    c.cover = NATIVE

    def _give(self, p: Player, cells: list):
        p.patch = list(cells)
        for i in cells:
            self.owner[i] = p.id

    # ---- what the game master records -----------------------------------
    def eliminate(self, pid: str):
        """Mark who went out. During the night that is lantana's pick; during the
        day it is the room's vote. One person per moment."""
        p = self.players[pid]
        if not p.alive:
            return
        key = "night_kill" if self.step == "night" else "vote"
        self.pending[key] = pid

    def uneliminate(self, pid: str):
        for key in ("night_kill", "vote"):
            if self.pending.get(key) == pid:
                self.pending[key] = None

    def choose(self, choice: str | None, action: str | None = None):
        if choice not in (None, "hunt", "resilience"):
            raise ValueError("choice must be hunt or resilience")
        if action not in (None, *ACTIONS):
            raise ValueError("unknown resilience action")
        self.pending["choice"] = choice
        self.pending["action"] = action if choice == "resilience" else None
        if choice == "resilience":
            self.pending["vote"] = None      # no vote on a resilience night

    # ---- resolving, one moment at a time ---------------------------------
    # Each returned step is an explanation the room reads, then one animation
    # that shows it happening. The game master presses through them.
    def resolve_night(self) -> list:
        if self.phase != "playing" or self.step != "night":
            raise ValueError("not waiting on a night")
        r = self.round
        steps: list = []
        self.log_open(r)
        pid = self.pending["night_kill"]
        if pid:
            p = self.players[pid]
            p.alive = False
            p.out_round = r
            self.log_player(pid, p.role, "removed")
            before = self.view()
            cells, _ = self._apply_elimination(p)
            after = self.view()
            # The card never names anyone. A night with no map change reads the
            # same whether the ranger saved someone or a specialist was taken,
            # so the room stays guessing and lantana can lie about it.
            key = "night.ground" if cells else "night.nothing"
            steps.append(self._step(
                "night", T("cards", "night.title"),
                T("cards", key, dir=self._dir_of(cells)) if cells else T("cards", key),
                self._transition(before, after, cells, "elimination"), cells=cells))
        else:
            steps.append(self._step(
                "night", T("cards", "night.title"), T("cards", "night.nothing"),
                [self._frame("quiet", "")]))
        self.step = "day"
        self.pending["night_kill"] = None
        end = self._check_end(r)
        if end:
            steps.append(self._ending_step(end))
        return steps

    def resolve_vote(self) -> list:
        if self.phase != "playing" or self.step != "day":
            raise ValueError("not waiting on a day")
        if self.pending["choice"] is None:
            raise ValueError("choose hunt or resilience first")
        r = self.round
        rng = self._rng(r)
        steps: list = []
        self.locked_sev, self.locked_cluster = self.severity()
        rec = self.log_current()
        rec["choice"] = self.pending["choice"]

        if self.pending["choice"] == "hunt":
            pid = self.pending["vote"]
            if pid and self.players[pid].alive:
                p = self.players[pid]
                p.alive = False
                p.out_round = r
                self.log_player(pid, p.role, "removed")
                before = self.view()
                cells, _ = self._apply_elimination(p)
                after = self.view()
                key = ("vote.cleared" if p.role == LANTANA else
                       "vote.lost" if p.role == NATIVE_P else "vote.nothing")
                steps.append(self._step(
                    "vote", T("cards", "vote.title"),
                    T("cards", key, dir=self._dir_of(cells)) if cells else T("cards", key),
                    self._transition(before, after, cells, "elimination"), cells=cells))
            else:
                steps.append(self._step(
                    "vote", T("cards", "vote.title"), T("cards", "vote.nothing"),
                    [self._frame("quiet", "")]))
        else:
            action = self.pending["action"]
            reason = ""
            if not action:
                action, reason = self._auto_action()
                rec["auto"] = True
            rec["resilience"] = {"type": {FIRELINE: "fire_line", WATER_ACT: "water",
                                          EWS: "early_warning"}[action], "cells": []}
            if action == FIRELINE:
                before = self.view()
                text = self._dig_line(r)
                after = self.view()
                cells = list(self.last_line["cells"]) if self.last_line else []
                rec["resilience"]["cells"] = [self.cell_name(i) for i in cells]
                steps.append(self._step(
                    "line", T("cards", "line.title"),
                    (reason + " " if reason else "") + text,
                    self._transition(before, after, cells, "line"), cells=cells))
            elif action == WATER_ACT:
                self.water_round = r
                steps.append(self._step(
                    "water", T("cards", "water.title"),
                    (reason + " " if reason else "") + T("ember", "water.ready"),
                    [self._frame("water", T("ember", "water.ready"))]))
            else:
                steps.append(self._step(
                    "ews", T("cards", "ews.title"),
                    (reason + " " if reason else "") + T("cards", "ews.body"),
                    [self._frame("quiet", "")]))

        # lantana takes ground
        before = self.view()
        grown, halo = self._grow(rng)
        leaked = self._leak(rng)
        advance(self.state, self.cfg, [])
        after = self.view()
        moved = sorted(set(grown) | set(leaked))
        steps.append(self._step(
            "growth", T("cards", "growth.title"),
            T("ember", "growth.one") if len(moved) == 1 else
            T("ember", "growth", n=len(moved)) if moved else T("ember", "growth.none"),
            self._transition(before, after, moved, "creep", halo=halo), cells=moved))

        # fire
        fire_beats, fire_rec, fire_text = self._fire(rng)
        rec["fire"] = fire_rec
        steps.append(self._step(
            "fire", T("cards", "fire.title") if fire_rec["severity"]
            else T("cards", "fire.none_title"), fire_text, fire_beats,
            cells=fire_rec.get("cells", [])))

        if (rec.get("resilience") or {}).get("type") == "early_warning":
            self.forecast = self._forecast(r + 1)
            steps.append(self._step(
                "forecast", T("cards", "forecast.title"),
                T("ember", "forecast", level=T("ember", f"forecast.{self.forecast['level']}"),
                  wind=self.forecast["wind"]),
                [self._frame("forecast", "")]))
        else:
            self.forecast = None

        self.history.append({"round": r, "choice": rec["choice"], "action": rec.get("action"),
                             "auto": rec.get("auto", False), "fire": rec.get("fire") or {"severity": 0},
                             "health": health_pct(self.state),
                             "eliminations": rec.get("player_changes", [])})
        self.log_close()

        end = self._check_end(r)
        if end:
            steps.append(self._ending_step(end))
        else:
            self.round += 1
            self.step = "night"
            if rng.random() < 0.3:
                self.state.wind = rng.choice(("N", "S", "E", "W"))
        self.pending = {"night_kill": None, "vote": None, "choice": None, "action": None}
        self.last_steps = steps
        return steps

    # ---- step and frame helpers -------------------------------------------
    def _step(self, key: str, title: str, text: str, beats: list, cells=None) -> dict:
        return {"key": key, "title": title, "text": text, "beats": beats,
                "cells": [self.cell_name(i) for i in (cells or [])]}

    def _frame(self, kind: str, text: str, view: dict | None = None, **extra) -> dict:
        f = {"kind": kind, "text": text, "fire": [], "focus": [], "halo": [],
             "held": [], "haze": False, "view": view or self.view(),
             "hold_ms": self.cfg["hold_ms"].get(kind, 900)}
        f.update(extra)
        return f

    @staticmethod
    def _blend(before: dict, after: dict, reveal) -> dict:
        """The board as it was, with `reveal` squares already turned over. This
        is what makes a change visible. Without it every frame of a step drew
        the finished map and the only motion was a blink."""
        rev = set(reveal)
        post = {c["index"]: c for c in after["cells"]}
        out = dict(after)
        out["cells"] = [post[c["index"]] if c["index"] in rev else c
                        for c in before["cells"]]
        return out

    def _transition(self, before: dict, after: dict, cells: list, kind: str,
                    halo: list | None = None) -> list:
        """Haze the rest of the board, hold on the squares about to change, turn
        them over a few at a time, then bring the whole map back at full weight.
        About four seconds, so a room can follow it."""
        cells = list(cells)
        if not cells:
            return [self._frame("quiet", "", before)]
        out = [self._frame("focus", "", before, focus=cells, haze=True)]
        if halo:
            out.append(self._frame("halo", "", before, focus=cells,
                                   halo=list(halo), haze=True))
        st = self.state
        order = sorted(cells, key=lambda i: (st.cells[i].r, st.cells[i].c))
        size = max(1, -(-len(order) // 4))
        shown: list = []
        for k in range(0, len(order), size):
            shown = shown + order[k:k + size]
            out.append(self._frame(kind, "", self._blend(before, after, shown),
                                   focus=list(shown), haze=True))
        out.append(self._frame("settle", "", after))
        return out

    def _ending_step(self, end: dict) -> dict:
        self.phase = "ended"
        self.ending = end
        self.log_ending(end)
        return {"key": "ending", "title": T("cards", "end.title"), "text": end["text"],
                "beats": [self._frame("ending", end["text"])], "cells": []}

    def cell_name(self, i: int) -> str:
        c = self.state.cells[i]
        return f"{chr(65 + c.c)}{c.r + 1}"

    def _rng(self, r: int) -> random.Random:
        return random.Random(self.seed * 1000 + r)

    # ---- the pieces --------------------------------------------------------
    def _apply_elimination(self, p: Player):
        """Returns (changed cells, what Ember says). The map only moves for a
        lantana or a native; the specialists own no ground."""
        s = self.state
        cells = [i for i, o in self.owner.items() if o == p.id]
        if p.role == LANTANA:
            for i in cells:
                c = s.cells[i]
                was = c.cover
                if self.cfg["bare_on_removal"]:
                    c.cover, c.stage, c.stage_age, c.seedbank = BARE, 0, 0, False
                else:
                    c.cover, c.stage, c.stage_age = NATIVE, 0, 0
                self.log_cell(i, was, c.cover, c.stage)
                del self.owner[i]
            key = "elim.lantana" if self.cfg["bare_on_removal"] else "elim.lantana_native"
            return cells, T("ember", key, dir=self._dir_of(cells))
        if p.role == NATIVE_P:
            core_n = self.cfg["native_loss_core"]
            free = [i for i in cells if s.cells[i].cover in (NATIVE, BARE)]
            lant = [c.index for c in s.cells if c.cover == INVASIVE]
            near = sorted(free, key=lambda i: min(
                (abs(s.cells[i].r - s.cells[j].r) + abs(s.cells[i].c - s.cells[j].c)
                 for j in lant), default=0))
            taken = near[:core_n]
            for i in taken:
                c = s.cells[i]
                was = c.cover
                c.cover, c.stage, c.stage_age = INVASIVE, ESTABLISHED, 0
                self.log_cell(i, was, c.cover, c.stage)
            for i in cells:
                del self.owner[i]
            return taken, T("ember", "elim.native", dir=self._dir_of(cells or taken))
        return [], T("ember", f"elim.{p.role}")

    def _grow(self, rng: random.Random):
        s, cfg = self.state, self.cfg
        new: dict[int, str | None] = {}
        candidates: set = set()          # ground lantana is pressing on, for the halo
        for c in s.cells:
            if c.cover != INVASIVE or c.stage < ESTABLISHED:
                continue
            base = cfg["growth_dense"] if c.stage == DENSE else cfg["growth_established"]
            own = self.owner.get(c.index)
            if own is None or not self.players[own].alive:
                base *= cfg["orphan_mult"]
            nbrs = neighbors8(s, c.index) if c.stage == DENSE else neighbors(s, c.index)
            for ni, d in nbrs:
                n = s.cells[ni]
                if n.cover not in (NATIVE, BARE) or n.fireline or ni in new:
                    continue
                candidates.add(ni)
                p = base
                if d == s.wind:
                    p *= cfg["growth_wind_mult"]
                if n.cover == BARE:
                    p *= cfg["growth_bare_mult"]
                if rng.random() < p:
                    new[ni] = own
        for ni, own in new.items():
            n = s.cells[ni]
            was = n.cover
            n.cover, n.stage, n.stage_age = INVASIVE, SEEDLING, 0
            self.log_cell(ni, was, n.cover, n.stage)
            if own is not None:
                self.owner[ni] = own
            else:
                self.owner.pop(ni, None)
        return sorted(new), sorted(candidates - set(new))

    def _leak(self, rng: random.Random):
        """Bare ground goes to whoever is next to it: lantana if any, else forest."""
        s, cfg = self.state, self.cfg
        changes = []
        for c in s.cells:
            if c.cover != BARE or c.fireline:
                continue
            lant = [ni for ni, _ in neighbors8(s, c.index) if s.cells[ni].cover == INVASIVE]
            if lant:
                if rng.random() < cfg["reinvade_p"]:
                    src = rng.choice(lant)
                    changes.append((c.index, INVASIVE, self.owner.get(src)))
            elif rng.random() < cfg["regen_p"]:
                changes.append((c.index, NATIVE, None))
        touched = []
        for i, cover, own in changes:
            c = s.cells[i]
            was = c.cover
            touched.append(i)
            if cover == INVASIVE:
                c.cover, c.stage, c.stage_age = INVASIVE, SEEDLING, 0
                if own is not None:
                    self.owner[i] = own
                else:
                    self.owner.pop(i, None)
            else:
                c.cover, c.seedbank = NATIVE, False
            self.log_cell(i, was, c.cover, c.stage)
        return touched

    # fire ---------------------------------------------------------------
    def dense_clusters(self) -> list:
        s = self.state
        seen, out = set(), []
        for c in s.cells:
            if c.cover != INVASIVE or c.stage != DENSE or c.index in seen:
                continue
            comp, q = [], deque([c.index])
            seen.add(c.index)
            while q:
                i = q.popleft()
                comp.append(i)
                for ni, _ in neighbors8(s, i):
                    n = s.cells[ni]
                    if ni not in seen and n.cover == INVASIVE and n.stage == DENSE:
                        seen.add(ni)
                        q.append(ni)
            out.append(comp)
        out.sort(key=len, reverse=True)
        return out

    def severity(self) -> tuple[int, list]:
        """0 nothing to burn, else 1..3 from the largest connected dense cluster."""
        clusters = self.dense_clusters()
        fuel = any(c.cover == INVASIVE and c.stage >= ESTABLISHED for c in self.state.cells)
        if not fuel and not clusters:
            return 0, []
        biggest = clusters[0] if clusters else []
        n = len(biggest)
        if n < self.cfg["sev_t1"]:
            return 1, biggest
        if n < self.cfg["sev_t2"]:
            return 2, biggest
        return 3, biggest

    def _fire(self, rng: random.Random):
        """Returns (animation frames, log record, what Ember says)."""
        s, cfg = self.state, self.cfg
        sev, cluster = self.locked_sev, self.locked_cluster
        cluster = [i for i in cluster
                   if s.cells[i].cover == INVASIVE and s.cells[i].stage == DENSE]
        quiet = ([self._frame("quiet", "")], {"severity": 0, "burned_cells": []},
                 T("ember", "fire.quiet"))
        if sev == 0:
            return quiet
        if sev == 1 and not cluster and rng.random() >= cfg["spark_p"]:
            return quiet
        capped = False
        if self.water_round == self.round and sev > 1:
            sev, capped = 1, True

        push = None
        forced_path: list = []
        target = None
        fresh = self.last_line and self.last_line["round"] == self.round
        if fresh and self.last_line.get("cells"):
            fenced = [i for i in self.last_line["cluster"]
                      if s.cells[i].cover == INVASIVE and s.cells[i].stage >= ESTABLISHED]
            lines = [i for i in self.last_line["cells"] if s.cells[i].fireline]
            if fenced and lines:
                got = self._run_to_line(fenced, lines)
                if got:
                    igniter, forced_path = got
                    push = self.last_line["dir"]
        if push is None:
            pool = cluster or [c.index for c in s.cells
                               if c.cover == INVASIVE and c.stage >= ESTABLISHED]
            if not pool:
                return quiet
            igniter = rng.choice(pool)

        ramp = 1 + cfg["fire_round_ramp"] * (self.round - 1)
        cap = round(cfg["fire_cells"][sev] * ramp)
        forced = forced_path[:max(0, cap - 1)] if push else []
        order, blocked = self._spread_fire(rng, igniter, cap, push=push, forced=forced)

        frames = [self._frame("ignite", "", None, fire=[igniter])]
        shown = [igniter]
        for wave in order[1:]:
            shown = shown + wave
            frames.append(self._frame("spread", "", fire=list(shown)))
        burned = list(shown)
        frames.append(self._frame("burn", "", fire=list(burned)))

        village_hit = False
        for i in burned:
            c = s.cells[i]
            was = c.cover
            c.cover, c.stage, c.stage_age, c.seedbank = BARE, 0, 0, True
            self.log_cell(i, was, c.cover, c.stage)
            if any(s.cells[ni].cover == VILLAGE for ni, _ in neighbors(s, i)):
                village_hit = True
        burnt_view = self.view()

        d = self._dir_of(burned)
        if self.water_round == self.round:
            text = T("ember", "fire.water", dir=d, n=len(burned))
        elif sev == 1:
            text = T("ember", "fire.spark.one" if len(burned) == 1 else "fire.spark",
                     dir=d, n=len(burned))
        else:
            text = T("ember", f"fire.sev{sev}", dir=d, n=len(burned))
        if blocked:
            text += " " + T("ember", "fire.blocked",
                            r=min(self.line_round.get(i, self.round) for i in blocked))
            frames.append(self._frame("blocked", "", fire=list(burned),
                                      held=sorted(blocked)))
        if village_hit:
            text += " " + T("ember", "fire.village")
        if sev >= 2 and not blocked:
            text += " " + T("ember", "fire.cost")
        # What it left behind. The frames above still showed the ground as it was
        # under the flames, so without this the room never sees the cost.
        frames.append(self._frame("scorch", "", burnt_view, focus=list(burned), haze=True))
        frames.append(self._frame("settle", "", burnt_view))

        c0 = s.cells[igniter]
        cause = "road_human" if c0.road else "dense_lantana" if sev > 1 else "spark"
        rec = {"ignition_cell": self.cell_name(igniter), "ignition_cause": cause,
               "severity": sev, "capped_by_water": capped,
               "burned_cells": [self.cell_name(i) for i in burned],
               "blocked_edges": self._blocked_edges(burned, blocked),
               "village_reached": village_hit}
        if village_hit and sev >= 2:
            self.village_lost = True
        return frames, rec, text

    def _blocked_edges(self, burned: list, blocked) -> list:
        """Which trench cells the fire actually pushed against, as the pair of
        cells the edge sits between."""
        s = self.state
        bset = set(burned)
        out = []
        for b in sorted(blocked):
            for ni, _ in neighbors(s, b):
                if ni in bset:
                    out.append([self.cell_name(ni), self.cell_name(b)])
        return out

    def _run_to_line(self, fuel: list, lines: list):
        """Find the shortest burnable run from any of `fuel` to any of `lines`.

        Breadth-first outward from the line, through ground the fire can cross,
        so the run goes around the river instead of giving up at it. Returns
        (igniter, path) where path is the cells between the two, or None if the
        fire could never get there.
        """
        s = self.state
        fuelset = set(fuel)
        prev: dict[int, int] = {}
        seen = set(lines)
        frontier = list(lines)
        hit = None
        for _ in range(12):
            nxt = []
            for i in frontier:
                for ni, _ in neighbors(s, i):
                    if ni in seen:
                        continue
                    n = s.cells[ni]
                    if n.cover in (WATER, VILLAGE) or n.fireline:
                        continue
                    seen.add(ni)
                    prev[ni] = i
                    if ni in fuelset:
                        hit = ni
                        break
                    nxt.append(ni)
                if hit:
                    break
            if hit or not nxt:
                break
            frontier = nxt
        if hit is None:
            return None
        path, cur = [], prev.get(hit)
        while cur is not None and cur not in lines:
            path.append(cur)
            cur = prev.get(cur)
        return hit, path

    def _spread_fire(self, rng: random.Random, igniter: int, cap: int,
                     push: str | None = None, forced: list | None = None):
        """Breadth-first fire from the igniter. Returns the waves in order and the
        set of fire-line cells the fire ran into. `push` leans the fire in one
        direction, the way wind does, used the night a line is dug."""
        s, cfg = self.state, self.cfg
        lean = push or s.wind
        seen = {igniter}
        waves = [[igniter]]
        blocked = set()

        # The run at a fresh fire line goes first, one cell per wave. Without
        # this the fire fills its own patch, hits the cell cap, and never gets
        # to the line the room just paid for.
        for i in (forced or []):
            if i in seen:
                continue
            seen.add(i)
            waves.append([i])
        for i in list(seen):
            for ni, _ in neighbors(s, i):
                if s.cells[ni].fireline:
                    blocked.add(ni)

        frontier = list(seen)
        for _ in range(cfg["fire_iters"]):
            nxt = []
            for i in frontier:
                for ni, d in neighbors(s, i):
                    if ni in seen or len(seen) >= cap:
                        continue
                    n = s.cells[ni]
                    if n.cover in (WATER, VILLAGE):
                        continue
                    if n.fireline:
                        blocked.add(ni)
                        continue
                    pp = (cfg["fire_p_invasive"] if n.cover == INVASIVE
                          else cfg["fire_p_native"] if n.cover == NATIVE else cfg["fire_p_bare"])
                    if d == lean:
                        pp *= cfg["fire_wind_mult"]
                    if rng.random() < pp:
                        seen.add(ni)
                        nxt.append(ni)
            if not nxt:
                break
            waves.append(nxt)
            frontier = nxt
        return waves, blocked

    # resilience -----------------------------------------------------------
    def village_at_risk(self) -> bool:
        """Is there dense lantana close enough to the homes to reach them?"""
        s = self.state
        clusters = self.dense_clusters()
        if not clusters:
            return False
        near = self._near(clusters[0], self.cfg["line_reach"] + 1)
        return any(s.cells[i].cover == VILLAGE for i in near)

    def _auto_action(self) -> tuple[str, str]:
        """Pick the most useful action for the map as it stands. A forecast is
        the last resort: spending the room's one choice on information while a
        dense stand sits next to the village teaches the wrong lesson."""
        s = self.state
        clusters = self.dense_clusters()
        sev = self.locked_sev
        # A fire this big will run past any single break, so the answer is
        # people and water, not a trench.
        if sev >= 3:
            return WATER_ACT, T("ember", "auto.big")
        if clusters:
            near = self._near(clusters[0], self.cfg["line_reach"])
            if any(s.cells[i].cover == VILLAGE for i in near):
                return FIRELINE, T("ember", "auto.village")
            return FIRELINE, T("ember", "auto.native")
        if sev >= 2:
            return WATER_ACT, T("ember", "auto.big")
        return EWS, T("ember", "auto.watch")

    def _near(self, cells: list, reach: int) -> set:
        s = self.state
        out, frontier, seen = set(), list(cells), set(cells)
        for _ in range(reach):
            nxt = []
            for i in frontier:
                for ni, _ in neighbors(s, i):
                    if ni not in seen:
                        seen.add(ni)
                        nxt.append(ni)
                        out.add(ni)
            frontier = nxt
        return out

    def _asset(self, fuel: list | None = None) -> tuple[list, str]:
        """What the crew defends: the homes when the fire could actually reach
        them, otherwise the largest unbroken block of native forest next to the
        fuel. Lines hug this, so each night the room spends on resilience
        extends the same sanctuary instead of chasing whichever stand happens to
        be worst tonight."""
        s = self.state
        vill = [c.index for c in s.cells if c.cover == VILLAGE]
        if vill and fuel:
            # Only defend the homes if the fire is near enough to threaten them.
            # A trench across the map from the fuel teaches nothing tonight.
            reach = self.cfg["village_defend_range"]
            close = min(abs(s.cells[v].r - s.cells[f].r) + abs(s.cells[v].c - s.cells[f].c)
                        for v in vill for f in fuel)
            if close > reach:
                vill = []
        if vill:
            ring = set(vill)
            for i in vill:
                for ni, _ in neighbors8(s, i):
                    if s.cells[ni].cover == NATIVE:
                        ring.add(ni)
            return sorted(ring), "village"
        seen, best, best_key = set(), [], None
        for c in s.cells:
            if c.cover != NATIVE or c.index in seen:
                continue
            comp, q = [], deque([c.index])
            seen.add(c.index)
            while q:
                i = q.popleft()
                comp.append(i)
                for ni, _ in neighbors(s, i):
                    if ni not in seen and s.cells[ni].cover == NATIVE:
                        seen.add(ni)
                        q.append(ni)
            # Prefer a big block, but a big block the fire can actually reach.
            if fuel:
                near = min(abs(s.cells[i].r - s.cells[f].r) + abs(s.cells[i].c - s.cells[f].c)
                           for i in comp for f in fuel[:12])
            else:
                near = 0
            key = (len(comp) >= 8, -near, len(comp))
            if best_key is None or key > best_key:
                best, best_key = comp, key
        return best, "native forest"

    def _dig_line(self, r: int) -> str:
        """Dig a break around what needs protecting, on the side the fire will
        come from. Lines are permanent, so repeated nights of resilience close
        the ring a bit further each time."""
        s, cfg = self.state, self.cfg
        clusters = self.dense_clusters()
        fuel = clusters[0] if clusters else [
            c.index for c in s.cells if c.cover == INVASIVE and c.stage >= ESTABLISHED]
        if not fuel:
            return T("ember", "growth.none")
        asset, asset_name = self._asset(fuel)
        if not asset:
            return T("ember", "line.none_room")

        aset = set(asset)
        # the ring of land just outside the asset: candidate trench cells
        rim = []
        for i in asset:
            for ni, _ in neighbors8(s, i):
                if ni in aset:
                    continue
                n = s.cells[ni]
                if n.cover in (WATER, VILLAGE) or n.fireline:
                    continue
                rim.append(ni)
        rim = sorted(set(rim))
        if len(rim) < 3:
            return T("ember", "line.none_room")

        # dig the stretch of that rim nearest the fuel: the side fire comes from
        def near_fuel(i):
            return min(abs(s.cells[i].r - s.cells[f].r) + abs(s.cells[i].c - s.cells[f].c)
                       for f in fuel)

        rim.sort(key=near_fuel)
        chosen = rim[:cfg["line_cells"]]
        for i in chosen:
            c = s.cells[i]
            if c.cover == INVASIVE:
                c.cover, c.stage, c.stage_age = BARE, 0, 0
            c.fireline = True
            self.line_round[c.index] = r
        self.last_line = {"round": r, "cluster": list(fuel), "dir": "-",
                          "cells": list(chosen)}
        key = "line.placed" if clusters else "line.none"
        return T("ember", key, dir=self._dir_of(chosen), asset=asset_name)

    def _forecast(self, next_round: int) -> dict:
        """Dry-run next round's growth on a copy, with next round's rng, and read
        the severity off it. Exact if the room changes nothing before then."""
        g = deepcopy(self)
        g.round = next_round
        rng = g._rng(next_round)
        g._grow(rng)
        g._leak(rng)
        advance(g.state, g.cfg, [])
        sev, cluster = g.severity()
        if sev == 1 and not cluster and rng.random() >= g.cfg["spark_p"]:
            sev = 0
        level = {0: "none", 1: "small", 2: "medium", 3: "large"}[sev]
        names = {"N": "north", "S": "south", "E": "east", "W": "west"}
        return {"round": next_round, "severity": sev, "level": level, "wind": names[self.state.wind]}

    # endings ------------------------------------------------------------------
    def _check_end(self, r: int) -> dict | None:
        alive = [p for p in self.players.values() if p.alive]
        h = health_pct(self.state)
        if self.cfg["village_loss"] and self.village_lost:
            return {"result": "lose", "reason": "village", "health": h,
                    "text": T("ember", "end.lose.village")}
        if not any(p.role == LANTANA for p in alive):
            key = "end.win" if h >= 60 else "end.win_low"
            return {"result": "win", "reason": "lantana", "health": h, "text": T("ember", key, health=h)}
        if h < self.cfg["loss_health"]:
            return {"result": "lose", "reason": "fire", "health": h, "text": T("ember", "end.lose.fire", health=h)}
        if not any(p.role == NATIVE_P for p in alive):
            return {"result": "lose", "reason": "natives", "health": h,
                    "text": T("ember", "end.lose.natives", health=h)}
        if self.cfg["team_loss"] and not any(p.role in (ECOLOGIST, RANGER) for p in alive):
            return {"result": "lose", "reason": "team", "health": h, "text": T("ember", "end.lose.team")}
        if r >= self.cfg["max_rounds"]:
            return {"result": "lose", "reason": "time", "health": h, "text": T("ember", "end.lose.time", r=r)}
        return None

    # views ----------------------------------------------------------------------
    def view(self) -> dict:
        """A full-detail map view in the shape render.py expects."""
        s = self.state
        cells = [{"index": c.index, "r": c.r, "c": c.c, "known": True, "cover": c.cover,
                  "stage": c.stage, "detail": 3, "bank": c.corridor, "fireline": c.fireline,
                  "hill": c.hill, "road": c.road, "risk": 0, "hotspot": False,
                  "monitored": False, "last_seen": 0} for c in s.cells]
        return {"cols": s.cols, "rows": s.rows, "cells": cells, "health": health_pct(s),
                "round": self.round, "max_rounds": self.cfg["max_rounds"], "wind": s.wind}

    def _dir_of(self, cells: list) -> str:
        s = self.state
        if not cells:
            return "middle"
        r = sum(s.cells[i].r for i in cells) / len(cells)
        c = sum(s.cells[i].c for i in cells) / len(cells)
        ns = "north" if r < s.rows * 0.38 else "south" if r > s.rows * 0.62 else ""
        ew = "west" if c < s.cols * 0.38 else "east" if c > s.cols * 0.62 else ""
        return (ns + (" " if ns and ew else "") + ew) or "middle"

    # ---- event log ---------------------------------------------------------
    # One record per round, written to stage2/logs so a post-game sequence can
    # be built from it without reading any of this code.
    def log_open(self, turn: int):
        self._log_rec = {"turn": turn, "choice": None, "auto": False,
                         "player_changes": [], "landscape_changes": [],
                         "resilience": None, "fire": None,
                         "health_before": health_pct(self.state)}

    def log_current(self) -> dict:
        if not getattr(self, "_log_rec", None):
            self.log_open(self.round)
        return self._log_rec

    def log_player(self, pid: str, role: str, to: str):
        self.log_current()["player_changes"].append(
            {"player_id": pid, "from": role, "to": to})

    def log_cell(self, i: int, was: str, now: str, stage: int = 0):
        if was == now:
            return
        name = {1: "invasive_young", 2: "invasive_spreading", 3: "invasive_thick"}
        to = name.get(stage, now) if now == INVASIVE else now
        frm = was
        self.log_current()["landscape_changes"].append(
            {"cell": self.cell_name(i), "from": frm, "to": to})

    def log_close(self):
        rec = self.log_current()
        rec["health"] = health_pct(self.state)
        rec["health_loss"] = max(0, rec["health_before"] - rec["health"])
        self.events.append(rec)
        self._log_rec = None
        self._write_log()

    def log_ending(self, end: dict):
        self.log_meta["ending"] = end
        self._write_log()

    def _write_log(self):
        """Rewrite this game's log file and point index.json at it. Cheap enough
        to do every round, and it means an interrupted game still leaves a log."""
        import json
        d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        os.makedirs(d, exist_ok=True)
        body = {"game": self.log_meta, "rounds": self.events}
        path = os.path.join(d, self.log_meta["file"])
        with open(path, "w", encoding="utf-8") as f:
            json.dump(body, f, indent=2)
        idx_path = os.path.join(d, "index.json")
        idx = {"latest": self.log_meta["file"], "games": []}
        if os.path.exists(idx_path):
            try:
                idx = json.load(open(idx_path, encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        idx["latest"] = self.log_meta["file"]
        games = [g for g in idx.get("games", []) if g.get("file") != self.log_meta["file"]]
        games.append({"file": self.log_meta["file"], "started": self.log_meta["started"],
                      "seed": self.seed, "rounds": len(self.events),
                      "ending": (self.log_meta.get("ending") or {}).get("reason")})
        idx["games"] = games[-50:]
        with open(idx_path, "w", encoding="utf-8") as f:
            json.dump(idx, f, indent=2)

    def gm_state(self) -> dict:
        alive = [p for p in self.players.values() if p.alive]
        return {
            "phase": self.phase, "round": self.round, "max_rounds": self.cfg["max_rounds"],
            "seed": self.seed, "lantana_count": self.lantana_count() if self.players else 0,
            "players": [p.public() for p in self.players.values()],
            "pending": dict(self.pending),
            "health": health_pct(self.state) if self.state else None,
            "alive": {"lantana": sum(p.role == LANTANA for p in alive),
                      "native": sum(p.role == NATIVE_P for p in alive),
                      "ecologist": any(p.role == ECOLOGIST for p in alive),
                      "ranger": any(p.role == RANGER for p in alive)},
            "forecast": self.forecast, "ending": self.ending,
            "village_at_risk": self.village_at_risk() if self.state else False,
            "log": self.log_meta["file"],
            "history": self.history[-3:],
        }
