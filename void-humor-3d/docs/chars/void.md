# THE VOID — `CHARS.VOID` (speaker `'VOID'`)

Files: `web/src/chars/void.js` (rig), `web/src/labs/void.js` (lab), this doc.
Lab: `node tools/render.js sheet --lab void --from 0 --to 4 --n 8 --cols 4` (turntable),
`--from 4.5 --to 29.5 --n 26 --cols 7` (expression sheet, 1 s each), `--from 30 --to 90 ...` (actions).
The lab segment list is exported as `segments` (`[start, end, name]`).

## Look

A huge (~3.07 m to the hood tip), plump, bell-shaped hooded cloak-being. Deep indigo velvet (MeshStandard +
key-lit violet sheen), faint stars drifting *inside* the fabric (two parallax star layers in the Void's own
space, low contrast, slow twinkle), faint nebula shimmer, an HDR violet→teal fresnel rim (bloom-friendly), and
sparse star motes lifting off. A shoulder **capelet** (open at the front, scalloped hem) marries the hood to the
cloak and gives the back view a clear "hooded cloak" read; the hood has a soft drooping peak and an arched,
overhanging brim. Inside the hood: unlit **cosmic darkness** (subtle nebula + tiny stars, vignetted to black at
the brim) holding:

- **Two big starlight eyes** (core `Eye`, glow mode): moon-white sclera, deep blue → teal iris, dark pupil; the
  lids use the same cosmic-darkness shader as the face field, so blinks / squints / side-eyes read as darkness
  sliding over the light. Soft halo sprites dim when the lids close.
- **Nebula-wisp brows**: additive glowing SweepTubes (violet inner → teal outer) + a wide faint halo tube.
- **Mouth**: painted by the Void itself (core mouth suppressed): a glowing crescent lip-line that opens into
  deeper cosmos (gradient, drifting nebula, stars, a tiny turning spiral galaxy in big opens). No teeth/tongue.
  Closed = lens-shaped crescent (smile U / frown arch); open = flat-ish upper lip + round bowl (laugh "D"),
  `mRound` → "O"; `mPout`/puff → small round pucker with pucker ticks. Starry violet blush; puffed-cheek glows.

Hands: big, gentle, 3 chunky fingers + thumb (core `Hand`, merged into one mesh per hand for speed) out of wide
sleeves. Short fat legs + big round feet (soles have a faint glowing pad) peek under the hem when walking,
sitting, kicking.

Rest measurements (root at the feet, facing +Z): hood tip 3.07, eyes 2.16, mouth 1.85, head centre 2.15
(z 0.10), shoulder tops ±0.77 @1.56, chest front z 0.87 @1.2, base radius 1.1 (≈2.2 m wide), hand at side ~0.6.

## Pose API — `void.update(t, pose)` (pure function of t + pose)

| field | meaning |
|---|---|
| `pos`, `yaw` | feet position, facing (0 = +Z) |
| `body.lean` | forward bend (rad, + forward; the base stays planted) |
| `body.tilt` | side bend (rad, **+ = toward its LEFT / +X**) |
| `body.twist` | upper-body turn (rad, + = toward its left) |
| `body.crouch` 0..1 | squash down, widen, knees out |
| `body.sit` 0..1 | plops onto its backside, legs stick out in front (toes up) |
| `body.kneel` 0..1 | lowers onto folded legs |
| `body.shrug` 0..1 | shoulders/capelet rise, hood sinks (combine with arm preset `shrug`) |
| `body.slump`, `hunch`, `recoil` (+ = flinch back), `bounce` (m), `swell` 0..1, `stretch` (vertical scale add), `pitch` (whole-body tip about the front-bottom, rad), `breathe` (amp mult), `breathRate` (Hz, default 0.21) |
| `walk {amount, phase, style}` | styles `waddle` (default, heavy), `walk`, `run`, `stomp`, `sneak`. phase in cycles. **Ground speed = 2·stride·cycles/s**, stride: waddle 0.38, walk 0.42, run 0.66, stomp 0.40, sneak 0.30 (e.g. waddle at 1.05 cyc/s ≈ 0.8 m/s). |
| `head {yaw, pitch, roll}` | relative to the neck (rad). yaw clamps at ±2.0 (over-the-shoulder ≈ ±1.9 with `body.twist` ∓0.35). **pitch + = nod down, − = tip back.** `track` 0..1 turns the hood toward `gaze`; `squash` (+ wider/shorter) |
| `gaze` | Vector3 / [x,y,z] / Character / `'camera'` / null — **eyes only** (the hood does not follow unless `head.track`). Peripheral side-eye: keep head still, use `gaze` or `face.gazeYaw ≈ ±0.65`. |
| `armL` / `armR` | `{ preset, target, reach, from, mix, pole, palm, fingers, hand, tip, pat, patRate, patPhase, offset }` — see below |
| `face` | flat Face params; build with `VX(name, overrides)` (Void presets) or core `X()`. `mTeeth*`, `mTongue` ignored; `mClench` → pressed wide lips. `blush` = violet starry blush, `tearL/R` = starlight tears. `puff` may ride here. |
| `speech` | `false` or `{open, wide, round, close}`; default = automatic lip-sync for speaker `VOID` (laughs/giggles/whispers drive the painted mouth) |
| `blinkAt` | extra explicit blink times |
| `extra.puff` 0..1 | huff & puff: hood swells, cheeks glow/bulge, mouth becomes a tight pucker, body swells |
| `extra.laugh` 0..1 | automatic maniacal-laugh body: "HA-HA" belly bounce (3.3 Hz), shake, head thrown back, mouth pumps. Pair with `face: VX('laugh')`, arms `belly`. |
| `extra.cough` | `{ t0, t1, rate=10, speed=2.3, life=2, seed }` coughed-up stars, nebula puffs & little spiral galaxies from the mouth along `mouthDir` (pure: particles are born only inside [t0, t1]) |
| `extra.kick` −0.5..1.25 | donkey back-kick: negative = chamber/wind-up (knee lifts forward), 1 = full extension (fat leg shoots out from under the lifted back hem, body tips forward ~20°, foot swells on impact), >1 overshoot. `kickSide` `'R'` (default) / `'L'`; `kickTarget` world point (default ≈ 1.3 m high, 1.5 m behind); `kickLevel` 0..1 how much the head counter-tilts to keep its calm face level (default 0.75). |
| `extra.cosmos` 0..1 | stars in face + cloak intensify, more motes, eyes/brows brighter (bonus scene) |
| `extra.motes` (mult, default 1), `stars` (fabric star mult), `rim` (rim mult — raise for silhouettes), `eyeGlow`, `browGlow` (mults), `mouthGlow` (+lip-line visibility), `hem` 0..1 (lift the whole hem to show the legs) |

### Arm presets (`ARM` export)
Body-relative: `rest`, `hips`, `belly` (hands on its belly — laughing/sitting), `crossed` (forearms crossed over
the upper belly, fists tucked), `up`, `shrug` (palms up, out), `wave`, `open` (welcoming palms), `point`, `fist`,
`hold`. Head-relative (follow the hood): `whisper` (hand cupped beside the mouth), `cover_mouth`, `chin`.
Target-driven hand shapes (use with `target`): `pat` (flat palm down), `around` (arm around someone: target their
far shoulder/back), `tip` (index fingertip ON the target — latches, buttons), `reach`.

- `target` (world) + `reach` 0..1 blends from the preset position to the target.
- `from: 'rest', mix: 0..1` blends between two presets (use for every transition).
- `pole`, `palm`, `fingers` are **world** directions (elbow hint, palm normal, finger direction).
- `tip: true` treats `target` as the index fingertip (wrist is backed off along `fingers`).
- `pat: 0..1` adds a patting bounce (`patRate` Hz, default 2.2; `patPhase` start time).
- Arms stretch up to 20 % (rubber hose) when a target is a bit out of reach.

### Helpers (exports)
- `VX(name | [[name, w], ...], over)` — Void expressions: `neutral calm listen curious gentle happy laugh
  giggle whisper sideeye scowl annoyed huff sadSmile sad innocent surprised wonder proud peripheral determined
  smug tender awkward flinch hopeful` (`VOID_EXPR`).
- `eyeRoll(u, dir=1)` — face overrides for an eye-roll at progress u (gaze sweeps up and over, lids follow;
  dir +1 starts at its left and ends at its right, −1 mirrors);
  merge over `VX('annoyed')`, ~0.9 s; follow with `huff`.
- `whisperPose(side=+1, depth=1, amount=1)` — body/head/arm fields for the whisper bend. side +1 bends toward its
  left. Mouth height ≈ 1.90 (depth 0), 1.72 (0.6), 1.65 (0.8), 1.58 (1.0), 1.50 (1.2).
- `v.solvePos(t, pose, anchorName, worldTarget)` — returns `pos` so that the anchor lands on the target in the
  ground plane (`.err` = remaining height error). E.g. put the Void's mouth at Jesus's ear:
  `const W = {yaw, ...whisperPose(1, 0.9), face: VX('whisper')}; pose.pos = v.solvePos(t, W, 'whisper', jesus.anchor('earL'))`.
  update() costs ~2–3 ms, so calling it 2–3× per frame is fine.
- `v.mouthDir()` — world unit vector out of the mouth.

## Anchors (`v.anchor(name)`, world, valid after update)
`head`, `eyes`, `mouth`, `mouthOut` (0.6 m out), `mouthDir` (**direction vector**), `whisper` (point 0.16 m in
front of the mouth — where a listener's ear should be), `earL`, `earR` (hood sides), `hoodTop`, `hood` (neck
pivot), `chest`, `back`, `backLow` (lower back, ~0.95 m: where a 1.75 m human's arm goes around it), `shoulderL`,
`shoulderR` (tops of the capelet shoulders: pats / hand on shoulder), `sideL`, `sideR` (flanks, ~0.95 m), `hip`,
`handL`, `handR` (palm centres), `footL`, `footR` (soles), `kickFoot` (sole of the kicking foot — impact point).

## Recipes
- **Laugh + coughing stars**: `face: VX('laugh')`, `extra: { laugh: 1, cough: { t0: T('b')+0.6, t1: T('b.end')-0.5 } }`,
  `armL/armR: { preset: 'belly', from: 'rest', mix }`. Finish with `giggle`, `tearL/R: 0.4` for wheezy tears.
- **Side-eye at the user while whispering**: `whisperPose` + `face: VX('whisper', { gazeYaw: ±0.6 })` or `gaze: user`.
- **Crossed arms + scowl**: arms `crossed` (R slightly later than L), `face: VX('scowl')`, `body.lean: -0.05`.
- **Eye roll → huff & puff → turn its back**: `VX('annoyed', eyeRoll(u))`, then `extra.puff` 0→1→0 twice with
  `face: VX('huff')` + `body.swell`, then key `yaw` by π.
- **Look over the shoulder**: `yaw: π (+...)`, `head.yaw: ∓1.9`, `body.twist: ∓0.35`, `face: VX('gentle')`.
- **Pat a shoulder**: `armL: { preset: 'pat', target: jesus.anchor('shoulderR') (+0.06 up), reach, pat: 1 }`.
- **Arm around someone**: `armL: { preset: 'around', target: their far shoulder }`, `body.tilt` +0.06 toward them.
- **Donkey kick**: key `extra.kick`: 0 → −0.5 (0.3 s chamber) → 1.1 (0.15 s, `ease.out`) → 1.0 (hold 0.4 s) → 0;
  keep `face` calm (`peripheral` → `determined` → `innocent`), `gaze` on Fear: the head counter-tilts so the face
  stays level. Use `anchor('kickFoot')` for the impact / magician launch.
- **Fingertip on a latch**: `armL: { preset: 'tip', target: latch, tip: true, fingers: [dir toward latch] }` + a
  little `lean`/`crouch`.
- **Silhouette at dusk**: raise `extra.rim` to 1.5–2 and `eyeGlow` 1.2; eyes/brows stay readable.

## Performance
update() ≈ 2–3 ms. See the report in the final message / the numbers below for render cost. Geometry: body
64×62 + capelet 64×22 (rewritten in place each frame), hood 64×50 static, 2 SweepTube arms + 2 legs, 2 merged
hands (1 draw call each), 1 particle mesh. No per-frame allocations of big geometry, no shader recompiles.

## Known limitations
- Particles (motes, cough) live in the Void's root space: if the Void moves fast while coughing, in-flight
  particles move with it; the cough origin follows the current mouth (slight wobble on hard laugh shakes).
- The body is 2.2 m wide: a human standing beside it can't be whispered to — place them front-diagonal
  (use `solvePos`). Arms cannot reach behind its own body.
- The kick leg is rubber-hose (stretches to ~1.2 m) — intended slapstick.
- Head yaw beyond ~±1.9 rad lets the hood rim cut into the capelet.
- Face field / hood lining are unlit by design (cosmic darkness ignores set lighting).
- A contact shadow is built in (`v.shadow`); hide it if the set provides its own.
