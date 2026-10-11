# Animation code contract (read before writing any module)

Stack: Node 22 ESM + `@napi-rs/canvas` (Skia, Canvas2D API). Frame = 720x1280 portrait, 24 fps.
All drawing is deterministic in time `t` (seconds): never use Math.random() or Date — use `rand(i, seed)`,
`noise1(x, seed)`, `fbm(x, seed)` from `src/engine.mjs`.

## Files you must NOT edit (shared core; other agents depend on them)
`src/engine.mjs`, `src/face.mjs`, `src/timeline.mjs`, `src/render.mjs`, `src/chars/fear.mjs`.
If you need a helper they lack, write it locally in your own module. Read them first — reuse
`ease`, `kf`, `clamp/lerp`, `ik`, `limb`, `glow`, `groundShadow`, `blobPath`, `rgba/shade/mixColor`, `autoBlink`,
`drawFace`, `makeExpr`, `EXPR`, `withSpeech`.

## Character module contract
```js
export function drawX(g, x, y, scale, pose)   // (x,y) = ground point between the feet (world coords)
```
- Must `g.save()`/`g.restore()`; must not leak transforms, alpha, filters, composite ops or shadow settings.
- `pose.t` drives idle life: breathing, subtle sway, automatic blinking (`autoBlink(t, seed)` unless `face.noAutoBlink`).
- Common pose fields (support all that make sense for your character, same names/semantics as fear.mjs):
  `face` (expression object for drawFace), `facing` (1/-1 mirror body; face stays readable), `headTilt` (rad),
  `headTurn` (-1..1 yaw; pass to face as `turn`), `headDX/headDY`, `lean` (rad), `crouch` (0..1),
  `tremble` (0..1), `breathe` (amplitude, default 1), `armL/armR` (`{target:[x,y], bend, front, hand}` in
  character-local coords: origin = feet, y negative = up — or a preset name), `walk: {phase}`, `shadow`, `alpha`.
- Export your arm presets object and your face style object (like `FEAR_ARMS`, `FEAR_FACE`) and export a
  `HEIGHT` constant (px at scale 1) and useful local anchor points (e.g. `ANCHORS = { shoulderR:[x,y], headTop:[x,y], hand reach }`).
- Faces MUST use `drawFace` from face.mjs with a per-character style so all faces act with the same
  parameter vocabulary (lids, brows, gaze, mouth, tears, blush, sparkle).
- Lip-sync: scenes pass `face: withSpeech(expr, S.lip('FEAR', t))` — your module just draws the face it's given.

Scale reference (world px at scale 1): FEAR ≈ 330 tall. CONSCIOUSNESS/SELF ≈ 600 tall (Fear ≈ 55% of it).
Emotions ≈ 420–520 tall. THE VOID ≈ 1700 tall (it must tower; in wide shots it is drawn at smaller scale for depth).

## Set / view module contract
```js
export function drawHQ(g, view, state)        // view ∈ 'front' | 'back' | 'alarm' | 'backOfMind'
export const HQ_VIEWS = { front: { width, height, anchors: { name: [x, y, scaleForCharacters] } }, ... }
```
Each view is its own world-coordinate stage (≥ 720x1280, may be larger for camera moves). `anchors` give
where characters stand and the perspective scale to draw them at. Scenes call `applyCamera(g, cam)` (engine)
then `drawHQ(...)`, then characters, then optional foreground/overlay layers (`drawHQForeground(g, view, state)`).

## Style guide
- Look: warm, soft, storybook 2D. Clean shapes, gentle radial-gradient shading (light from upper-left unless
  a scene light dominates), tinted dark outlines (never pure black), ~2.5–3.5 px lines at scale 1.
- Palette anchors: HQ walls deep indigo/plum `#1d1936 #2b2550 #3a3266`; console warm amber glow `#ffcf7a`;
  screen-of-consciousness cool daylight `#9fd8ff #cfeeff`; alarm red `#ff4d5e`; back-of-mind near-black violet
  `#0d0b1c` fading into the room; Void body `#0a0914` with violet rim `#8a6cff` and faint cyan `#5ad1ff`.
  Emotions: JOY gold `#ffc94a`, SADNESS blue `#6fa8e8`, ANGER coral red `#f0634f`, CALM mint `#7fd6b0`.
  Fear lavender `#b9a6ea`. Self/Consciousness: warm skin `#d9a27e`, dark hair `#2f2433`, sweater dusty teal `#4f8c8a`, blazer charcoal `#3a3d4a`, gold badge `#e8c25a`.
- COMPRESSION-FRIENDLY (the film must fit in < 15 MB): smooth gradients and flat fills; NO film grain,
  noise textures, per-frame random flicker over large areas, or busy high-frequency patterns. Twinkles must
  be small. Idle motion should be gentle and slow.

## Performance budget
A full frame should render in < 40 ms. Cache static artwork in offscreen canvases created ONCE per process
(`createCanvas` from '@napi-rs/canvas'; key caches by parameters), and draw them with `drawImage`.
Avoid `ctx.filter = 'blur(...)'` on large areas per frame (use radial gradients for glows, or blur once into a cache).

## Testing your module
Write a sheet script in `tools/` (see `tools/sheet_fear.mjs`) that renders a labelled grid PNG of your
module's states into `out/`, then LOOK at the PNG (Read the image) and iterate until it is genuinely good.
Render timing: measure ms per draw call with a loop of ~50 draws.
