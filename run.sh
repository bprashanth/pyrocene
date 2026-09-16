#!/usr/bin/env bash
# Start everything an evening needs, print the one address to open, and stop it
# all again on ctrl-c.
#
#   ./run.sh                 room on 8020, films on 8022, Stage 4 on 8024
#   ./run.sh --stage 1       start the room on stage 1
#   ./run.sh --port 9000     move the room (films +2, Stage 4 +4)
#
# Anything else you pass is handed to the game server, so --seed, --style and
# --fast work here too. See python3 -m stage2.server --help.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

PORT=8020
ARGS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --port) PORT="$2"; shift 2 ;;
    --port=*) PORT="${1#*=}"; shift ;;
    *) ARGS+=("$1"); shift ;;
  esac
done
FILMS_PORT=${PYROCENE_FILMS_PORT:-$((PORT + 2))}
STAGE4_PORT=${PYROCENE_STAGE4_PORT:-$((PORT + 4))}
FILMS=${PYROCENE_FILMS:-/mnt/seagate/videos/pyrocene}

pids=()
stop() {
  printf '\nstopping\n'
  for p in "${pids[@]:-}"; do
    [ -n "$p" ] && kill "$p" 2>/dev/null
  done
  for p in "${pids[@]:-}"; do
    [ -n "$p" ] && wait "$p" 2>/dev/null
  done
  exit 0
}
trap stop INT TERM

PYROCENE_FILMS_PORT="$FILMS_PORT" PYROCENE_STAGE4_PORT="$STAGE4_PORT" python3 -u -m stage2.server --port "$PORT" "${ARGS[@]}" &
pids+=($!)
python3 -u -m stage2.films.serve --port "$FILMS_PORT" --assets "$FILMS" &
pids+=($!)
python3 -u -m stage4.serve --host 0.0.0.0 --port "$STAGE4_PORT" &
pids+=($!)

# Give the servers a moment to bind, then fail loudly rather than printing an address
# that answers nothing.
sleep 2
for p in "${pids[@]}"; do
  if ! kill -0 "$p" 2>/dev/null; then
    echo "one of the servers did not start. Scroll up for why."
    stop
  fi
done

ip=$(python3 - <<'PY'
from stage2.server import addresses
print(addresses()[0][0])
PY
)
cat <<TXT

  open this            http://$ip:$PORT/start

  players              http://$ip:$PORT/
  game master          http://$ip:$PORT/gm
  map                  http://$ip:$PORT/projector
  fire lab             http://$ip:$PORT/simulation/claude/lab/?run=sample
  films                http://$ip:$FILMS_PORT/
  stage 4              http://$ip:$STAGE4_PORT/

  ctrl-c stops everything

TXT

wait
