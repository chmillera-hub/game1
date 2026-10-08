"""Act 1: twelve views, bad advice, the hamster wheel and the money bag.
Also hosts the creator's bedroom used again in the finale."""
import math, random
import skia
from common import *
from characters import *
from cast import CREATOR, JESUS

COMMENTS = [("c1", "@grindset_bro", "bro just make a new account", "#e67e22"),
            ("c2", "@just_vibes", "the algorithm's just confused lol", "#9b59b6"),
            ("c3", "@growthhacks101", "delete it & re-upload on a CLEAN account!!", "#2ecc71"),
            ("c4", "@realist", "don't hate the player, hate the game", "#3498db")]


def draw_heart(cv, x, y, s, p):
    path = skia.Path()
    path.moveTo(x, y + s * 0.9)
    path.cubicTo(x - s * 1.6, y - s * 0.1, x - s * 0.7, y - s * 1.2, x, y - s * 0.35)
    path.cubicTo(x + s * 0.7, y - s * 1.2, x + s * 1.6, y - s * 0.1, x, y + s * 0.9)
    path.close()
    cv.drawPath(path, p)


def draw_coin(cv, x, y, r, spin=0.0, a=1.0):
    sx = abs(math.cos(spin)) * 0.85 + 0.15
    ellipse(cv, x, y, r * sx, r, paint("#b8860b", a))
    ellipse(cv, x, y, r * sx * 0.82, r * 0.82, paint("#f4c430", a))
    if sx > 0.5:
        text(cv, "$", x, y + r * 0.38, font("black", r * 1.05), paint("#b8860b", a), "center")


def draw_bag(cv, x, y, s, t, glow=0.0):
    cv.save()
    cv.translate(x, y)
    cv.scale(s, s)
    if glow > 0:
        circle(cv, 0, 0, 420, paint("#ffd84a", 0.35 * glow, blur=80))
    p = smooth_path([(-90, -250), (90, -250), (60, -180), (230, -40), (280, 140), (220, 280),
                     (0, 320), (-220, 280), (-280, 140), (-230, -40), (-60, -180)], True, 0.45)
    cv.drawPath(p, paint("#c8a165"))
    cv.save()
    cv.clipPath(p, skia.ClipOp.kIntersect, True)
    ellipse(cv, 120, 60, 150, 260, paint("#9c7a45", 0.45, blur=30))
    ellipse(cv, -120, -20, 70, 120, paint("#ffffff", 0.12, blur=20))
    cv.restore()
    cv.drawPath(p, paint("#7d5f33", stroke=6))
    rrect(cv, -95, -205, 190, 34, 16, paint("#8b5a2b"))
    text(cv, "$", 0, 150, font("black", 300), paint("#2e7d32"), "center")
    cv.restore()


class Opening:
    def __init__(self, tl):
        self.tl = tl
        T, E, Wd = tl.s, tl.e, tl.wfind
        self.T, self.E, self.Wd = T, E, Wd
        self.blink = Blinker(91)
        self.face = FaceTrack([
            (0, "tired"), (T("n1") + 1.2, expr("sad", lid=0.4)), (T("c1"), "deadpan"), (T("c2") + 0.5, "annoyed"),
            (T("c3"), expr("annoyed", twitch=0.6)), (T("c4"), "deadpan"), (T("n3"), expr("deadpan", twitch=0.0)),
            (Wd("n3", "Sure"), expr("annoyed", twitch=1.0)), (Wd("n3", "smartest"), "skeptical"),
            (Wd("n3", "confused", 1), "angry"), (T("n4"), "furious", 0.15),
            (T("n5"), expr("tired", sweat=1)), (Wd("n5", "Round"), expr("nervous", sweat=1)),
            (T("n9"), expr("tired", lid=0.35)), (Wd("n9", "Jesus"), "smile"), (Wd("n9", "fired"), "grin"),
        ])
        self.shots = [
            (0, (540, 1060, 1080), 0), (T("n1"), (560, 1110, 760), 3.6),
            (Wd("n2", "Twelve") - 0.15, "PHONE", 0),
            (T("n3") - 0.1, (600, 1150, 560), 0), (Wd("n3", "planet") , (600, 1130, 420), 1.6),
            (T("n4"), (600, 1110, 330), 0.15),
            (T("n5") - 0.05, "WHEEL", 0),
        ]
        self.wheel_start = T("n5") - 0.05
        self.reveal = T("n6")
        self.bag_t = Wd("n7", "that")
        self.cards_t = T("n8")
        self.count_t = Wd("n8", "It's")
        self.bed_back = T("n9") - 0.1

    # ------------------------------------------------------------ dispatch
    def draw(self, cv, t, world):
        if t < self.wheel_start:
            shot = self._shot(t)
            if shot == "PHONE":
                self.draw_phone(cv, t)
            else:
                world(cv, *shot, lambda c: self.draw_bedroom(c, t, night=1.0))
                if t < 1.4:
                    rect(cv, 0, 0, W, H, paint("#000", 1 - smooth(t / 1.4)))
        elif t < self.bed_back:
            self.draw_wheel_world(cv, t, world)
        else:
            k = prog(t, self.bed_back, self.E("n9") + 0.3)
            world(cv, 560, lerp(1080, 1060, k), lerp(900, 980, k), lambda c: self.draw_bedroom(c, t, night=1.0))
            self.draw_thought(cv, t)

    def _shot(self, t):
        cur = None
        for t0, s, d in self.shots:
            if t < t0:
                break
            if s == "PHONE" or s == "WHEEL":
                cur = s
                continue
            if d > 0 and isinstance(cur, tuple):
                u = ease_io(prog(t, t0, t0 + d))
                cur = tuple(lerp(a, b, u) for a, b in zip(cur, s))
            else:
                cur = s
        if isinstance(cur, tuple):
            cx, cy, w = cur
            if self.T("n4") < t < self.E("n4") + 0.2:
                cx += math.sin(t * 70) * 6
                cy += math.cos(t * 63) * 6
            return cx + noise1(t * 0.3, 5) * 4, cy + noise1(t * 0.3, 6) * 4, w
        return cur

    # ------------------------------------------------------------ bedroom
    def draw_bedroom(self, cv, t, night=1.0, phone=True, plant=0.0, notif=0.0, face=None, look=None):
        wall = mix("#e9b98f", "#1a2242", night)
        wall2 = mix("#f6d7b0", "#10152b", night)
        rect(cv, -600, -600, 2300, 3200, paint("#000", shader=lin_grad((0, 0), (0, 1900), [(wall2, 1), (wall, 1)])))
        # window
        wx, wy, ww, wh = 70, 260, 400, 520
        rrect(cv, wx - 18, wy - 18, ww + 36, wh + 36, 10, paint(mix("#fff4e0", "#2b3560", night)))
        sky = lin_grad((0, wy), (0, wy + wh), [(mix("#ffd27f", "#0b1030", night), 1), (mix("#ff9a6b", "#1d2a5a", night), 1)])
        rect(cv, wx, wy, ww, wh, paint("#000", shader=sky))
        cv.save()
        cv.clipRect(skia.Rect.MakeXYWH(wx, wy, ww, wh))
        if night > 0.3:
            r = random.Random(2)
            for _ in range(30):
                sx, sy = wx + r.random() * ww, wy + r.random() * wh * 0.6
                circle(cv, sx, sy, r.uniform(1.2, 3), paint("#ffffff", (0.4 + 0.6 * abs(math.sin(t * r.uniform(0.5, 2) + sx))) * night))
            circle(cv, wx + 290, wy + 120, 52, paint("#fdf6d8", night))
            circle(cv, wx + 312, wy + 108, 46, paint(mix("#ffd27f", "#0b1030", night), night))
        else:
            circle(cv, wx + 200, wy + wh - 40, 90, paint("#fff3c4", 1 - night, blur=10))
        r = random.Random(8)
        bx = wx - 10
        while bx < wx + ww:
            bw = r.uniform(40, 90)
            bh = r.uniform(80, 240)
            rect(cv, bx, wy + wh - bh, bw - 4, bh, paint(mix("#c27a5a", "#0d1226", night)))
            for yy in range(int(wy + wh - bh + 12), int(wy + wh), 26):
                for xx in range(int(bx + 8), int(bx + bw - 12), 16):
                    if r.random() < 0.4:
                        rect(cv, xx, yy, 7, 11, paint("#ffd77a", 0.8 * night))
            bx += bw
        cv.restore()
        line(cv, wx + ww / 2, wy, wx + ww / 2, wy + wh, paint(mix("#fff4e0", "#2b3560", night), stroke=10))
        line(cv, wx, wy + wh / 2, wx + ww, wy + wh / 2, paint(mix("#fff4e0", "#2b3560", night), stroke=10))
        # sill + plant pot
        rect(cv, wx - 40, wy + wh + 18, ww + 80, 26, paint(mix("#fff4e0", "#2b3560", night)))
        px, py = wx + ww - 70, wy + wh + 18
        cv.drawPath(poly([(px - 46, py - 70), (px + 46, py - 70), (px + 34, py), (px - 34, py)]), paint(mix("#c0603a", "#4a2a2a", night)))
        rect(cv, px - 50, py - 80, 100, 16, paint(mix("#a24f2e", "#3a2020", night)))
        if plant > 0:
            g = ease_out(plant)
            cv.drawPath(quad_path((px, py - 78), (px + 4, py - 78 - 40 * g), (px - 2, py - 78 - 70 * g)),
                        paint("#4caf50", stroke=7))
            for s in (-1, 1):
                cv.save()
                cv.translate(px - 2, py - 78 - 70 * g)
                cv.rotate(s * 35 - 10)
                cv.scale(g, g)
                ellipse(cv, s * 26, 0, 28, 13, paint("#66bb6a"))
                cv.restore()
            if plant > 0.5:
                circle(cv, px, py - 120, 120, paint("#fff3b0", 0.18 * (plant - 0.5), blur=40))
        # poster
        rrect(cv, 700, 360, 280, 380, 6, paint(mix("#f2e6d0", "#2a3050", night)))
        rrect(cv, 720, 380, 240, 340, 4, paint(mix("#4e8fbf", "#1f2c4a", night)))
        text(cv, "KEEP", 840, 520, font("black", 56), paint(mix("#ffffff", "#7f8db5", night)), "center")
        text(cv, "MAKING", 840, 580, font("black", 56), paint(mix("#ffffff", "#7f8db5", night)), "center")
        text(cv, "THINGS", 840, 640, font("black", 56), paint(mix("#ffffff", "#7f8db5", night)), "center")
        # bed headboard
        rrect(cv, 140, 1000, 900, 520, 50, paint(mix("#7a4f35", "#2a1e2a", night)))
        rrect(cv, 170, 1030, 840, 470, 40, paint(mix("#8e6142", "#33253a", night)))
        rrect(cv, 260, 1120, 300, 170, 60, paint(mix("#fbf3e6", "#4a5070", night)))
        # creator
        L = CREATOR
        f = face(t) if face else self.face(t)
        f["blink"] = self.blink(t)
        if look is not None:
            f["gx"], f["gy"], f["turn"] = look
        else:
            f["gy"] = 0.65 if phone else -0.2
            f["gx"] = 0.0
        if self.T("n9") < t < self.E("n9") + 1:
            f["gy"] = -0.8
            f["gx"] = -0.3
        sp = self.tl.mouth("NARR", t) * 0.0
        cx, cy = 600, 1310
        cv.save()
        cv.translate(cx, cy)
        draw_torso(cv, L, t, math.sin(t * 1.3))
        draw_neck(cv, L)
        cv.save()
        cv.translate(0, -112 + noise1(t * 0.4, 3) * 3)
        draw_head(cv, L, f, t, sp)
        # phone glow on face
        if phone and night > 0.5:
            circle(cv, 0, 30, 140, paint("#8fd3ff", 0.18 * night, blur=40))
        cv.restore()
        # phone + hands
        if phone:
            ph_y = 170
            draw_arm(cv, L, -1, (-46, ph_y + 40), "fist", 0, L.c1)
            draw_arm(cv, L, 1, (46, ph_y + 40), "fist", 0, L.c1)
            rrect(cv, -62, ph_y - 70, 124, 210, 18, paint("#1c1c22"))
            circle(cv, -30, ph_y - 44, 9, paint("#333"))
            if night > 0.5:
                cv.drawPath(poly([(-60, ph_y - 70), (60, ph_y - 70), (90, -60), (-90, -60)]), paint("#9fdcff", 0.05))
            draw_hand(cv, L, -50, ph_y + 30, "fist", -1)
            draw_hand(cv, L, 50, ph_y + 30, "fist", 1)
            if notif > 0:
                self._notif_bubble(cv, 0, -400, notif)
        else:
            draw_arm(cv, L, -1, (-70, 240), "fist", 0, L.c1)
            draw_arm(cv, L, 1, (70, 240), "fist", 0, L.c1)
        cv.restore()
        # blanket
        bl = smooth_path([(-100, 1500), (300, 1440), (700, 1470), (1180, 1430), (1180, 2600), (-100, 2600)], True, 0.4)
        cv.drawPath(bl, paint(mix("#d9785f", "#3c3f6e", night)))
        for k in range(5):
            cv.drawPath(quad_path((0, 1560 + k * 70), (540, 1520 + k * 70), (1080, 1560 + k * 70)),
                        paint(mix("#c46550", "#33365e", night), stroke=6))
        if night > 0.5:
            rect(cv, -600, -600, 2300, 3200, paint("#0a0e22", 0.25 * night))
            # cool phone light spill
            if phone:
                circle(cv, cx, cy + 40, 420, paint("#7fc8ff", 0.08, blur=60))

    def _notif_bubble(self, cv, x, y, k):
        a = clamp(k * 2)
        s = ease_back(k)
        cv.save()
        cv.translate(x, y)
        cv.scale(s, s)
        rrect(cv, -330, -70, 660, 140, 30, paint("#000", 0.25 * a, blur=12))
        rrect(cv, -330, -80, 660, 140, 30, paint("#ffffff", a))
        circle(cv, -260, -10, 38, paint("#f39c12", a))
        text(cv, "@someone_who_needed_it", -205, -28, font("bold", 26), paint("#555", a))
        text(cv, "this made me feel less alone.", -205, 8, font("semi", 30), paint("#111", a))
        text(cv, "thank you", -205, 42, font("semi", 30), paint("#111", a))
        draw_heart(cv, -50, 36, 14, paint("#e74c3c", a))
        cv.restore()

    # ------------------------------------------------------------ phone
    def draw_phone(self, cv, t):
        rect(cv, 0, 0, W, H, paint("#0b0f1e"))
        jx = noise1(t * 0.8, 1) * 8
        jy = noise1(t * 0.8, 2) * 8
        cv.save()
        cv.translate(jx, jy)
        rrect(cv, 50, 70, 980, 1780, 90, paint("#16161c"))
        rrect(cv, 70, 90, 940, 1740, 74, paint("#fafafa"))
        cv.save()
        cv.clipRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(70, 90, 940, 1740), 74, 74), True)
        text(cv, "2:47", 150, 160, font("bold", 38), paint("#111"))
        rrect(cv, 830, 132, 70, 32, 8, paint("#111", stroke=3))
        rect(cv, 836, 138, 9, 20, paint("#e74c3c"))
        rrect(cv, 480, 120, 120, 40, 20, paint("#111"))
        text(cv, "Your videos", 130, 260, font("black", 60), paint("#111"))
        # thumbnail
        tx, ty, tw, th = 130, 300, 820, 560
        rrect(cv, tx, ty, tw, th, 28, paint("#000", shader=lin_grad((tx, ty), (tx + tw, ty + th), [("#ff9a8b", 1), ("#a18cd1", 1)])))
        draw_heart(cv, tx + tw / 2, ty + th / 2 - 30, 110, paint("#ffffff", 0.9))
        circle(cv, tx + tw / 2, ty + th / 2 - 30, 60, paint("#000", 0.25))
        cv.drawPath(poly([(tx + tw / 2 - 18, ty + th / 2 - 62), (tx + tw / 2 + 30, ty + th / 2 - 30), (tx + tw / 2 - 18, ty + th / 2 + 2)]),
                    paint("#ffffff"))
        text(cv, "I made this for anyone who", tx + 30, ty + th - 80, font("black", 40), paint("#fff"))
        text(cv, "feels invisible 🎵" if False else "feels invisible", tx + 30, ty + th - 32, font("black", 40), paint("#fff"))
        # stats
        k = pulse(t, self.Wd("n2", "Twelve") - 0.1, 0.2, 0.9, 0.4)
        cv.save()
        cv.translate(240, 960)
        cv.scale(1 + 0.35 * k, 1 + 0.35 * k)
        ellipse(cv, -70, -14, 34, 22, paint("#111", stroke=6))
        circle(cv, -70, -14, 10, paint("#111"))
        text(cv, "12", -20, 6, font("black", 64), paint(mix("#111", "#e74c3c", k)))
        text(cv, "views", 68, 4, font("semi", 36), paint("#666"))
        cv.restore()
        draw_heart(cv, 640, 944, 22, paint("#e74c3c"))
        text(cv, "1", 680, 962, font("black", 48), paint("#111"))
        nc = sum(1 for c in COMMENTS if t >= self.T(c[0]) - 0.15)
        rrect(cv, 780, 920, 52, 42, 10, paint("#111", stroke=5))
        text(cv, str(nc), 850, 962, font("black", 48), paint("#111"))
        line(cv, 130, 1010, 950, 1010, paint("#ddd", stroke=3))
        text(cv, "Comments", 130, 1075, font("black", 44), paint("#111"))
        for i, (cid, user, msg, col) in enumerate(COMMENTS):
            t0 = self.T(cid) - 0.15
            if t < t0:
                continue
            u = ease_back(prog(t, t0, t0 + 0.35))
            y = 1110 + i * 170
            cv.save()
            cv.translate(540, y + 70)
            cv.scale(u, u)
            cv.translate(-540, -y - 70)
            rrect(cv, 120, y, 840, 150, 28, paint("#f0f2f5"))
            circle(cv, 190, y + 75, 42, paint(col))
            text(cv, user[1].upper(), 190, y + 92, font("black", 44), paint("#fff"), "center")
            text(cv, user, 255, y + 55, font("bold", 30), paint("#555"))
            words = msg
            fz = 34 if len(words) < 34 else 30
            text(cv, words, 255, y + 105, font("semi", fz), paint("#111"))
            cv.restore()
        cv.restore()
        cv.restore()

    # ------------------------------------------------------------ hamster wheel world
    def draw_wheel_world(self, cv, t, world):
        T, E, Wd = self.T, self.E, self.Wd
        # camera: wheel close -> pull back to show machine -> pan to the money bag
        c0 = (540, 960, 1150)
        c1 = (540, 1500, 2150)
        c2 = (560, 2560, 1350)
        u1 = ease_io(prog(t, self.reveal - 0.2, self.reveal + 2.6))
        u2 = ease_io(prog(t, self.bag_t - 0.55, self.bag_t + 0.1))
        cam = tuple(lerp(a, b, u1) for a, b in zip(c0, c1))
        cam = tuple(lerp(a, b, u2) for a, b in zip(cam, c2))
        cx, cy, w = cam
        if self.bag_t < t < self.bag_t + 0.4:
            k = 1 - prog(t, self.bag_t, self.bag_t + 0.4)
            cx += math.sin(t * 80) * 10 * k
        world(cv, cx, cy, w, lambda c: self._wheel_scene(c, t))
        self._overlay_cards(cv, t)

    def wheel_angle(self, t):
        t0 = self.wheel_start
        fast = Wd = self.Wd("n5", "Round")
        a = 0.0
        # integrate speed: base 1.2 rad/s, ramps to 5 after "Round"
        d = max(0, t - t0)
        d2 = max(0, t - fast)
        return 1.4 * d + 1.6 * d2 * d2 / 2 if d2 < 2.5 else 1.4 * d + 1.6 * 2.5 * 2.5 / 2 + 4.0 * (d2 - 2.5)

    def _wheel_scene(self, cv, t):
        T, E, Wd = self.T, self.E, self.Wd
        rect(cv, -2000, -2000, 5000, 7000, paint("#000", shader=rad_grad((540, 1000), 1600, [("#2a2f4a", 1), ("#0c0e18", 1)])))
        circle(cv, 540, 1000, 700, paint("#ffffff", 0.05, blur=60))
        wx, wy, R = 540, 900, 400
        ang = self.wheel_angle(t)
        # belt to machine
        my = 1700
        cv.drawPath(poly([(wx - 30, wy), (wx - 120, my)], False), paint("#222", stroke=14))
        cv.drawPath(poly([(wx + 30, wy), (wx + 120, my)], False), paint("#222", stroke=14))
        dash = (t * 300) % 60
        for s in (-1, 1):
            for k in range(14):
                u = (k * 60 + dash * s) % 840 / 840
                bx = lerp(wx + 30 * s, wx + 120 * s, u)
                by = lerp(wy, my, u)
                circle(cv, bx, by, 5, paint("#666"))
        # stand
        cv.drawPath(poly([(wx - 300, wy + 560), (wx, wy), (wx + 300, wy + 560)], False), paint("#5a6070", stroke=26))
        rect(cv, wx - 360, wy + 550, 720, 30, paint("#5a6070"))
        # wheel back rim
        circle(cv, wx, wy, R, paint("#9aa3b5", stroke=26))
        for k in range(16):
            a = ang + k * math.pi / 8
            line(cv, wx, wy, wx + R * math.cos(a), wy + R * math.sin(a), paint("#7d869a", stroke=8))
        for k in range(48):
            a = ang + k * math.pi / 24
            line(cv, wx + (R - 16) * math.cos(a), wy + (R - 16) * math.sin(a), wx + (R + 14) * math.cos(a),
                 wy + (R + 14) * math.sin(a), paint("#c3c9d6", stroke=5))
        circle(cv, wx, wy, 34, paint("#c3c9d6"))
        # runner
        self._runner(cv, wx, wy + R - 18, t)
        # front rim
        circle(cv, wx, wy, R + 2, paint("#c3c9d6", stroke=10))
        # account signs popping on each "Fresh account" / "Upload it again"
        pops = []
        L = self.tl.by_id["n5"]
        n = 1
        for i, wd in enumerate(L["words"]):
            if wd[0].lower().startswith("fresh"):
                n += 1
                pops.append((L["start"] + wd[1], f"ACCOUNT #{n}", "#f39c12"))
            if wd[0].lower().startswith("upload"):
                pops.append((L["start"] + wd[1], "UPLOADING...", "#3498db"))
        for k, (tp, label, col) in enumerate(pops):
            if t < tp:
                continue
            age = t - tp
            u = ease_back(prog(age, 0, 0.3))
            fade = 1 - prog(age, 1.2, 1.7)
            if fade <= 0:
                continue
            x = wx + (-250 if k % 2 == 0 else 250)
            y = wy - R - 40 - age * 40
            cv.save()
            cv.translate(x, y)
            cv.rotate(-8 if k % 2 == 0 else 8)
            cv.scale(u, u)
            rrect(cv, -170, -50, 340, 100, 20, paint(col, fade))
            text(cv, label, 0, 16, font("black", 40), paint("#fff", fade), "center")
            cv.restore()
        # counter
        tr = Wd("n5", "Round")
        if t > tr:
            cnt = 7 + int((t - tr) * 9)
            text_outlined(cv, f"ACCOUNTS CREATED: {cnt}", wx, wy - R - 160, font("black", 54), "#ff6b6b", ow=10)
        # sweat drops flying
        if t > T("n5") + 1:
            r = random.Random(int(t * 6))
            for _ in range(3):
                circle(cv, wx + r.uniform(-60, 60), wy + R - 300 + r.uniform(-40, 40), 6, paint("#8fd0ff", 0.8))
        self._machine(cv, wx, my, t)
        draw_bag(cv, 560, 2700, 1.0, t, glow=pulse(t, self.bag_t, 0.2, 1.5, 1.0))
        # coins pouring from chute into the bag
        cv_chute = (860, 2060)
        cv.drawPath(poly([(760, 1900), (900, 1900), (900, 2120), (760, 2050)]), paint("#4b5262"))
        r = random.Random(4)
        for i in range(40):
            ph = (t * 0.8 + i / 40) % 1.0
            if t < self.reveal:
                break
            x = 840 + ph * -240 + r.uniform(-40, 40)
            y = 2080 + ph * 520 + ph * ph * 200
            if y > 2500:
                continue
            draw_coin(cv, x, y, 26, t * 6 + i)
        r = random.Random(9)
        for i in range(18):
            x = 560 + r.uniform(-320, 320)
            y = 2960 + r.uniform(-10, 40)
            draw_coin(cv, x, y, 30, i)

    def _runner(self, cv, x, y, t):
        L = CREATOR
        d = max(0, t - self.wheel_start)
        speed = 1.0 + 1.6 * clamp(t - self.Wd("n5", "Round"), 0, 2.5)
        ph = d * 7 * speed
        cv.save()
        cv.translate(x, y)
        cv.scale(0.62, 0.62)
        cv.translate(0, -545 - abs(math.sin(ph)) * 18)
        cv.rotate(8)
        col = L.c1
        pants = "#2c3e50"
        hip = (0, 300)
        draw_torso(cv, L, t)
        for s, off in ((-1, 0), (1, math.pi)):
            a = math.sin(ph + off)
            kx, ky = hip[0] + a * 80, hip[1] + 120 - abs(a) * 20
            fx, fy = kx + math.sin(ph + off - 1.2) * 70 - 20, ky + 115
            cv.drawPath(poly([hip, (kx, ky), (fx, fy)], False), paint(shade(pants, -0.2 if s < 0 else 0), stroke=46))
            ellipse(cv, fx + 18, fy + 10, 36, 16, paint("#f4f4f4" if s > 0 else "#d9d9d9"))
        for s, off in ((-1, math.pi), (1, 0)):
            a = math.sin(ph + off)
            hx, hy = s * 40 + a * 90, 150 - abs(a) * 30
            draw_arm(cv, L, s, (hx, hy), "fist", 0, col)
        f = self.face(t)
        f["blink"] = self.blink(t)
        f["turn"] = 0.35
        f["gx"] = 0.6
        cv.save()
        cv.translate(8, -112)
        draw_head(cv, L, f, t, 0.25 + 0.25 * abs(math.sin(ph * 0.5)))
        cv.restore()
        cv.restore()

    def _machine(self, cv, x, y, t):
        rrect(cv, x - 380, y, 760, 440, 40, paint("#3d4455"))
        rrect(cv, x - 360, y + 20, 720, 400, 30, paint("#4b5367"))
        text(cv, "PLATFORM™", x, y + 95, font("black", 64), paint("#e6e9ef"), "center")
        text(cv, "GROWTH ENGINE", x, y + 150, font("bold", 40), paint("#aab3c5"), "center")
        for k, gx in enumerate((x - 220, x + 220)):
            cv.save()
            cv.translate(gx, y + 300)
            cv.rotate(t * 120 * (1 if k else -1))
            for j in range(10):
                cv.rotate(36)
                rect(cv, -14, -96, 28, 30, paint("#8a93a8"))
            circle(cv, 0, 0, 72, paint("#8a93a8"))
            circle(cv, 0, 0, 24, paint("#3d4455"))
            cv.restore()
        # gauge
        circle(cv, x, y + 300, 80, paint("#f4f4f4"))
        cv.drawPath(poly([(x - 60, y + 300), (x + 60, y + 300)], False), paint("#ccc", stroke=2))
        a = -math.pi + 0.3 + (0.5 + 0.5 * math.sin(t * 2)) * (math.pi - 0.6) * 0.3 + (math.pi - 0.6) * 0.65
        line(cv, x, y + 300, x + 62 * math.cos(a), y + 300 + 62 * math.sin(a), paint("#e74c3c", stroke=6))
        text(cv, "NEW USERS", x, y + 360, font("black", 20), paint("#333"), "center")
        # chimney puffs
        for i in range(4):
            ph = (t * 0.6 + i / 4) % 1
            circle(cv, x + 300 + ph * 60, y - 40 - ph * 260, 30 + ph * 50, paint("#9aa3b5", 0.5 * (1 - ph)))
        rect(cv, x + 270, y - 60, 60, 70, paint("#3d4455"))

    def _overlay_cards(self, cv, t):
        t0 = self.cards_t
        if t < t0 - 0.1 or t > self.bed_back:
            return
        out = prog(t, self.count_t - 0.2, self.count_t + 0.2)
        for i in range(2):
            u = ease_back(prog(t, t0 + i * (self.Wd("n8", "Old") - t0), t0 + i * (self.Wd("n8", "Old") - t0) + 0.4))
            if u <= 0:
                continue
            a = 1 - out
            if a <= 0:
                continue
            x = 300 if i == 0 else 780
            y = 560
            cv.save()
            cv.translate(x, y)
            cv.rotate(-4 if i == 0 else 4)
            cv.scale(u, u)
            rrect(cv, -230, -230, 460, 470, 36, paint("#000", 0.35 * a, blur=16))
            rrect(cv, -230, -240, 460, 470, 36, paint("#ffffff", a))
            col = "#2ecc71" if i == 0 else "#95a5a6"
            circle(cv, 0, -110, 80, paint(col, a))
            if i == 0:
                text(cv, "NEW", 0, -92, font("black", 46), paint("#fff", a), "center")
                text(cv, "New account", 0, 20, font("black", 42), paint("#111", a), "center")
                text(cv, "Likely to spend", 0, 80, font("semi", 34), paint("#555", a), "center")
                text(cv, "$$$  ▲", 0, 160, font("black", 64), paint("#2ecc71", a), "center")
            else:
                f = expr("sad")
                cv.save()
                cv.translate(0, -110)
                cv.scale(0.75, 0.75)
                draw_head(cv, CREATOR, f, t)
                cv.restore()
                text(cv, "Your account", 0, 20, font("black", 42), paint("#111", a), "center")
                text(cv, "Spent so far", 0, 80, font("semi", 34), paint("#555", a), "center")
                text(cv, "$0.00", 0, 160, font("black", 64), paint("#e74c3c", a), "center")
                sk = prog(t, self.Wd("n8", "Not") - 0.05, self.Wd("n8", "Not") + 0.15)
                if sk > 0:
                    cv.save()
                    cv.rotate(-18)
                    s = lerp(2, 1, ease_in(sk))
                    cv.scale(s, s)
                    rrect(cv, -210, -50, 420, 100, 14, paint("#e74c3c", clamp(sk * 2) * a, stroke=10))
                    text(cv, "HIDDEN", 0, 30, font("black", 76), paint("#e74c3c", clamp(sk * 2) * a), "center")
                    cv.restore()
            cv.restore()
        # counting: big revenue ticker
        if t > self.count_t - 0.1:
            u = ease_back(prog(t, self.count_t, self.count_t + 0.4))
            v = 1_284_903_221 + int((t - self.count_t) * 7_919_311)
            cv.save()
            cv.translate(540, 560)
            cv.scale(u, u)
            rrect(cv, -470, -120, 940, 230, 40, paint("#0f3d24"))
            rrect(cv, -470, -120, 940, 230, 40, paint("#2ecc71", stroke=6))
            text(cv, "REVENUE", 0, -50, font("black", 40), paint("#7dffb0"), "center")
            text(cv, f"${v:,}", 0, 60, font("mono", 84), paint("#7dffb0"), "center")
            cv.restore()

    # ------------------------------------------------------------ thought bubble
    def draw_thought(self, cv, t):
        t0 = self.Wd("n9", "Jesus") - 0.2
        u = ease_back(prog(t, t0, t0 + 0.45))
        if u <= 0:
            return
        bx, by = 560, 560
        for i, (dx, dy, r) in enumerate(((560 - 40, 900, 22), (560 - 10, 820, 34))):
            circle(cv, dx, dy, r * u, paint("#ffffff"))
        cv.save()
        cv.translate(bx, by)
        cv.scale(u, u)
        cl = smooth_path([(-330, 0), (-300, -150), (-150, -230), (60, -240), (250, -180), (340, -40),
                          (300, 120), (140, 210), (-80, 220), (-260, 150)], True, 0.6)
        cv.drawPath(cl, paint("#ffffff"))
        # mini board table + Jesus
        rect(cv, -250, 60, 300, 40, paint("#835c42"))
        for k in range(3):
            circle(cv, -210 + k * 100, 20, 30, paint(["#f0c09c", "#8a5638", "#f6d2b6"][k]))
            rect(cv, -235 + k * 100, 45, 50, 30, paint(["#1f2b47", "#5c6575", "#26364a"][k]))
        cv.save()
        cv.translate(170, 10)
        cv.scale(0.55, 0.55)
        f = expr("kind")
        f["blink"] = self.blink(t + 1)
        draw_head(cv, JESUS, f, t)
        cv.restore()
        fk = prog(t, self.Wd("n9", "fired") - 0.05, self.Wd("n9", "fired") + 0.15)
        if fk > 0:
            cv.save()
            cv.rotate(-14)
            s = lerp(2.2, 1, ease_in(fk))
            cv.scale(s, s)
            a = clamp(fk * 2)
            rrect(cv, -190, -70, 380, 130, 16, paint("#e74c3c", a, stroke=12))
            text(cv, "FIRED", 0, 34, font("black", 100), paint("#e74c3c", a), "center")
            cv.restore()
        cv.restore()
