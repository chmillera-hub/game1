# Scene author's guide

The film is a single procedural canvas animation, 1920×1080 film units, rendered by
`js/engine.js` with the shared art kit in `js/art.js` and helpers in `js/util.js`.
Each scene is a self-contained file in `scenes/` that registers itself with `Film.scene({...})`.
Read `scenes/00-title.js` first — it is the reference for structure and polish.
Read `tools/lab-scenes.js` to see how every art-kit primitive is called (it renders the
model sheets).

## Hard rules

1. **Edit only your own scene file(s).** Never modify `js/*`, `index.html`, `tools/*`, `docs/*`
   or another author's scene. Need a helper? Write it inside your file's IIFE. Found a bug or
   limitation in the shared kit? Work around it locally and describe it in your final report.
2. **The film is a pure function of time.** `render(ctx, t, S)` must draw the frame for local
   time `t` from scratch. No state carried between frames, no `Math.random()`, no `Date`.
   Use `U.rng(seed)`, `U.hash(i, seed)`, `U.noise1`. Scrubbing backwards must work.
3. `t` can run up to ~2 s past `duration` (crossfades into the next scene) — hold or continue
   gracefully; never throw.
4. **Use the story's exact words** from `docs/SCRIPT.md`. You may add a little invented
   background chatter only where SCRIPT.md says so.
5. **Performance:** headless average render time (`--timing`) should stay under ~20 ms/frame
   and max under ~45 ms. Avoid per-frame loops over thousands of shapes; prefer bands and
   cached offscreen canvases (`Art.canvas(key, w, h)`) for static detail.
6. Keep everything inside the IIFE; the only globals you may touch are `Film`, `U`, `Art`.

## Scene definition

```js
(function () {
  'use strict';
  const { W, H } = U;
  Film.scene({
    id: 'trail', order: 1, title: 'The Trail', duration: 30,
    chapter: 'Part One · The Hike',     // optional: label shown briefly in the top bar
    mood: 'forest',                     // audio ambience/music bed (see Audio)
    sfx: [[2.0, 'bird'], [8.5, 'chime', { gain: 0.6 }]],  // local-time cues
    fadeIn: 0.8, fadeOut: 0.8,          // seconds to/from black (0 = hard cut)
    crossIn: 0,                         // >0: crossfade from previous scene instead of fadeIn
    fadeColor: '#000000',
    post: { vignette: 0.32, grain: 0.045, letterbox: 1 },   // or (t) => ({...})
    render(ctx, t, S) { /* S.d = duration, S.T = global time */ },
  });
})();
```

The engine draws scenes, then vignette → grain → letterbox → fade, then the **overlay
pass** (captions, titles queued with `Art.later` / `Art.caption`).

## Frame & composition

- Film space is 1920×1080. With `letterbox: 1` (house standard) the visible picture is
  **y 139 → 941** (`Art.PIC`). Narration captions sit in the bottom black bar (y≈1011).
  Keep all important imagery and every speech bubble inside the picture area.
- Use `Art.cam(ctx, {x, y, zoom})` inside `ctx.save()/restore()` for camera moves (focus point
  lands at screen center). `Art.shake(t, amt, seed)` gives handheld drift.
- Depth of field: `Art.blurred(ctx, amount, (c) => { ...draw layer... })`.
- Parallax: pass `offset: cameraX * depth` to `Art.ridge/forest/ground/grass/trail`.
- Whole-frame grading: `Art.desaturate(ctx, amt)`, `Art.colorize(ctx, color, amt)`.

## Palettes — `Art.TOD`

`dawn, morning, golden, dusk, night`. Each has `sky[3], sun, haze, far, mid, summit, snow,
trees[3] (far→near), ground, ground2, trail, grass, light, fog`. Blend with
`U.mixDeep(Art.TOD.a, Art.TOD.b, k)`; grey a palette with `Art.desatPalette(P, amt)`.
Never invent new environment colors when a palette entry exists.

## Environment primitives

`Art.sky(ctx, P, {horizon})`, `Art.sun(ctx, x, y, r, color, a)`, `Art.stars(ctx, {...})`,
`Art.clouds(ctx, {...})`, `Art.ridge(ctx, {seed, y, amp, color, offset})`,
`Art.ridgeY(x, sameOpts)`, `Art.summit(ctx, {x, y, h, w, P, glow, t, flag})` → tip `{x,y}`,
`Art.ground(ctx, {y, amp, offset, color, color2})`, `Art.groundY(x, {y, amp, offset})`,
`Art.trail(ctx, {...})`, `Art.forest(ctx, {seed, y, offset, spacing, hMin, hMax, color, light, kind:'pine'|'round'|'mix', sway, t})`,
`Art.pine(ctx, x, y, h, color, {sway, light})`, `Art.roundTree`, `Art.grass(ctx, {y | y:(x)=>..., offset, color, t})`,
`Art.fern(ctx, x, y, s, color, sway)`, `Art.bush`, `Art.rock(ctx, x, y, w, h, color, seed)`,
`Art.glow(ctx, x, y, r, color, a)`, `Art.rays(ctx, {...})`, `Art.motes(ctx, {...})` (dust,
pollen, fireflies via `glow`/`blink`), `Art.fog(ctx, {y, h, color, alpha})`.

**The summit** (`Art.summit`) is the film's recurring symbol of the goal everyone chases:
a tall snow-capped peak with a faint "promise" glow and a tiny red flag.

## Characters — `Art.person(ctx, opts)` → anchors

The cast (`Art.CAST`, do not recolor):
- `me` — the narrator ("I"): rust beanie, mustard jacket, olive pack, stubble. Male (the
  story calls him "Bro").
- `h1` — trail leader, tall, navy cap, electric-blue jacket, trekking poles. Says "Bro…".
- `h2` — ponytail, teal shell, huge orange pack.
- `h3` — curly hair, bucket hat, violet fleece.
- `h4` — buzz cut, grey hoodie, glued to his phone.
- `emb` — **Embarrassment**, the flower-shop owner: a personified emotion. Lanky, rose-pink
  skin, permanent blush, round glasses, magenta tuft of hair, green apron. Dry, deadpan.

Options: `x, y` (feet), `s` (scale; 1 ≈ 300 px tall), `facing` (1 right / −1 left), `look`,
`pose` ('stand'|'walk'|'sit'|'bench'|'crouch'|'kneel'), `walk` (phase, radians — use
`t * speed + offset`), `stride`, `lean`, `gesture` (`Art.GESTURES`: wave, shrug, point, give,
cheer, reach, open, hips, hold, holdHigh, pocket, chin, facepalm, heart, phone, phoneLook,
behind) with `gw` weight 0..1 for smooth blends, `armF/armB` [shoulder, elbow] overrides,
`reachF/reachB` {x,y} world-space IK targets, `shrug` 0..1, `head {tilt, turn, nod}`,
`face {...}`, `tired`, `bounce`, `t`, `seed`, `holdF/holdB` (fn(ctx) drawn at that hand in
local units; +x is "forward"), `glow`, `alpha`, `shadow`, `pack:false`.

Returns world-space anchors `{head:{x,y,r}, top, mouth, handF, handB, shoulder, chest, hip, feet, scale}`
— use `mouth` as a speech-bubble tail target and `top` for things above the head.

Faces (`face`): `smile` −1..1, `open` 0..1, `talk` 0..1 (animated mouth while speaking),
`eyes` ('open'|'happy'|'closed'|'wide'|'roll'|'distant'|'flat'|'sparkle'|'squeeze'),
`brow` −1 (angry) .. 1 (worried), `browUp`, `blush`, `sweat`, `lookX/lookY`, `blink`
(auto when omitted), `smirk` 0..1, `mouth:'o'`.
Standalone head: `Art.head(ctx, x, y, r, look, face, {facing, turn, t, tilt})`.

Walking: feet stay planted only if the ground scrolls at the walk speed. For a walk phase
`walk: t * k`, the rig's mean stance-foot travel is `72.32 · sin(0.42 · stride) · k · s · height`
px/s (≈ `29.5 · k · s · height` at stride 1), e.g. ≈ 141.6 px/s at k = 6, s = 0.8, height 1.
Give each character the rate `k / height` so a mixed-height group shares one ground speed.
The stance sweep is sinusoidal, so a constant scroll still slips a few px per step; scenes
01/02 tie each walker's position to its phase integral for zero average slip.

## Emotions — `Art.emotion(ctx, opts)`

Small luminous bean-shaped beings that live in the narrator's mind. Colors in `Art.EMO`:
`wonder` (amber — the one that taps him on the shoulder), `calm` (blue), `heart` (rose),
`spark` (mint), `dream` (lilac), `shy` (coral). Options: `x, y, s, color, face, arms`
('idle'|'facepalm'|'wave'|'tap'|'cheer'|'point'|'hug'|'shrug'), `t, seed, glow, facing, squash, alpha`.

## Flowers — `Art.flower(ctx, opts)` → `{head:{x,y}, r}`

**The** flower (`kind:'hero'`, default colors `Art.FLOWER`): magenta-rose petals, golden
phyllotaxis center. Options: `x, y` (stem base), `s`, `bloom` 0..1, `sat` 0..1 (0 = grey,
"invisible"), `glow`, `t`, `sway`, `droop`, `face` (0 side .. 1 front), `stemH`, `dust`,
`colors`, `kind` ('hero'|'daisy'|'tulip'|'bell'|'rose'|'wild'). `Art.pot(ctx, x, y, w, h, color)`.
`Art.phyllotaxis(ctx, {x, y, n, c, size, rot, color, color2, grow})` draws golden-angle seed
spirals (`Art.GOLDEN_ANGLE` = 137.5°).

## Text

- **Narration** → `Art.captions(ctx, t, [[t0, t1, text], ...])`. Word-by-word reveal, sits in
  the bottom bar, deferred above post-FX. One cue on screen at a time, ≤ 2 lines.
  Minimum on-screen time: `max(2.4 s, words / 2.7)` seconds. Leave ≥ 0.3 s gap between cues.
- **Dialogue** → `const b = Art.bubbles(ctx, t, [[t0, t1, text, {x, y, tx, ty, who, style, maxW}], ...])`.
  `(x,y)` is the bubble center, `(tx,ty)` the tail tip — aim it at the speaker's `mouth`
  anchor (from the previous frame's layout or a constant you compute). Sync mouths with
  `face.talk = Art.talkingAt(t, cues, 'me')`. Styles: 'speech', 'thought', 'shout', 'whisper'.
  Minimum on-screen time: `max(2.0 s, words / 2.5)`. Bubbles must not cover faces.
- **Inner voice** (the emotions speaking) → `Art.hand(ctx, text, {x, y, size, reveal, color, glow})`
  (Caveat handwriting) or a 'thought' bubble.
- **Big words** (e.g. "I stop.") → `Art.title(ctx, text, {y, size, reveal, alpha, now:false})`.
- Typography uses curly quotes/apostrophes (’ “ ”) and the em dash (—) and ellipsis (…).

## Audio

Scenes don't make sound directly; they declare `mood` and `sfx`. The audio engine
(`js/audio.js`) plays a mood bed and fires cues when playback crosses them.

Moods: `title, forest, wonder, tender, cosmic, machine, dusk, comedy, town, shop, parking,
reflection, silence`.

SFX ids: `chime, swell, whoosh, sparkle, pop, bird, footsteps, step, heartbeat, tap, thud,
bell, register, cash, sigh, laugh, chuckle, gasp, boing, ding, whisper, car-door, engine,
petal, paper, squelch, clock, scratch, breath, wind, shimmer, bloom`.
Optional per-cue `{gain: 0..1}`. A scene may switch moods mid-way with
`moods: [[0, 'forest'], [12.5, 'wonder']]` (local times) instead of `mood`.

## Checking your work

```
node tools/snap.js --list
node tools/snap.js --scene trail --every 1.5 --sheet /path/to/sheet.png --cols 4
node tools/snap.js --scene trail --times 3,7.5 --out /path/to/dir      # full-res frames
node tools/snap.js --scene trail --every 3 --sheet /path/s.png --timing
node tools/snap.js --page tools/lab.html --T 5,15,25,35,45,55 --out /path   # model sheets
```

Look at the images (Read tool). Iterate until every frame would survive a frame-by-frame
critique: readable text, no bubble over a face, feet on the ground, nothing clipped by the
letterbox, consistent cast looks, deliberate composition, motion that reads clearly across
the contact sheet. Write scratch images to your scratchpad, not the repo.
