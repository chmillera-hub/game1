import json, wave, subprocess, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 24
SR = 22050
segs = json.load(open("segs.json"))
INTRO, GAP, OUTRO = 2.4, 1.6, 3.2

# ---- timeline
t = INTRO
for i, s in enumerate(segs):
    with wave.open(f"seg{i}.wav") as w:
        s["dur"] = w.getnframes() / w.getframerate()
        s["pcm"] = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    s["start"] = t
    s["end"] = t + s["dur"]
    t = s["end"] + (GAP if i < len(segs) - 1 else 0)
TOTAL = t + OUTRO
print("total seconds", round(TOTAL, 2))

# ---- audio: narration + soft pad
n = int(TOTAL * SR)
voice = np.zeros(n, np.float32)
for s in segs:
    a = int(s["start"] * SR)
    voice[a:a + len(s["pcm"])] += s["pcm"]
tt = np.arange(n) / SR
pad = np.zeros(n, np.float32)
for f, g in [(110.0, .5), (164.81, .35), (220.0, .3), (277.18, .2), (329.63, .18)]:  # A major-ish, warm
    trem = 0.75 + 0.25 * np.sin(2 * np.pi * (0.07 + f / 5000) * tt + f)
    pad += g * trem * (np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(2 * np.pi * f * 1.004 * tt))
pad /= np.abs(pad).max()
env = np.minimum(1, tt / 3) * np.minimum(1, (TOTAL - tt) / 3)
pad = pad * env * 0.16
# duck pad slightly under voice
mix = voice * 0.95 + pad
mix = np.clip(mix, -1, 1)
with wave.open("mix.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())

# ---- visuals
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
d = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H * 0.42) / H) ** 2)
glow = np.exp(-(d / 0.33) ** 2)[..., None]
vert = (yy / H)[..., None]
top = np.array([14, 18, 46], np.float32); bot = np.array([40, 22, 54], np.float32)
base = top * (1 - vert) + bot * vert
warm = np.array([255, 190, 110], np.float32)

random.seed(4)
motes = [dict(x=random.random(), y=random.random(), r=random.uniform(2, 7),
              sp=random.uniform(.01, .04), ph=random.uniform(0, 6.28)) for _ in range(45)]

F = lambda size, bold=False: ImageFont.truetype(
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif%s.ttf" % ("-Bold" if bold else ""), size)
f_main, f_ref, f_title, f_sub = F(54), F(34), F(80, True), F(38)
CREAM, GOLD = (250, 240, 220), (232, 185, 105)

def fade(tm, a, b, fi=0.6, fo=0.6):
    if tm < a or tm > b: return 0.0
    return min(1, (tm - a) / fi, (b - tm) / fo)

def draw_text(img, text, font, y, color, alpha, rise=0, spacing=18, center=True):
    if alpha <= 0: return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(layer)
    lines = text.split("\n")
    lh = font.size + spacing
    y0 = y + rise - (len(lines) * lh) / 2
    for k, ln in enumerate(lines):
        w = dr.textlength(ln, font=font)
        dr.text(((W - w) / 2, y0 + k * lh), ln, font=font, fill=color + (int(255 * alpha),))
    img.alpha_composite(layer)

def frame(fi):
    tm = fi / FPS
    pulse = 0.85 + 0.15 * math.sin(tm * 0.9)
    # glow brightens a touch while narrator speaks
    speaking = any(s["start"] - .2 <= tm <= s["end"] for s in segs)
    boost = 1.12 if speaking else 1.0
    arr = base + warm * glow * 0.42 * pulse * boost
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    # motes
    ml = Image.new("RGBA", (W // 2, H // 2), (0, 0, 0, 0)); md = ImageDraw.Draw(ml)
    for m in motes:
        y = (m["y"] - tm * m["sp"]) % 1.0
        x = m["x"] + 0.02 * math.sin(tm * .5 + m["ph"])
        a = int(110 * (0.5 + 0.5 * math.sin(tm * 1.1 + m["ph"])))
        r = m["r"]
        md.ellipse([x * W / 2 - r, y * H / 2 - r, x * W / 2 + r, y * H / 2 + r], fill=(255, 215, 150, a))
    ml = ml.filter(ImageFilter.GaussianBlur(2.5)).resize((W, H))
    img.alpha_composite(ml)

    # intro
    a = fade(tm, 0.2, INTRO + .3, 0.8, 0.6)
    draw_text(img, "A Moment\nof Reflection", f_title, H * 0.42, CREAM, a, rise=(1 - a) * 20, spacing=24)
    draw_text(img, "John 10  ·  John 17", f_sub, H * 0.42 + 190, GOLD, a)

    for i, s in enumerate(segs):
        last = i == len(segs) - 1
        a0 = s["start"] - 0.1
        a1 = s["end"] + (OUTRO - 0.4 if last else 0.7)
        a = fade(tm, a0, a1, 0.7, 0.8)
        if a > 0:
            draw_text(img, s["cap"], f_main, H * 0.42, CREAM, a, rise=(1 - a) * 24)
            draw_text(img, s["ref"], f_ref, H * 0.42 + 70 + 40 * (s["cap"].count("\n") + 1) + 40, GOLD, a * .9)
    # thin gold line progress
    pw = int(W * 0.5 * tm / TOTAL)
    ImageDraw.Draw(img).rectangle([W // 4, H - 110, W // 4 + pw, H - 108], fill=GOLD + (255,))
    return img.convert("RGB")

nf = int(TOTAL * FPS)
p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                      "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", "mix.wav",
                      "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium",
                      "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart",
                      "reflection.mp4"], stdin=subprocess.PIPE)
for fi in range(nf):
    p.stdin.write(frame(fi).tobytes())
p.stdin.close(); p.wait()
print("done", nf, "frames")
