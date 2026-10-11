# Emotions — JOY, SADNESS, ANGER, CALM (`src/chars/emotions.mjs`)

These are the four "other emotions" who work the console. They are drawn in the same family as FEAR (same line
weight, head shading, face rig, knobbly legs, mitten hands). Each has one silhouette tuft and one accessory:

| name | colour | design | tuft | accessory |
|---|---|---|---|---|
| JOY | gold `#ffc94a` | round head, gumdrop body | star-shaped cowlick | orange sunflower-petal collar |
| SADNESS | blue `#6fa8e8` | soft, rounded, wider at the bottom | droopy lock ending in a raindrop | indigo cardigan with oversized cuffs ("sweater paws") |
| ANGER | coral `#f0634f` | flat-top square head, stocky | tiny curl of heat (grows and steams with `heat`) | slate denim overalls |
| CALM | mint `#7fd6b0` | tall egg-shaped head, slim | two-leaf sprout | teal shawl draped over the shoulders |

Sheet: `node tools/sheet_emotions.mjs [--extra]` writes `out/sheet_emotions.png`, plus `out/sheet_emotions_poses.png`
when you pass `--extra`.

```js
import { drawEmotion, EMOTION_ANCHORS, EMOTION_ARMS, EMOTION_EXPR, LOOKBACK_SMILE, PANIC_FACE,
         EMOTION_HEIGHTS, EMOTION_FACES, EMOTION_COLORS, EMOTION_NAMES } from '../chars/emotions.mjs';
drawEmotion(g, 'JOY', x, y, scale, { t, view: 'back', lookBack: k, face: LOOKBACK_SMILE, armL: 'pressButton', armR: 'pressButton' });
```

## Signature

`drawEmotion(g, name, x, y, scale = 1, pose = {})`
- `name` is one of `'JOY' | 'SADNESS' | 'ANGER' | 'CALM'`. Any other value throws.
- `(x, y)` is the world point on the ground between the feet. `scale` 1 gives the heights below.
- The function does its own `save`/`restore`, so it never leaks transform, alpha, composite, filter or shadow. It also
  puts back `fillStyle`/`strokeStyle` itself, because @napi-rs/canvas's `restore()` does not restore them. (drawFear
  *does* leak them, so after Fear set your styles before you fill.)
- It is deterministic in `pose.t`. Measured cost per call, rasterised (`node tools/sheet_emotions.mjs` prints it):
  front about 3–4.7 ms at scale 1; back view with `lookBack` about 4.5–5 ms at scale 1 and about 3.4 ms at the HQ
  console scale (0.54). The look-back face needs two `drawFace` passes. Four emotions plus Fear come to roughly
  15–22 ms.

## Sizes at scale 1 (local coords: origin = feet, +x = screen right at facing 1, y negative = up)

| | JOY | SADNESS | ANGER | CALM |
|---|---|---|---|---|
| `EMOTION_HEIGHTS` (silhouette top) | 457 | 419 | 394 (taller with heat) | 523 |
| silhouette half-width at rest | 88 | 100 | 94 | 70 |
| head centre y | −304 | −314 | −280 | −390 |
| head rx / ry | 84 / 80 | 90 / 80 | 90 / 70 | 66 / 76 |
| face centre y | −294 | −302 | −272 | −378 |
| eyes (±x, y) | ±36, −300 | ±37, −304 | ±38, −274 | ±29, −382 |
| mouth y | −254 | −260 | −234 | −343 |
| neck y | −232 | −240 | −216 | −314 |
| shoulders (±x, y) | ±34, −213 | ±42, −222 | ±50, −199 | ±30, −280 |
| hip y | −112 | −92 | −92 | −156 |
| body half-width | 55 | 72 | 62 | 40 |
| arm reach (L1+L2) | 106 | 100 | 98 | 128 |
| pressFront hand (±x, y) | ±42, −147 | ±50, −160 | ±58, −138 | ±38, −201 |
| pressBack hand (±x, y) | ±55, −201 | ±72, −206 | ±62, −186 | ±40, −265 |

For reference, FEAR is about 330 tall and CONSCIOUSNESS about 600. All of these values are also exported as
`EMOTION_ANCHORS[name]`: `height, headCenter, headTop, headRx, headRy, faceCenter, eyeL, eyeR, mouth, neck, shoulderL,
shoulderR, hipY, bodyHalfWidth, armReach, pressFrontL/R, pressBackL/R`, plus `shoulderTouch` (where another
character's hand rests on the right shoulder; mirror x for the left).
To convert a local point to world coordinates: `wx = x + lx * scale * facing`, `wy = y + ly * scale`. Anchors are rest
values. Crouch moves the upper body down by `crouch × (30 | 26 | 24 | 32)` for JOY/SADNESS/ANGER/CALM.

## Pose fields

| field | range | meaning |
|---|---|---|
| `t` | seconds | Drives idle life: breathing, tuft sway, auto-blink, wave/flail motion, steam. Always pass it. |
| `view` | `'front'` \| `'back'` | `'back'` means seen from behind (at the console). There is no face unless `lookBack` > 0. |
| `lookBack` | 0..1 | **Back view only.** Turns the head over the shoulder toward the camera. At 0 you see the back of the head. The features come round the head like on a turning sphere: around 0.3–0.5 a narrow, foreshortened eye slides in from the silhouette edge and fades in. By 0.7 the eye, brow and mouth corner show. At 1 you get a 3/4 face: one eye with its brow, a near-cheek blush, a smile set well inside the head, and the smiling far cheek gently pushing the outline. The far eye stays just hidden. The head also tilts a little and the body leans about 1.7°. Any value reads, so you can hold mid-turn. |
| `lookSide` | +1 \| −1 | Which side the face appears on, in **screen space**, independent of `facing`. The default is +1 (screen right). Point it toward whoever they are looking at. |
| `face` | expr object | A `drawFace` expression (EXPR presets work; see face.mjs). The emotion's small **base expression is added** (see below). Auto-blinks unless `face.noAutoBlink`. In lookBack, `face.lookX` is **relative to looking straight at the camera**. |
| `noBase` | bool | Turns off the additive base expression. |
| `facing` | 1 \| −1 | Mirrors the body (arms, tufts, accessories). The face stays readable. |
| `headTurn` | −1..1 | Yaw in screen space. +1 turns toward screen right and is passed to the face as `turn`. In back view it only drifts the tuft. |
| `headTilt` | rad | Head roll (body-local: it mirrors with `facing`). About ±0.1 reads well. |
| `headDX`, `headDY` | px | Head offset for nods, recoils and swallows (`headDY` +3..6). |
| `lean` | rad | Whole upper body pivots about the feet. Keep it to ±0.08. |
| `crouch` | 0..1 | Cower or squash: knees bend out and the upper body drops. Preset hands follow. |
| `tremble` | 0..1 | Body shiver, hand jitter and a faster blink rate. |
| `breathe` | 0..2 | Breath amplitude, default 1. `breathRate` (Hz) overrides each character's own rate (JOY 0.32, SAD 0.22, ANGER 0.36, CALM 0.2). |
| `armL`, `armR` | see below | `armL` is the arm on screen-left at facing 1, **in both views**. |
| `walk` | `{ phase }` | Walk cycle: advance `phase` by about `t × 2π × 1.1`. Legs swing and the body bobs. Move `x` yourself. |
| `heat` | 0..1 | ANGER only, default 0.2. The heat curl grows and wiggles faster. Above 0.35 small steam curls rise, and above 0.75 there are three. At 1 the top of the silhouette, steam included, is about 430 instead of 394. |
| `shadow` | bool | Set it to `false` to skip the ground shadow (radius 76/86/84/62 px). |
| `alpha` | 0..1 | Multiplies the current globalAlpha. |

### Base expressions (added to `face`, then clamped to [−1, 1])
These are part of each character's personality at rest:
- JOY `{browUp:.1, smile:.22, lidL:.1}`
- SADNESS `{lidTilt:.25, browIn:.3, smile:−.04}`
- ANGER `{browIn:−.3, browSquish:.2}`
- CALM `{smile:.15}`

The face *styles* also differ: CALM rests half-lidded (`restLid .4`, almond eyes), SADNESS has heavy soft lids
(`restLid .2`), and ANGER has 10 px brows. Use `noBase: true` if a beat needs an exact face, for example an
un-grumpy ANGER.

### Expression exports
- `EMOTION_EXPR[name]` is each emotion's characteristic face: JOY beaming, SADNESS teary droop, ANGER grumpy
  pressed lips, CALM serene smile.
- `LOOKBACK_SMILE` is `{smile:.85, open:.16, teeth:.5, lidL:.42, browUp:.2, blush:.35}`, a warm brief smile
  that stays readable on a small 3/4 face. Drop `open`/`teeth` for a closed smile.
- `PANIC_FACE` is the alarm face (wide eyes, small pupils, open grimace, trembling lips).
- `EMOTION_FACES[name]` is the face style object passed to `drawFace`. `EMOTION_COLORS[name]` is the palette.
- Lip-sync works the same as Fear: `face: withSpeech(expr, S.lip('JOY', t))`.

## Arms

`armL` / `armR` accept any of the following:
1. A **preset name**: `'pressButton'`.
2. A **preset with tweaks**: `{ preset:'pressButton', dx, dy, atY, hand, bend, layer, fore, boneK, handAng }`.
   - `dx` moves the hand **outward** (positive = away from the body's centre line, on both sides).
   - `dy` moves it down in px (positive = down). Use it for taps: animate `dy` 0 → 7 → 0 over about 0.25 s.
   - `atY` sets the hand's local y absolutely, for example to put the hand exactly on your console's top surface.
     For front-view `pressButton`, raising the hands with `atY` also spreads them outward by half the lift so they
     clear the face. Above the shoulder, the hand turns fingertip-down onto the edge.
3. A **raw IK target**: `{ target:[x, y], bend, hand, layer | front, fore, boneK, handAng }`, where `[x, y]` is in
   local coordinates. Raw targets do not follow crouch or breathing; preset targets do.

Other fields:
- `bend` (±1) chooses the elbow side. For both arms, `bend = side` puts the elbow outward/down when the hand is below
  the shoulder, and `bend = −side` does the same when the hand is above it.
- `hand` is one of `'open'` (three-finger mitten, the default), `'palm'` (flat open palm), `'fist'`, `'grip'` or
  `'point'` (index finger along the forearm).
- `handAng` is an absolute hand angle in radians in local coordinates; `−π/2` points the fingers up.
- `fore` (0..1) foreshortens the bones for arms pointing into depth, toward or away from the camera.
- `boneK: [upper, lower]` sets explicit bone-length multipliers and overrides `fore`. For example, back-view
  `pressButton` uses `[0.95, 0.45]`: a forearm pointing straight away from the camera.
- `layer` controls draw order:
  - `'back'` (the default): behind the body in both views.
  - `'front'` (or `front:true`): over the chest in front view, drawn after the head. In back view it is behind the
    body, which hides it.
  - `'over'`: on top of everything in both views.

Presets (`EMOTION_ARMS[name][preset](side, view, t)` returns the resolved object). Targets are given for the right arm
of JOY at scale 1:

| preset | JOY R target | layer | hand | notes |
|---|---|---|---|---|
| `rest` | 64, −119 | back | open | Hangs just outside the body, elbow slightly out. |
| `pressButton` (front) | 42, −147 | front | point | Down and forward onto a console in front of them, elbows out. `fore` .8. |
| `pressButton` (back) | 55, −201 | front (behind body) | open | Forward onto a console beyond them. From behind, the elbow drops just outside the torso and the foreshortened forearm (`boneK [.95, .45]`) rises to the hand. The hand shows beside the collar, fingers pointing away from the camera (`handAng −π/2 ± .25`). |
| `coverEars` | 90, −270 | over | palm | Palms on the sides of the head, fingers up. Pair with `PANIC_FACE`, `tremble`, `crouch` .3. |
| `wave` | 87, −291 | back | palm | Oscillates by itself at 1.4 Hz from `t`. |
| `flail` | 121, −294 (moving) | back | open | Panic arms driven by noise at about 4–5 Hz. Use it on both arms. |
| `handsOnHips` | 57, −142 | over | fist | Elbows out. Reads in both views. |
| `hugSelf` | −20, −181 | front | open | Crosses to the opposite side of the chest. Use it on both arms. |
| `pointing` | 137, −228 | back | point | Straight out to the side at shoulder height. |
| `cheer` | 79, −308 | back | fist | Arm raised, with a slight bounce. |
| `wipeEye` | 40, −292 | front | fist | Knuckle at the eye on the same side. Reduce `face.tears` while it is up. |
| `clasp` | 6, −168 | front | fist | Hands together in front of the chest. Use it on both arms. |

Unknown preset names fall back to `rest`.

## Draw order and staging

Draw order inside the character, front view: shadow, legs, back-layer arms, body and accessory, tuft (behind or over
the head), head, face, neckwear, then front and over arms.

In back view: shadow, legs (heels first), back and front arms, body back, head (back, or the look-back 3/4 face),
neckwear, then over arms.

**Console, front view** (they face camera behind the console): draw the emotion **first** and the console after it as a
foreground layer. For a generic console, put its top edge about 20 px (local) **below** the `pressFront` wrist, so the
fist shows and the pointing fingertip dips behind the edge: world `consoleTopY ≈ y + (pressFrontY + 20) * scale`. If
the console top is higher or lower than this, set `atY = (consoleTopY − y) / scale − 20` for the arm.

*With the real HQ set* (`drawHQ(g,'front')`, characters at `HQ_VIEWS.front.anchors.consoleSlot1..4`, scale ≈ 0.8):
`drawHQForeground` puts the console top at about local y **−246**, above every emotion's shoulders except CALM's. Only
the heads show, and the default `pressFront` hands are hidden behind the panel. That reads fine: animate small `dy`
taps and the shoulders move. If you want hands visible on the edge, use `atY: -266`. The hands then spread outward
past the head and rest fingertip-down on the rim. CALM at slot 4 is half off-frame in the `console` cam.

**Console, back view** (they face the Screen of Consciousness): draw the console **first**, behind them, then the
emotions. The default hands show beside the collar at `pressBack` y, with the elbows dropping outside the torso. Place
the console's front panel or deck so that it sits around that y on screen, or move the hands with `atY`.
*With the real HQ set* (`drawHQ(g,'back')`, characters at `HQ_VIEWS.back.anchors.consoleBack1..4`, scale ≈ 0.54, cam
`console`), the default hands land on the console's front panel, which reads well. HQ's `button1..4` anchors sit at
about local y −325, behind the heads. To reach one, use a raw target there; the hand is hidden by the head.

**Story beat: they look back at Fear, smile, then return to work.** Use `view:'back'`, arms on `pressButton`, and set
`lookSide` toward Fear. Key `lookBack` as `0 → 1` over 0.45–0.6 s (`ease.cubic`). Lead with the eyes: blend the face
from neutral to `LOOKBACK_SMILE` starting about 0.2 s after the turn begins (`mix({}, LOOKBACK_SMILE, k)` works). Hold
for 1.0–1.5 s with a blink, then return `lookBack` `1 → 0` over about 0.6 s and resume `dy` taps. Stagger the four
emotions by 0.15–0.3 s so they don't move in unison. At the HQ back-view `console` cam the one-eye smile reads clearly.
In the `wide` cam the faces are small, so push in or cut closer for the smile.

Shoulder-touch, comforting or hugging contacts: use `EMOTION_ANCHORS[name].shoulderTouch` × scale.

## Gotchas
- `lookBack` does nothing in front view. In front view, turn the head with `headTurn` (up to about ±0.7).
- The look-back face is drawn with `drawFace` in two passes, one for the near eye and brow and one for the mouth,
  placed on the measured head silhouette. All expression fields still work, including lip-sync, tears, blush and
  blinks. `browUpL/R` keep their screen-side meaning. The rig's `sweat` drop and `turn` are not used in look-back.
- In lookBack, `face.lookX` is an offset from "looking at the camera". The default already aims the iris toward the
  viewer. To look at Fear standing off-camera, nudge it by ±0.2–0.4.
- On ANGER's square head the cheek push is halved, so the 3/4 face reads a little flatter than on the round heads.
- In back view, tufts are mirrored so they stay on the same side anatomically. For example, SADNESS's raindrop lock
  hangs screen-right from the front and screen-left from behind.
- `armL`/`armR` are always the screen-left and screen-right arms at `facing 1`, in both views. They swap sides with
  `facing:-1`.
- `headTurn` is screen space. `headTilt` and `lean` are body-local, so they mirror with `facing`.
- SADNESS's arms are always cardigan sleeves; only the fingertips poke out of the cuff. `palm` and `point` still
  read correctly.
- ANGER's `heat` above 0.5 makes its silhouette taller by up to about 15 px, and the steam curls rise about 80 px
  above the head. Leave headroom in tight close-ups.
- CALM is the tallest (523). In a lineup at the console, put CALM at the edge or furthest back so it doesn't hide
  the Screen.
- Faces read at phone size down to about scale 0.5. For the look-back smile, aim for scale 0.6 or more, or push in.
- Keep a single `t` per character, offset by a few seconds (for example `t + 3.7`) so the blinks and breaths of
  side-by-side emotions don't sync. Each character's seeds already differ.
