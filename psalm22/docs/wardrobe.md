# lib/wardrobe.py — period clothing for MPFB humans

1st‑century Judean / Roman garments built **procedurally from each person's actual rest‑pose body**
(any MPFB phenotype: man, woman, child, baby, heavy, lean). Every garment is a real mesh
(voxel‑united shell → clean cuts → smoothing → procedural folds → push‑out from the body and
from inner layers), parented to `person.rig` and deformed by an **Armature modifier** with bone
weights transferred from the body (long skirts use MPFB's `helper-skirt` weights, so hems do not
tear between the legs). Optional cloth simulation (`drape`, `cloth_sim`) for hero stills / shots.

```python
import sys; sys.path.insert(0, "/home/user/game1/psalm22/blender")
from lib import characters as P, wardrobe as W

# usual path: characters.make_person calls wardrobe.dress for spec["outfit"] (a name or a list)
j = P.make_person("jesus", "JESUS_CROSS")           # outfit=["loincloth", "crown_of_thorns"]
P.place_on_cross(j, cross_root)
W.drape(j, j.garments, frames=25, ramp=15, ground=None)   # optional hero settle (loincloth ~12-18 s)

# direct use (any object with .rig/.body/.height works)
m = P.make_person("m1", "CROWD_MAN", outfit=None)
gs = W.dress(m, ["tunic", "mantle", "sandals"],
             colors={"tunic": "oatmeal", "mantle": "indigo", "belt": "madder"},
             seed=3, detail="crowd",
             tunic={"sleeves": "long", "length": "ankle"}, mantle={"style": "himation"})
P.pose(m, "walk")                                    # garments follow the rig automatically
```

## dress(person, outfit, colors=None, seed=0, detail="hero", **opts) -> list[bpy.types.Object]

| arg | meaning |
|---|---|
| `person` | object with `.rig` (MPFB *default* armature), `.body` (MPFB basemesh incl. helper geometry + vertex groups), `.height`. `characters.Person` works; extra: `.parts["hair"]`, `.garments` (appended to). |
| `outfit` | one name or a list (built inner → outer automatically; duplicates resolved: `robe`+`mantle` → robe's own mantle, `robe`/`robe_rich`/`roman_soldier` + `tunic` → no extra tunic, `roman_soldier`+`sandals` → caligae only). |
| `colors` | `None` (seeded pick from muted natural dyes), a palette name / **sRGB** tuple (applies to the main garment), or a dict keyed by part (see table). Values: names from `W.PALETTE` or sRGB 0‑1 tuples. |
| `seed` | variation (colours, knot side, folds, himation shoulder). Same seed + same body → same result. |
| `detail` | `"hero"` (≈1.3 cm cloth resolution, 10–18k verts per long garment) or `"crowd"` (≈2.4 cm, ~4x fewer verts, ~2.5x faster). Anything else = crowd. |
| `**opts` | single outfit: keyword options of that outfit (below). List: pass a dict per outfit name, e.g. `tunic={"sleeves": "long"}`. |

Returns every created object (garments, belts, knots, studs …). Each has custom props
`ob["wardrobe"]` (part name), `ob["outfit"]`, `ob["wardrobe_person"]`, and its dye in `ob.color`
(the shared materials read *Object Info ▸ Color*: recolour with `ob.color = (*W.color("indigo"), 1)`;
no new shader compile).

### Outfits

| outfit | parts created (name suffix) | colour keys | options (defaults) |
|---|---|---|---|
| `tunic` | `tunic`, `tunic_belt` | `tunic`, `belt` | `length="calf"` (`thigh, knee, below_knee, calf, ankle, floor` or a rig‑space z), `sleeves="elbow"` (`none, short, elbow, 3q, long`), `belt="sash"` (`sash, leather, cord, None`), `fabric="linen"` (`linen, fine_linen, wool, homespun, sackcloth`), `ease=0.03`, `flare=0.07`, `fold=0.014`, `wear=1.0`, `embroidery=False`, `loose=0.7` (0 = follows the body, 1 = hangs straight from chest/shoulder blades), `mask=True` |
| `robe` | tunic (ankle, long/elbow sleeves, sash) + `mantle` (himation) | `tunic` (alias `robe`), `belt`, `mantle` | tunic options |
| `mantle` | `mantle` | `mantle` (alias `main`) | `style="himation"` (diagonal wrap over `side` shoulder, rolled edge) / `"cloak"` (both shoulders, open front, wide elbow sleeves) / `"cape"` (back + shoulder tops), `side="L"`, `length="calf"`, `fabric="wool"`, `fold=0.016`, `embroidery=False`, `roll=True` |
| `robe_rich` | priest: `tunic` (fine white linen, embroidered hem, long sleeves), `sash` (striped), `robe_outer` (open cloak, rich dye, embroidered), `prayer_shawl` (striped, fringe + 4 tzitzit) | `tunic`, `belt`, `mantle`, `shawl` | – |
| `veil` | `veil` (frames the face, over shoulders and back) | `veil` | `length="back"` (`shoulder, chest, back, waist`), `fabric="linen"`, `band=None` |
| `headcloth` | `headcloth` + `headcloth_band` (cord at the brow) | `headcloth` | `length="shoulder"`, `band=<colour>` |
| `hood` | `hood` (peaked wool hood + short cape) | `hood` | `length="chest"` |
| `turban` | `turban` (wrapped linen, bone‑parented to `head`) | `turban` | `wraps=6`, `fabric="fine_linen"`, `hide_hair=True` |
| `roman_soldier` | `tunic` (red wool, knee), `lorica_hamata` (ring mail, short sleeves) or `lorica_segmentata` (iron hoops + shoulder guards), `cingulum` + `apron` + `apron_studs`, `sagum` (red cape hanging from the shoulder line down the back) + `fibula`, `galea` (helmet with brow ridge, neck guard, cheek guards; bone‑parented), `caligae` (hob‑soled lattice boots) | `tunic`, `cloak` | `armor="hamata"`/`"segmentata"`, `helmet=True`, `cloak=True`, `metal="iron"`/`"bronze"`, `humeralia=False` |
| `swaddle` | `swaddle` (cocoon with criss‑cross bands, collar behind the head); hides the whole body except head/neck | `swaddle` | `hood=True` |
| `crown_of_thorns` | `crown_of_thorns` (4 twisted vines, ~170 thorns, sized to head+hair, lower at the back; bone‑parented to `head`) | – | `strands=4`, `thorns=None` |
| `loincloth` | `loincloth` (low wrap, swag folds, overlapping front flap, twisted knot, 2 hanging ends) | `loincloth` | `knot_side=±1` (+1 = character's left), `fold=0.006`, `flap=True` |
| `sandals` | `sandals` (sole + instep/mid/ankle straps + toe thong + heel strap, both feet) | `sandals` | `style="sandal"`/`"caligae"`, `sole=None` (thickness m) |

Palette names (sRGB): undyed, cream, linen, white_linen, bleached, oatmeal, sand, camel, brown,
dark_brown, umber, grey, charcoal, black_wool, indigo, blue_grey, woad, tekhelet, mary_blue, madder,
roman_red, rust, ochre, saffron, olive, purple, plum, scarlet, leather, dark_leather, iron, bronze, brass, gold, thorn.
`W.color(name_or_srgb)` → linear RGB.

## drape(person, garments, frames=30, ramp=20, quality=5, keep_rig=True, self_collision=False, sequential=False, ground=True) -> list

Cloth‑simulates the soft garments onto the person's **current** pose (for stills / near‑static hero
shots: kneeling, crouching, sitting, on the cross). The rig is animated rest → current pose over
`ramp` frames, then held `frames` frames (gravity + body collision, pinned by each garment's `pin`
group: neck/shoulder band, belt line, head part of head coverings, loincloth waistband).
Rigid parts (crown, helmet, turban, belts, sandals, studs, fibula) are skipped.
* `keep_rig=True`: the result is written back into the rest shape by **inverse skinning**, so the
  garment still has its Armature modifier, reproduces the drape exactly at this pose and follows small
  motions (breathing, head turns, slow camera‑time movement). `False`: frozen mesh (Armature removed).
* Layers are simulated **together** (default `sequential=False`): every inner soft garment also gets a
  Collision modifier after its Cloth, so the outer one rests on it (tested: tunic + himation kneeling, clean,
  43 s). `sequential=True` (inner first, then outer) is NOT recommended: the inner layer's inverse‑skinned
  rest shape can intersect the outer layer at the start of its sim → inner cloth shows through.
* `ground`: `True` = temporary floor under the lowest posed body point, a float = world z, `None` = no floor
  (use `None` on the cross).
* Removes the `WardrobeHide` masks of the body and of these garments (cloth moved; the sim keeps it
  outside the body).
* Call **after** posing and after placing the rig; the scene frame/range and the rig's action are restored.

## cloth_sim(person, garments, ctx=None, preroll=20, frame_end=None, quality=5, self_collision=False, ground=None, bake=True) -> list[Modifier]

For **animated** hero shots (e.g. the old man kneeling into the dust, robes in a walk). Call in
`build(ctx)` **after** keying the character animation:
```python
P.key_pose(old, 1, "stand"); P.key_pose(old, 60, "kneel_bow")
W.cloth_sim(old, old.garments, ctx, preroll=20, frame_end=ctx.render_frames, ground=terrain_obj_or_z)
```
Adds Cloth (after the Armature, `pin` group) + body Collision, keys the rest pose at frame `1-preroll`
so the cloth starts from its fitted rest shape, and (default `bake=True`) bakes immediately with
`bpy.ops.ptcache.bake_all` (in memory). Baking here is required for the pre‑roll: `scene.frame_start`
can't be negative, so a sequential render from frame 1 never visits frames ≤ 0. Then any frame list
(`all`, `odd`, `sheet6`, random access) renders from the cache. With `bake=False` it only sets
`ctx.needs_bake = True` (render_shot then calls `core.bake_all` for non‑sequential frame lists; fine
for `preroll=0`). `ground`: z value (invisible floor collider) or a mesh object (gets a Collision
modifier, e.g. the terrain).

## Helpers
* `auto_pin(person, ob)` – (re)create the `pin` vertex group used by drape/cloth_sim.
* `unmask(person, garments=None)` – remove all `WardrobeHide` masks (skin, inner layers, hair). Call
  it if you hide/delete a garment later (e.g. the casting‑lots shot where the tunic is taken off).
* `hide_body(person, idx)`, `hide_verts(ob, idx)` – add vertices to the inverted `WardrobeHide` mask.
* `fabric_material(kind, embroidery=False, stripes=False)`, `metal_material("iron"|"bronze"|"brass"|"gold")`,
  `mail_material()`, `thorn_material()` – shared materials (one per kind; colour from `ob.color`).
* `W.SUBDIV = 1` before `dress()` – render‑time Subdivision on hero garments for extreme close‑ups only
  (see performance). `W.MASK_LAYERS = False` disables inner‑layer masking.
* Garment vertex attributes: `wear` (0‑1 dust/dirt, strongest at hems) and `hem` (metres above the hem;
  drives embroidery bands and prayer‑shawl stripes). UVs (`UVMap`) are cylindrical **in metres**
  (column around the body axis, seam at the back; sleeves around the arm, seam underneath).

## What dress() changes on the person
* Body: vertex group `wardrobe_hide` + MASK modifier `WardrobeHide` (inverted, before the
  Subdivision) hiding skin that is well inside a garment (≥ 8–12 cm from any opening) → no skin poking
  through, cheaper renders. Loincloth also hides the `genitals` group. Swaddle hides everything but head/neck.
* Inner garments: `WardrobeHide` masks where an outer garment fully covers them (no tunic poking through a mantle).
* Hair: turban/helmet hide the hair cards above the brim (`WardrobeHide` on the hair object).
* Nothing on the rig. Characters' grounding (`lbs_points`) ignores these masks.

## Performance (per person; 4 shared cores, other agents rendering; `WARDROBE_DEBUG=1` prints stages)
| item | hero | crowd |
|---|---|---|
| body analysis (cached per body, shared by all its garments) | 0.3–0.8 s | same |
| tunic (+belt) | 1.9–3.5 s, ~15k verts | 0.9 s, ~5k verts |
| robe (tunic + himation) | 4.2 s, 29k verts | 1.8 s, 10k verts |
| tunic + mantle + sandals (CROWD_MAN) | 3.8–5.4 s | 1.7–2.4 s |
| robe + veil (MARY) | 5.8 s | 2.6 s |
| mantle / veil / headcloth / hood | 1.0–1.6 s | ~0.8 s |
| turban / crown_of_thorns / sandals | 0.6 / 1.1 / 0.3 s | 0.5 / 1.1 / 0.3 s |
| loincloth | 1.0–2.5 s | 0.6 s |
| robe_rich (priest, 4 objects) | 5.7–11 s | 2.3 s |
| roman_soldier (9 objects) | 4.3–9 s | 2.1 s |
| swaddle (baby ~0.6 m) | 1.5–2 s | <1 s |
| drape: loincloth on the cross (25+15 frames) | 12–18 s | |
| drape: tunic alone (15k verts, 50 frames) | 27–55 s | |
| drape: tunic + himation kneeling (layers together) | ~45 s | |
| cloth_sim bake (animated) | ~1 s / frame for a 15k‑vert robe | |

Render cost is small without subdivision. **Subdivision on garments is expensive on this CPU/llvmpipe
EEVEE: +~1.2 GB RAM and +60 % render time for one dressed person** — keep `W.SUBDIV = 0` (default).
Body + garments for 3–4 people at 960x640 took ~2.5–3 GB RAM per Blender process in tests.

## Gotchas
* Build garments **before** changing body shape; posing before/after `dress()` is fine (everything is
  computed in the rest pose; `dress()` temporarily sets `pose_position="REST"` on the rig).
* Skinned long skirts look wrong in extreme poses (crouch, sit, deep kneel: the hem follows the shins
  and balloons). Use `drape()` for such stills and `cloth_sim()` for such animations.
* Rest A‑pose: hands hang next to the hips. Belts, hems and outer layers never take forearm/hand weights,
  but if a pose pushes the hands into a robe they will intersect it (as in reality – keep hands slightly off
  the body or drape).
* Colours in presets/dicts are **sRGB** (palette‑like), not linear.
* `drape()` cost grows with vertex count × frames; for crowds never drape (use poses where skinning works:
  stand, walk, point, arms_raised, mourn, light kneel). Drape the 1–3 hero characters of a shot.
* Masks are computed for the fitted rest shape. After `drape()` they are removed for the draped garments
  and the body. If you delete/hide a garment, call `W.unmask(person)`.
* A garment object sits at identity under the rig: its mesh coordinates are rig (armature) space.
  Move people via `person.rig`, never the garments.
* The cloth materials use Poly Haven CC0 textures (rough_linen, poly_wool_herringbone, hessian_380,
  hessian_230, brown_leather; downloaded on first use to /opt/assets/polyhaven); ring mail, embroidery
  and stripes are generated in numpy at runtime (packed images, no files).
* `WARDROBE_DEBUG=1` prints per‑stage timings and peak RSS.
