#!/bin/bash
# Full pipeline: voices -> audio mix -> parallel frame render -> final compressed MP4.
set -e
cd "$(dirname "$0")"
: "${WORK:?set WORK to a scratch directory}"
: "${KOKORO_DIR:?set KOKORO_DIR to the folder holding kokoro-v1.0.onnx and voices-v1.0.bin}"
OUTMP4=${OUTMP4:-psalm22_why_have_you_forsaken_me.mp4}
VBR=${VBR:-380k}
[ -f "$WORK/voice/meta.json" ] || python3 tts.py
python3 audio.py
NF=$(python3 -c "import timeline as T; print(int(T.TOTAL*T.FPS))")
J=${JOBS:-4}
PARTS=${PARTS:-8}
STEP=$(( (NF + PARTS - 1) / PARTS ))
: > "$WORK/parts.txt"
for k in $(seq 0 $((PARTS-1))); do
  A=$((k*STEP)); B=$(( (k+1)*STEP < NF ? (k+1)*STEP : NF ))
  echo "$A $B $WORK/part$k.mkv"
  echo "file '$WORK/part$k.mkv'" >> "$WORK/parts.txt"
done | xargs -P "$J" -L 1 sh -c 'python3 render.py "$0" "$1" "$2" > "$2.log" 2>&1'
ffmpeg -v error -y -f concat -safe 0 -i "$WORK/parts.txt" -c copy "$WORK/video_lossless.mkv"
# loudness-normalised AAC
ffmpeg -v error -y -i "$WORK/mix.wav" -af loudnorm=I=-15:TP=-1.5:LRA=11 -ar 48000 -c:a aac -b:a ${ABR:-72k} "$WORK/audio.m4a"
X264="-c:v libx264 -preset veryslow -tune animation -profile:v high -level 4.0 -pix_fmt yuv420p -g 240 -keyint_min 24 -x264-params aq-mode=3:aq-strength=0.9:deblock=1,1"
ffmpeg -v error -y -i "$WORK/video_lossless.mkv" $X264 -b:v $VBR -pass 1 -passlogfile "$WORK/x264" -an -f mp4 /dev/null
ffmpeg -v error -y -i "$WORK/video_lossless.mkv" -i "$WORK/audio.m4a" $X264 -b:v $VBR -pass 2 -passlogfile "$WORK/x264" \
  -c:a copy -map 0:v -map 1:a -movflags +faststart -shortest "$OUTMP4"
ls -la "$OUTMP4"
