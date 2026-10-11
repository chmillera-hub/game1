#!/usr/bin/env bash
# Render the whole film in parallel segments, then two-pass encode to a target file size.
#   tools/render_all.sh [target_MB=14.2] [jobs=4] [audio_kbps=64]
set -euo pipefail
cd "$(dirname "$0")/.."
TARGET_MB=${1:-14.2}
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
# bitrate budget
VK=$(python3 -c "print(int(($TARGET_MB*8*1024*1024/ $DUR - $AK*1000)/1000))")
echo "duration ${DUR}s frames ${FRAMES} -> video ${VK} kbps + audio ${AK} kbps"
X264="-c:v libx264 -preset veryslow -tune animation -profile:v high -level 4.0 -pix_fmt yuv420p -b:v ${VK}k -maxrate $((VK*3))k -bufsize $((VK*6))k -g 240 -keyint_min 24 -bf 5 -refs 6 -x264-params aq-mode=3:aq-strength=0.9:deblock=-1,-1:psy-rd=0.6,0"
ffmpeg -y -loglevel error -i out/master_video.mp4 $X264 -pass 1 -passlogfile out/x264pass -an -f mp4 /dev/null
ffmpeg -y -loglevel error -i out/master_video.mp4 -i out/mix.wav $X264 -pass 2 -passlogfile out/x264pass \
  -c:a aac -b:a ${AK}k -ac 2 -ar 44100 -movflags +faststart -shortest out/final.mp4
ls -la out/final.mp4
