# That They May Be One — John 17 (NIV)

A vertical (1080×1920) animated short of Jesus' prayer in John 17, made in the
art style of *A New Commandment*: soft cel-shaded characters, lamp-lit night
interiors, blurred backgrounds with bokeh and dust, gold Cinzel titles, and
centred subtitles (bold sans for speech, Lora italic for narration, gold
speaker labels).

**Watch:** [`John17_That_They_May_Be_One.mp4`](John17_That_They_May_Be_One.mp4) (about 4 min 53 s)

## What's in it

The whole of John 17 is read verbatim from the NIV, framed by John 13:30 and
16:33 before the prayer and John 18:1 after it, plus three short narration
lines of my own (the opening hook, "Then Jesus spoke to the eleven who
remained", and the closing line). The three NIV section headings appear as
title cards:

| Verses | Section | Visuals |
| --- | --- | --- |
| 17:1–5 | Jesus Prays to Be Glorified | Jesus lifts his eyes in the upper room; Golgotha at dusk; heavenly glory; the cosmos "before the world began" |
| 17:6–19 | Jesus Prays for His Disciples | the eleven at the table; Judas in the night street; the lit window in sleeping Jerusalem; the scroll ("your word is truth"); disciples sent out on the sunrise road |
| 17:20–26 | Jesus Prays for All Believers | a candle flame passed from person to person; a crowd of believers from every nation; glory again |
| 18:1 | — | Jesus leads the eleven across the Kidron Valley by lantern light |

Scripture quotations are taken from The Holy Bible, New International Version® NIV®.
Copyright © 1973, 1978, 1984, 2011 by Biblica, Inc.™ Used by permission. All rights reserved worldwide.
(The notice is on the end card.)

## How it's made

Everything is generated from code: no stock art, footage or music.

- `script/cues.json`: the script. Each unit is one spoken line; `|` marks subtitle breaks; `shots` picks the picture.
- `tools/tts.py`: speaks every unit with [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) (narrator `bm_george`, Jesus `am_michael`), then builds `build/timeline.json` (word-timed subtitles, shot list, section cards, per-frame lip-sync).
- `tools/music.py`: synthesises the original ambient score (pads, piano-like arpeggios, reverb), following the three sections of the prayer.
- `src/rig.js`: parametric SVG characters (blinks, gaze, lip-sync, poses, tears, halo); `src/sets*.js`: backgrounds and props; `src/shots.js`: the 20 shots; `src/engine.js`: deterministic frame renderer.
- `tools/render.mjs`: renders every frame in headless Chromium (Playwright) and encodes with ffmpeg; `tools/mix.py`: ducks the music under the voice, normalises to −14 LUFS and muxes the final MP4.

### Rebuild

```sh
cd john17
python tools/tts.py            # needs: kokoro, torch (CPU), soundfile, scipy
python tools/music.py
node tools/render.mjs --out build/video.mp4 --workers 4
python tools/mix.py build/video.mp4 John17_That_They_May_Be_One.mp4
```

Preview any moment in a browser by serving this folder and opening
`index.html?t=<seconds>` or `index.html?shot=<shot id>&lt=<seconds>&take=<n>`.
