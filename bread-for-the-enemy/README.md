# Bread for the Enemy

A portrait (9:16) animated short film, about 7½ minutes long, built entirely from
code: anime-style characters, voice acting, an original score, sound design and
burned-in subtitles.

It weaves four passages (NIV) into one story:

| Passage | Where it lands in the film |
|---|---|
| John 13:34 / 15:12 – "Love each other as I have loved you" | Jesus at the Last Supper (prologue); Asher's father repeats it when he is arrested; Asher repeats it at dawn |
| Romans 12:17–21 – "If your enemy is hungry, feed him… overcome evil with good" | Paul's letter read aloud in a house church in Rome; Asher quotes it at Paul; the narrator closes the bread scene with v.21 |
| 1 Timothy 1:12–16 – "I was once a blasphemer and a persecutor and a violent man… the worst of sinners" | Paul's confession in the cell and his memory of the Damascus road |
| Romans 8:35–39 – "Who shall separate us from the love of Christ?" | Paul's answer on the night before his execution; Asher joins him for the last line |

**Story.** Rome, about AD 67. Asher was eight when Saul of Tarsus dragged his
father Yosef out of their home in Jerusalem; his father never came home. Thirty-four
years later, the night before Paul's execution, Asher brings bread to Paul's cell,
because Paul's own letter said: *if your enemy is hungry, feed him.*

## Outputs

- `output/bread_for_the_enemy.mp4`: the main delivery (H.264/AAC, 720×1280, under 15 MB)
- `output/bread_for_the_enemy_hevc.mp4`: a sharper HEVC (H.265) version at the same size, for iPhones and recent Android phones
- `output/bread_for_the_enemy.srt`: a subtitle sidecar (the subtitles are also burned into the video)

The first frame is a fully lit shot of Jesus holding the bread with the title on it,
so previews on social media are never black.

## How it is made

| Step | File | What it does |
|---|---|---|
| Screenplay | `screenplay.py` | Every shot, spoken line, acting keyframe (emotion / gaze / pose), sound cue and title card |
| Voices | `tts.py`, `build_timeline.py` | Kokoro-82M neural TTS (timestamped ONNX export), one voice per character, with per-phoneme timing for lip-sync and room treatment per scene |
| Animation | `render/*.js` | Procedural 2.5D anime rig in `@napi-rs/canvas`: projected 3D facial features, eyelids, brows, iris and gaze, visemes, tears, cel shading; blinks, eye saccades, breathing, speech nods and trembling are procedural |
| Score | `music.py` | An original score written as MIDI on the film's clock and rendered with FluidSynth (FluidR3 GM soundfont) |
| Sound design | `sfx.py` | Synthesised ambiences (cell drips, torches, desert wind, dawn birds) and effects (knocks, bolt, chains, bread breaking…) |
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
python3 render_video.py h264 bread_for_the_enemy.mp4 190 64
```

To preview single frames while editing: `node render/render.js --timeline $BFE_WORK/timeline.json --still 12.5 --out frame.png`.

## Editing

- **Dialogue or timing:** edit `screenplay.py`, then rerun from `build_timeline.py`. Everything downstream (lip-sync, subtitles, music cues) follows the new timing.
- **Acting:** `E("paul", emo="grief", look="down", tears=0.8, dur=1.0)`. The emotion presets live in `render/engine.js` (`EMO`), and the poses in `POSES`.
- **Framing and lighting:** each shot id in the screenplay is a function in `render/shots.js`.
- **Character designs:** `render/characters.js` (colours, hair, beards, headwear) and `render/face.js` (the face rig).

Scripture quotations: New International Version (NIV).
