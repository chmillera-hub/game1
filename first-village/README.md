# The First Village — animated short (portrait, ~4:18)

A 720×1280 (9:16) animated parable of Moses: the village of straight lines, the Elder,
the speech about cracked vessels, the exile, and the presence that says *"I see you."*
Everything (pictures, voices, music and sound effects) is generated from code in this folder.

`the_first_village.mp4` is the finished film: H.264 + AAC, 24 fps, under 15 MB.

## Pipeline

| step | file | output |
|---|---|---|
| beat sheet: every line, pause and scene marker | `script.py` | — |
| voices (Kokoro TTS) + character FX + Whisper check + timeline | `make_voices.py` | `build/voices/*.wav`, `build/timeline.json` |
| score, sound design, ducking, mix | `make_audio.py` | `build/mix.wav` (+ stems) |
| animation (skia), captions | `render.py`, `scenes.py`, `rig.py`, `sets.py`, `cast.py`, `anim.py` | `build/video_master.mkv` |
| size-targeted encode | `encode.py` | `build/the_first_village.mp4` |

The timeline is driven by the real voice durations, so editing a line in `script.py` and
re-running the build re-times every shot, caption and music cue automatically.

## Rebuild

```sh
pip install kokoro-onnx skia-python scipy soundfile faster-whisper
# Skia needs libEGL (apt install libegl1); ffmpeg must be on PATH.
mkdir -p models && cd models
curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
cd .. && ./build.sh
```

Fonts (Cinzel, Cormorant Garamond) are from Google Fonts, under the SIL Open Font License.

## Common tweaks

- **Change dialogue / narration / pauses:** edit `script.py`, then `python3 make_voices.py --force`
  (or delete just the changed `build/voices/<id>_dry.wav`).
- **Voices:** `VOICES` in `script.py` (Kokoro voice names, blends and speed).
- **No burned-in captions:** `CAPTIONS=0 python3 render.py`.
- **Preview single frames:** `python3 render.py --test 12.5 90 205` → `build/test/`.
- **Different size budget:** `python3 encode.py --target-mb 9 --audio-kbps 48`.
- **Shots, expressions, gestures:** each scene is a function in `scenes.py`; a character's
  face/pose is a dict of parameters (`lid`, `worry`, `anger`, `smile`, `gx`/`gy` gaze, `arm_l`…)
  documented in `rig.py`.
