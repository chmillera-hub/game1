"""Characters for 'The Assembly' (original designs)."""
import math
import skia
from gfx import *
from chars import P_, head_path, draw_eye, draw_brow, draw_mouth, sweat_drops

SKIN_A, SKIN_B, SKIN_C, SKIN_D = "#f4c79f", "#e0a878", "#b9774f", "#8a5636"


def _has(prop, name):
    return prop == name or (isinstance(prop, (tuple, list, set)) and name in prop)


def limb(c, a, b, w, color, outline=OUT):
    p = poly([a, b], False)
    c.drawPath(p, stroke(outline, w + 8))
    c.drawPath(p, stroke(color, w))


def vtorso(sw, ww, top, bot, neck=42):
    """broad shoulders tapering to a narrow waist"""
    p = skia.Path()
    p.moveTo(-neck, top)
    p.cubicTo(-sw * 0.62, top - 6, -sw, top + 4, -sw, top + 60)
    p.cubicTo(-sw * 0.98, top + 130, -ww * 1.12, bot - 80, -ww, bot)
    p.lineTo(ww, bot)
    p.cubicTo(ww * 1.12, bot - 80, sw * 0.98, top + 130, sw, top + 60)
    p.cubicTo(sw, top + 4, sw * 0.62, top - 6, neck, top)
    p.quadTo(0, top + 18, -neck, top)
    p.close()
    return p


def pecs(c, y, w, color, a=0.6):
    for s in (-1, 1):
        c.drawPath(smooth_path([(s * 8, y - 30), (s * w * 0.55, y + 8), (s * w, y - 18)], False), stroke(color, 4, a))


def two_seg(c, s, e, h, w1, w2, c1, c2):
    limb(c, s, e, w1, c1)
    limb(c, e, h, w2, c2)


def face(c, P, skin, eye_dx=38, eye_y=0, erx=22, ery=26, iris="#3a2a20", brow="#4a3020", brow_w=9, mouth_y=58, mouth_w=30,
         lash=OUT):
    for s in (-1, 1):
        draw_eye(c, s * eye_dx, eye_y, erx, ery, P, s, skin, iris=iris, lash=lash)
        extra = P["browL"] if s < 0 else P["browR"]
        draw_brow(c, s * eye_dx, eye_y - ery - 16 - P["brow_y"] * 12 - extra * 12, erx, P["brow_ang"], s, brow, brow_w)
    if P["blush"] > 0 or P["red"] > 0.25:
        a = max(P["blush"], P["red"] - 0.25)
        for s in (-1, 1):
            c.drawPath(oval(s * (eye_dx + 18), eye_y + 34, 20, 12), fill("#ff6a6a", 0.45 * clamp(a), blur=5))
    draw_mouth(c, 0, mouth_y + P["jaw"] * 6, mouth_w, P)


# ---------------------------------------------------------------------- Carter (bratty kid)
CARTER_POSES = {   # (hand L, hand R) relative to body centre; arms from shoulders (+-95, -40)
    "sit": ((-120, 80), (120, 80)),
    "grip": ((-150, 120), (150, 120)),
    "whisper": ((-120, 80), (55, -95)),
    "yell": ((-60, -110), (60, -110)),
    "shrug": ((-170, -40), (170, -40)),
    "flail": ((-170, -140), (170, -140)),
    "shield": ((-120, 80), (48, -150)),
    "proud": ((-120, 20), (120, 20)),
    "perform": ((-175, -90), (70, -95)),
    "small": ((-60, 70), (60, 70)),
    "point": ((-120, 80), (200, -60)),
    "beep": ((-120, 80), (110, -10)),
    "facepalm": ((-120, 80), (30, -170)),
    "fists": ((-140, -30), (140, -30)),
    "cross": ((70, 20), (-70, 20)),
    "stomp": ((-150, 100), (150, 100)),
    "cup": ((-70, -100), (70, -100)),
    "hold_mic": ((-150, 60), (60, -85)),
    "wave": ((-120, 80), (180, -170)),
}


def carter(c, P, t=0.0, pose="sit", blend=None, legs="sit", flail=0.0, mic=False, shake=0.0, fluff=0.0, walk=0.0):
    skin = hexs(mix(SKIN_A, "#e3322a", P["red"] * 0.4))
    jacket, jdark = "#7b4fd6", "#5b34b0"
    c.save()
    c.translate(shake * 5 * math.sin(t * 50), -6 * abs(math.sin(t * 7)) * walk)
    # legs
    if legs == "sit":
        for s in (-1, 1):
            fs(c, rrect(s * 55 - 32, 70, 64, 70, 24), "#5a4636", 5)
            fs(c, oval(s * 55, 150, 40, 20), "#1d1d22", 4)
    elif legs == "dangle":
        for s in (-1, 1):
            sw = 18 * math.sin(t * 14 + s) * flail
            fs(c, rrect(s * 50 - 28 + sw, 80, 56, 90, 24), "#5a4636", 5)
            fs(c, oval(s * 50 + sw * 1.4, 178, 36, 18), "#1d1d22", 4)
    else:  # stand
        for s in (-1, 1):
            st = 14 * math.sin(t * 7 + (0 if s < 0 else math.pi)) * walk
            fs(c, rrect(s * 50 - 30 + st, 80, 60, 80, 24), "#5a4636", 5)
            fs(c, oval(s * 55 + st * 1.2, 168, 44, 20), "#1d1d22", 4)
    # body (puffy jacket; 'fluff' = puffed up with pride)
    c.save()
    c.scale(1 + 0.16 * fluff, 1 + 0.06 * fluff)
    body = oval(0, 20, 150, 120)
    fs(c, body, jacket, 6)
    c.drawPath(poly([(0, -80), (0, 130)], False), stroke(jdark, 5))
    for k in range(3):
        c.drawPath(smooth_path([(-140, -20 + k * 45), (0, -8 + k * 45), (140, -20 + k * 45)], False), stroke(jdark, 3, 0.6))
    c.restore()
    # arms
    hl, hr = CARTER_POSES[pose]
    if blend:
        p2, u = blend
        hl2, hr2 = CARTER_POSES[p2]
        hl = (lerp(hl[0], hl2[0], u), lerp(hl[1], hl2[1], u))
        hr = (lerp(hr[0], hr2[0], u), lerp(hr[1], hr2[1], u))
    if flail > 0:
        hl = (hl[0] + 30 * math.sin(t * 17) * flail, hl[1] + 30 * math.cos(t * 15) * flail)
        hr = (hr[0] + 30 * math.sin(t * 19 + 1) * flail, hr[1] + 30 * math.cos(t * 13 + 2) * flail)
    def draw_arm(s, h):
        sx, sy = s * 110 * (1 + 0.16 * fluff), -30
        mx, my = (sx + h[0]) / 2 + s * 25, (sy + h[1]) / 2 + 15
        two_seg(c, (sx, sy), (mx, my), h, 42, 38, jacket, jacket)
        fs(c, oval(h[0], h[1], 24, 22), "#ff8c42", 4)
        if mic and s > 0:
            x, y = hr
            c.drawPath(poly([(x, y), (x - 10, y - 60)], False), stroke("#1d1d22", 10))
            c.drawCircle(x - 12, y - 68, 16, fill("#5a5a66"))
            c.drawCircle(x - 12, y - 68, 16, stroke(OUT, 3))

    def near_face(h):
        return abs(h[0]) < 125 and h[1] < -70

    for s, h in ((-1, hl), (1, hr)):
        if not near_face(h):
            draw_arm(s, h)
    # head
    c.save()
    c.translate(0, -160)
    fs(c, head_path(108, 98, 0.2, P["puff"]), skin, 5)
    face(c, P, skin, eye_dx=40, eye_y=-4, erx=25, ery=29, iris="#5b3a24", brow="#4a3020", brow_w=10, mouth_y=52, mouth_w=34)
    if P["sweat"] > 0.02:
        sweat_drops(c, 108, 98, P["sweat"], t, 7)
    # beanie
    hat = skia.Path()
    hat.moveTo(-104, -40)
    hat.cubicTo(-110, -120, -50, -150, 0, -150)
    hat.cubicTo(50, -150, 110, -120, 104, -40)
    hat.close()
    fs(c, hat, "#2a9d6f", 5)
    fs(c, rrect(-112, -58, 224, 34, 16), "#5ccf9a", 5)
    fs(c, oval(0, -158, 24, 22), "#ff8c42", 4)
    c.restore()
    for s, h in ((-1, hl), (1, hr)):
        if near_face(h):
            draw_arm(s, h)
    c.restore()


# ---------------------------------------------------------------------- Principal Brodie
BRODIE_POSES = {   # (hand L, hand R) relative to chest centre (0,0); shoulders at (+-150, -60)
    "stand": ((-185, 170), (185, 170)),
    "hips": ((-120, 120), (120, 120)),
    "crossed": ((60, 40), (-60, 40)),
    "glasses": ((-185, 170), (40, -175)),
    "hat": ((-185, 170), (150, -10)),
    "mic": ((-185, 170), (60, -120)),
    "fist": ((-185, 170), (210, -40)),
    "thumbs": ((-185, 170), (170, 0)),
    "kneel_reach": ((-185, 170), (230, 90)),
    "flex": ((-230, -120), (230, -120)),
    "shake": ((-185, 170), (120, 110)),
    "wave": ((-185, 170), (210, -170)),
    "point": ((-185, 170), (250, -60)),
    "chin": ((-185, 170), (30, -120)),
    "heart": ((-185, 170), (45, -15)),
    "hug": ((70, 25), (-20, 10)),
    "press": ((-170, -230), (170, -230)),
    "open": ((-230, 40), (230, 40)),
    "fist_r": ((-185, 170), (235, -40)),
    "jog": ((-150, 40), (150, 60)),
    "cup": ((-185, 170), (55, -130)),
}


def brodie(c, P, t=0.0, pose="stand", blend=None, glasses=1.0, hold_glasses=False, shake=0.0, prop=None, kneel=0.0):
    skin = SKIN_B
    polo, polo_d = "#23395d", "#1a2a45"
    c.save()
    c.translate(shake * 4 * math.sin(t * 40), 0)
    # legs / shorts
    c.save()
    c.translate(0, 60 * kneel)
    for s in (-1, 1):
        fs(c, rrect(s * 60 - 45, 210, 90, 120, 20), "#c8b48a", 5)
        fs(c, rrect(s * 60 - 32, 320 - 50 * kneel, 64, 110 - 40 * kneel, 18), skin, 5)
        fs(c, rrect(s * 60 - 44, 420 - 90 * kneel, 88, 36, 14), "#f2f2f2", 5)
    c.restore()
    # torso (V shape)
    tor = vtorso(198, 112, -100, 232, 46)
    fs(c, tor, polo, 6)
    pecs(c, 30, 120, polo_d, 0.7)
    fs(c, poly([(-40, -100), (0, -40), (40, -100)]), polo_d, 4)
    text(c, "PRINCIPAL", 95, -10, "inter_black", 18, "#c9d6ea")
    # whistle
    c.drawPath(smooth_path([(-45, -95), (-20, 20), (20, 20), (45, -95)], False), stroke("#e63946", 4))
    fs(c, rrect(-14, 18, 28, 18, 6), "#c0c0c8", 3)
    # arms
    hl, hr = BRODIE_POSES[pose]
    if blend:
        p2, u = blend
        hl2, hr2 = BRODIE_POSES[p2]
        hl = (lerp(hl[0], hl2[0], u), lerp(hl[1], hl2[1], u))
        hr = (lerp(hr[0], hr2[0], u), lerp(hr[1], hr2[1], u))
    for s, h in ((-1, hl), (1, hr)):
        sx, sy = s * 165, -55
        mx, my = (sx + h[0]) / 2 + s * 40, (sy + h[1]) / 2 + 20
        limb(c, (sx, sy), (mx, my), 70, polo if abs(my - sy) < 30 else skin)
        limb(c, (sx, sy), (sx + (mx - sx) * 0.35, sy + (my - sy) * 0.35), 76, polo)
        limb(c, (mx, my), h, 58, skin)
        c.drawCircle(h[0], h[1], 32, fill(skin))
        c.drawCircle(h[0], h[1], 32, stroke(OUT, 5))
    if hold_glasses:
        x, y = hr
        fs(c, rrect(x - 50, y - 50, 100, 26, 10), "#111111", 3)
    if _has(prop, "hat"):
        x, y = hr
        fs(c, rrect(x - 60, y - 120, 120, 110, 10), "#1d1d22", 5)
        fs(c, oval(x, y - 10, 90, 18), "#1d1d22", 5)
        c.drawRect(skia.Rect.MakeLTRB(x - 60, y - 40, x + 60, y - 24), fill("#e63946"))
    if _has(prop, "barbell"):
        y = (hl[1] + hr[1]) / 2
        c.drawPath(poly([(hl[0] - 120, y), (hr[0] + 120, y)], False), stroke(OUT, 18))
        c.drawPath(poly([(hl[0] - 120, y), (hr[0] + 120, y)], False), stroke("#b8bec8", 10))
        for s, h in ((-1, hl), (1, hr)):
            fs(c, rrect(h[0] + s * 70 - 22, y - 70, 44, 140, 12), "#2b2d42", 5)
            fs(c, rrect(h[0] + s * 112 - 16, y - 50, 32, 100, 10), "#e63946", 5)
        for s, h in ((-1, hl), (1, hr)):
            c.drawCircle(h[0], h[1], 32, fill(skin))
            c.drawCircle(h[0], h[1], 32, stroke(OUT, 5))
    if _has(prop, "shake"):
        x, y = hr
        fs(c, rrect(x - 26, y - 90, 52, 90, 12), "#f4f1de", 4)
        text(c, "PROTEIN", x, y - 40, "inter_black", 11, "#23395d")
    # head (small on a big body)
    c.save()
    c.translate(0, -175)
    fs(c, rrect(-42, 40, 84, 60, 20), skin, 5)
    fs(c, head_path(78, 86, 0.05, 0.0, 0.9, 0.12), skin, 5)
    c.drawPath(poly([(-50, 70), (0, 92), (50, 70)], False), stroke(hexs(mix(skin, "#000000", 0.2)), 3, 0.5))
    if glasses < 1.0:
        Pw = dict(P)
        face(c, Pw, skin, eye_dx=30, eye_y=-6, erx=19, ery=22, iris="#6b4423", brow="#c9a040", brow_w=8, mouth_y=48, mouth_w=26)
        if glasses < 0.5:
            # warm, caring sparkle
            a = (1 - glasses * 2) * clamp((Pw["lid"] - 0.25) / 0.4)
            for s in (-1, 1):
                ex = s * 30 + Pw["px"] * 9
                c.drawCircle(ex - 6, -15, 5.5, fill("#ffffff", 0.95 * a))
                c.drawCircle(ex + 6, -1, 3, fill("#ffffff", 0.85 * a))
                p = skia.Path()
                r = 5 + 1.5 * math.sin(t * 5 + s)
                cx_, cy_ = ex + 4, -12
                p.moveTo(cx_, cy_ - r); p.quadTo(cx_, cy_, cx_ + r, cy_); p.quadTo(cx_, cy_, cx_, cy_ + r)
                p.quadTo(cx_, cy_, cx_ - r, cy_); p.quadTo(cx_, cy_, cx_, cy_ - r)
                c.drawPath(p, fill("#fffbe0", a))
                c.drawPath(oval(s * 44, 18, 14, 7), fill("#ff8a8a", 0.4 * a, blur=3))
    else:
        draw_mouth(c, 0, 48, 26, P)
        for s in (-1, 1):
            draw_brow(c, s * 30, -36 - P["brow_y"] * 10, 19, P["brow_ang"], s, "#c9a040", 8)
    if glasses > 0:
        c.save()
        c.translate(0, -60 * (1 - glasses))
        c.saveLayerAlpha(None, int(255 * clamp(glasses * 1.5)))
        fs(c, smooth_path([(-74, -26), (-8, -26), (-6, 6), (-30, 16), (-66, 8)]), "#111111", 4)
        fs(c, smooth_path([(74, -26), (8, -26), (6, 6), (30, 16), (66, 8)]), "#111111", 4)
        c.drawRect(skia.Rect.MakeLTRB(-10, -24, 10, -14), fill("#111111"))
        c.drawPath(poly([(-60, -18), (-30, -2)], False), stroke("#ffffff", 4, 0.35))
        c.drawPath(poly([(30, -18), (60, -2)], False), stroke("#ffffff", 4, 0.35))
        c.restore()
        c.restore()
    # blond flat-top
    fs(c, rrect(-74, -112, 148, 64, 10), "#f2d16b", 5)
    for k in range(7):
        c.drawPath(poly([(-60 + k * 20, -108), (-60 + k * 20, -60)], False), stroke("#d9b34d", 3, 0.6))
    c.restore()
    c.restore()


# ---------------------------------------------------------------------- Emotional Chad
CHAD_POSES = {   # shoulders at (+-125, -50)
    "stand": ((-150, 160), (150, 160)),
    "mic": ((-150, 160), (55, -110)),
    "puppet": ((-150, 160), (150, -120)),
    "heart": ((-30, -40), (30, -40)),
    "fist": ((-150, 160), (190, -30)),
    "open": ((-200, 20), (200, 20)),
    "hat_draw": ((-60, -10), (170, -60)),
    "flex": ((-200, -110), (200, -110)),
    "wipe": ((-150, 160), (40, -150)),
    "point": ((-150, 160), (220, -50)),
    "wave": ((-150, 160), (190, -170)),
    "fist_l": ((-235, -40), (150, 160)),
    "chin": ((-60, 40), (30, -95)),
    "clap": ((-28, -20), (28, -20)),
    "spot": ((-95, -150), (95, -150)),
    "guns": ((-200, -20), (200, -20)),
    "plead": ((-35, -10), (35, -10)),
    "laugh": ((-30, 60), (40, -150)),
}


def chad(c, P, t=0.0, pose="stand", blend=None, prop=None, shake=0.0, tears=0.0, puppet_talk=0.0):
    skin = SKIN_C
    c.save()
    c.translate(shake * 4 * math.sin(t * 40), 0)
    for s in (-1, 1):
        fs(c, rrect(s * 50 - 38, 200, 76, 230, 20), "#2b2d42", 5)
        fs(c, rrect(s * 50 - 44, 420, 88, 36, 14), "#ff5a5f", 5)
    for s in (-1, 1):   # bare shoulders under the tank straps
        fs(c, oval(s * 128, -40, 52, 56), skin, 5)
    tor = vtorso(140, 100, -88, 215, 70)
    fs(c, tor, "#9aa3ad", 6)
    fs(c, smooth_path([(-62, -84), (0, -40), (62, -84), (0, -62)]), skin, 4)
    pecs(c, 10, 100, "#6f7780", 0.7)
    text(c, "FEEL IT", 0, 60, "bangers", 40, "#ff5a5f", outline=OUT, ow=5)
    hl, hr = CHAD_POSES[pose]
    if blend:
        p2, u = blend
        hl2, hr2 = CHAD_POSES[p2]
        hl = (lerp(hl[0], hl2[0], u), lerp(hl[1], hl2[1], u))
        hr = (lerp(hr[0], hr2[0], u), lerp(hr[1], hr2[1], u))
    for s, h in ((-1, hl), (1, hr)):
        sx, sy = s * 135, -45
        mx, my = (sx + h[0]) / 2 + s * 35, (sy + h[1]) / 2 + 20
        limb(c, (sx, sy), (mx, my), 58, skin)
        limb(c, (mx, my), h, 50, skin)
        c.drawCircle(h[0], h[1], 28, fill(skin))
        c.drawCircle(h[0], h[1], 28, stroke(OUT, 5))
    if _has(prop, "mic"):
        x, y = hr
        c.drawPath(poly([(x, y), (x - 8, y - 55)], False), stroke("#1d1d22", 10))
        c.drawCircle(x - 10, y - 64, 16, fill("#5a5a66"))
        c.drawCircle(x - 10, y - 64, 16, stroke(OUT, 3))
    if _has(prop, "puppet"):
        x, y = hr
        c.save()
        c.translate(x, y)
        c.scale(1.35, 1.35)
        c.translate(-x, -y)
        # a dumbbell with googly eyes and a little mouth
        c.drawPath(poly([(x - 70, y - 40), (x + 70, y - 40)], False), stroke(OUT, 22))
        c.drawPath(poly([(x - 70, y - 40), (x + 70, y - 40)], False), stroke("#9aa0aa", 14))
        for s in (-1, 1):
            fs(c, rrect(x + s * 80 - 22, y - 85, 44, 90, 12), "#2b2d42", 4)
        for s in (-1, 1):
            c.drawCircle(x + s * 14, y - 52, 11, fill("#ffffff"))
            c.drawCircle(x + s * 14, y - 52, 11, stroke(OUT, 2.5))
            c.drawCircle(x + s * 14 + 3 * math.sin(t * 9), y - 49, 5, fill(OUT))
        mo = 3 + 9 * puppet_talk
        c.drawPath(oval(x, y - 28, 10, mo), fill("#5a1626"))
        c.restore()
    if _has(prop, "hat"):
        x, y = hl
        fs(c, rrect(x - 60, y - 110, 120, 100, 10), "#1d1d22", 5)
        fs(c, oval(x, y - 10, 90, 18), "#1d1d22", 5)
        c.drawRect(skia.Rect.MakeLTRB(x - 60, y - 40, x + 60, y - 24), fill("#e63946"))
    if _has(prop, "slip"):
        x, y = hr
        c.save()
        c.translate(x, y - 60)
        c.rotate(-8)
        fs(c, rrect(-70, -28, 140, 56, 4), "#ffffff", 3)
        text(c, "CARTER", 0, 12, "bangers", 34, "#e63946")
        c.restore()
    # head
    c.save()
    c.translate(0, -160)
    fs(c, rrect(-36, 40, 72, 55, 18), skin, 5)
    hair = smooth_path([(-82, -10), (-86, -70), (-40, -112), (20, -116), (80, -84), (86, -10), (60, -60), (0, -78), (-60, -60)])
    fs(c, head_path(80, 90, 0.04), skin, 5)
    fs(c, hair, "#3b2318", 4)
    Pc = dict(P)
    Pc["tears"] = max(Pc["tears"], tears)
    face(c, Pc, skin, eye_dx=32, eye_y=0, erx=20, ery=24, iris="#3a2414", brow="#3b2318", brow_w=8, mouth_y=52, mouth_w=28)
    for s in (-1, 1):   # long lashes
        c.drawPath(poly([(s * 32 + s * 18, -22), (s * 32 + s * 28, -32)], False), stroke(OUT, 3))
    fs(c, rrect(-86, -62, 172, 22, 8), "#e63946", 4)
    c.restore()
    c.restore()


# ---------------------------------------------------------------------- gym bros (35, very ripped)
def gym_bro(c, t=0.0, variant=0, carry=0.0, walk=0.0, grin=0.6, mo=0.15, px=0.0, py=0.0):
    skin = [SKIN_B, SKIN_D][variant % 2]
    tank = ["#d62828", "#1d1d22"][variant % 2]
    c.save()
    bob = 6 * abs(math.sin(t * 6)) * walk
    c.translate(0, -bob)
    for s in (-1, 1):
        st = 16 * math.sin(t * 6 + (0 if s < 0 else math.pi)) * walk
        fs(c, rrect(s * 55 - 42 + st, 200, 84, 220, 20), "#3a3f5c", 5)
        fs(c, rrect(s * 55 - 48 + st, 410, 96, 34, 14), "#111111", 5)
    for s in (-1, 1):
        fs(c, oval(s * 150, -40, 62, 62), skin, 5)
    tor = vtorso(165, 105, -92, 215, 74)
    fs(c, tor, tank, 6)
    fs(c, smooth_path([(-66, -88), (0, -40), (66, -88), (0, -66)]), skin, 4)
    pecs(c, 10, 110, hexs(mix(tank, "#000000", 0.35)), 0.8)
    for s in (-1, 1):
        hx = s * lerp(190, 105, carry)
        hy = lerp(150, -270, carry)
        ex, ey = s * lerp(210, 215, carry), lerp(60, -150, carry)
        limb(c, (s * 160, -50), (ex, ey), 66, skin)
        limb(c, (ex, ey), (hx, hy), 56, skin)
        c.drawCircle(hx, hy, 30, fill(skin))
        c.drawCircle(hx, hy, 30, stroke(OUT, 5))
    c.save()
    c.translate(0, -165)
    fs(c, rrect(-44, 40, 88, 60, 20), skin, 5)
    fs(c, head_path(76, 84, 0.05, 0, 0.9, 0.1), skin, 5)
    c.drawPath(smooth_path([(-72, 10), (-60, 70), (0, 95), (60, 70), (72, 10), (40, 60), (0, 72), (-40, 60)]), fill("#3b2318", 0.85))
    P = P_(t=t, lid=0.9 * blink(t, 60 + variant, 3.0), smile=grin, teeth=True, mouth_open=mo, px=px, py=py)
    face(c, P, skin, eye_dx=28, eye_y=-8, erx=16, ery=18, iris="#3a2a20", brow="#2a1a10", brow_w=9, mouth_y=44, mouth_w=24)
    fs(c, rrect(-80, -66, 160, 18, 8), "#ffffff", 4)
    c.restore()
    c.restore()


# ---------------------------------------------------------------------- crowd kids
KID_LOOKS = [(SKIN_A, "#3b2318", "#e63946"), (SKIN_C, "#111111", "#3a86ff"), (SKIN_B, "#f2d16b", "#2a9d6f"),
             (SKIN_D, "#111111", "#ffb703"), (SKIN_A, "#b5651d", "#8338ec"), (SKIN_C, "#3b2318", "#fb5607"),
             (SKIN_B, "#111111", "#06d6a0"), (SKIN_D, "#3b2318", "#ef476f")]


def kid(c, look, P, t=0.0, hair_style=0, cap=None, glasses=False, scale=1.0, lean=0.0):
    skin, hairc, shirt = look
    c.save()
    c.scale(scale, scale)
    c.rotate(lean)
    fs(c, smooth_path([(-90, 60), (-100, 160), (100, 160), (90, 60), (0, 45)]), shirt, 5)
    fs(c, head_path(78, 80, 0.06), skin, 5)
    if hair_style == 0:
        fs(c, smooth_path([(-80, -10), (-84, -60), (-30, -88), (30, -88), (84, -60), (80, -10), (50, -50), (-50, -50)]), hairc, 4)
    elif hair_style == 1:
        for k in range(9):
            a = math.pi * (1.05 + 0.9 * k / 8)
            c.drawCircle(math.cos(a) * 70, math.sin(a) * 70 - 10, 22, fill(hairc))
    else:
        fs(c, smooth_path([(-82, 20), (-86, -60), (-30, -90), (40, -88), (86, -50), (82, 20), (70, -30), (0, -55), (-70, -30)]), hairc, 4)
    face(c, P, skin, eye_dx=28, eye_y=0, erx=16, ery=19, mouth_y=42, mouth_w=22)
    if glasses:
        for s in (-1, 1):
            c.drawPath(oval(s * 28, 0, 24, 22), stroke("#222", 4))
    if cap:
        fs(c, smooth_path([(-80, -30), (-78, -78), (0, -96), (78, -78), (80, -30)]), cap, 4)
        fs(c, rrect(-10 if True else 0, -42, 120, 18, 8), cap, 4)
    c.restore()
