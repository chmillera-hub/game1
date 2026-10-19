# The House That Hums

A 3:50 portrait (9:16) animated short, inspired by a haunted-house puzzle illustration and given a gothic stop-motion feel: a giant moon, spiral swirls, curly bare trees, striped walls and a crooked house. All characters are original.

- `the-house-that-hums.mp4`: 720×1280, 24 fps, H.264 + AAC, 14.3 MB. SSIM against the lossless master is 0.972. The first frame is the title shot, with no fade from black.
- `poster.jpg`: the first frame.

## Story
Pip, the newest ghost in the house, can't remember who they were. Patch, a gentle patchwork giant made of "a lot of somebodies", and Auntie Bramble, a witch who once kept a lighthouse, help Pip carve a lantern. The light brings back one small memory, a hummed song that goes "low… high… home", and the whole house learns to hum it.

## Sound
- Voices: Kokoro TTS, pitch-shifted per character. Mouths are lip-synced from each line's loudness and brightness.
- Score: synthesized from scratch. It has an original waltz theme in D minor that turns to D major at the end, plus a skeleton polka on xylophone.
- Word cues: hopeful words (gold in the subtitles) trigger a bell or celesta swell. Heavy words (blue in the subtitles) trigger a low cello and gong.
- Mix: the music ducks under dialogue. Integrated loudness is about -15 LUFS.

## Rebuild
Needs Python with `kokoro-onnx soundfile scipy`, Node with `@napi-rs/canvas`, and ffmpeg built with rubberband and libx264.

You also need these downloads, which are not checked in:
- Kokoro model files `kokoro-v1.0.onnx` and `voices-v1.0.bin`, placed in `models/`.
- The OFL fonts `Baloo2[wght].ttf` and `MysteryQuest-Regular.ttf`, placed in `fonts/`.

Layout used by the scripts: `src/*.py` and `render_all.sh` sit next to `models/`, `fonts/`, `work/` and `render/` (the JS files).

1. `node render/export_lines.js` exports the dialogue lines.
2. `python tts.py` synthesizes the voices and writes `work/lines_out.json`.
3. `./render_all.sh` renders the frames into `work/video_lossless.mkv`.
4. `python music.py` builds the score and writes `work/mix.wav`.
5. Encode with ffmpeg using 2-pass x264 at about 410k (`-preset veryslow -tune animation`) and `-c:a aac -b:a 80k`.

`render/script.js` holds the whole story: lines, voices, camera moves, expressions and poses. Edit it and re-run the steps above to change anything.
