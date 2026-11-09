# JESUS — `CHARS.JESUS` (speaker `'JESUS'`)

Files: `web/src/chars/jesus.js` (rig), `web/src/labs/jesus.js` (lab), this doc. No core files were modified.

```bash
node tools/render.js sheet --lab jesus --from 0 --to 3.5 --n 8 --cols 8 --out out/sheets/jesus_turn.jpg      # turntable
node tools/render.js sheet --lab jesus --from 4.5 --to 28.5 --n 25 --cols 5 --out out/sheets/jesus_expr.jpg  # expressions (1 s each)
node tools/render.js sheet --lab jesus --from 29.5 --to 80 --n 24 --cols 6 --out out/sheets/jesus_act.jpg    # poses / actions
```
Lab segments (exported as `SEGMENTS`, name shown in a HUD label on every frame):
0–4 turntable · 4–29 expressions: kind, warm, beam, laugh, teehee, listening (nods), whisper, amused, awkward
(darting), compassion, tender, hopeful, eager, surprised, ooh, curious, reading, shrug "eh", rueful, sad smile,
wince, content, holding in a laugh, heart/sincere, talking · 29–31.5 idle · 31.5–34.5 calm walk 3/4 ·
34.5–37.5 stroll side, hands behind · 37.5–39.5 run · 39.5–45.5 kneel to a seated person, open palms ·
45.5–50.5 arm around a big partner + whisper · 50.5–53.5 listening nods · 53.5–56.5 hand on shoulder ·
56.5–59 shrug palms up · 59–62 look at a floating notification · 62–64.5 teehee · 64.5–67.5 awkward grimace ·
67.5–72.5 talking gestures · 72.5–77.5 walk off with an arm around, talking · 77.5–80.5 crouch + sit.

## Look

Stylized Pixar-like man, 1.74 m to the top of the hair, head (×1.08 sculpted skull + hair + beard) ≈ ¼ of the
height. Warm olive-tan skin with soft wrap shading and a **very subtle golden rim** on skin / hair / robe (no halo,
no iconography; `glow` scales it). Big warm brown eyes (deep-set eyeballs, lash line, catchlights), thick
swept dark-brown brows, a lofted rounded nose, gentle laugh lines + eye crinkles painted into the face decal when
smiling (`mSmile` > 0.3). **Sculpted short full beard**: a shell over jaw/cheeks/chin whose mouth opening is
recomputed every frame from the painted mouth shape, so lips (rosy lower lip + thin upper lip, painted) and the
mouth line always sit in a clean skin band — the mustache never covers the mouth, and teeth/laughs/clench read.
**Hair**: middle-parted cap with broad flow grooves that continues into a hanging curtain to the shoulders
(gravity-bent, rests on the shoulders via collision, scalloped wavy ends rolled under) + four chunky sheen locks.
Cream/oatmeal lathe robe to the ankles: the skirt is **re-draped every frame** by a stateless column solver
(collides with invisible IK legs / hips / floor; displacement diffusion "tents" it over knees; fabric bunches
when the hips drop) — walk sway, a knee pushing through when stepping, folds over the raised knee when
kneeling, a small puddle on the floor. Wide bell sleeves (dark open lining) that slide toward the elbow when the
forearm is raised (forearm visible) and droop when horizontal. Terracotta mantle band over the LEFT shoulder
(front diagonal to the right hip, back diagonal), twisted two-strand rope belt with a knot and two hanging ends
that ride the skirt, brown sandals with visible toes. Smooth one-piece-finger hands (own `SoftHand` in the file,
same API as core `Hand`, anatomically correct thumb side).

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
| `body.sit` 0..1 | sit on the ground, knees up (generic; shins show — not a hero pose) |
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
| `armL` / `armR` | see below |
| `glow` | golden rim multiplier (default 1; 0 = off, 1.5 = a touch more radiant) |
| `shadow` | `false` hides the built-in soft contact shadow |

**Face presets (`JX(name, overrides)` / `JEXPR`)**: `kind` (default resting warmth), `warm`, `beam`, `laugh`
(eyes squeezed into ^^ arcs), `teehee` (eyes squeezed shut, big closed grin, blush), `content` (half-lidded
peace), `listening`, `whisper` (conspiratorial, lopsided pursed smile), `amused`, `awkward` (clenched-teeth wide
grimace, brows high — combine with `dart` + `body.shrug`), `compassion` (inner brows up & together),
`concerned`, `tender`, `hopeful`, `eager` (way-too-intense sparkly grin), `shrug` (brows up, corners down "eh"),
`rueful`, `oh`, `ooh`, `surprised`, `curious`, `reading` (squint/furrow), `sadSmile`, `wince`, `serene`,
`pressed` (holding in a laugh).

### Arms — `armL` / `armR`
`{ preset, target, pole, palm, fingers, reach, at, offset, hand, gesture, wiggle, pat, patRate }`
- `preset`: name or weighted list `[['open', 0.6], ['knee_rest', 0.4]]` (blended in root space). Presets are
  defined for the LEFT arm and mirrored. Body-space presets follow the torso; face presets follow the head.
- `target` (world) overrides the preset's wrist target — or the **palm centre** for contact presets
  (`at: 'palm'`, default for `around`, `shoulder`, `pat`; force with `at: 'palm' | 'wrist'`).
- `pole` (elbow direction), `palm` (palm normal, i.e. the side the palm faces / the surface normal pointing INTO
  what it touches), `fingers` (finger direction): world-space directions overriding the preset.
- `reach` 0..1 blends from `rest` (keyframe it for reaches); `offset` (world vector) nudges the target.
- `hand`: `{ curl, point, spread, thumb, cup, splay, grip }` overrides (0..1).
- `gesture` 0..1: beat-gesture amplitude for `explain` (accents grow with the speech envelope).
- `pat`, `patRate`: amplitude / Hz of rhythmic pats (preset `pat`).

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
| `around` | arm around someone BIG: give `target` = a point on their side/back at ~1.35–1.6 m (palm lands on it) |
| `shoulder` | hand resting on someone's shoulder: `target` on their shoulder surface; default palm faces forward-down — pass `palm` (into their surface) when it's a top-of-shoulder |
| `pat` | rhythmic pats (palm-anchored) |
| `whisper` | (face space) hand cupped vertically beside the mouth — `armR` shields the right side so he whispers to his LEFT; mirror with `armL` |
| `teehee` / `cover_mouth` / `chin` / `wipe_eye` | (face space) fingertips to the lips giggle · palm over the mouth · knuckles under the chin · knuckle wiping a laugh tear |
| `hips`, `side`, `crossed`, `up`, `wave` | hands on hips · hand on own side · arms folded · arm up · waving |

## Anchors (world, valid after `update`)
`head` (centre), `top`, `eyes`, `mouth`, `earL`, `earR`, `chest` (front), `back`, `shoulderL`, `shoulderR`
(tops — where a hand/arm rests), `handL`, `handR` (palm centres), `hip`, plus `footL/R`, `kneeL/R`, `elbowL/R`.

## Recipes
- **Idle**: `{ face: 'kind', gaze: 'camera', armL: {preset: 'clasp'}, armR: {preset: 'clasp'} }` (breathing + sway are automatic).
- **Calm walk**: `const r = J.walkRate('walk'); pos.z += J.walkSpeed('walk') * r * dt; { walk: {amount: 1, phase: t * r} }`. Hands behind for the stroll: style `stroll` + `behind`.
- **Arm around the Void**: `armL: { preset: 'around', target: voidSidePoint }` (≈1.4–1.6 m on its side/back, within ~0.5 m of his shoulder), `head: {look: voidEyes, follow: 0.6}`, `gaze: voidEyes`.
- **Whisper into an ear**: `armR: {preset: 'whisper'}`, `face: 'whisper'`, `gaze: ear`, `head: {look: ear, follow: 0.75, roll: -0.1}`, `body: {tilt: 0.1, lean: 0.05, tiptoe: 0.8}`, `speech: {open: 0.1–0.2, round: 0.5}`.
- **Teehee**: `face: 'teehee', body: {giggle: 1, shrug: 0.4}, armR: {preset: 'teehee'}, head: {roll: 0.12}` (ramp `reach` 0→1 over ~0.3 s).
- **Listening nods**: drive `head.pitch` (e.g. `0.13 * max(0, sin(2π·1.3·t))`) with face `listening`.
- **Awkward**: `face: 'awkward', dart: 1, body: {shrug: 0.7}, armL/armR: {preset: 'clasp'}`; drive `gaze`/`gazeYaw` explicitly for scripted darts.
- **Hand on someone's shoulder**: `armR: {preset: 'shoulder', target: theirShoulderSurfacePoint, palm: intoTheirSurface}`; small nod via `head.pitch`.
- **Kneel to a seated person**: key `body.kneel` 0→1 over ~1.2 s, `gaze: theirEyes, head: {follow: 0.6}`, `armL: {preset: [['knee_rest', 0.6], ['open', 0.4]]}`, `armR: {preset: 'open' | 'explain', hand: {splay: 0.08, cup: 0.45}}`.
- **Shrug**: `body.shrug 0.85`, both arms `shrug`, `face: 'shrug'`, `head.roll 0.1`.
- **Look at a floating notification**: `gaze: p, head: {look: p, follow: 0.7}`, face `reading` → `surprised` / `oh`.
- **Walk off with an arm around someone, talking**: walk as above with `yaw` = travel direction, `armL: {preset: 'around', target: partner.anchor(...)}`, `armR: {preset: 'explain'}` (beats follow the lip-sync), `head: {look: partnerEyes, follow: 0.6}`.

## Performance
CPU `update()` ≈ 6 ms/frame (robe drape + hair curtain + beard opening + arms); 60 meshes / ~49k triangles
(feet, belt, nose/ears, palms merged; only robe, head, hair shell, sleeves and mantle cast shadows; outer layers
draw first so early-z culls the skin underneath; face decal kept small). GPU (SwiftShader fill) dominates.
Measured: quiet machine, before the last optimisation pass — empty lab 0.42 s, lab + Jesus in a head-filling
close-up 0.81 s. Under the shared load during development (load avg ≈ 11 on 4 cores) the trivial `facetest` lab
benched 0.88–1.37 s/frame and this lab 1.04–1.45 s (full body) / 1.23–1.76 s (close-up), i.e. Jesus costs about
0–30 % more than the facetest head in the same conditions. Frames are bit-identical regardless of render order.

## Known limitations
- Legs are invisible IK colliders; only ankles/sandals are drawn (fine under the robe; `sit` shows shins).
- Robe and hair have no momentum (stateless): swing is procedural from the walk phase; fast turns don't swish.
- The beard's mouth opening mirrors the mouth math of `core/face.js` (`mouthGeom`); if the core mouth drawing
  changes, update `mouthGeom()` in `jesus.js`.
- The mantle is rigid with the chest (no flutter); raising the LEFT arm very high intersects its shoulder band
  slightly — prefer `armR` for overhead gestures, or `armL` with moderate height.
- `around` cannot physically reach behind a 3 m-wide body: put the target on the partner's near side/back
  within ~0.5 m of his shoulder (the Void should stand close / lean in).
- Pupils/eyelids follow the core `Eye` (spherical lid shells); extreme upward gazes show sclera below the iris —
  turn the head (`head.follow`) for big look-ups.
