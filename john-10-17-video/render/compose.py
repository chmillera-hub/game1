"""Composite rendered shots into the final video: cross-dissolves, title/chapter/end cards,
subtitles (Cormorant Garamond, as in the reference), film grain, and the audio mix.

Usage: python3 -I render/compose.py <frames_dir> <fonts_dir> <audio.wav> <out.mp4> [--preview t1,t2,...]
"""
import json, math, os, subprocess, sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRAMES, FONTS, AUDIO, OUT = sys.argv[1:5]
PREVIEW = None
if "--preview" in sys.argv:
    PREVIEW = [float(x) for x in sys.argv[sys.argv.index("--preview") + 1].split(",")]
W, H, FPS = 720, 1280, 24

shots = json.load(open(f"{ROOT}/script/shots.json"))["shots"]
tl = json.load(open(f"{ROOT}/script/timeline.json"))
script = json.load(open(f"{ROOT}/script/narration.json"))
TOTAL = tl["duration"]
NFRAMES = math.ceil(TOTAL * FPS)


def font(size, weight=500, italic=False):
    f = ImageFont.truetype(f"{FONTS}/CormorantGaramond{'-Italic' if italic else ''}[wght].ttf", size, layout_engine=ImageFont.Layout.RAQM)
    f.set_variation_by_axes([weight])
    return f


def smoothstep(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


# ---------------- text layers (RGBA, full frame) ----------------
LNUM = ["lnum"]


def tracked_width(f, text, track):
    return sum(f.getlength(ch, features=LNUM) for ch in text) + track * (len(text) - 1)


def draw_tracked(d, xy, text, f, fill, track):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill, features=LNUM)
        x += f.getlength(ch, features=LNUM) + track


def layer_with_shadow(draw_fn, fg, shadow=(0, 0, 0), blur=3.0, shadow_alpha=0.85, wide_blur=11.0, wide_alpha=0.35, glow=None):
    """draw_fn(draw, fill) draws the text; returns RGBA layer with soft shadow/glow underneath."""
    mask = Image.new("L", (W, H), 0)
    draw_fn(ImageDraw.Draw(mask), 255)
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for b, a, col in ([(wide_blur, wide_alpha, shadow), (blur, shadow_alpha, shadow)] if glow is None else glow):
        m = mask.filter(ImageFilter.GaussianBlur(b))
        m = m.point(lambda v, a=a: int(v * a))
        out.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), c) for c in col], m)))
    out.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), c) for c in fg], mask)))
    return out


SUB_FONT = font(35, 520)
SUB_COLOR = (251, 247, 238)


def subtitle_layer(text):
    lines = text.split("|")
    f = SUB_FONT
    while max(f.getlength(l) for l in lines) > 650:
        f = font(f.size - 1, 520)
    lh = 50
    cy = int(0.705 * H)
    y0 = cy - (len(lines) * lh) // 2

    def fn(d, fill):
        for i, l in enumerate(lines):
            w = f.getlength(l)
            d.text(((W - w) / 2, y0 + i * lh), l, font=f, fill=fill)
    return layer_with_shadow(fn, SUB_COLOR)


def smallcaps_layer(text, cy=0.56):
    """Large small-caps line with glow, like the reference's closing 'HE HAS DONE IT!'."""
    lines = text.replace("”", "").split("|")
    big, small = font(58, 600), font(45, 600)
    track = 2.5
    lh = 66
    y0 = int(cy * H) - (len(lines) * lh) // 2

    def runs(line):
        out = []
        for wi, word in enumerate(line.split(" ")):
            for ci, ch in enumerate(word):
                out.append((ch.upper(), big if (ci == 0 and ch.isalpha() and ch.isupper()) or (ci == 0 and wi == 0) else small))
            out.append((" ", small))
        return out[:-1]

    def fn(d, fill):
        for i, line in enumerate(lines):
            rr = runs(line)
            w = sum(fo.getlength(ch) + track for ch, fo in rr) - track
            x = (W - w) / 2
            base = y0 + i * lh
            for ch, fo in rr:
                asc = fo.getmetrics()[0]
                d.text((x, base + (big.getmetrics()[0] - asc)), ch, font=fo, fill=fill)
                x += fo.getlength(ch) + track
    return layer_with_shadow(fn, (255, 248, 234), glow=[(16, 0.45, (40, 25, 10)), (5, 0.8, (30, 18, 8)), (24, 0.25, (255, 220, 160))])


def card_layer(heading, sub=None, ref=None, dark=True, y=0.27, heading_size=66, sub_size=31, italic_sub=True, track_em=0.12):
    hf = font(heading_size, 600)
    sf = font(sub_size, 500, italic=italic_sub)
    rf = font(24, 500)
    track = heading_size * track_em
    ink = (28, 19, 11) if dark else (250, 244, 232)
    glow = [(18, 0.75, (255, 248, 232)), (6, 0.6, (255, 250, 240))] if dark else [(18, 0.6, (10, 8, 6)), (5, 0.7, (10, 8, 6))]
    hy = int(y * H) - heading_size // 2
    ly = int((y + 0.052) * H)
    sy = int((y + 0.075) * H)
    ry = sy + int(sub_size * 1.45)

    def fn(d, fill):
        w = tracked_width(hf, heading, track)
        draw_tracked(d, ((W - w) / 2, hy), heading, hf, fill, track)
        d.rectangle([W / 2 - 52, ly, W / 2 + 52, ly + 1], fill=fill)
        if sub:
            d.text(((W - sf.getlength(sub)) / 2, sy), sub, font=sf, fill=fill)
        if ref:
            d.text(((W - rf.getlength(ref)) / 2, ry), ref, font=rf, fill=fill)
    return layer_with_shadow(fn, ink, glow=glow)


def to_np(layer):
    a = np.asarray(layer).astype(np.float32) / 255.0
    return a[..., :3], a[..., 3:4]


# ---------------- frame access ----------------
def load_shot_frame(shot, n):
    n = min(max(n, shot["frame_start"]), shot["frame_end"])
    p = f"{FRAMES}/{shot['id']}/{n:05d}.jpg"
    im = Image.open(p).convert("RGB")
    if im.size != (W, H):
        im = im.resize((W, H), Image.LANCZOS)
    return np.asarray(im).astype(np.float32) / 255.0


def frame_at(n):
    t = n / FPS
    acc, wsum = None, 0.0
    for i, s in enumerate(shots):
        xin, xout = s["xfade_in"], s["xfade_out"]
        a_in = 1.0 if i == 0 else smoothstep(s["start"] - xin / 2, s["start"] + xin / 2, t)
        a_out = 1.0 if i == len(shots) - 1 else 1.0 - smoothstep(s["end"] - xout / 2, s["end"] + xout / 2, t)
        w = a_in * a_out
        if w <= 1e-4:
            continue
        img = load_shot_frame(s, n)
        acc = img * w if acc is None else acc + img * w
        wsum += w
    return acc / max(wsum, 1e-6)


# ---------------- overlays ----------------
def mean_luma(shot, n, box, default=0.6):
    if not os.path.exists(f"{FRAMES}/{shot['id']}/{min(max(n, shot['frame_start']), shot['frame_end']):05d}.jpg"):
        return default
    img = load_shot_frame(shot, n)
    x0, y0, x1, y1 = box
    reg = img[y0:y1, x0:x1]
    return float((reg * np.array([0.2126, 0.7152, 0.0722])).sum(-1).mean())


overlays = []  # (t_in, t_out, fade_in, fade_out, rgb, alpha)
title_shot = shots[0]
dark = mean_luma(title_shot, 48, (80, 250, 640, 520)) > 0.5
overlays.append((0.35, 4.55, 0.7, 0.6, *to_np(card_layer(script["title"]["heading"], script["title"]["sub"], dark=dark))))
chap = next(s for s in shots if s["id"] == "S21_chapter")
dark = mean_luma(chap, int((chap["start"] + chap["end"]) / 2 * FPS), (80, 250, 640, 520), default=0.1) > 0.5
overlays.append((chap["start"] + 0.15, chap["end"] - 0.15, 0.6, 0.6, *to_np(card_layer(script["chapter"]["heading"], script["chapter"]["sub"], dark=dark))))
endshot = shots[-1]
dark = mean_luma(endshot, int((endshot["start"] + 3) * FPS), (80, 280, 640, 560)) > 0.5
overlays.append((endshot["start"] + 0.9, TOTAL + 1, 1.0, 0.1, *to_np(card_layer(script["end"]["heading"], script["end"]["quote"], script["end"]["ref"], dark=dark, y=0.27, heading_size=46, sub_size=36, track_em=0.1))))
for u in tl["units"]:
    for s in u["subs"]:
        if u["style"] == "emph":
            rgb, al = to_np(smallcaps_layer(s["text"]))
            hide = s["hide"] + (1.2 if u["id"] == "u40" else 0.6)
            overlays.append((s["show"], hide, 0.35, 0.5, rgb, al))
        else:
            rgb, al = to_np(subtitle_layer(s["text"]))
            overlays.append((s["show"], s["hide"], 0.2, 0.22, rgb, al))
print(f"{len(overlays)} overlays prepared", flush=True)

rng = np.random.default_rng(7)
GRAIN = [rng.normal(0, 1, (H, W, 1)).astype(np.float32) for _ in range(8)]


def composite(n):
    t = n / FPS
    img = frame_at(n)
    for (t0, t1, fi, fo, rgb, al) in overlays:
        if t < t0 or t > t1:
            continue
        a = smoothstep(t0, t0 + fi, t) * (1.0 - smoothstep(t1 - fo, t1, t))
        if a <= 0:
            continue
        aa = al * a
        img = img * (1 - aa) + rgb * aa
    fade = smoothstep(0.0, 0.8, t) * (1.0 - smoothstep(TOTAL - 1.2, TOTAL - 0.05, t))
    img = img * fade
    img = img + GRAIN[n % 8] * (1.4 / 255.0) * (0.6 + 0.4 * img)
    return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)


if PREVIEW:
    for t in PREVIEW:
        n = int(t * FPS)
        Image.fromarray(composite(n)).save(f"{OUT}_{t:07.2f}.jpg", quality=92)
        print("preview", t)
    sys.exit(0)

cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
       "-i", AUDIO, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-tune", "film",
       "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
       "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
       "-metadata", "title=John 10 & 17", OUT]
proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
for n in range(NFRAMES):
    proc.stdin.write(composite(n).tobytes())
    if n % 240 == 0:
        print(f"frame {n}/{NFRAMES}", flush=True)
proc.stdin.close()
proc.wait()
print("done", OUT)
