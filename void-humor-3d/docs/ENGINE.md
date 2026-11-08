# ENGINE — how the 3D film is built (read this before writing any rig, set or scene)

Project root: `/home/user/game1/void-humor-3d` (all paths below are relative to it).
Story/cast/look: `BIBLE.md`. Screenplay: `data/screenplay.json` (format `data/SCREENPLAY_FORMAT.md`).

## Runtime

- three.js r170 (ES modules, import map: `three`, `three/addons/...`), rendered in headless Chromium with
  SwiftShader (CPU WebGL2). **Frame = 720×1280, 24 fps.** MSAA ×4 HDR → bloom → ACES → grade (`core/post.js`).
- Every frame is a **pure function of time t** (seconds). NEVER use `Math.random`, `Date`, `performance.now`,
  or state carried between frames. Use `core/util.js` (`rng(seed)`, `hash1`, `noise1`, `fbm1`, `schedule`).
  Frames are rendered out of order by several browsers in parallel.
- Performance budget: a full frame (set + up to 4 characters + post) should render in **< 1.2 s** on SwiftShader.
  Keep geometry moderate (spheres 32–64 segments, not 256), few lights (hemisphere + 1–2 directional + a few
  point lights), at most ONE shadow-casting light (1024² map) per set, no per-frame `new` of big geometries
  (update attributes in place — `SweepTube` does), no per-frame shader recompiles.
- Compression-friendly: avoid fine high-contrast noise textures, flicker, full-frame sparkle. Smooth gradients,
  clean shapes, soft light.

## Commands

```bash
node tools/render.js stills --lab <name> --t 0,1.5,3 [--out out/stills]      # stills from a lab module
node tools/render.js sheet  --lab <name> --from 0 --to 10 --n 12 --cols 4 --out out/sheets/<x>.jpg
node tools/render.js bench  --lab <name> --t 2                                # s/frame
node tools/render.js stills --t 12.5,40                                       # film mode (needs scenes)
node tools/render.js sheet  --from 30 --to 60 --n 16 --out out/sheets/s03.jpg # film contact sheet
```
Use the **Read tool on the output .jpg** to look at what you made. Look critically, fix, re-render. Iterate.
Write scratch images to `out/` (git-ignored).

## Coordinate conventions

- Metres. Y up. Ground at y = 0. A character's root sits at its feet; **yaw 0 = facing +Z** (toward a camera
  placed at +Z looking toward −Z). +X = the character's LEFT when yaw = 0 (screen-right in a front view).
- Heights: JESUS 1.75, USER 1.65, VOID ~3.0 (wide, plump), FEAR 0.85, MAGICIAN 2.1 (stooped).
- Head-local face space (core/face.js): +Z out of the face, +Y up, +X character's left; `u` = longitude
  (+ toward character's left), `v` = latitude (+ up).

## Core modules (`web/src/core/`)

| module | what |
|---|---|
| `util.js` | clamp/lerp/smooth/ease, `rng`, `hash1/2`, `noise1`, `fbm1`, `schedule`, `lagged` |
| `timeline.js` | `T('s03b02.end+0.4')` → seconds; `k(t, [[time, value, ease], ...])` keyframes (numbers, arrays, flat objects); `env`, `prog`, `between`, `beatsOf`, `linesOf` |
| `materials.js` | `skin`, `cloth`, `hair`, `being` (effervescent inner-being glow), `flat`, `enhance` (rim/glow/fizz/wrap/jaw-drop), `glowSprite`, `contactShadow`, `GLOBAL.uTime` |
| `face.js` | `Face` (eyes+lids+brows+painted mouth decal, auto-blink, saccades, gaze, lip-sync blend), `Eye`, `X(name, overrides)`, `EXPR` presets, `FACE_DEFAULTS`, `ellipsoidSurface` |
| `limbs.js` | `SweepTube` (in-place swept tubes), `solveIK2`, `orientYZ`, `Hand` (capsule cartoon hand with pose params), `Limb` (IK tube arm + hand) |
| `character.js` | `Character` base (root, `place`, `breath`, `sway`, `speech(t,pose)`, anchors), `gazePoint` |
| `particles.js` | `Particles` (deterministic billboards: `stream`, `burst`, `add`), `CELL` sprite ids (star, dot, galaxy, puff, dust, ring, nebula, heart) |
| `camera.js` | `applyShot`, `shotAt` (keyframed camera), `framed(look, {dist,yaw,pitch,fov,screenY})`, `orbitPos`, `worldToScreen` |
| `speech.js` | `speechAt(SPEAKER, t)` lip-sync sample `{open,wide,round,close}`, `isTalking` |
| `post.js` | look params per scene: `{ bloom, bloomRadius, bloomThreshold, vignette, sat, warm, lift, gain, fade, exposure }` |
| `context.js` | `CTX.camera`, `EYE_LIGHT` (key direction/colour for all eyeball shaders — sets should set it) |

### Face params (flat; build with `X('happy', { mOpen: 0.2 })`, keyframe with `k()`)
Eyes/lids: `lidU` (1 normal, 0 closed, ~1.4 wide), `lidL` (0 relaxed .. 1 raised/squint), `lidAngry`, `lidSad`
(lid-line tilt), `lidAsym`, per-side `lidUL/lidUR/lidLL/lidLR`, `pupil` (1 normal), `blink` (manual 0..1),
`autoBlink` (0/1), `wet` (extra eye shine), `squint`, `gazeYaw/gazePitch` (radian offsets), `saccade` (0..1).
Brows: `browIn`, `browOut`, `browMid` (−1..1 raise), `browSq` (0..1 furrow), `browAsym` (−1..1, + raises the
character's left), per-side `browInL/browInR/browOutL/browOutR`.
Mouth: `mOpen` (0..1.3), `mWide` (−1..1), `mRound`, `mSmile` (−1..1), `mAsym` (smirk), `mTeethU/mTeethL`,
`mClench` (gritted-teeth grimace), `mPress` (pressed lips), `mTongue`, `mPout`, `mTremble`, `mShift`.
Other: `blush`, `tearL/tearR` (0..1 streak length), `talk` (lip-sync strength, 0 = mouth ignores speech).
Presets (`EXPR`): neutral soft happy grin laugh giggle tender sad sadSmile scared terror surprised wtf angry scowl
awkward smug sideeye skeptical annoyed disgust wonder hopeful worried guarded relieved innocent hungry.
Lip-sync is blended automatically from `data/lipsync.json` for the character's speaker (pass `speech:false` in
the pose to suppress, e.g. while a line is voice-over).

## Characters (`web/src/chars/<name>.js`)

```js
export async function create() { return new Jesus(); }   // registered in src/chars/index.js as CHARS.JESUS
class Jesus extends Character { constructor() { super({ name: 'JESUS', speaker: 'JESUS', height: 1.75, seed: 11 }); ... }
  update(t, pose) { ... } }
```
`update(t, pose)` — pose fields (all optional, sensible defaults = relaxed standing idle with breathing):
- `pos: [x,y,z]`, `yaw` (rad)
- `body: { lean, tilt, twist, crouch (0..1), sit (0..1 = on the ground on its backside), kneel (0..1),
  breathe (amplitude mult, default 1), breathRate, shrug (0..1), slump (0..1), bounce, recoil, hunch }`
- `walk: { amount (0..1), phase (cycles, e.g. t*1.8), style: 'walk'|'run'|'stomp'|'sneak'|'waddle' }`
  — the scene moves `pos` itself; `walk` animates legs/arms/bob consistent with `phase`.
- `head: { yaw, pitch, roll }` (relative to torso, rad), `gaze`: Vector3 | [x,y,z] | Character | 'camera' | null
- `armL`, `armR`: `{ target: [x,y,z] world | Vector3 | null, pole: [x,y,z] dir, reach (0..1 blend from rest),
  hand: { curl, point, spread, thumb, cup, splay, grip }, palm: [x,y,z] palm-normal dir, fingers: dir,
  preset: 'rest'|'hips'|'crossed'|'up'|'shrug'|'wave'|'cover_mouth'|'chin'|'pocket'|... }`
  (`preset` gives a good default the target may override; `crossed` = arms folded on the chest.)
- `face`: flat face params (see above)
- `speech`: false | sample (default: automatic lip-sync)
- character-specific extras (documented in `docs/chars/<name>.md`).
Anchors (world positions after `update`): `head`, `eyes`, `mouth`, `earL`, `earR`, `chest`, `back`,
`shoulderL`, `shoulderR`, `handL`, `handR`, `hip` (+ any extras). Use them for gaze targets, whispering, arm
around shoulders, pats, kicks, camera framing.
Every character ALSO provides `web/src/labs/<name>.js` (turntable / expression sheet / pose sheet / walk) and
`docs/chars/<name>.md` (look, pose extras, tips, perf).

## Sets (`web/src/sets/<name>.js`)

```js
export async function create() { return { scene, update(t, opts), anchors: {...}, props: {...}, look: {...} }; }
```
`scene` is a `THREE.Scene` with sky/background, ground, lights, props. `update(t, opts)` animates ambient life
(drifting seeds, clouds, flicker-free glows) and set-specific params (`opts.timeOfDay`, `opts.voidSky`, ...).
`look` is the default post look. Sets must set `EYE_LIGHT` to match their key light. Register in
`src/sets/index.js` as `SETS.EDGE`, `SETS.BACKROOM`, `SETS.COSMOS`.

## Scenes (`web/src/scenes/sNN.js`)

```js
export default { id: 's03',
  async setup(app) { const set = await app.set('EDGE'); const jesus = await app.char('JESUS'); ...; return { scene: set.scene, set, jesus, look: {...} }; },
  async update(t, app, st) { st.scene.add(st.jesus.root); /* (re)attach chars you use */ st.set.update(t, {...});
    st.jesus.update(t, { pos, yaw, face: k(t, [...]), ... }); applyShot(app.camera, shotAt(t, [...]), t); st.look = {...}; } }
```
Times come from the timeline: `T('s03b04')`, `T('s03b04.end-0.2')`. Build everything relative to beats so
re-timed audio re-times the picture automatically. Keep faces in screen y ≈ 110–850 px (subtitle band below).
