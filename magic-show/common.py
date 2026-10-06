"""Helpers shared by both parts: act utilities and the stage renderer."""
import math
import random

import cairo

import engine as E
from engine import tw, ease, clamp, lerp

RABBIT_SPOTS = [(560, 652), (770, 656), (330, 642), (880, 648), (470, 664), (1080, 642),
                (215, 656), (640, 668), (990, 664), (115, 642), (1185, 660), (400, 630),
                (830, 632), (705, 642), (285, 666)]


def sfx(S, t, name, g=1.0):
    S["sfx"].append((t, name, g))


def music(S, t, mood, vol=1.0):
    S["music"].append((t, mood, vol))


def active(lt, b):
    return lt < b.d - 1e-6


def hand(c, side, target, lt, t0, t1, fn=ease):
    key = "hl" if side < 0 else "hr"
    cur = c[key]
    if isinstance(target, str):
        target = E.pose(c["kind"], side, target)
    if t1 <= t0:
        u = 1.0 if lt >= t0 else 0.0
    else:
        u = fn(clamp((lt - t0) / (t1 - t0)))
    c[key] = (lerp(cur[0], target[0], u), lerp(cur[1], target[1], u))


def walk(c, x, lt, t0, t1, speed=1.0):
    c["x"] = tw(lt, t0, t1, c["x"], x)
    if t0 < lt < t1:
        c["walking"] = speed


def set_(c, lt, t0, **kw):
    if lt >= t0:
        c.update(kw)


def base_state():
    return dict(sfx=[], music=[], subtitle=None, subs=True,
                cam=[640.0, 360.0, 1.0], shake=0.0, fade=0.0, card=0.0, endcard=0.0,
                dim=0.0, spot_x=640.0, spot_y=470.0, spot_r=230.0,
                rabbits=[], missiles=[], bursts=[], cloud=None, scorch=0.0,
                turtle="hidden", turtle_xy=(612, 505), hat_wobble=0.0, curtain=1.0,
                rabbit_giggle=0.0, rabbit_look=0.0, mirror=None, scene="stage",
                swirl=0.0, cones=1.0)


def apply_camera(ctx, S, t):
    cx, cy, z = S["cam"]
    z = max(z, 1.0)
    cx = clamp(cx, E.W / 2 / z, E.W - E.W / 2 / z)
    cy = clamp(cy, E.H / 2 / z, E.H - E.H / 2 / z)
    sh = S["shake"]
    ox = math.sin(t * 71) * sh * 10
    oy = math.cos(t * 59) * sh * 8
    ctx.translate(E.W / 2 + ox, E.H / 2 + oy)
    ctx.scale(z, z)
    ctx.translate(-cx, -cy)


def rabbit_state(r, t):
    """Return (x, y, visible, emerging) for a rabbit popped from the hat."""
    dt = t - r["t0"]
    if dt < 0:
        return None
    rise = 0.22
    fly = 0.75
    if dt < rise:
        u = dt / rise
        return E.HAT_X, E.HAT_TOP + 46 * (1 - E.ease_out(u)), True
    if dt < rise + fly:
        u = (dt - rise) / fly
        x = lerp(E.HAT_X, r["x"], u)
        y = lerp(E.HAT_TOP, r["y"], u) - math.sin(u * math.pi) * 150
        return x, y, False
    return r["x"], r["y"], False


def draw_rabbits(ctx, S, t, emerging_only=None):
    for i, r in enumerate(S["rabbits"]):
        st = rabbit_state(r, t)
        if not st:
            continue
        x, y, em = st
        if emerging_only is not None and em != emerging_only:
            continue
        settled = t - r["t0"] > 1.0
        face = 1 if r["x"] >= E.HAT_X else -1
        if settled and S["rabbit_look"]:
            face = -1 if S["rabbit_look"] < 0 else 1
        if em:
            ctx.save()
            E.hat_clip_above(ctx)
            E.draw_rabbit(ctx, x, y, 0.62, face, t, i * 0.37, 0)
            ctx.restore()
        else:
            E.draw_rabbit(ctx, x, y, 0.62, face, t if settled else 0, i * 0.37,
                          S["rabbit_giggle"] if settled else 0, 0)


def draw_stage(ctx, S, t, chars):
    ctx.save()
    apply_camera(ctx, S, t)
    ctx.set_source_surface(E.stage_bg(), 0, 0)
    ctx.paint()
    E.draw_bulbs_twinkle(ctx, t)
    E.draw_ambient_cones(ctx, t, S["cones"] * (1 - S["dim"]))
    E.draw_scorch(ctx, 1192, 470, S["scorch"])
    for c in chars:
        if c["layer"] < 0:
            E.draw_char(ctx, c, t)
    for c in chars:
        if c["layer"] == 0:
            E.draw_char(ctx, c, t)
    E.draw_table(ctx, 660, t)
    draw_rabbits(ctx, S, t, emerging_only=True)
    E.draw_hat(ctx, t, S["hat_wobble"])
    if S["turtle"] == "table":
        x, y = S["turtle_xy"]
        E.draw_turtle(ctx, x, y, 0.62, 1, t, smile=S.get("turtle_smile", 0.0))
    for c in chars:
        if c["layer"] > 0:
            E.draw_char(ctx, c, t)
    draw_rabbits(ctx, S, t, emerging_only=False)
    for m in S["missiles"]:
        E.draw_missile(ctx, m, t)
    for e in S["bursts"]:
        E.draw_burst(ctx, e, t)
    if S["cloud"]:
        cl = S["cloud"]
        E.draw_cloud(ctx, cl["x"], cl["y"], cl["a"], t, cl.get("size", 1.0))
    if S["mirror"]:
        mr = S["mirror"]
        E.draw_hand_mirror_arm(ctx, mr["x"], mr["y"], t, mr.get("reflect"), mr.get("ang", 0.0))
    E.draw_spot_overlay(ctx, S["dim"], S["spot_x"], S["spot_y"], S["spot_r"])
    E.draw_main_curtains(ctx, S["curtain"])
    ctx.restore()


def draw_fade(ctx, a):
    if a > 0:
        ctx.set_source_rgba(0, 0, 0, clamp(a))
        ctx.paint()
