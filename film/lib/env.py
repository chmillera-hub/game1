"""env.py -- THE ENVIRONMENT KIT: painterly storybook-medieval backgrounds (no outlines).

    from film.lib import env, fx
    def setup():
        M = env.MARGIN                                         # w=2100 h=1240 x=-90 y=-80
        return {"sky": fx.Layer(lambda cr: env.draw_sky(cr, kind="dusk", horizon=620), opaque=True, **M),
                "far": fx.Layer(lambda cr: (env.draw_castle_hill(cr, 1350, 560, 0.8, kind="dusk"),
                                            env.draw_hills(cr, base_y=700, kind="dusk")), blur=3, res=0.5, **M),
                "garden": fx.Layer(draw_my_garden, **M),
                "tree": env.OakTree(300, 900, 1.0, kind="dusk"),          # sways: draw per frame
                "light": fx.LightLayer()}
    def draw(cr, t, st):
        with cam.view(cr, 0.15): st["sky"].paint(cr)
        with cam.view(cr, 0.4): st["far"].paint(cr)
        with cam.view(cr, 1.0): st["garden"].paint(cr); st["tree"].draw(cr, t)

Conventions:
  * Environments get NO outlines (STYLE.md): shapes, value, colour, texture and blur carry the
    depth. Backgrounds sit in a narrower value band than the cast and lose saturation and
    contrast with distance (atmospheric perspective: `haze_toward`, `draw_haze`, `draw_mist`).
  * Every draw function takes WORLD coordinates (px, y down) and draws only into the context;
    static art belongs in an `fx.Layer` built in setup() (`env.layer(fn, blur=..)` adds the
    standard margin, so camera moves never reveal an edge). Animated pieces are pure functions
    of `t`: `StarField.draw`, `OakTree.draw`, `Rain.draw`, `puddle_ripples`, `Mist.draw`.
  * Palettes: `PALETTES[kind]` for kind in "night", "rain_night", "dusk", "golden",
    "blue_hour", "evening" (S5 grey-blue), "washhouse": sky stops, haze, far/mid/near land,
    foliage, stone, plaster, timber, roofs, window glow. Pass kind= or your own colours.
  * Texture: `texture(cr, kind, alpha, scale)` paints a seamless watercolour/plaster/stone
    granulation (an FFT-noise tile, cached) over the current clip -- the painterly finish.
  * Keep the bottom 180 px of the frame free of anything the eye must read (captions).
  * Period rule (SPEC 0.1): candlelight and moonlight only, wood, plaster, stone, thatch,
    leaded diamond-pane windows; nothing modern.
"""

import functools
import math

import cairocffi as cairo
import numpy as np

from . import core, fx
from .core import clamp, lerp, smooth, TAU

__all__ = [
    "MARGIN", "PALETTES", "palette", "layer", "texture", "haze_toward",
    "draw_sky", "StarField", "draw_moon", "draw_clouds", "draw_castle_hill", "draw_hills", "draw_haze", "draw_mist",
    "Mist", "draw_house", "draw_street_row", "draw_roofline", "draw_stone_wall", "draw_arch", "draw_vaulted_hall",
    "draw_cobbles", "draw_wet_reflections", "draw_puddle", "puddle_ripples", "draw_gravel_path", "draw_grass",
    "draw_hedge", "draw_flower_bed", "OakTree", "draw_oak", "Rain", "draw_ground_shadow",
]

MARGIN = dict(w=2100, h=1240, x=-90, y=-80)     # fx.Layer margin so camera moves never show an edge


def layer(draw, blur=0.0, res=1.0, opaque=False, **kw):
    """fx.Layer with the standard margin (MARGIN) unless overridden."""
    m = dict(MARGIN)
    m.update(kw)
    return fx.Layer(draw, blur=blur, res=res, opaque=opaque, **m)


# ----------------------------------------------------------------------------------------
# palettes
# ----------------------------------------------------------------------------------------

PALETTES = {
    # S3 rainy night street and S8 (with stars): deep navy, cold, quiet
    "night": dict(sky=["#070b18", "#0e1630", "#1a2645", "#2a3a5c"], cloud=("#1a2442", "#33456c"), haze="#26355a",
                  far="#141c34", mid="#111a2e", near="#0c1322", ground="#151d2e", foliage=("#0c1a1e", "#16302e", "#24443c"),
                  stone="#2e3648", plaster=("#3c4458", "#45434a", "#40404e"), timber="#211e24", roof="#1a1e2e",
                  window="#ffc56b", window_dark="#141b2a", star=True, moon=True),
    "rain_night": dict(sky=["#090e1c", "#111a32", "#1c2844", "#2c3b58"], cloud=("#151e36", "#2a3858"), haze="#2c3b5c",
                       far="#151d33", mid="#121a2d", near="#0d1424", ground="#141c2c",
                       foliage=("#0c1a1e", "#16302e", "#24443c"), stone="#2c3446",
                       plaster=("#3a4258", "#43414a", "#3e3e4e"), timber="#201d24", roof="#181c2c",
                       window="#ffbf5f", window_dark="#131a28", star=False, moon=False),
    # S6 dusk garden: violet above, peach at the horizon, the first warmth
    "dusk": dict(sky=["#3e3768", "#6c5a8e", "#b582a2", "#f0b496", "#f8d3a8"], cloud=("#8a6a96", "#f6c6a0"),
                 haze="#c99aa8", far="#8c7a9e", mid="#6c6688", near="#4a4a68", ground="#5a5470",
                 foliage=("#2a3344", "#3e5a50", "#8c9a62"), stone="#8a7c8c", plaster=("#d8c4b8", "#e0c8a8", "#c8b8c4"),
                 timber="#4a3438", roof="#6a4a5a", window="#ffd08a", window_dark="#4a3c58", star=False, moon=False),
    # S7 golden hour
    "golden": dict(sky=["#5e7aa8", "#9aa0b4", "#e2b07a", "#f8cf8a", "#fde3a8"], cloud=("#b88a7a", "#ffe0a8"),
                   haze="#e8c08a", far="#a8907a", mid="#8a7a5e", near="#5e5a40", ground="#7a6a48",
                   foliage=("#2e3e24", "#556e32", "#b4b452"), stone="#a89478", plaster=("#ecd8b0", "#f0d0a0", "#e0c8b0"),
                   timber="#5a3a26", roof="#8a5a3a", window="#ffe0a0", window_dark="#6a5040", star=False, moon=False),
    # S7 later: blue hour, the first stars
    "blue_hour": dict(sky=["#141c44", "#25336a", "#4a5a92", "#8a86b4", "#b8a4bc"], cloud=("#3a4a7a", "#9a94c0"),
                      haze="#6a6e9e", far="#3e4670", mid="#2e3658", near="#1e2442", ground="#2a304a",
                      foliage=("#141e2a", "#22323e", "#36484e"), stone="#5a5e7a", plaster=("#8a8aa6", "#9a92a0", "#8a8698"),
                      timber="#262434", roof="#2e3248", window="#ffd38a", window_dark="#2a2e48", star=True, moon=False),
    # S5 town square at evening: grey-blue stone, cold
    "evening": dict(sky=["#2c3650", "#46536e", "#6e7c94", "#98a2b2", "#b4b8c0"], cloud=("#4a566e", "#a8b0bc"),
                    haze="#8a96aa", far="#5a6680", mid="#465068", near="#323a50", ground="#4a5266",
                    foliage=("#1e2a30", "#2e3e44", "#46565a"), stone="#6a7286", plaster=("#a8aab4", "#b4ac9c", "#a4a2ae"),
                    timber="#2e2a2e", roof="#3e4458", window="#c8e6ff", window_dark="#2a3244", star=False, moon=False),
    # S1 interior: cold sickly teal
    "washhouse": dict(sky=["#0a1626", "#16304a", "#1e3a52"], cloud=("#18303a", "#2a4a50"), haze="#3a6a66",
                      far="#1d3436", mid="#162a2c", near="#0f1e20", ground="#12201f", foliage=("#0f2020", "#1a3030", "#26403c"),
                      stone="#33585a", plaster=("#4a6a68", "#4e6660", "#46605e"), timber="#1a2422", roof="#1e2e30",
                      window="#9fffe0", window_dark="#0a1618", star=False, moon=True),
}


def palette(kind):
    """The colour dict for a scene kind (see PALETTES); a dict is passed through."""
    if isinstance(kind, dict):
        return kind
    return PALETTES.get(kind, PALETTES["dusk"])


def haze_toward(c, haze, k):
    """Atmospheric perspective: blend colour c toward the haze colour by k (0 near .. 1 far),
    and lose saturation on the way."""
    return core.saturate(core.mix(c, haze, k), -0.35 * k)


# ----------------------------------------------------------------------------------------
# texture: seamless painterly granulation (FFT noise tiles, cached)
# ----------------------------------------------------------------------------------------

@functools.lru_cache(maxsize=16)
def _noise_tile(n, beta, seed):
    """A seamless (periodic) fractal noise tile in [-1, 1]: random phases on a 1/f^beta
    spectrum, inverse FFT -- it wraps perfectly, so it can REPEAT without seams."""
    rng = np.random.default_rng(seed)
    kx = np.fft.fftfreq(n)[:, None]
    ky = np.fft.rfftfreq(n)[None, :]
    k = np.sqrt(kx * kx + ky * ky)
    k[0, 0] = 1.0
    amp = k ** (-beta / 2.0)
    amp[0, 0] = 0.0
    phase = rng.uniform(0.0, TAU, amp.shape)
    img = np.fft.irfft2(amp * np.exp(1j * phase), s=(n, n))
    img = img / (img.std() * 2.2 + 1e-9)
    return np.clip(img, -1.0, 1.0).astype(np.float32)


_TEX_KINDS = {
    # name: [(beta, weight, seed)], light/dark strengths
    "paint": ([(2.2, 0.65, 1), (0.8, 0.35, 2)], 0.55, 1.0),       # watercolour wash: soft blooms + granulation
    "plaster": ([(1.6, 0.6, 3), (0.4, 0.4, 4)], 0.7, 1.0),        # lime plaster: blotchy + fine speckle
    "stone": ([(1.3, 0.7, 5), (0.3, 0.3, 6)], 0.5, 1.0),          # weathered stone
    "foliage": ([(1.0, 0.6, 7), (0.2, 0.4, 8)], 0.8, 1.0),        # leaf dapple
    "grain": ([(0.2, 1.0, 9)], 0.8, 1.0),                         # fine speckle only
    "wood": ([(1.4, 1.0, 10)], 0.4, 1.0),                         # stretched later into grain
}


@functools.lru_cache(maxsize=16)
def _tex_surface(kind, n=512):
    """RGBA tile for `kind`: dark specks (black, alpha) where the noise is low, light specks
    (white, alpha) where it is high -- painting it over any colour granulates that colour."""
    spec, k_light, k_dark = _TEX_KINDS.get(kind, _TEX_KINDS["paint"])
    v = np.zeros((n, n), np.float32)
    for beta, wgt, sd in spec:
        v += _noise_tile(n, beta, sd) * wgt
    v = np.clip(v, -1.0, 1.0)
    a = np.where(v > 0, v * k_light, -v * k_dark)
    a = np.clip(a, 0.0, 1.0)
    arr = np.zeros((n, n, 4), np.uint8)
    arr[..., 3] = (a * 255).astype(np.uint8)
    lum = np.where(v > 0, a * 255, 0).astype(np.uint8)       # premultiplied white for the light specks
    arr[..., 0] = lum
    arr[..., 1] = lum
    arr[..., 2] = lum
    data = bytearray(arr.tobytes())
    surf = cairo.ImageSurface.create_for_data(data, cairo.FORMAT_ARGB32, n, n, n * 4)
    return surf, data


def texture(cr, kind="paint", alpha=0.18, scale=1.0, angle=0.0, offset=(0.0, 0.0), sx=1.0, sy=1.0):
    """Paint the seamless `kind` texture ("paint", "plaster", "stone", "foliage", "grain",
    "wood") over the current clip at `alpha` -- the painterly granulation on any flat shape.
    scale/sx/sy stretch the features (wood: sx=4, sy=0.25). Clip first, e.g.:
        cr.save(); path...; cr.clip(); env.texture(cr, "plaster", 0.2); cr.restore()"""
    if alpha <= 0:
        return
    surf, _keep = _tex_surface(kind)
    pat = cairo.SurfacePattern(surf)
    pat.set_extend(cairo.EXTEND_REPEAT)
    pat.set_filter(cairo.FILTER_BILINEAR)
    m = cairo.Matrix()
    m.translate(offset[0], offset[1])
    if angle:
        m.rotate(angle)
    m.scale(scale * sx, scale * sy)
    m.invert()
    pat.set_matrix(m)
    cr.save()
    cr.set_source(pat)
    cr.paint_with_alpha(alpha)
    cr.restore()


def _fill_tex(cr, color, kind=None, alpha=0.2, scale=1.0, **kw):
    """Fill the current path with a solid colour, then granulate it (path consumed)."""
    core.src(cr, color)
    if kind is None:
        cr.fill()
        return
    cr.save()
    cr.fill_preserve()
    cr.clip()
    texture(cr, kind, alpha, scale, **kw)
    cr.restore()
    cr.new_path()


def _wobbly(pts, amp, seed, freq=0.05):
    """Displace a polyline/polygon by smooth noise (painterly hand-drawn edges)."""
    out = []
    for i, (x, y) in enumerate(pts):
        out.append((x + amp * core.noise1(x * freq + i * 0.01, seed), y + amp * core.noise1(x * freq + 7.3, seed + 1)))
    return out


# ----------------------------------------------------------------------------------------
# sky, clouds, stars, moon
# ----------------------------------------------------------------------------------------

def draw_sky(cr, x=-90.0, y=-80.0, w=2100.0, h=1240.0, kind="dusk", horizon=640.0, seed=0, clouds=True, stars=None,
             moon=None, sun=None, glow=None, texture_alpha=0.05):
    """A painterly sky filling (x, y, w, h): the palette's gradient down to the `horizon` line,
    a soft glow low in the sky (the sun's side at dusk/golden), cloud banks lit from below or the
    side, static stars and the moon on clear nights, and a whisper of watercolour granulation.

    kind: a PALETTES name or dict. stars/moon: None = the palette's default; moon=(mx, my, r)
    or True; sun=(sx, sy, r) for golden hour. Static: cache it (fx.Layer(..., opaque=True)) and
    add StarField.draw for twinkles."""
    P = palette(kind)
    stops = P["sky"]
    n = len(stops)
    span = max(1.0, horizon - y)
    pat = core.linear(0, y, 0, horizon, [(i / (n - 1), c) for i, c in enumerate(stops)])
    cr.rectangle(x, y, w, h)
    cr.set_source(pat)
    cr.fill()
    if horizon < y + h:
        core.src(cr, stops[-1])
        cr.rectangle(x, horizon, w, y + h - horizon)
        cr.fill()
    gx, gy = (sun[0], sun[1]) if sun else (x + w * 0.62, horizon - span * 0.04)
    gcol = glow or (stops[-1] if kind not in ("night", "rain_night", "washhouse") else stops[-2])
    if kind in ("dusk", "golden", "blue_hour", "evening"):
        cr.save()
        cr.translate(gx, gy)
        cr.scale(1.0, 0.42)
        rr = w * 0.55
        g = core.radial(0, 0, rr, [(0.0, core.alpha(core.tint(gcol, 0.25), 0.55)), (0.45, core.alpha(gcol, 0.25)),
                                    (1.0, core.alpha(gcol, 0.0))])
        cr.set_source(g)
        cr.arc(0, 0, rr, 0, TAU)
        cr.fill()
        cr.restore()
    show_stars = P.get("star") if stars is None else stars
    if show_stars:
        _static_stars(cr, x, y, w, horizon - y, seed, P)
    show_moon = P.get("moon") if moon is None else moon
    if show_moon:
        mx, my, mr = moon if isinstance(moon, tuple) else (x + w * 0.72, y + span * 0.28, 34.0)
        draw_moon(cr, mx, my, mr, kind)
    if sun:
        sx_, sy_, sr = sun
        fx.glow(cr, sx_, sy_, sr * 7.0, "#fff0c8", 0.45, additive=False)
        core.src(cr, "#fff6dc")
        core.circle(cr, sx_, sy_, sr)
        cr.fill()
    if clouds:
        draw_clouds(cr, x, y, w, horizon - y, kind, seed, light_from=(gx, gy))
    if texture_alpha > 0:
        cr.save()
        cr.rectangle(x, y, w, h)
        cr.clip()
        texture(cr, "paint", texture_alpha, 3.0)
        cr.restore()


def _static_stars(cr, x, y, w, h, seed, P):
    for i in range(int(w * h / 9000)):
        px = x + core.hash01(i, seed + 21) * w
        py = y + core.hash01(i, seed + 22) ** 1.4 * h * 0.9
        b = core.hash01(i, seed + 23)
        a = (0.25 + 0.6 * b) * (1.0 - (py - y) / max(h, 1.0)) ** 0.6
        core.src(cr, "#eef2ff", a)
        core.circle(cr, px, py, 0.6 + 1.0 * b * b)
        cr.fill()


def draw_moon(cr, x, y, r, kind="night", glow=0.5):
    """A storybook moon: a soft halo, a pale disc with faint mare blotches."""
    fx.glow(cr, x, y, r * 6.0, "#b8c8f0", 0.35 * glow, additive=False)
    core.src(cr, "#f2f0e2")
    core.circle(cr, x, y, r)
    cr.fill()
    core.src(cr, "#c8c8c0", 0.35)
    for (dx, dy, rr) in ((-0.3, -0.2, 0.28), (0.25, 0.15, 0.2), (0.05, -0.45, 0.14), (-0.1, 0.35, 0.18)):
        core.circle(cr, x + dx * r, y + dy * r, rr * r)
    cr.fill()


class StarField:
    """Twinkling stars drawn per frame (cheap): n stars in rect (x, y, w, h), each with its own
    slow twinkle; a few bright ones get a four-point glint. draw(cr, t, alpha)."""

    def __init__(self, rect, n=120, seed=0, color="#eef2ff"):
        x, y, w, h = rect
        self.stars = []
        for i in range(n):
            b = core.hash01(i, seed + 31)
            self.stars.append((x + core.hash01(i, seed + 32) * w, y + core.hash01(i, seed + 33) ** 1.3 * h,
                               0.5 + 1.3 * b * b, b, core.hash01(i, seed + 34) * TAU, 0.6 + 1.6 * core.hash01(i, seed + 35)))
        self.color = color

    def draw(self, cr, t, alpha=1.0):
        c = core.col(self.color)
        cr.save()
        cr.set_operator(cairo.OPERATOR_ADD)
        for (sx, sy, r, b, ph, f) in self.stars:
            tw = 0.55 + 0.45 * math.sin(t * f + ph)
            cr.set_source_rgba(c[0], c[1], c[2], alpha * (0.25 + 0.75 * b) * tw)
            cr.arc(sx, sy, r, 0, TAU)
            cr.fill()
        cr.restore()
        for (sx, sy, r, b, ph, f) in self.stars:
            if b > 0.93:
                fx.sparkle(cr, sx, sy, 5.0 + 4.0 * b, self.color, alpha * 0.5 * (0.6 + 0.4 * math.sin(t * f * 0.7 + ph)))


def _cloud(cr, cx, cy, w, h, seed, lit, shadow, light_dx=0.0, light_dy=-1.0, alpha=1.0):
    """One painterly cloud bank with a soft flat base: a union of round puffs (big in the
    middle, small at the ends) cut at its base line; the shadow tone first, then the lit tone
    from puffs nudged toward the light, then a darker belly. Soften it with the layer's blur."""
    puffs = []
    n = max(4, int(w / (h * 0.55)))
    for i in range(n):
        u = (i + 0.5) / n
        bump = math.sin(math.pi * u) ** 0.8
        pr = h * (0.22 + 0.42 * bump) * (0.8 + 0.4 * core.hash01(i, seed + 1))
        px = cx - w / 2 + u * w + core.jitter(i, w * 0.03, seed)
        py = cy - pr * (0.55 + 0.35 * bump) + core.jitter(i, h * 0.06, seed + 2)
        puffs.append((px, py, pr))
    for i in range(n // 2):                                   # a second, higher tier of puffs
        u = 0.25 + 0.5 * core.hash01(i, seed + 3)
        pr = h * (0.25 + 0.2 * core.hash01(i, seed + 4))
        puffs.append((cx - w / 2 + u * w, cy - h * 0.62 - pr * 0.3, pr))

    def add(dx=0.0, dy=0.0, k=1.0):
        cr.new_path()
        for (px, py, pr) in puffs:
            cr.new_sub_path()
            cr.arc(px + dx, py + dy, pr * k, 0, TAU)

    cr.save()
    cr.rectangle(cx - w, cy - h * 3, w * 2, h * 3)          # the flat base: nothing below cy
    cr.clip()
    cr.push_group()
    add()
    core.src(cr, shadow)
    cr.fill()
    add()
    cr.clip()
    add(light_dx * h * 0.1, light_dy * h * 0.1, 0.98)
    core.src(cr, core.mix(shadow, lit, 0.55))
    cr.fill()
    add(light_dx * h * 0.24, light_dy * h * 0.24, 0.95)
    core.src(cr, lit)
    cr.fill()
    cr.pop_group_to_source()
    cr.paint_with_alpha(alpha)
    cr.rectangle(cx - w, cy - h * 0.3, w * 2, h * 0.3)      # the shadowed belly
    cr.set_source(core.linear(0, cy - h * 0.3, 0, cy, [core.alpha(shadow, 0.0), core.alpha(shadow, 0.45 * alpha)]))
    cr.fill()
    cr.restore()


def _streak(cr, x0, y0, L, th, lit, shadow, alpha, seed):
    """A long thin stratus streak: a tapered ribbon in the shadow tone with a lit upper edge."""
    pts = [(x0 + L * k / 6, y0 + 3.0 * math.sin(k * 1.3 + seed) - 2.0 * k * (k - 6) / 9) for k in range(7)]
    core.tapered(cr, pts, 1.0, 1.0, profile=lambda s_: 1.0 + th * math.sin(math.pi * s_) ** 0.8)
    core.src(cr, shadow, alpha)
    cr.fill()
    core.tapered(cr, [(px, py - th * 0.22) for px, py in pts], 1.0, 1.0,
                 profile=lambda s_: 0.5 + th * 0.45 * math.sin(math.pi * s_) ** 1.2)
    core.src(cr, lit, alpha)
    cr.fill()


def draw_clouds(cr, x, y, w, h, kind="dusk", seed=0, light_from=None, n=None, alpha=1.0, streaks=None):
    """Clouds across the sky band (x, y, w, h): a few cumulus banks and long stratus streaks,
    lit from `light_from` (the sun's or moon's side; below the clouds at dusk). rain_night is
    an overcast lid of heavy cloud. Soft once the sky layer is blurred."""
    P = palette(kind)
    shadow, lit = P["cloud"]
    horizon_c = P["sky"][-1]
    if kind == "rain_night":
        # overcast: a heavy, low-contrast deck of big soft masses, darker underneath, a few
        # thinner patches where the hidden moon silvers the edges
        for i in range(16):
            u = core.hash01(i, seed + 5)
            cw = w * (0.18 + 0.22 * core.hash01(i, seed + 6))
            ch = cw * (0.16 + 0.1 * core.hash01(i, seed + 7))
            cy = y + h * (0.05 + 0.62 * core.hash01(i, seed + 8))
            k = (cy - y) / max(1.0, h)
            _cloud(cr, x + u * w, cy, cw, ch, seed + i * 3, core.mix(lit, horizon_c, 0.35 * k + 0.1 * (i % 3)),
                   core.mix(shadow, horizon_c, 0.3 * k), 0.15, -1.0, alpha * (0.55 + 0.25 * core.hash01(i, seed + 9)))
        for i in range(6):
            _streak(cr, x + w * core.hash01(i, seed + 10) - w * 0.1, y + h * (0.5 + 0.45 * core.hash01(i, seed + 11)),
                    w * (0.3 + 0.3 * core.hash01(i, seed + 12)), 12.0, core.mix(lit, horizon_c, 0.4),
                    core.mix(shadow, horizon_c, 0.5), alpha * 0.5, seed + i)
        return
    n = 4 if n is None else n
    n_streak = 7 if streaks is None else streaks
    for i in range(n):
        u = (i + 0.5) / n + core.jitter(i, 0.08, seed + 41)
        v = core.hash01(i, seed + 42)
        cw = w * (0.12 + 0.12 * core.hash01(i, seed + 43))
        ch = cw * (0.20 + 0.08 * core.hash01(i, seed + 44))
        cx = x + u * w
        cy = y + h * (0.22 + 0.5 * v)
        k = (cy - y) / max(1.0, h)
        sh = core.mix(shadow, horizon_c, 0.3 * k)
        lt = core.mix(lit, horizon_c, 0.2 * k)
        ldx, ldy = 0.0, -1.0
        if light_from is not None:
            ldx, ldy = core.normalize((light_from[0] - cx, light_from[1] - cy))
        _cloud(cr, cx, cy, cw, ch, seed + i * 7, lt, sh, ldx, ldy, alpha * (0.82 - 0.25 * k))
    for i in range(n_streak):
        sy = y + h * (0.35 + 0.6 * core.hash01(i, seed + 51))
        sx = x + w * (core.hash01(i, seed + 52) * 1.1 - 0.15)
        L = w * (0.18 + 0.3 * core.hash01(i, seed + 53))
        k = (sy - y) / max(1.0, h)
        _streak(cr, sx, sy, L, 7.0 + 10.0 * core.hash01(i, seed + 54), core.mix(lit, horizon_c, 0.2 * k),
                core.mix(shadow, horizon_c, 0.45 * k), alpha * (0.55 + 0.3 * core.hash01(i, seed + 55)), seed + i)


# ----------------------------------------------------------------------------------------
# the castle on the hill, rolling hills, haze and mist
# ----------------------------------------------------------------------------------------

def _tower(cr, x, base, w, top, roof=None, crenel=True, roof_h=None):
    """A tower body (round-ish) with crenellations or a conical roof, as path pieces (filled
    by the caller in one go)."""
    cr.rectangle(x - w / 2, top, w, base - top)
    if roof == "cone":
        rh = roof_h if roof_h is not None else w * 1.4
        cr.move_to(x - w / 2 - 4.0, top + 1.0)
        cr.curve_to(x - w * 0.2, top - rh * 0.4, x - 2.0, top - rh * 0.8, x, top - rh)
        cr.curve_to(x + 2.0, top - rh * 0.8, x + w * 0.2, top - rh * 0.4, x + w / 2 + 4.0, top + 1.0)
        cr.close_path()
    elif crenel:
        m = max(4.0, w / 7.0)
        k = 0
        xx = x - w / 2
        while xx < x + w / 2 - 1e-6:
            if k % 2 == 0:
                cr.rectangle(xx, top - m * 0.9, min(m, x + w / 2 - xx), m * 0.9 + 1.0)
            xx += m
            k += 1


def draw_castle_hill(cr, x, y, scale=1.0, kind="dusk", seed=0, color=None, rim=None, windows=9, window_color=None,
                     window_alpha=None, banners=True, t=0.0, hill=True, hill_w=1100.0, hill_h=170.0, road=True,
                     light_dx=-0.6):
    """The castle on the hill, as a distant storybook silhouette: curtain walls, round towers
    with conical roofs and pennants, a tall keep with a spire, a gatehouse, a winding road, a
    few lit windows; a soft rim of light on the sky's bright side (light_dx < 0: the left).

    Anchor (x, y) = the castle's foot on the hilltop; the castle is ~360 x 290 at scale 1.0 and
    the hill spreads hill_w wide and hill_h down below it, with a broad crown the castle stands
    ON (its outer walls carry on down into the hill where the ground falls away). hill=False
    draws the castle alone, its foundations reaching 64 below the anchor: sink them into a
    ridge of draw_hills. Colours from the palette's "far" (silhouette) and "haze" (rim);
    window_color/alpha default by palette (lit at night). Static (banners are drawn at time
    t): put it in a blurred far Layer."""
    P = palette(kind)
    col = color or P["far"]
    rimc = rim or core.mix(P["haze"], P["sky"][-1], 0.5)
    wc = window_color or P["window"]
    wa = window_alpha if window_alpha is not None else (0.95 if kind in ("night", "rain_night", "blue_hour", "evening") else 0.5)
    ls = -1.0 if light_dx <= 0 else 1.0                      # which side the light comes from
    cr.save()
    cr.translate(x, y)
    cr.scale(scale, scale)
    j = lambda i, a: core.jitter(i, a, seed)               # noqa: E731
    towers = [  # (x, width, top, roof)
        (-152.0, 36.0, -118.0 + j(1, 8), "cone"), (-62.0, 50.0, -128.0 + j(2, 8), "crenel"),
        (36.0, 64.0, -178.0 + j(3, 10), "crenel"), (36.0, 26.0, -214.0 + j(3, 10), "cone"),
        (104.0, 28.0, -152.0 + j(4, 10), "cone"), (156.0, 38.0, -108.0 + j(5, 8), "cone"),
    ]

    def silhouette(dx=0.0, dy=0.0):
        cr.new_path()
        cr.translate(dx, dy)
        if hill:
            # the hill: a broad flat crown under the walls (the castle stands ON it, never
            # balanced on a peak), shoulders that round over, flanks falling away and a long
            # gentle slope past the foot (no edge where it meets the hills)
            top, half = 120.0, max(hill_w / 2, 330.0)
            pts = []
            for i in range(57):
                xx = -1.7 * half + 3.4 * half * i / 56
                a = abs(xx)
                if a <= top:
                    drop = 0.0
                elif a <= half:
                    drop = hill_h * ((a - top) / (half - top)) ** 1.45
                else:
                    drop = hill_h * (1.0 + 0.9 * (a - half) / half)
                drop += 6.0 * core.noise1(xx * 0.02, seed + 3) * clamp((a - top) / 120.0, 0.0, 1.0)
                pts.append((xx, 8.0 + drop))
            core.smooth_open(cr, pts)
            cr.line_to(pts[-1][0], hill_h + 500.0)
            cr.line_to(pts[0][0], hill_h + 500.0)
            cr.close_path()
        # the walls' foundations: where the ground falls away under the outer towers the walls
        # carry on down, battered (splayed a little), until the hill swallows them
        core.polygon(cr, [(-168.0, 0.0), (174.0, 0.0), (186.0, 64.0), (-180.0, 64.0)])
        # curtain wall
        cr.rectangle(-150.0, -64.0, 306.0, 72.0)
        xx = -150.0
        k = 0
        while xx < 156.0:
            if k % 2 == 0:
                cr.rectangle(xx, -71.0, 8.0, 8.0)
            xx += 8.0
            k += 1
        for (tx, tw, top, roof) in towers:
            _tower(cr, tx, 8.0, tw, top, roof if roof == "cone" else None, roof != "cone",
                   roof_h=tw * (1.9 if tw < 30 else 1.5))
        cr.translate(-dx, -dy)

    # the rim (lit side) then the body offset away from the light
    silhouette(2.0 * ls, -1.5)
    core.src(cr, rimc, 0.8)
    cr.fill()
    silhouette()
    cr.set_source(core.linear(0, -60.0, 0, hill_h + 10.0, [col, col, haze_toward(col, P["haze"], 0.55)]))
    cr.fill()
    cr.save()
    silhouette()
    cr.clip()
    texture(cr, "stone", 0.12, 0.6)
    # form: every tower is a drum lit from one side -- a pale band toward the light, a dark one
    # away from it -- and the conical roofs take a little of the roof colour
    for (tx, tw, top, roof) in towers:
        # a turret standing on a broader tower ends where that tower's top begins
        foot = min([8.0] + [tp for (ox, ow, tp, _) in towers if ow > tw and abs(ox - tx) < ow / 2 and tp > top])
        cr.rectangle(tx + ls * tw * 0.5 - (tw * 0.3 if ls > 0 else 0.0), top, tw * 0.3, foot - top)
        core.src(cr, rimc, 0.2)
        cr.fill()
        cr.rectangle(tx - ls * tw * 0.5 - (tw * 0.34 if ls < 0 else 0.0), top, tw * 0.34, foot - top)
        core.src(cr, core.shade(col, 0.3), 0.28)
        cr.fill()
        if roof == "cone":
            rh = tw * (1.9 if tw < 30 else 1.5)
            cr.rectangle(tx - tw, top - rh - 2.0, tw * 2.0, rh + 3.0)
            core.src(cr, core.mix(col, P["roof"], 0.35), 0.5)
            cr.fill()
    # the walls darken a little toward their foot (they sit in their own shadow)
    cr.rectangle(-170.0, -60.0, 344.0, 68.0)
    cr.set_source(core.linear(0, -60.0, 0, 8.0, [core.alpha(core.shade(col, 0.2), 0.0), core.alpha(core.shade(col, 0.2), 0.45)]))
    cr.fill()
    cr.restore()
    if road and hill:
        core.tapered(cr, [(-30.0, 8.0), (-120.0, 40.0), (40.0, 80.0), (-90.0, 130.0), (-40.0, hill_h + 10.0)], 3.0, 9.0)
        core.src(cr, core.mix(col, rimc, 0.35), 0.8)
        cr.fill()
    # lit windows: tiny arched slits on the towers and the keep
    if windows and wa > 0.01:
        for i in range(windows):
            tx, tw, top, roof = towers[i % len(towers)]
            wy = top + 18.0 + core.hash01(i, seed + 61) * (abs(top) - 40.0) * 0.6
            wx = tx + (core.hash01(i, seed + 62) - 0.5) * tw * 0.5
            core.rounded_rect(cr, wx - 1.8, wy - 3.5, 3.6, 7.0, 1.6)
            core.src(cr, wc, wa)
            cr.fill()
            if wa > 0.6:
                fx.glow(cr, wx, wy, 9.0, wc, 0.35 * wa)
    if banners:
        for (tx, tw, top, roof) in towers:
            if roof != "cone":
                continue
            ph = t * 2.2 + tx * 0.05
            px0 = tx
            py0 = top - tw * (1.9 if tw < 30 else 1.5)
            cr.set_line_width(1.4)
            core.src(cr, col)
            cr.move_to(px0, py0)
            cr.line_to(px0, py0 - 16.0)
            cr.stroke()
            flag = [(px0, py0 - 16.0)]
            for k in range(1, 6):
                u = k / 5
                flag.append((px0 + u * 18.0, py0 - 16.0 + 2.5 * math.sin(ph + u * 3.0) + u * 1.5))
            for k in range(5, 0, -1):
                u = k / 5
                flag.append((px0 + u * 14.0, py0 - 10.5 + 2.5 * math.sin(ph + u * 3.0) + u * 0.5))
            core.polygon(cr, flag + [(px0, py0 - 10.0)])
            core.src(cr, core.mix("#a83a3a", col, 0.45))
            cr.fill()
    cr.restore()


def _round_tree(cr, x, y, r, dark, mid, lit, light_dx=-0.6, kind="round"):
    """A stylised storybook tree seen from afar: a little trunk and a round crown (or a tall
    poplar), mostly a dark silhouette with a thin crescent of sky light on the lit side."""
    if kind == "poplar":
        rx, ry = r * 0.42, r * 1.3
        cy = y - ry - r * 0.25
    else:
        rx, ry = r, r * 0.9
        cy = y - ry - r * 0.35
    cr.rectangle(x - r * 0.09, cy, r * 0.18, y - cy)
    core.src(cr, dark)
    cr.fill()
    core.ellipse(cr, x + light_dx * rx * 0.12, cy - ry * 0.06, rx, ry)
    core.src(cr, lit)
    cr.fill()
    core.ellipse(cr, x - light_dx * rx * 0.05, cy + ry * 0.02, rx * 0.97, ry * 0.97)
    core.src(cr, mid)
    cr.fill()
    core.ellipse(cr, x - light_dx * rx * 0.25, cy + ry * 0.3, rx * 0.7, ry * 0.55)
    core.src(cr, dark, 0.7)
    cr.fill()


def _hedgerow(cr, pts, r, color, seed, alpha=1.0):
    """A hedgerow: a chain of small overlapping bush dabs along a polyline."""
    cr.new_path()
    for i, (px, py) in enumerate(core.resample(pts, max(2, int(core.polyline_length(pts) / (r * 1.1))))):
        rr = r * (0.75 + 0.5 * core.hash01(i, seed))
        cr.new_sub_path()
        cr.arc(px, py - rr * 0.4, rr, 0, TAU)
    core.src(cr, color, alpha)
    cr.fill()


def draw_hills(cr, x=-90.0, w=2100.0, base_y=760.0, kind="dusk", layers=3, seed=0, height=(70.0, 190.0), trees=True,
               fields=True, bottom=1200.0, colors=None, light_dx=-0.6, rim=True):
    """Rolling storybook hills in `layers` bands from far (hazy, light) to near (deeper): each
    band is shaded from its sky-lit ridge down to a darker foot and edged with a thin rim of sky
    light; hedgerows follow its contours with strips of field between them, and copses of
    round trees and tall poplars stand along the ridge and the hedges. Ridges peak about
    height[1] above base_y (far band) .. height[0] (near band). light_dx < 0: lit from the left."""
    P = palette(kind)
    if colors is None:
        # far bands sink into the haze, the nearest takes the palette's deep "near" colour
        cols = []
        for i in range(layers):
            u_ = i / max(1, layers - 1)
            base = P["far"] if u_ < 0.34 else P["mid"] if u_ < 0.67 else P["near"]
            cols.append(haze_toward(base, P["haze"], 0.62 * (1.0 - u_) ** 1.2))
    else:
        cols = colors
    sky_lo = P["sky"][-1]
    fol_d, fol_m, fol_l = P["foliage"]
    nseg = 60
    for li in range(layers):
        u = li / max(1, layers - 1)
        hh = lerp(height[1], height[0], u)
        y0 = base_y + 30.0 * u * layers
        col = cols[li]
        far_k = 0.78 - 0.55 * u

        def ridge_y(xx, li=li, hh=hh, y0=y0):
            return (y0 - hh * (0.55 + 0.25 * math.sin(xx * 0.0021 + seed + li * 1.7) + 0.2 * math.sin(xx * 0.0057 + li * 2.3))
                    - 8.0 * core.fbm1(xx * 0.01, 2, seed + li))

        pts = [(x + w * i / nseg, ridge_y(x + w * i / nseg)) for i in range(nseg + 1)]
        top_y = min(py for _, py in pts)
        cr.new_path()
        core.smooth_open(cr, pts)
        cr.line_to(x + w, bottom)
        cr.line_to(x, bottom)
        cr.close_path()
        band = Path_(cr)
        ridge_c = core.mix(col, sky_lo, 0.22 * (1 - u) + 0.08)
        foot_c = core.shade(col, 0.14 + 0.1 * u)
        band.add(cr)
        cr.set_source(core.linear(0, top_y, 0, y0 + 170.0, [ridge_c, col, foot_c]))
        cr.fill()
        hedge_c = haze_toward(fol_d, P["haze"], far_k * 0.85)
        cr.save()
        band.add(cr)
        cr.clip()
        contours = []
        if fields:
            # field strips and hedgerows that follow the band's contours
            n_c = 2 + int(u * 2)
            for c_ in range(n_c):
                dy = (28.0 + 34.0 * c_) * (0.7 + 0.8 * u)
                cp = [(px, py + dy + 9.0 * math.sin(px * 0.006 + c_ * 2.1 + seed)) for px, py in pts]
                contours.append(cp)
            for c_ in range(len(contours) - 1):
                if (c_ + li) % 2 == 0:
                    continue
                core.smooth_open(cr, contours[c_])
                rev = contours[c_ + 1][::-1]
                for q_ in rev:
                    cr.line_to(*q_)
                cr.close_path()
                core.src(cr, core.mix(col, fol_l, 0.08 + 0.05 * u), 0.6)
                cr.fill()
            for k_, cp in enumerate(contours):
                _hedgerow(cr, cp, 2.2 + 3.0 * u, hedge_c, seed + li * 7 + k_, 0.55 + 0.25 * u)
            # a few dividing hedges running down the slope
            for i in range(int(w / 420)):
                if core.hash01(i, seed + li * 5 + 1) > 0.6:
                    continue
                hx = x + (i + 0.5) * w / int(w / 420) + core.jitter(i, 90, seed + li * 5)
                hy = ridge_y(hx) + 30.0 * (0.7 + u)
                bend = core.jitter(i, 30.0, seed + li * 5 + 2)
                core.tapered(cr, [(hx, hy), (hx + bend, hy + 40.0 * (0.7 + u)), (hx + bend * 0.4, hy + 80.0 * (0.7 + u))],
                             1.5 + 2 * u, 2.5 + 2 * u)
            core.src(cr, hedge_c, 0.35 + 0.2 * u)
            cr.fill()
        texture(cr, "paint", 0.06, 1.6)
        cr.restore()
        if rim:
            core.tapered(cr, [(px, py + 1.2) for px, py in pts], 2.4, 2.4)
            core.src(cr, core.mix(sky_lo, "#ffffff", 0.25), 0.4 * (1 - 0.6 * u))
            cr.fill()
        if trees:
            dark = haze_toward(core.shade(fol_d, 0.25), P["haze"], far_k * 0.7)
            mid = haze_toward(fol_d, P["haze"], far_k * 0.7)
            lit = haze_toward(core.mix(fol_m, sky_lo, 0.45), P["haze"], far_k * 0.6)
            spots = []
            for i in range(int(w / 120)):                      # copses on the ridge
                if core.hash01(i, seed + li * 13 + 72) > 0.45:
                    continue
                tx = x + core.hash01(i, seed + li * 13 + 71) * w
                spots.append((tx, ridge_y(tx) + 5.0))
            for cp in contours[:2]:                            # and along the hedgerows
                for i in range(int(w / 200)):
                    if core.hash01(i, seed + li * 17 + len(spots)) > 0.4:
                        continue
                    k_ = int(core.hash01(i, seed + li * 19) * (len(cp) - 1))
                    spots.append(cp[k_])
            for j, (tx, ty) in enumerate(spots):
                n_ = 1 + int(core.hash01(j, seed + 73) * 4)
                for k in range(n_):
                    r = (7.0 + 6.0 * core.hash01(j * 7 + k, seed + 74)) * (0.6 + 1.0 * u)
                    kind_t = "poplar" if core.hash01(j * 7 + k, seed + 76) > 0.7 else "round"
                    _round_tree(cr, tx + k * r * 1.45, ty + core.jitter(k, 2.0, seed), r, dark, mid, lit, light_dx, kind_t)


class Path_:
    """Minimal captured-path helper (env does not import the character kit)."""

    def __init__(self, cr):
        self.p = cr.copy_path()

    def add(self, cr):
        cr.new_path()
        cr.append_path(self.p)


def draw_haze(cr, x, y, w, h, color, top_alpha=0.0, bottom_alpha=0.5, additive=False):
    """A vertical haze/fog wash over everything drawn so far in (x, y, w, h): atmospheric depth
    between layers (light toward the horizon). additive=True adds light instead (glow haze)."""
    pat = core.linear(0, y, 0, y + h, [(0.0, core.alpha(color, top_alpha)), (1.0, core.alpha(color, bottom_alpha))])
    cr.save()
    if additive:
        cr.set_operator(cairo.OPERATOR_ADD)
    cr.rectangle(x, y, w, h)
    cr.set_source(pat)
    cr.fill()
    cr.restore()


def draw_mist(cr, x, y, w, h, color, alpha=0.35, seed=0, scale=2.0, offset=0.0):
    """A low band of painterly mist (x, y, w, h): noise-shaped, densest in its middle, fading to
    nothing at the top and bottom. offset scrolls it (Mist animates this cheaply)."""
    surf, _keep = _mist_surface(int(seed))
    pat = cairo.SurfacePattern(surf)
    pat.set_extend(cairo.EXTEND_REPEAT)
    pat.set_filter(cairo.FILTER_BILINEAR)
    m = cairo.Matrix()
    m.translate(x + offset, y)
    m.scale(scale * 2.0, h / 256.0)
    m.invert()
    pat.set_matrix(m)
    c = core.col(color)
    cr.save()
    cr.rectangle(x, y, w, h)
    cr.clip()
    cr.set_source_rgba(c[0], c[1], c[2], alpha)
    cr.mask(pat)
    cr.restore()


@functools.lru_cache(maxsize=8)
def _mist_surface(seed):
    n = 512
    v = _noise_tile(n, 2.4, seed + 101)[:256, :] * 0.5 + 0.5
    prof = np.sin(np.linspace(0, math.pi, 256)) ** 1.5
    a = np.clip((v * 1.4 - 0.3) * prof[:, None], 0, 1)
    arr = np.zeros((256, n, 4), np.uint8)
    arr[..., 3] = (a * 255).astype(np.uint8)
    data = bytearray(arr.tobytes())
    return cairo.ImageSurface.create_for_data(data, cairo.FORMAT_ARGB32, n, 256, n * 4), data


class Mist:
    """A drifting mist band: Mist(x, y, w, h, color, alpha, seed, speed).draw(cr, t). ~2 ms."""

    def __init__(self, x, y, w, h, color, alpha=0.3, seed=0, speed=8.0, scale=2.0):
        self.args = (x, y, w, h, color, alpha, seed, scale)
        self.speed = speed

    def draw(self, cr, t, alpha=1.0):
        x, y, w, h, color, a, seed, scale = self.args
        draw_mist(cr, x, y, w, h, color, a * alpha, seed, scale, offset=t * self.speed)


# ----------------------------------------------------------------------------------------
# the town: half-timbered houses, street rows, the far roofline
# ----------------------------------------------------------------------------------------

FLOOR_H = 520.0          # an upper storey at scale 1.0 (the dragon is 520 tall: he would stoop)
GROUND_H = 600.0         # the ground storey (stone or timber); doors ~470 high


@functools.lru_cache(maxsize=64)
def _h(seed, k):
    return core.hash01(k, seed)


class HouseRig:
    """Where things are on a drawn house (world coordinates): rect = (x, y_top, w, h) of the
    facade, windows = [(cx, cy, w, h, lit)], door = (x, y, w, h), roof_top = y of the ridge,
    lights = [((x, y), colour, level, width)] for the lit windows -- glows, and wet-street
    reflections via [(p[0], p[1], c, lv, ground_y) for (p, c, lv, w) in rig.lights]."""

    def __init__(self, **kw):
        self.__dict__.update(kw)


def _beam(cr, x0, y0, x1, y1, wdt, col, lit, shadow, light_side=-1):
    """A timber beam (a straight quad) with a lit edge and a shadowed edge."""
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L * wdt / 2, dx / L * wdt / 2
    core.polygon(cr, [(x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)])
    core.src(cr, col)
    cr.fill()
    k = 0.28
    core.polygon(cr, [(x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 + nx * (1 - 2 * k), y1 + ny * (1 - 2 * k)),
                      (x0 + nx * (1 - 2 * k), y0 + ny * (1 - 2 * k))])
    core.src(cr, shadow if (nx * light_side + ny * -1) < 0 else lit, 0.8)
    cr.fill()


def _window(cr, cx, cy, w, h, lit, P, seed, shutters="open", arched=False, detail=2, glow=1.0):
    """A leaded diamond-pane window in a timber frame: warm candlelight when lit (the lattice
    dark against it), a deep night pane with a faint sky glint when not; wooden shutters open
    beside it, or closed over it."""
    tim = P["timber"]
    lit_c = P["window"]
    dark_c = P["window_dark"]
    x0, y0 = cx - w / 2, cy - h / 2
    # frame
    core.rounded_rect(cr, x0 - 7, y0 - 7, w + 14, h + 14, 3 if not arched else (w / 2 + 7, w / 2 + 7, 3, 3))
    core.src(cr, tim)
    cr.fill()
    if shutters == "closed":
        for k in (0, 1):
            sx = x0 + k * w / 2
            cr.rectangle(sx + 1.0, y0, w / 2 - 2.0, h)
            core.src(cr, core.mix(tim, P["plaster"][seed % 3], 0.25))
            cr.fill()
            if detail >= 1:
                core.src(cr, core.shade(tim, 0.3), 0.8)
                for j in range(1, 3):
                    cr.rectangle(sx + 1.0 + j * (w / 2 - 2.0) / 3 - 0.8, y0, 1.6, h)
                cr.fill()
                core.src(cr, "#1a1a1e")
                cr.rectangle(sx + 2.0, y0 + h * 0.2, w / 2 - 6.0, 3.0)
                cr.rectangle(sx + 2.0, y0 + h * 0.75, w / 2 - 6.0, 3.0)
                cr.fill()
        if lit > 0.05:            # light leaks through the cracks of the shutters
            core.src(cr, lit_c, 0.7 * lit)
            cr.rectangle(cx - 1.0, y0 + 2, 2.0, h - 4)
            cr.fill()
        return
    if arched:
        cr.move_to(x0, y0 + h)
        cr.line_to(x0, y0 + w / 2)
        cr.arc(cx, y0 + w / 2, w / 2, math.pi, TAU)
        cr.line_to(x0 + w, y0 + h)
        cr.close_path()
    else:
        cr.rectangle(x0, y0, w, h)
    pane = cr.copy_path()
    if lit > 0.02:
        cr.set_source(core.radial(cx, cy + h * 0.15, max(w, h) * 0.75,
                                  [(0.0, core.tint(lit_c, 0.45)), (0.6, lit_c), (1.0, core.mix(lit_c, dark_c, 0.45))]))
        cr.fill()
        if lit < 0.99:
            cr.append_path(pane)
            core.src(cr, dark_c, 1.0 - lit)
            cr.fill()
    else:
        cr.set_source(core.linear(0, y0, 0, y0 + h, [core.mix(dark_c, P["sky"][-1], 0.25), dark_c]))
        cr.fill()
    if detail >= 1:
        # the leading: a diamond lattice clipped to the pane
        cr.save()
        cr.append_path(pane)
        cr.clip()
        cr.set_line_width(max(1.0, w * 0.035))
        core.src(cr, core.shade(tim, 0.2), 0.85)
        step = max(8.0, w / 4.0)
        k = -h
        while k < w + h:
            cr.move_to(x0 + k, y0)
            cr.line_to(x0 + k + h * 0.75, y0 + h)
            cr.move_to(x0 + k, y0 + h)
            cr.line_to(x0 + k + h * 0.75, y0)
            k += step
        cr.stroke()
        cr.rectangle(cx - 2.5, y0, 5.0, h)                    # mullion and transom
        cr.rectangle(x0, cy - 2.0, w, 4.0)
        core.src(cr, tim)
        cr.fill()
        cr.restore()
    if shutters == "open":
        for sgn in (-1, 1):
            sx = cx + sgn * (w / 2 + 9.0) + (0 if sgn > 0 else -w * 0.42)
            cr.rectangle(sx, y0 - 2.0, w * 0.42, h + 4.0)
            core.src(cr, core.mix(tim, "#6a4a3a", 0.35))
            cr.fill()
            if detail >= 2:
                core.src(cr, core.shade(tim, 0.3), 0.6)
                cr.rectangle(sx + w * 0.14 - 0.7, y0, 1.4, h)
                cr.rectangle(sx + w * 0.28 - 0.7, y0, 1.4, h)
                cr.fill()


def _door(cr, x, ybase, w, h, P, seed, detail=2, lit=0.0):
    """An arched plank door with iron strap hinges and a ring handle, in a stone surround."""
    tim = P["timber"]
    st = P["stone"]
    cr.move_to(x - 12, ybase)
    cr.line_to(x - 12, ybase - h + w / 2)
    cr.arc(x + w / 2, ybase - h + w / 2, w / 2 + 12, math.pi, TAU)
    cr.line_to(x + w + 12, ybase)
    cr.close_path()
    core.src(cr, core.mix(st, P["plaster"][0], 0.3))
    cr.fill()
    cr.move_to(x, ybase)
    cr.line_to(x, ybase - h + w / 2)
    cr.arc(x + w / 2, ybase - h + w / 2, w / 2, math.pi, TAU)
    cr.line_to(x + w, ybase)
    cr.close_path()
    door = cr.copy_path()
    core.src(cr, core.mix(tim, ("#7a4e2e", "#5a3e5a", "#3e5a4a", "#6a4a2a")[seed % 4], 0.45))
    cr.fill()
    if detail >= 1:
        cr.save()
        cr.append_path(door)
        cr.clip()
        core.src(cr, core.shade(tim, 0.35), 0.7)
        for k in range(1, 5):
            cr.rectangle(x + k * w / 5 - 1.2, ybase - h, 2.4, h)
        cr.fill()
        core.src(cr, "#1e1c20")
        for hy in (0.25, 0.7):
            cr.rectangle(x, ybase - h * hy - 4, w * 0.7, 8)
        cr.fill()
        cr.set_line_width(3.0)
        cr.arc(x + w * 0.82, ybase - h * 0.45, 9, 0, TAU)
        cr.stroke()
        cr.restore()
    if lit > 0.02:     # light under the door
        core.src(cr, P["window"], 0.6 * lit)
        cr.rectangle(x + 4, ybase - 3, w - 8, 3)
        cr.fill()


def _shop_front(cr, x, ybase, w, h, P, seed, detail=2):
    """A shuttered shop front: a wide opening closed by a plank shutter with an iron bar, a
    counter flap below it (S3: the shops are shut for the night)."""
    tim = P["timber"]
    cr.rectangle(x, ybase - h, w, h)
    core.src(cr, tim)
    cr.fill()
    cr.rectangle(x + 10, ybase - h + 10, w - 20, h * 0.68)
    core.src(cr, core.mix(tim, "#6a4a32", 0.4))
    cr.fill()
    if detail >= 1:
        core.src(cr, core.shade(tim, 0.35), 0.7)
        n = max(4, int(w / 34))
        for k in range(1, n):
            cr.rectangle(x + 10 + k * (w - 20) / n - 1.2, ybase - h + 10, 2.4, h * 0.68)
        cr.fill()
        core.src(cr, "#1e1c20")
        cr.rectangle(x + 4, ybase - h + 10 + h * 0.3, w - 8, 9)
        cr.fill()
    cr.rectangle(x + 6, ybase - h * 0.26, w - 12, h * 0.16)     # the counter flap
    core.src(cr, core.mix(tim, "#7a5a3a", 0.5))
    cr.fill()


def draw_house(cr, x, y, w=620.0, floors=2, scale=1.0, kind="night", seed=0, lit=0.4, roof=None, ground="stone",
               shutters=None, shop=None, chimney=True, jetty=34.0, plaster=None, detail=2):
    """A half-timbered storybook house, seen face-on from the street.

    Anchor (x, y) = the BOTTOM-LEFT of its ground storey on the street; w = its width at scale
    1.0 (the jettied upper storeys overhang `jetty` on each side). floors = storeys (1-3); the
    ground storey is GROUND_H = 600 tall (stone or timber), each upper one FLOOR_H = 520, then
    the roof: roof "gable" (gable end to the street, carved bargeboards and a finial), "side"
    (the eaves to the street, a dormer) or "thatch". Timber framing (posts, braces, crosses),
    lime plaster (tint by seed, granulated), leaded diamond-pane windows with shutters,
    an arched plank door or a shuttered shop front (shop=True/False/None=by seed).
    lit 0..1: the chance a window is lit (deterministic by seed). Colours from PALETTES[kind].
    Static: cache rows of houses in an fx.Layer. Returns a HouseRig (world coordinates)."""
    P = palette(kind)
    rnd = lambda k: core.hash01(k, seed * 31 + 7)         # noqa: E731
    cr.save()
    cr.translate(x, y)
    cr.scale(scale, scale)
    lean = (rnd(99) - 0.5) * 0.022                        # storybook houses lean a little
    if lean:
        cr.transform(cairo.Matrix(1.0, 0.0, lean, 1.0, 0.0, 0.0))
    m = cr.get_matrix()
    tim = P["timber"]
    tim_lit = core.tint(tim, 0.18)
    tim_dk = core.shade(tim, 0.35)
    pl = plaster or P["plaster"][int(rnd(1) * len(P["plaster"]))]
    roof = roof or ("gable", "side", "gable", "thatch")[int(rnd(2) * 4)]
    shop = (rnd(3) < 0.4) if shop is None else shop
    shutters_mode = shutters
    windows, lights = [], []
    sil = []                                    # silhouette pieces (for the night falloff clip)
    # --- ground storey
    gh = GROUND_H
    sil.append(("rect", (0.0, -gh, w, gh)))
    if ground == "stone":
        draw_stone_wall(cr, 0.0, -gh, w, gh, kind, seed=seed + 5, block=(70.0, 44.0), texture_alpha=0.12)
    else:
        cr.rectangle(0.0, -gh, w, gh)
        _fill_tex(cr, pl, "plaster", 0.18, 1.0)
    door_w = 230.0
    door_x = w * (0.18 + 0.5 * rnd(4)) - door_w / 2
    door_x = clamp(door_x, 40.0, w - door_w - 40.0)
    if shop and w > 520:
        sx_ = 40.0 if door_x > w / 2 else door_x + door_w + 50.0
        sw_ = min(w - sx_ - 40.0, w * 0.5)
        if sw_ > 160:
            _shop_front(cr, sx_, 0.0, sw_, 360.0, P, seed, detail)
    lit_door = 0.6 if rnd(5) < lit else 0.0
    _door(cr, door_x, 0.0, door_w, 470.0, P, seed, detail, lit_door)
    if not shop or w <= 520:
        wx = w * 0.78 if door_x < w / 2 else w * 0.22
        wl = 1.0 if rnd(6) < lit else 0.0
        _window(cr, wx, -300.0, 130.0, 170.0, wl, P, seed + 1, "open" if rnd(7) < 0.5 else "closed", True, detail)
        windows.append((wx, -300.0, 130.0, 170.0, wl))
    # --- upper storeys (jettied)
    top = -gh
    for f in range(floors - 1):
        fh = FLOOR_H
        jx = jetty * (f + 1)
        fx0, fx1 = -jx, w + jx
        y0, y1 = top - fh, top
        sil.append(("rect", (fx0, y0, fx1 - fx0, fh)))
        # the jetty: a shadow under the overhang and carved brackets
        cr.rectangle(fx0, y1, fx1 - fx0, 26.0)
        cr.set_source(core.linear(0, y1, 0, y1 + 26.0, [core.alpha("#000000", 0.45), core.alpha("#000000", 0.0)]))
        cr.fill()
        cr.rectangle(fx0, y0, fx1 - fx0, fh)
        _fill_tex(cr, pl, "plaster", 0.2, 1.0)
        if detail >= 1:                                       # grime toward the bottom of the plaster
            cr.rectangle(fx0, y1 - 90.0, fx1 - fx0, 90.0)
            cr.set_source(core.linear(0, y1 - 90.0, 0, y1, [core.alpha(tim_dk, 0.0), core.alpha(tim_dk, 0.25)]))
            cr.fill()
        # timber frame: sill, plate, posts, braces
        bw = 20.0
        n_bays = max(2, int((fx1 - fx0) / 150.0))
        bay = (fx1 - fx0) / n_bays
        for k in range(n_bays + 1):
            px = fx0 + k * bay
            _beam(cr, px, y0, px, y1, bw, tim, tim_lit, tim_dk)
        # windows in some bays, braces/crosses in the others
        win_bays = set()
        for k in range(n_bays):
            if rnd(20 + f * 10 + k) < 0.55 and 0 < k < n_bays - 1 or (n_bays <= 3 and k == n_bays // 2):
                win_bays.add(k)
        if not win_bays:
            win_bays.add(n_bays // 2)
        for k in range(n_bays):
            bx0, bx1 = fx0 + k * bay, fx0 + (k + 1) * bay
            if k in win_bays:
                wl = 1.0 if rnd(40 + f * 10 + k) < lit else 0.0
                ww, wh = min(bay - 46.0, 140.0), 190.0
                wcx, wcy = (bx0 + bx1) / 2, y0 + fh * 0.48
                mode = shutters_mode or ("open" if rnd(50 + k) < 0.6 else "closed")
                if mode == "closed":
                    wl = 0.0 if rnd(60 + k) < 0.5 else wl * 0.6
                _window(cr, wcx, wcy, ww, wh, wl, P, seed + k, mode, False, detail)
                windows.append((wcx, wcy, ww, wh, wl))
                _beam(cr, bx0, wcy + wh / 2 + 22, bx1, wcy + wh / 2 + 22, 14.0, tim, tim_lit, tim_dk)
            else:
                style = int(rnd(70 + f * 10 + k) * 3)
                if style == 0:
                    _beam(cr, bx0, y1, bx1, y0, 16.0, tim, tim_lit, tim_dk)
                elif style == 1:
                    _beam(cr, bx0, y1, bx1, y0, 16.0, tim, tim_lit, tim_dk)
                    _beam(cr, bx0, y0, bx1, y1, 16.0, tim, tim_lit, tim_dk)
                else:
                    _beam(cr, bx0, y0 + fh * 0.5, bx1, y0 + fh * 0.5, 14.0, tim, tim_lit, tim_dk)
                    _beam(cr, (bx0 + bx1) / 2, y0 + fh * 0.5, bx0, y1, 14.0, tim, tim_lit, tim_dk)
                    _beam(cr, (bx0 + bx1) / 2, y0 + fh * 0.5, bx1, y1, 14.0, tim, tim_lit, tim_dk)
        _beam(cr, fx0 - 6, y1 - 10, fx1 + 6, y1 - 10, 26.0, tim, tim_lit, tim_dk)      # the jetty bressumer
        _beam(cr, fx0, y0 + 10, fx1, y0 + 10, 20.0, tim, tim_lit, tim_dk)
        if detail >= 1:
            for k in range(n_bays + 1):                      # carved brackets under the jetty
                px = fx0 + k * bay
                core.polygon(cr, [(px - 9, y1), (px + 9, y1), (px + 4, y1 + 30), (px - 4, y1 + 30)])
                core.src(cr, tim_dk)
                cr.fill()
        top = y0
    # --- the roof
    jx = jetty * (floors - 1)
    rx0, rx1 = -jx - 30.0, w + jx + 30.0
    roof_c = P["roof"]
    if roof in ("gable", "thatch"):
        rh = (rx1 - rx0) * (0.62 if roof == "gable" else 0.5)
        ridge = top - rh
        apex = ((rx0 + rx1) / 2, ridge)
        sil.append(("poly", [(rx0 - 40, top + 40), (apex[0], ridge - 20), (rx1 + 40, top + 40)]))
        if roof == "gable":
            # the gable wall (plaster + timbers) under projecting bargeboards
            core.polygon(cr, [(rx0 + 40, top), apex, (rx1 - 40, top)])
            _fill_tex(cr, pl, "plaster", 0.2, 1.0)
            _beam(cr, (rx0 + rx1) / 2, ridge + 30, (rx0 + rx1) / 2, top, 18.0, tim, tim_lit, tim_dk)
            _beam(cr, rx0 + 120, top, (rx0 + rx1) / 2, ridge + 110, 16.0, tim, tim_lit, tim_dk)
            _beam(cr, rx1 - 120, top, (rx0 + rx1) / 2, ridge + 110, 16.0, tim, tim_lit, tim_dk)
            gw = 90.0
            wl = 1.0 if rnd(90) < lit * 0.8 else 0.0
            _window(cr, (rx0 + rx1) / 2, top - rh * 0.38, gw, gw * 1.2, wl, P, seed + 9, "none", True, detail)
            windows.append(((rx0 + rx1) / 2, top - rh * 0.38, gw, gw * 1.2, wl))
            for sgn in (-1, 1):                               # bargeboards (roof edges)
                ex = rx0 - 10 if sgn < 0 else rx1 + 10
                _beam(cr, ex, top + 14, apex[0], apex[1] - 12, 34.0, roof_c, core.tint(roof_c, 0.15), core.shade(roof_c, 0.3))
            core.polygon(cr, [(apex[0] - 6, apex[1] - 10), (apex[0] + 6, apex[1] - 10), (apex[0], apex[1] - 70)])
            core.src(cr, tim)
            cr.fill()
        else:
            # thatch: straight thick slopes, a deep rounded eave that overhangs the wall, a
            # combed texture running down the slope and a scalloped ridge roll
            thc = core.mix(roof_c, "#7a6038", 0.5)
            ex0, ex1 = rx0 - 30, rx1 + 30
            th = [(ex0, top + 34), (ex0 + 10, top - 10), (apex[0] - 40, ridge + 6), (apex[0] + 40, ridge + 6),
                  (ex1 - 10, top - 10), (ex1, top + 34), (apex[0], top + 42)]
            core.smooth_closed(cr, th, 0.35)
            _fill_tex(cr, thc, "wood", 0.32, 0.6, sx=0.25, sy=3.0, angle=0.0)
            cr.save()
            core.smooth_closed(cr, th, 0.35)
            cr.clip()
            cr.rectangle(ex0, top - 30, ex1 - ex0, 80)
            cr.set_source(core.linear(0, top - 30, 0, top + 45, [core.alpha("#000000", 0.0), core.alpha("#000000", 0.4)]))
            cr.fill()
            core.src(cr, core.shade(thc, 0.3), 0.6)
            for k in range(14):
                xx = lerp(ex0 + 60, ex1 - 60, k / 13)
                cr.move_to(xx, top + 30)
                cr.line_to(apex[0] + (xx - apex[0]) * 0.15, ridge + 30)
            cr.set_line_width(3.0)
            cr.stroke()
            cr.restore()
            for k in range(9):                                # the ridge roll's scallops
                xx = lerp(apex[0] - 120, apex[0] + 120, k / 8)
                core.circle(cr, xx, ridge + 14, 22)
            core.src(cr, core.shade(thc, 0.12))
            cr.fill()
        roof_top = ridge
    else:
        # eaves to the street: the roof slope as a band of tiles above the facade, a dormer
        rh = 260.0
        ridge = top - rh
        sil.append(("poly", [(rx0, top + 10), (rx0 + 60, ridge), (rx1 - 60, ridge), (rx1, top + 10)]))
        core.polygon(cr, [(rx0, top + 10), (rx0 + 60, ridge), (rx1 - 60, ridge), (rx1, top + 10)])
        _fill_tex(cr, roof_c, "stone", 0.18, 0.8)
        if detail >= 1:
            core.src(cr, core.shade(roof_c, 0.35), 0.7)
            yy = top + 4
            row = 0
            while yy > ridge + 10:
                cr.rectangle(rx0 + 20, yy - 2, rx1 - rx0 - 40, 3.0)
                for k in range(int((rx1 - rx0) / 34)):
                    cr.rectangle(rx0 + 20 + k * 34 + (17 if row % 2 else 0), yy - 26, 2.0, 26)
                yy -= 28
                row += 1
            cr.fill()
        dw = 150.0
        dx = (rx0 + rx1) / 2 + (rnd(91) - 0.5) * 200
        core.polygon(cr, [(dx - dw / 2 - 20, top - 40), (dx - dw / 2, ridge + 60), (dx, ridge + 10), (dx + dw / 2, ridge + 60),
                          (dx + dw / 2 + 20, top - 40)])
        core.src(cr, roof_c)
        cr.fill()
        wl = 1.0 if rnd(92) < lit * 0.7 else 0.0
        _window(cr, dx, top - 110, 80.0, 90.0, wl, P, seed + 11, "none", False, detail)
        windows.append((dx, top - 110, 80.0, 90.0, wl))
        roof_top = ridge
    # night: the facade falls into darkness toward the roof (the lanterns are down in the street)
    night_k = {"night": 0.55, "rain_night": 0.6, "blue_hour": 0.35, "evening": 0.25}.get(kind if isinstance(kind, str) else "", 0.0)
    if night_k > 0:
        cr.save()
        cr.new_path()
        for kind_, d in sil:
            if kind_ == "rect":
                cr.rectangle(*d)
            else:
                core.polygon(cr, d)
        cr.clip()
        cr.rectangle(rx0 - 40, roof_top - 80, rx1 - rx0 + 80, -roof_top + 80)
        cr.set_source(core.linear(0, roof_top, 0, 0.0, [core.alpha(P["sky"][0], night_k), core.alpha(P["sky"][0], night_k * 0.35),
                                                         core.alpha(P["sky"][0], 0.0)]))
        cr.fill()
        cr.restore()
    if chimney and rnd(93) < 0.75:
        cx_ = rx0 + (rx1 - rx0) * (0.22 + 0.56 * rnd(94))
        ch_top = roof_top - 60.0
        cr.rectangle(cx_ - 34, ch_top, 68, (top - 80) - ch_top if roof == "side" else rh * 0.6)
        _fill_tex(cr, core.mix(P["stone"], "#8a5a4a", 0.3), "stone", 0.25, 0.5)
        cr.rectangle(cx_ - 42, ch_top - 16, 84, 18)
        core.src(cr, core.shade(core.mix(P["stone"], "#8a5a4a", 0.3), 0.2))
        cr.fill()
    cr.restore()

    def W(px, py):
        return m.transform_point(px, py)

    for (wx, wy, ww, wh, wl) in windows:
        if wl > 0.01:
            lights.append((W(wx, wy), P["window"], wl, ww * scale))
    return HouseRig(rect=(x - jx * scale, y + roof_top * scale, (w + 2 * jx) * scale, -roof_top * scale),
                    windows=[(W(wx, wy), ww * scale, wh * scale, wl) for (wx, wy, ww, wh, wl) in windows],
                    door=(x + door_x * scale, y - 470.0 * scale, door_w * scale, 470.0 * scale), lights=lights,
                    roof_top=y + roof_top * scale)


def draw_street_row(cr, x0, x1, ground_y, scale=0.5, kind="night", seed=0, lit=0.4, floors=(2, 3), widths=(520.0, 760.0),
                    alley=0.25, detail=2):
    """A row of half-timbered houses along a street from x0 to x1 (world px) standing on
    ground_y, at `scale` (0.35-0.6 for the far side of a street behind the cast). Widths,
    storeys, roofs, plaster tints and lit windows vary deterministically by seed; now and then
    a dark alley gap. Returns [HouseRig] (their .lights feed glows and wet reflections)."""
    P = palette(kind)
    rigs = []
    x = x0
    k = 0
    while x < x1:
        w = lerp(widths[0], widths[1], core.hash01(k, seed + 1))
        f = floors[0] + int(core.hash01(k, seed + 2) * (floors[1] - floors[0] + 1))
        if k > 0 and core.hash01(k, seed + 3) < alley:
            # a narrow alley between two houses: a deep shadow that thickens toward the ground
            gap = (60.0 + 80.0 * core.hash01(k, seed + 4)) * scale
            ah = GROUND_H * 1.9 * scale
            cr.rectangle(x - 4 * scale, ground_y - ah, gap + 8 * scale, ah)
            cr.set_source(core.linear(0, ground_y - ah, 0, ground_y, [core.mix(P["near"], P["sky"][-1], 0.3),
                                                                      core.shade(P["near"], 0.5)]))
            cr.fill()
            x += gap
        jx = 34.0 * (f - 1) * scale
        rigs.append(draw_house(cr, x + jx, ground_y, w, f, scale, kind, seed * 97 + k, lit, detail=detail))
        x += (w + 0.0) * scale + jx * 2 - 6.0 * scale
        k += 1
    return rigs


def draw_roofline(cr, x0, x1, y, scale=0.25, kind="night", seed=0, color=None, lit=0.3, spire=True, haze=0.0):
    """A distant town as a roofline silhouette: gables, chimneys, a church spire, a few tiny lit
    windows -- for far layers (S3 behind the street, S8 the town glowing small and far away).
    y = the line where the houses stand; heights at scale 1.0 are house-sized (x ~1/4 typical)."""
    P = palette(kind)
    col = color or haze_toward(P["far"], P["haze"], haze)
    cr.save()
    cr.new_path()
    x = x0
    k = 0
    pts = [(x0, y + 40)]
    wins = []
    while x < x1:
        w = (300 + 400 * core.hash01(k, seed + 1)) * scale
        h = (900 + 700 * core.hash01(k, seed + 2)) * scale
        style = int(core.hash01(k, seed + 3) * 3)
        if style == 0:      # gable to the street
            pts += [(x, y - h), (x + w / 2, y - h - w * 0.6), (x + w, y - h)]
        elif style == 1:    # eaves: flat-topped roof band
            pts += [(x, y - h), (x + w * 0.15, y - h - w * 0.35), (x + w * 0.85, y - h - w * 0.35), (x + w, y - h)]
        else:               # a little tower/turret
            pts += [(x, y - h), (x, y - h * 1.15), (x + w * 0.5, y - h * 1.15 - w * 0.8), (x + w, y - h * 1.15), (x + w, y - h)]
        if core.hash01(k, seed + 4) < 0.6:
            cx_ = x + w * (0.2 + 0.6 * core.hash01(k, seed + 5))
            cr.rectangle(cx_, y - h - w * 0.45, 22 * scale * 2, w * 0.45)
        for j in range(3):
            if core.hash01(k * 5 + j, seed + 6) < lit:
                wins.append((x + w * (0.2 + 0.6 * core.hash01(k * 5 + j, seed + 7)), y - h * (0.3 + 0.5 * core.hash01(k * 5 + j, seed + 8))))
        x += w
        k += 1
    if spire:
        sx = x0 + (x1 - x0) * (0.3 + 0.4 * core.hash01(0, seed + 9))
        cr.rectangle(sx - 60 * scale, y - 2600 * scale, 120 * scale, 2600 * scale)
        cr.move_to(sx - 80 * scale, y - 2600 * scale)
        cr.line_to(sx, y - 3700 * scale)
        cr.line_to(sx + 80 * scale, y - 2600 * scale)
        cr.close_path()
    pts += [(x1, y + 40)]
    core.polygon(cr, pts)
    core.src(cr, col)
    cr.fill()
    for (wx, wy) in wins:
        core.src(cr, P["window"], 0.85)
        cr.rectangle(wx - 10 * scale, wy - 14 * scale, 20 * scale, 28 * scale)
        cr.fill()
    cr.restore()
    return wins


# ----------------------------------------------------------------------------------------
# stone: walls, arches, the vaulted hall (S1)
# ----------------------------------------------------------------------------------------

def draw_stone_wall(cr, x, y, w, h, kind="washhouse", seed=0, block=(84.0, 46.0), color=None, mortar=None,
                    texture_alpha=0.16, light_top=0.035, variation=0.08):
    """Coursed stone blocks filling (x, y, w, h): irregular widths per course, each block a
    slightly different tone with a lit top edge and a shadowed foot, sunk in darker mortar,
    granulated. block = (typical width, course height)."""
    P = palette(kind)
    base = color or P["stone"]
    mort = mortar or core.shade(base, 0.32)
    cr.save()
    cr.rectangle(x, y, w, h)
    cr.clip()
    core.src(cr, mort)
    cr.paint()
    bw, bh = block
    yy = y
    row = 0
    while yy < y + h:
        ch = bh * (0.85 + 0.3 * core.hash01(row, seed + 1))
        xx = x - bw * core.hash01(row, seed + 2)
        k = 0
        while xx < x + w:
            hsh = row * 97 + k
            ww = bw * (0.55 + 0.9 * core.hash01(hsh, seed + 3))
            v = (core.hash01(hsh, seed + 4) - 0.5) * 2 * variation
            c = core.tint(base, v) if v > 0 else core.shade(base, -v)
            c = core.hue_shift(c, (core.hash01(hsh, seed + 9) - 0.5) * 12.0)
            # a hewn stone: an irregular, slightly rounded quad inside its cell
            j = ch * 0.07
            g_ = 2.6
            quad = [(xx + g_ + core.jitter(hsh, j, seed + 5), yy + g_ + core.jitter(hsh, j, seed + 6)),
                    (xx + ww - g_ + core.jitter(hsh + 1, j, seed + 5), yy + g_ + core.jitter(hsh + 1, j, seed + 6)),
                    (xx + ww - g_ + core.jitter(hsh + 2, j, seed + 5), yy + ch - g_ + core.jitter(hsh + 2, j, seed + 6)),
                    (xx + g_ + core.jitter(hsh + 3, j, seed + 5), yy + ch - g_ + core.jitter(hsh + 3, j, seed + 6))]
            mid = [((quad[i][0] + quad[(i + 1) % 4][0]) / 2 + core.jitter(hsh + 7 + i, j * 0.6, seed + 7),
                    (quad[i][1] + quad[(i + 1) % 4][1]) / 2 + core.jitter(hsh + 7 + i, j * 0.6, seed + 8)) for i in range(4)]
            pts = [quad[0], mid[0], quad[1], mid[1], quad[2], mid[2], quad[3], mid[3]]
            core.smooth_closed(cr, pts, 0.35)
            core.src(cr, c)
            cr.fill()
            if light_top > 0:
                core.tapered(cr, [(pts[0][0] + 2, pts[0][1] + 2.0), (pts[1][0], pts[1][1] + 2.0), (pts[2][0] - 2, pts[2][1] + 2.0)],
                             2.4, 2.4)
                core.src(cr, core.tint(c, 0.22), 0.55 * light_top / 0.035)
                cr.fill()
                core.tapered(cr, [(pts[6][0] + 2, pts[6][1] - 2.5), (pts[5][0], pts[5][1] - 2.5), (pts[4][0] - 2, pts[4][1] - 2.5)],
                             3.4, 3.4)
                core.src(cr, core.shade(c, 0.22), 0.55)
                cr.fill()
            xx += ww
            k += 1
        yy += ch
        row += 1
    texture(cr, "stone", texture_alpha, 0.8)
    cr.restore()


def draw_arch(cr, cx, base_y, w, h, kind="washhouse", fill=None, depth=24.0, voussoirs=True, color=None, seed=0):
    """A round-headed stone arch (a window, a door, an arcade bay): voussoir stones round the
    head, a shadowed inner reveal of `depth`, and the opening filled with `fill` (a colour,
    a callable fill(cr) drawn clipped to the opening, or None to leave it open). (cx, base_y) =
    the middle of its sill; w x h the opening (h includes the round head)."""
    P = palette(kind)
    st = color or P["stone"]
    r = w / 2
    spring = base_y - h + r

    def opening(c, inset=0.0):
        c.move_to(cx - r + inset, base_y)
        c.line_to(cx - r + inset, spring)
        c.arc(cx, spring, r - inset, math.pi, TAU)
        c.line_to(cx + r - inset, base_y)
        c.close_path()

    if voussoirs:
        n = 11
        for i in range(n):
            a0 = math.pi + math.pi * i / n
            a1 = math.pi + math.pi * (i + 1) / n
            cr.new_path()
            cr.arc(cx, spring, r + 34.0, a0 + 0.012, a1 - 0.012)
            cr.arc_negative(cx, spring, r + 2.0, a1 - 0.012, a0 + 0.012)
            cr.close_path()
            v = (core.hash01(i, seed + 3) - 0.5) * 0.18
            core.src(cr, core.tint(st, v) if v > 0 else core.shade(st, -v))
            cr.fill()
    opening(cr)
    core.src(cr, core.shade(st, 0.45))
    cr.fill()
    cr.save()
    opening(cr, depth * 0.35)
    cr.clip()
    if callable(fill):
        fill(cr)
    elif fill is not None:
        core.src(cr, fill)
        cr.paint()
    # the reveal's shadow on the near side
    opening(cr, depth * 0.35)
    cr.set_source(core.linear(cx - r, 0, cx - r + depth * 1.4, 0, [core.alpha("#000000", 0.5), core.alpha("#000000", 0.0)]))
    cr.fill()
    cr.restore()


def draw_vaulted_hall(cr, x=-90.0, y=-80.0, w=2100.0, h=1240.0, kind="washhouse", seed=0, floor_y=700.0, vp=(900.0, 520.0),
                      bays=4, window_fill=None, moon=True):
    """The S1 wash-house interior as a back wall: coursed stone, an arcade of round-headed bays
    on heavy pillars, tall arched night windows (moon in one), ribs of the vault overhead, and a
    flagstone floor in one-point perspective toward vp, damp near the back wall.
    floor_y = where the back wall meets the floor. Static: cache it (blur ~1.5 for depth)."""
    P = palette(kind)
    st = P["stone"]
    draw_stone_wall(cr, x, y, w, floor_y - y, kind, seed, (110.0, 52.0), texture_alpha=0.14)
    # darken toward the vault and the floor (lamps hang in the middle band)
    cr.rectangle(x, y, w, floor_y - y)
    cr.set_source(core.linear(0, y, 0, floor_y, [core.alpha("#000000", 0.55), core.alpha("#000000", 0.0),
                                                  core.alpha("#000000", 0.1), core.alpha("#000000", 0.35)]))
    cr.fill()
    pitch = w / bays
    for i in range(bays):
        cx = x + pitch * (i + 0.5)
        win_w, win_h = pitch * 0.32, (floor_y - y) * 0.48
        sill = floor_y - (floor_y - y) * 0.14

        def night(c, cx=cx, win_w=win_w, sill=sill, win_h=win_h, i=i):
            c.set_source(core.linear(0, sill - win_h, 0, sill, ["#16304a", P["sky"][0], "#0e2030"]))
            c.paint()
            if moon and i == bays // 2:
                fx.glow(c, cx + win_w * 0.15, sill - win_h * 0.7, win_w * 1.6, "#a9c4f0", 0.5)
                core.src(c, "#e8f0ff", 0.9)
                core.circle(c, cx + win_w * 0.15, sill - win_h * 0.7, win_w * 0.12)
                c.fill()
            core.src(c, "#0a1618")
            c.rectangle(cx - 3, sill - win_h, 6, win_h)
            for k in range(1, 5):
                c.rectangle(cx - win_w / 2, sill - win_h + win_w / 2 + k * (win_h - win_w / 2) / 5 - 2.5, win_w, 5)
            c.fill()

        draw_arch(cr, cx, sill, win_w, win_h, kind, fill=window_fill or night, depth=30.0, seed=seed + i)
    # pillars between the bays, and the vault ribs springing from them
    for i in range(bays + 1):
        px = x + pitch * i
        cr.rectangle(px - 44, y, 88, floor_y - y)
        cr.set_source(core.linear(px - 44, 0, px + 44, 0, [core.shade(st, 0.45), core.tint(st, 0.05), core.shade(st, 0.5)]))
        cr.fill()
        cr.rectangle(px - 58, floor_y - 60, 116, 60)
        core.src(cr, core.shade(st, 0.3))
        cr.fill()
    for i in range(bays):
        cx = x + pitch * (i + 0.5)
        cr.set_line_width(26.0)
        core.src(cr, core.shade(st, 0.6), 0.9)
        cr.arc(cx, y + (floor_y - y) * 0.36, pitch * 0.5 - 30, math.pi, TAU)
        cr.stroke()
        cr.set_line_width(6.0)
        core.src(cr, core.tint(st, 0.08), 0.35)
        cr.arc(cx, y + (floor_y - y) * 0.36, pitch * 0.5 - 40, math.pi * 1.05, math.pi * 1.6)
        cr.stroke()
    # the floor: flagstones in one-point perspective, damp and darker toward us
    fl = core.shade(st, 0.3)
    cr.rectangle(x, floor_y, w, y + h - floor_y)
    cr.set_source(core.linear(0, floor_y, 0, y + h, [core.tint(fl, 0.05), core.shade(fl, 0.55)]))
    cr.fill()
    vx, vy = vp
    cr.set_line_width(3.0)
    core.src(cr, core.shade(fl, 0.5), 0.55)
    for k in range(-24, 26):
        x_far = vx + k * 95.0
        t_far = (floor_y - vy) / max(1.0, (y + h - vy))
        x_near = vx + (x_far - vx) / t_far
        cr.move_to(x_far, floor_y)
        cr.line_to(x_near, y + h)
    cr.stroke()
    z = 1.0
    while True:
        yy = floor_y + (y + h - floor_y) * (1.0 - 1.0 / z) * 1.5
        if yy > y + h:
            break
        cr.rectangle(x, yy - 1.5, w, 3.0)
        z += 0.42
    cr.fill()
    cr.save()
    cr.rectangle(x, floor_y, w, y + h - floor_y)
    cr.clip()
    texture(cr, "stone", 0.12, 0.7)
    cr.restore()


# ----------------------------------------------------------------------------------------
# ground: cobbles (dry / wet), reflections, puddles
# ----------------------------------------------------------------------------------------

def draw_cobbles(cr, x, y_top, w, y_bot, kind="night", seed=0, wet=False, size=(9.0, 44.0), vp=None, color=None,
                 texture_alpha=0.14, sheen=None, contrast=1.0):
    """A cobbled street in perspective filling x..x+w, y_top (far) .. y_bot (near): rows of
    rounded river stones that grow toward the viewer, each a little different in size, shape
    and tone, with a lit crown, set in dark joints. vp = (vx, vy) makes the rows' joints
    converge to a vanishing point (the town square); None keeps rows straight (a street seen
    from the side, S3). wet=True: darker glossier stones, water in the joints, a sky sheen that
    grows toward the far rows (where the stones melt into reflection) -- add
    draw_wet_reflections() for the lamps and windows. contrast scales the stone-to-stone
    variation. Static (cache it)."""
    P = palette(kind)
    base = color or core.mix(P["stone"], P["ground"], 0.35)
    if wet:
        base = core.saturate(core.shade(base, 0.22), 0.1)
    joint = core.shade(base, 0.36 if not wet else 0.42)       # dry: sandy grit; wet: dark water
    sky_c = sheen or P["haze"]
    cr.save()
    cr.rectangle(x, y_top, w, y_bot - y_top)
    cr.clip()
    cr.rectangle(x, y_top, w, y_bot - y_top)
    cr.set_source(core.linear(0, y_top, 0, y_bot, [core.mix(joint, sky_c, 0.35 if wet else 0.1), joint]))
    cr.fill()
    span = max(1.0, y_bot - y_top)
    yy = y_top
    row = 0
    while yy < y_bot:
        d = (yy - y_top) / span
        rh = lerp(size[0], size[1], d ** 1.15)
        if vp is not None:
            vx, vy = vp
            k = (yy + rh * 0.5 - vy) / max(1.0, (y_bot - vy))
        else:
            vx, k = 0.0, 1.0
        cw_world = size[1] * 1.5
        off = core.hash01(row, seed + 1) * cw_world
        xx_w = (x - vx) / max(k, 1e-3) - off if vp is not None else x - off * rh / size[1]
        x_end_w = (x + w - vx) / max(k, 1e-3) if vp is not None else x + w
        fade = (1.0 - d) ** 2 * (0.7 if wet else 0.25)          # far rows melt into the sheen
        j = 0
        while xx_w < x_end_w:
            hsh = row * 131 + j
            cw = (cw_world * (0.7 + 0.6 * core.hash01(hsh, seed + 2)) if vp is not None else
                  rh * (1.15 + 0.7 * core.hash01(hsh, seed + 2)))
            if vp is not None:
                sx0, sx1 = vx + xx_w * k, vx + (xx_w + cw) * k
            else:
                sx0, sx1 = xx_w, xx_w + cw
            gap = max(0.8, rh * 0.12)
            cx_, cy_ = (sx0 + sx1) * 0.5, yy + rh * 0.5 + core.jitter(hsh, rh * 0.06, seed + 8)
            # tone: a little per stone, plus broad patches (whole stretches of the street were
            # laid with lighter or darker stone), so it never reads as a printed pattern
            patch = core.noise2(cx_ * 0.0045, yy * 0.012, seed + 9) * 0.16
            v = ((core.hash01(hsh, seed + 3) - 0.5) * 0.26 + patch) * contrast
            c = core.tint(base, v) if v > 0 else core.shade(base, -v)
            c = core.hue_shift(c, (core.hash01(hsh, seed + 4) - 0.5) * 16.0)
            c = core.mix(c, sky_c, fade)
            rx_ = (sx1 - sx0) * 0.5 - gap * (0.7 if not wet else 1.0)
            ry_ = (rh * 0.5 - gap * (0.6 if not wet else 0.8)) * (0.86 + 0.14 * core.hash01(hsh, seed + 10))
            if rx_ > 0.6 and ry_ > 0.4:
                ang = (core.hash01(hsh, seed + 11) - 0.5) * 0.22
                # the stone's rounded underside in shadow, then its face set back toward the top
                core.blob(cr, cx_, cy_, rx_, 0.13, 7, seed=seed + hsh, sy=ry_ / rx_, angle=ang)
                core.src(cr, core.shade(c, 0.3 + 0.1 * contrast))
                cr.fill()
                core.blob(cr, cx_, cy_ - ry_ * 0.13, rx_ * 0.93, 0.13, 7, seed=seed + hsh, sy=ry_ * 0.84 / rx_, angle=ang)
                core.src(cr, c)
                cr.fill()
                # most stones catch the light on their crown -- each a little differently
                hl = core.hash01(hsh, seed + 5)
                if hl > 0.22:
                    hx = cx_ + rx_ * (core.hash01(hsh, seed + 6) - 0.5) * 0.5
                    core.ellipse(cr, hx, cy_ - ry_ * 0.42, rx_ * (0.36 + 0.3 * hl), ry_ * (0.16 + 0.14 * hl))
                    core.src(cr, core.tint(c, (0.12 if not wet else 0.16) + 0.1 * hl), 0.35 + 0.4 * hl)
                    cr.fill()
                if wet and hl > 0.45:
                    # a wet glint of sky on the crown: small and sharp
                    core.ellipse(cr, cx_ + rx_ * (core.hash01(hsh, seed + 7) - 0.5) * 0.6, cy_ - ry_ * 0.5,
                                 rx_ * 0.22, max(0.5, ry_ * 0.09))
                    core.src(cr, core.tint(sky_c, 0.35), (0.25 + 0.4 * (1 - d)) * hl)
                    cr.fill()
            xx_w += cw
            j += 1
        yy += rh
        row += 1
    if wet:
        # the sky's sheen on the wet street, strongest toward the far rows (Fresnel)
        cr.rectangle(x, y_top, w, span)
        cr.set_source(core.linear(0, y_top, 0, y_bot, [core.alpha(sky_c, 0.4), core.alpha(sky_c, 0.1), core.alpha(sky_c, 0.0)]))
        cr.fill()
    texture(cr, "stone", texture_alpha, 0.7)
    cr.restore()


def draw_wet_reflections(cr, lights, ground_y=None, stretch=0.85, width=1.0, seed=0, alpha=1.0, clip=None):
    """Reflections of light sources on a wet street: for each light (x, y, colour, level[,
    base_y]) a long vertical streak of broken horizontal glints below the point where its
    post / wall meets the ground (base_y, default ground_y), as long as the light is high
    (stretch), additive. HouseRig.lights and lantern PropRigs feed it. Cache it in a layer and
    paint it with a flicker alpha, or draw it every frame (~0.5 ms per light)."""
    cr.save()
    if clip is not None:
        cr.rectangle(*clip)
        cr.clip()
    cr.set_operator(cairo.OPERATOR_ADD)
    for i, L_ in enumerate(lights):
        lx, ly, c, lv = L_[0], L_[1], L_[2], L_[3]
        by = L_[4] if len(L_) > 4 else ground_y
        if by is None:
            continue
        H = max(20.0, by - ly)
        length = H * stretch
        cc = core.col(c)
        n = int(18 + length / 8)
        for k in range(n):
            u = k / n
            yy = by + u * length + core.jitter(i * 97 + k, 3.0, seed)
            ww = (16.0 + 26.0 * core.hash01(i * 97 + k, seed + 1)) * width * (1.0 + 0.8 * u)
            hh = 1.2 + 2.8 * core.hash01(i * 97 + k, seed + 2) * (0.6 + u)
            a = alpha * lv * (1.0 - u) ** 1.3 * (0.3 + 0.7 * core.hash01(i * 97 + k, seed + 3))
            xo = core.jitter(i * 97 + k, ww * 0.3, seed + 4)
            cr.set_source_rgba(cc[0], cc[1], cc[2], min(1.0, a * 0.6))
            core.ellipse(cr, lx + xo, yy, ww * 0.5, hh)
            cr.fill()
            if k % 2 == 0:                                   # the hot core of the streak
                cr.set_source_rgba(min(1, cc[0] + 0.3), min(1, cc[1] + 0.3), min(1, cc[2] + 0.3), min(1.0, a * 0.5))
                core.ellipse(cr, lx + xo * 0.3, yy, ww * 0.18, hh * 0.7)
                cr.fill()
        # a soft core glow at the base of the streak
        fx.glow(cr, lx, by + length * 0.15, length * 0.35, c, 0.25 * lv * alpha)
    cr.restore()


def draw_puddle(cr, x, y, rx, ry, kind="rain_night", seed=0, reflections=(), sky=None, rim=True, lights=(),
                stretch=0.85, stones=True):
    """A rain puddle lying in the street at (x, y), about rx x ry: a flat sheet of water that
    drowns the joints (a few stone crowns still break its surface near the edge), darker than
    the wet stones round it -- it mirrors the night facades -- with a pale sheen of sky along
    its far edge, and, crisper and brighter than on the stones, the reflections of the lights:
      * reflections = [(x, colour, level)]: a streak at world x;
      * lights = the (x, y, colour, level[, base_y]) list given to draw_wet_reflections (with
        the same `stretch`): every light whose streak runs over the puddle continues through
        it, sharp -- pass the street's lights and the puddles agree with the street.
    Static (cache it with the street); add puddle_ripples() per frame."""
    P = palette(kind)
    sky_c = sky or P["sky"]
    hz = P["haze"]
    pts = []
    for i in range(20):
        a = TAU * i / 20
        rr = 1.0 + 0.18 * core.noise1(i * 0.8, seed) + 0.07 * math.sin(3 * a + seed)
        pts.append((x + math.cos(a) * rx * rr, y + math.sin(a) * ry * rr))

    def shape(k=1.0, ky=1.0):
        cr.save()
        cr.translate(x, y)
        cr.scale(k, ky)
        cr.translate(-x, -y)
        core.smooth_closed(cr, pts, 0.9)
        cr.restore()

    if rim:
        # the damp, darkened stones round the water: two soft steps
        for k, ky, al in ((1.16, 1.34, 0.14), (1.07, 1.15, 0.16)):
            shape(k, ky)
            core.src(cr, "#000000", al)
            cr.fill()
    shape()
    path = cr.copy_path()
    deep = core.mix(core.shade(sky_c[0], 0.2), P["near"], 0.5)
    cr.set_source(core.linear(0, y - ry * 1.1, 0, y + ry, [(0.0, core.mix(hz, sky_c[-1], 0.35)), (0.28, core.mix(hz, sky_c[1], 0.5)),
                                                         (0.55, core.mix(sky_c[1], deep, 0.6)), (1.0, deep)]))
    cr.fill()
    cr.save()
    cr.append_path(path)
    cr.clip()
    # streaks: the lights mirrored in the water
    streaks = [(lx, c, lv) for (lx, c, lv) in reflections]
    for L_ in lights:
        lx, ly, c, lv = L_[0], L_[1], L_[2], L_[3]
        by = L_[4] if len(L_) > 4 else None
        if by is None or by > y + ry or abs(lx - x) > rx * 1.1:
            continue
        u = (y - by) / max(20.0, (by - ly) * stretch)
        if u < 1.6:                     # a mirror: it holds the light further out than the stones do
            streaks.append((lx, c, lv * max(0.35, 1.0 - max(0.0, u)) ** 0.6))
    cr.set_operator(cairo.OPERATOR_ADD)
    for si, (lx, c, lv) in enumerate(streaks):
        cc = core.col(c)
        fx.glow(cr, lx, y, max(rx * 0.35, 30.0), c, 0.22 * lv)
        n = max(6, int(ry * 2 / 3.0))
        for k in range(n):
            yy = y - ry * 1.1 + (k + 0.5) * 2.2 * ry / n
            h = core.hash01(si * 61 + k, seed + 7)
            ww = (10.0 + 14.0 * h) * (1.0 + 0.5 * (yy - y + ry) / (2 * ry))
            xo = core.jitter(si * 61 + k, 3.0, seed + 8)
            cr.set_source_rgba(cc[0], cc[1], cc[2], min(1.0, 0.75 * lv * (0.55 + 0.45 * h)))
            core.ellipse(cr, lx + xo, yy, ww, 1.1 + 0.9 * h)
            cr.fill()
            cr.set_source_rgba(min(1, cc[0] + 0.35), min(1, cc[1] + 0.35), min(1, cc[2] + 0.35), min(1.0, 0.55 * lv))
            core.ellipse(cr, lx + xo * 0.4, yy, ww * 0.3, 0.8 + 0.6 * h)
            cr.fill()
    cr.set_operator(cairo.OPERATOR_OVER)
    if stones:
        # crowns of the drowned stones breaking the surface near the shallow edge
        st = core.saturate(core.shade(core.mix(P["stone"], P["ground"], 0.35), 0.25), 0.1)
        for i in range(int(4 + rx / 30)):
            a = TAU * core.hash01(i, seed + 21)
            rr = 0.72 + 0.22 * core.hash01(i, seed + 22)
            sx_, sy_ = x + math.cos(a) * rx * rr, y + math.sin(a) * ry * rr
            sr = ry * (0.22 + 0.18 * core.hash01(i, seed + 23))
            core.ellipse(cr, sx_, sy_, sr * 1.7, sr * 0.55)
            core.src(cr, st, 0.85)
            cr.fill()
            core.ellipse(cr, sx_ - sr * 0.2, sy_ - sr * 0.22, sr * 0.7, sr * 0.16)
            core.src(cr, core.tint(hz, 0.3), 0.35)
            cr.fill()
    # the far edge catches a bright line of sky
    cr.set_line_width(max(1.0, ry * 0.07))
    core.src(cr, core.tint(sky_c[-1], 0.25), 0.4)
    cr.arc(x, y + ry * 0.45, rx * 0.95, math.pi * 1.18, math.pi * 1.82)
    cr.stroke()
    cr.restore()


def puddle_ripples(cr, t, x, y, rx, ry, n=5, seed=0, color="#cfe0ff", alpha=0.32, rate=1.0, squash=None):
    """Raindrop rings spreading on a puddle (pure function of t): n ring slots, each restarting
    at a new random spot inside the puddle -- a bright fleck where the drop lands, then one thin
    ring that widens and fades. The rings are circles lying on the ground, so they take the
    ground's perspective squash (default: ry/rx, but never flatter than 0.35), not the puddle's
    outline. ~0.1 ms per ring."""
    c = core.col(color)
    sq = squash if squash is not None else max(0.35, min(1.0, ry / max(rx, 1e-3)))
    cr.save()
    cr.translate(x, y)
    cr.scale(1.0, ry / max(rx, 1e-3))
    cr.arc(0, 0, rx * 0.95, 0, TAU)
    cr.scale(1.0, max(rx, 1e-3) / ry)
    cr.clip()
    for i in range(n):
        period = (0.7 + 0.6 * core.hash01(i, seed)) / rate
        ph = core.hash01(i, seed + 1) * period
        cyc = math.floor((t + ph) / period)
        u = ((t + ph) % period) / period
        px = (core.hash01(cyc * 31 + i, seed + 2) - 0.5) * rx * 1.4
        py = (core.hash01(cyc * 31 + i, seed + 3) - 0.5) * ry * 1.4
        rr = min(rx, ry / sq) * (0.05 + 0.24 * u) + 1.5
        if u < 0.12:
            cr.set_source_rgba(c[0], c[1], c[2], alpha * 1.6 * (1.0 - u / 0.12))
            core.ellipse(cr, px, py, 1.6, 1.0)
            cr.fill()
        cr.save()
        cr.translate(px, py)
        cr.scale(1.0, sq)
        cr.new_path()
        cr.arc(0, 0, rr, 0, TAU)
        cr.restore()
        cr.set_line_width(1.1)
        cr.set_source_rgba(c[0], c[1], c[2], alpha * (1.0 - u) ** 1.6)
        cr.stroke()
    cr.restore()


def draw_ground_shadow(cr, x, y, rx, ry, alpha=0.35, color=(0.02, 0.03, 0.06)):
    """A soft elliptical shadow on the ground (trees, posts, benches, carts)."""
    c = core.col(color)
    cr.save()
    cr.translate(x, y)
    cr.scale(1.0, ry / max(rx, 1e-3))
    g = cairo.RadialGradient(0, 0, 0, 0, 0, rx)
    g.add_color_stop_rgba(0.0, c[0], c[1], c[2], alpha)
    g.add_color_stop_rgba(0.5, c[0], c[1], c[2], alpha * 0.6)
    g.add_color_stop_rgba(1.0, c[0], c[1], c[2], 0.0)
    cr.set_source(g)
    cr.arc(0, 0, rx, 0, TAU)
    cr.fill()
    cr.restore()


# ----------------------------------------------------------------------------------------
# the garden: grass, gravel, hedges, flower beds, the old oak
# ----------------------------------------------------------------------------------------

def draw_grass(cr, x, y, w, h, kind="dusk", seed=0, density=1.0, light_dx=-0.6, color=None, flowers=True, blades=True):
    """A meadow-lawn filling (x, y, w, h), y = its far edge: hazier and finer at the back,
    deeper and coarser toward us, soft patches of colour, blade tufts in three tones that grow
    with nearness, and a sprinkle of tiny wild flowers. Static (cache it)."""
    P = palette(kind)
    fd, fm, fl = P["foliage"]
    base = color or fm
    far_c = haze_toward(base, P["haze"], 0.45)
    near_c = core.shade(base, 0.15)
    cr.save()
    cr.push_group()
    cr.rectangle(x, y, w, h)
    cr.clip()
    cr.rectangle(x, y, w, h)
    cr.set_source(core.linear(0, y, 0, y + h, [far_c, base, near_c]))
    cr.fill()
    # soft patches
    for i in range(int(w * h / 26000 * density) + 4):
        px = x + core.hash01(i, seed + 1) * w
        py = y + core.hash01(i, seed + 2) * h
        d = (py - y) / max(1.0, h)
        core.blob(cr, px, py, 60.0 + 160.0 * d, 0.25, 8, seed=seed + i, sy=0.22)
        tone = (fl, fd, core.mix(fm, P["sky"][-1], 0.3))[i % 3]
        core.src(cr, haze_toward(tone, P["haze"], 0.4 * (1 - d)), 0.09)
        cr.fill()
    texture(cr, "foliage", 0.12, 1.2)
    if blades:
        tones = [haze_toward(core.shade(fd, 0.1), P["haze"], 0.0), fm, core.mix(fl, P["sky"][-1], 0.25)]
        for layer_k, tone in enumerate(tones):
            cr.new_path()
            n = int(w * h / 2600 * density)
            for i in range(n):
                hsh = i * 3 + layer_k
                px = x + core.hash01(hsh, seed + 11) * w
                d = core.hash01(hsh, seed + 12) ** 0.8
                py = y + d * h
                L = (4.0 + 22.0 * d) * (0.6 + 0.8 * core.hash01(hsh, seed + 13))
                lean = (core.hash01(hsh, seed + 14) - 0.5) * 0.8 + light_dx * 0.1
                for b in range(3):
                    bl = lean + (b - 1) * 0.35
                    core.tapered(cr, [(px + b * 2.0, py), (px + b * 2.0 + math.sin(bl) * L * 0.5, py - L * 0.5),
                                      (px + b * 2.0 + math.sin(bl) * L, py - L)], max(0.8, L * 0.12), 0.0)
            core.src(cr, haze_toward(tone, P["haze"], 0.15), 0.55 if layer_k == 0 else 0.5)
            cr.fill()
    if flowers:
        for i in range(int(w * h / 9000 * density)):
            px = x + core.hash01(i, seed + 21) * w
            d = core.hash01(i, seed + 22)
            py = y + d * h
            c = ("#f2e8f0", "#f6d46a", "#e8a8c8", "#b8a8e8")[i % 4]
            core.src(cr, haze_toward(c, P["haze"], 0.35 * (1 - d)), 0.85)
            core.circle(cr, px, py, 1.0 + 2.2 * d)
            cr.fill()
    cr.pop_group_to_source()
    cr.mask(core.linear(0, y, 0, y + 46.0, [(0.0, (0, 0, 0, 0.0)), (1.0, (0, 0, 0, 1.0))]))
    cr.restore()


def draw_gravel_path(cr, pts, widths=(60.0, 360.0), kind="dusk", seed=0, color=None, edge_tufts=True):
    """A gravel path along the centre line pts (far end first), widening from widths[0] to
    widths[1] toward us: a pale crunchy band, speckled light and dark, stones growing with
    nearness, its edges nibbled by grass. Static."""
    P = palette(kind)
    base = color or core.mix(core.mix(P["ground"], P["stone"], 0.5), "#b4a282", 0.4)
    sp = core.spline(pts, 8)
    total = core.polyline_length(sp)
    cr.new_path()
    core.tapered(cr, sp, widths[0], widths[1], profile=lambda s_: lerp(widths[0], widths[1], s_ ** 1.2) * 1.06 + 6.0, cap=False)
    core.src(cr, core.shade(base, 0.35), 0.5)                 # the damp, trodden edge
    cr.fill()
    core.tapered(cr, sp, widths[0], widths[1], profile=lambda s_: lerp(widths[0], widths[1], s_ ** 1.2), cap=False)
    path = cr.copy_path()
    cr.set_source(core.linear(0, sp[0][1], 0, sp[-1][1], [haze_toward(base, P["haze"], 0.35), base, core.shade(base, 0.12)]))
    cr.fill()
    cr.save()
    cr.append_path(path)
    cr.clip()
    texture(cr, "grain", 0.35, 0.7)
    # pebbles: dark and light specks, bigger toward the near end
    acc = 0.0
    for i in range(1, len(sp)):
        (ax, ay), (bx, by) = sp[i - 1], sp[i]
        seg = math.hypot(bx - ax, by - ay)
        acc += seg
        u = acc / max(1.0, total)
        wd = lerp(widths[0], widths[1], u ** 1.2)
        nx, ny = -(by - ay) / max(seg, 1e-6), (bx - ax) / max(seg, 1e-6)
        for k in range(int(seg * wd / 220) + 1):
            hsh = i * 53 + k
            o = (core.hash01(hsh, seed + 1) - 0.5) * wd
            px, py = ax + nx * o + (bx - ax) * core.hash01(hsh, seed + 2), ay + ny * o + (by - ay) * core.hash01(hsh, seed + 2)
            r = 0.8 + 3.0 * u * core.hash01(hsh, seed + 3)
            light = core.hash01(hsh, seed + 4) > 0.45
            core.src(cr, core.tint(base, 0.35) if light else core.shade(base, 0.35), 0.75)
            core.ellipse(cr, px, py, r * 1.3, r * 0.8)
            cr.fill()
    cr.restore()
    if edge_tufts:
        fd, fm, fl = P["foliage"]
        cr.new_path()
        acc = 0.0
        for i in range(1, len(sp)):
            (ax, ay), (bx, by) = sp[i - 1], sp[i]
            seg = math.hypot(bx - ax, by - ay)
            acc += seg
            u = acc / max(1.0, total)
            wd = lerp(widths[0], widths[1], u ** 1.2)
            nx, ny = -(by - ay) / max(seg, 1e-6), (bx - ax) / max(seg, 1e-6)
            for side in (-1, 1):
                if core.hash01(i * 2 + side, seed + 9) < 0.5:
                    continue
                px, py = bx + nx * side * wd * 0.5, by + ny * side * wd * 0.5
                L = 4.0 + 14.0 * u
                for b in range(3):
                    core.tapered(cr, [(px + b * 2 - 2, py), (px + b * 2 - 2 + (b - 1) * L * 0.25, py - L)], max(0.8, L * 0.15), 0.0)
        core.src(cr, fm, 0.8)
        cr.fill()


def _foliage_tones(P):
    """(dark, mid, lit, highlight) foliage tones for a palette: the lit side takes a little of
    the sky's warmth (dusk/golden) but stays green and saturated."""
    fd, fm, fl = P["foliage"]
    warm = P["sky"][-1]
    lit = core.saturate(core.mix(core.mix(fl, fm, 0.3), warm, 0.12), 0.15)
    return core.shade(fd, 0.08), fm, lit, core.tint(lit, 0.16)


def _scallops(circles, k=0.2, step=0.42):
    """Small bumps all round the outer boundary of a union of circles: a leafy silhouette."""
    out = []
    for i, (cx, cy, r) in enumerate(circles):
        n = max(6, int(TAU * r / (r * k * 2 * step + 1e-6) / 2.2))
        for j in range(n):
            a = TAU * j / n + i * 0.37
            px, py = cx + math.cos(a) * r, cy + math.sin(a) * r
            inside = False
            for m, (ox, oy, orr) in enumerate(circles):
                if m != i and (px - ox) ** 2 + (py - oy) ** 2 < (orr * 0.96) ** 2:
                    inside = True
                    break
            if not inside:
                out.append((px - math.cos(a) * r * k * 0.35, py - math.sin(a) * r * k * 0.35, r * k))
    return out


def _leaf_mass(cr, circles, dark, mid, lit, light_dx=-0.6, light_dy=-0.8, dabs=True, seed=0, alpha=1.0, hi=None):
    """A mass of foliage from (x, y, r) circles: a scalloped leafy silhouette in the shadow tone,
    a mid tone and a lit tone stepping toward the light, with small clusters of leaves -- darker
    ones in the shade (under the lit tone), lighter ones along the bright edge -- so it reads as
    leaves, not spots."""
    sc = _scallops(circles)
    allc = circles + sc

    def add(cl, dx=0.0, dy=0.0, k=1.0):
        cr.new_path()
        for (cx, cy, r) in cl:
            cr.new_sub_path()
            cr.arc(cx + dx, cy + dy, r * k, 0, TAU)

    def clusters(lit_side):
        col = (hi or core.tint(lit, 0.14)) if lit_side else core.mix(dark, mid, 0.5)
        cr.new_path()
        for i, (cx, cy, r) in enumerate(circles):
            for k in range(int(r / 10) + 3):
                a = core.hash01(i * 17 + k, seed + 5) * TAU
                rr = r * (0.45 + 0.5 * core.hash01(i * 17 + k, seed + 6))
                px, py = cx + math.cos(a) * rr, cy + math.sin(a) * rr
                facing = math.cos(a) * light_dx + math.sin(a) * light_dy
                if (lit_side and facing < 0.45) or (not lit_side and (facing > -0.4 or core.hash01(i * 17 + k, seed + 8) > 0.6)):
                    continue
                lr = r * (0.055 + 0.035 * core.hash01(i * 17 + k, seed + 7)) + 0.8
                for m in range(3):
                    b_ = a + m * 2.1
                    cr.new_sub_path()
                    cr.arc(px + math.cos(b_) * lr * 0.9, py + math.sin(b_) * lr * 0.9, lr, 0, TAU)
        core.src(cr, col, 0.85)
        cr.fill()

    rmax = max(r for _, _, r in circles)
    if alpha < 1.0:
        cr.push_group()
    add(allc)
    core.src(cr, dark)
    cr.fill()
    cr.save()
    add(allc)
    cr.clip()
    add(allc, light_dx * rmax * 0.16, light_dy * rmax * 0.16, 0.92)
    core.src(cr, mid)
    cr.fill()
    if dabs:
        clusters(False)
    add(circles, light_dx * rmax * 0.36, light_dy * rmax * 0.36, 0.78)
    core.src(cr, lit)
    cr.fill()
    if dabs:
        clusters(True)
        texture(cr, "foliage", 0.08, 0.6)
    cr.restore()
    if alpha < 1.0:
        cr.pop_group_to_source()
        cr.paint_with_alpha(alpha)


def draw_hedge(cr, x, y, w, h, kind="dusk", seed=0, light_dx=-0.6, color=None, shadow=True):
    """A clipped box hedge (x, y) = its bottom-left on the ground, w x h: a leafy rounded block
    with a bumpy crown, lit along its top and light side, darker toward its foot, leaf dabs.
    Static."""
    P = palette(kind)
    fd, fm, fl = P["foliage"]
    if color:
        fm = color
    if shadow:
        draw_ground_shadow(cr, x + w / 2, y, w * 0.6, 14.0, 0.35)
    circles = []
    # the crown: a row of overlapping bumps; the body: big circles that fill the block
    n = max(3, int(w / (h * 0.32)))
    for i in range(n):
        u = (i + 0.5) / n
        r = h * (0.2 + 0.06 * core.hash01(i, seed + 1))
        circles.append((x + u * w, y - h + r * 0.9 + core.jitter(i, 3.0, seed), r))
    for i in range(n):
        u = (i + 0.5) / n
        circles.append((x + u * w, y - h * 0.45, h * 0.36))
    for side in (0, 1):
        circles.append((x + side * w + (h * 0.12 if side == 0 else -h * 0.12), y - h * 0.5, h * 0.38))
    cr.save()
    cr.rectangle(x - h, y - h * 1.5, w + 2 * h, h * 1.5)        # nothing below the ground line
    cr.clip()
    dk, md, lt, hi = _foliage_tones(P)
    if color:
        md = color
    _leaf_mass(cr, circles, dk, md, lt, light_dx, -0.8, True, seed, hi=hi)
    cr.new_path()
    for (cx, cy, r) in circles + _scallops(circles):
        cr.new_sub_path()
        cr.arc(cx, cy, r, 0, TAU)
    cr.clip()
    cr.rectangle(x - h, y - h * 0.55, w + 2 * h, h * 0.55)
    cr.set_source(core.linear(0, y - h * 0.55, 0, y, [core.alpha(fd, 0.0), core.alpha(core.shade(fd, 0.3), 0.75)]))
    cr.fill()
    cr.restore()


def draw_flower_bed(cr, x, y, w, h, kind="dusk", seed=0, colors=None, wattle=True):
    """A cottage flower bed (x, y) = bottom-left, w x h: a mound of leafy plants starred with
    small blooms (pink, white, lavender, gold) behind a low woven-willow (wattle) edging.
    Static."""
    P = palette(kind)
    fd, fm, fl = P["foliage"]
    cols = colors or ("#e88aa8", "#f4ecf0", "#b49ae0", "#f2c85a", "#e86a6a")
    circles = []
    for i in range(max(3, int(w / 36))):
        u = (i + 0.5) / max(3, int(w / 36))
        r = h * (0.32 + 0.18 * core.hash01(i, seed + 1))
        circles.append((x + u * w, y - h * 0.38 - r * 0.3 * core.hash01(i, seed + 2), r))
    cr.save()
    cr.rectangle(x - h, y - h * 2, w + 2 * h, h * 2)
    cr.clip()
    dk, md, lt, hi = _foliage_tones(P)
    _leaf_mass(cr, circles, dk, md, lt, -0.6, -0.8, True, seed, hi=hi)
    for i in range(int(w * h / 160)):
        px = x + core.hash01(i, seed + 5) * w
        py = y - h * (0.25 + 0.75 * core.hash01(i, seed + 6))
        c = haze_toward(cols[i % len(cols)], P["haze"], 0.12)
        r = 2.2 + 2.0 * core.hash01(i, seed + 7)
        core.src(cr, c, 0.95)
        for k in range(5):
            a = k * TAU / 5 + i
            core.circle(cr, px + math.cos(a) * r * 0.55, py + math.sin(a) * r * 0.55, r * 0.5)
        cr.fill()
        core.src(cr, "#f6e08a", 0.9)
        core.circle(cr, px, py, r * 0.25)
        cr.fill()
    cr.restore()
    if wattle:
        wc = core.mix("#8a6a46", P["haze"], 0.15)
        cr.rectangle(x - 6, y - 24, w + 12, 24)
        core.src(cr, core.shade(wc, 0.3))
        cr.fill()
        for row in range(3):
            yy = y - 20 + row * 7
            cr.new_path()
            for k in range(int(w / 18) + 1):
                xx = x - 6 + k * 18
                off = 2.2 if (k + row) % 2 else -2.2
                core.ellipse(cr, xx + 9, yy + off * 0.4, 10.5, 3.4)
            core.src(cr, wc)
            cr.fill()
        for k in range(int(w / 54) + 2):
            cr.rectangle(x - 6 + k * 54, y - 30, 5, 30)
        core.src(cr, core.shade(wc, 0.2))
        cr.fill()


def _oak_parts(scale, seed):
    """Geometry of the old oak at scale 1.0 (base at the origin): limbs [(spine, w0, w1, cap)]
    -- the trunk, its root flares, the great limbs and their branches -- and the crown's leaf
    clumps [(cx, cy, [(x, y, r)...]), ...]. The crown is an arch: low and broad at the ends of
    the two long horizontal limbs, lifted in the middle, so the trunk's crotch and the limbs
    fanning out from it show under it (that is what makes it read as an OAK)."""
    rnd = lambda k: core.hash01(k, seed + 300)            # noqa: E731
    jit = lambda k, a: (rnd(k) - 0.5) * 2.0 * a             # noqa: E731
    limbs = []
    # the trunk, short and stout, with a slight twist; the root flares
    limbs.append(([(0.0, 0.0), (5.0, -110.0), (-7.0, -205.0), (-2.0, -285.0)], 150.0, 104.0, False))
    for sx in (-1, 1):
        limbs.append(([(sx * 28.0, -56.0), (sx * 90.0, -12.0), (sx * 156.0, 4.0)], 70.0, 6.0, True))
    limbs.append(([(10.0, -30.0), (36.0, -4.0), (58.0, 6.0)], 40.0, 5.0, True))
    # the great limbs from the crotch: two long ones reaching out nearly level, three climbing
    great = [
        [(-26.0, -262.0), (-170.0, -362.0 + jit(1, 12)), (-330.0, -436.0 + jit(2, 14)), (-440.0, -468.0)],
        [(-14.0, -280.0), (-92.0, -452.0 + jit(3, 14)), (-180.0, -626.0)],
        [(-2.0, -296.0), (-26.0, -452.0), (-14.0, -650.0)],
        [(10.0, -288.0), (66.0, -478.0 + jit(4, 14)), (104.0, -700.0)],
        [(26.0, -262.0), (184.0, -348.0 + jit(5, 12)), (364.0, -410.0 + jit(6, 14)), (462.0, -436.0)],
    ]
    widths = [(74.0, 16.0), (62.0, 16.0), (40.0, 12.0), (60.0, 16.0), (72.0, 16.0)]
    for pts, (w0, w1) in zip(great, widths):
        limbs.append((pts, w0, w1, True))
    # branches off the great limbs, up into the clumps
    for pts in ([(-250.0, -404.0), (-292.0, -520.0), (-318.0, -604.0)],
                [(-130.0, -532.0), (-208.0, -604.0), (-262.0, -660.0)],
                [(80.0, -590.0), (160.0, -668.0), (214.0, -716.0)],
                [(270.0, -382.0), (318.0, -492.0), (330.0, -566.0)],
                [(-372.0, -452.0), (-420.0, -520.0)],
                [(392.0, -420.0), (430.0, -498.0)]):
        limbs.append((pts, 24.0, 7.0, True))
    clumps = []
    centers = [(-438.0, -506.0, 122.0), (-298.0, -650.0, 172.0), (-126.0, -786.0, 204.0), (-4.0, -676.0, 150.0),
               (116.0, -806.0, 212.0), (314.0, -660.0, 176.0), (456.0, -478.0, 116.0)]
    for i, (cx, cy, r) in enumerate(centers):
        cx += jit(i + 10, 18.0)
        cy += jit(i + 20, 12.0)
        circ = []
        for k in range(8):
            a = TAU * k / 8 + rnd(i * 7 + k)
            rr = r * (0.42 + 0.22 * rnd(i * 7 + k + 50))
            circ.append((cx + math.cos(a) * r * 0.58, cy + math.sin(a) * r * 0.42, rr))
        circ.append((cx, cy, r * 0.62))
        clumps.append((cx, cy, circ))
    clumps.sort(key=lambda c: -c[1])           # lower clumps first: the top ones overlap them
    return limbs, clumps


def _oak_bounds(limbs):
    """(x0, y0, x1, y1) of the trunk and limbs at scale 1.0, ground shadow included."""
    xs, ys = [-300.0, 300.0], [40.0]
    for pts, w0, w1, cap in limbs:
        for (px, py) in pts:
            xs += [px - w0 / 2, px + w0 / 2]
            ys += [py - w0 / 2, py + w0 / 2]
    return min(xs), min(ys), max(xs), max(ys)


def _oak_trunk(cr, P, limbs, light_dx, kind):
    """The trunk and limbs as one bark silhouette: base tone, a lit band toward the light and a
    shadow band away from it on every limb (clipped to the silhouette, so horizontal limbs get
    a lit top and vertical ones a lit side), bark furrows, and the dark crotch."""
    bark = core.mix(core.mix("#4a3a32", P["timber"], 0.5), P["far"], 0.2)     # follows the light of the hour
    bl = core.tint(bark, 0.24)
    bd = core.shade(bark, 0.38)
    draw_ground_shadow(cr, 0.0, 0.0, 300.0, 30.0, 0.45)
    ldx, ldy = light_dx, -0.8
    n = math.hypot(ldx, ldy) or 1.0
    ldx, ldy = ldx / n, ldy / n
    spines = [(core.spline(pts, 6), w0, w1, cap) for (pts, w0, w1, cap) in limbs]

    def silhouette():
        cr.new_path()
        for sp, w0, w1, cap in spines:
            core.tapered(cr, sp, w0, w1, cap=cap)

    silhouette()
    core.src(cr, bark)
    cr.fill()
    cr.save()
    silhouette()
    cr.clip()
    cr.new_path()
    for sp, w0, w1, cap in spines:
        core.tapered(cr, [(px - ldx * w0 * 0.34, py - ldy * w0 * 0.34) for px, py in sp], w0 * 0.62, w1 * 0.62, cap=cap)
    core.src(cr, bd, 0.62)
    cr.fill()
    for sp, w0, w1, cap in spines:
        core.tapered(cr, [(px + ldx * w0 * 0.3, py + ldy * w0 * 0.3) for px, py in sp], w0 * 0.5, w1 * 0.5, cap=cap)
    core.src(cr, bl, 0.72)
    cr.fill()
    # bark furrows: long wavy grooves up the trunk and along the great limbs
    cr.set_line_width(3.0)
    core.src(cr, bd, 0.5)
    for k in range(7):
        x0 = -54.0 + k * 18.0 + core.jitter(k, 4.0, 77)
        y0 = -6.0 - 46.0 * core.hash01(k, 79)                # some grooves start up the trunk...
        y1 = -272.0 + 70.0 * core.hash01(k, 78)               # ...and some give out early
        cr.move_to(x0, y0)
        cr.curve_to(x0 + 8 + core.jitter(k, 4.0, 80), (2 * y0 + y1) / 3, x0 - 9 + core.jitter(k, 4.0, 81),
                    (y0 + 2 * y1) / 3, x0 * 0.7 + 3, y1)
    for sp, w0, w1, cap in spines[4:9]:
        for off in (-0.18, 0.16):
            pts = []
            for i in range(len(sp)):
                if i == 0:
                    tx, ty = sp[1][0] - sp[0][0], sp[1][1] - sp[0][1]
                else:
                    tx, ty = sp[i][0] - sp[i - 1][0], sp[i][1] - sp[i - 1][1]
                L = math.hypot(tx, ty) or 1.0
                w = w0 + (w1 - w0) * i / max(1, len(sp) - 1)
                pts.append((sp[i][0] - ty / L * w * off, sp[i][1] + tx / L * w * off))
            core.smooth_open(cr, pts[: int(len(pts) * 0.7)])
    cr.stroke()
    # a knot hole with a lit lip
    core.ellipse(cr, -26.0, -158.0, 11.0, 15.0)
    core.src(cr, core.shade(bark, 0.6), 0.85)
    cr.fill()
    cr.set_line_width(3.0)
    core.src(cr, bl, 0.7)
    cr.arc(-26.0, -158.0, 13.0, math.pi * 1.1, math.pi * 1.9)
    cr.stroke()
    # the crotch where the limbs part sits in its own shadow
    core.circle(cr, -4.0, -286.0, 70.0)
    cr.set_source(core.radial(-4.0, -286.0, 70.0, [core.alpha(bd, 0.75), core.alpha(bd, 0.0)]))
    cr.fill()
    cr.restore()


def draw_oak(cr, x, y, scale=1.0, kind="dusk", seed=0, t=0.0, sway=0.0, light_dx=-0.6, part="all"):
    """The old oak (S6-S8, behind the bench): a stout flared trunk parting into great limbs --
    two reaching out nearly level, three climbing -- under a broad arched crown of leaf clumps,
    lit from the light side, a soft shadow at its foot. Anchor (x, y) = the base of the trunk;
    about 1200 wide x 1030 tall at scale 1.0, the crown's underside ~370 up at its ends and ~520
    in the middle (scale it down: 0.45-0.7 behind the bench). part "trunk" / "crown" / "all".
    For the gentle sway use OakTree (cached clumps, cheap per frame)."""
    P = palette(kind)
    fd, fm, fl = P["foliage"]
    limbs, clumps = _oak_parts(scale, seed)
    cr.save()
    cr.translate(x, y)
    cr.scale(scale, scale)
    if part in ("all", "trunk"):
        _oak_trunk(cr, P, limbs, light_dx, kind)
    if part in ("all", "crown"):
        dk, md, lt, hi = _foliage_tones(P)
        for i, (cx, cy, circ) in enumerate(clumps):
            dx = sway * 6.0 * (0.4 + 0.6 * (-cy / 900.0)) * math.sin(t * 0.7 + i * 1.3)
            cr.save()
            cr.translate(dx, 0.0)
            _leaf_mass(cr, circ, dk, md, lt, light_dx, -0.8, True, seed + i, hi=hi)
            cr.restore()
    cr.restore()


class OakTree:
    """The old oak, cached for animation: the trunk in one layer and each leaf clump in its own
    small layer, so the crown can sway every frame for ~2-4 ms.

        tree = env.OakTree(380, 930, 0.6, kind="dusk")      # in setup()
        tree.draw(cr, t)                                   # every frame (inside the camera view)

    blur softens it for depth of field. Anchor and size as draw_oak."""

    def __init__(self, x, y, scale=1.0, kind="dusk", seed=0, light_dx=-0.6, blur=0.0, sway=1.0):
        self.x, self.y, self.scale, self.sway = x, y, scale, sway
        P = palette(kind)
        fd, fm, fl = P["foliage"]
        limbs, clumps = _oak_parts(scale, seed)
        s = scale

        def trunk(cr):
            cr.translate(x, y)
            cr.scale(s, s)
            _oak_trunk(cr, P, limbs, light_dx, kind)

        bx0, by0, bx1, by1 = _oak_bounds(limbs)
        pad = 8.0 + 3.0 * blur
        self.trunk = fx.Layer(trunk, (bx1 - bx0) * s + 2 * pad, (by1 - by0) * s + 2 * pad, x + bx0 * s - pad,
                              y + by0 * s - pad, blur=blur)
        self.clumps = []
        dk, md, lt, hi = _foliage_tones(P)
        for i, (cx, cy, circ) in enumerate(clumps):
            rmax = max(max(abs(px - cx), abs(py - cy)) + r for px, py, r in circ) * 1.25 + 20

            def clump(cr, circ=circ, i=i):
                cr.translate(x, y)
                cr.scale(s, s)
                _leaf_mass(cr, circ, dk, md, lt, light_dx, -0.8, True, seed + i, hi=hi)

            lx, ly = x + (cx - rmax) * s, y + (cy - rmax) * s
            self.clumps.append((fx.Layer(clump, 2 * rmax * s + 4, 2 * rmax * s + 4, lx, ly, blur=blur), cy, i))

    def draw(self, cr, t, sway=None, alpha=1.0):
        sw = self.sway if sway is None else sway
        self.trunk.paint(cr, alpha)
        for L_, cy, i in self.clumps:
            k = 0.4 + 0.6 * (-cy / 900.0)
            dx = sw * 6.0 * self.scale * k * (math.sin(t * 0.7 + i * 1.3) + 0.35 * core.noise1(t * 0.4 + i, 11))
            dy = sw * 1.5 * self.scale * k * math.sin(t * 0.9 + i * 0.7)
            L_.paint(cr, alpha, dx, dy)


# ----------------------------------------------------------------------------------------
# rain
# ----------------------------------------------------------------------------------------

class Rain:
    """Rain in three depths (far: fine and faint; mid; near: long bright streaks), splashes on
    a ground band, and drops that light up inside lamp glows (the classic street-lamp rain).

        rain = env.Rain(kind="rain_night", ground=(860, 1080))        # setup
        rain.draw(cr, t, lights=[(x, y, radius, colour)])            # every frame, after the set

    rect = the area it falls in (world px); density scales every layer; angle = slant (rad).
    ~6-10 ms per frame at density 1."""

    def __init__(self, rect=(-90.0, -80.0, 2100.0, 1240.0), kind="rain_night", density=1.0, angle=0.16, seed=0,
                 ground=None, color=None, near=True):
        self.rect = rect
        self.kind = kind
        self.d = density
        self.angle = angle
        self.seed = seed
        self.ground = ground
        P = palette(kind)
        self.color = color or core.mix(P["haze"], "#c8d8f0", 0.6)
        self.near = near

    def draw(self, cr, t, lights=(), alpha=1.0):
        x, y, w, h = self.rect
        d, a, sd, c = self.d, self.angle, self.seed, self.color
        fx.rain(cr, t, self.rect, int(260 * d), 1050.0, a, 16.0, 1.0, c, 0.16 * alpha, sd)
        fx.rain(cr, t, self.rect, int(150 * d), 1500.0, a, 30.0, 1.5, c, 0.24 * alpha, sd + 1)
        area = max(1.0, w * h)
        for i, (lx, ly, r, lc) in enumerate(lights):   # drops lit up inside a lamp's glow
            box = (lx - r, ly - r, 2 * r, 2 * r)
            k = (4 * r * r) / area
            cr.save()
            cr.arc(lx, ly, r, 0, TAU)
            cr.clip()
            cr.set_operator(cairo.OPERATOR_ADD)
            fx.rain(cr, t, box, max(4, int(150 * d * k * 1.6)), 1500.0, a, 30.0, 1.6, lc, 0.5 * alpha, sd + 11 + i)
            fx.rain(cr, t, box, max(6, int(260 * d * k * 1.6)), 1050.0, a, 16.0, 1.1, lc, 0.32 * alpha, sd + 21 + i)
            cr.restore()
        if self.ground is not None:
            g0, g1 = self.ground
            fx.splashes(cr, t, (x, g0, w, g1 - g0), int(70 * d), 9.0, core.tint(c, 0.2), 0.45 * alpha, sd + 2)
        if self.near:
            fx.rain(cr, t, self.rect, int(34 * d), 2300.0, a, 72.0, 2.4, core.tint(c, 0.2), 0.22 * alpha, sd + 3)


# ----------------------------------------------------------------------------------------
# character-sheet hook (python3 film/render.py --sheet --only env; and the showcase)
# ----------------------------------------------------------------------------------------

def sheet_items():
    """Sheet cells: every environment piece, in every palette it is meant for."""
    from .characters import base as B
    items = []

    def add(label, w, h, fn, group):
        items.append(B.SheetItem(label, w, h, fn, group))

    def panel(fn, w=600, h=338):
        def draw(cr):
            cr.save()
            cr.scale(w / 1920.0, h / 1080.0)
            fn(cr)
            cr.restore()
        return draw

    # ---- skies and distance -------------------------------------------------------------
    g = "skies, the castle on the hill, rolling hills (one per palette)"
    for kind in ("dusk", "golden", "blue_hour", "night", "rain_night", "evening"):
        def fn(cr, kind=kind):
            draw_sky(cr, 0, 0, 1920, 1080, kind=kind, horizon=680, sun=(1250, 650, 40) if kind == "golden" else None, seed=1)
            draw_castle_hill(cr, 1350, 520, 0.85, kind=kind, hill_w=900, hill_h=160, seed=1)
            draw_hills(cr, 0, 1920, 760, kind=kind, seed=2)
            draw_mist(cr, 0, 700, 1920, 160, palette(kind)["haze"], 0.3, seed=1)
            if palette(kind).get("star"):
                StarField((0, 0, 1920, 500), 90, seed=2).draw(cr, 1.0)
        add(f"{kind}", 600, 338, panel(fn), g)

    # ---- the town -------------------------------------------------------------------------
    g = "the town: half-timbered houses (roof gable / side + dormer / thatch), street row, far roofline"
    for k, (roof, kind, lit) in enumerate((("gable", "evening", 0.6), ("side", "night", 0.7), ("thatch", "golden", 0.0))):
        def fn(cr, roof=roof, kind=kind, lit=lit, k=k):
            P = palette(kind)
            core.vgrad(cr, 0, 0, 340, 420, [P["sky"][1], P["sky"][-1]])
            cr.rectangle(0, 390, 340, 30)
            core.src(cr, P["ground"])
            cr.fill()
            draw_house(cr, 70, 392, 560, 2 if roof != "thatch" else 1, 0.25 if roof != "thatch" else 0.32, kind, seed=k + 3,
                       lit=lit, roof=roof, shop=(k == 1))
        add(f"{roof} roof ({kind})", 340, 420, fn, g)

    def row(cr):
        P = palette("rain_night")
        core.vgrad(cr, 0, 0, 800, 420, [P["sky"][1], P["sky"][-1]])
        draw_roofline(cr, -20, 820, 200, 0.08, "rain_night", seed=4, haze=0.35)
        rigs = draw_street_row(cr, -20, 820, 360, 0.15, "rain_night", seed=11, lit=0.55)
        draw_cobbles(cr, 0, 360, 800, 420, "rain_night", seed=5, wet=True, size=(4.0, 14.0))
        cr.save()
        cr.rectangle(0, 360, 800, 60)
        cr.clip()
        draw_wet_reflections(cr, [(p_[0], p_[1], c, lv * 0.5, 362) for r in rigs for (p_, c, lv, ww) in r.lights], stretch=0.6, width=0.5)
        cr.restore()
    add("street row + far roofline, rainy night (draw_street_row)", 800, 420, row, g)

    # ---- stone ----------------------------------------------------------------------------
    g = "stone: coursed walls, arches, the vaulted wash-house (S1)"
    add("stone wall (washhouse)", 300, 260, lambda cr: draw_stone_wall(cr, 0, 0, 300, 260, "washhouse", seed=2), g)
    add("stone wall (evening)", 300, 260, lambda cr: draw_stone_wall(cr, 0, 0, 300, 260, "evening", seed=3, block=(70, 40)), g)

    def arch(cr):
        draw_stone_wall(cr, 0, 0, 300, 260, "washhouse", seed=4)
        draw_arch(cr, 150, 240, 120, 200, "washhouse", fill=lambda c: core.vgrad(c, 0, 0, 300, 260, ["#16304a", "#0a1626"]))
    add("arch with a night window", 300, 260, arch, g)
    add("vaulted hall (draw_vaulted_hall)", 600, 338, panel(lambda cr: draw_vaulted_hall(cr, 0, 0, 1920, 1080, "washhouse", floor_y=720)), g)

    # ---- ground ---------------------------------------------------------------------------
    g = "ground: cobbles dry and wet, reflections, puddles, gravel and grass"
    add("cobbles, dry, converging (vp)", 600, 300, lambda cr: draw_cobbles(cr, 0, 0, 600, 300, "evening", seed=1, vp=(300, -400)), g)

    def wet(cr):
        draw_cobbles(cr, 0, 0, 600, 300, "rain_night", seed=2, wet=True, size=(6.0, 30.0))
        lights = [(160, -260, "#ffc56b", 1.0, 10), (430, -200, "#ffc56b", 0.7, 10)]
        draw_wet_reflections(cr, lights, stretch=0.8)
        draw_puddle(cr, 360, 222, 130, 32, "rain_night", seed=1, lights=lights, stretch=0.8)
        puddle_ripples(cr, 1.3, 360, 222, 130, 32, n=6, seed=1)
    add("wet cobbles: lamp reflections, a puddle with ripples", 600, 300, wet, g)

    def garden_ground(cr):
        draw_grass(cr, 0, 0, 600, 300, "dusk", seed=3)
        draw_gravel_path(cr, [(330, -10), (300, 120), (250, 320)], (40.0, 200.0), "dusk", seed=4)
    add("grass + gravel path (dusk)", 600, 300, garden_ground, g)

    # ---- the garden ------------------------------------------------------------------------
    g = "the garden: the old oak (OakTree sways), hedges, flower beds"

    def oak(cr):
        core.vgrad(cr, 0, 0, 420, 420, palette("dusk")["sky"][1:])
        draw_oak(cr, 210, 400, 0.38, "dusk")
    add("the old oak (dusk)", 420, 420, oak, g)

    def oak_g(cr):
        core.vgrad(cr, 0, 0, 420, 420, palette("golden")["sky"][1:])
        draw_oak(cr, 210, 400, 0.38, "golden", seed=3)
    add("the old oak (golden hour)", 420, 420, oak_g, g)

    def hedges(cr):
        core.vgrad(cr, 0, 0, 560, 420, palette("dusk")["sky"][1:])
        draw_grass(cr, 0, 260, 560, 160, "dusk", seed=5)
        draw_hedge(cr, 30, 300, 500, 110, "dusk", seed=6)
        draw_flower_bed(cr, 60, 400, 440, 70, "dusk", seed=7)
    add("box hedge + flower bed with wattle edging", 560, 420, hedges, g)

    # ---- weather ----------------------------------------------------------------------------
    g = "weather and atmosphere: rain (3 depths, lit drops), mist, haze"

    def rain(cr):
        P = palette("rain_night")
        core.vgrad(cr, 0, 0, 600, 338, [P["sky"][0], P["sky"][-1]])
        draw_haze(cr, 0, 150, 600, 188, P["haze"], 0.0, 0.5)
        fx.glow(cr, 400, 120, 120, "#ffb860", 0.5)
        Rain((0, 0, 600, 338), "rain_night", 0.5, ground=(300, 338)).draw(cr, 1.0, lights=[(400, 120, 110, "#ffb860")])
    add("Rain: drops light up inside a lamp's glow", 600, 338, rain, g)

    def mist(cr):
        P = palette("dusk")
        core.vgrad(cr, 0, 0, 600, 338, P["sky"][1:])
        draw_hills(cr, 0, 600, 250, "dusk", layers=3, height=(40.0, 110.0), seed=3)
        for k in range(2):
            draw_mist(cr, 0, 180 + k * 70, 600, 80, P["haze"], 0.4, seed=k, scale=0.8)
    add("Mist bands between the hills", 600, 338, mist, g)
    return items
