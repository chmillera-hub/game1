#!/usr/bin/env bash
# Render every frame of the film into out/frames/%05d.jpg with K parallel headless browsers.
#   tools/render_all.sh [K=3] [--force]
# Each worker takes an interleaved block of ~240 frames at a time so scene setup cost is shared and
# workers finish together. Already-rendered frames are skipped (unless --force).
set -euo pipefail
cd "$(dirname "$0")/.."
K=${1:-3}
FORCE=${2:-}
DUR=$(python3 -c "import json;print(json.load(open('data/timeline.json'))['duration'])")
N=$(python3 -c "import math;print(int(math.floor($DUR*24)))")
BLOCK=240
mkdir -p out/frames out/logs
echo "rendering frames 0..$N with $K workers"
for w in $(seq 0 $((K-1))); do
  (
    b=$w
    while :; do
      f0=$((b*BLOCK)); f1=$((f0+BLOCK-1)); [ $f0 -gt $N ] && break; [ $f1 -gt $N ] && f1=$N
      node tools/render.js frames --from $f0 --to $f1 --out out/frames $FORCE >> out/logs/render_w$w.log 2>&1 || echo "worker $w block $f0-$f1 FAILED" >> out/logs/render_w$w.log
      b=$((b+K))
    done
  ) &
done
wait
have=$(ls out/frames/*.jpg | wc -l)
echo "frames on disk: $have / $((N+1))"
