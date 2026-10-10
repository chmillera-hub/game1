# TIREDNESS

Portrait (9:16) animated short, ~4:33, 720x1280 @ 24 fps, H.264 + AAC,
**14.5 MB** → `Tiredness_portrait.mp4`.

Tiredness just wants to play his game. Embarrassment, his nervous lab-scientist
friend, loses a lab critter in his house. Impulsivity (the frozen, wall-eyed
household creature) finally goes off. The critter bites Tiredness, HushCorp
leans on Embarrassment to record him, and Tiredness walks into the lab as
"the printer guy". He falls out of a window, wakes in the sewer with new
senses, and meets the real escaped creature. It leads him to what HushCorp is
hiding.

Everything is procedural: Python + cairo drawings, Kokoro TTS voices,
numpy-synthesized music and sound effects.

## Rebuild
```bash
python3 build.py tts          # voices + lip-sync + timeline (cached per line)
python3 build.py video        # render all 13 scene segments
python3 build.py audio        # voices + music + SFX mix (-14 LUFS)
python3 build.py final --mb 13.7   # 2-pass encode sized to fit (MiB)
```
The Kokoro model (`model.onnx`, `voices.npz`) comes from
huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX; point `KOKORO_DIR` at it.

## Changing things
- **Dialogue / timing:** `script.json` (lines, pauses, cues, voices, music
  cue per scene). Use `engine/scriptedit.update_scene` for pause/cue edits.
  Re-run `tts`, then `video`, `audio`, `final`.
- **A scene's animation:** `scenes/sNN_*.py` (`render(ctx, t, info)` +
  `SFX(info)`). Preview with `python3 build.py sheet sNN --n 16`.
- **Characters:**
  - people: `engine/human.py` (`API_human.md`);
  - Impulsivity, the critter and the creature: `engine/creatures.py` (`API_creatures.md`).
- **Places / props:** `engine/sets.py`, `engine/props.py` (`API_sets.md`).
  Effects, screens and titles: `engine/fx.py` (`API_fx.md`).
- **Music / SFX / mix:** `audio/music.py`, `audio/sfx.py` (`API_audio.md`),
  `audio/mix.py`.

Docs: `SPEC.md` (production bible), `DIRECTION.md` (shot-by-shot direction).
