# USER ("the Twitter user") — `CHARS.USER` (speaker `'USER'`)

Files: `web/src/chars/user.js` (rig), `web/src/labs/user.js` (lab), this doc. **No core files were modified.**

```bash
node tools/render.js sheet --lab user --from 0 --to 3.5 --n 8 --cols 4 --out out/sheets/user_turn.jpg        # turntable
node tools/render.js sheet --lab user --from 4.5 --to 27.5 --n 24 --cols 6 --out out/sheets/user_expr.jpg    # expressions (1 s each)
node tools/render.js sheet --lab user --from 28.6 --to 87.6 --n 30 --cols 6 --out out/sheets/user_act.jpg    # poses / actions
```
Lab segments (exported as `SEGMENTS`; the name is printed in a HUD label on every frame):
0–4 turntable · 4–28 expressions: idle (default, guarded), scroll (phone up), sob + tears, terror + tears,
silent scream, gasp, what the actual—, scrunch (the bleep), deadpan, hell no, pout, smirk, suspicious squint, glare,
gulp, guilt flicker, softening (glisten), lip tremble, dawning "…you?", not-quite smile, nervous grimace, storm,
disbelief (half-mast), talking · 28–31 phone up, scroll + thumb taps · 31–34 walk · 34–37 panicked run (front),
sobbing, look back · 37–39 run (side) · 39–42.5 stumble + fall onto backside (sit 0→1) → defend · 42.5–45 seated
terror, tears, trembling splayed hand · 45–48 scoot backward · 48–50.5 "what the actual—" lean + flap ·
50.5–53 "hell no" head shake · 53–56.5 jab phone at a partner → crossed arms + pout · 56.5–59 hug the phone
(clutch) · 59–62 softening: hand on heart, lip tremble, glisten · 62–64 phone face-down in lap · 64–66.5 get up
(rise path) · 66.5–69.5 storm off (stomp) · 69.5–72.5 stomp away + look back · 72.5–75.5 thumb-tap Block →
blocked (phone insert) · 75.5–77.5 show the phone over the shoulder · 77.5–80 defend at a partner (arm target) ·
80–83 wipe tear, push glasses up · 83–85.5 phone glow in the dark · 85.5–88 kneel + crouch.

## Look
Young adult, gender-ambiguous-to-feminine, 1.65 m (≈1.63 to the top of the hair, cowlick a bit above). Big
round head (×1.12 sculpted skull, round cranium, full cheeks, soft small chin), **big hazel eyes** (green outer
iris → warm gold centre, lash lines with an outer flick, lower lashes), swept dark brows with a wide range, a
small upturned button nose, painted mouth with a soft rosy lower lip, permanent rosy cheeks and **painted
freckles** (cheeks + nose bridge; decal). **Round glasses**, slightly too big, thin plum-black frames, a faint
diagonal lens glint (stronger when the phone glows) — the frames sit below the brows and never cover the eyes;
temple arms hug the face and vanish under the hair. **Messy dark-brown bob**: one sculpted shell (side part on
the character's LEFT, chunky flow grooves, hair falling straight from the widest point to the jaw, rolled-under
ends) + chunky accent locks (a fringe swept to the character's right that stays above the brows, face-framing
clumps, curtain clumps that flick out / tuck under) + a 3-lock **cowlick** at the crown that bounces. The hanging
ends swing on the GPU (stateless). **Oversized slate-blue hoodie**: a skinned lathe body that bends between pelvis
and chest, drapes over the thighs when sitting / running (capsule push-out), ribbed hem, kangaroo pocket (raised
patch + slanted openings), hood down (thick rolled collar + hood lying on the back), two drawstrings with metal
aglets that hang with gravity and bounce; oversized drop-shoulder sleeves with accordion bunching on the forearm
and ribbed cuffs. Charcoal joggers (bunched above the cuff), **chunky white sneakers** (two-tone sole, laces,
padded collar, slate heel tab, no logos). Soft hands (one-piece fingers, anatomically correct thumb).
**Phone**: generic coral-cased slab with a camera bump; the screen is a canvas (no logos: plain white
speech-bubble icon on a header, grey cards). Its cool glow lights whatever the screen faces (face, hands, hoodie)
via a custom shading term (no extra scene light → no recompiles in any set), glints in the corneas and lenses.

Rest measurements (root at the feet, facing +Z): head centre 1.43 · eyes 1.43 (z 0.16) · mouth 1.35 (z 0.15) ·
shoulder joints ±0.17 @1.215 · chest front (0, 1.10, 0.15) · hip (pelvis) 0.835 · hands hang at ~0.76 · feet ±0.10.

## Pose API — `user.update(t, pose)` (pure function of t + pose)

| field | meaning |
|---|---|
| `pos`, `yaw` | feet position, facing (0 = +Z) |
| `body.lean` | forward bend (rad, + forward). The head auto-compensates for lean and pelvis tilt (`head.compensate`, default 1) |
| `body.tilt`, `body.twist` | side bend (+ toward their LEFT) · chest turn vs hips (+ toward their left) |
| `body.sit` 0..1 | sit on the ground on the backside, legs forward, toes up. **`body.sitPath`**: `'fall'` (default) = animated stumble → fall: one foot skids, legs kick up, arms fling up (the phone hand keeps the phone up high), impact squash (head dips, glasses jump, eyes squeeze), slight rebound; `'rise'` = get-up path for 1→0 (knees pull in, weight forward over the feet, push up); `'plain'` = straight blend. Ease 0→1 over ~0.6–0.8 s for a fall, 1→0 over ~1.4–1.8 s to get up |
| `body.scoot` 0..1, `body.scootPhase` | scoot backward while seated (needs sit ≈ 1): hips hitch back, feet re-plant. **Move `pos` backward at `user.scootSpeed(scoot) × cycles/s`** (0.09 m/cycle; default phase `t*1.6`) |
| `body.kneel` 0..1 (`kneelSide` 'L'/'R'), `body.crouch` 0..1 | one knee down · squat |
| `body.shrug`, `hunch` (default 0.18 — they're always a bit hunched), `slump`, `recoil` (+ = lean back), `bounce` (m) | posture |
| `body.flinch` 0..1 | jolt: shoulders up, head down/back (key it over ~0.1–0.2 s; pair with face `scrunch` for 3 frames) |
| `body.tremble` 0..1 | fine full-body tremor (torso, head, hands, cowlick) |
| `body.pant` 0..1 | fast shallow breathing (strings bounce with it) · `breathe`, `breathRate` as usual |
| `body.jut` −0.5..1 | head/neck forward ('what the actual—' disbelief) |
| `body.lookBack` −1..1 | look back over the shoulder (+ = over their LEFT shoulder): hips, chest and head twist; also set `gaze` behind |
| `walk {amount, phase, style, flail}` | styles `walk`, `run` (panicked: forward lean, high knees, pumping fists with the phone in the fist, `flail` 0..1 default 0.55 = arms going wild), `stomp` (storm off: hunched, chin down, fists, heavy flat slams with a body drop on each step, phone in fist at the side), `sneak`. **Move `pos` at `user.walkSpeed(style) × user.walkRate(style)` m/s** (stride m/cycle: walk 0.92, run 1.7, stomp 0.8, sneak 0.55; rates 0.95, 1.45, 1.0, 0.6 cyc/s) |
| `head {yaw, pitch, roll, look, follow, talk, compensate}` | rad relative to the chest; yaw + = toward their left, pitch + = chin DOWN, roll + = toward their left shoulder. `look`/`follow` turn the head to a world point. Use `headShake()` for 'hell no' (below) |
| `gaze` | Vector3 / [x,y,z] / Character / `'camera'` / null — the eyes (use `user.anchor('phoneScreen')` to read the phone) |
| `face` | `'name'` · `['name', w]` · `[['a', wa], ['b', wb]]` · `{ expr: 'name', ...overrides }` · flat params (core `X()` works). Default `'idle'` |
| `speech` | `false` or `{open, wide, round, close}`; default = automatic lip-sync for speaker `USER` |
| `blinkAt` | extra explicit blink times (s) |
| `armL` / `armR` | see below |
| `extra` | phone, tears, glasses — see below |
| `rim` | rim-light multiplier (default 1) · `shadow: false` hides the contact shadow |

### `extra` (character-specific)
| field | meaning |
|---|---|
| `phone` 0..1 | screen brightness (default 0.85). 0 = dark screen. Drives the cool glow on the face/hands/hoodie |
| `phoneUp` 0..1 | lifts the phone hand from its preset to "reading it" in front of the chest (screen to the face). Pair with `gaze: user.anchor('phoneScreen')` and `head.pitch ≈ 0.2` |
| `screen` | `'feed'` (default; scrolling grey cards) · `'block'` (confirm dialog "Block Jesus?" with a red **Block** button) · `'blocked'` ("You blocked Jesus." + avatar + Unblock) · `'profile'` (profile card, bio "Would love to hear about your feelings.", red Block) · `'off'` |
| `screenName` | name shown on block/blocked/profile screens (default `'Jesus'`) |
| `scroll` | feed scroll offset (cards; animate it while the thumb flicks) |
| `tap` 0..1 | thumb press (pulses; 0 = hovering 1.4 cm above the screen, 1 = touching). Setting `tap` puts the thumb on the screen |
| `thumb` 0..1 | thumb over the screen without tapping (default 1 whenever `tap` is given) |
| `thumbAt` [u, v] | where the thumb hovers/taps in screen coords (u right, v down). Defaults per screen: the red **Block** button on `'block'` |
| `glow` | glow multiplier (default 1) |
| `phoneHand` | `'L'` (default) or `'R'` — the hand that holds the phone (its default arm preset becomes `hold`) |
| `phoneVisible` | false hides the phone |
| `tears` 0..1 | tear streaks + 3D drops sliding down the cheeks (flung back while running) + wet eyes |
| `glisten` 0..1 | wet tear line along both lower lids + extra eye shine (also automatic from face `wet`) |
| `glasses` | 0 hides the glasses · `glassesSlip` 0..1 slid down the nose · `glassesTilt` (rad, askew) · `glassesJump` (m-ish bump; automatic on the fall impact) |
| `hairSwing` [x,y,z] | extra displacement of the hanging bob ends (head space, metres; ~±0.02). `headShake()` returns it |

### Arms — `armL` / `armR`
`{ preset, target, pole, palm, fingers, reach, offset, hand, grip, tremble, flap, flail, wiggle }`
- `preset`: name or weighted list `[['prop', 0.6], ['knee', 0.4]]`. Defined for the LEFT arm, mirrored.
- `target` (world wrist target) overrides the preset; `pole` (elbow dir), `palm` (palm normal = the phone screen's
  facing when the phone is in that hand), `fingers` (finger dir) — world space. `reach` 0..1 blends from the
  default (`hold` for the phone hand, `rest` otherwise). `offset` world nudge.
- `hand`: `{ curl, point, spread, thumb, cup, splay, grip }` overrides. `grip`: phone grip `'flat'|'fist'|'tuck'`.
- `tremble` 0..1 (shaking hand), `flap` 0..1 (a feeble outward flap of a raised hand — key it as a pulse),
  `flail` (run only).

| preset | use |
|---|---|
| `rest` / `hold` | arms down · phone held at the belly, screen tilted to the face (phone-hand default) |
| `look` | phone up reading it (same as `extra.phoneUp: 1`) |
| `clutch` | **hug the phone flat to the sternum, screen in** (use on the phone hand) · `hug` = the other hand pressing over it |
| `defend` | **hand UP defensively, palm out, fingers splayed** (add `tremble`; `target` = toward the threat) |
| `stop` | feeble chest-height stop palm |
| `prop` | seated: palm flat on the ground behind the hip (the phone hand props on a fist) |
| `knee` | seated: hand resting on the knee · `lap` = phone held in the lap (add `palm: [0,-1,0]` world for face-down) |
| `crossed` | arms folded (phone tucked) — use on both arms |
| `heart` | hand flat on own chest ("is something in there real?") |
| `jab` | thrust the phone out screen-first (give `target` toward the threat; add `tremble`) |
| `shield` | phone held up in front of the lower face, screen out |
| `show` | phone held up over the shoulder, screen facing back (show someone behind: "blocked") |
| `pocket`, `hips`, `point`, `shrug`, `strings` | hand in the kangaroo pocket · on hip · point · shrug · tug the hood strings |
| `wipe`, `glasses`, `cover_mouth` | (face space) knuckle wipes a tear · index pushes the glasses up the nose · palm over the mouth |

### Face presets (`UX(name, overrides)` / `UEXPR`; all core `EXPR` names work too)
`idle` (default: guarded neutral), `scroll` (phone-face), `sob` (eyes squeezed, inner brows up, wailing mouth,
tears), `terror` (whites around the irises, pinpoint pupils, trembling open mouth), `scream` (silent scream
grimace, teeth), `gasp` (O mouth), `wtf` (brows up asymmetric, jaw open), `scrunch` (the bleep: everything
squeezed), `deadpan` (half-mast), `hellno` (narrowed, brows crushed, lips pressed), `pout` (lower lip out),
`smirk`, `suspicious`, `glare`, `gulp`, `guilt` (6-frame flicker), `soften` (wide, wet, inner brows up, lips
parted), `tremble` (pressed trembling lips, chin crumple, wet), `dawning` ("…you?"), `notquite` (the faintest
not-quite smile), `nervous` (clenched grimace), `storm` (angry pout), `disbelief`.

## Anchors (world, valid after `update`)
`head`, `top`, `eyes`, `mouth`, `earL`, `earR`, `chest` (front), `back`, `shoulderL`, `shoulderR`, `handL`,
`handR` (palm centres), `hip`, **`phone`** (phone centre), **`phoneScreen`** (screen centre, on the glass), plus
`footL/R`, `kneeL/R`, `elbowL/R`. `user.phone` is the phone Group (its +Z = screen normal, +Y = phone up) for
insert shots.

## Helpers
`headShake(t, t0, {count=2.5, dur=0.85, amp=0.36})` → `{ yaw, hairSwing }` — 'hell no': pass `head: {yaw}` and
`extra: {hairSwing}` (the bob lags the head). `user.walkSpeed/walkRate(style)`, `user.scootSpeed(amount)`.
Exports: `UX`, `UEXPR`, `ARM`, `WALK`, `headShake`, `User`.

## Recipes (story beats)
- **Run crying from the Void**: `walk: {amount: 1, style: 'run', phase: t*rate}`, `face: 'sob'`, `extra: {tears: 1, phone: 0.8}`;
  look back: `body: {lookBack: 0.85}`, `gaze: voidEyes`, face → `'scream'` for ~0.5 s.
- **Stumble + fall**: ramp run amount 1→0 over 0.2 s while `body.sit` 0→1 over ~0.75 s (`sitPath: 'fall'`, default),
  face `gasp` mid-air → `terror`; after impact ramp `armR: {preset: 'defend', tremble: 1}`, `armL: {preset: 'prop'}`,
  `body: {shrug: 0.6, tremble: 0.6, pant: 1}`, `extra: {tears: 0.7}`.
- **Scoot back**: `body: {sit: 1, scoot: 1, scootPhase: lt*1.6}` and move pos backward at `scootSpeed(1)*1.6` m/s.
- **"What the actual—"**: `body: {sit: 1, jut: 1, lean: 0.2}`, `face: 'wtf'`, a `flap` pulse on the raised arm on
  "actual", `face: 'scrunch'` (+`flinch` 0.5) on the bleep; then `glassesSlip` 1→0 with `armR: {preset: 'glasses'}`.
- **Pretend to scroll**: `extra: {phoneUp: 1, scroll: k*t, tap: pulses}`, `gaze: anchor('phoneScreen')`, `head.pitch 0.2`;
  peek up: gaze to the Void with `head.pitch` still down (eyes over the glasses).
- **'Hell no'**: `const hs = headShake(t, T('line')+0.1)` → `head: {yaw: hs.yaw}`, `extra: {hairSwing: hs.hairSwing}`, `face: 'hellno'`.
- **"That scary thing"**: `armL: {preset: 'jab', target: towardVoid, tremble: 0.6}`, then both arms `crossed`, `face: 'pout'`, `head.pitch −0.12`.
- **Softening**: `face: 'soften'` / `'tremble'`, `armR: {preset: 'heart'}`, `extra: {glisten: 1}`; phone face-down:
  `armL: {preset: 'lap', palm: [0,-1,0]}`, `extra: {phone: 0}`.
- **Hug the phone**: `armL: {preset: 'clutch'}`, `armR: {preset: 'hug'}`, `body: {shrug: 0.45, hunch: 0.4}`.
- **Get up + storm off**: `body: {sit: 1→0, sitPath: 'rise'}` over ~1.6 s, face `storm`; then `walk: {style: 'stomp'}`.
  Glance back: `body.lookBack` ramp 0→0.9→0 over ~1 s with face `guilt`.
- **Block insert**: `extra: {phoneUp: 1, screen: 'block', tap: pulse, thumb: 1}` (thumb defaults to the Block button),
  then `screen: 'blocked'`. Put the camera on `user.phone`'s +Z axis ~0.24 m out and roll it by the phone's +Y
  (see the lab's insert segment). Lower `extra.phone` (~0.6) if the screen blooms too much in a close insert.
- **Show the screen over the shoulder**: `armL: {preset: 'show'}`, `extra: {screen: 'blocked', phone: 1}`.

## Performance
CPU `update()` ≈ 4 ms (torso skinning ~1k verts, ~20 swept tubes, decal redraw only when the mouth changes).
≈ 72 draw calls / ~20k character triangles; secondary materials have no sheen; small parts (shoes, locks, hood)
don't cast shadows. The machine was heavily loaded during development (load avg 6–8.5 on 4 cores; the trivial
`facetest` lab benched 0.525 s). Best measured: lab set alone **0.554 s/frame**, set + USER full body (t=2)
**0.591 s/frame**, seated action (t=50) 0.677 s; under heavier load the same frames measured up to 1.0–1.4 s
(set alone up to 1.03 s) — the character itself adds ≈ 0.04–0.1 s.

## Known limitations
- Stateless: hair swing / strings / cowlick are procedural from walk phase, impact and `hairSwing`; fast turns
  don't swish unless the scene passes `hairSwing` (use `headShake()` for shakes).
- The hoodie hem drapes over the thighs via capsule push-out only; extreme crouches can show slight hem/leg
  interpenetration. Sleeves and torso don't collide (arms crossing deep into the chest clip a little).
- Phone `flat` grip: the phone lies on the palm/fingers (fingers stay behind the slab); fingertips don't wrap the
  edges. `fist` grip (running/stomping) wraps the fingers over the screen.
- Glasses are a rigid frame (no lens refraction); the lens glint is additive and slightly visible in darkness.
- Seated `defend`/`prop` presets assume `sit ≈ 1`; `sitPath: 'plain'` at mid values floats the pelvis (generic).
- **Core note (not changed):** `core/camera.js framed()` places the look point at `1 − screenY` from the top
  (its doc says `screenY`, 0 = top) — the lab uses its own corrected `framed()`.
