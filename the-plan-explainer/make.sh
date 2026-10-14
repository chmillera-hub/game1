#!/usr/bin/env bash
# Rebuild THE PLAN: narration -> sound cues -> soundtrack -> video.
#
#   ./make.sh                 everything, writes out/the-plan.mp4
#   ./make.sh preview         stop after the soundtrack (enough for index.html)
#   ./make.sh --to 30         any extra flags go to the video step (here: first 30 s only)
set -euo pipefail
cd "$(dirname "$0")"
PY=${PYTHON:-python3}

step() { printf '\n== %s\n' "$*"; }

step "narration (Kokoro TTS, Whisper word timing)"
"$PY" tools/voice.py

step "sound cues from src/scenes.js"
node tools/render.mjs cues

step "soundtrack"
"$PY" tools/audio.py

if [ "${1:-}" = "preview" ]; then
  echo
  echo "Preview ready: open index.html"
  exit 0
fi

step "video"
node tools/render.mjs video "$@"
