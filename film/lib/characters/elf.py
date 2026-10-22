"""elf.py -- THE ELF, the wash-house stranger (S1; elves also turn up in the tavern and square).

Elegant and aloof: a deep plum hooded travelling cloak (a hood with a shoulder cape, clasped
with pewter) over a long cool silver-blue kirtle, pale-gold hair falling in two curtains from a
center part, long pointed ears poking out through the hood with tiny enchanted sea-shells
glowing in them, half-lidded eyes that never leave the glowing hand-mirror in her hand -- its
runes scroll, and its cold light is on her face. She taps the SELF-SERVICE plaque behind her
without looking up.

    p = ch.ElfPose(facing=-1, sit=1.0, near=ch.ElfArm("mirror", phase=t), glow=1.0,
                   far=ch.ElfArm("tap_sign", phase=u, screen=(plaque_x, plaque_y)))
    rig = ch.draw_elf(cr, x, ground_y, 0.9, p, ch.LIGHTS["washhouse"], t)
    fx.glow(cr, *rig.mirror, 60 * 0.9, "#5fe0ff", 0.35)      # the scene adds the light spill

Scale 1.0: standing, ground -> ear tips = ELF_HEIGHT = 470 px (hood crown ~451, eyes ~400;
seated: crown ~348, the mirror's glass ~228 above the ground). Seated on a
bench of seat_h (default 125) her feet stay on the ground (knees together, ankles crossed,
the kirtle falling to the floor). Anchor (x, y) = the ground point below her pelvis
(pose.anchor="seat": the seat point). 3D-lite, like the dragon.
"""

import math
from dataclasses import dataclass, field, replace

from .. import core
from ..core import clamp, lerp, smooth
from . import _cast_kit as K
from . import base as B
from .base import Mat, Path, Proj, m_mul, m_rot_x, m_rot_y, m_rot_z, m_vec, v_add, v_lerp

TAU = math.tau

__all__ = ["ElfPose", "ElfArm", "ElfRig", "draw_elf", "elf_mirror", "ELF_HEIGHT", "ELF_SEAT_H", "ELF_COLORS",
           "ELF_GESTURES", "elf_mats"]

ELF_HEIGHT = 470.0
ELF_SEAT_H = B.BENCH_SEAT_H
LINE = B.LINE
PELVIS_Y = -228.0
HIP_W = 15.0
THIGH, SHIN, ANKLE_H = 110.0, 102.0, 16.0
UPPER_ARM, FOREARM, HAND_LEN = 76.0, 70.0, 44.0
SHOULDER_W = 36.0
ELEV = 0.12
HS = 1.45
HEAD_CHEAT = 0.2
SEAT_DY = 10.0
# the rig is authored a little small: this brings the measured top (ear tips) to ELF_HEIGHT
SIZE_K = 470.0 / 451.0

ELF_COLORS = {
    "skin": "#ECDCD2",       # pale, cool
    "hair": "#E1CC98",       # pale gold
    "cloak": "#4A3B5C",      # deep plum
    "cloak_in": "#6A5478",   # lining
    "kirtle": "#8A9AA8",     # cool silver-blue
    "trim": "#D5DCE6",       # silver embroidery on the hems
    "shoe": "#5A4A44",
    "lips": "#B97F86",
    "mouth": "#4A2028",
    "brow": "#9C8862",
    "eye": "#7FA7A0",        # pale sea-green
    "eye_hi": "#D2EEE6",
    "shell": "#F3E6DE",      # mother-of-pearl
    "shell_in": "#E2A39C",   # the shell's pink mouth
    "glow": "#5FE0FF",       # the cold magic of the shells and the mirror
    "pewter": "#9AA0A8",
    "glass": "#163C48",
}

_MATS = {}


def elf_mats():
    if not _MATS:
        C = ELF_COLORS
        _MATS.update({
            "skin": Mat.of(C["skin"], sss=0.45, line_k=0.5),
            "hair": Mat.of(C["hair"], sheen=0.3, line_k=0.55),
            "cloak": Mat.of(C["cloak"], shadow_k=1.1),
            "cloak_in": Mat.of(C["cloak_in"]),
            "kirtle": Mat.of(C["kirtle"], shadow_k=1.05),
            "shoe": Mat.of(C["shoe"], sheen=0.3),
            "shell": Mat.of(C["shell"], sheen=0.6),
            "pewter": Mat.of(C["pewter"], sheen=0.7),
            "brow": Mat.of(C["brow"]),
            "lips": Mat.of(C["lips"]),
        })
    return _MATS


@dataclass
class ElfArm:
    """gesture (ELF_GESTURES), amt/prev blend, hold callback (the "mirror" gesture draws her
    mirror by default), target (body space) or screen (caller coordinates) -- tap_sign reaches
    for it with a pointing finger -- hand override, phase 0..1 (tap_sign: two taps; mirror: the
    thumb's idle scrolling)."""
    gesture: str = "rest"
    amt: float = 1.0
    prev: str = "rest"
    hold: object = None
    target: tuple = None
    screen: tuple = None
    depth: float = -40.0
    hand: str = None
    phase: float = 0.0


@dataclass
class ElfPose:
    """facing/turn, sit (0..1 on a bench of seat_h), lean, head_turn/tilt/nod, look, mood
    (default "bored": aloof), mood2/mood_mix, talk, smile, blink, near/far ElfArm, glow (0..1:
    the mirror's light on her face), hood (1 up .. 0 down), shells (0..1 glow of the ear-shells),
    scroll (rune-scroll speed of the mirror), anchor, elev, shadow, seed."""
    facing: int = -1
    turn: float = 0.0
    sit: float = 0.0
    seat_h: float = ELF_SEAT_H
    lean: float = 0.0
    head_turn: float = 0.0
    head_tilt: float = 0.0
    head_nod: float = 0.0
    look: tuple = (0.0, 0.0)
    mood: object = "bored"
    mood2: object = None
    mood_mix: float = 0.0
    talk: float = 0.0
    smile: float = None
    blink: float = None
    near: ElfArm = field(default_factory=ElfArm)
    far: ElfArm = field(default_factory=ElfArm)
    glow: float = 0.0
    hood: float = 1.0
    shells: float = 1.0
    scroll: float = 1.0
    anchor: str = "ground"
    elev: float = ELEV
    shadow: bool = True
    seed: int = 0

    def with_(self, **kw):
        return replace(self, **kw)


@dataclass
class ElfRig:
    hand_near: B.HandFrame = None
    hand_far: B.HandFrame = None
    mirror: tuple = None          # the mirror's glass center (for the scene's light spill)
    shells: list = field(default_factory=list)
    head: tuple = (0.0, 0.0)
    mouth: tuple = (0.0, 0.0)
    eyes: list = field(default_factory=list)
    top: tuple = (0.0, 0.0)
    chest: tuple = (0.0, 0.0)
    feet: list = field(default_factory=list)
    seat: tuple = (0.0, 0.0)
    scale: float = 1.0
    facing: float = 1.0
    yaw: float = 0.0


# ----------------------------------------------------------------------------------------
# the mirror
# ----------------------------------------------------------------------------------------

def elf_mirror(cr, frame, t=0.0, light=None, glow=1.0, size=1.0, scroll=1.0, lw=None, detail=2):
    """Her enchanted hand-mirror as a hold callback: an oval pewter frame with a little finial on
    a short handle (the handle in the grip); the glass glows cold cyan, a mist drifts in it and
    rows of rune-glyphs scroll up through it. Draws upright (gravity) with the glass toward the
    camera; usable in any hand. The glass center is 44*size above the grip."""
    light = light or B.LIGHTS["neutral"]
    M = elf_mats()
    if lw is None:
        lw = B.line_w(cr, LINE * 0.8)
    cr.save()
    cr.rotate(-frame.angle)
    cr.scale(size, size)
    pw = B.palette(light, M["pewter"])
    # handle (in the fist), the finial, the oval frame -- one pewter union
    cr.new_path()
    core.smooth_closed(cr, B.offset_closed([(-4, 14), (4, 14), (3.5, -8), (6, -16), (-6, -16), (-3.5, -8)], lw), 0.8)
    core.ellipse(cr, 0.0, -44.0, 24.0 + lw, 30.0 + lw)
    core.ellipse(cr, 0.0, -77.0, 4.0 + lw, 4.5 + lw)
    core.src(cr, pw.line)
    cr.fill()
    core.smooth_closed(cr, [(-4, 14), (4, 14), (3.5, -8), (6, -16), (-6, -16), (-3.5, -8)], 0.8)
    core.ellipse(cr, 0.0, -44.0, 24.0, 30.0)
    core.ellipse(cr, 0.0, -77.0, 4.0, 4.5)
    core.src(cr, pw.lit)
    cr.fill()
    # glass
    cr.new_path()
    core.ellipse(cr, 0.0, -44.0, 19.5, 25.5)
    gl = Path(cr)
    gc = core.mix(ELF_COLORS["glass"], ELF_COLORS["glow"], 0.22 + 0.4 * glow)
    gl.add(cr)
    core.src(cr, gc)
    cr.fill()
    if detail >= 1:
        cr.save()
        gl.add(cr)
        cr.clip()
        bright = core.mix(ELF_COLORS["glow"], (1, 1, 1), 0.35)
        # a slow mist drifting in the glass
        B.sheen(cr, 6.0 * math.sin(t * 0.7), -46.0 + 6.0 * math.sin(t * 0.5), 17.0, 13.0, alpha=0.32 * glow, color=bright)
        # runes scrolling up: rows of little stave-glyphs (a stem and one or two twigs)
        pos = t * 13.0 * scroll
        off = pos % 8.0
        base_row = int(pos // 8.0)
        cr.new_path()
        for row in range(-4, 5):
            yy = -44.0 + row * 8.0 - off + 4.0
            half = 19.5 * math.sqrt(max(0.0, 1.0 - ((yy + 44.0) / 25.5) ** 2)) - 3.0
            if half < 3.0:
                continue
            n = max(1, int(half * 2.0 / 5.0))
            x0 = -(n - 1) * 2.5
            rid = row + base_row
            for k in range(n):
                h = core.hash01(rid * 13 + k, 5)
                if h < 0.12:          # a word gap
                    continue
                gx = x0 + k * 5.0
                cr.move_to(gx, yy - 2.4)
                cr.line_to(gx, yy + 2.4)
                kind = int(h * 4.0)
                if kind == 0:
                    cr.move_to(gx, yy - 1.6)
                    cr.line_to(gx + 1.8, yy - 2.6)
                    cr.move_to(gx, yy)
                    cr.line_to(gx + 1.8, yy - 1.0)
                elif kind == 1:
                    cr.move_to(gx - 1.6, yy - 1.4)
                    cr.line_to(gx, yy)
                    cr.line_to(gx + 1.6, yy - 1.4)
                elif kind == 2:
                    cr.move_to(gx, yy - 2.4)
                    cr.line_to(gx + 1.8, yy - 0.8)
                    cr.line_to(gx, yy + 0.6)
                else:
                    cr.move_to(gx - 1.4, yy + 1.4)
                    cr.line_to(gx + 1.4, yy - 1.4)
        cr.set_line_width(0.9)
        cr.set_line_cap(1)        # round
        core.src(cr, core.mix(ELF_COLORS["glow"], (1, 1, 1), 0.6), 0.9 * glow)
        cr.stroke()
        cr.set_line_cap(0)
        if detail >= 2:           # the glass darkens toward its rim, so the runes fade out there
            g3 = core.col(gc)[:3]
            cr.translate(0.0, -44.0)
            cr.scale(19.5 / 25.5, 1.0)
            cr.set_source(core.radial(0.0, 0.0, 25.5, [(0.0, (*g3, 0.0)), (0.6, (*g3, 0.0)), (1.0, (*g3, 0.9))]))
            cr.paint()
        cr.restore()
        cr.new_path()
        core.ellipse(cr, 0.0, -44.0, 21.6, 27.8)
        cr.set_line_width(1.1)
        core.src(cr, pw.shadow)
        cr.stroke()
    B.sheen(cr, -9.0, -58.0, 6.0, 3.0, angle=-0.5, alpha=0.5)
    cr.restore()


# ----------------------------------------------------------------------------------------
# gestures
# ----------------------------------------------------------------------------------------

def _g_rest(sk, side, c):
    if c["sit_k"] > 0.5:
        return v_add(c["lap"], (side * 14.0, -6.0, 6.0)), "relaxed", 0.3, "front"
    return v_add(sk, (side * 10.0, 150.0, 12.0)), "relaxed", 0.0, "auto"


def _g_mirror(sk, side, c):
    # the mirror held up before her chest, tilted toward her face; phase = idle thumb scrolling
    ph = c["phase"]
    wob = math.sin(ph * TAU * 1.3) * 1.5
    return v_add(c["chest"], (side * 4.0 + c["fwd"][0] * 18.0, 34.0 + wob, 58.0)), "grip", 0.0, "front"


def _g_tap(sk, side, c):
    # reaching back over the shoulder; two quick taps on whatever is there (screen= target)
    ph = c["phase"]
    tap = math.sin(min(1.0, ph * 2.0) * math.pi * 2.0) ** 2 * 6.0 if ph < 0.9 else 0.0
    base = c.get("tap_target") or v_add(sk, (side * 26.0 - c["fwd"][0] * 70.0, -96.0, -40.0))
    return v_add(base, (c["fwd"][0] * tap, 0.0, 0.0)), "point", 0.0, "back"


def _g_point(sk, side, c):
    f = c["fwd"]
    return v_add(sk, (side * 14.0 + f[0] * 70.0, 30.0, 20.0 + f[2] * 60.0)), "point", 0.0, "front"


ELF_GESTURES = {"rest": _g_rest, "mirror": _g_mirror, "tap_sign": _g_tap, "point": _g_point}


# ----------------------------------------------------------------------------------------
# the rig
# ----------------------------------------------------------------------------------------

def draw_elf(cr, x, y, scale=1.0, pose=None, light=None, t=0.0, detail=None):
    pose = pose or ElfPose()
    light = light or B.LIGHTS["neutral"]
    q = K.Q(cr, light, elf_mats(), t, pose)
    yaw = K.yaw_of(pose.facing, pose.turn)
    q.yaw = yaw
    proj = Proj(yaw, pose.elev)
    q.proj = proj
    sit = clamp(pose.sit)
    q.sit = sit
    scale_px = scale
    scale = scale * SIZE_K            # internal units: lines stay LINE px on screen
    dev = q.lod(scale, detail)
    q.lw = B.line_for(LINE / SIZE_K, dev, 1.0 / SIZE_K)
    cr.save()
    cr.translate(x, y + (pose.seat_h * scale_px * sit if pose.anchor == "seat" else 0.0))
    cr.scale(scale, scale)
    S = _skeleton(pose, t, sit, yaw)
    q.S = S
    rig = ElfRig(scale=scale_px, facing=1.0 if yaw >= 0 else -1.0, yaw=yaw)
    if pose.shadow:
        fa = [proj.xy(f["ankle"]) for f in S["feet"]]
        B.contact_shadow(cr, (fa[0][0] + fa[1][0]) / 2.0, 2.0, 60.0, 12.0, alpha=0.3)
    near_side = -1.0 if yaw >= 0 else 1.0
    far_side = -near_side
    arms = {near_side: pose.near, far_side: pose.far}
    A = {s: _solve_arm(q, S, s, arms[s]) for s in (near_side, far_side)}
    frontish = abs(yaw) < 0.38
    zf = A[far_side]["z"]
    far_layer = ("mid" if frontish else "back") if zf in ("auto", "back") else (("front" if frontish else "mid") if zf == "front" else zf)
    if zf == "back":
        far_layer = "back"
    _cloak_back(q)
    if far_layer == "back":
        _upper(q, A[far_side])
        rig.hand_far = _lower(q, A[far_side], far_side)
    _legs(q)
    _kirtle(q)
    _cloak_front(q)
    if far_layer != "back":
        _upper(q, A[far_side])
    _upper(q, A[near_side])
    _cowl(q)
    if far_layer == "mid":
        rig.hand_far = _lower(q, A[far_side], far_side)
    head = _head(q)
    if far_layer == "front":
        rig.hand_far = _lower(q, A[far_side], far_side)
    rig.hand_near = _lower(q, A[near_side], near_side)
    mirror = None
    for s_ in (near_side, far_side):
        if A[s_]["arm"].gesture == "mirror":
            mirror = A[s_]["mirror"]
    ex = K.Exporter(cr)
    cr.restore()
    ex.ready(cr)
    rig.head, rig.mouth = ex(head["center"]), ex(head["mouth"])
    rig.eyes = [ex(e) for e in head["eyes"]]
    rig.shells = [ex(sh) for sh in head["shells"]]
    rig.top = ex(head["top"])
    rig.chest = ex(proj.xy(S["chest"]))
    rig.feet = [ex(proj.xy(f["ankle"])) for f in S["feet"]]
    rig.seat = ex((0.0, -pose.seat_h / SIZE_K * sit))
    ex.hand(rig.hand_near, scale)
    ex.hand(rig.hand_far, scale)
    if mirror is not None:
        rig.mirror = ex(mirror)
    return rig


def _skeleton(pose, t, sit, yaw):
    S = {}
    br = B.breathing(t, 0.2, pose.seed)
    k = smooth(sit)
    S.update(br=br, sit_k=k)
    stand_pel = (0.0, PELVIS_Y, 0.0)
    sit_pel = (0.0, -pose.seat_h / SIZE_K - SEAT_DY, -10.0)
    pel = v_lerp(stand_pel, sit_pel, k)
    S["pelvis"] = pel
    tilt = 0.22 * pose.lean + 0.1 * k + 0.012 * B.sway(t, 0.18, pose.seed + 3)
    R = m_mul(m_rot_z(0.01 * B.sway(t, 0.14, pose.seed + 5)), m_rot_x(-tilt))
    S["R"], S["tilt"] = R, tilt

    def T(v):
        return v_add(pel, m_vec(R, v))

    S["T"] = T
    S["waist"] = T((0.0, -40.0, 1.0))
    S["chest"] = T((0.0, -78.0, 4.0 + br))
    sh_y = -108.0 - 1.2 * br
    S["sh_y"] = sh_y
    S["shoulders"] = {s: T((s * SHOULDER_W, sh_y + 6.0, -2.0)) for s in (-1.0, 1.0)}
    S["neck"] = T((0.0, sh_y - 4.0, 2.0))
    talk = clamp(pose.talk)
    nod = pose.head_nod * 0.42 + 0.012 * br + 0.02 * talk * math.sin(t * 6.0) + 0.015 * B.sway(t, 0.2, pose.seed + 2) - 0.4 * tilt
    hy = clamp(pose.head_turn, -1.2, 1.2) * 0.95
    RH = m_mul(m_rot_y(hy - HEAD_CHEAT * yaw), m_mul(m_rot_x(nod), m_rot_z(pose.head_tilt)))
    S["RH"], S["head_yaw"] = RH, hy - HEAD_CHEAT * yaw
    pivot = v_add(S["neck"], m_vec(R, (0.0, -12.0, 6.0)))
    S["pivot"] = pivot
    S["head_c"] = v_add(pivot, m_vec(RH, (0.0, -24.0 * HS, 3.0)))
    # legs: standing straight; seated, knees together and the near ankle crossed in front
    feet = []
    near = -1.0 if yaw >= 0 else 1.0
    for s in (-1.0, 1.0):
        hip = v_add(pel, m_vec(R, (s * HIP_W, 8.0, 0.0)))
        stand_ank = (s * (HIP_W - 2.0), -ANKLE_H, 3.0)
        if s == near:
            seat_ank = (-near * 2.0, -ANKLE_H, THIGH * 0.86 + 6.0)
        else:
            seat_ank = (s * 9.0, -ANKLE_H, THIGH * 0.86 - 4.0)
        ank_t = v_lerp(stand_ank, seat_ank, smooth((sit - 0.3) / 0.7))
        knee, ank = B.ik3(hip, ank_t, THIGH, SHIN, (s * 0.06, lerp(0.1, -0.6, k), 1.0))
        feet.append({"hip": hip, "knee": knee, "ankle": ank, "side": s})
    S["feet"] = feet
    S["near"] = near
    lap = v_add(v_lerp(pel, v_lerp(feet[0]["knee"], feet[1]["knee"], 0.5), 0.5), (0.0, -14.0, 0.0))
    S["ctx"] = {"chest": S["chest"], "lap": lap, "sit_k": k, "fwd": K.facing_dir(yaw), "phase": 0.0}
    return S


def _solve_arm(q, S, side, arm):
    sk = S["shoulders"][side]
    c = dict(S["ctx"], phase=arm.phase)
    if arm.screen is not None and arm.gesture == "tap_sign":
        c["tap_target"] = K.screen_to_body(q, q.proj, arm.screen, q.proj.depth(sk) + arm.depth)
    tgt, hp, hang, z = ELF_GESTURES.get(arm.gesture, _g_rest)(sk, side, c)
    if arm.amt < 1.0:
        t0, hp0, ha0, z0 = ELF_GESTURES.get(arm.prev, _g_rest)(sk, side, dict(c, phase=0.0))
        u = core.inout_sine(clamp(arm.amt))
        arc = math.sin(math.pi * u) * 16.0
        tgt = v_add(v_lerp(t0, tgt, u), (side * arc * 0.5, -arc * 0.5, arc * (1 if z != "back" else -1)))
        hang = lerp(ha0, hang, u)
        if u < 0.5:
            hp = hp0
            z = z0
    if arm.target is not None:
        tgt = arm.target
    if arm.screen is not None and arm.gesture != "tap_sign":
        tgt = K.screen_to_body(q, q.proj, arm.screen, q.proj.depth(sk) + arm.depth)
    if arm.hand:
        hp = arm.hand
    pole = (side * 1.0, 0.5, -0.5) if arm.gesture != "tap_sign" else (side * 0.8, 0.9, 0.3)
    elbow, wrist = B.ik3(sk, tgt, UPPER_ARM, FOREARM, pole)
    w2 = q.proj.xy(wrist)
    return {"sh": sk, "el": elbow, "wr": wrist, "hand": hp, "z": z, "arm": arm, "hang": hang, "side": side,
            "mirror": (w2[0], w2[1] - 50.0)}


def _upper(q, A):
    """The upper sleeve (mostly under the shoulder cape: shaded only when the arm is raised
    out from under it, else one flat shadow-side fill)."""
    cr, proj = q.cr, q.proj
    s_, o_ = K.caps(cr, [proj.xy(A["sh"]), proj.xy(A["el"])], [15.0, 12.5], q.lw)
    if A["el"][1] < A["sh"][1] + 40.0:
        q.shade(s_, q.M["kirtle"], outline=o_, size=26, rim=0.6, shadow=0.8)
    else:
        K.flat(q, s_, o_, q.M["kirtle"], tone=0.35)


def _lower(q, A, side):
    """The forearm sleeve and her hand (+ the mirror)."""
    cr, proj, M = q.cr, q.proj, q.M
    el, wr = proj.xy(A["el"]), proj.xy(A["wr"])
    fdx, fdy = core.normalize((wr[0] - el[0], wr[1] - el[1]))
    ang = math.atan2(fdy, fdx)
    s_, o_ = K.caps(cr, [el, wr], [12.5, 9.5], q.lw)
    q.shade(s_, M["kirtle"], outline=o_, size=24, rim=0.7)
    arm = A["arm"]
    hold = arm.hold
    if hold is None and arm.gesture == "mirror":
        t, light, glow, sp, det = q.t, q.light, max(0.6, q.pose.glow), q.pose.scroll, q.detail

        def hold(cr_, f, t=t, light=light, glow=glow, sp=sp, det=det):
            elf_mirror(cr_, f, t, light, glow, scroll=sp, detail=det)
    flip = (side > 0) == (q.yaw >= 0)
    return B.hand(cr, wr[0] + fdx * 3.0, wr[1] + fdy * 3.0, ang + A["hang"], HAND_LEN, A["hand"], M["skin"], q.light_nb, q.lw,
                  flip=flip, claw=None, hold=hold, finger_len=1.15, finger_w=0.85, palm_w=0.9, detail=q.detail)


def _legs(q):
    """Slim legs in soft pointed shoes (only the shoes show under the kirtle)."""
    proj, S, M = q.proj, q.S, q.M
    shoes = []
    for f in S["feet"]:
        a = f["ankle"]
        pts = []
        for k in range(6):
            ang = TAU * k / 6
            pts.append(proj.xy((a[0] + math.cos(ang) * 7.5, a[1] + math.sin(ang) * 3.0, a[2] + math.sin(ang) * 6.0)))
            pts.append(proj.xy((a[0] + math.cos(ang) * 7.5, a[1] + ANKLE_H - 4.0 + math.sin(ang) * 3.5, a[2] + 12.0)))
        pts.append(proj.xy((a[0], a[1] + ANKLE_H - 3.0, a[2] + 30.0)))       # the pointed toe
        shoes.append(core.convex_hull(pts))
    K.union(q, shoes, M["shoe"], size=14, flat_tone=0.2)


def _trim(q, pts):
    """The silver embroidered band along a hem (detail >= 1)."""
    if q.detail >= 1 and len(pts) >= 2:
        B.detail_lines(q.cr, [pts], q.lw * 1.3, ELF_COLORS["trim"], 0.75, taper=(0.6, 1.0, 0.6))


def _kirtle(q):
    """The long kirtle: standing an A-line to the ankles; seated it drapes over the knees and
    falls to the floor in a skirt, the shoe tips peeking out under the hem."""
    cr, proj, S, t = q.cr, q.proj, q.S, q.t
    T, pel = S["T"], S["pelvis"]
    xy = proj.xy
    k = S["sit_k"]
    pal = q.P(q.M["kirtle"])
    if k < 0.5:
        rings = [(T((0.0, -100.0, 2.0)), 30.0, 21.0), (T((0.0, -76.0, 4.0)), 33.0, 23.0), (T((0.0, -40.0, 2.0)), 25.0, 19.0),
                 (v_add(pel, (0.0, 6.0, 0.0)), 36.0, 27.0), ((0.0, -112.0, 0.0), 46.0, 33.0), ((0.0, -10.0, -2.0), 60.0, 42.0)]
        left, right = [], []
        for (c, a, cz) in rings:
            x, y, hw = proj.ellipse(c, a, cz)
            left.append((x - hw, y))
            right.append((x + hw, y))
        hem = [(lerp(left[-1][0], right[-1][0], u), lerp(left[-1][1], right[-1][1], u) + 8.0 * math.sin(math.pi * u) + 1.5 * math.sin(u * 9 + t))
               for u in (0.2, 0.4, 0.6, 0.8)]
        nb = xy(S["neck"])
        pts = left + hem + right[::-1] + [(nb[0] + 14.0, nb[1] + 4.0), (nb[0] - 14.0, nb[1] + 4.0)]
        ks, ko = B.smooth_paths(cr, pts, q.lw, 0.8)
        q.shade(ks, q.M["kirtle"], outline=ko, size=90, shadow=0.6)
        if q.detail >= 1:
            cr.save()
            ks.add(cr)
            cr.clip()
            folds = [[xy((dx * 0.6, -150.0, 18.0)), xy((dx, -80.0, 30.0)), xy((dx * 1.25, -20.0, 40.0))] for dx in (-14.0, 12.0)]
            B.detail_lines(cr, folds, q.lw, pal.line, 0.35)
            cr.restore()
            _trim(q, [(lerp(left[-1][0], right[-1][0], u), lerp(left[-1][1], right[-1][1], u) + 8.0 * math.sin(math.pi * u) - 6.0)
                      for u in (0.12, 0.3, 0.5, 0.7, 0.88)])
        return
    # seated: bodice + lap over the knees + the skirt (one union). The skirt is a soft BELL of
    # cloth hanging from just under the knees to the floor -- stacked rings like the standing
    # kirtle, flaring toward a scalloped hem -- so it drapes instead of reading as a board
    kn = {f["side"]: f["knee"] for f in S["feet"]}
    kx = 0.5 * (kn[-1.0][0] + kn[1.0][0])
    ky = 0.5 * (kn[-1.0][1] + kn[1.0][1])
    kz = max(kn[-1.0][2], kn[1.0][2])
    torso = B.ellipsoid_pts(xy, T((0.0, -76.0, 4.0)), 31.0, 34.0, 22.0, 8) + B.ellipsoid_pts(xy, T((0.0, -40.0, 2.0)), 25.0, 10.0, 19.0, 6)
    hips = B.ellipsoid_pts(xy, v_add(pel, (0.0, 4.0, -2.0)), 38.0, 12.0, 28.0, 8)
    knees = K.circle_pts(xy(kn[-1.0]), 19.0, 8) + K.circle_pts(xy(kn[1.0]), 19.0, 8)
    sway = 1.5 * math.sin(t * 0.8 + q.pose.seed)
    bell = []
    for u in (0.0, 0.3, 0.62, 1.0):
        bell.append(((kx + sway * u, lerp(ky + 8.0, -8.0, u), lerp(kz - 6.0, kz - 16.0, u)),
                     lerp(29.0, 47.0, u ** 1.4), lerp(22.0, 36.0, u)))
    left, right = [], []
    for (c, a, cz) in bell:
        x, y, hw = proj.ellipse(c, a, cz)
        left.append((x - hw, y))
        right.append((x + hw, y))
    c, a, cz = bell[-1]
    cy = xy(c)[1]
    ring = [xy((c[0] + math.sin(ang) * a, c[1] + 2.6 * math.sin(7.0 * ang + 0.5 * math.sin(t * 0.7)),
                c[2] + math.cos(ang) * cz)) for ang in (TAU * i / 32 for i in range(32))]
    hem = sorted((p for p in ring if p[1] >= cy - 0.5), key=lambda p: p[0])
    skirt = left + hem + right[::-1]
    if sum(skirt[i][0] * skirt[i - 1][1] - skirt[i - 1][0] * skirt[i][1] for i in range(len(skirt))) > 0:
        skirt.reverse()                                  # wound like the convex hulls (one union)
    hulls = [core.convex_hull(torso), core.convex_hull(hips + knees), skirt]
    path = K.union(q, hulls, q.M["kirtle"], size=70, shadow=0.7)
    if q.detail >= 1:
        cr.save()
        path.add(cr)
        cr.clip()
        folds = []
        for s in (-1.0, 1.0):
            kk = kn[s]
            folds.append([xy(v_add(kk, (s * 6.0, 14.0, 16.0))), xy((kk[0] + s * 16.0, -60.0, kz + 10.0)), xy((kk[0] + s * 24.0, -14.0, kz + 12.0 - 7.0))])
        folds.append([xy((kx, kn[1.0][1] + 16.0, kz + 6.0)), xy((kx + 1.0, -50.0, kz + 13.0)), xy((kx, -14.0, kz + 15.0))])
        B.detail_lines(cr, folds, q.lw, pal.line, 0.4)
        cr.restore()
        n = len(hem)
        _trim(q, [(p[0], p[1] - 6.0) for p in hem[n // 6: n - n // 6]])


def _cloak_rings(q):
    S = q.S
    T, pel = S["T"], S["pelvis"]
    k = S["sit_k"]
    hem_y = lerp(-14.0, pel[1] + 40.0, k)
    return [(T((0.0, -106.0, -2.0)), 40.0, 28.0), (T((0.0, -70.0, -4.0)), 47.0, 32.0),
            (v_add(pel, (0.0, 0.0, -4.0)), 55.0, 37.0), ((pel[0], hem_y, -6.0 - 20.0 * k), lerp(76.0, 66.0, k), 48.0)]


def _cloak_back(q):
    """The cloak's back panel (behind everything): from the shoulders, flaring to the ankles
    (seated: hanging over the bench behind her)."""
    cr, proj = q.cr, q.proj
    rings = _cloak_rings(q)
    pts = []
    for (c, a, cz) in rings:
        for i in range(10):
            ang = math.pi * 0.5 + math.pi * i / 9          # the back half
            pts.append(proj.xy((c[0] + math.sin(ang) * a, c[1], c[2] + math.cos(ang) * cz)))
    hull = core.convex_hull(pts)
    cs, co = B.smooth_paths(cr, hull, q.lw, 0.85)
    q.shade(cs, q.M["cloak"], outline=co, size=100, shadow=0.7)


def _cloak_front(q):
    """The cloak's front edges down each side, open at the front (we see the kirtle between
    them, the lighter lining turning at the edges)."""
    cr, proj = q.cr, q.proj
    rings = _cloak_rings(q)
    pairs = []
    edges = []
    for s in (-1.0, 1.0):
        pts = []
        edge = []
        for (c, a, cz), w0 in zip(rings, (0.0, 0.3, 0.55, 0.72)):
            for i in range(6):
                ang = s * (w0 + (math.pi * 0.5 + 0.2 - w0) * i / 5)
                pts.append(proj.xy((c[0] + math.sin(ang) * a * 1.03, c[1], c[2] + math.cos(ang) * cz * 1.03)))
            ang = s * (w0 + 0.05)
            edge.append(((c[0] + math.sin(ang) * a * 1.03, c[1], c[2] + math.cos(ang) * cz * 1.03), ang))
        pairs.append(B.smooth_paths(cr, core.convex_hull(pts), q.lw, 0.85))
        # the lining shows along an edge only where that edge faces us
        if -math.sin(edge[-1][1]) * proj.s + math.cos(edge[-1][1]) * proj.c > 0.2:
            edges.append([proj.xy(e) for e, _a in edge[1:]])
    K.union_paths(q, pairs, q.M["cloak"], size=40, rim=0.8, shadow=0.7)
    if q.detail >= 1 and edges:
        B.detail_lines(cr, edges, q.lw * 1.6, q.P(q.M["cloak_in"]).lit, 0.9, taper=(0.2, 1.0, 1.0))


def _cowl(q):
    """The hood's shoulder cape: over the shoulders and the upper arms, a pewter clasp."""
    cr, proj, S = q.cr, q.proj, q.S
    T, sh_y = S["T"], S["sh_y"]
    pts = []
    for yy, a, cz, zc in ((sh_y - 8.0, 18.0, 14.0, 2.0), (sh_y + 4.0, 46.0, 29.0, -1.0), (sh_y + 40.0, 55.0, 35.0, -2.0)):
        for i in range(12):
            ang = TAU * i / 12
            pts.append(proj.xy(T((math.sin(ang) * a, yy + (2.5 * math.cos(ang) if yy > sh_y else 0.0), zc + math.cos(ang) * cz))))
    cs, co, _h = B.hull_paths(cr, pts, q.lw, 0.85)
    pal = q.shade(cs, q.M["cloak"], outline=co, size=60, rim=0.8, shadow=0.75)
    if q.detail >= 1:
        cr.save()
        cs.add(cr)
        cr.clip()
        folds = []
        for ang in (-1.15, -0.55, 0.5, 1.1):
            if -math.sin(ang) * proj.s + math.cos(ang) * proj.c > 0.25:
                folds.append([proj.xy(T((math.sin(ang) * 26.0, sh_y + 2.0, 2.0 + math.cos(ang) * 18.0))),
                              proj.xy(T((math.sin(ang) * 54.0, sh_y + 42.0, -2.0 + math.cos(ang) * 35.0)))])
        B.detail_lines(cr, folds, q.lw * 1.1, pal.line, 0.45, taper=(0.1, 1.0, 0.6))
        cr.restore()
    c = proj.xy(T((0.0, sh_y + 12.0, 22.0)))
    bs, bo = B.ellipse_paths(cr, c[0], c[1], 6.0, 6.0, q.lw * 0.8)
    K.flat(q, bs, bo, q.M["pewter"])
    if q.detail >= 2:
        B.sheen(cr, c[0] - 1.5, c[1] - 1.5, 2.6, 2.0, alpha=0.6)


# ----------------------------------------------------------------------------------------
# head
# ----------------------------------------------------------------------------------------

# the hair: two curtains from a center part, sweeping over the brow and down past the jaw
# (outer edge top -> bottom, then the inner edge bottom -> top; x is mirrored per side)
_CURTAIN = ((1.0, -30.5, 11.0), (9.5, -29.5, 10.0), (17.5, -23.5, 8.0), (22.5, -12.0, 5.0), (23.2, 2.0, 3.0),
            (22.0, 17.0, 2.0), (19.5, 32.0, 2.0), (16.0, 46.0, 4.0), (13.0, 56.0, 6.0),
            (11.5, 49.0, 7.0), (14.0, 35.0, 7.5), (16.5, 21.0, 8.0), (18.4, 7.0, 9.5), (18.6, -5.0, 11.0),
            (16.0, -15.0, 15.0), (10.0, -22.0, 18.5), (3.0, -24.8, 19.0), (0.6, -26.5, 18.5))
_ARCH3 = ((-20.0, 22.0, 2.0), (-24.0, 4.0, 2.0), (-21.0, -16.0, 6.0), (-11.0, -27.0, 10.0), (0.0, -30.0, 11.0),
          (11.0, -27.0, 10.0), (21.0, -16.0, 6.0), (24.0, 4.0, 2.0), (20.0, 22.0, 2.0))


def _head(q):
    cr, proj, M, S, pose, t = q.cr, q.proj, q.M, q.S, q.pose, q.t
    RH, HC = S["RH"], S["head_c"]
    e = B.expr(pose.mood)
    if pose.mood2 is not None and pose.mood_mix > 0:
        e = e.blend(B.expr(pose.mood2), pose.mood_mix)
    if pose.smile is not None:
        e = e.with_(smile=pose.smile)
    lw = q.lw
    hyaw = q.yaw + S["head_yaw"]
    near = -1.0 if hyaw >= 0 else 1.0
    far = -near
    xy = proj.xy

    def P(v):
        w = m_vec(RH, v)
        return xy((HC[0] + w[0] * HS, HC[1] + w[1] * HS, HC[2] + w[2] * HS))

    def nz(v):
        w = m_vec(RH, v)
        return -w[0] * proj.s + w[2] * proj.c

    skin = q.P(M["skin"])
    hood = clamp(pose.hood) > 0.5
    # ---- the hood dome (behind the face) and the ears through their slits
    for s in (far, near):
        _ear(q, P, nz, s, back=True)
    if hood:
        dome = K.circle_pts(P((0.0, -4.0, -4.0)), 29.0 * HS, 16, sy=1.04)
        drape = [P((math.sin(a) * 25.0, 26.0 + 6.0 * math.cos(a), -6.0 + math.cos(a) * 18.0)) for a in (TAU * i / 8 for i in range(8))]
        hs_, ho_, _h = B.hull_paths(cr, dome + drape, lw)
        q.shade(hs_, M["cloak"], outline=ho_, size=60, shadow=0.85, rim=0.7)
    else:
        hs_, ho_, _h = B.hull_paths(cr, K.circle_pts(P((0.0, -5.0, -3.0)), 26.0 * HS, 14), lw)
        q.shade(hs_, M["hair"], outline=ho_, size=50, shadow=0.8, rim=0.7)
    # ---- hair: two curtains from a center part. In 3/4 the far one hangs behind the face
    # (only its edge shows past the cheek); a curtain facing us is drawn over the face's edge.
    sway = 1.2 * B.sway(t, 0.25, pose.seed + 9)
    curtains = {}
    for s in (-1.0, 1.0):
        pts = [P((s * x_, y_, z_ + (sway * s * (y_ - 10.0) / 48.0 if y_ > 10.0 else 0.0))) for x_, y_, z_ in _CURTAIN]
        if s < 0:
            pts.reverse()
        curtains[s] = B.smooth_paths(cr, pts, lw, 0.7)
    front_hair = [s for s in (-1.0, 1.0) if nz((s * 0.55, 0.0, 0.83)) > 0.3]
    back_hair = [s for s in (-1.0, 1.0) if s not in front_hair]
    hp = q.P(M["hair"])
    if back_hair:
        K.union_paths(q, [curtains[s] for s in back_hair], M["hair"], size=34, rim=0.0, shadow=0.8)
    # ---- the hood's front edge: the whole band first (the face hides its far run), the near
    # run again after the face and hair (as on the gnome)
    arch = [P(a) for a in _ARCH3]
    vis = [nz(tuple(c / (math.sqrt(a3[0] ** 2 + a3[1] ** 2 + a3[2] ** 2) or 1.0) for c in a3)) for a3 in _ARCH3]
    if hood:
        hs2, ho2 = B.taper_paths(cr, arch, 4.0, 4.0, lw, cap=True, profile=lambda u: 4.0 * (0.6 + 0.4 * math.sin(math.pi * u)))
        K.flat(q, hs2, ho2, M["cloak_in"])
    # ---- face: a long elegant oval, a pointed chin
    face = B.ellipsoid_pts(P, (0.0, 2.0, 5.0), 19.5, 27.0, 16.0, 10) + K.circle_pts(P((0.0, 25.0, 9.0)), 6.5 * HS, 8)
    fs, fo = B.smooth_paths(cr, core.convex_hull(face), lw, 0.85)
    q.shade(fs, M["skin"], outline=fo, size=40, shadow=0.8, rim=0.0)
    glow = clamp(pose.glow)
    cr.save()
    fs.add(cr)
    cr.clip()
    # ---- eyes: almond, half-lidded, long lashes (clipped to the face: the far one turns away)
    blink = B.auto_blink(t, pose.seed + 71) if pose.blink is None else pose.blink
    eyes = []
    for s in (far, near):
        ec = P((s * 9.5, -2.0, 19.0))
        eyes.append(ec)
        fz = nz((s * 0.4, -0.1, 0.9))
        if fz < 0.12:
            continue
        fore = clamp(0.3 + fz * 0.8, 0.3, 1.0)
        op = P((s * 16.0, -4.0, 16.0))
        outer = 1.0 if op[0] > ec[0] else -1.0
        ang = math.atan2((op[1] - ec[1]) * outer, (op[0] - ec[0]) * outer)
        B.eye(cr, ec[0], ec[1], 7.0 * HS * fore, 5.4 * HS, q.light, lw * 0.9, angle=ang * 0.8 - 0.1 * outer,
              look=(pose.look[0] * outer, pose.look[1]), lid=e.lid, lid_bot=e.lid_bot, tilt=e.lid_tilt, outer=outer,
              blink=blink, iris=ELF_COLORS["eye"], iris_hi=ELF_COLORS["eye_hi"], pupil="#1d120c", pupil_size=0.45,
              skin=ELF_COLORS["skin"], crease=0.25 if q.detail >= 2 else 0.0, lash=1.15, lash_flick=1.0, line=skin.line,
              lid_shade=0.08)
    if glow > 0.01:            # the mirror's cold light from below, over the face and eyes
        gp = P((0.0, 30.0, 26.0))
        B.sheen(cr, gp[0], gp[1], 34.0 * HS, 30.0 * HS, alpha=0.38 * glow, color=ELF_COLORS["glow"])
    cr.restore()
    brows = []
    for s in (far, near):
        if nz((s * 0.4, -0.4, 0.8)) < -0.05:
            continue
        li = (e.brow_in * 0.7 + e.brow_y) * 4.0
        lo_ = (e.brow_out * 0.6 + e.brow_y) * 4.0
        brows.append([P((s * 4.0, -10.5 - li, 21.0)), P((s * 10.0, -13.5 - (li + lo_) / 2, 20.0)), P((s * 16.0, -11.0 - lo_, 16.5))])
    if brows:
        B.detail_lines(cr, brows, lw * 1.25, q.P(M["brow"]).shadow, 0.95, taper=(0.3, 1.0, 0.2))
    # ---- nose and mouth: small, cool
    nl = [[P((0.8, 4.0, 23.0)), P((1.4, 8.5, 24.0)), P((-0.6, 10.0, 23.0))]]
    B.detail_lines(cr, nl, lw * 0.8, skin.line, 0.55, taper=(0.1, 1.0, 0.5))
    mo = _mouth(q, P, e, skin)
    # ---- the curtains facing us, over the face's edges, then the hood's near edge over them
    if front_hair:
        K.union_paths(q, [curtains[s] for s in front_hair], M["hair"], size=34, rim=0.6, shadow=0.8)
    if q.detail >= 1:
        strands = []
        for s in front_hair:
            strands.append([P((s * 3.0, -27.5, 15.0)), P((s * 14.0, -20.0, 13.0)), P((s * 20.0, -4.0, 9.0)), P((s * 19.0, 20.0, 7.0))])
            strands.append([P((s * 19.5, 26.0, 6.0)), P((s * 16.0, 44.0, 6.0))])
        B.detail_lines(cr, strands, lw * 0.9, hp.line, 0.4)
    if hood:
        idx = [i for i, v_ in enumerate(vis) if v_ > -0.15]
        if len(idx) >= 2:
            run = arch[idx[0]:idx[-1] + 1]      # the arch is ordered: the visible part is one stretch
            hs2, ho2 = B.taper_paths(cr, run, 4.0, 4.0, lw, cap=True, profile=lambda u: 4.0 * (0.5 + 0.5 * math.sin(math.pi * u)))
            K.flat(q, hs2, ho2, M["cloak_in"])
    shells = []
    for s in (far, near):
        sh = _ear(q, P, nz, s, back=False)
        if sh is not None:
            shells.append(sh)
    return {"center": P((0.0, 0.0, 0.0)), "mouth": mo, "eyes": eyes, "shells": shells, "top": P((0.0, -34.0, 0.0))}


def _mouth(q, P, e, skin):
    """A small, cool mouth: a line with a hint of a smile, or a neat opening when she talks."""
    cr, lw = q.cr, q.lw
    sm = e.smile
    talk = clamp(q.pose.talk)
    y0, z0 = 17.0, 19.0
    if talk < 0.05:
        B.detail_line(cr, [P((-5.0, y0 - sm * 1.5, z0 - 1.0)), P((0.0, y0 + 0.5, z0 + 0.5)), P((5.0, y0 - sm * 1.5, z0 - 1.0))],
                      lw * 1.0, q.P(q.M["lips"]).shadow, 0.9, taper=(0.3, 1.0, 0.3))
        return P((0.0, y0, z0))
    hw = 4.4
    h = 1.2 + 4.0 * talk
    L, R = P((-hw, y0 - sm * 1.2, z0 - 1.0)), P((hw, y0 - sm * 1.2, z0 - 1.0))
    top, bot = P((0.0, y0 - 0.8, z0 + 0.5)), P((0.0, y0 + h, z0 - h * 0.2))
    cr.new_path()
    cr.move_to(*L)
    cr.curve_to(lerp(L[0], top[0], 0.6), top[1], lerp(R[0], top[0], 0.6), top[1], *R)
    cr.curve_to(lerp(R[0], bot[0], 0.4), bot[1], lerp(L[0], bot[0], 0.4), bot[1], *L)
    cr.close_path()
    mp = Path(cr)
    B.flat(cr, mp, ELF_COLORS["mouth"], lw * 0.8, skin.line)
    if h > 3.0:
        cr.save()
        mp.add(cr)
        cr.clip()
        tl, tr = P((-hw * 0.6, y0 - 1.6, z0)), P((hw * 0.6, y0 - 1.6, z0))
        core.polygon(cr, [tl, tr, (tr[0], tr[1] + 2.6), (tl[0], tl[1] + 2.6)])
        core.src(cr, "#F2ECE6")
        cr.fill()
        cr.restore()
    return P((0.0, y0 + h * 0.4, z0))


def _ear(q, P, nz, s, back):
    """A long elf ear poking out of the hood (back pass: the far/behind ear; front pass: the
    near ear + the glowing sea-shell in its hollow). Returns the shell position (front pass)."""
    cr, pose, t = q.cr, q.pose, q.t
    facing = nz((s * 1.0, -0.2, 0.1))
    if back != (facing < 0.0):
        return None
    tw = 0.03 * math.sin(t * 1.1 + s)
    base = (s * 21.0, -2.0, -2.0)
    tip = (s * (42.0 + 2.0 * tw), -42.0 + 2.0 * tw, -12.0)
    pts = [P((base[0], base[1] - 10.0, base[2] + 2.0)), P(((base[0] + tip[0]) * 0.5 + s * 1.0, (base[1] + tip[1]) * 0.5 - 6.0, -8.0)),
           P(tip), P(((base[0] + tip[0]) * 0.5 + s * 4.0, (base[1] + tip[1]) * 0.5 + 6.0, -8.0)), P((base[0], base[1] + 9.0, base[2]))]
    es, eo = B.smooth_paths(cr, pts, q.lw, 0.9)
    if back:
        K.flat(q, es, eo, q.M["skin"], tone=0.4)
        return None
    q.shade(es, q.M["skin"], outline=eo, size=12, rim=0.8)
    # inner ear + the shell in its hollow, glowing
    ip = [P((base[0] + s * 2.0, base[1] - 5.0, base[2] + 3.0)), P(((base[0] + tip[0]) * 0.5 + s * 2.0, (base[1] + tip[1]) * 0.5 - 1.0, -6.0)),
          P((base[0] + s * 3.0, base[1] + 5.0, base[2] + 2.0))]
    B.detail_lines(cr, [ip], q.lw * 1.4, q.P(q.M["skin"]).shadow, 0.8, taper=(0.4, 1.0, 0.3))
    sc = P((base[0] + s * 1.5, base[1] + 1.0, base[2] + 4.0))
    g = clamp(pose.shells) * (0.85 + 0.15 * math.sin(t * 3.1 + s))
    if g > 0.02:
        B.sheen(cr, sc[0], sc[1], 9.0 * HS, 9.0 * HS, alpha=0.55 * g, color=ELF_COLORS["glow"])
    _shell(q, sc, P(tip))
    return sc


def _shell(q, sc, toward):
    """A tiny whelk shell, its spire pointing up the ear, pearly with a pink mouth."""
    cr = q.cr
    dx, dy = core.normalize((toward[0] - sc[0], toward[1] - sc[1]))
    nx, ny = -dy, dx
    r = 2.9 * HS
    pts = [(sc[0] + math.cos(a) * r * 1.1 * dx + math.sin(a) * r * 0.9 * nx, sc[1] + math.cos(a) * r * 1.1 * dy + math.sin(a) * r * 0.9 * ny)
           for a in (TAU * i / 10 for i in range(10))]
    pts.append((sc[0] + dx * r * 2.3, sc[1] + dy * r * 2.3))           # the spire
    ss, so = B.smooth_paths(cr, core.convex_hull(pts), q.lw * 0.6, 0.8)
    sp = K.flat(q, ss, so, q.M["shell"])
    if q.detail >= 1:
        cr.new_path()
        core.ellipse(cr, sc[0] - dx * r * 0.3 + nx * r * 0.2, sc[1] - dy * r * 0.3 + ny * r * 0.2, r * 0.5, r * 0.75,
                     math.atan2(dy, dx))
        core.src(cr, ELF_COLORS["shell_in"])
        cr.fill()
        whorls = [[(sc[0] + dx * r * k + nx * r * 0.7, sc[1] + dy * r * k + ny * r * 0.7),
                   (sc[0] + dx * r * (k + 0.3) - nx * r * 0.6, sc[1] + dy * r * (k + 0.3) - ny * r * 0.6)] for k in (0.6, 1.3)]
        B.detail_lines(cr, whorls, q.lw * 0.5, core.mix(ELF_COLORS["glow"], sp.line, 0.5), 0.8)


# ----------------------------------------------------------------------------------------
# sheets
# ----------------------------------------------------------------------------------------

def lineup():
    return [B.LineupItem("elf", lambda cr, x, y, sc: draw_elf(cr, x, y, sc, ElfPose(facing=1), t=0.4), 150.0)]


def sheet_items():
    items = []
    L = B.LIGHTS
    neutral = L["neutral"]

    def add(label, w, h, fn, group):
        items.append(B.SheetItem(label, w, h, fn, group))

    SC = 0.95
    for label, pose in (("3/4 left", ElfPose(facing=-1)), ("front", ElfPose(facing=0)), ("3/4 right", ElfPose(facing=1)),
                        ("standing, mirror", ElfPose(facing=-1, near=ElfArm("mirror"), look=(0.0, 0.8), head_nod=-0.5, glow=1.0)),
                        ("talking, hood down", ElfPose(facing=1, hood=0.0, talk=0.6, mood="skeptical"))):
        def fn(cr, p=pose):
            B.sheet_bg(cr, 220, 490, floor=460)
            rig = draw_elf(cr, 112, 475, SC, p.with_(blink=0.0), neutral, t=0.4)
            if rig.mirror:
                from .. import fx
                fx.glow(cr, rig.mirror[0], rig.mirror[1], 40, ELF_COLORS["glow"], 0.2)
        add(label, 220, 490, fn, "turnaround & S1")

    def seated(pose, light=neutral, name="neutral", tap=None):
        def fn(cr):
            B.sheet_bg(cr, 300, 490, name, floor=460)
            K.sheet_bench(cr, 150, 475, SC, w=230, light=light)
            p = pose
            if tap:
                core.src(cr, "#8a6a48")
                cr.rectangle(tap[0] - 34, tap[1] - 16, 68, 32)
                cr.fill()
                core.text(cr, "SELF-SERVICE", tap[0], tap[1] + 4, 9, core.SERIF, "#f0e2c0", align="center")
                p = p.with_(far=ElfArm("tap_sign", phase=0.25, screen=tap))
            rig = draw_elf(cr, 150, 475, SC, p.with_(blink=0.0), light, t=0.6)
            if rig.mirror:
                from .. import fx
                fx.glow(cr, rig.mirror[0], rig.mirror[1], 40, ELF_COLORS["glow"], 0.25)
        return fn
    add("S1 seated, scrolling the mirror", 300, 490, seated(ElfPose(facing=-1, sit=1.0, near=ElfArm("mirror"), look=(0.1, 0.9), head_nod=-0.5, glow=1.0),
                                                       L["washhouse"], "washhouse"), "turnaround & S1")
    add("S1 8.3: taps the plaque, never looks up", 300, 490, seated(ElfPose(facing=-1, sit=1.0, near=ElfArm("mirror"), look=(0.1, 0.9), head_nod=-0.5, glow=1.0),
                                                                L["washhouse"], "washhouse", tap=(232, 150)), "turnaround & S1")
    FS = 2.4
    for label, kw in (("aloof (bored)", dict(look=(0.0, 0.8), head_nod=-0.3, glow=1.0)), ("lit by the mirror", dict(look=(0.0, 0.9), head_nod=-0.5, glow=1.0)),
                      ("glance (raised)", dict(mood="skeptical", look=(-0.8, 0.0))), ("front", dict(facing=0)),
                      ("talking", dict(facing=1, talk=0.6, mood="skeptical"))):
        kw = dict(kw)
        facing = kw.pop("facing", -1)
        pose = ElfPose(facing=facing, blink=0.0, **kw)

        def fn(cr, p=pose):
            B.sheet_bg(cr, 240, 240, "washhouse")
            hx, hy = K.head_frame(draw_elf, p, FS, L["washhouse"])
            draw_elf(cr, 120 - hx, 120 - hy, FS, p, L["washhouse"], t=0.4)
        add(label, 240, 240, fn, "faces & light")

    def mirror_cell(cr):
        B.sheet_bg(cr, 240, 240, "washhouse")
        f = B.HandFrame(0.0, 0.0, 0.0, 1.0)
        cr.save()
        cr.translate(120, 196)
        elf_mirror(cr, f, 0.7, L["washhouse"], 1.0, size=2.4)
        cr.restore()
    add("the mirror (runes scroll)", 240, 240, mirror_cell, "faces & light")
    for name in ("washhouse", "tavern", "square", "neutral"):
        def fn(cr, name=name):
            B.sheet_bg(cr, 240, 240, name, floor=215)
            rig = draw_elf(cr, 120, 228, 0.42, ElfPose(facing=-1, near=ElfArm("mirror"), glow=1.0, look=(0, 0.8), head_nod=-0.4, blink=0.0), L[name], t=0.4)
            from .. import fx
            fx.glow(cr, rig.mirror[0], rig.mirror[1], 18, ELF_COLORS["glow"], 0.25)
        add(name, 240, 240, fn, "faces & light")
    return items
