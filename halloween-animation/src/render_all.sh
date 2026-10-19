#!/bin/bash
# Render all frames in parallel segments, then join them losslessly.
set -e
cd "$(dirname "$0")/render"
FR=$(node render.js info | python3 -c "import json,sys; print(json.load(sys.stdin)['frames'])")
J=${J:-4}
mkdir -p ../work/seg
rm -f ../work/seg/*.mkv
node render.js still 0 ../work/frame0.png
PER=$(( (FR + J - 1) / J ))
for k in $(seq 0 $((J-1))); do
  F0=$((k*PER)); F1=$(( (k+1)*PER )); [ $F1 -gt $FR ] && F1=$FR
  node render.js range $F0 $F1 ../work/seg/seg_$k.mkv &
done
wait
: > ../work/seg/list.txt
for k in $(seq 0 $((J-1))); do echo "file 'seg_$k.mkv'" >> ../work/seg/list.txt; done
ffmpeg -y -loglevel error -f concat -safe 0 -i ../work/seg/list.txt -c copy ../work/video_lossless.mkv
echo "frames=$FR done"
