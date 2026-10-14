# Brindle Cross

A 3:33 portrait (9:16) 3D short, made entirely in code: voices, faces, bodies, set, music,
sound, subtitles and the final encode.

- `brindle_cross.mp4`: the film. 540 × 960, 24 fps, H.264 High plus AAC, 14.4 MB, subtitles burned in.
  The first frame is the opening shot, with no fade, so social previews aren't black.
- `script/screenplay.md`: the screenplay and acting notes. `script/lines.txt` holds every spoken line.
- `script/brindle_cross.ass`: the subtitles and name supers, as a separate file.
- `docs/acting_breakdown.md`: how the lip-sync, eyes, eyelids, expressions and body language work, with the values used.

## Changing things

| To change | Edit | Then rerun |
|---|---|---|
| A line's words, speed or delivery | `script/lines.txt` (`ID\|SPEAKER[speed]\|tts text\|subtitle\|trim\|flags`) | voices, build, render, mix, subs, encode |
| A voice | `src/make_voices.py` `VOICES` | voices, build, render, mix, subs, encode |
| A character's look | `src/chars.py` `SPECS`; geometry in `src/character.py`, `src/headgen.py`, `src/hair.py` | build, render, encode |
| Acting, staging or a camera in a shot | `src/shots.py` (one function per shot, e.g. `s3_20`) | build, render (that shot only), encode |
| The set or lighting | `src/env.py`, `src/shots.py` `lighting`/`face_lights` | build, render, encode |
| Music or sound effects | `src/music_lib.py`, `src/sfx_lib.py`, cue/sfx calls in `src/shots.py` | build, mix, encode |

## Rebuilding

The pipeline needs Blender 4.5, Kokoro ONNX, rubberband, fluidsynth with FluidR3_GM, and ffmpeg with libass.
Run all of these from `src/`:

```
python3 make_voices.py ../script/lines.txt VOICES          # wavs + phoneme timings + mouth curves
blender -b --python shots.py -- VOICES FILM               # film.blend + timeline.json
./render_chunks.sh FILM/film.blend FILM/timeline.json RENDER 5 fwd 2 &   # two runners share shots
./render_chunks.sh FILM/film.blend FILM/timeline.json RENDER 5 rev 2
python3 mix.py FILM/timeline.json VOICES mix.wav          # -16 LUFS, every line >= +10 dB over the bed
python3 subs.py FILM/timeline.json film.ass
python3 encode.py --frames 'RENDER/f%05d.png' --audio mix.wav --ass film.ass \
    --timeline FILM/timeline.json --out brindle_cross.mp4 --max-mb 14.5 --quality-check
```

To re-render one shot, delete its frames (and `RENDER.locks/<shot>`) and run a runner again.
It skips every frame that already exists. `preview.py` renders quick stills of chosen frames.
After changing `tts.py` mouth rules, `revisemes.py VOICES` recomputes the mouth curves without
resynthesising the voices.
