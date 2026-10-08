#!/usr/bin/env bash
# One-time setup: Python + Node packages, open-licensed fonts, and the Kokoro text-to-speech model.
set -euo pipefail
cd "$(dirname "$0")"
pip install kokoro-onnx soundfile scipy numpy
npm install
mkdir -p .cache/fonts .cache/models
GF=https://raw.githubusercontent.com/google/fonts/main/ofl
curl -sSL -o .cache/fonts/Nunito.ttf        "$GF/nunito/Nunito%5Bwght%5D.ttf"
curl -sSL -o .cache/fonts/Fredoka.ttf       "$GF/fredoka/Fredoka%5Bwdth,wght%5D.ttf"
curl -sSL -o .cache/fonts/PatrickHand.ttf   "$GF/patrickhand/PatrickHand-Regular.ttf"
curl -sSL -o .cache/fonts/JetBrainsMono.ttf "$GF/jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf"
curl -sSL -o .cache/fonts/Caveat.ttf        "$GF/caveat/Caveat%5Bwght%5D.ttf"
K=https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0
[ -f .cache/models/kokoro-v1.0.onnx ] || curl -sSL -o .cache/models/kokoro-v1.0.onnx "$K/kokoro-v1.0.onnx"
[ -f .cache/models/voices-v1.0.bin ]  || curl -sSL -o .cache/models/voices-v1.0.bin  "$K/voices-v1.0.bin"
echo "setup done; run ./build.sh"
