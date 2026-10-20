#!/usr/bin/env bash
# Render all frames with 4 parallel workers, then concat (-c copy) into build/video_raw.mkv.
# Usage: ./render_all.sh [FROM TO]   (default 0..TL.frames; used with a short range by encode.py --test)
set -euo pipefail
cd "$(dirname "$0")"
FROM=${1:-0}
TO=${2:-$(node -e "console.log(JSON.parse(require('fs').readFileSync('build/timeline.json')).frames)")}
N=4; mkdir -p build/parts; rm -f build/parts/p*.mkv build/parts/list.txt
T0=$(date +%s)
pids=()
for i in $(seq 0 $((N-1))); do
  A=$((FROM + (TO-FROM)*i/N)); B=$((FROM + (TO-FROM)*(i+1)/N))
  node render/render.mjs --from $A --to $B --out build/parts/p$i.mkv > build/parts/p$i.log 2>&1 &
  pids+=($!); echo "worker $i: frames $A-$B"
  echo "file 'p$i.mkv'" >> build/parts/list.txt
done
for p in "${pids[@]}"; do wait $p || { echo "worker failed, see build/parts/*.log"; exit 1; }; done
ffmpeg -y -loglevel error -f concat -safe 0 -i build/parts/list.txt -c copy build/video_raw.mkv
echo "rendered $((TO-FROM)) frames in $(( $(date +%s)-T0 ))s -> build/video_raw.mkv"
