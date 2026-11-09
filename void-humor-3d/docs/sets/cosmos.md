# SET 'COSMOS' — the universe the Void shows Fear (`SETS.COSMOS`, bonus-scene climax)

Files: `web/src/sets/cosmos.js` (set), `web/src/labs/cosmos.js` (lab), this doc. **No core files modified.**

```bash
node tools/render.js sheet --lab cosmos --from 0.5 --to 11 --n 12 --cols 6 --out out/sheets/cosmos_revealA.jpg   # reveal from inside a room
node tools/render.js sheet --lab cosmos --from 12 --to 27 --n 8 --cols 4 --out out/sheets/cosmos_lookup.jpg      # looking up past Fear + Void
node tools/render.js sheet --lab cosmos --from 28 --to 39.5 --n 8 --cols 4 --out out/sheets/cosmos_standalone.jpg
node tools/render.js sheet --lab cosmos --from 40 --to 56 --n 8 --cols 4 --out out/sheets/cosmos_backroom.jpg    # inside the real BACKROOM
node tools/render.js sheet --lab cosmos --from 58 --to 69 --n 4 --cols 4 --out out/sheets/cosmos_rigs.jpg        # real VOID + FEAR rigs
node tools/render.js sheet --lab cosmos --from 100 --to 109 --n 10 --cols 5 --out out/sheets/cosmos_survey.jpg   # 360° sky survey
```
Lab segments (exported `segments`): A 0–12 reveal 0→1 in a placeholder room (front view) · B 12–22 reveal 0→1,
low camera looking up past two capsules (Fear 0.85 m, eyes up, beside a 3 m Void) · C 22–28 hold (calm, slow push)
· D 28–36 standalone, slow orbit · E 36–40 standalone zenith / wide · F 40–52 inside the real **BACKROOM** (its
own `cosmos` wall fade + this group) · G 52–58 BACKROOM looking up · H 58–64 real VOID + FEAR rigs, standalone ·
I 64–70 real rigs, looking up. Debug ranges (100+ surveys, 9000+ empty baseline, k·1000+t variants) are listed in
the lab header.

## Look / layout (camera convention: usually at +Z looking −Z at the characters)

- **Sky shell**: an inside-out ellipsoid (radius × height) around the characters. Its colour comes from a nebula
  **cube map baked once on the GPU** (640² × 6, half float) and is looked up **by camera ray direction**, so the sky
  is at infinity (no parallax / swimming when the camera moves), while the shell's geometry is depth-tested against
  the host scene: anything farther than the shell (walls, far props) is covered by the cosmos.
- **Nebulae** (smooth domain-warped fbm, low contrast, compression-friendly), designed as distinct cloud complexes
  separated by deep dark space and dust lanes:
  - violet → magenta, high behind the characters (az −15°, el 32°);
  - a small **warm cloud with a gold core and rose edges** just right of / above the Void in a front view
    (az +19°, el 21°) and under the hero galaxy in the looking-up view;
  - teal → blue on the left (az −70°), rose → magenta on the right horizon (az +90°), blue/teal and rose/violet
    behind the camera (+Z), a faint teal veil overhead, and a **calmer, darker blue/teal band at eye level behind the
    characters** (az 0…20°, el 0…15°) so faces keep a quiet background;
  - a faint pale galactic band (stars are denser along it) that is routed away from the hero galaxy.
- **Spiral galaxies** (5 discs, 4 baked variants, mipmapped 512²): gold bulge, blue/violet/teal arms with rose
  knots, dust lanes, sparse resolved stars; inclined discs at infinity, each spinning slowly.
  0 **hero** az +23°, el 38° (big, 27° across; the money shot of the looking-up angle) · 1 az −7°, el 22° (upper
  left of a front two-shot) · 2 right horizon · 3 overhead · 4 behind the camera.
- **Stars**: far layer (~2600 points on the shell at infinity), mid layer (520, world-space shell 0.42–0.92 of the
  radius → parallax), near layer (72, 0.9–4 m around `source`; 26 of them **kindle one by one** with a small 4-point
  flare). Gaussian cores ≥ 3.5 px (no sub-pixel shimmer), brightness power law (few bright), slow per-star twinkle on
  the brighter ~20 % only — **no global flicker** (frame-to-frame MAE at full reveal ≈ 0.002).
- **Nebula puffs**: 5 big soft world-space billboards (3–4 m, alpha ≈ 0.1) for parallax depth; they swell open
  when the bloom front reaches them.
- **Bits of meaning**: 9 tiny glowing glyphs (heart, sun, music note, house, handprint, pencil; rose / gold / teal /
  peach) orbiting the source at 1.9–3.5 m, 0.2–2.2 m above it, ~0.11–0.17 m big, gently breathing. Subtle.
- **Floor veil** (host mode): beyond `r0` the host floor fades into the same sky + a procedural star field, seamless
  with the shell where the shell meets the floor plane → the characters stand on an island of floor in space.
  Standalone: a soft violet/teal **light pool** under the characters ("glass over the universe").
- **Lights** (in the group, intensity × reveal): violet/teal hemisphere + warm starlight key from the hero galaxy
  (from behind/above in a front view → a gentle warm rim). Standalone scene adds a cool rim, a soft lilac front fill
  and a faint hemi so faces read.

## Reveal timeline (`opts.reveal` 0 → 1)

| reveal | what happens |
|---|---|
| 0 | nothing is drawn (cosmos objects hidden; lights at 0) |
| .015–.29 | **stars kindle** one by one near the source (the Void), each with a little glint |
| .12 → ~.75 | the **walls dissolve** into deep starry space, opening outward from the source *as seen by the current camera* (front in units of the frame half-diagonal: covers a frame around the source by ≈ .7), with a faint fringe |
| .14 → .72 | a soft cloudy **light unfurls** from behind the source (violet → rose → teal), fading as the sky takes over |
| .24 → ~.85 | **nebulae bloom open** behind that front (brighter at their leading edge); puffs swell open |
| .5 → 1 | **galaxies drift in** (staggered: slide ~6°, grow 80 → 100 %, fade in) |
| .62 → 1 | glyphs appear |
| 1 | everything; the shell skips all masking math (cheapest state) |

Animate it with `k()` or `smooth()` over 6–12 s for "breathtaking yet calm". The front is camera-relative, so
avoid cutting in the middle of the .2–.75 range (a cut re-centres the opening on the new view); slow camera moves are fine.

## API

```js
const cos = await app.set('COSMOS');
// -> { scene, group, update(t, opts), attach(scene), blendLook(base, w), anchors, props, look }
```
- `scene` — standalone THREE.Scene (dark background, cosmos group, rim/fill/hemi lights).
- `group` — everything cosmic (shell, floor veil, stars, puffs, galaxies, glyphs, cosmic lights). One parent at a time.
- `attach(scene)` — re-parent `group` (idempotent). **Call every frame before `update()`**, like characters.
- `update(t, opts)` — pure function of (t, opts); returns the set. Methods are bound (destructuring is safe).
- `look` — default post look `{ bloom .7, bloomRadius .62, bloomThreshold .72, vignette .3, sat 1.08, lift, exposure 1.05 }`.
- `blendLook(hostLook, w)` — post look blended from a host look toward `look` (use `w = smooth(reveal)`).

### `update(t, opts)` fields (all optional)

| field | default | meaning |
|---|---|---|
| `reveal` | 1 | 0..1, see the timeline above |
| `center` | [0,0,0] | floor point the cosmos surrounds (the characters' spot; its y = floor height) |
| `source` | center+[0,1.6,0] | where the reveal starts — pass the Void's chest anchor |
| `radius` | 7.5 | horizontal radius of the sky shell (m). Things farther than the shell are covered |
| `height` | .87·radius | vertical semi-axis (lower it under a low ceiling) |
| `lift` | 1.5 | shell centre height above `center` |
| `drift` | 1 | speed of all slow motion (sky drift, galaxy spin, glyph/near-star orbits, puff turn) |
| `clock` | t·drift | explicit motion clock (pass your own integral if you animate `drift`) |
| `intensity` | 1 | global brightness |
| `stars`, `nebula`, `galaxies`, `glyphs`, `puffs` | 1 | per-element multipliers (0 hides and skips the draw) |
| `bloom` | 1 | strength of the mid-reveal unfurling light |
| `fringe` | 1 | dissolve-front glow + nebula leading-edge brightening |
| `light` | 1 | cosmic hemi + key (host: .4/.65 × light; standalone .55/1.25). 0 = add no light |
| `floor` | — | `{ cover, inner, r0=2.2, r1=5.5, glow }` — `cover` (host 1 / standalone 0): sky over the host floor beyond r0→r1; `inner`: sky tint inside r0; `glow` (host .35 / standalone 1): light pool |
| `eyeLight` | standalone 1, host 0 | blend `EYE_LIGHT` toward the cosmos key (in a host, call after the host's update) |
| `standalone` | auto | force standalone/host defaults (auto = `group.parent === scene`) |

The sky drift is **bounded** (starts at 0.0045 rad/s, never more than ±8° from the designed layout), so which
galaxy is where never depends on absolute film time.

### Anchors (`cos.anchors`, world Vector3s, valid after `update`)
`center`, `source`, `domeCenter`, `hero` (hero galaxy), `galaxies[0..4]`, `nebula` (the violet complex), `up`
(zenith). Galaxy anchors sit on the shell along their direction from the shell centre — use them as **gaze
targets** (`fear.update(t, { gaze: cos.anchors.hero, ... })`) and to aim cameras; on screen the galaxies are at
infinity (direction matters, not distance).

### Props (`cos.props`)
`dome`, `floor`, `far`, `mid`, `near`, `puffs`, `galaxies[]`, `glyphs`, `hemi`, `key`, `skyTex` (the nebula cube
map — usable as an env/reflection map if a rig wants cosmic reflections).

## Recipes

**Standalone background** (cuts to "pure cosmos"):
```js
setup: st.cos = await app.set('COSMOS'); st.scene = st.cos.scene;
update: applyShot(...); st.cos.attach(st.cos.scene); st.scene.add(st.void.root, st.fear.root);
        st.cos.update(t, { reveal: 1, center: [0.1, 0, 0], source: st.void.anchor('chest') }); st.look = st.cos.look;
```
**Inside BACKROOM** (walls dissolve; verified in lab segments F/G):
```js
const br = await app.set('BACKROOM'), cos = await app.set('COSMOS');
const reveal = k(t, [['bXX', 0], ['bXX+9', 1, 'inOut']]);
cos.attach(br.scene);                                   // before cos.update
br.update(t, { cosmos: smooth(reveal / 0.8), ... });    // BACKROOM fades its own walls/props/screen/fog
cos.update(t, { reveal, center: [(vs.x + fo.x) / 2, 0, (vs.z + fo.z) / 2], source: voidRig.anchor('chest'), radius: 9 });
st.look = cos.blendLook(br.look, smooth(reveal));
```
BACKROOM's walls are only ~4.5 m from the Void spot (inside any useful shell), so the room's own `cosmos` fade
handles them; the shell covers everything beyond `radius` (the far screen, the room's dark dome) and the floor
veil turns the floor beyond r0 into sky. The BACKROOM bulb on its cord stays visible unless the scene hides it.

**Camera recipes** (from the lab):
- Two-shot from inside: `{ pos: [0.35, 1.35, 6.6], look: [0.3, 1.95, 0], fov: 50 }` (Void at [0.95,0,−0.25],
  Fear at [−0.7,0,0.35]) — galaxy 1 upper left, warm cloud upper right, calm dark-blue behind the faces.
- **Looking up past Fear + Void** (hero shot): low camera in front-left of Fear,
  `{ pos: [-2.0, 0.42, 3.3], look: [0.5, 4.4, -4.2], fov: 56 }` — the hero galaxy fills the upper frame above
  the warm cloud, Fear's upturned face at the bottom, the Void's flank on the right.
- Pair with `void.update(..., { extra: { cosmos: 1 } })` (stars in its cloak brighten) and Fear's `wonder`/`awe`
  faces (`head.pitch −0.6`, `extra.cry .3–.45` for tears of awe, `glow 1.3`).

## Rules & gotchas
- Keep the **camera inside the shell** (distance from the shell centre < radius − ~0.5 m); stars and galaxies are
  projected onto the shell along camera rays.
- The shell only covers geometry **farther than the shell**. Walls/ceilings closer than `radius` must be faded by
  the host (BACKROOM `cosmos`) or the radius reduced (galaxies/sky stay at infinity regardless).
- Soft billboards (puffs, glyphs) never touch the floor; galaxies sit above ~10° elevation.
- Adding the group to a host adds 2 lights → one shader recompile of the host's lit materials on first attach
  (no per-frame recompiles; intensities go to 0 when hidden).
- Order with `EYE_LIGHT`: hosts set it in their update; COSMOS only touches it if `eyeLight > 0` (default in
  standalone), so call `cos.update` after the host's update when you blend.
- All ShaderMaterials ignore scene fog by design (BACKROOM fog does not grey out the cosmos).

## Performance (SwiftShader, 720×1280, MSAA + bloom post)
Interleaved min-of-8 benches while other agents loaded the 4-core box (load ≈ 5–7):
empty-scene floor (post + readback) 0.34–0.38 s · placeholder room alone 0.43–0.47 · **room + full cosmos
0.57–0.62** · **standalone cosmos + capsules 0.53** · looking-up hero frame 0.55–0.57 · mid-reveal 0.58–0.70.
So the cosmos itself costs **≈ 0.1–0.17 s/frame** under load (≈ 0.08–0.12 unloaded): shell ≈ 0.04–0.08, puffs ≈
0.03–0.04, floor veil ≈ 0.02–0.05 (host mode only), stars + galaxies + glyphs ≈ 0.02. One-time setup (GPU bakes:
sky cube 6×640², 4 galaxies 512², puff atlas 256²) ≈ 1–2 s. Draw calls ≈ 13. `opts.puffs: 0` is the cheapest
quality knob (≈ −0.03 s).

## Known limitations
- The reveal front is computed **per camera** (screen-space-like opening from the source); a cut mid-reveal
  re-centres it. Hold the shot (or move slowly) through reveal .2–.75.
- Stars below the horizon are hidden by an opaque host floor; the floor veil replaces them with a procedural
  star field (statistically similar, not the same stars).
- Shell parallax is zero by design (sky at infinity); depth comes from the mid/near star layers and the puffs.
- Galaxies/stars assume the camera is inside the shell; from outside (very wide shots) they are pushed far away
  and may clip.
- The glyph orbits can pass in front of the source at 1.9 m+; at extreme close-ups set `glyphs: 0` or lower.
