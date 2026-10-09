"""Shared animation utilities: colors, easing, keyframes, camera, timeline lookups,
lip-sync, blinking, music envelopes and a few skia drawing helpers.

Coordinate system: the "stage" is 720 x 1280 units (same as the video frame).
Camera(cx, cy, zoom) maps stage point (cx, cy) to the frame center; zoom 2 shows
a 360 x 640 region. Sets may extend beyond the stage for pans.
All times are absolute seconds on the master timeline unless a name says "local".
"""
from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import skia

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import FPS, H, LIPSYNC, MUSIC_ENV, PAL, TIMELINE, W  # noqa: E402

# --------------------------------------------------------------------------- colors


def col(c, a: float = 1.0) -> int:
    """Hex string / palette key / (r,g,b[,a]) tuple -> skia color int. `a` multiplies alpha."""
    if isinstance(c, str):
        c = PAL.get(c, c)
        c = c.lstrip("#")
        r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
        al = int(c[6:8], 16) / 255 if len(c) == 8 else 1.0
    elif isinstance(c, int):
        return skia.ColorSetA(c, int(max(0, min(1, a)) * skia.ColorGetA(c)))
    else:
        r, g, b = c[0], c[1], c[2]
        al = c[3] if len(c) > 3 else 1.0
    return skia.Color(int(r), int(g), int(b), int(max(0.0, min(1.0, al * a)) * 255))


def rgb(c) -> tuple:
    """Palette key / hex -> (r, g, b) floats 0..255."""
    c = PAL.get(c, c).lstrip("#")
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))


def mix_col(a, b, t: float, alpha: float = 1.0) -> int:
    """Blend two colors (palette keys / hex / tuples) -> skia color int."""
    ra = rgb(a) if isinstance(a, str) else a
    rb = rgb(b) if isinstance(b, str) else b
    t = max(0.0, min(1.0, t))
    return skia.Color(*(int(ra[i] + (rb[i] - ra[i]) * t) for i in range(3)), int(255 * max(0, min(1, alpha))))


# --------------------------------------------------------------------------- math / easing


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    return a + (b - a) * t


def remap(x, a, b, c=0.0, d=1.0, clip=True):
    """Map x from [a,b] to [c,d]."""
    if b == a:
        return d
    t = (x - a) / (b - a)
    if clip:
        t = clamp(t)
    return c + (d - c) * t


def smoothstep(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_in_out(x):
    x = clamp(x)
    return 0.5 - 0.5 * math.cos(math.pi * x)


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in(x):
    x = clamp(x)
    return x ** 3


def ease_out_back(x, s=1.7):
    x = clamp(x) - 1
    return x * x * ((s + 1) * x + s) + 1


def ease_out_elastic(x):
    x = clamp(x)
    if x in (0, 1):
        return x
    return 2 ** (-10 * x) * math.sin((x * 10 - 0.75) * (2 * math.pi) / 3) + 1


def window(t, a, b, fade_in=0.3, fade_out=0.3):
    """1 inside [a,b] with smooth ramps of the given lengths at each edge, else 0."""
    if t < a or t > b:
        return 0.0
    v = 1.0
    if fade_in > 0:
        v = min(v, smoothstep((t - a) / fade_in))
    if fade_out > 0:
        v = min(v, smoothstep((b - t) / fade_out))
    return v


def noise1(x: float, seed: int = 0) -> float:
    """Smooth 1D value noise in [-1, 1] (deterministic)."""
    i = math.floor(x)
    f = x - i

    def h(n):
        n = (n * 374761393 + seed * 668265263) & 0xFFFFFFFF
        n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
        return ((n ^ (n >> 16)) & 0xFFFF) / 32767.5 - 1.0

    u = f * f * (3 - 2 * f)
    return h(i) * (1 - u) + h(i + 1) * u


def hash01(n: int, seed: int = 0) -> float:
    n = (n * 2654435761 + seed * 40503 + 12345) & 0xFFFFFFFF
    n = ((n ^ (n >> 15)) * 2246822519) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) & 0xFFFFFFFF
    return n / 0xFFFFFFFF


class Track:
    """Keyframed scalar/tuple track.

    Track([(t0, v0), (t1, v1, ease), ...]) - ease names how we arrive at that key:
    'io' (ease in-out, default), 'lin', 'in', 'out', 'back', 'step', 'elastic'.
    Values may be floats or tuples of floats.
    """

    EASES = {"io": ease_in_out, "lin": lambda x: clamp(x), "in": ease_in, "out": ease_out,
             "back": ease_out_back, "step": lambda x: 1.0 if x >= 1 else 0.0, "elastic": ease_out_elastic,
             "smooth": smoothstep}

    def __init__(self, keys):
        self.keys = sorted([(k[0], k[1], k[2] if len(k) > 2 else "io") for k in keys], key=lambda k: k[0])

    def __call__(self, t):
        ks = self.keys
        if t <= ks[0][0]:
            return ks[0][1]
        if t >= ks[-1][0]:
            return ks[-1][1]
        for i in range(1, len(ks)):
            if t < ks[i][0]:
                t0, v0, _ = ks[i - 1]
                t1, v1, e = ks[i]
                x = self.EASES[e]((t - t0) / (t1 - t0))
                if isinstance(v0, tuple):
                    return tuple(a + (b - a) * x for a, b in zip(v0, v1))
                return v0 + (v1 - v0) * x
        return ks[-1][1]


# --------------------------------------------------------------------------- camera


@dataclass
class Camera:
    cx: float = W / 2
    cy: float = H / 2
    zoom: float = 1.0
    rot: float = 0.0       # degrees
    shake: float = 0.0     # stage units of handheld jitter

    def apply(self, canvas: skia.Canvas, t: float = 0.0):
        sx = sy = 0.0
        if self.shake:
            sx = noise1(t * 9.0, 11) * self.shake
            sy = noise1(t * 9.0, 23) * self.shake
        canvas.translate(W / 2, H / 2)
        canvas.scale(self.zoom, self.zoom)
        if self.rot:
            canvas.rotate(self.rot)
        canvas.translate(-self.cx + sx, -self.cy + sy)

    def to_screen(self, x, y):
        """Stage -> screen (ignores rot/shake)."""
        return (W / 2 + (x - self.cx) * self.zoom, H / 2 + (y - self.cy) * self.zoom)

    @staticmethod
    def lerp(a: "Camera", b: "Camera", t: float) -> "Camera":
        return Camera(lerp(a.cx, b.cx, t), lerp(a.cy, b.cy, t), a.zoom * (b.zoom / a.zoom) ** t,
                      lerp(a.rot, b.rot, t), lerp(a.shake, b.shake, t))


# --------------------------------------------------------------------------- timeline access


@lru_cache(maxsize=1)
def timeline() -> dict:
    return json.loads(Path(TIMELINE).read_text())


def beat(name: str) -> float:
    return timeline()["beats"][name]


def scene_span(sid: str) -> tuple:
    for s in timeline()["scenes"]:
        if s["id"] == sid:
            return s["start"], s["end"]
    raise KeyError(sid)


def line(lid: str) -> dict:
    for ln in timeline()["lines"]:
        if ln["id"] == lid:
            return ln
    raise KeyError(lid)


def line_start(lid):
    return line(lid)["start"]


def line_end(lid):
    return line(lid)["end"]


def speaking(char: str, t: float, pad: float = 0.0):
    """Return the line dict `char` is speaking at time t (or None)."""
    for ln in timeline()["lines"]:
        if ln["char"] == char and ln["start"] - pad <= t <= ln["end"] + pad:
            return ln
    return None


def music_cue(cue: str) -> dict:
    for m in timeline()["music"]:
        if m["cue"] == cue:
            return m
    raise KeyError(cue)


@lru_cache(maxsize=1)
def _lips():
    p = Path(LIPSYNC)
    return json.loads(p.read_text()) if p.exists() else {}


def mouth(char: str, t: float) -> tuple:
    """(open 0..1, round 0..1) lip-sync for `char` at time t. (0, 0) when silent."""
    ln = speaking(char, t)
    if not ln:
        return 0.0, 0.0
    d = _lips().get(ln["id"])
    if not d:
        return 0.0, 0.0
    f = (t - ln["start"]) * FPS
    i = int(f)
    o, r = d["open"], d["round"]
    if i >= len(o) - 1:
        return 0.0, 0.0
    a = f - i
    return o[i] * (1 - a) + o[i + 1] * a, r[i] * (1 - a) + r[i + 1] * a


@lru_cache(maxsize=1)
def _music_env():
    p = Path(MUSIC_ENV)
    return json.loads(p.read_text()) if p.exists() else {}


def music_env(cue: str, t: float, key: str = "rms") -> float:
    """Music loudness envelope 0..1 for `cue` at absolute time t (0 outside the cue).

    Reads build/music/envelopes.json written by audio/music.py:
      {cue: {"rms": [per-frame 0..1], "low": [...], "high": [...], "onsets": [local seconds]}}
    """
    env = _music_env().get(cue)
    if not env:
        return 0.0
    try:
        m = music_cue(cue)
    except KeyError:
        return 0.0
    local = t - m["start"]
    arr = env.get(key) or env.get("rms")
    i = int(local * FPS)
    if i < 0 or i >= len(arr):
        return 0.0
    return arr[i]


def music_onsets(cue: str) -> list:
    """Absolute times of note onsets for a cue (for sparkles synced to notes)."""
    env = _music_env().get(cue)
    if not env:
        return []
    st = music_cue(cue)["start"]
    return [st + o for o in env.get("onsets", [])]


# --------------------------------------------------------------------------- organic motion


def auto_blink(t: float, seed: int = 0, rate: float = 4.2, robotic: bool = False) -> float:
    """Eyelid openness 0..1 with natural blinks (~every `rate` s, jittered).

    robotic=True: perfectly periodic, very quick, both eyes identical (for Quill).
    """
    if robotic:
        ph = (t + seed * 0.37) % rate
        d = 0.10
        if ph < d:
            return 1.0 - math.sin(ph / d * math.pi)
        return 1.0
    # jittered blink schedule: blink k happens near k*rate + jitter
    k = math.floor(t / rate)
    for kk in (k - 1, k, k + 1):
        bt = kk * rate + hash01(kk, seed) * rate * 0.6
        dt = t - bt
        dur = 0.16 + 0.06 * hash01(kk, seed + 7)
        if 0 <= dt < dur:
            x = dt / dur
            # fast close, slower open
            return 1.0 - (math.sin(min(1.0, x / 0.4) * math.pi / 2) if x < 0.4 else math.cos((x - 0.4) / 0.6 * math.pi / 2))
    return 1.0


def breathe(t: float, rate: float = 0.25, seed: int = 0) -> float:
    """Breathing phase -1..1 (sinusoid at `rate` Hz with tiny variation)."""
    return math.sin(2 * math.pi * rate * t + seed) * 0.9 + noise1(t * 0.5, seed) * 0.1


def wobble(t: float, amp: float = 1.0, freq: float = 0.6, seed: int = 0) -> float:
    """Small organic drift for idle motion."""
    return noise1(t * freq, seed) * amp


# --------------------------------------------------------------------------- drawing helpers


def paint(color, alpha=1.0, stroke=0.0, aa=True, blur=0.0, cap="round", shader=None, blend=None):
    p = skia.Paint(AntiAlias=aa, Color=col(color, alpha) if color is not None else skia.ColorBLACK)
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap({"round": skia.Paint.kRound_Cap, "butt": skia.Paint.kButt_Cap,
                        "square": skia.Paint.kSquare_Cap}[cap])
        p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if shader is not None:
        p.setShader(shader)
        if color is None:
            p.setAlphaf(alpha)
    if blend:
        p.setBlendMode({"add": skia.BlendMode.kPlus, "screen": skia.BlendMode.kScreen,
                        "multiply": skia.BlendMode.kMultiply, "overlay": skia.BlendMode.kOverlay,
                        "srcatop": skia.BlendMode.kSrcATop}[blend])
    return p


def smooth_path(points, closed=True, tension=0.5) -> skia.Path:
    """Catmull-Rom spline through points -> skia.Path (cubic beziers)."""
    path = skia.Path()
    n = len(points)
    if n < 2:
        return path
    pts = list(points)
    path.moveTo(*pts[0])
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = pts[(i - 1) % n] if closed else pts[max(i - 1, 0)]
        p1 = pts[i]
        p2 = pts[(i + 1) % n] if closed else pts[i + 1]
        p3 = pts[(i + 2) % n] if closed else pts[min(i + 2, n - 1)]
        k = tension / 3 * 2
        c1 = (p1[0] + (p2[0] - p0[0]) * k / 2, p1[1] + (p2[1] - p0[1]) * k / 2)
        c2 = (p2[0] - (p3[0] - p1[0]) * k / 2, p2[1] - (p3[1] - p1[1]) * k / 2)
        path.cubicTo(*c1, *c2, *p2)
    if closed:
        path.close()
    return path


def linear_grad(x0, y0, x1, y1, colors, pos=None):
    return skia.GradientShader.MakeLinear([(x0, y0), (x1, y1)], [col(c) if not isinstance(c, int) else c for c in colors], pos)


def radial_grad(cx, cy, r, colors, pos=None):
    return skia.GradientShader.MakeRadial((cx, cy), max(r, 0.01), [col(c) if not isinstance(c, int) else c for c in colors], pos)


def glow(canvas, x, y, r, color, alpha=1.0, blend="add"):
    """Soft radial glow blob."""
    c = col(color, alpha)
    sh = skia.GradientShader.MakeRadial((x, y), max(r, 0.5), [c, skia.ColorSetA(c, 0)])
    canvas.drawCircle(x, y, r, paint(None, shader=sh, blend=blend))


_FONT_CACHE = {}


def font(size: float, family: str = "Inter", weight: int = 400) -> skia.Font:
    key = (family, weight)
    if key not in _FONT_CACHE:
        style = skia.FontStyle(weight, skia.FontStyle.kNormal_Width, skia.FontStyle.kUpright_Slant)
        _FONT_CACHE[key] = skia.Typeface.MakeFromName(family, style)
    f = skia.Font(_FONT_CACHE[key], size)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    f.setSubpixel(True)
    return f


def draw_text(canvas, text, x, y, size, color="white", alpha=1.0, align="center", family="Inter",
              weight=400, tracking=0.0, glow_r=0.0):
    """Draw single-line text. y is the baseline. tracking = extra px between glyphs."""
    f = font(size, family, weight)
    if tracking:
        widths = [f.measureText(ch) for ch in text]
        total = sum(widths) + tracking * (len(text) - 1)
        sx = x - total / 2 if align == "center" else (x - total if align == "right" else x)
        if glow_r:
            for ch, w_ in zip(text, widths):
                canvas.drawString(ch, sx, y, f, paint(color, alpha * 0.6, blur=glow_r))
                sx += w_ + tracking
            sx = x - total / 2 if align == "center" else (x - total if align == "right" else x)
        for ch, w_ in zip(text, widths):
            canvas.drawString(ch, sx, y, f, paint(color, alpha))
            sx += w_ + tracking
        return total
    w_ = f.measureText(text)
    sx = x - w_ / 2 if align == "center" else (x - w_ if align == "right" else x)
    if glow_r:
        canvas.drawString(text, sx, y, f, paint(color, alpha * 0.6, blur=glow_r))
    canvas.drawString(text, sx, y, f, paint(color, alpha))
    return w_


def fade_overlay(canvas, amount: float, color="#000000"):
    """Full-frame overlay in SCREEN space (call with identity matrix)."""
    if amount <= 0:
        return
    canvas.drawRect(skia.Rect(0, 0, W, H), paint(color, clamp(amount)))


class Layer:
    """Context manager for an offscreen layer with alpha and optional color filter.

    with Layer(canvas, alpha=0.5, cf=skia.ColorFilters.Matrix(...)):
        ...draw...
    """

    def __init__(self, canvas, alpha=1.0, cf=None, blur=0.0, blend=None, bounds=None):
        self.c = canvas
        self.p = skia.Paint()
        self.p.setAlphaf(clamp(alpha))
        if cf is not None:
            self.p.setColorFilter(cf)
        if blur:
            self.p.setImageFilter(skia.ImageFilters.Blur(blur, blur))
        if blend:
            self.p.setBlendMode({"add": skia.BlendMode.kPlus, "screen": skia.BlendMode.kScreen}[blend])
        self.bounds = bounds

    def __enter__(self):
        if self.bounds is not None:
            self.c.saveLayer(self.bounds, self.p)
        else:
            self.c.saveLayer(None, self.p)
        return self.c

    def __exit__(self, *a):
        self.c.restore()


def light_filter(light: float = 1.0, tint=(0, 0, 0), tint_amt: float = 0.0):
    """Color filter that darkens by `light` (0..1+) and blends toward `tint` (r,g,b 0..255)."""
    l = light
    ta = tint_amt
    tr, tg, tb = (c / 255 for c in tint)
    m = [l * (1 - ta), 0, 0, 0, tr * ta,
         0, l * (1 - ta), 0, 0, tg * ta,
         0, 0, l * (1 - ta), 0, tb * ta,
         0, 0, 0, 1, 0]
    return skia.ColorFilters.Matrix(m)


def new_surface():
    return skia.Surface(W, H)
