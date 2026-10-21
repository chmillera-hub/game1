#!/usr/bin/env bash
# Rebuild "Clickety-Clack!":  sung vocals -> band & mix -> frames -> clickety_clack.mp4
# Needs: python3.12 with kokoro, torch (cpu), pyworld, soundfile, scipy, numpy, pycairo, pillow; ffmpeg with libx264.
set -euo pipefail
cd "$(dirname "$0")"

mkdir -p ~/.fonts && cp -n ../alice_ghost_video/assets/fonts/*.ttf ~/.fonts/ && fc-cache -f >/dev/null

python sing.py           # speech -> singing (WORLD vocoder), timeline, lip-sync
python music.py          # the band, effects and the mix
rm -rf build/segments
python render.py         # Cairo frames -> lossless segments (parallel)
python encode.py "${1:-14.2}"   # two-pass H.264/AAC portrait MP4 sized to fit (MB) + .srt
