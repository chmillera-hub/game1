#!/usr/bin/env bash
# Full pipeline: voices -> frames -> score/mix -> final compressed MP4 (+ SRT).
# Needs: python3 with pycairo numpy scipy soundfile kokoro-onnx, ffmpeg, and the Kokoro model in $KOKORO_DIR.
set -euo pipefail
export CZ_BUILD=${CZ_BUILD:-/tmp/cz-build}
export KOKORO_DIR=${KOKORO_DIR:-$CZ_BUILD/kokoro}
mkdir -p "$CZ_BUILD"
cd "$(dirname "$0")"
python3 tts.py "$CZ_BUILD"                 # voices + timeline.json
WORKERS=${WORKERS:-4} python3 render.py video   # frames -> $CZ_BUILD/video.mp4 (high quality intermediate)
python3 audio.py                           # score + sound design + mix -> $CZ_BUILD/mix.wav
python3 srt.py the-first-witness.srt
BR=${VBR:-318k}
ffmpeg -y -i "$CZ_BUILD/video.mp4" -c:v libx264 -preset veryslow -tune animation -b:v $BR -pass 1 \
  -x264-params keyint=240:min-keyint=24:aq-mode=3 -an -f mp4 /dev/null
ffmpeg -y -i "$CZ_BUILD/video.mp4" -i "$CZ_BUILD/mix.wav" -c:v libx264 -preset veryslow -tune animation -b:v $BR -pass 2 \
  -x264-params keyint=240:min-keyint=24:aq-mode=3 -pix_fmt yuv420p -profile:v high \
  -af "loudnorm=I=-14.5:TP=-3:LRA=7,alimiter=limit=0.68:level=false" -c:a aac -b:a 64k -ar 48000 -movflags +faststart -shortest the-first-witness.mp4
