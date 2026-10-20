# "For Someone, Someday" — production spec

A ~5.5 minute **portrait (720x1280, 24 fps)** animated short for phones. An android with one directive — *help
people* — washes up on an empty island. It has unlimited time (solar powered, sand-proof) and no one to help, so it
spends decades preparing the island for whoever might come someday, gives part of its own power to a lighthouse,
and powers down. Years later a girl (Mira, 9) and her grandfather follow the light through a storm, find everything
it built, and wake it up. Framed by adult Mira's narration. Final message to viewers: if you're doing good no one
has seen yet, keep the light on — someone is on their way.

Project root: `film/` (this file's directory). Everything is deterministic code — no image assets.

## Files you must know

| Path | What |
|---|---|
| `script.json` | The screenplay: shots (id, desc, framing, mood) and lines (speaker, text, emotion, music notes). |
| `build/timeline.json` | Absolute times: every shot's start/end/dur; every line's start/end and **per-word** start/end. Music `notes` (word hits). |
| `build/lines.json` | Per line: duration, word times (line-relative), mouth tracks (100 Hz open/wide/round/press). |
| `build/voices/<lineId>.wav` | Voice clips (48 kHz mono). `build/dialogue.wav` = all lines placed on the timeline. |
| `render/lib/core.mjs` | Shared helpers: math/easing/noise, palette `PAL`, lights `LIGHT`, cel shading `cel()`, `splinePath`, `taperStroke`, `glow`, `blurLayer`, `cached`, camera `withCam`, `handheld`, `titleCard`, `hudText`. **Read it first. Use it.** |
| `render/lib/timeline.mjs` | `makeCtx(shot)` → ctx passed to shot draw fns (line/word timing, lip-sync). |
| `render/lib/frame.mjs` | `drawFrameAt(g, shot, t)` composes one frame (shot + overlays). |
| `render/render.mjs` | `node render/render.mjs --stills s01a@0.5,s01a@2 --dir tests/x` (PNGs) or `--from F --to F --out build/parts/x.mkv`. |
| `render/sheet.mjs` | Contact sheet: `node render/sheet.mjs s01a s01b --n 6 --out tests/sheet_s01.png` or explicit `s01a@1.2 s01a@3.4`. Tiles are labelled with the line being spoken. **Use Read on the PNG to look at your work.** |

Run node from `film/` (e.g. `cd film && node render/sheet.mjs ...`). Canvas is `@napi-rs/canvas` (Skia; supports
Path2D, gradients, `ctx.filter = 'blur(4px)'`, composite modes, `letterSpacing`). Fonts registered in core:
`TitleSerif`, `TitleSerifItalic`, `UISans`, `HUDMono`, `Carved`.

## Art direction

"Cinematic 90s anime" — think late-90s space-western / sci-fi TV anime: **realistic adult proportions** (heads
~1/7 of body for adults), long faces with defined jaw and cheekbones, narrow-ish expressive eyes with detailed
irises (not giant moe eyes; Mira's are a bit larger since she's a child), **hard-edged two-tone cel shading**
(one shadow tone, crisp edge, cast from the scene light), thin warm-dark ink outlines (`PAL.ink`), occasional
thin rim-light on the side away from the key light. **Painted backgrounds**: soft gradients, simple shapes, aerial
perspective (far things lighter/bluer), low-detail but atmospheric. Filmic color: warm highlights, teal/violet
shadows, nothing oversaturated. Light glows/flares with `glow()`.

"3D lifelike" is achieved through **depth**, not textures: pseudo-3D head turns (features slide around a
rounded head volume as yaw changes), parallax layers, slow camera push-ins / drifts (`withCam`, `handheld`),
depth-of-field blur on far/near layers (`blurLayer`), consistent light direction, contact shadows.

### Compression rules (the final file must be < 15 MB for 5.5 min — this matters)
- **No per-pixel noise, film grain, dithering or high-frequency textures.** Use flat cel fills + smooth gradients.
- Avoid full-frame shimmer (thousands of sparkles every frame). Water: a few smooth moving bands/foam shapes.
- Rain: a modest number of thin streaks (≤ 120), not a full-screen noise field.
- Static backgrounds: paint once with `cached(key, fn)` and blit; animate only what moves.
- Camera moves should be slow and smooth. Lightning flashes ≤ 3 per shot.

### Facial performance is the priority
Faces are never frozen. Every on-screen face has: natural auto-blinks (every 2–5 s, ~150 ms; slower, heavier
blinks when sad/tired), tiny eye saccades, subtle breathing (shoulders/head bob), and expression changes that
**follow the dialogue word by word** (use `ctx.word(lineId, 'word').start`). Listeners react while others speak
(small nods, brow lifts, lip presses, glances). Lip-sync on-screen dialogue with `ctx.mouth(speaker, t)`.
VO lines (narrator, Keeper's log lines with `vo: true`, Directive) have **no** lip movement — show the
face/body reacting instead. Emotion is mostly carried by **eyebrows (inner/outer), upper/lower eyelids, gaze,
mouth corners, head tilt, shoulder posture**. Subtle beats > big cartoon takes.

### "Say it, show it"
When a line describes an action or object, it is visible on screen at that moment (e.g. "pouring out of the rocks"
→ water pours on the word *pouring*; "sand can't get in" → sand slides off; "the light does" → eyes go to the
tower). The `desc` of every shot in `script.json` lists these beats.

## Character bible

**Keeper (the android)** — designation `H-7` stenciled small on the chest. Looks like a slender adult (~mid 20s),
androgynous-leaning male, calm face. Hair: ash-silver (`kHair`, shadow `kHairShadow`), medium length, messy, a few
strands falling across the forehead, slightly spiky clumps at the back; moves in wind. Skin: pale porcelain
(`kSkin`/`kSkinShadow`) with thin **panel seams** (`kSeam`): one along the jaw from below the ear toward the chin,
one short line at the temple. Eyes: amber irises (`kIris`) with a thin luminous ring (`kIrisRing`) that glows when
active (param `glow` 0..1; flickers on boot, dims on power-down; can tint cyan `PAL.hud` when the Directive
speaks). Outfit: worn teal-navy work jumpsuit (`kSuit`) with a faded orange stripe across the chest (`kStripe`),
dark undersuit collar; **dark-blue solar-cell shoulder plates** (`kPanel` with grid `kPanelGrid`) that can glint.
A rectangular chest panel can open to reveal glowing power cells (gold with cyan core). Costume variants:
`new` (day 1), `worn` (faded `kSuitFaded`, frayed sleeves), `dormant` (worn + sand on shoulders/lap, vines across,
dull panels). Hands: pale, subtle seam at the wrist.

**Mira (girl, 9)** — brown skin (`mSkin`), dark curly hair in a puffy high ponytail with loose curls at the
temples (`mHair`/`mHairHi`), large warm dark-brown eyes (`mIris`), a few freckles, small nose, expressive brows.
Yellow raincoat (`mCoat`) with hood down, red striped shirt under it (`mShirt`), rolled-up pants, bare feet on the
island. In the storm the hood is up and she is soaked. Epilogue (s10a): older silhouette only.

**Grandpa** — ~70, weathered tan skin (`gSkin`), white short beard and bushy white eyebrows (`gBeard`), deep-set kind
grey-blue eyes (`gIris`) with crow's feet, big nose, navy knit cap (`gCap`), olive heavy rain jacket (`gCoat`).
Broad, slightly stooped. Takes his cap off in s09h.

**Captain** — small hermit crab: orange-red legs/claws (`crab`), cream spiral shell with brown stripes
(`shell`, `shellStripe`), black eye-stalks that swivel. Expressive through eye-stalk angle and claw raises.

**Directive** — no body. It is a voice inside Keeper. When it speaks, the global overlay shows a small cyan HUD
voice indicator and Keeper's iris ring may tint cyan.

## Module contracts (render/lib)

All draw functions take the canvas context `g` first, draw in **screen/world pixels** at the given position/scale,
never call `g.setTransform` (so they work under `withCam`), restore state they change, and are pure functions of
their params (time is passed in). Export everything named.

### face.mjs — pseudo-3D anime head rig (shared by all three characters)
```js
drawHead(g, style, p)          // style = STYLES.keeper | STYLES.mira | STYLES.grandpa
STYLES                         // exported style objects (proportions, colors, hair/beard/cap drawers, extras)
EXPR                           // presets: neutral, worried, sad, hopeful, smile, laugh, surprised, determined,
                               // tender, tired, awe, relief, cryingSmile, sleep, wry, fond, focused, scared,
                               // shout, reading, wonder, pained, moved
expr(name, overrides?)         // -> params object (copy)
blend(a, b, k)                 // numeric lerp of two param objects
blinkAt(t, seed, rate=1)       // 0..1 lid-closure from natural blinking (deterministic)
saccade(t, seed, amp=1)        // {x, y} small gaze jitter to add to gazeX/gazeY
lipsync(p, m)                  // apply ctx.mouth(...) result m onto params p (returns new p)
```
Params `p` (all optional, defaults neutral):
- placement: `x, y` (center of head = between the eyes), `s` scale (**s = 1 → crown-to-chin ≈ 330 px**; CU ≈ 1–1.3,
  ECU ≈ 2–3, MCU ≈ 0.6–0.8, MS ≈ 0.35–0.5, wide ≤ 0.15 — at s < 0.25 drop fine details), `yaw` (-1..1 ≈ ±60°,
  + = character turns to screen-right), `pitch` (-1..1, + = looks up), `roll` (radians).
- lighting: `light` (a `LIGHT.*` object), `lightDir` (-1 key from screen-left .. +1 from right), `rim` (0..1),
  `lightK` (0..1 how strongly the light tints the fills, default 0.6).
- eyes: `eyeOpen` (0 closed .. 1 normal .. 1.35 wide), `eyeOpenL`, `eyeOpenR` (override per eye), `lowerLid` (0..1
  cheek-raise/squint), `blink` (0..1 extra closure, from `blinkAt`), `gazeX`, `gazeY` (-1..1), `pupil` (0.6..1.4),
  `tears` (0..1 glassy wet eyes with brighter highlights / pooled water line), `tearDrop` (0..1 progress of a drop
  rolling down the cheek; `tearSide` -1|1).
- brows: `browInner` (-1 angry/knit-down .. +1 sad/worried up), `browOuter` (-1..1), `browRaise` (-1..1 whole brow),
  `browL`, `browR` (extra per-side raise), `browKnit` (0..1 pull together).
- mouth: `smile` (-1 frown .. 1 smile), `mouthOpen` (0..1), `mouthWide` (-1 pucker .. 1 wide), `mouthRound` (0..1),
  `mouthPress` (0..1 lips pressed / M-B-P), `mouthAsym` (-1..1 one-sided smirk), `lipTremble` (0..1, needs `t`),
  `teeth` (bool, default true when open wide).
- skin/fx: `blush` (0..1), `wet` (0..1 rain droplets on face), `sweat`, `dirt`, `sand` (0..1 sand grains on cheek).
- Keeper only: `glow` (0..1 iris ring light), `glowColor` (default kIrisRing), `seams` (default true).
- hair: `t` (time, for wind motion), `wind` (0..1), `windDir` (-1|1), `wetHair` (0..1 flatter, darker).
- `hood` (Mira, 0..1 raincoat hood up), `cap` (Grandpa, default true).

### body.mjs — full-figure puppet + hands (all three characters, plus costume variants)
```js
drawFigure(g, who, pose, opts)   // who: 'keeper'|'mira'|'grandpa'
  // opts: { x, y (ground point between the feet, or seat point when sitting), s (scale: s = 1 -> standing
  //   height 1000 px for Keeper; Mira is 0.62x, Grandpa 0.95x of Keeper at same s), facing (-1|1 mirror),
  //   costume ('new'|'worn'|'dormant' for keeper; 'storm'|'island' for mira/grandpa), light, lightDir, t,
  //   head: (g, hx, hy, hs, roll) => void   // callback that draws the head at the neck socket
  //   chestOpen 0..1, cellOut 0..1 (Keeper), capInHand (grandpa), hood (mira), wet 0..1, sand 0..1, vines 0..1,
  //   breathe (0..1 amount), panelGlint (0..1) }
POSES                            // named poses (joint-angle objects) incl.: stand, standLookUp, standWind,
                                 // walk (use walkPose(phase)), kneel, crouch, crouchCarve, sitGround, sitKneesUp,
                                 // sitRest (power-down, slumped), sitDoorway, lieSide, pushUp (rising from lying),
                                 // reachDown, cuppedHands, holdUp (lantern/cell), chestOpen, handsLook (looking at
                                 // own open hands), cling (to mast), tiller, drink, brush (reach to touch), point,
                                 // capChest (cap held at chest), holdHands
walkPose(phase)                  // walk cycle 0..1
blendPose(a, b, k)
drawHand(g, o)                   // detailed hand for inserts: {x, y, s, rot, side:'L'|'R', who, shape:'open'|'cupped'|
                                 // 'pinch'|'fist'|'point'|'relaxed'|'hold'|'brush', light, lightDir}
headSocket(who, pose, opts)      // -> {x, y, s, roll} where the head is drawn (so shots can place things)
```
The head is NOT drawn by body.mjs itself — it calls `opts.head(g, hx, hy, hs, roll)` at the right moment in
draw order (so face.mjs and body.mjs stay independent). `hs` uses the same scale convention as `drawHead`'s `s`.

### env.mjs — painted backgrounds (all accept `{t, cam?}` and paint the whole frame unless noted)
Continuous time of day: `tod` in hours (5.5 dawn, 7 morning, 12 noon, 17.5 golden, 18.7 dusk, 20.5+ night) so
time-lapses can sweep it. Provide at least:
`skyAt(tod)` → palette object {top, mid, horizon, sun, sea, seaDeep, key, shadow} (smoothly interpolated);
`sky(g, o)` (o: tod, horizonY, sunX, clouds, stars, t), `sea(g, o)` (horizonY, tod, t, rough 0..1, beam?),
`surfClose(g, o)` (s01a: wet sand plane seen close, foam washing in/out with `t`),
`beach(g, o)` (horizonY, tod, t — sky + sea + sand + foam line; the generic beach backdrop),
`islandWide(g, o)` (EWS of the island: beach, palms, jungle hill, rocky point; options: tod, t, hut 0..1,
tower 0..1, lantern 0..1, beamAngle, palmGrowth 0..1, boats n, keeperTiny {x,y} — tiny silhouette),
`tideline(g, o)` (low-angle close sand for the crab), `spring(g, o)` (mossy rocks + pool, jungle shade),
`path(g, o)` (sandy path at jungle edge, ground-level), `jungleEdge(g, o)`, `clearing(g, o)`,
`reef(g, o)` (shallow clear water with coral below), `pointNight(g, o)` (rocky point, stars, black sea; works for
dusk via tod), `hutDoorway(g, o)` (interior looking out at the rain-night through the door frame),
`hutInterior(g, o)` (dry, warm light through gaps, carved stone on wall drawn by props), `palmUp(g, o)`
(low-angle tall palm, morning), `stormSea(g, o)` (huge dark waves, rain, lightning param), `reefChannel(g, o)`
(storm night, jagged rocks with white marker stones/pole, beam), `towerBase(g, o)` (morning, base of the stone
tower, sand, sea behind), `cove(g, o)` (dusk epilogue: cove with moored boats, tower with beam, gardens).

### props.mjs — objects  /  fx.mjs — effects  /  overlays.mjs — global overlay
props: `crab(g, o)` {x,y,s,t, flipped, legs (anim 0..1), eyeYaw, clawRaise, walk}, `carvedStone(g, o)` {x,y,s,
text lines, arrow, icon 'check'|'x', progress 0..1 (strokes appear in order), shape, light}, `mapStone(g, o)`,
`bush(g, o)` {berry:'blue'|'red'}, `hut(g, o)` {build 0..1, view 'front'|'side'}, `tower(g, o)` {build 0..1,
lantern 0..1, beamAngle, view}, `beam(g, o)` {x,y, angle, length, spread, intensity} (additive light cone),
`boat(g, o)` {x,y,s,roll,heave, sail}, `palm(g, o)` {x,y,s,growth 0..1, sway, t}, `coconut`, `sapling`,
`powerCell(g, o)` {x,y,s, glow}, `shellTool`, `markerStone`, `gull(g, o)` {x,y,s,flap}.
fx: `waterPour(g, o)` {x0,y0 (lip), x1,y1 (hands), t, flow 0..1}, `splash`, `sandSlide(g, o)` (grains sliding off a
surface), `sandGust(g, o)`, `rain(g, o)` {t, intensity, angle}, `faceDrops(g, o)`, `lightning(g, o)` {k},
`scanRing(g, o)` {cx, cy, r, k}, `glint(g, o)` {x,y,s,k} (4-point star sparkle), `chips(g, o)` (stone chips),
`dayCounter(g, o)` {text, k}, `powerReadout(g, o)`, `stars(g, o)`, `shipLight(g, o)`, `leavesVines(g, o)`.
overlays.mjs: `drawOverlays(g, shot, t, ctx)` — when the Directive is speaking (`ctx.speaking('directive', t)`),
draw a small, elegant cyan HUD voice indicator near the top of the frame (a thin bracket frame with a tiny live
waveform driven by the directive's audio activity; fades in/out over 0.25 s). Keep it small (≤ 260x60 px) and in
the top 12% of the frame. Nothing else global.

## Shots (render/shots/sNN.mjs, one file per scene)
```js
import ... from '../lib/*.mjs';
export default {
  s01a(g, t, ctx) { ... },   // paint the WHOLE frame (opaque). t = seconds since shot start, 0..ctx.dur
  s01b(g, t, ctx) { ... },
};
```
- Must be a pure function of `t` (no state across frames, no Math.random — use `rng(seed)`/`noise1`).
- Sync to dialogue with `ctx.line(id).start/end` and `ctx.word(id, 'word').start`. Read `build/timeline.json`
  for the exact shot durations, lines and word times.
- On-screen speakers lip-sync via `lipsync(p, ctx.mouth(speaker, t))`. VO lines → no lip movement.
- **Frame 0 of s01a is the video's first frame / social preview: a fully lit, beautiful close-up. No fade from
  black anywhere at the start.** Cuts between shots are hard cuts unless a shot desc asks for something else.
- Subtitles are burned in later by ffmpeg in the lower-middle band (roughly y 840–1010). Keep important faces
  and on-screen text out of y 820–1030, and keep the bottom 12% free of key content (phone UI covers it).
- Keep important content inside x 40..680.

## Audio (audio/)
Voices are done. Score + SFX + mix are generated from `build/timeline.json` (shot moods + word `notes`): soft piano,
warm strings/pads, celesta/bells for "high" word hits (hopeful), low cello/piano/bass swells for "low" hits
(existential/sad) — hits support the words, never mask them. Ambience: surf, wind, gulls, night insects, rain,
thunder, storm. Music ducks under dialogue. Output `build/mix.wav` (48 kHz stereo, ~-14 LUFS integrated).
