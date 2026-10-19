#!/usr/bin/env bash
# Rebuild "Alice" end to end:  voices -> timeline -> score & mix -> frames -> alice.mp4
# Needs: python3.12 with kokoro, torch (cpu), soundfile, scipy, numpy, pycairo, pillow; ffmpeg with libx264.
set -euo pipefail
cd "$(dirname "$0")"

mkdir -p ~/.fonts && cp -n assets/fonts/*.ttf ~/.fonts/ && fc-cache -f >/dev/null

python voice.py          # Kokoro TTS for every line (cached by text + voice settings)
python timeline.py       # when every line, word, shot, emotion and action lands
python audio.py          # original waltz score, stingers, sound effects, mix + lip-sync data
rm -rf build/segments
python render.py         # Cairo frames -> lossless segments (parallel)
python encode.py "${1:-14.2}"   # two-pass H.264/AAC portrait MP4 sized to fit (MB) + alice.srt
