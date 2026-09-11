"""Drawn: a field map, inked on paper.

The one that reads fastest in a room. Green ground, a hatched weed you can pick
out at a glance, little houses you do not need a legend to understand. The
wobble is a turbulence filter rather than random numbers, so the same board
always draws the same way and nothing jitters between frames of an animation.
"""
from __future__ import annotations
from . import base
from .geom import region_path, coast

NAME = "drawn"
BLURB = "Ink and hatching on paper. The one a room reads fastest."

PAPER = "#f2ebda"
PAPER_2 = "#e7dcc4"
EDGE = "#d3c6a8"
INK = "#2a2823"
FOREST = "#7d9b6a"
FOREST_HI = "#8dab78"
WATER = "#93b6cb"
WATER_INK = "#4d7a95"
BARE = "#d9c9a6"
LANT_INK = "#6d2a5d"
FIRE_INK = "#9c1f10"
TRENCH = "#1f5f88"
DUG = "#efe6d2"
ROOF = "#fbf6ea"
DIM = "#8b8371"
GOOD = "#4f7a3f"

CSS = """
.ttl{font-size:17px;letter-spacing:.34em;font-weight:800}
.deck{font-size:14px;letter-spacing:.02em;font-weight:500}
.lab{font-size:11px;letter-spacing:.22em;font-weight:700}
.pct{font-size:30px;font-weight:800;font-variant-numeric:tabular-nums}
.leg{font-size:13.5px;font-weight:600}
.note{font-size:21px;font-weight:500}
.src{font-size:12px;font-weight:500;letter-spacing:.04em}
"""

DEFS = '''
<filter id="rough" x="-6%" y="-6%" width="112%" height="112%">
  <feTurbulence type="fractalNoise" baseFrequency="0.022" numOctaves="3" seed="7" result="n"/>
  <feDisplacementMap in="SourceGraphic" in2="n" scale="5" xChannelSelector="R" yChannelSelector="G"/>
</filter>
<filter id="rougher" x="-8%" y="-8%" width="116%" height="116%">
  <feTurbulence type="fractalNoise" baseFrequency="0.04" numOctaves="3" seed="19" result="n"/>
  <feDisplacementMap in="SourceGraphic" in2="n" scale="8" xChannelSelector="R" yChannelSelector="G"/>
</filter>
<filter id="grain">
  <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="4" seed="3"/>
  <feColorMatrix type="saturate" values="0"/>
  <feComponentTransfer><feFuncA type="linear" slope="0.075"/></feComponentTransfer>
</filter>
<pattern id="lant" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
  <rect width="10" height="10" fill="#b06a9c"/>
  <line x1="0" y1="0" x2="0" y2="10" stroke="#6d2a5d" stroke-width="2.6"/>
</pattern>
<pattern id="lantT" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
  <rect width="6" height="6" fill="#8d3f7a"/>
  <line x1="0" y1="0" x2="0" y2="6" stroke="#4a1740" stroke-width="3"/>
</pattern>
<pattern id="fire" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(30)">
  <rect width="7" height="7" fill="#e8622e"/>
  <line x1="0" y1="0" x2="0" y2="7" stroke="#9c1f10" stroke-width="2.4"/>
</pattern>
<pattern id="relief" width="9" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(-35)">
  <line x1="0" y1="0" x2="0" y2="9" stroke="#5f7a50" stroke-width="1" opacity=".6"/>
</pattern>
'''


def render(scene) -> str:
    x0, y0, u = base.board_box(scene, top=128, bottom=140)
    W, Hh = u * scene.cols, u * scene.rows
    hazed = scene.haze

    def nat(cells, wobble=0.16, seed=11, scale=4):
        return coast(cells, scene.cols, scene.rows, u, scale, wobble, x0, y0, seed)

    def cut(cells, rad=0.18):
        return region_path(cells, scene.cols, scene.rows, u, rad, x0, y0)

    B = [f"<defs>{DEFS}</defs>"]
    # the sheet the map is printed on
    B.append(f'<rect x="{x0-9}" y="{y0-9}" width="{W+18}" height="{Hh+18}" fill="{EDGE}" filter="url(#rough)"/>')
    B.append(f'<clipPath id="bd"><rect x="{x0}" y="{y0}" width="{W}" height="{Hh}"/></clipPath>')
    B.append('<g clip-path="url(#bd)">')
    B.append(f'<rect x="{x0}" y="{y0}" width="{W}" height="{Hh}" fill="{FOREST}"/>')

    ghost = 0.42 if hazed else 1.0
    B.append(f'<g opacity="{ghost}">')
    if scene.hill:
        d = nat(scene.hill, 0.18, 53)
        B.append(f'<path d="{d}" fill="{FOREST_HI}" filter="url(#rough)" fill-rule="evenodd"/>')
        B.append(f'<path d="{d}" fill="url(#relief)" filter="url(#rough)" fill-rule="evenodd"/>')
    bare = scene.of("bare")
    if bare:
        B.append(f'<path d="{nat(bare, 0.18, 41)}" fill="{BARE}" filter="url(#rough)" fill-rule="evenodd"/>')
    water = scene.of("water")
    if water:
        d = nat(water, 0.12, 29)
        B.append(f'<path d="{d}" fill="{WATER}" filter="url(#rough)" fill-rule="evenodd"/>')
        B.append(f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="1.4" opacity=".34" '
                 f'filter="url(#rough)" fill-rule="evenodd"/>')
    for run in _runs(scene.road, scene):
        pts = " ".join(f"{x0+(c+0.5)*u:.1f},{y0+(r+0.5)*u:.1f}" for r, c in run)
        B.append(f'<polyline points="{pts}" fill="none" stroke="{INK}" stroke-width="1.5" '
                 f'stroke-dasharray="7 5" opacity=".35" filter="url(#rough)"/>')
    B.append("</g>")

    # --- lantana, hatched, thicker where it has taken hold -----------------
    lant = scene.of("lantana")
    if lant:
        keep = scene.focus | scene.halo
        o = 1.0 if not hazed else 0.42
        thick = {i for i in lant if scene.stage.get(i, 1) >= 3}
        d = nat(lant, 0.2, 67)
        B.append(f'<g opacity="{o}">')
        B.append(f'<path d="{d}" fill="url(#lant)" filter="url(#rougher)" fill-rule="evenodd"/>')
        if thick:
            B.append(f'<path d="{nat(thick, 0.22, 71)}" fill="url(#lantT)" '
                     f'filter="url(#rougher)" fill-rule="evenodd"/>')
        B.append(f'<path d="{d}" fill="none" stroke="{LANT_INK}" stroke-width="2.2" '
                 f'filter="url(#rougher)" fill-rule="evenodd"/>')
        B.append("</g>")
    if scene.halo:
        B.append(f'<path d="{nat(scene.halo, 0.18, 83)}" fill="none" stroke="{LANT_INK}" '
                 f'stroke-width="2" stroke-dasharray="7 6" opacity=".85" filter="url(#rough)" '
                 f'fill-rule="evenodd"/>')

    # --- the trench: turned earth with a dashed centre ---------------------
    if scene.fireline:
        d = cut(scene.fireline, 0.16)
        B.append(f'<path d="{d}" fill="{DUG}" filter="url(#rough)" fill-rule="evenodd"/>')
        B.append(f'<path d="{d}" fill="none" stroke="{TRENCH}" stroke-width="2.6" '
                 f'stroke-dasharray="{u*0.3:.0f} {u*0.2:.0f}" filter="url(#rough)" fill-rule="evenodd"/>')

    # --- homes --------------------------------------------------------------
    for i in scene.of("village"):
        r, c = scene.rc(i)
        cx, cy = x0 + (c + 0.5) * u, y0 + (r + 0.5) * u
        s = u * 0.30
        B.append(f'<g filter="url(#rough)">'
                 f'<rect x="{cx-s*0.55:.1f}" y="{cy-s*0.18:.1f}" width="{s*1.1:.1f}" '
                 f'height="{s*0.8:.1f}" fill="{ROOF}" stroke="{INK}" stroke-width="1.7"/>'
                 f'<path d="M{cx-s*0.72:.1f},{cy-s*0.18:.1f} L{cx:.1f},{cy-s*0.78:.1f} '
                 f'L{cx+s*0.72:.1f},{cy-s*0.18:.1f}" fill="{ROOF}" stroke="{INK}" '
                 f'stroke-width="1.7" stroke-linejoin="round"/></g>')

    # --- fire ----------------------------------------------------------------
    if scene.fire:
        d = nat(scene.fire, 0.22, 97)
        B.append(f'<path d="{d}" fill="url(#fire)" filter="url(#rougher)" fill-rule="evenodd"/>')
        B.append(f'<path d="{d}" fill="none" stroke="{FIRE_INK}" stroke-width="2.6" '
                 f'filter="url(#rougher)" fill-rule="evenodd"/>')
    if scene.held:
        d = cut(scene.held, 0.16)
        B.append(f'<path d="{d}" fill="none" stroke="{TRENCH}" stroke-width="{max(6, u*0.34):.1f}" '
                 f'stroke-linejoin="round" filter="url(#rough)" fill-rule="evenodd">'
                 f'<animate attributeName="opacity" values="1;.35;1" dur=".95s" repeatCount="indefinite"/></path>')
    if scene.focus:
        d = cut(scene.focus, 0.2)
        B.append(f'<path d="{d}" fill="{PAPER}" opacity=".35" filter="url(#rough)" fill-rule="evenodd"/>')
        B.append(f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="3.4" '
                 f'filter="url(#rough)" fill-rule="evenodd"/>')
    B.append("</g>")
    B.append(f'<rect x="0" y="0" width="{base.W}" height="{base.H}" filter="url(#grain)" opacity=".55"/>')

    # --- editorial chrome ---------------------------------------------------
    head = (f'<text x="{base.PAD}" y="52" class="ttl" fill="{INK}">P Y R O C E N E</text>'
            f'<line x1="{base.PAD}" y1="64" x2="{base.PAD+250}" y2="64" stroke="{INK}" '
            f'stroke-width="1.4" opacity=".5"/>'
            f'<text x="{base.PAD}" y="88" class="deck" fill="{DIM}">'
            f'Night {scene.round} of {scene.max_rounds}</text>')
    bar = base.health_bar(base.W - base.PAD - 330, 44, 240, scene.health,
                          DIM, GOOD, "#b8862a", FIRE_INK, "#ddd3bd")
    leg = base.legend(base.PAD, base.H - 86, [
        (f'<rect width="20" height="20" fill="{FOREST}" stroke="{INK}" stroke-width="1.2"/>', "forest"),
        (f'<rect width="20" height="20" fill="url(#lant)" stroke="{INK}" stroke-width="1.2"/>', "lantana"),
        (f'<rect width="20" height="20" fill="url(#lantT)" stroke="{INK}" stroke-width="1.2"/>', "thick lantana"),
        (f'<rect width="20" height="20" fill="url(#fire)" stroke="{INK}" stroke-width="1.2"/>', "fire"),
        (f'<rect width="20" height="20" fill="{DUG}" stroke="{TRENCH}" stroke-width="2.4" stroke-dasharray="5 4"/>', "fire line"),
        (f'<rect width="20" height="20" fill="{WATER}" stroke="{INK}" stroke-width="1.2"/>', "water"),
        (f'<path d="M1,13 L10,4 L19,13 Z M4,13 h12 v6 h-12 Z" fill="{ROOF}" stroke="{INK}" stroke-width="1.4"/>', "homes"),
    ], INK, gap=152)
    note = (f'<text x="{base.PAD}" y="{base.H-34}" class="note" fill="{INK}">'
            f'{base.esc(scene.note)}</text>' if scene.note else "")
    return base.shell("".join(B) + head + bar + leg + note, CSS, PAPER)


def _runs(cells, scene):
    left = set(cells)
    runs = []
    while left:
        i = min(left)
        run = [i]
        left.discard(i)
        for end in (1, 0):
            while True:
                cur = run[-1] if end else run[0]
                r, c = scene.rc(cur)
                nxt = None
                for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)):
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
