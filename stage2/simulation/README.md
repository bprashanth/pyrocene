# Post-game replay

A replay of the game that just finished, built from its event log. Two are being
written independently, one per folder, and the room server picks up whichever
folders exist.

```
stage2/simulation/
  claude/index.html     one replay
  codex/index.html      the other
  sample-game.json      a finished game to develop against, no server needed
  SPEC.md               the event log format, and the rules both must follow
```

Each folder is a self-contained static page. The server serves it at
`/simulation/<folder>/` and hands it the log at `/api/log`. Nothing in a folder
is imported by the game, and the game imports nothing from one.

After a game ends, the game master console shows a **Show animation** button for
each installed folder. It opens the page in a new tab with the log name in the
query string, which is what you put on the projector.

Open one directly while developing:

```
python3 -m stage2.server
# then http://localhost:8020/simulation/claude/?log=sample-game.json
```

Read `SPEC.md` before writing anything.
