# Props + REAL_ROOM — API reference for scene animators

Files: `src/sets/props.mjs` (cage, notebook, desk lamp), `src/sets/realroom.mjs` (the real-world room).
Sheet: `node tools/sheet_props.mjs [out.png] [--time] [--placeholder]` → `out/sheet_props.png`
(`--placeholder` swaps the real SELF for a silhouette).
All functions are deterministic in `state.t`, `save()/restore()` internally, and leak no transform/alpha/composite.
Cached bitmaps are built only from quantised parameters, so a frame renders bit-identically whatever was rendered
before it (safe for out-of-order / parallel rendering).
Coordinates: px at scale 1, x right, y **down**. Fonts self-register on import (Caveat, Patrick Hand, Fraunces).

```js
import { drawCage, CAGE_ANCHORS, CAGE_PRESETS, CAGE_SIZE, cagePoint,
         drawNotebook, NOTEBOOK_SIZE, NOTEBOOK_PALETTES,
         drawDeskLamp, LAMP_ANCHORS, hrand, vnoise, vfbm } from '../sets/props.mjs';
import { drawRealRoom, drawRealRoomForeground, drawLitByRoom, REALROOM } from '../sets/realroom.mjs';
```

---------------------------------------------------------------------------------------------------
## 1. The TIME-OUT cage — `drawCage(g, x, y, scale, state)`

A gunmetal birdcage: riveted plinth, 13 bars + a domed top with a hanging loop, a front door (hinged on the
LEFT jamb, padlock on the RIGHT jamb), and a wooden "TIME-OUT" sign (Patrick Hand) hanging from the top loop
in front of the dome. Sized for Fear at the **same scale** (Fear 330 tall ↔ interior 428 tall at centre).

**Origin (x, y)** = centre of the cage footprint ON THE GROUND (like a character's feet point).
The plinth's front lip appears 36 px *below* the origin (perspective), the loop top 480 px above.

| size at scale 1 (`CAGE_SIZE`) | value |
|---|---|
| overall width (plinth) | 356 (bars 330) |
| visual height | ≈ 516 (y −480 … +36) |
| interior height / width | 428 / ≈310 |
| cage floor (where occupants stand) | y = −20 (centre) |
| door at `door:1` swings out to | x ≈ −211 (left of origin; mirrored with flip) |

### state

| field | range | meaning |
|---|---|---|
| `layer` | `'back'` \| `'front'` \| `'all'` (default) | `'back'` = ground shadow, plinth, floor, back bars, back dome — draw BEFORE the occupant. `'front'` = front bars, front dome, rings, finial, hinges, door, padlock, grip-fingers, sign, rust flakes — draw AFTER the occupant. |
| `t` | seconds | drives rattle, sign sway, padlock swing |
| `door` | 0..1 | 0 closed; swings outward on the left hinges; ~0.5 = edge-on toward camera; 1 = wide open (≈146°). |
| `locked` | 0..1 | 1 = padlock closed through the door hasp; 0 = shackle popped, lock hanging tilted from the jamb staple (outBack ease built in: animate 1→0 over ~0.4–0.7 s for a satisfying *click*; 0→1 snaps shut at the end). |
| `rust` | 0..1 | clean dark gunmetal → orange-brown rust with spots, pits and flakes; padlock and sign weather (sign paint chips out of the lettering from ≈0.4). ≥0.55 the lower hinge snaps; ≥0.7 one sign string snaps and the sign hangs askew; door sags on its top hinge (at `door:1, rust:1` its free corner rests on the ground). |
| `shake` | 0..1 | bars rattle (front bars most, the door rattles in its frame, padlock + sign swing, whole cage jitters ≤1 px). Deterministic in `t`. Use while Fear pulls the bars (0.5–1) and decay it to 0. |
| `dim` | 0..1 | fades toward darkness (`darkColor`, default `#0d0b1c`) and to 60 % opacity — 0.85–1 = "barely visible". |
| `flake` | 0..1 or array | progress of a rust flake tumbling down from the gate's top rail to the ground in front of the cage (s17 "a flake of rust drifts down"). Animate 0→1 over ~3–4 s; pass an array (`[k1, k2]`) for several flakes. Omit / ≤0 / ≥1 = none. |
| `flip` | 1 \| −1 | mirror: hinge on the right, padlock on the left. Sign text stays readable. |
| `shadow` | bool (true) | soft ground shadow (drawn in the back layer). |
| `grips` | array of anchor names or `[x,y]` cage-local (unflipped) points | draws the occupant's fingers wrapped over the nearest bar at that point (follows the bar's rattle). Use the same points you give Fear's hands. |
| `gripColor`, `gripLine`, `gripScale` | colours / number | finger colours (default Fear lavender `#b9a6ea` / `#3d2c66`); `gripScale` = occupantScale / cageScale (default 1). |
| `rim` | colour | violet rim light on bar edges (default `#8a6cff`). |
| `darkColor` | colour | what `dim` fades toward (default back-of-mind `#0d0b1c`). |

### CAGE_PRESETS (spread them into state)
`locked` (s09–s10) · `unlocked` (s11, after the Void's fingertip) · `ajar` door .3 (gate drifts open) ·
`open` · `rustedOpen` (s21) · `barelyVisible` (rust 1, door 1, dim .85 — s22).

### CAGE_ANCHORS (cage-local, scale 1, unflipped) — use `cagePoint(name, x, y, scale, state)` → world `[x, y]`

| name | local [x, y] | use |
|---|---|---|
| `occupant` | [0, −20] | occupant's feet, centre of the cage floor |
| `occupantFront` | [0, 0] | feet right behind the front bars — use for gripping the bars |
| `occupantBack` | [0, −34] | feet near the back bars (cowering) |
| `occupantSide` | [−70, −12] | feet in the left half (curled up; with the Void on the right this is "the side farthest from the Void", s10) |
| `gripL` / `gripR` | [∓79, −186] | hands on the two door-jamb bars at Fear's face height (reachable from `occupantFront`). **L/R are screen sides** (swapped automatically when `flip:-1`). |
| `gripHighL` / `gripHighR` | [∓79, −233] | higher grip (arms up; at the edge of Fear's reach) |
| `gripC` | [0, −166] | door centre bar |
| `lockHang` | [84, −119] | staple the padlock hangs from — the Void's fingertip / the key target |
| `lock` | [84, −89] | padlock body centre (closed); keyhole ≈ +4 px lower |
| `doorHandle` | [84, −121] at door 0 | hasp on the door's free edge: grab point to open/close. **Moves with `door`/`rust`: always use `cagePoint('doorHandle', …, state)`** (door .5 → [−31, −90], door 1 → [−211, −103]). |
| `hingeTop` | [−80, −262] | upper hinge |
| `doorway` | [0, 13] | threshold centre (feet stepping out; "sinks down on the threshold, half in and half out", s12) |
| `outside` | [0, 70] | feet just outside the door |
| `floorFront` | [0, 36] | lowest visible point (plinth lip) |
| `sign` | [0, −377] | centre of the TIME-OUT sign (clean cage; tilts away from this when rust ≥ 0.7) |
| `top` | [0, −480] | top of the hanging loop |
| `topRingFront` | [0, −307] | front of the top ring (above Fear's head) |

### Recipe: Fear inside, crying and pulling the bars
```js
const [cx, cy, cs] = HQ_VIEWS.backOfMind.anchors.cage;            // cage stands here
const cst = { t, ...CAGE_PRESETS.locked, shake: S.k(t, [['s09b04', 0], ['s09b04+0.3', 0.8], ['s09b04.end', 0]]) };
drawCage(g, cx, cy, cs, { ...cst, layer: 'back' });
const [fx, fy] = cagePoint('occupantFront', cx, cy, cs, cst);      // Fear at the same scale as the cage
const loc = (p) => [(p[0] - fx) / cs, (p[1] - fy) / cs];            // world → Fear-local arm target
drawFear(g, fx, fy, cs, { t, tremble: 0.7, face: withSpeech(EXPR.crying, S.lip('FEAR', t)),
  armL: { target: loc(cagePoint('gripL', cx, cy, cs, cst)), bend: 1,  front: true, hand: 'grip' },
  armR: { target: loc(cagePoint('gripR', cx, cy, cs, cst)), bend: -1, front: true, hand: 'grip' } });
drawCage(g, cx, cy, cs, { ...cst, layer: 'front', grips: ['gripL', 'gripR'] });
```
Add a small pull: offset the arm targets by `[0, +3*shake*sin(t*9)]` and lean Fear back (`lean: -0.04`).

### z-order & gotchas
- Order: `back` → anything INSIDE (Fear, its shadow) → `front`. A character standing OUTSIDE in front of the
  cage (Consciousness, the Void's hand) is drawn after `front`; a character BEHIND the cage before `back`.
- Someone walking out: draw Fear between the layers until its feet pass `doorway` (y > 13·scale below origin),
  then after the `front` layer.
- With Fear centred at `occupantFront` the door's centre bar runs between its eyes and splits the mouth (intended:
  the caged face; eyes and brows stay clear, a crying/frowning mouth still reads on both sides of the bar).
  Shifting Fear's x by ±20–60 px puts a bar through an eye — keep it centred. For lip-synced lines, open the door
  first or frame Fear outside the cage.
- `locked:1` with `door>0` is physically wrong (the hasp moves away from the lock) — unlock first.
- The door at `door ≈ 0.5–0.65` is edge-on (a thin slab): pass through it quickly; hold on 0.25–0.35 or 1.
- The Void's unlock (s11): fingertip to `cagePoint('lockHang')`, `locked` 1→0 over 0.6 s, then `door` 0→0.3
  over ~2 s with `ease.outCubic` (drifts open on its own weight), small `shake` 0.15 at the click.
- The rusted gate "creaks a few degrees and settles" (s17): `rust: 1`, `door` 0.93→1.0 over ~1.5 s with
  `ease.outBack`, plus `flake` 0→1 over ~3.5 s starting a beat later.
- Static parts are cached as bitmaps per (rust, dim in 0.05 steps, on-screen pixel scale in 1/8 steps, up to
  4× so an insert on the padlock stays crisp). Animating rust/dim/zoom continuously rebuilds a ~5–15 ms cache
  every few frames — fine, but avoid animating rust every frame for long shots. Memory is bounded
  (LRU, ≈96 MB of bitmaps max). `shake > 0` draws the front bars live (+3 ms).
- Draw time (incl. flush, 720×1280): ≈2.5–3 ms static, ≈6–8 ms shaking or rusted+open.

---------------------------------------------------------------------------------------------------
## 2. The old notebook — `drawNotebook(g, x, y, scale, state)`

"My first story": a worn **cream-gold** cardboard notebook with a tan cloth spine (the same notebook SELF holds in
`self.mjs`'s `drawSelfNotebook`, so cuts between the two keep continuity), a crooked paper label
**"My Feelings"** / *a story by me* (Caveat), crayon doodles (lavender Fear bean with huge eyes and a coral knitted
scarf, a dark hooded figure with gold star stickers, a heart, stars), scuffed corners and a faint mug ring.
Open spread: LEFT (inside of the front cover) = childlike pencil handwriting on lined paper ("Inside my head there /
is a control room. / My Fear lives there. / It keeps pulling / the fire alarm!! / A big dark one / stands in the
back. / It never moves. / Fear is scared of it."). RIGHT = the **first page**: a crayon drawing of the control room
— Fear (scarf, labelled FEAR) pulling a red alarm ("AAAA!!"), a tall hooded shape scribbled in near-black crayon
with **no stars** and a "?", a console with coloured buttons, a gold star sticker — and big pencil handwriting
**under the drawing**: "Why does it just / stand there??" (screenplay s01 insert).

**Origin** = centre of the book (closed: centre of the cover; open: centre of the spread — the book slides
right→centre as it opens so the spread ends centred on (x, y)).
Sizes at scale 1 (`NOTEBOOK_SIZE`): closed 220 × 290; open spread 440 × 290. Handwriting cap height ≈ 16 px →
for legible text on a phone show the spread ≥ 560 px wide (scale ≥ 1.3; `REALROOM.anchors.notebookInsert` =
scale 1.45).

| field | range | meaning |
|---|---|---|
| `open` | 0..1 | cover flips around the spine (0.5 = cover vertical/edge-on, 1 = spread). Animate over 1.0–1.6 s, `ease.inOut`. |
| `flat` | 0..1 | 0 = facing camera (held up / insert); 1 = lying on a desk (vertical squash ×0.5). |
| `rot` | rad | rotation in the picture plane (a casual angle on the desk: ±0.05–0.15). |
| `dim` | 0..1 | darkens (use ~0.5 when the room lamp is off). |
| `shadow` | bool (true) | soft drop shadow. |
| `palette` | `'gold'` (default) \| `'blue'` | `'gold'` matches SELF's held notebook — keep it for the whole film. `'blue'` (sky-blue board, red spine) is an alternative with more contrast on the desk, but it is NOT the notebook SELF holds. |

Gotchas: all art is pre-rendered once (2.5× resolution) — crisp up to scale ≈ 2.5. Draw time 1–3 ms.
Hands holding it are not part of the prop (draw them after, or use Self's own notebook pose).
Continuity note: SELF's small held notebook is lettered "My Story"; this prop (per the brief) says "My Feelings".
At SELF's held size the lettering is barely legible, but the two titles should be unified in one of the modules.

---------------------------------------------------------------------------------------------------
## 3. Desk lamp — `drawDeskLamp(g, x, y, scale, state)`

Mustard-enamel articulated lamp. **Origin** = centre of the base on the desk top. Height ≈ 238 at scale 1.
`state`: `on` 0..1 (bulb + halo + light cone; at 0 the inside of the shade goes dark so "clicked off" reads),
`facing` 1 (shade points down-right) / −1, `cone` bool or 0..1 (light-cone strength, default 1), `glow` bool
(halo, default true), `night` 0..1 (tints the lamp body toward `nightColor`, default `#141331`, for a dark room),
`t` (tiny flicker).
`LAMP_ANCHORS` (facing 1, mirror x for −1): `base [0,0]`, `head [58,−224]`, `bulb [107,−156]` (light source),
`lightDir [0.58, 0.81]`, `top [58,−238]`, `bbox [−52,−238,146,7]` (silhouette; cone and halo extend further).
The room draws its own lamp — only use this elsewhere.

---------------------------------------------------------------------------------------------------
## 4. REAL_ROOM — `drawRealRoom(g, state)` + `drawRealRoomForeground(g, state)` + `REALROOM`

A cozy night bedroom corner: plum wall warmed by the lamp, a sash window (deep-blue night sky, a few soft
twinkling stars, a crescent moon RISING low over hills and rooftops with tiny lit windows, soft clouds, a
succulent on the sill), dusty-rose curtains with tiebacks, warm fairy lights along the rod, a shelf with books,
a framed crayon drawing and a trailing pothos (left), a hanging plant + small framed heart (right), and a wooden
desk across the lower third with the lamp (left), a mug with gentle steam, a book stack and three crayons (right).

**The stage is 840 × 1280** (wider than the frame). Keep the camera inside the stage: at zoom z, camera x within
`360/z … 840−360/z` and y within `640/z … 1280−640/z` (outside that the frame shows past the stage edge).

### cameras (`REALROOM.cameras`, pass to `applyCamera`) — all verified in frame
| name | value | shot |
|---|---|---|
| `full` | {x 420, y 640, zoom 1} | the whole corner (default; same as `REALROOM.camera`) |
| `opening` | {x 420, y 655, zoom 1.12} | **first frame / thumbnail** (s01): title box fully in the upper third (frame y 54–294), face in the middle third (y ≈ 668), notebook lying open on the desk in the lower third (y 959–1058) above the bottom 15 % (y 1088). The 2 % push-in ends at zoom 1.142. |
| `desk` | {x 424, y 760, zoom 1.5} | "close on SELF at the desk in the lamp pool, notebook open, starry window behind" (s20) |
| `face` | {x 424, y 680, zoom 2.2} | face close-up |
| `window` | {x 432, y 450, zoom 1.45} | the window: stars, moon, the star-hood (s20 ending) |

### state
| field | range | meaning |
|---|---|---|
| `t` | s | stars twinkle, fairy lights breathe, steam rises, dust motes drift (all small/slow) |
| `lamp` | 0..1 (1) | lamp light: 0 = moonlit blue room, 1 = warm. Animatable (cross-dissolves two caches). As the lamp goes off the stars brighten and grow a touch ("the stars become the brightest thing in frame"). |
| `moon` | 0..1 (1) | moon + moon glow + cool window spill. Baked in 0.1 steps — keep constant in a shot. |
| `dusk` | 0..1 (0) | sky: deep night → violet/rose twilight horizon. Baked in 0.1 steps — keep constant. |
| `fairy` | 0..1 (1) | fairy-light brightness. For the lamp-off ending use ≈0.3 so the stars stay the brightest points. |
| `starHood` | 0..1 (0) | s20: "a faint hooded shape made of stars seems to stand among them" — a constellation of a tall hood (peak, rounded hood, broad shoulders, cloak to the far hills) with faint lines, a whisper of the Void's violet and a dark hood opening. Fade 0→0.8→0 over ~4 s. |
| `starWink` | 0..1 (0) | "one star twinkles": a 4-point glint in the hood opening (`REALROOM.anchors.starWink`). Pulse it 0→1→0 over ~0.8 s near the hood's peak. Works with or without `starHood`. |
| `deskTop` | bool (true) | foreground redraws the desk-top surface (covers anything below the desk line). |
| `motes`, `steam` | bool (true) | dust motes in the lamp light / mug steam |

### anchors (`REALROOM.anchors.name = [x, y, scale]`)
| name | value | meaning |
|---|---|---|
| `selfSeated` | [420, 905, 1] | `drawSelf(…, {seated:true})` origin = where the desk top's far edge meets the body |
| `faceCloseUp` | [424, 680] | camera target for a face close-up (zoom 1.8–2.4) |
| `notebook` | [430, 984, 0.6] | notebook lying on the desk (`flat: 1`, `rot ≈ −0.04…−0.06`; open or closed) |
| `notebookHeld` | [410, 846, 0.62] | notebook held upright at the desk edge, cover to camera (`flat: 0`) |
| `notebookInsert` | [420, 640, 1.45] | spread filling the default frame for an insert |
| `lamp` | [124, 984, 0.86] | lamp base; `lampLight` [216, 850] = the bulb (light source for face lighting) |
| `mug` | [628, 1004] · `window` [432, 327] · `moon` [556, 414] · `starWink` [412, 196] |
Also: `REALROOM.deskY` 905 (far edge) · `deskNearY` 1030 · `deskFrontY` 1047 ·
`window {x0 254, x1 610, y0 114, y1 540, rail 362}` · `titleBox {x 266, y 132, w 332, h 214}` (WORLD coords) =
the clean upper window pane for the title card on the first frame (title "The Void and My Fear" in 2 lines of
cream Caveat at ~50 px fits; stars behind it are small and dim).

### z-order (first frame / s01, s20)
```js
applyCamera(g, REALROOM.cameras.opening);
drawRealRoom(g, st);
const [sx, sy, ss] = REALROOM.anchors.selfSeated;
drawLitByRoom(g, st, (c) => drawSelf(c, sx, sy, ss, { ...pose, seated: true, layer: 'body' }));
drawRealRoomForeground(g, st);                         // desk top + front + lamp, mug, books, crayons, motes
drawLitByRoom(g, st, (c) => drawSelf(c, sx, sy, ss, { ...pose, seated: true, layer: 'front' })); // arms/hands
drawNotebook(g, ...REALROOM.anchors.notebook, { open: 1, flat: 1, rot: -0.04 });
// title text inside REALROOM.titleBox (world coords, still under the camera), then g.restore()
```
- `drawLitByRoom(g, state, drawFn, box?)` lights a character like the room: subtle warm lamp key from below-left
  when the lamp is on (the face stays clean and saturated for the thumbnail); as `lamp` → 0 the figure sinks into
  the room's soft night blue with a faint cool window wash on hair and shoulders, so SELF does not stay brightly
  lit in the dark ending. `drawFn(ctx)` draws in the same world coords as `g`. `box` = world rect containing the
  character (default `[150, 470, 560, 620]` = the seated narrator; pass your own for other placements). Cost
  ≈2–4 ms per call (two calls per frame for the two-pass narrator). Drawing SELF directly also works (lamp-on
  shots look almost the same).
- Everything of Self below `deskY` is hidden by the foreground's desk top; hands/forearms resting on the desk must
  be drawn AFTER the foreground (Self's `layer:'front'`). If you draw Self in one pass and its hands rest on the
  desk, use `deskTop: false` (Self must then not draw below the desk line itself).
- The lamp, its warm cone (0.45 strength) and the warm wall bloom behind the head make the face the focal point.
- Ending (s20): animate `lamp` 1→0 at the click (≈0.25 s), `fairy` 1→0.3, then `starHood` + `starWink` pulses;
  keep `moon` constant (baked).
- Caches are built once per process per (lamp on/off, moon, dusk, resolution). Resolution follows the on-screen
  scale in 0.5 steps (1×, 1.5×, 2×, 2.5×, 3×), so the opening still at zoom 1.12 is rendered at 1.5× and stays
  sharp; a 2 % push-in never changes the step. First frame ≈ 50 ms (1×) … 250 ms (3×) to build, then
  (incl. flush, both layers) ≈ 3–4 ms at zoom 1, ≈ 9–10 ms at the opening camera incl. the notebook, ≈ 9–10 ms at
  zoom 1.8, ≈ 4–5 ms while the lamp fades. Memory bounded (LRU, ≈120 MB of bitmaps max).

---------------------------------------------------------------------------------------------------
## 5. Notes
- `hrand(i, seed)`, `vnoise(x, seed)`, `vfbm(x, seed)` (exported from props.mjs) are integer-safe deterministic
  noise helpers; props and the room use only these.
- **ENGINE BUG (src/engine.mjs, shared core — needs the owner's fix):** `hash()` overflows double precision
  (`n * (n*n*15731 + 789221)` with n up to 2³¹), so `rand(i, seed)` returns exactly 1.0 for every input except
  `rand(0, 0)`; `noise1(x, seed)` is a constant 1.0 for every seed ≥ 2 (checked 2–20), flat for seed 1 once
  x ≳ 30, and only seed 0 behaves. Consequences today: `autoBlink` blinks on a fixed metronome and ALWAYS
  double-blinks; Fear's `tremble` shiver (`noise1(t*38, 1)`) is a constant offset instead of a shake after the
  first second; `fbm`-driven idle sway (Fear's tuft, `drift()`) is frozen. Fix: integer hashing with `Math.imul`
  (as in props.mjs `h32`), keeping the same signatures.
- @napi-rs/canvas quirk: after `restore()`, reading `g.fillStyle`/`strokeStyle` returns the stale value even
  though the real drawing state is restored. Never read them back; always set before drawing.
