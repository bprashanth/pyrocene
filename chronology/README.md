# chronology — pyrocene

Notes from building Pyrocene, a game about invasive lantana and the fires it
feeds, made for a national climate week event.

The game runs in three stages. Stage 1 is plain Mafia played in a room. Stage 2
adds a projected map and fire to that same room game. Stage 3 is the
single-player terminal game, live at
[pyrocene.netlify.app](https://pyrocene.netlify.app). The work below mostly runs
backwards through that list: stage 3 was built first, then stage 2, and stage 1
then fell out of stage 2 nearly for free.

Evidence links are paths relative to the repository root.

Read in filename order.

| | |
|---|---|
| [2026-07-22T2115](2026-07-22T2115-browser-build.md) | Putting the terminal game in a browser without changing it |
| [2026-09-11T1616](2026-09-11T1616-room-game.md) | Stage 2: mirroring a room onto a map, and staying away from the live game |
| [2026-09-11T1849](2026-09-11T1849-showing-the-change.md) | Why the room could not see what changed |
| [2026-09-12T0157](2026-09-12T0157-map-styles.md) | Six map styles, and what actually made one readable |
| [2026-09-12T2311](2026-09-12T2311-fire-line.md) | The fire line took five passes |
| [2026-09-12T2332](2026-09-12T2332-balance.md) | Balance we decided not to fake |
| [2026-09-13T0100](2026-09-13T0100-stage-one-and-replay.md) | Stage 1, and the replay that ties the two evenings together |
| [2026-09-13T0800](2026-09-13T0800-handoff.md) | Handing the post-game film to two agents at once |
| [2026-09-13T0930](2026-09-13T0930-where-we-are.md) | Stock-take, and what is still untested |
| [2026-09-13T1100](2026-09-13T1100-two-replays-claude.md) | Two post-game films from one agent: paper, then a night forest |
| [2026-09-13T1200](2026-09-13T1200-testing-the-transition.md) | Driving the stage 1 to stage 2 handover, and what is missing |
| [2026-09-13T1230](2026-09-13T1230-three-film-studies.md) | When real-time 3D was the wrong deliverable |
| [2026-09-13T1630](2026-09-13T1630-fire-lab.md) | Board, then a real fire model, then a picture: the fire lab |
| [2026-09-13T1900](2026-09-13T1900-real-fires.md) | Real fires on the game's board |
| [2026-09-14T0200](2026-09-14T0200-beneath-the-canopy.md) | Beneath the canopy: cinema anchored to real measurements |
| [2026-09-14T0945](2026-09-14T0945-amazon-fire-legacy.md) | A real Amazon fire legacy, and the point cloud we refused to invent |
| [2026-09-14T1230](2026-09-14T1230-one-real-lidar-film.md) | Removing generated imagery and making one restrained LiDAR film |
| [2026-09-14T1525](2026-09-14T1525-lidar-final.md) | Freezing the LiDAR final before the hyperspectral experiments |
| [2026-09-14T1540](2026-09-14T1540-hyperspectral-studies.md) | From measured structure to measured forest content |

The largest caveat, stated once here and repeated where it matters: **no room
has played stage 2 yet.** Every balance number comes from a scripted model, and
every judgement about whether a map reads well comes from one person looking at
a laptop.

Entries are appended, not rewritten. Where a later entry corrects an earlier
one, both stay and the later one says what changed.
