"""Turning a grid of cells into shapes that read as a map rather than a chart.

The board is 22 by 12 squares. Drawn as squares it looks like a spreadsheet. The
work here dissolves the grid: take the set of cells with one cover, trace the
outline of the region they form, and round the corners. What comes back is a
coastline, a stand of forest, a patch of weed.
"""
from __future__ import annotations


def outlines(cells, cols: int, rows: int) -> list:
    """Trace the boundary loops of a set of cell indices, in grid units.

    Every cell contributes four edges; edges shared by two cells in the set
    cancel. What survives is the boundary, which we then chain into closed
    loops. Returns a list of loops, each a list of (x, y) corner points.
    """
    inside = set(cells)
    edges: dict = {}
    for i in inside:
        r, c = divmod(i, cols)
        # clockwise so exterior rings wind the same way
        for a, b in (((c, r), (c + 1, r)),
                     ((c + 1, r), (c + 1, r + 1)),
                     ((c + 1, r + 1), (c, r + 1)),
                     ((c, r + 1), (c, r))):
            if (b, a) in edges:
                del edges[(b, a)]       # shared with a neighbour: interior
            else:
                edges[(a, b)] = True

    starts: dict = {}
    for a, b in edges:
        starts.setdefault(a, []).append(b)

    loops = []
    while starts:
        a = next(iter(starts))
        loop = [a]
        while True:
            nxt = starts.get(a)
            if not nxt:
                break
            b = nxt.pop()
            if not nxt:
                del starts[a]
            loop.append(b)
            a = b
            if a == loop[0]:
                break
        if len(loop) > 3:
            loops.append(loop[:-1] if loop[0] == loop[-1] else loop)
    return loops


def simplify(loop: list) -> list:
    """Drop points that sit in the middle of a straight run."""
    if len(loop) < 3:
        return loop
    out = []
    n = len(loop)
    for k in range(n):
        p, q, r = loop[k - 1], loop[k], loop[(k + 1) % n]
        if (q[0] - p[0]) * (r[1] - q[1]) != (q[1] - p[1]) * (r[0] - q[0]):
            out.append(q)
    return out or loop


def rounded_path(loop: list, unit: float, radius: float = 0.28,
                 ox: float = 0.0, oy: float = 0.0) -> str:
    """An SVG path for one loop with its corners rounded.

    radius is in cell units. At 0 this is the raw staircase; at 0.5 the shape
    goes fully blobby and a single cell becomes a circle.
    """
    pts = simplify(loop)
    n = len(pts)
    if n < 3:
        return ""
    out = []
    for k in range(n):
        prev, cur, nxt = pts[k - 1], pts[k], pts[(k + 1) % n]

        def cut(a, b, frac):
            dx, dy = b[0] - a[0], b[1] - a[1]
            length = (dx * dx + dy * dy) ** 0.5 or 1.0
            f = min(frac, length / 2) / length
            return (a[0] + dx * f, a[1] + dy * f)

        a = cut(cur, prev, radius)
        b = cut(cur, nxt, radius)
        px = lambda p: (ox + p[0] * unit, oy + p[1] * unit)
        ax, ay = px(a)
        cx, cy = px(cur)
        bx, by = px(b)
        if k == 0:
            out.append(f"M{ax:.1f},{ay:.1f}")
        else:
            out.append(f"L{ax:.1f},{ay:.1f}")
        out.append(f"Q{cx:.1f},{cy:.1f} {bx:.1f},{by:.1f}")
    out.append("Z")
    return "".join(out)


def region_path(cells, cols: int, rows: int, unit: float,
                radius: float = 0.28, ox: float = 0.0, oy: float = 0.0) -> str:
    """One SVG path covering every cell in `cells`, corners rounded.

    Holes come out with the opposite winding, so fill-rule evenodd cuts them.
    """
    return " ".join(rounded_path(lp, unit, radius, ox, oy)
                    for lp in outlines(cells, cols, rows))


def edge_segments(cells, cols: int, rows: int):
    """The boundary of a region as individual segments in grid units, for
    drawing a shoreline or a hatched edge without filling anything."""
    out = []
    for lp in outlines(cells, cols, rows):
        for k in range(len(lp)):
            out.append((lp[k], lp[(k + 1) % len(lp)]))
    return out


def neighbours4(i: int, cols: int, rows: int):
    r, c = divmod(i, cols)
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        rr, cc = r + dr, c + dc
        if 0 <= rr < rows and 0 <= cc < cols:
            yield rr * cols + cc


def distance_field(seeds, blocked, cols: int, rows: int, limit: int = 6) -> dict:
    """How many steps each cell is from the nearest seed. Used for heat maps and
    for the soft glow around a stand of weed."""
    from collections import deque
    dist = {i: 0 for i in seeds}
    q = deque(seeds)
    while q:
        i = q.popleft()
        if dist[i] >= limit:
            continue
        for n in neighbours4(i, cols, rows):
            if n in dist or n in blocked:
                continue
            dist[n] = dist[i] + 1
            q.append(n)
    return dist
