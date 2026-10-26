#!/usr/bin/env bash
# Renders the film, synthesizes the score from the film's cues, and muxes them.
#   ./build.sh            -> statistically-likely.mp4 + soundtrack.m4a
set -euo pipefail
cd "$(dirname "$0")"
BUILD="${OUT_DIR:-build}"
mkdir -p "$BUILD"

OUT_DIR="$BUILD" node render.mjs
python3 audio.py "$BUILD/events.json" "$BUILD/soundtrack.wav"

ffmpeg -y -loglevel error -i "$BUILD/soundtrack.wav" -c:a aac -b:a 192k soundtrack.m4a
ffmpeg -y -loglevel error -f concat -safe 0 -i "$BUILD/segments.txt" -i soundtrack.m4a \
  -map 0:v -map 1:a -c:v copy -c:a copy -movflags +faststart -shortest statistically-likely.mp4
echo "done: $(du -h statistically-likely.mp4 | cut -f1) statistically-likely.mp4"
