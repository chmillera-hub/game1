# API.md: the film library for scene and character authors

Everything here is plain Python 3 + cairocffi + numpy + Pillow. Run every command from the
repo root (`/home/user/game1`). Style rules (outlines, shading, scale, eyes, LOD, budget) live
in **STYLE.md**; this file is the reference for *how to call things*. Keep it accurate when you
add to the library: append your module under **Cast**, **Props** or **Environment**.

```python
from film.lib import core, fx, timeline            # + env, props when they exist
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
                       #       .duration .wav .caption .vo .fx .env (envelope samples) .env_at(t)
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
* Stub: `python3 -m film.lib.timeline --stub film/build/stub_timeline.json`. It mirrors the SPEC
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
* `embers(cr, t, x, y, t0, n, life, spread, rise, color, hot, size, seed, burst, scale, wind)`.
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
  * `size` is the part's thickness (crescent width).
  * Cost is ~0.2-0.5 ms per part.
* `flat(cr, path, color, lw, line)`: flat fill + thin outline (claws, buttons).
* `detail_line(cr, pts, w, color, alpha, taper)` and **`detail_lines(cr, [pts, ...], w, color,
  alpha, taper)`** for batched tapered ink.
* `occlusion(cr, x, y, rx, ry, color, alpha, clip)`: soft contact darkening.
* `sheen(cr, x, y, rx, ry, angle, alpha)`: a specular dab.
* `outline_under(cr, path, lw, color, exclude)`.
* `device_scale(cr)`, `line_w(cr, lw)`, `local_dir(cr, v)`.
* `LINE = 2.2`, `MIN_LINE_PX = 1.0`.

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

## Props

*(film/lib/props.py: each recurring prop, its draw signature, anchor, size at scale 1.0 and
how it attaches to a hand via `hold`.)*

## Environment

*(film/lib/env.py: the environment kit: walls, timber facades, cobbles, sky, trees, castle;
how to cache it in `fx.Layer`s and its parallax planes.)*
