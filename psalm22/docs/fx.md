# fx — special effects (`psalm22/blender/lib/fx.py`)

```python
import sys; sys.path.insert(0, "/home/user/game1/psalm22/blender")
from lib import core as C
from lib import fx as FX
```

Every effect returns an **`FX` handle**: `fx.root` is an empty you can move / parent / animate, and the
parts are attributes (`fx.light`, `fx.walls`, ...). `print(fx)` lists them.

## Key facts (read first)

* **No baking.** All particles and deformations are closed-form functions of the scene frame,
  evaluated in Geometry Nodes. Any frame renders correctly in isolation (`--frames 57` works);
  **do not** set `ctx.needs_bake` for this module.
* **Effect time** is seconds: `T = (frame - frame0) / fps * time_scale`. Slow motion = `time_scale < 1`.
* **Billboards / fire cards face the scene's active camera at render time** (GN *Active Camera*),
  so you can create the camera before or after the effect. Pass `camera=` to `fire_cards` to override.
* **Flames are additive** (Emission + Transparent, BLENDED, no shadow casting). Their brightness is
  calibrated for AgX "Medium High Contrast" at exposure 0; scale with `strength=`.
* **Lights:** every `flame()` / `torch()` / `campfire()` adds point light(s) with an f-curve NOISE
  modifier for flicker (cheap, deterministic). Use `lamp_field()` for many lamps (few lights).
* **Moving emitters:** embers / sparks are emitted in the emitter's *local* space, so if you parent
  a torch to a walking person, the embers travel with the torch (fine for slow motion; fast swings
  will look "attached").
* Animated shader inputs use keyed Value nodes; GN uses Scene Time. **Do not** call
  `bpy.ops.ptcache.*` for these effects.
* Memory: EEVEE allocates ~0.5 GB more on the second rendered frame of a process; effects here add
  little (Earth textures ~150 MB, Red Sea meshes ~60k verts + ~1.5k spray quads).

---

## 1. Flames

### `flame(loc=(0,0,0), size=0.03, color_temp=1850, flicker=True, seed=0, light=True, light_energy=None, light_radius=None, shadow=True, lod="near", wind=(0,0,0), strength=1.0, style="candle", name="Flame", coll=None, parent=None) -> FX`
Small candle / oil-lamp flame: teardrop lathe mesh (16x14) with a procedural shader (yellow-white
core, orange rim/tip, blue root, darker inner cone, internal turbulence) + GN sway, plus a
flickering point light.

| param | meaning |
|---|---|
| `loc` | base of the flame (wick tip). World space, or `parent` space if `parent` given |
| `size` | flame height in m (candle 0.025–0.035, oil lamp 0.03–0.045) |
| `color_temp` | K of the luminous zone (1700 deep orange … 2200 yellow) |
| `flicker` | `False` steady, `True` = 1.0 (normal draft), float amount; > 1.6 switches to a *guttering* shader |
| `lod` | `"near"` (animated) or `"far"` (8x5 mesh, no noise/GN — distant lamps) |
| `wind` | tip lean as a fraction of the height, e.g. `(0.15, 0, 0)` |
| `light_energy` | W, default `1.2 * (size/0.03)**2 * strength` (≈ 1.2 W candle). Raise for interiors lit only by lamps |
| `light_radius` | soft-shadow radius (default `0.12*size`) |
| `parent` | object to parent the root to (e.g. an oil-lamp prop); `loc` is then local |

Returns `FX(root, mesh, light, modifier, material)`.

```python
lamp = ...                                   # your clay lamp prop
f = FX.flame((0.06, 0, 0.035), size=0.04, flicker=1.2, parent=lamp, light_energy=3.0)
```

### `lamp_field(points, size=0.035, color_temp=1850, flicker=True, lights=16, light_energy=None, shadow=False, strength=1.0, seed=0, name="LampField", coll=None) -> FX`
Hundreds of distant lamp flames as **one** GN instancer (far-LOD flame mesh, per-instance random
flicker in scale/tilt) + `lights` cluster point lights (k-means of the lamp positions, energy =
sum of members, soft radius = cluster spread, shadowless by default).
`points`: list of world positions (flame bases) or a mesh object (its vertices).
Returns `FX(root, obj, lights=[...], material, modifier)`.
Use for s17a (assembly with hundreds of lamps) and s20b (river of lights). Lamps nearer than ~3 m
from camera should use `flame()` instead.

```python
pts = [(x, y, C.height_at("Terrain", x, y) + 1.2) for x, y in path_points]   # hand height
FX.lamp_field(pts, size=0.04, lights=12, light_energy=2.0)
```

### `torch(loc=(0,0,0), flame_height=0.45, color_temp=1750, frame_start=1, frame_end=None, smoke=True, embers=True, stick=True, light_energy=60.0, shadow=True, wind=(0,0,0), strength=1.0, seed=0, name="Torch", coll=None, parent=None) -> FX`
Hand torch. `loc` = **top of the burning head** (flames start there). Builds a 0.75 m wooden stick
(below `loc`), a charred pitch head with ember cracks, 4 procedural **fire cards** (licking
tongues), a smoke volume column, rising embers (velocity-stretched streaks), a flickering light.
`wind` (m/s) drifts embers/smoke and leans the flames. Parent it to a hand with `parent=` (then
`loc` is in hand space) or move `fx.root`.
Returns `FX(root, stick, head, flames, light, smoke, embers)`.

### `campfire(loc=(0,0,0), size=1.0, color_temp=1700, frame_start=1, frame_end=None, logs=6, stones=True, smoke=True, sparks=True, light_energy=350.0, shadow=True, wind=(0,0,0), strength=1.0, seed=0, name="Campfire", coll=None) -> FX`
Campfire on the ground at `loc` (z = ground). `size=1` ≈ 0.95 m stone ring, flames up to ~1 m.
Teepee logs (bark PBR + charred upper halves with glowing cracks), stone ring (rock PBR), glowing
coal bed, 11 fire cards, rising sparks, smoke column, 2 flickering lights (main with soft shadows).
Returns `FX(root, coals, logs, stones, flames, lights=[main, fill], sparks, smoke)`.
For s20a (small fire by grandfather & child) use `size=0.6, light_energy=180`.

### `fire_cards(name, cards, temp=1800, strength=1.0, flicker=1.0, lean=(0,0,0), seed=0, camera=None, coll=None, parent=None) -> Object`
Low level: your own cluster of procedural fire cards. `cards = [(x, y, z, width, height), ...]`
(z = flame base, object space). Cards are vertical and rotate about Z toward the camera
(so don't look straight down on them). Good for burning brands, a fire in a brazier, etc.

---

## 2. `red_sea(ctx=None, length=640, width=36, height=45, center_y=0, shore_slope=150, lighting=True, sun_elevation=7.0, spray=True, spray_rate=0.12, mist=True, mist_density=0.0022, haze=0.0006, collapse=None, zipper=(None, 60.0), seabed="coast_sand_rocks_02", seabed_scale=0.25, puddles=0.12, glow=1.0, foam=1.0, frame_start=1, frame_end=None, wind=(0, 2.0, 0.6), seed=0, name="RedSea", coll=None) -> FX`

The parted Red Sea for s04a / s04b.

**Layout:** corridor along **+Y** (toward the far shore and the dawn sun), centred on `x = 0`, from
`y0 = center_y - length/2` to `y1 = center_y + length/2`. Seabed z = 0 in the middle, rising over
`shore_slope` m at each end to sea level (z = `height`) and dry land beyond. Walls are `height` m
(top = sea level), the corridor floor is `width` m wide. Open sea planes continue outside the walls.

* **Walls:** GN-deformed meshes (~30k verts each): slow bulges + churn, rolling heaving crest;
  shader = dark deep water, glossy large-scale chop, emerald translucency rising toward the crest
  with swirling depth variation, crest / foot foam, sparse face foam. Wall noise is stretched along
  Y on purpose (walls are seen foreshortened from inside the corridor).
* **Seabed:** Poly Haven texture + `wet_material` (darkened, glossy, sand ripples, mirror puddles)
  + macro variation to hide tiling.
* **Spray:** camera-facing translucent puffs lifting off both crests and drifting with `wind`.
* **Mist / haze:** a low fog box along the corridor + a large thin haze box (aerial perspective).
* **Lighting** (`lighting=True`): `qwantani_sunrise_puresky` HDRI rotated so its sun is over the far
  shore (+Y) + sun lamp at `sun_elevation` from +Y (backlight). Set `lighting=False` to do your own.
* **Collapse** (`collapse=(start_frame, duration_frames)`): walls lean in (tops first), slump and
  meet; whitewater churn; a dense spray burst where they meet. `zipper=(y_start, speed m/s)`:
  collapse starts at `y_start` (default: 20 % of the length before the centre, i.e. away from the
  destination shore) and spreads both ways at `speed`.

Returns `FX(root, seabed, walls=[L, R], sea=[L, R], spray, crash (if collapse), mist, haze, sun)`
plus **`fx.floor_at(x, y) -> z`** (place people / props on the seabed) and
**`fx.corridor = {"x": (-w/2, w/2), "y": (y0, y1), "H": height, "shore_slope": ...}`**.

```python
def build(ctx):
    sea = FX.red_sea(ctx)                                   # s04a
    y = -110.0
    cam = C.camera((0, y, sea.floor_at(0, y) + 1.8), (0, y + 100, 12), lens=28)
    for (x, yy) in crowd_xy:                                # people on the wet seabed
        person.location = (x, yy, sea.floor_at(x, yy))
    ctx.render_opts = {"volumetrics": "low", "raytracing": True}   # strongly recommended

def build(ctx):                                             # s04b: crash seen from the far shore
    sea = FX.red_sea(ctx, collapse=(60, 72), zipper=(None, 60.0))
    y1 = sea.corridor["y"][1]
    C.camera((6, y1 + 25, sea.floor_at(0, y1 + 25) + 7), (0, 0, 22), lens=35)
```

**Strongly recommended:** `ctx.render_opts["raytracing"] = True`. Without it EEVEE can only reflect
the sky probe, so the walls look paler/glassier and puddles reflect only sky; the module fakes it by
fading wall specular toward the foot, but RT (screen-space) is clearly better (walls show dark glassy
depth, seabed reflects the walls). See PERF for the cost.

---

## 3. `earth_from_space(ctx=None, radius=6.371, center=(0,0,0), focus=(32.0, 27.0), sunrise_lon=(58.0, -12.0), declination=6.0, frame_start=1, frame_end=None, ease=True, clouds=True, night_lights=True, atmosphere=True, stars=True, camera=True, cam_dist=(4.1, 3.4), cam_offset=(0.0, -0.12), lens=35, sun_energy=4.5, night_strength=3.5, cloud_spin=0.6, name="Earth", coll=None) -> FX`

Earth for s18a: NASA Blue Marble (April) day map with ocean specular (derived water mask),
Black Marble city lights on the night side, NASA cloud layer (shell at 1.006 R), atmosphere shell
(1.032 R; blue limb glow on the day side, orange twilight band at the terminator, haze over the
disc), procedural star field world, and a **sunrise terminator sweeping west**: the sub-solar
longitude is keyed per frame identically in the shaders and on the Sun lamp.

| param | meaning |
|---|---|
| `radius` | globe radius (6.371 ⇒ 1 unit = 1000 km) |
| `focus` | (lon, lat) turned toward a camera on −Y. Default = Levant/Egypt/Arabia |
| `sunrise_lon` | (start, end) longitude (deg E) of the morning terminator at the equator. Default: dawn on Arabia/Middle East first (58 E) sweeping over Egypt, the Levant, Europe/Africa (−12) |
| `ease` | True: gentle ease-out; `"inout"`: cosine ease; False: linear |
| `camera` | build an animated camera: `cam_dist` (start, end) in radii from the centre, `cam_offset` (x, z) of the look-at point in radii (negative z ⇒ globe sits higher in frame), `lens` |
| `stars` | True / float strength (world shader; replaces your world!) |

Returns `FX(root, globe, clouds, atmosphere, sun, camera)` + `fx.sun_lon(frame) -> radians`.
The world is replaced by the star field when `stars` is truthy. Textures are cached in
`/opt/assets/earth/` (downloaded from NASA on first use if missing).
The sun lamp is shadowless by design (an animated sun shadow over a globe costs ~200 MB extra RAM
per frame and is not needed).

```python
def build(ctx):
    e = FX.earth_from_space(ctx)                 # complete shot incl. camera and stars
    # or: e = FX.earth_from_space(ctx, camera=False); then your own camera looking at e.root
    ctx.post.update({"bloom": 0.4})
```

---

## 4. Ash and dust

### `ash_disintegrate(obj, start_frame, duration, direction=(1,0,0), wind=None, count=30000, flake_size=0.01, life=2.5, jitter=0.25, noise_scale=None, edge_glow=True, glow_color=(1.0,0.62,0.22), glow=4.0, ash_color=(0.05,0.045,0.04), keep_mesh=True, mode="flakes", turbulence=0.4, gravity=-0.4, seed=0) -> FX`
Adds a GN modifier (last in the stack, so it works on an armature-posed mesh) that deletes the
faces behind a front sweeping across the object along `direction` (world space) between
`start_frame` and `start_frame + duration`, and releases `count` ash flakes from the surface as the
front passes. Flakes glow (`glow_color`) when released and cool to dark ash, tumbling and streaming
away with `wind` (default: faster than the front along `direction`, plus lift).
`edge_glow=True` also injects a glowing rim + charring band into the object's own materials
(Principled-based) — reads attribute `fx_dis`.
`mode="points"` uses a point cloud instead of instanced flakes (cheaper, less detail).
Returns `FX(root=obj, modifier, material)`.

```python
lion = ...                                  # mesh (or rigged) silhouette made of dark ash material
FX.ash_disintegrate(lion, start_frame=40, duration=80, direction=(1, 0, 0.2),
                    glow_color=(1.0, 0.78, 0.4), count=40000, flake_size=0.012)
```
Tip (s14c): `direction` = direction the golden light advances; match `start_frame`/`duration` to
the light sweep. Object scale is handled (flake_size is in world metres).

### `dust_burst(loc, start_frame, size=1.0, color=(0.72,0.62,0.5), count=60, grains=1500, direction=(0,0,1), wind=(0.6,0,0), floor=None, opacity=0.9, life=3.0, seed=0, name="DustBurst", coll=None) -> FX`
One-shot dust puff (hoof strike, a body falling, a stone dropped): expanding soft billboard puffs
that settle and drift with `wind`, plus grains thrown out ballistically. `size` ≈ cloud radius after
~1 s. `floor` = ground z (default `loc.z`). Returns `FX(root, puffs, grains)`.
Call it once per impact (cheap: 60 quads + 1500 points).

### `dust_pour(hand_location, start_frame, end_frame=None, rate=2500, opening=0.03, wind=(1.2,0,0.1), color=(0.62,0.55,0.46), haze=True, floor=0.0, grain_size=0.0012, life=4.0, gusts=0.25, seed=0, name="DustPour", coll=None) -> FX`
Fine dust trickling from an opening hand (s11b): grains emitted from an ellipse of radius `opening`
at `hand_location` (more at first, tapering as the hand empties), falling with drag, pushed by
`wind`, skating along the ground (`floor` z) and fading; `haze` adds soft dust wisps peeling off the
stream. Returns `FX(root, grains, haze)`.

---

## 5. `water_pour(lip=(0,0,0.7), direction=(1,0), speed=0.55, stream_radius=0.009, start_frame=1, end_frame=None, time_scale=0.25, ground_z=0.0, jar=True, jar_tilt=(95,118), ground=None, ground_material=None, puddle_radius=0.32, drain_time=1.6, splash=True, droplets=True, seed=0, name="WaterPour", coll=None) -> FX`

Slow-motion pour for s10a (all fake, no fluid sim, no bake):
* **stream**: GN tube along the exact parabola from `lip` (exit velocity `direction*speed` slightly
  downward), thinning with speed (continuity), twisting elliptical section, ripples/beads travelling
  with the water, tapered front, thinning and detaching tail after `end_frame`.
* **droplets** peeling off the lower stream + **splash** droplets at the impact (closed-form
  ballistic, killed at the ground), water material.
* **puddle**: clear, slightly muddy water film (fresnel mix of tinted transparency + mirror gloss)
  growing from the impact with noisy lobes and irregular ripples while pouring; after the last water
  lands it **drains** over `drain_time` *screen* seconds by sinking below the plate tops, so water
  lingers only in the cracks (needs a cracked / displaced ground, e.g. `ground=True`).
* **wet patch**: injected into `ground_material` (or the built ground) — darker, glossier, grows
  with the puddle; afterwards the plates dry slightly while the cracks stay dark and wet.
* **jar** (`jar=True`): terracotta lathe jar (with wet lip) whose lip pivot sits at `lip`, tilting
  from `jar_tilt[0]` to `[1]` degrees. Use `jar=False` with your own jar and put `lip` at its spout.
* **ground** (`ground=True`): 2.4 m `cracked_ground()` patch centred on the impact.

`time_scale` = slow-motion factor (0.25 ⇒ 4x slower). Returns
`FX(root, stream, droplets, puddle, ground, jar, jar_pivot, impact=(x, y, z))`.
Use `ctx.render_opts["raytracing"] = True` (refraction & reflections of the water).

Also exported: `water_material(name, rough, tint, raytrace)`, `clay_jar(height, name, coll, material)`.

---

## 6. `melting_candle(loc=(0,0,0), start_frame=1, end_frame=None, height=(0.14, 0.035), radius=0.022, drips=9, pool_radius=0.075, flame_size=0.03, flicker=2.4, light_energy=None, color=(0.78,0.38,0.07), seed=0, name="MeltCandle", coll=None) -> FX`

Time-lapse beeswax pillar for s10b: the top sinks linearly from `height[0]` to `height[1]` between
`start_frame` and `end_frame` (molten cup + irregular rim), `drips` drips run down the sides
(born at random moments, flowing fast then solidifying as ridges; their upper part melts away with
the top), a pool spreads around the base with lobed edges, the wick and a **guttering** `flame()`
ride down with the top, and a shadowless amber fill light inside the candle imitates light leaking
through the wax onto the pool/table. Wax shader: amber subsurface, honeycomb-ish micro bump, glow
near the flame (attribute `fx_below`).
Returns `FX(root, body, drips, pool, wick, flame (an FX), top (empty riding the top), glow_light,
material, height_at(frame) -> m)`.

```python
def build(ctx):
    C.world_color((0.003, 0.003, 0.004))
    table = ...
    c = FX.melting_candle((0, 0, table_top_z), 1, ctx.nframes, seed=2)
    C.camera((0, -0.42, 0.13), (0, 0, 0.065), lens=55, fstop=4.0)
```

---

## Helpers you may reuse

| function | what |
|---|---|
| `wet_material(m, wetness=0.8, puddles=0.35, puddle_scale=0.06, ripples=0.0, ripple_dir=(1,0), ripple_len=0.45, darken=0.45, mask=None)` | inject wetness into any Principled material (e.g. `C.mat_pbr`): darker, glossier, flat mirror puddles in world-space noise lows, optional sand ripples. `mask(nb) -> socket` limits it |
| `hdri_rotation_for_sun((x, y), sun_u=0.600)` | degrees for `C.world_hdri(rotation=...)` that put a Poly Haven HDRI's sun toward world direction (x, y). All cached Poly Haven skies have the sun at u≈0.60 (e.g. `qwantani_sunrise_puresky` at 2.1° elevation) |
| `wax_material(...)`, `water_material(...)` | materials used above |
| `clay_jar(height=0.32)` | earthen jar mesh (base at z=0, lip at z=height), terracotta shader with wet lip streaks |
| `cracked_ground(loc, size=2.4, res=260, cell=0.12, depth=0.018, width=0.08, texture="brown_mud_dry", tint, seed)` | parched polygonal mud-crack patch: GN voronoi grooves + curled plate edges, PBR texture with dark crack interiors (attribute `fx_crack`). ~68k verts at res 260; use for s10a / s11a close-ups |
| `fire_cards(...)` | procedural fire sprites (see 1) |

## PERF

See the report section (timings were measured on a heavily loaded shared machine; see notes there).

## Gotchas

* The flame light energies are physically small (candle ≈ 1.2 W). In a scene lit only by lamps,
  either raise `light_energy` or the camera exposure (`ctx.render_opts["exposure"]`).
* `earth_from_space(stars=True)` **replaces the world** shader.
* `red_sea(lighting=True)` replaces the world (HDRI) and adds a sun; pass `lighting=False` to light
  it yourself (sun from +Y, low, looks best).
* Fire cards are cylindrical billboards: avoid top-down views of torches/campfires.
* Don't animate the `torch` root faster than ~2 m/s if embers are visible (they're emitted in
  local space).
* `ash_disintegrate` deletes faces of the target (GN modifier "Ash"); disable the modifier to get
  the intact object back. `edge_glow` edits the object's materials in place (once).
* All particle objects are shadowless (`visible_shadow=False`); fire/smoke too.
