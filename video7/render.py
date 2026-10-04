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
# ================================================================= A Tour of My Emotions
GY = 650
ORDER = ["title", "intro", "bored", "lonely", "fear", "anger", "trapped", "scream", "sad", "irritated", "meaning"]
KIND = {"boredom": ((150, 162, 128), (98, 110, 84)), "lonely": ((128, 154, 210), (86, 108, 162)), "fear": ((190, 144, 218), (132, 92, 160)),
        "anger": ((224, 74, 64), (152, 42, 38)), "sad": ((72, 124, 180), (46, 86, 134))}
NAMES_E = {"boredom": "BOREDOM", "lonely": "LONELINESS", "fear": "FEAR", "anger": "ANGER", "sad": "SADNESS"}
POS = {"boredom": 600, "fear": 330, "anger": 440, "lonely": 1090, "sad": 700}
REVEAL = {"boredom": "bored", "lonely": "lonely", "fear": "fear", "anger": "anger"}

def revealed(kind, sc, t):
    """0 -> silhouette, 1 -> coloured. Each emotion is introduced in its own scene."""
    k = REVEAL.get(kind)
    if k is None: return 1.0
    i, j = ORDER.index(sc), ORDER.index(k)
    if i > j: return 1.0
    if i < j: return 0.0
    return tseg(t, 0.2, 1.0)

_AB = {}
def apartment():
    if "a" in _AB: return _AB["a"].copy()
    img = gradient((74, 78, 104), (50, 54, 76), "apt"); d = ImageDraw.Draw(img); rng = random.Random(5)
    d.rectangle([0, 598, W, 616], fill=(60, 48, 46)); d.rectangle([0, 616, W, H], fill=(104, 80, 64))
    for k in range(14): d.line([(k * 100 - 40, 616), (k * 150 - 300, 720)], fill=(88, 66, 54), width=2)
    # window with a night skyline
    d.rectangle([520, 110, 770, 380], fill=(18, 26, 52)); d.rectangle([520, 110, 770, 380], outline=(120, 100, 84), width=8)
    d.line([(645, 110), (645, 380)], fill=(120, 100, 84), width=6); d.line([(520, 245), (770, 245)], fill=(120, 100, 84), width=6)
    d.ellipse([700, 140, 732, 172], fill=(236, 232, 210))
    for k in range(18):
        bx = 530 + k * 13; bh = rng.randint(30, 110); d.rectangle([bx, 380 - bh, bx + 11, 380], fill=(28, 34, 62))
        for j in range(bh // 14):
            if rng.random() < 0.5: d.rectangle([bx + 3, 380 - bh + 4 + j * 14, bx + 6, 380 - bh + 8 + j * 14], fill=(250, 220, 120))
    d.polygon([(500, 100), (540, 100), (530, 390), (500, 390)], fill=(110, 70, 84)); d.polygon([(750, 100), (790, 100), (790, 390), (760, 390)], fill=(110, 70, 84))
    # the door to the outside
    d.rectangle([40, 160, 210, 604], fill=(96, 70, 52), outline=(60, 44, 34), width=6); d.rectangle([62, 190, 188, 340], outline=(70, 52, 40), width=4); d.rectangle([62, 370, 188, 560], outline=(70, 52, 40), width=4)
    d.ellipse([176, 400, 192, 416], fill=(220, 190, 90)); d.ellipse([112, 150, 138, 176], fill=(40, 30, 28), outline=(160, 140, 100), width=3)
    # shelf, plant, poster
    d.rectangle([950, 230, 1240, 244], fill=(110, 82, 60))
    for k in range(9):
        bh = rng.randint(34, 54); d.rectangle([960 + k * 18, 230 - bh, 972 + k * 18, 230], fill=rng.choice([(120, 60, 60), (60, 90, 110), (100, 110, 70), (130, 100, 60)]))
    d.rectangle([1170, 190, 1214, 230], fill=(138, 92, 70))
    for a in range(-3, 4): d.ellipse([1192 + a * 12 - 14, 150 - abs(a) * 6, 1192 + a * 12 + 14, 196], fill=(70, 130, 84))
    d.rectangle([260, 200, 380, 300], fill=(222, 214, 190), outline=(110, 90, 70), width=4); d.text((277, 236), "DEEP\nDIVES", font=F(26, bold=True), fill=(60, 50, 60))
    d.polygon([(0, 640), (W, 630), (W, H), (0, H)], fill=(112, 86, 68)); d.ellipse([200, 650, 1100, 740], fill=(92, 62, 78))
    _AB["a"] = img; return img.copy()

def man(img, x, yb, h=300, t=0.0, mood="tired", alpha=1.0, glow=0.5, look=0.0, lean=0.0):
    w = int(h * 1.5); hh = int(h * 1.1); lay = Image.new("RGBA", (w, hh), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); cx = w / 2; gy = hh - 4
    U = lambda ux, uy: (cx + ux * h + lean * h * (-uy) * 0.2, gy + uy * h)
    hood = (92, 100, 124); hood_d = (66, 72, 92); skin = (222, 176, 138)
    d.ellipse([U(-0.19, -0.84)[0], U(-0.19, -0.84)[1], U(0.19, -0.72)[0] * 1.0, U(0.19, -0.64)[1]], fill=hood_d)
    d.polygon([U(-0.16, -0.76), U(0.16, -0.76), U(0.2, -0.4), U(-0.2, -0.4)], fill=hood); d.polygon([U(0.0, -0.76), U(0.16, -0.76), U(0.2, -0.4), U(0.0, -0.4)], fill=hood_d)
    d.line([U(-0.02, -0.74), U(-0.03, -0.6)], fill=(210, 210, 220), width=2); d.line([U(0.03, -0.74), U(0.04, -0.6)], fill=(210, 210, 220), width=2)
    typing = math.sin(t * 14) * 0.012
    for sg in (-1, 1):                                     # arms reaching forward to the keyboard
        S = U(sg * 0.15, -0.72); E = U(sg * 0.2, -0.55); Hd = U(sg * 0.09, -0.44 + typing * sg)
        d.line([S, E, Hd], fill=hood, width=int(h * 0.075), joint="curve"); d.ellipse([Hd[0] - h * 0.032, Hd[1] - h * 0.032, Hd[0] + h * 0.032, Hd[1] + h * 0.032], fill=skin)
    hx, hy = U(0, -0.86); r = h * 0.075
    d.rectangle([hx - r * 0.3, hy + r * 0.7, hx + r * 0.3, hy + r * 1.2], fill=skin)
    d.ellipse([hx - r, hy - r * 1.1, hx + r, hy + r * 1.1], fill=skin); d.pieslice([hx - r * 1.05, hy - r * 1.3, hx + r * 1.05, hy + r * 0.4], 180, 360, fill=(48, 36, 32))
    ex = r * 0.4; ey = hy - r * 0.05
    for sg in (-1, 1):
        d.ellipse([hx + sg * ex - 3, ey - 3, hx + sg * ex + 3 + 0, ey + 3], fill=(36, 28, 26)) if mood != "sad" else d.arc([hx + sg * ex - 4, ey - 3, hx + sg * ex + 4, ey + 4], 200, 340, fill=(36, 28, 26), width=2)
        d.line([(hx + sg * ex - 5, ey - 7 + (2 if mood == "tired" else 0)), (hx + sg * ex + 5, ey - 6)], fill=(60, 44, 38), width=2)
    for sg in (-1, 1): d.arc([hx + sg * ex - 6, ey + 4, hx + sg * ex + 6, ey + 12], 20, 160, fill=(190, 150, 140), width=1)       # eye bags
    d.line([(hx - r * 0.3, hy + r * 0.62), (hx + r * 0.3, hy + r * 0.62)], fill=(150, 90, 84), width=2)
    if mood == "smile": d.arc([hx - r * 0.45, hy + r * 0.3, hx + r * 0.45, hy + r * 0.85], 20, 160, fill=(150, 90, 84), width=2)
    gl = Image.new("RGBA", lay.size, (120, 170, 255, 0)); a_ = lay.split()[3]
    if glow > 0:
        face_glow = Image.new("RGBA", lay.size, (130, 180, 255, 255)); lay = Image.blend(lay, face_glow, 0.10 * glow); lay.putalpha(a_)
    if alpha < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * alpha)))
    img.paste(lay, (int(x - cx), int(yb - gy)), lay)
    return {"head": (x + (hx - cx), yb - gy + hy), "shoulderL": (x + U(-0.15, -0.72)[0] - cx, yb - gy + U(-0.15, -0.72)[1]), "shoulderR": (x + U(0.15, -0.72)[0] - cx, yb - gy + U(0.15, -0.72)[1])}

def desk(img, t, screen_on=1.0):
    d = ImageDraw.Draw(img)
    d.rectangle([690, 556, 1060, 572], fill=(138, 100, 72)); d.rectangle([700, 572, 1050, 650], fill=(110, 78, 56)); d.rectangle([700, 572, 1050, 580], fill=(94, 66, 48))
    d.rectangle([714, 650, 730, 700], fill=(80, 56, 42)); d.rectangle([1020, 650, 1036, 700], fill=(80, 56, 42))
    # laptop seen from behind, glowing at the edges
    gl = Image.new("RGB", (W, H), (0, 0, 0)); ImageDraw.Draw(gl).rectangle([790, 480, 930, 560], fill=(int(60 * screen_on), int(90 * screen_on), int(160 * screen_on))); softglow(img, gl, 24, 1.0)
    d = ImageDraw.Draw(img); d.rounded_rectangle([796, 484, 924, 558], 8, fill=(122, 126, 140), outline=(80, 84, 96), width=3); d.ellipse([850, 514, 870, 530], fill=(160, 164, 176))
    d.rectangle([780, 556, 940, 564], fill=(100, 104, 116))
    d.ellipse([740, 520, 764, 556], fill=(240, 240, 232), outline=(150, 140, 130), width=2); d.rectangle([746, 534, 758, 556], fill=(230, 120, 80))      # a mug

def blob(img, x, yb, r, kind, t, mood="idle", Lh=None, Rh=None, alpha=1.0, sil=0.0, look=0.0, nod=0.0, run=0.0, tears=0.0, sweat=0.0, flip=False, squash=0.0, thumb=False, rot=0.0, shout=0.0):
    w = int(r * 6.4); hh = int(r * 5.0); lay = Image.new("RGBA", (w, hh), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); cx = w / 2; gy = hh - 5
    C, D = KIND[kind]; U = lambda ux, uy: (cx + ux * r, gy + uy * r * (1 - 0.0))
    top = -2.45 + squash * 0.5 + nod * 0.25
    # feet
    for sg in (-1, 1):
        ph = run * 10 + (0 if sg > 0 else math.pi); fx = sg * 0.5 + (math.sin(ph) * 0.25 if run else 0); fy = -0.04 - (max(0, math.cos(ph)) * 0.2 if run else 0)
        d.ellipse([U(fx - 0.4, fy - 0.14)[0], U(fx - 0.4, fy - 0.14)[1], U(fx + 0.4, fy + 0.14)[0], U(fx + 0.4, fy + 0.14)[1]], fill=D)
    # arms
    Lh = Lh or (-1.55, -0.55); Rh = Rh or (1.55, -0.55)
    for sg, Hd in ((-1, Lh), (1, Rh)):
        S = U(sg * 0.9, -1.25); E0 = U(*Hd); mid = ((S[0] + E0[0]) / 2, (S[1] + E0[1]) / 2); vx, vy = E0[0] - S[0], E0[1] - S[1]; n = math.hypot(vx, vy) or 1
        p1 = (-vy / n * 0.3 * r, vx / n * 0.3 * r); p = p1 if p1[1] > 0 else (-p1[0], -p1[1]); E = (mid[0] + p[0] * 0.4 * sg * 0 + p[0] * 0.5, mid[1] + p[1] * 0.5); wd = int(r * 0.34)
        d.line([S, E, E0], fill=D, width=wd, joint="curve")
        for q in (S, E): d.ellipse([q[0] - wd / 2, q[1] - wd / 2, q[0] + wd / 2, q[1] + wd / 2], fill=D)
        d.ellipse([E0[0] - r * 0.24, E0[1] - r * 0.24, E0[0] + r * 0.24, E0[1] + r * 0.24], fill=C, outline=D, width=2)
        if thumb and sg == 1:
            d.rounded_rectangle([E0[0] - r * 0.09, E0[1] - r * 0.62, E0[0] + r * 0.11, E0[1] - r * 0.1], int(r * 0.1), fill=C, outline=D, width=2)
    # body
    d.ellipse([U(-1, top)[0], U(-1, top)[1], U(1, -0.1)[0], U(1, -0.1)[1]], fill=C, outline=D, width=3)
    d.ellipse([U(-0.62, top + 0.2)[0], U(-0.62, top + 0.2)[1], U(0.1, top + 0.9)[0], U(0.1, top + 0.9)[1]], fill=tuple(min(255, c + 22) for c in C))
    if kind == "sad":      # her: dark bob hair, a little bow
        d.ellipse([U(-1.12, top - 0.1)[0], U(-1.12, top - 0.1)[1], U(1.12, top + 1.3)[0], U(1.12, top + 1.3)[1]], fill=(30, 42, 82)); d.polygon([U(-1.12, top + 0.6), U(-0.86, top + 1.9), U(-0.62, top + 0.9)], fill=(30, 42, 82)); d.polygon([U(1.12, top + 0.6), U(0.86, top + 1.9), U(0.62, top + 0.9)], fill=(30, 42, 82))
        d.polygon([U(0.52, top + 0.05), U(0.95, top - 0.18), U(0.95, top + 0.32)], fill=(244, 150, 180)); d.polygon([U(0.52, top + 0.05), U(0.1, top - 0.18), U(0.1, top + 0.32)], fill=(244, 150, 180)); d.ellipse([U(0.46, top - 0.04)[0], U(0.46, top - 0.04)[1], U(0.62, top + 0.14)[0], U(0.62, top + 0.14)[1]], fill=(210, 90, 130))
    ex = 0.4; ey = -1.62
    def eye(sg, kind_):
        cxe, cye = U(sg * ex, ey)
        if kind_ == "dot": d.ellipse([cxe - r * 0.1, cye - r * 0.12, cxe + r * 0.1, cye + r * 0.12], fill=(26, 22, 28))
        elif kind_ == "bored":
            d.ellipse([cxe - r * 0.2, cye - r * 0.18, cxe + r * 0.2, cye + r * 0.2], fill=(250, 250, 244), outline=(40, 36, 36), width=2); d.ellipse([cxe - r * 0.07 + look * r * 0.08, cye - r * 0.02, cxe + r * 0.07 + look * r * 0.08, cye + r * 0.14], fill=(26, 22, 28)); d.pieslice([cxe - r * 0.22, cye - r * 0.2, cxe + r * 0.22, cye + r * 0.22], 180, 360, fill=D)
        elif kind_ == "wide":
            d.ellipse([cxe - r * 0.27, cye - r * 0.3, cxe + r * 0.27, cye + r * 0.3], fill=(255, 255, 255), outline=(40, 36, 36), width=2); d.ellipse([cxe - r * 0.05, cye - r * 0.05, cxe + r * 0.05, cye + r * 0.05], fill=(20, 16, 20))
        elif kind_ == "closed": d.arc([cxe - r * 0.2, cye - r * 0.12, cxe + r * 0.2, cye + r * 0.2], 200, 340, fill=(30, 24, 30), width=max(3, int(r * 0.07)))
        elif kind_ == "side": d.ellipse([cxe - r * 0.16, cye - r * 0.17, cxe + r * 0.16, cye + r * 0.17], fill=(250, 250, 244), outline=(40, 36, 36), width=2); d.ellipse([cxe - r * 0.06 + look * r * 0.1, cye - r * 0.06, cxe + r * 0.06 + look * r * 0.1, cye + r * 0.07], fill=(26, 22, 28))
    em = {"idle": "dot", "bored": "bored", "thumb": "bored", "sob": "closed", "panic": "wide", "shrug": "side", "grr": "dot", "irritated": "side", "sad": "dot", "yell": "closed", "cower": "closed"}[mood]
    for sg in (-1, 1): eye(sg, em)
    if kind == "sad":
        for sg in (-1, 1): cxe, cye = U(sg * ex, ey); d.line([(cxe + sg * r * 0.18, cye - r * 0.12), (cxe + sg * r * 0.32, cye - r * 0.24)], fill=(30, 24, 30), width=3)       # lashes
    # brows
    bw = max(3, int(r * 0.07))
    if mood in ("grr", "yell"):
        for sg in (-1, 1): d.line([U(sg * 0.7, ey - 0.38), U(sg * 0.12, ey - 0.16)], fill=(70, 12, 12), width=bw + 2)
    elif mood in ("irritated", "shrug"):
        for sg in (-1, 1): d.line([U(sg * 0.68, ey - 0.3 - (0.1 if mood == "shrug" else 0.0)), U(sg * 0.14, ey - (0.18 if mood == "irritated" else 0.36))], fill=tuple(int(c * 0.45) for c in C), width=bw)
    elif mood in ("sad", "sob", "cower"):
        for sg in (-1, 1): d.line([U(sg * 0.7, ey - 0.16), U(sg * 0.16, ey - 0.34)], fill=tuple(int(c * 0.45) for c in C), width=bw)
    elif mood == "panic":
        for sg in (-1, 1): d.arc([U(sg * ex - 0.3, ey - 0.78)[0], U(sg * ex - 0.3, ey - 0.78)[1], U(sg * ex + 0.3, ey - 0.3)[0], U(sg * ex + 0.3, ey - 0.3)[1]], 200, 340, fill=tuple(int(c * 0.45) for c in C), width=bw)
    # mouth
    mx, my = U(0, -1.0)
    if mood in ("idle", "bored"): d.line([(mx - r * 0.22, my), (mx + r * 0.22, my)], fill=(40, 30, 34), width=max(3, int(r * 0.07)))
    elif mood == "thumb": d.line([(mx - r * 0.2, my), (mx + r * 0.2, my - 2)], fill=(40, 30, 34), width=max(3, int(r * 0.07)))
    elif mood in ("sob", "cower"):
        pts = [(mx + k * r * 0.1, my + math.sin(t * 20 + k) * r * 0.05 - abs(k) * r * 0.05) for k in range(-3, 4)]; d.line(pts, fill=(40, 30, 34), width=max(3, int(r * 0.07)))
    elif mood == "panic": d.ellipse([mx - r * 0.2, my - r * 0.12, mx + r * 0.2, my + r * 0.34 + 0.08 * r * math.sin(t * 26)], fill=(60, 14, 30))
    elif mood in ("shrug", "irritated"): d.line([(mx - r * 0.22, my + r * 0.04), (mx + r * 0.22, my - r * 0.02)], fill=(40, 30, 34), width=max(3, int(r * 0.07)))
    elif mood == "grr":
        d.rounded_rectangle([mx - r * 0.34, my - r * 0.14, mx + r * 0.34, my + r * 0.22], int(r * 0.08), fill=(70, 12, 18)); [d.line([(mx - r * 0.3 + k * r * 0.12, my - r * 0.12), (mx - r * 0.3 + k * r * 0.12, my - r * 0.02)], fill=(255, 255, 255), width=2) for k in range(6)]
    elif mood == "yell": d.ellipse([mx - r * 0.36, my - r * 0.2, mx + r * 0.36, my + r * 0.5], fill=(70, 12, 18)); d.ellipse([mx - r * 0.2, my + r * 0.2, mx + r * 0.2, my + r * 0.46], fill=(220, 100, 110))
    else: d.arc([mx - r * 0.22, my - r * 0.04, mx + r * 0.22, my + r * 0.3], 200, 340, fill=(40, 30, 34), width=max(3, int(r * 0.07)))
    # tears and sweat
    ex_l, ey_l = U(-ex, ey); ex_r, ey_r = U(ex, ey)
    if tears > 0:
        for sg, (tx, ty) in ((-1, (ex_l, ey_l)), (1, (ex_r, ey_r))):
            for k in range(3):
                u = (t * 1.1 + k / 3 + (0.2 if sg > 0 else 0)) % 1
                d.polygon([(tx, ty + u * r * 1.2 - 8), (tx - 5, ty + u * r * 1.2 + 2), (tx + 5, ty + u * r * 1.2 + 2)], fill=(150, 210, 255, int(255 * (1 - u))))
                d.ellipse([tx - 5, ty + u * r * 1.2 - 2, tx + 5, ty + u * r * 1.2 + 8], fill=(150, 210, 255, int(255 * (1 - u))))
    if sweat > 0:
        for k in range(3):
            u = (t * 1.3 + k / 3) % 1; sx = cx + (k - 1) * r * 0.9; sy = gy + top * r + r * 0.3 + u * r * 0.7
            d.polygon([(sx, sy - 12), (sx - 6, sy), (sx + 6, sy)], fill=(160, 215, 255)); d.ellipse([sx - 6, sy - 4, sx + 6, sy + 8], fill=(160, 215, 255))
    if sil > 0:
        a_ = lay.split()[3]; dark = Image.new("RGBA", lay.size, (16, 20, 36, 255)); lay2 = Image.blend(lay, dark, sil); lay2.putalpha(a_.point(lambda v: int(v * (0.55 if sil > 0.99 else 1.0)))); lay = lay2
    if flip: lay = lay.transpose(Image.FLIP_LEFT_RIGHT)
    if rot: lay = lay.rotate(rot, center=(cx, gy), resample=Image.BICUBIC)
    if alpha < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * alpha)))
    img.paste(lay, (int(x - cx), int(yb - gy)), lay)
    return {"head": (x, yb - gy + gy + top * r + r * 0.6 - hh * 0 + 0), "top": (x, yb - (-top) * r)}

def fetal(img, x, yb, r, t, sob=1.0, sil=0.0, alpha=1.0, pool=1.0, shake=0.0, rippl=True):
    """loneliness curled up in the fetal position in a pool of its own tears."""
    C, D = KIND["lonely"]
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    pw = r * (2.4 + 1.6 * pool); ph = r * (0.55 + 0.25 * pool)
    d.ellipse([x - pw, yb - ph * 0.5, x + pw, yb + ph * 1.1], fill=(110, 160, 230, int(150 * alpha)), outline=(160, 200, 250, int(200 * alpha)), width=3)
    for k in range(3):
        u = (t * 0.5 + k / 3) % 1; d.ellipse([x - pw * u * 0.9, yb - ph * 0.4 * u + ph * 0.1, x + pw * u * 0.9, yb + ph * 0.7 * u + ph * 0.1], outline=(200, 225, 255, int(160 * (1 - u) * alpha)), width=2)
    img.paste(lay, (0, 0), lay)
    jx = math.sin(t * 38) * 2.0 * shake + math.sin(t * 9) * 1.5 * sob; jy = math.sin(t * 7) * 1.5 * sob
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); bx, by = x + jx, yb - r * 0.95 + jy
    d.ellipse([bx - r * 1.2, by - r * 0.9, bx + r * 1.2, by + r * 0.95], fill=C + (255,), outline=D + (255,), width=3)               # curled body
    d.ellipse([bx - r * 0.7, by - r * 0.7, bx + r * 0.1, by - r * 0.1], fill=tuple(min(255, c + 22) for c in C) + (255,))
    d.ellipse([bx + r * 0.35, by + r * 0.1, bx + r * 1.3, by + r * 0.95], fill=D + (255,))                                          # knees
    d.line([(bx - r * 1.0, by + r * 0.25), (bx - r * 0.1, by + r * 0.8), (bx + r * 0.7, by + r * 0.5)], fill=D + (255,), width=int(r * 0.28))   # arms hugging
    hx, hy = bx - r * 0.55, by - r * 0.1                                                                                              # face, tucked into the knees
    d.ellipse([hx - r * 0.55, hy - r * 0.5, hx + r * 0.55, hy + r * 0.55], fill=C + (255,), outline=D + (255,), width=3)
    for sg in (-1, 1): d.arc([hx + sg * r * 0.22 - r * 0.15, hy - r * 0.12, hx + sg * r * 0.22 + r * 0.15, hy + r * 0.12], 200, 340, fill=(30, 24, 30, 255), width=max(3, int(r * 0.07))); d.line([(hx + sg * r * 0.4, hy - r * 0.22), (hx + sg * r * 0.12, hy - r * 0.36)], fill=D + (255,), width=3)
    d.arc([hx - r * 0.2, hy + r * 0.2, hx + r * 0.2, hy + r * 0.42], 200, 340, fill=(30, 24, 30, 255), width=3)
    for sg in (-1, 1):
        for k in range(3):
            u = (t * 0.9 + k / 3 + (0.15 if sg > 0 else 0)) % 1; tx = hx + sg * r * 0.22; ty = hy + r * 0.1 + u * r * 1.2
            d.ellipse([tx - 5, ty - 3, tx + 5, ty + 8], fill=(160, 215, 255, int(255 * (1 - u * 0.5)))); d.polygon([(tx, ty - 12), (tx - 5, ty - 2), (tx + 5, ty - 2)], fill=(160, 215, 255, int(255 * (1 - u * 0.5))))
    if sil > 0:
        a_ = lay.split()[3]; dark = Image.new("RGBA", lay.size, (16, 20, 36, 255)); l2 = Image.blend(lay, dark, sil); l2.putalpha(a_.point(lambda v: int(v * (0.55 if sil > 0.99 else 1.0)))); lay = l2
    if alpha < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * alpha)))
    img.paste(lay, (0, 0), lay)
    return (bx, by)

def tag_label(img, x, y, kind, a=1.0):
    if a <= 0: return
    C, D = KIND[kind]; label(img, x, y, NAMES_E[kind], 24, tuple(min(255, c + 70) for c in C), a)

def room(t, sc, screen=1.0, dim=0.0, mood="tired", glow=0.5):
    img = apartment(); m = man(img, 860, 705, 300, t, mood=mood, glow=glow); desk(img, t, screen); return img, m

def bars(img, a):
    if a <= 0: return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for k in range(9): d.rectangle([520 + k * 31, 104, 526 + k * 31, 386], fill=(40, 42, 50, int(255 * a)))
    for k in range(5): d.rectangle([58 + k * 38, 154, 64 + k * 38, 606], fill=(40, 42, 50, int(255 * a)))
    img.paste(lay, (0, 0), lay)

def vignette(img, a):
    if a <= 0: return img
    return Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), img, Image.new("L", (W, H), 0).filter(ImageFilter.GaussianBlur(1))) if False else Image.blend(img, ImageChops.multiply(img, vig_mask()), a)

_VG = {}
def vig_mask():
    if "v" not in _VG:
        yy, xx = np.mgrid[0:H, 0:W]; v = np.clip(1.15 - (((xx - 640) / 760.0) ** 2 + ((yy - 360) / 470.0) ** 2), 0.2, 1.0)
        _VG["v"] = Image.fromarray((v[..., None].repeat(3, 2) * 255).astype(np.uint8))
    return _VG["v"]

def heart_icon(d, x, y, s, col):
    d.ellipse([x - s, y - s, x, y], fill=col); d.ellipse([x, y - s, x + s, y], fill=col); d.polygon([(x - s, y - s * 0.4), (x + s, y - s * 0.4), (x, y + s)], fill=col)

def post_card(im, x, y, title_, a, likes=0, ignored=False):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([x, y, x + 400, y + 150], 14, fill=(244, 246, 250, int(250 * a)), outline=(120, 130, 160, int(255 * a)), width=3); d.rectangle([x + 2, y + 2, x + 398, y + 26], fill=(90, 110, 180, int(255 * a)))
    d.ellipse([x + 14, y + 36, x + 50, y + 72], fill=(150, 160, 190, int(255 * a)))
    im.paste(lay, (0, 0), lay)
    label(im, x + 62, y + 38, "me", 17, (60, 70, 100), a, anchor="l")
    for i, ln in enumerate(textwrap.wrap(title_, 40)[:2]): label(im, x + 62, y + 58 + i * 22, ln, 18, (30, 36, 56), a, anchor="l", bold=True)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); heart_icon(d, x + 30, y + 128, 9, (170, 176, 196, int(255 * a))); im.paste(lay, (0, 0), lay)
    label(im, x + 46, y + 116, str(likes), 18, (120, 126, 150), a, anchor="l"); label(im, x + 110, y + 116, "(seen)" if ignored else "0 replies", 17, (120, 126, 150), a, anchor="l")

# ---- scenes
def silhouettes(img, t, sc, skip=()):
    out = {}
    for kind in ("fear", "anger", "boredom"):
        if kind in skip: continue
        sil = 1.0 - revealed(kind, sc, t); blob(img, POS[kind], GY, 58, kind, t, "idle" if kind != "boredom" else "bored", sil=sil if sil > 0 else 0.0)
    if "lonely" not in skip:
        rv = revealed("lonely", sc, t); fetal(img, POS["lonely"], GY + 10, 50, t, 1.0, sil=1.0 - rv if rv < 1 else 0.0, pool=0.8)

def s_title(t, d, p):
    img, m = room(t, "title", glow=0.7); img = Image.blend(img, Image.new("RGB", (W, H), (8, 10, 22)), 0.55)
    a = tseg(t, 0.4, 1.2) * (1 - tseg(t, d - 0.8, d - 0.1)); title(img, "A TOUR OF MY EMOTIONS", "a loneliness comedy, with feelings", a, y=250, size=50)
    return img

def s_intro(t, d, p):
    n1 = ev("intro", "n1"); img, m = room(t, "intro")
    silhouettes(img, t, "intro")
    hlabel(640, 70, "my emotional state, personified", 34, (240, 236, 220), tseg(t, 0.6, 1.4) * (1 - tseg(t, d - 1.2, d - 0.4)))
    return img

def s_bored(t, d, p):
    nb, bd = ev("bored", "nb"), ev("bored", "bd"); img, m = room(t, "bored")
    rv = revealed("boredom", "bored", t); nodding = math.sin(t * 3.2) > 0
    for kind in ("fear", "anger"): blob(img, POS[kind], GY, 58, kind, t, "idle", sil=1.0)
    fetal(img, POS["lonely"], GY + 10, 50, t, 1.0, sil=1.0, pool=0.8)
    thumb = t > nb[0] + 1.2
    blob(img, POS["boredom"], GY, 62, "boredom", t, "thumb" if thumb else "bored", Rh=(1.35, -2.0) if thumb else None, thumb=thumb, nod=(max(0, math.sin(t * 3.2)) * 0.22 if thumb else 0.0), sil=1.0 - rv if rv < 1 else 0.0)
    if rv > 0.5: tag_label(img, 600, GY - 205, "boredom", tseg(t, 0.7, 1.2))
    if t > nb[0] + 6.4: HUD(lambda im: post_card(im, 820, 80, "Deep Dive #47: emotional suppression, capitalism & loneliness", tseg(t, nb[0] + 6.4, nb[0] + 7.0) * (1 - tseg(t, bd[1] + 0.2, bd[1] + 0.8)), 0))
    if bd[0] <= t <= bd[1] + 0.5: bubble(img, 600, 300, "Yep. All good over here.", 24, 1.0, tail=(600, 400))
    return img

def s_lonely(t, d, p):
    nl, ld = ev("lonely", "nl"), ev("lonely", "ld"); img, m = room(t, "lonely")
    for kind in ("fear", "anger"): blob(img, POS[kind], GY, 58, kind, t, "idle", sil=1.0)
    blob(img, POS["boredom"], GY, 62, "boredom", t, "bored")
    rv = revealed("lonely", "lonely", t); pool = 0.4 + 1.0 * tseg(t, 0.8, nl[1] + 2.0)
    fetal(img, POS["lonely"], GY + 10, 54, t, 1.0, sil=1.0 - rv if rv < 1 else 0.0, pool=pool, alpha=1.0)
    if rv > 0.5: tag_label(img, POS["lonely"], GY - 135, "lonely", tseg(t, 0.7, 1.2))
    k = nl[0] + 0.65 * (nl[1] - nl[0])
    if t > nl[0] + 5.0:                      # no cute woman by my side: an empty chair
        a = tseg(t, nl[0] + 5.0, nl[0] + 6.0) * (1 - tseg(t, ld[0] - 0.6, ld[0] + 0.0)); lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay)
        for seg in range(0, 12):
            dd.line([(1000, 470 + seg * 14), (1000, 478 + seg * 14)], fill=(255, 230, 190, int(200 * a)), width=4)
        dd.rounded_rectangle([1000, 470, 1060, 650], 10, outline=(255, 230, 190, int(200 * a)), width=4); dd.rectangle([960, 590, 1060, 604], outline=(255, 230, 190, int(200 * a)), width=4); img.paste(lay, (0, 0), lay)
        label(img, 1010, 420, "?", 70, (255, 230, 190), a)
    if t > nl[0] + 2.8: hlabel(640, 70, "24 / 7", 54, (170, 210, 255), tseg(t, nl[0] + 2.8, nl[0] + 3.4) * (1 - tseg(t, nl[0] + 6.0, nl[0] + 6.8)))
    if ld[0] <= t <= ld[1] + 0.4: bubble(img, 960, 300, "...sniff... no one to post deep dives with...", 19, 1.0, tail=(1040, 400), col=(232, 240, 255))
    return img

def s_fear(t, d, p):
    nf, fd, nf2 = ev("fear", "nf"), ev("fear", "fd"), ev("fear", "nf2"); img, m = room(t, "fear")
    rv = revealed("fear", "fear", t); on = t > nf[0] + 7.0
    for kind in ("anger",): blob(img, POS[kind], GY, 58, kind, t, "idle", sil=1.0)
    blob(img, POS["boredom"], GY, 62, "boredom", t, "bored"); fetal(img, POS["lonely"], GY + 10, 54, t, 1.0, pool=1.2)
    fx = 360 + 200 * math.sin(t * 1.9) if on else 330; face_r = math.cos(t * 1.9) > 0
    blob(img, fx, GY, 58, "fear", t, "panic" if on else "idle", Lh=(-1.2, -2.6), Rh=(1.2, -2.6), run=t * 1.2 if on else 0.0, sweat=1.0 if on else 0.0, flip=not face_r, sil=1.0 - rv if rv < 1 else 0.0)
    if rv > 0.5: tag_label(img, fx, GY - 195, "fear", tseg(t, 0.7, 1.2))
    # the stranger-filled town outside (thought cloud)
    items = [("church", "join churches", 130), ("hobby", "hobby groups", 330), ("people", "random people", 530)]
    T = "And when I think about going outside, into town, to talk to random people, or join churches, or try hobby groups in the local area... my fear starts running around with its hands in the air."
    def _town(im):
        a = tseg(t, nf[0] + 4.0, nf[0] + 4.8) * (1 - tseg(t, fd[0] - 0.2, fd[0] + 0.4))
        if a <= 0: return
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld_ = ImageDraw.Draw(lay)
        ld_.rounded_rectangle([700, 60, 1240, 300], 28, fill=(246, 244, 252, int(238 * a)), outline=(90, 80, 120, int(255 * a)), width=3); im.paste(lay, (0, 0), lay)
        for i, (kind_, txt, _) in enumerate(items):
            t0 = nf[0] + T.index({"church": "join churches", "hobby": "hobby groups", "people": "random people"}[kind_]) / len(T) * (nf[1] - nf[0]); b = tseg(t, t0 - 0.6, t0 - 0.1) * a
            if b <= 0: continue
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay); cx_ = 790 + i * 170; cy_ = 200
            if kind_ == "church": dd.rectangle([cx_ - 30, cy_ - 30, cx_ + 30, cy_ + 40], fill=(180, 160, 140, int(255 * b))); dd.polygon([(cx_ - 36, cy_ - 30), (cx_ + 36, cy_ - 30), (cx_, cy_ - 76)], fill=(150, 90, 80, int(255 * b))); dd.line([(cx_, cy_ - 76), (cx_, cy_ - 98)], fill=(90, 70, 60, int(255 * b)), width=4); dd.line([(cx_ - 8, cy_ - 90), (cx_ + 8, cy_ - 90)], fill=(90, 70, 60, int(255 * b)), width=4)
            elif kind_ == "hobby":
                for k in range(5): a_ = k / 5 * 6.28; dd.ellipse([cx_ + math.cos(a_) * 36 - 11, cy_ + math.sin(a_) * 26 - 11 - 6, cx_ + math.cos(a_) * 36 + 11, cy_ + math.sin(a_) * 26 + 11 - 6], fill=(120, 130, 170, int(255 * b))); dd.rectangle([cx_ + math.cos(a_) * 36 - 9, cy_ + math.sin(a_) * 26 + 6, cx_ + math.cos(a_) * 36 + 9, cy_ + math.sin(a_) * 26 + 26], fill=(120, 130, 170, int(255 * b)))
            else:
                for k in range(3): dd.ellipse([cx_ - 44 + k * 38 - 12, cy_ - 36, cx_ - 44 + k * 38 + 12, cy_ - 12], fill=(60, 56, 80, int(255 * b))); dd.rectangle([cx_ - 44 + k * 38 - 14, cy_ - 12, cx_ - 44 + k * 38 + 14, cy_ + 40], fill=(60, 56, 80, int(255 * b)))
            im.paste(lay, (0, 0), lay); label(im, cx_ + 4, 250, txt, 16, (70, 60, 100), b); label(im, cx_ + 4, 110, "?", 44, (200, 60, 70), b)
    HUD(_town)
    if on:                                                       # alarm
        pulse_ = 0.5 + 0.5 * math.sin(t * 9); HUD(lambda im, pu=pulse_: (im.paste(Image.blend(im, Image.new("RGB", (W, H), (230, 30, 30)), 0.12 * pu))))
    if fd[0] <= t <= fd[1] + 0.8: hlabel(400, 120 + 6 * math.sin(t * 18), "HIGH THREAT!", 52, (255, 90, 90), 1.0)
    if t > nf2[0] + 1.0:
        def _say(im):
            a = tseg(t, nf2[0] + 4.6, nf2[0] + 5.4); 
            if a <= 0: return
            bubble(im, 940, 120, "I'm suffering, and I need deep, soul-level connection with a woman my age.", 17, a, tail=(900, 190)); 
            for k, sx in enumerate((760, 900, 1040)): label(im, sx, 250 + (k % 2) * 16, "???", 36, (150, 140, 180), tseg(t, nf2[0] + 6.0 + k * 0.5, nf2[0] + 6.5 + k * 0.5))
        HUD(_say)
    return img

def s_anger(t, d, p):
    na, ad = ev("anger", "na"), ev("anger", "ad"); img, m = room(t, "anger", mood="tired")
    rv = revealed("anger", "anger", t); shrugging = t > na[0] + 0.6
    blob(img, POS["boredom"], GY, 62, "boredom", t, "bored"); fetal(img, POS["lonely"], GY + 10, 54, t, 1.0, pool=1.3)
    nodv = max(0, math.sin(t * 6)) * 0.25 if t > ad[0] + 3.5 else 0.0
    blob(img, 300 + 20 * math.sin(t * 5) * (0.5 if t > ad[0] + 3.5 else 0), GY, 58, "fear", t, "cower" if t > ad[0] + 3.5 else "panic", Lh=(-1.0, -1.6), Rh=(1.0, -1.6), nod=nodv, sweat=1.0)
    ax = 470; sh_ = tseg(t, na[0] + 0.4, na[0] + 1.0)
    blob(img, ax, GY, 62, "anger", t, "shrug" if t < ad[0] + 3.0 else "irritated", Lh=(-1.7 - 0.2 * sh_, -1.6 * sh_ - 0.55 * (1 - sh_)), Rh=(1.7 + 0.2 * sh_, -1.6 * sh_ - 0.55 * (1 - sh_)), look=1.0, sil=1.0 - rv if rv < 1 else 0.0, squash=0.15 * sh_)
    if rv > 0.5: tag_label(img, ax, GY - 200, "anger", tseg(t, 0.4, 1.0))
    def _counter(im):
        a = tseg(t, ad[0] + 0.3, ad[0] + 1.0) * (1 - tseg(t, ad[1] + 0.2, ad[1] + 0.9))
        if a <= 0: return
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay); dd.rounded_rectangle([780, 70, 1220, 200], 16, fill=(24, 20, 34, int(225 * a)), outline=(230, 90, 80, int(255 * a)), width=3); im.paste(lay, (0, 0), lay)
        label(im, 800, 84, "people actively dehumanizing you right now:", 18, (240, 220, 210), a, anchor="l")
        sw = tseg(t, ad[0] + 2.2, ad[0] + 2.8); label(im, 1000, 118, "0" if sw < 0.5 else "?!", 56, (120, 255, 150) if sw < 0.5 else (255, 90, 90), a)
        label(im, 800, 176, "(but it could happen)" if sw > 0.5 else "", 20, (255, 170, 150), a, anchor="l")
    HUD(_counter)
    return img

def s_trapped(t, d, p):
    nt, nt2, nt3, nt4 = [ev("trapped", k) for k in ("nt", "nt2", "nt3", "nt4")]; img, m = room(t, "trapped", glow=0.3)
    cell = tseg(t, nt[0] + 4.0, nt[0] + 6.0); bars(img, cell)
    blob(img, POS["boredom"], GY, 62, "boredom", t, "bored"); fetal(img, POS["lonely"], GY + 10, 54, t, 1.0, pool=1.5)
    blob(img, 300, GY, 58, "fear", t, "cower", Lh=(-1.0, -1.6), Rh=(1.0, -1.6), sweat=1.0); blob(img, 470, GY, 62, "anger", t, "irritated", look=1.0)
    img = vignette(img, 0.55 * cell)
    if t > nt[0] + 6.5 and t < nt2[0] - 0.5: hlabel(640, 74, "SOLITARY CONFINEMENT  (my apartment)", 34, (255, 220, 190), tseg(t, nt[0] + 6.5, nt[0] + 7.3) * (1 - tseg(t, nt2[0] - 1.2, nt2[0] - 0.5)))
    def _outside(im):
        a = tseg(t, nt2[0] + 0.5, nt2[0] + 1.3) * (1 - tseg(t, nt2[0] + 9.0, nt2[0] + 9.8))
        if a <= 0: return
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay); dd.rounded_rectangle([640, 80, 1240, 330], 22, fill=(60, 18, 24, int(235 * a)), outline=(240, 90, 80, int(255 * a)), width=3); im.paste(lay, (0, 0), lay)
        label(im, 940, 94, "OUTSIDE  (socially & emotionally)", 22, (255, 190, 170), a)
        for k in range(5):
            cx_ = 700 + k * 120; lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay); dd.ellipse([cx_ - 20, 160, cx_ + 20, 200], fill=(30, 20, 28, int(255 * a))); dd.rounded_rectangle([cx_ - 26, 200, cx_ + 26, 290], 16, fill=(30, 20, 28, int(255 * a))); im.paste(lay, (0, 0), lay); label(im, cx_, 118 + 90 - 8, "?", 36, (255, 120, 120), a)
        for lbl, y_, v in (("THREAT", 304, 0.95), ("UNKNOWN", 304, 0.8)): pass
        label(im, 780, 296, "THREAT: HIGH    SUPPORT: ???", 20, (255, 210, 200), a)
    HUD(_outside)
    def _internet(im):
        a = tseg(t, nt3[0] + 0.2, nt3[0] + 1.0) * (1 - tseg(t, nt3[1] + 0.2, nt3[1] + 0.8))
        if a <= 0: return
        post_card(im, 800, 70, "I've been feeling really lonely lately and I need real connection.", a, 0, True)
        for k, (c, txt) in enumerate([("troll_91:", "lol cringe"), ("xX_chad_Xx:", "ok and?"), ("(seen)", "")]):
            b = tseg(t, nt3[0] + 1.8 + k * 0.7, nt3[0] + 2.2 + k * 0.7) * a; lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay); dd.rounded_rectangle([830, 240 + k * 56, 1190, 286 + k * 56], 12, fill=(60, 40, 52, int(230 * b)), outline=(220, 100, 100, int(255 * b)), width=2); im.paste(lay, (0, 0), lay)
            label(im, 846, 252 + k * 56, c + " " + txt, 20, (255, 200, 200), b, anchor="l")
    HUD(_internet)
    T4 = "But right there, in close physical proximity to other people, there's no telling what could happen. I could be dehumanized, or gaslit, or ostracized, or told to get lost. And then my loneliness pain could go beyond a ten."
    def _prox(im):
        a = tseg(t, nt4[0] + 0.4, nt4[0] + 1.0) * (1 - tseg(t, nt4[1] + 0.3, nt4[1] + 1.0))
        if a <= 0: return
        for i, (word, key) in enumerate([("dehumanized", "dehumanized"), ("gaslit", "gaslit"), ("ostracized", "ostracized"), ("told to get lost", "told to get lost")]):
            t0 = nt4[0] + T4.index(key) / len(T4) * (nt4[1] - nt4[0]); b = tseg(t, t0, t0 + 0.3) * a
            if b > 0:
                lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay); ox = 70 + (i % 2) * 20; dd.rounded_rectangle([ox, 100 + i * 70, ox + 300, 154 + i * 70], 14, fill=(52, 16, 22, int(235 * b)), outline=(240, 90, 80, int(255 * b)), width=3); im.paste(lay, (0, 0), lay); label(im, ox + 150, 112 + i * 70, word.upper(), 26, (255, 150, 140), b)
        # a loneliness pain gauge that goes past 10
        g = tseg(t, nt4[0] + T4.index("And then") / len(T4) * (nt4[1] - nt4[0]), nt4[1] + 0.2) * a
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay); cx_, cy_, R_ = 1000, 300, 130
        dd.pieslice([cx_ - R_, cy_ - R_, cx_ + R_, cy_ + R_], 180, 360, fill=(30, 26, 40, int(235 * a)), outline=(200, 190, 220, int(255 * a)), width=3)
        for k in range(11):
            ang = math.radians(180 + k * 15); dd.line([(cx_ + math.cos(ang) * (R_ - 26), cy_ + math.sin(ang) * (R_ - 26)), (cx_ + math.cos(ang) * (R_ - 8), cy_ + math.sin(ang) * (R_ - 8))], fill=(255, 120 if k > 7 else 230, 120 if k > 7 else 230, int(255 * a)), width=3)
        ang = math.radians(180 + min(1.35, 0.1 + g * 1.25) * 150 / 1.0 * 1.0) if g > 0 else math.radians(190)
        ang = math.radians(180 + (10 + 7 * clamp(g)) * 15 / 1.0 * (1.0) * 0.0 + 150 * (0.05 + 0.95 * clamp(g)) * 1.0) if g > 0 else math.radians(190)
        over = math.radians(180 + 150 * (0.05 + 0.95 * clamp(g * 1.15)) + (10 * math.sin(t * 30) * (g > 0.9)))
        dd.line([(cx_, cy_), (cx_ + math.cos(over) * (R_ - 14), cy_ + math.sin(over) * (R_ - 14))], fill=(255, 90, 90, int(255 * a)), width=6); dd.ellipse([cx_ - 9, cy_ - 9, cx_ + 9, cy_ + 9], fill=(255, 90, 90, int(255 * a)))
        im.paste(lay, (0, 0), lay); label(im, cx_, cy_ + 12, "LONELINESS PAIN", 20, (230, 210, 230), a)
        if g > 0.75: label(im, cx_, 130, "11... 12...", 34, (255, 110, 110), tseg(g, 0.75, 0.95) * a)
    HUD(_prox)
    return img

def s_scream(t, d, p):
    ns = ev("scream", "ns"); img, m = room(t, "scream", glow=0.3); bars(img, 0.8)
    yelling = tseg(t, ns[0] + 1.0, ns[0] + 1.5) * (1 - tseg(t, ns[0] + 5.2, ns[0] + 5.8))
    blob(img, POS["boredom"], GY, 62, "boredom", t, "bored", look=-1.0)
    blob(img, 300, GY, 58, "fear", t, "cower", Lh=(-0.6, -2.2), Rh=(0.6, -2.2), sweat=1.0, squash=0.3)
    shake = yelling
    fetal(img, POS["lonely"], GY + 10, 54, t, 1.0, pool=1.6, shake=shake)
    ax = lerp(470, 900, ease(tseg(t, ns[0] + 0.6, ns[0] + 1.8))) * 1.0; ax = lerp(ax, 470, ease(tseg(t, ns[0] + 5.6, ns[0] + 6.4)))
    ax = min(ax, 880)
    blob(img, ax, GY, 70 if yelling > 0.5 else 62, "anger", t, "yell" if yelling > 0.3 else "irritated", Lh=(-1.4, -2.2), Rh=(1.4, -2.2) if yelling > 0.3 else None, shout=yelling)
    if yelling > 0.4:
        for k in range(3): label(img, ax + 120 + k * 50, GY - 220 - k * 24 + math.sin(t * 20 + k) * 3, "!", 60, (255, 90, 80), yelling)
    img = vignette(img, 0.5)
    if t > ns[0] + 5.2: hlabel(640, 90, "...that sounds like a way to break them.", 34, (255, 200, 190), tseg(t, ns[0] + 5.2, ns[0] + 5.9))
    return img

def s_sad(t, d, p):
    nsa, sd1, nq, sd2 = [ev("sad", k) for k in ("nsa", "sd1", "nq", "sd2")]; img, m = room(t, "sad", glow=0.4)
    fade = 1 - tseg(t, nsa[0] + 1.0, nsa[0] + 2.2)                         # fear and anger leave: this is not them
    blob(img, POS["boredom"], GY, 62, "boredom", t, "bored")
    if fade > 0.02: blob(img, 300, GY, 58, "fear", t, "cower", Lh=(-1.0, -1.6), Rh=(1.0, -1.6), alpha=fade); blob(img, 440, GY, 62, "anger", t, "irritated", alpha=fade)
    fetal(img, POS["lonely"], GY + 10, 54, t, 1.0, pool=1.6)
    ap = tseg(t, nsa[0] + 4.2, nsa[0] + 5.0)                               # sadness arrives and puts her arm around me
    shake = math.sin(t * 9) * 0.5 * (tseg(t, sd2[0], sd2[0] + 0.2) * (1 - tseg(t, sd2[0] + 1.0, sd2[0] + 1.3)))
    if ap > 0:
        sx = 700 + 8 * shake
        blob(img, sx, GY, 64, "sad", t, "irritated" if t > sd2[0] - 0.2 else "sad", Lh=(-1.0, -1.1), Rh=(1.95, -2.45), alpha=ap, look=-1.0, tears=0.0)
        if ap > 0.2 and ap < 1: soul_burst(img, 700, 520, ap, t) if False else None
        tag_label(img, 700, GY - 215, "sad", tseg(t, nsa[0] + 4.8, nsa[0] + 5.6))
    if t < nsa[0] + 4.0: hlabel(640, 80, "*record scratch*", 40, (255, 230, 190), tseg(t, nsa[0] + 0.2, nsa[0] + 0.5) * (1 - tseg(t, nsa[0] + 2.4, nsa[0] + 3.0)))
    if nsa[0] + 2.6 < t < nsa[0] + 5.0: label(img, POS["lonely"] - 30, GY - 160, "that's LONELINESS, on the floor", 22, (170, 210, 255), tseg(t, nsa[0] + 2.6, nsa[0] + 3.2) * (1 - tseg(t, nsa[0] + 4.6, nsa[0] + 5.0)))
    if sd2[0] - 0.1 < t < sd2[1] + 0.8: bubble(img, 700, 330, "No. Just kind of irritated.", 22, 1.0, tail=(700, 420), col=(224, 238, 255))
    return img

def s_irritated(t, d, p):
    nir, sd3 = ev("irritated", "nir"), ev("irritated", "sd3"); img, m = room(t, "irritated", glow=0.4)
    spot = tseg(t, sd3[0] - 0.4, sd3[0] + 0.6)
    blob(img, POS["boredom"], GY, 62, "boredom", t, "bored"); fetal(img, POS["lonely"], GY + 10, 54, t, 1.0, pool=1.6)
    blob(img, 700, GY, 64, "sad", t, "irritated", Lh=(-1.0, -1.1), Rh=(1.95, -2.45), look=-1.0)
    T = "Irritated that I'm actively expressing the pain of my loneliness, and society is acting like there's nothing to see here. Let's move on to more board games, and more vacations, and more restaurants, and more pictures of people smiling and nodding."
    def _feed(im):
        a = tseg(t, nir[0] + 3.6, nir[0] + 4.2) * (1 - tseg(t, sd3[0] - 0.4, sd3[0] + 0.2))
        if a <= 0: return
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay); dd.rounded_rectangle([60, 56, 1220, 250], 22, fill=(246, 244, 240, int(235 * a)), outline=(150, 140, 130, int(255 * a)), width=3); im.paste(lay, (0, 0), lay)
        label(im, 640, 62, "SOCIETY, scrolling by:  “nothing to see here”", 22, (110, 100, 100), a)
        kinds = ["board", "plane", "plate", "smile"]
        for i in range(8):
            kind_ = kinds[i % 4]; x_ = ((i * 160 + t * 70) % 1300) - 40; y_ = 150
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay); c_ = (92, 96, 120, int(255 * a))
            if kind_ == "board": dd.rectangle([x_ - 30, y_ - 30, x_ + 30, y_ + 30], outline=c_, width=4); [dd.ellipse([x_ - 18 + (k % 2) * 28, y_ - 18 + (k // 2) * 28, x_ - 8 + (k % 2) * 28, y_ - 8 + (k // 2) * 28], fill=c_) for k in range(4)]
            elif kind_ == "plane": dd.polygon([(x_ - 40, y_ + 6), (x_ + 36, y_ - 8), (x_ - 40, y_ - 20)], fill=c_); dd.polygon([(x_ - 10, y_ - 6), (x_ - 28, y_ + 30), (x_ + 4, y_ - 4)], fill=c_)
            elif kind_ == "plate": dd.ellipse([x_ - 34, y_ - 22, x_ + 34, y_ + 22], outline=c_, width=4); dd.line([(x_ - 46, y_ - 24), (x_ - 46, y_ + 24)], fill=c_, width=4); dd.line([(x_ + 46, y_ - 24), (x_ + 46, y_ + 24)], fill=c_, width=4)
            else:
                dd.ellipse([x_ - 30, y_ - 30, x_ + 30, y_ + 30], outline=c_, width=4); dd.ellipse([x_ - 14, y_ - 12, x_ - 8, y_ - 4], fill=c_); dd.ellipse([x_ + 8, y_ - 12, x_ + 14, y_ - 4], fill=c_); dd.arc([x_ - 16, y_ - 6, x_ + 16, y_ + 18], 20, 160, fill=c_, width=4)
            im.paste(lay, (0, 0), lay)
        label(im, 640, 214, "more board games · more vacations · more restaurants · more smiling pictures", 18, (120, 110, 110), a)
    HUD(_feed)
    if spot > 0:                                                         # the spotlight: there IS something to see
        dim = Image.new("RGB", (W, H), (6, 6, 16)); mask = Image.new("L", (W, H), 0); md = ImageDraw.Draw(mask); md.ellipse([560, 330, 1240, 720], fill=255); mask = mask.filter(ImageFilter.GaussianBlur(60))
        img = Image.composite(img, Image.blend(img, dim, 0.7 * spot), mask) if spot > 0 else img
        blob(img, 700, GY, 64, "sad", t, "irritated", Lh=(-1.0, -1.1), Rh=(1.95, -2.45), look=-1.0); fetal(img, POS["lonely"], GY + 10, 54, t, 1.0, pool=1.6)
        hlabel(640, 90, "YOUR SUFFERING.", 54, (255, 236, 200), tseg(t, sd3[0] + 1.6, sd3[0] + 2.2)); hlabel(640, 160, "HUMANITY.", 44, (255, 200, 180), tseg(t, sd3[0] + 3.0, sd3[0] + 3.6))
    return img

def s_meaning(t, d, p):
    nm, sd4, nend = ev("meaning", "nm"), ev("meaning", "sd4"), ev("meaning", "nend"); img, m = room(t, "meaning", glow=0.4, mood="smile" if t > nend[0] else "tired")
    blob(img, POS["boredom"], GY, 62, "boredom", t, "thumb" if t > nend[0] else "bored", Rh=(1.35, -2.0) if t > nend[0] else None, thumb=t > nend[0])
    sob_ = 1.0 - 0.7 * tseg(t, sd4[0], sd4[1])
    fetal(img, POS["lonely"], GY + 10, 54, t, sob_, pool=1.6)
    looking = tseg(t, sd4[0] - 0.4, sd4[0] + 0.6) * (1 - tseg(t, sd4[1] + 0.4, sd4[1] + 1.2))
    blob(img, 700, GY, 64, "sad", t, "sad" if t > sd4[0] - 1.0 else "irritated", Lh=(-1.0, -1.1), Rh=(1.95, -2.45), look=-1.0 + 0.0 * looking, tears=1.0 if t > sd4[0] else 0.0)
    # strangers walking past outside the window, not looking
    for k in range(5):
        px = ((t * 55 + k * 270) % 1500) - 150
        if 520 < px < 770:
            ImageDraw.Draw(img).ellipse([px - 9, 306, px + 9, 326], fill=(12, 16, 32)); ImageDraw.Draw(img).rectangle([px - 11, 326, px + 11, 372], fill=(12, 16, 32)); ImageDraw.Draw(img).rectangle([px - 6, 338, px + 6, 350], fill=(150, 210, 255))
    def _def(im):
        a = tseg(t, nm[0] + 0.6, nm[0] + 1.4) * (1 - tseg(t, nm[0] + 9.0, nm[0] + 9.8))
        if a <= 0: return
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay); dd.rounded_rectangle([160, 60, 1120, 210], 22, fill=(22, 36, 70, int(235 * a)), outline=(120, 170, 240, int(255 * a)), width=3); im.paste(lay, (0, 0), lay)
        label(im, 640, 74, "SADNESS  =", 30, (150, 200, 255), a); label(im, 640, 116, "recognizing suffering in another human being", 28, (240, 246, 255), a); label(im, 640, 154, "and thinking about how to care for them", 28, (240, 246, 255), a)
    HUD(_def)
    def _score(im):
        a = tseg(t, nm[0] + 10.0, nm[0] + 10.8) * (1 - tseg(t, sd4[1] + 0.6, sd4[1] + 1.4))
        if a <= 0: return
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay); dd.rounded_rectangle([780, 70, 1220, 250], 18, fill=(24, 20, 34, int(230 * a)), outline=(200, 190, 220, int(255 * a)), width=3); im.paste(lay, (0, 0), lay)
        for i, (nm_, val) in enumerate([("empathy shown", "0"), ("solidarity", "0"), ("material support", "0")]):
            b = tseg(t, nm[0] + 10.6 + i * 0.5, nm[0] + 11.1 + i * 0.5) * a; label(im, 800, 88 + i * 52, nm_, 24, (230, 224, 240), b, anchor="l"); label(im, 1180, 84 + i * 52, val, 40, (255, 120, 120), b, anchor="c")
    HUD(_score)
    if t > nend[0] - 0.3: hlabel(640, 90, "messed up emotions, bro.", 40, (255, 240, 210), tseg(t, nend[0], nend[0] + 0.6))
    fade = tseg(t, d - 2.0, d - 0.2)
    if fade > 0: img = Image.blend(img, Image.new("RGB", (W, H), (0, 0, 0)), fade)
    return img

def _shift(fn):
    def f(t, d, p):
        img = fn(t, d, p); out = Image.new("RGB", (W, H), (112, 86, 68)); out.paste(img, (0, -90)); out.paste(img.crop((0, H - 4, W, H)).resize((W, 90)).filter(ImageFilter.GaussianBlur(40)), (0, H - 90)); return out
    return f
_SF = {"title": s_title, "intro": s_intro, "bored": s_bored, "lonely": s_lonely, "fear": s_fear, "anger": s_anger, "trapped": s_trapped, "scream": s_scream, "sad": s_sad, "irritated": s_irritated, "meaning": s_meaning}
SCENE_FN = {k: (v if k == "title" else _shift(v)) for k, v in _SF.items()}
CAMK = {"intro": [(0, 640, 400, 1.0), ("end", 700, 420, 1.1)],
        "bored": [(0, 620, 440, 1.5), ("end", 640, 440, 1.45)],
        "lonely": [(0, 1050, 480, 1.55), ("end", 1050, 500, 1.7)],
        "fear": [(0, 420, 470, 1.25), ("end", 560, 470, 1.15)],
        "anger": [(0, 460, 470, 1.4), ("end", 520, 470, 1.35)],
        "trapped": [(0, 640, 400, 1.0), ("end", 640, 410, 1.0)],
        "scream": [(0, 800, 490, 1.15), ("end", 820, 490, 1.25)],
        "sad": [(0, 780, 480, 1.35), ("end", 790, 470, 1.55)],
        "irritated": [(0, 820, 450, 1.15), ("end", 860, 470, 1.35)],
        "meaning": [(0, 820, 470, 1.25), ("end", 820, 470, 1.45)]}
CONT_IN = set(ORDER) - {"title", "intro"}
CONT_OUT = set(ORDER) - {"title", "meaning"}


SPK = {"n": (255, 255, 255), "b": (206, 220, 178), "l": (170, 205, 255), "f": (222, 184, 248), "a": (255, 150, 140), "s": (150, 200, 255)}
NAMES = {"b": "BOREDOM", "l": "LONELINESS", "f": "FEAR", "a": "ANGER", "s": "SADNESS"}
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
                           "-shortest", "-movflags", "+faststart", "a_tour_of_my_emotions.mp4"], stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for k, b in enumerate(pool.imap(frame, range(n), chunksize=6)):
            ff.stdin.write(b)
            if k % 240 == 0: print(k, "/", n, flush=True)
    ff.stdin.close(); ff.wait()
