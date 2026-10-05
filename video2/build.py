"""Builds "Set the Table" — a ~2.5 minute narrated, illustrated short film.

Reuses the pipeline in ../video/build.py (Piper TTS -> PIL scenes -> ffmpeg) with a new script and new scenes.
Run:  python3 build.py            full render
      PREVIEW=1 python3 build.py  only write the scene PNGs (fast)
"""
import importlib.util, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("base", os.path.join(HERE, "..", "video", "build.py"))
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

base.HERE = HERE
base.WORK = os.path.join(HERE, "_work")
base.VOICE = os.environ.get("VOICE", os.path.join(HERE, "..", "video", "_work", "en_US-lessac-medium.onnx"))
base.OUT_NAME = "set_the_table.mp4"
os.makedirs(base.WORK, exist_ok=True)

from PIL import Image, ImageDraw
W, H, S = base.W, base.H, base.S
canvas, R, P, E, glow, stars, person, finish, font = (base.canvas, base.R, base.P, base.E, base.glow, base.stars,
                                                      base.person, base.finish, base.font)

SCENES = [
    ("party", [
        "A man, thirty-one, stands in a coworker's kitchen, holding a drink he isn't drinking.",
        "Around him, the conversation drifts the way these conversations do. The weather. The game. A show everyone has already seen.",
    ]),
    ("say", [
        "Then he does something strange. He says a true thing.",
        "Honestly, he says, what I want is a family. A partner. A place to belong.",
    ]),
    ("silence", [
        "Nobody is cruel. The room just goes quiet.",
        "Someone says, you'll find someone. Someone says, have you tried the apps. Someone remembers they need a refill.",
    ]),
    ("why", [
        "Here is what he can't see.",
        "Behind every polite face is the same hunger. One woman is thinking about her empty apartment. A man by the fridge hasn't had dinner with anyone in months.",
        "They aren't rejecting him. They just have nowhere to put it. Nobody ever showed them how to hold a want like that, out loud, in a room.",
    ]),
    ("village", [
        "There was once a place built to catch that sentence.",
        "A young man would say it, and an elder would answer, good, let me think who I know. A neighbor would mention a niece, visiting next month.",
        "The need was never a private quest. It belonged to everyone.",
    ]),
    ("mall", [
        "We traded that for apps, and algorithms, and a lonely hustle.",
        "Say you want a promotion, and you're ambitious. Say you want people, and you're too much.",
        "We replaced the village with the mall, and now we wonder why nobody is home.",
    ]),
    ("walk", [
        "He walks home that night, wondering if he's the problem.",
        "He isn't. He's the error message. Loud, inconvenient, and pointing at something real.",
    ]),
    ("text", [
        "His phone buzzes. A coworker.",
        "I couldn't say it in there, she writes. But, me too.",
    ]),
    ("table", [
        "So he builds the container himself. A long table in his backyard. Sunday dinner.",
        "One rule: say one true thing. The first week, three people come.",
        "By autumn, the neighbors are lending chairs.",
    ]),
    ("end", [
        "You don't have to wait for the village to appear.",
        "Find the ones who are already building. And if you can't find them, build anyway.",
        "Someone has to be first to set the table.",
    ]),
]

# ------------------------------------------------------------- helpers
def bubble(d, x, y, w, h, text, tail=None, size=44, fill=(255, 255, 255, 238), ink=(50, 50, 60), cloud=False):
    R(d, x, y, w, h, fill, r=h // 2.4 if not cloud else h // 2)
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

def room(top=(92, 66, 74), bot=(60, 44, 54), lamp=True):
    img, d = canvas(top, bot)
    d = ImageDraw.Draw(img, "RGBA")
    R(d, 0, 760, W, 320, (44, 32, 40))  # floor
    R(d, 0, 748, W, 14, (30, 22, 28))
    R(d, 1380, 300, 380, 460, (70, 52, 60), r=14)  # fridge-ish / shelf
    R(d, 1400, 320, 340, 20, (90, 70, 78))
    if lamp:
        for i in range(9):  # string lights
            x = 140 + i * 205
            y = 90 + 40 * abs(((i % 4) - 1.5))
            E(d, x, y, 9, 9, (255, 220, 150, 255))
            glow(img, x, y, 55, (255, 210, 130), 0.35)
        d = ImageDraw.Draw(img, "RGBA")
    return img, d

COLORS = [(58, 78, 124), (126, 70, 82), (84, 110, 90), (118, 98, 60), (96, 70, 120), (70, 100, 120)]
SKIN = (74, 58, 58)

# ------------------------------------------------------------- scenes
def scene_party():
    img, d = room()
    xs = [330, 560, 790, 1010, 1240, 1500]
    for i, x in enumerate(xs[1:]):
        person(d, x, 930 - (i % 2) * 20, 2.4, body=COLORS[(i + 1) % 6], head=SKIN)
    person(d, 230, 1000, 3.0, body=(40, 130, 150), head=SKIN)  # Marcus, teal, foreground
    R(d, 262, 800, 22, 34, (240, 240, 240, 220), r=4)  # his untouched cup
    bubble(d, 480, 250, 520, 100, "Crazy weather, huh?", tail=(640, 400))
    bubble(d, 1060, 150, 580, 100, "Did you see the game?", tail=(1220, 420))
    return finish(img, 0.45)

def scene_say():
    img, d = room((70, 52, 62), (46, 34, 44), lamp=False)
    glow(img, 700, 560, 520, (255, 200, 130), 0.28)
    d = ImageDraw.Draw(img, "RGBA")
    person(d, 620, 1120, 5.2, body=(40, 130, 150), head=SKIN)
    bubble(d, 900, 230, 960, 340, "Honestly?\nI want a family.\nA partner. A place to belong.",
           tail=(1000, 560), size=56, fill=(255, 244, 214, 245))
    return finish(img, 0.5)

def scene_silence():
    img, d = room((52, 56, 76), (30, 32, 48), lamp=False)  # colder
    for i, x in enumerate([1000, 1230, 1460, 1680]):
        person(d, x, 930 - (i % 2) * 18, 2.4, body=tuple(int(c * 0.55) for c in COLORS[i]), head=(50, 44, 50))
    person(d, 300, 1000, 3.0, body=(40, 130, 150), head=SKIN)
    bubble(d, 560, 190, 480, 100, "You'll find someone.", tail=(1000, 520 - 40), size=42)
    bubble(d, 1060, 330, 620, 100, "Have you tried the apps?", tail=(1230, 640), size=42)
    bubble(d, 690, 470, 150, 90, "...", tail=(780, 640), size=52)
    return finish(img, 0.55)

def scene_why():
    img, d = canvas((22, 26, 44), (14, 16, 28))
    d = ImageDraw.Draw(img, "RGBA")
    R(d, 0, 820, W, 260, (24, 24, 36))
    spots = [(260, "Dinner alone,\nagain."), (640, "I don't know what\nto do with heavy."), (1030, "I'd say it too,\nif I knew how."),
             (1420, "Me. Same."), (1740, None)]
    for i, (x, txt) in enumerate(spots):
        y = 940
        person(d, x, y, 2.9, body=COLORS[i % 6], head=(60, 52, 58))
        glow(img, x, y - 130, 70, (255, 190, 110), 0.85)  # the hidden hunger, a warm glow in each chest
        d = ImageDraw.Draw(img, "RGBA")
        E(d, x, y - 130, 10, 10, (255, 236, 190))
        if txt:
            bubble(d, x - 170, 220 + (i % 2) * 130, 340, 150 if "\n" in txt else 100, txt, tail=(x, 560), size=34,
                   fill=(226, 232, 250, 225), cloud=True)
    return finish(img, 0.5)

def scene_village():
    img, d = canvas((40, 30, 66), (212, 112, 74))
    stars(d, 60, 300, seed=9)
    d = ImageDraw.Draw(img, "RGBA")
    P(d, [(0, 640), (400, 560), (900, 640), (1400, 540), (1920, 620), (1920, 1080), (0, 1080)], (36, 30, 40))
    for x, w in [(150, 220), (1500, 260), (1150, 200)]:  # huts
        R(d, x, 600, w, 150, (84, 56, 50)); P(d, [(x - 20, 600), (x + w / 2, 500), (x + w + 20, 600)], (60, 40, 36))
        R(d, x + w / 2 - 20, 650, 40, 100, (255, 196, 118))
        glow(img, x + w / 2, 700, 90, (255, 190, 100), 0.5)
    d = ImageDraw.Draw(img, "RGBA")
    glow(img, 860, 820, 420, (255, 150, 60), 0.9)  # the fire
    d = ImageDraw.Draw(img, "RGBA")
    P(d, [(820, 860), (860, 740), (900, 860)], (255, 170, 60)); P(d, [(838, 860), (860, 790), (882, 860)], (255, 232, 140))
    for i, x in enumerate([480, 640, 1080, 1240, 1400]):
        person(d, x, 940, 2.4, body=tuple(int(c * 0.6) for c in COLORS[i % 6]), head=(46, 38, 40))
    person(d, 360, 960, 2.7, body=(40, 130, 150), head=(46, 38, 40))  # the young man
    person(d, 930, 960, 2.8, body=(120, 110, 100), head=(66, 60, 60))  # the elder
    d.line([(990 * S, 960 * S), (1000 * S, 770 * S)], fill=(90, 62, 44), width=8 * S)  # staff
    bubble(d, 760, 190, 700, 110, "Good. Let me think who I know.", tail=(930, 640), size=40, fill=(255, 238, 200, 240))
    return finish(img, 0.45)

def scene_mall():
    img, d = canvas((70, 80, 108), (140, 150, 170))
    d = ImageDraw.Draw(img, "RGBA")
    R(d, 0, 700, W, 380, (58, 62, 72))  # parking lot
    for x in range(-60, W + 120, 160):
        P(d, [(x, 760), (x + 20, 760), (x - 40, 1080), (x - 70, 1080)], (210, 210, 210, 150))  # stall lines
    R(d, 200, 360, 1520, 340, (176, 180, 192))  # mall box
    R(d, 200, 340, 1520, 30, (120, 126, 140))
    R(d, 700, 420, 520, 110, (30, 34, 50), r=10)
    d.text((750 * S, 435 * S), "THE MALL", font=font(72 * S), fill=(230, 232, 245))
    R(d, 880, 580, 160, 120, (40, 44, 60))  # entrance
    for x in range(260, 1700, 200):
        if abs(x - 880) > 120: R(d, x, 560, 130, 100, (50, 54, 70))
    for x in (260, 1660):  # lamp posts
        R(d, x, 620, 10, 260, (40, 40, 50)); E(d, x + 5, 620, 18, 18, (240, 240, 200))
    person(d, 1000, 960, 1.6, body=(40, 130, 150), head=SKIN)
    return finish(img, 0.5)

def scene_walk():
    img, d = canvas((8, 10, 28), (30, 34, 66))
    stars(d, 140, 600, seed=21)
    d = ImageDraw.Draw(img, "RGBA")
    E(d, 1480, 260, 70, 70, (240, 240, 220))
    R(d, 0, 760, W, 320, (22, 24, 36))
    P(d, [(0, 840), (W, 780), (W, 860), (0, 940)], (36, 38, 54))  # road
    for x in (300, 900, 1500):
        R(d, x, 440, 12, 330, (30, 30, 40)); E(d, x + 6, 440, 24, 24, (255, 220, 140))
        glow(img, x + 6, 470, 160, (255, 210, 130), 0.55)
    d = ImageDraw.Draw(img, "RGBA")
    person(d, 1000, 930, 2.2, body=(40, 130, 150), head=SKIN)
    glow(img, 1030, 840, 55, (150, 200, 255), 0.8)  # phone glow
    d = ImageDraw.Draw(img, "RGBA")
    return finish(img, 0.55)

def scene_text():
    img, d = canvas((14, 16, 30), (8, 8, 18))
    d = ImageDraw.Draw(img, "RGBA")
    R(d, 640, 60, 640, 960, (30, 32, 44), r=70)  # phone
    R(d, 664, 90, 592, 900, (240, 242, 248), r=50)
    R(d, 664, 90, 592, 110, (230, 232, 240), r=50)
    d.text((780 * S, 118 * S), "Coworker", font=font(44 * S), fill=(40, 40, 60))
    bubble(d, 690, 300, 500, 150, "I couldn't say it\nin there.", size=36, fill=(210, 222, 250, 255), ink=(30, 30, 50))
    bubble(d, 740, 500, 480, 100, "...but me too.", size=40, fill=(40, 130, 150, 255), ink=(255, 255, 255))
    glow(img, 960, 540, 520, (150, 200, 255), 0.18)
    return finish(img, 0.5)

def scene_table(title=None):
    img, d = canvas((20, 22, 52), (112, 70, 82))
    stars(d, 70, 360, seed=4)
    d = ImageDraw.Draw(img, "RGBA")
    R(d, 0, 700, W, 380, (28, 48, 42))  # grass
    R(d, 1150, 330, 620, 400, (54, 42, 52)); P(d, [(1120, 330), (1460, 190), (1800, 330)], (36, 28, 36))
    for x in (1210, 1400, 1590):
        R(d, x, 440, 90, 100, (255, 200, 120)); glow(img, x + 45, 490, 80, (255, 190, 100), 0.5)
    d = ImageDraw.Draw(img, "RGBA")
    for i in range(14):  # string lights in an arc
        t = i / 13; x = 60 + t * 1050; y = 250 + 190 * math_sin(t)
        E(d, x, y, 9, 9, (255, 226, 160)); glow(img, x, y, 60, (255, 210, 130), 0.4)
    d = ImageDraw.Draw(img, "RGBA")
    R(d, 160, 780, 1360, 36, (124, 88, 62))  # the long table
    for x in (200, 760, 1440): R(d, x, 816, 20, 130, (84, 58, 44))
    for i, x in enumerate(range(260, 1500, 160)):
        person(d, x, 790, 1.9, body=COLORS[i % 6], head=(60, 48, 50))
        R(d, x - 28, 770, 56, 8, (240, 236, 224))  # plate
    glow(img, 840, 770, 520, (255, 200, 120), 0.45)
    d = ImageDraw.Draw(img, "RGBA")
    return finish(img, 0.45)

def math_sin(t):
    import math
    return math.sin(math.pi * t)

def scene_end():
    img = scene_table()
    img = img.copy()
    d = ImageDraw.Draw(img)
    f = font(88, True)
    t = "Set the table."
    tw = d.textlength(t, font=f)
    d.text(((W - tw) / 2, 90), t, font=f, fill=(255, 238, 205), stroke_width=3, stroke_fill=(20, 16, 24))
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
