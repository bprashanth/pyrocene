# Pyrocene services

This directory is the source of truth for repository-managed systemd units.
Agents should edit files here, then reload/restart the affected service. Do not
edit generated files in `/run/user/1000/systemd/transient/` or maintain a second
copy in the user configuration directory.

## Event stack: everyday commands

The installed `pyrocene-games.target` starts at boot. Each server restarts on
failure and has its own journal. Lore stays independent. Run from the repository:

```sh
./run.sh                              # managed start, checks readiness, exits
python3 services/manage.py status
python3 services/manage.py logs
python3 services/manage.py logs gateway
python3 services/manage.py restart room # resets the shared Mafia room
python3 services/manage.py stop        # stops event servers, leaves Lore up
python3 services/manage.py start
python3 services/manage.py disable     # stop and disable event startup at boot
python3 services/manage.py install     # install/re-enable repository unit links
python3 services/manage.py uninstall   # stop/disable and remove our event links
```

`stop` lasts until a manual start or reboot; use `disable` to keep it off after
reboot. `uninstall` preserves Lore, shared cloudflared, repository, assets and
organiser credentials. Use the separate Lore instructions below if you also want
to remove that service. Do not disable user lingering or the shared tunnel.

All unit files are symlinked from this directory. After editing them, run
`systemctl --user daemon-reload`, then restart the affected service. The manager's
`restart` command does this reload for you. Installation refuses to overwrite a
unit owned by another checkout. Backing up/moving this checkout requires updating
the unit working directories and symlinks.

| Unit | Local listener | Role |
| --- | --- | --- |
| `pyrocene-room.service` | 8020 | Start, Mafia, Stages 1/2, fire lab |
| `pyrocene-cinematic.service` | 8021 | Existing cinematic prototype |
| `pyrocene-films.service` | 8022 | Film gallery, streamed video with byte-range seeking |
| `pyrocene-lore.service` | 8024 | Existing Lore + Stage 4, outside the games stop group |
| `pyrocene-gateway.service` | **127.0.0.1:8030** | Single-origin event entry |

The gateway is loopback-only. Local office links on the existing backend ports
still work, without the gateway's organiser gate. Treat those ports as trusted
LAN access: never publish them directly through another public route or firewall
rule. Cloudflare should reach only the gateway plus the narrow public Lore path.

`./run.sh --manual --port 9000` retains the foreground/custom-port development
workflow. Once managed services are installed, plain `./run.sh` starts systemd
services and exits; Ctrl-C in that shell no longer stops them. Use `manage.py stop`.
Do not use manual default ports while the managed services own them.

## Cloudflare: exact event setup

**The repository does not change Cloudflare configuration.** The user must make
these changes on their existing named tunnel. Keep its other applications intact.

Tunnel routes for `pyrocene.idli.cc`, in this order:

1. Path regex `^/lore(/.*)?$` -> `http://localhost:8024`.
2. Empty path (all remaining paths) -> `http://localhost:8030`.

The first route includes `/lore`, `/lore/`, its CSS and pictures. The second
must be a catch-all, not just `/start`, because player pages, APIs, live events,
films and forest data also need it. `/start` belongs to 8020 behind the gateway;
pointing it directly at 8024 will not serve the launcher.

Create two **Access self-hosted applications**, separately from tunnel routes:

- `pyrocene.idli.cc` with Path empty: Allow only the organiser/tester accounts.
- A more-specific public Lore application covering `pyrocene.idli.cc/lore`
  and `pyrocene.idli.cc/lore/*`: **Bypass / Include / Everyone**.

Specific Access paths override the host-wide gate; tunnel route ordering alone
does not grant a login exemption. An Access wildcard ending `/lore/*` does not
include the bare `/lore`, so cover both. Official references:
[application paths](https://developers.cloudflare.com/cloudflare-one/access-controls/policies/app-paths/),
[public endpoint bypass](https://developers.cloudflare.com/cloudflare-one/access-controls/policies/common-policies/),
[tunnel path forwarding](https://developers.cloudflare.com/tunnel/features/locally-managed-tunnels/configuration-file/).

Before sharing, test in a logged-out/incognito browser or on mobile data:

- `/lore`, `/lore/lore.css` and an image load with **no login**.
- `/start`, `/stage4/expedition.html`, `/stage3/`, `/films/` and `/api/state`
  hit Access before login (the last also needs the organiser login afterwards).
- After login: join from a phone, watch the projector update, open Stage 4 and
  its close view, seek a film, and enter Stage 3's terminal game.

For game day, temporarily use **Bypass / Everyone** on the general event
application if you want login-free attendees. Keep the Lore exception. Restore
the organiser-only policy after the event. No service restart is needed for
Access policy changes. Use a named tunnel: Quick Tunnels do not support the
Mafia server's SSE live updates. Do not cache game APIs/events or enable response
buffering for `/events`. Existing no-store and streaming headers are preserved.

## Public paths and organiser login

| Path | Service |
| --- | --- |
| `/start` | Main launcher |
| `/`, `/gm`, `/projector`, `/api/*`, `/events` | Room on 8020 |
| `/stage4/expedition.html` and `/stage4/*` | Forest on 8024 |
| `/films/*` | Films on 8022 |
| `/cinematic/*` | Prototype on 8021 |
| `/stage3/*` | Existing `web/` browser build, served by gateway |
| `/lore`, `/lore/*` | Lore on 8024, also supported by gateway |

The gateway's GM login protects `/gm`, GM actions, private state/steps/logs and
the GM SSE channel. It remains in force even if the event's Cloudflare login
is removed. It uses the browser's login dialog, username **gm**. Retrieve the
generated `username:password` locally with:

```sh
cat ~/.config/pyrocene/gm-credentials
```

This file is mode 0600, outside the repository. Never paste it into chronology,
screenshots or Cloudflare route settings. It is separate from Cloudflare login.
To change it, edit that file with a password of at least 16 characters, then
`python3 services/manage.py restart gateway`. This server-side secret is used
only for the organiser gate; no credential is embedded in frontend assets.

Stage 3 is now linked to `/stage3/` through the gateway. Its worker and isolation
headers are preserved. Like its original Netlify deployment it still downloads
Pyodide and xterm from jsDelivr, so participants need internet access. The existing
Netlify site remains separately public; this installation does not modify it.
The Stage 3 Python build refreshes when the gateway starts.

## Stage switching and no-intervention demonstration

`/gm?stage=1` and `/gm?stage=2` now switch from any current phase, including
mid-animation. Switching abandons the old run and opens a fresh lobby, keeping
connected names/tokens. Refreshing the same active stage preserves it. Selecting
an ended stage starts it again. The Reset button can restart the same stage;
the Back to stage 1 button also updates its URL so refresh stays in stage 1.
Player links never change the room's stage.

For the demonstration: open `/gm?stage=2`, Seed test players, Start game, and
open the projector. Finish night, show its changes, choose **Hunt lantana** but
vote nobody out, then Finish vote and show its changes. This applies neither
removal nor resilience. Repeat through the season to show growth and fire. The
season-length controls can bring the last night forward. Afterwards use
`/start` -> Stage 1 -> GM to replay the normal stages.

Restarting the room process resets its in-memory run. Restarting the Lore/Stage4
process resets shared Stage 4 rooms. Gateway/film restarts do not reset game
backends. Startup after reboot is enabled, but a reboot does **not** resume shared
games. Keep `/mnt/seagate` mounted for the forest data and films.

Tests: `python3 -m unittest services.test_gateway services.test_gateway_play -q`.
Screenshots are external under `/tmp/pyrocene-event-qa/`, never committed.

## pyrocene-lore.service

A **user-level systemd service**, owned by `beeps`, serving the lore page and
Stage 4 through `python3 -m stage4.serve` on **0.0.0.0:8024**. It is independent
of the terminal, SSH connection, and agent session. It restarts after a failure
with a three-second delay. Logs go to the user journal.

The installed unit at `~/.config/systemd/user/pyrocene-lore.service` is a symlink
to this directory. It is enabled for the user manager's `default.target`.
`loginctl show-user beeps -p Linger` returned `Linger=yes` on September 28,
2026, so the user manager can start at boot and remain after logout. Keep this
checkout at its configured location; moving it requires updating the unit and
its installation link.

| Item | Location |
| --- | --- |
| Working directory | `%h/src/github.com/bprashanth/pyrocene` (`%h` is the user's home) |
| Lore | `http://127.0.0.1:8024/lore` or `/lore/` |
| Public lore | `https://pyrocene.idli.cc/lore` |
| Application | `stage4/serve.py` |
| Page, CSS, images | `stage4/lore/` |
| Prepared game assets | `/mnt/seagate/models/pyrocene/stage4/assets` by default |

The public route is configured separately through Cloudflare. This unit does
not run or configure Cloudflare, and it does not start the room server on 8020.
Despite its name, it serves the existing Stage 4 app, not an isolated static-only
server. Cloudflare routing must include the lore CSS and images under `/lore/`.

## Editing and operating

Run as `beeps`, without `sudo`:

```sh
# After editing the unit file in this directory:
systemctl --user daemon-reload
systemctl --user restart pyrocene-lore.service

# Inspect:
systemctl --user status pyrocene-lore.service
systemctl --user cat pyrocene-lore.service
journalctl --user -u pyrocene-lore.service -n 60 --no-pager
curl -I http://127.0.0.1:8024/lore/
curl -I https://pyrocene.idli.cc/lore

# Stop or start deliberately:
systemctl --user stop pyrocene-lore.service
systemctl --user start pyrocene-lore.service
```

HTML, CSS and image edits are served from disk immediately. Changes to Python
server code or its startup settings require a restart. Do not launch another
process on 8024 while this unit is running. The event target reuses this unit.

To install on this machine from a clean state:

```sh
systemctl --user enable /home/beeps/src/github.com/bprashanth/pyrocene/services/pyrocene-lore.service
systemctl --user daemon-reload
systemctl --user start pyrocene-lore.service
```

If replacing the old transient unit, stop it before the installation commands.
For a different account or checkout location, adjust the paths first. Disabling
with `systemctl --user disable --now pyrocene-lore.service` stops it and removes
the enablement links; the repository unit remains available for reinstalling.

## Event-day link

The lore button currently says **RSVP** and links to the Google Form in
`stage4/lore/index.html`. On Wednesday, September 30, manually change its label
to **Enter the forest** and its destination to `https://pyrocene.idli.cc/start`
after configuring the routes above. No automatic switch is scheduled.

The room launcher's Stage 4 tile already goes directly to
`8024/expedition.html`, avoiding a loop back to the lore page. Starting or
exposing the room server for event day is separate from this service.
