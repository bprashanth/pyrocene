#!/usr/bin/env bash
# Stage the game's Python into web/py/ so the browser can fetch it.
#
# Nothing here modifies the game. It copies engine/ and terminal/ verbatim and
# writes a manifest the worker walks to populate Pyodide's virtual filesystem.
# Run it from anywhere; paths are resolved from this script's location.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(dirname "$here")"
out="$here/py"

rm -rf "$out"
mkdir -p "$out"

# The packages the game needs at runtime. pokeflow_panel/pokeflow_bundle are
# left out on purpose: that path needs a real tty and is not reachable on web.
for pkg in engine terminal; do
  (cd "$root" && find "$pkg" -type f \( -name '*.py' -o -name '*.txt' \) \
      -not -name 'pokeflow_*' -print0) |
    while IFS= read -r -d '' f; do
      mkdir -p "$out/$(dirname "$f")"
      cp "$root/$f" "$out/$f"
    done
done

# manifest.json: a flat list of paths, relative to py/. Written with shell only,
# so the build needs nothing but bash and coreutils on the host. The paths are
# our own file names, so plain quoting is safe.
files=$(cd "$out" && find . -type f -not -name manifest.json | sed 's|^\./||' | sort)

{
  printf '['
  sep=""
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    printf '%s"%s"' "$sep" "$f"
    sep=", "
  done <<< "$files"
  printf ']\n'
} > "$out/manifest.json"

echo "staged $(printf '%s\n' "$files" | grep -c .) files into web/py/"
