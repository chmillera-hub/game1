"""Diner shots: camera moves, night -> dawn light, both actors, table props, the pour and the fist bump."""
import math

import skia

import acting
import poses
import rig
import scene_diner as sd
from anchors import L, Wd, resolve
from gfx import (clamp, draw_text, ease_io, fbm1, fill, font, hexc, linear_shader, radial_shader, smooth_path,
                 smoothstep, stroke)

W, H = sd.W, sd.H

T_DAWN = (269.0, 278.6)
T_RAIN_HEAVY = 207.6
T_RAIN_EASE = (269.0, 277.0)

MUG_HALE = (470.0, 1300.0)
MUG_KAI = (642.0, 1302.0)
BELT = (352.0, 1356.0)
SKETCHBOOK = (676.0, 1344.0)
CONDIMENTS = (578.0, 1282.0)
PIE = (548.0, 1346.0)

_T = {}


def tt(name):
    """Story times resolved once."""
    if not _T:
        _T.update(
            pour0=resolve(Wd("L04", "Please", "end", 0.12)),
            pour1=resolve(L("L05", "start", -0.42)),
            pot_down=resolve(Wd("L09", "asked", "end", -0.05)),
            book_open=resolve(L("L13", "start", -0.2)),
            bump=resolve(Wd("L46", "bump", "start", 0.25)),
            tv_touch=resolve(Wd("L01", "touch")),
            tv_consent=resolve(Wd("L01", "consent")),
            # time-lapse props
            kai_mug=271.0, pie=272.6, pie_half=275.4, belt_push=(270.2, 271.0),
        )
    return _T[name]


def cam_at(keys, lt):
    if lt <= keys[0][0]:
        return sd.Cam(*keys[0][1])
    for (t0, c0), (t1, c1) in zip(keys, keys[1:]):
        if t0 <= lt <= t1:
            u = ease_io((lt - t0) / max(1e-3, t1 - t0))
            return sd.lerp_cam(sd.Cam(*c0), sd.Cam(*c1), u)
    return sd.Cam(*keys[-1][1])


def light_at(t):
    return smoothstep(T_DAWN[0], T_DAWN[1], t)


def rain_at(t):
    r = 1.0 + 0.7 * smoothstep(T_RAIN_HEAVY, T_RAIN_HEAVY + 2.0, t)
    return r * (1.0 - smoothstep(T_RAIN_EASE[0], T_RAIN_EASE[1], t))


# --------------------------------------------------------------------------- titles

def draw_title(c, lt):
    a = 1.0 - clamp((lt - 2.7) / 0.8)
    if a <= 0.01:
        return
    # soft scrim so the words sit cleanly on the window
    g = skia.Paint(AntiAlias=True)
    g.setShader(radial_shader((540, 600), 520, [hexc("#060a18", 0.62 * a), hexc("#060a18", 0.0)]))
    c.drawRect(skia.Rect.MakeLTRB(0, 300, W, 900), g)
    f1 = font(96, "black")
    f2 = font(46, "semibold", italic=True)
    for k, s in enumerate(("WHAT IF NO ONE", "COULD USE FORCE?")):
        y = 560 + k * 104
        glow = skia.Paint(AntiAlias=True, Color=hexc("#ff8fa8", 0.32 * a))
        glow.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 16))
        c.drawString(s, 540 - f1.measureText(s) / 2, y, f1, glow)
        draw_text(c, s, 540, y, f1, hexc("#ffffff", a), outline=hexc("#0a1030", 0.7 * a), outline_w=7)
    draw_text(c, "…not police. not soldiers. not anyone.", 540, 760, f2, hexc("#ffd36b", a),
              outline=hexc("#0a1030", 0.7 * a), outline_w=5)


# --------------------------------------------------------------------------- helpers

def local_to_world(place, mirror, lx, ly):
    x, y, s = place
    return (x - lx * s if mirror else x + lx * s), y + ly * s


def pot_spout(ch, pose, place, mirror):
    """World position of the carafe's pouring lip (follows rig.draw_pot's transform)."""
    _, _, Wr, ndir = rig.arm_local(ch, pose, "near")
    ox, oy = Wr[0] + math.sin(ndir) * 8, Wr[1] + math.cos(ndir) * 8
    a = pose.get("pot_tilt", 0.0)
    px, py = 62.0, -32.0
    lx = ox + px * math.cos(a) - py * math.sin(a)
    ly = oy + px * math.sin(a) + py * math.cos(a)
    return local_to_world(place, mirror, lx, ly)


def draw_pour(c, x0, y0, x1, y1, k, t):
    """Coffee stream from the spout to the mug; k fades the stream in/out."""
    if k <= 0.01:
        return
    pts = []
    for i in range(9):
        u = i / 8
        # leaves the lip sideways, then falls
        x = x0 + (x1 - x0) * (1 - (1 - u) ** 2.2)
        y = y0 + (y1 - y0) * u
        x += math.sin(t * 40 + u * 9) * 0.8
        pts.append((x, y))
    p = smooth_path(pts, False)
    c.drawPath(p, stroke(hexc("#2a160c", 0.95 * k), 7.5))
    c.drawPath(p, stroke(hexc("#7a4426", 0.9 * k), 4.0))
    c.drawPath(p, stroke(hexc("#e2b48a", 0.55 * k), 1.4))
    # splash ring on the coffee surface
    c.drawOval(skia.Rect.MakeLTRB(x1 - 12, y1 - 3, x1 + 12, y1 + 3), stroke(hexc("#c79a74", 0.6 * k), 2))


def draw_bump_fx(c, x, y, u):
    """Comic contact lines + a warm pulse when the fists meet."""
    if not (0.0 <= u <= 1.0):
        return
    a = math.sin(math.pi * u)
    g = skia.Paint(AntiAlias=True)
    g.setShader(radial_shader((x, y), 70, [hexc("#ffe6a8", 0.55 * a), hexc("#ffe6a8", 0.0)]))
    c.drawCircle(x, y, 70, g)
    for k in range(6):
        ang = -math.pi / 2 + (k - 2.5) * 0.42
        r0 = 30 + 18 * u
        r1 = r0 + 18 + 10 * (1 - u)
        c.drawLine(x + math.cos(ang) * r0, y + math.sin(ang) * r0, x + math.cos(ang) * r1, y + math.sin(ang) * r1,
                   stroke(hexc("#fff4d8", 0.9 * a), 4))


def prop_pot_down(place, pose):
    """The carafe Kai set on the table, drawn where his hand left it."""
    _, _, Wr, ndir = rig.arm_local(rig.KAI, pose, "near")
    x, y, s = place

    def f(c):
        c.save()
        c.translate(x, y)
        c.scale(-s, s)
        rig.draw_pot(c, Wr[0] + math.sin(ndir) * 8, Wr[1] + math.cos(ndir) * 8, 1.0, 0.0)
        c.restore()
    return f


def prop_closed_book(x, y):
    def f(c):
        c.save()
        c.translate(x, y)
        cover = smooth_path([(-86, -30), (86, -34), (94, 30), (-94, 34)], True, 0.1)
        c.drawPath(cover, stroke(hexc(sd.OUTLINE), 5))
        c.drawPath(cover, fill(hexc("#2f3f66")))
        c.drawLine(-80, 26, 86, 22, stroke(hexc("#f3ead8"), 4))  # page edges
        c.drawRect(skia.Rect.MakeLTRB(30, -34, 40, 30), fill(hexc("#d9534f")))  # elastic band
        c.restore()
    return f


# The sketchbook page: Kai's quick drawings appear stroke by stroke while he draws.
_SKETCH_STROKES = {
    "toolkit": [  # two stick figures, one reaching for the other's hand; a crowd of eyes
        [(-70, 18), (-70, -4)], [(-78, -14), (-70, -22), (-62, -14), (-70, -6), (-78, -14)],
        [(-70, 4), (-84, 14)], [(-70, 4), (-50, 0)], [(-70, 18), (-78, 30)], [(-70, 18), (-62, 30)],
        [(-30, 18), (-30, -4)], [(-38, -14), (-30, -22), (-22, -14), (-30, -6), (-38, -14)],
        [(-30, 4), (-48, 0)], [(-30, 4), (-16, 14)], [(-30, 18), (-38, 30)], [(-30, 18), (-22, 30)],
        [(18, -16), (26, -20), (34, -16), (26, -12), (18, -16)], [(44, -4), (52, -8), (60, -4), (52, 0), (44, -4)],
        [(16, 12), (24, 8), (32, 12), (24, 16), (16, 12)], [(48, 20), (56, 16), (64, 20), (56, 24), (48, 20)],
        [(70, -20), (78, -24), (86, -20), (78, -16), (70, -20)],
    ],
    "circle": [  # a circle of chairs
        [(34 * math.cos(a), 2 + 22 * math.sin(a)) for a in [i * math.pi / 8 for i in range(17)]],
        [(0, -26), (0, -16)], [(34, 2), (44, 2)], [(0, 26), (0, 34)], [(-34, 2), (-44, 2)],
        [(24, -16), (30, -24)], [(-24, -16), (-30, -24)], [(24, 20), (30, 28)], [(-24, 20), (-30, 28)],
    ],
}


def prop_sketch_page(x, y, strokes, prog):
    def f(c):
        c.save()
        c.translate(x, y)
        book = smooth_path([(-90, -32), (90, -36), (100, 34), (-100, 38)], True, 0.1)
        c.drawPath(book, stroke(hexc(sd.OUTLINE), 5))
        c.drawPath(book, fill(hexc("#f3ead8")))
        c.drawLine(0, -35, 0, 36, stroke(hexc("#c9bda4"), 3))
        n = len(strokes)
        done = prog * n
        pen = stroke(hexc("#2b2a33", 0.85), 2.4)
        for i, st in enumerate(strokes):
            if done <= i:
                break
            k = clamp(done - i)
            m = max(2, int(round(1 + k * (len(st) - 1))))
            c.drawPath(smooth_path(st[:m], False, 0.3), pen)
        c.restore()
    return f


def prop_pie(x, y, eaten):
    def f(c):
        c.save()
        c.translate(x, y)
        c.drawOval(skia.Rect.MakeLTRB(-54, -16, 54, 16), stroke(hexc(sd.OUTLINE), 5))
        c.drawOval(skia.Rect.MakeLTRB(-54, -16, 54, 16), fill(hexc("#f4f1ea")))
        c.drawOval(skia.Rect.MakeLTRB(-40, -10, 40, 10), stroke(hexc("#d9d3c6"), 2))
        w = 34 * (1 - 0.6 * eaten)
        sl = smooth_path([(-w, 4), (w * 0.6, -12), (w, 6)], True, 0.0)
        c.drawPath(sl, stroke(hexc(sd.OUTLINE), 4))
        c.drawPath(sl, fill(hexc("#e9b45c")))
        c.drawLine(-w * 0.8, 3, w * 0.9, 5, stroke(hexc("#b8432f"), 3))
        # two forks
        c.drawLine(22, -6, 52, -20, stroke(hexc("#c7cdd6"), 3))
        c.drawLine(-30, 10, -58, 22, stroke(hexc("#c7cdd6"), 3))
        c.restore()
    return f


# --------------------------------------------------------------------------- render

def _walk_bob(actor, t):
    """Vertical bob and leg swing while the x offset is changing (Kai walking in)."""
    v = (actor.xoff.at(t + 0.02) - actor.xoff.at(t - 0.02)) / 0.04
    k = clamp(abs(v) / 180.0)
    ph = t * 2 * math.pi * 1.9
    return k, -7.0 * k * abs(math.sin(ph)), math.sin(ph)


def _standing_legs(pose, place, stand, swing, k):
    """Show legs for a standing character; feet stay on the floor behind the table."""
    x, y, s = place
    floor_y = 1374.0
    ly = (floor_y - y) / s
    pose["standing"] = True
    pose["hide_legs"] = False
    pose["knee_bend"] = -1.0
    pose["near_foot"] = (-14.0 + 34.0 * swing * k, ly)
    pose["far_foot"] = (22.0 - 34.0 * swing * k, ly)


def render(c, t, shot):
    P = shot.get("params", {})
    lt = t - shot["start"]
    cam = cam_at(P["cam"], lt)
    # a little hand-held drift
    cam.cx += 2.2 * fbm1(t * 0.23, 3) * (cam.zoom ** 0.5) / cam.zoom * 2
    cam.cy += 1.6 * fbm1(t * 0.19, 8) * (cam.zoom ** 0.5) / cam.zoom * 2
    light = light_at(t)
    rain = rain_at(t)
    act = acting.actors()
    hale, kai = act["hale"], act["kai"]
    show_kai = P.get("kai") != "away"

    sd.draw_room(c, cam, t, light, rain, dict(touch=tt("tv_touch"), consent=tt("tv_consent")), t)
    sd.draw_lamp_light(c, cam, light)
    sd.draw_seats(c, cam, light)

    hplace, _ = hale.place_at(t)
    kplace, kstand = kai.place_at(t)
    wk, bob, swing = _walk_bob(kai, t)
    kplace = (kplace[0], kplace[1] + bob, kplace[2])
    hf, hp = hale.state(t, hplace, kplace)
    kf, kp = kai.state(t, kplace, hplace)
    if kstand > 0.02:
        _standing_legs(kp, kplace, kstand, swing, wk)

    rim_moon = 0.75 * (1 - light) + 0.15
    rim_warm = 0.35 + 0.55 * light
    c.save()
    cam.apply(c, 1.0)
    rig.draw_character(c, rig.HALE, hf, hp, t, *hplace, rim_moon=rim_moon, rim_warm=rim_warm, parts=("body",))
    if show_kai:
        rig.draw_character(c, rig.KAI, kf, kp, t, *kplace, rim_moon=rim_moon, rim_warm=rim_warm, parts=("body",),
                           mirror=True)
    c.restore()

    # ---- table props
    props = []
    props.append(sd.prop_condiments(*CONDIMENTS, light))
    bx, by = BELT
    b0, b1 = tt("belt_push")
    bx -= 150.0 * smoothstep(b0, b1, t)  # pushed aside during the long talk
    props.append(sd.prop_belt(bx, by))
    if t >= tt("pie"):
        props.append(prop_pie(*PIE, smoothstep(tt("pie_half") - 0.4, tt("pie_half"), t)))
    if t < tt("book_open"):
        props.append(prop_closed_book(*SKETCHBOOK))
    else:
        strokes, prog = _sketch_progress(t)
        props.append(prop_sketch_page(*SKETCHBOOK, strokes, prog))
    if t >= tt("kai_mug"):
        props.append(sd.prop_mug(*MUG_KAI, 0.8 * (1 - light * 0.5), t + 0.3))
    steam = 0.25 if t < tt("pour0") else max(0.15, 0.95 - (t - tt("pour0")) / 140.0)
    if t > 271.6:
        steam = 0.8  # fresh refill in the time-lapse
    props.append(sd.prop_mug(*MUG_HALE, steam, t))
    if t >= tt("pot_down"):
        props.append(prop_pot_down(acting.BASE_PLACE["kai"], poses.pose_for("kai", "set_pot")))
    sd.draw_table(c, cam, t, light, props)

    # ---- arms over the table
    c.save()
    cam.apply(c, 1.0)
    rig.draw_character(c, rig.HALE, hf, hp, t, *hplace, rim_moon=rim_moon, rim_warm=rim_warm, parts=("arms",))
    if show_kai:
        rig.draw_character(c, rig.KAI, kf, kp, t, *kplace, rim_moon=rim_moon, rim_warm=rim_warm, parts=("arms",),
                           mirror=True)
        if kp.get("pot") and tt("pour0") - 0.2 < t < tt("pour1") + 0.2:
            k = smoothstep(tt("pour0"), tt("pour0") + 0.12, t) * (1 - smoothstep(tt("pour1") - 0.25, tt("pour1"), t))
            k *= clamp((kp.get("pot_tilt", 0.0) - 0.3) / 0.2)
            sx, sy = pot_spout(rig.KAI, kp, kplace, True)
            draw_pour(c, sx, sy, MUG_HALE[0] + 2, MUG_HALE[1] - 26, k, t)
    tb = tt("bump")
    draw_bump_fx(c, 546.0, 1166.0, (t - tb + 0.02) / 0.32)
    c.restore()

    _grade(c, light)
    if P.get("title"):
        draw_title(c, lt)


def _sketch_progress(t):
    """Which drawing is on Kai's open page and how much of it is done."""
    a0, a1 = resolve(L("L13", "start", 0.4)), resolve(L("L13", "end", -0.3))
    c0, c1 = resolve(L("L23", "start", 0.3)), resolve(L("L23", "end", -0.4))
    if t < c0 - 2.0:
        return _SKETCH_STROKES["toolkit"], clamp((t - a0) / (a1 - a0))
    return _SKETCH_STROKES["circle"], clamp((t - c0) / (c1 - c0))


def _grade(c, light):
    """Screen-space finishing: dawn wash through the window, vignette."""
    if light > 0.01:
        g = skia.Paint(AntiAlias=True)
        g.setShader(radial_shader((700, 700), 1300, [hexc("#ffc98a", 0.22 * light), hexc("#ffb070", 0.08 * light),
                                                     hexc("#ffb070", 0.0)], [0.0, 0.55, 1.0]))
        g.setBlendMode(skia.BlendMode.kScreen)
        c.drawRect(skia.Rect.MakeLTRB(0, 0, W, H), g)
    v = skia.Paint(AntiAlias=True)
    va = 0.42 * (1 - 0.55 * light)
    v.setShader(radial_shader((W / 2, H * 0.47), 1180, [hexc("#000000", 0.0), hexc("#000000", 0.0),
                                                       hexc("#05030a", va)], [0.0, 0.58, 1.0]))
    c.drawRect(skia.Rect.MakeLTRB(0, 0, W, H), v)
