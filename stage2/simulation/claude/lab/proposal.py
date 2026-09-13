"""A fire-management proposal for the board: clear the worst lantana, dig a
line between what is left and what it threatens. The lower row of the lab
burns the board with this done, so the room can compare.

The rule is deliberately simple and stated on the page:
  1. clear every square of the largest connected stand of thick lantana;
  2. dig a fire line of LINE_CELLS squares along the downwind edge of the
     lantana that remains, starting nearest the ignition, so the wind pushes
     the fire onto the line rather than around it.
"""
import math
import numpy as np
import landscape as L
from landscape import NATIVE, INVASIVE, BARE

LINE_CELLS = 12

def neighbours(i, cols, rows, eight=False):
    r, c = divmod(i, cols); out = []
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if not dr and not dc: continue
            if not eight and dr and dc: continue
            rr, cc = r + dr, c + dc
            if 0 <= rr < rows and 0 <= cc < cols: out.append(rr * cols + cc)
    return out

def clusters(cells, cols, rows):
    left = set(cells); out = []
    while left:
        s = left.pop(); comp = [s]; q = [s]
        while q:
            i = q.pop()
            for n in neighbours(i, cols, rows, eight=True):
                if n in left: left.discard(n); comp.append(n); q.append(n)
        out.append(comp)
    return sorted(out, key=len, reverse=True)

def make(board, wind=None):
    wind = wind or L.WIND
    cols, rows = board["cols"], board["rows"]
    cell = {c["i"]: c for c in board["cells"]}
    thick = [i for i, c in cell.items() if c["cover"] == INVASIVE and c["stage"] == 3]
    big = clusters(thick, cols, rows)
    cleared = set(big[0]) if big else set()
    remaining = [i for i, c in cell.items() if c["cover"] == INVASIVE and i not in cleared]
    # wind blows towards this unit vector (x east, y south)
    th = math.radians(wind["from_deg"] + 180.0); wx, wy = math.sin(th), -math.cos(th)
    ign = board["ignition"]; ir, ic = divmod(ign, cols)
    # candidates: forest squares touching the lantana region (what remains and
    # what was cleared), on the downwind side of the region's centre
    region = set(remaining) | cleared
    if not region: return {"cleared": sorted(cleared), "line": []}
    gr = sum(i // cols for i in region) / len(region); gc = sum(i % cols for i in region) / len(region)
    cand = {}
    for i in region:
        for n in neighbours(i, cols, rows, eight=True):
            c = cell[n]
            if c["cover"] != NATIVE or c["fireline"] or n in region: continue
            nr, nc = divmod(n, cols)
            down = (nc - gc) * wx + (nr - gr) * wy
            if down > 0: cand[n] = down
    if not cand: return {"cleared": sorted(cleared), "line": []}
    dist = lambda n: math.hypot(n % cols - ic, n // cols - ir)
    start = min(cand, key=dist)
    line = [start]; used = {start}
    while len(line) < LINE_CELLS:
        best = None
        for end in (line[-1], line[0]):
            for n in neighbours(end, cols, rows, eight=True):
                if n in cand and n not in used and (best is None or dist(n) < dist(best[1])): best = (end, n)
        if best is None: break
        end, n = best; used.add(n)
        line.append(n) if end == line[-1] else line.insert(0, n)
    return {"cleared": sorted(cleared), "line": line}

if __name__ == "__main__":
    import json, sys
    b = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "/mnt/seagate/models/pyrocene/lab/board-sample-night5.json"))
    p = make(b); cols = b["cols"]
    print("clear", len(p["cleared"]), "squares:", sorted((i // cols, i % cols) for i in p["cleared"]))
    print("line", len(p["line"]), "squares:", [(i // cols, i % cols) for i in p["line"]])
