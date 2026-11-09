#!/usr/bin/env bash
# Rebuild the whole soundtrack from the current timeline: SFX library (if missing) -> SFX events -> score -> mix.
#   tools/build_audio.sh            # uses data/timeline.json (run tools/build_timeline.py after TTS first)
#   tools/build_audio.sh --replan   # also re-derive data/music_plan.json from the screenplay
# Output: out/mix.wav (what tools/encode.sh muxes). See docs/AUDIO.md.
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f audio/sfx/meta.json ] || python3 audio/sfx.py
python3 tools/collect_sfx.py
python3 audio/music.py "$@"
python3 audio/mix.py
