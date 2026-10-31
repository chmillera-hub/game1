#!/bin/bash
# Joins the rendered scene segments, adds the synthesized soundtrack, and writes the final MP4.
# usage: ./assemble.sh <segs dir> <out.mp4> [crf]
set -euo pipefail
SEGS="$1"; OUT="$2"; CRF="${3:-24}"
HERE="$(cd "$(dirname "$0")" && pwd)"
: > "$SEGS/list.txt"
for f in $(ls "$SEGS"/seg*.mp4 | sort); do echo "file '$(realpath "$f")'" >> "$SEGS/list.txt"; done
ffmpeg -y -v error -f concat -safe 0 -i "$SEGS/list.txt" -c copy "$SEGS/joined.mp4"
python3 "$HERE/soundtrack.py" "$SEGS" "$SEGS/soundtrack.wav"
ffmpeg -y -v error -i "$SEGS/joined.mp4" -i "$SEGS/soundtrack.wav" -map 0:v -map 1:a \
  -c:v libx264 -preset slow -crf "$CRF" -tune animation -pix_fmt yuv420p \
  -c:a aac -b:a 160k -shortest -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration,size,bit_rate -of default=nw=1 "$OUT"
