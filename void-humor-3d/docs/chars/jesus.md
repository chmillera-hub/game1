# JESUS — `CHARS.JESUS` (speaker `'JESUS'`)

Files: `web/src/chars/jesus.js` (rig), `web/src/labs/jesus.js` (lab), this doc. No core files were modified.

```bash
node tools/render.js sheet --lab jesus --from 0 --to 3.5 --n 8 --cols 8 --out out/sheets/jesus_turn.jpg      # turntable
node tools/render.js sheet --lab jesus --from 4.5 --to 28.5 --n 25 --cols 5 --out out/sheets/jesus_expr.jpg  # expressions (1 s each)
node tools/render.js stills --lab jesus --t 46.6,48,50.5,53,56,60.5,79.5,82.5                                  # partner beats (real Void)
```
Lab segments (exported as `SEGMENTS`, name shown in a HUD label on every frame; every change is a weighted
crossfade, no ternary pops): 0–4 turntable · 4–29 expressions: kind, warm, beam, laugh, teehee, listening (nods),
whisper, amused, awkward (darting), compassion, tender, hopeful, eager, surprised, ooh, curious, reading, shrug
"eh, oh well", rueful, sad smile, wince, content, holding in a laugh, heart/sincere, talking · 29–31.5 idle ·
31.5–34.5 calm walk 3/4 · 34.5–37.5 stroll side, hands behind · 37.5–39.5 run · 39.5–45.5 kneel to the (real)
seated User, open palms · 45.5–51.5 arm around the **real Void** + whisper (front 3/4, then a close two-shot) ·
51.5–54.5 arm around the Void (back 3/4: the arm across its back) · 54.5–58 listening nods while the Void whispers
into his ear (`solvePos`) · 58–62 hand on the Void's shoulder (it looks over its shoulder) · 62–64.5 shrug ·
64.5–67.5 look at a floating notification (framed together) · 67.5–70 teehee · 70–73 awkward grimace · 73–78
talking gestures · 78–84 walk off with an arm around the Void, talking (front, then back 3/4) · 84–87 crouch + sit.

## Look

Stylized Pixar-like man, 1.74 m to the top of the hair, head (×1.08 sculpted skull + hair + beard) ≈ ¼ of the
height. Warm olive-tan skin with soft wrap shading and a **very subtle golden rim** on skin / hair / robe (no halo,
no iconography; `glow` scales it). Big warm brown eyes (deep-set eyeballs, lash line, catchlights), thick
swept dark-brown brows (wide range: the inner ends climb high for compassion / sad smiles), a lofted rounded nose,
gentle laugh lines + eye crinkles painted into the face decal when smiling. **Happy squeeze** (`lidU` < ~0.3 with
`mSmile` > ~0.5: `laugh`, `teehee`): the lower lids push up harder, the closed lids flatten into the socket, a dark
arched **^ ^ crease** is drawn over each closed eye (the normal lash lines hide), crow's feet and a cheek-bunching
crease + lit cheek apple are painted under the eyes.
**Sculpted short full beard**: a shell over jaw/cheeks/chin on a grid concentrated around the mouth. Its edges (the
static cheek line with a few soft tuft scallops, and the live lip opening) use a linear signed ramp, so the shell
crosses the skin exactly on the contour — clean curves, no grid stair-steps. The opening is recomputed every frame
from the painted mouth (lips: rosy lower lip + a visible upper-lip band), and the **mustache rides the upper lip**:
in a smile its corners lift with the mouth corners (no "toothbrush" patch), tuft lobes break the jaw/chin silhouette.
**Hair**: one sculpted shell — middle part with flow grooves, two soft side-swept masses over the temples (soft thin
forehead edge, no ledge), then a curtain to the shoulders made of **7 chunky locks** (3 per side + one at the back
centre): each lock bulges with an S-wave lobe profile, grooves between locks, and ends in its own rounded/tapered tip
rolled under. Matte (Lambert) with vertex-colour shading: darker roots, a soft sheen band round the crown and on the
lock crowns, lighter tips. The curtain rests on the shoulders, lifts over the sash on the left shoulder, and is pushed
outward over the raised upper arms / sleeve roots (no punch-through); front columns never dip inside the cheeks.
Cream/oatmeal lathe robe to the ankles (rounder shoulder rows): the skirt is **re-draped every frame** by a stateless
column solver (legs / hips / floor collisions; displacement diffusion "tents" it over knees; fabric bunches when the
hips drop). **Wide sleeves with real thickness**: outer cloth, a rolled hem at the cuff that folds inward, and a lit
inner lining running back up the sleeve (darkening with depth) — the cuff reads from every angle, no flat discs.
Terracotta **sash**: from a knot at the right front hip up over the LEFT shoulder, down the back, and wrapped round
the right side at the waist (under the rope belt) back into the knot — one continuous drape from every side — with
two short tails hanging from the knot under gravity. Twisted two-strand rope belt whose ends hang under gravity and
drape over the skirt (kneel: over the thigh, never sticking out). Sandals with visible toes. Smooth one-piece-finger
hands (own `SoftHand`, same API as core `Hand`). Shoulder / scapula **protraction**: far reaches and contacts slide
the shoulder joint up to ~11 cm toward the target; the robe shoulder, sleeve root and sash follow.

Rest measurements (root at feet, facing +Z): top 1.74 · head centre 1.53 · eyes 1.55 (z 0.14) · mouth 1.46
(z 0.13) · ears ±0.15 @1.52 · shoulder tops ±0.165 @1.35 · chest front (0, 1.20, 0.15) · hip 0.91 ·
hands hang at ~0.72 · feet ±0.10.

## Pose API — `jesus.update(t, pose)` (pure function of t + pose)

| field | meaning |
|---|---|
| `pos`, `yaw` | feet position, facing (0 = +Z) |
| `body.lean` | forward bend at the waist (rad, + forward). The head auto-compensates (`head.compensate`, default 1) |
| `body.tilt` | side bend (rad, **+ = toward his LEFT / +X**) |
| `body.twist` | chest turn vs. hips (rad, + = toward his left) |
| `body.kneel` 0..1 | **one knee down** (default right knee, `body.kneelSide: 'L'` for the left): 0→0.45 the front foot steps forward, 0.15→1 the hips drop, back knee to the floor, toes tucked; robe drapes over the raised knee and folds on the floor. Ease it over ~1–1.4 s |
| `body.crouch` 0..1 | squat, knees out, torso leans forward |
| `body.sit` 0..1 | sit on the ground, knees up (generic; above 0.35 the shins are wrapped in robe cloth — still not a hero pose) |
| `body.tiptoe` 0..1 | up on the balls of the feet (+6 cm) — whispering up to someone tall, reaching a high shoulder |
| `body.shrug` 0..1 | shoulders up (robe, mantle, hair and arm roots follow), head sinks |
| `body.giggle` 0..1 | teehee: rhythmic shoulder/head bounce at ~5 Hz + shoulders up a bit |
| `body.slump`, `hunch`, `recoil` (+ = lean back), `bounce` (m), `breathe` (amp mult, default 1), `breathRate` (Hz, default 0.22), `sway` (idle sway mult, default 1) |
| `walk {amount, phase, style}` | styles `walk` (calm, default), `stroll` (slower, smaller), `run`, `sneak`. `phase` in cycles (default `t * rate`). **Move `pos` at `jesus.walkSpeed(style) * cycles/s`** (metres per cycle: walk 1.05, stroll 0.9, run 2.1, sneak 0.6; default rates `jesus.walkRate(style)`: 0.85, 0.72, 1.35, 0.6 cyc/s → calm walk ≈ 0.9 m/s). Arms on `rest` swing automatically; other presets stay put |
| `head {yaw, pitch, roll}` | rad, relative to the chest. **yaw + = toward his left; pitch + = chin DOWN (nod), − = look up; roll + = tilt toward his LEFT shoulder.** Split 30/70 between neck and head |
| `head.look`, `head.follow` | world point the head turns toward with weight `follow` 0..1 (`follow` alone uses `gaze`). Eyes still need `gaze` |
| `head.talk` | head accents driven by speech (default 1, 0 = off) |
| `gaze` | Vector3 / [x,y,z] / Character / `'camera'` / null — the eyes |
| `dart` 0..1 | AWKWARD eye-darting: fast left/right saccades with holds (0.3–0.7 s). Use with face `'awkward'` |
| `face` | `'name'` · `['name', w]` · `[['a', wa], ['b', wb]]` · `{ expr: 'name', ...overrides }` · or flat params (core `X()` works too). Default `'kind'`. Names: Jesus presets below + all core `EXPR` |
| `speech` | `false` or `{open, wide, round, close}`; default = automatic lip-sync for speaker `JESUS` (mouth, beard opening and jaw follow) |
| `blinkAt` | extra explicit blink times (s) |
| `armL` / `armR` | see below. An arm with preset `around` (weight × reach) also adds an automatic lean / tilt / chest twist toward the partner (`auto: false` on that arm disables it) |
| `glow` | golden rim multiplier (default 1; 0 = off, 1.5 = a touch more radiant) |
| `shadow` | `false` hides the built-in soft contact shadow |

**Face presets (`JX(name, overrides)` / `JEXPR`)**: `kind` (default resting warmth, lower lids relaxed), `warm`,
`beam`, `laugh` (open laugh, eyes squeezed into ^ ^ creases), `teehee` (eyes squeezed shut into ^ ^, big closed
grin, blush), `content` (half-lidded peace), `listening`, `whisper` (conspiratorial, lopsided pursed smile),
`amused`, `awkward` (the hero "oh boy": wide clenched teeth with a tall teeth band, corners strained out & a touch
down, inner brows way up with a worried tilt — combine with `dart` + `body: {shrug: 0.7, hunch: 0.25}`),
`compassion` (inner brows high & together, sad lids, wet eyes), `concerned`, `tender` (inner brows up, sad lid tilt,
wet eyes — add a head roll), `hopeful`, `eager` (way-too-intense sparkly grin), `shrug` (brows way up, small
lopsided closed smile: an amiable "eh — oh well"), `rueful`, `oh`, `ooh`, `surprised`, `curious`, `reading`
(squint/furrow), `sadSmile` (inner brows high, strong sad lid tilt over a small smile), `wince`, `serene`,
`pressed` (holding in a laugh). The brow range is 0.2 rad of latitude at full value (inner/outer independent).

### Arms — `armL` / `armR`
`{ preset, target, surface, normal, height, span, auto, pole, palm, fingers, reach, at, offset, hand, gesture, wiggle, pat, patRate }`
- `preset`: name or weighted list `[['open', 0.6], ['knee_rest', 0.4]]` (blended in root space). Presets are
  defined for the LEFT arm and mirrored. Body-space presets follow the torso; face presets follow the head.
- `target` (world) overrides the preset's wrist target — or the **palm centre** for contact presets
  (`at: 'palm'`, default for `around`, `shoulder`, `pat`; force with `at: 'palm' | 'wrist'`).
- **Contact with a body** (`surface` / `normal`, palm presets):
  - `surface`: the partner — a Character (e.g. the Void instance) or any Object3D (its visible opaque meshes are
    raycast; update the partner BEFORE Jesus in the frame), or a world point on the partner's vertical axis
    (`[x,y,z]` / `{center}`) for an analytic round body.
  - `around` + `surface`: the hand walks round the partner's flank toward its back (the side away from his chest)
    at height `height` (default his shoulder + 0.16 m, or `target.y`) as far as a comfortable `span` from the
    shoulder (default 0.47 m; a `target` caps how far round). The palm faces into the surface, the fingers lie along
    it (wrapping, slightly curled), the hand sits just outside it, the elbow goes up and out toward the partner
    (reads from the front as the arm going up and round behind them; from behind as an arm across their back),
    the shoulder protracts, and the body leans / tilts / twists toward them automatically.
  - `around` with only `target` (old API, still fine): the palm lands on the target with the palm facing away from
    his chest and the fingers wrapping toward his back; pass `normal` (the partner's OUTWARD surface normal there)
    for exact control.
  - other palm presets (`shoulder`, `pat`) + `surface`: `target` is snapped onto the partner's surface (from above
    for a shoulder top, else along the reach) and the palm faces into it. `normal` alone does the same without
    raycasting.
- `pole` (elbow direction), `palm` (palm normal = the side the palm faces / the surface normal pointing INTO what it
  touches), `fingers` (finger direction): world-space directions overriding the preset. **If `palm` is given (or
  derived from a contact) and `fingers` isn't, the fingers are derived**: they lie forward along the reach in the
  palm plane, drooping a little — a hand on top of a shoulder drapes over it instead of pointing up.
- `reach` 0..1 blends from `rest` (keyframe it for reaches); `offset` (world vector) nudges the target.
- `hand`: `{ curl, point, spread, thumb, cup, splay, grip }` overrides (0..1).
- `gesture` 0..1: beat-gesture amplitude for `explain` (accents grow with the speech envelope).
- `pat`, `patRate`: amplitude / Hz of rhythmic pats (preset `pat`).
- Far reaches protract the shoulder (up to ~11 cm toward the target); robe shoulder, sleeve root and sash follow.

| preset | use |
|---|---|
| `rest` | relaxed at the sides (default; swings when walking) |
| `clasp` / `clasp_chest` | hands loosely clasped at the belt (patient listening) / at the chest (hopeful, excited) |
| `behind` | hands clasped behind the back (unhurried stroll) |
| `open` | open palms forward and out (welcoming, "talk to me"); with kneel + `hand: {splay: 0.08, cup: 0.45}` |
| `explain` | one-hand talking gesture, palm up, with automatic beat accents (`gesture`) |
| `offer` | palm-up reach toward someone · `reach` palm-down reach · `point` · `stop` (gentle "hold on, one sec") |
| `heart` | hand flat on his chest ("meaningful to me") |
| `shrug` | elbows in, forearms out, palms up — pair with `body.shrug` + face `shrug` |
| `knee_rest` | forearm resting on the raised knee when kneeling (auto-targets the front knee) |
| `around` | arm around someone BIG: `{ preset: 'around', surface: theVoid }` (best) or `target` = a point on their side/back |
| `shoulder` | hand resting ON someone's shoulder: `target` on their shoulder (+ `surface: them` to snap onto it); default palm down / fingers forward-down over the shoulder |
| `pat` | rhythmic pats (palm-anchored) |
| `whisper` | (face space) hand cupped beside the mouth, palm turned forward-inward so the C-shaped cup reads from the front — `armR` shields the right side so he whispers to his LEFT; mirror with `armL` |
| `teehee` / `cover_mouth` / `chin` / `wipe_eye` | (face space) curled fingertips to the lower lip, palm toward the face · palm over the mouth · knuckles under the chin · knuckle wiping a laugh tear |
| `hips`, `side`, `crossed`, `up`, `wave` | hands on hips · hand on own side · arms folded · arm up · waving |

## Anchors (world, valid after `update`)
`head` (centre), `top`, `eyes`, `mouth`, `earL`, `earR`, `chest` (front), `back`, `shoulderL`, `shoulderR`
(tops — where a hand/arm rests), `handL`, `handR` (palm centres), `hip`, plus `footL/R`, `kneeL/R`, `elbowL/R`.

## Recipes
- **Idle**: `{ face: 'kind', gaze: 'camera', armL: {preset: 'clasp'}, armR: {preset: 'clasp'} }` (breathing + sway are automatic).
- **Calm walk**: `const r = J.walkRate('walk'); pos.z += J.walkSpeed('walk') * r * dt; { walk: {amount: 1, phase: t * r} }`. Hands behind for the stroll: style `stroll` + `behind`.
- **Arm around the Void** (beat 2): stand him at its flank (his feet ~1.15–1.25 m from its axis; keep its near arm
  off its side, e.g. its `belly` preset), update the Void first, then
  `armL: { preset: 'around', surface: theVoid, reach }` (ramp `reach` 0→1 over ~0.8 s), `gaze: voidEyes`,
  `head: {look: voidEyes, follow: 0.55}`. Front shots read as the arm going up and round behind it; a back 3/4 shows
  the arm across its back. Lab: 45.5–54.5 s.
- **Whisper into an ear**: `armR: {preset: 'whisper'}`, `face: 'whisper'`, `gaze: ear`, `head: {look: ear, follow: 0.75, roll: -0.1}`, `body: {tilt: 0.1, lean: 0.05, tiptoe: 0.8}`, `speech: {open: 0.1–0.2, round: 0.5}`. The Void leans down to him with `whisperPose(-1, 0.75)` (its ear = `earR`).
- **Teehee**: `face: 'teehee', body: {giggle: 1, shrug: 0.4}, armR: {preset: 'teehee'}, head: {roll: 0.12}` (ramp `reach` 0→1 over ~0.3 s).
- **Listening nods**: drive `head.pitch` (e.g. `0.13 * max(0, sin(2π·1.3·t))`) with face `listening`; the Void's mouth goes to his ear with `vd.solvePos(t, W, 'whisper', jesus.anchor('earL'))`.
- **Awkward**: `face: 'awkward', dart: 1, body: {shrug: 0.7, hunch: 0.25}, armL/armR: {preset: 'clasp'}`; drive `gaze`/`gazeYaw` explicitly for scripted darts.
- **Hand on someone's shoulder** (beat 11): `armR: { preset: 'shoulder', target: theVoid.anchor('shoulderR'), surface: theVoid, reach }` — the palm snaps onto the shoulder top and the fingers drape forward over it (or give `palm` only: fingers are derived). Small nod via `head.pitch`.
- **Kneel to a seated person**: key `body.kneel` 0→1 over ~1.2 s, `gaze: them, head: {follow: 0.6}`, `armL: {preset: [['knee_rest', 0.6], ['open', 0.4]]}`, `armR: {preset: 'open' | 'explain', hand: {splay: 0.08, cup: 0.45}}`.
- **Shrug**: `body.shrug 0.85`, both arms `shrug`, `face: 'shrug'`, `head.roll 0.12`.
- **Look at a floating notification**: `gaze: p, head: {look: p, follow: 0.7}`, face `reading` → `oh` / `surprised` (blend with weights).
- **Walk off with an arm around someone, talking** (beat 15): walk as above with `yaw` = travel direction, the Void
  on his left (≈1.24 m to the side, waddling at the same ground speed), `armL: {preset: 'around', surface: theVoid}`,
  `armR: {preset: 'explain'}` (beats follow the lip-sync), `head: {look: voidEyes, follow: 0.5}`.
- **Crossfades**: never switch presets with a ternary — blend `face: [['kind', 1-w], ['tender', w]]`,
  `armR: {preset: [['open', 1-w], ['explain', w]]}`.

## Performance
- Materials: skin = MeshStandard, cloth / hair / beard / rope / leather = MeshLambert, all with a slim injected
  rim / glow / wrap term (`stdMat()` in jesus.js: no MeshPhysical sheen, no core `enhance()` fizz-noise code, which
  costs SwiftShader fill even when off). Only robe, head and hair shell cast shadows (sleeves / sash do not).
  Face decal uses a Lambert material. Outer layers draw first so early-z culls the skin underneath.
- CPU `update()` ≈ 5–7 ms/frame (robe drape, hair curtain + collisions, beard opening, arms); an `around` /
  `shoulder` contact with `surface` adds ~10 raycasts against the partner (≈ 5–12 ms with the Void).
- Benchmarks (machine load 17–28 on 4 cores, so measured as summed CPU time of the browser + SwiftShader threads per
  frame, interleaved with the core `facetest` lab, 10 frames each, two rounds):
  facetest 1.22–1.29 · full body (lab set) 1.23 (≈1.0× facetest) · face close-up 1.47–1.49 (≈1.2×) · partner
  two-shot with the real Void 1.55–1.73 (≈1.3–1.4×, includes the Void) · head filling the frame: original rig
  2.04–2.13 → now 1.48–1.57 (−27 %). With facetest at ≈0.42–0.48 s/frame unloaded this puts Jesus at ≈0.45 s full
  body, ≈0.55 s in a face close-up and ≈0.6 s in a Jesus + Void two-shot.
- Frames are a pure function of t: Jesus's pixels are identical whatever the render order (checked on lab frames
  rendered in two different orders).

## Known limitations
- Legs are invisible IK colliders; only ankles/sandals are drawn. `sit` wraps the raised shins in robe cloth, but the
  skirt itself puddles flat instead of tenting over the knees — keep `sit` out of hero shots.
- Robe, hair and sash have no momentum (stateless): swing is procedural from the walk phase; fast turns don't swish.
- The beard's mouth opening and the mustache lift mirror the mouth math of `core/face.js` (`mouthGeom`); if the core
  mouth drawing changes, update `mouthGeom()` in `jesus.js`.
- `around` reaches ~0.47 m (`span`) from the shoulder: on the 2.2 m-wide Void the hand lands on its flank / lower back,
  not its far side. From a straight front camera the arm reads as going up and round behind it (that is what an
  arm round a much bigger body looks like); show the hand / arm across the back with a back or side 3/4 angle.
- `surface` raycasts the partner's visible opaque meshes: if the partner's hand / arm hangs where the contact goes,
  the hand rests on that instead (put the Void's near arm on its belly / hips).
- Pupils/eyelids follow the core `Eye` (spherical lid shells); extreme upward gazes show sclera below the iris —
  turn the head (`head.follow`) for big look-ups.
- `framed()`'s `screenY` in core/camera.js places the look point at (1 − screenY) of the frame height from the top
  (the comment says the opposite); the lab uses values > 0.5 for faces in the upper half.
