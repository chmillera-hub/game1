"""Shared drawing helpers, easing, noise and timeline access."""
import json, math, os, random
import numpy as np
import skia

W, H, FPS = 1080, 1920, 30
BUILD = os.environ.get("BUILD", "build")

# ---------------------------------------------------------------- math

def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    return a + (b - a) * t


def lerp2(p, q, t):
    return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)


def prog(t, t0, t1):
    """0..1 progress of t through [t0, t1]."""
    if t1 <= t0:
        return 1.0 if t >= t1 else 0.0
    return clamp((t - t0) / (t1 - t0))


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_io(x):
    x = clamp(x)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in(x):
    x = clamp(x)
    return x ** 3


def ease_back(x, s=1.70158):
    x = clamp(x)
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


def ease_elastic(x):
    x = clamp(x)
    if x in (0, 1):
        return x
    return 2 ** (-10 * x) * math.sin((x * 10 - 0.75) * (2 * math.pi) / 3) + 1


def pulse(t, t0, rise=0.15, hold=0.0, fall=0.3):
    """0 -> 1 -> 0 envelope starting at t0."""
    if t < t0:
        return 0.0
    if t < t0 + rise:
        return smooth((t - t0) / rise)
    if t < t0 + rise + hold:
        return 1.0
    return 1 - smooth((t - t0 - rise - hold) / fall)


_perm = list(range(256))
random.Random(7).shuffle(_perm)
_grad = [random.Random(i * 31 + 5).uniform(-1, 1) for i in range(256)]


def noise1(x, seed=0):
    """Smooth 1D gradient noise, roughly in [-1, 1]."""
    i = math.floor(x)
    f = x - i
    a = _grad[_perm[(i + seed * 17) & 255]]
    b = _grad[_perm[(i + 1 + seed * 17) & 255]]
    u = f * f * (3 - 2 * f)
    return 2.2 * lerp(a * f, b * (f - 1), u)


# ---------------------------------------------------------------- color / paint

def hexc(h):
    if isinstance(h, tuple):
        return h
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(c1, c2, t):
    c1, c2 = hexc(c1), hexc(c2)
    return tuple(int(round(lerp(a, b, clamp(t)))) for a, b in zip(c1, c2))


def shade(c, k):
    """k<0 darker, k>0 lighter."""
    c = hexc(c)
    return mix(c, (0, 0, 0), -k) if k < 0 else mix(c, (255, 255, 255), k)


def argb(c, a=1.0):
    c = hexc(c)
    return skia.ColorSetARGB(int(clamp(a) * 255), c[0], c[1], c[2])


def paint(c, a=1.0, stroke=None, blur=None, shader=None, cap="round"):
    p = skia.Paint(AntiAlias=True)
    p.setColor(argb(c, a))
    if stroke is not None:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap(skia.Paint.kRound_Cap if cap == "round" else skia.Paint.kButt_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if shader is not None:
        p.setShader(shader)
        p.setAlphaf(clamp(a))
    return p


def lin_grad(p0, p1, colors, stops=None):
    return skia.GradientShader.MakeLinear(
        [skia.Point(*p0), skia.Point(*p1)], [argb(c, a) for c, a in colors], stops)


def rad_grad(center, r, colors, stops=None):
    return skia.GradientShader.MakeRadial(
        skia.Point(*center), r, [argb(c, a) for c, a in colors], stops)


# ---------------------------------------------------------------- shapes

def ellipse(cv, x, y, rx, ry, p):
    cv.drawOval(skia.Rect.MakeLTRB(x - rx, y - ry, x + rx, y + ry), p)


def circle(cv, x, y, r, p):
    cv.drawCircle(x, y, r, p)


def rrect(cv, x, y, w, h, r, p):
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r), p)


def rect(cv, x, y, w, h, p):
    cv.drawRect(skia.Rect.MakeXYWH(x, y, w, h), p)


def line(cv, x0, y0, x1, y1, p):
    cv.drawLine(x0, y0, x1, y1, p)


def poly(pts, close=True):
    path = skia.Path()
    path.moveTo(*pts[0])
    for q in pts[1:]:
        path.lineTo(*q)
    if close:
        path.close()
    return path


def smooth_path(pts, close=True, tension=0.5):
    """Catmull-Rom spline through points as a cubic path."""
    n = len(pts)
    path = skia.Path()
    path.moveTo(*pts[0])
    rng = range(n) if close else range(n - 1)
    for i in rng:
        p0 = pts[(i - 1) % n] if (close or i > 0) else pts[i]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if (close or i + 2 < n) else p2
        k = tension / 3 * 2
        c1 = (p1[0] + (p2[0] - p0[0]) * k / 2, p1[1] + (p2[1] - p0[1]) * k / 2)
        c2 = (p2[0] - (p3[0] - p1[0]) * k / 2, p2[1] - (p3[1] - p1[1]) * k / 2)
        path.cubicTo(*c1, *c2, *p2)
    if close:
        path.close()
    return path


def quad_path(p0, c, p1):
    path = skia.Path()
    path.moveTo(*p0)
    path.quadTo(*c, *p1)
    return path


# ---------------------------------------------------------------- text

FONT_DIR = "/usr/share/fonts/opentype/inter"
_tf = {}


def typeface(name):
    if name not in _tf:
        paths = {
            "black": f"{FONT_DIR}/Inter-Black.otf",
            "xbold": f"{FONT_DIR}/Inter-ExtraBold.otf",
            "bold": f"{FONT_DIR}/Inter-Bold.otf",
            "semi": f"{FONT_DIR}/Inter-SemiBold.otf",
            "medium": f"{FONT_DIR}/Inter-Medium.otf",
            "regular": f"{FONT_DIR}/Inter-Regular.otf",
            "serif_i": "/usr/share/fonts/truetype/crosextra/Caladea-Italic.ttf",
            "serif_bi": "/usr/share/fonts/truetype/crosextra/Caladea-BoldItalic.ttf",
            "serif": "/usr/share/fonts/truetype/crosextra/Caladea-Regular.ttf",
            "serif_b": "/usr/share/fonts/truetype/crosextra/Caladea-Bold.ttf",
            "mono": "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
            "hand": "/usr/share/fonts/truetype/crosextra/Carlito-BoldItalic.ttf",
        }
        _tf[name] = skia.Typeface.MakeFromFile(paths[name])
    return _tf[name]


_fonts = {}


def font(name, size):
    key = (name, round(size, 1))
    if key not in _fonts:
        f = skia.Font(typeface(name), size)
        f.setEdging(skia.Font.Edging.kAntiAlias)
        f.setSubpixel(True)
        _fonts[key] = f
    return _fonts[key]


def text_w(s, f):
    return f.measureText(s)


def text(cv, s, x, y, f, p, align="left"):
    w = f.measureText(s)
    if align == "center":
        x -= w / 2
    elif align == "right":
        x -= w
    cv.drawString(s, x, y, f, p)
    return w


def text_outlined(cv, s, x, y, f, fill, outline=(0, 0, 0), ow=8, a=1.0, align="center"):
    text(cv, s, x, y, f, paint(outline, a, stroke=ow), align)
    text(cv, s, x, y, f, paint(fill, a), align)


# ---------------------------------------------------------------- timeline

class Timeline:
    def __init__(self, path=None):
        d = json.load(open(path or f"{BUILD}/timeline.json"))
        self.total = d["total"]
        self.lines = d["lines"]
        self.by_id = {L["id"]: L for L in self.lines}
        self.spoken = [L for L in self.lines if L["who"]]

    def s(self, lid):
        return self.by_id[lid]["start"]

    def e(self, lid):
        return self.by_id[lid]["end"]

    def w(self, lid, k, end=False):
        L = self.by_id[lid]
        wd = L["words"][k]
        return L["start"] + (wd[2] if end else wd[1])

    def wfind(self, lid, word, nth=0, end=False):
        L = self.by_id[lid]
        hits = [i for i, wd in enumerate(L["words"]) if word.lower() in wd[0].lower()]
        return self.w(lid, hits[nth], end)

    def speaking(self, who, t):
        for L in self.spoken:
            if L["who"] == who and L["start"] - 0.05 <= t <= L["end"] + 0.05:
                return L
        return None

    def current(self, t):
        """Line being spoken at t (or None)."""
        for L in self.spoken:
            if L["start"] <= t <= L["end"]:
                return L
        return None

    def last_speaker(self, t):
        best = None
        for L in self.spoken:
            if L["start"] <= t:
                best = L
        return best

    def mouth(self, who, t):
        L = self.speaking(who, t)
        if not L:
            return 0.0
        env = L["env"]
        x = (t - L["start"]) * FPS
        i = int(x)
        if i < 0 or i >= len(env):
            return 0.0
        a = env[i]
        b = env[i + 1] if i + 1 < len(env) else 0.0
        v = lerp(a, b, x - i)
        return clamp((v - 0.08) * 1.25)


class Keys:
    """Piecewise keyframes: list of (t, value) with eased transitions."""

    def __init__(self, keys, dur=0.3, ease=smooth):
        self.keys = sorted(keys, key=lambda k: k[0])
        self.dur = dur
        self.ease = ease

    def __call__(self, t):
        ks = self.keys
        if t <= ks[0][0]:
            return ks[0][1]
        prev = ks[0]
        for k in ks[1:]:
            if t < k[0]:
                break
            prev = k
        else:
            return ks[-1][1] if t >= ks[-1][0] + self._d(ks[-1]) else self._blend(ks, len(ks) - 1, t)
        i = ks.index(prev)
        return self._blend(ks, i, t)

    def _d(self, k):
        return k[2] if len(k) > 2 else self.dur

    def _blend(self, ks, i, t):
        if i == 0:
            return ks[0][1]
        k = ks[i]
        d = self._d(k)
        u = self.ease(prog(t, k[0], k[0] + d))
        prev_val = self._value_at(ks, i - 1, k[0])
        return blend_val(prev_val, k[1], u)

    def _value_at(self, ks, i, t):
        if i == 0:
            return ks[0][1]
        return self._blend(ks, i, t)


def blend_val(a, b, u):
    if isinstance(a, (int, float)):
        return lerp(a, b, u)
    if isinstance(a, (tuple, list)):
        return tuple(blend_val(x, y, u) for x, y in zip(a, b))
    if isinstance(a, dict):
        keys = set(a) | set(b)
        return {k: blend_val(a.get(k, b.get(k)), b.get(k, a.get(k)), u) for k in keys}
    return b if u >= 0.5 else a
