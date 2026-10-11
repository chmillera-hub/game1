# API — `engine/creatures.py`

Three creature rigs (plus the sweater lump and a cheap pod sleeper). Flat colours,
plum `ink` outline 5.5 px at s=1 (it scales with `s`), one shadow tone per material.
Episode 2 extends the specimen rig: it is now **Curiosity**, with new expressions, poses,
continuous `ears` / `tail_curl` / `tears` / `melt` controls, and **baby Joy**
(`draw_specimen(..., baby=True)`). Every Episode 1 call still works and renders the same
(see §3.9).

```python
from engine.creatures import (draw_impulsivity, draw_thing, draw_sweater_lump,
                              draw_specimen, draw_specimen_pod_sleeper,
                              IMP_DERP_L, IMP_DERP_R, EYEROLL_DUR,
                              SPEC_WALK_CYCLE, SPEC_WALK_SPEED, SPEC_WAVE_HZ, SPEC_RAISE,
                              BABY_WALK_CYCLE, BABY_WALK_SPEED, BABY_ROLL_SPEED,
                              BABY_ROLL_RADIUS)
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


## 3. Curiosity (Specimen Zero) — `draw_specimen`

```python
draw_specimen(ctx, x, y, s, t, form=1.0, pose="crouch", expr="calm", look=None, glow=1.0,
              writhe=0.0, sleeping=False, blink=None, flip=False, pose_t=None, face=None,
              point_angle=0.0, hold=None, tilt=0.0,
              # Episode 2
              ears=None, tail_curl=0.0, tears=None, melt=None, reach=1.0,
              baby=False, roll=None, pose_from=None, pose_mix=1.0) -> anchors
```
Sleek, dog-sized creature: crouch ≈ **533 x 315 px** at s=1 (including tail and ears). It has a
deep indigo body, long swept-back fin ears with ribs, a long tail with a spade fin, a soft teal
rim and huge eyes with glowing teal irises.

| param | meaning |
|---|---|
| `form` | 0 = shadow mass → 1 = true shape (§3.6). Use 1 for all of Episode 2. |
| `look` | screen-space pupil direction. `None` (default) = `(0, 0)` plus the pose's own default (e.g. `lead` looks back and up). |
| `glow` | 0..2: rim, outer halo and eye glow. The rim line keeps reading when dimmed: its alpha follows `glow ** 0.6`, so **`glow=0.2` still shows a clear rim** at s≈0.2–0.35 on a dark set, and the rim never drops below ~1.5 device px. The bright teal irises do not dim. |
| `face` | head yaw: 1 = facing forward, 0 = toward the camera, **-1 = looking back over its shoulder**. `None` (default) = 1, or the pose's own default (`wave` 0.35, `cover_mouth` 0.6, `perch` 0.45, `lead` -1). |
| `tilt` | extra head rotation, **+ = nose down** (also on a looking-back head, see §3.9). Animate it for nods. |
| `point_angle` | radians of the pointing paw in `point` (0 = straight ahead, + = down; clamped -0.7..0.9). |
| `hold` | prop / person callback (§3.7). |
| `ears` | **0..1 continuous ear angle, independent of `expr`**: 0 = flat back and down (hurt), 0.25 = drooped, **0.5 = neutral**, 0.75 = lifted, 1 = shot straight up (alert). `None` = the expression's default. Tween it for "ears lowering degree by degree". Below 0.5 the little ear twitches fade out, so a hurt creature never twitches perkily. |
| `tail_curl` | 0..1: the tail is carried higher and its tip hooks over into a happy "?" (0.5–0.7 = a clear hook, 1 = a tight curl). Works on every pose (it curls upward for tails lying on the ground, e.g. `sit`). |
| `tears` | 0..1, on any expression: 0–0.35 a glisten line brightens along both lower lids, ~0.3 a tear bead starts welling at the near eye, 0.6 a full bead, 0.8–1 it runs a little way down the cheek. `None` = the expression's default (`teary` = 0.6, others 0). |
| `melt` | 0..1 melts the **current pose** into a flat shadow puddle (§3.4); -0.3..0 = springy over-stretch for the re-form pop. `None` = 0 (`pose="puddle"` defaults to 1). |
| `reach` | 0..1 for `reach_up`: 0 = paws held at the chest (begging), 1 = full stretch up and forward. |
| `pose_from`, `pose_mix` | optional skeleton blend from `pose_from` (mix 0) to `pose` (mix 1, eased). §3.8. |
| `baby` | `True` draws baby Joy instead (§4). `roll` is the baby's tumble angle. |

### 3.1 Poses
| pose | (x, y) | size at s=1 | notes |
|---|---|---|---|
| `crouch` | ground | 533 x 315 | ready to pounce: 1.1 Hz butt wiggle and a lashing tail. |
| `leap` ✈ | body centre | 648 x 263 | mid-air lunge with front paws reaching forward, **claws out**, tail streaming. |
| `held` ✈ | body centre | 406 x 357 | sagging across a person's arms with legs and tail dangling. **`hold` callback + `hold_points`**. |
| `writhe` ✈ | body centre | ~430 x 440 | held, plus spine twist (1.7 Hz), head thrash and leg kicks (2.6 Hz). Amplitude = `writhe` (0 → 1.0 for this pose). `writhe` > 0 also works on `held`. |
| `sit` | ground | 295 x 372 | cat sit, with the tail curled around its front paws. |
| `walk` | ground | 553 x 335 | four-leg walk: **0.9 s cycle** (`SPEC_WALK_CYCLE`) from `pose_t` (or `t`). Move x by **`SPEC_WALK_SPEED * s` = 120·s px/s** to keep the feet planted. |
| `stand` | ground | 553 x 332 | the walk skeleton standing still, with a breath. |
| `point` | ground | ~340 x 371 | sitting, near front paw extended with one digit. `point_angle` aims it; `face` and `look` stay free. Anchor `paw` = the tip. |
| `tug` | ground | 521 x 344 | bites a hoodie hem (low: mouth ≈ 74 px up at s=1) and pulls back: 2 Hz yank, 4 Hz head shake. `hold` is called at `a["mouth"]`, **between the jaw line and the fangs**. |
| `nuzzle` | ground | 471 x 363 | head raised and tilted, rubbing on a 1.2 s cycle with eyes closed (forces `content`). Extra anchor `rub`. |
| **`wave`** | ground | 312 x 383 | sitting, the near front paw up beside the cheek in a small **bent-elbow wave** (mitten paw with toe lines, never a straight arm): `SPEC_WAVE_HZ` = 1.7 Hz swing from `pose_t`. With `pose_t` given the paw rises over `SPEC_RAISE` = 0.3 s (slight overshoot) — start `pose_t` at the cue. Default `face` 0.35 so the grin reads. The arm is always drawn in front of the head (no z-flicker). |
| **`wave_stand`** | ground | 505 x 473 | up on the hind legs (tail as a tripod), far paw at the chest, near paw waving beside the head. |
| **`reach_up`** | ground | 462 x 446 (reach 0) → 530 x 491 (reach 1) | up on the hind legs, head tipped back looking up, **both front paws** reaching up and forward (`reach` 0..1; paws arc forward as they rise so they never cross the face). Anchors **`paw`** (near), **`paw_far`**, **`paws`** (midpoint, for the hood edge). `hold` is called **after the head and before the near arm** (§3.7). `a["paws"]` is ≈ 245 px above the ground at reach 0 and ≈ 440 px at reach 1 (s=1). |
| **`cover_mouth`** | ground | 281 x 435 | sitting, near paw pressed over its mouth (the nose peeks over it), hiding a giggle: `expr="calm"` becomes **`giggle`** (squeezed eyes, 2.8 Hz head shake). The paw tracks the mouth whatever `face`/`tilt`. Rises over 0.3 s from `pose_t` like `wave`. |
| **`lead`** (alias `walk_lookback`) | ground | 627 x 337 | the 0.9 s walk cycle with the head turned **back over its shoulder** (`face` -1, `look` back and up, head bobbing with the gait). Same `SPEC_WALK_SPEED`. For "stop, look back once, go": `walk` → `stand` + `face=-1` → `walk`, or blend with `pose_from`. |
| **`perch`** | ground | 337 x 211 | curled up resting (on a person's back): belly flat on y=0, head on its front paws, tail wrapped round the front, slow 4.2 s breath. `expr="calm"` becomes **`asleep`** (pass `content` / `sleepy` for awake). Anchors **`base_l`**, **`base`**, **`base_r`** (contact line, screen-left/right) and **`top`** (top of the back: put baby Joy's ground point there). |
| **`tug_sleeve`** | ground | 464 x 418 | a gentle 1.1 Hz pull on a sleeve cuff held high (mouth ≈ 199 px up at s=1), leaning back with front legs braced; no head shake. `hold` is called at `a["mouth"]` exactly like `tug` (the old `tug` is for low hems). |
| **`puddle`** | floor | 472 x 55 | = `crouch` with `melt=1` (§3.4). |

Unknown pose names fall back to `crouch` (as before).

### 3.2 Expressions
`ears` column = the expression's default on the 0..1 `ears` scale (override with `ears=`).
As in Episode 1, an expression's own gaze offset (e.g. `sad` (0, 0.6), `troll` (0.4, -0.08),
`hopeful` (0, -0.22)) is **added** to `look`.

| expr | look | ears |
|---|---|---|
| `calm` | relaxed lids, medium pupils, small smile. | 0.5 |
| `snarl` | angry lids, slit pupils, open mouth with fangs, muzzle wrinkles. | 0.27 |
| `wide` | eyes 1.22x, tiny pupils, small "o" mouth (realisation). | 0.63 |
| `curious` | head tilt (-0.24 rad), one ear up and one down, big pupils. | 0.54 |
| `content` | closed happy ^ ^ arcs, smile, gentle 0.5 Hz head sway (purring). | 0.4 |
| `eyeroll` | timed (below). | 0.46 |
| `pleading` | eyes 1.15x, huge pupils, extra wet highlights and a lower shine line, inner lid corners raised. | 0.29 |
| `sad` | downcast pupils, lids slanted sad, head lowered. | 0.1 |
| `annoyed` | flat half lids (impatient), flat mouth. | 0.44 |
| **`troll`** | the mischievous evil little grin: a **wide toothy smirk** (near corner hiked into the cheek, a neat row of rounded teeth, no fangs: funny, not scary), **half-lidded sly squint** (far eye lower), **one cocked brow** over the near eye, pupils slid sideways (default look (0.4, -0.08)), slight chin-down. | 0.62 |
| **`teary`** | big wet eyes (1.16x, huge pupils, wet highlights), inner corners raised, lower lids slightly up, a **glisten line** and one **welling tear** (`tears` default 0.6), a trembling wobble mouth (5 Hz). | 0.28 |
| **`proud`** | **chin up** (-0.22 rad), eyes **squeezed happy** (thick ^ arcs with a cheek crease), wide closed grin with curled corners. Pair with `tail_curl`. | 0.74 |
| **`hopeful`** | eyes wide and **soft** (1.17x, big pupils, inner corners raised, shiny), small open mouth, looking up a little. | 0.7 (half up) |
| **`surprised_soft`** | eyes a little wide, medium-small pupils, tiny "o" mouth, head back a hair. | 0.8 |
| **`giggle`** | squeezed happy eyes, open laughing mouth with tongue, a quick little head bounce (~5 bumps/s). | 0.62 |
| **`sleepy`** | lids 58% down, gaze low, head slightly lowered. | 0.36 |
| **`asleep`** | closed sleeping u-arcs, tiny mouth. | 0.34 |

**Eyeroll timing** (`EYEROLL_DUR` = 1.25 s from `pose_t`; with `pose_t=None` it loops every 2.6 s of `t`):
`0–0.20 s` lids drop to 40% and the pupils slide right → `0.20–0.95 s` the pupils roll **up and over the top to the left** with a slight head tilt → `0.95–1.25 s` they return to `look` → after that, a flat half-lidded stare. No auto-blinks during the roll. Set `pose_t = t - info.cue("roll")`.

Expressions switch instantly; the continuous controls (`ears`, `tears`, `tail_curl`, `look`, `blink`, `tilt`, `face`, `melt`, `reach`) are what you tween inside a hold.

### 3.3 Ears, tears and tail recipes
**The ear-lowering hurt beat (s04 "hurt").** Hold ONE expression for the whole beat and ramp the
continuous controls slowly (degree by degree, ~4–5 s), with the gaze sliding down before the
head:
```python
k = core.seg(t, info.cue("hurt"), info.cue("hurt") + 4.5)
ears = core.lerp(0.5, 0.02, core.ease_in_out(k))           # neutral -> flat back and down
tears = core.lerp(0.0, 0.9, core.smoothstep(core.seg(k, 0.2, 1.0)))
look = core.tween(t, [(t0, (0.15, -0.4)), (t0 + 3.0, (0.1, 0.45))])   # up at him -> down
draw_specimen(ctx, x, y, 2.4, t, pose="sit", expr="teary", ears=ears, tears=tears, look=look)
```
(Switching `pleading` → `teary` mid-hold pops the lower lids; start on `teary` with `tears=0` —
at 0 it reads as pleading.) Let go of the sleeve first: `tug_sleeve` → `sit` with
`pose_from="tug_sleeve", pose_mix=ramp over 0.4 s`.

**The troll wave (s03 "troll")**: stage Curiosity right behind the guard's head (on a crate or
pipe so its face is at his head height, s≈1.3–1.8), facing his back:
```python
c = info.cue("troll")
draw_specimen(ctx, x, y, s, t, pose="wave", expr="troll", pose_t=t - c)   # paw rises 0.3 s
```
The grin, sly squint and cocked brow are on from the first frame; the paw comes up over 0.3 s
and waves at 1.7 Hz beside the cheek (it never covers the grin). Hold it ≥ 1.5 s so the gag
lands (cut to Tiredness freezing), and keep the default `face` 0.35 so the grin reads to camera.
The troll's pupils glance sideways by default (its look offset (0.4, -0.08) is added to `look`);
to share the joke with the audience centre them with `face=0.0, look=(-0.4, 0.08)` facing
right, or `look=(0.4, 0.08)` when `flip=True` (expression offsets follow the facing). On the
hind legs instead: `pose="wave_stand"`. To end it, melt (§3.4) without changing the pose:
the paw drops as the melt starts.

**Perk (s01 "perk")**: `expr="surprised_soft"`, tween `ears` 0.45 → 1.0 over ~0.18 s with
`core.ease_out_back`, then hold. **Hopeful (s05)**: `expr="hopeful"` (ears 0.7 by default).
**Droop (s06)**: tween `ears` from 0.3 → 0.1 on the line.
**Proud grin (s01)**: `expr="proud", tail_curl` tweened 0 → 0.7.

### 3.4 Melt into a shadow puddle (s03 "melt" / "reform")
`melt` works on **any pose** and is a pure function of the value, so it plays backwards for the
re-form. What happens as it rises:

| melt | what you see |
|---|---|
| 0 → 0.4 | the raised paw drops, the ears flatten back, lids close, the grin and brow fade into the body; the body slumps (squash + a jelly wobble) and **goo of its own colour climbs the legs**; rim glow off by 0.42. |
| 0.2 → 0.8 | colour runs indigo → near-black shadow; the eyes become **two teal glints** sinking with the body. |
| 0.6 → 0.95 | an amorphous low mound, then a lobed, slowly undulating flat blob (~470 x 55 px at s=1). |
| 0.9 | flat puddle with two **faint glints** (hold here for "it's still watching"). |
| **1.0** | **just a flat dark floor shadow**: no eyes, no rim, no outline (only the puddle is drawn, ~0.25 ms). A flashlight cone over it reads as "just floor". |
| -0.3 .. 0 | over-stretch (taller, thinner) for the springy re-form. |

```python
# s03: troll wave, then melt at the last instant, then re-form smug
melt = core.tween(t, [(c_melt, 0.0), (c_melt + 0.45, 1.0),                     # hide fast
                      (c_reform, 1.0), (c_reform + 0.7, -0.15), (c_reform + 0.95, 0.0)])
draw_specimen(ctx, x, y, s, t, pose="wave", expr="troll", pose_t=t - c_troll, melt=melt)
# after the re-form switch to expr="proud" and do the happy wiggle with tail_curl / tilt
```
Anchors stay valid while melted (they sit on the puddle), so a beam / hit test can keep using
`a["center"]`. `pose="puddle"` alone = a crouch fully melted.

### 3.5 Glow in the dark (s01 "dark", s04 "leave")
`glow` scales the rim, halo and eye glow; the eyes themselves stay bright teal. For "walks
away into the dark, its glow shrinking": shrink `s` with distance and tween `glow` 1 → 0.2; the
rim stays readable down to s≈0.22 at 720p (preview `creat_ep2_glow.png`).

### 3.6 `form` morph (0 = shadow mass → 1 = true shape)
The morph is geometric rather than a cross-fade. The same skeleton is wrapped in an inflated,
wispy **shadow shell** that contracts onto the real body:

| form | what happens |
|---|---|
| 0 | writhing shadow mass: an inflated near-black shell with a dim violet edge, 9 body wisps plus 3 head wisps, slow inner smoke curls, a fat wavy tail, **glowing teal slits** and a jagged maw with ~21 teeth that snaps (~0.5 Hz). |
| 0 → 0.48 | the wisps shorten and **curl back in**; the shell deflates (gone by 0.66); the head wisps retract as the ears smooth out. |
| 0.08 → 0.55 | the maw shrinks and its teeth retract into the real mouth. |
| 0.28 → 0.85 | colour runs shadow → indigo. The outline runs violet → ink (0.45–0.9). |
| 0.32 → 0.82 | the slits open. The sclera turns teal → white and the irises grow (0.45–0.8). Pupils appear from 0.55. |
| 0.52 → 0.93 | the **teal rim traces itself** along the back, head, tail and ears, brightest around 0.76, then settles. |
| 0.78 → 0.95 | eye highlights pop in with an overshoot: the sparkle moment. |

Suggested timing: `form = core.tween(t, [(t0, 0.0), (t0 + 1.4, 1.0)])` (eased), then `expr="wide"`.
Auto blink starts once form ≥ 0.5.

### 3.7 `hold` callbacks (props, arms, the hood)
`hold=fn` → `fn(ctx, a)` is called mid-draw in caller coordinates:

| pose | when it is called | use |
|---|---|---|
| `held`, `writhe` | after the tail, far legs, body and hind legs; **before** the near front leg and the head | the person's forearms (`a["hold_points"]` = front, back, chest, rump, belly). |
| `tug`, `tug_sleeve` | at `a["mouth"]`, between the jaw line and the fangs | the hem / sleeve cuff in the teeth. |
| **`reach_up`** | after the whole body **and head**, **before the near arm**; `a["paw"]`, `a["paw_far"]`, `a["paws"]` are already set | draw his hood (or his head + hood): the near paw then lands **on top of** the hood edge, the far paw stays behind. |

**The hood pull (s02 "nudge" / "hood")**: put Curiosity beside him so `a["paws"]` meets the hood
rim, tween `reach` 0.2 → 1 (reach), hold, then 1 → 0.55 (pulling the hood down/forward) while
the human rig's `hood` goes 0 → 1; draw the hood in the callback at `a["paws"]`.

**The pile (s08)**: draw him face-down, then
`a = draw_specimen(..., pose="perch")` aligned so `a["base_l"]`..`a["base_r"]` sits on his back
(rotate the ctx a few degrees to follow the curve), then
`draw_specimen(ctx, *a["top"], s, t, baby=True, pose="curl")`.

### 3.8 Pose blend (optional)
`pose_from="tug_sleeve", pose="sit", pose_mix=k` eases the skeleton (spine, head, haunch, tail,
matching legs) from one pose to the other (`k` is smoothstepped). Flags (mouth clamp, which
legs exist, tail in front/behind) switch at k = 0.5. Poses with raised paws (`wave`,
`wave_stand`, `reach_up`, `cover_mouth`) and airborne poses do not blend; they switch at 0.5
(those paws already rise smoothly from `pose_t`). Good pairs: `stand`↔`walk`↔`crouch`,
`tug_sleeve`/`tug`→`sit`/`stand`, `sit`→`perch`, `walk`→`lead` (the head turns through the
camera on its way back). 0.3–0.5 s is a natural speed.

### 3.9 Backward compatibility
Every Episode 1 call renders pixel-identical except two deliberate fixes:
* `glow < 1`: the rim is brighter than before (alpha ∝ `glow ** 0.6`) so a dimmed creature
  still reads; `glow=1` is unchanged.
* `face < 0`: expression and user `tilt` used to turn the wrong way on the mirrored
  (looking-back) head (`sad` lifted its nose). `+` now means nose-down on both facings.

### 3.10 Anchors
`head`, `eye_l`, `eye_r`, `nose`, `mouth`, `paw` (the near front paw; the pointing tip in
`point`; the raised paw in `wave` / `wave_stand` / `reach_up` / `cover_mouth`), `tail_tip`,
`center`, `hold_points` = {`front`, `back`, `chest`, `rump`, `belly`}, plus `rub` (nuzzle),
`paw_far` + `paws` (reach_up, wave_stand), `base_l` / `base` / `base_r` / `top` (perch).

### 3.11 Sleeping / pods
* `sleeping=True` draws `draw_specimen_pod_sleeper(..., seed=0)` (baby: the baby sleeper).
* `draw_specimen_pod_sleeper(ctx, x, y, s, t, seed=0, flip=None, glow=1.0, baby=False,
  label=None)`: a curled loaf with its head tucked on its tail, the ear fin folded back, closed
  eyes leaking a faint teal glint, and a teal rim arc. Size ≈ 323 x 146 at s=1; `(x, y)` =
  ground point. Slow breath (3.2–4 s period). `seed` sets the breath phase and rate, the facing
  (when `flip=None`) and the tail tip. No clips or gradients; outline never thinner than 2
  logical px, so it reads at s≈0.2–0.4.
* **`baby=True`**: a tiny curled baby sleeper (round body, big tucked head, ear nub, stubby
  tail), ≈ 145 x 82 at s=1 — at the same `s` it is ~45% of an adult sleeper; s≈0.5–0.6 suits
  the small JOY pod. Breath 2.6–3.2 s.
* `label` is accepted and ignored: the caller draws the nameplate (JOY, COURAGE…) at the
  returned anchor **`plate`** (just below the sleeper). Anchors: `center`, `head`, `top`, `plate`.

---

## 4. Baby Joy — `draw_specimen(..., baby=True)`

```python
draw_specimen(ctx, x, y, s, t, baby=True, pose="sit", expr="calm", look=None, glow=1.0,
              blink=None, flip=False, pose_t=None, face=None, hold=None, tilt=0.0,
              ears=None, tail_curl=0.0, roll=None, sleeping=False) -> anchors
```
A chubby, big-headed, tiny-eared, short-legged baby of the same species: a round bean body
with a lighter belly, stubby legs with round paws, a huge head with **bigger eyes for its head
than the adult's** (eye height ~63% of the head vs ~57%), tiny fin ears, a little curl tuft on top, a tiny tail with a tiny spade, a soft teal
cheek blush. Same indigo (a touch lighter) and the same teal rim and eyes, but softer: thinner
outline (~4.6 px at s=1 vs 5.5) and a fainter, thinner rim. **At the same `s` its walk length is ~40%
of the adult's** (219 vs 553 px); `BABY_SCALE` = 1.08 is already applied. Other params as the
adult (`form`, `melt`, `tears`, `reach`, `writhe`, `point_angle` are ignored).

### Poses
| pose | (x, y) | size at s=1 | notes |
|---|---|---|---|
| `sit` | ground | 163 x 189 | upright bean, front paws together, tail at the back. |
| `wobble_walk` (alias `walk`) | ground | 219 x 181 | toddle: **0.56 s cycle** (`BABY_WALK_CYCLE`) from `pose_t`, stubby alternating steps, a 2x-per-cycle bob, a ±0.09 rad side-to-side rock and a lagging head wobble. Move x by **`BABY_WALK_SPEED * s` = 69·s px/s**. |
| `tumble` | ground under the ball | 136 x 127 | tucked into a ball rolling about its centre (60 px up). `roll` = angle in radians (+ = clockwise = rolling right); `None` = `pose_t * BABY_ROLL_SPEED` (7.5 rad/s). To roll without slipping move x by `roll * BABY_ROLL_RADIUS * s` (60 px per radian at s=1). Ears pressed flat (unless `ears=` is given); `expr="calm"` becomes **`startled`**. Paws can dip ~15 px below the floor mid-spin. |
| `held` (alias `shoulder`) ✈ | body centre | 146 x 232 | sitting in someone's arms / on a shoulder: paws and feet dangle (0.8 Hz swing), tail hangs. `hold` callback (after the body and hind legs, before the front paws and head, like the adult) + `hold_points`. |
| `curl` | ground | 175 x 127 | asleep, curled into a ball with the head tucked on its paws and the tail round the front; slow 3.6 s breath. `expr="calm"` becomes **`asleep`**. Anchors `base_l` / `base` / `base_r`, `top`. |

### Expressions
| expr | look |
|---|---|
| `calm` | open big eyes (auto blink ~0.25/s), small smile. |
| **`blink`** | a timed slow **double blink** from `pose_t` (0.1–0.5 s and 0.62–0.92 s), then open; `pose_t=None` repeats every 2.4 s. For "tumbles out, blinks". |
| **`giggle`** | eyes squeezed (^ ^), open laughing mouth with tongue, a quick little **bounce** (~5 bumps/s): on the ground it squash-stretches about its feet (feet stay planted); `held` / `tumble` hop instead. Plus a fast head wiggle. |
| **`sleepy`** | heavy lids, gaze low, a slow 0.35 Hz head nod. |
| **`curious`** | head tilt (-0.26 rad), one ear up, big pupils, tiny "o" mouth. |
| **`startled`** | eyes 1.22x with tiny pupils, ears straight up, "o" mouth, a slight upward stretch. |
| `content` | closed happy arcs, smile. |
| `asleep` | closed sleeping u-arcs. |

`ears` (0..1, same scale as the adult), `tail_curl`, `look`, `blink`, `tilt`, `face` (default
0.8: a little more frontal = cuter; `-1` mirrors the head to look back) and `glow` behave like
the adult's.

### Anchors
`head`, `crown` (top of the head), `eye_l`, `eye_r`, `nose`, `mouth`, `paw` (near front paw),
`tail_tip`, `center`, `hold_points` = {`front`, `back`, `chest`, `rump`, `belly`}; `curl` adds
`base_l` / `base` / `base_r` and `top` (top of the back).

### Recipes
**Tumbles out of the pod, blinks, wobbles, giggles (s07 "baby")**:
```python
r = core.tween(t, [(c0, 0.0), (c0 + 0.8, 2 * math.pi)], core.ease_out)       # one roll
x = x_pod + r * C.BABY_ROLL_RADIUS * s          # rolls without slipping
draw_specimen(ctx, x, floor_y, s, t, baby=True, pose="tumble", roll=r)
# then: pose="sit", expr="blink", pose_t=t - c1   (blink-blink)
# then: pose="wobble_walk", pose_t=..., x += BABY_WALK_SPEED * s * dt   (a few wobbly steps)
# then: pose="sit", expr="giggle"   (hold >= 1 s so the bounce reads)
```
**Baby giggle**: `expr="giggle"` on any pose. The bounce, squeezed eyes and head wiggle run from
`t` on their own; hold ≥ 1 s and sync a giggle SFX to the start. Sitting, the feet stay
planted (squash-stretch); `held` it hops in the arms. Lead into it with `expr="blink"` (or
`curious` → `giggle` on a cut beat) so it reads as a reaction.

**Scooped up / on his shoulder (s07 "run", s08 "dawn")**: `pose="held"`, `(x, y)` = where the
body sits on the arm / shoulder, draw his hand in `hold`, `expr="giggle"` or `"sleepy"`.

---

## 5. Performance (720x1280 output, ctx scaled 720/1080, s=1, single process)
Measured by `python3 preview/creat_ep2_perf.py` (Episode 1 numbers: `preview/creat_perf.py`
in the Episode 1 project):

| rig | budget | measured |
|---|---|---|
| Impulsivity (all poses) | < 8 ms | 5.0 – 6.1 ms (Episode 1) |
| the thing (all states) / lump | < 3 ms | 0.6 – 1.3 ms (Episode 1) |
| Curiosity form=0 (all poses) | < 10 ms | 4.3 – 4.9 ms (Episode 1) |
| **Curiosity form=1, every pose and expression** (incl. ears / tail_curl / tears) | < 6 ms | **3.5 – 4.9 ms** |
| Curiosity melting (0.3 / 0.6 / 0.9 / 1.0) | < 6 ms | 4.5 / 1.9 / 1.2 / 0.25 ms |
| **baby Joy, every pose x expression** | < 4 ms | **1.3 – 2.9 ms** (run-to-run noise) |
| pod sleeper (s=0.3) / baby pod sleeper (s=0.5) | < 1.5 ms | 0.23 / 0.19 ms |

Bitrate notes: the puddle is two flat fills; the only gradients are two small eye glows per
creature. No particles.

## 6. Preview boards
Episode 2: `python3 preview/creat_ep2_test.py [board ...|all]` → `preview/creat_ep2_<board>.png`

| board | shows |
|---|---|
| `expr` | every expression close-up (s=2), incl. troll with face 0.4 and a flipped look-back |
| `troll` | the s03 troll beat at medium-shot size: wave cycle frames, wave_stand, flipped |
| `tears` | the `tears` ramp 0 → 1, and tears on `sad` / `pleading` |
| `hurt` | the s04 hurt beat at close-up: ears 0.5 → 0.02 with tears 0 → 0.9 |
| `ears` | the `ears` ramp 0 / .25 / .5 / .75 / 1 on sad, pleading, calm |
| `curl` | `tail_curl` 0 / .33 / .66 / 1 on walk, sit, stand |
| `poses` | every new pose (stand-in hood / sleeve bars drawn at the anchors) |
| `melt`, `melt_fine` | melt strip 0 → 1 from the troll wave, the reverse re-form, the puddle on a lit floor; fine steps 0.1–0.5 |
| `lead` | the lead / walk_lookback cycle, 8 phases |
| `glow` | glow 1 / .5 / .2 / .08 at s .55 / .35 / .22 on a dark tunnel, at 720p scale |
| `beats` | perk, proud grin, the hood pull via `hold`, cover_mouth, hopeful look-back, lead, the s08 pile, baby on a shoulder |
| `pile` | s08 close-up: perch on his back + baby curl on top (and variants) |
| `blend` | `pose_from` blends: tug_sleeve→sit, sit→perch, stand→sit, walk→lead |
| `baby_expr`, `baby_poses`, `baby_walk`, `giggle` | baby expressions; every baby pose; toddle cycle + tumble roll; the giggle bounce |
| `baby_scale` | baby next to the adult (walk, sit, the pile) and the pod sleepers (adult and baby) |
| `anchors` | every anchor (pink dots) on the new poses, flipped variants included |
| `ref` | Episode 1 poses and expressions for comparison |

## 7. Limitations
* Expressions switch instantly. Blend the continuous controls (`ears`, `tears`, `tail_curl`,
  `look`, `blink`, `tilt`, `face`, `melt`, `reach`, `form`) or the skeleton (`pose_from`).
* Impulsivity's `sit` and `lie` are frontal only, and its side poses use a fixed 3/4 head.
* The thing has no separate `expr`: its state sets its face.
* At form 0 the specimen keeps its pose skeleton, so its shadow legs are visible inside the mass.
* `flip` mirrors the shading too, so the light side flips with the character.
* The pod sleepers are separate simplified drawings, not the full rigs curled up (use
  `perch` / baby `curl` for close shots).
* `reach_up` reaches up and forward; to reach straight up behind a head, position the creature
  so `a["paws"]` meets the target and let the near paw overlap the hood via `hold`.
* The baby has no `melt`, `tears` or `form`; its `tumble` is drawn as a ball rotated whole, so
  its face turns upside down during the roll (intended).
