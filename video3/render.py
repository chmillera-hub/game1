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

# ================================================================= The Library
EV = {}
for _s in SC:
    EV[_s["id"]] = {z["tag"]: (z["start"] - _s["start"], z["end"] - _s["start"]) for z in _s["sents"] if z.get("tag")}
def ev(sc, tag): return EV[sc][tag]
def tseg(t, a, b): return ease((t - a) / (b - a)) if b > a else (1.0 if t >= a else 0.0)

BOOKS = [(92, 28, 28), (40, 64, 44), (60, 42, 30), (34, 44, 78), (100, 80, 40), (70, 30, 50), (50, 50, 56), (110, 56, 34)]
DX0, DX1, DT, DB = 1130, 1250, 250, 600
HX, HYB, HH = 1040, 606, 270
_R = {}

def room():
    if "img" in _R: return _R["img"]
    rng = random.Random(4)
    img = gradient((12, 8, 10), (34, 22, 18), "roomwall"); d = ImageDraw.Draw(img)
    for x in range(0, W, 160): d.rectangle([x + 8, 120, x + 150, 590], outline=(26, 18, 16), width=3)
    d.rectangle([0, 0, W, 60], fill=(22, 14, 12)); d.rectangle([0, 56, W, 70], fill=(46, 30, 22))
    d.rectangle([0, 600, W, 720], fill=(40, 26, 18))
    for i in range(-4, 16): d.line([(i * 100, 604), (i * 150 - 330, 720)], fill=(30, 19, 14), width=2)
    d.rectangle([0, 590, W, 606], fill=(56, 36, 26))
    def shelf(x0, x1):
        d.rectangle([x0, 80, x1, 598], fill=(30, 19, 13))
        for r in range(5):
            yb = 96 + r * 100 + 92; x = x0 + 8
            while x < x1 - 16:
                w = rng.randint(9, 20); h = rng.randint(54, 84); col = rng.choice(BOOKS)
                d.rectangle([x, yb - h, x + w, yb], fill=col); d.line([(x + 2, yb - h + 8), (x + w - 2, yb - h + 8)], fill=(150, 120, 60), width=1)
                x += w + rng.randint(0, 2)
            d.rectangle([x0, yb, x1, yb + 8], fill=(62, 40, 28))
    shelf(0, 330); shelf(920, 1110)
    # arched window
    d.rectangle([350, 190, 470, 450], fill=(38, 58, 100)); d.pieslice([350, 130, 470, 250], 180, 360, fill=(38, 58, 100))
    d.ellipse([396, 160, 424, 188], fill=(200, 210, 235))
    d.rectangle([350, 190, 470, 450], outline=(86, 58, 40), width=7); d.arc([350, 130, 470, 250], 180, 360, fill=(86, 58, 40), width=7)
    d.line([(410, 130), (410, 450)], fill=(86, 58, 40), width=5); d.line([(350, 320), (470, 320)], fill=(86, 58, 40), width=5)
    d.rectangle([338, 450, 482, 464], fill=(100, 70, 48))
    # fireplace
    d.rectangle([540, 330, 860, 600], fill=(60, 52, 50)); d.rectangle([590, 405, 810, 600], fill=(5, 3, 3)); d.pieslice([590, 380, 810, 430], 180, 360, fill=(5, 3, 3))
    for k in range(6): d.line([(540, 345 + k * 42), (860, 345 + k * 42)], fill=(48, 42, 40), width=2)
    d.rectangle([515, 310, 885, 334], fill=(98, 76, 60)); d.rectangle([560, 596, 840, 610], fill=(70, 62, 58))
    d.rectangle([608, 146, 792, 300], fill=(120, 92, 40)); d.rectangle([616, 154, 784, 292], fill=(18, 24, 32))
    d.polygon([(616, 270), (680, 210), (720, 245), (760, 200), (784, 230), (784, 292), (616, 292)], fill=(26, 36, 46))
    d.ellipse([740, 170, 760, 190], fill=(90, 96, 110))
    d.ellipse([640, 540, 760, 590], fill=(30, 20, 14)); d.ellipse([650, 520, 750, 560], fill=(40, 26, 18))   # logs
    # rug
    d.polygon([(250, 628), (990, 628), (1070, 714), (170, 714)], fill=(70, 20, 24)); d.polygon([(280, 640), (960, 640), (1020, 702), (220, 702)], outline=(150, 110, 50), width=3)
    # armchair back + seat
    d.rounded_rectangle([316, 410, 392, 604], 26, fill=(86, 34, 28)); d.rounded_rectangle([322, 420, 386, 596], 22, outline=(120, 56, 42), width=3)
    for yy in (450, 490, 530): d.ellipse([348, yy, 358, yy + 10], fill=(120, 56, 42))
    d.rounded_rectangle([316, 556, 520, 596], 14, fill=(96, 40, 32)); d.rectangle([326, 596, 338, 612], fill=(40, 24, 16)); d.rectangle([498, 596, 510, 612], fill=(40, 24, 16))
    d.rounded_rectangle([326, 520, 404, 562], 14, fill=(80, 32, 26))
    _R["img"] = img
    yy, xx = np.mgrid[0:H, 0:W]
    g = np.exp(-(((xx - 700) / 430.0) ** 2 + ((yy - 500) / 330.0) ** 2))[..., None] * np.array([120, 56, 16], np.float32)
    _R["glow"] = g
    v = np.clip(1.15 - (((xx - 640) / 760.0) ** 2 + ((yy - 360) / 470.0) ** 2), 0.18, 1.0)[..., None]
    _R["vig"] = Image.fromarray((v.repeat(3, 2) * 255).astype(np.uint8))
    return img

# ---- fire
def softglow(img, layer, radius=40, strength=1.0):
    g = layer.resize((W // 4, H // 4)).filter(ImageFilter.GaussianBlur(radius / 4)).resize((W, H))
    if strength != 1.0: g = g.point(lambda v: min(255, int(v * strength)))
    img.paste(ImageChops.add(img, g))
def fire(img, t, level=1.0, lite=False):
    d = ImageDraw.Draw(img)
    lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay)
    f = 0.75 + 0.25 * math.sin(t * 9) * math.sin(t * 5.3 + 1)
    ld.ellipse([700 - 150 * level, 500 - 90 * level, 700 + 150 * level, 610], fill=(int(190 * f), int(80 * f), 14))
    softglow(img, lay, 90, 1.0 + 0.3 * level)
    d = ImageDraw.Draw(img)
    for sc, col in ((1.0, (222, 70, 18)), (0.72, (255, 150, 36)), (0.42, (255, 226, 130))):
        for i in range(8):
            cx = 612 + i * 25 + math.sin(t * 3 + i) * 4
            h = (62 + 42 * level) * sc * (0.62 + 0.38 * math.sin(t * 7 + i * 1.9) + 0.25 * math.sin(t * 13 + i * 0.7)) + 10
            w = 20 * (0.7 + 0.3 * sc)
            tipx = cx + 9 * math.sin(t * 5 + i * 1.3)
            d.polygon([(cx - w, 598), (cx - w * 0.7, 598 - h * 0.45), (tipx, 598 - h), (cx + w * 0.7, 598 - h * 0.45), (cx + w, 598)], fill=col)
    r = random.Random(11)
    for i in range(int(14 * level)):
        sp = 60 + r.random() * 90; ph = r.random() * 6.28
        y = 560 - ((t * sp + r.random() * 300) % 260); x = 700 + math.sin(t * 2 + ph) * (30 + (560 - y) * 0.2) + (r.random() - 0.5) * 80
        s = 1.5 + r.random() * 1.5; d.ellipse([x - s, y - s, x + s, y + s], fill=(255, 190 + int(40 * r.random()), 80))

def christ_flame(img, a):
    if a <= 0: return
    lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay); cx, yb = 700, 598; h = 200
    c = (255, 232, 170)
    ld.ellipse([cx - 22, yb - h - 4, cx + 22, yb - h + 40], outline=c, width=4)            # halo
    ld.ellipse([cx - 11, yb - h + 8, cx + 11, yb - h + 34], fill=c)                        # head
    ld.polygon([(cx - 13, yb - h + 36), (cx + 13, yb - h + 36), (cx + 46, yb - 24), (cx + 52, yb), (cx - 52, yb), (cx - 46, yb - 24)], fill=c)   # robe
    ld.line([(cx - 12, yb - h + 46), (cx - 48, yb - 80)], fill=c, width=9); ld.line([(cx + 12, yb - h + 46), (cx + 48, yb - 80)], fill=c, width=9)  # open arms
    lay = lay.point(lambda v: int(v * a))
    glow(img, lay, 26, 1.7)

def christ_seated(img, a):
    """a robed, haloed figure in the same seated pose as the android, flashing over its form."""
    if a <= 0: return
    robe = (246, 238, 222); skin = (232, 192, 150); hair = (110, 76, 52)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.polygon([(402, 452), (446, 452), (456, 520), (450, 556), (388, 556), (392, 500)], fill=robe + (255,))              # torso / robe
    d.polygon([(388, 540), (486, 536), (500, 560), (498, 606), (452, 606), (446, 566), (392, 572)], fill=robe + (255,))   # lap and thighs, drape to the floor
    d.line([(420, 462), (448, 514), (484, 540)], fill=robe + (255,), width=15)                                           # arm resting on the knee
    d.ellipse([476, 531, 494, 548], fill=skin + (255,))                                                                  # hand
    d.line([(404, 470), (462, 500)], fill=(196, 150, 96, 255), width=6)                                                  # sash
    d.ellipse([410, 392, 456, 442], fill=hair + (255,)); d.ellipse([416, 398, 452, 436], fill=skin + (255,))             # hair and face
    d.polygon([(420, 424), (448, 424), (434, 448)], fill=hair + (255,))                                                  # beard
    d.ellipse([430, 413, 434, 417], fill=(60, 40, 30, 255)); d.ellipse([442, 413, 446, 417], fill=(60, 40, 30, 255))
    lay.putalpha(lay.split()[3].point(lambda v: int(v * min(1.0, a * 1.15))))
    img.paste(lay, (0, 0), lay)
    halo = Image.new("RGB", (W, H), (0, 0, 0)); hd = ImageDraw.Draw(halo)
    hd.ellipse([408, 364, 458, 398], outline=(255, 226, 150), width=5)                                                  # halo
    hd.polygon([(402, 452), (446, 452), (456, 520), (450, 556), (388, 556)], fill=(150, 125, 80))                          # soft aura on the body
    hd.polygon([(388, 540), (486, 536), (500, 560), (498, 606), (446, 606)], fill=(130, 108, 70))
    halo = halo.point(lambda v: int(v * a)); glow(img, halo, 22, 1.6)

def lightpass(img, t, level=1.0, vig=True):
    room()
    f = (0.78 + 0.22 * math.sin(t * 8.3) * math.sin(t * 3.1 + 0.5)) * (0.7 + 0.3 * level)
    g = Image.fromarray(np.clip(_R["glow"] * f * level, 0, 255).astype(np.uint8))
    img.paste(ImageChops.add(img, g))
    if vig: img.paste(ImageChops.multiply(img, _R["vig"]))

def rain(img, t):
    d = ImageDraw.Draw(img)
    r = random.Random(3)
    for i in range(34):
        x = 356 + r.random() * 108; sp = 220 + r.random() * 160; y0 = r.random() * 300
        y = 140 + (y0 + t * sp) % 310
        if y < 445: d.line([(x, y), (x - 2, y + 14)], fill=(100, 130, 190), width=1)

# ---- door
def door(img, t, o, hall_light=True):
    d = ImageDraw.Draw(img)
    d.rectangle([DX0 - 10, DT - 12, DX1 + 10, DB + 6], fill=(60, 40, 28))        # frame
    a = o * 1.25
    xf = DX1 - (DX1 - DX0) * math.cos(a)
    if o > 0:
        d.rectangle([DX0, DT, DX1, DB], fill=(40, 58, 92))                          # lit hall
        d.rectangle([DX0, DT, DX1, DT + 90], fill=(30, 44, 74))
        lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay)
        k = int(40 * o); ld.polygon([(DX0, DB - 2), (DX1, DB - 2), (DX0 - 330, 720), (DX0 - 640, 720)], fill=(int(30 * o), int(48 * o), int(80 * o)))
        img.paste(ImageChops.add(img, lay))
        d = ImageDraw.Draw(img)
    s = math.sin(a)
    d.polygon([(xf, DT + 8 * s), (DX1, DT), (DX1, DB), (xf, DB - 5 * s)], fill=(74, 48, 34))
    d.polygon([(xf + 8, DT + 30), (DX1 - 8, DT + 28), (DX1 - 8, DT + 140), (xf + 8, DT + 140)], outline=(104, 70, 50), width=3) if DX1 - xf > 40 else None
    if o < 0.3: d.ellipse([DX0 + 10, 430, DX0 + 24, 444], fill=(180, 140, 60))

# ---- android
def android(img, t, gaze=0.0, speak=0.0, eye=1.0):
    d = ImageDraw.Draw(img); br = math.sin(t * 1.4) * 1.2
    G = (56, 60, 68); P = (172, 178, 192); D = (28, 30, 36)
    def limb(a, b, w, col=G):
        d.line([a, b], fill=col, width=w)
        for q in (a, b): d.ellipse([q[0] - w / 2, q[1] - w / 2, q[0] + w / 2, q[1] + w / 2], fill=col)
    hip, knee, foot = (402, 548), (480, 552), (488, 604)
    limb(hip, knee, 24); limb(knee, foot, 20); d.rounded_rectangle([476, 596, 524, 610], 4, fill=D)
    limb((hip[0] + 6, hip[1] - 4), (knee[0] - 8, knee[1] - 10), 8, P)
    sh = (420, 464 + br)
    d.polygon([(hip[0] - 20, hip[1] + 6), (hip[0] + 22, hip[1] + 6), (sh[0] + 26, sh[1] + 4), (sh[0] - 22, sh[1] + 4)], fill=G)
    d.polygon([(sh[0] - 6, sh[1] + 10), (sh[0] + 24, sh[1] + 10), (hip[0] + 16, hip[1] - 10), (hip[0] - 4, hip[1] - 10)], fill=P)
    d.ellipse([sh[0] - 6, sh[1] - 6, sh[0] + 20, sh[1] + 16], fill=D)
    limb((sh[0] + 8, sh[1] + 14), (450, 516), 15); limb((450, 516), (484, 540), 12); d.ellipse([476, 532, 496, 548], fill=P)
    d.rectangle([sh[0] - 1, sh[1] - 24, sh[0] + 11, sh[1] + 6], fill=D)
    for k in range(4): d.line([(sh[0] + 1 + k * 3, sh[1] - 22), (sh[0] - 6 + k * 3, sh[1] + 2)], fill=(90, 94, 104), width=1)
    head = Image.new("RGBA", (130, 130), (0, 0, 0, 0)); hd = ImageDraw.Draw(head); cx, cy = 65, 62
    hd.ellipse([cx - 27, cy - 34, cx + 27, cy + 30], fill=G)
    hd.polygon([(cx + 2, cy - 32), (cx + 28, cy - 14), (cx + 28, cy + 14), (cx + 18, cy + 34), (cx - 4, cy + 30)], fill=P)
    hd.ellipse([cx - 18, cy - 6, cx - 4, cy + 8], fill=D); hd.arc([cx - 24, cy - 28, cx + 20, cy + 22], 200, 300, fill=(120, 126, 140), width=2)
    ec = tuple(int(v * (0.35 + 0.65 * eye)) for v in (255, 176, 60))
    hd.rounded_rectangle([cx + 8, cy - 11, cx + 31, cy], 3, fill=ec)
    ang = lerp(-11, 5, gaze); npv = (cx, cy + 32)
    head = head.rotate(ang, center=npv, resample=Image.BICUBIC)
    wx, wy = sh[0] + 4, sh[1] - 16
    img.paste(head, (int(wx - npv[0]), int(wy - npv[1])), head)
    a = math.radians(ang); dx, dy = (cx + 20) - npv[0], (cy - 5) - npv[1]
    ex = wx + dx * math.cos(a) + dy * math.sin(a); ey = wy - dx * math.sin(a) + dy * math.cos(a)
    lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay)
    ld.ellipse([ex - 9, ey - 5, ex + 9, ey + 5], fill=tuple(int(v * eye) for v in (255, 170, 50)))
    ld.line([(sh[0] + 4, sh[1] + 34), (sh[0] + 4, sh[1] + 78)], fill=(int(255 * (0.5 + 0.5 * speak)), int(150 * (0.5 + 0.5 * speak)), 50), width=3)
    if speak > 0:
        rr = 16 + 14 * ((t * 3) % 1); ld.ellipse([wx - rr, wy + 14 - rr, wx + rr, wy + 14 + rr], outline=(int(200 * speak * (1 - ((t * 3) % 1))), int(120 * speak * (1 - ((t * 3) % 1))), 30), width=2)
    glow(img, lay, 14, 1.3)
    return ex, ey

# ---- human rig
KEYS = ["hip", "neck", "head", "kl", "kr", "fl", "fr", "el", "er", "hl", "hr"]
def _p(**k): return {n: k[n] for n in KEYS}
POSES = {
 "stand": _p(fl=(-.05, 0), fr=(.06, 0), kl=(-.045, -.25), kr=(.055, -.25), hip=(0, -.5), neck=(.005, -.83), head=(.005, -.91), el=(-.06, -.64), hl=(-.07, -.46), er=(.07, -.64), hr=(.075, -.46)),
 "kneel": _p(fl=(.12, 0), fr=(.18, 0), kl=(-.08, -.01), kr=(-.02, -.01), hip=(.06, -.27), neck=(.02, -.58), head=(.015, -.66), el=(-.02, -.4), hl=(-.1, -.5), er=(.03, -.38), hr=(-.09, -.48)),
 "bow": _p(fl=(.12, 0), fr=(.18, 0), kl=(-.1, -.01), kr=(-.04, -.01), hip=(.08, -.24), neck=(-.17, -.33), head=(-.26, -.27), el=(-.2, -.15), hl=(-.31, -.01), er=(-.15, -.13), hr=(-.24, -.01)),
 "recoil": _p(fl=(-.2, 0), fr=(-.25, 0), kl=(-.03, -.3), kr=(.0, -.26), hip=(.14, -.07), neck=(.26, -.36), head=(.32, -.44), el=(.03, -.5), hl=(-.12, -.63), er=(.3, -.2), hr=(.36, -.02)),
 "cower": _p(fl=(-.05, 0), fr=(.06, 0), kl=(-.02, -.24), kr=(.07, -.24), hip=(.05, -.46), neck=(.11, -.74), head=(.14, -.82), el=(-.08, -.7), hl=(-.16, -.82), er=(-.03, -.62), hr=(-.11, -.77)),
}
def pmix(a, b, u): return {k: (lerp(a[k][0], b[k][0], u), lerp(a[k][1], b[k][1], u)) for k in KEYS}
def walk(P, ph, amp=0.07):
    P = dict(P); s = math.sin(ph); c = math.cos(ph)
    P["fl"] = (P["fl"][0] + amp * s, P["fl"][1] - 0.05 * max(0, c)); P["fr"] = (P["fr"][0] - amp * s, P["fr"][1] - 0.05 * max(0, -c))
    P["kl"] = ((P["kl"][0] + P["fl"][0]) / 2 + 0.02, P["kl"][1]); P["kr"] = ((P["kr"][0] + P["fr"][0]) / 2 + 0.02, P["kr"][1])
    return P
def tremble(P, t, amt=0.006):
    P = dict(P)
    for k in ("hl", "hr", "head", "el", "er"): P[k] = (P[k][0] + amt * math.sin(t * 31 + len(k) * 2), P[k][1] + amt * math.sin(t * 27 + len(k)))
    return P
def rig(d, x, yb, hh, P, fill, rim=None):
    pts = {k: (x + P[k][0] * hh, yb + P[k][1] * hh) for k in KEYS}
    def draw(ox, oy, col):
        lw = int(hh * 0.075); tw = int(hh * 0.15)
        def L(a, b, w):
            pa, pb = pts[a], pts[b]; d.line([(pa[0] + ox, pa[1] + oy), (pb[0] + ox, pb[1] + oy)], fill=col, width=w)
            for q in (pa, pb): d.ellipse([q[0] + ox - w / 2, q[1] + oy - w / 2, q[0] + ox + w / 2, q[1] + oy + w / 2], fill=col)
        L("hip", "neck", tw); L("hip", "kr", lw + 2); L("kr", "fr", lw); L("hip", "kl", lw + 2); L("kl", "fl", lw)
        L("neck", "er", lw - 1); L("er", "hr", lw - 2); L("neck", "el", lw - 1); L("el", "hl", lw - 2)
        hx, hy = pts["head"]; r = hh * 0.058; d.ellipse([hx + ox - r, hy + oy - r * 1.1, hx + ox + r, hy + oy + r * 1.1], fill=col)
    if rim: draw(-3, -1, rim)
    draw(0, 0, fill)
    xs = [p[0] for p in pts.values()]; ys = [p[1] for p in pts.values()]
    return (min(xs) - hh * 0.06, min(ys) - hh * 0.08, max(xs) + hh * 0.06, max(ys) + 4)

def human_state(sc, t):
    """returns (visible, x, pose) for the human in each scene."""
    S, B, K, R, C = POSES["stand"], POSES["bow"], POSES["kneel"], POSES["recoil"], POSES["cower"]
    if sc in ("title", "room"): return False, HX, S
    if sc == "enter":
        if t < 1.5: return False, HX, S
        u = tseg(t, 1.5, 5.0); x = lerp(1190, HX, u)
        P = walk(S, t * 6.5) if u < 1 else S
        return True, x, tremble(P, t, 0.003)
    if sc in ("confess",): return True, HX, tremble(S, t, 0.004)
    if sc == "silence":
        return True, HX, tremble(pmix(S, C, 0.25 * tseg(t, 3.0, 5.0)), t, 0.005)
    if sc == "kneel":
        base = pmix(pmix(S, C, 0.25), K, tseg(t, 0.0, 1.3)); P = pmix(base, B, tseg(t, 1.5, 2.5))
        P = dict(P); sway = 0.012 * math.sin(t * 1.3); P["neck"] = (P["neck"][0], P["neck"][1] + sway); P["head"] = (P["head"][0], P["head"][1] + sway)
        return True, HX, tremble(P, t, 0.004)
    if sc == "enough":
        P = pmix(B, R, tseg(t, 0.5, 0.82)); return True, HX + 6 * max(0, 1 - (t - 0.5) * 5) * (1 if t > 0.5 else 0), tremble(P, t, 0.01)
    if sc == "thermal":
        th1, th2, th3, lv = ev("thermal", "th1"), ev("thermal", "th2"), ev("thermal", "th3"), ev("thermal", "leave")
        if t < th1[1] + 0.3: return True, HX, tremble(R, t, 0.012)
        if t < th3[0]:
            return True, HX, tremble(pmix(R, C, tseg(t, th1[1] + 0.3, th1[1] + 2.0)), t, 0.01)
        u = tseg(t, th3[0], th3[1] - 0.6); x = lerp(HX, 1200, u)
        P = walk(C, t * 4.5, 0.06) if 0 < u < 1 else C
        return (x < 1196), x, tremble(P, t, 0.008)
    return False, HX, S

def door_open(sc, t):
    if sc in ("title", "room"): return 0.0
    if sc == "enter": return tseg(t, 0.3, 2.0)
    if sc in ("confess", "silence", "kneel", "enough"): return 1.0
    if sc == "thermal":
        dc = ev("thermal", "leave")[1] - 1.1
        return 1.0 - tseg(t, dc - 1.0, dc)
    return 0.0

def draw_scene(sc, t, d, fire_level=1.0, gaze=0.0, speak=0.0, eye=1.0, with_human=True, dim=0.0):
    img = room().copy()
    rain(img, t); door(img, t, door_open(sc, t))
    fire(img, t, fire_level)
    android(img, t, gaze, speak, eye)
    particles(img, t, 30, 17, (80, 72, 56), speed=5, size=1.5, up=True, wob=10)
    lightpass(img, t, fire_level)
    hv = human_state(sc, t) if with_human else (False, 0, None)
    bbox = None
    if hv[0]:
        dd = ImageDraw.Draw(img); bbox = rig(dd, hv[1], HYB, HH, hv[2], (7, 5, 9), rim=(120, 60, 24))
    if dim > 0: img = Image.blend(img, Image.new("RGB", (W, H), (0, 0, 0)), dim)
    return img, hv, bbox

# ---- thermal
def thermal_lut():
    if "lut" in _R: return _R["lut"]
    stops = [(0, (4, 0, 24)), (0.2, (40, 0, 110)), (0.42, (150, 20, 120)), (0.6, (230, 60, 40)), (0.78, (255, 170, 20)), (1.0, (255, 250, 200))]
    xs = [s[0] * 255 for s in stops]; lut = np.stack([np.interp(np.arange(256), xs, [s[1][c] for s in stops]) for c in range(3)], 1).astype(np.uint8)
    _R["lut"] = lut; return lut

def sc_thermal_view(sc, t, d):
    th = {k: ev("thermal", k) for k in ("th1", "th2", "th3", "leave")}
    img, hv0, bbox = draw_scene("thermal", t, d, 1.0, 1.0, 0, 1.0, with_human=False)
    hv = human_state("thermal", t)
    base = img.convert("L").point(lambda v: min(255, int(v * 1.5) + 8))
    hl = Image.new("L", (W, H), 0); hd = ImageDraw.Draw(hl)
    bb = None
    if hv[0]:
        bb = rig(hd, hv[1], HYB, HH, hv[2], 255)
    halo = hl.filter(ImageFilter.GaussianBlur(16)).point(lambda v: min(255, int(v * 1.1)))
    heat = ImageChops.lighter(ImageChops.lighter(base, halo), hl)
    arr = np.array(heat); arr = np.clip(arr.astype(np.int16) + (np.random.default_rng(int(t * 24)).standard_normal(arr.shape) * 5).astype(np.int16), 0, 255).astype(np.uint8)
    out = Image.fromarray(thermal_lut()[arr])
    dd = ImageDraw.Draw(out)
    for y in range(0, H, 4): dd.line([(0, y), (W, y)], fill=(0, 0, 0), width=1)
    out = Image.blend(out, ImageChops.multiply(out, _R["vig"]), 0.4)
    # lens vignette
    lv = Image.new("L", (W, H), 0); ImageDraw.Draw(lv).ellipse([-260, -180, W + 260, H + 180], fill=255); lv = lv.filter(ImageFilter.GaussianBlur(60))
    out = Image.composite(out, Image.new("RGB", (W, H), (0, 0, 0)), lv)
    dd = ImageDraw.Draw(out); fm = F(18, mono=True); fs = F(15, mono=True)
    cyan = (120, 255, 235)
    dd.text((50, 40), "ANDROID // THERMAL OPTICS", font=fm, fill=cyan)
    if int(t * 2) % 2 == 0: dd.ellipse([1130, 44, 1146, 60], fill=(255, 60, 60))
    dd.text((1154, 40), "REC", font=fm, fill=cyan)
    dd.text((50, 66), "AMBIENT 14.2°C   FIRE 612°C", font=fs, fill=cyan)
    if bb and t > 1.2:
        a = tseg(t, 0.9, 1.6); x0, y0, x1, y1 = bb; L = 28
        for (cx, cy, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
            dd.line([(cx, cy), (cx + sx * L, cy)], fill=cyan, width=3); dd.line([(cx, cy), (cx, cy + sy * L)], fill=cyan, width=3)
        tx = max(60, x0 - 215); ty = y0 + 4
        lines = [("SUBJECT: HUMAN", 0.0)]
        bpm = int(np.interp(t, [0.9, th["th3"][0], th["leave"][0]], [152, 134, 104]))
        lines += [("PULSE: %d BPM" % bpm, th["th2"][0] - 0.2), ("STRESS: HIGH", th["th2"][0] + 0.6), ("WEAPONS: NONE", th["th3"][0] - 0.2), ("THREAT: NONE", th["th3"][0] + 0.6)]
        for i, (s, t0) in enumerate(lines):
            if t > max(t0, 1.4 + 0.2 * i):
                col = (140, 255, 170) if "NONE" in s else cyan
                dd.text((tx, ty + i * 24), s, font=fm, fill=col)
    # ECG
    ex0, ey0 = 920, 640; pts = []
    for i in range(160):
        u = (i / 160.0) * 3 + t * 2.2; ph = u % 1.0
        y = -34 * math.exp(-((ph - 0.3) / 0.025) ** 2) + 10 * math.exp(-((ph - 0.36) / 0.03) ** 2) + 6 * math.exp(-((ph - 0.6) / 0.06) ** 2)
        pts.append((ex0 + i * 2, ey0 - y))
    dd.line(pts, fill=(140, 255, 170), width=2)
    # glitch bars at cut / enter
    g = max(0, 1 - t * 4 if False else 0)
    return out

# ---- scenes
def s_title(t, d, p):
    img, hv, bb = draw_scene("title", t, d, 0.8, 0.0, 0.0, 0.8, dim=0.55 * (1 - tseg(t, 2.0, 6.0)) + 0.25)
    a = tseg(t, 0.4, 1.6) * (1 - tseg(t, d - 1.4, d - 0.3))
    title(img, "THE LIBRARY", "a scene about a monster, and a mercy that is easy to miss", a, y=250, size=48)
    return img

def s_room(t, d, p):
    img, hv, bb = draw_scene("room", t, d, 1.0, 0.0, 0.0, 1.0, dim=0.25 * (1 - tseg(t, 0, 2.0)))
    return img

def s_enter(t, d, p):
    img, hv, bb = draw_scene("enter", t, d, 0.95, 0.0, 0.0, 1.0)
    return img

def s_confess(t, d, p):
    a1, a2 = ev("confess", "ai1"), ev("confess", "ai2")
    sp = 1.0 if (a1[0] <= t <= a1[1] or a2[0] <= t <= a2[1]) else 0.0
    img, hv, bb = draw_scene("confess", t, d, 0.9, 0.0, sp, 1.0)
    return img

def s_silence(t, d, p):
    img, hv, bb = draw_scene("silence", t, d, 0.85, 0.0, 0.0, 0.9)
    return img

def s_kneel(t, d, p):
    img, hv, bb = draw_scene("kneel", t, d, 0.9, 0.0, 0.0, 0.9)
    return img

def s_enough(t, d, p):
    on = t >= 0.5; k = t - 0.5
    lvl = 1.0 + (1.5 * math.exp(-k * 2.2) if on else 0)
    img, hv, bb = draw_scene("enough", t, d, lvl, 1.0 if on else 0.0, 1.0 if on and k < 1.0 else 0.0, 1.0 + (0.6 if on else 0))
    if on:
        fl = math.exp(-k * 7) * 0.7; img = Image.blend(img, Image.new("RGB", (W, H), (255, 230, 190)), fl)
    return img

def s_thermal(t, d, p):
    if t < 0.9:    # the android turns
        k = tseg(t, 0.0, 0.8)
        img, hv, bb = draw_scene("thermal", t, d, 1.0, k, 0.0, 1.0 + 0.6 * k)
        return img
    img = sc_thermal_view("thermal", t, d)
    if t < 1.15:   # glitch on the cut
        arr = np.array(img); r = np.random.default_rng(int(t * 100))
        for _ in range(8):
            y = int(r.integers(0, H - 30)); h = int(r.integers(4, 26)); arr[y:y + h] = np.roll(arr[y:y + h], int(r.integers(-80, 80)), axis=1)
        img = Image.fromarray(arr)
    return img

def s_alone(t, d, p):
    s1, s2, fk = ev("alone", "s1"), ev("alone", "s2"), ev("alone", "flick")
    sp = 0.6 if (s1[0] <= t <= s1[1] or s2[0] <= t <= s2[1]) else 0.0
    tf = fk[0] + 1.5
    a = max(0.0, 1 - abs(t - tf) / 0.105)      # a flicker of roughly five frames
    img, hv, bb = draw_scene("alone", t, d, 1.0 - 0.35 * a, 0.0, sp, (0.85 + 0.15 * math.sin(t * 2)) * (1 - a))
    if a > 0: christ_seated(img, a)               # Christ, seated, flashing over the android's form
    return img

def s_end(t, d, p):
    img = Image.new("RGB", (W, H), (0, 0, 0))
    a = tseg(t, 0.6, 1.8) * (1 - tseg(t, d - 1.2, d - 0.1))
    label(img, 640, 330, "Did you see it?", 44, (235, 225, 205), a)
    return img

SCENE_FN = {"title": s_title, "room": s_room, "enter": s_enter, "confess": s_confess, "silence": s_silence, "kneel": s_kneel,
            "enough": s_enough, "thermal": s_thermal, "alone": s_alone, "end": s_end}
CAM = {"title": ((640, 360, 1.0), (640, 360, 1.04)), "room": ((640, 360, 1.04), (600, 420, 1.16)), "enter": ((600, 420, 1.16), (860, 390, 1.12)),
       "confess": ((860, 390, 1.12), (520, 440, 1.38)), "silence": ((520, 440, 1.38), (880, 400, 1.2)), "kneel": ((880, 400, 1.2), (900, 470, 1.25)),
       "enough": ((900, 470, 1.25), (860, 440, 1.3)), "alone": ((560, 470, 1.5), (640, 520, 1.85))}
CONT_IN = {"enter", "confess", "silence", "kneel", "enough", "thermal", "alone"}
CONT_OUT = {"room", "enter", "confess", "silence", "kneel", "enough", "thermal"}

SPK = {"n": (255, 255, 255), "a": (255, 205, 120), "as": (255, 205, 120), "h": (190, 212, 255), "e": (255, 150, 120)}
def subtitles(img, t):
    for s in SC:
        for z in s["sents"]:
            if z["text"] and z["who"] != "e" and z["start"] - 0.05 <= t <= z["end"] + 0.25:
                lines = textwrap.wrap(z["text"], 62)
                lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
                f = F(26); lh = 36; bh = lh * len(lines) + 20 + (20 if z.get("label") else 0); y0 = H - bh - 18
                d.rounded_rectangle([90, y0, W - 90, y0 + bh], 12, fill=(0, 0, 0, 160))
                yy = y0 + 8
                if z.get("label"):
                    lf = F(14, bold=True); tw = d.textlength(z["label"], font=lf); d.text(((W - tw) / 2, yy), z["label"], font=lf, fill=(150, 170, 215, 255)); yy += 20
                col = SPK.get(z["who"], (255, 255, 255)) + (255,)
                for i, ln in enumerate(lines):
                    tw = d.textlength(ln, font=f); d.text(((W - tw) / 2, yy + 2 + i * lh), ln, font=f, fill=col)
                img.paste(lay, (0, 0), lay); return img
    return img

def ov_enough(img, t):
    on = t >= 0.5; k = t - 0.5
    if not on: return img
    a = tseg(t, 0.5, 0.65) * (1 - tseg(t, 2.0, 2.8)); sh = math.exp(-k * 3) * 14
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay); f = F(150, bold=True); s_ = "ENOUGH."; tw = ld.textlength(s_, font=f)
    ld.text(((W - tw) / 2 + 4, 250 + 4), s_, font=f, fill=(0, 0, 0, int(220 * a)))
    ld.text(((W - tw) / 2, 250), s_, font=f, fill=(255, 235, 215, int(255 * a)))
    img.paste(lay, (0, 0), lay)
    return img.transform((W, H), Image.AFFINE, (1, 0, math.sin(t * 100) * sh, 0, 1, math.cos(t * 83) * sh))

def camera(img, sc, p):
    if sc["id"] not in CAM: return img
    (x0, y0, z0), (x1, y1, z1) = CAM[sc["id"]]; u = ease(p)
    cx, cy, z = lerp(x0, x1, u), lerp(y0, y1, u), lerp(z0, z1, u)
    w, h = W / z, H / z; xa = clamp(cx - w / 2, 0, W - w); ya = clamp(cy - h / 2, 0, H - h)
    return img.crop((int(xa), int(ya), int(xa + w), int(ya + h))).resize((W, H), Image.BILINEAR)

def frame(i):
    t = i / FPS
    sc = next((s for s in SC if s["start"] <= t < s["end"]), SC[-1])
    tt = t - sc["start"]; dur = sc["end"] - sc["start"]; p = clamp(tt / dur)
    img = SCENE_FN[sc["id"]](tt, dur, p).convert("RGB")
    img = camera(img, sc, p)
    if sc["id"] == "enough": img = ov_enough(img, tt)
    fi = 1 if sc["id"] in CONT_IN else tt / 0.6
    fo = 1 if sc["id"] in CONT_OUT else (dur - tt) / 0.8
    fade = min(1, fi, fo)
    if fade < 1: img = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), img, clamp(fade))
    img = subtitles(img, t)
    return img.tobytes()

if __name__ == "__main__":
    n = int(TOTAL * FPS) + FPS
    if len(sys.argv) > 1:
        import os; os.makedirs("stills", exist_ok=True)
        qs = [float(x) for x in sys.argv[1:]] if sys.argv[1] != "grid" else None
        if qs is None:
            for sc in SC:
                for q in (0.2, 0.55, 0.9):
                    i = int((sc["start"] + (sc["end"] - sc["start"]) * q) * FPS); Image.frombytes("RGB", (W, H), frame(i)).save(f"stills/{sc['id']}_{int(q*100)}.png")
        else:
            for q in qs: Image.frombytes("RGB", (W, H), frame(int(q * FPS))).save(f"stills/t{int(q*10):04d}.png")
        sys.exit()
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-i", "mix.wav", "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                           "-shortest", "-movflags", "+faststart", "the_library.mp4"], stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for k, b in enumerate(pool.imap(frame, range(n), chunksize=6)):
            ff.stdin.write(b)
            if k % 240 == 0: print(k, "/", n, flush=True)
    ff.stdin.close(); ff.wait()
