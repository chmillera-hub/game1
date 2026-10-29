#!/bin/bash
# Two-pass delivery encode from the composited master (~45 MB for 3:43 at 720x1280).
set -euo pipefail
IN=$1; OUT=$2; LOG=$(mktemp -d)/x264
ffmpeg -v error -y -i "$IN" -c:v libx264 -preset slow -b:v 1450k -pass 1 -passlogfile "$LOG" -an -f mp4 /dev/null
ffmpeg -v error -y -i "$IN" -c:v libx264 -preset slow -b:v 1450k -maxrate 2600k -bufsize 4000k -pass 2 -passlogfile "$LOG" \
  -pix_fmt yuv420p -c:a aac -b:a 160k -movflags +faststart -metadata title="John 10 & 17" "$OUT"
ls -la "$OUT"
