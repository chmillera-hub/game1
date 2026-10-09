"""Dr. Malvo Sneakworth -- the evil genius rig.

    draw_villain(ctx, x, y, s, t, expr="neutral", look=(0,0), mouth=(0,0),
                 arms="rest", lean=0.0, blink=None, snake=None, seed=1)

(x, y) = centre of his waistline (desk-top level). At s=1 the top of the
bald dome is ~735 px above y, the torso+cape is ~700 px wide.  Everything
below y (to ~+140) is suit/cape meant to be hidden by a desk.

Use the helpers FACE / EYES / anchors() to aim looks and place emotes.
"""
import math

from .core import (hexc, clamp, lerp, smoothstep, noise1, hash01, blink_amount,
                   ellipse, circle, smooth_path, seg)
from . import snake as _snake

# ---------------------------------------------------------------------------
# colours (pre-resolved tuples: faster than hexc() per call)
# ---------------------------------------------------------------------------
INK = hexc("ink")
SKIN = hexc("skin")
SKIN_SH = hexc("skin_sh")
SKIN_DK = hexc("skin_dk")
SUIT = hexc("suit")
SUIT_DK = hexc("suit_dk")
CAPE = hexc("cape")
CAPE_HI = hexc("#2e1c3d")
CAPE_IN = hexc("cape_in")
CAPE_IN_DK = hexc("#7d0a28")
HAIR = hexc("hair")
HAIR_SH = hexc("#a7a7b8")
STACHE = hexc("mustache")
STACHE_HI = hexc("#5a3a2a")
GLOVE = hexc("glove")
GLOVE_SH = hexc("#c9c8da")
GOLD = hexc("monocle")
GOLD_DK = hexc("#a9822a")
WHITE = hexc("#ffffff")
SHIRT_SH = hexc("#d7d3e6")
PUPIL = hexc("#1a1022")
IRIS = hexc("#4a2a6e")
MOUTH_IN = hexc("#4a0f1e")
TONGUE = hexc("#e0566e")
TEETH_SH = hexc("#d9d4e4")
BLUSH = hexc("#ff6f8f")
VEIN = hexc("#d42a4a")
SWEAT = hexc("#8fd8ff")
GLOOM = hexc("#5a3a8a")

OUT_W = 6.0   # outer ink weight at s=1
IN_W = 4.0    # inner detail lines

# ---------------------------------------------------------------------------
# skeleton (waist-local coords, s=1, y up is negative)
# ---------------------------------------------------------------------------
NECK = (0.0, -340.0)          # head pivot
FACE_OFF = -178.0             # face origin (eye line centre) relative to NECK
SHOULDER = (204.0, -294.0)    # screen-right shoulder joint (mirror for left)
EYE_DX, EYE_DY = 62.0, -4.0   # eye centres relative to face origin
EYE_RX, EYE_RY = 37.0, 45.0
HAND_SCALE = 1.45

FACE = (NECK[0], NECK[1] + FACE_OFF)                                 # (0, -518)
EYES = ((FACE[0] - EYE_DX, FACE[1] + EYE_DY), (FACE[0] + EYE_DX, FACE[1] + EYE_DY))


def anchors(x=0.0, y=0.0, s=1.0):
    """World-space anchor points for scenes (ignores lean / head tilt)."""
    def P(px, py):
        return (x + px * s, y + py * s)
    return {
        "face": P(*FACE), "eye_l": P(*EYES[0]), "eye_r": P(*EYES[1]),
        "head_top": P(0, -735), "mouth": P(0, FACE[1] + 130),
        "brow": P(0, FACE[1] - 75), "dome": P(70, FACE[1] - 160),
        "temple_l": P(-150, FACE[1] - 110), "temple_r": P(150, FACE[1] - 110),
        "above_head": P(0, -800), "snake_head": P(*SNAKE_HEAD),
        "chest": P(0, -200), "hand_l_rest": P(-130, -10), "hand_r_rest": P(130, -10),
    }


# ---------------------------------------------------------------------------
# expressions
# ---------------------------------------------------------------------------
# suffix 1 = screen-left eye/brow, 2 = screen-right (monocle) eye/brow
_BASE = dict(
    by1=0.0, by2=0.0,        # brow vertical offset (neg = up)
    ba1=0.12, ba2=0.12,      # brow tilt: + inner end down (angry), - inner up (worried)
    bc1=0.35, bc2=0.35,      # brow arch
    ul1=0.24, ul2=0.20,      # upper lid 0 open .. 1 closed
    ll1=0.08, ll2=0.08,      # lower lid
    lt1=0.0, lt2=0.0,        # lid tilt (+ inner side lower)
    ps=1.0, shine=0.0, es=1.0,
    ex=0.0, ey=0.0,          # look bias
    mc=0.12, mw=1.0, mo=0.0, mt=0.0, msk=0.0, mx=0.0, tng=0.0,
    tilt=0.0, hy=0.0, shy=0.0,
    blush=0.0, vein=0.0, sweat=0.0, gloom=0.0, hair=0.0, mono=0.0, flutter=0.0,
    sneer=0.0,
)

VILLAIN_EXPR = {
    "neutral": {},
    "smug": dict(by1=4, by2=-16, ba1=0.18, ba2=0.05, bc2=0.6, ul1=0.48, ul2=0.42, ll1=0.12,
                 ll2=0.12, lt1=0.12, lt2=0.05, mc=0.65, msk=0.55, mw=0.95, tilt=-0.06,
                 hy=-4, sneer=0.4),
    "sneaky": dict(by1=14, by2=-30, ba1=0.42, ba2=-0.12, bc1=0.15, bc2=0.75, ul1=0.44,
                   ul2=0.36, ll1=0.2, ll2=0.18, lt1=0.28, lt2=0.12, ps=0.85, ex=0.55,
                   mc=0.75, msk=-0.55, mw=1.08, mt=0.35, mo=0.06, tilt=0.09, hy=8, shy=-12,
                   sneer=0.6),
    "evil_grin": dict(by1=10, by2=6, ba1=0.5, ba2=0.5, bc1=0.2, bc2=0.2, ul1=0.42, ul2=0.38,
                      ll1=0.22, ll2=0.22, lt1=0.38, lt2=0.38, ps=0.78, mc=1.15, mw=1.55,
                      mo=0.36, mt=1.0, tilt=-0.04, hy=-6, shy=-8, sneer=1.0),
    "excited": dict(by1=-28, by2=-30, ba1=-0.12, ba2=-0.12, bc1=0.6, bc2=0.6, ul1=0.0,
                    ul2=0.0, ll1=0.0, ll2=0.0, es=1.08, shine=0.5, mc=0.95, mw=1.18,
                    mo=0.55, mt=0.45, hy=-12, hair=0.45, shy=-10),
    "shocked": dict(by1=-48, by2=-52, ba1=-0.22, ba2=-0.22, bc1=0.8, bc2=0.8, ul1=0.0,
                    ul2=0.0, ll1=0.0, ll2=0.0, es=1.2, ps=0.5, mc=-0.35, mw=0.72, mo=0.9,
                    mt=0.35, hy=-18, hair=1.0, mono=1.0, shy=-14),
    "angry": dict(by1=14, by2=14, ba1=0.62, ba2=0.62, bc1=0.1, bc2=0.1, ul1=0.36, ul2=0.36,
                  ll1=0.16, ll2=0.16, lt1=0.38, lt2=0.38, ps=0.75, mc=-0.75, mw=1.05,
                  mo=0.26, mt=0.95, vein=1.0, hy=4, hair=0.3, sneer=0.7),
    "frustrated": dict(by1=10, by2=-6, ba1=0.42, ba2=0.18, ul1=0.5, ul2=0.4, ll1=0.14,
                       ll2=0.14, lt1=0.18, lt2=0.1, ps=0.85, mc=-0.65, msk=0.45, mw=0.92,
                       mo=0.14, mt=0.6, vein=0.6, sweat=0.7, tilt=0.05),
    "pleading": dict(by1=-16, by2=-18, ba1=-0.52, ba2=-0.52, bc1=0.25, bc2=0.25, ul1=0.04,
                     ul2=0.04, ll1=0.0, ll2=0.0, lt1=-0.12, lt2=-0.12, es=1.1, ps=1.45,
                     shine=1.0, mc=-0.4, mw=0.72, mo=0.18, blush=0.55, tilt=0.11, hy=6,
                     flutter=1.0, shy=-6),
    "defeated": dict(by1=10, by2=10, ba1=-0.38, ba2=-0.38, bc1=0.1, bc2=0.1, ul1=0.6,
                     ul2=0.58, ll1=0.06, ll2=0.06, lt1=-0.28, lt2=-0.28, ps=0.8, ey=0.45,
                     mc=-0.85, mw=0.8, mo=0.04, tilt=0.09, hy=24, gloom=1.0, shy=20,
                     hair=-0.6),
    "sheepish": dict(by1=-12, by2=-4, ba1=-0.32, ba2=-0.2, ul1=0.3, ul2=0.28, lt1=-0.1,
                     lt2=-0.1, ex=-0.55, ey=0.15, mc=0.3, msk=0.7, mw=0.9, mt=0.75, mo=0.08,
                     blush=0.85, sweat=1.0, tilt=0.12, hy=8, shy=-8),
    "hopeful": dict(by1=-22, by2=-22, ba1=-0.3, ba2=-0.3, bc1=0.45, bc2=0.45, ul1=0.04,
                    ul2=0.04, ll1=0.02, ll2=0.02, es=1.05, ps=1.22, shine=0.75, mc=0.45,
                    mw=0.82, mo=0.14, tilt=-0.06, hy=-8, blush=0.2),
    "happy": dict(by1=-14, by2=-14, ba1=-0.06, ba2=-0.06, bc1=0.55, bc2=0.55, ul1=0.26,
                  ul2=0.24, ll1=0.36, ll2=0.34, lt1=-0.05, lt2=-0.05, mc=1.0, mw=1.2,
                  mo=0.45, mt=0.45, blush=0.35, hy=-6, shine=0.3),
    "thinking": dict(by1=8, by2=-24, ba1=0.28, ba2=-0.08, bc2=0.6, ul1=0.3, ul2=0.06,
                     lt1=0.12, ex=0.45, ey=-0.6, mc=-0.12, msk=0.55, mw=0.68, mx=8,
                     tilt=0.08),
    "typing_focus": dict(by1=10, by2=6, ba1=0.32, ba2=0.28, ul1=0.42, ul2=0.38, ll1=0.16,
                         ll2=0.16, lt1=0.14, lt2=0.12, ps=0.9, ey=0.2, mc=-0.05, mw=0.62,
                         msk=0.35, mx=6, tng=1.0, hy=6, shy=-4),
}
EXPRESSIONS = list(VILLAIN_EXPR)

_cache = {}
_warned = set()


def _warn(kind, name):
    if (kind, name) not in _warned:
        _warned.add((kind, name))
        import sys
        print(f"[villain] unknown {kind} '{name}', using default", file=sys.stderr)


def _params(name):
    p = _cache.get(name)
    if p is None:
        if name not in VILLAIN_EXPR:
            _warn("expr", name)
        p = dict(_BASE)
        p.update(VILLAIN_EXPR.get(name, {}))
        _cache[name] = p
    return p


def resolve_expr(expr):
    if isinstance(expr, (tuple, list)):
        a, b, k = expr
        pa, pb = _params(a), _params(b)
        k = clamp(float(k))
        if k <= 0.0:
            return dict(pa)
        if k >= 1.0:
            return dict(pb)
        return {key: pa[key] + (pb[key] - pa[key]) * k for key in pa}
    return dict(_params(expr))


# ---------------------------------------------------------------------------
# arm poses (screen coords relative to waist, s=1).  'a' = screen-left arm,
# 'b' = screen-right arm.  e=elbow, w=wrist, ha=hand angle (direction the
# fingers point), cu=finger curl, ix=index curl, th=thumb angle offset,
# sp=finger spread, pm=palm facing viewer, hs=hand scale, tf=thumb side.
# ---------------------------------------------------------------------------
def _arm(ex, ey, wx, wy, ha, cu=0.3, ix=None, th=0.0, sp=0.5, pm=0.0, hs=1.0, tf=1.0):
    return dict(ex=ex, ey=ey, wx=wx, wy=wy, ha=ha, cu=cu, ix=cu if ix is None else ix,
                th=th, sp=sp, pm=pm, hs=hs, tf=tf)


def _mirror(a):
    m = dict(a)
    m["ex"], m["wx"] = -a["ex"], -a["wx"]
    m["ha"] = math.pi - a["ha"]
    m["tf"] = -a["tf"]
    return m


def _pose(a, b=None, shy=0.0, hdy=0.0, tilt=0.0):
    return dict(a=a, b=b if b is not None else _mirror(a), shy=shy, hdy=hdy, tilt=tilt)


_REST_A = _arm(-262, -140, -152, -52, 0.06, cu=0.3, th=0.2, sp=0.45)
_REST_B = _mirror(_REST_A)

ARM_POSES = {
    "rest": _pose(_REST_A),
    "type": _pose(_arm(-256, -122, -112, -70, 1.0, cu=0.45, th=0.1, sp=0.7)),
    "steeple": _pose(_arm(-222, -108, -94, -186, -0.9, cu=0.0, th=0.35, sp=0.05),
                     shy=-6),
    "rub": _pose(_arm(-206, -104, -46, -214, -0.32, cu=0.35, th=0.2, sp=0.25), shy=-10,
                 hdy=4),
    "point": _pose(_REST_A, _arm(300, -268, 358, -390, -1.0, cu=1.0, ix=0.0, th=0.0,
                                 sp=0.2, tf=-1)),
    "fist": _pose(_arm(-262, -140, -150, -52, 0.06, cu=1.0, th=0.0, sp=0.2),
                  _arm(314, -236, 306, -424, -1.57, cu=1.0, th=0.0, sp=0.2, tf=-1), shy=-6),
    "facepalm": _pose(_arm(-182, -246, -156, -456, -0.52, cu=0.05, th=0.6, sp=1.0, hs=1.65),
                      _REST_B, hdy=10, tilt=0.06),
    "beg": _pose(_arm(-166, -134, -30, -258, -1.36, cu=0.12, th=0.1, sp=0.0, hs=1.15),
                 shy=-14, hdy=6),
    "shrug": _pose(_arm(-240, -150, -350, -224, math.pi + 0.28, cu=0.08, th=-0.2, sp=0.8,
                        pm=1.0, tf=-1), shy=-26, hdy=10),
    "chin": _pose(_arm(-224, -112, 52, -122, 0.12, cu=0.62, th=0.0, sp=0.3),
                  _arm(160, -152, 72, -306, -2.2, cu=0.75, ix=0.1, th=0.5, sp=0.3, tf=1)),
    "present": _pose(_arm(-306, -206, -396, -276, math.pi + 0.42, cu=0.05, th=-0.2, sp=0.9,
                          pm=1.0, tf=-1), _REST_B),
    "slump": _pose(_arm(-250, -62, -196, 6, 1.36, cu=0.12, th=0.1, sp=0.2), shy=22, hdy=12),
}
ARM_NAMES = list(ARM_POSES)


def _blend_arm(a, b, k):
    out = {key: a[key] + (b[key] - a[key]) * k for key in a if key != "tf"}
    out["tf"] = a["tf"] if k < 0.5 else b["tf"]
    return out


def _arm_weights(arms):
    if isinstance(arms, (tuple, list)):
        a, b, k = arms
        k = clamp(float(k))
        w = {}
        w[a] = w.get(a, 0.0) + (1 - k)
        w[b] = w.get(b, 0.0) + k
        return w
    return {arms: 1.0}


def resolve_arms(arms, t):
    """name | (from,to,blend) -> (arm_a, arm_b, shy, hdy, tilt) with animation applied."""
    for nm in (arms[:2] if isinstance(arms, (tuple, list)) else (arms,)):
        if nm not in ARM_POSES:
            _warn("arms", nm)
    if isinstance(arms, (tuple, list)):
        pa_, pb_, k = arms
        k = clamp(float(k))
        pa, pb = ARM_POSES.get(pa_, ARM_POSES["rest"]), ARM_POSES.get(pb_, ARM_POSES["rest"])
        A = _blend_arm(pa["a"], pb["a"], k)
        B = _blend_arm(pa["b"], pb["b"], k)
        shy = lerp(pa["shy"], pb["shy"], k)
        hdy = lerp(pa["hdy"], pb["hdy"], k)
        tilt = lerp(pa["tilt"], pb["tilt"], k)
    else:
        P = ARM_POSES.get(arms, ARM_POSES["rest"])
        A, B = dict(P["a"]), dict(P["b"])
        shy, hdy, tilt = P["shy"], P["hdy"], P["tilt"]
    w = _arm_weights(arms)
    # --- procedural animation layered on top -------------------------------
    wt = w.get("type", 0.0)
    if wt > 0:
        for arm, ph in ((A, 0.0), (B, 2.1)):
            tap = max(0.0, math.sin(t * 15.0 + ph)) ** 2
            arm["wy"] -= wt * 10 * tap
            arm["wx"] += wt * 6 * math.sin(t * 3.1 + ph)
            arm["cu"] += wt * 0.25 * math.sin(t * 19 + ph * 2)
            arm["ix"] += wt * 0.35 * math.sin(t * 23 + ph)
    wr = w.get("rub", 0.0)
    if wr > 0:
        c, sn = math.cos(t * 8.0), math.sin(t * 8.0)
        A["wx"] += wr * 16 * sn
        A["wy"] += wr * 6 * c
        B["wx"] -= wr * 16 * sn
        B["wy"] -= wr * 6 * c
        A["ha"] += wr * 0.12 * c
        B["ha"] -= wr * 0.12 * c
    wf = w.get("fist", 0.0)
    if wf > 0:
        B["wx"] += wf * 7 * math.sin(t * 21)
        B["wy"] += wf * 5 * math.sin(t * 21 + 1.3)
        B["ex"] += wf * 3 * math.sin(t * 21)
    wb = w.get("beg", 0.0)
    if wb > 0:
        d = wb * 2.5 * math.sin(t * 17)
        A["wx"] += d
        B["wx"] += d
        A["wy"] += wb * 2 * math.sin(t * 2.3)
        B["wy"] += wb * 2 * math.sin(t * 2.3)
    wp = w.get("point", 0.0)
    if wp > 0:
        jab = math.sin(t * 4.0)
        B["wx"] += wp * 5 * jab
        B["wy"] -= wp * 5 * jab
    ws = w.get("steeple", 0.0)
    if ws > 0:  # villainous finger tapping
        tap = max(0.0, math.sin(t * 6.0)) * ws
        A["sp"] += 0.25 * tap
        B["sp"] += 0.25 * tap
    wc = w.get("chin", 0.0)
    if wc > 0:  # stroking the goatee
        B["wy"] += wc * 6 * math.sin(t * 3.0)
        B["ha"] += wc * 0.06 * math.sin(t * 3.0)
    return A, B, shy, hdy, tilt


# ---------------------------------------------------------------------------
# small drawing utils
# ---------------------------------------------------------------------------
def _poly(ctx, pts):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.close_path()


def _rgba(c, a):
    return (c[0], c[1], c[2], c[3] * a)


def _fs(ctx, fillc, w=OUT_W, inkc=INK):
    """fill current path with fillc then stroke with ink."""
    ctx.set_source_rgba(*fillc)
    ctx.fill_preserve()
    ctx.set_source_rgba(*inkc)
    ctx.set_line_width(w)
    ctx.stroke()


# ---------------------------------------------------------------------------
# body parts
# ---------------------------------------------------------------------------
def _cape_back(ctx, shy):
    sy = shy * 0.6
    # outer cape behind everything
    ctx.move_to(-150, -352 + sy)
    ctx.curve_to(-230, -350 + sy, -278, -330 + sy, -296, -270 + sy)
    ctx.curve_to(-316, -190, -322, -60, -328, 150)
    ctx.line_to(328, 150)
    ctx.curve_to(322, -60, 316, -190, 296, -270 + sy)
    ctx.curve_to(278, -330 + sy, 230, -350 + sy, 150, -352 + sy)
    ctx.close_path()
    _fs(ctx, CAPE)
    # crimson lining visible at the inner front edges
    for sx in (-1, 1):
        ctx.move_to(sx * 240, -296 + sy)
        ctx.curve_to(sx * 270, -230, sx * 282, -100, sx * 290, 150)
        ctx.line_to(sx * 206, 150)
        ctx.line_to(sx * 210, -100)
        ctx.close_path()
        ctx.set_source_rgba(*CAPE_IN)
        ctx.fill_preserve()
        ctx.set_source_rgba(*INK)
        ctx.set_line_width(IN_W)
        ctx.stroke()
        # lining fold shadow
        ctx.move_to(sx * 256, -200 + sy * 0.5)
        ctx.curve_to(sx * 266, -120, sx * 270, -20, sx * 272, 150)
        ctx.line_to(sx * 258, 150)
        ctx.curve_to(sx * 254, -20, sx * 250, -120, sx * 256, -200 + sy * 0.5)
        ctx.set_source_rgba(*CAPE_IN_DK)
        ctx.fill()


def _collar(ctx, shy):
    sy = shy * 0.6
    for sx in (-1, 1):
        # black outer collar
        ctx.move_to(sx * 72, -350 + sy)
        ctx.curve_to(sx * 140, -352 + sy, sx * 196, -346 + sy, sx * 218, -330 + sy)
        ctx.curve_to(sx * 248, -420 + sy, sx * 258, -520 + sy, sx * 276, -622 + sy)
        ctx.curve_to(sx * 222, -578 + sy, sx * 158, -520 + sy, sx * 108, -470 + sy)
        ctx.curve_to(sx * 86, -420 + sy, sx * 76, -390 + sy, sx * 72, -350 + sy)
        ctx.close_path()
        _fs(ctx, CAPE)
        # crimson inner face
        ctx.move_to(sx * 92, -360 + sy)
        ctx.curve_to(sx * 150, -360 + sy, sx * 186, -356 + sy, sx * 204, -342 + sy)
        ctx.curve_to(sx * 230, -420 + sy, sx * 240, -510 + sy, sx * 254, -594 + sy)
        ctx.curve_to(sx * 212, -556 + sy, sx * 156, -506 + sy, sx * 118, -464 + sy)
        ctx.curve_to(sx * 100, -420 + sy, sx * 94, -392 + sy, sx * 92, -360 + sy)
        ctx.close_path()
        ctx.set_source_rgba(*CAPE_IN)
        ctx.fill()
        # one shadow tone: inner fold near the neck
        ctx.move_to(sx * 92, -360 + sy)
        ctx.curve_to(sx * 96, -400 + sy, sx * 104, -430 + sy, sx * 118, -464 + sy)
        ctx.curve_to(sx * 150, -500 + sy, sx * 190, -530 + sy, sx * 230, -560 + sy)
        ctx.curve_to(sx * 180, -500 + sy, sx * 140, -440 + sy, sx * 128, -380 + sy)
        ctx.close_path()
        ctx.set_source_rgba(*CAPE_IN_DK)
        ctx.fill()


def _torso(ctx, shy, breath, snake_on):
    sy = shy
    ctx.save()
    ctx.scale(1.0, 1.0 + 0.008 * breath)
    # suit body
    def body():
        ctx.move_to(-70, -354 + sy)
        ctx.curve_to(-130, -352 + sy, -184, -346 + sy, -214, -326 + sy)
        ctx.curve_to(-240, -308 + sy, -244, -270 + sy, -238, -232)
        ctx.curve_to(-226, -150, -208, -70, -204, 150)
        ctx.line_to(204, 150)
        ctx.curve_to(208, -70, 226, -150, 238, -232)
        ctx.curve_to(244, -270 + sy, 240, -308 + sy, 214, -326 + sy)
        ctx.curve_to(184, -346 + sy, 130, -352 + sy, 70, -354 + sy)
        ctx.close_path()
    body()
    ctx.set_source_rgba(*SUIT)
    ctx.fill()
    # one shadow tone: strip down the right side
    _poly(ctx, [(214, -326 + sy), (240, -308 + sy), (244, -270 + sy), (238, -232),
                (226, -150), (208, -70), (204, 150), (180, 150), (184, -70), (202, -150),
                (214, -232), (218, -276 + sy), (196, -326 + sy)])
    ctx.set_source_rgba(*SUIT_DK)
    ctx.fill()
    # shirt V
    _poly(ctx, [(-66, -356 + sy), (66, -356 + sy), (0, -170)])
    ctx.set_source_rgba(*WHITE)
    ctx.fill_preserve()
    ctx.set_source_rgba(*INK)
    ctx.set_line_width(IN_W)
    ctx.stroke()
    # shirt shadow under the chin
    ellipse(ctx, 0, -350 + sy, 60, 26)
    ctx.set_source_rgba(*SHIRT_SH)
    ctx.fill()
    # skinny crimson tie
    ctx.move_to(-13, -318 + sy * 0.8)
    ctx.line_to(13, -318 + sy * 0.8)
    ctx.line_to(9, -300 + sy * 0.8)
    ctx.line_to(16, -214)
    ctx.line_to(0, -192)
    ctx.line_to(-16, -214)
    ctx.line_to(-9, -300 + sy * 0.8)
    ctx.close_path()
    _fs(ctx, CAPE_IN, IN_W)
    # lapels
    for sx in (-1, 1):
        _poly(ctx, [(sx * 66, -356 + sy), (sx * 122, -344 + sy), (sx * 108, -268),
                    (sx * 140, -256), (sx * 18, -150), (0, -168), (sx * 8, -182)])
        _fs(ctx, SUIT_DK, IN_W)
    # gold buttons
    for by_ in (-112, -48):
        circle(ctx, 0, by_, 9)
        _fs(ctx, GOLD, 3)
    # body outline
    body()
    ctx.set_source_rgba(*INK)
    ctx.set_line_width(OUT_W)
    ctx.stroke()
    # center seam line below the V
    ctx.move_to(0, -168)
    ctx.line_to(0, 150)
    ctx.set_line_width(3)
    ctx.stroke()
    ctx.restore()


# ---------------------------------------------------------------------------
# head
# ---------------------------------------------------------------------------
_HEAD_PTS = [(0, -216), (90, -198), (144, -142), (162, -62), (158, 10), (146, 70),
             (112, 130), (58, 170), (0, 188), (-58, 170), (-112, 130), (-146, 70),
             (-158, 10), (-162, -62), (-144, -142), (-90, -198)]
MOUTH_Y = 130.0


def _head_path(ctx, jaw, dx=0.0, dy=0.0):
    pts = []
    for x, y in _HEAD_PTS:
        if y > 70:
            y += jaw * (y - 70) / 118
        pts.append((x + dx, y + dy))
    smooth_path(ctx, pts, closed=True)


def _hair_tuft(ctx, sx, t, hair, seed):
    """Wild white side tuft: curved flame-like wisps fanning out above the ear."""
    cx, cy = sx * 148, -50
    angs = (-2.0, -1.4, -0.84, -0.3, 0.3)
    lens = (66, 92, 98, 86, 60)

    def P(a, r):
        aa = a if sx > 0 else math.pi - a
        return (cx + math.cos(aa) * r, cy + math.sin(aa) * r)

    tips = []
    for i, (a, L) in enumerate(zip(angs, lens)):
        L = L * (1 + 0.32 * hair) + noise1(t * 1.4 + i * 1.7, seed + i) * 5
        if hair > 0:
            a = lerp(a, -1.57, 0.22 * hair)
        else:
            a = a - hair * 0.55 * (i + 1) / 5
        a += noise1(t * 0.9 + i, seed + 30 + i) * 0.05
        tips.append((a, L))
    ctx.move_to(*P(-2.45, 30))
    for i, (a, L) in enumerate(tips):
        C1 = P(a - 0.34, L * 0.62)
        ctx.curve_to(C1[0], C1[1], C1[0], C1[1], *P(a, L))
        a2 = (a + tips[i + 1][0]) / 2 if i + 1 < len(tips) else a + 0.5
        C2 = P(a + 0.04, L * 0.6)
        V = P(a2, 34 if i + 1 < len(tips) else 24)
        ctx.curve_to(C2[0], C2[1], C2[0], C2[1], *V)
    ctx.line_to(sx * 146, 22)
    ctx.line_to(sx * 128, -100)
    ctx.close_path()
    ctx.set_source_rgba(*HAIR)
    ctx.fill_preserve()
    ctx.set_source_rgba(*INK)
    ctx.set_line_width(OUT_W - 1)
    ctx.stroke()
    # shadow tone strands
    ctx.set_source_rgba(*HAIR_SH)
    ctx.set_line_width(5)
    for a, L in tips[1:4]:
        ctx.move_to(*P(a + 0.15, 22))
        C = P(a - 0.1, L * 0.45)
        ctx.curve_to(C[0], C[1], C[0], C[1], *P(a - 0.05, L * 0.7))
    ctx.stroke()


def _ear(ctx, sx):
    ellipse(ctx, sx * 156, 18, 24, 34, sx * 0.15)
    _fs(ctx, SKIN, OUT_W - 1)
    ctx.move_to(sx * 150, 2)
    ctx.curve_to(sx * 168, 6, sx * 170, 30, sx * 156, 38)
    ctx.set_source_rgba(*SKIN_DK)
    ctx.set_line_width(4)
    ctx.stroke()


def _brow(ctx, sx, cx, by, ba, bc, flutter_bob):
    """Thick tapered villain brow. sx = side, ba + = inner end down."""
    inner_x = cx - sx * 50
    L = 112
    base_y = -76 + by + flutter_bob
    top, bot = [], []
    n = 12
    for i in range(n + 1):
        u = i / n
        x = inner_x + sx * u * L
        arch = -bc * 22 * math.sin(u * math.pi)
        tiltv = ba * 60 * (0.5 - u)          # inner (u=0) lower if ba>0
        flick = -10 * u ** 3                  # outer end flicks up
        y = base_y + arch + tiltv + flick
        th = lerp(24, 6, u ** 1.15)
        top.append((x, y - th * 0.55))
        bot.append((x, y + th * 0.45))
    ctx.move_to(*top[0])
    for p in top[1:]:
        ctx.line_to(*p)
    for p in reversed(bot):
        ctx.line_to(*p)
    ctx.close_path()
    ctx.set_source_rgba(*STACHE)
    ctx.fill_preserve()
    ctx.set_source_rgba(*INK)
    ctx.set_line_width(3)
    ctx.stroke()
    # highlight strand
    ctx.move_to(*top[2])
    for p in top[3:8]:
        ctx.line_to(p[0], p[1] + 6)
    ctx.set_source_rgba(*STACHE_HI)
    ctx.set_line_width(3)
    ctx.stroke()


def _eye(ctx, sx, cx, cy, rx, ry, ul, ll, lt, ps, shine, lookx, looky, flutter):
    """Sclera + pupil + skin lids, clipped to the eye. lt + = inner side lower."""
    ctx.save()
    ellipse(ctx, cx, cy, rx, ry)
    ctx.clip()
    ctx.set_source_rgba(*WHITE)
    ctx.paint()
    # lid geometry first: pupils stay visible inside a squint
    lt_s = lt * (-sx)          # inner side = toward face centre
    dy = math.tan(lt_s) * rx
    top_y = cy - ry + 2 * ry * ul
    bot_y = cy + ry - 2 * ry * ll
    sag = ry * 0.16 * (1 - abs(ul - 0.5) * 1.2)
    # pupil
    pr = 17.0 * ps
    px = cx + lookx * rx * 0.46
    py = cy + looky * ry * 0.38
    if ul < 0.95:
        lo = top_y + sag + pr * 0.5
        hi = bot_y - pr * 0.25
        py = (lo + hi) * 0.5 if lo > hi else clamp(py, lo, hi)
    if shine > 0.05:
        ctx.set_source_rgba(*IRIS)
        circle(ctx, px, py, pr * (1 + 0.28 * shine))
        ctx.fill()
    ctx.set_source_rgba(*PUPIL)
    circle(ctx, px, py, pr)
    ctx.fill()
    ctx.set_source_rgba(*WHITE)
    hr = 4.8 * ps + 1.5 + shine * 4
    circle(ctx, px - pr * 0.38, py - pr * 0.42, hr)
    ctx.fill()
    circle(ctx, px + pr * 0.4, py + pr * 0.36, hr * 0.42)
    ctx.fill()
    if shine > 0.4:
        circle(ctx, px + pr * 0.05, py - pr * 0.62, hr * 0.32)
        ctx.fill()
        # wet lower rim glint
        ctx.set_source_rgba(1, 1, 1, 0.8 * shine)
        ctx.set_line_width(3)
        ctx.arc(cx, cy + 4, ry * 0.86, 0.6, math.pi - 0.6)
        ctx.stroke()
    # lids
    ctx.set_source_rgba(*SKIN)
    ctx.move_to(cx - rx - 3, top_y - dy)
    ctx.curve_to(cx - rx * 0.4, top_y - dy * 0.4 + sag, cx + rx * 0.4, top_y + dy * 0.4 + sag,
                 cx + rx + 3, top_y + dy)
    ctx.line_to(cx + rx + 3, cy - ry - 4)
    ctx.line_to(cx - rx - 3, cy - ry - 4)
    ctx.close_path()
    ctx.fill()
    if ll > 0.01:
        ctx.move_to(cx - rx - 3, bot_y)
        ctx.curve_to(cx - rx * 0.4, bot_y - ry * 0.14, cx + rx * 0.4, bot_y - ry * 0.14,
                     cx + rx + 3, bot_y)
        ctx.line_to(cx + rx + 3, cy + ry + 4)
        ctx.line_to(cx - rx - 3, cy + ry + 4)
        ctx.close_path()
        ctx.fill()
    ctx.set_source_rgba(*INK)
    if ul >= 1.0 - ll - 0.01:   # closed: lash line at the seam
        ctx.set_line_width(IN_W + 2.5)
        ctx.move_to(cx - rx - 3, bot_y + 1)
        ctx.curve_to(cx - rx * 0.4, bot_y + ry * 0.12, cx + rx * 0.4, bot_y + ry * 0.12,
                     cx + rx + 3, bot_y + 1)
        ctx.stroke()
    elif ul > 0.02:
        ctx.set_line_width(IN_W + 2)
        ctx.move_to(cx - rx - 3, top_y - dy)
        ctx.curve_to(cx - rx * 0.4, top_y - dy * 0.4 + sag, cx + rx * 0.4, top_y + dy * 0.4 + sag,
                     cx + rx + 3, top_y + dy)
        ctx.stroke()
    if ll > 0.06 and ul < 1 - ll - 0.03:
        ctx.set_line_width(IN_W - 1)
        ctx.move_to(cx - rx - 3, bot_y)
        ctx.curve_to(cx - rx * 0.4, bot_y - ry * 0.14, cx + rx * 0.4, bot_y - ry * 0.14,
                     cx + rx + 3, bot_y)
        ctx.stroke()
    ctx.restore()
    # outline
    ellipse(ctx, cx, cy, rx, ry)
    ctx.set_source_rgba(*INK)
    ctx.set_line_width(IN_W + 0.5)
    ctx.stroke()
    # fluttery lashes
    if flutter > 0.3 and ul < 0.5:
        ctx.set_line_width(4.5)
        for a in (0.55, 0.9):
            ang = -math.pi / 2 + sx * a
            bx, by_ = cx + math.cos(ang) * rx, cy + math.sin(ang) * ry
            ctx.move_to(bx, by_)
            ctx.line_to(bx + math.cos(ang) * 15 + sx * 3, by_ + math.sin(ang) * 15 - 3)
        ctx.stroke()


def _mouth(ctx, p, mo, wide, t):
    """Mouth with lip-sync layered on top of the expression's shape."""
    mc, msk, mt = p["mc"], p["msk"], p["mt"]
    mx = p["mx"]
    base = MOUTH_Y
    hw = 48 * p["mw"] * (1 + 0.24 * wide) * (1 - 0.12 * mo * (wide < 0))
    lift = mc * 15
    yl = base - lift + msk * 11
    yr = base - lift - msk * 11
    xl, xr = mx - hw, mx + hw
    um = base + mc * 7 - mo * 5
    open_px = mo * (50 + 10 * (-min(0.0, wide)))
    lm = base + mc * 12 + open_px
    # upper lip: corner -> corner
    def upper(move=True):
        if move:
            ctx.move_to(xl, yl)
        ctx.curve_to(xl + hw * 0.55, um + mc * 2, xr - hw * 0.55, um + mc * 2, xr, yr)

    def lower():
        ctx.curve_to(xr - hw * 0.35, lm + 2, xl + hw * 0.35, lm + 2, xl, yl)

    if mo > 0.035 or mt > 0.05:
        if mo <= 0.035:
            lm = um + 4 + mt * 14
        upper()
        lower()
        ctx.close_path()
        ctx.set_source_rgba(*MOUTH_IN)
        ctx.fill_preserve()
        ctx.save()
        ctx.clip()
        # tongue
        if open_px > 14:
            ctx.set_source_rgba(*TONGUE)
            ellipse(ctx, mx + 6, lm + 4, hw * 0.55, open_px * 0.42)
            ctx.fill()
        # teeth
        tu = 6 + 14 * mt
        if mt > 0.05 or mo > 0.25:
            ctx.set_source_rgba(*WHITE)
            ctx.set_line_width(tu * 2)
            upper()
            ctx.stroke()
            if mt > 0.3:
                ctx.set_line_width(2 * 12 * mt)
                ctx.move_to(xr, yr)
                lower()
                ctx.stroke()
            # tooth gaps
            ctx.set_source_rgba(*TEETH_SH)
            ctx.set_line_width(2.5)
            nt = 6 if mt > 0.5 else 4
            for k in range(1, nt):
                u = k / nt
                xx = lerp(xl, xr, u)
                yy = lerp(yl, yr, u) + (um - (yl + yr) / 2) * 1.6 * math.sin(u * math.pi)
                ctx.move_to(xx, yy - 6)
                ctx.line_to(xx, yy + tu)
                if mt > 0.3:
                    ly = lerp(yl, yr, u) + (lm - (yl + yr) / 2) * 1.5 * math.sin(u * math.pi)
                    ctx.move_to(xx, ly + 4)
                    ctx.line_to(xx, ly - 12 * mt)
            ctx.stroke()
        ctx.restore()
        upper()
        lower()
        ctx.close_path()
        ctx.set_source_rgba(*INK)
        ctx.set_line_width(IN_W + 0.5)
        ctx.stroke()
    else:
        upper()
        ctx.set_source_rgba(*INK)
        ctx.set_line_width(IN_W + 1)
        ctx.stroke()
    # corner creases
    ctx.set_source_rgba(*INK)
    ctx.set_line_width(3)
    for sx, cxp, cyp in ((-1, xl, yl), (1, xr, yr)):
        ctx.move_to(cxp + sx * 2, cyp - 9 + mc * 2)
        ctx.curve_to(cxp + sx * 9, cyp - 4, cxp + sx * 9, cyp + 4, cxp + sx * 3, cyp + 8)
    ctx.stroke()
    # concentration tongue poking out of the corner
    if p["tng"] > 0.05:
        k = p["tng"]
        wig = math.sin(t * 5) * 2
        ellipse(ctx, xr + 6 * k, yr + 8 + wig, 9 * k + 1, 12 * k + 1, -0.5)
        ctx.set_source_rgba(*TONGUE)
        ctx.fill_preserve()
        ctx.set_source_rgba(*INK)
        ctx.set_line_width(3)
        ctx.stroke()
    return xl, yl, xr, yr, lm


def _mustache(ctx, mx, yl, yr, base, t):
    """Thin curly villain mustache following the mouth corners."""
    ctx.set_source_rgba(*STACHE)
    ctx.set_line_cap(1)
    for sx, yc in ((-1, yl), (1, yr)):
        lift = (yc - base) * 0.5
        pts = [(mx + sx * 2, 100), (mx + sx * 24, 102 + lift * 0.4),
               (mx + sx * 48, 103 + lift * 0.8), (mx + sx * 62, 95 + lift),
               (mx + sx * 64, 83 + lift), (mx + sx * 55, 79 + lift), (mx + sx * 51, 86 + lift)]
        smooth_path(ctx, pts[:4])
        ctx.set_line_width(9)
        ctx.stroke()
        smooth_path(ctx, pts[2:])
        ctx.set_line_width(5)
        ctx.stroke()
    ellipse(ctx, mx, 99, 10, 5)
    ctx.fill()


def _goatee(ctx, jaw, mx):
    y0 = 168 + jaw * 0.85
    ctx.move_to(mx - 22, y0)
    ctx.curve_to(mx - 10, y0 - 6, mx + 10, y0 - 6, mx + 22, y0)
    ctx.curve_to(mx + 18, y0 + 24, mx + 12, y0 + 40, mx + 6, y0 + 58)
    ctx.curve_to(mx - 4, y0 + 40, mx - 16, y0 + 24, mx - 22, y0)
    ctx.close_path()
    ctx.set_source_rgba(*STACHE)
    ctx.fill_preserve()
    ctx.set_source_rgba(*INK)
    ctx.set_line_width(3)
    ctx.stroke()
    ctx.move_to(mx - 6, y0 + 6)
    ctx.curve_to(mx - 2, y0 + 20, mx + 2, y0 + 30, mx + 4, y0 + 42)
    ctx.set_source_rgba(*STACHE_HI)
    ctx.set_line_width(3)
    ctx.stroke()


def _nose(ctx, nx):
    pts = [(nx - 7, -6), (nx - 12, 30), (nx - 26, 60), (nx - 22, 80), (nx - 8, 90),
           (nx + 4, 95), (nx + 18, 86), (nx + 27, 64), (nx + 12, 30), (nx + 7, -6)]
    smooth_path(ctx, pts, closed=True)
    ctx.set_source_rgba(*SKIN)
    ctx.fill()
    # shadow side
    ctx.move_to(nx + 6, 4)
    ctx.curve_to(nx + 16, 36, nx + 32, 60, nx + 24, 78)
    ctx.curve_to(nx + 16, 90, nx + 8, 94, nx + 2, 94)
    ctx.curve_to(nx + 14, 74, nx + 14, 40, nx + 6, 4)
    ctx.set_source_rgba(*SKIN_SH)
    ctx.fill()
    # outline: sides + bulb only (top blends into the face)
    smooth_path(ctx, pts[1:-1])
    ctx.set_source_rgba(*INK)
    ctx.set_line_width(IN_W + 0.5)
    ctx.stroke()
    # nostrils
    ctx.set_line_width(3.5)
    for sx in (-1, 1):
        ctx.move_to(nx + sx * 19, 72)
        ctx.curve_to(nx + sx * 13, 76, nx + sx * 11, 80, nx + sx * 13, 84)
    ctx.stroke()
    # highlight
    ellipse(ctx, nx - 9, 60, 6, 4, -0.4)
    ctx.set_source_rgba(1, 1, 1, 0.55)
    ctx.fill()


def _monocle(ctx, cx, cy, r, drop, t, seed, glint_on=True):
    """Gold monocle ring + chain. Returns ring centre."""
    if drop > 0.001:
        sw = math.sin(t * 5.5) * 0.35 * drop
        hx, hy = cx + 66 * drop, cy + 150 * drop
        mx_ = lerp(cx, hx + math.sin(sw) * 20, smoothstep(drop))
        my_ = lerp(cy, hy, smoothstep(drop))
        rot = sw
    else:
        mx_, my_, rot = cx, cy, 0.0
    # chain: from ring's lower-right, sagging down to the collar
    ax, ay = mx_ + r * 0.7, my_ + r * 0.72
    ctx.move_to(ax, ay)
    ctx.curve_to(ax + 30, ay + 70, ax + 10, 170, 100, 196)
    ctx.set_source_rgba(*INK)
    ctx.set_line_width(7)
    ctx.set_dash([1, 9], 0)
    ctx.stroke_preserve()
    ctx.set_source_rgba(*GOLD)
    ctx.set_line_width(4.5)
    ctx.stroke()
    ctx.set_dash([], 0)
    # glass tint
    circle(ctx, mx_, my_, r)
    ctx.set_source_rgba(0.8, 0.95, 1.0, 0.14)
    ctx.fill()
    # static highlight arc
    ctx.set_source_rgba(1, 1, 1, 0.7)
    ctx.set_line_width(4)
    ctx.arc(mx_, my_, r * 0.74, math.pi * 1.08, math.pi * 1.42)
    ctx.stroke()
    # occasional glint sweep
    if glint_on:
        period = 4.6
        k = math.floor(t / period)
        g0 = k * period + hash01(k, seed + 41) * period * 0.6
        gp = (t - g0) / 0.42
        if 0 <= gp <= 1:
            ctx.save()
            circle(ctx, mx_, my_, r)
            ctx.clip()
            off = lerp(-r * 1.6, r * 1.6, gp)
            ctx.translate(mx_ + off, my_)
            ctx.rotate(0.6)
            ctx.rectangle(-9, -r * 2, 18, r * 4)
            ctx.rectangle(16, -r * 2, 6, r * 4)
            ctx.set_source_rgba(1, 1, 1, 0.75)
            ctx.fill()
            ctx.restore()
            # sparkle star on the rim
            sk = math.sin(gp * math.pi)
            sx_, sy_ = mx_ - r * 0.7, my_ - r * 0.7
            ctx.set_source_rgba(1, 1, 0.9, 1)
            ctx.move_to(sx_, sy_ - 18 * sk)
            ctx.line_to(sx_ + 4 * sk, sy_)
            ctx.line_to(sx_, sy_ + 18 * sk)
            ctx.line_to(sx_ - 4 * sk, sy_)
            ctx.close_path()
            ctx.move_to(sx_ - 18 * sk, sy_)
            ctx.line_to(sx_, sy_ + 4 * sk)
            ctx.line_to(sx_ + 18 * sk, sy_)
            ctx.line_to(sx_, sy_ - 4 * sk)
            ctx.close_path()
            ctx.fill()
    # ring
    circle(ctx, mx_, my_, r)
    ctx.set_source_rgba(*INK)
    ctx.set_line_width(16)
    ctx.stroke_preserve()
    ctx.set_source_rgba(*GOLD)
    ctx.set_line_width(8)
    ctx.stroke_preserve()
    ctx.set_source_rgba(*GOLD_DK)
    ctx.set_line_width(3)
    ctx.save()
    ctx.translate(2, 2)
    ctx.stroke()
    ctx.restore()
    ctx.new_path()
    return mx_, my_


def _vein(ctx, x, y, k, t):
    sc = (0.85 + 0.15 * math.sin(t * 9)) * k
    if sc <= 0.02:
        return
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(sc, sc)
    ctx.set_source_rgba(*VEIN)
    ctx.set_line_width(7)
    for ang in (0, math.pi / 2, math.pi, 3 * math.pi / 2):
        ctx.save()
        ctx.rotate(ang + 0.785)
        ctx.move_to(6, -16)
        ctx.curve_to(6, -6, 6, -6, 16, -6)
        ctx.restore()
    ctx.stroke()
    ctx.restore()


def _sweat(ctx, x, y, k, t):
    if k <= 0.02:
        return
    slide = (t * 0.5) % 1.0
    yy = y + slide * 30
    a = k * (1 - smoothstep(seg(slide, 0.75, 1.0)))
    ctx.move_to(x, yy - 22)
    ctx.curve_to(x + 4, yy - 10, x + 13, yy - 2, x + 13, yy + 7)
    ctx.arc(x, yy + 7, 13, 0, math.pi)
    ctx.curve_to(x - 13, yy - 2, x - 4, yy - 10, x, yy - 22)
    ctx.close_path()
    ctx.set_source_rgba(SWEAT[0], SWEAT[1], SWEAT[2], a)
    ctx.fill_preserve()
    ctx.set_source_rgba(INK[0], INK[1], INK[2], a)
    ctx.set_line_width(3.5)
    ctx.stroke()
    ellipse(ctx, x - 4, yy + 5, 3, 5)
    ctx.set_source_rgba(1, 1, 1, a)
    ctx.fill()


def _draw_head(ctx, p, t, look, mouth, blink, seed, talk_amt):
    """Head drawn in face coords (origin = eye-line centre)."""
    mo_lip, wide = mouth
    mo = clamp(p["mo"] + mo_lip * 0.85 * (1 - 0.45 * p["mo"]))
    jaw = mo * 24
    lx = clamp(look[0] + p["ex"], -1.2, 1.2)
    ly = clamp(look[1] + p["ey"], -1.2, 1.2)
    turn = lx * 9.0          # fake 3D: features slide toward the look direction
    nose_turn = lx * 14.0

    # ears + hair tufts (behind the head outline)
    for sx in (-1, 1):
        _ear(ctx, sx)
    for sx in (-1, 1):
        _hair_tuft(ctx, sx, t, p["hair"], seed)

    # head (one shadow tone + dome shine)
    _head_path(ctx, jaw)
    ctx.set_source_rgba(*SKIN_SH)
    ctx.fill()
    ctx.save()
    ctx.translate(-70, -110)
    ctx.scale(0.915, 0.94)
    ctx.translate(70, 110)
    _head_path(ctx, jaw)
    ctx.restore()
    ctx.set_source_rgba(*SKIN)
    ctx.fill()
    # dome shine
    ellipse(ctx, -62, -150, 40, 20, -0.55)
    ctx.set_source_rgba(1, 1, 1, 0.55)
    ctx.fill()
    ellipse(ctx, -18, -184, 8, 5, -0.2)
    ctx.fill()
    # blush
    if p["blush"] > 0.01:
        ctx.set_source_rgba(*_rgba(BLUSH, 0.45 * p["blush"]))
        ellipse(ctx, -96 + turn, 62, 30, 15)
        ctx.fill()
        ellipse(ctx, 96 + turn, 62, 30, 15)
        ctx.fill()
    # gloom lines over the dome
    if p["gloom"] > 0.01:
        ctx.save()
        _head_path(ctx, jaw)
        ctx.clip()
        ctx.set_source_rgba(*_rgba(GLOOM, 0.55 * p["gloom"]))
        ctx.set_line_width(6)
        for k in range(7):
            gx = -96 + k * 32
            ctx.move_to(gx, -210)
            ctx.line_to(gx, -120 + 18 * math.sin(k * 1.7))
        ctx.stroke()
        ctx.restore()
    _head_path(ctx, jaw)
    ctx.set_source_rgba(*INK)
    ctx.set_line_width(OUT_W + 1)
    ctx.stroke()

    # wrinkles: forehead lines when brows go up
    up = -min(p["by1"], p["by2"])
    if up > 18:
        a = clamp((up - 18) / 25)
        ctx.set_source_rgba(*_rgba(SKIN_DK, a))
        ctx.set_line_width(3.5)
        for k in range(3):
            yy = -140 - k * 18
            ctx.move_to(-46 + turn, yy + 4)
            ctx.curve_to(-20 + turn, yy - 4, 20 + turn, yy - 4, 46 + turn, yy + 4)
        ctx.stroke()

    # cheek / sneer lines
    if p["sneer"] > 0.05 or p["mc"] > 0.5:
        a = clamp(max(p["sneer"], (p["mc"] - 0.5) * 2))
        ctx.set_source_rgba(*_rgba(SKIN_DK, a))
        ctx.set_line_width(4)
        for sx in (-1, 1):
            ctx.move_to(turn + sx * 40, 50)
            ctx.curve_to(turn + sx * 60, 66, turn + sx * 66, 84, turn + sx * 62, 104)
        ctx.stroke()

    # eyes
    b = blink_amount(t, seed, rate=0.24) if blink is None else clamp(blink)
    flut = 0.0
    if p["flutter"] > 0.01:
        ph = (t % 1.7) / 1.7
        if ph < 0.45:
            flut = p["flutter"] * 0.55 * max(0.0, math.sin(ph / 0.45 * math.pi * 3)) ** 2
    # micro-saccades
    k = math.floor(t * 1.4 + hash01(seed, 3))
    f = t * 1.4 + hash01(seed, 3) - k
    sa = smoothstep(f / 0.12)
    sxv = lerp(noise1(k - 1, seed + 21), noise1(k, seed + 21), sa) * 0.09
    syv = lerp(noise1(k - 1, seed + 22), noise1(k, seed + 22), sa) * 0.07
    eye_lx, eye_ly = lx + sxv, ly + syv
    ecx = []
    for side, sx in ((1, -1), (2, 1)):
        es = p["es"] * (1.07 if side == 2 else 1.0)
        rx, ry = EYE_RX * es, EYE_RY * es
        cx, cy = sx * EYE_DX + turn, EYE_DY
        ul, ll = p["ul%d" % side], p["ll%d" % side]
        ul = clamp(ul + flut * (1 - ul))
        if b > 0.0:   # lids meet ~60% down the eye
            ll = lerp(ll, max(ll, 0.4), b)
            ul = lerp(ul, max(ul, 1.0 - ll), b)
        # under-eye crease (age + villainy), deeper when squinting
        ctx.move_to(cx - sx * rx * 0.55, cy + ry + 9)
        ctx.curve_to(cx - sx * rx * 0.1, cy + ry + 16 - ll * 6, cx + sx * rx * 0.4,
                     cy + ry + 14 - ll * 6, cx + sx * rx * 0.8, cy + ry + 2)
        ctx.set_source_rgba(*_rgba(SKIN_DK, 0.55 + 0.4 * ll))
        ctx.set_line_width(3.5)
        ctx.stroke()
        _eye(ctx, sx, cx, cy, rx, ry, ul, ll, p["lt%d" % side], p["ps"], p["shine"],
             eye_lx, eye_ly, p["flutter"])
        ecx.append((cx, cy, rx, ry))

    # nose, mouth, mustache, goatee
    mp = dict(p)
    mp["mx"] = p["mx"] + turn * 1.1
    xl, yl, xr, yr, lm = _mouth(ctx, mp, mo, wide, t)
    _goatee(ctx, jaw, mp["mx"] * 0.8)
    _mustache(ctx, mp["mx"], yl, yr, MOUTH_Y, t)
    _nose(ctx, nose_turn)

    # monocle on the screen-right eye
    cx2, cy2, rx2, ry2 = ecx[1]
    _monocle(ctx, cx2, cy2 + p["by2"] * 0.08, 52 * p["es"] ** 0.5 + 2, p["mono"], t, seed)

    # brows (on top of monocle)
    bob = -mo_lip * 5 * talk_amt
    _brow(ctx, -1, ecx[0][0], p["by1"] + bob - (p["es"] - 1) * 30, p["ba1"], p["bc1"], 0)
    _brow(ctx, 1, ecx[1][0], p["by2"] + bob - (p["es"] - 1) * 30, p["ba2"], p["bc2"], 0)

    # effects
    _vein(ctx, 92, -150, p["vein"], t)
    _sweat(ctx, -134, -120, p["sweat"], t)


# ---------------------------------------------------------------------------
# arms + hands
# ---------------------------------------------------------------------------
def _finger_pts(hand):
    """Hand-local capsules (x0, y0, x1, y1, width): thumb first, then 3 fingers.

    x runs from the wrist toward the fingertips. Also returns thumb 'wrap'
    (0..1): in a fist the thumb lies across the curled fingers, in front.
    """
    cu, ix, th, sp = hand["cu"], hand["ix"], hand["th"], hand["sp"]
    out = []
    bases = ((49, -15, -0.25, ix), (54, 0, 0.0, cu), (49, 15, 0.25, cu))
    for bx, by_, a, c in bases:
        c = clamp(c)
        L = 31 * (1 - 0.8 * c)
        ang = a * (0.45 + 1.3 * sp) * (1 - 0.6 * c)
        out.append((bx, by_, bx + math.cos(ang) * L, by_ + math.sin(ang) * L, 21.0))
    wrap = smoothstep(clamp((max(cu, ix * 0.0 + cu) - 0.6) / 0.35))
    ta = lerp(-1.05 + th * 0.9, 0.95, wrap)
    tl = lerp(25 + 4 * th, 17, wrap)
    tb = (lerp(26, 34, wrap), lerp(-18, -16, wrap))
    out.insert(0, (tb[0], tb[1], tb[0] + math.cos(ta) * tl, tb[1] + math.sin(ta) * tl, 20.0))
    return out, wrap


def _draw_hand(ctx, x, y, hand):
    hs = HAND_SCALE * hand["hs"]
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(hand["ha"])
    ctx.scale(hs, hs * hand["tf"])
    F, wrap = _finger_pts(hand)
    lw = OUT_W / hs          # outer line in local units
    il = 2.6 / hs * 1.45     # inner line half-extra
    ctx.set_line_cap(1)
    # silhouette pass (thick outer ink)
    ctx.set_source_rgba(*INK)
    for x0, y0, x1, y1, w in F:
        ctx.move_to(x0, y0)
        ctx.line_to(x1, y1)
    ctx.set_line_width(21 + 2 * lw)
    ctx.stroke()
    ellipse(ctx, 34, 0, 26, 25)
    ctx.set_line_width(2 * lw)
    ctx.stroke_preserve()
    ctx.fill()
    # cuff
    _poly(ctx, [(-10, -29), (12, -22), (12, 22), (-10, 29)])
    ctx.set_source_rgba(*GLOVE)
    ctx.fill_preserve()
    ctx.set_source_rgba(*INK)
    ctx.set_line_width(lw * 0.8)
    ctx.stroke()

    def capsule(c):
        x0, y0, x1, y1, w = c
        ctx.move_to(x0, y0)
        ctx.line_to(x1, y1)
        ctx.set_source_rgba(*INK)
        ctx.set_line_width(w + 2 * il)
        ctx.stroke_preserve()
        ctx.set_source_rgba(*GLOVE)
        ctx.set_line_width(w)
        ctx.stroke()

    if wrap < 0.5:
        capsule(F[0])          # thumb behind the palm
    # palm + one shadow tone
    ellipse(ctx, 34, 0, 26, 25)
    ctx.set_source_rgba(*GLOVE)
    ctx.fill()
    ellipse(ctx, 31, 12, 20, 9)
    ctx.set_source_rgba(*GLOVE_SH)
    ctx.fill()
    for c in F[3:0:-1]:
        capsule(c)
    if wrap >= 0.5:
        capsule(F[0])          # fist: thumb wrapped across the knuckles
    # glove-back stitches (soft) or palm crease
    ctx.set_source_rgba(*GLOVE_SH)
    ctx.set_line_width(3.2 / hs * 1.45)
    if hand["pm"] < 0.5:
        if hand["cu"] < 0.7:
            for yy in (-7, 7):
                ctx.move_to(18, yy)
                ctx.line_to(34, yy * 1.05)
            ctx.stroke()
    else:
        ctx.set_source_rgba(*INK)
        ctx.move_to(22, 10)
        ctx.curve_to(30, 2, 40, 0, 46, 6)
        ctx.stroke()
    ctx.restore()


def _draw_arm(ctx, shoulder, arm):
    sx_, sy_ = shoulder
    ex, ey, wx, wy = arm["ex"], arm["ey"], arm["wx"], arm["wy"]
    ctx.set_line_cap(1)
    ctx.set_line_join(1)

    def path(dx=0.0, dy=0.0):
        ctx.move_to(sx_ + dx, sy_ + dy)
        ctx.line_to(ex + dx, ey + dy)
        ctx.line_to(wx + dx, wy + dy)
    path()
    ctx.set_source_rgba(*INK)
    ctx.set_line_width(62 + 2 * OUT_W)
    ctx.stroke()
    path()
    ctx.set_source_rgba(*SUIT_DK)
    ctx.set_line_width(62)
    ctx.stroke()
    path(-6, -6)
    ctx.set_source_rgba(*SUIT)
    ctx.set_line_width(40)
    ctx.stroke()
    _draw_hand(ctx, wx, wy, arm)


# ---------------------------------------------------------------------------
# snake coil
# ---------------------------------------------------------------------------
SNAKE_HEAD = (-306.0, -474.0)
SNAKE_SCALE = 0.98
_COIL = [(-304, -440), (-292, -398), (-262, -360), (-214, -348), (-120, -374),
         (0, -386), (120, -376), (212, -352), (258, -314), (242, -264), (150, -226),
         (30, -210), (-92, -222), (-178, -256), (-214, -296), (-200, -332), (-170, -340),
         (-150, -326)]
_COIL_SPLIT = 7   # control index where the front part starts (right shoulder)


def _coil_samples(t, shy, breath):
    pts = []
    for i, (px, py) in enumerate(_COIL):
        dy = shy * 0.6 if py < -300 else shy * 0.3
        # gentle slither: tail tip curls a little
        if i >= len(_COIL) - 3:
            px += math.sin(t * 2.2 + i) * 4
            py += math.cos(t * 2.2 + i) * 3
        pts.append((px, py + dy - breath * 1.5))
    P = _snake.coil_points(pts, 5)
    split = _COIL_SPLIT * 5
    return P, split


def _snake_back(ctx, P, split, W):
    _snake.draw_tube(ctx, P, W, 0, split, cap0=True, cap1=False, belly_side=-1,
                     spot_phase=10, belly_lines=False)


def _snake_front(ctx, P, split, W, fp):
    n = len(P)
    end = n - 1
    if fp > 0.02:
        # the tail tip leaves to slap over Hissy's eyes: stop the coil early
        end = n - 1 - int(round(fp * 10))
    _snake.draw_tube(ctx, P, W, split, end, cap0=False, cap1=fp <= 0.02, belly_side=-1,
                     spot_phase=30)
    return P[end]


# ---------------------------------------------------------------------------
# main entry
# ---------------------------------------------------------------------------
def draw_villain(ctx, x, y, s, t, expr="neutral", look=(0, 0), mouth=(0, 0), arms="rest",
                 lean=0.0, blink=None, snake=None, seed=1):
    """Draw Dr. Malvo Sneakworth. See module docstring / SPEC.md section 2."""
    p = resolve_expr(expr)
    A, B, a_shy, a_hdy, a_tilt = resolve_arms(arms, t)
    if not isinstance(mouth, (tuple, list)):
        mouth = (float(mouth), 0.0)
    mo_lip, wide = float(mouth[0]), float(mouth[1])
    talk = clamp(mo_lip * 3)

    breath = math.sin(t * 2 * math.pi / 3.6 + seed * 1.3)
    shy = p["shy"] + a_shy - breath * 2.5
    # head motion: expression offset + breathing + speech bob + idle drift
    head_dy = p["hy"] + a_hdy - breath * 3.0 + shy * 0.5 - mo_lip * 5
    head_rot = (p["tilt"] + a_tilt + noise1(t * 0.35, seed + 5) * 0.025
                + noise1(t * 2.2, seed + 6) * 0.03 * talk)

    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    if lean:
        ctx.rotate(lean)
    ctx.set_tolerance(0.3)
    ctx.set_line_join(1)
    ctx.set_line_cap(1)

    _cape_back(ctx, shy)
    _torso(ctx, shy, breath, snake is not None)
    _collar(ctx, shy)

    sn = None
    if snake is not None:
        sn = dict(snake) if isinstance(snake, dict) else {}
        sexpr = sn.get("expr", "idle")
        sp = _snake.resolve_expr(sexpr)
        P, split = _coil_samples(t, shy, breath)
        W = _snake.tail_widths(len(P), 46, taper_frac=0.3, tip=9, head_frac=0.08)
        _snake_back(ctx, P, split, W)

    # neck shadow
    ctx.save()
    ctx.translate(NECK[0], NECK[1] + shy * 0.5)
    ellipse(ctx, 0, -6, 66, 30)
    ctx.set_source_rgba(*SKIN_DK)
    ctx.fill()
    ctx.restore()

    # head
    ctx.save()
    ctx.translate(NECK[0], NECK[1] + head_dy)
    ctx.rotate(head_rot)
    ctx.translate(0, FACE_OFF)
    _draw_head(ctx, p, t, look, (mo_lip, wide), blink, seed, 1.0)
    ctx.restore()

    tail_end = None
    if sn is not None:
        tail_end = _snake_front(ctx, P, split, W, sp["fp"])

    # arms (screen-left then screen-right)
    shL = (-SHOULDER[0], SHOULDER[1] + shy)
    shR = (SHOULDER[0], SHOULDER[1] + shy)
    _draw_arm(ctx, shL, A)
    _draw_arm(ctx, shR, B)

    # snake head peeking over the screen-left shoulder
    if sn is not None:
        hx, hy = SNAKE_HEAD[0], SNAKE_HEAD[1] + shy * 0.6 - breath * 1.5
        tf = None
        if tail_end is not None:
            tf = ((tail_end[0] - hx) / SNAKE_SCALE, (tail_end[1] - hy) / SNAKE_SCALE)
        _snake.draw_snake_head(ctx, hx, hy, SNAKE_SCALE, t, sexpr,
                               sn.get("look", (0.3, 0.0)), sn.get("mouth", 0.0),
                               sn.get("tongue", None), sn.get("blink", None), tail_from=tf,
                               seed=seed + 4, neck=False)
    ctx.restore()
