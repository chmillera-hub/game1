"""core.py -- the drawing toolbox every other module builds on.

Sections
  1. surfaces & contexts          new_surface, frame, surface_to_pil, pil_to_surface, save_png
  2. color                        col, mix, shade, tint, alpha, mul, saturate, hue_shift, luma, src
  3. math, easing, tracks         clamp, lerp, remap, ramp, pingpong, smoothstep, ease(), EASE, track
  4. camera                       Camera (push / pan / zoom / roll with per-layer parallax)
  5. noise & jitter               hash01, noise1, noise2, fbm1, fbm2, jitter, noise_array
  6. shapes & paths               circle, ellipse, rounded_rect, superellipse, smooth_closed/open,
                                  spline, blob, capsule, tapered, star, polygon
  7. gradients                    linear, radial, vgrad
  8. text (cairo toy API)         text, measure, wrap, text_block, arc_text, rotated_text, glow_text

Conventions: 1920x1080 frames, y grows downward, angles in radians, colors are float
tuples (r, g, b) or (r, g, b, a) in 0..1 (hex strings are accepted everywhere a color is).
Everything is deterministic -- no wall clock, no unseeded randomness.
"""

import contextlib
import functools
import math

import cairocffi as cairo
from cairocffi import cairo as _lib

W, H = 1920, 1080
FPS = 24
TAU = math.tau

# Direct C entry points for hot path-building loops (skip cairocffi's per-call status check;
# ~2x less Python overhead). Use only for pure path construction.
_move_to = _lib.cairo_move_to
_line_to = _lib.cairo_line_to
_curve_to = _lib.cairo_curve_to
_close = _lib.cairo_close_path
_arc = _lib.cairo_arc
_arc_neg = _lib.cairo_arc_negative

# ----------------------------------------------------------------------------------------
# 1. surfaces & contexts
# ----------------------------------------------------------------------------------------


def new_surface(w=W, h=H, fmt=cairo.FORMAT_ARGB32):
    """A fresh, fully transparent cairo ImageSurface."""
    return cairo.ImageSurface(fmt, int(w), int(h))


def new_context(surface, tolerance=0.25):
    """Context with the film's defaults (round joins/caps, slightly relaxed curve tolerance
    -- 0.25 px is visually identical to the default 0.1 but ~15% faster)."""
    cr = cairo.Context(surface)
    cr.set_tolerance(tolerance)
    cr.set_line_join(cairo.LINE_JOIN_ROUND)
    cr.set_line_cap(cairo.LINE_CAP_ROUND)
    return cr


def frame(w=W, h=H):
    """(surface, context) pair for a full frame."""
    s = new_surface(w, h)
    return s, new_context(s)


def surface_to_pil(surface):
    """Copy a cairo ARGB32 surface into a straight-alpha PIL RGBA image."""
    from PIL import Image
    surface.flush()
    w, h = surface.get_width(), surface.get_height()
    im = Image.frombuffer("RGBa", (w, h), bytes(surface.get_data()), "raw", "BGRa",
                          surface.get_stride(), 1)
    return im.convert("RGBA")


def pil_to_surface(img):
    """PIL image (any mode) -> new premultiplied cairo ARGB32 surface."""
    img = img.convert("RGBA").convert("RGBa")      # premultiply
    w, h = img.size
    data = bytearray(img.tobytes("raw", "BGRa"))
    return cairo.ImageSurface.create_for_data(data, cairo.FORMAT_ARGB32, w, h, w * 4)


def save_png(surface, path):
    surface.flush()
    surface.write_to_png(str(path))


# ----------------------------------------------------------------------------------------
# 2. color
# ----------------------------------------------------------------------------------------


@functools.lru_cache(maxsize=8192)
def _hex(s):
    s = s.lstrip("#")
    if len(s) in (3, 4):
        s = "".join(ch * 2 for ch in s)
    vals = tuple(int(s[i:i + 2], 16) / 255.0 for i in range(0, len(s), 2))
    return vals


def col(c):
    """Normalize a color: '#3E6E73', '#3E6E73CC', 'abc' or a float tuple -> float tuple."""
    if isinstance(c, str):
        return _hex(c)
    return tuple(c)


hex2rgb = col


def rgb2hex(c):
    c = col(c)
    return "#" + "".join(f"{int(round(clamp(v) * 255)):02X}" for v in c[:3])


def alpha(c, a):
    """Color with alpha a (multiplies an existing alpha)."""
    c = col(c)
    return (c[0], c[1], c[2], (c[3] if len(c) > 3 else 1.0) * a)


def mix(a, b, t):
    """Linear blend of two colors (alpha blended too when either has it)."""
    a = col(a)
    b = col(b)
    if len(a) != len(b):
        a = a if len(a) == 4 else (*a, 1.0)
        b = b if len(b) == 4 else (*b, 1.0)
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def shade(c, k):
    """Darken toward black by k (0..1); alpha kept."""
    c = col(c)
    f = 1.0 - k
    return (c[0] * f, c[1] * f, c[2] * f) + tuple(c[3:])


def tint(c, k):
    """Lighten toward white by k (0..1); alpha kept."""
    c = col(c)
    return tuple(v + (1.0 - v) * k for v in c[:3]) + tuple(c[3:])


def mul(a, b):
    """Per-channel multiply (light color x material color)."""
    a = col(a)
    b = col(b)
    return tuple(clamp(x * y) for x, y in zip(a[:3], b[:3])) + tuple(a[3:])


def add(a, b, k=1.0):
    a = col(a)
    b = col(b)
    return tuple(clamp(x + y * k) for x, y in zip(a[:3], b[:3])) + tuple(a[3:])


def luma(c):
    c = col(c)
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def saturate(c, k):
    """k > 0 more saturated, k < 0 toward grey (k = -1 is fully grey)."""
    c = col(c)
    y = luma(c)
    return tuple(clamp(y + (v - y) * (1.0 + k)) for v in c[:3]) + tuple(c[3:])


def to_hsv(c):
    import colorsys
    c = col(c)
    return colorsys.rgb_to_hsv(*c[:3])


def from_hsv(h, s, v):
    import colorsys
    return colorsys.hsv_to_rgb(h % 1.0, clamp(s), clamp(v))


def hue_shift(c, deg):
    c = col(c)
    h, s, v = to_hsv(c)
    return from_hsv(h + deg / 360.0, s, v) + tuple(c[3:])


def src(cr, c, a=None):
    """Set a solid source color (optionally with extra alpha)."""
    c = col(c)
    if a is None:
        if len(c) > 3:
            cr.set_source_rgba(c[0], c[1], c[2], c[3])
        else:
            cr.set_source_rgb(c[0], c[1], c[2])
    else:
        cr.set_source_rgba(c[0], c[1], c[2], (c[3] if len(c) > 3 else 1.0) * a)


# ----------------------------------------------------------------------------------------
# 3. math, easing, tracks
# ----------------------------------------------------------------------------------------


def clamp(x, lo=0.0, hi=1.0):
    return lo if x < lo else hi if x > hi else x


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_pt(p, q, t):
    return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)


def lerp_tuple(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def invlerp(a, b, x):
    return 0.0 if b == a else (x - a) / (b - a)


def remap(x, a0, a1, b0, b1, clamped=True):
    u = invlerp(a0, a1, x)
    if clamped:
        u = clamp(u)
    return b0 + (b1 - b0) * u


def ramp(t, t0, t1, ease_fn=None):
    """0 before t0, 1 after t1, linear (or eased) in between."""
    if t1 <= t0:
        return 1.0 if t >= t1 else 0.0
    u = clamp((t - t0) / (t1 - t0))
    return ease(ease_fn, u) if ease_fn else u


def window(t, t0, t1, fade_in=0.25, fade_out=0.25, ease_fn="inout_sine"):
    """0 -> 1 -> 0 envelope: ramps up over fade_in at t0, down over fade_out ending at t1."""
    return min(ramp(t, t0, t0 + fade_in, ease_fn), 1.0 - ramp(t, t1 - fade_out, t1, ease_fn))


def pingpong(t, length=1.0):
    """Triangle wave 0 -> length -> 0 with period 2*length."""
    m = t % (2.0 * length)
    return m if m <= length else 2.0 * length - m


def smoothstep(e0, e1, x):
    u = clamp((x - e0) / (e1 - e0)) if e1 != e0 else (1.0 if x >= e1 else 0.0)
    return u * u * (3.0 - 2.0 * u)


def smooth(u):
    u = clamp(u)
    return u * u * (3.0 - 2.0 * u)


def smoother(u):
    u = clamp(u)
    return u * u * u * (u * (u * 6.0 - 15.0) + 10.0)


def wrap_angle(a):
    return (a + math.pi) % TAU - math.pi


def lerp_angle(a, b, t):
    return a + wrap_angle(b - a) * t


def dist(p, q):
    return math.hypot(q[0] - p[0], q[1] - p[1])


def angle_to(p, q):
    return math.atan2(q[1] - p[1], q[0] - p[0])


def rotate_pt(p, a, origin=(0.0, 0.0)):
    c, s = math.cos(a), math.sin(a)
    x, y = p[0] - origin[0], p[1] - origin[1]
    return (origin[0] + x * c - y * s, origin[1] + x * s + y * c)


def normalize(v):
    n = math.hypot(v[0], v[1])
    return (v[0] / n, v[1] / n) if n > 1e-12 else (0.0, 0.0)


# --- easing functions (all map 0..1 -> 0..1) ---

def linear(u):
    return u


def in_quad(u):
    return u * u


def out_quad(u):
    return 1.0 - (1.0 - u) * (1.0 - u)


def inout_quad(u):
    return 2 * u * u if u < 0.5 else 1.0 - (-2 * u + 2) ** 2 / 2


def in_cubic(u):
    return u * u * u


def out_cubic(u):
    return 1.0 - (1.0 - u) ** 3


def inout_cubic(u):
    return 4 * u * u * u if u < 0.5 else 1.0 - (-2 * u + 2) ** 3 / 2


def in_sine(u):
    return 1.0 - math.cos(u * math.pi / 2)


def out_sine(u):
    return math.sin(u * math.pi / 2)


def inout_sine(u):
    return -(math.cos(math.pi * u) - 1.0) / 2


_BACK = 1.70158


def in_back(u, s=_BACK):
    return u * u * ((s + 1) * u - s)


def out_back(u, s=_BACK):
    v = u - 1.0
    return 1.0 + v * v * ((s + 1) * v + s)


def inout_back(u, s=_BACK * 1.525):
    if u < 0.5:
        return ((2 * u) ** 2 * ((s + 1) * 2 * u - s)) / 2
    v = 2 * u - 2
    return (v * v * ((s + 1) * v + s) + 2) / 2


def out_elastic(u, bounces=2.5, decay=6.0):
    """'Elastic-lite': overshoots ~10-15% and settles within the interval (exactly 1 at u=1)."""
    if u <= 0.0:
        return 0.0
    if u >= 1.0:
        return 1.0
    return 1.0 - math.cos(u * math.pi * bounces) * math.exp(-decay * u)


def in_elastic(u):
    return 1.0 - out_elastic(1.0 - u)


EASE = {
    "linear": linear,
    "in_quad": in_quad, "out_quad": out_quad, "inout_quad": inout_quad,
    "in_cubic": in_cubic, "out_cubic": out_cubic, "inout_cubic": inout_cubic,
    "in_sine": in_sine, "out_sine": out_sine, "inout_sine": inout_sine,
    "in_back": in_back, "out_back": out_back, "inout_back": inout_back,
    "out_elastic": out_elastic, "in_elastic": in_elastic,
    "smooth": smooth, "smoother": smoother,
}


def ease(fn, u):
    """Apply an easing given by name (see EASE), callable or None (linear). u is clamped."""
    u = clamp(u)
    if fn is None:
        return u
    if isinstance(fn, str):
        return EASE[fn](u)
    return fn(u)


def _interp(a, b, u):
    if isinstance(a, (tuple, list)):
        return tuple(x + (y - x) * u for x, y in zip(a, b))
    return a + (b - a) * u


def track(t, keys, ease_fn="inout_sine"):
    """Keyframe interpolation.

    keys: [(t0, v0), (t1, v1), (t2, v2, 'out_back'), ...] sorted by time. v may be a number or
    a tuple. The optional 3rd element is the easing used on the way INTO that key (default
    `ease_fn`). Holds v0 before the first key and the last value after the last key.
    """
    if t <= keys[0][0]:
        return keys[0][1]
    for i in range(1, len(keys)):
        k1 = keys[i]
        if t < k1[0]:
            k0 = keys[i - 1]
            u = (t - k0[0]) / (k1[0] - k0[0])
            e = k1[2] if len(k1) > 2 else ease_fn
            return _interp(k0[1], k1[1], ease(e, u))
    return keys[-1][1]


def frames(seconds):
    return int(round(seconds * FPS))


# ----------------------------------------------------------------------------------------
# 4. camera
# ----------------------------------------------------------------------------------------


class Camera:
    """A 2D multiplane camera.

    (x, y)  world point shown at the screen center (world == screen coords at the default),
    zoom    magnification (1 = none), rot = roll in radians (positive = clockwise on screen).

    Layers are drawn inside `with cam.view(cr, parallax=p):`. p = 1 is the main action plane,
    p < 1 moves/zooms less (distant: sky 0.0-0.2, far town 0.3-0.6), p > 1 more (foreground
    1.2-1.6). For a layer at parallax p the effective pan is scaled by p and the zoom is
    zoom**p, so a dolly push-in makes foreground grow faster than background.
    """

    __slots__ = ("x", "y", "zoom", "rot")

    def __init__(self, x=W / 2, y=H / 2, zoom=1.0, rot=0.0):
        self.x, self.y, self.zoom, self.rot = float(x), float(y), float(zoom), float(rot)

    def __repr__(self):
        return f"Camera(x={self.x:.1f}, y={self.y:.1f}, zoom={self.zoom:.3f}, rot={self.rot:.3f})"

    @staticmethod
    def about(fx, fy, zoom, rot=0.0):
        """Camera that zooms about screen point (fx, fy), keeping that point fixed on screen."""
        return Camera(fx - (fx - W / 2) / zoom, fy - (fy - H / 2) / zoom, zoom, rot)

    def _params(self, parallax):
        z = self.zoom ** parallax
        cx = W / 2 + (self.x - W / 2) * parallax
        cy = H / 2 + (self.y - H / 2) * parallax
        return cx, cy, z

    def matrix(self, parallax=1.0):
        cx, cy, z = self._params(parallax)
        m = cairo.Matrix()
        m.translate(W / 2, H / 2)
        if self.rot:
            m.rotate(self.rot)
        m.scale(z, z)
        m.translate(-cx, -cy)
        return m

    def apply(self, cr, parallax=1.0):
        cr.transform(self.matrix(parallax))

    @contextlib.contextmanager
    def view(self, cr, parallax=1.0):
        cr.save()
        cr.transform(self.matrix(parallax))
        try:
            yield cr
        finally:
            cr.restore()

    def to_screen(self, x, y, parallax=1.0):
        return self.matrix(parallax).transform_point(x, y)

    def to_world(self, sx, sy, parallax=1.0):
        m = self.matrix(parallax)
        m.invert()
        return m.transform_point(sx, sy)

    def scale_at(self, parallax=1.0):
        """On-screen magnification of a layer at this parallax."""
        return self.zoom ** parallax

    @staticmethod
    def lerp(a, b, u):
        # zoom interpolated geometrically so push-ins feel linear
        z = a.zoom * (b.zoom / a.zoom) ** u
        return Camera(lerp(a.x, b.x, u), lerp(a.y, b.y, u), z, lerp(a.rot, b.rot, u))

    @staticmethod
    def track(t, keys, ease_fn="inout_sine"):
        """keys: [(t0, Camera), (t1, Camera[, ease]), ...] -> interpolated Camera."""
        if t <= keys[0][0]:
            return keys[0][1]
        for i in range(1, len(keys)):
            k1 = keys[i]
            if t < k1[0]:
                k0 = keys[i - 1]
                u = ease(k1[2] if len(k1) > 2 else ease_fn, (t - k0[0]) / (k1[0] - k0[0]))
                return Camera.lerp(k0[1], k1[1], u)
        return keys[-1][1]

    def shake(self, t, amp=6.0, freq=9.0, seed=0, rot_amp=0.0):
        """Deterministic handheld/impact shake (amp in screen px)."""
        return Camera(self.x + amp * noise1(t * freq, seed) / self.zoom,
                      self.y + amp * noise1(t * freq, seed + 17) / self.zoom,
                      self.zoom, self.rot + rot_amp * noise1(t * freq, seed + 31))

    def drift(self, t, amp=3.0, freq=0.15, seed=0):
        """Very slow 'breathing camera' float, for otherwise locked shots."""
        return Camera(self.x + amp * fbm1(t * freq, 2, seed), self.y + amp * 0.6 * fbm1(t * freq, 2, seed + 5),
                      self.zoom, self.rot)


def camera_move(t, t0, t1, a, b, ease_fn="inout_sine"):
    """Camera moving from a to b between t0 and t1 (held outside)."""
    return Camera.lerp(a, b, ramp(t, t0, t1, ease_fn))


@contextlib.contextmanager
def saved(cr):
    cr.save()
    try:
        yield cr
    finally:
        cr.restore()


@contextlib.contextmanager
def at(cr, x, y, angle=0.0, sx=1.0, sy=None):
    """Temporarily move the origin to (x, y), rotate and scale."""
    cr.save()
    cr.translate(x, y)
    if angle:
        cr.rotate(angle)
    if sx != 1.0 or (sy is not None and sy != 1.0):
        cr.scale(sx, sx if sy is None else sy)
    try:
        yield cr
    finally:
        cr.restore()


@contextlib.contextmanager
def zoom_about(cr, px, py, z, rot=0.0):
    """Scale (and roll) the drawing about point (px, py)."""
    cr.save()
    cr.translate(px, py)
    if rot:
        cr.rotate(rot)
    cr.scale(z, z)
    cr.translate(-px, -py)
    try:
        yield cr
    finally:
        cr.restore()


# ----------------------------------------------------------------------------------------
# 5. noise & jitter (deterministic)
# ----------------------------------------------------------------------------------------


def hash01(i, seed=0):
    """Integer hash -> float in [0, 1)."""
    h = (int(i) * 374761393 + int(seed) * 668265263 + 0x9E3779B9) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h ^= h >> 16
    return (h & 0xFFFFFF) / 16777216.0


def hash2(ix, iy, seed=0):
    return hash01(int(ix) * 73856093 ^ int(iy) * 19349663, seed)


def jitter(i, amp=1.0, seed=0):
    """Deterministic offset in [-amp, amp] for item i."""
    return (hash01(i, seed) * 2.0 - 1.0) * amp


def noise1(x, seed=0):
    """Smooth 1D value noise in [-1, 1]."""
    i = math.floor(x)
    f = x - i
    a = hash01(i, seed)
    b = hash01(i + 1, seed)
    u = f * f * (3.0 - 2.0 * f)
    return (a + (b - a) * u) * 2.0 - 1.0


def noise2(x, y, seed=0):
    """Smooth 2D value noise in [-1, 1]."""
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = x - ix, y - iy
    ux = fx * fx * (3.0 - 2.0 * fx)
    uy = fy * fy * (3.0 - 2.0 * fy)
    a = hash2(ix, iy, seed)
    b = hash2(ix + 1, iy, seed)
    c = hash2(ix, iy + 1, seed)
    d = hash2(ix + 1, iy + 1, seed)
    top = a + (b - a) * ux
    bot = c + (d - c) * ux
    return (top + (bot - top) * uy) * 2.0 - 1.0


def fbm1(x, octaves=3, seed=0, lacunarity=2.0, gain=0.5):
    total, amp, freq, norm = 0.0, 1.0, 1.0, 0.0
    for o in range(octaves):
        total += amp * noise1(x * freq, seed + o * 101)
        norm += amp
        amp *= gain
        freq *= lacunarity
    return total / norm


def fbm2(x, y, octaves=3, seed=0, lacunarity=2.0, gain=0.5):
    total, amp, freq, norm = 0.0, 1.0, 1.0, 0.0
    for o in range(octaves):
        total += amp * noise2(x * freq, y * freq, seed + o * 101)
        norm += amp
        amp *= gain
        freq *= lacunarity
    return total / norm


def noise_array(w, h, scale=64.0, octaves=4, seed=0, gain=0.5):
    """Smooth fbm value noise as a float32 numpy array (h, w) in roughly [-1, 1].

    Built by bicubic-upsampling random lattices (fast, for texture generation in setup())."""
    import numpy as np
    from PIL import Image
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, norm, cell = 1.0, 0.0, float(scale)
    for _ in range(octaves):
        gw, gh = max(2, int(math.ceil(w / cell)) + 2), max(2, int(math.ceil(h / cell)) + 2)
        lat = rng.random((gh, gw), dtype=np.float32) * 2.0 - 1.0
        img = Image.fromarray(lat, mode="F").resize((int(gw * cell), int(gh * cell)), Image.BICUBIC)
        arr = np.asarray(img, np.float32)[:h, :w]
        out[:arr.shape[0], :arr.shape[1]] += arr * amp
        norm += amp
        amp *= gain
        cell = max(1.0, cell / 2.0)
    return out / norm


# ----------------------------------------------------------------------------------------
# 6. shapes & paths (they build the current path; the caller fills / strokes)
# ----------------------------------------------------------------------------------------


def circle(cr, x, y, r):
    cr.new_sub_path()
    cr.arc(x, y, max(r, 0.0), 0.0, TAU)
    cr.close_path()


def ellipse(cr, cx, cy, rx, ry, angle=0.0):
    rx, ry = max(rx, 1e-3), max(ry, 1e-3)
    cr.save()
    cr.translate(cx, cy)
    if angle:
        cr.rotate(angle)
    cr.scale(rx, ry)
    cr.new_sub_path()
    cr.arc(0.0, 0.0, 1.0, 0.0, TAU)
    cr.close_path()
    cr.restore()


def rounded_rect(cr, x, y, w, h, r):
    """r: radius or (tl, tr, br, bl)."""
    if isinstance(r, (int, float)):
        r = (r, r, r, r)
    m = min(w, h) / 2.0
    tl, tr, br, bl = (min(max(v, 0.0), m) for v in r)
    cr.new_sub_path()
    cr.arc(x + w - tr, y + tr, tr, -math.pi / 2, 0.0)
    cr.arc(x + w - br, y + h - br, br, 0.0, math.pi / 2)
    cr.arc(x + bl, y + h - bl, bl, math.pi / 2, math.pi)
    cr.arc(x + tl, y + tl, tl, math.pi, 1.5 * math.pi)
    cr.close_path()


def polygon(cr, pts, close=True):
    ptr = cr._pointer
    _move_to(ptr, pts[0][0], pts[0][1])
    for p in pts[1:]:
        _line_to(ptr, p[0], p[1])
    if close:
        _close(ptr)


def superellipse(cr, cx, cy, rx, ry, n=4.0, steps=48, angle=0.0):
    """|x/rx|^n + |y/ry|^n = 1 -- n=2 ellipse, n=4 'squircle' (barrels, portholes, plaques)."""
    pts = []
    e = 2.0 / n
    ca, sa = math.cos(angle), math.sin(angle)
    for i in range(steps):
        a = TAU * i / steps
        c, s = math.cos(a), math.sin(a)
        x = rx * math.copysign(abs(c) ** e, c)
        y = ry * math.copysign(abs(s) ** e, s)
        pts.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    polygon(cr, pts)


def _cr_ctrl(p0, p1, p2, p3, k):
    return ((p1[0] + (p2[0] - p0[0]) * k, p1[1] + (p2[1] - p0[1]) * k),
            (p2[0] - (p3[0] - p1[0]) * k, p2[1] - (p3[1] - p1[1]) * k))


def smooth_closed(cr, pts, tension=1.0):
    """Closed smooth curve passing through every point (Catmull-Rom -> cubic Bezier)."""
    n = len(pts)
    if n < 3:
        polygon(cr, pts)
        return
    k = tension / 6.0
    ptr = cr._pointer
    _move_to(ptr, pts[0][0], pts[0][1])
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        _curve_to(ptr, p1[0] + (p2[0] - p0[0]) * k, p1[1] + (p2[1] - p0[1]) * k,
                  p2[0] - (p3[0] - p1[0]) * k, p2[1] - (p3[1] - p1[1]) * k, p2[0], p2[1])
    _close(ptr)


def smooth_open(cr, pts, tension=1.0, move=True):
    """Open smooth curve through pts (end tangents mirror the first/last segment).
    move=False continues the current path (line_to the first point)."""
    n = len(pts)
    if n < 2:
        return
    ptr = cr._pointer
    if move:
        _move_to(ptr, pts[0][0], pts[0][1])
    else:
        _line_to(ptr, pts[0][0], pts[0][1])
    if n == 2:
        _line_to(ptr, pts[1][0], pts[1][1])
        return
    k = tension / 6.0
    for i in range(n - 1):
        p1, p2 = pts[i], pts[i + 1]
        p0 = pts[i - 1] if i > 0 else (2 * p1[0] - p2[0], 2 * p1[1] - p2[1])
        p3 = pts[i + 2] if i + 2 < n else (2 * p2[0] - p1[0], 2 * p2[1] - p1[1])
        _curve_to(ptr, p1[0] + (p2[0] - p0[0]) * k, p1[1] + (p2[1] - p0[1]) * k,
                  p2[0] - (p3[0] - p1[0]) * k, p2[1] - (p3[1] - p1[1]) * k, p2[0], p2[1])


def spline(pts, n=8, closed=False, tension=1.0):
    """Sample a Catmull-Rom spline through pts: n samples per segment. Returns a point list."""
    m = len(pts)
    if m < 2:
        return list(pts)
    k = tension / 6.0
    out = []
    segs = m if closed else m - 1
    for i in range(segs):
        if closed:
            p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % m], pts[(i + 2) % m]
        else:
            p1, p2 = pts[i], pts[i + 1]
            p0 = pts[i - 1] if i > 0 else (2 * p1[0] - p2[0], 2 * p1[1] - p2[1])
            p3 = pts[i + 2] if i + 2 < m else (2 * p2[0] - p1[0], 2 * p2[1] - p1[1])
        c1, c2 = _cr_ctrl(p0, p1, p2, p3, k)
        for j in range(n):
            u = j / n
            v = 1.0 - u
            a, b, c, d = v * v * v, 3 * v * v * u, 3 * v * u * u, u * u * u
            out.append((a * p1[0] + b * c1[0] + c * c2[0] + d * p2[0],
                        a * p1[1] + b * c1[1] + c * c2[1] + d * p2[1]))
    if not closed:
        out.append(tuple(pts[-1]))
    return out


def polyline_length(pts):
    return sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))


def resample(pts, n):
    """n points evenly spaced by arc length along polyline pts."""
    if len(pts) < 2 or n < 2:
        return list(pts)
    seg = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)]
    total = sum(seg) or 1e-9
    out = [tuple(pts[0])]
    j, acc = 0, 0.0
    for k in range(1, n - 1):
        target = total * k / (n - 1)
        while j < len(seg) - 1 and acc + seg[j] < target:
            acc += seg[j]
            j += 1
        u = (target - acc) / (seg[j] or 1e-9)
        out.append(lerp_pt(pts[j], pts[j + 1], u))
    out.append(tuple(pts[-1]))
    return out


def blob(cr, cx, cy, r, wobble=0.12, n=7, seed=0, t=0.0, speed=0.0, sx=1.0, sy=1.0, angle=0.0):
    """Organic closed blob (bushes, clouds, smoke, cloth bundles). `speed` > 0 animates it."""
    pts = []
    ca, sa = math.cos(angle), math.sin(angle)
    for i in range(n):
        a = TAU * i / n
        rr = r * (1.0 + wobble * noise1(i * 1.7 + t * speed, seed + i * 13))
        x, y = math.cos(a) * rr * sx, math.sin(a) * rr * sy
        pts.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    smooth_closed(cr, pts)


def capsule(cr, x0, y0, r0, x1, y1, r1):
    """Tapered capsule: two circles joined by their outer tangents (a seamless limb segment)."""
    dx, dy = x1 - x0, y1 - y0
    d = math.hypot(dx, dy)
    if d <= abs(r0 - r1) + 1e-6:
        if r0 >= r1:
            circle(cr, x0, y0, r0)
        else:
            circle(cr, x1, y1, r1)
        return
    base = math.atan2(dy, dx)
    s = (r0 - r1) / d
    a = math.acos(clamp(s, -1.0, 1.0))   # angle from the axis to the tangent point
    cr.new_sub_path()
    cr.arc(x1, y1, r1, base - a, base + a)       # far cap
    cr.arc(x0, y0, r0, base + a, base - a + TAU)  # near cap
    cr.close_path()


def tapered(cr, pts, w0, w1=None, profile=None, samples=None, cap=True, smooth_spine=True):
    """Build a filled ribbon path along the smooth curve through pts.

    Width (full width, user units) goes from w0 to w1 (default: tapering to a point), or follows
    profile(s) -> width for s in 0..1 (s = arc-length fraction). Round caps when cap=True.
    Caller fills it. For hair strands, whiskers, horns, folds, fringe, inked detail lines.
    Offsets are taken at the knots and joined with Bezier curves (fast); sparse inputs (< 5
    points) are first densified along the spline (`samples` per segment, default 3).
    """
    if w1 is None:
        w1 = 0.0
    sp = list(pts)
    if smooth_spine and 3 < len(sp) < 5 and samples:
        sp = spline(sp, n=samples)
    m = len(sp)
    if m < 2:
        return
    if m == 2 and profile is None:
        # fast path: straight tapered segment with round caps
        (ax, ay), (bx, by) = sp
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy) or 1e-9
        nx, ny = -dy / L, dx / L
        h0, h1 = w0 * 0.5, w1 * 0.5
        ptr = cr._pointer
        _move_to(ptr, ax + nx * h0, ay + ny * h0)
        _line_to(ptr, bx + nx * h1, by + ny * h1)
        a = math.atan2(ny, nx)
        if cap and h1 > 0.3:
            _arc_neg(ptr, bx, by, h1, a, a - math.pi)
        else:
            _line_to(ptr, bx - nx * h1, by - ny * h1)
        _line_to(ptr, ax - nx * h0, ay - ny * h0)
        if cap and h0 > 0.3:
            _arc_neg(ptr, ax, ay, h0, a + math.pi, a)
        _close(ptr)
        return
    # arc-length fractions
    acc = [0.0]
    for i in range(1, m):
        acc.append(acc[-1] + math.hypot(sp[i][0] - sp[i - 1][0], sp[i][1] - sp[i - 1][1]))
    tot = acc[-1] or 1e-9
    left, right = [], []
    for i in range(m):
        if i == 0:
            tx, ty = sp[1][0] - sp[0][0], sp[1][1] - sp[0][1]
        elif i == m - 1:
            tx, ty = sp[-1][0] - sp[-2][0], sp[-1][1] - sp[-2][1]
        else:
            tx, ty = sp[i + 1][0] - sp[i - 1][0], sp[i + 1][1] - sp[i - 1][1]
        L = math.hypot(tx, ty) or 1e-9
        nx, ny = -ty / L, tx / L
        s = acc[i] / tot
        w = (profile(s) if profile else w0 + (w1 - w0) * s) * 0.5
        left.append((sp[i][0] + nx * w, sp[i][1] + ny * w))
        right.append((sp[i][0] - nx * w, sp[i][1] - ny * w))
    ptr = cr._pointer
    if smooth_spine and m > 2:
        smooth_open(cr, left, move=True)
    else:
        polygon(cr, left, close=False)
    if cap:
        # round end cap: sweep from the left offset through the forward tangent to the right one
        we = (profile(1.0) if profile else w1) * 0.5
        if we > 0.3:
            a = math.atan2(left[-1][1] - sp[-1][1], left[-1][0] - sp[-1][0])
            _arc_neg(ptr, sp[-1][0], sp[-1][1], we, a, a - math.pi)
    rr = right[::-1]
    if smooth_spine and m > 2:
        smooth_open(cr, rr, move=False)
    else:
        for p in rr:
            _line_to(ptr, p[0], p[1])
    if cap:
        ws = (profile(0.0) if profile else w0) * 0.5
        if ws > 0.3:
            a = math.atan2(left[0][1] - sp[0][1], left[0][0] - sp[0][0])
            _arc_neg(ptr, sp[0][0], sp[0][1], ws, a + math.pi, a)
    _close(ptr)


def star(cr, cx, cy, r_out, r_in, n=5, angle=-math.pi / 2):
    pts = []
    for i in range(2 * n):
        r = r_out if i % 2 == 0 else r_in
        a = angle + math.pi * i / n
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    polygon(cr, pts)


def convex_hull(points):
    """Andrew's monotone chain; returns hull points counter-clockwise (screen y-down: clockwise)."""
    pts = sorted(set(points))
    if len(pts) <= 2:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


# ----------------------------------------------------------------------------------------
# 7. gradients
# ----------------------------------------------------------------------------------------


def _norm_stops(stops):
    """Accept [c0, c1, ...] (evenly spaced) or [(offset, c), ...]."""
    out = []
    if not stops:
        return out
    first = stops[0]
    if isinstance(first, str) or (isinstance(first, (tuple, list)) and len(first) in (3, 4)
                                  and all(isinstance(v, (int, float)) for v in first)):
        n = len(stops)
        return [(i / max(1, n - 1), s) for i, s in enumerate(stops)]
    return [(float(o), c) for o, c in stops]


def linear(x0, y0, x1, y1, stops):
    """Linear gradient pattern. stops: [c0, c1, ...] or [(offset, color), ...]."""
    pat = cairo.LinearGradient(x0, y0, x1, y1)
    for off, c in _norm_stops(stops):
        c = col(c)
        if len(c) > 3:
            pat.add_color_stop_rgba(off, c[0], c[1], c[2], c[3])
        else:
            pat.add_color_stop_rgb(off, c[0], c[1], c[2])
    return pat


def radial(cx, cy, r, stops, r0=0.0, fx=None, fy=None):
    """Radial gradient pattern from (fx, fy, r0) [default: the center] out to (cx, cy, r).

    Note: full-frame radial gradients are expensive (~45 ms at 1080p); fill only the circle
    you need, or cache the result (see fx.Layer / fx.vignette)."""
    pat = cairo.RadialGradient(cx if fx is None else fx, cy if fy is None else fy, r0, cx, cy, r)
    for off, c in _norm_stops(stops):
        c = col(c)
        if len(c) > 3:
            pat.add_color_stop_rgba(off, c[0], c[1], c[2], c[3])
        else:
            pat.add_color_stop_rgb(off, c[0], c[1], c[2])
    return pat


def vgrad(cr, x, y, w, h, stops):
    """Fill a rectangle with a vertical gradient (top -> bottom)."""
    cr.rectangle(x, y, w, h)
    cr.set_source(linear(x, y, x, y + h, stops))
    cr.fill()


def hgrad(cr, x, y, w, h, stops):
    cr.rectangle(x, y, w, h)
    cr.set_source(linear(x, y, x + w, y, stops))
    cr.fill()


# ----------------------------------------------------------------------------------------
# 8. text (cairo toy text API; fonts installed via fontconfig)
# ----------------------------------------------------------------------------------------

SERIF = "Cormorant Garamond"      # storybook serif: signs, titles, end card
SERIF_LIGHT = "Cormorant Garamond Light"
SANS = "Inter"                    # captions / UI
SANS_SEMI = "Inter SemiBold"
HAND = "Caveat"                   # handwriting (the note)
HAND2 = "Patrick Hand"
MARKER = "Permanent Marker"       # the SMILE stamp
SIGN = "Bebas Neue"               # condensed signage
SIGN2 = "Oswald"


@functools.lru_cache(maxsize=256)
def _face(family, bold, italic):
    return cairo.ToyFontFace(family,
                             cairo.FONT_SLANT_ITALIC if italic else cairo.FONT_SLANT_NORMAL,
                             cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)


def set_font(cr, size, family=SANS, bold=False, italic=False):
    cr.set_font_face(_face(family, bool(bold), bool(italic)))
    cr.set_font_size(size)


def _advance(cr, s, spacing):
    if not spacing:
        return cr.text_extents(s)[4]
    return sum(cr.text_extents(ch)[4] for ch in s) + spacing * max(0, len(s) - 1)


def measure(cr, s, size, family=SANS, bold=False, italic=False, spacing=0.0):
    """-> (advance_width, ink_height, ink_y_bearing) for a single line."""
    set_font(cr, size, family, bold, italic)
    ext = cr.text_extents(s)
    return _advance(cr, s, spacing), ext[3], ext[1]


def _show(cr, s, spacing):
    if not spacing:
        cr.show_text(s)
        return
    x, y = cr.get_current_point()
    for ch in s:
        cr.move_to(x, y)
        cr.show_text(ch)
        x += cr.text_extents(ch)[4] + spacing


def _text_path(cr, s, spacing):
    if not spacing:
        cr.text_path(s)
        return
    x, y = cr.get_current_point()
    for ch in s:
        cr.move_to(x, y)
        cr.text_path(ch)
        x += cr.text_extents(ch)[4] + spacing


def _origin(cr, s, x, y, align, valign, spacing):
    w = _advance(cr, s, spacing)
    if align == "center":
        x -= w / 2.0
    elif align == "right":
        x -= w
    if valign != "baseline":
        asc, desc = cr.font_extents()[:2]
        if valign == "middle":
            ext = cr.text_extents("Hxg" if s.strip() == "" else s)
            y -= ext[1] + ext[3] / 2.0
        elif valign == "top":
            y += asc
        elif valign == "bottom":
            y -= desc
        elif valign == "cap":       # center on capital height (stable for signage)
            cap = -cr.text_extents("H")[1]
            y += cap / 2.0
    return x, y, w


def text(cr, s, x, y, size, family=SANS, color=(1, 1, 1), align="left", valign="baseline",
         spacing=0.0, bold=False, italic=False, alpha_=1.0, outline=None):
    """Draw one line of text. align: left|center|right. valign: baseline|middle|top|bottom|cap.
    spacing = extra letter-spacing in px. outline = (color, width) strokes behind the fill.
    Returns the advance width."""
    set_font(cr, size, family, bold, italic)
    ox, oy, w = _origin(cr, s, x, y, align, valign, spacing)
    if outline:
        oc, ow = outline
        cr.move_to(ox, oy)
        _text_path(cr, s, spacing)
        src(cr, oc, alpha_)
        cr.set_line_width(ow * 2.0)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)
        cr.stroke()
    cr.move_to(ox, oy)
    src(cr, color, alpha_)
    _show(cr, s, spacing)
    cr.new_path()
    return w


def text_path(cr, s, x, y, size, family=SANS, align="left", valign="baseline", spacing=0.0,
              bold=False, italic=False):
    """Append the outline of the text to the current path (for gradient fills, clips...)."""
    set_font(cr, size, family, bold, italic)
    ox, oy, w = _origin(cr, s, x, y, align, valign, spacing)
    cr.move_to(ox, oy)
    _text_path(cr, s, spacing)
    return w


def wrap(cr, s, width, size, family=SANS, bold=False, italic=False, spacing=0.0):
    """Greedy word wrap -> list of lines that fit in `width`."""
    set_font(cr, size, family, bold, italic)
    lines = []
    for para in s.split("\n"):
        cur = ""
        for word in para.split(" "):
            trial = word if not cur else cur + " " + word
            if _advance(cr, trial, spacing) <= width or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
    return lines


def text_block(cr, s, x, y, width, size, family=SANS, color=(1, 1, 1), align="left",
               line_height=1.25, bold=False, italic=False, spacing=0.0, alpha_=1.0):
    """Wrapped paragraph; (x, y) = top-left of the box (x = center when align='center').
    Returns the block height."""
    lines = wrap(cr, s, width, size, family, bold, italic, spacing)
    set_font(cr, size, family, bold, italic)
    asc = cr.font_extents()[0]
    for i, ln in enumerate(lines):
        text(cr, ln, x, y + asc + i * size * line_height, size, family, color, align, "baseline",
             spacing, bold, italic, alpha_)
    return len(lines) * size * line_height


def rotated_text(cr, s, x, y, angle, size, family=SANS, color=(1, 1, 1), align="center",
                 valign="middle", spacing=0.0, bold=False, italic=False, alpha_=1.0):
    with at(cr, x, y, angle):
        return text(cr, s, 0, 0, size, family, color, align, valign, spacing, bold, italic, alpha_)


def arc_text(cr, s, cx, cy, radius, size, family=SERIF, color=(0, 0, 0), center_angle=-math.pi / 2,
             spacing=0.0, bold=False, italic=False, alpha_=1.0, inside=False):
    """Text along a circular arc centered on `center_angle` (default: top of the circle, reading
    left->right clockwise). inside=True puts the text on the inside reading counter-clockwise
    (an arch below the center, e.g. a smile-shaped banner)."""
    set_font(cr, size, family, bold, italic)
    adv = [cr.text_extents(ch)[4] for ch in s]
    total = sum(adv) + spacing * max(0, len(s) - 1)
    direction = -1.0 if inside else 1.0
    a = center_angle - direction * (total / 2.0) / radius
    src(cr, color, alpha_)
    for ch, w in zip(s, adv):
        mid = a + direction * (w / 2.0) / radius
        with at(cr, cx + math.cos(mid) * radius, cy + math.sin(mid) * radius,
                mid + direction * math.pi / 2):
            cr.move_to(-w / 2.0, (size * 0.35) if not inside else (size * 0.35))
            cr.show_text(ch)
        a += direction * (w + spacing) / radius
    cr.new_path()
    return total


@functools.lru_cache(maxsize=512)
def _glow_bitmap(s, size, family, bold, italic, spacing, radius, gcol):
    """Blurred text mask (premultiplied) + the offset of the text origin inside it."""
    from PIL import Image, ImageFilter
    tmp = new_surface(4, 4)
    tcr = cairo.Context(tmp)
    set_font(tcr, size, family, bold, italic)
    w = _advance(tcr, s, spacing)
    asc, desc = tcr.font_extents()[:2]
    pad = int(radius * 3 + 4)
    sw, sh = int(w + 2 * pad + 2), int(asc + desc + 2 * pad + 2)
    surf = new_surface(sw, sh)
    c2 = cairo.Context(surf)
    set_font(c2, size, family, bold, italic)
    c2.move_to(pad, pad + asc)
    src(c2, gcol)
    _show(c2, s, spacing)
    surf.flush()
    im = Image.frombuffer("RGBA", (sw, sh), bytes(surf.get_data()), "raw", "RGBA", 0, 1)
    im = im.filter(ImageFilter.GaussianBlur(radius))
    data = bytearray(im.tobytes())
    out = cairo.ImageSurface.create_for_data(data, cairo.FORMAT_ARGB32, sw, sh, sw * 4)
    return out, data, pad, pad + asc, w


def glow_text(cr, s, x, y, size, family=SANS, color=(1, 1, 1), glow=None, radius=8.0,
              glow_alpha=0.9, align="left", valign="baseline", spacing=0.0, bold=False,
              italic=False, alpha_=1.0, additive=True, passes=1):
    """Text with a soft blurred glow behind it (cached per string -- cheap per frame).

    glow: glow color (default = color). additive=True adds light (rune text, neon), False
    paints it normally (a dark halo for legibility). passes > 1 stacks the glow for intensity."""
    gcol = tuple(col(glow if glow is not None else color)[:3])
    bmp, _keep, ox, oy, w = _glow_bitmap(s, float(size), family, bool(bold), bool(italic), float(spacing),
                                        float(radius), gcol)
    set_font(cr, size, family, bold, italic)
    tx, ty, _ = _origin(cr, s, x, y, align, valign, spacing)
    cr.save()
    if additive:
        cr.set_operator(cairo.OPERATOR_ADD)
    cr.set_source_surface(bmp, tx - ox, ty - oy)
    for _ in range(max(1, passes)):
        cr.paint_with_alpha(clamp(glow_alpha * alpha_))
    cr.restore()
    cr.move_to(tx, ty)
    src(cr, color, alpha_)
    _show(cr, s, spacing)
    cr.new_path()
    return w
