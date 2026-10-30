"""Shot list. Every shot is (t_start, t_end, fn(ctx, t)). Times are tied to voice lines."""
import math
import cairo
from common import (W, H, SCENES, LINES, L, at, word_t, mouth, speaking, blink, clamp, lerp, ease, ease2, ramp,
                    kf, sn, hsh, hexc, mix, mul, rgba, soft_dot, soft_stroke, capsule, ellipse, smooth_open,
                    smooth_closed, shade)
import rig
import world
from world import Cam, ZC, WALL, BLD, FIG_H

HORDE = world.Horde()


def S(sc):
    return SCENES[sc]


# ---------------------------------------------------------------- lights
def LT(**kw):
    d = dict(dir=(-0.45, -0.85), rim=hexc("ffb070"), shadow=hexc("2a2040"), amb=hexc("c8a090"), amb_k=0.10,
             line=hexc("1c1520"))
    d.update(kw)
    n = math.hypot(*d["dir"])
    d["dir"] = (d["dir"][0] / n, d["dir"][1] / n)
    return d


LF0 = LT()                                                                                  # sunset, front-lit
LB0 = LT(dir=(0.15, -1), rim=hexc("ffa060"), shadow=hexc("1a1428"), amb=hexc("7a6a8a"), amb_k=0.15)  # sunset, back-lit
LF1 = LT(dir=(-0.4, -0.9), rim=hexc("ff9a5a"), shadow=hexc("1c1630"), amb=hexc("9a86a6"), amb_k=0.14)   # dusk
LFn = LT(dir=(-0.35, -0.9), rim=hexc("ff8a50"), shadow=hexc("161228"), amb=hexc("8a7aa0"), amb_k=0.18)  # night, fires behind cam
LBn = LT(dir=(0.1, -1), rim=hexc("ff7a40"), shadow=hexc("141020"), amb=hexc("6a5e86"), amb_k=0.2)
LSOUL = LT(dir=(0.0, -1), rim=hexc("ffe0a0"), shadow=hexc("2a2040"), amb=hexc("d0b0a0"), amb_k=0.10)
LCAB = LT(dir=(-0.7, -0.7), rim=hexc("ff6a50"), shadow=hexc("1e1a26"), amb=hexc("a09aa0"), amb_k=0.12)
LSPOT = LT(dir=(0.1, -1), rim=hexc("fff4dc"), shadow=hexc("161228"), amb=hexc("9a90b0"), amb_k=0.15)
LDEF = LT(dir=(0.3, -0.95), rim=hexc("ffa060"), shadow=hexc("1a1830"), amb=hexc("8a8aa8"), amb_k=0.15)


def flick(Lb, t, amount=1.0):
    f = HORDE.flash(t) * amount
    if f <= 0:
        return Lb
    d = dict(Lb)
    d["rim"] = mix(Lb["rim"], hexc("e8f4ff"), 0.5 * f)
    d["amb"] = mix(Lb["amb"], hexc("d0e0ff"), 0.25 * f)
    return d


# ---------------------------------------------------------------- framing helpers
HEAD_Y = 670 / FIG_H * 1.75   # head centre height (m) standing
KNEEL_DROP = 238


def frame_cam(X, Z, d, depth, head_px, head_sy, sx=W / 2, cam_y=1.55, kneel=0.0):
    s = head_px / (116 * 1.08)
    f = s * FIG_H * depth / 1.75
    Yh = HEAD_Y - kneel * KNEEL_DROP / FIG_H * 1.75
    hy = head_sy + (Yh - cam_y) * f / depth
    cz = Z - d * depth
    cx = X - (sx - W / 2) * depth / (d * f)
    return Cam(x=cx, y=cam_y, z=cz, d=d, f=f, hy=hy)


def place(cam, X, Z, kneel=0.0, Y=0.0):
    x, y = cam.p(X, Y, Z)
    s = cam.scale(Z)
    return x, y - (578 - KNEEL_DROP * kneel) * s, s


def ext(ctx, t, cam, phase, east=False, extras=(), fire=True, building=False, horde=True, stars=0.0, light=None,
        sun=True, zmax=None, bflag=True, moon="auto"):
    lb = light or (LB0 if phase < 1 else LBn)
    lf = LF0 if phase < 1 else LFn
    world.draw_sky(ctx, cam, t, phase, east=east, stars=stars, sun=sun, moon=moon)
    world.draw_ground(ctx, cam, t, phase, east=east)
    if not east:
        world.draw_fortress(ctx, cam, t, phase, lb, flash=HORDE.flash(t) if fire else 0, aim=HORDE.recent(t) if fire else ())
        world.draw_smoke(ctx, cam, t, phase)
    items = list(extras)
    if horde:
        items += HORDE.items(cam, t, flick(lf, t), lb, fire=fire, zmax=zmax)
    if building and cam.d > 0:
        items.append((cam.depth(BLD[1]) + 0.5, lambda c: world.draw_building(c, cam, t, lb, phase, flag=bflag)))
    for dp, fn in sorted(items, key=lambda a: -a[0]):
        fn(ctx)


# ---------------------------------------------------------------- the conscious zombie
def ZE(t, **kw):
    o, w = mouth("Z", t)
    e = dict(milky=0.0, glow=0.12, t=t, pupil=0.45, drone=0.0, grime=0.25, life=0.3)
    e.update(kw)
    e["op"] = e.get("op", 0.0) + o * kw.pop("talk", 0.85)
    e["wd"] = e.get("wd", 0.0) + w * 0.3
    e["lid"] = max(e.get("lid", 0.0), blink(t, 7) if kw.get("blinks", True) else 0)
    e.pop("blinks", None)
    return rig.expr(**e)


def idle(t, k=1.0, seed=1):
    return dict(iyaw=sn(t, seed, 0.5) * 0.03 * k, ipitch=sn(t, seed + 1, 0.4) * 0.025 * k, iroll=sn(t, seed + 2, 0.3) * 0.02 * k)


def _foot_dx(t, per, parity, seed):
    k = math.floor(t / per)
    kk = k if k % 2 == parity else k - 1
    tgt = lambda j: 8 * math.sin(j * 1.7 + seed + parity * 2.1)
    if kk == k:
        return lerp(tgt(kk - 2), tgt(kk), ease((t - k * per) / 0.6))
    return tgt(kk)


def groggy(t, amp=1.0, per=1.7, seed=0.0):
    """Getting its bearings: weight rolling through the hips and knees, small alternating foot shuffles."""
    w = math.sin(2 * math.pi * t / 3.3 + seed) + 0.4 * math.sin(2 * math.pi * t / 1.9 + seed * 2)
    lean = amp * 0.012 * math.sin(2 * math.pi * t / 2.7 + seed)
    k = math.floor(t / per)
    u = (t - k * per) / 0.6
    lift = math.sin(clamp(u) * math.pi) * 0.24 * amp if u <= 1 else 0.0
    left = k % 2 == 0
    legs = dict(mode="stand", liftL=lift if left else 0.0, liftR=0.0 if left else lift,
                dxL=_foot_dx(t, per, 0, seed) * amp, dxR=_foot_dx(t, per, 1, seed) * amp)
    return dict(lean=lean, lean_pivot=560, iroll=amp * 0.03 * w - lean * 0.6, legs=legs, hip_shift=amp * 12 * w,
                waist_bend=-amp * 0.06 * w, kneeL=amp * 0.6 * max(0.0, -w), kneeR=amp * 0.6 * max(0.0, w))


def alive(P, t, kind="stand", amp=1.0, seed=0.0):
    """Energy with nowhere to go: sway, weight shifts, a shoulder lift now and then, restless fingers."""
    if amp <= 0:
        return P
    w = math.sin(2 * math.pi * t / 3.7 + seed) + 0.35 * math.sin(2 * math.pi * t / 1.6 + seed * 2.3)
    if kind == "stand":
        P["hip_shift"] = P.get("hip_shift", 0.0) + amp * 9 * w
        P["waist_bend"] = P.get("waist_bend", 0.0) - amp * 0.045 * w
        P["kneeL"] = P.get("kneeL", 0.0) + amp * 0.5 * max(0.0, -w)
        P["kneeR"] = P.get("kneeR", 0.0) + amp * 0.5 * max(0.0, w)
    elif kind == "kneel":
        P["waist_bend"] = P.get("waist_bend", 0.0) + amp * 0.05 * w
        P["hip_shift"] = P.get("hip_shift", 0.0) + amp * 3 * w
    else:
        P["waist_bend"] = P.get("waist_bend", 0.0) + amp * 0.03 * w
    lean = amp * 0.008 * math.sin(2 * math.pi * t / 2.9 + seed)
    P["lean"] = P.get("lean", 0.0) + lean
    if "lean_pivot" not in P:
        P["lean_pivot"] = 330 if kind == "kneel" else (560 if kind == "stand" else 200)
    P["iroll"] = P.get("iroll", 0.0) + amp * 0.03 * w + amp * 0.012 * math.sin(t * 0.9 + seed)
    P["iyaw"] = P.get("iyaw", 0.0) + amp * 0.05 * sn(t, 3 + seed, 0.35)
    P["ipitch"] = P.get("ipitch", 0.0) + amp * 0.025 * sn(t, 4 + seed, 0.5)
    P["shrug"] = P.get("shrug", 0.0) + amp * 0.1 * max(0.0, math.sin(2 * math.pi * t / 4.3 + seed)) ** 4
    for side in ("armL", "armR"):
        a = P.get(side)
        if isinstance(a, dict) and "curl" in a and a.get("curl", 0) < 0.8:
            a = dict(a)
            a["curl"] = clamp(a["curl"] + amp * 0.14 * math.sin(t * 4.4 + (0 if side == "armL" else 1.9) + seed))
            P[side] = a
    return P


def zitem(cam, t, pose, X=0.0, Z=ZC, kneel=0.0, Y=0.0, light=None):
    def fn(ctx):
        x, y, s = place(cam, X, Z, kneel, Y)
        P = dict(x=x, y=y, s=s)
        P.update(pose)
        if "legs" not in pose and kneel == 0:
            P["legs"] = dict(mode="stand")
        kind = "kneel" if kneel > 0.5 else ("stand" if P.get("legs") else "bust")
        alive(P, t, kind, pose.get("alive", 1.0))
        rig.draw_character(ctx, rig.ZOMBIE, P, light or flick(LF0, t), t)
    return (cam.depth(Z) - 0.05, fn)


def arms_hang(t, k=1.0):
    return dict(armL=dict(a1=-8 - sn(t, 4, 0.6) * 2 * k, a2=-4, curl=0.5, spread=0.1, thumb=0.5, flip=False),
                armR=dict(a1=8 + sn(t, 5, 0.6) * 2 * k, a2=4, curl=0.5, spread=0.1, thumb=0.5, flip=True))


def runners(cam, t, t0, specs, speed=3.0, seed=500):
    """Staged zombies running at the camera: specs = [(X, start_depth), ...]."""
    out = []
    for k, spec in enumerate(specs):
        X, d0 = spec[0], spec[1]
        z = dict(HORDE.L[k * 37])
        z.update(i=seed + k, style=rig.horde_style(seed + k), reach=k % 2 == 0, quad=len(spec) > 2 and spec[2])
        if z["quad"]:
            z["rate"] = 11.0
        Zk = cam.z + cam.d * (d0 - speed * (t - t0))
        if cam.depth(Zk) > 1.2:
            x, y = cam.p(X, 0, Zk)
            out.append((cam.depth(Zk), HORDE._fig(z, x, y, cam.scale(Zk), t, cam, flick(LF0, t), 1.0)))
    return out


def bump_runner(cam, t, t_b, side, seed):
    """A runner clips the hero's shoulder at t_b and glances off toward the fortress."""
    z = dict(HORDE.L[(seed * 7) % len(HORDE.L)])
    z.update(i=seed, style=rig.horde_style(seed), reach=False, quad=False)
    Zr = ZC + 3.3 * (t - t_b)
    Xr = side * (0.48 + 0.4 * ramp(t, t_b, t_b + 0.5))
    if not (1.2 < cam.depth(Zr) < 60):
        return []
    x, y = cam.p(Xr, 0, Zr)
    return [(cam.depth(Zr), HORDE._fig(z, x, y, cam.scale(Zr), t, cam, flick(LF0, t), 1.0))]


def bump_kick(t, t_b):
    """The hero's lurch after being clipped: a push that settles, smooth rather than jittery."""
    u = t - t_b
    if u < 0 or u > 1.8:
        return 0.0
    return math.exp(-u * 3.0) * math.sin(u * 6.5 + 0.5)


def add_bump(P, t, t_b, side):
    k = bump_kick(t, t_b)
    if k:
        P["hip_shift"] = P.get("hip_shift", 0.0) - side * 16 * k
        P["waist_bend"] = P.get("waist_bend", 0.0) - side * 0.09 * k
        P["iroll"] = P.get("iroll", 0.0) + side * 0.05 * k
        lg = dict(P.get("legs") or dict(mode="stand"))
        step = max(0.0, math.sin(clamp((t - t_b) / 0.6) * math.pi)) * 0.35
        lg["liftR" if side > 0 else "liftL"] = max(lg.get("liftR" if side > 0 else "liftL", 0.0), step)
        P["legs"] = lg
    return P


def staged_hit(cam, t, th, X, Z0, v=3.0, seed=600, quad=False):
    """A zombie runs toward the wall and is struck at th: burst fire, crumble, dust plume."""
    z = dict(HORDE.L[seed % len(HORDE.L)])
    z.update(i=seed, style=rig.horde_style(seed), reach=False, quad=quad, rate=11.0 if quad else HORDE.L[seed % len(HORDE.L)]["rate"])
    if t < th and th - t < 0.34:
        bolt = (cam.depth(Z0) - 0.2, HORDE._bolts(X, Z0, t - th, cam))
    else:
        bolt = None
    if t < th:
        Zk = Z0 - v * (th - t)
        x, y = cam.p(X, world.hgt(Zk), Zk)
        return [(cam.depth(Zk), HORDE._fig(z, x, y, cam.scale(Zk), t, cam, flick(LB0, t), 1.0))] + ([bolt] if bolt else [])
    return [(cam.depth(Z0) - 0.1, HORDE._dust(z, X, Z0, t - th, cam, LB0, True))]


def soul_orb(ctx, x, y, r, t, a=1.0):
    soft_dot(ctx, x, y, r * 6, hexc("ffd890"), 0.25 * a)
    soft_dot(ctx, x, y, r * 2.5, hexc("fff0c8"), 0.6 * a)
    soft_dot(ctx, x, y, r, (1, 1, 1), 0.95 * a)
    for k in range(6):
        ang = t * 2 + k * 1.047
        ln = r * (3 + math.sin(t * 5 + k) * 0.8)
        ctx.new_path(); ctx.move_to(x, y); ctx.line_to(x + math.cos(ang) * ln, y + math.sin(ang) * ln)
        rgba(ctx, hexc("fff0c8"), 0.35 * a); ctx.set_line_width(2); ctx.stroke()


def tear_state(t, t0, dur=2.6):
    """One tear: runs down then fades out as a whole."""
    if t < t0:
        return None
    u = (t - t0) / dur
    if u > 1.25:
        return None
    return clamp(u / 0.85), clamp(1 - (u - 0.85) / 0.4)


# ================================================================= SHOTS
SHOTS = []


def shot(t0, t1):
    def deco(fn):
        SHOTS.append((t0, t1, fn))
        return fn
    return deco


# ---------------------------------------------------------------- OPEN (cold open: the eyes)
o0, o1 = S("open")


@shot(o0, o1)
def open_ecu(ctx, t):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *hexc("241c38"))
    g.add_color_stop_rgb(0.6, *hexc("4a3050"))
    g.add_color_stop_rgb(1, *hexc("241c2a"))
    ctx.set_source(g); ctx.paint()
    for i in range(16):  # bokeh of distant fortress lights
        soft_dot(ctx, hsh(i, 1) * W, 200 + hsh(i, 2) * 900, 30 + hsh(i, 3) * 50, hexc("ffc070"), 0.12 + 0.08 * hsh(i, 4))
    soft_dot(ctx, W / 2, -80, 700, hexc("ffd890"), 0.14)
    lid = kf(t, [(0, 0.55), (1.1, 0.36), (2.4, 0.36), (2.55, 1.0), (2.8, 0.38)])  # heavy, one slow blink
    E = ZE(t, lid=lid, blinks=False, milky=1.0, drone=1.0, grime=1.0, life=0.0, glow=0.0, pupil=0.3, bi=-0.05, bo=-0.15,
           gx=0.05 * math.sin(t * 0.6), gy=0.15, op=0.2 + 0.04 * math.sin(t * 1.3), sm=-0.35, talk=0.0)
    P = dict(x=W / 2 - 6, y=560 + 92 * 4.3 - 10 + math.sin(t * 1.1) * 4, s=4.3, E=E, breath=0.9, breath_T=3.0,
             roll=0.09 + 0.03 * math.sin(t * 0.9), pitch=0.12 + 0.03 * math.sin(t * 0.7), yaw=-0.06)
    rig.draw_character(ctx, rig.ZOMBIE, P, LF1, t)


# ---------------------------------------------------------------- HORDE
h0, h1 = S("horde")
t_bro = word_t("h2", "brothers") - 0.3
t_run = word_t("h2", "running") - 0.4
t_def = L("h3")[0] - 0.2
t_scary = word_t("h3", "protect") - 0.3


@shot(h0, t_bro)
def horde_wide(ctx, t):
    u = (t - h0) / (t_bro - h0)
    cam = Cam(x=0, y=lerp(15, 12, u), z=lerp(38, 52, ease(u)), d=1, f=760, hy=lerp(470, 455, u))
    ext(ctx, t, cam, 0.0, building=True)
    world.draw_motes(ctx, t, 25, hexc("e0b090"), 0.12)


@shot(t_bro, t_run)
def horde_faces(ctx, t):
    u = (t - t_bro) / (t_run - t_bro)
    cam = Cam(x=lerp(-0.3, 0.3, u), y=1.5, z=ZC + 6, d=-1, f=1500, hy=500)
    run = runners(cam, t, t_bro, ((-0.6, 8.5), (0.55, 10.5), (-0.05, 13.0), (0.95, 6.5), (-1.1, 11.5), (0.2, 16), (0.3, 7.6, True)))
    ext(ctx, t, cam, 0.1, east=True, stars=0.2, extras=run)


@shot(t_run, t_def)
def horde_toward(ctx, t):
    u = (t - t_run) / (t_def - t_run)
    cam = Cam(x=2, y=lerp(1.2, 1.8, u), z=ZC - 22 + u * 6, d=1, f=820, hy=600)
    ext(ctx, t, cam, 0.1, building=True)


@shot(t_def, t_scary)
def horde_dust(ctx, t):
    u = (t - t_def) / (t_scary - t_def)
    cam = Cam(x=-1.2 + u * 1.6, y=3.0, z=WALL - 112 + u * 12, d=1, f=900, hy=640)
    hits = staged_hit(cam, t, word_t("h3", "tearing"), -1.5, WALL - 92, seed=601) + \
        staged_hit(cam, t, word_t("h3", "dust") - 0.1, -4.8, WALL - 86, seed=602) + \
        staged_hit(cam, t, word_t("h3", "dust") + 1.1, 1.2, WALL - 80, seed=603, quad=True)
    ext(ctx, t, cam, 0.15, extras=hits)
    world.draw_motes(ctx, t, 30, hexc("c8b8a8"), 0.15, drift=(30, -8))


def draw_rifle(ctx, bx, by, ang, length, light, glow=0.0):
    """Energy rifle (no real-world design); butt at (bx, by) pointing along ang. Returns key grip points."""
    k = length / 355.0
    ctx.save(); ctx.translate(bx, by); ctx.rotate(ang); ctx.scale(k, k)
    lw = 2.0 / k
    metal, dark, olive = hexc("3a3e44"), hexc("24272c"), hexc("4a5240")
    shade(ctx, lambda: smooth_closed(ctx, [(0, -20), (68, -14), (72, 12), (0, 24)], 0.4), olive, light, lw)
    shade(ctx, lambda: smooth_closed(ctx, [(118, 12), (140, 12), (132, 52), (112, 50)], 0.5), dark, light, lw)
    shade(ctx, lambda: (ctx.new_sub_path(), rig._rrect(ctx, 148, 14, 26, 30, 5)), hexc("2a6a7a"), light, lw, shadow=0.3)
    shade(ctx, lambda: (ctx.new_sub_path(), rig._rrect(ctx, 60, -20, 135, 36, 8)), metal, light, lw)
    shade(ctx, lambda: (ctx.new_sub_path(), rig._rrect(ctx, 96, -42, 70, 18, 6)), dark, light, lw)
    shade(ctx, lambda: (ctx.new_sub_path(), rig._rrect(ctx, 190, -11, 140, 21, 6)), metal, light, lw)
    shade(ctx, lambda: (ctx.new_sub_path(), rig._rrect(ctx, 326, -14, 29, 27, 7)), dark, light, lw)
    for q in range(5):
        ctx.new_path(); ctx.rectangle(205 + q * 22, -6, 12, 4); rgba(ctx, hexc("121418")); ctx.fill()
    soft_stroke(ctx, [(196, 4), (320, 4)], hexc("7ff0ff"), 0.35 + 0.5 * glow, 3)
    soft_dot(ctx, 161, 29, 16, hexc("7ff0ff"), 0.35 + 0.4 * glow)
    soft_dot(ctx, 120, -36, 6, (1, 1, 1), 0.5)
    ctx.restore()
    c, s_ = math.cos(ang), math.sin(ang)
    pt = lambda lx, ly: (bx + (lx * c - ly * s_) * k, by + (lx * s_ + ly * c) * k)
    return dict(grip=pt(126, 34), fore=pt(250, 6), muzzle=pt(355, 0), dir=(c, s_))


@shot(t_scary, h1)
def defender(ctx, t):
    """A defender on the wall: no fear, no doubt. Rifle at the ready, then shouldered and fired."""
    tt = t - t_scary
    world.draw_sky(ctx, Cam(hy=1400), t, 0.2)
    ctx.new_path(); ctx.rectangle(0, 880, W, 400)
    ctx.set_source(world.pattern("stone", 1.6)); ctx.fill_preserve()
    rgba(ctx, hexc("1a1424"), 0.45); ctx.fill()
    fires = (t_scary + 3.25, t_scary + 4.25)
    rec = 0.0
    for tf in fires:
        if tf <= t < tf + 0.45:
            rec = max(rec, math.exp(-(t - tf) * 9.0))
    sw = ease2(ramp(t, t_scary + 2.5, t_scary + 2.95))
    x, y, s = 280, 760, 2.2
    # rifle: port-arms across the body -> shouldered, aimed down-right over the parapet
    bx, by = lerp(x - 70 * s, x - 50 * s, sw), lerp(y + 120 * s, y + 30 * s, sw)
    ang = lerp(-0.25, 0.32, sw)
    bx -= math.cos(ang) * 16 * rec
    by -= math.sin(ang) * 16 * rec
    Ld = dict(flick(LDEF, t, 1.5))
    if rec > 0:
        Ld["rim"] = mix(Ld["rim"], hexc("c8f4ff"), 0.7 * rec)
    probe = draw_rifle(cairo.Context(cairo.ImageSurface(cairo.FORMAT_A8, 1, 1)), bx, by, ang, 560, Ld)
    hdir = math.atan2(probe["dir"][1], probe["dir"][0])
    to_body = lambda p, back, a: ((p[0] - math.cos(a) * back * s - x) / s, (p[1] - math.sin(a) * back * s - y) / s)
    gL = to_body(probe["grip"], 22, hdir)
    gR = to_body(probe["fore"], 22, hdir - math.pi / 2)
    smirk = 0.18 * ramp(t, fires[1] + 0.3, fires[1] + 0.9)
    E = rig.expr(bi=-1.0, bo=0.95, lid=max(0.26 + 0.08 * sw + 0.08 * rec, blink(t, 3)), low=0.55, gx=lerp(0.12, 0.45, sw),
                 gy=lerp(0.5, 0.4, sw), op=0.2 + 0.06 * rec, wd=1.0, sm=0.05 + smirk, press=0.0, sneer=1.0, t=t, pupil=0.22)
    P = dict(x=x, y=y, s=s, E=E, yaw=lerp(0.05, 0.25, sw), pitch=lerp(0.28, 0.18, sw) - 0.04 * rec, roll=-0.03 + 0.02 * math.sin(tt * 0.9),
             breath=1.0, breath_T=3.4, shrug=0.1 * sw,
             armL=dict(el=(lerp(-62, -60, sw), lerp(130, 120, sw)), wr=gL, hand_ang=hdir, curl=0.85, thumb=0.8, flip=False),
             armR=dict(el=(lerp(118, 120, sw), lerp(100, 60, sw)), wr=gR, hand_ang=hdir - math.pi / 2, curl=0.85, thumb=0.8, flip=True))
    rig.draw_character(ctx, rig.DEFENDER, P, Ld, t)
    pts = draw_rifle(ctx, bx, by, ang, 560, Ld, glow=rec)
    rig.draw_hand(ctx, rig.DEFENDER, x + gL[0] * s, y + gL[1] * s, hdir, Ld, 2.0, curl=0.88, thumb=0.85, flip=False, size=s)
    rig.draw_hand(ctx, rig.DEFENDER, x + gR[0] * s, y + gR[1] * s, hdir - math.pi / 2, Ld, 2.0, curl=0.88, thumb=0.85, flip=True, size=s)
    ctx.new_path(); ctx.rectangle(0, 1060, W, 230)
    ctx.set_source(world.pattern("stone", 1.6, 20, 0)); ctx.fill_preserve()
    rgba(ctx, hexc("1a1424"), 0.45); ctx.fill()
    ctx.new_path(); ctx.rectangle(0, 1060, W, 34); rgba(ctx, hexc("8a7a80"), 0.35); ctx.fill()
    soft_stroke(ctx, [(0, 1061), (W, 1061)], hexc("ffb080"), 0.5, 3, smooth=False)
    if rec > 0:
        m = pts["muzzle"]
        d = pts["dir"]
        for wdt, al in ((26, 0.12), (10, 0.35), (3.5, 0.95)):
            ctx.new_path(); ctx.move_to(*m); ctx.line_to(m[0] + d[0] * 1200, m[1] + d[1] * 1200)
            rgba(ctx, hexc("d4ecff"), al * rec); ctx.set_line_width(wdt); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
        soft_dot(ctx, m[0], m[1], 110, hexc("e0f6ff"), 0.85 * rec)
        soft_dot(ctx, x + 40, y - 200, 380, hexc("c8f0ff"), 0.18 * rec)


# ---------------------------------------------------------------- SOUL
s0, s1_ = S("soul")
t_fall = L("s2")[0] - 0.4
t_hit = at("s2", 0.8)


@shot(s0, t_fall)
def soul_sky(ctx, t):
    u = (t - s0) / (t_fall - s0)
    cam = Cam(hy=1700 - u * 200)
    world.draw_sky(ctx, cam, t, 0.25, sun=False)
    ox, oy = W / 2 + 40 - u * 60, lerp(-60, 980, ease2(u))
    for k in range(10):  # god rays from the parting clouds
        a = -math.pi / 2 + (k - 4.5) * 0.12
        ctx.new_path(); ctx.move_to(W / 2, -120)
        ctx.line_to(W / 2 + math.cos(a + 0.03) * 1600, -120 - math.sin(a + 0.03) * -1600)
        ctx.line_to(W / 2 + math.cos(a - 0.03) * 1600, -120 - math.sin(a - 0.03) * -1600)
        ctx.close_path()
        rgba(ctx, hexc("ffe8b0"), 0.05 * ramp(t, s0, s0 + 1.2)); ctx.fill()
    for k in range(18):
        lag = k * 0.03
        uu = clamp(u - lag)
        px, py = W / 2 + 40 - uu * 60 + math.sin(k * 3.1 + t * 3) * 10, lerp(-60, 980, ease2(uu))
        soft_dot(ctx, px, py, 10 - k * 0.4, hexc("fff0c8"), 0.5 * (1 - k / 18))
    soul_orb(ctx, ox, oy, 16, t)


@shot(t_fall, s1_)
def soul_enter(ctx, t):
    cam = frame_cam(0, ZC, -1, 9.0, 120, 560, cam_y=1.4)
    run = t < t_hit
    stop = ramp(t, t_hit, t_hit + 0.8)
    Zz = ZC - 3.0 * max(0, t_hit - t) if run else ZC
    ph = t * 8
    milky = 1.0

    def zfn(ctx2):
        x, y, s = place(cam, 0, Zz)
        bob = abs(math.sin(ph)) * 10 * (1 - stop)
        lg = dict(mode="run", phase=ph * (1 - stop))
        E = ZE(t, milky=milky, op=0.25 * (1 - stop) + 0.12 * stop, glow=0.0, bi=0.15 * stop, sm=-0.25, blinks=False,
               drone=1.0, grime=1.0, life=0.0, lid=0.32)
        P = dict(x=x, y=y + bob * s, s=s, legs=lg, E=E, roll=math.sin(ph) * 0.05 * (1 - stop) - 0.06 * stop * math.sin((t - t_hit) * 6) * (1 - ramp(t, t_hit + 0.3, t_hit + 1.2)),
                 pitch=0.1 - 0.15 * stop, lean=-0.08 * stop * (1 - ramp(t, t_hit + 0.4, t_hit + 1.2)))
        for side, sgn in (("armL", -1), ("armR", 1)):
            sw = math.sin(ph + (0 if sgn < 0 else math.pi)) * (1 - stop)
            P[side] = dict(el=(sgn * (74 - 6 * stop), 112 - 16 * sw), wr=(sgn * (62 - 16 * max(0, sw)), 196 - 110 * max(0, sw)),
                           curl=0.5 - 0.2 * stop, flip=sgn > 0)
        rig.draw_character(ctx2, rig.ZOMBIE, P, flick(LF0, t), t)
        if t >= t_hit - 0.05:
            k = clamp(1 - (t - t_hit) / 1.2)
            soft_dot(ctx2, x, y + 110 * s, 380 * s * (1 + (1 - k)), hexc("ffe0a0"), 0.75 * k)

    ext(ctx, t, cam, 0.25, east=True, stars=0.3, extras=[(cam.depth(Zz) - 0.05, zfn)])
    if t < t_hit:
        u = clamp((t - t_fall) / (t_hit - t_fall))
        x, y, s = place(cam, 0, Zz)
        soul_orb(ctx, lerp(W / 2 + 60, x, ease2(u)), lerp(-60, y + 110 * s, ease2(u)), 14, t)
        for k in range(10):
            uu = clamp(u - k * 0.04)
            soft_dot(ctx, lerp(W / 2 + 60, x, ease2(uu)), lerp(-60, y + 110 * s, ease2(uu)), 9 - k * 0.6, hexc("fff0c8"), 0.4 * (1 - k / 10))


# ---------------------------------------------------------------- WAKE
w0, w1_ = S("wake")
t_wk = L("w1")[1] + 0.1


@shot(w0, t_wk)
def wake_ecu(ctx, t):
    tt = t - w0
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *hexc("2a2244")); g.add_color_stop_rgb(1, *hexc("3a2a40"))
    ctx.set_source(g); ctx.paint()
    look0 = L("w1")[0] - w0 + 0.2
    gx = kf(tt, [(0, 0.0), (look0, 0.0), (look0 + 0.5, -0.7), (look0 + 1.2, -0.7), (look0 + 1.7, 0.65), (look0 + 2.4, 0.65),
                 (look0 + 2.9, 0.1)])
    stir = ramp(tt, look0 - 0.4, look0 + 0.6)
    flick_ = 0.2 * max(0.0, math.sin(tt * 5.0)) * stir  # a faint warmth flickering deep in the milky eyes
    E = ZE(t, lid=lerp(0.4, 0.24, stir), milky=1.0, drone=lerp(1.0, 0.8, stir), grime=1.0, life=0.0, glow=flick_, pupil=0.3,
           gx=gx, gy=0.05, bi=0.3 * stir, bo=0.05, op=0.14, sm=-0.25, blinks=False, talk=0.0)
    s = 4.7
    P = dict(x=W / 2 - gx * 4, y=440 + 90 * s, s=s, E=E, breath=0.6, yaw=gx * 0.15,
             roll=0.06 * (1 - stir) + 0.02 * math.sin(tt * 0.8))
    rig.draw_character(ctx, rig.ZOMBIE, P, LF1, t)


t_ign = word_t("w2", "see") - 0.35
t_frz = L("w3")[0] - 0.3


@shot(t_wk, t_frz)
def wake_cu(ctx, t):
    """The awakening: it rubs its eyes, then holds its face; under its hands the eyes ignite and the grime lifts."""
    cam = frame_cam(0, ZC, -1, 2.3, 300, 430, cam_y=1.55)
    a_up, a_rub, a_hold, a_low = t_wk + 0.55, t_ign - 0.5, t_ign - 0.08, t_frz - 0.12
    rubk = ramp(t, a_up - 0.05, a_up + 0.1) * (1 - ramp(t, a_rub - 0.05, a_rub + 0.08))
    osc = math.sin(t * 11.0) * 4 * rubk

    def keys(rest, rub, hold, low):
        return [(t_wk, rest), (a_up, rub), (a_rub, rub), (a_hold, hold), (t_frz - 0.95, hold), (a_low, low)]
    wrL = kf(t, keys((-62, 200), (-24, -40), (-50, -26), (-62, 198)))
    elL = kf(t, keys((-74, 112), (-78, 62), (-92, 58), (-78, 112)))
    wrR = kf(t, keys((62, 200), (24, -40), (50, -26), (62, 196)))
    elR = kf(t, keys((74, 112), (78, 62), (92, 58), (78, 112)))
    angL = kf(t, keys(1.6, 2 * math.pi - 1.42, 2 * math.pi - 1.48, 1.62))
    angR = kf(t, keys(1.54, -1.72, -1.66, 1.52))
    curl = kf(t, keys(0.5, 0.55, 0.12, 0.5))
    thumb = kf(t, keys(0.4, 0.6, 0.3, 0.4))
    tr = ramp(t, t_ign - 0.15, t_ign + 1.0)
    burst = math.sin(clamp((t - (t_ign - 0.1)) / 1.5) * math.pi)
    E = ZE(t, lid=max(0.92 * rubk, lerp(0.38, 0.0, tr)), milky=1 - tr, drone=1 - tr, grime=lerp(1.0, 0.25, tr), life=0.4 * tr,
           glow=0.95 * burst + 0.3 * tr, pupil=lerp(0.25, 0.55, tr), bi=lerp(0.25, 0.8, tr), bo=lerp(0.0, 0.35, tr),
           gx=0.0, gy=lerp(0.1, -0.05, tr), sm=lerp(-0.25, -0.05, tr), blinks=False)
    pose = dict(E=E, pitch=lerp(0.15, -0.04, tr) + 0.06 * rubk, roll=0.03 * math.sin(t * 0.9), shrug=0.15 * rubk + 0.2 * tr,
                breath=1.3,
                armL=dict(el=elL, wr=(wrL[0] + osc, wrL[1] + osc * 0.5), hand_ang=angL, curl=curl, spread=0.35, thumb=thumb, flip=False),
                armR=dict(el=elR, wr=(wrR[0] - osc, wrR[1] + osc * 0.5), hand_ang=angR, curl=curl, spread=0.35, thumb=thumb, flip=True))
    chest = ramp(t, t_wk + 0.2, t_ign - 0.35) * (1 - ramp(t, t_ign - 0.15, t_ign + 0.5))

    def soul_glow(ctx2):
        x, y, s_ = place(cam, 0, ZC)
        soft_dot(ctx2, x, y + 70 * s_, 260 * s_, hexc("ffd890"), 0.55 * chest * (0.8 + 0.2 * math.sin(t * 9)))
    pose["alive"] = 0.3
    ext(ctx, t, cam, 0.3, east=True, stars=0.3, extras=[zitem(cam, t, pose), (cam.depth(ZC) - 0.1, soul_glow)])
    if burst > 0:
        soft_dot(ctx, W / 2, 430, 430, hexc("ffd890"), 0.22 * burst)
        for q in range(14):  # golden motes rising off the face
            u = ((t - t_ign) * 0.6 + hsh(q, 131)) % 1.0
            soft_dot(ctx, W / 2 + (hsh(q, 132) - 0.5) * 260, 520 - u * 300, 5 + 4 * hsh(q, 133), hexc("fff0c0"), 0.6 * burst * (1 - u))


@shot(t_frz, w1_)
def wake_freeze(ctx, t):
    cam = frame_cam(0, ZC, -1, 3.4, 165, 400, cam_y=1.5)
    E = ZE(t, bi=0.85, bo=0.35, lid=0.0, low=0.0, glow=0.35, pupil=0.55, gx=0.18, gy=-0.03, life=0.4, sm=-0.1, blinks=False)
    pose = dict(E=E, yaw=0.08, pitch=-0.04, shrug=0.4, breath=0.25,
                armL=dict(el=(-78, 112), wr=(-62, 196), hand_ang=1.62, curl=0.5, spread=0.1, flip=False),
                armR=dict(el=(78, 112), wr=(62, 196), hand_ang=1.52, curl=0.5, spread=0.1, flip=True))
    t_b = L("w3")[0] + 0.5  # clipped by a runner while frozen: jostled, but the face never changes
    add_bump(pose, t, t_b, 1)
    run = runners(cam, t, t_frz, ((-0.95, 6.0), (-1.4, 10.5), (0.85, 12.6), (0.7, 9.4, True)), seed=540) + bump_runner(cam, t, t_b, 1, 571)
    ext(ctx, t, cam, 0.3, east=True, stars=0.3, extras=[zitem(cam, t, pose)] + run)


# ---------------------------------------------------------------- HANDS
c0, c1_ = S("hands")


@shot(c0, c1_)
def hands(ctx, t):
    t_ctl = L("c1")[0]
    t_my = L("c2")[0]
    t_but = L("c3")[0]
    t_feel = word_t("c3", "feel")
    cam = frame_cam(0, ZC, -1, 3.3, 165, 330, cam_y=1.4)
    up = ramp(t, t_ctl, t_ctl + 1.3) * (1 - ramp(t, t_feel, t_feel + 1.2) * 0.7)
    fl = 0.5 + 0.5 * math.sin((t - t_ctl) * 1.7)
    curl = lerp(0.15, 0.75, fl * ramp(t, t_ctl + 1.0, t_ctl + 1.6))
    lookdown = ramp(t, t_ctl + 0.3, t_ctl + 1.1) * (1 - ramp(t, t_but + 0.6, t_but + 1.2))
    E = ZE(t, gy=lerp(0.0, 0.75, lookdown) - 0.15 * ramp(t, t_but + 0.6, t_but + 1.2), gx=0.12 * ramp(t, t_but + 0.6, t_but + 1.4),
           bi=kf(t, [(t_ctl, 0.3), (t_my, 0.55), (t_but + 0.6, 0.7), (t_feel, 0.9)]), bo=kf(t, [(t_my, 0.2), (t_feel, -0.1)]),
           glow=0.3, lid=0.15 * lookdown, sm=kf(t, [(t_but, 0.0), (t_feel, -0.4)]), tr=0.3 * ramp(t, t_feel - 0.5, t_feel + 0.5))
    hy = lerp(200, 96, up)
    pose = dict(E=E, pitch=0.5 * lookdown - 0.05, **groggy(t, 0.35, seed=2.0), breath=1.2,
                armL=dict(el=(lerp(-82, -98, up), lerp(130, 165, up)), wr=(lerp(-66, -46, up), hy), hand_ang=lerp(1.65, -0.95, up),
                          curl=lerp(0.35, curl, up), spread=0.5, thumb=0.3, flip=up < 0.5, palm=False),
                armR=dict(el=(lerp(82, 98, up), lerp(130, 165, up)), wr=(lerp(66, 46, up), hy - 6 * fl * up), hand_ang=lerp(1.49, -2.19, up),
                          curl=lerp(0.35, curl * 0.9, up), spread=0.5, thumb=0.3, flip=up > 0.5, palm=False))
    t_b = word_t("c3", "witness") - 0.25  # another runner clips it; it glances after them
    add_bump(pose, t, t_b, -1)
    k = bump_kick(t, t_b)
    pose["E"]["gx"] += -0.45 * ramp(t, t_b, t_b + 0.2) * (1 - ramp(t, t_b + 0.8, t_b + 1.3))
    for side in ("armL", "armR"):
        a = dict(pose[side])
        a["wr"] = (a["wr"][0] + 14 * k, a["wr"][1] - 8 * abs(k))
        pose[side] = a
    ext(ctx, t, cam, 0.35, east=True, stars=0.35, extras=[zitem(cam, t, pose)] + bump_runner(cam, t, t_b, -1, 572))


# ---------------------------------------------------------------- WITNESS
v0, v1_ = S("witness")
t_reach = L("v2")[0] - 0.5
t_dust = L("v3")[0] - 0.3
t_react = word_t("v3", "suffering") - 0.6
t_pain = L("v4")[0] - 0.3
t_lone = L("v6")[0] - 0.3


@shot(v0, t_reach)
def witness_ots(ctx, t):
    cam = Cam(x=0.5, y=1.7, z=ZC - 2.4, d=1, f=720, hy=470)
    look = kf(t, [(v0, -0.25), (v0 + 1.4, -0.25), (v0 + 2.2, 0.2), (v0 + 3.6, 0.2), (v0 + 4.4, -0.05)])
    pose = dict(view="back", yaw=look, pitch=0.05, E=rig.expr(), **arms_hang(t), **groggy(t, 1.0, seed=0.7), alive=0.35)
    ext(ctx, t, cam, 0.35, extras=[zitem(cam, t, pose, light=flick(LB0, t))], building=True)


@shot(t_reach, t_dust)
def witness_reach(ctx, t):
    tv = L("v2")[0]
    cam = frame_cam(0, ZC, -1, 3.6, 150, 330, sx=430, cam_y=1.45)
    r = ramp(t, tv - 0.3, tv + 0.6)
    gg = groggy(t, 1.0 - r, seed=1.3)
    step = ramp(t, tv - 0.35, tv + 0.25)
    gg["legs"]["liftL"] = max(gg["legs"]["liftL"], math.sin(step * math.pi) * 0.35)
    gg["legs"]["dxL"] = lerp(gg["legs"]["dxL"], -26, step)
    gg["lean"] -= 0.07 * r
    gg["iroll"] += 0.03 * r
    E = ZE(t, bi=0.85, bo=-0.25, gx=-0.55, gy=0.0, glow=0.3, tr=0.5, sm=-0.3)
    pose = dict(E=E, yaw=-0.3, **gg,
                armL=dict(el=(lerp(-74, -122, r), lerp(110, 78, r)), wr=(lerp(-62, -212, r), lerp(200, 44, r)),
                          hand_ang=lerp(1.6, math.pi - 0.15, r), curl=lerp(0.35, 0.15, r), spread=0.55, thumb=0.35, flip=False),
                armR=dict(a1=8, a2=4, curl=0.4, flip=True))
    run = runners(cam, t, t_reach, ((1.3, 5.6),), seed=560)
    ext(ctx, t, cam, 0.35, east=True, stars=0.35, extras=[zitem(cam, t, pose)] + run)


@shot(t_dust, t_react)
def witness_dust(ctx, t):
    u = (t - t_dust) / (t_react - t_dust)
    cam = Cam(x=-2 + u * 2, y=2.2, z=WALL - 95 + u * 8, d=1, f=950, hy=600)
    td = word_t("v3", "destroyed")
    hits = staged_hit(cam, t, td - 0.2, -0.8, WALL - 78, seed=611) + staged_hit(cam, t, td + 0.9, -3.6, WALL - 74, seed=612) + \
        staged_hit(cam, t, td + 2.0, 1.6, WALL - 70, seed=613, quad=True)
    ext(ctx, t, cam, 0.4, extras=hits)
    world.draw_motes(ctx, t, 34, hexc("c8b8a8"), 0.16, drift=(30, -8))


@shot(t_react, t_pain)
def witness_react(ctx, t):
    cam = frame_cam(0, ZC, -1, 2.2, 260, 520, cam_y=1.55)
    fl = HORDE.flash(t)
    E = ZE(t, bi=0.7 + 0.2 * fl, bo=-0.2, glow=0.25 + 0.3 * fl, tr=0.6, sm=-0.45, gy=-0.05, gx=0.05, low=0.2 + 0.3 * fl)
    pose = dict(E=E, **idle(t, 0.6), pitch=0.05 + 0.04 * fl, **arms_hang(t))
    ext(ctx, t, cam, 0.4, east=True, stars=0.35, extras=[zitem(cam, t, pose)])


@shot(t_pain, t_lone)
def witness_pain(ctx, t):
    hits = [word_t("v4", "sorrow"), word_t("v4", "see"), word_t("v4", "suffering"), word_t("v5", "hurts", 0), word_t("v5", "loneliness"),
            word_t("v5", "destruction"), word_t("v5", "hurts", 1)]
    j = 0.0
    for h in hits:
        if h <= t < h + 1.2:
            j = max(j, math.sin(clamp((t - h) / 1.2) * math.pi) * (1 - clamp((t - h) / 1.2)) * 1.6)
    cam = frame_cam(0, ZC, -1, 2.0, 300, 470, cam_y=1.6)
    t_v5 = L("v5")[0]
    clutch = ramp(t, t_v5 - 0.6, t_v5 + 0.3)
    E = ZE(t, bi=0.88 + 0.12 * j, bo=-0.3, lid=0.05 + 0.8 * j, low=0.45 + 0.3 * j, sm=-0.65 - 0.25 * j, wd=0.45 + 0.4 * j,
           op=0.06 + 0.12 * j, tr=0.6, glow=0.2, gy=0.1)
    pose = dict(E=E, yaw=-0.04 * j, pitch=0.08 + 0.12 * j + 0.1 * clutch, roll=0.05 * j, shrug=0.2 + 0.3 * j, breath=1.6, breath_T=2.2,
                armL=dict(el=(lerp(-74, -82, clutch), lerp(112, 120, clutch)), wr=(lerp(-62, -10, clutch), lerp(200, 50, clutch)),
                          hand_ang=lerp(1.6, -0.5, clutch), curl=lerp(0.35, 0.8, clutch), thumb=0.7, flip=False),
                armR=dict(a1=8, a2=4, curl=0.5, flip=True))
    ext(ctx, t, cam, 0.45, east=True, stars=0.35, extras=[zitem(cam, t, pose)])
    if j > 0:
        soft_dot(ctx, W / 2, 500, 700, hexc("2a1030"), 0.18 * j)


@shot(t_lone, v1_)
def witness_lone(ctx, t):
    u = (t - t_lone) / (v1_ - t_lone)
    tw = word_t("v6", "witness")
    ts = word_t("v6", "suffering")
    cam = frame_cam(0, ZC, -1, 11 - u * 2.0, 72 + 10 * u, 500, cam_y=2.0)
    glow = 0.25 + 0.6 * ramp(t, tw - 0.3, tw + 0.3) * (1 - 0.7 * ramp(t, ts - 0.2, ts + 0.6))
    E = ZE(t, bi=0.6, glow=glow, gy=0.05)
    pose = dict(E=E, **idle(t, 0.4), **arms_hang(t), legs=dict(mode="stand"))

    def halo(ctx2):
        x, y, s = place(cam, 0, ZC)
        soft_dot(ctx2, x, y + 200 * s, 900 * s, hexc("ffd890"), 0.3 * glow)
    ext(ctx, t, cam, 0.5, east=True, stars=0.4, extras=[(cam.depth(ZC) + 0.01, halo), zitem(cam, t, pose)])


# ---------------------------------------------------------------- KNEES
k0, k1_ = S("knees")
t_fell = word_t("k1", "fell") - 0.1
t_cover = word_t("k1", "covered") - 0.2
t_alone = L("k2")[0] - 0.3
t_rev = L("k3")[0] - 0.3
t_why = L("k4")[0] - 0.4
t_pow = L("k5")[0] - 0.3
t_tears = word_t("k5", "tears") - 0.4
t_others = word_t("k5", "others") - 0.5
t_giving = word_t("k5", "giving") - 0.6


def kneel_pose(t, t_f, t_c, k_hold=None):
    """Standing -> fall to knees at t_f -> cover face at t_c."""
    k = ramp(t, t_f, t_f + 0.55) if k_hold is None else k_hold
    c = ramp(t, t_c, t_c + 0.65)
    ca = ramp(c, 0.0, 0.5)
    sob = math.sin(t * 2 * math.pi / 2.4) * c
    E = ZE(t, bi=0.9, bo=-0.3, lid=max(0.3 * k, c), low=0.4 * c, sm=-0.55, tr=0.5, glow=0.15, gy=0.3 * k)
    P = dict(E=E, pitch=0.12 * k + 0.25 * c + 0.03 * sob, roll=0.02 * sob, shrug=0.15 * c + 0.12 * max(0, sob), breath=0.4,
             legs=dict(mode="kneel", k=k), lean=0.06 * k)
    P["armL"] = dict(el=(lerp(-74, -40, c), lerp(112, 64, c)), wr=(lerp(-62, -24, c), lerp(200, -34, c)),
                     hand_ang=lerp(1.6, 2 * math.pi - 1.62, ca), curl=lerp(0.4, 0.06, c), spread=lerp(0.3, 0.5, c),
                     thumb=lerp(0.4, 0.15, c), flip=False, hs=lerp(1, 1.1, c))
    P["armR"] = dict(el=(lerp(74, 40, c), lerp(112, 64, c)), wr=(lerp(62, 24, c), lerp(200, -34, c)),
                     hand_ang=lerp(1.54, -1.52, ca), curl=lerp(0.4, 0.06, c), spread=lerp(0.3, 0.5, c),
                     thumb=lerp(0.4, 0.15, c), flip=True, hs=lerp(1, 1.1, c))
    return P, k


@shot(k0, t_alone)
def knees_fall(ctx, t):
    cam = frame_cam(0, ZC, -1, 4.6, 150, 330, cam_y=1.2)
    P, k = kneel_pose(t, t_fell, t_cover)
    ext(ctx, t, cam, 0.6, east=True, stars=0.45, extras=[zitem(cam, t, P, kneel=k)])


@shot(t_alone, t_rev)
def knees_alone(ctx, t):
    u = (t - t_alone) / (t_rev - t_alone)
    tm = word_t("k2", "meaning")
    cam = Cam(x=0, y=lerp(5.5, 7.5, ease(u)), z=ZC - lerp(8, 10.5, u), d=1, f=900, hy=lerp(240, 220, u))
    P, k = kneel_pose(t, -10, -10)
    P["view"] = "back"
    P["arms_behind"] = ("L", "R")
    g = ramp(t, tm - 0.4, tm + 0.4) * (1 - ramp(t, tm + 1.5, tm + 3))

    def halo(ctx2):
        x, y, s = place(cam, 0, ZC, 1)
        soft_dot(ctx2, x, y + 250 * s, 1100 * s, hexc("ffd890"), 0.15 + 0.45 * g)
    ext(ctx, t, cam, 0.65, extras=[(cam.depth(ZC) + 0.01, halo), zitem(cam, t, P, kneel=1, light=flick(LB0, t))])


@shot(t_rev, t_why)
def knees_reveal(ctx, t):
    t_lower = t_rev + 1.0
    t_heaven = word_t("k3", "heaven") - 0.2
    cam = frame_cam(0, ZC, -1, 2.4, 230, 470, cam_y=1.1, kneel=1)
    c = 1 - ramp(t, t_lower, t_lower + 2.2)
    look_hands = ramp(t, t_lower + 1.2, t_lower + 2.4) * (1 - ramp(t, t_heaven - 0.2, t_heaven + 0.4)) + \
        ramp(t, t_heaven + 1.4, t_heaven + 2.2) * 0.6
    up = ramp(t, t_heaven - 0.2, t_heaven + 0.4) * (1 - ramp(t, t_heaven + 1.4, t_heaven + 2.2))
    tears = []
    ts = tear_state(t, t_lower + 2.6, 3.0)
    if ts:
        tears.append((1, ts[0], ts[1]))
    E = ZE(t, bi=0.85, bo=-0.2, lid=max(c * 0.95, 0.25 + 0.1 * look_hands), sm=-0.45, tr=0.4, glow=0.15 + 0.25 * up,
           gy=0.6 * look_hands - 0.6 * up, gx=0.05, tears=tears)
    hand_y = lerp(-34, 118, 1 - c)
    cu = 1 - c
    flipk = cu > 0.5
    P = dict(E=E, pitch=0.28 * c + 0.25 * look_hands - 0.25 * up, legs=dict(mode="kneel", k=1), shrug=0.1, breath=1.0, **idle(t, 0.4),
             armL=dict(el=(lerp(-40, -84, cu), lerp(64, 150, cu)), wr=(lerp(-24, -40, cu), hand_y),
                       hand_ang=kf(cu, [(0, -1.62), (0.55, -1.5), (1.0, 1.25 - 2 * math.pi)]), hfs=lerp(1.0, 0.55, cu),
                       curl=lerp(0.06, 0.35, cu), spread=0.35, thumb=lerp(0.15, 0.5, cu), flip=flipk, palm=flipk, hs=1.1),
             armR=dict(el=(lerp(40, 84, cu), lerp(64, 150, cu)), wr=(lerp(24, 40, cu), hand_y),
                       hand_ang=kf(cu, [(0, -1.52), (0.55, -1.64), (1.0, 1.89)]), hfs=lerp(1.0, 0.55, cu),
                       curl=lerp(0.06, 0.35, cu), spread=0.35, thumb=lerp(0.15, 0.5, cu), flip=not flipk, palm=flipk, hs=1.1))
    ext(ctx, t, cam, 0.7, east=True, stars=0.5, extras=[zitem(cam, t, P, kneel=1)])


@shot(t_why, t_pow)
def knees_why(ctx, t):
    cam = frame_cam(0, ZC, -1, 1.8, 320, 520, cam_y=1.0, kneel=1)
    tears = []
    ts = tear_state(t, t_why + 2.2, 2.6)
    if ts:
        tears.append((-1, ts[0], ts[1]))
    E = ZE(t, bi=0.9, bo=-0.1, gy=-0.45, gx=kf(t, [(t_why, -0.2), (t_why + 2.0, -0.2), (t_why + 2.6, 0.15)]), sm=-0.4, tr=0.6,
           glow=0.2, tears=tears, low=0.15)
    P = dict(E=E, pitch=-0.25, yaw=kf(t, [(t_why, -0.1), (t_why + 2.0, -0.1), (t_why + 2.6, 0.06)]), roll=0.03 * sn(t, 2, 0.5),
             legs=None, breath=1.3, **arms_hang(t))
    ext(ctx, t, cam, 0.75, east=True, stars=0.6, extras=[zitem(cam, t, P, kneel=1)])


@shot(t_pow, t_tears)
def knees_power(ctx, t):
    u = (t - t_pow) / (t_tears - t_pow)
    cam = frame_cam(0, ZC, -1, lerp(4.0, 3.2, ease(u)), lerp(150, 180, ease(u)), 440, sx=430, cam_y=1.0, kneel=1)
    P, k = kneel_pose(t, -10, -10)
    P["armL"] = dict(el=(-70, 120), wr=(-52, 205), hand_ang=1.75, curl=0.4, flip=False)
    P["armR"] = dict(el=(70, 120), wr=(52, 205), hand_ang=1.39, curl=0.4, flip=True)
    P["E"] = ZE(t, bi=0.75, bo=-0.1, lid=0.3, gy=0.35, glow=0.2, sm=-0.35)
    P["pitch"] = 0.2
    P["yaw"] = -0.25
    ext(ctx, t, cam, 0.8, east=True, stars=0.6, extras=[zitem(cam, t, P, kneel=1)])


@shot(t_tears, t_others)
def knees_tear(ctx, t):
    tt = t - t_tears
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *hexc("1a1a34")); g.add_color_stop_rgb(1, *hexc("2a2236"))
    ctx.set_source(g); ctx.paint()
    ts = tear_state(t, t_tears + 0.6, 2.4)
    tears = [(1, ts[0], ts[1])] if ts else []
    E = ZE(t, bi=0.85, bo=-0.15, lid=0.35, low=0.2, gy=0.25, tears=tears, glow=0.15, sm=-0.3, tr=0.3)
    s = 4.6
    P = dict(x=W / 2 - 30, y=440 + 90 * s, s=s, E=E, pitch=0.15, yaw=-0.12, breath=0.4)
    rig.draw_character(ctx, rig.ZOMBIE, P, LF1, t)


@shot(t_others, t_giving)
def knees_pov(ctx, t):
    u = (t - t_others) / (t_giving - t_others)
    cam = Cam(x=lerp(-0.3, 0.3, u), y=1.1, z=ZC + 0.2, d=-1, f=1300, hy=560)
    run = runners(cam, t, t_others, ((-0.7, 7.5), (0.6, 9.5), (0.0, 12.0), (1.0, 5.5), (-1.2, 10.5), (-0.25, 8.6, True)), seed=520)
    ext(ctx, t, cam, 0.85, east=True, stars=0.6, extras=run)


@shot(t_giving, k1_)
def knees_eyes(ctx, t):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *hexc("1a1a34")); g.add_color_stop_rgb(1, *hexc("2a2236"))
    ctx.set_source(g); ctx.paint()
    u = (t - t_giving) / (k1_ - t_giving)
    s = lerp(4.4, 4.8, u)
    ts = tear_state(t, t_giving + 1.2, 2.6)
    E = ZE(t, bi=0.8, bo=-0.2, lid=0.3, low=0.3, glow=lerp(0.2, 0.8, ease(u)), gx=0.0, gy=0.05, pupil=0.48, sm=-0.25,
           tears=[(-1, ts[0], ts[1])] if ts else [])
    P = dict(x=W / 2, y=440 + 90 * s, s=s, E=E, breath=0.3)
    rig.draw_character(ctx, rig.ZOMBIE, P, LF1, t)


# ---------------------------------------------------------------- SKY
y0_, y1_ = S("sky")
t_chest = L("y3")[0] - 0.3
t_wide = L("y5")[0] - 0.3
t_eyes2 = word_t("y5", "But") - 0.3
t_hell = L("y6")[0] - 0.3
t_stair = L("y7")[0] - 0.3


@shot(y0_, t_chest)
def sky_up(ctx, t):
    t_sent = word_t("y2", "sent")
    cam = frame_cam(0, ZC, -1, 2.6, 190, 760, cam_y=0.6, kneel=1)
    look = ramp(t, y0_, y0_ + 1.2)
    E = ZE(t, bi=0.7, bo=0.1, gy=-0.95 * look, gx=kf(t, [(y0_ + 2.0, 0.0), (y0_ + 3.5, -0.3), (L("y2")[0] + 2, -0.3), (L("y2")[0] + 3, 0.1)]),
           glow=0.25, sm=-0.2, low=0.1)
    fid = [0.45 + 0.3 * math.sin(t * 3.1 + q) * (0.6 + 0.4 * math.sin(t * 0.7 + q)) for q in (0, 2.2)]
    rock = 0.05 * math.sin(2 * math.pi * t / 2.6)
    P = dict(E=E, pitch=-0.85 * look + rock, roll=0.02 * sn(t, 1, 0.3) + 0.05 * look, legs=dict(mode="kneel", k=1), breath=1.4,
             alive=1.8,
             armL=dict(el=(-82, 150), wr=(-48 + 5 * math.sin(t * 1.3), 262), hand_ang=1.35, curl=fid[0], spread=0.3, thumb=0.5,
                       hfs=0.62, flip=False),
             armR=dict(el=(82, 150), wr=(48 + 5 * math.sin(t * 1.1 + 1), 262), hand_ang=1.79, curl=fid[1], spread=0.3, thumb=0.5,
                       hfs=0.62, flip=True))
    ext(ctx, t, cam, 1.7, east=True, stars=1.0, extras=[zitem(cam, t, P, kneel=1, light=LFn)], moon=(W * 0.68, 300, 76))
    if t_sent - 0.2 < t < t_sent + 2.0:  # memory of the soul's descent
        u = (t - (t_sent - 0.2)) / 2.2
        a = math.sin(clamp(u) * math.pi)
        x, y = lerp(W * 0.8, W * 0.55, u), lerp(80, 420, u)
        soul_orb(ctx, x, y, 7, t, 0.6 * a)


@shot(t_chest, t_wide)
def sky_chest(ctx, t):
    te = word_t("y4", "existence")
    tp = word_t("y4", "plans") - 0.3
    ta = word_t("y4", "actions")
    tl = word_t("y4", "life") - 0.2
    cam = frame_cam(0, ZC, -1, 2.6, 200, 430, cam_y=1.0, kneel=1)
    h = ramp(t, t_chest + 0.6, t_chest + 2.0)
    up = ramp(t, tp - 0.3, tp + 0.5)
    g = 0.25 + 0.4 * h + 0.5 * ramp(t, te - 0.4, te + 0.3) * (1 - ramp(t, te + 1.8, te + 3)) + 0.5 * ramp(t, tl - 0.3, tl + 0.5)
    nod = math.sin(clamp((t - ta) / 0.7) * math.pi) * 0.12
    E = ZE(t, bi=lerp(0.45, 0.15, up), bo=0.05, gy=lerp(-0.4, 0.55, ramp(t, t_chest, t_chest + 1.2)) - 0.45 * ramp(t, te - 0.5, te + 0.2)
           * (1 - up) - 0.25 * up, gx=0.12 * up, glow=g * 0.6, lid=lerp(0.15, 0.05, up), sm=0.08 * ramp(t, tl, tl + 0.8))
    P = dict(E=E, pitch=lerp(-0.2, 0.25, ramp(t, t_chest, t_chest + 1.2)) - 0.25 * ramp(t, te - 0.5, te + 0.2) * (1 - up) - 0.12 * up + nod,
             legs=dict(mode="kneel", k=1), breath=1.0,
             armR=dict(el=(lerp(74, 70, h), lerp(112, 128, h)), wr=(lerp(62, 6, h), lerp(200, 70, h)), hand_ang=lerp(1.5, -2.6, h),
                       curl=lerp(0.35, 0.12, h), spread=0.35, thumb=0.3, flip=True),
             armL=dict(a1=-8, a2=-4, curl=0.35, flip=False))

    def glow_fn(ctx2):
        x, y, s = place(cam, 0, ZC, 1)
        soft_dot(ctx2, x - 10 * s, y + 70 * s, 140 * s, hexc("ffd890"), 0.6 * g * h)
    ext(ctx, t, cam, 1.8, east=True, stars=1.0, extras=[zitem(cam, t, P, kneel=1, light=LFn), (cam.depth(ZC) - 0.1, glow_fn)])


@shot(t_wide, t_eyes2)
def sky_wide(ctx, t):
    u = (t - t_wide) / (t_eyes2 - t_wide)
    cam = Cam(x=-1.0, y=lerp(2.0, 2.4, u), z=ZC - 5 - u * 1.5, d=1, f=700, hy=520)
    P, k = kneel_pose(t, -10, -10)
    P["view"] = "back"
    P["pitch"] = -0.2
    P["armL"] = dict(a1=-8, a2=-4, curl=0.35, flip=False)
    P["armR"] = dict(el=(70, 128), wr=(10, 70), hand_ang=-2.6, curl=0.12, flip=True)
    P["arms_behind"] = ("R",)

    def glow_fn(ctx2):
        x, y, s = place(cam, 0, ZC, 1)
        soft_dot(ctx2, x, y + 70 * s, 260 * s, hexc("ffd890"), 0.45)
    ext(ctx, t, cam, 1.9, stars=0.9, extras=[zitem(cam, t, P, kneel=1, light=LBn), (cam.depth(ZC) - 0.1, glow_fn)], building=True)


@shot(t_eyes2, t_hell)
def sky_eyes(ctx, t):
    th_ = word_t("y5", "help") - 0.3
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *hexc("141530")); g.add_color_stop_rgb(1, *hexc("241c34"))
    ctx.set_source(g); ctx.paint()
    u = (t - t_eyes2) / (t_hell - t_eyes2)
    s = lerp(4.4, 4.8, u)
    res = ramp(t, th_, th_ + 0.8)
    E = ZE(t, bi=lerp(0.75, 0.15, res), bo=lerp(-0.15, -0.1, res), lid=lerp(0.28, 0.12, res), low=lerp(0.25, 0.1, res),
           glow=lerp(0.3, 0.9, res),
           gx=kf(t, [(t_eyes2, 0.2), (t_eyes2 + 1.5, 0.2), (t_eyes2 + 2.2, 0.0)]), pupil=0.46)
    P = dict(x=W / 2, y=440 + 90 * s, s=s, E=E, breath=0.3)
    rig.draw_character(ctx, rig.ZOMBIE, P, LFn, t)


@shot(t_hell, t_stair)
def sky_hell(ctx, t):
    u = (t - t_hell) / (t_stair - t_hell)
    cam = Cam(x=lerp(-6, 4, u), y=6, z=ZC + 20 + u * 10, d=1, f=760, hy=440)
    ext(ctx, t, cam, 2.0, stars=0.6)
    soft_dot(ctx, W / 2, 520, 800, hexc("c03a20"), 0.22)
    world.draw_motes(ctx, t, 50, hexc("ff9a50"), 0.35, seed=3, drift=(10, -30))


@shot(t_stair, y1_)
def sky_stair(ctx, t):
    u = (t - t_stair) / (y1_ - t_stair)
    tw = word_t("y7", "well-being") - 0.3
    cam = Cam(x=BLD[0] - 1.0, y=lerp(1.5, 8.5, ease2(u)), z=BLD[1] - 9, d=1, f=700, hy=lerp(700, 640, u))
    lt = LBn
    ext(ctx, t, cam, 2.0, stars=0.8, building=True, horde=False, fire=False, light=lt)
    warm = ramp(t, tw, tw + 1.5)
    # light from a break in the clouds onto the roof
    top = cam.p(BLD[0] - 1.0, 14.2, BLD[1] + 2.5)
    for k in range(5):
        ctx.new_path(); ctx.move_to(top[0] - 120 + k * 40, -50); ctx.line_to(top[0] - 30 + k * 10, top[1])
        ctx.line_to(top[0] - 10 + k * 10, top[1]); ctx.line_to(top[0] - 70 + k * 40, -50); ctx.close_path()
        rgba(ctx, mix(hexc("b8c8ff"), hexc("ffe0a0"), warm), 0.06 + 0.05 * warm); ctx.fill()
    soft_dot(ctx, top[0], top[1], 160, mix(hexc("b8c8ff"), hexc("ffe0a0"), warm), 0.25 + 0.3 * warm)


# ---------------------------------------------------------------- BUILDING
b0, b1_ = S("building")
t_stand = L("b2")[0] - 0.7
t_seeb = word_t("b1", "looked") - 0.1
t_climb = L("b3")[0] - 0.4
t_roof = L("b4")[0] - 0.3


@shot(t_seeb, t_stand)
def bld_pov(ctx, t):
    u = (t - t_seeb) / (t_stand - t_seeb)
    cam = Cam(x=12.5, y=1.1, z=ZC - 1 + u * 1.5, d=1, f=640, hy=600)
    lt = dict(LBn)
    ext(ctx, t, cam, 1.9, stars=0.9, building=True, light=lt)
    top = cam.p(BLD[0] - 1.0, 14.2, BLD[1] + 2.5)
    soft_dot(ctx, top[0], top[1], 120, hexc("ffe0a0"), 0.25)


@shot(b0, t_seeb)
def bld_wipe(ctx, t):
    tw0 = b0 + 0.6
    tl = word_t("b1", "looked") - 0.2
    cam = frame_cam(0, ZC, -1, 2.4, 230, 470, cam_y=1.1, kneel=1)
    wipe = ramp(t, tw0, tw0 + 0.6) * (1 - ramp(t, tw0 + 2.2, tw0 + 2.9))
    wx = math.sin((t - tw0) * 2.4) * 10 * wipe
    look = ramp(t, tl, tl + 0.7)
    E = ZE(t, bi=lerp(0.7, 0.35, look), lid=0.35 * wipe + 0.1, gx=-0.65 * look, gy=-0.1 * look, glow=0.25 + 0.2 * look,
           sm=-0.2 * (1 - look))
    P = dict(E=E, pitch=0.15 * wipe - 0.08 * look, yaw=-0.35 * look, legs=dict(mode="kneel", k=1), breath=1.0, **idle(t, 0.4),
             armR=dict(el=(lerp(74, 88, wipe), lerp(112, 62, wipe)), wr=(lerp(62, 24 + wx, wipe), lerp(200, -20, wipe)),
                       hand_ang=lerp(1.5, -2.3, wipe), curl=lerp(0.35, 0.5, wipe), thumb=0.6, flip=True),
             armL=dict(a1=-8, a2=-4, curl=0.35, flip=False))
    ext(ctx, t, cam, 1.8, east=True, stars=0.9, extras=[zitem(cam, t, P, kneel=1, light=LFn)])


@shot(t_stand, t_climb)
def bld_stand(ctx, t):
    cam = frame_cam(0, ZC, -1, 3.6, 160, 360, cam_y=1.3)
    k = 1 - ramp(t, t_stand, t_stand + 0.9)
    nod = ramp(word_t("b2", "something") - 0.2, 0, 1)
    E = ZE(t, bi=lerp(0.4, -0.25, 1 - k), bo=0.0, press=0.4 * (1 - k) if not speaking("Z", t) else 0, glow=0.45, gx=-0.1)
    P = dict(E=E, pitch=0.12 * k + 0.1 * math.sin(clamp((t - word_t("b2", "something")) / 0.6) * math.pi), legs=dict(mode="kneel", k=k),
             breath=1.4, **arms_hang(t))
    ext(ctx, t, cam, 1.9, east=True, stars=0.9, extras=[zitem(cam, t, P, kneel=k, light=LFn)])


@shot(t_climb, t_roof)
def bld_climb(ctx, t):
    u = clamp((t - t_climb) / (t_roof - t_climb))
    lx = BLD[0] - 4.0 + 0.9
    Yz = lerp(0.2, 7.5, u)
    cam = Cam(x=lx + 0.4, y=Yz + 1.3, z=BLD[1] - 5.0, d=1, f=760, hy=620)
    cyc = (t - t_climb) * 3.0 * math.pi

    def climber(ctx2):
        x, y, s = place(cam, lx, BLD[1] - 0.35, 0, Y=Yz)
        a = math.sin(cyc)
        P = dict(x=x, y=y, s=s, view="back", pitch=-0.25, breath=0.5,
                 armL=dict(el=(-80, -20 - 30 * a), wr=(-52, -150 - 50 * a), hand_ang=-1.57, curl=0.85, thumb=0.8, flip=False),
                 armR=dict(el=(80, -20 + 30 * a), wr=(52, -150 + 50 * a), hand_ang=-1.57, curl=0.85, thumb=0.8, flip=True),
                 legs=dict(mode="run", phase=cyc + 1.57), E=rig.expr())
        rig.draw_character(ctx2, rig.ZOMBIE, P, LBn, t)
    ext(ctx, t, cam, 2.0, stars=0.7, building=True, horde=False, fire=False,
        extras=[(cam.depth(BLD[1]) - 0.4, climber)], light=LBn)


@shot(t_roof, b1_)
def bld_flag(ctx, t):
    tf = word_t("b4", "flag") - 0.2
    rise = ramp(t, t_roof, t_roof + 1.0)
    cam = Cam(x=BLD[0] - 2.4, y=11.6, z=BLD[1] - 2.4, d=1, f=700, hy=520)
    lt = dict(LBn)
    lt["rim"] = mix(LBn["rim"], hexc("ffe0a0"), ramp(t, tf, tf + 0.5))

    def head(ctx2):
        x, y, s = place(cam, BLD[0] - 3.1, BLD[1] + 0.3, 0, Y=lerp(9.4, 10.9, rise))
        P = dict(x=x, y=y, s=s, view="back", pitch=-0.05, yaw=0.15 * ramp(t, tf - 0.5, tf + 0.3), E=rig.expr(),
                 legs=dict(mode="run", phase=1.57 * (1 - rise)),
                 armL=dict(el=(-88, 80), wr=(-64, 150), hand_ang=1.57, curl=0.8, thumb=0.7, flip=False),
                 armR=dict(el=(88, 80), wr=(64, 150), hand_ang=1.57, curl=0.8, thumb=0.7, flip=True))
        rig.draw_character(ctx2, rig.ZOMBIE, P, lt, t)
    ext(ctx, t, cam, 2.0, stars=0.7, building=True, extras=[(cam.depth(BLD[1]) - 0.6, head)], light=lt)
    fp = cam.p(BLD[0] - 1.0, 14.2, BLD[1] + 2.5)
    soft_dot(ctx, fp[0] + 40, fp[1] + 20, 120, hexc("ffe8c0"), 0.2 * ramp(t, tf, tf + 0.6))


# ---------------------------------------------------------------- FLAG
f0, f1_ = S("flag")
t_grab = word_t("f1", "grabbed") - 0.1
t_shout = L("f2")[0] - 0.4
t_fwide = L("f3")[0] - 0.3


def pole_angle(t, t0):
    w = ramp(t, t0 + 0.7, t0 + 1.4)
    return 0.4 * math.sin((t - t0) * 2 * math.pi / 1.7) * w, w


def draw_pole_hands(ctx2, x, y, s, t, t0, lt=None, view="back", lift=1.0):
    """Body-space pole held in both hands; returns arm dicts."""
    ang, w = pole_angle(t, t0)
    px, py = 10, lerp(60, -20, lift)
    L_ = 1050
    top = (px + math.sin(ang) * L_ * 0.75, py - math.cos(ang) * L_ * 0.75)
    bot = (px - math.sin(ang) * L_ * 0.06, py + math.cos(ang) * L_ * 0.06)
    h1 = (px + math.sin(ang) * 30, py - math.cos(ang) * 30)
    h2 = (px + math.sin(ang) * 230, py - math.cos(ang) * 230)
    return ang, top, bot, h1, h2


@shot(f0, t_shout)
def flag_wave(ctx, t):
    cam = Cam(x=BLD[0] - 2.0, y=12.8, z=BLD[1] - 1.0, d=1, f=640, hy=640)
    lift = ramp(t, t_grab, t_grab + 0.7)
    zx, zz = BLD[0] - 2.3, BLD[1] + 1.8

    def fig(ctx2):
        x, y, s = place(cam, zx, zz, 0, Y=11.0)
        ang, top, bot, h1, h2 = draw_pole_hands(ctx2, x, y, s, t, t_grab, LBn, lift=lift)
        # body-space -> screen
        sx = lambda p: (x + p[0] * s, y + p[1] * s)
        if lift < 0.05:
            topw = cam.p(BLD[0] - 1.0, 14.2, BLD[1] + 2.5)
            botw = cam.p(BLD[0] - 1.0, 11.0, BLD[1] + 2.5)
        else:
            topw, botw = sx(top), sx(bot)
        def pole(c):
            c.new_path(); c.move_to(*botw); c.line_to(*topw)
            rgba(c, LBn["line"], 0.9); c.set_line_width(max(2, 30 * s)); c.stroke()
            c.new_path(); c.move_to(*botw); c.line_to(*topw)
            rgba(c, hexc("8a8478"), 1); c.set_line_width(max(1.2, 20 * s)); c.stroke()
            dang = math.cos((t - t_grab) * 2 * math.pi / 1.7)
            world.flag_cloth(c, topw[0], topw[1] + 5, 440 * s, 280 * s, t, 1.0, light=LBn,
                             lw=1.5, side=1 if dang < 0 else -1)
        P = dict(x=x, y=y, s=s, view="back", pitch=-0.1 - 0.15 * lift, breath=1.2, E=rig.expr(),
                 legs=dict(mode="stand"), lean=0.06 * math.sin(ang) * lift)
        if lift > 0.05:
            P["armL"] = dict(tgt=h2, bend=-1, hand_ang=ang - math.pi / 2, curl=0.85, thumb=0.8, flip=False)
            P["armR"] = dict(tgt=h1, bend=1, hand_ang=ang - math.pi / 2, curl=0.85, thumb=0.8, flip=True)
            P["arms_behind"] = ("L", "R")
            P["post"] = None
            pole(ctx2)
            rig.draw_character(ctx2, rig.ZOMBIE, P, LBn, t)
        else:
            reach = ramp(t, f0, t_grab)
            P["armR"] = dict(el=(lerp(74, 110, reach), lerp(112, 40, reach)), wr=(lerp(62, 160, reach), lerp(200, -60, reach)),
                             hand_ang=lerp(1.6, -1.3, reach), curl=lerp(0.4, 0.7, reach), flip=True)
            P["armL"] = dict(a1=-8, a2=-4, curl=0.4, flip=False)
            rig.draw_character(ctx2, rig.ZOMBIE, P, LBn, t)
    ext(ctx, t, cam, 2.0, stars=0.7, building=True, extras=[(cam.depth(BLD[1]) - 0.5, fig)], light=LBn, bflag=lift < 0.05)


@shot(t_shout, t_fwide)
def flag_shout(ctx, t):
    world.draw_sky(ctx, Cam(hy=1450, d=-1), t, 2.0, east=True, stars=1.0, moon=None)
    soft_dot(ctx, W / 2, 1300, 700, hexc("ff7a40"), 0.25)
    ang, _ = pole_angle(t, t_grab)
    sway = ang * 0.25
    tears = [(1, 0.7, 0.6), (-1, 0.55, 0.5)]
    E = ZE(t, bi=0.95, bo=0.1, op=0.15, talk=1.15, sm=-0.3, wd=0.5, glow=0.4, tr=0.4, gy=-0.2, gx=-0.05, tears=tears, low=0.2)
    x, y, s = W / 2 - 40, 470 + 92 * 2.5, 2.5
    bx, by = 600 + sway * 60, 1400
    tx, ty = 600 + sway * 500, -60
    pole_x = lambda yy: lerp(bx, tx, (yy - by) / (ty - by))
    hi_y, lo_y = 735, 965
    to_body = lambda px, py: ((px - x) / s, (py - y) / s)
    P = dict(x=x, y=y, s=s, E=E, pitch=-0.12, yaw=0.06, roll=-sway * 0.2, shrug=0.25, breath=1.8, breath_T=1.8,
             armR=dict(tgt=to_body(pole_x(hi_y) - 26 * s, hi_y), bend=-1, curl=0.85, thumb=0.8, hand_ang=0.0, flip=True),
             armL=dict(tgt=to_body(pole_x(lo_y) - 26 * s, lo_y), bend=-1, curl=0.85, thumb=0.8, hand_ang=0.0, flip=False))
    rig.draw_character(ctx, rig.ZOMBIE, P, LFn, t)
    for wdt, col in ((26, LFn["line"]), (18, hexc("8a8478"))):
        ctx.new_path(); ctx.move_to(bx, by); ctx.line_to(tx, ty)
        rgba(ctx, col, 0.95); ctx.set_line_width(wdt); ctx.stroke()
    world.flag_cloth(ctx, tx - 4, ty + 30, 330, 220, t, 1.0, light=LFn, lw=2, side=-1)
    for yy, fl in ((hi_y, True), (lo_y, False)):  # fists wrap the pole
        rig.draw_hand(ctx, rig.ZOMBIE, pole_x(yy) - 30 * s, yy, 0.0, LFn, 2.0, curl=0.9, thumb=0.85, flip=fl, size=s)


@shot(t_fwide, f1_)
def flag_lone(ctx, t):
    u = (t - t_fwide) / (f1_ - t_fwide)
    cam = Cam(x=BLD[0] + 1.0, y=1.6, z=BLD[1] - lerp(19, 14, ease(u)), d=1, f=620, hy=880)

    def fig(ctx2):
        x, y, s = place(cam, BLD[0] - 2.3, BLD[1] + 0.55, 0, Y=11.0)
        ang, top, bot, h1, h2 = draw_pole_hands(ctx2, x, y, s, t, t_grab)
        topw = (x + top[0] * s, y + top[1] * s); botw = (x + bot[0] * s, y + bot[1] * s)
        ctx2.new_path(); ctx2.move_to(*botw); ctx2.line_to(*topw)
        rgba(ctx2, hexc("1a1420")); ctx2.set_line_width(max(1.5, 20 * s)); ctx2.stroke()
        dang = math.cos((t - t_grab) * 2 * math.pi / 1.7)
        world.flag_cloth(ctx2, topw[0], topw[1], 520 * s, 330 * s, t, 1.0, light=LBn, lw=1, side=1 if dang < 0 else -1)
        P = dict(x=x, y=y, s=s, view="back", pitch=-0.25, E=rig.expr(), legs=dict(mode="stand"), arms_behind=("L", "R"),
                 armL=dict(tgt=h2, bend=-1, hand_ang=ang - math.pi / 2, curl=0.85, flip=False),
                 armR=dict(tgt=h1, bend=1, hand_ang=ang - math.pi / 2, curl=0.85, flip=True))
        rig.draw_character(ctx2, rig.ZOMBIE, P, LBn, t)
    ext(ctx, t, cam, 2.0, stars=0.8, building=True, extras=[(cam.depth(BLD[1]) + 1.2, fig)], light=LBn, bflag=False)


# ---------------------------------------------------------------- HELICOPTER
r0, r1_ = S("heli")
t_rope = L("r2")[0] - 0.3
t_grabz = L("r2a")[0] - 0.35
t_up = L("r2c")[1] + 0.12


def heli_pos(t):
    u = ramp(t, r0, L("r1")[1] + 0.3)
    return lerp(W + 500, W / 2 + 80, u), lerp(-300, 170, u), lerp(0.25, -0.05, u)


@shot(r0, t_rope)
def heli_arrive(ctx, t):
    cam = Cam(x=BLD[0] - 2.2, y=12.8, z=BLD[1] - 1.4, d=1, f=640, hy=560)
    hx, hy_, bank = heli_pos(t)
    spot = ramp(t, r0 + 1.2, r0 + 2.2)
    lt = dict(LBn)
    lt["rim"] = mix(LBn["rim"], hexc("fff4dc"), spot)
    look = ramp(t, r0 + 0.8, r0 + 1.8)
    zx, zz = BLD[0] - 2.3, BLD[1] + 1.8

    def fig(ctx2):
        x, y, s = place(cam, zx, zz, 0, Y=11.0)
        ang, top, bot, h1, h2 = draw_pole_hands(ctx2, x, y, s, t, t_grab)
        k = 1 - look
        ang *= k
        topw = (x + math.sin(ang) * 975 * s, y + (-20 - math.cos(ang) * 975) * s)
        botw = (x + -math.sin(ang) * 60 * s, y + (-20 + math.cos(ang) * 60) * s)
        ctx2.new_path(); ctx2.move_to(*botw); ctx2.line_to(*topw)
        rgba(ctx2, hexc("8a8478")); ctx2.set_line_width(max(1.5, 20 * s)); ctx2.stroke()
        world.flag_cloth(ctx2, topw[0], topw[1], 520 * s, 330 * s, t * 1.6, 1.0, light=lt, lw=1, side=-1)
        h1b = (10 + math.sin(ang) * 30, -20 - math.cos(ang) * 30)
        h2b = (10 + math.sin(ang) * 230, -20 - math.cos(ang) * 230)
        P = dict(x=x, y=y, s=s, view="back", pitch=-0.1 - 0.4 * look, yaw=0.2 * look, E=rig.expr(), legs=dict(mode="stand"),
                 arms_behind=("L", "R"),
                 armL=dict(tgt=h2b, bend=-1, hand_ang=ang - math.pi / 2, curl=0.85, flip=False),
                 armR=dict(tgt=h1b, bend=1, hand_ang=ang - math.pi / 2, curl=0.85, flip=True))
        rig.draw_character(ctx2, rig.ZOMBIE, P, lt, t)
        if spot > 0:
            soft_dot(ctx2, x, y + 300 * s, 900 * s, hexc("fff4dc"), 0.25 * spot)
    ext(ctx, t, cam, 2.0, stars=0.7, building=True, extras=[(cam.depth(BLD[1]) - 0.5, fig)], light=lt, bflag=False)
    world.draw_heli(ctx, hx, hy_, 0.9, t, LSPOT, spot=spot, bank=bank, face=-1)


@shot(t_rope, t_grabz)
def heli_rope(ctx, t):
    tt = t - t_rope
    cam = Cam(x=0, y=0, z=0, d=-1, f=700, hy=1500)
    world.draw_sky(ctx, cam, t, 2.0, east=True, stars=1.0, moon=(130, 560, 55))
    hx, hy_ = W / 2 + 40 + math.sin(t * 0.9) * 6, 260 + math.sin(t * 1.3) * 5
    world.draw_heli(ctx, hx, hy_, 1.0, t, LSPOT, spot=0.0, bank=0.0, face=-1)
    door = (hx - 5, hy_ + 40)
    drop = ramp(tt, 0.0, 0.9)
    rope_end = (door[0] + math.sin(t * 2) * 6, door[1] + drop * 1200)
    soft_stroke(ctx, [door, ((door[0] + rope_end[0]) / 2 + math.sin(t * 3) * 8, (door[1] + rope_end[1]) / 2), rope_end],
                hexc("c8b890"), 1.0, 5)
    slide = ramp(tt, 1.0, 3.6)
    if tt > 0.8:
        yb = lerp(door[1] + 40, 980, slide)
        xb = door[0] + math.sin(t * 2) * 6
        E = rig.expr(bi=-0.2, lid=0.15, gy=0.6, t=t, press=0.3)
        P = dict(x=xb + 10, y=yb + 170 * 0.55, s=0.55, E=E, pitch=0.35, yaw=0.15, lw=2.0,
                 armL=dict(el=(-40, -40), wr=(-14, -150), hand_ang=-1.57, curl=0.9, thumb=0.8, flip=False),
                 armR=dict(el=(40, -20), wr=(-12, -110), hand_ang=-1.57, curl=0.9, thumb=0.8, flip=True),
                 legs=dict(mode="run", phase=1.2))
        rig.draw_character(ctx, rig.HUMAN_B, P, LSPOT, t)
    # zombie head & shoulders looking up, bottom foreground (back view)
    P = dict(x=W / 2 - 150, y=1180, s=1.8, view="back", pitch=-0.5, E=rig.expr(), breath=1.5,
             armL=dict(a1=-12, a2=-6, curl=0.5, flip=False), armR=dict(a1=12, a2=6, curl=0.5, flip=True))
    rig.draw_character(ctx, rig.ZOMBIE, P, LSPOT, t)
    world.draw_motes(ctx, t, 30, hexc("e0d8c8"), 0.2, seed=5, drift=(60, 20))


@shot(t_grabz, t_up)
def heli_grab(ctx, t):
    """He stops mid-reach: "A zombie... are you dangerous?"  "Ummm... no?" (head shake, hand behind its head).
    A small smile and a nod, then: "Hey bud, come with me."  "Wait... what?" """
    world.draw_sky(ctx, Cam(hy=1500, d=-1), t, 2.0, east=True, stars=0.8, moon=None)
    soft_dot(ctx, W / 2, -100, 900, hexc("fff4dc"), 0.35)
    q0, q1 = L("r2a")
    n0, n1 = L("r2d")
    g0 = L("r2b")[0]
    t_nod = n1 + 0.35
    hover = ramp(t, t_grabz, t_grabz + 0.5)
    grab = ramp(t, g0 - 0.3, g0 + 0.15)
    huh = ramp(t, L("r2c")[0] - 0.2, L("r2c")[0] + 0.15)
    shake_env = ramp(t, n0 - 0.05, n0 + 0.15) * (1 - ramp(t, n1 + 0.1, n1 + 0.5))
    shake = 0.2 * math.sin((t - n0) * 2 * math.pi * 1.7) * shake_env
    sheep = ramp(t, n0 - 0.15, n0 + 0.45) * (1 - ramp(t, g0 - 0.6, g0 - 0.2))  # hand behind its head
    sad = ramp(t, n0 - 0.3, n0 + 0.1) * (1 - ramp(t, t_nod, t_nod + 0.6))
    hope = ramp(t, t_nod, t_nod + 0.5) * (1 - huh)
    EZ = ZE(t, bi=lerp(0.6, 0.95, max(sad, huh)), bo=lerp(0.25, -0.25, sad) + 0.6 * huh, lid=0.1 * sad, op=0.08, sm=-0.3 * sad + 0.08 * hope,
            gx=lerp(0.55, 0.35, huh), gy=-0.1, glow=0.35, pupil=lerp(0.42, 0.26, huh), low=0.0, tr=0.3 * sad, blinks=False)
    PZ = dict(x=250, y=640, s=2.0, E=EZ, yaw=0.35 + shake, pitch=-0.05 + 0.06 * sad, roll=0.05 * sheep, shrug=0.3 * grab + 0.15 * sheep,
              breath=1.8, breath_T=1.6, legs=dict(mode="stand"),
              armL=dict(el=(lerp(-86, -122, sheep), lerp(120, -46, sheep)), wr=(lerp(-66, -44, sheep), lerp(205, -138, sheep)),
                        hand_ang=lerp(1.7, -0.5, sheep), curl=lerp(0.6, 0.3, sheep), spread=0.3, thumb=0.5, flip=False),
              armR=dict(el=(110, 110), wr=(lerp(80, 150, grab), lerp(150, 40, grab)), hand_ang=-0.3, curl=lerp(0.4, 0.85, grab),
                        thumb=0.8, flip=True))
    if sheep > 0.3:
        PZ["arms_behind"] = ("L",)
    rig.draw_character(ctx, rig.ZOMBIE, PZ, LSPOT, t)
    soft_stroke(ctx, [(650, -20), (646, 400), (642, 1300)], hexc("c8b890"), 1.0, 6)  # rope from above
    oB, wB = mouth("HB", t)
    wary = ramp(t, q0 - 0.4, q0) * (1 - ramp(t, t_nod - 0.1, t_nod + 0.3))
    nod = math.sin(clamp((t - t_nod) / 0.8) * math.pi)
    smile = ramp(t, t_nod - 0.1, t_nod + 0.4) * 0.22 + 0.2 * ramp(t, g0 - 0.2, g0 + 0.3)
    EB = rig.expr(biL=lerp(0.35, 0.65, wary), biR=lerp(0.35, 0.0, wary), bo=lerp(0.2, 0.1, wary), lid=max(0.1 + 0.15 * wary, blink(t, 11)),
                  gx=-0.55, t=t, op=oB * 0.8, wd=wB * 0.3, sm=lerp(0.4, -0.05, wary) * (1 - ramp(t, t_nod - 0.1, t_nod + 0.4)) + smile,
                  low=0.25 * wary)
    gx_ = lerp(lerp(372, 345, hover), 270, grab)  # the reaching hand hovers while he asks, then closes on the shirt
    PB = dict(x=560, y=600, s=2.0, E=EB, yaw=-0.45, pitch=0.05 + 0.13 * nod, roll=0.07 * wary, breath=1.4, legs=dict(mode="stand"),
              armR=dict(el=(96, -50), wr=(28, -150), hand_ang=-1.57, curl=0.9, thumb=0.8, flip=True),
              armL=dict(el=(-120, 90), wr=((gx_ - 560) / 2.0, lerp(lerp(150, 60, hover), 30, grab)), hand_ang=math.pi + 0.3,
                        curl=lerp(0.3, 0.92, grab), thumb=lerp(0.3, 0.9, grab), flip=False))
    rig.draw_character(ctx, rig.HUMAN_B, PB, LSPOT, t)
    if grab > 0.6:  # fabric bunching around the fist
        fx, fy = 560 + PB["armL"]["wr"][0] * 2.0, 600 + PB["armL"]["wr"][1] * 2.0
        for k in range(3):
            soft_stroke(ctx, [(fx - 30 - k * 8, fy + 20 + k * 10), (fx - 8, fy + 8), (fx + 4 - k * 4, fy + 34 + k * 8)],
                        mul(rig.ZOMBIE["shirt"], 0.5), 0.5, 3)


@shot(t_up, r1_)
def heli_up(ctx, t):
    tt = t - t_up
    cam = Cam(x=0, y=0, z=0, d=-1, f=700, hy=1400)
    world.draw_sky(ctx, cam, t, 2.0, east=True, stars=1.0, moon=(130, 560, 55))
    hx, hy_ = W / 2 + 60 - tt * 30, 330 - tt * 20
    world.draw_heli(ctx, hx, hy_, 1.0, t, LSPOT, bank=-0.05 * tt, face=-1)
    door = (hx - 5, hy_ + 40)
    yank = 1 - (1 - clamp(tt / 0.45)) ** 3  # a sudden comic yank, then a steady winch
    rise = 0.28 * yank + 0.72 * ramp(tt, 0.45, 4.6)
    ybot = lerp(1040, door[1] + 70, rise)
    soft_stroke(ctx, [door, (door[0], ybot - 120)], hexc("c8b890"), 1.0, 4)
    if rise < 0.97:
        a = 1 - ramp(rise, 0.85, 0.97)
        ctx.push_group()
        s_ = 0.66
        flail = t * 16
        # the zombie, held against the human's side, legs kicking in surprise
        P2 = dict(x=door[0] + 34, y=ybot - 10, s=s_, E=ZE(t, bi=0.95, bo=0.8, op=0.3, gy=-0.3, gx=-0.3, blinks=False), pitch=-0.15,
                  yaw=-0.3, roll=0.15,
                  armL=dict(el=(-80, 10), wr=(-70, -90), hand_ang=-2.0, curl=0.7, flip=False),
                  armR=dict(el=(80, 60 + 20 * math.sin(flail)), wr=(110, -10 + 30 * math.sin(flail * 1.3)), hand_ang=-0.6, curl=0.3,
                            spread=0.6, flip=True),
                  legs=dict(mode="run", phase=flail))
        rig.draw_character(ctx, rig.ZOMBIE, P2, LSPOT, t)
        # the human: one hand on the rope, the other arm wrapped round the zombie
        P = dict(x=door[0] - 10, y=ybot - 60, s=s_, view="front", E=rig.expr(gy=-0.6, bi=0.3, sm=0.3, t=t), pitch=0.05, yaw=0.15,
                 armL=dict(el=(-70, -80), wr=(-8, -200), hand_ang=-1.57, curl=0.9, flip=False),
                 armR=dict(el=(90, 120), wr=(150, 110), hand_ang=0.2, curl=0.55, thumb=0.6, flip=True), legs=dict(mode="run", phase=0.8))
        rig.draw_character(ctx, rig.HUMAN_B, P, LSPOT, t)
        ctx.pop_group_to_source(); ctx.paint_with_alpha(a)


# ---------------------------------------------------------------- CABIN
i0, i1_ = S("cabin")
t_peek = L("i2")[0] - 0.4
t_hum1 = word_t("i2", "humans") - 0.3
t_who = L("i3")[0] - 0.5
t_zk = L("i4")[0] - 0.4
t_look1 = L("i5")[1] + 0.1
t_how = L("i7")[0] - 0.4
t_look2 = L("i7")[1] + 0.3
t_ha = L("i10")[0] - 0.2
t_react = L("i10b")[0] - 0.35
t_nod = L("i11")[0] - 0.3


def dawn(t):
    return ramp(t, i0 + 15, i1_ + 4) * 0.6


def cab_light(t):
    d = dict(LCAB)
    d["rim"] = mix(LCAB["rim"], hexc("ffd0a0"), dawn(t))
    return d


def zombie_cab(t, s, x, y, extra=None, **kw):
    E = ZE(t, **kw.pop("E", {}))
    P = dict(x=x, y=y, s=s, E=E, breath=1.0, legs=dict(mode="sit"), **arms_hang(t))
    P.update(kw)
    return alive(P, t, "bust", kw.get("alive", 0.8), seed=1.0)


def bench(ctx, y, x0=0, x1=W, light=None):
    """Padded troop bench along the cabin wall."""
    ctx.new_path(); ctx.rectangle(x0, y, x1 - x0, 60)
    rgba(ctx, hexc("2a2e2a")); ctx.fill()
    ctx.new_path(); ctx.rectangle(x0, y, x1 - x0, 14)
    rgba(ctx, hexc("4a5048")); ctx.fill()
    soft_stroke(ctx, [(x0, y + 1), (x1, y + 1)], hexc("ff8a60"), 0.35, 2, smooth=False)


def humans(ctx, t, s=1.9, base_y=830, gxA=0.35, gxB=0.3, yawA=0.18, yawB=0.1, A_kw=None, B_kw=None):
    """Two-shot: A (left, nearer), B (right). Both on a bench facing the zombie (off right of camera)."""
    oA, wA = mouth("HA", t)
    oB, wB = mouth("HB", t)
    A_kw = A_kw or {}
    B_kw = B_kw or {}
    bench(ctx, base_y + 226 * s)
    eB = dict(gx=gxB, t=t, op=oB * 0.8, wd=wB * 0.3, lid=max(0.1, blink(t, 11)))
    eB.update(B_kw.pop("E", {}))
    PB = dict(x=500, y=base_y - 40, s=s * 0.9, E=rig.expr(**eB), yaw=yawB, breath=1.0, **idle(t, 0.6, 5), legs=dict(mode="sit"),
              armL=dict(el=(-84, 150), wr=(-46, 222), hand_ang=1.3, curl=0.55, thumb=0.6, hfs=0.6, flip=False),
              armR=dict(el=(84, 150), wr=(46, 222), hand_ang=1.84, curl=0.55, thumb=0.6, hfs=0.6, flip=True))
    PB.update(B_kw)
    rig.draw_character(ctx, rig.HUMAN_B, PB, cab_light(t), t)
    eA = dict(gx=gxA, t=t, op=oA * 0.8, wd=wA * 0.3, lid=max(0.05, blink(t, 13)))
    eA.update(A_kw.pop("E", {}))
    PA = dict(x=225, y=base_y, s=s, E=rig.expr(**eA), yaw=yawA, breath=1.0, **idle(t, 0.6, 9), legs=dict(mode="sit"),
              armL=dict(el=(-84, 150), wr=(-46, 222), hand_ang=1.3, curl=0.55, thumb=0.6, hfs=0.6, flip=False),
              armR=dict(el=(84, 150), wr=(46, 222), hand_ang=1.84, curl=0.55, thumb=0.6, hfs=0.6, flip=True))
    PA.update(A_kw)
    rig.draw_character(ctx, rig.HUMAN_A, PA, cab_light(t), t)


@shot(i0, t_peek)
def cabin_cower(ctx, t):
    world.draw_cabin(ctx, t, dawn(t), shake=1.5, window_x=560)
    ctx.new_path(); ctx.rectangle(0, 1080, W, 200); rgba(ctx, hexc("1e2020")); ctx.fill()
    soft_stroke(ctx, [(0, 1081), (W, 1081)], hexc("ff8060"), 0.3, 3, smooth=False)
    soft_dot(ctx, 380, 1090, 260, (0, 0, 0), 0.4)
    tr = math.sin(t * 2 * math.pi * 1.1) * 0.5 + math.sin(t * 7.3) * 0.15
    E = dict(lid=1.0, bi=0.85, bo=-0.2, sm=-0.55, wd=0.6, tr=0.6, op=0.05, glow=0.0, blinks=False)
    P = zombie_cab(t, 1.35, 380 + tr * 2, 675, E=E, yaw=-0.5, pitch=0.4, roll=-0.1, shrug=0.6, breath=1.8, breath_T=1.6, alive=0.3,
                   legs=dict(mode="sit_knees"),
                   armL=dict(el=(-96, 10), wr=(-10, -120), hand_ang=-0.5, curl=0.35, spread=0.4, thumb=0.4, flip=True),
                   armR=dict(el=(96, 10), wr=(10, -128), hand_ang=-2.64, curl=0.35, spread=0.4, thumb=0.4, flip=False))
    rig.draw_character(ctx, rig.ZOMBIE, P, cab_light(t), t)
    soft_dot(ctx, 120, 90, 500, hexc("ff4a30"), 0.08)


@shot(t_peek, t_hum1 + 0.6)
def cabin_peek(ctx, t):
    world.draw_cabin(ctx, t, dawn(t), shake=1.0, window_x=560)
    tt = t - t_peek
    lower = ramp(tt, 0.3, 1.6)
    E = dict(lidR=kf(tt, [(0, 1.0), (0.6, 1.0), (1.0, 0.35)]), lidL=kf(tt, [(0, 1.0), (1.2, 1.0), (1.7, 0.1)]), lid=0.0,
             bi=0.8, bo=0.1, gx=-0.6, gy=0.05, sm=-0.3, tr=0.4, glow=0.25, blinks=False)
    bench(ctx, 640 + 226 * 2.0)
    P = zombie_cab(t, 2.0, 400, 640, E=E, yaw=lerp(-0.45, -0.25, lower), pitch=lerp(0.25, 0.05, lower), roll=-0.05, shrug=0.4,
                   breath=1.5, breath_T=2.0,
                   armL=dict(el=(-96, lerp(10, 110, lower)), wr=(lerp(-10, -40, lower), lerp(-120, 40, lower)), hand_ang=-0.9, curl=0.3,
                             spread=0.5, thumb=0.3, flip=False),
                   armR=dict(el=(60, 100), wr=(40, 150), hand_ang=-1.9, curl=0.4, flip=True))
    rig.draw_character(ctx, rig.ZOMBIE, P, cab_light(t), t)


@shot(t_hum1 + 0.6, t_who)
def cabin_humans1(ctx, t):
    world.draw_cabin(ctx, t, dawn(t), shake=0.6, window_x=380)
    humans(ctx, t, A_kw=dict(E=dict(bi=0.35, bo=0.2), roll=0.05), B_kw=dict(E=dict(bi=-0.1, lid=0.2)))


@shot(t_who, t_zk)
def cabin_who(ctx, t):
    world.draw_cabin(ctx, t, dawn(t), shake=0.6, window_x=380)
    lean = ramp(t, t_who, t_who + 0.6)
    humans(ctx, t, A_kw=dict(E=dict(bi=0.35 + 0.15 * lean, bo=0.25), roll=0.07 * lean, pitch=0.05 * lean),
           B_kw=dict(E=dict(bi=0.0, lid=0.15)))


@shot(t_zk, t_look1)
def cabin_dontknow(ctx, t):
    world.draw_cabin(ctx, t, dawn(t), shake=0.6, window_x=560)
    t4, t5 = L("i4")[0], L("i5")[0]
    t_z = word_t("i5", "zombie")
    t_th = word_t("i5", "though")
    down = ramp(t, t4 - 0.1, t4 + 0.3) * (1 - ramp(t, t4 + 0.6, t4 + 1.0))
    self_look = ramp(t, t_z - 0.3, t_z + 0.2) * (1 - ramp(t, t_th - 0.4, t_th))
    shrug = math.sin(clamp((t - t4 - 0.3) / 0.9) * math.pi) * 0.45 + math.sin(clamp((t - t_th + 0.1) / 0.7) * math.pi) * 0.3
    E = dict(bi=0.75, bo=0.1, gx=-0.45 * (1 - max(down, self_look)), gy=0.55 * max(down, self_look), sm=-0.15, glow=0.3,
             lid=0.1 + 0.25 * self_look)
    P = zombie_cab(t, 3.0, 380, 760, E=E, yaw=-0.22, pitch=0.2 * self_look + 0.08 * down, roll=0.05 * ramp(t, t_th - 0.3, t_th + 0.3),
                   shrug=shrug)
    rig.draw_character(ctx, rig.ZOMBIE, P, cab_light(t), t)


@shot(t_look1, t_how)
def cabin_look1(ctx, t):
    world.draw_cabin(ctx, t, dawn(t), shake=0.6, window_x=380)
    # they trade a look ("That's great...": not thrilled it's a zombie, quietly relieved it isn't trying to eat them),
    # then he turns back to it for "...but I also think you are conscious, my guy."
    t6, t6b = L("i6")[0], L("i6b")[0]
    look = ramp(t, t_look1 + 0.1, t_look1 + 0.6) * (1 - ramp(t, t6b - 0.55, t6b - 0.1))
    brow = ramp(t, t_look1 + 0.5, t_look1 + 0.9) * (1 - ramp(t, t6b - 0.3, t6b + 0.6) * 0.7)
    wry = ramp(t, t6 - 0.2, t6 + 0.3) * (1 - ramp(t, t6b - 0.4, t6b))
    warm = ramp(t, word_t("i6b", "guy") - 0.4, word_t("i6b", "guy") + 0.2)
    exhale = math.sin(clamp((t - t6 - 0.2) / 0.9) * math.pi)
    humans(ctx, t, gxA=lerp(0.35, 0.8, look), gxB=lerp(0.3, -0.85, look), yawA=lerp(0.18, 0.5, look), yawB=lerp(0.1, -0.45, look),
           A_kw=dict(E=dict(bi=0.2 + 0.55 * brow, bo=0.2 + 0.45 * brow, press=0.45 * wry, sm=-0.1 * wry + 0.15 * warm),
                     pitch=0.05 * exhale, shrug=-0.15 * exhale),
           B_kw=dict(E=dict(biL=0.15 + 0.75 * brow, biR=0.1 + 0.25 * brow, bo=0.1 + 0.4 * brow, sm=0.18 * wry + 0.3 * warm),
                     roll=0.06 * wry, pitch=0.05 * math.sin(clamp((t - word_t("i6b", "guy") + 0.3) / 0.7) * math.pi)))


@shot(t_how, t_look2)
def cabin_how(ctx, t):
    world.draw_cabin(ctx, t, dawn(t), shake=0.5, window_x=560)
    w_ = ramp(t, t_how, t_how + 0.5)
    E = dict(bi=0.6 + 0.3 * w_, bo=0.5 * w_, lid=0.0, gx=-0.4, gy=-0.05, glow=0.4, pupil=0.52, low=0.0)
    P = zombie_cab(t, 3.3, 380, 770, E=E, yaw=-0.2, roll=0.08 * w_, pitch=-0.03)
    rig.draw_character(ctx, rig.ZOMBIE, P, cab_light(t), t)


@shot(t_look2, t_ha)
def cabin_look2(ctx, t):
    world.draw_cabin(ctx, t, dawn(t), shake=0.6, window_x=380)
    t8, t9 = L("i8")[0], L("i9")[0]
    look = ramp(t, t_look2, t_look2 + 0.5) * (1 - ramp(t, t8 - 0.6, t8 - 0.1))
    brow = ramp(t, t_look2 + 0.4, t_look2 + 0.8) * (1 - ramp(t, t8, t8 + 0.8) * 0.7)
    chest = ramp(t, word_t("i8", "feel") - 0.3, word_t("i8", "feel") + 0.3) * (1 - ramp(t, t9, t9 + 0.6))
    nodB = math.sin(clamp((t - word_t("i9", "weight")) / 0.9) * math.pi) * 0.12
    offer = ramp(t, t9, t9 + 0.5)
    humans(ctx, t, gxA=lerp(0.35, 0.8, look), gxB=lerp(0.3, -0.85, look), yawA=lerp(0.18, 0.5, look), yawB=lerp(0.1, -0.45, look),
           A_kw=dict(E=dict(bi=0.3 + 0.5 * brow, bo=0.2 + 0.5 * brow, sm=0.1 * (1 - look)),
                     armR=dict(el=(lerp(84, 74, chest), lerp(150, 120, chest)), wr=(lerp(46, 18, chest), lerp(222, 40, chest)),
                               hand_ang=lerp(1.5, -2.6, chest), curl=0.25, flip=True)),
           B_kw=dict(E=dict(bi=0.2 + 0.5 * brow, bo=0.1 + 0.5 * brow, sm=0.15), pitch=nodB,
                     armR=dict(el=(lerp(84, 88, offer), lerp(150, 150, offer)), wr=(lerp(46, 30, offer), lerp(222, 96, offer)),
                               hand_ang=lerp(1.84, 0.35, offer), hfs=lerp(0.6, 0.55, offer), curl=lerp(0.55, 0.3, offer), spread=0.35, thumb=0.5,
                               palm=offer > 0.5, flip=True)))


@shot(t_ha, t_react)
def cabin_ha(ctx, t):
    world.draw_cabin(ctx, t, dawn(t), shake=0.5, window_x=260)
    o, w = mouth("HA", t)
    E = rig.expr(bi=0.45, bo=0.1, gx=0.35, op=o * 0.8, wd=w * 0.3, sm=0.15, lid=max(0.1, blink(t, 13)), t=t, low=0.2)
    P = dict(x=330, y=650, s=2.6, E=E, yaw=0.2, roll=0.06, breath=1.0, **idle(t, 0.5, 9))
    rig.draw_character(ctx, rig.HUMAN_A, P, cab_light(t), t)


@shot(t_react, t_nod)
def cabin_react(ctx, t):
    world.draw_cabin(ctx, t, dawn(t), shake=0.5, window_x=560)
    tt = t - t_react
    ts = tear_state(t, L("i10b")[1] + 0.05, 2.4)
    tears = [(1, ts[0], ts[1])] if ts else []
    resolve = ramp(t, word_t("i10b", "want") - 0.2, word_t("i10b", "want") + 0.4)
    E = dict(bi=lerp(0.85, 0.55, resolve), bo=lerp(-0.05, 0.1, resolve), gx=-0.4, lid=0.12, press=0.5 * ramp(t, L("i10b")[1], L("i10b")[1] + 0.4),
             tr=0.5, sm=lerp(-0.2, 0.0, resolve), glow=lerp(0.5, 0.75, resolve), tears=tears, low=0.25)
    P = zombie_cab(t, 3.4, 380, 780, E=E, yaw=-0.2, pitch=0.02, breath=1.5, breath_T=2.6)
    rig.draw_character(ctx, rig.ZOMBIE, P, cab_light(t), t)


@shot(t_nod, i1_)
def cabin_nod(ctx, t):
    world.draw_cabin(ctx, t, dawn(t), shake=0.4, window_x=560)
    tn = word_t("i11", "nodded") - 0.1
    nod = math.sin(clamp((t - tn) / 1.4) * math.pi)
    sm = 0.35 * ramp(t, tn + 0.6, tn + 1.6)
    E = dict(bi=0.45, gx=-0.4, gy=0.45 * nod, lid=0.15 + 0.4 * nod, sm=sm, glow=0.55)
    P = zombie_cab(t, 3.2, 380, 770, E=E, yaw=-0.2, pitch=0.62 * nod, breath=1.0)
    rig.draw_character(ctx, rig.ZOMBIE, P, cab_light(t), t)


# ---------------------------------------------------------------- END
e0, e1_ = S("end")


@shot(e0, e1_ + 0.01)
def end_dawn(ctx, t):
    """Dawn through polluted air: a dim, smog-veiled sun rising behind the fortress."""
    u = (t - e0) / (e1_ - e0)
    th = word_t("e2", "heaven", 1) - 0.3
    cam = Cam(x=0, y=8, z=60 + u * 20, d=1, f=720, hy=760)
    ph = lerp(2.3, 2.7, ramp(t, e0, th + 0.5))
    ext(ctx, t, cam, ph, horde=False, fire=False, sun=False)
    lift = ramp(t, th, th + 2.5)
    sunp = cam.p(0, 80 + 12 * ramp(t, e0, e1_), WALL + 10)
    smog = hexc("8a7462")
    g = cairo.LinearGradient(0, 0, 0, cam.hy + 40)  # brown haze over the whole sky
    g.add_color_stop_rgba(0, *smog, 0.28)
    g.add_color_stop_rgba(1, *mix(smog, hexc("c0a080"), 0.4), 0.45)
    ctx.set_source(g); ctx.rectangle(0, 0, W, cam.hy + 40); ctx.fill()
    soft_dot(ctx, *sunp, 260 + 120 * lift, hexc("e8b070"), 0.18 + 0.12 * lift)
    ctx.new_path(); ctx.arc(sunp[0], sunp[1], 46, 0, 2 * math.pi)
    rgba(ctx, mix(hexc("f0c890"), hexc("fff0d0"), lift), 0.5 + 0.2 * lift); ctx.fill()
    for q in range(5):  # smog bands drifting across the sun
        y = sunp[1] - 70 + q * 34
        x = (t * (6 + q * 2) + q * 170) % (W + 400) - 200
        ctx.save(); ctx.translate(x, y); ctx.scale(7, 1)
        gg = cairo.RadialGradient(0, 0, 0, 0, 0, 22)
        gg.add_color_stop_rgba(0, *mul(smog, 0.8), 0.45)
        gg.add_color_stop_rgba(1, *mul(smog, 0.8), 0)
        ctx.set_source(gg); ctx.arc(0, 0, 22, 0, 2 * math.pi); ctx.fill()
        ctx.restore()
    for k in range(10):  # faint shafts struggling through the haze
        a = math.pi + (k + 0.5) * math.pi / 10
        ctx.new_path(); ctx.move_to(*sunp)
        ctx.line_to(sunp[0] + math.cos(a - 0.03) * 1500, sunp[1] + math.sin(a - 0.03) * 1500)
        ctx.line_to(sunp[0] + math.cos(a + 0.03) * 1500, sunp[1] + math.sin(a + 0.03) * 1500)
        ctx.close_path()
        rgba(ctx, hexc("f0d8b0"), 0.015 + 0.03 * lift); ctx.fill()
    for i in range(4):  # smoke still rising from the battlefield
        for k in range(5):
            age = (t * 0.12 + i * 0.27 + k / 5) % 1.0
            p = cam.p(-60 + i * 40 + age * 12, age * 60, WALL - 40 - i * 15)
            soft_dot(ctx, p[0], p[1], 20 + age * 70, hexc("5a5048"), 0.25 * (1 - age))
    hx = lerp(W / 2 + 260, W / 2 - 40, ease(u))
    hy_ = lerp(380, cam.hy - 40, ease(u))
    world.draw_heli(ctx, hx, hy_, lerp(0.3, 0.06, ease(u)), t, LT(dir=(0, -1), rim=hexc("e8c090"), shadow=hexc("2a2030"),
                    amb=hexc("7a6a6a"), amb_k=0.3), bank=-0.08, face=-1)
    world.draw_motes(ctx, t, 30, hexc("d8c8b0"), 0.15, seed=9, drift=(8, -10))


SHOTS.sort(key=lambda s: s[0])


def render_frame(ctx, t):
    for t0, t1, fn in SHOTS:
        if t0 <= t < t1:
            fn(ctx, t)
            return fn.__name__
    SHOTS[-1][2](ctx, t)
    return SHOTS[-1][2].__name__
