# THE DEPRESSION MAGICIAN — `CHARS.MAGICIAN` (speaker `MAGICIAN`)

Files: `web/src/chars/magician.js` (rig), `web/src/labs/magician.js` (lab), this doc.
Exports: `create()`, `Magician`, `MX(name, overrides)` (face presets), `MEXPR`, `ARM` (arm presets), `GAIT`.

## Look
A creepy-funny stage magician made of desaturated grey-blue gloom. 2.1 m to the top of the hat but stooped:
hunched back, sloped sad shoulders, long thin neck jutting forward, head carried ~0.33 m ahead of the hips.
Gaunt pale-grey head (scaled 1.2× so faces read at phone size): sculpted sharp cheekbones over sunken cheeks that
carry round to the silhouette, temple hollows, deep eye sockets under a brow ridge, a lean jaw and a long pointed chin.
Heavy-lidded sunken eyes (dark socket rings, tired eye-bag creases), pale yellow-grey irises, small pupils; thin
angular villain brows; a long nose that projects forward with a small hook; too-wide thin grin (lip-synced painted
mouth, grey-yellow teeth, violet-grey interior); a straight, near-horizontal PENCIL MOUSTACHE just above the upper lip,
split around the nose (tips flick at most ~0.08·HW0). Dented, leaning stovepipe top hat with a band and a dead grey MOTH
pinned to it (bald dome + 3 comb-over strands underneath that spring up when it flies off).
Swallow-tail coat cut away at the waist, tails tattered (jagged hem) and dynamic, high flared collar, satin lapels,
shirt front, a sad WILTED bow tie, a dark satin waistcoat band over the waist (trousers read as trousers, no seam).
Grey-white gloves (own skinned glove, see below) with long thin tapered fingers, flared gauntlet cuffs + shirt cuffs.
Spindly legs in vertical-pinstripe trousers (seam-free shader stripes), glossy pointy curled shoes.
Gloom look: cold fresnel rim on every silhouette, cool wrap light, a cheap slow low-contrast fizz on coat + skin,
sparse grey dust motes falling off it.
Props: small wavy (kris-like) dagger in the RIGHT fist (wide wavy blade, dark central fuller, bright edges; it
auto-rolls about its long axis so the wavy FACE turns to the camera), plum-grey velvet pouch of numbing dust
pinched by the LEFT hand (thumb + index/middle tips).

## Pose API (`mag.update(t, pose)`; all fields optional; a pure function of t)
Standard fields (see docs/ENGINE.md): `pos`, `yaw`, `gaze` (Vector3 | [x,y,z] | Character | 'camera' | null),
`speech` (false | sample; default = automatic lip-sync from `data/lipsync.json`), `blinkAt`, `shadow:false`, `glow` (rim mult).

- `face`: preset name | `['gloat', 0.6]` | `[['gloat',0.5],['ow',0.5]]` | `{ expr: 'gloat', mOpen: 0.3 }` | flat params (layered on 'rest').
  Default `'sly'`. Magician presets (`MEXPR`), all core `EXPR` names also work:
  `sly` (default resting smirk) · `rest` · `lurk` (peeking grin, brows up) · `scheme` (narrowed, brows down, wide grin) ·
  `gloat` (the too-wide toothy grin) · `hungry` (ogling, wet eyes, mouth ajar) · `relish` (eyes shut, savouring) ·
  `whisper` (gloating whisper, one brow up — use with lip-sync) · `snicker` (hee-hee squint) · `innocent` (fake "who, me?") ·
  `curious` · `uhoh` (sees the leg: wide eyes, clenched grimace) · `popped` (kicked: eyes popped, screaming mouth) ·
  `ow` (squeezed wince, trembling clench) · `dazed` (crooked, slack — pair with `extra.dizzy`) · `sulk` · `annoyed` · `startled`.
- `body`: `lean`, `tilt`, `twist`, `hunch` (extra stoop, can be negative), `slump`, `shrug`, `recoil`, `bounce`,
  `crouch` 0..1 (deep creepy spider-crouch on its toes, knees splayed — LURKING), `peek` −1..1 (lean round something:
  pelvis shift + chest tilt + sideways neck slide + head roll ≈ 0.4 m of lateral reach at the head; +1 = toward its
  LEFT/+X, −1 = toward its right/−X), `tiptoe`, `kneel` (right knee down), `sit` (on the floor, knees up),
  `giggle`/`snicker` 0..1 (shoulder-bounce snicker), `breathe`, `breathRate`, `sway`.
- `walk`: `{ amount, phase (cycles), style }`, styles: `walk` (0.76 m/s), `sneak` (cartoon tiptoe sneak: crouched,
  high knee lifts, on the toes; arms default to `creep`; 0.40 m/s), `tiptoe` (upright, 0.50 m/s), `run` (2.9 m/s, the
  stoop straightens a little), `stomp` (heavy, high lifts; 0.68 m/s), `waddle` (short side-to-side steps; 0.45 m/s),
  `limp` (left leg stiff/dragging, hip dips; 0.31 m/s). Unknown styles fall back to `walk`.
  Move `pos` at `mag.walkSpeed(style) * mag.walkRate(style)` m/s and use `phase = time * mag.walkRate(style)`.
- `head`: `{ yaw, pitch, roll, follow 0..1 (turn the head toward look/gaze), look, compensate (default 1), talk }`.
- `armL` / `armR`: `{ preset, target (world), pole, palm, fingers (world dirs), offset, reach 0..1 (blend from rest),
  gap (edge only, default 0.03), hand: { curl, point, spread, thumb, cup, splay, grip, pinch, tap } }`.
  `preset` may be a name or `[[name, w], ...]` (blends). Unknown names fall back to `rest`.
  Presets (written for the left arm, mirrored): `rest` `hang` `hips` `behind` `crossed` `steeple` (fingertips
  together, drumming) `rub` (gleeful hand-rub) `creep` (sneaking claws, wiggling) `claw` (raised claw, wiggling)
  `edge` (hand on a surface, fingers tapping — give `target` = a point ON the big thing's surface and `palm` = minus its
  outward normal; the wrist is backed off along the palm normal by `gap` so the fingertips tap ON the surface)
  `dagger_ready` (fist beside the face, blade up) `dagger_low` (low, blade forward-up) `dagger_stab` (thrust, blade
  forward) `pouch` (pouch held up) `pour` (tip the pouch forward — pair with `extra.dust`) `present` (ta-da) `shrug`
  `up` `wave` `point` `pocket` (hand tucked into the trouser pocket) `clutch_chest` (after the kick) `clutch_back`
  (limping) `cover_mouth` (snicker) `shush` `whisper` (cupped hand by the mouth) `chin` (stroking the chin).
  While the dagger / pouch are shown, the right hand is forced into the dagger fist (`grip` 1: fingertips closed on
  the palm round the handle, thumb wrapped over the index) and the left into the pouch pinch (`pinch` 1).
- Hands: `GloveHand` (in the rig file) replaces core `Hand` for this character: one skinned mesh per hand (palm,
  4 tapered fingers with fat roots/webbing, opposable thumb with a thenar pad, flared gauntlet), correct chirality
  (thumb on the index side), same `pose()` params as core `Hand` plus `grip` (dagger fist) and `pinch` (thumb meets
  index/middle tips). `hand.grip` (Object3D) is the dagger-handle frame, `hand.tipWorld(i | 'thumb')` gives fingertips.
- `extra` (magician-specific):
  - `hatOff` 0..1 — blends the hat from the head to free (default = max(kicked, crashed)). `hatPos` [x,y,z] world and
    `hatRot` [x,y,z] world Euler override the free hat (drive these along an arc for the hat flying off / landing).
    Without `hatPos` it pops up and back from the head (or lies on the floor beside it when crashed). `hat:false` hides it.
  - `lick` 0..1 — one lick: the long, thin grey-violet tongue comes out over the upper lip at the right corner, its
    tip sweeps along the UPPER LIP (riding over the moustache, the body arching proud of the face in front of the nose
    base) to the left corner and curls up there, then goes back in; a clear whitish drool drop hangs from the left
    lip corner on a thin strand near the end and thins away. Keyframe 0→1 over ~1.2 s per lick; the mouth opens
    automatically. The best "read" is lick ≈ 0.6–0.85 (tip at the far corner). (`face.mTongue` = painted tongue inside the mouth.)
  - `tongueOut` 0..1 — tongue lolling out of the left corner and hanging along GRAVITY (works in any orientation:
    over the chin when upright, toward the floor past the nose when upside-down), kept off the skull.
    Default = `crashed * dizzy * 0.85`.
  - `dust` 0..1 — opens the pouch, tips it to pour, and streams grey-silver glitter + a faint grey haze from its mouth.
  - `kicked` 0..1 — slapstick flight: whole body leans back around a pivot ~1.05 m above `pos`, chest arched back,
    arms & legs spread-eagle and windmilling/bicycling, coat tails streaming, eyes popped (eyeballs scale up),
    screaming mouth, hat off. The SCENE moves `pos` along the trajectory (pos.y > 0 in the air; the contact shadow
    stays on y = 0 and fades with height). `flip` (rad) tumbles the body about its pivot; `flail` (default 1) scales
    the limb windmilling; `vel` [world m/s] streams the coat tails against the motion.
  - `crashed` 0..1 — sprawled upside-down headstand slump: head on the floor (head top ~0.36 m up, room for a bucket),
    back toward −Z (put the wall / bucket pile behind it), face toward +Z (camera), legs up in a splayed V, arms
    flopped on the floor, an occasional leg twitch. Blending kicked → crashed tumbles it into place; crashed → 0
    flips it back upright (cut or cover it if you want).
  - `dizzy` 0..1 — spinning spiral irises (both eyes, opposite directions), lolling head, gaze ignored;
    `stars` 0..1 (default = dizzy) — five little stars circling above the head (round the head when upside-down).
  - `eyePop` 0..1 — extra eyeball pop for any expression. `tap` 0..1 — finger drumming on both hands.
  - `daggerFace` 0..1 (default 1) — how much the blade rolls to face the camera; `daggerRoll` (rad) sets a fixed roll.
  - `dagger` / `pouch`: `false` (or 0) hides the prop (and frees the hand). `motes` (default 1) dust-mote rate mult.
    `limp` 0..1 adds the limp to any gait.

## Anchors (`mag.anchor(name)`, world space, valid after `update`)
`head`, `headTop` (bucket goes here), `eyes`, `mouth`, `mouthOut`, `earL`, `earR`, `noseTip`, `chest` (kick target,
front of the chest), `back`, `neck`, `shoulderL`, `shoulderR`, `handL`, `handR`, `hip`, `belly`, `dagger` (blade tip),
`pouch` (pouch mouth — emit your own dust here if you need world-space trails), `hat` (hat centre), `footL/R`,
`kneeL/R`, `elbowL/R`. Directions (unit vectors, not points): `headUp` (head-up axis: orient a bucket with its
opening along −headUp), `mouthDir`.
Rest pose (pos 0, yaw 0): head (0, 1.68, 0.34), headTop y 1.85, hat top y 2.15, eyes (0, 1.70, 0.47),
mouth (0, 1.60, 0.46), chest (0, 1.35, 0.19), hands y 0.84. Crashed: head (0.13, 0.53, 0.36), headTop y 0.36.
The Void's default backward kick target (y 1.3) lines up with `chest`.

## Tips
- Lurking (lab 37–42 s): stand him BEHIND the Void's body (not beside it), on the side he peeks to, close enough
  that the hand reaches the silhouette edge: `body: { crouch: 0.5, peek: ±1 }`, `face: 'lurk'`,
  `head: { follow: 0.6 }`, `gaze: fear`, the free hand `{ preset: 'edge', target: <surface point just behind the
  silhouette>, palm: <−surface normal>, fingers: <round the edge toward camera> }`, the dagger hand `'dagger_ready'`,
  `extra: { tap: 1, pouch: false }`. Only head, hat, tapping fingers and the blade should clear the edge.
- Licking its lips: `face: 'hungry'` (or `'relish'` with eyes shut), `speech: false`, `extra.lick` 0→1 over ~1.2 s,
  then `'gloat'`. Camera at eye level or slightly below (pitch ≈ −4°), 3/4 front, ~1.4 m.
- Gloating whisper: `face: 'whisper'` + lip-sync (`face.talk` ~0.6 for small mouth moves), `body.hunch: 0.4`,
  `armR: 'dagger_ready'` or `'whisper'`, head yaw/roll toward the listener.
- Kick: hold `face: 'uhoh'` for ~0.3 s before contact; at contact ramp `kicked` 0→1 in ~0.06 s, move `pos` on an arc
  (e.g. y = 3.6τ − 3.9τ², z = −1.6τ), `flip` −1.3τ, `hatOff` 0→1 in 0.25 s with its own higher arc in `hatPos`/`hatRot`.
  Near landing ramp `crashed` 0→1 over ~0.2 s, then `dizzy` 0→1, swap `face` to `'dazed'`.
- Limping off: `walk.style: 'limp'`, `armL: 'clutch_back'` (or `'clutch_chest'`), `face: 'sulk'`, `head.pitch: 0.12`.
  Fade `dizzy` out first. Its "...ow." line: `face: 'ow'`.
- Frame faces with the `head` anchor (the head hangs well ahead of `pos`); open-mouth beats read best at eye level.

## Lab (`?lab=magician`, 90.3 s)
0–4 turntable · 4–22 expression sheet (18 × 1 s) · 22–76.8 actions (idle steeple, sneak side/3/4, walk, run, LURK,
lick close-up, gloating whisper + dagger, pouch pour, dagger stab, kick → flight → crash, mid-air hold, crash + bucket,
get up + limp, sit/kneel, ta-da) · 76.8–90.3 arm-preset sheet (27 presets × 0.5 s, both arms, props where relevant).
Review aid: setting `globalThis.__MAGCAM = { anchor: 'handR', dist, yaw, pitch, fov }` (or `look: [x,y,z]`) in the
page overrides the shot for detail renders; never set in normal renders.

## Perf / notes
- ~40k triangles, ~41–54 draw calls for the character in the main pass (was ~100): static details merged per
  material (shirt/lapels/buttons/bow, hat crown+brim, both ears, pouch ties), one skinned mesh per glove.
  `update()` ≈ 1.3–2.7 ms CPU. MeshStandard materials (physical only on the velvet pouch + wet tongue); the fizz is a
  3-sine shimmer (a few ALU ops/pixel) injected after core `enhance()`'s emissive block instead of core's 24-hash fbm.
  Face decal: Lambert, 640×512 canvas; mouth inputs are quantised to 1/100 so near-static holds don't redraw it.
- Bench: the 4-core box was at load average 16–33 (other agents rendering) during this pass, so absolute s/frame
  numbers are inflated 3–6× and noisy. `bench --t 1`: magician 1.84 s vs `--lab jesus --t 1` 2.79 s back to back.
  In-page interleaved A/B (magician visible vs hidden, load ≈ 16): full body 1.71 vs 1.36 s, close-up 1.64 vs 1.02 s,
  flight 1.90 vs 1.58 s. Re-bench on an idle machine (expected well under 0.6 s for the lab with only this asset).
- PURITY: three's `Curve` caches arc lengths until `curve.needsUpdate` is set and core `SweepTube.update()` doesn't set
  it, so every tube update in this rig goes through `sweep()` (invalidates first) and the Face brow tubes are
  invalidated before `face.update()`. Verified: md5-identical frames for 18.5 / 43.2 / 43.5 / 46.5 / 60 / 62.3 rendered
  in different orders and in fresh pages. The matching core fix (`this.curve.needsUpdate = true` after
  `this.curve.points = pts` in `core/limbs.js` `SweepTube.update`) has since landed in core; `sweep()` stays as a
  harmless belt-and-braces.
- Particles (motes, numbing dust, dizzy stars) live in the rig's root space: a long dust TRAIL while walking will move
  with the character — for world-space trails emit from the `pouch` anchor with your own `Particles`.
- `crashed` is a fixed composition (back toward −Z); rotate with `yaw` to fit the set. `crashed` 1→0 rolls upright sideways.
- The tongue is kept off the face by path design (lick) / a radial push-out (loll), not true collision.
