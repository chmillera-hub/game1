# A Table Instead of a Palace

A 6 min 16 s animated short in portrait (720×1280, 24 fps, H.264 + AAC, 14.8 MB). It follows the arc from David to Solomon to Jesus, told as a late-night kitchen conversation between Noa and Teo, with flashbacks.

- `a-table-instead-of-a-palace.mp4`: the finished video. Subtitles are burned in, and the first frame is a bright, fully drawn shot (no fade from black).
- `a-table-instead-of-a-palace.srt`: the same subtitles as a separate file, for platforms that take caption uploads.
- `source/`: everything used to make the video, so any scene, line, voice, or music cue can be changed and the video rebuilt.

## How to rebuild

Requirements: Python 3 with `piper-tts`, `numpy`, and `scipy`; Node 18+ with `@napi-rs/canvas`; and `ffmpeg`.

Put these Piper voices (`.onnx` and `.onnx.json`) in a `voices/` folder next to `source/`: en_US-ryan-high, en_US-lessac-high, en_US-joe-medium, en_US-john-medium, en_US-hfc_female-medium, en_GB-alan-medium, en_GB-northern_english_male-medium, en_US-libritts_r-medium.

```bash
cd source
npm install @napi-rs/canvas
python3 voices.py      # TTS for every line, writes timeline.json and voice.npy
python3 music.py       # score, accents and sound effects, ducked under the voices, writes final.wav
node render.js 0 9034 master.mp4   # renders every frame (fast; can be split into ranges)
ffmpeg -i master.mp4 -i final.wav -c:v libx264 -preset slow -tune animation -b:v 234k \
       -c:a aac -b:a 72k -movflags +faststart out.mp4   # two-pass is recommended
```

## Where to change things

- **Dialogue and pacing:** `screenplay.py`. Put `^word` before a word to get a high, bright note on it (hopeful words) and `~word` to get a deep, low note (heavy words). The number at the end of each line is the pause before it.
- **Voice casting:** the `VOICES` table in `screenplay.py`.
- **Staging, expressions, and camera:** `scenes.js` (rig helpers and kitchen scenes) and `scenes2.js` (all other scenes). Expressions are keyframed per line, for example `[[L[2].s, 'warm'], [L[3].s, 'hurt|{"tears":0.5}']]`. The presets are in `EX` in `core.js` and control brows, lids, gaze, smile, and tears.
- **Music moods per scene:** `MOODS` in `music.py`.
