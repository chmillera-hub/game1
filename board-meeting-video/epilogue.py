"""Act 3: the seed grows, two thousand years pass, and the creator plants seeds."""
import math, random
import skia
from common import *
from characters import *
from cast import CREATOR
from boardroom import SEED_POS, SHOTS

BIRD_COLS = ["#3f7fd6", "#e0533d", "#f2c230", "#4fb37a", "#9b6ad6", "#f08a3c", "#5cc3e8"]


class Tree:
    def __init__(self, base, seed=12):
        self.base = base
        self.segs = []
        self.tips = []
        self.D = 8
        r = random.Random(seed)
        self._grow(r, base[0], base[1], -math.pi / 2, 470, 84, 0)
        self.leaves = []
        for (x, y, d) in self.tips:
            for k in range(3):
                self.leaves.append((x + r.uniform(-60, 60), y + r.uniform(-60, 40), r.uniform(48, 86),
                                    r.choice(["#3f8f46", "#4caf50", "#66bb6a", "#2e7d32", "#7cc576"]), d,
                                    r.random()))
        self.flowers = [(x + r.uniform(-50, 50), y + r.uniform(-50, 30), r.random()) for (x, y, d) in self.tips
                        for _ in range(2)]

    def _grow(self, r, x, y, a, ln, w, d):
        x2, y2 = x + ln * math.cos(a), y + ln * math.sin(a)
        self.segs.append((x, y, x2, y2, w, d))
        if d >= self.D - 1:
            self.tips.append((x2, y2, d))
            return
        n = 2 if d < 2 else r.choice([2, 2, 3])
        spread = 0.95 if d < 3 else 0.75
        for i in range(n):
            da = (i - (n - 1) / 2) * spread / max(1, n - 1) * 2 * 0.62 + r.uniform(-0.18, 0.18)
            na = a + da
            # keep the canopy rounded rather than drooping
            na = lerp(na, -math.pi / 2, 0.12 if d < 4 else 0.0)
            self._grow(r, x2, y2, na, ln * r.uniform(0.66, 0.8), w * 0.66, d + 1)

    def draw(self, cv, g, t):
        D = self.D
        for (x, y, x2, y2, w, d) in self.segs:
            u = clamp(g * D * 0.95 - d * 0.82)
            if u <= 0:
                continue
            ex, ey = lerp(x, x2, u), lerp(y, y2, u)
            line(cv, x, y, ex, ey, paint("#4e342e", stroke=w * (0.12 + 0.88 * clamp(g * 1.5))))
            if w > 12:
                line(cv, x - w * 0.15, y, ex - w * 0.15, ey, paint("#6d4c41", 0.7, stroke=w * 0.3 * clamp(g * 1.5)))
        lk = clamp((g - 0.55) / 0.4)
        if lk > 0:
            for (x, y, rr, col, d, ph) in self.leaves:
                s = ease_back(clamp(lk * 1.4 - ph * 0.4))
                if s <= 0:
                    continue
                sway = math.sin(t * 1.3 + x * 0.01) * 6
                circle(cv, x + sway, y, rr * s, paint(col, 0.96))
            fk = clamp((g - 0.85) / 0.15)
            for (x, y, ph) in self.flowers:
                s = clamp(fk * 1.5 - ph * 0.5)
                if s > 0:
                    sway = math.sin(t * 1.3 + x * 0.01) * 6
                    for k in range(5):
                        a = k * 2 * math.pi / 5 + ph * 6
                        circle(cv, x + sway + 9 * s * math.cos(a), y + 9 * s * math.sin(a), 7 * s, paint("#fff3a0"))
                    circle(cv, x + sway, y, 5 * s, paint("#f2b630"))


def draw_bird(cv, x, y, s, col, flap, t, face=1, blink=0.0):
    cv.save()
    cv.translate(x, y)
    cv.scale(s * face, s)
    ellipse(cv, 0, 0, 30, 24, paint(col))
    ellipse(cv, 6, 8, 18, 13, paint("#fff6e6"))
    cv.drawPath(poly([(-26, -4), (-52, -14), (-48, 6)]), paint(shade(col, -0.2)))
    circle(cv, 22, -14, 16, paint(col))
    cv.drawPath(poly([(34, -16), (48, -11), (34, -7)]), paint("#f2a530"))
    if blink < 0.5:
        circle(cv, 26, -17, 4, paint("#111"))
        circle(cv, 27, -18, 1.4, paint("#fff"))
    else:
        line(cv, 22, -17, 30, -17, paint("#111", stroke=2))
    wa = math.sin(flap) * 55
    cv.save()
    cv.translate(-4, -6)
    cv.rotate(-wa)
    ellipse(cv, -14, -4, 22, 11, paint(shade(col, -0.15)))
    cv.restore()
    cv.restore()


class Epilogue:
    def __init__(self, tl, board, opening):
        self.tl, self.board, self.op = tl, board, opening
        T, E, Wd = tl.s, tl.e, tl.wfind
        self.T, self.E, self.Wd = T, E, Wd
        self.tree = Tree(SEED_POS)
        self.sprout0 = T("grow") + 0.2
        self.doomed0 = T("e1") - 0.1
        self.doomed1 = E("e1") + 0.7
        self.tl0 = self.doomed1
        self.tl1 = self.tl0 + 6.8
        self.wheel0 = T("e3") - 0.9
        self.dawn0 = Wd("e3", "And") - 0.25
        self.end0 = E("e4") + 1.4
        self.end_fade = tl.total - 1.4
        r = random.Random(21)
        cands = [p for p in self.tree.tips if p[1] < 900]
        r.shuffle(cands)
        self.birds = []
        for i in range(7):
            x, y, _ = cands[i % len(cands)]
            side = r.choice([-1, 1])
            arrive = self.tl0 + 3.6 + i * 0.45
            start = (x + side * r.uniform(1300, 1800), y - r.uniform(500, 1100))
            self.birds.append(dict(land=(x, y - 30), start=start, arrive=arrive, col=BIRD_COLS[i],
                                   face=-side, blink=Blinker(300 + i, mean=2.5)))

    def growth(self, t):
        return ease_io(prog(t, self.tl0, self.tl1)) ** 1.1

    def camera(self, t):
        a = SHOTS["SEED"]
        b = (1580, 980, 2080)
        u = ease_io(prog(t, self.tl0 + 0.3, self.tl0 + 6.5))
        cx, cy, w = (lerp(p, q, u) for p, q in zip(a, b))
        cx += noise1(t * 0.2, 61) * 5
        return cx, cy, w

    def draw_world(self, cv, t):
        """Seed sprout and time-lapse tree over the darkened boardroom."""
        g = self.growth(t)
        room = 1 - smooth(prog(t, self.tl0 + 1.6, self.tl0 + 4.6))
        if room > 0:
            self.board.draw(cv, t)
        if room < 1:
            a = 1 - room
            sky = lin_grad((0, -1500), (0, 1950), [("#2c3e7a", a), ("#f6b26b", a)])
            rect(cv, -3000, -4000, 9000, 6000, paint("#000", shader=sky))
            sx, sy = 1560, 1720
            circle(cv, sx, sy, 520, paint("#fff1c1", 0.55 * a, blur=120))
            circle(cv, sx, sy, 200, paint("#fff8e0", a))
            cv.save()
            cv.translate(sx, sy)
            cv.rotate(t * 3)
            for k in range(16):
                cv.rotate(360 / 16)
                cv.drawPath(poly([(0, 0), (-90, -2600), (90, -2600)]), paint("#fff3c4", 0.06 * a))
            cv.restore()
            # hills
            cv.drawPath(smooth_path([(-3000, 2000), (-600, 1880), (900, 1930), (1566, 1890), (2400, 1930),
                                     (4200, 1880), (6000, 2100), (6000, 4000), (-3000, 4000)], True, 0.4),
                        paint("#5f9e4f", a))
            cv.drawPath(smooth_path([(-3000, 2150), (0, 2060), (2000, 2120), (6000, 2050), (6000, 4000),
                                     (-3000, 4000)], True, 0.4), paint("#4a8a3e", a))
        # sprout (before the time-lapse) then the tree
        sp = ease_out(prog(t, self.sprout0, self.sprout0 + 2.6))
        x, y = SEED_POS
        if sp > 0 and g < 0.08:
            k = 1 - clamp(g / 0.08)
            hgt = 70 * sp
            cv.drawPath(quad_path((x, y - 4), (x + 8, y - hgt * 0.5), (x - 2, y - hgt)), paint("#7cc576", k, stroke=7))
            for s in (-1, 1):
                cv.save()
                cv.translate(x - 2, y - hgt)
                cv.rotate(s * 30 - 8 + math.sin(t * 2) * 4)
                cv.scale(sp, sp)
                ellipse(cv, s * 22, 0, 24, 11, paint("#8bd17c", k))
                cv.restore()
            circle(cv, x, y - 40, 90, paint("#fff0a0", 0.25 * sp * k, blur=30))
        if g > 0:
            self.tree.draw(cv, g, t)
        # birds
        for b in self.birds:
            u = prog(t, b["arrive"] - 2.0, b["arrive"])
            if u <= 0:
                continue
            lx, ly = b["land"]
            sx, sy = b["start"]
            e = ease_out(u)
            bx = lerp(sx, lx, e)
            by = lerp(sy, ly, e) - math.sin(u * math.pi) * 200
            if u < 1:
                flap = t * 22
            else:
                flap = 0.4 if (t * 1.5 + lx) % 4 > 0.3 else t * 20
                by += -abs(math.sin((t - b["arrive"]) * 3)) * 6 * ((t * 0.7 + lx) % 3 < 0.5)
            draw_bird(cv, bx, by, 3.0, b["col"], flap, t, b["face"], b["blink"](t))

    def draw_overlay(self, cv, t):
        a = 0.0
        if a > 0:
            text_outlined(cv, "2,000 years later...", W / 2, 300, font("serif_bi", 70), "#fff4d6", "#2a1a10", 8, a)

    # ------------------------------------------------ wheel insert: stepping off
    def draw_wheel_stop(self, cv, t, world):
        def scene(c):
            rect(c, -2000, -2000, 5000, 6000, paint("#000", shader=rad_grad((540, 1000), 1500, [("#3a3550", 1), ("#141320", 1)])))
            wx, wy, R = 420, 860, 360
            k = prog(t, self.wheel0, self.wheel0 + 2.5)
            ang = 6.0 * (k - k * k / 2) * 2.5
            c.drawPath(poly([(wx - 270, wy + 500), (wx, wy), (wx + 270, wy + 500)], False), paint("#5a6070", stroke=24))
            circle(c, wx, wy, R, paint("#9aa3b5", stroke=24))
            for j in range(16):
                a = ang + j * math.pi / 8
                line(c, wx, wy, wx + R * math.cos(a), wy + R * math.sin(a), paint("#7d869a", stroke=7))
            rect(c, -500, wy + 500, 2200, 1200, paint("#22202e"))
            # discarded sign on the floor
            c.save()
            c.translate(300, wy + 560)
            c.rotate(-8)
            rrect(c, -150, -40, 300, 80, 16, paint("#f39c12"))
            text(c, "ACCOUNT #47", 0, 14, font("black", 34), paint("#fff"), "center")
            c.restore()
            # creator standing beside the wheel, turning to us
            L = CREATOR
            f = FaceTrack([(0, "tired"), (self.wheel0 + 0.8, "kind")])(t)
            f["blink"] = self.op.blink(t)
            f["gx"] = lerp(-0.6, 0.0, smooth(prog(t, self.wheel0 + 0.4, self.wheel0 + 1.2)))
            f["turn"] = f["gx"] * 0.5
            c.save()
            c.translate(820, wy + 20)
            for s in (-1, 1):
                rect(c, s * 40 - 24, 300, 48, 220, paint("#2c3e50"))
                ellipse(c, s * 44, 525, 40, 18, paint("#f4f4f4"))
            draw_torso(c, L, t, math.sin(t * 1.4))
            draw_neck(c, L)
            draw_arm(c, L, -1, (-90, 230), "fist", 0, L.c1)
            draw_arm(c, L, 1, (90, 230), "fist", 0, L.c1)
            c.translate(0, -112)
            draw_head(c, L, f, t)
            c.restore()
        world(cv, 560, 1080, 1180, scene)

    # ------------------------------------------------ dawn bedroom
    def draw_dawn(self, cv, t, world):
        p_notif = prog(t, self.dawn0 + 0.35, self.dawn0 + 1.0)
        look_plant = smooth(prog(t, self.T("e4") - 0.3, self.T("e4") + 0.4))
        notif_out = smooth(prog(t, self.T("e4") - 0.4, self.T("e4") + 0.1))
        plant = prog(t, self.T("e4") + 0.1, self.T("e4") + 1.8)
        face = FaceTrack([(0, expr("hopeful", glisten=0.9)), (self.T("e4"), expr("kind", glisten=0.7))])
        gx = lerp(0.0, -0.9, look_plant)
        gy = lerp(0.6, -0.5, look_plant)
        look = (gx, gy, lerp(0.0, -0.35, look_plant))
        cam = (lerp(590, 470, look_plant), lerp(1020, 930, look_plant), lerp(820, 1000, look_plant))
        world(cv, *cam, lambda c: self.op.draw_bedroom(c, t, night=0.0, phone=True, plant=plant,
                                                         notif=p_notif * (1 - notif_out), face=face, look=look))

    # ------------------------------------------------ end card
    def draw_end(self, cv, t):
        rect(cv, 0, 0, W, H, paint("#000", shader=lin_grad((0, 0), (0, H), [("#1d1426", 1), ("#3a2418", 1)])))
        circle(cv, W / 2, 700, 380, paint("#ffcf7a", 0.18, blur=90))
        a0 = prog(t, self.end0 + 0.2, self.end0 + 1.2)
        cv.save()
        cv.translate(W / 2, 860)
        cv.scale(0.24, 0.24)
        cv.translate(-SEED_POS[0], -SEED_POS[1])
        self.tree.draw(cv, clamp(0.5 + 0.5 * a0), t)
        cv.restore()
        a1 = smooth(prog(t, self.end0 + 0.6, self.end0 + 1.6))
        a2 = smooth(prog(t, self.end0 + 1.6, self.end0 + 2.6))
        f = font("serif_i", 70)
        text(cv, "“The kingdom of heaven", W / 2, 1050, f, paint("#fff4d6", a1), "center")
        text(cv, "is like a mustard seed.”", W / 2, 1140, f, paint("#fff4d6", a1), "center")
        text(cv, "— Matthew 13:31", W / 2, 1250, font("serif", 46), paint("#e8c48a", a2), "center")
        fo = prog(t, self.end_fade, self.tl.total)
        if fo > 0:
            rect(cv, 0, 0, W, H, paint("#000", fo))
