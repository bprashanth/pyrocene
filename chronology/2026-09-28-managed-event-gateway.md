# Managed event stack and replayable stage navigation

28 September 2026. This changes deployment and stage navigation, not the forest
game's rules, projections or visual design.

## Checkpoint and ownership

Before this work, tag `pyrocene-before-managed-event-20260928` preserved HEAD
`e7784b9`. Existing uncommitted Lore/service work was also copied to
`/tmp/pyrocene-pre-managed-20260928.tar.gz`. The archive is local, not a portable
backup. Other-agent Lore routes/assets and user narrative drafts were left in
place. The existing Lore unit is reused; its source and the extended service
README are included with this deployment work.

Do not reset the whole checkout to undo deployment. First stop/disable or
uninstall the event units using `services/manage.py`, then revert the deployment
commit selectively. Lore and the shared Cloudflare tunnel remain independent.

## Stage 1 / Stage 2 fix

Previously, `/gm?stage=1` or `stage=2` changed the room only while it was in the
lobby. A GM could follow a Stage 1 link but still see the ongoing Stage 2 game.
Now explicitly choosing the other stage abandons the current run and opens that
stage's lobby. Names and phone tokens survive the switch. Selecting an ended
stage starts it again. Refreshing the same active stage preserves play; Reset
still provides an explicit same-stage restart and clears the roster.

Switching cancels pending playback by epoch and clears replay/comparison state.
Animation checks and paints are locked together, so the previous game cannot
paint over the fresh lobby. The Back to stage 1 button updates the URL as well.
Phone links no longer change the room's stage.

For a no-intervention demonstration, enter `/gm?stage=2`, seed players, start,
finish each night, and choose Hunt lantana without voting anybody out. Neither
removal nor resilience work occurs. Show each transition on the projector.
Afterwards `/gm?stage=1` starts the normal sequence without restarting servers.

## One public origin

The new loopback gateway on **8030** routes the existing stack:

| Path | Backend |
| --- | --- |
| `/start`, Mafia room, GM, projector and room APIs/events | 8020 |
| `/stage4/*` | 8024, with the prefix removed upstream |
| `/films/*` | 8022, streamed with byte-range support |
| `/cinematic/*` | 8021 |
| `/stage3/*` | Existing browser build in `web/` |
| `/lore` and children | 8024 |

Stage 4 API/team URLs resolve against the app module root, so both direct-port
and prefixed links work. The obsolete 8033 fallback was removed. The launcher
uses these same-origin paths only when served through the gateway; direct LAN
links remain usable. Stage 3 preserves cross-origin isolation and still fetches
Pyodide/xterm from jsDelivr. The old Netlify deployment was not changed.

SSE is streamed immediately. Media is streamed rather than accumulated in
memory. The film server now handles Range requests for seeking. The gateway
rejects traversal, cross-origin action posts and arbitrary proxy destinations.
GM pages, actions, private state/logs and GM events have a separate organiser
login, even when the outer event login is disabled. The generated credential is
outside git at `~/.config/pyrocene/gm-credentials`, mode 0600. Do not copy its
contents into documentation or screenshots.

## Services installed and running

`pyrocene-games.target` is enabled for boot and owns room, films, cinematic and
gateway services. Each server restarts on failure. The target starts the existing
Lore unit but does not own its shutdown. `Linger=yes` was already enabled; the
machine was not rebooted for testing.

The old foreground `run.sh` process was identified and stopped with its own
cleanup trap. Managed services now own 8020/8021/8022/8030. The Lore process on
8024 retained PID 3613537 through the migration, stop/start check and gateway
crash-recovery check. The shared system cloudflared process was not modified.

Plain `./run.sh` now starts the managed group, checks readiness and exits.
`./run.sh --manual --port 9000` retains the foreground development workflow.
Start, stop, restart, status, logs, disable and uninstall commands are in
[services/README.md](../services/README.md). Stopping the event group leaves Lore
running. Uninstall removes only owned event-unit links and preserves the repo,
assets, credentials, Lore and tunnel. Backends still bind to the trusted LAN;
never publish their ports directly as an alternative public route.

Game state is still in memory. Restarting room resets Mafia, and restarting
Lore resets shared Stage 4 rooms. Reboot starts services but does not resume a
game. `/mnt/seagate` must remain mounted for the prepared forest/media assets.

## Cloudflare remains a user action

No Cloudflare changes were made. On the existing named tunnel, route
`^/lore(/.*)?$` to `http://localhost:8024` first, then the same hostname with an
empty path to `http://localhost:8030`. The second rule must cover all remaining
paths, not just `/start`.

Separately create a host-wide Access application allowing organisers/testers,
and a more-specific Lore application covering both `/lore` and `/lore/*` with
Bypass / Everyone. Tunnel ordering does not control authentication. Temporarily
bypass the general application on game day if attendees should enter freely.
The gateway's GM login remains. Exact settings and official references are in
the service README. Public end-to-end Access/phone checks remain pending these
user-configured routes. Existing public `/lore` continued to return 200.

## Verification

- Gateway tests cover prefix/API routing, organiser access, immediate SSE,
  film ranges, traversal rejection and stage resets during playback. The final
  combined gateway/browser run passed all nine checks in 59 seconds.
- Browser playthrough follows `/start` into Stage 2 without Stage 1, advances
  without interventions until fire, returns to Stage 1, starts it, jumps to
  Stage 2, then uses Back to stage 1 and refreshes.
- Browser playthrough enters the forest, creates a room, commits all-A, moves
  projection, opens Prelude III, enters The Game and returns to the same room.
  Team links keep the public prefix. No page errors were recorded.
- Stage 3 actually boots into its terminal menu with cross-origin isolation.
  The live managed gateway was checked separately for forest and terminal boot.
- Existing suites: 42 rules/styles/isolation, 24 stage browser checks, 23
  journey browser checks and 40 Stage 4 cooperation/delivery/shared-room checks
  passed. The stage-test reset fixture now explicitly starts Stage 1 to avoid
  test-order leakage after Stage 2 handovers.
- Film Range requests returned 206 and the correct byte boundaries. FFmpeg
  successfully sought to 20 seconds and decoded a frame over the live gateway.
  The bundled test Chromium lacks H.264, so actual film playback still needs
  the final event-Chrome check; its aborted media loads were a codec limitation.
- Systemd unit verification passed. Event stop/start preserved Lore and its
  public page. Killing only the gateway process exercised its automatic restart.
- Screenshots are outside git in `/tmp/pyrocene-event-qa/`, including the
  no-intervention fire aftermath, stage jumps, committed forest, Prelude, Game,
  and live managed forest/Stage 3. No large media or secrets were added to git.
