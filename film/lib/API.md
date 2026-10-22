# API.md: the film library for scene and character authors

Everything here is plain Python 3 + cairocffi + numpy + Pillow. Run every command from the
repo root (`/home/user/game1`). Style rules (outlines, shading, scale, eyes, LOD, budget) live
in **STYLE.md**; this file is the reference for *how to call things*. Keep it accurate when you
add to the library: append your module under **Cast**, **Props** or **Environment**.

```python
from film.lib import core, fx, timeline, env, props, storybook
from film.lib import characters as ch               # every creature, auto-registered
from film.lib.characters import base as B           # the shared rig kit (also ch.base)
```

**Conventions.**

* Frames are 1920x1080 at 24 fps, with y growing downward.
* Angles are in radians.
* Colours are float tuples `(r, g, b[, a])` in 0..1, or hex strings (accepted everywhere).
* Time `t` is **local scene seconds**.
* Everything is deterministic: seed randomness with `core.hash01`, `random.Random(seed)` or
  numpy `default_rng(seed)`. Never use the wall clock.
* Characters are authored at **scale 1.0 = the heights in STYLE.md §3**. The anchor `(x, y)` is
  the ground point below the pelvis.

---

## 0. A scene in 30 lines

```python
# film/scenes/s6_bench.py   (draw_sky / draw_castle_hill / draw_garden: your static art)
from film.lib import core, fx, timeline as tl
from film.lib import characters as ch

SCENE = 6
L = ch.LIGHTS["dusk"]

def setup():                                    # once per render process: cache static art
    M = dict(w=2100, h=1240, x=-90, y=-80)      # margin so camera moves never show an edge
    return {"sky": fx.Layer(draw_sky, opaque=True, **M),            # full-bleed, back
            "far": fx.Layer(draw_castle_hill, blur=5, res=0.5, **M), # distant = soft (DOF)
            "garden": fx.Layer(draw_garden, blur=1.0, **M),         # mid-ground set, transparent sky
            "light": fx.LightLayer()}

def draw(cr, t, st):                            # one full frame at local time t
    cam = core.Camera.track(t, [(0, core.Camera()), (8, core.Camera.about(960, 600, 1.08))])
    with cam.view(cr, 0.1): st["sky"].paint(cr)
    with cam.view(cr, 0.4): st["far"].paint(cr)
    with cam.view(cr, 1.0):
        st["garden"].paint(cr)
        pose = ch.DragonPose(facing=-1, sit=core.ramp(t, 1.5, 4.0, "inout_sine"),
                             talk=tl.talk(SCENE, t, "MAN"), mood="tired",
                             laugh=core.window(t, 26.8, 29.5, 0.25, 0.8))
        rig = ch.draw_dragon(cr, 1250, 930, 0.9, pose, L, t)
        ch.dragon_embers(cr, t, 26.9, rig)       # the laugh's warm puff
    lc = st["light"].begin()
    with cam.view(lc, 1.0): fx.light_pool(lc, 1100, 950, 500, 90, "#ffcf9a", 0.3)
    fx.post(cr, t, light=st["light"], bloom_strength=0.45, threshold=0.7, grain=0.035, vignette=0.4)
```

`film/build/demo_hero.py` is a complete, timed example frame (S1 look). Read it before your
first scene.

---

## 1. render.py

```
python3 film/render.py --scene 3                 film/build/video/s3.mp4 (video only)
python3 film/render.py --scene 3 --jobs 4        frames split over 4 processes, then concatenated
python3 film/render.py --all --jobs 4            every scene found
python3 film/render.py --scene 3 --preview [--times 0,2.5,10]   film/build/preview/s3_t002.50.png ...
python3 film/render.py --scene 3 --contact       film/build/preview/s3_contact.png (labelled grid)
python3 film/render.py --scene 3 --still 12.5 --out x.png       one frame
python3 film/render.py --scene 3 --frames 0:48   partial video (s3_f0-48.mp4) for testing
python3 film/render.py --sheet [--only dragon,gnome]            character sheets + cast line-up
python3 film/render.py --list                    scenes found, durations, frame counts
```

* **Scene contract.** The scene module is `film/scenes/s{N}_*.py` (found by glob, imported as
  `film.scenes.<name>`). It defines `SCENE = N`, an optional `setup() -> state` (called once
  per process; cache static art here), and `draw(cr, t, state)`. `draw` must fully paint the
  1920x1080 ARGB32 frame, because each frame starts black.
* Video gets exactly `round(duration * 24)` frames. Raw BGRA is piped to ffmpeg
  (`libx264 -crf 16 -preset medium -pix_fmt yuv420p`), and the frame count is verified with
  ffprobe.
* Output prints `avg draw N ms/frame` and the setup time per scene. The budget is
  **≤ 350 ms/frame** average.
* Default `--preview` times are every 2 s, every line start + 0.3 s, and every beat. The
  contact sheet labels each still with the beats and lines active at that time.
* Timing comes from `film/timeline.json`, or the file named by `FILM_TIMELINE`. For testing
  before the real timeline exists:
  `FILM_TIMELINE=film/build/stub_timeline.json python3 film/render.py --scene 3 --preview`.
* **Sheet hooks.** Every module in `film/lib/characters/` with `sheet_items()` (or
  `draw_sheet(cr, w, h)`) gets pages named
  `film/build/preview/character_sheet_<module>_<k>.png`. `film.lib.props` and `film.lib.env`
  are included the same way if they define these hooks. `sheet_items()` returns
  `[B.SheetItem(label, w, h, draw(cr), group)]`. Cells are shelf-packed onto 1920x1080 pages,
  one or more pages per `group`. `draw(cr)` paints the box `(0, 0, w, h)`, and the label is
  printed under it.
* **Line-up.** Every creature module with `lineup()` returning
  `[B.LineupItem(name, draw(cr, x, ground_y, scale), width)]` appears on
  `character_sheet_lineup.png`. All creatures are drawn at one scale against 100 px guides,
  the bench seat line and the planned `CAST_HEIGHTS`, with each one's measured top printed
  under it.

---

## 2. timeline.py: timing truth

```python
tl.scene(3)            # Scene: .id .name .start (global s) .duration .end .frames
tl.line("s3_l4")       # Line: .id .scene .speaker .text .start .end (LOCAL s) .global_start .global_end
                       #       .duration .wav .caption .vo .sung .fx .env (envelope samples) .env_at(t) .raw
tl.beat("s3_hold")     # Beat: .id .scene .t .end (LOCAL s; end may be None) .dur
tl.talk(3, t, "MAN")   # 0..1 mouth openness from the real speech envelope (smoothed, never snaps)
tl.speaking(3, t, "MAN")        # bool
tl.active_line(3, t, "MAN")     # Line or None
tl.lines_in(3, speaker=None)    # [Line] in time order;  tl.beats_in(3) -> [Beat]
tl.has_line(id) / tl.has_beat(id)
tl.word_times("s3_l1") # [(word, t0, t1)] local times, aligned to the envelope (word-by-word reveals)
tl.to_global(3, t) / tl.to_local(3, tg); tl.fps(); tl.total(); tl.cast(); tl.scenes()
tl.reload()            # re-read the file (after tts.py rewrote it)
```

* The speaker ids are `MAN`, `OLD_WOMAN`, `PHARMACIST`, `PHONE`, `BOUNCER` and `CROWD`. Line
  ids are `sN_lK` and beat ids are `sN_<name>` (SPEC §6). Scenes add their own beats as
  constants defined relative to these.
* The real timeline also has scene 0 (the prologue, speaker `BARD`, lyric lines with `.sung`
  True) and a `(laughs)` line `s6_laugh` for MAN, so `talk(6, t, "MAN")` opens his mouth on the
  laugh. Beats with no end have `.end` None and `.dur` 0.
* Stub: `python3 -m film.lib.timeline --stub film/build/stub_timeline.json` (or
  `tl.make_stub(path)`). It mirrors the SPEC
  target times with synthetic envelopes. It refuses to write `film/timeline.json`, which is
  owned by `film/audio/tts.py`. `--info` prints the loaded timeline.

---

## 3. core.py: drawing toolbox

**Surfaces.**

* `frame(w=1920, h=1080) -> (surface, cr)`
* `new_surface(w, h)`
* `new_context(surface, tolerance=0.25)` (round joins and caps)
* `surface_to_pil(s)`, `pil_to_surface(img)`, `save_png(s, path)`
* Constants `W, H, FPS, TAU`

**Colour.**

* `col(c)` converts hex or a tuple to a float tuple. `rgb2hex`, `alpha(c, a)`.
* `mix(a, b, t)`, `shade(c, k)` (toward black), `tint(c, k)` (toward white), `mul(a, b)`,
  `add(a, b, k)`, `luma(c)`, `saturate(c, k)`, `to_hsv` / `from_hsv`, `hue_shift(c, deg)`.
* `src(cr, c, a=None)` sets the source colour.

**Math, easing, animation.**

* `clamp`, `lerp`, `lerp_pt`, `lerp_tuple`, `invlerp`, `remap(x, a0, a1, b0, b1, clamped)`,
  `smoothstep(e0, e1, x)`, `smooth`, `smoother`, `pingpong`, `wrap_angle`, `lerp_angle`,
  `dist`, `angle_to`, `rotate_pt`, `normalize`.
* Easings `linear`, `in_/out_/inout_` × `quad/cubic/sine/back`, `out_elastic`, `in_elastic`. They
  are also in the `EASE` dict, and `ease(name_or_fn, u)` applies one.
* `ramp(t, t0, t1, ease)`: 0 to 1 between t0 and t1.
* `window(t, t0, t1, fade_in, fade_out, ease)`: 0 to 1 to 0.
* `track(t, [(t0, v0), (t1, v1, "out_back"), ...], ease)`: keyframes. Values may be numbers or
  tuples, and the third element is the easing into that key.
* `frames(sec)`.

**Camera.**

* `Camera(x=960, y=540, zoom=1, rot=0)`: `(x, y)` is the world point at the screen centre.
* `Camera.about(fx, fy, zoom)` zooms about a screen point.
* `Camera.track(t, [(t0, cam), (t1, cam, ease)])`, `Camera.lerp(a, b, u)`.
* `cam.shake(t, amp, freq, seed)`, `cam.drift(t, amp, freq, seed)`.
* `with cam.view(cr, parallax):` applies the camera to a layer. Parallax p means pan × p and
  zoom ** p. Sky is 0-0.2, the far town 0.3-0.6, the action plane 1.0, foreground 1.2-1.6.
* `cam.to_screen(x, y, p)`, `cam.to_world(sx, sy, p)`, `cam.scale_at(p)`.
* Helpers: `camera_move(t, t0, t1, a, b)`, `saved(cr)` (context manager), `at(cr, x, y, angle,
  sx, sy)` (context manager), `zoom_about(cr, px, py, z)`.

**Noise.**

* `hash01(i, seed)`, `hash2`, `jitter`, `noise1(x, seed)`, `noise2(x, y, seed)`, `fbm1`, `fbm2`.
* `noise_array(w, h, scale, octaves, seed)`: a float32 array for textures, built in `setup()`.

**Shapes** (each one builds a path; you fill it).

* `circle`, `ellipse(cr, cx, cy, rx, ry, angle)`, `rounded_rect`, `polygon(cr, pts)`,
  `superellipse(cr, cx, cy, rx, ry, n)` (portholes, plaques).
* `smooth_closed(cr, pts, tension)` and `smooth_open(cr, pts, tension, move)`: Catmull-Rom
  curves through the points.
* `spline(pts, n, closed, tension)` returns points. Also `polyline_length` and `resample`.
* `blob(cr, cx, cy, r, wobble, n, seed, t, speed)`: organic shapes such as bushes, clouds and
  bundles.
* `capsule(cr, x0, y0, r0, x1, y1, r1)`.
* `tapered(cr, pts, w0, w1, profile, cap)`: a ribbon along a curve for strands, folds, horns and
  ink.
* `star`, `convex_hull(points)`.

**Gradients.**

* `linear(x0, y0, x1, y1, stops)` and `radial(cx, cy, r, stops, r0, fx, fy)` return patterns.
* `vgrad(cr, x, y, w, h, stops)` and `hgrad(...)` fill a rectangle.
* Stops are `[c0, c1, ...]` or `[(offset, c), ...]`.
* A full-frame radial gradient costs ~45 ms: cache it.

**Text** (cairo toy API with fontconfig fonts).

* Fonts: `SERIF` (Cormorant Garamond), `SERIF_LIGHT`, `SANS` (Inter), `SANS_SEMI`, `HAND`
  (Caveat), `HAND2` (Patrick Hand), `MARKER` (Permanent Marker), `SIGN` (Bebas Neue), `SIGN2`
  (Oswald). In-world signs must look medieval: use `SERIF`, or add an OFL uncial or blackletter
  font (SPEC §2).
* `text(cr, s, x, y, size, family, color, align=left|center|right,
  valign=baseline|middle|top|bottom|cap, spacing, bold, italic, alpha_, outline=(color, w))`
  returns the advance.
* `measure`, `text_path`, `wrap`, `text_block(cr, s, x, y, width, size, ..., line_height)`,
  `rotated_text`, `arc_text(cr, s, cx, cy, radius, size, ..., inside)`.
* `glow_text(cr, s, x, y, size, family, color, glow, radius, glow_alpha, ..., additive=True)`:
  cached blurred glow, ~1-2 ms. Use it for the S3 rune lettering.

---

## 4. fx.py: light, post, particles

**Cached layers.**

* `Layer(draw, w, h, x, y, blur, res, opaque)` renders `draw(cr)` once.
  `.paint(cr, alpha=1, dx=0, dy=0, operator=None)` costs ~3-7 ms full frame.
* `blur` pre-blurs the layer (depth of field). `res=0.5` renders half-res and soft. Use
  `opaque=True` for full-bleed backgrounds.
* `cache_layer(draw, **kw)` is an alias. `blur_surface(surface, radius)` blurs a surface.

**Light shapes.** These are additive by default.

* `glow(cr, x, y, r, color, alpha, additive, core_r, core_alpha)`: cost ~ r² (r100 ≈ 0.9 ms,
  r300 ≈ 7 ms at full resolution).
* `light_pool(cr, x, y, rx, ry, color, alpha)`.
* `light_shaft(cr, x0, y0, x1, y1, w0, w1, color, alpha, soft, fade_start, fade_end)`: ~10 ms
  at full resolution.
* `god_rays(cr, x, y, angle, spread, length, color, t, n, width, alpha, seed, shimmer)`.
* **`LightLayer(res=0.25)`**: a quarter-resolution additive layer for big soft light.
  `lc = L.begin()` gives a cleared context in full-res coordinates. Draw shafts, pools and big
  glows into it (1/16 the cost), then pass it to `post()`/`bloom()` or call `L.composite(cr)`.

**Post** (once per frame, in this order).

* `post(cr, t, light=None, bloom_strength=0, threshold=0.72, bloom_radius=2.0, wide=0,
  grain=0.04, vignette=0.35, vignette_color, bloom_tint)` does light + bloom + vignette + grain
  in ~18 ms.
* Or call the pieces:
  * `bloom(cr, threshold, strength, radius, knee, tint, wide, wide_radius, light)`: ~10 ms.
    Radius is in 1/8-res px.
  * `finish(cr, t, grain, vignette, vignette_color)`: ~6 ms.
  * `grain(cr, t, amount)`, `vignette(cr, strength, color)`.
* Grading:
  * Cheap: `tint(cr, color, alpha)` (OVER), `lift(cr, color, amount)` (ADD),
    `gradient_tint(cr, top, bottom, alpha)`.
  * Expensive: `multiply` and `screen` (~25 ms), `make_lut(...)` + `grade_lut(cr, lut)` (~20 ms).
* Fades go last: `fade(cr, amount, color)` and `fade_alpha(t, duration, fade_in, fade_out)`.
  S1 fades in from black, S8 fades out, and S9 does both.

**Particles.** These are pure functions of `t`, so frames can render in any order.

* `rain(cr, t, rect, n, speed, angle, length, width, color, alpha, seed, wind)`: layer 2-3
  depths.
* `splashes(cr, t, rect, n, size, color, alpha, seed, life)`.
* `dust(cr, t, rect, n, color, alpha, size, seed, drift, twinkle, mask=fn(x, y)->0..1)`.
  `mask` keeps motes inside a light shaft.
* `embers(cr, t, x, y, t0, n, life, spread, rise, color, hot, size, seed, burst, scale, wind, alpha,
  solid=False)`. `solid=True` paints the spark cores opaque (with a small additive halo) so warm
  sparks stay gold in front of a cool-coloured character (additive orange over teal goes white-green).
* `smoke(cr, t, t0, x, y, n, dur, rise, drift, size, color, alpha, seed, scale)`.
* `fireflies(cr, t, rect, n, color, size, seed, alpha, speed, halo)`.
* `crumbs(cr, t, t0, x, y, n, seed, vx, vy, gravity, ground_y, size, ...)` and
  `crumb_landings(t0, x, y, ...)`, which returns `[(x_rest, t_rest)]` for pigeons to peck at.
* `sparkle(cr, x, y, r, color, alpha, angle)`.

---

## 5. characters/: the cast package

```python
from film.lib import characters as ch
ch.draw_dragon(...), ch.DragonPose, ch.Arm         # every module's __all__, re-exported
ch.LIGHTS, ch.Light, ch.Mat, ch.Expr, ch.MOODS, ch.expr, ch.contact_shadow, ch.eye, ch.hand, ...
ch.REGISTRY            # {module_name: module}; ch.IMPORT_ERRORS {name: traceback}
ch.lineup_items()      # every LineupItem, tallest planned first
```

Every module in the package except `base.py` and `_private.py` is imported automatically.
A module that fails to import prints a warning and is skipped (`FILM_STRICT=1` raises
instead), so one broken creature never takes the others down.

**Contract for a creature module** (copy the dragon's structure):

* `__all__` lists public names **prefixed with the creature**: `draw_gnome`, `GnomePose`,
  `GnomeRig`, `GNOME_HEIGHT`, `GNOME_COLORS`, `gnome_mats`. No name may collide with another
  module's.
* Draw function: `draw_<name>(cr, x, y, scale=1.0, pose=None, light=None, t=0.0, detail=None)`
  returns a rig.
  * `(x, y)` is the ground point below the pelvis (or below the seat when sitting).
  * `scale=1.0` gives the STYLE.md §3 height.
  * `light` is a `B.Light`, default `LIGHTS["neutral"]`.
  * `t` drives the idle life: breathing, blinks, tails, cloth.
  * `detail=None` picks the LOD automatically (2/1/0 by on-screen size).
* Pose dataclass: every field optional, with `.with_(**kw)`. Use the same field names as
  `DragonPose` where they apply: `facing, turn, sit, seat_h, walk, phase, lean, head_turn,
  head_tilt, head_nod, look, mood, mood2, mood_mix, talk, smile, laugh, blink, near, far,
  anchor, seed`.
* The rig (returned) holds attach points **in the caller's coordinates**: `head`, `mouth`,
  `nose`, `eyes`, `top`, `chest`, `lap`, `feet`, `seat`, `hand_near` / `hand_far` (a
  `B.HandFrame`), `scale`, `facing`, `yaw`.
* `sheet_items()` and `lineup()` hooks (see render.py). Show a turnaround, expressions,
  gestures with props, and the 8 lights.
* Draw the creature with the `base` kit. Shading, outlines, eyes, hands and secondary motion
  must come from it (STYLE.md).

---

## 6. characters/base.py: the shared rig kit

### Light and materials

* `Light(key, ambient, rim, rim_strength, direction, rim_direction=None, exposure=1, shadow_size=1,
  bounce=None, bounce_strength=0, name)` is a frozen dataclass.
  * `direction` points **toward** the key in screen space (y down).
  * `.with_(**kw)`, `Light.lerp(a, b, u)`, `.rim_dir()`, `.key_dir()`.
* `LIGHTS` presets: `neutral`, `washhouse`, `apothecary`, `street_night`, `tavern`, `square`,
  `dusk`, `golden`, `blue_hour`, `lantern_night`.
* `Mat(base, sss=0, shadow_k=1, sheen=0, line_k=0.55)` is a material. Build one with
  `Mat.of("#hex", sss=0.4)`.
* `palette(light, mat)` (cached) returns a `Palette` with `lit, shadow, line, deep, rim, hi,
  base`. `pal(light, color, **mat_kw)` is a shortcut.

### Paths, outlines, shading

* `Path(cr)` captures the current path (raw, cheap) so it can be reused.
  `p.add(cr, dx=0, dy=0)` re-adds it; `p.extents(cr)` measures it. `capture(cr)` is an alias.
* Builders return `(shape_path, outline_path)`:
  * `smooth_paths(cr, pts, lw, tension)`
  * `hull_paths(cr, pts, lw)`, which returns `(shape, outline, hull_pts)`
  * `ellipse_paths(cr, cx, cy, rx, ry, lw, angle)`
  * `taper_paths(cr, pts, w0, w1, lw, cap, profile)`
  * `tube_paths(cr, pts, radii, lw, samples, tension, cap_start, cap_end)` for limbs, tails and
    necks: one contour, round caps, de-looped joints.
* `offset_closed(pts, d)`, `fill_outlines(cr, [outline_paths], color)` (a union's silhouette
  line), `tube_outline(...)`.
* **`shade(cr, path, mat, light, lw, *, shadow=1, rim=1, outline=True|False|Path, size=None,
  bounce=1, line_color=None, alpha=1)`** is the house recipe (STYLE.md §5). It returns the
  `Palette`.
  * Pass the `outline` Path from a builder (preferred), `True` (stroke-under, for any path) or
  `False` (draw your own union outline first).
  * `size` is the part's thickness (crescent width). The bounce band (lights with `bounce`) is
    drawn only when `size >= BOUNCE_MIN_SIZE` (40).
  * Cost is ~0.2-0.5 ms per part.
* `flat(cr, path, color, lw, line)`: flat fill + thin outline (claws, buttons).
* `detail_line(cr, pts, w, color, alpha, taper)` and **`detail_lines(cr, [pts, ...], w, color,
  alpha, taper)`** for batched tapered ink.
* `occlusion(cr, x, y, rx, ry, color, alpha, clip)`: soft contact darkening.
* `sheen(cr, x, y, rx, ry, angle, alpha)`: a specular dab.
* `outline_under(cr, path, lw, color, exclude)`.
* `device_scale(cr)`, `line_w(cr, lw)`, `local_dir(cr, v)`.
* `LINE = 2.2`, `MIN_LINE_PX = 1.0`, `LINE_GROW = 0.5`.
* **`line_for(line, dev, k=1.0)`** is THE line width for every outlined drawing, in local units:
  `line` at scale 1.0, never under `MIN_LINE_PX` on screen, and in close-ups (zoom > 1) the ink
  thickens at only `LINE_GROW` of the drawing's rate (a 3x close-up gets a 2x line, not a 3x
  marker outline). `dev` = screen px per local unit (`scale * device_scale(cr)`), `k` = local units
  per scale-1 px (1, or `1/SIZE_K`, `1/fit` for calibrated builds). Every rig and prop uses it, and
  `line_w(cr, lw)` applies it inside hold callbacks.

### 3D-lite rigs

Joints live in **body space**: X is the character's left, Y down, Z forward (toward the
camera when facing front).

* `Proj(yaw, elev)`: `p(v) -> (x, y, depth)`, `.xy(v)`, `.depth(v)`,
  `.ellipse(center, a, c) -> (x, y, half_width)`.
  * yaw +1.0 rad is the 3/4 view facing screen-right, -1.0 facing left, 0 the front view.
  * elev ~0.1 makes things nearer the camera sit lower (feet and hems read round).
* `ik3(S, T, l1, l2, pole) -> (elbow, wrist)`: 3D two-bone IK; `pole` is where the elbow
  points. `ik2(sx, sy, tx, ty, l1, l2, bend)` is the 2D version.
* `v_add, v_sub, v_mul, v_dot, v_cross, v_len, v_norm, v_lerp`, `m_rot_x/y/z`, `m_mul`,
  `m_vec`, `M_ID`.
* `tube(...)`, `limb(cr, a, b, c, ra, rb, rc)`.

### Hands (3 fingers + thumb is the house standard)

`hand(cr, x, y, angle, size, pose, mat, light, lw, *, flip=False, claw=None, claw_len, pad=None,
show_palm=False, hold=None, stamp=None, fingers=3, finger_len=1, finger_w=1, thumb=True,
palm_w=1, curl_add=0, knuckles=True, detail=2, hold_behind=False)`

* `(x, y)` is the wrist, `angle` points toward the fingers, `size` is the wrist-to-fingertip
  length, and `pose` is a `HAND_POSES` name: `relaxed, open, flat, fist, point, grip, cup,
  pinch, back, offer`.
* `hold(cr, frame)` draws the held prop **between the palm and the curled fingers**
  (z-correct). The callback's origin is the grip point, +x runs along the fingers, the frame
  is unscaled (1 unit = 1 caller unit) and un-mirrored. For a gravity-aligned prop (a hanging
  bag, a mug) use `cr.rotate(-frame.angle)`.
* `hold_behind=True` draws the prop behind the whole hand instead (a stone held to an ear).
* `stamp(cr)` draws on the back of the hand (the SMILE stamp).
* Returns a `HandFrame(x, y, angle, scale, tips, palm, flip)`: the grip point, the finger
  direction, the hand size, the fingertips and the palm centre, all in caller coordinates.
  Cost is ~1 ms.

### Faces

* `Expr(brow_in, brow_out, brow_y, brow_asym, lid=0.22, lid_bot=0.06, lid_tilt, smile, open,
  mouth="", cheek, pupil=1)`, with `.blend(other, u)` and `.with_(**kw)`.
* `MOODS`: `neutral, tired, sad, lonely, raised, surprised, worried, happy, warm, laugh,
  skeptical, angry, bored, sneer, sigh, kind`. `expr(mood, **overrides)`.
* `eye(cr, cx, cy, rx, ry, light, lw, *, angle, look=(x, y), lid, lid_bot, tilt, outer, blink,
  squint_arc, iris, iris_hi, pupil, pupil_size, pupil_aspect, sclera, skin, iris_size=0.66,
  foreshort, crease, bags, lash, lash_flick, highlight, line, lid_shade, hide_lid)` is THE
  shared eye.
  * `outer=+1` when the outer corner is toward screen-right.
  * `look` moves the iris; the lid follows it.
  * `blink` closes the eye; `squint_arc` turns a closed eye into a happy ^ arc.
* `mouth(cr, x, y, w, light, lw, *, e=Expr, talk=0..1, skin, lip, inside, tongue, teeth,
  upper_teeth, line, angle)`: a generic cartoon mouth (lips, inside, teeth, tongue).
* `brow_shape(x_in, x_out, y, e, side_sign, span)` returns brow points from an `Expr`.

### Secondary motion and ground

* `breathing(t, rate=0.22, seed)` returns -1..1.
* `auto_blink(t, seed, interval=(2.4, 5.2), dur=0.18, double_chance=0.2)` returns 0..1 closure.
* `sway(t, freq, seed)`.
* `spring(t, t0, freq=2.2, damping=0.45)`: a damped settle after an event at t0.
* `wobble(t, t0, freq, decay)`.
* `lagged(f, t, delay)` and `follow(f, t, delay, gain)`.
* `chain(t, n, freq, delay, amp, seed, grow)` returns n per-segment offsets for tails, scarves
  and hood tips.
* `walk_cycle(phase, stride, lift, bob, swing)` returns a `WalkPose`:
  * `feet` holds `[(dz, lift, toe, planted)] * 2`.
  * Also `hip_dy`, `hip_sway`, `lean`, `arms`, `head_bob`, `phase`.
* `contact_shadow(cr, x, y, rx, ry=None, alpha=0.35, color)`.

### Sheets and the cast table

* `SheetItem(label, w, h, draw(cr), group="")`.
* `LineupItem(name, draw(cr, x, ground_y, scale), width)`.
* `CAST_HEIGHTS` (STYLE.md §3) and `BENCH_SEAT_H = 125`.

---

## 7. The hero: `characters/dragon.py`

`rig = ch.draw_dragon(cr, x, y, scale=1.0, pose=None, light=None, t=0.0, detail=None)`

**Scale.**

* At `scale=1.0`, standing, ground to horn tips = `DRAGON_HEIGHT` = **520 px**. The crown is
  488 and the eyes are at 445.
* Seated on the standard bench (`DRAGON_SEAT_H = 125`), the crown is at 390 and the eyes at
  345.
* `(x, y)` is the ground point below his pelvis.
* With `pose.anchor="seat"`, `(x, y)` is the seat point instead: put it on the bench's seat
  surface.
* Build benches with the seat height `seat_h * scale` above the dragon's ground y.

**Cost.**

* ~21 ms at scale 1.0 (seated head-on ~22), ~17-19 ms at 0.67, ~13-14 ms at 0.45 (CPU, this machine).
* Detail drops automatically: detail 2 at ≥ 0.9 on-screen scale, 1 at ≥ 0.55, else 0.

### DragonPose (all fields optional; `pose.with_(**kw)`)

| field | meaning |
|---|---|
| `facing` | +1 3/4 view facing screen-right, -1 facing left, 0 front |
| `turn` | extra body yaw (×0.6 rad) on top of `facing`, continuous: animate it to turn him. Yaw is clamped to ±1.45 rad (near profile), so there are **no back views**: stage exits as profile walks, or let a door or crowd cover him (sheet page 1, bottom row) |
| `sit`, `seat_h` | 0 standing .. 1 seated. **Animate `sit` 0 → 1 to sit down**: hips go down and back, the chest tips forward, the coat swings over the knees, the hands move to the thighs, the feet slide forward at the end. `seat_h` defaults to 125; 72 is the S1 stool |
| `walk`, `phase` | blend into the walk cycle; `phase = ch.dragon_walk_phase(distance_px, scale, facing)` keeps the feet planted |
| `lean`, `hunch` | lean -1 back .. +1 forward; hunch 0 upright .. 1 very hunched (his default 0.45) |
| `head_turn`, `head_tilt`, `head_nod` | head yaw -1..1 relative to the body; roll (rad); nod -1 down .. +1 up |
| `look` | eyes (-1..1, -1..1): +x screen-right, +y down. Looking down lowers the lids |
| `mood`, `mood2`, `mood_mix` | a `MOODS` name or an `Expr`, and a blend toward a second mood |
| `talk` | 0..1 from `timeline.talk(scene, t, "MAN")` |
| `smile` | -1..1 override |
| `laugh` | 0..1: head back, shoulders shake, wings lift, eyes squeeze. Add `dragon_embers` |
| `sigh` | 0..1: deflate, eyes close. Add `dragon_smoke` |
| `blink` | None = automatic, else 0..1 |
| `wings` | -1 drooped (lonely) .. 0 folded .. +1 lifted (happy) |
| `tail_curl`, `tail_swing`, `tail_drag` | tip curl 0..1; sideways sweep -1..1; dragging on the ground 0..1 (S3) |
| `tail_front` | seated: the tail wraps round his left leg and curls in front of the feet (S8) |
| `near`, `far` | `Arm(...)` for the arm nearer / farther from the camera. In the front view `near` is the screen-left arm |
| `damp` | 0..1 rain-soaked coat and scarf (S3) |
| `anchor` | "ground" or "seat" |
| `elev` | camera elevation, default 0.12 |
| `shadow` | draw the contact shadow |
| `seed` | per-instance idle variation |

### Arm(gesture, amt=1, prev="rest", hold=None, stamp=None, target=None, hand=None, phase=0)

* `amt` blends from `prev` into `gesture`. Animate it 0 → 1 for the move; hands travel on an
  arc.
* `target` is an explicit hand target in body space. `hand` overrides the hand pose.
  `phase` is the gesture's own 0..1.

| gesture | use | hand / prop frame |
|---|---|---|
| `rest` | hanging (standing), on the thighs (seated); blends while sitting | relaxed |
| `hand_to_ear` | S3 the speaking stone at his ear | **prop drawn behind the hand** (`hold_behind`); +x points up along the fingers. Make the stone longer than the palm is wide (~70 × 34 units) so both ends show, and draw its glow *after* the dragon at `rig.hand_near` |
| `hand_out_offer` | open palm forward (S7: receiving the bread; seated it reaches over the knees) | offer, palm shown |
| `hold_item` | holding something in front | grip |
| `carry_bag` | S3 the apothecary bag | grip. The bag hangs: `cr.rotate(-frame.angle)` |
| `slide_note` | S2 slides the parchment note | flat |
| `look_at_hand` | S4 looks at the stamped back of his hand | back. `stamp=` draws on it |
| `arms_crossed` | | |
| `hug` | arms open | open, palms shown |
| `toss_crumbs` | S7, `phase` 0..0.55 wind-up, then release | pinch → open. Pair with `fx.crumbs` from `rig.hand_near` |
| `hold_book` | S6 the coloring book. Both arms `hold_book`, `hold=` on one | two-hand prop: the callback is called once at the midpoint between the grips, upright |
| `pockets` | hands in the coat pockets (S5) | hidden |
| `point`, `wave` | `wave` uses `phase` for the wag | |

### DragonRig (all in caller coordinates)

* `hand_near`, `hand_far`: `HandFrame` (`.x .y` grip, `.angle`, `.scale` in px, `.tips`,
  `.palm`).
* `head`, `mouth`, `nose`, `eyes`, `ear_near`, `top`, `chest`, `lap`, `feet`, `seat`.
* `scale`, `facing` (±1), `yaw` (continuous).

Use these to attach things: the stone's glow at `hand_near`, rune text from `ear_near`, smoke
from `nose`, embers from `mouth`, the gnome handing bread to `hand_near`, pigeons at `feet`.

### Effects

* `dragon_smoke(cr, t, t0, rig, scale=None, dur=2.6, alpha=0.5, light_tint=None)`: the sigh
  puff from his nostrils.
* `dragon_embers(cr, t, t0, rig, scale=None, n=34, life=1.9, intensity=1)`: the S6 laugh.
  Warm glow plus golden embers from his mouth; in the front view they fountain out to the
  sides.
* `dragon_stride(scale, facing, turn)`: screen px per walk cycle.
* `dragon_walk_phase(distance_px, scale, facing, turn)`.
* `DRAGON_COLORS`, `dragon_mats()`, `DRAGON_GESTURES` (name → function), `DRAGON_LINE = 2.4`.

### Recipes

```python
# S1: on the too-small stool, wings drooped, glancing over then leaning (stool seat = 72)
p = ch.DragonPose(facing=1, turn=-0.3, sit=1, seat_h=72, hunch=0.9, wings=-1, mood="lonely",
                  head_turn=core.ramp(t, 5.3, 5.8) * 0.5, lean=core.window(t, 7.0, 8.4, 0.3, 0.4) * 0.6,
                  talk=tl.talk(1, t, "MAN"))
# S3: walking in the rain, stone at the ear, bag in the far hand
p = ch.DragonPose(facing=1, walk=1, phase=ch.dragon_walk_phase(x - x0, sc), damp=1, tail_drag=0.8,
                  wings=-0.9, near=ch.Arm("hand_to_ear", hold=props_stone), far=ch.Arm("carry_bag", hold=props_bag))
# S6: sit down on the bench (1.5 -> 4.0 s), later laugh
p = ch.DragonPose(facing=-1, sit=core.ramp(t, 1.5, 3.6, "inout_sine"), laugh=core.window(t, 26.8, 29.6, 0.2, 0.9))
# S7: receive the bread (blend the arm in over 0.6 s)
p = p.with_(near=ch.Arm("hand_out_offer", amt=core.ramp(t, 1.4, 2.0, "inout_sine"), hold=bread if t > 2.0 else None))
# S8: settled, tail curled round the bench
p = ch.DragonPose(facing=0, turn=0.25, sit=1, tail_front=True, mood="kind", wings=0.0)
```

---

## Cast

*(Each creature module adds its section here: file, draw function, pose fields, gestures, rig
attach points, heights at scale 1.0, cost.)*

### Cast A: gnome, elf, lioness, troll, pigeons

Files: `characters/gnome.py`, `elf.py`, `lioness.py`, `troll.py` and `pigeon.py`. Their shared
private helpers live in `characters/_cast_kit.py`, which is not auto-imported. Every public
name is re-exported as `ch.*`.

**Conventions shared by all five** (the same as the dragon's):

* The draw call is `ch.draw_X(cr, x, y, scale=1.0, pose=None, light=None, t=0.0, detail=None)`
  and returns an `XRig`.
  * `(x, y)` is the ground point below the pelvis. For the pigeon it is between the feet.
  * Give characters in the same depth plane the dragon's `scale`, so the `CAST_HEIGHTS` hold.
    The line-up page measures them: gnome 160 (crown) / 175 (with the hood tip), elf 470,
    lioness 450, troll 660, pigeon 43.
* Every pose field is optional, and `pose.with_(**kw)` returns a changed copy.
* Idle life is a pure function of `t`. Breathing, sway, auto-blink (`blink=None`), the hood
  tip, hair, whiskers and the mirror runes all follow it, so pass the scene's local time.
* `talk` (0..1) is the mouth: use `timeline.talk(scene, t, "SPEAKER")`.
* `mood`, `mood2`, `mood_mix` and `smile` use the shared `B.MOODS`. `look=(x, y)` moves the
  irises, each in -1..1.
* Arms use `XArm(gesture, amt=1, prev="rest", hold=None, target=None, screen=None, hand=None, phase=0)`.
  * `near` is the arm on the camera side and `far` is the other one.
  * `amt` blends from the `prev` gesture: animate it from 0 to 1 and the reach arcs.
  * `phase` (0..1) drives the gesture's own motion: tosses, taps, stamps, the till.
  * `hold(cr, frame)` draws a prop in the hand.
    * The frame origin is the grip. Call `cr.rotate(-frame.angle)` to keep a prop upright.
    * The hold callbacks below work in any character's hand.
  * `screen=(x, y)` (caller coordinates) aims the reach at a point on screen. `target=` takes a
    body-space point, and `hand=` overrides the hand pose.
  * **In 3/4 views only the FAR arm reaches toward the side the character faces**, so use the
    far arm for offers.
* Rig points are in caller coordinates:
  * `hand_near` / `hand_far` are `HandFrame`s with `x, y, angle, scale, tips, palm`.
  * Also `head`, `mouth`, `eyes`, `top`, `chest` and `feet`, plus the per-creature points
    below.
* `anchor="seat"` (gnome, elf) puts `(x, y)` on the bench seat instead of the ground.

#### `ch.draw_gnome`: the gnome grandmother (`OLD_WOMAN`), second lead

She is tiny and round. She has a big soft nose, rosy cheeks, round brass spectacles that glint
and a silver bun under a faded-red pointed hood whose long tip flops. She wears a lavender
knitted shawl, a mossy skirt and laced boots, and carries a linen satchel with a round crusty
loaf.

**Size and seating.**

* Standing, the hood crown is `GNOME_HEIGHT` = 160. Like hats, the floppy tip is not counted;
  it adds about 15.
* Seated on the standard bench (`seat_h=125`, which is `GNOME_SEAT_H`):
  * her crown is about 227 and her head centre about 193, level with the seated dragon's elbow
    at the same scale;
  * her boots dangle about 100 above the ground.

**`GnomePose` fields** (beyond the shared ones):

| field | meaning |
|---|---|
| `sit`, `seat_h` | 0 standing .. 1 on a bench of `seat_h`, legs dangling |
| `kick`, `legs_out` | dangling boots swing 0..1; legs stuck straight out (too short for the bench) |
| `walk`, `phase` | waddle; `phase = ch.gnome_walk_phase(distance_px, scale, facing)` |
| `smirk` | 0..1 her one-sided dry-wit smile |
| `laugh` | 0..1 the warm laugh: eyes squeeze to arcs, mouth open, shoulders and hood tip bounce |
| `specs` | 0..1; at 1 the spectacles slide down her nose and she glances OVER them |
| `glint` | `None` gives a glint sweep every ~8 s; 0..1 forces the sweep; -1 never |
| `hood_swing` | extra push on the hood tip (-1..1), on top of its own lag and bounce |
| `satchel`, `satchel_side` | `"loaf"` (it peeks out), `"empty"`, or `None` for no satchel; the side is -1 or +1 |
| `mood` | default `"kind"`; she also uses `"warm"`, `"happy"`, `"skeptical"`, `"sad"` |

**`GnomeArm(..., bread=None, depth=16)`.** Set `bread` to `"loaf"`, `"half"` or `"piece"` to
put her bread in that hand.

| gesture | |
|---|---|
| `rest` | hands folded on her tummy (standing) or resting on her lap (seated) |
| `toss_crumbs` | wind-up until 0.38, flick 0.38–0.55 (crumbs leave at ~0.47), then follow-through, aimed the way she faces |
| `tear_bread` | needs **both arms at the same phase**: grip, crack 0.25–0.5, snaps at 0.5, the halves pull apart. Then switch to `hold_bread` with `bread="half"` |
| `hold_bread` | a piece or half held before her chest |
| `hand_out_offer` | arm out the way she faces, palm up; use the far arm in 3/4, or `screen=` |
| `hand_on_chest`, `reach_satchel`, `pat_bench`, `wave`, `point` | `pat_bench` and `wave` use `phase` |

**`GnomeRig` extras.** `nose`, `lenses` (the lens centres, for flares), `hood_tip`, `lap`,
`seat`, `satchel`, and `bread` (where the loaf snaps during `tear_bread`).

**Bread and crumbs.**

* `ch.gnome_bread(cr, x, y, size=GNOME_LOAF(46), light, state="loaf"|"half"|"piece", angle, crack, face)`
  draws her bread.
* `ch.gnome_bread_hold(state, light, size=46)` returns a `hold` callback for **any** hand. For
  example, the dragon takes the piece with `ch.Arm("hand_out_offer", hold=ch.gnome_bread_hold("piece", L))`.
* `ch.gnome_rig_at(x, y, scale, pose, t)` returns her rig without drawing her. Use it for the
  moment of release (about one draw's cost, so do it in `setup()`).
* `ch.gnome_toss_crumbs(cr, t, t0, rig_at_release, ground_y, n=10, flock=None)` draws the
  crumbs she flicks at `t0`.
  * `ch.gnome_crumb_landings(t0, rig_at_release, ground_y, n)` returns `[(x, t_rest, y)]`, ready
    for `PigeonFlock(crumbs=...)`.
  * Pass that flock as `flock=` and the crumbs it has pecked up vanish.
* `ch.gnome_tear_crumbs(cr, t, t0, rig)` is the little spray when the loaf snaps, with `t0` at
  tear phase 0.5.

#### `ch.draw_elf`: the wash-house stranger (S1, plus tavern and square extras)

She is elegant and aloof. She wears a deep-plum hooded travelling cloak (a hood with a shoulder
cape and a pewter clasp) over a long silver-blue kirtle with an embroidered hem. Pale-gold hair
falls in two curtains, and her long ears poke through the hood with tiny glowing sea-shells in
them. Her half-lidded eyes stay on an enchanted hand-mirror whose runes scroll, and its cold
light falls on her face.

**Size and seating.**

* Standing, the ear tips are at `ELF_HEIGHT` = 470, the hood crown at about 451 and the eyes at
  about 400.
* Seated on a bench of `seat_h` (`ELF_SEAT_H` = 125), her knees are together, her ankles are
  crossed and the kirtle falls to the floor. Her crown is then about 348, and the mirror glass
  is about 228 above the ground.

**`ElfPose` extras.**

| field | meaning |
|---|---|
| `sit`, `seat_h` | 0 standing .. 1 seated |
| `glow` | 0..1 the mirror's light on her face (use 1 while she holds it) |
| `scroll` | rune scroll speed of the mirror |
| `shells` | 0..1 glow of the ear-shells |
| `hood` | 1 up, 0 down (hair shows) |
| `mood` | default `"bored"` (aloof); try `"skeptical"` for the raised glance |

**Gestures.**

| gesture | |
|---|---|
| `mirror` | the mirror held up before her chest. It draws `ch.elf_mirror` by default; `phase` is her idle thumb |
| `tap_sign` | reaches back over her shoulder and taps twice over `phase`. Put `screen=` on the plaque. Use the **far** arm; it draws behind her |
| `point`, `rest` | |

**Rig extras.** `mirror` (the glass centre, for the scene's `fx.glow` light spill) and
`shells`.

**The mirror itself.** `ch.elf_mirror(cr, frame, t, light, glow=1, size=1, scroll=1)` is also a
hold callback. It is a pewter oval with a finial on a short handle, with runes and mist
drifting in the glowing glass. The glass centre sits `44*size` above the grip.

#### `ch.draw_lioness`: the kind apothecary (`PHARMACIST`, S2)

She has tawny fur, a pale muzzle, round ears and a tufted tail. She wears an apothecary-green
robe, a cream bib-apron with lavender in the pocket, a cream collar with a rose ribbon, and gold
half-moon spectacles on a beaded chain. She looks OVER them and reads THROUGH them.

**Size and counter.** Her ear tips are at `LIONESS_HEIGHT` = 450 and her eyes at about 400.
Build the S2 counter to `LIONESS_COUNTER_H` = 200 (`pose.counter_h`). Her paws rest on it, and
items are set down on it.

**`LionessPose` extras.**

| field | meaning |
|---|---|
| `walk`, `phase` | glide along the shelves; `phase = ch.lioness_walk_phase(distance_px, scale, facing)` |
| `specs` | 0 low on the muzzle (looking over them) .. 1 pushed up (reading through them) |
| `freeze` | 0..1 stops her idle motion: the held beat of the frozen smile |
| `whisker` | 0..1 whisker twitch |
| `tail_swing` | -1..1 |
| `counter_h` | the counter height (default 200) |
| `head_nod` | `s2_nod` |

**Gestures.**

| gesture | |
|---|---|
| `rest` | paws loosely clasped before her apron |
| `on_counter` | both paws on the counter top |
| `reach_up` | reaches to a high shelf (`screen=` the jar), grip hand |
| `place` | carries the item at her chest, sets it down at phase 0.55, then opens her paw and draws back. Use `hold=` for the item |
| `hold_note` | one paw pinches the `hold=` prop (a note) before her chest |
| `read_note` | both arms. Pass the note callback as `hold=` on either arm. It is drawn upright between the paws, which pinch its lower edge, and `rig.note` is its centre |
| `present` | "Try these": an open palm toward the pile |
| `ring_till` | the paw lifts and presses the key down at phase 0.45, then bounces |
| `point` | |

**Rig extras.** `nose` and `note`.

#### `ch.draw_troll`: the stone troll bouncer (`BOUNCER`, S4)

He is a boulder on small legs. Huge mossy shoulder mounds hunch past a low, heavy-browed head.
He has tiny bored eyes, a stone nose, an underbite with tusks, cracks and lichen, a leather
jerkin laced across his chest and rough breeches. The wooden SMILE stamp disappears in his fist.

**Size.** The top of his silhouette (the mossy crown, in 3/4) is `TROLL_HEIGHT` = 660, his eyes
are at about 575 and his chest at about 365. At scale 0.6 he stands about 400 px tall.

**`TrollPose` extras.**

| field | meaning |
|---|---|
| `look` | his tiny eyes slide sideways (`look=(-0.6, 0.2)` = the side-eye) |
| `talk` | a slow, flat jaw |
| `shrug` | 0..1 |
| `mood` | default `"bored"` |

**Gestures.**

| gesture | |
|---|---|
| `rest` | knuckles by his knees |
| `arms_crossed` | both arms |
| `hold_up_stamp` | the stamp raised beside his shoulder like a torch |
| `press_stamp` | raise (and rise a little), then **slam at phase 0.5** -- he lunges his whole bulk into it -- with a wobble, hold until 0.75, then lift and settle back. `screen=` is where the DIE FACE lands (e.g. the dragon's `hand_near.palm`): the aim is solved through the real fist geometry, so `rig.stamp_face` is exactly where the die is. He must stand within reach: anchors at most ~530 × scale px apart, facing each other (farther and the die falls short; check `rig.stamp_face`) |
| `belt` | fists at his belt |
| `thumb` | a jerk of the thumb over his shoulder |

Both stamp gestures draw `ch.troll_stamp` unless `hold=` is given. It is a carved wooden stamp
with SMILE cut in mirror-writing and pink ink.

**Rig extras.** `stamp_face` is where the die is, so the scene can add the thunk and the ink.

#### `ch.draw_pigeon` and `ch.PigeonFlock`: plump grey pigeons (S6–S8)

They are blue-grey with iridescent green and purple necks, two dark wing bars and coral feet.
They are drawn in profile (`facing` ±1) and only the head turns. At scale 1.0 a pigeon is
`PIGEON_HEIGHT` = 42.

**`PigeonPose` fields.**

| field | meaning |
|---|---|
| `walk`, `phase` | head-bobbing walk; one cycle covers `ch.pigeon_stride(scale)` px |
| `peck` | 0..1 cycle; the beak reaches the ground |
| `hop` | 0..1 |
| `flap` | 0..1 wings up, with `lift` px off the ground (takeoff-lite) |
| `fly` | 0..1 open wings, airborne |
| `look` | the SWIVEL, in screen terms: -1 beak to screen-left, 0 at the camera, +1 screen-right; `None` = straight ahead |
| `tilt`, `puff`, `blink`, `seed` | |

**`ch.PigeonFlock(n=6, x_range, y_range, seed, scale, crumbs=[(x, t_land[, y])], arrivals=[(t, side)], t_end=40)`.**

* The birds are placed deterministically and schedule themselves, first come first served.
  They idle, bob, peck, hop and flap now and then, walk to each crumb as it lands and peck it
  up. Birds listed in `arrivals` fly in and land.
* `flock.draw(cr, t, light, look=None, sync=1.0)` is a pure function of `t`. Farther birds
  (smaller y) are drawn first and slightly smaller.
* `look=±1` with `sync=1` is the **S6 synchronized head swivel**: every bird on the ground turns
  its head together. Peckers look up, walkers keep walking with their heads turned, and birds
  in the air don't join. `sync<1` lets only some of them join, chosen deterministically per
  bird.
* `flock.crumb_eaten(k, t)`, `flock.states(t)` → `[(x, y, PigeonPose, scale)]`.

#### Recipes (tested against the stub timeline)

```python
L = ch.LIGHTS
# S1 wash-house: the elf scrolling on the bench; at 8.3 she taps the plaque without looking up
p = ch.ElfPose(facing=-1, sit=1.0, glow=1.0, look=(0.1, 0.9), head_nod=-0.5,
               near=ch.ElfArm("mirror", phase=t * 0.3),
               far=ch.ElfArm("tap_sign", amt=core.ramp(t, 8.3, 8.7, "inout_sine"),
                             phase=core.ramp(t, 8.3, 11.0), screen=plaque_xy))
rig = ch.draw_elf(cr, x, ground_y, 0.9, p, L["washhouse"], t)
fx.glow(cr, *rig.mirror, 60 * 0.9, "#5fe0ff", 0.35)            # the mirror's light spill

# S2 apothecary: set the jars down (s2_items), the frozen smile (s2_pause), the till (s2_ring 23.3)
p = ch.LionessPose(facing=-1, talk=timeline.talk(2, t, "PHARMACIST"),
                   near=ch.LionessArm("place", phase=((t - 8.0) / 1.5) % 1.0, hold=jar),
                   far=ch.LionessArm("on_counter"))
p = p.with_(smile=0.6, freeze=1.0, whisker=1.0, near=ch.LionessArm("on_counter"))
p = p.with_(near=ch.LionessArm("ring_till", phase=core.ramp(t, 23.3 - 0.45, 24.3)))  # key down at 23.3
rig = ch.draw_lioness(cr, x, ground_y, 0.95, p, L["apothecary"], t)

# S4 tavern door: the troll stamps the dragon's hand (slam = phase 0.5 = s4_stamp 3.0)
# the BACK of his hand up (hand="back"): the stamp goes on the back of the hand (SPEC S4)
dragon = ch.draw_dragon(cr, dx, ground_y, 0.6, ch.DragonPose(facing=1, near=ch.Arm("hand_out_offer", hand="back")),
                        L["tavern"], t)
p = ch.TrollPose(facing=-1, look=(-0.6, 0.2), talk=timeline.talk(4, t, "BOUNCER"),
                 near=ch.TrollArm("press_stamp", phase=core.ramp(t, 2.5, 3.5), screen=dragon.hand_near.palm))
rig = ch.draw_troll(cr, dx + 530 * 0.6, ground_y, 0.6, p, L["tavern"], t)   # rig.stamp_face: the thunk + ink
# from s4_stamp on: near=ch.Arm(..., stamp=P.smile_stamp(ink=0.9)) prints SMILE on the back of his hand

# S6 bench: crumbs tossed at 5.0 (set up once), the pigeons come, the heads swivel to the speaker
rel = ch.gnome_rig_at(gx, ground_y, 0.95, ch.GnomePose(facing=-1, sit=1.0,
                      near=ch.GnomeArm("toss_crumbs", phase=0.47, bread="piece")), 5.0)
flock = ch.PigeonFlock(n=6, x_range=(560, 1350), y_range=(ground_y + 15, ground_y + 70), seed=3,
                       scale=0.95, crumbs=ch.gnome_crumb_landings(5.0, rel, ground_y + 10))
gp = ch.GnomePose(facing=-1, sit=1.0, talk=timeline.talk(6, t, "OLD_WOMAN"),
                  specs=core.ramp(t, 12.6, 12.9) * (1 - core.ramp(t, 13.4, 13.8)),     # s6_glance
                  laugh=core.ramp(t, 26.8, 27.1))                                       # s6_laugh
ch.draw_gnome(cr, gx, ground_y, 0.95, gp, L["dusk"], t)
ch.gnome_toss_crumbs(cr, t, 5.0, rel, ground_y + 10, flock=flock)
who = 1.0 if timeline.speaking(6, t, "OLD_WOMAN") else -1.0 if timeline.speaking(6, t, "MAN") else None
flock.draw(cr, t, L["dusk"], look=who, sync=1.0)

# S7: tear the loaf (s7_tear 0.8, snaps at 1.3), offer a piece with the FAR arm (s7_hand 1.8)
tear = core.ramp(t, 0.8, 1.8)
arms = (dict(near=ch.GnomeArm("tear_bread", phase=tear), far=ch.GnomeArm("tear_bread", phase=tear)) if t < 1.8 else
        dict(near=ch.GnomeArm("hold_bread", bread="half"),
             far=ch.GnomeArm("hand_out_offer", amt=core.ramp(t, 1.8, 2.4, "inout_sine"), bread="piece")))
rig = ch.draw_gnome(cr, gx, ground_y, 0.95, ch.GnomePose(facing=-1, sit=1.0, mood="warm", **arms), L["dusk"], t)
ch.gnome_tear_crumbs(cr, t, 1.3, rig)
# ...and from then on the dragon's hand holds her bread: hold=ch.gnome_bread_hold("piece", L["dusk"])
```

#### Cost

All figures are CPU per draw, measured against the dragon at the same time on this loaded
machine and scaled to the dragon's ~21 ms nominal.

| creature | cost |
|---|---|
| gnome | ~8–9 ms at 0.9–1.0, seated with busy hands in dusk light; ~5.5 ms at 0.5 |
| elf | ~7–7.5 ms at 0.9, seated with the mirror; ~5 ms at 0.5 |
| lioness | ~7.5 ms at 0.9 (~8 when reading the note); ~6 ms at 0.6 walking |
| troll | ~7.5–8 ms at 0.6; ~6.5 ms at 0.4 |
| pigeon | ~0.9 ms each; a flock of 8 is ~7.5 ms |

* Lights with a ground bounce (dusk, golden, street_night) cost a little more than neutral.
* Only the big ground-touching cloth (her skirt) draws the bounce band.
* Detail drops on its own below 0.9 and below 0.55 on-screen scale.

**New base-kit helpers** (added to `base.py` for this cast; existing signatures unchanged):

* `B.ellipsoid_pts(project, c, rx, ry, rz, n=10)` returns the silhouette points of a 3D
  ellipsoid through any projection, for hull unions.
* `B.sheet_bg(cr, w, h, light="neutral", floor=None)` and `B.SHEET_BG` give sheet cells a
  backdrop in a light's colours.

### Cast B: orc, minotaur, faun, dwarf, griffin, pixie, crowd extras, scrying crystal

Files are `characters/orc.py`, `minotaur.py`, `faun.py`, `dwarf.py`, `griffin.py`, `pixie.py`
and `crowd.py`. They share the private rig `characters/_folk.py`, which is not auto-imported
and adds nothing to `base.py`. Everything is re-exported by `film.lib.characters` (`ch.`).

#### Common to every Cast-B creature

* **Signature.**
  `draw_<name>(cr, x, y, scale=1.0, pose=None, light=None, t=0.0, detail=None, parts=None)`
  returns a rig.
  * `(x, y)` is the ground point under the pelvis (or under the seat when sitting).
  * The pixie and the griffin use the same anchor: the ground under her, the ground under his
    hips.
* **Scale.** `scale=1.0` matches `CAST_HEIGHTS`, measured on the lineup with hats excluded.
  Each build carries a `fit` factor, so do not fudge the scale per character. Seat and table
  heights stay in screen px: `seat_h=125` sits on the standard bench at any scale.
* **Detail.** `detail=None` chooses the level of detail from the creature's **on-screen
  height**, not from its scale (`_folk.lod_for`):
  * detail 2 at 420 px or taller,
  * detail 1 at 300 px or taller,
  * otherwise detail 0, which uses flat-lit mitten hands, `eye_lite` eyes and no rim pass.
  A goblin at scale 1 is 260 px tall, so it draws as detail 0.
* **Pose.** Every Pose extends `FolkPose`. Its fields are the `DragonPose` names, plus:
  * `facing=±2` and an explicit `yaw` (rad). These creatures have **back views**.
  * `stance` (-1..1): fighting stance.
  * Every field is optional; use `.with_(**kw)`.
* **Arms.** `near=` and `far=` take `ch.Arm(gesture, amt, prev, hold, stamp, target, hand,
  phase)`, the same class as the dragon's. Shared gestures:
  * `rest`, `slump`, `guard`, `shove` (`phase`; aimed by `pose.shove_y`), `stagger`, `hug`,
    `cheer` (`phase` pumps)
  * `raise_crystal_film` / `raise_crystal`, `lower_crystal`
  * `tankard` / `hold_tankard` (`phase` 0..1 raises a toast)
  * `offer` / `hand_out_offer`, `reach` / `take` (`phase` 0..1 extends), `point`, `wave`,
    `talk`, `arms_crossed`
  * `on_table` (`pose.table_h`), `knees`, `strap`, `drag`, `hand_on_chest`
  * `eat` (`phase` 0 lap .. 1 mouth), `hip` / `hand_on_hip`
* **Layers.** `parts` takes any of `"back"`, `"body"`, `"mid"`, `"head"` and `"front"`. Use it
  to interleave two creatures; see `draw_brawl`.
* **Rig.** All points are in caller coordinates:
  * `head`, `mouth`, `nose`, `eyes`, `top`, `chest`, `lap`, `feet`, `seat`
  * `hand_near` and `hand_far` (`HandFrame`)
  * `scale`, `facing`, `yaw`, and the per-creature `points{}` listed below
* **Walking.** `walk=1, phase=ch.<name>_walk_phase(distance_px, scale, yaw)` keeps the feet
  planted.
* **Life.** Every creature breathes, blinks, sways and does its own idle business: tail
  flicks, ear twitches, a wing flutter, a beard sway.

#### Heights at scale 1.0, seat heights and cost (CPU, min of 12 runs, `square` light)

Costs depend on the machine and its load.

| creature | height (px) | seated | cost per draw |
|---|---|---|---|
| orc | 480 | bench 125 | 12.8 ms at 1.0; 6.4 ms at 0.6 (288 px, detail 0) |
| minotaur | 600 (horn tips) | bench 125 | 15.6 ms at 1.0; 12.0 ms at 0.6 |
| `draw_brawl` (the pair) | | | 24 ms at 0.8 |
| faun | 410 (horns) | bench 125: hooves on the ground | 14.7 ms at 1.0; 14.0 ms seated at 0.9 |
| dwarf | 300 (cap excluded, about 320 with it) | bench 125: **boots dangle** | 8.7 ms at 1.0 (detail 1) |
| griffin | 380 sitting on his haunches (ear tufts; cap excluded) | sits on the ground beside the bench | 15.4 ms |
| pixie | 90 (spikes and ears; wings extra) | hovers | 9.7 ms at 2.4; 5.2 ms at 1.0 |
| crowd extra | `CAST_HEIGHTS[kind]` | `sit_table` seat 70 | 5-6.5 ms below 300 px; 9.5-11.6 ms at 300-420 px; 10.7-13 ms at 450 px. The minotaur variant is 7.7 / 13.7 / 16 ms |

For comparison, the hero dragon costs 21 ms at 1.0. Crowd figures include the crystal and its
glow.

#### Orc: `ch.draw_orc`, `ch.OrcPose`, `ch.draw_brawl`, `ch.brawl_state`

The orc is green, with tusks, a black mohawk crest, a laced red leather jerkin
(`ORC_COLORS["jerkin"]`), fur-cuffed boots and iron bracers.

`OrcPose` adds these fields to `FolkPose`:

* `snarl`: 0..1, bares the tusks.
* `ears`: -1 flat .. +1 perked.
* `hug_reach`, `hug_w`, `hug_d`, `hug_y`, `hug_y_far`: the hug partner's torso. `draw_brawl`
  sets them.

```python
# S5, the whole beat in one call: shoves (orc, minotaur, orc, ...), the stop at 8.5, the hug at
# 9.6, the minotaur's slow hug back 11 -> 15, rocking, still holding on at 22-25.
o_rig, m_rig = ch.draw_brawl(cr, cx, ground_y, 0.8, ch.LIGHTS["square"], t,
                             t_stop=tl.beat("s5_stop").t, t_hug=tl.beat("s5_hug").t, hug_back=(11.0, 15.0),
                             orc_left=True)
st = ch.brawl_state(t)    # plain numbers: fight, shover, shove_index, phase, impact, orc_shove / mino_shove,
                          # orc_stagger / mino_stagger, orc_x / mino_x (body px from the pair centre), stop, hug, hug_back, step
```

* `draw_brawl` interleaves the two creatures' layers. In the hug, the orc's face rests on the
  minotaur's chest with his eyes closed, the minotaur's head bows over him, and his far arm
  goes over the orc's shoulder while the near one goes under it.
* Use `brawl_state` for sound cues: a cheer on each new `shove_index`, silence at `stop`.
* Alone: `ch.OrcPose(facing=1, stance=0.6, snarl=0.6, mood="angry", near=ch.Arm("shove", phase=u))`.

#### Minotaur: `ch.draw_minotaur`, `ch.MinotaurPose`

The minotaur has big ivory horns with dark tips, a grey hooded tunic (the hood hangs down his
back), a brass-buckled belt, wrapped shins, cloven hooves and a tufted tail.

`MinotaurPose` adds:

* `shove_y`: aim the shove at a shorter opponent's chest.
* `tail_swing`.
* `variant`: one of `MINOTAUR_VARIANTS`: chestnut, black, dun or brindle.
* The `hug_*` fields, as for the orc.

There is an extra gesture, `Arm("surprised")`: hands up, stunned (S5 9.6-11).
`rig.points["horn_tips"]` holds the horn tips.

#### Faun (S7 teen): `ch.draw_faun`, `ch.FaunPose`

The teen faun is gangly. He has goat legs, small horns through a **red wool hood**
(`FAUN_COLORS["hood"]`) with a dagged capelet, a patched tunic, a rope belt, a satchel and a
**wooden reed-pipe on a cord**. He wears no headphones.

`FaunPose` adds:

* `hood`: 1 up, 0 pushed back. When the hood is pushed back his hair and ears show.
* `ears`.

Extra gestures:

* `Arm("neck_rub")`: the shy hesitation.
* `Arm("pipe")`: fiddles with the pipe.
* `Arm("reach", phase=, hold=bread)`: takes the bread.
* `Arm("eat", phase=)`.

```python
p = ch.FaunPose(facing=-1, walk=1 - core.ramp(t, 5.8, 6.6), phase=ch.faun_walk_phase(x0 - x, sc),
                look=(-0.6, 0.1), mood="worried", near=ch.Arm("neck_rub", amt=core.window(t, 7.0, 9.0, 0.3, 0.4)))
p = ch.FaunPose(facing=1, turn=-0.2, sit=core.ramp(t, 9.8, 10.8, "inout_sine"), mood="warm",
                near=ch.Arm("reach", phase=core.ramp(t, 11.0, 11.8), hold=bread))
```

#### Dwarf (S7 worker): `ch.draw_dwarf`, `ch.DwarfPose`, `ch.dwarf_grip`

The dwarf is stout. He wears an **orange-brown tanned-leather work vest** with brass buckles
and tool loops (hammer, tongs) over a slate tunic. He has a braided beard with brass rings,
soot smudges, and a miner's leather cap with a brass candle-holder and candle.

`DwarfPose` adds:

* `drag` (0..1): he leans back with his heels dug in.
* `grip` (fwd, height): the bench end he holds.
* `lamp_lit`: a tiny warm flame; use it in S8.
* `soot`.
* `palette`: colour overrides.
* `cap`.

`rig.points["grip"]` (while dragging) and `rig.points["lamp"]` (the flame, for a glow) are set.

```python
# S7 15.5-18.0: he drags the second bench (walking backwards: phase decreases with distance)
p = ch.DwarfPose(facing=-1, drag=1, walk=1, phase=-ch.dwarf_walk_phase(dist, sc),
                 near=ch.Arm("drag"), far=ch.Arm("drag"), mood="angry", talk=0.3)
gx, gy = ch.dwarf_grip(p, sc)          # draw the bench's near end at (x + gx, y + gy)
```

Seated on the standard bench, his boots dangle, and that is intended.

#### Griffin (S7 courier): `ch.draw_griffin`, `ch.GriffinPose`

The griffin has an eagle head and a lion body. He wears a royal-post blue felt cap with a
badge and a quill feather, and carries a leather parcel satchel with a red wax seal. His eyes
droop.

`GriffinPose` is its own dataclass and has no arms. Its fields:

* `sit`: 0 on four legs .. 1 on his haunches. Animate it; the front talons stay planted.
* `walk`, `phase`: `phase` comes from `ch.griffin_walk_phase(distance_px, scale, facing, turn)`.
* `yawn` (0..1): the big droopy yawn, with the wings stretching.
* `beak_open`.
* `beak_hold=cb`: a mouthful held in the beak. The callback is `cb(cr, frame)`, drawn over
  the mandibles at the gape near the tip.
  * The frame origin is the gape. +x runs along the head's left-right axis; do not undo
    `frame.angle`.
  * 1 unit = 1 body px. Draw a piece about 40-60 px wide.
* `talon=ch.Arm("reach", phase=, hold=cb)`: the near front talon lifts and takes it (it is a
  `base.hand` with claws).
* `wings`: -1..1.
* `tail_curl`.
* `cap`, `satchel`.
* The usual head, look and mood fields. The default mood is `"tired"`.

Rig points: `rig.points["beak"]` (hand him bread there), `["satchel"]`, `["seal"]`, and
`rig.hand_near` (the talon, while reaching).

#### Pixie (S5, speaker CROWD): `ch.draw_pixie`, `ch.PixiePose`, `ch.pixie_wing_buzz`

The pixie is tiny and lilac, with long pointed ears, a spiky magenta crop
(`PIXIE_COLORS["hair"]`), sneering green eyes and a leaf tunic with a petal collar. She has
four dragonfly wings, and each one is a fan of three translucent blurred copies with a speed
arc. The buzz never stops.

`PixiePose` adds:

* `hover`: feet above the ground anchor, in body px. Its `bob` is automatic.
* `buzz`: 0..1. At 0 the wings are spread and still (lineup).
* The default is `mood="sneer"`, `head_nod=0.12`, so she looks down her nose.
* Use `far=ch.Arm("hip")` for attitude.
* Her `raise_crystal_film` holds the crystal high and out beside her big head.
* Her lines are finer than the cast standard (0.8 × LINE), and her face uses 0.6 of that.

Her LOD follows on-screen height: detail 2 at 220 px or taller, detail 1 at 110 px or taller.

```python
hold = ch.crystal_hold(face=-1.0 if facing_us else 1.0, size=1.7, thumb=feed, t=t)
p = ch.PixiePose(facing=-1, hover=150, talk=tl.talk(5, t, "CROWD"), far=ch.Arm("hip"),
                 near=ch.Arm("lower_crystal" if t > 13.0 else "raise_crystal_film",
                             amt=core.ramp(t, 13.0, 13.6), prev="raise_crystal_film", hold=hold))
rig = ch.draw_pixie(cr, x, ground_y, 1.6, p, ch.LIGHTS["square"], t)
```

When a held crystal draws, the pixie paints its cold glow over her face and sets
`rig.points["crystal"]`. `rig.points["wings"]` is the wing root.

#### Crowd extras: `ch.random_creature`, `ch.crowd_pose`, `ch.draw_crowd`

```python
spec = ch.random_creature(seed)              # deterministic; or random_creature(seed, "goblin")
pose = ch.crowd_pose(action, t, spec, facing=0, turn=0.3, amount=1.0, thumb=feed, glow=1.0)
rig  = ch.draw_crowd(cr, x, ground_y, scale, spec, pose, ch.LIGHTS["square"], t)
```

**Kinds** (`CROWD_KINDS`): dwarf, goblin, kobold, satyr, elf, harpy and minotaur.
* `random_creature` picks a kind with weights 5, 6, 5, 3, 4, 2 and 1, so minotaurs are rare.
* The minotaur is the real rig in a `MINOTAUR_VARIANTS` colour.
* A `CrowdSpec` (kind, seed, size 0.92-1.08, skin, cloth, cloth2, hair, accent, eye, hat,
  beard, ears, horns, variant) is plain data. Edit it freely, e.g. `spec.hat = "hood"`.
* Hats are `""`, `"hood"` or `"cap"` (a soft pointed felt cap). Hooded elves' long ears come out
  through the hood. Skins are creature tones (granite-ruddy dwarves with stone flecks, moon-pale /
  lilac elves) and hose are earthy wool, so no extra reads as a human. Dwarves always have beards
  (with a brass ring); satyrs have one 70 % of the
  time.

**Actions** (`CROWD_ACTIONS`, the first argument of `crowd_pose`):

| action | what it does | knobs |
|---|---|---|
| `idle` | weight shifts, seeded glances | |
| `cheer` | an arm pumps (both arms for some seeds), shouting | `amount` |
| `film` | `raise_crystal_film`: the crystal is held up beside the face. When the extra faces us we see the crystal's back and its cold glow lights the face; when it faces away we see the face with the reflected fight. A red recording rune pulses | `thumb`, `glow` |
| `lower` | `lower_crystal`: the crystal comes down to the belly and dims, the head drops, the mood turns bored | `amount` (stagger it per extra: "one by one") |
| `turn_away` | the yaw swings toward 180° as `amount` goes to 1, eyes on the lowered crystal (S5 18.8: the circle dissolves) | `amount` |
| `laugh` | **the synchronized laugh**: `laugh_sync(t)` gives everyone with the same `t` the identical pulse. Tankard raised on the beat | |
| `tankard` | a tankard at the chest, a slow toast now and then | |
| `sit_table` | seated (`seat_h=70` by default), forearms on a table at `table_h=150` | `seat_h=`, `table_h=` |
| `talk` | leans in and talks, with an explaining hand | `amount` |

* `crowd_pose(...)` keyword arguments override any `CrowdPose` field, e.g. `facing`, `yaw`,
  `mood`, `seed`.
* `draw_crowd` paints a held crystal's glow by itself and returns `rig.points["crystal"]`.

```python
# S5: a ring of 14 filming extras; the crystals lower one by one 10.8 -> 13.0, then they turn away
feed = ch.crystal_feed(lambda c, w, h: ch.draw_brawl(c, w / 2, h - 4, 0.11, ch.LIGHTS["square"], t), 96, 72)
for i, (x, y, sc) in enumerate(ring):
    spec = ch.random_creature(500 + i)
    k = core.ramp(t, 10.8 + 0.15 * i, 11.6 + 0.15 * i)                 # this extra lowers
    act = "film" if k <= 0 else "lower" if t < 18.8 else "turn_away"
    amt = k if act == "lower" else core.ramp(t, 18.8 + 0.1 * i, 20.0 + 0.1 * i) if act == "turn_away" else 1.0
    ch.draw_crowd(cr, x, y, sc, spec, ch.crowd_pose(act, t, spec, facing=1 if x < cx else -1, amount=amt, thumb=feed),
                  ch.LIGHTS["square"], t)
# S4: the tavern laugh -- identical rhythm because everyone gets the same t
ch.draw_crowd(cr, x, y, sc, spec, ch.crowd_pose("laugh", t, spec, facing=0), ch.LIGHTS["tavern"], t)
```

`laugh_sync(t, bpm=280, t0=0)` returns 0.55..1. Use it to pulse the laugh sound at the same
beat.

#### Scrying crystal, tankard and feed

```python
c = ch.draw_scrying_crystal(cr, x, y, size=1.0, angle=0.0, light=None, *, face=1.0, glow=1.0, rec=True,
                            t=0.0, thumb=None, handle=True, detail=2, lw=None)
```

* It is a long hexagonal crystal slab in a brass collar on a short wooden handle, like a
  hand-mirror.
* `(x, y)` is the grip and the crystal stands above it. At size 1 it is 62 px tall.
* `face`:
  * +1: the scrying face, with the reflected scene `thumb(cr, w, h)` clipped and tinted cold.
  * -1: the back, cold facets.
  * In between it turns edge-on.
* `glow` (0..1) dims it.
* `rec` is a tiny pulsing red rune sigil: a medieval "recording" rune, not a dot.
* It returns the centre.

The other helpers:

* `ch.crystal_hold(face, glow, rec, thumb, size, t, tilt, light)` returns a `CrystalHold`, a
  hold callback for any `Arm(hold=...)`.
  * The crystal is about 1.45 hand lengths tall × `size`.
  * Call `.light(cr, strength=1)` afterwards to paint its cold glow. `draw_crowd` and
    `draw_pixie` do this themselves; for other creatures call it after drawing them.
* `ch.crystal_feed(draw_fn, w=96, h=72)` renders the reflected fight **once per frame** into
  a small surface. Every crystal's face then paints it as one image. `ch.demo_thumb` is a
  stand-in.
* `ch.draw_tankard(cr, x, y, size=1.0, light, foam=1.0, slosh=0.0)`: a pewter tankard with
  foam, 34 px tall at size 1.
* `ch.tankard_hold(foam, size, light, slosh)`: its hold callback.

#### Shared helpers in `_folk.py` (private; for Cast-B modules)

* `dome_cap(q, P, D, c, r, h, mat, size, extra=())`: a cap drawn so its back never paints over the face
  (`extra`: more head-space hull points, e.g. a felt cap's peak)
  when the head tips back. The dwarf, crowd caps and the dwarf hair dome use it.
* `mitten(...)` and `eye_lite(...)`: the detail-0 hands and eyes.
* `lod_for(dev, height)`: the on-screen-height level of detail.
* `Build.fit`: the scale calibration.

## Props

File: `film/lib/props.py` (`from film.lib import props as P`).

Sheets:

* `python3 film/render.py --sheet --only props` (7 pages).
* `python3 film/build/props_env_showcase.py` writes four files to `film/build/preview/`:
  * `props_sheet.png`: every prop, its states, in hands, at film scale;
  * `env_sheet.png`;
  * two composed frames, `showcase_street_rain.png` (S3) and `showcase_dusk_garden.png` (S6).
* Pass `props`, `env`, `street` or `garden` to build one of them. The two frames are written
  like scenes (`setup()` + `draw(cr, t, st)`): read them as worked examples.

The props are every recurring object in the film, in the house style and the period (SPEC
§0.1):

* materials: slate, parchment, glass, brass, oak and wrought iron;
* light: candles, the moon and caged wisps;
* storybook lettering throughout;
* nothing electric, plastic or printed.

```python
L = ch.LIGHTS["street_night"]                                   # S3: the walk home
amp = tl.talk(3, t, "PHONE")
pose = ch.DragonPose(facing=1, walk=1, phase=ph, damp=1.0, mood="sad",
                     near=ch.Arm("hand_to_ear", hold=P.stone_hold(L, "pulsing", amp, t)),
                     far=ch.Arm("carry_bag", hold=P.bag_hold(L, t, 0.1 * math.sin(ph * math.tau), damp=1.0)))
rig = ch.draw_dragon(cr, x, ground_y, 0.62, pose, L, t)
lvl = P.stone_level("pulsing", amp, t)
P.stone_glow(cr, rig.hand_near.x, rig.hand_near.y, 0.62, lvl, t)       # after him
# ... and on the light pass:  P.stone_light(lc, rig.hand_near.x, rig.hand_near.y, 0.62, lvl)
```

### Conventions

* **Call shape.** `P.draw_<prop>(cr, x, y, scale=1.0, light=None, t=0.0, ..., detail=None)`.
  * Units are px at scale 1.0, the cast's scale (the dragon stands 520). Give a prop the scale
    of whoever uses it.
  * `light` is a `B.Light`. Pass the scene's preset (the default is `LIGHTS["neutral"]`).
  * `detail=None` picks the level of detail from the on-screen size, like the cast: 2 at
    ≥ 0.9, 1 at ≥ 0.55, else 0. Line widths never drop below STYLE's minimum.
  * Anything that moves is a pure function of `t` (and `seed`).
* **Outlines.** Props a character touches get the dilated-fill outline and `B.shade`:
  * the stone, the sack, the note, the remedies and the book;
  * the bread, the stamp and the tankard;
  * the till, the benches, the stool and the plaque.

  Set dressing has no outline, like the environment: shelves, tables, lantern posts and
  strings, wisp lamps, drums and hanging signs.
* **Returns.**
  * Most calls return a `P.PropRig` of attach points in the caller's coordinates, read as
    attributes (e.g. `rig.mouth`).
  * Seats return a `P.BenchRig`.
  * A lantern string returns a list.
* **Holding.** `P.<prop>_hold(...)` returns a hold callback for `Arm(..., hold=cb)` on any
  creature.
  * Its frame is the grip: +x runs along the fingers, and 1 unit is 1 px at the holder's scale
    1.0.
  * Most callbacks keep the prop upright in a turning hand (`upright=True`, `die_down=True`),
    and the sack hangs plumb. `note_hold` defaults to `upright=False`, so the note turns with
    the fingers.
* **Light on the world.** `P.<prop>_light(lc, ...)` paints a prop's light onto the world: lamp
  halos, pools on the ground, the stone's cold glow on his face.
  * Call it on `st["light"].begin()`, inside the same camera view.
  * Do this before `fx.post(cr, t, light=...)`.
* **Colours and lettering.**
  * `P.PROP_COLORS` holds hex colours; `P.prop_mats()` holds the matching `B.Mat`s, keyed the
    same way.
  * In-world lettering: `P.FONTS.label` (IM FELL English SC), `.text` (IM FELL English),
    `.sign` (Uncial Antiqua) and `.hand` (Caveat).
  * The "digits" on the stone and the till are Cistercian numerals: real medieval digits that
    read as runes.

### Hand props

| prop | draw call | anchor | size at scale 1.0 | hold callback |
|---|---|---|---|---|
| speaking stone | `draw_speaking_stone` | centre, long axis on +x | 70 × 34 | `stone_hold` |
| apothecary sack | `draw_apothecary_bag` | grip on the tied neck | 64 × 100 | `bag_hold` |
| note | `draw_note` | centre (the fold line) | 80 × 50 open, 80 × 25 folded | `note_hold` |
| SLEEP DRAUGHT | `draw_sleep_draught` | bottom centre | 50 × 81 | `remedy_hold("sleep")` |
| VITAMINS | `draw_vitamins` | bottom centre | 48 × 62 | `remedy_hold("vitamins")` |
| CALM candle | `draw_calm_candle` | bottom centre | 47 × 53, flame +16 | `remedy_hold("calm")` |
| coloring book | `draw_coloring_book` | centre (open: middle of the spine) | 64 × 72 per page, 128 wide open | `book_hold` |
| bread | `draw_bread` | centre | diameter `size`, 46 (`LOAF`) | `bread_hold` |
| stamp | `draw_stamp` | middle of the die's face | 60 × 54 | `stamp_hold` |
| SMILE print | `draw_smile_mark` | centre | 64 × 30 | `smile_stamp` (a `stamp=` callback) |
| tankard | `draw_tankard` | bottom centre | 38 (+16 handle) × 50 (+ foam) | `tankard_hold` |

The sizes are also constants: `STONE_W/H`, `BAG_W/H`, `NOTE_W/H`, `BOOK_W/H`, `LOAF`, and
`REMEDIES` = {name: (w, h)}.

#### The speaking stone (the "phone", S3 onward)

```python
rig = P.draw_speaking_stone(cr, x, y, scale, light, t, angle=0.0, state="idle", amp=0.0,
                            pressed=None, face="front")    # -> PropRig(center, mouth, level, glow_r)
```

* It is a palm-sized slate pebble.
  * The front (`face="front"`) has nine carved rune keys (Cistercian 1–9) and a spiral "mouth"
    at its +x end that pulses with the voice. `pressed` (1..9) lights a key.
  * The back (`face="back"`) is one big carved spiral. This is the side that shows round his
    hand.
  * A band of small runes round the edge glows cold cyan when the stone is awake.
* `P.stone_level(state, amp, t)` returns the glow, 0..1. `state` is one of:
  * `"off"`;
  * `"idle"`: a slow, faint breathing;
  * `"active"`: lit, with a gentle shimmer;
  * `"pulsing"`: follows `amp`, e.g. `tl.talk(3, t, "PHONE")`;
  * a number, used as the level.
* `P.stone_hold(light, state, amp, t, pressed, face="back")` is the callback for the dragon's
  `hand_to_ear`. The stone is drawn **behind** his hand; its ends and its glow show past the
  palm.
* **After** drawing the character, call
  `P.stone_glow(cr, rig.hand_near.x, rig.hand_near.y, scale, level, t)`: a cyan halo and rising
  rune motes.
* On the light pass, call `P.stone_light(lc, x, y, scale, level)`: the cold spill on his face.
* Two pieces of the S3 hold loop:
  * `P.draw_hourglass(cr, x, y, scale, light, t, period=4, flip_time=0.6, glow=1,
    label="on hold")`: 34 × 56 plus a ribbon, anchored at its centre. It flips over every
    `period` seconds.
  * `P.draw_music_note(cr, x, y, size, t, color, alpha, kind, angle, glow)`: a medieval
    mensural note, anchored at its head, ~14 × 38. `kind` is `"minim"`, `"semiminim"` or
    `"fusa"`.

#### The apothecary's sack (S2, S3, S6)

```python
rig = P.draw_apothecary_bag(cr, x, y, scale, light, t, angle=0.0, state="tied", swing=0.0,
                            damp=0.0)                       # -> PropRig(grip, bottom, mouth)
```

* It is stiff white paper gathered at the neck and tied with twine, with the green cross
  block-printed on its belly (SPEC S2, S3).
* It hangs along +y from the grip. The paper ruff rises 14 above the grip and the bottom is 87
  below it.
* `state="open"` (S6) unties it: the coloring book and the SLEEP DRAUGHT peek out.
* `damp` (0..1, the S3 rain) greys and spots it.
* `P.bag_hold(light, t, swing, state, damp)` is the callback for `carry_bag`.
  * The sack hangs plumb from the fist whatever the hand's angle.
  * Swing it with `swing = 0.1 * math.sin(walk_phase * math.tau)`.

#### The note (S2)

```python
rig = P.draw_note(cr, x, y, scale, light, t, angle=0.0, unfold=1.0,
                  text=P.NOTE_TEXT)                         # -> PropRig(center, top, bottom)
```

* It is a parchment slip, handwritten in iron-gall ink: "Something for / loneliness?".
* `unfold` runs from 0 (folded in half) to 1 (open flat). The flap is edge-on at 0.5; animate
  it for the reveal.
* For the S2 insert, draw it at scale 5–7.
* `P.note_hold(light, t, unfold=0, angle=0, upright=False)` is the callback for `slide_note`
  and `hold_item`.

#### The remedies (the S2 pile, the S6 sack)

* The three remedies:
  * `P.draw_sleep_draught(...)`: a round blue flask, corked and sealed with midnight wax, with
    a parchment label and a crescent moon.
  * `P.draw_vitamins(..., glow=1)`: a squat jar of softly glowing berry-pills under a linen
    cover.
  * `P.draw_calm_candle(..., lit=1, flame="cool")`: a lavender candle in a glass tumbler.
    * `lit=0` shows a dark wick and a thread of smoke.
    * `flame="cool"` is a pale lavender spell-flame: the remedies are stones, not kindness.
      `"warm"` is an ordinary flame.
    * Paint its halo with `P.candle_glow(cr, rig, scale, t, flame, strength)`.
* All three:
  * stand on their bottom centre;
  * take `label=True`;
  * return `PropRig(top, center, label)`, and the candle adds `flame`.
* `P.draw_remedy(cr, name, x, y, ...)` dispatches on `name`: `"sleep"`, `"vitamins"`, `"calm"`,
  `"book"` (the coloring book lying flat) or `"book_up"` (standing, cover out).
* `P.remedy_hold(name, light, t, upright=True)` puts one in any hand (the lioness's `place`).
* `P.pile_layout(n)` returns `[(name, dx, dy)]`: offsets from the pile's bottom centre for the
  first `n` items of the absurdly neat S2 pile, in the order she sets them down. Draw them in
  that order.
* **The labels read from an on-screen scale of about 1.5** (an item ~120 px tall). Stage the
  S2 beat where the words matter as a push-in or an insert.

#### The coloring book (S2, S6)

```python
P.draw_coloring_book(cr, x, y, scale, light, t, angle=0.0, state="closed", flip=0.0, page=0,
                     colored=0.0)
```

* It is MINDFUL COLORING FOR ADULTS: parchment covers with a rose-window mandala.
* `state`:
  * `"closed"`: the front cover;
  * `"back"`: the back cover;
  * `"open"`: two line-art pages;
  * `"flat"`: lying on a counter, 66 × ~22, anchored at the centre of its top face.
* `flip` (0..1, open only) turns the right-hand page over to the left.
* `page` picks the mandalas.
* `colored` (0..1) fills a few petals: someone tried.
* `P.book_hold(light, t, state="open", flip, page, colored)` is the callback for the dragon's
  two-hand `hold_book`. The open book faces the camera between his grips.

#### Bread (S6–S8)

```python
rig = P.draw_bread(cr, x, y, size=P.LOAF, light=L, t=t, angle=0.0, state="loaf", face=1.0,
                   tear=0.0, seed=0, scale=1.0)          # -> PropRig(center, top, tear)
```

* It is a golden boule with three scored ears and a dusting of flour.
* `size` is its diameter at scale 1.0. `LOAF` = 46 is the gnome's loaf; a piece is about 0.45
  of it.
* `state`:
  * `"loaf"`: `tear` (0..1) pulls it into two halves with strands of crumb;
  * `"half"`: a torn half, its fluffy face turned toward `face` (+1 = +x);
  * `"piece"`: a torn chunk, varied by `seed`;
  * `"crumb"`.
* `P.bread_hold(state="piece", light, size, face, seed, upright=True, rest="palm")` puts bread
  in any hand.
  * `rest="palm"` sits it on an open palm (`hand_out_offer`).
  * `rest="grip"` closes the hand round it.
* `P.draw_crumbs(cr, pts, scale, light, seed, size=3)` draws crumbs lying still. For crumbs in
  flight use `fx.crumbs`; for the pigeons' landing spots use `fx.crumb_landings`.
* The gnome draws her own loaf through `GnomeArm(bread=...)`. These calls are for everyone
  else.

#### The SMILE stamp (S4)

* `P.draw_stamp(cr, x, y, scale, light, t, angle=0, ink=1)` returns `PropRig(die, grip)`.
  * It is a turned oak knob, a block and a felt die wet with pink ink.
  * The anchor is the middle of the die's face.
* `P.stamp_hold(light, t, ink, die_down=True)` holds it by the neck in any hand. The troll's
  `press_stamp` draws his own stamp (`ch.troll_stamp`).
* `P.draw_smile_mark(cr, x, y, scale, angle=-0.12, ink=1, seed=0, text="SMILE", color=None)` is
  the print.
  * SMILE in a double border, slightly rotated and unevenly inked.
  * `ink` fades it; a fresh print is about 0.9.
  * It is a cached mask (~0.1 ms).
* `P.smile_stamp(size=0.52, angle=-0.1, ink=1, seed=0)` is the `stamp=` callback for the
  dragon's `look_at_hand`: the print on the back of his hand.

#### Tankards (S4)

```python
rig = P.draw_tankard(cr, x, y, scale, light, t, kind="wood", foam=1.0, angle=0.0, flip=False,
                     outline=True)                          # -> PropRig(handle, top)
```

* `kind` is `"wood"` (oak staves, iron hoops) or `"pewter"`.
* The handle is on +x; `flip=True` puts it on -x.
* Use `outline=False` for far-away dressing.
* `P.tankard_hold(light, t, kind, foam, side=1, tilt=0)` puts the fist round the handle, with
  the mug upright beside it. `tilt=-0.3` is a toast.
* Cast B's `ch.draw_tankard` (pewter, 34 px at size 1) is the crowd's built-in mug. Use the
  props tankard on tables and in the leads' hands. Don't mix the two in one shot.

### Seats, tables, the till and shelves

**Seats** are built in 3D and projected with `B.Proj(yaw, elev)`, exactly like the cast.

* They turn continuously: yaw 0 is the front view, ±0.5 is 3/4 and ±1.45 is the side view.
* They agree with their sitters at any yaw.

#### The garden bench (S6–S8)

```python
bench = P.draw_garden_bench(cr, x, y, scale, light, t, yaw=0.0, elev=0.12, length=440,
                            seat_h=125, part="all", crumbs=0)        # -> BenchRig
```

* It has oak slats on wrought-iron ends with scrolled arms, and a crest board with quatrefoil
  cut-outs.
* The anchor is the ground point below the middle of the seat.
* Measurements at scale 1.0:
  * The seat top is `BENCH_SEAT_H` = 125 (the same as `B.BENCH_SEAT_H`).
  * The depth is `BENCH_DEPTH` = 84: the front edge is 42 ahead of a sitter's anchor and the
    backrest is 46 behind it.
  * The back top is ~245.
  * The length is `BENCH_LEN` = 440.
* `crumbs=n` scatters `n` crumbs on the seat.
* The `BenchRig` places the sitters:
  * `rig.place(u)` is the **ground anchor** for a sitter at fraction `u` (0 is the bench's left
    end, 1 its right end, each 30 in from the end). Draw the sitter with `pose.sit=1` and
    `seat_h=rig.seat_h`, e.g. `ch.draw_gnome(cr, *rig.place(0.18), sc, pose, L, t)`.
  * `rig.seat(u)` is the point on the seat surface, for `pose.anchor="seat"`.
  * `rig.ends` holds the ground points of the two ends, and `rig.back_top` the top of the
    backrest.
* Draw order:
  1. `part="back"`;
  2. the sitters;
  3. `part="front"`: the near end's front leg and arm.

  In the front view there is no near end, so `"back"` is the whole bench.

#### The stool, the wash-house form and the tavern table

* `P.draw_stool(cr, x, y, scale, light, t, yaw=0.3, elev=0.16, seat_h=72, radius=42,
  part="all", wobble=0)`: the three-legged milking stool, far too small for the dragon (S1).
  * The anchor is the sitter's anchor. The seat top is `STOOL_SEAT_H` = 72.
  * `part="back"` draws two legs and the seat; `part="front"` draws the front leg.
  * `wobble` rocks it, e.g. `B.wobble(t, t_sit) * 0.04` as he sits.
  * It returns `PropRig(seat, ground)`.
* `P.draw_washhouse_bench(cr, x, y, scale, light, t, yaw=0, elev=0.12, length=260,
  seat_h=125)`: the elf's medieval "form" (S1).
  * It is a thick plank on splayed slab ends, 56 deep.
  * It returns a `BenchRig`.
* `P.draw_tavern_table(cr, x, y, scale, light, t, yaw=0, elev=0.28, length=420, depth=110,
  height=115, clutter=True, seed=0)`: a dark-oak trestle table with tankards and a candle stub
  (S4).
  * The anchor is the ground below its middle. The top is 115 up: elbow height for the cast.
  * It returns `PropRig(top_center, top_y)`.

#### The till (S2)

```python
till = P.draw_till(cr, x, y, scale, light, t, ring=None, receipt=0.0, pressed=None,
                   drawer=0.0)                 # -> PropRig(key, bell, slot, receipt_end)
```

* It is an engraved brass cabinet on an oak plinth, with:
  * eight ivory rune keys;
  * a side crank;
  * a bell on a curly bracket;
  * number flags;
  * a parchment receipt.
* The anchor is the bottom centre, on the counter. It is ~136 × 130.
* `ring` is the local time the key went down: the bell rocks and dings, and the flags pop.
* `receipt` (0..1) is how far the strip has curled out. Animate it after the ring.
* `pressed` (1..8) holds a key down.
* `drawer` (0..1) opens the cash drawer.

#### The shelves (S2)

```python
P.draw_shelves(cr, x, y, w=420, h=420, scale=1.0, light=L, t=0.0, rows=4, seed=0, depth=34,
               gaps=(), herbs=True)                   # -> PropRig(boards=[y of each shelf top])
```

* A wall of dark-oak shelves, filled from `seed` with flasks, jars and glazed pots, and dried
  herbs hanging from the top board.
* The anchor is the **top-left**.
* `gaps=[(row, slot)]` leaves those spaces empty: where she took something.
* It costs ~10 ms, so always put it in a Layer.

### Lights, signs and the wash-house (set dressing)

#### Lantern posts

```python
post = P.draw_lantern_post(cr, x, y, scale, light, t, lit=1.0, kind="warm", style="crook",
                           side=1, height=600, seed=0)  # -> PropRig(lamp, flame, top, ground, kind, lit)
```

* A flared foot, a twisted-iron column, and a glass-and-iron lantern with a candle in it.
  `kind="wisp"` cages a cold green-cyan wisp instead.
* The anchor is the foot.
* `style`:
  * `"crook"` hangs the lantern from a scrolled arm on `side` (+1 is right). Its centre is
    ~`height - 50` up.
  * `"top"` sits it on the post's head.
* `lit` (0..1) lights it. Animate it in S7.
* The flame flickers, so draw the post every frame (1.7 ms).
* Its light is `P.lantern_light(lc, rig, scale, t, strength=1, ground_y=None, pool=1)`: a big
  soft halo, plus a pool on the ground when you give `ground_y`.

#### Wisp lamps and lantern strings

* `P.draw_wisp_lamp(cr, x, y, scale, light, t, seed=0, top=None, intensity=1)` returns
  `PropRig(center, level, scale)`.
  * An iron cage on a chain from the vault, with a flickering wisp inside (S1).
  * The anchor is the cage centre; the cage is 40 × 56.
  * The chain runs up to caller-y `top` (default: 220 above).
  * Its light is `P.wisp_light(lc, rig, scale, floor_y, strength)`.
* `P.draw_lantern_string(cr, p0, p1, t, scale, light, n=9, sag=0.16, seed=0,
  palette="tavern", lit=1, swing=1)` returns `[(x, y, colour, level)]`.
  * Candle-lit paper lanterns (~22 × 26) on a swaying cord between the fixings `p0` and `p1`
    (S4).
  * `sag` is a fraction of the span, or px if it is > 1.
  * `palette` is `"tavern"`, `"warm"`, `"cold"` or a list of colours.
  * Its light is `P.lantern_string_light(lc, lanterns, scale, strength)`.

#### Hanging signs and the plaque

* `P.draw_hanging_sign(cr, x, y, kind="apothecary", scale, light, t, side=1, text=None,
  emblem=None, paint=None, ink=None, swing=1, glow=0, seed=0)` returns
  `PropRig(board, emblem, glow)`.
  * A painted board on a scrolled iron wall bracket, rocking gently.
  * `kind`:
    * `"apothecary"`: a cream arch, the green cross, APOTHECARY;
    * `"flagon"`: a burgundy shield, a gold tankard, THE MERRY FLAGON;
    * `"washhouse"`: a blue board, a washtub, WASH-HOUSE;
    * `None`: your own `text=(line1[, line2])`, `emblem` (`"cross"`, `"tankard"` or `"tub"`),
      `paint` and `ink`.
  * The anchor is where the bracket meets the wall. The arm reaches 150 toward `side`, and the
    ~120 × 120 board hangs below it.
  * `glow` lights the emblem from within (S8, small and far away). Add
    `P.sign_light(lc, rig, scale, color, strength)` on the light pass.
* `P.draw_plaque(cr, x, y, text="SELF-SERVICE", scale, light, t, taps=(), swing=0, size=34,
  paint, letter)` returns `PropRig(nail, center, tap_point, size)`.
  * A notched oak board, painted deep green with cream uncial letters, hanging from a nail by a
    cord (S1).
  * The anchor is the **nail**. The board hangs ~22 below it and is ~300 × 74 for
    SELF-SERVICE.
  * `taps` are the times (local s) it was tapped. Each one sets it rocking: the elf's two taps.
  * It is outlined, because it is touched.

#### The tumbling drums (S1)

```python
rig = P.draw_tumbling_drum(cr, x, y, scale, light, t, seed=0, speed=1.0, glow=1.0, rumble=1.0,
                           vp=None, depth=(62, -24))   # -> PropRig(center, radius, glow): the porthole
```

* The S1 "dryer": an oak barrel on its side in a cradle, with brass hoops and staves that turn
  by themselves.
* Its brass lid has a round glass porthole. Behind it a stranger's laundry tumbles, set by each
  drum's own `seed` and `speed`.
* Faint runes breathe on the bezel.
* The anchor is the ground below the lid's centre. The lid radius is `DRUM_R` = 92 and the axle
  is 130 up.
* The barrel recedes by `depth`. Give it a vanishing point `vp` (caller coordinates) instead,
  and a row of drums shares one perspective.
* Its light is `P.drum_light(lc, rig, strength)`.
* `P.drum_body(...)` and `P.drum_porthole(...)` draw the two halves separately, with the same
  arguments, when something must go between them.

### Recipes

These are tested in `props_env_showcase.py` and the sheets.

```python
# S6: two on the bench, a book between his hands; the bench's near end goes over them
bench = P.draw_garden_bench(cr, 1000, 925, 0.78, L, t, part="back")
ch.draw_gnome(cr, *bench.place(0.18), 0.78, ch.GnomePose(facing=1, sit=1.0), L, t)
ch.draw_dragon(cr, *bench.place(0.8), 0.78,
               ch.DragonPose(facing=-1, sit=1.0, near=ch.Arm("hold_book", hold=P.book_hold(L, t, flip=0.3)),
                             far=ch.Arm("hold_book")), L, t)
P.draw_garden_bench(cr, 1000, 925, 0.78, L, t, part="front")

# S2: the pile, then the till rings at 11.2 s and the receipt curls out
for name, dx, dy in P.pile_layout(4):
    P.draw_remedy(cr, name, px + dx * sc, py + dy * sc, sc, La, t)
till = P.draw_till(cr, tx, counter_y, sc, La, t, ring=11.2, receipt=core.ramp(t, 11.5, 13.0))

# S1: a row of drums sharing one vanishing point, their portholes lighting the floor
rigs = [P.draw_tumbling_drum(cr, x, 905, 0.9, Lw, t, seed=i, vp=(1500, 560))
        for i, x in enumerate((420, 760, 1100))]
lc = st["light"].begin()
with cam.view(lc, 1.0):
    for rig in rigs:
        P.drum_light(lc, rig)

# S4: the print on the back of his hand, as he looks at it
pose = ch.DragonPose(near=ch.Arm("look_at_hand", stamp=P.smile_stamp(ink=0.9)), mood="sad")
```

* **Rigs you need in `setup()`.** You may need a rig before the frame, e.g. a lamp position for
  the wet reflections, or the bench for a sitter's layout. Draw the prop once onto a scratch
  surface to get it: `P.draw_garden_bench(core.frame(4, 4)[1], ...)`.
* **Cache whatever doesn't move.** Shelves, tables, a bench nobody shifts, a sign with
  `swing=0`: put them in an `fx.Layer`.

### Cost

CPU per call, at scale 1.0 unless noted (best of 3 × 12 runs).

| call | ms |
|---|---|
| speaking stone (active) / `stone_glow` | 1.9 / 0.4 |
| sack / note (scale 1, scale 5) | 1.3 / 0.6, 1.0 |
| SLEEP DRAUGHT / VITAMINS / CALM | 1.5 / 2.7 / 1.1 |
| coloring book (open) | 6.5 |
| loaf / stamp / SMILE print | 0.8 / 0.7 / 0.1 |
| till | 3.1 |
| garden bench (scale 0.78) / stool / wash-house form | 7.6 / 1.8 / 0.8 |
| lantern post / wisp lamp / lantern string (9) | 1.7 / 1.0 / 2.6 |
| tumbling drum | 5.2 |
| plaque / hanging sign | 1.2 / 0.9 |
| shelves (420 × 420) / tavern table / tankard | 9.9 / 4.3 / 1.0 |
| hourglass / music note | 0.8 / 0.1 |

## Environment

File: `film/lib/env.py` (`from film.lib import env`).

Sheets:

* `python3 film/render.py --sheet --only env` (6 pages);
* `env_sheet.png` from `film/build/props_env_showcase.py` (see **Props**).

The kit paints storybook-medieval backgrounds with **no outlines** (STYLE.md): shapes, value,
colour, texture and blur carry the depth. Backgrounds sit in a narrower value band than the
cast and lose saturation and contrast with distance.

```python
def setup():                                       # S6 at dusk (the showcase's Garden, condensed)
    k = "dusk"
    def far(cr):
        env.draw_castle_hill(cr, 1380, 430, 0.72, kind=k, hill_w=900, hill_h=150, seed=1)
        env.draw_hills(cr, -90, 2100, 640, kind=k, height=(40, 120), seed=2)
    return {"sky": env.layer(lambda cr: env.draw_sky(cr, kind=k, horizon=600, seed=1), blur=3, opaque=True),
            "far": env.layer(far, blur=1.6),
            "garden": env.layer(draw_garden, blur=0.6),      # grass, hedges, path, flower beds
            "tree": env.OakTree(330, 790, 0.62, kind=k, blur=0.8),
            "light": fx.LightLayer()}

def draw(cr, t, st):
    cam = core.Camera.about(980, 640, 1.0)
    with cam.view(cr, 0.1): st["sky"].paint(cr)
    with cam.view(cr, 0.4): st["far"].paint(cr)
    with cam.view(cr, 1.0):
        st["garden"].paint(cr)
        st["tree"].draw(cr, t)                     # the crown sways: ~3 ms
        ...                                        # props, then the cast
```

### Conventions

* Every call takes **world coordinates** (px, y down) and only draws into the context.
* **Cache static art.** Build it in `setup()` with
  `env.layer(fn, blur=0, res=1, opaque=False)`.
  * This is an `fx.Layer` with the standard margin `env.MARGIN` = `dict(w=2100, h=1240,
    x=-90, y=-80)`, so camera moves never show an edge.
  * The layer is drawn as soon as you create it, so anything `fn` returns or collects is ready
    on the next line of `setup()`.
  * Painting a layer costs ~0.5–1.3 ms.
  * A `res=0.5` layer builds faster but paints in ~4.5 ms (a bilinear upscale). Keep it for
    strongly blurred planes.
* **Per-frame pieces** are pure functions of `t`:
  * `StarField.draw`, `OakTree.draw`, `Rain.draw`, `Mist.draw` and `puddle_ripples`;
  * the lantern flames, which live in **Props**.
* **Palettes.** Pass `kind=` to every call: a name in `env.PALETTES` or your own dict.
  `env.palette(kind)` returns the dict.

  | kind | scenes |
  |---|---|
  | `"night"` | S3 dry, S8; stars and a moon |
  | `"rain_night"` | S3; an overcast lid of cloud |
  | `"dusk"` | S6 |
  | `"golden"` | S7 |
  | `"blue_hour"` | S7 later; the first stars |
  | `"evening"` | S5; the cold grey-blue square |
  | `"washhouse"` | S1 |

  * Each palette has these keys: `sky` (stops, top to horizon), `cloud`, `haze`, `far`, `mid`,
    `near`, `ground`, `foliage` (dark, mid, lit), `stone`, `plaster` (three tints), `timber`,
    `roof`, `window`, `window_dark`, `star` and `moon`.
* **Atmosphere.**
  * `env.haze_toward(c, haze, k)` pushes a colour toward the haze (`k` 0 near .. 1 far) and
    desaturates it.
  * `env.draw_haze(cr, x, y, w, h, color, top_alpha=0, bottom_alpha=0.5, additive=False)`
    washes over whatever is already drawn. Use it between planes.
* **Texture.** `env.texture(cr, kind, alpha, scale, angle, offset, sx, sy)` paints a seamless
  granulation over the current clip: the painterly finish on any flat shape.
  * `kind` is `"paint"`, `"plaster"`, `"stone"`, `"foliage"`, `"grain"` or `"wood"`.
  * For wood, try `sx=4, sy=0.25`.
* **Captions.** Keep the bottom 180 px free of anything the eye must read.
* **The period** (SPEC §0.1).
  * Light: candles and the moon only.
  * Materials: wood, plaster, stone and thatch.
  * Windows: leaded diamond panes.
  * Nothing modern.

### Planes and cost

| plane | what | `cam.view` factor | layer | build (ms) |
|---|---|---|---|---|
| sky | `draw_sky`, plus `StarField` per frame | 0.05–0.15 | `blur=2–3, opaque=True` | 53 |
| far | `draw_castle_hill`, `draw_hills`, `draw_roofline`, `draw_haze` | 0.3–0.45 | `blur=1.5–3` | 6 + 100 |
| mid | `draw_street_row`, `draw_vaulted_hall`, hedges, grass | 0.7–1.0 | `blur=0.6–1.5` | 190 / 58 / 83 |
| ground | `draw_cobbles`, `draw_gravel_path`, puddles, reflections | 1.0 | sharp | 320 (the wet street) |
| per frame | `OakTree` 2.8, `Rain` 9.3, `Mist` 1.6, `StarField` 1.3, ripples 0.3 ms | 1.0 | none | |

Whole frames: `showcase_street_rain.png` costs ~100 ms and `showcase_dusk_garden.png` ~90 ms.
Both include the cast and `fx.post`.

### Sky and distance

* `env.draw_sky(cr, x=-90, y=-80, w=2100, h=1240, kind="dusk", horizon=640, seed=0,
  clouds=True, stars=None, moon=None, sun=None, glow=None, texture_alpha=0.05)` paints:
  * the palette's gradient down to `horizon`;
  * a soft glow low on the sun's side;
  * cloud banks, lit from below or from the side;
  * static stars and the moon on clear nights.

  Its options:
  * `stars` and `moon` default to the palette's choice.
  * `moon` can be `(mx, my, r)` or `True`.
  * `sun=(sx, sy, r)` is for golden hour.
  * `glow` overrides the horizon glow's colour.
* `env.StarField(rect, n=120, seed=0, color).draw(cr, t, alpha=1)` draws twinkling stars per
  frame; a few get four-point glints.
* `env.draw_moon(cr, x, y, r, kind="night", glow=0.5)` and
  `env.draw_clouds(cr, x, y, w, h, kind, seed, light_from=None, n=None, alpha=1, streaks=None)`
  are for building a sky by hand.
* **The castle.**
  `env.draw_castle_hill(cr, x, y, scale=1, kind="dusk", seed=0, color=None, rim=None,
  windows=9, window_color=None, window_alpha=None, banners=True, t=0, hill=True, hill_w=1100,
  hill_h=170, road=True, light_dx=-0.6)` draws the kingdom's castle as a distant silhouette:
  * curtain walls, round towers with conical roofs and pennants, and the keep with its spire;
  * a winding road, and lit windows at night;
  * a rim of sky light on the light side (`light_dx` < 0 is the left), with each tower shaded
    as a drum.

  Placing it:
  * The anchor is the castle's foot on the hilltop. The castle is ~360 × 290 at scale 1.
  * The hill (`hill_w` × `hill_h`) has a broad crown the castle stands on. Where the ground
    falls away, its outer walls carry on down into the hill.
  * `hill=False` draws the castle alone, with foundations 64 deep: sink them into a ridge.
* `env.draw_hills(cr, x=-90, w=2100, base_y=760, kind="dusk", layers=3, seed=0,
  height=(70, 190), trees=True, fields=True, bottom=1200, colors=None, light_dx=-0.6,
  rim=True)` draws rolling bands from far (hazy) to near:
  * hedgerows and strips of field follow their contours;
  * copses of round trees and poplars stand along them.

  Its options:
  * Ridges peak about `height[1]` above `base_y` for the far band, and `height[0]` for the near
    one.
  * `colors` sets your own band colours, far to near.
* `env.draw_roofline(cr, x0, x1, y, scale=0.25, kind="night", seed=0, color=None, lit=0.3,
  spire=True, haze=0)` draws a distant town as a roofline: gables, chimneys, a church spire and
  a few tiny lit windows. Use it behind S3's street and for S8's town far away.
* **Mist.**
  * `env.draw_mist(cr, x, y, w, h, color, alpha=0.35, seed=0, scale=2, offset=0)` is a static
    band.
  * `env.Mist(x, y, w, h, color, alpha=0.3, seed=0, speed=8, scale=2).draw(cr, t, alpha=1)`
    drifts (~1.6 ms).

### The town

```python
house = env.draw_house(cr, x, y, w=620, floors=2, scale=1.0, kind="night", seed=0, lit=0.4,
                       roof=None, ground="stone", shutters=None, shop=None, chimney=True,
                       jetty=34, plaster=None, detail=2)        # -> HouseRig
```

* It is a half-timbered house seen face-on.
* The anchor is the **bottom-left** of its ground storey; `w` is its width at scale 1.
* Storeys:
  * The ground storey is `GROUND_H` = 600 tall, stone or timber (`ground="stone"`).
  * Each upper storey is `FLOOR_H` = 520 and jetties out `jetty` per side.
  * `floors` is 1–3.
* `roof`:
  * `"gable"`: the gable end to the street, carved bargeboards and a finial;
  * `"side"`: the eaves to the street, and a dormer;
  * `"thatch"`;
  * `None` picks one by seed.
* The rest:
  * timber framing (posts, braces, crosses);
  * granulated lime plaster, tinted by seed or by `plaster=`;
  * leaded diamond-pane windows, with `shutters` `"open"`, `"closed"` or `None` (by seed);
  * an arched plank door, or a shuttered shop front (`shop` True, False or None).
* `lit` (0..1) is the chance a window is lit, deterministic by seed.
* The `HouseRig` holds:
  * `rect` = (x, y_top, w, h);
  * `windows` = [(cx, cy, w, h, lit)];
  * `door` = (x, y, w, h);
  * `roof_top`;
  * `lights` = [((x, y), colour, level, width)] for the lit windows.
* `env.draw_street_row(cr, x0, x1, ground_y, scale=0.5, kind="night", seed=0, lit=0.4,
  floors=(2, 3), widths=(520, 760), alley=0.25, detail=2)` returns `[HouseRig]`.
  * It is a varied row of houses across a street, with the odd dark alley.
  * Use a scale of 0.35–0.6 behind the cast.

### Stone interiors

* `env.draw_stone_wall(cr, x, y, w, h, kind="washhouse", seed=0, block=(84, 46), color=None,
  mortar=None, texture_alpha=0.16, light_top=0.035, variation=0.08)` lays coursed blocks.
  * Each block is a little different, with a lit top edge and a shadowed foot, set in darker
    mortar.
  * `block` is (typical width, course height).
* `env.draw_arch(cr, cx, base_y, w, h, kind="washhouse", fill=None, depth=24, voussoirs=True,
  color=None, seed=0)` draws a round-headed arch: a window, a door or an arcade bay.
  * `(cx, base_y)` is the middle of its sill.
  * `w` × `h` is the opening; `h` includes the head.
  * `fill` is a colour, a callable `fill(cr)` clipped to the opening, or `None` to leave it
    open.
* `env.draw_vaulted_hall(cr, x=-90, y=-80, w=2100, h=1240, kind="washhouse", seed=0,
  floor_y=700, vp=(900, 520), bays=4, window_fill=None, moon=True)` draws the S1 back wall:
  * an arcade of bays on heavy pillars;
  * tall arched night windows, the moon in one;
  * the ribs of the vault;
  * a flagstone floor in one-point perspective toward `vp`.

  Cache it, with a blur of ~1.5.

### Ground

* `env.draw_cobbles(cr, x, y_top, w, y_bot, kind="night", seed=0, wet=False, size=(9, 44),
  vp=None, color=None, texture_alpha=0.14, sheen=None, contrast=1.0)` lays rows of rounded
  stones. They grow from `size[0]` px tall (far, at `y_top`) to `size[1]` (near, at `y_bot`).
  * Every stone varies in size, shape and tone. Broad patches of the street run lighter or
    darker, and most crowns catch the light.
  * `vp=(vx, vy)` converges the joints to a vanishing point (the town square). `None` keeps the
    rows straight: a street seen from the side (S3).
  * `wet=True` gives darker, glossy stones, water in the joints, glints of sky, and a sheen that
    grows toward the far rows.
  * `contrast` scales the stone-to-stone variation.
* `env.draw_wet_reflections(cr, lights, ground_y=None, stretch=0.85, width=1.0, seed=0,
  alpha=1.0, clip=None)` adds the reflections of the lights.
  * Each light is `(x, y, colour, level[, base_y])`.
  * Each one becomes a long vertical streak of broken glints. It runs down from where its wall
    or post meets the ground (`base_y`, else `ground_y`), as long as the light is high ×
    `stretch`.
  * It is additive. Cache it, and paint the layer with a flickering alpha.
* `env.draw_puddle(cr, x, y, rx, ry, kind="rain_night", seed=0, reflections=(), sky=None,
  rim=True, lights=(), stretch=0.85, stones=True)` draws a rain puddle:
  * a flat sheet of water, darker than the stones round it;
  * a pale sheen along its far edge;
  * a few drowned stone crowns near the edge;
  * crisp reflections.

  Its options:
  * Pass `lights` (and `stretch`) exactly as you gave them to `draw_wet_reflections`. Every
    streak that runs over the puddle continues through it, sharper and brighter: a mirror holds
    the light further out than the stones do.
  * `reflections=[(x, colour, level)]` adds a streak at world x.
  * Keep `ry/rx` near the ground's perspective (the cobbles' aspect, ~0.25–0.5). Very flat
    puddles read as slugs.
* `env.puddle_ripples(cr, t, x, y, rx, ry, n=5, seed=0, color="#cfe0ff", alpha=0.32,
  rate=1.0, squash=None)` animates the rain on a puddle, per frame.
  * Each drop is a bright fleck, then one thin ring that widens and fades.
  * The rings lie on the ground: `squash` defaults to `max(0.35, ry/rx)`.
* `env.draw_gravel_path(cr, pts, widths=(60, 360), kind="dusk", seed=0, color=None,
  edge_tufts=True)` lays a gravel path along the centre line `pts`, far end first.
  * It widens toward us, is speckled light and dark, and its edges are nibbled by grass.
* `env.draw_grass(cr, x, y, w, h, kind="dusk", seed=0, density=1, light_dx=-0.6, color=None,
  flowers=True, blades=True)` paints a meadow lawn; `y` is its far edge.
  * It is finer and hazier at the back, with blade tufts in three tones that grow toward us,
    and tiny wild flowers.
* `env.draw_ground_shadow(cr, x, y, rx, ry, alpha=0.35, color)` is a soft contact shadow for
  posts, benches, trees and carts.

### The garden

* `env.draw_hedge(cr, x, y, w, h, kind="dusk", seed=0, light_dx=-0.6, color=None,
  shadow=True)` draws a clipped box hedge; `(x, y)` is its bottom-left on the ground.
  * It has a bumpy, leafy crown, lit along its top and light side, and darker toward its foot.
* `env.draw_flower_bed(cr, x, y, w, h, kind="dusk", seed=0, colors=None, wattle=True)` draws a
  mound of leafy plants starred with small blooms, behind a woven-willow edging; `(x, y)` is
  its bottom-left.
* **The old oak** stands behind the bench (S6–S8).
  * A stout flared trunk with a knot hole parts into great limbs: two reach out nearly level
    and three climb.
  * Above them is a broad, arched crown of leaf clumps.
  * The anchor is the base of the trunk. At scale 1 it is ~1200 wide × 1030 tall.
  * The crown's underside is ~370 up at its ends and ~520 in the middle, so the limbs show
    under it. That is what makes it read as an oak.
  * Use a scale of 0.45–0.7 behind the bench.

  The two calls:
  * `env.OakTree(x, y, scale=1, kind="dusk", seed=0, light_dx=-0.6, blur=0, sway=1)` caches
    the trunk and each leaf clump in its own small layer (setup ~130 ms).
    `.draw(cr, t, sway=None, alpha=1)` then sways the crown for ~3 ms a frame.
  * `env.draw_oak(cr, x, y, scale, kind, seed, t, sway=0, light_dx, part="all")` draws it
    uncached (~74 ms at 0.62), for sheets and stills. `part` is `"all"`, `"trunk"` or
    `"crown"`.

### Weather

```python
rain = env.Rain(rect=(-90, -80, 2100, 1240), kind="rain_night", density=1.0, angle=0.16, seed=0,
                ground=(830, 1080), color=None, near=True)        # in setup()
rain.draw(cr, t, lights=[(x, y, radius, colour)], alpha=1.0)      # every frame, after the set and the cast
```

* Rain falls in three depths:
  * far: fine and faint;
  * mid;
  * near: long bright streaks.
* Drops splash on the `ground=(y0, y1)` band.
* Drops light up inside each lamp's glow (`lights`).
* It costs ~9 ms at density 1 with two lamps.
* `near=False` drops the closest layer, e.g. for rain seen through a window.

### Recipe: the S3 street at night in the rain

This is `Street` in `film/build/props_env_showcase.py`, condensed.

```python
k, POSTS, PUDDLES = "rain_night", [(470, 905), (1560, 905)], [(800, 1016, 118, 30), (1250, 900, 72, 15)]

def setup():
    st = {"light": fx.LightLayer()}
    st["sky"] = env.layer(lambda cr: env.draw_sky(cr, kind=k, horizon=560, seed=3), blur=3, opaque=True)
    st["far"] = env.layer(lambda cr: (env.draw_castle_hill(cr, 1420, 300, 0.42, kind=k, hill_w=700, hill_h=120),
                                      env.draw_roofline(cr, -100, 2020, 520, 0.2, k, seed=4, haze=0.35)),
                          blur=2.5, res=0.5)
    rows = []
    def houses(cr):
        rows.extend(env.draw_street_row(cr, -120, 2060, 800, 0.43, k, seed=11, lit=0.5))
        env.draw_haze(cr, -90, -80, 2100, 880, env.palette(k)["haze"], 0.38, 0.16)   # into the rain
    st["houses"] = env.layer(houses, blur=1.4)                      # drawn now: `rows` is filled
    lamps = [P.draw_lantern_post(core.frame(4, 4)[1], px, gy, 0.95) for px, gy in POSTS]   # rigs only
    lights = ([(p[0], p[1], c, lv * 0.55, 822) for r in rows for (p, c, lv, w) in r.lights] +
              [(r.lamp[0], r.lamp[1], P.PROP_COLORS["candle"], 1.0, r.ground[1] + 6) for r in lamps])
    st["street"] = env.layer(lambda cr: env.draw_cobbles(cr, -90, 820, 2100, 1160, k, wet=True, size=(6, 34)))
    st["refl"] = env.layer(lambda cr: env.draw_wet_reflections(cr, lights, stretch=0.75, width=1.3, alpha=1.4))
    st["puddles"] = env.layer(lambda cr: [env.draw_puddle(cr, *pd, k, seed=i, lights=lights, stretch=0.75)
                                          for i, pd in enumerate(PUDDLES)])
    st["rain"] = env.Rain(kind=k, ground=(830, 1080), seed=7)
    st["mist"] = env.Mist(-90, 680, 2100, 220, env.palette(k)["haze"], 0.22, seed=3, speed=12)
    return st

def draw(cr, t, st):
    L = ch.LIGHTS["street_night"]
    cam = core.Camera.about(960, 620, 1.0 + 0.004 * t)
    with cam.view(cr, 0.1): st["sky"].paint(cr)
    with cam.view(cr, 0.35): st["far"].paint(cr)
    with cam.view(cr, 1.0):
        st["houses"].paint(cr)
        st["street"].paint(cr)
        st["refl"].paint(cr, alpha=0.85 + 0.15 * (0.5 + 0.5 * core.noise1(t * 6, 4)))   # candle flicker
        st["puddles"].paint(cr)
        for i, pd in enumerate(PUDDLES):
            env.puddle_ripples(cr, t, *pd, seed=i)
        st["mist"].draw(cr, t)
        posts = [P.draw_lantern_post(cr, px, gy, 0.95, L, t, seed=i) for i, (px, gy) in enumerate(POSTS)]
        ...                                                         # the dragon, the stone, the hourglass
        st["rain"].draw(cr, t, lights=[(p.lamp[0], p.lamp[1], 230, "#ffb860") for p in posts])
    lc = st["light"].begin()
    with cam.view(lc, 1.0):
        for p in posts:
            P.lantern_light(lc, p, 0.95, t, ground_y=p.ground[1] + 10)
    fx.post(cr, t, light=st["light"], bloom_strength=0.55, threshold=0.62, grain=0.04, vignette=0.55)
```

## Bard

File: `characters/bard.py`. Every public name is re-exported as `ch.*`. Sheets:
`python3 film/render.py --sheet --only bard` (7 pages) and `python3 film/build/bard_showcase.py`
(`bard_sheet.png`, `storybook_sheet.png`, `prologue_mock.png` in `film/build/preview/`).

THE BARD (speaker `BARD`) frames the film: the prologue (S0), a cameo on the second bench in S8
and the reprise under the end card (S9). He is a plump, twinkly **cockatrice minstrel**:

* a rooster's golden-chestnut head with a floppy red comb and wattles, a cream face mask, big
  bright green eyes, and a short horn-yellow beak that opens to sing;
* a dragon's small leathery green wings and a scaly green tail with a rooster-feather tuft;
* a ruff of hackle feathers, a patched burgundy-and-gold doublet over a round belly, scaly
  yellow hands, chicken feet in soft leather boots;
* a green felt beret with a long white plume pinned by a gold brooch;
* a well-loved **lute** with a ribbed pear-shaped bowl, a carved rose, a bent-back pegbox with
  a red ribbon and 7 strings, played with one of his own quills.

His colours are in `BARD_COLORS` and his materials in `bard_mats()`.

```python
pose = ch.BardPose(sit=1, facing=1, turn=-0.45, look_cam=0.5, **ch.bard_song(t))   # S0
ch.draw_bard_stool(cr, x, ground_y, sc, light, yaw=ch.bard_yaw(pose))              # first
rig = ch.draw_bard(cr, x, ground_y, sc, pose, light, t)
```

### Draw calls

* `ch.draw_bard(cr, x, y, scale=1.0, pose=None, light=None, t=0.0, detail=None)` returns a
  `BardRig`.
  * `(x, y)` is the ground point below his pelvis. With `pose.anchor="seat"` it is the seat
    point instead.
  * Idle life is a pure function of `t`: breathing, auto-blinks, the comb flop, the wattles,
    the plume, the lute ribbon and the tail tuft. Pass the scene's local time.
* `ch.draw_bard_stool(cr, x, y, scale=1.0, light=None, seat_h=28, yaw=0.0, detail=None)` draws
  his three-legged milking stool. It uses the same anchor as the bard.
  * Draw it **before** him, with `yaw=ch.bard_yaw(pose)` so it turns with him.
  * It returns the seat point.
* Light: `ch.BARD_LIGHTS["candle"]` is the prologue's candlelight. It has the same values as
  `storybook.STORY_LIGHT` (they compare equal): a warm key from the candles (screen right), a
  deep plum ambient and a hearth-orange rim from the left. Use `LIGHTS["lantern_night"]` for S8 and any `B.LIGHTS`
  preset elsewhere.

### Heights at scale 1.0 (measured)

| pose | plume top | comb top | eyes | beak |
|---|---|---|---|---|
| standing (`BARD_HEIGHT` = 178) | 178 | 156 | 124 | 109 |
| on his stool (`BARD_STOOL_H` = 28), boots planted | 153 | 142 | 113 | 98 |
| on the standard bench (`B.BENCH_SEAT_H` = 125), boots dangle | 250 | 238 | 209 | 194 |

`CAST_HEIGHTS["bard"]` is 156 (the comb top; hats are not planned). He is the gnome's height plus his comb and plume, about a third of the dragon. In a shared
plane (S8), give him the dragon's scale.

### `BardPose` fields

Every field is optional, and `pose.with_(**kw)` returns a changed copy.

* **Body**
  * `facing` / `turn` work like the dragon's: +1 is 3/4 right, -1 is 3/4 left, 0 is front, and
    `turn` adds yaw (×0.6 rad). The default is front, turned a little right.
    * **Seated, use 3/4: `facing=1, turn=-0.45`.** Then the thighs, the stool legs and the
      draped tail all read. From the front a seated figure reads as standing.
  * `sit` (0..1) and `seat_h` (default 28). `walk` and `phase` drive a strut with a rooster
    head-thrust (`ch.bard_walk_phase(distance_px, scale, facing, turn)`).
  * `lean`, `head_turn`, `head_tilt`, `head_nod`, `look=(x, y)`.
* **Face**
  * `look_cam` (0..1) turns his head and eyes into the lens.
  * `mood` defaults to `"twinkle"`. `BARD_MOODS` adds `twinkle`, `sing`, `rapture`, `listen`
    and `sly`; `base.MOODS` also works. Mix with `mood2` and `mood_mix`; override with `smile`.
  * `wink` (0..1) winks the near eye. `blink=None` is an auto-blink.
* **Voice**
  * `sing` (0..1) opens the beak; `talk` is the same for spoken lines.
  * `vowel` is `"a"`, `"o"`, `"e"` or `"m"` (`m` closes the beak).
  * `rapture` (0..1) is the long-note bliss: his eyes close, his brows lift and his head tips up.
* **The lute**
  * `lute` is `"play"` (in his lap), `"back"` (slung) or `"none"`.
  * The right arm strums and the left arm frets. `right` and `left` are
    `ch.BardArm(gesture, amt=1, prev="play", hold=None, hand=None, target=None, phase=0)`.
    Gestures (`BARD_GESTURES`): `play`, `strum`, `fret`, `rest`, `present` (an open-palm flourish
    toward the story), `wave`, `tip_cap`, `point`.
  * `amt` blends from `prev`, so animate it from 0 to 1 to lift a hand off the lute and back. A
    seated `tip_cap` or `wave` with the right arm leaves the fret hand on the neck.
  * Strum hand: `strum_t` (seconds since the last stroke), `strum_next` (seconds to the next),
    `strum_dir` and `strum_next_dir` (+1 down, -1 up) and `strum_amt` (size).
    * Each stroke has an anticipation wind-up, a 75 ms sweep across the strings, an overshoot
      follow-through and a recovery. When the next stroke goes the same way, the hand lifts
      clear of the strings.
    * The plucked strings vibrate and the body rocks slightly on each stroke.
  * Fret hand: `chord` is an index into `BARD_CHORDS` (7 shapes, one per song chord, see
    `BARD_CHORD_NAMES`: D, G, A, C, Bm, A7, Em). `chord_to` and `chord_mix` slide the hand to
    another shape.
  * `tune` (0..1) puts the fret hand at the pegbox turning a peg while he cocks his head and
    listens. `tune_phase` drives the peg wiggle.
* **Music and secondary motion**
  * `beat` (a continuous beat count) and `groove` (0..1) give the head bob on the beat, the body
    sway, the plume and comb following late, and the left boot's foot tap (`tap` scales it).
  * `wings` runs from -1 (drooped) to +1 (lifted). `tail_curl` and `tail_swing` shape the tail.
* **Cap and misc**
  * `cap` wears the beret. `cap_lift` (0..1) lifts it, for `tip_cap`.
  * `anchor`, `elev` (camera elevation), `shadow` and `seed`.

### `BardRig` (caller coordinates)

* `hand_right` (strum), `hand_left` (fret), `hand_near` and `hand_far` are `HandFrame`s.
* `head`, `mouth` (between the mandibles: song breath, notes, sparkles), `beak` (the tip),
  `eyes`, `top` (beret top), `comb`, `plume_tip`, `chest`, `lap`, `feet`, `seat`.
* `lute` is a dict: `rose`, `bridge`, `nut`, `pegbox`, `center` and `strum` (where the
  strings are hit: put string glints and floating notes here).
* `scale`, `facing`, `yaw`.

### Music helpers: the song drives him

* `ch.bard_song(t, piece="prologue", timing=None, offset=0.0)` returns **every music-driven
  pose field** at song time `t - offset`, read from `film/assets/song/song_timing.json`
  (`ch.bard_song_timing()` loads it once and caches it). `piece` is `"prologue"` or `"reprise"`.
  * **Strums:** every lute stroke.
    * Down and up strums. Bass notes and plucks are alternating quill strokes.
    * Runs, rolls, the flourish and the final chord. Each stroke's size comes from its velocity.
  * **Chords:** the fret hand reaches each new chord 0.16 s early.
  * **Beat:** `beat` and `groove` from the beat grid and the sections (intro 0.35, verses 1.0,
    coda 0.8, outro 0.45).
  * **Tuning:** the tuning gesture over the intro's tuning strokes.
  * **Singing:**
    * `sing` comes from each line's 24 fps envelope.
    * `vowel` comes from the current syllable.
    * `rapture` rises on long notes.
  * Splat it into a pose: `ch.BardPose(sit=1, facing=1, turn=-0.45, **ch.bard_song(t))`. Any
    keyword you give after the splat wins.
  * It costs ~0.01 ms. It returns `{}` if the file is missing.
  * **Staging stays with the scene:** `look_cam`, `wink`, `tip_cap`/`present`, `mood` and the
    camera.
* Without the song file, build the same fields yourself:
  * `ch.bard_beat(t, beats)` gives a continuous beat count.
  * `ch.bard_strum(t, strums, amt=1.0)` takes times (alternating down/up) or `(time, dir)` pairs
    and returns the strum fields.
  * `ch.bard_chord(t, [(time, idx)], slide=0.16)` returns a float. `ch.bard_chords(...)` returns
    `chord`, `chord_to` and `chord_mix`.
  * `ch.bard_sing(t, env_fn)` returns `sing` and `rapture`. Use it with
    `lambda tt: timeline.talk(0, tt, "BARD")`.
* `ch.bard_twinkle(cr, t, t0, rig, scale=None, dur=0.55)` draws the wink's "ting!", a
  four-point sparkle by his winking eye from `t0`. Draw it after him.
* `ch.bard_cameo_pose(t, facing=-1, turn=0.35, period=1.4, seed=0, **kw)` is the S8 cameo:
  * seated on the standard bench, boots dangling, tail hanging;
  * quietly strumming at half size (silent: the score carries the music), slow chord changes;
  * eyes half closed, swaying.
  * Extra keywords override `BardPose` fields.

### Recipes

```python
from film.lib import characters as ch, storybook as sb
L = sb.STORY_LIGHT                                  # == ch.BARD_LIGHTS["candle"]
marks = ch.bard_song_timing()["prologue"]["marks"]  # flourish, vamp, page_turn_v2, coda_look_up,
                                                    # break, final_chord, book_opens, interlude
# S0: the whole prologue performance, staged 3/4 toward the lectern, glancing at us
pose = ch.BardPose(sit=1, facing=1, turn=-0.45, look_cam=0.35, tail_swing=-0.6, **ch.bard_song(t))
# S0 coda: he looks up at us and winks (from the coda_look_up mark), tips his cap on the last line
u = core.smooth((t - marks["coda_look_up"]) / 0.6)
pose = pose.with_(look_cam=max(pose.look_cam, u), mood="sly" if u > 0.5 else pose.mood,
                  wink=core.smooth((t - (marks["coda_look_up"] + 1.2)) / 0.2)
                       * (1 - core.smooth((t - (marks["coda_look_up"] + 1.7)) / 0.2)))
ch.draw_bard_stool(cr, x, floor_y, sc, L, yaw=ch.bard_yaw(pose))
rig = ch.draw_bard(cr, x, floor_y, sc, pose, L, t)
ch.bard_twinkle(cr, t, marks["coda_look_up"] + 1.2, rig)
# S8: among the crowd on the second bench (scale = the dragon's), silent strumming
rig = ch.draw_bard(cr, x, ground_y, sc, ch.bard_cameo_pose(t, facing=-1), L_lantern, t)
# S9 end card (the reprise): bard_song(t - reprise_start, "reprise") if he is shown at all
```

### Cost

CPU per draw on this machine:

| draw | cost |
|---|---|
| `draw_bard`, seated with the lute, scale 3.0 (prologue close shot) | ~42 ms |
| `draw_bard`, scale 1.0 | ~28 ms |
| `draw_bard`, scale 0.5 (cameo) | ~19 ms |
| `draw_bard_stool` | ~1.5 ms |
| `bard_song` | ~0.01 ms |

Detail drops automatically below on-screen scales of 0.9 and 0.55.

## Storybook

File: `film/lib/storybook.py` (`from film.lib import storybook as sb`). This is the prologue's
storybook kit (SPEC 0.2, S0):

* the great book, *The Stone and the Bread*: oxblood calf, brass corners, a gilt title, marbled
  endpapers;
* its illuminated pages: parchment with deckled edges, gold-leaf vine borders, an Uncial drop cap
  "O" with a little castle inside it, the verse in IM FELL italic;
* the living watercolour illustrations;
* a carved oak lectern, beeswax candles, and a stone hearth with a living fire.

Every function is deterministic in `t`. Units are px at scale 1, y down.

```python
book = sb.Book()                                          # PROLOGUE_SPREADS, 150 x 200 pages
lec = sb.draw_lectern(cr, x, floor_y, sc, sb.STORY_LIGHT, book, view=V)   # static: fx.Layer it
rig = sb.draw_book(cr, book, *lec.desk, sc, t, open=o, spread=k, turn=p, light=sb.STORY_LIGHT, view=V)
for i, c in enumerate(lec.candles):
    cd = sb.draw_candle(cr, *c, sc, t + i, sb.STORY_LIGHT, seed=i)   # then glow at cd.flame
```

### The book

* `sb.Book(spreads=PROLOGUE_SPREADS, title="The Stone and the Bread", page_w=150, page_h=200,
  block=12, seed=3)`. At scale 1 the open book is ~325 px across, about twice the bard's
  height.
* `sb.draw_book(cr, book, x, y, scale=1.0, t=0.0, open=1.0, spread=0, turn=0.0, light=None,
  view=0.42, detail=None, shimmer=None, flutter=6, center_closed=True)` returns a `BookRig`.
  * `(x, y)` is the middle of the spine on the desk (`LecternRig.desk`).
  * `open` runs from 0 (closed, title up) to 1:
    * 0 to 0.45: the cover swings over. This is the creak.
    * 0.3 to 1.0: a flutter of `flutter` pages settles on the spread. The last page carries the
      spread's left page.
    * Animate `open` over about 1.5 s from the `book_opens` mark.
    * `center_closed=True` keeps the closed book centred on its anchor and slides it to the
      spine as it opens. Pass `False` and move the camera instead if you prefer.
  * `spread=k` shows that spread; `turn` (0..1) turns the right page over to `spread + 1`.
    * The page is a 16-strip curl with a lambert-shaded back and a shadow sweeping the pages.
    * Ease it over ~0.9 s, then set `spread=k+1, turn=0`.
  * `view` is how far from face-on the desk is seen (rad). It **must match `draw_lectern`'s**.
    * ~0.6 reads as a book lying on a lectern in wide shots.
    * Ease it toward ~0.15–0.3 as the camera pushes into a page so the painting faces us.
  * `shimmer` (0..1) is the gold-leaf burnish. It defaults to a slow candle flicker.
* **`BookRig`** (caller coordinates):
  * `pages["left"/"right"]` holds the 4 corners (tl, tr, br, bl) of each open page.
  * `page_matrix[side]` is a `cairo.Matrix` from page units (0..150, 0..200) to caller
    coordinates.
  * `page_point(side, u, v)` gives a point at page **fractions** (0..1). Use it for push-in
    targets, e.g. the middle of an illustration: `rig.page_point("right", 0.5, 0.5)`, or
    (for a box `b`) `page_point(side, b[0] + b[2] / 2, b[1] + b[3] / 2)`.
  * `anchor`, `scale`, `page_size`.
* Close-ups stay crisp. The page art is vector, drawn through the page's own transform.
  * The static page layers are cached per resolution bucket.
  * Each illustration caches its static background and paints only its life each frame.

### The pages: `PROLOGUE_SPREADS`

There are 4 spreads, so 3 page turns. The verse is set in ballad half-lines.

| spread | left page | right page | lines |
|---|---|---|---|
| 0 | drop-cap "O" + verse 1, over `doors` | `castle` (gothic arch) | `s0_l1`–`s0_l4` |
| 1 | `dragon` (arch) + lines 5–6 | `market` (arch) + lines 7–8 | `s0_l5`–`s0_l8` |
| 2 | drop-cap "S" + the coda, over `stool` | `bread` (gothic) | `s0_l9`–`s0_l10` |
| 3 | rubric: *Here beginneth the tale of the Stone and the Bread* + `fleuron` | `washhouse` (gothic) | push in, then S1 |

Suggested turns, all **read from the song's marks and line times** (the song is still being
tuned, so never hard-code them):

* `open` 0→1 from `marks["book_opens"]`.
* `turn` 0→1 (spread 0→1) at `marks["page_turn_v2"]`.
* turn 1→2 at `marks["coda_look_up"]`, as the camera pulls back to the bard.
* turn 2→3 on the word "bread" in `s0_l10`. This is the spec's "the page turns to the
  wash-house".
* Then push into `rig.page_point("right", 0.5, 0.5)` and dissolve to S1.

Build your own pages with `sb.Page`:

* `text` uses `"\n"` for new lines. A line starting with `">"` is indented as a second
  half-line.
* `drop_cap`, `cap_lines` (default 3), `illus` (a callable), `box` (page fractions),
  `frame` (`"rect"`, `"arch"`, `"gothic"` or `None`), `text_box`, `text_size`, `align`,
  `heading`, `folio`, `border` (`"vine"`, `"rule"` or `None`), `ink` (`sb.RUBRIC` for red).
* `sb.Spread(left, right)` pairs two pages.
* `sb.draw_page(cr, page, w, h, t, side, light, shimmer, detail, blank=False)` draws a single
  page in page units.

### Illustrations

`sb.ILLUSTRATIONS[name](cr, w, h, t)` paints into a box (0..w, 0..h) with "cover" fitting.
Each one keeps its static layer cached and animates by `t`. At 600×700: ~4-8 ms each, except
`market` (~16 ms) and `dragon` (~25 ms: it draws the real dragon rig every frame).

* `castle`: a castle on a hill at dusk. Pennants flutter, stars twinkle, the windows light up.
* `doors`: a street of shut doors and lanterns. Folk close and bolt their doors in a loop.
* `dragon`: **the real dragon rig**, on-model and painted in (`sb.storybook_dragon`), waving on
  a cobbled street while a goblin, a kobold and a mouse hurry by.
* `market`: the STONES / POTIONS / CANDLES stalls. Rune-glow stones, bubbling potions,
  flickering candles, fluttering awnings, swinging signs.
* `stool`: the coda vignette. An empty stool waits by a candle.
* `bread`: the moral. A grey stone and a broken loaf on a board, with a gold-leaf glory behind
  the loaf and warm steam rising.
* `washhouse`: the wash-house at night. Cold teal arched windows with tumbling drums, a sign,
  steam, a moon. This is the S1 hand-off.
* `fleuron`: a gilded ivy-leaf ornament.

The painter's toolkit is public:

* `sb.wash`: a watercolour fill with pooled edges and blooms.
* `sb.ink`, `sb.ink_outline`: iron-gall line.
* `sb.gild`: burnished gold leaf; `shimmer` brightens it.
* `sb.hatch`, `sb.paper_grain`.
* `sb.PIGMENTS`, `sb.INK`, `sb.RUBRIC`.
* `sb.folk(cr, x, y, s, kind, ...)`: little goblin, elf, dwarf, kobold and mouse figures.
* `sb.storybook_dragon(cr, x, y, s, t, wave)`.
* `sb.STORYBOOK_LIGHT`: soft light for characters painted into pages.
* Fonts: `sb.TEXT_FONT` (IM FELL English), `sb.CAP_FONT` (Uncial Antiqua) and `sb.SIGN_FONT`
  (IM FELL English SC). These are OFL fonts in `film/assets/fonts/`; if they are not installed
  the module falls back to `core.SERIF`.

### Lectern, candles, hearth, fire

* `sb.draw_lectern(cr, x, y, scale=1.0, light=None, book=None, height=230, view=0.42,
  candles=True, detail=None)` returns a `LecternRig`.
  * `(x, y)` is the floor under the column. It has scrolled tripod feet, a turned baluster
    column and a carved capital.
  * The desk is narrower than the great book, which overhangs it and rests on its ledge. Two
    scrolled iron candle arms reach out past the book's edges.
  * `LecternRig` has `desk` (where `draw_book` goes), `top`, `candles` (2 dish points) and
    `scale`.
  * It is static (~4.4 ms), so cache it in an `fx.Layer`.
* `sb.draw_candle(cr, x, y, scale=1.0, t=0.0, light=None, height=34, width=10, holder="dish",
  lit=1.0, seed=0, glow=True, drips=3)` returns a `CandleRig`.
  * It draws a beeswax candle with drips and a flickering flame (~0.9 ms).
  * `CandleRig` has `flame`, `tip`, `flicker` (0.8..1.15) and `scale`.
  * Put the room glow in the LightLayer:
    `fx.glow(lc, *cd.flame, 420 * cd.flicker, "#ffaa55", 0.4)`.
  * `sb.candle_flicker(t, seed)` returns `(brightness, sway, stretch)`.
* `sb.draw_hearth(cr, x, y, scale=1.0, light=None, seed=0, width=300, height=300,
  mantel=True)` returns a `HearthRig`.
  * It is the nook's stone fireplace: dressed-stone jambs, an arched mouth of wedge stones, a
    sooty firebox with a brick fireback, a raised hearthstone and an oak mantel on corbels.
  * `HearthRig` has `fire`, `mouth`, `mantel` and `scale`.
  * It is static (~15 ms), so cache it.
* `sb.draw_fire(cr, x, y, scale=1.0, t=0.0, seed=0, logs=True, intensity=1.0, embers=True)`
  returns a `FireRig`. Call it every frame at `HearthRig.fire` (~6.5 ms).
  * Nested tongues of flame (deep red, orange, gold, white heart) lick with their own noise and
    shed wisps.
  * Split logs with pulsing ember cracks, an ember bed and rising sparks.
  * `FireRig` has `glow`, `top`, `flicker` and `scale`.
  * Put `fx.glow(lc, *fr.glow, 900 * fr.flicker, "#ff7a30", 0.36)` in the LightLayer.
  * `sb.fire_flicker(t, seed)` returns the fire's brightness.

### The nook (reference frame)

`film/build/bard_showcase.py::prologue_mock` assembles the reference frame,
`film/build/preview/prologue_mock.png`.

* The setting is a minstrel's nook at night:
  * a stone wall in warm darkness under a ceiling beam;
  * the hearth at the left;
  * the bard's frame drum and recorder on wall pegs;
  * a little arched window with the moon;
  * a woven rug, a stack of old books with a candle stub, plank floor.
* The bard sits on his stool at 3/4, singing from `bard_song`. The lectern and open book stand
  at the right.
* Post-processing is `fx.post` with bloom 0.6, grain 0.035 and a plum vignette.
* Its `_nook(cr)` (static set dressing, drawn once in an `fx.Layer`) is a good starting point for
  `s0_prologue.py`.
* It costs ~0.3 s per frame at 1080p with all three layers cached.

### Cost

CPU per draw on this machine, scale ~1.55 unless noted:

| draw | cost |
|---|---|
| `draw_book`, open, spread 0 / 2 / 3 | ~13-18 ms |
| `draw_book`, open, spread 1 (the `dragon` + `market` pages) | ~37 ms |
| `draw_book`, open, scale 4 (push-in), spread 1 | ~80 ms |
| `draw_book`, opening (flutter) | ~11 ms |
| `draw_book`, closed | ~11 ms |
| `draw_book`, page turn | ~45-50 ms |
| `draw_lectern` (static) | ~4.4 ms |
| `draw_candle` | ~0.9 ms |
| `draw_hearth` (static) | ~15 ms |
| `draw_fire` | ~6.5 ms |

## Index: every exported name

Generated from the code (`python3 film/build/test_lib.py --only doc` fails when a module
exports a name this file never mentions). Classes are in **bold**; UPPER_CASE names are
constants. Each creature module follows one pattern: `draw_<name>`, `<Name>Pose`, `<Name>Rig`,
`<NAME>_HEIGHT`, `<NAME>_COLORS` (hex dict), `<name>_mats()` (its `B.Mat`s), `<NAME>_GESTURES`
(gesture name -> function), `<name>_walk_phase` / `<name>_stride` where it walks.

| module | prefix | names |
|---|---|---|
| core | `core.` | **Camera**, add, alpha, angle_to, arc_text, at, blob, camera_move, capsule, circle, clamp, col, convex_hull, dist, ease, ellipse, fbm1, fbm2, frame, frames, from_hsv, glow_text, hash01, hash2, hex2rgb, hgrad, hue_shift, in_back, in_cubic, in_elastic, in_quad, in_sine, inout_back, inout_cubic, inout_quad, inout_sine, invlerp, jitter, lerp, lerp_angle, lerp_pt, lerp_tuple, linear, luma, measure, mix, mul, new_context, new_surface, noise1, noise2, noise_array, normalize, out_back, out_cubic, out_elastic, out_quad, out_sine, pil_to_surface, pingpong, polygon, polyline_length, radial, ramp, remap, resample, rgb2hex, rotate_pt, rotated_text, rounded_rect, saturate, save_png, saved, set_font, shade, smooth, smooth_closed, smooth_open, smoother, smoothstep, spline, src, star, superellipse, surface_to_pil, tapered, text, text_block, text_path, tint, to_hsv, track, vgrad, window, wrap, wrap_angle, zoom_about |
| fx | `fx.` | **Layer**, **LightLayer**, bloom, blur_surface, cache_layer, crumb_landings, crumbs, dust, embers, fade, fade_alpha, finish, fireflies, glow, god_rays, grade_lut, gradient_tint, grain, lift, light_pool, light_shaft, make_lut, multiply, post, rain, screen, smoke, sparkle, splashes, tint, vignette |
| timeline | `tl.` | **Beat**, **Line**, **Scene**, active_line, beat, beats_in, cast, fps, has_beat, has_line, line, lines_in, make_stub, path, raw, reload, scene, scenes, speaking, talk, to_global, to_local, total, word_times |
| characters/base.py | `B.` / `ch.` | **Expr**, **HandFrame**, **Light**, **LineupItem**, **Mat**, **Palette**, **Path**, **Proj**, **SheetItem**, **WalkPose**, auto_blink, breathing, brow_shape, build, capture, chain, contact_shadow, detail_line, detail_lines, device_scale, ellipse_paths, ellipsoid_pts, expr, eye, fill_outlines, flat, follow, hand, hull_paths, ik2, ik3, lagged, limb, line_for, line_w, local_dir, m_mul, m_rot_x, m_rot_y, m_rot_z, m_vec, mouth, occlusion, offset_closed, outline_under, pal, shade, sheen, sheet_bg, smooth_paths, spring, sway, taper_paths, tube, tube_outline, tube_paths, v_add, v_cross, v_dot, v_len, v_lerp, v_mul, v_norm, v_sub, walk_cycle, wobble |
| characters/bard.py | `ch.` | **BardArm**, **BardPose**, **BardRig**, bard_beat, bard_cameo_pose, bard_chord, bard_chords, bard_mats, bard_sing, bard_song, bard_song_timing, bard_stride, bard_strum, bard_twinkle, bard_walk_phase, bard_yaw, draw_bard, draw_bard_stool, BARD_CHORD_NAMES, BARD_CHORDS, BARD_COLORS, BARD_GESTURES, BARD_HEIGHT, BARD_LIGHTS, BARD_LINE, BARD_MOODS, BARD_STOOL_H |
| characters/crowd.py | `ch.` | **CrowdPose**, **CrowdRig**, **CrowdSpec**, **CrystalHold**, crowd_mats, crowd_pose, crystal_feed, crystal_hold, demo_thumb, draw_crowd, draw_scrying_crystal, draw_tankard, laugh_sync, random_creature, tankard_hold, CROWD_ACTIONS, CROWD_HEIGHTS, CROWD_KINDS |
| characters/dragon.py | `ch.` | **Arm**, **DragonPose**, **DragonRig**, dragon_embers, dragon_mats, dragon_smoke, dragon_stride, dragon_walk_phase, draw_dragon, DRAGON_COLORS, DRAGON_GESTURES, DRAGON_HEIGHT, DRAGON_LINE, DRAGON_SEAT_H |
| characters/dwarf.py | `ch.` | **DwarfPose**, **DwarfRig**, draw_dwarf, dwarf_grip, dwarf_mats, dwarf_walk_phase, DWARF_COLORS, DWARF_GESTURES, DWARF_HEIGHT |
| characters/elf.py | `ch.` | **ElfArm**, **ElfPose**, **ElfRig**, draw_elf, elf_mats, elf_mirror, ELF_COLORS, ELF_GESTURES, ELF_HEIGHT, ELF_SEAT_H |
| characters/faun.py | `ch.` | **FaunPose**, **FaunRig**, draw_faun, faun_mats, faun_walk_phase, FAUN_COLORS, FAUN_GESTURES, FAUN_HEIGHT |
| characters/gnome.py | `ch.` | **GnomeArm**, **GnomePose**, **GnomeRig**, draw_gnome, gnome_bread, gnome_bread_hold, gnome_crumb_landings, gnome_mats, gnome_rig_at, gnome_stride, gnome_tear_crumbs, gnome_toss_crumbs, gnome_walk_phase, GNOME_COLORS, GNOME_GESTURES, GNOME_HEIGHT, GNOME_LINE, GNOME_LOAF, GNOME_SEAT_H |
| characters/griffin.py | `ch.` | **GriffinPose**, **GriffinRig**, draw_griffin, griffin_mats, griffin_stride, griffin_walk_phase, GRIFFIN_COLORS, GRIFFIN_HEIGHT |
| characters/lioness.py | `ch.` | **LionessArm**, **LionessPose**, **LionessRig**, draw_lioness, lioness_mats, lioness_stride, lioness_walk_phase, LIONESS_COLORS, LIONESS_COUNTER_H, LIONESS_GESTURES, LIONESS_HEIGHT |
| characters/minotaur.py | `ch.` | **MinotaurPose**, **MinotaurRig**, draw_minotaur, minotaur_mats, minotaur_walk_phase, MINOTAUR_COLORS, MINOTAUR_GESTURES, MINOTAUR_HEIGHT, MINOTAUR_VARIANTS |
| characters/orc.py | `ch.` | **OrcPose**, **OrcRig**, brawl_state, draw_brawl, draw_orc, orc_mats, orc_walk_phase, ORC_COLORS, ORC_GESTURES, ORC_HEIGHT |
| characters/pigeon.py | `ch.` | **PigeonFlock**, **PigeonPose**, **PigeonRig**, draw_pigeon, pigeon_mats, pigeon_stride, PIGEON_COLORS, PIGEON_HEIGHT |
| characters/pixie.py | `ch.` | **PixiePose**, **PixieRig**, draw_pixie, pixie_mats, pixie_wing_buzz, PIXIE_COLORS, PIXIE_GESTURES, PIXIE_HEIGHT |
| characters/troll.py | `ch.` | **TrollArm**, **TrollPose**, **TrollRig**, draw_troll, troll_mats, troll_stamp, TROLL_COLORS, TROLL_GESTURES, TROLL_HEIGHT |
| props | `P.` | **BenchRig**, **PropRig**, bag_hold, book_hold, bread_hold, candle_glow, draw_apothecary_bag, draw_bread, draw_calm_candle, draw_coloring_book, draw_crumbs, draw_garden_bench, draw_hanging_sign, draw_hourglass, draw_lantern_post, draw_lantern_string, draw_music_note, draw_note, draw_plaque, draw_remedy, draw_shelves, draw_sleep_draught, draw_smile_mark, draw_speaking_stone, draw_stamp, draw_stool, draw_tankard, draw_tavern_table, draw_till, draw_tumbling_drum, draw_vitamins, draw_washhouse_bench, draw_wisp_lamp, drum_body, drum_light, drum_porthole, lantern_light, lantern_string_light, note_hold, pile_layout, prop_mats, remedy_hold, sign_light, smile_stamp, stamp_hold, stone_glow, stone_hold, stone_level, stone_light, tankard_hold, wisp_light, BAG_H, BAG_W, BENCH_DEPTH, BENCH_LEN, BENCH_SEAT_H, BOOK_H, BOOK_W, FONTS, LOAF, NOTE_H, NOTE_W, PROP_COLORS, REMEDIES, STONE_H, STONE_W, STOOL_SEAT_H |
| env | `env.` | **Mist**, **OakTree**, **Rain**, **StarField**, draw_arch, draw_castle_hill, draw_clouds, draw_cobbles, draw_flower_bed, draw_grass, draw_gravel_path, draw_ground_shadow, draw_haze, draw_hedge, draw_hills, draw_house, draw_mist, draw_moon, draw_oak, draw_puddle, draw_roofline, draw_sky, draw_stone_wall, draw_street_row, draw_vaulted_hall, draw_wet_reflections, haze_toward, layer, palette, puddle_ripples, texture, MARGIN, PALETTES |
| storybook | `sb.` | **Book**, **BookRig**, **CandleRig**, **FireRig**, **HearthRig**, **Illustration**, **LecternRig**, **Page**, **Spread**, candle_flicker, draw_book, draw_candle, draw_fire, draw_hearth, draw_lectern, draw_page, fire_flicker, folk, gild, hatch, illus_bread, illus_castle, illus_doors, illus_dragon, illus_fleuron, illus_market, illus_stool, illus_washhouse, ink, ink_outline, page_turn_shadow, paper_grain, storybook_dragon, wash, CAP_FONT, ILLUSTRATIONS, INK, PIGMENTS, PROLOGUE_SPREADS, RUBRIC, SIGN_FONT, STORY_LIGHT, STORYBOOK_LIGHT, TEXT_FONT |
