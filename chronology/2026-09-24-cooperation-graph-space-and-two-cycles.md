# Cooperation: graph-first recap and two removal cycles

Baseline `962f16b`. User approved the direct Room flow and requested a second
smooth removal cycle plus a larger, more tightly framed interactive graph.

- Main unplanted removal now fades out, in, out and in over ten years. Cover
  peaks at years 0/5/10 and reaches cleared troughs at 2.5/7.5. A continuous
  cosine avoids flashes at reset boundaries. These are illustrative projection
  timings, not a claim that a crew takes years to clear a plot.
- The first trough is the initial paid removal; only the next completed cut
  counts as repeat income/native damage. Ten-year recap amounts therefore
  remain unchanged from the prior checkpoint. Fuel follows the same cover.
- Recap I gives the graph about two-thirds of a wider modal. The four learning
  points become one paragraph using the same wording. No new controls.
- Graph bounds follow all 21 allowed outcomes with 6% padding around observed
  extents, including zero. Linear axes retain actual values and all plans.
  Horizontal ticks are five credits apart; vertical ticks are two health points.
  No cropping, jitter or nonlinear axis is used to create apparent separation.
- Combined is untouched. Community integration there is the next discussion,
  not approved implementation in this checkpoint.

Tests cover both full cycles, smooth adjacent slider values, matching fuel,
unchanged repeat-cut count, graph bounds, wider layout and interactive points.
Browser skill found no available browser; repo Playwright fallback was used.
Screenshots remain outside git under
`/mnt/seagate/models/pyrocene/stage4/qa-cooperation-integrated/`, including
`live-wide-graph-laptop.png`, `debt-recap.png`, and `two-cycles-year-*.png`
with software variants. Live testing uses actual clicks/keyboard controls.

Only already-allowlisted static files changed. No server restart is needed;
reload the game to pick up the changes while retaining the room link.
Rollback by reverting this scoped checkpoint, preserving unrelated user notes.

Verification completed: all 17 main browser tests and 15 model tests passed.
The affected projection/recap playthrough also passed independently in WebGL
and disabled-WebGL browsers. Live 8024 was checked at 1280 x 800: all 21 dots
present, no modal overflow, no browser errors. No running server was restarted.
