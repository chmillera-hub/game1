"""THE CRAWLER - the cave monster of ANGER (BIBLE.md section 2), plus the hermit's glove (THE VOICE).

Procedural 2D rig in the film's style (clean vector, soft cel shading, thin dark contours).

Public API
    draw(canvas, pose, t)          the crawler, body pass (the eyes are drawn as lit, NOT emissive)
    draw_eyes(canvas, pose, t)     emissive pass: the four glowing eyes (bright cores + additive halos). Scenes
                                   draw it AFTER the darkness overlay so the eyes read in total darkness. It uses
                                   the same canvas transform (camera) as draw().
    head_pos(pose, t=0.0)          stage point between the (near) eyes
    mouth_pos(pose, t=0.0)         stage point at the front of the mouth opening (between the jaw tips)
    tail_tip(pose, t=0.0)          stage point of the tail tip (where the glove grabs it)
    eye_points(pose, t=0.0)        [(x, y, r, openness, glow)] of the 4 eyes in stage units (glow already scaled)
    drool_drops(pose, t)           [(x, y)] stage points of drool drops currently falling (for splat sfx/fx)
    draw_glove(canvas, x, y, scale=1.0, grip=0.0, angle=0.0, alpha=1.0, layer="all")
                                   the hermit's leather work glove + ragged sleeve fading into darkness
    glove_grip_point(x, y, scale=1.0, angle=0.0)   == (x, y): the grip axis passes through it (documented anchor)
    HEIGHT    top of the hunched spine (creep) at scale 1, ridge plates not included (255; plates add ~25)
    LENGTH    snout to tail tip in "creep" (945)
    ADVANCE   {"creep": 120, "scurry": 290} stage units the body must move (toward facing) per gait cycle
    CYCLE     suggested seconds per gait cycle {"creep": 1.5, "scurry": 0.34}
    LUNGE_REACH  forward travel built into "lunge" at phase 1 (~250; the rig moves itself, keep pose.x fixed)
    STATES    tuple of state names

Pose fields used
    x, y        floor point under the middle of the body (stage units). scale. facing +1 = head to screen-right.
    lean        whole-body pitch in degrees (+ = nose up / rearing), about a point 150 above the floor
    head_tilt   extra head angle in degrees (+ = snout down)
    lid_l/lid_r None = automatic (de-synced, creepy) blinks; a value 0..1 forces all four lids
    look_x/look_y   front view: eye-core darts (-1..1); side view: ignored
    light, tint, tint_amt   lighting colour filter (core.light_filter, perceptual curve light**0.65)
    rim, rim_color          thin rim-light edge on the upper silhouette (0..1)
pose.extra keys
    state   "lurk" (only the eyes in a dark crevice, blinking; front view), "scurry" (fast low run, phase),
            "creep" (slow stalk, phase), "snarl" (jaw open, drool dripping, tongue hanging, head low and close),
            "lunge" (phase 0..1: coil 0-0.35, spring 0.35-0.65, extended 0.65-1), "ko" (knocked out: limp,
            eyes dim / rolled, tongue lolling, a bump on the head), "dragged" (limp, pulled backward by the tail)
    phase   gait cycles for scurry / creep (advance pose.x by ADVANCE[state] * scale per cycle), 0..1 for lunge
    state2, mix   blend toward a second side-view state (mix 0..1), e.g. ko -> dragged, creep -> snarl
    view    "side" (default) | "front" (facing the camera: "lurk" always; "creep" = approaching with a sway,
            "snarl" and "lunge" = the head looming at the camera, "ko")
    jaw 0..1, drool 0..1, eye_glow 0..1, tongue 0..1   (None / missing = the state's default)
    tail_to   (x, y) STAGE point the tail tip is pulled to in "dragged" (the glove); default behind and up
    bump      0..1 size of the KO bump (default 1 in ko / dragged)
    body_alpha  silhouette opacity in "lurk" (default 0.55 of a near-black shape)
    twitch    0..1 small involuntary leg twitches in ko (default 1)
"""
from __future__ import annotations

import math

import skia

from anim.core import auto_blink, clamp, col, ease_in_out, ease_out, hash01, lerp, light_filter, mix_col, noise1
from anim.core import paint as _core_paint
from anim.core import smooth_path, smoothstep
from anim.rig import Pose

# --------------------------------------------------------------------------- constants
HEIGHT = 255.0
LENGTH = 945.0
STATES = ("lurk", "scurry", "creep", "snarl", "lunge", "ko", "dragged")
_GAIT = {   # duty, stride (foot sweep relative to the body), lift
    "creep": (0.75, 90.0, 30.0),
    "scurry": (0.44, 128.0, 46.0),
}
ADVANCE = {k: v[1] / v[0] for k, v in _GAIT.items()}     # creep 120, scurry ~291
CYCLE = {"creep": 1.5, "scurry": 0.34}
LUNGE_REACH = 250.0
TAIL_N = 22
TAIL_SEG = 22.0
D2R = math.pi / 180.0

# leg geometry: (joint offset from S/P, L1, L2, L3, foot dir (F -> wrist/hock), knee forward)
FRONT = dict(off=(-8.0, 58.0), L=(70.0, 78.0, 44.0), fd=(-0.30, -0.95), fwd=False, home=24.0)
HIND = dict(off=(14.0, 40.0), L=(80.0, 86.0, 64.0), fd=(-0.58, -0.81), fwd=True, home=-16.0)

# --------------------------------------------------------------------------- palette
C_SKIN = col("m_skin")
C_SKIN_SH = mix_col("m_skin", "#07060A", 0.55)
C_SKIN_HI = col("m_skin_hi")
C_FAR = mix_col("m_skin", "#07060A", 0.38)
C_FAR_SH = mix_col("m_skin", "#07060A", 0.7)
C_BELLY = mix_col("m_skin", "#5A4E58", 0.45)
C_GLOSS = col("#9C9AB8")
C_LINE = col("ink")
C_RIDGE = mix_col("m_skin", "#07060A", 0.35)
C_RIDGE_HI = mix_col("m_skin_hi", "#B8B4CC", 0.25)
C_CLAW = col("#D8CFB8")
C_CLAW_DK = col("#4A443C")
C_GUM = col("m_gum")
C_GUM_SH = mix_col("m_gum", "#1A0508", 0.5)
C_TOOTH = col("m_tooth")
C_TOOTH_SH = mix_col("m_tooth", "#7A6E5A", 0.5)
C_MOUTH = col("#12060A")
C_TONGUE = mix_col("m_gum", "#E07A8C", 0.45)
C_TONGUE_SH = mix_col("m_gum", "#1A0508", 0.25)
C_TONGUE_HI = col("#F2A6B2")
C_DROOL = col("m_drool")
C_EYE = col("m_eye")
C_EYE_GLOW = col("m_eye_glow")
C_EYE_CORE = col("#FBFFE0")
C_EYE_DEAD = mix_col("m_eye", "#2B2A33", 0.72)
C_BUMP = mix_col("m_skin_hi", "#7A4A6A", 0.3)
WHITE = col("#FFFFFF")

# --------------------------------------------------------------------------- lighting-aware paint
_CF = None
_CF_KEY = None
_PAINT_CACHE = {}


def paint(color, alpha=1.0, **kw):
    """core.paint plus the current lighting colour filter (plain paints cached)."""
    if kw.get("shader") is None and kw.get("blend") is None:
        key = (color, round(alpha, 3), kw.get("stroke", 0.0), kw.get("blur", 0.0), kw.get("cap", "round"), _CF_KEY)
        p = _PAINT_CACHE.get(key)
        if p is None:
            p = _core_paint(color, alpha, **kw)
            if _CF is not None:
                p.setColorFilter(_CF)
            if len(_PAINT_CACHE) > 4000:
                _PAINT_CACHE.clear()
            _PAINT_CACHE[key] = p
        return p
    p = _core_paint(color, alpha, **kw)
    if _CF is not None:
        p.setColorFilter(_CF)
    return p


def _set_light(pose):
    global _CF, _CF_KEY
    lit = pose.light != 1.0 or pose.tint_amt > 0
    if lit:
        _CF = light_filter(max(0.0, pose.light) ** 0.65, pose.tint, pose.tint_amt)
        _CF_KEY = (round(pose.light, 3), tuple(pose.tint), round(pose.tint_amt, 3))
    else:
        _CF, _CF_KEY = None, None


def _clear_light():
    global _CF, _CF_KEY
    _CF, _CF_KEY = None, None


# --------------------------------------------------------------------------- geometry helpers
def _norm(x, y):
    d = math.hypot(x, y)
    if d < 1e-9:
        return 0.0, 0.0
    return x / d, y / d


def _rot(p, a_deg, o=(0.0, 0.0)):
    a = a_deg * D2R
    ca, sa = math.cos(a), math.sin(a)
    x, y = p[0] - o[0], p[1] - o[1]
    return (o[0] + x * ca - y * sa, o[1] + x * sa + y * ca)


def _add(a, b, k=1.0):
    return (a[0] + b[0] * k, a[1] + b[1] * k)


def _lp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def _cr(path, pts, move=True, tension=0.5):
    n = len(pts)
    if move:
        path.moveTo(pts[0][0], pts[0][1])
    else:
        path.lineTo(pts[0][0], pts[0][1])
    k = tension / 3.0
    for i in range(n - 1):
        p0 = pts[i - 1] if i > 0 else pts[0]
        p1 = pts[i]
        p2 = pts[i + 1]
        p3 = pts[i + 2] if i + 2 < n else pts[n - 1]
        path.cubicTo(p1[0] + (p2[0] - p0[0]) * k, p1[1] + (p2[1] - p0[1]) * k,
                     p2[0] - (p3[0] - p1[0]) * k, p2[1] - (p3[1] - p1[1]) * k, p2[0], p2[1])
    return path


def _curve(pts, tension=0.5):
    return _cr(skia.Path(), pts, True, tension)


def _ribbon(center, widths, tension=0.5):
    """Closed tapered ribbon around a polyline; widths are full widths per point. Round end caps."""
    n = len(center)
    L, R = [], []
    for i in range(n):
        a = center[max(i - 1, 0)]
        b = center[min(i + 1, n - 1)]
        nx, ny = _norm(-(b[1] - a[1]), b[0] - a[0])
        w = widths[i] * 0.5
        L.append((center[i][0] + nx * w, center[i][1] + ny * w))
        R.append((center[i][0] - nx * w, center[i][1] - ny * w))
    p = skia.Path()
    _cr(p, L, tension=tension)
    # rounded tip
    tx, ty = _norm(center[-1][0] - center[-2][0], center[-1][1] - center[-2][1])
    w = widths[-1] * 0.5
    p.quadTo(center[-1][0] + tx * w * 1.6 + (L[-1][0] - center[-1][0]) * 0.3,
             center[-1][1] + ty * w * 1.6 + (L[-1][1] - center[-1][1]) * 0.3, R[-1][0], R[-1][1])
    _cr(p, R[::-1], move=False, tension=tension)
    p.close()
    return p


def _capsule(a, b, ra, rb, bulge=0.0):
    dx, dy = b[0] - a[0], b[1] - a[1]
    ux, uy = _norm(dx, dy)
    if ux == 0 and uy == 0:
        p = skia.Path()
        p.addCircle(a[0], a[1], max(ra, rb))
        return p
    nx, ny = -uy, ux
    m = (a[0] + dx * 0.5, a[1] + dy * 0.5)
    rm = (ra + rb) * 0.5 + bulge
    pts = [(a[0] + nx * ra, a[1] + ny * ra), (m[0] + nx * rm, m[1] + ny * rm), (b[0] + nx * rb, b[1] + ny * rb),
           (b[0] + ux * rb, b[1] + uy * rb),
           (b[0] - nx * rb, b[1] - ny * rb), (m[0] - nx * rm, m[1] - ny * rm), (a[0] - nx * ra, a[1] - ny * ra),
           (a[0] - ux * ra, a[1] - uy * ra)]
    return smooth_path(pts, closed=True, tension=0.55)


def _fill(c, path, color, alpha=1.0, blur=0.0):
    c.drawPath(path, paint(color, alpha, blur=blur))


def _stroke(c, path, color, width, alpha=1.0, blur=0.0):
    c.drawPath(path, paint(color, alpha, stroke=width, blur=blur))


def _cel(c, path, base, shade, dx, dy, line=C_LINE, line_w=1.25, line_a=0.85, rim=None):
    """Cel shading: contour underlay, shade fill, base shifted toward the light (clipped)."""
    if line is not None:
        c.drawPath(path, paint(line, line_a, stroke=line_w * 2.0))
    _fill(c, path, shade)
    c.save()
    c.clipPath(path, doAntiAlias=True)
    c.translate(dx, dy)
    _fill(c, path, base)
    c.restore()
    if rim is not None:
        rim.append(path)
    return path


def _ik(a, b, l1, l2, fwd):
    dx, dy = b[0] - a[0], b[1] - a[1]
    d0 = math.hypot(dx, dy)
    d = max(abs(l1 - l2) + 1e-3, min(l1 + l2 - 1e-3, d0))
    ang = math.atan2(dy, dx)
    ca = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)
    A = math.acos(max(-1.0, min(1.0, ca)))
    j1 = (a[0] + l1 * math.cos(ang + A), a[1] + l1 * math.sin(ang + A))
    j2 = (a[0] + l1 * math.cos(ang - A), a[1] + l1 * math.sin(ang - A))
    return j1 if (j1[0] > j2[0]) == fwd else j2


def _blend(a, b, k):
    """Recursive lerp of skeleton values (floats, tuples, lists, dicts)."""
    if isinstance(a, dict):
        return {key: _blend(a[key], b[key], k) if key in b else a[key] for key in a}
    if isinstance(a, (list, tuple)):
        out = [_blend(x, y, k) for x, y in zip(a, b)]
        return tuple(out) if isinstance(a, tuple) else out
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a + (b - a) * k
    return b if k >= 0.5 else a


# --------------------------------------------------------------------------- side-view skeleton
def _gait_foot(ph, off, duty, stride, lift, home):
    q = (ph + off) % 1.0
    if q < duty:
        u = q / duty
        return home + stride * (0.5 - u), 0.0, 0.0
    v = (q - duty) / (1.0 - duty)
    e = ease_in_out(v)
    s = math.sin(math.pi * v)
    return home + stride * (-0.5 + e), -lift * s, s


def _leg(J0, F, spec, fd=None):
    """IK leg -> [J0, K, W, F]. fd overrides the foot direction (F -> wrist)."""
    L1, L2, L3 = spec["L"]
    fdx, fdy = fd if fd is not None else spec["fd"]
    W = (F[0] + fdx * L3, F[1] + fdy * L3)
    K = _ik(J0, W, L1, L2, spec["fwd"])
    # if the target is out of reach, slide the wrist along K->W so segment lengths hold
    kx, ky = _norm(W[0] - K[0], W[1] - K[1])
    W2 = (K[0] + kx * L2, K[1] + ky * L2)
    if math.hypot(W[0] - J0[0], W[1] - J0[1]) > L1 + L2:
        W = W2
    return [J0, K, W, F]


def _leg_fk(J0, angs, spec):
    """FK leg from absolute segment angles (deg, 0 = +x, y down)."""
    pts = [J0]
    p = J0
    for a, L in zip(angs, spec["L"]):
        p = (p[0] + L * math.cos(a * D2R), p[1] + L * math.sin(a * D2R))
        pts.append(p)
    return pts


def _tail_chain(base, h0, curl, amp, freq, t, phase_k=0.42, ground=True, n=TAIL_N, seg=TAIL_SEG, extra=None):
    pts = [base]
    h = h0
    p = base
    for i in range(1, n):
        k = i / (n - 1)
        w = amp * (0.25 + 0.75 * k) * math.sin(2 * math.pi * freq * t - i * phase_k)
        hh = h + curl * i + w
        if extra:
            hh += extra(i, k)
        p = (p[0] + seg * math.cos(hh * D2R), p[1] + seg * math.sin(hh * D2R))
        if ground and p[1] > -4.0:
            p = (p[0], -4.0)
        pts.append(p)
    return pts


def _tail_to(base, target, t, sag_k=1.0, n=TAIL_N, seg=TAIL_SEG):
    """Tail from base to a target point; sags when slack, wiggles a little with the drag."""
    L = seg * (n - 1)
    dx, dy = target[0] - base[0], target[1] - base[1]
    d = math.hypot(dx, dy)
    slack = math.sqrt(max(0.0, L * L - d * d)) * 0.42 * sag_k
    mid = ((base[0] + target[0]) * 0.5, (base[1] + target[1]) * 0.5 + slack)
    pts = []
    for i in range(n):
        u = i / (n - 1)
        x = (1 - u) ** 2 * base[0] + 2 * (1 - u) * u * mid[0] + u * u * target[0]
        y = (1 - u) ** 2 * base[1] + 2 * (1 - u) * u * mid[1] + u * u * target[1]
        y += math.sin(u * math.pi) * 4.0 * noise1(t * 6.0 + u * 3.0, 41)
        if y > -4.0:
            y = -4.0
        pts.append((x, y))
    if d > 1e-3:
        pts[-1] = target
    return pts


def _side_skel(state, ph, t, ex):
    """Skeleton dict for a side-view state (local frame: facing +1, floor origin, y down)."""
    S = {}
    jaw_d = {"creep": 0.06, "scurry": 0.18, "snarl": 0.78, "lunge": 0.0, "ko": 0.26, "dragged": 0.3}[state]
    tongue_d = {"creep": 0.0, "scurry": 0.12, "snarl": 0.5, "lunge": 0.15, "ko": 0.55, "dragged": 0.6}[state]
    S["glow"] = 1.0 if state not in ("ko", "dragged") else 0.13
    S["lid"] = 1.0 if state not in ("ko", "dragged") else 0.4
    S["roll"] = 0.0 if state not in ("ko", "dragged") else 1.0
    S["brow"] = {"creep": 0.4, "scurry": 0.3, "snarl": 1.0, "lunge": 1.0, "ko": -0.6, "dragged": -0.6}[state]
    S["bump"] = 1.0 if state in ("ko", "dragged") else 0.0
    S["flat"] = 0.0
    S["tongue_mode"] = 0.0      # 0 hang from the jaw tip, 1 loll out of the side onto the ground
    S["snarl_lip"] = 1.0 if state in ("snarl", "lunge") else 0.25
    legs = [None] * 4           # near front, far front, near hind, far hind
    claws = [0.0] * 4
    twitch = ex.get("twitch", 1.0)

    if state in ("creep", "scurry"):
        duty, stride, lift = _GAIT[state]
        if state == "creep":
            offs = (0.25, 0.75, 0.0, 0.5)
            hip_h, sh_h, hump = 186.0, 178.0, 70.0
            b1 = 3.5 * math.sin(2 * math.pi * (2 * ph))
            b2 = 3.5 * math.sin(2 * math.pi * (2 * ph) + 1.3)
            P = (-112.0, -hip_h + b1)
            Sh = (106.0, -sh_h + b2)
            hump_v = hump + 3.0 * math.sin(2 * math.pi * ph * 2 + 0.6)
            H = (Sh[0] + 84.0, Sh[1] + 46.0 + 1.5 * math.sin(2 * math.pi * ph * 2))
            ha = 12.0 + 2.0 * noise1(t * 0.7, 3)
            tail = _tail_chain((P[0] - 26, P[1] + 12), 166.0, 1.7, 7.0, 0.55, t, ground=True)
        else:
            offs = (0.52, 0.04, 0.02, 0.5)
            hip_h, sh_h, hump = 168.0, 160.0, 56.0
            ph2 = 2 * math.pi * ph
            b1 = 8.0 * math.sin(2 * ph2 + 0.4)
            b2 = 8.0 * math.sin(2 * ph2 + 2.0)
            flex = math.sin(ph2)
            P = (-112.0 - 12.0 * flex, -hip_h + b1)
            Sh = (108.0 + 12.0 * flex, -sh_h + b2)
            hump_v = hump + 12.0 * flex
            H = (Sh[0] + 90.0, Sh[1] + 34.0 + 3.0 * math.sin(2 * ph2 + 2.6))
            ha = 6.0 + 3.0 * math.sin(2 * ph2 + 2.2)
            tail = _tail_chain((P[0] - 26, P[1] + 12), 176.0, 0.6, 9.0, 1.0, ph, phase_k=0.38, ground=True)
        S["P"], S["S"], S["hump"], S["H"], S["ha"] = P, Sh, hump_v, H, ha
        for i, (spec, root) in enumerate(((FRONT, Sh), (FRONT, Sh), (HIND, P), (HIND, P))):
            J0 = (root[0] + spec["off"][0], root[1] + spec["off"][1])
            fx, fy, sw = _gait_foot(ph, offs[i], duty, stride, lift, J0[0] + spec["home"] + (6.0 if i % 2 else 0.0))
            fd = _rot(spec["fd"], (-35.0 if spec["fwd"] else 30.0) * sw)
            legs[i] = _leg(J0, (fx, fy), spec, fd=fd)
            claws[i] = 40.0 * sw
        S["tail"] = tail
        S["jaw"] = jaw_d
    elif state == "snarl":
        tr = noise1(t * 14.0, 5) * 1.6
        breathe_ = math.sin(t * 2.0 * math.pi * 0.9)
        P = (-108.0, -200.0 + 2.0 * breathe_)
        Sh = (104.0, -160.0 + 2.5 * breathe_)
        S["P"], S["S"], S["hump"] = P, Sh, 70.0 + 3.0 * breathe_
        S["H"] = (Sh[0] + 90.0 + tr, Sh[1] + 2.0 + tr * 0.6)
        S["ha"] = -9.0 + 1.5 * noise1(t * 3.0, 9)
        for i, (spec, root, fx) in enumerate(((FRONT, Sh, 58.0), (FRONT, Sh, 24.0), (HIND, P, -8.0),
                                              (HIND, P, 20.0))):
            J0 = (root[0] + spec["off"][0], root[1] + spec["off"][1])
            legs[i] = _leg(J0, (J0[0] + fx, 0.0), spec)
        S["tail"] = _tail_chain((P[0] - 26, P[1] + 12), 158.0, 2.2, 13.0, 0.45, t, ground=True)
        S["jaw"] = jaw_d
    elif state == "lunge":
        a = smoothstep(ph / 0.35)
        b = ease_out(clamp((ph - 0.35) / 0.3))
        hold = clamp((ph - 0.65) / 0.35)
        dx = -26.0 * a * (1 - b) + LUNGE_REACH * b
        air = 70.0 * math.sin(math.pi * clamp((ph - 0.42) / 0.58)) if ph > 0.42 else 0.0
        P = (lerp(-118.0, -100.0, b) + dx, lerp(lerp(-186.0, -150.0, a), -180.0, b) - air * 0.6)
        Sh = (lerp(104.0, 146.0, b) + dx, lerp(lerp(-178.0, -140.0, a), -236.0, b) - air)
        S["P"], S["S"], S["hump"] = P, Sh, lerp(lerp(72.0, 92.0, a), 22.0, b)
        S["H"] = (Sh[0] + lerp(lerp(90.0, 70.0, a), 112.0, b), Sh[1] + lerp(lerp(40.0, 34.0, a), 6.0, b))
        S["ha"] = lerp(lerp(12.0, 4.0, a), -14.0, b) + 4.0 * hold
        for i, (spec, root) in enumerate(((FRONT, Sh), (FRONT, Sh), (HIND, P), (HIND, P))):
            J0 = (root[0] + spec["off"][0], root[1] + spec["off"][1])
            if i < 2:
                plant = (J0[0] + spec["home"] - 30.0 * a + (6.0 if i else 0.0) - dx * (1 - b) * 0 , 0.0)
                reach = (J0[0] + 150.0 - 18.0 * i, J0[1] + 62.0 + 10.0 * i)
                F = _lp(plant, reach, b)
                fd = _rot(spec["fd"], -70.0 * b)
                legs[i] = _leg(J0, F, spec, fd=fd)
                claws[i] = -12.0 * b
            else:
                home = (-118.0 + HIND["off"][0] + HIND["home"] + (8.0 if i == 3 else 0.0), 0.0)
                F = home if b < 0.5 else _lp(home, (J0[0] - 175.0, J0[1] + 120.0), (b - 0.5) * 2)
                legs[i] = _leg(J0, F, spec, fd=_rot(spec["fd"], 40.0 * b))
                claws[i] = 30.0 * b
        S["tail"] = _tail_chain((P[0] - 26, P[1] + 12), lerp(162.0, 186.0, b), lerp(2.0, 0.3, b), 6.0, 0.8, t,
                                ground=True)
        S["jaw"] = lerp(0.1, 1.0, b)
    else:   # ko / dragged
        drag = state == "dragged"
        tw = twitch * (math.sin(2 * math.pi * clamp((t % 3.7) / 0.35)) if (t % 3.7) < 0.35 else 0.0)
        tw2 = twitch * (math.sin(2 * math.pi * clamp(((t + 1.6) % 5.3) / 0.3)) if ((t + 1.6) % 5.3) < 0.3 else 0.0)
        S["flat"] = 1.0
        breathe_ = math.sin(t * 2 * math.pi * 0.35) * (0.0 if drag else 1.5)
        if drag:
            tt = ex.get("_tail_local")
            jit = noise1(t * 7.0, 17) * 2.0
            lift = 0.0
            if tt is not None:
                lift = clamp((-tt[1] - 160.0) * 0.25, 0.0, 40.0)
            P = (-110.0, -60.0 - lift + jit)
            Sh = (104.0, -54.0 + jit * 0.5)
            S["H"] = (Sh[0] + 95.0, -40.0 + noise1(t * 5.0, 19) * 2.0)
            S["ha"] = 10.0 + 5.0 * noise1(t * 3.0, 23)
            base = (P[0] - 26, P[1] + 10)
            tgt = tt if tt is not None else (-640.0, -150.0)
            S["tail"] = _tail_to(base, tgt, t)
            # legs trail forward (toward the head) and splay
            fa = [(20.0, 5.0, -5.0), (30.0, 12.0, 0.0), (-6.0, 15.0, 5.0), (8.0, 25.0, 15.0)]
        else:
            P = (-110.0, -60.0 + breathe_)
            Sh = (104.0, -56.0 + breathe_ * 0.6)
            S["H"] = (Sh[0] + 92.0, -40.0)
            S["ha"] = 12.0
            S["tail"] = _tail_chain((P[0] - 26, P[1] + 10), 178.0, -0.25, 1.5, 0.3, t, ground=True,
                                    extra=lambda i, k: (-60.0 * smoothstep((k - 0.82) / 0.18)))
            fa = [(28.0 + 6 * tw, 8.0 + 8 * tw, -4.0), (40.0, 14.0, 2.0), (-176.0, 176.0 + 10 * tw2, 178.0),
                  (-168.0, 172.0, 176.0)]
        S["P"], S["S"], S["hump"] = P, Sh, 12.0 + (0.0 if drag else breathe_ * 0.5)
        for i, (spec, root) in enumerate(((FRONT, Sh), (FRONT, Sh), (HIND, P), (HIND, P))):
            J0 = (root[0] + spec["off"][0] * 0.5, root[1] + spec["off"][1] * 0.6)
            angs = fa[i]
            if drag and i >= 2:
                angs = (angs[0] + 160.0, angs[1] + 150.0, angs[2] + 150.0)
            leg = _leg_fk(J0, angs, spec)
            leg = [(x, min(y, -5.0)) for x, y in leg]
            legs[i] = leg
            claws[i] = 25.0
        S["jaw"] = jaw_d
        S["tongue_mode"] = 1.0
    S["legs"] = legs
    S["claws"] = claws
    S["tongue"] = tongue_d
    return S


def _resolve(pose: Pose, t: float):
    """Full solved rig (skeleton + derived values) for pose at time t."""
    ex = pose.extra or {}
    state = ex.get("state", "creep")
    view = ex.get("view", "side")
    if state == "lurk":
        view = "front"
    R = {"state": state, "view": view, "ex": ex}
    if view == "front":
        return R
    ph = ex.get("phase", 0.0) or 0.0
    # tail target for dragged (stage -> local)
    exl = dict(ex)
    if ex.get("tail_to") is not None:
        exl["_tail_local"] = _to_local(pose, ex["tail_to"])
    sk = _side_skel(state if state in STATES and state != "lurk" else "creep", ph, t, exl)
    s2 = ex.get("state2")
    mix = clamp(ex.get("mix", 0.0) or 0.0)
    if s2 and s2 != "lurk" and mix > 0.0:
        ph2 = ex.get("phase2", ph) or 0.0
        sk2 = _side_skel(s2, ph2, t, exl)
        sk = _blend(sk, sk2, mix)
    # parameter overrides
    jaw = ex.get("jaw")
    sk["jaw"] = sk["jaw"] if jaw is None else clamp(jaw)
    tg = ex.get("tongue")
    sk["tongue"] = sk["tongue"] if tg is None else clamp(tg)
    eg = ex.get("eye_glow")
    if eg is not None:
        sk["glow"] = clamp(eg)
    bump = ex.get("bump")
    if bump is not None:
        sk["bump"] = clamp(bump)
    dr = ex.get("drool")
    if dr is None:
        dr = {"snarl": 1.0, "lunge": 0.6, "ko": 0.5, "dragged": 0.4, "creep": 0.25, "scurry": 0.15}.get(state, 0.2)
    sk["drool"] = clamp(dr)
    sk["ha"] += pose.head_tilt
    _derive(sk)
    R.update(sk)
    return R


def _derive(sk):
    """Spine curve, outline offsets, head matrix."""
    P, Sh, hump, H, ha = sk["P"], sk["S"], sk["hump"], sk["H"], sk["ha"]
    jaw = sk["jaw"]
    ha_eff = ha - jaw * 9.0
    sk["ha_eff"] = ha_eff
    C = ((P[0] + Sh[0]) * 0.5 - 18.0, min(P[1], Sh[1]) - 2.0 * hump)
    body = []
    for i in range(13):
        u = i / 12.0
        x = (1 - u) ** 2 * P[0] + 2 * (1 - u) * u * C[0] + u * u * Sh[0]
        y = (1 - u) ** 2 * P[1] + 2 * (1 - u) * u * C[1] + u * u * Sh[1]
        body.append((x, y))
    # neck: from the shoulders to the top-back of the skull
    Ht = _add(H, _rot((-22.0, -36.0), ha_eff))
    N = (Sh[0] + (Ht[0] - Sh[0]) * 0.45, Sh[1] + (Ht[1] - Sh[1]) * 0.45 - 16.0)
    neck = []
    for i in range(1, 7):
        u = i / 6.0
        x = (1 - u) ** 2 * Sh[0] + 2 * (1 - u) * u * N[0] + u * u * Ht[0]
        y = (1 - u) ** 2 * Sh[1] + 2 * (1 - u) * u * N[1] + u * u * Ht[1]
        neck.append((x, y))
    sk["spine"] = body + neck
    flat = sk.get("flat", 0.0)
    depth = []
    tab = [(0.0, 64.0), (0.2, 56.0), (0.42, 57.0), (0.66, 84.0), (0.86, 96.0), (1.0, 90.0)]
    for i in range(13):
        u = i / 12.0
        for j in range(len(tab) - 1):
            if tab[j][0] <= u <= tab[j + 1][0]:
                k = (u - tab[j][0]) / (tab[j + 1][0] - tab[j][0])
                d = lerp(tab[j][1], tab[j + 1][1], ease_in_out(k))
                break
        depth.append(d * (1.0 - 0.3 * flat))
    for i in range(1, 7):
        v = i / 6.0
        depth.append(lerp(86.0 * (1.0 - 0.25 * flat), 70.0, v ** 0.9))
    sk["depth"] = depth
    norms = []
    sp = sk["spine"]
    for i in range(len(sp)):
        a = sp[max(i - 1, 0)]
        b = sp[min(i + 1, len(sp) - 1)]
        dx, dy = _norm(b[0] - a[0], b[1] - a[1])
        norms.append((dy, -dx))     # "up" normal
    sk["norms"] = norms
    # keep the body above the floor when flat
    if flat > 0:
        for i in range(len(sp)):
            bot = sp[i][1] - norms[i][1] * depth[i]
            if bot > -2.0:
                depth[i] = max(10.0, depth[i] - (bot + 2.0) / max(0.3, -norms[i][1]))


# --------------------------------------------------------------------------- head geometry (head-local)
# x forward along the skull, y down; origin near the jaw hinge / back of the skull.
SKULL_TOP = [(-32.0, -40.0), (-4.0, -56.0), (30.0, -60.0), (58.0, -54.0), (80.0, -44.0), (100.0, -35.0),
             (126.0, -27.0), (147.0, -20.0), (160.0, -10.0), (165.0, 2.0)]
MOUTH_UP = [(161.0, 8.0), (136.0, 10.0), (104.0, 12.0), (72.0, 13.5), (42.0, 14.5), (16.0, 16.0)]
CHEEK = [(16.0, 16.0), (8.0, 30.0), (-14.0, 34.0), (-36.0, 18.0)]
HINGE = (10.0, 17.0)
JAW_TOP = [(20.0, 18.0), (54.0, 17.0), (94.0, 16.0), (130.0, 14.0), (151.0, 12.0), (157.0, 14.0)]
JAW_BOT = [(157.0, 14.0), (152.0, 27.0), (118.0, 38.0), (72.0, 45.0), (30.0, 45.0), (2.0, 37.0), (-8.0, 22.0)]
EYES_SIDE = [((84.0, -30.0), 7.6, 5.0, True), ((60.0, -39.0), 5.6, 3.8, True),
             ((90.0, -40.0), 6.4, 4.2, False), ((65.0, -51.0), 4.8, 3.2, False)]
JAW_MAX = 50.0


def _head_xf(R):
    """skia matrix: head-local -> body-local."""
    m = skia.Matrix()
    m.setTranslate(R["H"][0], R["H"][1])
    m.preRotate(R["ha_eff"])
    return m


def _jaw_xf(R):
    m = skia.Matrix()
    m.setRotate(R["jaw"] * JAW_MAX, HINGE[0], HINGE[1])
    return m


def _map(m, p):
    q = m.mapXY(p[0], p[1])
    return (q.fX, q.fY)


_SKULL = None
_JAW = None


def _skull():
    global _SKULL
    if _SKULL is None:
        p = skia.Path()
        _cr(p, SKULL_TOP, tension=0.5)
        _cr(p, MOUTH_UP, move=False, tension=0.4)
        _cr(p, CHEEK, move=False, tension=0.5)
        p.close()
        _SKULL = p
    return _SKULL


def _jaw_shape():
    global _JAW
    if _JAW is None:
        p = skia.Path()
        _cr(p, JAW_TOP, tension=0.4)
        _cr(p, JAW_BOT, move=False, tension=0.5)
        p.close()
        _JAW = p
    return _JAW


def _teeth_path(line, n, length, up, seed, lean=0.35, w=5.2, jitter=0.35, x_min=None):
    """Needle teeth along a polyline (base line); up=True points toward -y."""
    path = skia.Path()
    # resample the line
    segs = []
    tot = 0.0
    for i in range(len(line) - 1):
        d = math.hypot(line[i + 1][0] - line[i][0], line[i + 1][1] - line[i][1])
        segs.append(d)
        tot += d
    for k in range(n):
        u = (k + 0.5) / n
        target = u * tot
        acc = 0.0
        for i, d in enumerate(segs):
            if acc + d >= target or i == len(segs) - 1:
                f = (target - acc) / max(d, 1e-6)
                a, b = line[i], line[i + 1]
                break
            acc += d
        bx, by = a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f
        tx, ty = _norm(b[0] - a[0], b[1] - a[1])
        nx, ny = (ty, -tx) if up else (-ty, tx)
        # make sure normal points the requested way
        if (ny > 0) == up:
            nx, ny = -nx, -ny
        L = length(u) * (1.0 + jitter * (hash01(k, seed) - 0.5))
        ww = w * (0.8 + 0.4 * hash01(k, seed + 3))
        b0 = (bx - tx * ww * 0.5, by - ty * ww * 0.5)
        b1 = (bx + tx * ww * 0.5, by + ty * ww * 0.5)
        tip = (bx + nx * L - tx * L * lean, by + ny * L - ty * L * lean)
        mid = (bx + nx * L * 0.55 - tx * L * lean * 0.2, by + ny * L * 0.55 - ty * L * lean * 0.2)
        path.moveTo(*b0)
        path.quadTo(mid[0] - tx * ww * 0.3, mid[1] - ty * ww * 0.3, *tip)
        path.quadTo(mid[0] + tx * ww * 0.45, mid[1] + ty * ww * 0.45, *b1)
        path.close()
    return path


# --------------------------------------------------------------------------- transforms
def _matrix(pose: Pose):
    m = skia.Matrix()
    m.setTranslate(pose.x, pose.y)
    m.preScale(pose.scale * (1 if pose.facing >= 0 else -1), pose.scale)
    if pose.lean:
        m.preRotate(-pose.lean, 0.0, -150.0)
    return m


def _to_stage(pose, p):
    return _map(_matrix(pose), p)


def _to_local(pose, p):
    inv = skia.Matrix()
    _matrix(pose).invert(inv)
    return _map(inv, p)


def _down_local(pose):
    """Unit vector of stage 'down' in the local frame (gravity for strands / tongue)."""
    a = pose.lean * D2R
    return (math.sin(a) * (1 if pose.facing >= 0 else 1), math.cos(a))


# --------------------------------------------------------------------------- blink / eyes
def _lids(pose, t, state, base=1.0):
    if pose.lid_l is not None or pose.lid_r is not None:
        v = pose.lid_l if pose.lid_l is not None else pose.lid_r
        return [v * base] * 4
    rate = 2.4 if state == "lurk" else 3.6
    a = auto_blink(t, seed=31, rate=rate)
    b = auto_blink(t + 0.13, seed=57, rate=rate * 1.17)
    return [a * base, b * base, a * base, b * base]


def _eye_side_geo(R, pose, t):
    """[(center(head-local), rx, ry, near, open)]"""
    lids = _lids(pose, t, R["state"], R["lid"])
    out = []
    for i, (cpt, rx, ry, near) in enumerate(EYES_SIDE):
        out.append((cpt, rx, ry, near, lids[i]))
    return out


def _eye_path(cx, cy, rx, ry, openv, brow, tilt=-14.0):
    """Almond eye clipped by the lid: openv 0..1; brow > 0 = angry slant (inner/front end lowered)."""
    p = skia.Path()
    top = cy - ry * (2.0 * openv - 1.0)
    pts = [(cx - rx, cy + ry * 0.1), (cx - rx * 0.2, top - ry * 0.05 * brow), (cx + rx * 0.7, top + ry * 0.35 * brow),
           (cx + rx, cy + ry * 0.15), (cx + rx * 0.3, cy + ry), (cx - rx * 0.5, cy + ry * 0.85)]
    if openv <= 0.02:
        return None
    p = smooth_path(pts, closed=True, tension=0.5)
    m = skia.Matrix()
    m.setRotate(tilt, cx, cy)
    p.transform(m)
    return p


# --------------------------------------------------------------------------- drool
def _strand_state(t, period, seed, lmax):
    """Hanging drool strand: returns (length, drop_r, fall) - fall > 0 means a drop is falling (distance)."""
    ph = (t / period + hash01(seed, 5)) % 1.0
    if ph < 0.78:
        g = ease_in_out(ph / 0.78)
        return lmax * (0.2 + 0.8 * g), 2.4 + 2.6 * g, 0.0
    f = (ph - 0.78) / 0.22
    fall = (f * period * 0.22) ** 2 * 900.0
    return lmax * 0.2 * (1.0 + 2.0 * (1.0 - f)), 2.0, lmax + fall


def _draw_strand(c, a, down, L, r, width=2.2, alpha=0.8, sway=0.0):
    if L <= 1.0:
        return
    end = (a[0] + down[0] * L + sway, a[1] + down[1] * L)
    mid = (a[0] + down[0] * L * 0.5 + sway * 0.3, a[1] + down[1] * L * 0.5)
    pth = skia.Path()
    pth.moveTo(*a)
    pth.quadTo(mid[0], mid[1], *end)
    _stroke(c, pth, C_DROOL, width, alpha * 0.85)
    _stroke(c, pth, WHITE, width * 0.35, alpha * 0.5)
    if r > 0:
        drop = skia.Path()
        drop.moveTo(end[0], end[1] - r * 1.6)
        drop.quadTo(end[0] + r * 1.1, end[1] + r * 0.1, end[0], end[1] + r)
        drop.quadTo(end[0] - r * 1.1, end[1] + r * 0.1, end[0], end[1] - r * 1.6)
        _fill(c, drop, C_DROOL, alpha * 0.9)
        c.drawCircle(end[0] - r * 0.3, end[1] - r * 0.1, r * 0.3, paint(WHITE, alpha * 0.8))


def _draw_drop(c, p, r, alpha=0.85):
    drop = skia.Path()
    drop.moveTo(p[0], p[1] - r * 1.9)
    drop.quadTo(p[0] + r * 1.1, p[1], p[0], p[1] + r)
    drop.quadTo(p[0] - r * 1.1, p[1], p[0], p[1] - r * 1.9)
    _fill(c, drop, C_DROOL, alpha)
    c.drawCircle(p[0] - r * 0.3, p[1] - r * 0.2, r * 0.3, paint(WHITE, alpha * 0.8))


# --------------------------------------------------------------------------- side-view drawing
def _leg_paths(leg, spec):
    J0, K, W, F = leg
    hind = spec is HIND
    if hind:
        upper = _capsule((J0[0] - 4, J0[1] - 10), K, 32.0, 12.0, bulge=7.0)
        lower = _capsule(K, W, 10.0, 6.0, bulge=1.0)
    else:
        upper = _capsule((J0[0] + 6, J0[1] - 44), K, 25.0, 10.0, bulge=5.0)
        lower = _capsule(K, W, 9.0, 6.0, bulge=1.0)
    foot = _capsule(W, F, 6.0, 5.5)
    return upper, lower, foot


def _draw_claws(c, F, claw, near):
    fx, fy = F
    for k, (dl, sp) in enumerate(((44.0, -10.0), (52.0, 0.0), (40.0, 12.0))):
        a = (-4.0 + sp * 0.6 + claw) * D2R
        ax, ay = math.cos(a), math.sin(a)
        b = (fx + ax * 4.0 - 2.0 + k * 2.5, fy - 3.0 + k * 1.2)
        tip = (b[0] + ax * dl, b[1] + ay * dl + 5.0)
        ctrl = (b[0] + ax * dl * 0.6, b[1] + ay * dl * 0.6 - 7.0)
        cp = skia.Path()
        nx, ny = -ay, ax
        cp.moveTo(b[0] - nx * 3.4, b[1] - ny * 3.4)
        cp.quadTo(ctrl[0] - nx * 2.0, ctrl[1] - ny * 2.0, *tip)
        cp.quadTo(ctrl[0] + nx * 1.5, ctrl[1] + ny * 1.5 + 2.0, b[0] + nx * 3.4, b[1] + ny * 3.4)
        cp.close()
        c.drawPath(cp, paint(C_LINE, 0.8, stroke=1.6))
        sh = skia.GradientShader.MakeLinear([b, tip], [C_CLAW_DK, C_CLAW if near else mix_col("#D8CFB8", "#2B2A33", 0.4)])
        c.drawPath(cp, paint(None, shader=sh))
    toe = _capsule((fx - 4, fy - 4), (fx + 12, fy - 2), 6.0, 4.0)
    _fill(c, toe, C_SKIN_SH if near else C_FAR_SH)


def _draw_leg(c, leg, spec, claw, near, rim, part="all"):
    """part: "all" | "under" (upper-limb contour underlay only, drawn before the body) |
    "over" (everything else; the upper limb fill without contour so it merges with the body)."""
    J0, K, W, F = leg
    base = C_SKIN if near else C_FAR
    shade = C_SKIN_SH if near else C_FAR_SH
    hind = spec is HIND
    upper, lower, foot = _leg_paths(leg, spec)
    if part == "under":
        c.drawPath(upper, paint(C_LINE, 0.85, stroke=2.5))
        return
    for pth in (lower, foot):
        _cel(c, pth, base, shade, 1.5, -3.0, rim=rim if near else None)
    _draw_claws(c, F, claw, near)
    if part == "all":
        _cel(c, upper, base, shade, 3.0, -6.0, rim=rim if near else None)
    else:
        _cel(c, upper, base, shade, 3.0, -6.0, line=None)
        if near and rim is not None:
            rim.append(upper)
    # knee / elbow knob blends the joint
    kp = skia.Path()
    kp.addCircle(K[0], K[1], 9.5 if hind else 8.5)
    _fill(c, kp, base)
    if near:
        # bony spur at the elbow (front) / hock (hind)
        if hind:
            kx, ky = W
            tipp = (kx - 15.0, ky - 5.0)
        else:
            kx, ky = K
            bx, by = _norm(K[0] - J0[0], K[1] - J0[1])
            tipp = (kx + bx * 12.0 - 8.0, ky + by * 12.0 - 6.0)
        spur = skia.Path()
        spur.moveTo(kx - 4, ky - 4)
        spur.lineTo(*tipp)
        spur.lineTo(kx + 3, ky + 4)
        spur.close()
        _fill(c, spur, C_RIDGE)
        _stroke(c, spur, C_LINE, 1.0, 0.7)
        # muscle crease + gloss on the upper limb
        if hind:
            cr = _curve([(J0[0] + 18, J0[1] + 4), (K[0] + 6, K[1] - 14), (K[0] - 4, K[1] - 2)])
            g = skia.Path()
            g.moveTo(J0[0] - 18, J0[1] - 10)
            g.quadTo(J0[0] + 6, J0[1] - 28, J0[0] + 26, J0[1] - 12)
        else:
            cr = _curve([(J0[0] - 14, J0[1] - 10), (K[0] - 8, K[1] - 16), (K[0] - 2, K[1] - 2)])
            g = skia.Path()
            g.moveTo(J0[0] - 8, J0[1] - 40)
            g.quadTo(J0[0] + 12, J0[1] - 36, J0[0] + 16, J0[1] - 12)
        _stroke(c, cr, C_SKIN_SH, 2.4, 0.8)
        _stroke(c, g, C_GLOSS, 3.0, 0.4, blur=1.2)


def _body_outline(R):
    sp, nm, dp = R["spine"], R["norms"], R["depth"]
    top = [(p[0] + n[0] * 3.0, p[1] + n[1] * 3.0) for p, n in zip(sp, nm)]
    bot = [(p[0] - n[0] * d, p[1] - n[1] * d) for p, n, d in zip(sp, nm, dp)]
    P = R["P"]
    rump_top = (P[0] - 30.0, P[1] + 8.0)
    rump_bot = (P[0] - 34.0, P[1] + 44.0 * (1.0 - 0.3 * R["flat"]))
    pts = [rump_top] + top + bot[::-1] + [rump_bot]
    return smooth_path(pts, closed=True, tension=0.5), top, bot


def _draw_ridges(c, R, top, tail):
    """Bony ridge plates along the spine and the first part of the tail."""
    sp = R["spine"]
    nm = R["norms"]
    path = skia.Path()
    hi = skia.Path()

    def plate(p, n, size, back=0.55):
        tx, ty = -n[1], n[0]     # along the spine (forward)
        b0 = (p[0] - tx * size * 0.55, p[1] - ty * size * 0.55)
        b1 = (p[0] + tx * size * 0.45, p[1] + ty * size * 0.45)
        tip = (p[0] + n[0] * size - tx * size * back, p[1] + n[1] * size - ty * size * back)
        path.moveTo(*b0)
        path.quadTo((b0[0] + tip[0]) * 0.5 + n[0] * 2, (b0[1] + tip[1]) * 0.5 + n[1] * 2, *tip)
        path.quadTo((b1[0] + tip[0]) * 0.5 + tx * 2, (b1[1] + tip[1]) * 0.5 + ty * 2, *b1)
        path.close()
        hi.moveTo(tip[0], tip[1])
        hi.lineTo(b1[0] - n[0] * 0.5 + tx * -1.0, b1[1] - n[1] * 0.5 + ty * -1.0)

    n_sp = len(sp)
    for i in range(1, n_sp - 2):
        u = i / (n_sp - 1)
        size = 13.0 + 15.0 * math.sin(math.pi * clamp(u * 1.15))
        if i >= 13:
            size *= 0.8
        p = (sp[i][0] + nm[i][0] * 2.0, sp[i][1] + nm[i][1] * 2.0)
        plate(p, nm[i], size)
        if i < n_sp - 3:
            q = ((sp[i][0] + sp[i + 1][0]) * 0.5 + nm[i][0] * 2.0, (sp[i][1] + sp[i + 1][1]) * 0.5 + nm[i][1] * 2.0)
            plate(q, nm[i], size * 0.62)
    # tail ridges
    for i in range(1, 9):
        a, b = tail[i - 1], tail[i]
        tx, ty = _norm(a[0] - b[0], a[1] - b[1])      # tail runs backward; forward = toward the body
        n = (ty, -tx)
        if n[1] > 0:
            n = (-n[0], -n[1])
        w = 30.0 * (1.0 - i / 22.0)
        p = (b[0] + n[0] * w * 0.42, b[1] + n[1] * w * 0.42)
        plate(p, n, 15.0 * (1.0 - i / 10.0) + 3.0, back=0.5)
    c.drawPath(path, paint(C_LINE, 0.8, stroke=2.2))
    _fill(c, path, C_RIDGE)
    _stroke(c, hi, C_RIDGE_HI, 1.4, 0.6)


def _tail_widths(n=TAIL_N):
    return [max(3.0, 40.0 * (1.0 - i / (n - 1)) ** 0.85) for i in range(n)]


def _draw_side(c, R, pose, t):
    rim = []
    legs = R["legs"]
    claws = R["claws"]
    specs = (FRONT, FRONT, HIND, HIND)
    # far legs
    for i in (3, 1):
        _draw_leg(c, legs[i], specs[i], claws[i], False, rim)
    # tail
    tail = R["tail"]
    tpath = _ribbon(tail, _tail_widths())
    _cel(c, tpath, C_SKIN, C_SKIN_SH, 2.0, -6.0, rim=rim)
    g = _curve([(x, y - w * 0.28) for (x, y), w in zip(tail[1:12], _tail_widths()[1:12])])
    _stroke(c, g, C_GLOSS, 2.4, 0.35, blur=1.0)
    # body (near upper limbs: contour underlay first so they merge with the body)
    body, top, bot = _body_outline(R)
    _draw_ridges(c, R, top, tail)
    _draw_leg(c, legs[2], HIND, claws[2], True, rim, part="under")
    _draw_leg(c, legs[0], FRONT, claws[0], True, rim, part="under")
    _cel(c, body, C_SKIN, C_SKIN_SH, 4.0, -15.0, rim=rim)
    c.save()
    c.clipPath(body, doAntiAlias=True)
    # pale-ish underside
    under = _curve([(b[0], b[1] + 6) for b in bot[2:13]])
    _stroke(c, under, C_BELLY, 14.0, 0.35, blur=5.0)
    # ribs
    sp, nm, dp = R["spine"], R["norms"], R["depth"]
    for k, i in enumerate((7, 8, 9, 10)):
        p, n, d = sp[i], nm[i], dp[i]
        a = (p[0] - n[0] * 22.0, p[1] - n[1] * 22.0)
        b = (p[0] - n[0] * d * 0.8 - 10.0, p[1] - n[1] * d * 0.8)
        m = ((a[0] + b[0]) * 0.5 + 9.0, (a[1] + b[1]) * 0.5)
        rp = skia.Path()
        rp.moveTo(*a)
        rp.quadTo(*m, *b)
        _stroke(c, rp, C_SKIN_SH, 3.0, 0.7)
        _stroke(c, rp, C_SKIN_HI, 1.2, 0.35)
    # slick gloss along the back
    gl = _curve([(p[0] - n[0] * 11.0, p[1] - n[1] * 11.0) for p, n in zip(sp[1:15], nm[1:15])])
    _stroke(c, gl, C_GLOSS, 5.0, 0.32, blur=2.0)
    _stroke(c, gl, C_GLOSS, 1.4, 0.55)
    c.restore()
    # near legs
    _draw_leg(c, legs[2], HIND, claws[2], True, rim, part="over")
    _draw_leg(c, legs[0], FRONT, claws[0], True, rim, part="over")
    # head
    _draw_head_side(c, R, pose, t, rim)
    if pose.rim > 0.01:
        _rim_pass(c, rim, pose)


def _draw_head_side(c, R, pose, t, rim):
    hx = _head_xf(R)
    jx = _jaw_xf(R)
    jaw = R["jaw"]
    c.save()
    c.concat(hx)
    skull = _skull()
    jawp = skia.Path(_jaw_shape())
    jawp.transform(jx)
    # far eyes (peeking above the skull silhouette)
    eyes = _eye_side_geo(R, pose, t)
    glow = R["glow"]
    for (cx, cy), rx, ry, near, op in eyes:
        if near:
            continue
        e = _eye_path(cx, cy, rx, ry, op * 1.0, R["brow"])
        if e is not None:
            _fill(c, e, C_LINE, 0.9)
            _fill(c, _eye_path(cx, cy, rx * 0.82, ry * 0.8, op, R["brow"]),
                  mix_col("m_eye", "#2B2A33", 0.25 + 0.6 * (1 - glow)))
    # mouth interior (between upper mouth line and the rotated jaw top)
    jt = [_map(jx, p) for p in JAW_TOP]
    inner = skia.Path()
    _cr(inner, MOUTH_UP, tension=0.4)
    _cr(inner, [MOUTH_UP[-1], (4.0, 18.0)] + jt[::-1][:1], move=False)
    _cr(inner, jt[::-1], move=False, tension=0.4)
    inner.close()
    _fill(c, inner, C_MOUTH)
    open_k = smoothstep(jaw / 0.25)
    if open_k > 0:
        # far-side teeth deep in the mouth
        far_up = _teeth_path([(x + 3.0, y + 2.0) for x, y in MOUTH_UP[::-1]], 13, lambda u: 9.0 + 12.0 * u, False, 7,
                             w=4.4)
        _fill(c, far_up, C_TOOTH_SH, 0.85 * open_k)
        far_lo = _teeth_path([(x + 3.0, y - 2.0) for x, y in jt], 12, lambda u: 8.0 + 9.0 * u, True, 8, w=4.2)
        _fill(c, far_lo, C_TOOTH_SH, 0.85 * open_k)
        # throat shading
        c.save()
        c.clipPath(inner, doAntiAlias=True)
        c.drawCircle(30.0, 22.0, 40.0, paint(col("#000000"), 0.8, blur=12.0))
        c.restore()
    # lower jaw
    _cel(c, jawp, C_SKIN, C_SKIN_SH, 2.0, -5.0, rim=rim)
    # lower gum band
    gum_lo = _curve([(x, y + 1.5) for x, y in jt[:-1]])
    _stroke(c, gum_lo, C_GUM, 5.0, 0.9 * max(open_k, 0.35))
    # tongue
    _draw_tongue_side(c, R, pose, t, jx, hx)
    lo_teeth = _teeth_path(jt[:-1] + [jt[-1]], 13, lambda u: 9.0 + 9.0 * u + 6.0 * smoothstep((u - 0.8) / 0.2),
                           True, 11, w=5.0)
    c.drawPath(lo_teeth, paint(C_LINE, 0.75, stroke=1.6))
    _fill(c, lo_teeth, C_TOOTH)
    # skull
    _cel(c, skull, C_SKIN, C_SKIN_SH, 3.0, -9.0, rim=rim)
    c.save()
    c.clipPath(skull, doAntiAlias=True)
    # upper gum (lip pulled back when snarling)
    lip = R["snarl_lip"] * (0.4 + 0.6 * open_k)
    gum = skia.Path()
    _cr(gum, MOUTH_UP, tension=0.4)
    _cr(gum, [(x, y - 4.0 - 7.0 * lip * (1.0 - abs((x - 92.0) / 100.0))) for x, y in MOUTH_UP[::-1]], move=False)
    gum.close()
    _fill(c, gum, C_GUM)
    _stroke(c, _curve([(x, y - 3.0 - 7.0 * lip * (1.0 - abs((x - 92.0) / 100.0))) for x, y in MOUTH_UP]), C_GUM_SH,
            1.6, 0.8)
    # snarl wrinkles on the snout
    if lip > 0.3:
        for k in range(3):
            xk = 100.0 + k * 14.0
            wr = skia.Path()
            wr.moveTo(xk, -28.0 + k * 3.5)
            wr.quadTo(xk + 6.0, -16.0 + k * 2.5, xk + 2.0, -3.0 + k)
            _stroke(c, wr, C_SKIN_SH, 2.2, 0.8 * (lip - 0.3) / 0.7)
    # gloss along the skull top
    gl = _curve([(x + 2.0, y + 6.0) for x, y in SKULL_TOP[1:8]])
    _stroke(c, gl, C_GLOSS, 4.0, 0.28, blur=1.5)
    _stroke(c, gl, C_GLOSS, 1.2, 0.5)
    c.restore()
    # nostril
    nos = skia.Path()
    nos.moveTo(149.0, -12.0)
    nos.quadTo(155.0, -14.0, 158.0, -9.0)
    _stroke(c, nos, C_LINE, 2.4, 0.9)
    # upper teeth
    up_teeth = _teeth_path(MOUTH_UP[::-1], 14,
                           lambda u: 9.0 + 10.0 * u + 9.0 * smoothstep((u - 0.78) / 0.12) * (1 - smoothstep((u - 0.93) / 0.07)),
                           False, 13, w=5.4)
    c.drawPath(up_teeth, paint(C_LINE, 0.75, stroke=1.6))
    _fill(c, up_teeth, C_TOOTH)
    # near eyes + brow
    for (cx, cy), rx, ry, near, op in eyes:
        if not near:
            continue
        sock = skia.Path()
        sock.addOval(skia.Rect(cx - rx - 3, cy - ry - 3, cx + rx + 3, cy + ry + 3))
        _fill(c, sock, C_SKIN_SH, 0.9)
        e = _eye_path(cx, cy, rx, ry, op, R["brow"])
        if e is not None:
            _fill(c, e, mix_col("m_eye", "#2B2A33", 0.15 + 0.7 * (1 - glow)))
            c.save()
            c.clipPath(e, doAntiAlias=True)
            # rolled (KO): dull bottom crescent only
            if R["roll"] > 0:
                c.drawRect(skia.Rect(cx - rx, cy - ry * 2, cx + rx, cy + ry * (1.0 - 1.2 * R["roll"])),
                           paint(C_EYE_DEAD, 0.9))
            c.restore()
            _stroke(c, e, C_LINE, 1.1, 0.9)
    br = R["brow"]
    brow = skia.Path()
    brow.moveTo(44.0, -47.0 - 2.0 * br)
    brow.quadTo(70.0, -50.0 + 2.0 * br, 98.0, -36.0 + 5.0 * br)
    _stroke(c, brow, C_RIDGE, 5.0, 0.95)
    _stroke(c, brow, C_RIDGE_HI, 1.2, 0.5)
    # KO bump
    if R["bump"] > 0.01:
        b = R["bump"]
        bp = smooth_path([(4.0 - 4 * b, -56.0), (12.0, -56.0 - 12.0 * b), (24.0, -59.0 - 17.0 * b),
                          (36.0, -59.0 - 12.0 * b), (44.0 + 4 * b, -56.0), (24.0, -50.0)], closed=True)
        _cel(c, bp, C_BUMP, C_SKIN, 1.5, -3.0, line_w=1.0)
        hl = skia.Path()
        hl.moveTo(16.0, -58.0 - 11.0 * b)
        hl.quadTo(24.0, -60.0 - 15.0 * b, 32.0, -58.0 - 11.0 * b)
        _stroke(c, hl, C_GLOSS, 2.2, 0.75)
    # drool
    _draw_drool_side(c, R, pose, t, jx, hx)
    c.restore()


def _tongue_pts(R, pose, t, jx, hx):
    """Tongue centreline in head-local coords."""
    tg = R["tongue"]
    if tg <= 0.01:
        return None
    base = [_map(jx, (40.0, 13.0)), _map(jx, (95.0, 11.0)), _map(jx, (146.0, 7.0))]
    out_len = 170.0 * tg
    n = 9
    seg = out_len / n
    # gravity in head-local: invert the head rotation (and the body lean)
    inv = skia.Matrix()
    hx.invert(inv)
    dl = _down_local(pose)
    g0 = _map(inv, (0.0, 0.0))
    g1 = _map(inv, dl)
    gx, gy = _norm(g1[0] - g0[0], g1[1] - g0[1])
    gang = math.degrees(math.atan2(gy, gx))
    pts = list(base)
    p = base[-1]
    d0 = _norm(base[-1][0] - base[-2][0], base[-1][1] - base[-2][1])
    ang = math.degrees(math.atan2(d0[1], d0[0]))
    mode = R["tongue_mode"]
    # floor in head-local (local y = -3 line)
    for i in range(n):
        k = 0.42 if mode < 0.5 else 0.2
        diff = ((gang - ang + 180.0) % 360.0) - 180.0
        ang += diff * k
        ang += 5.0 * math.sin(t * 2.6 + i * 0.6) * (1.0 - mode)
        p = (p[0] + seg * math.cos(ang * D2R), p[1] + seg * math.sin(ang * D2R))
        pts.append(p)
    # clamp to the floor (body-local y <= -3)
    out = []
    for q in pts:
        b = _map(hx, q)
        if b[1] > -3.0:
            b = (b[0] + (b[1] + 3.0) * 0.6, -3.0)
            q = _map(inv, b)
        out.append(q)
    return out


def _draw_tongue_side(c, R, pose, t, jx, hx):
    pts = _tongue_pts(R, pose, t, jx, hx)
    if pts is None:
        return
    n = len(pts)
    widths = [12.0 + 6.0 * math.sin(math.pi * min(1.0, i / (n - 1) * 1.3)) for i in range(n)]
    widths[-1] = 12.0
    tp = _ribbon(pts, widths)
    _cel(c, tp, C_TONGUE, C_TONGUE_SH, 1.5, -3.5, line_w=1.0)
    _stroke(c, _curve(pts[2:-1]), C_TONGUE_SH, 1.6, 0.7)
    _stroke(c, _curve([(x - 1.0, y - 4.0) for x, y in pts[3:-2]]), C_TONGUE_HI, 1.6, 0.55)


def _draw_drool_side(c, R, pose, t, jx, hx):
    dr = R["drool"]
    if dr <= 0.01:
        return
    jaw = R["jaw"]
    inv = skia.Matrix()
    hx.invert(inv)
    dl = _down_local(pose)
    g0 = _map(inv, (0.0, 0.0))
    g1 = _map(inv, dl)
    down = _norm(g1[0] - g0[0], g1[1] - g0[1])
    # strands between the jaws
    if jaw > 0.15:
        for k, (xu, xl) in enumerate(((130.0, 124.0), (92.0, 86.0), (58.0, 52.0))):
            if k >= 1 + int(dr * 2.99):
                break
            a = (xu, 12.0)
            b = _map(jx, (xl, 14.0))
            d = math.hypot(b[0] - a[0], b[1] - a[1])
            sag = 10.0 + d * 0.55 + 4.0 * math.sin(t * 2.0 + k)
            side = 7.0 * math.sin(t * 1.3 + k * 2.0)
            m = ((a[0] + b[0]) * 0.5 + down[0] * sag + side, (a[1] + b[1]) * 0.5 + down[1] * sag)
            sp = skia.Path()
            sp.moveTo(*a)
            sp.quadTo(*m, *b)
            _stroke(c, sp, C_DROOL, 2.4 - 0.4 * k, 0.75)
            _stroke(c, sp, WHITE, 0.7, 0.45)
            c.drawCircle(a[0], a[1] + 1.5, 2.4, paint(C_DROOL, 0.8))
            c.drawCircle(b[0], b[1] - 1.5, 2.4, paint(C_DROOL, 0.8))
            c.drawCircle(m[0] * 0.5 + (a[0] + b[0]) * 0.25, m[1] * 0.5 + (a[1] + b[1]) * 0.25, 2.2,
                         paint(C_DROOL, 0.8))
    # hanging strands
    anchors = [(_map(jx, (146.0, 32.0)), 2.1, 1), (_map(jx, (100.0, 41.0)), 2.6, 2), ((160.0, 9.0), 1.9, 3)]
    tpts = _tongue_pts(R, pose, t, jx, hx)
    if tpts is not None and R["tongue_mode"] < 0.5:
        anchors.insert(0, (tpts[-1], 1.7, 4))
    for idx, (a, per, seed) in enumerate(anchors):
        if idx >= 1 + int(dr * 3.5):
            break
        L, r, fall = _strand_state(t, per, seed, 40.0 + 70.0 * dr)
        sway = 3.0 * math.sin(t * 3.0 + seed)
        _draw_strand(c, a, down, L, r, sway=sway)
        if fall > 0:
            fp = (a[0] + down[0] * fall, a[1] + down[1] * fall)
            # stop at the floor
            b = _map(hx, fp)
            if b[1] < -2.0:
                _draw_drop(c, fp, 3.2)


def _rim_pass(c, paths, pose):
    """Rim edges of the collected part paths (in draw order). Each part's rim is clipped by the parts drawn
    after it, so an occluded edge (a leg behind the head, the far side of the body) never shows through."""
    a = clamp(pose.rim)
    dx, dy = (-3.5, -3.5)
    if pose.facing < 0:
        dx = -dx
    cover = None
    for pth in reversed(paths):
        c.save()
        c.clipPath(pth, doAntiAlias=True)
        sh = skia.Path(pth)
        sh.offset(-dx, -dy)
        c.clipPath(sh, skia.ClipOp.kDifference, True)
        if cover is not None:
            c.clipPath(cover, skia.ClipOp.kDifference, True)
        c.drawPath(pth, paint(pose.rim_color, a * 0.9))
        c.restore()
        if cover is None:
            cover = skia.Path(pth)
        else:
            u = skia.Op(cover, pth, skia.PathOp.kUnion_PathOp)
            cover = u if u is not None else cover


# --------------------------------------------------------------------------- front view
def _front_params(pose, t, ex):
    st = ex.get("state", "lurk")
    ph = ex.get("phase", 0.0) or 0.0
    F = {"state": st}
    F["jaw"] = {"lurk": 0.0, "creep": 0.1, "snarl": 0.8, "lunge": 1.0, "ko": 0.3}.get(st, 0.2)
    F["tongue"] = {"lurk": 0.0, "creep": 0.15, "snarl": 0.85, "lunge": 0.4, "ko": 0.9}.get(st, 0.0)
    F["drool"] = {"lurk": 0.0, "creep": 0.4, "snarl": 1.0, "lunge": 0.6, "ko": 0.4}.get(st, 0.2)
    F["glow"] = 0.13 if st == "ko" else 1.0
    F["lid"] = 0.4 if st == "ko" else 1.0
    F["brow"] = -0.5 if st == "ko" else 1.0
    F["bump"] = 1.0 if st == "ko" else 0.0
    sway = 0.0
    bob = 0.0
    lift = [0.0, 0.0]
    if st == "creep":
        sway = 14.0 * math.sin(2 * math.pi * ph)
        bob = 4.0 * math.sin(4 * math.pi * ph)
        lift = [max(0.0, math.sin(2 * math.pi * ph)) * 30.0, max(0.0, -math.sin(2 * math.pi * ph)) * 30.0]
    elif st == "snarl":
        sway = 3.0 * noise1(t * 1.3, 4)
        bob = 2.0 * math.sin(t * 2 * math.pi * 0.9) + noise1(t * 14.0, 5) * 1.2
    elif st == "lunge":
        b = ease_out(clamp((ph - 0.35) / 0.3))
        bob = -40.0 * b + 10.0 * smoothstep(ph / 0.35) * (1 - b)
        F["head_s"] = 1.0 + 0.45 * b
    elif st == "lurk":
        sway = 4.0 * noise1(t * 0.4, 8)
        bob = 1.5 * noise1(t * 0.5, 9)
    F["sway"], F["bob"], F["lift"] = sway, bob, lift
    F.setdefault("head_s", 1.0 if st != "snarl" else 1.12)
    F["head_c"] = (sway * 0.6, -178.0 + bob + (40.0 if st == "ko" else 0.0) + (30.0 if st == "snarl" else 0.0))
    if st == "ko":
        F["head_c"] = (0.0, -70.0)
    for k in ("jaw", "tongue", "drool", "eye_glow", "bump"):
        v = ex.get(k)
        if v is not None:
            F["glow" if k == "eye_glow" else k] = clamp(v)
    return F


# front head geometry (head-local, origin = head centre, y down)
FH_EYES = [((-34.0, -30.0), 10.5, 6.5, 0), ((34.0, -30.0), 10.5, 6.5, 1), ((-70.0, -46.0), 7.0, 4.6, 2),
           ((70.0, -46.0), 7.0, 4.6, 3)]


def _front_head_shapes(F):
    jaw = F["jaw"]
    drop = 18.0 + 115.0 * jaw
    corner_y = 18.0 + 6.0 * jaw
    # upper jaw line (teeth line), from left corner to right corner (dips at the snout front)
    up = [(-92.0, corner_y - 4.0), (-70.0, 18.0), (-38.0, 30.0), (0.0, 36.0), (38.0, 30.0), (70.0, 18.0),
          (92.0, corner_y - 4.0)]
    lo = [(-90.0, corner_y), (-66.0, corner_y + drop * 0.45), (-34.0, corner_y + drop * 0.85),
          (0.0, corner_y + drop), (34.0, corner_y + drop * 0.85), (66.0, corner_y + drop * 0.45), (90.0, corner_y)]
    head = [(-106.0, -12.0), (-98.0, -50.0), (-66.0, -78.0), (-24.0, -90.0), (0.0, -84.0), (24.0, -90.0),
            (66.0, -78.0), (98.0, -50.0), (106.0, -12.0), (98.0, 12.0), (70.0, 20.0), (40.0, 32.0), (0.0, 38.0),
            (-40.0, 32.0), (-70.0, 20.0), (-98.0, 12.0)]
    jaw_out = [(-98.0, 4.0), (-96.0, corner_y + 10)] + [(x * 1.12, y + 16.0) for x, y in lo[1:-1]] + \
              [(96.0, corner_y + 10), (98.0, 4.0)]
    return up, lo, head, jaw_out


def _draw_front(c, pose, t, ex, emissive=False):
    F = _front_params(pose, t, ex)
    st = F["state"]
    if emissive:
        return F
    rim = []
    body_a = 1.0
    if st == "lurk":
        body_a = ex.get("body_alpha", 0.55)
    if st == "lurk":
        # a near-black shape in the crevice: everything (teeth included) crushed toward black
        lp = skia.Paint()
        lp.setAlphaf(clamp(body_a))
        lp.setColorFilter(light_filter(0.18, (4, 5, 9), 0.5))
        c.saveLayer(None, lp)
    elif body_a < 0.999:
        c.saveLayerAlpha(None, int(255 * clamp(body_a)))
    base = C_SKIN if st != "lurk" else mix_col("m_skin", "#000000", 0.6)
    shade = C_SKIN_SH if st != "lurk" else mix_col("m_skin", "#000000", 0.8)
    sway, bob = F["sway"], F["bob"]
    hc = F["head_c"]
    ko = st == "ko"
    if st != "lurk":
        # tail curling round from behind
        tl = [(30.0 + sway * 0.2, -150.0)]
        for i in range(1, TAIL_N):
            k = i / (TAIL_N - 1)
            ang = -20.0 + 150.0 * k + 18.0 * math.sin(t * 1.4 - k * 3.0)
            p = tl[-1]
            tl.append((p[0] + 18.0 * math.cos((ang - 70) * D2R) * 1.2, min(-4.0, p[1] + 18.0 * math.sin((ang - 70) * D2R))))
        _cel(c, _ribbon(tl, [w * 0.85 for w in _tail_widths()]), C_FAR, C_FAR_SH, 2.0, -5.0)
        # hind legs (behind)
        for sgn in (-1, 1):
            hip = (sgn * 85.0 + sway * 0.3, -120.0 + bob * 0.5)
            knee = (sgn * 150.0, -150.0 + (0 if not ko else 120.0))
            foot = (sgn * 120.0, -6.0)
            for a, b, ra, rb in ((hip, knee, 26.0, 16.0), (knee, foot, 14.0, 9.0)):
                _cel(c, _capsule(a, b, ra, rb), C_FAR, C_FAR_SH, 2.0, -4.0)
        # back hump, rising behind the head, with the ridge plates stacked along its centreline
        hump_top = -300.0 + bob * 0.7 if not ko else -150.0
        back = [(-120.0 + sway * 0.4, -150.0 + bob), (-110.0, -228.0 + bob), (-60.0, hump_top + 22.0),
                (0.0 + sway * 0.2, hump_top), (60.0, hump_top + 22.0), (110.0, -228.0 + bob),
                (120.0 + sway * 0.4, -150.0 + bob), (0.0, -120.0 + bob)]
        bp = smooth_path(back, closed=True, tension=0.5)
        _cel(c, bp, base, shade, 3.0, -12.0, rim=rim)
        ridge = skia.Path()
        rhi = skia.Path()
        for k in range(8):
            u = k / 7.0
            x = sway * 0.2 * (1 - u) + 2.0 * math.sin(k * 1.7)
            y = hump_top + 4.0 + u * 96.0
            sz = 18.0 + 16.0 * u
            ridge.moveTo(x - sz * 0.42, y + sz * 0.25)
            ridge.quadTo(x - sz * 0.2, y - sz * 0.4, x + (u - 0.5) * 3.0, y - sz * 0.85)
            ridge.quadTo(x + sz * 0.2, y - sz * 0.4, x + sz * 0.42, y + sz * 0.25)
            ridge.close()
            rhi.moveTo(x + (u - 0.5) * 3.0, y - sz * 0.8)
            rhi.lineTo(x + sz * 0.3, y + sz * 0.1)
        c.drawPath(ridge, paint(C_LINE, 0.8, stroke=2.2))
        _fill(c, ridge, C_RIDGE)
        _stroke(c, rhi, C_RIDGE_HI, 1.3, 0.55)
        # front legs: high spidery elbows, long clawed hands
        for sgn in (-1, 1):
            lf = F["lift"][0 if sgn < 0 else 1]
            sh = (sgn * 104.0 + sway * 0.5, -200.0 + bob - lf * 0.3)
            if not ko:
                elbow = (sgn * 200.0 + sway * 0.3, -226.0 + bob - lf * 0.8)
                wrist = (sgn * 186.0, -30.0 - lf)
                hand = (sgn * 176.0, -4.0 - lf)
            else:
                elbow = (sgn * 210.0, -60.0)
                wrist = (sgn * 270.0, -18.0)
                hand = (sgn * 290.0, -8.0)
            upper = _capsule(sh, elbow, 40.0, 14.0, bulge=8.0)
            lower = _capsule(elbow, wrist, 13.0, 7.5, bulge=2.5)
            handp = _capsule(wrist, hand, 9.0, 11.0)
            _cel(c, lower, base, shade, 2.0 * sgn, -5.0, rim=rim)
            _cel(c, handp, base, shade, 1.0, -3.0)
            # four long claws fanning out, curving toward the camera / down onto the ground
            for k in range(4):
                spread = (k - 1.5) * 0.42
                a = (90.0 - sgn * 8.0) * D2R + spread
                b0 = (hand[0] + (k - 1.5) * 7.0, hand[1] + 2.0)
                L = 34.0 + 8.0 * (1.0 - abs(k - 1.5) / 1.5)
                tip = (b0[0] + math.cos(a) * L * 0.9 + sgn * 6.0 * spread, b0[1] + math.sin(a) * L * 0.55 + 4.0)
                ctrl = (b0[0] + math.cos(a) * L * 0.5, b0[1] - 3.0)
                cp = skia.Path()
                cp.moveTo(b0[0] - 3.6, b0[1])
                cp.quadTo(ctrl[0] - 2.5, ctrl[1], *tip)
                cp.quadTo(ctrl[0] + 2.5, ctrl[1] + 3.0, b0[0] + 3.6, b0[1])
                cp.close()
                c.drawPath(cp, paint(C_LINE, 0.8, stroke=1.6))
                shd = skia.GradientShader.MakeLinear([b0, tip], [C_CLAW_DK, C_CLAW])
                c.drawPath(cp, paint(None, shader=shd))
            _cel(c, upper, base, shade, 3.0 * sgn, -8.0, rim=rim)
            spur = skia.Path()
            spur.moveTo(elbow[0] - sgn * 8, elbow[1] - 6)
            spur.lineTo(elbow[0] + sgn * 14, elbow[1] - 26)
            spur.lineTo(elbow[0] + sgn * 10, elbow[1] + 4)
            spur.close()
            _fill(c, spur, C_RIDGE)
            _stroke(c, spur, C_LINE, 1.0, 0.7)
            gl_ = skia.Path()
            gl_.moveTo(sh[0] - sgn * 10, sh[1] - 26)
            gl_.quadTo((sh[0] + elbow[0]) * 0.5, (sh[1] + elbow[1]) * 0.5 - 22, elbow[0] - sgn * 6, elbow[1] - 12)
            _stroke(c, gl_, C_GLOSS, 3.0, 0.35, blur=1.2)
        chest = smooth_path([(-90.0 + sway * 0.5, -210.0 + bob), (90.0 + sway * 0.5, -210.0 + bob),
                             (70.0, -110.0 + bob), (0.0, -78.0 + bob), (-70.0, -110.0 + bob)], closed=True)
        _cel(c, chest, base, shade, 0.0, -12.0, rim=rim)
    # head
    hs = F["head_s"]
    c.save()
    c.translate(*hc)
    c.scale(hs, hs)
    if ko:
        c.rotate(-24.0)
    up, lo, head, jaw_out = _front_head_shapes(F)
    jaw = F["jaw"]
    # lower jaw outer shape (behind)
    jp = smooth_path(jaw_out, closed=False, tension=0.5)
    jp.close()
    _cel(c, jp, base, shade, 0.0, -6.0, rim=rim)
    # mouth interior
    mouth = skia.Path()
    _cr(mouth, up, tension=0.5)
    _cr(mouth, lo[::-1], move=False, tension=0.5)
    mouth.close()
    if jaw > 0.04:
        _fill(c, mouth, C_MOUTH)
        c.save()
        c.clipPath(mouth, doAntiAlias=True)
        # gums
        _stroke(c, _curve(lo), C_GUM, 10.0, 0.95)
        _stroke(c, _curve(up), C_GUM, 10.0, 0.95)
        # throat
        c.drawCircle(0.0, (up[3][1] + lo[3][1]) * 0.5 + 10.0, 30.0 + 30.0 * jaw, paint(col("#000000"), 0.85,
                                                                                   blur=10.0))
        # far teeth row (back of the mouth)
        bt = _teeth_path([(x * 0.7, y + 10.0) for x, y in up], 12, lambda u: 10.0, False, 21, w=4.2, lean=0.0)
        _fill(c, bt, C_TOOTH_SH, 0.8)
        c.restore()
    # lower teeth (pointing up)
    lt = _teeth_path(lo, 14, lambda u: 12.0 + 10.0 * math.sin(math.pi * u), True, 23, w=5.6, lean=0.0)
    c.drawPath(lt, paint(C_LINE, 0.75, stroke=1.6))
    _fill(c, lt, C_TOOTH)
    # tongue
    tg = F["tongue"]
    if tg > 0.01 and jaw > 0.04:
        sw = 8.0 * math.sin(t * 2.2)
        L = 40.0 + 200.0 * tg
        top_y = lo[3][1] - 26.0
        tpts = [(0.0, top_y), (sw * 0.2, lo[3][1] - 4.0), (sw * 0.6, lo[3][1] + L * 0.4),
                (sw, lo[3][1] + L * 0.8), (sw * 0.9, lo[3][1] + L)]
        tw = [34.0, 38.0, 32.0, 28.0, 24.0]
        tp = _ribbon(tpts, tw)
        _cel(c, tp, C_TONGUE, C_TONGUE_SH, 2.0, -4.0, line_w=1.0)
        _stroke(c, _curve(tpts[1:-1]), C_TONGUE_SH, 2.0, 0.75)
        _stroke(c, _curve([(x - 7.0, y) for x, y in tpts[1:-1]]), C_TONGUE_HI, 2.0, 0.5)
    # skull / upper jaw
    hp = smooth_path(head, closed=True, tension=0.5)
    _cel(c, hp, base, shade, 0.0, -10.0, rim=rim)
    c.save()
    c.clipPath(hp, doAntiAlias=True)
    # snout bridge highlight, nostrils, snarl wrinkles
    snout = smooth_path([(-26.0, -36.0), (26.0, -36.0), (34.0, 12.0), (0.0, 22.0), (-34.0, 12.0)], closed=True)
    _fill(c, snout, C_SKIN_HI if st != "lurk" else base, 0.45)
    for sgn in (-1, 1):
        n = skia.Path()
        n.moveTo(sgn * 9.0, -2.0)
        n.quadTo(sgn * 15.0, 2.0, sgn * 16.0, 10.0)
        _stroke(c, n, C_LINE, 3.6, 0.9)
        cb = skia.Path()
        cb.moveTo(sgn * 98.0, -30.0)
        cb.quadTo(sgn * 80.0, -6.0, sgn * 58.0, 4.0)
        _stroke(c, cb, C_SKIN_SH, 3.0, 0.7)
        for k in range(3):
            w = skia.Path()
            w.moveTo(sgn * (30.0 + k * 12.0), -16.0 + k * 3.0)
            w.quadTo(sgn * (38.0 + k * 12.0), -4.0, sgn * (34.0 + k * 12.0), 8.0)
            _stroke(c, w, C_SKIN_SH, 2.4, 0.7 * jaw)
    gl = _curve([(-60.0, -62.0), (-20.0, -70.0), (20.0, -70.0), (60.0, -62.0)])
    _stroke(c, gl, C_GLOSS, 4.0, 0.3, blur=1.5)
    # upper gum showing under the lip
    _stroke(c, _curve(up), C_GUM, 7.0, 0.9 if jaw > 0.04 else 0.5)
    c.restore()
    # upper teeth (pointing down)
    ut = _teeth_path(up[::-1], 16, lambda u: 14.0 + 12.0 * math.sin(math.pi * u) + 8.0 * math.exp(-((u - 0.25) ** 2) / 0.004)
                     + 8.0 * math.exp(-((u - 0.75) ** 2) / 0.004), False, 29, w=6.0, lean=0.0)
    c.drawPath(ut, paint(C_LINE, 0.75, stroke=1.6))
    _fill(c, ut, C_TOOTH)
    # eyes (lit) + brow ridges
    lids = _lids(pose, t, st, F["lid"])
    glow = F["glow"]
    for (cpt, rx, ry, idx) in FH_EYES:
        cx, cy = cpt
        sgn = -1 if cx < 0 else 1
        sock = skia.Path()
        sock.addOval(skia.Rect(cx - rx - 4, cy - ry - 4, cx + rx + 4, cy + ry + 4))
        _fill(c, sock, C_SKIN_SH)
        e = _eye_path(cx, cy, rx, ry, lids[idx], F["brow"], tilt=-14.0 * sgn)
        if e is not None:
            if sgn > 0:
                m = skia.Matrix()
                m.setScale(-1, 1, cx, cy)
                e.transform(m)
            _fill(c, e, mix_col("m_eye", "#2B2A33", 0.15 + 0.7 * (1 - glow)))
            _stroke(c, e, C_LINE, 1.2, 0.9)
        br = skia.Path()
        b = F["brow"]
        br.moveTo(cx - sgn * rx * 1.5, cy - ry - 4.0 + 7.0 * b)
        br.quadTo(cx, cy - ry - 11.0 + 1.0 * b, cx + sgn * rx * 1.5, cy - ry - 12.0 - 5.0 * b)
        _stroke(c, br, C_LINE, 9.0 if idx < 2 else 6.5, 0.6)
        _stroke(c, br, C_RIDGE, 7.0 if idx < 2 else 5.0, 1.0)
        _stroke(c, br, C_RIDGE_HI, 1.4, 0.5)
    if F["bump"] > 0.01:
        b = F["bump"]
        bp = skia.Path()
        bp.addOval(skia.Rect(20.0 - 18 * b, -80.0 - 26 * b, 20.0 + 18 * b, -80.0 + 8 * b))
        _cel(c, bp, C_BUMP, C_SKIN_SH, 2.0, -4.0)
    # drool: strands between the jaws and hanging from the chin
    dr = F["drool"]
    if dr > 0.01:
        if jaw > 0.15:
            for k, xu in enumerate((-56.0, -18.0, 26.0, 60.0)):
                if k >= 1 + int(dr * 3.99):
                    break
                a = (xu, 26.0 + 8.0 * (1 - abs(xu) / 92.0))
                yb = lo[3][1] * (1 - abs(xu) / 100.0) + lo[0][1] * abs(xu) / 100.0
                b = (xu + 4.0, yb - 8.0)
                m = ((a[0] + b[0]) * 0.5 + 3.0, (a[1] + b[1]) * 0.5 + 10.0 + 3.0 * math.sin(t * 2 + k))
                sp = skia.Path()
                sp.moveTo(*a)
                sp.quadTo(*m, *b)
                _stroke(c, sp, C_DROOL, 2.4, 0.7)
                _stroke(c, sp, WHITE, 0.8, 0.45)
        for k, (xa, per) in enumerate(((-40.0, 2.0), (30.0, 2.5), (-6.0, 1.7))):
            if k >= 1 + int(dr * 2.99):
                break
            yb = lo[3][1] + 14.0 - abs(xa) * 0.4
            L, r, fall = _strand_state(t, per, 50 + k, 50.0 + 90.0 * dr)
            _draw_strand(c, (xa, yb), (0.0, 1.0), L, r, width=2.6, sway=3.0 * math.sin(t * 3 + k))
            if fall > 0:
                _draw_drop(c, (xa, yb + fall), 3.6)
    c.restore()
    if body_a < 0.999 or st == "lurk":
        c.restore()
    if pose.rim > 0.01:
        _rim_pass(c, rim, pose)
    return F


def _front_eye_list(pose, t, ex):
    """[(center(local body frame), rx, ry, open, glow, idx)] for the front view."""
    F = _front_params(pose, t, ex)
    lids = _lids(pose, t, F["state"], F["lid"])
    hc, hs = F["head_c"], F["head_s"]
    out = []
    rot = -24.0 if F["state"] == "ko" else 0.0
    for (cpt, rx, ry, idx) in FH_EYES:
        p = _rot((cpt[0] * hs, cpt[1] * hs), rot)
        out.append(((hc[0] + p[0], hc[1] + p[1]), rx * hs, ry * hs, lids[idx], F["glow"], idx, F["brow"], rot))
    return out


# --------------------------------------------------------------------------- public API
def draw(canvas, pose: Pose, t: float):
    """Draw the crawler (body pass). The canvas carries the camera (stage units)."""
    c = canvas
    _set_light(pose)
    try:
        c.save()
        c.concat(_matrix(pose))
        ex = pose.extra or {}
        st = ex.get("state", "creep")
        view = "front" if st == "lurk" else ex.get("view", "side")
        if view == "front":
            _draw_front(c, pose, t, ex)
        else:
            R = _resolve(pose, t)
            _draw_side(c, R, pose, t)
        c.restore()
    finally:
        _clear_light()


def _eye_draw_list(pose, t):
    """Eyes as [(stage center, rx, ry, angle_deg, open, glow, near, brow, mirror)] in stage units."""
    ex = pose.extra or {}
    st = ex.get("state", "creep")
    view = "front" if st == "lurk" else ex.get("view", "side")
    M = _matrix(pose)
    out = []
    if view == "front":
        for (cpt, rx, ry, op, gl, idx, brow, rot) in _front_eye_list(pose, t, ex):
            sgn = -1 if idx in (0, 2) else 1
            out.append((cpt, rx, ry, op, gl, True, brow, sgn, rot, idx))
        return out, M, view
    R = _resolve(pose, t)
    for (cpt, rx, ry, near, op) in _eye_side_geo(R, pose, t):
        out.append((cpt, rx, ry, op, R["glow"] * (1.0 if near else 0.7), near, R["brow"], -1, 0.0, -1))
    return out, (M, _head_xf(R), R), view


def eye_points(pose: Pose, t: float = 0.0):
    lst, M, view = _eye_draw_list(pose, t)
    res = []
    for item in lst:
        cpt, rx, ry, op, gl = item[:5]
        if view == "front":
            p = _map(M, cpt)
        else:
            Mb, hx, _ = M
            p = _map(Mb, _map(hx, cpt))
        res.append((p[0], p[1], rx * pose.scale, op, gl))
    return res


def draw_eyes(canvas, pose: Pose, t: float):
    """Emissive pass: bright eye cores + soft additive halos (draw after the darkness overlay)."""
    lst, M, view = _eye_draw_list(pose, t)
    c = canvas
    c.save()
    if view == "front":
        c.concat(M)
        ex = pose.extra or {}
        lx, ly = clamp(pose.look_x, -1, 1), clamp(pose.look_y, -1, 1)
        if lx == 0.0 and ly == 0.0 and ex.get("state") == "lurk":
            # restless darting when the scene gives no gaze
            lx = 0.8 * noise1(t * 0.9, 61) + 0.4 * (1.0 if noise1(t * 0.35, 62) > 0.35 else 0.0)
            ly = 0.4 * noise1(t * 0.7, 63)
        for (cpt, rx, ry, op, gl, near, brow, sgn, rot, idx) in lst:
            _emit_eye(c, cpt, rx, ry, op, gl, brow, tilt=-14.0 * sgn + rot, mirror=sgn > 0, look=(lx, ly))
    else:
        Mb, hx, R = M
        c.concat(Mb)
        c.concat(hx)
        skull = _skull()
        for (cpt, rx, ry, op, gl, near, brow, sgn, rot, idx) in lst:
            if not near:
                c.save()
                c.clipPath(skull, skia.ClipOp.kDifference, True)
                _emit_eye(c, cpt, rx * 0.82, ry * 0.8, op, gl, brow, halo=0.6)
                c.restore()
            else:
                _emit_eye(c, cpt, rx, ry, op, gl, brow, roll=R["roll"])
    c.restore()


def _emit_eye(c, cpt, rx, ry, op, gl, brow, tilt=-14.0, mirror=False, look=(0.0, 0.0), halo=1.0, roll=0.0):
    if gl <= 0.003:
        return
    cx, cy = cpt
    # halo (additive)
    hr = rx * 4.2
    gcol = col("m_eye_glow")
    sh = skia.GradientShader.MakeRadial((cx, cy), hr, [skia.ColorSetA(gcol, int(120 * gl * halo * (0.35 + 0.65 * op))),
                                                       skia.ColorSetA(gcol, int(40 * gl * halo * op)),
                                                       skia.ColorSetA(gcol, 0)], [0.0, 0.35, 1.0])
    p = skia.Paint(AntiAlias=True)
    p.setShader(sh)
    p.setBlendMode(skia.BlendMode.kPlus)
    c.drawCircle(cx, cy, hr, p)
    e = _eye_path(cx, cy, rx, ry, op, brow, tilt=tilt)
    if e is None:
        return
    if mirror:
        m = skia.Matrix()
        m.setScale(-1, 1, cx, cy)
        e.transform(m)
    c.save()
    c.clipPath(e, doAntiAlias=True)
    fx = cx + look[0] * rx * 0.35
    fy = cy + look[1] * ry * 0.3 - ry * 0.1
    core = skia.GradientShader.MakeRadial((fx, fy), max(rx, ry) * 1.1,
                                          [col(C_EYE_CORE, gl), col(C_EYE, gl), col(C_EYE_GLOW, gl * 0.95)],
                                          [0.0, 0.45, 1.0])
    pc = skia.Paint(AntiAlias=True)
    pc.setShader(core)
    c.drawRect(skia.Rect(cx - rx * 2, cy - ry * 2, cx + rx * 2, cy + ry * 2), pc)
    if roll > 0:
        c.drawRect(skia.Rect(cx - rx * 2, cy - ry * 2, cx + rx * 2, cy + ry * (1.0 - 1.2 * roll)),
                   _core_paint(C_EYE_DEAD, 0.85 * roll))
    # thin slit pupil (reads as a predator)
    if gl > 0.3 and roll < 0.5:
        sl = skia.Path()
        sl.moveTo(fx, fy - ry * 0.9)
        sl.quadTo(fx + rx * 0.16, fy, fx, fy + ry * 0.9)
        sl.quadTo(fx - rx * 0.16, fy, fx, fy - ry * 0.9)
        c.drawPath(sl, _core_paint("#2A3300", 0.75))
    c.restore()


def head_pos(pose: Pose, t: float = 0.0):
    ex = pose.extra or {}
    st = ex.get("state", "creep")
    view = "front" if st == "lurk" else ex.get("view", "side")
    if view == "front":
        F = _front_params(pose, t, ex)
        hc, hs = F["head_c"], F["head_s"]
        return _to_stage(pose, (hc[0], hc[1] - 34.0 * hs))
    R = _resolve(pose, t)
    return _to_stage(pose, _map(_head_xf(R), (74.0, -33.0)))


def mouth_pos(pose: Pose, t: float = 0.0):
    ex = pose.extra or {}
    st = ex.get("state", "creep")
    view = "front" if st == "lurk" else ex.get("view", "side")
    if view == "front":
        F = _front_params(pose, t, ex)
        hc, hs = F["head_c"], F["head_s"]
        up, lo, _, _ = _front_head_shapes(F)
        return _to_stage(pose, (hc[0], hc[1] + hs * (up[3][1] + lo[3][1]) * 0.5))
    R = _resolve(pose, t)
    hx = _head_xf(R)
    a = (146.0, 10.0)
    b = _map(_jaw_xf(R), (144.0, 14.0))
    return _to_stage(pose, _map(hx, ((a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5)))


def tail_tip(pose: Pose, t: float = 0.0):
    ex = pose.extra or {}
    st = ex.get("state", "creep")
    view = "front" if st == "lurk" else ex.get("view", "side")
    if view == "front":
        return _to_stage(pose, (260.0, -40.0))
    R = _resolve(pose, t)
    return _to_stage(pose, R["tail"][-1])


def drool_drops(pose: Pose, t: float):
    """Stage points of drool drops currently falling (side view, approximate)."""
    ex = pose.extra or {}
    if ex.get("state") == "lurk" or ex.get("view", "side") == "front":
        return []
    R = _resolve(pose, t)
    if R["drool"] <= 0.01:
        return []
    hx = _head_xf(R)
    jx = _jaw_xf(R)
    M = _matrix(pose)
    out = []
    anchors = [(_map(jx, (146.0, 32.0)), 2.1, 1), (_map(jx, (100.0, 41.0)), 2.6, 2), ((160.0, 9.0), 1.9, 3)]
    for idx, (a, per, seed) in enumerate(anchors):
        if idx >= 1 + int(R["drool"] * 3.5):
            break
        L, r, fall = _strand_state(t, per, seed, 40.0 + 70.0 * R["drool"])
        if fall > 0:
            out.append(_map(M, _map(hx, (a[0], a[1] + fall))))
    return out


# --------------------------------------------------------------------------- THE GLOVE (the hermit)
C_GLOVE = col("glove")
C_GLOVE_HI = col("glove_hi")
C_GLOVE_SH = mix_col("glove", "#1A0F08", 0.45)
C_GLOVE_DK = mix_col("glove", "#1A0F08", 0.7)
C_GLOVE_LINE = col("#22140B")
C_STITCH = col("#B89A70")
C_SLEEVE = col("#3B342D")
C_SLEEVE_SH = col("#231E1A")
C_SLEEVE_HI = col("#564B40")

# finger chain specs: base (hand-local), segment lengths, width, open angles, closed angles, depth tint
_FINGERS = [
    # pinky, ring, middle, index (back -> front)
    ((8.0, 20.0), (23.0, 17.0, 14.0), 15.0, (30.0, 12.0, 8.0), (100.0, 100.0, 70.0), 0.45),
    ((12.0, 8.0), (29.0, 21.0, 16.0), 17.0, (16.0, 10.0, 8.0), (96.0, 98.0, 72.0), 0.3),
    ((14.0, -4.0), (31.0, 22.0, 17.0), 18.0, (2.0, 9.0, 7.0), (92.0, 98.0, 72.0), 0.15),
    ((12.0, -16.0), (29.0, 21.0, 16.0), 17.0, (-14.0, 8.0, 6.0), (88.0, 96.0, 74.0), 0.0),
]


def _finger_chain(base, segs, angs):
    pts = [base]
    a = 0.0
    p = base
    for L, d in zip(segs, angs):
        a += d
        p = (p[0] + L * math.cos(a * D2R), p[1] + L * math.sin(a * D2R))
        pts.append(p)
    return pts


def glove_grip_point(x, y, scale=1.0, angle=0.0):
    """The grip axis passes through (x, y) (the draw_glove anchor)."""
    return (x, y)


def draw_glove(canvas, x, y, scale=1.0, grip=0.0, angle=0.0, alpha=1.0, layer="all", sleeve_len=520.0):
    """The hermit's weathered leather work glove with a ragged sleeve emerging from darkness.

    (x, y) is the grip point (palm centre when open; the axis of whatever the fist holds when closed).
    angle: direction the arm reaches, degrees (0 = reaching to screen-right, the forearm coming from the left;
    90 = reaching down). grip 0 = open, reaching; 1 = fist closed around a tail (the held object passes through
    (x, y) roughly perpendicular to the forearm). The sleeve fades out over its last ~45% (into the dark).
    layer: "all" | "back" (sleeve, cuff, palm - draw before the held tail) | "front" (fingers + thumb - after)."""
    c = canvas
    g = clamp(grip)
    c.save()
    c.translate(x, y)
    c.rotate(angle)
    c.scale(scale, scale)
    if alpha < 0.999:
        c.saveLayerAlpha(None, int(255 * clamp(alpha)))
    back = layer in ("all", "back")
    front = layer in ("all", "front")
    # hand frame: wrist at (-58, 0); knuckle line x ~ +6; grip axis at the origin.
    hand_dx = lerp(-12.0, -4.0, g)        # the hand shifts as the fist closes so (0,0) is inside the fist
    hand_dy = lerp(0.0, -16.0, g)
    if back:
        _glove_sleeve(c, sleeve_len)
        _glove_cuff_palm(c, g, hand_dx, hand_dy)
    if front:
        _glove_fingers(c, g, hand_dx, hand_dy)
    if alpha < 0.999:
        c.restore()
    c.restore()


def _glove_sleeve(c, L):
    # ragged sleeve: from far back (fading) to the torn hem just behind the cuff
    hem_x = -118.0
    top = [(-L, -64.0), (-L * 0.7, -66.0), (-L * 0.45, -62.0), (-260.0, -58.0), (-180.0, -56.0), (hem_x, -58.0)]
    rag = []
    n = 9
    for i in range(n + 1):
        u = i / n
        yy = lerp(-58.0, 54.0, u)
        dx = (14.0 + 10.0 * hash01(i, 71)) if i % 2 else (-2.0 + 4.0 * hash01(i, 73))
        rag.append((hem_x + dx, yy))
    bot = [(hem_x - 4.0, 56.0), (-180.0, 60.0), (-260.0, 62.0), (-L * 0.45, 64.0), (-L * 0.7, 66.0), (-L, 62.0)]
    pts = top + rag + bot
    path = skia.Path()
    path.moveTo(*pts[0])
    for p in top[1:]:
        path.lineTo(*p)
    for p in rag:
        path.lineTo(*p)
    for p in bot:
        path.lineTo(*p)
    path.close()
    # soften: smooth path of the same points but keep the zigzag hem sharp-ish
    sm = skia.Path()
    _cr(sm, top, tension=0.5)
    for p in rag:
        sm.lineTo(*p)
    _cr(sm, bot, move=False, tension=0.5)
    sm.close()
    c.saveLayer(skia.Rect(-L - 10, -90, 0, 90), None)
    c.drawPath(sm, _core_paint(C_GLOVE_LINE, 0.9, stroke=2.4))
    c.drawPath(sm, _core_paint(C_SLEEVE_SH))
    c.save()
    c.clipPath(sm, doAntiAlias=True)
    c.translate(0.0, -12.0)
    c.drawPath(sm, _core_paint(C_SLEEVE))
    c.restore()
    c.save()
    c.clipPath(sm, doAntiAlias=True)
    # folds
    for k, (x0, w) in enumerate(((-400.0, 30.0), (-300.0, 40.0), (-215.0, 26.0), (-160.0, 34.0))):
        f = skia.Path()
        f.moveTo(x0, -60.0)
        f.quadTo(x0 + w * 0.6, -10.0, x0 + w * 0.2, 60.0)
        c.drawPath(f, _core_paint(C_SLEEVE_SH, 0.8, stroke=4.0))
        f2 = skia.Path()
        f2.moveTo(x0 + 8, -58.0)
        f2.quadTo(x0 + w * 0.6 + 8, -16.0, x0 + w * 0.3 + 6, 20.0)
        c.drawPath(f2, _core_paint(C_SLEEVE_HI, 0.6, stroke=2.0))
    # a darned patch
    pt = skia.Path()
    pt.addRect(skia.Rect(-250.0, -30.0, -205.0, 6.0))
    m = skia.Matrix()
    m.setRotate(-8.0, -228.0, -12.0)
    pt.transform(m)
    c.drawPath(pt, _core_paint("#4A3B2C"))
    c.drawPath(pt, _core_paint("#1E1712", 0.8, stroke=1.4))
    c.restore()
    # threads hanging from the hem
    for k, (yy, ln) in enumerate(((-30.0, 26.0), (14.0, 34.0), (40.0, 20.0))):
        th = skia.Path()
        th.moveTo(hem_x + 6.0, yy)
        th.quadTo(hem_x + 14.0, yy + ln * 0.5, hem_x + 10.0 + 4.0 * k, yy + ln)
        c.drawPath(th, _core_paint(C_SLEEVE_HI, 0.9, stroke=1.6))
    # fade into darkness (alpha mask along the sleeve)
    fade = skia.Paint()
    fade.setShader(skia.GradientShader.MakeLinear([(-L, 0), (-L * 0.55, 0)],
                                                  [skia.ColorSetA(skia.ColorBLACK, 0), skia.ColorBLACK]))
    fade.setBlendMode(skia.BlendMode.kDstIn)
    c.drawRect(skia.Rect(-L - 10, -90, 0, 90), fade)
    c.restore()


def _glove_cuff_palm(c, g, hdx, hdy):
    # cuff (flared gauntlet) - behind the sleeve hem? The hem overlaps it: draw the cuff then re-draw nothing.
    cuff = smooth_path([(-132.0, -50.0), (-60.0 + hdx * 0.5, -38.0 + hdy * 0.5), (-56.0 + hdx * 0.5, 36.0 + hdy * 0.3),
                        (-132.0, 50.0), (-142.0, 0.0)], closed=True, tension=0.45)
    # palm / back of hand
    hx, hy = hdx, hdy
    palm_pts = [(-64.0 + hx * 0.5, -32.0 + hy * 0.5), (-20.0 + hx, -34.0 + hy), (14.0 + hx, -26.0 + hy),
                (22.0 + hx, -6.0 + hy), (19.0 + hx, 20.0 + hy), (-4.0 + hx, 30.0 + hy * 0.6),
                (-40.0 + hx * 0.5, 34.0 + hy * 0.4), (-62.0 + hx * 0.5, 30.0 + hy * 0.4)]
    palm = smooth_path(palm_pts, closed=True, tension=0.5)
    _cel(c, palm, C_GLOVE, C_GLOVE_SH, -2.0, -7.0, line=C_GLOVE_LINE, line_w=1.3)
    c.save()
    c.clipPath(palm, doAntiAlias=True)
    # worn scuffs + seam stitches on the back of the hand
    for k, (sx, sy, r) in enumerate(((-30.0, -18.0, 9.0), (2.0, -22.0, 6.0), (-12.0, 10.0, 7.0))):
        c.drawOval(skia.Rect(sx + hx - r * 1.4, sy + hy - r * 0.7, sx + hx + r * 1.4, sy + hy + r * 0.7),
                   _core_paint(C_GLOVE_HI, 0.45, blur=2.5))
    st = skia.Path()
    st.moveTo(-58.0 + hx * 0.5, -22.0 + hy)
    st.quadTo(-20.0 + hx, -30.0 + hy, 14.0 + hx, -22.0 + hy)
    sp = _core_paint(C_STITCH, 0.8, stroke=1.4)
    sp.setPathEffect(skia.DashPathEffect.Make([4.0, 3.5], 0.0))
    c.drawPath(st, sp)
    c.restore()
    # cuff over the wrist end of the palm
    _cel(c, cuff, C_GLOVE_SH, C_GLOVE_DK, -2.0, -6.0, line=C_GLOVE_LINE, line_w=1.3)
    c.save()
    c.clipPath(cuff, doAntiAlias=True)
    cs = skia.Path()
    cs.moveTo(-66.0 + hdx * 0.5, -36.0)
    cs.lineTo(-62.0 + hdx * 0.5, 34.0)
    sp2 = _core_paint(C_STITCH, 0.7, stroke=1.3)
    sp2.setPathEffect(skia.DashPathEffect.Make([4.0, 3.5], 0.0))
    c.drawPath(cs, sp2)
    c.drawOval(skia.Rect(-120.0, -30.0, -90.0, -12.0), _core_paint(C_GLOVE_HI, 0.35, blur=3.0))
    c.restore()
    # torn sleeve hem lies over the cuff end: a few ragged flaps
    flap = skia.Path()
    flap.moveTo(-136.0, -58.0)
    for i in range(7):
        u = (i + 1) / 7
        yy = lerp(-58.0, 56.0, u)
        flap.lineTo(-110.0 + (12.0 if i % 2 == 0 else -2.0) + 6 * hash01(i, 91), yy - 8.0)
        flap.lineTo(-118.0, yy)
    flap.lineTo(-140.0, 56.0)
    flap.close()
    c.drawPath(flap, _core_paint(C_GLOVE_LINE, 0.85, stroke=2.0))
    c.drawPath(flap, _core_paint(C_SLEEVE))


def _glove_fingers(c, g, hdx, hdy):
    knuckle = (hdx, hdy)
    for i, (base, segs, w, a_open, a_closed, dk) in enumerate(_FINGERS):
        angs = [lerp(a, b, ease_in_out(g)) for a, b in zip(a_open, a_closed)]
        # reaching open hand spreads a little (fan)
        fan = (i - 1.5) * 7.0 * (1.0 - g)
        angs[0] += fan
        b = (base[0] + knuckle[0], base[1] + knuckle[1])
        pts = _finger_chain(b, segs, angs)
        widths = [w, w * 0.95, w * 0.88, w * 0.8]
        base_c = mix_col("glove", "#1A0F08", 0.15 + dk * 0.6)
        shade_c = mix_col("glove", "#1A0F08", 0.5 + dk * 0.3)
        path = skia.Path()
        for k in range(3):
            pth = _capsule(pts[k], pts[k + 1], widths[k] * 0.5, widths[k + 1] * 0.5)
            path.addPath(pth)
        path.setFillType(skia.PathFillType.kWinding)
        _cel(c, path, base_c, shade_c, -1.5, -4.0, line=C_GLOVE_LINE, line_w=1.2)
        # joint creases (worn leather)
        for k in (1, 2):
            p = pts[k]
            dx, dy = _norm(pts[k + 1][0] - pts[k - 1][0], pts[k + 1][1] - pts[k - 1][1])
            nx, ny = -dy, dx
            cr = skia.Path()
            ww = widths[k] * 0.42
            cr.moveTo(p[0] - nx * ww, p[1] - ny * ww)
            cr.quadTo(p[0] + dx * 3.0, p[1] + dy * 3.0, p[0] + nx * ww * 0.3, p[1] + ny * ww * 0.3)
            c.drawPath(cr, _core_paint(C_GLOVE_DK, 0.8, stroke=1.4))
        # worn shine on the knuckle
        c.drawCircle(pts[1][0] - 1.0, pts[1][1] - widths[1] * 0.25, widths[1] * 0.18, _core_paint(C_GLOVE_HI, 0.55,
                                                                                                    blur=1.5))
    # thumb: from the side of the palm, wrapping over the fingers when closed
    tb = (-30.0 + hdx, -24.0 + hdy)
    t_open = (-30.0, 14.0, 10.0)
    t_closed = (8.0, 60.0, 40.0)
    angs = [lerp(a, b, ease_in_out(g)) for a, b in zip(t_open, t_closed)]
    pts = _finger_chain(tb, (30.0, 24.0, 18.0), angs)
    path = skia.Path()
    ws = (24.0, 20.0, 17.0, 15.0)
    for k in range(3):
        path.addPath(_capsule(pts[k], pts[k + 1], ws[k] * 0.5, ws[k + 1] * 0.5))
    _cel(c, path, C_GLOVE, C_GLOVE_SH, -1.5, -4.5, line=C_GLOVE_LINE, line_w=1.2)
    c.drawCircle(pts[2][0], pts[2][1] - 3.0, 3.0, _core_paint(C_GLOVE_HI, 0.5, blur=1.5))
    # a split seam at the thumb tip (weathered)
    sp = skia.Path()
    sp.moveTo(pts[3][0] - 3.0, pts[3][1] - 4.0)
    sp.lineTo(pts[3][0] + 2.0, pts[3][1] + 1.0)
    c.drawPath(sp, _core_paint(C_GLOVE_DK, 0.9, stroke=1.4))
