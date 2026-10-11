"""2D character rig drawn with Skia.

Head-local units: head is ~100 wide (x -50..50), crown at y=-72, chin at y=+64.
Faces turn (yaw), nod (pitch) and tilt (roll); features are projected on a
sphere so a turn shifts and foreshortens them like a real head.
"""
import math
import numpy as np
import skia

# ----------------------------------------------------------------- colour ---

def hx(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def mix(a, b, t):
    a, b = (hx(a) if isinstance(a, str) else a), (hx(b) if isinstance(b, str) else b)
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def c4(c, a=1.0):
    r, g, b = hx(c) if isinstance(c, str) else c
    return skia.Color4f(r, g, b, a)


def P(c='#000000', a=1.0, stroke=0.0, blur=0.0, cap=True, blend=None, shader=None):
    p = skia.Paint()
    p.setAntiAlias(True)
    p.setColor4f(c4(c, a))
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        if cap:
            p.setStrokeCap(skia.Paint.kRound_Cap)
            p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if blend is not None:
        p.setBlendMode(blend)
    if shader is not None:
        p.setShader(shader)
    return p


def lin(p0, p1, cols, pos=None):
    return skia.GradientShader.MakeLinear([skia.Point(*p0), skia.Point(*p1)],
                                          [c4(c, a).toColor() for c, a in cols], pos)


def rad(ctr, r, cols, pos=None):
    return skia.GradientShader.MakeRadial(skia.Point(*ctr), r,
                                          [c4(c, a).toColor() for c, a in cols], pos)

# ------------------------------------------------------------------ paths ---

def smooth(pts, closed=True, tension=0.5):
    """Catmull-Rom spline through points -> skia.Path."""
    p = skia.Path()
    n = len(pts)
    if n < 2:
        return p
    p.moveTo(*pts[0])
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = pts[(i - 1) % n] if (closed or i > 0) else pts[i]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if (closed or i + 2 < n) else p2
        k = tension / 3 * 2
        c1 = (p1[0] + (p2[0] - p0[0]) * k / 2, p1[1] + (p2[1] - p0[1]) * k / 2)
        c2 = (p2[0] - (p3[0] - p1[0]) * k / 2, p2[1] - (p3[1] - p1[1]) * k / 2)
        p.cubicTo(*c1, *c2, *p2)
    if closed:
        p.close()
    return p


def poly(pts, closed=True):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if closed:
        p.close()
    return p


def bez(p0, p1, p2, p3, n=16):
    t = np.linspace(0, 1, n)[:, None]
    a, b, c, d = map(np.array, (p0, p1, p2, p3))
    return ((1 - t) ** 3 * a + 3 * (1 - t) ** 2 * t * b + 3 * (1 - t) * t * t * c + t ** 3 * d)


def qbez(p0, p1, p2, n=16):
    t = np.linspace(0, 1, n)[:, None]
    a, b, c = map(np.array, (p0, p1, p2))
    return (1 - t) ** 2 * a + 2 * (1 - t) * t * b + t * t * c


def tapered(pts, w0, w1, wmid=None):
    """Filled stroke along polyline with width tapering w0 -> w1."""
    pts = np.asarray(pts, float)
    n = len(pts)
    d = np.gradient(pts, axis=0)
    nrm = np.stack([-d[:, 1], d[:, 0]], 1)
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-9
    s = np.linspace(0, 1, n)
    if wmid is None:
        w = w0 + (w1 - w0) * s
    else:
        w = np.where(s < 0.5, w0 + (wmid - w0) * s * 2, wmid + (w1 - wmid) * (s - 0.5) * 2)
    left = pts + nrm * (w[:, None] / 2)
    right = pts - nrm * (w[:, None] / 2)
    return smooth([tuple(q) for q in np.concatenate([left, right[::-1]])], closed=True, tension=0.3)


def lerp(a, b, t):
    return a + (b - a) * t


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)

# ------------------------------------------------------------------ noise ---

class Noise:
    """Cheap smooth 1D noise from summed sines (deterministic per seed)."""

    def __init__(self, seed):
        r = np.random.default_rng(seed)
        self.f = r.uniform(0.6, 1.7, 4)
        self.ph = r.uniform(0, 6.28, 4)
        self.a = np.array([0.5, 0.27, 0.15, 0.08])

    def __call__(self, t, speed=1.0):
        return float(np.sum(self.a * np.sin(self.f * t * speed + self.ph)))


class Blinker:
    def __init__(self, seed, mean=3.6):
        r = np.random.default_rng(seed)
        t, self.times = 0.4, []
        while t < 400:
            t += r.uniform(mean * 0.45, mean * 1.5)
            self.times.append(t)
        self.times = np.array(self.times)

    def __call__(self, t, extra=()):
        """Return lid factor 1=open, 0=closed."""
        best = 1.0
        for bt in list(self.times[(self.times > t - 0.4) & (self.times < t + 0.1)]) + list(extra):
            d = t - bt
            if 0 <= d < 0.07:
                v = 1 - d / 0.07
            elif 0.07 <= d < 0.12:
                v = 0.0
            elif 0.12 <= d < 0.26:
                v = (d - 0.12) / 0.14
            else:
                continue
            v = 1 - ease(1 - v) if d >= 0.12 else v
            best = min(best, v)
        return best


class Saccade:
    """Micro eye movements: small fixation jumps every ~0.6-2.2 s."""

    def __init__(self, seed, amp=0.12):
        r = np.random.default_rng(seed + 99)
        t, self.ev = 0.0, []
        while t < 400:
            t += r.uniform(0.6, 2.2)
            self.ev.append((t, r.normal(0, amp), r.normal(0, amp * 0.6)))

    def __call__(self, t):
        x = y = 0.0
        for tt, dx, dy in self.ev:
            if tt > t:
                break
            k = clamp((t - tt) / 0.05)
            x, y = lerp(x, dx, k), lerp(y, dy, k)
        return x, y

# ------------------------------------------------------------- face state ---

DEFAULT = dict(
    yaw=0.0, pitch=0.0, roll=0.0,
    open_l=1.0, open_r=1.0, lower=0.0, gx=0.0, gy=0.0,
    b_in=0.0, b_out=0.0, knit=0.0, b_asym=0.0,
    m_open=0.0, m_wide=1.0, smile=0.0, smirk=0.0, m_round=0.0, tremble=0.0,
    wet=0.0, flush=0.0, strain=0.0, tears=(), breath=0.0, sag=0.0,
    light=(-0.6, -0.8),
)


class Design:
    def __init__(self, **kw):
        self.skin = '#b07a55'
        self.shade = '#7a4a32'
        self.hi = '#d9a27c'
        self.lip = '#9a5248'
        self.iris = '#3b2414'
        self.brow = '#2a1a10'
        self.lash = '#1a0f0a'
        self.blush = '#c0503c'
        self.age = 0.0
        self.eye_w = 19.5
        self.eye_h = 9.2
        self.eye_y = 0.0
        self.eye_x = 20.0
        self.brow_w = 3.2
        self.fem = 0.0
        self.jaw = 1.0       # jaw width factor
        self.chin = 64.0
        self.ears = True
        self.layers_back = []   # callables(canvas, face, st)
        self.layers_body = []
        self.layers_mid = []    # after skin, before features (beard base)
        self.layers_front = []  # after features (hair, veil, glasses)
        self.layers_over_mouth = []
        self.layers_skin = []
        self.layers_hands = []
        self.stubble = 0.0
        self.stubble_c = '#3a2a22'
        self.__dict__.update(kw)


class Face:
    """Projection helper bound to one character state."""

    def __init__(self, d, st):
        self.d, self.st = d, st
        self.yaw, self.pitch = st['yaw'], st['pitch']
        self.jawdrop = st['m_open'] * 11.0

    def pr(self, x, y, depth=0.0):
        R, Rv = 54.0, 78.0
        ph = math.asin(clamp(x / R, -0.999, 0.999))
        th = math.asin(clamp(y / Rv, -0.999, 0.999))
        X = R * math.sin(ph + self.yaw) + depth * math.sin(self.yaw)
        Y = Rv * math.sin(th - self.pitch) - depth * math.sin(self.pitch) * 0.6
        return X, Y

    def sx(self, x):
        R = 54.0
        ph = math.asin(clamp(x / R, -0.999, 0.999))
        return max(0.08, math.cos(ph + self.yaw)) / max(0.3, math.cos(ph))

    def sy(self, y):
        Rv = 78.0
        th = math.asin(clamp(y / Rv, -0.999, 0.999))
        return max(0.2, math.cos(th - self.pitch)) / max(0.3, math.cos(th))

    def outline(self):
        d = self.d
        jd = self.jawdrop
        ch = d.chin + jd
        jw = d.jaw
        base = [(0, -72), (30, -67), (47, -48), (52, -20), (51, 2), (48, 22),
                (40 * jw, 40 + jd * 0.4), (26 * jw, 54 + jd * 0.8), (12, ch - 2), (0, ch),
                (-12, ch - 2), (-26 * jw, 54 + jd * 0.8), (-40 * jw, 40 + jd * 0.4), (-48, 22),
                (-51, 2), (-52, -20), (-47, -48), (-30, -67)]
        out = []
        for x, y in base:
            k = clamp((y + 10) / 70, 0, 1)            # lower face follows the turn more
            X = x * (1 - 0.07 * abs(self.yaw)) + 54 * math.sin(self.yaw) * (0.15 + 0.45 * k)
            if (x > 0) == (self.yaw > 0) and abs(x) > 30:
                X += 6 * self.yaw * (1 if x > 0 else -1) * 0  # near side unchanged
            Y = y - 20 * math.sin(self.pitch) * k
            out.append((X, Y))
        return smooth(out, True, 0.55)


# ------------------------------------------------------------- features ---

def draw_eye(cv, f, side, st, t):
    d = f.d
    ex, ey = d.eye_x * side, d.eye_y
    X, Y = f.pr(ex, ey, 2)
    sxf = f.sx(ex) * (1.0 if side * f.yaw >= 0 else 1.0)
    syf = f.sy(ey)
    opn = st['open_l'] if side < 0 else st['open_r']
    low = st['lower']
    ew, eh = d.eye_w, d.eye_h
    cv.save()
    cv.translate(X, Y)
    cv.scale(sxf * side, syf)
    # socket shadow
    cv.drawOval(skia.Rect(-ew * 0.9, -eh * 2.6, ew * 0.9, eh * 1.6),
                P(d.shade, 0.10 + 0.28 * d.age + 0.2 * st['strain'], blur=5))
    if st['flush'] > 0:
        cv.drawOval(skia.Rect(-ew * 0.7, -eh * 0.5, ew * 0.7, eh * 2.0), P(d.blush, 0.35 * st['flush'], blur=4))

    wide = max(0.0, opn - 1.0)
    o = clamp(opn, 0, 1)
    I = (-ew / 2, 1.0)
    O = (ew / 2, -1.2 + 0.6 * d.fem)
    up_top = -eh * (1.0 + 0.45 * wide)
    lo_bot = eh * 0.72
    lo_raise = lerp(lo_bot, eh * 0.05, low * 0.75)
    lid_y = lerp(lo_raise - 0.4, up_top, o)

    def upper(yc):
        return bez(I, (-ew * 0.22, yc), (ew * 0.22, yc * 1.04), O, 18)

    def lower(yc):
        return bez(O, (ew * 0.25, yc), (-ew * 0.2, yc * 0.98), I, 18)

    lid_curve = upper(lid_y)
    lower_curve = lower(lo_raise)
    ap = np.concatenate([lid_curve, lower_curve[1:]])
    ap_path = poly([tuple(q) for q in ap])
    visible = o > 0.04
    if visible:
        cv.save()
        cv.clipPath(ap_path, doAntiAlias=True)
        cv.drawPaint(P('#efe7dc'))
        cv.drawOval(skia.Rect(-ew * 0.7, -eh * 0.4, ew * 0.7, eh * 1.4), P('#d8c8b8', 0.6, blur=3))
        gx, gy = st['gx'] * side, st['gy']
        ir = eh * 0.86
        cx, cy = gx * ew * 0.27 - 0.6, gy * eh * 0.55 - 0.6
        cv.drawCircle(cx, cy, ir, P(d.iris))
        cv.drawCircle(cx, cy, ir, P(mix(d.iris, '#000000', 0.5), stroke=1.1))
        cv.drawCircle(cx + 0.6, cy + ir * 0.35, ir * 0.55, P(mix(d.iris, '#ffffff', 0.25), 0.35, blur=1.2))
        cv.drawCircle(cx, cy, ir * 0.42, P('#0b0706'))
        # lid shadow on eyeball
        cv.drawRect(skia.Rect(-ew, lid_y * 0.75 - 6, ew, lid_y * 0.75 + 2.5), P('#3a2418', 0.35, blur=2.2))
        # catch lights (image-space light from upper-left)
        cv.drawCircle(cx - 2.0 * side, cy - 2.2, 1.55 + 0.4 * st['wet'], P('#ffffff', 0.95))
        cv.drawCircle(cx + 2.3 * side, cy + 1.6, 0.7, P('#ffffff', 0.55 + 0.4 * st['wet']))
        if st['wet'] > 0:
            # wet lower rim glint
            cv.drawPath(poly([tuple(q) for q in lower_curve[3:-3]], False), P('#ffffff', 0.5 * st['wet'], stroke=1.0))
        cv.restore()
        # waterline redness
        if st['flush'] > 0.1:
            cv.drawPath(poly([tuple(q) for q in lower_curve[2:-2]], False),
                        P('#c4645a', 0.5 * st['flush'], stroke=1.2))
    # crease
    crease = upper(lerp(up_top - eh * 0.45, lid_y - eh * 0.9, 0.35)) + np.array([0, -eh * 0.35])
    cv.drawPath(poly([tuple(q) for q in crease[3:-2]], False), P(d.shade, 0.5, stroke=1.0))
    # lash line
    lw = 1.9 + 0.5 * d.fem
    cv.drawPath(tapered(lid_curve, lw * 0.6, lw * 1.3), P(d.lash, 0.95))
    if d.fem > 0.3:
        tip = lid_curve[-1]
        cv.drawPath(tapered([tuple(lid_curve[-3]), tuple(tip), (tip[0] + 2.4, tip[1] - 1.8)], 1.6, 0.4), P(d.lash))
    # lower lid line
    cv.drawPath(poly([tuple(q) for q in lower_curve[2:-3]], False), P(d.shade, 0.55, stroke=0.9))
    # under-eye
    ue = lower(lo_raise + eh * 0.9) + np.array([0, 1.5])
    cv.drawPath(poly([tuple(q) for q in ue[4:-5]], False), P(d.shade, 0.06 + 0.4 * d.age + 0.2 * st['strain'], stroke=0.9))
    if d.age > 0.4:
        for k in (-1, 0, 1):
            cv.drawLine(ew * 0.62, -1 + k * 3.2, ew * 0.62 + 4.5, -2 + k * 4.5, P(d.shade, 0.35 * d.age, stroke=0.8))
    cv.restore()


def brow_pts(f, side, st):
    d = f.d
    ex = d.eye_x * side
    ew = d.eye_w
    bi, bo, kn = st['b_in'], st['b_out'], st['knit']
    sgn = 1 if side > 0 else -1
    bi += st['b_asym'] * sgn * 0.5
    bo += st['b_asym'] * sgn * 0.6
    inner = (ex - sgn * ew * 0.46 - sgn * (-kn * 2.6), d.eye_y - 13.5 - bi * 6.5 + kn * 2.8)
    mid = (ex + sgn * ew * 0.08, d.eye_y - 17.0 - (bi * 0.45 + bo * 0.8) * 5.5 + kn * 1.2)
    outer = (ex + sgn * ew * 0.62, d.eye_y - 12.0 - bo * 5.0 + (bi > 0.3) * bi * 1.5)
    return [f.pr(*inner, 1), f.pr(*mid, 1), f.pr(*outer, 1)]


def draw_brow(cv, f, side, st):
    d = f.d
    a, b, c = brow_pts(f, side, st)
    pts = qbez(a, (2 * b[0] - (a[0] + c[0]) / 2, 2 * b[1] - (a[1] + c[1]) / 2), c, 14)
    w = d.brow_w * min(f.sx(d.eye_x * side) * 1.1, 1.15)
    cv.drawPath(tapered(pts, w * 1.15, w * 0.35, w * 1.0), P(d.brow, 0.95))


def draw_forehead(cv, f, st):
    d = f.d
    k = clamp((st['b_in'] * 0.9 + st['strain'] * 0.4) * (0.45 + 0.6 * d.age) + d.age * 0.3)
    if k > 0.05:
        for i, yy in enumerate((-33, -40, -47)):
            pts = [f.pr(x, yy + abs(x) * 0.06 - (i == 1) * 1.5, 1) for x in np.linspace(-14 + i * 2, 14 - i * 2, 7)]
            cv.drawPath(smooth(pts, False), P(d.shade, 0.32 * k, stroke=1.0))
    kn = st['knit']
    if kn > 0.1:
        for s in (-1, 1):
            a = f.pr(s * 3, -12, 1)
            b = f.pr(s * 4.5, -22, 1)
            cv.drawLine(*a, *b, P(d.shade, 0.5 * kn, stroke=1.1))


def draw_nose(cv, f, st):
    d = f.d
    tip = f.pr(0, 20, 14)
    sh = -1 if st['light'][0] < 0 else 1
    # bridge shadow on the side away from the light
    pts = [f.pr(sh * 4.0, -4, 4), f.pr(sh * 5.5, 8, 9), f.pr(sh * 6.5, 17, 11)]
    cv.drawPath(tapered(qbez(*pts, 10), 0.4, 3.4), P(d.shade, 0.28, blur=1.8))
    # wings
    for s_ in (-1, 1):
        a = f.pr(s_ * 6.5, 14, 9)
        b = f.pr(s_ * 9.2, 20, 8)
        c = f.pr(s_ * 6.0, 24.5, 9)
        cv.drawPath(tapered(qbez(a, b, c, 10), 0.3, 1.5), P(d.shade, 0.55 + 0.1 * (s_ == sh)))
        n = f.pr(s_ * 3.6, 24.3, 11)
        cv.drawOval(skia.Rect(n[0] - 2.4, n[1] - 1.0, n[0] + 2.4, n[1] + 1.1), P(mix(d.shade, '#000000', 0.35), 0.75))
    # tip shading / highlight
    cv.drawOval(skia.Rect(tip[0] - 5, tip[1] + 1, tip[0] + 5, tip[1] + 5.5), P(d.shade, 0.25, blur=1.8))
    cv.drawOval(skia.Rect(tip[0] - 3.2, tip[1] - 4.5, tip[0] + 2.0, tip[1] - 0.5), P(d.hi, 0.5, blur=1.4))
    u = f.pr(0, 28, 6)
    cv.drawOval(skia.Rect(u[0] - 8, u[1] - 1.5, u[0] + 8, u[1] + 2), P(d.shade, 0.22, blur=2))


def mouth_geom(f, st, t):
    d = f.d
    o = st['m_open']
    w = st['m_wide']
    s = st['smile']
    r = st['m_round']
    trem = st['tremble'] * (math.sin(t * 37) * 0.6 + math.sin(t * 23.3) * 0.4)
    hw = 12.0 * w * (1 - 0.32 * r) * (1 + 0.1 * s)
    cy = 39 + f.jawdrop * 0.35
    sk = st['smirk']
    cl = (-hw, cy - s * 3.6 + o * 1.2 + sk * 1.0)
    cr = (hw * (1 + 0.12 * sk), cy - s * 3.6 + o * 1.2 - sk * 4.5)
    top_in = cy - o * 4.0 - r * 1.2 + s * 0.6
    bot_in = cy + o * 16.5 + r * 2.0 + trem * 1.2 - s * 0.4
    top_out = top_in - 3.6 - 0.6 * d.fem
    bot_out = bot_in + 4.6 + 0.6 * d.fem - o * 0.8
    return cl, cr, cy, top_in, bot_in, top_out, bot_out, hw, o


def draw_mouth(cv, f, st, t):
    d = f.d
    cl, cr, cy, ti, bi, to, bo, hw, o = mouth_geom(f, st, t)

    def P2(x, y):
        return f.pr(x, y, 8 - abs(x) * 0.2)

    cl2, cr2 = P2(*cl), P2(*cr)
    # interior
    up_in = [cl2, P2(-hw * 0.5, ti + 0.4), P2(0, ti), P2(hw * 0.5, ti + 0.4), cr2]
    lo_in = [cr2, P2(hw * 0.5, bi - (bi - cy) * 0.2), P2(0, bi), P2(-hw * 0.5, bi - (bi - cy) * 0.2), cl2]
    if o > 0.04:
        inner = smooth(up_in + lo_in[1:-1], True, 0.5)
        cv.drawPath(inner, P('#2a1210'))
        cv.save()
        cv.clipPath(inner, doAntiAlias=True)
        th = min(4.2, o * 11)
        tt = P2(0, ti)
        cv.drawRect(skia.Rect(tt[0] - hw * 0.62, tt[1] - 3, tt[0] + hw * 0.62, tt[1] + th), P('#e9e0d2'))
        cv.drawLine(tt[0] - hw, tt[1] + th, tt[0] + hw, tt[1] + th, P('#b8aa98', 0.6, stroke=0.6))
        if o > 0.25:
            bb = P2(0, bi)
            cv.drawOval(skia.Rect(bb[0] - hw * 0.6, bb[1] - 6 * o, bb[0] + hw * 0.6, bb[1] + 4), P('#8a3a36'))
        cv.restore()
    # lips
    up_out = [cl2, P2(-hw * 0.55, to + 1.0), P2(-hw * 0.14, to - 0.5), P2(0, to + 0.8),
              P2(hw * 0.14, to - 0.5), P2(hw * 0.55, to + 1.0), cr2]
    lo_out = [cr2, P2(hw * 0.55, bo - 1.2), P2(0, bo), P2(-hw * 0.55, bo - 1.2), cl2]
    lipc = d.lip
    upper_lip = smooth(up_out + up_in[::-1][1:-1], True, 0.45)
    lower_lip = smooth(lo_out + lo_in[::-1][1:-1], True, 0.45)
    cv.drawPath(upper_lip, P(mix(lipc, d.shade, 0.25)))
    cv.drawPath(lower_lip, P(lipc))
    bm = P2(0, (bi + bo) / 2 - 0.6)
    cv.drawOval(skia.Rect(bm[0] - hw * 0.35, bm[1] - 1.2, bm[0] + hw * 0.3, bm[1] + 1.0), P('#ffffff', 0.18, blur=1))
    # lip line
    cv.drawPath(smooth(up_in, False, 0.5), P(mix(lipc, '#2a1210', 0.6), 0.9, stroke=1.2))
    if o <= 0.04:
        pass
    # corners
    for c, sgn in ((cl2, -1), (cr2, 1)):
        dy = -st['smile'] * 2.6
        cv.drawLine(c[0], c[1], c[0] + sgn * 2.0, c[1] + dy + 1.0, P(d.shade, 0.55, stroke=1.0))
    # chin shadow under lower lip
    ch = P2(0, bo + 4.5)
    cv.drawOval(skia.Rect(ch[0] - 6, ch[1] - 1.6, ch[0] + 6, ch[1] + 1.8), P(d.shade, 0.25, blur=2))


def draw_folds(cv, f, st):
    d = f.d
    k = clamp(0.25 + d.age * 0.6 + max(st['smile'], 0) * 0.6 + st['strain'] * 0.5 + st['b_in'] * 0.15)
    for s in (-1, 1):
        pts = [f.pr(s * 10, 20, 6), f.pr(s * 16, 31, 4), f.pr(s * 17.5 + s * f.jawdrop * 0.1, 42 + f.jawdrop * 0.5, 2)]
        cv.drawPath(tapered(qbez(*pts, 10), 1.3, 0.3), P(d.shade, 0.35 * k, blur=0.6))


def draw_tears(cv, f, st, t):
    d = f.d
    for (side, prog, alpha) in st['tears']:
        if alpha <= 0:
            continue
        ex = d.eye_x * side + side * 3
        path_pts = [f.pr(ex, d.eye_y + 6, 3), f.pr(ex + side * 3, 18, 3), f.pr(ex + side * 4, 34, 2),
                    f.pr(ex + side * 2, 50, 1)]
        pts = bez(*path_pts, 24)
        k = int(clamp(prog) * 23)
        if k >= 1:
            cv.drawPath(poly([tuple(q) for q in pts[:k + 1]], False), P('#ffffff', 0.32 * alpha, stroke=1.6))
            cv.drawPath(poly([tuple(q) for q in pts[:k + 1]], False), P(d.shade, 0.18 * alpha, stroke=0.6))
        x, y = pts[k]
        cv.drawOval(skia.Rect(x - 1.8, y - 2.2, x + 1.8, y + 2.4), P('#dfe8ef', 0.7 * alpha))
        cv.drawCircle(x - 0.6, y - 0.8, 0.7, P('#ffffff', 0.95 * alpha))


def draw_character(cv, d, st, t):
    """Draw a character with head at origin (head units). Body hangs below."""
    s = dict(DEFAULT)
    s.update(st)
    st = s
    f = Face(d, st)
    br = st['breath']
    hx_, hy_ = st.get('hx', 0.0), st.get('hy', 0.0)

    def head_tf():
        cv.translate(hx_, hy_ - br * 1.0)
        cv.translate(0, 45)
        cv.rotate(st['roll'])
        cv.translate(0, -45)

    cv.save(); head_tf()
    for L in d.layers_back:
        L(cv, f, st, t)
    cv.restore()
    cv.save(); cv.translate(0, -br * 2.2)
    for L in d.layers_body:
        L(cv, f, st, t)
    cv.restore()
    cv.save(); head_tf()
    draw_head(cv, d, f, st, t)
    cv.restore()
    cv.save(); cv.translate(0, -br * 2.2)
    for L in d.layers_hands:
        L(cv, f, st, t)
    cv.restore()
    return f


def draw_head(cv, d, f, st, t):
    if d.ears:
        for side in (-1, 1):
            vis = math.cos(math.asin(0.93) + f.yaw * side)
            if vis < 0.02:
                continue
            ex, ey = f.pr(side * 50, 4)
            w = 9 * clamp(vis * 1.6, 0.25, 1)
            ear = smooth([(ex, ey - 13), (ex + side * w, ey - 10), (ex + side * w * 0.9, ey + 6),
                          (ex + side * 2, ey + 13), (ex - side * 3, ey)], True)
            cv.drawPath(ear, P(d.skin))
            cv.drawPath(ear, P(d.shade, 0.35, stroke=1.2))
            cv.drawLine(ex + side * w * 0.3, ey - 6, ex + side * w * 0.5, ey + 5, P(d.shade, 0.4, stroke=1.2))
    head = f.outline()
    cv.drawPath(head, P(d.skin))
    cv.save()
    cv.clipPath(head, doAntiAlias=True)
    lx, ly = st['light']
    cv.drawPaint(P(shader=lin((-60 * lx, -60 * ly), (60 * lx, 60 * ly),
                                 [(d.shade, 0.0), (d.shade, 0.12), (d.shade, 0.55)], [0, 0.5, 1])))
    cv.drawOval(skia.Rect(-38 + f.yaw * 30, -60, 10 + f.yaw * 30, -20), P(d.hi, 0.35, blur=10))
    jd = f.jawdrop
    cv.drawOval(skia.Rect(-40, 52 + jd, 40, 80 + jd), P(d.shade, 0.3, blur=6))
    if d.stubble > 0:
        cv.drawPath(stubble_path(f), P(d.stubble_c, d.stubble, blur=3))
    for s_ in (-1, 1):
        cx, cy = f.pr(s_ * 24, 20, 3)
        cv.drawOval(skia.Rect(cx - 11, cy - 6, cx + 11, cy + 7),
                    P(d.blush, 0.10 + 0.25 * st['flush'], blur=6))
    nose_r = f.pr(0, 20, 12)
    cv.drawOval(skia.Rect(nose_r[0] - 5, nose_r[1] - 4, nose_r[0] + 5, nose_r[1] + 4),
                P(d.blush, 0.08 + 0.3 * st['flush'], blur=3))
    for L in d.layers_skin:
        L(cv, f, st, t)
    cv.restore()
    cv.drawPath(head, P(d.shade, 0.5, stroke=0.9))
    for L in d.layers_mid:
        L(cv, f, st, t)
    draw_forehead(cv, f, st)
    draw_folds(cv, f, st)
    draw_nose(cv, f, st)
    for side in (-1, 1):
        draw_eye(cv, f, side, st, t)
    draw_tears(cv, f, st, t)
    for side in (-1, 1):
        draw_brow(cv, f, side, st)
    draw_mouth(cv, f, st, t)
    for L in d.layers_over_mouth:
        L(cv, f, st, t)
    for L in d.layers_front:
        L(cv, f, st, t)


def stubble_path(f):
    jd = f.jawdrop
    pts = [f.pr(-47, 14), f.pr(-30, 30), f.pr(-16, 34 + jd * 0.3), f.pr(0, 31), f.pr(16, 34 + jd * 0.3),
           f.pr(30, 30), f.pr(47, 14)]
    ol = [hp(f, x, y) for x, y in [(44, 36), (26, 56), (0, 70), (-26, 56), (-44, 36)]]
    return smooth(pts + ol, True)


def hp(f, x, y, follow=1.0):
    """Project a hair/cloth point attached to the head outline."""
    jd = f.jawdrop if y > 30 else 0
    y = y + (jd * clamp((y - 30) / 34) if y > 30 else 0)
    k = clamp((y + 10) / 70, 0, 1)
    X = x * (1 - 0.07 * abs(f.yaw)) + 54 * math.sin(f.yaw) * (0.15 + 0.45 * k) * follow
    Y = y - 20 * math.sin(f.pitch) * k - 8 * math.sin(f.pitch) * (1 - k) * (y < -40)
    return X, Y
