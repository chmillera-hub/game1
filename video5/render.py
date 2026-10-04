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
OFF = 70
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
         armor=False, shield=False, spear=False, mouth="flat", brow=0.0, cut=None, rot=0.0, hood=False, eyes="open", wide=1.0, hscale=1.0, brow1=0.0):
    """frontal figure. returns world positions of hands and head."""
    yb = yb - OFF
    if cut is not None: cut = cut - OFF
    w = int(h * 1.8); hh = int(h * 1.14); lay = Image.new("RGBA", (w, hh), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    cx = w / 2; gy = hh - 4
    U = lambda ux, uy: (cx + ux * h * wide, gy + uy * h)
    L = L or (-0.2, -0.42); R = R or (0.2, -0.42)
    shade = tuple(int(c * 0.82) for c in robe)
    sL, sR = U(-0.13, -0.77), U(0.13, -0.77)
    def arm(S, Hd, col):
        S = S; E0 = U(*Hd); mid = ((S[0] + E0[0]) / 2, (S[1] + E0[1]) / 2); vx, vy = E0[0] - S[0], E0[1] - S[1]; n = math.hypot(vx, vy) or 1
        p1 = (-vy / n * 0.05 * h, vx / n * 0.05 * h); p2 = (-p1[0], -p1[1]); p = p1 if p1[1] > p2[1] else p2
        E = (mid[0] + p[0], mid[1] + p[1]); wd = int(h * 0.062)
        d.line([S, E, E0], fill=col, width=wd, joint="curve")
        for q in (S, E): d.ellipse([q[0] - wd / 2, q[1] - wd / 2, q[0] + wd / 2, q[1] + wd / 2], fill=col)
        d.ellipse([E0[0] - h * 0.032, E0[1] - h * 0.032, E0[0] + h * 0.032, E0[1] + h * 0.032], fill=skin)
    # back-most: spear
    if spear:
        hx, hy = U(*R); d.line([(hx, hy + h * 0.55), (hx - 4, hy - h * 0.6)], fill=(110, 80, 50), width=5); d.polygon([(hx - 4, hy - h * 0.72), (hx - 11, hy - h * 0.58), (hx + 3, hy - h * 0.58)], fill=(200, 205, 214))
    # robe body
    d.polygon([U(-0.13, -0.78), U(0.13, -0.78), U(0.17, -0.5), U(0.23, 0.0), U(-0.23, 0.0), U(-0.17, -0.5)], fill=robe)
    d.polygon([U(-0.02, -0.78), U(0.13, -0.78), U(0.17, -0.5), U(0.23, 0.0), U(0.05, 0.0)], fill=shade)
    if sash: d.polygon([U(-0.17, -0.5), U(0.17, -0.5), U(0.18, -0.45), U(-0.18, -0.45)], fill=sash); d.polygon([U(0.1, -0.45), U(0.15, -0.45), U(0.15, -0.2), U(0.1, -0.2)], fill=sash)
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


JESUS = dict(robe=(244, 240, 230), skin=SKIN[0], hair=(100, 68, 46), beard=True, sash=(170, 120, 70))
_HUDQ = []
def HUD(fn): _HUDQ.append(fn)
def hlabel(*a, **k): HUD(lambda im: label(im, *a, **k))
# ================================================================= Kingdom scene specifics
def speaking(sc, tag, t): 
    a, b = ev(sc, tag); return a <= t <= b
def talk_mouth(t, on, rest="flat"): return ("o" if math.sin(t * 15) > 0.1 else "flat") if on else rest

# ---- the world
_BG = {}
def road_bg(sun):
    k = int(round(clamp(sun) * 20))
    if k in _BG: return _BG[k].copy()
    s = k / 20.0
    top = mix((92, 150, 214), (52, 44, 104), s); hor = mix((255, 214, 140), (255, 116, 70), s)
    img = gradient(top, hor, "road%d" % k); d = ImageDraw.Draw(img)
    sx, sy = 300, 250 + 100 * s
    lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay); ld.ellipse([sx - 110, sy - 110, sx + 110, sy + 110], fill=mix((255, 224, 150), (255, 130, 70), s)); softglow(img, lay, 90, 1.6)
    d = ImageDraw.Draw(img); d.ellipse([sx - 46, sy - 46, sx + 46, sy + 46], fill=mix((255, 244, 200), (255, 190, 120), s))
    rng = random.Random(6)
    for i in range(6):
        cx = rng.uniform(0, W); cy = rng.uniform(70, 230); w = rng.uniform(160, 330)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); cd = ImageDraw.Draw(lay); cd.ellipse([cx - w / 2, cy - 12, cx + w / 2, cy + 12], fill=mix((255, 230, 190), (255, 150, 110), s) + (90,)); img.paste(lay, (0, 0), lay)
    d = ImageDraw.Draw(img)
    far = mix((150, 130, 160), (80, 52, 96), s); near = mix((112, 100, 84), (60, 42, 60), s); ground = mix((206, 164, 106), (120, 84, 70), s)
    d.polygon([(0, 330), (160, 290), (340, 320), (560, 276), (800, 318), (1040, 280), (1280, 316), (1280, 360), (0, 360)], fill=far)
    # a small village on the far hill
    for i, (vx, vw, vh) in enumerate([(930, 40, 26), (976, 34, 34), (1016, 46, 24), (1070, 36, 30), (1114, 42, 22)]):
        d.rectangle([vx, 324 - vh, vx + vw, 330], fill=mix((176, 150, 120), (84, 62, 80), s)); d.rectangle([vx + vw * 0.3, 330 - vh * 0.6, vx + vw * 0.55, 330], fill=mix((80, 60, 50), (30, 20, 40), s))
    d.polygon([(0, 346), (220, 318), (500, 340), (760, 320), (1000, 344), (1280, 326), (1280, 420), (0, 420)], fill=near)
    for tx, ty, sc_ in ((120, 346, 1.0), (240, 338, 0.8), (1100, 340, 0.9), (1210, 350, 1.1)):
        d.line([(tx, ty), (tx + 4, ty - 44 * sc_)], fill=mix((70, 52, 36), (30, 20, 30), s), width=int(7 * sc_))
        for k in range(5): d.ellipse([tx - 30 * sc_ + k * 14 * sc_, ty - 74 * sc_ + (k % 2) * 12, tx - 6 * sc_ + k * 14 * sc_, ty - 50 * sc_ + (k % 2) * 12], fill=mix((92, 118, 70), (40, 50, 60), s))
    d.rectangle([0, 396, W, H], fill=ground)
    d.polygon([(470, H), (900, H), (700, 372), (610, 372)], fill=mix((228, 190, 130), (150, 108, 90), s))
    for k in range(4): d.line([(560 + k * 70, H), (640 + k * 12, 380)], fill=mix((206, 164, 106), (120, 84, 70), s), width=3)
    r2 = random.Random(8)
    for i in range(16):
        rx = r2.uniform(0, W); ry = r2.uniform(420, 700)
        if 470 < rx < 900 and ry > 400: continue
        d.ellipse([rx - 16, ry - 9, rx + 16, ry + 9], fill=mix((150, 124, 96), (80, 60, 70), s))
    _BG[k] = img
    return img.copy()

def kingdom(img, a, t):
    if a <= 0.01: return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); gold = (255, 226, 150)
    base = 336
    shapes = [(820, 40, 46), (858, 30, 70), (890, 36, 104), (930, 28, 62), (966, 44, 130), (1012, 30, 76), (1048, 38, 98), (1088, 32, 58), (1124, 40, 80)]
    for x, w, h in shapes:
        d.rectangle([x, base - h, x + w, base], fill=gold + (int(235 * a),)); d.pieslice([x, base - h - w * 0.5, x + w, base - h + w * 0.5], 180, 360, fill=gold + (int(235 * a),))
        d.rectangle([x + w * 0.4, base - h * 0.5, x + w * 0.6, base - h * 0.3], fill=(255, 250, 220, int(255 * a)))
    d.line([(995, base - 140), (995, base - 190)], fill=gold + (int(255 * a),), width=3); d.polygon([(995, base - 196), (987, base - 182), (1003, base - 182)], fill=(255, 250, 230, int(255 * a)))
    img.paste(lay, (0, 0), lay)
    gl = Image.new("RGB", (W, H), (0, 0, 0)); gd = ImageDraw.Draw(gl); r = 190 + 14 * math.sin(t * 2)
    gd.ellipse([970 - r * 1.3, base - 60 - r * 0.6, 970 + r * 1.3, base - 60 + r * 0.6], fill=(int(150 * a), int(118 * a), int(54 * a))); softglow(img, gl, 60, 1.3)
    rays(img, 995, base - 90, t, (255, 226, 150), n=12, length=360, strength=0.22 * a)

def dust(img, t, a=1.0): particles(img, t, int(46 * a), 3, (255, 220, 150), speed=8, size=2, up=True, wob=22)

def shadow(img, x, yb, h, sun):
    L = h * (1.1 + 1.6 * sun); lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); y = yb - OFF
    d.polygon([(x - 0.18 * h, y), (x + 0.18 * h, y), (x + 0.18 * h - L, y + 0.07 * h), (x - 0.18 * h - L, y + 0.07 * h)], fill=(50, 30, 20, 90)); img.paste(lay, (0, 0), lay)

def seat(img, x, yb, h, robe, skin, rock=False, L=None, R=None, **kw):
    d = ImageDraw.Draw(img); y = yb - OFF
    if rock: d.polygon([(x - 0.30 * h, y + 0.02 * h), (x - 0.27 * h, y - 0.07 * h), (x - 0.12 * h, y - 0.13 * h), (x + 0.12 * h, y - 0.12 * h), (x + 0.27 * h, y - 0.06 * h), (x + 0.31 * h, y + 0.02 * h)], fill=(150, 128, 102), outline=(104, 86, 68))
    pos = cfig(img, x, yb + 0.22 * h, h, robe, skin, cut=yb - 0.27 * h, L=L or (-0.13, -0.5), R=R or (0.13, -0.5), **kw)
    d.ellipse([x - 0.25 * h, y - 0.25 * h, x + 0.25 * h, y - 0.07 * h], fill=tuple(int(c * 0.93) for c in robe)); d.arc([x - 0.25 * h, y - 0.25 * h, x + 0.25 * h, y - 0.07 * h], 195, 345, fill=tuple(int(c * 0.72) for c in robe), width=2)
    return pos

JX, JY, JH = 880, 640, 300
ODX, ODY, ODH = 410, 654, 300
DISC = [dict(x=1190, y=606, h=200, robe=(160, 150, 100), skin=SKIN[3], hair=(70, 50, 36), beard=True), dict(x=570, y=618, h=210, robe=(120, 90, 110), skin=SKIN[0], hair=None, beard=True),
        dict(x=1062, y=632, h=236, robe=(110, 130, 150), skin=SKIN[1], hair=None, beard=False), dict(x=704, y=648, h=258, robe=(150, 100, 80), skin=SKIN[2], hair=(60, 44, 32), beard=True)]

def drop(img, x, y, u):
    d = ImageDraw.Draw(img); y = y + u * 40; a = 1 - u
    d.polygon([(x, y - 12), (x - 6, y), (x + 6, y)], fill=(int(120 + 100 * u), int(180 + 60 * u), 255)); d.ellipse([x - 6, y - 4, x + 6, y + 8], fill=(int(120 + 100 * u), int(180 + 60 * u), 255))

def world(t, sun=0.0, jes=None, od=None, disc=None, kingdom_a=0.0, tint=None, dim=0.0, odvis=True, bg=None):
    jes = jes or {}; od = od or {}; disc = disc or {}
    img = bg.copy() if bg is not None else road_bg(sun); kingdom(img, kingdom_a, t); dust(img, t)
    d = ImageDraw.Draw(img)
    for p_ in DISC: shadow(img, p_["x"], p_["y"], p_["h"], sun)
    shadow(img, JX, JY, JH, sun)
    if odvis: shadow(img, ODX, ODY, ODH, sun)
    look = disc.get("look", 0.0); dm = disc.get("mouth", "smile" if look < 0.1 else "o"); sh = disc.get("shift", 0.0)
    for i, p_ in enumerate(DISC):
        seat(img, p_["x"], p_["y"] + (math.sin(t * 1.3 + i) * 1.2), p_["h"], p_["robe"], p_["skin"], hair=p_["hair"], beard=p_["beard"], mouth=dm if dm != "smile" else "flat", eyes="open", hood=(i == 1))
    # Jesus
    g = jes.get("gest", 0.0); gs = math.sin(t * 3.1) * 0.07 * g; gs2 = math.sin(t * 2.3 + 1) * 0.06 * g
    Lh = jes.get("L") or (-0.2 - gs, -0.58 + abs(gs2)); Rh = jes.get("R") or (0.2 + gs2, -0.58 + abs(gs))
    lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay); hy = JY - OFF - 0.74 * JH
    ld.ellipse([JX - 90, hy - 90, JX + 90, hy + 90], fill=(110 + int(50 * jes.get("glow", 0.3)), 90 + int(40 * jes.get("glow", 0.3)), 50)); softglow(img, lay, 50, 1.0)
    jp = seat(img, JX, JY, JH, rock=True, L=Lh, R=Rh, mouth=jes.get("mouth", "smile"), eyes=jes.get("eyes", "open"), brow1=jes.get("brow1", 0.0), **{k: v for k, v in JESUS.items() if k != "robe" and k != "skin"}, robe=JESUS["robe"], skin=JESUS["skin"])
    # the overwhelmed disciple
    if odvis:
        od_l = od.get("L") or (-0.2, -0.42); od_r = od.get("R") or (0.2, -0.42); tr = od.get("tremble", 0.0)
        ox = ODX + math.sin(t * 38) * 2.2 * tr
        op = cfig(img, ox, ODY + math.sin(t * 1.1) * 0.8, ODH, (208, 178, 126), (226, 164, 132), hair=(120, 74, 42), sash=(108, 120, 60), L=od_l, R=od_r, mouth=od.get("mouth", "flat"), eyes=od.get("eyes", "blank"), wide=1.32, hscale=1.28)
        if od.get("sweat", 0.0) > 0:
            for k in range(3): drop(img, op["head"][0] + 36 + k * 8, op["head"][1] - 40 + k * 14, ((t * 0.9 + k / 3) % 1.0))
    if tint is not None: img = Image.blend(img, Image.new("RGB", (W, H), tint[:3]), tint[3])
    warm = Image.new("RGB", (W, H), mix((255, 196, 120), (255, 120, 90), sun)); img = Image.blend(img, warm, 0.10 + 0.1 * sun)
    if dim > 0: img = Image.blend(img, Image.new("RGB", (W, H), (6, 4, 12)), dim)
    return img

# ---- scenes
def s_title(t, d, p):
    img = world(t, 0.0, jes=dict(mouth="smile"), od=dict(), dim=0.5)
    a = tseg(t, 0.4, 1.4) * (1 - tseg(t, d - 1.0, d - 0.2))
    title(img, "JESUS, THE KINGDOM,", "and one extremely overwhelmed disciple", a, y=235, size=50)
    return img

def s_setup(t, d, p):
    st = ev("setup", "set"); tt = t - st[0]
    gest = tseg(t, 12.0, 13.0) * 0.8
    img = world(t, 0.0, jes=dict(gest=gest, mouth=talk_mouth(t, gest > 0.3, "smile")), od=dict(), disc=dict(look=0.0))
    return img

def s_speech(t, d, p):
    s1, s2, s3 = ev("speech", "s1"), ev("speech", "s2"), ev("speech", "s3")
    on = any(a <= t <= b for a, b in (s1, s2, s3)); seeit = s2[0] + 0.76 * (s2[1] - s2[0])
    ka = tseg(t, seeit - 0.3, seeit + 1.0)                                     # the kingdom shimmers into view for Jesus
    ka2 = ka * (0.45 + 0.55 * tseg(t, seeit + 1.0, seeit + 2.4)) * (0.8 + 0.2 * tseg(t, s3[0], s3[0] + 1))
    look = tseg(t, seeit + 1.2, seeit + 2.6) * 0.9
    img = world(t, 0.0, jes=dict(gest=1.0 if on else 0.3, mouth=talk_mouth(t, on, "smile"), glow=0.3 + 0.7 * ka), od=dict(mouth="flat"), disc=dict(look=look), kingdom_a=ka2)
    return img

def s_stare(t, d, p):
    dr, pa = ev("stare", "drink"), ev("stare", "patrick")
    img = world(t, 0.0, jes=dict(mouth="smile"), od=dict(mouth="o", tremble=0.0), disc=dict(look=1.0, mouth="o"), kingdom_a=0.5)
    wf = tseg(t, dr[0] + 1.5, dr[0] + 2.5) * (1 - tseg(t, dr[1] + 0.2, dr[1] + 1.2))      # words pouring down like a waterfall
    if wf > 0:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay); r = random.Random(12)
        for i in range(70):
            x = r.uniform(380, 1260); sp = 200 + r.random() * 260; y = ((t * sp + r.random() * 800) % 560) + 20
            ld.line([(x, y), (x, y + 30 + r.random() * 40)], fill=(255, 232, 170, int(150 * wf)), width=3)
        for k, wd in enumerate(["world", "abandon", "Father", "kingdom", "believe", "see it"]):
            x = 520 + k * 120; y = ((t * 160 + k * 90) % 520) + 30; ld.text((x, y), wd, font=F(22, bold=True), fill=(255, 244, 200, int(230 * wf)))
        img.paste(lay, (0, 0), lay)
    return img

def s_bro(t, d, p):
    b, br = ev("bro", "bro"), ev("bro", "brow")
    sp = b[0] <= t <= b[1]
    img = world(t, 0.0, jes=dict(mouth="flat", brow1=1.0 if t > br[0] - 0.2 else 0.0), od=dict(mouth=talk_mouth(t, sp, "o"), L=(-0.42, -0.5) if sp else None, R=(0.42, -0.5) if sp else None, sweat=1.0 if sp else 0.0), disc=dict(look=1.0, mouth="o"), kingdom_a=0.0)
    if sp: bubble(img, 420, 300, "Bro...", 34, 1.0, tail=(420, 350))
    if t > br[0] and t < br[0] + 1.6: label(img, 880, 170, "✨ (one eyebrow) ✨", 24, (255, 240, 200), tseg(t, br[0], br[0] + 0.3))
    return img

ODDS_TEXT = "Look, man... we're living with overwhelming odds against us. The Pharisees are super powerful. Rome probably despises me personally. I don't have money. I don't have an army. I don't have political connections. I'm literally just some guy hanging out with you. And they're probably going to kill you. So what are you even trying to say?"
ODDS_CARDS = [("The Pharisees are", "PHARISEES", "super powerful"), ("Rome probably", "ROME", "despises me personally"), ("I don't have money", "MONEY", "none"), ("I don't have an army", "ARMY", "none"),
              ("I don't have political", "CONNECTIONS", "none"), ("I'm literally just", "JUST SOME GUY", "hanging out with you"), ("And they're probably", "THEY'LL KILL YOU", "probably")]

def s_odds(t, d, p):
    o, pa = ev("odds", "odds"), ev("odds", "patience")
    sp = o[0] <= t <= o[1] + 0.2; tt = (t - o[0]) / (o[1] - o[0])
    wob = math.sin(t * 3) * 0.08
    img = world(t, 0.0, jes=dict(mouth="smile", glow=0.4), od=dict(mouth=talk_mouth(t, sp, "o"), L=(-0.45 - wob, -0.55 + wob) if sp else None, R=(0.45 + wob, -0.55 - wob) if sp else None, tremble=0.4 if sp else 0.0, sweat=1.0), disc=dict(look=1.0, mouth="o"))
    for i, (key, h1, h2) in enumerate(ODDS_CARDS):
        t0 = o[0] + ODDS_TEXT.index(key) / len(ODDS_TEXT) * (o[1] - o[0]); a = tseg(t, t0, t0 + 0.3) * (1 - tseg(t, o[1] + 0.8, o[1] + 1.4))
        if a <= 0: continue
        y = 96 + i * 52 + (1 - a) * 14
        def _card(im, y=y, a=a, h1=h1, h2=h2):
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
            ld.rounded_rectangle([40, y, 420, y + 46], 12, fill=(30, 22, 36, int(215 * a)), outline=(230, 120, 100, int(230 * a)), width=2); im.paste(lay, (0, 0), lay)
            label(im, 58, y + 4, h1, 17, (255, 170, 150), a, anchor="l"); label(im, 58, y + 24, h2, 16, (255, 240, 225), a, anchor="l")
        HUD(_card)
    if t > pa[0]:
        a = tseg(t, pa[0] + 0.5, pa[0] + 1.5)
        lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay)
        for k in range(10):
            u = (t * 0.3 + k / 10) % 1; x = JX - 80 + math.sin(k * 2 + t) * 90; y = JY - 380 - u * 120
            ld.polygon([(x, y + 8), (x - 9, y - 2), (x - 5, y - 8), (x, y - 3), (x + 5, y - 8), (x + 9, y - 2)], fill=(int(255 * (1 - u) * a), int(130 * (1 - u) * a), int(150 * (1 - u) * a)))
        softglow(img, lay, 8, 2.0); img.paste(ImageChops.add(img, lay))
    return img

def s_drone(t, d, p):
    dr, bl = ev("drone", "drone"), ev("drone", "blinks")
    sp = dr[0] <= t <= dr[1]; tt = (t - dr[0]) / (dr[1] - dr[0])
    txt = "If you aren't building the kingdom with me... then what are you doing? Are you going to be an obedient drone? You think that's going to help build the kingdom? You think the kingdom will come if you contribute to the system of death and destruction and hell on earth?"
    i_dr = txt.index("obedient") / len(txt); i_sys = txt.index("system of death") / len(txt)
    ash = tseg(tt, i_sys - 0.02, i_sys + 0.08) * (1 - tseg(t, bl[0] - 0.3, bl[0] + 0.6))
    img = world(t, 0.0, jes=dict(gest=1.0 if sp else 0.2, mouth=talk_mouth(t, sp, "flat"), glow=0.6), od=dict(mouth="flat", eyes="blank" if (t < bl[0] or int(t * 6) % 3) else "closed", sweat=1.0), disc=dict(look=1.0, mouth="o"), tint=(90, 30, 24, 0.42 * ash))
    # a line of identical grey 'obedient drones' marches across the road
    da = tseg(tt, i_dr - 0.01, i_dr + 0.05) * (1 - tseg(tt, i_sys + 0.05, i_sys + 0.12))
    if da > 0:
        for k in range(9):
            x = ((t * 90 + k * 140) % 1500) - 110; cfig(img, x, 530, 120, (110, 110, 118), (170, 168, 170), mouth="flat", eyes="blank", alpha=da, L=(-0.14, -0.4), R=(0.14, -0.4))
        hlabel(640, 120, "OBEDIENT DRONES", 36, (225, 225, 235), da)
    if ash > 0:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        for k in range(7):
            x = 120 + k * 190; u = (t * 0.25 + k * 0.17) % 1
            ld.rectangle([x, 250, x + 30, 340], fill=(40, 30, 34, int(220 * ash)))
            for j in range(6): ld.ellipse([x - 14 + math.sin(t * 2 + j + k) * 14, 240 - j * 34 - u * 30, x + 44 + math.sin(t * 2 + j) * 10, 270 - j * 34 - u * 30], fill=(70, 56, 56, int(120 * ash * (1 - j / 7))))
        img.paste(lay, (0, 0), lay)
        hlabel(640, 120, "THE SYSTEM OF DEATH AND DESTRUCTION", 32, (255, 180, 160), ash)
    return img

def s_force(t, d, p):
    f, ps, vl = ev("force", "force"), ev("force", "pause"), ev("force", "village")
    sp = f[0] <= t <= f[1] or vl[0] <= t <= vl[1]
    txt = "The world will force you to see what I'm saying. If not today, then tomorrow. If not tomorrow, then someday in your life. You will see that there is no other way but to build the kingdom now, with me and with the Father."
    def at(s_): return f[0] + txt.index(s_) / len(txt) * (f[1] - f[0])
    ka = tseg(t, at("You will see") - 0.2, at("You will see") + 1.2) * (1 - 0.0)
    look = tseg(t, at("You will see"), at("You will see") + 1.5)
    # village / burning world thought (the alternative)
    vil = tseg(t, vl[0] + 1.2, vl[0] + 2.0) * (1 - tseg(t, vl[0] + 5.8, vl[0] + 6.4))
    pointing = tseg(t, vl[1] - 2.4, vl[1] - 1.8)
    jl = (-0.2 - 0.55 * pointing, -0.58 - 0.12 * pointing)
    img = world(t, 0.0, jes=dict(gest=1.0 if sp and pointing < 0.1 else 0.1, L=jl if pointing > 0.01 else None, mouth=talk_mouth(t, sp, "smile"), glow=0.5 + 0.5 * ka), od=dict(mouth="flat", sweat=1.0 if t > vl[1] - 3 else 0.0), disc=dict(look=0.5 + 0.5 * look, mouth="o"), kingdom_a=ka)
    for k, (w, key, x) in enumerate([("TODAY", "today", 250), ("TOMORROW", "tomorrow", 640), ("SOMEDAY", "someday", 1030)]):
        t0 = at({"today": "If not today", "tomorrow": "then tomorrow", "someday": "then someday"}[key]); a = tseg(t, t0 - 0.1, t0 + 0.3) * (1 - tseg(t, t0 + 2.4, t0 + 3.0))
        if a > 0:
            def _day(im, x=x, a=a, w=w):
                cx, cy, r = x, 150 - (1 - a) * 12, 22
                lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay); ld.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(int(255 * a), int(210 * a), int(120 * a))); softglow(im, lay, 14, 1.4)
                label(im, x, 188, w, 34, (255, 244, 214), a)
            HUD(_day)
    now = at("build the kingdom now") 
    if t > now: label(img, 640, 120, "BUILD THE KINGDOM — NOW", 44, (255, 238, 190), tseg(t, now, now + 0.5) * (1 - tseg(t, f[1] + 0.2, f[1] + 0.9)))
    if vil > 0:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        ld.ellipse([300, 70, 620, 250], fill=(250, 246, 236, int(240 * vil)), outline=(80, 60, 50, int(255 * vil)), width=3)
        for k in range(4): ld.rectangle([390 + k * 44, 170 - (k % 2) * 14, 424 + k * 44, 200], fill=(196, 160, 120, int(255 * vil)))
        for k in range(8):
            fx = 330 + k * 38; ld.polygon([(fx, 232), (fx + 10, 200 - (k % 3) * 8), (fx + 20, 232)], fill=(238, 100, 40, int(230 * vil)))
        img.paste(lay, (0, 0), lay); label(img, 460, 90, "a quiet village", 20, (70, 50, 40), vil)
    return img

def s_silence(t, d, p):
    st, ab, lg, ye = ev("silence", "still"), ev("silence", "absurd"), ev("silence", "long"), ev("silence", "yeah")
    u = tseg(t, ab[0], lg[1]); sun = 0.62 * u
    img = world(t, sun, jes=dict(mouth="flat", eyes="open", glow=0.3), od=dict(mouth="flat", eyes="blank", tremble=0.0), disc=dict(look=0.0, mouth="flat"))
    # a fly circles the frozen disciple's head, and a tumbleweed rolls through
    if t > lg[0] + 1.0 and t < ye[0]:
        fa = tseg(t, lg[0] + 1.0, lg[0] + 1.5); a = t * 7
        fx = ODX + 40 + math.cos(a) * (60 + 30 * math.sin(t * 1.3)); fy = ODY - OFF - 0.95 * ODH + math.sin(a * 1.3) * 34
        dd = ImageDraw.Draw(img); dd.ellipse([fx - 3, fy - 3, fx + 3, fy + 3], fill=(20, 16, 16)); dd.line([(fx - 6, fy - 4), (fx, fy - 1)], fill=(120, 120, 130), width=1); dd.line([(fx + 6, fy - 4), (fx, fy - 1)], fill=(120, 120, 130), width=1)
    tw = tseg(t, lg[0] + 2.4, lg[0] + 7.0)
    if 0 < tw < 1:
        x = 1350 - tw * 1500; y = 560 + math.sin(tw * 40) * -10; rr = 34; dd = ImageDraw.Draw(img); r = random.Random(2)
        for k in range(26):
            a = r.random() * 6.28 + tw * 30; l = rr * (0.4 + r.random() * 0.6); dd.line([(x, y), (x + math.cos(a) * l, y + math.sin(a) * l)], fill=(112, 84, 52), width=2)
    # the other disciples sneak glances at each other
    cap = [("...", lg[0] + 0.5), ("(30 seconds later)", lg[0] + 3.0), ("(a few minutes later)", lg[0] + 6.0)]
    for i, (s, t0) in enumerate(cap):
        a = tseg(t, t0, t0 + 0.4) * (1 - tseg(t, t0 + 2.4 if i < 2 else lg[1], t0 + 2.9 if i < 2 else lg[1] + 0.4))
        hlabel(640, 56, s, 38, (255, 240, 205), a)
    if t >= ye[0] - 0.1: bubble(img, 410, 300, "...yeah I guess.", 28, 1.0, tail=(420, 355))
    if t >= ye[0] + 1.6: bubble(img, 420, 238, "Weren't you finishing your speech or something?", 22, 1.0, tail=(420, 290))
    return img

def cosmic(img, t, a):
    if a <= 0.01: return img
    bgc = gradient((6, 4, 24), (40, 22, 70), "cosmos"); d = ImageDraw.Draw(bgc); r = random.Random(31)
    for i in range(200):
        x, y = r.random() * W, r.random() * H * 0.9; b = int(110 + 140 * abs(math.sin(t * 1.5 + i)))
        s = 1 + (i % 5 == 0); d.ellipse([x, y, x + s, y + s], fill=(b, b, min(255, b + 40)))
    lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay)
    for arm in range(3):                                           # a slow galaxy spiral
        for k in range(120):
            ang = arm * 2.094 + k * 0.09 + t * 0.12; rr = 8 + k * 2.6; x = 330 + math.cos(ang) * rr * 1.5; y = 230 + math.sin(ang) * rr * 0.55
            ld.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(int(140 + k), int(110 + k * 0.6), 255))
    softglow(bgc, lay, 8, 1.4); bgc.paste(ImageChops.add(bgc, lay.point(lambda v: int(v * 0.5))))
    return Image.blend(img, bgc, a)

def s_sigh(t, d, p):
    cl, inh, cs, ex = ev("sigh", "closes"), ev("sigh", "inhale"), ev("sigh", "cosmic"), ev("sigh", "exhale")
    sun = 0.62 + 0.15 * tseg(t, 0, d); cos = tseg(t, cs[0], cs[0] + 3.5)
    bg = cosmic(road_bg(sun), t, cos)                                       # the sky turns into the universe, behind everyone
    closed = t > cl[0] + 0.6
    img = world(t, sun, jes=dict(mouth="flat" if t < cs[0] else "o", eyes="closed" if closed else "open", glow=0.4 + 0.6 * tseg(t, inh[1], cs[0] + 2.0), L=(-0.2, -0.58), R=(0.2, -0.58)),
                od=dict(mouth="o", eyes="blank"), disc=dict(look=0.0, mouth="flat"), bg=bg)
    # the exhale: a long, fine golden stream from his mouth that drifts up into the stars
    b0 = cs[0] + 0.2; hx, hy = JX - 6, JY - OFF - 0.80 * JH
    if t > b0:
        lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay)
        for i in range(150):
            u = ((t - b0) * 0.2 + i / 150.0) % 1.0
            x = hx - 10 - u * 640 + math.sin(u * 12 + i) * 14; y = hy + 6 - u * 250 + math.sin(u * 8 + i * 0.5) * 18
            sz = 1.4 + 2.6 * (1 - u); k = 1 - u * 0.55; ld.ellipse([x - sz, y - sz, x + sz, y + sz], fill=(int(255 * k), int(224 * k), int((150 + 70 * u) * k)))
        softglow(img, lay, 8, 1.2); img.paste(ImageChops.add(img, lay.point(lambda v: int(v * 0.8))))
    # what the sigh carries: the weight of the universe, the fishermen, the love
    items = [("the weight of the universe", cs[0] + 1.0, "star"), ("teaching eternal truth to fishermen", cs[0] + 4.2, "fish"), ("the love of someone who refuses to give up", cs[0] + 7.6, "heart")]
    def _items(im):
        for s_, t0, kind in items:
            a = tseg(t, t0, t0 + 0.6) * (1 - tseg(t, t0 + 2.8, t0 + 3.5))
            if a <= 0: continue
            x = 640 + (t - t0) * 6; y = 230 - (t - t0) * 5; lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay); c = (int(255 * a), int(226 * a), int(160 * a))
            if kind == "star": ld.polygon([(x + math.cos(k * 0.628 - 1.57) * (36 if k % 2 == 0 else 15), y + math.sin(k * 0.628 - 1.57) * (36 if k % 2 == 0 else 15)) for k in range(10)], fill=c)
            elif kind == "fish":
                for j in range(3):
                    fx = x - 70 + j * 70 + math.sin(t * 3 + j) * 6; fy = y + (j % 2) * 24
                    ld.ellipse([fx - 22, fy - 9, fx + 14, fy + 9], fill=c); ld.polygon([(fx + 12, fy), (fx + 30, fy - 12), (fx + 30, fy + 12)], fill=c)
            else: ld.ellipse([x - 30, y - 24, x, y + 4], fill=c); ld.ellipse([x, y - 24, x + 30, y + 4], fill=c); ld.polygon([(x - 30, y - 8), (x + 30, y - 8), (x, y + 36)], fill=c)
            softglow(im, lay, 16, 1.5); im.paste(ImageChops.add(im, lay)); label(im, 640, 90 + (1 - a) * 6, s_, 30, (255, 244, 214), a)
    HUD(_items)
    fade = tseg(t, d - 2.6, d - 0.3)
    if fade > 0: img = Image.blend(img, Image.new("RGB", (W, H), (0, 0, 0)), fade)
    return img

SCENE_FN = {"title": s_title, "setup": s_setup, "speech": s_speech, "stare": s_stare, "bro": s_bro, "odds": s_odds, "drone": s_drone, "force": s_force, "silence": s_silence, "sigh": s_sigh}
# camera keyframes: (time or (tag, offset) or (tag@end, offset), cx, cy, zoom); duplicate times make a hard cut
CAMK = {"setup": [(0, 640, 380, 1.0), (("set@end", 0.0), 800, 430, 1.25)],
        "speech": [(0, 860, 430, 1.35), ("end", 900, 420, 1.55)],
        "stare": [(0, 780, 430, 1.05), (("patrick", 0.0), 780, 430, 1.05), (("patrick", 3.5), 480, 440, 1.4)],
        "bro": [(0, 430, 440, 1.5), (("brow", -0.25), 430, 440, 1.5), (("brow", -0.25), 880, 430, 1.8), ("end", 900, 430, 1.9)],
        "odds": [(0, 420, 430, 1.4), (("patience", -0.1), 420, 430, 1.4), (("patience", -0.1), 880, 430, 1.6), ("end", 900, 430, 1.72)],
        "drone": [(0, 880, 430, 1.5), (("blinks", -0.1), 880, 430, 1.5), (("blinks", -0.1), 430, 440, 1.6), ("end", 430, 440, 1.7)],
        "force": [(0, 860, 430, 1.35), (("pause", 0.0), 860, 430, 1.35), (("village", 0.0), 860, 430, 1.2), (("village", 6.0), 860, 430, 1.2), (("village", 6.6), 640, 440, 1.0), ("end", 560, 440, 1.5)],
        "silence": [(0, 640, 420, 1.0), (("long", 0.0), 640, 420, 1.0), (("long", 0.0), 430, 440, 1.45), ("end", 430, 440, 1.65)],
        "sigh": [(0, 880, 430, 1.7), (("exhale", 0.0), 880, 420, 2.0), ("end", 880, 420, 2.2)]}
CONT_IN = {"setup", "speech", "stare", "bro", "odds", "drone", "force", "silence", "sigh"}
CONT_OUT = {"setup", "speech", "stare", "bro", "odds", "drone", "force", "silence", "title"}


SPK = {"n": (255, 255, 255), "j": (255, 236, 190), "d": (190, 235, 200)}
NAMES = {"j": "JESUS", "d": "THE OVERWHELMED DISCIPLE"}
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
                           "-shortest", "-movflags", "+faststart", "jesus_and_the_overwhelmed_disciple.mp4"], stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for k, b in enumerate(pool.imap(frame, range(n), chunksize=6)):
            ff.stdin.write(b)
            if k % 240 == 0: print(k, "/", n, flush=True)
    ff.stdin.close(); ff.wait()
