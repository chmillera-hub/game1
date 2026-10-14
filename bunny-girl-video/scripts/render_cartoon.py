"""Render the cartoon version of "Bunny Girl and Wolf Dog" (1080x1920, 30 fps).

Every frame is drawn from scratch with vector shapes (scripts/toon.py and
scripts/toon_world.py); the characters act out the narration, timed to the
spoken words in build/timeline.json. Read-along captions sit in a box at the
top (clear of the app buttons at the bottom/right on Reels/TikTok/Shorts).

Usage:
  python render_cartoon.py                   # full render -> build/cartoon_noaudio.mp4
  python render_cartoon.py --preview 0 16 45 # still frames -> build/cpreview/
"""
import argparse
import math
import os
import re
import subprocess
import sys
from multiprocessing import Pool

import cv2
import numpy as np
import skia
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import timeline  # noqa: E402
import toon  # noqa: E402
import toon_world as tw  # noqa: E402
from toon import OUT, WHITE, Fade, Xf  # noqa: E402

BUILD = os.path.join(ROOT, "build")
FONTS = os.path.join(ROOT, "fonts")
W, H, FPS = 1080, 1920, 30
BEAT = 60 / 104
BOX = (36, 196, 1044, 492)
CAP_TOP, CAP_BOT = 212, 476
PLUM = (63, 45, 99)

GS, WS, MS = 1.12, 1.06, 1.08          # girl, wolf, mom scales
DS = dict(Cosmo=1.38, Pettie=1.32, Luna=1.42, Mooky=1.2, Buddy=1.32)
DOGS = ["Cosmo", "Pettie", "Luna", "Mooky", "Buddy"]
TAG_COL = dict(Cosmo=(86, 170, 240), Pettie=(240, 110, 160), Luna=(150, 110, 220), Mooky=(235, 100, 90), Buddy=(80, 180, 110))
Y_MAIN, Y_BACK, Y_DOGS = 1590, 1500, 1730


# ------------------------------------------------------------------ easing
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def seg(t, a, b):
    return clamp((t - a) / (b - a)) if b > a else float(t >= b)


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_in(x):
    x = clamp(x)
    return x * x


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 2


def back(x, k=1.8):
    x = clamp(x) - 1
    return 1 + x * x * ((k + 1) * x + k)


def elastic(x):
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    return 1 + 2 ** (-9 * x) * math.sin((x * 6 - 0.75) * (2 * math.pi) / 3)


def lerp(a, b, k):
    return a + (b - a) * k


def kf(t, keys, fn=ease):
    """Piecewise interpolation through (time, value) keys."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t < t1:
            k = fn((t - t0) / (t1 - t0)) if t1 > t0 else 1.0
            if isinstance(v0, tuple):
                return tuple(lerp(a, b, k) for a, b in zip(v0, v1))
            return lerp(v0, v1, k)
    return keys[-1][1]


def bump(t, t0, dur):
    return math.sin(math.pi * seg(t, t0, t0 + dur))


def blink(t, seed=0.0):
    period = 2.9 + (seed * 0.37) % 1.3
    return 0.08 if (t + seed * 1.13) % period < 0.12 else 1.0


def beat_bounce(t, amp=1.0):
    return amp * abs(math.sin(math.pi * ((t / BEAT) % 1.0)))


def hop(t, t0, dur, h):
    """Height above ground and squash for one hop starting at t0."""
    k = (t - t0) / dur
    if 0 <= k <= 1:
        return h * math.sin(math.pi * k), (1 - 0.06 * math.sin(math.pi * k), 1 + 0.08 * math.sin(math.pi * k))
    if 1 < k <= 1.35:
        q = math.sin(math.pi * (k - 1) / 0.35)
        return 0.0, (1 + 0.08 * q, 1 - 0.08 * q)
    return 0.0, (1.0, 1.0)


def hops(t, times, dur, h):
    up, sq = 0.0, (1.0, 1.0)
    for t0 in times:
        u, s = hop(t, t0, dur, h)
        if u > up or s != (1.0, 1.0):
            up, sq = max(up, u), s
    return up, sq


def wave(t, t0, t1, base=128, amp=22, speed=12):
    """Arm raise for a wave between t0..t1 (eases in and out)."""
    w = ease(clamp(min(seg(t, t0, t0 + 0.25), 1 - seg(t, t1 - 0.25, t1))))
    return lerp(18, base + amp * math.sin((t - t0) * speed), w), w


def walk_front(phase, amt=1.0):
    s = math.sin(phase)
    return dict(leg_l=9 * s * amt, leg_r=-9 * s * amt, lift_l=max(0, s) * 20 * amt, lift_r=max(0, -s) * 20 * amt,
                arm_l=(18 - 16 * s * amt, 8), arm_r=(18 + 16 * s * amt, 8)), abs(s) * 10 * amt


def walk_wolf(phase, amt=1.0):
    s = math.sin(phase)
    return dict(lift_b=max(0, s) * 26 * amt, lift_f=max(0, -s) * 26 * amt, leg_b=8 * s * amt, leg_f=-8 * s * amt), abs(s) * 9 * amt


def mover(t, keys, step=46.0, fn=ease, vref=140.0):
    """Position along keys plus a walk phase from distance (no foot sliding)."""
    x = kf(t, keys, fn)
    v = (kf(t + 0.02, keys, fn) - kf(t - 0.02, keys, fn)) / 0.04
    amt = clamp(abs(v) / vref)
    return x, x / step * math.pi, amt, (1 if v > 0 else -1 if v < 0 else 0)


def norm(w):
    return re.sub(r"[^a-z0-9'\-]", "", w.lower().replace("’", "'").replace("“", "").replace("”", ""))


# ---------------------------------------------------------------- captions
def pil_font(name, size, weight=None):
    f = ImageFont.truetype(os.path.join(FONTS, name), size)
    if weight is not None:
        f.set_variation_by_axes([weight, 100])
    return f


def premult(img):
    f = np.asarray(img.convert("RGBA")).astype(np.float32)
    a = f[..., 3:4] / 255.0
    return np.concatenate([f[..., :3] * a, a], -1)


def blit(dst, spr, x, y, op=1.0):
    h, w = spr.shape[:2]
    x, y = int(round(x)), int(round(y))
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, dst.shape[1]), min(y + h, dst.shape[0])
    if x1 <= x0 or y1 <= y0 or op <= 0.002:
        return
    s = spr[y0 - y:y1 - y, x0 - x:x1 - x]
    d = dst[y0:y1, x0:x1]
    d *= 1 - s[..., 3:4] * op
    d += s[..., :3] * op


class Captions:
    """Read-along text in the top box; a yellow pill glides under each word."""

    def __init__(self, tl):
        self.pages = []
        for sc in tl["scenes"]:
            for p in sc["pages"]:
                self.pages.append(self.layout(p, sc["id"] == "title"))

    def layout(self, page, title):
        size = 56
        while True:
            f = pil_font("Fredoka-Variable.ttf", size, 600)
            lh = int(size * 1.22)
            lines = self.wrap(page["words"], f, 900)
            if len(lines) * lh <= CAP_BOT - CAP_TOP or size <= 44:
                break
            size -= 2
        space = f.getlength(" ")
        y0 = (CAP_TOP + CAP_BOT) / 2 - len(lines) * lh / 2
        oy = CAP_TOP - 30
        canvas = Image.new("RGBA", (W, CAP_BOT - CAP_TOP + 60), (0, 0, 0, 0))
        d = ImageDraw.Draw(canvas)
        boxes = []
        for li, line in enumerate(lines):
            lw = sum(f.getlength(w["w"]) for w in line) + space * (len(line) - 1)
            x = W / 2 - lw / 2
            y = y0 + li * lh + lh / 2
            for w in line:
                ww = f.getlength(w["w"])
                d.text((x, y - oy), w["w"], font=f, fill=PLUM + (255,), anchor="lm")
                boxes.append(dict(x=x, y=y, w=ww, start=w["start"], end=w["end"]))
                x += ww + space
        return dict(start=page["start"], img=premult(canvas), oy=oy, boxes=boxes, lh=lh, title=title)

    @staticmethod
    def wrap(words, f, maxw):
        lines, cur = [], []
        for w in words:
            if cur and f.getlength(" ".join(x["w"] for x in cur + [w])) > maxw:
                lines.append(cur)
                cur = [w]
            else:
                cur = cur + [w]
        if cur:
            lines.append(cur)
        return lines

    def index(self, t):
        i = 0
        for k, p in enumerate(self.pages):
            if p["start"] - 0.12 <= t:
                i = k
        return i

    def box_alpha(self, t):
        p1 = self.pages[1]["start"] - 0.25
        return ease(seg(t, p1, p1 + 0.3))

    def draw(self, band, t, y_off):
        """Composite onto `band` (float RGB slice of the frame starting at y_off)."""
        i = self.index(t)
        p = self.pages[i]
        if p["title"]:
            return
        k = ease((t - (p["start"] - 0.12)) / 0.22)
        if k < 1 and i > 0 and not self.pages[i - 1]["title"]:
            q = self.pages[i - 1]
            blit(band, q["img"], 0, q["oy"] - y_off - 12 * k, 1 - k)
        b = next((b for b in p["boxes"] if b["start"] - 0.03 <= t < b["end"]), None)
        if b is not None:
            prev = None
            for c in p["boxes"]:
                if c is b:
                    break
                prev = c
            same = prev is not None and prev["y"] == b["y"]
            g = ease((t - b["start"]) / 0.09) if same else 1.0
            x = lerp(prev["x"], b["x"], g) if same else b["x"]
            w = lerp(prev["w"], b["w"], g) if same else b["w"]
            hh = p["lh"] * 0.8
            pw, ph = int(w + 26), int(hh)
            img = Image.new("RGBA", (pw * 2, ph * 2), (0, 0, 0, 0))
            ImageDraw.Draw(img).rounded_rectangle([0, 0, pw * 2 - 1, ph * 2 - 1], radius=ph, fill=(255, 214, 77, 255))
            blit(band, premult(img.resize((pw, ph), Image.LANCZOS)), x - 13, b["y"] - hh / 2 + 3 - y_off, k)
        blit(band, p["img"], 0, p["oy"] - y_off + 14 * (1 - k), k)


# ------------------------------------------------------------------- story
class Story:
    def __init__(self):
        self.tl = timeline.load()
        self.ev = self.tl["events"]
        self.sc = {s["id"]: s for s in self.tl["scenes"]}
        self.words = {}
        for s in self.tl["scenes"]:
            for p in s["pages"]:
                for w in p["words"]:
                    self.words.setdefault((s["id"], norm(w["w"])), []).append(w["start"])
        self.G, self.Wd, self.M, self.B = toon.BunnyGirl(), toon.WolfDog(), toon.Mom(), toon.LittleBunny()
        self.D = {n: toon.Dog(n) for n in DOGS}
        self.cache = {}
        self.caps = Captions(self.tl)
        self.T = self.tl["duration_video"]
        # scene changes that use an iris wipe (same-place changes are seamless)
        self.iris = {"park": (400, 1300), "invisible": (500, 1300), "hug": (520, 1300),
                     "family": (540, 1300), "end": (540, 1300)}

    def wt(self, scene, word, n=0):
        return self.words[(scene, word)][n]

    # ---------------------------------------------------- cached scenery
    def bg(self, c, key):
        if key not in self.cache:
            arr = np.zeros((H, W, 4), np.uint8)
            getattr(self, "paint_" + key)(skia.Surface(arr).getCanvas())
            self.cache[key] = (arr, skia.Image.fromarray(arr))
        c.drawImage(self.cache[key][1], 0, 0)

    def meadow_base(self, c, sky="day", hill=((184, 230, 164), (150, 216, 128)), grd=((146, 212, 120), (116, 192, 98)), flowers=True):
        tw.sky(c, sky)
        tw.hills(c, 1150, *hill)
        tw.house(c, 860, 1150, 0.8)
        tw.ground(c, 1260, *grd)
        tw.round_tree(c, 90, 1300, 0.9)
        tw.bush(c, 1000, 1290, 0.8)
        tw.grass_tufts(c, 1, 34, 1300, 1900)
        if flowers:
            cols = [(255, 140, 180), (255, 200, 80), (190, 140, 240)]
            for i, (x, y) in enumerate(((60, 1760), (190, 1860), (900, 1800), (1010, 1690), (560, 1890), (330, 1330), (760, 1320))):
                tw.tulip(c, x, y, 0.9 + 0.2 * (y > 1500), cols[i % 3])
            for x, y in ((470, 1840), (720, 1880), (980, 1880), (120, 1640)):
                tw.daisy(c, x, y)

    def paint_meadow(self, c):
        self.meadow_base(c)

    def paint_rain(self, c):
        self.meadow_base(c, "rain", ((150, 196, 140), (124, 180, 116)), ((124, 186, 106), (104, 170, 92)))

    def paint_snow(self, c):
        tw.sky(c, "snow")
        tw.hills(c, 1150, (236, 242, 250), (226, 234, 246))
        tw.house(c, 860, 1150, 0.8)
        tw.snow_ground(c, 1260)
        tw.round_tree(c, 90, 1300, 0.9, col=(226, 238, 246))
        tw.bush(c, 1000, 1290, 0.8, col=(236, 244, 250))

    def paint_sunset(self, c):
        tw.sky(c, "sunset")
        tw.rainbow(c, 540, 1180, 600, 40, 0.55)
        tw.hills(c, 1150, (196, 226, 160), (164, 212, 132))
        tw.house(c, 860, 1150, 0.8)
        tw.ground(c, 1260, (156, 212, 120), (126, 192, 100))
        tw.round_tree(c, 90, 1300, 0.9)
        tw.bush(c, 1000, 1290, 0.8)
        tw.grass_tufts(c, 5, 30, 1300, 1900)
        cols = [(255, 140, 180), (255, 200, 80), (190, 140, 240)]
        for i, (x, y) in enumerate(((60, 1760), (190, 1860), (900, 1800), (1010, 1690), (560, 1890))):
            tw.tulip(c, x, y, 1.0, cols[i % 3])

    def paint_park(self, c):
        tw.sky(c, "day")
        tw.hills(c, 1110, (170, 222, 150), (140, 206, 120), seed=1)
        tw.round_tree(c, 110, 1180, 0.85)
        tw.round_tree(c, 980, 1170, 0.75, col=(80, 180, 90))
        tw.fence(c, 1212, gate=(380, 500))
        tw.ground(c, 1240, (150, 216, 120), (120, 196, 100))
        tw.dog_park_sign(c, 830, 1262, 0.85)
        tw.grass_tufts(c, 2, 30, 1390, 1900)
        for x in (40, 230, 560, 660, 1040):
            tw.tulip(c, x, 1236, 0.85, (255, 140, 180) if x % 3 else (255, 200, 80))
        for x, y in ((80, 1820), (980, 1840), (620, 1890)):
            tw.daisy(c, x, y)

    def paint_park2(self, c):
        tw.sky(c, "day")
        tw.hills(c, 1110, (176, 226, 156), (146, 210, 124), seed=2)
        tw.round_tree(c, 130, 1170, 0.7, col=(80, 180, 90))
        tw.bush(c, 380, 1210, 0.8)
        tw.ground(c, 1220, (150, 216, 120), (120, 196, 100))
        tw.grass_tufts(c, 6, 30, 1400, 1900)
        for i, x in enumerate((60, 180, 300, 540, 640)):
            tw.tulip(c, x, 1390 + 30 * (i % 2), 0.9, [(255, 140, 180), (255, 200, 80), (190, 140, 240)][i % 3])
        for x, y in ((90, 1830), (430, 1880), (700, 1860)):
            tw.daisy(c, x, y)

    def paint_glade(self, c):
        tw.sky(c, "soft")
        tw.hills(c, 1130, (160, 214, 160), (132, 200, 132), seed=2)
        tw.leafy_tree(c, 80, 1330, 1.0, 0.0, seed=1)
        tw.leafy_tree(c, 1010, 1310, 0.95, 0.0, seed=2)
        tw.ground(c, 1270, (156, 214, 130), (124, 194, 104))
        tw.sunbeam(c, 560, 0, 1560, 160, 600, 0.38)
        tw.big_red_flower(c, 120, 1760, 1.0)
        for i, x in enumerate((250, 330, 820, 900, 980)):
            tw.round_flower(c, x, 1450 + (i % 2) * 70, 1.0, stem=110 + 20 * (i % 3))
        tw.grass_tufts(c, 3, 26, 1350, 1900)

    # ------------------------------------------------------- shared bits
    def sky_life(self, c, t, kind="day"):
        if kind in ("day", "soft", "sunset"):
            tw.sun(c, t)
        tw.drifting_clouds(c, t, "rain" if kind == "rain" else "day")

    def butterflies(self, c, t, n=2, seed=0):
        for i in range(n):
            ph = seed * 1.7 + i * 2.1
            x = W / 2 + 400 * math.sin(t * 0.31 + ph) + 80 * math.sin(t * 1.1 + ph * 2)
            y = 860 + 140 * math.sin(t * 0.47 + ph * 1.3) + 40 * math.cos(t * 1.7 + ph)
            flap = abs(math.sin(t * 14 + ph * 5))
            col = [(255, 160, 200), (150, 200, 255), (255, 210, 100)][(i + seed) % 3]
            with Xf(c, x, y, 12 * math.sin(t * 0.8 + ph)):
                for side in (-1, 1):
                    with Xf(c, 0, 0, 0, side * (0.35 + 0.65 * flap), 1):
                        toon.shape(c, toon.oval(18, -12, 18, 15), col, 3.5)
                        toon.shape(c, toon.oval(14, 10, 12, 10), col, 3.5)
                toon.shape(c, toon.rrect(-4, -18, 4, 16, 4), OUT, 0)

    def tag(self, c, t, t0, x, y, label, col, dur=2.6):
        if t < t0:
            return
        a = 1 - seg(t, t0 + dur, t0 + dur + 0.3)
        if a > 0:
            tw.name_tag(c, x, y + 5 * math.sin(t * 3), label, col, back(seg(t, t0, t0 + 0.35), 2.2), a, 3 * math.sin(t * 2))

    def hearts_burst(self, c, t, t0, x, y, n=7, spread=160, rise=260, dur=1.8, seed=0, scale=1.0):
        rng = np.random.default_rng(seed)
        for i in range(n):
            dl, dx, sz = rng.uniform(0, 0.4), rng.uniform(-spread, spread), rng.uniform(0.6, 1.1)
            k = (t - t0 - dl) / dur
            if 0 <= k <= 1:
                tw.heart(c, x + dx + 20 * math.sin(k * 6 + i), y - rise * ease_out(k), sz * scale * (0.5 + 0.5 * ease_out(k * 3)),
                         a=1 - ease((k - 0.6) / 0.4), rot=10 * math.sin(k * 5 + i))

    def sparkle_ring(self, c, t, x, y, r, n=6, speed=1.0, a=1.0, size=18):
        for i in range(n):
            ang = t * speed * 2 + i * 2 * math.pi / n
            tw.sparkle(c, x + r * math.cos(ang), y + r * 0.45 * math.sin(ang), size * (0.7 + 0.3 * math.sin(t * 6 + i)),
                       a=a, rot=t * 90 + i * 30)

    def confetti_burst(self, c, t, t0, x, y, n=40, seed=1):
        rng = np.random.default_rng(seed)
        cols = [(255, 92, 141), (255, 205, 60), (90, 200, 250), (140, 220, 110), (190, 130, 255), (255, 150, 70)]
        for i in range(n):
            ang, spd, spin = rng.uniform(math.pi * 1.05, math.pi * 1.95), rng.uniform(500, 1200), rng.uniform(-500, 500)
            k = t - t0 - rng.uniform(0, 0.12)
            if 0 <= k <= 2.4:
                px = x + math.cos(ang) * spd * k * 0.9
                py = y + math.sin(ang) * spd * k + 700 * k * k
                tw.confetti(c, px, py, i, cols[i % 6], spin * k, 1.0, 1 - ease((k - 1.7) / 0.7))

    def dust(self, c, t, x, y, direction):
        for i in range(3):
            k = ((t * 3 + i / 3) % 1.0)
            tw.puff(c, x - direction * (30 + 60 * k), y - 20 - 30 * k, 22 * (0.5 + k), a=0.7 * (1 - k))

    # ---------------------------------------------------- the characters
    def girl(self, c, x, y, s=GS, **pose):
        self.G.draw(c, x, y, s, **pose)

    def wolf(self, c, x, y, s=WS, **pose):
        self.Wd.draw(c, x, y, s, **pose)

    def mom(self, c, x, y, s=MS, **pose):
        self.M.draw(c, x, y, s, **pose)

    def dog(self, c, name, x, y, **pose):
        self.D[name].draw(c, x, y, DS[name] * pose.pop("k", 1.0), **pose)

    # ============================================================ SCENES
    def scene_intro(self, c, t):
        """Title, then Bunny Girl: name, hat with bunny ears, pretend bunny, hops."""
        self.bg(c, "meadow")
        self.sky_life(c, t)
        self.butterflies(c, t, 2)
        bunny_s = self.wt("bunny", "loves")
        hop_ts = self.ev["hops"]
        # ---- little real bunny hops in, then hops along
        if t > bunny_s - 0.2:
            bx = kf(t, [(bunny_s - 0.2, 1180), (bunny_s + 1.2, 800)], fn=lambda k: k)
            arrive = [bunny_s - 0.2 + i * 0.35 for i in range(4)]
            up, sq = hops(t, arrive + [h - 0.02 for h in hop_ts], 0.3, 46)
            happy = self.wt("bunny", "do")
            nose = 2 * math.sin(t * 30) if t > happy - 0.4 else 0
            self.B.draw(c, bx, Y_MAIN - 10 - up, 1.25, facing=-1, sx=sq[0], sy=sq[1], ear=8 * math.sin(t * 4),
                        eye_open=blink(t, 4), nose=nose)
        # ---- Wolf Dog: hand in hand for the title, then dashes off
        dash = seg(t, 2.30, 3.30)
        WX0 = 400
        if dash < 1:
            wx = lerp(WX0, -460, ease_in(dash))
            pose = dict(arm_f=70, arm_b=20, tail=14 * math.sin(t * 9), eye_open=blink(t, 2), mouth_kind="smile")
            bob = beat_bounce(t, 14)
            if dash > 0:
                wp, bb = walk_wolf(t * 28, 1.2)
                pose.update(wp, arm_f=50, arm_b=60, mouth_kind="laugh", lean=-6)
                bob = bb
                self.dust(c, t, wx + 120, Y_MAIN, -1)
            self.wolf(c, wx, Y_MAIN - bob, facing=1 if dash == 0 else -1, **pose)
            if dash > 0:
                tw.speed_lines(c, wx + 160, Y_MAIN - 260, 1, 4, 140, 1 - dash)
        # ---- Bunny Girl (starts holding Wolf Dog's paw)
        px, py = toon.wolf_paw(WX0, Y_MAIN, WS, True, 70)
        hx, hy = toon.girl_hand(0, 0, GS, -1, 74, -8)
        gx0 = px - hx
        gx, ph, amt, d = mover(t, [(0, gx0), (3.0, gx0), (4.4, 540)])
        pose = dict(eye_open=blink(t, 1), ear_l=-14 + 3 * math.sin(t * 2.1), ear_r=14 + 3 * math.sin(t * 2.4 + 1),
                    arm_l=(18 + 3 * math.sin(t * 1.7), 4), arm_r=(18 + 3 * math.sin(t * 1.9 + 1), 4))
        y = Y_MAIN
        sx, sy = 1.0, 1.0
        if t < 2.4:  # title: holding hands, bouncing to the beat
            pose["arm_l"] = (74, -8)
            y -= beat_bounce(t, 14)
        if 2.3 < t < 3.2:  # waves bye-bye to Wolf Dog
            a, _ = wave(t, 2.3, 3.2, 140, 24, 13)
            pose["arm_l"] = (a, -20)
            pose["look"] = (-0.7, 0)
        if amt > 0.01:
            wp, bob = walk_front(ph, amt)
            pose.update(wp)
            y -= bob
            pose["lean"] = 3 * d * amt
        t_meet = self.wt("bunny", "meet")
        if t_meet - 0.4 < t < t_meet + 0.9:  # waves hello to us
            a, _ = wave(t, t_meet - 0.4, t_meet + 0.9)
            pose["arm_r"] = (a, -18)
            pose["mouth_kind"] = "open"
        t_name = self.wt("bunny", "bunny", 0)
        up, sq = hop(t, t_name - 0.05, 0.45, 80)
        if t_name - 0.1 < t < t_name + 0.9:  # happy jump on her name
            pose.update(arm_l=(150, -10), arm_r=(150, -10), mouth_kind="laugh", eye_open=0.1)
            y -= up
            sx, sy = sq
        t_hat, t_imag = self.wt("bunny", "hat"), self.wt("bunny", "imagine")
        if t_hat - 0.3 < t < t_imag - 0.1:  # points at her bunny ears; ears wiggle
            k = ease(seg(t, t_hat - 0.3, t_hat)) * (1 - ease(seg(t, t_imag - 0.5, t_imag - 0.1)))
            pose["arm_l"] = (lerp(18, 158, k), lerp(4, -40, k))
            pose["arm_r"] = (lerp(18, 158, k), lerp(4, -40, k))
            wig = 14 * math.sin(t * 22) * ease(seg(t, self.wt("bunny", "bunny", 1) - 0.2, self.wt("bunny", "bunny", 1)))
            pose["ear_l"] -= wig
            pose["ear_r"] += wig
            pose["look"] = (0, -0.8)
        if t_imag - 0.1 < t < bunny_s - 0.3:  # "imagine that!" - cheeky head tilt
            k = ease(seg(t, t_imag - 0.1, t_imag + 0.3)) * (1 - ease(seg(t, bunny_s - 0.7, bunny_s - 0.3)))
            pose["head_tilt"] = 12 * k
            pose["arm_l"] = (lerp(18, 40, k), lerp(4, 128, k))
            pose["arm_r"] = (lerp(18, 40, k), lerp(4, 128, k))
            pose["blush_a"] = 0.55 + 0.4 * k
            if t > self.wt("bunny", "that") - 0.1:
                pose["eye_open"] = 0.1
                pose["mouth_kind"] = "laugh"
        if bunny_s - 0.3 < t < hop_ts[0] - 0.1:  # pretends to be a bunny: paws up
            k = ease(seg(t, bunny_s - 0.3, bunny_s + 0.3))
            pose["arm_l"] = (lerp(18, 34, k), lerp(4, 112, k))
            pose["arm_r"] = (lerp(18, 34, k), lerp(4, 112, k))
            pose["look"] = (0.7, 0)
            pose["ear_l"], pose["ear_r"] = -8, 8
            sy = 1 - 0.05 * k
        if hop_ts[0] - 0.1 <= t < hop_ts[-1] + 0.6:  # Hop! Hop! Hop!
            up, sq = hops(t, [h - 0.05 for h in hop_ts], 0.3, 120)
            y -= up
            sx, sy = sq
            pose.update(arm_l=(34, 112), arm_r=(34, 112), mouth_kind="open", ear_bend=0.5 if up > 10 else 0.0)
            pose["ear_l"], pose["ear_r"] = -24 - up * 0.08, 24 + up * 0.08
        t_do = self.wt("bunny", "do")
        if hop_ts[-1] + 0.6 <= t:  # laughing "just like bunnies do!"
            pose.update(mouth_kind="laugh", eye_open=0.1 if t < t_do + 0.6 else pose["eye_open"],
                        arm_l=(150, -10), arm_r=(150, -10))
        self.girl(c, gx, y, sx=sx, sy=sy, **pose)
        self.tag(c, t, t_name, gx, 820 - up, "Bunny Girl", (60, 190, 200), dur=2.2)
        if t_hat < t < t_imag:
            for i in range(3):
                tw.sparkle(c, gx - 90 + 90 * i, 900 + 20 * math.sin(t * 5 + i), 20, a=bump(t, t_hat + 0.2 * i, 1.0), rot=t * 80)
        self.hearts_burst(c, t, t_do - 0.2, (gx + 800) / 2, 1260, n=6, seed=3)
        if t < 2.7:
            self.title(c, t)

    def title(self, c, t):
        a = 1 - seg(t, 2.35, 2.7)
        lines = [("Bunny", "Girl"), ("and", "Wolf", "Dog!")]
        times = iter([0.41, 0.71, 1.08, 1.21, 1.46])
        ends = [0.71, 1.08, 1.21, 1.46, 2.05]
        f = toon.font("Chewy-Regular.ttf", 124)
        idx = 0
        for li, line in enumerate(lines):
            widths = [f.measureText(w) for w in line]
            total = sum(widths) + 30 * (len(line) - 1)
            x = W / 2 - total / 2
            for w, wd in zip(line, widths):
                t0 = next(times)
                t1 = ends[idx]
                idx += 1
                active = t0 - 0.03 <= t < t1
                s = 1 + 0.14 * bump(t, t0, max(0.2, t1 - t0)) if active else 1.0
                y = 330 + li * 140 - beat_bounce(t + idx * 0.12, 8)
                col = (255, 220, 70) if active else WHITE
                with Fade(c, a), Xf(c, x + wd / 2, y - 45, 0, s):
                    toon.text(c, w, 0, 45, 124, col, PLUM, 16)
                x += wd + 30

    def scene_park(self, c, t):
        """Mom and Bunny Girl bring the five dogs; roll call; Mooky and Buddy zoom by."""
        sc = self.sc["park"]
        t0 = sc["t0"]
        self.bg(c, "park")
        self.sky_life(c, t)
        tw.river(c, t, 1318)
        self.butterflies(c, t, 1, seed=2)
        hooray = self.wt("park", "hooray")
        hi = self.wt("park", "hi")
        names = dict(zip(DOGS, self.ev["dog_names"]))
        # ---- Mom + Bunny Girl walk in
        for who in ("mom", "girl"):
            keys = [(t0 - 0.3, -60), (t0 + 2.6, 190)] if who == "mom" else [(t0 - 0.3, 230), (t0 + 2.4, 470)]
            x, ph, amt, d = mover(t, keys)
            pose = dict(eye_open=blink(t, 3 if who == "mom" else 1))
            y = Y_BACK + (0 if who == "mom" else 20)
            if amt > 0.01:
                wp, bob = walk_front(ph, amt)
                pose.update(wp)
                y -= bob
            up, sq = hop(t, hooray - 0.1, 0.5, 90 if who == "girl" else 50)
            if hooray - 0.4 < t < hooray + 0.9:
                k = bump(t, hooray - 0.4, 1.3)
                pose.update(arm_l=(lerp(18, 155, min(1, k * 2)), -10), arm_r=(lerp(18, 155, min(1, k * 2)), -10), mouth_kind="laugh")
                y -= up
            if hi - 0.3 < t < hi + 1.0:
                a, _ = wave(t, hi - 0.3, hi + 1.0)
                pose["arm_r"] = (a, -18)
                pose["mouth_kind"] = "open"
            if t > names["Cosmo"] - 0.3:
                pose["look"] = (0.6, 0.3)
            if who == "mom":
                self.mom(c, x, y, sx=sq[0] if hooray - 0.1 < t < hooray + 0.6 else 1, **pose)
            else:
                self.girl(c, x, y, sx=sq[0] if hooray - 0.1 < t < hooray + 0.6 else 1,
                          sy=sq[1] if hooray - 0.1 < t < hooray + 0.6 else 1, **pose)
        # ---- dogs
        spots = dict(Cosmo=(150, Y_DOGS), Pettie=(490, Y_DOGS + 40), Luna=(860, Y_DOGS))
        for i, n in enumerate(DOGS):
            if n in spots:
                tx, ty = spots[n]
                x, ph, amt, d = mover(t, [(t0 - 0.3 + 0.1 * i, -200 - 150 * i), (t0 + 2.8 + 0.2 * i, tx)], step=34, fn=ease_out)
                y = ty
                up, sq = hop(t, names[n] - 0.05, 0.45, 90)
                bark = names[n] - 0.05 < t < names[n] + 0.5 or hi - 0.1 < t < hi + 0.5 or hooray - 0.2 < t < hooray + 0.5
                self.dog(c, n, x, y, phase=ph, run=amt, tail=25 * math.sin(t * 14 + i), jump=up, sx=sq[0], sy=sq[1],
                         mouth_kind="open" if bark else "smile", eye_open=blink(t, 5 + i),
                         facing=1)
                if t > names[n] - 0.05:
                    self.tag(c, t, names[n], x + 20, y - 300, n, TAG_COL[n], dur=29.5 - names[n])
            else:  # Mooky and Buddy run ahead, then zoom by
                zt = names[n]
                x1, ph1, amt1, _ = mover(t, [(t0 - 0.3 + 0.1 * i, -160 - 120 * i), (t0 + 3.4, 1350)], step=34, fn=ease_in)
                x2, ph2, amt2, _ = mover(t, [(zt - 0.35, -330), (zt + 1.0, 1400)], step=30, fn=lambda k: k)
                y = Y_DOGS - 110 + (0 if n == "Mooky" else 40)
                if t < zt - 0.35:
                    x, ph, amt = x1, ph1, amt1
                else:
                    x, ph, amt = x2, ph2, 1.0
                if -300 < x < 1380:
                    self.dog(c, n, x, y, phase=ph * 1.4, run=amt, tail=30 * math.sin(t * 16), mouth_kind="open",
                             eye_open=1.0, k=1.0)
                    if t > zt - 0.35:
                        tw.speed_lines(c, x - 150, y - 120, -1, 4, 160)
                        self.tag(c, t, zt - 0.3, x, y - 330, n, TAG_COL[n], dur=1.6)

    def scene_invisible(self, c, t):
        """Wolf Dog waits, they play catch, he gets shy and turns invisible;
        the others can't see him; he hides behind a bush... peek-a-boo!"""
        sc = self.sc["invisible"]
        t0 = sc["t0"]
        self.bg(c, "park2")
        self.sky_life(c, t)
        tw.river(c, t, 1310, 60)
        w_wolf = self.wt("invisible", "wolf", 0)
        love = self.wt("invisible", "love")
        laugh = self.wt("invisible", "laugh")
        shy = self.wt("invisible", "shy", 0)
        inv = self.ev["invisible"][0]
        only = self.wt("invisible", "only")
        spot = self.wt("invisible", "spot")
        pk = self.ev["peekaboo"]
        BX, BY, BS = 900, 1640, 2.2                     # the bush he hides behind
        confused = only + 0.3 < t
        # ---- Mom wanders in behind them and can't see him
        if t > only - 0.8:
            mx, mph, mamt, _ = mover(t, [(only - 0.8, -180), (only + 0.5, 470)])
            mp, mb = walk_front(mph, mamt)
            look = (math.sin(t * 2.6), -0.2) if confused else (1, 0)
            self.mom(c, mx, Y_BACK - 110 - mb, 0.75, look=look, mouth_kind="o" if confused else "smile",
                     eye_open=blink(t, 7), **mp)
            if confused:
                tw.question_mark(c, mx + 10, Y_BACK - 110 - 610 + 6 * math.sin(t * 4), 0.9,
                                 ease(seg(t, only + 0.3, only + 0.6)), rot=8 * math.sin(t * 2.6))
        # ---- Bunny Girl runs in to play
        gx, gph, gamt, gd = mover(t, [(t0 + 1.0, -160), (t0 + 2.4, 300)])
        pose = dict(eye_open=blink(t, 1), look=(0.6, 0))
        y = Y_MAIN
        if gamt > 0.01:
            wp, bob = walk_front(gph * 1.3, gamt)
            pose.update(wp)
            y -= bob
        # ---- Wolf Dog
        wx = kf(t, [(spot - 0.75, 560), (spot - 0.05, BX)])
        wpose = dict(facing=-1, tail=20 * math.sin(t * (16 if t < shy else 8)), eye_open=blink(t, 2), look=(0.4, 0))
        wy = Y_MAIN
        if t < t0 + 2.4:  # eager, bouncing on his toes while he waits
            wy -= beat_bounce(t * 1.4, 12)
            wpose["look"] = (1, 0) if t < t0 + 1.2 else (0.4, 0)
        if spot - 0.75 < t < spot - 0.05:  # tiptoes over to the bush
            ww, wb = walk_wolf((t - spot) * 26, 1.0)
            wpose.update(ww)
            wy -= wb
        duck = 560 * ease(seg(t, spot - 0.1, spot + 0.25)) * (1 - ease_out(seg(t, pk - 0.2, pk + 0.05)))
        wy += duck
        wy -= hop(t, pk + 0.02, 0.45, 70)[0]
        alpha = 1.0
        ball = None
        if love - 0.15 < t < laugh - 0.3:  # they love each other: big happy wave
            a, _ = wave(t, love - 0.15, laugh - 0.3, 140, 20, 12)
            pose.update(arm_r=(a, -16), mouth_kind="laugh")
            wpose.update(arm_f=a, mouth_kind="laugh")
        if laugh - 0.35 < t < shy - 0.4:  # play catch
            for i in range(4):
                ts = laugh - 0.35 + 0.62 * i
                k = (t - ts) / 0.62
                if 0 <= k < 1:
                    a_x, b_x = (gx + 70, wx - 110) if i % 2 == 0 else (wx - 110, gx + 70)
                    ball = (lerp(a_x, b_x, k), 1180 - 260 * math.sin(math.pi * k))
                    if k > 0.7:
                        if i % 2 == 0:
                            wpose["arm_f"] = 95
                        else:
                            pose["arm_r"] = (100, 0)
                    elif k < 0.2:
                        if i % 2 == 0:
                            pose["arm_r"] = (150, -20)
                        else:
                            wpose["arm_f"] = 140
            pose["mouth_kind"] = "laugh"
            wpose["mouth_kind"] = "laugh"
        if shy - 0.4 < t < inv:  # shy: blushes and hides his face
            k = ease(seg(t, shy - 0.4, shy))
            wpose.update(blush_a=0.9 * k, ear_droop=22 * k, head_tilt=-8 * k, look=(0, 0.8), arm_f=lerp(20, 150, k),
                         mouth_kind="smile")
            wy -= 4 * math.sin(t * 6) * k
            pose["look"] = (0.6, -0.2)
        if t >= inv - 0.3:  # ...and turns invisible
            k = ease(seg(t, inv - 0.3, inv + 0.7))
            alpha = lerp(1.0, 0.42 + 0.05 * math.sin(t * 3), k)
            wpose.update(blush_a=0.5, arm_f=lerp(150, 20, k))
        if only - 0.2 < t < spot - 0.4:  # she points: "only Bunny Girl can see him"
            pose.update(arm_r=(95, 0), mouth_kind="open", look=(0.7, 0))
            wpose.update(arm_f=120 + 20 * math.sin(t * 12), mouth_kind="laugh")
        if spot - 0.4 < t < pk - 0.15:
            pose.update(hands_together=True, look=(0.8, 0.1), mouth_kind="smile")
        if t > pk - 0.15:  # peek-a-boo!
            k = ease(seg(t, pk - 0.15, pk + 0.1))
            alpha = lerp(alpha, 0.8, k * (1 - seg(t, pk + 0.9, pk + 1.5) * 0.4))
            wpose.update(mouth_kind="laugh", eye_open=1.0, arm_f=lerp(20, 135, k), arm_b=lerp(20, 135, k), look=(0, 0))
            pose.update(mouth_kind="laugh", hands_together=True, eye_open=0.1 if t > pk + 0.2 else 1.0)
        c.save()
        if duck > 1:
            c.clipRect(skia.Rect.MakeLTRB(0, 0, W, BY + 20))
        self.wolf(c, wx, wy, alpha=alpha, **wpose)
        c.restore()
        if alpha < 0.99 and duck < 200:
            self.sparkle_ring(c, t, wx, wy - 260, 170, 5, 0.8, a=0.8 * ease(seg(t, inv - 0.3, inv + 0.4)), size=16)
        # the bush (rustles while he hides behind it)
        rustle = 5 * math.sin(t * 30) * bump(t, spot - 0.1, 0.6) + 6 * math.sin(t * 34) * bump(t, pk - 0.25, 0.5)
        tw.bush(c, BX + rustle, BY, BS, col=(104, 192, 100))
        for fx_, fy_ in ((-60, -95), (30, -135), (100, -70)):
            toon.shape(c, toon.circle(BX + rustle + fx_ * BS / 2.1, BY + fy_ * BS / 2.1, 13), (255, 150, 190), 3.5)
            toon.shape(c, toon.circle(BX + rustle + fx_ * BS / 2.1, BY + fy_ * BS / 2.1, 5), (255, 230, 120), 0)
        self.girl(c, gx, y, **pose)
        if ball:
            tw.ball(c, ball[0], ball[1], 32, t * 400)
        # ---- two dogs sniff around, right next to him, and can't see him either
        if t > only - 0.6:
            for k, (n, keys, face) in enumerate((("Luna", [(only - 0.6, -260), (only + 0.6, 470)], 1),
                                               ("Cosmo", [(only - 0.4, 1340), (only + 0.7, 790)], -1))):
                dx, dph, damt, dd = mover(t, keys, step=30)
                sniff = 4 * math.sin(t * 9 + k) if confused else 0
                look = (0.8 * math.sin(t * 2.2 + k * 2), -0.4) if confused else (0.4, 0)
                self.dog(c, n, dx, Y_DOGS + 20 * k, phase=dph, run=damt, facing=face, head_tilt=sniff,
                         look=look, eye_open=blink(t, 8 + k), tail=12 * math.sin(t * 6 + k))
                if confused:
                    hy_ = Y_DOGS + 20 * k - 300 - (60 if n == "Cosmo" else 30)
                    tw.question_mark(c, dx + 10 * face, hy_ + 6 * math.sin(t * 4 + k), 0.75,
                                     ease(seg(t, only + 0.5 + 0.2 * k, only + 0.8 + 0.2 * k)), rot=10 * math.sin(t * 3 + k))
        self.hearts_burst(c, t, love - 0.1, (gx + wx) / 2, 1150, n=7, seed=5)
        if laugh < t < shy - 0.4:
            for i in range(3):
                k = ((t - laugh) * 0.8 + i / 3) % 1.0
                tw.music_note(c, (gx + wx) / 2 - 100 + 100 * i, 1000 - 120 * k, 0.9, 1 - k)
        self.tag(c, t, w_wolf, wx, 860, "Wolf Dog", (150, 130, 190), dur=2.5)
        if t > pk - 0.1:
            for i in range(5):
                tw.sparkle(c, wx - 170 + 85 * i, 980 + 30 * math.sin(i), 22, a=bump(t, pk - 0.1 + 0.08 * i, 1.0), rot=t * 120)

    def scene_glade(self, c, t):
        """The wish, the idea, the big hug, the glow, POOF!, the dogs play."""
        tp = self.ev["poof"]
        self.bg(c, "glade")
        self.sky_life(c, t, "soft")
        bub_on = self.wt("hug", "wished")
        bub_off = self.wt("hug", "but")
        idea = self.wt("hug", "idea")
        hug1, hug2 = self.ev["hugs"]
        love = self.ev["love"][0]
        best = self.wt("hug", "best")
        sud = self.ev["suddenly"]
        r0, r1 = self.ev["drumroll"]
        appeared = self.wt("poof", "appeared")
        ran = self.wt("poof", "ran", 0)
        jumped, played, ran2 = self.wt("poof", "jumped"), self.wt("poof", "played"), self.wt("poof", "ran", 1)
        came = self.wt("poof", "came")
        no_longer = self.wt("poof", "no")
        wx, wy = 700, Y_MAIN
        # ---- Mom: walks past without seeing him, later runs in after the POOF
        if bub_off < t < bub_off + 3.6:
            mx, mph, mamt, _ = mover(t, [(bub_off + 0.1, -240), (bub_off + 3.4, 1300)], fn=lambda k: k)
            mp, mb = walk_front(mph, mamt)
            self.mom(c, mx, Y_BACK - 80 - mb, 0.78, eye_open=blink(t, 7), look=(1, 0), **mp)
            for k, n in enumerate(("Pettie", "Buddy")):
                dx, dph, damt, _ = mover(t, [(bub_off + 0.3 + 0.2 * k, -420 - 200 * k), (bub_off + 3.6, 1250 - 150 * k)], step=30, fn=lambda q: q)
                self.dog(c, n, dx, Y_BACK - 40 + 20 * k, k=0.8, phase=dph, run=damt, eye_open=blink(t, 9 + k))
        if t > tp:
            mx, mph, mamt, _ = mover(t, [(appeared - 0.6, -240), (appeared + 0.7, 150)])
            mp, mb = walk_front(mph, mamt)
            mpose = dict(eye_open=blink(t, 7), look=(0.8, 0), **mp)
            if appeared + 0.6 < t < ran - 0.2:
                k = ease(seg(t, appeared + 0.6, appeared + 0.9))
                mpose.update(arm_l=(lerp(14, 36, k), lerp(0, 132, k)), arm_r=(lerp(14, 36, k), lerp(0, 132, k)),
                             mouth_kind="o" if t < appeared + 1.4 else "open")
            if t > jumped - 0.2:
                mpose.update(arm_l=(30, 120), arm_r=(30, 120), mouth_kind="laugh")
                if int((t - jumped) * 4) % 2 == 0:
                    mpose.update(arm_l=(36, 110), arm_r=(36, 110))
            if mamt > 0.01 or t > tp:
                self.mom(c, mx, Y_BACK - 10 - mb, MS * 0.88, **mpose)
        # ---- dogs run up after the POOF and play
        dog_spots = dict(Cosmo=(470, Y_DOGS - 10), Pettie=(250, Y_DOGS + 40), Luna=(880, Y_DOGS + 10),
                         Mooky=(980, Y_DOGS - 120), Buddy=(650, Y_DOGS + 60))
        actors = []
        if t > ran - 0.6:
            for i, n in enumerate(DOGS):
                sx_, sy_ = dog_spots[n]
                from_left = n in ("Cosmo", "Pettie", "Buddy")
                start = -300 - 140 * i if from_left else 1400 + 140 * i
                x, ph, amt, d = mover(t, [(ran - 0.6 + 0.12 * i, start), (ran + 1.1 + 0.12 * i, sx_)], step=32, fn=ease_out)
                y = sy_
                facing = 1 if d > 0 else -1 if d < 0 else (1 if sx_ < wx else -1)
                up, sq = hop(t, jumped + 0.09 * i, 0.5, 120)
                up2, sq2 = hop(t, played + 0.09 * i, 0.4, 70)
                if up2 > up:
                    up, sq = up2, sq2
                if ran2 - 0.15 < t < no_longer - 0.3:  # run around Wolf Dog in a loop
                    k = seg(t, ran2 - 0.15, no_longer - 0.3)
                    ang = 2 * math.pi * (k * 1.6) + i * 2 * math.pi / 5
                    blend = ease(seg(t, ran2 - 0.15, ran2 + 0.2)) * (1 - ease(seg(t, no_longer - 0.7, no_longer - 0.3)))
                    lx, ly = wx + 360 * math.cos(ang), Y_MAIN + 60 + 110 * math.sin(ang)
                    x, y = lerp(x, lx, blend), lerp(y, ly, blend)
                    if blend > 0.5:
                        facing = -1 if math.sin(ang) > 0 else 1
                    ph, amt = t * 16 + i, max(amt, blend)
                happy = t > ran - 0.2
                actors.append((y, "dog", dict(name=n, x=x, y=y, phase=ph, run=amt, facing=facing, jump=up, sx=sq[0], sy=sq[1],
                                              tail=30 * math.sin(t * 16 + i), mouth_kind="open" if happy else "smile",
                                              eye_open=blink(t, 11 + i))))
        # ---- Wolf Dog
        wpose = dict(facing=-1, tail=10 * math.sin(t * 6), eye_open=blink(t, 2), look=(0.3, 0))
        alpha = 0.45 + 0.05 * math.sin(t * 3)
        glow = 0.0
        shake = 0.0
        if t < bub_off + 1.0:
            wpose.update(look=(0.6, -0.3))
        if bub_off + 0.6 < t < bub_off + 1.8:  # waves at Mom; she can't see him
            a, _ = wave(t, bub_off + 0.6, bub_off + 1.8, 120, 20, 12)
            wpose["arm_f"] = a
            wpose["mouth_kind"] = "open"
        if bub_off + 1.9 < t < idea:  # sad
            k = ease(seg(t, bub_off + 1.9, bub_off + 2.3))
            wpose.update(ear_droop=26 * k, mouth_kind="sad", head_tilt=-10 * k, look=(0, 0.9), tail=0)
        hugging = hug1 - 0.05 < t < best - 0.3
        if t > hug1 - 0.3:
            wpose.update(mouth_kind="smile", blush_a=0.8, eye_open=0.1 if hugging else blink(t, 2),
                         tail=26 * math.sin(t * 18))
        if hugging:
            wpose.update(arm_f=80, head_tilt=8)     # his arm wraps around her; snout tucked by her cheek
        if t > best - 0.3:
            wpose.update(mouth_kind="laugh" if t < sud else "o", blush_a=0.9)
        if t > sud - 0.1:
            glow = lerp(0, 0.6, ease(seg(t, sud - 0.1, r0))) + lerp(0, 0.4, ease(seg(t, r0, r1)))
            wpose.update(eye_open=1.0, mouth_kind="o", look=(0, -0.5))
            shake = 6 * ease(seg(t, r0, r1))
        if t >= tp:  # visible!
            alpha, glow, shake = 1.0, max(0.0, 1 - seg(t, tp, tp + 0.9)), 0.0
            k = seg(t, tp, appeared)
            wpose.update(arm_f=lerp(150, 60, ease(seg(t, tp + 0.6, appeared))), arm_b=lerp(150, 40, ease(seg(t, tp + 0.6, appeared))),
                         mouth_kind="o" if t < tp + 0.9 else "laugh", look=(0, -0.3) if k < 1 else (0.3, 0),
                         ear_droop=0, head_tilt=0, blush_a=0.3, tail=30 * math.sin(t * 16))
            if appeared - 0.3 < t < ran - 0.4:  # looks at his paws: "I can be seen!"
                wpose.update(arm_f=70, arm_b=70, look=(0.4, 0.8), mouth_kind="laugh")
            up, sq = hop(t, jumped - 0.05, 0.55, 150)
            up2, _ = hop(t, played - 0.05, 0.45, 90)
            wy -= max(up, up2)
            if came - 0.4 < t:  # waves proudly at everyone
                a, _ = wave(t, came - 0.4, self.sc["poof"]["t1"] + 0.5, 130, 22, 12)
                wpose["arm_f"] = a
                wpose["mouth_kind"] = "laugh"
        jx = shake * math.sin(t * 60)
        actors.append((wy, "wolf", dict(x=wx + jx, y=wy, alpha=alpha, glow=glow, **wpose)))
        # ---- Bunny Girl
        gx, gph, gamt, gd = mover(t, [(idea + 0.85, 300), (hug1 - 0.05, wx - 240), (best - 0.4, wx - 240), (best, 430),
                                      (sud - 0.1, 470), (sud + 0.4, 400)])
        pose = dict(eye_open=blink(t, 1), look=(0.6, 0))
        y = Y_MAIN
        if gamt > 0.01:
            wp, bob = walk_front(gph * 1.3, gamt)
            pose.update(wp)
            y -= bob
        if bub_on - 0.2 < t < bub_off + 0.2:  # dreaming
            pose.update(hands_together=True, look=(0.2, -0.9), mouth_kind="smile", head_tilt=6)
        if bub_off + 1.9 < t < idea - 0.2:
            pose.update(mouth_kind="sad", look=(0.5, 0.4))
        if idea - 0.2 < t < hug1 - 0.6:  # idea!
            k = ease(seg(t, idea - 0.2, idea + 0.1))
            pose.update(arm_r=(lerp(18, 165, k), -10), mouth_kind="open", look=(0, -0.8))
        if hugging:
            pose.update(arm_l=(50, 95), arm_r=(95, 15), eye_open=0.1, mouth_kind="smile", blush_a=0.9, head_tilt=8)
        if best - 0.3 < t < sud - 0.1:
            pose.update(mouth_kind="laugh", hands_together=True, blush_a=0.8)
        if sud - 0.1 < t < tp:
            pose.update(mouth_kind="o", look=(0.7, -0.4), arm_l=(40, 120), arm_r=(40, 120))
        if tp <= t:
            k = ease(seg(t, tp, tp + 0.4))
            pose.update(mouth_kind="o" if t < tp + 0.8 else "laugh", look=(0.7, -0.3))
            if t > ran - 0.5:
                bounce = beat_bounce(t, 10)
                y -= bounce
                pose.update(arm_l=(150, -10), arm_r=(150, -10), mouth_kind="laugh", eye_open=blink(t, 1))
        squeeze = 0.0
        for w_ in (self.wt("hug", "squeezy"), self.wt("hug", "cozy"), self.wt("hug", "snuggle-bug"), hug2):
            squeeze = max(squeeze, bump(t, w_ - 0.05, 0.35))
        hsx, hsy = 1 + 0.05 * squeeze, 1 - 0.04 * squeeze
        actors.append((y + 1, "girl", dict(x=gx, y=y, sx=hsx, sy=hsy, **pose)))
        # ---- draw everything back to front
        actors.sort(key=lambda a: a[0])
        for _, kind, kw in actors:
            if kind == "dog":
                n = kw.pop("name")
                self.dog(c, n, kw.pop("x"), kw.pop("y"), **kw)
            elif kind == "wolf":
                x_, y_ = kw.pop("x"), kw.pop("y")
                if hugging:
                    self.wolf(c, x_, y_, sx=hsx, sy=hsy, parts="back", **kw)
                    self.wolf_arm_later = (x_, y_, kw)
                else:
                    self.wolf(c, x_, y_, **kw)
                    self.wolf_arm_later = None
            else:
                self.girl(c, kw.pop("x"), kw.pop("y"), **kw)
        if hugging and self.wolf_arm_later:
            x_, y_, kw = self.wolf_arm_later
            self.wolf(c, x_, y_, sx=hsx, sy=hsy, parts="arm", **kw)
        # ---- effects
        if alpha < 0.99 and t < tp:
            self.sparkle_ring(c, t, wx, wy - 260, 170 + 30 * glow, 5 + int(4 * glow), 0.8 + 3 * glow, a=0.75 + 0.25 * glow, size=16 + 8 * glow)
        if bub_on - 0.1 < t < bub_off + 0.3:
            self.wish_bubble(c, t, bub_on, bub_off, gx)
        if bub_off + 0.15 < t < bub_off + 0.9:
            for i in range(6):
                k = seg(t, bub_off + 0.15, bub_off + 0.9)
                tw.puff(c, 540 + 260 * math.cos(i) * k, 790 + 140 * math.sin(i * 1.7) * k, 60 * (1 - 0.5 * k), a=1 - k)
        if idea - 0.15 < t < hug1 - 0.5:
            k = seg(t, idea - 0.15, idea + 0.2)
            tw.lightbulb(c, gx, 860 - 20 * math.sin(t * 4), back(k, 2.5), glow=0.6 + 0.4 * math.sin(t * 10),
                         a=1 - seg(t, hug1 - 0.8, hug1 - 0.5))
        for hw in (hug1, hug2):
            self.hearts_burst(c, t, hw - 0.05, 600, 1120, n=8, spread=200, seed=int(hw * 10))
        for w_ in (self.wt("hug", "squeezy"), self.wt("hug", "cozy"), self.wt("hug", "snuggle-bug")):
            self.hearts_burst(c, t, w_, 620, 1100, n=3, spread=120, rise=200, seed=int(w_ * 7))
        self.hearts_burst(c, t, love - 0.1, 600, 1080, n=10, spread=240, rise=320, dur=2.2, seed=11)
        if best - 0.2 < t < sud:
            k = back(seg(t, best - 0.2, best + 0.3), 2.0) * (1 - seg(t, sud - 0.4, sud))
            tw.heart(c, (gx + wx) / 2 + 20, 960 - 10 * math.sin(t * 4), 2.6 * k * (1 + 0.06 * math.sin(t * 9)), a=k)
        if t < tp:
            tw.vignette(c, 0.8 * ease(seg(t, r0 - 0.2, r1)))
        if tp - 0.02 <= t < tp + 1.6:  # POOF!
            k = seg(t, tp, tp + 1.3)
            for i in range(14):
                ang = i * 2 * math.pi / 14 + 0.3
                dist = 120 + 300 * ease_out(k)
                tw.puff(c, wx + dist * math.cos(ang), wy - 250 + dist * 0.7 * math.sin(ang), 80 * (1 - 0.4 * k), a=1 - ease((k - 0.3) / 0.7))
            tw.puff(c, wx, wy - 250, 230 * (1 - ease(seg(t, tp, tp + 0.6))) + 1, a=1 - seg(t, tp + 0.2, tp + 0.7))
            tw.burst(c, 330, 860, 190, "POOF!", back(seg(t, tp, tp + 0.35), 2.6) * 0.95, 1 - seg(t, tp + 1.2, tp + 1.6),
                     rot=-8 + 5 * math.sin(t * 7))
        self.confetti_burst(c, t, tp, wx, wy - 300, 44, seed=2)
        self.confetti_burst(c, t, came, wx, wy - 400, 40, seed=7)
        self.hearts_burst(c, t, self.wt("poof", "happy"), 600, 1320, n=9, spread=320, seed=13)
        tw.flash(c, max(0.0, 1 - abs(t - tp) / (0.08 if t < tp else 0.45)))

    def wish_bubble(self, c, t, t_on, t_off, gx):
        k = back(seg(t, t_on - 0.1, t_on + 0.35), 2.0)
        x, y, w, h = 600, 712, 720, 380
        with Xf(c, x, y, 0, k):
            tw.thought_bubble(c, 0, 0, w, h, (gx - x, 1000 - y))
            c.save()
            c.clipPath(toon.oval(0, 0, w / 2 - 30, h / 2 - 26), doAntiAlias=True)
            c.drawRect(skia.Rect.MakeLTRB(-w / 2, 40, w / 2, h / 2), toon.fill_paint((170, 226, 150)))
            b = beat_bounce(t, 14)
            self.mom(c, -200, 140 - b * 0.5, 0.33, shadow=False, arm_l=(150, -10), arm_r=(150, -10), mouth_kind="laugh", eye_open=0.1)
            self.wolf(c, 90, 140 - b, 0.31, shadow=False, arm_f=125, mouth_kind="laugh", tail=20 * math.sin(t * 14))
            self.dog(c, "Buddy", -40, 150 - b * 0.8, k=0.5, shadow=False, mouth_kind="open", tail=25 * math.sin(t * 15))
            self.dog(c, "Cosmo", 250, 150 - beat_bounce(t + 0.2, 14), k=0.46, shadow=False, facing=-1, mouth_kind="open")
            tw.heart(c, -60, -90 - 10 * math.sin(t * 3), 0.8)
            tw.heart(c, 160, -110 - 10 * math.sin(t * 3 + 1), 0.6)
            c.restore()

    def scene_family(self, c, t):
        """Every kind of weather together; Mom and the dogs; family photo."""
        sc = self.sc["family"]
        t0 = sc["t0"]
        rain_on, snow_on = self.wt("family", "in"), self.wt("family", "weather")
        sun_back = self.wt("family", "bunny") - 0.15
        with_mom = self.wt("family", "with")
        fam = self.wt("family", "family")
        weather = "day" if t < rain_on - 0.1 else "rain" if t < snow_on - 0.05 else "snow" if t < sun_back else "day"
        key = {"day": "meadow", "rain": "rain", "snow": "snow"}[weather]
        self.bg(c, key)
        if weather == "day" and t > sun_back:
            tw.rainbow(c, 540, 1200, 600, 40, 0.9 * ease(seg(t, sun_back, sun_back + 1.0)))
        self.sky_life(c, t, "rain" if weather == "rain" else "day")
        # ---- the pair walk along together, hand in hand
        gx, ph, amt, d = mover(t, [(t0 - 0.1, 230), (with_mom - 0.4, 420), (with_mom + 1.2, 420)], step=40,
                               fn=lambda k: k, vref=45)
        wx = gx + 270
        pose = dict(eye_open=blink(t, 1), look=(0.5, 0), arm_r=(64, -8))
        wpose = dict(facing=1, arm_b=62, tail=22 * math.sin(t * 12), eye_open=blink(t, 2), look=(-0.4, 0))
        y, wy = Y_MAIN, Y_MAIN
        if amt > 0.01:
            wp, bob = walk_front(ph, amt)
            wp.pop("arm_r")
            pose.update(wp)
            y -= bob
            ww, wb = walk_wolf(ph + 1.2, amt)
            wpose.update(ww)
            wy -= wb
        if weather == "rain":
            pose.update(arm_l=(150, -25), mouth_kind="open")
        if weather == "snow":
            pose.update(look=(0, -1), mouth_kind="open", arm_l=(120, -20))
            wpose.update(look=(0, -1), mouth_kind="laugh")
        photo = fam - 0.1
        dog_spots = dict(Cosmo=(170, Y_DOGS + 30), Pettie=(420, Y_DOGS + 60), Luna=(640, Y_DOGS + 40), Mooky=(860, Y_DOGS - 40),
                         Buddy=(900, Y_DOGS + 80))
        actors = []
        if t > with_mom - 0.4:
            mx, mph, mamt, _ = mover(t, [(with_mom - 0.4, -250), (with_mom + 1.0, 170)])
            mp, mb = walk_front(mph, mamt)
            mpose = dict(eye_open=blink(t, 7), look=(0.5, 0), **mp)
            if t > photo - 0.6:
                mpose.update(arm_r=(70, -10), mouth_kind="smile", look=(0, 0))
            actors.append((Y_BACK, "mom", dict(x=mx, y=Y_BACK - 10 - mb, s=MS * 0.9, **mpose)))
            for i, n in enumerate(DOGS):
                tx, ty = dog_spots[n]
                start = -300 - 160 * i if i % 2 == 0 else 1400 + 160 * i
                x, dph, damt, dd = mover(t, [(with_mom + 0.1 * i, start), (with_mom + 1.5 + 0.15 * i, tx)], step=32, fn=ease_out)
                face = 1 if dd > 0 else -1 if dd < 0 else (1 if tx < 540 else -1)
                up = beat_bounce(t + i * 0.2, 10) if t > photo + 0.3 else 0
                actors.append((ty, "dog", dict(name=n, x=x, y=ty, phase=dph, run=damt, facing=face, jump=up,
                                               tail=28 * math.sin(t * 15 + i), mouth_kind="open" if t > photo else "smile",
                                               eye_open=0.1 if photo < t < photo + 0.4 else blink(t, 11 + i))))
        if t > photo - 0.6:
            pose.update(look=(0, 0), mouth_kind="laugh", arm_l=(150, -10))
            wpose.update(look=(-0.3, 0), mouth_kind="laugh", arm_f=125)
            if photo < t < photo + 0.4:
                pose["eye_open"] = 0.1
                wpose["eye_open"] = 0.1
        actors.append((wy, "wolf", dict(x=wx, y=wy, **wpose)))
        actors.append((y + 1, "girl", dict(x=gx, y=y, **pose)))
        actors.sort(key=lambda a: a[0])
        for _, kind, kw in actors:
            x_, y_ = kw.pop("x"), kw.pop("y")
            if kind == "dog":
                n = kw.pop("name")
                self.dog(c, n, x_, y_, **kw)
            elif kind == "wolf":
                self.wolf(c, x_, y_, **kw)
            elif kind == "mom":
                self.mom(c, x_, y_, **kw)
            else:
                self.girl(c, x_, y_, **kw)
        # ---- weather on top
        if weather == "rain":
            hx, hy = toon.girl_hand(gx, y, GS, -1, 150, -25)
            tw.umbrella(c, hx + 20, hy + 40, 1.05 * back(seg(t, rain_on - 0.1, rain_on + 0.2), 2.4), tilt=12)
            tw.rain(c, t)
            for i, px in enumerate((gx - 140, wx + 150, gx + 120)):
                tw.puddle_splash(c, px, Y_MAIN + 20, t + i * 0.2, 0.5)
        if weather == "snow":
            tw.snow(c, t)
        if t > sun_back and t < with_mom:
            self.hearts_burst(c, t, sun_back + 0.6, (gx + wx) / 2, 1100, n=6, seed=21)
        # ---- family photo: flash + frame
        if t > photo:
            tw.flash(c, 0.9 * (1 - seg(t, photo, photo + 0.35)))
            k = back(seg(t, photo + 0.1, photo + 0.45), 1.6)
            if k > 0:
                with Xf(c, 540, 1250, -2 * k, k):
                    tw.photo_frame(c, -480, -560, 480, 470)
                    toon.text(c, "Our Family", 0, 548, 70, (236, 96, 140), WHITE, 0)
            self.hearts_burst(c, t, photo + 0.4, 540, 1100, n=10, spread=360, seed=23)

    def scene_end(self, c, t):
        """Hug a shy friend, say hi, a little love, The End, let's go play."""
        self.bg(c, "sunset")
        self.sky_life(c, t, "sunset")
        shy = self.wt("end", "shy")
        hug = self.wt("end", "hug")
        hi = self.wt("end", "hi")
        love = self.wt("end", "love")
        end_t = self.ev["the_end"]
        now = self.wt("end", "now")
        play = self.wt("end", "play")
        gx, wx = 330, 690
        hugging = hug - 0.3 < t < hi - 0.3
        if hugging:
            gx = kf(t, [(hug - 0.3, 330), (hug, wx - 240)])
        elif t > hi - 0.3:
            gx = kf(t, [(hi - 0.3, wx - 240), (hi + 0.1, 400)])
        pose = dict(eye_open=blink(t, 1), look=(0.6, 0))
        wpose = dict(facing=-1, tail=20 * math.sin(t * 10), eye_open=blink(t, 2), look=(0.3, 0))
        y = wy = Y_MAIN
        if t < hug - 0.3:  # shy friend
            k = ease(seg(t, shy - 0.5, shy))
            wpose.update(blush_a=0.9 * k, ear_droop=20 * k, head_tilt=-8 * k, arm_f=lerp(20, 150, k), look=(0, 0.8))
        if hugging:
            pose.update(arm_l=(50, 95), arm_r=(95, 15), eye_open=0.1, blush_a=0.9, head_tilt=8)
            wpose.update(arm_f=80, head_tilt=8, eye_open=0.1, blush_a=0.8, mouth_kind="smile")
        if hi - 0.3 < t < love - 0.2:  # say hi!
            a, _ = wave(t, hi - 0.3, love - 0.2)
            pose.update(arm_r=(a, -18), mouth_kind="open", look=(0, 0))
            wpose.update(arm_f=a, mouth_kind="laugh", look=(-0.2, 0))
        if t > love - 0.3:
            pose.update(hands_together=True, mouth_kind="smile", look=(0.3, -0.6), blush_a=0.8)
            wpose.update(mouth_kind="smile", look=(-0.3, -0.6), blush_a=0.6)
        # the gang runs in for "let's go out and play"
        actors = []
        if t > now - 0.5:
            mx, mph, mamt, _ = mover(t, [(now - 0.5, -260), (now + 0.9, 170)])
            mp, mb = walk_front(mph, mamt)
            mpose = dict(eye_open=blink(t, 7), **mp)
            if t > play - 0.2:
                mpose.update(arm_l=(150, -10), arm_r=(150, -10), mouth_kind="laugh")
            actors.append((Y_BACK, "mom", dict(x=mx, y=Y_BACK - mb - beat_bounce(t, 8) * (t > play), **mpose)))
            spots = dict(Cosmo=(170, Y_DOGS + 40), Pettie=(380, Y_DOGS + 70), Luna=(600, Y_DOGS + 50), Mooky=(850, Y_DOGS - 30), Buddy=(820, Y_DOGS + 90))
            for i, n in enumerate(DOGS):
                tx, ty = spots[n]
                start = -300 - 150 * i if i % 2 == 0 else 1400 + 150 * i
                x, dph, damt, dd = mover(t, [(now - 0.4 + 0.1 * i, start), (now + 1.0 + 0.12 * i, tx)], step=32, fn=ease_out)
                up, sq = hops(t, [play - 0.1 + 0.08 * i, play + 0.6 + 0.08 * i, play + 1.2 + 0.08 * i, play + 1.8 + 0.08 * i], 0.5, 90)
                face = 1 if dd > 0 else -1 if dd < 0 else (1 if tx < 540 else -1)
                actors.append((ty, "dog", dict(name=n, x=x, y=ty, phase=dph, run=damt, facing=face, jump=up, sx=sq[0], sy=sq[1],
                                               tail=28 * math.sin(t * 15 + i), mouth_kind="open", eye_open=blink(t, 11 + i))))
        if t > play - 0.2:
            jumps = [play - 0.1 + 0.6 * i for i in range(4)]
            up, sq = hops(t, jumps, 0.5, 110)
            y -= up
            wy -= hops(t, [j + 0.1 for j in jumps], 0.5, 120)[0]
            pose.update(arm_l=(150, -10), arm_r=(150, -10), mouth_kind="laugh", hands_together=False)
            wpose.update(arm_f=130, mouth_kind="laugh")
        actors.append((wy, "wolf", dict(x=wx, y=wy, **wpose)))
        actors.append((y + 1, "girl", dict(x=gx, y=y, **pose)))
        actors.sort(key=lambda a: a[0])
        for _, kind, kw in actors:
            x_, y_ = kw.pop("x"), kw.pop("y")
            if kind == "dog":
                n = kw.pop("name")
                self.dog(c, n, x_, y_, **kw)
            elif kind == "wolf":
                if hugging:
                    self.wolf(c, x_, y_, parts="back", **kw)
                else:
                    self.wolf(c, x_, y_, **kw)
            elif kind == "mom":
                self.mom(c, x_, y_, **kw)
            else:
                self.girl(c, x_, y_, **kw)
                if hugging:
                    self.wolf(c, wx, wy, parts="arm", **wpose)
        self.hearts_burst(c, t, hug - 0.1, 600, 1120, n=8, spread=200, seed=31)
        if t > love - 0.3:  # a little love goes a long way: a big glowing heart
            k = back(seg(t, love - 0.3, love + 0.4), 1.8)
            fade = 1 - seg(t, end_t - 0.3, end_t + 0.2)
            tw.heart(c, 545, 880 - 20 * math.sin(t * 2), 3.4 * k * (1 + 0.05 * math.sin(t * 8)), a=0.9 * fade)
            self.hearts_burst(c, t, love, 545, 1000, n=12, spread=420, rise=420, dur=2.4, seed=33)
        if t > end_t - 0.1:  # The End
            k = back(seg(t, end_t - 0.1, end_t + 0.4), 2.2)
            cols = [(255, 110, 140), (255, 170, 80), (255, 214, 70), (120, 210, 120), (100, 180, 255), (180, 140, 240)]
            letters = "The End"
            f = toon.font("Chewy-Regular.ttf", 150)
            total = f.measureText(letters)
            x = W / 2 - total / 2
            for i, ch in enumerate(letters):
                cw = f.measureText(ch)
                if ch != " ":
                    yb = 720 - 18 * math.sin(t * 5 + i * 0.7)
                    with Xf(c, x + cw / 2, yb - 50, 4 * math.sin(t * 3 + i), k):
                        toon.text(c, ch, 0, 50, 150, cols[i % len(cols)], PLUM, 16)
                x += cw
            self.confetti_burst(c, t, end_t, 540, 760, 50, seed=9)
            for i in range(6):
                tw.sparkle(c, 140 + 160 * i, 600 + 40 * math.sin(i * 2), 20, a=bump(t, end_t + 0.15 * i, 1.4), rot=t * 90)

    # ============================================================ FRAME
    SCENE_FN = {"title": "scene_intro", "bunny": "scene_intro", "park": "scene_park", "invisible": "scene_invisible",
                "hug": "scene_glade", "poof": "scene_glade", "family": "scene_family", "end": "scene_end"}

    def scene_at(self, t):
        for s in self.tl["scenes"]:
            if s["t0"] <= t < s["t1"]:
                return s["id"]
        return self.tl["scenes"][-1]["id"]

    def draw_scene(self, c, t, sid):
        getattr(self, self.SCENE_FN[sid])(c, t)

    def frame(self, t):
        arr = np.zeros((H, W, 4), np.uint8)
        c = skia.Surface(arr).getCanvas()
        sid = self.scene_at(t)
        # iris wipe: close on the old scene, open on the new one
        ids = [s["id"] for s in self.tl["scenes"]]
        i = ids.index(sid)
        nxt = ids[i + 1] if i + 1 < len(ids) else None
        r_full = 1400.0
        if nxt in self.iris and t > self.sc[nxt]["t0"] - 0.32:
            self.draw_scene(c, t, sid)
            k = seg(t, self.sc[nxt]["t0"] - 0.32, self.sc[nxt]["t0"])
            self.iris_mask(c, self.iris[nxt], r_full * (1 - ease_in(k)))
        elif sid in self.iris and t < self.sc[sid]["t0"] + 0.32:
            self.draw_scene(c, t, sid)
            k = seg(t, self.sc[sid]["t0"], self.sc[sid]["t0"] + 0.32)
            self.iris_mask(c, self.iris[sid], r_full * ease_out(k))
        else:
            self.draw_scene(c, t, sid)
        # caption box
        ba = self.caps.box_alpha(t)
        if ba > 0:
            x0, y0, x1, y1 = BOX
            c.drawPath(toon.rrect(x0 + 4, y0 + 10, x1 + 4, y1 + 10, 46), toon.fill_paint(OUT, 0.18 * ba, blur=10))
            c.drawPath(toon.rrect(x0, y0, x1, y1, 46), toon.fill_paint(WHITE, 0.94 * ba))
            c.drawPath(toon.rrect(x0, y0, x1, y1, 46), toon.stroke_paint((190, 170, 220), 5, ba))
        rgb = arr[..., :3]
        y0, y1 = CAP_TOP - 40, CAP_BOT + 40
        band = rgb[y0:y1].astype(np.float32)
        self.caps.draw(band, t, y0)
        rgb[y0:y1] = np.clip(band, 0, 255).astype(np.uint8)
        return np.ascontiguousarray(rgb)

    @staticmethod
    def iris_mask(c, center, r):
        p = skia.Path()
        p.addRect(skia.Rect.MakeLTRB(-10, -10, W + 10, H + 10))
        hole = skia.Path()
        hole.addCircle(center[0], center[1], max(r, 0.01))
        mask = skia.Op(p, hole, skia.PathOp.kDifference_PathOp)
        c.drawPath(mask, toon.fill_paint((52, 38, 72)))
        if r > 1:
            c.drawPath(hole, toon.stroke_paint((255, 214, 77), 10))


# ----------------------------------------------------------------- driver
_S = None


def _init():
    global _S
    _S = Story()


def _chunk(args):
    k, f0, f1, path = args
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
           "-crf", "8", "-pix_fmt", "yuv420p", path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(f0, f1):
        p.stdin.write(_S.frame(f / FPS).tobytes())
    p.stdin.close()
    p.wait()
    return k


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", nargs="*", type=float)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    os.makedirs(BUILD, exist_ok=True)
    if args.preview is not None:
        s = Story()
        out = os.path.join(BUILD, "cpreview")
        os.makedirs(out, exist_ok=True)
        for t in args.preview:
            cv2.imwrite(os.path.join(out, f"t{t:07.2f}.png"), cv2.cvtColor(s.frame(t), cv2.COLOR_RGB2BGR))
        print("previews in", out)
        return
    T = timeline.load()["duration_video"]
    n = int(round(T * FPS))
    step = math.ceil(n / args.workers)
    jobs = [(k, k * step, min(n, (k + 1) * step), os.path.join(BUILD, f"cchunk{k}.mp4")) for k in range(args.workers)]
    with Pool(args.workers, initializer=_init) as pool:
        for k in pool.imap_unordered(_chunk, jobs):
            print("chunk", k, "done", flush=True)
    lst = os.path.join(BUILD, "cchunks.txt")
    with open(lst, "w") as f:
        for _, _, _, p in jobs:
            f.write(f"file '{p}'\n")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c", "copy", os.path.join(BUILD, "cartoon_noaudio.mp4")], check=True)
    for _, _, _, p in jobs:
        os.remove(p)
    print("frames:", n, "->", os.path.join(BUILD, "cartoon_noaudio.mp4"))


if __name__ == "__main__":
    main()
