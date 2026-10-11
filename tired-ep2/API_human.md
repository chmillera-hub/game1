# engine/human.py — the people rig

One shared, data-driven full-body rig for every person: **tired** (Tiredness), **embar**
(Embarrassment), **boss**, **guard**, **recep**. Faces carry this film, so most of the
rig is the face system.

```python
from engine.human import draw_person, cycle_speed, SEAT_H, DESK_H, SILL_H, CRATE_H, ground_from_seat
# also: draw_tired / draw_embar / draw_boss / draw_guard / draw_recep (ctx, x, y, s=1, t=0, **kw),
#       metrics(who), POSE_NAMES, EXPR_NAMES, W (waves), K (keyframes)

a = draw_person(ctx, who, x, y, s, t, pose="stand", expr="neutral", look=(0, 0), mouth=(0, 0),
                face=None, turn=0.0, flip=False, blink=None, blush=None, sweat=0.0, power=0.0,
                outfit="default", headphones=None, bandage=False, hold=None, pose_t=None, seed=0,
                counter=None, glint=0.0, shadow=True, drift=True,
                # Episode 2 additions (all optional; defaults = Episode 1 behaviour)
                hood=0.0, tears=0.0, glasses_tilt=0.0, glasses_dx=0.0, glasses_dy=0.0,
                hold_sides=None, hold_layer=None, reach=None, pocket_side=None)   # -> anchors
```

The last four Episode 1 keyword arguments are optional extras:

* `counter`: receptionist counter. `None` means on for `recep` only.
* `glint`: 0..1 lens flash on Embarrassment's glasses.
* `shadow`: soft contact shadow on the ground.
* `drift`: idle eye saccades.

The Episode 2 keyword arguments are explained where they belong:

| kwarg | what | section |
|-------|------|---------|
| `hood` 0..1 | Tiredness's hood: down behind the neck → up and low over his eyes | §5 |
| `tears` 0..1 | wet glisten on the lower lids; ≥0.7 a single tear wells and rolls | §4 |
| `glasses_tilt`, `glasses_dx`, `glasses_dy` | askew glasses (radians / px at s=1) | §5 |
| `hold_sides` | which hands get the `hold` callback: `"r"`, `"l"`, `"lr"`, `"both"` | §6 |
| `hold_layer` | prop z-order: `None`/`"auto"`, `"back"`, `"front"` (after the arm), `"top"` | §6 |
| `reach` | world-space hand targets `{"r": (x, y), "l": (x, y)}` in YOUR coordinates | §6 |
| `pocket_side` | which chest pocket the `pocket` anchor (and Emb's drawn pocket) uses | §5 |

Every Episode 1 call still works unchanged. The visible changes on old calls are bug fixes, all listed in "Episode 2 notes" at the end.

Draw cost is about 5–6 ms per full body at s=1 into a 720x1280 surface (budget is 8 ms). The exact numbers are under Performance below.

---------------------------------------------------------------------------------------------
## 1. Placement, scale, sides

* **`(x, y)`** is the **ground contact point** in the caller's ctx coordinates:
  * **Standing / walking:** the point between the feet; the lowest sole touches `y`.
  * **Seated in a chair** (`sit_chair`, `sit_game`, `sit_desk`): the floor point below the hips. The feet stay planted. The butt sits at `y - SEAT_H[who]*s`, so draw the chair seat there.
  * **Desk and counter top:** `y - DESK_H[who]*s`.
  * **Window sill:** `y - SILL_H[who]*s`.
  * **`sit_floor`, `sit_up`:** the butt and heel contact point. The floor is `y`. **Episode 2 fix:** in side-on views the legs are now laid on the floor (progressively from |turn| ≈ 0.25 to fully at ≈ 0.8), so the butt *and* the heels sit on `y` (before, the butt floated above a side-on floor). Front views keep the Episode 1 look (feet lower than the butt, the floor recedes toward camera). The floor hands lie flat, pointing back.
  * **`sit_crate`** (Ep2): the floor point below the hips; the feet are planted on `y` and the butt sits on a low box whose top is `y - CRATE_H[who]*s` (anchor `crate`). CRATE_H: tired 126, embar 164, boss 173, guard 136, recep 140 (about 0.72 × SEAT_H).
  * **`phone_thumb`** (Ep2): seated like `sit_chair` (chair / bed edge at `SEAT_H`).
  * **`lie_front`, `phone_thumb_lie`, `flop`** (Ep2): `y` is the bed surface (the body's lowest point), `x` is under the hips. In `lie_front` the head rests ≈48 px·s above `y` (it is on the pillow: draw the pillow there); the head points to screen-right. These poses carry their own profile turn (+1.45), so call them with `turn=0` and use `flip=True` to put the head on the left.
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
| `pocket` | chest pocket. Lab-coat breast pocket for embar; wearer's-left chest for the others (the recorder). Side selectable with `pocket_side` (§5) |
| `shoulder_l`, `shoulder_r`, `neck`, `hip` | joints |
| `foot_l`, `foot_r` | sole points |
| `elbow_l`, `elbow_r`, `knee_l`, `knee_r` | joints (Ep2) |
| `ground` | `(x, y)` as passed |
| `seat`, `desk`, `sill`, `crate` | furniture heights above `ground` (see §1; `crate` is new) |
| `speed` | screen-x px/s that keeps the planted foot from sliding, for the current pose, `turn`, `s` and `flip` (0 for non-locomotion). **Ep2 fix:** dict poses whose `base` is a cycle (`{"base": "walk", "lean": 0.1}`, `{"base": "sneak"}`) now return the real speed (was 0) |
| `cycle` | the cycle length in seconds (or `None`) |
| `blink` | the blink value used this frame |
| `order`, `layers` | (Ep2) the arm draw order this frame, e.g. `("l", "r")` = r drawn last, and each arm's layer `("mid", "front")`. Use them to test for z-order pops |
| `hood_rim` | (Ep2) the hood rim centre (where the under-rim glow sits), or `None` when the hood is down |

Locomotion: `cycle_speed(who, pose, turn)` gives the same speed at s=1. Move the character by `speed * dt` each frame. Screen-x speeds at s=1, turn=1 (they scale by `sin(turn·0.86)`):

| who | walk | run | run_panic | scream_run | tiptoe | crawl | stumble | sneak | walk_eyes_closed |
|-----|------|-----|-----------|------------|--------|-------|---------|-------|------------------|
| tired | 436 | 1097 | 1396 | 1335 | 231 | 150 | 195 | 276 | 456 |
| embar | 514 | 1004 | 1277 | 1222 | 281 | 183 | 226 | 374 | 538 |
| boss | 637 | 1341 | 1707 | 1633 | 395 | 183 | 238 | 340 | 669 |
| guard | 470 | 1178 | 1499 | 1434 | 248 | 160 | 203 | 326 | 491 |
| recep | 547 | 1163 | 1480 | 1415 | 246 | 160 | 206 | 296 | 478 |

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
| `stand` | neutral stand (character posture: Tiredness slouches; the Boss stands with hands behind her back; the Guard has elbows out) | relaxed at the sides. Ep2: the Boss also walks / sneaks / tiptoes with her hands clasped behind her |
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
| `shrug` | **BIG** clear shrug (Ep2: retuned): shoulders right up to the ears, forearms out wide and level, palms up, head tilted | open, palm-up, out to the sides at waist height |
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

### Episode 2 static poses
| pose | looks like | hands / staging |
|------|-----------|-----------------|
| `sit_crate` | sitting on a low box, elbows on the knees, forearms hanging, head hanging: tired | relaxed, dangling between the knees. Box top at `CRATE_H` (anchor `crate`). Reads best at turn 0.6..1 |
| `punch_wind` | anticipation: body coiled back, punching fist pulled back by the hip, other fist up | fists. **Punches use the l arm = the NEAR arm when turn > 0**; stage at turn 0.8..1.2 and use `flip=True` to punch screen-left |
| `punch` | straight punch forward at shoulder height, arm locked, body leaning into it, rear fist at the chest | fist (the grip point is the knuckles, see `hand_l`) |
| `guard_fists` | ready stance between punches (the `punch_cycle` rest) | fists at the chest |
| `haul` | both hands gripping a lever above head height and pulling DOWN: leaning far back, front leg braced, back knee bent, shoulders up (pair with `expr="pain"` / `face={"teeth": 1}`) | grips forward-up above the head. Stage at turn 0.8..1.3 (at turn 0 the arms cover the face). Put the hands on your lever with `reach=` (§6) |
| `lie_front` | lying face-down on a bed, head turned sideways on the pillow so the face is visible, arms up by the head (tucked behind it) | relaxed, peeking above the head. `turn=0` (pose carries its profile), `flip` for head-left. `(x, y)` = bed contact under the hips |
| `flop` | falling forward toward the bed (stiff plank, arms forward, face turning to camera). Built to blend `stand → flop → lie_front` | open, forward. Same staging as `lie_front` |
| `hand_out` | offering something on an open palm, arm extended toward the other person | r cup, palm up; `hold` is drawn ON the palm (like `present`). Best at turn 0.6..1 |

### Episode 2 cycles (period s)
| pose | period | looks like / hands |
|------|--------|--------------------|
| `sneak` | 1.30 | **upright** crouch sneak: knees bent, torso upright, short careful steps, arms close with hands at the belly (never butt-up). Locomotion: use `speed` |
| `punch_cycle` | 1.20 | one-shot style punch built from keyframes: guard (0) → wind-up (phase 0.40) → **the fist lands at phase 0.52 (0.62 s)** → held to 0.75 → back to guard. Drive with `pose_t = t - t0`; freeze on contact with `pose_t=min(t - t0, 0.62)` |
| `haul_strain` | 0.36 | `haul` plus small straining trembles |
| `wave_small` | 0.70 | small bent-elbow wave (r arm): elbow out low, forearm up, open palm toward camera, hand at shoulder / chest height (never a raised straight arm). Reads at turn −0.3..1; for a screen-left facing use `flip=True` |
| `phone_thumb` | 0.42 | seated (`SEAT_H`), hunched over a phone held in both hands, thumbs tapping; `hold` gets `"both"` = the phone centre |
| `phone_thumb_lie` | 0.42 | `lie_front` with the NEAR (l) hand up by the head holding a phone, thumb tapping; `hold` gets `"l"` |
| `walk_eyes_closed` | 1.05 | confident stride for walking blind under the hood: chin up, chest out, bigger loose arm swing, less slouch |

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
  * `coat_trail`;
  * Ep2: `hand_top` (+1 = r hand drawn on top when both hands sit at about the same depth; default l, like `arms_crossed` / `cradle`), `head_face` (0..1: turn the face to the camera whatever the body turn), `hold_hand` (−1 = the pose's one-hand `hold` is the l hand), `pillow` (px: with `plant_all`, the head may rest this much above the ground line).
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
* Ep2: `K((phase, value), ...)` gives keyframed (eased, wrapping) values for asymmetric cycles, e.g. `{"base": "stand", "period": 1.0, "ar_p": K((0, 0.1), (0.4, -0.6), (0.5, 1.5), (0.8, 1.5))}`.
* Ep2: waves in a dict whose `base` is a cycle now use that cycle's period unless the dict gives its own `"period"` (before, they silently used 0.5 s). A dict with its own `"period"` reports it in the `cycle` anchor.

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
* **`look=(x, y)`:** gaze, −1..1 (up to ±1.25 for extreme). Lids follow the gaze: looking down drops them, looking up lifts them.
  * **Episode 2 fix (heavy lids):** the gaze-driven droop is soft-capped (`GAZE_LID`: Tiredness never droops past lid 0.6 from gaze alone, others 0.64–0.66), so `look=(0, 1)` on Tiredness shows his irises looking down instead of closing his eyes. Drop the old −0.15..−0.3 `lid` corrections: they now over-open him.
  * With heavy lids the iris settles toward the middle of the *visible* opening, so a level gaze (`look y=0`) reads as straight ahead, not down, and the pupil stays visible.
  * Looking up lifts Tiredness's lids less than before (gain 0.16), to protect the s06 payoff: only `expr="determined"/"awe"` or explicit negative `lid` really open his eyes.
  * A fully closed lid now stays fully closed with `lid_ang` (sad / bored blinks used to leave a sliver open).
* **`mouth=(open, wide)`:** pass `info.mouth(who, t)` directly. It opens the mouth naturally on top of the expression shape (`wide` + = "ee", − = "oo"). A pressed mouth relaxes while talking. Closed mouths keep all their curve, smirk and press.
* **`blink`:** `None` gives automatic blinks (`core.blink_amount`, per-character seed and rate: Embarrassment blinks a lot, the Boss rarely, Tiredness slowly). A float 0..1 overrides. Idle eye drift (tiny saccades) runs unless `drift=False`.
* **`power` 0..1 (Tiredness):**
  * the irises turn teal, with a bright ring;
  * the pupils tighten;
  * the eyes get a screen-blended teal glow that dims as the lids close;
  * **Ep2, eyes CLOSED** (`blink=1`, `expr="content"`, `face={"lid": 0.6}`...): a thin teal light runs along the lash line plus a faint glow just under it, so the sense still reads in the dark;
  * **Ep2, hood over the eyes** (`hood` near 1): the eye glow is masked by the hood; instead teal light leaks along the underside of the hood rim at each eye (anchor `hood_rim`).
* **`tears` 0..1 (Ep2):** a wet glisten pooling on the lower lids with bigger catchlights (0.3 = glassy, 0.6 = brimming). From 0.7 a single tear wells at the outer corner of the more frontal eye; tween 0.7 → 1.0 to make it roll down the cheek (it stays at the cheek at 1.0). `face={"tear": x}` adds to it. Works on every character (try `embar` + `pleading`).
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
* **`hood` 0..1 (Ep2, Tiredness / any hoodie):**
  * `0`: down behind the neck (the Episode 1 lump, unchanged).
  * `0 → 0.4`: the hood rises behind the head (a dark shell growing out of the neck lump).
  * `0.4 → 1`: the rim slides forward over the crown, the forehead and finally **low over the eyes**; the side panels close in on the cheeks.
  * `1`: eyes and brows hidden under the rim; nose (its usual bottom curve), mouth, cheeks and jaw visible; the hood shadows the upper face; a seam and soft creases at close-up. Raised brows nudge the rim up a hair (a surprise still reads under the hood).
  * In-between values are all valid (e.g. 0.8 = rim on the brows, eyes peeking out). It follows head turn / tilt / nod (`face={"head_turn": ...}` makes him "look" around blind). Tween it over ~0.5–0.8 s: `hood=tween(t, [(t0, 0), (t0 + .7, 1)])`.
  * With `power`, see §4 (glow under the rim). Headphones still work (they sit over the hood).
* **`glasses_tilt` (radians), `glasses_dx`, `glasses_dy` (px at s=1, head space) (Ep2, Embarrassment):** askew glasses without monkeypatching. The frame rotates about the bridge and sags 12 px·|tilt| (one lens drops), the temples stay hooked on the ears. 0.1–0.15 = slightly crooked, 0.3 + `glasses_dy=10` = knocked half off. Works in 3/4.
* **`pocket_side` (Ep2):** `None`/`"r"` (default, Episode 1: the wearer's left = screen-right chest in a front shot), `"l"`, or `"near"` (the side toward the camera for this facing: screen-left when turn > 0, screen-right when turn ≤ 0). It moves the `pocket` anchor, and for Embarrassment the drawn breast pocket with its pens too, so the recorder is never hidden behind the far arm. Choose it per shot: with `"near"` the pocket jumps sides when the turn crosses 0.
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
* For two-hand poses (`cradle carry_front tug struggle_hold phone_thumb`), `side == "both"`, `hx, hy` = the midpoint between the hands, and `ang` = the angle of the hand-to-hand line.
* Z-order: the prop is drawn **before** the front-most holding arm, so fingers wrap over handles and `cradle`'s near arm crosses in front of the creature. In `present` / `hand_out` it is drawn **after** the hand (the item sits on the palm).
* Scale your prop by your own `s`.
* For any other pose, read `a["hand_r"]` and draw the prop yourself after `draw_person`, or add `"hold": 1` (right hand) or `2` (both hands) to a pose dict, or use `hold_sides` (below).

**Episode 2: `hold_sides`, `hold_layer`.**

* `hold_sides=None` (default) keeps the Episode 1 rule above: the pose decides (`("r",)` for one-hand hold poses, `"both"` for two-hand ones, nothing otherwise).
* `hold_sides="r"`, `"l"` or `"lr"` (or a tuple) calls `hold(ctx, side, hx, hy, ang)` **once per listed hand, in ANY pose** (Embarrassment's flashlight in `walk`, a keycard in the l hand while the r hand waves...). `"both"` forces the midpoint call.
* Each hand's prop is drawn in that hand's own z-slot, so a prop in the **far hand goes behind the body** with the far arm, and the near hand's prop stays in front. Through blends and cycles the slot follows the arm's draw order (§6b), so props never flicker either.
* `hold_layer`:
  * `None` / `"auto"`: before the arm (fingers wrap over), or after it for `present` / `hand_out`;
  * `"back"`: always before the arm;
  * `"front"`: **after** the holding arm, so the prop is never covered by the gripping hand or sleeve (cards, recorders, phones, a lever handle);
  * `"top"`: after the whole character.

```python
def light(ctx, side, x, y, ang):
    with saved(ctx, x, y, s, ang): draw_flashlight(ctx)
draw_person(ctx, "embar", x, y, s, t, pose="walk", hold=light, hold_sides="r", hold_layer="front")
draw_person(ctx, "tired", x, y, s, t, pose="carry_front", hold=box)                 # Episode 1 call
draw_person(ctx, "guard", x, y, s, t, pose="stand", hold=prop, hold_sides="lr")     # one call per hand
```

**Episode 2: `reach` (world-space IK).**

* `reach={"r": (x, y), "l": (x, y)}` puts each listed hand's **grip point** (`hand_r` / `hand_l`) on that point, given in YOUR ctx coordinates (the same space as `x, y`). The point is not body-relative, so you can pass a lever handle, a door handle or a button straight from your set.
* The elbow bends naturally: it uses the pose's `bend` (+1 = out/down), and the depth stays near the pose's own hand depth.
* Targets beyond arm's length are clamped: the arm points straight at the target.
* Optional extras per side: `(x, y, weight)` blends from the pose's hand (0) to the target (1), handy for easing a reach in. `(x, y, weight, ang)` also fixes the hand direction (screen radians, your coordinates). By default the hand points along the shoulder → target line (the wrist bends as needed), so the grip lands exactly on any reachable target.
* The rest of the pose (hand shapes, torso, legs) comes from `pose`. `haul` + `reach` on the lever handle is the s07 pull: animate the handle down and the hands follow it.

```python
hx, hy = lever_handle(t)                            # your set's coordinates
draw_person(ctx, "tired", x, y, s, t, pose="haul_strain", turn=1.0,
            reach={"l": (hx - 14 * s, hy), "r": (hx + 14 * s, hy)}, expr="pain")
```

```python
def cage(ctx, side, x, y, ang):
    with saved(ctx, x, y, s, 0): draw_cage(ctx)
draw_person(ctx, "embar", x, y, s, t, pose="carry_front", hold=cage)
```

## 6b. Draw order: no hand / arm z-order flicker (Episode 2)
Each frame the rig decides, for both arms, a layer (`back` = behind the legs and torso, `mid` = over the torso and under the head, `front` = over the head) and which arm is drawn last. The anchors `order` and `layers` report the result. These decisions are now continuous, so hands never pop in front of or behind each other or the body from one frame to the next:

* **Static poses:** within a layer, depth decides only when the hands are clearly at different depths (> `ZTIE` = 24 px). Otherwise the pose's preference holds. The default is the **l hand on top**, matching `arms_crossed`, `cradle` and `struggle_hold`; set `hand_top=1` in a pose dict for r on top. Breathing, sway and IK rounding can no longer flip two clasped hands.
* **Blends `(a, b, k)`:** the order is pose a's until one switch point k\*, then pose b's. k\* is chosen once per blend (cached per pose pair and turn), at the k where the elements whose order changes are farthest apart: hand vs hand (forearm and hand clearance), arm vs torso silhouette and thighs, or hand vs head. So the order changes **at most once, and only where the hands are apart**.
* **Blends where an arm travels from behind the body to in front of it** (`hands_behind_back` and the Boss's `stand` → `plead`, `arms_crossed`, `cradle`...): the arm swings out around the hips mid-blend instead of passing through the torso. It also swings slightly when only the far arm changes layer.
* **Cycles:** the layers are decided by a majority vote over the whole cycle (no mid-cycle layer pops, e.g. `bang_door`, `walk` at turn ±0.5). The hand-over-hand order can only change at phases where the hands are clearly apart (an arm swinging past the other at the sides is fine).
* **Verified** by `python3 preview/human_ep2_test.py zorder`: blend sweeps at k = 0, 0.02, …, 1, for tired / embar / guard / boss, at turns 0, ±0.6, ±1, over every pair of `plead cover_eyes arms_crossed facepalm carry_front cradle wring_hands` (and from `stand`), plus 22 cycles at 5 turns. Results: every sweep changes order at most once, and every cycle change is made with the hands apart.
* **Residual:** the Boss's hands-behind-back `stand` → a front pose seen in pure side view (|turn| ≥ 0.9). The near hand comes out from behind the hip and its single switch happens while it still overlaps the hip by ≈10–45 px·s. Stage those at |turn| ≤ 0.6, or go through `attention` / `stand` dicts first.
* If you build a crossing pose by hand, give it explicit `al_layer` / `ar_layer` (as `arms_crossed` does) and blend through it rather than around it.

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
* **Ep2 recipes:**
  * *Hood pulled up by Curiosity:* `hood=tween(t, [(t0, 0), (t0 + 0.7, 1)], ease_in_out)`. Keep `expr="annoyed"` for the beat, then `"sigh"`. Under the hood only the mouth acts, so lean on `press`, `smirk` and `curve`.
  * *"Looking" blind:* `hood=1, power=0.6` and `face={"head_turn": ±0.4}`. The glow under the rim follows his head.
  * *Slow blink with the sense on:* the lash line glows teal while the lids are shut.
  * *Hurt moment (Curiosity's human, or Emb):* `tears=tween(...)` 0 → 0.6 (glassy), then 0.7 → 1.0 over ~1.5 s for the single tear.
  * *Embarrassment's crooked glasses:* `glasses_tilt=0.12` (+ `glasses_dy=6`); tween them back to 0 when he fixes them.
  * *Recorder:* `pocket_side="near"` and read `a["pocket"]` for the red LED. To hold it, use `pose="hand_out"`, `hold=recorder` (drawn on the palm).
  * *Smash:* `pose="punch_cycle", pose_t=t - t0, turn=1.0`. The fist (`hand_l`) lands 0.62 s after t0; spawn the shards on that frame.
  * *Lever haul:* `pose="haul_strain"`, `reach=` on the handle (see §6), `expr="pain"`.
  * *Flop on the bed:* `pose=state_at(t, [(0, "walk"), (t1, "flop"), (t1 + 0.35, "lie_front")], 0.3)`; the bounce is your `y` offset. Then `phone_thumb_lie` for the "zzz" reply.
  * *Sneak:* `pose="sneak"` + `x += a["speed"] * dt`. Freeze by blending to the cycle's current phase: `pose_t` held constant.

## 8. Preview boards
**Episode 2 boards** (`python3 preview/human_ep2_test.py [board ...]`, files `preview/human_ep2_<board>.png`):

| board | what |
|-------|------|
| `lookdown` | Tiredness gaze ramp (level / down / up) at close-up, front + 3/4, bored / sad (also `human_ep2_lookdown_cmp.png`: Episode 1 rig vs Episode 2 rig) |
| `hood`, `hood_close` | hood ramp 0..1 at close-up and medium, 3/4, with power glow on dark |
| `closed` | power with closed eyes (slow-blink ramp, content, closed lids); tears ramp on tired + embar |
| `glasses` | `glasses_tilt` / dx / dy, front + 3/4 |
| `poses` | the Episode 2 poses for tired / embar / boss / guard, front + 3/4 |
| `cycles` | sneak, punch_cycle, wave_small, walk_eyes_closed, haul_strain, phone_thumb (8 phases) |
| `holds` | hold_sides l / r / lr, hold_layer front, two-hand both, reach targets (red circles) |
| `sit`, `butt` | side-on floor planting (red floor line); seat volume in bent / crouch / climb poses |
| `zorder` | blend strips + the sweep report (k step 0.02) + cycle order report |
| `speed`, `timing` | speed anchor for dict poses; ms per body |

`python3 preview/human_ep2_handcheck.py` reports, for every blend sweep (k step 0.02) of the z-order pose list, the hand-to-hand clearance at each frame where the l / r draw order flips.

**Episode 1 boards** still run against this rig: `python3 preview/human_ep1_suite.py all` (files `preview/human_ep1suite_<board>.png`):

| board | file |
|-------|------|
| turnarounds (each who, turn −1/0/1, outfits, flip, headphones) | `human_ep1suite_turn.png` |
| face close-ups, every expression, front / 3/4 | `human_ep1suite_faces_<who>.png`, `human_ep1suite_faces34_<who>.png` |
| s=0.5 readability | `human_ep1suite_small.png` |
| all poses, front / 3/4 | `human_ep1suite_poses_<who>.png`, `human_ep1suite_poses34_<who>.png` |
| locomotion cycles (8 phases) | `human_ep1suite_cycles.png` (embar), `human_ep1suite_cycles_tired.png` |
| gesture cycles | `human_ep1suite_gestures.png`, `human_ep1suite_gestures_embar.png` |
| subtle acting (Tiredness lid/brow/eyes/press; Boss 0.05 steps) | `human_ep1suite_subtle.png` |
| blush ramp + sweat; power ramp | `human_ep1suite_blush.png` |
| power at s=3 | `human_ep1suite_power_close.png` |
| gaze: up/down/left/right, cross-eye, wall-eye, blinks | `human_ep1suite_eyes.png` |
| hand shapes | `human_ep1suite_hands.png` |
| hold z-order, pose/expr blends | `human_ep1suite_holds.png` |
| headphones neck→on | `human_ep1suite_headphones.png` |

## 9. Performance and limitations
* **Performance:** about 5.1–5.8 ms per full body at s=1 into a 720x1280 surface (`timing` board), and about 6.9 ms with `hood=1` + `power`. An s=2.5 close-up costs about 7 ms, the same as the Episode 1 rig. The cost is mostly cairo rasterisation. Limbs use fill-only outlines, and the curve tolerance is set to 0.3 device px. The z-order logic adds two tiny skeleton solves per blended frame. It caches a 32-phase order table per (character, cycle, turn rounded to 0.05) and a switch point per (blend pair, turn), so the first frame of a new combination costs 1–3 ms more.
* **Limitations:**
  * The rig is 2.5D: at full profile (`turn` ±1.6) faces are still a hard 3/4.
  * Poses that reach straight at the camera (`catch`, `lean_in`, `crawl`) read best at turn ±0.6..1.
  * Hands are drawn flat in the screen plane. A pointing finger aimed at the camera does not foreshorten.
  * `punch`, `haul`, `hand_out`, `sneak` and `wave_small` reach along the facing direction; stage them at turn 0.6..1.3 (at turn 0 they point at the camera).
  * Far eyes in strong 3/4 views can poke slightly past the face outline (unchanged from Episode 1).

---------------------------------------------------------------------------------------------
## Episode 2 notes
**Fixes for Episode 1 complaints**

1. **Look-down closing Tiredness's eyes.** The gaze droop is soft-capped and heavy lids re-centre the iris in the visible opening, so `look y=0` reads as straight ahead and down-looks keep the irises. Remove old `lid` −0.15..−0.3 compensations.
2. **Askew glasses:** `glasses_tilt`, `glasses_dx`, `glasses_dy` (no more monkeypatching `_draw_glasses`).
3. **Both hands can hold:** `hold_sides="l" | "r" | "lr" | "both"`, each prop drawn in its own hand's z-slot (far hand behind the body).
4. **Props covered by the gripping arm:** `hold_layer="front"` (or `"top"`).
5. **World-space arm targets:** `reach={"r": (x, y), "l": (x, y)}` in caller coordinates (optional weight and hand angle), clamped to arm length.
6. **`speed` for dict poses based on a cycle** (was 0). Dict waves now use the base cycle's period.
7. **`sit_up` / `sit_floor` floating in side-on sets:** the legs are laid on the floor from |turn| ≈ 0.3 to 0.8, so butt and heels share `y`; the floor hands lie flat.
8. **Pocket behind the far arm:** `pocket_side="near"` (or `"l"` / `"r"`); Embarrassment's drawn pocket follows.
9. **No butt emphasis:** bent-over, crouched and seated poses flatten the rear. The back depth of the hips and hem shrinks, and the thigh tops slim and start nearer the knee. Hip flexion and torso lean drive it. Nothing protrudes in `crouch`, `pick_up`, `cover_sweater`, `climb`, `crawl`, `sit_*`, `sneak`.
10. **No hand z-order flicker:** depth ties use a pose preference, blends switch once at the clearest k (with an around-the-body arm path when needed), and cycles use voted layers and sticky hand order (see §6b).

**Other fixes found while testing**
* The torso collapsed to a line whenever the spine lay horizontal pointing right (`rot` ≈ +π/2: lying poses and the rotated `flip` ball): a bad guard in `_torso_geom`.
* The Boss's hands-behind-back `stand` leaked into every cycle and dict built on `stand`. Her `wring_hands` / `roll_hand` hands were drawn behind her body, and her walk swung clasped hands apart. Now:
  * arms that a cycle drives by IK get their own layer;
  * the Boss walks / sneaks / tiptoes with her hands still clasped behind her (no swing);
  * her runs swing normally.
* Fully closed lids stayed open a sliver with `lid_ang` (sad and bored blinks).
* Lab-coat tails ignored the body roll (pointed down through the bed in lying poses).
* `plant_all` (lying poses) measures the torso's projected thickness, so profile bodies rest on `y` (identical at turn 0).

**New:** `hood`, `tears`, `power` with closed eyes / under the hood, `CRATE_H` and the anchors `crate`, `elbow_*`, `knee_*`, `order`, `layers`, `hood_rim`, the pose keys `hand_top`, `head_face`, `hold_hand`, `pillow`, `K()` keyframes. Poses: `sit_crate punch_wind punch guard_fists haul lie_front flop hand_out`. Cycles: `sneak punch_cycle haul_strain wave_small phone_thumb phone_thumb_lie walk_eyes_closed`. `shrug` was retuned to a big, clear shrug.

**Staging reminders (SPEC §0)**
* No butt-up anything: `sneak` is the upright crouch. Avoid rear views of `crouch` / `pick_up` (stage them in 3/4 from the front).
* Waves are `wave_small` only (bent elbow, chest height). Pointing is `point` (thumb up, sideways).
* Tiredness's lids open fully only with `expr="determined"` / `"awe"` (s06 "I'm not tired"). Keep `hood` < 0.85 there so we see it.
* Headphones are off in Episode 2 (`headphones=None`); they still work.
