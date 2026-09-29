# Community: paying for care beyond the project grant

Accepted baseline: `b8f50f8`, tagged `stage4-before-community` before work.
Prototype checkpoint tag: `stage4-community-v0`.

The request was to try a community agroforestry extension separately from the
accepted Cooperation / Negligence / Combined game. Hazel's concluding page is
deferred. The user's edits to `narrative/RECAP.md` and `stage4/v2_recap.md` were
left alone.

Play: **http://100.82.28.38:8035/community/#fresh=1**.
Rules, sources, migration boundaries and reproducible checks:
[Community README](../stage4/community/README.md).

## The small loop

Two native plantings sit behind two cleared buffer gaps. Start a local seed
nursery or shade-crop partnership in those gaps, then keep tending the native
plantings. Local income pays for local weeding and shade development. It is not
extra cash for the player. Reserves can contribute to rebuilding after fire.

The buffer changes the existing grass and canopy variables used by connected
fire. It is not a magic wall. It does not count as native forest restoration.
Both young and working buffers can burn. A damaged buffer returns to Unstable
plots when its shade drops below establishment; a destroyed one needs rebuilding.

The fixture starts four open commitments on Combined's fine grid. All active
squares remain selectable, but only the two marked gaps accept partnerships.
Native removal, replanting, inspection and six-month turns retain their familiar
meaning. The grant is 18 for this fixture. Main-game economics are unchanged.

## What changed while playing

- The first fixture referenced inactive squares. These were replaced with actual
  active forest-side squares before the playable traces.
- Early traces were too punishing to make the buffer tradeoff readable. Young
  native starting cover and boundary pressure were tuned. Additional boundary
  ignitions now begin after two setup moves; normal fires can still occur earlier.
- A truthy but unstarted community record initially hid Start partnership. Fixed.
- Local accounts now show care actually paid, not the amount due. Income stays
  separate from the project wallet and accumulated reserves are not discarded
  when a buffer is rebuilt.
- The renderer initially treated agroforestry as mature cover. A renderer-only
  young-growth adapter now gives it gradual point-cloud height and density.
- Both fire events are rendered when the base and boundary process ignite in
  the same season. The first version showed only the first event.
- Native care says Weed. Buffer selection has thin dashed outlines before
  establishment and green outlines after partnership, without filling the map.
- Completing the two native targets now offers an early finish. The first
  draft required many empty Next season clicks after success. Keep exploring
  remains available for looking at the buffer or trying other work.
- Close view retains species records, dispersal and germination. Shade-crop
  labels prioritise cupuaçu and the remaining grasses, without presenting grass
  as a deliberately planted crop.

## Evidence from play

The default seed 991 is an illustrative scenario, not a universal result. Actual
browser clicks using visible conditions recovered both native targets by year
3.5 with either partnership and 5 credits left. The matched run without buffers
lost F8 repeatedly; affordable replanting eventually exhausted most of its
budget. At year 12 it had one target closed and 3 credits left.

In 100-seed model probes, a simple native-care policy recovered both targets in
62 runs; nursery plus care did so in 78 and shade crops plus care in 74. On a
separate 100-seed set the corresponding counts were 57, 74 and 71. Waiting alone
won none. These are game-balance trials, not field effectiveness estimates.

A smaller-model engine agent and player agent handled bounded work. Cursor's
`gpt-5.3-codex-low` returned action batches from observations; the impatient
expander spent moves on clearance while the native targets reinvaded. Claude's
Haiku alias passed authentication but timed out on play prompts. The document
does not pretend that it completed a match. Early traces are preserved with
their model-snapshot caveat in [player findings](../stage4/community/player-findings.md).

Real browser runs and screenshots cover both enterprises, native care without
buffers, point-cloud inspection, species tabs, disabled-WebGL mode, reload and
return to an untouched Combined save. Screenshot directory is outside git:
`/mnt/seagate/models/pyrocene/stage4/qa-community/`.

Final checks passed: 111 JavaScript tests including 9 Community model tests,
6 Community browser tests, 9 existing Combined browser tests and 6 delivery
tests. No large media files were added to git.

The UI was exercised through Python Playwright after the in-app browser runtime
reported no available browser. This is actual browser interaction, not solely
calls into the model. Nobody has yet tested it with a room of participants.

## What remains an assumption

Embrapa, Xingu Seed Network and IPAM support the choice of Amazon enterprise
and community-management examples. They do not validate our numeric income,
growth or fire parameters. Secure access, agreement, labour and buyers are
assumed. The point-cloud fragments are measured; their use as a managed farm
and the crop inventory are simulated. Nursery presently outperforms shade crops
slightly under the simple probe policy. Further balancing should follow the
user's review rather than adding more systems tonight.

The accepted game's files, saves and running room servers were not replaced.
Only serving and packaging allowlists changed outside the isolated module and
its tests/docs. To continue from Combined later, import a copy of its state and
choose suitable degraded buffer plots explicitly. Do not transplant the fixed
scenario or its extra ignition process unexamined.
