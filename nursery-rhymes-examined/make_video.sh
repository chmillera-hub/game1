#!/usr/bin/env bash
# Renders and encodes the film. Needs build/tts (tts/synth.py), build/audio/mix.wav (audio/score.py + audio/mix.py)
# and the shared renderer in ../the-last-witness/render (with its node_modules installed).
#   ./make_video.sh                 render + encode
#   SKIP_RENDER=1 ./make_video.sh   encode only
set -euo pipefail
cd "$(dirname "$0")"
WORKERS=${WORKERS:-4}
mkdir -p build/chunks output
if [ -z "${SKIP_RENDER:-}" ]; then
  node render/timeline.js
  NF=$(node -e "console.log(require('./build/timeline.json').nFrames)")
  per=$(( (NF + WORKERS - 1) / WORKERS ))
  pids=()
  for i in $(seq 0 $((WORKERS - 1))); do
    (cd render && node render.js --frames $(( i * per )) $(( (i + 1) * per )) --out ../build/chunks/part_$i.mkv > ../build/chunks/part_$i.log 2>&1) &
    pids+=($!)
  done
  for p in "${pids[@]}"; do wait "$p"; done
  : > build/chunks/list.txt
  for i in $(seq 0 $((WORKERS - 1))); do echo "file 'part_$i.mkv'" >> build/chunks/list.txt; done
  ffmpeg -y -loglevel error -f concat -safe 0 -i build/chunks/list.txt -c copy build/master.mkv
fi
# 720x1280, 24 fps, HEVC 10-bit; quality chosen to keep SSIM ~0.98+ against the master
[ -f build/audio/mix.wav ] || { echo "no audio yet: master rendered at build/master.mkv"; exit 0; }
CRF=${CRF:-30}
ffmpeg -y -loglevel error -i build/master.mkv -i build/audio/mix.wav -c:v libx265 -preset slow -crf $CRF -pix_fmt yuv420p10le \
  -x265-params "aq-mode=3:keyint=240:min-keyint=24:bframes=8:rc-lookahead=60:log-level=error" -tag:v hvc1 \
  -c:a libopus -b:a 48k -frame_duration 60 -ac 1 -application audio -map 0:v -map 1:a -shortest -movflags +faststart output/nursery-rhymes-examined.mp4
ls -la output
