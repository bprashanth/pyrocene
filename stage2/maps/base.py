"""Bits every SVG style wants: the frame, the health bar, a legend, a title."""
from __future__ import annotations

W, H = 1280, 760            # projector canvas
PAD = 48


def board_box(scene, top=132, bottom=150):
    """Where the map sits, and how big one cell is, keeping squares square."""
    avail_w = W - PAD * 2
    avail_h = H - top - bottom
    unit = min(avail_w / scene.cols, avail_h / scene.rows)
    bw, bh = unit * scene.cols, unit * scene.rows
    return (W - bw) / 2, top + (avail_h - bh) / 2, unit


def esc(t: str) -> str:
    return (t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def health_bar(x, y, w, pct, ink, good, warn, bad, track, label="FOREST"):
    col = good if pct >= 60 else warn if pct >= 40 else bad
    fill = w * max(0, min(100, pct)) / 100
    return f'''
  <text x="{x}" y="{y - 14}" class="lab" fill="{ink}">{label}</text>
  <rect x="{x}" y="{y}" width="{w}" height="14" rx="7" fill="{track}"/>
  <rect x="{x}" y="{y}" width="{fill:.1f}" height="14" rx="7" fill="{col}"/>
  <text x="{x + w + 18}" y="{y + 13}" class="pct" fill="{col}">{pct}%</text>'''


def legend(x, y, items, ink, gap=196):
    """items: list of (swatch_svg_fn, label). Each swatch draws at 0,0 in a
    20x20 box; we translate it into place."""
    out = []
    for k, (swatch, label) in enumerate(items):
        tx = x + k * gap
        out.append(f'<g transform="translate({tx},{y})">{swatch}'
                   f'<text x="30" y="15" class="leg" fill="{ink}">{label}</text></g>')
    return "".join(out)


def shell(body: str, css: str, bg: str, w=W, h=H) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'width="{w}" height="{h}" font-family="Inter, Helvetica Neue, Arial, sans-serif">'
            f'<style>{css}</style><rect width="{w}" height="{h}" fill="{bg}"/>{body}</svg>')
