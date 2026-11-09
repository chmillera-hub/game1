# SET 'COSMOS' — the universe the Void shows Fear (`SETS.COSMOS`, bonus-scene climax)

Files: `web/src/sets/cosmos.js` (set), `web/src/labs/cosmos.js` (lab), this doc. **No core files modified.**

```bash
node tools/render.js sheet --lab cosmos --from 0.5 --to 11 --n 12 --cols 6 --out out/sheets/cosmos_revealA.jpg   # reveal from inside a room
node tools/render.js sheet --lab cosmos --from 12 --to 27 --n 8 --cols 4 --out out/sheets/cosmos_lookup.jpg      # looking up past Fear + Void
node tools/render.js sheet --lab cosmos --from 28 --to 39.5 --n 8 --cols 4 --out out/sheets/cosmos_standalone.jpg
node tools/render.js sheet --lab cosmos --from 41 --to 57 --n 8 --cols 4 --out out/sheets/cosmos_backroom.jpg    # real BACKROOM + real rigs
node tools/render.js sheet --lab cosmos --from 58 --to 69 --n 4 --cols 4 --out out/sheets/cosmos_rigs.jpg        # real VOID + FEAR rigs
node tools/render.js sheet --lab cosmos --from 100 --to 109 --n 10 --cols 5 --out out/sheets/cosmos_survey.jpg   # 360° sky survey
```
Lab segments (exported `segments`): A 0–12 reveal 0→1 in a placeholder room (front two-shot) · B 12–22 reveal 0→1,
low camera looking up past two capsules (Fear 0.85 m, eyes up, beside a 3 m Void) · C 22–28 hold (calm, slow push)
· D 28–36 standalone, slow orbit · E 36–40 standalone zenith / wide · F 40–52 inside the real **BACKROOM** with the
real VOID + FEAR rigs, using exactly the recipe below · G 52–58 BACKROOM looking up past the rigs · H 58–64 real rigs,
standalone two-shot · I 64–70 real rigs, the hero looking-up shot. Frames of A–C and F–I print
`COSMOSPIX t seg fear:[[x,y],[x,y]] void:[[x,y],[x,y]]` (screen px of each eye) to check framings. Debug ranges (100+
surveys, 9000+ empty baseline, k·1000+t variants incl. 13 = BACKROOM alone and 14 = the old recipe) are in the lab header.

## Look / layout (camera convention: usually at +Z looking −Z at the characters)

- **Sky shell**: an inside-out ellipsoid (radius × height) around the characters. Its colour comes from a nebula
  **cube map baked once on the GPU** (640² × 6, half float) and is looked up **by camera ray direction**, so the sky
  is at infinity (no parallax / swimming when the camera moves), while the shell's geometry is depth-tested against
  the host scene: anything farther than the shell (walls, far props) is covered by the cosmos. Where the sky is
  revealed the shell also **writes depth**, so a host's far transparent things (BACKROOM's own backdrop stars, far
  nebula sprites, the far screen glow) disappear behind the cosmos instead of floating over it.
- **Nebulae** (smooth domain-warped fbm, low contrast, compression-friendly), designed as distinct cloud complexes
  separated by deep dark space and dust lanes:
  - violet → magenta, high behind the characters (az −15°, el 32°);
  - **the warm counterpoint**: a cloud with a saturated **amber-gold heart and rose/peach edges** low behind the pair
    (az 0°, el 15°; warped toward the upper left of a front two-shot, above Fear's sightline, left/below the hero galaxy
    in the looking-up view) + a gold glow overhead beside the hero galaxy, and **gold rim light along the dust-lane
    edges** near both. Reads gold/peach after ACES (not salmon);
  - teal → blue on the left (az −70°), rose → magenta on the right horizon (az +90°), blue/teal and rose/violet
    behind the camera (+Z), a faint teal veil overhead, and a **calmer, darker blue/teal band at eye level behind the
    characters** (az 0…20°, el 0…15°) so faces keep a quiet background;
  - a faint pale galactic band (stars are denser along it) that is routed away from the hero galaxy.
- **Spiral galaxies** (5 discs, 4 baked variants, mipmapped 512²): gold bulge, blue/violet/teal arms with rose
  knots, dust lanes, sparse resolved stars; inclined discs at infinity, each spinning slowly.
  0 **hero** az +14°, el 28° (big, 27° across; fills the upper-left/top half of the gentle looking-up hero shot) ·
  1 az −7°, el 22° (upper left of a front two-shot) · 2 right horizon · 3 overhead · 4 behind the camera.
  (The sky drifts ≤ ±8° with `clock`, see below; aim at `cos.anchors.hero` when in doubt.)
- **Stars**: far layer (~2600 points on the shell at infinity), mid layer (520, world-space shell 0.42–0.92 of the
  radius → parallax), near layer (72, 0.9–4 m around `source`; 26 of them **kindle one by one** with a small 4-point
  flare). Gaussian cores ≥ 3.5 px (no sub-pixel shimmer), brightness power law (few bright), slow per-star twinkle on
  the brighter ~20 % only — **no global flicker** (frame-to-frame MAE at full reveal ≈ 0.002).
- **Nebula puffs**: 5 big soft world-space billboards (3–4 m, alpha ≈ 0.1) for parallax depth; they swell open
  when the bloom front reaches them.
- **Bits of meaning**: 9 tiny glowing glyphs (heart, sun, music note, house, handprint, pencil; rose / gold / teal /
  peach) orbiting the source at 1.9–3.5 m, 0.2–2.2 m above it, ~0.11–0.17 m big, gently breathing. Subtle.
- **Floor veil** (drawn over the floor plane): beyond `r0` the host floor fades into **exactly the shell's reveal look**
  (same deep space / nebula fronts / unfurling light / fringe along the same view ray — no seam where floor meets
  wall mid-reveal) + a procedural star field → the characters stand on an **island of floor** in space (host default
  r0 1.8 m → r1 4.4 m). Under the pair: a lilac/teal **light pool** (bright soft core + faint skirt) and a soft dark
  **contact core** (darkens whatever floor is there).
- **Island underlay**: a disc of dark **"glass over the universe"** just *below* the floor plane, with a faint fresnel
  mirror of the sky above and a lilac sheen. It is depth-tested, so it is **invisible wherever a host floor exists** and
  becomes the ground whenever there is none (standalone; or a host that hides its floor, e.g. BACKROOM at `cosmos`
  ≥ .999). The characters' own contact shadows land on it. Standalone: alpha .6, radius 3.6 m.
- **Lights** (in the group, intensity × reveal): a warm starlight **key** from just above the hero galaxy (from
  behind/above in a front view → a gentle warm rim) and a violet/teal **hemisphere** (standalone only by default —
  hosts such as BACKROOM tint their own ambient with their `cosmos` param; `opts.hemi` turns it on in a host). The
  standalone scene adds a soft lilac front fill so faces read; inner beings bring their own fresnel rims.

## Reveal timeline (`opts.reveal` 0 → 1)

| reveal | what happens |
|---|---|
| 0 | nothing is drawn (cosmos objects hidden; lights at 0) |
| .015–.29 | **stars kindle** one by one near the source (the Void), each with a little glint |
| .12 → ~.75 | the **walls dissolve** into deep starry space, opening outward from the source *as seen by the current camera* at a steady pace across the frame (front ≈ 1.9 frame half-diagonals per unit; a frame around the source is covered by ≈ .68), then races around the rest of the sphere; faint fringe. Host objects patched with `cos.dissolve()` open with the **same front** |
| .14 → .72 | a soft cloudy **light unfurls** from behind the source (violet → rose → teal), fading as the sky takes over (shell AND floor veil) |
| .24 → ~.85 | **nebulae bloom open** behind that front (brighter at their leading edge); puffs swell open |
| .5 → 1 | **galaxies drift in** (staggered: slide ~6°, grow 80 → 100 %, fade in) |
| .62 → 1 | glyphs appear |
| 1 | everything; the shell skips all masking math (cheapest state); dissolved host geometry emits no fragments |

Animate it with `k()` or `smooth()` over 6–12 s for "breathtaking yet calm". The front is camera-relative, so
avoid cutting in the middle of the .2–.75 range (a cut re-centres the opening on the new view); slow camera moves are fine.

## API

```js
const cos = await app.set('COSMOS');
// -> { scene, group, update(t, opts), attach(scene), dissolve(target, opts), hostFade(reveal), blendLook(base, w),
//      anchors, props, look }        (all methods are bound: destructuring is safe)
```
- `scene` — standalone THREE.Scene (dark background, cosmos group, a lilac front fill).
- `group` — everything cosmic (shell, island, floor veil, stars, puffs, galaxies, glyphs, cosmic lights). One parent at a time.
- `attach(scene)` — re-parent `group` (idempotent). **Call every frame before `update()`**, like characters. The first
  attach to a scene chains its `onBeforeRender/onAfterRender`: the group is drawn only in a render that follows an
  `update()` in the same frame (so a frame of another scene that renders the same host without updating the cosmos
  never shows stale cosmos state), and the dissolve gate knows which scene is rendering.
- `update(t, opts)` — pure function of (t, opts); returns the set.
- `dissolve(target, { opaque } = {})` — make host objects open with the **same front as the sky**. `target`: Object3D
  | Material | array. Transparent materials are patched **in place** (alpha × (1 − mask) + a faint fringe glow at the
  edge); a material's `userData.twin` (BACKROOM's transparent fade twins) is patched too, so **one call at setup**
  is enough (calling every frame is fine: idempotent). Opaque materials are skipped unless `opaque: true`: then each
  mesh gets a patched **clone** that is cut (discarded) behind the front — the original, possibly shared material
  (e.g. BACKROOM's cord material, also used by the cage tag string) is untouched. The patch is **inert** whenever this
  cosmos is not drawn in the scene being rendered (a live uniform gate), so the host looks exactly as before in every
  other scene; at reveal 1 patched geometry emits no fragments (no cost). Sprites/points/lines/ShaderMaterials are
  not patched (fade them with the host's own params).
- `hostFade(reveal)` — `0.97 · smooth(reveal / 0.8)`: the value to give a host's own room fade (BACKROOM `cosmos`).
  **Capped at .97 on purpose**: BACKROOM hard-toggles its bulbs at `cosmos ≥ .98` and hides its whole room group —
  floor included — at `≥ .999`; below the cap it keeps its floor (the veil turns it into the island) and nothing pops.
- `look` — default post look `{ bloom .7, bloomRadius .62, bloomThreshold .72, vignette .3, sat 1.08, lift, exposure 1.05 }`.
- `blendLook(hostLook, w)` — post look blended from a host look toward `look` (use `w = smooth(reveal)`).

### `update(t, opts)` fields (all optional)

| field | default | meaning |
|---|---|---|
| `reveal` | 1 | 0..1, see the timeline above |
| `center` | [0,0,0] | floor point the cosmos surrounds (the characters' spot; its y = floor height). Array or Vector3 |
| `source` | center+[0,1.6,0] | where the reveal starts — pass the Void's chest anchor (Vector3 ok) |
| `radius` | 7.5 | horizontal radius of the sky shell (m). Things farther than the shell are covered |
| `height` | .87·radius | vertical semi-axis (lower it under a low ceiling) |
| `lift` | 1.5 | shell centre height above `center` |
| `drift` | 1 | speed of all slow motion (sky drift, galaxy spin, glyph/near-star orbits, puff turn) |
| `clock` | t·drift | explicit motion clock (pass your own integral if you animate `drift`) |
| `intensity` | 1 | global brightness |
| `stars`, `nebula`, `galaxies`, `glyphs`, `puffs` | 1 | per-element multipliers (0 hides and skips the draw) |
| `bloom` | 1 | strength of the mid-reveal unfurling light |
| `fringe` | 1 | dissolve-front glow + nebula leading-edge brightening |
| `light` | 1 | cosmic key (host .65 × light, standalone 1.25) and hemi (standalone .3 + .35 × light) |
| `hemi` | false | also add the cosmic hemisphere in a host (true or a 0..1 strength) |
| `dissolve` | 1 | strength of the host dissolve on `cos.dissolve()`-patched materials (0 = they ignore the front) |
| `blendShell` | false | keep the shell a blended pass at reveal 1 (default: opaque pass, cheaper, identical pixels) |
| `floor` | — | see below |
| `eyeLight` | standalone 1, host 0 | blend `EYE_LIGHT` toward the cosmos key. It is **set from a fixed base** each frame (standalone: the engine defaults; in a host: the values the host set earlier in the same frame — so call `cos.update` after the host's update), never accumulated across frames |
| `standalone` | auto | force standalone/host defaults (auto = `group.parent === scene`) |

`floor` = `{ cover, inner, r0, r1, glow, contact, rc, island, islandR, reflect }`:

| key | host default | standalone | meaning |
|---|---|---|---|
| `cover` | 1 | 0 | sky over the host floor, ramping in from `r0` to `r1` |
| `r0`, `r1` | 1.8, 4.4 | 2.2, 5.5 | island radius / where the floor is fully sky (m, from `center`) |
| `inner` | 0 | 0 | sky tint inside `r0` |
| `glow` | .6 | 1 | the light pool under the pair |
| `contact`, `rc` | .28, 1.25 | .3, 1.25 | soft dark contact core under `center` (strength, radius m) |
| `island` | 1 | .6 | alpha of the glass island **under** the floor plane (host: only visible if the host floor is gone) |
| `islandR` | r1 | 3.6 | island radius (m) |
| `reflect` | 1 | 1 | strength of the island's sky mirror |

The sky drift is **bounded** (starts at 0.0045 rad/s, never more than ±8° from the designed layout), so which
galaxy is where never depends on absolute film time.

### Anchors (`cos.anchors`, world Vector3s, valid after `update`)
`center`, `source`, `domeCenter`, `hero` (hero galaxy), `galaxies[0..4]`, `nebula` (the violet complex), `up`
(zenith). Galaxy anchors sit on the shell along their direction from the shell centre — use them as **gaze
targets** (`fear.update(t, { gaze: cos.anchors.hero, ... })`) and to aim cameras; on screen the galaxies are at
infinity (direction matters, not distance).

### Props (`cos.props`)
`dome`, `floor` (veil), `island`, `far`, `mid`, `near`, `puffs`, `galaxies[]`, `glyphs`, `hemi`, `key`, `skyTex` (the
nebula cube map — usable as an env/reflection map if a rig wants cosmic reflections).

## Recipes

**Standalone background** (cuts to "pure cosmos"):
```js
setup: st.cos = await app.set('COSMOS'); st.scene = st.cos.scene;
update: applyShot(...); st.cos.attach(st.cos.scene); st.scene.add(st.void.root, st.fear.root);
        st.cos.update(t, { reveal: 1, center: [0.1, 0, 0], source: st.void.anchor('chest') }); st.look = st.cos.look;
```
**Inside BACKROOM** (walls/pipes/boxes and the bulb cords open with the cosmos front; the room keeps its floor, which
becomes the island; nothing pops — verified frame by frame across reveal .3–1 in lab segment F, `t` 43–49):
```js
// setup (once): patch the room's fade twins (alpha) + the two hanging bulbs (cut clones)
cos.dissolve(br.props.room);
cos.dissolve([br.props.bulb.parent, br.props.bulb2.parent], { opaque: true });
// update (every frame)
const reveal = k(t, [['bXX', 0], ['bXX+9', 1, 'inOut']]);
const fade = (a, b) => smooth(clamp((reveal - a) / (b - a)));
br.update(t, { ...,
  cosmos: cos.hostFade(reveal),                      // capped at .97: floor + bulbs never hard-toggle
  shafts: 1 - fade(0, 0.6), dust: 1 - fade(0, 0.6),
  lights: { bulb: 1 - fade(0.12, 0.4), bulb2: 1 - fade(0.12, 0.4) },   // bulbs dim as the front approaches them
});
cos.attach(br.scene);                                // before cos.update
cos.update(t, { reveal, center: [(vs.x + fo.x) / 2, 0, (vs.z + fo.z) / 2], source: voidRig.anchor('chest'), radius: 9 });
st.look = cos.blendLook(br.look, smooth(reveal));
```
BACKROOM's walls are only ~4.5 m from the Void spot (inside any useful shell), so without `dissolve` they would only
cross-fade uniformly with the host's `cosmos` (a hard horizontal seam at the wall top for ~3 s); with it they open
from the Void with the sky. The shell covers everything beyond `radius` (the far screen, the room's dark dome, its far
backdrop stars). If a host still hides its floor (e.g. the old recipe `cosmos: smooth(reveal / .8)` reaches .999 at
reveal ≈ .78), the island underlay takes over under the characters (no floating) — but the bulbs then still pop at
`.98`, so use `hostFade`.

**Camera recipes** (verified with the real VOID + FEAR rigs; screen y of the eyes, 720×1280; faces must stay in
y ≈ 110–850, subtitles below):
- **Two-shot from inside** (lab A/H; Void at [0.95, 0, −0.25] facing Fear, Fear at [−0.7, 0, 0.35]):
  `{ pos: [0.3, 0.95, 7.0], look: [0.25, 1.38, 0], fov: 46 }` → Fear's eyes **y ≈ 790**, the Void's eyes **y ≈ 415–470**.
  Galaxy 1 upper left, the warm gold cloud behind/left of the Void's hood, the hero galaxy just peeking at the top.
  In BACKROOM (lab F, pair at `voidSpot`/`fearOutside`, centre `mid`): `{ pos: [mid.x − .05, .95, mid.z + 6.6],
  look: [mid.x − .05, 1.4, mid.z − .2], fov: 46 }` → Fear **y ≈ 800**, the Void **y ≈ 470–480**.
- **Looking up past Fear + the Void** (hero shot, lab B/C/I): low camera in front-left of Fear, gentle 12° pitch,
  `{ pos: [-1.3, 0.3, 4.0], look: [-0.03, 1.34, -0.72], fov: 60 }` → Fear's upturned face **y ≈ 750** (x ≈ 220–270),
  both Void eyes **y ≈ 415–425** (x ≈ 545–650), the hero galaxy filling the upper-left/top half above Fear's sightline.
  In BACKROOM (lab G): `{ pos: [fo.x − .67, .3, fo.z + 2.77], look: [fo.x + .51, 1.34, fo.z − 1.98], fov: 56 }` → Fear
  **y ≈ 720** (in front of the Void's body), Void eyes **y ≈ 320–330**, galaxy upper left, the cage at the left edge.
  (These hold for `clock` ≈ 20–70 s; the bounded sky drift moves the galaxy ≤ 8°: re-check with `worldToScreen` of
  `cos.anchors.hero` if your scene time is far from that.)
- Pair with `void.update(..., { extra: { cosmos: 1 } })` (stars in its cloak brighten) and Fear's `wonder`/`awe`
  faces (`head.pitch −0.5…−0.6`, `gaze: cos.anchors.hero`, `extra.cry .3–.45` for tears of awe, `glow 1.3`).

## Rules & gotchas
- Keep the **camera inside the shell** (distance from the shell centre < radius − ~0.5 m); stars and galaxies are
  projected onto the shell along camera rays.
- The shell only covers geometry **farther than the shell**. Walls/ceilings closer than `radius` must be faded by
  the host (BACKROOM `cosmos` via `hostFade`) and preferably `dissolve`d, or the radius reduced (galaxies/sky stay at
  infinity regardless).
- Soft billboards (puffs, glyphs) never touch the floor; galaxies sit above ~10° elevation.
- Adding the group to a host adds 1 light (the key; +1 with `opts.hemi`) → one shader recompile of the host's lit
  materials on first attach (no per-frame recompiles; intensities go to 0 when hidden). `dissolve` compiles one extra
  program per patched material type once. At reveal 1 the shell switches to its solid program (compiled once).
- Order: `br.update` → `cos.attach` → `cos.update` (EYE_LIGHT blending reads what the host set this frame).
- All ShaderMaterials ignore scene fog by design (BACKROOM fog does not grey out the cosmos).

## Performance (SwiftShader, 720×1280, MSAA + bloom post)
PERF_PLACEHOLDER

## Known limitations
- The reveal front is computed **per camera** (screen-space-like opening from the source); a cut mid-reveal
  re-centres it. Hold the shot (or move slowly) through reveal .2–.75.
- Stars below the horizon are hidden by an opaque host floor; the floor veil replaces them with a procedural
  star field (statistically similar, not the same stars).
- `dissolve` does not patch sprites (BACKROOM's bulb halos: fade them with `lights.bulb`), points, lines or
  ShaderMaterials; transparent materials are patched in place (shared with anything else that uses them).
- Mid-reveal, where the shell is still partly transparent, a host's geometry beyond the shell (e.g. a far floor/wall
  corner) can show through faintly as the front passes; it is gone once the sky there is fully open.
- Shell parallax is zero by design (sky at infinity); depth comes from the mid/near star layers and the puffs.
- Galaxies/stars assume the camera is inside the shell; from outside (very wide shots) they are pushed far away
  and may clip.
- The glyph orbits can pass in front of the source at 1.9 m+; at extreme close-ups set `glyphs: 0` or lower.
