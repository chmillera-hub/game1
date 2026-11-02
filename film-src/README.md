# The Last Thing on My Mind

A short animated film, about 5½ minutes long. A 99-year-old man is on his deathbed, staged as the last night of a long run in an old theatre. The emotional family he cared for all his life (the parts of him that keep his heart, breath, mind, body and wonder well) gathers around him, holds on, and makes death the last thing on his mind.

Every frame is drawn in code with the Canvas 2D API, and every sound is synthesised with the Web Audio API. There are no image, video or audio files.

## Watch it

Open `../the-last-thing-on-my-mind.html` in a browser and press **Begin** (with sound on).

| Key | Action |
| --- | --- |
| Space or K | Play / pause |
| ← and → | Previous / next act |
| M | Mute |
| F | Full screen |

## How it is built

`src/` holds the modules. The build joins them, in filename order, into one self-contained page.

| File | What it does |
| --- | --- |
| `00-head.html` | Page markup, styles, intro screen, captions and transport |
| `01-util.js` | Easing, keyframe tracks, noise, seeded random |
| `02-audio.js` | The synthesiser: piano, pads, strings, choir, bells, heartbeat, breath, clock, rain, beds and gate |
| `03-draw.js` | The family of light, the reaper and the running spirit |
| `04-world.js` | The room, the bed and the old man |
| `05-env.js` | The garden, the sea and the ship, the starfield, and the shadow-puppet memories |
| `05b-theatre.js` | The proscenium, curtain, spotlight, ghost light, audience, act cards and the hook |
| `06-score.js` | Chord parsing and note generators |
| `07-fx.js` | Camera, layers, transitions, bloom and tone |
| `08-film.js` | **The film itself**: timeline, narration, cast, every animation track, the render and the score |
| `09-player.js` | The interactive web player |
| `10-render.js` | Deterministic video-export mode (open the page with `#render`) |

Everything on screen and in the score is a pure function of time, so any frame can be rendered on its own.

Rebuild the page after editing `src/`:

```sh
node film-src/build.mjs
```

## Export the YouTube video (1920×1080, 30 fps, H.264 + AAC)

You need Node.js, Playwright with Chromium (`npm i playwright && npx playwright install chromium`) and ffmpeg.

```sh
node film-src/render-video.js the-last-thing-on-my-mind.html out/ --fps 30 --workers 3 --name The-Last-Thing-on-My-Mind
```

- Frames render in parallel, headless browsers, and stream into ffmpeg.
- The score is rendered offline, sample-accurately, with an `OfflineAudioContext`.
- The exporter masters the mix for YouTube: a high-pass, a bus compressor, gain to about −15 LUFS integrated, and a −2 dBTP true-peak limiter.
- It then muxes the picture and sound into `out/The-Last-Thing-on-My-Mind.mp4`.

Options:
- `--w 3840 --h 2160` renders 4K.
- `--from` and `--to` (in seconds) render an excerpt.
- `--noaudio` skips the score.
