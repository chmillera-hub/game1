"""Shot-by-shot direction. Every cut and gesture is keyed to the voice timeline."""
import bisect
import json
import math
import os
import random

import skia

import sets as S
from anim import (FPS, H, HERE, W, C, Track, clamp, ease_in, ease_out, font, glow, hashf, lerp, lin, mixc, noise,
                  oval, paint, path, rad, ramp, shade, smooth, spline, text_w, window)
from cast import ELDER, GUARD, GUARD2, MOSES, POTTER, WEAVER, villager
from rig import draw_person, mk


# ------------------------------------------------------------------ timeline access
class Timeline:
    def __init__(self, p):
        d = json.load(open(p))
        self.marks = d["marks"]
        self.items = d["items"]
        self.by_id = {it["id"]: it for it in self.items}
        self.lines = [it for it in self.items if it["kind"] == "line"]

    def s(self, i):
        return self.by_id[i]["start"] if i in self.by_id else self.marks[i]

    def e(self, i):
        return self.by_id[i]["end"]

    def m(self, i):
        return self.marks[i]

    def cap(self, i, k):
        caps = self.by_id[i]["caps"]
        return caps[max(-len(caps), min(k, len(caps) - 1))][0]

    def lip(self, speakers, t):
        for it in self.lines:
            if it["speaker"] in speakers and it["start"] - 0.03 <= t < it["end"] + 0.06:
                k = int((t - it["start"]) * FPS)
                op = it["open"]
                if 0 <= k < len(op):
                    return op[k], it["bright"][k], True
                return 0.0, 0.5, True
        return 0.0, 0.5, False

    def lip_slow(self, speakers, t):
        return sum(self.lip(speakers, t + d)[0] for d in (-0.12, -0.06, 0, 0.06, 0.12)) / 5


TL = Timeline(os.path.join(HERE, "build", "timeline.json"))


# ------------------------------------------------------------------ life: blinks, saccades, idle motion
class Life:
    def __init__(self, seed, rate=1.0):
        rng = random.Random(seed)
        self.seed = seed
        self.blinks = []
        t = rng.uniform(0.3, 2.5)
        while t < 400:
            self.blinks.append(t)
            if rng.random() < 0.12:
                self.blinks.append(t + 0.28)  # double blink
            t += rng.uniform(2.2, 5.2) / rate
        self.sacc_t, self.sacc_v = [], []
        t = 0
        while t < 400:
            self.sacc_t.append(t)
            self.sacc_v.append((rng.uniform(-0.28, 0.28), rng.uniform(-0.15, 0.15)))
            t += rng.uniform(0.5, 2.3)

    def blink(self, t):
        i = bisect.bisect_right(self.blinks, t) - 1
        if i < 0:
            return 0.0
        dt = t - self.blinks[i]
        if dt < 0.06:
            return dt / 0.06
        if dt < 0.19:
            return 1 - (dt - 0.06) / 0.13
        return 0.0

    def gaze(self, t):
        i = max(0, bisect.bisect_right(self.sacc_t, t) - 1)
        g1 = self.sacc_v[i]
        g0 = self.sacc_v[i - 1] if i > 0 else g1
        u = clamp((t - self.sacc_t[i]) / 0.06)
        return lerp(g0[0], g1[0], u), lerp(g0[1], g1[1], u)

    def apply(self, p, t, amt=1.0, blinks=True):
        if blinks:
            p["blink"] = max(p["blink"], self.blink(t))
        gx, gy = self.gaze(t)
        p["gx"] += gx * amt
        p["gy"] += gy * amt
        p["turn"] += 0.035 * noise(t, self.seed, 0.7) * amt
        p["tilt"] += 1.3 * noise(t, self.seed + 5, 0.55) * amt
        return p


LIVES = {k: Life(i * 17 + 3) for i, k in enumerate(["moses", "elder", "weaver", "potter", "g1", "g2"])}
for i in range(40):
    LIVES[f"v{i}"] = Life(100 + i * 7)


def speak(p, speakers, t, gain=1.0, emph=1.0):
    o, b, active = TL.lip(speakers, t)
    p["open"] = max(p["open"], clamp(o * gain))
    p["bright"] = b
    if active:
        slow = TL.lip_slow(speakers, t)
        p["brow"] += 0.22 * slow * emph
        p["pitch"] += (-0.05 * slow + 0.03 * math.sin(t * 5.1)) * emph
        p["tilt"] += 1.6 * noise(t, 9, 1.4) * slow * emph
    return active


def fake_talk(t, seed=1, amt=0.6):
    phrase = clamp(noise(t, seed, 0.9) * 1.6 + 0.4)
    syl = 0.5 + 0.5 * math.sin(t * 2 * math.pi * 4.2 + 2 * noise(t, seed + 1, 3))
    return amt * phrase * syl


# ------------------------------------------------------------------ drawing helpers
REST = (8, -8, 1.0, 1.0)
MOUTH = (20, -169, 0.45, 1.0)      # fingertips to the lips
THROAT = (18, -160, 0.5, 0.92)
CHEST = (16, -128, 0.8, 0.95)
OPEN = (30, 25, 0.85, 0.65)        # palms opened outward


def arm_mix(a, b, u):
    return tuple(lerp(x, y, u) for x, y in zip(a, b))


def fig(cv, st, p, x, y, s, t):
    cv.save()
    cv.translate(x, y)
    cv.scale(s, s)
    r = draw_person(cv, st, p, t)
    cv.restore()
    return r


def head_off(p):
    return -450 + 172 * p["kneel"] + 46 * p["bow"]


def at_head(cv, st, p, hx, hy, s, t):
    """Place a figure so that its head centre lands on (hx, hy)."""
    return fig(cv, st, p, hx, hy - head_off(p) * s, s, t)


class Cam:
    def __init__(self, cv, cx=W / 2, cy=H / 2, z=1.0, rot=0.0, shake=0.0, t=0.0):
        self.cv, self.a = cv, (cx, cy, z, rot, shake, t)

    def __enter__(self):
        cx, cy, z, rot, shake, t = self.a
        cv = self.cv
        cv.save()
        sx = shake * (noise(t, 3, 31) * 9)
        sy = shake * (noise(t, 7, 29) * 9)
        cv.translate(W / 2 + sx, H / 2 + sy)
        cv.scale(z, z)
        cv.rotate(rot)
        cv.translate(-cx, -cy)
        return cv

    def __exit__(self, *a):
        self.cv.restore()


class Blur:
    def __init__(self, cv, sigma):
        self.cv, self.sigma = cv, sigma

    def __enter__(self):
        p = skia.Paint()
        if self.sigma > 0:
            p.setImageFilter(skia.ImageFilters.Blur(self.sigma, self.sigma))
        self.cv.saveLayer(None, p)
        return self.cv

    def __exit__(self, *a):
        self.cv.restore()


def run(cv, t, shots):
    cur = shots[0]
    for sh in shots:
        if t >= sh[0]:
            cur = sh
    cur[1](cv, t, t - cur[0])


def fill(cv, c, a=1.0):
    cv.drawRect(skia.Rect.MakeLTRB(-2000, -2000, 4000, 4000), paint(c, a))


def title_text(cv, txt, y, a, size=58, col=(255, 236, 200), spacing=1.0):
    if a <= 0:
        return
    f = font("title", size)
    w = text_w(txt, f)
    x = (W - w) / 2
    cv.drawString(txt, x, y + 3, f, paint((0, 0, 0), 0.45 * a, blur=6))
    cv.drawString(txt, x, y, f, paint(col, a))


# ------------------------------------------------------------------ scene: OPENING (desert dawn)
def walk_feet(cv, t, t0):
    """Close on his sandals striding over hard-cracked earth (profile)."""
    ground = 960
    S.sky(cv, [(120, 84, 120), (236, 150, 110), (252, 190, 130)], [0, 0.6, 1], 0, ground - 120)
    with Blur(cv, 6):
        S.dune_layer(cv, ground - 130, 40, (214, 150, 104), 3, bottom=ground + 40)
        S.dune_layer(cv, ground - 40, 50, (200, 136, 92), 8, bottom=ground + 40)
    v = 180
    scroll = (t * v) % 2000
    cv.save()
    cv.translate(-scroll % 140, 0)
    S.cracked_ground(cv, (-300, ground - 10, W + 300, H + 50), (182, 128, 84), seed=12, cell=140, line_a=0.6)
    cv.restore()
    cv.drawRect(skia.Rect.MakeLTRB(0, ground - 30, W, ground + 60), paint(
        shader=lin((0, ground - 30), (0, ground + 60), [((255, 210, 150), 0.0), ((255, 210, 150), 0.25)])))
    T = 1.15
    stride = 240
    skin, sole, strap = MOSES.skin, (96, 62, 38), (70, 44, 28)
    hem_y = 420 + 6 * math.sin(t / T * 2 * math.pi * 2)
    feet = []
    for i in range(2):
        ph = (t / T + i * 0.5) % 1.0
        if ph < 0.6:
            u = ph / 0.6
            x = 360 + stride / 2 - u * stride
            lift, rot = 0.0, 0.0
        else:
            u = (ph - 0.6) / 0.4
            x = 360 - stride / 2 + smooth(u) * stride
            lift = math.sin(math.pi * u) * 46
            rot = -10 * math.sin(math.pi * u)
        feet.append((x, ground - lift, rot, i))
    for x, y, rot, i in sorted(feet, key=lambda f: f[3]):
        dk = 0.82 if i == 0 else 1.0
        kx, ky = 360 + (x - 360) * 0.25, hem_y + 30
        shin = skia.Path()
        shin.moveTo(x - 46, y - 64)
        shin.lineTo(kx - 34, ky)
        shin.lineTo(kx + 30, ky)
        shin.lineTo(x - 8, y - 64)
        shin.close()
        cv.drawPath(shin, paint(shader=lin((kx - 40, 0), (kx + 40, 0), [shade(skin, 0.7 * dk), shade(skin, 0.95 * dk),
                                                                      shade(skin, 0.8 * dk)])))
        cv.save()
        cv.translate(x, y)
        cv.rotate(rot)
        cv.drawRoundRect(skia.Rect.MakeLTRB(-70, -14, 80, 0), 8, 8, paint(shade(sole, dk)))
        foot = skia.Path()
        foot.moveTo(-64, -14)
        foot.cubicTo(-70, -60, -40, -84, -20, -80)
        foot.cubicTo(10, -60, 40, -40, 74, -26)
        foot.quadTo(84, -18, 76, -14)
        foot.close()
        cv.drawPath(foot, paint(shade(skin, dk)))
        for sx in (-34, 6, 40):
            cv.drawLine(sx - 4, -14, sx + 6, -60 + abs(sx) * 0.4, paint(shade(strap, dk), stroke=8))
        cv.restore()
        ph = ((t / T + i * 0.5) % 1.0)
        if ph < 0.25:  # dust kicked up on landing
            u = ph / 0.25
            for k in range(7):
                ang = math.pi + (k / 6) * math.pi
                d = 30 + 70 * u
                cv.drawCircle(x + math.cos(ang) * d * 1.4, ground - 6 + math.sin(ang) * d * 0.4, 8 + 14 * u,
                              paint((230, 196, 150), 0.35 * (1 - u), blur=6))
    # robe hem
    hem = skia.Path()
    hem.moveTo(-50, -100)
    hem.lineTo(W + 50, -100)
    pts = [(W + 50, hem_y)]
    for k in range(9, -2, -1):
        x = k * 80
        pts.append((x, hem_y + 22 * math.sin(k * 1.3 + t * 3)))
    hem.lineTo(*pts[0])
    for q in pts[1:]:
        hem.lineTo(*q)
    hem.close()
    cv.drawPath(hem, paint(shader=lin((0, 0), (0, hem_y), [(120, 100, 76), (176, 150, 112)])))
    cv.save()
    cv.clipPath(hem, skia.ClipOp.kIntersect, True)
    for k in range(12):
        fx = k * 70 - 30 + 10 * math.sin(t * 2 + k)
        cv.drawLine(fx, -100, fx + 12 * math.sin(k), hem_y + 30, paint((110, 88, 64), 0.5, stroke=6 + 4 * (k % 3)))
    cv.restore()
    cv.drawPath(hem, paint((118, 84, 56), stroke=10))
    S.dust(cv, t, 30, 0.35, wind=-120, y0=500, y1=1000)


def opening(cv, t):
    n1c = TL.cap("n1", 1)
    g0, n2 = TL.s("g0"), TL.s("n2")
    n2c = TL.cap("n2", 1)
    ridge = TL.e("n2") + 0.25
    life = LIVES["moses"]

    def wide(cv, t, lt):
        rise = ramp(t, 0, 10)
        with Cam(cv, 360, 640 - 20 * ramp(t, 0, 8), 1.0 + 0.04 * t / 8, t=t):
            S.desert(cv, t, horizon=690, sun=(470, 655 - 40 * rise), warm=0.6 + 0.4 * rise)
            ww = ramp(t, 2.4, n1c)
            p = mk(walk=t * 1.7, staff=True, ember=0.25, arm_l=(12, -36, 1, 1), shadow=0.6)
            p["dim"] = 0.25
            p["tint"] = ((255, 170, 110), 0.25)
            fig(cv, MOSES, p, 300 + 30 * ww, 905 + 70 * ww, 0.13 + 0.15 * ww, t)
            S.dust(cv, t, 50, 0.3, wind=-50, y0=600, y1=1280)
        title_text(cv, "THE FIRST VILLAGE", 400, window(t, 0.5, 4.5, 1.2, 0.9), 50)
        f = font("italic", 30, 500)
        sub = "a parable of Moses"
        cv.drawString(sub, (W - text_w(sub, f)) / 2, 452, f, paint((255, 230, 200), 0.85 * window(t, 1.2, 4.5, 1.0, 0.9)))

    def mcu(cv, t, lt):
        with Cam(cv, 360, 640, 1.0 + 0.012 * lt, t=t):
            with Blur(cv, 5):
                cv.save()
                cv.translate(360, 640)
                cv.scale(1.6, 1.6)
                cv.translate(-360, -560)
                S.desert(cv, t, horizon=760, sun=(520, 690), warm=1.0)
                cv.restore()
            em = 0.2 + 0.8 * ramp(t, n1c + 0.8, n1c + 3.0)
            p = mk(walk=t * 1.6, ember=em, staff=True, arm_l=(12, -36, 1, 1), shadow=0)
            p["gx"], p["gy"] = 0.0, -0.1
            life.apply(p, t)
            p["brow"] += 0.15 * em
            p["smile"] = 0.1 * em
            p["tint"] = ((255, 176, 110), 0.12)
            at_head(cv, MOSES, p, 360 + 6 * math.sin(t * 1.6 * math.pi / 2), 480, 2.05, t)
            S.dust(cv, t, 45, 0.45, wind=-90, y0=500, y1=1280, size=1.6)

    def memory(cv, t, lt):
        with Cam(cv, 360, 640, 1.06 + 0.02 * lt, t=t):
            with Blur(cv, 5):
                cv.save()
                cv.translate(360, 640)
                cv.scale(1.6, 1.6)
                cv.translate(-360, -560)
                S.desert(cv, t, horizon=760, sun=(520, 690), warm=1.0)
                cv.restore()
            mem = window(t, g0 - 0.2, n2 + 0.9, 0.8, 1.0)
            glow(cv, 360, 170, 260, (255, 210, 150), 0.35 * mem, blend="screen")
            S.burning_bush(cv, 360, 215, 0.62, t, a=0.7 * mem)
            S.light_rays(cv, 360, 160, mem * 0.45, t, n=11, L=900, spread=2.2, base=math.pi / 2)
            closed = window(t, g0 - 0.25, n2 + 0.5, 0.35, 0.4)
            hand = window(t, g0 + 0.1, n2 + 0.8, 0.6, 0.6)
            p = mk(ember=1.0, lid=closed * 0.97, smile=0.35 * closed, staff=True, arm_l=(12, -36, 1, 1),
                   arm_r=arm_mix(REST, MOUTH, hand), shadow=0, hand_r="open", hand_rot_r=-15 * hand)
            life.apply(p, t)
            p["pitch"] = -0.12 * closed
            p["tint"] = ((255, 176, 110), 0.12)
            at_head(cv, MOSES, p, 360, 500, 2.05, t)
            S.dust(cv, t, 40, 0.4, wind=-90, y0=500, y1=1280, size=1.6)

    def ridge_back(cv, t, lt):
        with Cam(cv, 360, 640, 1.0 + 0.02 * lt, t=t):
            S.desert(cv, t, horizon=640, sun=(560, 520), warm=1.0, dunes=False)
            S.dune_layer(cv, 690, 30, (206, 140, 98), 5)
            cv.save()
            cv.translate(420, 780)
            cv.scale(0.3, 0.3)
            S.village_aerial(cv, t)
            cv.restore()
            cv.drawRect(skia.Rect.MakeLTRB(-100, 700, W + 100, 900),
                        paint(shader=lin((0, 700), (0, 900), [((240, 180, 130), 0.35), ((240, 180, 130), 0.0)])))
            S.dune_layer(cv, 1000, 90, (214, 146, 92), 6, rim=0.7, light=(255, 210, 160))
            S.draw_back(cv, MOSES, 200, 1260, 1.25, t)
            cv.drawLine(80, 1240, 112, 700, paint((96, 66, 40), stroke=13))
            S.dust(cv, t, 50, 0.35, wind=-60, y0=600, y1=1280)

    run(cv, t, [(0, wide), (n1c, mcu), (g0 - 0.6, memory), (n2c, walk_feet), (ridge, ridge_back)])


# ------------------------------------------------------------------ scene: VILLAGE & the Elder
CROWD = [villager(i) for i in range(16)]


def plaza(cv, t, dim=0.0, crack=0.0, elder=None, crowd_backs=True, people=None, lights=0.0):
    S.sky(cv, [mixc((176, 188, 200), (20, 24, 50), dim), mixc((214, 206, 190), (50, 46, 74), dim)], None, 0, 520)
    S.house_row(cv, 520, 200, n=5, x0=-160, x1=W + 160, dim=dim, seed=2, col=(190, 180, 164))
    S.house_row(cv, 560, 150, n=7, x0=-260, x1=W + 260, dim=dim * 0.9, seed=4, col=(168, 158, 142), lights=lights)
    S.paving(cv, (360, 380), 560, 900, S.GROUND_IN, dim=dim)
    S.dais(cv, 360, 690, 300, 60, crack=crack, dim=dim)
    if elder:
        elder()
    if people:
        people()


def elder_pose(t, **kw):
    p = mk(**kw)
    LIVES["elder"].apply(p, t, 0.6)
    p["pitch"] -= 0.06
    return p


def chop(t, beats, side="r"):
    """Arm 'hammer' gesture hitting at each beat time."""
    v = 0.0
    for b in beats:
        d = t - b
        if -0.35 < d < 0.5:
            v = max(v, ease_out(clamp((d + 0.35) / 0.3)) * (1 - clamp(d / 0.5)) if d > 0 else ease_out(clamp((d + 0.35) / 0.35)) * 0.6)
    return v


def village(cv, t):
    n3b, n3bc = TL.s("n3b"), TL.cap("n3b", 2)
    e1a, e1b, e1c = TL.s("e1a"), TL.s("e1b"), TL.s("e1c")
    e1b2 = TL.cap("e1b", 2)

    def aerial(cv, t, lt):
        u = smooth(lt / (n3b - TL.m("village")))
        S.aerial_view(cv, t, zoom=lerp(1.0, 1.9, u), focus=(0, lerp(80, 0, u)))
        S.grade(cv, (140, 150, 180), 0.2)

    def wide(cv, t, lt):
        z = 1.0 + 0.03 * lt

        def elder():
            p = elder_pose(t, open=fake_talk(t, 3, 0.5), arm_r=(lerp(10, 40, chop(t, [t - (t % 1.3) + 0.6])), -60, 1, 1),
                           hand_r="fist", lid=0.25)
            fig(cv, ELDER, p, 360, 676, 0.55, t)

        def people():
            for i in range(7):
                x = -40 + i * 125 + (i % 2) * 30
                S.draw_back(cv, CROWD[i], x, 1080 + (i % 2) * 40, 0.78, t)
            for i in range(5):
                S.draw_back(cv, CROWD[8 + i], 60 + i * 150, 1330, 1.0, t)
        with Cam(cv, 360, 640, z, t=t):
            plaza(cv, t, elder=elder, people=people)
        S.grade(cv, (150, 160, 180), 0.18)

    def medium(cv, t, lt):
        beats = [TL.cap("n3b", 2) + 0.4 + k * 0.8 for k in range(6)]
        c = chop(t, beats)
        with Cam(cv, 360, 640, 1.0 + 0.01 * lt, t=t):
            with Blur(cv, 4):
                cv.save()
                cv.translate(360, 640)
                cv.scale(2.0, 2.0)
                cv.translate(-360, -560)
                plaza(cv, t)
                cv.restore()
            p = elder_pose(t, open=fake_talk(t, 4, 0.55), anger=0.2, lid=0.2, hand_r="fist",
                           arm_r=(lerp(20, 60, c), lerp(-150, -60, c), 1, 1))
            p["brow"] += -0.2 * c
            at_head(cv, ELDER, p, 360, 470, 1.5, t)
        S.grade(cv, (150, 160, 180), 0.18)

    def mcu_e1a(cv, t, lt):
        u = ramp(t, e1a + 1.6, TL.e("e1a"))
        with Cam(cv, 360, 640, 1.0 + 0.012 * lt, t=t):
            with Blur(cv, 6):
                cv.save()
                cv.translate(360, 640)
                cv.scale(2.4, 2.4)
                cv.translate(-330, -540)
                plaza(cv, t)
                cv.restore()
            p = elder_pose(t, sneer=0.9 * u, lid=0.3 + 0.15 * u, anger=0.25, gx=0.6, turn=0.18,
                           arm_r=(lerp(10, 82, ramp(t, e1a + 0.3, e1a + 1.0)), -12, 1, 1), hand_r="point")
            speak(p, ("elder",), t)
            at_head(cv, ELDER, p, 360, 520, 2.3, t)
        S.grade(cv, (150, 160, 180), 0.18)

    def nodders(cv, t, lt):
        nod = 0.5 + 0.5 * math.sin((t - e1b) * 2 * math.pi / 1.4)
        with Cam(cv, 360, 640, 1.0 + 0.015 * lt, t=t):
            with Blur(cv, 5):
                plaza(cv, t)
            for k, i in enumerate((3, 6, 9)):
                p = mk(lid=0.35, pitch=0.1 + 0.18 * nod, gx=-0.3 if k == 2 else 0.3 * (1 - k), gy=-0.4)
                LIVES[f"v{i}"].apply(p, t, 0.2)
                at_head(cv, CROWD[i], p, 130 + k * 230, 520 + (k % 2) * 60, 1.25, t)
            for k, i in enumerate((1, 5)):
                p = mk(lid=0.35, pitch=0.12 + 0.18 * nod, gy=-0.4)
                LIVES[f"v{i}"].apply(p, t, 0.2)
                at_head(cv, CROWD[i], p, 245 + k * 230, 820, 1.55, t)
        S.grade(cv, (150, 160, 180), 0.22)

    def mcu_e1c(cv, t, lt):
        beats = [TL.cap("e1c", 1) + 0.35, TL.cap("e1c", 2) + 0.35]
        c = chop(t, beats)
        smug = ramp(t, e1c - 0.5, e1c + 1.0)
        with Cam(cv, 360, 640, 1.04 + 0.02 * lt, t=t):
            with Blur(cv, 6):
                cv.save()
                cv.translate(360, 640)
                cv.scale(2.4, 2.4)
                cv.translate(-390, -540)
                plaza(cv, t)
                cv.restore()
            p = elder_pose(t, lid=0.2 + 0.25 * smug, sneer=0.3 * smug, smile=0.15 * smug, hand_r="fist",
                           arm_r=(lerp(20, 60, c), lerp(-150, -60, c), 1, 1))
            p["pitch"] -= 0.15 * smug
            speak(p, ("elder",), t)
            at_head(cv, ELDER, p, 360, 520, 2.3, t)
        S.grade(cv, (150, 160, 180), 0.18)

    run(cv, t, [(TL.m("village"), aerial), (n3b, wide), (n3bc, medium), (e1a, mcu_e1a), (e1b, nodders),
                (e1b2, mcu_e1c), (e1c, mcu_e1c)])


# ------------------------------------------------------------------ scene: FEAR, then the fire
def fear(cv, t):
    f0, f1, n5, n5b = TL.s("n4"), TL.s("f1"), TL.s("n5"), TL.s("n5b")
    step = TL.cap("n5", 1)
    life = LIVES["moses"]

    def at_gate(cv, t, lt):
        fearv = ramp(t, f0 + 0.5, f1 + 0.5) * (1 - ramp(t, n5 + 0.3, n5 + 1.6))
        flare = ramp(t, n5 + 0.2, n5 + 1.6)
        stepu = ramp(t, step, step + 1.0, ease_out)
        z = 1.0 + 0.04 * lt / 8 + 0.08 * stepu
        with Cam(cv, 360, 640, z, t=t):
            with Blur(cv, 4):
                cv.save()
                cv.translate(360, 640)
                cv.scale(1.35, 1.35)
                cv.translate(-360, -600)
                S.gate_inside(cv, t, light=1.0 - 0.6 * fearv)
                cv.restore()
            ember = lerp(0.45, 0.12, fearv) if flare == 0 else lerp(0.12, 0.85, flare) * (1 - 0.3 * ramp(t, n5 + 3, n5 + 5))
            p = mk(ember=ember, worry=0.9 * fearv, brow=0.35 * fearv, wide=0.5 * fearv, press=0.5 * fearv,
                   staff=True, arm_l=(12, -36, 1, 1), rim=1, rim_a=0.5)
            life.apply(p, t, 1.0 + 1.6 * fearv)
            dart = fearv * 0.5 * noise(t, 4, 6)
            p["gx"] += dart
            p["gy"] += 0.25 * fearv
            if fearv > 0.6:
                p["blink"] = max(p["blink"], window(t, f1 + 1.6, f1 + 2.0, 0.08, 0.1))
            # resolve: eyes close as the fire rises, then open set and steady
            shut = window(t, n5 + 0.1, n5 + 1.2, 0.2, 0.35)
            p["lid"] = max(p["lid"], 0.95 * shut)
            p["anger"] = 0.25 * flare * (1 - shut)
            p["press"] = max(p["press"], 0.5 * flare)
            p["breath"] = 2 * window(t, n5, n5 + 1.6, 0.4, 0.6)
            hy, sc = 520 + 60 * stepu, 2.0 + 0.25 * stepu
            if flare > 0:
                S.light_rays(cv, 360, hy + 136 * sc, flare * (1 - ramp(t, n5 + 2.5, n5 + 4.5)), t, n=13, L=1100,
                             spread=6.2)
            at_head(cv, MOSES, p, 360, hy, sc, t)
            S.ghost(cv, 360, 470, t, a=fearv, s=1.5)
        S.vignette(cv, 0.35 + 0.5 * fearv)
        S.grade(cv, (60, 70, 110), 0.45 * fearv, "multiply")
        S.grade(cv, (255, 170, 90), 0.25 * flare * (1 - ramp(t, n5 + 3, n5 + 5)), "softlight")

    def enters(cv, t, lt):
        turn = ramp(t, n5b + 0.6, n5b + 1.8)
        walk = 1 - ramp(t, n5b + 2.4, n5b + 3.2)
        mx = lerp(-60, 170, ramp(t, n5b - 0.3, n5b + 3.0, ease_out))
        z = lerp(1.0, 1.25, ramp(t, TL.cap("n5b", 1), TL.cap("n5b", 1) + 3.5))

        def elder():
            p = elder_pose(t, gx=-0.7 * turn, turn=-0.25 * turn, lid=0.2, brow=0.3 * turn, open=fake_talk(t, 3, 0.5) * (1 - turn))
            fig(cv, ELDER, p, 470, 676, 0.55, t)

        def people():
            for i in range(6):
                x = 250 + i * 95
                S.draw_back(cv, CROWD[i], x, 960 + (i % 2) * 30, 0.62, t, turn=-1.5 * turn * (1 if i < 4 else 0.5))
            p = mk(walk=t * 1.7 if walk > 0 else None, ember=0.75, staff=True, arm_l=(12, -36, 1, 1), turn=0.35,
                   gx=0.6)
            LIVES["moses"].apply(p, t)
            fig(cv, MOSES, p, mx, 1180, 0.95, t)
        with Cam(cv, lerp(360, 250, ramp(t, TL.cap("n5b", 1), TL.cap("n5b", 1) + 3.5)), 700, z, t=t):
            plaza(cv, t, elder=elder, people=people)
        S.grade(cv, (150, 160, 180), 0.15)

    run(cv, t, [(TL.m("fear"), at_gate), (n5b, enters)])


# ------------------------------------------------------------------ scene: MOSES SPEAKS
def moses_bg(cv, t, sc=2.2, ox=360, oy=560, sigma=7, dim=0.0, warm=0.0):
    with Blur(cv, sigma):
        cv.save()
        cv.translate(360, 640)
        cv.scale(sc, sc)
        cv.translate(-ox, -oy)
        plaza(cv, t, dim=dim)
        cv.restore()
    if warm:
        glow(cv, 360, 600, 700, (255, 190, 120), 0.25 * warm, blend="screen")


def speech(cv, t):
    m0, m1, m2, m3, m4, m5, m6, m7 = (TL.s(f"m{i}") for i in range(8))
    life = LIVES["moses"]
    light_on = m5 + 1.0

    def mcu(cv, t, lt):
        with Cam(cv, 360, 640, 1.0 + 0.01 * lt, t=t):
            moses_bg(cv, t)
            up = ramp(t, m1 - 0.3, m1 + 0.6)
            hands = ramp(t, m1 + 0.3, m1 + 1.2)
            p = mk(ember=0.6, worry=0.6 - 0.3 * up, gy=0.6 * (1 - up) - 0.15 * up, pitch=0.25 * (1 - up),
                   arm_l=arm_mix(REST, OPEN, hands), arm_r=arm_mix(REST, OPEN, hands), hand_rot_l=40 * hands,
                   hand_rot_r=-40 * hands)
            life.apply(p, t)
            speak(p, ("moses",), t, 1.0, 1.2)
            at_head(cv, MOSES, p, 360, 500, 2.2, t)
        S.grade(cv, (255, 200, 150), 0.08)

    def listeners(cv, t, lt, lit=0.0):
        with Cam(cv, 360, 640, 1.0 + 0.012 * lt, t=t):
            moses_bg(cv, t, 1.8, 420, 600, 6, warm=lit)
            soft = ramp(t, m2 + 1.2, m2 + 3.0)
            p = mk(gx=-0.7, gy=-0.1, worry=0.35 * soft + 0.2 * lit, brow=0.15 + 0.4 * lit, turn=-0.25,
                   wide=0.35 * lit, open=0.15 * lit, light=lit)
            LIVES["potter"].apply(p, t, 0.4)
            if lit:
                p["tint"] = ((255, 200, 140), 0.25 * lit)
            at_head(cv, POTTER, p, 520, 470, 1.55, t)
            p = mk(gx=-0.75, gy=-0.05, worry=0.5 * soft, smile=0.1 * soft - 0.05, turn=-0.3,
                   wide=0.45 * lit, open=0.2 * lit, brow=0.5 * lit)
            LIVES["weaver"].apply(p, t, 0.5)
            if lit:
                p["tint"] = ((255, 200, 140), 0.3 * lit)
            at_head(cv, WEAVER, p, 250, 600, 1.85, t)
            if lit:
                glow(cv, 0, 600, 600, (255, 200, 120), 0.35 * lit, blend="screen")
        S.grade(cv, (255, 200, 150), 0.08)

    def cu_throat(cv, t, lt):
        touch = window(t, m3 + 0.3, m4 - 0.3, 0.6, 0.6)
        with Cam(cv, 360, 640, 1.0 + 0.012 * lt, t=t):
            moses_bg(cv, t, 2.8, 380, 520, 9)
            p = mk(ember=0.6, worry=0.75, brow=0.15, gy=0.3 * touch, gx=-0.15,
                   arm_r=arm_mix(REST, THROAT, touch), hand_r="open", hand_rot_r=-15 * touch)
            life.apply(p, t)
            speak(p, ("moses",), t, 0.95, 1.0)
            at_head(cv, MOSES, p, 360, 470, 3.0, t)
        S.grade(cv, (255, 200, 150), 0.08)

    def vessel_shot(cv, t, lt):
        crack = ramp(t, m4 + 0.6, m4 + 2.6)
        light = ramp(t, light_on, light_on + 1.4)
        with Cam(cv, 360, 640 - 60 * light, 1.0 + 0.02 * lt + 0.25 * light, t=t):
            moses_bg(cv, t, 1.9, 360, 540, 6, warm=0.6 * light)
            p = mk(ember=0.6 + 0.4 * light, worry=0.55 * (1 - light), brow=0.25 * light, smile=0.12 * light, gy=0.45,
                   arm_l=(26, -70, 0.9, 1), arm_r=(26, -70, 0.9, 1), hand_rot_l=-50, hand_rot_r=50)
            life.apply(p, t)
            speak(p, ("moses",), t, 0.95, 1.0)
            at_head(cv, MOSES, p, 360, 330, 1.6, t)
            S.vessel(cv, 360, 700 + 6 * math.sin(t * 1.3), 1.25, t, crack=crack, light=light,
                     a=0.92 * ramp(t, m4 - 0.2, m4 + 0.8))
        S.grade(cv, (255, 200, 150), 0.08 + 0.15 * light)

    def ecu(cv, t, lt):
        wav = window(t, m6, m7, 0.6, 0.3)
        with Cam(cv, 360, 640, 1.0 + 0.01 * lt, t=t):
            moses_bg(cv, t, 3.4, 360, 520, 11, warm=0.4)
            p = mk(ember=0.8, worry=0.45, wet=0.8 * wav, smile=0.18 + 0.05 * math.sin(t * 7), brow=0.1, gx=-0.1)
            life.apply(p, t)
            speak(p, ("moses",), t, 0.9, 0.8)
            p["tilt"] += 1.5 * math.sin(t * 9) * wav  # the voice that wavers
            at_head(cv, MOSES, p, 360, 520, 4.0, t)
        S.grade(cv, (255, 200, 150), 0.1)

    def hand_heart(cv, t, lt):
        up = window(t, TL.cap("m7", 1) - 0.4, TL.cap("m7", 1) + 1.6, 0.4, 0.6)
        with Cam(cv, 360, 640, 1.0 + 0.015 * lt, t=t):
            moses_bg(cv, t, 2.2, 360, 540, 7, warm=0.3)
            hand = ramp(t, m7 + 0.2, m7 + 1.0)
            p = mk(ember=0.7 + 0.3 * hand, worry=0.3, smile=0.15,
                   arm_l=(lerp(8, 18, hand), lerp(-8, -122, hand), 1, 1), hand_rot_l=20 * hand, gy=-0.75 * up,
                   pitch=-0.2 * up)
            life.apply(p, t)
            speak(p, ("moses",), t, 1.0, 1.0)
            at_head(cv, MOSES, p, 360, 470, 2.3, t)
        S.grade(cv, (255, 200, 150), 0.1)

    run(cv, t, [(TL.m("speech"), mcu), (m2, listeners), (m3, cu_throat), (m4, vessel_shot),
                (TL.e("m5") + 0.5, lambda cv, t, lt: listeners(cv, t, lt, lit=1.0 - 0.4 * ramp(t, m6, m6 + 1.5))),
                (m6 + 1.0, ecu), (m7, hand_heart)])


# ------------------------------------------------------------------ scene: THE ELDER SNAPS
def elder2(cv, t):
    n6, e2a, e2b, e2c = TL.s("n6"), TL.s("e2a"), TL.s("e2b"), TL.s("e2c")
    brittle = TL.cap("n6", -1)

    def cu(cv, t, lt):
        u = ramp(t, n6 + 0.3, brittle - 1.5)
        with Cam(cv, 360, 640, 1.0 + 0.03 * lt, t=t):
            with Blur(cv, 8):
                cv.save()
                cv.translate(360, 640)
                cv.scale(3.0, 3.0)
                cv.translate(-360, -520)
                plaza(cv, t)
                cv.restore()
            p = elder_pose(t, anger=0.9 * u, furrow=u, press=u, lid=0.15 + 0.15 * u, flush=0.5 * u, jaw_clench=u,
                           gx=-0.5, turn=-0.12, sneer=0.2 * u, smile=-0.3 * u)
            at_head(cv, ELDER, p, 360, 560, 3.2, t)
        S.grade(cv, (150, 160, 180), 0.2)

    def small(cv, t, lt):
        z = lerp(1.15, 1.0, ramp(t, brittle - 2.0, brittle + 1.0))

        def el():
            p = elder_pose(t, anger=0.9, furrow=1, press=1, flush=0.5, gx=-0.5)
            fig(cv, ELDER, p, 360, 676, 0.55, t)
        with Cam(cv, 360, 700, z, t=t):
            plaza(cv, t, crack=ramp(t, brittle, brittle + 0.8), elder=el)
        S.grade(cv, (150, 160, 180), 0.2)

    def snap(cv, t, lt):
        pt = ramp(t, e2a - 0.1, e2a + 0.35, ease_out)
        with Cam(cv, 360, 640, 1.0 + 0.02 * lt, shake=0.5 * window(t, e2a, e2a + 0.5, 0.05, 0.3), t=t):
            with Blur(cv, 6):
                cv.save()
                cv.translate(360, 640)
                cv.scale(2.4, 2.4)
                cv.translate(-400, -540)
                plaza(cv, t)
                cv.restore()
            p = elder_pose(t, anger=0.8, wide=0.55, worry=0.25, flush=0.5, gx=-0.85, turn=-0.25,
                           arm_l=(lerp(8, 88, pt), lerp(-8, -8, pt), 1, 1), hand_l="point")
            speak(p, ("elder",), t, 1.1, 1.3)
            at_head(cv, ELDER, p, 400, 520, 2.3, t)
        S.grade(cv, (150, 160, 180), 0.2)

    def sweep(cv, t, lt):
        sw = ramp(t, e2b + 0.1, e2b + 0.9)
        with Cam(cv, 360, 640, 1.0 + 0.01 * lt, t=t):
            with Blur(cv, 4):
                cv.save()
                cv.translate(360, 640)
                cv.scale(2.0, 2.0)
                cv.translate(-360, -560)
                plaza(cv, t)
                cv.restore()
            p = elder_pose(t, anger=0.6, flush=0.4, gx=lerp(-0.4, 0.6, sw), turn=lerp(-0.2, 0.25, sw),
                           arm_l=(lerp(70, 40, sw), lerp(-10, -20, sw), 1, 1), hand_l="open",
                           arm_r=(lerp(8, 60, sw), -30, 1, 1), hand_r="open")
            speak(p, ("elder",), t, 1.0, 1.2)
            at_head(cv, ELDER, p, 360, 470, 1.5, t)
        S.grade(cv, (150, 160, 180), 0.2)

    def flick(cv, t, lt):
        fl = ramp(t, TL.cap("e2c", 1) - 0.1, TL.cap("e2c", 1) + 0.25)
        back = ramp(t, TL.cap("e2c", 1) + 0.6, TL.cap("e2c", 1) + 1.2)
        g = ramp(t, TL.e("e2c") - 0.2, TL.e("e2c") + 0.5)
        with Cam(cv, 360, 640, 1.0 + 0.015 * lt, t=t):
            with Blur(cv, 6):
                cv.save()
                cv.translate(360, 640)
                cv.scale(2.4, 2.4)
                cv.translate(-330, -540)
                plaza(cv, t)
                cv.restore()
            p = elder_pose(t, lid=0.55, sneer=0.6, gx=0.5, turn=0.3, anger=0.15,
                           arm_r=(lerp(30, 55, fl) * (1 - back) + 8 * back, -95 * (1 - back), 1, 1),
                           hand_r="open", hand_rot_r=lerp(-40, 60, fl))
            p["pitch"] -= 0.1
            speak(p, ("elder",), t, 1.0, 1.0)
            at_head(cv, ELDER, p, 360, 520, 2.3, t)
            for s, st, x0 in ((-1, GUARD, -160), (1, GUARD2, W + 160)):
                gp = mk(lid=0.4, arm_l=(8, -8, 1, 1), arm_r=(8, -8, 1, 1), walk=t * 1.6)
                fig(cv, st, gp, lerp(x0, x0 - s * 170, g), 1450, 1.9, t)
        S.grade(cv, (150, 160, 180), 0.2)

    run(cv, t, [(TL.m("elder2"), cu), (brittle - 2.0, small), (e2a, snap), (e2b, sweep), (e2c, flick)])


# ------------------------------------------------------------------ scene: EXPELLED
def expel(cv, t):
    n7 = TL.s("n7")
    c1, c2 = TL.cap("n7", 1), TL.cap("n7", 2)
    th = TL.s("throw")

    def grabbed(cv, t, lt):
        g = ramp(t, n7 - 0.1, n7 + 0.6)
        with Cam(cv, 360, 640, 1.0 + 0.02 * lt, t=t):
            with Blur(cv, 4):
                cv.save()
                cv.translate(360, 640)
                cv.scale(1.8, 1.8)
                cv.translate(-360, -560)
                plaza(cv, t)
                cv.restore()
            for st, x, s in ((GUARD, 130, -1), (GUARD2, 590, 1)):
                gp = mk(lid=0.4, turn=-0.35 * s, gx=-0.6 * s)
                arm = "arm_r" if s < 0 else "arm_l"
                gp[arm] = (lerp(8, 70, g), lerp(-8, -40, g), 1, 1)
                gp["hand_" + arm[-1]] = "grip"
                LIVES["g1" if s < 0 else "g2"].apply(gp, t, 0.2)
                fig(cv, st, gp, x - s * 30 * g, 1290, 1.45, t)
            p = mk(ember=0.4, worry=0.55, lid=0.45, gy=0.45, pitch=0.2,
                   arm_l=(lerp(8, 22, g), -10, 1, 1), arm_r=(lerp(8, 22, g), -10, 1, 1))
            LIVES["moses"].apply(p, t, 0.5)
            fig(cv, MOSES, p, 360, 1300, 1.5, t)
            for st, x, s in ((GUARD, 130, -1), (GUARD2, 590, 1)):  # guards' gripping hands in front
                hx = 360 + s * (95 - 10 * g) * 1.5
                cv.drawCircle(hx, 1300 - 330 * 1.5, 20 * g, paint(st.skin, g))
        S.grade(cv, (150, 160, 180), 0.2)

    def faces(cv, t, lt):
        pan = (t - c1) / max(0.5, c2 - c1)
        with Cam(cv, lerp(250, 1050, pan), 640, 1.0, t=t):
            with Blur(cv, 5):
                for k in range(3):
                    cv.save()
                    cv.translate(k * 720, 0)
                    plaza(cv, t)
                    cv.restore()
            for k in range(6):
                i = (k * 5 + 2) % 16
                gasp = window(t, c1 + k * 0.25, c2 + 2, 0.25, 0.5)
                p = mk(wide=0.7 * gasp, brow=0.7 * gasp, worry=0.4, open=0.35 * gasp, bright=0.2, gx=-0.4 + 0.8 * pan,
                       turn=0.1)
                if k in (1, 4):
                    p["arm_r"] = MOUTH
                LIVES[f"v{i}"].apply(p, t, 0.3)
                at_head(cv, CROWD[i], p, 130 + k * 230, 470 + (k % 2) * 80, 1.6, t)
        # silhouettes of the guards and Moses passing close to the lens
        cv.saveLayerAlpha(None, 210)
        with Blur(cv, 10):
            for k, st in enumerate((GUARD, MOSES, GUARD2)):
                x = lerp(1000, -400, pan) + k * 200
                p = mk(walk=t * 1.8, dim=0.8)
                fig(cv, st, p, x, 1900, 1.9, t)
        cv.restore()
        S.grade(cv, (150, 160, 180), 0.2)

    def thrown(cv, t, lt):
        gate = ramp(t, c2 - 0.2, c2 + 0.8) * (1 - ramp(t, th + 0.6, th + 1.5, ease_in))
        push = ramp(t, c2 + 0.9, c2 + 1.6, ease_in)
        land = TL.e("n7") - 0.1
        fall = ramp(t, land - 0.35, land + 0.1, ease_in)
        shake = window(t, land, land + 0.5, 0.02, 0.4) + 0.6 * window(t, th + 1.5, th + 1.9, 0.02, 0.35)
        with Cam(cv, 360, 640, 1.0, shake=shake, t=t):
            S.wall_outside(cv, t, gate=gate, night=0.15)
            if t < th + 1.4:  # guards in the gateway
                for st, x in ((GUARD, 300), (GUARD2, 420)):
                    gp = mk(lid=0.4, dim=0.35, arm_l=(30, -40, 1, 1), arm_r=(30, -40, 1, 1))
                    fig(cv, st, gp, x, 822, 0.6, t)
            s = lerp(0.62, 1.2, push)
            y = lerp(822, 1160, push)
            p = mk(ember=0.15, worry=0.8, wide=0.5 * (1 - fall), lid=0.3 * fall, kneel=fall, bow=0.5 * fall,
                   pitch=0.3 * fall, arm_l=(lerp(30, 20, fall), lerp(-60, -20, fall), 1, 1),
                   arm_r=(lerp(30, 20, fall), lerp(-60, -20, fall), 1, 1), dirt=0.5 * fall, shadow=1)
            p["lean"] = 6 * push * (1 - fall)
            if push > 0:
                fig(cv, MOSES, p, 360 + 20 * push, y, s, t)
            if t > land:
                u = clamp((t - land) / 1.2)
                for k in range(16):
                    ang = math.pi + (k / 15) * math.pi
                    d = 60 + 240 * ease_out(u)
                    cv.drawCircle(380 + math.cos(ang) * d * 1.3, 1170 + math.sin(ang) * d * 0.35, 20 + 40 * u,
                                  paint((210, 170, 120), 0.45 * (1 - u), blur=14))
        S.grade(cv, (255, 160, 100), 0.12)

    run(cv, t, [(TL.m("expel"), grabbed), (c1, faces), (c2 - 0.2, thrown)])


# ------------------------------------------------------------------ scene: ALONE
def dusk_of(t):
    return lerp(0.2, 0.55, ramp(t, TL.m("alone"), TL.m("presence") + 6))


def kneel_pose(t, **kw):
    p = mk(kneel=1.0, bow=0.6, pitch=0.35, dirt=0.85, lid=0.5, worry=0.85, smile=-0.35, ember=0.1,
           arm_l=(14, -26, 1, 1), arm_r=(14, -26, 1, 1), hand_l="open", hand_r="open")
    p.update(kw)
    return p


def alone(cv, t):
    n8, n8c, n8b = TL.s("n8"), TL.cap("n8", -2), TL.s("n8b")
    mp1, mp3, mp4, n9, n9b = TL.s("mp1"), TL.s("mp3"), TL.s("mp4"), TL.s("n9"), TL.s("n9b")
    life = LIVES["moses"]

    def outside(t):
        night = dusk_of(t)
        S.wall_outside(cv, t, gate=0, night=night)
        return night

    def medium(cv, t, lt):
        with Cam(cv, 360, 700, 1.0 + 0.1 * smooth(lt / 9), t=t):
            night = outside(t)
            p = kneel_pose(t, dim=night * 0.45, tears=0.3)
            life.apply(p, t, 0.4)
            fig(cv, MOSES, p, 380, 1160, 1.2, t)
        S.grade(cv, (90, 100, 150), 0.2, "multiply")

    def face(cv, t, lt, tears=0.5):
        night = dusk_of(t)
        with Cam(cv, 360, 640, 1.0 + 0.01 * lt, t=t):
            with Blur(cv, 9):
                cv.save()
                cv.translate(360, 640)
                cv.scale(2.6, 2.6)
                cv.translate(-370, -700)
                outside(t)
                cv.restore()
            p = kneel_pose(t, dim=night * 0.35, tears=tears, tear_t=t, wet=0.8, bow=0.2, pitch=0.25, lid=0.4,
                           gx=0.0, gy=0.4)
            life.apply(p, t, 0.5)
            p["press"] = 0.4 + 0.2 * math.sin(t * 3)
            at_head(cv, MOSES, p, 360, 560, 3.6, t)
        S.grade(cv, (90, 100, 150), 0.18, "multiply")

    def chest(cv, t, lt):
        night = dusk_of(t)
        em = lerp(0.35, 0.06, ramp(t, n8b + 0.5, n8b + 4.0))
        with Cam(cv, 360, 640 + 40 * smooth(lt / 5), 1.0 + 0.06 * lt / 5, t=t):
            with Blur(cv, 8):
                cv.save()
                cv.translate(360, 640)
                cv.scale(2.0, 2.0)
                cv.translate(-370, -720)
                outside(t)
                cv.restore()
            p = kneel_pose(t, dim=night * 0.35, ember=em, tears=0.5, tear_t=t, wet=0.6)
            life.apply(p, t, 0.4)
            at_head(cv, MOSES, p, 360, 360, 2.2, t)
        S.grade(cv, (90, 100, 150), 0.2, "multiply")

    def prayer(cv, t, lt):
        night = dusk_of(t)
        up = window(t, mp3 - 0.3, mp4 + 0.6, 0.8, 0.9)
        with Cam(cv, 360, 640, 1.0 + 0.008 * lt, t=t):
            with Blur(cv, 9):
                cv.save()
                cv.translate(360, 640)
                cv.scale(2.6, 2.6)
                cv.translate(-370, -700)
                outside(t)
                cv.restore()
            closed = 1 - up
            p = kneel_pose(t, dim=night * 0.32, tears=0.9, tear_t=t, wet=1.0, bow=0.25 * closed,
                           pitch=0.45 * closed - 0.25 * up, lid=0.9 * closed + 0.15 * up, worry=1.0,
                           gy=-0.8 * up, smile=-0.45)
            life.apply(p, t, 0.3)
            speak(p, ("moses_w",), t, 0.8, 0.4)
            p["tilt"] += 0.8 * math.sin(t * 11) * 0.6
            at_head(cv, MOSES, p, 360, 560, 3.4, t)
        S.grade(cv, (90, 100, 150), 0.18, "multiply")

    def tiny(cv, t, lt):
        night = dusk_of(t)
        swirl = ramp(t, n9 + 0.4, n9b + 0.5)
        with Cam(cv, 360, 560, 0.62, t=t):
            S.wall_outside(cv, t, gate=0, night=night)
            p = kneel_pose(t, dim=night * 0.5)
            fig(cv, MOSES, p, 380, 1000, 0.5, t)
            # dust devil drifting past
            cx = lerp(-300, 1000, swirl)
            for k in range(60):
                h = k / 60
                ang = t * 6 + k * 0.7
                r = 20 + 90 * h
                cv.drawCircle(cx + math.cos(ang) * r, 1060 - h * 520 + math.sin(ang) * r * 0.2, 10 + 18 * h,
                              paint((200, 160, 120), 0.32 * math.sin(math.pi * swirl), blur=10))
        S.grade(cv, (90, 100, 150), 0.25, "multiply")
        S.vignette(cv, 0.55)

    def bowed(cv, t, lt):
        with Cam(cv, 360, 760, 1.12 + 0.05 * lt / 5, t=t):
            night = outside(t)
            p = kneel_pose(t, dim=night * 0.5, bow=1.0, pitch=0.5, lid=0.9, shake=1.0, tears=0.6, tear_t=t)
            life.apply(p, t, 0.2)
            fig(cv, MOSES, p, 370, 1160, 1.2, t)
        S.grade(cv, (80, 90, 150), 0.3, "multiply")
        S.vignette(cv, 0.6)

    run(cv, t, [(TL.m("alone"), medium), (n8c, face), (n8b, chest), (mp1, prayer), (n9, tiny), (n9b, bowed)])


# ------------------------------------------------------------------ scene: THE PRESENCE
def presence(cv, t):
    pr = TL.m("presence")
    n10b, n10c, g1, n11, g2, n12, n12b = (TL.s(k) for k in ("n10b", "n10c", "g1", "n11", "g2", "n12", "n12b"))
    warmth = TL.cap("n10b", 3)
    sigh0 = TL.s("sigh")
    life = LIVES["moses"]

    def night_sky(cv, t, horizon=820, rot=0.0, amount=1.0):
        night = lerp(dusk_of(t), 0.9, ramp(t, pr, n10c + 2))
        S.wall_outside(cv, t, gate=0, night=night, horizon=horizon)
        return night

    def stars_over(cv, t, a, rot=0.0, cy=200):
        S.stars(cv, t, a, cx=360, cy=cy, rot=rot, n=300, y1=700)

    def sighp(t):
        u = (t - sigh0)
        if u < 0:
            return 0.0
        if u < 1.1:
            return smooth(u / 1.1)
        return 1 - 1.6 * smooth((u - 1.1) / 2.0)

    def medium(cv, t, lt):
        warm = ramp(t, warmth - 0.5, warmth + 2.5)
        with Cam(cv, 360, 760, 1.17 + 0.05 * lt / 8, t=t):
            night = night_sky(cv, t)
            pres = ramp(t, TL.cap("n10b", 2), warmth + 2)
            glow(cv, 370, 700, 520 * (0.4 + warm), (255, 200, 130), 0.32 * pres, blend="screen")
            S.light_rays(cv, 370, -200, 0.9 * pres, t, n=7, L=1500, spread=0.5, base=math.pi / 2,
                         col=(255, 214, 150))
            p = kneel_pose(t, dim=night * 0.5 * (1 - 0.6 * warm), bow=1.0 - 0.5 * warm, pitch=0.5 - 0.2 * warm,
                           lid=0.9 - 0.3 * ramp(t, warmth + 1.5, warmth + 3), shake=1.0 - warm, tears=0.6, tear_t=t,
                           glowhand=warm)
            p["tint"] = ((255, 190, 120), 0.3 * warm)
            life.apply(p, t, 0.2)
            fig(cv, MOSES, p, 370, 1160, 1.2, t)
        S.grade(cv, (80, 90, 150), 0.3 * (1 - 0.5 * warm), "multiply")
        S.vignette(cv, 0.6)

    def turning(cv, t, lt):
        with Cam(cv, 360, 640, 1.0, t=t):
            fill(cv, (8, 10, 28))
            S.sky(cv, [(6, 8, 26), (20, 22, 60), (50, 44, 86)], [0, 0.6, 1], 0, 1000)
            rot = (t - n10c) * 2.2
            S.stars(cv, t, 1.0, cx=360, cy=260, rot=rot, n=420, x0=-700, x1=1400, y0=-800, y1=1300)
            for k in range(40):  # faint star trails
                r = 80 + k * 22
                a0 = hashf(k, 2) * 360
                arc = skia.Path()
                arc.addArc(oval(360, 260, r, r), a0 + rot, 6 + 10 * ramp(t, n10c, g1))
                cv.drawPath(arc, paint((200, 210, 255), 0.18, stroke=1.4))
            cv.drawRect(skia.Rect.MakeLTRB(-400, 1000, W + 400, H + 400), paint((24, 22, 40)))
            cv.drawRect(skia.Rect.MakeLTRB(-400, 960, W + 400, 1000), paint((34, 32, 54)))
            glow(cv, 360, 1080, 110, (255, 200, 130), 0.35, blend="screen")
            p = kneel_pose(t, dim=0.6, bow=0.3, pitch=0.1, lid=0.4, tears=0.5)
            fig(cv, MOSES, p, 360, 1150, 0.42, t)
        S.vignette(cv, 0.5)

    def cu(cv, t, lt, smile=0.0, close=0.0):
        hear = ramp(t, g1 - 0.1, g1 + 0.4)
        with Cam(cv, 360, 640, 1.0 + 0.01 * lt, t=t):
            fill(cv, (12, 14, 34))
            with Blur(cv, 6):
                stars_over(cv, t, 1.0, rot=(t - n10c) * 2.2, cy=-200)
            glow(cv, 360, 200, 800, (255, 190, 120), 0.18, blend="screen")
            p = kneel_pose(t, dim=0.2, bow=0.0, pitch=-0.25 * hear * (1 - close) + 0.08 * close,
                           lid=0.1 + 0.88 * close, wide=0.4 * hear * (1 - smile),
                           brow=0.5 * hear * (1 - smile), worry=0.7 - 0.35 * smile, gy=-0.75 * hear * (1 - close),
                           open=0.18 * hear * (1 - smile), smile=-0.2 + 0.55 * smile, tears=0.9, tear_t=t, wet=1.0,
                           glowhand=0.55)
            p["tint"] = ((255, 190, 130), 0.1)
            life.apply(p, t, 0.3)
            if smile:
                p["tilt"] += 1.0 * math.sin(t * 8) * smile * (1 - close)
            at_head(cv, MOSES, p, 360, 600, 3.6, t)
        S.vignette(cv, 0.45)

    def two(cv, t, lt):
        form = ramp(t, n12 + 0.6, n12 + 4.0)
        sg = sighp(t)
        with Cam(cv, 360, 700, 1.0 + 0.04 * lt / 10, t=t):
            fill(cv, (8, 10, 28))
            S.sky(cv, [(6, 8, 26), (18, 20, 56), (44, 40, 80)], [0, 0.6, 1], 0, 960)
            S.stars(cv, t, 1.0, cx=360, cy=260, rot=(t - n10c) * 2.2, n=300, x0=-500, x1=1200, y0=-600, y1=1000)
            cv.drawRect(skia.Rect.MakeLTRB(-400, 960, W + 400, H + 400), paint((30, 28, 46)))
            cv.drawRect(skia.Rect.MakeLTRB(-400, 940, W + 400, 960), paint((40, 38, 60)))
            S.star_figure(cv, 480, 1100, 0.95, t, a=form, sigh=max(0, sg), st=MOSES)
            # a soft wave of light on the out-breath
            if t > sigh0 + 1.1:
                u = clamp((t - sigh0 - 1.1) / 2.4)
                ring = skia.Path()
                ring.addOval(oval(390, 1000, 120 + 500 * u, 40 + 160 * u))
                cv.drawPath(ring, paint((255, 220, 170), 0.35 * (1 - u), stroke=10, blur=8, blend="plus"))
            p = kneel_pose(t, dim=0.35, bow=0.15 - 0.1 * sg, pitch=0.1, lid=lerp(0.35, 0.95, ramp(t, sigh0 + 0.9, sigh0 + 1.6)),
                           worry=0.4, smile=0.05, glowhand=0.7, sigh=sg, tears=0.6, breath=1.0)
            p["tint"] = ((200, 190, 255), 0.15)
            life.apply(p, t, 0.2, blinks=t < sigh0)
            fig(cv, MOSES, p, 250, 1100, 0.95, t)
            S.dust(cv, t, 30, 0.25 * ramp(t, sigh0 + 1.1, sigh0 + 2), wind=30, col=(255, 230, 190), y0=900, y1=1100)
        S.vignette(cv, 0.45)

    run(cv, t, [(pr, medium), (n10c, turning), (g1 - 0.4, cu), (n11, lambda cv, t, lt: cu(cv, t, lt, 0.1)),
                (g2 - 0.3, lambda cv, t, lt: cu(cv, t, lt, ramp(t, g2 + 0.5, g2 + 1.6),
                                              ramp(t, g2 + 1.1, g2 + 1.8))),
                (n12, two)])


# ------------------------------------------------------------------ scene: BACK INSIDE THE VILLAGE
def courtyard_bg(cv, t, dim=0.75):
    S.sky(cv, [(14, 18, 42), (40, 40, 76)], None, 0, 600)
    S.stars(cv, t, 0.6, n=120, y1=420)
    S.house_row(cv, 640, 300, n=3, x0=-200, x1=200, dim=dim, seed=7, lights=1.0)
    S.house_row(cv, 640, 300, n=3, x0=520, x1=W + 200, dim=dim, seed=8, lights=1.0)
    # the closed gate at the end of the straight street
    cv.drawRect(skia.Rect.MakeLTRB(200, 420, 520, 640), paint(mixc((150, 138, 118), (36, 40, 66), dim)))
    cv.drawRect(skia.Rect.MakeLTRB(300, 480, 420, 640), paint(mixc((112, 80, 52), (30, 26, 40), dim * 0.9)))
    cv.drawLine(360, 480, 360, 640, paint((20, 16, 24), stroke=3))
    S.paving(cv, (360, 520), 640, 900, S.GROUND_IN, dim=dim)
    glow(cv, 120, 560, 160, (255, 170, 90), 0.4)
    glow(cv, 120, 560, 30, (255, 220, 160), 0.8)


def village2(cv, t):
    v2 = TL.m("village2")
    look = TL.cap("n13", 3)
    p1, p2, p3, n14, n14b, n14c = (TL.s(k) for k in ("p1", "p2", "p3", "n14", "n14b", "n14c"))
    cage = TL.cap("n14", 2)
    end = TL.m("end")

    def lamp(p, a=0.35):
        p["tint"] = ((255, 170, 100), a)
        return p

    def weaver_loom(cv, t, lt):
        stop = ramp(t, v2 + 2.0, v2 + 3.0)
        lookup = ramp(t, TL.cap("n13", 1) + 0.6, TL.cap("n13", 1) + 1.4)
        shuttle = 0.5 + 0.5 * math.sin(t * 2.2) if stop < 1 else 0.5 + 0.5 * math.sin((v2 + 3.0) * 2.2)
        with Cam(cv, 360, 640, 1.0 + 0.012 * lt, t=t):
            with Blur(cv, 5):
                courtyard_bg(cv, t)
            p = lamp(mk(gy=0.55 * (1 - lookup), gx=0.6 * lookup, turn=0.2 * lookup, pitch=0.3 * (1 - lookup),
                        worry=0.3 * lookup, arm_l=(20, -60, 0.5, 0.5), arm_r=(20, -60, 0.5, 0.5), dim=0.25))
            LIVES["weaver"].apply(p, t, 0.4)
            at_head(cv, WEAVER, p, 360, 420, 1.9, t)
            S.loom(cv, 360, 760, 1.25, t, shuttle=shuttle, dim=0.4)
        S.grade(cv, (60, 70, 130), 0.25, "multiply")

    def two_shot(cv, t, lt):
        with Cam(cv, 360, 640, 1.0 + 0.015 * lt, t=t):
            courtyard_bg(cv, t)
            S.wheel(cv, 560, 1000, 1.2, t, spin=t * (1 - ramp(t, look, look + 2)), dim=0.5)
            pp = lamp(mk(gx=-0.3, gy=-0.1, turn=-0.3, worry=0.4, lid=0.15, dim=0.35, arm_l=(10, -20, 1, 1)), 0.25)
            LIVES["potter"].apply(pp, t, 0.3)
            fig(cv, POTTER, pp, 530, 960, 0.75, t)
            pw = lamp(mk(gx=0.8, turn=0.35, worry=0.35, dim=0.25), 0.35)
            LIVES["weaver"].apply(pw, t, 0.3)
            at_head(cv, WEAVER, pw, 170, 760, 1.55, t)
        S.grade(cv, (60, 70, 130), 0.25, "multiply")

    def potter(cv, t, lt):
        turn = ramp(t, p3 - 0.2, p3 + 0.5)
        hurt = ramp(t, p2 - 0.2, p2 + 0.6)
        ang = ramp(t, p3 + 0.8, p3 + 2.2)
        with Cam(cv, 360, 640, 1.0 + 0.02 * lt, shake=0.15 * window(t, p3 + 2.0, p3 + 2.6, 0.1, 0.3), t=t):
            with Blur(cv, 7):
                cv.save()
                cv.translate(360, 640)
                cv.scale(1.8, 1.8)
                cv.translate(-300, -600)
                courtyard_bg(cv, t)
                cv.restore()
            p = lamp(mk(gx=lerp(-0.4, -0.85, turn), gy=-0.05, turn=lerp(-0.15, -0.4, turn), worry=0.7 + 0.2 * hurt,
                        brow=0.25 * hurt, anger=0.75 * ang, furrow=0.7 * ang, dim=0.2, flush=0.3 * ang,
                        arm_r=arm_mix(REST, OPEN, ang), hand_r="open", hand_rot_r=-40 * ang), 0.3)
            LIVES["potter"].apply(p, t, 0.5)
            speak(p, ("potter",), t, 1.0, 1.4)
            at_head(cv, POTTER, p, 380, 520, 2.4, t)
        S.grade(cv, (60, 70, 130), 0.22, "multiply")

    def weaver_cu(cv, t, lt):
        bars = ramp(t, cage - 0.5, cage + 2.0)
        down = ramp(t, n14 + 1.0, n14 + 2.0)
        with Cam(cv, 360, 640, 1.0 + 0.015 * lt, t=t):
            with Blur(cv, 8):
                cv.save()
                cv.translate(360, 640)
                cv.scale(2.0, 2.0)
                cv.translate(-360, -560)
                courtyard_bg(cv, t)
                cv.restore()
            p = lamp(mk(gx=0.4 * (1 - down), gy=0.5 * down - 0.6 * bars * (1 - down * 0.5), worry=0.75 + 0.15 * bars,
                        wide=0.3 * bars, brow=0.15 + 0.2 * bars, smile=-0.12, lid=0.2 + 0.25 * down * (1 - bars),
                        dim=0.2), 0.32)
            LIVES["weaver"].apply(p, t, 0.4)
            at_head(cv, WEAVER, p, 360, 560, 3.0, t)
            # the straight lines become bars
            for k in range(8):
                x = -40 + k * 110 + 20 * math.sin(t * 0.3)
                h = H * bars
                cv.drawRect(skia.Rect.MakeLTRB(x, 0, x + 34, h), paint((10, 10, 24), 0.55, blur=6))
        S.grade(cv, (60, 70, 130), 0.22 + 0.15 * bars, "multiply")
        S.vignette(cv, 0.4 + 0.3 * bars)

    def seed(cv, t, lt):
        fallu = ramp(t, n14b - 0.6, n14b + 1.4, ease_out)
        landed = ramp(t, n14b + 1.2, n14b + 1.6)
        miracle = ramp(t, n14c - 0.3, n14c + 3.2)
        to_air = ramp(t, n14c + 2.4, n14c + 4.2)
        cx, cy = 360, 930
        with Cam(cv, 360, lerp(700, 760, smooth(lt / 8)), 1.0 + 0.05 * lt / 8, t=t):
            S.sky(cv, [(6, 8, 26), (26, 28, 62)], None, 0, 470)
            S.stars(cv, t, 1.0, n=140, y1=440)
            S.house_row(cv, 470, 220, n=4, x0=-120, x1=W + 120, dim=0.82, seed=9, lights=1.0)
            S.paving(cv, (360, 330), 470, 900, S.GROUND_IN, dim=0.82, spacing=150)
            # the crack between two straight stones
            crack = [(cx - 70, cy - 6), (cx - 30, cy + 4), (cx, cy - 2), (cx + 34, cy + 6), (cx + 80, cy - 4)]
            cv.drawPath(path(crack, closed=False), paint((12, 12, 22), 0.9, stroke=6))
            # the seed of light drifting down
            sx = lerp(520, cx, fallu) + 30 * math.sin(fallu * 5) * (1 - fallu)
            sy = lerp(-80, cy - 6, fallu)
            if landed < 1:
                for k in range(8):  # sparkle trail
                    u = clamp(fallu - k * 0.03)
                    tx = lerp(520, cx, u) + 30 * math.sin(u * 5) * (1 - u)
                    ty = lerp(-80, cy - 6, u)
                    glow(cv, tx, ty, 14, (255, 220, 160), 0.5 * (1 - k / 8) * (1 - landed))
            pulse = 1 + 0.25 * math.sin(t * 3)
            glow(cv, sx, sy, (40 + 40 * landed) * pulse, (255, 214, 150), 0.9)
            glow(cv, sx, sy, 8, (255, 250, 230), 1.0)
            if miracle > 0:
                # warm light seeps along the straight joints and bends them
                glow(cv, cx, cy - 40, 120 + 420 * miracle, (255, 196, 120), 0.4 * miracle, blend="screen")
                for k in range(-3, 4):
                    yy = cy + k * 22
                    bend = skia.Path()
                    bend.moveTo(cx - 260 * miracle, yy)
                    bend.quadTo(cx, yy - 30 * miracle * (1 - abs(k) / 4), cx + 260 * miracle, yy)
                    cv.drawPath(bend, paint((255, 214, 150), 0.3 * miracle * (1 - abs(k) / 4), stroke=2.5,
                                            blend="plus"))
                S.light_rays(cv, cx, cy - 20, miracle * 0.9, t, n=9, L=900, spread=1.4)
                S.sprout(cv, cx, cy, miracle, t, a=1.0, s=2.4)
        S.vignette(cv, 0.55)
        if to_air > 0:
            cv.saveLayerAlpha(None, int(255 * to_air))
            S.aerial_view(cv, t, zoom=lerp(1.9, 1.15, ramp(t, n14c + 2.4, end)), focus=(0, 0), night=1.0,
                          lights=1.0, glow_seed=0.4 + 0.6 * ramp(t, n14c + 3, end))
            S.vignette(cv, 0.5)
            cv.restore()
        title_text(cv, "THE FIRST VILLAGE", 230, window(t, n14c + 3.4, end + 1, 1.2, 0.1), 46)

    run(cv, t, [(v2, weaver_loom), (look, two_shot), (p1, potter), (n14, weaver_cu), (n14b - 0.6, seed)])


SCENES = [("opening", opening), ("village", village), ("fear", fear), ("speech", speech), ("elder2", elder2),
          ("expel", expel), ("alone", alone), ("presence", presence), ("village2", village2)]


def draw_frame(cv, t):
    marks = TL.marks
    cur = SCENES[0][1]
    for name, fn in SCENES:
        if t >= marks[name]:
            cur = fn
    cur(cv, t)
