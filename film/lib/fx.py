"""fx.py -- lighting, post effects and particles. Everything here is cheap per frame.

Typical scene frame (see film/build/demo_hero.py for a complete, timed example):

    def setup():
        return {"bg": fx.Layer(draw_background, blur=1.5, opaque=True),   # static art, cached
                "far": fx.Layer(draw_far, blur=6, res=0.5),                # pre-blurred = DOF
                "light": fx.LightLayer()}                                   # 1/4-res soft light

    def draw(cr, t, st):
        with cam.view(cr, 0.4): st["far"].paint(cr)
        with cam.view(cr, 1.0): st["bg"].paint(cr); ...props, characters, small glows...
        lc = st["light"].begin()                       # cleared, FULL-RES coordinates
        with cam.view(lc, 1.0): fx.light_shaft(lc, ...); fx.glow(lc, ..., r=300); fx.light_pool(lc, ...)
        fx.post(cr, t, light=st["light"], bloom_strength=0.5, threshold=0.65,
                grain=0.035, vignette=0.4)             # light + bloom + vignette + grain, ~18 ms
        fx.fade(cr, 1 - core.ramp(t, 0, 1))             # fades go on top of everything

Costs at 1920x1080 (single core): full-frame OVER of a cached layer ~3-7 ms; radial glow
r=100 ~0.9 ms, r=300 ~7 ms at full res (cost ~ area: big glows and shafts belong in the
LightLayer, 1/16 the cost); bloom ~10 ms; finish (grain + vignette) ~6 ms; grade_lut ~20 ms.
Blend operators other than OVER/ADD/SOURCE (multiply, overlay, screen) cost ~25 ms full frame.
"""

import functools
import math

import cairocffi as cairo
import numpy as np
from PIL import Image, ImageFilter

from . import core
from .core import col, clamp, hash01, noise1, TAU

# ----------------------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------------------


def _target(x):
    """Accept a Context or a Surface; return the ImageSurface."""
    return x.get_target() if isinstance(x, cairo.Context) else x


def _ctx(x):
    return x if isinstance(x, cairo.Context) else cairo.Context(x)


def blur_surface(surface, radius, opaque_edges=False):
    """Gaussian-blurred copy of an ARGB32 surface (premultiplied blur, so no dark fringes).
    opaque_edges=True replicates edge pixels first (for full-bleed backgrounds)."""
    surface.flush()
    w, h = surface.get_width(), surface.get_height()
    stride = surface.get_stride()
    im = Image.frombuffer("RGBA", (w, h), bytes(surface.get_data()), "raw", "RGBA", stride, 1)
    if radius <= 0:
        out = im
    elif opaque_edges:
        pad = int(radius * 3) + 2
        arr = np.asarray(im)
        arr = np.pad(arr, ((pad, pad), (pad, pad), (0, 0)), mode="edge")
        out = Image.fromarray(arr, "RGBA").filter(ImageFilter.GaussianBlur(radius))
        out = out.crop((pad, pad, pad + w, pad + h))
    else:
        out = im.filter(ImageFilter.GaussianBlur(radius))
    data = bytearray(out.tobytes())
    res = cairo.ImageSurface.create_for_data(data, cairo.FORMAT_ARGB32, w, h, w * 4)
    res._keepalive = data  # cairocffi keeps a ref too, but be explicit
    return res


# ----------------------------------------------------------------------------------------
# Layer cache -- static art rendered once, reused every frame
# ----------------------------------------------------------------------------------------


class Layer:
    """Static art rendered once into an ImageSurface and painted every frame.

    draw(cr) draws in WORLD coordinates covering the rect (x, y, w, h) (default: the frame).
    res < 1 renders at reduced resolution (cheaper + naturally soft: use for blurred far layers).
    blur = Gaussian radius in world px (depth of field); opaque=True avoids dark edges when
    blurring full-bleed backgrounds. Paint inside a camera view for parallax:

        with cam.view(cr, 0.5): layer.paint(cr)
    """

    def __init__(self, draw, w=core.W, h=core.H, x=0.0, y=0.0, blur=0.0, res=1.0, opaque=False):
        self.x, self.y, self.w, self.h, self.res = float(x), float(y), float(w), float(h), float(res)
        sw, sh = int(math.ceil(w * res)), int(math.ceil(h * res))
        surf = core.new_surface(sw, sh)
        cr = core.new_context(surf)
        cr.scale(res, res)
        cr.translate(-x, -y)
        draw(cr)
        surf.flush()
        if blur > 0:
            surf = blur_surface(surf, blur * res, opaque_edges=opaque)
        self.surface = surf

    def paint(self, cr, alpha=1.0, dx=0.0, dy=0.0, operator=None, fast=False):
        cr.save()
        cr.translate(self.x + dx, self.y + dy)
        if self.res != 1.0:
            cr.scale(1.0 / self.res, 1.0 / self.res)
        cr.set_source_surface(self.surface, 0, 0)
        pat = cr.get_source()
        pat.set_filter(cairo.FILTER_FAST if fast else cairo.FILTER_BILINEAR)
        if operator is not None:
            cr.set_operator(operator)
        cr.rectangle(0, 0, self.surface.get_width(), self.surface.get_height())
        if alpha >= 0.999:
            cr.fill()
        else:
            cr.clip()
            cr.paint_with_alpha(alpha)
        cr.restore()


def cache_layer(draw, **kw):
    """Functional alias for Layer(draw, **kw)."""
    return Layer(draw, **kw)


# ----------------------------------------------------------------------------------------
# glows, light pools, shafts
# ----------------------------------------------------------------------------------------

# a soft, natural falloff (closer to inverse-square-ish than a linear ramp)
_GLOW_PROFILE = ((0.0, 1.0), (0.12, 0.72), (0.3, 0.38), (0.5, 0.16), (0.72, 0.05), (1.0, 0.0))


def glow(cr, x, y, r, color, alpha=1.0, additive=True, core_r=0.0, core_alpha=1.0):
    """Soft radial light glow (bounded to its circle, cost ~ r^2: r=100 ~0.9 ms).

    additive=True adds light (lamps, wisps, embers); False paints it normally.
    core_r > 0 adds a small bright hot-spot of that radius."""
    if r <= 0 or alpha <= 0:
        return
    c = col(color)
    pat = cairo.RadialGradient(x, y, 0.0, x, y, r)
    for off, k in _GLOW_PROFILE:
        pat.add_color_stop_rgba(off, c[0], c[1], c[2], k * alpha)
    cr.save()
    if additive:
        cr.set_operator(cairo.OPERATOR_ADD)
    cr.set_source(pat)
    cr.arc(x, y, r, 0, TAU)
    cr.fill()
    if core_r > 0:
        p2 = cairo.RadialGradient(x, y, 0.0, x, y, core_r)
        p2.add_color_stop_rgba(0.0, 1, 1, 1, core_alpha * alpha)
        p2.add_color_stop_rgba(0.5, c[0], c[1], c[2], 0.6 * core_alpha * alpha)
        p2.add_color_stop_rgba(1.0, c[0], c[1], c[2], 0.0)
        cr.set_source(p2)
        cr.arc(x, y, core_r, 0, TAU)
        cr.fill()
    cr.restore()


def light_pool(cr, x, y, rx, ry, color, alpha=0.5, additive=True):
    """Elliptical pool of light on a floor / wall (e.g. under a lantern)."""
    if rx <= 0 or ry <= 0:
        return
    c = col(color)
    cr.save()
    cr.translate(x, y)
    cr.scale(1.0, ry / rx)
    pat = cairo.RadialGradient(0, 0, 0, 0, 0, rx)
    for off, k in _GLOW_PROFILE:
        pat.add_color_stop_rgba(off, c[0], c[1], c[2], k * alpha)
    if additive:
        cr.set_operator(cairo.OPERATOR_ADD)
    cr.set_source(pat)
    cr.arc(0, 0, rx, 0, TAU)
    cr.fill()
    cr.restore()


def light_shaft(cr, x0, y0, x1, y1, w0, w1, color, alpha=0.22, soft=3, fade_start=0.0,
                fade_end=1.0, additive=True):
    """A soft volumetric beam from (x0, y0) [width w0] to (x1, y1) [width w1].

    Built from `soft` nested quads (wide+faint -> narrow) with a gradient along the beam, so
    the edges feel soft. fade_start/fade_end shape where along the beam it is visible."""
    c = col(color)
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1e-6
    nx, ny = -dy / L, dx / L
    cr.save()
    if additive:
        cr.set_operator(cairo.OPERATOR_ADD)
    for k in range(soft):
        f = 1.0 - 0.55 * k / max(1, soft - 1) if soft > 1 else 1.0
        a = alpha / soft
        h0, h1 = w0 * 0.5 * f, w1 * 0.5 * f
        cr.move_to(x0 + nx * h0, y0 + ny * h0)
        cr.line_to(x1 + nx * h1, y1 + ny * h1)
        cr.line_to(x1 - nx * h1, y1 - ny * h1)
        cr.line_to(x0 - nx * h0, y0 - ny * h0)
        cr.close_path()
        pat = cairo.LinearGradient(x0, y0, x1, y1)
        pat.add_color_stop_rgba(0.0, c[0], c[1], c[2], a * fade_start)
        pat.add_color_stop_rgba(0.15, c[0], c[1], c[2], a)
        pat.add_color_stop_rgba(0.6, c[0], c[1], c[2], a * 0.55)
        pat.add_color_stop_rgba(1.0, c[0], c[1], c[2], a * (1.0 - fade_end))
        cr.set_source(pat)
        cr.fill()
    cr.restore()


def god_rays(cr, x, y, angle, spread, length, color, t=0.0, n=5, width=(30, 120), alpha=0.18,
             seed=0, shimmer=0.35):
    """A fan of n soft shafts from a source point (window, crack, canopy gap).
    angle = central direction (rad, 0 = +x, pi/2 = down), spread = fan angle, width=(w0, w1).
    Shafts breathe slowly with t (shimmer 0..1)."""
    for i in range(n):
        u = (i + 0.5) / n - 0.5
        a = angle + u * spread + core.jitter(i, spread * 0.15, seed)
        L = length * (0.75 + 0.25 * hash01(i, seed + 3))
        k = 1.0 - shimmer * (0.5 + 0.5 * noise1(t * 0.35 + i * 3.1, seed + i))
        light_shaft(cr, x, y, x + math.cos(a) * L, y + math.sin(a) * L, width[0], width[1],
                    color, alpha * k * (0.6 + 0.4 * hash01(i, seed + 9)))


# ----------------------------------------------------------------------------------------
# bloom
# ----------------------------------------------------------------------------------------


@functools.lru_cache(maxsize=4)
def _buffers(w, h):
    """Shared scratch surfaces: 1/2, 1/4, 1/8 res chain + one full-res upscale target."""
    return (core.new_surface(w // 2, h // 2), core.new_surface(w // 4, h // 4),
            core.new_surface(w // 8, h // 8), core.new_surface(w, h))


def _resample(dst, srcs, sx, sy=None, op=cairo.OPERATOR_SOURCE):
    c = cairo.Context(dst)
    c.scale(sx, sx if sy is None else sy)
    c.set_source_surface(srcs, 0, 0)
    pat = c.get_source()
    pat.set_filter(cairo.FILTER_BILINEAR)
    pat.set_extend(cairo.EXTEND_PAD)
    c.set_operator(op)
    c.paint()
    dst.flush()


def _add_full(target, small):
    """Upscale a small additive surface to the frame and ADD it (fast path: bilinear SOURCE into
    a scratch buffer, then an unscaled ADD -- ~6.5 ms instead of ~26 ms for a scaled ADD)."""
    surf = _target(target)
    w, h = surf.get_width(), surf.get_height()
    full = _buffers(w, h)[3]
    _resample(full, small, w / small.get_width(), h / small.get_height())
    cr = _ctx(target)
    cr.save()
    cr.identity_matrix()
    cr.reset_clip()
    cr.set_operator(cairo.OPERATOR_ADD)
    cr.set_source_surface(full, 0, 0)
    cr.paint()
    cr.restore()


class LightLayer:
    """A quarter-resolution additive layer for soft light: shafts, god rays, light pools, big
    glows, haze. Drawing into it costs 1/16 of drawing at full res, and it is composited with
    one cheap upscale (+ the bloom, if you pass it to bloom()/post()).

        L = fx.LightLayer()                    # once (setup or module level)
        lc = L.begin()                         # every frame: cleared context, FULL-RES coords
        with cam.view(lc, 1.0): fx.light_shaft(lc, ...); fx.glow(lc, ...)
        fx.post(cr, t, light=L, bloom_strength=0.5)   # or L.composite(cr)

    Use additive drawing inside (glow()/light_shaft()/light_pool() default to ADD).
    """

    def __init__(self, w=core.W, h=core.H, res=0.25):
        self.w, self.h, self.res = int(w), int(h), res
        self.surface = core.new_surface(int(w * res), int(h * res))
        self.ctx = None
        self.dirty = False

    def begin(self):
        c = core.new_context(self.surface)
        c.set_operator(cairo.OPERATOR_CLEAR)
        c.paint()
        c.set_operator(cairo.OPERATOR_OVER)
        c.scale(self.res, self.res)
        self.ctx = c
        self.dirty = True
        return c

    def composite(self, target, alpha=1.0):
        if not self.dirty:
            return
        self.surface.flush()
        if alpha < 0.999:
            tmp = _buffers(self.w, self.h)[1]
            c = cairo.Context(tmp)
            c.set_operator(cairo.OPERATOR_SOURCE)
            c.set_source_surface(self.surface, 0, 0)
            c.paint_with_alpha(alpha)
            tmp.flush()
            _add_full(target, tmp)
        else:
            _add_full(target, self.surface)
        self.dirty = False


@functools.lru_cache(maxsize=64)
def _bloom_lut(threshold, knee, strength):
    lut = []
    for v in range(256):
        lum = v / 255.0
        soft = clamp(lum - threshold + knee, 0.0, 2.0 * knee)
        soft = soft * soft / (4.0 * knee + 1e-5)
        c = max(soft, lum - threshold) / max(lum, 1e-4)
        lut.append(int(min(255, round(c * strength * 255))))
    return lut


def _bloom_image(surf, threshold, strength, radius, knee, wide, wide_radius, tint):
    """Bloom contribution as a PIL RGB image at 1/8 res."""
    from PIL import ImageChops
    w, h = surf.get_width(), surf.get_height()
    half, quarter, eighth, _ = _buffers(w, h)
    _resample(half, surf, 0.5)
    _resample(quarter, half, 0.5)
    _resample(eighth, quarter, 0.5)
    ew, eh = eighth.get_width(), eighth.get_height()
    q = Image.frombuffer("RGBA", (ew, eh), bytes(eighth.get_data()), "raw", "BGRA", eighth.get_stride(), 1)
    rgb = q.convert("RGB")
    k = rgb.convert("L").point(_bloom_lut(round(threshold, 3), round(knee, 3), round(strength, 3)))
    g = ImageChops.multiply(rgb, Image.merge("RGB", (k, k, k)))
    if tint is not None:
        tc = col(tint)
        g = ImageChops.multiply(g, Image.new("RGB", g.size, tuple(int(v * 255) for v in tc[:3])))
    out = g.filter(ImageFilter.GaussianBlur(radius))
    if wide > 0:
        g2 = g.resize((ew // 3, eh // 3), Image.BILINEAR).filter(ImageFilter.GaussianBlur(wide_radius))
        g2 = g2.point([int(min(255, v * wide)) for v in range(256)] * 3).resize((ew, eh), Image.BILINEAR)
        out = ImageChops.add(out, g2)
    return out


def bloom(target, threshold=0.72, strength=0.6, radius=2.0, knee=0.12, tint=None, wide=0.0,
          wide_radius=2.5, light=None):
    """Make bright areas glow: luminance threshold (soft knee) -> blur -> add. ~9 ms at 1080p.

    threshold: luminance 0..1 where bloom starts. strength: gain of the glow (0.3-1.0).
    radius: blur radius in 1/8-res px (x8 on screen: 2.0 ~ a 16 px halo). wide > 0 adds a second
    very wide halo with that relative strength. tint: multiply the glow color.
    light: a LightLayer -- its contents are composited in the same upscale (saves ~6 ms)."""
    surf = _target(target)
    surf.flush()
    img = _bloom_image(surf, threshold, strength, radius, knee, wide, wide_radius, tint)
    data = bytearray(img.tobytes("raw", "BGRX"))
    small = cairo.ImageSurface.create_for_data(data, cairo.FORMAT_ARGB32, img.width, img.height, img.width * 4)
    if light is not None and light.dirty:
        # fold the bloom into the light layer (1/4 res), then one upscale for both
        light.surface.flush()
        _resample(light.surface, small, light.surface.get_width() / img.width,
                  light.surface.get_height() / img.height, op=cairo.OPERATOR_ADD)
        light.composite(target)
    else:
        _add_full(target, small)


def post(target, t, light=None, bloom_strength=0.0, threshold=0.72, bloom_radius=2.0, wide=0.0,
         grain=0.04, vignette=0.35, vignette_color=(0, 0, 0), bloom_tint=None):
    """One call for the standard end-of-frame chain: light layer + bloom, vignette, grain."""
    if bloom_strength > 0:
        bloom(target, threshold, bloom_strength, bloom_radius, tint=bloom_tint, wide=wide, light=light)
    elif light is not None:
        light.composite(target)
    finish(target, t, grain=grain, vignette=vignette, vignette_color=vignette_color)


# ----------------------------------------------------------------------------------------
# grain, vignette, finish
# ----------------------------------------------------------------------------------------

@functools.lru_cache(maxsize=4)
def _grain_tiles(size=384, n=4, seed=7, softness=2, k_light=0.35, k_dark=1.0):
    """n tiles of grain as premultiplied ARGB painted with OVER: black specks darken
    proportionally (film-like), weaker white specks lift the darks a little. Generated at
    1/softness res and bicubic-upsampled -> soft ~2 px clumps that survive H.264.
    Calibrated: paint alpha 0.064 gives ~0.016 std-dev at mid grey, ~0.011 in deep shadow."""
    rng = np.random.default_rng(seed)
    tiles = []
    for _ in range(n):
        small = rng.normal(0.0, 1.0, (size // softness, size // softness)).astype(np.float32)
        im = Image.fromarray(small, "F").resize((size, size), Image.BICUBIC)
        v = np.asarray(im, np.float32)
        v = v / max(1e-6, float(v.std()))
        a = np.clip(np.where(v > 0, v * k_light, -v * k_dark), 0.0, 1.0)
        arr = np.zeros((size, size, 4), np.uint8)
        arr[..., 3] = (a * 255).astype(np.uint8)
        lum = np.where(v > 0, a * 255, 0).astype(np.uint8)
        arr[..., 0] = lum
        arr[..., 1] = lum
        arr[..., 2] = lum
        data = bytearray(arr.tobytes())
        s = cairo.ImageSurface.create_for_data(data, cairo.FORMAT_ARGB32, size, size, size * 4)
        tiles.append((s, data))
    return tiles


def _apply_grain(target, t=0.0, amount=0.04, frame=None, seed=0):
    """Film grain: ~amount brightness std-dev (0.03-0.05 recommended). Changes every frame."""
    if amount <= 0:
        return
    cr = _ctx(target)
    fi = int(round(t * core.FPS)) if frame is None else int(frame)
    tiles = _grain_tiles()
    tile = tiles[fi % len(tiles)][0]
    ox = hash01(fi, seed + 1) * 384.0
    oy = hash01(fi, seed + 2) * 384.0
    cr.save()
    cr.identity_matrix()
    cr.reset_clip()
    pat = cairo.SurfacePattern(tile)
    pat.set_extend(cairo.EXTEND_REPEAT)
    pat.set_filter(cairo.FILTER_FAST)
    m = cairo.Matrix()
    m.translate(int(ox), int(oy))
    pat.set_matrix(m)
    cr.set_source(pat)
    cr.paint_with_alpha(clamp(amount * 1.6))
    cr.restore()


@functools.lru_cache(maxsize=16)
def _vignette_surface(w, h, strength, radius, softness, color, roundness):
    s = core.new_surface(w, h)
    c = cairo.Context(s)
    cx, cy = w / 2.0, h / 2.0
    # ellipse matching the frame aspect, pulled toward a circle by `roundness`
    sx = 1.0 + (w / h - 1.0) * (1.0 - roundness)
    rr = math.hypot(cx / sx, cy) * radius
    c.translate(cx, cy)
    c.scale(sx, 1.0)
    pat = cairo.RadialGradient(0, 0, rr * (1.0 - softness), 0, 0, rr * 1.15)
    r_, g_, b_ = color
    for i in range(9):
        u = i / 8.0
        pat.add_color_stop_rgba(u, r_, g_, b_, strength * (u ** 1.6))
    c.set_source(pat)
    c.paint()
    s.flush()
    return s


def _apply_vignette(target, strength=0.35, radius=1.0, softness=0.75, color=(0.0, 0.0, 0.0), roundness=0.35):
    """Soft darkening toward the corners (cached; ~3 ms). color can tint it (e.g. deep blue)."""
    if strength <= 0:
        return
    cr = _ctx(target)
    surf = _vignette_surface(_target(target).get_width(), _target(target).get_height(),
                             round(float(strength), 3), round(float(radius), 3), round(float(softness), 3),
                             tuple(round(v, 3) for v in col(color)[:3]), round(float(roundness), 3))
    cr.save()
    cr.identity_matrix()
    cr.reset_clip()
    cr.set_source_surface(surf, 0, 0)
    cr.paint()
    cr.restore()


grain = _apply_grain
vignette = _apply_vignette


def finish(target, t, grain=0.04, vignette=0.35, vignette_color=(0, 0, 0)):
    """The standard last pass on every frame: vignette + grain (before fades / titles).
    grain = brightness std-dev (0.03-0.05), vignette = corner darkening strength (0.25-0.5)."""
    _apply_vignette(target, vignette, color=vignette_color)
    _apply_grain(target, t, grain)


# ----------------------------------------------------------------------------------------
# color grade & fades
# ----------------------------------------------------------------------------------------


def _full_paint(cr, op, color, a):
    cr.save()
    cr.identity_matrix()
    cr.reset_clip()
    cr.set_operator(op)
    core.src(cr, color, a)
    cr.paint()
    cr.restore()


def tint(target, color, alpha=0.1):
    """Wash the frame toward a color (OVER, ~0.5 ms)."""
    _full_paint(_ctx(target), cairo.OPERATOR_OVER, color, alpha)


def lift(target, color, amount=0.05):
    """Add light (raises blacks; ADD, ~1 ms). Good for haze / warmth entering a scene."""
    _full_paint(_ctx(target), cairo.OPERATOR_ADD, color, amount)


def multiply(target, color, alpha=1.0):
    """Multiply the frame by a color (true per-channel grade; ~15-25 ms)."""
    _full_paint(_ctx(target), cairo.OPERATOR_MULTIPLY, color, alpha)


def screen(target, color, alpha=1.0):
    _full_paint(_ctx(target), cairo.OPERATOR_SCREEN, color, alpha)


def gradient_tint(target, top, bottom, alpha=1.0, additive=False):
    """Vertical graded wash (e.g. warm top / cool bottom), ~2 ms."""
    cr = _ctx(target)
    s = _target(target)
    hh = s.get_height()
    cr.save()
    cr.identity_matrix()
    cr.reset_clip()
    if additive:
        cr.set_operator(cairo.OPERATOR_ADD)
    pat = core.linear(0, 0, 0, hh, [core.alpha(top, alpha), core.alpha(bottom, alpha)])
    cr.set_source(pat)
    cr.paint()
    cr.restore()


def make_lut(r=None, g=None, b=None, all_=None, contrast=0.0, gamma=1.0, lift_=0.0, gain=1.0):
    """Build a 256*4 LUT (BGRA order for cairo surfaces) from per-channel functions f(x)->y on
    0..1, plus simple global contrast / gamma / lift / gain."""
    def mk(fn):
        out = []
        for i in range(256):
            x = i / 255.0
            if all_:
                x = all_(x)
            if fn:
                x = fn(x)
            x = lift_ + (gain - lift_) * x
            if gamma != 1.0:
                x = clamp(x) ** (1.0 / gamma)
            if contrast:
                x = 0.5 + (x - 0.5) * (1.0 + contrast)
            out.append(int(round(clamp(x) * 255)))
        return out
    return mk(b) + mk(g) + mk(r) + list(range(256))


def grade_lut(target, lut):
    """Apply a per-channel curve LUT (from make_lut) to the whole frame (~20 ms)."""
    surf = _target(target)
    surf.flush()
    w, h = surf.get_width(), surf.get_height()
    buf = surf.get_data()
    im = Image.frombuffer("RGBA", (w, h), buf, "raw", "RGBA", 0, 1)
    out = im.point(lut).tobytes()
    np.frombuffer(buf, np.uint8)[:] = np.frombuffer(out, np.uint8)
    surf.mark_dirty()


def fade(target, amount, color=(0, 0, 0)):
    """Fade toward a color: amount 0 = no change, 1 = solid color."""
    if amount <= 0:
        return
    _full_paint(_ctx(target), cairo.OPERATOR_OVER, color, clamp(amount))


def fade_alpha(t, duration, fade_in=1.0, fade_out=0.0):
    """Fade amount for a scene: 1 at t=0 -> 0 after fade_in; rising to 1 at the end over fade_out."""
    a = 0.0
    if fade_in > 0:
        a = max(a, 1.0 - core.ramp(t, 0.0, fade_in, "inout_sine"))
    if fade_out > 0:
        a = max(a, core.ramp(t, duration - fade_out, duration, "inout_sine"))
    return a


# ----------------------------------------------------------------------------------------
# particles -- all are pure functions of t (deterministic, no state)
# ----------------------------------------------------------------------------------------


def rain(cr, t, rect=(0, 0, core.W, core.H), n=260, speed=1500.0, angle=0.18, length=28.0,
         width=1.3, color="#9fb8d8", alpha=0.35, seed=0, wind=0.0):
    """Falling rain streaks inside rect=(x, y, w, h). angle = slant from vertical (rad).
    Layer it 2-3 times (far: thin/slow/faint, near: long/bright) for depth."""
    x0, y0, w, h = rect
    dx, dy = math.sin(angle), math.cos(angle)
    slant = h * dx / dy                       # horizontal drift over the rect height
    span = (h + 2 * length) / dy              # path length from above the top to below the bottom
    xs0 = x0 - max(0.0, slant)                # spawn band widened so slanted drops cover rect
    xw = w + abs(slant)
    cr.save()
    cr.rectangle(x0, y0, w, h)
    cr.clip()
    for i in range(n):
        sp = speed * (0.8 + 0.4 * hash01(i, seed + 1))
        d = (hash01(i, seed) * span + sp * t) % span
        px = xs0 + (hash01(i, seed + 2) * xw + wind * t) % xw + d * dx
        py = y0 - length + d * dy
        L = length * (0.7 + 0.6 * hash01(i, seed + 3))
        cr.move_to(px, py)
        cr.line_to(px + dx * L, py + dy * L)
    cr.set_line_width(width)
    cr.set_line_cap(cairo.LINE_CAP_ROUND)
    core.src(cr, color, alpha)
    cr.stroke()
    cr.restore()


def splashes(cr, t, rect, n=40, size=10.0, color="#b8cce6", alpha=0.5, seed=0, life=0.32):
    """Tiny rain splashes popping on a ground band rect=(x, y, w, h): a flattened ring that
    expands + 2 droplets, each slot re-randomized every cycle."""
    x0, y0, w, h = rect
    c = col(color)
    cr.save()
    cr.set_line_width(max(0.8, size * 0.12))
    for i in range(n):
        period = 0.45 + 0.5 * hash01(i, seed)
        ph = hash01(i, seed + 1) * period
        cyc = math.floor((t + ph) / period)
        u = ((t + ph) % period) / life
        if u >= 1.0:
            continue
        px = x0 + hash01(cyc * 131 + i, seed + 2) * w
        py = y0 + hash01(cyc * 131 + i, seed + 3) * h
        s = size * (0.5 + py / max(1.0, y0 + h) * 0.5) * (0.7 + 0.6 * hash01(i, seed + 4))
        a = alpha * (1.0 - u) ** 1.5
        cr.set_source_rgba(c[0], c[1], c[2], a)
        core.ellipse(cr, px, py, s * (0.3 + u), s * 0.28 * (0.3 + u))
        cr.stroke()
        for k in (-1, 1):
            hx = px + k * s * 0.6 * u
            hy = py - s * 1.6 * u * (1.0 - u) * 2.2
            cr.arc(hx, hy, max(0.6, s * 0.09), 0, TAU)
            cr.fill()
    cr.restore()


def dust(cr, t, rect, n=40, color="#fff2d0", alpha=0.5, size=(1.0, 2.6), seed=0, drift=(6.0, -3.0),
         twinkle=0.6, mask=None, additive=True):
    """Floating dust motes drifting in rect=(x, y, w, h). mask(x, y) -> 0..1 optional brightness
    (e.g. only visible inside a light shaft)."""
    x0, y0, w, h = rect
    c = col(color)
    cr.save()
    if additive:
        cr.set_operator(cairo.OPERATOR_ADD)
    for i in range(n):
        bx = hash01(i, seed) * w
        by = hash01(i, seed + 1) * h
        px = x0 + (bx + drift[0] * t + 14.0 * noise1(t * 0.13 + i, seed + 2)) % w
        py = y0 + (by + drift[1] * t + 10.0 * noise1(t * 0.11 + i * 1.3, seed + 3)) % h
        k = 1.0
        if mask is not None:
            k = mask(px, py)
            if k <= 0.01:
                continue
        tw = 1.0 - twinkle * (0.5 + 0.5 * math.sin(t * (1.0 + 2.0 * hash01(i, seed + 4)) + i))
        r = size[0] + (size[1] - size[0]) * hash01(i, seed + 5)
        cr.set_source_rgba(c[0], c[1], c[2], alpha * k * tw)
        cr.arc(px, py, r, 0, TAU)
        cr.fill()
    cr.restore()


def embers(cr, t, x, y, t0=0.0, n=24, life=1.6, spread=40.0, rise=110.0, color="#ffb347",
           hot="#fff2b0", size=2.4, seed=0, burst=0.25, scale=1.0, wind=0.0, alpha=1.0, solid=False):
    """Rising sparks/embers emitted from (x, y) starting at t0 (all born within `burst` s).
    Each flickers, drifts sideways, shrinks and cools from `hot` to `color`.

    solid=False: everything is additive (sparks over dark backgrounds: fires, night).
    solid=True: the spark cores are painted opaque (OVER) with a smaller additive halo, so
    warm sparks stay warm gold in front of a cool-coloured character (additive orange over
    teal turns pale green-white)."""
    if t < t0:
        return
    c1, c2 = col(hot), col(color)
    cr.save()
    cr.set_operator(cairo.OPERATOR_ADD)
    for i in range(n):
        born = t0 + burst * hash01(i, seed)
        lf = life * (0.6 + 0.6 * hash01(i, seed + 1))
        u = (t - born) / lf
        if u < 0 or u >= 1:
            continue
        ang = -math.pi / 2 + (hash01(i, seed + 2) - 0.5) * 1.6
        v0 = (0.6 + 0.8 * hash01(i, seed + 3))
        ease_u = 1.0 - (1.0 - u) ** 2
        px = x + (math.cos(ang) * spread * ease_u * v0 + wind * u + 10 * noise1(u * 3 + i, seed + 4)) * scale
        py = y + (math.sin(ang) * spread * 0.5 * ease_u * v0 - rise * u * v0) * scale
        fl = 0.65 + 0.35 * noise1(t * 14.0 + i * 7.0, seed + 5)
        a = alpha * fl * (1.0 - u) ** 1.2 * min(1.0, u * 8.0)
        cc = core.mix(c1, c2, min(1.0, u * 1.6))
        r = size * scale * (1.0 - 0.6 * u) * (0.7 + 0.6 * hash01(i, seed + 6))
        if solid:
            glow(cr, px, py, r * 3.2, c2, a * 0.22, True)
            cr.set_operator(cairo.OPERATOR_OVER)
            cr.set_source_rgba(cc[0], cc[1], cc[2], min(1.0, a * 1.15))
            cr.arc(px, py, max(0.6, r * 1.1), 0, TAU)
            cr.fill()
            cr.set_operator(cairo.OPERATOR_ADD)
            continue
        glow(cr, px, py, r * 4.0, cc, a * 0.35, True)
        cr.set_source_rgba(cc[0], cc[1], cc[2], a)
        cr.arc(px, py, max(0.5, r), 0, TAU)
        cr.fill()
    cr.restore()


def fireflies(cr, t, rect, n=14, color="#d8ff7a", size=2.2, seed=0, alpha=0.9, speed=1.0, halo=7.0):
    """Slow wandering fireflies with soft pulsing glows inside rect=(x, y, w, h)."""
    x0, y0, w, h = rect
    for i in range(n):
        px = x0 + w * (0.5 + 0.5 * core.fbm1(t * 0.05 * speed + i * 7.3, 2, seed + i))
        py = y0 + h * (0.5 + 0.5 * core.fbm1(t * 0.045 * speed + i * 3.9, 2, seed + 50 + i))
        pulse = 0.5 + 0.5 * math.sin(t * (1.1 + 0.9 * hash01(i, seed)) * TAU * 0.5 + i * 2.1)
        pulse = pulse ** 2
        a = alpha * (0.15 + 0.85 * pulse)
        glow(cr, px, py, size * halo, color, a * 0.5, True)
        glow(cr, px, py, size * 1.8, "#ffffe0", a, True)


def crumbs(cr, t, t0, x, y, n=8, seed=0, vx=(-60.0, 140.0), vy=(-220.0, -80.0), gravity=900.0,
           ground_y=None, size=3.0, color="#c89a5a", crust="#8a5a2b", spin=True, scale=1.0, release=0.12):
    """Crumbs tossed from (x, y) at t0: ballistic arcs, a small bounce on ground_y, then rest.
    Returns nothing; draw pigeons pecking at the landing spots via crumb_landings()."""
    if t < t0:
        return
    gy = ground_y if ground_y is not None else y + 200 * scale
    cc, kc = col(color), col(crust)
    for i in range(n):
        tb = t0 + release * hash01(i, seed)
        if t < tb:
            continue
        px, py, ang = _crumb_pos(t - tb, i, x, y, seed, vx, vy, gravity, gy, scale)
        s = size * scale * (0.6 + 0.8 * hash01(i, seed + 7))
        cr.save()
        cr.translate(px, py)
        cr.rotate(ang if spin else 0.0)
        pts = [(math.cos(k * TAU / 5) * s * (0.7 + 0.5 * hash01(i * 5 + k, seed + 8)),
                math.sin(k * TAU / 5) * s * (0.7 + 0.5 * hash01(i * 5 + k, seed + 9))) for k in range(5)]
        core.polygon(cr, pts)
        cr.set_source_rgb(*kc[:3])
        cr.fill_preserve()
        cr.translate(-s * 0.15, -s * 0.15)
        cr.scale(0.65, 0.65)
        cr.new_path()
        core.polygon(cr, pts)
        cr.set_source_rgb(*cc[:3])
        cr.fill()
        cr.restore()


def _crumb_pos(dt, i, x, y, seed, vx, vy, g, gy, scale):
    vx_i = (vx[0] + (vx[1] - vx[0]) * hash01(i, seed + 1)) * scale
    vy_i = (vy[0] + (vy[1] - vy[0]) * hash01(i, seed + 2)) * scale
    gg = g * scale
    # time to hit the ground
    disc = vy_i * vy_i + 2 * gg * (gy - y)
    t_hit = (-vy_i + math.sqrt(max(0.0, disc))) / gg if disc > 0 else 1e9
    if dt <= t_hit:
        return x + vx_i * dt, y + vy_i * dt + 0.5 * gg * dt * dt, dt * 9.0 * (hash01(i, seed + 3) - 0.5)
    # one small bounce, then rest
    xb = x + vx_i * t_hit
    b = dt - t_hit
    bvx, bvy = vx_i * 0.35, -abs(vy_i + gg * t_hit) * 0.22
    tb = -2 * bvy / gg
    if b <= tb:
        return xb + bvx * b, gy + bvy * b + 0.5 * gg * b * b, t_hit * 9.0 * (hash01(i, seed + 3) - 0.5)
    return xb + bvx * tb, gy, t_hit * 9.0 * (hash01(i, seed + 3) - 0.5)


def crumb_landings(t0, x, y, n=8, seed=0, vx=(-60.0, 140.0), vy=(-220.0, -80.0), gravity=900.0,
                   ground_y=None, scale=1.0, release=0.12):
    """[(x_rest, t_rest), ...] where each crumb from crumbs() comes to rest (for pecking pigeons)."""
    gy = ground_y if ground_y is not None else y + 200 * scale
    out = []
    for i in range(n):
        tb = t0 + release * hash01(i, seed)
        px, _, _ = _crumb_pos(30.0, i, x, y, seed, vx, vy, gravity, gy, scale)
        out.append((px, tb + 0.8))
    return out


def smoke(cr, t, t0, x, y, n=7, dur=2.6, rise=70.0, drift=(28.0, 0.0), size=9.0, color="#9aa0a8",
          alpha=0.55, seed=0, scale=1.0, spread=0.35):
    """A soft sigh-puff of smoke from (x, y) starting at t0: puffs expand, rise, curl and fade."""
    if t < t0 or t > t0 + dur + 0.6:
        return
    c = col(color)
    cr.save()
    for i in range(n):
        born = t0 + 0.32 * dur * (i / max(1, n - 1)) ** 1.3
        u = (t - born) / dur
        if u <= 0 or u >= 1:
            continue
        e = 1.0 - (1.0 - u) ** 2
        curl = math.sin(u * 4.0 + i * 1.7) * 10.0 * u
        px = x + (drift[0] * e + curl + (hash01(i, seed) - 0.5) * 20 * spread * e) * scale
        py = y + (drift[1] * e - rise * e * (0.7 + 0.5 * hash01(i, seed + 1))) * scale
        r = size * scale * (0.6 + 2.4 * e) * (0.8 + 0.4 * hash01(i, seed + 2))
        a = alpha * min(1.0, u * 6.0) * (1.0 - u) ** 1.4
        pat = cairo.RadialGradient(px, py, 0, px, py, r)
        pat.add_color_stop_rgba(0.0, c[0], c[1], c[2], a)
        pat.add_color_stop_rgba(0.55, c[0], c[1], c[2], a * 0.55)
        pat.add_color_stop_rgba(1.0, c[0], c[1], c[2], 0.0)
        cr.set_source(pat)
        cr.arc(px, py, r, 0, TAU)
        cr.fill()
    cr.restore()


def sparkle(cr, x, y, r, color="#ffffff", alpha=1.0, angle=0.0):
    """Four-point twinkle star (magic glints, glass highlights)."""
    c = col(color)
    cr.save()
    cr.translate(x, y)
    cr.rotate(angle)
    cr.set_operator(cairo.OPERATOR_ADD)
    cr.set_source_rgba(c[0], c[1], c[2], alpha)
    w = r * 0.18
    cr.move_to(-r, 0)
    cr.curve_to(-w, -w, -w, -w, 0, -r)
    cr.curve_to(w, -w, w, -w, r, 0)
    cr.curve_to(w, w, w, w, 0, r)
    cr.curve_to(-w, w, -w, w, -r, 0)
    cr.close_path()
    cr.fill()
    cr.restore()
    glow(cr, x, y, r * 1.4, color, alpha * 0.4)
