#!/usr/bin/env bash
# Render the whole film in parallel segments, then two-pass encode to a target file size.
#   tools/render_all.sh [target_MB=14.2] [jobs=4] [audio_kbps=64]
set -euo pipefail
cd "$(dirname "$0")/.."
TARGET_MB=${1:-14.5}
JOBS=${2:-4}
AK=${3:-64}
DUR=$(python3 -c "import json;print(json.load(open('data/timeline.json'))['duration'])")
FRAMES=$(python3 -c "import math;print(math.ceil($DUR*24))")
mkdir -p out/seg
rm -f out/seg/*.mp4 out/seg/list.txt
per=$(( (FRAMES + JOBS - 1) / JOBS ))
pids=()
for ((j=0; j<JOBS; j++)); do
  from=$(( j * per )); to=$(( (j+1) * per )); (( to > FRAMES )) && to=$FRAMES
  node src/render.mjs --from $from --to $to --out out/seg/seg_$j.mp4 2> out/seg/log_$j.txt &
  pids+=($!)
  echo "file 'seg_$j.mp4'" >> out/seg/list.txt
done
for p in "${pids[@]}"; do wait $p; done
ffmpeg -y -loglevel error -f concat -safe 0 -i out/seg/list.txt -c copy out/master_video.mp4
tools/encode.sh "$TARGET_MB" "$AK"
