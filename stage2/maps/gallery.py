"""Render the same real game moments through every style, side by side.

    python3 -m stage2.maps.gallery                 # all styles, all moments
    python3 -m stage2.maps.gallery poster heat     # just these
    python3 -m stage2.maps.gallery --moment fire

Writes stage2/maps/out/gallery.html plus one SVG per cell, so a style can be
opened on its own at full size.
"""
from __future__ import annotations
import argparse
import importlib
import os
import sys

from ..game import Game
from .model import from_view
from .scenes import all_scenes

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

STYLES = ["poster", "signal", "heat", "drawn", "terrain", "iso"]


def load(name):
    return importlib.import_module(f".{name}", __package__)


def moments(seed=3, players=14):
    """Play a game and grab the states worth judging a style on."""
    g = Game(seed=seed)
    for i in range(players):
        g.add_player(f"P{i + 1}")
    g.start()
    out = {}

    def snap(key, **ov):
        out[key] = from_view(g.view(), **ov)

    snap("opening", note="Night 1. Three separate patches of lantana.")

    nat = [p for p in g.players.values() if p.role == "native"]
    lant = [p for p in g.players.values() if p.role == "lantana"]
    # a night where a stand is lost, held on the squares that change
    g.eliminate(nat[0].id)
    steps = g.resolve_night()
    st = next((s for s in steps if s["key"] == "night"), None)
    if st:
        f = st["beats"][0]
        out["focus"] = from_view(f["view"], focus=f["focus"], haze=True,
                                 note="Holding on the squares about to change.")
    g.choose("hunt", None)
    g.resolve_vote()

    for r in range(3):
        if g.phase != "playing":
            break
        g.resolve_night()
        g.choose("hunt", None)
        steps = g.resolve_vote()
    snap("midgame", note="Night 5. The patches have met.")

    # a growth moment with the halo
    g.resolve_night()
    g.choose("hunt", None)
    steps = g.resolve_vote()
    gr = next((s for s in steps if s["key"] == "growth"), None)
    if gr and len(gr["beats"]) > 1:
        f = gr["beats"][1]
        out["halo"] = from_view(f["view"], focus=f["focus"], halo=f["halo"],
                                haze=True, note="Ground the lantana is pressing on.")
    fr = next((s for s in steps if s["key"] == "fire"), None)
    if fr:
        mid = fr["beats"][min(2, len(fr["beats"]) - 1)]
        out["fire"] = from_view(mid["view"], fire=mid["fire"],
                                note="Fire running through the fuel.")

    # a line that holds
    for seed2 in range(12):
        h = Game(seed=seed2)
        for i in range(players):
            h.add_player(f"P{i + 1}")
        h.start()
        for _ in range(2):
            h.resolve_night()
            h.choose("hunt", None)
            h.resolve_vote()
        if h.phase != "playing":
            continue
        h.resolve_night()
        h.choose("resilience", "fireline")
        steps = h.resolve_vote()
        fr = next((s for s in steps if s["key"] == "fire"), None)
        if fr and any(b["kind"] == "blocked" for b in fr["beats"]):
            b = next(b for b in fr["beats"] if b["kind"] == "blocked")
            out["blocked"] = from_view(b["view"], fire=b["fire"], held=b["held"],
                                       note="The fire runs into the trench and stops.")
            ln = next((s for s in steps if s["key"] == "line"), None)
            if ln:
                lb = ln["beats"][0]
                out["trench"] = from_view(lb["view"], focus=lb["focus"], haze=True,
                                          note="Where the crew is digging.")
            break
    return out


def build(styles, keys=None, real=False):
    os.makedirs(OUT, exist_ok=True)
    # Hand-built scenes first: every style judged on identical, well-formed
    # content. Real games are appended for a sanity check that nothing in a
    # style falls over on whatever the dice actually produce.
    scenes = all_scenes()
    if real:
        scenes.update({f"game-{k}": v for k, v in moments().items()})
    if keys:
        scenes = {k: v for k, v in scenes.items() if k in keys}
    mods = []
    for s in styles:
        try:
            mods.append(load(s))
        except ModuleNotFoundError:
            print(f"  (no style {s} yet)")
    rows = []
    for key, scene in scenes.items():
        cells = []
        for m in mods:
            try:
                svg = m.render(scene)
            except Exception as e:                      # a broken style must not
                svg = f"<p style='color:#f66'>{m.NAME}: {e}</p>"   # hide the rest
            path = os.path.join(OUT, f"{m.NAME}-{key}.svg")
            if svg.startswith("<svg"):
                open(path, "w").write(svg)
            cells.append(f'<figure><figcaption>{m.NAME}'
                         f'<span>{getattr(m, "BLURB", "")}</span></figcaption>'
                         f'<div class="frame">{svg}</div></figure>')
        rows.append(f'<section><h2>{key}</h2><div class="row">{"".join(cells)}</div></section>')
    html = f"""<!doctype html><meta charset="utf-8"><title>Pyrocene map styles</title>
<style>
 body{{margin:0;background:#0a0d12;color:#e6edf5;font:15px/1.5 Inter,system-ui,sans-serif}}
 h1{{margin:0;padding:22px 28px;font-size:19px;letter-spacing:.2em}}
 section{{padding:6px 28px 26px}}
 h2{{font-size:13px;letter-spacing:.24em;text-transform:uppercase;color:#7b8a9c;margin:22px 0 10px}}
 .row{{display:flex;gap:20px;flex-wrap:wrap}}
 figure{{margin:0;background:#11151c;border:1px solid #1e2530;border-radius:12px;overflow:hidden}}
 figcaption{{padding:9px 14px;font-size:12px;letter-spacing:.16em;text-transform:uppercase;
   color:#9fb0c4;border-bottom:1px solid #1e2530;display:flex;gap:14px;align-items:baseline}}
 figcaption span{{text-transform:none;letter-spacing:0;color:#5f6e80;font-size:12px}}
 .frame{{width:640px}} .frame svg{{width:100%;height:auto;display:block}}
</style>
<h1>PYROCENE - STAGE 2 MAP STYLES</h1>
{''.join(rows)}"""
    path = os.path.join(OUT, "gallery.html")
    open(path, "w").write(html)
    print(f"{len(mods)} styles x {len(scenes)} moments -> {path}")
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("styles", nargs="*", default=None)
    ap.add_argument("--moment", action="append")
    ap.add_argument("--real", action="store_true", help="also render moments from a played game")
    a = ap.parse_args()
    build(a.styles or STYLES, a.moment, a.real)


if __name__ == "__main__":
    main()
