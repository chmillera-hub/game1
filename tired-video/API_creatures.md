# API — `engine/creatures.py`

Three creature rigs (plus the sweater lump and a cheap pod sleeper). Flat colours,
plum `ink` outline 5.5 px at s=1 (it scales with `s`), one shadow tone per material.

```python
from engine.creatures import (draw_impulsivity, draw_thing, draw_sweater_lump,
                              draw_specimen, draw_specimen_pod_sleeper,
                              IMP_DERP_L, IMP_DERP_R, EYEROLL_DUR,
                              SPEC_WALK_CYCLE, SPEC_WALK_SPEED)
```

## 0. Conventions (all rigs)

| thing | rule |
|---|---|
| units | logical 1080x1920 px. `s` scales the whole rig (s=1 sizes below). Works inside `core.camera()`. |
| `(x, y)` | the **ground point** under the body, except airborne / held poses where it is the **body centre** (marked ✈ in the tables). |
| facing | every rig faces **right**. `flip=True` mirrors it to face left, shading included. |
| `look` | always **screen space**: (+1, 0) = right, (0, +1) = down, length ≤ 1. It stays correct when you flip. |
| `t` | scene time. It drives all the automatic life (breathing, blinks, idle motion, cycles). Same `t` = same frame. |
| `pose_t` | optional seconds since a pose or expression began (lunge stretch, eyeroll, walk). `None` = derived from `t`. |
| `blink` | `None` = automatic. Pass a number 0..1 to force the lids (it works even on a frozen rig). |
| return | dict of anchors `name -> (x, y)` in the **caller's** coordinates (the specimen also has the nested dict `hold_points`). |
| callbacks | `hold=fn` → `fn(ctx, a)` is called **mid-draw**, in caller coordinates, so a prop can be sandwiched in z-order. `a` = the anchors so far + `a["s"]`, `a["flip"]` and, where relevant, `a["angle"]` (screen radians). |
| randomness | none: everything is a pure function of the arguments. |

---

## 1. Impulsivity — `draw_impulsivity`

```python
draw_impulsivity(ctx, x, y, s, t, pose="sit", expr="derp", look_l=None, look_r=None,
                 pant=1.0, wag=0.0, blink=None, frozen=True, flip=False, hold=None,
                 pose_t=None) -> anchors
```

### Poses (sizes at s=1, w x h)
| pose | view | (x, y) | size | notes |
|---|---|---|---|---|
| `sit` | frontal | ground | 654 x 600 | the default tripwire pose. The tail sticks out at the right. |
| `stand` | side, 3/4 head | ground | 794 x 563 | four stubby legs. The far legs use a darker tone. |
| `lunge` ✈ | side | body centre | 1049 x 492 | bursting through a door. The body is stretched 1.2x at `pose_t`=0 and eases to 1.0 by 0.45 s. Ears and tongue stream back, with a 7 Hz flutter. |
| `tug` | side | ground | 678 x 600 | leans back with its front legs braced. Cage handle clamped in a grin: 2.2 Hz yank, 4.4 Hz head shake, 3 Hz tail wag. Uses `hold`. |
| `lie` | frontal | ground | 751 x 436 | belly down, chin on its front paws. |

### Expressions
| expr | look |
|---|---|
| `derp` | huge white eyes with tiny pupils, wall-eyed by default (`IMP_DERP_L` = (-0.78, -0.42), `IMP_DERP_R` = (0.72, 0.5)). Dumbest grin, tongue lolling. |
| `happy` | cheeks push the lower lids up, brows rise, wider grin. |
| `excited` | eyes 1.2x with even smaller pupils, ears perk, tongue flaps side to side at 5 Hz, pant at 4 Hz. |
| `focused` | **both pupils align** (default (0, 0.05): a dead stare at the camera). Flat lids and furrowed brows; the grin narrows and the tongue goes in. Comedic: use it for ~0.5–0.8 s. |
| `sleepy` | lids 60% closed, droopy pupils, longer tongue, slow 1.2 Hz pant. |

### Life controls
* `pant` 0..1: tongue bob, belly swell and head bob at **3 Hz** (4 Hz excited, 1.2 Hz sleepy). `pant=0` leaves a slow 3.5 s breath.
* `frozen=True` (default): no blinks, no pupil drift, no head sway. **Only the pant moves** (plus the tail if you pass `wag`). `frozen=False` adds blinks (~0.28/s), a ±0.1 pupil drift, a small head sway and ear jiggle.
* `wag` 0..1: tail wag amplitude at 2.6 Hz. `tug` always wags.
* `look_l` / `look_r`: the pupil direction of the **screen-left / screen-right** eye. They are independent; `None` = the expression default.

### Anchors
`head`, `top` (crown), `eye_l`, `eye_r`, `nose`, `mouth` (the clamp point in `tug`), `tongue` (tip, only while it is out), `tail` (tip), `chest`, `center`, `paw_l`, `paw_r`. The paws are screen-left/right: the front paws in sit/lie, the rear/front paws in side poses. The sitting eyes are ≈ 100 px wide at s=1.

### Recipes
**The one-eye-tracks gag** (the tripwire that never goes off). Stay frozen and move ONE pupil slowly; nothing else changes:
```python
lr = core.tween(t, [(t0, IMP_DERP_R), (t0 + 2.5, (-0.85, 0.05))])   # slow, ~2-3 s
draw_impulsivity(ctx, x, y, s, t, look_r=lr)        # look_l keeps its derp default
```
**Focused beat**: tween both looks to the same target over ~0.15 s, then switch `expr="focused"`. Hold, then snap back to `derp` (the pop back is the joke).

**Cage handle in the mouth (s07 tug)**: the callback runs after the mouth interior and **before the teeth**, so the bar sits between the jaws:
```python
def cage(ctx, a):
    mx, my = a["mouth"]; k = a["s"]          # a["angle"] = head tilt (screen radians)
    with core.saved(ctx, mx, my, k, a["angle"]):
        props.draw_cage(ctx, ...)            # draw the handle bar through (0, 0)
draw_impulsivity(ctx, x, y, s, t, pose="tug", hold=cage)
```
The cage hangs from the handle, so it overlaps the chest; anything drawn in the callback is covered only by the teeth and the lolling tongue.

---

## 2. The thing — `draw_thing`

```python
draw_thing(ctx, x, y, s, t, state="sit", look=(0, 0), flip=False, blink=None, motion=0.0)
```
A fuzzy violet critter (~125 px long at s=1 without its tail) with big shiny black eyes, round ears, a long thin tail and two tiny teeth. Auto blink is ~0.35/s; the ears twitch on hashed beats (~1.4 s / 1.7 s).

| state | (x, y) | size | cycle / notes |
|---|---|---|---|
| `sit` | ground | 145 x 133 | upright with paws at its chest. Breath 1.3 Hz, tail sway, ear twitches. |
| `scurry` | ground | 234 x 85 | **0.22 s** leg cycle. `motion` 0..1 adds a fur smear, speed lines and stretch. Above ~0.75 the legs become a blur wheel. Move it fast (≥ 600 px/s) when motion is high. |
| `peek` | the floor / edge line | 76 x 77 | head and paws only, peeking from under something. `look` also turns the head. Draw the occluder (bed edge) after it if needed. |
| `hiss` | ground | 161 x 139 | arched back, bristled bottle-brush tail, angry lids, tiny teeth, trembling. |
| `leap` ✈ | body centre | 254 x 102 | stretched mid-air, wide eyes, speed lines (always ≥ 0.4). |
| `bite` | **the bite point** | 112 x 214 | jaws clamped at (x, y) with eyes squeezed `> <`. The body dangles and swings (1.7 Hz) and kicks (4 Hz). "Chomp" lines pop every **0.25 s**. |
| `struggle` ✈ | body centre | 146 x 121 | 3.2 Hz wriggle with flailing legs and a whipping tail. The eyes alternate squeezed/wide (~0.9 Hz). |
| `cage_inside` | ground | 88 x 133 | compact frontal sit with paws raised (to hold bars). Ears droop. Draw the bars over it. |

Anchors: `head`, `top`, `eye_l`, `eye_r`, `nose`, `mouth`, `tail_tip`, `center` (+ `paw_l`/`paw_r` in `cage_inside`).

### Sweater lump — `draw_sweater_lump(ctx, x, y, s, t, wiggle=0.0, color=None, tail=0.0, flip=False)`
A knit sweater heaped on the floor (≈ 360 x 90 px at s=1, `(x, y)` = floor point under the middle), with a sleeve and ribbed cuff, a ribbed hem and V-stitch columns that ride the surface.
* `wiggle` 0..1: the lump under the knit. At 0 it is a still heap. As it rises the lump grows, roams left/right (noise) and jerks (pulses every ~0.9 s when high). Stretch folds radiate from it, and from ~0.3 the **two little ears press up under the knit**.
* `tail` 0..1: pokes the violet tail out from under the hem at the right.
* `color`: knit colour (default warm red `#c9524a`).
* Anchors: `lump` (top of the lump), `center`, `tail_tip` (when shown).

---

## 3. Specimen Zero — `draw_specimen`

```python
draw_specimen(ctx, x, y, s, t, form=1.0, pose="crouch", expr="calm", look=(0, 0), glow=1.0,
              writhe=0.0, sleeping=False, blink=None, flip=False, pose_t=None,
              face=1.0, point_angle=0.0, hold=None, tilt=0.0) -> anchors
```
Extras beyond the brief: `face` is the head yaw (1 = facing forward, 0 = toward the camera, **-1 = looking back over its shoulder**). `point_angle` is the radians of the pointing paw (0 = straight ahead, + = down; clamped -0.7..0.9). `hold` is the prop callback. `tilt` is extra head rotation (+ = nose down); animate it for nods.

Sleek, dog-sized creature: crouch ≈ **533 x 315 px** at s=1 (including tail and ears). It has a deep indigo body, long swept-back fin ears with ribs, a long tail with a spade fin, a soft teal rim and huge eyes with glowing teal irises. `glow` 0..2 scales the rim, the outer halo and the eye glow.

### Poses
| pose | (x, y) | size | notes |
|---|---|---|---|
| `crouch` | ground | 533 x 315 | ready to pounce: 1.1 Hz butt wiggle and a lashing tail. |
| `leap` ✈ | body centre | 648 x 263 | mid-air lunge with front paws reaching forward, **claws out**, tail streaming. |
| `held` ✈ | body centre | 406 x 357 | sagging across a person's arms with legs and tail dangling. **`hold` callback + `hold_points`** (see below). |
| `writhe` ✈ | body centre | ~430 x 440 | held, plus spine twist (1.7 Hz), head thrash and leg kicks (2.6 Hz). Amplitude = `writhe` (0 → 1.0 for this pose). `writhe` > 0 also works on `held`. |
| `sit` | ground | 295 x 371 | cat sit, with the tail curled around its front paws. |
| `walk` | ground | 553 x 332 | four-leg walk: **0.9 s cycle** (`SPEC_WALK_CYCLE`) from `pose_t` (or `t`). Move x by **`SPEC_WALK_SPEED * s` = 120·s px/s** to keep the feet planted. |
| `stand` | ground | 553 x 332 | the walk skeleton standing still, with a breath. |
| `point` | ground | ~340 x 371 | sitting, near front paw extended with one digit. `point_angle` aims it; `face` and `look` stay free (e.g. `face=-1` looks back at Tiredness while it points down the tunnel). Anchor `paw` = the tip. |
| `tug` | ground | 521 x 344 | bites a hoodie hem and pulls back: 2 Hz yank, 4 Hz head shake. `hold` is called at `a["mouth"]`, **between the jaw line and the fangs**: draw the hem there. |
| `nuzzle` | ground | 471 x 363 | head raised and tilted, rubbing on a 1.2 s cycle (`pose_t` or `t`) with eyes closed (forces `content`). Extra anchor `rub` = the top-front of the head, where it presses: put the cheek or hand there. |

### `form` morph (0 = shadow mass → 1 = true shape)
The morph is geometric rather than a cross-fade. The same skeleton is wrapped in an inflated, wispy **shadow shell** that contracts onto the real body:

| form | what happens |
|---|---|
| 0 | writhing shadow mass: an inflated near-black shell with a dim violet edge, 9 body wisps plus 3 head wisps (smooth tapered shapes waving at ~1.5–2 rad/s), slow inner smoke curls, a fat wavy tail, **glowing teal slits** (bare, no outlines) and a jagged maw with ~21 teeth that snaps (~0.5 Hz). |
| 0 → 0.48 | the wisps shorten and **curl back in**; the shell deflates (gone by 0.66); the head wisps retract as the ears smooth out. |
| 0.08 → 0.55 | the maw shrinks and its teeth retract into the real mouth. |
| 0.28 → 0.85 | colour runs shadow → indigo. The outline runs violet → ink (0.45–0.9). |
| 0.32 → 0.82 | the slits open (a glowing "visor" around 0.55). The sclera turns teal → white and the irises grow (0.45–0.8). Pupils appear from 0.55. |
| 0.52 → 0.93 | the **teal rim traces itself** along the back, head, tail and ears, brightest around 0.76, then settles. |
| 0.78 → 0.95 | eye highlights pop in with an overshoot: the sparkle moment. |

Suggested timing: `form = core.tween(t, [(t0, 0.0), (t0 + 1.4, 1.0)])` (eased), then `expr="wide"` for the eyesWide beat. Auto blink starts once form ≥ 0.5. At form 0, `expr` only affects the pupils and mouth once they exist, so use `snarl` or `wide` around the morph.

### Expressions
| expr | look |
|---|---|
| `calm` | relaxed lids, medium pupils, small smile. |
| `snarl` | angry lids, slit pupils, ears flat back, open mouth with fangs, muzzle wrinkles. |
| `wide` | eyes 1.22x, tiny pupils, ears perked, small "o" mouth (realisation). |
| `curious` | head tilt (-0.24 rad), one ear up and one down, big pupils. |
| `content` | closed happy ^ ^ arcs, smile, gentle 0.5 Hz head sway (purring). |
| `eyeroll` | timed, see below. |
| `pleading` | eyes 1.15x, huge pupils, extra wet highlights and a lower shine line, inner lid corners raised, ears back. |
| `sad` | downcast pupils, lids slanted sad, ears drooping, head lowered. |
| `annoyed` | flat half lids (impatient), flat mouth. |

**Eyeroll timing** (`EYEROLL_DUR` = 1.25 s from `pose_t`; with `pose_t=None` it loops every 2.6 s of `t`):
`0–0.20 s` lids drop to 40% and the pupils slide right → `0.20–0.95 s` the pupils roll **up and over the top to the left** (the lids lift a little at the top) with a slight head tilt → `0.95–1.25 s` they return to `look` → after that, a flat half-lidded stare. No auto-blinks during the roll. Set `pose_t = t - info.cue("roll")`.

### Holding it in arms (s12 grab / writhe / form / calm)
```python
def arms(ctx, a):
    hp = a["hold_points"]                    # front, back, chest, rump, belly (screen coords)
    draw_forearm(ctx, hp["front"])           # forearm under the chest
    draw_forearm(ctx, hp["back"])            # forearm under the rump
draw_specimen(ctx, x, y, s, t, form=f, pose="writhe", writhe=w, expr="snarl", hold=arms)
```
The callback runs after the tail, the far legs, the body and the hind legs, and **before** the near front leg and the head. So the front paw hangs **over** the forearm and the head sits on top. Draw the person's torso before the call and their hands or upper arms after it. `hold_points` is returned for every pose (estimated from the body), so a scene can also catch it mid-leap.

### Sleeping / pods
* `sleeping=True` draws `draw_specimen_pod_sleeper(..., seed=0)`.
* `draw_specimen_pod_sleeper(ctx, x, y, s, t, seed=0, flip=None, glow=1.0)`: a curled loaf with its head tucked on its tail, the ear fin folded back, closed eyes leaking a faint teal glint, and a teal rim arc. Size ≈ 324 x 146 at s=1; `(x, y)` = ground point. Slow breath (3.2–4 s period). `seed` sets the breath phase and rate, the facing (when `flip=None`) and the tail tip. No clips or gradients, and the outline is never thinner than 2 logical px, so it reads at s≈0.2–0.4.
* Anchors: `center`, `head`, `top`.

### Anchors
`head`, `eye_l`, `eye_r`, `nose`, `mouth`, `paw` (the near front paw; the pointing tip in `point`), `tail_tip`, `center`, `hold_points` = {`front`, `back`, `chest`, `rump`, `belly`}, and `rub` (nuzzle only).

---

## 4. Performance (720x1280 output, ctx scaled 720/1080, s=1, single process)
Measured by `python3 preview/creat_perf.py`:

| rig | budget | measured |
|---|---|---|
| Impulsivity (all poses) | < 8 ms | 5.0 – 6.1 ms |
| the thing (all states) / lump | < 3 ms | 0.6 – 1.3 ms |
| specimen form=0 (all poses) | < 10 ms | 4.3 – 4.9 ms |
| specimen form=1 (all poses) | < 6 ms | 3.7 – 4.3 ms |
| pod sleeper (s=0.3) | < 1.5 ms | 0.24 ms |

Bitrate notes: the wisps are a few large smooth shapes moving moderately, with no particles. The only gradients are two small eye glows per specimen (they move with it). The outer teal halo is flat translucent strokes. Pod sleepers use no gradients at all.

## 5. Preview boards (`python3 preview/creat_test.py [board|all]`)
| file | shows |
|---|---|
| `preview/creat_imp_poses.png` | Impulsivity: all poses, a few expressions, flip, tug with a stand-in cage |
| `preview/creat_imp_expr.png` | Impulsivity expression close-ups (s=1.6) |
| `preview/creat_imp_eyes.png` | **the independent-eye gag**: look_r tracks while look_l stays (frozen) |
| `preview/creat_imp_pant.png` | the 3 Hz pant cycle, 8 phases |
| `preview/creat_thing.png`, `creat_thing_expr.png` | every thing state, plus face close-ups (s=2.6) |
| `preview/creat_thing_cycle.png` | scurry cycle (8 phases) and sweater-lump wiggle ramp |
| `preview/creat_spec_poses.png` | every specimen pose (stand-in arms on held/writhe), plus form-0 versions |
| `preview/creat_spec_expr.png` | specimen expression close-ups (s=2) |
| `preview/creat_spec_morph.png`, `creat_spec_morph_held.png` | the morph: form 0 / .2 / .4 / .6 / .8 / 1 (crouch) and 8 in-betweens (held) |
| `preview/creat_spec_walk.png`, `creat_spec_roll.png` | walk cycle (8 phases), eyeroll timeline |
| `preview/creat_sleepers.png`, `creat_small.png` | pod sleepers at s=0.25–0.3, and everything at in-scene sizes at 720p |
| `preview/creat_anchors.png` (`preview/creat_anchors.py`) | every anchor labelled, including flipped rigs |

`preview/creat_zoom.py name "C.draw_specimen(ctx, X, Y, 1.3, 1.0, pose='sit')" ...` renders ad-hoc zooms.

## 6. Limitations
* Expressions and poses switch instantly (there is no internal blend). Cut on a beat, or blend the continuous controls yourself (`look_*`, `blink`, `tilt`, `form`, `wiggle`, `motion`).
* Impulsivity's `sit` and `lie` are frontal only, and its side poses use a fixed 3/4 head. There is no head-turn control.
* The thing has no separate `expr`: its state sets its face (`hiss` angry, `bite` squeezed, `leap` wide, `struggle` alternating).
* At form 0 the specimen keeps its pose skeleton, so its shadow legs are visible as dark legs inside the mass.
* `flip` mirrors the shading too, so the light side flips with the character.
* The pod sleeper is a separate simplified drawing, not the full rig curled up.
