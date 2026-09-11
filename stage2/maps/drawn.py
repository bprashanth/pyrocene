"""Drawn: a field sketch.

Paper, ink and hatching. The wobble comes from a turbulence filter rather than
from random numbers, so the same board always draws the same way and nothing
jitters between frames of an animation.
"""
from __future__ import annotations
from . import base
from .geom import region_path

NAME = "drawn"
BLURB = "Hand-drawn field sketch. Ink and hatching on paper."

PAPER = "#efe7d6"
PAPER_2 = "#e5dbc6"
INK = "#2b2a26"
FOREST = "#7d9b6a"
WATER = "#8fb2c4"
BARE = "#d8c8a8"
LANTANA = "#8d3f7a"
FIRE = "#d4442a"
TRENCH = "#1d5f86"
DIM = "#8a8272"

CSS = """
.lab{font-size:13px;letter-spacing:.22em;font-weight:700}
.pct{font-size:26px;font-weight:800;font-variant-numeric:tabular-nums}
.ttl{font-size:16px;letter-spacing:.36em;font-weight:800}
.rnd{font-size:15px;letter-spacing:.1em;font-weight:600}
.leg{font-size:14px;font-weight:600}
.note{font-size:20px;font-weight:500;font-style:italic}
"""

DEFS = '''
<filter id="rough" x="-6%" y="-6%" width="112%" height="112%">
  <feTurbulence type="fractalNoise" baseFrequency="0.028" numOctaves="3" seed="7" result="n"/>
  <feDisplacementMap in="SourceGraphic" in2="n" scale="7" xChannelSelector="R" yChannelSelector="G"/>
</filter>
<filter id="rougher" x="-8%" y="-8%" width="116%" height="116%">
  <feTurbulence type="fractalNoise" baseFrequency="0.05" numOctaves="3" seed="19" result="n"/>
  <feDisplacementMap in="SourceGraphic" in2="n" scale="11" xChannelSelector="R" yChannelSelector="G"/>
</filter>
<filter id="grain">
  <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="4" seed="3"/>
  <feColorMatrix type="saturate" values="0"/>
  <feComponentTransfer><feFuncA type="linear" slope="0.08"/></feComponentTransfer>
</filter>
<pattern id="hatchL" width="9" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
  <rect width="9" height="9" fill="#a85c94"/>
  <line x1="0" y1="0" x2="0" y2="9" stroke="#6d2a5d" stroke-width="3.2"/>
</pattern>
<pattern id="hatchH" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(-30)">
  <line x1="0" y1="0" x2="0" y2="10" stroke="#5f7a50" stroke-width="1" opacity=".55"/>
</pattern>
<pattern id="hatchF" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(30)">
  <rect width="7" height="7" fill="#e35a2c"/>
  <line x1="0" y1="0" x2="0" y2="7" stroke="#9c1f10" stroke-width="2.6"/>
</pattern>
'''


def render(scene) -> str:
    x0, y0, u = base.board_box(scene)
    p = lambda c, r=0.34: region_path(c, scene.cols, scene.rows, u, r, x0, y0)
    op = 0.3 if scene.haze else 1.0
    b = [f'<defs>{DEFS}</defs>']
    b.append(f'<rect x="{x0-10}" y="{y0-10}" width="{u*scene.cols+20}" height="{u*scene.rows+20}" '
             f'fill="{PAPER_2}" filter="url(#rough)"/>')
    b.append(f'<g opacity="{op}">')
    b.append(f'<path d="{p(scene.land, 0.4)}" fill="{FOREST}" filter="url(#rough)" fill-rule="evenodd"/>')
    if scene.hill:
        b.append(f'<path d="{p(scene.hill, 0.42)}" fill="url(#hatchH)" filter="url(#rough)" fill-rule="evenodd"/>')
    b.append(f'<path d="{p(scene.of("water"), 0.44)}" fill="{WATER}" filter="url(#rough)" fill-rule="evenodd"/>')
    b.append(f'<path d="{p(scene.of("water"), 0.44)}" fill="none" stroke="{INK}" stroke-width="1.6" '
             f'filter="url(#rough)" opacity=".5" fill-rule="evenodd"/>')
    b.append(f'<path d="{p(scene.of("bare"), 0.34)}" fill="{BARE}" filter="url(#rough)" fill-rule="evenodd"/>')
    b.append("</g>")

    lant = scene.of("lantana")
    if lant:
        keep = scene.focus | scene.halo
        o = 1.0 if not scene.haze else 0.35
        b.append(f'<g opacity="{o}">')
        b.append(f'<path d="{p(lant, 0.36)}" fill="url(#hatchL)" filter="url(#rougher)" fill-rule="evenodd"/>')
        b.append(f'<path d="{p(lant, 0.36)}" fill="none" stroke="{LANTANA}" stroke-width="2.4" '
                 f'filter="url(#rougher)" fill-rule="evenodd"/>')
        b.append("</g>")
    if scene.halo:
        b.append(f'<path d="{p(scene.halo, 0.4)}" fill="none" stroke="{LANTANA}" stroke-width="2.2" '
                 f'stroke-dasharray="7 6" filter="url(#rough)" opacity=".9" fill-rule="evenodd"/>')

    for i in scene.of("village"):
        r, c = scene.rc(i)
        cx, cy = x0 + (c + 0.5) * u, y0 + (r + 0.5) * u
        b.append(f'<g filter="url(#rough)"><rect x="{cx-u*0.22:.1f}" y="{cy-u*0.16:.1f}" '
                 f'width="{u*0.44:.1f}" height="{u*0.32:.1f}" fill="{PAPER}" stroke="{INK}" stroke-width="2"/>'
                 f'<path d="M{cx-u*0.28:.1f},{cy-u*0.16:.1f} L{cx:.1f},{cy-u*0.4:.1f} '
                 f'L{cx+u*0.28:.1f},{cy-u*0.16:.1f}" fill="{PAPER}" stroke="{INK}" stroke-width="2"/></g>')

    if scene.fireline:
        b.append(f'<path d="{p(scene.fireline, 0.3)}" fill="{PAPER}" filter="url(#rough)" fill-rule="evenodd"/>')
        b.append(f'<path d="{p(scene.fireline, 0.3)}" fill="none" stroke="{TRENCH}" '
                 f'stroke-width="{max(3, u*0.16):.1f}" stroke-dasharray="{u*0.28:.0f} {u*0.16:.0f}" '
                 f'filter="url(#rough)" fill-rule="evenodd"/>')
    if scene.fire:
        b.append(f'<path d="{p(scene.fire, 0.34)}" fill="url(#hatchF)" filter="url(#rougher)" fill-rule="evenodd"/>')
        b.append(f'<path d="{p(scene.fire, 0.34)}" fill="none" stroke="#8c1a0c" stroke-width="2.6" '
                 f'filter="url(#rougher)" fill-rule="evenodd"/>')
    if scene.held:
        b.append(f'<path d="{p(scene.held, 0.3)}" fill="none" stroke="{TRENCH}" '
                 f'stroke-width="{max(5, u*0.26):.1f}" filter="url(#rough)" fill-rule="evenodd">'
                 f'<animate attributeName="opacity" values="1;.3;1" dur=".9s" repeatCount="indefinite"/></path>')
    if scene.focus:
        b.append(f'<path d="{p(scene.focus, 0.4)}" fill="none" stroke="{INK}" stroke-width="3.4" '
                 f'filter="url(#rough)" fill-rule="evenodd"/>')
    b.append(f'<rect x="0" y="0" width="{base.W}" height="{base.H}" filter="url(#grain)" '
             f'opacity=".5" pointer-events="none"/>')

    head = (f'<text x="{base.PAD}" y="62" class="ttl" fill="{INK}">P Y R O C E N E</text>'
            f'<text x="{base.PAD}" y="92" class="rnd" fill="{DIM}">NIGHT {scene.round} OF {scene.max_rounds}</text>')
    bar = base.health_bar(base.W - base.PAD - 340, 52, 250, scene.health,
                          DIM, "#4f7a3f", "#b8862a", FIRE, "#d8ceba")
    leg = base.legend(base.PAD, base.H - 86, [
        (f'<rect width="20" height="20" fill="{FOREST}"/>', "forest"),
        (f'<rect width="20" height="20" fill="url(#hatchL)"/>', "lantana"),
        (f'<rect width="20" height="20" fill="url(#hatchF)"/>', "fire"),
        (f'<line x1="0" y1="10" x2="20" y2="10" stroke="{TRENCH}" stroke-width="5" stroke-dasharray="5 4"/>', "fire line"),
        (f'<rect width="20" height="20" fill="{WATER}"/>', "water"),
    ], INK, gap=180)
    note = (f'<text x="{base.PAD}" y="{base.H-34}" class="note" fill="{INK}">{base.esc(scene.note)}</text>'
            if scene.note else "")
    return base.shell("".join(b) + head + bar + leg + note, CSS, PAPER)
