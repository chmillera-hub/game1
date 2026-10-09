"""The AI character rig -- "the wall with a door".

A friendly floating screen-head: rounded-square navy monitor with a cyan rim
light, a dark screen face, a soft halo ring, a little detached "stand" piece
floating under it, and two floating mitten hands.

    draw_ai(ctx, x, y, s, t, expr="neutral", look=(0, 0), mouth=(0, 0),
            hands="idle", blink=None, glow=1.0, think=0.0, seed=2,
            roll0=None, aura=1.0, shake=0.0, nod=0.0)  -> anchors dict

* (x, y)  = centre of the screen-head.  At s=1 the head is 560 x 470 px
            (screen 492 x 386); halo ring centred 306 px above, stand 286 below.
            BBOX (all poses, s=1, rel. to x,y) = (-452, -374, 454, 386);
            the soft back-glow ("aura") reaches 440 px from the centre.
* expr    = name, or (from, to, blend) from core.state_at, or a dict of
            params.  Names: EXPRS.  'eyeroll' loops on t (1.5 s period)
            unless roll0 (start time) is given -> plays once, then 😒.
* look    = pupil direction (-1..1, -1..1); also nudges the face (parallax).
            Looking against an expression's built-in side-glance (😒 glances
            right) smoothly mirrors the whole face, so look=(-1,0) gives a
            proper left side-eye.
* mouth   = (open 0..1, wide -1..1) lip-sync from info.mouth("ai", t),
            layered on the expression mouth (talks in every expression).
* hands   = name, or (from, to, blend).  Names: HAND_POSES.  Hands are named
            by SCREEN side: "L" = viewer's left, "R" = viewer's right.
            Single-hand gestures use R (point, present, wave, thumbs_up,
            point_up, chin) or L (stop); "_l" variants use the other hand.
* blink   = None (automatic, seeded) or 0..1 override.
* glow    = brightness of face/halo glows (0.3 dim .. 1.2 bright).
* think   = 0..1 processing light sweeping round the bezel + data ticks.
* aura    = 0..1 soft cyan back-glow (set 0 over busy backgrounds).
* shake / nod = 0..1 automatic head shake ("nope") / nod ("yep").

Returns world-space anchors: face, eyeL, eyeR, mouth, halo, top, handL,
handR (palm centres) and handL_tip, handR_tip (finger tips) -- for props,
emotes and speech-bubble tails.
"""
import math

import cairocffi as cairo

from .core import (PAL, hexc, clamp, lerp, smoothstep, ease_in_out, ease_out_back,
                   blink_amount, noise1, hash01, rrect, ellipse, circle)

# ---------------------------------------------------------------------------
# palette
# ---------------------------------------------------------------------------
INK = hexc("ink")
BODY = hexc("ai_body")
BODY_SH = hexc("#111d3b")
BODY_HI = hexc("#2a4377")
RIM = hexc("ai_rim")
SCREEN = hexc("ai_screen")
EYE = hexc("ai_eye")
GLOW = hexc("ai_glow")
PUPIL = hexc("#0b1733")
MOUTH_IN = hexc("#15476a")
TONGUE = hexc("#ff86b4")
BLUSH = hexc("#ff6fa8")
BLUSH_HI = hexc("#ffb3d1")
HAND = hexc("#2b4a8a")
HAND_SH = hexc("#1a2c58")
LIDSHADE = hexc("#7fd9f0")

# ---------------------------------------------------------------------------
# geometry (head-local units, s = 1)
# ---------------------------------------------------------------------------
HEAD_W, HEAD_H, HEAD_R = 560.0, 470.0, 128.0
SCR_X, SCR_Y, SCR_W, SCR_H, SCR_R = -246.0, -201.0, 492.0, 386.0, 92.0   # screen rect
EYE_X, EYE_Y, EYE_RX, EYE_RY = 108.0, -36.0, 64.0, 78.0
MOUTH_Y = 104.0
MOUTH_HW = 66.0
BROW_GAP = 34.0
BROW_HL = 50.0
HALO_Y, HALO_RX, HALO_RY = -306.0, 150.0, 30.0
STAND_Y = 286.0
HU = 1.4                 # hand unit (mitten width = 66*HU)
INK_W = 7.0              # body outline width

EXPRS = ["neutral", "happy", "unimpressed", "skeptical", "eyeroll", "thinking",
         "alert", "wink", "warm", "sympathetic", "determined", "amused", "sad"]

# ---------------------------------------------------------------------------
# expressions: parameter dicts, blended linearly
# ---------------------------------------------------------------------------
# brows:  bLy/bRy raise px (+ up), bLa/bRa angle rad (+ = inner end up), arch
# lids:   tL/tR top-lid coverage 0..1 (fraction of eye height from the top)
#         ttL/ttR top-lid tilt (+ = lower at the inner corner), tc lid arch
#         lL/lR bottom-lid coverage, lc bottom-lid arch (+ = smiling eyes)
#         wL/wR extra per-eye closure (wink)
# eyes:   px/py pupil offset (-1..1), ps pupil scale, es eye scale, eLs/eRs
# mouth:  mc curve (+ smile / - frown), mw width, mx/my offset px, mt tilt,
#         mo base open, ms smirk (+ raises viewer-right corner), mlook =
#         px the mouth slides per unit of pupil-x (the 😒 off-centre mouth)
# misc:   blush, tilt (head rad), scan (processing scanline), glow mult,
#         bk blink multiplier, sacc saccade multiplier
BASE = dict(bLy=0.0, bRy=0.0, bLa=0.04, bRa=0.04, arch=0.3,
            tL=0.07, tR=0.07, ttL=0.0, ttR=0.0, tc=0.25, lL=0.03, lR=0.03, lc=0.0,
            wL=0.0, wR=0.0,
            px=0.0, py=0.0, ps=1.0, es=1.0, eLs=1.0, eRs=1.0,
            mc=0.3, mw=0.82, mx=0.0, my=0.0, mt=0.0, mo=0.0, ms=0.0, mlook=12.0,
            blush=0.0, tilt=0.0, scan=0.0, glow=1.0, bk=1.0, sacc=1.0, pr=1.0,
            mflip=0.0, nomir=0.0)


def _E(**kw):
    d = dict(BASE)
    d.update(kw)
    return d


EXPR = {
    "neutral": _E(),
    "happy": _E(bLy=14, bRy=14, arch=0.6, tL=0.0, tR=0.0, lL=0.33, lR=0.33, lc=0.34,
                mc=1.0, mw=1.08, mo=0.5, blush=0.8, ps=1.06),
    # 😒 flat half lids, pupils parked sideways under the lid, flat off-centre mouth
    "unimpressed": _E(bLy=-44, bRy=-44, bLa=0.04, bRa=0.04, arch=0.08,
                      tL=0.54, tR=0.54, tc=0.0, lL=0.12, lR=0.12,
                      px=0.86, py=0.5, ps=1.04, mc=-0.1, ms=-0.32, mw=0.62, mt=-0.05,
                      my=8, mlook=42.0, tilt=0.035, sacc=0.35),
    # 🤨 one heavy lid + low brow, the other brow way up
    "skeptical": _E(bLy=-12, bRy=30, bLa=-0.22, bRa=-0.12, arch=0.75,
                    tL=0.43, tR=0.03, ttL=0.18, ttR=0.0, tc=0.05, lL=0.16, lR=0.03,
                    eLs=0.96, eRs=1.06, px=-0.3, py=0.05, mc=-0.12, mw=0.62, mt=0.1,
                    mx=10, ms=-0.25, mlook=18, tilt=-0.05, sacc=0.5),
    "eyeroll": _E(),  # animated, see _eyeroll()
    "thinking": _E(bLy=4, bRy=22, bLa=0.1, bRa=-0.05, arch=0.6, tL=0.13, tR=0.1,
                   lL=0.08, lR=0.08, px=0.58, py=-0.68, mc=-0.12, mw=0.42, mx=-34,
                   mt=0.14, mlook=0, tilt=-0.045, scan=1.0, sacc=0.6),
    "alert": _E(bLy=26, bRy=26, arch=0.65, tL=0.0, tR=0.0, tc=0.3, lL=0.0, lR=0.0,
                es=1.09, ps=0.7, mc=0.0, mw=0.4, mo=0.34, sacc=0.4),
    "wink": _E(bLy=-6, bRy=16, bLa=-0.06, arch=0.55, tL=0.05, tR=0.0, lL=0.3, lR=0.3,
               lc=0.36, wL=1.0, mc=0.8, mw=0.92, ms=0.45, blush=0.35, tilt=0.05),
    "warm": _E(bLy=7, bRy=7, bLa=0.12, bRa=0.12, arch=0.45, tL=0.1, tR=0.1, lL=0.25,
               lR=0.25, lc=0.24, ps=1.16, mc=0.7, mw=0.9, blush=0.6, tilt=0.06),
    "sympathetic": _E(bLy=8, bRy=8, bLa=0.38, bRa=0.38, arch=0.25, tL=0.24, tR=0.24,
                      ttL=-0.2, ttR=-0.2, tc=0.15, lL=0.1, lR=0.1, ps=1.2, py=0.12,
                      mc=0.12, mw=0.62, mt=0.04, tilt=0.08, blush=0.15),
    "determined": _E(bLy=-10, bRy=-10, bLa=-0.3, bRa=-0.3, arch=0.1, tL=0.3, tR=0.3,
                     ttL=0.26, ttR=0.26, tc=0.05, lL=0.15, lR=0.15, ps=0.9,
                     mc=0.18, mw=0.8, ms=0.22, sacc=0.4),
    "amused": _E(bLy=2, bRy=18, bLa=0.0, bRa=0.05, arch=0.5, tL=0.17, tR=0.12,
                 lL=0.3, lR=0.3, lc=0.26, px=-0.22, mc=0.45, mw=0.86, mx=8, ms=0.7,
                 blush=0.25, tilt=-0.05),
    "sad": _E(bLy=6, bRy=6, bLa=0.52, bRa=0.52, arch=0.2, tL=0.3, tR=0.3, ttL=-0.28,
              ttR=-0.28, tc=0.1, lL=0.04, lR=0.04, ps=1.22, py=0.32, mc=-0.75, mw=0.66,
              glow=0.75, tilt=-0.05),
}


def _eyeroll(t, roll0=None):
    """Dynamic eyeroll params. Loops every 1.5 s, or one-shot from roll0."""
    P = 1.5
    if roll0 is None:
        p, start = (t % P) / P, (0.78, 0.45)      # loop: start where it ends
    else:
        p, start = clamp((t - roll0) / P), (0.0, 0.1)
    end = (0.78, 0.45)
    R = 0.88
    if p < 0.14:                                   # dart to the left
        k = ease_in_out(p / 0.14)
        px, py = lerp(start[0], -R, k), lerp(start[1], 0.0, k)
    elif p < 0.62:                                 # up and over the top
        k = ease_in_out((p - 0.14) / 0.48)
        a = math.pi + math.pi * k
        px, py = R * math.cos(a), R * math.sin(a) * 1.05
    else:                                          # settle into a side-glance
        k = ease_in_out((p - 0.62) / 0.3)
        px, py = lerp(R, end[0], k), lerp(0.0, end[1], k)
    up = math.sin(math.pi * clamp((p - 0.1) / 0.6))       # 0..1 at the top of roll
    settle = smoothstep((p - 0.6) / 0.3) if roll0 is not None else \
        max(smoothstep((p - 0.6) / 0.3), 1 - smoothstep(p / 0.14))
    T = lerp(lerp(0.2, 0.04, up), 0.5, settle)
    d = _E(px=px, py=py, ps=0.88, tL=T, tR=T, tc=lerp(0.2, 0.0, settle),
           lL=0.1, lR=0.1, bLy=lerp(lerp(0, 16, up), -8, settle),
           bRy=lerp(lerp(0, 18, up), -8, settle), arch=0.3, bLa=0.06, bRa=0.06,
           mc=lerp(-0.2, -0.1, settle), ms=lerp(0.0, -0.3, settle), mw=0.6, mt=-0.05,
           mlook=lerp(18, 40, settle), my=8, nomir=1.0,
           tilt=lerp(lerp(-0.02, 0.06, up), 0.03, settle), bk=0.0, sacc=0.0,
           pr=1.0 + 0.45 * up)
    return d


_SWAP = [("bLy", "bRy"), ("bLa", "bRa"), ("tL", "tR"), ("ttL", "ttR"), ("lL", "lR"),
         ("wL", "wR"), ("eLs", "eRs")]


def _mirror_expr(d):
    """Left/right mirror of an expression dict (for glancing the other way)."""
    m = dict(d)
    for a, b in _SWAP:
        m[a], m[b] = d[b], d[a]
    for k in ("px", "mx", "mt", "tilt"):
        m[k] = -d[k]
    m["mflip"] = 1.0 - d["mflip"]
    return m


def _expr_params(e, t, roll0):
    if isinstance(e, (tuple, list)):
        a, b, k = e
        da, db = _expr_params(a, t, roll0), _expr_params(b, t, roll0)
        if a == b or k >= 1:
            return db
        if k <= 0:
            return da
        return {key: lerp(da[key], db[key], k) for key in da}
    if isinstance(e, dict):
        d = dict(BASE)
        d.update(e)
        return d
    if e == "eyeroll":
        return _eyeroll(t, roll0)
    if e not in EXPR:
        _warn("expr", e)
    return EXPR.get(e, EXPR["neutral"])


# ---------------------------------------------------------------------------
# hand poses
# ---------------------------------------------------------------------------
# Each hand: wrist position x,y (head-local), rot (0 = fingers up, + clockwise),
# open (0 fist .. 1 flat mitten), index (pointing finger 0..1), thumb (angle
# out from the fingers, rad), tl thumb length, palm (glowing palm pad 0..1),
# sc scale, sx/sy squash.  "L" hand = viewer's left; its thumb is on its
# inner (+x) side; "R" is drawn mirrored.
def _H(x, y, rot, open=0.55, index=0.0, thumb=0.5, tl=1.0, palm=0.0, sc=1.0, sx=1.0, sy=1.0):
    return dict(x=float(x), y=float(y), rot=float(rot), open=float(open), index=float(index),
                thumb=float(thumb), tl=float(tl), palm=float(palm), sc=float(sc),
                sx=float(sx), sy=float(sy))


def _mir(h):
    d = dict(h)
    d["x"] = -h["x"]
    d["rot"] = -h["rot"]
    return d


IDLE_L = _H(-316, 150, -math.pi - 0.24, open=0.5, thumb=0.5, tl=0.85, sx=-1.0)
IDLE_R = _mir(IDLE_L)

HAND_POSES = ["idle", "wave", "stop", "stop_both", "present", "present_l", "present_both",
              "point", "point_l", "point_up", "shrug", "chin", "typing", "thumbs_up",
              "thumbs_both", "fists"]

_PRESENT_R = _H(272, 176, 0.98, open=1.0, thumb=0.75, palm=0.85, sc=1.05)
_POINT_R = _H(282, 34, 1.22, open=0.0, index=1.0, thumb=0.22, tl=0.6)
_THUMB_R = _H(306, 168, 1.57, open=0.0, thumb=1.62, tl=1.15, sc=1.05)


_WARNED = set()


def _warn(kind, name):
    if (kind, name) not in _WARNED:
        _WARNED.add((kind, name))
        import sys
        print(f"[ai_char] unknown {kind} {name!r}; using default", file=sys.stderr)


def _pose(name, t, seed):
    if name not in HAND_POSES:
        _warn("hands", name)
    kb = 0.0
    L, R = dict(IDLE_L), dict(IDLE_R)
    if name == "wave":
        w = math.sin(t * 2 * math.pi * 1.9)
        R = _H(336, -24, 0.26 + 0.36 * w, open=1.0, thumb=0.75, palm=0.9)
    elif name == "stop":
        # crossing-guard palm toward camera (bigger = closer)
        L = _H(-262, 262, -0.1, open=1.0, thumb=0.62, palm=1.0, sc=1.4)
    elif name == "stop_both":
        L = _H(-268, 262, -0.14, open=1.0, thumb=0.62, palm=1.0, sc=1.3)
        R = _mir(L)
    elif name == "present":
        R = dict(_PRESENT_R)
    elif name == "present_l":
        L = _mir(_PRESENT_R)
    elif name == "present_both":
        R = dict(_PRESENT_R)
        L = _mir(_PRESENT_R)
    elif name == "point":
        R = dict(_POINT_R)
    elif name == "point_l":
        L = _mir(_POINT_R)
    elif name == "point_up":
        # tilted index with the thumb out: an upright single finger seen from
        # the back of the mitten reads as a rude gesture at phone size
        R = _H(330, 10, -0.45, open=0.0, index=1.0, thumb=1.1, tl=1.0)
    elif name == "shrug":
        b = 0.5 + 0.5 * math.sin(t * 2 * math.pi * 0.8)
        L = _H(-288, 70 - 10 * b, -1.16, open=1.0, thumb=0.8, palm=0.8, sc=1.02)
        R = _mir(L)
    elif name == "chin":
        tap = 0.5 + 0.5 * math.sin(t * 2 * math.pi * 1.4)
        R = _H(138, 316, -0.16, open=0.0, index=0.45 + 0.3 * tap, thumb=0.3, tl=0.7)
    elif name == "typing":
        kb = 1.0
        ph = t * 2 * math.pi * 3.1
        tapL = max(0.0, math.sin(ph))
        tapR = max(0.0, math.sin(ph + 2.2 + 0.6 * math.sin(t * 1.7)))
        L = _H(-118, 252 + 16 * tapL, -math.pi + 0.28, open=0.62, thumb=0.35, tl=0.85,
               sx=-1.0, sy=0.78)
        R = _mir(_H(-118, 252 + 16 * tapR, -math.pi + 0.28, open=0.62, thumb=0.35, tl=0.85,
                    sx=-1.0, sy=0.78))
    elif name == "thumbs_up":
        R = dict(_THUMB_R)
    elif name == "thumbs_both":
        R = dict(_THUMB_R)
        L = _mir(_THUMB_R)
    elif name == "fists":
        L = _H(-318, 214, -0.12, open=0.0, thumb=0.6, tl=0.8)
        R = _mir(L)
    return {"L": L, "R": R, "kb": kb}


def _hands_params(h, t, seed):
    if isinstance(h, (tuple, list)):
        a, b, k = h
        pa, pb = _pose(a, t, seed), _pose(b, t, seed)
        if a == b or k >= 1:
            return pb
        if k <= 0:
            return pa
        out = {"kb": lerp(pa["kb"], pb["kb"], k)}
        arc = math.sin(math.pi * k)
        for side in ("L", "R"):
            A, B = pa[side], pb[side]
            d = {key: lerp(A[key], B[key], k) for key in A}
            moved = abs(A["x"] - B["x"]) + abs(A["y"] - B["y"]) + 60 * abs(A["rot"] - B["rot"])
            if moved > 8:
                d["y"] -= 34 * arc              # travel on an arc
                d["sc"] *= 1 - 0.07 * arc       # tiny squash mid-move
            out[side] = d
        return out
    return _pose(h, t, seed)


# ---------------------------------------------------------------------------
# small drawing helpers
# ---------------------------------------------------------------------------
def _rgba(ctx, c, a=1.0):
    ctx.set_source_rgba(c[0], c[1], c[2], c[3] * a)


def _stroke(ctx, c, w, a=1.0):
    _rgba(ctx, c, a)
    ctx.set_line_width(w)
    ctx.stroke()


def _mixc(c1, c2, k):
    return tuple(c1[i] + (c2[i] - c1[i]) * k for i in range(4))


def _poly(ctx, pts):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.close_path()


def _capsule(ctx, x0, y0, x1, y1, r):
    """Path of a capsule (stadium) from (x0,y0) to (x1,y1) of radius r."""
    a = math.atan2(y1 - y0, x1 - x0)
    ctx.new_sub_path()
    ctx.arc(x1, y1, r, a - math.pi / 2, a + math.pi / 2)
    ctx.arc(x0, y0, r, a + math.pi / 2, a + 3 * math.pi / 2)
    ctx.close_path()


def _rrect_point(x, y, w, h, r, p):
    """Point at fraction p (0..1, clockwise from top-left straight) on a rrect."""
    straight_w, straight_h, arc = w - 2 * r, h - 2 * r, math.pi * r / 2
    per = 2 * straight_w + 2 * straight_h + 4 * arc
    d = (p % 1.0) * per
    segs = [("l", x + r, y, 1, 0, straight_w), ("a", x + w - r, y + r, -math.pi / 2, arc),
            ("l", x + w, y + r, 0, 1, straight_h), ("a", x + w - r, y + h - r, 0.0, arc),
            ("l", x + w - r, y + h, -1, 0, straight_w), ("a", x + r, y + h - r, math.pi / 2, arc),
            ("l", x, y + h - r, 0, -1, straight_h), ("a", x + r, y + r, math.pi, arc)]
    for sg in segs:
        ln = sg[-1]
        if d <= ln or sg is segs[-1]:
            if sg[0] == "l":
                return (sg[1] + sg[3] * d, sg[2] + sg[4] * d)
            ang = sg[3] + (d / r if r else 0)
            return (sg[1] + r * math.cos(ang), sg[2] + r * math.sin(ang))
        d -= ln
    return (x, y)


# ---------------------------------------------------------------------------
# saccades
# ---------------------------------------------------------------------------
def _saccade(t, seed):
    """Small, quick, discrete eye jumps (normalized pupil units)."""
    step = 0.55
    k = math.floor(t / step)
    def pos(j):
        if hash01(j, seed + 41) < 0.45:         # often hold still
            j = j - 1
        return ((hash01(j, seed + 11) * 2 - 1) * 0.1, (hash01(j, seed + 23) * 2 - 1) * 0.07)
    a, b = pos(k - 1), pos(k)
    f = smoothstep((t - k * step) / 0.06)
    return (lerp(a[0], b[0], f), lerp(a[1], b[1], f))


# ---------------------------------------------------------------------------
# face parts
# ---------------------------------------------------------------------------
TH_CLOSED = 0.19     # visible thickness (eye-normalized) of a closed eye
SEAM = 0.62          # where the lids meet when closing (0 = top lid, 1 = bottom)


def _lids(u, inner, T, tilt, tc, B, lc, blink):
    ui = u * inner
    q = 1 - u * u
    top = -1 + 2 * T + tilt * ui - tc * q * 0.35
    bot = 1 - 2 * B - lc * q
    if blink > 0:
        seam = top + (bot - top) * SEAM
        top = lerp(top, seam, blink)
        bot = lerp(bot, seam, blink)
    return top, bot


def _eye_pts(cx, cy, rx, ry, T, tilt, tc, B, lc, inner, blink, n=18):
    """Visible eye polygon after top/bottom lids (lids = screen colour).

    Lids are curves v(u) in eye-normalized coords (u, v in -1..1).  Where the
    lids (nearly) meet, the eye becomes a glowing closed-eye line that
    follows the seam and tapers to the corners.
    """
    top_c, bot_c = [], []
    for i in range(n + 1):
        th = math.pi * (1 - i / n)
        u = math.cos(th)
        ext = math.sin(th)
        top, bot = _lids(u, inner, T, tilt, tc, B, lc, blink)
        tmin = TH_CLOSED * ext ** 0.5
        if bot - top < tmin:
            mid = (top + bot) * 0.5
            mid = clamp(mid, -ext - 0.25, ext + 0.25)
            lo, hi = mid - tmin * 0.5, mid + tmin * 0.5
        else:
            lo, hi = max(top, -ext), min(bot, ext)
            if hi - lo < 1e-3:
                continue
        x = cx + u * rx
        top_c.append((x, cy + lo * ry))
        bot_c.append((x, cy + hi * ry))
    return top_c + bot_c[::-1]


def _draw_eye(ctx, cx, cy, rx, ry, T, tilt, tc, B, lc, inner, blink, pupil, pr, g, eye_col):
    pts = _eye_pts(cx, cy, rx, ry, T, tilt, tc, B, lc, inner, blink)
    if len(pts) < 3:
        return
    # glow, then the eye itself
    _poly(ctx, pts)
    _rgba(ctx, GLOW, 0.22 * g)
    ctx.set_line_width(24)
    ctx.stroke_preserve()
    _rgba(ctx, eye_col)
    ctx.fill_preserve()
    # how closed is the eye at its centre?
    t0, b0 = _lids(0.0, inner, T, tilt, tc, B, lc, blink)
    open_frac = clamp((b0 - t0) / 0.45)
    if open_frac <= 0.05:
        ctx.new_path()
        return
    ctx.save()
    ctx.clip()
    # lid shade band just under the top lid (sells the lid)
    if t0 > -0.98:
        for i in range(11):
            u = -1.1 + 2.2 * i / 10
            tp, _ = _lids(clamp(u, -1, 1), inner, T, tilt, tc, B, lc, blink)
            (ctx.line_to if i else ctx.move_to)(cx + u * rx, cy + tp * ry)
        _rgba(ctx, LIDSHADE, 0.95)
        ctx.set_line_width(24)
        ctx.stroke()
    # pupil (fades as the eye closes so a closed eye stays a clean line)
    pa = smoothstep(open_frac)
    px, py = pupil
    circle(ctx, px, py, pr)
    _rgba(ctx, PUPIL, pa)
    ctx.fill()
    circle(ctx, px - pr * 0.36, py - pr * 0.38, pr * 0.3)
    ctx.set_source_rgba(1, 1, 1, 0.95 * pa)
    ctx.fill()
    circle(ctx, px + pr * 0.38, py + pr * 0.34, pr * 0.12)
    ctx.set_source_rgba(1, 1, 1, 0.6 * pa)
    ctx.fill()
    ctx.restore()


def _draw_brow(ctx, cx, cy, ang, arch, inner, g, col, hl=BROW_HL):
    ca, sa = math.cos(ang), math.sin(ang)
    ix, iy = cx + inner * hl * ca, cy - hl * sa          # inner end
    ox, oy = cx - inner * hl * ca, cy + hl * sa          # outer end
    mx, my = (ix + ox) / 2, (iy + oy) / 2 - arch * 22
    for w, a, c in ((34, 0.2 * g, GLOW), (17, 1.0, col)):
        ctx.move_to(ox, oy)
        ctx.curve_to(lerp(ox, mx, 0.66), lerp(oy, my, 0.66), lerp(ix, mx, 0.66),
                     lerp(iy, my, 0.66), ix, iy)
        _stroke(ctx, c, w, a)


def _mouth_path(ctx, cx, cy, hw, curve, smirk, op, wide, closed):
    """smirk = (left corner lift, right corner lift) in px."""
    lift = curve * 26
    yl = cy - lift - smirk[0]
    yr = cy - lift - smirk[1]
    ymid = cy + curve * 7 - op * 6 - (smirk[0] + smirk[1]) * 0.21
    # cubic with symmetric handles: mid = (y0 + 3*yc)/4
    y0 = (yl + yr) / 2
    yc = (4 * ymid - y0) / 3
    ctx.move_to(cx - hw, yl)
    ctx.curve_to(cx - hw * 0.4, yc, cx + hw * 0.4, yc, cx + hw, yr)
    if closed:
        return (yl, yr, ymid)
    h = op * 70 * (1 - 0.22 * wide)
    ylow = ymid + h
    yc2 = (4 * ylow - y0) / 3
    ctx.curve_to(cx + hw * 0.95, yc2, cx - hw * 0.95, yc2, cx - hw, yl)
    ctx.close_path()
    return (yl, yr, ylow)


def _draw_mouth(ctx, e, mouth, face_dx, face_dy, pupil_x, g, col):
    op_talk, wide = mouth
    ms, w = e["ms"], e["mflip"]
    sm = (lerp(-ms * 6, ms * 20, w), lerp(ms * 20, -ms * 6, w))
    op = clamp(e["mo"] + op_talk * 0.95, 0.0, 1.1)
    wide = clamp(wide, -1, 1)
    hw = MOUTH_HW * e["mw"] * (1 + 0.2 * wide * min(1.0, op * 3)) * (1 + 0.15 * op)
    cx = e["mx"] + e["mlook"] * pupil_x + face_dx
    cy = MOUTH_Y + e["my"] + face_dy
    ctx.save()
    ctx.translate(cx, cy)
    if e["mt"]:
        ctx.rotate(e["mt"])
    if op < 0.06:
        _mouth_path(ctx, 0, 0, hw, e["mc"], sm, 0, 0, True)
        _stroke(ctx, GLOW, 32, 0.2 * g)
        _mouth_path(ctx, 0, 0, hw, e["mc"], sm, 0, 0, True)
        _stroke(ctx, col, 15)
    else:
        _mouth_path(ctx, 0, 0, hw, e["mc"], sm, op, wide, False)
        _rgba(ctx, GLOW, 0.2 * g)
        ctx.set_line_width(32)
        ctx.stroke_preserve()
        _rgba(ctx, MOUTH_IN)
        ctx.fill_preserve()
        if op > 0.4 and hw > 30:                    # little tongue
            ctx.save()
            ctx.clip()
            yl, yr, ylow = _mouth_path(ctx, 0, 0, hw, e["mc"], sm, op, wide, False)
            ctx.new_path()
            ellipse(ctx, hw * 0.1, ylow + 2, hw * 0.5, 10 + 16 * op)
            _rgba(ctx, TONGUE, 0.9)
            ctx.fill()
            ctx.restore()
        else:
            ctx.new_path()
        _mouth_path(ctx, 0, 0, hw, e["mc"], sm, op, wide, False)
        _rgba(ctx, col)
        ctx.set_line_width(12)
        ctx.stroke()
    ctx.restore()


# ---------------------------------------------------------------------------
# hands
# ---------------------------------------------------------------------------
def _hand_geom(h):
    u = HU
    W_ = 66 * u
    Lf = lerp(8, 50, clamp(h["open"])) * u
    H_ = 60 * u + Lf
    return u, W_, H_


def _draw_hand(ctx, h, mirror, g):
    u, W_, H_ = _hand_geom(h)
    r_m = W_ * 0.44
    idx = clamp(h["index"])
    # thumb geometry
    tb = (W_ * 0.36, -24 * u)
    ta = h["thumb"]
    tlen = 34 * u * h["tl"]
    te = (tb[0] + math.sin(ta) * tlen, tb[1] - math.cos(ta) * tlen)
    tr = 13 * u
    # index finger geometry
    fist_top = -(60 * u + 8 * u)
    i0 = (W_ * 0.2, fist_top + 16 * u)
    i1 = (W_ * 0.2, fist_top + 16 * u - 56 * u * idx)
    ir = 12.5 * u
    sxx = h["sc"] * h["sx"] * (-1 if mirror else 1)
    mn = 0.45 * h["sc"]                 # keep some body while the hand turns over
    if abs(sxx) < mn:
        sxx = mn if sxx >= 0 else -mn
    syy = h["sc"] * h["sy"]

    def local(dx=0.0, dy=0.0):
        ctx.translate(h["x"] + dx, h["y"] + dy)
        ctx.rotate(h["rot"])
        ctx.scale(sxx, syy)

    def parts(dx=0.0, dy=0.0):
        ctx.save()
        local(dx, dy)
        rrect(ctx, -W_ / 2, -H_, W_, H_, r_m)
        _capsule(ctx, tb[0], tb[1], te[0], te[1], tr)
        if idx > 0.02:
            _capsule(ctx, i0[0], i0[1], i1[0], i1[1], ir)
        ctx.restore()

    # union outline: fat ink stroke of every part, fills on top
    parts()
    _rgba(ctx, INK)
    ctx.set_line_width(12)
    ctx.stroke()
    # world-lit fill: rim light top-left, shade bottom-right
    ctx.save()
    parts()
    ctx.clip()
    _rgba(ctx, RIM)
    ctx.paint()
    parts(5, 6)
    ctx.clip()
    _rgba(ctx, HAND_SH)
    ctx.paint()
    parts(-6, -9)
    _rgba(ctx, HAND)
    ctx.fill()
    ctx.restore()
    # details in hand space
    ctx.save()
    local()
    o = clamp(h["open"])
    clen = lerp(12, 34, o) * u
    ytop = -H_ + 5 * u
    for k in range(3):
        xx = (-0.25 + 0.25 * k) * W_ + (0.06 * W_ if idx > 0.5 else 0)
        if idx > 0.5 and k == 2:
            continue
        ctx.move_to(xx, ytop + 5 * u)
        ctx.line_to(xx, ytop + clen)
    ctx.restore()
    _rgba(ctx, INK, 0.75)
    ctx.set_line_width(4.5)
    ctx.stroke()
    if h["palm"] > 0.02:
        ctx.save()
        local()
        circle(ctx, 0, -30 * u, 22 * u)
        ctx.restore()
        _rgba(ctx, GLOW, 0.3 * h["palm"] * g)
        ctx.fill()
        ctx.save()
        local()
        circle(ctx, 0, -30 * u, 13 * u)
        ctx.restore()
        _rgba(ctx, EYE, 0.95 * h["palm"])
        ctx.fill()


def _hand_world(h, mirror, which):
    """Point on the hand in head-local coords: 'palm' centre or finger 'tip'."""
    u, W_, H_ = _hand_geom(h)
    if which == "tip":
        if h["index"] > 0.5:
            lx, ly = W_ * 0.2, -(68 * u) + 16 * u - 56 * u * h["index"] - 12 * u
        else:
            lx, ly = 0.0, -H_
    else:
        lx, ly = 0.0, -H_ * 0.5
    lx *= h["sc"] * h["sx"] * (-1 if mirror else 1)
    ly *= h["sc"] * h["sy"]
    c, s_ = math.cos(h["rot"]), math.sin(h["rot"])
    return (h["x"] + lx * c - ly * s_, h["y"] + lx * s_ + ly * c)


def _draw_keyboard(ctx, kb, t, g, hp):
    if kb <= 0.02:
        return
    y0, y1 = 300, 372
    top_hw, bot_hw = 190, 236
    pts = [(-top_hw, y0), (top_hw, y0), (bot_hw, y1), (-bot_hw, y1)]
    _poly(ctx, pts)
    _rgba(ctx, GLOW, 0.13 * kb * g)
    ctx.fill_preserve()
    _rgba(ctx, GLOW, 0.8 * kb)
    ctx.set_line_width(4)
    ctx.stroke()
    for r in (1, 2):
        f = r / 3
        y = lerp(y0, y1, f)
        hw = lerp(top_hw, bot_hw, f)
        ctx.move_to(-hw + 6, y)
        ctx.line_to(hw - 6, y)
    for c in range(-3, 4):
        ctx.move_to(c * 50 * top_hw / 190, y0 + 4)
        ctx.line_to(c * 50 * bot_hw / 190, y1 - 4)
    _rgba(ctx, GLOW, 0.32 * kb)
    ctx.set_line_width(2.5)
    ctx.stroke()
    # key flash under each tapping hand
    for side in ("L", "R"):
        h = hp[side]
        down = clamp((h["y"] - 258) / 8)
        if down > 0.05:
            ctx.rectangle(h["x"] - 30 + (12 if side == "L" else -12), y0 + 8, 46, 20)
            _rgba(ctx, EYE, 0.7 * kb * down)
            ctx.fill()


# ---------------------------------------------------------------------------
# main entry
# ---------------------------------------------------------------------------
_GLOW = {}
AURA_R = 440.0


def _glow_img():
    """Soft cyan back-glow, rendered once at low res and upscaled (cheap)."""
    img = _GLOW.get("img")
    if img is None:
        n = 64
        img = cairo.ImageSurface(cairo.FORMAT_ARGB32, n, n)
        c = cairo.Context(img)
        gr = cairo.RadialGradient(n / 2, n / 2, 0, n / 2, n / 2, n / 2)
        gr.add_color_stop_rgba(0.0, GLOW[0], GLOW[1], GLOW[2], 0.14)
        gr.add_color_stop_rgba(0.3, GLOW[0], GLOW[1], GLOW[2], 0.12)
        gr.add_color_stop_rgba(1.0, GLOW[0], GLOW[1], GLOW[2], 0.0)
        c.set_source(gr)
        c.paint()
        _GLOW["img"] = img
    return img


def draw_ai(ctx, x, y, s, t, expr="neutral", look=(0, 0), mouth=(0, 0), hands="idle",
            blink=None, glow=1.0, think=0.0, seed=2, roll0=None, aura=1.0,
            shake=0.0, nod=0.0):
    look = look or (0, 0)
    e = _expr_params(expr, t, roll0)
    # glancing against the expression's built-in side-glance mirrors the face
    # smoothly (so 😒 + look=(-1,0) is a proper LEFT side-eye, not centred)
    if e["nomir"] < 0.5 and abs(e["px"]) > 0.15 and look[0] * e["px"] < 0:
        wm = smoothstep((abs(look[0]) - 0.1) / 0.5)
        if wm > 0:
            em = _mirror_expr(e)
            e = {k: lerp(e[k], em[k], wm) for k in e}
    hp = _hands_params(hands, t, seed)
    g = clamp(glow * e["glow"] * (1 + 0.07 * math.sin(t * 2 * math.pi * 0.6 + seed)), 0, 1.6)
    op_talk = clamp(mouth[0] if mouth else 0.0)
    wide = mouth[1] if mouth else 0.0
    lx, ly = clamp(look[0], -1.6, 1.6), clamp(look[1], -1.6, 1.6)

    # --- body motion -------------------------------------------------------
    ph = t * 2 * math.pi * 0.47 + seed * 1.7
    bob = math.sin(ph) * 9 - op_talk * 3
    sway = noise1(t * 0.35, seed + 5) * 0.022
    tilt = e["tilt"] + sway
    # optional head shake ("nope") / nod ("yep")
    shk = math.sin(t * 2 * math.pi * 2.6) * clamp(shake)
    ndd = math.sin(t * 2 * math.pi * 2.2) * clamp(nod)
    hx = shk * 14
    bob += ndd * 9
    tilt += shk * 0.03
    out = {}

    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)

    # --- soft back glow (static-ish, one big radial) -----------------------
    # (kept light: gradients cost bitrate)
    if aura > 0.01:
        img = _glow_img()
        n = img.get_width()
        ctx.save()
        ctx.translate(-AURA_R, bob - AURA_R)
        ctx.scale(2 * AURA_R / n, 2 * AURA_R / n)
        ctx.set_source_surface(img, 0, 0)
        ctx.get_source().set_filter(cairo.FILTER_BILINEAR)
        ctx.rectangle(0, 0, n, n)
        ctx.clip()
        ctx.paint_with_alpha(clamp(aura * g))
        ctx.restore()

    # --- floating stand piece (lags behind the head) -----------------------
    sb = math.sin(ph - 0.9) * 12
    sy_ = STAND_Y + sb
    rrect(ctx, -74, sy_ - 22, 148, 44, 22)
    _rgba(ctx, BODY)
    ctx.fill_preserve()
    _rgba(ctx, INK)
    ctx.set_line_width(INK_W)
    ctx.stroke()
    ctx.move_to(-46, sy_ - 9)
    ctx.line_to(46, sy_ - 9)
    _rgba(ctx, RIM, 0.9)
    ctx.set_line_width(5)
    ctx.set_line_cap(1)
    ctx.stroke()
    ellipse(ctx, 0, sy_ + 44, 60, 9)
    _rgba(ctx, GLOW, 0.18 * g)
    ctx.fill()

    # --- head group (bob + tilt) ------------------------------------------
    ctx.save()
    ctx.translate(hx, bob)
    ctx.rotate(tilt)

    # halo ring (lags a touch, tilts a bit more)
    hb = math.sin(ph - 0.5) * 5
    hy = HALO_Y + hb
    ctx.save()
    ctx.translate(0, hy)
    ctx.rotate(-tilt * 0.4 + noise1(t * 0.3, seed + 9) * 0.03)
    ctx.scale(1, HALO_RY / HALO_RX)
    ctx.new_sub_path()
    ctx.arc(0, 0, HALO_RX, 0, 2 * math.pi)
    ctx.restore()
    _stroke(ctx, GLOW, 34, 0.16 * g)
    ctx.save()
    ctx.translate(0, hy)
    ctx.scale(1, HALO_RY / HALO_RX)
    ctx.new_sub_path()
    ctx.arc(0, 0, HALO_RX, 0, 2 * math.pi)
    ctx.restore()
    _stroke(ctx, _mixc(GLOW, EYE, 0.35), 11, min(1.0, 0.75 + 0.25 * g))
    # orbiting spark on the ring (faster while thinking)
    oa = t * (1.4 + 4.0 * think) + seed
    ox, oy = HALO_RX * math.cos(oa), hy + HALO_RY * math.sin(oa)
    circle(ctx, ox, oy, 10)
    ctx.set_source_rgba(1, 1, 1, 0.9 if math.sin(oa) > -0.2 else 0.45)
    ctx.fill()

    # ear nubs
    for sx in (-1, 1):
        rrect(ctx, sx * (HEAD_W / 2 - 4) - 17, -60, 34, 112, 16)
        _rgba(ctx, BODY_SH)
        ctx.fill_preserve()
        _rgba(ctx, INK)
        ctx.set_line_width(INK_W)
        ctx.stroke()
        ctx.move_to(sx * (HEAD_W / 2 + 7), -30)
        ctx.line_to(sx * (HEAD_W / 2 + 7), 22)
        _rgba(ctx, RIM, 0.85)
        ctx.set_line_width(5)
        ctx.stroke()

    # body
    hx0, hy0 = -HEAD_W / 2, -HEAD_H / 2
    rrect(ctx, hx0, hy0, HEAD_W, HEAD_H, HEAD_R)
    _rgba(ctx, BODY)
    ctx.fill()
    ctx.save()
    rrect(ctx, hx0, hy0, HEAD_W, HEAD_H, HEAD_R)
    ctx.clip()
    # shadow crescent bottom-right
    ctx.rectangle(hx0 - 50, hy0 - 50, HEAD_W + 100, HEAD_H + 100)
    rrect(ctx, hx0 - 16, hy0 - 18, HEAD_W, HEAD_H, HEAD_R)
    ctx.set_fill_rule(1)
    _rgba(ctx, BODY_SH)
    ctx.fill()
    # rim light crescent top-left
    ctx.rectangle(hx0 - 50, hy0 - 50, HEAD_W + 100, HEAD_H + 100)
    rrect(ctx, hx0 + 9, hy0 + 9, HEAD_W, HEAD_H, HEAD_R)
    _rgba(ctx, RIM, 0.95)
    ctx.fill()
    ctx.set_fill_rule(0)
    ctx.restore()
    rrect(ctx, hx0, hy0, HEAD_W, HEAD_H, HEAD_R)
    _rgba(ctx, INK)
    ctx.set_line_width(INK_W)
    ctx.stroke()

    # little status LED on the chin bezel
    circle(ctx, 0, SCR_Y + SCR_H + 22, 6)
    _rgba(ctx, _mixc(GLOW, hexc("ai_accent"), clamp(think * 2)), 0.9)
    ctx.fill()

    # screen
    rrect(ctx, SCR_X, SCR_Y, SCR_W, SCR_H, SCR_R)
    _rgba(ctx, SCREEN)
    ctx.fill_preserve()
    _rgba(ctx, INK)
    ctx.set_line_width(5)
    ctx.stroke()

    # face parallax
    fdx, fdy = lx * 14 + shk * 24, ly * 9 + ndd * 12

    ctx.save()
    rrect(ctx, SCR_X + 3, SCR_Y + 3, SCR_W - 6, SCR_H - 6, SCR_R - 3)
    ctx.clip()
    # glass reflection
    gx = -fdx * 0.6
    _poly(ctx, [(SCR_X + 40 + gx, SCR_Y - 10), (SCR_X + 140 + gx, SCR_Y - 10),
                (SCR_X - 10 + gx, SCR_Y + 170), (SCR_X - 60 + gx, SCR_Y + 170)])
    _poly(ctx, [(SCR_X + 168 + gx, SCR_Y - 10), (SCR_X + 198 + gx, SCR_Y - 10),
                (SCR_X + 48 + gx, SCR_Y + 170), (SCR_X + 18 + gx, SCR_Y + 170)])
    ctx.set_source_rgba(1, 1, 1, 0.045)
    ctx.fill()
    # processing scanline
    if e["scan"] > 0.02:
        sp = (t * 0.9) % 1.0
        yy = SCR_Y - 30 + sp * (SCR_H + 60)
        ctx.rectangle(SCR_X, yy - 34, SCR_W, 34)
        _rgba(ctx, GLOW, 0.07 * e["scan"])
        ctx.fill()
        ctx.rectangle(SCR_X, yy - 3, SCR_W, 4)
        _rgba(ctx, GLOW, 0.4 * e["scan"])
        ctx.fill()

    eye_col = _mixc(SCREEN, EYE, clamp(0.55 + 0.45 * g))
    face_col = eye_col

    # blush
    if e["blush"] > 0.02:
        for sx in (-1, 1):
            bx_, by_ = sx * 170 + fdx, 62 + fdy
            ellipse(ctx, bx_, by_, 42, 17)
            _rgba(ctx, BLUSH, 0.5 * e["blush"])
            ctx.fill()
            for k in (-1, 0, 1):                      # little /// blush ticks
                ctx.move_to(bx_ + k * 17 + 5, by_ - 9)
                ctx.line_to(bx_ + k * 17 - 5, by_ + 9)
            _rgba(ctx, BLUSH_HI, 0.95 * e["blush"])
            ctx.set_line_width(5)
            ctx.stroke()

    # pupils
    sac = _saccade(t, seed)
    sk = e["sacc"]
    ppx = e["px"] + lx + sac[0] * sk
    ppy = e["py"] + ly + sac[1] * sk
    m = math.hypot(ppx, ppy)
    if m > 1:
        ppx, ppy = ppx / m, ppy / m

    # blink
    bl = blink_amount(t, seed) if blink is None else clamp(blink)
    bl *= e["bk"]
    out_eyes = {}
    for side, sx in (("L", -1), ("R", 1)):
        es = e["es"] * (e["eLs"] if side == "L" else e["eRs"])
        rx, ry = EYE_RX * es, EYE_RY * es
        cx, cy = sx * EYE_X + fdx, EYE_Y + fdy
        inner = -sx
        T = e["t" + side]
        B = e["l" + side]
        tt = e["tt" + side]
        w = clamp(bl + e["w" + side])
        pr = rx * 0.44 * e["ps"]
        pup = (cx + ppx * rx * 0.56 * e["pr"], cy + ppy * ry * 0.44 * e["pr"])
        _draw_eye(ctx, cx, cy, rx, ry, T, tt, e["tc"], B, e["lc"], inner, w, pup, pr, g, eye_col)
        # brow (lifts a hair while talking)
        by = cy - ry - BROW_GAP - e["b" + side + "y"] - op_talk * 5
        _draw_brow(ctx, cx, by, e["b" + side + "a"], e["arch"], inner, g, face_col)
        out_eyes[side] = (cx, cy)

    _draw_mouth(ctx, e, (op_talk, wide), fdx, fdy, ppx, g, face_col)
    ctx.restore()  # screen clip

    # thinking: light sweep round the bezel + data ticks
    if think > 0.02:
        p0 = (t * 0.75) % 1.0
        bx, by_, bw, bh, br = hx0 + 14, hy0 + 14, HEAD_W - 28, HEAD_H - 28, HEAD_R - 14
        pts = [_rrect_point(bx, by_, bw, bh, br, p0 - 0.16 * i / 11) for i in range(12)]
        for wdt, a, c in ((26, 0.22, GLOW), (9, 0.95, EYE)):
            ctx.move_to(*pts[0])
            for p in pts[1:]:
                ctx.line_to(*p)
            _rgba(ctx, c, a * think)
            ctx.set_line_width(wdt)
            ctx.set_line_cap(1)
            ctx.stroke()
        # data ticks on the chin bezel
        k = math.floor(t * 10)
        for i in range(6):
            on = hash01(k * 7 + i, seed + 3) < 0.55
            xx = -150 + i * 22 + (0 if i < 3 else 216)
            ctx.rectangle(xx, SCR_Y + SCR_H + 18, 12, 6)
            _rgba(ctx, EYE if on else GLOW, (0.95 if on else 0.25) * think)
            ctx.fill()

    # world-space anchors (head-local -> world)
    ct, st_ = math.cos(tilt), math.sin(tilt)

    def W2(px_, py_):
        X = px_ * ct - py_ * st_
        Y = px_ * st_ + py_ * ct + bob
        return (x + (X + hx) * s, y + Y * s)

    out["face"] = W2(fdx, fdy)
    out["eyeL"] = W2(*out_eyes["L"])
    out["eyeR"] = W2(*out_eyes["R"])
    out["mouth"] = W2(e["mx"] + e["mlook"] * ppx + fdx, MOUTH_Y + e["my"] + fdy)
    out["halo"] = W2(0, HALO_Y)
    out["top"] = W2(0, -HEAD_H / 2)
    ctx.restore()  # head group

    # --- hands --------------------------------------------------------------
    _draw_keyboard(ctx, hp["kb"], t, g, hp)
    for side, mirror, phase in (("L", False, 0.0), ("R", True, 1.3)):
        h = dict(hp[side])
        h["y"] += math.sin(ph - 0.7 - phase) * 7 + bob * 0.3
        h["x"] += math.sin(ph * 0.5 + phase) * 3
        _draw_hand(ctx, h, mirror, g)
        for which in ("palm", "tip"):
            hxp, hyp = _hand_world(h, mirror, which)
            out["hand" + side + ("" if which == "palm" else "_tip")] = (x + hxp * s, y + hyp * s)
    ctx.restore()
    return out


# ---------------------------------------------------------------------------
# helpers for scenes
# ---------------------------------------------------------------------------
# Bounding box at s=1 relative to (x, y), covering halo, stand and every pose.
BBOX = (-452, -374, 454, 386)


def ai_bbox(x, y, s):
    return (x + BBOX[0] * s, y + BBOX[1] * s, x + BBOX[2] * s, y + BBOX[3] * s)
