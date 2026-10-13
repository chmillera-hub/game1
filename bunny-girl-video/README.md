# Bunny Girl and Wolf Dog: animated read-along

**`Bunny_Girl_and_Wolf_Dog.mp4`** is the finished video:

- Portrait 1080×1920 (9:16) for phones, 30 fps, 1 min 44 s, 14.4 MB.
- H.264 + AAC with faststart.
- The first frame is already the full cover (characters and title), so social apps never show a blank square.
- A child-like voice reads a rhyming version of the story over an original children's tune.
- The captions highlight each word as it is read.

## What's in here

| Path | What it is |
| --- | --- |
| `source_pages/` | The original phone photos of the Kindle Create pages |
| `art/` | Cleaned illustrations (moiré removed, straightened, colours restored), plus character cutouts and background plates |
| `scripts/story.py` | The rhyming read-aloud text: **edit this to change any line** |
| `scripts/*.py` | The build pipeline (see below) |
| `fonts/` | Chewy (Apache-2.0), Fredoka, Baloo 2, Lilita One, Sniglet (SIL OFL), with their licences |

## Rebuild after changing the words

```bash
python scripts/extract_art.py   # photos -> cleaned art/*.png
python scripts/make_cutouts.py  # characters + background plates
python scripts/make_voice.py    # narration + word timings (build/)
python scripts/make_audio.py    # music, sound effects, final mix
python scripts/render_video.py  # animation frames -> build/video_noaudio.mp4
python scripts/encode.py        # final MP4 under 15 MB (--mb to change the target)
```

`python scripts/render_video.py --preview 0 45.4 67.9` writes still frames to `build/preview/` for a quick look.

**Requirements:**

- Python 3.12 with: `kokoro`, `torch` (the CPU build is enough), `soundfile`, `opencv-python-headless`, `scipy`, `mido`, `numpy`, `pillow`, and the spaCy `en_core_web_sm` model.
- System packages: `ffmpeg`, `fluidsynth`, `fluid-soundfont-gm` and `rubberband-cli`.

## Credits and licences

- **Story and drawings:** the author.
- **Voice:** [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) (Apache-2.0), voice `af_heart`, shifted up to a child's pitch and timbre.
- **Music:** an original tune written for this video, played with the FluidR3 GM soundfont (MIT).
