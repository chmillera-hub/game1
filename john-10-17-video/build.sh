#!/bin/bash
# End-to-end build. Assets (Poly Haven CC0, NASA earth maps, fonts, Kokoro model) live in $SCRATCH/assets and $SCRATCH/tts.
set -euo pipefail
cd "$(dirname "$0")"
SCRATCH=${SCRATCH:-/tmp/claude-0/-home-user-game1/2b62858c-fbb0-5a8d-a052-11a01031b8ed/scratchpad}
export SCRATCH
mkdir -p "$SCRATCH/audio" "$SCRATCH/out"
python3 -I audio/tts.py "$SCRATCH/tts" "$SCRATCH/audio"             # narration + script/timeline.json
python3 -I script/plan_shots.py                                    # script/shots.json
python3 -I audio/music.py "$SCRATCH/audio/music.wav"                # original score
python3 -I audio/mix.py "$SCRATCH/audio/narration.wav" "$SCRATCH/audio/music.wav" "$SCRATCH/audio/mix.wav"
node render/render.js frames all                                   # 3D frames (headless Chromium)
python3 -I render/compose.py "$SCRATCH/out/frames" "$SCRATCH/assets/fonts" "$SCRATCH/audio/mix.wav" "$SCRATCH/out/master.mp4"
render/deliver.sh "$SCRATCH/out/master.mp4" john-10-17.mp4
