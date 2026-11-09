# SET 'EDGE' — "The Edge of the Mind" (`SETS.EDGE`, Part One)

Files: `web/src/sets/edge.js` (set), `web/src/labs/edge.js` (set lab, placeholder capsules),
`web/src/labs/edge_cast.js` (lighting check with the real JESUS + VOID rigs), this doc. No core files modified.

```bash
node tools/render.js sheet --lab edge --from 1 --to 51 --n 26 --cols 9 --out out/sheets/edge_all.jpg       # every view
node tools/render.js sheet --lab edge_cast --from 1 --to 27 --n 14 --cols 7 --out out/sheets/edge_cast.jpg  # real rigs
```
Lab segments (2 s each, label at the bottom; exported `segments`): 01 establishing wide · 02 two-shot · 03 MCU ·
04 low angle up at the Void (voidSky 1) · 05 high angle on a seated figure · 06 reverse (tod .5) · 07 side ·
08 walk-off (tod 1) · **09 `shots.finale` recipe (tod .9)** · 10 tod sweep 0→1 · 11 voidSky sweep 0→1 · 12 high
establishing · 13 reverse low (voidSky .6) · 14 sky up / stars (tod 1) · 15 seeds ×2 · 16 OTS · **17–20 the staging
camera setups of `scenes/marks.js`** (MASTER looking north-east, FRAME0 on the peach crest, BEND sunward, WHISPER) ·
21/22 medium two-shot voidSky .6 / 1 (side by side) · 23 OTS with `heroTreeGlow .35` · 24 rose-gold tree close ·
25 finale recipe tod 1 · 26 finale WITHOUT the recipe (comparison).
`edge_cast`: real JESUS + VOID — MCUs (incl. the rose-gold tree behind a face), low Void MCU, reverse, wide, high
kneel, walk-off, **finale recipe at tod .85 and 1** + a no-recipe comparison, medium two-shots at voidSky .6 / 1, OTS.

## Layout (metres, Y up; world −Z = toward the sun)

Built to match `scenes/marks.js` (EDGE.PATH_WORLD / CREST / RISE / HILL / TREE_WORLD), where most Part One
shots look **north-east (away from the sun)** and the reverse angles look into the sunset.

- **Stage**: one clear soft mint (analogous variation only — no complementary blends, so it never goes grey-sage),
  **exactly y = 0 for r < 5.2 m**. Sparse tiny glowing flowers from r ≈ 2.6 m out (bloom head + faint glow point) —
  hide them under a seated/fallen character with `opts.clear`.
- **Path**: pale cream ribbon (soft alpha edges, receives shadows). It sits on the *rendered* terrain mesh
  (`pathSurfaceAt`: 1.2 cm up on the stage, ~2–3.5 cm on hills, never below the mesh) and, near the stage (r < 18 m),
  is drawn in the opaque pass right after the ground and BEFORE everything else, so feet, a seated user or a kneeling
  robe always land on top of it. Comes from the far north-east hills, over the **peach crest** (`groundAt(7.4, 10.3)`
  = 1.26), **through the stage** (`anchors.pathStart` ≈ origin), over the **gentle rise** (`groundAt(-0.8, -11)` =
  0.49) beside the **lilac hillock** (top `groundAt(-3.6,-10)` = 2.61), climbs the long **crest**
  (`anchors.pathFar` = (−0.50, 2.01, −40.6), 41 m along) and converges into a low gap in the far ridge under the sun.
- **Hills**: the three staging hills (`FEATURES`, smooth domes, joined with a smooth max — no crease), each ONE hue
  with value variation (the lilac hillock: deeper lilac at the toe → light lilac on top, coloured over the rise so it
  never turns teal), then soft rolling pastel patchwork (peach / mint / lilac / rose, blended with partial chroma
  restore: no mud, no neon), far ridges at 120–330 m with the sun gap. A form term lightly shapes slopes (clamped
  0.86–1.15: backlit slopes never go muddy). A tod-aware ground grade keeps the grass pastel at sunset (no olive).
  Per-vertex atmospheric haze, coloured by the sky in that direction, layers the distance.
- **Sky** (dome, −6°…90°): gold → peach → rose-lilac → indigo zenith; a low pink belt of Venus + lilac earth shadow on
  the anti-sun side (the north-east master backdrop); a soft low sun ~8° left of −Z (`SUN_AZ = −0.14`, elevation 6.2°
  → 0.6°; disc HDR kept moderate so bloom stays tight) with glows and a warm horizon line; early stars high up.
- **Clouds** (billboards, procedural height-field atlas with form normals, lit per cloud by the actual low sun: warm lit
  undersides, cool tops, silver/gold lining on the edges facing the sun): **hero cumulus on both main camera axes** —
  a sunward pair (~9° right / 11° left of −Z, 10–14° up, above head height in eye-level mediums) and a north-east pair
  (4.6–6° up, in the staging MASTER's sky band) — plus low banks, a high streak and a faint low streak just above the
  sun (glows gold in the finale's long lens), more cumulus around the sky and high wisps. Drift 0.03°/s.
- **Void bleed** (`voidSky`): the sky around the Void, *as seen from the current camera*, deepens to a clearly indigo
  night (perceptual curve `vm^0.6`) with violet/teal nebula, many stars and a soft violet fringe; it spares the
  horizon glow so the Void's dark body keeps its silhouette; clouds inside it darken too. The centre sits `voidLift`
  (2 m) above `voidPos`, biased up a little, and is pulled down to at most ~9° above the view axis when the Void is in
  front of the camera — so eye-level mediums show the patch (0.6 = mood, 1 = full night), not just its lower rim.
- **Dressing**: luminous puff-trees (S-curved trunk, ONE smooth soft-union crown per tree: icosphere shrink-wrapped
  onto blended puffs, SDF-gradient normals — distinct lobes, no seams, no faceting), two of them on the far north-east
  crest; round glowing bushes (same smooth-union build); ~70 dandelion-like **thought seeds**; faint golden motes.
  Nothing tall stands within ±12° of the −Z axis seen from the stage except the hero tree.
- **The rose-gold "soft crystal" tree** (hero prop, `scenes/marks.js` EDGE.TREE_WORLD = (2, 0, −5.2)): slender
  pale trunk forking into three branches, a lobed rose-gold crown held HIGH (bottom ≈ 2.6 m, top ≈ 4.2 m, ≈ 2.3 m
  wide) so it clears heads in eye-level and OTS framings; satin finish (roughness 0.48, no metal, no hot spots), soft
  iridescent lilac rim, no halo sprite, four glowing buds tucked under the crown. `heroTreeGlow` calms it,
  `hideHeroTree` removes it.
- **Lights**: `key` = warm sun light, the ONE shadow caster (1024², ±7 m frustum around `shadowAt`); `fill` = warm
  front "bounce" from world (+0.5, +0.42, +0.76) (the face light for anyone facing +Z); cool lilac `hemi`. Only trees /
  bushes near the shadow frustum cast (far ones stay out of the shadow pass). A faint `FogExp2` hazes characters at
  30–50 m. `EYE_LIGHT` is set every update.
- **Key-direction cheat (deliberate)**: by default the key is 35° left of the visible sun (`keyYaw −0.62`) and higher
  (28° → 18° vs a 6.2° → 0.6° sun), so faces turned toward camera get modelling and shadows stay short and readable.
  For shots looking INTO the sun fold it back: `keyYaw` → 0 and a low `keyElev` (shadows then run toward camera and
  get long). `shots.walkoff.opts` (`keyYaw −0.22, keyElev 12`) and `shots.finale.opts` (`keyYaw 0, keyElev 5`) do this.
  `EYE_LIGHT` points 35% of the way from the key toward the fill (`eyeKey`), so eyes keep a catchlight from the front.

## API

```js
const set = await app.set('EDGE');
set.update(t, { tod, voidSky, voidPos, seeds, ... });   // returns set; pure function of (t, opts)
st.scene = set.scene; st.look = { ...set.look, /* overrides */ };
```

| `opts` field | meaning |
|---|---|
| `tod` 0..1 | 0 golden dusk (sun 6.2° up, gold/peach/lilac) → 1 deep sunset (sun 0.6°, half behind the far ridge, red-orange; sky deeper; more stars; lights redder/dimmer; key lower → longer shadows; ground graded away from olive). Everything lerps — keyframe it with `k()`. |
| `voidSky` 0..1 | the Void's presence (a mood at 0.4–0.6, full indigo night + stars at 1). Lights cool ~12–30%. |
| `voidPos` [x,y,z] | where the Void stands (feet). Bleed centre `voidLift` (default **2.0** m) above it; angular radius `voidRadius` (default **34°**; smaller = a compact pocket). |
| `seeds` | thought-seed density multiplier (1 ≈ 70 seeds in a 30×5×39 m volume; 0 = none; also drives motes). `seedGlow` brightness mult. |
| `sunShift` | per-shot cheat (rad, ±0.15): nudge the sun's azimuth (+ = toward +X). **Use it so the disc never sits right behind Jesus's head** (reads as a halo — forbidden by the bible). The key follows. |
| `sunGlow` | sun disc/glow multiplier (default 1). ~0.5–0.7 calms close-ups with the sun behind a face. |
| `silhouette` 0..1 | **shots into the sun with dark figures** (the finale): key ×0.5, fill ×0.06, hemi ×0.28, fog off, backlit ground → dusky rose-lilac. Pair with a low, tight bloom (`shots.finale.post`). |
| `heroTreeGlow` 0..1 | glow / rim / bud brightness of the rose-gold tree (default 1; ~0.3–0.4 when it sits beside a face in a close-up). |
| `hideHeroTree` | `true` removes the rose-gold tree for this shot. |
| `shadowAt` [x,y,z] | centre of the shadow frustum (default origin). Move it with walkers (e.g. `pathAt(s).pos`); beyond 6 m from the origin the far ground also receives shadows; only trees/bushes near it cast. |
| `clear` [[x,z,r],...] | hide the little flowers (and their glow) inside these circles (under a seated / fallen character). |
| `keyYaw`, `keyElev` | key azimuth offset from the sun (rad, default −0.62) / elevation (deg) — see the key-direction cheat above. |
| `keyMul`, `fillMul`, `hemiMul` | light multipliers (default 1). |
| `eyeKey` 0..1 | EYE_LIGHT direction blend sun-key → fill (default 0.35). |
| `haze` | haze density multiplier. `glow`: tree/bush glow multiplier. |

Returned object: `scene`, `update`, `look` (post look kept in sync with tod: `exposure`, `warm`; bloomThreshold 0.92
so the bright sky itself never blooms), `anchors`, `props` (sky, clouds, terrain & path = Groups with
`userData.inner/outer` meshes + `userData.material`, trees[] (the hero tree last, also `set.heroTree`), bushes[],
flowers, seeds, motes, key, fill, hemi), `shots`, `groundAt(x, z)` (exact ground height),
`pathAt(s)` → `{ pos:[x, groundAt, z], dir:[dx,0,dz], yaw, surface }` (s = metres along the path from `pathStart`:
+ toward the sun, − upstream toward the north-east; `yaw` faces along the path; `surface` = y of the path ribbon
there). Named exports of `sets/edge.js`: `FEATURES`, `SUN_AZ`, `groundAt`, `pathAt`, `pathSurfaceAt(x, z)`,
`meshHeightAt(x, z)` (height of the rendered, linearly interpolated terrain mesh) — all usable **before `create()`**.

### Anchors
`origin` · `pathStart` (≈ origin, `pathStartYaw` ≈ −3.02 = facing the sun) · `pathFar` (+ `pathFarYaw`,
`pathFarS` = 41) = the crest for the walk-off · `pathBeyond` (14 m past the crest, walkers half hidden) ·
`sunHorizon` (ground point on the horizon under the sun) · `clearingRadius`.
Useful path stations: `pathAt(-20)` ≈ peach crest (12.2, 1.26, 15.7) · `pathAt(10)` ≈ the rise (−0.5, 0.47, −9.9).

### Shot presets (`set.shots`, for `applyShot`)
`wide`, `two`, `lowUp`, `highDown`, `reverse`, `walkoff` (+ `walkoff.opts`: key folded toward the sun), and the
**`finale` recipe** — Part One's last image. It has three parts; use all of them:

```js
const F = set.shots.finale;
applyShot(app.camera, F, t);                                   // 18° lens from ≈ (8.3, 2.26, 9.0), aimed so the pair
set.update(t, { ...myOpts, ...F.opts, tod: myTod });           //   just below the crest stands IN FRONT of the disc
st.look = { ...lookFor('s16', set.look), ...F.post };          // ('look' is the camera target, hence 'post')
// walk the pair along pathAt(s), s in F.walk = [33, 47]: they cross the disc dark against the glow, then sink
// behind the crest. Jesus ~0.45-0.5 m left of the path, the Void ~0.9 m right (as in the labs).
```
`F.opts` = `{ tod: 0.9, silhouette: 1, sunShift: -0.05, keyYaw: 0, keyElev: 5, seeds: 0.5, shadowAt }` (the
`sunShift` is part of the alignment — it also keeps the rose-gold tree and the bend's bushes out of the long lens);
`F.post` = `{ bloom: 0.18, bloomRadius: 0.3, bloomThreshold: 0.95 }`. Aligned for tod 0.9; good for 0.8–1 (at tod 1
the disc sits a little lower behind the pair). Without the recipe (scene bloom ~0.5–0.7 + full fill) the disc's bloom
spills over the figures and the Void turns tan — compare lab segments 25 / 26 and edge_cast 17–21.

## Tips
- Portrait frames are narrow (±10° horizontal at fov 35): anything within ~±12° of the camera axis can sit behind a
  face. Check the sun in sunward close-ups with `sunShift` / `sunGlow`, and the rose-gold tree with `heroTreeGlow`.
- Walkers: feet `y = groundAt(x, z)`; move `shadowAt` with them.
- `voidSky` 0.4–0.6 reads as a mood behind the Void in eye-level mediums; 1 = full indigo night with stars.
- `core/camera.js framed()` lands the subject at `1 − screenY` (noted in scenes/marks.js); the labs here compensate.

## Perf
Per frame in a wide: terrain ~29k triangles (polar mesh, 0.5 m rings over the staging hills, 144 segments), flowers
~13k (low-poly heads + one glow point each), trees/bushes ~45k (hero crown 8.8k), sky dome ~6k (−6°…90°), one 1024²
shadow map (casters culled to the frustum's neighbourhood). Per-pixel work is kept lean: sky gradient, haze and the grass
scatter / sheen / form terms per vertex; the Void-bleed centre computed once per render on the CPU; the sky drawn last
among opaques and the far ground (r > 18 m) drawn after characters / props so early-z skips hidden pixels.

Measured on the shared 4-core box under heavy load from other agents (load 15–24), so as **CPU time of the whole
browser process tree per frame** (load-independent), interleaved in one browser, vs the trivial one-head `facetest`
(known unloaded wall floor 0.486 s/frame):

| lab | CPU / frame vs facetest | ≈ unloaded wall |
|---|---|---|
| set only (4 camera setups) | **1.16×** | ≈ 0.56 s |
| `edge` lab (set + placeholder capsules + label) | 1.23× | ≈ 0.60 s |
| `edge_cast` (set + real JESUS + VOID) | 1.59× | ≈ 0.77 s |
| the previous version of the set (same 4 setups) | 1.43× | ≈ 0.69 s |
| post chain on an empty scene | 0.62× | ≈ 0.30 s |

Cost split of the set (CPU-s/frame, hide-one-at-a-time): terrain 0.27, shadow 0.20, sky 0.14, trees 0.09, path 0.09,
clouds / flowers / bushes / seeds ≈ 0.01 each. A 4-tap shadow filter on the ground would save another ~0.09 but shows
stair-stepped shadow edges in close high angles, so the renderer's PCF-soft is kept. Wall-clock `bench --lab edge
--t 3` at load 15 read 1.49 s vs facetest 1.05 s (both inflated ~2–3×). Re-check on a quiet machine:
`node tools/render.js bench --lab edge --t 3`.

## Known limitations
- The Void bleed is camera-relative (it always appears around/above the Void in frame, from any angle); its world
  position therefore shifts between reverse angles — intended ("the sky above it deepens").
- The terrain mesh is a linear interpolation of `groundAt`: exact on the stage, ≤ 1.5 cm over almost all of the 24 m
  around it, up to ~9 cm at the steep far toe of the lilac hillock (nobody walks there); along the path ≤ 4.4 cm out
  to s = 45 (coarser rings beyond 22 m) and ≤ 8.4 cm around s ≈ 52. `meshHeightAt()` gives the exact rendered height;
  for far walkers (s > 20) `pathAt(s).surface` (the ribbon top, never below the mesh) is a no-sink foot height.
- Beyond 18 m from the origin the path ribbon draws after characters (early-z saving): a walker's sole there can lose
  its bottom ~3 cm under the translucent ribbon — invisible at those distances (finale walkers are ~45 m away).
- Shadows exist only inside the ±7 m frustum around `shadowAt`.
- The lilac hillock and the rose-gold tree (staging requirements) are visible behind the actors in shots that look
  straight down −Z from the stage; frame accordingly (`heroTreeGlow` / `hideHeroTree` for close-ups).
- Clouds are billboards facing the origin: from cameras far from the stage (> ~30 m) their shading is approximate.
