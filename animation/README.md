# The Void and My Fear — animated short

A portrait (9:16, 720×1280, 24 fps) animated short, about 5:19, with voice acting, narration, an
original score, sound design and burned-in subtitles — generated entirely in code from the creator's story.

**Deliverables:** `The_Void_and_My_Fear.mp4` (H.264 + AAC, BT.709, < 15 MB, captions burned in),
`The_Void_and_My_Fear.srt` (the same captions as a sidecar file) and `thumbnail.png` (frame 1).

## How it is made

| Stage | Files |
|---|---|
| Story brief, cast, locations | `BIBLE.md` |
| Screenplay (scenes → beats: lines, delivery, shots, acting notes, SFX) | `data/screenplay.json` |
| Voices (Kokoro TTS; narrator = 50/50 blend of two voices for a gender-neutral sound) | `audio/tts.py` → `audio/wav/`, `data/lines.json` |
| Timeline (every beat's absolute time, from real line lengths + pauses) | `tools/build_timeline.py` → `data/timeline.json` |
| Dialogue speed (all lines ×1.15; picture time-warped to match, silent beats unchanged) | `tools/speed_dialogue.py` → `audio/wav_play/`, `data/timeline_play.json`, `data/timewarp.json` |
| Captions (phrase timing from voice pauses + shot cuts; positions avoid faces) | `tools/detect_cuts.py`, `tools/build_subtitles.py`, `render.mjs --place-subs`, `src/subtitles.mjs`, `data/subtitle_overrides.json` |
| Lip-sync (loudness + whisper word alignment + phonemes → mouth shapes per frame) | `audio/lipsync.py` → `data/lipsync.json` |
| Staging & continuity plan | `data/staging.md` |
| Engine, face rig, characters, sets, cosmos | `src/engine.mjs`, `src/face.mjs`, `src/chars/`, `src/sets/`, `src/fx/` (APIs in `docs/`) |
| One module per scene (camera, acting keyed to beats, sound cues) | `src/scenes/sNN_*.mjs` |
| Score (soundfont orchestra, leitmotifs, cue plan keyed to beats) | `audio/music.py`, `data/music_plan.json` |
| Sound effects (synthesised) | `audio/sfx.py` → `audio/sfx/` |
| Mix (reverb per space, ducking under speech, −16 LUFS) | `audio/mix.py` |
| Render + size-targeted encode | `tools/render_all.sh`, `tools/encode.sh`, `tools/zones.py` |

All animation timing is anchored to beats (`'s07b03.end+0.5'`), so changing a line, a pause or a voice
re-times everything automatically. Scenes are authored in *story time* (`data/timeline.json`); the film plays
in *play time* (`data/timeline_play.json`), where spoken lines run faster — the renderer maps each output frame
back to story time, and lip-sync, sound effects, music and captions are placed in play time.

## Rebuild

Needs Node 22, Python 3 with `kokoro-onnx soundfile scipy faster-whisper tinysoundfont`, ffmpeg, and these
model files in `models/`: `kokoro-v1.0.onnx`, `voices-v1.0.bin` (kokoro-onnx release), `whisper-base.en/`
(Systran/faster-whisper-base.en), `MuseScore_General.sf2`.

```bash
npm install
python3 audio/tts.py data/screenplay.json      # voices (or pass beat ids: ... s06b03,s07b02)
python3 tools/build_timeline.py data/screenplay.json
python3 tools/speed_dialogue.py 1.15             # dialogue speed (1.0 = as recorded)
python3 audio/lipsync.py
node tools/collect_sfx.mjs
python3 tools/resolve_music.py && python3 audio/music.py data/music_cues.json out/music.wav
python3 audio/mix.py
python3 tools/detect_cuts.py                     # needs a previous render (out/master_video.mp4); optional
python3 tools/build_subtitles.py && node src/render.mjs --place-subs
tools/render_all.sh 14.5                         # -> out/final.mp4 (target size in decimal MB)
```

Preview without a full render: `node src/render.mjs --sheet s14 --n 16 --out out/s14.png` (contact sheet) or
`--stills 12.5,40` (PNG frames). Times are play time; add `--story` for story time, `--nosubs` to hide captions.

## Common changes

- **A different narrator voice:** edit `VOICES["NARRATOR"]` / `["CONSCIOUSNESS"]` in `audio/tts.py`
  (e.g. `[("am_michael", 1.0)]` or `[("af_heart", 1.0)]`), then rebuild from the TTS step.
- **Change or add a line / pause:** edit `data/screenplay.json`, re-run TTS for those beats, then the rest.
- **Slower/faster speech:** `python3 tools/speed_dialogue.py <factor>` for the whole film (then the steps after
  it), or `speed`, `tempo` and `gap` per speaker in `audio/tts.py`.
- **Captions:** wording comes from the screenplay; placement/splits/end times can be pinned in
  `data/subtitle_overrides.json`; style (font, colours, box) in `src/subtitles.mjs`. `--nosubs` for a clean render.
- **Music mood or intensity per scene:** `data/music_plan.json`.
- **Bigger/smaller file:** `tools/render_all.sh <MB>` (or `tools/encode.sh <MB>` to re-encode only).
