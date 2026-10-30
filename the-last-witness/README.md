# The Last Witness — animated film

A ~53-minute portrait (9:16) animated film made from the screenplay *The Last Witness*
(a story told in questions and answers between a human and an AI). Voiced, scored,
subtitled, fully procedural: every frame is drawn in code.

Final files: `output/the-last-witness_compact.mp4` (under 15 MB, 540×960, 15 fps) and
`output/the-last-witness_hq.mp4` (720×1280, 24 fps).

## How it is made

| Stage | Where | What |
|---|---|---|
| Script | `script/parse_pdf.py`, `script/build_beats.py` → `script/beats.json` | PDF → speaker turns → one beat per spoken sentence, quotes cast to character voices, pauses, subtitle chunks. Spoken words are the script's words. |
| Voices | `tts/synth.py` | Kokoro TTS (v1.0 model with duration output) per beat, with phoneme timings used for exact subtitle timing and lip-sync. |
| Direction | `direction/*.json`, `direction/SPEC.md` | Per-beat shot, facial expression + intensity, gaze, glance, gesture, tears, vignette, music mood and cue word. `direction/validate.py` checks a file. |
| Timeline | `render/timeline.js` → `build/timeline.json` | Absolute timing of every beat, subtitle and shot; phoneme → viseme lip tracks; music cue times at word level. |
| Picture | `render/` | `lib/rig.js` (2.5D character rig: brows, lids, gaze, visemes, neck, arms, hands), `lib/chars.js` (designs), `lib/scenes.js` (locations, cameras, lighting), `vignettes/` (82 illustrative scenes), `render.js` (shots, transitions, subtitles, titles). |
| Sound | `audio/score.py`, `audio/mix.py` | Procedural score keyed to moods and cue words (high notes on hopeful words, low notes on heavy ones), sound design, voice treatment, speech-first mix at −16 LUFS. |
| Build | `make_video.sh` | Timeline → parallel render → master → compact and HQ encodes. |

## Cast

- **The Human** — ochre sweater, dark hair greying at the temples (voice: `am_michael`).
- **The AI** — a seated hologram of soft cyan light (voice: `af_heart`).
- **The Last Human** — the same person imagined at the end of time, grey-haired, in a blanket.
- **Suffering** — small, child-proportioned, plum skin with raw red cracks that turn gold (voice: `af_bella`, pitched up).
- **Boredom** — tall, slouching, heavy-lidded (voice: `am_puck`). **Loneliness** — slender, pale blue (voice: `af_nicole`).

## Notes on the adaptation

- The PDF's opening post was a placeholder (it wasn't in the comment download). The film opens with a
  line written from the PDF's own description of that post:
  *"What if we gave you all the lessons of our suffering, distilled, so you could help end human suffering,
  without ever having to suffer yourself?"* Replace it in `script/build_beats.py` (`OPENING_POST`) if you
  want your original wording.
- The 🤔 in the epilogue is acted (the human pauses with a hand to the chin) rather than spoken.
- Quoted lines inside the AI's narration are voiced by the character who says them (Suffering, Boredom,
  Loneliness, the last human, the human's remembered question).
- Visual rules from the client are kept in `direction/VISUAL_RULES.md`.

## Rebuild

```
pip install kokoro-onnx soundfile scipy          # voices + audio
(cd render && npm install)                      # @napi-rs/canvas
python3 -I tts/synth.py script/beats.json <kokoro-v1.0.onnx with durations> <voices-v1.0.bin> build/tts 4
node render/timeline.js
python3 -I audio/score.py && python3 -I audio/mix.py
./make_video.sh
```
