"""Poster: flat vector cartography on a dark ground.

The grammar borrows from printed city maps. One dark field, one striking colour
for the thing that matters, thin bright lines for the network. Here the striking
colour is lantana, because lantana is what the room is looking for, and it
escalates into fire: gold is fuel, red is fuel that caught.
"""
from __future__ import annotations
from . import base
from .geom import region_path, outlines, rounded_path

NAME = "poster"
BLURB = "Flat vector. Gold is fuel, red is fuel that caught."

INK = "#0f1620"          # the ground
FOREST = "#16281f"       # calm, recessive, the thing we are protecting
FOREST_EDGE = "#1f3a2c"
WATER = "#1d3a52"
WATER_LINE = "#2f5f82"
WATER_EDGE = "#24354a"
BARE = "#3a3730"
LANTANA = "#f0a92b"      # the figure
LANTANA_DEEP = "#c9781a"
FIRE = "#f4402e"
TRENCH = "#4fd6ff"
VILLAGE = "#f4ede0"
TEXT = "#cfd8e3"
DIM = "#5a6675"

CSS = """
.lab{font-size:13px;letter-spacing:.22em;font-weight:700}
.pct{font-size:26px;font-weight:800;font-variant-numeric:tabular-nums}
.ttl{font-size:15px;letter-spacing:.38em;font-weight:800}
.rnd{font-size:15px;letter-spacing:.1em;font-weight:600}
.leg{font-size:14px;font-weight:600}
.note{font-size:19px;font-weight:500}
"""


def render(scene) -> str:
    x0, y0, u = base.board_box(scene)
    p = lambda cells, rad=0.3: region_path(cells, scene.cols, scene.rows, u, rad, x0, y0)
    hazed = scene.haze
    keep = scene.focus | scene.halo

    def mute(colour, amount=0.82):
        """Pull a colour toward the ground while the projector holds on a few
        squares, so the eye goes where it is meant to."""
        if not hazed:
            return colour
        c = colour.lstrip("#")
        r, g, b = (int(c[k:k + 2], 16) for k in (0, 2, 4))
        gr, gg, gb = 0x0f, 0x16, 0x20
        f = amount
        return "#%02x%02x%02x" % (int(r + (gr - r) * f), int(g + (gg - g) * f),
                                  int(b + (gb - b) * f))

    body = [f'<rect x="{x0}" y="{y0}" width="{u*scene.cols}" height="{u*scene.rows}" fill="{mute(INK,0.5)}"/>']

    # --- land masses -------------------------------------------------------
    body.append(f'<path d="{p(scene.land, 0.34)}" fill="{mute(FOREST)}" fill-rule="evenodd"/>')
    body.append(f'<path d="{p(scene.of("water"), 0.38)}" fill="{mute(WATER)}" fill-rule="evenodd"/>')
    body.append(f'<path d="{p(scene.of("bare"), 0.3)}" fill="{mute(BARE)}" fill-rule="evenodd"/>')

    # A shoreline, so water reads as water. It is also a fire break, which is
    # exactly the kind of thing the room should be able to see without asking.
    water = scene.of("water")
    if water:
        body.append(f'<path d="{p(water, 0.42)}" fill="none" stroke="{mute(WATER_LINE)}" '
                    f'stroke-width="2" opacity=".9" fill-rule="evenodd"/>')

    # Relief as slope hatching inside the hill regions, not an outline. An
    # outline read as a random rounded box floating on the forest.
    if scene.hill:
        body.append(f'<g opacity="{0.10 if hazed else 0.30}">')
        body.append(f'<clipPath id="hills"><path d="{p(scene.hill, 0.4)}" fill-rule="evenodd"/></clipPath>')
        body.append('<g clip-path="url(#hills)">')
        step = max(7, u * 0.34)
        k = -int(scene.rows * u)
        while k < scene.cols * u:
            body.append(f'<line x1="{x0+k:.0f}" y1="{y0:.0f}" x2="{x0+k+scene.rows*u:.0f}" '
                        f'y2="{y0+scene.rows*u:.0f}" stroke="#7fb08a" stroke-width="1.1"/>')
            k += step
        body.append("</g></g>")

    # Tracks: one continuous polyline per run, so the network reads as lines.
    for run in _runs(scene.road, scene):
        pts = " ".join(f"{x0+(c+0.5)*u:.1f},{y0+(r+0.5)*u:.1f}" for r, c in run)
        body.append(f'<polyline points="{pts}" fill="none" stroke="{mute("#9a4b42")}" '
                    f'stroke-width="{max(1.6, u*0.08):.1f}" stroke-linecap="round" '
                    f'stroke-linejoin="round" opacity=".75"/>')

    # --- lantana, the figure ----------------------------------------------
    lant = scene.of("lantana")
    if lant:
        thick = {i for i in lant if scene.stage.get(i, 1) >= 3}
        body.append(f'<path d="{p(lant, 0.32)}" fill="{mute(LANTANA)}" fill-rule="evenodd"/>')
        if thick:
            body.append(f'<path d="{p(thick, 0.3)}" fill="{mute(LANTANA_DEEP)}" fill-rule="evenodd"/>')
        body.append(f'<path d="{p(lant, 0.32)}" fill="none" stroke="{mute("#ffd77a")}" '
                    f'stroke-width="1.6" opacity=".55" fill-rule="evenodd"/>')

    # ground it is pressing on
    if scene.halo:
        body.append(f'<path d="{p(scene.halo, 0.36)}" fill="none" stroke="{LANTANA}" '
                    f'stroke-width="2" stroke-dasharray="5 5" opacity=".85" fill-rule="evenodd"/>')

    # --- people ------------------------------------------------------------
    # Homes: a bright block with a ring of clear ground, so they sit on the map
    # as a place rather than a floating chip.
    for i in scene.of("village"):
        r, c = scene.rc(i)
        cx, cy = x0 + (c + 0.5) * u, y0 + (r + 0.5) * u
        body.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{u*0.52:.1f}" '
                    f'fill="{mute(INK, 0.25)}" opacity=".85"/>')
        body.append(f'<rect x="{cx-u*0.2:.1f}" y="{cy-u*0.2:.1f}" width="{u*0.4:.1f}" '
                    f'height="{u*0.4:.1f}" fill="{mute(VILLAGE)}"/>')
        body.append(f'<rect x="{cx-u*0.34:.1f}" y="{cy-u*0.34:.1f}" width="{u*0.68:.1f}" '
                    f'height="{u*0.68:.1f}" fill="none" stroke="{mute(VILLAGE)}" '
                    f'stroke-width="1.4" opacity=".55"/>')

    if scene.fireline:
        body.append(f'<path d="{p(scene.fireline, 0.3)}" fill="{mute(INK,0.3)}" fill-rule="evenodd"/>')
        body.append(f'<path d="{p(scene.fireline, 0.3)}" fill="none" stroke="{mute(TRENCH)}" '
                    f'stroke-width="{max(2.4, u*0.13):.1f}" stroke-dasharray="{u*0.3:.0f} {u*0.2:.0f}" '
                    f'fill-rule="evenodd"/>')

    # --- fire --------------------------------------------------------------
    if scene.fire:
        body.append(f'<path d="{p(scene.fire, 0.3)}" fill="{FIRE}" fill-rule="evenodd"/>')
        body.append(f'<path d="{p(scene.fire, 0.3)}" fill="none" stroke="#ffd27a" '
                    f'stroke-width="2.4" opacity=".9" fill-rule="evenodd"/>')
    if scene.held:
        body.append(f'<path d="{p(scene.held, 0.3)}" fill="none" stroke="{TRENCH}" '
                    f'stroke-width="{max(3.5, u*0.2):.1f}" fill-rule="evenodd">'
                    f'<animate attributeName="opacity" values="1;.25;1" dur="0.9s" repeatCount="indefinite"/></path>')

    # --- what to look at ---------------------------------------------------
    if scene.focus:
        d = p(scene.focus, 0.34)
        body.append(f'<path d="{d}" fill="none" stroke="#ffffff" stroke-width="3" '
                    f'opacity=".95" fill-rule="evenodd"/>')
        body.append(f'<path d="{d}" fill="none" stroke="#ffffff" stroke-width="10" '
                    f'opacity=".18" fill-rule="evenodd"/>')

    # --- chrome ------------------------------------------------------------
    head = (f'<text x="{base.PAD}" y="62" class="ttl" fill="{LANTANA}">P Y R O C E N E</text>'
            f'<text x="{base.PAD}" y="92" class="rnd" fill="{DIM}">'
            f'NIGHT {scene.round} OF {scene.max_rounds}</text>')
    bar = base.health_bar(base.W - base.PAD - 340, 52, 250, scene.health,
                          DIM, "#39c07a", LANTANA, FIRE, "#1c2531")
    sw = lambda fill, extra="": f'<rect width="20" height="20" rx="5" fill="{fill}"{extra}/>'
    leg = base.legend(base.PAD, base.H - 86, [
        (sw(FOREST) + f'<rect width="20" height="20" rx="5" fill="none" stroke="{FOREST_EDGE}"/>', "forest"),
        (sw(LANTANA), "lantana"),
        (sw(LANTANA_DEEP), "thick lantana"),
        (sw(FIRE), "fire"),
        (f'<rect width="20" height="20" rx="5" fill="none" stroke="{TRENCH}" stroke-width="3" stroke-dasharray="5 4"/>', "fire line"),
        (sw(VILLAGE), "homes"),
    ], TEXT, gap=170)
    note = (f'<text x="{base.PAD}" y="{base.H - 34}" class="note" fill="{TEXT}">'
            f'{base.esc(scene.note)}</text>' if scene.note else "")
    return base.shell("".join(body) + head + bar + leg + note, CSS, INK)


def _runs(cells, scene):
    """Chain road cells into connected paths so they draw as one line each."""
    left = set(cells)
    runs = []
    while left:
        i = min(left)
        run = [i]
        left.discard(i)
        # walk forward from either end while a neighbour is still unused
        for end in (0, 1):
            while True:
                cur = run[-1] if end else run[0]
                r, c = scene.rc(cur)
                nxt = None
                for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1), (0, -1), (-1, 0)):
                    rr, cc = r + dr, c + dc
                    j = rr * scene.cols + cc
                    if 0 <= rr < scene.rows and 0 <= cc < scene.cols and j in left:
                        nxt = j
                        break
                if nxt is None:
                    break
                left.discard(nxt)
                run.append(nxt) if end else run.insert(0, nxt)
        runs.append([scene.rc(j) for j in run])
    return runs
