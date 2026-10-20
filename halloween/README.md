# TOO MOM — a Halloween tale

A spooky-sweet animated short (portrait 1080×1920, ~5 min) made from a child's
pencil drawing: five pencil mice, three striped pumpkins, a flower, a little
girl, and the words **TOO MOM I LOVE YOU**.

On Halloween night the drawing wakes up. A cynical black cat tells the mice
that drawings get thrown away; the mice decide the "TOO" was never a mistake
("I love you, *too*"); a horned monster on the stairs turns out to be Mom in
hair curlers — and she answers: *"I love you too, baby. With two O's."*

The finished video is `out/too_mom_halloween.mp4`.

## How it is made

Everything is generated from code — no stock art, music or footage.

| Step | File | What it does |
| --- | --- | --- |
| Script | `story.py` | Screenplay, cast, and `^hopeful` / `_heavy` word marks |
| Voices | `voices.py` | Kokoro TTS per line (+ pitch shaping), word timestamps |
| Timeline | `timeline.py` | Absolute timing, lip-sync envelopes and visemes |
| Characters | `mice.py`, `cat.py`, `mom.py` | Posable puppets: brows, lids, pupils, mouths, ears, limbs |
| Sets | `sets.py`, `letters.py` | Crooked moonlit kitchen, clock, stairs, fridge, house, the drawing |
| Acting | `anim.py`, `shots.py` | Keyframes, blinks, breathing, emphasis on stressed words, cameras |
| Frames | `views.py`, `subs.py`, `render.py` | Skia rendering, karaoke subtitles, stop-motion "on twos" |
| Sound | `synth.py`, `audio.py` | Original score + SFX, high/low notes on marked words, ducking |
| Encode | `encode.py` | Two-pass H.264 + AAC under 15 MB, SSIM check vs. lossless master |

Rebuild (Python 3.12+, ffmpeg with libx264 + librubberband):

```bash
pip install kokoro misaki[en] soundfile scipy skia-python numpy
python3 voices.py          # ~2.5 min on CPU
python3 audio.py           # score + mix -> build/mix.wav
python3 render.py --workers 4
python3 encode.py --target-mb 14.4
```

## Style notes

Gothic stop-motion storybook mood: spirals, stripes, crooked architecture, a
huge pale moon, spindly limbs, dark-ringed eyes, pale paper puppets lit by
jack-o'-lantern orange. All designs are original; no characters, symbols,
scenes or music from any existing film are used.

## Credits & licences

- Voices: [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) (Apache-2.0)
- Fonts: Fredoka and Griffy (SIL Open Font License, see `assets/fonts/OFL_*.txt`)
- Story, art, animation, music and sound design: generated for this project
