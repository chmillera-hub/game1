"""Builds "The Blue Light" — a ~2.5 minute narrated, illustrated short film.

Pipeline: Piper TTS narration -> PIL illustrated scenes -> ffmpeg (Ken Burns, captions, ambient pad).
Run:  python3 build.py   (needs piper-tts, pillow, numpy, ffmpeg and a Piper voice .onnx)
"""
import math, os, random, subprocess, sys, wave
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.environ.get("WORK", os.path.join(HERE, "_work"))
VOICE = os.environ.get("VOICE", os.path.join(WORK, "en_US-lessac-medium.onnx"))
os.makedirs(WORK, exist_ok=True)
W, H, S = 1920, 1080, 2  # output size, supersample factor
FPS = 30
GAP = 0.8  # seconds of silence between sentences

# ---------------------------------------------------------------- script
SCENES = [
    ("street_dawn", [
        "There is a street you probably know.",
        "Twelve houses. Twelve green lawns, cut to exactly the same height.",
    ]),
    ("mowers", [
        "Every Saturday morning, the mowers start up all at once.",
        "It sounds like a community. It isn't.",
    ]),
    ("ruth", [
        "At the end of the street, behind the window with the blue light, lives Ruth.",
        "Seventy-four. Her husband died two winters ago.",
        "Last week, the only person who said her name out loud was the pharmacist.",
    ]),
    ("wave", [
        "Ruth waves at her neighbor. He waves back, one hand still on the mower.",
        "Hot one today, he says. Supposed to rain Thursday, she says.",
        "That is the whole conversation. They have had it forty times.",
    ]),
    ("tv", [
        "Inside his house, the television is on.",
        "A man in a suit is furious about people Dale will never meet, in a city Dale will never visit.",
        "Dale knows the anchor's face better than he knows the name of the woman next door.",
    ]),
    ("edges", [
        "Here is the strange part. Nobody chose this.",
        "The weather is safe. The outrage is loud. A lawn has edges, and you can finish it.",
        "Loneliness has no edges. It is quiet. It never trends.",
    ]),
    ("stat", [
        "But the research is blunt.",
        "Chronic isolation can harm the body about as much as smoking fifteen cigarettes a day.",
        "We file it under private, something to endure quietly, while we give our hours to things that will never know our names.",
    ]),
    ("quiet", [
        "Then, one Saturday, Dale's mower runs out of gas.",
        "Silence. And in that silence, for the first time in eleven years, he sees the blue light.",
    ]),
    ("door", [
        "He walks over. He has nothing clever to say.",
        "I have lived next to you for eleven years, he tells her, and I don't know anything about you.",
        "Ruth is quiet for a moment. Then she opens the door wider. Would you like some coffee?",
    ]),
    ("end", [
        "Suffering like this doesn't need a solution. It needs a knock on the door.",
        "The lawn will grow back. The news will repeat itself.",
        "But the window won't stay lit forever. Go and learn someone's name.",
    ]),
]

# ---------------------------------------------------------------- drawing helpers
def lerp(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def canvas(top, bottom):
    img = Image.new("RGB", (W * S, H * S))
    px = ImageDraw.Draw(img)
    for y in range(H * S):
        px.line([(0, y), (W * S, y)], fill=lerp(top, bottom, y / (H * S)))
    return img, ImageDraw.Draw(img, "RGBA")

def R(d, x, y, w, h, fill, r=0):
    box = [x * S, y * S, (x + w) * S, (y + h) * S]
    d.rounded_rectangle(box, radius=r * S, fill=fill) if r else d.rectangle(box, fill=fill)

def P(d, pts, fill): d.polygon([(x * S, y * S) for x, y in pts], fill=fill)
def E(d, cx, cy, rx, ry, fill): d.ellipse([(cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S], fill=fill)

def glow(img, cx, cy, radius, color, strength=0.55):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse([(cx - radius) * S, (cy - radius) * S, (cx + radius) * S, (cy + radius) * S],
                                  fill=color + (int(255 * strength),))
    layer = layer.filter(ImageFilter.GaussianBlur(radius * S * 0.45))
    img.paste(layer, (0, 0), layer)

def stars(d, n, ymax, seed=3):
    rnd = random.Random(seed)
    for _ in range(n):
        x, y, r = rnd.random() * W, rnd.random() * ymax, rnd.choice([1, 1, 1.5, 2])
        E(d, x, y, r, r, (255, 255, 240, rnd.randint(90, 220)))

def house(d, img, x, base, w=130, h=100, wall=(40, 44, 60), roof=(26, 28, 40), lit=(255, 205, 120), lit_prob=0.5,
          window=None, rnd=None):
    R(d, x, base - h, w, h, wall)
    P(d, [(x - 10, base - h), (x + w / 2, base - h - 55), (x + w + 10, base - h)], roof)
    R(d, x + w * 0.42, base - 52, w * 0.16, 52, (22, 20, 28))  # door
    for i, wx in enumerate((x + 14, x + w - 14 - 28)):
        col = window if (window and i == 1) else ((lit if (rnd or random).random() < lit_prob else (30, 34, 48)))
        R(d, wx, base - h + 22, 28, 28, col)
    return (x + w - 28, base - h + 22, 28, 28)  # the right window

def person(d, x, base, s=1.0, body=(20, 20, 28), head=(24, 24, 32), hat=False):
    R(d, x - 14 * s, base - 78 * s, 28 * s, 50 * s, body, r=10 * s)
    R(d, x - 10 * s, base - 30 * s, 8 * s, 30 * s, body)
    R(d, x + 2 * s, base - 30 * s, 8 * s, 30 * s, body)
    E(d, x, base - 92 * s, 13 * s, 14 * s, head)

def lawn(d, y, color_a, color_b, step=42):
    R(d, 0, y, W, H - y, color_a)
    for i, x in enumerate(range(-100, W + 200, step)):
        if i % 2:
            P(d, [(x, y), (x + step, y), (x + step - 180, H), (x - 180, H)], color_b)

def finish(img, vignette=0.55):
    out = img.resize((W, H), Image.LANCZOS)
    v = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(v)
    vd.ellipse([-W * 0.25, -H * 0.3, W * 1.25, H * 1.3], fill=255)
    v = v.filter(ImageFilter.GaussianBlur(160))
    dark = Image.new("RGB", (W, H), (4, 5, 10))
    out = Image.composite(out, Image.blend(out, dark, vignette), v)
    return out

def font(sz, bold=True):
    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif%s.ttf" % ("-Bold" if bold else ""), sz)

# ---------------------------------------------------------------- scenes
def street(dawn=True, blue_window=False, mower_sound=False, focus_ruth=False):
    top, bot = ((255, 168, 110), (252, 226, 176)) if dawn else ((18, 22, 52), (60, 52, 92))
    img, d = canvas(top, bot)
    if not dawn: stars(d, 90, 420)
    if dawn: glow(img, 1500, 520, 330, (255, 236, 170), 0.8)
    d = ImageDraw.Draw(img, "RGBA")
    E(d, 1500, 520, 70, 70, (255, 244, 200))
    # distant hills
    P(d, [(0, 560), (300, 470), (700, 540), (1100, 450), (1500, 530), (1920, 470), (1920, 700), (0, 700)],
      (96, 104, 130) if dawn else (30, 34, 62))
    base = 700
    rnd = random.Random(7)
    lawn(d, base, (66, 120, 74) if dawn else (24, 52, 46), (78, 138, 86) if dawn else (30, 62, 54))
    wall = (210, 190, 170) if dawn else (44, 46, 70)
    roof = (112, 82, 82) if dawn else (24, 24, 40)
    ruth_win = None
    for i in range(12):
        x = 40 + i * 152
        win = (120, 190, 255) if (blue_window and i == 11) else None
        ww = house(d, img, x, base, 118, 96, wall, roof, lit_prob=0.08 if dawn else 0.55, window=win, rnd=rnd)
        if win: ruth_win = ww
    if ruth_win:
        glow(img, ruth_win[0] + 14, ruth_win[1] + 14, 70, (110, 180, 255), 0.7)
    d = ImageDraw.Draw(img, "RGBA")
    return img, d, ruth_win

def scene_street_dawn():
    img, d, _ = street(True)
    return finish(img, 0.35)

def scene_mowers():
    img, d, _ = street(True)
    rnd = random.Random(5)
    for i in range(12):
        if i == 11: continue
        x = 40 + i * 152 + 40
        y = 830 + (i % 3) * 22
        person(d, x, y, 1.0, body=(40, 46, 70), head=(60, 54, 56))
        R(d, x + 22, y - 24, 46, 18, (190, 60, 50), r=4)  # mower deck
        R(d, x + 18, y - 70, 5, 52, (60, 60, 70))  # handle
        for k in range(3):  # noise arcs
            d.arc([(x + 40 - 18 * (k + 1)) * S, (y - 90 - 18 * (k + 1)) * S, (x + 40 + 18 * (k + 1)) * S,
                   (y - 90 + 18 * (k + 1)) * S], 200, 340, fill=(30, 30, 40, 150 - 35 * k), width=3 * S)
    return finish(img, 0.4)

def scene_ruth():
    img, d, win = street(False, blue_window=True)
    return finish(img, 0.55)

def scene_wave():
    img, d = canvas((255, 196, 140), (253, 232, 190))
    glow(img, 1450, 360, 300, (255, 240, 190), 0.7)
    d = ImageDraw.Draw(img, "RGBA")
    lawn(d, 760, (66, 120, 74), (78, 138, 86))
    R(d, 1150, 250, 500, 510, (212, 190, 168))  # Ruth's house front
    P(d, [(1120, 250), (1400, 110), (1680, 250)], (112, 82, 82))
    R(d, 1380, 520, 60, 240, (70, 50, 56))
    R(d, 1220, 340, 100, 100, (140, 200, 255)); R(d, 1480, 340, 100, 100, (140, 200, 255))
    R(d, 0, 760, W, 12, (150, 150, 150))  # fence line / curb
    # Dale (left) with mower
    person(d, 520, 960, 2.3, body=(52, 60, 100), head=(70, 56, 54))
    R(d, 580, 905, 160, 56, (190, 60, 50), r=10)
    R(d, 560, 770, 14, 170, (60, 60, 70))
    # Ruth (right)
    person(d, 1000, 840, 2.0, body=(120, 70, 90), head=(70, 56, 54))
    d.line([(1020 * S, 690 * S), (1075 * S, 600 * S)], fill=(120, 70, 90), width=22 * S)  # raised arm
    # speech bubbles
    for (bx, by, bw, txt, tail) in [(240, 250, 470, "Hot one today.", 560), (700, 390, 590, "Rain Thursday, they say.", 1000)]:
        R(d, bx, by, bw, 110, (255, 255, 255, 235), r=40)
        P(d, [(tail - 20, by + 108), (tail + 20, by + 108), (tail, by + 160)], (255, 255, 255, 235))
        d.text((bx * S + 40 * S, by * S + 24 * S), txt, font=font(46 * S, False), fill=(50, 50, 60))
    return finish(img, 0.35)

def scene_tv():
    img, d = canvas((26, 22, 36), (20, 16, 26))
    d = ImageDraw.Draw(img, "RGBA")
    R(d, 0, 780, W, 300, (40, 30, 34))  # floor
    R(d, 160, 380, 820, 400, (12, 12, 18), r=18)  # TV frame
    R(d, 190, 408, 760, 344, (200, 40, 50))
    R(d, 190, 640, 760, 112, (20, 30, 90))  # ticker
    for k in range(5): R(d, 210 + k * 140, 668, 100, 14, (255, 255, 255, 220))
    P(d, [(480, 752), (640, 752), (660, 560), (460, 560)], (30, 30, 40))  # suit torso
    E(d, 560, 515, 55, 62, (232, 190, 160))
    R(d, 530, 590, 60, 160, (240, 240, 245)); P(d, [(560, 600), (545, 720), (575, 720)], (190, 30, 40))
    d.text((220 * S, 425 * S), "BREAKING", font=font(40 * S), fill=(255, 255, 255))
    glow(img, 570, 560, 520, (220, 80, 120), 0.35)
    d = ImageDraw.Draw(img, "RGBA")
    # Dale in armchair, silhouetted
    R(d, 1180, 560, 520, 330, (54, 40, 50), r=60)
    R(d, 1220, 700, 440, 160, (66, 50, 62), r=40)
    person(d, 1440, 800, 2.4, body=(30, 26, 38), head=(40, 34, 42))
    glow(img, 1440, 640, 280, (220, 80, 120), 0.18)
    d = ImageDraw.Draw(img, "RGBA")
    # window with the blue light, seen through the gap (faint, unnoticed)
    R(d, 1700, 120, 150, 190, (30, 34, 54)); R(d, 1722, 150, 106, 130, (70, 120, 190, 160))
    return finish(img, 0.55)

def scene_edges():
    img, d = canvas((24, 26, 46), (16, 18, 30))
    d = ImageDraw.Draw(img, "RGBA")
    # left: crisp lawn square with sharp edges
    R(d, 160, 330, 560, 420, (62, 128, 78))
    for i in range(8): R(d, 160 + i * 70, 330, 35, 420, (74, 148, 90))
    d.rectangle([160 * S, 330 * S, 720 * S, 750 * S], outline=(235, 235, 235), width=5 * S)
    d.text((180 * S, 790 * S), "a lawn: finish it, feel done", font=font(36 * S, False), fill=(210, 214, 230))
    # right: fog with no edges
    fog = Image.new("RGBA", img.size, (0, 0, 0, 0))
    fd = ImageDraw.Draw(fog)
    rnd = random.Random(2)
    for _ in range(40):
        cx, cy, r = 1150 + rnd.random() * 650, 330 + rnd.random() * 420, 60 + rnd.random() * 120
        fd.ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], fill=(120, 170, 240, 38))
    fog = fog.filter(ImageFilter.GaussianBlur(70 * S / 2))
    img.paste(fog, (0, 0), fog)
    d = ImageDraw.Draw(img, "RGBA")
    # a tiny lit window lost in the fog
    R(d, 1448, 520, 26, 26, (140, 200, 255)); glow(img, 1461, 533, 45, (110, 180, 255), 0.6)
    d = ImageDraw.Draw(img, "RGBA")
    d.text((1150 * S, 790 * S), "loneliness: no edges, no end", font=font(36 * S, False), fill=(210, 214, 230))
    return finish(img, 0.5)

def scene_stat():
    img, d = canvas((16, 18, 34), (10, 10, 20))
    d = ImageDraw.Draw(img, "RGBA")
    f = font(280 * S)
    txt = "15"
    tw = d.textlength(txt, font=f)
    d.text(((W * S - tw) / 2, 150 * S), txt, font=f, fill=(255, 228, 160))
    sub = "cigarettes a day"
    f2 = font(64 * S, False); sw = d.textlength(sub, font=f2)
    d.text(((W * S - sw) / 2, 500 * S), sub, font=f2, fill=(230, 232, 245))
    for i in range(15):  # a row of cigarettes
        x = 330 + i * 84
        R(d, x, 640, 18, 150, (240, 240, 240)); R(d, x, 640, 18, 42, (220, 140, 80)); R(d, x, 788, 18, 4, (160, 160, 170))
    s3 = "the health risk of chronic isolation, by widely cited research"
    f3 = font(34 * S, False); w3 = d.textlength(s3, font=f3)
    d.text(((W * S - w3) / 2, 830 * S), s3, font=f3, fill=(170, 176, 200))
    return finish(img, 0.5)

def scene_quiet():
    img, d, win = street(False, blue_window=True)
    d = ImageDraw.Draw(img, "RGBA")
    person(d, 1200, 960, 3.0, body=(14, 14, 22), head=(18, 18, 26))  # Dale, big, foreground
    R(d, 1250, 905, 170, 62, (150, 50, 44), r=12)  # silent mower
    R(d, 1230, 760, 14, 190, (40, 40, 50))
    glow(img, win[0] + 14, win[1] + 14, 130, (110, 180, 255), 0.8)
    return finish(img, 0.6)

def scene_door():
    img, d = canvas((18, 18, 30), (14, 12, 22))
    d = ImageDraw.Draw(img, "RGBA")
    R(d, 0, 820, W, 260, (40, 34, 40))
    R(d, 0, 0, W, 820, (58, 48, 56))  # wall
    R(d, 620, 120, 680, 700, (92, 64, 56))  # door frame
    R(d, 660, 160, 600, 660, (255, 196, 118))  # warm light spilling out
    glow(img, 960, 500, 520, (255, 190, 100), 0.7)
    d = ImageDraw.Draw(img, "RGBA")
    P(d, [(660, 160), (660, 820), (790, 800), (790, 180)], (110, 78, 64))  # door swung open
    person(d, 1000, 820, 3.0, body=(110, 66, 84), head=(60, 50, 52))  # Ruth silhouette in the doorway
    person(d, 330, 1000, 2.8, body=(20, 24, 40), head=(26, 26, 32))  # Dale, back to us
    R(d, 1300, 760, 120, 50, (255, 255, 255, 40), r=10)
    return finish(img, 0.5)

def scene_end():
    img, d, win = street(False)
    # turn Ruth's window warm and add a second warm window beside it
    d = ImageDraw.Draw(img, "RGBA")
    for i in (10, 11):
        x = 40 + i * 152
        R(d, x + 14, 700 - 96 + 22, 28, 28, (255, 205, 120))
        R(d, x + 118 - 14 - 28, 700 - 96 + 22, 28, 28, (255, 205, 120))
        glow(img, x + 60, 640, 90, (255, 190, 100), 0.55)
    d = ImageDraw.Draw(img, "RGBA")
    f = font(78 * S); t = "Go and learn someone's name."
    tw = d.textlength(t, font=f)
    d.text(((W * S - tw) / 2, 130 * S), t, font=f, fill=(255, 238, 205))
    return finish(img, 0.5)

# ---------------------------------------------------------------- narration
def synth():
    from piper import PiperVoice, SynthesisConfig
    voice = PiperVoice.load(VOICE)
    sr = voice.config.sample_rate
    clips = []
    for si, (_, lines) in enumerate(SCENES):
        for li, line in enumerate(lines):
            path = os.path.join(WORK, f"n_{si:02d}_{li}.wav")
            with wave.open(path, "wb") as w:
                voice.synthesize_wav(line, w, syn_config=SynthesisConfig(length_scale=1.14))
            with wave.open(path) as w:
                dur = w.getnframes() / w.getframerate()
            clips.append((si, li, path, dur))
    return clips, sr

def srt_time(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def main():
    clips, sr = synth()
    # timeline
    t = 0.6  # lead-in
    cues, scene_spans = [], {}
    concat_audio = []
    silence = lambda sec: concat_audio.append(("sil", sec))
    silence(0.6)
    for si, li, path, dur in clips:
        start = t
        scene_spans.setdefault(si, [start, None])
        concat_audio.append(("wav", path))
        cues.append((start, start + dur, SCENES[si][1][li]))
        t += dur
        scene_spans[si][1] = t
        pause = GAP if li < len(SCENES[si][1]) - 1 else 1.3
        silence(pause)
        t += pause
    total = t + 1.4
    silence(1.4)

    # assemble narration wav
    import numpy as np
    chunks = []
    for kind, v in concat_audio:
        if kind == "sil":
            chunks.append(np.zeros(int(v * sr), dtype=np.int16))
        else:
            with wave.open(v) as w: chunks.append(np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16))
    nar = np.concatenate(chunks)
    npath = os.path.join(WORK, "narration.wav")
    with wave.open(npath, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(nar.tobytes())

    # captions
    srt = os.path.join(WORK, "captions.srt")
    with open(srt, "w") as f:
        for i, (a, b, txt) in enumerate(cues, 1):
            f.write(f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{txt}\n\n")

    # scene videos with slow push / pan, cut at sentence-group boundaries
    builders = {n: globals()["scene_" + n] for n, _ in SCENES}
    seg_files = []
    names = [n for n, _ in SCENES]
    bounds = []
    for si, n in enumerate(names):
        a = 0.0 if si == 0 else scene_spans[si][0] - 0.45
        b = total if si == len(names) - 1 else scene_spans[si + 1][0] - 0.45
        bounds.append((a, b))
    for si, n in enumerate(names):
        png = os.path.join(WORK, f"s_{n}.png")
        builders[n]().save(png)
        dur = bounds[si][1] - bounds[si][0]
        frames = int(dur * FPS) + 2
        mp4 = os.path.join(WORK, f"s_{n}.mp4")
        zoom_in = si % 2 == 0
        z = f"'1.0+0.10*on/{frames}'" if zoom_in else f"'1.10-0.10*on/{frames}'"
        fx = "iw/2-(iw/zoom/2)" if si % 3 else f"iw/2-(iw/zoom/2)+{40}*on/{frames}"
        vf = (f"scale=2880:1620,zoompan=z={z}:x='{fx}':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps={FPS},"
              f"fade=t=in:st=0:d=0.45,fade=t=out:st={max(dur-0.45,0):.2f}:d=0.45,format=yuv420p")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", png, "-vf", vf, "-frames:v",
                        str(frames), "-t", f"{dur:.3f}", "-c:v", "libx264", "-crf", "18", mp4], check=True)
        seg_files.append(mp4)
    lst = os.path.join(WORK, "list.txt")
    with open(lst, "w") as f:
        for p in seg_files: f.write(f"file '{p}'\n")
    silent = os.path.join(WORK, "silent.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent],
                   check=True)

    # ambient pad (A minor-ish drone) under the voice
    pad = os.path.join(WORK, "pad.wav")
    tones = [110.0, 164.81, 220.0, 261.63]
    expr = "+".join(f"0.18*sin(2*PI*{f}*t+{0.7*i})*(0.75+0.25*sin(2*PI*{0.07+0.02*i}*t))" for i, f in enumerate(tones))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                    f"aevalsrc='{expr}':s=44100:d={total:.2f}", "-af",
                    f"lowpass=f=900,afade=t=in:d=3,afade=t=out:st={total-4:.2f}:d=4,volume=0.55", pad], check=True)

    out = os.path.join(HERE, "the_blue_light.mp4")
    style = "FontName=DejaVu Sans,FontSize=13,PrimaryColour=&H00FFFFFF,OutlineColour=&H99000000,BorderStyle=1,Outline=1.2,Shadow=0.6,MarginV=14,Bold=1"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", npath, "-i", pad, "-filter_complex",
                    "[1:a]volume=1.0,aresample=44100[v];[2:a]volume=0.5[p];[v][p]amix=inputs=2:duration=longest:normalize=0,"
                    "alimiter=limit=0.95[a]", "-map", "0:v", "-map", "[a]",
                    "-vf", f"subtitles={srt}:force_style='{style}'", "-c:v", "libx264", "-crf", "20", "-preset", "medium",
                    "-c:a", "aac", "-b:a", "160k", "-t", f"{total:.2f}", "-movflags", "+faststart", out], check=True)
    print("total seconds: %.1f -> %s" % (total, out))

if __name__ == "__main__":
    main()
