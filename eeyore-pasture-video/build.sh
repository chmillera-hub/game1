#!/usr/bin/env bash
# Rebuild "Eeyore & the Pasture" from scratch.
# Requires: python3 (numpy, piper-tts), ffmpeg (with rubberband), node + playwright/chromium.
set -euo pipefail
cd "$(dirname "$0")"
VOICES_DIR="${VOICES_DIR:-$PWD/voices}"
mkdir -p "$VOICES_DIR"
for v in en_GB-cori-high en_GB-semaine-medium en_GB-vctk-medium en_GB-alan-medium; do
  [ -f "$VOICES_DIR/$v.onnx" ] || python3 -m piper.download_voices --data-dir "$VOICES_DIR" "$v"
done
VOICES_DIR="$VOICES_DIR" python3 tts.py      # dialogue -> build/voice.wav + build/timeline.json
python3 music.py                              # score + sfx + ducking -> build/mix.wav
rm -rf build/frames
node render.js video build/frames "${WORKERS:-4}"   # animation -> build/frames/seg*.mp4
ffmpeg -y -loglevel error -f concat -safe 0 -i build/frames/list.txt -i build/mix.wav \
  -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart eeyore-and-the-pasture.mp4
echo "done -> eeyore-and-the-pasture.mp4"
