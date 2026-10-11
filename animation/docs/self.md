# SELF / CONSCIOUSNESS — `src/chars/self.mjs`

The narrator: the same person in two outfits. **SELF** is the real-world version (`outfit:'sweater'`, REAL_ROOM).
**CONSCIOUSNESS / "the CEO"** is the mind version (`outfit:'ceo'`: charcoal blazer over the sweater, gold CEO badge, optional clipboard).
Contact sheet: `node tools/sheet_self.mjs` → `out/sheet_self.png` (35 cells; also prints draw timings).

```js
import { drawSelf, SELF_EXPR, SELF_ARMS, ANCHORS, HEIGHT, WALK_ADVANCE, selfLocal, selfPoseAnchors,
         drawSelfNotebook, drawClipboard, SELF_FACE, SELF_COLORS } from '../chars/self.mjs';
import { EXPR, withSpeech } from '../face.mjs';

drawSelf(g, x, y, scale, { t, outfit: 'ceo', face: withSpeech(SELF_EXPR.sternKind, S.lip('CONSCIOUSNESS', t)) });
```

## Exports
| name | what |
|---|---|
| `drawSelf(g, x, y, scale, pose)` | Draws the character. Saves/restores the canvas state (transform, alpha, composite, line/font state are left as found). |
| `HEIGHT` | 600 (px at scale 1, feet → top of the hair). |
| `ANCHORS` | Static local points at scale 1, facing 1, neutral pose: standing, `.seated`, `.kneel`. See below. |
| `WALK_ADVANCE` | 176: px (× scale) the character must travel per 2π of `walk.phase` so the planted foot does not slide. |
| `selfPoseAnchors(x, y, scale, pose)` | **World** coords of `headCenter, headTop, eyes, mouth, chin, neck, shoulderL, shoulderR, chest, hip` for any pose (kneel/lean/seated/walk/facing/back-view head shift included). Use for eyelines, camera targets, props. |
| `selfLocal(x, y, scale, facing, wx, wy)` | Converts a world point into this character's local arm-target coords (same x,y,scale,facing you pass to drawSelf). |
| `SELF_EXPR` | Expression presets tuned for this face (see below). Same vocabulary as face.mjs `EXPR`; both work. |
| `SELF_ARMS` | Arm presets `(side, skeleton) => spec`. Use by name. |
| `SELF_FACE`, `SELF_COLORS` | Face style for `drawFace`, palette. |
| `drawSelfNotebook(g, x, y, scale, {mode, angle, t})` | The old notebook "my first story" (crayon cover: "My Story", sun, tiny lavender bean with huge eyes beside a tall dark hooded figure with gold star stickers). `mode`: `'closed'` (cover to camera, 70×92 at scale 1), `'heldOpen'` (outer covers, 140×92), `'pages'` (lying open, pencil writing + doodle, 150×96). Centred on (x,y). Use it for the desk prop so it matches the one SELF holds. The title uses `Caveat` (register it with `GlobalFonts` in the renderer; falls back to sans-serif). |
| `drawClipboard(g)` | Clipboard prop centred at (0,0), 62×84 (translate/scale yourself). |

## Coordinates and sizes (scale 1)
Local coords: origin = the point you pass as (x,y); **y up is negative**; +x = the facing direction side when `facing:1`.

- **Standing / walking / kneeling**: origin = ground point between the feet.
  hair top −598 · head centre (0,−488) · eyes −486 · mouth −451 · chin −426 · neck −400 · shoulders (±58, −382) ·
  chest (0,−342) · hip −250 · rest wrists ≈ (±71, −197), fingertips ≈ −150. Width ≈ 170 (shoulders+arms).
  Head (face oval) ≈ 124 wide × 150 tall; with hair ≈ 150 × 175.
- **Seated** (`seated:true`): origin = where the **desk top meets the body** (centre of the waist line). Nothing of the torso
  below y=0 is drawn. Hair top −308 · head centre −198 · eyes −196 · mouth −161 · chin −136 · shoulders (±58, −92) · chest −52.
  The desk surface is assumed to extend toward the viewer (y > 0): `handsOnDesk` puts the hands at y ≈ +30.
- **Kneel 1** (one knee down, default bodyTurn 0.45 toward `facing`): head centre (29,−368) · eyes −366 · chin −307 ·
  shoulders (−49,−276)/(56,−254) · hip (−24,−136). Front foot planted at x ≈ +84, back knee on the ground at x ≈ −16,
  back toes at x ≈ −124 (all × facing). Footprint ≈ 230 wide.
- Arm: upper 100 + forearm 92 = **192 reach to the wrist**; the hand adds ≈ 48 beyond the wrist.
- Next to **Fear at the same scale**: Fear is 330 tall (≈55%); its head top ≈ −282, its shoulder ≈ (±27..±40, −128..−136).
  Standing SELF's rest hands hang at Fear's eye level; kneeling SELF's eyes are ~145 px above Fear's (looking down gently).

## Pose fields
| field | range / default | meaning |
|---|---|---|
| `t` | seconds (required) | breathing, weight sway, auto-blink, hair-strand sway, tremble noise |
| `outfit` | `'sweater'` (default) \| `'ceo'` | real-world vs CEO look. CEO = blazer, blazer sleeves with a teal sweater cuff, CEO badge, darker trousers |
| `clipboard` | bool | clipboard in **armL**. If `armL` is not given it defaults to `holdClipboard`; with `armL:'rest'` it hangs at the side |
| `face` | expression object | `drawFace` params (`SELF_EXPR.*`, `EXPR.*`, `withSpeech(...)`). Auto-blink added unless `face.noAutoBlink`. Brow params get ×1.3 gain internally (human brows need more travel). `tearL/tearR` drops are drawn by this module at a size that reads on SELF's smaller eyes (with a wet trail) |
| `facing` | 1 \| −1 | mirror the body (face, badge text, notebook art stay readable; light stays upper-left) |
| `view` | `'front'` (default) \| `'back'` | back = back of head/hair (crown whorl), ears, nape, back of sweater/blazer (centre seam + vent). No face — but see `headTurn`. Arms raised to the face (`rubEyes`, `wipeTear`, `coverMouth`, `chinInHand`, …) show from behind as elbows swinging out with the forearms rising beside the head; arms in front of the body below the shoulders are hidden by the torso except what pokes out |
| `headTurn` | −1..1, **screen space** (+ = toward screen right) | head yaw; passed to the face as `turn`; hair parting, ears and jaw follow. Default = `bodyTurn × 0.5` when bodyTurn/walk/kneel is used, else 0. **In `view:'back'`**: 0..0.55 = back of head turning, the ear swings in and a lost-profile cheek/lash/brow appears on that side; ≥ 0.68 = **looking back over the shoulder**: a 3/4 face toward that side with the back of the skull + nape hair showing behind it, head slid ≈15 px toward that shoulder and 5 px down (expressions work). 0.56–0.68 is a short crossfade — move through it in ≤ 4 frames |
| `bodyTurn` | −1..1, **screen space** | 3/4 body: front details (collar, lapels, button, badge) slide, far arm/leg go behind and darken. Default 0, or 0.4×facing when walking, 0.45×kneel×facing when kneeling. For a 3/4 toward the facing side use `bodyTurn: 0.4*facing` |
| `headTilt` | radians (+ = clockwise) | head roll; hair strands lag the opposite way |
| `headDX`, `headDY` | px, local (headDX mirrors with `facing`, as in fear.mjs) | head offset (nods: small `headDY` dips; recoils) |
| `lean` | radians (+ = top toward facing side) | torso lean around the hip (head follows ~45%) |
| `crouch` | 0..1 | hips drop 36 px, slight forward lean; in front view the knees bend toward the camera (foreshortened, no bow-legs); in 3/4 they bend toward the facing side. Cowering, bracing |
| `kneel` | 0..1 | 0 stand → 1 one-knee kneel (front leg = facing side). In between: the front foot steps forward first (0–0.6), then the back leg folds onto its knee (0.1–0.85) while the hips drop. Animate over 0.6–1.0 s with an ease. Not combined with walk |
| `seated` | bool | upper body only (see origin above). Default arms `handsOnDesk` |
| `walk` | `{phase}` radians | walk cycle, one step per π. Phase 0 = contact with leg −1 (armL side) forward, π/2 = passing, π = contact with the other leg. The legs stride side-on under the 3/4 torso (the sweater/blazer hem hides the hip cheat); heel strike, toe-off and a lifted swing foot; hips dip at contact. **Feet stay planted if x advances `WALK_ADVANCE`·scale = 176·scale px per 2π** toward the side the body is turned to (default bodyTurn 0.4×facing → toward `facing`): e.g. `phase = t·2π·0.8`, `x += facing·0.8·176·scale` px/s. Rest arms swing opposite their legs. With `|bodyTurn| < 0.1` the stride goes toward the camera instead (no horizontal advance) |
| `tremble` | 0..1 | whole-body shiver (also shakes both hands) |
| `breathe` | default 1 (0..2) | breathing amplitude; `breathRate` Hz (default 0.2) |
| `shrug` | 0..1 | shoulders up 14 px (tension, sheepishness, hunched at the console) |
| `hairWind` | −1..1 | extra push on the loose hair strands |
| `armL`, `armR` | preset name, `{preset:'name', ...overrides}`, or full spec | see Arms. armL = side −1 (screen-left when facing 1) |
| `notebook` | `{tilt}` radians | tilt of the held notebook (`holdNotebook` / `showNotebook`) |
| `layer` | `'all'` (default) \| `'body'` \| `'front'` | `'body'` = everything except front-layer arms; `'front'` = only front-layer arms (+their props). Use to sandwich another character (hand on Fear's shoulder) |
| `shadow` | default true | ground contact shadow (never drawn when seated or `layer:'front'`) |
| `alpha` | 0..1 | overall opacity (with layered drawing, overlaps double up — avoid fading a split character) |

## Arms
Spec: `{ target:[x,y], bend, front, layer, hand, handAngle, wrist, thumb, prop, board, palm, reach1, reach2, shake }`
- `target` = **wrist** position in local coords (feet origin; desk-line origin when seated). Unreachable targets are clamped.
- `bend` ±1: elbow side. `front:true` → drawn over the head/face. `layer`: `'back'` (behind torso) / `'side'` (over torso, under head) / `'front'`. Default: front if `front`, else `'side'`, or `'back'` for the far arm in a 3/4 turn.
- `hand`: `'open'` (relaxed), `'rest'` (hanging, thumb along the fingers), `'drape'` (laid over something), `'palm'` (spread, palm out), `'flat'`, `'cup'`, `'point'`, `'fist'`, `'grip'`. Hands are simple 4-finger mittens.
- `handAngle` absolute radians in local coords (0 = +x, −π/2 = up); otherwise the hand follows the forearm + `wrist`. `thumb` ±1 flips the thumb side.
- `palm:true` → `target` is where the **palm** lands (wrist pulled back automatically). `reach1/reach2` scale upper arm/forearm (2D foreshortening when pointing at the camera). `shake` 0..1 trembles just that hand (e.g. a hand resting on trembling Fear).
- `prop`: `'clipboard'` (with `board:[dx,dy,rot]` offset from the wrist), `'notebook'` (open, held by both hands), `'notebookCover'` (closed, cover to camera).

Presets (all follow the current pose — lean, kneel, head position and tilt):
| standing | | seated (`seated:true`) | |
|---|---|---|---|
| `rest` | hangs, swings when walking | `handsOnDesk` | forearms forward on the desk |
| `onShoulder` | **give an explicit target** (palm lands there), drape hand | `holdNotebook` | both hands: open notebook in front of the chest (use on armL+armR) |
| `handOnHeart` | flat hand over the heart (wearer's left chest); best on armL (crosses the body). On armR it is the elbow-out "pledge" version | `showNotebook` | both hands: closed notebook upright against the desk edge, **cover art to camera** (opening still) |
| `palmOut` | gentle "wait": elbow low by the body, forearm up and out, palm toward whoever is in front | `chinInHand` | elbow on the desk, chin on the hand (one arm) |
| `reachOut` | reaching forward-down | | |
| `holdClipboard` | clipboard against the waist (armL) | | |
| `pointing` | index finger out to the side | | |
| `rubNeck` | sheepish: elbow up, hand behind the head | | |
| `wipeTear` | elbow tucked in front of the chest, sweater-paw/knuckle under the same-side eye | | |
| `rubEyes` | heels of hands to the eyes (use on both arms; from `view:'back'` the elbows flare out beside the head) | | |
| `clasped` | hands together in front of the belly | | |
| `coverMouth` | flat fingers across the lips (gasp / giggle), elbow tucked | | |
Override any field: `armR: { preset: 'wipeTear', hand: 'open' }`.

## Expressions (`SELF_EXPR`)
`neutral, calm, worried, sternKind` (firm knit brows but open, soft eyes and a level mouth — reads firm-but-caring even
when looking down at Fear), `holdingBackTears, singleTear` (tearR 0.55 — animate `tearR` 0→1 over ~1.2 s for the fall),
`tenderSmile, tired, wonder, sad, smile, laughSoft, surprised, focused` (reading, eyes down), `sheepish, resolve, dread`.
Blend with `S.k(t, [[a, SELF_EXPR.worried], [b, SELF_EXPR.sternKind]])`. Tears: `tears` (welling), `tearL/tearR` (drop + wet trail), `stream`.

## Recipes
**Hand on Fear's shoulder (s07)** — kneel beside Fear, facing it; sandwich Fear between the two layers:
```js
const s = 0.9, sx = 250, gy = 1150, fx = sx + 240 * s; // Fear's feet ≈ 240 local px in front of SELF's feet
const pose = { t, outfit: 'ceo', kneel: k, facing: 1, headTilt: 0.12, face: {...SELF_EXPR.sternKind, lookX: .55, lookY: .55},
  armR: { preset: 'onShoulder', target: selfLocal(sx, gy, s, 1, fx - 38 * s, gy - 132 * s), shake: 0.4 } };
drawSelf(g, sx, gy, s, { ...pose, layer: 'body' });
drawFear(g, fx, gy, s, { t, facing: -1, tremble: .5, ... });
drawSelf(g, sx, gy, s, { ...pose, layer: 'front' });   // hand + arm over Fear
```
Fear's "shoulder" sits under its big head: aim the palm at Fear-local (−34..−40, −128..−134) (mirror x by Fear's facing).
Keep SELF's feet ≈ 230–250 local px from Fear's (same scale) so the arm angles down onto the shoulder instead of poking sideways; SELF's raised front knee then tucks behind Fear.

**Opening still (REAL_ROOM)**: `{ seated:true, outfit:'sweater', armL:'showNotebook', armR:'showNotebook', bodyTurn:-0.2, headTurn:-0.25, headTilt:0.1, face:{...SELF_EXPR.tenderSmile, lookY:0.6} }` — draw the desk first, then SELF at the desk line.

**Back at the console**: `{ view:'back', outfit:'ceo', armL:'rubEyes', armR:'rubEyes', shrug:0.4, headTilt:0.12 }`. Looking back: animate `headTurn` 0 → 0.85 quickly (through 0.56–0.68 in ≤ 4 frames).

**Walking across**: `x = x0 + facing * WALK_ADVANCE * scale * phase / (2π)`, `phase = 2π·0.8·t` (0.8 cycles/s is an unhurried CEO walk).

## Draw order / z notes
- Internal order: back-layer arms → legs → torso → neck → collar/lapels/badge → side-layer arms → head (back hair, ears, face, front hair, strands) → front-layer arms (+ props: notebook/clipboard under the hands).
- Seated: draw the desk **before** SELF; SELF's torso stops exactly at y=0, but arms are not clipped — use the seated presets so hands stay on the desk (y 0..+40). If your desk front edge is higher than +40·scale, draw the desk's front lip after SELF.
- Fear/props between SELF's body and hand: use `layer:'body'` / `'front'` (above).

## Gotchas
- `headTurn`/`bodyTurn` are **screen-space**; `armL/armR` targets and `headDX` are **local** (x mirrors with `facing`). Use `selfLocal()`.
- `@napi-rs/canvas` quirk: after `restore()` the `fillStyle`/`strokeStyle` **getters** still report the inner value, although drawing correctly uses the restored style. Never read a style back to "remember" it; just set styles before you draw (true for every module).
- `@napi-rs/canvas` records commands and rasterises lazily. To time a draw, flush inside the timed region (e.g. `g.getImageData(0,0,1,1)`), or you only measure recording and the real cost shows up later as one multi-second flush.
- Kneel and walk are exclusive (kneel wins). Seated ignores kneel/walk/crouch/shadow.
- The hair, strands and breathing move with `t`; pass the real film time even on held poses or the character freezes.
- Performance (median, including rasterisation, on a busy machine): ≈ 4 ms at scale 0.6, ≈ 7 ms at 1.2, ≈ 8–10 ms at 1.8 or a face close-up — about 2× Fear at the same screen size. Fine for the 40 ms frame budget, but avoid several large SELFs in one frame.
