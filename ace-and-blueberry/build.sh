#!/usr/bin/env bash
# Rebuilds Ace_and_Blueberry.mp4 from scratch.
# Needs: python3, node, ffmpeg (with libx264), internet (first run only: TTS model + fonts).
set -euo pipefail
cd "$(dirname "$0")"

# --- one-time setup -------------------------------------------------------
[ -d venv ] || { python3 -m venv venv && ./venv/bin/pip install -q kokoro-onnx soundfile numpy scipy fonttools; }
mkdir -p models fonts
[ -f models/kokoro-v1.0.onnx ] || curl -sSL -o models/kokoro-v1.0.onnx https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
[ -f models/voices-v1.0.bin ]  || curl -sSL -o models/voices-v1.0.bin  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
if [ ! -f fonts/Fredoka-Bold.ttf ]; then
  curl -sSL -o fonts/Fredoka.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/fredoka/Fredoka%5Bwdth,wght%5D.ttf"
  curl -sSL -o fonts/LuckiestGuy-Regular.ttf https://raw.githubusercontent.com/google/fonts/main/apache/luckiestguy/LuckiestGuy-Regular.ttf
  ./venv/bin/fonttools varLib.instancer fonts/Fredoka.ttf wght=600 wdth=100 -o fonts/Fredoka-SemiBold.ttf
  ./venv/bin/fonttools varLib.instancer fonts/Fredoka.ttf wght=700 wdth=100 -o fonts/Fredoka-Bold.ttf
fi
[ -d render/node_modules ] || (cd render && npm install --silent)

# --- build ----------------------------------------------------------------
[ "${SKIP_TTS:-0}" = 1 ] || ./venv/bin/python -I tts.py   # voices/*.wav (pass line ids to redo only some)
./venv/bin/python -I timeline.py                          # timeline.json (timing + lip-sync)
./venv/bin/python -I audio.py                             # mix.wav (voices + music + sound effects)
(cd render && node main.js video) | ffmpeg -hide_banner -loglevel error -y -f rawvideo -pix_fmt rgba -s 720x1280 -r 24 -i - \
  -c:v libx264 -preset veryfast -crf 6 -pix_fmt yuv444p master.mkv
ffmpeg -hide_banner -loglevel error -y -i master.mkv -i mix.wav -map 0:v -map 1:a \
  -c:v libx264 -preset veryslow -tune animation -crf 25 -profile:v high -level 4.0 -pix_fmt yuv420p -g 240 \
  -c:a aac -b:a 72k -af "loudnorm=I=-15:TP=-2:LRA=11,alimiter=limit=0.8:level=false" -ar 48000 \
  -metadata title="Ace and Blueberry" -movflags +faststart -shortest Ace_and_Blueberry.mp4
ls -la Ace_and_Blueberry.mp4
