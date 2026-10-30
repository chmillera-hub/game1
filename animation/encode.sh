#!/usr/bin/env bash
# Encode build/video_nosound.mp4 + build/mix.wav into portrait MP4s under a size target.
set -euo pipefail
cd "$(dirname "$0")"
TARGET_MB=${TARGET_MB:-14.6}
ABR=${ABR:-64}
DUR=$(python3 -c "import json;print(json.load(open('build/schedule.json'))['duration'])")
VBR=$(python3 -c "print(int(($TARGET_MB*8*1000 - $DUR*$ABR*1.02) / $DUR))")
echo "duration ${DUR}s -> video ${VBR} kbps, audio ${ABR} kbps"
SRC=build/video_nosound.mp4
VF="scale=720:1280:flags=lanczos"
ffmpeg -y -loglevel error -i "$SRC" -vf "$VF" -c:v libx265 -preset slow -b:v "${VBR}k" -tag:v hvc1 \
  -x265-params "pass=1:stats=build/x265.log:log-level=error" -an -f mp4 /dev/null
ffmpeg -y -loglevel error -i "$SRC" -i build/mix.wav -vf "$VF" -c:v libx265 -preset slow -b:v "${VBR}k" -tag:v hvc1 \
  -x265-params "pass=2:stats=build/x265.log:log-level=error" -pix_fmt yuv420p \
  -c:a aac -b:a "${ABR}k" -ac 2 -ar 48000 -movflags +faststart -shortest build/the_family_inside.mp4
ffmpeg -y -loglevel error -i "$SRC" -vf "$VF" -c:v libx264 -preset veryslow -tune animation -b:v "${VBR}k" \
  -pass 1 -passlogfile build/x264 -an -f mp4 /dev/null
ffmpeg -y -loglevel error -i "$SRC" -i build/mix.wav -vf "$VF" -c:v libx264 -preset veryslow -tune animation -b:v "${VBR}k" \
  -pass 2 -passlogfile build/x264 -pix_fmt yuv420p -profile:v high \
  -c:a aac -b:a "${ABR}k" -ac 2 -ar 48000 -movflags +faststart -shortest build/the_family_inside_h264.mp4
ls -la build/the_family_inside*.mp4
