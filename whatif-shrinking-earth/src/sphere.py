"""Numpy orthographic sphere renderer + procedural planet textures.

Textures are equirectangular (H x W), cached to paths.CACHE. render_* return
straight-alpha RGBA uint8 sprites centred on the sphere, plus the integer
offset (sprite pixel (0,0) relative to the sphere centre).
"""
import math
import os

import numpy as np
import skia

import paths

TW, TH = 2048, 1024
LIGHT = np.array([-0.55, -0.32, 0.77], np.float32)
LIGHT /= np.linalg.norm(LIGHT)

_TEX = {}


# ----------------------------------------------------------------------------
# noise
# ----------------------------------------------------------------------------

def _hash3(ix, iy, iz, seed):
    h = (ix.astype(np.uint64) * np.uint64(73856093)) ^ (iy.astype(np.uint64) * np.uint64(19349663)) \
        ^ (iz.astype(np.uint64) * np.uint64(83492791)) ^ np.uint64((seed * 2654435761) & 0xFFFFFFFF)
    h = (h ^ (h >> np.uint64(13))) * np.uint64(1274126177)
    h = h ^ (h >> np.uint64(16))
    return (h & np.uint64(0xFFFFFF)).astype(np.float32) / np.float32(0x1000000)


def vnoise3(x, y, z, seed=0):
    xi, yi, zi = np.floor(x), np.floor(y), np.floor(z)
    xf, yf, zf = x - xi, y - yi, z - zi
    xi, yi, zi = xi.astype(np.int64), yi.astype(np.int64), zi.astype(np.int64)
    u = xf * xf * (3 - 2 * xf)
    v = yf * yf * (3 - 2 * yf)
    w = zf * zf * (3 - 2 * zf)
    out = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                h = _hash3(xi + dx, yi + dy, zi + dz, seed)
                wx = u if dx else (1 - u)
                wy = v if dy else (1 - v)
                wz = w if dz else (1 - w)
                out = out + h * wx * wy * wz
    return out


def fbm3(x, y, z, seed=0, octaves=5, lac=2.0, gain=0.5):
    amp, freq, tot, norm = 1.0, 1.0, 0.0, 0.0
    for o in range(octaves):
        tot = tot + amp * vnoise3(x * freq, y * freq, z * freq, seed + o * 17)
        norm += amp
        amp *= gain
        freq *= lac
    return tot / norm


def _sphere_grid(w=TW, h=TH):
    lon = (np.arange(w, dtype=np.float32) + 0.5) / w * 2 * np.pi - np.pi
    lat = np.pi / 2 - (np.arange(h, dtype=np.float32) + 0.5) / h * np.pi
    LON, LAT = np.meshgrid(lon, lat)
    X = np.cos(LAT) * np.sin(LON)
    Y = np.sin(LAT)
    Z = np.cos(LAT) * np.cos(LON)
    return LON, LAT, X, Y, Z


def _smooth(a, sigma):
    from scipy.ndimage import gaussian_filter
    return gaussian_filter(a, sigma, mode=("nearest", "wrap"))


# ----------------------------------------------------------------------------
# textures
# ----------------------------------------------------------------------------

def _land_mask():
    import warnings
    from PIL import Image, ImageDraw
    import geopandas
    warnings.filterwarnings("ignore")
    world = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
    S = 4
    W, H = TW * S, TH * S
    img = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(img)
    for geom in world.geometry:
        polys = list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom]
        for p in polys:
            xs, ys = p.exterior.coords.xy
            pts = [((lo + 180) / 360 * W, (90 - la) / 180 * H) for lo, la in zip(xs, ys)]
            d.polygon(pts, fill=255)
    img = img.resize((TW, TH), Image.LANCZOS)
    return np.asarray(img, np.float32) / 255.0


def earth_textures():
    if "earth" in _TEX:
        return _TEX["earth"]
    fn = os.path.join(paths.CACHE, "earth_tex_v4.npz")
    if os.path.exists(fn):
        z = np.load(fn)
        _TEX["earth"] = {k: z[k] for k in z.files}
        return _TEX["earth"]
    land = _land_mask()
    LON, LAT, X, Y, Z = _sphere_grid()
    latd = np.degrees(LAT)
    n1 = fbm3(X * 3, Y * 3, Z * 3, 11, 5)
    n2 = fbm3(X * 7 + 3, Y * 7, Z * 7, 23, 4)
    # land colours by climate band
    alat = np.abs(latd)
    rain = np.array([0.20, 0.47, 0.20], np.float32)
    desert = np.array([0.80, 0.66, 0.42], np.float32)
    temperate = np.array([0.36, 0.52, 0.24], np.float32)
    boreal = np.array([0.24, 0.38, 0.22], np.float32)
    tundra = np.array([0.55, 0.55, 0.45], np.float32)
    ice = np.array([0.94, 0.96, 0.99], np.float32)
    def band(c, a):
        return np.clip(a, 0, 1)[..., None] * c
    w_rain = np.clip(1 - np.abs(alat - 4) / 12, 0, 1)
    w_des = np.clip(1 - np.abs(alat - 24) / 11, 0, 1) * np.clip((n1 - 0.38) * 3.0, 0, 1)
    w_temp = np.clip(1 - np.abs(alat - 44) / 14, 0, 1)
    w_bor = np.clip(1 - np.abs(alat - 60) / 9, 0, 1)
    w_tun = np.clip((alat - 64) / 6, 0, 1)
    wsum = w_rain + w_des + w_temp + w_bor + w_tun + 1e-3
    landc = (band(rain, w_rain) + band(desert, w_des) + band(temperate, w_temp) + band(boreal, w_bor)
             + band(tundra, w_tun)) / wsum[..., None]
    fill_mask = (w_rain + w_des + w_temp + w_bor + w_tun) < 0.2
    landc[fill_mask] = temperate
    landc *= (0.85 + 0.3 * n2)[..., None]
    # ice: Antarctica, Greenland, high Arctic
    lond = np.degrees(LON)
    green = (latd > 59) & (lond > -75) & (lond < -10)
    ice_w = np.clip((-latd - 62) / 4, 0, 1) + green.astype(np.float32) * np.clip((latd - 59) / 3, 0, 1)
    ice_w = np.clip(ice_w + np.clip((alat - 72) / 5, 0, 1), 0, 1)
    landc = landc * (1 - ice_w[..., None]) + ice * ice_w[..., None]
    shallow = np.clip(_smooth(land, 6.0) * 2.4, 0, 1)
    deep = np.array([0.07, 0.22, 0.48], np.float32)
    shal = np.array([0.15, 0.47, 0.66], np.float32)
    ocean = deep * (1 - shallow[..., None]) + shal * shallow[..., None]
    ocean *= (0.92 + 0.12 * n1)[..., None]
    seaice = np.clip((alat - 74) / 6, 0, 1)
    ocean = ocean * (1 - seaice[..., None]) + np.array([0.85, 0.9, 0.95], np.float32) * seaice[..., None]
    color = ocean * (1 - land[..., None]) + landc * land[..., None]
    # clouds: warped fbm
    wx = fbm3(X * 2 + 5, Y * 2, Z * 2, 31, 3)
    cl = fbm3(X * 4 + wx * 2.2, Y * 6 + wx * 1.5, Z * 4, 41, 6)
    clouds = _smooth(np.clip((cl - 0.47) * 3.2, 0, 1), 1.2).astype(np.float32)
    # lava cracks: ridged noise
    r1 = 1 - np.abs(2 * fbm3(X * 5, Y * 5, Z * 5, 51, 4) - 1)
    r2 = 1 - np.abs(2 * fbm3(X * 11 + 7, Y * 11, Z * 11, 61, 3) - 1)
    cracks = np.clip(np.clip((r1 - 0.80) / 0.20, 0, 1) ** 1.8 * 1.25 + np.clip((r2 - 0.86) / 0.14, 0, 1) ** 2 * 0.7,
                     0, 1).astype(np.float32)
    mott = fbm3(X * 9, Y * 9, Z * 9, 71, 4).astype(np.float32)
    tex = dict(color=color.astype(np.float32), land=land.astype(np.float32), clouds=clouds,
               cracks=cracks, mott=mott)
    np.savez_compressed(fn, **tex)
    _TEX["earth"] = tex
    return tex


def moon_texture():
    if "moon" in _TEX:
        return _TEX["moon"]
    fn = os.path.join(paths.CACHE, "moon_tex_v3.npy")
    if os.path.exists(fn):
        _TEX["moon"] = np.load(fn)
        return _TEX["moon"]
    LON, LAT, X, Y, Z = _sphere_grid()
    n = fbm3(X * 3, Y * 3, Z * 3, 5, 5)
    base = 0.66 + 0.10 * (fbm3(X * 12, Y * 12, Z * 12, 9, 4) - 0.5)
    maria = np.clip((n - 0.52) * 6, 0, 1)
    g = base * (1 - 0.32 * maria)
    rng = np.random.default_rng(3)
    P = np.stack([X, Y, Z], -1)
    for k in range(70):
        v = rng.normal(size=3)
        v /= np.linalg.norm(v)
        rad = rng.uniform(0.03, 0.16) if k < 20 else rng.uniform(0.015, 0.05)
        ang = np.arccos(np.clip(P @ v.astype(np.float32), -1, 1))
        rr = ang / rad
        g = g - 0.10 * np.clip(1 - rr, 0, 1) ** 0.5 * (rr < 1) + 0.09 * np.exp(-((rr - 1.0) / 0.12) ** 2)
    tex = np.clip(np.stack([g * 1.0, g * 0.99, g * 0.95], -1), 0, 1).astype(np.float32)
    np.save(fn, tex)
    _TEX["moon"] = tex
    return tex


def mars_texture():
    if "mars" in _TEX:
        return _TEX["mars"]
    fn = os.path.join(paths.CACHE, "mars_tex_v2.npy")
    if os.path.exists(fn):
        _TEX["mars"] = np.load(fn)
        return _TEX["mars"]
    LON, LAT, X, Y, Z = _sphere_grid()
    n = fbm3(X * 3, Y * 3, Z * 3, 101, 5)
    n2 = fbm3(X * 10, Y * 10, Z * 10, 103, 4)
    base = np.array([0.80, 0.37, 0.18], np.float32)
    dark = np.array([0.45, 0.20, 0.12], np.float32)
    w = np.clip((n - 0.5) * 4, 0, 1)
    col = base * (1 - w[..., None]) + dark * w[..., None]
    col *= (0.88 + 0.24 * n2)[..., None]
    cap = np.clip((np.abs(np.degrees(LAT)) - 76) / 4, 0, 1)
    col = col * (1 - cap[..., None]) + np.array([0.95, 0.93, 0.9], np.float32) * cap[..., None]
    col = col.astype(np.float32)
    np.save(fn, col)
    _TEX["mars"] = col
    return col


# ----------------------------------------------------------------------------
# geometry + shading
# ----------------------------------------------------------------------------

class Geom:
    def __init__(self, r, tilt=0.35, spin=0.0, pad=2):
        self.r = r
        N = int(math.ceil(2 * r)) + 2 * pad
        self.N = N
        c = N / 2.0
        idx = np.arange(N, dtype=np.float32) + 0.5
        x = (idx[None, :] - c) / r
        y = (idx[:, None] - c) / r
        d2 = x * x + y * y
        d = np.sqrt(d2)
        self.alpha = np.clip((1 - d) * r + 0.5, 0, 1).astype(np.float32)
        z = np.sqrt(np.clip(1 - d2, 0, 1))
        k = 1.0 / np.maximum(d, 1.0)  # keep edge pixels on the sphere
        x, y = x * k, y * k
        self.x, self.y, self.z = x.astype(np.float32), np.broadcast_to(y, x.shape).astype(np.float32), z.astype(np.float32)
        ct, st = math.cos(tilt), math.sin(tilt)
        # planet axes in view space: pole P=(0,-ct,st), front F=(0,st,ct), east E=(1,0,0)
        npole = -self.y * ct + self.z * st
        nfront = self.y * st + self.z * ct
        self.lat = np.arcsin(np.clip(npole, -1, 1))
        self.lon0 = np.arctan2(self.x, nfront)
        self.spin = spin
        self.off = -c  # sprite origin relative to centre
        self.ndl = (self.x * LIGHT[0] + self.y * LIGHT[1] + self.z * LIGHT[2]).astype(np.float32)

    def uv(self, extra_spin=0.0):
        lon = self.lon0 - self.spin - extra_spin
        u = ((lon / (2 * np.pi) + 0.5) % 1.0) * TW
        v = (0.5 - self.lat / np.pi) * TH
        ui = np.clip(u.astype(np.int32), 0, TW - 1)
        vi = np.clip(v.astype(np.int32), 0, TH - 1)
        return vi, ui


def _sstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def _to_rgba(col, alpha):
    out = np.empty(alpha.shape + (4,), np.uint8)
    out[..., :3] = np.clip(col * 255, 0, 255).astype(np.uint8)
    out[..., 3] = np.clip(alpha * 255, 0, 255).astype(np.uint8)
    return out


def render_earth(r, spin=0.0, tilt=0.35, steam=0.0, molten=0.0, glow=0.0, white=0.0, cloud_spin=0.0,
                 blur_spin=0.0, night=0.07):
    """Earth through all of its 'squeezed' states. Returns RGBA uint8 sprite and offset."""
    tex = earth_textures()
    g = Geom(r, tilt, spin)
    vi, ui = g.uv()
    if blur_spin > 0:
        acc = None
        for k in range(5):
            vi2, ui2 = g.uv(blur_spin * (k - 2) / 4)
            s = tex["cracks"][vi2, ui2]
            acc = s if acc is None else acc + s
        cracks = acc / 5
    else:
        cracks = tex["cracks"][vi, ui]
    base = tex["color"][vi, ui]
    land = tex["land"][vi, ui]
    day = _sstep(-0.16, 0.32, g.ndl)
    lit = night + (1.0 - night) * day
    col = base * lit[..., None]
    z = g.z
    # ocean glint
    if molten < 0.5 and white < 0.5:
        hv = LIGHT + np.array([0, 0, 1], np.float32)
        hv /= np.linalg.norm(hv)
        nh = np.clip(g.x * hv[0] + g.y * hv[1] + g.z * hv[2], 0, 1)
        col += ((nh ** 60) * 0.55 * (1 - land) * (1 - steam) * (1 - molten))[..., None]
    # clouds
    cv, cu = g.uv(cloud_spin)
    cl = tex["clouds"][cv, cu]
    ca = np.clip(cl * (1 + 2.2 * steam) + steam * 0.35, 0, 1) * (1 - molten) * 0.92
    cloud_col = (0.06 + 0.98 * day)[..., None] * np.array([1.0, 1.0, 1.0], np.float32)
    col = col * (1 - ca[..., None]) + cloud_col * ca[..., None]
    if steam > 0:
        haze = np.array([0.86, 0.89, 0.93], np.float32) * (0.10 + 0.9 * day)[..., None]
        col = col * (1 - 0.45 * steam) + haze * 0.45 * steam
    # atmosphere rim
    rim = (1 - z) ** 2.4
    atm = np.array([0.45, 0.70, 1.0], np.float32) * (1 - 0.6 * molten)
    col += atm * (rim * (0.15 + 0.85 * day) * (0.55 + 0.6 * steam))[..., None] * (1 - glow)
    # molten crust + glowing cracks
    if molten > 0 or glow > 0:
        crust = np.array([0.12, 0.08, 0.07], np.float32) * (0.4 + 0.6 * lit)[..., None]
        m = max(molten, glow)
        col = col * (1 - m) + crust * m
        mott = tex["mott"][vi, ui]
        hotc = np.array([1.0, 0.45, 0.10], np.float32)
        deep = np.array([0.55, 0.08, 0.02], np.float32)
        emis = ((cracks ** 2.0) * 1.9)[..., None] * hotc * molten + (cracks * 0.35)[..., None] * deep * molten
        if glow > 0:
            warm = np.array([1.0, 0.55, 0.16], np.float32) * (0.55 + 0.6 * mott)[..., None]
            whiteh = np.array([1.0, 0.92, 0.78], np.float32)
            body = warm * (1 - glow * 0.0) + (whiteh - warm) * (cracks[..., None] * 0.9)
            limb = (0.55 + 0.45 * z ** 0.6)[..., None]
            emis = emis * (1 - glow) + body * limb * glow
            col = col * (1 - glow)
        col = col + emis
    if white > 0:
        mott = tex["mott"][vi, ui]
        wcol = np.array([0.86, 0.93, 1.0], np.float32) * (0.80 + 0.2 * z ** 0.5)[..., None]
        wcol = wcol + (cracks * 0.12)[..., None] - ((mott - 0.5) * 0.08)[..., None]
        col = col * (1 - white) + wcol * white
    return _to_rgba(col, g.alpha), g.off


def render_textured(r, tex, spin=0.0, tilt=0.2, night=0.05, rim_col=None, rim_k=0.0):
    g = Geom(r, tilt, spin)
    vi, ui = g.uv()
    base = tex[vi, ui]
    day = _sstep(-0.12, 0.28, g.ndl)
    col = base * (night + (1 - night) * day)[..., None]
    if rim_col is not None and rim_k > 0:
        rim = (1 - g.z) ** 2.5
        col += np.array(rim_col, np.float32) * (rim * day * rim_k)[..., None]
    return _to_rgba(col, g.alpha), g.off


def sprite_image(rgba):
    return skia.Image.fromarray(rgba, colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType)


def draw_sprite(c, rgba_off, cx, cy, sx=1.0, sy=1.0, alpha=1.0, rot=0.0):
    rgba, off = rgba_off
    img = sprite_image(rgba)
    c.save()
    c.translate(cx, cy)
    if rot:
        c.rotate(rot)
    c.scale(sx, sy)
    p = skia.Paint(AntiAlias=True)
    if alpha < 0.999:
        p.setAlphaf(max(0.0, alpha))
    c.drawImage(img, off, off, skia.SamplingOptions(skia.FilterMode.kLinear), p)
    c.restore()
