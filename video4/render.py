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
OFF = 80
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
         armor=False, shield=False, spear=False, mouth="flat", brow=0.0, cut=None, rot=0.0, hood=False, eyes="open"):
    """frontal figure. returns world positions of hands and head."""
    yb = yb - OFF
    if cut is not None: cut = cut - OFF
    w = int(h * 1.8); hh = int(h * 1.14); lay = Image.new("RGBA", (w, hh), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    cx = w / 2; gy = hh - 4
    U = lambda ux, uy: (cx + ux * h, gy + uy * h)
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
    hx, hy = U(0, -0.88); r = h * 0.07
    if hair: d.ellipse([hx - r * 1.35, hy - r * 1.25, hx + r * 1.35, hy + r * 2.4], fill=hair)
    d.rectangle([hx - r * 0.35, hy + r * 0.6, hx + r * 0.35, hy + r * 1.25], fill=skin)
    fc = face if face else skin
    d.ellipse([hx - r, hy - r * 1.1, hx + r, hy + r * 1.1], fill=fc)
    if hood: d.pieslice([hx - r * 1.35, hy - r * 1.5, hx + r * 1.35, hy + r * 1.4], 180, 360, fill=shade)
    if beard: d.polygon([(hx - r * 0.95, hy + r * 0.1), (hx + r * 0.95, hy + r * 0.1), (hx + r * 0.6, hy + r * 1.6), (hx, hy + r * 1.95), (hx - r * 0.6, hy + r * 1.6)], fill=hair or (90, 60, 40))
    ey = hy - r * 0.12
    if eyes == "closed":
        for s in (-1, 1): d.arc([hx + s * r * 0.42 - 4, ey - 3, hx + s * r * 0.42 + 4, ey + 3], 200, 340, fill=(40, 30, 28), width=2)
    else:
        for s in (-1, 1): d.ellipse([hx + s * r * 0.42 - 2.5, ey - 2.5, hx + s * r * 0.42 + 2.5, ey + 2.5], fill=(36, 28, 26))
    for s in (-1, 1): d.line([(hx + s * r * 0.2, ey - r * (0.28 + brow * 0.2 * (1 if s == -1 else 1))), (hx + s * r * 0.7, ey - r * (0.28 - brow * 0.28 * 1))], fill=(50, 36, 30), width=2) if brow else None
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

# ---- crowd
def crowd_list():
    if "crowd" in _C: return _C["crowd"]
    rng = random.Random(21); L = []
    for yb, h, n, row in ((476, 112, 28, 0), (508, 128, 24, 1), (542, 146, 20, 2)):
        for i in range(n):
            x = (i + 0.5) / n * (W + 80) - 40 + rng.uniform(-18, 18)
            L.append(dict(x=x, yb=yb + rng.uniform(-4, 4), h=h * rng.uniform(0.92, 1.08), robe=rng.choice(ROBES), skin=rng.choice(SKIN), hood=rng.random() < 0.25, ph=rng.random() * 6.28, row=row, side=(-1 if x < 640 else 1), leave=rng.random()))
    for yb, h, xs in ((612, 176, (60, 150, 250)), (616, 176, (1030, 1130, 1230))):
        for x in xs: L.append(dict(x=x + rng.uniform(-14, 14), yb=yb + rng.uniform(-4, 4), h=h * rng.uniform(0.94, 1.06), robe=rng.choice(ROBES), skin=rng.choice(SKIN), hood=rng.random() < 0.2, ph=rng.random() * 6.28, row=3, side=(-1 if x < 640 else 1), leave=rng.random()))
    L.sort(key=lambda c: c["yb"]); _C["crowd"] = L; return L

def crowd(img, t, mode="calm", leaving=0.0, qmarks=0.0, mx=None):
    d = ImageDraw.Draw(img)
    for c in crowd_list():
        x, yb, h = c["x"], c["yb"], c["h"]
        if leaving > 0 and c["leave"] < 0.22:      # a few panic and follow the soldiers out
            x += c["side"] * 900 * ease(leaving - c["leave"] * 0.5) if leaving > c["leave"] * 0.5 else 0
            if x < -80 or x > W + 80: continue
        if c["row"] <= 2 and abs(x - 640) < 150: continue
        bob = 0.0; L = (-0.2, -0.42); R = (0.2, -0.42); mouth = "flat"
        if mode == "cheer": bob = abs(math.sin(t * 8 + c["ph"])) * 0.03 * h; L = (-0.22, -0.98 - 0.05 * math.sin(t * 9 + c["ph"])); R = (0.22, -0.98 - 0.05 * math.sin(t * 9 + c["ph"] + 1)); mouth = "shout"
        elif mode == "cower": L = (-0.08, -0.9); R = (0.08, -0.9); bob = -0.02 * h + 0.004 * h * math.sin(t * 30 + c["ph"]); mouth = "o"
        elif mode == "frozen": mouth = "o"
        elif mode == "laugh": bob = abs(math.sin(t * 7 + c["ph"])) * 0.02 * h; mouth = "laugh"
        else: bob = 0.005 * h * math.sin(t * 2 + c["ph"])
        cfig(img, x, yb - bob, h, c["robe"], c["skin"], hood=c["hood"], L=L, R=R, mouth=mouth)
        if qmarks > 0 and c["row"] < 3 and int(c["ph"] * 10) % 3 == 0:
            label(img, x, yb - OFF - h * 1.2 - 4, "?", int(h * 0.22), (60, 40, 30), min(1.0, qmarks), anchor="c")

# ---- food, table
def draw_item(img, kind, x, y, s=1.0, rot=0.0, a=1.0):
    if a <= 0 or s <= 0.02: return
    y = y - OFF
    sp = Image.new("RGBA", (120, 120), (0, 0, 0, 0)); d = ImageDraw.Draw(sp); cx, cy = 60, 60
    if kind == "loaf":
        d.ellipse([cx - 32, cy - 16, cx + 32, cy + 16], fill=(196, 134, 66), outline=(140, 90, 40), width=2)
        for k in (-14, 0, 14): d.line([(cx + k - 5, cy - 9), (cx + k + 5, cy + 4)], fill=(150, 98, 44), width=3)
        d.ellipse([cx - 22, cy - 13, cx + 6, cy - 5], fill=(222, 164, 90))
    elif kind == "jug":
        d.polygon([(cx - 12, cy - 30), (cx + 12, cy - 30), (cx + 22, cy + 6), (cx + 14, cy + 30), (cx - 14, cy + 30), (cx - 22, cy + 6)], fill=(176, 100, 60), outline=(120, 64, 34), width=2)
        d.rectangle([cx - 8, cy - 40, cx + 8, cy - 28], fill=(150, 84, 50)); d.ellipse([cx - 9, cy - 36, cx + 9, cy - 28], fill=(122, 28, 46))
        d.arc([cx + 14, cy - 18, cx + 36, cy + 8], 270, 90, fill=(120, 64, 34), width=4)
    elif kind == "basket":
        d.pieslice([cx - 34, cy - 22, cx + 34, cy + 26], 0, 180, fill=(170, 124, 70), outline=(110, 76, 40), width=2)
        for k in range(5): d.ellipse([cx - 28 + k * 13, cy - 26 + (k % 2) * 6, cx - 14 + k * 13, cy - 12 + (k % 2) * 6], fill=(102, 44, 96) if k % 2 else (150, 60, 70))
    elif kind == "dates":
        d.ellipse([cx - 36, cy - 10, cx + 36, cy + 20], fill=(226, 220, 206), outline=(160, 150, 130), width=2)
        for k in range(7): d.ellipse([cx - 28 + k * 9, cy - 8 + (k % 2) * 7, cx - 20 + k * 9, cy + 2 + (k % 2) * 7], fill=(110, 58, 28))
    elif kind == "fish":
        d.ellipse([cx - 46, cy - 14, cx + 46, cy + 24], fill=(228, 222, 208), outline=(160, 150, 130), width=2)
        d.ellipse([cx - 30, cy - 8, cx + 22, cy + 14], fill=(176, 120, 76)); d.polygon([(cx + 20, cy + 3), (cx + 38, cy - 8), (cx + 38, cy + 14)], fill=(176, 120, 76)); d.ellipse([cx - 22, cy - 2, cx - 16, cy + 4], fill=(30, 20, 16))
    s2 = sp
    if rot: s2 = sp.rotate(rot, resample=Image.BICUBIC)
    if s != 1.0: s2 = s2.resize((max(1, int(120 * s)), max(1, int(120 * s))), Image.BILINEAR)
    if a < 1: s2.putalpha(s2.split()[3].point(lambda v: int(v * a)))
    img.paste(s2, (int(x - s2.width / 2), int(y - s2.height / 2)), s2)

def food_layout():
    if "food" in _C: return _C["food"]
    items = []; rng = random.Random(5)
    for k, (kind, x) in enumerate([("loaf", 380), ("jug", 440), ("loaf", 510), ("fish", 580), ("basket", 700), ("dates", 770), ("jug", 840), ("loaf", 910), ("loaf", 330), ("basket", 960)]):
        items.append(dict(kind=kind, x=x, y=596, s=0.62, idx=k * 0.5, land=(x + rng.uniform(-200, 200), 680 + rng.uniform(-20, 30))))
    for side, cx0 in ((-1, 215), (1, 1065)):          # the mountains of bread
        k = 0
        for row in range(5):
            for i in range(6 - row):
                items.append(dict(kind="loaf", x=cx0 + (i - (5 - row) / 2) * 52, y=672 - row * 24, s=0.55, idx=2 + k * 0.35, land=(cx0 + rng.uniform(-260, 260), 690 + rng.uniform(-30, 30)))); k += 1
    _C["food"] = items; return items

def table_sprite():
    if "table" in _C: return _C["table"]
    sp = Image.new("RGBA", (760, 160), (0, 0, 0, 0)); d = ImageDraw.Draw(sp)
    d.polygon([(30, 20), (730, 20), (750, 40), (10, 40)], fill=(150, 104, 62)); d.rectangle([10, 40, 750, 150], fill=(238, 232, 218))
    for k in range(14): d.line([(30 + k * 52, 40), (24 + k * 52, 150)], fill=(214, 206, 188), width=3)
    d.rectangle([10, 40, 750, 52], fill=(190, 60, 54)); d.rectangle([10, 140, 750, 150], fill=(190, 60, 54))
    _C["table"] = sp; return sp

def table(img, t, a=1.0, u=0.0, food=1.0, spawn=None, back=0.0, flash=0.0):
    """u: scatter progress (0 = set, 1 = flipped & scattered). spawn: staggered pop-in time or None (all present)."""
    if a <= 0: return
    sp = table_sprite(); tcx, tcy = 640, 640 - OFF
    if u < 0.02 or u > 0.98 and False:
        img.paste(sp, (int(tcx - sp.width / 2), int(tcy - sp.height / 2)), sp)
    else:
        rot = -78 * ease(min(1, u * 1.3)); dy = 40 * ease(u); dx = 30 * ease(u)
        rs = sp.rotate(rot, resample=Image.BICUBIC, expand=True); img.paste(rs, (int(tcx - rs.width / 2 + dx), int(tcy - rs.height / 2 + dy)), rs)
    for it in food_layout():
        sc = it["s"] if spawn is None else it["s"] * clamp((spawn - it["idx"] * 0.12) / 0.5) * (1 + 0.25 * math.sin(clamp((spawn - it["idx"] * 0.12) / 0.5) * math.pi))
        if sc <= 0: continue
        x, y = it["x"], it["y"]
        if u > 0:
            uu = ease(u); x = lerp(x, it["land"][0], uu); y = lerp(y, it["land"][1], uu) - 150 * math.sin(uu * math.pi) * (0.5 + 0.5 * (it["idx"] % 2)); 
        draw_item(img, it["kind"], x, y, sc, rot=(u * 300 * (1 if it["idx"] % 2 else -1)) if u else 0)

def mosquitos(img, t, n):
    d = ImageDraw.Draw(img); r = random.Random(44)
    for i in range(int(n)):
        cx = r.random() * W; cy = 120 + r.random() * 260; ph = r.random() * 6.28
        x = cx + math.sin(t * 3 + ph) * 36 + math.sin(t * 9 + ph * 2) * 8; y = cy + math.cos(t * 2.4 + ph) * 28
        d.ellipse([x - 1.6, y - 1.6, x + 1.6, y + 1.6], fill=(40, 30, 30)); d.line([(x - 4, y - 3), (x, y - 1)], fill=(120, 110, 110), width=1); d.line([(x + 4, y - 3), (x, y - 1)], fill=(120, 110, 110), width=1)

def shock(img, cx, cy, u):
    if u <= 0 or u >= 1: return
    lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay); r = u * 1100
    ld.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(int(255 * (1 - u)), int(240 * (1 - u)), int(190 * (1 - u))), width=int(26 * (1 - u)) + 2)
    softglow(img, lay, 14, 1.0); img.paste(ImageChops.add(img, lay.point(lambda v: int(v * 0.5))))

def ghost_ripple(img, x, y, t, a=1.0):
    y = y - OFF
    lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay)
    for k in range(4):
        u = (t * 1.3 + k / 4) % 1; r = 40 + u * 120
        ld.ellipse([x - r * 0.6, y - r * 1.1, x + r * 0.6, y + r * 1.1], outline=(int(150 * (1 - u) * a), int(200 * (1 - u) * a), int(255 * (1 - u) * a)), width=3)
    softglow(img, lay, 12, 1.2)

# ---- the cast
JESUS = dict(robe=(244, 240, 230), skin=SKIN[0], hair=(100, 68, 46), beard=True, sash=(170, 120, 70))
def jesus_fig(img, x, yb, t, L=None, R=None, mouth="smile", alpha=1.0, cut=None, h=300, glowg=0.0):
    lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay); hy = yb - 0.88 * h
    ld.ellipse([x - 70, hy - 70, x + 70, hy + 70], fill=(120, 96, 50)); softglow(img, lay, 40, 0.9 + 0.4 * glowg)
    return cfig(img, x, yb, h, mouth=mouth, L=L, R=R, alpha=alpha, cut=cut, **JESUS)

def soldier(img, x, yb, h=250, face=None, mouth="flat", brow=0.5, L=None, R=None, alpha=1.0, rot=0.0, spear=False, helmet=True, shield=True):
    return cfig(img, x, yb, h, (150, 44, 40), SKIN[1], helmet=helmet, armor=True, shield=shield, spear=spear, face=face, mouth=mouth, brow=brow, L=L or (-0.22, -0.4), R=R or (0.2, -0.5), alpha=alpha, rot=rot, sash=(90, 60, 40))

DISC = [(430, (160, 120, 80), SKIN[2]), (540, (110, 130, 150), SKIN[1]), (760, (150, 100, 110), SKIN[0]), (870, (120, 140, 90), SKIN[3])]
def disciples(img, t, a=1.0, laugh=0.0, ghost=0.0, shift=None):
    for i, (x, robe, skin) in enumerate(DISC):
        b = abs(math.sin(t * 6 + i * 1.7)) * 0.025 * 240 * laugh
        ox = shift[i] if shift else 0
        cfig(img, x + ox, 700 - b, 240, robe, skin, hair=(70, 50, 36) if i % 2 == 0 else None, beard=(i % 2 == 0), mouth="laugh" if laugh > 0.3 else "smile", cut=604, alpha=a * (1 - 0.5 * ghost), hood=(i == 3))

def bubble(img, x, y, text, size=22, a=1.0, tail=None, col=(252, 250, 244)):
    if a <= 0: return
    y = y - OFF + 20
    if tail: tail = (tail[0], tail[1] - OFF + 20)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); f = F(size)
    tw = d.textlength(text, font=f); x0, y0, x1, y1 = x - tw / 2 - 16, y - 8, x + tw / 2 + 16, y + size + 14
    d.rounded_rectangle([x0, y0, x1, y1], 16, fill=col + (int(240 * a),), outline=(70, 50, 36, int(255 * a)), width=2)
    if tail: d.polygon([(x - 9, y1 - 2), (x + 9, y1 - 2), tail], fill=col + (int(240 * a),))
    d.text((x - tw / 2, y), text, font=f, fill=(46, 36, 30, int(255 * a))); img.paste(lay, (0, 0), lay)

def fish_story(img, x, y, t, a=1.0):
    """a little thought-cloud: a boat, a fish, and Peter falling in again."""
    if a <= 0: return
    lay = Image.new("RGBA", (360, 220), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.ellipse([10, 10, 350, 190], fill=(250, 248, 240, 245), outline=(70, 50, 36, 255), width=3)
    d.rectangle([20, 120, 340, 180], fill=(110, 170, 220, 255)); d.ellipse([10, 100, 350, 190], outline=(250, 248, 240, 255), width=14)
    for k in range(6): d.arc([30 + k * 52, 118 + (k % 2) * 6, 76 + k * 52, 134 + (k % 2) * 6], 180, 360, fill=(240, 250, 255, 255), width=2)
    sway = math.sin(t * 2) * 4
    d.polygon([(100, 118 + sway), (230, 118 + sway), (214, 146 + sway), (116, 146 + sway)], fill=(150, 100, 60, 255)); d.line([(165, 118 + sway), (165, 56 + sway)], fill=(110, 70, 40, 255), width=4); d.polygon([(165, 58 + sway), (212, 100 + sway), (165, 100 + sway)], fill=(240, 232, 214, 255))
    u = (t * 0.7) % 1; px = 250 + 30 * u; py = 70 + 90 * ease(u) - 20 * math.sin(u * math.pi); ang = u * 200
    d.ellipse([px - 7, py - 7, px + 7, py + 7], fill=(226, 180, 140, 255)); d.line([(px, py + 6), (px + 6 * math.cos(math.radians(ang)), py + 22)], fill=(130, 90, 70, 255), width=6)
    if u > 0.8: d.ellipse([px - 22, 146, px + 22, 166], outline=(250, 255, 255, 255), width=3)
    d.text((250, 36), "Peter", font=F(14, bold=True), fill=(60, 40, 30, 255))
    if a < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * a)))
    img.paste(lay, (int(x - 180), int(y - 110)), lay)

# ---- scene drawing
def base_scene(t):
    img = square().copy(); return img

SOLD_HOME = [(330, 640, 275), (170, 650, 250), (1110, 650, 250), (1215, 646, 245)]
def sc_title(t, d, p):
    img = base_scene(t); dr = ImageDraw.Draw(img)
    crowd(img, t, "calm")
    jesus_fig(img, 640, 640, t, L=(-0.18, -0.42), R=(0.2, -0.45), glowg=0.8); 
    img = Image.blend(img, Image.new("RGB", (W, H), (20, 14, 10)), 0.5)
    a = tseg(t, 0.4, 1.4) * (1 - tseg(t, d - 1.0, d - 0.2))
    title(img, "JESUS AND THE GAUNTLET", "that everyone wanted to use wrong", a, y=250, size=50)
    return img

def sc_square(t, d, p):
    img = base_scene(t)
    sq1, sq2 = ev("square", "sq1"), ev("square", "sq2")
    tag_t = [("SOLDIERS", 0.20, 250, 380), ("ZEALOTS", 0.34, 420, 340), ("TOWNSPEOPLE", 0.48, 780, 360), ("REVOLUTIONARIES", 0.62, 960, 400)]
    crowd(img, t, "calm")
    for x, yb, h in SOLD_HOME[:4]:
        soldier(img, x, yb, h, spear=(x < 640), brow=0.3)
    pos = jesus_fig(img, 640, 640, t, L=(-0.2, -0.42), R=(0.26, -0.58), glowg=1.0)
    gauntlet(img, pos["R"], t, 1.2, 1.0)
    for lbl, th, x, y in tag_t:
        u = (t - (sq1[0] + (sq1[1] - sq1[0]) * th))
        a = tseg(u, 0, 0.4) * (1 - tseg(u, 2.2, 3.0))
        label(img, x, y - 70 + (1 - a) * 10, lbl, 24, (255, 244, 220), a)
    for k, (s, th) in enumerate([("CARNAGE", 0.0), ("JUDGMENT", 1.7), ("THE SNAP", 3.4)]):
        u = t - sq2[0] - th; a = tseg(u, 0, 0.3) * (1 - tseg(u, 1.4, 1.7)) if k < 2 else tseg(u, 0, 0.3)
        label(img, 640, 130, s, 56, (255, 236, 200), a)
    return img

def hand_up(t, a): return (0.2 + 0.08 * a, -0.42 - 0.62 * a)

def sc_demand(t, d, p):
    dem, roar, hum = ev("demand", "dem"), ev("demand", "roar"), ev("demand", "hum")
    img = base_scene(t)
    cheer = dem[0] + 2.0 < t < roar[1] + 0.2
    brace = t > hum[0] + 2.6
    crowd(img, t, "cower" if brace else ("cheer" if cheer else "calm"))
    sp = dem[0] < t < dem[1]
    # lead soldier on the left shouting, others cheering
    soldier(img, 360, 640, 280, mouth="shout" if sp else "flat", brow=1.0, L=(-0.3, -0.8) if sp else None, R=(0.32, -0.84) if sp else None, spear=False)
    for i, (x, yb, h) in enumerate(SOLD_HOME[1:]):
        soldier(img, x, yb, h, mouth="shout" if cheer else "flat", brow=0.6, R=(0.25, -0.9) if cheer else None, spear=True)
    up = tseg(t, hum[0] + 1.4, hum[0] + 3.0)
    pos = jesus_fig(img, 640, 640, t, L=(-0.2, -0.42), R=hand_up(t, up), glowg=1.0 + up)
    gauntlet(img, pos["R"], t, 1.3, 1.0 + 1.5 * up)
    if sp:
        words = ["JUSTICE!", "END THE WICKED!", "END THE TRAITORS!", "END THE SINNERS!", "END THE ONES WHO OPPOSE US!"]
        k = min(len(words) - 1, int((t - dem[0]) / (dem[1] - dem[0]) * len(words)))
        label(img, 360, 340 + (k % 2) * 10, words[k], 34, (255, 240, 210), 1.0)
    if cheer: label(img, 640, 120, "THE CROWD ROARS", 40, (255, 232, 190), tseg(t, roar[0], roar[0] + 0.3) * (1 - tseg(t, roar[1] - 0.2, roar[1] + 0.2)))
    if brace: label(img, 640, 120, "BRACE FOR ANNIHILATION", 40, (255, 200, 170), tseg(t, hum[0] + 2.6, hum[0] + 3.2))
    img = Image.blend(img, Image.new("RGB", (W, H), (30, 14, 20)), 0.18 * up)
    return img

def feast_state(t):
    pop = ev("snap", "pop"); n = ev("snap", "feast")
    return clamp((t - (pop[0] + 0.3)) / 2.0)

def sc_snap(t, d, p):
    pop = ev("snap", "pop"); feast = ev("snap", "feast"); dn = ev("snap", "dinner")
    tp = pop[0] + 0.3; img = base_scene(t); after = t > tp
    crowd(img, t, "frozen" if after else "cower")
    for i, (x, yb, h) in enumerate(SOLD_HOME): soldier(img, x, yb, h, mouth="o" if after else "flat", brow=0.2, spear=(i % 2 == 0))
    sp = (t - tp) / 2.4 if after else None
    if after: disciples(img, t, a=tseg(t, tp + 0.5, tp + 1.5)); table(img, t, 1.0, 0.0, spawn=sp * 6 if sp is not None else 0)
    raised = 1.0 - tseg(t, tp, tp + 0.5)
    pos = jesus_fig(img, 640, 640 if not after else 640, t, L=(-0.2, -0.42), R=hand_up(t, raised), mouth="smile", glowg=1.0 + raised) if not (after and t > tp + 1.4) else jesus_fig(img, 640, 700, t, L=(-0.18, -0.2), R=(0.18, -0.2), mouth="smile", cut=604)
    if raised > 0.05: gauntlet(img, pos["R"], t, 1.3, 0.6 + 2.0 * raised)
    shock(img, 640, 420, (t - tp) / 1.0 if after else 0)
    if after and t < tp + 0.25: img = Image.blend(img, Image.new("RGB", (W, H), (255, 248, 220)), 0.7 * (1 - (t - tp) / 0.25))
    mq = 40 if not after else 40 - 16 * tseg(t, feast[0] + 8.0, feast[0] + 10.0) 
    mosquitos(img, t, mq)
    if t > feast[0] + 8.5: label(img, 640, 118, "MOSQUITOES  −40%", 44, (255, 240, 200), tseg(t, feast[0] + 8.5, feast[0] + 9.0) * (1 - tseg(t, feast[1] - 0.2, feast[1] + 0.3)))
    if t > dn[0]: bubble(img, 640, 330, "Dinner is served.", 30, tseg(t, dn[0], dn[0] + 0.3), tail=(640, 410))
    return img

def sc_stunned(t, d, p):
    fr, wh, wo, st = ev("stunned", "frozen"), ev("stunned", "what"), ev("stunned", "worms"), ev("stunned", "story")
    img = base_scene(t)
    crowd(img, t, "frozen", qmarks=tseg(t, fr[0], fr[0] + 0.6))
    for i, (x, yb, h) in enumerate(SOLD_HOME): soldier(img, x, yb, h, mouth="o", brow=0.1, spear=(i % 2 == 0))
    laugh = tseg(t, st[0] + 1.5, st[0] + 2.5)
    disciples(img, t, laugh=laugh)
    table(img, t, 1.0)
    gest = math.sin(t * 3) * 0.06
    pos = jesus_fig(img, 640, 700, t, L=(-0.2 - gest, -0.34 + abs(gest)), R=(0.2 + gest, -0.34), mouth="laugh" if laugh > 0.5 else "smile", cut=604)
    if wh[0] < t < wh[1] + 0.8: bubble(img, 1010, 330, "Wait... what?", 26, 1.0, tail=(1040, 400))
    if wo[0] + 0.5 < t < wo[1] + 0.3: label(img, 640, 118, "PARASITIC WORMS: REDUCED", 38, (230, 255, 210), tseg(t, wo[0] + 0.5, wo[0] + 0.9) * (1 - tseg(t, wo[1] - 0.2, wo[1] + 0.3)))
    if t > st[0] + 0.8: fish_story(img, 640, 250, t, tseg(t, st[0] + 0.8, st[0] + 1.6))
    return img

def lead_pos(t, sc):
    return 330

def sc_rage(t, d, p):
    pu, ab, mg, tk = ev("rage", "purple"), ev("rage", "abom"), ev("rage", "myguy"), ev("rage", "taking")
    img = base_scene(t)
    purple = tseg(t, pu[0], pu[1])
    crowd(img, t, "frozen")
    angry = lambda lo, hi: lo < t < hi
    lead_x = lerp(330, 420, tseg(t, ab[0], ab[1])) + (math.sin(t * 40) * 3 if purple > 0.8 else 0)
    face = mix(SKIN[1], (150, 60, 160), purple)
    for i, (x, yb, h) in enumerate(SOLD_HOME[1:]): soldier(img, x, yb, h, mouth="frown", brow=0.8, spear=(i % 2 == 0))
    disciples(img, t, laugh=0.6 if mg[0] - 0.3 < t < mg[1] else 0.0)
    table(img, t, 1.0)
    butter = math.sin(t * 5) * 0.05
    pos = jesus_fig(img, 640, 700, t, L=(-0.2, -0.34), R=(0.2 + butter, -0.34 - abs(butter)), mouth="smile", cut=604)
    shout = angry(ab[0], ab[1]) or angry(tk[0], tk[1])
    soldier(img, lead_x, 654, 285, face=face, mouth="shout" if shout else "frown", brow=1.0 if purple > 0.3 else 0.4, L=(-0.34, -0.74) if shout else None, R=(0.34, -0.78) if shout else None)
    if purple > 0.6 and t < ab[0] + 1.0: label(img, lead_x, 300, "!!!", 52, (255, 150, 180), purple)
    if mg[0] < t < mg[1] + 0.4: bubble(img, 800, 330, "My guy... I'm literally trying to feed you.", 24, 1.0, tail=(780, 420))
    return img

def sc_flip(t, d, p):
    fn, br, ap, ph = ev("flip", "flipn"), ev("flip", "bro"), ev("flip", "appr"), ev("flip", "phase")
    img = base_scene(t)
    tf = fn[0] + 3.0
    u = tseg(t, tf, tf + 1.2) * (1 - tseg(t, ph[0] + 4.5, ph[0] + 6.5))
    standing = t > br[0] - 0.4 and t < ph[0] + 4.0
    mist = tseg(t, ph[0] + 1.2, ph[0] + 2.2) * (1 - tseg(t, ph[0] + 3.8, ph[0] + 4.8))
    crowd(img, t, "frozen")
    # soldiers stomp to the table, then guards grab
    approach = tseg(t, fn[0] + 0.3, tf)
    sx = [lerp(330, 460, approach), lerp(170, 330, approach), lerp(1110, 850, approach), lerp(1215, 940, approach)]
    grab = tseg(t, ap[1] - 0.2, ph[0] + 1.0) * (1 - tseg(t, ph[0] + 3.8, ph[0] + 5.0))
    disciples(img, t, laugh=0.0, shift=[(-30 * u) if i < 2 else (30 * u) for i in range(4)], a=1.0)
    table(img, t, 1.0, u=u)
    ys = 650 + 0
    if standing:
        jx = 640; pos = jesus_fig(img, jx, 640 + 60 * (1 - tseg(t, br[0] - 0.4, br[0] + 0.4)), t, L=(-0.2, -0.38), R=(0.2, -0.3 if mist < 0.1 else -0.5), mouth="flat", alpha=1 - 0.55 * mist)
        if mist > 0.05: ghost_ripple(img, 640, 480, t, mist)
    else:
        pos = jesus_fig(img, 640, 700, t, L=(-0.2, -0.34), R=(0.2, -0.34), mouth="smile", cut=604)
    for i, (x, yb, h) in enumerate(SOLD_HOME):
        arms_g = grab > 0.1 and i in (0, 3)
        L = (-0.12, -0.34) if (arms_g and i == 0) else None; R = (0.12 * (1 if i == 3 else 1), -0.4) if arms_g else None
        if i == 0 and grab > 0.1: L, R = (0.1, -0.5), (0.25, -0.52)
        if i == 3 and grab > 0.1: sx[i] = lerp(sx[i], 760, grab)
        scream = fn[0] + 3.0 < t < br[0] - 0.3
        soldier(img, sx[i] if i != 0 else lerp(sx[0], 540, grab), yb, h, mouth="shout" if scream else ("o" if mist > 0.2 else "frown"), brow=1.0, L=L, R=R, spear=False)
    if t > ap[0]: bubble(img, 330, 300, "APPREHEND HIM!", 30, tseg(t, ap[0], ap[0] + 0.2) * (1 - tseg(t, ap[1] + 0.3, ap[1] + 0.8)), tail=(380, 380))
    if t > br[0] and t < br[1] + 0.5: bubble(img, 760, 250, "I have the Infinity Gauntlet.", 24, 1.0, tail=(700, 340))
    return img

def sc_violence(t, d, p):
    pn, ru, de, ha = ev("violence", "punch"), ev("violence", "rule"), ev("violence", "demonic"), ev("violence", "harmless")
    img = base_scene(t); crowd(img, t, "frozen")
    fall = tseg(t, pn[0] + 3.2, pn[0] + 4.4)
    pun = tseg(t, pn[0] + 1.8, pn[0] + 2.8) * (1 - fall)
    lunge = tseg(t, pn[0] + 6.0, pn[0] + 7.4) * (1 - tseg(t, pn[0] + 8.4, pn[0] + 9.6))
    disciples(img, t, laugh=0.0, ghost=lunge * 0.8)
    table(img, t, 1.0)
    ghost = max(pun, 0.0) * 0.8 + 0.0
    pos = jesus_fig(img, 640, 700, t, L=(-0.2, -0.34), R=(0.2, -0.34), mouth="smile" if t < ru[0] else "flat", cut=604, alpha=1 - 0.55 * max(ghost, 0))
    if ghost > 0.05: ghost_ripple(img, 640, 500, t, ghost)
    # the puncher (S1 on the left) throws a fist through Jesus, then tumbles into the bread pile
    px = lerp(330, 480, tseg(t, pn[0] + 0.5, pn[0] + 1.8)); 
    if fall > 0: px = lerp(480, 590, fall)
    soldier(img, px, 654 - 20 * math.sin(fall * math.pi), 255, mouth="shout" if pun > 0.1 else "frown", brow=1.0, R=(0.15 + 0.7 * pun, -0.6 + 0.08 * pun), L=(-0.22, -0.4), rot=(-80 * fall))
    if pun > 0.5 and fall < 0.2:
        lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay); ld.ellipse([640 - 22, 480 - 22, 640 + 22, 480 + 22], fill=(120, 180, 255)); softglow(img, lay, 18, 1.4)
    # the lunger (S3 on the right) reaches for a disciple, hand passes through like smoke
    lx = lerp(1050, 930, tseg(t, pn[0] + 5.8, pn[0] + 7.0))
    soldier(img, lx, 650, 250, mouth="shout" if lunge > 0.1 else "frown", brow=1.0, L=(-0.5 * lunge - 0.22, -0.55), R=(0.2, -0.4), spear=False)
    if lunge > 0.3: ghost_ripple(img, 870, 540, t + 1, lunge)
    others = [(190, 650, 255), (1215, 646, 240)]
    for i, (x, yb, h) in enumerate(others): soldier(img, x, yb, h, mouth="frown", brow=0.8, spear=(i == 0))
    # the rule
    if ru[0] < t < ha[1] + 0.5:
        a = tseg(t, ru[0] + 1.2, ru[0] + 1.8) * (1 - tseg(t, de[0] - 0.2, de[0] + 0.3))
        rows = [("you CAN", "yell · complain · express your feelings", (170, 255, 190)), ("you CANNOT", "touch anyone without consent", (255, 190, 170))]
        for k, (h1, h2, c) in enumerate(rows):
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
            ld.rounded_rectangle([250, 80 + k * 72, 1030, 140 + k * 72], 14, fill=(20, 24, 40, int(200 * a))); img.paste(lay, (0, 0), lay)
            label(img, 280, 96 + k * 72, h1, 28, c, a, anchor="l"); label(img, 500, 100 + k * 72, h2, 24, (250, 250, 250), a, anchor="l")
    if de[0] < t < de[1] + 0.3: bubble(img, 330, 300, "DEMONIC! DARK MAGIC!", 30, 1.0, tail=(360, 380))
    if ha[0] < t: bubble(img, 640, 330, "No. I'm making you harmless.", 28, tseg(t, ha[0], ha[0] + 0.3), tail=(640, 410))
    return img

def sc_leave(t, d, p):
    st, sm, s2, an = ev("leave", "storm"), ev("leave", "someday"), ev("leave", "snap2"), ev("leave", "anyway")
    img = base_scene(t)
    go = tseg(t, st[0] + 2.0, st[1] - 0.8)
    crowd(img, t, "frozen" if t < st[1] else ("laugh" if t > s2[0] + 6 else "calm"), leaving=go)
    reset = tseg(t, s2[0] + 0.4, s2[0] + 1.2) 
    disciples(img, t, laugh=tseg(t, s2[0] + 5.5, s2[0] + 6.5))
    table(img, t, 1.0, u=(0.0 if t > s2[0] + 0.4 else 0.0))
    # soldiers storm off the stage
    for i, (x, yb, h) in enumerate(SOLD_HOME):
        tx = -200 if x < 640 else W + 200; xx = lerp(x, tx, go) + (math.sin(t * 6 + i) * 3 if 0 < go < 1 else 0)
        if -150 < xx < W + 150: soldier(img, xx, yb, h, mouth="shout" if go < 1 else "flat", brow=1.0, L=(-0.3, -0.7) if go < 1 else None, spear=(i % 2 == 0))
    snap2 = max(0.0, 1 - abs(t - (s2[0] + 0.4)) / 0.25)
    mouth = "smile"; gl = tseg(t, s2[0] - 0.3, s2[0] + 0.4) * (1 - tseg(t, s2[0] + 0.6, s2[0] + 1.4))
    laugh = tseg(t, s2[0] + 5.5, s2[0] + 6.5)
    gest = math.sin(t * 3) * 0.06 * tseg(t, an[0] - 0.6, an[0])
    pos = jesus_fig(img, 640, 700, t, L=(-0.2 - gest, -0.34), R=(0.2 + 0.1 * gl + gest, -0.34 - 0.5 * gl), mouth="laugh" if laugh > 0.5 else "smile", cut=604, glowg=gl)
    if gl > 0.1: gauntlet(img, pos["R"], t, 1.0, 1.5 * gl)
    shock(img, 640, 480, (t - (s2[0] + 0.4)) / 0.9 if t > s2[0] + 0.4 else 0)
    if snap2 > 0: img = Image.blend(img, Image.new("RGB", (W, H), (255, 246, 210)), 0.5 * snap2)
    if t > sm[0] and t < sm[1] + 0.4: bubble(img, 640, 300, "Maybe someday they'll understand.", 26, tseg(t, sm[0], sm[0] + 0.4), tail=(640, 380), col=(240, 244, 252))
    if t > an[0]: fish_story(img, 640, 240, t, tseg(t, an[0], an[0] + 0.6))
    return img

def icon(img, kind, cx, cy, t, s=1.0):
    d = ImageDraw.Draw(img)
    if kind == "gauntlet": gauntlet(img, (cx, cy), t, 1.4 * s, 1.0)
    elif kind == "jesus": cfig(img, cx, cy + 56 * s, 120 * s, mouth="smile", **JESUS)
    elif kind == "soldier": soldier(img, cx, cy + 58 * s, 118 * s, mouth="frown", brow=0.8, spear=False)
    elif kind == "phase":
        for k in range(3): d.ellipse([cx - 28 + k * 12, cy - 28 + k * 4, cx + 28 + k * 12, cy + 28 + k * 4], outline=(130 + k * 40, 190, 255), width=3)
        d.line([(cx - 44, cy), (cx + 44, cy)], fill=(255, 255, 255), width=4); d.polygon([(cx + 44, cy), (cx + 30, cy - 9), (cx + 30, cy + 9)], fill=(255, 255, 255))
    elif kind == "feast":
        draw_item(img, "loaf", cx - 22, cy + 12, 0.8); draw_item(img, "jug", cx + 26, cy + 4, 0.7); draw_item(img, "basket", cx, cy - 14, 0.7)

def sc_metaphor(t, d, p):
    img = gradient((16, 18, 34), (40, 34, 56), "metabg"); dr = ImageDraw.Draw(img)
    rows = [("gauntlet", "THE GAUNTLET", "= technology", "a tool that prevents non-consensual harm without inflicting harm", "m1"),
            ("jesus", "JESUS", "= the pro-human, non-violent framework", "a presence that dissolves violence instead of countering it", "m2"),
            ("soldier", "THE SOLDIERS", "= people who think power only matters when it can hurt", "and who panic when they meet a power that refuses to", "m3"),
            ("phase", "THE PHASING", "= consent-based interaction", "talk, express, disagree — but no touching without consent", "m4"),
            ("feast", "THE FEAST", "= the kingdom of heaven as abundance, not domination", "power used to nourish, not to destroy", "m5")]
    for i, (ic, h1, h2, h3, tag) in enumerate(rows):
        a0 = ev("metaphor", tag)[0]; a = tseg(t, a0 - 0.2, a0 + 0.5); y = 112 + i * 100
        if a <= 0: continue
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        ld.rounded_rectangle([60, y - 42, W - 60, y + 50], 16, fill=(255, 255, 255, int(24 * a)), outline=(210, 180, 120, int(120 * a)), width=2); img.paste(lay, (0, 0), lay)
        tmp = Image.new("RGB", (W, H), (0, 0, 0)); tmp.paste(img); icon(tmp, ic, 140, y + 6, t, 0.8); img = Image.blend(img, tmp, a)
        label(img, 230, y - 40, h1, 20, (230, 190, 110), a, anchor="l"); label(img, 230, y - 12, h2, 27, (255, 250, 240), a, anchor="l"); label(img, 230, y + 24, h3, 19, (190, 200, 225), a, anchor="l")
    title(img, "THE METAPHOR", a=1.0, y=26, size=28)
    return img

def sc_end(t, d, p):
    e1, e2, fin = ev("end", "e1"), ev("end", "e2"), ev("end", "fin")
    dusk = tseg(t, 0, d)
    img = base_scene(t)
    img = Image.blend(img, Image.new("RGB", (W, H), (255, 170, 90)), 0.25 + 0.15 * dusk)
    crowd(img, t, "laugh" if t > e2[0] else "calm")
    disciples(img, t, laugh=0.7)
    table(img, t, 1.0)
    # one soldier comes back, takes off his helmet and sits down at the table
    back = tseg(t, e2[0] + 2.8, e2[0] + 6.5); seated = tseg(t, e2[0] + 7.0, e2[0] + 8.0)
    if back > 0:
        sx = lerp(1330, 960, back)
        if seated < 1: soldier(img, sx, 650 + 50 * seated, 250, mouth="smile" if back > 0.9 else "flat", brow=0.0, helmet=(back < 0.6), shield=False, L=(-0.2, -0.4) if back < 0.9 else (-0.1, -0.5), alpha=1.0, spear=False)
        else: soldier(img, 960, 700, 250, mouth="smile", brow=0.0, helmet=False, shield=False, spear=False)
    gest = math.sin(t * 3) * 0.06
    pos = jesus_fig(img, 640, 700, t, L=(-0.2 - gest, -0.34), R=(0.2 + gest, -0.34), mouth="laugh" if t > e2[0] else "smile", cut=604, glowg=0.5)
    if back > 0.8: draw_item(img, "loaf", 880 + 60 * tseg(t, e2[0] + 6.6, e2[0] + 7.4), 590, 0.6)
    particles(img, t, 40, 8, (255, 230, 150), speed=20, size=2.5)
    a = tseg(t, fin[0] - 0.4, fin[0] + 0.8)
    label(img, 640, 100, "transformation, not erasure", 44, (255, 246, 226), a)
    return img

SCENE_FN = {"title": sc_title, "square": sc_square, "demand": sc_demand, "snap": sc_snap, "stunned": sc_stunned, "rage": sc_rage,
            "flip": sc_flip, "violence": sc_violence, "leave": sc_leave, "metaphor": sc_metaphor, "end": sc_end}
CAM = {"square": ((640, 380, 1.0), (640, 440, 1.28)), "demand": ((520, 430, 1.1), (640, 430, 1.12)), "snap": ((640, 430, 1.15), (640, 450, 1.0)),
       "stunned": ((640, 420, 1.0), (640, 440, 1.1)), "rage": ((560, 440, 1.1), (560, 450, 1.18)), "flip": ((640, 400, 1.0), (640, 420, 1.06)),
       "violence": ((640, 420, 1.05), (640, 430, 1.12)), "leave": ((640, 400, 1.0), (640, 440, 1.1)), "end": ((640, 440, 1.2), (640, 400, 1.0))}
CONT_IN = {"demand", "snap", "stunned", "rage", "flip", "violence", "leave"}
CONT_OUT = {"square", "demand", "snap", "stunned", "rage", "flip", "violence"}


SPK = {"n": (255, 255, 255), "j": (255, 236, 190), "jq": (255, 236, 190), "s": (255, 170, 150), "t": (200, 225, 255)}
NAMES = {"j": "JESUS", "jq": "JESUS", "s": "LEAD SOLDIER", "t": "TOWNSPERSON"}
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
                           "-shortest", "-movflags", "+faststart", "jesus_and_the_gauntlet.mp4"], stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for k, b in enumerate(pool.imap(frame, range(n), chunksize=6)):
            ff.stdin.write(b)
            if k % 240 == 0: print(k, "/", n, flush=True)
    ff.stdin.close(); ff.wait()
