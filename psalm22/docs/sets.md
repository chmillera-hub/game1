# `lib/sets.py` — interior / built sets

Owner key: **sets**. Six ready-to-dress sets for the shots that are not open landscape, plus the
reusable props / helpers they are built from. Everything is procedural or CC0 (Poly Haven textures);
no external model downloads are needed (the table set optionally pulls bread/cup/jug from
`lib/assets.py`, the camp set optionally uses `lib/fx.py` for the fire; both fall back to built-ins).

```python
import sys; sys.path.insert(0, "/home/user/game1/psalm22/blender")
from lib import core as C
from lib import sets as S
```

| builder | shot | what |
|---|---|---|
| `S.stable_cave(ctx)` | s07a | Bethlehem stable cave at night, stone manger with straw, oil lamps, starlight shaft through an arched doorway |
| `S.garden_tomb(ctx, stone_open=...)` | s15 | rock-cut tomb, rolling stone in a groove (animatable), chamber with bench + folded grave cloths, dawn |
| `S.holy_of_holies(ctx, veil_open=...)` | s03 | gold-overlaid sanctuary with carved reliefs, parting embroidered veil, Ark + kneeling cherubim, glory light, incense |
| `S.courtyard_assembly(ctx)` | s17a | stone courtyard at dusk, colonnades + portico, ~480 flickering lamps, lampstands, crowd spots |
| `S.table_interior(ctx)` | s17b | lamplit room, rough plank table with flatbread (two halves), wine cup, jug, olives, lamps, steam |
| `S.camp_night(ctx)` | s20a | open ground at night, campfire (fx.campfire), seats for grandfather + child, stars, moonlight |

---------------------------------------------------------------------------------------------------

## Common contract

Every builder: `fn(ctx, loc=(0,0,0), rot_z=0.0, coll=None, world=True, ..., seed=N) -> SetInfo`

* Call it inside `build(ctx)` **after** `C.reset_scene(ctx)` (the runner does that) — the builders
  key per-frame flicker / smoke animation over `scene.frame_end`, so `ctx.render_frames` must
  already be set (it is).
* **Local frame of every set:** floor at z=0, the main camera looks from **-Y towards +Y**, X right.
  `loc` (metres) and `rot_z` (degrees) place the whole set; every returned position is already in
  **world space**.
* `coll`: an existing `bpy.types.Collection` to nest the set's collection in (default: scene root).
* `world=True` installs a matching world (night sky / dawn sky / dusk sky / dark gold). Pass
  `world=False` when the shot (or `lib/env.py`) sets the world itself.
* Nothing calls `configure_render`; set `ctx.render_opts` / `ctx.samples` as usual (see PERF).

### `SetInfo` (return value)

| attribute | type | meaning |
|---|---|---|
| `root` | Object (Empty) | parent of the whole set. Move/rotate it to re-place the set (anchors are NOT updated then — use `info.to_world()` on the local value or just pass `loc`/`rot_z`). |
| `coll` | Collection | holds every object of the set |
| `anchors` | `{name: Vector}` | world-space positions; also `info["name"]` |
| `facing` | `{name: yaw_deg}` | world yaw for a character/animal standing at that anchor. **0 = facing +Y**, 90 = facing -X (Blender Z rotation). Use `obj.rotation_euler.z = math.radians(info.facing[k])` for a rig whose front is +Y; for `lib/assets` animals/props (front = -Y) add 180. |
| `cameras` | `{name: {"loc","target","lens"}}` | world-space camera suggestions |
| `camera(name, fstop=None, focus=None, **kw)` | method | creates + activates `C.camera()` at a suggestion (kw go to `C.camera`, e.g. `lens=50`) |
| `lights` | `{name: Object}` | the set's lights (key `.data.energy` to animate) |
| `objects` | `{name: Object}` | notable objects (manger, stone, veil_L, bread, ...) |
| `extra` | dict | set-specific data (camera paths, crowd spots, helper callables) |
| `matrix` / `to_world(p)` | Matrix / fn | local-to-world transform of the set |

```python
def build(ctx):
    st = S.stable_cave(ctx)                       # world, lights, fog, straw ... all included
    cam = st.camera("wide", fstop=2.8, focus=3.2)
    mary_pos, mary_yaw = st["mary"], st.facing["mary"]
    # animate a camera along a suggestion-based move:
    a, b = st.cameras["wide"], st.cameras["manger_close"]
    C.animate_camera(cam, lambda f: (a["loc"].lerp(b["loc"], C.ease_in_out(ctx.u(f))),
                                     a["target"].lerp(b["target"], C.ease_in_out(ctx.u(f)))))
    ctx.samples = 6
    ctx.render_opts = {"volumetrics": "low"}
```

---------------------------------------------------------------------------------------------------

## 1. `stable_cave(ctx, loc=(0,0,0), rot_z=0, coll=None, world=True, lamps=2, starlight=1.0, lamp_energy=1.0, fog=True, dust_motes=True, straw=True, straw_density=900, manger="stone", seed=7, props=True, straw_shadows=False)`

Irregular limestone cave (~6.6 x 7.4 m, ceiling ~2.75 m, soot-darkened above, bedding strata),
arched doorway in the back-left wall (night sky with stars + the Bethlehem star visible through it),
straw-littered floor (procedural litter texture + ~10k realized 3D strands, denser around manger /
Mary / animals), rough-hewn stone manger heaped with straw on two stones, a rock seat for Mary,
oil lamp on a rock ledge (right wall) + one on a flat stone by Mary, clay jars, hay heap,
shepherd's staff by the door, boulders outside.

* `lamps` 1 or 2 (floor lamp by Mary). `lamp_energy` scales both lamps + warm bounce fills.
* `starlight` scales the cool volumetric spot through the door (0 disables it and the door fill).
* `manger="wood"` builds a wooden trough on splayed legs instead of the stone one.
* `fog` cave haze + denser beam haze (makes the starlight shaft visible). `dust_motes` GN specks in the shaft.
* `straw_density` strands/m² at full mask (cost driver, see PERF). `straw_shadows=True` lets manger/heap straw cast shadows.

Anchors: `mary` (top of her seat stone; facing -60° = towards camera-right/manger), `mary_head`
(approx. seated eye height), `manger` (top centre of the straw), `baby_manger` (where a swaddled
baby lies), `ox` (lying, back right, facing 115°), `donkey` (standing, back left, facing -115°),
`doorway` (threshold centre), `lamp_ledge`, `lamp_floor` (flame positions), `star` (200 m out
along the star direction).
Cameras: `wide` (26 mm, whole cave + doorway), `mary_close` (55 mm on Mary's seat), `manger_close`
(45 mm), `doorway_view` (32 mm on the doorway/star), `low_straw` (30 mm, low over the straw).
Lights: `lamp_ledge`, `lamp_floor` (flickering points, shadows), `starlight` (spot 10000 K),
`door_fill`, `bounce` (warm ceiling area), `floor_bounce` (warm up-light).
Extra: `door_dir`, `star_dir` (world unit vectors), `wall_fn_local(theta, z)` → (point, inward normal)
in set-local coords (to put more props against the wall).

Ox / donkey / Mary come from `lib/assets.py` (`A.animal("ox", ...)`, `A.animal("donkey", ...)`) and
`lib/characters.py`; place them on the anchors.

## 2. `garden_tomb(ctx, loc=(0,0,0), rot_z=0, coll=None, stone_open=0.0, world=True, sun=True, sun_elevation=4.5, sun_azimuth=-32.0, fog=True, interior_fill=1.0, garden=True, dust_motes=True, seed=11, roll_dist=2.25)`

Pale limestone cliff (18 m wide, ~5.5 m high, fractures, stepped ledges) with a flat dressed facade
around a low rectangular doorway (0.95 x 1.4 m, 0.55 m deep passage); round rolling stone (r 1.0 m,
0.32 m thick, chiselled) in a carved groove in front of the face with a stop block; chamber behind
(3.2 x 3.0 x 2.1 m, floor 0.32 m below the threshold, chisel-marked walls) with a bench along the
right (+X) wall carrying the collapsed linen sheet + 3 wrapping strips, and the face-cloth folded
separately at the head end (John 20:7). Rocky ground with dry grass tufts and boulders. Dawn: low
warm sun from front-left, warm-tinted Nishita sky, big shadowed sky-fill area light.

* `stone_open`: float 0..1 (0 = door covered, 1 = rolled `roll_dist` m to +X) **or** a list of
  `(frame, value)` keys. Rolling rotation is consistent with the distance. Later:
  `S.animate_tomb_stone(info, [(f, v), ...], interp="BEZIER")`.
  The stone opening also drives the `dawn_shaft` and `chamber_fill` energies (dark inside while closed).
* World lighting is deliberately ~0 (`light_strength=0.03`) so the chamber does not get lit through
  the rock (EEVEE Next world light leaks into closed rooms); exterior ambient comes from `sky_fill`.
* `garden=False` skips grass + boulders.

Anchors: `entrance` (threshold), `door_center`, `stone` (closed centre), `stone_open` (open centre),
`angel_seat` (top of the open stone, Matthew 28:2), `bench` (bench top centre), `linen`, `napkin`,
`chamber` (chamber floor centre), `garden_path` (4 m in front).
Cameras: `wide`, `approach`, `stone_low`, `interior`, `bench_close`.
`extra["move_in"]` = 4 world (loc, target) waypoints from outside to the bench (lerp between them for
the "camera moves in" of s15). `extra["stone_params"]` = {R, y, z, roll} (local).
Lights: `sun`, `dawn_shaft` (spot through the doorway onto the cloths, volumetric), `chamber_fill`,
`sky_fill`.

```python
tomb = S.garden_tomb(ctx, stone_open=[(1, 0.0), (int(ctx.nframes * 0.45), 1.0)])
wps = tomb.extra["move_in"]
def path(f):
    u = C.ease_in_out(ctx.u(f)) * (len(wps) - 1)
    i = min(len(wps) - 2, int(u)); t = u - i
    return wps[i][0].lerp(wps[i + 1][0], t), wps[i][1].lerp(wps[i + 1][1], t)
C.animate_camera(tomb.camera("approach"), path)
```

## 3. `holy_of_holies(ctx, loc=(0,0,0), rot_z=0, coll=None, veil_open=0.0, glory=1.0, smoke=True, shafts=True, holy_place=True, room=9.0, probe=True, seed=3)`

A 9 m cube (`room`) of gold-overlaid cedar: walls/ceiling carry a generated relief (framed panels
with palm trees and cherubim over a band of open flowers, 1 Kings 6:29; 2.25 m tile) with cavity
patina, gold pilasters, gold floor. The **veil** (two pleated halves across y=0, 8.6 m high) uses a
generated embroidery texture: deep blue ground, scarlet/purple/gold border bands, gold lozenge
lattice with rosettes and winged cherubim (Exodus 26:31), sheen + weave bump + translucency (glows
when backlit). The **Ark** (1.15 x 0.69 x 0.66 m: crown moulding, panelled sides, feet, 4 rings,
2 poles, mercy seat) stands at (0, 4.5, 0), long axis along X; two **cherubim** kneel on the lid
facing each other — metaball-sculpted robed figures (heads bowed to the mercy seat, forearms raised),
each with two feathered wings (lofted membrane + 3 shingled feather rows + leading-edge roll) rising
from the back and arching forward so the four wing tips meet over the centre. The **glory** is an
emissive spherical volume + 6200 K point light (volumetric rays through the incense) + top fill.
Incense: room-wide animated smoke volume + a rising column from a censer in front of the Ark;
2 narrow volumetric spots from the upper corners (`shafts`). `holy_place=True` adds 7 m of the Holy
Place in front of the veil with the golden incense altar (smoke column, glowing coals) lit by an
off-screen menorah. Two sphere reflection probes make the gold reflect the room.

* `veil_open`: float 0..1 or `[(frame, value), ...]`; later `S.animate_veil(info, pairs)`.
  0 = closed, 1 = each half drawn aside (gathered to its outer edge, most at the bottom, still
  attached at the rod). Implemented as a shape key "open" on `objects["veil_L"/"veil_R"]`.
* `glory` multiplies all glory light at build time; animate with `S.set_glory(info, [(f, mult), ...])`
  (keys point light, fill and volume emission together — use e.g. 1 → 6 for "rising into the
  blinding light").

Anchors: `ark`, `mercy_seat` (lid top centre), `glory`, `veil` (seam at eye height), `altar`
(incense altar top, only with holy_place), `high_priest` (1.6 m in front of the Ark, facing +Y).
Cameras: `approach` (Holy Place, veil fills frame), `through` (at the veil), `ark_wide`, `cherubim`,
`glory_rise`. `extra["path"]` = 5 waypoints from the Holy Place through the veil, rising into the
glory (s03). Lights: `glory`, `glory_fill`, `room_fill`, `shaft0`, `shaft1`, `menorah`, `veil_front`,
`altar_glow`. Objects: `veil_L`, `veil_R`, `ark`, `glory_volume`.

```python
hoh = S.holy_of_holies(ctx)
n = ctx.nframes
S.animate_veil(hoh, [(int(n * 0.15), 0.0), (int(n * 0.45), 1.0)])
S.set_glory(hoh, [(1, 0.6), (int(n * 0.7), 1.0), (n, 6.0)])
wps = hoh.extra["path"]          # lerp as in the tomb example
```

## 4a. `courtyard_assembly(ctx, loc=(0,0,0), rot_z=0, coll=None, lamps=480, world=True, crowd_rows=14, crowd_cols=14, glow=1.0, haze=True, seed=21, columns=True, sun_elevation=-3.0, sun_azimuth=200.0, stands=8)`

Flagstone court x -9..9, y -6..22 framed by roofed colonnades (x = ±7.3) and ashlar walls with lamp
niches; six steps up to a columned portico with a gate at the back (y ≈ 15.6..22). `lamps` instanced
clay lamps (GN, emissive flames flickering per instance, **no per-lamp lights**) line the steps,
stylobates, niches, the central aisle and the ground among the crowd; shadowless **cluster point
lights** (one per 3 m cell, energy ∝ lamp count × `glow`) make them pool warm light. `stands`
bronze lampstands with real flickering lights flank the aisle. Dusk sky (sun 3° below horizon).

Crowd: `extra["crowd_spots"]` = list of `(Vector world, yaw_deg)` — a jittered 14 x 14 grid over
x -5.5..5.5, y 0.3..13.5 with a 1.2 m central aisle, all facing roughly +Y (towards the portico).
`extra["lamp_points"]` world lamp positions; `extra["add_lamps"](points_local)` adds more lamps
(e.g. at characters' hands; points = (x, y, z[, yaw_deg]) in set-local coords).
Anchors: `crowd_center`, `portico`, `steps_front`, `leader`. Cameras: `wide`, `glide_start`,
`glide_end`, `faces` (looking back at the crowd's faces), `lamps_close`; `extra["glide"]` waypoints.
Lights: `stand0..N`, `crowd_glow` (12 x 14 m upward warm area at hand height — lights faces from
below), `crowd_key`, `wall_glow_L/R`, `moon`.

## 4b. `table_interior(ctx, loc=(0,0,0), rot_z=0, coll=None, world=True, use_assets=True, lamps=3, lamp_energy=1.0, haze=True, seed=31, steam=True)`

Room 5.2 x 5 x 2.7 m (soot-darkened plaster, timber beams, earth floor, small night window, wall
niche). Heavy table of 4 planks (2.1 x 0.86 m, top z = 0.76) centred at the origin along X, benches
both sides. On it: flatbread (from `assets.load("flatbread", variant=1)` → children `half_a/half_b`;
fallback built-in two halves), clay cup with wine, clay jug, wooden bowl of olives, crumbs, two oil
lamps (+ one in the niche), rising bread-steam volume.

Anchors: `table_top`, `bread`, `cup`, `jug`, `lamp_table`, `hands_zone` (12 cm above the bread),
`seat_N0..2` (far bench, facing -Y = 180°), `seat_S0..2` (near bench, facing +Y = 0°).
Objects: `bread` (root; animate its two half children apart to break it), `cup`, `steam`.
Cameras: `bread_close` (50 mm high three-quarter on the bread — use `fstop=2.8`), `table_wide`, `low_side`.
Lights: `lamp_table`, `lamp_table2`, `lamp_niche` (flickering), `bounce`, `wall_fill`, `window`.

## 4c. `camp_night(ctx, loc=(0,0,0), rot_z=0, coll=None, world=True, fire=True, fire_size=0.8, fire_energy=1.0, moon=True, seed=41, use_fx=True, grass=True)`

60 m ground patch rising into dark hills, dry grass tufts, scattered rocks, starry night sky, cool
moon rim light from behind (+Y). The fire at the origin is `fx.campfire(...)` (logs, stone ring,
coals, flames, sparks, smoke, 2 flickering lights) when `lib/fx.py` imports, otherwise a built-in
fallback (stone ring, logs, emissive flame cones, flickering light).

Anchors: `fire`, `grandfather` (top of a low boulder at (-0.95, 0.35), facing the child/fire),
`child` (small stone at (0.75, 0.55)), `handoff` (between them at hand height — where the lamp is
passed), `scroll_spot`. Cameras: `two_shot`, `over_shoulder`, `fire_low`, `wide`.
Lights: `fire` (fx light 0 or fallback), `fire_bounce` (warm up-fill), `moon`. `extra["fx"]` = the
fx.FX handle when used.

---------------------------------------------------------------------------------------------------

## Reusable props / helpers

| function | returns | notes |
|---|---|---|
| `oil_lamp(loc, rot_z=0, scale=1, light=True, energy=12, temp=2300, flame_strength=18, flicker=0.18, seed=0, name="oil_lamp", shadow=True, light_radius=0.012, parent=None, coll=None)` | `(lamp, flame, light_or_None)` | Herodian clay lamp (9 cm, nozzle +X), flame at the nozzle (per-frame flicker of light + flame), light is a child of the lamp → parent `lamp` to a hand bone/empty to carry it (s20a hand-off). Energy 20–60 W lights a face at 0.5–1 m. |
| `lamp_field(points, name="lamp_field", scale=1, flame_strength=16, seed=0, cluster_lights=0, cluster_size=3, light_per_lamp=2, temp=2000, coll=None)` | carrier object | hundreds of instanced lamps; points `(x,y,z[,yaw_deg])`. `cluster_lights>0` adds shadowless pooling lights. (`lib/fx.lamp_field` is the flame-only alternative.) |
| `night_world(strength=1, zenith, horizon, stars=1, star_dir=None, star_strength=60)` | Background node | night gradient + procedural stars (+ one bright star in `star_dir`). |
| `sky_world(sun_elevation, sun_rotation, strength, light_strength=None, air, dust, ozone, tint=None)` | lighting Background node | Nishita sky; camera sees `strength`, lighting uses `light_strength`. |
| `world_light_keys([(f, strength), ...])` | – | key `sky_world`'s lighting strength (e.g. dim when the camera enters a room). |
| `dust(center, size, count=600, radius=0.0035, color, emission=0, speed=0.08, amp=0.25, seed=0, name="dust", coll=None)` | object | GN dust motes drifting with scene time — **no bake**, lit by scene lights (sparkle in shafts). |
| `straw_scatter(carrier, density=1500, seed=0, keep_surface=True, tilt=0.35, density_attr=None, realize=True)` | modifier | straw strands on any mesh (density per m², optional float attribute/vertex group mask). |
| `flicker_light(light_obj, base=None, amount=0.18, speed=9, seed=0)` | light | keyed candle flicker on `.data.energy`. |
| `clay_jar(loc, height=0.55, ...)`, `clay_cup(loc, wine=True, ...)` | object | lathe props. |
| `gold_material(name, color, rough, relief=None, relief_scale, relief_strength, patina, hammered)` | material | burnished gold (+ optional relief map bump/patina). |
| `clay_material()`, `straw_material()`, `linen_material(color)` | material | shared look-dev materials. |
| `animate_tomb_stone(info, pairs)`, `animate_veil(info, pairs)`, `set_glory(info, pairs)` | – | see sets above. |
| `temple_relief_map()`, `veil_texture()` | path(s) | generated maps cached in `$WORK/cache/sets/` (regenerated automatically if missing, ~3 s). |

---------------------------------------------------------------------------------------------------

## PERF (measured; see report for the exact numbers)

All sets build in < 7 s (holy_of_holies ~4–7 s the first time it generates its textures, < 1 s after).
Render cost is dominated by: realized straw (stable), volumes (every set has haze; holy has 4
volume boxes), shadowed lights (each point light = 6 shadow views), and the many cluster lights in
the courtyard. Recommended shot settings:

| set | `ctx.samples` | `ctx.render_opts` |
|---|---|---|
| stable_cave | 6 | `{"volumetrics": "low"}` |
| garden_tomb | 6 | `{"volumetrics": "low"}` |
| holy_of_holies | 6 | `{"volumetrics": "low"}` (use `"medium"` only for the close glory end) |
| courtyard_assembly | 6 | `{"volumetrics": "low"}` |
| table_interior | 6–8 | `{"volumetrics": "low"}` |
| camp_night | 6 | `{"volumetrics": "low"}` |

Cheaper knobs: `stable_cave(straw_density=500)`, `fog=False`/`dust_motes=False`,
`holy_of_holies(smoke=False, shafts=False, holy_place=False)` for shots that never see the Holy
Place, `courtyard_assembly(lamps=250, stands=4)`, `table_interior(haze=False, steam=False)`.

## Gotchas

* **Build after `reset_scene`**; flicker/smoke keys span `scene.frame_end` at build time.
* EEVEE Next **world light leaks into closed rooms**. The tomb therefore uses near-zero world
  lighting + a shadowed sky-fill area light; if you swap the world, keep its lighting strength low or
  the chamber will look lit. The interiors (stable, table) use dark night worlds, so they are fine.
* Gold needs something to reflect: keep `probe=True` in the Holy of Holies, and keep at least some
  light in the room — with all lights off the gold reads black.
* The veil halves are shape-keyed meshes with a Solidify; don't apply modifiers or the "open" shape
  key breaks. The veil only parts; it does not tear.
* `info.facing` is +Y-forward yaw. lib/assets rigs face -Y → add 180°.
* Straw is a realized GN mesh on `objects["floor"]`, `manger_straw`, `hay_heap` — characters sitting
  on the straw may intersect strands slightly; lower `straw_density` locally or hide straw under them.
* `courtyard_assembly` lamps have no individual lights: characters holding lamps should get their own
  `oil_lamp(...)` (with light) parented to the hand for close shots.
* Never add a world volume (core rule) — every set uses finite `fog_box` volumes already.
* Generated textures live in `$WORK/cache/sets/` (`temple_relief_v4.png`, `veil_color_v4.png`,
  `veil_height_v4.png`); delete them to force regeneration.
