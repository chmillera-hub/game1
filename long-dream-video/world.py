"""All scenes for The Long Dream. Everything is drawn in 1080x1920 design space;
film.py applies cameras and picks which scene is on screen."""
import math, random
import skia
from common import *
from characters import *
from cast import CYAN, GOLD, CONSTITUENT

STAR_R = random.Random(5)
STARS = [(STAR_R.uniform(-600, 1700), STAR_R.uniform(-600, 2500), STAR_R.uniform(0.8, 3.2), STAR_R.random() * 6)
         for _ in range(420)]


def starfield(cv, t, dim=1.0, drift=0.0):
    for (x, y, r, ph) in STARS:
        a = (0.35 + 0.65 * (0.5 + 0.5 * math.sin(t * 1.3 + ph * 3))) * dim
        circle(cv, x + drift * r, y, r, paint("#ffffff", a))


def glow(cv, x, y, r, col, a):
    circle(cv, x, y, r, paint(col, a, blur=r * 0.35))


def person(cv, L, x, y, f, t, speak=0.0, hands=((-62, 186), (62, 186)), kinds=("fist", "fist"),
           breathe=0.0, lean=0.0, head_dx=0.0, head_dy=0.0, scale=1.0, arms_front=True):
    cv.save()
    cv.translate(x, y)
    cv.scale(scale, scale)
    cv.rotate(lean)
    draw_torso(cv, L, t, breathe)
    draw_neck(cv, L)
    if not arms_front:
        draw_arm(cv, L, -1, hands[0], kinds[0], 0, arm_color(L))
        draw_arm(cv, L, 1, hands[1], kinds[1], 0, arm_color(L))
    cv.save()
    cv.translate(head_dx + f["turn"] * 6, -112 + head_dy - breathe * 4)
    draw_head(cv, L, f, t, speak)
    cv.restore()
    if arms_front:
        draw_arm(cv, L, -1, hands[0], kinds[0], 0, arm_color(L))
        draw_arm(cv, L, 1, hands[1], kinds[1], 0, arm_color(L))
    cv.restore()


def badge(cv, x, y, label, col):
    line(cv, x - 26, y - 120, x, y, paint(col, stroke=4))
    line(cv, x + 26, y - 120, x, y, paint(col, stroke=4))
    rrect(cv, x - 34, y, 68, 84, 8, paint("#ffffff"))
    rect(cv, x - 34, y, 68, 20, paint(col))
    text(cv, label, x, y + 52, font("black", 15), paint("#22304d"), "center")
    text(cv, "PUBLIC", x, y + 70, font("bold", 11), paint("#22304d"), "center")


# ==================================================================== cosmic window

class Window:
    """Two voices of the public behind Window 7, watching the constituent on a monitor."""
    POS = {"CYAN": (330, 1125), "GOLD": (750, 1125)}
    MON = (540, 1215)

    def __init__(self, tl, kitchen):
        self.tl, self.kitchen = tl, kitchen
        T, E, Wd = tl.s, tl.e, tl.wfind
        self.T, self.E, self.Wd = T, E, Wd
        self.blink = {"CYAN": Blinker(41, mean=4.2), "GOLD": Blinker(77, mean=3.6)}
        F = FaceTrack
        self.face = {
            "CYAN": F([(0, "serene"), (T("a3"), expr("smug", lid=0.3)), (T("a5"), "kind"), (T("a7"), "smile"),
                       (T("d2"), expr("kind", lid=0.3)), (Wd("d3", "recertification"), "sad"), (Wd("d3", "shelter"), "kind"),
                       (T("d4"), "smile"), (T("r2"), "hopeful"), (T("r3"), "serene"), (T("r4"), "kind"),
                       (T("l2"), "kind"), (T("l3"), "sad"), (T("l4"), expr("compassion", glisten=0.5)),
                       (T("l5"), expr("compassion", glisten=0.7)), (T("t1"), "serene"), (T("t2"), "stern"),
                       (Wd("t2", "legal"), "smug"), (T("t3"), "nervous"), (T("t4"), "kind"), (T("w1"), "hopeful"),
                       (T("w2"), "kind"), (T("w4"), "smile")]),
            "GOLD": F([(0, "kind"), (T("a2"), expr("nervous", sweat=0)), (Wd("a2", "Code"), "skeptical"),
                       (T("a3"), "deadpan"), (T("a4"), "smile"), (T("a6"), "kind"), (T("d1"), "smile"),
                       (T("d4"), "grin"), (Wd("d4", "ZIP"), "smile"), (T("r1"), "skeptical"),
                       (T("r3"), "confused"), (T("r4"), "serene"), (T("l1"), "hopeful"), (T("l3"), "sad"),
                       (T("l4"), expr("compassion", glisten=0.8)), (T("l5"), "kind"), (T("t1"), expr("sad", lid=0.3)),
                       (T("t2"), "serene"), (Wd("t2", "legal"), "grin"), (T("t3"), "nervous"), (T("t5"), "smile"),
                       (T("w1"), "kind"), (T("w3"), "serene"), (T("w4"), "smile")]),
        }
        # who looks where: (t0, t1, target)
        self.look = {
            "CYAN": [(T("w4"), 9999, "CAM")],
            "GOLD": [(T("w4"), 9999, "CAM"), (T("d4"), Wd("d4", "ZIP"), "CYAN")],
        }
        self.shrug = {"CYAN": [(T("a3"), 1.4)], "GOLD": [(Wd("t2", "legal"), 1.2)]}
        self.laugh = {"GOLD": [(T("d4"), 1.6), (Wd("t2", "legal") + 0.3, 1.2)]}
        self.lean_in = [(T("l3"), E("l4") + 0.5)]

    def target(self, who, t):
        for a, b, name in self.look.get(who, []):
            if a <= t < b:
                return name
        L = self.tl.current(t) or self.tl.last_speaker(t)
        if L and L["who"] in self.POS and L["who"] != who and self.tl.current(t):
            return L["who"]
        return "MON"

    def gaze(self, who, t):
        hx, hy = self.POS[who][0], self.POS[who][1] - 112

        def g(tt):
            n = self.target(who, tt)
            if n == "CAM":
                return 0.0, 0.0
            p = self.MON if n == "MON" else (self.POS[n][0], self.POS[n][1] - 112)
            return p[0] - hx, p[1] - hy
        a = [g(t - k * 0.06) for k in range(6)]
        dx = sum(v[0] for v in a) / 6
        dy = sum(v[1] for v in a) / 6
        return (clamp(dx / 260, -1, 1) + noise1(t * 1.4, len(who)) * 0.07,
                clamp(dy / 200, -1, 1) + noise1(t * 1.1, len(who) + 4) * 0.05,
                clamp(dx / 1100, -0.4, 0.4))

    def entity(self, cv, who, t):
        L = CYAN if who == "CYAN" else GOLD
        x, y = self.POS[who]
        f = self.face[who](t)
        gx, gy, turn = self.gaze(who, t)
        f["gx"], f["gy"], f["turn"] = gx, gy, turn
        f["blink"] = max(f["blink"], self.blink[who](t))
        sp = self.tl.mouth(who, t)
        shr = 0.0
        for t0, d in self.shrug.get(who, []):
            shr = max(shr, pulse(t, t0, 0.25, d * 0.4, 0.4))
        lau = 0.0
        for t0, d in self.laugh.get(who, []):
            if t0 < t < t0 + d:
                lau = abs(math.sin((t - t0) * 9)) * (1 - (t - t0) / d)
        lean_in = max([smooth(prog(t, a, a + 0.8)) * (1 - smooth(prog(t, b, b + 0.8))) for a, b in self.lean_in] + [0])
        col = "#7fe8ff" if who == "CYAN" else "#ffd86a"
        glow(cv, x, y - 60, 260, col, 0.22 + 0.06 * math.sin(t * 1.3 + x))
        f["tilt"] += noise1(t * 0.4, len(who)) * 3 + sp * noise1(t * 2.5, 9) * 4 + lau * 4
        hl, hr = (-60, 196), (60, 196)
        kinds = ("fist", "fist")
        if sp > 0.05 or self.tl.speaking(who, t):
            k = 0.5 + 0.5 * noise1(t * 0.9, 13 + len(who))
            hr = lerp2(hr, (78 if who == "GOLD" else 70, 100), k * 0.8)
            kinds = ("fist", "open")
        if shr > 0:
            hl = lerp2(hl, (-120, 90), shr)
            hr = lerp2(hr, (120, 90), shr)
            kinds = ("open", "open")
        dy = -shr * 14 + lau * -6 + lean_in * 18
        cv.save()
        cv.translate(0, dy)
        person(cv, L, x, y, f, t, sp * 0.95, (hl, hr), kinds, math.sin(t * 1.2 + x), 0,
               head_dy=shr * 10 + lean_in * 6)
        badge(cv, x + 44, y + 40, "WINDOW 7", "#2f8fa3" if who == "CYAN" else "#b8862b")
        cv.restore()

    def draw(self, cv, t, kitchen_fn):
        rect(cv, -800, -800, 2700, 3600, paint("#000", shader=lin_grad((0, 0), (0, 1920), [("#090d26", 1), ("#1b1240", 1)])))
        for (x, y, r, c) in ((200, 400, 420, "#3b2a7a"), (900, 1500, 520, "#1f5a7a"), (700, 200, 300, "#5a2a6a")):
            circle(cv, x + math.sin(t * 0.1 + x) * 30, y, r, paint(c, 0.35, blur=140))
        starfield(cv, t, 1.0, math.sin(t * 0.05) * 6)
        # window frame
        x0, y0, x1, y1 = 110, 640, 970, 1440
        rrect(cv, x0 - 26, y0 - 26, x1 - x0 + 52, y1 - y0 + 52, 46, paint("#2c3866"))
        rrect(cv, x0 - 26, y0 - 26, x1 - x0 + 52, y1 - y0 + 52, 46, paint("#8fa8ff", 0.25, stroke=4))
        cv.save()
        cv.clipRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x0, y0, x1, y1), 30, 30), True)
        rect(cv, x0, y0, x1 - x0, y1 - y0, paint("#000", shader=lin_grad((0, y0), (0, y1), [("#20306a", 1), ("#3a2d6e", 1)])))
        for k in range(5):
            line(cv, x0 + 40 + k * 180, y0, x0 + 40 + k * 180, y1, paint("#ffffff", 0.04, stroke=60))
        self.entity(cv, "CYAN", t)
        self.entity(cv, "GOLD", t)
        # counter + monitor
        rect(cv, x0, 1300, x1 - x0, 160, paint("#3d4a80"))
        rect(cv, x0, 1300, x1 - x0, 12, paint("#8fa8ff", 0.5))
        mx, my = self.MON
        rrect(cv, mx - 150, my - 100, 300, 200, 14, paint("#11152a"))
        cv.save()
        cv.clipRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(mx - 138, my - 88, 276, 176), 8, 8), True)
        cv.translate(mx - 138, my - 88)
        cv.scale(276 / 1080, 276 / 1080)
        cv.translate(0, -560)
        kitchen_fn(cv, t, thumb=True)
        cv.restore()
        rrect(cv, mx - 150, my - 100, 300, 200, 14, paint("#8fa8ff", 0.6, stroke=4))
        rect(cv, mx - 20, my + 100, 40, 30, paint("#11152a"))
        # bell
        ellipse(cv, 860, 1316, 34, 10, paint("#c9b26b"))
        cv.drawPath(smooth_path([(830, 1316), (836, 1290), (860, 1280), (884, 1290), (890, 1316)], False), paint("#e8d48a"))
        circle(cv, 860, 1276, 6, paint("#e8d48a"))
        # glass sheen
        cv.drawPath(poly([(x0 + 60, y0), (x0 + 200, y0), (x0 - 40, y1), (x0 - 180, y1)]), paint("#ffffff", 0.05))
        cv.restore()
        # sign + now serving
        rrect(cv, 330, 540, 420, 80, 18, paint("#11152a"))
        rrect(cv, 330, 540, 420, 80, 18, paint("#8fa8ff", 0.5, stroke=3))
        text(cv, "WINDOW 7", 540, 596, font("black", 50), paint("#e8ecff"), "center")
        rrect(cv, 300, 1480, 480, 80, 14, paint("#0a0a12"))
        text(cv, "NOW SERVING", 330, 1532, font("bold", 26), paint("#ff6b5a"))
        rrect(cv, 520, 1500, 230, 40, 6, paint("#ff6b5a", 0.9))


# ==================================================================== kitchen

class Kitchen:
    def __init__(self, tl):
        self.tl = tl
        T, E, Wd = tl.s, tl.e, tl.wfind
        self.T, self.E, self.Wd = T, E, Wd
        self.blink = Blinker(19, mean=3.0)
        self.wake0 = Wd("w2", "breath") - 0.3
        self.stir = [(T("t3"), 1.2), (Wd("t3", "session"), 0.8), (T("w1") + 0.4, 0.8)]
        self.face_awake = FaceTrack([(0, "tired"), (self.wake0 + 1.0, expr("hopeful", lid=0.0)),
                                     (Wd("w2", "fingers"), "smile"), (Wd("w2", "district"), "kind"),
                                     (T("s5"), "tired"), (Wd("s5", "checklist"), "hopeful"),
                                     (Wd("s5", "alive"), expr("shocked", mouth=0.3)), (Wd("s5", "Those"), expr("hopeful", glisten=0.9)),
                                     (T("s6"), expr("grin", glisten=1.0, tears=0.5)), (E("s6") + 1, "kind")])

    def awake(self, t):
        return clamp((t - self.wake0) / 1.4)

    def draw(self, cv, t, thumb=False, phone_close=0.0):
        night = 1.0
        rect(cv, -800, -800, 2700, 3600, paint("#000", shader=lin_grad((0, 0), (0, 1920), [("#1c2448", 1), ("#141a33", 1)])))
        # window
        wx, wy = 70, 380
        rrect(cv, wx - 14, wy - 14, 368, 448, 8, paint("#2b3560"))
        rect(cv, wx, wy, 340, 420, paint("#0b1030"))
        circle(cv, wx + 240, wy + 110, 44, paint("#fdf6d8"))
        circle(cv, wx + 258, wy + 98, 40, paint("#0b1030"))
        r = random.Random(3)
        for _ in range(16):
            circle(cv, wx + r.random() * 340, wy + r.random() * 260, r.uniform(1, 2.5),
                   paint("#ffffff", 0.5 + 0.5 * math.sin(t * 2 + r.random() * 9)))
        line(cv, wx + 170, wy, wx + 170, wy + 420, paint("#2b3560", stroke=10))
        # fridge
        rrect(cv, 760, 380, 300, 940, 24, paint("#c9d0dc"))
        line(cv, 760, 760, 1060, 760, paint("#9aa3b5", stroke=4))
        rect(cv, 790, 470, 10, 200, paint("#9aa3b5"))
        rrect(cv, 840, 800, 170, 200, 6, paint("#ffffff"))
        text(cv, "OCTOBER", 925, 836, font("black", 22), paint("#c0392b"), "center")
        for k in range(12):
            rect(cv, 852 + (k % 4) * 38, 852 + (k // 4) * 44, 30, 36, paint("#eeeeee"))
        circle(cv, 852 + 2 * 38 + 15, 852 + 2 * 44 + 18, 22, paint("#c0392b", stroke=4))
        text(cv, "RECERT DUE", 925, 1030, font("black", 18), paint("#c0392b"), "center")
        for k, c in enumerate(("#e74c3c", "#3498db", "#f1c40f")):
            circle(cv, 820 + k * 60, 560, 14, paint(c))
        # lamp
        line(cv, 560, 0, 560, 520, paint("#111", stroke=4))
        cv.drawPath(poly([(480, 600), (640, 600), (600, 520), (520, 520)]), paint("#2b2b33"))
        cv.drawPath(poly([(480, 600), (640, 600), (900, 1380), (220, 1380)]), paint("#ffd98a", 0.07))
        glow(cv, 560, 640, 260, "#ffd98a", 0.18)
        # constituent
        self.draw_constituent(cv, t)
        # table
        rect(cv, -200, 1330, 1500, 60, paint("#8a5a3a"))
        rect(cv, -200, 1390, 1500, 800, paint("#5a3a26"))
        rect(cv, -200, 1330, 1500, 8, paint("#a8744d"))
        # laptop (3/4 view, screen glow)
        cv.drawPath(poly([(110, 1336), (470, 1336), (500, 1356), (90, 1356)]), paint("#9aa3b5"))
        cv.drawPath(poly([(130, 1336), (450, 1336), (420, 1110), (150, 1090)]), paint("#2a2f39"))
        cv.drawPath(poly([(146, 1322), (436, 1322), (410, 1124), (164, 1106)]), paint("#9fd3ff", 0.95))
        for k in range(6):
            line(cv, 180, 1150 + k * 26, 380 - (k % 3) * 40, 1150 + k * 26, paint("#4a6a9a", 0.7, stroke=6))
        glow(cv, 290, 1210, 240, "#8fd3ff", 0.12)
        # papers + mug + phone
        cv.save()
        cv.translate(700, 1340)
        cv.rotate(-8)
        for k in range(4):
            rect(cv, -100 + k * 4, -20 - k * 6, 190, 30, paint("#fbfbf7" if k % 2 else "#eeeeea"))
        cv.restore()
        rrect(cv, 600, 1268, 56, 64, 10, paint("#e8e2d6"))
        cv.drawPath(quad_path((656, 1280), (680, 1298), (656, 1318)), paint("#e8e2d6", stroke=8))
        rrect(cv, 860, 1306, 120, 30, 8, paint("#111"))
        rrect(cv, 866, 1310, 108, 22, 5, paint("#2ecc71", 0.8))
        text(cv, "ON HOLD", 920, 1327, font("black", 14), paint("#06240f"), "center")

    def draw_constituent(self, cv, t):
        L = CONSTITUENT
        aw = self.awake(t)
        f = dict(self.face_awake(t))
        stir = 0.0
        for t0, d in self.stir:
            stir = max(stir, pulse(t, t0, 0.2, d * 0.5, 0.4))
        sleep_f = expr("sleepy", lid=1.0)
        sleep_f["browA"] = -0.3 * stir
        sleep_f["browL"] = 0.3 * stir
        f = face_blend(sleep_f, f, aw)
        f["blink"] = max(f["blink"], self.blink(t) * aw)
        # gaze
        if aw > 0:
            look_t = t - self.wake0
            gx = 0.0
            if 1.2 < look_t < 3.0:
                gx = -0.6 * math.sin((look_t - 1.2) / 1.8 * math.pi)
            if self.T("s5") - 0.5 < t < self.Wd("s5", "alive"):
                gx, gy = -0.8, 0.5
            else:
                gy = 0.0
            f["gx"], f["gy"] = gx, gy
            f["turn"] = gx * 0.3
        breath = math.sin(t * 1.1) * (1 - aw) * 1.5 + math.sin(t * 1.4)
        big = 0.0
        for w in ("breath", "another"):
            tb = self.Wd("w2", w)
            big = max(big, pulse(t, tb - 0.1, 0.9, 0.3, 0.9))
        tb = self.Wd("s5", "alive")
        big = max(big, pulse(t, tb - 0.1, 0.7, 0.4, 1.0))
        # pose: sleeping head on right hand -> upright
        tilt = lerp(18 + math.sin(t * 1.1) * 1.5 - stir * 4, 0, ease_io(aw))
        f["tilt"] += tilt
        hr_sleep, hr_awake = (92, -44), (66, 196)
        hl = (-62, 196)
        hr = lerp2(hr_sleep, hr_awake, ease_io(aw))
        kinds = ("fist", "open" if aw < 0.5 else "fist")
        fing = prog(t, self.Wd("w2", "fingers") - 0.1, self.Wd("w2", "Have") + 0.2)
        if 0 < fing < 1:
            hl = (-70, 70)
            kinds = ("open" if int(t * 5) % 2 == 0 else "fist", kinds[1])
            f["gx"], f["gy"] = -0.5, 0.6
        person(cv, L, 600, 1190 + (1 - aw) * 40, f, t, 0.0, (hl, hr), kinds, breath + big * 3,
               lean=0, head_dx=lerp(24, 0, aw), head_dy=lerp(30, 0, aw) - big * 4, arms_front=aw > 0.5)


# ==================================================================== laptop screen (full frame)

def browser(cv, t, url="apply.yourstate.gov", tabs=3, tab_hi=-1, scroll=0.0):
    rect(cv, 0, 0, W, H, paint("#0d1020"))
    rrect(cv, 40, 220, 1000, 1480, 36, paint("#1d2130"))
    rrect(cv, 60, 240, 960, 1440, 26, paint("#f4f6fa"))
    cv.save()
    cv.clipRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(60, 240, 960, 1440), 26, 26), True)
    rect(cv, 60, 240, 960, 130, paint("#dfe3ea"))
    tw = min(220, 900 / max(1, tabs))
    for k in range(tabs):
        col = "#ffffff" if k == 0 else ("#fff4c8" if k == tab_hi else "#cfd5df")
        rrect(cv, 80 + k * tw, 256, tw - 8, 48, 10, paint(col))
        if tw > 60:
            text(cv, ("Apply" if k == 0 else ("Official" if k == tab_hi else "Tab")), 96 + k * tw, 288,
                 font("semi", 20), paint("#333"))
    rrect(cv, 90, 316, 900, 44, 22, paint("#ffffff"))
    text(cv, "\U0001F512 " if False else "", 110, 346, font("semi", 22), paint("#555"))
    text(cv, url, 120, 346, font("semi", 24), paint("#333"))
    # .gov banner
    rect(cv, 60, 370, 960, 44, paint("#e9eef6"))
    rect(cv, 86, 384, 28, 18, paint("#3b6fb6"))
    text(cv, "An official website of the United States government", 126, 400, font("semi", 22), paint("#333"))
    cv.restore()


def laptop_scene(cv, t, mode, tl, k=1.0):
    T, E, Wd = tl.s, tl.e, tl.wfind
    if mode == "tabs":
        browser(cv, t, tabs=28, tab_hi=17)
        hk = pulse(t, Wd("l2", "official") - 0.2, 0.3, 2.0, 0.5)
        if hk > 0:
            cv.save()
            cv.translate(540, 900)
            cv.scale(0.9 + 0.1 * ease_back(min(1, hk * 2)), 0.9 + 0.1 * ease_back(min(1, hk * 2)))
            rrect(cv, -380, -150, 760, 300, 30, paint("#ffffff"))
            rrect(cv, -380, -150, 760, 300, 30, paint("#3b6fb6", stroke=6))
            text(cv, "✔ Official source", 0, -30, font("black", 56), paint("#1f4f8f"), "center")
            text(cv, "plain answer, real phone number", 0, 50, font("semi", 34), paint("#555"), "center")
            cv.restore()
        for i in range(40):
            r = random.Random(i)
            x, y = r.uniform(120, 960), r.uniform(500, 1600)
            if hk < 0.5:
                rrect(cv, x - 90, y - 20, 180, 40, 10, paint("#c9d0dc", 0.5))
        return
    browser(cv, t)
    if mode == "chatbot":
        rrect(cv, 520, 1180, 460, 440, 24, paint("#ffffff"))
        rrect(cv, 520, 1180, 460, 440, 24, paint("#3b6fb6", stroke=4))
        rect(cv, 520, 1180, 460, 70, paint("#3b6fb6"))
        text(cv, "Virtual Assistant", 550, 1226, font("bold", 28), paint("#fff"))
        circle(cv, 590, 1320, 34, paint("#9fd3ff"))
        circle(cv, 578, 1312, 5, paint("#123"))
        circle(cv, 602, 1312, 5, paint("#123"))
        cv.drawPath(quad_path((574, 1330), (590, 1342), (606, 1330)), paint("#123", stroke=4))
        rrect(cv, 640, 1290, 310, 90, 18, paint("#eef3fb"))
        text(cv, "Hi! How can I help", 660, 1328, font("semi", 26), paint("#222"))
        text(cv, "you today?", 660, 1362, font("semi", 26), paint("#222"))
        for k in range(3):
            circle(cv, 700 + k * 26, 1440, 8, paint("#9aa3b5", 0.4 + 0.6 * (int(t * 3) % 3 == k)))
        text(cv, "Apply for benefits", 100, 520, font("black", 54), paint("#1b2a4a"))
        for k in range(8):
            rrect(cv, 100, 580 + k * 66, 380, 40, 8, paint("#e3e7ee"))
    elif mode == "sideways":
        text(cv, "Upload: proof_of_income.pdf", 100, 500, font("black", 44), paint("#1b2a4a"))
        cv.save()
        cv.translate(540, 1000)
        rot = 90 - 90 * ease_io(prog(t, Wd("a4", "give") - 0.2, Wd("a4", "sideways") + 0.4)) * 0
        cv.rotate(90)
        rect(cv, -300, -220, 600, 440, paint("#ffffff"))
        rect(cv, -300, -220, 600, 440, paint("#c9d0dc", stroke=3))
        text(cv, "PAY STUB", -260, -160, font("black", 40), paint("#333"))
        for k in range(7):
            rect(cv, -260, -110 + k * 44, 420 - (k % 3) * 60, 18, paint("#c9d0dc"))
        cv.restore()
        rrect(cv, 300, 1400, 480, 90, 45, paint("#3b6fb6"))
        text(cv, "↻  Rotate & retry", 540, 1458, font("black", 36), paint("#fff"), "center")
    elif mode == "gov":
        text(cv, "Notice", 100, 520, font("black", 54), paint("#1b2a4a"))
        L = tl.by_id["a5"]
        words = L["words"]
        shown = [w[0] for w in words if L["start"] + w[1] <= t]
        txt = " ".join(shown)
        lines, cur = [], ""
        for w in txt.split():
            if text_w(cur + " " + w, font("serif", 52)) > 840:
                lines.append(cur)
                cur = w
            else:
                cur = (cur + " " + w).strip()
        lines.append(cur)
        for i, s in enumerate(lines):
            text(cv, s, 100, 640 + i * 72, font("serif", 52), paint("#222"))
        if int(t * 2) % 2 == 0:
            rect(cv, 100 + text_w(lines[-1], font("serif", 52)) + 6, 600 + (len(lines) - 1) * 72, 4, 52, paint("#222"))
    elif mode == "appeal":
        text(cv, "Decision", 100, 520, font("black", 54), paint("#1b2a4a"))
        rrect(cv, 100, 570, 880, 120, 12, paint("#fdecea"))
        text(cv, "Your application was denied.", 130, 645, font("bold", 40), paint("#a12a1d"))
        k2 = pulse(t, Wd("l5", "appeal") - 0.3, 0.4, 2.5, 0.5)
        s = 1 + 0.08 * math.sin(t * 6) * k2
        cv.save()
        cv.translate(540, 1000)
        cv.scale(s, s)
        glow(cv, 0, 0, 300, "#ffd86a", 0.4 * k2)
        rrect(cv, -260, -70, 520, 140, 70, paint("#1f4f8f"))
        text(cv, "APPEAL", 0, 22, font("black", 64), paint("#fff"), "center")
        cv.restore()
        text(cv, "You have 60 days to request a hearing.", 540, 1200, font("semi", 34), paint("#555"), "center")
    elif mode == "timeout":
        text(cv, "Apply for benefits", 100, 520, font("black", 54), paint("#1b2a4a"))
        for k in range(8):
            rrect(cv, 100, 580 + k * 66, 520, 40, 8, paint("#e3e7ee"))
        rect(cv, 60, 240, 960, 1440, paint("#000", 0.35))
        secs = max(0, 59 - int((t - T("t3")) * 6))
        rrect(cv, 140, 760, 800, 420, 30, paint("#ffffff"))
        text(cv, "Are you still there?", 540, 860, font("black", 50), paint("#1b2a4a"), "center")
        text(cv, "Your session will expire in", 540, 940, font("semi", 36), paint("#555"), "center")
        text(cv, f"0:{secs:02d}", 540, 1050, font("mono", 90), paint("#c0392b"), "center")
        rrect(cv, 340, 1090, 400, 66, 33, paint("#1f4f8f"))
        text(cv, "Stay signed in", 540, 1134, font("bold", 32), paint("#fff"), "center")
    elif mode == "regs":
        k1 = prog(t, Wd("s5", "decoded") - 0.2, Wd("s5", "checklist") + 0.3)
        text(cv, "§ 1.4  Eligibility", 100, 520, font("black", 50), paint("#1b2a4a"))
        r = random.Random(4)
        for i in range(14):
            y = 590 + i * 56
            wv = r.uniform(500, 860)
            rect(cv, 100, y, wv, 22, paint("#b5bccb", 1 - k1))
        if k1 > 0:
            items = ["Bring two forms of ID", "Upload last pay stub", "Call 1-800-███-████"]
            for i, s in enumerate(items):
                kk = ease_back(prog(k1, i * 0.25, i * 0.25 + 0.4))
                if kk <= 0:
                    continue
                y = 640 + i * 150
                cv.save()
                cv.translate(110, y)
                cv.scale(kk, kk)
                rrect(cv, 0, 0, 860, 110, 20, paint("#eef7ee"))
                rrect(cv, 30, 30, 50, 50, 10, paint("#2e9e5b"))
                cv.drawPath(poly([(40, 55), (52, 68), (72, 40)], False), paint("#fff", stroke=7))
                text(cv, s, 110, 72, font("bold", 42), paint("#1b2a4a"))
                cv.restore()
        rk = pulse(t, Wd("s5", "rang") - 0.3, 0.2, 1.4, 0.4)
        if rk > 0:
            cv.save()
            cv.translate(540, 1300)
            cv.rotate(math.sin(t * 40) * 12 * rk)
            circle(cv, 0, 0, 90, paint("#2ecc71"))
            cv.drawPath(smooth_path([(-40, -20), (-20, -40), (0, -20), (-10, 0), (10, 20), (20, 0), (40, 20), (20, 40), (-40, -20)], True, 0.2), paint("#fff"))
            cv.restore()
            for j in range(3):
                circle(cv, 540, 1300, 110 + j * 30 + (t * 120) % 30, paint("#2ecc71", 0.5 * rk, stroke=5))


# ==================================================================== dream bubble icons

def dream_icon(cv, name, x, y, s, t, a=1.0):
    cv.save()
    cv.translate(x, y)
    cv.scale(s, s)
    if name == "sun":
        circle(cv, -60, -40, 50, paint("#ffd84a", a))
        for k in range(10):
            ang = k / 10 * 2 * math.pi + t
            line(cv, -60 + 62 * math.cos(ang), -40 + 62 * math.sin(ang), -60 + 80 * math.cos(ang), -40 + 80 * math.sin(ang), paint("#ffd84a", a, stroke=6))
        rect(cv, 60, 0, 18, 80, paint("#6d4c41", a))
        circle(cv, 69, -20, 60, paint("#4caf50", a))
    elif name == "fire":
        cv.drawPath(smooth_path([(-60, 60), (-90, 0), (-60, -80), (-40, -20), (-20, -60), (0, 60)], True, 0.5), paint("#ff7a2a", a))
        cv.drawPath(smooth_path([(-50, 60), (-60, 20), (-40, -20), (-20, 60)], True, 0.5), paint("#ffd84a", a))
        p = skia.Path()
        p.moveTo(70, -70)
        p.quadTo(120, 10, 70, 60)
        p.quadTo(20, 10, 70, -70)
        cv.drawPath(p, paint("#3fa9f5", a))
    elif name == "shop":
        rect(cv, -90, -40, 180, 120, paint("#e8e2d6", a))
        cv.drawPath(poly([(-110, -40), (110, -40), (90, -90), (-90, -90)]), paint("#e74c3c", a))
        rrect(cv, -50, 0, 100, 40, 6, paint("#2ecc71", a))
        text(cv, "OPEN", 0, 30, font("black", 26), paint("#fff", a), "center")
    elif name == "password":
        crack = clamp((t % 4) / 1.0)
        rrect(cv, -140, -40, 280, 80, 14, paint("#ffffff", a))
        rrect(cv, -140, -40, 280, 80, 14, paint("#333", a, stroke=4))
        for k in range(8):
            circle(cv, -110 + k * 30, 0, 9, paint("#333", a))
        cv.drawPath(poly([(-20, -40), (0, -10), (-14, 10), (10, 40)], False), paint("#e74c3c", a, stroke=5))
    elif name == "job":
        rrect(cv, -110, -30, 110, 80, 10, paint("#8a5a3a", a))
        rect(cv, -80, -46, 50, 18, paint("#8a5a3a", a, stroke=6))
        rect(cv, 40, -40, 120, 80, paint("#ffffff", a))
        cv.drawPath(poly([(40, -40), (100, 0), (160, -40)], False), paint("#c0392b", a, stroke=4))
        text(cv, "RECERT", 100, 30, font("black", 20), paint("#c0392b", a), "center")
        for k in range(3):
            line(cv, 20 - k * 16, -20 + k * 20, -0 - k * 16, -20 + k * 20, paint("#c0392b", a * 0.6, stroke=4))
    elif name == "house":
        rect(cv, -80, -20, 160, 110, paint("#f3e3c3", a))
        cv.drawPath(poly([(-100, -20), (0, -100), (100, -20)]), paint("#8e4a2e", a))
        rect(cv, -20, 30, 40, 60, paint("#6d4c41", a))
        rrect(cv, -150, 100, 300, 40, 8, paint("#2e9e5b", a))
        text(cv, "VOUCHERS WELCOME", 0, 128, font("black", 20), paint("#fff", a), "center")
    elif name == "zip":
        rect(cv, -10, 0, 20, 110, paint("#555", a))
        rrect(cv, -90, -80, 180, 90, 40, paint("#3b6fb6", a))
        rect(cv, 60, -110, 10, 50, paint("#e74c3c", a))
        rect(cv, 60, -110, 40, 24, paint("#e74c3c", a))
        text(cv, "ZIP", 0, -20, font("black", 40), paint("#fff", a), "center")
    cv.restore()


# ==================================================================== montage scenes

def people_lights(cv, t, tl, glitch=0.0):
    rect(cv, 0, 0, W, H, paint("#000", shader=lin_grad((0, 0), (0, H), [("#06081a", 1), ("#141235", 1)])))
    r = random.Random(11)
    pts = []
    for i in range(330):
        a = r.uniform(0, 2 * math.pi)
        rr = r.uniform(0, 1) ** 0.6 * 430
        pts.append((540 + rr * math.cos(a) * 1.0, 960 + rr * math.sin(a) * 1.3))
    k = ease_out(prog(t, tl.s("r2"), tl.s("r2") + 2.5))
    for i in range(0, 330, 3):
        x0, y0 = pts[i]
        x1, y1 = pts[(i * 7 + 3) % 330]
        if math.hypot(x1 - x0, y1 - y0) < 160:
            line(cv, x0, y0, x1, y1, paint("#7fe8ff", 0.18 * k, stroke=2))
    for i, (x, y) in enumerate(pts):
        a = k * (0.5 + 0.5 * math.sin(t * 2 + i))
        circle(cv, x, y, 5, paint("#ffe9a8" if i % 3 else "#7fe8ff", a))
    text(cv, "330,000,000", 540, 360, font("mono", 80), paint("#ffe9a8", k), "center")
    text(cv, "people, working on it together", 540, 430, font("semi", 36), paint("#9fb0d8", k), "center")
    if glitch > 0:
        r = random.Random(int(t * 30))
        for _ in range(16):
            y = r.uniform(0, H)
            h = r.uniform(10, 90)
            dx = r.uniform(-80, 80) * glitch
            rect(cv, 0, y, W, h, paint(r.choice(["#ff2a6a", "#2affd0", "#ffffff"]), 0.25 * glitch))
            rect(cv, dx, y, W, h * 0.3, paint("#000", 0.5 * glitch))
        for _ in range(10):
            text(cv, r.choice(["**??§§", "§§??", "**§?", "?§*"]), r.uniform(60, 900), r.uniform(300, 1700),
                 font("mono", r.uniform(40, 120)), paint(r.choice(["#ff2a6a", "#2affd0", "#ffffff"]), glitch))


def black_sun(cv, t):
    rect(cv, 0, 0, W, H, paint("#000", shader=lin_grad((0, 0), (0, H), [("#4a5466", 1), ("#c9d3df", 1)])))
    glow(cv, 540, 560, 300, "#ffffff", 0.35)
    circle(cv, 540, 560, 160, paint("#05060a"))
    circle(cv, 540, 560, 170, paint("#e8f0ff", 0.6, stroke=6))
    cv.drawPath(smooth_path([(-100, 1400), (300, 1320), (700, 1380), (1180, 1300), (1180, 2100), (-100, 2100)], True), paint("#e8eef5"))
    r = random.Random(2)
    for i in range(90):
        x = (r.uniform(0, W) + t * 30 * r.uniform(0.5, 1.5)) % W
        y = (r.uniform(0, H) + t * 120 * r.uniform(0.5, 1.2)) % H
        circle(cv, x, y, r.uniform(2, 5), paint("#ffffff", 0.8))
    # tiny shivering figure
    L = CONSTITUENT
    f = expr("sad", lid=0.35)
    f["blink"] = 0.0
    cv.save()
    cv.translate(540 + math.sin(t * 40) * 2, 1300)
    cv.scale(0.55, 0.55)
    person(cv, L, 0, 0, f, t, 0, ((-30, 120), (30, 120)), ("fist", "fist"))
    for s in (-1, 1):
        rect(cv, s * 40 - 22, 300, 44, 220, paint("#2c3e50"))
    cv.restore()


def hold_phone(cv, t):
    rect(cv, 0, 0, W, H, paint("#141a33"))
    rrect(cv, 240, 300, 600, 1240, 70, paint("#111"))
    rrect(cv, 262, 322, 556, 1196, 54, paint("#0f2a1c"))
    text(cv, "ON HOLD", 540, 560, font("black", 70), paint("#7dffb0"), "center")
    secs = 2 * 3600 + 47 * 60 + 11 + int(t)
    text(cv, f"{secs // 3600:02d}:{secs % 3600 // 60:02d}:{secs % 60:02d}", 540, 680, font("mono", 80), paint("#7dffb0"), "center")
    text(cv, "Your call is important", 540, 820, font("semi", 36), paint("#9fd8b5"), "center")
    text(cv, "to us.", 540, 870, font("semi", 36), paint("#9fd8b5"), "center")
    for i in range(6):
        ph = (t * 0.4 + i / 6) % 1
        x = 540 + math.sin(ph * 8 + i) * 160
        y = 1350 - ph * 400
        text(cv, "♪" if i % 2 else "♫", x, y, font("black", 70), paint("#7dffb0", 1 - ph), "center")


def letterhead(cv, t, tl):
    Wd = tl.wfind
    rect(cv, 0, 0, W, H, paint("#000", shader=lin_grad((0, 0), (0, H), [("#22203a", 1), ("#3a2d4e", 1)])))
    stages = [(Wd("w3", "mountain") - 0.4, "mountain", "THE SPIRIT OF THE MOUNTAIN"),
              (Wd("w3", "post") - 0.2, "post", "THE POST OFFICE"),
              (Wd("w3", "gods") - 0.2, "angels", "GODS & ANGELS, LLC"),
              (Wd("w3", "IRS") - 0.2, "irs", "INTERNAL REVENUE"),
              (Wd("w3", "letterhead") - 0.1, "flip", ""),
              (Wd("w3", "not") - 0.4, "light", "")]
    cur = stages[0]
    for s in stages:
        if t >= s[0]:
            cur = s
    t0, kind, title = cur
    if t < stages[0][0]:
        lk = smooth(prog(t, tl.s("w3") - 0.3, stages[0][0]))
        glow(cv, 380, 900, 360, "#7fe8ff", 0.4 * lk)
        glow(cv, 700, 900, 360, "#ffd86a", 0.4 * lk)
        text(cv, "Who are we?", 540, 960, font("serif_i", 70), paint("#fff7e0", lk), "center")
        return
    k = ease_back(prog(t, t0, t0 + 0.3))
    if kind == "light":
        lk = prog(t, t0, t0 + 1.0)
        glow(cv, 380, 900, 400, "#7fe8ff", 0.5 * lk)
        glow(cv, 700, 900, 400, "#ffd86a", 0.5 * lk)
        text(cv, "We do not change.", 540, 960, font("serif_i", 70), paint("#fff7e0", lk), "center")
        return
    if kind == "flip":
        kind = ["mountain", "post", "angels", "irs"][int(t * 8) % 4]
        title = {"mountain": "THE SPIRIT OF THE MOUNTAIN", "post": "THE POST OFFICE", "angels": "GODS & ANGELS, LLC",
                 "irs": "INTERNAL REVENUE"}[kind]
        k = 1.0
    cv.save()
    cv.translate(540, 960)
    cv.scale(k, k)
    cv.rotate(-2)
    rect(cv, -360, -470, 720, 940, paint("#000", 0.3, blur=20))
    rect(cv, -360, -480, 720, 940, paint("#fbf8f0"))
    cy = -330
    if kind == "mountain":
        cv.drawPath(poly([(-120, cy + 60), (-30, cy - 80), (40, cy + 10), (80, cy - 40), (140, cy + 60)]), paint("#4a6a8a"))
        circle(cv, 60, cy - 90, 26, paint("#f2b630"))
    elif kind == "post":
        rect(cv, -80, cy - 50, 160, 100, paint("#3b6fb6"))
        cv.drawPath(poly([(-80, cy - 50), (0, cy + 10), (80, cy - 50)], False), paint("#fff", stroke=6))
        for s in (-1, 1):
            cv.drawPath(poly([(s * 80, cy - 20), (s * 150, cy - 70), (s * 130, cy - 10)]), paint("#9fc3ef"))
    elif kind == "angels":
        circle(cv, 0, cy - 10, 40, paint("#f6dc96"))
        ellipse(cv, 0, cy - 70, 50, 12, paint("#f2b630", stroke=6))
        for s in (-1, 1):
            cv.drawPath(smooth_path([(s * 40, cy), (s * 140, cy - 80), (s * 160, cy + 10), (s * 60, cy + 40)], True), paint("#ffffff"))
            cv.drawPath(smooth_path([(s * 40, cy), (s * 140, cy - 80), (s * 160, cy + 10), (s * 60, cy + 40)], True), paint("#c9b26b", stroke=3))
    elif kind == "irs":
        cv.drawPath(poly([(-130, cy - 30), (0, cy - 90), (130, cy - 30)]), paint("#6a6a6a"))
        for k2 in range(5):
            rect(cv, -110 + k2 * 50, cy - 26, 20, 90, paint("#8a8a8a"))
        rect(cv, -140, cy + 64, 280, 16, paint("#6a6a6a"))
    text(cv, title, 0, -180, font("black", 34 if len(title) < 22 else 28), paint("#22304d"), "center")
    line(cv, -300, -150, 300, -150, paint("#22304d", stroke=3))
    for i in range(8):
        rect(cv, -300, -100 + i * 56, 560 - (i % 3) * 90, 18, paint("#c9ccd6"))
    text(cv, "Sincerely,", -300, 400, font("serif_i", 34), paint("#22304d"))
    cv.restore()


def story_once(cv, t, tl):
    rect(cv, 0, 0, W, H, paint("#000", shader=lin_grad((0, 0), (0, H), [("#0b0f2a", 1), ("#2a1a4a", 1)])))
    starfield(cv, t, 0.9)
    k = ease_io(prog(t, tl.wfind("s1", "was") - 0.3, tl.e("s1") + 0.5))
    cv.save()
    cv.translate(540, 1200)
    s = lerp(0.5, 1.1, k)
    cv.scale(s, s)
    circle(cv, 0, 260, 300, paint("#3a5a8a"))
    circle(cv, 0, 260, 300, paint("#7fe8ff", 0.3, stroke=6))
    glow(cv, 0, -100, 260, "#ffe9a8", 0.35)
    f = expr("kind")
    f["blink"] = 0.0
    person(cv, CONSTITUENT, 0, -60, f, t, 0, ((-70, 230), (70, 230)))
    for side in (-1, 1):
        rect(cv, side * 40 - 22, 260, 44, 0, paint("#2c3e50"))
    cv.restore()
    text(cv, "Once upon a time...", 540, 420, font("serif_i", 64), paint("#fff7e0", clamp((t - tl.s("s1")) * 2)), "center")


def story_atoms(cv, t, tl):
    rect(cv, 0, 0, W, H, paint("#000", shader=lin_grad((0, 0), (0, H), [("#9fd3ff", 1), ("#fbe9c8", 1)])))
    cv.drawPath(smooth_path([(-100, 1200), (400, 1150), (1180, 1220), (1180, 2100), (-100, 2100)], True), paint("#6fbf5a"))
    cv.drawPath(smooth_path([(-100, 1500), (500, 1430), (1180, 1520), (1180, 1600), (500, 1520), (-100, 1590)], True), paint("#4aa3df"))
    T, Wd = tl.s, tl.wfind
    g = ease_io(prog(t, Wd("s2", "woman") - 0.6, Wd("s2", "body") + 0.4))
    r = random.Random(9)
    sil = []
    for i in range(160):
        a = r.uniform(0, 2 * math.pi)
        rr = r.random() ** 0.5
        # silhouette target: head + body ellipse with a rounded belly
        if i < 30:
            tx, ty = 540 + rr * 60 * math.cos(a), 760 + rr * 70 * math.sin(a)
        else:
            tx, ty = 540 + rr * 130 * math.cos(a) + (40 * rr if math.cos(a) > 0.3 else 0), 1060 + rr * 230 * math.sin(a)
        sx, sy = r.uniform(0, W), r.uniform(900, 1800)
        x = lerp(sx + math.sin(t + i) * 20, tx, g)
        y = lerp(sy + math.cos(t * 0.8 + i) * 20, ty, g)
        circle(cv, x, y, 7, paint(r.choice(["#ffffff", "#fff3b0", "#bfefff"]), 0.85))
    if g > 0.95:
        glow(cv, 540, 980, 300, "#fff3b0", 0.3)
    ck = ease_back(prog(t, Wd("s2", "birth") - 0.2, Wd("s2", "birth") + 0.3))
    if ck > 0:
        cv.save()
        cv.translate(540, 1500)
        cv.rotate(-4)
        cv.scale(ck, ck)
        rect(cv, -300, -150, 600, 300, paint("#fffdf2"))
        rect(cv, -290, -140, 580, 280, paint("#c9a227", stroke=6))
        text(cv, "CERTIFICATE", 0, -60, font("serif_b", 50), paint("#22304d"), "center")
        text(cv, "OF BIRTH", 0, -10, font("serif_b", 40), paint("#22304d"), "center")
        rect(cv, -200, 50, 400, 30, paint("#111"))
        circle(cv, 200, 100, 36, paint("#c0392b"))
        cv.restore()


def story_baby(cv, t, tl):
    Wd = tl.wfind
    rect(cv, 0, 0, W, H, paint("#000", shader=rad_grad((540, 900), 1200, [("#ffe9c8", 1), ("#e8b88a", 1)])))
    # arms cradling
    cv.drawPath(smooth_path([(160, 1100), (540, 1300), (920, 1100), (900, 1250), (540, 1420), (180, 1250)], True), paint("#a06848"))
    ellipse(cv, 540, 1080, 260, 190, paint("#f6f1e6"))
    hk = clamp((t - tl.s("s3")) / 2.5)
    f = expr("sleepy", lid=lerp(1.0, 0.1, hk))
    f["blink"] = 0.0
    f["smile"] = 0.3
    cv.save()
    cv.translate(540, 980)
    cv.scale(1.15, 1.15)
    L = Look(skin="#c08a66", hair="#1c1412", hair_style="short", hw=72, hh=70, jaw=0.85, eye_rx=13, eye_ry=13)
    draw_head(cv, L, f, t)
    cv.restore()
    sk = ease_back(prog(t, Wd("s3", "Social") - 0.2, Wd("s3", "Social") + 0.3))
    if sk > 0:
        cv.save()
        cv.translate(540, 540)
        cv.rotate(3)
        cv.scale(sk, sk)
        rrect(cv, -280, -110, 560, 220, 16, paint("#eaf2ff"))
        rrect(cv, -280, -110, 560, 220, 16, paint("#3b6fb6", stroke=5))
        text(cv, "SOCIAL SECURITY", 0, -40, font("black", 36), paint("#1f4f8f"), "center")
        text(cv, "███-██-████", 0, 40, font("mono", 50), paint("#111"), "center")
        cv.restore()
    lk = prog(t, Wd("s3", "milk") - 0.2, Wd("s3", "Eligible"))
    if 0 < lk < 1:
        for i in range(8):
            ph = (lk * 1.5 + i / 8) % 1
            x = 540 + math.sin(i * 2.1) * 300
            y = 1100 - ph * 600
            cv.save()
            cv.translate(x, y)
            cv.scale(1.2, 1.2)
            p = skia.Path()
            p.moveTo(0, 18)
            p.cubicTo(-30, -2, -14, -24, 0, -8)
            p.cubicTo(14, -24, 30, -2, 0, 18)
            cv.drawPath(p, paint("#e74c3c", 1 - ph))
            cv.restore()
    ek = ease_back(prog(t, Wd("s3", "Eligible") - 0.2, Wd("s3", "Eligible") + 0.3))
    if ek > 0:
        cv.save()
        cv.translate(540, 1600)
        cv.scale(ek, ek)
        rrect(cv, -360, -130, 720, 260, 20, paint("#ffffff"))
        text(cv, "ELIGIBLE (on paper):", -320, -60, font("black", 34), paint("#22304d"))
        for i, s in enumerate(("Several things", "you haven't asked about yet")):
            rrect(cv, -320, -20 + i * 60, 36, 36, 6, paint("#22304d", stroke=4))
            text(cv, s, -270, 12 + i * 60, font("semi", 34), paint("#22304d"))
        cv.restore()


def story_star(cv, t, tl):
    rect(cv, 0, 0, W, H, paint("#05060f"))
    starfield(cv, t, 0.7)
    sx, sy = 540, 620
    glow(cv, sx, sy, 500, "#ffcf6a", 0.5)
    circle(cv, sx, sy, 170, paint("#fff3c4"))
    cv.save()
    cv.translate(sx, sy)
    cv.rotate(t * 8)
    for k in range(12):
        cv.rotate(30)
        cv.drawPath(poly([(0, -170), (-20, -290 - 30 * math.sin(t * 3 + k)), (20, -290)]), paint("#ffd86a", 0.6))
    cv.restore()
    r = random.Random(1)
    for i in range(120):
        ph = (t * 0.25 + r.random()) % 1
        tx, ty = 540 + r.uniform(-90, 90), 1420 + r.uniform(-180, 260)
        x = lerp(sx, tx, ph) + math.sin(ph * 6 + i) * 30
        y = lerp(sy, ty, ph)
        circle(cv, x, y, 5, paint("#fff3c4", 0.9 * (1 - ph * 0.5)))
    # outline of a person made of starlight
    cv.save()
    cv.translate(540, 1400)
    cv.drawPath(smooth_path([(-110, 300), (-120, 60), (-60, -10), (60, -10), (120, 60), (110, 300)], True), paint("#ffe9a8", 0.8, stroke=5))
    circle(cv, 0, -100, 80, paint("#ffe9a8", 0.8, stroke=5))
    cv.restore()


def tiles_404(cv, t, t0):
    k = prog(t, t0, t0 + 1.4)
    if k <= 0 or k >= 1:
        return
    r = random.Random(7)
    for i in range(36):
        x = 120 + (i % 6) * 168
        y = 380 + (i // 6) * 190
        d = r.uniform(0, 0.4)
        u = clamp((k - d) / 0.6)
        if u >= 1:
            continue
        cv.save()
        cv.translate(x + u * r.uniform(-300, 300), y + u * u * 900)
        cv.rotate(u * r.uniform(-200, 200))
        rrect(cv, -70, -50, 140, 100, 12, paint("#ffffff", 0.9 * (1 - u)))
        text(cv, "404", 0, 18, font("black", 50), paint("#c0392b", 1 - u), "center")
        cv.restore()


def id_cards(cv, t, t0):
    for i in range(2):
        k = ease_back(prog(t, t0 + i * 0.25, t0 + i * 0.25 + 0.35))
        if k <= 0:
            continue
        cv.save()
        cv.translate(330 + i * 420, 560)
        cv.rotate(-8 + i * 16)
        cv.scale(k, k)
        rrect(cv, -170, -110, 340, 220, 18, paint("#ffffff"))
        rrect(cv, -170, -110, 340, 50, 18, paint("#3b6fb6" if i == 0 else "#2e9e5b"))
        text(cv, "ID" if i == 0 else "ID #2", 0, -74, font("black", 30), paint("#fff"), "center")
        rect(cv, -140, -40, 90, 110, paint("#c9d0dc"))
        for k2 in range(3):
            rect(cv, -30, -30 + k2 * 36, 160, 16, paint("#c9d0dc"))
        cv.restore()


def forest(cv, t):
    rect(cv, 0, 0, W, H, paint("#000", shader=lin_grad((0, 0), (0, H), [("#bfe8a8", 1), ("#5f9e4f", 1)])))
    cv.save()
    cv.translate(780, -100)
    cv.rotate(18)
    for k in range(7):
        rect(cv, -200 + k * 90, 0, 40, 2600, paint("#fffbe0", 0.12 + 0.05 * math.sin(t + k)))
    cv.restore()
    r = random.Random(6)
    for i in range(9):
        x = r.uniform(-50, 1130)
        w = r.uniform(50, 110)
        rect(cv, x - w / 2, 0, w, 1700, paint(r.choice(["#6d4c41", "#5d4037", "#795548"]), 0.95))
    for i in range(70):
        x, y = r.uniform(-100, 1180), r.uniform(-100, 700)
        circle(cv, x + math.sin(t * 0.8 + i) * 8, y, r.uniform(60, 130), paint(r.choice(["#3f8f46", "#4caf50", "#66bb6a", "#2e7d32"]), 0.9))
    for i in range(14):
        ph = (t * 0.12 + i / 14) % 1
        x = (i * 97 + math.sin(t + i) * 60) % W
        circle(cv, x, ph * H, 8, paint("#9ccc65", 0.9))
    rect(cv, -100, 1650, 1300, 400, paint("#4a7a3a"))
    # sign
    rect(cv, 300, 1300, 20, 400, paint("#5d4037"))
    rect(cv, 760, 1300, 20, 400, paint("#5d4037"))
    rrect(cv, 220, 1180, 640, 220, 14, paint("#6b4a2a"))
    rrect(cv, 236, 1196, 608, 188, 10, paint("#f2e6c9", stroke=5))
    text(cv, "NATIONAL", 540, 1280, font("black", 70), paint("#f2e6c9"), "center")
    text(cv, "FOREST", 540, 1360, font("black", 70), paint("#f2e6c9"), "center")


def winter(cv, t, tl):
    rect(cv, 0, 0, W, H, paint("#000", shader=lin_grad((0, 0), (0, H), [("#070b22", 1), ("#22305a", 1)])))
    starfield(cv, t, 0.9)
    k = prog(t, tl.s("s8"), tl.e("s8") + 0.5)
    sx, sy = lerp(-50, 1130, k), 360 - 80 * math.sin(k * math.pi)
    circle(cv, sx, sy, 6, paint("#ffffff", 0.6 + 0.4 * (int(t * 3) % 2)))
    glow(cv, sx, sy, 30, "#bfefff", 0.4)
    # street + houses
    for i, (x, h) in enumerate(((60, 380), (330, 460), (600, 400), (870, 500))):
        rect(cv, x - 120, 1500 - h, 250, h, paint("#151b33"))
        cv.drawPath(poly([(x - 140, 1500 - h), (x + 5, 1500 - h - 120), (x + 150, 1500 - h)]), paint("#1d2545"))
        cv.drawPath(poly([(x - 140, 1500 - h), (x + 5, 1500 - h - 120), (x + 150, 1500 - h)]), paint("#e8eef5", 0.8, stroke=10))
        for wy in range(int(1500 - h + 60), 1450, 110):
            rect(cv, x - 60, wy, 50, 60, paint("#ffd98a", 0.85 if (i + wy) % 3 else 0.2))
    # warm door
    dx = 870
    rect(cv, dx - 50, 1330, 100, 170, paint("#ffd98a"))
    glow(cv, dx, 1420, 220, "#ffd98a", 0.35)
    rect(cv, -100, 1500, 1300, 500, paint("#e8eef5"))
    # walking figure (back view silhouette)
    wx = lerp(260, 760, ease_io(k))
    bob = abs(math.sin(t * 6)) * 6
    cv.save()
    cv.translate(wx, 1440 - bob)
    rect(cv, -30, 0, 26, 110, paint("#2c3e50"))
    rect(cv, 4, 0, 26, 110, paint("#2c3e50"))
    cv.drawPath(smooth_path([(-60, 10), (-56, -140), (0, -170), (56, -140), (60, 10)], True), paint("#6a4c93"))
    circle(cv, 0, -200, 52, paint("#1c1412"))
    cv.restore()
    r = random.Random(4)
    for i in range(110):
        x = (r.uniform(0, W) + t * 25 * r.uniform(0.5, 1.5)) % W
        y = (r.uniform(0, H) + t * 90 * r.uniform(0.5, 1.2)) % H
        circle(cv, x, y, r.uniform(2, 5), paint("#ffffff", 0.85))


class Finale:
    def __init__(self, tl):
        self.tl = tl
        self.blink = Blinker(55, mean=3.2)
        self.bl = {"CYAN": Blinker(61, mean=4), "GOLD": Blinker(62, mean=4)}

    def draw(self, cv, t):
        tl = self.tl
        T, E = tl.s, tl.e
        u = prog(t, T("f1") - 0.5, E("f9"))
        top = mix("#2a2a6a", "#7fb8ff", u)
        bot = mix("#f2a65a", "#fff3d6", u)
        rect(cv, 0, 0, W, H, paint("#000", shader=lin_grad((0, 0), (0, H), [(top, 1), (bot, 1)])))
        sy = lerp(1500, 1250, u)
        glow(cv, 540, sy, 600, "#fff1c1", 0.6)
        circle(cv, 540, sy, 160, paint("#fff8e0"))
        # giant translucent voices in the sky
        for who, L, x in (("CYAN", CYAN, 250), ("GOLD", GOLD, 830)):
            f = expr("kind", glisten=0.6)
            f["gx"] = 0.4 if x < 540 else -0.4
            f["gy"] = 0.7
            f["turn"] = 0.15 if x < 540 else -0.15
            f["blink"] = self.bl[who](t)
            sp = tl.mouth(who, t)
            cv.saveLayerAlpha(None, int(255 * 0.55))
            cv.save()
            cv.translate(x, 560)
            cv.scale(1.6, 1.6)
            glow(cv, 0, 0, 220, "#7fe8ff" if who == "CYAN" else "#ffd86a", 0.5)
            draw_head(cv, L, f, t, sp)
            cv.restore()
            cv.restore()
        # ground + door
        cv.drawPath(smooth_path([(-100, 1560), (540, 1500), (1180, 1560), (1180, 2100), (-100, 2100)], True), paint("#7fae5f"))
        rect(cv, 700, 1240, 170, 300, paint("#ffd98a"))
        rect(cv, 690, 1230, 190, 14, paint("#6b4a2a"))
        # constituent looking up
        f = FaceTrack([(0, expr("hopeful", glisten=0.8)), (tl.wfind("f9", "love") - 0.2, expr("grin", glisten=1.0, tears=0.6))])(t)
        f["gy"] = -0.7
        f["gx"] = 0.1 * math.sin(t * 0.7)
        f["blink"] = self.blink(t)
        f["tilt"] = -6
        cv.save()
        cv.translate(470, 1520)
        cv.scale(0.95, 0.95)
        person(cv, CONSTITUENT, 0, -330, f, t, 0, ((-70, 220), (70, 220)), ("open", "open"), math.sin(t * 1.3) * 2)
        for s in (-1, 1):
            rect(cv, s * 40 - 24, -20, 48, 200, paint("#2c3e50"))
        cv.restore()
        # light flood on "I love you"
        lk = prog(t, tl.wfind("f9", "love") - 0.1, E("f9") + 1.8)
        if lk > 0:
            rect(cv, 0, 0, W, H, paint("#fff8e8", 0.85 * smooth(lk)))
