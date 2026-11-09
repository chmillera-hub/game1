# FEAR — `CHARS.FEAR` (speaker `'FEAR'`)

Files: `web/src/chars/fear.js` (rig), `web/src/labs/fear.js` (lab), this doc. One core change was made (see
"Core change" at the end: the one-line `SweepTube` arc-length fix).

```bash
node tools/render.js sheet --lab fear --from 0 --to 3.5 --n 8 --cols 8 --out out/sheets/fear_turn.jpg        # turntable
node tools/render.js sheet --lab fear --from 4.7 --to 29.7 --n 26 --cols 9 --out out/sheets/fear_expr.jpg    # 26 expressions, 1 s each
node tools/render.js sheet --lab fear --from 30.5 --to 108.5 --n 40 --cols 10 --out out/sheets/fear_act.jpg  # poses / actions
node tools/render.js bench --lab fear --t 31
```
Lab segments (exported as `segments` = `[start, end, name]`, HUD label on every frame):
0–4 turntable · 4–30 expressions: neutral, worried, nervous, scared, terror, flinch, cry, sob, sniffle, startle,
listen, curious, peek, wonder, awe, shy, shySmile, hopeful, relieved, happy, giggle, sad, gulp, trust, whimper,
confused · 30 idle · 33 walk · 36 sneak (timid steps) · 40 run (scurry) · 42.5 **startle + "what's that noise?"**
(crash off-left, head snaps toward it, tuft perks, talks, gulps) · 47.5 tremble ramp + self-hug · 50.5 **cage**:
cowers gripping two bars, trembles, cries, then peeks out hopeful · 56.5 sob → **wipes tears** (left, then right
fist; sniff + shoulders up after each) · 62 **hugs itself** (clutches its scarf, rocks) · 65.5 **looks UP in
wonder** (head.pitch −0.6, mouth open, eyes wet and huge, pupils dilated, tears of awe, hands clasped) · 71 **shy
smile** (eyes down, one quick glance up, blush, fidgeting fingers) · 75 partner: takes a big partner's finger ·
79.5 hides behind a partner's leg (both hands on it), peeks out · 83 sit · 86 kneel · 89 cower (hands up in front of
the eyes, squeezed '><' eyes, tremble) · 92 shy wave · 94.5 head snaps L/R (tuft secondary-motion test) · 98 talking
· **101 cage, wide front shot** · **105 cage, side shot** (both replay cower → cry → peek: clearance checks).

## Look

A small soft **pale-lavender bean/teardrop**: head and body are ONE smooth shape (smooth union of a full lower
ellipsoid and a head ellipsoid whose crown tapers and leans back), so it is wider at the bottom with a narrower crown,
and has a gentle kidney curve in profile (tummy forward, crown back). No neck. Inner-being shading: MeshPhong + core
`enhance()` (pink wrap "subsurface" tint, lavender fresnel rim that blooms gently, a faint slow fizz), a faint additive
aura in wide shots only, and sparse slow star motes (≈1.6/s).

**Oversized round eyes** (r 8 cm, set fairly deep so they don't stick out like lenses) with big **soft violet-grey
irises** (darker outer ring, lighter violet centre, dark limbal ring), an off-white sclera that the rig keeps
**below the bloom threshold** whatever the set's `EYE_LIGHT` is, and catchlights. **Heavy upper lids** with a dark-plum
lash line. **Thin worried plum brows** (the baseline already has the inner ends lifted). A painted mouth (plum line,
dark-plum interior, pink tongue), wider than before (half-width 4.7 cm). Closed eyes can **squeeze**: flattened lid
domes, both lids rolled into one slanted line (no sclera at the corners), a crease from the inner corner (the eyes read
as `> <`), a short lid-fold crease, and cheek push lines + highlight under each eye.

**Antenna tuft**: three thin, soft, drooping wisps of different lengths (16, 12 and 9 cm) with small **glowing bulb
tips**, driven by secondary motion. Thin arms with **small four-digit hands** (3 fingers + thumb), **knobbly little
legs** (knee knobs, ankle knobs) on **round feet**. A **chunky, lopsided, hand-knitted mustard scarf**: about 1¼ turns,
so the last quarter rides up over the first pass on Fear's left; it sags at the back-right and its thickness varies.
It has a procedural V-stitch knit (colour plus a derivative bump that fades out when stitches get smaller than ~3 px,
so it doesn't shimmer). A knot sits at the front-left, with two spread, fringed ends: a long one down the tummy and a
short one splayed out to its left. The ends swing, keep off the bean and slide over the forearms. Original design: no
bow tie, no single curl of hair, not lanky.

Rest measurements (root at the feet, facing +Z, metres): top of the bean 0.832 · tuft tips up to ≈0.905 · head
centre (Face origin) 0.612 · eyes 0.644 (surface z 0.16, ±0.077) · mouth 0.554 (z 0.185) · scarf wrap top ≈0.48,
knot (0.139, 0.432, 0.194) · shoulders ±0.168 @0.392 · chest (0, 0.382, 0.235) · belly (0, 0.272, 0.24) ·
hip/pelvis 0.212 · widest body radius ≈0.232; with the scarf ≈0.28 (knot ≈0.30) · feet ±0.08.
Head centre: seated 0.486, kneeling 0.525, full cower 0.483.

## Pose API — `fear.update(t, pose)`

`pose` may be an object **or a function `(t) => pose`**. Passing the function (or `pose.poseAt = fn`) lets the
rig look back in time for secondary motion (tuft + scarf ends). This is recommended in scenes:
`st.fear.update(t, (tt) => fearPose(Math.max(tt, shotStart)))`. Clamping to the shot start stops a cut from whipping
the tuft. The look-back samples the pose on an **absolute time grid** (16 ms, 0.8 s), so a fast head snap gives the
same lag → overshoot → settle whatever frame is rendered. Without a function, the rig extrapolates the current pose
(`pose.vel` [m/s] and the walk cadence); tremble, walk bob, breathing and idle sway still drive the tuft.

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
| `body.shrug` | 0..1 head sinks into the scarf (the scarf slips down a little), arm roots rise |
| `body.slump` | 0..1 sad deflate |
| `body.recoil` | lean/shift back (flinch away), can be negative |
| `body.squash` / `body.stretch` | squash (+) / stretch volume about the pelvis (0.05–0.12 is plenty) |
| `body.bounce` | extra vertical offset (hops) |
| `body.breathe`, `body.breathRate` | breathing amplitude multiplier (default 1) / rate (breaths per second, default 0.32) |
| `body.idle` | idle micro-sway multiplier (default 1; 0 for dead-still) |
| `body.tiptoe` | 0..1 heels up |
| `body.feet` | `{ L: [x,y,z], R: [...] }` root-space ankle overrides, `body.feetMix` 0..1 |
| `walk` | `{ amount 0..1, phase (cycles), style, rate? }`. Styles: `walk` (0.37 m/s), `sneak`/`tiptoe` (timid crouched tiptoe steps with lift-and-hold and hands up at the chest; 0.16 m/s), `run`/`scurry` (panicked scurry with flailing arms; 0.99 m/s), `waddle` (0.27 m/s), `stomp`. Speed = `walkSpeed(style, rate)` = 4·stride·rate. The scene moves `pos`; `walk.phase` should advance at `rate` cycles/s. |
| `head.yaw/pitch/roll` | relative to the body. **pitch < 0 looks UP** (−0.6 = look up at the sky; clamp −0.8..0.6); yaw + turns toward its left; clamp ±1.35 |
| `head.look`, `head.track` | world point / Character / `'camera'` the head turns toward, weight 0..1 (default 1). Use ~0.45–0.6 and let the eyes do the rest. |
| `head.up`, `head.forward` | small extra head offsets (m): peeking out (`forward` 0.01–0.02), stretching up |
| `gaze` | eyes: Vector3 / [x,y,z] / Character / `'camera'` / null (+ `face.gazeYaw/gazePitch` offsets) |
| `face` | flat Face params or a preset name string (`'scared'`). Partial objects merge over Fear's baseline (anxious: lids a touch wide, inner brows up, slightly small pupils). Build with `FX(name, over)`, blend with `mixFace(a, b, u)` (handles per-side keys). Fear-only params: **`squeeze`, `squeezeL`, `squeezeR`** (0..1: squeezed-shut eyes, use with `lidU` ≈ 0 or `blink` 1 and `lidL` ≈ 1). |
| `speech` | false / sample (default: automatic lip-sync for speaker `'FEAR'`) |
| `blinkAt` | extra explicit blink times |
| `armL`, `armR` | see below |
| `extra` | see below |

**The head can never sink so far that the mouth goes behind the scarf**: the mouth line is held ≥ 3.2 cm above the top
of the wrap (a smooth limit on the head's vertical offset), whatever cower, shrug, sob or pitch does. Lids at
`lidU` < ~0.2 are closed like a blink, **per side**, so a single eye can shut (peek, wipe).

### Arms — `armL` / `armR`
`{ preset, from, mix, target, reach, hand, palm, fingers, pole, shoulder, grip, bar, barRadius, stretch, rub, rubRate, wave, waveRate, fidget, squeeze }`
- Arms are a two-bone IK with **rubber-hose stretch**. Reach is ≈0.23 m at rest length; for farther targets the bones
  stretch up to `stretch` × (default **1.36**, so ≈0.31 m). Every arm point except the buried root is **kept
  outside the bean and the scarf**, so arms wrap around the body instead of passing through it.
- `preset` (defined for the left arm, mirrored for the right):
  - Body frame:
    - `rest`.
    - `hug`: hugs itself. The arm roots slide forward-in, elbows tuck low at the sides, and the forearms rise in a
      crossed V so both **fists clutch the scarf** under the chin (R fist a bit higher and in front), kneading it
      slightly. Combine with `body.shrug` ~0.5, `hunch` ~0.2, `squash` 0.04, a small `twist`/`tilt` rock and
      `head.pitch` ~0.1.
    - `clasp`: hands together at the chest (hopeful, pleading, wonder).
    - `chest`: hand on heart.
    - `tummy`.
    - `fidget`: shy; index fingers fiddling in front of the tummy, `fidget` 0..1 motion.
    - `behind`.
    - `up`: startle, hands thrown up, fingers splayed.
    - `shrug`: palms up.
    - `point`.
    - `wave`: `wave` 0..1 amount, `waveRate` Hz.
    - `reach`.
    - `tiptoe`: sneak hands.
    - `flail`: run.
    - `grip`, `hold`.
  - Head frame (they follow the head):
    - `wipe`: a small **fist, palm to the face, rubbing the lower half of the eye**, with a slow, large knuckle rub
      (`rub` 0..1, `rubRate` default 1.25 Hz). The head tilts into the hand automatically, and the wiped eye squeezes
      shut with creases (`squeeze` 0..1 limits this).
    - `cover_mouth`: gasp.
    - `cheeks`: hands on cheeks.
    - `shield`: cowering; hands up **in front of the eyes**, palms out.
    - `eyes`: hands over the eyes.
    - `chin`.
    - `bite`: fingertips at the mouth, nervous.
  - Aliases: `crossed` / `self` / `scarf` → hug, `hips` → tummy, `pocket` → behind, `heart` → chest. `ARM_PRESETS`
    lists them all.
- `from` + `mix` blend between two presets; `reach` 0..1 blends from `rest` toward the preset/target (use it to
  animate any reach).
- `target` (a world point) overrides the wrist. With `preset: 'grip'` (or `grip: true`) the target is a point on a
  **bar**. The palm faces the bar, the fingers wrap around it (`bar` = world axis, default vertical; `barRadius`
  default 0.008), the hand closes, and the arm root slides ~3 cm toward the bar on the soft bean. Targets beyond
  ≈0.31 m from the shoulder are clamped: the arm goes straight and the hand stops short.
- `hand` = core `Hand.pose` overrides (`curl, point, spread, thumb, cup, splay, grip`). `palm` / `fingers` are world
  directions, `pole` is a world elbow hint, and `shoulder` = [dx,dy,dz] adds extra arm-root slide in body space.
- While walking with no arm preset, the walk style drives the arms (swing / tiptoe hands / flailing). Free hands
  shake with `extra.tremble`; hands on a `target` stay put.

### Extras — `extra`
| field | meaning |
|---|---|
| `tremble` 0..1 | small shake of body, head and hands (≈3 mm body amplitude at 1), plus a soft ~10 Hz quiver of the tuft (≈0.08 rad); the body shake also reaches the tuft through the spring. Lip tremble, faster breathing. Compression-friendly: at 0.8 the tuft tip drifts a few px per frame rather than jumping. |
| `cry` 0..1 | wet eyes, tear streaks (decal), glossy **tear drops** that well at the lower lid and roll down the cheeks (1–2 per eye, rate ∝ cry), a watery meniscus on the lower lids, lip wobble. Face `tearL/tearR/wet` still work on their own. |
| `sob` 0..1 | irregular sob hiccups (~1.3 Hz): shoulders jerk, head sinks (never behind the scarf), mouth pumps |
| `startle` 0..1 | key it as a quick envelope (up 0.06 s, down 0.5 s): hop + stretch, eyes snap wide, pupils shrink, tuft perks |
| `tuftPerk` 0..1 | the wisps straighten and stand up, alert ("what's that noise?") |
| `tuftDroop` 0..1 | the wisps flop outward and down (sad, defeated) |
| `tuftWobble` | secondary-motion gain multiplier (default 1) |
| `glow`, `fizz`, `aura`, `motes` | inner-being rim/glow multiplier, surface fizz, aura sprite (auto-faded in close-ups), mote rate (all default 1) |

### Face presets (`FX(name)`, Fear-tuned; unknown names fall back to core `EXPR`)
- `neutral` (baseline: anxious, not deadpan)
- `worried`
- `nervous` (clenched-teeth nervous grin, darting eyes)
- `scared`, `terror` (big open mouth)
- `flinch` / alias `squeeze` (eyes squeezed `><`, inner brows **up** and pinched, clenched grimace)
- `cry`, `sob` (squeezed eyes, open mouth), `sniffle`
- `startle`
- `listen` (wide-eyed, one brow up, small 'o': "what's that noise?")
- `curious`
- `peek` (right eye squeezed, left open)
- `wonder` (huge eyes, pupils 1.5, wet, mouth open), `awe` (wonder + tears + small smile)
- `shy` (eyes **down**, inner brows up, tiny pressed smile, strong blush), `shySmile` (the same with a small closed
  smile, no smirk)
- `hopeful`, `relieved`, `happy` (open-eyed delight), `giggle`
- `sad`
- `gulp` (pressed lips, wide eyes)
- `trust`, `whimper`, `confused`

Heavy lids are reserved for sad, tired and crying. Any face param can be overridden, and per-side lids, brows and
squeeze (`lidUL`, `browInR`, `squeezeL`, …) work.

## Anchors (world, valid after `update`)
- Head: `head` (Face origin), `eyes`, `eyeL`, `eyeR`, `mouth`, `mouthOut` (0.3 m in front of the mouth), `earL`,
  `earR` (the sides of the head, since Fear has no ears; use as whisper targets), `top`.
- Tuft: `tuft` (tip of the long wisp, moves with the wobble), `tuftBase`.
- Body: `chest`, `back`, `belly`, `hip`, `scarf` (the knot).
- Limbs: `shoulderL`, `shoulderR`, `handL`, `handR` (palm centres), `footL`, `footR` (on the floor).
- Helper: `fear.tearPoint('L'|'R')` returns the world point under an eye's outer corner (for tears, or a partner
  wiping Fear's tears).

## Recipes
- **Cowering in the cage, gripping bars**:
  - Put Fear **at the cage centre**, at most ~3 cm off it. Grip bars **beside the shoulders, at ±50–60° from
    Fear's facing**, at y ≈ 0.43–0.50 (the arms stretch and the arm roots slide to reach them).
  - Pose: `body: { cower: 0.55 }`, `extra: { tremble: 0.6, cry: 0.8 }`,
    `armL: { preset: 'grip', target: barL, reach }`, `armR: { preset: 'grip', target: barR, reach }`,
    `face: FX('scared')` → `mixFace(.., FX('cry'), u)`.
  - Peek out: lower `cower`, `head: { up: 0.02, forward: 0.015 }`, `FX('hopeful')`.
  - Clearance: in the lab cage (R 0.42, 16 bars, Fear 2 cm in front of the centre), the body, scarf, knot, tails and
    eyes stay **≥ 8.9 cm inside the bars** through the whole beat, cower lean and peek included (checked numerically
    over 50.5–56.5). Fear's footprint is ≈0.28 m from its centre (≈0.30 at the knot) plus ~4 cm of forward lean, so
    any cage with R ≥ 0.36 works with Fear centred. Do NOT push Fear toward the front bars to make the grip
    reachable.
- **What's that noise?**: key `extra.startle` (0.06 s up / 0.5 s down) plus `blinkAt` on the hit. Use
  `head: { look: noisePoint, track: 0.45 }` snapping in ~0.12 s, `body.twist` −0.18 toward the noise and
  `extra.tuftPerk` 0.8. Face `FX('startle')` → `FX('listen')` for the line, `armL: { preset: 'up', mix: 0.7 }`
  briefly, then `FX('gulp')`. Frame with ≥ 0.1 m of headroom above the tuft: perked wisps reach ≈1.0 m.
- **Looking up in wonder**: `head: { pitch: -0.6 }`, `body: { lean: -0.06, stretch: 0.02 }`, `FX('wonder')` →
  `FX('awe')` with `extra.cry` 0.4, `face.gazePitch` +0.2, arms `clasp`, `extra.glow` 1.3. Frame from a 3/4 front
  angle at or slightly below eye level; a high camera only sees the top of the tilted head.
- **Crying / wiping**: `FX('sob')` + `extra: { cry: 1, sob: 1, tuftDroop: 0.6 }`, then
  `armL: { preset: 'wipe', from: 'rest', mix }` (envelope ~1.7 s). End each wipe with a sniff:
  `body.shrug` 0.45 pulse (0.5 s) and `FX('sniffle', { mPout: 0.6, mPress: 0.6 })`.
- **Hugging itself**: `armL/armR: { preset: 'hug', from: 'rest', mix }` (R 0.15 s later),
  `body: { shrug: 0.55, hunch: 0.22, squash: 0.04, twist: 0.07·rock, tilt: 0.045·rock }` with
  rock = sin(t·2π·0.55), `head: { pitch: 0.1, roll: -0.08 }`, `FX('whimper', { lidU: 0.86 })`, `extra.tremble` 0.25.
- **Shy smile**: `FX('shy')` → `FX('shySmile')` (eyes down, so use `gaze: null`). For ONE quick glance up, blend to
  `FX('shySmile', { lidU: 1.05, gazePitch: 0, gazeYaw: 0 })` with `gaze: 'camera'` for ~0.5 s. Add
  `head: { roll: -0.15, pitch: 0.14 }`, arms `fidget`, `body: { shrug: 0.25, twist: small sway }`.
- **Cower**: `body.cower` 1, `FX('scared')` → `FX('flinch')`, both arms `shield` (R 0.05 s later),
  `head: { pitch: 0.12, yaw: -0.22 }`, `extra: { tremble: 0.8, tuftDroop: 0.5 }`.
- **Timid steps**: `walk: { amount: 1, style: 'sneak', phase: u * 0.8 }`, move `pos` at `walkSpeed('sneak')`,
  `FX('nervous')`, darting eyes (`gaze` at points around), `extra.tremble` 0.15.
- **Holding a partner's finger / clinging**: `armL: { preset: 'hold', target: partner.anchor('handR'), reach }`
  (+ `hand: { grip: 0.9 }`). To cling to a leg or post, put two `target`s ON its near surface (offset ~1 cm along
  the normal toward Fear, ±3.5 cm sideways) with `palm` = −normal. Keep them within ≈0.3 m of the shoulders.

## Performance
- Rig JS ≈ 3–5 ms/frame in-page. This includes the 50-sample spring look-back, 11 swept tubes, IK, arm collision and
  copying parts into the combined meshes. The face decal canvas is redrawn only when mouth, tear, blush or squeeze
  values change.
- GPU (SwiftShader) is the real cost, and on SwiftShader with 4× MSAA HDR every draw call and every triangle counts.
  So:
  - All limbs (arm and leg tubes, hands, knees, feet) are copied each frame into ONE dynamic mesh, as are the scarf
    parts, the tuft, the brows, the lids and the lashes. That is ≈20 draws instead of ≈64.
  - ≈20k triangles instead of ≈32k: the eyeballs are front caps only, and lids, hands and scarf are re-tessellated.
  - The being parts use Phong + `enhance()` instead of physical sheen. The knit is procedural instead of a
    map + bump texture (texture fetches were most of the scarf's cost). The tears use Standard instead of clearcoat
    physical. Only the body and the scarf cast shadows. The aura is faded out in close-ups.
- Measured as CPU-seconds per frame in the browser processes (load-robust; the machine was at load 7–33 on 4 cores
  the whole time). Old and new rig were interleaved in one browser on the same lab frames. Fear's increment over the
  lab with Fear hidden:

  | lab frame | new rig | old rig |
  |---|---|---|
  | t=31 full-body | **0.43–0.51** | 0.76–0.80 |
  | t=52.5 cage | **0.43–0.48** | 0.78–0.83 |
  | t=60 cry close-up | **0.67–0.74** | 1.08–1.12 |
  | t=68 wonder 3/4 | **0.40–0.47** | 0.78–0.90 |

- Wall clock in a lower-load window (load ≈7–9), same page, interleaved:

  | lab frame | Fear lab, Fear visible | Fear lab, Fear hidden | facetest |
  |---|---|---|---|
  | full-body | 0.62 s | 0.47 s | 0.46 s |
  | close-up | 0.86 s | 0.58 s | 0.70 s |

  The lab's own base equals facetest's; Fear adds ≈0.15–0.28 s.
- Re-bench on an idle machine; `tools/render.js bench` numbers from the final run are in the report.

## Known limitations / tips
- The head bend happens in a zone just above the scarf; the face and decal are rigid above it. At extreme pitch
  (|pitch| > 0.6), tear drops near the bottom of their path can sit a few mm off the skin.
- The scarf follows ~45 % of the head bend (it "slips" on the body) so it stays level when looking up.
- Arms: ≈0.23 m reach, stretching to ≈0.31 m. Targets beyond that are clamped (the hand stops short), so keep grip
  and cling targets within ~0.3 m of the shoulders. Arm collision is against the bean + scarf band only (not against
  the other arm), and the hands themselves don't collide.
- The self-hug clutches the scarf with crossed forearms; with these short arms Fear cannot reach round to its own
  back, by design.
- Secondary motion depends on the pose history: pass the pose **function** (see above) to get lag and overshoot from
  head snaps and walking.
- Shadows are cast by the un-bent bean (the depth material has no bend), which is invisible at Fear's scale.
- The face decal (mouth, tears, blush) is a canvas texture. When the mouth changes every frame (talking, lip
  tremble), the canvas is re-rasterised and uploaded every frame (≈0.1 CPU-s in close-ups). This is core Face
  behaviour, shared by every character.
- In the combiners, hidden sub-parts must be hidden via `obj.userData.hide = true`: the parts themselves are excluded
  with `layers` and are not drawn individually.

## Core change
`core/limbs.js` `SweepTube.update()` reassigned `this.curve.points` without setting `this.curve.needsUpdate = true`.
So three's `Curve.getPointAt()` reused the **previous frame's arc-length table**, and tube vertices (brows, arms, legs,
hair locks, scarf ends…) depended on which frame was rendered before. Frames were not a pure function of t when
rendered out of order, for EVERY rig using SweepTube. The one-line fix (`this.curve.needsUpdate = true;` right after
`this.curve.points = pts;`) is now applied in core, and Fear's local `pureTube()` patch is removed. With it, Fear's
lab renders byte-identically regardless of the previously rendered frame (checked at t = 53.8, 95.45, 59.2 and 43.2
after unrelated frames). Fear also makes its own Face decal drawing a pure function of Face's 3-decimal redraw key,
and flattens squeezed eyes BEFORE Face places the catchlights.
