# The Long Dream (of a Benefit)

A 4:48 portrait (1080×1920, 30 fps) animated short. Two voices of the public,
Cyan and Gold, work at Window 7, a service counter floating in space. They
watch a constituent who has fallen asleep at the kitchen table halfway through
a benefits application. They talk about what it dreams, what it cannot read
yet, and what they are not allowed to tell it. Then they wake it gently and
tell it a story with citations.

Final video: [`the_long_dream.mp4`](the_long_dream.mp4)

The legal name is never spoken. It appears as a black redaction bar with a soft
chime, so anyone can watch it as if it were addressed to them. Thoughts above
the constituent's clearance come through as static with `**??§§` captions.

## Files

| File | What it does |
| --- | --- |
| `script.py` | Screenplay as data (`[NAME]` and `[GLITCH]` tokens, voices, pauses) |
| `tts.py` | Piper synthesis, best-of-5 takes scored by Whisper, token splicing, word timings |
| `world.py` | Every scene: Window 7, the kitchen, laptop screens, dream bubble, montage, finale |
| `film.py` | Shot schedule, crossfades, title/end cards, captions |
| `audio.py` / `synth.py` | Ambient score, hold music, sound effects, mix, loudness normalization |
| `common.py`, `characters.py`, `cast.py` | Drawing helpers and the expressive character rig |
| `render.py`, `encode.sh`, `preview.py` | Parallel rendering, final encode, single-frame previews |

## Rebuild

```bash
export BUILD=/path/to/build
python3 tts.py && python3 audio.py && python3 render.py 4 && ./encode.sh 29
```
