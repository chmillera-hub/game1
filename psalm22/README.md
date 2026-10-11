# Why Have You Forsaken Me — a Psalm 22 short

A ~4 minute vertical (9:16, 720×1280, 24 fps) animated film built entirely from code:
voices, faces, music, ambience and the final compressed MP4.

**Final file:** `psalm22_why_have_you_forsaken_me.mp4` (H.264 + AAC, under 15 MB, first frame is the
title shot so feed previews are never black).

## Story

1. **Golgotha, noon.** Darkness gathers. Passers-by and a soldier mock (Psalm 22:7–8). Mary flinches;
   Magdalene asks how they can laugh; John answers that laughing lets them avoid feeling.
2. **Connection from the cross.** “Woman, here is your son… Son, here is your mother.” John holds Mary.
3. **Three hours of darkness.** A whispered prayer (“You are my strength… do not be far from me”).
4. **The cry** (Mark 15:34): *Eloi, Eloi, lema sabachthani?* then “My God, my God, why have you forsaken me?”
5. **Mary refuses to hush him.** She remembers the night he was born crying, and that she held him
   (flashback). John recognises the psalm (“From my mother’s womb you have been my God”).
   “He’s still praying, John. Out loud.”
6. **The end and the centurion.** “Father, into your hands…” The soldier removes his helmet:
   “Truly, this man was the Son of God.” Mary turns to look at him.
7. **Now.** A young woman on a porch at night, numb in phone light, asks her grandmother how to cry out
   without turning cruel or being gaslit. Nana: speak close to the heart, feel it all the way through,
   listen to what the night teaches; God didn’t stay silent while He suffered. She gives her an acorn.
8. **The garden** (John 19:41). The acorn is planted; at the hill, a tree grows from the foot of the
   cross and bears fruit; people gather under it. Dawn on the porch. “Keep the fire lit.”

No blood, wounds or nudity are shown. Jesus is framed chest-up in close shots and as a silhouette in wide shots.

## How it is made

| File | Role |
| --- | --- |
| `script.py` | Screenplay lines, cast → voice mapping, pause markers |
| `tts.py` | Voices every line with Kokoro-82M (ONNX), lengthens pauses, writes lip-sync envelopes |
| `timeline.py` | Audio-first timeline: line timings, shot cut list, captions |
| `rig.py` | 2D face rig in Skia: projected features, eyelids, gaze, brows, mouth, tears, blinks |
| `characters.py` | Character designs (hair, veils, beards, helmets, clothing, hands) |
| `scenes.py` | Every shot: staging, expression keyframes, backgrounds, lighting, captions |
| `audio.py` | Synthesized score (strings, duduk-like reed, choir, piano, guitar), ambience, mix |
| `render.py`, `build.sh` | Parallel frame render → lossless intermediate → 2-pass x264 + AAC |
| `preview.py` | Contact sheet of chosen timestamps for quick visual checks |

### Rebuild

```bash
pip install skia-python scipy soundfile kokoro-onnx
# needs ffmpeg with libx264 and rubberband, plus libegl1 for skia
export KOKORO_DIR=/path/to/kokoro   # kokoro-v1.0.onnx + voices-v1.0.bin
export WORK=/tmp/psalm22-work
./build.sh                           # VBR=380k ABR=72k by default
```

### Easy changes

- **Dialogue / voices:** edit `script.py` (text, `CAST` voice and speed), delete `$WORK/voice`, rebuild.
- **Captions:** set `CAPTIONS_ON = False` in `scenes.py`.
- **Pacing:** pauses between lines live in `timeline.AUDIO`; cut points in `timeline.SHOTS`.
- **Expressions:** each shot in `scenes.py` keyframes face parameters
  (`b_in` brow raise, `knit`, `open_l/open_r` eyelids, `gx/gy` gaze, `smile`, `tears`, `wet`, `flush`…).
- **File size:** `VBR` (video bitrate) and `ABR` (audio bitrate) in `build.sh`.
