# TIREDNESS — Episode 2: Lights Out

Portrait (9:16) animated short, ~5:43, 720x1280 @ 24 fps, H.264 + AAC (rev 3: user notes applied, no length cap).
- `Tiredness_ep2_portrait.mp4`: about 16.9 MB, the same quality per second as rev 2.
- `Tiredness_ep2_portrait_under15MB.mp4`: about 14.4 MB, a lower bitrate for upload limits.

Picks up where Episode 1 ended, on the shaft catwalk:
- Thing 1 gazes at its sleeping sibling in a pod.
- Tiredness finds Thing 1's empty pod (CalmCorp calls it "THING 1"), and the Boss cuts the lights.
- He learns his new sense works with his eyes closed, and they dodge flashlights.
- He is overwhelmed and doesn't want to abandon it, but he's scared.
- He commits: "Hell or high water."
- Embarrassment (who works for CalmCorp) is talked round. He switches off his recorder and hands over his keycard.
- Tiredness refuses the Boss's offer of endless sleep ("But right now... I'm not tired"), frees baby Joy, and escapes.
- He gets home at dawn.

Everything is procedural: Python + cairo drawings, Kokoro TTS voices,
numpy-synthesized music and sound effects.

## Rebuild
```bash
python3 build.py tts          # voices + lip-sync + timeline (cached per line)
python3 build.py video        # render all 8 scene segments
python3 build.py audio        # voices + music + SFX mix (-14 LUFS)
python3 build.py final --mb 16.15  # 2-pass encode sized to fit (MiB); --out <name.mp4> for a second size
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
