#!/usr/bin/env bash
# Final encode: H.264 High (plays everywhere: TikTok, Reels, Shorts, X) + AAC.
# usage: BUILD=... ./encode.sh [crf] [out.mp4]
set -euo pipefail
CRF="${1:-26}"
OUT="${2:-$BUILD/the_long_dream.mp4}"
ffmpeg -y -hide_banner -loglevel error -stats \
  -f concat -safe 0 -i "$BUILD/chunks.txt" -i "$BUILD/mix.wav" \
  -map 0:v -map 1:a \
  -c:v libx264 -preset veryslow -tune animation -crf "$CRF" \
  -profile:v high -level 4.2 -pix_fmt yuv420p -r 30 -g 300 -keyint_min 30 \
  -x264-params "aq-mode=3:deblock=-1,-1" \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -c:a aac -b:a 96k -ac 2 -ar 44100 \
  -shortest -movflags +faststart \
  -metadata title="The Long Dream (of a Benefit)" \
  "$OUT"
ls -la "$OUT"
