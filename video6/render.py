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

# ================================================================= Jesus and the Gauntlet
def softglow(img, layer, radius=40, strength=1.0):
    g = layer.resize((W // 4, H // 4)).filter(ImageFilter.GaussianBlur(radius / 4)).resize((W, H))
    if strength != 1.0: g = g.point(lambda v: min(255, int(v * strength)))
    img.paste(ImageChops.add(img, g))
OFF = 0
EV = {}
for _s in SC:
    EV[_s["id"]] = {z["tag"]: (z["start"] - _s["start"], z["end"] - _s["start"]) for z in _s["sents"] if z.get("tag")}
def ev(sc, tag): return EV[sc][tag]
def tseg(t, a, b): return ease((t - a) / (b - a)) if b > a else (1.0 if t >= a else 0.0)
def pulse(t, f): return 0.5 + 0.5 * math.sin(t * f)

SKIN = [(228, 184, 142), (208, 160, 118), (186, 136, 96), (160, 112, 78), (236, 196, 160)]
ROBES = [(176, 140, 100), (128, 100, 74), (150, 80, 60), (90, 110, 120), (170, 160, 120), (110, 70, 80), (96, 120, 80), (190, 170, 140), (120, 96, 120), (160, 120, 70)]
_C = {}

def square():
    if "bg" in _C: return _C["bg"]
    img = gradient((98, 156, 214), (252, 222, 168), "sq_sky"); d = ImageDraw.Draw(img)
    d.ellipse([930, 70, 1010, 150], fill=(255, 244, 200))
    d.polygon([(0, 400), (180, 340), (360, 392), (560, 330), (760, 388), (980, 322), (1280, 380), (1280, 440), (0, 440)], fill=(206, 176, 134))
    rng = random.Random(9)
    sandy = [(226, 196, 150), (214, 182, 134), (234, 206, 162), (200, 168, 124)]
    x = -20
    while x < W:
        w = rng.randint(120, 210); h = rng.randint(120, 230); col = rng.choice(sandy)
        d.rectangle([x, 440 - h, x + w, 440], fill=col); d.rectangle([x, 440 - h, x + w, 440 - h + 10], fill=tuple(int(c * 0.86) for c in col))
        if rng.random() < 0.4: d.pieslice([x + w * 0.25, 440 - h - w * 0.2, x + w * 0.75, 440 - h + w * 0.2], 180, 360, fill=col)
        for k in range(rng.randint(1, 3)):
            wx = x + 18 + k * (w - 40) / 3; wy = 440 - h + 30
            d.rounded_rectangle([wx, wy, wx + 20, wy + 34], 8, fill=(86, 64, 48))
        d.rounded_rectangle([x + w / 2 - 18, 440 - 60, x + w / 2 + 18, 440], 16, fill=(70, 52, 40))
        x += w + rng.randint(-6, 8)
    # awnings
    for ax in (60, 330, 900, 1130):
        for k in range(6): d.polygon([(ax + k * 22, 396), (ax + k * 22 + 22, 396), (ax + k * 22 + 28, 428), (ax + k * 22 + 6, 428)], fill=(190, 70, 60) if k % 2 == 0 else (240, 230, 210))
    d.rectangle([0, 438, W, H], fill=(214, 184, 140))
    for i in range(14): d.line([(i * 120 - 300, 720), (640 + (i - 7) * 36, 440)], fill=(196, 164, 120), width=2)
    for j in range(1, 7): d.line([(0, 440 + j * j * 7), (W, 440 + j * j * 7)], fill=(198, 166, 122), width=2)
    # palms
    for px in (210, 1060):
        d.line([(px, 440), (px + 8, 280)], fill=(110, 80, 50), width=8)
        for a in range(-3, 4): d.line([(px + 8, 280), (px + 8 + a * 34, 262 + abs(a) * 14)], fill=(70, 120, 60), width=7)
    _C["bg"] = img
    return img

def cfig(img, x, yb, h, robe, skin=SKIN[0], hair=None, beard=False, helmet=False, sash=None, L=None, R=None, face=None, alpha=1.0,
         armor=False, shield=False, spear=False, mouth="flat", brow=0.0, cut=None, rot=0.0, hood=False, eyes="open", wide=1.0, hscale=1.0, brow1=0.0, tunic=False, mantle=None, headwrap=None):
    """frontal figure. returns world positions of hands and head."""
    yb = yb - OFF
    if cut is not None: cut = cut - OFF
    w = int(h * 1.8); hh = int(h * 1.14); lay = Image.new("RGBA", (w, hh), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    cx = w / 2; gy = hh - 4
    U = lambda ux, uy: (cx + ux * h * wide, gy + uy * h)
    L = L or (-0.2, -0.42); R = R or (0.2, -0.42)
    shade = tuple(int(c * 0.82) for c in robe)
    sw_ = 0.16 if tunic else 0.13
    sL, sR = U(-sw_, -0.77), U(sw_, -0.77)
    def arm(S, Hd, col):
        S = S; E0 = U(*Hd); mid = ((S[0] + E0[0]) / 2, (S[1] + E0[1]) / 2); vx, vy = E0[0] - S[0], E0[1] - S[1]; n = math.hypot(vx, vy) or 1
        p1 = (-vy / n * 0.05 * h, vx / n * 0.05 * h); p2 = (-p1[0], -p1[1]); p = p1 if p1[1] > p2[1] else p2
        E = (mid[0] + p[0], mid[1] + p[1]); wd = int(h * 0.062)
        if tunic:     # short sleeve to the elbow, bare forearm
            w1 = int(h * 0.085); w2 = int(h * 0.066)
            d.line([S, E], fill=col, width=w1); d.ellipse([S[0] - w1 / 2, S[1] - w1 / 2, S[0] + w1 / 2, S[1] + w1 / 2], fill=col); d.ellipse([E[0] - w1 / 2, E[1] - w1 / 2, E[0] + w1 / 2, E[1] + w1 / 2], fill=col)
            d.line([E, E0], fill=skin, width=w2); d.ellipse([E[0] - w2 / 2, E[1] - w2 / 2, E[0] + w2 / 2, E[1] + w2 / 2], fill=skin)
        else:
            d.line([S, E, E0], fill=col, width=wd, joint="curve")
            for q in (S, E): d.ellipse([q[0] - wd / 2, q[1] - wd / 2, q[0] + wd / 2, q[1] + wd / 2], fill=col)
        d.ellipse([E0[0] - h * 0.032, E0[1] - h * 0.032, E0[0] + h * 0.032, E0[1] + h * 0.032], fill=skin)
    # back-most: spear
    if spear:
        hx, hy = U(*R); d.line([(hx, hy + h * 0.55), (hx - 4, hy - h * 0.6)], fill=(110, 80, 50), width=5); d.polygon([(hx - 4, hy - h * 0.72), (hx - 11, hy - h * 0.58), (hx + 3, hy - h * 0.58)], fill=(200, 205, 214))
    # body
    if tunic:     # a straight knee-length tunic, belted at the waist, bare legs and sandals
        for sg in (-1, 1):
            d.line([U(sg * 0.07, -0.3), U(sg * 0.075, -0.035)], fill=skin, width=int(h * 0.068))
            d.rounded_rectangle([cx + sg * 0.078 * h * wide - h * 0.05, gy - h * 0.03, cx + sg * 0.078 * h * wide + h * 0.05, gy + 3], 4, fill=(120, 86, 56), outline=(84, 58, 38))
        d.polygon([U(-0.16, -0.78), U(0.16, -0.78), U(0.155, -0.5), U(0.185, -0.27), U(-0.185, -0.27), U(-0.155, -0.5)], fill=robe)
        d.polygon([U(0.0, -0.78), U(0.16, -0.78), U(0.155, -0.5), U(0.185, -0.27), U(0.02, -0.27)], fill=shade)
        d.line([U(0.0, -0.78), U(0.0, -0.27)], fill=tuple(int(c * 0.7) for c in robe), width=2)
        d.line([U(-0.185, -0.275), U(0.185, -0.275)], fill=tuple(int(c * 0.7) for c in robe), width=3)
        if mantle:    # a mantle draped diagonally from the shoulder across the body
            md = tuple(int(c * 0.78) for c in mantle)
            d.polygon([U(-0.18, -0.81), U(-0.03, -0.81), U(0.18, -0.5), U(0.19, -0.26), U(0.04, -0.26), U(-0.18, -0.6)], fill=mantle)
            d.line([U(-0.03, -0.81), U(0.18, -0.5)], fill=md, width=3); d.line([U(-0.18, -0.6), U(0.04, -0.26)], fill=md, width=3)
            for k in range(3): d.line([U(0.06 + k * 0.045, -0.3), U(0.08 + k * 0.045, -0.26)], fill=md, width=2)
    else:
        d.polygon([U(-0.13, -0.78), U(0.13, -0.78), U(0.17, -0.5), U(0.23, 0.0), U(-0.23, 0.0), U(-0.17, -0.5)], fill=robe)
        d.polygon([U(-0.02, -0.78), U(0.13, -0.78), U(0.17, -0.5), U(0.23, 0.0), U(0.05, 0.0)], fill=shade)
    if sash and tunic:
        d.polygon([U(-0.158, -0.53), U(0.158, -0.53), U(0.156, -0.47), U(-0.156, -0.47)], fill=sash); d.ellipse([cx + 0.05 * h * wide, gy - 0.54 * h, cx + 0.1 * h * wide, gy - 0.46 * h], fill=tuple(min(255, int(c * 1.25)) for c in sash))
    elif sash: d.polygon([U(-0.17, -0.5), U(0.17, -0.5), U(0.18, -0.45), U(-0.18, -0.45)], fill=sash); d.polygon([U(0.1, -0.45), U(0.15, -0.45), U(0.15, -0.2), U(0.1, -0.2)], fill=sash)
    if armor:
        d.polygon([U(-0.14, -0.78), U(0.14, -0.78), U(0.15, -0.55), U(-0.15, -0.55)], fill=(176, 130, 66)); d.line([U(0, -0.78), U(0, -0.55)], fill=(130, 92, 44), width=2)
        d.ellipse([cx - h * 0.03, gy - h * 0.7, cx + h * 0.03, gy - h * 0.64], outline=(130, 92, 44), width=2)
        for k in range(6): d.polygon([U(-0.17 + k * 0.057, -0.5), U(-0.12 + k * 0.057, -0.5), U(-0.12 + k * 0.057, -0.36), U(-0.17 + k * 0.057, -0.36)], fill=(136, 78, 44))
    arm(sL, L, robe); arm(sR, R, robe)
    if shield:
        sx, sy = U(*L); d.ellipse([sx - h * 0.16, sy - h * 0.16, sx + h * 0.16, sy + h * 0.16], fill=(160, 40, 36), outline=(190, 150, 70), width=4); d.ellipse([sx - 6, sy - 6, sx + 6, sy + 6], fill=(190, 150, 70))
    # head
    hx, hy = U(0, -0.88); r = h * 0.07 * hscale
    if hair: d.ellipse([hx - r * 1.35, hy - r * 1.25, hx + r * 1.35, hy + r * 2.4], fill=hair)
    d.rectangle([hx - r * 0.35, hy + r * 0.6, hx + r * 0.35, hy + r * 1.25], fill=skin)
    fc = face if face else skin
    d.ellipse([hx - r, hy - r * 1.1, hx + r, hy + r * 1.1], fill=fc)
    if hood: d.pieslice([hx - r * 1.35, hy - r * 1.5, hx + r * 1.35, hy + r * 1.4], 180, 360, fill=shade)
    if headwrap:
        hd_ = tuple(int(c * 0.75) for c in headwrap)
        for sg in (-1, 1): d.polygon([(hx + sg * r * 1.2, hy - r * 0.4), (hx + sg * r * 1.55, hy + r * 2.4), (hx + sg * r * 0.85, hy + r * 2.2), (hx + sg * r * 0.95, hy + r * 0.1)], fill=headwrap, outline=hd_)
        d.pieslice([hx - r * 1.28, hy - r * 1.5, hx + r * 1.28, hy + r * 0.85], 180, 360, fill=headwrap, outline=hd_)
        d.arc([hx - r * 1.28, hy - r * 1.2, hx + r * 1.28, hy - r * 0.1], 195, 345, fill=(56, 42, 34), width=max(3, int(r * 0.22)))
    if beard: d.polygon([(hx - r * 0.95, hy + r * 0.1), (hx + r * 0.95, hy + r * 0.1), (hx + r * 0.6, hy + r * 1.6), (hx, hy + r * 1.95), (hx - r * 0.6, hy + r * 1.6)], fill=hair or (90, 60, 40))
    ey = hy - r * 0.12
    if eyes == "blank":
        for s in (-1, 1): d.ellipse([hx + s * r * 0.42 - r * 0.26, ey - r * 0.26, hx + s * r * 0.42 + r * 0.26, ey + r * 0.26], fill=(250, 250, 250), outline=(60, 44, 40)); d.ellipse([hx + s * r * 0.42 - 2.2, ey - 2.2, hx + s * r * 0.42 + 2.2, ey + 2.2], fill=(30, 24, 22))
    elif eyes == "closed":
        for s in (-1, 1): d.arc([hx + s * r * 0.42 - 4, ey - 3, hx + s * r * 0.42 + 4, ey + 3], 200, 340, fill=(40, 30, 28), width=2)
    else:
        for s in (-1, 1): d.ellipse([hx + s * r * 0.42 - 2.5, ey - 2.5, hx + s * r * 0.42 + 2.5, ey + 2.5], fill=(36, 28, 26))
    for s in (-1, 1): d.line([(hx + s * r * 0.2, ey - r * (0.28 + brow * 0.2 * (1 if s == -1 else 1))), (hx + s * r * 0.7, ey - r * (0.28 - brow * 0.28 * 1))], fill=(50, 36, 30), width=2) if brow else None
    if brow1:
        d.line([(hx - r * 0.7, ey - r * 0.5), (hx - r * 0.2, ey - r * 0.5)], fill=(50, 36, 30), width=2)
        d.arc([hx + r * 0.1, ey - r * 1.45, hx + r * 0.85, ey - r * 0.55], 200, 340, fill=(50, 36, 30), width=3)
    my = hy + r * 0.52
    if mouth == "smile": d.arc([hx - r * 0.45, my - r * 0.3, hx + r * 0.45, my + r * 0.35], 20, 160, fill=(150, 70, 60), width=2)
    elif mouth == "laugh": d.pieslice([hx - r * 0.5, my - r * 0.25, hx + r * 0.5, my + r * 0.6], 0, 180, fill=(90, 30, 36))
    elif mouth == "shout": d.ellipse([hx - r * 0.38, my - r * 0.22, hx + r * 0.38, my + r * 0.55], fill=(80, 24, 28))
    elif mouth == "o": d.ellipse([hx - r * 0.18, my - r * 0.1, hx + r * 0.18, my + r * 0.3], fill=(90, 36, 40))
    elif mouth == "frown": d.arc([hx - r * 0.4, my, hx + r * 0.4, my + r * 0.5], 200, 340, fill=(120, 50, 46), width=2)
    else: d.line([(hx - r * 0.3, my + 2), (hx + r * 0.3, my + 2)], fill=(130, 60, 54), width=2)
    if helmet:
        d.pieslice([hx - r * 1.2, hy - r * 1.55, hx + r * 1.2, hy + r * 0.7], 180, 360, fill=(188, 140, 70)); d.rectangle([hx - r * 1.2, hy - r * 0.45, hx + r * 1.2, hy - r * 0.3], fill=(150, 108, 50))
        d.rectangle([hx - r * 1.2, hy - r * 0.4, hx - r * 0.85, hy + r * 1.0], fill=(176, 128, 62)); d.rectangle([hx + r * 0.85, hy - r * 0.4, hx + r * 1.2, hy + r * 1.0], fill=(176, 128, 62))
        d.polygon([(hx - r * 0.9, hy - r * 1.35), (hx + r * 0.9, hy - r * 1.35), (hx + r * 0.6, hy - r * 2.3), (hx - r * 0.6, hy - r * 2.3)], fill=(190, 40, 36))
    if cut is not None:
        ly = int(cut - (yb - gy)); lay.paste((0, 0, 0, 0), (0, max(0, ly), w, hh))
    if alpha < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * alpha)))
    pos = {"L": (x - w / 2 + U(*L)[0], yb - gy + U(*L)[1]), "R": (x - w / 2 + U(*R)[0], yb - gy + U(*R)[1]), "head": (x - w / 2 + hx, yb - gy + hy)}
    if rot:
        pad = Image.new("RGBA", (w * 2, hh * 2), (0, 0, 0, 0)); pad.paste(lay, (w // 2, hh)); lay2 = pad.rotate(rot, center=(w, hh * 2 - 4), resample=Image.BICUBIC)
        img.paste(lay2, (int(x - w), int(yb - (hh * 2 - 4))), lay2)
    else:
        img.paste(lay, (int(x - w / 2), int(yb - gy)), lay)
    return pos

def gauntlet(img, pos, t, s=1.0, g=1.0):
    g = min(g, 1.5); x, y = pos; lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay)
    rr = (46 + 12 * math.sin(t * 5)) * s * (0.6 + 0.9 * g)
    ld.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(int(255 * min(1, 0.45 + 0.4 * g)), int(220 * min(1, 0.45 + 0.4 * g)), int(120 * min(1, 0.4 + 0.3 * g))))
    softglow(img, lay, 36 * s, 1.0 + 0.5 * g)
    d = ImageDraw.Draw(img); r = 15 * s
    d.ellipse([x - r, y - r * 1.1, x + r, y + r * 1.1], fill=(230, 180, 50), outline=(150, 100, 20), width=2)
    for k in range(4): d.rectangle([x - r + k * r * 0.5, y - r * 1.5, x - r + k * r * 0.5 + r * 0.38, y - r * 0.7], fill=(230, 180, 50), outline=(150, 100, 20))
    gem = [(150, 70, 230), (60, 130, 255), (230, 60, 60), (255, 150, 40), (60, 200, 90), (255, 230, 60)]
    for k, c in enumerate(gem):
        gx = x - r * 0.75 + (k % 3) * r * 0.75; gy = y - r * 0.2 + (k // 3) * r * 0.55; d.ellipse([gx - 3.2 * s, gy - 3.2 * s, gx + 3.2 * s, gy + 3.2 * s], fill=c, outline=(255, 255, 255))
    if g > 0.2:
        lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay)
        for k, c in enumerate(gem):
            a = t * 2 + k * 1.05; gx = x + math.cos(a) * r * 1.9; gy = y + math.sin(a) * r * 1.9; ld.ellipse([gx - 4, gy - 4, gx + 4, gy + 4], fill=c)
        softglow(img, lay, 10, 1.4)


def bubble(img, x, y, text, size=22, a=1.0, tail=None, col=(252, 250, 244)):
    if a <= 0: return
    y = y - OFF + 20
    if tail: tail = (tail[0], tail[1] - OFF + 20)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); f = F(size)
    tw = d.textlength(text, font=f); x0, y0, x1, y1 = x - tw / 2 - 16, y - 8, x + tw / 2 + 16, y + size + 14
    d.rounded_rectangle([x0, y0, x1, y1], 16, fill=col + (int(240 * a),), outline=(70, 50, 36, int(255 * a)), width=2)
    if tail: d.polygon([(x - 9, y1 - 2), (x + 9, y1 - 2), tail], fill=col + (int(240 * a),))
    d.text((x - tw / 2, y), text, font=f, fill=(46, 36, 30, int(255 * a))); img.paste(lay, (0, 0), lay)


JESUS = dict(robe=(240, 235, 222), skin=SKIN[0], hair=(100, 68, 46), beard=True, sash=(120, 84, 52))
_HUDQ = []
def HUD(fn): _HUDQ.append(fn)
def hlabel(*a, **k): HUD(lambda im: label(im, *a, **k))
# ================================================================= Death takes a service call
BONE = (238, 232, 216); BONE_D = (150, 140, 118); CLOAK = (36, 34, 54); CLOAK_D = (22, 20, 34)
GY = 626                                  # ground line for the characters

def death(img, x, yb, h=320, t=0.0, flip=False, jaw=0.0, eyes="norm", look=(0.0, 0.0), L=None, R=None, scythe=True, sa=-6, lean=0.0, bend=0.0, walk=0.0,
          watch=False, alpha=1.0, whiten=0.0, sweat=0.0, brow=0.0, foot=None):
    w = int(h * 2.3); hh = int(h * 1.45); lay = Image.new("RGBA", (w, hh), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); cx = w / 2; gy = hh - 8
    ys = 1 - 0.14 * bend
    U = lambda ux, uy: (cx + ux * h, gy + uy * h * ys + 0.07 * h * bend)
    sway = math.sin(walk * 2) * 0.025
    L = L or (-0.24, -0.42 + 0.01 * math.sin(t * 2)); R = R or (0.27, -0.46)
    def arm(S, Hd, hand=True):
        E0 = U(*Hd); vx, vy = E0[0] - S[0], E0[1] - S[1]; n = math.hypot(vx, vy) or 1; mid = ((S[0] + E0[0]) / 2, (S[1] + E0[1]) / 2)
        p1 = (-vy / n * 0.06 * h, vx / n * 0.06 * h); p = p1 if p1[1] > 0 else (-p1[0], -p1[1]); E = (mid[0] + p[0], mid[1] + p[1]); wd = int(h * 0.085)
        d.line([S, E, E0], fill=CLOAK, width=wd, joint="curve")
        for q in (S, E): d.ellipse([q[0] - wd / 2, q[1] - wd / 2, q[0] + wd / 2, q[1] + wd / 2], fill=CLOAK)
        d.ellipse([E0[0] - h * 0.03, E0[1] - h * 0.03, E0[0] + h * 0.03, E0[1] + h * 0.03], fill=BONE, outline=BONE_D)
        for k in range(3): d.line([E0, (E0[0] + (k - 1) * h * 0.02, E0[1] + h * 0.045)], fill=BONE, width=max(2, int(h * 0.011)))
        return E0
    hR = U(*R)
    if scythe:        # the pole goes behind the arm
        a = math.radians(sa); dx, dy = math.sin(a), -math.cos(a)
        p0 = (hR[0] - dx * h * 0.35, hR[1] - dy * h * 0.35); p1 = (hR[0] + dx * h * 1.0, hR[1] + dy * h * 1.0)
        d.line([p0, p1], fill=(92, 66, 44), width=int(h * 0.02))
        bx, by = p1; d.polygon([(bx, by), (bx - h * 0.3 * math.cos(a) - dx * h * 0.02, by - h * 0.3 * math.sin(a) * 0 + h * 0.05), (bx - h * 0.28, by + h * 0.1), (bx - h * 0.02, by + h * 0.03)], fill=(190, 198, 214), outline=(120, 128, 146))
    # legs (bony) + cloak
    for sg in (-1, 1):
        fx = sg * 0.085 + (math.sin(walk * 2 + (0 if sg > 0 else math.pi)) * 0.07 if walk else 0); fy = -0.0 - max(0, math.cos(walk * 2 + (0 if sg > 0 else math.pi))) * 0.05 * (1 if walk else 0)
        if foot and sg > 0: fx, fy = foot
        d.line([U(sg * 0.07, -0.08), U(fx, fy - 0.01)], fill=BONE, width=int(h * 0.022)); d.ellipse([U(fx, fy)[0] - h * 0.04, U(fx, fy)[1] - h * 0.015, U(fx, fy)[0] + h * 0.04, U(fx, fy)[1] + h * 0.015], fill=BONE, outline=BONE_D)
    pts = [U(-0.12, -0.76), U(0.12, -0.76), U(0.19, -0.5), U(0.27, -0.03)]
    for k in range(9): pts.append(U(0.27 - k * 0.0675 + sway * (k % 2 * 2 - 1), -0.0 if k % 2 == 0 else -0.045))
    pts += [U(-0.27, -0.03), U(-0.19, -0.5)]
    d.polygon(pts, fill=CLOAK); d.polygon([U(0.01, -0.76), U(0.12, -0.76), U(0.19, -0.5), U(0.27, -0.03), U(0.05, -0.03)], fill=CLOAK_D)
    d.polygon([U(-0.14, -0.78), U(0.14, -0.78), U(0.12, -0.66), U(-0.12, -0.66)], fill=CLOAK_D)             # shoulders
    # hood and skull
    hx, hy = U(0, -0.85)
    d.ellipse([hx - h * 0.125, hy - h * 0.13, hx + h * 0.125, hy + h * 0.14], fill=CLOAK); d.polygon([(hx - h * 0.1, hy - h * 0.07), (hx, hy - h * 0.2), (hx + h * 0.1, hy - h * 0.07)], fill=CLOAK)
    d.ellipse([hx - h * 0.088, hy - h * 0.088, hx + h * 0.088, hy + h * 0.1], fill=(10, 8, 16))
    d.ellipse([hx - h * 0.066, hy - h * 0.074, hx + h * 0.066, hy + h * 0.074], fill=BONE, outline=BONE_D)
    d.polygon([(hx - h * 0.012, hy + h * 0.012), (hx + h * 0.012, hy + h * 0.012), (hx, hy + h * 0.03)], fill=(30, 24, 30))
    ex = h * 0.03; ey = hy - h * 0.012
    for sg in (-1, 1):
        cxk = hx + sg * ex; r1 = h * (0.024 if eyes != "wide" else 0.032)
        if eyes in ("shut", "squint"):
            d.arc([cxk - r1, ey - r1 * 0.6, cxk + r1, ey + r1 * 0.9], 200, 340, fill=(20, 16, 24), width=max(3, int(h * 0.01))) if eyes == "shut" else d.line([(cxk - r1, ey), (cxk + r1, ey)], fill=(20, 16, 24), width=max(3, int(h * 0.012)))
        else:
            d.ellipse([cxk - r1, ey - r1 * 1.15, cxk + r1, ey + r1 * 1.15], fill=(14, 10, 20))
            if eyes == "roll": px, py = math.cos(t * 7) * r1 * 0.5, math.sin(t * 7) * r1 * 0.5 - r1 * 0.2
            else: px, py = look[0] * r1 * 0.5, look[1] * r1 * 0.5
            d.ellipse([cxk + px - h * 0.007, ey + py - h * 0.007, cxk + px + h * 0.007, ey + py + h * 0.007], fill=(255, 255, 255))
        if brow: d.line([(cxk - r1, ey - r1 * 1.5 - brow * h * 0.01 * sg), (cxk + r1, ey - r1 * 1.5 + brow * h * 0.01 * sg)], fill=CLOAK_D, width=3)
    # teeth + jaw
    ty = hy + h * 0.055
    d.rectangle([hx - h * 0.04, ty - h * 0.012, hx + h * 0.04, ty + h * 0.008], fill=BONE, outline=BONE_D)
    for k in range(-2, 3): d.line([(hx + k * h * 0.016, ty - h * 0.012), (hx + k * h * 0.016, ty + h * 0.008)], fill=BONE_D, width=1)
    jy = lerp(ty + h * 0.012, gy - 0.03 * h, clamp(jaw)) if jaw > 0.01 else ty + h * 0.012
    d.polygon([(hx - h * 0.042, jy - h * 0.01), (hx + h * 0.042, jy - h * 0.01), (hx + h * 0.03, jy + h * 0.026), (hx - h * 0.03, jy + h * 0.026)], fill=BONE, outline=BONE_D)
    for k in range(-2, 3): d.line([(hx + k * h * 0.016, jy - h * 0.01), (hx + k * h * 0.016, jy + h * 0.004)], fill=BONE_D, width=1)
    arm(U(-0.13, -0.72), L); arm(U(0.13, -0.72), R)
    if watch:
        wx, wy = U(*L); d.ellipse([wx - h * 0.026, wy - h * 0.045, wx + h * 0.026, wy + h * 0.007], fill=(232, 192, 70), outline=(150, 112, 30), width=2); d.ellipse([wx - h * 0.017, wy - h * 0.036, wx + h * 0.017, wy - 0.002 * h], fill=(250, 250, 244))
        d.line([(wx, wy - h * 0.019), (wx + 0.008 * h * math.cos(t * 3), wy - h * 0.019 + 0.008 * h * math.sin(t * 3))], fill=(40, 30, 20), width=2)
    if sweat > 0:
        for k in range(3):
            u = (t * 0.9 + k / 3) % 1; sx = hx + (k - 1) * h * 0.11; sy = hy - h * 0.05 + u * h * 0.14
            d.polygon([(sx, sy - 11), (sx - 5, sy), (sx + 5, sy)], fill=(150, 210, 255)); d.ellipse([sx - 5, sy - 4, sx + 5, sy + 7], fill=(150, 210, 255))
    if whiten > 0:
        tint = Image.new("RGBA", lay.size, (255, 252, 236, 255)); a_ = lay.split()[3]; lay = Image.blend(lay, tint, clamp(whiten)); lay.putalpha(a_)
    if flip: lay = lay.transpose(Image.FLIP_LEFT_RIGHT)
    if lean: lay = lay.rotate(-lean if not flip else lean, center=(cx, gy), resample=Image.BICUBIC)
    if alpha < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * alpha)))
    img.paste(lay, (int(x - w / 2), int(yb - gy)), lay)
    sgf = -1 if flip else 1
    pos = lambda p_: (x + sgf * (p_[0] - cx), yb - gy + p_[1])
    return {"head": pos((hx, hy)), "L": pos(U(*L)), "R": pos(U(*R)), "shoulder": pos(U(0.1, -0.74)), "jaw": pos((hx, jy))}

DOGO = (84, 74, 60)
def skulldog(img, x, yb, s=1.0, t=0.0, flip=False, mode="stand", alpha=1.0, tongue=1.0, ph=None, tilt=0.0):
    """a chunky cartoon skeleton dog: dark ribcage with white ribs, a clear skull head, floppy ear, lolling tongue, wagging tail."""
    w, hh = int(320 * s), int(230 * s); lay = Image.new("RGBA", (w, hh), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); cx = w * 0.42; gy = hh - 8
    P = lambda ux, uy: (cx + ux * s, gy + uy * s)
    ph = (t * 14 if mode == "run" else 0.0) if ph is None else ph
    bob = abs(math.sin(ph)) * 8 if mode == "run" else math.sin(t * 6) * 1.5
    def bone(a_, b_, w_):
        d.line([P(*a_), P(*b_)], fill=DOGO, width=int(w_ * s + 4)); d.line([P(*a_), P(*b_)], fill=BONE, width=int(w_ * s))
        for q in (a_, b_): c = P(*q); r = w_ * s * 0.85; d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=BONE, outline=DOGO, width=2)
    for sx, hind, off in [(-36, True, 0.0), (-22, True, 3.1), (34, False, 3.1), (46, False, 0.0)]:      # legs, back ones first
        sw = math.sin(ph + off) * (28 if mode == "run" else 3); lift = max(0, math.cos(ph + off)) * (16 if mode == "run" else 0)
        top = (sx, -52 - bob); knee = (sx + sw * 0.5 + (10 if hind else -6), -30 - bob - lift * 0.5); paw = (sx + sw, -6 - lift)
        bone(top, knee, 9); bone(knee, paw, 8); c = P(*paw); d.ellipse([c[0] - 12 * s, c[1] - 5 * s, c[0] + 12 * s, c[1] + 6 * s], fill=BONE, outline=DOGO, width=2)
    tx, ty = -58, -78 - bob; ang = math.sin(t * 16) * 0.55 - 0.7                                                   # tail
    for k in range(5):
        nx = tx - 13 * math.cos(ang + k * 0.15); ny = ty + 13 * math.sin(ang + k * 0.15) - 8; bone((tx, ty), (nx, ny), 6); tx, ty = nx, ny
    d.rounded_rectangle([P(-62, -96 - bob)[0], P(-62, -96 - bob)[1], P(46, -36 - bob)[0], P(46, -36 - bob)[1]], int(20 * s), fill=(54, 48, 56), outline=DOGO, width=3)     # dark ribcage
    for k in range(6):
        rx = -48 + k * 17; d.arc([P(rx - 10, -92 - bob)[0], P(rx - 10, -92 - bob)[1], P(rx + 10, -40 - bob)[0], P(rx + 10, -40 - bob)[1]], 280, 80, fill=BONE, width=max(4, int(7 * s)))
    d.line([P(-58, -94 - bob), P(44, -94 - bob)], fill=BONE, width=max(5, int(9 * s)))                          # spine
    hx, hy = 70, -100 - bob                                                                                       # head
    d.polygon([P(hx - 16, hy - 14), P(hx - 40, hy + 8 + math.sin(ph) * 3), P(hx - 28, hy + 26), P(hx - 6, hy + 6)], fill=BONE, outline=DOGO)                # floppy ear
    d.ellipse([P(hx - 26, hy - 26)[0], P(hx - 26, hy - 26)[1], P(hx + 26, hy + 22)[0], P(hx + 26, hy + 22)[1]], fill=BONE, outline=DOGO, width=3)
    d.rounded_rectangle([P(hx + 10, hy - 6)[0], P(hx + 10, hy - 6)[1], P(hx + 56, hy + 14)[0], P(hx + 56, hy + 14)[1]], int(8 * s), fill=BONE, outline=DOGO, width=3)
    jo = 6 + 4 * math.sin(t * 12) * tongue
    d.polygon([P(hx + 12, hy + 14), P(hx + 54, hy + 14), P(hx + 46, hy + 26 + jo), P(hx + 18, hy + 24 + jo)], fill=BONE, outline=DOGO)
    for k in range(4): d.polygon([P(hx + 16 + k * 10, hy + 14), P(hx + 22 + k * 10, hy + 14), P(hx + 19 + k * 10, hy + 22)], fill=(255, 255, 255), outline=DOGO)
    d.rounded_rectangle([P(hx + 22, hy + 22)[0], P(hx + 22, hy + 22)[1], P(hx + 42, hy + 24 + jo + 16 * tongue)[0], P(hx + 22, hy + 24 + jo)[1] + 16 * tongue * s], int(7 * s), fill=(240, 120, 142), outline=(180, 70, 100))   # tongue
    d.ellipse([P(hx + 50, hy - 8)[0], P(hx + 50, hy - 8)[1], P(hx + 62, hy + 4)[0], P(hx + 62, hy + 4)[1]], fill=(24, 18, 24))                          # nose
    d.ellipse([P(hx - 2, hy - 18)[0], P(hx - 2, hy - 18)[1], P(hx + 22, hy + 4)[0], P(hx + 22, hy + 4)[1]], fill=(22, 16, 28)); d.ellipse([P(hx + 8, hy - 12)[0], P(hx + 8, hy - 12)[1], P(hx + 15, hy - 5)[0], P(hx + 15, hy - 5)[1]], fill=(255, 255, 255))
    if flip: lay = lay.transpose(Image.FLIP_LEFT_RIGHT)
    if tilt: lay = lay.rotate(tilt if not flip else -tilt, center=(cx, gy), resample=Image.BICUBIC)
    if alpha < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * alpha)))
    img.paste(lay, (int(x - (w - cx if flip else cx)), int(yb - gy)), lay)

def cross(img, x, y, s, kind="jesus", a=1.0, figure=True, bow=0.0):
    """a stylised cross with a modest, non-graphic figure on it (jesus) or a darker silhouette (thief)."""
    if a <= 0: return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); wood = (112, 80, 52, 255); wd_ = (80, 56, 36, 255); vb = 0.055 * s
    d.rectangle([x - vb / 2, y, x + vb / 2, y + s], fill=wood); d.rectangle([x - 0.31 * s, y + 0.2 * s, x + 0.31 * s, y + 0.2 * s + vb], fill=wood)
    d.line([(x + vb / 2 - 2, y), (x + vb / 2 - 2, y + s)], fill=wd_, width=3)
    if figure:
        j = kind == "jesus"; skin = (226, 184, 142, 255) if j else (96, 78, 66, 255); cloth = (246, 242, 232, 255) if j else (110, 92, 78, 255)
        hy = y + 0.125 * s; hx = x + (0.0 if j else 0.02 * s * bow)
        d.line([(x - 0.045 * s, y + 0.225 * s), (x - 0.29 * s, y + 0.2 * s + vb / 2)], fill=skin, width=int(0.036 * s)); d.line([(x + 0.045 * s, y + 0.225 * s), (x + 0.29 * s, y + 0.2 * s + vb / 2)], fill=skin, width=int(0.036 * s))
        d.polygon([(x - 0.05 * s, y + 0.19 * s), (x + 0.05 * s, y + 0.19 * s), (x + 0.05 * s, y + 0.5 * s), (x - 0.05 * s, y + 0.5 * s)], fill=cloth if j else skin)
        d.line([(x - 0.02 * s, y + 0.5 * s), (x - 0.025 * s, y + 0.82 * s)], fill=skin, width=int(0.036 * s)); d.line([(x + 0.02 * s, y + 0.5 * s), (x + 0.025 * s, y + 0.82 * s)], fill=skin, width=int(0.036 * s))
        d.polygon([(x - 0.06 * s, y + 0.44 * s), (x + 0.06 * s, y + 0.44 * s), (x + 0.07 * s, y + 0.62 * s), (x - 0.07 * s, y + 0.62 * s)], fill=cloth)
        d.ellipse([hx - 0.045 * s, hy - 0.05 * s, hx + 0.045 * s, hy + 0.05 * s], fill=skin)
        if j:
            d.ellipse([hx - 0.05 * s, hy - 0.058 * s, hx + 0.05 * s, hy - 0.012 * s], fill=(100, 68, 46, 255)); d.polygon([(hx - 0.035 * s, hy + 0.01 * s), (hx + 0.035 * s, hy + 0.01 * s), (hx, hy + 0.075 * s)], fill=(100, 68, 46, 255))
            d.ellipse([hx - 0.075 * s, hy - 0.085 * s, hx + 0.075 * s, hy - 0.03 * s], outline=(255, 226, 140, 255), width=max(2, int(0.01 * s)))
        else: d.ellipse([hx - 0.05 * s, hy - 0.056 * s, hx + 0.05 * s, hy - 0.012 * s], fill=(50, 40, 34, 255))
    if a < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * a)))
    img.paste(lay, (0, 0), lay)

# ---- settings
_BG6 = {}
def golgotha():
    if "g" in _BG6: return _BG6["g"].copy()
    img = gradient((52, 38, 84), (232, 128, 92), "golg"); d = ImageDraw.Draw(img); rng = random.Random(4)
    for i in range(7):
        cx = rng.uniform(0, W); cy = rng.uniform(40, 230); w = rng.uniform(260, 520)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay); ld.ellipse([cx - w / 2, cy - 26, cx + w / 2, cy + 26], fill=(40, 26, 60, 150)); img.paste(lay, (0, 0), lay)
    d = ImageDraw.Draw(img); d.ellipse([940, 250, 1010, 320], fill=(255, 214, 160))
    d.polygon([(0, 440), (180, 400), (420, 430), (700, 380), (1000, 420), (1280, 390), (1280, 720), (0, 720)], fill=(52, 38, 56))
    d.polygon([(260, 470), (520, 372), (800, 360), (1040, 420), (1280, 470), (1280, 720), (260, 720)], fill=(78, 56, 62))
    d.polygon([(0, 560), (420, 540), (900, 556), (1280, 540), (1280, 720), (0, 720)], fill=(104, 78, 70))
    d.polygon([(0, 700), (600, 640), (1280, 650), (1280, 720), (0, 720)], fill=(150, 112, 90))
    for i in range(20):
        rx, ry = rng.uniform(0, W), rng.uniform(580, 700)
        d.ellipse([rx - 18, ry - 8, rx + 18, ry + 8], fill=(86, 66, 64))
    _BG6["g"] = img; return img.copy()

def office():
    if "o" in _BG6: return _BG6["o"].copy()
    img = gradient((18, 26, 40), (36, 52, 66), "office"); d = ImageDraw.Draw(img)
    for i in range(6):                                                     # a wall of hourglasses
        for j in range(3):
            x = 100 + i * 190; y = 90 + j * 110
            d.rectangle([x - 10, y - 38, x + 38, y - 30], fill=(130, 100, 60)); d.rectangle([x - 10, y + 36, x + 38, y + 44], fill=(130, 100, 60))
            d.polygon([(x - 2, y - 30), (x + 30, y - 30), (x + 16, y + 4), (x + 30, y + 36), (x - 2, y + 36), (x + 14, y + 4)], fill=(190, 210, 230, ), outline=(120, 150, 180)); d.polygon([(x + 4, y - 18), (x + 24, y - 18), (x + 14, y - 2)], fill=(230, 190, 110)); d.polygon([(x + 2, y + 34), (x + 28, y + 34), (x + 14, y + 18)], fill=(230, 190, 110))
    d.rectangle([0, 560, W, H], fill=(46, 36, 34)); d.rectangle([0, 556, W, 566], fill=(70, 54, 48))
    d.rectangle([180, 520, 780, 570], fill=(88, 62, 44)); d.rectangle([180, 510, 780, 524], fill=(116, 84, 58)); d.rectangle([200, 570, 224, 650], fill=(70, 50, 36)); d.rectangle([736, 570, 760, 650], fill=(70, 50, 36))
    d.ellipse([300, 470, 360, 514], fill=(230, 200, 110)); d.rectangle([326, 430, 334, 470], fill=(90, 80, 70))
    _BG6["o"] = img; return img.copy()

def heaven():
    if "h" in _BG6: return _BG6["h"].copy()
    img = gradient((255, 250, 224), (176, 212, 255), "heav"); d = ImageDraw.Draw(img); rng = random.Random(8)
    for i in range(14):
        cx = rng.uniform(0, W); cy = rng.uniform(80, 420); w = rng.uniform(160, 340)
        for k in range(4): d.ellipse([cx - w / 2 + k * w * 0.18, cy - 30 - (k % 2) * 16, cx - w / 2 + k * w * 0.18 + w * 0.45, cy + 24], fill=(255, 255, 255))
    for i in range(16):                                                         # the cloud floor
        cx = i * 90 - 20; d.ellipse([cx - 90, 560 + (i % 3) * 18, cx + 120, 660 + (i % 3) * 18], fill=(250, 250, 255)); d.ellipse([cx - 40, 540 + (i % 2) * 20, cx + 90, 620], fill=(255, 255, 255))
    d.rectangle([0, 640, W, H], fill=(236, 240, 252))
    for x in (1010, 1220):                                                      # golden gate
        d.rectangle([x, 230, x + 34, 600], fill=(236, 200, 110), outline=(176, 140, 60), width=3); d.ellipse([x - 10, 210, x + 44, 250], fill=(250, 226, 150), outline=(176, 140, 60), width=3)
    d.pieslice([1010, 130, 1254, 330], 180, 360, fill=(240, 206, 120), outline=(176, 140, 60), width=3)
    for k in range(8): d.line([(1048 + k * 20, 330), (1048 + k * 20, 598)], fill=(220, 186, 100), width=4)
    _BG6["h"] = img; return img.copy()

def beam(img, x, ytop, ybot, a, t):
    if a <= 0.01: return
    lay = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(lay); wv = 90 + 12 * math.sin(t * 5)
    d.polygon([(x - wv * 0.35, 0), (x + wv * 0.35, 0), (x + wv, ybot), (x - wv, ybot)], fill=(int(190 * a), int(170 * a), int(110 * a)))
    softglow(img, lay, 44, 0.8); img.paste(ImageChops.add(img, lay.point(lambda v: int(v * 0.25))))
    rays(img, x, ytop, t, (255, 236, 170), n=16, length=900, strength=0.16 * a)

def flare(img, x, y, a):
    if a <= 0.01: return
    lay = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(lay); r = 70 + 90 * a
    d.ellipse([x - r, y - r, x + r, y + r], fill=(int(170 * a), int(150 * a), int(110 * a))); softglow(img, lay, 60, 1.0)

def smoke(img, x, y, u, col=(70, 66, 84)):
    if u <= 0 or u >= 1: return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); r = random.Random(3)
    for i in range(18):
        a = r.random() * 6.28; dist = (20 + u * 130) * r.uniform(0.4, 1); rr = (24 + 60 * u) * r.uniform(0.7, 1.2)
        px, py = x + math.cos(a) * dist, y - 80 + math.sin(a) * dist * 0.7 - u * 40
        d.ellipse([px - rr, py - rr, px + rr, py + rr], fill=col + (int(220 * (1 - u)),))
    img.paste(lay, (0, 0), lay)

def music_notes(img, t, x, y, a=1.0):
    d = ImageDraw.Draw(img); f = F(34)
    for i in range(4):
        u = (t * 0.55 + i / 4) % 1; c = int(255 * math.sin(u * math.pi) * a)
        d.text((x + math.sin(i * 2.3 + t * 2) * 30 + u * 60, y - u * 120), "♪" if i % 2 else "♫", font=f, fill=(c, int(c * 0.9), int(c * 0.6)))

def soul(img, x, y, u, t, s=1.0, a=1.0, ph=0.0):
    """a floating soul. u=0: a red devil soul with horns and a mean grin; u=1: a divine, haloed soul with a gentle smile."""
    if a <= 0.01: return
    y = y + math.sin(t * 2.2 + ph) * 9; r = 34 * s
    c = mix((206, 36, 34), (255, 236, 172), u); c2 = mix((255, 124, 40), (255, 255, 232), u)
    gl = Image.new("RGB", (W, H), (0, 0, 0)); ImageDraw.Draw(gl).ellipse([x - r * 2.2, y - r * 2.0, x + r * 2.2, y + r * 2.4], fill=tuple(int(v * 0.55 * a) for v in c)); softglow(img, gl, 30, 1.2)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    sw = math.sin(t * 5 + ph) * r * 0.35
    d.polygon([(x - r * 0.75, y + r * 0.5), (x + r * 0.75, y + r * 0.5), (x + sw * 0.6, y + r * 1.6), (x + sw, y + r * 2.5)], fill=c + (220,))          # wispy tail
    d.ellipse([x - r, y - r, x + r, y + r * 1.1], fill=c + (255,), outline=tuple(int(v * 0.6) for v in c) + (255,), width=3)
    d.ellipse([x - r * 0.6, y - r * 0.75, x + r * 0.35, y + r * 0.1], fill=c2 + (120,))
    hh = clamp(1 - u / 0.8)
    if hh > 0.02:                                                                                                                                      # horns that melt away
        for sg in (-1, 1):
            d.polygon([(x + sg * r * 0.32, y - r * 0.82), (x + sg * r * (0.62 + 0.12 * hh), y - r * (0.82 + 0.95 * hh)), (x + sg * r * 0.8, y - r * 0.6)], fill=(122, 14, 18, int(255 * hh)), outline=(70, 8, 10, int(255 * hh)))
    ey = y - r * 0.12
    if u < 0.5:                                                                                                                                        # glaring devil eyes + jagged grin
        for sg in (-1, 1):
            d.ellipse([x + sg * r * 0.38 - r * 0.2, ey - r * 0.14, x + sg * r * 0.38 + r * 0.2, ey + r * 0.2], fill=(255, 236, 80, 255)); d.ellipse([x + sg * r * 0.38 - 3, ey - 2, x + sg * r * 0.38 + 3, ey + 6], fill=(20, 10, 10, 255))
            d.line([(x + sg * r * 0.7, ey - r * 0.34), (x + sg * r * 0.12, ey - r * 0.12)], fill=(60, 8, 10, 255), width=4)
        pts = [(x - r * 0.5, y + r * 0.34)] + [(x - r * 0.5 + k * r * 0.2, y + r * (0.55 if k % 2 else 0.3)) for k in range(1, 6)] + [(x + r * 0.5, y + r * 0.34)]
        d.polygon(pts + [(x + r * 0.4, y + r * 0.7), (x - r * 0.4, y + r * 0.7)], fill=(30, 6, 8, 255)); d.line(pts, fill=(255, 255, 255, 255), width=2)
    else:                                                                                                                                              # serene, happy
        for sg in (-1, 1): d.arc([x + sg * r * 0.38 - r * 0.2, ey - r * 0.12, x + sg * r * 0.38 + r * 0.2, ey + r * 0.22], 200, 340, fill=(120, 90, 40, 255), width=4)
        d.arc([x - r * 0.35, y + r * 0.1, x + r * 0.35, y + r * 0.55], 20, 160, fill=(150, 100, 60, 255), width=3)
    if u > 0.25: d.ellipse([x - r * 0.75, y - r * (1.65), x + r * 0.75, y - r * 1.25], outline=(255, 226, 120, int(255 * clamp((u - 0.25) / 0.5))), width=4)         # halo
    if a < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * a)))
    img.paste(lay, (0, 0), lay)

def soul_burst(img, x, y, u, t):
    """sparkles when a soul transforms."""
    if u <= 0 or u >= 1: return
    lay = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(lay); r = random.Random(int(x))
    for k in range(18):
        a_ = k / 18 * 6.28 + 0.3; dist = 30 + 150 * u; c = int(255 * (1 - u))
        d.ellipse([x + math.cos(a_) * dist - 5, y + math.sin(a_) * dist - 5, x + math.cos(a_) * dist + 5, y + math.sin(a_) * dist + 5], fill=(c, int(c * 0.9), int(c * 0.55)))
    softglow(img, lay, 10, 1.5); img.paste(ImageChops.add(img, lay))

def jfig(img, x, yb, h=300, rot=0.0, mouth="smile", eyes="open", alpha=1.0, L=None, R=None):
    return cfig(img, x, yb, h, (246, 242, 232), SKIN[0], hair=(100, 68, 46), beard=True, sash=(206, 188, 150), mantle=None, tunic=True, mouth=mouth, eyes=eyes, rot=rot, alpha=alpha, L=L, R=R)

def jlie(img, cx, cy, h=270, su=0.0, eyes="closed", mouth="smile", alpha=1.0):
    """Jesus lying across a surface (su=0) rising to standing (su=1). cx, cy: where his torso centre is when lying."""
    rot = 82 * (1 - su); px = cx + 0.44 * h * (1 - su); py = lerp(cy, GY + 4, su)
    return jfig(img, px, py, h, rot=rot, eyes=eyes, mouth=mouth, alpha=alpha)

# ---- scenes
CX = {"L": 430, "C": 780, "R": 1110}                      # cross positions: thief, Jesus, thief
def bubble6(img, x, y, text, size=24, a=1.0, tail=None, col=(252, 250, 244)): bubble(img, x, y + OFF - 20, text, size, a, tail=(tail[0], tail[1] + OFF - 20) if tail else None, col=col)

def s_title(t, d, p):
    img = golgotha(); img = Image.blend(img, Image.new("RGB", (W, H), (10, 6, 18)), 0.4)
    for k, kx in enumerate((CX["L"], CX["C"], CX["R"])): cross(img, kx, 330 - (0 if k == 1 else -20), 330 if k == 1 else 270, "jesus" if k == 1 else "thief", figure=False)
    a = tseg(t, 0.4, 1.3) * (1 - tseg(t, d - 0.8, d - 0.1))
    title(img, "DEATH TAKES A SERVICE CALL", "a very short tale of a very long day for Death", a, y=235, size=50)
    return img

def s_ticket(t, d, p):
    n1, tk = ev("ticket", "n1"), ev("ticket", "tk"); img = office()
    lamp = 0.5 + 0.1 * math.sin(t * 3); lay = Image.new("RGB", (W, H), (0, 0, 0)); ImageDraw.Draw(lay).ellipse([240, 380, 420, 540], fill=(int(120 * lamp), int(90 * lamp), 40)); softglow(img, lay, 60, 1.2)
    go = tseg(t, tk[1] - 1.6, tk[1] - 0.8); gone = tseg(t, tk[1] - 0.8, tk[1] - 0.2)
    reading = tseg(t, tk[0] - 0.4, tk[0] + 0.4)
    L_ = (-0.1, -0.74 + 0.12 * (1 - reading)) if go < 0.1 else None
    pos = death(img, 520 + 180 * go, GY - 6, 330, t, L=(-0.28, -0.52), R=(0.30 - 0.1 * (1 - go), -0.5), scythe=go > 0.05, sa=-6 + 10 * go, eyes="norm", look=(math.sin(t * 2) * 0.6 * (1 - reading), -0.6 * reading), alpha=1 - gone)
    smoke(img, 700, GY - 60, gone)
    # the service ticket (screen space)
    def _ticket(im):
        a = tseg(t, tk[0] - 0.3, tk[0] + 0.5) * (1 - tseg(t, tk[1] - 2.2, tk[1] - 1.6))
        if a <= 0: return
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay); x0, y0 = 760, 90
        ld.rounded_rectangle([x0, y0, x0 + 440, y0 + 330], 16, fill=(250, 242, 214, int(250 * a)), outline=(120, 90, 50, int(255 * a)), width=4)
        for k in range(16): ld.ellipse([x0 - 8 + k * 29, y0 - 6, x0 + 6 + k * 29, y0 + 8], fill=(18, 26, 40, int(255 * a)))
        im.paste(lay, (0, 0), lay)
        T = "Oh, I got a service ticket for the next one. Let's see... thirty-something-year-old dude, named Jesus. Former carpenter. Should be located between two thieves. Alright, I'll go pick him up and bring him to the afterlife. Let's go."
        rows = [("SERVICE TICKET #0033", "Let's see", 24, (90, 50, 30)), ("PICK UP:  JESUS", "dude, named Jesus", 28, (30, 24, 20)), ("AGE:  30-something", "thirty-something", 22, (60, 48, 40)),
                ("OCCUPATION:  former carpenter", "Former carpenter", 22, (60, 48, 40)), ("LOCATION:  between two thieves", "between two thieves", 22, (150, 40, 36)), ("DESTINATION:  the afterlife", "afterlife", 22, (60, 48, 40))]
        for i, (txt, key, sz, col) in enumerate(rows):
            tt = tk[0] + T.index(key) / len(T) * (tk[1] - tk[0]); b = tseg(t, tt - 0.1, tt + 0.5) * a
            if b > 0: label(im, x0 + 26, y0 + 28 + i * 44, txt, sz, col, b, anchor="l")
        s_ = tseg(t, tk[1] - 2.6, tk[1] - 2.2) * a
        if s_ > 0: label(im, x0 + 320, y0 + 270, "URGENT", 34, (200, 40, 40), s_ * 0.9, anchor="c")
    HUD(_ticket)
    return img

def s_walk(t, d, p):
    w1, wh, dg, kk, kd = ev("walk", "w1"), ev("walk", "whistle"), ev("walk", "dogw"), ev("walk", "kick"), ev("walk", "kicked")
    img = golgotha()
    for k, kx in enumerate((830, 900, 970)): cross(img, kx, 380, 150 if k == 1 else 120, "jesus" if k == 1 else "thief", figure=False)
    u = tseg(t, 0.2, kd[1] + 0.8); x = lerp(170, 820, u); walk = t * 4.2
    stroll = 1.0 if t < kd[1] + 0.8 else 0.0
    lookx = math.sin(t * 1.6) * 0.9                                           # looking side to side, bored
    watch_u = tseg(t, w1[1] - 2.8, w1[1] - 2.0) * (1 - tseg(t, w1[1] + 0.2, w1[1] + 0.9))
    Lh = (-0.18 + 0.1 * watch_u, -0.42 - 0.3 * watch_u)
    kicking = tseg(t, kk[0] + 2.5, kk[0] + 3.0) * (1 - tseg(t, kk[0] + 3.0, kk[0] + 3.6))
    stone_x = x + 130 + 380 * tseg(t, kk[0] + 2.8, kd[1]) if t > kk[0] + 2.8 else x + 120
    stone_y = GY + 4 - 90 * math.sin(tseg(t, kk[0] + 2.8, kd[1]) * math.pi) if t > kk[0] + 2.8 else GY + 4
    looking_down = tseg(t, kk[0], kk[0] + 1.0) 
    pos = death(img, x, GY, 320, t, L=Lh, watch=watch_u > 0.1 or True, walk=walk * stroll, eyes="norm", look=(lookx * (1 - watch_u) * (1 - looking_down), 0.9 * looking_down - 0.8 * watch_u), lean=-4 * looking_down,
                scythe=True, sa=-10 + math.sin(walk * 2) * 3, foot=(0.17 * math.sin(walk * 2) + 0.12 * kicking, -0.05 * kicking) if kicking > 0 else None)
    d = ImageDraw.Draw(img)
    if t < kd[1] + 1.5:
        sx = stone_x if t > kk[0] + 2.8 else x + 130; d.ellipse([sx - 13, stone_y - 10, sx + 13, stone_y + 6], fill=(110, 96, 90), outline=(70, 60, 58), width=2)
    if wh[0] - 3.0 < t < wh[1] + 1.0 or t < w1[1] - 3: music_notes(img, t, x + 60, GY - 330, tseg(t, 0.6, 1.4))
    if dg[0] <= t <= dg[1] + 0.4: bubble6(img, x + 40, GY - 440, "...time to walk the skull dog after this.", 24, 1.0, tail=(x + 10, GY - 360))
    return img

def s_cross(t, d, p):
    c1, bt, c2, wtf, th, why, see, dl, br = [ev("cross", k) for k in ("c1", "beat", "c2", "wtf", "thanks", "why", "see", "delay", "bring")]
    img = golgotha()
    stretch = tseg(t, c1[0] + 1.2, c1[0] + 2.4) * (1 - tseg(t, c1[0] + 3.8, c1[0] + 4.4)); cough = tseg(t, c1[0] + 4.6, c1[0] + 5.0) * (1 - tseg(t, c1[0] + 5.6, c1[0] + 6.0))
    look_up = tseg(t, c1[0] + 6.2, c1[1] - 0.2)
    drop = tseg(t, c2[0], c2[0] + 0.45); jb = drop + (0.08 * math.sin((t - c2[0]) * 14) * math.exp(-(t - c2[0]) * 3) if t > c2[0] else 0)
    light = tseg(t, c2[0], c2[0] + 0.6) * (1 - 0.5 * tseg(t, br[0], br[0] + 1.5)) * (1 - 0.0)
    for k, kx in enumerate((CX["L"], CX["C"], CX["R"])):
        cross(img, kx, 130 if k == 1 else 230, 480 if k == 1 else 380, "jesus" if k == 1 else "thief", figure=True)
    beam(img, CX["C"], 150, 600, light, t)
    L_ = (-0.5 * stretch - 0.24 * (1 - stretch), -0.62 * stretch - 0.42 * (1 - stretch)); R_ = (0.5 * stretch + 0.27 * (1 - stretch), -0.62 * stretch - 0.46 * (1 - stretch))
    shield = tseg(t, why[1] - 3.2, why[1] - 2.4) * (1 - tseg(t, br[0] + 0.5, br[0] + 1.5)) if light > 0.2 else 0.0
    if cough > 0: R_ = (0.0 + 0.07 * (1 - cough), -0.78 + 0.0); 
    if shield > 0: L_ = (-0.1, -0.86); 
    gulp = tseg(t, dl[0] - 0.1, dl[0] + 0.3) * (1 - tseg(t, dl[0] + 0.3, dl[0] + 0.9))
    eyes = "shut" if (stretch > 0.2 and look_up < 0.1) else ("squint" if shield > 0.4 else ("wide" if drop > 0.1 else "norm"))
    pos = death(img, 560, GY - 6, 330, t, L=L_, R=R_ if (stretch > 0.01 or cough > 0.01) else (0.27, -0.46), scythe=cough < 0.05 and stretch < 0.05, jaw=jb, eyes=eyes, look=(0.4, -0.9 * look_up), whiten=0.5 * light, sweat=1.0 if gulp > 0.05 or t > dl[0] else 0.0, bend=0.4 * gulp, lean=-5 * shield)
    flare(img, 560, 330, 0.6 * light * (0.5 + 0.5 * math.sin(t * 6)) if light > 0 else 0)
    if cough > 0.3: bubble6(img, 600, 280, "*ahem*", 28, 1.0, tail=(570, 330))
    if drop > 0.05 and t < wtf[0] + 1.0: bubble6(img, 640, 250, "!!!", 40, tseg(t, c2[0], c2[0] + 0.2), tail=(580, 320))
    if why[0] <= t <= why[0] + 3.0: pass
    return img

def s_carry(t, d, p):
    c3, hk, th, hl, pa, dv = [ev("carry", k) for k in ("c3", "heck", "thieves", "hell", "para", "devil")]
    img = golgotha()
    lift = tseg(t, c3[0] + 1.0, c3[0] + 3.2)
    gone1 = tseg(t, th[0] + 2.4, th[0] + 3.1); gone2 = tseg(t, th[0] + 3.4, th[0] + 4.1)
    cross(img, CX["L"], 230, 380, "thief", a=1 - gone1, figure=True); cross(img, CX["R"], 230, 380, "thief", a=1 - gone2, figure=True)
    cross(img, CX["C"], 130, 480, "jesus", figure=(lift < 0.05))
    for kx, g in ((CX["L"], gone1), (CX["R"], gone2)):
        if 0 < g < 1: smoke(img, kx, 600, g, (200, 50, 30))
    dx = 560 - 130 * tseg(t, th[0] - 0.4, th[0] + 1.6) + 40 * tseg(t, th[0] + 2.6, th[0] + 4.0)
    # the thieves' souls pop out as red devil souls and drift to hover behind Death
    for k, (g0, gx, tx, ty) in enumerate(((th[0] + 2.7, CX["L"], dx - 170, 300), (th[0] + 3.7, CX["R"], dx + 190, 272))):
        e = tseg(t, g0, g0 + 1.5)
        if t >= g0: soul(img, lerp(gx, tx, e), lerp(320, ty, e), 0.0, t, 1.0, a=min(1.0, (t - g0) / 0.3), ph=k * 2)
    bend = 0.9 * lift; fp = tseg(t, dv[0] + 0.3, dv[0] + 0.9)
    souls_in = t > th[0] + 3.7
    pos = death(img, dx, GY - 6, 330, t, L=(-0.24, -0.5), R=(0.26, -0.5) if fp < 0.1 else (0.0, -0.8), scythe=fp < 0.1, bend=bend, eyes="wide" if hk[0] < t < hk[1] + 1 else "norm", sweat=1.0 if lift > 0.5 else 0.0,
                look=((1.0 if math.sin(t * 2.2) > 0 else -1.0) if souls_in else 0.5, 0.2), brow=0.8 if souls_in else 0.0)
    if lift > 0:
        sh = pos["shoulder"]; e = ease(lift)
        cx_ = lerp(CX["C"], dx + 119, e); cy_ = lerp(524, sh[1] + 66, e); rot = lerp(0, 82, e)
        jfig(img, cx_, cy_, 270, rot=rot, eyes="closed", mouth="smile")
        crack = tseg(t, c3[0] + 3.0, c3[0] + 3.5); d_ = ImageDraw.Draw(img)
        if crack > 0: d_.line([(dx - 90, GY + 8), (dx - 30, GY + 28), (dx + 20, GY + 14), (dx + 90, GY + 34)], fill=(40, 28, 26), width=4)
        if lift > 0.8: label(img, dx - 120, GY - 400, "\u00d7100", 52, (255, 220, 160), tseg(t, c3[0] + 3.0, c3[0] + 3.6) * (1 - tseg(t, hk[1], hk[1] + 0.6)))
    return img

def s_whisper(t, d, p):
    nw, wl, ch, rl = ev("whisper", "nwh"), ev("whisper", "will"), ev("whisper", "change"), ev("whisper", "rules")
    img = golgotha(); img = Image.blend(img, Image.new("RGB", (W, H), (255, 240, 200)), 0.08 * tseg(t, wl[0], wl[1]))
    beam(img, 780, 150, 600, 0.35 + 0.3 * tseg(t, wl[0], wl[1] + 1.0), t)
    u_soul = tseg(t, wl[1] + 0.2, wl[1] + 2.8)                                           # red -> divine
    vanish = tseg(t, rl[1] + 0.5, rl[1] + 1.4); alpha = 1 - vanish
    CXD = 640; sy = (GY - 6)
    souls = ((CXD - 200, 300, 0.0), (CXD + 215, 270, 2.0))
    for sx_, sy_, ph_ in souls:
        soul(img, sx_, sy_, u_soul, t, 1.1, alpha, ph_); soul_burst(img, sx_, sy_ + math.sin(t * 2.2 + ph_) * 9, tseg(t, wl[1] + 1.0, wl[1] + 2.4), t)
    # Death looks from soul to soul, getting more and more exasperated and confused
    glance = 1.0 if math.sin(t * 2.4) > 0 else -1.0
    after = t > wl[1]
    pos = death(img, CXD, GY - 6, 340, t, L=(-0.22, -0.46), R=(0.27, -0.6) if t < rl[0] else (0.27, -0.46), scythe=False, bend=0.7, alpha=alpha,
                eyes=("wide" if (after and u_soul > 0.3 and u_soul < 0.9) else ("roll" if t > rl[0] + 1.0 and t < rl[0] + 3.0 else "norm")),
                look=(glance if t > nw[1] else 0.8, 0.0), sweat=1.0 if after else 0.0, brow=1.0 if after else 0.0)
    sh = pos["shoulder"]
    jfig(img, 640 + 119, sh[1] + 66, 270, rot=82, eyes="closed" if t < wl[0] - 0.4 else "open", mouth="smile", alpha=alpha)
    hx, hy = pos["head"]
    if wl[0] <= t <= wl[1] + 0.6:
        bubble6(img, hx + 120, hy - 150, "Thy will has been done.", 22, 1.0, tail=(hx - 10, hy - 40), col=(255, 250, 230))
        ImageDraw.Draw(img).ellipse([hx + 60 - 24, hy - 220 - 6, hx + 60 + 24, hy - 214 + 2], outline=(255, 226, 140), width=3)
    if t > wl[1] + 3.0 and vanish < 0.1:
        for k, kx in enumerate((-60, 40)): label(img, hx + kx, hy - 120 - (k % 2) * 30 + math.sin(t * 4 + k) * 4, "?", 56, (255, 240, 200), tseg(t, wl[1] + 3.0 + k * 0.5, wl[1] + 3.5 + k * 0.5))
    if vanish > 0: smoke(img, 640, GY - 60, tseg(t, rl[1] + 0.4, rl[1] + 1.8))
    return img

def s_arrive(t, d, p):
    pop, th, ar, st, aw, t2, wk, gd = [ev("arrive", k) for k in ("pop", "thud", "arise", "stand", "awk", "thanks2", "walkask", "getdog")]
    img = heaven(); land = th[1] - 0.45                                                   # Jesus hits the ground at the end of "...very loud thud"
    appear = tseg(t, pop[0] + 0.5, pop[0] + 1.5); smoke_u = tseg(t, pop[0] + 0.2, pop[0] + 3.0)
    beam(img, 640, 100, 600, 0.9 * tseg(t, ar[0] - 0.4, ar[0] + 0.6) * (1 - tseg(t, ar[1] + 1.5, ar[1] + 3.0)) + 0.25, t)
    drop = tseg(t, land - 0.55, land); on_ground = t >= land
    leave = tseg(t, gd[0] + 0.3, gd[1] + 0.6)                                              # Death goes to fetch the dog, Jesus waits where the dog will arrive
    dxd = 640 if t < land - 0.3 else lerp(640, 470, ease(tseg(t, land - 0.3, land + 1.4)))
    dxd = lerp(dxd, 330, ease(leave))
    jx = lerp(640, 820, ease(tseg(t, gd[0] + 0.5, gd[1] + 0.8)))
    stand_u = ease(tseg(t, st[0] + 0.2, st[0] + 2.0)) if on_ground else 0.0
    # divine souls follow Death in, hover, then float up into the light
    up = tseg(t, ar[0] + 1.0, ar[0] + 3.8)
    for k, (ox, oy, ph_) in enumerate(((-170, 330, 0.0), (190, 300, 2.0))):
        if appear > 0: soul(img, dxd + ox + (60 * up if k else -60 * up), oy - 260 * up, 1.0, t, 1.1, appear * (1 - up), ph_)
    carrying = t < land - 0.3
    moving = on_ground and (t < land + 1.4 or leave > 0.01) and not carrying
    awkward = on_ground and t > st[0] + 1.5 and leave < 0.01
    look = (math.sin(t * 2.2) * 1.0, 0.5 * math.sin(t * 1.5)) if awkward else (0.6, 0.0)
    pos = death(img, dxd, GY - 6, 330, t, L=(-0.24, -0.5) if carrying else ((-0.24, -0.42) if not awkward else (-0.2 + 0.1 * math.sin(t * 1.6), -0.38)), R=(0.26, -0.5) if carrying else (0.27, -0.46),
                bend=(0.8 if carrying else max(0.0, 0.5 * (1 - tseg(t, land, land + 0.8)))), eyes="norm", look=look, walk=(t * 4 if moving else 0.0), sweat=1.0 if (awkward or carrying) else 0.0, alpha=appear,
                lean=(3 * math.sin(t * 1.3) if awkward else 0.0), scythe=True, sa=-6 + (4 * math.sin(t * 1.9) if awkward else 0), watch=awkward and math.sin(t * 0.8) > 0.8)
    if appear > 0.05:
        sh = pos["shoulder"]
        if t < land - 0.6: jlie(img, dxd, sh[1] + 66, 270, 0.0, "closed", alpha=appear)
        elif not on_ground:
            cy_ = lerp(sh[1] + 66, GY - 34, ease(drop)); jlie(img, dxd if t < land - 0.3 else lerp(dxd, 640, 1), cy_, 270, 0.0, "closed")
        else: jlie(img, jx, GY - 34, 270, stand_u, "open" if t > st[0] else "closed")
    if smoke_u < 1: smoke(img, 640, GY - 40, smoke_u)
    sh_ = max(0, 1 - (t - land) * 5) * 16 if on_ground else 0
    if on_ground and t < land + 1.2:                      # the loud thud: a ring of cloud dust
        u = (t - land) / 1.2; lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        for k in range(10): a_ = k / 10 * 6.28; ld.ellipse([640 + math.cos(a_) * 360 * u - 36, GY + 10 + math.sin(a_) * 40 * u - 24, 640 + math.cos(a_) * 360 * u + 36, GY + 10 + math.sin(a_) * 40 * u + 24], fill=(255, 255, 255, int(230 * (1 - u)))); img.paste(lay, (0, 0), lay)
    if st[0] + 1.6 < t < st[1] + 0.4:                     # dust brushed off his feet
        for k in range(8): u = ((t - st[0]) * 1.4 + k / 8) % 1; ImageDraw.Draw(img).ellipse([600 + k * 12 - u * 20, GY - 10 - u * 40, 606 + k * 12 - u * 20, GY - 4 - u * 40], fill=(220, 214, 200))
    if awkward and t < aw[1] + 1.0:
        hx, hy = pos["head"]; bubble6(img, hx + 30, hy - 120, "...", 34, tseg(t, st[0] + 2.0, st[0] + 2.4) * (1 - tseg(t, aw[1] + 0.4, aw[1] + 1.0)), tail=(hx, hy - 50))
    if sh_ > 0: img = img.transform((W, H), Image.AFFINE, (1, 0, math.sin(t * 90) * sh_, 0, 1, math.cos(t * 70) * sh_))
    if on_ground and t < land + 0.2: img = Image.blend(img, Image.new("RGB", (W, H), (255, 255, 255)), 0.3 * (1 - (t - land) / 0.2))
    return img

def s_dog(t, d, p):
    rs, bk, pc, jm, cd, wd, sr = [ev("dog", k) for k in ("rush", "bark", "precious", "jump", "cuddle", "walkdone", "sure")]
    img = heaven(); beam(img, 640, 100, 600, 0.22, t)
    JXp = 820
    run_u = tseg(t, bk[0] - 0.4, bk[1] + 1.6)                                    # the dog bursts in from the left
    jump_u = tseg(t, jm[0] + 2.5, jm[0] + 3.5)
    dogx = lerp(-100, 480, run_u) if jump_u <= 0 else lerp(480, 640, jump_u)
    # Death waits with arms crossed (and eyes that roll)
    roll = jm[0] + 3.2 < t
    death(img, 330, GY - 6, 320, t, L=(-0.1, -0.5) if roll else (-0.24, -0.42), R=(0.1, -0.52) if roll else (0.27, -0.46), scythe=not roll, eyes="roll" if (jm[0] + 4.2 < t < wd[0]) else "norm", look=(0.8, 0.0))
    ph = t * 14
    jesus_pos = jfig(img, JXp, GY + 4, 300, mouth="smile", L=(-0.2, -0.5 - 0.1 * jump_u), R=(0.22, -0.5 - 0.1 * jump_u))
    if jump_u <= 0:
        if t > bk[0] - 0.4 and run_u < 1.0: skulldog(img, dogx, GY + 6, 1.3, t, flip=False, mode="run")
        elif run_u >= 1.0: skulldog(img, 480, GY + 6, 1.3, t, flip=False, mode="stand", tongue=1.0)
    elif jump_u < 1:
        arc = math.sin(jump_u * math.pi) * 150; dx = lerp(480, JXp - 70, jump_u); dy = lerp(GY + 6, GY - 160, ease(jump_u)) - arc
        skulldog(img, dx, dy, 1.3 - 0.25 * jump_u, t, flip=False, mode="stand", ph=jump_u * 6, tilt=-20 * (1 - jump_u))
    if t > jm[0] + 3.5: 
        # cuddling in Jesus's arms, licking
        skulldog(img, JXp - 40, GY - 160, 0.62, t, flip=False, mode="stand", tongue=1.0 + 0.5 * math.sin(t * 10), tilt=-15)
        lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay)
        for k in range(5):
            u = (t * 0.6 + k / 5) % 1; hx = JXp - 20 + math.sin(k * 2 + t) * 60; hy = GY - 340 - u * 120
            c = (int(255 * (1 - u)), int(120 * (1 - u)), int(150 * (1 - u))); ld.ellipse([hx - 9, hy - 8, hx, hy + 2], fill=c); ld.ellipse([hx, hy - 8, hx + 9, hy + 2], fill=c); ld.polygon([(hx - 9, hy - 2), (hx + 9, hy - 2), (hx, hy + 12)], fill=c)
        softglow(img, lay, 10, 1.6); img.paste(ImageChops.add(img, lay))
    if bk[0] < t < bk[1] + 1.2:
        for k in range(2): bubble6(img, 560 + k * 80, GY - 420 - k * 50, "WOOF!" if k == 0 else "WOOF WOOF!", 26, tseg(t, bk[0] + k * 0.45, bk[0] + k * 0.45 + 0.1) * (1 - tseg(t, bk[1] + 0.8, bk[1] + 1.2)))
    # the walk: they set off together into the light
    go = tseg(t, sr[1] - 0.5, d - 0.4)
    if go > 0: img = Image.blend(img, Image.new("RGB", (W, H), (255, 252, 236)), 0.8 * go)
    return img

SCENE_FN = {"title": s_title, "ticket": s_ticket, "walk": s_walk, "cross": s_cross, "carry": s_carry, "whisper": s_whisper, "arrive": s_arrive, "dog": s_dog}
CAMK = {"ticket": [(0, 640, 400, 1.0), ("end", 560, 400, 1.15)],
        "walk": [(0, 400, 440, 1.2), ("end", 760, 450, 1.2)],
        "cross": [(0, 640, 420, 1.0), (("c2", 0.0), 640, 420, 1.0), (("c2", 0.0), 600, 300, 1.7), (("wtf", 0.0), 600, 300, 1.7), (("thanks", 0.0), 640, 420, 1.0), ("end", 640, 420, 1.0)],
        "carry": [(0, 640, 420, 1.0), ("end", 640, 430, 1.1)],
        "whisper": [(0, 640, 400, 1.3), ("end", 660, 380, 1.55)],
        "arrive": [(0, 640, 420, 1.0), ("end", 640, 430, 1.0)],
        "dog": [(0, 560, 440, 1.0), ("end", 640, 430, 1.1)]}
CONT_IN = {"ticket", "walk", "cross", "carry", "whisper", "arrive", "dog"}
CONT_OUT = {"title", "ticket", "walk", "cross", "carry", "whisper", "arrive"}


SPK = {"n": (255, 255, 255), "d": (200, 212, 255), "f": (255, 226, 150), "j": (255, 244, 214)}
NAMES = {"d": "DEATH", "f": "THE FATHER", "j": "JESUS"}
def subtitles(img, t):
    for s in SC:
        for z in s["sents"]:
            if z["text"] and z["start"] - 0.05 <= t <= z["end"] + 0.25:
                lines = textwrap.wrap(z["text"], 62)
                lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
                lab = z.get("label") or NAMES.get(z["who"])
                f = F(26); lh = 36; bh = lh * len(lines) + 20 + (20 if lab else 0); y0 = H - bh - 18
                d.rounded_rectangle([90, y0, W - 90, y0 + bh], 12, fill=(0, 0, 0, 160))
                yy = y0 + 8
                if lab:
                    lf = F(14, bold=True); tw = d.textlength(lab, font=lf); d.text(((W - tw) / 2, yy), lab, font=lf, fill=SPK.get(z["who"], (200, 200, 220)) + (255,)); yy += 20
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

def _kt(sc, spec):
    if isinstance(spec, (int, float)): return float(spec)
    if spec == "end": return sc["end"] - sc["start"]
    tg, off = spec
    if tg.endswith("@end"): return ev(sc["id"], tg[:-4])[1] + off
    return ev(sc["id"], tg)[0] + off

def camera(img, sc, p):
    if sc["id"] not in CAMK: return img
    t_ = p * (sc["end"] - sc["start"]); ks = [(_kt(sc, a), b, c, e) for (a, b, c, e) in CAMK[sc["id"]]]
    cx, cy, z = ks[0][1:]
    for (ta, xa, ya, za), (tb, xb, yb, zb) in zip(ks, ks[1:]):
        if t_ >= tb: cx, cy, z = xb, yb, zb
        elif t_ >= ta and tb > ta: u = ease((t_ - ta) / (tb - ta)); cx, cy, z = lerp(xa, xb, u), lerp(ya, yb, u), lerp(za, zb, u); break
    w, h = W / z, H / z; xa = clamp(cx - w / 2, 0, W - w); ya = clamp(cy - h / 2, 0, H - h)
    return img.crop((int(xa), int(ya), int(xa + w), int(ya + h))).resize((W, H), Image.BILINEAR)

def frame(i):
    t = i / FPS
    sc = next((s for s in SC if s["start"] <= t < s["end"]), SC[-1])
    tt = t - sc["start"]; dur = sc["end"] - sc["start"]; p = clamp(tt / dur)
    _HUDQ.clear()
    img = SCENE_FN[sc["id"]](tt, dur, p).convert("RGB")
    img = camera(img, sc, p)
    for fn in list(_HUDQ): fn(img)
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
                           "-shortest", "-movflags", "+faststart", "death_takes_a_service_call.mp4"], stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for k, b in enumerate(pool.imap(frame, range(n), chunksize=6)):
            ff.stdin.write(b)
            if k % 240 == 0: print(k, "/", n, flush=True)
    ff.stdin.close(); ff.wait()
