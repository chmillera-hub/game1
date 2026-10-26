#!/usr/bin/env bash
# Renders the film, voices it, synthesizes the score from the film's cues, and muxes them.
#   ./build.sh            -> statistically-likely.mp4 + soundtrack.m4a
set -euo pipefail
cd "$(dirname "$0")"
BUILD="${OUT_DIR:-build}"
export KOKORO_DIR="${KOKORO_DIR:-$BUILD/kokoro}"
mkdir -p "$BUILD"

OUT_DIR="$BUILD" node render.mjs

if python3 -c "import kokoro_onnx" 2>/dev/null; then
  mkdir -p "$KOKORO_DIR"
  for f in kokoro-v1.0.onnx voices-v1.0.bin; do
    [ -s "$KOKORO_DIR/$f" ] || curl -fsSL -o "$KOKORO_DIR/$f" "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/$f"
  done
  python3 voice.py "$BUILD/events.json" "$BUILD"
  python3 audio.py "$BUILD/events.json" "$BUILD/soundtrack.wav" "$BUILD/narration.wav" "$BUILD/crowd.wav"
else
  echo "kokoro-onnx is not installed (pip install kokoro-onnx), so building without narration"
  python3 audio.py "$BUILD/events.json" "$BUILD/soundtrack.wav"
fi

ffmpeg -y -loglevel error -i "$BUILD/soundtrack.wav" -c:a aac -b:a 192k soundtrack.m4a
ffmpeg -y -loglevel error -f concat -safe 0 -i "$BUILD/segments.txt" -i soundtrack.m4a \
  -map 0:v -map 1:a -c:v copy -c:a copy -movflags +faststart -shortest statistically-likely.mp4
echo "done: $(du -h statistically-likely.mp4 | cut -f1) statistically-likely.mp4"
