#!/bin/sh
# Rebuild game-scripts/ and dist/zuujis-game-scripts.zip from a games-rs checkout.
#
#   scripts/build-game-scripts.sh ../games.zuujis.com
#
# game-scripts/js/ gets the shared game scripts the Studio starters load, plus the parts of three.js they import.
# The ZIP adds what those scripts read at run time (the asset library, served at /assets/) and the fifteen starters,
# so it runs as it is from any static web server.
set -eu
SRC=${1:?usage: scripts/build-game-scripts.sh <games-rs checkout>}
SRC=$(cd "$SRC" && pwd)
ROOT=$(cd "$(dirname "$0")/.." && pwd)
OUT="$ROOT/game-scripts"
SCRIPTS="game-assets.js game-sfx.js game-pad.js game-vision.js game-vision-3d.js game-racing.js game-fight.js game-flight.js"
ADDONS="GLTFLoader.js OrbitControls.js utils/BufferGeometryUtils.js"

for f in $SCRIPTS three.module.min.js; do test -f "$SRC/public/js/$f" || { echo "missing public/js/$f in $SRC" >&2; exit 1; }; done

rm -rf "$OUT/js"
mkdir -p "$OUT/js/three-addons/utils"
for f in $SCRIPTS three.module.min.js; do cp "$SRC/public/js/$f" "$OUT/js/$f"; done
for f in $ADDONS; do cp "$SRC/public/js/three-addons/$f" "$OUT/js/three-addons/$f"; done
cp "$ROOT/scripts/three-LICENSE.txt" "$OUT/js/three-LICENSE.txt"

# Every script and addon a starter loads must be here.
for t in "$SRC"/studio/templates/*.html; do
  for p in $(grep -o '"/js/[A-Za-z0-9./-]*\.js"' "$t" | tr -d '"'); do
    test -f "$OUT$p" || { echo "$(basename "$t") loads $p, which is not packed" >&2; exit 1; }
  done
  for p in $(grep -o "three/addons/[A-Za-z/]*\.js" "$t"); do
    test -f "$OUT/js/three-addons/${p#three/addons/}" || { echo "$(basename "$t") imports $p, which is not packed" >&2; exit 1; }
  done
done

# The kit: scripts, the asset library and the starters, filled in as the Studio fills a new draft.
KIT=$(mktemp -d)/zuujis-game-scripts
mkdir -p "$KIT/starters"
cp -R "$OUT/js" "$KIT/js"
cp -R "$SRC/public/assets" "$KIT/assets"
cp "$OUT/README.md" "$KIT/README.md"
cp "$ROOT/LICENSE" "$KIT/LICENSE-CC0.txt"
list=""
for t in "$SRC"/studio/templates/*.html; do
  n=$(basename "$t")
  sed -e 's/{{NAME}}/My Game/g' -e 's/{{ICON}}/🎮/g' -e 's/{{COLOR}}/#8b5cf6/g' "$t" > "$KIT/starters/$n"
  list="$list<li><a href=\"starters/$n\">${n%.html}</a></li>"
done
cat > "$KIT/index.html" <<EOF
<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Zuujis game starters</title>
<style>body{font:16px/1.6 system-ui,sans-serif;max-width:640px;margin:40px auto;padding:0 20px}a{color:#6d28d9}</style></head>
<body><h1>Zuujis game starters</h1><p>Each starter plays with the keyboard, a gamepad, or touch. Open one, then edit its HTML.</p>
<ul>$list</ul><p>See README.md for the scripts and licences.</p></body></html>
EOF
find "$KIT" -name .DS_Store -delete
mkdir -p "$ROOT/dist"
rm -f "$ROOT/dist/zuujis-game-scripts.zip"
(cd "$(dirname "$KIT")" && zip -qrX "$ROOT/dist/zuujis-game-scripts.zip" zuujis-game-scripts)
rm -rf "$(dirname "$KIT")"
echo "game-scripts/js: $(find "$OUT/js" -type f | wc -l | tr -d ' ') files"
ls -l "$ROOT/dist/zuujis-game-scripts.zip"
