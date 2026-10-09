#!/usr/bin/env bash
# usage: encode.sh <framesDir> <buildDir> <out.mp4> [videoKbps]
set -euo pipefail
FR=$1; BD=$2; OUT=$3; VK=${4:-380}
venc=(-c:v libx264 -preset veryslow -tune animation -b:v ${VK}k -maxrate $((VK * 3))k -bufsize $((VK * 4))k
      -pix_fmt yuv420p -g 240 -profile:v high)
ffmpeg -y -hide_banner -loglevel error -framerate 24 -i "$FR/f%06d.jpg" "${venc[@]}" -pass 1 -passlogfile /tmp/x264pass -an -f mp4 /dev/null
ffmpeg -y -hide_banner -loglevel error -framerate 24 -i "$FR/f%06d.jpg" -i "$BD/mix.wav" -map 0:v -map 1:a \
  "${venc[@]}" -pass 2 -passlogfile /tmp/x264pass -c:a aac -b:a 64k -ar 44100 -shortest -movflags +faststart "$OUT"
ls -l "$OUT"
