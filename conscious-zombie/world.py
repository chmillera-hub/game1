"""Environment: camera, skies, ground, fortress, horde, dust, beams, building, helicopter, cabin."""
import math
import numpy as np
import cairo
from common import (W, H, clamp, lerp, ease, mix, mul, hexc, rgba, smooth_closed, smooth_open, capsule,
                    ellipse, soft_dot, shade, soft_stroke, hsh, sn, tint)
import rig

WALL = 260.0      # fortress wall depth (m)
ZC = 120.0        # where the soul lands
BLD = (17.0, 134.0)  # building (X, front-face Z)
FIG_H = 743.0     # rig units crown->sole


# ---------------------------------------------------------------- textures
_KEEP = []


def _tex(arr):
    h, w, _ = arr.shape
    a = np.zeros((h, w, 4), np.uint8)
    a[..., 0] = arr[..., 2]
    a[..., 1] = arr[..., 1]
    a[..., 2] = arr[..., 0]
    a[..., 3] = 255
    surf = cairo.ImageSurface.create_for_data(memoryview(a).cast("B"), cairo.FORMAT_RGB24, w, h)
    _KEEP.append(a)
    return surf


def _noise(h, w, seed, oct=4):
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w))
    for o in range(oct):
        n = 2 ** (o + 2)
        g = rng.random((n + 1, n + 1))
        yy = np.linspace(0, n, h, endpoint=False)
        xx = np.linspace(0, n, w, endpoint=False)
        y0, x0 = yy.astype(int), xx.astype(int)
        fy, fx = (yy - y0)[:, None], (xx - x0)[None, :]
        fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
        a = g[y0][:, x0]; b = g[y0][:, x0 + 1]; c = g[y0 + 1][:, x0]; d = g[y0 + 1][:, x0 + 1]
        out += ((a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy) / (2 ** o)
    out -= out.min()
    return out / out.max()


def make_stone(seed=3):
    """Irregular, chipped, grime-streaked fortress stone (tileable)."""
    h = w = 256
    rng = np.random.default_rng(seed)
    n = _noise(h, w, seed)
    grit = rng.random((h, w))
    img = np.zeros((h, w, 3))
    filled = np.zeros((h, w), bool)
    y = 0
    for hh in (28, 34, 30, 36, 32, 30, 34, 32):
        x = 0
        while x < w:
            bw = int(rng.integers(34, 80))
            col = np.array([102, 98, 104], float) * (0.68 + 0.42 * rng.random()) * (0.92 + 0.12 * rng.random(3))
            x0, x1 = x + 2, min(w, x + bw - 1)
            if x1 > x0:
                img[y + 2:y + hh - 1, x0:x1] = col
                filled[y + 2:y + hh - 1, x0:x1] = True
                img[y + 2:y + 4, x0:x1] *= 1.18          # worn top edge catches light
                img[y + hh - 4:y + hh - 1, x0:x1] *= 0.72  # underside
                for _ in range(int(rng.integers(0, 3))):   # chipped corners
                    cx = x0 if rng.random() < 0.5 else x1 - 1
                    cy = y + 2 if rng.random() < 0.5 else y + hh - 2
                    r = int(rng.integers(3, 8))
                    yy, xx = np.ogrid[:h, :w]
                    m = ((yy - cy) ** 2 + (xx - cx) ** 2) < r * r
                    img[m] = 0
                    filled[m] = False
            x += bw
        y += hh
    img[~filled] = np.array([34, 30, 34], float)          # deep, dirty mortar
    img *= (0.7 + 0.45 * n[..., None]) * (0.86 + 0.18 * grit[..., None])
    img[grit < 0.035] *= 0.55                               # pitting
    # grime streaks running down from the courses
    for _ in range(60):
        x0 = int(rng.integers(0, w)); y0 = int(rng.integers(0, h)); L = int(rng.integers(20, 110)); wd = int(rng.integers(2, 7))
        for k in range(L):
            yy = (y0 + k) % h
            img[yy, x0:x0 + wd] *= 1 - 0.38 * (1 - k / L)
    # mossy damp patches
    moss = _noise(h, w, seed + 9, 3)
    m = moss > 0.62
    img[m] = img[m] * 0.8 + np.array([44, 58, 30]) * 0.2
    # cracks
    for _ in range(14):
        cx, cy = float(rng.integers(0, w)), float(rng.integers(0, h))
        ang = rng.random() * 6.28
        for k in range(int(rng.integers(12, 40))):
            ang += (rng.random() - 0.5) * 0.9
            cx = (cx + np.cos(ang) * 1.5) % w; cy = (cy + np.sin(ang) * 1.5) % h
            img[int(cy), int(cx)] *= 0.35
    stain = _noise(h, w, seed + 7, 3)
    img *= (0.72 + 0.4 * stain[..., None])
    return _tex(np.clip(img, 0, 255).astype(np.uint8))


TILE_M = 10.0  # dirt texture tile size in metres


def make_dirt(seed=11):
    """Ground albedo: dusty earth, darker damp patches, pebbles, cracks, dead grass. Returns float mips."""
    h = w = 512
    rng = np.random.default_rng(seed)
    n1 = _noise(h, w, seed, 5)
    n2 = _noise(h, w, seed + 1, 3)
    img = np.ones((h, w, 3)) * np.array([104, 88, 72], float)
    img *= (0.78 + 0.4 * n1[..., None])
    img = img * (1 - 0.25 * (n2[..., None] > 0.6)) + np.array([128, 112, 92]) * 0.12 * (n2[..., None] < 0.3)
    yy, xx = np.ogrid[:h, :w]
    for _ in range(420):  # pebbles: lit top, dark lower edge
        cx, cy = int(rng.integers(0, w)), int(rng.integers(0, h)); r = rng.integers(2, 6)
        m = ((yy - cy) ** 2 + (xx - cx) ** 2 * 0.8) < r * r
        tone = 0.75 + 0.5 * rng.random()
        img[m] = img[m] * 0.3 + np.array([120, 112, 104]) * tone * 0.7
        m2 = ((yy - cy - r * 0.6) ** 2 + (xx - cx) ** 2) < (r * 0.8) ** 2
        img[m2 & ~m] *= 0.7
    for _ in range(40):  # dry cracks
        cx, cy = float(rng.integers(0, w)), float(rng.integers(0, h)); ang = rng.random() * 6.28
        for k in range(int(rng.integers(10, 50))):
            ang += (rng.random() - 0.5) * 1.1
            cx = (cx + np.cos(ang)) % w; cy = (cy + np.sin(ang)) % h
            img[int(cy), int(cx)] *= 0.55
    for _ in range(160):  # dead grass blades lying flat
        cx, cy = float(rng.integers(0, w)), float(rng.integers(0, h)); ang = rng.random() * 6.28
        col = np.array([140, 126, 80]) * (0.7 + 0.4 * rng.random())
        for k in range(int(rng.integers(6, 16))):
            img[int(cy) % h, int(cx) % w] = img[int(cy) % h, int(cx) % w] * 0.4 + col * 0.6
            cx += np.cos(ang); cy += np.sin(ang)
    img = np.clip(img, 0, 255).astype(np.float32) / 255.0
    mips = [img]
    while mips[-1].shape[0] > 8:
        m = mips[-1]
        mips.append(((m[0::2, 0::2] + m[1::2, 0::2] + m[0::2, 1::2] + m[1::2, 1::2]) / 4).astype(np.float32))
    return mips


_DIRT = None
_MACRO = None


def dirt():
    global _DIRT, _MACRO
    if _DIRT is None:
        _DIRT = make_dirt()
        _MACRO = (0.8 + 0.4 * _noise(64, 64, 77, 3)).astype(np.float32)
    return _DIRT, _MACRO


def make_brick(seed=5):
    h = w = 256
    rng = np.random.default_rng(seed)
    n = _noise(h, w, seed)
    grit = rng.random((h, w))
    img = np.zeros((h, w, 3))
    mortar = np.array([120, 110, 100], float)
    img[:] = mortar
    bh, bw = 16, 48
    for r in range(h // bh):
        off = (r % 2) * (bw // 2)
        for c in range(-1, w // bw + 1):
            x0 = c * bw + off
            col = np.array([132, 70, 52], float) * (0.75 + 0.45 * rng.random())
            col = col * (0.9 + 0.2 * rng.random(3))
            ys, ye = r * bh + 2, r * bh + bh - 1
            xs, xe = max(0, x0 + 2), min(w, x0 + bw - 1)
            if xe > xs:
                img[ys:ye, xs:xe] = col
    img *= (0.7 + 0.5 * n[..., None]) * (0.85 + 0.2 * grit[..., None])
    soot = _noise(h, w, seed + 3, 3)
    img *= (0.75 + 0.3 * soot[..., None])
    return _tex(np.clip(img, 0, 255).astype(np.uint8))


_TEX = {}


def tex(name):
    if name not in _TEX:
        if name == "stone":
            _TEX[name] = make_stone()
        elif name == "dirt":
            _TEX[name] = _tex((dirt()[0][1] * 255).astype(np.uint8))
        else:
            _TEX[name] = make_brick()
    return _TEX[name]


def pattern(name, scale, ox=0, oy=0):
    p = cairo.SurfacePattern(tex(name))
    p.set_extend(cairo.EXTEND_REPEAT)
    p.set_filter(cairo.FILTER_GOOD)
    m = cairo.Matrix()
    m.scale(1 / max(1e-3, scale), 1 / max(1e-3, scale))
    m.translate(-ox, -oy)
    p.set_matrix(m)
    return p


# ---------------------------------------------------------------- camera
class Cam:
    def __init__(self, x=0.0, y=1.6, z=0.0, d=1, f=700.0, hy=640.0, roll=0.0):
        self.x, self.y, self.z, self.d, self.f, self.hy, self.roll = x, y, z, d, f, hy, roll

    def depth(self, Z):
        return (Z - self.z) * self.d

    def p(self, X, Y, Z):
        dp = max(0.05, self.depth(Z))
        return (W / 2 + (X - self.x) * self.d * self.f / dp, self.hy - (Y - self.y) * self.f / dp)

    def scale(self, Z, height=1.75):
        dp = max(0.05, self.depth(Z))
        return height * self.f / dp / FIG_H


# ---------------------------------------------------------------- sky
SKY = {
    # phase: (top, mid, horizon, glow)
    0.0: (hexc("1d1a3a"), hexc("6a3a5e"), hexc("f08a4a"), hexc("ffc070")),   # sunset
    1.0: (hexc("141530"), hexc("3a2a50"), hexc("b0584a"), hexc("e08a50")),   # late dusk
    2.0: (hexc("0a0c1e"), hexc("1a1a38"), hexc("4a3050"), hexc("8a4a40")),   # night (fires)
    3.0: (hexc("3a5a8a"), hexc("c08a8a"), hexc("ffc890"), hexc("fff0c0")),   # dawn
}


def sky_cols(phase):
    k0 = math.floor(clamp(phase, 0, 2.999))
    u = phase - k0
    a, b = SKY[float(k0)], SKY[float(k0 + 1)]
    return [mix(x, y, ease(u)) for x, y in zip(a, b)]


def draw_sky(ctx, cam, t, phase, east=False, stars=0.0, sun=True):
    top, mid, hor, glow = sky_cols(phase)
    if east:
        top, mid, hor = mul(top, 0.8), mix(mid, top, 0.5), mix(hor, mid, 0.65)
    hy = cam.hy
    g = cairo.LinearGradient(0, hy - 1100, 0, hy + 20)
    g.add_color_stop_rgb(0, *top)
    g.add_color_stop_rgb(0.55, *mid)
    g.add_color_stop_rgb(0.9, *mix(mid, hor, 0.7))
    g.add_color_stop_rgb(1, *hor)
    ctx.set_source(g)
    ctx.rectangle(0, 0, W, hy + 40)
    ctx.fill()
    if sun and not east and phase < 1.6:
        soft_dot(ctx, W / 2 + 90 - cam.x * 2, hy + 10, 420, glow, 0.55 * (1 - phase / 1.6))
        soft_dot(ctx, W / 2 + 90 - cam.x * 2, hy + 10, 120, (1, 0.95, 0.8), 0.45 * (1 - phase / 1.6))
    if phase >= 2.5 and not east:
        soft_dot(ctx, W / 2 - 60, hy + 10, 520, glow, 0.7)
        soft_dot(ctx, W / 2 - 60, hy + 10, 160, (1, 1, 0.9), 0.7)
    if stars > 0:
        for i in range(70):
            x = hsh(i, 1) * W
            y = hsh(i, 2) * (hy - 120)
            a = stars * (0.25 + 0.6 * hsh(i, 3)) * (0.75 + 0.25 * math.sin(t * (1 + hsh(i, 4) * 2) + i))
            soft_dot(ctx, x, y, 2.4 + hsh(i, 5) * 2, (1, 0.97, 0.9), a)
    # clouds: layered soft bands lit from below
    lit = mix(glow, hor, 0.4) if not east else mix(mid, hor, 0.5)
    for i in range(14):
        cx = ((hsh(i, 7) * 1.6 - 0.3) * W + t * (4 + hsh(i, 8) * 6) - cam.x * 3) % (W * 1.6) - W * 0.3
        cy = hy - 120 - hsh(i, 9) * (hy - 120) * 0.95
        rx = 140 + hsh(i, 10) * 220
        ry = 22 + hsh(i, 11) * 30
        dk = mix(top, mid, 0.5 + 0.5 * hsh(i, 12))
        ctx.save()
        ctx.translate(cx, cy)
        ctx.scale(rx / ry, 1)
        g = cairo.RadialGradient(0, 0, 0, 0, 0, ry)
        g.add_color_stop_rgba(0, *dk, 0.55)
        g.add_color_stop_rgba(1, *dk, 0)
        ctx.set_source(g)
        ctx.arc(0, 0, ry, 0, 2 * math.pi)
        ctx.fill()
        g = cairo.RadialGradient(0, ry * 0.45, 0, 0, ry * 0.45, ry * 0.8)
        g.add_color_stop_rgba(0, *lit, 0.35 * (1 - clamp((phase - 1.5) / 1.0) * 0.6))
        g.add_color_stop_rgba(1, *lit, 0)
        ctx.set_source(g)
        ctx.arc(0, ry * 0.45, ry * 0.8, 0, 2 * math.pi)
        ctx.fill()
        ctx.restore()


SLOPE0, SLOPE1, HILL = WALL - 48.0, WALL - 6.0, 16.0


def hgt(Z):
    """Ground height: flat plain, then the earthen hill the fortress stands on."""
    if Z <= SLOPE0:
        return 0.0
    u = clamp((Z - SLOPE0) / (SLOPE1 - SLOPE0))
    return HILL * u * u * (3 - 2 * u)


def ground_cols(phase, east):
    top, mid, hor, glow = sky_cols(phase)
    k = float(np.interp(phase, [0, 1, 2, 2.6, 3], [0.68, 0.56, 0.42, 0.6, 0.95]))
    if east:
        k *= 1.08
        fog = mix(mid, hexc("1e1c28"), 0.5)
        warm = mix(hexc("ffb080"), hexc("ffffff"), 0.5) if phase < 1.5 else mix(mid, hexc("ffffff"), 0.4)
    else:
        fog = mix(mix(hor, mid, 0.55), hexc("3a3036"), 0.35)
        warm = mix(glow, hexc("ffffff"), 0.4)
    return k, fog, warm, mid


def draw_ground(ctx, cam, t, phase, east=False):
    hy = cam.hy
    y0 = max(0, int(math.floor(hy)) + 1)
    k, fog, warm, mid = ground_cols(phase, east)
    if y0 < H:
        mips, macro = dirt()
        sub = 2  # half-res sampling, smooth upscale
        ys = np.arange(y0, H, sub, dtype=np.float32) + sub * 0.5
        xs = np.arange(0, W, sub, dtype=np.float32) + sub * 0.5 - W / 2
        dy = np.maximum(ys - hy, 0.25)
        dp = np.minimum(cam.f * max(cam.y, 0.2) / dy, 900.0)
        X = cam.x + cam.d * xs[None, :] * (dp[:, None] / cam.f)
        Z = cam.z + cam.d * dp[:, None] + np.zeros_like(X)
        fp = np.maximum(dp * dp / (cam.f * max(cam.y, 0.2)), dp / cam.f) * sub * (mips[0].shape[0] / TILE_M)
        lvl = np.clip(np.floor(np.log2(np.maximum(fp, 1e-6))), 0, len(mips) - 1).astype(int)
        out = np.empty((len(ys), len(xs), 3), np.float32)
        for Lv in np.unique(lvl):
            rows = np.where(lvl == Lv)[0]
            m = mips[Lv]
            nn = m.shape[0]
            u = np.floor(X[rows] / TILE_M * nn).astype(np.int64) % nn
            v = np.floor(Z[rows] / TILE_M * nn).astype(np.int64) % nn
            out[rows] = m[v, u]
        mu = np.floor(X / 150.0 * 64).astype(np.int64) % 64
        mv = np.floor(Z / 150.0 * 64).astype(np.int64) % 64
        out *= macro[mv, mu][..., None]
        out = out * k * np.array(mix(warm, mid, 0.35), np.float32)
        fg = (1 - np.exp(-dp / (140.0 if not east else 110.0)))[:, None, None]
        out = out * (1 - fg) + np.array(fog, np.float32) * fg
        img = np.clip(out * 255, 0, 255).astype(np.uint8)
        hh, ww = img.shape[:2]
        buf = np.zeros((hh, ww, 4), np.uint8)
        buf[..., 0], buf[..., 1], buf[..., 2], buf[..., 3] = img[..., 2], img[..., 1], img[..., 0], 255
        surf = cairo.ImageSurface.create_for_data(memoryview(buf).cast("B"), cairo.FORMAT_RGB24, ww, hh)
        ctx.save()
        ctx.rectangle(0, y0, W, H - y0)
        ctx.clip()
        ctx.translate(0, y0)
        ctx.scale(sub, sub)
        ctx.set_source_surface(surf, 0, 0)
        ctx.get_source().set_filter(cairo.FILTER_BILINEAR)
        ctx.get_source().set_extend(cairo.EXTEND_PAD)
        ctx.paint()
        ctx.restore()
        if not east:  # warm glare haze at the horizon (into the sun)
            g = cairo.LinearGradient(0, hy, 0, hy + 120)
            g.add_color_stop_rgba(0, *warm, 0.35 * (1 - clamp(phase - 1.6)))
            g.add_color_stop_rgba(1, *warm, 0)
            ctx.set_source(g); ctx.rectangle(0, hy, W, 120); ctx.fill()
    draw_features(ctx, cam, t, phase, east, k, fog, warm)


FEATS = []
for _i in range(360):
    _X = (hsh(_i, 21) - 0.5) * 130
    _Z = 3 + hsh(_i, 22) * (SLOPE0 - 6)
    if abs(_X) < 2.2 and abs(_Z - ZC) < 5:
        continue
    if abs(_X - BLD[0]) < 6 and BLD[1] - 2 < _Z < BLD[1] + 9:
        continue
    _kind = ("rock", "rock", "mound", "crater", "shrub", "stake", "pebbles", "rock")[int(hsh(_i, 25) * 8)]
    FEATS.append((_i, _X, _Z, _kind))


def _rock(ctx, x, y, r, i, base, rim, sh, line):
    pts = []
    n = 7
    for k in range(n):
        a = math.pi + k * math.pi / (n - 1)
        rr = r * (0.75 + 0.4 * hsh(i * 7 + k, 26))
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr * 0.7))
    pts += [(x + r * 0.9, y + r * 0.12), (x - r * 0.9, y + r * 0.12)]
    soft_dot(ctx, x + r * 0.3, y + r * 0.1, r * 1.3, (0, 0, 0), 0.35)
    ctx.new_path(); smooth_closed(ctx, pts, 0.6)
    rgba(ctx, base); ctx.fill_preserve()
    ctx.save(); ctx.clip_preserve()
    g = cairo.LinearGradient(x, y - r * 0.8, x, y + r * 0.2)
    g.add_color_stop_rgba(0, *rim, 0.55)
    g.add_color_stop_rgba(0.45, *rim, 0.0)
    g.add_color_stop_rgba(1, *sh, 0.45)
    ctx.set_source(g); ctx.paint()
    ctx.restore()
    rgba(ctx, line, 0.6); ctx.set_line_width(max(0.8, r * 0.06)); ctx.stroke()


def draw_features(ctx, cam, t, phase, east, k, fog, warm):
    """Rocks, dirt mounds, scorched craters, dead shrubs, broken stakes, pebble clusters."""
    vis = []
    for (i, X, Z, kind) in FEATS:
        dp = cam.depth(Z)
        if dp < 1.6 or dp > 190:
            continue
        x, y = cam.p(X, 0, Z)
        sz = cam.f / dp
        if x < -sz * 5 or x > W + sz * 5 or y > H + sz * 2 or y < cam.hy - 2:
            continue
        vis.append((dp, i, X, Z, kind, x, y, sz))
    vis.sort(key=lambda a: -a[0])
    for dp, i, X, Z, kind, x, y, sz in vis:
        fade = 1 - math.exp(-dp / 140)
        base = mix(mul(hexc("5a4c40"), k * 1.3), fog, fade)
        rim = mix(warm, fog, fade)
        sh = mix(hexc("140e14"), fog, fade)
        line = mix(hexc("1a1214"), fog, fade)
        if kind == "rock":
            r = (0.18 + hsh(i, 23) * 0.55) * sz
            if r > 1.2:
                _rock(ctx, x, y, r, i, base, rim, sh, line)
        elif kind == "pebbles":
            for q in range(5):
                px = x + (hsh(i * 5 + q, 27) - 0.5) * 0.9 * sz
                py = y + (hsh(i * 5 + q, 28) - 0.5) * 0.12 * sz
                r = (0.05 + hsh(i * 5 + q, 29) * 0.08) * sz
                if r > 0.9:
                    _rock(ctx, px, py, r, i * 5 + q, base, rim, sh, line)
        elif kind == "mound":
            wdt = (1.2 + hsh(i, 23) * 2.2) * sz
            ht = (0.25 + hsh(i, 24) * 0.45) * sz
            if wdt < 3:
                continue
            soft_dot(ctx, x + wdt * 0.15, y + ht * 0.05, wdt * 0.7, (0, 0, 0), 0.25)
            ctx.new_path()
            ctx.move_to(x - wdt, y + ht * 0.08)
            ctx.curve_to(x - wdt * 0.5, y - ht * 0.9, x + wdt * 0.4, y - ht * 1.05, x + wdt, y + ht * 0.08)
            ctx.close_path()
            rgba(ctx, mix(base, hexc("6a5644"), 0.2)); ctx.fill_preserve()
            ctx.save(); ctx.clip_preserve()
            g = cairo.LinearGradient(x, y - ht, x, y + ht * 0.1)
            g.add_color_stop_rgba(0, *rim, 0.4)
            g.add_color_stop_rgba(0.5, *rim, 0)
            g.add_color_stop_rgba(1, *sh, 0.35)
            ctx.set_source(g); ctx.paint()
            for q in range(3):  # small pebbles on the mound
                soft_dot(ctx, x + (hsh(i * 3 + q, 30) - 0.5) * wdt, y - ht * 0.4 * hsh(i + q, 31), 0.05 * sz + 1, sh, 0.5)
            ctx.restore()
            ctx.new_path(); ctx.move_to(x - wdt, y + ht * 0.08)
            ctx.curve_to(x - wdt * 0.5, y - ht * 0.9, x + wdt * 0.4, y - ht * 1.05, x + wdt, y + ht * 0.08)
            rgba(ctx, line, 0.35); ctx.set_line_width(max(0.8, sz * 0.02)); ctx.stroke()
        elif kind == "crater":
            r = (0.35 + hsh(i, 23) * 0.6) * sz
            if r < 3:
                continue
            soft_dot(ctx, x, y, r * 1.1, mix(hexc("1c1416"), fog, fade), 0.45)
            ctx.save(); ctx.translate(x, y); ctx.scale(1, 0.25)
            ctx.new_path(); ctx.arc(0, 0, r * 1.05, math.pi * 1.1, math.pi * 1.9)
            rgba(ctx, rim, 0.16); ctx.set_line_width(max(1, r * 0.12)); ctx.stroke()
            ctx.restore()
        elif kind == "shrub":
            ht = (0.35 + hsh(i, 23) * 0.5) * sz
            if ht < 4:
                continue
            for q in range(7):
                a = -math.pi / 2 + (q - 3) * 0.32 + math.sin(t * 1.2 + i + q) * 0.04
                ln = ht * (0.6 + 0.4 * hsh(i * 7 + q, 32))
                ex, ey = x + math.cos(a) * ln, y + math.sin(a) * ln
                ctx.new_path(); ctx.move_to(x, y); ctx.line_to(ex, ey)
                ctx.move_to((x + ex) / 2, (y + ey) / 2)
                ctx.line_to((x + ex) / 2 + math.cos(a + 0.6) * ln * 0.35, (y + ey) / 2 + math.sin(a + 0.6) * ln * 0.35)
                rgba(ctx, line, 0.85); ctx.set_line_width(max(0.8, sz * 0.025)); ctx.stroke()
        elif kind == "stake":
            ht = (0.6 + hsh(i, 23) * 0.8) * sz
            if ht < 4:
                continue
            a = (hsh(i, 24) - 0.5) * 0.7
            ex, ey = x + math.sin(a) * ht, y - math.cos(a) * ht
            soft_dot(ctx, x, y, sz * 0.2, (0, 0, 0), 0.3)
            ctx.new_path(); ctx.move_to(x, y); ctx.line_to(ex, ey)
            rgba(ctx, line, 0.9); ctx.set_line_width(max(1.5, sz * 0.12)); ctx.stroke()
            ctx.new_path(); ctx.move_to(x, y); ctx.line_to(ex, ey)
            rgba(ctx, mix(mul(hexc("6a4a30"), k * 1.4), fog, fade)); ctx.set_line_width(max(1, sz * 0.08)); ctx.stroke()
            ctx.new_path(); ctx.move_to(x - sz * 0.02, y); ctx.line_to(ex - sz * 0.02, ey)
            rgba(ctx, rim, 0.4); ctx.set_line_width(max(0.6, sz * 0.02)); ctx.stroke()


# ---------------------------------------------------------------- fortress
TOWERS = [(-130, 58, 26), (-70, 50, 22), (0, 78, 40), (70, 50, 22), (130, 58, 26)]
TURRETS = [(-130, 52), (-70, 44), (-25, 36), (25, 36), (70, 44), (130, 52)]


def draw_hill(ctx, cam, t, phase, light):
    """The earthen hill the fortress stands on: a slope the horde charges up, with a path to the gate."""
    k, fog, warm, mid = ground_cols(phase, False)
    top_, mid_, hor, glow = sky_cols(phase)
    zs = [SLOPE0 + (SLOPE1 - SLOPE0) * q / 8 for q in range(9)]
    left = [cam.p(-215 + 45 * (hgt(z) / HILL), hgt(z), z) for z in zs]
    right = [cam.p(215 - 45 * (hgt(z) / HILL), hgt(z), z) for z in zs]
    far_l, far_r = cam.p(-170, HILL, WALL), cam.p(170, HILL, WALL)
    poly = [cam.p(-330, 0, SLOPE0 - 10)] + left + [far_l, far_r] + list(reversed(right)) + [cam.p(330, 0, SLOPE0 - 10)]
    base = mix(mul(hexc("5c4a3c"), k * 1.15), fog, 0.35)

    def outline():
        ctx.move_to(*poly[0])
        smooth_open(ctx, poly[1:-1], move=False)
        ctx.line_to(*poly[-1])
        ctx.close_path()
    ctx.new_path(); outline()
    sc = cam.f / max(1, cam.depth((SLOPE0 + WALL) / 2))
    ctx.set_source(pattern("dirt", sc * TILE_M / 256.0)); ctx.fill_preserve()
    ctx.save(); ctx.clip_preserve()
    rgba(ctx, base, 0.62); ctx.fill_preserve()
    ytop, ybot = far_l[1], poly[0][1]
    g = cairo.LinearGradient(0, ytop, 0, ybot)
    g.add_color_stop_rgba(0, *mix(warm, glow, 0.5), 0.38 * (1 - clamp(phase - 1.6)))
    g.add_color_stop_rgba(0.12, *light["shadow"], 0.15)
    g.add_color_stop_rgba(1, *light["shadow"], 0.45)
    ctx.set_source(g); ctx.paint()
    # erosion gullies + scorch marks
    for q in range(16):
        X = (hsh(q, 101) - 0.5) * 300
        a = cam.p(X, hgt(SLOPE1 - 2), SLOPE1 - 2)
        b = cam.p(X + (hsh(q, 102) - 0.5) * 20, 0.5, SLOPE0 + 2)
        soft_stroke(ctx, [a, ((a[0] + b[0]) / 2 + 6, (a[1] + b[1]) / 2), b], light["shadow"], 0.22, max(1.5, sc * 0.8))
    for q in range(10):
        X = (hsh(q, 103) - 0.5) * 120
        Zq = SLOPE0 + hsh(q, 104) * (SLOPE1 - SLOPE0)
        p = cam.p(X, hgt(Zq), Zq)
        soft_dot(ctx, p[0], p[1], sc * (2 + 3 * hsh(q, 105)), hexc("140c0c"), 0.35)
    # switchback path up to the gate
    path = [(4, SLOPE0 - 6), (10, SLOPE0 + 6), (-9, SLOPE0 + 16), (8, SLOPE0 + 26), (-6, SLOPE0 + 34), (0, SLOPE1 + 1), (0, WALL - 1)]
    pp = [cam.p(X, hgt(Z) + 0.05, Z) for X, Z in path]
    for wdt, col, a in ((sc * 6.5, light["shadow"], 0.35), (sc * 5.0, mix(hexc("8a7458"), fog, 0.3), 0.55)):
        ctx.new_path(); smooth_open(ctx, pp)
        rgba(ctx, mul(col, k * 1.25), a); ctx.set_line_width(max(2, wdt)); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
    # rocks and rubble on the slope and heaped at the foot of the wall
    for q in range(60):
        X = (hsh(q, 106) - 0.5) * 320
        Zq = SLOPE0 + hsh(q, 107) * (WALL - 2 - SLOPE0) if q < 40 else WALL - 1.5 - hsh(q, 108) * 4
        p = cam.p(X, hgt(Zq), Zq)
        r = (0.5 + hsh(q, 109) * 1.6) * cam.f / max(1, cam.depth(Zq))
        if r > 1.2:
            _rock(ctx, p[0], p[1], r, 900 + q, mix(base, hexc("6a6064"), 0.3), mix(warm, fog, 0.3), light["shadow"], light["line"])
    ctx.restore()
    # crest rim light + contact shadow line under the wall
    ctx.new_path(); ctx.move_to(*left[-1]); ctx.line_to(*far_l); ctx.line_to(*far_r); ctx.line_to(*right[-1])
    rgba(ctx, mix(warm, glow, 0.5), 0.55 * (1 - clamp(phase - 1.6))); ctx.set_line_width(2); ctx.stroke()


def _wood(ctx, x0, y0, x1, y1, seed, k=1.0, col=None):
    col = col or hexc("7a5a3c")
    ctx.new_path(); ctx.rectangle(x0, y0, x1 - x0, y1 - y0)
    rgba(ctx, mul(col, k)); ctx.fill_preserve()
    ctx.save(); ctx.clip()
    hgt_ = y1 - y0
    for q in range(5):  # grain
        yy = y0 + hgt_ * (0.15 + 0.7 * hsh(seed * 5 + q, 111))
        soft_stroke(ctx, [(x0, yy), ((x0 + x1) / 2, yy + hgt_ * 0.08 * (hsh(seed + q, 112) - 0.5)), (x1, yy)],
                    mul(col, 0.55 * k), 0.45, max(0.6, hgt_ * 0.05))
    g = cairo.LinearGradient(0, y0, 0, y1)
    g.add_color_stop_rgba(0, 1, 0.95, 0.85, 0.12)
    g.add_color_stop_rgba(1, 0, 0, 0, 0.35)
    ctx.set_source(g); ctx.paint()
    ctx.restore()


def draw_sign(ctx, cam, t, phase, light):
    """A crooked, weathered wooden sign that says HUMANITY, hung from one nail by a loop of string."""
    Zs = WALL - 0.4
    dp = cam.depth(Zs)
    if dp < 3:
        return
    nail = cam.p(0, HILL + 33.5, Zs)
    m = cam.f / dp * 1.25  # px per sign unit (sign is 25 m wide)
    if m < 0.6:
        return
    k = float(np.interp(phase, [0, 1, 2, 3], [0.95, 0.85, 0.75, 1.0]))
    lant = cam.p(16.5, HILL + 28.5, Zs - 0.3)
    soft_dot(ctx, lant[0], lant[1], 8 * m, hexc("ffb050"), 0.32)
    swing = -0.13 + 0.035 * math.sin(t * 1.25) + 0.01 * math.sin(t * 3.1)
    ctx.save()
    ctx.translate(*nail)
    ctx.rotate(swing)
    ctx.scale(m, m)
    lw = 1.2 / m
    # string loop from the nail to both top corners
    for cx_ in (-9.6, 9.6):
        ctx.new_path(); ctx.move_to(0, 0); ctx.line_to(cx_ * 0.98, 3.6)
        rgba(ctx, hexc("d8ccaa"), 0.85); ctx.set_line_width(max(lw, 0.14)); ctx.stroke()
    # planks (one shorter, broken corner, gaps)
    planks = [(-10.0, 3.6, 10.2, 5.3), (-10.3, 5.45, 9.7, 7.1), (-9.6, 7.25, 8.3, 8.9)]
    for q, (x0, y0, x1, y1) in enumerate(planks):
        ctx.save(); ctx.translate(0, (y0 + y1) / 2); ctx.rotate((hsh(q, 113) - 0.5) * 0.03); ctx.translate(0, -(y0 + y1) / 2)
        _wood(ctx, x0, y0, x1, y1, q, k)
        rgba(ctx, light.get("line"), 0.85); ctx.new_path(); ctx.rectangle(x0, y0, x1 - x0, y1 - y0)
        ctx.set_line_width(lw * 1.4); ctx.stroke()
        for nx in (x0 + 0.5, x1 - 0.5):  # nail heads
            soft_dot(ctx, nx, (y0 + y1) / 2, 0.22, hexc("2a2622"), 0.95)
        ctx.restore()
    # chunk missing from the bottom-right corner
    ctx.new_path(); ctx.move_to(8.45, 9.05); ctx.line_to(6.9, 9.05); ctx.line_to(7.6, 8.05); ctx.line_to(8.45, 8.35); ctx.close_path()
    rgba(ctx, mul(hexc("231c22"), k)); ctx.fill_preserve()
    rgba(ctx, light.get("line"), 0.8); ctx.set_line_width(lw * 1.2); ctx.stroke()
    # crack through the middle plank
    soft_stroke(ctx, [(-2.0, 5.5), (-1.4, 6.2), (-1.9, 6.6), (-1.2, 7.05)], hexc("1a120c"), 0.8, 0.16, smooth=False)
    # hand-painted letters, each a little off
    ctx.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(3.6)
    word = "HUMANITY"
    widths = [ctx.text_extents(c).x_advance for c in word]
    total = sum(widths) + 0.25 * (len(word) - 1)
    x = -total / 2 - 0.2
    for q, (c, wd) in enumerate(zip(word, widths)):
        ctx.save()
        rot = (hsh(q, 114) - 0.5) * 0.16 + (0.28 if c == "Y" else 0)
        dy = (hsh(q, 115) - 0.5) * 0.45 + (0.35 if c == "Y" else 0)
        ctx.translate(x + wd / 2, 7.75 + dy)
        ctx.rotate(rot)
        ctx.new_path(); ctx.move_to(-wd / 2, 0); ctx.text_path(c)
        rgba(ctx, hexc("1a120c"), 0.55); ctx.set_line_width(0.28); ctx.stroke_preserve()
        rgba(ctx, mul(hexc("efe6cf"), k), 0.95); ctx.fill()
        for z_ in range(3):  # chipped paint
            soft_dot(ctx, (hsh(q * 3 + z_, 116) - 0.5) * wd * 0.8, -1.3 * hsh(q * 3 + z_, 117), 0.18, mul(hexc("7a5a3c"), k), 0.9)
        ctx.restore()
        x += wd + 0.25
    # lantern glow washing over the right side of the sign
    g = cairo.RadialGradient(13.0, 4.0, 0, 13.0, 4.0, 16)
    g.add_color_stop_rgba(0, 1.0, 0.75, 0.4, 0.2)
    g.add_color_stop_rgba(1, 1.0, 0.75, 0.4, 0.0)
    ctx.set_source(g); ctx.rectangle(-11, 3, 22, 7); ctx.fill()
    # the nail
    ctx.new_path(); ctx.arc(0, 0, 0.32, 0, 2 * math.pi); rgba(ctx, hexc("3a3430")); ctx.fill()
    soft_dot(ctx, -0.08, -0.08, 0.16, (1, 1, 1), 0.5)
    ctx.restore()
    # lantern on a bracket
    ctx.save(); ctx.translate(*lant); ctx.scale(m, m)
    ctx.new_path(); ctx.move_to(-1.6, -2.6); ctx.line_to(0, -2.6); ctx.line_to(0, -1.4)
    rgba(ctx, hexc("2a2622")); ctx.set_line_width(0.25); ctx.stroke()
    ctx.new_path(); ctx.rectangle(-0.6, -1.4, 1.2, 1.8); rgba(ctx, hexc("ffcf70")); ctx.fill_preserve()
    rgba(ctx, hexc("2a2622")); ctx.set_line_width(0.22); ctx.stroke()
    ctx.restore()
    soft_dot(ctx, lant[0], lant[1], 2.2 * m, hexc("fff0c0"), 0.6)


def draw_fortress(ctx, cam, t, phase, light, flash=0.0):
    if cam.d < 0 or cam.depth(WALL) < 5:
        return
    Z = WALL
    hill_y = HILL
    draw_hill(ctx, cam, t, phase, light)
    top, mid, hor, glow = sky_cols(phase)
    sc = cam.f / cam.depth(Z)
    stone = mix(hexc("6a6470"), mid, 0.2)

    def block(x0, x1, y0, y1, crenel=True):
        a = cam.p(x0, y0, Z); b = cam.p(x1, y1, Z)
        ctx.new_path()
        ctx.move_to(a[0], a[1])
        ctx.line_to(a[0], b[1])
        if crenel:
            n = max(2, int((x1 - x0) / 5))
            wdt = (b[0] - a[0]) / n
            for k in range(n):
                xx = a[0] + k * wdt
                hh = 2.2 * sc if k % 2 == 0 else 0
                q = hsh(int(x0 * 7) + k, 91)
                if hh and q < 0.2:
                    hh = 0                      # merlon fallen away
                elif hh and q < 0.4:
                    hh *= 0.45                  # broken stump
                ctx.line_to(xx, b[1] - hh); ctx.line_to(xx + wdt, b[1] - hh)
        ctx.line_to(b[0], b[1]); ctx.line_to(b[0], a[1]); ctx.close_path()

    def paint_block(x0, x1, y0, y1, crenel=True):
        block(x0, x1, y0, y1, crenel)
        ctx.set_source(pattern("stone", sc * 0.09, 0, 0))
        ctx.fill_preserve()
        ctx.save(); ctx.clip_preserve()
        a = cam.p(x0, y0, Z); b = cam.p(x1, y1, Z)
        g = cairo.LinearGradient(0, b[1], 0, a[1])
        g.add_color_stop_rgba(0, *mix(stone, glow, 0.35), 0.3)
        g.add_color_stop_rgba(0.25, *hexc("2a2238"), 0.5)
        g.add_color_stop_rgba(1, *hexc("1a1424"), 0.72)
        ctx.set_source(g); ctx.fill()
        # grime streaks running down from the top, soot, damp
        for q in range(int((x1 - x0) / 3.5)):
            sx = x0 + hsh(int(x0) * 13 + q, 92) * (x1 - x0)
            ln = 3 + hsh(int(x0) * 13 + q, 93) * (y1 - y0) * 0.6
            wd = (0.5 + hsh(int(x0) * 13 + q, 94) * 1.6) * sc
            p0 = cam.p(sx, y1, Z); p1 = cam.p(sx, y1 - ln, Z)
            g = cairo.LinearGradient(0, p0[1], 0, p1[1])
            g.add_color_stop_rgba(0, 0.06, 0.05, 0.05, 0.55)
            g.add_color_stop_rgba(1, 0.06, 0.05, 0.05, 0.0)
            ctx.set_source(g); ctx.rectangle(p0[0] - wd / 2, p0[1], wd, p1[1] - p0[1]); ctx.fill()
        for q in range(int((x1 - x0) / 12) + 1):  # cracks
            cx_ = x0 + 1 + hsh(int(x0) * 17 + q, 95) * (x1 - x0 - 2)
            cy_ = y0 + 2 + hsh(int(x0) * 17 + q, 96) * (y1 - y0 - 4)
            pts = [cam.p(cx_, cy_, Z)]
            for r in range(5):
                cx_ += (hsh(int(x0) * 17 + q * 5 + r, 97) - 0.5) * 2.4
                cy_ -= 1.0 + hsh(int(x0) * 17 + q * 5 + r, 98) * 1.6
                pts.append(cam.p(cx_, cy_, Z))
            soft_stroke(ctx, pts, hexc("0e0a0e"), 0.75, max(0.8, sc * 0.18), smooth=False)
        g = cairo.LinearGradient(0, a[1] - 6 * sc, 0, a[1])  # damp, dark base
        g.add_color_stop_rgba(0, 0.05, 0.06, 0.04, 0.0)
        g.add_color_stop_rgba(1, 0.05, 0.06, 0.04, 0.5)
        ctx.set_source(g); ctx.paint()
        ctx.restore()
        rgba(ctx, glow, 0.45 * (1 - clamp(phase - 1.5)))
        ctx.set_line_width(max(1, sc * 0.4))
        block(x0, x1, y0, y1, crenel)
        ctx.stroke()

    paint_block(-150, 150, hill_y, hill_y + 30)
    for (x, h, w) in TOWERS:
        paint_block(x - w / 2, x + w / 2, hill_y, hill_y + h)
    # boarded-up breaches
    for (bx, by, bw_, bh_) in ((-46, hill_y + 6, 9, 7), (96, hill_y + 9, 7, 6)):
        a = cam.p(bx, by, Z); b = cam.p(bx + bw_, by + bh_, Z)
        ctx.new_path(); smooth_closed(ctx, [(a[0], a[1]), (a[0] - sc, (a[1] + b[1]) / 2), (a[0] + sc, b[1]), ((a[0] + b[0]) / 2, b[1] - sc),
                                            (b[0], b[1] + sc), (b[0] + sc * 0.5, a[1])], 0.7)
        rgba(ctx, hexc("0c080c")); ctx.fill()
        for q in range(3):
            y_ = lerp(b[1], a[1], 0.2 + q * 0.3)
            ctx.save(); ctx.translate((a[0] + b[0]) / 2, y_); ctx.rotate((hsh(q + bx, 99) - 0.5) * 0.5)
            _wood(ctx, -(b[0] - a[0]) * 0.65, -0.55 * sc, (b[0] - a[0]) * 0.65, 0.55 * sc, q + 7, 0.75)
            ctx.restore()
    # gate
    a = cam.p(-9, hill_y, Z); b = cam.p(9, hill_y + 16, Z)
    ctx.new_path(); ctx.rectangle(a[0], b[1], b[0] - a[0], a[1] - b[1]); rgba(ctx, hexc("140e14")); ctx.fill()
    # lit windows (soot above each) + glow
    for i in range(46):
        tw = TOWERS[i % 5]
        x = tw[0] + (hsh(i, 31) - 0.5) * tw[2] * 0.7
        y = hill_y + 6 + hsh(i, 32) * (tw[1] - 12)
        if i >= 30:
            x = (hsh(i, 33) - 0.5) * 280
            y = hill_y + 8 + hsh(i, 34) * 16
        p = cam.p(x, y, Z)
        on = 0.6 + 0.4 * math.sin(t * 0.7 + i)
        wcol = hexc("ffd27a")
        soft_dot(ctx, p[0], p[1] - 2.2 * sc, 1.8 * sc, hexc("0a0608"), 0.45)
        soft_dot(ctx, p[0], p[1], 3.5 * sc, wcol, 0.35 * on)
        rgba(ctx, wcol, 0.9 * on)
        ctx.new_path(); ctx.rectangle(p[0] - 0.7 * sc, p[1] - 1.1 * sc, 1.4 * sc, 2.2 * sc); ctx.fill()
    draw_sign(ctx, cam, t, phase, light)
    # searchlights sweeping
    for k, (x, h, w) in enumerate((TOWERS[0], TOWERS[2], TOWERS[4])):
        p = cam.p(x, hill_y + h - 4, Z)
        ang = -math.pi / 2 + math.sin(t * 0.35 + k * 2.1) * 0.7
        ln = 900
        ctx.new_path()
        ctx.move_to(*p)
        ctx.line_to(p[0] + math.cos(ang - 0.05) * ln, p[1] + math.sin(ang - 0.05) * ln)
        ctx.line_to(p[0] + math.cos(ang + 0.05) * ln, p[1] + math.sin(ang + 0.05) * ln)
        ctx.close_path()
        g = cairo.RadialGradient(p[0], p[1], 0, p[0], p[1], ln)
        g.add_color_stop_rgba(0, 0.9, 0.95, 1, 0.22)
        g.add_color_stop_rgba(1, 0.9, 0.95, 1, 0)
        ctx.set_source(g); ctx.fill()
    if flash > 0:
        soft_dot(ctx, *cam.p(0, 40, Z), 300, hexc("cfe8ff"), 0.25 * flash)


# ---------------------------------------------------------------- horde
class Horde:
    def __init__(self, n=230, near=70):
        self.z0 = 30.0
        self.z_items = []
        self.L = []
        for i in range(n + near):
            if i < n:
                X = (hsh(i, 41) - 0.5) * 50
            else:
                X = (hsh(i, 41) - 0.5) * 9
            v = 2.5 + hsh(i, 42) * 1.3
            zd = WALL - 18 - hsh(i, 43) * 55
            span = zd - self.z0
            ph = hsh(i, 44) * span
            self.L.append(dict(i=i, X=X, v=v, zd=zd, span=span, ph=ph, style=rig.horde_style(i),
                               run=hsh(i, 45) * 6.28, reach=hsh(i, 46) < 0.45, rate=7.5 + hsh(i, 47) * 2))

    def state(self, z, t):
        u = z["v"] * t + z["ph"]
        k = math.floor(u / z["span"])
        Z = self.z0 + (u - k * z["span"])
        tdeath = (k * z["span"] - z["ph"]) / z["v"]
        X = z["X"]
        # flow around the conscious one (like water around a stone) and around the building
        for (ox, oz, r) in ((0.0, ZC, 1.7), (BLD[0], BLD[1] + 4, 6.5)):
            dx = X - ox
            if abs(dx) < r:
                # the gap stays open downstream (toward the fortress side of the stone)
                b = math.exp(-((Z - oz) / (r * (2.2 if Z < oz else 8.0))) ** 2)
                X = X + (math.copysign(r, dx if dx != 0 else 1) - dx) * b
        return X, Z, tdeath

    def items(self, cam, t, light_f, light_b, fire=True, dust=True, alive_only=False, zmax=None):
        """Return [(depth, fn)] for depth sorting."""
        out = []
        for z in self.L:
            X, Z, td = self.state(z, t)
            dp = cam.depth(Z)
            if zmax is not None and Z > zmax:
                continue
            if 0.8 < dp < 330:
                x, y = cam.p(X, hgt(Z), Z)
                s = cam.scale(Z, 1.72 + hsh(z["i"], 48) * 0.12)
                if -150 * max(1, s * 3) < x < W + 150 * max(1, s * 3) and y - FIG_H * s < H:
                    fadein = clamp((Z - self.z0) / 3)
                    out.append((dp, self._fig(z, x, y, s, t, cam, light_f if cam.d < 0 else light_b, fadein)))
            # dust + beam for a recent death
            if dust and t - td < 3.0 and td > -5:
                Xd = X  # lane at death (no deflection near the wall)
                Zd = z["zd"]
                dpd = cam.depth(Zd)
                if 0.8 < dpd < 330:
                    out.append((dpd - 0.1, self._dust(z, Xd, Zd, t - td, cam, light_b, fire)))
        return out

    def _fig(self, z, x, y, s, t, cam, light, alpha):
        def fn(ctx):
            ph = t * z["rate"] + z["run"]
            bob = abs(math.sin(ph)) * 10
            view = "back" if cam.d > 0 else "front"
            P = dict(x=x, y=y - (578 - bob) * s, s=s, view=view, lw=1.6, breath=0,
                     legs=dict(mode="run", phase=ph), roll=math.sin(ph) * 0.05,
                     yaw=math.sin(ph * 0.5 + z["i"]) * 0.08, pitch=0.1,
                     E=rig.expr(op=0.22 + 0.1 * math.sin(ph * 0.5), sm=-0.25, milky=1.0, t=t, bi=0.0, lid=0.32,
                                drone=1.0, grime=1.0))
            for side, sgn in (("armL", -1), ("armR", 1)):
                sw = math.sin(ph + (0 if sgn < 0 else math.pi))
                if view == "back":
                    # running at the wall: arms reach forward, hands hidden in front of the body
                    P[side] = dict(el=(sgn * (66 + 4 * sw), 92 + 8 * sw), wr=(sgn * 30, 64 + 12 * sw), hand_ang=-1.57,
                                   curl=0.5, flip=sgn > 0)
                    P["arms_behind"] = ("L", "R")
                elif z["reach"]:
                    P[side] = dict(el=(sgn * 72, 110 + 6 * sw), wr=(sgn * 46, 140 + 10 * sw), hand_ang=1.57 - sgn * 0.25,
                                   curl=0.55, thumb=0.6, flip=sgn > 0, palm=False, hfs=0.55)
                    if view == "back":
                        P["arms_behind"] = ("L", "R")
                else:
                    P[side] = dict(el=(sgn * 74, 112 - 16 * sw), wr=(sgn * (62 - 16 * max(0, sw)), 196 - 110 * max(0, sw)),
                                   curl=0.5, flip=sgn > 0)
            if s < 0.02:
                # distant: simple silhouette
                rgba(ctx, tint(z["style"]["shirt"], light), alpha)
                ctx.new_path()
                capsule(ctx, (x, y - 520 * s), (x, y - 330 * s), 70 * s, 55 * s); ctx.fill()
                rgba(ctx, tint(z["style"]["pants"], light), alpha)
                ctx.new_path()
                ctx.rectangle(x - 45 * s, y - 330 * s, 90 * s, 330 * s - bob * s); ctx.fill()
                rgba(ctx, tint(z["style"]["skin"] if cam.d < 0 else z["style"]["hair"], light), alpha)
                ctx.new_path(); ctx.arc(x, y - 640 * s, 55 * s, 0, 6.3); ctx.fill()
                return
            if alpha < 0.99:
                ctx.push_group()
            rig.draw_character(ctx, z["style"], P, light, t)
            if alpha < 0.99:
                ctx.pop_group_to_source(); ctx.paint_with_alpha(alpha)
        return fn

    def _dust(self, z, X, Z, age, cam, light, fire):
        def fn(ctx):
            s = cam.scale(Z)
            Y0 = hgt(Z)
            x, y = cam.p(X, Y0, Z)
            # the body crumbling: fading silhouette
            if age < 0.6:
                a = 1 - age / 0.6
                rgba(ctx, mix(hexc("8a7a6a"), (1, 1, 1), 0.4 * a), a * 0.9)
                ctx.new_path()
                capsule(ctx, (x, y - 560 * s), (x, y - 120 * s), 75 * s, 60 * s)
                ctx.fill()
            ex = cam.f / max(1, cam.depth(Z))
            for k in range(26):
                r0 = hsh(z["i"] * 31 + k, 51)
                px = X + (r0 - 0.5) * 0.8 + age * (0.9 + hsh(k, 52) * 1.2)
                py = Y0 + 0.2 + hsh(k, 53) * 1.6 + age * (0.35 + hsh(k, 54) * 0.6)
                p = cam.p(px, py, Z)
                rr = (0.22 + age * 0.45) * ex
                a = clamp(1 - age / 3.0) * 0.5 * (0.5 + hsh(k, 55))
                soft_dot(ctx, p[0], p[1], max(1.5, rr), mix(hexc("9a8c7e"), light["rim"], 0.25), a)
            # beam from the wall
            if fire and age < 0.25 and cam.d > 0:
                tx = min(TURRETS, key=lambda q: abs(q[0] - X))
                a0 = cam.p(tx[0], 16 + tx[1], WALL)
                a1 = cam.p(X, Y0 + 1.0, Z)
                k = 1 - age / 0.25
                for wdt, al in ((14, 0.12), (6, 0.35), (2, 0.95)):
                    ctx.new_path(); ctx.move_to(*a0); ctx.line_to(*a1)
                    rgba(ctx, hexc("d4ecff"), al * k)
                    ctx.set_line_width(wdt)
                    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
                    ctx.stroke()
                soft_dot(ctx, a1[0], a1[1], 60 * max(0.3, s * 4), hexc("e0f2ff"), 0.6 * k)
                soft_dot(ctx, a0[0], a0[1], 30, hexc("e0f2ff"), 0.8 * k)
        return fn

    def flash(self, t):
        """How much beam light is in the air (for lighting flicker)."""
        f = 0.0
        for z in self.L[::3]:
            _, _, td = self.state(z, t)
            if 0 <= t - td < 0.3:
                f += 1 - (t - td) / 0.3
        return clamp(f * 0.6)


def beam_times(horde, t0, t1):
    out = []
    for z in horde.L:
        u0 = z["v"] * t0 + z["ph"]
        u1 = z["v"] * t1 + z["ph"]
        k0, k1 = math.floor(u0 / z["span"]), math.floor(u1 / z["span"])
        for k in range(k0 + 1, k1 + 1):
            out.append(((k * z["span"] - z["ph"]) / z["v"], z["X"], z["zd"]))
    return sorted(out)


def draw_motes(ctx, t, n=40, col=(0.9, 0.8, 0.7), a=0.25, seed=0, drift=(14, -6)):
    for i in range(n):
        x = (hsh(i, 61 + seed) * W + t * drift[0] * (0.5 + hsh(i, 62))) % (W + 40) - 20
        y = (hsh(i, 63 + seed) * H + t * drift[1] * (0.5 + hsh(i, 64)) + math.sin(t + i) * 8) % (H + 40) - 20
        r = 2 + hsh(i, 65) * 5
        soft_dot(ctx, x, y, r, col, a * (0.4 + 0.6 * hsh(i, 66)))


def draw_smoke(ctx, cam, t, phase, n=10):
    if cam.d < 0:
        return
    top, mid, hor, glow = sky_cols(phase)
    for i in range(n):
        X = (hsh(i, 71) - 0.5) * 300
        Zs = WALL - 30 - hsh(i, 72) * 30
        for k in range(6):
            age = (t * 0.25 + hsh(i, 73) + k / 6) % 1.0
            p = cam.p(X + age * 25, hgt(Zs) + age * 70, Zs)
            r = (6 + age * 26) * cam.f / max(1, cam.depth(Zs))
            soft_dot(ctx, p[0], p[1], r, mix(hexc("3a3238"), mid, 0.3), 0.32 * (1 - age))
        fp = cam.p(X, hgt(Zs) + 0.5, Zs)
        soft_dot(ctx, fp[0], fp[1], 40 * cam.f / max(1, cam.depth(Zs)) * 0.6, hexc("ff8a3a"), 0.35 + 0.1 * math.sin(t * 7 + i))


# ---------------------------------------------------------------- building
def draw_building(ctx, cam, t, light, phase, flag=True, flag_k=0.0):
    """Ruined 3-storey brick building; front face at Z=BLD[1]; ladder on the front, left side."""
    X0, Z0 = BLD
    w, h, dpt = 8.0, 11.0, 7.0
    dp = cam.depth(Z0)
    if dp < 0.3:
        return
    top, mid, hor, glow = sky_cols(phase)
    sc = cam.f / dp
    fl, fr = X0 - w / 2, X0 + w / 2
    # side face (visible side depends on camera x)
    if cam.d > 0:
        side_x = fl if cam.x < fl else fr if cam.x > fr else None
        if side_x is not None:
            pts = [cam.p(side_x, 0, Z0), cam.p(side_x, h, Z0), cam.p(side_x, h, Z0 + dpt), cam.p(side_x, 0, Z0 + dpt)]
            ctx.new_path(); ctx.move_to(*pts[0])
            for q in pts[1:]:
                ctx.line_to(*q)
            ctx.close_path()
            ctx.set_source(pattern("brick", sc * 0.012)); ctx.fill_preserve()
            rgba(ctx, hexc("140e18"), 0.6); ctx.fill()
    a = cam.p(fl, 0, Z0); b = cam.p(fr, h, Z0)
    # broken roofline
    ctx.new_path()
    ctx.move_to(a[0], a[1])
    ctx.line_to(a[0], b[1])
    for k in range(9):
        u = (k + 1) / 9
        dy = (0.0 if k % 3 else 0.5) + (hsh(k, 81) * 0.4 if 3 < k < 7 else 0)
        ctx.line_to(lerp(a[0], b[0], u), b[1] + dy * sc)
    ctx.line_to(b[0], a[1])
    ctx.close_path()
    ctx.set_source(pattern("brick", sc * 0.012, a[0] / (sc * 0.012), 0))
    ctx.fill_preserve()
    ctx.save(); ctx.clip_preserve()
    lx = light["dir"][0]
    g = cairo.LinearGradient(a[0], 0, b[0], 0)
    g.add_color_stop_rgba(0, *light["shadow"], 0.35 if lx > 0 else 0.05)
    g.add_color_stop_rgba(1, *light["shadow"], 0.05 if lx > 0 else 0.35)
    ctx.set_source(g); ctx.fill_preserve()
    rgba(ctx, hexc("141028"), 0.45 * clamp(phase - 1.0)); ctx.fill_preserve()
    g = cairo.LinearGradient(0, b[1], 0, a[1])
    g.add_color_stop_rgba(0, *light["rim"], 0.18)
    g.add_color_stop_rgba(0.4, *light["shadow"], 0.15)
    g.add_color_stop_rgba(1, *light["shadow"], 0.45)
    ctx.set_source(g); ctx.fill()
    soft_dot(ctx, (a[0] + b[0]) / 2, a[1], (b[0] - a[0]) * 0.7, (0, 0, 0), 0.35)
    # windows (dark, broken) + cracks
    for fy in (2.2, 5.6, 9.0):
        for fx in (1.6, 4.0, 6.4):
            if fx < 2.5 and fy > 1:
                pass
            p0 = cam.p(fl + fx - 0.6, fy + 1.4, Z0)
            p1 = cam.p(fl + fx + 0.6, fy, Z0)
            ctx.new_path(); ctx.rectangle(p0[0], p0[1], p1[0] - p0[0], p1[1] - p0[1])
            rgba(ctx, hexc("100c12"), 0.92); ctx.fill()
            soft_dot(ctx, (p0[0] + p1[0]) / 2, p1[1], (p1[0] - p0[0]) * 0.6, glow, 0.08)
            rgba(ctx, mix(hexc("6a5a50"), light["rim"], 0.2), 0.7)
            ctx.new_path(); ctx.rectangle(p0[0] - 0.08 * sc, p1[1], p1[0] - p0[0] + 0.16 * sc, 0.12 * sc); ctx.fill()
    for k in range(5):
        cx0 = fl + 0.8 + hsh(k, 82) * (w - 1.6)
        cy0 = 1 + hsh(k, 83) * (h - 2)
        pts = [cam.p(cx0, cy0, Z0)]
        for j in range(4):
            pts.append(cam.p(cx0 + (hsh(k * 4 + j, 84) - 0.5) * 0.8, cy0 - 0.5 * (j + 1), Z0))
        soft_stroke(ctx, pts, hexc("1a1214"), 0.5, max(1, 0.03 * sc), smooth=False)
    ctx.restore()
    rgba(ctx, light.get("line"), 0.8); ctx.set_line_width(max(1, sc * 0.03)); ctx.stroke()
    # roof surface when seen from above
    if cam.y > h:
        pts = [cam.p(fl, h, Z0), cam.p(fr, h, Z0), cam.p(fr, h, Z0 + dpt), cam.p(fl, h, Z0 + dpt)]
        ctx.new_path(); ctx.move_to(*pts[0])
        for q in pts[1:]:
            ctx.line_to(*q)
        ctx.close_path()
        ctx.set_source(pattern("brick", sc * 0.02)); ctx.fill_preserve()
        rgba(ctx, mix(hexc("2a2228"), light["shadow"], 0.3), 0.78); ctx.fill_preserve()
        rgba(ctx, light.get("line"), 0.8); ctx.set_line_width(1.5); ctx.stroke()
        soft_stroke(ctx, [pts[0], pts[1]], light["rim"], 0.35, 3, smooth=False)
    # ladder
    draw_ladder(ctx, cam, fl + 0.9, Z0 - 0.15, h + 1.0, sc, light)
    # flagpole
    if flag:
        draw_flag(ctx, cam, X0 - 1.0, h, Z0 + 2.5, t, light, phase, held=False)


def draw_ladder(ctx, cam, X, Z, top, sc, light):
    rust = hexc("6a4a3a")
    for dx in (-0.25, 0.25):
        p0 = cam.p(X + dx, 0, Z); p1 = cam.p(X + dx, top, Z)
        ctx.new_path(); ctx.move_to(*p0); ctx.line_to(*p1)
        rgba(ctx, light.get("line"), 0.9); ctx.set_line_width(max(1.5, 0.075 * sc)); ctx.stroke()
        ctx.new_path(); ctx.move_to(*p0); ctx.line_to(*p1)
        rgba(ctx, tint(rust, light)); ctx.set_line_width(max(1, 0.05 * sc)); ctx.stroke()
    n = int(top / 0.32)
    for k in range(1, n):
        y = k * 0.32
        p0 = cam.p(X - 0.25, y, Z); p1 = cam.p(X + 0.25, y, Z)
        ctx.new_path(); ctx.move_to(*p0); ctx.line_to(*p1)
        rgba(ctx, light.get("line"), 0.9); ctx.set_line_width(max(1.2, 0.05 * sc)); ctx.stroke()
        ctx.new_path(); ctx.move_to(*p0); ctx.line_to(*p1)
        rgba(ctx, tint(mix(rust, light["rim"], 0.2), light)); ctx.set_line_width(max(0.8, 0.03 * sc)); ctx.stroke()


def flag_cloth(ctx, x, y, w, h, t, wind=1.0, col=hexc("ece6d8"), light=None, lw=1.5, side=1):
    """Cloth flying from a pole at (x,y) (top attach) to the side."""
    n = 10
    topp, botp = [], []
    for k in range(n + 1):
        u = k / n
        wave = math.sin(t * 9 * wind - u * 5.5) * h * 0.16 * u * wind + math.sin(t * 5.3 - u * 3) * h * 0.06 * u
        xx = x + side * w * u * (0.92 + 0.08 * math.cos(t * 7 - u * 4))
        topp.append((xx, y + wave + u * h * 0.08 * (1 - wind)))
        botp.append((xx - side * u * w * 0.04, y + h + wave * 1.15 + u * h * 0.25 * (1 - wind)))
    ctx.new_path()
    smooth_open(ctx, topp)
    smooth_open(ctx, list(reversed(botp)), move=False)
    ctx.close_path()
    lt = light or dict(amb=(1, 1, 1), amb_k=0, shadow=(0.2, 0.2, 0.3), rim=(1, 0.8, 0.6), line=(0.1, 0.1, 0.1))
    rgba(ctx, tint(col, lt)); ctx.fill_preserve()
    ctx.save(); ctx.clip_preserve()
    for k in range(1, n):
        u = k / n
        sh = math.sin(t * 9 * wind - u * 5.5 + 1.2)
        if sh > 0.2:
            soft_stroke(ctx, [topp[k], botp[k]], lt["shadow"], 0.25 * sh, lw * 6)
    ctx.restore()
    rgba(ctx, lt.get("line"), 0.85); ctx.set_line_width(lw); ctx.stroke()


def draw_flag(ctx, cam, X, Y, Z, t, light, phase, held=False):
    p0 = cam.p(X, Y, Z); p1 = cam.p(X, Y + 3.2, Z)
    sc = cam.f / max(0.3, cam.depth(Z))
    ctx.new_path(); ctx.move_to(*p0); ctx.line_to(*p1)
    rgba(ctx, light.get("line"), 0.9); ctx.set_line_width(max(1.5, 0.07 * sc)); ctx.stroke()
    ctx.new_path(); ctx.move_to(*p0); ctx.line_to(*p1)
    rgba(ctx, tint(hexc("8a8478"), light)); ctx.set_line_width(max(1, 0.045 * sc)); ctx.stroke()
    flag_cloth(ctx, p1[0], p1[1] + 0.05 * sc, 1.5 * sc, 0.95 * sc, t, 0.7, light=light, lw=max(1, 0.02 * sc))


# ---------------------------------------------------------------- helicopter
def draw_heli(ctx, x, y, s, t, light, door=True, spot=0.0, bank=0.0, face=1):
    """Side view, nose toward +face. (x,y) = cabin centre."""
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(bank)
    ctx.scale(s * face, s)
    lw = 2.0 / s
    body = hexc("4a5048")
    if spot > 0:
        g = cairo.LinearGradient(120, 40, 120, 900)
        g.add_color_stop_rgba(0, 1, 0.97, 0.85, 0.35 * spot)
        g.add_color_stop_rgba(1, 1, 0.97, 0.85, 0)
        ctx.new_path(); ctx.move_to(110, 40); ctx.line_to(-80, 900); ctx.line_to(420, 900); ctx.line_to(140, 40); ctx.close_path()
        ctx.set_source(g); ctx.fill()
    # tail boom
    shade(ctx, lambda: (ctx.move_to(-120, -30), ctx.line_to(-420, -50), ctx.line_to(-430, -30), ctx.line_to(-120, 10), ctx.close_path()),
          body, light, lw)
    shade(ctx, lambda: (ctx.move_to(-410, -48), ctx.line_to(-450, -120), ctx.line_to(-425, -120), ctx.line_to(-395, -40), ctx.close_path()),
          body, light, lw)
    # tail rotor blur
    soft_dot(ctx, -430, -80, 46, hexc("c8c8c0"), 0.25)
    ctx.new_path(); ctx.move_to(-430 + 40 * math.cos(t * 50), -80 + 40 * math.sin(t * 50))
    ctx.line_to(-430 - 40 * math.cos(t * 50), -80 - 40 * math.sin(t * 50))
    rgba(ctx, hexc("2a2a2a"), 0.5); ctx.set_line_width(4); ctx.stroke()
    # fuselage
    fus = [(-140, -60), (40, -78), (150, -60), (215, -10), (210, 40), (150, 70), (-120, 70), (-160, 20)]
    shade(ctx, lambda: smooth_closed(ctx, fus), body, light, lw, shadow=0.5)
    # cockpit glass
    shade(ctx, lambda: smooth_closed(ctx, [(120, -58), (165, -50), (206, -8), (200, 18), (130, 10)]),
          hexc("7a9aaa"), light, lw, shadow=0.3, rim=1.0)
    # door opening
    if door:
        ctx.new_path(); ctx.rectangle(-60, -50, 130, 105)
        rgba(ctx, hexc("1a1214")); ctx.fill()
        soft_dot(ctx, 5, 0, 70, hexc("ff5a3a"), 0.45)
    # skids
    for sx in (-90, 110):
        soft_stroke(ctx, [(sx, 70), (sx - 10, 100)], hexc("202020"), 1.0, 5, smooth=False)
    soft_stroke(ctx, [(-150, 100), (170, 100), (190, 90)], hexc("202020"), 1.0, 6)
    # mast + rotor disc
    shade(ctx, lambda: (ctx.rectangle(-10, -100, 22, 26)), mul(body, 0.8), light, lw)
    g = cairo.RadialGradient(0, -102, 0, 0, -102, 380)
    g.add_color_stop_rgba(0, 0.8, 0.8, 0.8, 0.0)
    g.add_color_stop_rgba(0.6, 0.8, 0.8, 0.8, 0.12)
    g.add_color_stop_rgba(1, 0.8, 0.8, 0.8, 0)
    ctx.save(); ctx.translate(0, -102); ctx.scale(1, 0.08)
    ctx.set_source(g); ctx.arc(0, 0, 380, 0, 6.3); ctx.fill()
    for k in range(2):
        a = t * 28 + k * math.pi
        ctx.new_path(); ctx.move_to(0, 0); ctx.line_to(380 * math.cos(a), 380 * math.sin(a))
        rgba(ctx, hexc("1a1a1a"), 0.55); ctx.set_line_width(10 / 0.08 * 0.08 * 6); ctx.stroke()
    ctx.restore()
    # nav lights
    soft_dot(ctx, -440, -120, 20, hexc("ff3030"), 0.6 + 0.4 * (math.sin(t * 6) > 0.6))
    ctx.restore()


# ---------------------------------------------------------------- cabin interior
def draw_cabin(ctx, t, dawn=0.0, shake=0.0, window_x=520, wall="back"):
    ox = math.sin(t * 13) * shake
    oy = math.sin(t * 17.3) * shake
    ctx.save(); ctx.translate(ox, oy)
    base = mix(hexc("3a4040"), hexc("4a4a44"), dawn * 0.4)
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *mul(base, 0.7))
    g.add_color_stop_rgb(0.5, *base)
    g.add_color_stop_rgb(1, *mul(base, 0.6))
    ctx.set_source(g); ctx.rectangle(-30, -30, W + 60, H + 60); ctx.fill()
    # ribs
    for i in range(-1, 6):
        x = i * 170 + 40
        ctx.new_path(); ctx.rectangle(x, -30, 22, H + 60)
        rgba(ctx, mul(base, 0.75)); ctx.fill()
        soft_stroke(ctx, [(x + 2, -30), (x + 2, H + 30)], hexc("ffa070"), 0.10 + 0.1 * dawn, 3, smooth=False)
        for k in range(12):
            soft_dot(ctx, x + 11, 60 + k * 100, 3, hexc("1a1a1a"), 0.5)
    # window with sky
    wx, wy, ww, wh = window_x, 300, 190, 150
    ctx.new_path(); rig._rrect(ctx, wx - ww / 2, wy - wh / 2, ww, wh, 40)
    g = cairo.LinearGradient(0, wy - wh / 2, 0, wy + wh / 2)
    g.add_color_stop_rgb(0, *mix(hexc("101430"), hexc("4a6a9a"), dawn))
    g.add_color_stop_rgb(1, *mix(hexc("3a2440"), hexc("ffc890"), dawn))
    ctx.set_source(g); ctx.fill_preserve()
    rgba(ctx, hexc("1a1c1c")); ctx.set_line_width(10); ctx.stroke()
    soft_dot(ctx, wx, wy + 60, 200, mix(hexc("6a5aa0"), hexc("ffd0a0"), dawn), 0.15 + 0.25 * dawn)
    # red cabin lamp
    soft_dot(ctx, 120, 90, 260, hexc("ff4a30"), 0.22 * (1 - dawn * 0.5))
    ctx.new_path(); ctx.rectangle(95, 70, 50, 20); rgba(ctx, hexc("ff6a50"), 0.9); ctx.fill()
    # straps / cargo net
    for i in range(5):
        soft_stroke(ctx, [(i * 160 - 20, 150), (i * 160 + 60, 230), (i * 160 + 140, 150)], hexc("8a7a50"), 0.5, 4)
    ctx.restore()
