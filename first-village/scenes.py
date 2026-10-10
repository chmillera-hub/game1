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
def _ik(hip, ankle, L1, L2, fwd=1):
    """Two-bone IK: knee position bending forward (+x when fwd=1)."""
    dx, dy = ankle[0] - hip[0], ankle[1] - hip[1]
    d = min(math.hypot(dx, dy), L1 + L2 - 1)
    a = math.atan2(dy, dx)
    b = math.acos(clamp((L1 * L1 + d * d - L2 * L2) / (2 * L1 * d), -1, 1))
    k = a - b * fwd
    return hip[0] + math.cos(k) * L1, hip[1] + math.sin(k) * L1


def _limb(cv, p0, p1, w0, w1, col):
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0]) + math.pi / 2
    cx, cy = math.cos(ang), math.sin(ang)
    pth = path([(p0[0] + cx * w0 / 2, p0[1] + cy * w0 / 2), (p1[0] + cx * w1 / 2, p1[1] + cy * w1 / 2),
                (p1[0] - cx * w1 / 2, p1[1] - cy * w1 / 2), (p0[0] - cx * w0 / 2, p0[1] - cy * w0 / 2)])
    cv.drawPath(pth, paint(col))
    cv.drawCircle(*p1, w1 / 2, paint(col))


def walk_feet(cv, t, t0):
    """Walking in profile: knee-length tunic, real knees and calves, sandals on hard-cracked earth."""
    ground = 875
    S.sky(cv, [(120, 84, 120), (236, 150, 110), (252, 190, 130)], [0, 0.6, 1], 0, ground - 150)
    with Blur(cv, 5):
        S.dune_layer(cv, ground - 170, 40, (214, 150, 104), 3, bottom=ground + 40)
        S.dune_layer(cv, ground - 70, 50, (200, 136, 92), 8, bottom=ground + 40)
    v = 230
    cv.save()
    cv.translate(-((t * v) % 140), 0)
    S.cracked_ground(cv, (-300, ground - 12, W + 300, H + 50), (182, 128, 84), seed=12, cell=140, line_a=0.6)
    cv.restore()
    T = 1.2
    stride = 300
    skin, sole, strap = MOSES.skin, (96, 62, 38), (70, 44, 28)
    bob = 10 * abs(math.cos(t / T * 2 * math.pi))
    hip = (350, -30 + bob)
    L1, L2 = 468, 455
    legs = []
    for i in range(2):
        ph = (t / T + i * 0.5) % 1.0
        if ph < 0.6:
            u = ph / 0.6
            fx = 360 + stride / 2 - u * stride
            lift, rot = 0.0, 0.0
        else:
            u = (ph - 0.6) / 0.4
            fx = 360 - stride / 2 + smooth(u) * stride
            lift = math.sin(math.pi * u) * 60
            rot = -12 * math.sin(math.pi * u)
        legs.append((fx, ground - lift, rot, i, ph))
    # far leg first (darker), then near leg
    legs.sort(key=lambda L: L[3])
    knees = []
    for fx, fy, rot, i, ph in legs:
        dk = 0.78 if i == 0 else 1.0
        ankle = (fx - 38, fy - 52)
        knee = _ik(hip, ankle, L1, L2, 1)
        knees.append(knee)
        col = shade(skin, dk)
        _limb(cv, hip, knee, 150, 92, shade(skin, 0.92 * dk))      # thigh (mostly under the tunic)
        _limb(cv, knee, ankle, 88, 50, col)                        # shin
        # calf muscle and knee cap
        mid = (lerp(knee[0], ankle[0], 0.3) - 26, lerp(knee[1], ankle[1], 0.3))
        cv.drawOval(oval(mid[0], mid[1], 34, 90), paint(col))
        cv.drawOval(oval(knee[0] + 16, knee[1] + 6, 30, 38), paint(shade(col, 1.07)))
        cv.save()
        cv.translate(fx, fy)
        cv.rotate(rot)
        cv.drawRoundRect(skia.Rect.MakeLTRB(-78, -14, 88, 0), 8, 8, paint(shade(sole, dk)))
        foot = skia.Path()
        foot.moveTo(-72, -14)
        foot.cubicTo(-80, -64, -50, -88, -26, -84)
        foot.cubicTo(8, -64, 44, -44, 82, -28)
        foot.quadTo(92, -18, 84, -14)
        foot.close()
        cv.drawPath(foot, paint(col))
        for sx in (-40, 4, 42):
            cv.drawLine(sx - 4, -14, sx + 6, -64 + abs(sx) * 0.4, paint(shade(strap, dk), stroke=8))
        cv.drawLine(-60, -60, -20, -78, paint(shade(strap, dk), stroke=8))
        cv.restore()
        if ph < 0.25:
            u = ph / 0.25
            for k in range(7):
                ang = math.pi + (k / 6) * math.pi
                d = 30 + 70 * u
                cv.drawCircle(fx + math.cos(ang) * d * 1.4, ground - 6 + math.sin(ang) * d * 0.4, 8 + 14 * u,
                              paint((230, 196, 150), 0.35 * (1 - u), blur=6))
    # knee-length tunic over the hips, its hem swinging with the stride
    swing = 26 * math.sin(t / T * 2 * math.pi)
    hem_y = 265 + bob
    front = max(k[0] for k in knees) + 40
    back = min(k[0] for k in knees) - 50
    tunic = skia.Path()
    tunic.moveTo(225, -60)
    tunic.lineTo(480, -60)
    tunic.cubicTo(500, 80, front + 20, 200, front + 10 + swing * 0.3, hem_y - 10)
    tunic.quadTo(360, hem_y + 34, back - 10 - swing * 0.3, hem_y + 6)
    tunic.cubicTo(back - 10, 220, 200, 90, 225, -60)
    tunic.close()
    cv.drawPath(tunic, paint(shader=lin((200, 0), (520, 0), [(126, 104, 78), (180, 154, 116), (150, 126, 94)])))
    cv.save()
    cv.clipPath(tunic, skia.ClipOp.kIntersect, True)
    for k in range(6):
        x0 = 250 + k * 45
        cv.drawLine(x0, -60, x0 + (k - 2.5) * 14 + swing * 0.4, hem_y + 30, paint((112, 90, 66), 0.5, stroke=5))
    cv.drawRect(skia.Rect.MakeLTRB(150, -60, 560, 10), paint((124, 70, 44)))   # sash
    cv.restore()
    cv.drawPath(tunic, paint((110, 80, 54), stroke=6))
    # the cloak trailing behind
    cloak = skia.Path()
    cloak.moveTo(150, -60)
    cloak.cubicTo(110, 80, 70 - swing * 0.4, 220, 40 - swing * 0.6, hem_y + 80)
    cloak.quadTo(110, hem_y + 60, 175 - swing * 0.3, hem_y + 30)
    cloak.cubicTo(205, 200, 220, 80, 240, -60)
    cloak.close()
    cv.drawPath(cloak, paint(shader=lin((40, 0), (240, 0), [(96, 66, 42), (124, 88, 58)])))
    cv.save()
    cv.clipPath(cloak, skia.ClipOp.kIntersect, True)
    for k in range(4):
        cv.drawLine(170 - k * 30, -60, 120 - k * 34 - swing * 0.4, hem_y + 80, paint((84, 58, 36), 0.6, stroke=5))
    cv.restore()
    S.dust(cv, t, 30, 0.35, wind=-140, y0=500, y1=900)


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
            glow(cv, 360, 250, 300, (255, 210, 150), 0.35 * mem, blend="screen")
            S.light_rays(cv, 360, 210, mem * 0.3, t, n=11, L=700, spread=2.2, base=math.pi / 2)
            S.burning_bush(cv, 360, 330, 0.95, t, a=0.92 * mem)
            closed = window(t, g0 - 0.25, n2 + 0.5, 0.35, 0.4)
            hand = window(t, g0 + 0.1, n2 + 0.8, 0.6, 0.6)
            p = mk(ember=1.0, lid=closed * 0.97, smile=0.35 * closed, staff=True, arm_l=(12, -36, 1, 1),
                   arm_r=arm_mix(REST, MOUTH, hand), shadow=0, hand_r="open", hand_rot_r=-15 * hand)
            life.apply(p, t)
            p["pitch"] = -0.12 * closed
            p["tint"] = ((255, 176, 110), 0.12)
            at_head(cv, MOSES, p, 360, 560, 2.05, t)
            S.dust(cv, t, 40, 0.4, wind=-90, y0=500, y1=1280, size=1.6)

    def ridge_back(cv, t, lt):
        with Cam(cv, 360, 640, 1.0 + 0.02 * lt, t=t):
            S.desert(cv, t, horizon=640, sun=(560, 520), warm=1.0, dunes=False)
            S.dune_layer(cv, 690, 30, (206, 140, 98), 5)
            cv.save()
            cv.clipRect(skia.Rect.MakeLTRB(-200, 644, W + 200, 1000))
            S.village3d(cv, S.Cam3((-40, 30, -170), 0.0, 900, cy=640), t)
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
        cam = S.Cam3.look_at((lerp(-22, -4, u), lerp(78, 54, u), lerp(-112, -40, u)), (0, 0, lerp(70, 64, u)), 900,
                             cy=lerp(700, 660, u))
        S.aerial_view(cv, t, cam)
        S.grade(cv, (140, 150, 180), 0.12)

    def wide(cv, t, lt):
        z = 1.0 + 0.03 * lt

        def elder():
            # addressing the crowd: arms bent and held out from the body, hands open toward them
            gl = 0.5 + 0.5 * math.sin(t * 2.1)
            gr = 0.5 + 0.5 * math.sin(t * 1.7 + 1.3)
            p = elder_pose(t, open=fake_talk(t, 3, 0.5), lid=0.25, gx=0.3 * math.sin(t * 0.7),
                           arm_l=(38 + 14 * gl, 78 + 18 * gl, 1, 0.85), arm_r=(38 + 14 * gr, 78 + 18 * gr, 1, 0.85),
                           hand_l="open", hand_r="open", hand_rot_l=0, hand_rot_r=0)
            p["turn"] += 0.15 * math.sin(t * 0.7)
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

    cough = TL.s("cough")
    coughs = (cough + 0.25, cough + 0.67)

    def mcu(cv, t, lt):
        with Cam(cv, 360, 640, 1.0 + 0.01 * lt, t=t):
            moses_bg(cv, t)
            up = ramp(t, m1 - 0.3, m1 + 0.6)
            hands = ramp(t, m1 + 0.3, m1 + 1.2)
            # a cough to clear the throat before he speaks: fist to mouth, eyes squeezed, a jolt each time
            fist = window(t, cough - 0.05, m0 - 0.15, 0.22, 0.3)
            jolt = sum(max(0.0, 1 - abs(t - c - 0.04) / 0.12) for c in coughs)
            p = mk(ember=0.6, worry=0.6 - 0.3 * up, gy=0.6 * (1 - up) - 0.15 * up, pitch=0.25 * (1 - up) + 0.25 * jolt,
                   arm_l=arm_mix(REST, OPEN, hands), arm_r=arm_mix(arm_mix(REST, OPEN, hands), MOUTH, fist),
                   hand_r="fist" if fist > 0.3 else "open", hand_rot_l=40 * hands, hand_rot_r=-40 * hands * (1 - fist))
            life.apply(p, t)
            p["lid"] = max(p["lid"], 0.85 * min(1, jolt * 1.6))
            p["furrow"] = 0.5 * min(1, jolt * 1.6)
            p["sigh"] = -0.8 * jolt
            speak(p, ("moses",), t, 1.0, 1.2)
            at_head(cv, MOSES, p, 360, 500 + 10 * jolt, 2.2, t)
        S.grade(cv, (255, 200, 150), 0.08)

    def elder_watch(cv, t, lt):
        """Cutaway: the Elder watching Moses, unmoved, measuring him."""
        with Cam(cv, 360, 640, 1.03 + 0.01 * lt, t=t):
            with Blur(cv, 6):
                cv.save()
                cv.translate(360, 640)
                cv.scale(2.4, 2.4)
                cv.translate(-390, -540)
                plaza(cv, t)
                cv.restore()
            p = elder_pose(t, gx=-0.75, gy=0.05, turn=-0.22, lid=0.38, brow_l=0.35, brow_r=-0.1, press=0.6,
                           anger=0.15, sneer=0.15, tilt=-3)
            at_head(cv, ELDER, p, 380, 540, 2.4, t)
        S.grade(cv, (150, 160, 180), 0.15)

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
        """The cracked vessel is a picture he holds up in words: it hangs, glowing and imaginary, above him."""
        crack = ramp(t, m4 + 0.6, m4 + 2.6)
        light = ramp(t, light_on, light_on + 1.4)
        appear = ramp(t, m4 - 0.2, m4 + 1.0)
        point = window(t, m4 + 0.1, TL.cap("m4", 1) + 0.6, 0.5, 0.6) + ramp(t, m5 - 0.2, m5 + 0.5)
        point = clamp(point)
        with Cam(cv, 360, 640, 1.0 + 0.02 * lt + 0.06 * light, t=t):
            moses_bg(cv, t, 1.9, 360, 540, 6, warm=0.6 * light)
            vy = 300 + 8 * math.sin(t * 1.3)
            # imagined: a soft aura, a faint ring, drifting sparks
            glow(cv, 360, vy - 10, 230 + 40 * light, (255, 226, 170), (0.35 + 0.35 * light) * appear, blend="screen")
            ring = skia.Path()
            ring.addOval(oval(360, vy - 10, 175, 175))
            cv.drawPath(ring, paint((255, 236, 200), 0.35 * appear * (1 - 0.5 * light), stroke=2.5, blur=3))
            for k in range(14):
                ang = t * 0.4 + k * 0.45
                rr = 150 + 30 * math.sin(t + k)
                cv.drawCircle(360 + math.cos(ang) * rr, vy - 10 + math.sin(ang) * rr, 2.2,
                              paint((255, 240, 210), 0.6 * appear))
            S.vessel(cv, 360, vy + 40, 0.95, t, crack=crack, light=light, a=0.82 * appear)
            p = mk(ember=0.6 + 0.4 * light, worry=0.4 * (1 - light), brow=0.2 + 0.2 * light, smile=0.1 * light,
                   gy=-0.7 * point, gx=0.2 * point, pitch=-0.15 * point,
                   arm_r=arm_mix(REST, (150, 25, 1, 1), point), hand_r="point",
                   arm_l=arm_mix(REST, OPEN, 0.6), hand_rot_l=40)
            life.apply(p, t)
            speak(p, ("moses",), t, 0.95, 1.0)
            at_head(cv, MOSES, p, 360, 700, 1.75, t)
        S.grade(cv, (255, 200, 150), 0.08 + 0.15 * light)

    def ecu(cv, t, lt):
        """Not near tears: dead serious, telling them straight what he believes."""
        with Cam(cv, 360, 640, 1.0 + 0.01 * lt, t=t):
            moses_bg(cv, t, 3.4, 360, 520, 11, warm=0.25)
            p = mk(ember=0.8, anger=0.12, furrow=0.3, lid=0.14, press=0.25, gx=0.0, gy=0.0, pitch=0.06)
            life.apply(p, t, 0.35)
            speak(p, ("moses",), t, 0.95, 0.9)
            at_head(cv, MOSES, p, 360, 520, 4.0, t)
        S.grade(cv, (255, 200, 150), 0.08)

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

    run(cv, t, [(TL.m("speech"), mcu), (TL.cap("m1", 1), elder_watch), (m2, mcu), (TL.cap("m2", 1), listeners),
                (m3, cu_throat), (m4, vessel_shot),
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
    p = mk(kneel=1.0, bow=0.6, pitch=0.35, dirt=0.85, lid=0.42, worry=0.45, furrow=0.35, smile=-0.12, ember=0.1,
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
            p = kneel_pose(t, dim=night * 0.45)
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
            # deep in thought: eyes on the ground a little way off, turning it over
            p = kneel_pose(t, dim=night * 0.35, bow=0.2, pitch=0.25, lid=0.38, gx=-0.35, gy=0.45, turn=-0.08)
            life.apply(p, t, 0.3)
            p["press"] = 0.3
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
            p = kneel_pose(t, dim=night * 0.35, ember=em)
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
            p = kneel_pose(t, dim=night * 0.32, bow=0.25 * closed, pitch=0.4 * closed - 0.25 * up,
                           lid=0.5 * closed + 0.12 * up, worry=0.45 + 0.25 * up, furrow=0.45 * closed,
                           gy=0.5 * closed - 0.8 * up, gx=-0.2 * closed, smile=-0.15)
            life.apply(p, t, 0.3)
            speak(p, ("moses_w",), t, 0.85, 0.5)
            at_head(cv, MOSES, p, 360, 560, 3.4, t)
        S.grade(cv, (90, 100, 150), 0.18, "multiply")

    def tiny(cv, t, lt):
        night = dusk_of(t)
        swirl = ramp(t, n9 + 0.4, n9b + 0.5)
        with Cam(cv, 360, 560, 0.62, t=t):
            S.wall_outside(cv, t, gate=0, night=night)
            p = kneel_pose(t, dim=night * 0.5)
            fig(cv, MOSES, p, 380, 1000, 0.5, t)
        # a dust devil passing close to the lens on the right, half out of frame, away from him
        cx = lerp(980, 640, smooth(swirl * 1.6)) + 40 * math.sin(t * 0.9)
        fade = math.sin(math.pi * swirl)
        for k in range(70):
            h = k / 70
            ang = t * 5 + k * 0.7
            r = 40 + 210 * h
            cv.drawCircle(cx + math.cos(ang) * r, 1290 - h * 1100 + math.sin(ang) * r * 0.18, 26 + 50 * h,
                          paint((196, 158, 120), 0.2 * fade * (1 - 0.4 * h), blur=22))
        S.grade(cv, (90, 100, 150), 0.25, "multiply")
        S.vignette(cv, 0.55)

    def bowed(cv, t, lt):
        with Cam(cv, 360, 760, 1.12 + 0.05 * lt / 5, t=t):
            night = outside(t)
            p = kneel_pose(t, dim=night * 0.5, bow=1.0, pitch=0.5, lid=0.7, shake=0.5)
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
    g1b_e, g2_e = TL.e("g1b"), TL.e("g2")
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
                           lid=0.7 - 0.25 * ramp(t, warmth + 1.5, warmth + 3), shake=0.5 * (1 - warm),
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
            p = kneel_pose(t, dim=0.6, bow=0.3, pitch=0.1, lid=0.4)
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
                           open=0.18 * hear * (1 - smile), smile=-0.2 + 0.55 * smile, glowhand=0.55,
                           wet=0.6 * ramp(t, g1b_e, g1b_e + 0.8) + 0.4 * ramp(t, g2_e, g2_e + 0.6),
                           drops=[(1, (t - g1b_e - 0.5) / 2.6), (-1, (t - g2_e - 0.4) / 2.4),
                                  (1, (t - g2_e - 1.1) / 2.4)])
            p["tint"] = ((255, 190, 130), 0.1)
            life.apply(p, t, 0.3)
            if smile:
                p["tilt"] += 1.0 * math.sin(t * 8) * smile * (1 - close)
            at_head(cv, MOSES, p, 360, 600, 3.6, t)
        S.vignette(cv, 0.45)

    def two(cv, t, lt):
        """Not a figure kneeling beside him: the presence all around him, vast in the stars, bending close."""
        form = ramp(t, n12 + 0.4, n12 + 4.2)
        sg = sighp(t)
        with Cam(cv, 360, 700, 1.0 + 0.04 * lt / 10, t=t):
            fill(cv, (8, 10, 28))
            S.sky(cv, [(6, 8, 26), (18, 20, 56), (44, 40, 80)], [0, 0.6, 1], 0, 960)
            S.stars(cv, t, 1.0, cx=360, cy=260, rot=(t - n10c) * 2.2, n=300, x0=-500, x1=1200, y0=-600, y1=1000)
            S.divine_figure(cv, 425, 960, 0.86, t, a=form, sigh=max(0, sg))
            cv.drawRect(skia.Rect.MakeLTRB(-400, 960, W + 400, H + 400), paint((30, 28, 46)))
            cv.drawRect(skia.Rect.MakeLTRB(-400, 940, W + 400, 962), paint((40, 38, 60)))
            # a soft wave of light on the out-breath
            if t > sigh0 + 1.1:
                u = clamp((t - sigh0 - 1.1) / 2.4)
                ring = skia.Path()
                ring.addOval(oval(260, 1060, 120 + 500 * u, 40 + 160 * u))
                cv.drawPath(ring, paint((255, 220, 170), 0.35 * (1 - u), stroke=10, blur=8, blend="plus"))
            p = kneel_pose(t, dim=0.35, bow=0.15 - 0.1 * sg, pitch=0.1,
                           lid=lerp(0.35, 0.95, ramp(t, sigh0 + 0.9, sigh0 + 1.6)), worry=0.3, furrow=0.0,
                           smile=0.08, glowhand=0.7, sigh=sg, breath=1.0)
            p["tint"] = ((200, 190, 255), 0.15)
            life.apply(p, t, 0.2, blinks=t < sigh0)
            fig(cv, MOSES, p, 260, 1100, 0.95, t)
            # the great hand resting over his shoulders, in front of him
            glow(cv, 425 - 205 * 0.86, 960 - 130 * 0.86, 110 * (1 + 0.2 * max(0, sg)), (190, 205, 255), 0.3 * form,
                 blend="screen")
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

    def exile_dawn(cv, t, lt):
        """Dawn outside the walls. Moses walks away into the sunrise; his footprints lead back to where he
        knelt, and from the place his tears fell, something green is pushing up."""
        hz = 470
        walk_u = ramp(t, n14b - 0.6, end, lambda u: u)
        glint = ramp(t, n14b - 0.2, n14b + 1.2)
        grow = ramp(t, n14c - 0.3, n14c + 3.4)
        push = smooth(ramp(t, n14b, n14c + 1.5)) * (1 - smooth(ramp(t, n14c + 2.0, end - 0.5)))
        spot = (330, 968)

        def gy(z):                  # ground plane: depth z -> screen y
            return hz + 500 / z

        def gx(z):                  # his path curves gently away toward the sun
            return 330 + 90 * (1 - 1 / z) + 12 * math.sin(z * 0.9)

        zm = lerp(4.2, 9.5, walk_u)
        with Cam(cv, lerp(360, spot[0], 0.5 * push), lerp(640, 820, push), 1.0 + 0.22 * push, t=t):
            S.sky(cv, [(36, 44, 98), (150, 104, 132), (250, 170, 120), (255, 214, 160)], [0, 0.5, 0.85, 1], 0,
                  hz + 4)
            S.stars(cv, t, 0.35, n=80, y1=200)
            sx = 520
            glow(cv, sx, hz, 420, (255, 190, 120), 0.55)
            cv.drawCircle(sx, hz + 18, 42, paint((255, 232, 190)))
            S.mountains(cv, hz + 2, (150, 104, 120), seed=5, h=34)
            ground = (170, 124, 90)
            cv.drawRect(skia.Rect.MakeLTRB(-400, hz, W + 400, H + 600),
                        paint(shader=lin((0, hz), (0, 1100), [(214, 160, 120), ground, shade(ground, 0.8)])))
            cv.drawRect(skia.Rect.MakeLTRB(-400, hz, W + 400, hz + 70),
                        paint(shader=lin((0, hz), (0, hz + 70), [((255, 200, 150), 0.5), ((255, 200, 150), 0.0)])))
            for k in range(140):   # pebbles in perspective
                z = 1 / (0.12 + 0.9 * hashf(k, 61))
                x = (hashf(k, 62) - 0.5) * 2200 / z + 360
                r = 10 / z
                cv.drawOval(oval(x, gy(z), r, r * 0.55), paint(shade(ground, 0.75), 0.7))
            # the long morning shadow of the wall behind us
            cv.drawRect(skia.Rect.MakeLTRB(-400, 1000, W + 400, H + 600),
                        paint(shader=lin((0, 1000), (0, 1200), [((40, 30, 40), 0.0), ((40, 30, 40), 0.35)])))
            # where he knelt: knee prints, hand prints, and dark spots where tears fell
            for dx in (-38, 38):
                cv.drawOval(oval(spot[0] + dx, spot[1] + 30, 34, 13), paint(shade(ground, 0.68), 0.85))
            for dx in (-120, 125):
                cv.drawOval(oval(spot[0] + dx, spot[1] + 8, 24, 9), paint(shade(ground, 0.7), 0.7))
            for k, (dx, dy) in enumerate(((0, 0), (-16, 6), (14, -4))):
                cv.drawOval(oval(spot[0] + dx, spot[1] + dy, 7 - k, 3.5), paint(shade(ground, 0.55), 0.9))
            # his footprints leading away to him
            z = 1.16
            k = 0
            while z < zm - 0.15:
                side = -1 if k % 2 else 1
                x = gx(z) + side * 22 / z
                y = gy(z)
                fw, fl = 20 / z, 44 / z          # sandal prints pressed into the dust
                cv.save()
                cv.translate(x, y)
                cv.drawOval(oval(0, 0, fw, fl * 0.4), paint(shade(ground, 0.62), 0.9))
                cv.drawOval(oval(0, fl * 0.04, fw * 0.7, fl * 0.26), paint(shade(ground, 0.8), 0.9))
                cv.drawOval(oval(-fw * 0.3, -fl * 0.4, fw * 0.32, fl * 0.12), paint(shade(ground, 0.62), 0.9))
                cv.drawOval(oval(fw * 0.25, -fl * 0.38, fw * 0.3, fl * 0.11), paint(shade(ground, 0.62), 0.9))
                cv.restore()
                z += 0.38 * (1 + 0.15 * z)
                k += 1
            # Moses, small, walking into the sunrise
            ms = 0.95 / zm
            bob = abs(math.sin(t * 3.3)) * 6 * ms
            S.draw_back(cv, MOSES, gx(zm), gy(zm) - bob, ms, t, dim=0.25)
            cv.drawLine(gx(zm) - 90 * ms, gy(zm) - 560 * ms - bob, gx(zm) - 76 * ms, gy(zm) - bob,
                        paint((70, 50, 40), stroke=max(1.2, 10 * ms)))
            glow(cv, gx(zm), gy(zm) - 250 * ms, 120 * ms + 30, (255, 200, 140), 0.25)
            # a tear's glint becomes a seed, the seed a sprout
            glow(cv, spot[0], spot[1] - 2, 18 + 30 * glint, (255, 226, 160), 0.7 * glint * (1 - 0.4 * grow))
            if grow > 0:
                S.light_rays(cv, spot[0], spot[1] - 10, 0.45 * grow, t, n=9, L=700, spread=1.3)
                glow(cv, spot[0], spot[1] - 30, 80 + 220 * grow, (255, 205, 130), 0.4 * grow, blend="screen")
                S.sprout(cv, spot[0], spot[1], grow, t, a=1.0, s=1.5)
        S.vignette(cv, 0.4)
        title_text(cv, "THE FIRST VILLAGE", 210, window(t, n14c + 3.2, end + 1, 1.2, 0.1), 46)

    run(cv, t, [(v2, weaver_loom), (look, two_shot), (p1, potter), (n14, weaver_cu), (n14b - 0.6, exile_dawn)])


SCENES = [("opening", opening), ("village", village), ("fear", fear), ("speech", speech), ("elder2", elder2),
          ("expel", expel), ("alone", alone), ("presence", presence), ("village2", village2)]


def draw_frame(cv, t):
    marks = TL.marks
    cur = SCENES[0][1]
    for name, fn in SCENES:
        if t >= marks[name]:
            cur = fn
    cur(cv, t)
