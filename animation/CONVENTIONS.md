# Animation build conventions (shared contract)

Short film "The Family Inside" — portrait 1080x1920, 24 fps, 2D, rendered with
Node + `@napi-rs/canvas` (Canvas2D API, Skia). Audio is Python/numpy at 48 kHz.

## Directory layout
```
animation/
  audio/script.json        screenplay (lines, speakers, hi/lo music words)
  audio/gen_voices.py      TTS -> build/voice_cache/*.wav + build/schedule.json
  audio/music.py           procedural score  -> build/music.wav        (music agent)
  audio/sfx.py             procedural SFX library                      (sfx agent)
  audio/mix.py             final mix -> build/mix.wav                  (sfx agent)
  src/core.js              math/easing/noise/color helpers (engine)
  src/rig.js, chars.js     character rig (engine)
  src/bg/kitchen.js        Maya's kitchen at dusk                      (bg agent A)
  src/bg/porch.js          Nana's front porch + hinged door            (bg agent A)
  src/bg/hearth.js         the inner hearth room + fire + visions      (bg agent B)
  src/bg/nana.js           Nana's kitchen (now + memory) + hospital    (bg agent C)
  src/shots.js             timeline / staging (engine)
  src/render.js            frame loop -> ffmpeg (engine)
  build/                   generated artifacts (not committed except final video)
```

## build/schedule.json (already generated)
`{ duration, cast, lines: [{id, sc, sp, text, t0, t1, wav, hi:[word], lo:[word],
words:[{w,t0,t1}], phones:[[ipa,t0,t1]]}] }` — all times absolute seconds.
`sc` is the scene tag: kitchen | hearth | memory | reflect | nanahouse.
`hi` = hopeful/light words that get a high note; `lo` = sad/existential words
that get a low note. Match a tag to the FIRST word in `words` whose text, lower-cased
and stripped of punctuation, equals the tag lower-cased.

## build/cues.json (written later by src/shots.js; agents must not depend on it existing)
```json
{ "scenes": [{"name": "kitchen1", "t0": 0, "t1": 15.2, "mood": "intimate"}],
  "sfx":    [{"t": 12.3, "name": "phone_buzz", "gain": 1.0, "pan": 0.2}],
  "amb":    [{"name": "clock_tick", "t0": 0, "t1": 15, "gain": 0.5}] }
```
For testing, agents write their own `build/cues_test.json`; scripts take the cue
path as an optional CLI argument and default to `build/cues.json`, falling back
to `build/cues_test.json`.

## Camera / world coordinates
- Logical frame is 1080 x 1920. The renderer applies:
  `scale(outW/1080) · translate(540, 960) · scale(zoom) · translate(-cam.x, -cam.y)`
  so `(cam.x, cam.y)` is the world point at frame centre; zoom 1 shows 1080 x 1920
  world units; zoom 3 is a close-up showing 360 x 640 units.
- y grows downward. Units ≈ pixels at zoom 1. An adult standing ≈ 950 units tall,
  head (crown→chin) ≈ 150 units.
- Each environment must fully cover its declared world extents (no empty canvas
  visible for any camera inside them).

## Environment module API (src/bg/*.js, CommonJS)
```js
module.exports = {
  ENV: { name, extents: {x0, y0, x1, y1}, anchors: {...named points...} },
  drawBack(ctx, t, o),   // everything behind characters (ctx already in world coords)
  drawFront(ctx, t, o),  // foreground occluders drawn after characters (tables, etc.)
  lightAt(x, y, t, o),   // lighting for a character standing at world (x, y)
};
```
- `t` = absolute time (s). `o` = options object (document every option + default).
- Must be deterministic: seeded pseudo-random only (`Math.random` forbidden), so a
  frame renders identically every time. No per-frame random noise or flicker on
  static surfaces (it destroys video compression); animate only things that should
  move (fire, smoke, dust motes, curtains, leaves), smoothly.
- Performance: < 40 ms per call at 1080x1920. Cache static layers once into an
  offscreen canvas (`createCanvas` from `@napi-rs/canvas`) at ~1.25x world scale
  and `drawImage` it each frame; slight softness in close-ups is welcome (reads as
  depth of field).
- `lightAt` returns:
```js
{ keyDir,      // radians, direction FROM character TOWARD key light, screen space (0 = +x, -PI/2 = up)
  keyColor, keyAmt,        // '#rrggbb', 0..1
  rimDir, rimColor, rimAmt,// rim/back light (e.g. a window or fire behind)
  shadowColor, shadowAmt,  // colour of the dark side tint, 0..0.6
  ambient, ambientAmt }    // overall tint multiplied onto characters, 0..0.4
```
  Rule: a character near/in front of a light is never near-black — always provide a
  rim from that source plus enough fill. Mood tints stay gentle: they shade clothing
  but never turn it a different colour.

## Art style
Soft, warm, painterly 2D. Flat colour shapes with smooth gradient shading; no black
outlines (at most thin outlines in a darker shade of the fill colour). Shadows are
soft-edged gradients, never muddy patches or hard brown lines. Brick and stone look
gritty, weathered and lifelike (varied bricks, mortar, chips, soft grime) but keep
contrast low and large areas smooth. Objects rest on surfaces — nothing floats. Keep
the palette harmonious with the cast:
- Maya: olive-green cardigan #7a8450, cream top #efe6d2, warm brown skin #a8714f.
- Eli: charcoal hoodie #4f565f, warm brown skin #9a6646.
- Nana: plum cardigan #7b3b55, silver hair. Young Maya: lilac tee #b9a3d6.
- Anger: red #d0402f, white shirt, maroon tie. Annoyance: peach skin, orange-red
  hair, white lab coat, YELLOW glow #ffd84a. Fear: same build, ORANGE glow #ff9a3c.
- Sadness: blue skin #7fb2e5, dark-blue hair, cream sweater with a small red heart.
Avoid making backgrounds saturated red, yellow, orange or blue in large areas so the
emotions stay readable against them.

## Audio
48 kHz. Voices are mono wavs in build/voice_cache (listed in schedule.json `wav`,
relative to build/). Final loudness target ≈ -16 LUFS integrated, true peak ≤ -1.5 dBTP.
Everything deterministic (seeded numpy RNG).
