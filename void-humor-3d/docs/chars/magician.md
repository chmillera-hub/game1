# THE DEPRESSION MAGICIAN — `CHARS.MAGICIAN` (speaker `MAGICIAN`)

Files: `web/src/chars/magician.js` (rig), `web/src/labs/magician.js` (lab), this doc.
Exports: `create()`, `Magician`, `MX(name, overrides)` (face presets), `MEXPR`, `ARM` (arm presets), `GAIT`.

## Look
A creepy-funny stage magician made of desaturated grey-blue gloom. 2.1 m to the top of the hat but stooped:
hunched back, sloped sad shoulders, long thin neck jutting forward, head carried ~0.33 m ahead of the hips.
Gaunt pale-grey egg-shaped head (scaled 1.2× so faces read at phone size) with a pointed chin, cheek hollows,
painted sunken eye sockets; heavy-lidded eyes with pale yellow-grey irises and small pupils; thin high-arched
pencil brows; long pointed nose; too-wide thin grin (lip-synced painted mouth, grey-yellow teeth, violet-grey
interior); tapered pencil moustache with flicked tips. Dented, leaning stovepipe top hat with a band and a
plain grey playing card tucked in (bald dome + 3 comb-over strands underneath that spring up when it flies off).
Swallow-tail coat cut away at the waist, tails tattered (jagged hem) and dynamic, high flared collar, satin
lapels, shirt front, puffed grey cravat with a pin. Grey-white gloves with long thin fingers, flared glove
cuffs + shirt cuffs. Spindly legs in vertical-pinstripe trousers (seam-free shader stripes), pointy curled shoes.
Faint cold rim glow + cool wrap light on everything, sparse grey dust motes falling off it (no per-pixel shimmer noise: too costly on SwiftShader for how little it showed).
Props: small wavy (kris-like) dagger in the RIGHT fist, plum-grey velvet pouch of numbing dust hanging from the LEFT hand.

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
  `crouch` 0..1 (deep creepy spider-crouch on its toes, knees splayed — LURKING), `peek` −1..1 (lean the upper body +
  head sideways to peek around something; −1 = toward its right/−X), `tiptoe`, `kneel` (right knee down), `sit`
  (on the floor, knees up), `giggle`/`snicker` 0..1 (shoulder-bounce snicker), `breathe`, `breathRate`, `sway`.
- `walk`: `{ amount, phase (cycles), style }`, styles: `walk` (0.76 m/s), `sneak` (cartoon tiptoe sneak: crouched,
  high knee lifts, on the toes; arms default to `creep`; 0.40 m/s), `tiptoe` (upright, 0.50 m/s), `run` (2.9 m/s),
  `limp` (left leg stiff/dragging, hip dips; 0.31 m/s). Move `pos` at `mag.walkSpeed(style) * mag.walkRate(style)`
  m/s and use `phase = time * mag.walkRate(style)`.
- `head`: `{ yaw, pitch, roll, follow 0..1 (turn the head toward look/gaze), look, compensate (default 1), talk }`.
- `armL` / `armR`: `{ preset, target (world), pole, palm, fingers (world dirs), offset, reach 0..1 (blend from rest),
  hand: { curl, point, spread, thumb, cup, splay, grip, tap } }`. `preset` may be a name or `[[name, w], ...]` (blends).
  Presets (written for the left arm, mirrored): `rest` `hang` `hips` `behind` `crossed` `steeple` (fingertips
  together, drumming) `rub` (gleeful hand-rub) `creep` (sneaking claws, wiggling) `claw` (raised claw, wiggling)
  `edge` (hand on a surface, fingers tapping — give `target` on the big thing's edge) `dagger_ready` (fist beside the
  face, blade up) `dagger_low` `dagger_stab` `pouch` (pouch held up) `pour` (tip the pouch forward — pair with
  `extra.dust`) `present` (ta-da) `shrug` `up` `wave` `point` `clutch_chest` (after the kick) `clutch_back` (limping)
  `cover_mouth` (snicker) `shush` `whisper` (cupped hand by the mouth) `chin` (stroking the chin).
  While the dagger / pouch are shown, the right hand is forced into a fist and the left into a pinch.
- `extra` (magician-specific):
  - `hatOff` 0..1 — blends the hat from the head to free (default = max(kicked, crashed)). `hatPos` [x,y,z] world and
    `hatRot` [x,y,z] world Euler override the free hat (drive these along an arc for the hat flying off / landing).
    Without `hatPos` it pops up and back from the head (or lies on the floor beside it when crashed). `hat:false` hides it.
  - `lick` 0..1 — one lick: the long grey-violet tongue comes out at the right corner (0.1), slides across the upper lip
    over the moustache with a wiggle to the left corner and flicks up (0.9), back in (1.0); a little drool drop falls
    near the end. Keyframe 0→1 over ~1.2 s per lick; the mouth opens automatically. (`face.mTongue` = painted tongue inside the mouth.)
  - `tongueOut` 0..1 — tongue lolling out of the corner (gravity-aware: flops toward the floor when upside-down).
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
  - `dagger` / `pouch`: `false` (or 0) hides the prop (and frees the hand). `motes` (default 1) dust-mote rate mult.
    `limp` 0..1 adds the limp to any gait.

## Anchors (`mag.anchor(name)`, world space, valid after `update`)
`head`, `headTop` (bucket goes here), `eyes`, `mouth`, `mouthOut`, `earL`, `earR`, `noseTip`, `chest` (kick target,
front of the chest), `back`, `neck`, `shoulderL`, `shoulderR`, `handL`, `handR`, `hip`, `belly`, `dagger` (blade tip),
`pouch` (pouch mouth — emit your own dust here if you need world-space trails), `hat` (hat centre), `footL/R`,
`kneeL/R`, `elbowL/R`. Directions: `headUp` (unit vector, head-up axis: orient a bucket with its opening along
−headUp), `mouthDir`.
Rest pose (pos 0, yaw 0): head (0, 1.68, 0.34), headTop y 1.85, hat top y 2.15, eyes (0, 1.70, 0.47),
mouth (0, 1.60, 0.46), chest (0, 1.35, 0.18), hands y 0.84. Crashed: head (0.13, 0.53, 0.36), headTop y 0.36.
The Void's default backward kick target (y 1.3) lines up with `chest`.

## Tips
- Lurking: `body: { crouch: 0.55–0.75, peek: -0.85 }`, `face: 'lurk'`, `head: { follow: 0.5 }`, `gaze: fear`,
  `armL: { preset: 'edge', target: <point on the Void's silhouette edge> }`, `armR: { preset: 'claw' }`, `extra: { tap: 1 }`.
  Frame it so the Void's body covers half of the magician (see the lab segment).
- Licking its lips: `face: 'hungry'` (or `'relish'` with eyes shut), `speech: false`, `extra.lick` 0→1 over ~1.2 s,
  then `'gloat'`. Camera ~1.4 m, 3/4 front, so the tongue silhouettes past the cheek.
- Gloating whisper: `face: 'whisper'` + lip-sync (`face.talk` ~0.6 for small mouth moves), `body.hunch: 0.4`,
  `armR: 'dagger_ready'` or `'whisper'`, head yaw/roll toward the listener.
- Kick: hold `face: 'uhoh'` for ~0.3 s before contact; at contact ramp `kicked` 0→1 in ~0.06 s, move `pos` on an arc
  (e.g. y = 3.6τ − 3.9τ², z = −1.6τ), `flip` −1.3τ, `hatOff` 0→1 in 0.25 s with its own higher arc in `hatPos`/`hatRot`.
  Near landing ramp `crashed` 0→1 over ~0.2 s, then `dizzy` 0→1, swap `face` to `'dazed'`.
- Limping off: `walk.style: 'limp'`, `armL: 'clutch_back'` (or `'clutch_chest'`), `face: 'sulk'`, `head.pitch: 0.12`.
  Fade `dizzy` out first. Its "...ow." line: `face: 'ow'`.
- Frame faces with the `head` anchor (the head hangs well ahead of `pos`).

## Perf / notes
- ~47k triangles, ~100 draw calls; `update()` ≈ 3–4 ms CPU. MeshStandard materials by default (physical only on the
  velvet pouch, blade, tongue), no per-pixel fizz noise, only the big parts cast shadows; the face decal is Lambert
  (640×512 canvas, redrawn only when mouth params change).
- Bench (720×1280, shared 4-core box with other agents rendering, load avg 4–7): `bench --lab magician --t 1`
  (full body) 0.61–0.77 s/frame vs `--lab jesus --t 1` 0.63–0.74 s/frame at the same moments; face close-up
  (`--t 43.3`) ≈ 0.9 s. A/B inside one page: the bare lab set (sky + floor + shadows + post) is ~0.55–0.85 s of
  that and the magician adds ~0.15–0.25 s (most in close-ups: fill rate). Re-bench on an idle machine.
- Particles (motes, numbing dust, dizzy stars) live in the rig's root space: a long dust TRAIL while walking will move
  with the character — for world-space trails emit from the `pouch` anchor with your own `Particles`.
- `crashed` is a fixed composition (back toward −Z); rotate with `yaw` to fit the set.
- Frames are pure functions of (t, pose) (verified byte-identical out-of-order renders).
