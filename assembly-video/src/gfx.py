"""Skia drawing helpers, easing, fonts."""
import math
import skia

W, H, FPS = 720, 1280, 24

# ------------------------------------------------------------------ math / easing
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, u):
    return a + (b - a) * u


def smooth(u):
    u = clamp(u)
    return u * u * (3 - 2 * u)


def ramp(t, t0, t1):
    """0 before t0, 1 after t1, smoothstep between."""
    if t1 <= t0:
        return 1.0 if t >= t0 else 0.0
    return smooth((t - t0) / (t1 - t0))


def lin(t, t0, t1):
    if t1 <= t0:
        return 1.0 if t >= t0 else 0.0
    return clamp((t - t0) / (t1 - t0))


def ease_out_back(u, s=1.70158):
    u = clamp(u) - 1
    return u * u * ((s + 1) * u + s) + 1


def ease_out_elastic(u):
    u = clamp(u)
    if u in (0, 1):
        return u
    return 2 ** (-10 * u) * math.sin((u * 10 - 0.75) * (2 * math.pi / 3)) + 1


def pulse(t, t0, dur):
    """bump 0->1->0 over [t0, t0+dur]"""
    if t < t0 or t > t0 + dur:
        return 0.0
    return math.sin(math.pi * (t - t0) / dur)


def hash1(n):
    n = (n << 13) ^ n
    return 1.0 - ((n * (n * n * 15731 + 789221) + 1376312589) & 0x7FFFFFFF) / 1073741824.0


def vnoise(x, seed=0):
    """smooth value noise in [-1,1]"""
    i = math.floor(x)
    f = x - i
    a = hash1(int(i) * 57 + seed * 131)
    b = hash1(int(i + 1) * 57 + seed * 131)
    u = f * f * (3 - 2 * f)
    return a + (b - a) * u


def blink(t, seed=0, period=3.6, dur=0.16):
    """eyelid factor (1 open, 0 closed) with pseudo-random blinks"""
    k = math.floor(t / period)
    best = 1.0
    for kk in (k - 1, k, k + 1):
        tb = kk * period + (0.5 + 0.45 * hash1(kk * 7 + seed * 13)) * period * 0.8
        if tb <= t <= tb + dur:
            best = min(best, 1 - math.sin(math.pi * (t - tb) / dur))
    return best


def saccade(t, seed=0, period=1.3, amp=0.35):
    k = math.floor(t / period + hash1(seed) * 0.5)
    tx = hash1(k * 31 + seed) * amp
    ty = hash1(k * 17 + seed + 5) * amp * 0.5
    return tx, ty


# ------------------------------------------------------------------ color
def col(h, a=1.0):
    if isinstance(h, tuple):
        r, g, b = h[:3]
        return skia.ColorSetARGB(int(clamp(a) * 255), int(r), int(g), int(b))
    h = _hx(h)
    return skia.ColorSetARGB(int(clamp(a) * 255), int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _hx(h):
    h = h.lstrip("#")
    return "".join(ch * 2 for ch in h) if len(h) == 3 else h


def rgb(h):
    h = _hx(h)
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def mix(c1, c2, u):
    a, b = rgb(c1) if isinstance(c1, str) else c1, rgb(c2) if isinstance(c2, str) else c2
    u = clamp(u)
    return tuple(int(a[i] + (b[i] - a[i]) * u) for i in range(3))


def hexs(c):
    return "#%02x%02x%02x" % c if isinstance(c, tuple) else c


# ------------------------------------------------------------------ paints
def fill(c, a=1.0, blur=0):
    p = skia.Paint(AntiAlias=True, Color=col(c, a))
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def stroke(c, w=4, a=1.0, cap="round"):
    return skia.Paint(AntiAlias=True, Color=col(c, a), Style=skia.Paint.kStroke_Style, StrokeWidth=w,
                      StrokeCap=skia.Paint.kRound_Cap if cap == "round" else skia.Paint.kButt_Cap,
                      StrokeJoin=skia.Paint.kRound_Join)


def lin_grad(x0, y0, x1, y1, cols, pos=None, a=1.0):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeLinear([skia.Point(x0, y0), skia.Point(x1, y1)],
                                               [col(c, a) for c in cols], pos))
    return p


def rad_grad(cx, cy, r, cols, pos=None, alphas=None):
    p = skia.Paint(AntiAlias=True)
    if alphas is None:
        alphas = [1.0] * len(cols)
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(cx, cy), max(r, 1), [col(c, a) for c, a in zip(cols, alphas)], pos))
    return p


OUT = "#1b1420"  # outline color


def fs(c, path, fillc, sw=4, outline=OUT, a=1.0):
    """fill + stroke a path"""
    if fillc is not None:
        c.drawPath(path, fill(fillc, a))
    if sw > 0 and outline is not None:
        c.drawPath(path, stroke(outline, sw, a))


def oval(cx, cy, rx, ry):
    p = skia.Path()
    p.addOval(skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry))
    return p


def rrect(x, y, w, h, r):
    p = skia.Path()
    p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r))
    return p


def poly(pts, close=True):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if close:
        p.close()
    return p


def smooth_path(pts, close=True):
    """Catmull-Rom through points -> cubic path"""
    p = skia.Path()
    n = len(pts)
    if n < 3:
        return poly(pts, close)
    p.moveTo(*pts[0])
    rng_ = range(n) if close else range(n - 1)
    for i in rng_:
        p0 = pts[(i - 1) % n] if (close or i > 0) else pts[i]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if (close or i + 2 < n) else pts[(i + 1) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        p.cubicTo(c1[0], c1[1], c2[0], c2[1], p2[0], p2[1])
    if close:
        p.close()
    return p


def blob(cx, cy, r, n=10, wob=0.1, t=0.0, seed=0, sy=1.0):
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        rr = r * (1 + wob * vnoise(t * 1.5 + i * 1.7, seed + i))
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr * sy))
    return smooth_path(pts)


def cloud(cx, cy, w, h, bumps=9, t=0.0, seed=0, wob=0.04):
    pts = []
    for i in range(bumps * 2):
        a = 2 * math.pi * i / (bumps * 2)
        k = 1.0 if i % 2 == 0 else 0.86
        k *= 1 + wob * vnoise(t * 2 + i, seed)
        pts.append((cx + math.cos(a) * w / 2 * k, cy + math.sin(a) * h / 2 * k))
    return smooth_path(pts)


# ------------------------------------------------------------------ text
_TF = {}


def typeface(name):
    if name not in _TF:
        if name == "bangers":
            _TF[name] = skia.Typeface.MakeFromFile("fonts/Bangers-Regular.ttf")
        elif name == "fredoka":
            _TF[name] = skia.Typeface.MakeFromFile("fonts/fredoka_bold.ttf")
        elif name == "fredoka_semi":
            _TF[name] = skia.Typeface.MakeFromFile("fonts/fredoka.ttf")
        elif name == "inter_bold":
            _TF[name] = skia.Typeface("Inter", skia.FontStyle(700, 5, skia.FontStyle.kUpright_Slant))
        elif name == "inter_black":
            _TF[name] = skia.Typeface("Inter", skia.FontStyle(900, 5, skia.FontStyle.kUpright_Slant))
        elif name == "mono":
            _TF[name] = skia.Typeface("DejaVu Sans Mono", skia.FontStyle.Bold())
        else:
            _TF[name] = skia.Typeface("Inter", skia.FontStyle.Normal())
    return _TF[name]


def font(name, size):
    f = skia.Font(typeface(name), size)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    return f


def text_w(s, name, size):
    return font(name, size).measureText(s)


def text(c, s, x, y, name="fredoka", size=40, color="#ffffff", align="center", outline=None, ow=6, a=1.0, shadow=False):
    f = font(name, size)
    w = f.measureText(s)
    if align == "center":
        x -= w / 2
    elif align == "right":
        x -= w
    if shadow:
        c.drawString(s, x + 4, y + 5, f, fill("#000000", 0.45 * a))
    if outline:
        c.drawString(s, x, y, f, stroke(outline, ow, a))
    c.drawString(s, x, y, f, fill(color, a))
    return w


def wrap(s, name, size, maxw):
    words = s.split()
    lines, cur = [], ""
    for w_ in words:
        cand = (cur + " " + w_).strip()
        if text_w(cand, name, size) <= maxw or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def starburst(c, cx, cy, r1, r2, n=14, fillc="#ffd23f", rot=0.0, sw=5):
    pts = []
    for i in range(n * 2):
        a = rot + math.pi * i / n
        r = r1 if i % 2 == 0 else r2
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    fs(c, poly(pts), fillc, sw)


def comic_text(c, s, x, y, size=90, color="#ffd23f", t=0.0, t0=0.0, rot=-6, burst=True, bcol="#e63946"):
    u = clamp((t - t0) / 0.25)
    if u <= 0:
        return
    sc = ease_out_back(u, 2.5)
    c.save()
    c.translate(x, y)
    c.rotate(rot + 3 * math.sin(t * 20) * (1 - u))
    c.scale(sc, sc)
    if burst:
        w = text_w(s, "bangers", size)
        starburst(c, 0, -size * 0.35, w * 0.75, w * 0.48, 16, bcol, t * 0.5)
    text(c, s, 0, 0, "bangers", size, color, outline=OUT, ow=12)
    c.restore()


def speed_lines(c, cx, cy, t, n=40, color="#ffffff", a=0.25, r0=260, seed=0):
    for i in range(n):
        ang = 2 * math.pi * (i + 0.5 * hash1(i + seed)) / n
        flick = 0.5 + 0.5 * math.sin(t * 25 + i * 3.1)
        r_a = r0 + 60 * flick
        r_b = 1200
        p = skia.Path()
        dx, dy = math.cos(ang), math.sin(ang)
        px, py = -dy, dx
        wdt = 6 + 10 * hash1(i * 3 + seed)
        p.moveTo(cx + dx * r_a, cy + dy * r_a)
        p.lineTo(cx + dx * r_b + px * wdt, cy + dy * r_b + py * wdt)
        p.lineTo(cx + dx * r_b - px * wdt, cy + dy * r_b - py * wdt)
        p.close()
        c.drawPath(p, fill(color, a * flick))


def vignette(c, a=0.6, color="#000000", r=900):
    c.drawRect(skia.Rect.MakeWH(W, H), rad_grad(W / 2, H / 2, r, [color, color], [0.45, 1.0], [0.0, a]))


def black(c, a):
    if a > 0:
        c.drawRect(skia.Rect.MakeWH(W, H), fill("#000000", a))


def iris(c, cx, cy, r):
    """black everywhere except a circle"""
    p = skia.Path()
    p.addRect(skia.Rect.MakeWH(W, H))
    p.addCircle(cx, cy, max(r, 0.1))
    p.setFillType(skia.PathFillType.kEvenOdd)
    c.drawPath(p, fill("#000000"))
