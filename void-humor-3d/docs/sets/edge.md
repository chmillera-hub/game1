# SET 'EDGE' — "The Edge of the Mind" (`SETS.EDGE`, Part One)

Files: `web/src/sets/edge.js` (set), `web/src/labs/edge.js` (set lab, placeholder capsules),
`web/src/labs/edge_cast.js` (lighting check with the real JESUS + VOID rigs), this doc. No core files modified.

```bash
node tools/render.js sheet --lab edge --from 1 --to 31 --n 16 --cols 8 --out out/sheets/edge_all.jpg   # every view
node tools/render.js sheet --lab edge --from 18 --to 21.95 --n 8 --cols 8 --out out/sheets/edge_sweeps.jpg  # tod / voidSky sweeps
node tools/render.js sheet --lab edge_cast --from 1 --to 19 --n 10 --cols 5 --out out/sheets/edge_cast.jpg  # real rigs
```
Lab segments (2 s each, label at the bottom; exported `segments`): 01 establishing wide · 02 two-shot · 03 MCU ·
04 low angle up at the Void (voidSky 1) · 05 high angle on a seated figure · 06 reverse (looking +Z, tod .5) ·
07 side · 08 walk-off (tod 1) · 09 `shots.finale` (tod 1) · 10 tod sweep 0→1 · 11 voidSky sweep 0→1 ·
12 high establishing · 13 reverse low (voidSky .6) · 14 sky up / stars (tod 1) · 15 seeds ×2 · 16 OTS.

## Look / layout (metres; camera usually at +Z looking −Z)

- **Clearing**: soft mint/sage grass, **exactly y = 0 for r < 7.5 m** (feet never float). Sparse tiny glowing
  flowers from r ≈ 2.6 m out (hide them under a seated/fallen character with `opts.clear`).
- **Path**: pale cream ribbon (soft alpha edges, receives shadows) that sweeps in from behind the camera on the
  LEFT, passes **~2.6 m behind the acting line** (`anchors.pathStart` ≈ (−0.34, 0, −2.82)), S-curves away, climbs a
  gentle crest (`anchors.pathFar` ≈ (−0.08, 2.0, −41.3), 39.5 m along) and reappears on the far hills, converging
  into a gap in the far ridge right under the sun. It glows slightly when you look toward the sun.
- **Hills**: rolling pastel patchwork (peach / mint / lilac / rose), far ridges at 120–330 m with a low gap under
  the sun; a form term darkens slopes facing away from the sun key beyond the clearing; per-vertex atmospheric haze
  (coloured by the sky in that direction: gold toward the sun, lilac away) layers distance.
- **Sky** (dome, drawn last among opaques): horizon gold → peach → rose-lilac → indigo zenith; belt-of-Venus pink
  band and a lilac earth-shadow band on the anti-sun side (reverse angles); a huge soft low sun (~8° left of −Z,
  `SUN_AZ = −0.14`) with layered glows and a warm line hugging the horizon; a few early stars high up (more at
  tod 1); 20 soft billboard clouds (low warm banks, puffy cumulus lit from below, feathered high wisps; silver
  lining only near the sun) drifting very slowly.
- **Void bleed** (`voidSky`): the sky around/above the Void, *as seen from the current camera*, deepens to
  indigo with faint violet/teal nebula, many stars and a soft violet fringe; it spares the horizon glow (so the
  Void's dark body keeps its silhouette against the warm horizon). Clouds inside it darken too.
- **Dressing**: 14 luminous puff-trees (soft S-curved trunk, glowing pastel canopy cluster, light halo, little
  lantern-fruits) and 18 round glowing bushes — all placed **outside ±12° of the main −Z axis** so the column
  behind faces stays calm; they frame wides, angled and reverse shots. ~70 dandelion-like **thought seeds**
  (own billboard sprite: glowing core + fanned pappus) drift on a soft wind; a few golden motes (core `Particles`).
- **Lights**: `key` = warm sun light from behind-left (azimuth sun −0.62 rad, elev 28°→18°), the ONE shadow
  caster (1024², ±7 m frustum around `shadowAt`, long soft shadows toward camera); `fill` = warm front-right
  "bounce" (the face light — the rigs read like in their own labs); cool lilac `hemi`. A faint `FogExp2` gives
  characters at 30–50 m a touch of haze. `EYE_LIGHT` is set every update (key blended 35% toward the fill so eyes
  keep life; see `eyeKey`).

## API

```js
const set = await app.set('EDGE');
set.update(t, { tod, voidSky, voidPos, seeds, ... });   // returns set; pure function of (t, opts)
st.scene = set.scene; st.look = { ...set.look, /* overrides */ };
```

| `opts` field | meaning |
|---|---|
| `tod` 0..1 | 0 golden dusk (sun 6.2° up, gold/peach/lilac) → 1 deep sunset (sun 0.6°, half behind the far ridge, red-orange; sky deeper; more stars; lights redder/dimmer; key lower → longer shadows). Everything lerps — keyframe it with `k()` for smooth changes. |
| `voidSky` 0..1 | the Void's presence (subtle at 0.3–0.6, full indigo + stars at 1). Lights cool ~12–30%. |
| `voidPos` [x,y,z] | where the Void stands (feet). The bleed is centred `voidLift` (3.2 m) above it, biased upward, radius `voidRadius` (36°). |
| `seeds` | thought-seed density multiplier (1 ≈ 70 seeds in a 30×5×39 m volume; 0 = none; also drives motes). `seedGlow` brightness mult. |
| `sunShift` | per-shot cheat (rad, ±0.15): nudge the sun's azimuth (+ = toward +X). **Use it so the disc never sits right behind Jesus's head** (reads as a halo — forbidden by the bible). The key follows. |
| `sunGlow` | sun disc/glow multiplier (default 1). ~0.5–0.7 calms close-ups with the sun behind a face. |
| `shadowAt` [x,y,z] | centre of the shadow frustum (default origin). Move it with the walkers (e.g. `pathAt(s).pos`). |
| `clear` [[x,z,r],...] | hide the little flowers inside these circles (under a seated / fallen character). |
| `keyYaw`, `keyElev` | key azimuth offset from the sun (rad, default −0.62) / elevation (deg). |
| `keyMul`, `fillMul`, `hemiMul` | light multipliers (default 1). |
| `eyeKey` 0..1 | EYE_LIGHT direction blend sun-key → front fill (default 0.35). |
| `haze` | haze density multiplier. `glow`: tree/bush glow multiplier. |

Returned object: `scene`, `update`, `look` (post look, kept in sync with tod: `exposure`, `warm`;
bloomThreshold 0.92 so the sky itself never blooms — only the sun, glows and HDR rims), `anchors`, `props`
(sky, clouds, terrain, path, trees[], bushes[], flowers, seeds, motes, key, fill, hemi), `shots`,
`groundAt(x, z)` (exact ground height; 0 in the clearing), `pathAt(s)` → `{ pos:[x,y,z], dir:[dx,0,dz], yaw }`
(s = metres along the path from `pathStart`, negative = back toward the camera side; `yaw` faces along the path,
for `place()`/`pos` of walkers), `SUN_AZ`.

### Anchors
`origin` · `pathStart` (+ `pathStartYaw`) · `pathFar` (+ `pathFarYaw`, `pathFarS` = 39.5 m) = the crest for the
walk-off · `pathBeyond` (14 m past the crest, walkers half hidden) · `sunHorizon` (ground point on the horizon
under the sun) · `clearingRadius` 7.5.

### Shot presets (`set.shots`, for `applyShot`)
`wide`, `two`, `lowUp`, `highDown`, `reverse`, `walkoff`, and **`finale`**: a 22° lens from behind, lined up so the
crest sits right in front of the low sun — walk the pair from `pathAt(28)` to `pathAt(45)` at tod ≈ 0.8–1 and they
top the crest silhouetted against the glow, then sink behind it.

## Tips
- Portrait frames are narrow (±10° horizontal at fov 35): anything within ~±12° of the camera axis can sit
  behind a face. The set keeps trees out of that cone; check the sun with `sunShift` / `sunGlow` in close-ups.
- Faces are lit by the warm front-right fill; the sun gives a gold back-left rim and long shadows toward camera.
  For shots looking toward +Z (reverse) the fill becomes a back light and the sun a front-left key — fine as is.
- Walk-off: feet `y = groundAt(x, z)` (or `pathAt(s).pos[1]`); move `shadowAt` with the walkers.
- Keep `voidSky` ≤ 0.6 in two-shots (the darkening reads as a mood, not a blackout); 1 for low angles at the Void.

## Perf
Geometry ~110k triangles (terrain 42k, flowers ~45k tiny, trees/bushes ~30k), ~37 draw calls, one 1024² shadow map.
Sky gradient, haze and lighting are cheap per-pixel (haze is per-vertex; no `acos`; the sky is drawn last so
early-z culls hidden sky pixels). Measured on the shared 4-core box under heavy contention from other agents
(load average 6–7): lab frames 0.55–0.78 s minimum (median ~1.1–1.3 s), vs. 0.55 s minimum for an EMPTY scene
with the same post chain at the same time; at load ~2.5 the full set measured ~0.68 s vs 0.36 s empty
(≈ +0.3 s for the whole set). Recheck with `node tools/render.js bench --lab edge --t 3` on a quiet machine.

## Known limitations
- The Void bleed is camera-relative (it always appears around/above the Void in frame, from any angle); its
  world position therefore shifts between reverse angles — intended ("the sky above it deepens").
- Flowers are static except a tiny sway; trees sway 0.5–1 cm. Clouds rotate 0.03°/s around the sky.
- The terrain mesh is a linear interpolation of `groundAt` beyond the clearing (≤ a few cm difference on hills).
- Shadows exist only inside the ±7 m frustum around `shadowAt` (far trees cast none).
