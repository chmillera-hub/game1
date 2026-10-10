#!/bin/sh
# Full rebuild: voices -> mix -> frames -> size-targeted MP4.
set -e
cd "$(dirname "$0")"
python3 make_voices.py
python3 make_audio.py
python3 render.py
python3 encode.py "$@"
cp build/the_first_village.mp4 .
