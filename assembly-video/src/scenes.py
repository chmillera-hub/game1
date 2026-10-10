"""All scene drawing for 'The Assembly'."""
import json, math
import skia
from gfx import *
from chars import P_
from chars2 import *

TL = json.load(open("timeline.json"))
M = TL["markers"]
LIPS = json.load(open("lipsync.json"))
LINES = {l["id"]: l for l in TL["lines"]}
SCENES = TL["scenes"]
BY_SPK = {}
for _l in TL["lines"]:
    BY_SPK.setdefault(_l["spk"], []).append(_l["id"])


# ======================================================================= timing helpers

def talk(lid, t, gain=1.0):
    l = LINES.get(lid)
    if not l or t < l["start"] or t > l["start"] + l["dur"]:
        return 0.0
    e = LIPS[lid]
    i = (t - l["start"]) * 24
    i0 = int(i)
    a = e[min(i0, len(e) - 1)]
    b = e[min(i0 + 1, len(e) - 1)]
    return clamp((a + (b - a) * (i - i0)) * 0.85 * gain, 0, 1.0)


def mouth(spk, t, gain=1.0):
    return max(talk(l, t, gain) for l in BY_SPK.get(spk, []))


def speaking(lid, t):
    l = LINES[lid]
    return l["start"] <= t <= l["start"] + l["dur"]


def L0(lid):
    return M[lid]


def L1(lid):
    return M[lid + "_end"]


def kf(t, keys):
    """smooth keyframes [(t, value or tuple), ...]; equal times = hard cut"""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            u = smooth((t - t0) / (t1 - t0)) if t1 > t0 else 1.0
            if isinstance(v0, tuple):
                return tuple(a + (b - a) * u for a, b in zip(v0, v1))
            return v0 + (v1 - v0) * u
    return keys[-1][1]


def pose_at(t, keys, dur=0.28):
    cur, prev, tc = keys[0][1], keys[0][1], -1e9
    for tk, p in keys:
        if t >= tk:
            prev, cur, tc = cur, p, tk
        else:
            break
    u = clamp((t - tc) / dur)
    if u >= 1 or prev == cur:
        return cur, None
    return prev, (cur, smooth(u))


def FP(t, seed, mo=0.0, look=None, period=3.4, noblink=False, **kw):
    """face params with blinking + small saccades"""
    lid = kw.pop("lid", 1.0)
    bl = 1.0 if noblink else blink(t, seed, period)
    sx, sy = saccade(t, seed, 1.7, 0.22)
    d = dict(t=t, lid=lid * bl if lid > 0.1 else lid, px=sx, py=sy * 0.6, mouth_open=mo)
    if look is not None:
        d["px"], d["py"] = look[0] + 0.12 * sx, look[1] + 0.1 * sy
    d.update(kw)
    return P_(**d)


# ======================================================================= camera / drawing helpers

def cam(c, zoom=1.0, cx=W / 2, cy=H / 2, rot=0.0, shake=0.0, t=0.0):
    c.translate(W / 2 + shake * 9 * vnoise(t * 30, 1), H / 2 + shake * 9 * vnoise(t * 30, 2))
    c.rotate(rot + shake * 0.8 * vnoise(t * 25, 3))
    c.scale(zoom, zoom)
    c.translate(-cx, -cy)


def at(c, x, y, s=1.0, rot=0.0):
    c.save()
    c.translate(x, y)
    if rot:
        c.rotate(rot)
    c.scale(s, s)


def put(c, x, y, s, fn, *a, rot=0.0, **kw):
    at(c, x, y, s, rot)
    fn(c, *a, **kw)
    c.restore()


def flash(c, t, t0, dur=0.3, color="#ffffff", amax=0.85):
    if t0 <= t <= t0 + dur:
        c.drawRect(skia.Rect.MakeWH(W, H), fill(color, amax * (1 - (t - t0) / dur)))


BIG = skia.Rect.MakeLTRB(-800, -800, W + 800, H + 800)


def desat_begin(c, amt, warm=0.0):
    s = 1 - amt
    lr, lg, lb = 0.2126, 0.7152, 0.0722
    m = [lr * (1 - s) + s, lg * (1 - s), lb * (1 - s), 0, warm * 0.04,
         lr * (1 - s), lg * (1 - s) + s, lb * (1 - s), 0, 0,
         lr * (1 - s), lg * (1 - s), lb * (1 - s) + s, 0, -warm * 0.03,
         0, 0, 0, 1, 0]
    c.saveLayer(None, skia.Paint(ColorFilter=skia.ColorFilters.Matrix(m)))


def sparkle_star(c, x, y, r, a=1.0, color="#ffffff"):
    p = skia.Path()
    p.moveTo(x, y - r)
    p.quadTo(x, y, x + r, y)
    p.quadTo(x, y, x, y + r)
    p.quadTo(x, y, x - r, y)
    p.quadTo(x, y, x, y - r)
    c.drawPath(p, fill(color, a))


def twinkles(c, t, x, y, spread, n=5, seed=0, color="#fff6b0", size=16):
    for i in range(n):
        ph = (t * 1.3 + hash1(i * 5 + seed) * 2) % 1.0
        a = math.sin(math.pi * ph)
        xx = x + spread * hash1(i * 11 + seed)
        yy = y + spread * 0.6 * hash1(i * 23 + seed + 1)
        sparkle_star(c, xx, yy, size * (0.5 + a), a, color)


def bubble_text(c, s, x, y, size=40, color="#ffffff", t=0.0, t0=0.0, a=1.0, rot=0.0):
    u = ease_out_back(clamp((t - t0) / 0.25), 2)
    if u <= 0:
        return
    at(c, x, y, u, rot)
    text(c, s, 0, 0, "bangers", size, color, outline=OUT, ow=8, a=a)
    c.restore()


def confetti(c, t, t0, n=70, seed=3):
    if t < t0:
        return
    lt = t - t0
    cols = ["#ff5a5f", "#ffd23f", "#3a86ff", "#06d6a0", "#8338ec", "#fb5607"]
    for i in range(n):
        x0 = (hash1(i * 7 + seed) * 0.5 + 0.5) * (W + 200) - 100
        sp = 160 + 140 * (hash1(i * 3 + seed) * 0.5 + 0.5)
        y = -40 - 400 * (hash1(i * 13 + seed) * 0.5 + 0.5) + sp * lt
        if y > H + 40:
            continue
        x = x0 + 30 * math.sin(lt * 3 + i)
        at(c, x, y, 1.0, lt * 200 + i * 40)
        c.drawRect(skia.Rect.MakeXYWH(-7, -4, 14, 8 * abs(math.cos(lt * 6 + i))), fill(cols[i % 6]))
        c.restore()


# ======================================================================= backgrounds

def bg_office(c, t, night=False):
    c.drawRect(BIG, lin_grad(0, 0, 0, H, ["#efe2c8", "#e2cfae"]))
    c.drawRect(skia.Rect.MakeLTRB(-800, 820, W + 800, 1000), fill("#c79a6b"))
    c.drawPath(poly([(-800, 820), (W + 800, 820)], False), stroke("#8a6038", 6))
    c.drawRect(skia.Rect.MakeLTRB(-800, 1000, W + 800, H + 800), lin_grad(0, 1000, 0, H, ["#7a5a3e", "#4e3826"]))
    # window
    fs(c, rrect(30, 150, 190, 250, 8), "#1a2a55" if night else "#9fd3ff", 7)
    if night:
        c.drawCircle(160, 210, 24, fill("#fff3c4"))
        c.drawCircle(150, 204, 22, fill("#1a2a55"))
    else:
        c.drawPath(cloud(110, 230, 90, 40, 6, t, 2), fill("#ffffff", 0.9))
    for k in range(9):
        c.drawPath(poly([(36, 165 + k * 26), (214, 165 + k * 26)], False), stroke("#f4f1de", 5, 0.8))
    # poster: a heart flexing
    at(c, 360, 255, 1.0, -2)
    fs(c, rrect(-95, -120, 190, 240, 6), "#23395d", 5)
    for s in (-1, 1):
        c.drawPath(poly([(s * 38, -40), (s * 66, -62), (s * 70, -88)], False), stroke(OUT, 22))
        c.drawPath(poly([(s * 38, -40), (s * 66, -62), (s * 70, -88)], False), stroke("#ff5a5f", 14))
        c.drawCircle(s * 70, -90, 12, fill("#ff5a5f"))
    hp = skia.Path()
    hp.moveTo(0, 10)
    hp.cubicTo(-60, -30, -34, -86, 0, -54)
    hp.cubicTo(34, -86, 60, -30, 0, 10)
    fs(c, hp, "#ff5a5f", 5)
    text(c, "FEELINGS", 0, 52, "bangers", 34, "#ffd23f")
    text(c, "= GAINS", 0, 92, "bangers", 34, "#ffffff")
    c.restore()
    # whiteboard
    fs(c, rrect(480, 140, 220, 250, 8), "#fafafa", 6)
    text(c, "ASSEMBLY PLAN", 590, 180, "inter_black", 20, "#23395d")
    items = [("1. FEELINGS", "#e63946"), ("2. ROLE PLAY", "#2a9d6f"), ("3. ???", "#3a86ff"), ("4. GAINS", "#e63946")]
    for i, (s_, cc) in enumerate(items):
        text(c, s_, 500, 222 + i * 40, "bangers", 30, cc, align="left")
    fs(c, rrect(470, 386, 240, 14, 4), "#9aa0aa", 4)
    if night:
        c.drawRect(BIG, fill("#1a1030", 0.35))
        c.drawCircle(360, 560, 520, rad_grad(360, 560, 520, ["#ffb347", "#ffb347"], [0, 1], [0.35, 0]))


def office_desk(c, t, y=930):
    fs(c, rrect(40, y, 640, 42, 8), "#8a5a34", 6)
    fs(c, rrect(60, y + 38, 600, 300, 6), "#6f4526", 6)
    for k in range(2):
        c.drawPath(rrect(90 + k * 290, y + 70, 250, 110, 8), stroke("#5a3820", 4))
    # nameplate
    fs(c, rrect(250, y - 44, 220, 46, 6), "#2b2d42", 4)
    text(c, "PRINCIPAL BRODIE", 360, y - 14, "inter_black", 17, "#ffd23f")
    # tissues ("for feelings") + protein tumbler
    fs(c, rrect(90, y - 50, 110, 52, 6), "#8ecae6", 4)
    c.drawPath(smooth_path([(130, y - 50), (140, y - 80), (152, y - 64), (160, y - 50)], False), fill("#ffffff"))
    text(c, "FEELINGS", 145, y - 16, "inter_black", 14, "#23395d")
    fs(c, rrect(560, y - 96, 56, 98, 10), "#f4f1de", 4)
    fs(c, rrect(556, y - 108, 64, 20, 6), "#2a9d6f", 4)
    text(c, "PROTEIN", 588, y - 46, "inter_black", 11, "#23395d")


def bg_gym(c, t, banner="FEELINGS ASSEMBLY", sub="(it's gonna be fun, bro)", lights=1.0):
    c.drawRect(BIG, lin_grad(0, 0, 0, 820, ["#dfe6ee", "#c3cfdc"]))
    for r in range(0, 22):
        y = r * 40 - 40
        c.drawPath(poly([(-800, y), (W + 800, y)], False), stroke("#aab6c4", 2, 0.7))
        off = 0 if r % 2 == 0 else 45
        for k in range(-10, 18):
            x = k * 90 + off
            c.drawPath(poly([(x, y), (x, y + 40)], False), stroke("#aab6c4", 2, 0.5))
    c.drawRect(skia.Rect.MakeLTRB(-800, 420, W + 800, 480), fill("#23395d"))
    text(c, "MAPLE HILL ELEMENTARY", 360, 462, "inter_black", 28, "#ffffff")
    # banner
    if banner:
        at(c, 360, 230, 1.0, 0)
        fs(c, rrect(-300, -70, 600, 140, 10), "#e63946", 6)
        for s in (-1, 1):
            c.drawPath(poly([(s * 280, -70), (s * 280, -140)], False), stroke("#555566", 4))
        text(c, banner, 0, 10, "bangers", 66 if len(banner) < 20 else 52, "#ffffff", outline=OUT, ow=8)
        if sub:
            text(c, sub, 0, 50, "fredoka", 26, "#ffe1e1")
        c.restore()
    # floor
    c.drawRect(skia.Rect.MakeLTRB(-800, 800, W + 800, H + 800), lin_grad(0, 800, 0, H, ["#e7b57a", "#c98b4f"]))
    c.drawPath(poly([(-800, 800), (W + 800, 800)], False), stroke("#8a5a34", 6))
    for k in range(-12, 13):
        c.drawPath(poly([(360 + k * 40, 800), (360 + k * 150, H + 400)], False), stroke("#b97a43", 2, 0.6))
    c.drawPath(oval(360, 1120, 420, 110), stroke("#ffffff", 7, 0.8))
    if lights > 0:
        for s in (-1, 1):
            p = poly([(360 + s * 330, -20), (360 + s * 300, -20), (360 + s * 60, 1100), (360 + s * 230, 1100)])
            c.drawPath(p, fill("#fff6c8", 0.10 * lights))


def stool(c, x, y, s=1.0):
    at(c, x, y, s)
    for k in (-1, 1):
        c.drawPath(poly([(k * 40, 10), (k * 62, 120)], False), stroke(OUT, 16))
        c.drawPath(poly([(k * 40, 10), (k * 62, 120)], False), stroke("#c0c0c8", 9))
    c.drawPath(poly([(-52, 70), (52, 70)], False), stroke("#c0c0c8", 7))
    fs(c, oval(0, 4, 70, 18), "#e63946", 5)
    c.restore()


def heads_back(c, t, y=1270, bounce=0.0, seed=0, turn=0.0):
    for k in range(7):
        x = -20 + k * 128 + 18 * hash1(k + seed)
        look = KID_LOOKS[(k * 3 + seed) % 8]
        b = bounce * 12 * abs(math.sin(t * 8 + k * 1.3))
        fs(c, rrect(x - 95, y + 40 - b, 190, 140, 50), look[2], 5)
        for s in (-1, 1):
            c.drawCircle(x + s * 70, y - b + 8, 15, fill(look[0]))
            c.drawCircle(x + s * 70, y - b + 8, 15, stroke(OUT, 4))
        fs(c, oval(x, y - b, 72, 80), look[1], 5)


def tumbleweed(c, x, y, r, t):
    at(c, x, y, 1.0, t * 300)
    for i in range(7):
        c.drawPath(oval(0, 0, r * (0.5 + 0.08 * i), r * (0.9 - 0.06 * i)), stroke("#a67c52", 4, 0.9))
        c.rotate(26)
    c.restore()


# ======================================================================= the bleachers (crowd)

ROWS = [(250, 0.44), (430, 0.52), (630, 0.6), (850, 0.7)]
CARTER_X = 360
SEATS = []
for _r, (_hy, _s) in enumerate(ROWS):
    _sp = 175 * _s
    _n = int((W + 260) / _sp) + 1
    _off = -110 + (_r % 2) * _sp * 0.5
    for _k in range(_n):
        _x = _off + _k * _sp
        if _r == 2 and abs(_x - CARTER_X) < 1.75 * _sp:
            continue
        _i = len(SEATS)
        h = hash1(_i * 7 + 3) * 0.5 + 0.5
        SEATS.append(dict(i=_i, r=_r, x=_x, y=_hy, s=_s, look=KID_LOOKS[int(h * 97) % 8], hair=int(h * 31) % 3,
                          cap=["#e63946", "#3a86ff", None, None, None][int(h * 53) % 5],
                          glasses=int(h * 71) % 5 == 0))
HECKLER = min((s for s in SEATS if s["r"] == 1), key=lambda s: abs(s["x"] - 560))
HECKLER.update(look=(SKIN_A, "#b5651d", "#8338ec"), hair=0, cap="#222233", glasses=False)
COUGHER = min((s for s in SEATS if s["r"] == 0), key=lambda s: abs(s["x"] - 600))
FRIEND_A = dict(look=(SKIN_C, "#111111", "#3a86ff"), hair=1, cap=None, glasses=False)
FRIEND_B = dict(look=(SKIN_B, "#f2d16b", "#2a9d6f"), hair=2, cap="#fb5607", glasses=False)


def crowd_face(t, i, mode, x, y, target=None):
    ph = hash1(i * 13) * 10
    if mode == "laugh":
        k = 0.5 + 0.5 * math.sin(t * 9 + ph)
        return P_(t=t, lid=0.0, happy=1.0, smile=0.9, mouth_open=0.3 + 0.4 * k), -9 * k, 3 * math.sin(t * 7 + ph)
    if mode == "giggle":
        k = 0.5 + 0.5 * math.sin(t * 11 + ph)
        return P_(t=t, lid=0.0, happy=1.0, smile=0.8, mouth_open=0.15 + 0.2 * k), -4 * k, 0
    if mode == "stare":
        tx, ty = target
        return P_(t=t, lid=0.95, px=clamp((tx - x) / 150, -1, 1), py=clamp((ty - y) / 220, -0.9, 0.9), smile=0.0, pr=0.8,
                  brow_y=-0.1), 0, 0
    if mode == "blank":
        return P_(t=t, lid=0.62 * blink(t, i, 4.5), smile=-0.05, py=0.1, brow_y=-0.2), 0, 0
    if mode == "gasp":
        tx, ty = target if target else (x, y)
        return P_(t=t, lid=1.1, px=clamp((tx - x) / 150, -1, 1), py=clamp((ty - y) / 220, -0.9, 0.9), mouth_open=0.55,
                  mouth_w=0.6, smile=-0.2, brow_y=0.6, pr=0.7), 0, 0
    if mode == "confused":
        return P_(t=t, lid=blink(t, i, 3.3), smile=-0.15, asym=0.4, browL=0.5, px=0.3 * hash1(i)), 0, 0
    sx, sy = saccade(t, i, 2.2, 0.25)
    look = (sx, 0.2 + sy * 0.5)
    if target is not None:
        tx, ty = target
        look = (clamp((tx - x) / 160, -1, 1), clamp((ty - y) / 260, -0.8, 0.8))
    return P_(t=t, lid=blink(t, i, 3.5 + hash1(i)), px=look[0], py=look[1], smile=0.25 + 0.15 * hash1(i * 5)), 0, 0


def draw_kid(c, t, seat, P, dy=0.0, lean=0.0, x=None, s=None):
    c.save()
    c.translate(seat["x"] if x is None else x, seat["y"] + dy)
    kid(c, seat["look"], P, t, seat["hair"], seat["cap"], seat["glasses"], seat["s"] if s is None else s, lean)
    c.restore()


def bg_bleachers(c, t):
    c.drawRect(BIG, lin_grad(0, 0, 0, H, ["#34446a", "#232d48"]))
    for k in range(-1, 6):
        fs(c, rrect(30 + k * 170, 40, 120, 80, 6), "#9cc3e6", 5)
        c.drawPath(poly([(90 + k * 170, 40), (90 + k * 170, 120)], False), stroke(OUT, 4))
    cols = ["#e63946", "#ffd23f", "#3a86ff", "#2a9d6f", "#e63946", "#ffd23f", "#3a86ff"]
    for k in range(-1, 6):
        x = 60 + k * 130
        fs(c, poly([(x, 140), (x + 90, 150), (x, 172)]), cols[k + 1], 4)


def bleachers(c, t, mode="watch", target=None, carter_fn=None, friends=0.0, friend_fn=None, seat_fn=None,
              after_row=None, floor_fn=None, max_row=3):
    """mode: str or fn(seat)->str. carter_fn(c) draws Carter in his seat (row 2). friends: scoot-away amount.
    seat_fn(seat) -> optional dict(P=..., dy=..., lean=...) overrides. after_row[r](c) draws extra stuff after row r."""
    bg_bleachers(c, t)
    for r, (hy, s) in enumerate(ROWS):
        if r > max_row:
            break
        for seat in SEATS:
            if seat["r"] != r:
                continue
            m = mode(seat) if callable(mode) else mode
            P, dy, lean = crowd_face(t, seat["i"], m, seat["x"], seat["y"], target)
            ov = seat_fn(seat) if seat_fn else None
            if ov:
                P = ov.get("P", P)
                dy = ov.get("dy", dy)
                lean = ov.get("lean", lean)
            draw_kid(c, t, seat, P, dy, lean)
        if r == 2:
            off = 135 + 80 * friends
            for side, fr in ((-1, FRIEND_A), (1, FRIEND_B)):
                seat = dict(fr, x=CARTER_X + side * off, y=hy, s=s, i=900 + side)
                P, dy, lean = crowd_face(t, 900 + side, mode if isinstance(mode, str) else "watch", seat["x"], hy, target)
                if friend_fn:
                    o = friend_fn(side)
                    if o:
                        P, dy, lean = o.get("P", P), o.get("dy", dy), o.get("lean", lean)
                draw_kid(c, t, seat, P, dy, lean)
            if carter_fn:
                carter_fn(c)
        y = hy + 128 * s
        c.drawRect(skia.Rect.MakeLTRB(-800, y, W + 800, y + 34 * s), fill("#d39a5d"))
        c.drawPath(poly([(-800, y), (W + 800, y)], False), stroke(OUT, 4))
        c.drawRect(skia.Rect.MakeLTRB(-800, y + 34 * s, W + 800, y + 34 * s + 300), fill("#6c4a2e"))
        c.drawPath(poly([(-800, y + 34 * s), (W + 800, y + 34 * s)], False), stroke(OUT, 4))
        if after_row and r in after_row:
            after_row[r](c)
    if max_row < 3:
        return
    # gym floor in front
    fy = ROWS[3][0] + 128 * ROWS[3][1] + 34 * ROWS[3][1] + 70
    c.drawRect(skia.Rect.MakeLTRB(-800, fy, W + 800, H + 800), lin_grad(0, fy, 0, H, ["#e7b57a", "#c98b4f"]))
    c.drawPath(poly([(-800, fy), (W + 800, fy)], False), stroke(OUT, 5))
    if floor_fn:
        floor_fn(c)


CARTER_S = 0.6 * 0.72
CARTER_SEAT_Y = ROWS[2][0] + 160 * CARTER_S


def carter_in_seat(c, t, P, pose="sit", blend=None, stand=0.0, shake=0.0, sway=0.0, x=CARTER_X, flail=0.0):
    legs = "stand" if stand > 0.5 else "sit"
    put(c, x, CARTER_SEAT_Y - 48 * stand, CARTER_S, carter, P, t, pose, blend, legs=legs, shake=shake, flail=flail,
        rot=sway)


# ======================================================================= the stage (gym floor)

CHAD_AT = (150, 740, 0.6)
CHAD_NEAR = (255, 740, 0.6)
BRODIE_NEAR = (480, 740, 0.6)
CLOSE = (2.45, 360, 560)
BRODIE_AT = (575, 740, 0.6)
CARTER_STOOL = (365, 852, 0.5)


def draw_stage(c, t, st):
    bg_gym(c, t, st.get("banner", "FEELINGS ASSEMBLY"), st.get("sub", "(it's gonna be fun, bro)"), st.get("lights", 1.0))
    if st.get("pre"):
        st["pre"](c)
    if st.get("stool", True):
        stool(c, 365, 905)
    for name, fn in (("chad", chad), ("brodie", brodie), ("carter", carter)):
        d = st.get(name)
        if not d:
            continue
        d = dict(d)
        x, y, s = d.pop("x"), d.pop("y"), d.pop("s")
        P = d.pop("P")
        rot = d.pop("rot", 0.0)
        put(c, x, y, s, fn, P, t, rot=rot, **d)
    if st.get("post"):
        st["post"](c)
    if st.get("heads", True):
        heads_back(c, t, 1272, st.get("bounce", 0.0))


def chad_st(t, P, pose="stand", blend=None, at_=CHAD_AT, **kw):
    return dict(x=at_[0], y=at_[1], s=at_[2], P=P, pose=pose, blend=blend, **kw)


def brodie_st(t, P, pose="stand", blend=None, at_=BRODIE_AT, **kw):
    return dict(x=at_[0], y=at_[1], s=at_[2], P=P, pose=pose, blend=blend, **kw)


def carter_st(t, P, pose="sit", blend=None, at_=CARTER_STOOL, **kw):
    return dict(x=at_[0], y=at_[1], s=at_[2], P=P, pose=pose, blend=blend, **kw)


# ======================================================================= 1. office

def sc_office(c, t):
    z, cx, cy = kf(t, [(0, (1.0, 360, 660)), (7.9, (1.06, 360, 660)), (8.3, (1.18, 290, 640)), (11.1, (1.18, 290, 640)),
                       (11.5, (1.18, 440, 640)), (14.8, (1.18, 440, 640)), (15.1, (1.2, 290, 640)), (17.9, (1.2, 290, 640)),
                       (18.3, (1.2, 440, 640)), (20.1, (1.2, 440, 640)), (20.4, (1.3, 360, 640)), (21.4, (1.36, 360, 640))])
    c.save()
    cam(c, z, cx, cy)
    bg_office(c, t)
    bpose, bbl = pose_at(t, [(0, "chin"), (L0("O1"), "open"), (L1("O1"), "crossed"), (L0("O3"), "fist"),
                             (L1("O3"), "hips"), (M["fistbump"] - 0.25, "fist_r")])
    cpose, cbl = pose_at(t, [(0, "chin"), (L0("O2"), "heart"), (L1("O2"), "stand"), (L0("O4"), "flex"),
                             (M["fistbump"] - 0.25, "fist_l")])
    nod = 4 * math.sin(t * 6) * (1 if L0("O2") < t < L1("O2") else 0)
    bP = FP(t, 1, mouth("BRODIE", t), smile=0.55 + 0.2 * (t > L0("O3")), brow_y=0.1 + nod * 0.02)
    cP = FP(t, 2, mouth("CHAD", t), look=(-0.8, 0) if t > L0("O1") else (0.6, -0.6) if t < L0("O1") else None,
            smile=0.6, tears=0.6 if L0("O2") < t < L1("O2") + 1.0 else 0.0, brow_ang=0.4 if L0("O2") < t < L1("O2") else 0.0,
            happy=1.0 if t > M["fistbump"] else 0.0, lid=0.0 if t > M["fistbump"] else 1.0)
    put(c, 200, 700 + nod, 0.72, brodie, bP, t, bpose, bbl)
    put(c, 525, 705, 0.72, chad, cP, t, cpose, cbl)
    if t > M["fistbump"]:
        u = t - M["fistbump"]
        starburst(c, 362, 672, 60 + 30 * u, 34 + 16 * u, 12, "#ffd23f", t, 4)
        bubble_text(c, "BUMP!", 362, 600, 56, "#ffffff", t, M["fistbump"], rot=-6)
        twinkles(c, t, 260, 520, 220, 6, 9)
    office_desk(c, t)
    c.restore()
    # title card
    if t < 2.7:
        a = 1 - ramp(t, 2.1, 2.6)
        c.drawRect(skia.Rect.MakeWH(W, H), fill("#141024", 0.82 * a))
        u = ease_out_back(clamp(t / 0.5), 2)
        at(c, 360, 560, u, -3)
        text(c, "THE", 0, -110, "bangers", 80, "#ffffff", outline=OUT, ow=10, a=a)
        text(c, "ASSEMBLY", 0, 20, "bangers", 150, "#ffd23f", outline=OUT, ow=16, a=a, shadow=True)
        c.restore()
        text(c, "a story about feelings (and gains)", 360, 700, "fredoka", 34, "#ffc2d6", outline=OUT, ow=6,
             a=a * ramp(t, 0.5, 0.9))


# ======================================================================= 2. the stands

def sc_stands(c, t):
    s0 = M["stands"]
    close = t >= L0("S1") - 0.1
    z, cx, cy = kf(t, [(s0, (1.0, 360, 640)), (L0("S1") - 0.1, (1.12, 360, 620)), (L0("S1") - 0.1, CLOSE),
                       (L0("S2") - 0.1, CLOSE), (L0("S2") + 0.3, (2.3, 285, 600)),
                       (L0("S3") - 0.1, (2.3, 285, 600)), (L0("S3") + 0.3, (2.55, 355, 590))])
    c.save()
    cam(c, z, cx, cy)
    cm = mouth("CARTER", t)
    pose, bl = pose_at(t, [(0, "cross"), (L0("S3") + 0.9, "whisper")])
    roll = pulse(t, L0("S1") + 1.4, 0.9)
    if t < L0("S3"):
        P = FP(t, 3, cm, look=(-0.8, 0) if L0("S2") < t else (0.1, -0.9 * roll), lid=0.55, smile=-0.3, brow_ang=-0.1)
    else:
        P = FP(t, 3, cm, look=(-0.7, 0.1) if t > L0("S3") + 0.9 else (0.0, 0.0), lid=0.75, smile=0.6, asym=0.5,
               browR=0.6, brow_ang=-0.3)

    def friend_fn(side):
        if side < 0:
            return dict(P=FP(t, 41, mouth("FRIEND", t), look=(0.9, 0.1), smile=0.1, brow_ang=0.4 if speaking("S2", t) else 0.0))
        return dict(P=FP(t, 42, 0.0, look=(-0.9, 0.1), smile=0.3))

    bleachers(c, t, "watch", carter_fn=lambda c_: carter_in_seat(c_, t, P, pose, bl), friend_fn=friend_fn,
              max_row=2 if close else 3)
    c.restore()
    if t < s0 + 0.6:
        black(c, 1 - ramp(t, s0, s0 + 0.4))


# ======================================================================= 3. LOSERS! / the stare

def stage_bros(t, bP, cP, bpose="hips", cpose="mic", bbl=None, cbl=None, cprop="mic", glasses=1.0, cat=CHAD_NEAR,
               bat=BRODIE_NEAR, **kw):
    st = dict(chad=chad_st(t, cP, cpose, cbl, prop=cprop, at_=cat), brodie=brodie_st(t, bP, bpose, bbl, glasses=glasses, at_=bat),
              stool=False)
    st.update(kw)
    return st


def sc_losers(c, t):
    s0 = M["losers"]
    t_yell, t_scr, t_stare = L0("T2"), M["scratch"], M["stare"]
    t_car = t_stare + 2.1
    t_wide = M["friends_scoot"] + 1.1
    if t < t_yell:
        # Chad opens the assembly
        z, cx, cy = kf(t, [(s0, (1.15, 365, 650)), (s0 + 1.0, (1.15, 365, 650)), (t_yell, (1.5, 290, 650))])
        wince = pulse(t, s0, 0.6)
        cP = FP(t, 5, mouth("CHAD", t), smile=0.8 - wince, squeeze=1.0 if wince > 0.3 else 0.0, brow_y=0.4)
        bP = FP(t, 6, 0, smile=0.6)
        c.save()
        cam(c, z, cx, cy)
        draw_stage(c, t, stage_bros(t, bP, cP, "hips", "mic"))
        c.restore()
        if wince > 0:
            bubble_text(c, "SKREEEE", 520, 380, 54, "#ffffff", t, s0, a=wince, rot=8)
        return
    if t < t_scr + 0.15:
        # Carter stands up and yells
        stand = ramp(t, t_yell - 0.25, t_yell)
        P = FP(t, 3, max(mouth("CARTER", t), 0.9 * pulse(t, t_yell, 0.75)), lid=1.1, smile=0.4, brow_ang=-0.5, red=0.4,
               teeth=True)
        sh = 0.0
        if t > t_scr:
            sh = 1.0

        def friend_fn(side):
            if side > 0 and t > t_yell + 0.15:
                return dict(P=P_(t=t, lid=0.0, happy=1.0, smile=0.8, mouth_open=0.2 + 0.15 * math.sin(t * 20)))
            return dict(P=FP(t, 40 + side, 0, look=(-side * 0.9, -0.3), smile=0.2, lid=1.1))

        c.save()
        cam(c, 2.2, 360, 585, shake=sh * 2, t=t)
        bleachers(c, t, lambda s: "giggle" if hash1(s["i"] * 3) > 0.55 and t > t_yell + 0.2 else "watch",
                  target=(CARTER_X, 600), friend_fn=friend_fn, max_row=2,
                  carter_fn=lambda c_: carter_in_seat(c_, t, P, "cup", None, stand))
        c.restore()
        comic_text(c, "LOSERS!", 360, 250, 120, "#ffd23f", t, t_yell + 0.05, -6, True, "#e63946")
        if t > t_scr:
            c.drawRect(skia.Rect.MakeWH(W, H), fill("#ffffff", 0.25))
        return
    if t < t_car:
        # dead silence: both bros stare
        u = (t - t_stare) / (t_car - t_stare)
        z = lerp(1.6, 2.2, smooth(u))
        cP = P_(t=t, lid=1.0, pr=0.75, smile=0.0, mouth_open=0.0, brow_y=-0.1)
        bP = P_(t=t, smile=0.0, brow_y=0.0)
        c.save()
        cam(c, z, 367, 625)
        draw_stage(c, t, stage_bros(t, bP, cP, "stand", "stand", cprop="mic", bounce=0.0))
        # glint across the sunglasses
        g = pulse(t, t_stare + 1.2, 0.5)
        if g > 0:
            sparkle_star(c, 480 + 24, 635 - 14, 26 * g, g)
        c.restore()
        vignette(c, 0.55)
        text(c, "*silence*", 360, 260, "fredoka", 40, "#ffffff", outline=OUT, ow=7, a=ramp(t, t_stare + 0.4, t_stare + 0.8))
        return
    if t < t_wide:
        # Carter sweats it out; friends scoot away
        dart = 0.7 * (1 if math.sin(t * 5.5) > 0 else -1)
        look = (dart, 0.0)
        if t > L0("T3") + 0.9:
            look = (-0.9, 0.1)
        if t > M["friends_scoot"]:
            look = (0.9 if math.sin(t * 3) > 0 else -0.9, 0.0)
        P = FP(t, 3, mouth("CARTER", t), look=look, noblink=True, lid=1.05, smile=0.55, teeth=True, sweat=0.9,
               brow_ang=0.7, red=0.3, clench=0.0 if speaking("T3", t) else 0.6)
        scoot = ramp(t, M["friends_scoot"], M["friends_scoot"] + 0.6)

        def friend_fn(side):
            return dict(P=P_(t=t, lid=0.8, px=side * 1.0, py=-0.6, smile=0.0, mouth_w=0.4, mouth_open=0.12 * scoot),
                        lean=side * 4 * scoot)

        c.save()
        cam(c, 2.0, 360, 590)
        bleachers(c, t, "stare", target=(CARTER_X, 560), friends=scoot, friend_fn=friend_fn, max_row=2,
                  carter_fn=lambda c_: carter_in_seat(c_, t, P, "shrug", None, 1.0, sway=3 * math.sin(t * 2.2)))
        c.restore()
        if scoot > 0:
            for s in (-1, 1):
                text(c, "scoot", 360 + s * 220, 470, "bangers", 44, "#ffffff", outline=OUT, ow=7, a=pulse(t, M["friends_scoot"], 1.2))
        return
    if t < M["resume"]:
        # the whole gym stares
        z = lerp(1.25, 1.45, smooth((t - t_wide) / (M["resume"] - t_wide)))
        sit = ramp(t, t_wide + 0.4, t_wide + 1.3)
        P = P_(t=t, lid=1.05, pr=0.6, px=0.5 * math.sin(t * 4), smile=0.2, wobble=0.6, sweat=1.0, brow_ang=0.8, red=0.3)

        def seat_fn(seat):
            if seat is COUGHER and t > M["cough"]:
                return dict(P=P_(t=t, lid=0.0, squeeze=1.0 if t < M["cough"] + 0.7 else 0.0, mouth_open=0.5 * pulse(t, M["cough"], 0.7),
                                 mouth_w=0.6, smile=0.0))
            return None

        c.save()
        cam(c, z, 360, 560)
        bleachers(c, t, "stare", target=(CARTER_X, 600), friends=1.0, seat_fn=seat_fn,
                  friend_fn=lambda side: dict(P=P_(t=t, lid=0.9, px=-side * 0.9, smile=0.0)),
                  carter_fn=lambda c_: carter_in_seat(c_, t, P, "small", None, 1.0 - sit))
        c.restore()
        c.drawRect(skia.Rect.MakeWH(W, H), rad_grad(360, 700, 600, ["#000000", "#000000"], [0.25, 1], [0.0, 0.55]))
        if t > M["cough"]:
            bubble_text(c, "*cough*", COUGHER["x"] - 30, COUGHER["y"] - 60, 40, "#ffffff", t, M["cough"])
        return
    # resume like nothing happened
    bm = mouth("BRODIE", t)
    bP = FP(t, 6, bm, smile=0.7, brow_y=0.4)
    cP = FP(t, 5, 0, smile=0.8, lid=1.0)
    c.save()
    cam(c, 1.35, 385, 650)
    draw_stage(c, t, stage_bros(t, bP, cP, "thumbs", "mic"))
    c.restore()


# ======================================================================= 4. existential crisis

def sc_crisis(c, t):
    s0 = M["crisis"]
    lt = t - s0
    c.drawRect(BIG, fill("#1a0f2e"))
    for i in range(24):
        a0 = i * 15 + lt * 18
        p = skia.Path()
        p.moveTo(360, 700)
        r = 1400
        p.lineTo(360 + r * math.cos(math.radians(a0)), 700 + r * math.sin(math.radians(a0)))
        p.lineTo(360 + r * math.cos(math.radians(a0 + 7.5)), 700 + r * math.sin(math.radians(a0 + 7.5)))
        p.close()
        c.drawPath(p, fill("#5b34b0" if i % 2 else "#2d1b5c", 0.8))
    for i in range(9):
        ph = (lt * 0.25 + i / 9) % 1.0
        ang = i * 40 + lt * 20
        rr = 110 + 250 * ph
        x = 360 + rr * math.cos(math.radians(ang))
        y = 700 + rr * math.sin(math.radians(ang))
        text(c, ["?", "joke?", "?", "loser?", "?", "who am I?", "?", "?!", "huh?"][i], x, y, "bangers", 30 + 40 * ph, "#ffffff",
             outline=OUT, ow=6, a=math.sin(math.pi * ph))
    z = lerp(1.0, 1.25, smooth(lt / 4.2))
    c.save()
    cam(c, z, 360, 680)
    P = P_(t=t, lid=1.12, pr=0.4, px=0.0, py=0.0, smile=-0.1, mouth_open=0.12, mouth_w=0.5, brow_ang=0.9, brow_y=0.4,
           sweat=0.5, lower=0.15)
    put(c, 360, 860, 1.05, carter, P, t, "small", legs="sit")
    c.restore()
    vignette(c, 0.7)


# ======================================================================= 5. the hat

def sc_hat(c, t):
    s0 = M["hat"]
    t_ins = M["all_carter"] - 0.1
    t_car = t_ins + 0.9
    t_whistle = L0("H4") - 0.15
    if t < t_ins:
        drawing = ramp(t, M["draw"] - 0.2, M["draw"] + 0.3)
        lift = ramp(t, M["draw"] + 0.3, M["draw"] + 0.9)
        cpose = "hat_draw"
        cbl = None
        prop = ("hat",)
        if t > M["draw"] - 0.2:
            cbl = ("plead", drawing * (1 - lift))
        if lift > 0:
            cbl = ("wave", lift * 0.8)
            prop = ("hat", "slip")
        cP = FP(t, 5, mouth("CHAD", t), smile=0.8, brow_y=0.5 if t > L0("H2") else 0.2,
                look=(0.6, -0.8) if lift > 0.5 else None)
        bP = FP(t, 6, 0, smile=0.6)
        z, cx, cy = kf(t, [(s0, (1.35, 330, 660)), (M["draw"], (1.5, 290, 640)), (L0("H2") + 0.7, (1.5, 290, 640)),
                           (t_ins - 0.2, (2.4, 345, 590))])
        c.save()
        cam(c, z, cx, cy)
        draw_stage(c, t, stage_bros(t, bP, cP, "hips", cpose, cbl=cbl, cprop=prop))
        c.restore()
        return
    if t < t_car:
        # insert: every slip in the hat says CARTER
        lt = t - t_ins
        c.drawRect(BIG, rad_grad(360, 520, 700, ["#ffd23f", "#e63946"], [0, 1]))
        speed_lines(c, 360, 520, t, 36, "#ffffff", 0.25)
        at(c, 360, 380, 1.4, 160)
        fs(c, rrect(-90, -150, 180, 160, 12), "#1d1d22", 6)
        fs(c, oval(0, 10, 130, 26), "#1d1d22", 6)
        c.drawRect(skia.Rect.MakeLTRB(-90, -50, 90, -26), fill("#e63946"))
        c.restore()
        for i in range(14):
            k = i / 14
            y = 470 + lt * 900 * (0.6 + 0.4 * hash1(i)) - 200 * k
            x = 360 + 260 * hash1(i * 7) + 40 * math.sin(lt * 5 + i)
            if y < 420:
                continue
            at(c, x, y, 1.0, 25 * hash1(i * 3) + lt * 80 * hash1(i * 5))
            fs(c, rrect(-80, -28, 160, 56, 4), "#ffffff", 3)
            text(c, "CARTER", 0, 12, "bangers", 38, "#e63946")
            c.restore()
        comic_text(c, "ALL OF THEM?!", 360, 1000, 80, "#ffffff", t, t_ins + 0.15, -4, True, "#3a86ff")
        return
    if t < t_whistle:
        P = FP(t, 3, mouth("CARTER", t), noblink=True, lid=1.15, pr=0.5, sweat=1.0, wobble=0.7 if not speaking("H3", t) else 0.0,
               smile=-0.3, brow_ang=1.0, pale=0.5, px=0.25 * math.sin(t * 13))
        c.save()
        cam(c, *CLOSE, shake=0.4, t=t)
        bleachers(c, t, "stare", target=(CARTER_X, 600), friends=1.0, max_row=2,
                  carter_fn=lambda c_: carter_in_seat(c_, t, P, "grip", None, 0.0, shake=0.6))
        c.restore()
        return
    # Brodie calls the gym bros
    bP = FP(t, 6, mouth("BRODIE", t), smile=0.6, brow_y=0.3)
    cP = FP(t, 5, 0, smile=0.7, look=(0.9, 0))
    c.save()
    cam(c, 1.45, 420, 650)
    draw_stage(c, t, stage_bros(t, bP, cP, "cup", "stand", cprop=None))
    c.restore()
    if t > L1("H4") - 0.2:
        bubble_text(c, "*stomp stomp*", 360, 1010, 46, "#ffffff", t, L1("H4") - 0.2, rot=-4)


# ======================================================================= 6. carried down

def god_rays(c, cx, cy, t, a=0.25, n=12, color="#fff2a8"):
    for i in range(n):
        ang = math.radians(i * 360 / n + t * 12)
        p = skia.Path()
        p.moveTo(cx, cy)
        p.lineTo(cx + 1600 * math.cos(ang - 0.09), cy + 1600 * math.sin(ang - 0.09))
        p.lineTo(cx + 1600 * math.cos(ang + 0.09), cy + 1600 * math.sin(ang + 0.09))
        p.close()
        c.drawPath(p, fill(color, a))


def procession(c, t, x, y, s, scream=0.0, cs_ratio=0.85):
    """two gym bros carrying Carter above their heads; (x, y) = bros' chest line centre"""
    off = 150 * s
    put(c, x - off, y, s, gym_bro, t, 0, 1.0, 1.0, 0.85, 0.3)
    put(c, x + off, y, s, gym_bro, t + 0.4, 1, 1.0, 1.0, 0.85, 0.3)
    cs = s * cs_ratio
    hy = y - 270 * s
    P = P_(t=t, lid=1.15, pr=0.45, mouth_open=0.7 + 0.3 * scream, smile=-0.5, brow_ang=1.0, red=0.6, sweat=0.8, teeth=True)
    put(c, x, hy - 112 * cs + 6 * math.sin(t * 14), cs, carter, P, t, "flail", legs="dangle", flail=1.0, rot=4 * math.sin(t * 9))


def sc_carry(c, t):
    s0 = M["carry"]
    t_lift = M["lift"]
    t_kids = L0("H7") - 0.1
    t_plop = M["plop"] - 0.35
    if t < t_lift:
        # the gym bros arrive at Carter's seat
        gm = mouth("GYM", t)
        P = FP(t, 3, 0, look=(0.0, -0.9), noblink=True, lid=1.15, pr=0.5, smile=-0.3, brow_ang=1.0, sweat=1.0, wobble=0.6)

        def extra(c_):
            for side, v in ((-1, 0), (1, 1)):
                put(c_, CARTER_X + side * 150, ROWS[2][0] + 25, 0.46, gym_bro, t + v, v, 0.0, 0.0, 0.9,
                    gm if v == 0 else 0.15, -side * 0.7, 0.5)

        c.save()
        cam(c, 1.85, 360, 560)
        bleachers(c, t, "stare", target=(CARTER_X, 600), friends=1.0, after_row={2: extra}, max_row=2,
                  carter_fn=lambda c_: carter_in_seat(c_, t, P, "grip", None, 0.0, shake=0.4))
        c.restore()
        return
    if t < t_kids:
        u = (t - t_lift) / (t_kids - t_lift)
        x = lerp(40, 680, u)
        bx = x

        def mode(seat):
            return "gasp" if abs(seat["x"] - bx) < 160 else "watch"

        c.save()
        cam(c, 1.0, 360, 640)
        bleachers(c, t, mode, target=(x, 600), friends=1.0)
        c.restore()
        c.drawRect(skia.Rect.MakeWH(W, H), fill("#2a1050", 0.35))
        god_rays(c, x, 520, t, 0.16)
        procession(c, t, x, 880, 0.75, mouth("CARTER", t))
        heads_back(c, t, 1280, 0.0, 3)
        if speaking("H6", t):
            text(c, "SQUEEEE!", 360 + 40 * math.sin(t * 9), 260, "bangers", 72, "#ffb3c6", outline=OUT, ow=9)
        return
    if t < t_plop:
        # two kids: what is he doing?
        lt = t - t_kids
        bg_bleachers(c, t)
        procession_x = lerp(-150, 900, lt / (t_plop - t_kids))
        for k in range(8):
            seat = SEATS[k * 3]
            P, dy, lean = crowd_face(t, seat["i"], "watch", -60 + k * 120, 330, (procession_x, 420))
            c.save()
            c.translate(-60 + k * 120, 330)
            kid(c, seat["look"], P, t, seat["hair"], seat["cap"], seat["glasses"], 0.5, 0)
            c.restore()
        c.drawRect(skia.Rect.MakeLTRB(-10, 400, W + 10, 424), fill("#d39a5d"))
        c.drawRect(skia.Rect.MakeLTRB(-10, 424, W + 10, 1000), fill("#6c4a2e"))
        procession(c, t, procession_x, 640, 0.33, 1.0)
        if 0 < procession_x < W:
            text(c, "AAAAA!", procession_x, 300, "bangers", 46, "#ffb3c6", outline=OUT, ow=6)
        c.drawRect(skia.Rect.MakeLTRB(-10, 700, W + 10, 724), fill("#d39a5d"))
        c.drawRect(skia.Rect.MakeLTRB(-10, 724, W + 10, 1300), fill("#5a3c24"))
        c.drawRect(skia.Rect.MakeLTRB(-10, 980, W + 10, 1010), fill("#d39a5d"))
        ka = (SKIN_D, "#3b2318", "#ef476f")
        kb = (SKIN_A, "#b5651d", "#06d6a0")
        aP = FP(t, 71, mouth("KIDA", t), look=(0.9, -0.5) if not speaking("H8", t) else (0.9, 0), smile=-0.15, asym=0.3,
                browL=0.6, brow_y=0.2)
        bP = FP(t, 72, mouth("KIDB", t), look=(-0.9, 0) if speaking("H7", t) else (-0.2, -0.4), lid=0.6, smile=0.0)
        put(c, 220, 790, 1.35, kid, ka, aP, t, 2)
        put(c, 510, 800, 1.35, kid, kb, bP, t, 0, "#3a86ff")
        return
    # plop onto the stool
    drop = ramp(t, t_plop, M["plop"])
    y = lerp(300, CARTER_STOOL[1], drop * drop)
    squash = pulse(t, M["plop"], 0.3)
    P = P_(t=t, lid=1.1 if drop < 1 else 0.9, pr=0.55, mouth_open=0.4 * (1 - drop), smile=-0.3, brow_ang=0.8, sweat=0.6)
    bP = FP(t, 6, 0, smile=0.5)
    cP = FP(t, 5, 0, smile=0.6)
    c.save()
    cam(c, 1.25, 365, 700)
    st = stage_bros(t, bP, cP, "hips", "stand", cprop=None, cat=CHAD_AT, bat=BRODIE_AT, stool=True)
    st["carter"] = carter_st(t, P, "flail" if drop < 1 else "grip", None, at_=(365, y, 0.5), legs="dangle" if drop < 1 else "sit",
                             flail=1 - drop)
    draw_stage(c, t, st)
    if squash > 0:
        for k in range(6):
            ang = math.radians(180 + k * 36)
            c.drawCircle(365 + 120 * squash * math.cos(ang) * 1.4, 930 + 40 * squash * math.sin(ang), 18 * squash, fill("#ffffff", 0.7))
    c.restore()
    if t > M["plop"]:
        bubble_text(c, "PLOP", 360, 450, 64, "#ffffff", t, M["plop"], rot=-6)


# ======================================================================= 7. the stool / the eyes

def stool_scene_state(t, carterP, cpose="shield", cbl=None, bP=None, bpose="crossed", bbl=None, glasses=1.0, kneel=0.0,
                      chadP=None, chpose="stand", chbl=None, chprop=None, puppet_talk=0.0, hold_glasses=False, **kw):
    st = dict(chad=chad_st(t, chadP or FP(t, 5, 0, smile=0.6), chpose, chbl, prop=chprop, puppet_talk=puppet_talk),
              brodie=brodie_st(t, bP or FP(t, 6, 0, smile=0.5), bpose, bbl, glasses=glasses, kneel=kneel,
                               hold_glasses=hold_glasses, at_=(575, 740 + 95 * kneel, 0.6)),
              carter=carter_st(t, carterP, cpose, cbl))
    st.update(kw)
    return st


def warm_eyes_P(t, mo=0.0, **kw):
    d = dict(lid=1.0, pr=1.25, smile=0.55, brow_ang=0.45, brow_y=0.2, blush=0.25)
    d.update(kw)
    return FP(t, 6, mo, period=4.0, **d)


def sc_stool(c, t):
    t_g = M["glasses_off"]
    t_u2 = L0("U2") - 0.05
    t_u3 = L0("U3") - 0.1
    t_u4 = L0("U4") - 0.1
    if t < t_g - 0.3:
        P = P_(t=t, squeeze=1.0, smile=-0.4, clench=0.6, brow_ang=0.8, sweat=0.7)
        c.save()
        cam(c, 1.55, 380, 700)
        draw_stage(c, t, stool_scene_state(t, P, "shield", shake=0.6, bP=FP(t, 6, 0, smile=0.15)))
        c.restore()
        return
    if t < t_u2:
        g = 1 - ramp(t, t_g, t_g + 0.8)
        lt = t - t_g
        c.save()
        cam(c, kf(t, [(t_g - 0.3, 3.0), (t_g + 1.0, 3.7)]), 572, 625)
        bP = warm_eyes_P(t, noblink=True) if g < 0.5 else FP(t, 6, 0, smile=0.3, noblink=True)
        pose, bl = pose_at(t, [(0, "crossed"), (t_g - 0.3, "glasses"), (t_g + 0.9, "heart")], 0.35)
        st = stool_scene_state(t, P_(t=t, squeeze=1.0), bP=bP, bpose=pose, bbl=bl, glasses=g, hold_glasses=g < 0.2 and t < t_g + 1.0)
        draw_stage(c, t, st)
        c.restore()
        if lt > 0.4:
            a = ramp(t, t_g + 0.4, t_g + 0.9)
            c.drawRect(skia.Rect.MakeWH(W, H), rad_grad(360, 560, 520, ["#ffd6a5", "#ffd6a5"], [0, 1], [0.35 * a, 0]))
            twinkles(c, t, 160, 380, 420, 8, 4, "#fff6b0", 20)
        return
    if t < t_u3:
        peek = ramp(t, t_u2, t_u2 + 0.5)
        P = FP(t, 3, mouth("CARTER", t), look=(0.9, -0.4), lidL=lerp(0.0, 1.05, peek), lidR=lerp(0.0, 0.25, peek),
               pr=1.2, smile=-0.1, brow_ang=0.7, mouth_w=0.8, blush=0.3 * peek)
        c.save()
        cam(c, 2.1, 380, 700)
        draw_stage(c, t, stool_scene_state(t, P, "shield", bP=warm_eyes_P(t), glasses=0.0, bpose="heart"))
        c.restore()
        return
    if t < t_u4:
        kn = ramp(t, t_u3, t_u3 + 0.6)
        P = FP(t, 3, 0, look=(0.9, 0.1), lid=1.05, pr=1.0, smile=-0.1, brow_ang=0.6)
        c.save()
        z, cx, cy = kf(t, [(t_u3, (1.5, 460, 720)), (L1("U3"), (1.6, 470, 720))])
        cam(c, z, cx, cy)
        draw_stage(c, t, stool_scene_state(t, P, "shield", bP=warm_eyes_P(t, mouth("BRODIE", t), look=(-0.8, 0.3)),
                                           glasses=0.0, bpose="heart", kneel=kn))
        c.restore()
        twinkles(c, t, 470, 420, 200, 3, 8, "#fff6b0", 12)
        return
    P = FP(t, 3, 0, look=(0.9, 0.0), lid=0.5, lid_tilt=0.5, smile=-0.2, brow_ang=-0.4, asym=0.3)
    c.save()
    cam(c, 2.1, 370, 700)
    draw_stage(c, t, stool_scene_state(t, P, "shield", cbl=("small", 0.35), bP=warm_eyes_P(t), glasses=0.0, bpose="heart", kneel=1.0))
    c.restore()
    text(c, "...", 470, 500, "bangers", 70, "#ffffff", outline=OUT, ow=8, a=ramp(t, t_u4 + 0.4, t_u4 + 0.8))


# ======================================================================= 8. the role play

def sc_roleplay(c, t):
    s0 = M["roleplay"]
    t_ch = M["carter_chuckle"]
    t_r4 = L0("R4") - 0.1
    t_r5 = L0("R5") - 0.1
    t_r6 = L0("R6") - 0.3
    t_cheer = M["cheer"]
    shield_down = ramp(t, t_ch, t_ch + 0.7)
    cpose = "shield" if shield_down < 1 else "sit"
    cbl = ("sit", shield_down) if 0 < shield_down < 1 else None
    puppet_t = talk("R2", t, 1.2)
    chadP = FP(t, 5, 0.12 * puppet_t if speaking("R2", t) else mouth("CHAD", t), smile=-0.2 if speaking("R2", t) else 0.6,
               brow_ang=0.9 if speaking("R2", t) else 0.2, look=(0.7, -0.4) if speaking("R2", t) else (0.8, 0.1))
    chpose, chbl = pose_at(t, [(0, "puppet"), (t_r4, "open"), (t_cheer, "clap")])
    chprop = "puppet" if t < t_r4 else None
    bP = warm_eyes_P(t, mouth("BRODIE", t), look=(-0.9, -0.3) if speaking("R3", t) else (-0.8, 0.2))
    bpose, bbl = pose_at(t, [(0, "heart"), (L0("R3"), "open"), (L1("R3"), "heart"), (t_cheer, "jog")])
    kneel = 1.0 if t < t_cheer - 0.2 else 0.0
    if t < L0("R2") - 0.2:
        cam_k = (1.0, 365, 640)
    elif t < L0("R3") - 0.1:
        cam_k = (1.9, 215, 610)
    elif t < t_ch - 0.05:
        cam_k = (1.7, 520, 700)
    elif t < t_r4:
        cam_k = (2.1, 370, 700)
    elif t < t_r5:
        cam_k = (1.4, 260, 680)
    elif t < t_cheer:
        cam_k = (2.15, 365, 700)
    else:
        cam_k = (1.12, 365, 650)
    # Carter's face
    if t < t_ch:
        P = FP(t, 3, 0, look=(-0.6, -0.2) if t > L0("R2") else (0.0, 0.0), lid=0.8, smile=-0.1, brow_ang=0.3)
    elif t < t_r4:
        P = P_(t=t, lid=0.0, happy=1.0, smile=0.7, mouth_open=0.15 * abs(math.sin(t * 14)) * (1 - ramp(t, t_ch + 0.6, t_ch + 0.9)),
               blush=0.4)
    elif t < t_r5:
        P = FP(t, 3, 0, look=(-0.8, 0.0), lid=1.0, smile=0.15, brow_ang=0.5)
    elif t < t_r6:
        k = (t - t_r5) / (t_r6 - t_r5)
        if k < 0.33:
            P = FP(t, 3, 0, look=(0.3, -0.8), lid=1.05, smile=0.35, brow_ang=0.5, brow_y=0.4)
        elif k < 0.6:
            P = FP(t, 3, 0, look=(0.0, 0.0), lid=0.5, lid_tilt=0.7, smile=-0.35, brow_ang=-0.6)
        else:
            P = FP(t, 3, 0, look=(0.5, 0.5), lid=0.85, smile=0.2, asym=0.3, brow_ang=0.4, blush=0.3)
    elif t < t_cheer:
        P = FP(t, 3, mouth("CARTER", t), look=(0.0, 0.0), lid=1.0, smile=0.1, brow_ang=0.6, mouth_w=0.6, blush=0.4)
    else:
        P = FP(t, 3, 0, look=(0.7, -0.2), lid=1.1, smile=0.6, brow_y=0.5, blush=0.4)
    if t >= t_r6:
        cpose, cbl = pose_at(t, [(t_r6, "sit"), (L0("R6") - 0.05, "beep")], 0.2)
    jog = 1.0 if t > t_cheer else 0.0
    st = stool_scene_state(t, P, cpose, cbl, bP=bP, bpose=bpose, bbl=bbl, glasses=0.0, kneel=kneel, chadP=chadP,
                           chpose=chpose, chbl=chbl, chprop=chprop, puppet_talk=puppet_t, bounce=0.6 * jog)
    if jog:
        b = st["brodie"]
        b["y"] = b["y"] - 14 * abs(math.sin(t * 9))
        b["blend"] = ("hips", 0.5 + 0.5 * math.sin(t * 9))
        st["brodie"]["P"] = warm_eyes_P(t, mouth("BRODIE", t), lid=0.0, happy=1.0, smile=0.9)
    c.save()
    cam(c, *cam_k)
    draw_stage(c, t, st)
    c.restore()
    if L0("R6") - 0.05 < t < t_cheer + 0.3:
        bubble_text(c, "beep beep", 470, 500, 46, "#7ef0ff", t, L0("R6"), rot=8)
    if t_ch < t < t_ch + 0.9:
        bubble_text(c, "heh", 260, 520, 50, "#ffffff", t, t_ch, rot=-8)
    if t > t_cheer:
        comic_text(c, "BEST TREADMILL EVER!", 360, 520, 56, "#ffd23f", t, t_cheer + 0.3, -4, False)
    if t_r5 < t < t_r6:
        k = (t - t_r5) / (t_r6 - t_r5)
        sym = "?" if k < 0.33 else "!" if k < 0.6 else "..."
        text(c, sym, 500, 420, "bangers", 90, "#ffffff", outline=OUT, ow=9)


# ======================================================================= 9. the bomb

def sc_bomb(c, t):
    s0 = M["bomb"]
    t_cr = L1("B1") + 0.05
    t_b2 = L0("B2") - 0.05
    t_b3 = L0("B3") - 0.05
    t_up = t_b3 + 1.75
    if t < t_cr:
        guns = ramp(t, L1("B1") - 1.5, L1("B1") - 1.2)
        cP = FP(t, 5, mouth("CHAD", t), smile=0.9, brow_y=0.6, teeth=True)
        bP = FP(t, 6, 0, smile=0.8)
        c.save()
        cam(c, 1.45, 300, 650)
        draw_stage(c, t, stage_bros(t, bP, cP, "hips", "mic", cbl=("guns", guns) if guns > 0 else None, cprop="mic", glasses=0.0))
        c.restore()
        return
    if t < t_b2:
        lt = t - t_cr
        c.save()
        cam(c, 1.0, 360, 640)

        def floor_fn(c_):
            tumbleweed(c_, lerp(-100, 820, lt / (t_b2 - t_cr)), 1140 - 40 * abs(math.sin(lt * 5)), 75, lt)

        def seat_fn(seat):
            if seat is COUGHER and t > s0 + 5.6:
                return dict(P=P_(t=t, lid=0.0, squeeze=1.0, mouth_open=0.4 * pulse(t, s0 + 5.6, 0.6), mouth_w=0.6, smile=0.0))
            return None

        bleachers(c, t, "blank", friends=1.0, floor_fn=floor_fn, seat_fn=seat_fn,
                  carter_fn=None)
        c.restore()
        text(c, "*crickets*", 360, 260, "fredoka", 40, "#ffffff", outline=OUT, ow=7, a=ramp(t, t_cr + 0.2, t_cr + 0.5))
        return
    if t < t_b3:
        bP = FP(t, 6, mouth("BRODIE", t), clench=0.0 if speaking("B2", t) else 0.7, smile=0.4, sweat=0.8, brow_ang=0.6, lid=1.0,
                pr=0.8)
        cP = FP(t, 5, 0, clench=0.7, smile=0.3, sweat=0.8, brow_ang=0.6)
        c.save()
        cam(c, 1.55, 430, 645)
        draw_stage(c, t, stage_bros(t, bP, cP, "thumbs", "stand", cprop="puppet", glasses=0.0))
        c.restore()
        return
    # Carter: they need my comedy
    up = ramp(t, t_up, t_up + 0.5)
    if t < t_up:
        P = FP(t, 3, 0, lid=0.4, smile=-0.3, brow_ang=0.3)
        pose, bl = "facepalm", None
    else:
        P = FP(t, 3, 0, look=(0.0, -0.1), lid=0.8, lid_tilt=0.5, smile=0.45, asym=0.3, brow_ang=-0.5, brow_y=0.2)
        pose, bl = "facepalm", ("fists", up)
    c.save()
    cam(c, lerp(2.0, 1.6, up), 365, lerp(720, 660, up))
    st = stool_scene_state(t, P, pose, bl, bP=FP(t, 6, 0, sweat=0.6, smile=0.2, clench=0.5), glasses=0.0, bpose="thumbs",
                           chadP=FP(t, 5, 0, sweat=0.6, smile=0.2, clench=0.5), chprop="puppet", chpose="puppet")
    st["carter"]["y"] = CARTER_STOOL[1] - 60 * up
    st["carter"]["legs"] = "stand" if up > 0.5 else "sit"
    if up > 0:
        st["pre"] = lambda c_: speed_lines(c_, 365, 720, t, 40, "#ffd23f", 0.45 * up, 150)
    draw_stage(c, t, st)
    c.restore()


# ======================================================================= 10. Carter saves them

def sc_saves(c, t):
    s0 = M["saves"]
    t_lb = L1("B4") + 0.05
    t_b5 = L0("B5") - 0.1
    t_lh = L1("B5") + 0.05
    t_gl = M["glance1"] - 0.3
    spot = 1.0
    cart = (365, 795, 0.5)
    if t < t_lb or t_b5 <= t < t_lh:
        b4 = t < t_lb
        k = (t - s0) / (t_lb - s0)
        if b4:
            pose, bl = pose_at(t, [(s0, "perform"), (s0 + 1.3, "point"), (s0 + 3.0, "shrug")])
        else:
            pose, bl = pose_at(t, [(t_b5, "point")])
        px = -0.9 if (b4 and 1.3 < t - s0 < 3.0) else 0.9 if not b4 else 0.0
        P = FP(t, 3, mouth("CARTER", t), look=(px, 0.0), lid=0.7 if (b4 and t - s0 > 3.0) else 1.0,
               smile=0.6, brow_y=0.4, teeth=True)
        cP = FP(t, 5, 0, look=(0.8, 0), smile=0.5, brow_ang=0.6)
        hug = not b4
        bP = warm_eyes_P(t, 0, look=(-0.7, 0), blush=0.6 if hug else 0.2, smile=0.6)
        st = dict(chad=chad_st(t, cP, "puppet", prop="puppet", puppet_talk=0.0),
                  brodie=brodie_st(t, bP, "hug" if hug else "hips", glasses=0.0, prop="shake" if hug else None),
                  carter=dict(x=cart[0], y=cart[1], s=cart[2], P=P, pose=pose, blend=bl, legs="stand", mic=pose != "point"),
                  stool=False, bounce=0.0)
        z, cx, cy = (1.6, 340, 650) if b4 and t - s0 < 1.3 else (1.15, 365, 660)
        if not b4:
            z, cx, cy = (1.3, 470, 660)
        c.save()
        cam(c, z, cx, cy)
        draw_stage(c, t, st)
        c.restore()
        c.drawRect(skia.Rect.MakeWH(W, H), rad_grad(360, 600, 700, ["#000000", "#000000"], [0.4, 1], [0.0, 0.35 * spot]))
        return
    if t < t_b5 or t < t_gl:
        # the crowd loses it
        c.save()
        cam(c, 1.05, 360, 640, shake=0.3, t=t)
        bleachers(c, t, "laugh", friends=1.0)
        c.restore()
        big = t >= t_lh
        for i in range(7 if big else 4):
            ph = (t * 0.8 + i / 7) % 1.0
            x = 80 + 560 * (hash1(i * 13) * 0.5 + 0.5)
            y = 300 + 600 * (hash1(i * 7) * 0.5 + 0.5)
            text(c, "HA", x, y - 60 * ph, "bangers", 56, "#ffd23f", outline=OUT, ow=7, a=math.sin(math.pi * ph))
        return
    # the knowing glance (Carter basking in front)
    lt = t - t_gl
    glance = ramp(t, M["glance1"], M["glance1"] + 0.3)
    bP = warm_eyes_P(t, 0, look=(lerp(0, -1.0, glance), 0.0), lid=lerp(1.0, 0.75, glance), smile=0.55, asym=0.3 * glance)
    cP = FP(t, 5, 0, look=(lerp(0, 1.0, glance), 0.0), lid=lerp(1.0, 0.75, glance), smile=0.55, asym=-0.3 * glance,
            browL=0.4 * glance)
    P = P_(t=t, lid=0.0, happy=1.0, smile=0.85, blush=0.4)
    c.save()
    cam(c, 1.8, 365, 560)
    st = dict(chad=chad_st(t, cP, "stand", at_=(250, 740, 0.6)), brodie=brodie_st(t, bP, "hips", glasses=0.0, at_=(485, 740, 0.6)),
              carter=dict(x=365, y=820, s=0.55, P=P, pose="proud", legs="stand", mic=False), stool=False, heads=False)
    draw_stage(c, t, st)
    c.restore()
    if glance > 0.5:
        sparkle_star(c, 360, 330, 30 * pulse(t, M["glance1"] + 0.3, 0.6), 1.0, "#fff6b0")


# ======================================================================= 11. afterwards

def sc_after(c, t):
    s0 = M["after"]
    t_leave = M["carter_leaves"]
    fl = ramp(t, s0, s0 + 0.6)
    cart_x = lerp(370, 900, ramp(t, t_leave, t_leave + 1.6))
    z, cx, cy = kf(t, [(s0, (1.3, 370, 720)), (L0("A2") - 0.2, (1.3, 370, 720)), (L0("A2") + 0.3, (1.2, 450, 700)),
                       (L0("A3") - 0.2, (1.2, 450, 700)), (L0("A3") + 0.2, (1.35, 380, 740)), (t_leave, (1.35, 380, 740)),
                       (t_leave + 0.8, (1.1, 360, 680))])
    c.save()
    cam(c, z, cx, cy)
    bg_office(c, t)
    bpose, bbl = pose_at(t, [(0, "hips"), (L0("A4"), "heart"), (L1("A5") - 1.0, "glasses")])
    cpose, cbl = pose_at(t, [(0, "clap"), (L0("A2"), "plead"), (L1("A2"), "stand"), (L0("A5"), "chin")])
    shades = ramp(t, L1("A5") - 0.6, L1("A5") + 0.1)
    bP = warm_eyes_P(t, mouth("BRODIE", t), look=(0.7, 0.3) if t < t_leave else (0.9, 0) if t < L0("A4") + 0.6 else (0.8, 0))
    cP = FP(t, 5, mouth("CHAD", t), look=(-0.8, 0.3) if t < t_leave else (0.8, 0) if t < L0("A5") else (-0.8, 0),
            smile=0.6, pr=1.25 if speaking("A2", t) else 1.0, brow_ang=0.7 if speaking("A2", t) else 0.2,
            lid_tilt=0.2 if t > L0("A5") + 1.2 else 0.0, asym=0.3 if t > L0("A5") + 1.2 else 0.0)
    put(c, 170, 700, 0.62, brodie, bP, t, bpose, bbl, glasses=shades)
    put(c, 560, 705, 0.62, chad, cP, t, cpose, cbl)
    roll = pulse(t, L0("A3"), 0.8)
    if t < L0("A3"):
        P = FP(t, 3, mouth("CARTER", t), look=(0.2, -0.8), lid=0.5, smile=0.7, asym=0.3, brow_y=0.3)
        pose = "proud"
    else:
        P = FP(t, 3, mouth("CARTER", t), look=(0.1, -0.95 * roll), lid=0.6, smile=0.35, asym=0.4)
        pose = "shrug" if t < t_leave else "proud"
    put(c, cart_x, 880, 0.6, carter, P, t, pose, None, legs="stand", fluff=fl, walk=1.0 if t > t_leave else 0.0)
    if t < t_leave:
        twinkles(c, t, cart_x - 160, 560, 320, 6, 2, "#fff6b0", 16)
    c.restore()
    if shades > 0.95:
        sparkle_star(c, 205, 340, 26 * pulse(t, L1("A5") + 0.1, 0.5), 1.0)


# ======================================================================= 12. the next assembly: the reveal

def sc_assembly2(c, t):
    s0 = M["assembly2"]
    t_c1 = L0("C1") - 0.2
    t_cr = L1("C1") + 0.1
    t_c2 = L0("C2") - 0.1
    t_now = M["now"]
    t_big = M["bigbit"]
    t_crowd_end = t_big + 2.2
    t_c5 = L0("C5") - 0.25
    t_c6 = L0("C6") - 0.1
    mic_cart = (365, 795, 0.5)
    if t < t_cr:
        P = FP(t, 3, mouth("CARTER", t), smile=0.6, lid=0.85, brow_y=0.3, lidR=0.0 if t > L1("C1") - 0.25 else None,
               teeth=True)
        st = stage_bros(t, FP(t, 6, 0, smile=0.4), FP(t, 5, 0, smile=0.5, look=(0.7, 0)), "crossed", "stand", cprop=None,
                        glasses=1.0, stool=False, banner="FEELINGS ASSEMBLY 2", sub="(featuring Carter)", cat=CHAD_AT, bat=BRODIE_AT)
        st["carter"] = dict(x=mic_cart[0], y=mic_cart[1], s=mic_cart[2], P=P, pose="perform", legs="stand", mic=True)
        z, cx, cy = (1.0, 360, 640) if t < t_c1 else (1.55, 365, 650)
        c.save()
        cam(c, z, cx, cy)
        draw_stage(c, t, st)
        c.restore()
        if t < t_c1 + 0.2:
            a = 1 - ramp(t, t_c1 - 0.3, t_c1 + 0.1)
            text(c, "THE NEXT ASSEMBLY", 360, 1120, "bangers", 84, "#ffd23f", outline=OUT, ow=11, a=a)
        return
    if t < t_c2:
        c.save()
        cam(c, 1.0, 360, 640)

        def seat_fn(seat):
            if seat["i"] % 9 == 4:
                return dict(P=P_(t=t, lid=0.0, mouth_open=0.7 * pulse(t, t_cr + 0.2, 1.2), mouth_w=0.6, smile=0.0))
            return None

        bleachers(c, t, "blank", friends=1.0, seat_fn=seat_fn)
        c.restore()
        text(c, "*crickets*", 360, 260, "fredoka", 40, "#ffffff", outline=OUT, ow=7, a=ramp(t, t_cr + 0.2, t_cr + 0.5))
        return
    if t < t_now:
        k = (t - t_c2) / (t_now - t_c2)
        look = (-0.9, 0.0) if k < 0.45 else (0.9, 0.0)
        P = FP(t, 3, 0, look=look, noblink=True, lid=1.1, pr=0.5, sweat=1.0, wobble=0.7, smile=-0.2, brow_ang=0.9, red=0.3)
        st = stage_bros(t, FP(t, 6, 0, smile=0.3), FP(t, 5, 0, smile=0.4), "crossed", "stand", cprop=None, glasses=1.0, stool=False,
                        banner="FEELINGS ASSEMBLY 2", sub="(featuring Carter)", cat=CHAD_AT, bat=BRODIE_AT)
        st["carter"] = dict(x=mic_cart[0], y=mic_cart[1], s=mic_cart[2], P=P, pose="hold_mic", legs="stand", mic=True, shake=0.4)
        c.save()
        cam(c, 2.1, 365, 680)
        draw_stage(c, t, st)
        c.restore()
        return
    if t < t_big + 0.1:
        # the bros' real bit: spotting each other
        nod = pulse(t, t_now + 0.1, 0.5)
        press = ramp(t, L0("C3") + 0.3, L0("C3") + 0.9)
        bP = FP(t, 6, mouth("BRODIE", t), smile=0.7, brow_y=0.4)
        cP = FP(t, 5, mouth("CHAD", t), smile=0.7, brow_y=0.4, look=(0.8, -0.3))
        bpose, bbl = ("hips", ("press", press)) if press < 1 else ("press", None)
        cpose, cbl = ("stand", ("spot", press)) if press < 1 else ("spot", None)
        if t > L0("C4") + 1.0:
            cpose, cbl = "guns", None
        P = FP(t, 3, 0, look=(0.3, -0.6), lid=0.9, smile=0.0, brow_ang=0.4, sweat=0.4)
        st = dict(chad=chad_st(t, cP, cpose, cbl, at_=(305, 745 + 4 * nod, 0.6)),
                  brodie=brodie_st(t, bP, bpose, bbl, glasses=1.0, prop="barbell" if press > 0.3 else None, at_=(470, 740, 0.6)),
                  carter=dict(x=640, y=860, s=0.45, P=P, pose="hold_mic", legs="stand", mic=True), stool=False,
                  banner="FEELINGS ASSEMBLY 2", sub="(featuring Carter)")
        c.save()
        cam(c, 1.15, 400, 600)
        draw_stage(c, t, st)
        c.restore()
        if t_now < t < t_now + 0.8:
            text(c, "*nod*", 360, 330, "fredoka", 40, "#ffffff", outline=OUT, ow=7)
        return
    if t < t_crowd_end:
        c.save()
        cam(c, 1.05, 360, 640, shake=0.5, t=t)
        bleachers(c, t, "laugh", friends=1.0)
        c.restore()
        confetti(c, t, t_big)
        comic_text(c, "BA-DUM TSS!", 360, 330, 90, "#ffd23f", t, t_big + 0.05, -5, True, "#3a86ff")
        return
    if t < t_c6:
        # Carter: you were funny this whole time?!
        jaw = ramp(t, t_crowd_end, t_crowd_end + 0.3)
        P = FP(t, 3, max(mouth("CARTER", t), 0.9 * jaw if t < t_c5 + 0.3 else 0), noblink=True, lid=1.2, pr=0.55, smile=-0.2,
               brow_y=0.9, brow_ang=0.3)
        bP = FP(t, 6, 0, smile=0.8)
        cP = FP(t, 5, 0, lid=0.0, happy=1.0, smile=0.8)
        st = dict(chad=chad_st(t, cP, "wave", at_=(205, 745, 0.6)), brodie=brodie_st(t, bP, "flex", glasses=1.0, at_=(525, 740, 0.6)),
                  carter=dict(x=365, y=850, s=0.55, P=P, pose="shrug" if t > t_c5 else "hold_mic", legs="stand", mic=t <= t_c5),
                  stool=False, banner="FEELINGS ASSEMBLY 2", sub="(featuring Carter)", bounce=0.5)
        c.save()
        cam(c, 1.75, 365, 700)
        draw_stage(c, t, st)
        c.restore()
        confetti(c, t, t_big)
        return
    # Chad: we toned it down, bro. so you could shine
    off = ramp(t, t_c6 + 0.6, t_c6 + 1.4)
    bP = warm_eyes_P(t, 0, look=(-0.6, 0.3)) if off > 0.5 else FP(t, 6, 0, smile=0.5)
    cP = FP(t, 5, mouth("CHAD", t), look=(0.6, 0.3), smile=0.55, brow_ang=0.45, pr=1.15)
    P = FP(t, 3, 0, look=(-0.6, -0.4), lid=1.1, pr=0.7, smile=-0.25, brow_ang=0.6, mouth_open=0.15)
    st = dict(chad=chad_st(t, cP, "heart", at_=(205, 745, 0.6)),
              brodie=brodie_st(t, bP, "glasses" if off < 1 else "heart", glasses=1 - off, hold_glasses=0.2 < off < 1, at_=(525, 740, 0.6)),
              carter=dict(x=365, y=850, s=0.55, P=P, pose="small", legs="stand"), stool=False,
              banner="FEELINGS ASSEMBLY 2", sub="(featuring Carter)")
    c.save()
    cam(c, 1.45, 330, 680)
    draw_stage(c, t, st)
    c.restore()
    confetti(c, t, t_big)


# ======================================================================= 13. going solo

def sc_solo(c, t):
    s0 = M["solo"]
    t_m = M["montage"]
    t_d3 = L0("D3") - 0.15
    if t < t_m:
        storm = ramp(t, L1("D1") - 0.2, L1("D1") + 0.6)
        P = FP(t, 3, mouth("CARTER", t), lid=0.7, lid_tilt=0.8, smile=-0.6, brow_ang=-1.0, red=0.9, teeth=True)
        bP = FP(t, 6, 0, smile=-0.1, brow_ang=0.7, look=(-0.7, 0.3))
        cP = FP(t, 5, 0, smile=-0.1, brow_ang=0.8, look=(0.7, 0.3), lid=0.85)
        st = dict(chad=chad_st(t, cP, "open", at_=(160, 745, 0.6)), brodie=brodie_st(t, bP, "open", glasses=0.0, at_=(570, 740, 0.6)),
                  carter=dict(x=lerp(365, 820, storm), y=850, s=0.55, P=P, pose="stomp", legs="stand", shake=0.5 * (1 - storm),
                              walk=storm), stool=False, banner="FEELINGS ASSEMBLY 2", sub="(featuring Carter)")
        c.save()
        cam(c, 1.4, 365, 690)
        draw_stage(c, t, st)
        c.restore()
        return
    if t < t_d3:
        k = (t - t_m) / (t_d3 - t_m)
        i = min(2, int(k * 3))
        lt = t - (t_m + i * (t_d3 - t_m) / 3)
        desat_begin(c, 0.85)
        c.drawRect(BIG, fill("#15151c"))
        c.drawPath(poly([(300, -20), (420, -20), (560, 1060), (170, 1060)]), fill("#fff6d8", 0.22))
        c.drawPath(oval(365, 1050, 200, 40), fill("#fff6d8", 0.35))
        pose = ["perform", "proud", "hold_mic"][i]
        P = P_(t=t, lid=[0.85, 0.0, 0.7][i], happy=1.0 if i == 1 else 0.0, smile=[0.6, 0.6, 0.15][i], mouth_open=0.3 if i == 0 else 0.0,
               teeth=i == 0)
        put(c, 365 + [0, 0, 60 * lt][i], 800, 0.85, carter, P, t, pose, None, legs="stand", mic=i != 1, walk=1.0 if i == 2 else 0.0)
        heads_back(c, t, 1265, 0.8, 5)
        for j in range(5):
            ph = (t * 0.7 + j / 5) % 1.0
            x = 80 + 560 * (hash1(j * 13 + i) * 0.5 + 0.5)
            y = 260 + 400 * (hash1(j * 7 + i) * 0.5 + 0.5)
            text(c, "ha", x, y - 40 * ph, "bangers", 48, "#cccccc", outline=OUT, ow=6, a=0.7 * math.sin(math.pi * ph))
        c.restore()
        if lt < 0.12:
            c.drawRect(skia.Rect.MakeWH(W, H), fill("#ffffff", 0.3 * (1 - lt / 0.12)))
        return
    # the empty gym
    desat_begin(c, 0.55)
    c.save()
    cam(c, lerp(1.55, 1.8, smooth((t - t_d3) / 2.6)), 365, 790)
    bg_gym(c, t, "FEELINGS ASSEMBLY 2", "(featuring Carter)", 0.0)
    c.drawRect(BIG, fill("#0a0a20", 0.45))
    c.drawPath(poly([(320, -20), (410, -20), (520, 1000), (210, 1000)]), fill("#fff6d8", 0.18))
    stool(c, 365, 905)
    P = FP(t, 3, 0, look=(0.0, 0.6), lid=0.7, smile=-0.3, brow_ang=0.7, period=5.0)
    put(c, 365, 852, 0.5, carter, P, t, "small", None, legs="sit")
    c.restore()
    c.restore()
    vignette(c, 0.6)


# ======================================================================= 14. the door

def slug_bubble(c, t, x, y, a):
    c.saveLayerAlpha(None, int(255 * a))
    for k, (dx, dy, r) in enumerate(((-130, 210, 12), (-110, 175, 18))):
        c.drawCircle(x + dx, y + dy, r, fill("#ffffff"))
        c.drawCircle(x + dx, y + dy, r, stroke(OUT, 4))
    p = cloud(x, y, 440, 300, 10, t, 5)
    fs(c, p, "#ffffff", 5)
    # Carter as a little slug (beanie on), crawling
    sx = x - 40 + 30 * math.sin(t * 1.5)
    body = smooth_path([(sx - 110, y + 70), (sx - 60, y + 40), (sx + 40, y + 10), (sx + 80, y - 20), (sx + 110, y + 10),
                        (sx + 100, y + 70)])
    fs(c, body, "#c7a3ff", 5)
    for s in (-1, 1):
        c.drawPath(poly([(sx + 85 + s * 10, y - 15), (sx + 85 + s * 22, y - 55)], False), stroke(OUT, 4))
        c.drawCircle(sx + 85 + s * 22, y - 58, 7, fill(OUT))
    hat = smooth_path([(sx + 55, y - 10), (sx + 70, y - 52), (sx + 110, y - 52), (sx + 120, y - 10)])
    fs(c, hat, "#2a9d6f", 4)
    c.drawCircle(sx + 90, y - 58, 9, fill("#ff8c42"))
    c.drawPath(poly([(sx - 140, y + 74), (sx - 300, y + 76)], False), stroke("#c7a3ff", 5, 0.6))
    text(c, "HA HA HA", x + 70, y - 90, "bangers", 40, "#e63946", outline=OUT, ow=5)
    text(c, "look who's back", x, y + 125, "fredoka", 26, "#444444")
    c.restore()


def hallway(c, t, night=True):
    c.drawRect(BIG, lin_grad(0, 0, 0, H, ["#1a2240", "#10162c"] if night else ["#c9d3e0", "#aab6c4"]))
    for k in range(-2, 9):
        x = k * 92
        fs(c, rrect(x, 330, 86, 520, 6), "#2f4a7a" if night else "#3a86ff", 5)
        for j in range(4):
            c.drawPath(poly([(x + 22, 360 + j * 14), (x + 64, 360 + j * 14)], False), stroke(OUT, 3, 0.6))
        c.drawRect(skia.Rect.MakeXYWH(x + 64, 560, 10, 34), fill("#c0c0c8"))
    c.drawRect(skia.Rect.MakeLTRB(-800, 850, W + 800, H + 800), lin_grad(0, 850, 0, H, ["#3a3f5c", "#23263a"] if night else ["#9aa0aa", "#7a808a"]))
    c.drawPath(poly([(-800, 850), (W + 800, 850)], False), stroke(OUT, 6))


def sc_door(c, t):
    s0 = M["door"]
    t_o = M["door_open"]
    t_d7 = L0("D7") - 0.15
    if t < t_o + 0.25:
        c.save()
        cam(c, kf(t, [(s0, 1.0), (t_o, 1.12)]), 360, 640)
        hallway(c, t)
        # the principal's door, ajar, warm light
        op = ramp(t, t_o - 0.1, t_o + 0.25)
        gap = lerp(36, 160, op)
        c.drawPath(poly([(470, 300), (470 + gap, 300), (470 + gap * 3, 1280), (470, 1280)]), fill("#ffcf7a", 0.28))
        c.drawRect(skia.Rect.MakeLTRB(470, 300, 470 + gap, 850), fill("#ffcf7a", 0.9))
        fs(c, poly([(470 + gap, 300), (630 + gap, 280), (630 + gap, 870), (470 + gap, 850)]), "#7a4a2a", 6)
        fs(c, rrect(470 + gap + 30, 360, 110, 40, 6), "#f4f1de", 4)
        text(c, "PRINCIPAL", 470 + gap + 85, 388, "inter_black", 16, "#23395d")
        walk = ramp(t, s0, s0 + 1.2)
        stop = t > s0 + 1.2
        P = FP(t, 3, 0, look=(0.9, 0.1), lid=0.85, smile=-0.25, brow_ang=0.7, period=4.0)
        put(c, lerp(60, 300, walk), 790, 0.74, carter, P, t, "small", None, legs="stand", walk=0.0 if stop else 0.7)
        c.restore()
        if L0("D4") - 0.1 < t < t_o + 0.1:
            slug_bubble(c, t, 380, 330, ramp(t, L0("D4") - 0.1, L0("D4") + 0.2) * (1 - ramp(t, t_o - 0.1, t_o + 0.1)))
        return
    if t < t_d7:
        # inside: they light up
        c.save()
        cam(c, 1.15, 360, 680)
        bg_office(c, t, night=True)
        fs(c, oval(360, 975, 230, 40), "#8a5a34", 6)
        fs(c, rrect(345, 990, 30, 160, 6), "#6f4526", 5)
        for x in (300, 420):
            fs(c, rrect(x - 22, 880, 44, 92, 10), "#f4f1de", 4)
            fs(c, rrect(x - 26, 868, 52, 18, 6), "#2a9d6f", 4)
        # empty chair (saved seat)
        fs(c, rrect(300, 760, 120, 140, 16), "#e63946", 5)
        text(c, "CARTER", 360, 840, "bangers", 30, "#ffffff")
        bpose, bbl = pose_at(t, [(0, "stand"), (L0("D5") + 0.2, "wave"), (L1("D5"), "heart")])
        bP = warm_eyes_P(t, mouth("BRODIE", t), smile=0.85, lid=1.05)
        cP = FP(t, 5, mouth("CHAD", t), smile=0.7, brow_ang=0.45, pr=1.2)
        put(c, 140, 700, 0.6, brodie, bP, t, bpose, bbl, glasses=0.0)
        put(c, 590, 705, 0.6, chad, cP, t, "open" if t > L0("D6") else "stand", None)
        c.restore()
        return
    # Carter: ...yeah. okay.
    P = FP(t, 3, mouth("CARTER", t), look=(0.0, 0.25), lid=0.9, smile=0.35, blush=0.6, tears=0.35, brow_ang=0.5, period=5.0)
    c.save()
    cam(c, 1.0, 360, 640)
    hallway(c, t)
    c.drawRect(BIG, rad_grad(360, 560, 650, ["#ffcf7a", "#ffcf7a"], [0, 1], [0.5, 0]))
    put(c, 360, 860, 1.05, carter, P, t, "small", None, legs="stand")
    c.restore()


# ======================================================================= 15. the roast + the heckler

def sc_roast(c, t):
    s0 = M["roast"]
    t_e2 = L0("E2") - 0.1
    t_lb = M["chad_laughs"]
    t_h = M["heckle"] - 0.05
    t_bl = M["bros_look"]
    banner = "THE ROAST ASSEMBLY"
    sub = "(they're in on it)"
    if t < t_lb:
        e2 = t >= t_e2
        n_lt = (t - s0) % 2.8
        laugh_nar = (not e2) and n_lt > 1.6
        P = FP(t, 3, mouth("CARTER", t), look=(-0.9 if e2 else 0.8, 0), smile=0.6, brow_y=0.3, teeth=True)
        cP = FP(t, 5, 0, lid=0.0 if (laugh_nar or t > L1("E2") - 0.3) else 1.0, happy=1.0, smile=0.8,
                mouth_open=0.3 if laugh_nar else 0.0)
        bP = FP(t, 6, 0, lid=0.0 if laugh_nar else 1.0, happy=1.0, smile=0.8, mouth_open=0.35 if laugh_nar else 0.0)
        st = dict(chad=chad_st(t, cP, "laugh" if laugh_nar else "stand"),
                  brodie=brodie_st(t, bP, "hug" if laugh_nar else "hips", glasses=1.0),
                  carter=dict(x=365, y=795, s=0.5, P=P, pose="point" if not e2 else "perform", legs="stand", mic=e2),
                  stool=False, banner=banner, sub=sub, bounce=0.6 if laugh_nar else 0.0)
        if e2:
            st["carter"]["pose"] = "perform"
            st["carter"]["blend"] = ("point", 0.0)
        z, cx, cy = (1.0, 360, 640) if not e2 else (1.35, 290, 660)
        c.save()
        cam(c, z, cx, cy)
        draw_stage(c, t, st)
        c.restore()
        return
    if t < t_h:
        cP = FP(t, 5, 0, lid=0.0, happy=1.0, smile=0.9, mouth_open=0.4 + 0.2 * math.sin(t * 12), tears=0.8)
        bP = FP(t, 6, 0, lid=0.0, happy=1.0, smile=0.9, mouth_open=0.4 + 0.2 * math.sin(t * 11 + 1))
        P = FP(t, 3, 0, lid=0.0, happy=1.0, smile=0.8)
        st = dict(chad=chad_st(t, cP, "wipe", tears=0.8), brodie=brodie_st(t, bP, "hug", glasses=1.0),
                  carter=dict(x=365, y=795, s=0.5, P=P, pose="proud", legs="stand", mic=False),
                  stool=False, banner=banner, sub=sub, bounce=1.0)
        c.save()
        cam(c, 1.15, 360, 650)
        draw_stage(c, t, st)
        c.restore()
        return
    if t < t_bl:
        hm = mouth("HECKLER", t)

        def seat_fn(seat):
            if seat is HECKLER:
                return dict(P=FP(t, 81, hm, look=(-0.6, 0.3), smile=0.5, asym=0.4, brow_ang=-0.6, lid=0.8), dy=-40)
            return None

        def mode(seat):
            return "gasp" if t > L1("E3") - 0.3 else "watch"

        c.save()
        cam(c, 1.75, HECKLER["x"] - 60, HECKLER["y"] + 60)
        bleachers(c, t, mode, target=(HECKLER["x"], HECKLER["y"] - 40), friends=1.0, seat_fn=seat_fn)
        c.restore()
        return
    # the bros' smiles fade; Carter notices
    fade = ramp(t, t_bl, t_bl + 0.6)
    cP = FP(t, 5, 0, look=(0.8 * fade, 0.0), smile=lerp(0.6, 0.0, fade), brow_ang=0.7 * fade, lid=1.0)
    bP = FP(t, 6, 0, smile=lerp(0.6, 0.05, fade), brow_ang=0.6 * fade)
    P = FP(t, 3, 0, look=(lerp(-0.8, 0.6, fade), lerp(0.0, -0.7, fade)), lid=0.8, lid_tilt=0.5 * fade, smile=-0.2 * fade,
           brow_ang=-0.5 * fade)
    st = dict(chad=chad_st(t, cP, "stand"), brodie=brodie_st(t, bP, "stand", glasses=lerp(1.0, 0.0, fade)),
              carter=dict(x=365, y=795, s=0.5, P=P, pose="hold_mic", legs="stand", mic=True),
              stool=False, banner=banner, sub=sub)
    c.save()
    cam(c, 1.5, 365, 640)
    draw_stage(c, t, st)
    c.restore()


# ======================================================================= 16. Carter has their backs

def standing_kid(c, t, look, P, x, y, s, cap=None, hair=0, lean=0.0, hands_pocket=True):
    at(c, x, y, s, lean)
    for k in (-1, 1):
        fs(c, rrect(k * 40 - 30, 140, 60, 170, 20), "#3a3f5c", 5)
        fs(c, oval(k * 44, 312, 42, 18), "#1d1d22", 4)
    kid(c, look, P, t, hair, cap, False, 1.0, 0.0)
    c.restore()


def sc_defend(c, t):
    s0 = M["defend"]
    t_k = M["knowing"] - 0.15
    if t < t_k:
        walk = ramp(t, s0, s0 + 0.6)
        c.save()
        z, cx, cy = kf(t, [(s0, (1.0, 360, 640)), (L0("E5") - 0.2, (1.05, 380, 640)), (L0("E5") + 0.2, (1.25, 470, 640))])
        cam(c, z, cx, cy)
        hallway(c, t, night=False)
        # the gym doors at the back, with two very large men peeking
        fs(c, rrect(250, 300, 240, 550, 6), "#8a5a34", 6)
        c.drawRect(skia.Rect.MakeLTRB(358, 300, 382, 850), fill("#2b1a10"))
        peek = ramp(t, L0("E4") + 1.5, L0("E4") + 2.2)
        if peek > 0:
            c.save()
            c.clipRect(skia.Rect.MakeLTRB(358, 300, 382 + 30 * peek, 850))
            put(c, 380, 520, 0.35, brodie, warm_eyes_P(t, 0, look=(0.6, 0.3)), t, "stand", glasses=0.0)
            put(c, 380, 680, 0.33, chad, FP(t, 5, 0, look=(0.6, 0.3), smile=0.5), t, "stand")
            c.restore()
        text(c, "GYM", 370, 280, "inter_black", 30, "#23395d")
        hm = mouth("HECKLER", t)
        sorry = t > L0("E5") - 0.2
        hP = FP(t, 81, hm, look=(-0.8, 0.5 if sorry else 0.0), smile=-0.1 if sorry else 0.2, brow_ang=0.7 if sorry else 0.0,
                lid=0.85 if sorry else 1.0, asym=0.3)
        standing_kid(c, t, (SKIN_A, "#b5651d", "#8338ec"), hP, 560, 700, 0.95, "#222233", 0, -4 if sorry else 0)
        cm = mouth("CARTER", t)
        P = FP(t, 3, cm, look=(0.9, -0.2), lid=0.95, lid_tilt=0.25, smile=0.0, brow_ang=-0.3)
        if sorry:
            P = FP(t, 3, 0, look=(0.9, 0.0), lid=0.9, smile=0.3, brow_ang=0.0)
        put(c, lerp(-120, 230, walk), 840, 0.62, carter, P, t, "cross" if walk >= 1 else "small", None, legs="stand",
            walk=1.0 if walk < 1 else 0.0)
        c.restore()
        return
    # the knowing look, peeking through the gym doors
    lt = t - t_k
    glance = ramp(t, t_k + 0.3, t_k + 0.7)
    c.save()
    cam(c, 1.0, 360, 640)
    c.drawRect(BIG, fill("#2b1a10"))
    c.drawRect(skia.Rect.MakeLTRB(240, 0, 480, H), lin_grad(0, 0, 0, H, ["#c9d3e0", "#9aa0aa"]))
    bP = warm_eyes_P(t, mouth("BRODIE", t), look=(lerp(-0.9, 0.0, 0), 0.6) if glance < 0.5 else (0.0, 0.9), lid=0.8, smile=0.6,
                     asym=0.3)
    cP = FP(t, 5, mouth("CHAD", t), look=(-0.6, 0.0) if glance < 0.5 else (0.0, -0.9), lid=0.8, smile=0.6, asym=-0.3,
            tears=0.5, brow_ang=0.3)
    put(c, 360, 640, 0.95, brodie, bP, t, "stand", glasses=0.0)
    put(c, 360, 1000, 0.9, chad, cP, t, "stand")
    # the doors
    for x0, x1, sgn in ((-100, 260, 1), (460, 820, -1)):
        fs(c, rrect(x0, -40, x1 - x0, H + 80, 6), "#8a5a34", 8)
        fs(c, rrect(x0 + 60 if sgn > 0 else x0 + 40, 300, 260, 260, 10), "#c9e4ff", 6)
        c.drawRect(skia.Rect.MakeXYWH(x1 - 60 if sgn > 0 else x0 + 30, 640, 30, 120), fill("#c0c0c8"))
    c.restore()
    if t > L0("E7") + 0.3:
        sparkle_star(c, 360, 300, 36 * pulse(t, L0("E7") + 0.3, 0.6), 1.0, "#fff6b0")


# ======================================================================= 17. end card

def sc_end(c, t):
    s0 = M["end"]
    lt = t - s0
    c.drawRect(BIG, rad_grad(360, 640, 900, ["#ffb36b", "#e63946"], [0, 1]))
    for i in range(16):
        a = math.radians(i * 22.5 + lt * 10)
        p = skia.Path()
        p.moveTo(360, 720)
        p.lineTo(360 + 1500 * math.cos(a - 0.08), 720 + 1500 * math.sin(a - 0.08))
        p.lineTo(360 + 1500 * math.cos(a + 0.08), 720 + 1500 * math.sin(a + 0.08))
        p.close()
        c.drawPath(p, fill("#ffffff", 0.08))
    u = ease_out_back(clamp(lt / 0.5), 2)
    at(c, 360, 180, u, -3)
    text(c, "FEELINGS ARE THE", 0, 0, "bangers", 74, "#ffffff", outline=OUT, ow=11, shadow=True)
    text(c, "ULTIMATE GAINS", 0, 100, "bangers", 104, "#ffd23f", outline=OUT, ow=14, shadow=True)
    c.restore()
    bP = warm_eyes_P(t, 0, lid=0.0, happy=1.0, smile=0.85)
    cP = FP(t, 5, 0, lid=0.0, happy=1.0, smile=0.85)
    P = FP(t, 3, 0, smile=0.75, blush=0.4, lid=1.0)
    put(c, 150, 800, 0.62, brodie, bP, t, "flex", glasses=0.0)
    put(c, 575, 805, 0.62, chad, cP, t, "flex")
    put(c, 365, 960, 0.62, carter, P, t, "wave", None, legs="stand")
    black(c, ramp(t, TL["duration"] - 0.8, TL["duration"] - 0.1))


# ======================================================================= captions + dispatch

SCENE_FN = {
    "office": sc_office, "stands": sc_stands, "losers": sc_losers, "crisis": sc_crisis, "hat": sc_hat, "carry": sc_carry,
    "stool": sc_stool, "roleplay": sc_roleplay, "bomb": sc_bomb, "saves": sc_saves, "after": sc_after,
    "assembly2": sc_assembly2, "solo": sc_solo, "door": sc_door, "roast": sc_roast, "defend": sc_defend, "end": sc_end,
}

CAP_Y = {}
SPK_COL = {"NARR": "#ffffff", "CARTER": "#ffd23f", "CINNER": "#d9c2ff", "BRODIE": "#8fd0ff", "CHAD": "#ffb3a7",
           "FRIEND": "#b8f5c8", "KIDA": "#b8f5c8", "KIDB": "#b8f5c8", "GYM": "#ffc98b", "HECKLER": "#ff9e9e"}
NO_CAP = {"N3"}


def chunks_for(line):
    words = line["cap"].split()
    chunks, cur = [], []
    for w_ in words:
        cur.append(w_)
        s = " ".join(cur)
        if len(s) >= 22 or w_.endswith((".", "?", "!", ",", "...")) and len(s) > 10:
            chunks.append(s)
            cur = []
    if cur:
        chunks.append(" ".join(cur))
    total = sum(len(ch) + 4 for ch in chunks)
    out, acc = [], 0.0
    for ch in chunks:
        d = line["dur"] * (len(ch) + 4) / total
        out.append((line["start"] + acc, line["start"] + acc + d, ch))
        acc += d
    return out


CHUNKS = {l["id"]: chunks_for(l) for l in TL["lines"]}


def draw_captions(c, t, scene):
    for l in TL["lines"]:
        if l["id"] in NO_CAP:
            continue
        if not (l["start"] - 0.05 <= t <= l["start"] + l["dur"] + 0.25):
            continue
        for (s0, s1, ch) in CHUNKS[l["id"]]:
            if s0 - 0.05 <= t < s1 + (0.25 if s1 >= l["start"] + l["dur"] - 0.01 else 0.0):
                y = CAP_Y.get(scene, 1140)
                u = clamp((t - s0 + 0.05) / 0.1)
                sc = 0.88 + 0.12 * ease_out_back(u, 2)
                if l["spk"] == "CINNER":
                    ch = "(" + ch.strip("()") + ")" if len(CHUNKS[l["id"]]) == 1 else ch
                lines = wrap(ch, "fredoka", 46, 600)
                at(c, 360, y, sc)
                colr = SPK_COL.get(l["spk"], "#ffffff")
                for i, ln in enumerate(lines):
                    yy = (i - (len(lines) - 1) / 2) * 54
                    text(c, ln, 0, yy + 16, "fredoka", 46, colr, outline="#000000", ow=11)
                c.restore()
                return


def scene_at(t):
    for s in SCENES:
        if s["start"] <= t < s["end"]:
            return s["name"]
    return SCENES[-1]["name"]


def render(c, t):
    name = scene_at(t)
    c.save()
    SCENE_FN[name](c, t)
    c.restore()
    draw_captions(c, t, name)
