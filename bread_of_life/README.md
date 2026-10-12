# The Bread of Life (John 6) — procedural animated short

A portrait (720×1280, 24 fps) animated short with voice acting, a music score, ambience and
burned-in subtitles. Everything in it, including the voices, is generated from code in this folder.

**Output:** `bread_of_life.mp4`. It runs about 4:52 and is under 15 MB (H.264 + AAC). The first frame is a full image, with no fade from black.

## Story

The scene follows the supplied passages (John 6:26–27, 32–35, 43–45, 51–58) and keeps the supplied wording,
including "not society" and "the disciples". Short scripture-based bridges turn the passages into a conversation:

| Scene | Content |
|---|---|
| Capernaum shore, morning | The crowd finds Jesus (6:24–25). He gives the teaching on food that spoils (6:26–27). Peter asks what work God requires (6:28–29). Eli asks for a sign, citing the manna (6:30–31). Jesus answers about the true bread (6:32–33). Miriam says "Sir… always give us this bread", and Jesus answers "I am the bread of life" (6:34–35). |
| Synagogue at Capernaum | The grumbling over "the son of Joseph" (6:41–42) leads to "Stop grumbling…" (6:43–45) and "I am the living bread…" (6:51). The disciples argue (6:52), and Jesus says "unless you eat the flesh…" (6:53–58). |
| Shore at sunset (coda) | "This is a hard teaching" (6:60). Many turn back (6:66). Jesus asks "You do not want to leave too?" and Peter answers "To whom shall we go?" (6:67–69). The film ends with Jesus breaking bread. |

## Pipeline

| File | Role |
|---|---|
| `script.py` | Screenplay: lines split into breath-group segments, plus pauses and voice casting |
| `tts.py` | Voice acting with Kokoro-82M (timestamped ONNX export). Writes per-phoneme timings for lip sync and subtitle timing |
| `timeline.py` | Absolute timing of every line, segment and word |
| `rig.py`, `hair.py`, `limbs.py`, `chars.py` | 2.5D anime-style character rig. The head is rotatable, built from 3D anchors and a cross-section silhouette. It has layered eyes (iris, pupil, catchlights, lids, lashes, tears), brows, a viseme mouth, beards, hair and head-cloths, and IK arms with hands |
| `anim.py` | Performance system: expression presets and keyframes, gaze, head poses and gestures, plus automatic blinks, saccades, breathing, idle sway, speech-driven nods and brow lifts, and phoneme lip sync |
| `direction.py` | Shot list (58 shots) and the acting direction for every character |
| `bg.py`, `fx.py`, `extras.py` | Painted backgrounds, light rays, dust, bokeh, crowds, colour grades and props |
| `subs.py` | Subtitles and titles. Jesus' words use a warm tint, narration is italic |
| `music.py` | 16 MIDI score cues rendered with FluidSynth (FluidR3 GM) through a convolution hall reverb |
| `audio.py` | Ambience, dialogue reverb and levels, music ducking, mastering to −16 LUFS |
| `render.py` | Frame compositor and parallel renderer |
| `encode.py` | Two-pass x264 encode sized under the 15 MB cap |

## Rebuild

Prerequisites:

```
apt-get install ffmpeg fluidsynth fluid-soundfont-gm espeak-ng fonts-noto-core
pip install skia-python numpy scipy soundfile kokoro-onnx mido pyloudnorm onnxruntime
```

Download the Kokoro model and voices into `$BOL_MODELS`:

- `ts/model.onnx` from `onnx-community/Kokoro-82M-v1.0-ONNX-timestamped`
- `voices-v1.0.bin` from the kokoro-onnx releases

Then run:

```
export BOL_WORK=/path/to/work BOL_MODELS=/path/to/models
python3 tts.py && python3 music.py && python3 audio.py
python3 render.py all && python3 encode.py bread_of_life.mp4
```

To preview a single frame: `python3 render.py frame 105.5 out.png`.
