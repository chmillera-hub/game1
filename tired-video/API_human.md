# engine/human.py — the people rig

One shared, data-driven full-body rig for every person: **tired** (Tiredness), **embar**
(Embarrassment), **boss**, **guard**, **recep**. Faces carry this film, so most of the
rig is the face system.

```python
from engine.human import draw_person, cycle_speed, SEAT_H, DESK_H, SILL_H, ground_from_seat
# also: draw_tired / draw_embar / draw_boss / draw_guard / draw_recep (ctx, x, y, s=1, t=0, **kw),
#       metrics(who), POSE_NAMES, EXPR_NAMES

a = draw_person(ctx, who, x, y, s, t, pose="stand", expr="neutral", look=(0, 0), mouth=(0, 0),
                face=None, turn=0.0, flip=False, blink=None, blush=None, sweat=0.0, power=0.0,
                outfit="default", headphones=None, bandage=False, hold=None, pose_t=None, seed=0,
                counter=None, glint=0.0, shadow=True, drift=True)   # -> dict of anchors
```

The last four keyword arguments are optional extras:

* `counter`: receptionist counter. `None` means on for `recep` only.
* `glint`: 0..1 lens flash on Embarrassment's glasses.
* `shadow`: soft contact shadow on the ground.
* `drift`: idle eye saccades.

Draw cost is about 5–6 ms per full body at s=1 into a 720x1280 surface (budget is 8 ms). The exact numbers are under Performance below.

---------------------------------------------------------------------------------------------
## 1. Placement, scale, sides

* **`(x, y)`** is the **ground contact point** in the caller's ctx coordinates:
  * **Standing / walking:** the point between the feet; the lowest sole touches `y`.
  * **Seated in a chair** (`sit_chair`, `sit_game`, `sit_desk`): the floor point below the hips. The feet stay planted. The butt sits at `y - SEAT_H[who]*s`, so draw the chair seat there.
  * **Desk and counter top:** `y - DESK_H[who]*s`.
  * **Window sill:** `y - SILL_H[who]*s`.
  * **`sit_floor`, `sit_up`:** the butt and heel contact point. The floor is `y`.
  * **`lie_back`, `heap`:** the lowest body point rests on `y`; `x` is under the hips.
  * **`leap_scared`:** the ground below him. The body floats 170 px*s up and the shadow shrinks.
  * **`climb`:** `(x, y)` is the **sill edge between his hands**. The body hangs below it.
  * **`fall`, `flip`:** the lowest body point. Animate `y` along the arc yourself.
* **`s`**: 1.0 = reference size. Use 0.5 for wide shots and up to about 3 for face close-ups. The ink outline is 5.5 px at s=1 and scales with `s`.
* **Heights at s=1** (soles to hair top, `stand`):

  | who   | height | notes |
  |-------|--------|-------|
  | tired | ≈ 955 to hair mass, 970 to cowlick tip | head with hair ≈ 266 (+cowlick) |
  | embar | ≈ 1045 to hair, 1074 to tuft tip | head ≈ 266 (+tuft) |
  | boss  | ≈ 1040 | head ≈ 257 |
  | guard | ≈ 1000 to cap top | head ≈ 272 |
  | recep | ≈ 995 to bun top | normally seated behind the counter |

  | who | SEAT_H | DESK_H | SILL_H |
  |-----|--------|--------|--------|
  | tired | 175 | 393 | 537 |
  | embar | 224 | 434 | 593 |
  | boss | 233 | 426 | 582 |
  | guard | 189 | 410 | 560 |
  | recep | 193 | 405 | 554 |

  These values are also returned as the anchors `seat`, `desk` and `sill`. If a set gives you a **seat** mark, place a seated person with `y = ground_from_seat(who, seat_y, s)`.
* **`turn`** −1..1 is a 3/4 yaw of the body: − faces screen-left, + faces screen-right. 1.0 is a solid 3/4 (about 49°); up to ±1.6 is allowed (near profile). Values ±0.7..1.0 suit walks, crawls, lean_in and tug. Limbs are real 2.5D: they foreshorten, the far arm and far leg go behind, and the nose and ear move.
* **`flip=True`** mirrors everything, including hold coordinates and angles.
* **Sides `_l` / `_r`** mean the side that appears on **screen-left / screen-right** at `turn=0, flip=False`. So `hand_r`, `lid_r`, `brow_r` and `look_r` are the screen-right ones in a front shot. With `flip=True` they mirror.

## 2. Returned anchors (caller ctx coordinates)

| key | value |
|-----|-------|
| `head` | head centre (eye line) `(x, y)` |
| `face` | centre of the face (between the eyes and mouth) |
| `eye_l`, `eye_r` | eye centres |
| `mouth` | mouth centre (moves with the open mouth) |
| `nose` | nose tip |
| `top` | top of the head / hair (cowlick, tuft, bun, cap) |
| `hand_l`, `hand_r` | `(x, y, ang)`: the **grip / palm contact point** of each hand and the direction it points (radians, screen) |
| `wrist_l`, `wrist_r` | wrists |
| `pocket` | chest pocket. Lab-coat breast pocket for embar; wearer's-left chest for the others (the recorder) |
| `shoulder_l`, `shoulder_r`, `neck`, `hip` | joints |
| `foot_l`, `foot_r` | sole points |
| `ground` | `(x, y)` as passed |
| `seat`, `desk`, `sill` | furniture heights above `ground` (see §1) |
| `speed` | screen-x px/s that keeps the planted foot from sliding, for the current pose, `turn`, `s` and `flip` (0 for non-locomotion) |
| `cycle` | the cycle length in seconds (or `None`) |
| `blink` | the blink value used this frame |

Locomotion: `cycle_speed(who, pose, turn)` gives the same speed at s=1. Move the character by `speed * dt` each frame. Screen-x speeds at s=1, turn=1 (they scale by `sin(turn·0.86)`):

| who | walk | run | run_panic | scream_run | tiptoe | crawl | stumble |
|-----|------|-----|-----------|------------|--------|-------|---------|
| tired | 436 | 1097 | 1396 | 1335 | 231 | 150 | 195 |
| embar | 514 | 1004 | 1277 | 1222 | 281 | 183 | 226 |
| boss | 637 | 1341 | 1707 | 1633 | 395 | 183 | 238 |
| guard | 470 | 1178 | 1499 | 1434 | 248 | 160 | 203 |
| recep | 547 | 1163 | 1480 | 1415 | 246 | 160 | 206 |

## 3. Poses

`pose` can be:

* a **name**;
* a **blend tuple** `(a, b, k)`, exactly what `core.state_at` returns. Each side may itself be a name or a dict;
* a **dict of joint overrides**. The dict layers on top of `"stand"`, or on top of `"base": "<pose>"` when given.

Every pose is numeric, so any two poses blend smoothly: hand shapes interpolate finger by finger, and seated poses keep the feet planted while blending. Cycles use `pose_t` (default `t`) for their phase.

`l`/`r` hand notes below are for a front shot. Hands are always the cartoon 4-finger rig. The shapes are `open relaxed fist point grip splay pinch flat claw cup`.

### Static
| pose | looks like | hands |
|------|-----------|-------|
| `stand` | neutral stand (character posture: Tiredness slouches; the Boss stands with hands behind her back; the Guard has elbows out) | relaxed at the sides |
| `slouch` | extra slouch, head forward, knees soft | hanging |
| `arms_crossed` | arms folded across the chest | l over r, at the chest |
| `hands_pockets` | hands hidden (Tiredness: hoodie pocket; others: trouser pockets) | hidden at the belly / hips |
| `hands_behind_back` | hands clasped behind | behind the back (hidden) |
| `attention` | stiff, arms straight at the sides, chin up, no sway (**no salute**) | flat at the thighs |
| `awkward` | shoulders up to the ears, hands clasped low | together in front of the crotch |
| `sheepish` | scratching the back of his head | r behind the head; l hanging |
| `plead` | palms pressed together at the chest, leaning in | together at the chest centre, pointing up |
| `cover_eyes` | both hands over his eyes, elbows down | over the eyes |
| `peek` | hands over the eyes, fingers splayed, eyes still visible | over the eyes (splay) |
| `facepalm` | one hand on the face, head dropped | r on the face |
| `shrug` | shoulders up, forearms out, palms up | open, palm-up, beside the hips |
| `point` | r arm out sideways, index pointing **with the thumb up** | r: point; l hanging |
| `hold_arm` | clutching his own forearm across the body | r grips the l forearm |
| `lean_in` | bent forward at the waist, peering (use turn ±0.8) | behind the back |
| `look_window` | leaning forward, hands on the sill line (`SILL_H`) | flat on the sill, in front |
| `sit_chair` | seated, hands on the thighs | on the knees |
| `sit_game` | seated, hunched, holding a **game controller** (drawn by the rig) | gripping the pad; thumbs on top |
| `sit_desk` | seated, forearms on the desk (`DESK_H`) | on the desk in front |
| `sit_floor` | on his butt, legs splayed forward, dazed tilt | flat on the floor behind |
| `heap` | crumpled upside-down pile, legs in the air, face visible sideways | flopped out |
| `lie_back` | lying flat (body horizontal, head to screen-left) | open, at the sides |
| `sit_up` | groggy, propped up on one arm | r on the floor behind; l on the knee |
| `crouch` | deep squat, searching low | r reaching forward low; l on the knee |
| `cover_sweater` | bent over a desk, pressing a lump down | both flat on `DESK_H` |
| `back_away` | leaning back, small open hands up at chest height (palms out) | open at the chest |
| `arm_jerk` | r arm jerking straight out sideways, body recoiling | r splay; l hanging |
| `hands_up_small` | small "whoa", forearms up, palms out at shoulder height (bent elbows) | open beside the shoulders |
| `catch` | lunging, arms thrust forward grabbing | claws in front |
| `cradle` | gently holding a dog-sized creature against the chest. **r arm cups underneath (behind the creature), l arm wraps in front** | `hold` gets `"both"`. Best at turn 0..1, or mirror with flip |
| `carry_front` | carrying a box or cage in both hands, leaning back | grips on the box sides; `hold` "both" |
| `hold_side` | one hand down at the side holding a handle | r grip at the side; `hold` "r" |
| `present` | palm-up offering of a small item (the prop is drawn **on top of** the palm) | r cup in front |
| `slide` | leaning over a desk, one arm stretched forward along it | r flat far forward; l on the desk |
| `leap_scared` | whole body in the air, arms and legs splayed in fright | splayed, above the shoulders, bent elbows |
| `climb` | pulling himself over a sill, legs dangling (anchor = sill edge) | flat on the sill |
| `pick_up` | deep crouch, reaching to the ground | r grip at the floor |
| `throw` | wind-up: r hand cocked up behind the head, l arm forward | r grip (`hold` "r") above/behind the head |
| `headphones_on` | both hands at the ears lifting the headphones. The hands track the cups for any `headphones` value | grips on the cups |
| `yawn` | body yawn: hand to the mouth, head back (pair with `expr="yawn"`) | r at the mouth |
| `fall` | midair, limbs flailing up (auto-wiggles, 0.5 s) | splayed |
| `flip` | tucked ball (rotate it with `{"base": "flip", "rot": angle}`) | grips on the shins |

### Cycles (period in seconds; drive with `pose_t`; all blendable)
| pose | period | looks like / hands |
|------|--------|--------------------|
| `walk` | 1.00 | relaxed walk, arms counter-swing |
| `run` | 0.56 | lean forward, pumping fists, coat trails |
| `run_panic` | 0.44 | running, arms flailing out front (splayed hands) |
| `scream_run` | 0.46 | running, arms up and flailing (bent elbows) |
| `tiptoe` | 1.40 | exaggerated sneaky high-knee tiptoe; hands up at the chest with fingers dangling |
| `crawl` | 1.20 | on all fours, torso horizontal (turn ±0.8..1); hands flat on the floor |
| `stumble` | 1.60 | groggy wobbly walk, whole body wobbling |
| `bang_door` | 0.50 | r fist pounding forward at head height; l flat on the door |
| `wring_hands` | 0.80 | hands clasped at the chest, twisting, shoulders up |
| `shake_arms` | 0.25 | panicked shaking of both arms (splay) |
| `tap_foot` | 0.50 | arms crossed + r foot tapping (toes lift on the heel) |
| `roll_hand` | 0.70 | "go on": r hand rolling in circles at chest height, palm up |
| `tug` | 1.20 | leaning back hauling on something with both hands (`hold` "both" between the grips) |
| `struggle_hold` | 0.90 | arms locked around a writhing thing, body straining and swaying (`hold` "both") |
| `game` | 0.30 | `sit_game` + thumbs mashing the controller |
| `type` | 0.35 | `sit_desk` with curled typing fingers moving |

### Joint keys for pose dicts
All angles are in radians and **absolute**, not inherited from the spine. Pitch `p`: 0 = hanging down, +π/2 = pointing forward (toward camera at turn 0), π = up. Abduct `o`: + = out to that limb's own side.

* **Global keys:**
  * `turn` (added to the kwarg);
  * `dx`, `dy` (px at s=1);
  * `rot` (screen roll about the hips);
  * `lift` (px up);
  * `plant` (1 = feet on the ground, 0 = use `hip_h`);
  * `hip_h` (hip height in leg lengths, or `"seat"`);
  * `plant_butt`, `plant_all` (ground-lock on the butt or the whole body);
  * `lean` (bend forward at the waist);
  * `chest`, `side` (lean sideways), `twist` (upper-body yaw), `hip_roll`, `hunch` (0..1 shoulders up);
  * `neck`, `nod`, `tilt`, `head_yaw`;
  * `breath`, `sway` (idle multipliers);
  * `posture` (0..1 weight of the character's built-in posture);
  * `coat_trail`.
* **Arms `al_*`, `ar_*`:**
  * Forward kinematics: `p o e eo w` (shoulder pitch/abduct, elbow bend, forearm abduct, wrist).
  * `h` is a hand name, and `tf` = ±1 sets the thumb side (−1 shows the palm). `hide` hides the hand.
  * IK: `ik` (0..1 weight) + `tx ty tz`, a ground target in fractions of the height: x outward, y above the ground (or `"desk"`/`"sill"`/`"seat+0.1"`), z forward.
  * Head-relative IK: `th`, `hx hy hz` (head px).
  * Other targets: `grab` reaches the other forearm; `cup` reaches the headphone cup.
  * `wa wabs` set an absolute hand angle (0 = toward the facing side) and its weight. `bend` = ±1 puts the elbow out/down or in.
  * `layer` = `back|mid|front`. `thumb` and `fing` are animation offsets.
* **Legs `ll_*`, `lr_*`:** `p o k ko a` (hip pitch/abduct, knee, shin abduct, ankle; + = toes up).
* Waves for custom cycles: `{"base": "stand", "period": 0.6, "ar_e": W(1.0, 0.4, 0.0)}`, where `W(base, amp, phase, amp2, phase2, r)` is in `engine.human`.

## 4. Face system

### Expressions (`expr`: a name, an `(a, b, k)` tuple, or a dict of deltas)
* **Basics:** `neutral`, `bored` (Tiredness's default mood: heavier lids, flat mouth), `deadpan`, `annoyed`, `unamused` (one brow up, lids heavy, lips pressed), `squint`, `sigh`, `content` (happy closed arcs), `soft_smile`, `curious` (one brow up, head tilt).
* **Big reactions:** `surprised`, `alarmed`, `scream` (head stretches, jaw drops), `pain` (squeezed eyes, clenched teeth), `groggy` (uneven heavy lids, unfocused), `dazed` (lids uneven, eyes drifting apart), `determined`, `awe` (lids fully open, mouth slightly open, big catchlights), `sad`.
* **Embarrassment's nervous range:** `nervous_smile` (awkward toothy grin), `panic`, `terrified`, `relieved`, `pleading` (huge wet pupils, worried brows), `guilty` (eyes down and away), `frozen_shock` (eyes huge, tiny pupils and no iris, mouth a tight wobbly line), `whisper` (small pursed "oo"), `sheepish`, `fake_cool` (smirk + one brow, wobbling).
* **Others:** `cold`, `stern` (the Boss), `yawn`.

All expressions work on every character. They are tuned per character:

* **Tiredness:** lid-opening deltas are halved, so his lids almost never open. `determined` and `awe` get an extra lid lift (lid ≈ 0.1 and ≈ 0.0 against his resting 0.45): that is the payoff.
* **Boss:** every expression delta is ×0.4, so she barely moves. Your `face=` deltas are not scaled, so a scene's 0.05 is a real 0.05.
* **Blush:** expression-default blush is mostly Embarrassment's; others get ×0.3.

A dict `expr` uses EXPR conventions: the multiplier keys `pupil iris hl eye_size width focus` are absolute values, and all other keys are deltas.

### `face=` additive deltas (summed on top of the expression)
Eye keys also accept `_l` / `_r` (one eye only, e.g. `lid_r`, `brow_l`). Values add to the character's resting face plus the expression; results are clamped.

| key | range | effect |
|-----|-------|--------|
| `lid` | −0.5..1 | upper lid closure (0 = open; Tiredness rests at 0.45, Boss 0.32, recep 0.5). Negative values widen the eye |
| `lid_ang` | −1..1 | + droops the outer lid (sad/sleepy), − droops the inner lid (intense/angry) |
| `lower` | 0..1 | lower lid raise (squint; at ≥0.8 with closed lids gives happy arcs) |
| `brow` | −1..1 | brow height (1 ≈ 20 px) |
| `brow_ang` | −1..1 | + inner ends up (worried/sad), − inner ends down (angry) |
| `brow_in` | −1..1 | extra bend of the inner third |
| `brow_out` | −1..1 | lifts / drops the outer tail |
| `pupil` | −0.8..+1 | pupil size delta (shock −0.5, adoring +0.4) |
| `iris` | −1..+0.5 | iris size delta (−1 = no iris: pure tiny-pupil shock) |
| `hl` | −1..+1 | catchlight size (bigger = wetter, more emotional) |
| `eye_size` | −0.3..+0.5 | whole-eye scale (takes) |
| `look_x`, `look_y` | −1..1 | gaze offset added to `look` (also per eye) |
| `look_l`, `look_r` | `(x, y)` | per-eye gaze offset (cross-eye: `look_l=(0.8,0), look_r=(-0.8,0)`; wall-eye: the reverse) |
| `focus` | −1..0 | unfocused eyes (pupils swell slightly) |
| `curve` | −1..1 | mouth smile (+) / frown (−) |
| `width` | −0.6..+0.6 | mouth width delta |
| `asym` | −1..1 | corner asymmetry (+ raises the screen-right corner) |
| `smirk` | −1..1 | one corner up with a dimple (sign = side, + is screen-right) |
| `press` | 0..1 | lips pressed thin, tension marks |
| `frown` | 0..1 | corners pulled down + chin bunch |
| `open` | 0..1 | mouth open (added to lip-sync) |
| `lip_up`, `lip_low` | 0..1 | upper lip raise (shows teeth) / lower lip drop |
| `teeth` | 0..1 | teeth (≥0.5 with a small opening = clenched grin) |
| `tongue` | 0..1 | tongue |
| `jaw` | −1..1 | jaw / mouth shift sideways |
| `wobble` | 0..1 | wobbly mouth line (nerves, frozen shock) |
| `cheek` | 0..1 | cheek puff (widens the jaw) |
| `flare` | 0..1 | nostril flare |
| `head_tilt` | −0.4..0.4 | head roll (radians) |
| `head_turn` | −1..1 | head yaw on top of the body `turn` |
| `head_nod` | −0.5..0.5 | + chin down (features shift down) |
| `squash` | −0.3..0.3 | head squash (+) / stretch (−) for takes |
| `bags` | −1..1 | under-eye bags (Tiredness rests at 1) |
| `lidshade` | −0.5..0.5 | shading on heavy lids |
| `blush` | 0..1 | blush delta (the `blush=` kwarg overrides the total) |

### Other face inputs
* **`look=(x, y)`:** gaze, −1..1 (up to ±1.25 for extreme). Lids follow the gaze: looking down drops them, looking up lifts them. Even Tiredness's heavy lids keep the iris readable looking far up or down.
* **`mouth=(open, wide)`:** pass `info.mouth(who, t)` directly. It opens the mouth naturally on top of the expression shape (`wide` + = "ee", − = "oo"). A pressed mouth relaxes while talking. Closed mouths keep all their curve, smirk and press.
* **`blink`:** `None` gives automatic blinks (`core.blink_amount`, per-character seed and rate: Embarrassment blinks a lot, the Boss rarely, Tiredness slowly). A float 0..1 overrides. Idle eye drift (tiny saccades) runs unless `drift=False`.
* **`power` 0..1 (Tiredness):**
  * the irises turn teal, with a bright ring;
  * the pupils tighten;
  * the eyes get a screen-blended teal glow that dims as the lids close.
* **`blush` 0..1 (`None` = expression default):**
  * 0.3: pink cheeks;
  * 0.7: the face is red;
  * 1.0: beet red, ears and neck included, with heat squiggles above the head.
* **`sweat` 0..1:** 1–3 beads at the visible temple; above 0.3 a drop slides down the cheek and loops.
* **`glint` 0..1:** a flash across Embarrassment's lenses. The lenses always carry small glints.

## 5. Accessories and outfits
* **`headphones`** (Tiredness):
  * `None`: no headphones.
  * `"neck"`: cups on the collar, band behind the neck.
  * `"on"`: on the ears, band over the hair.
  * a float 0..1: the transition. Pair it with `pose=("stand", "headphones_on", k)`; the hands follow the cups automatically.
* **`bandage`:** `True` (= `"r"`, the screen-right forearm in a front shot) or `"l"`. The sleeve is pushed up to the elbow, showing a white wrap.
* **`outfit`** (Tiredness):
  * `"default"`: hoodie with hood, drawstrings and kangaroo pocket; sweatpants; fuzzy slippers.
  * `"printer"`: beige polo with collar and placket, short sleeves, khakis, teal lanyard + badge, brown shoes. Pass `headphones=None`.
  * `"sewer"`: hoodie, damp hair (drooping cowlick, drips), two band-aids (forehead, cheek), smudges.
* **Built in per character:**
  * Embarrassment: round glasses, freckles, lab coat with pens in the breast pocket. The coat tails lag behind the legs and trail when running.
  * Boss: teal HushCorp pin, cheekbones.
  * Guard: cap with badge, mustache, shoulder radio, chest badge, belt.
  * Receptionist: headset with mic, name badge, and the counter (`counter=False` if the set draws its own; its top is `DESK_H`).

## 6. Props: `hold`
`hold(ctx, side, hx, hy, ang)` is called in the **caller's** coordinates at the right z-order:

* `side` is `"r"` (or `"l"`) for one-hand poses, with `hx, hy` = that hand's grip point and `ang` = the hand direction.
* For two-hand poses (`cradle carry_front tug struggle_hold`), `side == "both"`, `hx, hy` = the midpoint between the hands, and `ang` = the angle of the hand-to-hand line.
* Z-order: the prop is drawn **before** the front-most holding arm, so fingers wrap over handles and `cradle`'s near arm crosses in front of the creature. In `present` it is drawn **after** the hand (the item sits on the palm).
* Scale your prop by your own `s`.
* For any other pose, read `a["hand_r"]` and draw the prop yourself after `draw_person`, or add `"hold": 1` (right hand) or `2` (both hands) to a pose dict.

```python
def cage(ctx, side, x, y, ang):
    with saved(ctx, x, y, s, 0): draw_cage(ctx)
draw_person(ctx, "embar", x, y, s, t, pose="carry_front", hold=cage)
```

## 7. Tips for scene animators
* **Blend poses with `state_at`:** `pose=state_at(t, [(0, "stand"), (cue, "arms_crossed")], 0.3)`. Expressions blend the same way: `expr=state_at(t, [(0, "bored"), (c, "annoyed")], 0.2)`.
* **Eyeroll:**
  * tween `look` from (0, 0) → (0.5, −1.2) → (0, 0) over about 0.6 s;
  * add `face={"lid": 0.1}` at the end;
  * for Tiredness, add `head_tilt` 0.05 and a small `head_nod` −0.1 at the top of the roll.
* **Slow blink:** `blink=tween(t, [(t0, 0), (t0 + .25, 1), (t0 + .7, 1), (t0 + 1.0, 0)])` (lids hold shut, then drag back up). Tiredness can reopen to `lid +0.1` for extra fatigue.
* **Double take:**
  1. glance at it: `look` x → 1 for 0.15 s;
  2. look back away: `look` x → 0;
  3. snap back: `head_turn` +0.3, `expr` → `surprised`, `squash` −0.1 then 0, plus `pupil` −0.3.
* **Held subtle reaction:** keep `expr` fixed and move one or two `face` keys by 0.05–0.15 with `tween` easing. For example:
  * a lid drop `{"lid": 0.1}`;
  * one brow `{"brow_r": 0.2}`;
  * eyes sliding sideways `look=(−0.7, 0)` and back;
  * a lip press `{"press": 0.4}`.

  Blinks and drift keep it alive. The Boss reads at close-up with `{"lid": 0.05}`.
* **Talking:** always pass `mouth=info.mouth(who, t)`. Combine it with an expression and the mouth shape stays in character.
* **Walking:** move `x += a["speed"] * dt` (or `cycle_speed(...) * s`) and pass `pose_t=t - t_start` so the cycle starts on a contact pose.
* **Facing:** `turn=1` (facing right) vs `turn=-1` (facing left). Use `flip=True` if you want the identical drawing mirrored.
* **Facial-feature anchors** (`eye_l`, `mouth`, `top`...) are returned for placing tears, sweat drops, speech-bubble tails, impact stars, and so on.

## 8. Preview boards (`python3 preview/human_test.py <board>|all|timing`)
| board | file |
|-------|------|
| turnarounds (each who, turn −1/0/1, outfits, flip, headphones) | `preview/human_turn.png` |
| face close-ups, every expression, front / 3/4 | `preview/human_faces_<who>.png`, `preview/human_faces34_<who>.png` |
| s=0.5 readability | `preview/human_small.png` |
| all poses, front / 3/4 | `preview/human_poses_<who>.png`, `preview/human_poses34_<who>.png` |
| locomotion cycles (8 phases) | `preview/human_cycles.png` (embar), `preview/human_cycles_tired.png` |
| gesture cycles | `preview/human_gestures.png`, `preview/human_gestures_embar.png` |
| subtle acting (Tiredness lid/brow/eyes/press; Boss 0.05 steps) | `preview/human_subtle.png` |
| blush ramp + sweat; power ramp | `preview/human_blush.png` |
| power at s=3 | `preview/human_power_close.png` |
| gaze: up/down/left/right, cross-eye, wall-eye, blinks | `preview/human_eyes.png` |
| hand shapes | `preview/human_hands.png` |
| hold z-order, pose/expr blends | `preview/human_holds.png` |
| headphones neck→on | `preview/human_headphones.png` |

## 9. Performance and limitations
* **Performance:** about 4.7–6.2 ms per full body at s=1 into a 720x1280 surface (`timing` board), and about 5.5 ms for an s=3 close-up. The cost is mostly cairo rasterisation. Limbs use fill-only outlines, and the curve tolerance is set to 0.3 device px.
* **Limitations:**
  * The rig is 2.5D: at full profile (`turn` ±1.6) faces are still a hard 3/4.
  * Poses that reach straight at the camera (`catch`, `lean_in`, `crawl`) read best at turn ±0.6..1.
  * Hands are drawn flat in the screen plane. A pointing finger aimed at the camera does not foreshorten.
