#!/usr/bin/env bash
# One-time setup: Python packages, the Kokoro TTS voice model, and the cartoon fonts.
set -euo pipefail
cd "$(dirname "$0")"

pip install pycairo numpy scipy soundfile kokoro-onnx

mkdir -p .cache/models
base=https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0
[ -f .cache/models/kokoro-v1.0.onnx ] || curl -L -o .cache/models/kokoro-v1.0.onnx "$base/kokoro-v1.0.onnx"
[ -f .cache/models/voices-v1.0.bin ] || curl -L -o .cache/models/voices-v1.0.bin "$base/voices-v1.0.bin"

mkdir -p ~/.fonts
gf=https://raw.githubusercontent.com/google/fonts/main
curl -sSL -o ~/.fonts/LuckiestGuy-Regular.ttf "$gf/apache/luckiestguy/LuckiestGuy-Regular.ttf"
curl -sSL -o ~/.fonts/Fredoka.ttf "$gf/ofl/fredoka/Fredoka%5Bwdth%2Cwght%5D.ttf"
curl -sSL -o ~/.fonts/Bangers-Regular.ttf "$gf/ofl/bangers/Bangers-Regular.ttf"
curl -sSL -o ~/.fonts/PatrickHand-Regular.ttf "$gf/ofl/patrickhand/PatrickHand-Regular.ttf"
fc-cache -f >/dev/null

echo "Ready. Run: python3 build.py 1 2 3"
