# Bunny Girl and Wolf Dog: animated read-along

There are two versions of the video. Both are portrait 1080×1920 (9:16) for phones, 30 fps, 1 min 44 s, under 15 MB, H.264 + AAC with faststart. Both share the same child-like rhyming narration, original children's tune and word-by-word read-along captions.

- **`Bunny_Girl_and_Wolf_Dog_Cartoon.mp4`** (the newest): a fully drawn cartoon. Bunny Girl, Wolf Dog, Mom and the five dogs (Cosmo, Pettie, Luna, Mooky and Buddy) are redrawn as cartoon characters inspired by the book's drawings, and they act out every line of the story.
- **`Bunny_Girl_and_Wolf_Dog.mp4`**: the first version, which animates the cleaned-up photos of the book pages.

In both, the first frame is already a full scene (characters and title), so social apps never show a blank square.

## What happens in the cartoon

| Time | Story | What the characters do |
| --- | --- | --- |
| 0:00 | Title | Bunny Girl and Wolf Dog hold hands and bounce to the music; Wolf Dog dashes off |
| 0:03 | Meet Bunny Girl | She waves, jumps at her name, wiggles her bunny ears, pretends to be a bunny with a real little bunny, Hop! Hop! Hop! |
| 0:18 | The doggy park | Mom and Bunny Girl bring the dogs; each dog jumps and gets a name tag; Mooky and Buddy zoom by |
| 0:30 | Wolf Dog | He waits, they play catch, he gets shy and turns invisible; Mom and the dogs can't see him; he hides behind a bush... Peek-a-boo! |
| 0:47 | The wish and the hug | A thought bubble of everyone playing; a lightbulb idea; a big snuggly hug and hearts; "And suddenly..." he glows |
| 1:07 | POOF! | Smoke, confetti, and Wolf Dog can be seen! Mom is amazed and the dogs run up to play |
| 1:20 | Always together | Rain (umbrella), snow, a rainbow; the whole family together for a photo |
| 1:33 | The End | Hug a shy friend and say hi; a big heart; "The End"; everyone runs in to play |

## What's in here

| Path | What it is |
| --- | --- |
| `scripts/story.py` | The rhyming read-aloud text: **edit this to change any line** |
| `scripts/toon.py`, `scripts/toon_world.py` | The cartoon characters, scenery and effects (vector drawing) |
| `scripts/render_cartoon.py` | The cartoon's scenes and acting, timed to the spoken words |
| `scripts/*.py` | The rest of the build pipeline (see below) |
| `source_pages/` | The original phone photos of the Kindle Create pages |
| `art/` | Cleaned illustrations used by the first version |
| `fonts/` | Chewy (Apache-2.0), Fredoka, Baloo 2, Lilita One, Sniglet (SIL OFL), with their licences |

## Rebuild after changing the words

```bash
python scripts/make_voice.py              # narration + word timings (build/)
python scripts/make_audio.py --cartoon    # music, sound effects, final mix
python scripts/render_cartoon.py          # cartoon frames -> build/cartoon_noaudio.mp4
python scripts/encode.py --cartoon        # final MP4 under 15 MB (--mb to change the target)
```

The scenes follow the spoken word timings, so they stay in sync when a line changes.

`python scripts/render_cartoon.py --preview 0 45.4 67.9` writes still frames to `build/cpreview/` for a quick look.

The first version is built with `extract_art.py`, `make_cutouts.py`, `make_audio.py` (without `--cartoon`), `render_video.py` and `encode.py`.

**Requirements:**

- Python 3.12 with: `kokoro`, `torch` (the CPU build is enough), `skia-python`, `soundfile`, `opencv-python-headless`, `scipy`, `mido`, `numpy`, `pillow`, and the spaCy `en_core_web_sm` model.
- System packages: `ffmpeg`, `fluidsynth`, `fluid-soundfont-gm` and `rubberband-cli`.

## Credits and licences

- **Story and characters:** the author. The cartoon characters are drawn after her illustrations.
- **Voice:** [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) (Apache-2.0), voice `af_heart`, shifted up to a child's pitch and timbre.
- **Music:** an original tune written for this video, played with the FluidR3 GM soundfont (MIT).
