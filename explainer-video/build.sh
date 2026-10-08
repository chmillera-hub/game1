#!/usr/bin/env bash
# Full pipeline: script.json -> voices -> timeline -> sound cues -> music + mix -> frames -> compressed MP4.
#   ./build.sh                  # everything (about 8-10 minutes)
#   TARGET_MB=9 ./build.sh      # smaller file
#   WIDTH=720 ./build.sh        # render at 720x1280 instead of 1080x1920
set -euo pipefail
cd "$(dirname "$0")"
TARGET_MB=${TARGET_MB:-14.3}   # whole-file size target, in MB (1 MB = 1,000,000 bytes)
WIDTH=${WIDTH:-1080}
OUT=${OUT:-how-i-make-videos.mp4}

echo "== 1/5 voices + timeline";   python3 tts.py
echo "== 2/5 sound cues";          node render/main.js --events
echo "== 3/5 music + mix";         python3 audio.py
echo "== 4/5 animation";           node render/main.js --w "$WIDTH" --out build/video_master.mp4

echo "== 5/5 compress"
cd build
# loudness: two-pass normalize to -14 LUFS (what most social apps expect), then AAC
ffmpeg -hide_banner -i mix.wav -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p' > loudnorm.json
LN=$(python3 -c "import json;j=json.load(open('loudnorm.json'));print(f\"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true\")")
ffmpeg -hide_banner -loglevel error -y -i mix.wav -af "$LN" -ar 48000 -c:a aac -b:a 80k audio.m4a
# pick the video bitrate so video + audio lands on TARGET_MB
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 video_master.mp4)
VK=$(python3 -c "print(int(($TARGET_MB*1e6 - $(stat -c %s audio.m4a) - 120000) * 8 / $DUR / 1000))")
echo "   video bitrate: ${VK}k"
X264="-c:v libx264 -preset slow -tune animation -b:v ${VK}k -pix_fmt yuv420p"
ffmpeg -hide_banner -loglevel error -y -i video_master.mp4 $X264 -pass 1 -passlogfile x264pass -an -f mp4 /dev/null
ffmpeg -hide_banner -loglevel error -y -i video_master.mp4 -i audio.m4a $X264 -pass 2 -passlogfile x264pass -c:a copy -movflags +faststart "../$OUT"
cd ..
echo "done: $OUT  $(python3 -c "import os;print(round(os.path.getsize('$OUT')/1e6,2))") MB"
