# The Hit-and-Hide: an animated explainer

A family-friendly, portrait (1080×1920, 9:16) animated explainer about a harmful
pattern: someone hurts you, then makes sure you can't answer back. It covers
online trolls who block after attacking and workplace managers who dismiss you
while being "too busy" to talk. It ends with 15 practical "lenses" for keeping
your dignity without putting your job or safety at risk.

**Output:**
- `output/hit-and-hide-explainer.mp4`: full quality, 1080×1920, about 72 MB
- `output/hit-and-hide-explainer-small.mp4`: 720×1280, about 14 MB, for upload size limits

Both are about 8 minutes long at 30 fps (H.264 video, AAC audio).

Everything is generated from code: the characters, lip sync, voices, music and
sound effects. The first frame is the title card over the animated scene, not a
black screen. Captions are burned in, with the current word highlighted, so the
video works with the sound off. They stay clear of the bottom and right edges,
where TikTok, Reels and Shorts put their buttons.

## Story outline

| Part | What happens |
| --- | --- |
| Hook | Ned dumps a bag of trash on Sam's doorstep, rings the bell and runs off laughing. Lumi (the narrator) names the pattern: **the Hit-and-Hide**. Step 1 is the hit; step 2 is the hide. |
| Online | Cruel comments pile up under Sam's post, then Ned blocks Sam, so Sam can't reply. |
| Advice | Ned gives "helpful" advice, then puts on headphones: "please don't respond." |
| Work | Mr. Marsh brushes off Sam's idea. His door is "always open, just not right now." He criticizes Sam's "attitude" and walks away before Sam can ask what he means. |
| Fear | He controls Sam's paycheck, so the block button becomes fear of losing shifts, reviews, or the job. |
| Systems | Complaint forms vanish, calls sit on hold forever, and speaking up feels risky. *It's not you.* |
| Why it hurts | Two harms at once: the hit, and the silence that follows. |
| The flip | Why run or hide at all? Because what they did wouldn't hold up face to face. Hiding is a way of avoiding accountability. |
| Toolkit | 15 lenses (below). |
| Outro | Affirmations, a gentle crisis-support note, and an end card listing all 15 lenses. |

The 15 lenses: Name it · Pause before you react · Keep a private log · Put it in
writing · Get curious · Use a four-part script · Find your people · Map your
outlets · Ask four quick questions · Vent safely, plan clearly · Stay calm and
boring · Their words are not a verdict · Build a quiet exit ramp · Online? You
owe them nothing · Be the open door.

## How it's made

| File | Role |
| --- | --- |
| `script.py` | The screenplay: every line, who says it, facial expressions, sound cues |
| `voice.py` | Text-to-speech with [Kokoro](https://github.com/thewh1teagle/kokoro-onnx) (five voices), plus a [Whisper](https://github.com/SYSTRAN/faster-whisper) pass that gets word timings for the captions and flags misread lines |
| `timeline.py` | Turns the script into absolute timings and builds the voice track and per-character lip-sync curves |
| `audio.py` | Music synthesized from scratch (five moods: playful, tense, turn, hopeful, warm), sound effects, ducking and the mix |
| `draw.py` | Cairo character rig: eyes with eyelids, pupils and highlights, eyebrows, lip-synced mouths, noodle arms with poses, about 30 expressions |
| `props.py` | Backgrounds and props |
| `engine.py` | Per-frame scene context, captions, transitions |
| `scenes.py` | The animation for each scene |
| `render.py` | Renders frames in parallel and pipes them to ffmpeg |
| `build.py` | Runs every step |

### Rebuild

```bash
pip install pycairo kokoro-onnx soundfile scipy faster-whisper numpy
# Kokoro model files (about 340 MB) go in build/models/
mkdir -p build/models
curl -L -o build/models/kokoro-v1.0.onnx https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
curl -L -o build/models/voices-v1.0.bin  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
# The Fredoka font (Google Fonts, OFL) must be installed for the titles and captions
python3 build.py                 # full build, about 10 minutes on 4 cores
python3 render.py still 12.5     # render a single frame at t=12.5s into build/
```

To make the small copy for upload limits (two-pass encode to about 14 MB):

```bash
cd build
for p in 1 2; do ffmpeg -y -i ../output/hit-and-hide-explainer.mp4 -i mix.wav -map 0:v -map 1:a \
  -vf scale=720:1280:flags=lanczos -c:v libx264 -preset veryslow -tune animation -b:v 170k \
  -maxrate 510k -bufsize 1020k -g 300 -pass $p \
  -af "loudnorm=I=-16:TP=-4:LRA=11,alimiter=limit=0.6:level=false" -c:a aac -b:a 56k \
  -shortest -movflags +faststart ../output/hit-and-hide-explainer-small.mp4; done
```

To change the wording, edit `script.py` and rebuild. Voice clips are cached, so
only the changed lines are synthesized again.
