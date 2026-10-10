"""All scene drawing."""
import json, math
import skia
from gfx import *
from chars import *

TL = json.load(open("timeline.json"))
M = TL["markers"]
LIPS = json.load(open("lipsync.json"))
LINES = {l["id"]: l for l in TL["lines"]}
SCENES = TL["scenes"]


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


def talk_any(lids, t, gain=1.0):
    return max(talk(l, t, gain) for l in lids)


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


def flash(c, t, t0, dur=0.3, color="#ffffff", amax=0.85):
    if t0 <= t <= t0 + dur:
        c.drawRect(skia.Rect.MakeWH(W, H), fill(color, amax * (1 - (t - t0) / dur)))


# ======================================================================= props / backgrounds

def bg_lord_room(c, t, led=1.0):
    c.drawRect(skia.Rect.MakeWH(W, H), lin_grad(0, 0, 0, H, ["#262347", "#16142c", "#0d0c1a"], [0, 0.5, 1]))
    # LED strip glow
    c.drawRect(skia.Rect.MakeLTRB(0, 30, W, 90), lin_grad(0, 30, 0, 90, ["#b14cff", "#b14cff"], None, 0.0))
    c.drawRect(skia.Rect.MakeLTRB(-20, 18, W + 20, 120), rad_grad(W / 2, 30, 520, ["#b14cff", "#b14cff"], [0, 1], [0.35 * led, 0]))
    c.drawPath(poly([(0, 30), (W, 30)], False), stroke("#e0a6ff", 6, 0.9))
    # poster
    at(c, 40, 160, 1.0, -3)
    fs(c, rrect(0, 0, 150, 210, 4), "#101018", 4, "#000000")
    c.drawPath(oval(75, 75, 46, 40), stroke("#ff4f9a", 5))
    for i in range(3):
        c.drawPath(smooth_path([(45 + i * 20, 50), (55 + i * 20, 75), (45 + i * 20, 100)], False), stroke("#ff4f9a", 3))
    text(c, "LOGIC", 75, 160, "bangers", 44, "#ffd23f")
    text(c, "FACTS > FEELINGS", 75, 190, "inter_bold", 13, "#cfcfe8")
    c.restore()
    # katana
    c.drawPath(poly([(215, 150), (470, 105)], False), stroke("#000000", 12))
    c.drawPath(poly([(215, 150), (470, 105)], False), stroke("#2a2a36", 8))
    c.drawPath(poly([(300, 125), (305, 150)], False), stroke("#c9a227", 8))
    c.drawPath(poly([(215, 150), (295, 136)], False), stroke("#7a1c2a", 8))
    # window with blinds
    fs(c, rrect(505, 150, 175, 240, 6), "#0f2b4d", 6, "#000000")
    c.drawCircle(600, 220, 30, rad_grad(600, 220, 80, ["#fff6d0", "#fff6d0"], [0, 1], [0.5, 0]))
    for i in range(12):
        y = 160 + i * 19
        c.drawPath(poly([(510, y), (675, y)], False), stroke("#24486e", 7))
    # shelf + figurine silhouettes
    c.drawRect(skia.Rect.MakeLTRB(505, 420, 690, 432), fill("#3b2b25"))
    for i, (x, h) in enumerate(((530, 40), (575, 55), (630, 35), (665, 48))):
        fs(c, rrect(x - 12, 420 - h, 24, h, 8), ["#6a4c93", "#1982c4", "#ff595e", "#8ac926"][i], 3, "#000000")


def chair_back(c, x, y, s=1.0):
    at(c, x, y, s)
    fs(c, rrect(-200, -260, 400, 760, 70), "#1a1a1f", 6, "#000000")
    for sx in (-1, 1):
        c.drawPath(poly([(sx * 160, -200), (sx * 160, 480)], False), stroke("#c1121f", 22))
    fs(c, rrect(-120, -240, 240, 70, 30), "#c1121f", 4, "#000000")
    c.restore()


def laptop_back(c, cx, cy, w=400, h=190, kind="lord", glow=0.0, t=0.0):
    fs(c, rrect(cx - w / 2, cy - h / 2, w, h, 14), "#a8adb8", 6, "#000000")
    c.drawRect(skia.Rect.MakeLTRB(cx - w / 2 + 8, cy - h / 2 + 6, cx + w / 2 - 8, cy - h / 2 + 14), fill("#ffffff", 0.25))
    if kind == "lord":
        at(c, cx - 110, cy - 10, 1.0, -8)
        fs(c, rrect(-62, -26, 124, 52, 10), "#ffffff", 3)
        text(c, "I", -40, 12, "bangers", 34, "#222222")
        hp = skia.Path()
        hp.moveTo(0, 14)
        hp.cubicTo(-30, -6, -16, -28, 0, -12)
        hp.cubicTo(16, -28, 30, -6, 0, 14)
        c.drawPath(hp, fill("#e63946"))
        text(c, "LOGIC", 32, 10, "bangers", 24, "#222222")
        c.restore()
        at(c, cx + 105, cy + 15, 0.55, 12)
        fs(c, oval(0, 2, 120, 20), "#2f2d36", 4)
        fs(c, smooth_path([(-70, 0), (-74, -60), (-20, -66), (0, -54), (20, -66), (74, -60), (70, 0)]), "#3a3842", 4)
        c.restore()
    else:
        g = 0.6 + 0.4 * math.sin(t * 3)
        c.drawCircle(cx, cy - 10, 70, rad_grad(cx, cy - 10, 90, ["#7ef0ff", "#7ef0ff"], [0, 1], [0.55 * g, 0]))
        brain_icon(c, cx, cy - 18, 34, "#7ef0ff")
        text(c, "Consciousness AI™", cx, cy + 50, "inter_black", 22, "#2b2f45")


def brain_icon(c, x, y, r, color="#7ef0ff", sw=5):
    p = cloud(x, y, r * 2.2, r * 1.8, 7, 0, 3, 0)
    c.drawPath(p, fill(color, 0.25))
    c.drawPath(p, stroke(color, sw))
    c.drawPath(poly([(x, y - r * 0.8), (x, y + r * 0.8)], False), stroke(color, sw * 0.7))
    for s in (-1, 1):
        c.drawPath(smooth_path([(x + s * r * 0.2, y - r * 0.3), (x + s * r * 0.6, y - r * 0.1), (x + s * r * 0.4, y + r * 0.3)], False), stroke(color, sw * 0.6))


def desk(c, y0=980, color="#3b2b25"):
    c.drawRect(skia.Rect.MakeLTRB(0, y0, W, H), lin_grad(0, y0, 0, H, [color, "#1e1512"]))
    c.drawPath(poly([(0, y0), (W, y0)], False), stroke("#5a4136", 6))


def cheeto_bag(c, x, y, s=1.0, rot=-8):
    at(c, x, y, s, rot)
    bag = smooth_path([(-55, -80), (0, -92), (55, -80), (62, 60), (0, 70), (-62, 60)])
    fs(c, bag, "#ff8a1e", 5)
    c.drawPath(poly([(-50, -70), (50, -70)], False), stroke("#c25a00", 4))
    text(c, "CHEESY", 0, -20, "bangers", 30, "#ffe14d", outline="#7a2a00", ow=5)
    text(c, "POOFS", 0, 12, "bangers", 30, "#ffe14d", outline="#7a2a00", ow=5)
    c.restore()
    for i in range(5):
        px, py = x + 60 + i * 18, y + 55 + (i % 2) * 10
        c.drawPath(blob(px, py, 9, 6, 0.3, 0, i), fill("#ff8a1e"))


def can(c, x, y, s=1.0, rot=0.0, colr="#1fd655"):
    at(c, x, y, s, rot)
    fs(c, rrect(-24, -80, 48, 80, 8), "#101418", 4)
    c.drawRect(skia.Rect.MakeLTRB(-22, -60, 22, -24), fill(colr))
    text(c, "VOLT", 0, -34, "bangers", 18, "#101418")
    c.drawPath(oval(0, -80, 22, 6), fill("#9aa0aa"))
    c.restore()


def cans_pyramid(c, x, y, t, fall=None):
    can(c, x - 30, y, 1.0)
    can(c, x + 30, y, 1.0, 0, "#ff4fd8")
    if fall is None or fall <= 0:
        can(c, x, y - 82, 1.0, 0, "#ffd23f")
    else:
        u = clamp(fall)
        ang = 90 * smooth(u)
        can(c, x + 60 * u, y - 82 + 82 * (u ** 2), 1.0, ang, "#ffd23f")


def panel(c, x, y, w, h, title, accent="#ff5700", dark=True, a=1.0, icon=None):
    c.saveLayerAlpha(None, int(255 * clamp(a)))
    c.drawPath(rrect(x + 6, y + 10, w, h, 22), fill("#000000", 0.35))
    fs(c, rrect(x, y, w, h, 22), "#1d1d2b" if dark else "#f7f7fb", 5, "#000000")
    c.save()
    c.clipPath(rrect(x, y, w, h, 22), skia.ClipOp.kIntersect, True)
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, 54), fill(accent))
    c.restore()
    if icon:
        icon(x + 34, y + 27)
        text(c, title, x + 62, y + 37, "inter_black", 24, "#ffffff", align="left")
    else:
        text(c, title, x + 22, y + 37, "inter_black", 24, "#ffffff", align="left")
    c.restore()


def typed(s, t, t0, cps=28):
    n = int(max(0, t - t0) * cps)
    return s[:n]


def draw_wrapped(c, s, x, y, w, size=24, color="#e8e8f0", name="fredoka_semi", lh=1.25, maxlines=6, cursor=False, t=0.0):
    lines = wrap(s, name, size, w)[:maxlines]
    for i, ln in enumerate(lines):
        text(c, ln, x, y + i * size * lh, name, size, color, align="left")
    if cursor and (t * 2) % 1 < 0.5:
        lw = text_w(lines[-1], name, size) if lines else 0
        yy = y + (len(lines) - 1 if lines else 0) * size * lh
        c.drawRect(skia.Rect.MakeXYWH(x + lw + 3, yy - size * 0.8, 3, size), fill(color))


def gauge(c, x, y, r, v, t, label="CHUCKLE PRESSURE", broken=0.0, a=1.0):
    if a <= 0:
        return
    c.saveLayerAlpha(None, int(255 * clamp(a)))
    fs(c, rrect(x - r - 18, y - r - 22, 2 * r + 36, r + 92, 18), "#14141f", 5, "#000000")
    for i in range(30):
        u0, u1 = i / 30, (i + 1) / 30
        cc = mix("#3ddc84", "#ffd23f", u0 * 2) if u0 < 0.5 else mix("#ffd23f", "#ff2e2e", (u0 - 0.5) * 2)
        p = skia.Path()
        p.arcTo(skia.Rect.MakeLTRB(x - r, y - r, x + r, y + r), 180 + u0 * 180, (u1 - u0) * 180 + 0.5, True)
        c.drawPath(p, stroke(hexs(cc), 16, cap="butt"))
    vv = clamp(v, 0, 1.12) + (0.015 * math.sin(t * 50) if v > 0.7 else 0)
    ang = math.pi + math.pi * vv
    c.drawPath(poly([(x, y), (x + math.cos(ang) * r * 0.85, y + math.sin(ang) * r * 0.85)], False), stroke("#ffffff", 6))
    c.drawCircle(x, y, 9, fill("#ffffff"))
    text(c, label, x, y + 38, "inter_black", 15 if r < 90 else 17, "#ffffff")
    text(c, "%d PSI" % int(vv * 100), x, y + 60, "mono", 16, "#ffd23f" if vv < 0.9 else "#ff4d4d")
    if broken > 0:
        for i in range(6):
            a0 = i * 1.1 + 0.3
            pts = [(x + 10, y - r * 0.4)]
            for k in range(1, 4):
                pts.append((x + 10 + math.cos(a0) * r * 0.35 * k + 8 * hash1(i * 9 + k), y - r * 0.4 + math.sin(a0) * r * 0.3 * k))
            c.drawPath(poly(pts, False), stroke("#ffffff", 2.5, clamp(broken * 3)))
    c.restore()


def bubble_cloud(c, cx, cy, w, h, t, trail=None, wob=0.03, shake=0.0):
    sx = shake * 8 * math.sin(t * 47)
    p = cloud(cx + sx, cy, w, h, 11, t, 7, wob)
    if trail:
        for (x, y, r) in trail:
            c.drawCircle(x, y, r, fill("#ffffff"))
            c.drawCircle(x, y, r, stroke(OUT, 5))
    c.drawPath(p, fill("#ffffff"))
    c.drawPath(p, stroke(OUT, 6))
    return p


def paper_plane(c, x, y, ang, s=1.0, glow=1.0):
    c.drawCircle(x, y, 60 * s, rad_grad(x, y, 70 * s, ["#fff6a8", "#fff6a8"], [0, 1], [0.7 * glow, 0]))
    at(c, x, y, s, ang)
    fs(c, poly([(40, 0), (-30, -24), (-14, 0), (-30, 22)]), "#ffffff", 3.5)
    c.drawPath(poly([(40, 0), (-14, 0)], False), stroke("#9aa0b0", 2.5))
    c.restore()


def sparkles(c, pts, t, color="#fff6a8"):
    for i, (x, y) in enumerate(pts):
        r = 6 + 4 * math.sin(t * 12 + i)
        c.drawPath(poly([(x, y - r * 2), (x + r * 0.5, y - r * 0.5), (x + r * 2, y), (x + r * 0.5, y + r * 0.5),
                         (x, y + r * 2), (x - r * 0.5, y + r * 0.5), (x - r * 2, y), (x - r * 0.5, y - r * 0.5)]), fill(color, 0.9))


def tomato(c, x, y, s):
    if s <= 0:
        return
    at(c, x, y, s)
    fs(c, oval(0, 0, 50, 44), "#e63946", 5)
    c.drawCircle(-16, -14, 9, fill("#ffffff", 0.6))
    fs(c, poly([(0, -40), (-24, -54), (-8, -44), (0, -62), (8, -44), (24, -54)]), "#2a9d4b", 3)
    c.restore()


def stink_lines(c, x, y, t, n=5, spread=160, h=180, color="#9be15d", a=0.8, seed=0):
    for i in range(n):
        xx = x + (i - (n - 1) / 2) * spread / max(n - 1, 1)
        ph = (t * 0.8 + hash1(i + seed) * 0.5) % 1.0
        pts = []
        for k in range(8):
            u = k / 7
            pts.append((xx + 14 * math.sin(u * 9 + t * 8 + i), y - u * h - ph * 40))
        c.drawPath(smooth_path(pts, False), stroke(color, 6, a * (1 - ph * 0.6)))


def gas_puff(c, x, y, r, a, t, seed=0, skull=False):
    p = blob(x, y, r, 9, 0.15, t, seed)
    c.drawPath(p, fill("#9ccf55", 0.75 * a))
    c.drawPath(p, stroke("#4e6d2a", 3.5, 0.8 * a))
    if skull and r > 22:
        s = r * 0.28
        c.drawPath(oval(x, y - s * 0.2, s, s * 0.9), fill("#f4f1de", a))
        c.drawRect(skia.Rect.MakeXYWH(x - s * 0.55, y + s * 0.5, s * 1.1, s * 0.5), fill("#f4f1de", a))
        for sx in (-1, 1):
            c.drawCircle(x + sx * s * 0.38, y - s * 0.2, s * 0.25, fill("#33402a", a))


# ======================================================================= shots

def lord_desk_shot(c, t, P, zoom=1.0, focus=(360, 640), shake=0.0, body=None, items=True, fall=None, extra=None,
                   lid_glow=0.0):
    c.save()
    cam(c, zoom, focus[0], focus[1], shake=shake, t=t)
    bg_lord_room(c, t)
    chair_back(c, 360, 650)
    body = body or {}
    at(c, 360, 590, 1.0)
    lord_body(c, P, t=t, **body)
    c.restore()
    # screen spill light
    c.drawRect(skia.Rect.MakeLTRB(80, 560, 640, 1000), rad_grad(360, 900, 330, ["#6fc3ff", "#6fc3ff"], [0, 1], [0.18 + lid_glow, 0]))
    desk(c, 975)
    laptop_back(c, 360, 925, 410, 190, "lord", t=t)
    if items:
        cheeto_bag(c, 100, 1075, 0.9)
        cans_pyramid(c, 615, 1090, t, fall)
    if extra:
        extra(c)
    c.restore()


def lord_face_shot(c, t, P, x=360, y=600, s=2.0, bg="room", shake=0.0, zoom=1.0, headkw=None, light="#6fc3ff", light_a=0.2,
                   rot=0.0):
    c.save()
    cam(c, zoom, 360, 640, shake=shake, t=t)
    if bg == "room":
        c.drawRect(skia.Rect.MakeWH(W, H), lin_grad(0, 0, 0, H, ["#1d1b3a", "#0e0d1c"]))
        for i in range(7):
            bx, by = 80 + i * 97, 180 + 120 * hash1(i * 5)
            c.drawCircle(bx, by, 40 + 20 * hash1(i), fill(["#b14cff", "#4cc9ff", "#ff4f9a"][i % 3], 0.18, blur=18))
    elif bg == "red":
        c.drawRect(skia.Rect.MakeWH(W, H), rad_grad(360, 600, 900, ["#ff4d4d", "#5a0000"], [0, 1]))
        speed_lines(c, 360, 600, t, 44, "#ffffff", 0.18, 330)
    elif bg == "gold":
        c.drawRect(skia.Rect.MakeWH(W, H), lin_grad(0, 0, 0, H, ["#2a2140", "#120f22"]))
    P = dict(P)
    P["light"] = light
    P["light_a"] = light_a
    at(c, x, y, s, rot)
    # shoulders hint
    fs(c, smooth_path([(-180, 150), (-220, 300), (-220, 420), (220, 420), (220, 300), (180, 150), (0, 125)]), SHIRT_LORD, 5)
    fs(c, rrect(-55, 80, 110, 80, 30), hexs(mix(SKIN_LORD, "#b8cf95", P["pale"] * 0.5)), 5)
    lord_head(c, P, **(headkw or {}))
    c.restore()
    c.restore()


def under_desk_shot(c, t, tremble=0.0, fart=0.0, stain=0.0, can_fall=0.0, bag_blow=0.0, drip=0.0):
    c.drawRect(skia.Rect.MakeWH(W, H), lin_grad(0, 0, 0, H, ["#0c0b14", "#1b1a2a", "#2b2d44"], [0, 0.5, 1]))
    # desk underside
    c.drawRect(skia.Rect.MakeLTRB(0, 0, W, 180), fill("#2a1e1a"))
    c.drawPath(poly([(0, 180), (W, 180)], False), stroke("#000000", 6))
    for i in range(3):
        c.drawPath(smooth_path([(120 + i * 40, 180), (150 + i * 30, 320), (100 + i * 50, 520), (140 + i * 20, 700)], False), stroke("#111111", 7))
    # floor
    c.drawRect(skia.Rect.MakeLTRB(0, 860, W, H), lin_grad(0, 860, 0, H, ["#3a3f5c", "#4a5072"]))
    vib = fart * 6 * math.sin(t * 70)
    # chair base column
    c.drawRect(skia.Rect.MakeLTRB(340, 560, 380, 900), fill("#222228"))
    for ang in (-160, -110, -70, -20):
        a = math.radians(ang)
        ex, ey = 360 + math.cos(a) * 300, 930 - math.sin(a) * 40
        c.drawPath(poly([(360, 900), (ex, ey)], False), stroke("#18181c", 22))
        c.drawCircle(ex, ey + 18, 18, fill("#0d0d10"))
    # seat cushion
    at(c, 360 + vib, 470 + vib * 0.5)
    fs(c, rrect(-250, -90, 500, 150, 50), "#1a1a1f", 6, "#000000")
    c.drawPath(poly([(-230, -20), (230, -20)], False), stroke("#c1121f", 10))
    c.restore()
    # legs (thighs coming toward viewer, knees, shins)
    k = 8 * tremble * math.sin(t * 40)
    kh = "#d2bd8f"
    for s in (-1, 1):
        sq = 1 - 0.35 * tremble
        cx_ = 360 + s * (88 * sq) + k * s + (vib if fart else 0)
        fs(c, rrect(cx_ - 82, 420, 164, 260, 70), kh, 5)
        c.drawPath(poly([(cx_ - 40 * s, 470), (cx_ - 30 * s, 600)], False), stroke("#b8a272", 3))
        fs(c, rrect(cx_ - 58, 650, 116, 360, 40), kh, 5)
        c.drawPath(oval(cx_, 662, 76, 44), fill("#c4ad7c"))
        c.drawPath(oval(cx_, 662, 76, 44), stroke(OUT, 4))
        for i in range(3):
            c.drawPath(poly([(cx_ - 22, 760 + i * 70), (cx_ + 20, 770 + i * 70)], False), stroke("#b8a272", 3))
        fs(c, rrect(cx_ - 72, 1000, 144, 70, 30), "#f2f2f2", 5)
        c.drawPath(poly([(cx_ - 66, 1045), (cx_ + 66, 1045)], False), stroke("#e63946", 8))
    # crotch / seat area
    crotch = smooth_path([(300, 425), (420, 425), (400, 480), (360, 500), (320, 480)])
    c.drawPath(crotch, fill(kh))
    if stain > 0:
        r = 30 + 90 * stain
        p = blob(360, 470, r, 11, 0.22, 3, 9, 0.55)
        c.save()
        c.clipPath(rrect(190, 420, 340, 250, 60), skia.ClipOp.kIntersect, True)
        c.drawPath(p, fill("#6b3e1a", 0.85))
        c.drawPath(blob(360, 465, r * 0.6, 9, 0.2, 5, 11, 0.55), fill("#5a3214", 0.7))
        c.restore()
    if drip > 0:
        L = 420 * drip
        c.drawPath(poly([(330, 560), (318, 560 + L)], False), stroke("#6b3e1a", 16, 0.9))
    if fart > 0:
        for i in range(8):
            ph = (t * 1.3 + i / 8) % 1.0
            sd = -1 if i % 2 else 1
            gas_puff(c, 360 + sd * (230 + 220 * ph), 470 - 160 * ph + 30 * math.sin(i), 25 + 60 * ph, fart * (1 - ph), t, i)
        stink_lines(c, 360, 420, t, 6, 420, 200, "#9be15d", 0.85 * fart)
        for i in range(8):
            ang = math.pi * (0.1 + 0.8 * i / 7)
            r0 = 270 + 30 * math.sin(t * 30 + i)
            x0, y0 = 360 + math.cos(ang) * r0, 470 + math.sin(ang) * r0 * 0.4
            c.drawPath(smooth_path([(x0, y0), (x0 + math.cos(ang) * 40, y0 + 10 * math.sin(t * 40 + i)), (x0 + math.cos(ang) * 80, y0)], False), stroke("#ffffff", 4, 0.5 * fart))
    # floor junk
    bx = 560 + 300 * bag_blow
    at(c, bx, 1150 - 60 * math.sin(math.pi * clamp(bag_blow)), 0.6, 360 * bag_blow)
    fs(c, smooth_path([(-55, -40), (55, -50), (60, 40), (-60, 45)]), "#ff8a1e", 4)
    c.restore()
    can(c, 150 + 40 * can_fall, 1130, 1.0, 90 * smooth(can_fall), "#1fd655")


def heap_shot(c, t, d=0.0, tears=1.0, mouth=0.6, gas=1.0, streak=0.0, puddle=0.0, head_drop=0.0, clown=0.0, honk=0.0,
              fedora_off=1.0, P_over=None, impact=0.0):
    c.drawRect(skia.Rect.MakeWH(W, H), lin_grad(0, 0, 0, H, ["#1a1830", "#121022"]))
    # floor
    c.drawRect(skia.Rect.MakeLTRB(0, 620, W, H), lin_grad(0, 620, 0, H, ["#2e3350", "#454c70"]))
    for i in range(9):
        c.drawPath(poly([(360 + (i - 4) * 40, 620), (360 + (i - 4) * 200, H)], False), stroke("#3a4060", 2))
    # chair seat + base behind
    c.drawRect(skia.Rect.MakeLTRB(338, 330, 382, 640), fill("#222228"))
    for ang in (-160, -110, -70, -20):
        a = math.radians(ang)
        c.drawPath(poly([(360, 640), (360 + math.cos(a) * 250, 660 - math.sin(a) * 30)], False), stroke("#18181c", 20))
    fs(c, rrect(130, 210, 460, 130, 50), "#1a1a1f", 6, "#000000")
    c.drawPath(poly([(150, 270), (570, 270)], False), stroke("#c1121f", 10))
    if streak > 0:
        # stain on seat
        c.drawPath(blob(360, 300, 55, 9, 0.2, 1, 4, 0.5), fill("#6b3e1a", 0.8))
    # puddle on floor
    if puddle > 0:
        c.drawPath(blob(185, 1150, 30 + 110 * puddle, 12, 0.18, t * 0.3, 6, 0.32), fill("#6b3e1a", 0.85))
    sy = 1 - 0.45 * d
    sx = 1 - 0.22 * d
    kh = "#d2bd8f"
    # legs splayed
    for s in (-1, 1):
        flat = 1 - 0.35 * d
        hip = (360 + s * 50, 870)
        knee = (360 + s * 170, 1010 + 20 * d)
        foot = (360 + s * 250, 1150)
        for (a_, b_) in ((hip, knee), (knee, foot)):
            pth = poly([a_, b_], False)
            c.drawPath(pth, stroke(OUT, 96 * flat + 10))
            c.drawPath(pth, stroke(kh, 96 * flat))
        if d > 0.2:
            for i in range(3):
                wx = lerp(hip[0], knee[0], 0.3 + 0.2 * i)
                wy = lerp(hip[1], knee[1], 0.3 + 0.2 * i)
                c.drawPath(poly([(wx - 20, wy - 10), (wx + 4, wy + 6), (wx + 24, wy - 6)], False), stroke("#9c875c", 3, d))
        fs(c, rrect(foot[0] - 60, foot[1] - 30, 120, 60, 26), "#f2f2f2", 5)
        c.drawPath(poly([(foot[0] - 55, foot[1] + 5), (foot[0] + 55, foot[1] + 5)], False), stroke("#e63946", 7))
    # streak down left leg
    if streak > 0:
        L = clamp(streak)
        p0 = (330, 880)
        p1 = (175, 1015)
        p2 = (190, 1150)
        pts = [p0]
        if L < 0.6:
            u = L / 0.6
            pts.append((lerp(p0[0], p1[0], u), lerp(p0[1], p1[1], u)))
        else:
            pts.append(p1)
            u = (L - 0.6) / 0.4
            pts.append((lerp(p1[0], p2[0], u), lerp(p1[1], p2[1], u)))
        c.drawPath(poly(pts, False), stroke("#6b3e1a", 20, 0.9))
        c.drawPath(blob(360, 875, 40, 9, 0.2, 2, 8, 0.6), fill("#6b3e1a", 0.85))
    # torso slumped (deflating)
    at(c, 360, 760 + 60 * d, 1.0)
    c.scale(sx, sy)
    torso = smooth_path([(-150, -150), (-175, 0), (-160, 120), (0, 140), (160, 120), (175, 0), (150, -150), (0, -175)])
    fs(c, torso, SHIRT_LORD, 6)
    text(c, "r/LOGIC", 0, -20, "inter_black", 30, "#f2e6c9", a=0.9)
    if d > 0.15:
        for i in range(5):
            yy = -110 + i * 50
            c.drawPath(smooth_path([(-120, yy), (-60, yy + 14), (0, yy), (60, yy + 16), (120, yy)], False), stroke("#2a4747", 4, d))
    c.restore()
    # arms limp
    skin = SKIN_LORD
    for s in (-1, 1):
        sh_ = (360 + s * 150 * sx, 650 + 70 * d)
        el = (360 + s * 230 * sx, 820 + 20 * d)
        hd = (360 + s * 270 * sx, 960)
        c.drawPath(poly([sh_, el], False), stroke(OUT, 54 * (1 - 0.3 * d) + 10))
        c.drawPath(poly([sh_, el], False), stroke(SHIRT_LORD, 54 * (1 - 0.3 * d)))
        c.drawPath(poly([el, hd], False), stroke(OUT, 44 * (1 - 0.3 * d) + 8))
        c.drawPath(poly([el, hd], False), stroke(skin, 44 * (1 - 0.3 * d)))
        draw_hand(c, hd[0], hd[1], "open", s, skin)
    # head
    hx, hy = 360 + 25 * head_drop, 530 + 110 * d + 60 * head_drop
    rot = 14 * head_drop + 6 * math.sin(t * 0.8)
    P = P_(t=t, lid=0.42 - 0.12 * d, lower=0.15, tears=tears, mouth_open=mouth, smile=-0.5, brow_ang=0.9, brow_y=0.3,
           px=0, py=0.5, sweat=0.3, pale=0.25)
    if P_over:
        P.update(P_over)
    at(c, hx, hy, 1.12 * (1 - 0.12 * d) * (1 + impact * 0.1), rot)
    lord_head(c, P, fedora=False, deflate=d, clown_nose=clown)
    if honk > 0 and clown > 0:
        c.drawCircle(0, 34, 26 * (1 + 0.4 * honk), stroke("#ffffff", 4, honk))
    c.restore()
    # fedora landed on the chair seat
    at(c, 500, 228, 0.6, 14)
    fs(c, oval(0, 2, 150, 26), "#2f2d36", 5)
    fs(c, smooth_path([(-82, 0), (-90, -60), (-30, -98), (0, -82), (30, -98), (90, -60), (82, 0)]), "#3a3842", 5)
    c.restore()
    # gas puffs from mouth
    if gas > 0:
        mx, my = hx, hy + 80 * 1.12 * (1 - 0.12 * d)
        for i in range(10):
            ph = (t * 0.45 + i / 10) % 1.0
            x = mx + 60 + 80 * math.sin(i * 2.3 + ph * 3) * ph + 60 * ph
            y = my - 40 - ph * 560
            r = 16 + 70 * ph
            gas_puff(c, x, y, r, gas * math.sin(math.pi * ph) ** 0.7, t, i, skull=(i % 3 == 0))


def webcam_closeup(c, t, zoom=1.0, rec=0.0, led_flare=0.0):
    c.save()
    cam(c, zoom, 385, 520)
    c.drawRect(skia.Rect.MakeLTRB(-400, -400, W + 400, H + 400), lin_grad(0, 0, 0, 420, ["#2a2350", "#0b0a14"]))
    c.drawRect(skia.Rect.MakeLTRB(-400, 380, W + 400, 410), fill("#000000", 0.4))
    # screen bezel (laptop seen from the Lord's side)
    fs(c, rrect(-40, 400, 800, 900, 30), "#15151c", 6, "#000000")
    c.drawPath(poly([(0, 404), (720, 404)], False), stroke("#4a4a5c", 3))
    c.drawRect(skia.Rect.MakeLTRB(20, 600, 700, 1400), lin_grad(0, 600, 0, 1400, ["#2b4b7a", "#16213a"]))
    # reflection of a fedora silhouette in the screen
    if zoom < 1.5:
        c.drawPath(oval(360, 900, 170, 30), fill("#000000", 0.18))
        c.drawPath(smooth_path([(270, 900), (260, 820), (360, 790), (460, 820), (450, 900)]), fill("#000000", 0.18))
    # lens
    c.drawCircle(360, 500, 34, fill("#050507"))
    c.drawCircle(360, 500, 34, stroke("#333344", 5))
    c.drawCircle(360, 500, 16, fill("#1a2440"))
    c.drawCircle(353, 493, 6, fill("#ffffff", 0.6))
    # LED
    g = 0.75 + 0.25 * math.sin(t * 4)
    c.drawCircle(420, 500, 30 + 40 * led_flare, rad_grad(420, 500, 34 + 50 * led_flare, ["#3dff6e", "#3dff6e"], [0, 1], [0.6 * g + 0.4 * led_flare, 0]))
    c.drawCircle(420, 500, 7, fill("#b6ffc8"))
    c.restore()
    if rec > 0:
        sc = ease_out_back(clamp(rec * 2), 2)
        at(c, 360, 260, sc)
        fs(c, rrect(-160, -60, 320, 110, 24), "#000000", 4, "#ff2e2e")
        c.drawCircle(-100, -5, 24, fill("#ff2e2e", 0.6 + 0.4 * ((t * 2) % 1 < 0.5)))
        text(c, "REC", 30, 22, "inter_black", 64, "#ffffff")
        c.restore()


def webcam_pov(c, t, peek=0.0, P=None, glitch=0.0):
    # the room from the laptop's camera
    c.drawRect(skia.Rect.MakeWH(W, H), lin_grad(0, 0, 0, H, ["#20283a", "#121722"]))
    c.save()
    at(c, 360, 700, 1.0)
    c.translate(-360, -650)
    bg_lord_room(c, t, 0.5)
    chair_back(c, 360, 650)
    c.restore()
    c.restore()
    # stain on the chair seat
    fs(c, rrect(150, 900, 420, 120, 40), "#1a1a1f", 6, "#000000")
    c.drawPath(blob(360, 950, 60, 9, 0.2, 1, 4, 0.5), fill("#6b3e1a", 0.85))
    if peek > 0:
        y = lerp(1500, 1010, peek)
        at(c, 330, y, 1.5, -8)
        lord_head(c, P, fedora=False, deflate=0.7, clown_nose=1.0)
        c.restore()
    # desk edge (bottom)
    c.drawRect(skia.Rect.MakeLTRB(0, 1150, W, H), fill("#2a1e1a"))
    # webcam look: tint, scanlines, vignette, overlay
    c.drawRect(skia.Rect.MakeWH(W, H), fill("#2bff88", 0.08))
    for y in range(0, H, 6):
        c.drawRect(skia.Rect.MakeLTRB(0, y, W, y + 2), fill("#000000", 0.13))
    vignette(c, 0.85, "#000000", 820)
    if glitch > 0:
        for i in range(8):
            y = (hash1(int(t * 24) * 7 + i) * 0.5 + 0.5) * H
            c.drawRect(skia.Rect.MakeLTRB(0, y, W, y + 10 + 30 * hash1(i)), fill(["#ff2e88", "#2ee6ff", "#ffffff"][i % 3], 0.35 * glitch))
    c.drawCircle(70, 120, 14, fill("#ff2e2e", 1.0 if (t * 2) % 1 < 0.6 else 0.2))
    text(c, "REC", 95, 132, "mono", 30, "#ffffff", align="left")
    secs = 2833 + (t - M["pov"])
    text(c, "00:%02d:%02d" % (int(secs // 60) % 60, int(secs % 60)), 650, 132, "mono", 30, "#ffffff", align="right")
    text(c, "WEBCAM_01  720p", 70, 1120, "mono", 24, "#ffffff", align="left", a=0.8)
    for (x, y, dx, dy) in ((40, 60, 1, 1), (680, 60, -1, 1), (40, 1150, 1, -1), (680, 1150, -1, -1)):
        c.drawPath(poly([(x, y + dy * 50), (x, y), (x + dx * 50, y)], False), stroke("#ffffff", 5, 0.8))


# ======================================================================= scenes

def sc_intro(c, t):
    lt = t - M["intro"]
    zoom = 1.0 + 0.04 * lt / 10
    c.save()
    cam(c, zoom, 360, 700)
    # warm room
    c.drawRect(skia.Rect.MakeWH(W, H), lin_grad(0, 0, 0, H, ["#ffb86b", "#e07a5f", "#5a3a5e"], [0, 0.5, 1]))
    # window with night sky
    fs(c, rrect(470, 150, 210, 260, 10), "#1d2a5a", 7, "#5a3a2a")
    for i in range(9):
        sx_, sy_ = 490 + 170 * (hash1(i * 3) * 0.5 + 0.5), 170 + 220 * (hash1(i * 5) * 0.5 + 0.5)
        c.drawCircle(sx_, sy_, 2.5 + 1.5 * math.sin(t * 3 + i), fill("#ffffff", 0.9))
    c.drawCircle(620, 210, 24, fill("#fff3c4"))
    c.drawPath(poly([(575, 150), (575, 410)], False), stroke("#5a3a2a", 7))
    # poster
    at(c, 50, 170, 1.0, 4)
    fs(c, rrect(0, 0, 160, 200, 6), "#2b2d42", 4)
    c.drawPath(poly([(60, 40), (60, 90), (35, 150), (125, 150), (100, 90), (100, 40)]), stroke("#7ef0ff", 5))
    c.drawPath(oval(80, 130, 30, 14), fill("#7ef0ff", 0.6))
    text(c, "MEME", 80, 180, "bangers", 26, "#ffd23f")
    text(c, "SCIENCE", 80, 30, "bangers", 24, "#ffd23f")
    c.restore()
    # string lights
    pts = [(x, 70 + 30 * math.sin(x / 720 * math.pi)) for x in range(0, 740, 60)]
    c.drawPath(smooth_path(pts, False), stroke("#3b2a20", 3))
    for i, (x, y) in enumerate(pts):
        cc = ["#ffd23f", "#ff6b6b", "#7ef0ff", "#9be15d"][i % 4]
        c.drawCircle(x, y + 12, 18, fill(cc, 0.35 + 0.15 * math.sin(t * 3 + i), blur=8))
        c.drawCircle(x, y + 12, 7, fill(cc))
    # creator
    look_up = ramp(t, M["A2"] - 0.2, M["A2"] + 0.1)
    after = ramp(t, M["post_click"] + 0.1, M["post_click"] + 0.35)
    bl = blink(t, 2)
    excite = ramp(t, M["A2"] + 1.5, M["A2"] + 1.8)
    P = P_(t=t, lid=bl * (1.0 + 0.1 * look_up), px=lerp(0.1, 0, look_up) + 0.6 * after, py=lerp(0.6, 0, look_up) - 0.6 * after,
           smile=0.55 + 0.3 * excite, mouth_open=talk("A2", t), teeth=True, brow_y=0.5 * look_up + 0.3 * excite,
           blush=0.3)
    if M["A2"] + 1.6 < t < M["A2_end"] + 0.2 and talk("A2", t) < 0.1:
        P.update(lid=0.0, happy=1.0)
    if 2.4 < t < 3.6:  # eyebrow wiggle
        P["brow_y"] = 0.4 * (0.5 + 0.5 * math.sin(t * 18))
    enter = lin(t, M["post_click"] - 0.25, M["post_click"] + 0.15)
    at(c, 360, 600, 1.0)
    creator_body(c, P, t=t, typing=1.0 if t < M["A2"] else 0.0, enter=enter if enter < 1 else 1, head_dy=-8 * look_up)
    c.restore()
    c.drawRect(skia.Rect.MakeLTRB(80, 560, 640, 1000), rad_grad(360, 900, 330, ["#7ef0ff", "#7ef0ff"], [0, 1], [0.15, 0]))
    desk(c, 985, "#6b4a35")
    laptop_back(c, 360, 935, 410, 190, "creator", t=t)
    # mug + plant
    fs(c, rrect(70, 1010, 70, 80, 10), "#ffd23f", 4)
    c.drawPath(oval(140, 1048, 16, 20), stroke(OUT, 6))
    fs(c, rrect(560, 1030, 90, 70, 12), "#c46b3a", 4)
    for i in range(5):
        a = math.radians(-150 + i * 30)
        c.drawPath(oval(605 + math.cos(a) * 40, 1010 + math.sin(a) * 50, 16, 32), fill("#3aa655"))
    c.restore()
    # floating AI panel
    pa = ramp(t, 0.3, 0.8) * (1 - ramp(t, M["post_click"] + 0.3, M["post_click"] + 0.7))
    if pa > 0:
        py0 = 70 - 30 * (1 - pa)
        panel(c, 40, py0, 640, 300, "Consciousness AI™", "#5a4bd6", a=pa, icon=lambda x, y: brain_icon(c, x, y, 13, "#ffffff", 3))
        c.saveLayerAlpha(None, int(255 * pa))
        prompt = "Write a meme-science post so funny it breaks a Logical Lord."
        draw_wrapped(c, typed(prompt, t, 0.9, 22), 70, py0 + 100, 580, 26, "#e8e8f0", cursor=t < 4.2, t=t)
        if t > 4.4:
            prog = clamp((t - 4.4) / 1.6)
            c.drawPath(rrect(70, py0 + 190, 420, 22, 11), fill("#33334a"))
            c.drawPath(rrect(70, py0 + 190, 420 * prog, 22, 11), fill("#7ef0ff"))
            text(c, "brewing meme science... %d%%" % int(prog * 100) if prog < 1 else "post ready!", 70, py0 + 245, "inter_bold", 20, "#c9c9e0", align="left")
        if t > 6.0:
            press = pulse(t, M["post_click"] - 0.05, 0.25)
            at(c, 590, py0 + 205, 1 - 0.12 * press + 0.06 * math.sin(t * 6) * (t < M["post_click"]))
            fs(c, rrect(-70, -32, 140, 64, 32), "#ff5fa2", 4, "#000000")
            text(c, "POST", 0, 12, "bangers", 38, "#ffffff")
            c.restore()
        c.restore()
    # paper plane
    if t > M["post_click"]:
        u = clamp((t - M["post_click"]) / 1.4)
        x = lerp(360, 820, u) + 90 * math.sin(u * math.pi)
        y = lerp(860, -120, u ** 1.2)
        sparkles(c, [(lerp(360, x, k / 5) - 30, lerp(860, y, k / 5) + 40) for k in range(5)], t)
        paper_plane(c, x, y, -60 + 20 * math.sin(u * 6), 1.4)
    black(c, 1 - ramp(t, 0, 0.5))


def sc_title(c, t):
    lt = t - M["title"]
    c.drawRect(skia.Rect.MakeWH(W, H), rad_grad(360, 620, 900, ["#5b2a86", "#1a0f2e"], [0, 1]))
    for i in range(18):
        a = 2 * math.pi * i / 18 + lt * 0.25
        p = poly([(360, 620), (360 + math.cos(a) * 1200, 620 + math.sin(a) * 1200), (360 + math.cos(a + 0.12) * 1200, 620 + math.sin(a + 0.12) * 1200)])
        c.drawPath(p, fill("#ffffff", 0.05))
    words = [("THE CHUCKLE", 0.15), ("THAT BROKE", 0.75), ("THE", 1.35), ("UNBREAKABLE", 1.6)]
    for i, (w, d) in enumerate(words):
        u = clamp((lt - d) / 0.3)
        if u <= 0:
            continue
        sc = ease_out_back(u, 3)
        y = [420, 540, 630, 760][i]
        size = [96, 96, 64, 118][i]
        at(c, 360, y, sc, -4 + 2 * math.sin(lt * 2 + i))
        text(c, w, 0, 0, "bangers", size, "#ffd23f" if i != 3 else "#ff5fa2", outline=OUT, ow=14, shadow=True)
        c.restore()
    if lt > 2.2:
        a = clamp((lt - 2.2) / 0.5)
        text(c, "a meme-science tragedy", 360, 860, "fredoka", 40, "#ffffff", outline=OUT, ow=6, a=a)
        if lt > 2.3:
            # cracked fedora icon
            at(c, 360, 1000, 0.7 * ease_out_back(clamp((lt - 2.3) / 0.4)))
            fs(c, oval(0, 2, 150, 26), "#2f2d36", 5)
            fs(c, smooth_path([(-82, 0), (-90, -60), (-30, -98), (0, -82), (30, -98), (90, -60), (82, 0)]), "#3a3842", 5)
            c.drawPath(poly([(0, -82), (-12, -55), (10, -35), (-6, -10)], False), stroke("#ffffff", 5))
            c.restore()
    flash(c, t, M["title"] + 0.15, 0.25)
    black(c, ramp(t, M["lord_intro"] - 0.25, M["lord_intro"]))


def lord_expr_intro(t):
    """Expressions/poses for the lord_intro scene."""
    bl = blink(t, 5, 3.2)
    P = P_(t=t, lid=0.55 * bl, smile=0.45, asym=0.5, brow_ang=-0.15, browR=0.4, px=0.0, py=0.55, mouth_open=0.0)
    body = dict(poseL="type", poseR="type", typing=1.0, quote_curl=0.0)
    # speaking lines
    sp = talk_any(["B4", "B5", "B6", "B7"], t)
    P["mouth_open"] = sp
    if M["B4"] - 0.3 < t < M["B4_end"] + 0.2:
        P.update(lid=0.35 * bl + 0.05, smile=0.35, asym=0.8, browR=0.8, py=0.5)
    if t >= M["notif"]:
        u = ramp(t, M["notif"], M["notif"] + 0.25)
        P.update(lid=lerp(0.55, 1.05, u) * bl, py=lerp(0.55, -0.2, u), px=lerp(0, 0.1, u), brow_y=0.4 * u, smile=0.4, asym=0.3)
        body["typing"] = 0.0
    if t >= M["B5"]:
        P.update(brow_y=0.8, smile=0.7, asym=0.2, teeth=True, px=0.0, py=0.4, lid=0.9 * bl)
    if t >= M["B6"]:
        P.update(lid=0.5 * bl, smile=0.8, asym=0.6, browR=0.7, brow_y=0.1, teeth=True, py=0.6)
        u = ramp(t, M["B6"] + 0.6, M["B6"] + 1.0)
        body.update(poseR="type", blendR=("point", u))
    if t >= M["B7"] - 0.1:
        u = ramp(t, M["B7"] - 0.1, M["B7"] + 0.35) * (1 - ramp(t, M["B7_end"] + 0.2, M["B7_end"] + 0.6))
        body.update(poseL="type", blendL=("quote", u), poseR="point", blendR=("quote", u))
        q0 = M["B7"] + 0.9
        body["quote_curl"] = pulse(t, q0, 0.3) + pulse(t, q0 + 0.35, 0.3)
        P.update(lid=0.4 * bl + 0.05, py=0.0, px=0.0, smile=0.6, asym=0.7, browR=1.0, browL=-0.2)
    if t >= M["snort"]:
        P.update(lid=0.0 if t < M["snort"] + 0.35 else 0.5 * bl, happy=1.0, smile=0.8, asym=0.4, mouth_open=0.0)
    if t >= M["B8"]:
        u = ramp(t, M["B8"] + 0.3, M["B8"] + 0.6) * (1 - ramp(t, M["B8"] + 1.9, M["B8"] + 2.3))
        body.update(poseL="type", blendL=("knuck", u), poseR="type", blendR=("knuck", u), typing=0.0)
        P.update(lid=0.6 * bl, smile=0.6, asym=0.5, browR=0.6, brow_ang=-0.3, happy=0.0, px=0.0, py=0.2)
    if t >= M["lean_in"]:
        P.update(lid=0.45, brow_ang=-0.5, smile=0.5, asym=0.6, py=0.6)
    return P, body


def sc_lord_intro(c, t):
    lt = t - M["lord_intro"]
    # webcam insert during B3
    if M["webcam_tease"] + 0.05 <= t < M["B3_end"] + 0.15:
        u = (t - M["webcam_tease"]) / 2.2
        webcam_closeup(c, t, 1.3 + 0.2 * u)
        text(c, "(the webcam light)", 360, 760, "fredoka", 34, "#bfffd0", outline=OUT, ow=6, a=ramp(t, M["webcam_tease"] + 0.3, M["webcam_tease"] + 0.6))
        return
    P, body = lord_expr_intro(t)
    zoom = 1.0 + 0.05 * clamp(lt / 10)
    focus = (360, 640)
    if M["B2"] <= t < M["webcam_tease"]:
        u = ramp(t, M["B2"], M["B2"] + 0.6)
        zoom = lerp(zoom, 1.12, u)
        focus = (lerp(360, 360, u), lerp(640, 820, u))
    if t >= M["lean_in"]:
        u = ramp(t, M["lean_in"], M["lean_in"] + 0.8)
        zoom = lerp(1.05, 1.5, u)
        focus = (360, lerp(640, 600, u))
    snort_k = pulse(t, M["snort"], 0.3)
    body = dict(body)
    body["head_dy"] = -14 * snort_k
    body["head_rot"] = -4 * snort_k
    if t >= M["lean_in"]:
        body["lean"] = ramp(t, M["lean_in"], M["lean_in"] + 0.6) * 1.5
    fall = lin(t, M["B2"] + 1.55, M["B2"] + 1.9) if t > M["B2"] + 1.5 else None
    lord_desk_shot(c, t, P, zoom, focus, body=body, fall=fall)
    # labels
    if M["B1"] + 0.8 < t < M["B1_end"] + 0.2:
        a = ramp(t, M["B1"] + 0.8, M["B1"] + 1.2) * (1 - ramp(t, M["B1_end"] - 0.2, M["B1_end"] + 0.2))
        c.saveLayerAlpha(None, int(255 * a))
        fs(c, rrect(30, 70, 470, 96, 10), "#000000", 0, None, a=0.6)
        c.drawRect(skia.Rect.MakeXYWH(30, 70, 10, 96), fill("#ffd23f"))
        text(c, "LOGICUS LORDICUS", 58, 112, "inter_black", 34, "#ffffff", align="left")
        text(c, "Natural habitat: the comment section", 58, 148, "fredoka_semi", 24, "#ffd23f", align="left")
        c.restore()
    if M["B2"] + 0.2 < t < M["webcam_tease"]:
        a1 = ramp(t, M["B2"] + 0.3, M["B2"] + 0.5)
        a2 = ramp(t, M["B2"] + 1.4, M["B2"] + 1.6)
        comic = lambda s, x, y, a, r: (at(c, x, y, ease_out_back(a, 2), r), text(c, s, 0, 0, "bangers", 44, "#ffd23f", outline=OUT, ow=10), c.restore()) if a > 0 else None
        comic("CHEETO DUST: 100%", 210, 820, a1, -6)
        comic("ENERGY DRINKS: 3", 510, 880, a2, 5)
    # floating forum panel
    pa = ramp(t, M["type_comment"] - 0.4, M["type_comment"]) * (1 - ramp(t, M["lean_in"] - 0.2, M["lean_in"] + 0.2))
    if pa > 0:
        y0 = 60
        panel(c, 40, y0, 640, 330, "r/LogicalLords", "#ff5700", a=pa)
        c.saveLayerAlpha(None, int(255 * pa))
        cmt = "Well, actually, humor is subjective, and this is a clear case of confirmation bias with a touch of Dunning-Kruger..."
        if t < M["notif"]:
            text(c, "Your comment (draft):", 70, y0 + 92, "inter_bold", 20, "#9a9ab8", align="left")
            draw_wrapped(c, typed(cmt, t, M["type_comment"], 34), 70, y0 + 130, 580, 25, "#ffffff", cursor=True, t=t)
        else:
            u = ramp(t, M["notif"], M["notif"] + 0.3)
            at(c, 0, -30 * (1 - u))
            fs(c, rrect(60, y0 + 72, 600, 238, 14), "#2a2a3d", 3, "#ff5700")
            text(c, "NEW POST", 80, y0 + 108, "inter_black", 20, "#ff5700", align="left")
            text(c, "Meme Science #42", 80, y0 + 150, "inter_black", 34, "#ffffff", align="left")
            text(c, "by u/humble_dweeb", 80, y0 + 186, "fredoka_semi", 24, "#c9c9e0", align="left")
            fs(c, rrect(80, y0 + 206, 330, 40, 20), "#5a4bd6", 0, None)
            brain_icon(c, 104, y0 + 226, 9, "#ffffff", 2.5)
            text(c, "made with Consciousness AI™", 122, y0 + 233, "inter_bold", 17, "#ffffff", align="left")
            # upvote arrow
            fs(c, poly([(600, y0 + 120), (630, y0 + 160), (612, y0 + 160), (612, y0 + 190), (588, y0 + 190), (588, y0 + 160), (570, y0 + 160)]), "#ff5700", 3)
            c.restore()
        c.restore()
    black(c, 1 - ramp(t, M["lord_intro"], M["lord_intro"] + 0.6))
    if lt < 0.7:
        iris(c, 360, 560, 900 * ramp(t, M["lord_intro"], M["lord_intro"] + 0.7))


def sc_post(c, t):
    hit = M["dart_hit"]
    bl = blink(t, 8, 2.8)
    glow = ramp(t, M["glow"], M["glow"] + 1.2)
    # reading: pupils scan left->right
    scan = ((t - M["C1"]) * 1.2) % 1.0
    P = P_(t=t, lid=0.6 * bl, smile=0.4, asym=0.5, browR=0.4, px=lerp(-0.5, 0.5, scan), py=0.5)
    if t > M["glow"]:
        P.update(lid=lerp(0.6, 0.95, glow) * bl, smile=lerp(0.4, 0.15, glow), asym=0.2, brow_y=0.4 * glow, px=0.0, py=0.45)
    if t > M["C3"]:
        P.update(brow_ang=0.3, smile=0.0, asym=0)
    shake = 0.0
    dart = 0.0
    if t >= hit:
        u = t - hit
        P.update(lid=1.25, pr=0.35, px=0, py=-0.1, smile=-0.1, mouth_open=0.0, brow_y=1.0, brow_ang=0.4)
        shake = max(0, 1 - u * 2.5) * 2
        dart = 1.0
    light = hexs(mix("#6fc3ff", "#ffcf4d", glow))
    zoom = 1.0 + 0.08 * ramp(t, M["C1"], M["C3"]) + (0.25 * ease_out_back(clamp((t - hit) / 0.2)) if t > hit else 0)
    lord_face_shot(c, t, P, 360, 640, 2.05, "gold" if glow > 0 else "room", shake, zoom,
                   headkw=dict(dart=dart, dart_wob=max(0, 1 - (t - hit) * 0.8) if t > hit else 0, glass_glow="#ffd84d", glow_a=glow * (1 if t < hit else 0.6)),
                   light=light, light_a=0.18 + 0.4 * glow)
    if glow > 0:
        # golden rays from below (the screen)
        for i in range(9):
            a = math.radians(-90 + (i - 4) * 12 + 3 * math.sin(t * 2 + i))
            p = poly([(360, 1400), (360 + math.cos(a) * 1600 - 40, 1400 + math.sin(a) * 1600), (360 + math.cos(a) * 1600 + 40, 1400 + math.sin(a) * 1600)])
            c.drawPath(p, fill("#ffe27a", 0.09 * glow))
        a = ramp(t, M["C2"] + 0.4, M["C2"] + 0.7)
        if a > 0 and t < hit:
            at(c, 360, 1150, 1.0, -3)
            fs(c, rrect(-300, -55, 600, 100, 6), "#000000", 4, "#ffd23f", a=a)
            text(c, "[ POST REDACTED FOR LEGAL REASONS ]", 0, 8, "inter_black", 26, "#ffd23f", a=a)
            c.restore()
    if M["dart_fire"] <= t < hit:
        u = (t - M["dart_fire"]) / (hit - M["dart_fire"])
        y = lerp(1450, 640 - 2.05 * 74, u)
        s = lerp(3.5, 2.05, u)
        at(c, 360, y, s)
        fs(c, oval(0, 0, 20, 12), "#2a7de1", 4)
        fs(c, rrect(-11, 4, 22, 90, 9), "#ff8c2a", 4)
        c.restore()
    if t >= hit:
        comic_text(c, "BAM!", 540, 300, 130, "#ffffff", t, hit, 10, True, "#e63946")
        flash(c, t, hit, 0.3)
    black(c, ramp(t, M["xray"] - 0.15, M["xray"]))


def sc_xray(c, t):
    lt = t - M["xray"]
    c.drawRect(skia.Rect.MakeWH(W, H), lin_grad(0, 0, 0, H, ["#071a33", "#03101f"]))
    for x in range(0, W, 40):
        c.drawPath(poly([(x, 0), (x, H)], False), stroke("#0f3a5f", 1.5))
    for y in range(0, H, 40):
        c.drawPath(poly([(0, y), (W, y)], False), stroke("#0f3a5f", 1.5))
    cyan = "#7fdcff"
    # body outline
    body = smooth_path([(250, 0), (250, 120), (90, 230), (60, 700), (90, 1150), (630, 1150), (660, 700), (630, 230), (470, 120), (470, 0)], False)
    c.drawPath(body, stroke(cyan, 14, 0.15))
    c.drawPath(body, stroke(cyan, 4, 0.9))
    # spine + ribs
    for i in range(7):
        y = 300 + i * 70
        for s in (-1, 1):
            c.drawPath(smooth_path([(360, y), (360 + s * 140, y + 20), (360 + s * 230, y + 70)], False), stroke("#e8f6ff", 7, 0.35))
    c.drawPath(poly([(360, 120), (360, 1150)], False), stroke("#e8f6ff", 10, 0.25))
    # esophagus
    c.drawPath(poly([(360, 0), (360, 760)], False), stroke("#ff8fb0", 60, 0.25))
    c.drawPath(poly([(360, 0), (360, 760)], False), stroke("#ff8fb0", 4, 0.6))
    # stomach
    st = blob(380, 860, 170, 10, 0.06, t, 2, 0.75)
    c.drawPath(st, fill("#ff8fb0", 0.35))
    c.drawPath(st, stroke("#ff8fb0", 5, 0.9))
    # gremlin
    wake = ramp(t, M["gremlin_wake"], M["gremlin_wake"] + 0.3)
    rise = ramp(t, M["C5"] + 1.0, M["C5_end"] + 0.3)
    glow = ramp(t, M["C5"], M["C5"] + 1.2)
    gx = 380 + 10 * math.sin(t * 3) * (1 - rise)
    gy = lerp(880, 330, rise) + 6 * math.sin(t * 9)
    r = 52 + 20 * glow
    if glow > 0:
        # ancient runic ring
        for i in range(12):
            a = t * 1.5 + 2 * math.pi * i / 12
            x, y = gx + math.cos(a) * (r + 50), gy + math.sin(a) * (r + 50)
            text(c, "HAHEHIHO"[i % 8], x, y + 10, "bangers", 30, "#ffd23f", a=glow * 0.85)
    gremlin(c, gx, gy, r, t, wake, glow)
    # bubbles
    for i in range(10):
        ph = (t * 0.6 + i / 10) % 1
        c.drawCircle(320 + 120 * hash1(i * 3), 980 - ph * 300, 6 + 6 * hash1(i), stroke("#ffffff", 3, 0.6 * (1 - ph) * (0.3 + glow)))
    # scanner line
    sy = (lt * 400) % (H + 200) - 100
    c.drawRect(skia.Rect.MakeLTRB(0, sy - 30, W, sy + 30), lin_grad(0, sy - 30, 0, sy + 30, [cyan, cyan, cyan], [0, 0.5, 1], 0.0))
    c.drawPath(poly([(0, sy), (W, sy)], False), stroke(cyan, 3, 0.7))
    # labels
    text(c, "X-RAY", 40, 110, "mono", 34, cyan, align="left")
    text(c, "SUBJECT: LOGICUS LORDICUS", 40, 150, "mono", 22, cyan, align="left", a=0.8)
    if t > M["gremlin_wake"] + 0.4:
        a = ramp(t, M["gremlin_wake"] + 0.4, M["gremlin_wake"] + 0.7)
        lx, ly = 600, gy - 160
        c.drawPath(poly([(lx - 40, ly + 30), (gx + r * 0.9, gy - r * 0.6)], False), stroke("#ffd23f", 4, a))
        text(c, "FORBIDDEN", lx, ly, "bangers", 40, "#ffd23f", outline=OUT, ow=6, a=a)
        text(c, "CHUCKLE", lx, ly + 40, "bangers", 40, "#ffd23f", outline=OUT, ow=6, a=a)
    black(c, 1 - ramp(t, M["xray"], M["xray"] + 0.3))


def sc_panic(c, t):
    bl = blink(t, 9, 2.0)
    jit = 0.15 * vnoise(t * 25, 4)
    P = P_(t=t, lid=1.18 * bl, pr=0.4, px=jit, py=0.0 + 0.1 * vnoise(t * 20, 5), wobble=1.0, smile=-0.15, brow_ang=0.9, brow_y=0.7,
           sweat=0.6 + 0.4 * ramp(t, M["C7"], M["C7_end"]), puff=0.15, red=0.2)
    lord_face_shot(c, t, P, 360, 640, 2.05, "red", 0.4, 1.0 + 0.05 * (t - M["panic"]) / 6,
                   headkw=dict(dart=1.0), light="#ffffff", light_a=0.0)
    # paper crown that cracks on "I lose"
    lose = M["C7_end"] - 0.6
    if t > M["C7"] + 0.2:
        a = ramp(t, M["C7"] + 0.2, M["C7"] + 0.6)
        fallu = ramp(t, lose, lose + 0.6)
        at(c, 360 + 40 * fallu, 120 + 1200 * fallu ** 2, 1.0, 25 * fallu)
        fs(c, poly([(-90, 40), (-90, -30), (-50, 5), (0, -50), (50, 5), (90, -30), (90, 40)]), "#ffd23f", 6, a=a)
        if t > lose:
            c.drawPath(poly([(0, -50), (-10, -10), (10, 10), (-5, 40)], False), stroke(OUT, 5))
        c.restore()
    black(c, 1 - ramp(t, M["panic"], M["panic"] + 0.15))


def sc_suppress(c, t):
    # sub-shots
    if M["D2"] + 1.2 <= t < M["D3"] - 0.05:
        tr = ramp(t, M["D2"] + 1.2, M["D2"] + 1.6)
        f = 0.0
        if t >= M["fart"]:
            f = clamp(1 - max(0, t - (M["fart"] + 3.4)) / 0.4)
        under_desk_shot(c, t, tremble=tr * (1 - 0.5 * f), fart=f, can_fall=lin(t, M["fart"] + 1.45, M["fart"] + 1.75),
                        bag_blow=lin(t, M["fart"] + 0.3, M["fart"] + 2.0))
        if t >= M["fart"]:
            comic_text(c, "BRRRAAAAP", 360, 200, 76, "#9be15d", t, M["fart"] + 0.15, -5 + 4 * math.sin(t * 9), True, "#5a2d82")
        return
    if M["squelch"] <= t < M["D5"] - 0.05:
        u = t - M["squelch"]
        if u > 0.25:
            under_desk_shot(c, t, tremble=0.3, stain=ramp(t, M["squelch"] + 0.25, M["squelch"] + 0.9))
            comic_text(c, "SQUELCH", 360, 200, 72, "#c68b59", t, M["squelch"] + 0.3, 4, True, "#3a2a1a")
            return
    gv = lerp(0.2, 0.78, ramp(t, M["D1"], M["D1_end"] + 2.4))
    if t < M["D3"] - 0.05:
        # face close-up: suppression
        bl = blink(t, 11, 2.4)
        clamp_ = ramp(t, M["D1"] + 0.5, M["D1"] + 0.8)
        water = ramp(t, M["D1"] + 1.6, M["D1"] + 2.4)
        tom = ramp(t, M["D1"] + 2.6, M["D1_end"])
        trem = ramp(t, M["tremble"], M["tremble"] + 0.4)
        puffk = 0.35 * clamp_ + 0.45 * tom + trem * (0.25 + 0.2 * abs(math.sin(t * 6.5 * math.pi)))
        P = P_(t=t, lid=lerp(1.0, 0.7, water) * bl, lower=0.25 * water, wobble=clamp_ * (1 + trem), smile=-0.05, puff=puffk,
               red=0.15 + 0.85 * tom, tears=0.3 * water + 0.6 * tom, sweat=0.4 + 0.6 * trem, brow_ang=0.7, brow_y=0.4,
               px=0.05 * vnoise(t * 8), py=0.0, pr=0.8)
        down = ramp(t, M["D2"] + 0.3, M["D2"] + 1.0)
        if down > 0:
            P.update(py=0.9 * down, px=0, brow_ang=1.0, lid=1.05 * bl)
        sh = 0.4 * trem + 0.3 * tom
        lord_face_shot(c, t, P, 360, 640, 1.95, "room", sh, 1.0 + 0.08 * ramp(t, M["D1"], M["D2"]), light="#ff8a8a", light_a=0.2)
        tomato(c, 600, 380, ease_out_back(clamp((t - (M["D1"] + 3.1)) / 0.35), 2) * (1 - ramp(t, M["tremble"], M["tremble"] + 0.3)))
        if trem > 0:
            for s in (-1, 1):
                for k in range(3):
                    ph = (t * 1.5 + k / 3) % 1
                    x = 360 + s * (230 + 120 * ph)
                    y = 640 - 40 - 80 * ph
                    c.drawPath(blob(x, y, 20 + 30 * ph, 7, 0.2, t, k), fill("#ffffff", 0.6 * (1 - ph) * trem))
            if (t * 3) % 1 < 0.5:
                text(c, "pfft", 520, 820, "bangers", 48, "#ffffff", outline=OUT, ow=6, a=trem)
        gauge(c, 120, 220, 85, gv, t, a=ramp(t, M["D1"] + 0.3, M["D1"] + 0.8))
        return
    # medium shot: surrender flag, darting eyes, then horror
    bl = blink(t, 12, 2.6)
    dart_eyes = math.sin((t - M["D3"]) * 5) * 0.8
    P = P_(t=t, lid=1.0 * bl, px=dart_eyes, py=0.0, red=0.85, puff=0.2, wobble=0.6, tears=0.5, sweat=0.9, brow_ang=0.8,
           brow_y=0.3)
    body = dict(poseL="clutch", poseR="type", blendR=("flag", ramp(t, M["D3"] + 0.2, M["D3"] + 0.7)), flag=ramp(t, M["D3"] + 0.4, M["D3"] + 0.9),
                typing=0.0)
    if t >= M["D4"] - 0.2:
        P.update(px=0, lid=0.75 * bl, smile=0.1, wobble=0.3, mouth_open=talk("D4", t) * 0.5, red=0.7, puff=0.0)
    zoom, shake = 1.22, 0.0
    if t >= M["squelch"]:
        u = t - M["squelch"]
        P.update(lid=1.25, pr=0.3, px=0, py=0.2, red=0.2, pale=0.7, smile=-0.3, wobble=1.0, mouth_open=0, brow_ang=1.0, brow_y=1.0)
        body["flag"] = 1 - ramp(t, M["squelch"], M["squelch"] + 0.3)
        zoom = 1.22 + 0.4 * ease_out_back(clamp(u / 0.2))
        shake = max(0, 1 - u * 3)
    if t >= M["D5"] - 0.05:
        P.update(lid=1.1, pr=0.5, py=0.9, px=0, tears=1.0, pale=0.6, red=0.0, smile=-0.6, wobble=0.6, brow_ang=1.0)
        P["lidR"] = 1.1 if (t * 7) % 1 > 0.2 else 0.6  # lid twitch
        zoom = 1.8
    lord_desk_shot(c, t, P, zoom, (390, 560) if t < M["squelch"] else (360, 600), shake, body=body)
    if t < M["D4"]:
        gauge(c, 120, 220, 85, 0.8, t)


def sc_defense(c, t):
    lt = t - M["defense"]
    c.drawRect(skia.Rect.MakeWH(W, H), rad_grad(360, 500, 900, ["#5b3a8c", "#1b1033"], [0, 1]))
    for i in range(6):
        a = lt * 0.2 + i
        c.drawCircle(360 + 260 * math.cos(a * 0.7 + i), 500 + 300 * math.sin(a * 0.5 + i * 2), 120, fill("#8a5cff", 0.06, blur=30))
    b1, b2, b3, brk = M["bubble1"], M["bubble2"], M["bubble3"], M["gauge_break"]
    # Lord head at bottom
    bl = blink(t, 13, 2.2)
    P = P_(t=t, squeeze=1.0, smile=-0.1, wobble=0.5, sweat=0.7, brow_ang=0.9, brow_y=0.2, red=0.35, puff=0.1)
    P["mouth_open"] = talk("E2", t) * 0.7
    if t > M["E2_end"]:
        P["mouth_open"] = 0
    gv = 0.62
    if t >= b1:
        gv = lerp(0.62, 0.48, ramp(t, M["E4"], M["E4"] + 1.5))
        P.update(smile=0.05, wobble=0.2, red=0.3)
    if t >= M["nod_fast"]:
        u = ramp(t, M["nod_fast"], M["nod_fast"] + 1.0)
        gv = lerp(0.48, 0.68, u)
        P.update(puff=0.5 * u, wobble=1.0, red=0.45)
    if t >= b2:
        u = ramp(t, M["E6"], M["E6_end"])
        gv = lerp(0.68, 0.84, u)
        P.update(puff=0.4 + 0.3 * u, red=0.5 + 0.2 * u, wobble=1.0)
        if M["E6_end"] - 0.6 < t < M["E6_end"] + 0.2:
            P["browR"] = 0.8 * abs(math.sin(t * 30))
    if t >= b3:
        u = ramp(t, M["E7"], M["couple_turn"])
        gv = lerp(0.84, 0.95, u)
        P.update(puff=0.6 + 0.2 * u, red=0.7 + 0.2 * u)
    if t >= M["couple_turn"]:
        u = ramp(t, M["couple_turn"], M["couple_turn"] + 0.3)
        P.update(squeeze=0.0, lid=1.2, pr=0.35, px=0, py=-0.6, red=0.95, puff=0.8)
        gv = lerp(0.95, 1.02, u)
    if t >= M["E10"]:
        gv = lerp(1.02, 1.12, ramp(t, M["E10"], brk))
        P.update(puff=0.9 + 0.1 * math.sin(t * 30), wobble=1.3)
    shake = 0.25 + (1.0 if t > M["E10"] else 0) * 0.8
    pose = "temple"
    at(c, 360 + shake * 5 * math.sin(t * 50), 1060, 0.95)
    lord_body(c, P, poseL="temple", poseR="temple", t=t, typing=0)
    c.restore()
    gauge(c, 100, 1010, 66, gv, t, broken=ramp(t, brk - 0.05, brk + 0.1))
    # thought bubble
    pop = ramp(t, brk, brk + 0.2)
    if pop >= 1:
        return
    grow = ease_out_back(clamp((t - M["E1"] - 0.3) / 0.5), 1.4)
    if grow <= 0:
        return
    trail = [(560, 860, 11 * grow), (585, 805, 17 * grow), (600, 742, 24 * grow)]
    cx, cy, bw, bh = 360, 400, 670 * grow, 600 * grow
    shake_b = ramp(t, M["E10"], brk) * 2
    p = bubble_cloud(c, cx, cy, bw, bh, t, trail, 0.03, shake_b)
    c.save()
    c.clipPath(p, skia.ClipOp.kIntersect, True)
    if t < b1:
        draw_fortress(c, t)
    elif t < b2:
        draw_therapy(c, t)
    elif t < b3:
        draw_sjw(c, t)
    else:
        draw_suburb(c, t)
    for bt in (b1, b2, b3):
        if bt <= t < bt + 0.3:
            c.drawRect(skia.Rect.MakeWH(W, H), fill("#ffffff", 1 - (t - bt) / 0.3))
    if t > M["E10"]:
        k = ramp(t, M["E10"], brk)
        for i in range(int(2 + 8 * k)):
            a0 = i * 2.4
            pts = [(cx + math.cos(a0) * 40, cy + math.sin(a0) * 40)]
            for j in range(1, 6):
                pts.append((cx + math.cos(a0 + 0.2 * hash1(i * 7 + j)) * 70 * j * k, cy + math.sin(a0 + 0.2 * hash1(i * 5 + j)) * 60 * j * k))
            c.drawPath(poly(pts, False), stroke(OUT, 5))
    c.restore()
    c.drawPath(p, stroke(OUT, 6))
    if pop > 0:
        c.drawRect(skia.Rect.MakeWH(W, H), fill("#ffffff", pop * 0.9))


def draw_fortress(c, t):
    c.drawRect(skia.Rect.MakeLTRB(0, 100, W, 720), lin_grad(0, 100, 0, 720, ["#c8d6e5", "#8395a7"]))
    n = int(clamp((t - M["E1"] - 0.6) / 4.5) * 48)
    k = 0
    for row in range(6):
        for col_ in range(8):
            if k >= n:
                break
            x = 120 + col_ * 60 + (30 if row % 2 else 0)
            y = 600 - row * 34
            if x > 560:
                continue
            fs(c, rrect(x, y, 56, 30, 4), "#9aa5b1", 3)
            k += 1
    for tx in (130, 530):
        if n > 30:
            fs(c, rrect(tx - 10, 330, 80, 300, 4), "#9aa5b1", 4)
            for j in range(3):
                fs(c, rrect(tx - 10 + j * 30, 300, 22, 32, 3), "#9aa5b1", 3)
    if n > 40:
        a = ramp(t, M["E2"] - 0.5, M["E2"])
        at(c, 360, 230, ease_out_back(a, 2), -3)
        fs(c, rrect(-230, -40, 460, 70, 10), "#e63946", 5, a=a)
        text(c, "FORTRESS OF UNFUNNY", 0, 14, "bangers", 42, "#ffffff", a=a)
        c.restore()


def draw_therapy(c, t):
    c.drawRect(skia.Rect.MakeLTRB(0, 100, W, 720), lin_grad(0, 100, 0, 720, ["#efe3cf", "#d9c7a8"]))
    fs(c, rrect(470, 180, 130, 100, 4), "#ffffff", 5, "#8a6a3a")
    text(c, "Ph.D.", 535, 240, "fredoka", 30, "#8a6a3a")
    fs(c, rrect(90, 520, 80, 100, 10), "#b5651d", 4)
    for i in range(5):
        a = math.radians(-160 + i * 35)
        c.drawPath(oval(130 + math.cos(a) * 40, 490 + math.sin(a) * 50, 14, 30), fill("#4a9a4a"))
    fs(c, rrect(170, 420, 380, 320, 60), "#7a4a2a", 5)
    nodf = 0.55
    amp = 1.0
    if t >= M["nod_fast"]:
        u = ramp(t, M["nod_fast"], M["nod_fast"] + 1.2)
        nodf = lerp(0.55, 4.0, u)
        amp = lerp(1.0, 1.6, u)
    ph = (t - M["bubble1"]) * nodf * 2 * math.pi if t < M["nod_fast"] else (M["nod_fast"] - M["bubble1"]) * 0.55 * 2 * math.pi + (t - M["nod_fast"]) * nodf * 2 * math.pi
    nod = amp * (0.5 + 0.5 * math.sin(ph))
    bl = blink(t, 21, 3.0)
    P = P_(t=t, lid=0.5 * bl, smile=0.1, mouth_open=talk("E4", t), brow_y=0.1, py=0.1)
    at(c, 360, 400, 0.8)
    therapist(c, P, t, nod)
    c.restore()
    if t > M["nod_fast"] + 0.3:
        text(c, "*nod nod nod*", 360, 180, "bangers", 44, "#5a3a1a", a=ramp(t, M["nod_fast"] + 0.3, M["nod_fast"] + 0.6))


def draw_sjw(c, t):
    c.drawRect(skia.Rect.MakeLTRB(0, 100, W, 720), fill("#e8f1ff"))
    fs(c, rrect(150, 132, 420, 50, 25), "#ffffff", 3, "#aab8d0")
    c.drawCircle(178, 157, 16, fill("#2ec4b6"))
    text(c, "@ChartsAndFeelings · thread 1/97", 200, 165, "inter_bold", 19, "#1d2a44", align="left")
    bl = blink(t, 23, 2.5)
    talking = talk("E6", t)
    P = P_(t=t, lid=1.05 * bl, smile=0.25, mouth_open=talking, brow_ang=0.4 + 0.3 * math.sin(t * 3), brow_y=0.4, py=-0.1, px=0.1 * math.sin(t))
    xs = ramp(t, M["E6_end"] - 1.9, M["E6_end"] - 1.5)
    at(c, 360, 292, 0.6)
    sjw(c, P, t, chart_shake=talking, x_stamp=xs)
    c.restore()


def draw_suburb(c, t):
    c.drawRect(skia.Rect.MakeLTRB(0, 100, W, 720), lin_grad(0, 100, 0, 720, ["#7fd3ff", "#d6f3ff"]))
    c.drawCircle(560, 200, 50, fill("#fff3a0"))
    c.drawCircle(560, 200, 80, fill("#fff3a0", 0.3, blur=10))
    # house
    fs(c, rrect(70, 300, 230, 200, 4), "#f4e1c1", 5)
    fs(c, poly([(50, 310), (185, 210), (320, 310)]), "#c0392b", 5)
    fs(c, rrect(160, 400, 50, 100, 4), "#6b4226", 4)
    for wx in (95, 235):
        fs(c, rrect(wx, 340, 45, 45, 3), "#a8e0ff", 4)
    c.drawRect(skia.Rect.MakeLTRB(0, 520, W, 720), lin_grad(0, 520, 0, 720, ["#6abf4b", "#4a9a35"]))
    # picket fence
    for i in range(16):
        x = 10 + i * 46
        fs(c, poly([(x, 560), (x, 488), (x + 14, 472), (x + 28, 488), (x + 28, 560)]), "#ffffff", 3)
    c.drawRect(skia.Rect.MakeLTRB(0, 505, W, 518), fill("#ffffff"))
    c.drawPath(poly([(0, 505), (W, 505)], False), stroke(OUT, 2))
    turn = ramp(t, M["couple_turn"], M["couple_turn"] + 0.6)
    sipu = pulse(t, M["slurp"] - 0.1, 1.1)
    bl = blink(t, 25, 3.0)
    creepy = turn
    Pg = P_(t=t, lid=lerp(0.95, 1.25, creepy) * (bl if creepy < 0.5 else 1), smile=lerp(0.7, 1.0, creepy), teeth=creepy > 0.3,
            mouth_open=max(talk("E8", t), 0.25 * creepy), px=lerp(0.6, 0.0, creepy), pr=lerp(1, 0.6, creepy), brow_y=0.3 * creepy)
    Pl = P_(t=t, lid=lerp(0.95, 1.25, creepy) * (bl if creepy < 0.5 else 1), smile=lerp(0.6, 1.0, creepy), teeth=creepy > 0.3,
            mouth_open=max(talk("E9", t), 0.25 * creepy), px=lerp(-0.6, 0.0, creepy), pr=lerp(1, 0.6, creepy), brow_y=0.3 * creepy)
    mow_x = lerp(150, 300, clamp((t - M["bubble3"]) / 10))
    if t > M["E8"] - 0.3:
        mow_x = lerp(150, 300, clamp((M["E8"] - 0.3 - M["bubble3"]) / 10))
    lawnmower(c, mow_x + 80, 690, t if t < M["E8"] else 0, 0.75)
    at(c, mow_x, 690, 0.95)
    suburb_person(c, Pg, t, "greg", turn, 0, 0)
    c.restore()
    at(c, 470, 690, 0.95)
    suburb_person(c, Pl, t, "linda", turn, sipu, 0)
    c.restore()
    dog(c, 600, 700, t, 0.75, pulse(t, M["woof"], 0.25) + pulse(t, M["woof"] + 0.32, 0.25))
    if M["slurp"] - 0.1 < t < M["slurp"] + 0.9:
        text(c, "*slurrrp*", 470, 300, "bangers", 40, "#6b4226", outline="#ffffff", ow=5)
    if t > M["woof"]:
        comic_text(c, "WOOF", 600, 470, 50, "#ffffff", t, M["woof"], 8, True, "#e0a040")


def sc_collapse(c, t):
    if t < M["thud"]:
        u = lin(t, M["slide"], M["thud"])
        P = P_(t=t, lid=1.2, pr=0.3, puff=1.0 - u, red=0.9, mouth_open=0.6 * u, smile=-0.3, brow_ang=1.0, brow_y=0.8, sweat=1)
        body = dict(poseL="up", poseR="up", typing=0, head_rot=8 * u)
        c.save()
        lord_desk_shot_slide(c, t, P, body, u)
        c.restore()
        flash(c, t, M["collapse"], 0.2)
        return
    d = clamp((t - M["deflate_start"]) / (M["honk"] - M["deflate_start"])) ** 0.9
    lt = t - M["deflate_start"]
    # chuckle pulse in mouth + gas
    chuck = 0.5 + 0.5 * math.sin(lt * 2 * math.pi * (5.5 - 2.5 * d))
    mouth = (0.45 + 0.35 * chuck * (1 - d)) if t > M["deflate_start"] else 0.2
    head_drop = 0.0
    tr = M["trombone"]
    steps = [tr, tr + 0.45, tr + 0.9, tr + 1.35]
    for i, st in enumerate(steps):
        head_drop += 0.25 * ramp(t, st, st + 0.25)
    impact = max(0, 1 - (t - M["thud"]) * 4)
    honk = pulse(t, M["honk"], 0.25) + pulse(t, M["honk"] + 0.42, 0.4)
    clown = ramp(t, M["F4"] + 1.3, M["F4"] + 1.6)
    c.save()
    cam(c, 1.0 + 0.06 * impact, 360, 640, shake=impact * 2, t=t)
    heap_shot(c, t, d=d, mouth=mouth, gas=ramp(t, M["deflate_start"], M["deflate_start"] + 1) * (1 - 0.5 * d), streak=ramp(t, M["deflate_start"] + 1, M["deflate_start"] + 7),
              puddle=ramp(t, M["deflate_start"] + 6, M["honk"]), head_drop=head_drop, clown=clown, honk=honk, impact=impact,
              P_over=dict(lid=0.5 - 0.2 * d if t > M["deflate_start"] else 1.1, squeeze=0))
    # dust puff on impact
    if impact > 0:
        for i in range(8):
            a = math.pi * (1 + i / 7)
            r = 200 + 200 * (1 - impact)
            c.drawPath(blob(360 + math.cos(a) * r, 900 + math.sin(a) * r * 0.3, 40, 7, 0.2, t, i), fill("#c8c0b0", impact * 0.7))
    c.restore()
    # ghost
    if t > M["ghost"]:
        u = clamp((t - M["ghost"]) / 7.5)
        gx = 360 + 80 * math.sin(u * 7)
        gy = lerp(700, -260, u)
        ghost(c, gx, gy, t, lerp(0.4, 1.1, clamp(u * 3)), 0.85 * clamp(u * 6))
    # warning banner
    if M["F2"] + 1.2 < t < M["F2"] + 5.0:
        a = ramp(t, M["F2"] + 1.2, M["F2"] + 1.4) * (1 - ramp(t, M["F2"] + 4.6, M["F2"] + 5.0))
        c.saveLayerAlpha(None, int(255 * a))
        c.drawRect(skia.Rect.MakeLTRB(0, 200, W, 290), fill("#ffd23f"))
        for i in range(20):
            x = i * 60 - (t * 80 % 60)
            c.drawPath(poly([(x, 200), (x + 30, 200), (x + 0, 290), (x - 30, 290)]), fill("#111111"))
        fs(c, rrect(70, 215, 580, 60, 8), "#111111", 0, None)
        text(c, "SOUL EVACUATION IN PROGRESS", 360, 256, "inter_black", 30, "#ffd23f")
        c.restore()
    # deflation timer
    if t > M["deflate_start"]:
        secs = 60 * clamp((t - M["deflate_start"]) / (M["honk"] - M["deflate_start"]))
        big = ramp(t, M["F5"], M["F5"] + 0.4) * (1 - ramp(t, M["trombone"] - 0.3, M["trombone"]))
        x, y = lerp(360, 360, big), lerp(110, 470, big)
        s = lerp(1.0, 2.2, big)
        at(c, x, y, s)
        fs(c, rrect(-170, -48, 340, 96, 20), "#111122", 4, "#ffffff", a=0.9)
        text(c, "DEFLATION", -60, -14, "inter_black", 18, "#ff9ad5")
        text(c, "▶▶ x2", -60, 14, "mono", 18, "#7ef0ff")
        done = secs >= 59.99
        text(c, "%d:%02d" % (int(secs) // 60, int(secs) % 60), 80, 22, "mono", 58, "#ffd23f" if not done else "#3dff6e")
        c.restore()
    black(c, ramp(t, M["webcam"] - 0.5, M["webcam"]))


def lord_desk_shot_slide(c, t, P, body, u):
    bg_lord_room(c, t)
    chair_back(c, 360, 650)
    drop = 700 * (u ** 1.6)
    at(c, 360, 590 + drop, 1.0, 6 * u)
    lord_body(c, P, t=t, **body)
    c.restore()
    # flying fedora
    if u > 0:
        at(c, 360 + 120 * u, 410 - 260 * math.sin(math.pi * min(u, 1)), 1.0, 200 * u)
        fs(c, oval(0, 2, 150, 26), "#2f2d36", 5)
        fs(c, smooth_path([(-82, 0), (-90, -60), (-30, -98), (0, -82), (30, -98), (90, -60), (82, 0)]), "#3a3842", 5)
        c.restore()
    desk(c, 975)
    laptop_back(c, 360, 925, 410, 190, "lord", t=t)
    cheeto_bag(c, 95, 1090, 0.95)
    cans_pyramid(c, 610, 1110, t, 1.0)


def sc_webcam(c, t):
    if t < M["pov"]:
        u = ramp(t, M["G1"], M["webcam_on"])
        z = lerp(1.6, 2.8, u)
        flare = pulse(t, M["webcam_on"], 0.5)
        webcam_closeup(c, t, z + 0.3 * ease_out_back(clamp((t - M["webcam_on"]) / 0.2)) * (t > M["webcam_on"]), rec=ramp(t, M["webcam_on"], M["webcam_on"] + 0.3), led_flare=flare)
        flash(c, t, M["webcam_on"], 0.25, "#3dff6e", 0.5)
        black(c, 1 - ramp(t, M["webcam"], M["webcam"] + 0.6))
        return
    peek = ramp(t, M["pov"] + 0.8, M["pov"] + 1.6)
    bl = blink(t, 30, 2.5)
    P = P_(t=t, lid=0.55 * bl, lower=0.2, py=-0.1, px=0.15, tears=0.7, mouth_open=talk("G3", t) * 0.6, smile=-0.5, brow_ang=1.0,
           pale=0.3, sweat=0.3)
    webcam_pov(c, t, peek, P, glitch=ramp(t, M["viral"] - 0.6, M["viral"]))


VIEWS = [(0, "1"), (0.5, "214"), (1.0, "3.1K"), (1.4, "88K"), (1.8, "1.4M"), (2.2, "27M"), (2.6, "310M"), (3.0, "1.2B")]
COMMENTS = ["the HONK at 0:59 lmaooo", "bro deflated like a pool float", "the anti-fun ghost has a FEDORA",
            "peer-reviewed by laughter", "certified meme science", "Logical Lord has left the chat", "remix when??"]


def sc_viral(c, t):
    lt = t - M["viral"]
    c.drawRect(skia.Rect.MakeWH(W, H), fill("#0f0f17"))
    # header
    c.drawRect(skia.Rect.MakeLTRB(0, 0, W, 110), fill("#181826"))
    c.drawPath(rrect(30, 38, 60, 42, 12), fill("#ff2e88"))
    c.drawPath(poly([(52, 48), (52, 70), (72, 59)]), fill("#ffffff"))
    text(c, "ViralHub", 105, 72, "inter_black", 34, "#ffffff", align="left")
    # video card with thumbnail (webcam still)
    c.save()
    c.clipPath(rrect(30, 140, 660, 420, 18), skia.ClipOp.kIntersect, True)
    c.translate(30, 140)
    c.scale(660 / W, 420 / 760)
    c.translate(0, -300)
    P = P_(t=t, lid=0.55, lower=0.2, tears=0.7, smile=-0.5, brow_ang=1.0, pale=0.3)
    webcam_pov(c, M["pov"] + 3.0, 1.0, P)
    c.restore()
    c.drawPath(rrect(30, 140, 660, 420, 18), stroke("#000000", 5))
    up = clamp((t - M["viral"]) / 1.0)
    if up < 1:
        c.drawRect(skia.Rect.MakeLTRB(30, 540, 30 + 660 * up, 560), fill("#ff2e88"))
        text(c, "uploading... %d%%" % int(up * 100), 360, 360, "inter_black", 40, "#ffffff", outline="#000000", ow=6)
    text(c, "logical lord DEFLATES for 1 full", 40, 610, "inter_black", 30, "#ffffff", align="left")
    text(c, "minute (webcam was on)", 40, 648, "inter_black", 30, "#ffffff", align="left")
    vs = "0"
    for (dt, v) in VIEWS:
        if lt - 1.2 >= dt:
            vs = v
    big = 1.0 + 0.15 * pulse((lt - 1.2) % 0.4, 0, 0.12) if 1.2 < lt < 4.4 else 1.0
    at(c, 40, 712, big)
    text(c, vs + " views", 0, 0, "inter_black", 40 if vs != "1.2B" else 46, "#ffd23f", align="left")
    c.restore()
    text(c, "• just now", 470, 712, "inter_bold", 24, "#9a9ab8", align="left")
    # comments
    y = 760
    for i, cm in enumerate(COMMENTS):
        ts = M["viral"] + 1.5 + i * 0.52
        if t < ts:
            break
        u = ease_out_back(clamp((t - ts) / 0.25), 2)
        yy = 765 + i * 52
        if yy > 1260:
            break
        at(c, 40 + 600 * (1 - u), yy)
        c.drawCircle(22, 22, 20, fill(["#ff5fa2", "#7ef0ff", "#ffd23f", "#9be15d", "#b14cff"][i % 5]))
        fs(c, rrect(54, 0, 560, 46, 14), "#20202f", 0, None)
        text(c, cm, 72, 32, "fredoka_semi", 25, "#ffffff", align="left")
        c.restore()
    if t > M["H2"]:
        u = ramp(t, M["H2"], M["H2"] + 0.3)
        at(c, 360, 640, ease_out_back(u, 2), -4)
        fs(c, rrect(-250, -60, 500, 110, 20), "#ff2e88", 6)
        text(c, "AUTOTUNED!!", 0, 18, "bangers", 66, "#ffffff", outline=OUT, ow=8)
        c.restore()
    black(c, 1 - ramp(t, M["viral"], M["viral"] + 0.2))
    flash(c, t, M["remix"] - 0.2, 0.2)


def sc_remix(c, t):
    lt = t - M["remix"]
    b = 0.5
    beat = (lt / b) % 1.0
    bar = int(lt / 2.0)
    kickp = (1 - beat) ** 3 if bar >= 2 else ((1 - (lt % 2.0) / 2.0) ** 3 if True else 0)
    # synthwave
    c.drawRect(skia.Rect.MakeWH(W, H), lin_grad(0, 0, 0, 760, ["#12002e", "#5b0b6e", "#ff2e88"], [0, 0.6, 1]))
    sunp = skia.Path()
    sunp.addCircle(360, 640, 210)
    c.save()
    c.clipPath(sunp, skia.ClipOp.kIntersect, True)
    c.drawRect(skia.Rect.MakeLTRB(150, 430, 570, 850), lin_grad(0, 430, 0, 850, ["#ffe14d", "#ff5fa2"]))
    for i in range(7):
        y = 560 + i * 26
        c.drawRect(skia.Rect.MakeLTRB(140, y, 580, y + 4 + i * 2), fill("#5b0b6e"))
    c.restore()
    c.drawRect(skia.Rect.MakeLTRB(0, 760, W, H), fill("#14002a"))
    for i in range(-12, 13):
        c.drawPath(poly([(360 + i * 18, 760), (360 + i * 140, H)], False), stroke("#ff2e88", 3, 0.8))
    for k in range(10):
        u = ((k + (lt * 2) % 1.0) / 10) ** 2
        y = 760 + u * (H - 760)
        c.drawPath(poly([(0, y), (W, y)], False), stroke("#ff2e88", 3, 0.8))
    # title
    tw = 1 + 0.06 * kickp
    at(c, 360, 110, tw, -3)
    text(c, "LOGICAL REDDITOR'S", 0, 0, "bangers", 58, "#7ef0ff", outline=OUT, ow=10)
    text(c, "LAMENT (REMIX)", 0, 62, "bangers", 64, "#ffd23f", outline=OUT, ow=10)
    c.restore()
    # lyrics
    vox = [("R1", "I'M THE LOGICAL LORD"), ("R2", "IF I LAUGH, I LOSE")][bar % 2]
    a = ramp(lt % 2.0, 0.0, 0.1) * (1 - ramp(lt % 2.0, 1.6, 1.9))
    at(c, 360, 300, 1 + 0.05 * kickp)
    text(c, vox[1], 0, 0, "bangers", 56, "#ffffff", outline="#ff2e88", ow=10, a=a)
    c.restore()
    # mouth from vocal envelopes (lyrics are re-timed onto each bar)
    rid = vox[0]
    env = LIPS[rid]
    idx = int((lt % 2.0 - 0.05) * 24)
    mo = env[idx] * 0.9 if 0 <= idx < len(env) else 0.0
    # Lord head bopping
    bop = math.sin(lt * math.pi * 2 / b * 0.5) if bar >= 2 else 0.3 * math.sin(lt * 3)
    sung = ramp(lt, 4.0, 4.3)
    P = P_(t=t, lid=0.5, smile=0.4, mouth_open=clamp(mo), teeth=True, brow_y=0.4, tears=0.0, red=0.2)
    at(c, 360 + 30 * bop, 760 - 30 * abs(bop) - 20 * kickp, 1.35 + 0.05 * kickp, 10 * bop)
    lord_head(c, P, fedora=True, fedora_tilt=10 * bop, deflate=0.3, clown_nose=1.0, sunglasses=sung)
    c.restore()
    # ghost dancer
    ghost(c, 600 + 20 * math.sin(lt * 6.28), 520 + 30 * abs(math.sin(lt * 6.28)), t, 0.6, 0.85)
    # EQ bars
    for i in range(14):
        hgt = 40 + 200 * abs(vnoise(lt * 6 + i * 3, i)) * (0.4 + 0.6 * kickp) * (1 if bar >= 2 else 0.4)
        x = 40 + i * 47
        c.drawRect(skia.Rect.MakeLTRB(x, 1250 - hgt, x + 34, 1250), lin_grad(0, 1250 - hgt, 0, 1250, ["#7ef0ff", "#ff2e88"]))
    # honk bursts
    honks = [M["remix"] + 2 + 1.5] + [M["remix"] + i * 2 + 1.75 for i in (3, 5, 7)]
    for ht in honks:
        if ht <= t < ht + 0.6:
            comic_text(c, "HONK!", 160 if int(ht) % 2 else 560, 470, 70, "#ffffff", t, ht, -10, True, "#e8202a")
    flash(c, t, M["remix"] + 4.0, 0.25, "#ffffff", 0.7)
    if M["remix"] + 3.75 < t < M["remix"] + 4.0:
        c.drawRect(skia.Rect.MakeWH(W, H), fill("#000000", 0.6))
    black(c, ramp(t, M["moral"] - 0.3, M["moral"]))


def sc_moral(c, t):
    lt = t - M["moral"]
    c.save()
    cam(c, 1.0 + 0.03 * lt / 14, 360, 700)
    c.drawRect(skia.Rect.MakeWH(W, H), lin_grad(0, 0, 0, H, ["#ffc98b", "#e88a6a", "#5a3a5e"], [0, 0.5, 1]))
    fs(c, rrect(470, 150, 210, 260, 10), "#ffd9a0", 7, "#5a3a2a")
    c.drawCircle(600, 260, 40, fill("#fff6d6"))
    pts = [(x, 70 + 30 * math.sin(x / 720 * math.pi)) for x in range(0, 740, 60)]
    c.drawPath(smooth_path(pts, False), stroke("#3b2a20", 3))
    for i, (x, y) in enumerate(pts):
        cc = ["#ffd23f", "#ff6b6b", "#7ef0ff", "#9be15d"][i % 4]
        c.drawCircle(x, y + 12, 7, fill(cc))
    seen = ramp(t, M["moral_notif"] + 0.5, M["moral_notif"] + 0.8)
    bl = blink(t, 40, 3.0)
    mug = 1 - ramp(t, M["I1"] - 0.4, M["I1"])
    P = P_(t=t, lid=lerp(0.9, 1.15, seen) * bl, py=lerp(0.4, -0.5, seen), px=lerp(0, 0.4, seen), smile=0.5 + 0.4 * seen,
           teeth=seen > 0.5, brow_y=0.6 * seen, blush=0.4)
    if t > M["I1"]:
        P.update(px=0, py=0, lid=0.85 * bl, browR=0.9, browL=-0.1, brow_y=0.1, smile=0.6, asym=0.5, teeth=False)
    if t > M["I2"]:
        P.update(browR=0.3, smile=0.9, asym=0.0, teeth=True, lid=0.9 * bl)
    if t > M["I3"]:
        P.update(px=0.5 * math.sin(t), py=-0.3, lid=1.0 * bl, smile=0.8)
    if t > M["I4"]:
        P.update(px=0, py=0, lid=0.0, happy=1.0, smile=1.0)
    enter = lin(t, M["post_again"] - 0.65, M["post_again"] - 0.25)
    nod = pulse(t, M["I2"] + 0.4, 0.4) + pulse(t, M["I2"] + 0.9, 0.4)
    at(c, 360, 600, 1.0)
    creator_body(c, P, t=t, mug=mug, head_dy=8 * nod, enter=enter if enter < 1 else 1)
    c.restore()
    desk(c, 985, "#6b4a35")
    laptop_back(c, 360, 935, 410, 190, "creator", t=t)
    c.restore()
    # notification
    na = ramp(t, M["moral_notif"] + 0.2, M["moral_notif"] + 0.5) * (1 - ramp(t, M["I2"] - 0.3, M["I2"]))
    if na > 0:
        at(c, 0, -40 * (1 - na))
        panel(c, 40, 70, 640, 190, "Notification", "#5a4bd6", a=na)
        c.saveLayerAlpha(None, int(255 * na))
        text(c, "Your post broke a Logical Lord.", 70, 165, "inter_black", 30, "#ffffff", align="left")
        text(c, "1.2B views • 47M 'I can't breathe's", 70, 210, "fredoka_semi", 26, "#ffd23f", align="left")
        c.restore()
        c.restore()
    if t > M["I2"] + 0.1:
        u = clamp((t - M["I2"] - 0.1) / 0.3)
        out = ramp(t, M["I3"] + 2.0, M["I3"] + 2.3)
        at(c, 360, 230 - 400 * out, ease_out_back(u, 3), -4)
        text(c, "POST THE", 0, 0, "bangers", 110, "#ffd23f", outline=OUT, ow=14, shadow=True)
        text(c, "DAMN MEME.", 0, 105, "bangers", 120, "#ff5fa2", outline=OUT, ow=14, shadow=True)
        c.restore()
    if t > M["post_again"]:
        u = clamp((t - M["post_again"]) / 4.0)
        x = 360 + 250 * math.sin(u * 2 * math.pi)
        y = 800 - 520 * math.sin(u * math.pi) - 120 * u
        sparkles(c, [(x - 40 * k * math.cos(u * 6), y + 30 * k) for k in range(1, 5)], t)
        paper_plane(c, x, y, -40 + 360 * u, 1.3)
    if t > M["I3"] + 2.3:
        a = ramp(t, M["I3"] + 2.3, M["I3"] + 2.6)
        at(c, 360, 260, ease_out_back(a, 2), 3)
        text(c, "CATALYST FOR", 0, 0, "bangers", 84, "#7ef0ff", outline=OUT, ow=12, shadow=True)
        text(c, "CHAOS & COMEDY", 0, 84, "bangers", 84, "#ffd23f", outline=OUT, ow=12, shadow=True)
        c.restore()
    if t > M["I4"]:
        a = ramp(t, M["I4"], M["I4"] + 0.3)
        k = clamp((t - M["I4"]) / 2.4)
        vals = [1, 2, 3, 7, 47, 312, 1024]
        v = vals[min(len(vals) - 1, int(k * len(vals)))]
        at(c, 360, 1150, ease_out_back(a, 2))
        fs(c, rrect(-250, -50, 500, 90, 18), "#111122", 4, "#ffffff", a=0.9)
        text(c, "LORDS DEFLATED:", -40, 10, "inter_black", 28, "#ff9ad5")
        text(c, "{:,}".format(v), 175, 14, "mono", 40, "#3dff6e")
        c.restore()
    black(c, 1 - ramp(t, M["moral"], M["moral"] + 0.3))


def sc_end(c, t):
    lt = t - M["end"]
    c.drawRect(skia.Rect.MakeWH(W, H), rad_grad(360, 640, 900, ["#3a1f6b", "#0e0820"], [0, 1]))
    for i in range(40):
        x, y = (hash1(i * 3) * 0.5 + 0.5) * W, (hash1(i * 7) * 0.5 + 0.5) * H
        c.drawCircle(x, y, 2 + 1.5 * math.sin(t * 2 + i), fill("#ffffff", 0.7))
    u = ease_out_back(clamp(lt / 0.4), 2)
    at(c, 360, 300, u, -3)
    text(c, "KEEP GOING,", 0, 0, "bangers", 100, "#ffd23f", outline=OUT, ow=14, shadow=True)
    text(c, "YOU UNHINGED", 0, 100, "bangers", 100, "#7ef0ff", outline=OUT, ow=14, shadow=True)
    text(c, "GENIUS.", 0, 200, "bangers", 120, "#ff5fa2", outline=OUT, ow=14, shadow=True)
    c.restore()
    # balloon lord floating
    bx = lerp(-150, 520, clamp(lt / 6.0))
    by = 820 - 40 * math.sin(lt * 1.3)
    c.drawPath(smooth_path([(bx, by + 140), (bx - 20, by + 220), (bx + 15, by + 300), (bx - 10, by + 400)], False), stroke("#ffffff", 3))
    awake = M["stinger"] + 1.0
    P = P_(t=t, lid=0.0 if t < awake else 0.6, happy=0.0, smile=-0.2 if t < awake else 0.5, asym=0.0 if t < awake else 0.6,
           mouth_open=0.0)
    sq = pulse(t, M["stinger"], 0.4)
    at(c, bx, by, 0.85 * (1 + 0.1 * sq), 8 * math.sin(lt))
    lord_head(c, P, fedora=True, fedora_tilt=-10, deflate=0.5, clown_nose=1.0)
    c.drawPath(poly([(-10, 125), (10, 125), (0, 140)]), fill("#c9a68a"))
    c.restore()
    if t > awake:
        text(c, "heh.", bx + 120, by - 60, "bangers", 50, "#ffffff", outline=OUT, ow=8, a=ramp(t, awake, awake + 0.2))
    black(c, ramp(t, TL["duration"] - 0.8, TL["duration"] - 0.1))


SCENE_FN = {
    "intro": sc_intro, "title": sc_title, "lord_intro": sc_lord_intro, "post": sc_post, "xray": sc_xray,
    "panic": sc_panic, "suppress": sc_suppress, "defense": sc_defense, "collapse": sc_collapse,
    "webcam": sc_webcam, "viral": sc_viral, "remix": sc_remix, "moral": sc_moral, "end": sc_end,
}

CAP_Y = {"defense": 780, "xray": 1080, "viral": 1175, "intro": 985, "moral": 985, "collapse": 1215, "webcam": 760, "remix": 1060, "end": 1060}
SPK_COL = {"NARR": "#ffffff", "LORD": "#ffd23f", "WHISP": "#d9c2ff", "CREATOR": "#7ef0ff", "THER": "#ffc2d6",
           "SJW": "#ffc2d6", "GREG": "#ffc2d6", "LINDA": "#ffc2d6"}
NO_CAP = {"A3", "R1", "R2"}


def chunks_for(line):
    words = line["cap"].split()
    chunks, cur = [], []
    for w_ in words:
        cur.append(w_)
        s = " ".join(cur)
        if len(s) >= 22 or w_.endswith((".", "?", "!", ",", "...", "”")) and len(s) > 10:
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
                y = CAP_Y.get(scene, 975)
                u = clamp((t - s0 + 0.05) / 0.1)
                sc = 0.88 + 0.12 * ease_out_back(u, 2)
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
