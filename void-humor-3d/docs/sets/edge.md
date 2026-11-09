# SET 'EDGE' — "The Edge of the Mind" (`SETS.EDGE`, Part One)

Files: `web/src/sets/edge.js` (set), `web/src/labs/edge.js` (set lab, placeholder capsules),
`web/src/labs/edge_cast.js` (lighting check with the real JESUS + VOID rigs), this doc. No core files modified.

```bash
node tools/render.js sheet --lab edge --from 1 --to 39 --n 20 --cols 10 --out out/sheets/edge_all.jpg     # every view
node tools/render.js sheet --lab edge --from 18 --to 21.95 --n 8 --cols 8 --out out/sheets/edge_sweeps.jpg # tod / voidSky sweeps
node tools/render.js sheet --lab edge_cast --from 1 --to 19 --n 10 --cols 5 --out out/sheets/edge_cast.jpg  # real rigs
```
Lab segments (2 s each, label at the bottom; exported `segments`): 01 establishing wide · 02 two-shot · 03 MCU ·
04 low angle up at the Void (voidSky 1) · 05 high angle on a seated figure · 06 reverse (tod .5) · 07 side ·
08 walk-off (tod 1) · 09 `shots.finale` (tod 1) · 10 tod sweep 0→1 · 11 voidSky sweep 0→1 · 12 high establishing ·
13 reverse low (voidSky .6) · 14 sky up / stars (tod 1) · 15 seeds ×2 · 16 OTS · **17–20 the staging camera
setups of `scenes/marks.js`** (MASTER looking north-east, FRAME0 on the peach crest, BEND sunward, WHISPER) with
placeholders on the staging marks.

## Layout (metres, Y up; world −Z = toward the sun)

Built to match `scenes/marks.js` (EDGE.PATH_WORLD / CREST / RISE / HILL / TREE_WORLD), where most Part One
shots look **north-east (away from the sun)** and the reverse angles look into the sunset.

- **Stage**: soft mint/sage grass, **exactly y = 0 for r < 5.2 m** (feet never float). Sparse tiny glowing
  flowers from r ≈ 2.6 m out — hide them under a seated/fallen character with `opts.clear`.
- **Path**: pale cream ribbon (soft alpha edges, receives shadows, glows a little when looking toward the sun).
  It comes from the far north-east hills (where the Void came from), runs over the **peach crest**
  (`groundAt(7.4, 10.3)` = 1.26), **through the stage** (`anchors.pathStart` ≈ origin; the user's mark U is on it),
  over the **gentle rise** (`groundAt(-0.8, -11)` = 0.49) beside the **lilac hillock** (top `groundAt(-3.6,-10)` =
  2.61), dips, climbs the long **crest** (`anchors.pathFar` = (−0.50, 2.01, −40.6), 41 m along) and reappears on the
  far hills, converging into a low gap in the far ridge right under the sun.
- **Hills**: the three staging hills above (`FEATURES`, smooth domes with their own clear hue), then rolling pastel
  patchwork (peach / mint / lilac / rose), far ridges at 120–330 m with the sun gap. A form term brightens slopes
  turned to the sun key and darkens the others (neutral on flat ground); per-vertex atmospheric haze, coloured by
  the sky in that direction (gold toward the sun, lilac away), layers the distance.
- **Sky** (dome): horizon gold → peach → rose-lilac → indigo zenith; belt-of-Venus pink band and a lilac
  earth-shadow band on the anti-sun side (= the background of the north-east master shots); a huge soft low sun
  ~8° left of −Z (`SUN_AZ = −0.14`, elevation 6.2° → 0.6°) with layered glows and a warm line hugging the horizon;
  a few early stars high up (more at tod 1); 20 soft billboard clouds (low warm banks, cumulus lit from below,
  feathered high wisps; silver lining only near the sun) drifting very slowly.
- **Void bleed** (`voidSky`): the sky around/above the Void, *as seen from the current camera*, deepens to indigo
  with faint violet/teal nebula, many stars and a soft violet fringe; it spares the horizon glow so the Void's dark
  body keeps its silhouette. Clouds inside it darken too.
- **Dressing**: 15 luminous trees — puff-trees (soft S-curved trunk, glowing pastel canopy cluster, light halo,
  little lantern-fruits) and 3 glassy **"soft crystal"** trees (candy-glass sheen + iridescent lilac rim), incl.
  the **rose-gold crystal tree beside the bend at (2, 0, −5.2)** — plus 18 round glowing bushes, ~70 dandelion-like
  **thought seeds** (own billboard sprite: glowing core + fanned pappus) on a soft wind, a few golden motes (core
  `Particles`). Except the rose-gold tree, nothing tall stands within ±12° of the −Z axis seen from the stage.
- **Lights**: `key` = warm sun light from behind-left (azimuth sun −0.62 rad, elevation 28°→18°), the ONE shadow
  caster (1024², ±7 m frustum around `shadowAt`, long soft shadows); `fill` = warm "bounce" from world direction
  (+0.5, +0.42, +0.76) (the face light for anyone facing +Z; a warm rim for anyone facing the sun); cool lilac
  `hemi`. Characters facing the sun (as in the marks.js staging) get the key as a front/3-4 light. A faint
  `FogExp2` hazes characters at 30–50 m. `EYE_LIGHT` is set every update (key blended 35% toward the fill; `eyeKey`).

## API

```js
const set = await app.set('EDGE');
set.update(t, { tod, voidSky, voidPos, seeds, ... });   // returns set; pure function of (t, opts)
st.scene = set.scene; st.look = { ...set.look, /* overrides */ };
```

| `opts` field | meaning |
|---|---|
| `tod` 0..1 | 0 golden dusk (sun 6.2° up, gold/peach/lilac) → 1 deep sunset (sun 0.6°, half behind the far ridge, red-orange; sky deeper; more stars; lights redder/dimmer; key lower → longer shadows). Everything lerps — keyframe it with `k()`. |
| `voidSky` 0..1 | the Void's presence (a mood at 0.3–0.6, full indigo + stars at 1). Lights cool ~12–30%. |
| `voidPos` [x,y,z] | where the Void stands (feet). The bleed is centred `voidLift` (3.2 m) above it, biased upward, angular radius `voidRadius` (30°; smaller = a compact pocket). |
| `seeds` | thought-seed density multiplier (1 ≈ 70 seeds in a 30×5×39 m volume; 0 = none; also drives motes). `seedGlow` brightness mult. |
| `sunShift` | per-shot cheat (rad, ±0.15): nudge the sun's azimuth (+ = toward +X). **Use it so the disc never sits right behind Jesus's head** (reads as a halo — forbidden by the bible). The key follows. |
| `sunGlow` | sun disc/glow multiplier (default 1). ~0.5–0.7 calms close-ups with the sun behind a face. |
| `shadowAt` [x,y,z] | centre of the shadow frustum (default origin). Move it with walkers (e.g. `pathAt(s).pos`); beyond 6 m from the origin the far ground also receives shadows. |
| `clear` [[x,z,r],...] | hide the little flowers inside these circles (under a seated / fallen character). |
| `keyYaw`, `keyElev` | key azimuth offset from the sun (rad, default −0.62) / elevation (deg). |
| `keyMul`, `fillMul`, `hemiMul` | light multipliers (default 1). |
| `eyeKey` 0..1 | EYE_LIGHT direction blend sun-key → fill (default 0.35). |
| `haze` | haze density multiplier. `glow`: tree/bush glow multiplier. |

Returned object: `scene`, `update`, `look` (post look kept in sync with tod: `exposure`, `warm`; bloomThreshold
0.92 so the bright sky itself never blooms — only the sun, glows and HDR rims; a scene threshold of ~0.8 makes the
horizon near the sun glow, fine in sunward shots), `anchors`, `props` (sky, clouds, terrain & path = Groups with
`userData.inner/outer` meshes + `userData.material`, trees[], bushes[], flowers, seeds, motes, key, fill, hemi),
`shots`, `groundAt(x, z)` (exact ground height), `pathAt(s)` → `{ pos:[x,y,z], dir:[dx,0,dz], yaw }` (s = metres
along the path from `pathStart`: + toward the sun, − upstream toward the north-east; `yaw` faces along the path),
`SUN_AZ`. `FEATURES`, `groundAt`, `pathAt` and `SUN_AZ` are also named exports of `sets/edge.js`.

### Anchors
`origin` · `pathStart` (≈ origin, `pathStartYaw` ≈ −3.02 = facing the sun) · `pathFar` (+ `pathFarYaw`,
`pathFarS` = 41) = the crest for the walk-off · `pathBeyond` (14 m past the crest, walkers half hidden) ·
`sunHorizon` (ground point on the horizon under the sun) · `clearingRadius`.
Useful path stations: `pathAt(-20)` ≈ peach crest (12.2, 1.26, 15.7) · `pathAt(10)` ≈ the rise (−0.5, 0.47, −9.9).

### Shot presets (`set.shots`, for `applyShot`)
`wide`, `two`, `lowUp`, `highDown`, `reverse`, `walkoff`, and **`finale`**: a 22° lens from behind (camera ≈
(5.9, 1.75, 4.9)), lined up so the crest sits right in front of the low sun — walk the pair from `pathAt(28)` to
`pathAt(48)` at tod ≈ 0.8–1 and they top the crest silhouetted against the glow, then sink behind it.

## Tips
- Portrait frames are narrow (±10° horizontal at fov 35): anything within ~±12° of the camera axis can sit behind a
  face. Check the sun in sunward close-ups with `sunShift` / `sunGlow`.
- Walkers: feet `y = groundAt(x, z)` (or `pathAt(s).pos[1]`); move `shadowAt` with them.
- `voidSky` 0.5–0.7 reads as a mood behind the Void in mediums; 1 for low angles looking up at it.

## Perf
~160k triangles and ~47 draw calls per frame in a wide (incl. the shadow pass; terrain ~55k, tiny flowers ~45k,
trees/bushes ~30k), one 1024² shadow map.
Optimisations: sky gradient evaluated per vertex on a horizon-dense dome (only the sun disc/inner glow/horizon line,
Void bleed and stars per pixel) and drawn LAST among opaques (early-z skips hidden sky); cloud background per vertex
on subdivided quads; haze per vertex on every edgified material; no `acos`; terrain + path split so only r < 18 m
receives the PCF-soft shadow (16 taps/pixel) unless `shadowAt` moves away.
Measured on the shared 4-core box under heavy contention from other agents (load average 7–9, all numbers inflated
~2×): `bench --lab edge --t 3` = 0.88 s/frame while the trivial one-head `facetest` lab benched 0.86 s/frame at the
same moment; interleaved A/B in one browser: full set 1.18 s median (0.75 min) vs an EMPTY scene with the same post
chain 0.61 s median (0.42 min). Re-check on a quiet machine: `node tools/render.js bench --lab edge --t 3`.

## Known limitations
- The Void bleed is camera-relative (it always appears around/above the Void in frame, from any angle); its
  world position therefore shifts between reverse angles — intended ("the sky above it deepens").
- Flowers are static except a tiny sway; trees sway 0.5–1 cm. Clouds rotate 0.03°/s around the sky.
- The terrain mesh is a linear interpolation of `groundAt` (≤ ~1 cm on the staging hills, a few cm far out); the
  path decal floats 1.2 cm on the stage and ~4 cm on hills (to stay above the mesh).
- Shadows exist only inside the ±7 m frustum around `shadowAt`.
- The lilac hillock and the rose-gold tree (staging requirements) are visible behind the actors in shots that look
  straight down −Z from the stage; frame accordingly.
