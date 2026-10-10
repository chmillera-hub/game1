"""Darkness and light for "ANGER" (BIBLE sections 3 "Light" and 7).

Every set and character is drawn LIT (full colour, as if well lit). `apply_darkness` then turns the
frame into a dark cave in SCREEN space: it multiplies the whole frame by a smooth per-channel light
map (ambient level + soft light holes) and adds a little additive glow around bright sources.

Frame recipe (in a scene's render):

    cam.apply(canvas, t);  env.draw_xxx(...);  char.draw(...)            # lit world, STAGE coords
    canvas.resetMatrix()
    light.apply_darkness(canvas, cam, ambient=0.06, lights=[light.torch_light(hx, hy, t)], t=t)
    cam.apply(canvas, t);  fx.draw_torch_flame(...); crawler eyes; fx.sparks(...)   # EMISSIVE, after
    canvas.resetMatrix();  light.vignette(canvas, 0.4)

Public API
    Light(x, y, radius=500, intensity=1.0, color="torch_light", kind="point", glow=0.0,
          glow_radius=None, glow_color=None, ry=None, screen=False)
        One light. x, y, radius in STAGE units (transformed by the camera) unless screen=True
        (then SCREEN pixels).  kind picks the falloff profile:
            "torch"  broad plateau + smooth tail (warm pool of light around a flame)
            "point"  generic smooth falloff                "fungus" soft, low, teal
            "spark"  tight bright core + short tail        "flash"  huge, flat, brief
        intensity: added light at the centre (>1 saturates a wider plateau; the map is soft-clipped).
        glow: strength of the ADDITIVE warm haze (0 = none) within glow_radius (default 0.32*radius).
        ry: vertical radius for elliptical pools (default = radius).
    torch_light(x, y, t, strength=1.0, radius=TORCH_RADIUS, seed=0) -> Light
        A hand-held torch at the FLAME position: radius / intensity / centre flicker with t
        (smooth layered noise, never strobing).  strength 0..1 fades it (0 -> radius 0).
    fungus_light(x, y, t, radius=140, strength=1.0, seed=0) -> Light      dim teal, slow breathing
    spark_light(x, y, t, amount=1.0, radius=260) -> Light                  hot stream of sparks (jittery)
    flash_light(x, y, age, strength=1.0, radius=1600, dur=0.45) -> Light|None
        A brief bright warm burst (door explosion, impact): age = seconds since the event.
    apply_darkness(canvas, cam, ambient=0.15, ambient_color="dark_ambient", lights=(), t=0.0,
                   lift=None, glow=1.0, sat=0.55)
        SCREEN space (identity matrix; it resets the matrix itself and restores it).
        cam: the scene's anim.core.Camera (rot + shake are honoured), or None = lights in screen px.
        ambient: brightness of unlit areas, 0..1, on a perceptual curve (see ambient_level):
            0.06 torch-only darkness (near black, faint navy shapes)
            0.12 after the torch dies: cold, dim, still readable (add the env fungi lights)
            1.0  fully lit (no darkening at all when there are no lights either)
        ambient_color: palette key / hex; the hue the darkness leans to (normalised; strength `sat`
            scaled by (1-ambient)).  lift: additive black-level lift in ambient_color (default
            0.55*(1-ambient)); glow: multiplier for all lights' additive haze.
        Cost ~6-10 ms at 720x1280 (light map 1/4 res in numpy, bilinear upscale, unscaled modulate).
    ambient_level(ambient) -> float        the multiplier used for unlit areas (ambient ** 0.5)
    light_at(x, y, ambient, lights, ambient_color="dark_ambient") -> (r, g, b) 0..1
        Light-map value at a STAGE point (no camera needed: radii in stage units) -- handy to set a
        character's Pose.light / tint so it matches the darkness (e.g. light=max(r,g,b)).
    vignette(canvas, amount=0.5, color="#05060A")      SCREEN space soft elliptical dark edges.

Notes
    * Lights never "add" over 1: lit areas reveal the lit scene (tinted by the light colour). The
      additive haze (glow) is what makes the air near a flame glow and over-brightens a little.
    * Smooth: the light map is computed in float, soft-clipped and quantised once; profiles all reach
      0 with zero slope at the radius, so there are no rings or bands.  No noise / grain anywhere.
    * The torch flame itself, sparks, embers and the crawler's eyes are EMISSIVE: draw them after
      apply_darkness.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import skia

from anim.core import clamp, noise1, rgb
from config import H, W

TORCH_RADIUS = 560.0          # stage units: the warm pool around Anger's torch at strength 1
_DS = 4                       # light map downscale factor
_LIN = skia.SamplingOptions(skia.FilterMode.kLinear)
_NEAR = skia.SamplingOptions()


# =========================================================================== lights
@dataclass
class Light:
    x: float
    y: float
    radius: float = 500.0
    intensity: float = 1.0
    color: str = "torch_light"
    kind: str = "point"
    glow: float = 0.0
    glow_radius: float | None = None
    glow_color: str | None = None
    ry: float | None = None
    screen: bool = False


def _fl(t, seed, *octaves):
    """Layered smooth noise in about [-1, 1]: octaves = (freq, amp), ..."""
    v = 0.0
    for i, (f, a) in enumerate(octaves):
        v += noise1(t * f, seed * 31 + i * 7 + 3) * a
    return v


def torch_light(x, y, t, strength=1.0, radius=TORCH_RADIUS, seed=0) -> Light:
    """Warm flickering torch light centred on the flame (stage coords)."""
    s = clamp(strength, 0.0, 2.0)
    fl = _fl(t, seed, (2.3, 0.55), (7.1, 0.30), (16.0, 0.15))          # -1..1, smooth
    r = radius * (0.35 + 0.65 * min(s, 1.0)) * (1.0 + 0.045 * fl) * max(s, 0.0) ** 0.25
    inten = 1.4 * min(s, 1.0) * (1.0 + 0.10 * fl)
    jx = _fl(t, seed + 5, (3.0, 0.7), (9.0, 0.3)) * 4.0
    jy = _fl(t, seed + 9, (3.4, 0.7), (11.0, 0.3)) * 5.0
    return Light(x + jx, y + jy - 10.0, r, inten, "torch_light", "torch", glow=0.32 * min(s, 1.0) * (1 + 0.12 * fl),
                 glow_radius=r * 0.26, glow_color="torch_flame")


def fungus_light(x, y, t, radius=140.0, strength=1.0, seed=0) -> Light:
    br = 0.85 + 0.15 * math.sin(t * 0.7 + seed * 1.7)
    return Light(x, y, radius, 0.55 * strength * br, "fungus", "fungus", glow=0.12 * strength * br,
                 glow_radius=radius * 0.45, glow_color="fungus")


def spark_light(x, y, t, amount=1.0, radius=260.0) -> Light:
    j = 0.75 + 0.25 * _fl(t, 77, (19.0, 0.6), (37.0, 0.4))
    return Light(x, y, radius * (0.8 + 0.2 * j), 1.1 * amount * j, "#FFD9A0", "spark", glow=0.6 * amount * j,
                 glow_radius=radius * 0.3, glow_color="torch_flame")


def flash_light(x, y, age, strength=1.0, radius=1600.0, dur=0.45) -> Light | None:
    if age is None or age < 0 or age > dur:
        return None
    k = (1.0 - age / dur) ** 2 * (min(1.0, age / 0.03) if age < 0.03 else 1.0)
    return Light(x, y, radius * (0.7 + 0.3 * age / dur), 1.6 * strength * k, "#FFE2B0", "flash",
                 glow=0.55 * strength * k, glow_radius=radius * 0.35, glow_color="#FFC27A")


# =========================================================================== helpers
_COLN_CACHE: dict = {}


def _norm_col(c, sat=1.0):
    """Colour normalised so its max channel is 1, then pulled toward white by (1-sat)."""
    key = (c, round(sat, 3))
    v = _COLN_CACHE.get(key)
    if v is None:
        r, g, b = rgb(c) if isinstance(c, str) else c[:3]
        m = max(r, g, b, 1)
        n = np.array([r / m, g / m, b / m], np.float32)
        v = 1.0 - (1.0 - n) * sat
        _COLN_CACHE[key] = v
    return v


def _lin_col(c):
    r, g, b = rgb(c) if isinstance(c, str) else c[:3]
    return np.array([r / 255.0, g / 255.0, b / 255.0], np.float32)


def ambient_level(ambient: float) -> float:
    """Multiplier for unlit areas (perceptual curve: 0.06 -> 0.24, 0.12 -> 0.35, 1 -> 1)."""
    return clamp(ambient) ** 0.5


def _cam_matrix(cam, t):
    m = skia.Matrix()
    if cam is None:
        return m, 1.0
    sx = sy = 0.0
    if cam.shake:
        sx = noise1(t * 9.0, 11) * cam.shake
        sy = noise1(t * 9.0, 23) * cam.shake
    m.preTranslate(W / 2, H / 2)
    m.preScale(cam.zoom, cam.zoom)
    if cam.rot:
        m.preRotate(cam.rot)
    m.preTranslate(-cam.cx + sx, -cam.cy + sy)
    return m, cam.zoom


def _profile(kind, d2):
    """Falloff 0..1 for squared normalised distance d2 (all reach 0 with zero slope at d=1)."""
    e = np.clip(1.0 - d2, 0.0, 1.0)
    if kind == "torch":
        return e ** 1.6 * (0.6 + 0.4 * np.exp(-4.0 * d2))
    if kind == "spark":
        return e * e * (0.25 + 0.75 * np.exp(-9.0 * d2))
    if kind == "flash":
        return e * (0.6 + 0.4 * e)
    if kind == "fungus":
        return e * e * e
    return e * e


def _glow_profile(d2):
    e = np.clip(1.0 - d2, 0.0, 1.0)
    return e * e * np.exp(-2.5 * d2)


def _softclip(L, knee=0.72):
    """C1 soft clip into [0, 1]: identity below knee, exponential shoulder above."""
    over = L > knee
    if np.any(over):
        k1 = 1.0 - knee
        L[over] = knee + k1 * (1.0 - np.exp(-(L[over] - knee) / k1))
    return L


class _Grid:
    def __init__(self, dw, dh):
        self.dw, self.dh = dw, dh
        self.lw, self.lh = (dw + _DS - 1) // _DS, (dh + _DS - 1) // _DS
        self.gx = ((np.arange(self.lw, dtype=np.float32) + 0.5) * _DS).astype(np.float32)
        self.gy = ((np.arange(self.lh, dtype=np.float32) + 0.5) * _DS).astype(np.float32)
        self.scratch = skia.Surface(dw, dh)
        self.bgra = np.empty((self.lh, self.lw, 4), np.uint8)
        self.bgra[..., 3] = 255


_GRIDS: dict = {}


def _grid(dw, dh) -> _Grid:
    g = _GRIDS.get((dw, dh))
    if g is None:
        g = _GRIDS[(dw, dh)] = _Grid(dw, dh)
    return g


def _to_image(arr_rgb01, alpha=None, out=None):
    """float (h, w, 3) -> BGRA premul skia Image (alpha 255 unless given as uint8 array)."""
    h, w = arr_rgb01.shape[:2]
    if out is None:
        out = np.empty((h, w, 4), np.uint8)
    q = np.clip(arr_rgb01 * 255.0 + 0.5, 0, 255).astype(np.uint8)
    out[..., 0] = q[..., 2]
    out[..., 1] = q[..., 1]
    out[..., 2] = q[..., 0]
    out[..., 3] = 255 if alpha is None else alpha
    return skia.Image.fromarray(out, colorType=skia.kBGRA_8888_ColorType, alphaType=skia.kPremul_AlphaType)


def _screen_lights(lights, cam, t):
    m, z = _cam_matrix(cam, t)
    out = []
    for L in lights:
        if L is None or L.radius <= 0 or (L.intensity <= 0 and L.glow <= 0):
            continue
        if L.screen:
            sx, sy, rs = L.x, L.y, 1.0
        else:
            p = m.mapXY(L.x, L.y)
            sx, sy, rs = p.x(), p.y(), z
        rx = L.radius * rs
        ry = (L.ry if L.ry is not None else L.radius) * rs
        out.append((L, sx, sy, rx, ry, rs))
    return out


def _accumulate(g: _Grid, ambient_rgb, slights):
    """Light map (lh, lw, 3) float32 and glow map bbox data."""
    Lm = np.empty((g.lh, g.lw, 3), np.float32)
    Lm[:] = ambient_rgb
    glows = []
    for (L, sx, sy, rx, ry, rs) in slights:
        if L.intensity > 0 and rx > 0.5 and ry > 0.5:
            x0 = max(0, int((sx - rx) / _DS) - 1)
            x1 = min(g.lw, int((sx + rx) / _DS) + 2)
            y0 = max(0, int((sy - ry) / _DS) - 1)
            y1 = min(g.lh, int((sy + ry) / _DS) + 2)
            if x1 > x0 and y1 > y0:
                dx = (g.gx[x0:x1] - sx) / rx
                dy = (g.gy[y0:y1] - sy) / ry
                d2 = dx[None, :] * dx[None, :] + dy[:, None] * dy[:, None]
                prof = _profile(L.kind, d2) * L.intensity
                c = _norm_col(L.color, 0.8)
                Lm[y0:y1, x0:x1] += prof[..., None] * c
        if L.glow > 0:
            gr = (L.glow_radius if L.glow_radius is not None else L.radius * 0.32) * rs
            if gr > 1.0:
                glows.append((sx, sy, gr, L.glow, L.glow_color or L.color))
    return Lm, glows


def apply_darkness(canvas, cam, ambient=0.15, ambient_color="dark_ambient", lights=(), t=0.0,
                   lift=None, glow=1.0, sat=0.55):
    """Darken the (already drawn, lit) frame except around lights. SCREEN space. See module doc."""
    ambient = clamp(ambient)
    info = canvas.imageInfo()
    dw, dh = info.width(), info.height()
    if dw <= 0 or dh <= 0:
        dw, dh = W, H
    slights = _screen_lights(lights or (), cam, t)
    canvas.save()
    canvas.resetMatrix()
    lvl = ambient_level(ambient)
    tint = _norm_col(ambient_color, sat * (1.0 - ambient))
    amb = (lvl * tint).astype(np.float32)
    if ambient >= 0.999 and not slights:
        canvas.restore()
        return
    g = _grid(dw, dh)
    Lm, glows = _accumulate(g, amb, slights)
    _softclip(Lm)
    if float(Lm.min()) < 0.998:
        img = _to_image(Lm, out=g.bgra)
        sc = g.scratch.getCanvas()
        sc.drawImageRect(img, skia.Rect(0, 0, dw, dh), _LIN, skia.Paint())   # opaque: src-over == src (fast path)
        snap = g.scratch.makeImageSnapshot()
        pm = skia.Paint()
        pm.setBlendMode(skia.BlendMode.kModulate)
        canvas.drawImage(snap, 0, 0, _NEAR, pm)
    # black-level lift (cold air), additive: a stretched 2x2 premul image with alpha 0 (src-over == add)
    lf = (0.55 * (1.0 - ambient)) if lift is None else lift
    if lf > 0.004:
        c = _lin_col(ambient_color) * lf
        q = tuple(int(v * 255 + 0.5) for v in c)
        if max(q) > 0:
            canvas.drawImageRect(_lift_image(q), skia.Rect(0.5, 0.5, 1.5, 1.5), skia.Rect(0, 0, dw, dh),
                                 _NEAR, skia.Paint())
    # additive haze around bright sources (cached sprite blits; premul alpha 0 == additive)
    if glow > 0:
        for (sx, sy, gr, ga, gc) in glows:
            _haze(canvas, sx, sy, gr, gc, ga * glow)
    canvas.restore()


_SPR: dict = {}
_LIFT: dict = {}


def _lift_image(q):
    img = _LIFT.get(q)
    if img is None:
        arr = np.zeros((2, 2, 4), np.uint8)
        arr[..., 0], arr[..., 1], arr[..., 2] = q[2], q[1], q[0]
        img = _LIFT[q] = skia.Image.fromarray(arr, colorType=skia.kBGRA_8888_ColorType,
                                              alphaType=skia.kPremul_AlphaType)
    return img


def _haze_sprite(color):
    img = _SPR.get(color)
    if img is None:
        n = 128
        yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
        d2 = (((xx - (n - 1) / 2) ** 2 + (yy - (n - 1) / 2) ** 2) / (n / 2) ** 2)
        prof = _glow_profile(d2)
        c = _lin_col(color)
        rgbf = c[None, None, :] * prof[..., None]
        img = _to_image(rgbf, alpha=np.zeros((n, n), np.uint8))
        _SPR[color] = img
    return img


def _haze(canvas, x, y, r, color, a):
    if a <= 0.003 or r <= 0.5:
        return
    p = skia.Paint()
    p.setAlphaf(clamp(a))
    canvas.drawImageRect(_haze_sprite(color), skia.Rect(x - r, y - r, x + r, y + r), _LIN, p)


def light_at(x, y, ambient, lights, ambient_color="dark_ambient", sat=0.55):
    """(r, g, b) 0..1 light-map value at STAGE point (x, y) (stage-unit radii, no camera)."""
    ambient = clamp(ambient)
    acc = ambient_level(ambient) * _norm_col(ambient_color, sat * (1.0 - ambient))
    acc = acc.astype(np.float64).copy()
    for L in lights or ():
        if L is None or L.radius <= 0:
            continue
        ry = L.ry if L.ry is not None else L.radius
        d2 = ((x - L.x) / L.radius) ** 2 + ((y - L.y) / ry) ** 2
        if d2 < 1.0:
            acc += float(_profile(L.kind, np.array(d2))) * L.intensity * _norm_col(L.color, 0.8)
    arr = _softclip(acc.astype(np.float32).reshape(1, 3))
    return tuple(float(v) for v in arr.reshape(3))


# =========================================================================== vignette
_VIG: dict = {}


def _vig_assets(dw, dh, color):
    key = (dw, dh, color)
    v = _VIG.get(key)
    if v is None:
        ky = dh / dw * 0.80
        m = skia.Matrix()
        m.setScale(1.0, ky, dw / 2, dh / 2)
        R = dw * 0.78 * 1.25
        stops = (0.0, 0.42, 0.66, 0.85, 1.0, 1.25)
        alph = (0.0, 0.0, 0.25, 0.6, 0.86, 1.0)
        r_, g_, b_ = rgb(color)
        cols = [skia.Color(r_, g_, b_, int(255 * a)) for a in alph]
        sh = skia.GradientShader.MakeRadial((dw / 2, dh / 2), R, cols, [s / 1.25 for s in stops],
                                            skia.TileMode.kClamp, 0, m)
        r0 = R * 0.42 / 1.25 * 0.995
        path = skia.Path()
        path.addRect(skia.Rect(0, 0, dw, dh))
        path.addOval(skia.Rect(dw / 2 - r0, dh / 2 - r0 * ky, dw / 2 + r0, dh / 2 + r0 * ky))
        path.setFillType(skia.PathFillType.kEvenOdd)
        v = _VIG[key] = (sh, path)
    return v


def vignette(canvas, amount=0.5, color="#05060A"):
    """SCREEN space soft dark elliptical edges (amount 0..1). Resets/restores the matrix.
    The gradient is rendered once into a full-frame image (cached) -> ~1-2 ms per call."""
    if amount <= 0.002:
        return
    info = canvas.imageInfo()
    dw, dh = (info.width(), info.height()) if info.width() > 0 else (W, H)
    key = ("img", dw, dh, color)
    img = _VIG.get(key)
    if img is None:
        sh, path = _vig_assets(dw, dh, color)
        surf = skia.Surface(dw, dh)
        cc = surf.getCanvas()
        cc.clear(skia.ColorTRANSPARENT)
        p = skia.Paint(AntiAlias=True)
        p.setShader(sh)
        p.setDither(True)
        cc.drawPath(path, p)
        img = _VIG[key] = surf.makeImageSnapshot()
    p = skia.Paint()
    p.setAlphaf(clamp(amount))
    canvas.save()
    canvas.resetMatrix()
    canvas.drawImage(img, 0, 0, _NEAR, p)
    canvas.restore()
