# `lib/env.py` — outdoor environments (Golgotha, Judean hills, Gethsemane, dawn plain)

Owner: **env**. Shared, consistent outdoor sets + skies/light/atmosphere for every exterior shot.
Everything is built from code (Blender 4.5 / EEVEE Next) with CC0 Poly Haven assets; heavy derived data
(decimated rocks, generated trees, HDRI analysis) is cached in `/opt/assets/env/` so rebuilding a shot is fast
(typical build 3–10 s).

```python
import sys; sys.path.insert(0, "/home/user/game1/psalm22/blender")
from lib import core as C, env as E
```

---------------------------------------------------------------------------------------------------
## 1. Quick start (copy-paste)

```python
from mathutils import Vector
from lib import core as C, env as E

def build(ctx):
    A = E.golgotha(ctx, mood="golden", view="wide")   # hill + 3 crosses + skull cliff + Jerusalem + sky + light
                                                      # view= culls scatter outside the camera cone (faster)
    cam_spec = A["cams"]["wide"]                  # suggested framings: wide, wide_low, skull, medium, low, from_cross, aerial
    cam = C.camera(loc=cam_spec["loc"], target=cam_spec["target"], lens=cam_spec["lens"])

    c = A["crosses"]["center"]                    # anchors for the characters module
    # c["hand_l"], c["hand_r"], c["feet"], c["head"], c["sign"], c["beam_z"], c["base"], c["front"] ...
    top = Vector(c["beam"])
    def path(f):                                  # slow push-in
        u = C.ease_in_out(ctx.u(f))
        return (Vector(cam_spec["loc"]).lerp(Vector((-2, -40, 6)), u), top)
    C.animate_camera(cam, path)
```

Other environments:

```python
A = E.judean_hills(ctx, timelapse=True)            # s02a: day -> golden -> dusk -> night (stars), dead tree
A = E.olive_grove(ctx)                             # s02b / s08: Gethsemane at night, prayer rock, mist, moon shafts
A = E.plain_dawn(ctx, time_of_day="sunrise")       # s16a / s18b: crowds at sunrise, distant hill with empty cross
A = E.plain_dawn(ctx, time_of_day="predawn", procession=True)   # s20b river of lamps
E.dust_storm(ctx, color=(0.55, 0.3, 0.16), density=0.03, speed=6)  # s09a, add on top of golgotha(mood="eclipse")
```

---------------------------------------------------------------------------------------------------
## 2. Environments

All builders take `ctx` (core.Ctx) first, create everything in the current scene, and return a dict of
**anchors** (plain tuples, metres, world space). Every builder also returns:

| key | meaning |
|---|---|
| `ground(x, y)` | analytic terrain height (fast, numpy-vectorised; accepts floats or arrays) |
| `ground_z(x, y)` | exact height by raycast on the built meshes (terrain + cliff/rock), use for feet/props |
| `cams` | `{name: dict(loc=, target=, lens=)}` suggested portrait framings (pass to `C.camera(**...)`) |
| `sky` | result of `E.sky()` (sun object `["sun"]`, `["sun_dir"]` towards the sun, `["sun_el"]`, `["preset"]`) |
| `terrain` | the terrain object |
| `build_time` | seconds |

### 2.1 `golgotha(ctx, mood="golden", crosses=3, center_occupied=True, sign=True, city=True, seed=0, ...)`

Rocky hill outside Jerusalem. **Layout (fixed for consistency across shots):**

* hill top ≈ `(0, 0, 11)`; the plateau is trodden bare around the crosses;
* crosses stand on the top in a shallow arc and **face −Y** (the default camera side):
  centre `(0, 0.6)`, left `(-4.5, 1.7)` (rot 9°), right `(4.7, 1.5)` (rot −11°);
* the **skull cliff** (weathered limestone scarp with two eroded eye-caves, nose hollow, broken mouth
  ledge — subtle, natural) faces −Y directly below the crosses, foot at y ≈ −12, z ≈ 2…3.5, top ≈ 10;
* a talus of boulders at the cliff foot, a trodden path winding up the west flank from the south-west plain;
* plain around z ≈ 0, a shallow wadi at y ≈ −70; distant hills and a mountain ring hide the terrain edge
  (4.2 km);
* **Jerusalem** towards +Y (behind the hill): walls/towers from ~300 m, Herod's three towers on the left,
  the Gennath gate, ~2000 houses, the Temple Mount and the white-and-gold sanctuary (right-back, ~800 m).
  It is seen above/around the hill from the plateau and from raised/side cameras;
* sky/sun per `mood`, haze matched to the sky, optional god-ray fog and floating dust.

Parameters:

| param | default | notes |
|---|---|---|
| `mood` | `"golden"` | `golden` (bright late sun, thumbnail/finale), `noon`, `eclipse` (darkness at midday: dim red-brown sky, dull red sun disk), `storm`, `dawn`, `sunrise`, `night` |
| `crosses` | 3 | 1 = centre only, 2 = the two side crosses, 3 = all |
| `center_occupied` | True | keeps a 1.3 m keep-out in front of the centre cross (no rocks/grass where the figure hangs/feet are). The figure itself comes from the characters module |
| `sign` | True | placard on the centre cross (`core.wooden_cross(sign=True)`) |
| `city` | True | build Jerusalem (adds ~0.3 s build; costs little to render) |
| `seed` | 0 | scatter variation (layout stays the same) |
| `sun_az` | preset | override sun azimuth (core.sun convention: 0 = sun at −Y/behind a camera looking +Y; 180 = sun at +Y = backlight in the default view). The HDRI is rotated to match |
| `grass`, `rocks`, `bushes` | 1.0 | density multipliers (0 disables) |
| `near_detail` | 1.0 | pebbles + wedge stones at the cross feet (close-ups at the foot of the cross) |
| `rays` | False | volumetric god-ray fog + moving cloud-shadow gobo. **Opt-in for hero shots**: roughly doubles the frame time (measured +50 cpu-s/frame); shafts are subtle. Cheaper alternative: `ctx.post["sun_dir"]` (always written by `sky()`) lets the compositor add light streaks |
| `fog` | False | light volumetric air box (adds depth near the hill; +~1.2 s/frame). The haze already gives aerial perspective |
| `view` | None | `"wide"`, `"wide_low"`, `"skull"` or a dict `loc/target/lens(/margin/near)` or a list of such dicts (camera path keys): scatter (grass/rocks/bushes) is only created inside that camera's horizontal view cone + 25° margin (+ always within 8 m of the camera). Saves ~20% render time. Leave None if the camera turns around |
| `dust` | per mood | floating backlit dust specks around the plateau (procedural, no bake) |
| `clouds` | per mood | coverage 0..1 of the animated procedural cloud layer in the sky |
| `skull` | 1.0 | 0 = no cliff; 0.5 = subtler eye/nose hollows |
| `cross_height` / `side_cross_height` | 4.4 / 4.0 | above ground (the upright is sunk 0.45 m) |
| `cross_material` | rough_wood | any material |
| `sky_over` | None | dict of SKY_PRESETS overrides, e.g. `dict(hdri="table_mountain_1_puresky", exposure=0.3)` |

Returns (in addition to the common keys):

* `crosses`: `{"center"|"left"|"right": anchors}` with, for each cross: `base` (ground contact),
  `root` (the cross root empty — animate/hide it), `top`, `beam` (crossbeam centre), `beam_z`, `beam_l`,
  `beam_r`, `front` (unit vector the cross faces), `hand_l`, `hand_r` (nail points on the front face of the
  beam ends), `head` (≈ head position of a crucified figure), `chest`, `feet` (≈ 1.72 m below the beam,
  on the front face), `sign` (placard centre), `height`.
* `hill_top`, `crowd_region` `(x0, y0, x1, y1)` = the plateau in front of the crosses (people stand here),
  `skull` = `{eye_l, eye_r, face_center}`, `cliff` (object), `city` = jerusalem() result
  (`temple`, `gate`, `towers`, `objects`), `rays` / `fog` / `dust` objects.
* `cams`: `wide` (cliff + crosses from the plain, the s00 framing), `wide_low`, `skull` (closer, crosses larger),
  `medium` (on the plateau, centre cross), `low` (looking up at the centre cross), `from_cross` (from the
  crucified figure's head down onto the crowd), `aerial`.

### 2.2 `judean_hills(ctx, mood="noon", timelapse=False, hour0=13, hour1=21, seed=0, terraces=0.6, olives=1, dead_tree_=True, rocks=1, grass=1, view_az=250, sun_az=None, clouds=None)`

Rolling limestone hills: a rocky spur (camera) with a **lone dead tree** at its edge, a valley, terraced
slopes with dry-stone risers, garrigue scrub patches, clustered olive groves, boulders, dry grass.
The vista is designed along `view_az` (compass degrees, 0 = +Y north, 90 = +X east; default 250 = WSW,
towards the sunset). `timelapse=True` animates the whole sky/light over the shot (see `timelapse_sky`).

Returns: `dead_tree` (object), `dead_tree_pos`, `knoll`, `cams` {`wide` (behind the tree over the
valley), `low` (looking up the tree), `high`}, `timelapse` (when animated: `keys` list of
`(frame, hour, sun_el, compass_az)`, `sun`, `moon` lamps).

### 2.3 `olive_grove(ctx, mood="night", seed=0, trees=14, moon_az=200, moon_el=40, mist=True, rays=True, city_lights=True, motes=True, detail=1.0)`

Gethsemane at night. Prayer rock at the origin clearing; gnarled olive trees (2 full-detail, 3 mid, many
far LODs) on soft terraces with stone walls; leaf litter ground, sparse grass; moonlight (cool, from
`moon_az`/`moon_el`) + stars + moon disk; low drifting mist (noise fog, wind) and a thin fog layer for moon
shafts through the canopy; faint glinting motes; Jerusalem as a lamp-lit silhouette across the Kidron (−X).

Returns: `rock`, `rock_top` (hand-rest point on the near edge of the rock top), `rock_top_center`,
`kneel` (ground point in front of the rock, figure faces `kneel_facing` = +Y), `clearing`, `trees`
(positions), `mob_path` (24 points from the west towards the clearing, for torches, s08), `flee_dir`,
`cams` {`wide`, `medium`, `dolly_a` → `dolly_b` (lateral dolly), `low`, `mob`}.

### 2.4 `plain_dawn(ctx, time_of_day="sunrise", seed=0, cross_hill=True, hillside=0.6, hills=0.5, grass_kind="mixed", sun_az=None, procession=False, grass=1, rays=True)`

Vast plain / gentle hillside for crowds, facing +Y where the sun rises (slightly right).
`cross_hill` adds a distant hill (≈ `(25, 330)`, +34 m) with an **empty cross** (5.6 m) catching the sun.
`time_of_day`: `sunrise` (sun just up, warm rays), `dawn` (pre-sunrise pink/blue), `predawn` (deep blue
night, faint stars, horizon glow — for the river of lamps). `hillside` tilts the crowd area down towards
the sun (s16a), `hills` makes the land more rolling. `grass_kind`: `mixed` | `dry` | `green`.

Returns: `crowd_region` (x0, y0, x1, y1), `crowd_points(n, seed_, region=None, spacing=0.9)` → list of
ground points for people, `cross` (cross anchors like golgotha's), `cross_hill_top`, `procession`
(list of 60 points winding away across the hills, when `procession=True`), `cams` {`behind_crowd`
(s18b), `crane_low` → `crane_high` (s16a crane up towards the sun), `wide`}.

### 2.5 Suggested use per shot (keeps the film consistent)

| shots | call |
|---|---|
| s00 title | `golgotha(ctx, "golden", view="wide")`, cam `wide` (push-in/rise); optional `rays=True` (hero, slow) |
| s01a face, "light dims" | `golgotha(ctx, "golden", ...)` + `sky_transition(ctx, "golden", "eclipse", f0, f1)`; figure at `crosses["center"]` |
| s01b pull-away | `golgotha(ctx, "eclipse", grass=0.6)` (no `view`: the camera travels), cams `low` → `aerial` |
| s02a time-lapse | `judean_hills(ctx, timelapse=True)`, cam `wide` |
| s02b, s08 Gethsemane | `olive_grove(ctx)`; figure kneels at `kneel`, hands on `rock_top`; torches along `mob_path` |
| s05, s06a/b, s07b, s12b, s13a/b | `golgotha(ctx, "eclipse", view=...)`; `from_cross` cam for s06a; `crowd_region` for people |
| s09a bulls | `golgotha(ctx, "eclipse")` + `dust_storm(ctx, center=(0, -5, hill_top_z - 6), size=(120,120,30))` |
| s11a potsherd | `golgotha(ctx, "noon", crosses=1, near_detail=1)` close to the ground, or a custom close-up |
| s11b skull face, fading light | `golgotha(ctx, "eclipse")` (+ `sky_transition` to `"night"`), cam `skull` |
| s12a dusk dogs | `golgotha(ctx, "sunrise", sun_az=200)` (low warm sun reads as dusk) |
| s14a light breaks | `golgotha(ctx, "eclipse")` + `sky_transition(ctx, "eclipse", "golden", f0, f1)`, `rays=True` if affordable |
| s16a hillside crowd | `plain_dawn(ctx, "sunrise", hillside=0.8)`, cams `crane_low` → `crane_high` |
| s18b nations bow | `plain_dawn(ctx, "sunrise")`, cam `behind_crowd`, longer lens (50–85 mm) to enlarge the far cross |
| s19a/b crowns, old man | `golgotha(ctx, "sunrise", crosses=1, center_occupied=False)` at the foot of the empty cross |
| s20b river of lamps | `plain_dawn(ctx, "predawn", procession=True, hills=1.0)`; lamps along `procession` |
| s20c finale | `golgotha(ctx, "golden" or "sunrise", crosses=1, center_occupied=False, view=...)` |

---------------------------------------------------------------------------------------------------
## 3. Sky, light, atmosphere

### `sky(mood="golden", sun_az=None, rotation=None, clouds=None, stars=None, moon=None, cfg=None, ctx=None, keep_sun=False, **overrides)`
Builds the world (HDRI rotated so its sun matches `sun_az`; HDRI ground replaced by the horizon colour),
a matching **sun lamp** (irradiance measured from the HDRI's sun, tinted), haze colours, optional
procedural cloud layer / stars / moon / dull sun disk. Lighting uses a clamped copy of the HDRI (no double
sun), the camera sees the full HDRI. Returns dict: `sun` (light object), `sun_dir`, `sun_el`,
`sun_energy`, `horizon`, `haze_color`, `hdri_rotation`, `nodes`, `preset`.
Calling it again replaces the previous world + sun.

### `sky_transition(ctx, mood_a="golden", mood_b="eclipse", f0=1, f1=None, over_a=None, over_b=None, ease=True)`
Cross-fades sky, sun (direction/energy/colour), haze and exposure from one mood to another between frames
`f0..f1` (both skies are built into one world, mixed via the uniform scene property `env_sky_mix`, so it is
cheap per frame). Call it **after** the environment builder (which builds its own static sky):
`A = E.golgotha(ctx, mood="golden"); E.sky_transition(ctx, "golden", "eclipse", 1, ctx.nframes)`.
Writes `ctx.post["grade_from"]` / `["grade"]`. Returns `dict(sun, a, b)`. Verified: golden → eclipse.

### `SKY_PRESETS` / `sky_preset(name, **overrides)`
`golden, noon, eclipse, storm, dawn, sunrise, night`. Keys: `hdri`, `sun_az`, `sun_el` (sun lamp / disk
elevation; for HDRIs only the azimuth of the HDRI sun is matched), `key` (target luminance of the HDRI
horizon — normalises exposure across HDRIs), `strength` (lighting), `bg` (visible sky), `sun_energy`
(absolute sun W/m², else measured from the HDRI × `sun_mult`, capped by `sun_max`), `clamp_sun`
(hide the HDRI's own sun from the camera: multiple of the sky clamp), `tint`, `sat`,
`sun_tint`, `sun_angle`, `haze_density`, `haze_tint`, `fog`, `fog_density`, `exposure`, `grade`
(compositor hint written to `ctx.post["grade"]`), `clouds`, `cloud_opts`, `sun_disk` (dict el, size,
color, strength, glow), `stars`, `moon`, `moon_az`, `moon_el`, `moon_light`, `horizon`, `zenith`.

### `night_sky(stars=True, moon=True, moon_az=210, moon_el=32, moon_light=0.35, strength=1, ctx=None, horizon=..., zenith=..., star_strength=1, clouds=0)`
Procedural night (gradient + ~1 px stars + moon disk/glow) and a cool moonlight sun lamp named `Moon`.

### `clouds_layer(coverage=0.5, height=1500, scale=0.00035, speed=(6, 2), color=..., shadow=..., opacity=0.92, evolve=0.05)`
Adds/replaces an animated flat cloud layer in the world shader over the current sky (keeps the sun
lamp). `speed` in m/s (60–200 for time-lapse streaks). Animated through scene properties (cheap).

### `timelapse_sky(ctx, hour0=13, hour1=21, f0=1, f1=None, clouds=0.35, cloud_speed=(90, 30), stars=True, moon=True, sun_max=4.5, exposure_night=1.2)`
Analytic day→night sky (zenith/horizon/sun-glow palette by solar elevation, sun disk, stars fading in,
fast clouds), sun lamp following the real solar arc for Jerusalem in April (`sun_dir_at(hour)`), moonlight
fading in, haze colour and a gentle exposure lift at night — all keyed per frame. Uses only uniform
(scene-property) animation, so frames don't recompile shaders.

### Haze (aerial perspective)
Every env material is routed through the shared `ENV_Haze` node group (`hazify(mat)`), which blends
towards the haze colour with view distance and height. Parameters are scene properties `env_haze_*`.
`set_haze(color=, density=, falloff=, start=, sun_color=, sun_dir=, sun_mix=, sun_power=, max=, frame=None)`
(frame → keyframe), `get_haze()`. **Use `E.hazify(material)` on your own outdoor materials** (characters,
props far away) so they sit in the same air.

### `god_rays(center=(0,0,0), size=(220,220,70), density=0.006, color=(1,.85,.65), coverage=0.55, gobo_height=None, anisotropy=0.6, speed=(2.5,.8), seed=0, gobo=True)`
Fog box lit by the sun + a moving invisible cloud-shadow plane (`cloud_shadows`) so shafts fan through the
gaps. Strongest looking towards a low sun. Returns `dict(fog=, gobo=)`.

### `fog_volume(center, size, density, color, anisotropy, noise_scale=None, noise_amount=0.6, height_falloff=0, name, wind=(0,0,0))`
Finite fog box (never a world volume). `noise_scale` adds wisps, `wind` (m/s) animates them (object
property → cheap). `height_falloff` thins it with height.

### `cloud_shadows(height=180, size=1600, coverage=0.45, scale=0.006, center=(0,0), speed=(3,1), softness=0.08)`
Camera-invisible plane casting moving cloud shadows (also usable without fog for sweeping light).

### `dust_motes(center, size, count=1500, radius=0.0025, color, emission=0.4, drift=(.15,.05,.02), turbulence=0.4, seed=0)`
Floating specks via Geometry Nodes (scene time driven, wrapped in the box — no particle bake needed).

### `dust_storm(ctx, color=(0.55,0.3,0.16), density=0.03, speed=6.0, center=(0,0,0), size=(160,160,40), direction=(1,.3,0), motes=True, sheets=True)`
Wind-driven noisy dust fog + dense low ground sheets + fast specks; raises the haze. For s09a combine with
`golgotha(ctx, mood="eclipse")`.

---------------------------------------------------------------------------------------------------
## 4. Building blocks

| function | returns | notes |
|---|---|---|
| `scatter(objects, terrain=None, count=100, region=..., seed=0, scale=(0.7,1.3), align=0.3, sink=0.05, max_slope=None, min_slope=None, zrange=None, density=None, exclude=(), min_dist=0, tilt=0, weights=None, name="Scatter", zscale=None, yaw=(0,360), return_points=False)` | instancer object | raycast placement onto all registered grounds; `objects` = prototype objects or Poly Haven model names; `region` rect `(x0,y0,x1,y1)`, `("circle",cx,cy,r)`, `("ring",cx,cy,r0,r1)` or `callable(rnd, n)`; `density(X, Y)` vectorised probability; `exclude=[(x,y,r)]`; `sink<0` buries a fraction of the height |
| `set_view(view)` | | restrict following `scatter` calls to a camera cone (see golgotha `view`); `set_view(None)` to reset |
| `place(proto, loc, rot=(0,0,0) deg, scale=1, name=None)` | object | one linked copy of a prototype |
| `instancer(name, protos, pos, rot, scl, idx, realize=False, shadows=True)` | object | raw GN instancing of arrays (`realize=True` merges into one mesh: fewer objects but no per-instance culling — measured slower here) |
| `rock_protos(kind="boulders"/"rocks"/"stones"/"cliff", tint=, sat=, value=, decimate=None)` | [obj] | limestone-shaded Poly Haven rocks (one shared material). One tint per kind per scene |
| `ph_protos(asset, max_polys=12000)` | [obj] | any Poly Haven model as prototypes (best LOD ≤ max_polys) |
| `olive_tree(seed=0, age=1.0, size=1.0, leaves=True, leaf_density=1.0, lod=0)` | proto | gnarled multi-strand trunk, clumped canopy of real folded leaves with silver undersides. lod0 ≈ 150k polys (hero), lod1 ≈ 40k (mid), lod2 ≈ 8k blob crown (far) |
| `dead_tree(seed=0, size=1.0)` | proto | bleached leafless tree ~4.5 m |
| `thorn_bush(seed=0, size=1.0, leafy=0.5)` | proto | twiggy thorn shrub 0.6–1 m (~4–7k polys) |
| `shrub_blob(seed=0, size=1.0, dry=0.3)` | proto | ~200-tri lumpy shrub for distances > 40 m |
| `grass_tuft(seed, blades, height, ...)`, `grass_protos(kind="dry"/"green"/"short", n=4, height=0.4)` | protos | fine-bladed tufts |
| `prayer_rock(loc, size=(2.7,1.7,1.0), seed=0)` | (obj, anchors) | flat-topped boulder; anchors `top`, `kneel`, `facing` |
| `skull_cliff(center, width, base_z, top_z, ...)` | (obj, anchors) | the Golgotha scarp |
| `jerusalem(center=(170,640), rot=0, seed=0, detail=1, houses=True)` | dict | distant city massing |
| `terrain_grid(name, height_fn, center, core, cell, extent, growth, mat_, attrs_fn)` | object | fine core + geometric growth to the horizon; registers with `core.TERRAINS` so `C.height_at(name,x,y)` works |
| `ground_material(name, style="golgotha"/"hills"/"plain"/"grove", scale, scrub=0)` | material | anti-tiled multi-texture ground (soil, cracked crust, limestone on slopes, trodden paths, macro variation, distance fade) |
| `limestone_material(...)`, `bark_material(...)`, `leaf_material(...)`, `grass_material(...)`, `city_material(...)`, `tint_material(mat, sat, tint, value, rand)` | material | all hazified |
| `ground_z(x, y)`, `ground_hit(x, y)` → (z, normal), `add_ground(obj)`, `release_bvh()` | | raycast helpers (the BVH is freed at the end of each builder to save RAM; it is rebuilt lazily, ~1 s) |
| `sun_dir_at(hour)` → (elevation, compass az) | | Jerusalem, April |
| `sky_palette(sun_el)` → (zenith, horizon, glow) | | colours used by the analytic time-lapse sky |
| `scene_prop(name, value=None, frame=None)` | | get/set/key the uniform scene properties used by env shaders (`env_haze_*`, `env_cloud_*`, `env_stars`, `env_tl_*`) |
| `perlin`, `fbm`, `ridged`, `smoothstep` | numpy | vectorised noise used for terrains/masks |

---------------------------------------------------------------------------------------------------
## 5. Performance (measured on this shared 4-core CPU, llvmpipe, load avg 5-6 from other agents)

Final quality = 540x960, `ctx.samples` 6, golgotha golden wide with `view="wide"`:

| configuration | cpu-s / frame | wall s / frame (loaded) | est. wall unloaded |
|---|---|---|---|
| bare terrain + cliff + crosses + city + sky (no scatter) | ~16 | ~10 | ~4 |
| **full default golgotha** (rocks, grass, bushes, dust, no fog/rays) | **~21** | **~13.7** | **~5–5.5** |
| + `fog=True` | +4.5 | | +1.2 |
| + `rays=True` | +45–55 | | +12 |
| 1 TAA sample instead of 6 | 8 | 4.7 | ~2 |

* Per frame ≈ 5 cpu-s fixed (sync, shadows) + ~2.9 cpu-s per TAA sample → **use `ctx.samples = 4` for wide
  env shots** (≈ 4 s unloaded); 6 for close-ups where the env is mostly out of focus anyway.
* Sun shadows ≈ 30% of the frame; grass/pebbles/far shrubs don't cast shadows (by design).
* Build time: golgotha 3–5 s, hills 3–4 s, grove 3–5 s, plain 3–4 s with a warm cache (first build of a new
  tree/rock variant +1–20 s, cached afterwards in `/opt/assets/env/protos`).
* First frame of a process includes shader compilation (+10–40 s). Avoid re-building materials per frame.
* RAM: 2.3–3 GB peak per render process (EEVEE on llvmpipe). `sky()` lowers the shadow pool to 256 MB.
* `judean_hills(timelapse=True)`: every frame changes the sky → ~1.3x a static frame; animation is via scene
  properties (uniforms) so there is no per-frame shader recompilation.
* Cheapest knobs: `view=...`, `grass=0.5`, `bushes=0.5`, `near_detail=0` (wide shots), `city=False`,
  `ctx.samples=4`, keep `rays`/`fog` off.

## 6. Gotchas

* **Never add a world volume** — use `fog_volume`/`god_rays`/`dust_storm` (finite boxes).
* `sky()` owns the world and the sun lamp; call it before adding your own lights. Re-calling replaces the sun
  object — re-read `A["sky"]["sun"]` afterwards (or use `clouds_layer`, which keeps it).
* Animate env shader parameters through `scene_prop(..., frame=f)` / `set_haze(..., frame=f)` — **not** by
  keyframing node sockets inside shared node groups (that re-evaluates every material each frame: ~2x slower).
* Scattered props are Geometry-Nodes instances: they render but can't be selected individually; to clear an
  area pass `exclude=[(x, y, r)]` when building (or hide the whole `Env*` instancer object).
* Placing characters: use `A["ground_z"](x, y)` (exact) rather than `ground(x, y)` near the cliff/rocks.
* `golgotha` crosses face −Y; the centre cross figure must be added by the characters module at
  `A["crosses"]["center"]` anchors (hands are on the beam front face, 4 cm proud of the wood).
* The skull cliff and plateau edge are at y ≈ −11; cameras for "medium" shots must stay at y > −10 to stand
  on the plateau.
* `rock_protos(kind)` shares prototype meshes per kind: calling it again with another tint re-tints every
  instance of that kind in the scene.
