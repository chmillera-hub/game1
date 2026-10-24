# The One Reading This

A portrait (720x1280) animated short with voice acting, a score and subtitles, built
around one thought experiment: wherever scripture says *Christ* or *Jesus*, read it as
*the one reading this*.

Everything is generated from code: Piper neural voices, a NumPy score, Cairo vector
animation, ffmpeg encoding.

**Finished video:** `output/the-one-reading-this.mp4` (subtitles burned in, plus a
soft subtitle track) and `output/the-one-reading-this.srt`.

## Pipeline

| step | file | what it does |
|---|---|---|
| screenplay | `script.py` | every line: speaker, text, camera shot, facial emotion, hand pose, eye direction, scripture card, music accents |
| voices | `tts.py` | Piper TTS per line (narrator, Maya, Abe), pitch/EQ per character, sentence timings |
| timeline | `timeline.py` | lays lines end to end, subtitles (SRT), mouth envelopes for lip sync |
| score | `music.py` | chord pads, piano, bass, word-synced bells (hopeful words) and low cello (heavy words), ducking under dialogue, rain |
| motion | `state.py` | per-frame face/body/camera state: blinks, eyelids, brows, gaze, smiles, tears, poses |
| drawing | `chars.py`, `scenes.py`, `visions.py` | the two characters, the kitchen, scripture cards, subtitles, illustrated cutaways |
| render | `render.py` | renders frames in parallel to a near-lossless intermediate |
| encode | `encode.sh` | two-pass H.264 + AAC to a size budget (default 14.2 MB) |

## Rebuild

```sh
pip install piper-tts pycairo numpy pillow
# download voices en_GB-alan-medium, en_US-lessac-high, en_US-ryan-high
# from huggingface.co/rhasspy/piper-voices into ./voices (or set VOICES=...)
python3 tts.py && python3 timeline.py && python3 music.py
python3 state.py && python3 render.py video && ./encode.sh
python3 render.py stills 0 62 336   # preview single frames
```

To change a moment, edit its line in `script.py` (text, `shot`, `m`/`a` emotion,
`mp`/`ap` pose, `cues`) and rebuild.
