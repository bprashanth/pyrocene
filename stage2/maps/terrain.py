"""Terrain: what it would look like from above.

Layered greens with texture, water with depth, relief shading from a low sun.
Lantana reads as a sickly bloom over the canopy rather than a flat colour, which
is closer to how an invasion actually looks on imagery.
"""
from __future__ import annotations
from . import base
from .geom import region_path

NAME = "terrain"
BLURB = "Naturalistic, like imagery from above."

SKY = "#080b0e"
CANOPY = "#1f3d24"
CANOPY_HI = "#2d5531"
SCRUB = "#3f5a2e"
WATER_D = "#10293d"
WATER_L = "#1d4c6b"
SAND = "#6b5c3f"
LANT = "#8f5ea8"
LANT_HOT = "#b06fc4"
FIRE = "#ff5a1f"
TRENCH = "#d8cba6"
ROOF = "#d9cfc0"
TEXT = "#cfd8d2"
DIM = "#69786f"

CSS = """
.lab{font-size:13px;letter-spacing:.22em;font-weight:700}
.pct{font-size:26px;font-weight:800;font-variant-numeric:tabular-nums}
.ttl{font-size:15px;letter-spacing:.38em;font-weight:800}
.rnd{font-size:15px;letter-spacing:.1em;font-weight:600}
.leg{font-size:14px;font-weight:600}
.note{font-size:19px;font-weight:500}
"""

DEFS = f'''
<filter id="canopyTex" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency="0.55" numOctaves="4" seed="11" result="n"/>
  <feColorMatrix in="n" type="saturate" values="0" result="g"/>
  <feComponentTransfer in="g" result="a"><feFuncA type="linear" slope="0.22"/></feComponentTransfer>
  <feComposite in="a" in2="SourceGraphic" operator="atop"/>
</filter>
<filter id="soft"><feGaussianBlur stdDeviation="7"/></filter>
<filter id="softer"><feGaussianBlur stdDeviation="16"/></filter>
<linearGradient id="wg" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="{WATER_L}"/><stop offset="1" stop-color="{WATER_D}"/>
</linearGradient>
<radialGradient id="fg"><stop offset="0" stop-color="#fff3c4"/>
  <stop offset=".45" stop-color="{FIRE}"/><stop offset="1" stop-color="#8c1d05" stop-opacity=".1"/>
</radialGradient>
'''


def render(scene) -> str:
    x0, y0, u = base.board_box(scene)
    p = lambda c, r=0.42: region_path(c, scene.cols, scene.rows, u, r, x0, y0)
    op = 0.3 if scene.haze else 1.0
    b = [f'<defs>{DEFS}</defs>']
    b.append(f'<rect x="{x0}" y="{y0}" width="{u*scene.cols}" height="{u*scene.rows}" fill="{CANOPY}"/>')
    b.append(f'<g opacity="{op}">')
    # canopy variation: hills catch the light, low ground is darker
    if scene.hill:
        b.append(f'<path d="{p(scene.hill, 0.46)}" fill="{CANOPY_HI}" filter="url(#soft)" fill-rule="evenodd"/>')
        b.append(f'<path d="{p(scene.hill, 0.46)}" fill="none" stroke="#0a1a0e" stroke-width="{u*0.18:.1f}" '
                 f'filter="url(#soft)" opacity=".5" transform="translate({u*0.18:.1f},{u*0.22:.1f})" fill-rule="evenodd"/>')
    b.append(f'<path d="{p(scene.of("bare"), 0.4)}" fill="{SAND}" fill-rule="evenodd"/>')
    b.append(f'<path d="{p(scene.of("water"), 0.46)}" fill="url(#wg)" fill-rule="evenodd"/>')
    b.append(f'<path d="{p(scene.of("water"), 0.46)}" fill="none" stroke="#3e7ea3" stroke-width="1.6" '
             f'opacity=".7" fill-rule="evenodd"/>')
    b.append(f'<rect x="{x0}" y="{y0}" width="{u*scene.cols}" height="{u*scene.rows}" '
             f'fill="{CANOPY}" filter="url(#canopyTex)" opacity=".55"/>')
    b.append("</g>")

    lant = scene.of("lantana")
    if lant:
        o = 1.0 if not scene.haze else 0.4
        thick = {i for i in lant if scene.stage.get(i, 1) >= 3}
        b.append(f'<g opacity="{o}">')
        b.append(f'<path d="{p(lant, 0.46)}" fill="{LANT}" filter="url(#soft)" opacity=".85" fill-rule="evenodd"/>')
        b.append(f'<path d="{p(lant, 0.44)}" fill="{LANT}" fill-rule="evenodd"/>')
        if thick:
            b.append(f'<path d="{p(thick, 0.42)}" fill="{LANT_HOT}" fill-rule="evenodd"/>')
        b.append(f'<path d="{p(lant, 0.44)}" fill="{CANOPY}" filter="url(#canopyTex)" opacity=".3" fill-rule="evenodd"/>')
        b.append("</g>")
    if scene.halo:
        b.append(f'<path d="{p(scene.halo, 0.46)}" fill="{LANT}" opacity=".28" filter="url(#soft)" fill-rule="evenodd"/>')

    for i in scene.of("village"):
        r, c = scene.rc(i)
        cx, cy = x0 + (c + 0.5) * u, y0 + (r + 0.5) * u
        for dx, dy, s in ((-0.2, -0.1, 0.2), (0.14, -0.18, 0.16), (0.02, 0.16, 0.18), (0.26, 0.1, 0.14)):
            b.append(f'<rect x="{cx+dx*u:.1f}" y="{cy+dy*u:.1f}" width="{s*u:.1f}" '
                     f'height="{s*u*0.8:.1f}" fill="{ROOF}" opacity=".95"/>')
    if scene.fireline:
        b.append(f'<path d="{p(scene.fireline, 0.36)}" fill="{TRENCH}" fill-rule="evenodd"/>')
        b.append(f'<path d="{p(scene.fireline, 0.36)}" fill="none" stroke="#8d7f5e" stroke-width="1.6" fill-rule="evenodd"/>')
    if scene.fire:
        b.append(f'<path d="{p(scene.fire, 0.44)}" fill="url(#fg)" filter="url(#softer)" fill-rule="evenodd"/>')
        b.append(f'<path d="{p(scene.fire, 0.4)}" fill="{FIRE}" fill-rule="evenodd"/>')
        b.append(f'<path d="{p(scene.fire, 0.36)}" fill="#ffd06a" opacity=".55" fill-rule="evenodd"/>')
    if scene.held:
        b.append(f'<path d="{p(scene.held, 0.34)}" fill="none" stroke="#ffffff" '
                 f'stroke-width="{max(4, u*0.22):.1f}" fill-rule="evenodd">'
                 f'<animate attributeName="opacity" values="1;.35;1" dur=".9s" repeatCount="indefinite"/></path>')
    if scene.focus:
        b.append(f'<path d="{p(scene.focus, 0.44)}" fill="none" stroke="#fff" stroke-width="3" fill-rule="evenodd"/>')

    head = (f'<text x="{base.PAD}" y="62" class="ttl" fill="#bfe0c4">P Y R O C E N E</text>'
            f'<text x="{base.PAD}" y="92" class="rnd" fill="{DIM}">NIGHT {scene.round} OF {scene.max_rounds}</text>')
    bar = base.health_bar(base.W - base.PAD - 340, 52, 250, scene.health,
                          DIM, "#4fb069", "#d2a531", "#ff5a1f", "#152119")
    leg = base.legend(base.PAD, base.H - 86, [
        (f'<rect width="20" height="20" rx="4" fill="{CANOPY_HI}"/>', "forest"),
        (f'<rect width="20" height="20" rx="4" fill="{LANT}"/>', "lantana"),
        (f'<rect width="20" height="20" rx="4" fill="{FIRE}"/>', "fire"),
        (f'<rect width="20" height="20" rx="4" fill="{TRENCH}"/>', "fire line"),
        (f'<rect width="20" height="20" rx="4" fill="{ROOF}"/>', "homes"),
    ], TEXT, gap=175)
    note = (f'<text x="{base.PAD}" y="{base.H-34}" class="note" fill="{TEXT}">{base.esc(scene.note)}</text>'
            if scene.note else "")
    return base.shell("".join(b) + head + bar + leg + note, CSS, SKY)
