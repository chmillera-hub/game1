"""pigeon.py -- PLUMP GREY PIGEONS (S6/S7/S8): the one "ordinary" animal, the same in every world.

Blue-grey, round-breasted, iridescent green-and-purple necks, two dark wing bars, a dark-tipped
tail and coral feet. They peck, hop, flap, fly in, bob their heads as they walk -- and do the
SYNCHRONIZED HEAD SWIVEL gag of S6 (pose.look, -1 beak to screen-left .. +1 to screen-right,
0 beak at the camera; a flock passes one shared value to every bird).

    from film.lib import characters as ch
    rig = ch.draw_pigeon(cr, x, ground_y, 0.9, ch.PigeonPose(facing=-1, peck=u), light, t)

    flock = ch.PigeonFlock(n=7, x_range=(560, 1350), y_range=(930, 975), seed=3, scale=0.9,
                           crumbs=ch.gnome_crumb_landings(t_toss, rig_gnome, 960), arrivals=[(3.0, -1)])
    flock.draw(cr, t, light, look=swivel(t))      # look=None: each bird minds its own business

Scale 1.0: ground -> top of the head = PIGEON_HEIGHT = 42 px (profile, standing). Anchor (x, y) =
the ground point between the feet. Drawn in profile (facing +1 right / -1 left); only the head
turns in 3D-lite. Cheap by design (a flock of ten is a few ms): one union per material, a small
custom eye below close-up size and the shared base.eye() in close-ups.
"""

import bisect
import heapq
import math
import random
from dataclasses import dataclass, field, replace

from .. import core
from ..core import clamp, lerp, smooth
from . import base as B
from .base import Mat, Path

TAU = math.tau

__all__ = ["PigeonPose", "PigeonRig", "PigeonFlock", "draw_pigeon", "pigeon_stride", "PIGEON_HEIGHT",
           "PIGEON_COLORS", "pigeon_mats"]

PIGEON_HEIGHT = 42.0
PIGEON_LINE = B.LINE
STRIDE = 13.0               # px per walk cycle (two quick steps)
HEAD_R = 7.2

PIGEON_COLORS = {
    "body": "#8F98A8",       # blue-grey
    "back": "#A3ABB9",       # paler mantle
    "wing": "#9AA2B1",
    "bar": "#3F4552",        # the two dark wing bars, tail band, primaries
    "head": "#7C8597",
    "neck_g": "#4E9B72",     # iridescent green
    "neck_p": "#8C5AA2",     # iridescent purple
    "beak": "#3B3539",
    "cere": "#E9E5DF",       # the white wattle at the base of the beak
    "feet": "#E36F69",       # coral
    "eye": "#E5832C",        # orange iris
}

_MATS = {}


def pigeon_mats():
    if not _MATS:
        C = PIGEON_COLORS
        _MATS.update({
            "body": Mat.of(C["body"], shadow_k=1.05),
            "back": Mat.of(C["back"]),
            "wing": Mat.of(C["wing"], shadow_k=1.05),
            "bar": Mat.of(C["bar"]),
            "head": Mat.of(C["head"]),
            "beak": Mat.of(C["beak"], sheen=0.4),
            "cere": Mat.of(C["cere"]),
            "feet": Mat.of(C["feet"], sss=0.3),
        })
    return _MATS


@dataclass
class PigeonPose:
    """facing   +1 right / -1 left (profile)
    walk     0..1 walking; phase = cycle phase (pigeon_walk_phase or the flock does it)
    peck     0..1 one peck (0 up .. 0.5 beak on the ground .. 1 up again)
    hop      0..1 progress of a little hop
    flap     0..1 wing flapping (with fly=0 a "takeoff-lite": a few beats, a small lift)
    fly      0..1 airborne pose (legs tucked, body level, wings beating); lift = height above
             the ground in px (the contact shadow stays on the ground)
    look     head swivel in SCREEN terms: -1 beak to screen-left, 0 at the camera, +1 screen-
             right; None = beak forward (the way it faces)
    tilt     head cock (rad); puff 0..1 chest puffed (cooing); blink None = auto
    """
    facing: int = 1
    walk: float = 0.0
    phase: float = 0.0
    peck: float = 0.0
    hop: float = 0.0
    flap: float = 0.0
    fly: float = 0.0
    lift: float = 0.0
    look: float = None
    tilt: float = 0.0
    puff: float = 0.0
    blink: float = None
    shadow: bool = True
    seed: int = 0

    def with_(self, **kw):
        return replace(self, **kw)


@dataclass
class PigeonRig:
    head: tuple = (0.0, 0.0)
    beak: tuple = (0.0, 0.0)
    feet: tuple = (0.0, 0.0)
    body: tuple = (0.0, 0.0)
    scale: float = 1.0
    facing: float = 1.0


def pigeon_stride(scale=1.0):
    """Screen px travelled per walk cycle."""
    return STRIDE * scale


def _shape(q, pts, mat, size, lw=None, shade=True, **kw):
    """A smooth closed shape with a dilated outline; house shading or (shade=False) one flat
    lit fill -- the pigeon's small parts are a few px wide."""
    cr = q["cr"]
    lw = q["lw"] if lw is None else lw
    sh, so = B.smooth_paths(cr, pts, lw, 0.9)
    if shade:
        kw.setdefault("bounce", 0.0)
        return sh, B.shade(cr, sh, mat, q["light"], lw, outline=so, size=size, **kw)
    p = B.palette(q["light"], mat)
    so.add(cr)
    core.src(cr, p.line)
    cr.fill()
    sh.add(cr)
    core.src(cr, p.lit)
    cr.fill()
    return sh, p


def _ell(cx, cy, rx, ry, ang=0.0, n=12):
    ca, sa = math.cos(ang), math.sin(ang)
    return [(cx + math.cos(TAU * i / n) * rx * ca - math.sin(TAU * i / n) * ry * sa,
             cy + math.cos(TAU * i / n) * rx * sa + math.sin(TAU * i / n) * ry * ca) for i in range(n)]


def draw_pigeon(cr, x, y, scale=1.0, pose=None, light=None, t=0.0, detail=None):
    """One pigeon, feet at (x, y). Returns a PigeonRig (caller coordinates)."""
    pose = pose or PigeonPose()
    light = light or B.LIGHTS["neutral"]
    dev = scale * B.device_scale(cr)
    if detail is None:
        detail = 2 if dev >= 1.8 else 1 if dev >= 0.7 else 0
    M = pigeon_mats()
    lw = max(PIGEON_LINE * 0.8, B.MIN_LINE_PX / max(dev, 1e-6))
    fs = 1.0 if pose.facing >= 0 else -1.0
    q = {"cr": cr, "light": light, "lw": lw}
    seed = pose.seed

    # ---- pose -> body/head geometry (local px, facing right, y up = negative)
    fly = clamp(pose.fly)
    hop = clamp(pose.hop)
    hop_y = -13.0 * math.sin(math.pi * hop)
    flap = clamp(max(pose.flap, fly))
    lift = pose.lift + hop_y * -1.0 if fly <= 0 else pose.lift
    br = B.breathing(t, 0.45, seed)
    walk = clamp(pose.walk)
    ph = pose.phase % 1.0
    pk = clamp(pose.peck)
    peck = math.sin(math.pi * pk) ** 1.5 if pk > 0 else 0.0
    pitch = -0.16 + 0.42 * peck + 0.12 * fly - 0.08 * pose.puff        # + nose-down
    body_dy = -lift + 1.2 * walk * abs(math.sin(TAU * ph))             # (lift >= 0 = up)
    puff = clamp(pose.puff + 0.08 * (br + 1.0))

    cr.save()
    cr.translate(x, y)
    cr.scale(scale * fs, scale)

    if pose.shadow:
        B.contact_shadow(cr, 0.0, 0.5, 15.0 * (1.0 - min(0.6, pose.lift / 120.0)), 3.6, alpha=0.3 * (1.0 - min(0.7, pose.lift / 150.0)))

    cr.translate(0.0, body_dy)
    # head bob while walking: the head holds still, then thrusts forward (a smoothed sawtooth)
    saw = (ph * 2.0) % 1.0
    thrust = (smooth(saw / 0.35) if saw < 0.35 else 1.0 - smooth((saw - 0.35) / 0.65)) * 2.0 - 1.0
    hx = 12.0 + 3.6 * walk * thrust * (1.0 - fly) + 10.0 * peck + 1.0 * puff
    hy = -34.5 + 28.0 * peck - 1.5 * puff + 0.4 * br
    if fly > 0:
        hx, hy = lerp(hx, 15.0, fly), lerp(hy, -27.0, fly)
    hc = (hx, hy)
    body_c = (0.0, -18.5)
    ca, sa = math.cos(pitch), math.sin(pitch)

    def BP(px, py):          # body-relative point, pitched about the body center
        dx, dy = px - body_c[0], py - body_c[1]
        return (body_c[0] + dx * ca - dy * sa, body_c[1] + dx * sa + dy * ca)

    # ---- legs (behind the body; tucked in flight / at the top of a hop)
    tuck = max(fly, 0.8 * math.sin(math.pi * hop))
    legs = []
    for k, side in enumerate((-1.0, 1.0)):
        u = (ph + 0.5 * k) % 1.0
        stp = math.sin(TAU * u) * 4.5 * walk
        up = max(0.0, math.cos(TAU * u)) * 3.5 * walk
        top = BP(side * 1.5 + 1.0, -9.0)
        foot = (side * 1.8 + stp, -up + lift - body_dy * 0.0 - (body_dy - 1.2 * walk * abs(math.sin(TAU * ph))))
        if tuck > 0:
            foot = (lerp(foot[0], top[0] - 4.0, tuck), lerp(foot[1], top[1] + 3.5, tuck))
        legs.append((top, foot))
    fp = B.palette(light, M["feet"])
    lwl = lw * 0.8
    for pass_ in (0, 1):
        cr.new_path()
        for top, foot in legs:
            d = lwl * 2 if pass_ == 0 else 0.0
            core.tapered(cr, [top, foot], 3.0 + d, 2.2 + d)
            if tuck < 0.6:
                for tx, ty in ((5.0, 0.0), (3.4, -0.4), (-3.0, -0.6)):     # three toes forward, one back
                    core.tapered(cr, [foot, (foot[0] + tx, foot[1] + ty)], 1.9 + d, 1.0 + d)
        core.src(cr, fp.line if pass_ == 0 else fp.lit)
        cr.fill()

    # ---- the far wing when the wings are open (behind the body)
    wing_up = flap * (0.55 + 0.45 * math.sin(t * TAU * (7.5 if fly > 0 else 6.0) + seed))
    if flap > 0.05:
        _wing(q, M, BP, wing_up * 1.08 + 0.1, far=True, detail=detail)

    # ---- tail: a fan with a dark band
    tail_spread = 1.0 + 0.6 * fly
    t0, t1 = BP(-13.0, -18.0), BP(-31.0, -14.0 + 2.0 * fly)
    tail = [BP(-12.0, -21.5), (t1[0] - 1.5, t1[1] - 4.8 * tail_spread), (t1[0] + 0.5, t1[1] + 0.5),
            (t1[0] - 1.0, t1[1] + 4.2 * tail_spread), BP(-12.5, -14.5)]
    tsh, tp = _shape(q, tail, M["wing"], size=8, rim=0.6)
    if detail >= 1:
        cr.save()
        tsh.add(cr)
        cr.clip()
        bp_ = B.palette(light, M["bar"])
        core.src(cr, bp_.lit)
        dx, dy = t1[0] - t0[0], t1[1] - t0[1]
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        bx, by = t0[0] + dx * 0.78, t0[1] + dy * 0.78
        core.polygon(cr, [(bx + nx * 9, by + ny * 9), (bx - nx * 9, by - ny * 9), (bx - nx * 9 + dx * 0.4, by - ny * 9 + dy * 0.4),
                          (bx + nx * 9 + dx * 0.4, by + ny * 9 + dy * 0.4)])
        cr.fill()
        cr.restore()

    # ---- body + neck + head: ONE union (the swivelling head stays attached)
    body = _ell(*BP(0.0, -18.5), 16.6 + 0.8 * puff, 11.6 + 1.2 * puff, pitch, 14)
    body += [BP(-14.0, -16.5), BP(-13.0, -21.0)]
    neck = []
    for k in range(8):                 # a fat neck from the shoulders to under the head
        a = TAU * k / 8
        neck.append(BP(7.0 + math.cos(a) * 7.5, -23.0 + math.sin(a) * 7.5))
        neck.append((hc[0] - 1.5 + math.cos(a) * (6.2 + 1.8 * puff), hc[1] + 3.5 + math.sin(a) * (6.0 + 1.5 * puff)))
    head = _ell(hc[0], hc[1], HEAD_R, HEAD_R * 0.97, 0.0, 12)
    hb = core.convex_hull(body)
    hn = core.convex_hull(neck)
    hh = head
    pal = B.palette(light, M["body"])
    cr.new_path()
    for h in (hb, hn, hh):
        core.smooth_closed(cr, B.offset_closed(h, lw), 0.9)
    core.src(cr, pal.line)
    cr.fill()
    for h in (hb, hn, hh):
        core.smooth_closed(cr, h, 0.9)
    bodyp = Path(cr)
    B.shade(cr, bodyp, M["body"], light, lw, outline=False, size=24, bounce=0.0)
    # the iridescent neck: green above, purple below, shimmering as the head moves
    if detail >= 1:
        cr.save()
        bodyp.add(cr)
        cr.clip()
        shim = 0.5 + 0.5 * math.sin(t * 2.3 + hc[0] * 0.4 + seed)
        g = core.mix(PIGEON_COLORS["neck_g"], PIGEON_COLORS["neck_p"], 0.25 * shim)
        pc = core.mix(PIGEON_COLORS["neck_p"], PIGEON_COLORS["neck_g"], 0.2 * (1.0 - shim))
        pg = B.palette(light, Mat.of(core.rgb2hex(g)))
        pp = B.palette(light, Mat.of(core.rgb2hex(pc)))
        nb = BP(6.5, -23.0)
        core.src(cr, pp.lit, 0.9)
        core.ellipse(cr, (nb[0] + hc[0]) * 0.5 + 0.5, (nb[1] + hc[1]) * 0.5 + 4.5, 8.0, 6.0, -0.9)
        cr.fill()
        core.src(cr, pg.lit, 0.9)
        core.ellipse(cr, (nb[0] + hc[0]) * 0.5 + 1.5, (nb[1] + hc[1]) * 0.5 - 0.5, 6.5, 5.0, -0.9)
        cr.fill()
        # the head is a deeper grey
        hp = B.palette(light, M["head"])
        core.src(cr, hp.lit)
        core.ellipse(cr, hc[0], hc[1] - 0.8, HEAD_R - 0.6, HEAD_R - 1.0)
        cr.fill()
        cr.restore()

    # ---- the folded near wing with its two dark bars (or the open near wing)
    if flap > 0.05:
        _wing(q, M, BP, wing_up, far=False, detail=detail)
    else:
        wing = [BP(7.0, -24.5), BP(1.0, -27.8), BP(-9.0, -26.8), BP(-19.0, -22.5), BP(-28.5, -17.5),
                BP(-22.0, -15.2), BP(-9.0, -15.0), BP(2.0, -17.5)]
        wsh, wp = _shape(q, wing, M["wing"], size=12, rim=0.7)
        if detail >= 1:
            cr.save()
            wsh.add(cr)
            cr.clip()
            bp_ = B.palette(light, M["bar"])
            cr.new_path()
            for (ax, ay, bx, by) in ((-3.0, -27.0, -7.5, -15.0), (-9.0, -26.0, -13.5, -15.0)):
                a0, b0 = BP(ax, ay), BP(bx, by)
                core.tapered(cr, [a0, b0], 2.6, 2.2)
            core.polygon(cr, [BP(-19.0, -23.0), BP(-30.0, -17.5), BP(-22.0, -15.0), BP(-16.0, -16.0)])   # dark primaries
            core.src(cr, bp_.lit)
            cr.fill()
            cr.restore()

    # ---- head details: beak (+ cere), eye(s) -- the head swivels in 3D-lite
    look = (fs if pose.look is None else clamp(pose.look)) * fs        # -> local terms (+1 forward)
    phi = (1.0 - look) * 0.5 * math.pi                                  # 0 beak forward .. pi back
    tilt = pose.tilt + 0.1 * math.sin(t * 0.9 + seed) * (1.0 - walk)
    head_rig = _head_details(q, M, hc, phi, tilt, pose, t, detail, fs)

    rig = PigeonRig(scale=scale, facing=fs)
    m = cr.get_matrix()
    cr.restore()
    inv = cr.get_matrix()
    inv.invert()

    def C(p):
        dx, dy = m.transform_point(p[0], p[1])
        return inv.transform_point(dx, dy)

    rig.head = C(hc)
    rig.beak = C(head_rig)
    rig.feet = C((0.0, -body_dy))
    rig.body = C(body_c)
    return rig


def _wing(q, M, BP, up, far, detail):
    """An open wing seen from the side: raised from the shoulder by `up` (0 folded .. 1 high)."""
    cr = q["cr"]
    ang = -0.35 - 1.5 * up                     # rad from pointing back, upward
    sx, sy = BP(4.0, -24.0)
    L = 30.0
    tip = (sx + math.cos(math.pi + ang * -1.0) * 0.0 - L * math.cos(ang) * 0.85, sy + L * math.sin(ang))
    mid = (sx - L * 0.5 * math.cos(ang * 0.8), sy + L * 0.55 * math.sin(ang * 0.8))
    pts = [(sx + 3.0, sy + 2.0), (sx - 1.0, sy - 3.0), mid, tip, (tip[0] + 6.0, tip[1] + 7.0),
           (mid[0] + 8.0, mid[1] + 8.0), (sx + 4.0, sy + 6.0)]
    off = (-3.0, -2.0) if far else (0.0, 0.0)
    pts = [(p[0] + off[0], p[1] + off[1]) for p in pts]
    mat = M["bar"] if far else M["wing"]
    sh, p = _shape(q, pts, mat, size=10, rim=0.5, shade=not far)
    if not far and detail >= 1:
        bp_ = B.palette(q["light"], M["bar"])
        cr.save()
        sh.add(cr)
        cr.clip()
        core.src(cr, bp_.lit)
        core.polygon(cr, [mid, tip, (tip[0] + 7.0, tip[1] + 8.0), (mid[0] + 9.0, mid[1] + 9.0)])
        cr.fill()
        cr.restore()


def _head_details(q, M, hc, phi, tilt, pose, t, detail, fs):
    """Beak and eyes on the swivelling head. phi: beak direction in the x-z plane (0 = forward
    in local terms, pi/2 = at the camera, pi = back). Returns the beak tip (local)."""
    cr, light, lw = q["cr"], q["light"], q["lw"]
    cp, sp = math.cos(phi), math.sin(phi)
    ct, st = math.cos(tilt), math.sin(tilt)

    def H(dx, dy, dz):      # head-local (x forward along the beak, y down, z left of the beak)
        # yaw by phi about the vertical, then a little roll (tilt)
        X = dx * cp - dz * sp
        Z = dx * sp + dz * cp
        Y = dy
        X, Y = X * ct - Y * st, X * st + Y * ct
        return (hc[0] + X, hc[1] + Y), Z

    # beak: a short tapered wedge + the white cere at its base
    base, zb = H(6.0, 0.3, 0.0)
    tipp, zt = H(12.5, 1.6, 0.0)
    bp = B.palette(light, M["beak"])
    cpal = B.palette(light, M["cere"])
    blen = math.hypot(tipp[0] - base[0], tipp[1] - base[1])
    front = sp > 0.85                           # beak pointing at the camera: foreshortened
    lwb = lw * 0.7
    cr.new_path()
    if blen > 2.0:
        core.tapered(cr, [base, tipp], 4.4 + 2 * lwb, 1.4 + 2 * lwb)
    else:
        core.circle(cr, base[0], base[1] + 1.5, 2.4 + lwb)
    core.src(cr, bp.line)
    cr.fill()
    if blen > 2.0:
        core.tapered(cr, [base, tipp], 4.4, 1.4)
    else:
        core.circle(cr, base[0], base[1] + 1.5, 2.4)
    core.src(cr, bp.lit)
    cr.fill()
    cer, _ = H(6.4, -1.2, 0.0)
    core.src(cr, cpal.lit)
    core.ellipse(cr, cer[0], cer[1], 2.2 if not front else 2.6, 1.5)
    cr.fill()
    # eyes: on the sides of the head, ~78 degrees off the beak
    blink = B.auto_blink(t, pose.seed * 7 + 41, interval=(1.8, 4.0)) if pose.blink is None else pose.blink
    for s in (-1.0, 1.0):
        ep, ez = H(2.6, -1.8, s * 5.0)
        if ez < 0.8:
            continue
        fore = clamp(ez / 5.0, 0.35, 1.0)
        if detail >= 2:
            B.eye(cr, ep[0], ep[1], 2.3 * fore, 2.4, light, lw * 0.5, look=(0.0, 0.0), lid=0.12, lid_bot=0.08,
                  blink=blink, iris=PIGEON_COLORS["eye"], pupil="#1d120c", pupil_size=0.45, iris_size=0.9,
                  skin=PIGEON_COLORS["head"], crease=0.0, lash=0.5)
        else:                                     # a few px: an orange ring, a pupil, a glint
            if blink > 0.6:
                core.src(cr, B.palette(light, M["head"]).line)
                core.ellipse(cr, ep[0], ep[1], 2.2 * fore, 0.6)
                cr.fill()
                continue
            core.src(cr, B.palette(light, M["head"]).line)
            core.ellipse(cr, ep[0], ep[1], 2.5 * fore + 0.4, 2.6)
            cr.fill()
            core.src(cr, PIGEON_COLORS["eye"])
            core.ellipse(cr, ep[0], ep[1], 2.0 * fore, 2.1)
            cr.fill()
            core.src(cr, "#1d120c")
            core.ellipse(cr, ep[0] + 0.2 * fs, ep[1], 1.0 * fore, 1.1)
            cr.fill()
            cr.set_source_rgba(1, 1, 1, 0.9)
            core.circle(cr, ep[0] - 0.5, ep[1] - 0.7, 0.45)
            cr.fill()
    return tipp


# ----------------------------------------------------------------------------------------
# the flock: deterministic schedules (pure functions of t), crumbs, arrivals, the swivel gag
# ----------------------------------------------------------------------------------------

class PigeonFlock:
    """N pigeons placed deterministically on a ground band that mind their own business --
    idling, bobbing about, pecking the ground, hopping, the odd flap -- and walk to crumbs as
    they land (first come, first served) and peck them up. More can fly in.

    x_range, y_range  the ground band (caller px); y is the feet line, farther (smaller y) birds
                      are drawn first and a touch smaller (depth_scale per px of y)
    crumbs            [(x, t_land)] or [(x, t_land, y)] -- e.g. gnome_crumb_landings(...)
    arrivals          [(t, side)]: extra birds flying in at t from side -1 (left) / +1 (right)
    t_end             schedules are built up to this time (local scene seconds)
    The whole schedule is built once in __init__; draw(cr, t, ...) is a pure function of t."""

    def __init__(self, n=6, x_range=(600.0, 1300.0), y_range=(900.0, 960.0), seed=1, scale=1.0,
                 crumbs=(), arrivals=(), t_end=40.0, depth_scale=0.0015, speed=50.0, reach=380.0):
        self.scale = scale
        self.depth_scale = depth_scale
        self.y_range = y_range
        rng = random.Random(seed)
        self.crumbs = []
        for c in crumbs:
            cx, ct = c[0], c[1]
            cy = c[2] if len(c) > 2 else rng.uniform(*y_range)
            self.crumbs.append({"x": cx, "y": cy, "t": ct, "by": None, "eaten": None})
        self.birds = []
        x0, x1 = x_range
        for i in range(n + len(arrivals)):
            arr = arrivals[i - n] if i >= n else None
            b = {"segs": [], "seed": seed * 31 + i, "arrive": arr}
            self.birds.append(b)
        # event-driven scheduling so crumb claims are first come, first served
        heap = []
        for i, b in enumerate(self.birds):
            r = random.Random(b["seed"])
            y = r.uniform(*y_range)
            if b["arrive"] is None:
                x = r.uniform(x0, x1)
                f = 1 if r.random() < 0.5 else -1
                b.update(x=x, y=y, f=f)
                heapq.heappush(heap, (0.0, i))
            else:
                ta, side = b["arrive"]
                lx = r.uniform(x0 + 0.15 * (x1 - x0), x1 - 0.15 * (x1 - x0))
                sx = (x0 - 260.0) if side < 0 else (x1 + 260.0)
                f = 1 if lx > sx else -1
                dur = 1.25 + 0.3 * r.random()
                b["segs"].append((ta, ta + dur, "fly", sx, y - 330.0 * scale, lx, y, f))
                b["segs"].append((ta + dur, ta + dur + 0.45, "land", lx, y, lx, y, f))
                b.update(x=lx, y=y, f=f)
                heapq.heappush(heap, (ta + dur + 0.45, i))
        while heap:
            tt, i = heapq.heappop(heap)
            if tt >= t_end:
                continue
            b = self.birds[i]
            r = random.Random(b["seed"] * 7919 + int(tt * 100))
            nt = self._decide(b, tt, r, speed * scale, reach * scale, x0, x1)
            heapq.heappush(heap, (nt, i))
        for b in self.birds:
            b["t0s"] = [s[0] for s in b["segs"]]

    def _decide(self, b, tt, r, speed, reach, x0, x1):
        x, y, f = b["x"], b["y"], b["f"]
        best = None
        for c in self.crumbs:                       # crumbs already landed (or about to) and free
            if c["by"] is None and c["t"] <= tt + 0.5:
                d = abs(c["x"] - x) + 2.0 * abs(c["y"] - y)
                if d < reach and (best is None or d < best[0]):
                    best = (d, c)
        if best is not None:
            c = best[1]
            c["by"] = id(b)
            f = 1 if c["x"] >= x else -1
            tx = c["x"] - f * 24.0 * self.scale       # stop so the beak reaches the crumb
            dist = abs(tx - x) + abs(c["y"] - y)
            dur = max(0.25, dist / speed)
            b["segs"].append((tt, tt + dur, "walk", x, y, tx, c["y"], f))
            npk = 2 + r.randint(0, 2)
            t1 = tt + dur + npk * 0.42
            b["segs"].append((tt + dur, t1, "peck", tx, c["y"], tx, c["y"], f))
            c["eaten"] = t1 - 0.1
            b.update(x=tx, y=c["y"], f=f)
            return t1
        k = r.random()
        if k < 0.36:                                 # idle: stand, bob, look about
            dur = r.uniform(0.9, 2.6)
            if r.random() < 0.25:
                f = -f
            b["segs"].append((tt, tt + dur, "idle", x, y, x, y, f))
        elif k < 0.68:                               # wander a few steps
            dx = r.uniform(20.0, 70.0) * self.scale * (1 if r.random() < 0.5 else -1)
            tx = clamp(x + dx, x0, x1)
            ty = clamp(y + r.uniform(-8.0, 8.0), *self.y_range)
            f = 1 if tx >= x else -1
            dur = max(0.3, (abs(tx - x) + abs(ty - y)) / speed)
            b["segs"].append((tt, tt + dur, "walk", x, y, tx, ty, f))
            x, y = tx, ty
        elif k < 0.9:                                # peck at the ground
            dur = r.choice((1, 2, 3)) * 0.42
            b["segs"].append((tt, tt + dur, "peck", x, y, x, y, f))
        elif k < 0.97:                               # a little hop
            tx = clamp(x + f * 9.0 * self.scale, x0, x1)
            b["segs"].append((tt, tt + 0.42, "hop", x, y, tx, y, f))
            x = tx
            dur = 0.42
        else:                                        # a flap (takeoff-lite)
            dur = 0.9
            b["segs"].append((tt, tt + dur, "flap", x, y, x, y, f))
        b.update(x=x, y=y, f=f)
        return tt + dur

    def crumb_eaten(self, k, t):
        """True once crumb k has been pecked up (hide it in the scene's crumb drawing)."""
        e = self.crumbs[k]["eaten"] if k < len(self.crumbs) else None
        return e is not None and t >= e

    def states(self, t):
        """[(x, y, PigeonPose, scale)] for every bird present at t (unsorted)."""
        out = []
        for b in self.birds:
            st = self._state(b, t)
            if st is not None:
                out.append(st)
        return out

    def _state(self, b, t):
        segs = b["segs"]
        if not segs or t < segs[0][0]:
            if b["arrive"] is not None:
                return None                          # not here yet
            if not segs:
                return (b["x"], b["y"], PigeonPose(facing=b["f"], seed=b["seed"]), self._sc(b["y"]))
            s = segs[0]
            return (s[3], s[4], PigeonPose(facing=s[7], seed=b["seed"]), self._sc(s[4]))
        j = bisect.bisect_right(b["t0s"], t) - 1
        t0, t1, kind, xa, ya, xb, yb, f = segs[j]
        u = clamp((t - t0) / max(1e-6, t1 - t0)) if t <= t1 else 1.0
        if t > t1:                                    # past the last segment: idle where it ended
            kind, xa, ya = "idle", xb, yb
        seed = b["seed"]
        tl = t + seed * 1.37
        idle_look = None
        nod = core.noise1(tl * 0.6, seed)
        if abs(nod) > 0.45:                           # now and then a glance toward the camera
            idle_look = f * (1.0 - 1.1 * smooth((abs(nod) - 0.45) / 0.2))
        if kind == "walk":
            x, y = lerp(xa, xb, u), lerp(ya, yb, u)
            dist = abs(x - xa) + abs(y - ya)
            p = PigeonPose(facing=f, walk=1.0, phase=dist / max(1e-6, pigeon_stride(self._sc(y))), seed=seed)
        elif kind == "peck":
            x, y = xa, ya
            p = PigeonPose(facing=f, peck=((t - t0) / 0.42) % 1.0, seed=seed)
        elif kind == "hop":
            x, y = lerp(xa, xb, u), ya
            p = PigeonPose(facing=f, hop=u, seed=seed)
        elif kind == "flap":
            x, y = xa, ya
            p = PigeonPose(facing=f, flap=math.sin(math.pi * u), lift=10.0 * math.sin(math.pi * u), seed=seed)
        elif kind == "fly":
            e = core.out_quad(u)
            x = lerp(xa, xb, e)
            y = yb
            h = (ya - yb) * -1.0                      # start height above the ground line
            lift = h * (1.0 - e) ** 1.4 + 30.0 * math.sin(math.pi * e) * (1.0 - e)
            p = PigeonPose(facing=f, fly=1.0, lift=lift / max(self._sc(yb), 1e-6), seed=seed)
        elif kind == "land":
            x, y = xb, yb
            p = PigeonPose(facing=f, flap=1.0 - u, lift=4.0 * (1.0 - u), seed=seed)
        else:
            x, y = xa, ya
            p = PigeonPose(facing=f, look=idle_look, puff=0.3 * max(0.0, core.noise1(tl * 0.3, seed + 5)), seed=seed)
        return (x, y, p, self._sc(y))

    def _sc(self, y):
        return self.scale * (1.0 + self.depth_scale * (y - self.y_range[0]))

    def draw(self, cr, t, light=None, look=None, sync=1.0, detail=None):
        """Draw every bird present at t, far to near. look (-1..1, screen terms) makes the birds
        that are not busy walking/flying turn their heads together -- the S6 gag (sync 0..1 =
        how many of them join in, deterministic per bird). Returns [PigeonRig]."""
        rigs = []
        for x, y, p, sc in sorted(self.states(t), key=lambda s: s[1]):
            if look is not None and p.walk < 0.5 and p.fly < 0.5 and core.hash01(p.seed, 99) < sync:
                p = p.with_(look=look, peck=0.0, puff=0.0)
            rigs.append(draw_pigeon(cr, x, y, sc, p, light, t, detail))
        return rigs


# ----------------------------------------------------------------------------------------
# character sheet
# ----------------------------------------------------------------------------------------

def lineup():
    return [B.LineupItem("pigeon", lambda cr, x, y, sc: draw_pigeon(cr, x, y, sc, PigeonPose(facing=1), t=0.4), 70.0)]


def sheet_items():
    items = []
    L = B.LIGHTS
    neutral = L["neutral"]

    def add(label, w, h, fn, group):
        items.append(B.SheetItem(label, w, h, fn, group))

    S = 4.0
    poses = [("profile, idle", PigeonPose(facing=1)), ("facing left", PigeonPose(facing=-1)),
             ("look at camera (swivel 0)", PigeonPose(facing=1, look=0.0)),
             ("swivel: look back (-1)", PigeonPose(facing=1, look=-1.0)),
             ("walk 0.0", PigeonPose(facing=1, walk=1.0, phase=0.0)), ("walk 0.25", PigeonPose(facing=1, walk=1.0, phase=0.25)),
             ("peck 0.5 (beak down)", PigeonPose(facing=1, peck=0.5)), ("peck 0.25", PigeonPose(facing=1, peck=0.25)),
             ("hop 0.5", PigeonPose(facing=1, hop=0.5)), ("flap", PigeonPose(facing=1, flap=1.0, lift=6.0)),
             ("fly in", PigeonPose(facing=-1, fly=1.0, lift=20.0)), ("puffed, coo", PigeonPose(facing=1, puff=1.0, tilt=0.2))]
    for label, pose in poses:
        def fn(cr, p=pose):
            B.sheet_bg(cr, 300, 260, "neutral", floor=220)
            draw_pigeon(cr, 150, 228 - p.lift * S * 0.0, S, p.with_(blink=0.0), neutral, t=0.3)
        add(label, 300, 260, fn, "poses (4x)")

    # the synchronized head swivel: a row of birds all looking the same way
    for lv in (-1.0, 0.0, 1.0):
        def fn(cr, lv=lv):
            B.sheet_bg(cr, 600, 200, "dusk", floor=160)
            for k in range(5):
                draw_pigeon(cr, 70 + k * 115, 172 + (k % 2) * 8, 1.6, PigeonPose(facing=1 if k % 2 else -1, look=lv, seed=k, blink=0.0),
                            L["dusk"], t=0.5 + k)
        add(f"S6 sync swivel look={lv:+.0f}", 600, 200, fn, "flock & scale")

    def flock_cell(cr):
        B.sheet_bg(cr, 900, 300, "golden", floor=200)
        fl = PigeonFlock(n=7, x_range=(80, 820), y_range=(215, 270), seed=4, scale=1.0,
                         crumbs=[(300, 0.5), (420, 0.6), (520, 0.5), (610, 0.7)], arrivals=[(0.5, -1), (1.0, 1)])
        core.src(cr, "#c89a5a")
        for c in fl.crumbs:
            if not fl.crumb_eaten(fl.crumbs.index(c), 2.0):
                core.circle(cr, c["x"], c["y"], 2.2)
        cr.fill()
        fl.draw(cr, 2.0, L["golden"])
    add("PigeonFlock at t=2.0: crumbs, arrivals", 900, 300, flock_cell, "flock & scale")
    for label, sc in (("film scale 0.9 (38 px)", 0.9), ("0.6", 0.6), ("0.4 (wide)", 0.4)):
        def fn(cr, sc=sc):
            B.sheet_bg(cr, 220, 160, "dusk", floor=120)
            for k in range(3):
                draw_pigeon(cr, 50 + k * 60, 135, sc, PigeonPose(facing=1 if k else -1, peck=0.5 if k == 1 else 0.0, seed=k), L["dusk"], t=0.7)
        add(label, 220, 160, fn, "flock & scale")
    for name in ("dusk", "golden", "blue_hour", "lantern_night"):
        def fn(cr, name=name):
            B.sheet_bg(cr, 220, 160, name, floor=120)
            draw_pigeon(cr, 110, 135, 2.0, PigeonPose(facing=1, blink=0.0), L[name], t=0.7)
        add(name, 220, 160, fn, "flock & scale")
    return items
