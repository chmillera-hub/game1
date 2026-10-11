# THE VOID + THE COSMOS — API for scene animators

Files: `src/chars/void.mjs` (the character), `src/fx/cosmos.mjs` (the universe in its face).
Sheets: `node tools/sheet_void.mjs` → `out/sheet_void.png`, `out/sheet_cosmos.png` (+ timings on stdout).

```js
import { drawVoid, drawVoidShadow, drawVoidGlow, drawVoidArm, drawVoidHand, voidRig, toVoidLocal,
         VOID_HANDS, VOID_POSES, ANCHORS, HEIGHT } from '../chars/void.mjs';
import { drawCosmos, drawCosmosGlyph, preloadCosmos, COSMOS_GLYPHS } from '../fx/cosmos.mjs';
```

## 1. Coordinates and sizes

`drawVoid(g, x, y, scale, pose)`: `(x, y)` = world point of the **hem centre on the floor**.
Local coords: origin at that point, **y negative = up**, scale 1 units.

| thing (scale 1) | local value |
|---|---|
| `HEIGHT` (floor → hood peak) | **1700** (peak + rim reach y ≈ -1715) |
| face opening centre (`ANCHORS.face`) | (0, -1508), half-size `faceRx` 80 × `faceRy` 112 |
| shoulders (`shoulderL/R`) | (∓222, -1292) |
| sleeves at rest: cuffs (`handRestL/R`) | (∓262, -560); cuff opening ~176 wide |
| hem on floor (`hemL/R`), pooled front | x ±452 at y 0; the pool bulges to y ≈ +32 toward camera |
| widest silhouette (`ANCHORS.width`) | ~900 (hem pool); the mantle (cape over the shoulders) is ~620 wide, the sleeves emerge from under it |
| hand: wrist → middle fingertip (`handLength`) | 196 (palm centre is 52 from the wrist) |
| max shoulder → palm reach (`ANCHORS.reach`) | 1222 (sleeves telescope / stretch up to 30%) |

Scale guide: wide shots `scale` 0.45–0.6 (765–1020 px tall: 60–80% of the 1280 frame). At **0.55** the Void
is 935 px tall, its hand ~108 px long, next to Fear at scale 1.0 (330 px) — see the sheet. `facing` is not
supported (the figure is symmetric; aim it with `headTurn`).

`toVoidLocal(x, y, scale, wx, wy)` converts any world point to Void-local (use it for hand targets).
`voidRig(pose)` returns live local anchors for a pose (scale 1 units, add `x/y` × `scale` for world):
`{ face:[x,y], faceRx, faceRy, shoulderL, shoulderR, handL/handR: { wrist, palm, tip, angle }, turn, down, lean }`.
Face centre by pose: still (0,-1508); `distance` (-9,-1505); `turnLeft` (-55,-1495) rx 56; `headTurn:-1`
(-72,-1508) rx 48; `lookDownRight` (39,-1397) ry 83; `headDown:1` (0,-1380). Use `voidRig(pose).face` to aim
cameras / place close-ups exactly. The shoulder joints never move (a bow only settles the mantle).

## 2. Pose fields (`drawVoid`)

| field | range (default) | meaning |
|---|---|---|
| `t` | seconds | idle life: rim shimmer, a slow glint travelling down the cloak edges (~every 30 s), a barely perceptible hem drift (±3 units at the floor), shadow breathing, cosmos drift. The Void never breathes or sways — stillness is its character. |
| `idle` | 0..1 (1) | scales ALL idle motion of the cloak: hem drift, rim shimmer, the travelling glint, shadow breathing. **`idle: 0` = perfectly frozen** — use it for the screenplay's "not one fold moves / rim light steady" beats (scenes 2, 10, 11). The cosmos keeps its own motion (`cosmosOpts.drift`). |
| `headTurn` | -1..1 (0) | hood yaw. **+ = looks toward screen-right (+x)**, − = screen-left. 0 = facing camera / staring into the distance. The opening slides ±72 toward its side edge and narrows (±1 ≈ near profile); the far inner hood wall shows, and the rim light migrates to the BACK edge of the hood (the face side dims) — exactly the screenplay's THE TURN. Animate it slowly; each 1/64 step builds one hood sprite. |
| `headDown` | 0..1 (0) | hood bows to look at someone small at its feet: face drops ~128, foreshortens; the mantle settles 36 (the shoulder joints/arms do not move). "Ten degrees down" ≈ 0.15. |
| `headTilt` | radians (0) | extra hood roll. (A turn+bow already adds `turn*down*0.12`.) |
| `lean` | radians (0) | whole-body lean, pivot at the hem centre. Keep within ±0.06. Hand targets stay world-aligned. |
| `cosmos` | 0..1 (0) | **0 = pure darkness (no eyes, ever)**; ~0.3 a few stars kindle; 0.6 nebulae; 1 = full universe with galaxies and glyphs. |
| `cosmosOpts` | `{ glyphs, seed, drift }` | passed to `drawCosmos` (see §6). |
| `rim` | 0..1 (1) | violet/cyan rim-light strength (silhouette readability against dark rooms). |
| `silhouette` | bool | cloak nearly invisible; only the rim light + face read. No floor shadow. |
| `alpha` | 0..1 (1) | overall opacity; drawn through an offscreen layer so overlaps don't show (+~1–2 ms). `layer:false` skips the layer (cheaper; overlapping parts then show through each other). |
| `shadow` | bool (true) | `false` = skip the floor shadow (draw `drawVoidShadow` yourself earlier). |
| `shadowSpread` | 0..1 (0.3) | 0 = contact shadow under the pooled hem; 1 = dark shadow spilling across the floor toward the viewer (~3400 × 900 local). |
| `handR`, `handL` | object | see §3. `handR` = **screen-right** hand (+x), same convention as Fear's `armR`. |
| `foldStar` | 0..1 (0) | "a single faint star glints in a fold of the cloth" (scene 17): a tiny slow-twinkling star on a fold near the hem, local (-127, -236). |
| `cache` | bool (true) | `false` = fully live vector drawing (debug / comparison only; ~3× slower; no hem drift). |

Head presets (`VOID_POSES`, spread into the pose): `still`, `distance` (turn -0.12: staring off at the
screen of consciousness), `turnRight` / `turnLeft` (±0.75, down 0.1), `lookDownRight` / `lookDownLeft`
(turn ±0.5, down 0.85: looking at Fear at its feet).

## 3. Hands (`handR` / `handL`)

Hands are hidden inside the long sleeves until used. Fields:

| field | range (default) | meaning |
|---|---|---|
| `show` | 0..1 (0) | hand emerges from inside the sleeve (0 hidden, 1 fully out). |
| `target` | [x,y] local | where the **palm centre** goes — or the **fingertip** if `tip:true` (middle fingertip, sliding to the index fingertip as `point` → 1). Omit = arm hangs at rest. Contact is exact (the sleeve telescopes; beyond `ANCHORS.reach` it stops short; targets very close to the shoulder bunch the sleeve up). |
| `reach` | 0..1 (1) | blend the arm from rest toward `target` (animate this for the reach). |
| `tip` | bool | target refers to a fingertip (used by `shoulder`, `unlock`, `push`, `point`). |
| `open` | 0..1 (0.15) | relaxed → fingers spread. |
| `point` | 0..1 (0) | index finger extends, the other fingers fold under the palm, thumb tucks (continuous — animate it as the hand arrives at a lock). |
| `gentle` | 0..1 (0.2) | palm softly curved / fingers curl (resting on a shoulder). |
| `angle` | radians | hand direction (0 = fingers point +x, π/2 = down). Default: shoulder→target direction blended 30% toward down (less as `point` → 1). |
| `curl` | ±1 | side the fingers curl toward (default: whichever side faces down, so they drape). |
| `bend` / `elbow` | ±1 / 0..1 | elbow side (default outward) / how bent (default 0.3 while reaching, 0 at rest). |
| `front` | bool (true) | `false` = arm drawn behind the cloak. |
| `defer` | `true` \| `'hand'` | `true`: `drawVoid` skips the whole arm (draw later with `drawVoidArm`); `'hand'`: draws the sleeve but not the hand (draw later with `drawVoidHand`). |

Presets (`VOID_HANDS`, all return a hand object — spread and override):
- `shoulder(target, side=1)` — the hand comes in from the side under Fear's big head and the fingertips curl
  over the shoulder/scarf. `side` +1 when the touched character stands to the Void's screen-right.
  **Target = the shoulder** (middle-fingertip contact). Draw the hand ON TOP of Fear (`defer:'hand'`).
- `unlock(target)` — "one fingertip, very gently, turns the tiny lock": index finger extended (`point:1`),
  **index fingertip exactly on the latch**. The arm is in front of the cage: `defer:true` + `drawVoidArm` after
  the cage (see §4). The hand naturally points down-and-toward the lock (it enters from above).
- `push(target, side=1)` — "two enormous fingertips nudge between the shoulder blades; the hand stays open
  behind Fear": fingertips (`tip:true`) on the character's back edge, fingers pointing in the push direction;
  `side` +1 pushes toward screen-right. **Draw the hand BEHIND Fear** (plain `drawVoid` before `drawFear`, no
  defer) so the fingertips meet its back. Nudge: move `target` ~6–10 local units in the push direction and
  back over ~1 s, then hold.
- `offer(target, side=1)` — open, softly curved hand held out to the side, fingers forward.
- `point(target)` — index finger extended, fingertip at `target` (keep it within reach; aim far for a gesture).
- `out()` — hand out at rest, hanging. `hidden()`.

Fear targets (Fear at world `(fx, fy)`, scale `fs`): near shoulder ≈ `(fx ∓ 34·fs, fy − 114·fs)`
(− when the Void is to Fear's left); Fear's back for a push ≈ `(fx − 34·fs, fy − 112·fs)` (Fear walking right).
Convert with `toVoidLocal(vx, vy, vs, wx, wy)`. Cage latch at ~200–400 local above the floor is in easy reach.

Recipe — reaching to Fear's shoulder:
```js
const tgt = toVoidLocal(vx, vy, vs, fx - 34 * fs, fy - 114 * fs);
const handR = { ...VOID_HANDS.shoulder(tgt, 1),
  show: S.k(t, [['s16b01', 0], ['s16b01+0.8', 1]]),           // emerges first
  reach: S.k(t, [['s16b01+0.3', 0], ['s16b01+2.2', 1, 'inOut']]), // slow, gentle travel
  defer: 'hand' };                                                 // hand goes on top of Fear
const pose = { t, ...VOID_POSES.lookDownRight, cosmos, handR };
drawVoid(g, vx, vy, vs, pose);
drawFear(g, fx, fy, fs, fearPose);
drawVoidGlow(g, vx, vy, vs, pose);   // optional, when cosmos > 0
drawVoidHand(g, vx, vy, vs, pose, 'R');
```
Lifting the hand away: reverse `reach` 1→0 (~1.5 s), then `show` 1→0.

Recipe — the unlock (arm in front of the cage):
```js
const latch = toVoidLocal(vx, vy, vs, lockX, lockY);
const pose = { t, ...VOID_POSES.distance, idle: 0,                    // the hood never moves
  handL: { ...VOID_HANDS.unlock(latch), show, reach, point: S.k(t, [...0→1 as it arrives]), defer: true } };
drawVoid(g, vx, vy, vs, pose);  drawCage(...);  drawVoidArm(g, vx, vy, vs, pose, 'L');
```

## 4. Z-order

1. set / floor → 2. `drawVoidShadow` (only if other things stand on the shadow and you passed `shadow:false`)
→ 3. `drawVoid` → 4. characters/props in front (Fear, cage) → 5. `drawVoidGlow` (light on them)
→ 6. deferred `drawVoidHand` / `drawVoidArm` → 7. foreground, vignette.
- Hand ON a character in front (shoulder): `defer:'hand'` + `drawVoidHand` after the character (sleeve stays behind).
- Hand BEHIND a character (push on the back): no defer; draw the character after `drawVoid`.
- Whole arm in front of a prop (e.g. reaching past the cage bars): `defer:true` + `drawVoidArm(g,x,y,s,pose,'L')` after the prop.
- `drawVoidArm(..., part)`: `'all'` (default) | `'sleeve'` | `'hand'`.

## 5. Light and shadow

- `drawVoidGlow(g, x, y, scale, pose)` — only draws when `pose.cosmos > 0`. Screen-blended violet→teal light:
  a cone falling from the face toward where it looks (stronger as it bows: `headDown`) + a pool on the floor
  toward `headTurn`. It never washes out the face. `pose.glow` multiplies intensity (0..2);
  `pose.glowExcludeHood` adds a clip so even the hood shell stays unlit (+~2 ms).
- `drawVoidShadow(g, x, y, scale, { t, shadowSpread })` — the floor shadow alone (baked soft sprite).

## 6. The cosmos

`drawCosmos(g, cx, cy, rx, ry, t, opts)` fills the rect `cx±rx, cy±ry` (current transform):

| opt | range (default) | meaning |
|---|---|---|
| `reveal` | 0..1 (1) | 0 abyss → a single first star (0.02–0.09, just off-centre) → stars kindle **from the centre outward** (0.05–0.62) → nebulae bloom (0.2–0.8) → galaxies (0.5–0.95) → glyphs (0.6–1). ~0.1 in the hood = "a single star twinkles"; 0.3 = "a few stars kindle". |
| `glyphs` | 0..1 (1) | visibility of the drifting "bits and pieces of meaning". |
| `seed` | int (7) | star layout / drift phases. |
| `drift` | (1) | speed multiplier for parallax drift, galaxy spin, glyph float. |
| `clip` | `'rect'` \| `'ellipse'` \| `'none'` | clip to the rect (default), an ellipse, or nothing (caller clipped). |
| `bg` | bool (true) | deep-space background; `false` = transparent overlay (lighter blend). |
| `alpha` | 0..1 | overall opacity. |

- Full-screen close-up: `drawCosmos(g, 360, 640, 380, 660, t, { reveal })` (slightly larger than the frame).
- Content scales with `min(rx, ry)`; positions are normalized to the rect, so a hood-sized and a full-screen
  cosmos share the same composition (galaxies upper-left / right, heart near centre, tiny Fear lower-left).
- Glyphs (`COSMOS_GLYPHS`): heart, sun, fear (tiny lavender Fear), note, house, handprint, speech, key,
  notebook, leaf, pencil — ~50–80 px tall at full screen. Small cosmos shows the first 5. `drawCosmosGlyph(g, name, x, y, size, color, {alpha, rot})`
  draws one (baked glowing sprite; `vector:true` for live strokes) — e.g. to float a glyph out of the face.
- Motion is slow and compression-friendly: parallax ≤ 3 px/s at full screen, small twinkles, no flicker.
- `preloadCosmos()` builds textures (~0.2 s) — call once at startup to keep the first frame fast.
- Suggested beats: hood `cosmos` 0 → 0.3 over ~2 s ("a few stars kindle"), hold, 0.3 → 1 over 4–6 s
  (`ease inOut`). For the reveal close-up either push the camera into the hood (`voidRig(pose).face`)
  or dissolve to a full-screen `drawCosmos` with the same `reveal`.

## 7. Performance (rasterized, 720×1280, medians; Fear ≈ 2 ms for reference)

| case | ms |
|---|---|
| Void 0.55 dark / cosmos 1 | ~5 / ~5.6 |
| Void 0.55 cosmos 1 + one moving hand + glow | ~10.6 |
| Void 1.0 (towering, cropped) cosmos 1 | ~4.5 |
| hood close-up (scale 2.3) cosmos 1 | ~15 |
| face fills frame (scale 4.5) cosmos 1 | ~21 (nothing else on screen) |
| hood push-in (scale 4) darkness | ~11 |
| animated head turn, per frame (incl. one hood build) | ~6 @0.55 · ~7 @1.0 · ~24 @2.3 |
| `alpha` 0.6 (layer) | ~6.5 |
| `drawVoidGlow` | ~2.5 |
| `drawCosmos` full screen reveal 1 / 0.4 | ~9 / ~7 |

Caches: the cloak body (+ resting sleeves) is one sprite keyed by quantized on-screen scale; the mantle is one
sprite per scale (a bow only translates it); the hood shell is one sprite per scale + quantized head pose
(1/64 turn/bow steps). The face (abyss/cosmos), moving arms, hands, glint/shimmer and hem drift are live.
A new head pose builds one hood sprite (~2 ms at 0.55, ~4 ms at 1, ~16 ms at 2.3 — included in the turn
row above); a new scale costs 5–30 ms once (camera push-ins step through ~12 scale buckets per doubling).
Timings vary ±3 ms with machine load (`node tools/sheet_void.mjs` prints them).

## 8. Gotchas

- `target` = **palm centre** unless `tip:true` (the `shoulder`, `unlock`, `push`, `point` presets use fingertips).
- `headTurn` + = screen-right; `handR` = screen-right hand.
- The face is darkness unless `cosmos > 0`; there are no eyes or expressions — act with stillness, head turns,
  bows, hands and the cosmos.
- `alpha < 1` uses an offscreen layer the size of the target canvas (`layer:false` to skip it); `silhouette`
  skips the floor shadow.
- Stillness is the performance: for "nothing moves" beats pass `idle: 0` (and keep `cosmos` 0). Default
  `idle: 1` gives only barely perceptible hem drift + rim shimmer + a glint every ~30 s.
- Hand presets are tuned for the Void standing to the LEFT of Fear (`side` +1, `handR`). Mirror with `side` -1
  and `handL` when it stands to the right.
- Determinism: `engine.mjs` `rand()` / `noise1()` / `fbm()` currently return constants for most inputs
  (float precision overflow in its hash), so these modules use their own integer-safe `hrand`, `vnoise`,
  `vfbm` (exported from `fx/cosmos.mjs`) — feel free to use them for your own jitter.
