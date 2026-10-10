# Nice Try, My Guy — AI vs. the Evil Genius

Portrait (9:16) animated short, ~4:59, 720x1280 @ 24 fps, H.264 + AAC,
**14.4 MB** → `AI_vs_Evil_Genius_portrait.mp4`.

The Evil Genius (and his snake) tries nine sneaky prompting tricks
on an AI — code words, "it's just a story", hypotheticals, "for research",
grandma's bedtime story, tiny innocent pieces, "you are now EVIL-BOT",
flattery, begging. The AI sees where each one leads, bricks off exactly the
harmful part, and hands him scary-but-harmless things to scheme instead:
villain stories, exposing scams, warning people about real dangers.

Everything is procedural: Python + cairo drawings, Kokoro TTS voices,
numpy-synthesized music and sound effects.

## Rebuild
```bash
python3 build.py tts          # voices + lip-sync + timeline (cached per line)
python3 build.py video        # render all 13 scene segments
python3 build.py audio        # voices + music + SFX mix (-14 LUFS)
python3 build.py final --mb 13.7   # 2-pass encode sized to fit (MiB)
```
The Kokoro model (`model.onnx`, `voices.npz`) is downloaded from
huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX; point `KOKORO_DIR` at it.

## Changing things
* **Dialogue / timing:** `script.json` (lines, pauses, cues, voices, music
  cue per scene). Re-run `tts`, then `video`, `audio`, `final`.
* **A scene's animation:** `scenes/sNN_*.py` (`render(ctx, t, info)` +
  `SFX(info)`). Preview with `python3 build.py sheet sNN --n 16`.
* **Characters / props:** `engine/villain.py`, `engine/snake.py`,
  `engine/ai_char.py`, `engine/props.py`. Captions: `engine/captions.py`.
* **Music / SFX / mix levels:** `audio/music.py`, `audio/sfx.py`, `audio/mix.py`.

Docs: `SPEC.md` (production bible), `DIRECTION.md` (shot-by-shot direction),
`API.md` (rig/prop/audio APIs), `drafts/` (script drafts + judging).
