"""Kai's sketchbook: page, wobbly ink, marker fills, hand lettering, icons, figures.

Everything here is deterministic: wobble comes from seeded value noise along the
stroke's arc length, so a stroke looks identical in every frame and only its
drawn-on fraction changes.
"""
import math
import os

import numpy as np
import skia

import paths
from gfx import clamp, hexc

W, H = 1080, 1920

# ---------------------------------------------------------------- palette
INK = "#26252c"
PAGE = "#f3ead8"
PAGE_SH = "#e2d4b8"
TEAL = "#5aa69c"
CORAL = "#e2765f"
MUSTARD = "#f0b84a"
BLUE = "#6d8ec2"
GREY = "#a3a6ab"
LGREY = "#c9cbcf"
NAVY = "#3f5378"
OLIVE = "#8a9a5b"
GREEN = "#5f8f5a"
COLD = "#7fa3cf"
HOODIE = "#9a9ea6"
SKIN = ["#c98c66", "#8d5a3b", "#e0b48a", "#a8714f", "#d9a27a", "#6e4630"]
WARM = "#ffd98a"


# ---------------------------------------------------------------- timing helpers
def prog(t, t0, dur):
    """0..1 linear progress of an animation that starts at t0 and lasts dur."""
    if dur <= 0:
        return 1.0 if t >= t0 else 0.0
    return clamp((t - t0) / dur)


def eprog(t, t0, dur):
    """Eased (smoothstep) progress."""
    u = prog(t, t0, dur)
    return u * u * (3 - 2 * u)


def pop(t, t0, dur=0.38):
    """Scale for a pop-in with a little overshoot (0 before t0, settles at 1)."""
    u = prog(t, t0, dur)
    if u <= 0:
        return 0.0
    if u >= 1:
        return 1.0
    s = 1.70158 * 1.4
    v = u - 1
    return v * v * ((s + 1) * v + s) + 1


def cue(cues, name, default):
    v = cues.get(name)
    return default if v is None else v


# ---------------------------------------------------------------- fonts
_TF = {}
FONT_FILES = {"caveat": "Caveat-SemiBold.ttf", "caveat_b": "Caveat-Bold.ttf", "hand": "PatrickHand-Regular.ttf"}


def _typeface(kind):
    if kind not in _TF:
        fp = os.path.join(paths.BUILD, "fonts", FONT_FILES[kind])
        if not os.path.exists(fp):
            try:
                import fetch_fonts
                fetch_fonts.fetch()
            except Exception:
                pass
        tf = skia.Typeface.MakeFromFile(fp) if os.path.exists(fp) else None
        if tf is None:
            tf = skia.Typeface("Inter", skia.FontStyle.Bold())
        _TF[kind] = tf
    return _TF[kind]


_FONTS = {}


def hfont(size, kind="caveat"):
    key = (kind, int(size))
    if key not in _FONTS:
        f = skia.Font(_typeface(kind), size)
        f.setEdging(skia.Font.Edging.kAntiAlias)
        f.setSubpixel(True)
        _FONTS[key] = f
    return _FONTS[key]


def write(c, s, x, y, size, kind="caveat", p=1.0, color=INK, align="center", rot=0.0, alpha=1.0):
    """Hand-lettered text revealed left-to-right by progress p."""
    if p <= 0 or alpha <= 0:
        return 0.0
    f = hfont(size, kind)
    w = f.measureText(s)
    x0 = x - w / 2 if align == "center" else (x - w if align == "right" else x)
    c.save()
    if rot:
        c.translate(x, y)
        c.rotate(rot)
        c.translate(-x, -y)
    if p < 1:
        c.clipRect(skia.Rect.MakeLTRB(x0 - 10, y - size * 1.4, x0 + (w + 20) * p, y + size * 0.6))
    paint = skia.Paint(AntiAlias=True, Color=hexc(color, alpha))
    c.drawString(s, x0, y, f, paint)
    c.restore()
    return w


# ---------------------------------------------------------------- noise + wobble
def _hash(i, seed):
    x = np.sin((np.asarray(i, np.float64) + seed * 131.71) * 12.9898) * 43758.5453
    return (x - np.floor(x)) * 2 - 1


def _vnoise(x, seed):
    i = np.floor(x)
    f = x - i
    u = f * f * (3 - 2 * f)
    return _hash(i, seed) * (1 - u) + _hash(i + 1, seed) * u


def densify(pts, step=7.0, closed=False):
    pts = np.asarray(pts, np.float64)
    if closed:
        pts = np.vstack([pts, pts[:1]])
    seg = np.diff(pts, axis=0)
    L = np.hypot(seg[:, 0], seg[:, 1])
    cum = np.concatenate([[0], np.cumsum(L)])
    total = cum[-1]
    if total < 1e-6:
        return pts, np.zeros(len(pts))
    n = max(2, int(total / step) + 1)
    s = np.linspace(0, total, n)
    x = np.interp(s, cum, pts[:, 0])
    y = np.interp(s, cum, pts[:, 1])
    return np.stack([x, y], 1), s


def wobble(pts, seed=0, amp=1.6, period=46.0, step=7.0, closed=False):
    """Resample a polyline and push it sideways with smooth seeded noise."""
    p, s = densify(pts, step, closed)
    if len(p) < 3:
        return p
    d = np.gradient(p, axis=0)
    nrm = np.stack([-d[:, 1], d[:, 0]], 1)
    nrm /= (np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-9)
    off = amp * (_vnoise(s / period, seed) + 0.35 * _vnoise(s / (period * 0.37), seed + 7))
    if closed:
        # fade the offset so the loop closes cleanly
        k = np.minimum(s, s[-1] - s) / max(1.0, period * 0.5)
        off = off * np.clip(k, 0, 1) + off[0] * (1 - np.clip(k, 0, 1))
    return p + nrm * off[:, None]


def smooth_path(pts, closed=False):
    pts = np.asarray(pts, np.float64)
    p = skia.Path()
    n = len(pts)
    if n < 2:
        return p
    if n == 2:
        p.moveTo(*pts[0])
        p.lineTo(*pts[1])
        return p
    p.moveTo(*pts[0])
    for i in range(1, n - 1):
        mx, my = (pts[i][0] + pts[i + 1][0]) / 2, (pts[i][1] + pts[i + 1][1]) / 2
        p.quadTo(pts[i][0], pts[i][1], mx, my)
    p.lineTo(*pts[-1])
    if closed:
        p.close()
    return p


_GEO = {}


def _cached(key, fn):
    g = _GEO.get(key)
    if g is None:
        if len(_GEO) > 60000:
            _GEO.clear()
        g = fn()
        _GEO[key] = g
    return g


def wpath(pts, seed=0, amp=1.6, closed=False, step=7.0, period=46.0):
    arr = np.asarray(pts, np.float64)
    key = ("p", arr.round(1).tobytes(), arr.shape, seed, round(amp, 2), closed, step, period)
    return _cached(key, lambda: smooth_path(wobble(arr, seed, amp, period, step, closed), closed))


def wcircle(cx, cy, r, seed=0, amp=None, start=-100.0, overshoot=14.0):
    key = ("c", round(cx, 1), round(cy, 1), round(r, 1), seed, amp, start, overshoot)
    return _cached(key, lambda: _wcircle(cx, cy, r, seed, amp, start, overshoot))


def _wcircle(cx, cy, r, seed=0, amp=None, start=-100.0, overshoot=14.0):
    """Hand-drawn circle: a slightly overshooting loop."""
    amp = amp if amp is not None else max(0.8, r * 0.035)
    a0 = math.radians(start)
    n = max(14, int(r * 0.9))
    a = np.linspace(a0, a0 + 2 * math.pi + math.radians(overshoot), n)
    rr = r * (1 + 0.03 * np.sin(a * 2 + seed))
    pts = np.stack([cx + np.cos(a) * rr, cy + np.sin(a) * rr], 1)
    return smooth_path(wobble(pts, seed, amp, period=max(20.0, r * 1.4), step=max(3.0, r * 0.12)))


def wellipse(cx, cy, rx, ry, seed=0, amp=1.4, start=-100.0, overshoot=10.0):
    key = ("e", round(cx, 1), round(cy, 1), round(rx, 1), round(ry, 1), seed, amp, start, overshoot)
    return _cached(key, lambda: _wellipse(cx, cy, rx, ry, seed, amp, start, overshoot))


def _wellipse(cx, cy, rx, ry, seed=0, amp=1.4, start=-100.0, overshoot=10.0):
    a0 = math.radians(start)
    a = np.linspace(a0, a0 + 2 * math.pi + math.radians(overshoot), 48)
    pts = np.stack([cx + np.cos(a) * rx, cy + np.sin(a) * ry], 1)
    return smooth_path(wobble(pts, seed, amp, period=40.0, step=6.0))


def wrect(x0, y0, x1, y1, seed=0, amp=1.4):
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0 + 3)]
    return wpath(pts, seed, amp)


# ---------------------------------------------------------------- partial drawing
class Lens:
    """Caches contour lengths of a path for draw-on animation."""

    def __init__(self, path):
        self.path = path
        pm = skia.PathMeasure(path, False)
        self.lens = []
        while True:
            self.lens.append(pm.getLength())
            if not pm.nextContour():
                break
        self.total = sum(self.lens)

    def partial(self, p):
        if p >= 0.999:
            return self.path
        out = skia.Path()
        if p <= 0 or self.total <= 0:
            return out
        target = p * self.total
        pm = skia.PathMeasure(self.path, False)
        acc = 0.0
        for L in self.lens:
            if acc + L <= target:
                pm.getSegment(0, L, out, True)
            else:
                pm.getSegment(0, max(0.0, target - acc), out, True)
                break
            acc += L
            if not pm.nextContour():
                break
        return out


def _ink_paint(w, color, alpha):
    p = skia.Paint(AntiAlias=True, Color=hexc(color, alpha), Style=skia.Paint.kStroke_Style, StrokeWidth=w)
    p.setStrokeCap(skia.Paint.kRound_Cap)
    p.setStrokeJoin(skia.Paint.kRound_Join)
    return p


_LENS = {}


def lens(path):
    k = id(path)
    L = _LENS.get(k)
    if L is None or L.path is not path:
        if len(_LENS) > 20000:
            _LENS.clear()
        L = Lens(path)
        _LENS[k] = L
    return L


def ink(c, path, p=1.0, w=4.6, color=INK, alpha=1.0):
    if p <= 0 or alpha <= 0:
        return
    if p < 0.999:
        path = lens(path).partial(p)
    c.drawPath(path, _ink_paint(w, color, alpha))


def marker(c, path, p=1.0, color=TEAL, alpha=0.88, off=(6.0, 5.0), sweep=True):
    """Flat marker fill, nudged off the ink line, swept in left-to-right."""
    if p <= 0 or alpha <= 0:
        return
    c.save()
    c.translate(*off)
    if p < 0.999:
        b = path.getBounds()
        if sweep:
            x = b.left() + (b.width() + 40) * p
            clip = skia.Path()
            clip.moveTo(b.left() - 40, b.top() - 40)
            clip.lineTo(x + 30, b.top() - 40)
            clip.lineTo(x - 30, b.bottom() + 40)
            clip.lineTo(b.left() - 40, b.bottom() + 40)
            clip.close()
            c.clipPath(clip, skia.ClipOp.kIntersect, True)
        else:
            alpha *= p
    c.drawPath(path, skia.Paint(AntiAlias=True, Color=hexc(color, alpha), Style=skia.Paint.kFill_Style))
    c.restore()


def solid(c, path, color, alpha=1.0):
    c.drawPath(path, skia.Paint(AntiAlias=True, Color=hexc(color, alpha), Style=skia.Paint.kFill_Style))


def hatch(c, path, p=1.0, spacing=13.0, angle=-35.0, w=2.2, color=INK, alpha=0.55, seed=0):
    """Pen hatching clipped to a shape."""
    if p <= 0:
        return
    b = path.getBounds()
    c.save()
    c.clipPath(path, skia.ClipOp.kIntersect, True)
    cx, cy = b.centerX(), b.centerY()
    R = math.hypot(b.width(), b.height()) / 2 + 10
    a = math.radians(angle)
    dx, dy = math.cos(a), math.sin(a)
    nx, ny = -dy, dx
    k = -R
    lines = skia.Path()
    i = 0
    while k <= R:
        x0, y0 = cx + nx * k - dx * R, cy + ny * k - dy * R
        x1, y1 = cx + nx * k + dx * R, cy + ny * k + dy * R
        lines.addPath(wpath([(x0, y0), (x1, y1)], seed + i, amp=1.0))
        k += spacing
        i += 1
    ink(c, lines, p, w, color, alpha)
    c.restore()


def cross_out(c, cx, cy, r, p=1.0, w=9.0, color=CORAL, seed=3):
    a = wpath([(cx - r, cy - r), (cx + r, cy + r)], seed, 2.0)
    b = wpath([(cx + r, cy - r * 0.95), (cx - r * 0.95, cy + r)], seed + 1, 2.0)
    ink(c, a, clamp(p * 2), w, color)
    ink(c, b, clamp(p * 2 - 1), w, color)


def underline(c, x0, x1, y, p=1.0, w=5.0, color=INK, seed=5):
    ink(c, wpath([(x0, y), ((x0 + x1) / 2, y + 4), (x1, y - 2)], seed, 2.5), p, w, color)


def arrow(c, pts, p=1.0, w=4.6, color=INK, seed=9, head=20.0):
    path = wpath(pts, seed, 1.6)
    ink(c, path, p, w, color)
    if p > 0.85:
        (x0, y0), (x1, y1) = pts[-2], pts[-1]
        a = math.atan2(y1 - y0, x1 - x0)
        hp = skia.Path()
        hp.moveTo(x1 - head * math.cos(a - 0.45), y1 - head * math.sin(a - 0.45))
        hp.lineTo(x1, y1)
        hp.lineTo(x1 - head * math.cos(a + 0.45), y1 - head * math.sin(a + 0.45))
        ink(c, hp, clamp((p - 0.85) / 0.15), w, color)


# ---------------------------------------------------------------- page
_PAGE_PIC = {}


def _record_page(tint):
    rec = skia.PictureRecorder()
    c = rec.beginRecording(skia.Rect.MakeWH(W, H))
    c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Color=hexc(tint)))
    # gentle shadow toward the spiral binding and a soft edge darkening
    g = skia.Paint(AntiAlias=True)
    g.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(150, 0)],
                                               [hexc(PAGE_SH, 1.0), hexc(PAGE_SH, 0.0)]))
    c.drawRect(skia.Rect.MakeLTRB(0, 0, 150, H), g)
    g2 = skia.Paint(AntiAlias=True)
    g2.setShader(skia.GradientShader.MakeLinear([skia.Point(W, 0), skia.Point(W - 60, 0)],
                                                [hexc(PAGE_SH, 0.7), hexc(PAGE_SH, 0.0)]))
    c.drawRect(skia.Rect.MakeLTRB(W - 60, 0, W, H), g2)
    # spiral rings
    for k in range(30):
        y = 52 + k * 64
        c.drawCircle(46, y, 7.5, skia.Paint(AntiAlias=True, Color=hexc("#5c574f")))
        ring = skia.Path()
        ring.addArc(skia.Rect.MakeLTRB(6, y - 17, 54, y + 13), 150, 230)
        c.drawPath(ring, _ink_paint(5.0, "#8c877d", 1.0))
        c.drawPath(ring, _ink_paint(2.0, "#d8d2c6", 0.9))
    return rec.finishRecordingAsPicture()


def page(c, tint=PAGE):
    if tint not in _PAGE_PIC:
        _PAGE_PIC[tint] = _record_page(tint)
    c.drawPicture(_PAGE_PIC[tint])


def page_turn(c, t, dur=0.42, back=PAGE):
    """The previous (blank) sheet swings toward the binding, revealing this page."""
    u = t / dur
    if u >= 1 or u < 0:
        return
    th = (u * u * (3 - 2 * u)) * math.pi / 2
    x_r = 70 + (W - 70) * math.cos(th)
    lift = math.sin(th) * 60
    if x_r < 72:
        return
    # soft shadow cast onto the new page
    sh = skia.Paint(AntiAlias=True)
    sh.setShader(skia.GradientShader.MakeLinear([skia.Point(x_r, 0), skia.Point(x_r + 120, 0)],
                                                [hexc("#000000", 0.18), hexc("#000000", 0.0)]))
    c.drawRect(skia.Rect.MakeLTRB(x_r, 0, x_r + 120, H), sh)
    sheet = skia.Path()
    sheet.moveTo(70, 0)
    sheet.lineTo(x_r, -lift)
    sheet.lineTo(x_r, H + lift)
    sheet.lineTo(70, H)
    sheet.close()
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeLinear([skia.Point(70, 0), skia.Point(x_r, 0)],
                                               [hexc(back), hexc("#d9ccb0")]))
    c.drawPath(sheet, p)
    c.drawLine(x_r, -lift, x_r, H + lift, _ink_paint(2.0, "#b9ab8e", 0.8))


# ---------------------------------------------------------------- icons (local coords, ~100 unit size)
def icon_cuffs(c, x, y, s=1.0, p=1.0, seed=11):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    ink(c, wcircle(-34, 8, 26, seed), clamp(p * 2.5), 7)
    ink(c, wcircle(34, 8, 26, seed + 1), clamp(p * 2.5 - 0.6), 7)
    chain = skia.Path()
    for k in range(3):
        chain.addPath(wellipse(-12 + k * 12, -18, 7, 5, seed + 4 + k, amp=0.6))
    ink(c, chain, clamp(p * 2.5 - 1.3), 4.5)
    marker(c, wcircle(-34, 8, 22, seed + 9), clamp(p * 2 - 1), GREY, 0.7, (4, 3))
    marker(c, wcircle(34, 8, 22, seed + 10), clamp(p * 2 - 1), GREY, 0.7, (4, 3))
    c.restore()


def icon_cage(c, x, y, s=1.0, p=1.0, seed=21):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    ink(c, wpath([(-50, -60), (50, -60)], seed, 1.5), clamp(p * 3), 7)
    ink(c, wpath([(-50, 60), (50, 60)], seed + 1, 1.5), clamp(p * 3 - 0.3), 7)
    for k in range(5):
        xx = -50 + k * 25
        ink(c, wpath([(xx, -60), (xx, 60)], seed + 2 + k, 1.3), clamp(p * 3 - 0.8 - k * 0.25), 6)
    c.restore()


def icon_bubble(c, x, y, s=1.0, p=1.0, seed=31, color=TEAL, text=None, size=44, tail=-1):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    body = wellipse(0, 0, 70, 48, seed, amp=1.6)
    marker(c, body, clamp(p * 1.5 - 0.3), color, 0.8, (5, 4))
    ink(c, body, clamp(p * 1.5), 5)
    ink(c, wpath([(tail * 30, 40), (tail * 52, 78), (tail * 6, 46)], seed + 1, 1.0), clamp(p * 2 - 0.8), 5)
    if text:
        write(c, text, 0, size * 0.35, size, "caveat_b", clamp(p * 2 - 1))
    c.restore()


def icon_feet(c, x, y, s=1.0, p=1.0, seed=41):
    """Footsteps stepping back (toward the left)."""
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    steps = [(55, 40, 0.0), (20, 6, 1.0), (-15, 40, 2.0), (-50, 6, 3.0)]
    for i, (fx, fy, k) in enumerate(steps):
        q = clamp(p * 4 - k)
        if q <= 0:
            continue
        sole = wellipse(fx, fy, 13, 20, seed + i, amp=0.8)
        marker(c, sole, q, CORAL, 0.75, (3, 2), sweep=False)
        ink(c, sole, q, 4)
        for tt in range(3):
            ink(c, wcircle(fx - 7 + tt * 7, fy - 27, 3.6, seed + 20 + i * 3 + tt), q, 3.0)
    arrow(c, [(60, -40), (-60, -40)], clamp(p * 2 - 1), 4, INK, seed + 50, 14)
    c.restore()


def icon_door(c, x, y, s=1.0, p=1.0, ajar=1.0, seed=51, glow=True):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    frame = wrect(-48, -95, 48, 95, seed)
    if glow and ajar > 0:
        light = skia.Path()
        light.moveTo(-44, -90)
        light.lineTo(-44 + 88 * ajar * 0.6, -90)
        light.lineTo(-44 + 88 * ajar * 0.6 + 70 * ajar, 160)
        light.lineTo(-44 - 30 * ajar, 160)
        light.close()
        solid(c, light, WARM, 0.55 * clamp(p * 2 - 0.5))
        solid(c, wrect(-44, -90, 44, 91, seed + 3), WARM, 0.9 * clamp(p * 2 - 0.5))
    ink(c, frame, clamp(p * 2), 6)
    # door leaf swung open (perspective skew)
    w = 88 * (1 - 0.65 * ajar)
    leaf = wpath([(-48, -95), (-48 + w, -95 - 12 * ajar), (-48 + w, 95 + 12 * ajar), (-48, 95), (-48, -92)], seed + 1, 1.2)
    marker(c, leaf, clamp(p * 2 - 0.6), CORAL, 0.85, (4, 3))
    ink(c, leaf, clamp(p * 2 - 0.4), 5)
    c.drawCircle(-48 + w - 12, 5, 5, skia.Paint(AntiAlias=True, Color=hexc(INK, clamp(p * 2 - 1))))
    c.restore()


def icon_chair(c, x, y, s=1.0, p=1.0, seed=61, color=MUSTARD):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    seat = wpath([(-26, 0), (26, 0), (30, 12), (-30, 12), (-26, 1)], seed, 0.8)
    marker(c, seat, p, color, 0.85, (3, 2))
    ink(c, seat, p, 4)
    ink(c, wpath([(-24, 12), (-26, 46)], seed + 1, 0.6), p, 4)
    ink(c, wpath([(24, 12), (26, 46)], seed + 2, 0.6), p, 4)
    ink(c, wpath([(-24, 0), (-26, -44), (24, -44), (24, 0)], seed + 3, 0.8), p, 4)
    c.restore()


def icon_coin(c, x, y, s=1.0, p=1.0, seed=71):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    body = wcircle(0, 0, 20, seed)
    marker(c, wcircle(0, 0, 18, seed + 1), p, MUSTARD, 0.95, (2, 2), sweep=False)
    ink(c, body, p, 3.6)
    write(c, "$", 0, 10, 28, "caveat_b", p)
    c.restore()


def icon_house(c, x, y, s=1.0, p=1.0, seed=81, color=CORAL):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    body = wpath([(-50, -10), (0, -60), (50, -10), (40, -10), (40, 50), (-40, 50), (-40, -10), (-50, -10)], seed, 1.2)
    marker(c, wrect(-38, -8, 38, 48, seed + 2), clamp(p * 2 - 0.5), color, 0.8, (3, 3))
    ink(c, body, clamp(p * 1.5), 5)
    solid(c, wrect(-10, 15, 10, 48, seed + 3), MUSTARD, clamp(p * 2 - 1))
    ink(c, wrect(-10, 15, 10, 48, seed + 3), clamp(p * 2 - 1), 3.5)
    c.restore()


def icon_clinic(c, x, y, s=1.0, p=1.0, seed=91):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    box = wrect(-46, -44, 46, 48, seed)
    marker(c, wrect(-44, -42, 44, 46, seed + 1), clamp(p * 2 - 0.4), "#ffffff", 0.9, (3, 3))
    ink(c, box, clamp(p * 1.6), 5)
    cr = skia.Path()
    cr.addRect(skia.Rect.MakeLTRB(-9, -28, 9, 30))
    cr.addRect(skia.Rect.MakeLTRB(-28, -9, 28, 9))
    solid(c, cr, CORAL, clamp(p * 2 - 1))
    c.restore()


def icon_heart(c, x, y, s=1.0, p=1.0, seed=101, color=CORAL):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    pts = []
    for k in range(40):
        a = k / 39 * 2 * math.pi
        hx = 16 * math.sin(a) ** 3
        hy = -(13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a))
        pts.append((hx * 3, hy * 3))
    hp = wpath(pts, seed, 1.0, closed=True)
    marker(c, hp, clamp(p * 2 - 0.5), color, 0.9, (3, 3))
    ink(c, hp, clamp(p * 1.5), 5)
    c.restore()


def icon_clock(c, x, y, s=1.0, p=1.0, seed=111, t=0.0):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    marker(c, wcircle(0, 0, 38, seed + 1), clamp(p * 2 - 0.6), "#ffffff", 0.9, (3, 3))
    ink(c, wcircle(0, 0, 40, seed), clamp(p * 1.5), 5)
    a = t * 1.6
    ink(c, wpath([(0, 0), (math.sin(a) * 28, -math.cos(a) * 28)], seed + 2, 0.5), clamp(p * 2 - 1), 4.5)
    ink(c, wpath([(0, 0), (16, 8)], seed + 3, 0.5), clamp(p * 2 - 1), 4.5)
    c.restore()


def icon_pills(c, x, y, s=1.0, p=1.0, seed=121):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    body = wrect(-22, -20, 22, 42, seed)
    marker(c, body, clamp(p * 2 - 0.5), MUSTARD, 0.85, (3, 3))
    ink(c, body, clamp(p * 1.5), 4.5)
    lid = wrect(-26, -38, 26, -20, seed + 1)
    marker(c, lid, clamp(p * 2 - 0.5), "#ffffff", 0.9, (2, 2))
    ink(c, lid, clamp(p * 1.5), 4.5)
    c.restore()


def icon_bottle(c, x, y, s=1.0, p=1.0, seed=131, ang=0.0):
    c.save()
    c.translate(x, y)
    c.rotate(ang)
    c.scale(s, s)
    body = wpath([(-8, -60), (8, -60), (8, -38), (16, -26), (16, 30), (-16, 30), (-16, -26), (-8, -38), (-8, -58)],
                 seed, 0.8)
    marker(c, body, p, GREEN, 0.8, (3, 2))
    ink(c, body, p, 4.5)
    c.restore()


def icon_phone(c, x, y, s=1.0, p=1.0, seed=141, color=BLUE):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    body = wrect(-16, -28, 16, 28, seed)
    marker(c, wrect(-12, -22, 12, 18, seed + 1), clamp(p * 2 - 0.5), color, 0.85, (1, 1))
    ink(c, body, clamp(p * 1.5), 4)
    c.restore()


def icon_scale_pan(c, x, y, s, p, seed):
    pan = wpath([(-70, 0), (-50, 34), (50, 34), (70, 0), (-70, 0)], seed, 1.0)
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    marker(c, pan, clamp(p * 2 - 0.5), LGREY, 0.8, (3, 3))
    ink(c, pan, clamp(p * 1.5), 5)
    c.restore()


def icon_gavel(c, x, y, s=1.0, p=1.0, seed=151):
    c.save()
    c.translate(x, y)
    c.rotate(-30)
    c.scale(s, s)
    head = wrect(-34, -16, 34, 16, seed)
    marker(c, head, clamp(p * 2 - 0.5), "#b08a62", 0.9, (3, 3))
    ink(c, head, clamp(p * 1.5), 5)
    handle = wrect(-6, 16, 6, 80, seed + 1)
    marker(c, handle, clamp(p * 2 - 0.5), "#b08a62", 0.9, (2, 2))
    ink(c, handle, clamp(p * 1.5), 4.5)
    c.restore()


def icon_mug(c, x, y, s=1.0, p=1.0, seed=171, color="#f6f2ea", steam=0.0, t=0.0):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    body = wpath([(-26, -30), (26, -30), (22, 30), (-22, 30), (-26, -28)], seed, 0.8)
    marker(c, body, clamp(p * 2 - 0.5), color, 0.95, (2, 2))
    ink(c, body, clamp(p * 1.5), 4.5)
    hd = skia.Path()
    hd.addArc(skia.Rect.MakeLTRB(16, -18, 44, 14), -80, 170)
    ink(c, hd, clamp(p * 2 - 1), 4.5)
    if steam > 0:
        for k in range(2):
            ph = t * 0.8 + k * 0.5
            fr = ph - math.floor(ph)
            pts = [(-8 + k * 14 + math.sin(j * 1.1 + k + t * 2) * 5, -40 - j * 10 - fr * 14) for j in range(5)]
            ink(c, smooth_path(np.array(pts)), 1.0, 3.0, GREY, steam * math.sin(fr * math.pi))
    c.restore()


def icon_tank(c, x, y, s=1.0, p=1.0, seed=181, t=0.0, moving=True):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    hull = wpath([(-110, 0), (110, 0), (92, 34), (-92, 34), (-110, 2)], seed, 1.2)
    turret = wpath([(-50, 0), (-40, -38), (36, -38), (48, 0)], seed + 1, 1.2)
    barrel = wpath([(36, -24), (130, -30)], seed + 2, 1.0)
    marker(c, hull, clamp(p * 2 - 0.5), OLIVE, 0.85, (4, 3))
    marker(c, turret, clamp(p * 2 - 0.5), OLIVE, 0.85, (4, 3))
    ink(c, hull, clamp(p * 1.5), 5.5)
    ink(c, turret, clamp(p * 1.5 - 0.2), 5.5)
    ink(c, barrel, clamp(p * 1.5 - 0.4), 9)
    for k in range(6):
        wx = -80 + k * 32
        rot = (t * 3.0 if moving else 0.0) + k
        ink(c, wcircle(wx, 34, 13, seed + 10 + k), clamp(p * 2 - 0.8), 4)
        ink(c, wpath([(wx, 34), (wx + math.cos(rot) * 10, 34 + math.sin(rot) * 10)], seed + 20 + k, 0.3),
            clamp(p * 2 - 1), 3)
    c.restore()


def icon_car(c, x, y, s=1.0, p=1.0, seed=191, color=BLUE, lightbar=False, flip=False):
    c.save()
    c.translate(x, y)
    c.scale(-s if flip else s, s)
    body = wpath([(-110, 0), (-104, -30), (-60, -36), (-36, -70), (40, -70), (66, -36), (108, -30), (114, 0),
                  (-110, 0)], seed, 1.3)
    marker(c, body, clamp(p * 2 - 0.5), color, 0.85, (4, 3))
    ink(c, body, clamp(p * 1.5), 5)
    ink(c, wpath([(-28, -64), (-28, -36)], seed + 1, 0.6), clamp(p * 2 - 1), 4)
    ink(c, wpath([(14, -66), (14, -36)], seed + 2, 0.6), clamp(p * 2 - 1), 4)
    for wx in (-64, 64):
        solid(c, wcircle(wx, 4, 20, seed + 3), "#3a3a40", clamp(p * 2 - 1))
        ink(c, wcircle(wx, 4, 20, seed + 4), clamp(p * 2 - 1), 4)
    if lightbar:
        bar = wrect(-22, -84, 22, -70, seed + 5)
        solid(c, wrect(-20, -82, 0, -72, seed + 6), "#d9534f", clamp(p * 2 - 1))
        solid(c, wrect(0, -82, 20, -72, seed + 7), BLUE, clamp(p * 2 - 1))
        ink(c, bar, clamp(p * 2 - 1), 4)
    c.restore()


def _bez(p0, p1, p2, n=10):
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2 = map(np.asarray, (p0, p1, p2))
    return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2


def figure(c, x, y, s=1.0, p=1.0, seed=0, skin=SKIN[0], outfit=TEAL, hair="short", hair_col=INK,
           face="neutral", arms=((-0.55, 0.85), (0.55, 0.85)), legs="stand", lean=0.0, tilt=0.0,
           apron=False, badge=False, hat=None, scribble=0.0, look=(0.0, 0.0), flip=False, hands="dot",
           alpha=1.0, step=0.0):
    """Simple expressive sketch person. (x, y) = point between the feet; height ~ 270*s.

    arms: hand positions relative to each shoulder, in arm-lengths (x right, y down).
    legs: "stand" | "walk" | "sit" | "floor" | "kneel".
    """
    if p <= 0 or alpha <= 0:
        return
    c.save()
    c.translate(x, y)
    c.scale(-s if flip else s, s)
    c.rotate(math.degrees(lean) * 0.6)
    hip_y = -112
    if legs == "sit":
        hip_y = -78
    elif legs == "floor":
        hip_y = -34
    elif legs == "kneel":
        hip_y = -70
    sh_y = hip_y - 92
    head_cy = sh_y - 40
    R = 34

    def ph(a, b):
        return clamp((p - a) / (b - a))

    # legs
    lp = ph(0.55, 0.85)
    if lp > 0:
        if legs == "stand":
            L = [((-14, hip_y), (-20, hip_y * 0.5), (-22 - step * 18, 0)),
                 ((14, hip_y), (20, hip_y * 0.5), (22 + step * 18, 0))]
        elif legs == "walk":
            L = [((-12, hip_y), (-30, hip_y * 0.45), (-44, 0)), ((12, hip_y), (24, hip_y * 0.5), (36, -4))]
        elif legs == "sit":
            L = [((-12, hip_y), (40, hip_y + 4), (44, 0)), ((12, hip_y), (60, hip_y + 4), (64, 0))]
        elif legs == "floor":
            L = [((-16, hip_y), (40, hip_y + 30), (-30, -6)), ((16, hip_y), (-40, hip_y + 30), (30, -6))]
        else:  # kneel
            L = [((-12, hip_y), (-10, -24), (-50, -4)), ((12, hip_y), (20, -30), (40, 0))]
        for i, (a, b, d) in enumerate(L):
            pts = _bez(a, b, d, 8)
            ink(c, wpath(pts, seed + 30 + i, 1.0), lp, 6.5, INK, alpha)
            if lp > 0.9 and legs in ("stand", "walk", "sit"):
                fdir = 1 if i == 1 or legs == "sit" else -1
                ink(c, wpath([(d[0], d[1]), (d[0] + fdir * 16, d[1] + 1)], seed + 36 + i, 0.4),
                    (lp - 0.9) / 0.1, 6.5, INK, alpha)
    # torso
    tp = ph(0.3, 0.6)
    torso_pts = [(-30, sh_y + 4), (-36, sh_y + 30), (-30, hip_y), (30, hip_y), (36, sh_y + 30), (30, sh_y + 4),
                 (0, sh_y - 4), (-30, sh_y + 4)]
    torso = wpath(torso_pts, seed + 1, 1.2)
    if tp > 0:
        marker(c, torso, tp, outfit, 0.9 * alpha, (4, 3))
        if apron:
            ap = wpath([(-22, sh_y + 28), (22, sh_y + 28), (26, hip_y + 18), (-26, hip_y + 18), (-22, sh_y + 30)],
                       seed + 2, 1.0)
            marker(c, ap, tp, GREEN, 0.92 * alpha, (3, 2))
            ink(c, ap, tp, 3.5, INK, alpha)
            ink(c, wpath([(-14, sh_y + 28), (-8, sh_y)], seed + 3, 0.5), tp, 3, INK, alpha)
            ink(c, wpath([(14, sh_y + 28), (8, sh_y)], seed + 4, 0.5), tp, 3, INK, alpha)
        if badge:
            solid(c, wcircle(-14, sh_y + 22, 6, seed + 5), MUSTARD, alpha * tp)
        ink(c, torso, tp, 5.5, INK, alpha)
        if scribble > 0:
            hatch(c, torso, tp * scribble, 10, -40, 2.4, INK, 0.65 * alpha, seed + 6)
    # arms
    ap_ = ph(0.45, 0.75)
    if ap_ > 0:
        for i, (side, hand) in enumerate(zip((-1, 1), arms)):
            shx, shy = side * 30, sh_y + 10
            hx, hy = shx + hand[0] * 88, shy + hand[1] * 88
            mx, my = (shx + hx) / 2 + side * 14, (shy + hy) / 2 + 8
            pts = _bez((shx, shy), (mx, my), (hx, hy), 8)
            ink(c, wpath(pts, seed + 40 + i, 0.9), ap_, 6.5, INK, alpha)
            if ap_ > 0.8:
                hp_ = (ap_ - 0.8) / 0.2
                if hands == "open":
                    hand_p = wcircle(hx, hy, 9, seed + 45 + i)
                    solid(c, hand_p, skin, alpha * hp_)
                    ink(c, hand_p, hp_, 3.5, INK, alpha)
                    for f in range(3):
                        a = math.atan2(hy - shy, hx - shx) + (f - 1) * 0.45
                        ink(c, wpath([(hx + math.cos(a) * 8, hy + math.sin(a) * 8),
                                      (hx + math.cos(a) * 17, hy + math.sin(a) * 17)], seed + 50 + f, 0.3),
                            hp_, 3.0, INK, alpha)
                else:
                    hand_p = wcircle(hx, hy, 8, seed + 45 + i)
                    solid(c, hand_p, skin, alpha * hp_)
                    ink(c, hand_p, hp_, 3.5, INK, alpha)
    # head
    hp = ph(0.0, 0.3)
    c.save()
    c.translate(0, head_cy)
    c.rotate(math.degrees(tilt))
    head = wcircle(0, 0, R, seed + 7)
    if hp > 0:
        if hair in ("long",):
            back = wpath([(-34, -6), (-40, 40), (-26, 58), (26, 58), (40, 40), (34, -6)], seed + 8, 1.0)
            solid(c, back, hair_col, alpha * hp)
        solid(c, head, skin, alpha * hp)
        ink(c, head, hp, 5, INK, alpha)
    hrp = ph(0.25, 0.4)
    if hrp > 0:
        _hair(c, hair, hair_col, seed, hrp, alpha, R)
        if hat == "cap":
            capp = wpath([(-34, -18), (-30, -46), (30, -46), (34, -18), (48, -14), (-34, -16)], seed + 9, 1.0)
            solid(c, capp, NAVY, alpha * hrp)
            ink(c, capp, hrp, 4.5, INK, alpha)
            solid(c, wcircle(0, -36, 5, seed + 10), MUSTARD, alpha * hrp)
        elif hat == "helmet":
            hel = wpath([(-38, -6), (-34, -36), (0, -50), (34, -36), (38, -6), (-38, -6)], seed + 9, 1.2)
            solid(c, hel, OLIVE, alpha * hrp)
            ink(c, hel, hrp, 4.5, INK, alpha)
    fp = ph(0.85, 1.0)
    if fp > 0:
        _face(c, face, fp, alpha, seed, look)
    c.restore()
    c.restore()


def _hair(c, style, col, seed, p, alpha, R):
    if style == "curls":
        rng = np.random.default_rng(seed + 300)
        for k in range(11):
            a = math.radians(-205 + k * 23)
            cx, cy = math.cos(a) * (R + 2), math.sin(a) * (R + 2) - 4
            r = 9 + rng.uniform(-1.5, 2.0)
            loop = wcircle(cx, cy, r, seed + 310 + k, amp=0.6)
            grey = k % 3 == 1
            solid(c, loop, "#b9b6b3" if grey else "#2e2826", alpha * p)
            ink(c, loop, p, 3.0, INK, alpha)
    elif style == "twists":
        for k in range(8):
            a = math.radians(-160 + k * 20)
            bx, by = math.cos(a) * (R - 2), math.sin(a) * (R - 2)
            tx, ty = math.cos(a) * (R + 18), math.sin(a) * (R + 18) - 6
            ink(c, wpath([(bx, by), (tx, ty)], seed + 320 + k, 0.8), p, 9.0, "#2b211e", alpha)
        cap = wpath([(-R, -6), (-R * 0.7, -R * 0.8), (0, -R - 4), (R * 0.7, -R * 0.8), (R, -6)], seed + 330, 0.8)
        ink(c, cap, p, 6.0, "#2b211e", alpha)
    elif style == "short":
        capp = wpath([(-R - 2, 0), (-R * 0.8, -R * 0.75), (0, -R - 6), (R * 0.8, -R * 0.75), (R + 2, 0),
                      (R * 0.5, -R * 0.45), (-R * 0.5, -R * 0.4), (-R - 2, 2)], seed + 340, 1.0)
        solid(c, capp, col, alpha * p)
        ink(c, capp, p, 3.5, INK, alpha)
    elif style == "long":
        capp = wpath([(-R - 4, 8), (-R * 0.9, -R * 0.7), (0, -R - 6), (R * 0.9, -R * 0.7), (R + 4, 8),
                      (R * 0.4, -R * 0.5), (-R * 0.4, -R * 0.5), (-R - 4, 10)], seed + 350, 1.0)
        solid(c, capp, col, alpha * p)
        ink(c, capp, p, 3.5, INK, alpha)
    elif style == "bun":
        solid(c, wcircle(0, -R - 10, 13, seed + 360), col, alpha * p)
        ink(c, wcircle(0, -R - 10, 13, seed + 361), p, 3.5, INK, alpha)
        capp = wpath([(-R - 1, -2), (-R * 0.8, -R * 0.75), (0, -R - 3), (R * 0.8, -R * 0.75), (R + 1, -2),
                      (0, -R * 0.5), (-R - 1, 0)], seed + 362, 0.8)
        solid(c, capp, col, alpha * p)


def _face(c, face, p, alpha, seed, look):
    a = alpha * p
    lx, ly = look
    ex = 12
    ey = -2
    if face in ("closed", "pained", "peace"):
        for sx in (-1, 1):
            if face == "pained":
                ink(c, wpath([(sx * ex - 7, ey - 3), (sx * ex, ey + 2), (sx * ex + 7, ey - 3)], seed + 400 + sx, 0.3),
                    1.0, 3.2, INK, a)
            else:
                ink(c, wpath([(sx * ex - 7, ey), (sx * ex, ey + 4), (sx * ex + 7, ey)], seed + 400 + sx, 0.3),
                    1.0, 3.2, INK, a)
    else:
        for sx in (-1, 1):
            c.drawCircle(sx * ex + lx * 3, ey + ly * 3, 3.6, skia.Paint(AntiAlias=True, Color=hexc(INK, a)))
    if face == "sad":
        for sx in (-1, 1):
            ink(c, wpath([(sx * (ex + 7), ey - 11), (sx * (ex - 6), ey - 15)], seed + 410 + sx, 0.3), 1.0, 3, INK, a)
        ink(c, wpath([(-8, 18), (0, 14), (8, 18)], seed + 420, 0.3), 1.0, 3.2, INK, a)
    elif face == "happy":
        ink(c, wpath([(-10, 12), (0, 20), (10, 12)], seed + 421, 0.3), 1.0, 3.4, INK, a)
    elif face == "angry":
        for sx in (-1, 1):
            ink(c, wpath([(sx * (ex + 7), ey - 15), (sx * (ex - 6), ey - 9)], seed + 430 + sx, 0.3), 1.0, 3.4, INK, a)
        ink(c, wpath([(-9, 17), (9, 17)], seed + 431, 0.4), 1.0, 3.4, INK, a)
    elif face == "shout":
        solid(c, wellipse(0, 16, 8, 7, seed + 432, amp=0.4), INK, a)
        for sx in (-1, 1):
            ink(c, wpath([(sx * (ex + 7), ey - 13), (sx * (ex - 6), ey - 9)], seed + 433 + sx, 0.3), 1.0, 3.2, INK, a)
    elif face == "scared":
        ink(c, wellipse(0, 17, 6, 5, seed + 440, amp=0.3), 1.0, 3.2, INK, a)
        for sx in (-1, 1):
            ink(c, wpath([(sx * (ex + 6), ey - 12), (sx * (ex - 5), ey - 16)], seed + 441 + sx, 0.3), 1.0, 3, INK, a)
    elif face == "pained":
        ink(c, wpath([(-9, 18), (0, 15), (9, 18)], seed + 450, 0.3), 1.0, 3.2, INK, a)
        ink(c, wpath([(16, 4), (17, 14)], seed + 451, 0.3), 1.0, 2.6, COLD, a)
    elif face == "peace":
        ink(c, wpath([(-8, 13), (0, 18), (8, 13)], seed + 452, 0.3), 1.0, 3.2, INK, a)
    elif face == "neutral":
        ink(c, wpath([(-7, 16), (7, 16)], seed + 453, 0.3), 1.0, 3.0, INK, a)
    elif face == "talk":
        ink(c, wellipse(0, 16, 7, 4, seed + 454, amp=0.3), 1.0, 3.0, INK, a)
    elif face == "closed":
        ink(c, wpath([(-7, 16), (7, 16)], seed + 455, 0.3), 1.0, 3.0, INK, a)


# ---------------------------------------------------------------- the cast in sketch form
def hale(c, x, y, s=1.0, p=1.0, seed=500, **kw):
    kw.setdefault("hair", "curls")
    figure(c, x, y, s, p, seed, skin=SKIN[3], outfit=NAVY, badge=True, **kw)


def kai(c, x, y, s=1.0, p=1.0, seed=600, **kw):
    kw.setdefault("hair", "twists")
    figure(c, x, y, s, p, seed, skin=SKIN[1], outfit=HOODIE, apron=True, **kw)


def hand_pos(x, y, s, side, hand, legs="stand", flip=False):
    """World position of a figure's hand (side -1 = left arm, +1 = right arm as drawn)."""
    hip_y = {"sit": -78, "floor": -34, "kneel": -70}.get(legs, -112)
    sh_y = hip_y - 92
    lx = side * 30 + hand[0] * 88
    ly = sh_y + 10 + hand[1] * 88
    return x + (-lx if flip else lx) * s, y + ly * s


def head_pos(x, y, s, legs="stand"):
    hip_y = {"sit": -78, "floor": -34, "kneel": -70}.get(legs, -112)
    return x, y + (hip_y - 132) * s


def spark(c, x, y, r=22, p=1.0, color=MUSTARD, seed=900):
    for k in range(5):
        a = math.radians(-90 + k * 45 - 90)
        ink(c, wpath([(x + math.cos(a) * r * 0.55, y + math.sin(a) * r * 0.55),
                      (x + math.cos(a) * r * 1.2, y + math.sin(a) * r * 1.2)], seed + k, 0.4),
            p, 4.0, color)


def alpha_layer(c, a, bounds=None):
    """Begin a translucent layer (pair with c.restore()); bounds (l, t, r, b) keeps it small."""
    rect = skia.Rect.MakeLTRB(*bounds) if bounds else None
    c.saveLayerAlpha(rect, int(255 * clamp(a)))


def turn_to(c, t, t0, old_fn, new_fn, dur=0.5, tint_old=PAGE, tint_new=PAGE):
    """Mid-scene page turn: the old page swings toward the binding, revealing the new one."""
    if t < t0:
        page(c, tint_old)
        old_fn(c)
        return
    page(c, tint_new)
    new_fn(c)
    u = (t - t0) / dur
    if u >= 1:
        return
    e = u * u * (3 - 2 * u)
    th = e * math.pi / 2
    x_r = 70 + (W - 70) * math.cos(th)
    if x_r < 74:
        return
    lift = math.sin(th) * 60
    sh = skia.Paint(AntiAlias=True)
    sh.setShader(skia.GradientShader.MakeLinear([skia.Point(x_r, 0), skia.Point(x_r + 140, 0)],
                                                [hexc("#000000", 0.2), hexc("#000000", 0.0)]))
    c.drawRect(skia.Rect.MakeLTRB(x_r, 0, x_r + 140, H), sh)
    sheet = skia.Path()
    sheet.moveTo(70, 0)
    sheet.lineTo(x_r, -lift)
    sheet.lineTo(x_r, H + lift)
    sheet.lineTo(70, H)
    sheet.close()
    c.save()
    c.clipPath(sheet, skia.ClipOp.kIntersect, True)
    c.translate(70, 0)
    c.scale((x_r - 70) / (W - 70), 1.0)
    c.translate(-70, 0)
    page(c, tint_old)
    old_fn(c)
    c.restore()
    shade = skia.Paint(AntiAlias=True)
    shade.setShader(skia.GradientShader.MakeLinear([skia.Point(70, 0), skia.Point(x_r, 0)],
                                                   [hexc("#000000", 0.0), hexc("#000000", 0.28 * e)]))
    c.drawPath(sheet, shade)
    c.drawLine(x_r, -lift, x_r, H + lift, _ink_paint(2.0, "#b9ab8e", 0.8))


def check(c, x, y, s=1.0, p=1.0, color=TEAL, seed=970):
    """A hand-drawn tick mark centred near (x, y)."""
    ink(c, wpath([(x - 22 * s, y), (x - 6 * s, y + 18 * s), (x + 26 * s, y - 26 * s)], seed, 0.6), p, 9 * s, color)
