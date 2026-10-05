"""Builds "Say What You Need" — a ~2.5 minute narrated, illustrated short film (no character names).

Reuses the pipeline in ../video/build.py (Piper TTS -> PIL scenes -> ffmpeg).
Run:  python3 build.py            full render
      PREVIEW=1 python3 build.py  only write the scene PNGs (fast)
"""
import importlib.util, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("base", os.path.join(HERE, "..", "video", "build.py"))
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
base.HERE = HERE
base.WORK = os.path.join(HERE, "_work")
base.VOICE = os.environ.get("VOICE", os.path.join(HERE, "..", "video", "_work", "en_US-lessac-medium.onnx"))
base.OUT_NAME = "say_what_you_need.mp4"
os.makedirs(base.WORK, exist_ok=True)

from PIL import Image, ImageDraw
W, H, S = base.W, base.H, base.S
canvas, R, P, E, glow, stars, person, finish, font = (base.canvas, base.R, base.P, base.E, base.glow, base.stars,
                                                      base.person, base.finish, base.font)

SCENES = [
    ("message", [
        "A man types the truest sentence he has.",
        "I'm lonely. I want real connection. I want a family, a village, a life with people in it.",
    ]),
    ("advice", [
        "The replies arrive fast, and every one of them is kind.",
        "Have you tried the apps. Have you tried a hobby group. Have you tried deep breathing. Have you tried touching grass.",
    ]),
    ("heard", [
        "To him, it sounds like a stack of pamphlets.",
        "He didn't ask for a solution. He said, I am hurting, and the answer was a list.",
        "He feels sorted, not seen.",
    ]),
    ("reply", [
        "So he sharpens the truth into a blade.",
        "I respect that you are useless to me, he writes. He says it loudly, on purpose. He wants someone to notice that this kind of help isn't help.",
        "Then he adds a request. If a woman tells you she's lonely, send her my way.",
    ]),
    ("receiver", [
        "Now, the other side of the screen.",
        "A woman reads it, standing in her kitchen. She had just spent a few minutes trying to be kind.",
        "She doesn't think, this person is in pain. She thinks, I'm being insulted. And then, I'm being recruited.",
    ]),
    ("block", [
        "She does the sensible thing. She blocks him.",
        "And the loneliness he was describing just got one more door heavier.",
    ]),
    ("shield", [
        "Here is the cruel math.",
        "The sharp sentence is armor. It protects the place that hurts, and it keeps out the one thing he's asking for.",
        "Warmth is built from warmth. And warmth is the one thing a blade can't carry.",
    ]),
    ("both", [
        "He wasn't wrong to be hungry.",
        "She wasn't wrong to be wary.",
        "They were both telling the truth, in languages that don't translate.",
    ]),
    ("rewrite", [
        "Now try it again. Same man, same ache.",
        "This time he writes, I'm not looking for tips. I'm looking for someone to stay in this with me for a minute.",
        "A different answer comes back. Okay. Tell me more.",
    ]),
    ("end", [
        "You can still call out help that isn't help.",
        "But say what you actually need. The sharpest sentence gets noticed. The honest one gets answered.",
        "Say what you need, and let someone stay.",
    ]),
]

# ------------------------------------------------------------- helpers
def bubble(d, x, y, w, h, text, tail=None, size=44, fill=(255, 255, 255, 238), ink=(50, 50, 60)):
    R(d, x, y, w, h, fill, r=min(h // 2.4, 60))
    if tail:
        tx, ty = tail
        P(d, [(tx - 18, y + h - 2), (tx + 18, y + h - 2), (tx, y + h + 46)], fill)
    f = font(size * S, False)
    lines = text.split("\n")
    lh = size * 1.25
    top = y + (h - lh * len(lines)) / 2
    for i, ln in enumerate(lines):
        tw = d.textlength(ln, font=f) / S
        d.text(((x + (w - tw) / 2) * S, (top + i * lh) * S), ln, font=f, fill=ink)

def phone(d, title="", glow_color=(150, 200, 255)):
    R(d, 620, 40, 680, 1000, (30, 32, 44), r=80)
    R(d, 644, 70, 632, 940, (238, 240, 247), r=58)
    R(d, 644, 70, 632, 110, (226, 229, 240), r=58)
    f = font(40 * S)
    tw = d.textlength(title, font=f) / S
    d.text(((960 - tw / 2) * S, 104 * S), title, font=f, fill=(40, 40, 60))

def msg(d, side, y, text, h=96, w=None, size=32, color=None):
    f = font(size * S, False)
    lines = text.split("\n")
    tw = max(d.textlength(l, font=f) for l in lines) / S
    w = w or tw + 56
    h = 56 + 40 * len(lines) if h is None else h
    x = 670 if side == "in" else 1250 - w
    fill, ink = ((218, 222, 236, 255), (40, 40, 60)) if side == "in" else (color or (40, 130, 150, 255), (255, 255, 255))
    R(d, x, y, w, h, fill, r=40)
    top = y + (h - 40 * len(lines)) / 2 + 2
    for i, ln in enumerate(lines):
        d.text(((x + 28) * S, (top + i * 40) * S), ln, font=f, fill=ink)
    return y + h + 22

def rotrect(d, cx, cy, w, h, ang, fill):
    a = math.radians(ang); pts = []
    for dx, dy in [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]:
        pts.append((cx + dx * math.cos(a) - dy * math.sin(a), cy + dx * math.sin(a) + dy * math.cos(a)))
    P(d, pts, fill)

COLORS = [(58, 78, 124), (126, 70, 82), (84, 110, 90), (118, 98, 60), (96, 70, 120), (70, 100, 120)]
SKIN = (74, 58, 58)
MAN = (40, 130, 150)
WOMAN = (170, 90, 110)

# ------------------------------------------------------------- scenes
def scene_message():
    img, d = canvas((14, 16, 30), (8, 8, 18))
    d = ImageDraw.Draw(img, "RGBA")
    phone(d, "Typing...")
    glow(img, 960, 540, 520, (150, 200, 255), 0.18)
    d = ImageDraw.Draw(img, "RGBA")
    msg(d, "out", 240, "I'm lonely. I want real\nconnection. I want a family,\na village, a life with people\nin it.", h=240, w=520)
    return finish(img, 0.5)

def scene_advice():
    img, d = canvas((14, 16, 30), (8, 8, 18))
    d = ImageDraw.Draw(img, "RGBA")
    phone(d, "Replies")
    y = 215
    y = msg(d, "out", y, "I'm lonely. I want a village.", size=28, h=72)
    for t in ["Have you tried dating apps?", "Try a hobby group!", "Meditation really helps.", "Have you tried deep breathing?",
              "Go touch grass :)"]:
        y = msg(d, "in", y, t, size=28, h=72)
    return finish(img, 0.5)

def scene_heard():
    img, d = canvas((18, 20, 36), (10, 10, 20))
    d = ImageDraw.Draw(img, "RGBA")
    R(d, 0, 840, W, 240, (24, 24, 34))
    R(d, 160, 700, 560, 24, (60, 50, 56)); R(d, 200, 724, 16, 120, (50, 42, 48)); R(d, 660, 724, 16, 120, (50, 42, 48))
    person(d, 360, 700, 3.0, body=MAN, head=SKIN)
    R(d, 470, 560, 230, 140, (30, 34, 50), r=10); R(d, 484, 574, 202, 112, (150, 200, 255))  # his screen
    glow(img, 590, 630, 260, (150, 200, 255), 0.4)
    d = ImageDraw.Draw(img, "RGBA")
    labels = ["try the apps", "join a group", "breathe deeply", "touch grass", "play board games", "go outside"]
    for i, t in enumerate(labels):  # a cascade of pamphlets
        cx, cy = 1100 + (i % 2) * 420, 200 + (i // 2) * 250
        rotrect(d, cx, cy, 380, 150, -5 + (i % 3) * 5, (244, 240, 226, 245))
        f = font(34 * S, False)
        d.text(((cx - 160) * S, (cy - 18) * S), t, font=f, fill=(70, 66, 80))
    return finish(img, 0.5)

def scene_reply():
    img, d = canvas((14, 16, 30), (8, 8, 18))
    d = ImageDraw.Draw(img, "RGBA")
    phone(d, "Reply")
    y = 220
    y = msg(d, "in", y, "Have you tried the apps?", size=28, h=72)
    msg(d, "out", y + 10, "I respect your boundary that\nyou are useless to me. Can you\nat least send any lonely woman\nmy way, if you have bandwidth?",
        h=230, w=540, size=28, color=(150, 40, 50, 255))
    glow(img, 960, 540, 520, (200, 80, 90), 0.14)
    return finish(img, 0.5)

def scene_receiver():
    img, d = canvas((70, 54, 60), (44, 34, 40))
    d = ImageDraw.Draw(img, "RGBA")
    R(d, 0, 780, W, 300, (36, 28, 34))
    R(d, 0, 700, W, 90, (92, 72, 70))  # counter
    R(d, 1180, 180, 560, 330, (50, 40, 48), r=10)  # window
    R(d, 1200, 200, 520, 290, (30, 40, 70))
    person(d, 760, 950, 3.4, body=WOMAN, head=SKIN)
    R(d, 800, 700, 56, 86, (30, 34, 50), r=8); glow(img, 828, 720, 120, (150, 200, 255), 0.5)  # her phone
    d = ImageDraw.Draw(img, "RGBA")
    bubble(d, 140, 160, 520, 100, "I was only trying to help.", tail=(640, 500), size=36, fill=(250, 244, 230, 240))
    bubble(d, 780, 80, 360, 100, "...Useless?", tail=(820, 430), size=44, fill=(250, 220, 220, 240))
    bubble(d, 160, 400, 560, 100, "Now I'm being recruited?", tail=(680, 580), size=36, fill=(250, 244, 230, 240))
    return finish(img, 0.5)

def scene_block():
    img, d = canvas((14, 16, 30), (8, 8, 18))
    d = ImageDraw.Draw(img, "RGBA")
    phone(d, "Conversation")
    msg(d, "out", 230, "I respect your boundary...", size=28, h=72)
    R(d, 700, 700, 520, 140, (255, 255, 255, 255), r=30)
    f = font(32 * S, False)
    for i, t in enumerate(["You can't reply to", "this conversation."]):
        tw = d.textlength(t, font=f) / S
        d.text(((960 - tw / 2) * S, (722 + i * 44) * S), t, font=f, fill=(120, 60, 70))
    glow(img, 960, 770, 300, (220, 70, 80), 0.2)
    return finish(img, 0.55)

def scene_shield():
    img, d = canvas((20, 22, 40), (12, 12, 24))
    stars(d, 60, 400, seed=12)
    d = ImageDraw.Draw(img, "RGBA")
    R(d, 0, 840, W, 240, (22, 22, 32))
    glow(img, 520, 700, 200, (255, 190, 110), 0.7)  # the hurt, kept inside
    d = ImageDraw.Draw(img, "RGBA")
    person(d, 520, 930, 3.6, body=MAN, head=SKIN)
    E(d, 520, 700, 12, 12, (255, 236, 190))
    E(d, 610, 700, 150, 190, (150, 156, 176))  # shield
    E(d, 610, 700, 126, 166, (112, 118, 138))
    R(d, 596, 560, 28, 280, (176, 182, 200, 120))
    for i, x in enumerate([1050, 1300, 1550]):
        person(d, x, 930, 2.6, body=COLORS[i], head=(60, 52, 58))
        glow(img, x, 800, 60, (255, 190, 110), 0.6)
        d = ImageDraw.Draw(img, "RGBA")
        d.line([(x - 20) * S, 820 * S, (x - 150 - i * 40) * S, 790 * S], fill=COLORS[i], width=14 * S) if False else None
        d.line([((x - 14) * S, 830 * S), ((x - 120) * S, 800 * S)], fill=COLORS[i], width=14 * S)
    return finish(img, 0.5)

def scene_both():
    img, d = canvas((22, 26, 46), (12, 14, 26))
    d = ImageDraw.Draw(img, "RGBA")
    R(d, 0, 840, W, 240, (22, 22, 32))
    person(d, 520, 940, 3.4, body=MAN, head=SKIN); glow(img, 520, 800, 90, (255, 190, 110), 0.85)
    d = ImageDraw.Draw(img, "RGBA")
    person(d, 1400, 940, 3.4, body=WOMAN, head=SKIN); glow(img, 1400, 800, 90, (255, 190, 110), 0.85)
    d = ImageDraw.Draw(img, "RGBA")
    R(d, 930, 140, 60, 800, (140, 180, 230, 70))  # the glass between them
    R(d, 926, 140, 6, 800, (190, 210, 240, 160)); R(d, 988, 140, 6, 800, (190, 210, 240, 160))
    bubble(d, 220, 260, 560, 100, "I'm hungry for people.", tail=(520, 600), size=38, fill=(220, 240, 250, 240))
    bubble(d, 1120, 260, 560, 100, "I'm afraid of being used.", tail=(1400, 600), size=38, fill=(250, 232, 232, 240))
    return finish(img, 0.5)

def scene_rewrite():
    img, d = canvas((14, 16, 30), (8, 8, 18))
    d = ImageDraw.Draw(img, "RGBA")
    phone(d, "Reply")
    y = 220
    y = msg(d, "in", y, "Have you tried the apps?", size=28, h=72)
    y = msg(d, "out", y, "I'm not looking for tips. I'm\nlooking for someone to stay\nin this with me for a minute.", h=170, w=520, size=28)
    msg(d, "in", y + 10, "Okay. Tell me more.", size=30, h=80, color=None)
    glow(img, 960, 540, 520, (255, 200, 130), 0.2)
    return finish(img, 0.5)

def scene_end():
    img, d = canvas((16, 18, 44), (110, 70, 84))
    stars(d, 90, 420, seed=31)
    d = ImageDraw.Draw(img, "RGBA")
    R(d, 0, 780, W, 300, (28, 40, 38))
    R(d, 800, 650, 420, 24, (110, 76, 58)); R(d, 830, 674, 18, 110, (80, 56, 44)); R(d, 1170, 674, 18, 110, (80, 56, 44))
    R(d, 800, 560, 420, 20, (110, 76, 58))
    R(d, 1070, 200, 12, 460, (34, 34, 44)); E(d, 1076, 200, 30, 30, (255, 226, 160))
    glow(img, 1076, 230, 360, (255, 206, 130), 0.75)
    d = ImageDraw.Draw(img, "RGBA")
    person(d, 900, 650, 2.4, body=MAN, head=SKIN)
    person(d, 1020, 650, 2.4, body=WOMAN, head=SKIN)
    img = finish(img, 0.45)
    d2 = ImageDraw.Draw(img)
    f = font(84, True); t = "Say what you need."
    tw = d2.textlength(t, font=f)
    d2.text(((W - tw) / 2, 90), t, font=f, fill=(255, 238, 205), stroke_width=3, stroke_fill=(20, 16, 24))
    return img

for name, _ in SCENES:
    setattr(base, "scene_" + name, globals()["scene_" + name])
base.SCENES = SCENES

if __name__ == "__main__":
    if os.environ.get("PREVIEW"):
        for name, _ in SCENES:
            globals()["scene_" + name]().save(os.path.join(base.WORK, f"p_{name}.png"))
        print("previews written")
    else:
        base.main()
