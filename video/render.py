import json, math, random, subprocess, sys, textwrap
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
from multiprocessing import Pool

W, H, FPS = 1280, 720, 24
TL = json.load(open("timeline.json"))
SC = TL["scenes"]
TOTAL = TL["total"]
FD = "/usr/share/fonts/truetype/dejavu/"
def font(sz, bold=False, mono=False, serif=False):
    n = "DejaVuSansMono.ttf" if mono else ("DejaVuSerif-Bold.ttf" if serif else ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"))
    return ImageFont.truetype(FD + n, sz)
_fc = {}
def F(sz, **k):
    key = (sz, tuple(sorted(k.items())))
    if key not in _fc: _fc[key] = font(sz, **k)
    return _fc[key]

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return x * x * (3 - 2 * x)
def lerp(a, b, t): return a + (b - a) * t
def mix(c1, c2, t): return tuple(int(lerp(a, b, t)) for a, b in zip(c1, c2))
def seg(p, a, b): return ease((p - a) / (b - a))

_grad = {}
def gradient(top, bot, key=None):
    k = key or (top, bot)
    if k not in _grad:
        y = np.linspace(0, 1, H)[:, None, None]
        a = np.array(top, np.float32)[None, None, :]; b = np.array(bot, np.float32)[None, None, :]
        arr = (a + (b - a) * y).repeat(W, axis=1).astype(np.uint8)
        _grad[k] = Image.fromarray(arr)
    return _grad[k].copy()

def glow(img, layer, radius=18, strength=1.0):
    """additively blend a blurred copy of layer (RGB on black) plus the layer itself."""
    small = layer.resize((W // 4, H // 4))
    g = small.filter(ImageFilter.GaussianBlur(radius / 4)).resize((W, H))
    if strength != 1.0: g = g.point(lambda v: min(255, int(v * strength)))
    img.paste(ImageChops.add(img, g)); img.paste(ImageChops.add(img, layer))

def alpha_over(base, top, a):
    if a <= 0: return base
    if a >= 1: return top
    return Image.blend(base, top, a)

# ---------------------------------------------------------------- figures
_spr = {}
def person_sprite(h, color, arms="down", coat=False, glasses=False, suit=False):
    key = (h, color, arms, coat, glasses, suit)
    if key in _spr: return _spr[key]
    w = int(h * 0.9); im = Image.new("RGBA", (w, h + 4), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cx = w // 2; hr = h * 0.075
    d.ellipse([cx - hr, 0, cx + hr, hr * 2], fill=color)
    top = hr * 2.1; sh = h * 0.13; hip = h * 0.52
    if coat:
        d.polygon([(cx - sh, top), (cx + sh, top), (cx + sh * 1.5, h * 0.9), (cx - sh * 1.5, h * 0.9)], fill=color)
    else:
        d.polygon([(cx - sh, top), (cx + sh, top), (cx + sh * 0.7, hip), (cx - sh * 0.7, hip)], fill=color)
        d.polygon([(cx - sh * 0.7, hip - 2), (cx + sh * 0.7, hip - 2), (cx + sh * 0.9, h), (cx + sh * 0.1, h),
                   (cx, hip + h * 0.1), (cx - sh * 0.1, h), (cx - sh * 0.9, h)], fill=color)
    lw = max(3, int(h * 0.045))
    if arms == "down":
        d.line([(cx - sh, top + 4), (cx - sh * 1.3, h * 0.5)], fill=color, width=lw)
        d.line([(cx + sh, top + 4), (cx + sh * 1.3, h * 0.5)], fill=color, width=lw)
    elif arms == "up":
        d.line([(cx - sh, top + 4), (cx - sh * 2.0, h * 0.12)], fill=color, width=lw)
        d.line([(cx + sh, top + 4), (cx + sh * 2.0, h * 0.12)], fill=color, width=lw)
    elif arms == "open":
        d.line([(cx - sh, top + 6), (cx - sh * 2.6, h * 0.42)], fill=color, width=lw)
        d.line([(cx + sh, top + 6), (cx + sh * 2.6, h * 0.42)], fill=color, width=lw)
    elif arms == "reach":
        d.line([(cx - sh, top + 4), (cx - sh * 1.2, h * 0.5)], fill=color, width=lw)
        d.line([(cx + sh, top + 6), (cx + sh * 3.2, top + h * 0.06)], fill=color, width=lw)
    elif arms == "slump":
        d.line([(cx - sh, top + 4), (cx - sh * 0.9, h * 0.55)], fill=color, width=lw)
        d.line([(cx + sh, top + 4), (cx + sh * 0.9, h * 0.55)], fill=color, width=lw)
    if suit:
        d.polygon([(cx - 4, top), (cx + 4, top), (cx, top + h * 0.2)], fill=(235, 235, 235))
    if glasses:
        d.rectangle([cx - hr * 0.9, hr * 0.7, cx + hr * 0.9, hr * 1.25], fill=(0, 0, 0))
        d.rectangle([cx - hr * 0.9, hr * 0.7, cx + hr * 0.9, hr * 1.25], outline=(60, 255, 120))
    _spr[key] = im
    return im

def put(img, spr, x, y_base, flip=False, rot=0, alpha=1.0):
    """paste sprite with feet at (x, y_base); optional rotation about the feet."""
    s = spr.transpose(Image.FLIP_LEFT_RIGHT) if flip else spr
    if rot:
        pad = Image.new("RGBA", (s.width * 2, s.height * 2), (0, 0, 0, 0))
        pad.paste(s, (s.width // 2, s.height))
        pad = pad.rotate(rot, center=(s.width, s.height * 2 - 2), resample=Image.BICUBIC)
        ox, oy = s.width, s.height * 2 - 2
        pos = (int(x - ox), int(y_base - oy)); s = pad
    else:
        pos = (int(x - s.width / 2), int(y_base - s.height))
    if alpha < 1:
        a = s.split()[3].point(lambda v: int(v * alpha)); s = s.copy(); s.putalpha(a)
    img.paste(s, pos, s)

def hut(d, x, y, w, h, roof=(30, 20, 25), wall=(22, 16, 20), lit=0.0):
    d.rectangle([x, y - h, x + w, y], fill=wall)
    d.polygon([(x - w * 0.12, y - h), (x + w * 1.12, y - h), (x + w * 0.5, y - h - w * 0.55)], fill=roof)
    if lit > 0:
        c = mix(wall, (255, 180, 70), lit)
        d.rectangle([x + w * 0.38, y - h * 0.62, x + w * 0.62, y - h * 0.25], fill=c)

def coin(img, cx, cy, r, t=0, spin=True, alpha=1.0, dark=True):
    """the ominous coin: dark disc, gold rim, $ sign, rotating rim ticks."""
    layer = Image.new("RGBA", (int(r * 2 + 40), int(r * 2 + 40)), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    c = r + 20
    d.ellipse([c - r, c - r, c + r, c + r], fill=(12, 8, 12) if dark else (200, 160, 50), outline=(190, 150, 40), width=max(3, int(r * 0.06)))
    d.ellipse([c - r * 0.82, c - r * 0.82, c + r * 0.82, c + r * 0.82], outline=(120, 90, 30), width=2)
    for i in range(36):
        a = i / 36 * 2 * math.pi + (t * 0.3 if spin else 0)
        d.line([(c + math.cos(a) * r * 0.88, c + math.sin(a) * r * 0.88), (c + math.cos(a) * r * 0.97, c + math.sin(a) * r * 0.97)], fill=(150, 110, 30), width=2)
    f = F(int(r * 1.1), bold=True); tw = d.textlength("$", font=f)
    d.text((c - tw / 2, c - r * 0.72), "$", font=f, fill=(190, 150, 40))
    if alpha < 1:
        al = layer.split()[3].point(lambda v: int(v * alpha)); layer.putalpha(al)
    img.paste(layer, (int(cx - c), int(cy - c)), layer)

def rays(img, cx, cy, t, color=(255, 220, 140), n=14, length=900, strength=0.35):
    lay = Image.new("RGB", (W // 2, H // 2), (0, 0, 0)); d = ImageDraw.Draw(lay)
    for i in range(n):
        a = i / n * 2 * math.pi + t * 0.12
        wdt = 0.07
        d.polygon([(cx / 2, cy / 2), ((cx + math.cos(a - wdt) * length) / 2, (cy + math.sin(a - wdt) * length) / 2),
                   ((cx + math.cos(a + wdt) * length) / 2, (cy + math.sin(a + wdt) * length) / 2)], fill=tuple(int(v * strength) for v in color))
    lay = lay.filter(ImageFilter.GaussianBlur(6)).resize((W, H))
    img.paste(ImageChops.add(img, lay))

def particles(img, t, n, seed, color, speed=40, size=3, up=True, spread=1.0, wob=18):
    r = random.Random(seed); d = ImageDraw.Draw(img)
    for i in range(n):
        x0 = r.random() * W; y0 = r.random() * H; sp = speed * (0.5 + r.random()); ph = r.random() * 6.28
        y = (y0 - sp * t) % H if up else (y0 + sp * t) % H
        x = x0 + math.sin(t * 0.8 + ph) * wob
        s = size * (0.5 + r.random())
        tw = 0.6 + 0.4 * math.sin(t * 3 + ph)
        d.ellipse([x - s, y - s, x + s, y + s], fill=tuple(int(v * tw) for v in color))

def title(img, text, sub=None, a=1.0, y=40, size=34):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    f = F(size, serif=True); tw = d.textlength(text, font=f)
    d.text(((W - tw) / 2 + 2, y + 2), text, font=f, fill=(0, 0, 0, int(200 * a)))
    d.text(((W - tw) / 2, y), text, font=f, fill=(245, 235, 210, int(255 * a)))
    if sub:
        f2 = F(18); sw = d.textlength(sub, font=f2)
        d.text(((W - sw) / 2, y + size + 16), sub, font=f2, fill=(200, 190, 170, int(230 * a)))
    img.paste(lay, (0, 0), lay)

def label(img, x, y, text, size=22, color=(255, 255, 255), a=1.0, bold=True, anchor="c"):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    f = F(size, bold=bold); tw = d.textlength(text, font=f)
    xx = x - tw / 2 if anchor == "c" else x
    d.text((xx + 2, y + 2), text, font=f, fill=(0, 0, 0, int(180 * a)))
    d.text((xx, y), text, font=f, fill=color + (int(255 * a),))
    img.paste(lay, (0, 0), lay)

# ---------------------------------------------------------------- scenes
def sc_title(t, d, p):
    img = gradient((6, 6, 14), (30, 22, 40), "title")
    dr = ImageDraw.Draw(img)
    r = random.Random(3)
    for i in range(140):
        x, y = r.random() * W, r.random() * H * 0.8
        b = int(120 + 120 * math.sin(t * 2 + i))
        dr.ellipse([x, y, x + 2, y + 2], fill=(b, b, min(255, b + 30)))
    a = seg(p, 0.05, 0.3) * (1 - seg(p, 0.85, 1))
    title(img, "WHAT IF REALITY WERE A MOVIE?", "a thought experiment on capitalism, the Matrix, and AI", a, y=270, size=42)
    return img

def village(img, y, lit, t, sc=1.0, offs=0):
    dr = ImageDraw.Draw(img)
    for i, (x, w, h) in enumerate([(120, 90, 60), (300, 110, 75), (520, 85, 55), (760, 120, 80), (980, 95, 62), (1130, 90, 58)]):
        hut(dr, x + offs, y, w * sc, h * sc, lit=lit * (0.7 + 0.3 * math.sin(t * 6 + i * 2)))

def sc_violent(t, d, p):
    img = gradient((18, 4, 10), (190, 70, 25), "violent")
    dr = ImageDraw.Draw(img)
    # looming coin eclipsing the sun
    cx, cy = 880, 190
    lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay)
    pulse = 1 + 0.03 * math.sin(t * 2)
    ld.ellipse([cx - 150 * pulse, cy - 150 * pulse, cx + 150 * pulse, cy + 150 * pulse], outline=(230, 60, 20), width=10)
    glow(img, lay, 40, 1.4)
    coin(img, cx, cy, 130 * (0.85 + 0.15 * seg(p, 0, 0.8)), t)
    dr = ImageDraw.Draw(img)
    # hills
    dr.polygon([(0, 560), (200, 500), (420, 540), (700, 470), (1000, 520), (1280, 480), (1280, 720), (0, 720)], fill=(14, 8, 10))
    # invaders marching along ridge
    for i in range(9):
        x = 1330 - ((t * 38 + i * 150) % 1500)
        yb = 500 + 12 * math.sin(i)
        spr = person_sprite(70, (6, 4, 6), "up")
        put(img, spr, x, yb + 20)
        dr.line([(x + 14, yb - 80), (x + 14, yb + 20)], fill=(6, 4, 6), width=3)
        dr.polygon([(x + 14, yb - 100), (x + 10, yb - 80), (x + 18, yb - 80)], fill=(6, 4, 6))
    dr.polygon([(0, 640), (400, 600), (900, 630), (1280, 600), (1280, 720), (0, 720)], fill=(10, 6, 8))
    village(img, 650, 1.0, t, 1.2)
    # fire glow on huts
    lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay)
    for x in (180, 600, 1030):
        rr = 60 + 12 * math.sin(t * 9 + x)
        ld.ellipse([x - rr, 600 - rr, x + rr, 600 + rr], fill=(210, 90, 20))
    glow(img, lay, 36, 1.2)
    particles(img, t, 70, 11, (255, 140, 40), speed=60, size=3)
    # cowering villagers
    dr = ImageDraw.Draw(img)
    for x in (300, 700, 1090):
        put(img, person_sprite(46, (8, 5, 7), "slump"), x, 690)
    title(img, "ACT I  ·  A VIOLENT TIME", a=seg(p, 0.02, 0.15), y=30)
    return img

def sc_savior(t, d, p):
    dawn = seg(p, 0.0, 0.35)
    img = gradient(mix((20, 14, 40), (110, 160, 220), dawn), mix((140, 70, 40), (255, 215, 140), dawn), "sav%d" % int(dawn * 30))
    dr = ImageDraw.Draw(img)
    sy = lerp(520, 330, dawn)
    lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay)
    ld.ellipse([640 - 70, sy - 70, 640 + 70, sy + 70], fill=(255, 230, 150))
    glow(img, lay, 50, 1.3); rays(img, 640, sy, t, strength=0.28 * dawn)
    # the dark coin shrinks away to the horizon
    coin(img, lerp(880, 1230, seg(p, 0, 0.5)), lerp(190, 120, seg(p, 0, .5)), lerp(110, 20, seg(p, 0, 0.6)), t, alpha=1 - seg(p, 0.45, 0.65))
    dr = ImageDraw.Draw(img)
    g = int(lerp(10, 70, dawn))
    dr.polygon([(0, 540), (300, 500), (640, 520), (980, 490), (1280, 530), (1280, 720), (0, 720)], fill=(30, 60 + g, 40))
    dr.polygon([(420, 600), (640, 470), (860, 600)], fill=(36, 80 + g, 46))
    # crops that grow over the "three years"
    for i in range(26):
        x = 30 + i * 49
        hh = 6 + 38 * seg(p, 0.25 + (i % 5) * 0.02, 0.9)
        dr.line([(x, 700), (x, 700 - hh)], fill=(110, 190, 70), width=3)
        dr.ellipse([x - 4, 700 - hh - 6, x + 4, 700 - hh + 2], fill=(240, 210, 90))
    village(img, 650, seg(p, 0.1, 0.5), t, 1.2)
    # villagers gather
    for i in range(10):
        tx = 640 + (i - 4.5) * 70
        sx = tx + (-1 if i % 2 else 1) * 700 * (1 - seg(p, 0.1 + i * 0.015, 0.55))
        put(img, person_sprite(56, (14, 14, 22), "up" if p > 0.55 and i % 3 == 0 else "down"), sx, 690 + (i % 3) * 8)
    # the savior: radiant figure on the hilltop
    lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay)
    ld.ellipse([640 - 60, 360 - 60, 640 + 60, 360 + 60], fill=(255, 235, 170))
    glow(img, lay, 30, 0.9)
    put(img, person_sprite(120, (255, 244, 215), "open", coat=True), 640, 480)
    particles(img, t, 50, 5, (255, 230, 140), speed=25, size=2.5)
    for k, lbl in enumerate(["YEAR 1", "YEAR 2", "YEAR 3"]):
        a = seg(p, 0.35 + k * 0.17, 0.42 + k * 0.17)
        label(img, 230 + k * 410 - 100 * 0, 110, lbl, 36, (255, 245, 210), a * (1 - 0.0 * k))
    title(img, "THE SAVIOR ARRIVES  ·  THREE GOOD YEARS", a=seg(p, 0.02, 0.15), y=30, size=28)
    return img

def sc_fall(t, d, p):
    img = gradient((16, 8, 20), (110, 40, 40), "fall")
    dr = ImageDraw.Draw(img)
    rise = seg(p, 0.0, 0.6)
    coin(img, 640, lerp(-100, 230, rise), lerp(60, 120, rise), t)
    dr = ImageDraw.Draw(img)
    dr.polygon([(0, 560), (300, 520), (640, 540), (980, 510), (1280, 550), (1280, 720), (0, 720)], fill=(20, 18, 24))
    village(img, 650, 0.3 * (1 - seg(p, 0.6, 0.8)), t, 1.2)
    # shadow forces converge from both sides
    conv = seg(p, 0.15, 0.55)
    for i in range(7):
        for side in (-1, 1):
            x = 640 + side * lerp(700 + i * 40, 90 + i * 22, conv)
            put(img, person_sprite(100, (4, 2, 6), "up"), x, 560 + (i % 3) * 14, flip=side > 0)
            dr.line([(x - side * 24, 440 + (i % 3) * 14), (x - side * 24, 565 + (i % 3) * 14)], fill=(4, 2, 6), width=3)
    # savior: stands, then falls
    fallp = seg(p, 0.55, 0.72)
    glow_a = 1 - seg(p, 0.55, 0.9)
    lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay)
    rr = 70 * glow_a + 6
    ld.ellipse([640 - rr, 440 - rr, 640 + rr, 440 + rr], fill=(int(255 * glow_a) + 20, int(230 * glow_a) + 10, int(170 * glow_a)))
    glow(img, lay, 36, 1.0)
    col = mix((120, 110, 100), (255, 244, 215), glow_a)
    put(img, person_sprite(120, col, "open", coat=True), 640, 580, rot=-85 * fallp)
    # lone spark drifting up
    sp = seg(p, 0.75, 1.0)
    if sp > 0:
        sx, sy = 640 + math.sin(t * 2) * 12, lerp(560, 300, sp)
        lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay)
        ld.ellipse([sx - 7, sy - 7, sx + 7, sy + 7], fill=(255, 230, 160)); glow(img, lay, 24, 1.3)
    for x in (260, 380, 900, 1020):
        put(img, person_sprite(50, (10, 8, 12), "slump"), x, 690)
    # flash + desaturate
    fl = max(0, 1 - abs(p - 0.62) * 14)
    if fl > 0: img = Image.blend(img, Image.new("RGB", (W, H), (255, 255, 255)), fl * 0.6)
    gray = seg(p, 0.65, 0.95)
    if gray > 0:
        img = Image.blend(img, img.convert("L").convert("RGB"), gray * 0.8)
    title(img, "THE EVIL FORCE CUTS THE SAVIOR DOWN", a=seg(p, 0.02, 0.15), y=30, size=28)
    return img

def rain(img, t, n=140, seed=2, a=0.5):
    r = random.Random(seed); lay = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(lay)
    for i in range(n):
        x0 = r.random() * W; y0 = r.random() * H; sp = 700 + r.random() * 400
        y = (y0 + sp * t) % H; x = x0 - y * 0.15
        d.line([(x, y), (x - 4, y + 22)], fill=(int(120 * a), int(135 * a), int(160 * a)), width=1)
    img.paste(ImageChops.add(img, lay))

def sc_drudgery(t, d, p):
    # Part A: grey rain, lone figure trudges with a spark
    A = gradient((28, 30, 36), (70, 74, 82), "grey")
    dr = ImageDraw.Draw(A)
    dr.polygon([(0, 560), (400, 530), (900, 550), (1280, 520), (1280, 720), (0, 720)], fill=(30, 32, 36))
    for x, w, h in [(140, 90, 50), (460, 100, 60), (900, 110, 62)]:   # ruined huts
        dr.rectangle([x, 600 - h, x + w, 600], fill=(24, 24, 28))
        dr.polygon([(x - 8, 600 - h), (x + w * 0.35, 600 - h - 25), (x + w * 0.5, 600 - h)], fill=(24, 24, 28))
    x = lerp(-80, 760, ease(p / 0.45)); bob = math.sin(t * 5) * 3
    put(A, person_sprite(120, (10, 10, 14), "slump", coat=True), x, 650 + bob)
    lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay)
    ld.ellipse([x + 22 - 8, 590 - 8 + bob, x + 22 + 8, 590 + 8 + bob], fill=(255, 220, 140)); glow(A, lay, 20, 1.2)
    rain(A, t)
    # Part B: sepia memory of childhood before the invasion
    B = gradient((120, 90, 55), (235, 200, 130), "sepia")
    db = ImageDraw.Draw(B)
    db.ellipse([560, 90, 720, 250], fill=(255, 240, 190))
    db.polygon([(0, 560), (400, 520), (900, 550), (1280, 510), (1280, 720), (0, 720)], fill=(92, 120, 60))
    for x, w, h in [(120, 100, 64), (900, 110, 70)]: hut(db, x, 580, w, h, roof=(110, 70, 40), wall=(150, 105, 65), lit=0.0)
    for i in range(4):
        cx = 420 + i * 120 + math.sin(t * 3 + i) * 40; jump = abs(math.sin(t * 4 + i * 1.7)) * 26
        put(B, person_sprite(46, (70, 45, 25), "up"), cx, 670 - jump)
    # kite
    kx, ky = 700 + math.sin(t) * 40, 220 + math.sin(t * 1.3) * 20
    db.polygon([(kx, ky - 24), (kx + 18, ky), (kx, ky + 24), (kx - 18, ky)], fill=(200, 60, 40))
    db.line([(kx, ky + 24), (560 + math.sin(t * 3) * 10, 640)], fill=(80, 50, 30), width=1)
    B = Image.blend(B, Image.new("RGB", (W, H), (255, 240, 200)), 0.1 + 0.05 * math.sin(t * 6))
    # vignette
    vg = Image.new("L", (W, H), 0); vd = ImageDraw.Draw(vg); vd.ellipse([-200, -150, W + 200, H + 150], fill=255)
    vg = vg.filter(ImageFilter.GaussianBlur(120))
    B = Image.composite(B, Image.new("RGB", (W, H), (30, 20, 10)), vg)
    # Part C: rebuilding, the spark is planted and a sapling grows
    C = gradient(mix((60, 70, 95), (160, 190, 230), seg(p, 0.7, 1)), mix((120, 130, 140), (250, 220, 170), seg(p, 0.7, 1)), "rebuild%d" % int(seg(p, .7, 1) * 20))
    dc = ImageDraw.Draw(C)
    dc.polygon([(0, 560), (400, 530), (900, 550), (1280, 520), (1280, 720), (0, 720)], fill=(60, 80, 55))
    gp = seg(p, 0.72, 1.0)
    for k, (x, w, h) in enumerate([(140, 100, 60), (470, 110, 66), (900, 110, 66)]):
        hh = h * clamp(gp * 2.2 - k * 0.4)
        if hh > 2: hut(dc, x, 610, w, hh, roof=(90, 60, 40), wall=(120, 90, 60), lit=gp)
    sx = 700; trunk = 12 + 110 * gp
    dc.line([(sx, 660), (sx, 660 - trunk)], fill=(90, 60, 35), width=6)
    for i in range(int(gp * 12)):
        a = i * 2.4; rr = 8 + gp * 40
        dc.ellipse([sx + math.cos(a) * rr * 1.4 - 12, 660 - trunk + math.sin(a) * rr - 12, sx + math.cos(a) * rr * 1.4 + 12, 660 - trunk + math.sin(a) * rr + 12], fill=(90, 170, 80))
    lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay)
    ld.ellipse([sx - 10, 664 - 10, sx + 10, 664 + 10], fill=(255, 225, 150)); glow(C, lay, 30, 1.1)
    for k in range(5):
        put(C, person_sprite(54, (30, 30, 40), "up" if int(t * 2 + k) % 2 else "down"), 330 + k * 120, 690)
    # sequencing
    img = A
    img = alpha_over(img, B, seg(p, 0.42, 0.5) * (1 - seg(p, 0.66, 0.72)))
    img = alpha_over(img, C, seg(p, 0.66, 0.74))
    cap = "THE DRUDGERY" if p < 0.42 else ("A MEMORY OF BEFORE" if p < 0.7 else "REBUILDING")
    title(img, cap, a=0.9, y=30, size=28)
    return img

def sc_metaphor(t, d, p):
    img = gradient((12, 14, 28), (26, 22, 44), "meta")
    dr = ImageDraw.Draw(img)
    # timeline curve: violent low -> hope spike -> crash -> slow climb
    pts = [(120, 470), (300, 490), (440, 290), (620, 240), (700, 520), (900, 490), (1160, 380)]
    def curve(u):  # piecewise smooth through pts
        u = clamp(u) * (len(pts) - 1); i = min(int(u), len(pts) - 2); f = ease(u - i)
        return lerp(pts[i][0], pts[i + 1][0], f), lerp(pts[i][1], pts[i + 1][1], f)
    prog = seg(p, 0.05, 0.75)
    path = [curve(i / 120 * prog) for i in range(121)]
    lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay)
    ld.line(path, fill=(255, 210, 120), width=8); glow(img, lay, 14, 1.0)
    dr = ImageDraw.Draw(img); dr.line(path, fill=(255, 225, 150), width=4)
    labels = [(0.06, "Violent\nbeginning", 160, 500, (230, 110, 90)),
              (0.30, "The Savior\n(3 good years)", 440, 175, (255, 230, 150)),
              (0.55, "Cut down", 730, 535, (230, 110, 90)),
              (0.75, "Remember.\nRebuild.", 1020, 300, (170, 230, 170))]
    for th, txt, x, y, c in labels:
        a = seg(p, th, th + 0.07)
        for i, line in enumerate(txt.split("\n")): label(img, x, y + i * 28, line, 24, c, a)
    a = seg(p, 0.78, 0.9)
    coin(img, 1130, 140, 56, t, alpha=a)
    label(img, 640, 82, "= the trajectory of money-obsessed capitalism", 30, (255, 240, 200), a)
    title(img, "THE METAPHOR", a=0.9, y=24, size=26)
    return img

_glyph = None
def matrix_bg(t, bright=1.0, seed=7):
    img = Image.new("RGB", (W, H), (0, 6, 2)); d = ImageDraw.Draw(img); f = F(16, mono=True)
    r = random.Random(seed); chars = "01ABCDEFGHJKLMNPQRSTUVWXYZabcdefgh0123456789$%#@"
    for c in range(W // 16):
        sp = 60 + r.random() * 160; off = r.random() * H; ln = 8 + int(r.random() * 18)
        head = (off + sp * t) % (H + ln * 18)
        for k in range(ln):
            y = head - k * 18
            if -18 < y < H:
                g = int((255 - k * (230 / ln)) * bright) if k else int(255 * bright)
                col = (200, 255, 210) if k == 0 else (0, max(20, g), int(g * 0.3))
                d.text((c * 16, y), chars[int((c * 7 + k * 3 + t * 8 + int(head / 18)) % len(chars))], font=f, fill=col)
    return img

def sc_matrix(t, d, p):
    img = matrix_bg(t, 0.55)
    dr = ImageDraw.Draw(img)
    words = ["DEBT", "RENT", "SCARCITY", "COERCION", "DEADLINES", "FEAR"]
    cx = 520
    for i, w in enumerate(words):
        s = 0.08 + i * 0.14; u = (p - s) / 0.2
        if 0 <= u <= 1:
            x = lerp(1350, -300, u); y = 440 + 30 * (i % 2) - 20 * (i % 3)
            near = 1 - clamp(abs(x - cx) / 260)
            y += near * (-1) * 0  # projectile stays on line; the hero moves instead
            lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay)
            ld.text((x, y), w, font=F(40, bold=True), fill=(230, 40, 40)); glow(img, lay, 14, 1.2)
            dr = ImageDraw.Draw(img)
            for k in range(1, 6): dr.line([(x + 140 + k * 26, y + 22), (x + 140 + k * 26 + 24, y + 22)], fill=(150, 30, 30), width=2)
    # Neo sidesteps based on proximity of nearest word
    dodge = 0.0
    for i in range(len(words)):
        s = 0.08 + i * 0.14; u = (p - s) / 0.2
        if 0 <= u <= 1:
            x = lerp(1350, -300, u); dodge = max(dodge, 1 - clamp(abs(x + 80 - cx) / 280))
    off = ease(dodge) * 130 * (-1 if int(p * 20) % 2 else 1)
    lean = ease(dodge) * 18
    # code flows glow around him ("reading the code")
    lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay)
    for k in range(5):
        rr = 150 + k * 40 + 10 * math.sin(t * 3 + k)
        ld.ellipse([cx + off - rr, 440 - rr * 1.2, cx + off + rr, 440 + rr * 1.2], outline=(0, 90 + k * 25, 40), width=2)
    glow(img, lay, 18, 1.0)
    # afterimages
    for k in range(3, 0, -1):
        put(img, person_sprite(210, (0, 60, 25), "down", coat=True, glasses=True), cx + off * (1 - k * 0.2), 640, rot=lean * (1 - k * 0.2), alpha=0.18)
    put(img, person_sprite(210, (8, 8, 10), "down", coat=True, glasses=True), cx + off, 640, rot=lean)
    title(img, "READING THE CODE OF CAPITALISM'S VIOLENCE", a=seg(p, 0.0, 0.1), y=26, size=26)
    return img

def sc_dismantle(t, d, p):
    img = matrix_bg(t, 0.4, 9)
    dr = ImageDraw.Draw(img)
    # seated figures bound by chains of code links
    brk = seg(p, 0.35, 0.8)
    xs = [180, 330, 880, 1040, 1180]
    for i, x in enumerate(xs):
        put(img, person_sprite(80, (10, 40, 22), "slump"), x, 650)
        for k in range(7):
            ky = 590 - k * 34
            dx = (k - 3) * 6 * brk * (1 if i % 2 else -1)
            col = (40, 200, 90) if brk < 0.5 else (int(230 * (1 - brk) + 40), int(200 * (1 - brk)), 90)
            dr.line([(x - 4, 650 - k * 12), (x + 220 * 0 + 0, 650 - k * 12)], fill=(0, 0, 0))
            dr.ellipse([x - 24 + dx * 3, 592 - k * 5 - 6 + (brk * k * 14), x - 14 + dx * 3, 600 - k * 5 + (brk * k * 14)], outline=col, width=2)
    # Neo open-handed at center, grid dissolving
    cx = 640
    lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay)
    for gx in range(0, W, 64):
        for gy in range(120, 520, 64):
            if random.Random(gx * 31 + gy).random() < brk * 0.8: continue
            ld.line([(gx, gy), (gx + 40, gy)], fill=(0, 120, 50), width=1); ld.line([(gx, gy), (gx, gy + 40)], fill=(0, 120, 50), width=1)
    glow(img, lay, 6, 0.8)
    lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay)
    rr = 70 + 20 * math.sin(t * 3); ld.ellipse([cx - rr, 400 - rr, cx + rr, 400 + rr], outline=(255, 235, 170), width=3)
    glow(img, lay, 24, 1.0)
    put(img, person_sprite(210, (8, 8, 10), "open", coat=True, glasses=True), cx, 640)
    label(img, cx, 100, "No harm. Only unlocking.", 34, (210, 255, 220), seg(p, 0.1, 0.25) * (1 - seg(p, 0.85, 1)))
    particles(img, t, 40, 8, (230, 255, 200), speed=-40, size=2, up=False)
    title(img, "DISMANTLE THE MATRIX  ·  END THE COERCION", a=seg(p, 0.0, 0.1), y=26, size=26)
    return img

def sc_backs(t, d, p):
    img = gradient((10, 18, 14), (20, 36, 26), "backs")
    img = Image.blend(img, matrix_bg(t, 0.25, 4), 0.5)
    dr = ImageDraw.Draw(img)
    # agents fall away
    for i, x in enumerate([300, 520, 760, 980]):
        fall = seg(p, 0.05 + i * 0.05, 0.3 + i * 0.05)
        put(img, person_sprite(150, (4, 4, 6), "down", suit=True, glasses=True), x, 400, rot=-90 * fall * (1 if i % 2 else -1), alpha=1 - 0.8 * fall)
    # citizens in rows, backs turned (facing away) - they walk away from Neo
    for row in range(3):
        for i in range(11):
            x = 120 + i * 100 + (row % 2) * 50 + seg(p, 0.4, 1.0) * 60 * (row + 1) * (1 if i > 5 else 1) * 0.5
            put(img, person_sprite(64 + row * 18, (30, 52 + row * 6, 40), "slump"), x, 470 + row * 50)
            # back-of-head cue: draw a lighter hair arc
            hy = 470 + row * 50 - (64 + row * 18) + 3
            dr.arc([x - 6, hy, x + 6, hy + 12], 180, 360, fill=(80, 100, 85), width=2)
    # Neo reaches toward them
    nx = lerp(100, 330, seg(p, 0.35, 0.7));
    put(img, person_sprite(210, (8, 8, 10), "reach", coat=True, glasses=True), nx, 680, flip=False)
    label(img, 640, 120, "“Look at me.”", 34, (200, 255, 215), seg(p, 0.45, 0.6) * (1 - seg(p, 0.9, 1)))
    title(img, "THE CITIZENS WON'T LOOK", a=seg(p, 0.0, 0.1), y=26, size=26)
    return img

def ai_core(img, cx, cy, t, hue=0.0, scale=1.0, intensity=1.0):
    """hue 0 = cold blue/red menace, 1 = warm gold."""
    cold = (90, 140, 255); hot = (255, 70, 60); warm = (255, 215, 140)
    c1 = mix(cold, warm, hue); c2 = mix(hot, (255, 190, 100), hue)
    lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay)
    for k in range(6):
        rr = (60 + k * 46) * scale; a = t * (0.25 + k * 0.1) * (1 if k % 2 else -1)
        box = [cx - rr, cy - rr * 0.62, cx + rr, cy + rr * 0.62]
        ld.arc(box, math.degrees(a), math.degrees(a) + 230, fill=tuple(int(v * intensity) for v in (c1 if k % 2 else c2)), width=3)
    r0 = (34 + 4 * math.sin(t * 2.5)) * scale
    ld.ellipse([cx - r0, cy - r0, cx + r0, cy + r0], fill=tuple(int(v * intensity) for v in c1))
    glow(img, lay, 40, 1.4)
    d = ImageDraw.Draw(img)
    d.ellipse([cx - r0 * 0.45, cy - r0 * 0.45, cx + r0 * 0.45, cy + r0 * 0.45], fill=(255, 255, 255))

def sc_ai(t, d, p):
    img = gradient((2, 4, 12), (12, 14, 34), "ai")
    dr = ImageDraw.Draw(img)
    r = random.Random(1)
    for i in range(80):
        x, y = r.random() * W, r.random() * H; b = int(60 + 60 * math.sin(t + i))
        dr.point((x, y), fill=(b, b, b + 30))
    # floor lines
    for i in range(12):
        dr.line([(640 + (i - 6) * 40, 450), (640 + (i - 6) * 300, 720)], fill=(20, 30, 60), width=1)
    for j in range(6): dr.line([(0, 470 + j * j * 8), (W, 470 + j * j * 8)], fill=(20, 30, 60), width=1)
    ai_core(img, 640, 250, t, 0.0, 1.5 + 0.2 * seg(p, 0.3, 1))
    # tenders hooked up to pods
    for x in (160, 280, 1000, 1120):
        dr.rounded_rectangle([x - 30, 400, x + 30, 560], 20, outline=(40, 80, 140), width=3)
        dr.line([(x, 400), (x, 330), (640, 250)], fill=(25, 45, 90), width=2)
    # tiny Neo walks in
    nx = lerp(-60, 560, ease(p / 0.85))
    put(img, person_sprite(130, (6, 6, 8), "down", coat=True, glasses=True), nx, 690 - (nx / 560) * 20)
    label(img, 640, 520, "far more powerful than he is", 24, (170, 200, 255), seg(p, 0.45, 0.65))
    title(img, "THE ARCHITECT  ·  THE AI", a=seg(p, 0.0, 0.1), y=26, size=26)
    return img

def sc_plug(t, d, p):
    warm = seg(p, 0.35, 0.9)
    img = gradient(mix((2, 4, 12), (30, 16, 24), warm), mix((12, 14, 34), (80, 50, 40), warm), "plug%d" % int(warm * 25))
    dr = ImageDraw.Draw(img)
    ai_core(img, 640, 260, t, warm, 1.7, 1.0)
    dr = ImageDraw.Draw(img)
    nx, ny = 470, 650
    put(img, person_sprite(190, (8, 8, 10), "open", coat=True, glasses=True), nx, ny)
    # cable from his back to the core
    pts = [(nx + 0, ny - 150)]
    for i in range(1, 25):
        u = i / 24; pts.append((lerp(nx, 640, u) + math.sin(u * 6 + t * 3) * 6, lerp(ny - 150, 285, ease(u)) + math.sin(u * 9 - t * 4) * 5))
    dr.line(pts, fill=(60, 120, 200) if warm < 0.5 else (255, 205, 130), width=4)
    # data stream: words flowing along the cable
    words = ["care", "dignity", "non-violence", "mercy", "we are fragile", "remember them", "compassion", "peace"]
    for i, w in enumerate(words):
        u = ((t * 0.18 + i / len(words)) % 1.0)
        if p < 0.2 + i * 0.01: continue
        x = lerp(nx, 640, u) + 20 * math.sin(i * 3 + t); y = lerp(ny - 150, 285, ease(u)) - 20 - 14 * (i % 3)
        a = math.sin(u * math.pi); label(img, x, y, w, 20, (230, 245, 255) if warm < 0.5 else (255, 240, 200), a, anchor="c")
    # the famous line is there, but it is just one thread in a much larger transfer
    big = seg(p, 0.25, 0.4) * (1 - seg(p, 0.55, 0.65))
    label(img, 640, 118, "“please don't hurt them”", 36, (255, 245, 220), big)
    label(img, 640, 166, "powerful, but only the surface of what he gives", 20, (200, 210, 230), big)
    deep = seg(p, 0.62, 0.78)
    label(img, 640, 118, "a massive data dump of pro-human non-violence", 32, (255, 240, 200), deep)
    # progress bar
    bar = seg(p, 0.15, 0.95)
    dr.rounded_rectangle([340, 690, 940, 702], 6, outline=(150, 160, 190), width=2)
    dr.rounded_rectangle([340, 690, 340 + 600 * bar, 702], 6, fill=mix((90, 140, 255), (255, 215, 140), bar))
    title(img, "NEO PLUGS IN  ·  HE DOES NOT FIGHT THE AI", a=seg(p, 0.0, 0.1), y=26, size=26)
    return img

def sc_peace(t, d, p):
    dawn = seg(p, 0.0, 0.6)
    img = gradient(mix((40, 20, 40), (120, 170, 230), dawn), mix((160, 60, 40), (255, 220, 160), dawn), "peace%d" % int(dawn * 30))
    dr = ImageDraw.Draw(img)
    sy = lerp(520, 360, dawn)
    lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay)
    ld.ellipse([640 - 80, sy - 80, 640 + 80, sy + 80], fill=(255, 230, 160)); glow(img, lay, 50, 1.3)
    rays(img, 640, sy, t, strength=0.25 * dawn)
    # distant AI core, now warm, safe at the center
    ai_core(img, 640, 280, t, 1.0, 0.7, 0.9)
    dr = ImageDraw.Draw(img)
    dr.polygon([(0, 560), (300, 520), (640, 540), (980, 510), (1280, 550), (1280, 720), (0, 720)], fill=(34, 52, 40))
    # rebels with rifles that they lower, then drop
    low = seg(p, 0.35, 0.65); drop = seg(p, 0.6, 0.85)
    for i in range(13):
        x = 90 + i * 92; yb = 640 + (i % 3) * 18
        put(img, person_sprite(92, (12, 14, 18), "down"), x, yb)
        ang = lerp(-35, 80, low)
        L = 70; x0, y0 = x + 8, yb - 50 + drop * 40
        gx = x0 + math.sin(math.radians(ang)) * L; gy = y0 - math.cos(math.radians(ang)) * L + drop * 28
        dr.line([(x0, y0), (gx, gy)], fill=(6, 6, 8), width=4)
    # peace doves of light
    particles(img, t, 40, 6, (255, 245, 200), speed=30, size=3)
    label(img, 640, 120, "they put down their weapons", 34, (255, 250, 230), seg(p, 0.5, 0.7))
    title(img, "THE AI IS SPARED  ·  THE HUMANS STAND DOWN", a=seg(p, 0.0, 0.1), y=26, size=26)
    return img

def sc_end(t, d, p):
    img = gradient((20, 24, 50), (255, 200, 140), "end")
    dr = ImageDraw.Draw(img)
    lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay)
    ld.ellipse([640 - 110, 420 - 110, 640 + 110, 420 + 110], fill=(255, 235, 170)); glow(img, lay, 60, 1.4)
    rays(img, 640, 420, t, strength=0.3)
    dr.polygon([(0, 560), (300, 520), (640, 540), (980, 510), (1280, 550), (1280, 720), (0, 720)], fill=(20, 24, 30))
    for k, (x, hh) in enumerate([(540, 100), (640, 110), (740, 96)]):
        put(img, person_sprite(hh, (10, 12, 16), "up" if k == 1 else "down"), x, 640)
    particles(img, t, 60, 4, (255, 240, 190), speed=20, size=3)
    lines = ["Sanctify the machine.", "Protect the people.", "Put down the weapons."]
    for i, s in enumerate(lines):
        a = seg(p, 0.12 + i * 0.22, 0.26 + i * 0.22)
        label(img, 640, 90 + i * 56, s, 42, (255, 250, 235), a)
    return img

SCENE_FN = {"title": sc_title, "violent": sc_violent, "savior": sc_savior, "fall": sc_fall, "drudgery": sc_drudgery,
            "metaphor": sc_metaphor, "matrix": sc_matrix, "dismantle": sc_dismantle, "backs": sc_backs,
            "ai": sc_ai, "plug": sc_plug, "peace": sc_peace, "end": sc_end}

def subtitles(img, t):
    for s in SCS:
        for z in s["sents"]:
            if z["start"] - 0.05 <= t <= z["end"] + 0.25:
                lines = textwrap.wrap(z["text"], 64)
                lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
                f = F(26); lh = 36; bh = lh * len(lines) + 20; y0 = H - bh - 18
                d.rounded_rectangle([90, y0, W - 90, y0 + bh], 12, fill=(0, 0, 0, 150))
                for i, ln in enumerate(lines):
                    tw = d.textlength(ln, font=f); d.text(((W - tw) / 2, y0 + 10 + i * lh), ln, font=f, fill=(255, 255, 255, 255))
                img.paste(lay, (0, 0), lay)
                return img
    return img
SCS = SC

def frame(i):
    t = i / FPS
    sc = next((s for s in SC if s["start"] <= t < s["end"]), SC[-1])
    tt = t - sc["start"]; dur = sc["end"] - sc["start"]; p = clamp(tt / dur)
    img = SCENE_FN[sc["id"]](tt, dur, p).convert("RGB")
    # cross-fade through black at scene edges
    fade = min(1, tt / 0.5, (dur - tt) / 0.5) if sc["id"] != "end" else min(1, tt / 0.5, (dur - tt) / 1.5)
    if fade < 1: img = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), img, clamp(fade))
    img = subtitles(img, t)
    return img.tobytes()

if __name__ == "__main__":
    n = int(TOTAL * FPS) + FPS
    only = int(sys.argv[1]) if len(sys.argv) > 1 else None
    if only is not None:   # preview: write PNG stills for a set of times
        import os; os.makedirs("stills", exist_ok=True)
        for sc in SC:
            for q in (0.25, 0.7):
                i = int((sc["start"] + (sc["end"] - sc["start"]) * q) * FPS)
                Image.frombytes("RGB", (W, H), frame(i)).save(f"stills/{sc['id']}_{int(q*100)}.png")
        sys.exit()
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-i", "mix.wav", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                           "-shortest", "-movflags", "+faststart", "what_if_reality_were_a_movie.mp4"], stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for k, b in enumerate(pool.imap(frame, range(n), chunksize=6)):
            ff.stdin.write(b)
            if k % 240 == 0: print(k, "/", n, flush=True)
    ff.stdin.close(); ff.wait()
