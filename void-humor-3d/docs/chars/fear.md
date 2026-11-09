# FEAR — `CHARS.FEAR` (speaker `'FEAR'`)

Files: `web/src/chars/fear.js` (rig), `web/src/labs/fear.js` (lab), this doc. **No core files were modified**
(see "Core issue found" at the end: one core bug is worked around locally).

```bash
node tools/render.js sheet --lab fear --from 0 --to 3.5 --n 8 --cols 8 --out out/sheets/fear_turn.jpg       # turntable
node tools/render.js sheet --lab fear --from 4.7 --to 29.7 --n 26 --cols 9 --out out/sheets/fear_expr.jpg   # 26 expressions, 1 s each
node tools/render.js sheet --lab fear --from 30.5 --to 100.5 --n 36 --cols 9 --out out/sheets/fear_act.jpg  # poses / actions
```
Lab segments (exported as `segments` = `[start, end, name]`, HUD label on every frame):
0–4 turntable · 4–30 expressions: neutral, worried, nervous, scared, terror, flinch, cry, sob, sniffle, startle,
listen, curious, peek, wonder, awe, shy, shySmile, hopeful, relieved, happy, giggle, sad, gulp, trust, whimper,
confused · 30 idle · 33 walk · 36 sneak (timid steps) · 40 run (scurry) · 42.5 **startle + "what's that noise?"**
(crash off-left, head snaps toward it, tuft perks, talks, gulps) · 47.5 tremble ramp + self-hug · 50.5 **cage**:
cowers gripping two bars, trembles, cries, then peeks out hopeful · 56.5 sob → **wipes tears** (left, then right
hand) · 62 **hugs itself** · 65.5 **looks UP in wonder** at galaxies (head.pitch −0.6, mouth open, eyes wet and
huge, pupils dilated, tears of awe, hands clasped) · 71 **shy smile** (fidgeting fingers, blush, glance up) ·
75 partner: looks up at a big partner and **takes its finger** (arm target) · 79.5 hides behind a partner's leg
gripping it, peeks out · 83 sit · 86 kneel (pleading clasp) · 89 cower (shield hands, squeezed eyes, tremble) ·
92 shy wave · 94.5 head snaps L/R (tuft secondary-motion test) · 98 talking.

## Look

A small soft **pale-lavender bean**: head and body are ONE smooth shape (smooth union of a wide lower ellipsoid
and a rounder upper one), wider at the bottom, no neck. Effervescent inner-being material (`materials.being`:
soft wrap shading with a pink sub-surface tint, lavender fresnel rim that blooms gently, slow fine fizz), a faint
additive aura behind the body and sparse slow star motes (≈1.6/s). **Oversized round eyes** (r 7.8 cm) with big
soft violet-grey irises, dark limbal ring, catchlights; **heavy upper lids** (round lid shells in body colour
with a dark-violet lash line) that can droop, squeeze or open wide; **thin worried plum brows** (baseline already
lifted at the inner ends). Small painted mouth (plum line, dark-plum interior, pink tongue). A **three-strand
antenna tuft** on top (soft tapering strands with rounded tips, brighter rim) driven by secondary motion. Thin
arms with **small four-digit hands** (3 fingers + thumb), **knobbly little legs** (knee knobs, ankle knobs) on
**round feet**. A **chunky hand-knitted mustard scarf**: lumpy spiralled wrap with V-stitch knit (colour + bump
map, low contrast), a knot at the front-left and two fringed ends that hang over the tummy, collide with the bean
and swing with motion. Original design: no bow tie, no single curl of hair, not lanky.

Rest measurements (root at the feet, facing +Z, metres): top of the bean 0.83 · tuft tips ≈0.92 · head centre
(Face origin) 0.612 · eyes 0.646 (z 0.17, ±0.081) · mouth 0.543 (z 0.19) · scarf line ≈0.46 (knot (0.106, 0.447,
0.193)) · shoulders ±0.168 @0.39 · chest (0, 0.38, 0.225) · belly (0, 0.27, 0.225) · hip/pelvis 0.212 · widest
body radius ≈0.215 · feet ±0.08. Seated head 0.49, kneeling 0.53, full cower 0.48.

## Pose API — `fear.update(t, pose)`

`pose` may be an object **or a function `(t) => pose`**. Passing the function (or `pose.poseAt = fn`) lets the
rig look back in time for secondary motion (tuft + scarf ends) — recommended in scenes:
`st.fear.update(t, (tt) => fearPose(Math.max(tt, shotStart)))` (clamp to the shot start so a cut doesn't whip
the tuft). Without it, the rig extrapolates the current pose (`pose.vel` [m/s] and the walk cadence) — tremble,
walk bob, breathing and idle sway still drive the tuft.

| field | meaning |
|---|---|
| `pos`, `yaw` | feet position, heading (0 faces +Z) |
| `vel` | optional [vx,vy,vz] ground velocity, only used for secondary motion when no pose function is given |
| `body.lean` | forward lean (rad, + forward) |
| `body.tilt` | side lean (+ toward its left / screen-right in a front view) |
| `body.twist` | body yaw relative to the feet |
| `body.crouch` | 0..1 knees bend, body lowers and leans in |
| `body.sit` | 0..1 sits on its bottom on the floor, legs stuck out front, toes up |
| `body.kneel` | 0..1 on both knees, feet tucked behind |
| `body.cower` | 0..1 composite: crouch + hunch + shrug (head sinks into the scarf) + squash |
| `body.hunch` | 0..1 curls forward, head tucks |
| `body.shrug` | 0..1 head sinks into the scarf, arm roots rise |
| `body.slump` | 0..1 sad deflate |
| `body.recoil` | lean/shift back (flinch away), can be negative |
| `body.squash` / `body.stretch` | squash (+) / stretch volume about the pelvis (0.05–0.12 is plenty) |
| `body.bounce` | extra vertical offset (hops) |
| `body.breathe`, `body.breathRate` | breathing amplitude multiplier (default 1) / rate (breaths per second, default 0.32) |
| `body.idle` | idle micro-sway multiplier (default 1; 0 for dead-still) |
| `body.tiptoe` | 0..1 heels up |
| `body.feet` | `{ L: [x,y,z], R: [...] }` root-space ankle overrides, `body.feetMix` 0..1 |
| `walk` | `{ amount 0..1, phase (cycles), style, rate? }` styles: `walk` (stride 0.055, 1.7 cyc/s → **0.37 m/s**), `sneak`/`tiptoe` (timid crouched tiptoe steps, lift-and-hold, hands up at the chest; 0.8 cyc/s → **0.16 m/s**), `run`/`scurry` (panicked scurry, arms flailing; 2.9 cyc/s → **0.99 m/s**), `waddle` (0.27 m/s), `stomp`. Speed = `walkSpeed(style, rate)` = 4·stride·rate. The scene moves `pos`; `walk.phase` should advance at `rate` cycles/s. |
| `head.yaw/pitch/roll` | relative to the body. **pitch < 0 looks UP** (−0.6 = look up at the sky; clamp −0.8..0.6); yaw + turns toward its left; clamp ±1.35 |
| `head.look`, `head.track` | world point / Character / `'camera'` the head turns toward, weight 0..1 (default 1). Use ~0.45–0.6 and let the eyes do the rest. |
| `head.up`, `head.forward` | small extra head offsets (m) — peeking out (`forward` 0.01–0.02), stretching up |
| `gaze` | eyes: Vector3 / [x,y,z] / Character / `'camera'` / null (+ `face.gazeYaw/gazePitch` offsets) |
| `face` | flat Face params or a preset name string (`'scared'`). Partial objects merge over Fear's baseline (worried-leaning brows, heavy lids). Build with `FX(name, over)`, blend with `mixFace(a, b, u)` (handles per-side keys). |
| `speech` | false / sample (default: automatic lip-sync for speaker `'FEAR'`) |
| `blinkAt` | extra explicit blink times |
| `armL`, `armR` | see below |
| `extra` | see below |

### Arms — `armL` / `armR`
`{ preset, from, mix, target, reach, hand, palm, fingers, pole, shoulder, grip, bar, barRadius, rub, wave, fidget, squeeze }`
- `preset` (left arm defined, mirrored for the right): body frame — `rest`, `hug` (hugs itself: forearms cross
  the tummy, hands clutch the opposite sides; R hand sits a little higher so they overlap), `clasp` (hands
  together at the chest: hopeful / pleading / wonder), `chest` (hand on heart/chest), `tummy`, `fidget` (shy:
  index fingers fiddling in front of the tummy; `fidget` 0..1 motion), `behind`, `up` (startle: hands thrown up,
  fingers splayed), `shrug` (palms up), `point`, `wave` (`wave` 0..1 amount, `waveRate` Hz), `reach`, `tiptoe`
  (sneak hands), `flail` (run), `grip`, `hold`; head frame (follow the head) — `wipe` (knuckles rub the eye;
  `rub` 0..1; the wiped eye squeezes shut automatically, `squeeze` 0..1 to limit), `cover_mouth` (gasp), `cheeks`
  (hands on cheeks), `shield` (hands up in front of the face, palms out — cowering), `eyes` (hands over eyes),
  `chin`, `bite` (fingertips at the mouth, nervous). Aliases: `crossed`/`self` → hug, `hips` → tummy, `pocket` →
  behind, `heart` → chest. `ARM_PRESETS` lists them.
- `from` + `mix` blend between two presets; `reach` 0..1 blends from `rest` toward the preset/target (use it to
  animate any reach).
- `target` (world point) overrides the wrist. With `preset: 'grip'` (or `grip: true`) the target is a point on a
  **bar**: the palm faces the bar, fingers wrap around it (`bar` = world axis, default vertical; `barRadius`
  default 0.008) and the hand closes. Cage recipe below.
- `hand` = core `Hand.pose` overrides (`curl, point, spread, thumb, cup, splay, grip`); `palm` / `fingers` world
  directions; `pole` world elbow hint; `shoulder` = [dx,dy,dz] extra arm-root slide in body space (the arm root
  sits on a soft bean: presets already slide it forward for hugs/clasps and up for face presets).
- While walking with no arm preset the style drives the arms (swing / tiptoe hands / flailing). Free hands
  shake with `extra.tremble`; hands on a `target` stay put.

### Extras — `extra`
| field | meaning |
|---|---|
| `tremble` 0..1 | fast small shake of body, head, hands and tuft (≈3 mm body amplitude at 1 — compression-friendly), lip tremble, faster breathing |
| `cry` 0..1 | wet eyes, tear streaks (decal), glossy **tear drops** that well at the lower lid and roll down the cheeks (1–2 per eye, rate ∝ cry), a watery meniscus on the lower lids, lip wobble. Face `tearL/tearR/wet` still work on their own. |
| `sob` 0..1 | irregular sob hiccups (~1.3 Hz): shoulders jerk, head sinks, mouth pumps |
| `startle` 0..1 | key it as a quick envelope (up 0.06 s, down 0.5 s): hop + stretch, eyes snap wide, pupils shrink, tuft perks |
| `tuftPerk` 0..1 | tuft stands up straight and alert ("what's that noise?") |
| `tuftDroop` 0..1 | tuft flops outward/back (sad, defeated) |
| `tuftWobble` | secondary-motion gain multiplier (default 1) |
| `glow`, `fizz`, `aura`, `motes` | inner-being rim/glow multiplier, surface fizz, aura sprite, mote rate (all default 1) |

### Face presets (`FX(name)` — Fear-tuned; unknown names fall back to core `EXPR`)
`neutral` (baseline: faintly worried) · `worried` · `nervous` (clenched-teeth nervous grin, darting eyes) ·
`scared` · `terror` · `flinch` (eyes squeezed shut, brows pulled down, grimace) · `cry` · `sob` · `sniffle` ·
`startle` · `listen` (wide-eyed, one brow up, small 'o' — "what's that noise?") · `curious` · `peek` (one eye
squeezed, one open) · `wonder` (huge eyes, pupils dilated 1.48, wet, mouth open) · `awe` (wonder + tears + small
smile) · `shy` (lids lowered, gaze down/aside, blush) · `shySmile` (small shy smile, blush) · `hopeful` ·
`relieved` · `happy` · `giggle` · `sad` · `gulp` (pressed lips, wide eyes) · `trust` · `whimper` · `confused`.
Any face param can be overridden; per-side lids/brows (`lidUL`, `browInR`, …) work. Lids at `lidU` < ~0.2 are
closed via `blink` internally, so squeezed eyes stay shut even when the gaze pitches.

## Anchors (world, valid after `update`)
`head` (Face origin), `eyes`, `eyeL`, `eyeR`, `mouth`, `mouthOut` (0.3 m in front of the mouth), `earL`, `earR`
(sides of the head — Fear has no ears; whisper targets), `top`, `tuft` (centre strand tip, moves with the
wobble), `tuftBase`, `chest`, `back`, `belly`, `hip`, `scarf` (knot), `shoulderL`, `shoulderR`, `handL`,
`handR` (palm centres), `footL`, `footR` (on the floor). Helper: `fear.tearPoint('L'|'R')` = world point under an
eye's outer corner (tears / a partner wiping Fear's tears).

## Recipes
- **Cowering in the cage, gripping bars**: `body: { cower: 0.55 }`, `extra: { tremble: 0.6, cry: 0.8 }`,
  `armL: { preset: 'grip', target: barPointL, reach }`, `armR: { preset: 'grip', target: barPointR, reach }`,
  `face: FX('scared')` → `mixFace(.., FX('cry'), u)`. Arms reach ≈0.25 m from the shoulders; with a round cage of
  radius ~0.4 put Fear ~0.15 m off-centre toward the front and grip the bars just beside the face (lab: bars at
  ±34°, y ≈ 0.45–0.5). Peek out: lower `cower`, `head: { up: 0.02, forward: 0.015 }`, `FX('hopeful')`.
- **What's that noise?**: key `extra.startle` (0.06 s up / 0.5 s down) + `blinkAt` on the hit, `head: { look:
  noisePoint, track: 0.45 }` snapping in ~0.12 s, `body.twist` −0.18 toward it, `extra.tuftPerk` 0.8,
  `FX('startle')` → `FX('listen')` for the line, `armL: { preset: 'up', mix: 0.7 }` briefly, then `FX('gulp')`.
- **Looking up in wonder**: `head: { pitch: -0.6 }`, `body: { lean: -0.06, stretch: 0.02 }`, `FX('wonder')` →
  `FX('awe')` with `extra.cry` 0.4, `face.gazePitch` +0.2, arms `clasp`, `extra.glow` 1.3. Frame from a 3/4 front
  angle at or slightly below eye level — a high camera only sees the top of the tilted head.
- **Crying / wiping**: `FX('sob')` + `extra: { cry: 1, sob: 1, tuftDroop: 0.6 }` then
  `armL: { preset: 'wipe', from: 'rest', mix }` (envelope ~1.5 s) and `FX('sniffle')`.
- **Shy smile**: `FX('shySmile')`, `head: { roll: -0.14, pitch: 0.1 }`, arms `fidget`, `body: { shrug: 0.25,
  twist: small sway }`, gaze down/aside then a quick glance at the partner.
- **Timid steps**: `walk: { amount: 1, style: 'sneak', phase: u * 0.8 }`, move `pos` at `walkSpeed('sneak')`,
  `FX('nervous')`, eyes darting (`gaze` at points around), `extra.tremble` 0.15.
- **Holding a partner's finger / clinging**: `armL: { preset: 'hold', target: partner.anchor('handR'), reach }`
  (+ `hand: { grip: 0.9 }`); clinging to a leg: two `target`s on the leg's near surface with `palm` facing it.

## Performance
Rig JS per frame ≈ 2–3 ms (measured in-page, incl. the 30-sample spring look-back for the tuft/scarf, 11 swept
tubes, face decal redraw only when mouth params change). Body: one 57×47 SDF-generated mesh with a vertex-shader
head bend (no CPU re-skinning). GPU cost is a single physical "being" material over most of the character;
the lab frame measured 0.95–2.2 s on SwiftShader **while the 4-core machine was at load average 10–13**
(the trivial `facetest` lab measured 1.0–1.7 s in the same conditions, i.e. Fear's lab ≈ 1.2–1.4× facetest).
Re-bench on an idle machine before trusting absolute numbers.

## Known limitations / tips
- The head bend happens in a zone just above the scarf; the face/decal are rigid above it. At extreme pitch
  (|pitch| > 0.6) tear drops near the bottom of their path can sit a few mm off the skin.
- The scarf follows ~45 % of the head bend (it "slips" on the body) so it stays level when looking up.
- Arms are short by design (not lanky): reach ≈0.25 m from the shoulder. Targets out of reach are clamped
  (arm straight). For self-hug / clasp the arm roots slide forward on the bean automatically.
- Secondary motion depends on the pose history: pass the pose **function** (see above) to get lag/overshoot from
  head snaps and walking; with a static pose object only time-driven motion (tremble/walk/breath) drives it.
- Shadows are cast by the un-bent bean (depth material has no bend) — invisible at Fear's scale.
- Eyelids are core `Eye` shells; when nearly closed they read as soft round "heavy lids" (by design).

## Core issue found (worked around locally, not edited)
`core/limbs.js` `SweepTube.update()` reassigns `this.curve.points` but never sets `this.curve.needsUpdate = true`,
so three's `Curve.getPointAt()` reuses the **previous frame's arc-length table** — tube vertices (brows, arms,
legs, hair locks, scarf ends…) depend on which frame was rendered before, i.e. frames are not a pure function
of t when rendered out of order. Fear patches its own tube instances (`pureTube()` in `fear.js`, including its
Face brow tubes); with the patch, the same t renders bit-identically in any order (verified: 0 differing pixels).
Suggested one-line core fix: add `this.curve.needsUpdate = true;` right after `this.curve.points = pts;` in
`SweepTube.update`. Other rigs using SweepTube are affected until then.
