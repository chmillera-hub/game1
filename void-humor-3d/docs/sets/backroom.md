# SET: BACKROOM — `SETS.BACKROOM` (`app.set('BACKROOM')`)

Files: `web/src/sets/backroom.js` (set), `web/src/labs/backroom.js` (lab), this doc. No core files were modified.

```bash
node tools/render.js sheet --lab backroom --from 0.6 --to 11.4 --n 10 --cols 5 --out out/sheets/backroom_angles.jpg  # 10 angles
node tools/render.js sheet --lab backroom --from 12 --to 16 --n 6 --cols 6 --out out/sheets/backroom_door.jpg        # latch + door
node tools/render.js sheet --lab backroom --from 16.2 --to 26 --n 16 --cols 8 --out out/sheets/backroom_crash.jpg    # crash
node tools/render.js sheet --lab backroom --from 26 --to 36.4 --n 12 --cols 6 --out out/sheets/backroom_end.jpg      # hat, roll, cosmos
```
Lab segments (exported `segments`): 0–12 angles (1.2 s each: wide, reverse, corner, cage, fearPOV, lurk, sideKick,
farCorner, high, latch) · 12–16 latch + creaky door · 16–26 crash (placeholder flies in, impact at 16.8, `crashT = t − 16.8`;
corner medium until crashT 5, then a LOW SIDE VIEW along the back wall: wringer clearance, puddle, sign) · 26–30.5 bucket
hat + mop wig (camera orbits on the room side of the head, never outside the walls) · 30.5–33.5 rolling bucket (whole path in
frame) · 33.5–36.5 cosmos fade. Placeholders: VOID 3.0 m indigo bell, FEAR 0.85 m lavender bean, MAGICIAN 2.1 m grey capsule
+ hat (sits slumped in the corner after the crash).

## Look
The back of the creator's mind: a dim, cavernous, cozy-creepy room. Smooth warm floorboards (low-contrast 0.33 m planks
running toward the screen, a modest tight sheen — no grey haze), plum-grey plaster walls with a dark wood wainscot and old
pipes that **dissolve upward into darkness** (vertex-colour fade, walls stop at 5.6 m where a dark gradient dome takes over),
a doorway into deeper dark (back-left), stacked boxes and a dust-sheet-draped armchair lump as silhouettes, pillars receding on
the open left side. Light: dim cool hemisphere + the **far cool "screen of consciousness" key** (directional from +Z, the one
shadow caster: shadows fall back toward the corner, so the Void's shadow is where the magician lurks) + the **Void's violet
starlight** (movable PointLight) + a **warm bare bulb on a cord** over the cage + a second bare bulb over the janitor corner
(its warm pool is a cheap in-shader fake glow that lights the floor, the walls AND the corner props — wrap-lit diffuse plus a
Blinn glint on the zinc — so the wreck reads warm-neutral metal against the cool-grey magician; the real light is opt-in).
Three soft dusty light shafts with drifting motes. Reverse angles (camera looking +Z) show the far screen as a **readable
soft-edged glowing rectangle** (just under the bloom threshold, with a small hot centre that blooms gently) and a narrow
soft streak of it in the floor.

- **TIME-OUT cage** (original birdcage): aged yellow-brass round bars (20 around, r 0.45 m; soft highlights, rust gathering
  low and creeping up the bars), iron base plate, mid band + shoulder ring, domed top (hub, finial ball, hanging ring; top of
  ring ≈ 1.17 m), a 3-bar door with a little arched scroll, hinge knuckles, a brass **turn-latch** (plate + lever + knob over a
  catch on the jamb) and a manila **paper tag** on a string with hand-lettered "TIME-OUT" (canvas, stroke font) that faces the
  default +Z camera.
- **Janitor corner** (back-right, original, no brands): galvanized **wringer bucket** on casters tucked right into the corner
  (press + red-grip lever), a **cotton mop** standing in it (gravity-drooping round, tapered cords with per-strand value
  variation), a standing **bucket** (the future hat; 48-segment lathe, soft rolled ribs), an upturned bucket used as a stool
  with **two spray bottles** (mint, pink; plain cream label bands) and a **stack of five rags** further along the back wall
  (all visible in the corner medium), a **corn broom** and a **push broom** leaning on the right wall, a yellow A-frame
  **wet-floor sign** ("CAUTION", a generic slipping-figure pictogram in a triangle, "WET FLOOR" on the two OUTER faces; the
  inner faces are plain yellow), standing slightly crooked. Galvanized zinc is warm-neutral grey (not blue).

## Layout (metres, world; also `set.layout`)
The action runs on one diagonal, front-left → back-right: cage/Fear → Void → magician → corner. The Void faces the cage
at yaw −45° (3/4 to a camera on +Z), so its backward donkey-kick sends the magician straight into the corner.

| name | value |
|---|---|
| back wall / right wall / left wall | z = −5.0 / x = 4.8 / x = −8.5 (walls are single-sided: cameras may sit outside the right or back wall and look in — cutaway, see below) |
| far screen glow | z = +24 (behind a camera that looks −Z) |
| `voidSpot` | (0.30, 0, −0.50), `yaws.void` = −π/4 |
| `fearOutside` | (−0.73, 0, 0.53), `yaws.fear` = 3π/4 (facing the Void) |
| cage | centre (−1.60, 0, 0.02), `yaws.cage` = 60° (door faces fearOutside / the Void) |
| `lurkSpot` | (1.43, 0, −1.63) — 1.6 m behind the Void, `yaws.magicianLurk` = −π/4 |
| `crashSpot` | (3.98, 0, −4.18) — 3.6 m further along the kick line; `yaws.magicianCrash` = −π/4 (back to the corner) |
| wringer (intact) | (4.45, 0, −4.62), in the corner BEHIND the landing spot; after the crash it lies along the back wall, x ≈ 3.0–4.3, z ≈ −4.95…−4.4 (behind his right hip; clear of a 2.1 m body sitting at `crashSpot`, legs to the room) |
| hat bucket / stool + sprays / rags | (3.56, −4.66) / (2.69, −4.68) / (2.13, −4.70) |
| bulb / corner bulb | glass ≈ (−1.15, 2.19, 0.50) / (3.45, 2.04, −3.75) |

**Cutaway (automatic).** The wall dressing that would stand between a camera placed beyond a wall and the set — right-wall
wainscot + pilasters, back-wall wainscot + pipes + door trim, the corner riser pipe — lives in three groups that are hidden for
the render whenever the rendering camera is beyond that wall (`x > 4.75` / `z < −4.95`; the corner pipe for either). It is
decided in `scene.onBeforeRender` from the camera actually being rendered, so it does not matter whether a scene calls
`update()` before or after placing its camera, and frames stay pure. (If a scene replaces `set.scene.onBeforeRender`, chain the
previous handler, as s22 does.)

## API
`const set = await app.set('BACKROOM')` → `{ scene, update(t, opts), anchors, props, look, yaws, layout, timing, cageBar(angleDeg, y), flightPos(u, apex) }`.
Call `set.update(t, opts)` every frame (it is a pure function of `(t, opts)`; it resets everything it owns, sets
`EYE_LIGHT`, and moves props). Every field is optional; `{}` = the intact, quiet room.

### `opts`
| field | meaning |
|---|---|
| `latch` 0..1 | turns the brass latch lever from across the gap (locked) up to vertical (open), with a tiny click-overshoot near 1 |
| `cageDoor` 0..1 | swings the door open on its hinge (0 → 112°) with a **creaky, hitching arc** (monotonic stutters), a small settle at the end and a hair of hinge sag; the paper tag jiggles while the door moves |
| `tagSwing` | extra tag sway (0 = gentle idle) |
| `crash` 0..1 | the janitor-corner smash. With `crashT` (seconds since impact, may be negative = intact) the props follow their slapstick timeline and `crash` blends intact (0) → smashed (1). Without `crashT`, `crash` alone drives it (`crashT = crash × 6 s`). |
| `crashT` | seconds since the magician hits the pile (deterministic; keyframe it as `t − T('impact')`) |
| `signFall` 0..1 | override the wet-floor sign's final tip-over (default: automatic at `timing.signFall` = 4.6 s after impact, 0.62 s fall). Before it the sign **teeters on one corner** the whole time |
| `signOn` (m) | height of whatever the falling sign lands on (e.g. 0.3 for the magician's legs); 0 = flat on the floor |
| `signAt` [x,z], `signToward` [x,y,z] | where the sign ends up teetering (default just in front of `crashSpot`) and the point it falls toward (default `crashSpot`) |
| `broomSlide` 0..1 | the last (push) broom, which survived the crash wobbling, slides down the wall and clatters flat (default automatic at `timing.broomSlide` = 7.2 s after impact; s21b01) |
| `rollBucket` 0..1 | the knocked-over bucket rolls slowly on along a lazy arc "across the floor from the corner" (s21b04); `rollTo` [x,z] changes the end point (default (−1.25, −3.35), ≈ `anchors.rollEnd`). Use the same `rollTo` in every scene after the crash |
| `bucketHat` | `{ pos, up, yaw, at, lift, tilt, blend }` — put the hat bucket upside-down on a head: `pos` = head-top point (magician `anchor('headTop')`), `up` = head-up direction (magician `anchor('headUp')`, default world up), `yaw` (rad, about `up`), `lift` (m above the head top; **default 0.075**: the bucket rides high so a long nose clears UNDER the rim; the "bucket lifts an inch" peek = 0.075 + 0.035), `tilt` (rad). During a crash it **flies from the pile** onto the head, flipping, landing at `at` s after impact (default 0.92) with a BONK squash; `blend` 0..1 overrides that flight. Without a crash it simply sits on the head. The wire bail hangs by gravity → a chin strap. |
| `mopWig` 0..1 or `{ blend, yaw, pos }` | the mop flops onto the hat like a **wig**: arcs in, strands morph into a draped mop-top over the bucket (bangs over the eyes), handle sticking out at ~40°. Strands stay round (their cross-sections turn with the bend) and taper to the tips. Needs `bucketHat` (or `pos` = top point). `yaw` turns which way the handle sticks out |
| `voidLight` | number = intensity multiplier, or `{ pos, intensity, color, distance }`. Default: violet (0x9a7cff) 3.2 at (−0.41, 2.0, 0.21), in front of the Void's face. You may also move `props.voidLight` **after** `set.update()` |
| `cosmos` 0..1 | the room dissolves into space (s22b02), **continuously**: walls/pillars/boxes/pipes cross-fade out while the stars + faint far nebulae (drawn before the fading room, so they show THROUGH it) fade in; both bulbs (glass, halo, cord, light) dim to exactly 0 by cosmos 0.9 (their PointLights stay in the scene at intensity 0: no light-count change, no recompile); the shafts and the far glow fade; fog goes deep violet, room light dims. The **floor stays** (it is not in `props.room`): it turns deep violet and, beyond ~5.5–12 m from the action, melts into the dome colour, so contact shadows, the cage and the wrecked corner (with the evidence in it) keep standing on it |
| `lights` | `{ screen, hemi, bulb, bulb2, cornerLight }` multipliers (default 1); `cornerLight: 1` switches the corner bulb's real PointLight on (nicer metal glints in corner close-ups, ~8 % slower, compiles a second program set on first use) |
| `shafts` | light-shaft intensity multiplier (0 hides them) · `dust` mote multiplier |
| `cage: false`, `corner: false` | hide the cage / the whole janitor corner |

### `anchors` (THREE.Vector3, world; live ones update in place every `update`)
`cageCenter` (−1.60, 0.50, 0.02) · `cageInside` (floor of the cage, y 0.04 — Fear's feet go here) · `cageDoor` (doorway
centre on the floor, ≈ (−1.21, 0, 0.25)) · `cageDoorOut` (one step outside the door, ≈ (−0.88, 0, 0.44)) · `cageLatch`
(live: the latch knob, ≈ (−1.43, 0.42, 0.40) — target for the Void's fingertip) · `cageTop` (hanging ring, y ≈ 1.15) ·
`cageTag` (live) · `voidSpot` · `lurkSpot` · `crashSpot` · `fearOutside` · `cornerCenter` (3.9, 0.35, −4.2: frame the
corner on this) · `bulb`, `bulb2` (live glass positions) · `voidLight` (live) · `screenGlow` (a point on the far glow,
for "eyes slide out toward us / the screen") · `rollEnd` (where the rolling bucket stops) · `mopHead`, `bucketHat` (live).

### `props`
`cage`, `cageDoor`, `latch` (lever group), `tag`, **`bucketHat`** (the hat bucket group; origin = its outer bottom centre),
`bucketB` (the rolling one), `wringer`, **`mop`** (group; origin = the clamp, +Y = handle), `broom1`, `broom2`, `spray1`,
`spray2`, `rags[5]`, `sign`, `puddle` (an Object3D: its position / rotation.y / scale (unit-radius blob, local X = long
axis) and `visible` drive the in-floor water shading; the floor reads its matrix right before it is drawn, so hand-placing it
after `update()` works), `drops` (InstancedMesh of splash droplets), `crown` (splash crown mesh), `corner` (group), `room`
(group: walls, wainscot, pipes, pillars, boxes, chair — NOT the floor), `floor`, `voidLight`, `bulb`, `bulb2` (PointLights),
`key` (DirectionalLight), `hemi`, `fx`, `fxN`, `fxSky` (the set's own Particles: additive motes / normal dust + debris /
the cosmos sky, drawn first among transparents). `update()` writes the transforms of all corner props every frame — to
hand-place one, do it **after** `set.update()`.

### `timing` (seconds after impact)
`hatLand 0.92` · `wringerFall [0.3, 0.62]` · `splash 0.5` · `puddle [0.5, 2.5]` · `rollDuringCrash [0.33, 2.33]` ·
`signFall 4.6` (+0.62) · `broomSlide 7.2` (+0.75) · `autoSpan 6` (crash-only mode). Crash beats: 0–0.1 the sign is clipped and
skids/spins onto a corner; the body slams the **wringer** back into the corner — it hops and rocks, then (0.3–0.62 s) topples
over sideways ALONG THE BACK WALL toward −X (behind his right hip, mouth turned a little to the room) and the water **gushes**
out: ~30 stretched droplets arc out of the mouth and flatten on the boards, a small spiky crown rises where the gush lands, and
a **puddle** spreads toward the room (darker wet boards, a crisp edge with a thin bright meniscus, a mirrored warm wall and the
bulb's glint, a broad warm wet sheen with a slow ripple — water, not an oil slick); the mop flies out and slaps flat; the corn
broom topples; the hat bucket flies ~1.5 m up, flips 1.5 turns and lands upside down (or on the head); the stool bucket tips,
sheds both spray bottles (one spins end over end through the air and skids) and rolls out; the rags flop; a dust puff +
debris (normal blending, no sparkle); the corner bulb swings on its cord (decaying ~6 s); the push broom wobbles and stays.

### helpers
- `set.cageBar(angleDeg, y)` → world point on the nearest fixed bar (0° = door centre, + toward the hinge side, never
  a door bar) — for Fear gripping bars from inside. Bars are 18° apart; the front facing the default camera is ≈ −60°.
- `set.flightPos(u, apex = 1.15)` → a simple root-position arc for the kicked magician from `lurkSpot` (u 0) to
  `crashSpot` (u 1) — pair with the magician's `extra.kicked`/`flip`, then `crashed`.

## Recipes
- **Opening the cage (s17b02)**: Void at `voidSpot` (it may stand nearer the cage for this beat), `armL: { preset: 'tip',
  target: set.anchors.cageLatch, tip: true, reach }`; key `latch` 0→1 over ~0.8 s, then `cageDoor` 0→1 over ~2 s (SFX
  `cage_creak` under it). Fear inside: `pos: anchors.cageInside`, `yaw: yaws.fearInCage`; grip bars with `cageBar(±40, 0.47)`.
- **Kick → crash (s20b04–b07)**: impact time `Ti`; magician `pos = set.flightPos((t − Tk)/(Ti − Tk))`, then at `crashSpot`
  with `yaw: yaws.magicianCrash`, `extra.crashed`. Set `crash: 1, crashT: t − Ti`, `signOn` ≈ height of his body under the
  sign, `bucketHat: { pos: mag.anchor('headTop'), up: mag.anchor('headUp') }` (lands at 0.92 s: BONK), then `mopWig`
  0→1 over ~0.5 s around 1.1–1.6 s. The sign tips at 4.6 s ("which has been teetering all this time") — or key `signFall`.
  If the magician ends **sitting** (screenplay: "sits in the wreckage... bucket on head, mop on top") the hat is upright and
  the wig drapes naturally; with the headstand pose (`crashed`) pass `mopWig: { blend, pos }` on his hips/feet instead.
  The tipped wringer needs no nudging any more (it falls behind him, along the back wall).
- **The last broom (s21b01)**: key `broomSlide` 0→1 (0.75 s) when you want the off-screen clatter.
- **Lone bucket (s21b04)**: key `rollBucket` 0→1 over 3–5 s; it rolls from the corner along the back wall toward −X, curving
  gently into the room, emerging from behind the Void as seen from Fear's side.
- **"Bucket lifts an inch" (s22b09)**: `bucketHat.lift` 0.075 → 0.11 → 0.075, the bail swings.
- **Cosmos (s22b02)**: key `cosmos` 0→1 over ~2 s (check continuity with a 0→1 sheet at 0.02 steps: no pops); keep
  `crash: 1, crashT: large` so the corner stays wrecked; add the Void's own nebulae/galaxy particles on top.

## Cameras that work (portrait, avoid the Void's 2.2 m body on the diagonal)
- Wide establishing: `framed([-0.5, 1.25, -0.9], { dist: 11, yaw: 6, pitch: 4, fov: 35, screenY: 0.47 })`.
- Cage close: `framed([cage.x, 0.6, cage.z], { dist: 2.4, yaw: 14, fov: 32 })`; latch insert: `framed(cageLatch, { dist: 0.85, yaw: 38 })`.
- Corner medium (crash, wreckage, bucket button): `{ pos: [3.7, 1.45, 1.15], look: [3.65, 0.36, -4.1], fov: 42 }` (looks −Z
  along the right wall, the Void stays out of frame; shows sign, stool, both sprays, hat bucket, wringer). From the room
  diagonal the Void blocks the corner.
- Far corner over everything: `{ pos: [-5.6, 3.1, -2.6], look: [3.7, 0.55, -4.25], fov: 34 }` (from the left wall, high: clears the Void).
- Low side view of the wreck (clearance, puddle): `{ pos: [1.2, 0.75, -2.6], look: [3.95, 0.3, -4.35], fov: 40 }`.
- Layered lurk shot (s18b06): `{ pos: [2.95, 1.55, -2.4], look: [-1.2, 0.8, 0.3], fov: 38 }`.
- Side view of the kick (s20b03): perpendicular to the diagonal, e.g. `{ pos: [6.6, 1.0, 5.8], look: [0.3, 1.45, -0.5] }` —
  outside the (single-sided) right wall: the cutaway hides the right-wall wainscot/pilasters/corner pipe for that render, so
  the room reads cleanly; or inside at `[4.4, 1.0, 3.6]` with fov ≥ 42.
- Reverse / screen of consciousness (s17b01): `{ pos: [-0.9, 1.5, -4.4], look: [-1.6, 1.9, 10], fov: 46 }`.
- Fear's low POV up at the Void: camera at Fear's eye height (0.55) just behind/beside it, fov 50.

## Performance
- `update()` ≈ 0.15–0.19 ms CPU (measured under load). 69–88 draw calls per frame including the shadow pass and post
  (was 102–110), ~80–100k triangles rendered including the shadow pass. One 1024² shadow map (the far key).
- Same-page interleaved A/B (one page holds this set, the PREVIOUS version of the set and `facetest`; 30 rounds, every view
  rendered once per round, trimmed mean; load avg 3–4): `facetest` 0.584 s, empty scene through the same pipeline 0.450 s
  (0.77×), backroom **wide 0.699 (1.20×) · corner 0.678 (1.16×) · crash 0.674 (1.15×) · cosmos 0.744 (1.27×)**; the
  previous version in the same page 0.725 / 0.697 / 0.693 / 0.735. Other runs put the new set 3–11 % ahead of the old one in
  every view. With `facetest` ≈ 0.48 s on an idle machine that is **≈ 0.55–0.57 s/frame** (cosmos ≈ 0.6).
- Where the rest goes (corner view, "hide one thing" A/B): the floor ≈ 40 % of the set's own cost (about half of it shading:
  vertex-lit, 4-tap shadow; the other half plain fill), the props + cage ≈ 30 %, walls ≈ 7 %, the shadow pass ≈ 6 %,
  all transparents ≈ 3 %. The fixed pipeline (MSAA HDR target, bloom, grade, readback) alone is ~0.77× `facetest`, which
  is why a full-frame lit room cannot reach 1.0× `facetest` (a head on a flat background) without baking its lighting.
- What was done for speed: the floor is a Lambert base with **vertex-lit** scene lights on a 0.4 m grid (only the shadow-casting
  far key stays per pixel, with a 4-tap bilinear PCF instead of three's 16-tap kernel and a tight Blinn sheen); the three
  wall planes are vertex-lit too (0.4 m grid); floor texture without anisotropy / trilinear, plaster without mips; the floor
  is drawn after the other opaques (early-z skips what walls/props hide); the 70 m sky dome is drawn only when it shows
  something (camera looking toward +Z or up, or during the cosmos); shafts are 16-sided and frustum-culled; small props
  don't cast the key's shadow and buckets/rags don't receive it (contact shadows instead); each prop's rigid parts are
  merged into one vertex-coloured mesh (buckets, wringer, mop, brooms, sprays, sign panels + feet); room materials are
  opaque (a transparent twin is swapped in only while `cosmos` > 0); walls stop at 5.6 m; the corner bulb's pool is a
  per-pixel fake glow (no 4th light) that also wraps the props.
- Frames are pure functions of `(t, opts)`: verified byte-identical renders out of order (crash and cosmos frames, before and
  after a cutaway frame).

## Known limitations
- The crash is a hand-tuned deterministic choreography (analytic bounces), not physics: props don't collide with
  characters. The defaults assume the magician lands at `crashSpot` and SITS (legs toward the room); the tipped wringer and
  the puddle are placed for that. Tune `signAt` / `signOn` to his final pose. The thrown mop (when it is not used as a wig)
  slaps down in front of him, across where his legs go.
- The mop wig shape is authored for the default hat bucket and an upright-ish head (it reads best when the hat's bottom
  faces up). The bucket's opening is sized for the magician's head (radii 0.11 × 0.17 × 0.13); at the default `lift` (0.075)
  his nose clears under the rim, at `lift` 0 it pokes through the wall.
- The puddle and splash read best within ~2 m of the corner bulb (its fake light makes the wet sheen and the meniscus); from
  the corner medium the magician and the sign hide part of the puddle.
- Galvanized metal picks up the corner bulb through the fake glow; for close-ups the real light (`lights.cornerLight`)
  adds proper per-light glints.
- Cutaway hiding (and the conditional sky dome) relies on `set.scene.onBeforeRender`; a scene that overwrites it without
  chaining loses both.
- Walls and floor are lit per vertex on a 0.4 m grid: a light a scene puts within ~0.3 m of a wall or the floor (a glowing
  prop dragged along the boards) shows a soft diamond pattern; keep such lights a little off the surfaces (the far key's
  shadow, the corner pool, the puddle and the cosmos dissolve are per pixel).
- Default `look.bloomThreshold` is 0.8 (was 0.72) so the brass highlights don't flare next to Fear's eyes; scenes that set
  their own look are unaffected.
