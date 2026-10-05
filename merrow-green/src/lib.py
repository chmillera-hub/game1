import math, random, re, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from script import LINES

K = 2
W, H = 1280, 720
GY, GL, GR = 560, 540, 740          # ground y, river gap left/right edges
FPS = 24

# ---------- timeline ----------
DURS = json.load(open('durs.json'))
LEAD = [3.4] + [1.0] * 12
TAIL = [2.3] * 13
TAIL[12] = 6.5
D = [LEAD[i] + DURS[i] + TAIL[i] for i in range(13)]
T0 = [sum(D[:i]) for i in range(13)]
TOTAL = sum(D)

def sentences(i):
    parts = re.split(r'(?<=[.!?])\s+', LINES[i])
    tot = sum(len(p) for p in parts)
    out, acc = [], 0
    for p in parts:
        s = LEAD[i] + DURS[i] * acc / tot
        acc += len(p)
        e = LEAD[i] + DURS[i] * acc / tot
        out.append((s, e, p))
    return out

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x):
    x = clamp(x); return x * x * (3 - 2 * x)
def lerp(a, b, t): return a + (b - a) * t
def lerpc(a, b, t): return tuple(int(lerp(a[j], b[j], t)) for j in range(3))
def ramp(u, a, b): return ease((u - a) / (b - a))

# ---------- canvas ----------
_fonts = {}
def F(sz, bold=False, serif=False):
    key = (sz, bold, serif)
    if key not in _fonts:
        base = '/usr/share/fonts/truetype/dejavu/DejaVu'
        name = ('Serif' if serif else 'Sans') + ('-Bold' if bold else '') + '.ttf'
        _fonts[key] = ImageFont.truetype(base + name, int(sz * K))
    return _fonts[key]

_gl = {}
def glow_mask(r, a):
    key = (int(r), round(a * 8) / 8)
    if key not in _gl:
        if len(_gl) > 400: _gl.clear()
        n = int(2 * key[0] * K)
        yy, xx = np.mgrid[-1:1:n * 1j, -1:1:n * 1j]
        d = np.sqrt(xx ** 2 + yy ** 2)
        m = np.clip(1 - d, 0, 1) ** 2.2 * key[1] * 255
        _gl[key] = Image.fromarray(m.astype('uint8'), 'L')
    return _gl[key]

class C:
    def __init__(s, w=W, h=H):
        s.w, s.h = w, h
        s.im = Image.new('RGB', (w * K, h * K))
        s.d = ImageDraw.Draw(s.im)
    def reset(s, im):
        s.im = im; s.d = ImageDraw.Draw(im)
    def ell(s, cx, cy, rx, ry=None, fill=None, outline=None, w=1):
        ry = rx if ry is None else ry
        s.d.ellipse([(cx - rx) * K, (cy - ry) * K, (cx + rx) * K, (cy + ry) * K],
                    fill=fill, outline=outline, width=max(1, int(w * K)))
    def rect(s, x0, y0, x1, y1, fill=None, r=0, outline=None, w=1):
        box = [x0 * K, y0 * K, x1 * K, y1 * K]
        if r: s.d.rounded_rectangle(box, radius=r * K, fill=fill, outline=outline, width=max(1, int(w * K)))
        else: s.d.rectangle(box, fill=fill, outline=outline, width=max(1, int(w * K)))
    def poly(s, pts, fill):
        s.d.polygon([(x * K, y * K) for x, y in pts], fill=fill)
    def line(s, pts, w, fill):
        P = [(x * K, y * K) for x, y in pts]
        s.d.line(P, fill=fill, width=max(1, int(w * K)), joint='curve')
        r = w * K / 2
        for p in (P[0], P[-1]):
            s.d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=fill)
    def arc(s, cx, cy, rx, ry, a0, a1, w, fill):
        s.d.arc([(cx - rx) * K, (cy - ry) * K, (cx + rx) * K, (cy + ry) * K], a0, a1, fill=fill, width=max(1, int(w * K)))
    def text(s, x, y, t, sz, fill, anchor='mm', bold=False, serif=False):
        s.d.text((x * K, y * K), t, font=F(sz, bold, serif), fill=fill, anchor=anchor)
    def glow(s, x, y, r, col, a=1.0):
        if a <= 0.02: return
        m = glow_mask(r, a)
        x0, y0 = int((x - r) * K), int((y - r) * K)
        s.im.paste(col, (x0, y0, x0 + m.size[0], y0 + m.size[1]), m)
    def veil(s, x0, y0, x1, y1, col, a):
        box = (int(x0 * K), int(y0 * K), int(x1 * K), int(y1 * K))
        reg = s.im.crop(box)
        s.im.paste(Image.blend(reg, Image.new('RGB', reg.size, col), a), box)
    def paste(s, other, x, y, mask=None):
        s.im.paste(other.im, (int(x * K), int(y * K)), mask)
    def fade(s, col, a):
        if a > 0.001:
            s.reset(Image.blend(s.im, Image.new('RGB', s.im.size, col), clamp(a)))
    def mix(s, other, f):
        s.reset(Image.blend(s.im, other.im, clamp(f)))
    def out(s):
        return s.im.resize((W, H), Image.LANCZOS)

# ---------- backgrounds ----------
SKY = {
    'dawn': ((84, 116, 196), (255, 200, 150)),
    'dusk':  ((26, 24, 70), (232, 124, 96)),
    'night': ((8, 10, 32), (52, 38, 86)),
    'warm':  ((16, 14, 46), (120, 70, 90)),
    'indoor_w': ((70, 46, 40), (110, 74, 56)),
    'indoor_p': ((22, 12, 44), (46, 22, 70)),
}
_sky = {}
def sky(mode):
    if mode not in _sky:
        top, bot = SKY[mode]
        y = np.linspace(0, 1, H * K)[:, None, None] ** 1.3
        arr = np.array(top)[None, None, :] * (1 - y) + np.array(bot)[None, None, :] * y
        arr = np.repeat(arr, W * K, axis=1)
        _sky[mode] = Image.fromarray(arr.astype('uint8'), 'RGB')
    return _sky[mode]

_rng = random.Random(7)
STARS = [(_rng.uniform(0, W), _rng.uniform(0, GY - 150), _rng.uniform(0.6, 1.5), _rng.uniform(0, 6.28)) for _ in range(150)]

def hills(c, t, mode, camx=0):
    cols = {'dusk': [(70, 44, 98), (48, 34, 82)], 'night': [(22, 24, 58), (14, 16, 44)], 'warm': [(40, 30, 70), (26, 22, 56)]}[mode]
    for li, (col, amp, base, sp) in enumerate([(cols[0], 55, GY - 120, 0.2), (cols[1], 40, GY - 60, 0.5)]):
        pts = [(0, H)]
        for x in range(0, W + 20, 20):
            y = base - amp * (0.5 + 0.5 * math.sin((x + camx * sp) / 170.0 + li * 2.1)) - 18 * math.sin((x + camx * sp) / 61.0)
            pts.append((x, y))
        pts.append((W, H))
        c.poly(pts, col)
        if li == 0:    # far windows
            r = random.Random(3)
            for k in range(14):
                hx = r.uniform(30, W - 30)
                hy = base - amp * (0.5 + 0.5 * math.sin((hx + camx * sp) / 170.0)) - 18 * math.sin((hx + camx * sp) / 61.0) + 14
                c.rect(hx - 7, hy - 6, hx + 7, hy + 6, fill=(34, 28, 60) if mode != 'dusk' else (60, 40, 80))
                c.poly([(hx - 9, hy - 6), (hx + 9, hy - 6), (hx, hy - 14)], (30, 24, 54))
                if r.random() < 0.7:
                    c.rect(hx - 2, hy - 2, hx + 2, hy + 2, fill=(255, 205, 110))

def world(c, t, mode='dusk', camx=0, planks=0, moon=None, water=True, bridge_lights=False):
    c.im.paste(sky(mode), (0, 0))
    if mode in ('night', 'warm', 'dusk'):
        sa = {'night': 1.0, 'warm': 0.9, 'dusk': 0.25}[mode]
        for (x, y, r, ph) in STARS:
            b = (0.55 + 0.45 * math.sin(t * 1.6 + ph)) * sa
            v = int(255 * b)
            c.ell(x, y, r, fill=(v, v, min(255, v + 20)))
    if moon:
        mx, my = moon
        c.glow(mx, my, 150, (120, 130, 190), 0.55)
        c.ell(mx, my, 34, fill=(240, 238, 215))
        c.ell(mx - 10, my - 6, 8, fill=(222, 220, 195)); c.ell(mx + 12, my + 10, 5, fill=(222, 220, 195))
    hills(c, t, 'dusk' if mode == 'dusk' else ('warm' if mode == 'warm' else 'night'), camx)
    # banks
    grass = (58, 92, 70) if mode != 'dusk' else (74, 104, 74)
    dirt = (70, 52, 50) if mode != 'dusk' else (96, 68, 58)
    dirt2 = (54, 40, 42) if mode != 'dusk' else (78, 54, 50)
    for (x0, x1) in ((-10, GL), (GR, W + 10)):
        c.rect(x0, GY, x1, H + 10, fill=dirt)
        for yy in range(GY + 40, H, 40):
            c.rect(x0, yy, x1, yy + 6, fill=dirt2)
        c.rect(x0, GY - 2, x1, GY + 22, fill=grass)
    if water:
        wt = (30, 70, 120) if mode == 'dusk' else (14, 28, 70)
        wb = (24, 50, 96) if mode == 'dusk' else (8, 16, 44)
        for yy in range(600, H + 10, 6):
            f = (yy - 600) / (H - 600)
            c.rect(GL, yy, GR, yy + 6, fill=lerpc(wt, wb, f))
        for i in range(10):
            yy = 610 + i * 11
            ox = (t * (18 + i * 3) + i * 37) % 200
            c.line([(GL + ox - 30, yy), (GL + ox, yy)], 2, lerpc(wt, (200, 220, 255), 0.35))
        # shore shade
        c.rect(GL - 2, GY, GL + 4, H, fill=dirt2); c.rect(GR - 4, GY, GR + 2, H, fill=dirt2)

def stars_none(): pass

def planks_draw(c, t, n, drop_t=None):
    """n = float number of planks (0..9)"""
    N = 9
    pw = (GR - GL + 20) / N
    for i in range(N):
        if n > i:
            f = clamp(n - i)
            yoff = (1 - ease(f)) * -60
            x0 = GL - 10 + i * pw
            c.rect(x0 + 1, GY - 4 + yoff, x0 + pw - 1, GY + 8 + yoff, fill=(150, 104, 62), r=1)
            c.line([(x0 + 4, GY - 1 + yoff), (x0 + pw - 5, GY - 1 + yoff)], 1.2, (180, 132, 82))
    if n >= N - 0.2:
        a = clamp(n - N + 0.2)
        for side in (GL - 10, GR + 10):
            c.rect(side - 4, GY - 80, side + 4, GY + 6, fill=(110, 76, 48))
        pts = [(GL - 10, GY - 74)]
        for i in range(1, 21):
            x = GL - 10 + (GR - GL + 20) * i / 20
            pts.append((x, GY - 74 + 20 * math.sin(math.pi * i / 20)))
        c.line(pts, 3, (172, 126, 80))
        for i in range(1, 8):
            x = GL - 10 + (GR - GL + 20) * i / 8
            yy = GY - 74 + 20 * math.sin(math.pi * i / 8)
            c.line([(x, yy), (x, GY - 2)], 1.5, (150, 108, 70))
        for side in (GL - 10, GR + 10):
            lantern(c, side, GY - 90, t, 1.2)

def lantern(c, x, y, t, sc=1.0, a=1.0, col=(255, 190, 90)):
    fl = 0.85 + 0.15 * math.sin(t * 5 + x * 0.13)
    c.glow(x, y, 46 * sc, col, 0.8 * fl * a)
    c.rect(x - 6 * sc, y - 9 * sc, x + 6 * sc, y + 9 * sc, fill=lerpc((90, 60, 40), col, a), r=3 * sc)
    c.rect(x - 4 * sc, y - 13 * sc, x + 4 * sc, y - 9 * sc, fill=(60, 44, 34))
    c.line([(x, y - 14 * sc), (x, y - 19 * sc)], 1, (60, 44, 34))

def string_lanterns(c, t, x0, y0, x1, y1, sag, n, a=1.0):
    pts = []
    for i in range(41):
        f = i / 40
        pts.append((lerp(x0, x1, f), lerp(y0, y1, f) + sag * math.sin(math.pi * f)))
    c.line(pts, 1.6, (40, 30, 30))
    for i in range(1, n + 1):
        f = i / (n + 1)
        x = lerp(x0, x1, f); y = lerp(y0, y1, f) + sag * math.sin(math.pi * f) + 10
        lantern(c, x, y, t + i, 0.9, a)

def pole(c, x, y0):
    c.rect(x - 4, y0, x + 4, GY + 6, fill=(60, 44, 40))

def house(c, cx, w, h, t, wall=(150, 96, 84), roof=(96, 52, 60), lit=True, door=(80, 52, 44), seed=0, flick=True, y=None):
    y = GY if y is None else y
    x0, x1 = cx - w / 2, cx + w / 2
    c.rect(x0, y - h, x1, y, fill=wall)
    c.poly([(x0 - 14, y - h + 2), (x1 + 14, y - h + 2), (cx, y - h - w * 0.36)], roof)
    c.rect(x1 - 36, y - h - w * 0.30, x1 - 18, y - h - 6, fill=lerpc(wall, (0, 0, 0), 0.35))
    c.rect(cx - 16, y - 80, cx + 16, y, fill=door, r=2)
    c.ell(cx + 8, y - 40, 2, fill=(220, 190, 110))
    for sx in (x0 + 26, x1 - 26 - 34):
        fl = 1.0 if not flick else 0.9 + 0.1 * math.sin(t * 4 + seed + sx)
        wcol = lerpc((40, 36, 60), (255, 214, 130), (1.0 if lit else 0.0) * fl)
        if lit: c.glow(sx + 17, y - h * 0.58, 70, (255, 190, 100), 0.5 * fl)
        c.rect(sx, y - h * 0.78, sx + 34, y - h * 0.42, fill=wcol)
        c.rect(sx - 2, y - h * 0.78 - 2, sx + 36, y - h * 0.42 + 2, outline=(70, 44, 40), w=2)
        c.line([(sx + 17, y - h * 0.78), (sx + 17, y - h * 0.42)], 1.5, (70, 44, 40))
        c.line([(sx, y - h * 0.6), (sx + 34, y - h * 0.6)], 1.5, (70, 44, 40))

def fireflies(c, t, n=18, seed=1, alpha=1.0):
    r = random.Random(seed)
    for i in range(n):
        bx, by = r.uniform(0, W), r.uniform(GY - 260, GY + 10)
        x = bx + 30 * math.sin(t * 0.5 + i) ; y = by + 18 * math.sin(t * 0.7 + i * 2.3)
        b = 0.5 + 0.5 * math.sin(t * 1.7 + i * 1.9)
        c.glow(x, y, 14, (255, 240, 140), b * alpha)
        c.ell(x, y, 1.6, fill=(255, 250, 200))

# ---------- people ----------
DAN = dict(skin=(236, 194, 164), hair=(44, 32, 30), shirt=(70, 112, 172), pants=(52, 58, 80), glasses=True, long=False)
MAR = dict(skin=(228, 178, 144), hair=(150, 72, 40), shirt=(232, 152, 70), pants=(96, 62, 84), glasses=False, long=True)
def villager(i):
    r = random.Random(100 + i)
    shirts = [(160, 80, 90), (90, 140, 110), (120, 100, 170), (190, 160, 80), (80, 140, 160), (170, 110, 80)]
    hairs = [(40, 30, 25), (110, 80, 50), (190, 170, 120), (70, 70, 80), (30, 24, 30)]
    skins = [(240, 200, 170), (210, 160, 125), (170, 120, 90), (235, 190, 160)]
    return dict(skin=r.choice(skins), hair=r.choice(hairs), shirt=r.choice(shirts), pants=(60, 60, 80),
                glasses=r.random() < 0.3, long=r.random() < 0.45)

def person(c, x, y, h, p, dir=1, walk=0.0, mood='flat', arms=(0, 0), nod=0.0, talk=0.0, lantern_t=None, tint=None, front=False, t=0):
    u = h
    d = dir if dir else 1
    def col(cc): return lerpc(cc, tint[0], tint[1]) if tint else cc
    skin, hair, shirt, pants = col(p['skin']), col(p['hair']), col(p['shirt']), col(p['pants'])
    hx = x + (0 if front else d * 0.012 * u)
    hy = y - 0.80 * u + nod * 0.02 * u
    hr = 0.115 * u
    sy = y - 0.66 * u
    hipy = y - 0.35 * u
    sw = 0.10 * u
    def arm(a, side, back=False):
        sx = x + (0 if front else 0) + side * sw * (0.8 if not front else 1.0)
        L = 0.31 * u
        if front:
            ex, ey = sx + side * L * math.sin(math.radians(a)) * 0.5 + side * 0.03 * u, sy + L * math.cos(math.radians(a))
        else:
            ex, ey = sx + d * L * math.sin(math.radians(a)), sy + L * math.cos(math.radians(a))
        c.line([(sx, sy + 0.02 * u), (ex, ey)], 0.075 * u, lerpc(shirt, (0, 0, 0), 0.12) if back else shirt)
        c.ell(ex, ey, 0.04 * u, fill=skin)
        return ex, ey
    if p['long']:
        c.ell(hx, hy + 0.04 * u, hr * 1.18, hr * 1.5, fill=hair)
    # legs
    for i, s in enumerate((-1, 1)):
        a = math.sin(walk + i * math.pi) * 0.5
        hxp = x + s * 0.045 * u
        fx = hxp + d * 0.34 * u * math.sin(a); fy = y - 0.34 * u * 0 - (0.34 * u * (1 - math.cos(a))) if False else y - 0.015 * u
        fx = hxp + d * 0.30 * u * math.sin(a)
        c.line([(hxp, hipy), (fx, y - 0.02 * u)], 0.085 * u, pants if i == 0 else lerpc(pants, (0, 0, 0), 0.15))
        c.ell(fx + d * 0.02 * u, y - 0.012 * u, 0.055 * u, 0.025 * u, fill=(40, 34, 40))
    # back arm
    wa = math.sin(walk) * 26
    ab, af = arms
    arm((ab - wa) if True else ab, -1 if front else -d * 0 + (-1 if False else -1) * 0 - 0, back=True) if False else None
    arm(ab - wa, -d if not front else -1, back=True)
    # torso
    c.rect(x - 0.105 * u, sy - 0.02 * u, x + 0.105 * u, hipy + 0.04 * u, fill=shirt, r=0.05 * u)
    if p['long'] is False and not front:
        pass
    # front arm
    hand = arm(af + wa, d if not front else 1)
    # neck + head
    c.rect(hx - 0.03 * u, hy + hr * 0.7, hx + 0.03 * u, sy + 0.01 * u, fill=skin)
    c.ell(hx, hy, hr, fill=skin)
    if not p['long']:
        c.ell(hx, hy - hr * 0.22, hr * 1.06, hr * 0.95, fill=hair)
        c.ell(hx + d * hr * 0.05, hy + hr * 0.18, hr * 0.97, hr * 0.88, fill=skin)
    else:
        c.ell(hx, hy - hr * 0.2, hr * 1.1, hr * 1.0, fill=hair)
        c.ell(hx + d * hr * 0.05, hy + hr * 0.2, hr * 0.92, hr * 0.86, fill=skin)
    # face
    ex = hx + (0 if front else d * hr * 0.32)
    for s in (-1, 1):
        c.ell(ex + s * hr * 0.38, hy + hr * 0.02, max(0.9, hr * 0.085), max(1.1, hr * 0.11), fill=(34, 28, 34))
    if p['glasses']:
        for s in (-1, 1):
            c.ell(ex + s * hr * 0.38, hy + hr * 0.02, hr * 0.27, hr * 0.27, outline=(30, 26, 30), w=max(1, hr * 0.06))
        c.line([(ex - hr * 0.11, hy), (ex + hr * 0.11, hy)], max(1, hr * 0.05), (30, 26, 30))
    my = hy + hr * 0.52
    mw = hr * 0.34
    lw = max(1.2, hr * 0.07)
    if mood == 'smile' or mood == 'fake':
        wdt = mw * (1.4 if mood == 'fake' else 1.0)
        c.arc(ex, my - hr * 0.2, wdt, hr * 0.32, 25, 155, lw, (120, 50, 50))
    elif mood == 'sad':
        c.arc(ex, my + hr * 0.25, mw, hr * 0.28, 205, 335, lw, (110, 50, 50))
    elif mood == 'o':
        c.ell(ex, my, hr * 0.13, hr * 0.17, fill=(110, 40, 50))
    elif mood == 'talk':
        o = abs(math.sin(talk))
        c.ell(ex, my, hr * 0.17, hr * (0.06 + 0.15 * o), fill=(110, 40, 50))
    else:
        c.line([(ex - mw * 0.7, my), (ex + mw * 0.7, my)], lw, (120, 60, 60))
    if lantern_t is not None:
        lantern(c, hand[0], hand[1] + 0.06 * u, lantern_t, 0.9 * u / 110 + 0.2)
    return hand

# ---------- captions ----------
def wrap(text, sz, maxw, bold=False):
    f = F(sz, bold)
    words, lines, cur = text.split(), [], ''
    for w_ in words:
        trial = (cur + ' ' + w_).strip()
        if f.getlength(trial) / K <= maxw: cur = trial
        else: lines.append(cur); cur = w_
    lines.append(cur)
    return lines

def caption(c, text, a):
    if a <= 0.01: return
    lines = wrap(text, 30, 1060)
    lh = 42
    hgt = lh * len(lines) + 24
    y1 = H - 22
    y0 = y1 - hgt
    wmax = max(F(30).getlength(l) / K for l in lines) + 56
    c.veil(W / 2 - wmax / 2, y0, W / 2 + wmax / 2, y1, (6, 6, 18), 0.62 * a)
    for i, l in enumerate(lines):
        yy = y0 + 12 + lh * i + lh / 2
        v = int(255 * a)
        c.text(W / 2 + 1, yy + 1.5, l, 30, (0, 0, 0), 'mm')
        c.text(W / 2, yy, l, 30, (v, v, min(255, v)), 'mm')
