"""Render the animated story as a portrait 1080x1920 video (no audio).

Layout: the drawing fills the top (with a scalloped cloud edge), the
read-along caption sits under it, and a grassy strip fills the bottom.
Frame 0 is already a complete cover (characters + title), so social apps
never show a blank first frame.

Usage:
  python render_video.py                 # full render -> build/video_noaudio.mp4
  python render_video.py --preview 0 7.6 # write preview PNGs for given times
"""
import argparse
import json
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import timeline  # noqa: E402

ART = os.path.join(ROOT, "art")
BUILD = os.path.join(ROOT, "build")
FONTS = os.path.join(ROOT, "fonts")

W, H, FPS = 1080, 1920, 30
WIN_H = 1300                  # art buffer height (scallops + border + shadow fit inside)
VIEW_H = 1215                 # the camera frames this much of it
EDGE_Y = 1180                 # straight part of the art window ends here
CAP_TOP, CAP_BOT = 1272, 1565
BPM_BEAT = 60 / 104

PLUM = (63, 45, 99)
CREAM = (255, 247, 236)


# ------------------------------------------------------------------ helpers
def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def ease_out_back(x, k=1.9):
    x = min(max(x, 0.0), 1.0) - 1
    return 1 + x * x * ((k + 1) * x + k)


def elastic(x):
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    return 1 + 2 ** (-9 * x) * math.sin((x * 6 - 0.75) * (2 * math.pi) / 3)


def lerp(a, b, x):
    return a + (b - a) * x


def premult(rgba):
    """uint8 RGBA -> float32 premultiplied (rgb*a in 0..255, a in 0..1)."""
    f = rgba.astype(np.float32)
    a = f[..., 3:4] / 255.0
    return np.concatenate([f[..., :3] * a, a], -1)


def load_rgba(name):
    bgra = cv2.imread(os.path.join(ART, name), cv2.IMREAD_UNCHANGED)
    return premult(cv2.cvtColor(bgra, cv2.COLOR_BGRA2RGBA))


def load_rgb(name):
    return cv2.cvtColor(cv2.imread(os.path.join(ART, name)), cv2.COLOR_BGR2RGB)


def pil_to_premult(img):
    return premult(np.asarray(img.convert("RGBA")))


def blit(dst, spr, x, y, opacity=1.0):
    """Composite a premultiplied sprite with its top-left at (x, y)."""
    h, w = spr.shape[:2]
    x, y = int(round(x)), int(round(y))
    x0, y0 = max(x, 0), max(y, 0)
    x1, y1 = min(x + w, dst.shape[1]), min(y + h, dst.shape[0])
    if x1 <= x0 or y1 <= y0 or opacity <= 0.002:
        return
    s = spr[y0 - y:y1 - y, x0 - x:x1 - x]
    d = dst[y0:y1, x0:x1]
    a = s[..., 3:4] * opacity
    d *= 1 - a
    d += s[..., :3] * opacity


def draw_sprite(dst, spr, cx, cy, scale=1.0, angle=0.0, opacity=1.0, anchor=(0.5, 0.5), sx=1.0, sy=1.0):
    """Place a premultiplied sprite: anchor point -> (cx, cy), then scale/rotate."""
    if opacity <= 0.002 or scale <= 0.005:
        return
    h, w = spr.shape[:2]
    ax, ay = anchor[0] * w, anchor[1] * h
    kx, ky = scale * sx, scale * sy
    c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    A = np.array([[c * kx, -s * ky], [s * kx, c * ky]], np.float64)
    t = np.array([cx, cy]) - A @ np.array([ax, ay])
    corners = np.array([[0, 0], [w, 0], [0, h], [w, h]], np.float64) @ A.T + t
    bx0, by0 = np.floor(corners.min(0)).astype(int) - 1
    bx1, by1 = np.ceil(corners.max(0)).astype(int) + 1
    bx0c, by0c = max(bx0, 0), max(by0, 0)
    bx1c, by1c = min(bx1, dst.shape[1]), min(by1, dst.shape[0])
    if bx1c <= bx0c or by1c <= by0c:
        return
    M = np.hstack([A, (t - [bx0c, by0c])[:, None]]).astype(np.float32)
    warped = cv2.warpAffine(spr, M, (bx1c - bx0c, by1c - by0c), flags=cv2.INTER_LINEAR,
                            borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    blit(dst, warped, bx0c, by0c, opacity)


def font(path, size, weight=None):
    f = ImageFont.truetype(os.path.join(FONTS, path), size)
    if weight is not None:
        f.set_variation_by_axes([weight, 100])
    return f


# ------------------------------------------------------------ sprite shapes
def make_sparkle(r=40, color=(255, 250, 200)):
    s = 4 * r
    img = np.zeros((s, s), np.float32)
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32) - s / 2 + 0.5
    d = np.sqrt(xx ** 2 + yy ** 2) / r
    star = np.maximum(np.exp(-(np.abs(xx) / (0.09 * r)) ** 1.2) * np.exp(-(np.abs(yy) / (1.6 * r)) ** 2),
                      np.exp(-(np.abs(yy) / (0.09 * r)) ** 1.2) * np.exp(-(np.abs(xx) / (1.6 * r)) ** 2))
    img = np.clip(star + 0.55 * np.exp(-(d / 0.35) ** 2), 0, 1)
    rgb = np.ones((s, s, 3), np.float32) * np.array(color, np.float32)
    rgb = rgb * 0.6 + 255 * 0.4 * img[..., None]
    return np.concatenate([rgb * img[..., None], img[..., None]], -1)


def make_heart(size=80, color=(255, 92, 141)):
    big = size * 4
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pts = []
    for i in range(200):
        a = 2 * math.pi * i / 200
        x = 16 * math.sin(a) ** 3
        y = 13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a)
        pts.append((big / 2 + x * big / 36, big / 2 - y * big / 36 + big * 0.03))
    d.polygon(pts, fill=(255, 255, 255, 255))
    inner = [(big / 2 + (x - big / 2) * 0.86, big / 2 + (y - big / 2) * 0.86) for x, y in pts]
    d.polygon(inner, fill=color + (255,))
    d.ellipse([big * 0.27, big * 0.28, big * 0.40, big * 0.40], fill=(255, 255, 255, 170))
    return pil_to_premult(img.resize((size, size), Image.LANCZOS))


def make_puff(r=90):
    s = 2 * r + 8
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32) - s / 2
    d = np.sqrt(xx ** 2 + yy ** 2) / r
    a = np.clip(1.15 - d ** 3, 0, 1) * 0.92
    shade = 255 - 22 * np.clip((yy / r + 0.2), 0, 1)
    rgb = np.stack([shade, shade, shade * 0.99 + 2], -1)
    return np.concatenate([rgb * a[..., None], a[..., None]], -1).astype(np.float32)


def make_confetti(color, w=18, h=30):
    return premult(np.dstack([np.full((h, w, 3), color, np.uint8), np.full((h, w), 255, np.uint8)]))


def make_star_confetti(color, size=40):
    img = Image.new("RGBA", (size * 4, size * 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = size * 2
    pts = []
    for i in range(10):
        r = size * 1.8 if i % 2 == 0 else size * 0.8
        a = -math.pi / 2 + i * math.pi / 5
        pts.append((c + r * math.cos(a), c + r * math.sin(a)))
    d.polygon(pts, fill=color + (255,))
    return pil_to_premult(img.resize((size, size), Image.LANCZOS))


def make_butterfly(color, size=70):
    """Two wing frames: open and closed (squashed)."""
    out = []
    for open_ in (1.0, 0.35):
        img = Image.new("RGBA", (size * 4, size * 4), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        c = size * 2
        ww = size * 1.6 * open_
        for side in (-1, 1):
            x0 = c if side > 0 else c - ww
            d.ellipse([x0, c - size * 1.5, x0 + ww, c + size * 0.1], fill=color + (255,), outline=(90, 60, 110, 255), width=6)
            d.ellipse([x0 + ww * 0.15, c - size * 0.1, x0 + ww * 0.85, c + size * 1.0], fill=color + (255,), outline=(90, 60, 110, 255), width=6)
            d.ellipse([x0 + ww * 0.35, c - size * 1.0, x0 + ww * 0.65, c - size * 0.6], fill=(255, 255, 255, 200))
        d.rounded_rectangle([c - 10, c - size * 1.2, c + 10, c + size * 0.9], radius=10, fill=(90, 60, 110, 255))
        out.append(pil_to_premult(img.resize((size, size), Image.LANCZOS)))
    return out


def make_label(text, fill, size=54, paw=True, pad=26):
    f = font("Fredoka-Variable.ttf", size, 600)
    tw = int(f.getlength(text))
    icon = int(size * 1.0) if paw else 0
    wpx, hpx = tw + 2 * pad + (icon + 12 if paw else 0), int(size * 1.55)
    sc = 3
    img = Image.new("RGBA", ((wpx + 16) * sc, (hpx + 20) * sc), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([8 * sc, 12 * sc, (wpx + 8) * sc, (hpx + 12) * sc], radius=hpx * sc // 2, fill=(70, 40, 90, 70))
    d.rounded_rectangle([6 * sc, 6 * sc, (wpx + 6) * sc, (hpx + 6) * sc], radius=hpx * sc // 2,
                        fill=fill + (255,), outline=(255, 255, 255, 255), width=6 * sc)
    img = img.resize((wpx + 16, hpx + 20), Image.LANCZOS)
    d = ImageDraw.Draw(img)
    x = 6 + pad
    if paw:  # little paw print
        cx, cy, r = x + icon / 2, 6 + hpx / 2 + 4, icon / 2
        pc = (255, 255, 255, 255)
        d.ellipse([cx - r * 0.55, cy - r * 0.15, cx + r * 0.55, cy + r * 0.75], fill=pc)
        for ox, oy in ((-0.62, -0.38), (-0.22, -0.78), (0.22, -0.78), (0.62, -0.38)):
            d.ellipse([cx + ox * r - r * 0.22, cy + oy * r - r * 0.26, cx + ox * r + r * 0.22, cy + oy * r + r * 0.26], fill=pc)
        x += icon + 12
    d.text((x, 6 + hpx / 2), text, font=f, fill=(255, 255, 255, 255), anchor="lm",
           stroke_width=4, stroke_fill=(70, 40, 90, 255))
    return pil_to_premult(img)


def make_burst(text, r=200):
    s = int(r * 2.4)
    sc = 2
    img = Image.new("RGBA", (s * sc, s * sc), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = s * sc / 2
    for rad, col in ((r * 1.08, (255, 120, 40)), (r * 0.98, (255, 214, 60))):
        pts = []
        for i in range(28):
            rr = rad * sc * (1.0 if i % 2 == 0 else 0.72)
            a = i * math.pi / 14
            pts.append((c + rr * math.cos(a), c + rr * math.sin(a)))
        d.polygon(pts, fill=col + (255,))
    img = img.resize((s, s), Image.LANCZOS)
    d = ImageDraw.Draw(img)
    f = font("Chewy-Regular.ttf", int(r * 0.62))
    d.text((s / 2, s / 2), text, font=f, fill=(255, 255, 255, 255), anchor="mm", stroke_width=10, stroke_fill=PLUM + (255,))
    return pil_to_premult(img)


# ------------------------------------------------------------ static layers
def scallop_mask(scale=2):
    """1 inside the art window (straight top part + a row of cloud bumps)."""
    m = Image.new("L", (W * scale, WIN_H * scale), 0)
    d = ImageDraw.Draw(m)
    d.rectangle([0, 0, W * scale, EDGE_Y * scale], fill=255)
    r = 62
    for i, cx in enumerate(range(-20, W + 120, 118)):
        cy = EDGE_Y + (8 if i % 2 else -2)
        d.ellipse([(cx - r) * scale, (cy - r) * scale, (cx + r) * scale, (cy + r) * scale], fill=255)
    m = m.resize((W, WIN_H), Image.LANCZOS)
    return np.asarray(m).astype(np.float32) / 255.0


def build_static():
    base = np.zeros((H, W, 3), np.float32)
    base[:] = CREAM
    # soft polka dots in the caption panel
    rng = np.random.default_rng(11)
    dots = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(dots)
    pal = [(255, 205, 220), (205, 230, 255), (215, 245, 215), (255, 236, 190), (230, 215, 255)]
    for _ in range(46):
        x, y = rng.uniform(0, W), rng.uniform(EDGE_Y + 60, 1700)
        r = rng.uniform(6, 15)
        d.ellipse([x - r, y - r, x + r, y + r], fill=pal[rng.integers(len(pal))] + (150,))
    # grassy hill + flowers along the bottom
    hill = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hill)
    for base_y, amp, col, ph in ((1630, 26, (170, 222, 140), 0.0), (1688, 20, (128, 199, 104), 1.7)):
        pts = [(0, H)] + [(x, base_y + amp * math.sin(x / 150 + ph) + 10 * math.sin(x / 47 + ph * 2)) for x in range(0, W + 1, 8)] + [(W, H)]
        hd.polygon(pts, fill=col + (255,))
    for _ in range(140):  # crayon grass blades
        x = rng.uniform(0, W)
        y0 = 1700 + rng.uniform(0, 200)
        hd.line([(x, y0), (x + rng.uniform(-8, 8), y0 - rng.uniform(16, 34))], fill=(92, 168, 84, 200), width=3)
    flower_cols = [(255, 120, 160), (255, 210, 80), (170, 140, 255), (255, 160, 90), (120, 200, 255)]
    for i in range(11):
        x = 50 + i * 98 + rng.uniform(-20, 20)
        y = 1735 + rng.uniform(0, 130)
        hd.line([(x, y), (x, y + 40)], fill=(70, 150, 70, 255), width=5)
        col = flower_cols[i % len(flower_cols)]
        for k in range(5):
            a = k * 2 * math.pi / 5
            px, py = x + 15 * math.cos(a), y + 15 * math.sin(a)
            hd.ellipse([px - 11, py - 11, px + 11, py + 11], fill=col + (255,))
        hd.ellipse([x - 8, y - 8, x + 8, y + 8], fill=(255, 240, 150, 255))
    layer = Image.alpha_composite(dots, hill)
    blit(base, pil_to_premult(layer), 0, 0)

    mask = scallop_mask()
    # white border + soft shadow just outside the scalloped edge
    m8 = (mask * 255).astype(np.uint8)
    border = cv2.dilate(m8, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (19, 19))).astype(np.float32) / 255
    shadow = cv2.GaussianBlur(cv2.dilate(m8, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21))), (0, 0), 9).astype(np.float32) / 255
    sh = np.zeros((H, W), np.float32)
    sh[8:WIN_H] = shadow[:WIN_H - 8] * 0.22
    base *= (1 - sh[..., None])
    bl = np.zeros((H, W), np.float32)
    bl[:WIN_H] = border
    base = base * (1 - bl[..., None]) + 255 * bl[..., None]
    return base, mask


# ------------------------------------------------------------- caption text
class Captions:
    def __init__(self, tl):
        self.pages = []
        for sc in tl["scenes"]:
            for p in sc["pages"]:
                big = p["show"] in ("Bunny Girl and Wolf Dog!", "POOF!")
                self.pages.append(self.layout(p, big))

    def layout(self, page, big):
        if big:
            f = font("Chewy-Regular.ttf", 118 if len(page["show"]) > 10 else 150)
            lh, maxw = int(f.size * 1.08), 980
        else:
            size = 62
            while True:
                f = font("Fredoka-Variable.ttf", size, 600)
                lh, maxw = int(size * 1.24), 940
                lines = self.wrap(page["words"], f, maxw)
                if len(lines) * lh <= CAP_BOT - CAP_TOP - 10 or size <= 48:
                    break
                size -= 3
        lines = self.wrap(page["words"], f, maxw)
        # balance a two-line title
        space = f.getlength(" ")
        hgt = len(lines) * lh
        y0 = (CAP_TOP + CAP_BOT) / 2 - hgt / 2
        canvas = Image.new("RGBA", (W, CAP_BOT - CAP_TOP + 80), (0, 0, 0, 0))
        d = ImageDraw.Draw(canvas)
        oy = CAP_TOP - 40
        boxes = []
        stroke = 9 if big else 0
        fill = (255, 255, 255, 255) if big else PLUM + (255,)
        for li, line in enumerate(lines):
            lw = sum(f.getlength(w["w"]) for w in line) + space * (len(line) - 1)
            x = W / 2 - lw / 2 - 20
            y = y0 + li * lh + lh / 2
            for w in line:
                ww = f.getlength(w["w"])
                d.text((x, y - oy), w["w"], font=f, fill=fill, anchor="lm",
                       stroke_width=stroke, stroke_fill=PLUM + (255,))
                boxes.append(dict(x=x, y=y, w=ww, start=w["start"], end=w["end"], text=w["w"]))
                x += ww + space
        return dict(start=page["start"], end=page["end"], img=pil_to_premult(canvas), oy=oy,
                    boxes=boxes, font=f, big=big, lh=lh)

    @staticmethod
    def wrap(words, f, maxw):
        lines, cur = [], []
        for w in words:
            trial = cur + [w]
            if cur and f.getlength(" ".join(x["w"] for x in trial)) > maxw:
                lines.append(cur)
                cur = [w]
            else:
                cur = trial
        if cur:
            lines.append(cur)
        if len(lines) == 2:  # even out two-line captions
            allw = lines[0] + lines[1]
            best = None
            for k in range(1, len(allw)):
                a = f.getlength(" ".join(x["w"] for x in allw[:k]))
                b = f.getlength(" ".join(x["w"] for x in allw[k:]))
                if max(a, b) <= maxw and (best is None or max(a, b) < best[0]):
                    best = (max(a, b), k)
            if best:
                lines = [allw[:best[1]], allw[best[1]:]]
        return lines

    def page_at(self, t):
        idx = 0
        for i, p in enumerate(self.pages):
            if p["start"] - 0.12 <= t:
                idx = i
        return idx

    def draw(self, canvas, t):
        i = self.page_at(t)
        p = self.pages[i]
        k = min(1.0, (t - (p["start"] - 0.12)) / 0.22) if i > 0 else 1.0
        if k < 1.0 and i > 0:  # fade the previous page out
            q = self.pages[i - 1]
            blit(canvas, q["img"], 0, q["oy"] - 14 * ease(k), 1 - ease(k))
        self.highlight(canvas, p, t, ease(k))
        blit(canvas, p["img"], 0, p["oy"] + 18 * (1 - ease(k)), ease(k))
        self.pop_word(canvas, p, t, ease(k))

    def current(self, p, t):
        for b in p["boxes"]:
            if b["start"] - 0.03 <= t < b["end"]:
                return b
        return None

    def highlight(self, canvas, p, t, op):
        """Yellow pill gliding under the word being read."""
        if p["big"]:
            return
        b = self.current(p, t)
        if b is None:
            return
        prev = None
        for c in p["boxes"]:
            if c is b:
                break
            prev = c
        g = ease((t - b["start"]) / 0.09) if prev is not None and prev["y"] == b["y"] else 1.0
        x = lerp(prev["x"], b["x"], g) if prev is not None and prev["y"] == b["y"] else b["x"]
        w = lerp(prev["w"], b["w"], g) if prev is not None and prev["y"] == b["y"] else b["w"]
        pad, hh = 12, p["lh"] * 0.78
        x0, y0, x1, y1 = int(x - pad), int(b["y"] - hh / 2), int(x + w + pad), int(b["y"] + hh / 2 + 4)
        pill = np.zeros((y1 - y0 + 8, x1 - x0 + 8, 4), np.float32)
        img = Image.new("RGBA", (pill.shape[1] * 2, pill.shape[0] * 2), (0, 0, 0, 0))
        ImageDraw.Draw(img).rounded_rectangle([4, 6, img.width - 4, img.height - 2], radius=int(hh),
                                              fill=(255, 214, 77, 255))
        blit(canvas, pil_to_premult(img.resize((pill.shape[1], pill.shape[0]), Image.LANCZOS)), x0 - 4, y0 - 4, op)

    def pop_word(self, canvas, p, t, op):
        """Big title / POOF words grow and turn yellow as they are read."""
        if not p["big"]:
            return
        b = self.current(p, t)
        if b is None:
            return
        k = (t - b["start"]) / max(0.12, b["end"] - b["start"])
        s = 1 + 0.12 * math.sin(math.pi * min(1, k * 1.6))
        img = Image.new("RGBA", (int(b["w"] + 60), int(p["font"].size * 1.6)), (0, 0, 0, 0))
        ImageDraw.Draw(img).text((30, img.height / 2), b["text"], font=p["font"], fill=(255, 220, 70, 255),
                                 anchor="lm", stroke_width=9, stroke_fill=PLUM + (255,))
        draw_sprite(canvas, pil_to_premult(img), b["x"] - 30 + img.width / 2, b["y"], scale=s, opacity=op)


# ------------------------------------------------------------------- scenes
class Story:
    def __init__(self):
        self.tl = timeline.load()
        self.ev = self.tl["events"]
        self.scenes = {s["id"]: s for s in self.tl["scenes"]}
        self.order = [s["id"] for s in self.tl["scenes"]]
        cuts = json.load(open(os.path.join(ART, "cutouts.json")))
        self.cuts = cuts
        self.art = {n: load_rgb(n + ".png") for n in ("park", "hug", "family", "plate_end", "plate_poof", "the_end")}
        self.spr = {n: load_rgba("cut_" + n + ".png") for n in ("girl", "duo", "wolf_poof", "wolf_end")}
        # ghost Wolf Dog (for the invisible scene): pale, glowing version
        g = self.spr["wolf_poof"].copy()
        a = g[..., 3:4]
        rgb = g[..., :3] / np.maximum(a, 1e-4)
        rgb = rgb * 0.45 + 255 * 0.55
        self.ghost = np.concatenate([rgb * a, a], -1)
        # "THE END" lettering lifted from the drawing
        end = cv2.cvtColor(self.art["the_end"], cv2.COLOR_RGB2LAB)[..., 0]
        bh = cv2.morphologyEx(cv2.GaussianBlur(end, (0, 0), 1.0), cv2.MORPH_BLACKHAT,
                              cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17)))
        x0, y0, x1, y1 = 360, 920, 905, 1018
        alpha = np.clip((bh[y0:y1, x0:x1].astype(np.float32) - 12) / 40, 0, 1)
        txt = np.zeros((y1 - y0, x1 - x0, 4), np.float32)
        txt[..., :3] = np.array([52, 36, 80], np.float32) * alpha[..., None]
        txt[..., 3] = alpha
        pad = 30
        big = np.zeros((txt.shape[0] + 2 * pad, txt.shape[1] + 2 * pad, 4), np.float32)
        big[pad:-pad, pad:-pad] = txt
        glow = cv2.GaussianBlur(cv2.dilate(big[..., 3], np.ones((9, 9), np.uint8)), (0, 0), 6) * 0.95
        halo = np.concatenate([np.ones_like(big[..., :3]) * 255 * glow[..., None], glow[..., None]], -1)
        out = halo.copy()
        out[..., :3] = out[..., :3] * (1 - big[..., 3:4]) + big[..., :3]
        out[..., 3:4] = out[..., 3:4] + big[..., 3:4] * (1 - out[..., 3:4])
        self.end_text = out
        self.end_text_pos = ((x0 + x1) / 2, (y0 + y1) / 2)

        self.sparkle = make_sparkle()
        self.sparkle_pink = make_sparkle(color=(255, 200, 230))
        self.heart = make_heart()
        self.heart2 = make_heart(color=(255, 150, 190))
        self.puff = make_puff()
        cols = [(255, 92, 141), (255, 205, 60), (90, 200, 250), (140, 220, 110), (190, 130, 255), (255, 150, 70)]
        self.confetti = [make_star_confetti(c) for c in cols] + [make_confetti(c) for c in cols]
        self.butterflies = [make_butterfly((255, 170, 200)), make_butterfly((150, 205, 255)), make_butterfly((255, 215, 110))]
        self.burst = make_burst("POOF!")
        names = ["Cosmo", "Pettie", "Luna", "Mooky", "Buddy"]
        ncol = [(86, 176, 240), (255, 120, 170), (160, 120, 230), (255, 150, 80), (90, 190, 130)]
        self.name_tags = [make_label(n, c) for n, c in zip(names, ncol)]
        self.girl_tag = make_label("Bunny Girl", (60, 190, 200), size=58, paw=False)
        self.wolf_tag = make_label("Wolf Dog", (150, 130, 190), size=58, paw=False)
        self.rng_events()

    # deterministic particle schedules (so any frame can be drawn on its own)
    def rng_events(self):
        rng = np.random.default_rng(2024)
        self.sparkles = {}
        for sid, (x0, y0, x1, y1), rate in (("title", (60, 60, 1020, 1100), 6), ("bunny", (60, 60, 1020, 1100), 3),
                                            ("park", (40, 40, 1040, 1150), 2.5), ("invisible", (40, 80, 560, 1120), 4),
                                            ("hug", (100, 200, 1000, 1100), 2.5), ("poof", (40, 40, 1040, 1150), 5),
                                            ("family", (60, 60, 1020, 1100), 4), ("end", (60, 60, 1020, 1100), 5)):
            s = self.scenes[sid]
            n = int((s["t1"] - s["t0"] + 1.5) * rate)
            ts = np.sort(rng.uniform(s["t0"] - 0.8, s["t1"], n))
            self.sparkles[sid] = [(t, rng.uniform(x0, x1), rng.uniform(y0, y1), rng.uniform(0.35, 0.9), rng.uniform(0, 90))
                                  for t in ts]
        self.hearts = []
        for t in self.ev["hugs"]:
            for _ in range(9):
                self.hearts.append(("hug", t + rng.uniform(-0.1, 0.9), rng.uniform(-90, 90), rng.uniform(0.4, 0.85),
                                    rng.uniform(0, 6.28), rng.uniform(180, 330)))
        for t in self.ev["love"]:
            for _ in range(10):
                self.hearts.append(("hug", t + rng.uniform(-0.2, 2.6), rng.uniform(-110, 110), rng.uniform(0.35, 0.8),
                                    rng.uniform(0, 6.28), rng.uniform(200, 360)))
        for sid in ("family", "end"):
            s = self.scenes[sid]
            for t in np.arange(s["t0"] + 0.5, s["t1"] - 0.5, 0.45):
                self.hearts.append((sid, t + rng.uniform(0, 0.3), rng.uniform(-330, 330), rng.uniform(0.3, 0.65),
                                    rng.uniform(0, 6.28), rng.uniform(220, 420)))
        self.puffs = [(rng.uniform(0, 2 * math.pi), rng.uniform(140, 330), rng.uniform(0.55, 1.15), rng.uniform(0, 0.12))
                      for _ in range(16)]
        self.bursts = {}
        for key, t0 in (("poof", self.ev["poof"]), ("end", self.ev["the_end"])):
            self.bursts[key] = [(t0 + rng.uniform(0, 0.15), rng.uniform(0, 2 * math.pi), rng.uniform(500, 1300),
                                 rng.integers(len(self.confetti)), rng.uniform(-400, 400), rng.uniform(0.6, 1.2))
                                for _ in range(46)]

    # --- camera: map art coords -> art buffer (W x WIN_H)
    @staticmethod
    def cover_scale(img):
        return max(W / img.shape[1], VIEW_H / img.shape[0])

    def shot(self, img, cx, cy, zoom=1.0, shake=(0.0, 0.0)):
        s = self.cover_scale(img) * zoom
        hw, hh = W / 2 / s, VIEW_H / 2 / s  # keep the view inside the drawing
        cx = min(max(cx, hw), img.shape[1] - hw)
        cy = min(max(cy, hh), img.shape[0] - hh)
        M = np.float32([[s, 0, W / 2 - s * cx + shake[0]], [0, s, VIEW_H / 2 - s * cy + shake[1]]])
        buf = cv2.warpAffine(img, M, (W, WIN_H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        return buf.astype(np.float32), (s, cx, cy, shake)

    @staticmethod
    def to_win(cam, x, y):
        s, cx, cy, sh = cam
        return (x - cx) * s + W / 2 + sh[0], (y - cy) * s + VIEW_H / 2 + sh[1]

    # --- shared effects
    def draw_sparkles(self, buf, sid, t):
        for (t0, x, y, sz, ang) in self.sparkles[sid]:
            k = (t - t0) / 0.9
            if 0 <= k <= 1:
                a = math.sin(math.pi * k)
                spr = self.sparkle if int(x) % 3 else self.sparkle_pink
                draw_sprite(buf, spr, x, y, scale=sz * (0.4 + 0.6 * a), angle=ang + 60 * k, opacity=a)

    def draw_hearts(self, buf, cam, sid, t, origin):
        for (hs, t0, dx, sz, ph, rise) in self.hearts:
            if hs != sid:
                continue
            k = (t - t0) / 2.2
            if 0 <= k <= 1:
                ox, oy = origin
                x = ox + dx + 26 * math.sin(ph + k * 7)
                y = oy - rise * k
                wx, wy = self.to_win(cam, x, y)
                a = min(1, k * 5) * (1 - ease((k - 0.6) / 0.4))
                spr = self.heart if int(dx) % 2 else self.heart2
                draw_sprite(buf, spr, wx, wy, scale=sz * cam[0] * (0.6 + 0.5 * min(1, k * 4)),
                            angle=10 * math.sin(ph + k * 5), opacity=a)

    def draw_butterflies(self, buf, t, n=2, seed=0):
        for i in range(n):
            ph = seed * 1.7 + i * 2.1
            x = W / 2 + 380 * math.sin(t * 0.33 + ph) + 90 * math.sin(t * 1.1 + ph * 2)
            y = 330 + 180 * math.sin(t * 0.47 + ph * 1.3) + 50 * math.cos(t * 1.7 + ph)
            flap = (math.sin(t * 16 + ph * 5) > 0)
            spr = self.butterflies[(i + seed) % 3][0 if flap else 1]
            draw_sprite(buf, spr, x, y, scale=1.0, angle=15 * math.sin(t * 0.8 + ph))

    def draw_confetti(self, buf, key, t, origin):
        for (t0, ang, spd, ci, spin, sz) in self.bursts[key]:
            k = t - t0
            if 0 <= k <= 2.6:
                x = origin[0] + math.cos(ang) * spd * k * (1 - 0.25 * k)
                y = origin[1] + math.sin(ang) * spd * k * (1 - 0.25 * k) + 420 * k * k
                draw_sprite(buf, self.confetti[ci], x, y, scale=sz, angle=spin * k, opacity=1 - ease((k - 1.8) / 0.8))

    def beat_bounce(self, t, amp=1.0):
        ph = (t / BPM_BEAT) % 1.0
        return amp * abs(math.sin(math.pi * ph))

    # --- the scenes, each returns the art buffer (W x WIN_H, float RGB)
    def scene_title(self, t):
        buf, cam = self.shot(self.art["plate_end"], 611, 540, 1.0)
        b = self.beat_bounce(t)
        d = self.cuts["duo"]
        foot = (d["x"] + d["w"] / 2, d["y"] + d["h"])
        wx, wy = self.to_win(cam, *foot)
        draw_sprite(buf, self.spr["duo"], wx, wy - 18 * b, scale=cam[0] * 0.98, angle=2.2 * math.sin(t * math.pi / BPM_BEAT / 2),
                    anchor=(0.5, 1.0), sx=1 + 0.025 * (1 - b), sy=1 - 0.025 * (1 - b))
        self.draw_sparkles(buf, "title", t)
        return buf

    def scene_bunny(self, t):
        sc = self.scenes["bunny"]
        buf, cam = self.shot(self.art["plate_end"], 540, 540, 1.0 + 0.04 * ease((t - sc["t0"]) / 16))
        self.draw_butterflies(buf, t, 2, seed=0)
        g = self.cuts["girl"]
        fx, fy = 520, g["y"] + g["h"]
        up, sx, sy = 10 * self.beat_bounce(t), 1.0, 1.0
        for ht in self.ev["hops"]:
            k = (t - (ht - 0.06)) / 0.30
            if 0 <= k <= 1:
                up = 115 * math.sin(math.pi * k)
                sx, sy = 1 - 0.06 * math.sin(math.pi * k), 1 + 0.08 * math.sin(math.pi * k)
            elif 1 < k <= 1.35:
                q = math.sin(math.pi * (k - 1) / 0.35)
                sx, sy = 1 + 0.08 * q, 1 - 0.08 * q
        wx, wy = self.to_win(cam, fx, fy)
        draw_sprite(buf, self.spr["girl"], wx, wy - up * cam[0], scale=cam[0] * 1.02,
                    angle=2.5 * math.sin(t * 1.9), anchor=(0.5, 1.0), sx=sx, sy=sy)
        nt = self.ev["bunny_name"][0] if self.ev["bunny_name"] else sc["t0"] + 4
        k = (t - nt) / 0.5
        if k > 0:
            out = 1 - ease((t - (nt + 4.2)) / 0.4)
            draw_sprite(buf, self.girl_tag, 862, 300 + 6 * math.sin(t * 3), scale=ease_out_back(k), angle=-4, opacity=out)
        self.draw_sparkles(buf, "bunny", t)
        return buf

    def scene_park(self, t):
        sc = self.scenes["park"]
        img = self.art["park"]
        names = self.ev["dog_names"]
        k = ease((t - sc["t0"]) / max(1.0, names[0] - 0.6 - sc["t0"]))
        buf, cam = self.shot(img, 376, lerp(430, 950, k), 1.0 + 0.06 * ease((t - names[0]) / 5))
        self.draw_butterflies(buf, t, 2, seed=1)
        spots = [(800, 170), (880, 395), (790, 620), (880, 845), (790, 1065)]
        for i, (nt, (x, y)) in enumerate(zip(names, spots)):
            q = (t - (nt - 0.05)) / 0.45
            if q > 0:
                draw_sprite(buf, self.name_tags[i], x, y + 8 * math.sin(t * 2.6 + i), scale=elastic(q), angle=4 * math.sin(t * 1.5 + i * 2))
        self.draw_sparkles(buf, "park", t)
        return buf

    def scene_invisible(self, t):
        sc = self.scenes["invisible"]
        img = self.art["park"]
        z = 1.40 + 0.08 * ease((t - sc["t0"]) / (sc["t1"] - sc["t0"]))
        buf, cam = self.shot(img, 245, 815, z)
        # ghostly Wolf Dog over the faint drawing: shown at first, fades on
        # "invisible", flashes back on "Peek-a-boo!"
        inv = self.ev["invisible"][0] if self.ev["invisible"] else sc["t0"] + 9
        pk = self.ev["peekaboo"]
        a = 0.38 * ease((t - sc["t0"]) / 1.2) * (1 - ease((t - inv) / 0.9))
        a = max(a, 0.10 + 0.06 * math.sin(t * 2.3)) if t > inv else a
        a = max(a, 0.72 * ease((t - (pk - 0.05)) / 0.18) * (1 - ease((t - (pk + 0.75)) / 0.5)))
        wx, wy = self.to_win(cam, 92, 1000)
        draw_sprite(buf, self.ghost, wx, wy - 6 * math.sin(t * 2), scale=cam[0] * 0.56, angle=3 * math.sin(t * 1.3),
                    anchor=(0.5, 1.0), opacity=a)
        intro = self.scenes["invisible"]["pages"][0]
        wt = next((w["start"] for w in intro["words"] if w["w"].startswith("Wolf")), sc["t0"] + 1)
        q = (t - wt) / 0.5
        if q > 0:
            out = 1 - ease((t - (wt + 3.6)) / 0.4)
            draw_sprite(buf, self.wolf_tag, 760, 150 + 6 * math.sin(t * 3), scale=ease_out_back(q), angle=4, opacity=out)
        self.draw_sparkles(buf, "invisible", t)
        return buf

    def scene_hug(self, t):
        sc = self.scenes["hug"]
        img = self.art["hug"]
        h1 = self.ev["hugs"][0]
        k = ease((t - sc["t0"] - 1.0) / max(1.0, h1 - sc["t0"] - 1.5))
        z = lerp(1.0, 1.42, k)
        cx, cy = lerp(391, 455, k), lerp(560, 760, k)
        sd = self.ev["suddenly"]
        q = ease((t - (sd - 0.3)) / (self.ev["poof"] - sd + 0.3))
        z *= 1 + 0.30 * q
        amp = 9 * ease((t - self.ev["drumroll"][0]) / 1.2)
        shake = (amp * math.sin(t * 47), amp * math.cos(t * 39)) if amp > 0 else (0.0, 0.0)
        buf, cam = self.shot(img, cx, cy, z, shake)
        self.draw_hearts(buf, cam, "hug", t, (455, 690))
        self.draw_sparkles(buf, "hug", t)
        if q > 0:  # darken the edges while the drum rolls
            yy, xx = np.ogrid[0:WIN_H, 0:W]
            r = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - VIEW_H / 2) / (VIEW_H * 0.62)) ** 2)
            v = 1 - 0.55 * q * np.clip(r, 0, 1.4) ** 2
            buf *= v[..., None].astype(np.float32)
        return buf

    def scene_poof(self, t):
        sc = self.scenes["poof"]
        tp = self.ev["poof"]
        img = self.art["plate_poof"]
        z = 1.0 + 0.10 * (1 - ease((t - tp) / 1.5))
        buf, cam = self.shot(img, 367, 575, z)
        wpos = self.cuts["wolf_poof"]
        foot = (wpos["x"] + wpos["w"] / 2, wpos["y"] + wpos["h"])
        k = (t - tp) / 0.7
        pop = elastic(k) if k < 1 else 1.0
        up, sx, sy = 12 * self.beat_bounce(t), 1.0, 1.0
        for jt in self.ev["jumps"]:
            q = (t - jt) / 0.42
            if 0 <= q <= 1:
                up = 110 * math.sin(math.pi * q)
                sx, sy = 1 - 0.05 * math.sin(math.pi * q), 1 + 0.07 * math.sin(math.pi * q)
            elif 1 < q <= 1.3:
                p = math.sin(math.pi * (q - 1) / 0.3)
                sx, sy = 1 + 0.07 * p, 1 - 0.07 * p
        # smoke puffs behind him
        cxy = (foot[0], foot[1] - wpos["h"] * 0.45)
        for (ang, dist, sz, dl) in self.puffs:
            q = (t - tp - dl) / 1.3
            if 0 <= q <= 1:
                x = cxy[0] + math.cos(ang) * dist * ease(q * 1.4)
                y = cxy[1] + math.sin(ang) * dist * 0.8 * ease(q * 1.4)
                wx, wy = self.to_win(cam, x, y)
                draw_sprite(buf, self.puff, wx, wy, scale=cam[0] * sz * (0.6 + 0.9 * q), opacity=1 - ease((q - 0.35) / 0.65))
        wx, wy = self.to_win(cam, *foot)
        draw_sprite(buf, self.spr["wolf_poof"], wx, wy - up * cam[0], scale=cam[0] * pop,
                    angle=3 * math.sin(t * 2.2), anchor=(0.5, 1.0), sx=sx, sy=sy)
        # front puffs that hide his arrival
        for (ang, dist, sz, dl) in self.puffs[:7]:
            q = (t - tp + 0.05 - dl) / 0.9
            if 0 <= q <= 1:
                x = cxy[0] + math.cos(ang + 1) * dist * 0.5 * ease(q * 1.5)
                y = cxy[1] + math.sin(ang + 1) * dist * 0.4 * ease(q * 1.5)
                wx2, wy2 = self.to_win(cam, x, y)
                draw_sprite(buf, self.puff, wx2, wy2, scale=cam[0] * sz * (0.9 + 0.6 * q), opacity=(1 - ease(q / 0.8)) * 0.95)
        self.draw_confetti(buf, "poof", t, self.to_win(cam, *cxy))
        q = (t - tp) / 0.5
        if 0 <= t - tp <= 2.4:
            out = 1 - ease((t - tp - 1.8) / 0.5)
            draw_sprite(buf, self.burst, 790, 250, scale=0.95 * ease_out_back(q, 2.6), angle=-8 + 5 * math.sin(t * 6), opacity=out)
        self.draw_sparkles(buf, "poof", t)
        return buf

    def scene_family(self, t):
        sc = self.scenes["family"]
        img = self.art["family"]
        k = ease((t - sc["t0"]) / 6.5)
        buf, cam = self.shot(img, lerp(450, 418, k), lerp(690, 600, k), lerp(1.32, 1.0, k) * (1 + 0.03 * ease((t - sc["t0"] - 6.5) / 6)))
        self.draw_hearts(buf, cam, "family", t, (450, 900))
        for i in range(5):  # sparkles twinkling along the rainbow
            ph = (t * 0.9 + i * 0.2) % 1.0
            a = 0.25 + 1.0 * ((t * 0.31 + i * 0.37) % 1.0) * math.pi
            x, y = 430 + 380 * math.cos(math.pi - a % math.pi), 430 - 300 * math.sin(a % math.pi)
            wx, wy = self.to_win(cam, x, y)
            draw_sprite(buf, self.sparkle, wx, wy, scale=0.7 * math.sin(math.pi * ph), angle=40 * ph, opacity=math.sin(math.pi * ph))
        self.draw_sparkles(buf, "family", t)
        return buf

    def scene_end(self, t):
        sc = self.scenes["end"]
        buf, cam = self.shot(self.art["plate_end"], 611, 540, 1.0 + 0.05 * ease((t - sc["t0"]) / 10))
        d = self.cuts["duo"]
        foot = (d["x"] + d["w"] / 2, d["y"] + d["h"])
        wx, wy = self.to_win(cam, *foot)
        b = self.beat_bounce(t)
        draw_sprite(buf, self.spr["duo"], wx, wy - 14 * b, scale=cam[0] * 0.98, angle=2.5 * math.sin(t * math.pi / BPM_BEAT / 2),
                    anchor=(0.5, 1.0), sx=1 + 0.02 * (1 - b), sy=1 - 0.02 * (1 - b))
        self.draw_hearts(buf, cam, "end", t, (611, 640))
        te = self.ev["the_end"]
        k = (t - (te - 0.05)) / 0.6
        if k > 0:
            ex, ey = self.to_win(cam, *self.end_text_pos)
            draw_sprite(buf, self.end_text, ex, ey, scale=cam[0] * 1.05 * ease_out_back(k, 2.4) * (1 + 0.03 * math.sin(t * 5)),
                        angle=2 * math.sin(t * 2.5))
            self.draw_confetti(buf, "end", t, (W / 2, 560))
        self.draw_sparkles(buf, "end", t)
        return buf

    def art_buffer(self, sid, t):
        return getattr(self, "scene_" + sid)(t)


# --------------------------------------------------------------- the frames
class Renderer:
    def __init__(self):
        self.story = Story()
        self.base, self.mask = build_static()
        self.caps = Captions(self.story.tl)
        self.T = self.story.tl["duration_video"]

    def frame(self, t):
        st = self.story
        order, scenes = st.order, st.scenes
        cur = next((s for s in order if scenes[s]["t0"] <= t < scenes[s]["t1"]), order[-1])
        buf = st.art_buffer(cur, t)
        # crossfade into the next scene (POOF uses a white flash instead)
        i = order.index(cur)
        if i + 1 < len(order) and order[i + 1] != "poof":
            nxt = order[i + 1]
            k = (t - (scenes[nxt]["t0"] - 0.28)) / 0.28
            if 0 < k < 1:
                buf = buf * (1 - 0.5 * ease(k)) + st.art_buffer(nxt, max(t, scenes[nxt]["t0"])) * (0.5 * ease(k))
        if i > 0 and cur != "poof":
            prev = order[i - 1]
            k = (t - scenes[cur]["t0"]) / 0.28
            if 0 <= k < 1:
                buf = buf * (0.5 + 0.5 * ease(k)) + st.art_buffer(prev, scenes[cur]["t0"] - 1e-3) * (0.5 - 0.5 * ease(k))
        tp = st.ev["poof"]
        flash = max(0.0, 1 - abs(t - tp) / (0.10 if t < tp else 0.55))
        if flash > 0:
            buf = buf * (1 - flash) + 255 * flash
        canvas = self.base.copy()
        m = self.mask[..., None]
        canvas[:WIN_H] = canvas[:WIN_H] * (1 - m) + buf * m
        self.caps.draw(canvas, t)
        return np.clip(canvas, 0, 255).astype(np.uint8)


_R = None


def _init():
    global _R
    _R = Renderer()


def _render_chunk(args):
    k, f0, f1, path = args
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
           "-crf", "8", "-pix_fmt", "yuv420p", path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(f0, f1):
        p.stdin.write(_R.frame(f / FPS).tobytes())
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
        r = Renderer()
        out = os.path.join(BUILD, "preview")
        os.makedirs(out, exist_ok=True)
        for t in args.preview:
            cv2.imwrite(os.path.join(out, f"t{t:07.2f}.png"), cv2.cvtColor(r.frame(t), cv2.COLOR_RGB2BGR))
        print("previews in", out)
        return
    T = timeline.load()["duration_video"]
    n = int(round(T * FPS))
    step = math.ceil(n / args.workers)
    jobs = [(k, k * step, min(n, (k + 1) * step), os.path.join(BUILD, f"chunk{k}.mp4")) for k in range(args.workers)]
    with Pool(args.workers, initializer=_init) as pool:
        for k in pool.imap_unordered(_render_chunk, jobs):
            print("chunk", k, "done", flush=True)
    lst = os.path.join(BUILD, "chunks.txt")
    with open(lst, "w") as f:
        for _, _, _, p in jobs:
            f.write(f"file '{p}'\n")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c", "copy", os.path.join(BUILD, "video_noaudio.mp4")], check=True)
    for _, _, _, p in jobs:
        os.remove(p)
    print("frames:", n, "->", os.path.join(BUILD, "video_noaudio.mp4"))


if __name__ == "__main__":
    main()
