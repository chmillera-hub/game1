# For Someone, Someday

A 5:32 portrait (720x1280, 24 fps) animated short with voice acting, a score and burned-in subtitles:
`for-someone-someday.mp4` (H.264 + AAC, 14.35 MB, SSIM 0.990 vs. the uncompressed-quality master).
`for-someone-someday.srt` holds the same subtitles as a separate track.

An android with one directive, *help people*, wakes on an empty island. It spends decades preparing the island
for whoever might come someday, gives part of its own power to a lighthouse, and powers down. Years later a girl
and her grandfather follow the light through a storm.

Everything is generated from code (no image or audio assets):

- `make_script.py` -> `script.json`: screenplay (shots, lines, emotions, music word-hits)
- `audio/tts.py`: Kokoro TTS voices with per-word timing and phoneme visemes for lip-sync
- `audio/timeline.py`: absolute timing for every shot, line and word
- `audio/score.py`, `audio/sfx.py`, `audio/mix.py`: FluidSynth score, synthesized ambience/SFX, final mix
- `render/`: canvas renderer (face rig, body puppet, backgrounds, props, one file per scene in `render/shots/`)
- `audio/subs.py`, `render_all.sh`, `encode.py`: subtitles, parallel render, final encodes

Rebuild: `npm install`, download the Kokoro models into `../models`, then
`python3 make_script.py && python3 audio/tts.py && python3 audio/timeline.py && python3 audio/score.py &&
python3 audio/sfx.py && python3 audio/mix.py && python3 encode.py --render`.
