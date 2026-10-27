"""Rooftop shots: camera moves, both sisters acting, props, sky overlays."""
import math

import skia

import acting
import rig
import scene_roof as sr
from anchors import resolve, L, Wd
from gfx import clamp, draw_text, ease_io, fill, font, hexc, smooth_path, stroke

MOON_SMALL = (930.0, 255.0, 75.0)
SKY_RECT = (70.0, 170.0, 1010.0, 860.0)

try:
    import sky_chalk
except Exception:  # module is built in parallel; fall back to nothing
    sky_chalk = None


def cam_at(keys, t):
    if t <= keys[0][0]:
        return sr.Cam(*keys[0][1])
    for (t0, c0), (t1, c1) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            u = ease_io((t - t0) / max(1e-3, t1 - t0))
            return sr.lerp_cam(sr.Cam(*c0), sr.Cam(*c1), u)
    return sr.Cam(*keys[-1][1])


# Tess's spin (figure-skater demo)
def spin_scale(t):
    t_out = resolve(Wd("L22", "Arms"))
    t_pull = resolve(Wd("L22", "pull"))
    t_stop = resolve(L("L24", "start", -0.2))

    def rev(tt):
        r = 0.0
        if tt > t_out:
            r += 0.45 * (min(tt, t_pull) - t_out)
        if tt > t_pull:
            r += 2.3 * (min(tt, t_stop) - t_pull)
        return r

    if t <= t_out:
        return 1.0, 0.0
    r = rev(t)
    if t > t_stop:
        r_stop = rev(t_stop)
        target = math.ceil(r_stop)
        u = clamp((t - t_stop) / 0.35)
        r = r_stop + (target - r_stop) * (1 - (1 - u) ** 2)
    speed = 2.3 if t_pull < t < t_stop else (0.45 if t_out < t < t_pull else 0.0)
    return math.cos(2 * math.pi * r), speed


def draw_title(c, t):
    a = 1.0 - clamp((t - 2.7) / 0.8)
    if a <= 0.01:
        return
    f1 = font(78, "black")
    f2 = font(54, "semibold", italic=True)
    glow = skia.Paint(AntiAlias=True, Color=hexc("#9ec2ff", 0.35 * a))
    glow.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14))
    s1, s2 = "WHAT IF EARTH SHRANK", "…but kept all of its mass?"
    w1 = f1.measureText(s1)
    c.drawString(s1, 540 - w1 / 2, 214, f1, glow)
    draw_text(c, s1, 540, 214, f1, hexc("#ffffff", a), outline=hexc("#0a1030", 0.6 * a), outline_w=6)
    draw_text(c, s2, 540, 290, f2, hexc("#ffd36b", a), outline=hexc("#0a1030", 0.6 * a), outline_w=5)


def draw_roof_mug(c, x, y, color, steam, t, dots):
    rig.draw_mug(c, x, y, 0.62, color, 0.0, steam, t, dots=dots)


def render(c, t, shot):
    """t: absolute time. shot: resolved shot dict with 'start', 'end', 'params'."""
    P = shot.get("params", {})
    lt = t - shot["start"]
    cam = cam_at(P["cam"], lt)
    act = acting.actors()
    sky_key = P.get("sky")
    moon_screen = MOON_SMALL if sky_key else None
    sr.draw_sky(c, cam, t, moon_screen=moon_screen)
    if sky_key and sky_chalk is not None and sky_key in getattr(sky_chalk, "SKY", {}):
        cues = {k: resolve(v) - shot["start"] for k, v in P.get("sky_cues", {}).items()}
        sky_chalk.SKY[sky_key](c, lt, shot["end"] - shot["start"], cues, P, SKY_RECT)
    sr.draw_town(c, cam, t)
    # window
    wo = P.get("window_open", 1.0)
    if "window_open_t" in P:
        a, b = P["window_open_t"]
        wo = clamp((lt - a) / (b - a))
    sr.draw_house(c, cam, t, window_glow=1.0, window_open=wo)

    c.save()
    cam.apply(c, 1.0)
    pip, tess = act["pip"], act["tess"]
    pplace, _ = pip.place_at(t)
    tplace, tstand = tess.place_at(t)
    at_window = P.get("tess_at") == "window"
    if at_window:
        tplace = (196.0, 1452.0, 0.66)
    # props: mugs set down on the roof
    if t > resolve(L("L09", "end", 0.4)):
        steam = max(0.12, 1.0 - (t - 60.0) / 180.0)
        draw_roof_mug(c, *acting.MUG_ROOF["pip"], "#d9534f", steam, t, True)
    if t > resolve(L("L07", "start", -0.3)):
        draw_roof_mug(c, *acting.MUG_ROOF["tess"], "#2f9e93", max(0.1, 1.0 - (t - 20.0) / 160.0), t + 0.4, False)

    tf, tp = tess.state(t, tplace, pplace)
    pf, pp = pip.state(t, pplace, tplace)

    # Tess
    if at_window:
        # only her upper body shows through the open window
        wx0, wy0, wx1, wy1 = 90, 1130, 280, sr.roof_y(330) + 170
        reveal = clamp((lt - 1.25) / 0.6)
        if reveal > 0:
            c.save()
            c.clipRect(skia.Rect.MakeLTRB(wx0, wy0, wx1, wy1), skia.ClipOp.kIntersect, True)
            dy = (1 - reveal) * 150
            rig.draw_character(c, rig.TESS, tf, tp, t, tplace[0], tplace[1] + dy, tplace[2],
                               rim_moon=0.35, rim_warm=1.0, mug_color="#2f9e93")
            c.restore()
            c.drawRect(skia.Rect.MakeLTRB(wx0 - 16, wy1, wx1 + 16, wy1 + 14), fill(hexc("#e8dcc0")))
    else:
        sx, spd = (1.0, 0.0)
        if P.get("tess_stand"):
            sx, spd = spin_scale(t)
        c.save()
        if abs(sx - 1.0) > 1e-3:
            c.translate(tplace[0] + 20 * tplace[2], 0)
            c.scale(sx if abs(sx) > 0.06 else (0.06 if sx >= 0 else -0.06), 1.0)
            c.translate(-(tplace[0] + 20 * tplace[2]), 0)
        rig.draw_character(c, rig.TESS, tf, tp, t, tplace[0], tplace[1], tplace[2], mug_color="#2f9e93")
        c.restore()
        if spd > 1.0:
            # motion arcs around the spinning sister
            cx, cy = tplace[0] + 15 * tplace[2], tplace[1] - 170 * tplace[2]
            for k in range(3):
                ph = t * 9 + k * 2.1
                r = (110 + 18 * k) * tplace[2]
                a0 = math.degrees(ph % (2 * math.pi))
                p = skia.Path()
                p.addArc(skia.Rect.MakeLTRB(cx - r, cy - r * 0.35 - 40 * k, cx + r, cy + r * 0.35 - 40 * k), a0, 70)
                c.drawPath(p, stroke(hexc("#e6f0ff", 0.55), 5))
    # "Same mass. Less space." -- a glowing ball between Tess's hands that shrinks but stays bright
    if shot["id"] == "S08":
        t_less = resolve(Wd("L07", "Less", "start", -0.15))
        t_end = resolve(Wd("L07", "Why", "start", -0.25))
        if t < t_end + 0.3:
            k = clamp((t - t_less) / 0.45)
            r = (34 - 18 * k * k * (3 - 2 * k)) * tplace[2]
            fade = 1.0 - clamp((t - t_end) / 0.3)
            fade *= clamp((t - shot["start"]) / 0.25)
            ox = tplace[0] + 80 * tplace[2]
            oy = tplace[1] - 152 * tplace[2]
            g = skia.Paint(AntiAlias=True)
            g.setShader(skia.GradientShader.MakeRadial(skia.Point(ox, oy), r * 3.2,
                        [hexc("#bfe3ff", 0.55 * fade), hexc("#7fb6ff", 0.0)], [0.0, 1.0]))
            c.drawCircle(ox, oy, r * 3.2, g)
            c.drawCircle(ox, oy, r, fill(hexc("#eaf6ff", 0.95 * fade)))
            c.drawCircle(ox, oy, r * (0.6 + 0.4 * k), stroke(hexc("#ffffff", 0.6 * fade), 2.0))
    # Pip
    rig.draw_character(c, rig.PIP, pf, pp, t, pplace[0], pplace[1], pplace[2], mug_color="#d9534f")
    # Tess's hand on Pip's shoulder when her arm is around her
    if tp.get("far_front") and not at_window:
        sh_y = -rig.TESS["torso_h"] + 12
        S = (rig.TESS["sh_half"] * 0.78, sh_y)
        E, Wp = rig.ik2(S[0], S[1], *tp["far_hand_pos"], rig.TESS["up_arm"], rig.TESS["fore_arm"], -1.0)
        ang = math.atan2(Wp[0] - E[0], Wp[1] - E[1])
        c.save()
        c.translate(tplace[0], tplace[1])
        c.scale(tplace[2], tplace[2])
        rig.draw_hand(c, rig.TESS, Wp[0], Wp[1], ang, "mitten", rig.TESS["hand_r"], mirror=-1)
        c.restore()
    c.restore()
    if P.get("title"):
        draw_title(c, lt)
