#!/bin/bash
# usage: render_all.sh <outdir> [--nocap]
set -e
OUT=$1; shift
mkdir -p $OUT
N=$(python3 -c "import json,math; print(math.ceil(json.load(open('build/timeline.json'))['total']*24))")
W=4
pids=()
for i in $(seq 0 $((W-1))); do
  f0=$(( N*i/W )); f1=$(( N*(i+1)/W ))
  python3 render.py --range $f0:$f1 --seg $OUT/seg$i.mp4 "$@" > $OUT/log$i.txt 2>&1 &
  pids+=($!)
done
for p in ${pids[@]}; do wait $p; done
: > $OUT/list.txt
for i in $(seq 0 $((W-1))); do echo "file 'seg$i.mp4'" >> $OUT/list.txt; done
ffmpeg -y -loglevel error -f concat -safe 0 -i $OUT/list.txt -c copy $OUT/video_hq.mp4
echo "frames $N done"
