#!/usr/bin/env bash
# Builds the film end to end.
#   ./build.sh <workdir> [target_MB]
# <workdir> must contain models/ (kokoro-v1.0.onnx, voices-v1.0.bin) and
# tools/Rhubarb-Lip-Sync-1.13.0-Linux/. Needs ffmpeg, fluidsynth + FluidR3_GM.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
WORK="$(cd "$1" && pwd)"
TARGET_MB="${2:-13.8}"
OUT_DIR="$HERE/output"
JOBS="${JOBS:-4}"
AUDIO_KBPS="${AUDIO_KBPS:-80}"
mkdir -p "$OUT_DIR" "$WORK/video"

echo "== voices"
python3 "$HERE/voices.py" "$WORK" 2>&1 | grep -vi warn
echo "== score + sound"
python3 "$HERE/audio.py" "$WORK"

DUR=$(python3 -c "import json;print(json.load(open('$WORK/timeline.json'))['duration'] + 0.6)")
FRAMES=$(python3 -c "import math;print(math.ceil($DUR*24))")
echo "== render $FRAMES frames in $JOBS parts"
rm -f "$WORK"/video/part_*.mkv "$WORK/video/parts.txt"
CHUNK=$(( (FRAMES + JOBS - 1) / JOBS ))
for i in $(seq 0 $((JOBS - 1))); do
  F0=$(( i * CHUNK )); F1=$(( (i + 1) * CHUNK )); [ $F1 -gt $FRAMES ] && F1=$FRAMES
  node "$HERE/anim/render.js" "$WORK/timeline.json" video "$WORK/video/part_$i.mkv" $F0 $F1 &
  echo "file '$WORK/video/part_$i.mkv'" >> "$WORK/video/parts.txt"
done
wait
ffmpeg -v error -y -f concat -safe 0 -i "$WORK/video/parts.txt" -c copy "$WORK/video/master.mkv"

echo "== loudness"
ffmpeg -v error -y -i "$WORK/audio/mix_raw.wav" -af "loudnorm=I=-15:TP=-1.5:LRA=11" -ar 48000 "$WORK/audio/mix.wav"

echo "== encode (two-pass, target ${TARGET_MB} MB)"
# decimal megabytes, ~3% left for container overhead
VKBPS=$(python3 -c "print(int(($TARGET_MB*8000/$DUR - $AUDIO_KBPS)*0.97))")
echo "video bitrate ${VKBPS}k"
X264="aq-mode=3:aq-strength=0.9:ref=6:bframes=8:b-adapt=2:direct=auto:me=umh:subme=10:trellis=2:psy-rd=0.8,0.0:deblock=1,1:keyint=240:min-keyint=24"
cd "$WORK/video"
ffmpeg -v error -y -i master.mkv -an -c:v libx264 -preset veryslow -tune animation -profile:v high -pix_fmt yuv420p \
  -b:v ${VKBPS}k -maxrate 1400k -bufsize 2800k -x264-params "$X264" -pass 1 -f mp4 /dev/null
ffmpeg -v error -y -i master.mkv -i "$WORK/audio/mix.wav" -map 0:v -map 1:a -c:v libx264 -preset veryslow -tune animation \
  -profile:v high -pix_fmt yuv420p -b:v ${VKBPS}k -maxrate 1400k -bufsize 2800k -x264-params "$X264" -pass 2 \
  -c:a aac -b:a ${AUDIO_KBPS}k -ac 2 -shortest -movflags +faststart \
  -metadata title="Yeah. I know." "$OUT_DIR/yeah-i-know.mp4"
cp "$WORK/captions.srt" "$OUT_DIR/yeah-i-know.srt"
ls -la "$OUT_DIR"
ffprobe -v error -show_entries format=duration,size,bit_rate -of default=nw=1 "$OUT_DIR/yeah-i-know.mp4"
