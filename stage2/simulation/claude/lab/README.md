# The fire lab

The board as it was when a game's biggest fire started, burned by real fire
models, side by side. An experiment in "game, then a bit of science, then the
film": if a model's picture teaches better than the game's flood, it can
drive the film's fire later. See `chronology/2026-09-13T1630-fire-lab.md`
for what was found.

## See it

```
python3 -m stage2.server
# http://localhost:8020/simulation/claude/lab/?run=sample
```

Eight panels: the game's own fire, the automaton, ForeFire and Cell2Fire,
each on the board as played and on the same board with the critical night's
joining squares cleared. One slider drives them all. The fuel table and the
assumed wind are printed under the panels.

## Run it

Needs the ForeFire venv (`/tmp/forefire_venv.rskvjS/bin/python`, or
`pip install forefire` from the wheel kept in `/mnt/seagate/models/pyrocene/lab/`)
and, for the Cell2Fire panel, the binary kept there too.

```bash
# 1. export the board just before the biggest fire from a game log
node -e '
const P=require("./stage2/simulation/claude/log.js"), fs=require("fs");
const w=P.build(JSON.parse(fs.readFileSync("stage2/simulation/sample-game.json")));
const nt=w.nights.find(n=>n.k===w.crit.major), b=w.frames[nt.frames.thicken].board, cols=w.cols;
const cells=[]; for(let i=0;i<w.n;i++) cells.push({i,r:Math.floor(i/cols),c:i%cols,cover:b.cover[i],stage:b.stage[i],seeded:b.seeded[i],burnt:b.burnt[i],fireline:b.fireline[i],hill:w.hill[i],road:w.road[i]});
const f=nt.fire; fs.writeFileSync("/mnt/seagate/models/pyrocene/lab/board.json", JSON.stringify({cols,rows:w.rows,night:nt.k,crit:{night:w.crit.night,size:w.crit.size,stand:w.crit.stand,cut:w.crit.cut,rest:w.crit.rest,sev:w.crit.sev},ignition:P.parseCell(f.ignition_cell,cols),cause:f.ignition_cause,severity:f.severity,burned:f.burned_cells.map(x=>P.parseCell(x,cols)),waves:f.waves.map(wv=>wv.map(x=>P.parseCell(x,cols))),cells}));'

# 2. run every model on both scenarios, write results/<name>.json and a contact sheet
cd stage2/simulation/claude/lab
CELL2FIRE=/mnt/seagate/models/pyrocene/lab/cell2fire/Cell2Fire \
  /tmp/forefire_venv.rskvjS/bin/python run_all.py --board /mnt/seagate/models/pyrocene/lab/board.json --name mygame
```

Then `?run=mygame` on the page.

## Files

```
landscape.py     board -> fuel and altitude rasters; the fuel table; Rothermel rate of spread
ca.py            the Cell2Fire-style automaton (own code)
run_forefire.py  ForeFire 2.5 through pyforefire, one run per subprocess, retried
run_cell2fire.py Cell2Fire (C2F-W) with Scott and Burgan fuels mapped from the board
run_all.py       both scenarios, every model, results JSON + PNG sheet
index.html       the comparison page
results/         results per run; sample.json is the sample game's night 5
```

## Assumptions, all in `landscape.py`

`CELL` 30 m per square, `RES` 3 m per pixel, `WIND` 3 m/s from the west,
`HILL_HEIGHT` 30 m, and the `FUELS` table. The moisture and load numbers
were set so that forest floor barely carries fire and thick lantana carries
it fast. Rate of spread is Rothermel (1972) coded the way ForeFire codes it,
so the automaton and ForeFire agree on a flat, still square.

## What each model needs to be told, and why

- **ForeFire**: wind layers shaped `(1, 2, nx, ny)`; a front resolved finer
  than a pixel; NaN nodes filtered before rasterising; one instance per
  process. Its front collapses on this board once the connected lantana has
  burned, and the page says at which minute.
- **Cell2Fire**: ASC rasters, a `Weather.csv` with one row per minute, an
  `Ignitions.csv` whose cell number is `row * cols + col`, `--ignitions` or
  it picks a random cell, `--weather rows --Weather-Period-Length 1`. Arrival
  times come from `Messages/MessagesFile1.csv` (from, to, minute, ROS).
- **The automaton**: nothing; it reads the rasters.

## Not tried

FARSITE (Windows tooling, or a from-source Linux build, for a result the
other two bracket) and QUIC-Fire (not open).
