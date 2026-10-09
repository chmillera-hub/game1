"""S0 - "Cold open" (BIBLE section 4, S0).

Deep space. The Meridian overtakes the camera from the lower left and settles into frame while the
title breathes in and out above it; then the camera dives - accelerating - into one warm arched
window (the lounge window, a tiny figure standing in it) until the glass fills the frame and the
picture flashes warm white (#FFF4E0). S1 opens from that flash.

Everything is SCREEN space: env.draw_space fills the frame, the ship is placed with
env.draw_ship(x, y, scale, angle) and the dive is a zoom about the hero window (env.ship_window).
render(canvas, t) is a pure function of absolute time t; all times derive from named beats.
"""
from __future__ import annotations

import math

import skia

from anim import env, fx
from anim.core import (Layer, Track, beat, clamp, lerp, light_filter, music_onsets, paint, remap, scene_span,
                       smoothstep)
from config import H, W

# =========================================================================== timing (named)
T0, T1 = scene_span("s0")
TITLE_IN = beat("title_in")
TITLE_OUT = beat("title_out")
DIVE = beat("dive_start")
FILL = DIVE + 2.9                      # ~15.4: the window glass fills the frame (whoosh peak)
GLIDE_IN = T0 + 0.5                    # the Meridian starts entering from the lower left
GLIDE_END = T1                         # the glide keeps easing out through the dive (never a dead stop)

# =========================================================================== the glide (screen space)
# cubic bezier the ship origin follows; enters off-frame lower left, settles a little below centre
_P = ((-140.0, 1720.0), (20.0, 1300.0), (300.0, 860.0), (362.0, 716.0))


def _bez(u):
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = _P
    v = 1.0 - u
    return (v ** 3 * x0 + 3 * v * v * u * x1 + 3 * v * u * u * x2 + u ** 3 * x3,
            v ** 3 * y0 + 3 * v * v * u * y1 + 3 * v * u * u * y2 + u ** 3 * y3)


def _glide_u(t):
    """0..1 progress along the path: quick graceful entry, long easing-out settle."""
    x = clamp((t - GLIDE_IN) / (GLIDE_END - GLIDE_IN))
    # fastest at the start (the ship is still off-frame) + a long decelerating tail
    return 1.0 - (1.0 - x) ** 1.75


SCALE0, SCALE1 = 1.34, 1.48            # ship grows a touch as it comes closer
ANGLE0 = 27.0                          # nose up-right while it overtakes the camera...


def glide(t):
    """(x, y, scale, angle) of the ship in screen space before the dive transform."""
    u = _glide_u(t)
    x, y = _bez(u)
    # ...and it straightens to the travel direction (stars drift straight down) as it settles
    ang = ANGLE0 * (1.0 - smoothstep(remap(t, GLIDE_IN + 1.0, DIVE + 1.6))) ** 1.15
    # a very slow, small bank so it never reads as a static cut-out
    ang += 1.2 * math.sin((t - GLIDE_IN) * 0.35) * (1.0 - smoothstep(remap(t, DIVE, DIVE + 1.5)))
    sc = lerp(SCALE0, SCALE1, smoothstep(u))
    return x, y, sc, ang


# =========================================================================== the dive
ZOOM_EXP = 6.5                         # ln of the final zoom factor at T1 (only reached under the flash)
DIVE_POW = 1.85                        # > 1: the push accelerates


def dive_zoom(t):
    u = clamp((t - DIVE) / (T1 - DIVE))
    return math.exp(ZOOM_EXP * u ** DIVE_POW)


# The dive is a zoom about a FOCUS point on the hull: it starts as the hero window's centre and, in the
# last half second, slides up to the warm light at the top of the glass, so we fly into the light
# (and past the little figure standing in the window) as the frame flashes.
CENTER = (W / 2, H / 2)
_center_ease = Track([(DIVE, 0.0), (FILL - 0.3, 1.0, "io")])
_FOCUS_GLOW = (0.5, -2.0)              # hero-window-local offset: the warm upper glass, just right of the figure
_focus_ease = Track([(FILL - 0.55, 0.0), (FILL + 0.2, 1.0, "io")])


def _rot(vx, vy, ang):
    a = math.radians(ang)
    return vx * math.cos(a) - vy * math.sin(a), vx * math.sin(a) + vy * math.cos(a)


def ship_xf(t):
    """Final (x, y, scale, angle, focus_xy, zoom) for drawing the ship at time t (screen space)."""
    x, y, sc, ang = glide(t)
    if t <= DIVE:
        wx, wy = env.ship_window(x, y, sc, ang)
        return x, y, sc, ang, (wx, wy), 1.0
    z = dive_zoom(t)
    S = sc * z
    f = _focus_ease(t)
    flx, fly = _FOCUS_GLOW[0] * f, _FOCUS_GLOW[1] * f
    # where the glide alone would put the focus point, eased to the frame centre
    wx0, wy0 = env.ship_window(x, y, sc, ang)
    dx0, dy0 = _rot(flx * sc, fly * sc, ang)
    e = _center_ease(t)
    fx_, fy_ = lerp(wx0 + dx0, CENTER[0], e), lerp(wy0 + dy0, CENTER[1], e)
    # back out the ship origin from the focus point at the zoomed scale
    dx, dy = _rot(flx * S, fly * S, ang)
    ox, oy = env.ship_window(0.0, 0.0, S, ang)
    return fx_ - dx - ox, fy_ - dy - oy, S, ang, (fx_, fy_), z


# =========================================================================== title
TITLE_Y = 300.0
title_alpha = Track([(TITLE_IN, 0.0), (TITLE_IN + 1.9, 1.0, "io"), (TITLE_OUT - 1.7, 1.0), (TITLE_OUT, 0.0, "io")])
# 8 px drift up while it fades in, then it keeps rising a hair (never settles into a dead hold)
title_dy = Track([(TITLE_IN, 8.0), (TITLE_IN + 1.9, 0.0, "out"), (TITLE_OUT, -5.0, "lin")])

# =========================================================================== light
space_bright = Track([(T0, 0.0), (T0 + 2.6, 1.0, "io")])
flash = Track([(FILL - 0.28, 0.0), (FILL + 0.15, 1.0, "in")])


def _warm_bloom(canvas, wx, wy, z, t):
    """Soft warm light from the window that blooms toward the camera as we approach."""
    k = smoothstep(remap(math.log(max(z, 1.0)), math.log(2.5), math.log(70.0)))
    if k <= 0.003:
        return
    r = 60.0 + 900.0 * k
    sh = skia.GradientShader.MakeRadial((wx, wy), r, [skia.Color(255, 226, 170, int(150 * k)),
                                                      skia.Color(255, 200, 130, int(55 * k)),
                                                      skia.Color(255, 190, 120, 0)], [0.0, 0.45, 1.0])
    p = skia.Paint(AntiAlias=False)
    p.setShader(sh)
    canvas.drawRect(skia.Rect(max(0.0, wx - r), max(0.0, wy - r), min(W, wx + r), min(H, wy + r)), p)


# =========================================================================== render
_ONSETS = None


def _onsets():
    global _ONSETS
    if _ONSETS is None:
        _ONSETS = [o for o in music_onsets("opening") if T0 <= o < DIVE + 1.0]
    return _ONSETS


def render(canvas, t):
    fl = flash(t)
    if fl >= 0.999:                                   # fully under the warm-white flash
        fx.draw_flash(canvas, 1.0)
        return
    x, y, S, ang, (wx, wy), z = ship_xf(t)
    # ---- space: stars drift down (camera travelling up with the ship); the dive pushes the layers out
    sz = z ** 0.32
    env.draw_space(canvas, t, drift=1.0, brightness=space_bright(t), zoom=sz)
    # ---- celesta notes of the opening cue: a few soft glints in the sky above the ship
    a_sp = space_bright(t) * (1.0 - smoothstep(remap(t, DIVE, DIVE + 0.8)))
    if a_sp > 0.01:
        fx.draw_note_sparkles(canvas, t, _onsets(), area=(70, 150, 650, 640), seed=3, life=1.9,
                              colors=("teal_glow", "amber_soft", "#D9C8FF"), alpha=0.55 * a_sp, size=0.75)
    # ---- the Meridian
    if t >= GLIDE_IN - 0.05:
        # up close the pearl hull would read as a white glare: hold it down a touch (cool tint) while
        # it fills the frame, so the warm window stays the brightest thing; back to full by the flash
        lz = math.log(max(z, 1.0))
        k = smoothstep(remap(lz, math.log(4.0), math.log(14.0))) * (1.0 - smoothstep(remap(lz, math.log(30.0), math.log(90.0))))
        if k > 0.01:
            with Layer(canvas, cf=light_filter(1.0 - 0.15 * k, (60, 70, 110), 0.10 * k)):
                env.draw_ship(canvas, t, x, y, S, ang, glow=1.0)
        else:
            env.draw_ship(canvas, t, x, y, S, ang, glow=1.0)
    # ---- warm light pouring out of the window as we close in
    if t > DIVE:
        _warm_bloom(canvas, wx, wy, z, t)
    # ---- soft vignette for depth while we are out in space (lifts as the hull fills the frame)
    vg = 0.38 * (1.0 - smoothstep(remap(t, DIVE + 1.0, DIVE + 2.2)))
    if vg > 0.003:
        fx.draw_vignette(canvas, vg)
    # ---- title
    ta = title_alpha(t)
    if ta > 0.003:
        fx.draw_title(canvas, t, "IF YOU HAVE TIME", TITLE_Y + title_dy(t), alpha=ta, size=44)
    # ---- fade up from black at the very top of the film
    fb = 1.0 - smoothstep(remap(t, T0, T0 + 1.2))
    if fb > 0.003:
        canvas.drawRect(skia.Rect(0, 0, W, H), paint("#000000", fb, aa=False))
    # ---- warm-white flash -> S1
    if fl > 0.002:
        fx.draw_flash(canvas, fl)
