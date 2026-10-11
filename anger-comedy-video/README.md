# Anger Goes to a Comedy Show

A 4:54 portrait (720×1280, 9:16) animated short adapted from the "Gemini bot stand-up / Anger meltdown"
story in `Tef_Claude_humor_112224_1.pdf` (items 7 and 11–16).

* **Video:** `anger_goes_to_a_comedy_show.mp4`: H.264 + AAC (mono, 64 kbps), about 13.5 MB, starts on a
  title frame (no fade-in from black), with burned-in captions.
* **Script with timestamps:** `SCRIPT.md`

Everything is generated from code. There is no stock footage or audio:

| file | what it does |
|---|---|
| `src/screenplay.py` | the script: every line, camera shot, facial expression, gesture and sound cue |
| `src/rig.py` | the character rig: eyes, eyelids, brows, mouth shapes, sweat, tears, arms (IK), poses |
| `src/robot.py` | the comedian robot with an LED screen face (no real logos or branding) |
| `src/sets.py` | the theater audience rows and the stage |
| `src/timeline.py` | keyframes plus "life" layers: auto-blinks, eye darts, breathing, lip-sync, walking |
| `src/tts.py` | voices (Kokoro TTS) with shout, whisper and robot effects, plus lip-sync envelopes |
| `src/music.py` | synthesized score and sound effects, ducking and the final mix |
| `src/render.py` / `src/build.py` | frame rendering and the size-targeted two-pass encode |

## Rebuilding

```bash
apt-get install -y libegl1            # needed by skia-python
pip install skia-python kokoro-onnx soundfile numpy
mkdir -p models && cd models
curl -LO https://huggingface.co/fastrtc/kokoro-onnx/resolve/main/kokoro-v1.0.onnx
curl -LO https://huggingface.co/fastrtc/kokoro-onnx/resolve/main/voices-v1.0.bin
cd ../src && python3 build.py ../anger_goes_to_a_comedy_show.mp4 --target-mb 13.5
```

A full build takes about 10 minutes on 4 cores.

## Easy changes

* **Voices:** edit `VOICES` in `src/tts.py`. For example, set `'me'` to `am_michael` for a male narrator.
* **Lines and acting:** edit `src/screenplay.py`. `d.say(...)` adds a line, and `[0.6]` inside the text
  adds a 0.6 s pause. `E(...)` sets an expression, `P(...)`/`R(...)` set poses and hand targets, and
  `K(...)` sets any parameter.
* **File size:** `--target-mb` in `build.py`.
