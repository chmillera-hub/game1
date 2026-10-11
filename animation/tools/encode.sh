#!/usr/bin/env bash
# Two-pass H.264 encode of out/master_video.mp4 + out/mix.wav to a target size (decimal MB).
#   tools/encode.sh [target_MB=14.5] [audio_kbps=64] [out=out/final.mp4]
set -euo pipefail
cd "$(dirname "$0")/.."
TARGET_MB=${1:-14.5}; AK=${2:-64}; OUT=${3:-out/final.mp4}
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 out/master_video.mp4)
VK=$(python3 -c "print(int(($TARGET_MB*8e6*0.985/ $DUR - $AK*1000)/1000))")
echo "duration ${DUR}s -> video ${VK} kbps + audio ${AK} kbps"
X264="-c:v libx264 -preset veryslow -tune animation -profile:v high -level 4.0 -pix_fmt yuv420p -b:v ${VK}k -maxrate $((VK*3))k -bufsize $((VK*6))k -g 240 -keyint_min 24 -bf 5 -refs 6 -x264-params aq-mode=3:aq-strength=0.9:deblock=-1,-1:psy-rd=0.6,0"
ffmpeg -y -loglevel error -i out/master_video.mp4 $X264 -pass 1 -passlogfile out/x264pass -an -f mp4 /dev/null
ffmpeg -y -loglevel error -i out/master_video.mp4 -i out/mix.wav $X264 -pass 2 -passlogfile out/x264pass \
  -c:a aac -b:a ${AK}k -ac 2 -ar 44100 -movflags +faststart -shortest "$OUT"
ls -la "$OUT"
