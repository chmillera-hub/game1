# Bread for the Enemy

A portrait (9:16) animated short film, about 9 minutes long, built entirely from
code: anime-style characters, voice acting, an original score, sound design and
burned-in subtitles.

It weaves four passages into one story:

| Passage | Where it lands in the film |
|---|---|
| John 13:34 / 15:12 – "A new commandment I give you… love one another as I have loved you" | Jesus at the Last Supper (prologue, in full); remembered by Asher before he breaks the bread; the closing card |
| Romans 12:17–21 – "If your enemy is hungry, feed him… overcome evil with good" | Paul's letter read aloud by Phoebe to the believers in Rome; Asher quotes it at Paul; the narrator closes the bread scene with v.21 |
| 1 Timothy 1:12–16 – "I was once a blasphemer and a persecutor and a violent man… the worst of sinners" | Paul's confession in the cell and his memory of the road to Damascus |
| Romans 8:35–39 – "Who shall separate us from the love of Christ?" | Paul's answer on the night before his execution, while Asher listens |

**Story.** Rome, about AD 67. Asher was eight when Paul, then a persecutor of the
church, dragged his father Yosef out of their home in Jerusalem, and his father
never came home. Thirty-four years later, on the night before Paul's execution, Asher
brings bread to Paul's cell, because Paul's own letter said: *if your enemy is hungry,
feed him.* Paul greets the stranger as a brother before he knows who he is. Asher's hate
does not vanish in one night. He says so more than once, and Paul answers him every
time without hating back. Asher breaks the bread anyway: "I don't forgive you. Not yet."

Characters are introduced with floating name tags. The subtitles show the speaker's
name whenever a different character starts talking.

## Outputs

- `output/bread_for_the_enemy.mp4`: the film (H.264 High + AAC stereo, 720×1280, 24 fps, about 9:07, under 15 MB)
- `output/bread_for_the_enemy.srt`: a subtitle sidecar (the subtitles are also burned into the video)

Compression: 2-pass x264 (`veryslow`, `tune animation`) at about 154 kbps video plus 56 kbps AAC.

The first frame is a fully lit shot of Jesus holding the bread with the title on it,
so previews on social media are never black.

## How it is made

| Step | File | What it does |
|---|---|---|
| Screenplay | `screenplay.py` | Every shot, spoken line, acting keyframe (emotion, gaze, pose, nods), sound cue, title card and name tag |
| Voices | `tts.py`, `build_timeline.py` | Kokoro-82M neural TTS (timestamped ONNX export), one voice per character, with per-phoneme timing for lip-sync and room treatment per scene. Pronunciations are fixed with a `tts=` override, e.g. "red" for past-tense "read" and "liv" for "live" |
| Animation | `render/*.js` | Procedural 2.5D anime rig in `@napi-rs/canvas`: projected 3D facial features, eyelids, brows, iris and gaze, visemes, tears and cel shading. Hair caps cover the whole skull. Blinks, eye saccades, breathing, speech nods, reaction nods, nervous fidgeting and trembling are procedural |
| Score | `music.py` | An original score written as MIDI and rendered with FluidSynth (FluidR3 GM soundfont). Every cue is anchored to a line or shot, so the music follows edits |
| Sound design | `sfx.py` | Synthesised ambiences (cell drips, torches, desert wind, dawn birds) and effects (knocks, bolt, a heavy wooden door, muffled chains, a shaky breath, bread breaking…) |
| Mix | `mix.py` | Dialogue-ducked music, bus compression, two-pass loudness normalisation to -15 LUFS |
| Video | `render_video.py` | Parallel frame rendering to a near-lossless master, then 2-pass encodes sized under 15 MB |

## Rebuild

Requirements: Python 3 with `kokoro-onnx soundfile scipy mido numpy`; Node 18+;
`ffmpeg`; `fluidsynth` and `fluid-soundfont-gm`.

```bash
export BFE_WORK=/path/to/workdir          # big intermediates go here
mkdir -p $BFE_WORK/models && cd $BFE_WORK/models
curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
curl -L -o kokoro-ts.onnx https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX-timestamped/resolve/main/onnx/model.onnx
cd -
npm install
python3 build_timeline.py      # voices + timeline.json + voice.wav + subtitles.srt
python3 music.py               # music.wav
python3 sfx.py                 # sfx.wav
python3 mix.py                 # mix.wav
python3 render_video.py master # frames -> master.mkv
python3 render_video.py h264 bread_for_the_enemy.mp4 154 56
```

To get under 15 MB, choose the video kbps as about `14.6e6 * 8 / seconds / 1000 - audio kbps`.

To preview single frames while editing: `node render/render.js --timeline $BFE_WORK/timeline.json --still 12.5 --out frame.png`.

## Editing

- **Dialogue or timing:** edit `screenplay.py`, then rerun from `build_timeline.py`. Everything downstream (lip-sync, subtitles, name tags, music cues) follows the new timing.
- **Acting:** `E("paul", emo="grief", look="down", tears=0.8, dur=1.0)`, or `E("asher", nod=1)` for a reaction nod. The emotion presets live in `render/engine.js` (`EMO`), and the poses in `POSES`.
- **Name tags:** `T("name", "PAUL", who="paul", at=0.3, dur=3.0)`. Use `·` to add a smaller second line.
- **Framing and lighting:** each shot id in the screenplay is a function in `render/shots.js`.
- **Character designs:** `render/characters.js` (colours, hair, beards, headwear) and `render/face.js` (the face rig).
