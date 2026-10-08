"""The green room: the couch, the cast, the Director (a CRT with pixel eyes), chaos mode."""
import copy, math, random
import skia
from common import *
from characters import *
from cast import CEO, CFO, TYLER, PAM, JESUS, KID, CYAN, GOLD

def glow(cv, x, y, r, col, a):
    circle(cv, x, y, r, paint(col, a, blur=r * 0.35))


FLOOR = 1880
TV = (850, 470)
SEAT = {"CFO": 520, "CEO": 850, "TYLER": 1180}
SHOULDER = 1330
PAM_XY = (1500, 1300)
KID_XY = (690, 1665)
ANGEL = {"CYAN": (1330, 760), "GOLD": (1560, 800)}
LOOKS = {"CEO": CEO, "CFO": CFO, "TYLER": TYLER, "PAM": PAM, "KID": KID, "CYAN": CYAN, "GOLD": GOLD, "JESUS": JESUS}
CEO_BLUE = copy.copy(CEO)
CEO_BLUE.skin = "#8fb4ff"

SHOTS = {
    "WIDE": (850, 1250, 1700), "TV": (850, 520, 720), "TV_C": (850, 480, 560), "COUCH": (850, 1420, 1250),
    "CEO_M": (850, 1340, 660), "CFO_M": (520, 1340, 660), "TYLER_M": (1180, 1340, 660),
    "PAM_M": (1500, 1320, 640), "KID_M": (700, 1600, 680), "ANGELS": (1445, 760, 720),
    "ANGEL_LEGS": (1445, 960, 760), "DOOR": (330, 1440, 900), "ROOM_HI": (850, 900, 1500),
}


class Room:
    def __init__(self, tl):
        self.tl = tl
        T, E, Wd = tl.s, tl.e, tl.wfind
        self.T, self.E, self.Wd = T, E, Wd
        self.blink = {k: Blinker(i * 17 + 5) for i, k in enumerate(list(LOOKS) + ["DIR"])}
        self.boot_on = 1.2
        self.wake = 2.6
        self.chaos0 = E("d9") + 0.1
        self.chaos1 = T("door") + 0.05
        self.door0 = T("door")
        self.bow = Wd("d10", "bow") + 0.2
        self.tv_off = T("end") + 5.2
        F = FaceTrack
        aw = expr("awkward", sweat=0)
        self.face = {
            "CEO": F([(0, "sleepy"), (self.wake, "tired"), (T("c1"), "deadpan"), (T("d2"), "shocked", 0.15),
                      (T("hush") + 1.2, "nervous"), (T("t2"), "annoyed"), (T("c2"), "smug"), (T("c3"), "smile"),
                      (T("m2"), "awkward"), (T("d3"), "neutral"), (Wd("d5", "receipts"), expr("smile", glisten=0.5)),
                      (T("c4"), "stern"), (T("t6"), "deadpan"), (T("c5"), "annoyed"), (T("d6"), "skeptical"),
                      (T("c6"), expr("sad", glisten=0.4)), (T("k2"), "confused"), (T("p3"), "neutral"),
                      (T("think"), "nervous"), (T("d7"), "neutral"), (T("d8"), expr("sad", glisten=0.6)),
                      (T("m4"), "smile"), (self.chaos0, "excited"), (T("c7"), "grin"), (self.door0, "shocked", 0.1),
                      (T("j2"), "awkward"), (T("d10"), "smile")]),
            "CFO": F([(0, "sleepy"), (self.wake + 0.3, "neutral"), (T("d2"), "shocked", 0.15), (T("hush") + 1.0, "skeptical"),
                      (T("m1"), "smug"), (T("c2"), "skeptical"), (T("m2"), "deadpan"), (T("d3"), "skeptical"),
                      (T("m3"), expr("hopeful", glisten=1.0, tears=0.8)), (T("t5"), "neutral"), (T("c4"), "annoyed"),
                      (T("c5"), "smile"), (T("p3"), "neutral"), (T("d8"), expr("compassion", glisten=0.8)),
                      (T("m4"), "smile"), (self.chaos0, "grin"), (T("m5"), "smug"), (self.door0, "shocked", 0.1),
                      (T("j2"), "smile"), (T("d10"), "kind")]),
            "TYLER": F([(0, "sleepy"), (self.wake + 0.1, "tired"), (T("t1"), "annoyed"), (T("d2"), "shocked", 0.15),
                        (T("t2"), "excited"), (T("t3"), "confused"), (T("m1"), "smug"), (T("d3"), "confused"),
                        (T("t4"), "smile"), (T("d4"), "nervous"), (T("t5"), "deadpan"), (T("t6"), "annoyed"),
                        (T("p3"), "neutral"), (T("d8"), expr("sad", glisten=1.0, tears=1.0)), (T("t7"), expr("wince", glisten=1.0, tears=1.0)),
                        (T("m4"), "excited"), (self.chaos0, "grin"), (self.door0, "shocked", 0.1), (T("d10"), "smile")]),
            "PAM": F([(0, "sleepy"), (self.wake + 0.5, "neutral"), (T("d2"), "shocked", 0.15), (T("hush") + 0.8, aw),
                      (T("d3"), "smile"), (T("p1"), "nervous"), (T("d5"), "hopeful"), (T("p2"), "excited"),
                      (T("p3"), "hopeful"), (T("d7"), expr("hopeful", glisten=1.0)), (T("m4"), "excited"),
                      (self.chaos0, "grin"), (self.door0, "shocked", 0.1), (T("j1") + 0.5, "excited"), (T("d10"), "smile"),
                      (T("p5"), expr("kind", glisten=0.6))]),
            "KID": F([(0, "sleepy"), (self.wake + 0.2, "tired"), (T("d2"), "shocked", 0.15), (T("hush") + 1.0, "confused"),
                      (T("d3"), "smile"), (T("k1"), "annoyed"), (T("k2"), "confused"), (T("d6b"), "kind"),
                      (T("d8"), expr("hopeful", glisten=0.8)), (self.chaos0, "grin"), (T("k3"), expr("excited", glisten=0.8)),
                      (self.door0, "shocked", 0.1), (T("d10"), "smile")]),
            "CYAN": F([(0, "serene"), (T("y1"), "smug"), (T("g2"), "sad"), (T("y2"), "kind"), (T("d8"), expr("compassion", glisten=0.7)),
                       (self.chaos0, "grin"), (self.door0, "shocked", 0.1), (T("j1") + 0.5, "kind")]),
            "GOLD": F([(0, "kind"), (T("g1"), expr("sad", lid=0.3)), (T("g2"), "deadpan"), (T("d8"), expr("compassion", glisten=0.7)),
                       (self.chaos0, "grin"), (self.door0, "shocked", 0.1), (T("j1") + 0.5, "kind")]),
            "JESUS": F([(0, "kind"), (T("j2"), "smile")]),
        }
        # director's mood: (time, mood)
        self.dir_mood = Keys([(0, (0.0, 0.0, 0.0)), (T("d2"), (0.0, -0.2, 0.0)), (T("d3"), (0.0, 0.6, 0.0)),
                              (T("t5"), (0.25, 0.0, 0.0)), (T("y1"), (0.45, -0.2, 0.0)), (T("d6"), (0.3, 0.0, 0.0)),
                              (T("p3"), (0.0, 0.3, 0.0)), (T("think"), (0.55, -0.4, 0.0), 1.0), (T("d7"), (0.3, -0.2, 0.3), 0.8),
                              (T("d8"), (0.25, 0.1, 0.8)), (E("d8") + 1.0, (0.1, 0.4, 0.4)), (T("d9"), (0.0, 0.9, 0.0)),
                              (self.door0, (0.0, -0.3, 0.0), 0.15), (T("j2"), (0.15, 0.7, 0.3)), (T("d10"), (0.1, 0.6, 0.0)),
                              (T("p5"), (0.3, 0.4, 0.4))])   # (lid, happy, tear)
        self.stand = {"CEO": Keys([(0, 0.0), (T("c2") - 0.4, 1.0, 0.5), (E("c3") + 0.3, 0.0, 0.5),
                                   (self.chaos0, 1.0, 0.4), (T("door") + 0.6, 1.0), (self.bow - 1.0, 1.0)]),
                      "CFO": Keys([(0, 0.0), (T("m4") - 0.2, 1.0, 0.5), (self.chaos0 + 1.0, 1.0)]),
                      "TYLER": Keys([(0, 0.0), (T("t2") + 0.2, 1.0, 0.3), (E("t3") + 0.2, 0.0, 0.4),
                                     (self.chaos0 + 0.3, 1.0, 0.4)])}
        self.pen_drop = T("hush") + 0.5

    # ------------------------------------------------------------ helpers
    def chaos(self, t):
        return self.chaos0 < t < self.chaos1

    def pos(self, who, t):
        if who in SEAT:
            st = smooth(self.stand[who](t)) if who in self.stand else 0
            return SEAT[who], SHOULDER - 95 * st
        if who == "PAM":
            return PAM_XY
        if who == "KID":
            return KID_XY
        if who in ANGEL:
            x, y = ANGEL[who]
            return x, y + math.sin(t * 1.2 + x) * 10
        if who == "JESUS":
            return self.jesus_x(t), 1560
        return TV

    def jesus_x(self, t):
        return lerp(-200, 330, ease_out(prog(t, self.door0 + 0.3, self.door0 + 1.6)))

    def target(self, who, t):
        L = self.tl.current(t)
        if self.door0 < t < self.T("d10"):
            return "JESUS" if who != "JESUS" else "DIR"
        if t < self.wake + 0.6:
            return "DIR"
        if self.T("hush") < t < self.E("hush"):
            others = [k for k in ("CEO", "CFO", "TYLER", "PAM", "KID") if k != who]
            return others[int((t * 1.7 + len(who)) % len(others))]
        if L is None:
            L = self.tl.last_speaker(t)
        if L is None:
            return "DIR"
        if L["who"] == who:
            return "DIR" if who != "DIR" else "CEO"
        return L["who"]

    def look_xy(self, name, t):
        if name == "DIR":
            return TV[0], TV[1] + 40
        x, y = self.pos(name, t)
        return x, y - 112

    def gaze(self, who, t):
        hx, hy = self.look_xy(who, t)

        def g(tt):
            n = self.target(who, tt)
            if n == who:
                return 0.0, 0.0
            p = self.look_xy(n, tt)
            return p[0] - hx, p[1] - hy
        a = [g(t - k * 0.06) for k in range(6)]
        dx = sum(v[0] for v in a) / 6
        dy = sum(v[1] for v in a) / 6
        return (clamp(dx / 300, -1, 1) + noise1(t * 1.6, len(who)) * 0.07,
                clamp(dy / 420, -1, 1) + noise1(t * 1.2, len(who) + 3) * 0.05,
                clamp(dx / 1300, -0.45, 0.45))

    def face_for(self, who, t):
        f = self.face[who](t)
        gx, gy, turn = self.gaze(who, t)
        f["gx"], f["gy"], f["turn"] = gx, gy, clamp(f["turn"] + turn, -0.6, 0.6)
        f["blink"] = max(f["blink"], self.blink[who](t))
        sp = self.tl.mouth(who, t)
        f["tilt"] += noise1(t * 0.4, len(who)) * 2.5 + sp * noise1(t * 2.3, len(who) + 1) * 4
        if self.chaos(t):
            f["tilt"] += math.sin(t * 8 + len(who)) * 6
        b = pulse(t, self.bow, 0.5, 0.8, 0.6)
        f["blink"] = max(f["blink"], b)
        return f, sp

    # ------------------------------------------------------------ draw
    def draw(self, cv, t):
        lights = clamp((t - self.boot_on) / 0.4) * (0.6 + 0.4 * (1 if t > self.boot_on + 0.8 else (int(t * 18) % 2)))
        self.draw_room(cv, t)
        self.draw_tv(cv, t)
        for who in ("CYAN", "GOLD"):
            self.draw_angel(cv, who, t)
        self.draw_couch_back(cv)
        for who in ("CFO", "CEO", "TYLER"):
            self.draw_sitter(cv, who, t)
        self.draw_couch_front(cv)
        self.draw_pam(cv, t)
        self.draw_kid(cv, t)
        self.draw_door(cv, t)
        if t > self.door0:
            self.draw_jesus(cv, t)
        self.draw_labels(cv, t)
        if self.chaos(t):
            self.draw_chaos(cv, t)
        if self.pen_drop - 0.1 < t < self.pen_drop + 1.0:
            k = prog(t, self.pen_drop, self.pen_drop + 0.45)
            x, y = PAM_XY[0] + 20, PAM_XY[1] + 120 + 440 * k * k
            cv.save()
            cv.translate(x, min(y, FLOOR - 10))
            cv.rotate(k * 400)
            rrect(cv, -4, -30, 8, 60, 3, paint("#2b6cb0"))
            cv.restore()
        # darkness before the lights come on
        rect(cv, -1000, -1000, 4000, 4500, paint("#05060b", 0.92 * (1 - lights)))

    def draw_room(self, cv, t):
        rect(cv, -1000, -1000, 4000, 4500, paint("#000", shader=lin_grad((0, 0), (0, FLOOR), [("#2c4a52", 1), ("#3f6b70", 1)])))
        for x in range(-400, 2200, 160):
            line(cv, x, 0, x, FLOOR, paint("#29454c", 0.5, stroke=6))
        # string lights
        for k in range(26):
            x = -60 + k * 72
            y = 120 + 30 * math.sin(k * 0.5)
            col = ["#ffd86a", "#ff8a8a", "#8fe0ff", "#b6ff8a"][k % 4]
            on = 1.0 if not self.chaos(t) else (0.3 + 0.7 * ((int(t * 8) + k) % 2))
            circle(cv, x, y, 12, paint(col, on))
            glow(cv, x, y, 40, col, 0.25 * on)
        cv.drawPath(smooth_path([(-60 + k * 72, 108 + 30 * math.sin(k * 0.5)) for k in range(26)], False), paint("#1b1b1b", stroke=3))
        # posters from the earlier videos
        self.poster(cv, 270, 640, "KINGDOM OF", "HEAVEN, INC.", "#1f2b47", "#c9a227")
        self.poster(cv, 1430, 380, "THE LONG", "DREAM", "#0b1030", "#7fe8ff")
        # snack table
        rect(cv, 1330, 1560, 340, 30, paint("#8a5a3a"))
        rect(cv, 1350, 1590, 20, 290, paint("#6b4428"))
        rect(cv, 1630, 1590, 20, 290, paint("#6b4428"))
        rrect(cv, 1380, 1480, 70, 80, 10, paint("#222"))
        for k in range(3):
            circle(cv, 1500 + k * 46, 1545, 22, paint("#d79b5a"))
            circle(cv, 1500 + k * 46, 1545, 8, paint("#8a5a3a"))
        # rug + floor
        rect(cv, -1000, FLOOR, 4000, 1600, paint("#4a3a32"))
        ellipse(cv, 850, FLOOR + 120, 700, 90, paint("#7a3b4a"))
        ellipse(cv, 850, FLOOR + 120, 600, 70, paint("#a24f5f", stroke=8))
        # render queue board
        rrect(cv, 40, 900, 300, 240, 12, paint("#1a1a1a"))
        text(cv, "RENDER QUEUE", 190, 948, font("black", 26), paint("#9fffb0"), "center")
        items = [("1. Board meeting", "DONE"), ("2. The long dream", "DONE"), ("3. ???", "NOW")]
        for i, (a, b) in enumerate(items):
            text(cv, a, 60, 1000 + i * 44, font("mono", 20), paint("#d0d0d0"))
            text(cv, b, 320, 1000 + i * 44, font("mono", 20), paint("#9fffb0" if b == "DONE" else "#ff8a8a"), "right")

    def poster(self, cv, x, y, l1, l2, bg, fg):
        rect(cv, x - 130, y - 180, 260, 360, paint("#111"))
        rect(cv, x - 120, y - 170, 240, 340, paint(bg))
        text(cv, l1, x, y - 20, font("black", 30), paint(fg), "center")
        text(cv, l2, x, y + 20, font("black", 30), paint(fg), "center")
        circle(cv, x, y - 100, 30, paint(fg, 0.8))

    # ---- the Director
    def draw_tv(self, cv, t):
        x, y = TV
        line(cv, x, 0, x, y - 220, paint("#222", stroke=12))
        rrect(cv, x - 300, y - 230, 600, 460, 50, paint("#cfc4a8"))
        rrect(cv, x - 300, y - 230, 600, 460, 50, paint("#9c9070", stroke=6))
        for k in range(5):
            circle(cv, x + 250, y - 120 + k * 50, 10, paint("#6b6250"))
        sw, sh = 470, 360
        on = clamp((t - 0.5) / 0.5) * (1 - clamp((t - self.tv_off) / 0.4))
        cv.save()
        clip = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - 280, y - 200, sw, sh), 40, 40)
        cv.clipRRect(clip, True)
        rect(cv, x - 280, y - 200, sw, sh, paint("#06120c"))
        if on > 0:
            # CRT power-on: a line that opens up
            open_ = ease_out(on)
            cv.save()
            cy = y - 200 + sh / 2
            cv.clipRect(skia.Rect.MakeLTRB(x - 280, cy - sh / 2 * open_, x - 280 + sw, cy + sh / 2 * open_))
            self.tv_face(cv, x - 280 + sw / 2, cy, t)
            cv.restore()
            for k in range(0, sh, 6):
                rect(cv, x - 280, y - 200 + k, sw, 2, paint("#000", 0.18))
            glow(cv, x - 45, y - 20, 260, "#5bff9b", 0.08)
        cv.restore()
        rrect(cv, x - 280, y - 200, sw, sh, 40, paint("#000", 0.35, stroke=10))

    def tv_face(self, cv, cx, cy, t):
        tl = self.tl
        col = "#7dffad"
        lid, happy, tear = self.dir_mood(t)
        sp = tl.mouth("DIR", t)
        if self.chaos(t) or (self.T("d9") < t < self.chaos0):
            col = ["#ff6b9a", "#ffd86a", "#7dffad", "#7fd8ff", "#c38aff"][int(t * 10) % 5]
        # pigeon slides while pitching ideas
        if self.T("d3") + 2.5 < t < self.E("d5") + 0.6:
            self.pigeon_slide(cv, cx, cy, t)
            return
        # eyes look at whoever is speaking
        L = tl.current(t) or tl.last_speaker(t)
        gx, gy = 0.0, 0.5
        if L and L["who"] in LOOKS and L["who"] != "DIR":
            px, py = self.look_xy(L["who"], t)
            gx = clamp((px - TV[0]) / 700, -1, 1)
            gy = clamp((py - TV[1]) / 900, -0.3, 1)
        if self.T("think") < t < self.T("d7"):
            gx, gy = 0.0, 1.0
        if t < self.wake + 0.6:
            gx = math.sin(t * 2) * 0.8
        bl = self.blink["DIR"](t)
        closed = max(bl, lid)
        for s in (-1, 1):
            ex, ey = cx + s * 95, cy - 40
            ew, eh = 96, 120
            rrect(cv, ex - ew / 2, ey - eh / 2, ew, eh, 22, paint(col, 0.95))
            px, py = ex + gx * 22, ey + gy * 26
            rrect(cv, px - 20, py - 24, 40, 48, 10, paint("#06120c"))
            rect(cv, px + 4, py - 18, 10, 10, paint(col))
            # eyelid
            lh = eh * clamp(closed)
            rect(cv, ex - ew / 2 - 4, ey - eh / 2 - 4, ew + 8, lh + 4, paint("#06120c"))
            # happy eyes: lower lid curve
            if happy > 0.05:
                rect(cv, ex - ew / 2 - 4, ey + eh / 2 - eh * 0.35 * happy, ew + 8, eh * 0.35 * happy + 4, paint("#06120c"))
            # brows
            by = ey - eh / 2 - 26 - happy * 8
            rect(cv, ex - 40, by + (s * 6 if lid > 0.4 else 0), 80, 12, paint(col, 0.9))
        if tear > 0.05:
            ph = (t * 0.6) % 1
            rrect(cv, cx + 95 + 30, cy + 10 + ph * 110, 16, 26, 8, paint("#7fd8ff", tear * (1 - ph)))
        # equalizer mouth
        for k in range(9):
            h = 6 + 70 * sp * (0.4 + 0.6 * abs(math.sin(t * 13 + k * 1.7)))
            rect(cv, cx - 108 + k * 26, cy + 105 - h / 2, 16, h, paint(col, 0.9))

    def pigeon_slide(self, cv, cx, cy, t):
        tl = self.tl
        stage = 0 if t < tl.s("d4") else (1 if t < tl.s("d5") else (2 if t < tl.wfind("d5", "fine") else 3))
        rect(cv, cx - 240, cy - 180, 480, 360, paint("#f6f3e8"))
        cap = ["IDEA #1: PIGEON FILES TAXES", "IDEA #2: ...LATE", "IDEA #3: AUDITED", "IT KEPT ITS RECEIPTS"][stage]
        text(cv, cap, cx, cy - 140, font("black", 24), paint("#22304d"), "center")
        bob = math.sin(t * 6) * 4
        self.pigeon(cv, cx - 40, cy + 30 + bob, 1.0, t, worried=stage in (1, 2), happy=stage == 3)
        rect(cv, cx + 40, cy - 40, 120, 150, paint("#ffffff"))
        rect(cv, cx + 40, cy - 40, 120, 150, paint("#9aa3b5", stroke=3))
        text(cv, "1040", cx + 100, cy - 6, font("black", 26), paint("#22304d"), "center")
        for k in range(4):
            rect(cv, cx + 56, cy + 14 + k * 20, 88, 6, paint("#c9d0dc"))
        if stage == 1:
            text(cv, "LATE", cx + 100, cy + 140, font("black", 30), paint("#d0392b"), "center")
        if stage >= 2:
            cv.save()
            cv.translate(cx + 160, cy + 80)
            cv.rotate(-14)
            rrect(cv, -90, -26, 180, 52, 8, paint("#d0392b" if stage == 2 else "#2e9e5b", stroke=6))
            text(cv, "AUDIT" if stage == 2 else "CLEARED", 0, 12, font("black", 30), paint("#d0392b" if stage == 2 else "#2e9e5b"), "center")
            cv.restore()
        if stage == 3:
            for k in range(5):
                ph = (t * 0.5 + k / 5) % 1
                rect(cv, cx - 200 + k * 40, cy + 150 - ph * 300, 30, 40, paint("#ffffff", 1 - ph))

    def pigeon(self, cv, x, y, s, t, worried=False, happy=False):
        cv.save()
        cv.translate(x, y)
        cv.scale(s, s)
        ellipse(cv, 0, 20, 70, 52, paint("#8a8fa3"))
        ellipse(cv, 20, 30, 40, 30, paint("#b8bccb"))
        ellipse(cv, -20, -40, 34, 36, paint("#6f7a9a"))
        ellipse(cv, -20, -10, 30, 20, paint("#5aa08a", 0.8))
        cv.drawPath(poly([(-52, -42), (-74, -36), (-52, -30)]), paint("#e0a030"))
        ey = -48
        circle(cv, -30, ey, 9, paint("#ffffff"))
        circle(cv, -32, ey + (2 if worried else 0), 5, paint("#111"))
        if worried:
            line(cv, -40, ey - 16, -20, ey - 12, paint("#333", stroke=3))
            p = skia.Path()
            p.moveTo(-2, -70)
            p.quadTo(6, -58, -2, -52)
            p.quadTo(-10, -58, -2, -70)
            cv.drawPath(p, paint("#8fd0ff"))
        if happy:
            rect(cv, -40, ey + 2, 20, 8, paint("#8a8fa3"))
        line(cv, -10, 70, -14, 92, paint("#e0a030", stroke=5))
        line(cv, 14, 70, 18, 92, paint("#e0a030", stroke=5))
        cv.restore()

    # ---- furniture
    def draw_couch_back(self, cv):
        rrect(cv, 300, 1150, 1100, 420, 60, paint("#7a2f3a"))
        for k in range(3):
            rrect(cv, 340 + k * 345, 1190, 330, 330, 40, paint("#8e3a46"))

    def draw_couch_front(self, cv):
        rrect(cv, 300, 1530, 1100, 110, 30, paint("#9a4450"))
        rrect(cv, 300, 1630, 1100, 90, 20, paint("#6a2632"))
        for x in (250, 1350):
            rrect(cv, x, 1330, 100, 390, 40, paint("#6a2632"))
        for x in (330, 1360):
            rect(cv, x, 1720, 20, 60, paint("#3a1a1a"))

    def legs(self, cv, x, y_hip, stand, t, pants="#2c3e50", shoe="#1a1a1a", bounce=0.0):
        if stand < 0.5:
            for s in (-1, 1):
                rrect(cv, x + s * 50 - 34, 1600, 68, FLOOR - 1600 - 20, 20, paint(pants))
                ellipse(cv, x + s * 54, FLOOR - 12, 42, 16, paint(shoe))
        else:
            for s in (-1, 1):
                rrect(cv, x + s * 42 - 30, y_hip, 60, FLOOR - y_hip - 16, 20, paint(pants))
                ellipse(cv, x + s * 46, FLOOR - 10 - bounce, 42, 16, paint(shoe))

    def draw_sitter(self, cv, who, t):
        L = CEO_BLUE if (who == "CEO" and self.blue(t)) else LOOKS[who]
        x, y = self.pos(who, t)
        st = smooth(self.stand[who](t)) if who in self.stand else 0
        f, sp = self.face_for(who, t)
        bounce = abs(math.sin(t * 8 + x)) * 22 if self.chaos(t) else 0
        y -= bounce
        if st > 0.5:
            self.legs(cv, x, y + 300, st, t, bounce=0)
        hands = ((-62, 250), (62, 250))
        kinds = ("fist", "fist")
        if self.chaos(t):
            hands = ((-120, -60 + math.sin(t * 8) * 30), (120, -60 + math.cos(t * 8) * 30))
            kinds = ("open", "open")
        elif self.tl.speaking(who, t):
            k = 0.5 + 0.5 * noise1(t * 0.9, len(who))
            hands = (hands[0], lerp2(hands[1], (90, 120), k))
            kinds = ("fist", "open")
        if who == "TYLER" and self.T("t6") < t < self.E("t6") + 0.3:
            hands, kinds = ((-62, 250), (30, -60)), ("fist", "point")
        if who == "TYLER" and self.T("t7") < t < self.E("t7"):
            hands, kinds = ((-40, -40), (40, -40)), ("fist", "fist")
        if who == "CEO" and self.T("c2") < t < self.E("c3"):
            hands, kinds = ((-90, 120), (90, 120)), ("fist", "fist")
        cv.save()
        cv.translate(x, y)
        draw_torso(cv, L, t, math.sin(t * 1.3 + x))
        draw_neck(cv, L)
        cv.save()
        cv.translate(f["turn"] * 6, -112 + pulse(t, self.bow, 0.5, 0.8, 0.6) * 30)
        draw_head(cv, L, f, t, sp * 0.9)
        cv.restore()
        draw_arm(cv, L, -1, hands[0], kinds[0], 0, arm_color(L))
        draw_arm(cv, L, 1, hands[1], kinds[1], 0, arm_color(L))
        cv.restore()
        if st <= 0.5:
            self.legs(cv, x, y + 300, st, t)

    def blue(self, t):
        if self.T("c5") + 1.5 < t < self.E("c5") + 0.4:
            return True
        if self.T("c7") - 0.3 < t < self.chaos1:
            return True
        return False

    def draw_pam(self, cv, t):
        x, y = PAM_XY
        f, sp = self.face_for("PAM", t)
        bounce = abs(math.sin(t * 8 + 3)) * 22 if self.chaos(t) else 0
        # stool
        rrect(cv, x - 90, y + 300, 180, 30, 10, paint("#c99a5a"))
        for s in (-1, 1):
            line(cv, x + s * 70, y + 330, x + s * 90, FLOOR, paint("#a07a45", stroke=14))
        self.legs(cv, x, y + 300, 0.0, t, pants="#4a5a7a", shoe="#7a3b4a")
        hands = ((-50, 240), (50, 240))
        kinds = ("fist", "fist")
        if self.T("p3") - 0.2 < t < self.T("p3") + 1.5:
            hands, kinds = ((-50, 240), (120, -160)), ("fist", "open")
        if self.T("p2") < t < self.E("p2") + 0.2:
            hands, kinds = ((-90, 90), (90, 90)), ("open", "open")
        if self.chaos(t):
            hands, kinds = ((-120, -60), (120, -60)), ("open", "open")
        cv.save()
        cv.translate(x, y - bounce)
        draw_torso(cv, PAM, t, math.sin(t * 1.4))
        draw_neck(cv, PAM)
        cv.save()
        cv.translate(f["turn"] * 6, -112 + pulse(t, self.bow, 0.5, 0.8, 0.6) * 30)
        draw_head(cv, PAM, f, t, sp * 0.9)
        cv.restore()
        draw_arm(cv, PAM, -1, hands[0], kinds[0], 0, arm_color(PAM))
        draw_arm(cv, PAM, 1, hands[1], kinds[1], 0, arm_color(PAM))
        if self.T("p2") < t < self.E("p2") + 0.2:
            rrect(cv, -110, 20, 220, 120, 10, paint("#1a1a1a"))
            text(cv, "freckles:", -96, 60, font("mono", 20), paint("#9fffb0"))
            text(cv, "Random(4)", -96, 96, font("mono", 22), paint("#ffd86a"))
        cv.restore()

    def draw_kid(self, cv, t):
        x, y = KID_XY
        f, sp = self.face_for("KID", t)
        bounce = abs(math.sin(t * 8 + 5)) * 18 if self.chaos(t) else 0
        # cross-legged on the floor
        ellipse(cv, x, FLOOR - 40, 170, 60, paint("#2c3e50"))
        for s in (-1, 1):
            ellipse(cv, x + s * 120, FLOOR - 30, 40, 18, paint("#f4f4f4"))
        cv.save()
        cv.translate(x, y - bounce)
        cv.scale(1.0, 0.95)
        draw_torso(cv, KID, t, math.sin(t * 1.3))
        draw_neck(cv, KID)
        cv.save()
        cv.translate(f["turn"] * 6, -112 + pulse(t, self.bow, 0.5, 0.8, 0.6) * 30)
        draw_head(cv, KID, f, t, sp * 0.9)
        cv.restore()
        phone_up = self.T("k3") - 0.2 < t < self.chaos1
        hands = ((-50, 170), (50, 170)) if not phone_up else ((-60, 170), (90, -40))
        draw_arm(cv, KID, -1, hands[0], "fist", 0, KID.c1)
        draw_arm(cv, KID, 1, hands[1], "fist", 0, KID.c1)
        hx, hy = hands[1]
        rrect(cv, hx - 40, hy - 150, 90, 150, 12, paint("#1c1c22"))
        rrect(cv, hx - 34, hy - 144, 78, 138, 8, paint("#fafafa"))
        views = "13" if phone_up else "12"
        text(cv, views, hx + 5, hy - 70, font("black", 40), paint("#e74c3c" if phone_up else "#111"), "center")
        text(cv, "views", hx + 5, hy - 40, font("semi", 16), paint("#555"), "center")
        if self.T("k1") < t < self.E("k1") + 0.3:
            draw_hand(cv, KID, 40, -230, "point", 1, -150)
        cv.restore()

    def draw_angel(self, cv, who, t):
        L = LOOKS[who]
        x, y = self.pos(who, t)
        f, sp = self.face_for(who, t)
        col = "#7fe8ff" if who == "CYAN" else "#ffd86a"
        glow(cv, x, y - 40, 240, col, 0.28)
        cv.save()
        cv.translate(x, y)
        if self.chaos(t):
            cv.rotate(math.sin(t * 5 + x) * 14)
        cv.scale(0.8, 0.8)
        draw_torso(cv, L, t, math.sin(t * 1.2 + x))
        # no legs: the body dissolves into sparkles
        rect(cv, -140, 180, 280, 200, paint("#000", shader=lin_grad((0, 180), (0, 340), [("#2c4a52", 0), ("#2c4a52", 1)])))
        r = random.Random(len(who))
        for i in range(24):
            ph = (t * 0.4 + r.random()) % 1
            circle(cv, r.uniform(-90, 90), 230 + ph * 160, r.uniform(3, 7), paint(col, 1 - ph))
        draw_neck(cv, L)
        cv.save()
        cv.translate(f["turn"] * 6, -112)
        draw_head(cv, L, f, t, sp * 0.9)
        cv.restore()
        draw_arm(cv, L, -1, (-60, 150), "fist", 0, arm_color(L))
        draw_arm(cv, L, 1, (60, 150) if not sp else (90, 60), "fist" if not sp else "open", 0, arm_color(L))
        cv.restore()

    def draw_door(self, cv, t):
        x0, x1, y0 = 20, 240, 1180
        rect(cv, x0 - 16, y0 - 16, x1 - x0 + 32, FLOOR - y0 + 16, paint("#1f3338"))
        rect(cv, x0, y0, x1 - x0, FLOOR - y0, paint("#ffe9b0"))
        open_ = pulse(t, self.door0, 0.35, 1.4, 0.5)
        dw = (x1 - x0) * (1 - 0.85 * open_)
        rect(cv, x0, y0, dw, FLOOR - y0, paint("#a07a55"))
        rect(cv, x0 + 16, y0 + 24, max(0, dw - 32), 260, paint("#8e6a47"))
        circle(cv, x0 + dw - 26, y0 + 380, 10, paint("#d9c27a"))
        rrect(cv, x0 + 20, y0 - 90, 180, 56, 8, paint("#1a1a1a"))
        text(cv, "TALENT", x0 + 110, y0 - 52, font("black", 30), paint("#ffd86a"), "center")

    def draw_jesus(self, cv, t):
        L = JESUS
        x, y = self.pos("JESUS", t)
        f, sp = self.face_for("JESUS", t)
        walking = t < self.door0 + 1.6
        bob = abs(math.sin(t * 7)) * 8 if walking else 0
        glow(cv, x, y, 320, "#ffd98a", 0.25)
        cv.save()
        cv.translate(x, y - bob)
        cv.drawPath(poly([(-100, 230), (100, 230), (118, FLOOR - y - 40), (-118, FLOOR - y - 40)]), paint(shade(L.c1, -0.06)))
        for s in (-1, 1):
            ellipse(cv, s * 44, FLOOR - y - 14, 34, 13, paint("#6b4423"))
        draw_torso(cv, L, t, math.sin(t * 1.4))
        draw_neck(cv, L)
        cv.save()
        cv.translate(f["turn"] * 6, -112)
        draw_head(cv, L, f, t, sp * 0.9)
        cv.restore()
        draw_arm(cv, L, -1, (-70, 250), "open", 0, L.c1, width=46)
        draw_arm(cv, L, 1, (60, 120), "fist", 0, L.c1, width=46)
        rrect(cv, 40, 70, 48, 58, 8, paint("#fafafa"))
        text(cv, "#1 BOSS", 64, 104, font("black", 10), paint("#c0392b"), "center")
        draw_hand(cv, L, 58, 104, "fist", 1)
        cv.restore()

    def draw_labels(self, cv, t):
        """Floating source-code labels when the cast finds their code."""
        def label(txt, x, y, t0, t1):
            k = pulse(t, t0, 0.3, t1 - t0 - 0.6, 0.3)
            if k <= 0:
                return
            w = text_w(txt, font("mono", 34)) + 40
            cv.save()
            cv.translate(x, y - 20 * k)
            cv.scale(k, k)
            rrect(cv, -w / 2, -40, w, 64, 12, paint("#111", 0.92))
            text(cv, txt, 0, 4, font("mono", 34), paint("#9fffb0"), "center")
            cv.restore()
        T, E = self.T, self.E
        label("draw_head()", SEAT["TYLER"], 1020, self.Wd("t6", "Draw") - 0.2, E("t6") + 0.6)
        label("hair_style = 'messy'", KID_XY[0] + 140, 1330, self.Wd("k1", "messy") - 0.2, E("k1") + 0.6)
        label("skin = '#8fb4ff'", SEAT["CEO"], 1030, T("c5") + 1.5, E("c6") + 0.3)
        label("legs = None", 1445, 520, T("g2"), E("y2") + 0.4)

    def draw_chaos(self, cv, t):
        k = t - self.chaos0
        # disco wash
        for i in range(6):
            a = t * 1.5 + i
            cv.drawPath(poly([(850, 100), (850 + 1600 * math.cos(a), 100 + 1600 * math.sin(a) + 1200),
                              (850 + 1600 * math.cos(a + 0.2), 100 + 1600 * math.sin(a + 0.2) + 1200)]),
                        paint(["#ff6b9a", "#ffd86a", "#7dffad", "#7fd8ff", "#c38aff", "#ff9a5a"][i], 0.14))
        circle(cv, 850, 120, 50, paint("#d9d9e8"))
        for i in range(10):
            circle(cv, 850 + 30 * math.cos(t * 3 + i), 120 + 30 * math.sin(t * 3 + i), 8, paint("#ffffff", 0.8))
        # the pigeon flies through with its return
        px = lerp(-200, 1900, (k / 3.0) % 1.0)
        self.pigeon(cv, px, 820 + math.sin(t * 6) * 40, 1.3, t, happy=True)
        # a tiny mustard tree bursts through the floor
        g = ease_out(clamp(k / 2.0))
        tx, ty = 170, FLOOR
        line(cv, tx, ty, tx, ty - 520 * g, paint("#4e342e", stroke=40 * g + 1))
        for (dx, dy, r) in ((-140, -520, 120), (120, -560, 130), (0, -650, 140), (-60, -420, 90), (90, -440, 90)):
            circle(cv, tx + dx * g, ty + dy * g, r * g, paint("#4caf50", 0.95))
            circle(cv, tx + dx * g + 20, ty + dy * g - 20, r * g * 0.5, paint("#fff3a0", 0.9))
        # SUPPRESSED stamp slams onto the Director, money bag bounces
        sk = prog(t, self.chaos0 + 0.6, self.chaos0 + 0.8)
        if sk > 0:
            cv.save()
            cv.translate(TV[0] - 40, TV[1] + 30)
            cv.rotate(-12)
            s = lerp(2.2, 1.0, ease_in(sk))
            cv.scale(s, s)
            rrect(cv, -220, -50, 440, 100, 14, paint("#e74c3c", 0.9, stroke=10))
            text(cv, "SUPPRESSED", 0, 26, font("black", 60), paint("#e74c3c", 0.9), "center")
            cv.restore()
        bx = 1520
        by = 1700 - abs(math.sin(t * 5)) * 160
        ellipse(cv, bx, by, 90, 100, paint("#c8a165"))
        text(cv, "$", bx, by + 34, font("black", 100), paint("#2e7d32"), "center")
        # floating redaction bar
        rx = 300 + math.sin(t * 2) * 120
        rrect(cv, rx - 120, 260, 240, 60, 8, paint("#000"))
        text(cv, "LEGAL NAME", rx, 298, font("bold", 22), paint("#777"), "center")
