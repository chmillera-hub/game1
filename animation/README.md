# The Family Inside — procedural animated short

A ~4:50 portrait (9:16) animated short about grief and the "emotional family" inside us
(Anger, Annoyance, Fear, Sadness), rendered entirely from code: voices, lip-sync, acting,
backgrounds, score, sound design and subtitles.

## Build
```
npm install                 # @napi-rs/canvas
pip install kokoro-onnx soundfile scipy
# Kokoro timestamped ONNX model + voice .bin files in $KOKORO_DIR (default /tmp/claude-0/models):
#   huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX-timestamped  (onnx/model.onnx -> model_ts.onnx)
#   huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX              (voices/*.bin)
./build.sh                  # voices -> cues -> score -> mix -> frames -> build/the_family_inside*.mp4
```
Outputs: `build/the_family_inside.mp4` (HEVC, 720x1280, < 15 MB) and
`build/the_family_inside_h264.mp4` (H.264 fallback for older players).

## Where things live
- `audio/script.json` — screenplay (lines, voices, pauses, high/low music words)
- `audio/gen_voices.py`, `audio/tts_engine.py` — TTS with phoneme/word timing
- `audio/music.py`, `audio/sfx.py`, `audio/mix.py` — score, sound effects, final mix
- `src/rig.js`, `src/chars.js`, `src/acting.js` — character rig, cast, expressions/lip-sync/blinks
- `src/bg/*.js` — environments; `src/props.js` — props
- `src/shots.js` — the staging: every shot, camera move and acting beat, timed to the voices
- `src/render.js` — stills, segments, parallel render; `tools/` — preview/review helpers
