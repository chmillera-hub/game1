# The Bread of Life (John 6) — procedural animated short

A portrait (720×1280, 24 fps) animated short with voice acting, a music score, ambience and
burned-in subtitles. Everything in it, including the voices, is generated from code in this folder.

**Output:** `bread_of_life.mp4`. It runs about 4:56 and is under 15 MB (H.264 + AAC). The first frame is a full image, with no fade from black.

## Story

The scene follows the supplied passages (John 6:26–27, 32–35, 43–45, 51–58) and keeps the supplied wording,
including "not society" and "the disciples". Short scripture-based bridges turn the passages into a conversation:

| Scene | Content |
|---|---|
| Capernaum shore, morning | The crowd comes ashore and finds Jesus alone on the beach (6:24–25). Eli asks how he got there when he was on none of the boats, and Jesus answers only that his Father willed it. He gives the teaching on food that spoils (6:26–27). Peter asks what work God requires (6:28–29). Eli asks for a sign, citing the manna (6:30–31). Jesus answers about the true bread (6:32–33). Miriam asks "Sir… how do we get this bread?", and Jesus answers "I am the bread of life" (6:34–35). |
| Synagogue at Capernaum | The grumbling over "the son of Joseph" (6:41–42) leads to "Stop grumbling…" (6:43–45) and "I am the living bread…" (6:51). The disciples argue (6:52), and Jesus says "unless you eat the flesh…" (6:53–58). |
| Shore at sunset (coda) | "This is a hard teaching" (6:60). Many turn back (6:66). Jesus asks "You do not want to leave too?" and Peter answers "To whom shall we go?" (6:67–69). Jesus breaks the bread and places half in Peter's hand, then prays over his half for those who stayed and those who left, while the end title rises. |

## Pipeline

| File | Role |
|---|---|
| `script.py` | Screenplay: lines split into breath-group segments, plus pauses and voice casting |
| `tts.py` | Voice acting with Kokoro-82M (timestamped ONNX export). Writes per-phoneme timings for lip sync and subtitle timing |
| `timeline.py` | Absolute timing of every line, segment and word |
| `rig.py`, `hair.py`, `body.py`, `chars.py` | 2.5D anime-style character rig. The head is rotatable, built from 3D anchors and a cross-section silhouette. It has layered eyes (iris, pupil, catchlights, gaze-following lids, lashes, tears), brows, a viseme mouth, beards, hair and head-cloths. Bodies are full length: robes to the hem, lower legs with sandals and contact shadows, and 3D two-bone IK arms whose elbows drop naturally (and swing out when a hand rises to the head). The upper arm and forearm are drawn in depth order so a nearer forearm hides the arm behind it. Hands are modelled in 3D: a palm slab, fingers as jointed capsules and a thumb that curves across the palm or over a held object, oriented from a 3D palm direction and drawn back to front through the camera. The palm or back of the hand shows correctly, the thumb sits on the anatomically right side, and props such as the bread sit between the fingers and the thumb (open, relaxed, flat, soft, pointing, holding, fist and cupped poses). Noses have a shaded side plane, nostril wings and nostrils |
| `anim.py` | Performance system: expression presets and keyframes, gaze, head poses and gestures, plus automatic blinks, saccades, breathing, idle sway, speech-driven nods and brow lifts, and phoneme lip sync |
| `direction.py` | Shot list (63 shots), gesture vocabulary per framing, and the acting direction for every character |
| `bg.py`, `fx.py`, `extras.py` | Painted backgrounds, light rays, dust, bokeh, colour grades, props and backlit walking figures. `extras.py` draws a live crowd: each member is a full-body variant of the rig with its own behaviour (looking between the speaker and neighbours, blinking, whispering, reacting, gesturing in an uproar) |
| `subs.py` | Subtitles and titles. Jesus' words use a warm tint, narration is italic |
| `music.py` | 18 MIDI score cues rendered with FluidSynth (FluidR3 GM) through a convolution hall reverb, plus a few accents: deep low notes under the weightiest words and high string-and-choir swells where Jesus lifts his eyes to the Father |
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

To preview a single frame: `python3 render.py frame 105.5 out.png`. To preview several: `python3 render.py frames out.png 14 60 142`.
`python3 test_body.py out.png` draws a full-body gesture test sheet.
