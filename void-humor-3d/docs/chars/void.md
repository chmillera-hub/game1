# THE VOID — `CHARS.VOID` (speaker `'VOID'`)

Files: `web/src/chars/void.js` (rig), `web/src/chars/void_parts.js` (mitt hands, sleeve cuffs, tube writer),
`web/src/labs/void.js` (lab), `web/src/labs/void_probe.js` (dev API sweep: NaN / anchor / contact / whisper checks),
this doc. Nothing under `web/src/core/` was changed.

```bash
node tools/render.js sheet --lab void --from 0 --to 4 --n 8 --cols 4 --out out/sheets/void_turn.jpg          # turntable
node tools/render.js sheet --lab void --from 4.6 --to 29.6 --n 26 --cols 7 --out out/sheets/void_expr.jpg     # 26 expressions
node tools/render.js sheet --lab void --from 30.5 --to 97 --n 32 --cols 8 --out out/sheets/void_act.jpg       # actions
node tools/render.js stills --lab void_probe --t 0                                                             # API sweep (console)
```
Lab segments (exported `segments`, `[start, end, name]`; the name is shown in an on-screen label): 0–4 turntable ·
4–30 expressions (1 s each) · 30 idle · 33 walk · 36 run · 38 back · 40.5 over-the-shoulder · 43.5 whisper (real
Jesus, `solveWhisper`; wide, then close at 46.1) · 48.5 laugh + coughed stars · 52.5 crossed (front → 3/4 →
profile) · 57 eye-roll → huff & puff → turn back · 61.5 pat (real Jesus; front, then 3/4 from 63.75) · 66 arm around
(real Jesus; front, then from behind at 68.25) · 70.5 shrug · 73 donkey kick (3/4: calm face + leg) · 78 latch ·
81.5 sit · 84.5 kneel · 87 wave · 89 cosmos · 92 backlit silhouette · 95 kick seen from behind · 96.5 crossed close 3/4.
(If the Jesus rig fails to load mid-edit, the lab falls back to a stand-in with his anchor layout and logs it.)

## Look

A huge (~3.05 m to the hood tip), plump, bell-shaped hooded cloak-being. Deep indigo velvet (MeshLambert + a
key-lit violet sheen term), faint stars drifting *inside* the fabric (parallax, varied size and brightness, tinted
violet/teal, fading out toward the silhouette, a rare brighter "hero" star), faint nebula shimmer, an HDR
violet→teal fresnel rim (bloom-friendly) and sparse star motes. A shoulder **capelet** (open at the front, rounded
sloping shoulders, a thin rolled lip so its hem blends into the body) is married to the hood by a thin, soft **collar
roll** at the back/sides (max radius ~5 cm: piping, not a tyre). The **hood** is a cowl: round from behind and from the
side (only a low, soft crown at the top-back, ~10 cm: never a pointed cone or a flat-topped box), a deep edge (brim forward over the brow, sides set back, chin edge drawn
forward and down), a rolled brim that is thick at the top and thin at the sides, a soft shield-shaped opening with a
slightly off-centre V at the chin, and one asymmetric overlap fold (its left side laps over the right at the chin).

Inside: unlit **cosmic darkness** (nebula + tiny stars + a faint violet glow, vignetted to black at the brim) holding
- **Two big starlight eyes** (core `Eye`, glow mode: moon-white sclera, deep blue → teal iris, dark pupil). The lids
  are the darkness itself: the lid shader projects every lid point along the view ray onto the face surface and
  samples the face decal there, so lids show exactly what the field behind them shows (incl. the violet blush and
  the puffed-cheek glows) — no goggle/bandit mask, no bluish bulges in 3/4. As the lids close or squint, the eye
  light fades into the darkness toward the corners (socket space), so laugh / giggle eyes are tapered arcs with no
  white corner wedges, and catchlight dots hide on squeezed eyes. Soft starlight halos (analytic) dim with the lids.
- **Nebula-wisp brows**: additive glowing SweepTubes (violet inner → teal outer) + a wider faint halo tube.
- **Mouth** painted by the Void (core mouth kept invisible): a glowing crescent lip-line that opens into deeper
  cosmos (gradient, drifting nebula, stars, a tiny turning spiral galaxy in big opens). No teeth/tongue. Closed =
  lens crescent (smile U / frown arch), open = flat-ish upper lip + round bowl (laugh "D"), `mRound` → "O",
  `mPout`/puff → small round pucker, `mDroop` → sad-smile corner hooks, `mWavy` → uneasy squiggle.

**Hands**: big soft mitts — a wide pillowy palm, 3 fat fingers + thumb (anatomically correct side) as smooth swept
tubes, all ONE mesh per hand (`VoidHand`) — coming out of a **flared open sleeve cuff** (velvet outside, dark lining
inside, the hem hangs a little toward the ground). The sleeve tube tapers to 0.15 m at the wrist (× the cuff scale
for a scaled-down hand). The cuff is a bell (it flares in its last ~12 cm), asymmetric (the upper side hugs the
forearm, only the gravity side flares) and **view-aware**: when the forearm points at / away from the lens its flare
shrinks and it slides back along the forearm, so it never reads as a ring around the hand (`Cuff.update(..., view)`).
Cupped `whisper` / `pat` / `around` hands (and any open hand with `cup` ≳ 0.5) get `hand.flat` ≈ 0.9 automatically: a
flatter palm, fingers a little apart and longer, less cup (pass `hand.flat` to override).
**Nods**: a positive `head.pitch` pivots about the hood's chin rim, not the neck, so a bowed hood rides over the chest
(no chest showing through the lower face from low cameras); level / tipped-back heads are unchanged.
**Legs**: short fat round legs (r ≈ 0.29) with round feet; each sole has a soft glowing pad + three toe beans.

Rest measurements (root at the feet, facing +Z): hood tip ≈ 3.05 (anchor `hoodTop` 3.065), eyes 2.16, mouth 1.86, head centre 2.15 (z 0.10),
shoulder tops ±0.77 @ ~1.56, chest front z 0.87 @ 1.2, base radius 1.1 (≈ 2.2 m wide), hands hang at ~0.6.

## Pose API — `void.update(t, pose)` (pure function of t + pose)

**Set the camera (`applyShot`) BEFORE calling `update()`**: core eye catchlights and `gaze: 'camera'` read
`CTX.camera` during update. (The ENGINE.md scene template shows `update()` before `applyShot`; with that order the
Void's catchlights/gaze use the previous frame's camera, which breaks out-of-order rendering.)

| field | meaning |
|---|---|
| `pos`, `yaw` | feet position, facing (0 = +Z) |
| `body.lean` | forward bend (rad, + forward; the base stays planted) |
| `body.tilt` | side bend (rad, **+ = toward its LEFT / +X**) |
| `body.twist` | upper-body turn (rad, + = toward its left) |
| `body.crouch` 0..1 | squash down, widen, knees out |
| `body.sit` 0..1 | plops onto its backside, legs stick out in front (soles + pads to camera) |
| `body.kneel` 0..1 | lowers onto folded legs |
| `body.shrug` 0..1 | shoulders/capelet rise, hood sinks (combine with arm preset `shrug`) |
| `body.slump`, `hunch`, `recoil` (+ = flinch back), `bounce` (m), `swell` 0..1, `stretch` (vertical scale add), `pitch` (whole-body tip about the front-bottom, rad), `breathe` (amp mult), `breathRate` (Hz, default 0.21) |
| `walk {amount, phase, style}` | styles `waddle` (default, heavy), `walk`, `run`, `stomp`, `sneak`. phase in cycles. **Ground speed = 2·stride·cycles/s**, stride: waddle 0.38, walk 0.42, run 0.66, stomp 0.40, sneak 0.30 (waddle at 1.05 cyc/s ≈ 0.8 m/s). |
| `head {yaw, pitch, roll}` | relative to the neck (rad). yaw clamps at ±2.0 (over-the-shoulder ≈ ±1.9 with `body.twist` ∓0.35). **pitch + = nod down, − = tip back.** `track` 0..1 turns the hood toward `gaze`; `squash` (+ wider/shorter) |
| `gaze` | Vector3 / [x,y,z] / Character / `'camera'` / null — **eyes only** (the hood follows only with `head.track`). Peripheral side-eye: keep the head still, use `gaze` or `face.gazeYaw ≈ ±0.65`. |
| `armL` / `armR` | see **Arms** |
| `face` | flat Face params; build with `VX(name, overrides)` (Void presets) or core `X()`. `mTeeth*`, `mTongue` ignored; `mClench` → pressed wide lips. Void extras: `puff` 0..1, `mDroop` 0..1 (sad-smile corners), `mWavy` 0..1 (squiggle). `blush` = violet starry blush (also shows on the lids), `tearL/R` = starlight tears. |
| `speech` | `false` or `{open, wide, round, close}`; default = automatic lip-sync for speaker `VOID` |
| `blinkAt` | extra explicit blink times |
| `extra.puff` 0..1 | huff & puff: hood swells, cheek glows bulge (visible over the lids too), pucker mouth, body swells |
| `extra.laugh` 0..1 | maniacal-laugh body: "HA-HA" belly bounce (3.3 Hz), shake, head thrown back, mouth pumps. Pair with `face: VX('laugh')`, arms `belly`. |
| `extra.cough` | coughed-up stars & spiral galaxies, born only inside `[t0, t1]` (pure). On every "HA" peak (3.3 Hz) a few BIG readable puffs fly out & up clear of the hood, plus a light sprinkle. `{ t0, t1, puffs=3 (per HA), galaxy=0.4 (share of puffs that are galaxies, ≈0.15–0.25 m), size=1 (mult), spread=1 (mult), forward=1 (speed mult along mouthDir), speed=2.4, up=1.1 (m/s upward kick), rate=4 (sprinkle /s), haRate=3.3, life=2.2, seed }` |
| `extra.kick` −0.5..1.25 | donkey back-kick: negative = wind-up (knee comes up in front, front hem lifts), 1 = full extension: the body tips forward (~24°), the back hem opens like a curtain (smooth, monotonic lift: no crease/fin) and the short fat leg (≈0.66 m hip→sole) shoots out back-and-to-its-side from under it, sole pad facing the target; the foot swells on impact (1.0–1.15). `kickSide` `'R'` (default) / `'L'`; `kickTarget` world point (the leg aims at it inside a cone; a higher target tips the body more); `kickLevel` 0..1 how much the head counter-tilts to keep the calm face level (default 0.75; 1 = fully level). |
| `extra.cosmos` 0..1 | stars in face + cloak intensify, more motes, eyes/brows brighter (bonus scene) |
| `extra.motes` (mult), `stars` (fabric star mult), `rim` (rim mult — raise to 1.5–2 for silhouettes), `eyeGlow`, `browGlow` (mults), `mouthGlow` (+lip-line visibility), `hem` 0..1 (lift the whole hem to show the legs) |

### Arms — `armL` / `armR`
`{ preset, target, on, spot, reach, at, handScale, from, mix, pole, palm, fingers, hand, tip, pat, patRate, patPhase, offset }`

- `preset` (defined for the LEFT arm, mirrored): body-relative `rest`, `hips`, `belly` (hands on its belly),
  `crossed` (folded arms: shoulders roll forward, lower forearm on the belly, the other stacked over it, fists
  tucked toward the opposite elbows), `up`, `shrug` (palms up), `wave`, `open` (welcoming palms), `point`, `fist`,
  `hold`; head-relative (follow the hood) `whisper` (cupped hand by the mouth), `cover_mouth`, `chin`;
  **contact shapes** `pat`, `around`, `tip`, `reach` (use with `target` or `on`).
- **Contact presets are palm-anchored**: for `pat`, `around`, `reach` the target is where the **palm centre** goes
  (the wrist is backed off by the hand); for `tip` it is the **index fingertip**. Force with `at: 'palm' | 'tip' |
  'wrist'`.
- `on: character` (any rig with `shoulderL/R` + `head` anchors, e.g. Jesus) computes the contact frame for you:
  - `pat`: palm flat on top of the NEAR shoulder (or `spot: 'shoulderL'|'shoulderR'`), palm normal down into it,
    fingers over the front of the shoulder and away from the head; elbow out-down-back.
  - `around`: palm down on the FAR shoulder, fingers draped over its front, elbow pole back-and-up so the forearm
    comes down behind the neck.
  - `handScale` defaults to **0.72 with `on`** (1 otherwise) so the mitt fits a 1.75 m partner; the cuff shrinks too.
- `target` (world) + `reach` 0..1 blends position AND hand orientation from the preset's rest shape to the contact.
- `from: 'rest', mix: 0..1` blends between two presets (use for every transition).
- `pole`, `palm`, `fingers` are **world** directions (elbow hint, palm normal = the side the palm faces / into what
  it touches, finger direction) and override the preset / contact frame.
- `pat: 0..1` pats: the palm lifts off along its normal and comes back down (`patRate` Hz, default 2.2; `patPhase`
  start time).
- Arms stretch up to 20 % (rubber hose; 40 % for `crossed`) when a target is a bit out of reach.

### Helpers (exports)
- `VX(name | [[name, w], ...], over)` — Void expressions (`VOID_EXPR`): `neutral calm listen curious gentle happy
  laugh giggle whisper sideeye scowl annoyed huff sadSmile sad innocent surprised wonder proud peripheral determined
  smug tender awkward flinch hopeful`. Tuned to read with an OFF-AXIS gaze too: `gentle`/`sadSmile`/`tender` keep the
  lids open (no sly half-lids), raise the inner brows, add wet; `sadSmile` droops its corners (`mDroop`); `smug` is
  clearly lopsided (lid + brow + smirk); `awkward` = brows up, wide eyes, darting saccades, squiggle mouth.
- `eyeRoll(u, dir=1)` — face overrides for an eye-roll at progress u (merge over `VX('annoyed')`, ~0.9 s).
- `whisperPose(side=+1, depth=1, amount=1)` — body/head/arm fields for the whisper bend (side +1 bends toward its
  left). **Mouth height** (anchor `mouth`, yaw 0, measured with `void_probe`): depth 0 → 1.86 m · 0.6 → 1.77 ·
  0.8 → 1.74 · 1.0 → 1.70 · 1.1 → 1.61 · 1.2 → 1.52 · 1.3 → 1.42. Above 1 the knees fold, the body tips further and
  the hood nods down.
- `v.solveWhisper(t, pose, earWorld, side=1, {amount})` → `{ pos, depth, err, pose }`: finds the depth whose
  `whisper` point is at the ear height and the ground position that puts it on the ear (err within ±1 cm). E.g.
  `const W = v.solveWhisper(t, { yaw, face: VX('whisper') }, jesus.anchor('earR'), 1); v.update(t, W.pose)`.
  Costs ~10 updates (≈ 40–70 ms CPU): call it once per frame (or once per shot and reuse the depth).
- `v.solvePos(t, pose, anchorName, worldTarget)` — returns `pos` so that the anchor lands on the target in the
  ground plane (`.err` = remaining height error).
- `v.mouthDir()` — world unit vector out of the mouth.

## Anchors (`v.anchor(name)`, world, valid after update)
`head`, `eyes`, `mouth`, `mouthOut` (0.6 m out), `mouthDir` (**direction vector**), `whisper` (point 0.16 m in
front of the mouth — where a listener's ear should be), `earL`, `earR` (hood sides), `hoodTop`, `hood` (neck pivot),
`chest`, `back`, `backLow` (lower back, ~0.95 m), `shoulderL`, `shoulderR` (tops of the capelet shoulders), `sideL`,
`sideR` (flanks, ~0.95 m), `hip`, `handL`, `handR` (palm-surface centres), `footL`, `footR` (soles), `kickFoot`
(sole of the kicking foot — impact point).

## Recipes
- **Laugh + coughing stars**: `face: VX('laugh')`, `extra: { laugh: 1, cough: { t0: T('b')+0.6, t1: T('b.end')-0.5 } }`,
  arms `{ preset: 'belly', from: 'rest', mix }`. Bigger/more galaxies for a "say it, show it" beat:
  `cough: { ..., galaxy: 0.6, size: 1.3 }`. Finish with `giggle`, `tearL/R: 0.4`.
- **Whisper into Jesus's ear**: `const W = v.solveWhisper(t, { yaw, face: VX('whisper', { gazeYaw: -0.45 }) }, jesus.anchor('earR'), 1)`,
  then key the bend in with `whisperPose(1, W.depth, amount)` and `pos` lerped toward `W.pos`.
- **Side-eye at the user while whispering**: as above with `face: VX('whisper', { gazeYaw: ±0.6 })` or `gaze: user`.
- **Crossed arms + scowl**: `armL/armR: { preset: 'crossed', from: 'rest', mix }` (R a little later), `face: VX('scowl')`, `body.lean: -0.05`.
- **Eye roll → huff & puff → turn its back**: `VX('annoyed', eyeRoll(u))`, then `extra.puff` 0→1→0 twice with
  `face: VX('huff')` + `body.swell`, then key `yaw` by π.
- **Look over the shoulder**: `yaw: π (+...)`, `head.yaw: ∓1.9`, `body.twist: ∓0.35`, `face: VX('gentle')`.
- **Pat Jesus's shoulder (beat 14)**: `armL: { preset: 'pat', on: jesus, reach, pat: 1, patPhase: T(...) }`,
  `face: VX('sadSmile')`, `gaze: jesus.anchor('eyes')`.
- **Arm around Jesus**: `armL: { preset: 'around', on: jesus, reach }` (he stands at its front-left, ~1.2 m from its
  centre), `body.tilt: +0.06`, `face: VX('gentle')`.
- **Donkey kick**: key `extra.kick`: 0 → −0.5 (0.3 s wind-up) → 1.12 (0.15 s, `ease.out`) → 1.0 (hold 0.4 s) → 0;
  `kickTarget: magician.anchor('chest')`, `kickLevel: 1`; keep the face calm (`peripheral` → `calm` → `innocent`)
  and `gaze` on Fear. Best read from a 3/4 front camera on the kicking side (lab segment 73–78). Use
  `anchor('kickFoot')` for the impact / magician launch.
- **Fingertip on a latch**: `armL: { preset: 'tip', target: latch, fingers: [dir toward the latch] }` + a little
  `lean`/`crouch`.
- **Silhouette at dusk**: `extra: { rim: 1.6, eyeGlow: 1.15 }`; eyes/brows stay readable when backlit.

## Performance
Measured interleaved against the core `facetest` lab in the same browser, under heavy shared load (load average
16–24 on 4 cores, so wall-clock times were 1.5–3 s/frame and unusable). The robust number is **CPU-seconds per frame
summed over all Chromium processes** (median of 8, interleaved):

| frame | CPU-s/frame |
|---|---|
| core `facetest` | 1.25 |
| void lab, laugh + coughed stars (t = 50.5, full body) | 1.43 |
| void lab, idle full body (t = 31.5) | 1.44 |
| void lab, laugh close-up (t = 10.6) | 1.42 |
| void lab with the Void hidden (sky + ground + shadow map + post) | 1.02 |

So the Void itself costs ≈ 0.4 CPU-s (≈ ⅓ of a facetest frame) and the lab frame is ≈ 1.14× facetest. Scaled to
facetest's unloaded 0.48 s/frame that is **≈ 0.55 s/frame unloaded** for the lab (under the 0.6 s target, but not
"well under"). The previous version measured 1.63 CPU-s at the same frame (Void ≈ 0.63) — i.e. ≈ 1.8–2× facetest in
wall-clock as the review found; the claim of parity in the earlier doc was wrong.
`update()` ≈ 6–8 ms CPU at that load (laugh + cough or idle; ≈ 3–4 ms unloaded); `solveWhisper` ≈ 10 updates.

What changed for speed: velvet is MeshLambert (no GGX) + cheap emissive terms; only the body and hood cast
shadows; arms, hood and face draw first (`renderOrder` < 0) so early-z rejects the big body behind them; eye halos
and the hood glow are analytic terms in the face shader (no big additive sprites); each hand is one mesh with
analytic normals rewritten only when its pose changes; foot pads + toe beans are one mesh; the mouth decal re-uploads
only when its (collision-free) digest changes, ≤ 12 Hz while the mouth is open.

## Implementation notes (deviations from the generic core path, all inside void.js / void_parts.js)
- The **mouth** is painted by `_paintMouth` through the Face decal's `drawExtra` hook (core mouth invisible; its
  toothy path can't make a crescent "D"). Lip-sync is blended in void.js with the same rule as core Face. The core
  decal is fed CONSTANT mouth params (so it never redraws on its own); the Void forces exactly one redraw (by
  clearing the core `Face._lastKey`) whenever a string digest of its quantized mouth inputs + 12 Hz time changes —
  no weighted sums, no modulo, so two different mouth states can never share a canvas. A public "decal key" hook on
  core `Face` would make this cleaner.
- Eyelids / face field share one shader; the lid variant (`LID` define) projects onto the face ellipsoid and samples
  the decal texture (`face.decal.tex`). The eye-corner fade patches the Void's own eye material instances (adds
  `uSock`/`uCorner` uniforms) — core `Eye` is untouched.
- Rim/sheen/stars are the Void's own shader block (not `materials.being/enhance`) — same idea (HDR violet→teal
  fresnel rim for bloom) at a fraction of the SwiftShader cost.

## Known limitations
- Particles (motes, cough) live in the Void's root space: if it moves fast while coughing, in-flight particles move
  with it.
- The body is 2.2 m wide: a partner must stand front-diagonal for whispers/pats (use `solveWhisper` / `on`).
- `crossed` is tuned for front / 3/4; in a strict profile the far fist can show past the belly.
- Head yaw beyond ~±1.9 rad lets the hood rim cut into the capelet.
- Face field / hood lining are unlit by design (cosmic darkness ignores set lighting).
- Catchlights come from core `Eye` and follow `CTX.camera` at update time (see the camera-order note above).
- A contact shadow is built in (`v.shadow`); hide it if the set provides its own.
