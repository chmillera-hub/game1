#!/usr/bin/env bash
# Builds The Last Witness end to end from the voice takes, direction and soundtrack.
#   ./make_video.sh            timeline + render + both encodes
#   SKIP_RENDER=1 ./make_video.sh   re-encode from an existing master
# Needs: node (render/ deps installed), ffmpeg with libx265 + libopus, and build/audio/mix.wav
# (python3 -I audio/score.py && python3 -I audio/mix.py).
set -euo pipefail
cd "$(dirname "$0")"
WORKERS=${WORKERS:-4}
OUT=output
mkdir -p build/chunks "$OUT"

if [ -z "${SKIP_RENDER:-}" ]; then
  node render/timeline.js
  NF=$(node -e "console.log(require('./build/timeline.json').nFrames)")
  per=$(( (NF + WORKERS - 1) / WORKERS ))
  pids=()
  for i in $(seq 0 $((WORKERS - 1))); do
    f0=$(( i * per )); f1=$(( (i + 1) * per ))
    (cd render && node render.js --frames $f0 $f1 --out ../build/chunks/part_$i.mkv > ../build/chunks/part_$i.log 2>&1) &
    pids+=($!)
  done
  for p in "${pids[@]}"; do wait "$p"; done
  : > build/chunks/list.txt
  for i in $(seq 0 $((WORKERS - 1))); do echo "file 'part_$i.mkv'" >> build/chunks/list.txt; done
  ffmpeg -y -loglevel error -f concat -safe 0 -i build/chunks/list.txt -c copy build/master.mkv
fi

DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 build/audio/mix.wav)
X265="aq-mode=3:keyint=600:min-keyint=24:bframes=8:rc-lookahead=60:log-level=error"

# Higher quality: 720x1280, 24 fps, HEVC 10-bit constant quality, Opus 40 kbps mono
HQ_CRF=${HQ_CRF:-31}
ffmpeg -y -loglevel error -i build/master.mkv -i build/audio/mix.wav -c:v libx265 -preset medium -crf ${HQ_CRF} -pix_fmt yuv420p10le \
  -x265-params "$X265" -tag:v hvc1 \
  -c:a libopus -b:a 40k -ac 1 -application audio -map 0:v -map 1:a -shortest -movflags +faststart "$OUT/the-last-witness_hq.mp4" &
HQ_PID=$!
# Compact (< 15 MB): 540x960, 15 fps, HEVC 10-bit two-pass, Opus 16 kbps mono
TARGET_MB=${TARGET_MB:-14.5}
ABR=16
VBR=$(python3 -c "print(int(($TARGET_MB*8e6*0.985 - $ABR*1000*$DUR) / $DUR / 1000))")
echo "compact video bitrate: ${VBR} kbps"
VF="scale=540:960:flags=lanczos,fps=15"
ffmpeg -y -loglevel error -i build/master.mkv -vf "$VF" -c:v libx265 -preset slow -b:v ${VBR}k -pix_fmt yuv420p10le \
  -x265-params "pass=1:stats=build/x265_compact.log:$X265" -an -f null -
ffmpeg -y -loglevel error -i build/master.mkv -i build/audio/mix.wav -vf "$VF" -c:v libx265 -preset slow -b:v ${VBR}k -pix_fmt yuv420p10le \
  -x265-params "pass=2:stats=build/x265_compact.log:$X265" -tag:v hvc1 \
  -c:a libopus -b:a ${ABR}k -ac 1 -application audio -map 0:v -map 1:a -shortest -movflags +faststart "$OUT/the-last-witness_compact.mp4"

wait $HQ_PID
ls -la "$OUT"
