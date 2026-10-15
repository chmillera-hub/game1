# `lib/characters.py` — people system (MPFB 2 humans, hair, faces, poses, crowds)

Every human in the film. Built on MPFB 2 (MakeHuman for Blender, CC0 assets) with our own skin,
eye, hair and beard shading, a pure-math pose engine (anatomical arm/leg/spine parameters + analytic
IK), MakeHuman expression units for faces, and baked crowds.

```python
import sys; sys.path.insert(0, "/home/user/game1/psalm22/blender")
from lib import core as C, characters as P

j = P.make_person("jesus", "JESUS_CROSS", pose=None)        # preset name or dict; spec keys override
cross = C.wooden_cross(loc=(0, 0, 0))
contacts = P.place_on_cross(j, cross, head="up", strain=0.6) # hands on the beam, back on the upright
P.expression(j, "anguish")
P.eyes_look(j, j.eye_pos() + Vector((0.3, -2, 4)))           # eyes up to the sky (clamped, iris stays visible)

mary = P.make_person("mary", "MARY_OLD")                     # dressed + posed ('mourn') + 'sorrow'
mary.rig.location = (1.2, -1.5, 0); mary.rig.rotation_euler.z = math.radians(160)
P.pose(mary, "mourn")                                        # re-pose AFTER moving the rig (feet re-grounded)

crowd = P.crowd(40, area=(0, -8, 10, 4), seed=3, variety=6, lod="mid",
                face=(0, 0, 3.5), pose=["stand", "mourn", ("point", {"target": (0, 0, 4)})])
```

Conventions: metres, Z up. A person is built at the origin **facing −Y** (towards a default
`core.camera`). Character's left = `.L` bones = +X. `person.rig` (armature object) is the parent of
everything — move/rotate the person through `person.rig` (`person.root` is the same object). **Never
scale the rig** (height is set at build time with `height_cm`).

---------------------------------------------------------------------------------------------------
## 1. Building people

### `make_person(name, preset=None, **spec) -> Person`
`preset`: a dict or the name of one in `PRESETS` (case-insensitive). Spec keys (all optional,
defaults in `DEFAULT_SPEC`):

| key | values / meaning |
|---|---|
| `gender` | 0 (female) .. 1 (male) |
| `age_years` | 1 .. 90 (MPFB minimum is ~1 y; `BABY` uses 0 → 1 y scaled to 52 cm) |
| `build` | `frail`, `lean`, `average`, `heavy`, `muscular` |
| `height_cm` | exact standing height (body is rebuilt at the right scale, no object scale) |
| `ethnicity` | `judean` (default: olive-tan skin, dark hair, brown eyes), `arab`, `african`, `east_asian`, `south_asian`, `european`, `latin` |
| `skin_tone` | 0 light .. 1 dark, around the ethnicity default (None = default) |
| `hair` | MPFB style: `long01`, `short01`..`short04`, `bob01`, `bob02`, `ponytail01`, `braid01`, `afro01`, `none` |
| `hair_color` | `black`, `dark_brown`, `brown`, `light_brown`, `auburn`, `blonde`, `grey`, `white` or linear RGB |
| `grey` | 0..1 greying (hair, beard, brows). Default from age |
| `hair_strands` | hero hair curves (default True for `lod="hero"` when no veil/turban/hood/helmet is worn). Long/bob/braid/ponytail styles: ~11k strands grown along the MPFB shell (shell kept as a dark under-layer). Short styles `short01..04`, `afro01`: ~20-24k scalp-rooted strands from `make_short_hair` (the card shell is hidden - it read as a rubber cap). `False` = shell only |
| `beard` | `none`, `stubble` (skin shading only), `short`, `full`, `long` |
| `beard_color`, `beard_length` | default = hair colour / per style (`long` 0.11 m; ELDER 0.16, MOSES 0.24) |
| `eye_color` | `brown`, `dark_brown`, `hazel`, `green`, `blue`, `grey` |
| `eyebrows` | MPFB `eyebrow001`..`eyebrow012` or `none` |
| `sweat`, `dirt` | 0..1 skin extras (sweat = glossy droplets on forehead/upper lip/chest; dirt = dust on feet/shins/knees/hands, light on face) |
| `blood` | 0..1, tasteful: thin drips from the crown line + thorn punctures at the brow, a little at palms/feet/right side |
| `scars` | 0..1 healed wound marks in palms/feet/side (risen Christ) |
| `redness` | 0..1 regional flush (nose, cheeks, ears) |
| `wrinkles` | 0..1 (default from age) – skin relief strength |
| `face` | extra MPFB modelling targets `{"nose/nose-hump-decr|incr": 0.3, "head/head-oval": 0.4, ...}` (−1..1 for decr/incr pairs) |
| `expression` | applied after posing (see §4) |
| `pose` | applied after dressing (`None` = leave in MPFB rest A-pose) |
| `outfit`, `outfit_colors`, `outfit_seed` | passed to `lib.wardrobe.dress` **as one list** (wardrobe resolves duplicates such as `robe`+`mantle` and builds inner -> outer); colours keyed by wardrobe part: `tunic`/`robe`, `mantle`, `veil`, `turban`, `belt`, `loincloth`, `swaddle`, `sandals` – palette names or sRGB tuples |
| `outfit_opts` | per-outfit wardrobe options, e.g. `{"tunic": {"sleeves": "long", "length": "ankle"}, "mantle": {"style": "cloak"}}` |
| `lod` | `hero` (subdivision, beard + hair curves, all body parts), `mid` (no subdivision, 35 % beard), `far` (MPFB proxy body, low-poly eyes, no brows/lashes/teeth/tongue/beard) |
| `staff` | True → `make_staff(person)` (Moses). Every `pose()` re-attaches it to the grip hand (`hold_staff`); use the poses `staff` / `staff_raised` |
| `seed` | crowd randomisation seed |

Build order inside `make_person`: MPFB human (rig `default`, high-poly eyes, brows, lashes, teeth,
tongue, hair shell) → macro shape baked into the mesh → landmarks + skin masks → materials →
beard/hair curves → **wardrobe (rest pose)** → pose → expression.
Wardrobe is optional: if `lib.wardrobe` cannot be imported a warning is printed and the person stays
undressed. `dress(person, outfit, colors=None, seed=0, detail="hero"|"crowd", opts=None)` can also be
called directly (call it before posing). It passes the whole list to `wardrobe.dress` in one call (if that
raises, it retries item by item and logs a warning).

### Presets (`PRESETS`)
`JESUS_CROSS` (33, lean, long dark-brown hair + strands, full beard, sweat/dust/blood, loincloth +
crown of thorns, pose `crucified`, `anguish`), `JESUS_ROBED` (cream tunic + madder mantle, sandals,
`sorrow`), `JESUS_RISEN` (clean, white robe, scars in palms/feet, `peace`), `MARY_YOUNG` (17, veil,
braid), `MARY_OLD` (48, veiled, `mourn` + `sorrow`), `PRIEST` (56, heavy, greying full beard,
`robe_rich` + turban, `sneer`), `ELDER` (72, frail, short white hair strands, long white beard, worn robe),
`CHILD` (7, short hair strands, tunic, `awe`), `BABY` (newborn-sized 52 cm, swaddled, asleep, pose `baby`),
`SOLDIER` (28, muscular, Roman kit over an undyed loincloth (subligaculum – shows when he crouches), stubble), `MOSES` (80, long white hair/beard, robe, staff, pose
`staff`, `awe`), `CROWD_MAN`, `CROWD_WOMAN` (seeded random age/build/skin/hair/beard/face shape; pass
`seed=`). All presets come out dressed and posed; see **§8 Cast sheet** for a tested recipe per preset.
`resolve_spec(preset, **spec)` returns the merged spec without building.

### `Person`
| attribute / method | |
|---|---|
| `.name`, `.spec`, `.height` (m), `.lm` (rest landmarks, rig space), `.build_time`, `.timings` | |
| `.rig` / `.root` | armature object, parent of everything |
| `.body` | MPFB basemesh (vertex groups + Armature modifier kept for garment weight transfer) |
| `.parts` | `eyes`, `eyebrows`, `eyelashes`, `teeth`, `tongue`, `mouth` (dark mouth-cavity occluder, bone-parented to `head`), `hair` (shell mesh, named `<name>.hair_<style>`; hidden when short-hair strands replace it or a veil covers it), `hair_strands` (curves), `beard` (curves), `proxy` (far LOD) |
| `.garments` | wardrobe objects; `.props` (e.g. staff); `.staff` (the staff object or absent); `.mats` (materials by role); `.masks` (per-vertex numpy masks: `beard, zone, wounds, dirt, red, sweat, lips, scalp, hair`) |
| `.bone_world(name, tail=False)` | world position of a bone in the current evaluated pose |
| `.bone_matrix(name)` | world matrix of a pose bone |
| `.head_pos()`, `.eye_pos()` | centre of head, midpoint between the eyes |
| `.hand_pos(side)` | palm centre; side `"L"`/`"R"` (character's left/right) |
| `.foot_pos(side)` | ankle joint |
| `.set_visible(bool, frame=None)` | hide/show all objects (optionally keyed) |
| `.objects()` | rig + all descendants |
| `.update()` | `view_layer.update()` (call before reading bone positions after changes) |

Bone names (MPFB `default` rig): `root, spine05..spine01, neck01..03, head, jaw, eye.L/R,
clavicle.L, shoulder01.L, upperarm01/02.L, lowerarm01/02.L, wrist.L, finger1-1..finger5-3.L,
metacarpal1..4.L, pelvis.L, upperleg01/02.L, lowerleg01/02.L, foot.L, toe1-1..toe5-3.L` (and `.R`).

---------------------------------------------------------------------------------------------------
## 2. Poses

### `pose(person, name, ground_z=None, ground=True, drape="auto", **params) -> state`
Static pose. All body bones are rewritten (face bones – jaw/eyes – are left to §4). Place the rig
(`person.rig.location / rotation_euler`) **before** posing: world-space targets are converted to
rig space and feet are grounded on `ground_z` (world z; default = the rig origin height) using fast
linear-blend skinned sample points (`lbs_points`).

`drape`: skinned skirts cannot follow raised thighs (a crouch turns a knee-length tunic into a stiff dish,
a kneel turns a robe into a sack). With `"auto"` (default) the skirted garments of a **hero** person
(`lod="hero"`) are cloth-settled on the pose when `name in DRAPE_POSES` (`crouch, sit, kneel,
kneel_pray, kneel_bow, prostrate`) via `drape_skirts()` – **30-90 s** per person. `True`/`False` force
it; `characters.AUTO_DRAPE = False` disables the automatic case globally. A later non-drape `pose()`
restores the fitted standing garments. If the person holds a staff it is re-attached to the hand.

| name | params |
|---|---|
| `rest` | MPFB A-pose |
| `stand`, `stand_relaxed` | `head` (`level`,`up`,`down`,`bowed`,`side`,`sky`), `hands` (hand shape), `turn` (deg head turn) |
| `crucified` | `head` = `up`/`down`/`side`/`level`, `strain` 0..1 (arm V-angle 14–30° above horizontal, shoulder lift, knee bend), `hands` (`cross`), `knee_side` ±1. Use `place_on_cross` to attach to a cross |
| `kneel` | both knees, upright torso, hands on thighs |
| `kneel_pray` | `rock=(x,y,z)` world point where the clasped hands rest (else in front of the chest), `head` (`bowed`) |
| `kneel_bow` | forehead towards the ground, arms forward |
| `prostrate` | face down, arms stretched forward |
| `arms_raised` | worship; `spread` deg from vertical (35), `head` (`up`), `hands` (`open`) |
| `point` | `target` world point, `side` `auto`/`L`/`R`; head looks at the target |
| `reach` | `target`, `side`, `hand` |
| `cradle` | holding a baby at the chest (head in the LEFT elbow crook); see `place_baby` |
| `baby` | swaddled newborn (arms folded, knees drawn up) |
| `mourn` | hands clasped at the chin, head bowed and tilted |
| `crouch` | soldier squatting on the balls of the feet; `throw` 0..1 extends the right hand (dice) |
| `hammer` | `phase` `raise`/`strike`; right hand grip (hammer), left hand low in front (spike) |
| `sit` | thighs horizontal, feet grounded (seat height ≈ knee height; the set provides the seat) |
| `staff` | standing, the staff (see `make_staff`) planted beside the feet, gripped at chest height; `side` (`R`), `lean` (deg, 6), `head`, `hands` (free hand) |
| `staff_raised` | Moses at the sea: staff held high in the `side` hand (fist axis searched so the staff runs through the grip), other arm stretched out, palm down, head up; `reach` 0..1 |
| `walk`, `run` | single frame of the cycle at `phase` (radians) |
| any | `look=(x,y,z)` turns neck+head towards a world point |

Hand shapes (`HANDS`): `relaxed, fist, open, palm, grip` (staff/hammer/lamp), `clasped, point,
cross` (nailed: palm open, fingers curled), `cup, claw`.

### `key_pose(person, frame, name, ground_z=None, ground=True, **params)`
Same as `pose` but keyframes every body bone (quaternions, Bezier) + root location at `frame`.
Consecutive key poses blend smoothly (e.g. `key_pose(p,1,"stand"); key_pose(p,40,"kneel")`).
Quaternion signs are kept continuous. **No drape** (animated skirts: `wardrobe.cloth_sim`), and the staff
keeps the hand offset of the last `pose()` (fine between `staff` / `staff_raised`: both grip the same way).

### `drape_skirts(person, ground_z=None, frames=22, ramp=14) -> list`
Cloth-settles the person's skirted garments (every garment tagged `ob["skirt_below"]` by wardrobe:
tunic / robe / mantle / cape, not the loincloth, swaddle or mail shirt) on the current static pose with
`wardrobe.drape` (body + floor collision at `ground_z`, default = rig origin z; the result is
inverse-skinned so it stays rigged). The visibility masks above the skirts (skin under the tunic, tunic under
the mail) are restored afterwards. Called by `pose()` (see above); measured 32 s (soldier crouch, tunic +
cape) and 49 s (elder kneel, tunic + himation) on the shared 4-core box.

### `place_on_cross(person, cross_root, head="up", strain=0.6, knee_side=1.0, hands="cross", feet_z=None) -> dict`
For `core.wooden_cross(...)` roots (reads the `*_upright` / `*_beam` children, any location/`rot_z`).
Sets `person.rig.matrix_world` so the back rests on the upright, palms meet the front of the beam
(arms in a V, IK-solved), knees bent and turned to `knee_side`, right foot over left against the
upright. Returns world points `hand_L, hand_R, foot_L, foot_R, nail_feet` (for nails / blood props).
Call `expression()` / `eyes_look()` afterwards. Re-call to change `head`/`strain` (static).

### Other pose helpers
- `look_at(person, world_point, frame=None, amount=1.0, eyes=True)` – neck+head (+eyes) towards a point, on top of the last pose (or the pose keyed at `frame`).
- `rotate_bone(person, bone, (x,y,z) deg, frame=None, mode="LOCAL"|"ADD")` – low level, bone-local Euler.
- `walk(person, points, f0, f1, run=False, ground_z=None, step=1, height_fn=None)` – procedural cycle along world points `[(x,y[,z]),...]`, person faces along the path; stride matches speed (no foot sliding to speak of). `height_fn(x,y)` follows terrain. `run(person, points, f0, f1)` = fleeing.
- `head_shake(person, f0, f1, amount=1, freq=1.6)`, `nod(...)`, `laugh(person, f0, f1)` (body bounce + `laugh` expression keys) – animated, on top of the last pose.
- `cradle_anchor(person)` → (world loc, euler) of the bundle; `place_baby(baby, holder)` lays a `BABY` in a `cradle` pose.
- `make_staff(person, side="R", length=None, seed=5)` – gnarled staff with knots and a worn knob (origin at its foot, +Z up; in `person.props`, also `person.staff`). Default length 1.08 × height.
- `hold_staff(person, grip=None, ground_z=None)` – bone-parents the staff to the wrist so it runs through the grip channel of the fist (index→little-finger knuckle line, offset into the palm). `grip` = fraction of the staff below the hand; `None` = planted on `ground_z` when the hand is low enough, else 0.38 (held aloft). Called by every `pose()`; call it yourself after manual bone edits.
- `lbs_points(person, state=None)` – ~4k skinned body sample points (rig space) for contact queries.

Joint safety: arms use an anatomical parameterisation (upper-arm direction + elbow crease, elbow
0–150°, forearm pronation relative to the rest pronation, split over both forearm twist bones) and
analytic two-bone IK with a pole; legs likewise (knee 0–165°). The humerus is swung with minimal
twist from rest when no crease is given. Checked: elbows, knees, shoulders, wrists, fingers in all
poses above (no candy-wrapping / broken joints).

---------------------------------------------------------------------------------------------------
## 3. Faces

### `expression(person, name="neutral", weight=1.0, frame=None, extra=None)`
`name` in `EXPRESSIONS`: `neutral, anguish` (brows up+knitted, eyes narrowed, mouth slightly open),
`sorrow, crying, peace` (soft faint smile), `smile, sneer, mock, laugh, cry_out` (mouth wide),
`awe, anger, fear, pain, exhausted, dead, sleep` — or a dict of MakeHuman expression units
(`UNITS`, e.g. `"eyebrows-inner-up"` = both sides, `"nose-left-elevation"`) plus `"jaw": degrees`.
`weight` scales everything; `frame` keys it (blend between keyed expressions). Units are loaded on
demand as shape keys `ex-<unit>` on the body and transferred to brows/lashes through the MPFB mhclo
correspondence; the beard follows automatically (curves deformed on the surface).

### Eyes
- `eyes_look(person, world_point, frame=None, limit=28, up_limit=12, down_limit=22)` – aims both eye bones (clamped in the head frame so the iris stays visible: tilt the head for big up-looks).
- `blink(person, frame, duration=5)` – keyed blink returning to the current expression.
- `eyes_closed(person, amount=1.0, frame=None)`.

---------------------------------------------------------------------------------------------------
## 4. Look / materials (what you get)
- Skin: MPFB CC0 diffuse map, hue/sat/value + multiply tint per ethnicity (olive Mediterranean by
  default), mottling, regional redness, lip tone, beard shadow/stubble dots, dirt, blood (drips,
  punctures, wounds), scars, sweat droplets (coat), roughness breakup, pores + fine wrinkles
  (bump in rest space – sticks to the skin when posing), EEVEE SSS (weight 0.4, radius 1/.35/.16 × 7 mm).
  Driven by per-vertex masks `cmask_a` (beard, crown zone, wounds, dirt) / `cmask_b` (redness,
  sweat, lips, scalp) and `rest_position`. `skin_material(person)` rebuilds it after editing `person.spec`.
- Hair-coloured scalp: the hair-bearing region (`person.masks["hair"]`: forehead hairline, temples, above
  the ears, nape – stored in `cmask_b.a`) is painted in the hair colour (greyed with `grey`), so short
  hair, veiled hairlines and thin shells never show bare skin through the hair.
- Eyes: photo-textured eyeball (CC0 MakeHuman maps, recoloured; ivory sclera, darker brown irises) +
  separate clear glossy cornea (Transparent + Glossy, Fresnel x 0.4, blended) – no EEVEE refraction
  needed. The eyeball itself has no specular and no subsurface (both washed brown irises out to blue-grey).
- Teeth/tongue: darkened and rough (no SSS) so the open mouth does not show glowing pink gums / sky-blue teeth.
- Hair (long styles `long01, bob01, bob02, ponytail01, braid01`): MPFB shell recoloured (darker matte
  under-layer) + for heroes ~11k hair-curve strands grown along the shell (root→tip = UV v), bound to shell
  triangles by vertex index (GN `PS22_FollowShell2`) so they follow every deformation exactly; strands are
  kept off the face. Cached in `$WORK/cache/characters/hair_*.npz` (first build ~5 s, then ~0.1 s).
- Short hair (`short01..04`, `afro01`, heroes): `make_short_hair(p, length=None, count=None, points=6,
  seed=None, color=None, grey=None, part_side=1.0)` grows ~20-24k strands **rooted on the scalp** (hair mask),
  combed along a crown-whorl field (radial + gravity; men's styles sweep to the side and stop at the
  hairline, `short04` keeps a boy's fringe), stacked up to the MPFB shell height (capped 1.2 cm), deformed
  with *Deform Curves on Surface* like the beard. The card shell is then hidden (`hide_render`, kept for
  head-garment fitting). Per style length/wave/lift/count in `SHORT_HAIR`. First build ~5-8 s, cached after.
  `lod="mid"`/`"far"` keep the card shell (over the painted scalp).
- Strand material (`curve_hair_material`): roughness 0.6, specular 0.18 (a little sheen; at 0.8/0.08 dark
  beards rendered as a flat black mass), translucency 0.35, per-strand value variation, grey strands mixed by `grey`.
- Beard: hair curves grown in the beard mask with a groomed direction field (moustache sweeps
  down/out, chin longest, cheeks short, under-chin forward/down), guide clumping (stronger "locks" for
  long beards), waves, collision; long beards taper to a point below the chin; deformed with Blender's
  *Deform Curves on Surface* (follows pose + expressions).
  `make_beard(person, style=None, length=None, density=1.0, color=None, grey=None, seed=None)`.

---------------------------------------------------------------------------------------------------
## 5. Crowds & baking

### `bake_static(person, name=None, delete=True, coll=None, decimate=None) -> Object`
Freezes the posed + dressed person into ONE mesh object (modifiers/pose/shape keys applied,
materials kept, object transform = the rig's). Wardrobe fabrics take their colour from `obj.color`;
it is preserved as the `obj_rgb` attribute (materials are swapped for `<mat>.baked` copies that
read it). Beard curves are kept as a frozen child curves object. `delete=False` keeps the live person
(useful to bake several poses of one person). Linked duplicates: `o.copy()` (shares the mesh) –
also copy the children (beard), see `_instance`.

### `crowd(n, positions=None, area=None, seed=0, variety=6, pose="stand_relaxed", pose_fn=None, lod="mid", presets=("CROWD_MAN","CROWD_WOMAN"), face=None, yaw=None, yaw_jitter=25, ground_z=0.0, height_fn=None, spacing=0.65, name="Crowd", outfit=None, colors=None, women=0.4, hide_sources=True, **spec) -> Crowd`
Builds `variety` unique dressed people (random ages/builds/skin/hair/beards/face shapes, wardrobe
`detail="crowd"`; exactly `round(variety * women)` of them use `presets[1]` (at least one of each when
`0 < women < 1`), shuffled by `seed`), poses them (`pose` = name, list of names / `(name, params)` tuples cycled per
variant, or `pose_fn(person, i)`), bakes them, hides the sources at z = −500 and scatters `n` linked
duplicates: `positions=[(x,y[,z])...]` or `area=(cx, cy, width, depth[, angle_deg])` with
`spacing`; z from `ground_z` or `height_fn(x, y)`; facing `face` (world point) or `yaw` (deg) ± jitter;
scale ±5 %. Variants are used evenly (every source once before any repeats, shuffled). Returns `Crowd` with `.instances`, `.sources`, `.collection`.
LOD: `near` = hero people, `mid` = no subdivision (+ thin beards), `far` = MPFB proxy body,
decimated to 40 % (~11k verts per person with clothes).

### `clone(person, loc, yaw=0, name=None, action_offset=0) -> Person`
Animated linked copy (new rig object sharing armature + meshes; the action is shared, optionally
offset through an NLA strip). Good for a few walking/laughing extras.

---------------------------------------------------------------------------------------------------
## 6. Performance (measured on this 4-core box while shared with other jobs, load avg 9–20)
- `make_person` (dressed, `lod="hero"`): JESUS_* 10–11 s (MPFB 1.2–1.5 s, landmarks/masks 0.15 s,
  materials 0.05 s, beard 0.4–0.5 s, hair strands 0.1 s cached / ~5 s first build per body shape,
  wardrobe 2–7 s), MARY 6 s, PRIEST 12 s, ELDER 10 s, CHILD/BABY 4 s, SOLDIER 10 s, MOSES 17 s
  (first build). Undressed hero ≈ 2–3 s; undressed `mid` ≈ 1.9 s. Wardrobe dominates.
- `pose()` 0.05–0.4 s (+ `drape_skirts` 18–60 s for a hero in a crouch / sit / kneel* pose), `key_pose`
  ~0.05 s per key, `walk` 72 frames 0.3 s, `place_on_cross` < 0.1 s, `bake_static` 0.1–0.3 s.
- `make_short_hair` (20–24k strands): 5–8 s the first time per body + style, ~0.05 s from the cache.
- `crowd()`: ~4 s per unique variant (wardrobe) + ~1 ms per linked instance
  (30 instances / 5 variants: 22 s; 40 far instances / 4 variants: 19 s). Baked person: ~30k verts
  (`mid`), ~11k (`far`, decimated).
- Render (EEVEE, final 540×960, 6 spp, face close-up of JESUS_CROSS with crown, beard + hair curves,
  DOF): ~55 s/frame steady state under load ≈ 10 (≈ 30 s without the hair/beard curves, ≈ 27 s with a
  plain skin shader too) — the machine was heavily shared; expect roughly 3–4× less on an idle box.
  Hair + beard curves are the main cost: use `lod="hero"` only for close-ups / medium shots of the
  main characters; `mid` (no strands, thin beard) for medium-wide shots; crowds `mid`/`far`.
  You can thin strands: `make_hair_strands(p, count=6000)` / `make_beard(p, density=0.6)` (delete the
  old `p.parts[...]` object first) or build with `hair_strands=False`.
- Memory: a hero person + EEVEE render ≈ 2.5 GB peak (shader compile). Keep one Blender per agent.

## 7. Gotchas
- Faces −Y. Move the rig **before** `pose()` with world targets; re-pose after moving if you need re-grounding.
- Don't add a Subdivision modifier to the hair shell (strands are bound by vertex index); don't
  remove the body's `rest_position` attribute / UV map (beard uses them).
- `pose()` does not touch jaw/eye bones; `expression()` sets the jaw, `eyes_look()` the eyes.
- Shape-key based expressions + `bake_static` → the expression is frozen into the bake.
- Wardrobe's body-hiding mask keeps the beard region (handled in `dress`).
- Hair strands are disabled under veils / turbans / hoods / helmets to avoid poke-through; veils /
  headcloths / hoods also hide the hair shell entirely (the painted scalp shows at the hairline).
- EEVEE hair curves: keep `scene.render.hair_type = "STRAND"` (default).
- `pose()` on a dressed hero in a crouch / sit / kneel* / prostrate pose takes 30-90 s (cloth settle). Pass
  `drape=False` for previews or when the skirt is out of frame; animated poses (`key_pose`) never drape.
- After a draped pose the garments' rest shape is the draped one; the next standing `pose()` restores the
  fitted garments automatically, but do not mix a draped static pose with `key_pose` animation.
- `make_person(..., pose="kneel")` (or any DRAPE_POSES pose in the spec) drapes at build time.
- Soft area lights: EEVEE Next renders their penumbras on skin and cloth as grainy speckle with the default
  `shadow_ray_count = 1` (it does not go away with more samples). `light.data.use_shadow_jitter = True`
  on the offending lights removes it (≈ +20 % render time; tested on the cross close-up).
- The staff is bone-parented to the wrist: move the person via the rig, never the staff.
- The first EEVEE frame of a shot includes ~40–60 s of shader compilation (skin shader is big).

---------------------------------------------------------------------------------------------------
## 8. Cast sheet (integration-tested presets)

Every preset below was built **fully dressed** with `make_person`, posed as listed and rendered at draft
quality (540×960, 6 spp, EEVEE Next) in film-like daylight (Poly Haven HDRI + matched sun + fill/rim
area lights, textured ground). Contact sheets: `/opt/work/psalm22/dev/cast/cast_sheet_v1.jpg` (before
the integration pass) and `cast_sheet_final.jpg` (after); harness `dev/cast/cast.py` (one Blender per
scenario: `bl.sh cast.py KEY TAG body,bust`).

Conventions for all recipes: `import sys; sys.path.insert(0, "/home/user/game1/psalm22/blender")`,
`from lib import core as C, characters as P`, `from mathutils import Vector`. Place the rig **before**
posing. Hero presets build in 4–10 s (+30–60 s when a kneel/crouch pose is cloth-settled, + ~5–8 s the
first time a short-hair cut is grown – cached afterwards).

| preset | default look / pose | build (s) | draft render body / bust (s)* |
|---|---|---|---|
| `JESUS_CROSS` | loincloth + crown of thorns, sweat/dust/blood, long hair strands, full beard, `crucified`, `anguish` | 4.5 | 43 / 54 |
| `JESUS_ROBED` | cream tunic + madder himation, sandals, `stand`, `sorrow` | 7.3 (+59 drape for `kneel_pray`) | 52 / 55 |
| `JESUS_RISEN` | bleached robe + white himation, sandals, healed scars, `stand`, `peace` | 7.1 | 50 / 50 |
| `MARY_YOUNG` (+ `BABY`) | linen tunic, mary-blue veil, `cradle` with `place_baby` | 9.8 (both) | 32 / 35 |
| `MARY_OLD` | umber tunic, blue-grey veil, `mourn`, `sorrow` | 4.4 | 25 / 31 |
| `PRIEST` | robe_rich (white tunic, open cloak, striped tallit) + turban, greying full beard, `point` up + `mock` | 8.5 | 34 / 40 |
| `ELDER` | oatmeal/brown robe, short white hair strands, long white beard, `kneel` | 60 (50 = drape) | 41 / 46 |
| `CHILD` | brown tunic, boy's short hair strands, `stand` + `awe`, looking up | 9.6 (6.7 = first hair growth) | 29 / 35 |
| `SOLDIER` | loincloth (subligaculum), red tunic, ring mail, belt + apron, red cape, helmet, caligae, `crouch throw=1` | 23–38 (18–31 = drape) | 29 / 32 |
| `MOSES` | oatmeal tunic + camel himation, staff, long white hair/beard, `staff_raised` | 8.4 | 53 / 62 |
| crowd of 12 | 6 variants (2 women), `lod="mid"`, mixed poses | 24 | 88 (wide) |

\* Render times are the first frame of a fresh Blender (≈ 20–40 s of it is shader compilation), measured
while the 4 cores were shared with 2–3 other renders (load ≈ 8.5). Final-quality frames of a lit shot
are typically 2–4× faster on an idle machine; hair/beard curves remain the main per-frame cost.

### Recipes
```python
# JESUS_CROSS – on a cross (no drape: the loincloth is skinned; W.drape it for extreme close-ups)
cross = C.wooden_cross(loc=(0, 0, 0))
j = P.make_person("jesus", "JESUS_CROSS", pose=None)
P.place_on_cross(j, cross, head="up", strain=0.6)
P.expression(j, "anguish")
j.update(); P.eyes_look(j, j.eye_pos() + Vector((0.3, -2.0, 4.0)))

# JESUS_ROBED – Gethsemane: kneeling in prayer, clasped hands resting on a rock (auto cloth-settle ~60 s)
rock, _ = C.ph_model("boulder_01", loc=(0.03, -0.80, -0.10), scale=0.78)   # top ≈ 0.62 m
j = P.make_person("jesus", "JESUS_ROBED", pose=None)
P.pose(j, "kneel_pray", rock=(0.0, -0.50, 0.65))       # world point where the hands rest
P.expression(j, "sorrow")

# JESUS_RISEN – standing in morning light (preset pose 'stand', expression 'peace')
j = P.make_person("jesus", "JESUS_RISEN")
j.update(); P.look_at(j, j.eye_pos() + Vector((0.5, -3.0, 0.6)))

# MARY_YOUNG cradling the BABY
m = P.make_person("mary", "MARY_YOUNG", pose="cradle")
b = P.make_person("baby", "BABY")                       # swaddled, asleep, pose 'baby'
P.place_baby(b, m)                                      # move m.rig first, then re-pose + place_baby

# MARY_OLD mourning at the cross (preset pose 'mourn' + 'sorrow')
m = P.make_person("mary", "MARY_OLD")
m.rig.location = (1.2, -1.5, 0); m.rig.rotation_euler.z = math.radians(160)
P.pose(m, "mourn")                                      # re-pose after moving (re-grounds the feet)

# PRIEST mocking, pointing up at the cross
pr = P.make_person("priest", "PRIEST", pose=None)
P.pose(pr, "point", target=(0.6, -1.5, 3.2))            # world target
P.expression(pr, "mock")                                # or 'sneer' (preset), 'laugh'

# ELDER kneeling (auto cloth-settle of tunic + himation ~50 s; drape=False for previews)
e = P.make_person("elder", "ELDER", pose="kneel")
# or: e = P.make_person("elder", "ELDER", pose=None); P.pose(e, "kneel_bow")

# CHILD in awe, looking up
c = P.make_person("child", "CHILD", pose="stand")
c.update(); P.look_at(c, c.eye_pos() + Vector((0.2, -2.0, 1.0)))

# SOLDIER crouching, hand out (casting lots); the tunic skirt and cape are cloth-settled (~20-30 s)
s = P.make_person("soldier", "SOLDIER", pose=None)
P.pose(s, "crouch", throw=1.0)                          # throw 0 = fist low, 1 = right hand out, palm up

# MOSES with the staff raised (preset pose 'staff' = staff planted beside him)
mo = P.make_person("moses", "MOSES", pose=None)
P.pose(mo, "staff_raised")                              # staff follows the right hand (bone-parented)

# Crowd of 12 mixing men and women in different poses
cr = P.crowd(12, area=(0, 0.6, 4.2, 2.4), seed=11, variety=6, lod="mid", face=(0, -8, 1.6),
             pose=["stand_relaxed", "mourn", ("point", {"target": (0, 6, 4)}), "stand", "arms_raised",
                   ("stand", {"head": "up"})], women=0.4)
```

### What changed in the integration pass (all presets)
- Dressing passes the whole outfit list to wardrobe in one call (duplicate resolution + inner→outer order);
  `outfit_opts` spec key.
- Staff: real grip (`hold_staff`), new poses `staff` / `staff_raised`; MOSES defaults to `staff`.
- Short hair (`short01..04`, `afro01`): scalp-rooted strands replace the rubber-cap card shell (CHILD no
  longer looks shaved, ELDER/crowd heroes get real hair); painted hairline on every scalp.
- Veils/headcloths/hoods: fitted closer to the skull, the hair shell is hidden (no dark helmet band or shell
  fragments on the forehead), front panels fall over the shoulders.
- Crouch / sit / kneel poses cloth-settle the skirts of hero people (no more dish-shaped tunic or sack robe);
  the upper body stays pinned so nothing drifts through mail or mantles.
- Eyes: brown irises stay brown in daylight (no eyeball specular/SSS), ivory sclera; open mouths show a dark
  cavity instead of the sky, teeth opaque and darker.
- Hair/beard: lighter dark-brown, a little sheen (no flat black mass), smooth salt-and-pepper greying,
  long beards fall in locks; eye-area redness halved.
- Clothes: slimmer himation, muted palette (whites ≤ 0.86, reds/blues less saturated), crease bumps, half the
  hem dust, no cloth SSS speckle, softer wool sheen.
- Crowds: deterministic men/women share and balanced variant use.

### Known limitations (honest)
- Faces are believable mid-range realistic CG, not Spirits Within: MakeHuman topology, no wrinkle/normal maps,
  skin reads smooth and slightly waxy in flat light. Expressions with open mouths are acceptable at bust
  distance, weaker in macro close-ups.
- Cloth without simulation (standing poses) has procedural folds + crease bumps only; garments still look a
  little thick/smooth in close-ups. Kneeling/crouching hero garments rely on a 20–60 s cloth settle; crowds
  (`lod="mid"/"far"`) are never draped, so kneeling crowd members balloon – keep crowds standing / walking.
- Draped crouch: the soldier's tunic falls between the knees and the thighs show (physically plausible but a
  little stiff); the cape can touch the heels.
- Veils still read slightly as a hood with flared shoulder edges; the priest's turban is a plain wrapped dome.
- Long white beards (ELDER, MOSES) are dense and somewhat stringy; the priest's beard thins under the jaw when
  the head is tilted far back.
- Mid-LOD crowd heads keep the MPFB card shell (cap-like up close) and thin dotted beards; use `lod="near"`
  (hero) for crowd members closer than ~3 m.
- Soft area-light penumbras speckle on skin/cloth with EEVEE Next defaults (see Gotchas: `use_shadow_jitter`).
- `pose()` with a staff re-attaches it; `key_pose()` does not (the grip offset of the last static pose is kept).
