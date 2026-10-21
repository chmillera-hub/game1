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
                  stone="#3a4458", plaster=("#5a6276", "#66604e", "#5c5a6a"), timber="#1e1a1c", roof="#232838",
                  window="#ffc56b", window_dark="#141b2a", star=True, moon=True),
    "rain_night": dict(sky=["#090e1c", "#111a32", "#1c2844", "#2c3b58"], cloud=("#151e36", "#2a3858"), haze="#2c3b5c",
                       far="#151d33", mid="#121a2d", near="#0d1424", ground="#141c2c",
                       foliage=("#0c1a1e", "#16302e", "#24443c"), stone="#3c465a",
                       plaster=("#59617a", "#686252", "#5e5b6d"), timber="#1d191c", roof="#20263a",
                       window="#ffbf5f", window_dark="#131a28", star=False, moon=False),
    # S6 dusk garden: violet above, peach at the horizon, the first warmth
    "dusk": dict(sky=["#3e3768", "#6c5a8e", "#b582a2", "#f0b496", "#f8d3a8"], cloud=("#8a6a96", "#f6c6a0"),
                 haze="#c99aa8", far="#8c7a9e", mid="#6c6688", near="#4a4a68", ground="#5a5470",
                 foliage=("#2e3a4a", "#4a5a5a", "#7a8466"), stone="#8a7c8c", plaster=("#d8c4b8", "#e0c8a8", "#c8b8c4"),
                 timber="#4a3438", roof="#6a4a5a", window="#ffd08a", window_dark="#4a3c58", star=False, moon=False),
    # S7 golden hour
    "golden": dict(sky=["#5e7aa8", "#9aa0b4", "#e2b07a", "#f8cf8a", "#fde3a8"], cloud=("#b88a7a", "#ffe0a8"),
                   haze="#e8c08a", far="#a8907a", mid="#8a7a5e", near="#5e5a40", ground="#7a6a48",
                   foliage=("#3a4a2a", "#5e6e34", "#9aa04a"), stone="#a89478", plaster=("#ecd8b0", "#f0d0a0", "#e0c8b0"),
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
                     window_alpha=None, banners=True, t=0.0, hill=True, hill_w=1100.0, hill_h=170.0, road=True):
    """The castle on the hill, as a distant storybook silhouette: curtain walls, round towers
    with conical roofs and pennants, a tall keep with a spire, a gatehouse, a winding road, a
    few lit windows; a soft rim of light on the sky's bright side.

    Anchor (x, y) = the castle's foot on the hilltop; the castle is ~330 x 280 at scale 1.0 and
    the hill spreads hill_w wide and hill_h down below it. Colours from the palette's "far"
    (silhouette) and "haze" (rim); window_color/alpha default by palette (lit at night). Static
    (banners are drawn at time t): put it in a blurred far Layer."""
    P = palette(kind)
    col = color or P["far"]
    rimc = rim or core.mix(P["haze"], P["sky"][-1], 0.5)
    wc = window_color or P["window"]
    wa = window_alpha if window_alpha is not None else (0.95 if kind in ("night", "rain_night", "blue_hour", "evening") else 0.5)
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
            pts = [(-hill_w / 2, hill_h)]
            for i in range(25):
                u = i / 24
                xx = -hill_w / 2 + u * hill_w
                hgt = hill_h * (1.0 - (abs(u - 0.5) * 2) ** 1.6) - 6.0 * core.noise1(xx * 0.02, seed + 3)
                pts.append((xx, hill_h - hgt + 8.0))
            pts.append((hill_w / 2, hill_h))
            core.smooth_open(cr, pts)
            cr.line_to(hill_w / 2, hill_h + 400.0)
            cr.line_to(-hill_w / 2, hill_h + 400.0)
            cr.close_path()
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
    silhouette(-2.0, -1.5)
    core.src(cr, rimc, 0.8)
    cr.fill()
    silhouette()
    core.src(cr, col)
    cr.fill()
    cr.save()
    silhouette()
    cr.clip()
    texture(cr, "stone", 0.12, 0.6)
    # a darker band where the castle meets the hill (it sits in its own shadow)
    cr.rectangle(-170.0, -10.0, 340.0, 20.0)
    core.src(cr, core.shade(col, 0.25), 0.5)
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
