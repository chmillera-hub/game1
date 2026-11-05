# A Table Instead of a Palace

A 6 min 39 s animated short in portrait for mobile: 720 × 1280, 24 fps, H.264 + AAC, **14.7 MB**, −14 LUFS. It traces the arc from David to Solomon to Jesus, told as a late-night kitchen conversation between Noa and Teo with flashbacks.

| File | What it is |
|---|---|
| `a-table-instead-of-a-palace.mp4` | The film. Subtitles are burned in, and the first frame is a fully drawn shot with no fade from black. |
| `a-table-instead-of-a-palace.srt` | The subtitles as a separate file (203 cues) |
| `production/SHOT_LIST.md` | Timed shot list: 102 shots with frame-accurate ranges, purpose, light, sound and dialogue |
| `production/PRODUCTION.md` | The brief as recorded, visual rules, locked designs, approximations and quality criteria |
| `production/AUDIO.md` | Voice sources and licenses, credit line, score and sound-effect design, mix notes |
| `production/EXPORT.md` | Measured export metadata, render settings and dependency versions |
| `production/CHECKS.md` | Checks completed and remaining gaps |
| `production/*.jpg` | Cast lineup, expression sheet, 6 contact sheets (121 frames), motion-test strips |
| `source/` | The complete project for reproducing the film |

## Rebuild

Requirements: Python 3 with `piper-tts`, `numpy` and `scipy`; Node 18+; `ffmpeg` with libx264.

Download these Piper voices (`.onnx` and `.onnx.json` files) from huggingface.co/rhasspy/piper-voices into `voices/`, next to `source/`. You can also point the `PIPER_VOICES` environment variable at a folder that holds them.
- en_US-john-medium
- en_US-joe-medium
- en_US-libritts_r-medium
- en_GB-northern_english_male-medium

```bash
cd source && npm install
./build.sh      # TTS -> score/mix -> 9,581 frames -> loudness-normalised two-pass encode -> out.mp4
./checks.sh     # export verification
node shots.js && python3 shotlist.py && python3 contact.py && node charsheet.js   # shot list and reference sheets (need a prod/ folder)
```

## Where to change things

- **Dialogue and pacing:** `screenplay.py`. Put `^word` before a word for a high, hopeful note and `~word` for a deep, heavy note. The number at the end of each line is the pause before it. Voice casting is the `VOICES` table in the same file.
- **Staging, expressions and camera:** `scenes.js` (rig helpers and kitchen scenes) and `scenes2.js` (all other scenes). The expression presets are `EX` in `core.js`, and the character designs are `CH`.
- **Music moods:** `MOODS` in `music.py`.
