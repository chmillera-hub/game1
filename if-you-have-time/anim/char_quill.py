"""QUILL - the ship's android. Full character rig (BIBLE section 2, contract in anim/rig.py).

Public API
    draw(canvas, pose, t, warm=None)   draw Quill; canvas already in stage coords (camera applied).
                                       warm 0..1 = iris glow teal -> amber (None = auto from smile*glow)
    head_center(pose) -> (x, y)        stage coords between the eyes (exact for every pose field)
    hand_pos(pose, side) -> (x, y)     stage coords of the palm centre ("l" / "r" = Quill's own side);
                                       for "palm_up" it is the top of the palm (props hover above it)
    ARMS                               rest, behind_back, raise_conduct, present, gesture_small, send
    HEIGHT                             770 stage units at scale 1
    EXPRESSIONS, expression(name, **overrides) -> dict of Pose kwargs (face presets)

Construction notes
    * The head is a small 3D model: horizontal elliptical slices (half-width a, front depth bf,
      back depth bb) rotated by a yaw angle and a small pitch (head_nod), then projected
      orthographically. Silhouette, hairline, ears, eyes, brows, nose and mouth are projected
      points, so turn / head_turn / back / head_nod stay coherent from front through profile to back.
      pose.back blends the yaw continuously (0.25..0.75): 0 front, 0.5 profile, >= 0.75 full back.
    * The torso uses the same slice idea; arms and legs are 2D chains with a forward-plane cheat
      so gestures read in the picture plane at three-quarter view (facing=-1 is a mirror image,
      so arm_r is always the near arm once Quill is turned).
    * Cel shading: one shade crescent (shape minus shifted shape, via PathOps) + a thin lit edge.
      Key light comes from the side Quill faces and from above.
    * pose.light / tint / tint_amt are applied per colour (same maths as core.light_filter, no
      offscreen layer); pose.rim adds a coloured edge on every shape + a soft blurred halo.
    * Irises, process rings and bloom are emissive: drawn unlit after the body so they glow in the
      dark, clipped by any arm that passes in front of the face.
"""
from __future__ import annotations

import math

import skia

from anim.core import auto_blink, clamp, col, glow, lerp, noise1, paint, rgb, smooth_path, smoothstep
from anim.rig import ArmPose, Pose

HEIGHT = 770.0
TURN_DEG = 75.0           # yaw degrees per unit of pose.turn / head_turn

# --------------------------------------------------------------------------- palette
SKIN, SKIN_SH, SKIN_HI = "#D7DCE3", "#AEB8C6", "#F3F6FA"
SKIN_SH2 = "#97A3B5"
SEAM = "#93A0B3"
HAIR, HAIR_HI, HAIR_SH = "#1D2740", "#3B4C73", "#131A2C"
IRIS, IRIS_GLOW, IRIS_DARK, LIMBAL, PUPIL = "#5FE3D0", "#B9FFF5", "#1C9C90", "#0B4A50", "#06232A"
AMBER, AMBER_SOFT = "#F4A259", "#FFD29A"
SCLERA, SCLERA_SH = "#EEF2F6", "#B4BFCE"
LASH = "#2A3247"
BROW = "#1D2740"
UNI, UNI_SH, UNI_HI, UNI_LINE = "#262B38", "#1A1E28", "#3A4357", "#141821"
COLLAR, COLLAR_SH, COLLAR_IN, COLLAR_HI = "#2EC4B6", "#1F8D84", "#145F5A", "#8CF0E6"
INSIG = "#DDE6F0"
PANTS, PANTS_SH = "#1E2331", "#151925"
BOOT, BOOT_HI = "#101219", "#343A4C"
MOUTH_IN, TEETH, TONGUE = "#2B2734", "#E6EBF1", "#8D7887"
LIPLINE = "#76808F"

# --------------------------------------------------------------------------- arm presets
ARMS = {
    "rest": ArmPose(shoulder=5.0, elbow=9.0, wrist=4.0, hand="relaxed"),
    "behind_back": ArmPose(shoulder=4.0, elbow=60.0, wrist=0.0, hand="relaxed", behind=1.0),
    "raise_conduct": ArmPose(shoulder=56.0, elbow=70.0, wrist=-24.0, hand="open"),
    "present": ArmPose(shoulder=22.0, elbow=72.0, wrist=-6.0, hand="palm_up"),
    "gesture_small": ArmPose(shoulder=14.0, elbow=72.0, wrist=-14.0, hand="open"),
    "send": ArmPose(shoulder=112.0, elbow=14.0, wrist=-14.0, hand="open"),
}

# --------------------------------------------------------------------------- face presets
EXPRESSIONS = {
    "neutral": {},
    "attentive": {"head_tilt": 6.0, "brow_raise": 0.25, "look_x": 0.0},
    "processing": {"process": 1.0, "glow": 0.8, "look_y": -0.15, "brow_raise": 0.1},
    "done": {"glow": 1.0, "brow_raise": 0.2},
    "deadpan": {"brow_raise": 0.05, "smile": 0.0, "lid_l": 0.86, "lid_r": 0.86},
    "concern": {"brow_worry": 0.3, "look_y": 0.6, "head_nod": -0.25, "smile": -0.12},
    # look_x is screen space: -0.55 looks toward Rae when Quill faces -1 (flip the sign for facing +1)
    "curious": {"head_tilt": 11.0, "brow_raise": 0.45, "look_x": -0.55, "head_turn": -0.05},
    "smile": {"smile": 0.3, "glow": 0.5, "squint": 0.12, "head_tilt": 4.0},
    "oo": {"mouth_open": 0.45, "mouth_round": 1.0},
    "ah": {"mouth_open": 0.85, "mouth_round": 0.1},
    "blink": {"lid_l": 0.0, "lid_r": 0.0},
    "wide": {"eye_wide": 0.5, "brow_raise": 0.8},
}


def expression(name: str, **overrides) -> dict:
    """Pose kwargs for a named face preset (merged with overrides): Pose(**expression('curious'))."""
    d = dict(EXPRESSIONS[name])
    d.update(overrides)
    return d


# --------------------------------------------------------------------------- small helpers
_rad = math.radians


def _spl(path, pts, move=True, closed=False):
    """Append a Catmull-Rom spline through pts to path."""
    n = len(pts)
    if n == 0:
        return path
    if move:
        path.moveTo(*pts[0])
    else:
        path.lineTo(*pts[0])
    if n == 1:
        return path
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = pts[(i - 1) % n] if closed else pts[max(i - 1, 0)]
        p1 = pts[i]
        p2 = pts[(i + 1) % n] if closed else pts[i + 1]
        p3 = pts[(i + 2) % n] if closed else pts[min(i + 2, n - 1)]
        path.cubicTo(p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6,
                     p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6, p2[0], p2[1])
    if closed:
        path.close()
    return path


def _two_curve_path(top, bot):
    """Closed shape: spline along `top` (a->b) then spline along `bot` (b->a). Sharp joins."""
    p = skia.Path()
    _spl(p, top)
    _spl(p, bot, move=False)
    p.close()
    return p


def _tapered(pts, widths):
    """Filled ribbon along pts with half-widths per point (0 at an end = pointed)."""
    n = len(pts)
    L, R = [], []
    for i in range(n):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, n - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / d, dx / d
        w = widths[i]
        L.append((pts[i][0] + nx * w, pts[i][1] + ny * w))
        R.append((pts[i][0] - nx * w, pts[i][1] - ny * w))
    p = skia.Path()
    _spl(p, L)
    _spl(p, R[::-1], move=False)
    p.close()
    return p


def _union(paths):
    out = paths[0]
    for q in paths[1:]:
        r = skia.Op(out, q, skia.PathOp.kUnion_PathOp)
        if r is not None:
            out = r
    return out


def _capsule(a, b, ra, rb):
    """Tapered capsule between circles (a, ra) and (b, rb): one analytic contour (no PathOps)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = math.hypot(dx, dy)
    p = skia.Path()
    if d < 1e-3 or abs(ra - rb) >= d:
        p.addCircle(a[0], a[1], max(ra, rb)) if ra >= rb else p.addCircle(b[0], b[1], rb)
        return p
    ux, uy = dx / d, dy / d
    nx, ny = -uy, ux
    sb = (ra - rb) / d
    cb = math.sqrt(max(0.0, 1.0 - sb * sb))
    beta = math.degrees(math.asin(sb))
    NL = (ux * sb + nx * cb, uy * sb + ny * cb)
    NR = (ux * sb - nx * cb, uy * sb - ny * cb)
    au = math.degrees(math.atan2(uy, ux))
    p.moveTo(a[0] + ra * NL[0], a[1] + ra * NL[1])
    p.lineTo(b[0] + rb * NL[0], b[1] + rb * NL[1])
    p.arcTo(skia.Rect(b[0] - rb, b[1] - rb, b[0] + rb, b[1] + rb), au + 90.0 - beta, -(180.0 - 2.0 * beta), False)
    p.lineTo(a[0] + ra * NR[0], a[1] + ra * NR[1])
    p.arcTo(skia.Rect(a[0] - ra, a[1] - ra, a[0] + ra, a[1] + ra), au - (90.0 - beta), -(180.0 + 2.0 * beta), False)
    p.close()
    return p


# Per-draw lighting state (set by draw(); the module draws single-threaded).
#   _LT  = (light, tint_amt, (tr, tg, tb))  colour transform identical to core.light_filter
#   _RIM = (rgb, alpha, d)                  rim-light edge applied to every shaded shape
_LT = (1.0, 0.0, (0.0, 0.0, 0.0))
_RIM = None


def _lc(color):
    """Colour (palette key / hex / rgb tuple) -> lit rgb tuple for the current pose lighting."""
    r, gg, b = (rgb(color) if isinstance(color, str) else color)[:3]
    l, ta, (tr, tg, tb) = _LT
    if l == 1.0 and ta == 0.0:
        return (r, gg, b)
    k = l * (1 - ta)
    return (clamp(r * k + tr * ta, 0, 255), clamp(gg * k + tg * ta, 0, 255), clamp(b * k + tb * ta, 0, 255))


def _pt(color, alpha=1.0, **kw):
    """paint() with the current pose lighting applied to the colour."""
    return paint(_lc(color), alpha, **kw)


def _rim_edge(c, path):
    """Thin bright rim-light edge on the top and both sides of `path` (unlit colour)."""
    if _RIM is None:
        return
    rc, ra, d = _RIM
    # key edge on the side Quill faces (+x) and the top, a fainter one on the other side (big shapes)
    bnd = path.computeTightBounds()
    big = bnd.width() * bnd.height() > 2500.0
    for v, k in (((-d, d * 0.85), 1.0), ((d * 0.75, d * 0.6), 0.45)):
        if k < 1.0 and not big:
            continue
        r = _minus_shifted(path, v)
        if r is not None:
            c.drawPath(r, paint(rc, ra * k))


def _minus_shifted(path, off):
    """path minus (path shifted by off): the crescent on the side opposite `off`."""
    sh = skia.Path(path)
    sh.offset(off[0], off[1])
    return skia.Op(path, sh, skia.PathOp.kDifference_PathOp)


def _cel(c, path, base, shade, off, hi=None, hi_off=None, hi_alpha=1.0, shade_alpha=1.0):
    """Fill path with base colour, shade crescent on the side opposite `off`, optional rim
    highlight crescent on the side opposite `hi_off`. (PathOps: much cheaper than AA clips.)"""
    c.drawPath(path, _pt(base))
    r = _minus_shifted(path, off)
    if r is not None:
        c.drawPath(r, _pt(shade, shade_alpha))
    if hi is not None and hi_off is not None:
        r = _minus_shifted(path, hi_off)
        if r is not None:
            c.drawPath(r, _pt(hi, hi_alpha))
    _rim_edge(c, path)


def _lit_rgb(color, g=None):
    """Apply the pose light/tint transform (same maths as core.light_filter) to a colour."""
    return _lc(color)


def _mixc(a, b, t):
    ra = rgb(a) if isinstance(a, str) else a
    rb = rgb(b) if isinstance(b, str) else b
    t = clamp(t)
    return tuple(ra[i] + (rb[i] - ra[i]) * t for i in range(3))


# --------------------------------------------------------------------------- head model
# (y, a, bf, bb) head coords: origin between the eyes, +y down. a = half width,
# bf / bb = depth toward the face / toward the back of the skull.
_HEAD = [
    (-69.0, 22.0, 19.0, 30.0),
    (-62.0, 34.5, 32.0, 44.0),
    (-51.0, 42.5, 41.5, 53.0),
    (-37.0, 45.5, 46.0, 57.0),
    (-19.0, 46.0, 48.5, 58.0),
    (-3.0, 45.5, 50.0, 55.0),
    (11.0, 44.0, 51.0, 48.0),
    (24.0, 42.0, 51.5, 36.0),
    (34.0, 39.5, 51.0, 22.0),
    (44.0, 34.0, 50.0, 10.0),
    (52.0, 27.0, 48.5, 3.0),
    (58.5, 18.5, 46.5, 0.6),
]
_HEAD_TOP_Y = -75.0
_CHIN_Y = 63.5
_EYE_X = 19.5


def _slice(y):
    hs = _HEAD
    if y <= hs[0][0]:
        return hs[0][1:]
    if y >= hs[-1][0]:
        return hs[-1][1:]
    for i in range(1, len(hs)):
        if y < hs[i][0]:
            y0, a0, f0, b0 = hs[i - 1]
            y1, a1, f1, b1 = hs[i]
            k = (y - y0) / (y1 - y0)
            return a0 + (a1 - a0) * k, f0 + (f1 - f0) * k, b0 + (b1 - b0) * k
    return hs[-1][1:]


def _face_z(x, y):
    a, bf, _ = _slice(y)
    u = clamp(x / a, -1.0, 1.0)
    return bf * math.sqrt(max(0.0, 1.0 - u * u))


def _surf(beta_deg, y, lift=0.0):
    """Point on the skull at azimuth beta (0 = front, +90 = local +x side) and height y."""
    a, bf, bb = _slice(y)
    b = math.radians(beta_deg)
    sb, cb = math.sin(b), math.cos(b)
    depth = bf if cb >= 0 else bb
    return (a + lift) * sb, y, (depth + lift) * cb, (sb / a, cb / depth)


class _Proj:
    """Yaw (psi, degrees; + turns the face toward local +x) then pitch (nod) projection."""

    def __init__(self, psi_deg, nod):
        self.psi = psi_deg
        self.c = math.cos(_rad(psi_deg))
        self.s = math.sin(_rad(psi_deg))
        th = _rad(nod * 10.0)
        self.ct, self.st = math.cos(th), math.sin(th)

    def p(self, x, y, z):
        x1 = x * self.c + z * self.s
        z1 = -x * self.s + z * self.c
        return (x1, y * self.ct - z1 * self.st)

    def depth(self, x, y, z):
        z1 = -x * self.s + z * self.c
        return y * self.st + z1 * self.ct

    def nz(self, nx, nz_):
        """View-facing component of a horizontal surface normal (nx, nz)."""
        d = math.hypot(nx, nz_) or 1.0
        return (-nx * self.s + nz_ * self.c) / d


def _jaw_y(y, jaw):
    if y <= 22.0:
        return y
    return y + jaw * (y - 22.0) / 42.0


def _head_outline(P, jaw):
    right, left = [], []
    s, c = P.s, P.c
    # far-side facial contour detail (brow, eye socket, cheekbone, cheek hollow) as the head turns
    amt = smoothstep((abs(s) - 0.18) / 0.5) * smoothstep((c + 0.6) / 0.35)
    for (y, a, bf, bb) in _HEAD:
        yy = _jaw_y(y, jaw)
        for sigma, lst in ((1.0, right), (-1.0, left)):
            b = bf if sigma * s >= 0 else bb
            R = math.sqrt((a * c) ** 2 + (b * s) ** 2) or 1e-6
            x = a * (sigma * a * c / R)
            z = b * (sigma * b * s / R)
            px, py = P.p(x, yy, z)
            if amt > 0 and sigma * s > 0:
                bump = (2.2 * math.exp(-((y + 19.0) / 6.0) ** 2) - 2.4 * math.exp(-((y + 3.0) / 6.0) ** 2)
                        + 1.6 * math.exp(-((y - 11.0) / 6.0) ** 2) - 1.8 * math.exp(-((y - 24.0) / 7.0) ** 2))
                px += sigma * bump * amt
            lst.append((px, py))
    top = P.p(0.0, _HEAD_TOP_Y, -4.0)
    chin_z = 0.5 * _HEAD[-1][2] * (1.0 + max(0.0, c))   # front view: chin sits forward; turned: centred
    chin = P.p(0.0, _CHIN_Y + jaw, chin_z * 0.95)
    pts = [top] + right + [chin] + left[::-1]
    sil = smooth_path(pts, closed=True)
    if abs(s) > 0.55:
        # profile-ish: let the nose, brow and lips break the silhouette
        def fp(x, y, dz):
            return P.p(x, y, _face_z(x, y) + dz)
        prof = [fp(0, -16, 1.0), fp(0, -9, 1.0), fp(0, -3, 2.0), fp(0, 10, 6.0), fp(0, 21, 10.0), fp(0, 25.5, 8.5),
                fp(0, 28.5, 4.5), fp(0, 31, 1.5), fp(0, 36, 3.0), fp(0, 39.5, 2.2), fp(0, 43, 2.8), fp(0, 48, 0.0)]
        inner = [fp(0, 48, -14.0), fp(0, 20, -18.0), fp(0, -16, -12.0)]
        nose = smooth_path(prof + inner, closed=True, tension=0.4)
        u = skia.Op(sil, nose, skia.PathOp.kUnion_PathOp)
        if u is not None:
            sil = u
    return sil


# hairline loop on the +x side, from the nape (beta 180) to the front (beta 0): (beta, y)
_HAIRLINE = [(180, 49), (166, 48), (152, 45), (140, 39), (130, 29), (121, 15), (112, 1), (103, -8), (95, -9.5), (88, -5),
             (84, 1), (81.5, 3), (78.5, -6), (73, -17), (64, -27), (54, -34), (43, -38.5), (30, -42.5), (16, -45),
             (0, -46)]
_HAIR_LOOP = _HAIRLINE + [(-b, y) for (b, y) in reversed(_HAIRLINE[1:-1])]


def _hair_outline(P, jaw):
    """Head outline grown by the hair volume (more at the top-front: combed-back volume)."""
    right, left = [], []
    s, c = P.s, P.c
    for (y, a, bf, bb) in _HEAD:
        k = smoothstep((-6.0 - y) / 28.0)
        kf = smoothstep((-40.0 - y) / 16.0)
        a2, bf2, bb2 = a + 2.6 * k, bf + 3.0 * k + 4.5 * kf, bb + 3.2 * k
        yy = _jaw_y(y, jaw)
        for sigma, lst in ((1.0, right), (-1.0, left)):
            b = bf2 if sigma * s >= 0 else bb2
            R = math.sqrt((a2 * c) ** 2 + (b * s) ** 2) or 1e-6
            lst.append(P.p(a2 * (sigma * a2 * c / R), yy, b * (sigma * b * s / R)))
    top = P.p(1.5, _HEAD_TOP_Y - 4.5, 2.0)
    chin_z = 0.5 * _HEAD[-1][2] * (1.0 + max(0.0, c))
    chin = P.p(0.0, _CHIN_Y + jaw, chin_z * 0.95)
    return smooth_path([top] + right + [chin] + left[::-1], closed=True)


def _hair_path(P, center_x):
    pts = []
    for (b, y) in _HAIR_LOOP:
        x3, y3, z3, n = _surf(b, y, 1.0)
        pts.append((P.p(x3, y3, z3), P.nz(*n)))
    n = len(pts)
    vis = [v > 0.0 for _, v in pts]
    if not any(vis):
        return None
    if all(vis):
        start = 0
    else:
        # start right after a hidden point
        start = next(i for i in range(n) if vis[i] and not vis[i - 1])
    run = []
    i = start
    while vis[i % n] and len(run) < n:
        run.append(i % n)
        i += 1
    if len(run) < 2:
        return None

    def cross(i_vis, i_hid):
        (pa, va), (pb, vb) = pts[i_vis], pts[i_hid]
        k = va / (va - vb) if va != vb else 0.0
        return (pa[0] + (pb[0] - pa[0]) * k, pa[1] + (pb[1] - pa[1]) * k)

    line = [pts[j][0] for j in run]
    if not all(vis):
        line = [cross(run[0], (run[0] - 1) % n)] + line + [cross(run[-1], (run[-1] + 1) % n)]
    a, b = line[0], line[-1]
    cy = -20.0

    def out(q, toward_x):
        dx, dy = q[0] - center_x, q[1] - cy
        n = math.hypot(dx, dy) or 1.0
        if abs(dx) < 1e-3:
            dx, n = toward_x, 1.0
        return (q[0] + dx / n * 140.0, q[1] + dy / n * 140.0)

    sa = 1.0 if a[0] >= center_x else -1.0
    sb = 1.0 if b[0] > center_x else -1.0
    if sa == sb:
        sb = -sa
    ea, eb = out(a, sa), out(b, sb)
    top = -260.0
    path = skia.Path()
    path.moveTo(center_x + sa * 260.0, ea[1])
    path.lineTo(*ea)
    path.lineTo(*a)
    _spl(path, line, move=False)
    path.lineTo(*eb)
    path.lineTo(center_x + sb * 260.0, eb[1])
    path.lineTo(center_x + sb * 260.0, top)
    path.lineTo(center_x + sa * 260.0, top)
    path.close()
    return path


# --------------------------------------------------------------------------- torso model
# (y, a, bf, bb) body-local coords (feet at 0, up is -y)
_TORSO = [
    (-590.0, 60.5, 22.0, 24.0),
    (-568.0, 60.0, 27.0, 27.0),
    (-542.0, 55.5, 29.5, 28.0),
    (-510.0, 49.5, 28.5, 26.5),
    (-478.0, 43.0, 26.0, 25.0),
    (-450.0, 41.0, 24.5, 24.5),
    (-420.0, 43.0, 25.5, 26.5),
    (-392.0, 46.0, 26.5, 28.0),
    (-374.0, 47.0, 27.0, 28.5),
]
_SHOULDER_Y = -574.0
_SHOULDER_X = 63.0
_NECK_TOP = -646.0
_HIP_Y = -395.0
_L_UP, _L_FORE = 124.0, 112.0


class _G:
    pass


def _yaws(pose):
    phi = clamp(pose.turn, -0.3, 1.0) * TURN_DEG
    hphi = phi + clamp(pose.head_turn, -0.6, 0.6) * TURN_DEG
    b = smoothstep((clamp(pose.back) - 0.25) / 0.5)
    return lerp(phi, 180.0 - phi, b), lerp(hphi, 180.0 - hphi, b)


def _layout(pose: Pose, t=None):
    g = _G()
    g.pose = pose
    g.t = t if t is not None else 0.0
    g.facing = 1.0 if pose.facing >= 0 else -1.0
    g.psb, g.psh = _yaws(pose)
    g.cb, g.sb = math.cos(_rad(g.psb)), math.sin(_rad(g.psb))
    g.back_view = g.cb < -0.05
    if pose.breath is not None:
        br = pose.breath
    elif t is not None:
        br = math.sin(2 * math.pi * 0.2 * t)      # android: perfectly regular
    else:
        br = 0.0
    g.br = br
    g.su = clamp(pose.shoulders_up)
    # light
    g.light = pose.light
    g.tint = pose.tint
    g.tint_amt = pose.tint_amt
    # matrices
    S = pose.scale
    g.M_stage = skia.Matrix.Translate(pose.x, pose.y)
    g.M_stage.preScale(S * g.facing, S)
    _leg_layout(g)
    g.M_legs = skia.Matrix.Translate(0.0, g.walk_dy)
    g.M_upper = skia.Matrix.Translate(0.0, pose.bounce + g.walk_dy)
    g.M_upper.preRotate(pose.lean, 0.0, _HIP_Y)
    inv = skia.Matrix()
    g.M_leg_rel = skia.Matrix.Concat(inv, g.M_legs) if g.M_upper.invert(inv) else skia.Matrix()
    # head
    g.jaw = clamp(pose.mouth_open) * 9.0
    g.P = _Proj(g.psh, clamp(pose.head_nod, -1.5, 1.5))
    piv = g.P.p(0.0, 50.0, -6.0)
    g.neck_x = -5.0 * g.sb
    g.M_head = skia.Matrix.Translate(g.neck_x, _NECK_TOP + 0.6 * pose.head_nod * -2.0)
    g.M_head.preRotate(pose.head_tilt)
    g.M_head.preTranslate(-piv[0], -piv[1])
    # shoulders
    g.sh_y = _SHOULDER_Y - g.su * 9.0 - br * 0.9
    g.arms = {"l": _arm_chain(g, "l"), "r": _arm_chain(g, "r")}
    return g


_L_THIGH, _L_SHIN = 181.0, 180.0


def _leg_layout(g):
    """Hip / knee / ankle per leg (+ walk cycle). g.legs[sig] = (hip, knee, ankle, lift)."""
    pose = g.pose
    g.legs = {}
    floors = []
    for sig in (1.0, -1.0):
        hip = _bp(g, sig * 24.0, _HIP_Y, 0.0)
        depth = _bdepth(g, sig * 22.0, 0.0)
        lift = -max(0.0, -depth) * 0.16          # far foot sits slightly higher (fake ground plane)
        if pose.walk is None:
            ank = (sig * 21.0 * g.cb, -34.0 + lift)
            knee = (lerp(hip[0], ank[0], 0.52), -214.0 + lift * 0.5)
        else:
            ph = 2.0 * math.pi * pose.walk + (0.0 if sig > 0 else math.pi)
            th = _rad(17.0 * math.sin(ph))
            kb = _rad(32.0 * max(0.0, math.sin(ph + 1.3)))
            fx = g.sb
            knee = (hip[0] + _L_THIGH * math.sin(th) * fx - sig * 1.5 * g.cb, hip[1] + _L_THIGH * math.cos(th))
            a2 = th - kb
            ank = (knee[0] + _L_SHIN * math.sin(a2) * fx - sig * 1.5 * g.cb, knee[1] + _L_SHIN * math.cos(a2) + lift)
        g.legs[sig] = (hip, knee, ank, lift)
        floors.append((-34.0 + lift) - ank[1])
    g.walk_dy = min(floors) if pose.walk is not None else 0.0


def _bp(g, x, y, z):
    """Body 3D point -> body-local 2D (yaw only)."""
    return (x * g.cb + z * g.sb, y)


def _bdepth(g, x, z):
    return -x * g.sb + z * g.cb


# --------------------------------------------------------------------------- arms


def _ik(S, T, l1, l2, guess):
    dx, dy = T[0] - S[0], T[1] - S[1]
    d = math.hypot(dx, dy)
    if d < 1e-6:
        dx, dy, d = 0.0, 1.0, 1.0
    ux, uy = dx / d, dy / d
    dc = clamp(d, abs(l1 - l2) + 0.5, l1 + l2 - 0.5)
    ca = clamp((l1 * l1 + dc * dc - l2 * l2) / (2 * l1 * dc), -1.0, 1.0)
    a = math.acos(ca)
    best = None
    for sgn in (1.0, -1.0):
        cs, sn = math.cos(sgn * a), math.sin(sgn * a)
        ex = S[0] + l1 * (ux * cs - uy * sn)
        ey = S[1] + l1 * (ux * sn + uy * cs)
        dd = (ex - guess[0]) ** 2 + (ey - guess[1]) ** 2
        if best is None or dd < best[0]:
            best = (dd, (ex, ey))
    W = (S[0] + ux * dc, S[1] + uy * dc)
    return best[1], W


def _ang(v):
    """2D direction -> angle in degrees, 0 = down, +90 = +x."""
    return math.degrees(math.atan2(v[0], v[1]))


def _dir(a_deg):
    r = _rad(a_deg)
    return (math.sin(r), math.cos(r))


def _wrap180(d):
    return (d + 180.0) % 360.0 - 180.0


def _torso_edge(g, y, side):
    """|x| of the torso silhouette at height y on screen side `side` (+1 / -1, body-local)."""
    a, bf, bb = _torso_slice(y)
    b = bf if side * g.sb >= 0 else bb
    return math.sqrt((a * g.cb) ** 2 + (b * g.sb) ** 2)


def _arm_chain(g, side):
    pose = g.pose
    ap = pose.arm_l if side == "l" else pose.arm_r
    sig = 1.0 if side == "l" else -1.0           # character's left lives on local +x (front view)
    z_sh = _bdepth(g, sig * _SHOULDER_X, 0.0)
    farness = smoothstep(-z_sh / 22.0)           # 0 at the front view .. 1 for the far arm at 3/4
    # the far shoulder sits slightly behind the chest so its cap never bulges out of the chest line
    S = (sig * _SHOULDER_X * g.cb - 9.0 * farness * g.sb, g.sh_y + 2.0 * farness)
    near = z_sh > 0.5 or (abs(z_sh) <= 0.5 and sig < 0)
    out = 1.0 if S[0] > 0.01 else (-1.0 if S[0] < -0.01 else sig)
    turn_eff = (g.psb if not g.back_view else 180.0 - g.psb) / TURN_DEG
    k = 0.0 if g.back_view else smoothstep((turn_eff - 0.03) / 0.22)
    th = ap.shoulder
    if pose.walk is not None and ap.behind < 0.5 and ap.across < 0.5:
        # arms swing opposite to the same-side leg
        th += 12.0 * math.sin(2.0 * math.pi * pose.walk + (math.pi if sig > 0 else 0.0)) * (1.0 - clamp(th / 40.0))
    sgn_raise = lerp(out, 1.0, k)
    d_front = -out * clamp((55.0 - th) / 35.0, -1.0, 1.0)
    sgn_bend = lerp(d_front, 1.0, k)
    # FK (projected length gives natural foreshortening when the swing plane faces camera)
    ur = _rad(th)
    E = (S[0] + _L_UP * sgn_raise * math.sin(ur), S[1] + _L_UP * math.cos(ur))
    au = _ang((E[0] - S[0], E[1] - S[1])) if abs(E[1] - S[1]) + abs(E[0] - S[0]) > 1e-3 else 0.0
    af = au + sgn_bend * ap.elbow
    fl = _L_FORE * (0.78 + 0.22 * abs(sgn_bend))
    dfv = _dir(af)
    W = (E[0] + fl * dfv[0], E[1] + fl * dfv[1])
    # near-front view: a raised arm swings FORWARD (toward camera) and foreshortens instead of
    # flapping out sideways in the picture plane
    fwd = 0.0 if g.back_view else (1.0 - k) * smoothstep((th - 20.0) / 45.0) * (1.0 - clamp(ap.behind * 2.0))
    if fwd > 0.0:
        abd = 0.32
        Ef = (S[0] + _L_UP * out * math.sin(ur) * abd, S[1] + _L_UP * math.cos(ur))
        a2 = ur + _rad(ap.elbow)
        Wf = (Ef[0] + _L_FORE * out * math.sin(a2) * abd * 0.6, Ef[1] + _L_FORE * math.cos(a2))
        E = (lerp(E[0], Ef[0], fwd), lerp(E[1], Ef[1], fwd))
        W = (lerp(W[0], Wf[0], fwd), lerp(W[1], Wf[1], fwd))
        af = _ang((W[0] - E[0], W[1] - E[1]))
    # across: hand toward the opposite side of the chest
    acr = clamp(ap.across)
    beh = clamp(ap.behind)
    if acr > 0.0:
        tx, _ = _bp(g, -sig * 20.0, 0.0, 30.0)
        ty = clamp(W[1], -600.0, -470.0)
        T = (lerp(W[0], tx, acr), lerp(W[1], ty, acr))
        mid = ((S[0] + T[0]) / 2, (S[1] + T[1]) / 2)
        gp = (mid[0] + out * 45.0, mid[1] + 25.0)
        E, W = _ik(S, T, _L_UP, _L_FORE, (lerp(E[0], gp[0], acr), lerp(E[1], gp[1], acr)))
    if beh > 0.0:
        # hands behind the back (small of the back; in profile the clasped hands peek out past it)
        if g.back_view:
            tb = (_bp(g, sig * 9.0, 0.0, -27.0)[0], -408.0)
        else:
            tb = (_bp(g, sig * 4.0, 0.0, -22.0 - 9.0 * smoothstep((abs(g.sb) - 0.55) / 0.4))[0], -418.0)
        bk = 0.22 if g.back_view else 0.32

        def l2_at(b_):
            return _L_FORE * (1.0 - bk * b_)

        px = out * 0.8 * abs(g.cb) - g.sb * (0.3 if g.back_view else 1.15)
        pv = (px, 0.35 if not g.back_view else 0.9)
        pn = math.hypot(*pv) or 1.0
        mid = ((S[0] + tb[0]) / 2, (S[1] + tb[1]) / 2)
        gp_b = (mid[0] + pv[0] / pn * 60.0, mid[1] + pv[1] / pn * 60.0)
        if beh >= 1.0:
            E, W = _ik(S, tb, _L_UP, l2_at(1.0), gp_b)
        else:
            # transition: the hand leaves / enters the back around the OUTSIDE of the hip on this
            # arm's side (waypoint just past the silhouette edge), the elbow staying out and back;
            # from the waypoint the arm swings to the front pose by interpolating joint angles
            # (lengths preserved, no IK elbow flips).
            yw = -440.0
            pw = (out * (_torso_edge(g, yw, out) + 22.0), yw)
            side_gp = (S[0] + out * 52.0, S[1] + 92.0)
            if beh >= 0.5:
                u = (beh - 0.5) / 0.5
                T = (lerp(pw[0], tb[0], u), lerp(pw[1], tb[1], u))
                gq = (lerp(side_gp[0], gp_b[0], u), lerp(side_gp[1], gp_b[1], u))
                E, W = _ik(S, T, _L_UP, l2_at(beh), gq)
            else:
                Em, Wm = _ik(S, pw, _L_UP, l2_at(0.5), side_gp)
                u = beh / 0.5
                au0 = _ang((E[0] - S[0], E[1] - S[1]))
                af0 = _ang((W[0] - E[0], W[1] - E[1]))
                aum = _ang((Em[0] - S[0], Em[1] - S[1]))
                afm = _ang((Wm[0] - Em[0], Wm[1] - Em[1]))
                lu = lerp(math.hypot(E[0] - S[0], E[1] - S[1]), _L_UP, u)
                lf = lerp(math.hypot(W[0] - E[0], W[1] - E[1]), l2_at(0.5), u)
                au_ = au0 + _wrap180(aum - au0) * u
                af_ = af0 + _wrap180(afm - af0) * u
                du, df = _dir(au_), _dir(af_)
                E = (S[0] + lu * du[0], S[1] + lu * du[1])
                W = (E[0] + lf * df[0], E[1] + lf * df[1])
    if acr > 0.0 or beh > 0.0:
        af = _ang((W[0] - E[0], W[1] - E[1]))
    wsgn = 1.0 if k > 0.5 else out * -1.0 if th < 55 else out
    ah = af + ap.wrist * (1.0 if k > 0.5 else wsgn)
    # thumb side: forward (+x) in 3/4, toward the body midline in a front view
    if g.back_view:
        thumb = -out
    elif side == "r":
        thumb = 1.0
    else:
        thumb = 1.0 if k > 0.5 else -1.0
    ch = _G()
    ch.side, ch.sig, ch.S, ch.E, ch.W, ch.ah, ch.af = side, sig, S, E, W, ah, af
    ch.near, ch.out, ch.thumb, ch.hand, ch.across, ch.behind = near, out, thumb, ap.hand, acr, beh
    ch.k = k
    ch.fwd = fwd
    ch.r_sh = 16.5 - 3.0 * farness
    # drawn in front of the torso? (near arm, or any arm reaching toward camera in a front view)
    ch.front = (near or fwd > 0.5) and beh < 0.5
    return ch


def _hand_frame(ch):
    f = _dir(ch.ah)
    k = _HAND_SCALE
    X = (f[1] * ch.thumb * k, -f[0] * ch.thumb * k)
    return skia.Matrix.MakeAll(X[0], f[0] * k, ch.W[0], X[1], f[1] * k, ch.W[1], 0, 0, 1)


_PALM = {"relaxed": (0.0, 20.0), "open": (0.0, 18.0), "palm_up": (0.5, 13.0), "palm_out": (0.0, 18.0),
         "point": (0.0, 16.0), "fist": (0.0, 15.0), "hold": (0.0, 16.0)}


# --------------------------------------------------------------------------- public geometry


def _to_stage(g, m_local, pt):
    m = skia.Matrix.Concat(g.M_stage, g.M_upper)
    if m_local is not None:
        m.preConcat(m_local)
    q = m.mapXY(pt[0], pt[1])
    return (q.x(), q.y())


def head_center(pose: Pose):
    """Stage coords of the face centre (between the eyes)."""
    g = _layout(pose, None)
    P = g.P
    pt = P.p(0.0, 0.0, _face_z(0.0, 0.0))
    return _to_stage(g, g.M_head, pt)


def hand_pos(pose: Pose, side: str):
    """Stage coords of the palm centre of Quill's left ("l") or right ("r") hand."""
    g = _layout(pose, None)
    ch = g.arms["l" if side.startswith("l") else "r"]
    m = _hand_frame(ch)
    px, py = _PALM.get(ch.hand, (0.0, 20.0))
    q = m.mapXY(px, py)
    return _to_stage(g, None, (q.x(), q.y()))


# --------------------------------------------------------------------------- drawing: legs


def _draw_leg(c, g, sig):
    sb = g.sb
    hip, knee, ank, lift = g.legs[sig]
    mid_t = ((hip[0] + knee[0]) / 2, (hip[1] + knee[1]) / 2)
    calf = (lerp(knee[0], ank[0], 0.3), lerp(knee[1], ank[1], 0.3))
    sx, sy = ank[0] - knee[0], ank[1] - knee[1]
    sl = math.hypot(sx, sy) or 1.0
    hem = (ank[0] + sx / sl * 8.0, ank[1] + sy / sl * 8.0)
    pts = [hip, mid_t, knee, calf, hem]
    hw = [24.0, 21.0, 18.5, 17.5, 14.5]
    L, R = [], []
    back = -1.0 if sb >= 0 else 1.0
    for i, (q, w) in enumerate(zip(pts, hw)):
        a_ = pts[max(i - 1, 0)]
        b_ = pts[min(i + 1, len(pts) - 1)]
        dx, dy = b_[0] - a_[0], b_[1] - a_[1]
        d = math.hypot(dx, dy) or 1.0
        nx, ny = dy / d, -dx / d                 # points to +x for a downward leg
        wl = wr = w
        if i == 3 and abs(sb) > 0.2:             # calf bulges on the back side
            if back < 0:
                wl += 2.5 * abs(sb)
            else:
                wr += 2.5 * abs(sb)
        L.append((q[0] - nx * wl, q[1] - ny * wl))
        R.append((q[0] + nx * wr, q[1] + ny * wr))
    p = skia.Path()
    _spl(p, L)
    _spl(p, R[::-1], move=False)
    p.close()
    _draw_boot(c, g, ank, lift)
    _cel(c, p, PANTS, PANTS_SH, (7.0, -4.0), hi="#2B3244", hi_off=(-2.5, 0.0), hi_alpha=0.9)
    # knee crease
    c.drawPath(_spl(skia.Path(), [(knee[0] - 8, knee[1] + 2), (knee[0], knee[1] + 5),
                                  (knee[0] + 7, knee[1] + 3)]), _pt(PANTS_SH, 0.6, stroke=1.4))


def _draw_boot(c, g, ank, lift):
    s = abs(g.sb)
    dirx = 1.0 if g.sb >= 0 else -1.0
    toe = 40.0 * s
    heel = 5.0 * s
    x = ank[0]
    y0 = ank[1] + 34.0
    w = 13.5
    # front view: rounded toe cap toward camera; 3/4: profile-ish foot pointing toward facing
    pts = [
        (x - w, y0 - 46),
        (x + w, y0 - 46),
        (x + w + dirx * toe * 0.25 + 0.5, y0 - 24),
        (x + w * (1 - s * 0.3) + dirx * toe * 0.75 + 1.0, y0 - 13 + s * 1.5),
        (x + w * (1 - s * 0.4) + dirx * toe + 2.0, y0 - 4),
        (x + w * (1 - s * 0.5) + dirx * toe, y0 + 0.5),
        (x - w - heel, y0 + 0.5),
        (x - w - heel - 0.5, y0 - 10),
        (x - w, y0 - 26),
    ]
    if dirx < 0:
        pts = [(2 * x - px, py) for (px, py) in pts]
    if g.back_view:
        # from behind we see the heel; toe hidden
        pts = [
            (x - w, y0 - 46), (x + w, y0 - 46), (x + w + 0.5, y0 - 20), (x + w + 1, y0 - 6),
            (x + w - 1, y0 + 0.5), (x - w + 1, y0 + 0.5), (x - w - 1, y0 - 6), (x - w - 0.5, y0 - 20)]
        if s > 0.1:
            pts[3] = (pts[3][0] + dirx * toe * 0.5, pts[3][1])
            pts[4] = (pts[4][0] + dirx * toe * 0.6, pts[4][1])
    p = smooth_path(pts, closed=True, tension=0.42)
    _cel(c, p, BOOT, "#08090D", (6.0, -3.0), hi=BOOT_HI, hi_off=(-2.0, 2.5), hi_alpha=0.8)
    # sole line
    c.drawLine(min(q[0] for q in pts) + 3, y0 - 3.0, max(q[0] for q in pts) - 3, y0 - 3.0,
               _pt("#2A2F3D", 0.9, stroke=1.6))


# --------------------------------------------------------------------------- drawing: torso


def _torso_path(g):
    br = g.br
    left, right = [], []
    s, cc = g.sb, g.cb
    for i, (y, a, bf, bb) in enumerate(_TORSO):
        if i <= 2:
            a = a * (1.0 + 0.006 * br)
            y = y - g.su * (6.0 if i == 0 else 3.0) - br * (0.8 if i < 2 else 0.4)
        for sigma, lst in ((1.0, right), (-1.0, left)):
            b = bf if sigma * s >= 0 else bb
            R = math.sqrt((a * cc) ** 2 + (b * s) ** 2) or 1e-6
            lst.append((sigma * R, y))
    # shoulder line (z ~ 0)
    sy = g.sh_y
    sh_pts = ((64.0, sy - 12.0), (52.0, sy - 23.5), (34.0, sy - 30.0), (16.0, sy - 32.5))
    top_r = [(x * cc, y) for (x, y) in sh_pts]
    top_l = [(-x * cc, y) for (x, y) in sh_pts]
    hem_y = _TORSO[-1][0]
    # hem: bows down toward the viewer (we look down on it)
    hl, hr = left[-1], right[-1]
    hem = [hl, (lerp(hl[0], hr[0], 0.3), hem_y + 4.0), (lerp(hl[0], hr[0], 0.7), hem_y + 4.0), hr]
    p = skia.Path()
    seq = top_l[::-1] + left + hem[1:-1] + right[::-1] + top_r
    _spl(p, seq, closed=True)
    return p


def _front_pt(g, x, y, a, bf):
    """Point on the torso front surface at local x (projected) + facing factor."""
    u = clamp(x / a, -1, 1)
    z = bf * math.sqrt(max(0.0, 1 - u * u))
    nz = -(u / a) * g.sb + (math.sqrt(max(0.0, 1 - u * u)) / bf) * g.cb
    nn = math.hypot(u / a, math.sqrt(max(0.0, 1 - u * u)) / bf) or 1.0
    return _bp(g, x, y, z), nz / nn


def _draw_torso(c, g, seam_a):
    p = _torso_path(g)
    _cel(c, p, UNI, UNI_SH, (11.0, -5.0), hi=UNI_HI, hi_off=(-3.0, 3.5), hi_alpha=0.95)
    c.save()
    c.clipPath(p, skia.ClipOp.kIntersect, True)
    if not g.back_view:
        # asymmetric closure seam on the right front + matching piping
        # (local x is mirrored for facing -1, so multiply by facing to keep it on his physical right)
        fs = g.facing
        pts = []
        for (x, y) in ((-12.0, -606.0), (-20.0, -560.0), (-24.0, -515.0), (-24.0, -470.0), (-23.0, -410.0),
                       (-22.0, -370.0)):
            a, bf, _ = _torso_slice(y)
            q, v = _front_pt(g, x * fs, y, a, bf)
            pts.append(q)
        c.drawPath(_spl(skia.Path(), pts), _pt(UNI_LINE, 0.95, stroke=2.0))
        c.drawPath(_spl(skia.Path(), [(q[0] + 2.2 * fs, q[1]) for q in pts]), _pt(UNI_HI, 0.5, stroke=1.0))
    else:
        # back seam + shoulder-blade yoke
        pts = []
        for y in (-606.0, -560.0, -500.0, -440.0, -372.0):
            pts.append(_bp(g, 0.0, y, -_torso_slice(y)[2]))
        c.drawPath(_spl(skia.Path(), pts), _pt(UNI_LINE, 0.8, stroke=1.6))
        yk = []
        for x in (-50.0, -25.0, 0.0, 25.0, 50.0):
            a, _, bb = _torso_slice(-548.0)
            u = clamp(x / a, -1, 1)
            yk.append(_bp(g, x, -548.0 + abs(x) * 0.18, -bb * math.sqrt(max(0, 1 - u * u))))
        c.drawPath(_spl(skia.Path(), yk), _pt(UNI_LINE, 0.55, stroke=1.4))
    # hem band
    band = skia.Path()
    hy = _TORSO[-1][0]
    band.moveTo(-200.0, hy - 13.0)
    band.cubicTo(-60.0, hy - 13.0, -40.0, hy - 9.0, 0.0, hy - 9.0)
    band.cubicTo(40.0, hy - 9.0, 60.0, hy - 13.0, 200.0, hy - 13.0)
    band.lineTo(200.0, 0.0)
    band.lineTo(-200.0, 0.0)
    band.close()
    c.clipPath(band, skia.ClipOp.kIntersect, True)
    c.drawPath(p, _pt(UNI_SH, 0.6))
    c.drawPath(_spl(skia.Path(), [(-200.0, hy - 13.0), (-50.0, hy - 12.0), (0.0, hy - 9.0), (50.0, hy - 12.0),
                                  (200.0, hy - 13.0)]), _pt(UNI_HI, 0.35, stroke=1.0))
    c.restore()
    return p


def _torso_slice(y):
    ts = _TORSO
    if y <= ts[0][0]:
        return ts[0][1:]
    if y >= ts[-1][0]:
        return ts[-1][1:]
    for i in range(1, len(ts)):
        if y < ts[i][0]:
            y0, a0, f0, b0 = ts[i - 1]
            y1, a1, f1, b1 = ts[i]
            k = (y - y0) / (y1 - y0)
            return a0 + (a1 - a0) * k, f0 + (f1 - f0) * k, b0 + (b1 - b0) * k
    return ts[-1][1:]


def _draw_insignia(c, g):
    if g.back_view:
        return
    # on his physical LEFT chest for both facings (facing -1 mirrors local x), so for the film's
    # facing -1 it sits on the near, readable side; the emblem itself is never drawn mirrored
    y = -548.0
    a, bf, _ = _torso_slice(y)
    q, v = _front_pt(g, 32.0 * g.facing, y, a, bf)
    if v < 0.12:
        return
    kx = clamp(v, 0.15, 1.0) ** 0.8
    c.save()
    c.translate(q[0], q[1])
    c.scale(kx * g.facing, 1.0)
    r = 9.5
    c.drawCircle(0, 0, r + 1.2, _pt(UNI_LINE, 0.6))
    c.drawCircle(0, 0, r, _pt(INSIG, 1.0, stroke=1.5))
    # stylized quill feather (tilted leaf with a shaft that runs out into a nib)
    c.rotate(38.0)
    vane = skia.Path()
    _spl(vane, [(0.0, -7.6), (3.0, -4.0), (3.1, 1.0), (1.0, 4.6), (0.0, 5.4)])
    _spl(vane, [(0.0, 5.4), (-2.2, 3.0), (-2.7, -1.5), (-1.6, -5.2), (0.0, -7.6)], move=False)
    vane.close()
    c.drawPath(vane, _pt(INSIG, 0.95))
    c.drawLine(0.4, -6.0, -0.2, 8.6, _pt(UNI, 1.0, stroke=0.9))
    # barb notches
    c.drawLine(0.3, -1.0, 3.2, -2.6, _pt(UNI, 0.9, stroke=0.7))
    c.drawLine(0.1, 2.2, -2.6, 0.9, _pt(UNI, 0.9, stroke=0.7))
    c.drawLine(-0.2, 7.0, -0.5, 9.4, _pt(INSIG, 1.0, stroke=1.0))
    c.restore()


def _draw_shoulder_stripe(c, g):
    """Teal stripe from the collar over the right shoulder (torso part)."""
    sy = g.sh_y
    pts3 = [(-23.0, sy - 26.0), (-38.0, sy - 21.5), (-53.0, sy - 13.0), (-63.0, sy - 3.0)]
    pts = [(_bp(g, x, y, 4.0 if not g.back_view else -4.0)) for (x, y) in pts3]
    pts = [(x, y + 3.0) for (x, y) in pts]
    c.drawPath(_spl(skia.Path(), pts), _pt(COLLAR_SH, 1.0, stroke=7.0))
    c.drawPath(_spl(skia.Path(), pts), _pt(COLLAR, 1.0, stroke=5.0))


# --------------------------------------------------------------------------- drawing: arms + hands


def _arm_paths(ch):
    cached = getattr(ch, "_paths", None)
    if cached is not None and cached[0] == (ch.S, ch.E, ch.W):
        return cached[1], cached[2]
    S, E, W = ch.S, ch.E, ch.W
    upper = _capsule(S, E, ch.r_sh, 12.8)
    fore = _capsule(E, W, 12.8, 10.0)
    ch._paths = ((S, E, W), upper, fore)
    return upper, fore


def _draw_arm(c, g, ch, part="all", seam_a=0.0, hand=True):
    """part: "all" (one continuous sleeve), "upper" or "fore" (for hands-behind-back layering)."""
    upper, fore = _arm_paths(ch)
    off = (5.0, -3.0)
    hoff = (-2.2, 2.2)
    line = _pt(UNI_LINE, 0.9, stroke=1.3)
    if part == "all":
        full = getattr(ch, "_full", None)
        if full is None:
            full = _union([upper, fore])
            ch._full = full
        _cel(c, full, UNI, UNI_SH, off, hi=UNI_HI, hi_off=hoff, hi_alpha=0.8)
        c.drawPath(full, line)
        _elbow_fold(c, ch)
    elif part == "upper":
        _cel(c, upper, UNI, UNI_SH, off, hi=UNI_HI, hi_off=hoff, hi_alpha=0.8)
        c.drawPath(upper, line)
    else:
        _cel(c, fore, UNI, UNI_SH, off, hi=UNI_HI, hi_off=hoff, hi_alpha=0.8)
        c.drawPath(fore, line)
    if part in ("all", "fore"):
        # cuff
        f = _dir(ch.af)
        cx, cy = ch.W[0] - f[0] * 7.0, ch.W[1] - f[1] * 7.0
        cuff = _capsule((cx, cy), (ch.W[0] - f[0] * 1.0, ch.W[1] - f[1] * 1.0), 10.6, 10.4)
        c.drawPath(cuff, _pt(UNI_SH, 1.0))
        nx, ny = -f[1], f[0]
        c.drawLine(cx + nx * 10.0, cy + ny * 10.0, cx - nx * 10.0, cy - ny * 10.0, _pt(UNI_HI, 0.45, stroke=1.0))
        if hand:
            _draw_hand(c, g, ch, seam_a)
    if part in ("all", "upper") and ch.side == "r":
        _draw_sleeve_stripe(c, g, ch)


def _elbow_fold(c, ch):
    """Small fabric crease on the inside of the elbow when it bends."""
    au = _ang((ch.E[0] - ch.S[0], ch.E[1] - ch.S[1]))
    bend = abs(_ang((ch.W[0] - ch.E[0], ch.W[1] - ch.E[1])) - au)
    bend = min(bend, 360 - bend)
    if bend <= 25:
        return
    u = _dir(au)
    f = _dir(ch.af)
    ix, iy = (f[0] - u[0]), (f[1] - u[1])
    n = math.hypot(ix, iy) or 1
    ix, iy = ix / n, iy / n
    px, py = ch.E[0] + ix * 6.0, ch.E[1] + iy * 6.0
    c.drawLine(px - iy * 5.0, py + ix * 5.0, px + iy * 5.0, py - ix * 5.0,
               _pt(UNI_LINE, clamp((bend - 25) / 40) * 0.8, stroke=1.4))


def _draw_sleeve_stripe(c, g, ch):
    S, E = ch.S, ch.E
    dx, dy = E[0] - S[0], E[1] - S[1]
    d = math.hypot(dx, dy) or 1.0
    ux, uy = dx / d, dy / d
    nx, ny = -uy, ux
    # lateral surface faces camera in 3/4 -> stripe runs near the middle; front view -> outer edge
    o = ch.out
    side_off = lerp(9.5, 2.0, ch.k) if not g.back_view else 9.5
    sgn = 1.0 if (nx * o) > 0 else -1.0
    if ch.k > 0.5 and not g.back_view:
        sgn = -1.0 if nx > 0 else 1.0    # keep the stripe on the back half of the sleeve
    a = (S[0] + nx * sgn * side_off * 0.6 - ux * 6, S[1] + ny * sgn * side_off * 0.6 - uy * 6)
    b = (E[0] + nx * sgn * side_off - ux * 8, E[1] + ny * sgn * side_off - uy * 8)
    m = ((a[0] + b[0]) / 2 + nx * sgn * 1.5, (a[1] + b[1]) / 2 + ny * sgn * 1.5)
    path = _spl(skia.Path(), [a, m, b])
    c.save()
    up, _ = _arm_paths(ch)
    c.clipPath(up, skia.ClipOp.kIntersect, True)
    c.drawPath(path, _pt(COLLAR_SH, 1.0, stroke=6.2, cap="butt"))
    c.drawPath(path, _pt(COLLAR, 1.0, stroke=4.4, cap="butt"))
    c.restore()


def _chain(pts, r0, r1):
    n = len(pts)
    rs = [lerp(r0, r1, i / (n - 1)) for i in range(n)]
    return _union([_capsule(pts[i], pts[i + 1], rs[i], rs[i + 1]) for i in range(n - 1)])


# Hand parts in hand-local coords: wrist at (0, 0), fingers toward +y, thumb toward +x.
# Each part: ("chain", points, r_start, r_end) or ("blob", points). Listed back to front.
_PALM_BLOB = [(-9.0, -1.0), (8.5, -1.0), (10.2, 12.0), (9.6, 26.5), (1.0, 29.0), (-9.4, 27.5), (-10.4, 13.0)]
_HAND_PARTS = {
    "relaxed": [
        # one curled finger mass (mitten) + thumb resting along the index finger
        ("blob", [(-7.4, -1.0), (-8.6, 9.0), (-9.0, 20.0), (-8.5, 30.0), (-6.8, 37.8), (-3.6, 43.2), (0.4, 45.4),
                  (3.8, 44.2), (5.5, 40.8), (5.3, 36.6), (6.8, 31.0), (8.2, 21.0), (8.0, 9.0), (6.8, -1.0)]),
        ("chain", [(6.2, 5.0), (9.6, 13.0), (10.2, 21.0), (8.6, 28.0)], 4.2, 2.9),
    ],
    "open": [
        ("chain", [(-8.2, 24.0), (-10.6, 34.0), (-12.2, 42.0)], 2.9, 2.5),
        ("chain", [(-3.8, 25.5), (-4.6, 38.5), (-5.0, 48.5)], 3.2, 2.8),
        ("chain", [(1.0, 26.0), (1.2, 40.5), (1.4, 51.5)], 3.3, 2.9),
        ("chain", [(5.8, 25.0), (7.2, 38.5), (8.4, 48.5)], 3.2, 2.8),
        ("blob", [(-10.0, -1.0), (9.5, -1.0), (11.5, 12.0), (10.5, 26.5), (0.0, 28.5), (-10.5, 27.0),
                  (-11.5, 13.0)]),
        ("chain", [(8.0, 5.0), (13.5, 12.0), (18.0, 19.0), (21.0, 25.0)], 4.3, 3.0),
    ],
    "palm_out": [
        ("chain", [(-8.0, 24.0), (-9.4, 34.0), (-10.2, 42.5)], 2.9, 2.5),
        ("chain", [(-3.8, 25.5), (-4.2, 38.5), (-4.4, 48.5)], 3.2, 2.8),
        ("chain", [(1.0, 26.0), (1.1, 40.5), (1.2, 51.0)], 3.3, 2.9),
        ("chain", [(5.8, 25.0), (6.6, 38.5), (7.2, 48.0)], 3.2, 2.8),
        ("blob", [(-10.0, -1.0), (9.5, -1.0), (11.5, 12.0), (10.5, 26.5), (0.0, 28.5), (-10.5, 27.0),
                  (-11.5, 13.0)]),
        ("chain", [(8.0, 5.0), (13.0, 11.0), (16.5, 18.0), (18.5, 24.0)], 4.3, 3.0),
    ],
    "palm_up": [
        # cupped palm seen from above-front (palm plane tilted toward camera); thumb on the near side
        # (-x = toward the viewer), fingertips curling up (+x) into a shallow dish
        ("chain", [(5.6, 23.0), (7.6, 28.5), (9.6, 33.0)], 2.5, 2.1),
        ("chain", [(3.0, 24.5), (5.0, 31.5), (7.6, 37.0)], 2.8, 2.3),
        ("chain", [(0.0, 25.5), (1.6, 33.5), (4.4, 40.0)], 2.9, 2.4),
        ("blob", [(-7.0, -1.0), (5.6, -1.0), (8.0, 9.0), (8.6, 18.5), (7.2, 25.0), (1.5, 27.2), (-5.0, 27.0),
                  (-9.4, 21.0), (-9.6, 10.0)]),
        ("blobhi", [(-5.6, 3.5), (4.8, 3.0), (6.4, 11.0), (6.0, 19.0), (1.0, 23.0), (-5.6, 21.4), (-7.2, 12.0)]),
        ("chain", [(-3.6, 25.0), (-3.0, 33.2), (-0.6, 39.6)], 3.0, 2.5),
        ("chain", [(-6.4, 4.5), (-10.4, 10.0), (-12.6, 16.0), (-12.8, 21.5)], 4.2, 3.0),
    ],
    "point": [
        ("blob", [(-9.5, -1.0), (9.0, -1.0), (11.0, 12.0), (10.6, 24.0), (6.0, 30.5), (-6.0, 31.0), (-10.6, 25.0),
                  (-11.0, 12.0)]),
        ("chain", [(6.0, 24.0), (7.0, 37.0), (7.6, 50.0)], 3.4, 2.9),
        ("chain", [(8.0, 5.0), (12.2, 13.0), (10.6, 22.0)], 4.2, 3.3),
    ],
    "fist": [
        ("blob", [(-9.5, -1.0), (9.0, -1.0), (11.0, 12.0), (11.0, 24.0), (6.5, 31.0), (-6.5, 31.5), (-11.0, 25.0),
                  (-11.0, 12.0)]),
        ("chain", [(8.5, 5.0), (11.0, 15.0), (5.5, 23.5)], 4.3, 3.4),
    ],
}
_HAND_PARTS["hold"] = _HAND_PARTS["fist"]
_HAND_LINES = {
    "relaxed": [([(-8.2, 30.6), (-3.6, 34.4), (2.2, 37.0)], 0.6), ([(-1.4, 38.0), (1.0, 43.0)], 0.35)],
    "open": [([(-4.0, 9.0), (0.5, 15.0), (6.0, 18.0)], 0.3), ([(-8.0, 20.0), (-2.0, 22.0)], 0.25)],
    "palm_out": [([(-4.0, 9.0), (0.5, 15.0), (6.0, 18.0)], 0.4), ([(-8.0, 19.0), (-1.0, 21.0), (4.0, 19.5)], 0.35)],
    "palm_up": [([(5.6, 15.5), (1.0, 18.2), (-4.6, 17.4)], 0.32), ([(-4.6, 5.0), (-3.4, 10.0), (-3.6, 15.0)], 0.28)],
    "point": [([(-9.0, 18.5), (-3.0, 21.0), (3.0, 21.0)], 0.4), ([(-8.0, 25.5), (-2.0, 27.5), (4.0, 26.5)], 0.35)],
    "fist": [([(-9.0, 17.5), (-3.0, 20.0), (4.0, 19.5)], 0.45), ([(-8.0, 24.5), (-2.0, 26.5), (4.5, 25.5)], 0.4)],
}
_HAND_LINES["hold"] = _HAND_LINES["fist"]
_HAND_SCALE = 1.06
_HAND_CACHE = {}
_HAND_SHADE = {}


def _hand_geom(kind):
    if kind not in _HAND_CACHE:
        parts = []
        for spec in _HAND_PARTS[kind]:
            if spec[0] == "chain":
                parts.append((_chain(spec[1], spec[2], spec[3]), False))
            else:
                parts.append((smooth_path(spec[1], closed=True, tension=0.5), spec[0] == "blobhi"))
        _HAND_CACHE[kind] = (parts, _union([q for q, hi in parts if not hi]), _HAND_LINES.get(kind, []))
    return _HAND_CACHE[kind]


def _draw_hand(c, g, ch, seam_a):
    kind = ch.hand if ch.hand in _PALM else "relaxed"
    parts, sil, lines = _hand_geom(kind)
    m = _hand_frame(ch)
    c.save()
    c.concat(m)
    # the light lives at body-local (+x, up); express that offset in hand space
    inv = skia.Matrix()
    off = (3.5, -2.0)
    if m.invert(inv):
        v = inv.mapVector(off[0], off[1])
        off = (v.x(), v.y())
    outline = _pt(SKIN_SH2, 0.9, stroke=0.9)
    for pth, hi in parts:
        if hi:
            c.drawPath(pth, _pt(SKIN_HI, 0.9))
            continue
        c.drawPath(pth, _pt(SKIN))
        c.drawPath(pth, outline)
    ang = int(round(math.degrees(math.atan2(off[1], off[0])) / 15.0)) % 24
    key = (kind, ang)
    shp = _HAND_SHADE.get(key)
    if shp is None:
        r = math.radians(ang * 15.0)
        shp = _minus_shifted(sil, (4.0 * math.cos(r), 4.0 * math.sin(r)))
        _HAND_SHADE[key] = shp
    if shp is not None:
        c.drawPath(shp, _pt(SKIN_SH, 0.8))
    if _RIM is not None:
        c.restore()
        c.save()
        hs = skia.Path(sil)
        hs.transform(m)
        _rim_edge(c, hs)
        c.concat(m)
    for pts, a in lines:
        c.drawPath(_spl(skia.Path(), pts), _pt(SKIN_SH2, a + 0.2, stroke=0.9))
    if seam_a > 0.02:
        c.drawLine(-8.5, 3.5, 8.0, 3.5, _pt(SEAM, seam_a * 0.8, stroke=0.8))
    c.restore()


def _draw_clasped_hands(c, g, chs, seam_a):
    """Back view, hands clasped at the small of the back: the far hand hangs relaxed, the near
    hand wraps over its wrist (we see the backs of both hands)."""
    order = sorted(chs, key=lambda ch: ch.near)
    far, near = order[0], order[1]
    for ch in order:
        _draw_arm(c, g, ch, "fore", seam_a, hand=False)
    toward = 1.0 if near.W[0] > far.W[0] else -1.0
    f2 = _G()
    f2.__dict__.update(far.__dict__)
    f2.ah = 30.0 * toward
    f2.hand = "relaxed"
    f2.thumb = -toward
    _draw_hand(c, g, f2, seam_a)
    n2 = _G()
    n2.__dict__.update(near.__dict__)
    n2.W = (far.W[0] + toward * 12.0, far.W[1] + 9.0)
    n2.ah = -70.0 * toward
    n2.hand = "fist"
    n2.thumb = 1.0
    _draw_hand(c, g, n2, seam_a)


# --------------------------------------------------------------------------- drawing: neck + collar


def _neck_head_edge(g):
    """x (head coords) of the neck's +x edge just under the skull, for the back-view jaw clip."""
    return 30.0 * 0.92


def _neck_geom(g):
    hx = g.neck_x
    m = g.M_head
    bk = smoothstep((0.35 - g.cb) / 1.1)          # 0 front .. 1 back: the back of the neck reads wider
    wt = lerp(19.0, 22.5, bk)
    wb = lerp(22.0, 25.5, bk)
    ty = lerp(26.0, 23.0, bk)
    g._neck_wt, g._neck_wb, g._neck_ty = wt, wb, ty
    q1 = m.mapXY(-wt, ty)
    q2 = m.mapXY(wt, ty)
    top_c = m.mapXY(0.0, ty)
    base_y = -604.0 - g.su * 4.0
    wm = (wt + wb) / 2 - lerp(-0.5, 2.0, bk)
    pts_l = [(q1.x(), q1.y()), (hx - wm, lerp(q1.y(), base_y, 0.6)), (hx - wb, base_y)]
    pts_r = [(hx + wb, base_y), (hx + wm, lerp(q2.y(), base_y, 0.6)), (q2.x(), q2.y())]
    p = skia.Path()
    _spl(p, pts_l)
    p.lineTo(*pts_r[0])
    _spl(p, pts_r, move=False)
    p.lineTo(top_c.x(), top_c.y() - 22.0)
    p.close()
    return p, base_y


def _draw_neck(c, g, seam_a, head_sil=None):
    p, base_y = _neck_geom(g)
    _cel(c, p, SKIN, SKIN_SH, (6.0, -2.0))
    hx = g.neck_x
    c.save()
    c.clipPath(p, skia.ClipOp.kIntersect, True)
    if head_sil is not None and not g.back_view:
        # jaw shadow on the neck
        sh = skia.Path(head_sil)
        sh.transform(g.M_head)
        sh.offset(1.5, 8.0)
        c.drawPath(sh, _pt(SKIN_SH, 0.95))
    if seam_a > 0.02:
        if not g.back_view:
            # one fine seam down each side of the throat
            for sx in (-1.0, 1.0):
                ang = _rad(sx * 62.0 + g.psb)
                x0 = hx + 15.5 * math.sin(ang)
                if math.cos(ang) > 0.1:
                    c.drawLine(x0, base_y - 40, x0 + sx * 0.8, base_y - 2, _pt(SEAM, seam_a * 0.9, stroke=0.9))
        else:
            c.drawLine(hx, base_y - 40, hx, base_y - 2, _pt(SEAM, seam_a, stroke=1.0))
    if g.P.c < 0.2:
        # shadow of the hair on the nape: the hair region nudged down, clipped to the neck
        center_x = g.P.p(0, -20, 0)[0]
        hp = _hair_path(g.P, center_x)
        if hp is not None:
            hs = skia.Path(hp)
            hs.offset(0.0, 3.5)
            hs.transform(g.M_head)
            c.drawPath(hs, _pt(SKIN_SH, 0.75 * smoothstep((0.2 - g.P.c) / 0.4)))
    c.restore()


def _collar_geom(g):
    hx = g.neck_x
    top = -624.0 - g.su * 4.0 - g.br * 0.4
    bot = -605.0 - g.su * 4.0 - g.br * 0.6
    rx = 25.0
    ry = 5.0
    return hx, top, bot, rx, ry


def _draw_collar_back(c, g):
    hx, top, bot, rx, ry = _collar_geom(g)
    if g.back_view:
        return
    inner = skia.Path()
    inner.addOval(skia.Rect(hx - rx + 1.5, top - ry, hx + rx - 1.5, top + ry))
    c.drawPath(inner, _pt(COLLAR_IN))


def _draw_collar(c, g):
    hx, top, bot, rx, ry = _collar_geom(g)
    # band: front half of a short cylinder
    band = skia.Path()
    n = 10
    upper = [(hx + rx * math.cos(math.pi * (1 - i / n)), top + ry * math.sin(math.pi * (1 - i / n)))
             for i in range(n + 1)]
    lower = [(hx + rx * 1.06 * math.cos(math.pi * (i / n)), bot + ry * 1.1 * math.sin(math.pi * (i / n)))
             for i in range(n + 1)]
    band = _two_curve_path(upper, lower)
    _cel(c, band, COLLAR, COLLAR_SH, (6.0, 0.0), hi=COLLAR_HI, hi_off=(0.0, 1.6), hi_alpha=0.75)
    if not g.back_view:
        # closure notch at the front
        fx = hx + rx * g.sb * 0.92
        c.drawLine(fx, top + ry * 0.9, fx, bot + ry * 1.0, _pt(COLLAR_IN, 0.9, stroke=1.4))
    else:
        c.drawLine(hx - rx * g.sb * 0.9, top + ry, hx - rx * g.sb * 0.9, bot + ry, _pt(COLLAR_SH, 0.6, stroke=1.0))


# --------------------------------------------------------------------------- drawing: head


class _Eye:
    pass


_UP_OPEN = [(-12.5, 1.0), (-8.5, -4.2), (-3.0, -6.1), (3.0, -6.0), (8.5, -3.9), (12.5, -0.8)]
_LO = [(-12.5, 1.0), (-7.5, 4.6), (0.0, 6.4), (7.5, 5.0), (12.5, -0.8)]
_CLOSED = [(-12.5, 1.0), (-8.5, 2.6), (-3.0, 3.6), (3.0, 3.5), (8.5, 2.3), (12.5, -0.8)]
_IRIS_R = 7.3
_EYE_RECESS = 6.0


def _eye_geom(g, side):
    """side +1 = Quill's left eye (local +x), -1 = right eye."""
    pose = g.pose
    P = g.P
    ex = _EYE_X * side
    lid_auto = auto_blink(g.t, seed=0, rate=4.6, robotic=True)
    lid = pose.lid_l if side > 0 else pose.lid_r
    if lid is None:
        lid = lid_auto
    lid = clamp(lid)
    wide = clamp(pose.eye_wide)
    sq = clamp(pose.squint + max(0.0, pose.smile) * 0.35)
    ly = clamp(pose.look_y, -1.2, 1.2)
    lx = clamp(pose.look_x * g.facing, -1.2, 1.2)
    bw = clamp(pose.brow_worry) ** 0.7          # worry reads early (0.3 is already legible)

    def ep(u, v):
        # the eyeball sits recessed in its socket, so at strong yaw the far eye tucks in behind the
        # cheek / brow-ridge contour instead of sliding onto the silhouette
        x = ex + side * u
        return P.p(x, v, _face_z(x, v) - _EYE_RECESS)

    def es(u, v, dz=-0.5):
        x = ex + side * u
        return P.p(x, v, _face_z(x, v) + dz)

    # normal / compression at the eye centre
    a, bf, _ = _slice(0.0)
    zc = _face_z(ex, 0.0)
    kx = P.nz(ex / (a * a), zc / (bf * bf))
    E = _Eye()
    E.side = side
    E.kx = kx
    E.alpha = smoothstep((kx - 0.12) / 0.1)     # far eye fades out over the last few degrees of yaw
    E.visible = E.alpha > 0.01
    if not E.visible:
        return E
    # iris placement (needed first: the upper lid never retracts above the iris top unless wide > 0.7)
    iu = lx * 5.2 * side
    iv = 0.9 + ly * 3.0
    iris_top = iv - _IRIS_R
    cover = 0.75 - max(0.0, wide - 0.7) / 0.3 * 2.9
    up_open = []
    for (u, v) in _UP_OPEN:
        w = 1.0 - (abs(u) / 12.5) ** 2
        v0 = v + ly * 1.9 * w + sq * 0.9 * w
        # worry lifts the inner half of the upper lid a touch (the sad triangle), lowers the outer
        v0 += (-0.9 * bw * clamp((2.0 - u) / 10.0) + 0.5 * bw * clamp((u - 4.0) / 8.0)) * w
        lim = iris_top + cover + (abs(u - iu) / 7.3) ** 2 * 3.0
        want = v0 - wide * 4.2 * w
        v2 = max(want, min(v0, lim))
        up_open.append((u, v2))
    lo = []
    for (u, v) in _LO:
        w = 1.0 - (abs(u) / 12.5) ** 2
        # the lower lid rises a little to meet a closing upper lid
        lo.append((u, v - sq * 4.6 * w + ly * 0.7 * w - wide * 0.8 * w - (1.0 - lid) * 1.4 * w))
    cl = [(u, lerp(v, lo_v, 0.8) - sq * 1.0 * (1 - (abs(u) / 12.5) ** 2))
          for (u, v), lo_v in zip(_CLOSED, [lo[0][1], lerp(lo[0][1], lo[1][1], 0.6), lerp(lo[1][1], lo[2][1], 0.6),
                                           lerp(lo[2][1], lo[3][1], 0.4), lerp(lo[3][1], lo[4][1], 0.45), lo[4][1]])]
    up = [(u, lerp(cv, ov, lid)) for (u, ov), (_, cv) in zip(up_open, cl)]
    # never let the upper lid cross below the lower lid
    lo_at = lambda u: _interp_curve(lo, u)  # noqa: E731
    up = [(u, min(v, lo_at(u) - 0.05)) for (u, v) in up]
    E.lid = lid
    E.gap = max(lo_at(u) - v for (u, v) in up[1:-1])
    E.up_uv, E.lo_uv, E.open_uv = up, lo, up_open
    E.up = [ep(u, v) for (u, v) in up]
    E.lo = [ep(u, v) for (u, v) in lo]
    E.crease = [es(u, v - 3.2 - wide * 0.6, -1.5) for (u, v) in up_open[1:-1]]
    E.opening = _two_curve_path(E.up, E.lo[::-1]) if E.gap > 0.4 else None
    E.iris_c = ep(iu, iv)
    E.iris_r = _IRIS_R
    E.kx_i = clamp(P.nz((ex + side * iu) / (a * a), _face_z(ex + side * iu, iv) / (bf * bf)), 0.12, 1.0) ** 0.85
    E.pupil = 2.55 * clamp(pose.pupil, 0.5, 1.6) * (1.0 - 0.22 * clamp(pose.process))
    # brows: thin and straight, restrained (~40 % of Rae's travel). Worry is mostly an ANGLE change
    # (inner third tilts up, kink at the middle) so even small values read at medium distance.
    br_r = clamp(pose.brow_raise, -1, 1)
    br_f = clamp(pose.brow_furrow)
    sm = clamp(pose.smirk, -1, 1)
    sqb = sq * 0.8
    b_tip = (-12.4 + br_f * 1.6 - bw * 0.4, -12.4 - br_r * 3.0 - bw * 4.6 + br_f * 2.6 + sqb)
    b_in = (-9.6 + br_f * 1.6 - bw * 0.3, -13.0 - br_r * 3.0 - bw * 3.6 + br_f * 2.3 + sqb)
    b_kink = (-3.0 + br_f * 0.6, -14.0 - br_r * 2.95 - bw * 1.3 + br_f * 1.1 + sqb * 0.8)
    b_mid = (4.0, -14.2 - br_r * 2.8 - bw * 0.2 + br_f * 0.3 + sqb * 0.6)
    b_out = (12.6, -13.7 - br_r * 2.4 + bw * 0.7 - br_f * 0.4 + sqb * 0.4)
    b_out2 = (14.6, -13.2 - br_r * 2.2 + bw * 0.8 - br_f * 0.3 + sqb * 0.4)
    if sm and side > 0:
        b_mid = (b_mid[0], b_mid[1] - sm * 0.5)
        b_out = (b_out[0], b_out[1] - sm * 0.8)
        b_out2 = (b_out2[0], b_out2[1] - sm * 0.8)
    E.brow = [es(*b_tip), es(*b_in), es(*b_kink), es(*b_mid), es(*b_out), es(*b_out2)]
    E.brow_w = [0.75, 1.55, 1.7, 1.5, 0.95, 0.25]
    # tiny vertical crease above the nose bridge when worried / furrowed
    E.crease_amt = clamp(bw * 1.3 + br_f * 1.0)
    E.brow_crease = [es(-14.6 + br_f * 1.0, -12.0 - bw * 3.0 + br_f * 2.2), es(-15.6 + br_f * 1.2, -8.0 - bw * 1.2),
                     es(-16.0 + br_f * 1.0, -5.0)]
    return E


def _interp_curve(pts, u):
    if u <= pts[0][0]:
        return pts[0][1]
    for i in range(1, len(pts)):
        if u <= pts[i][0]:
            u0, v0 = pts[i - 1]
            u1, v1 = pts[i]
            k = (u - u0) / (u1 - u0) if u1 != u0 else 0
            return v0 + (v1 - v0) * k
    return pts[-1][1]


def _draw_eye_base(c, E, g):
    """Sclera, lid crease, lash line, lit placeholder iris (lit pass)."""
    if not E.visible:
        return
    al = E.alpha
    # lid crease (skin fold) - faint
    if len(E.crease) > 1:
        c.drawPath(_spl(skia.Path(), E.crease), _pt(SKIN_SH2, 0.42 * al, stroke=1.1))
    if E.opening is not None:
        c.drawPath(E.opening, _pt(SCLERA, al))
        c.save()
        c.clipPath(E.opening, skia.ClipOp.kIntersect, True)
        sh = _spl(skia.Path(), [(x, y + 1.6) for (x, y) in E.up])
        c.drawPath(sh, _pt(SCLERA_SH, 0.75 * al, stroke=4.0))
        # dark placeholder iris (the emissive pass paints the real one on top)
        _iris_shape(c, E, g, emissive=False, alpha=al)
        c.restore()
        _lash_line(c, E, _lc(LASH), al)
        lo = E.lo[1:]
        c.drawPath(_spl(skia.Path(), lo), _pt(SKIN_SH2, 0.55 * al, stroke=1.0))
    else:
        # closed: single lid line, slightly curved down
        c.drawPath(_spl(skia.Path(), E.up), _pt(LASH, 0.95 * al, stroke=1.9))


def _lash_line(c, E, color, alpha=1.0):
    pts = E.up
    n = len(pts)
    # u runs inner->outer for both eyes: a fine line that thickens slightly, capped (no eyeliner wing)
    w = [0.45 + 0.55 * math.sin(math.pi * min(1.0, 0.15 + 0.85 * i / (n - 1))) + 0.25 * (i / (n - 1))
         for i in range(n)]
    w[-1] = min(w[-1], 0.5)
    c.drawPath(_tapered(pts, w), paint(color, 0.96 * alpha))


# iris colour stops (inner, mid, outer, dark rim, limbal ring) for teal -> pale gold -> amber.
# Every stop is blended, and the route goes through gold so no frame of the warm-up turns muddy.
_IR_TEAL = ((206, 255, 247), (95, 227, 208), (58, 196, 182), (28, 140, 132), (11, 74, 80))
_IR_GOLD = ((255, 248, 214), (247, 222, 128), (214, 172, 70), (128, 92, 26), (62, 44, 10))
_IR_AMBER = ((255, 230, 176), (246, 162, 74), (200, 116, 42), (122, 62, 18), (74, 36, 8))
_GL_TEAL, _GL_GOLD, _GL_AMBER = (185, 255, 245), (255, 240, 190), (255, 214, 150)
_RING_TEAL, _RING_AMBER = (10, 84, 84), (96, 46, 10)


_IR_PALE = ((252, 255, 246), (226, 246, 228), (200, 214, 188), (132, 136, 112), (66, 64, 48))
_GL_PALE = (245, 255, 240)


def _warm3(a, b, c3, w, pale=None):
    """Colour route a -> (pale, w=0.2) -> b (w=0.5) -> c3 (w=1): the iris flares pale, turns gold,
    then settles amber - never through olive / mint-grey."""
    if pale is not None and w <= 0.2:
        return _mixc(a, pale, smoothstep(w / 0.2))
    if w <= 0.5:
        return _mixc(pale if pale is not None else a, b, smoothstep((w - 0.2) / 0.3 if pale is not None else w / 0.5))
    return _mixc(b, c3, smoothstep((w - 0.5) / 0.5))


def _iris_cols(g, warm):
    """(stops, glow colour, ring colour) for the current warmth."""
    w = clamp(warm)
    if w <= 0.001:
        return _IR_TEAL, _GL_TEAL, _RING_TEAL
    stops = tuple(_warm3(t_, g_, a_, w, p_) for t_, g_, a_, p_ in zip(_IR_TEAL, _IR_GOLD, _IR_AMBER, _IR_PALE))
    return stops, _warm3(_GL_TEAL, _GL_GOLD, _GL_AMBER, w, _GL_PALE), _mixc(_RING_TEAL, _RING_AMBER,
                                                                            smoothstep(w / 0.6))


def _iris_shape(c, E, g, emissive=True, alpha=1.0, warm=0.0, flick=1.0):
    pose = g.pose
    cx, cy = E.iris_c
    r = E.iris_r
    (s_in, s_mid, s_out, s_dk, s_lim), gl, ring = _iris_cols(g, warm)
    glw = clamp(pose.glow)
    proc = clamp(pose.process)
    boost = clamp(0.2 + 0.8 * glw + 0.3 * proc) * flick
    # glow brightens the core and the mid ring; whitening capped so the iris keeps its colour
    inner = _mixc(s_in, (255, 255, 255), min(0.55, 0.15 + 0.4 * boost))
    mid = _mixc(s_mid, s_in, min(0.55, 0.45 * boost))
    outer = _mixc(s_out, s_mid, 0.35 * boost)
    dk = _mixc(s_dk, s_out, 0.25 * boost)
    lim = s_lim
    pup = PUPIL if warm < 0.5 else (34, 16, 4)
    if not emissive:
        inner, mid, outer, dk, lim, gl, ring = (_lc(q) for q in (inner, mid, outer, dk, lim, gl, ring))
        pup = _lc(pup)
    c.save()
    c.translate(cx, cy)
    c.scale(E.kx_i, 1.0)
    sh = skia.GradientShader.MakeRadial((0.0, -0.5), r, [col(inner, alpha), col(mid, alpha), col(outer, alpha),
                                                         col(dk, alpha)], [0.16, 0.5, 0.8, 1.0])
    c.drawCircle(0, 0, r, paint(None, shader=sh))
    c.drawCircle(0, 0, r - 0.45, paint(lim, alpha * 0.9, stroke=0.9))
    # static fine "lens" ring
    c.drawCircle(0, 0, r * 0.64, paint(ring, alpha * 0.28, stroke=0.45))
    if emissive and proc > 0.01:
        # thin dark rotating rings inside the bright iris (contrast survives any glow level)
        t = g.t
        for i, (rr, spd, segs, frac) in enumerate(((0.44, 250.0, 3, 0.55), (0.62, -165.0, 4, 0.5),
                                                   (0.82, 115.0, 6, 0.45))):
            rot = (t * spd * (0.6 + 0.4 * proc)) % 360.0
            rect = skia.Rect(-r * rr, -r * rr, r * rr, r * rr)
            pth = skia.Path()
            for s_ in range(segs):
                pth.addArc(rect, rot + s_ * 360.0 / segs, 360.0 / segs * frac)
            c.drawPath(pth, paint(ring, alpha * proc * 0.78, stroke=0.85 + 0.15 * proc, cap="butt"))
        # one bright tick ring between them: reads as "lens elements" spinning
        rot = (-t * 320.0) % 360.0
        rect = skia.Rect(-r * 0.72, -r * 0.72, r * 0.72, r * 0.72)
        pth = skia.Path()
        for s_ in range(8):
            pth.addArc(rect, rot + s_ * 45.0, 14.0)
        c.drawPath(pth, paint(gl, alpha * proc * 0.55, stroke=0.6, cap="butt"))
    # pupil last (+ thin aperture ring) so gaze always reads
    pr = E.pupil
    c.drawCircle(0, 0.2, pr + 0.6, paint(ring, alpha * 0.55, stroke=0.6))
    c.drawCircle(0, 0.2, pr, paint(pup, alpha))
    # catch-lights
    hl = (255, 255, 255) if emissive else _lc((255, 255, 255))
    c.drawCircle(-2.5, -2.7, 1.55, paint(hl, alpha * 0.95))
    c.drawCircle(2.4, 2.3, 0.7, paint(hl, alpha * 0.6))
    c.restore()


def _draw_eye_emissive(c, E, g, warm, flick, emis):
    if not E.visible or E.opening is None:
        return
    al = E.alpha
    c.save()
    c.clipPath(E.opening, skia.ClipOp.kIntersect, True)
    _iris_shape(c, E, g, emissive=True, alpha=emis * al, warm=warm, flick=flick)
    # lid shadow over the iris top (lit colour)
    sh = _spl(skia.Path(), [(x, y + 1.6) for (x, y) in E.up])
    c.drawPath(sh, paint(_lc(SCLERA_SH), 0.35 * emis * al, stroke=3.2))
    c.restore()
    _lash_line(c, E, _lc(LASH), al)


def _draw_brow(c, E, g):
    if not E.visible:
        return
    al = E.alpha
    c.drawPath(_tapered(E.brow, E.brow_w), _pt(BROW, al))
    if E.crease_amt > 0.02:
        c.drawPath(_spl(skia.Path(), E.brow_crease), _pt(SKIN_SH2, 0.55 * E.crease_amt * al, stroke=0.9))


def _draw_nose(c, g, seam_a):
    P = g.P
    s = P.s

    def np_(x, y, dz):
        return P.p(x, y, _face_z(x, y) + dz)

    t3 = clamp(abs(s) * 2.5)
    sg = 1.0 if s >= 0 else -1.0
    # soft shade on the shadow (-x) flank of the nose, widest at the tip
    flank = [np_(-1.4, 4.0, 4.0), np_(-2.6, 13.0, 6.5), np_(-4.6, 20.5, 8.0), np_(-7.4, 26.0, 2.5),
             np_(-4.0, 28.4, 4.5), np_(-1.0, 22.0, 9.5), np_(-0.2, 12.0, 6.0)]
    c.drawPath(smooth_path(flank, closed=True, tension=0.5), _pt(SKIN_SH, 0.5 + 0.25 * max(0.0, s)))
    # nostril base: a small curl on the shadow side + a short line under the tip
    under = [np_(-7.6, 25.2, 2.0), np_(-6.6, 27.6, 3.0), np_(-3.4, 28.6, 4.5), np_(0.0, 29.0, 6.0),
             np_(3.4, 28.6, 4.5)]
    c.drawPath(_tapered(under, [0.2, 0.75, 0.75, 0.6, 0.15]), _pt(SKIN_SH2, 0.9))
    wing = [np_(6.6, 24.0, 2.5), np_(7.2, 26.6, 2.5), np_(5.2, 28.0, 3.5)]
    c.drawPath(_spl(skia.Path(), wing), _pt(SKIN_SH2, 0.45 * (1.0 - t3 * 0.6), stroke=0.9))
    # bridge / tip highlight on the lit side
    hl = [np_(1.3, 6.0, 5.5), np_(1.5, 14.0, 7.5), np_(1.4, 21.0, 10.0)]
    c.drawPath(_tapered(hl, [0.2, 0.9, 1.4]), _pt(SKIN_HI, 0.85))
    # far-side profile line of the bridge when turned (lower half only, fades in)
    if t3 > 0.02:
        prof = [np_(sg * 1.6, 5.0, 5.0), np_(sg * 2.0, 13.0, 7.0), np_(sg * 1.7, 21.0, 10.0),
                np_(sg * 0.6, 25.6, 8.4), np_(sg * 2.6, 28.4, 4.8)]
        c.drawPath(_tapered(prof, [0.1, 0.55, 0.75, 0.7, 0.2]), _pt(SKIN_SH2, 0.8 * t3))
    # philtrum hint
    ph = [np_(-1.8, 31.5, 3.0), np_(0.0, 34.0, 3.0), np_(1.8, 31.5, 3.0)]
    c.drawPath(_spl(skia.Path(), ph), _pt(SKIN_SH, 0.3, stroke=1.1))


def _draw_mouth(c, g):
    pose = g.pose
    P = g.P
    o = clamp(pose.mouth_open)
    r = clamp(pose.mouth_round)
    sm = clamp(pose.smile, -1, 1)
    sk = clamp(pose.smirk, -1, 1)
    my = 40.0

    def mp(x, y, dz=1.5):
        return P.p(x, my + y, _face_z(x, my + y) + dz)

    w = 14.0 * (1.0 - 0.5 * r * min(1.0, o * 3.0 + 0.3)) * (1.0 - 0.16 * o) + 1.0 * max(sm, 0.0)
    # smirk lifts ONE corner only (+ = Quill's left / local +x)
    dyl = -(sm * 4.2 + max(sk, 0.0) * 3.2)
    dyr = -(sm * 4.2 + max(-sk, 0.0) * 3.2)
    cen = sm * 1.2
    if o < 0.05:
        pts = [mp(-w, dyr), mp(-w * 0.5, cen * 0.8 + 0.3), mp(0, cen + 0.2), mp(w * 0.5, cen * 0.8 + 0.3), mp(w, dyl)]
        ww = [0.35, 1.0, 1.05, 1.0, 0.35]
        c.drawPath(_tapered(pts, ww), _pt(LIPLINE, 0.95))
        # lower lip shade
        ll = [mp(-6.5, 4.6 + cen), mp(0, 5.6 + cen), mp(6.5, 4.6 + cen)]
        c.drawPath(_spl(skia.Path(), ll), _pt(SKIN_SH, 0.5, stroke=1.6))
        if sm > 0.05:
            for sx, dy in ((-1, dyr), (1, dyl)):
                a_ = clamp(sm / 0.3) * 0.5
                cc = [mp(sx * (w + 0.8), dy - 1.6), mp(sx * (w + 1.8), dy + 0.2), mp(sx * (w + 1.2), dy + 1.8)]
                c.drawPath(_spl(skia.Path(), cc), _pt(SKIN_SH2, a_, stroke=0.9))
        return
    h_top = -o * (1.4 + r * 2.4)
    h_bot = o * (10.0 + r * 1.5)
    # corners sit ~40 % down the opening (50 % when round): a calm, deadpan "ah", never a grin
    fr = lerp(0.42, 0.5, r)
    cy0 = h_top + (h_bot - h_top) * fr
    cyr = cy0 + dyr * 0.8
    cyl = cy0 + dyl * 0.8
    sx = 0.62 + 0.2 * r
    # top lip: a soft arch, highest at the centre, curving DOWN into the corners
    tq = lerp(0.55, 0.85, r)
    top = [mp(-w, cyr), mp(-w * sx, lerp(cyr, h_top, tq) + dyr * 0.2), mp(-w * 0.2, h_top + 0.25),
           mp(0, h_top + 0.5 * (1 - r)), mp(w * 0.2, h_top + 0.25),
           mp(w * sx, lerp(cyl, h_top, tq) + dyl * 0.2), mp(w, cyl)]
    bq = lerp(0.72, 0.9, r)
    bot = [mp(w, cyl), mp(w * sx, lerp(cyl, h_bot, bq) + dyl * 0.2), mp(0, h_bot),
           mp(-w * sx, lerp(cyr, h_bot, bq) + dyr * 0.2), mp(-w, cyr)]
    shape = _two_curve_path(top, bot)
    if r > 0.05:
        # pursed lips: a soft rim around the opening
        c.drawPath(shape, _pt(SKIN_SH, 0.45 * r, stroke=4.2))
    c.drawPath(shape, _pt(MOUTH_IN))
    c.save()
    c.clipPath(shape, skia.ClipOp.kIntersect, True)
    if o > 0.12:
        # a narrow strip of upper teeth (<= 2 units)
        th = min(2.0, 0.9 + o * 1.2) * (1.0 - 0.6 * r)
        teeth = [(x, y + th) for (x, y) in top]
        tp = _two_curve_path(top, teeth[::-1])
        c.drawPath(tp, _pt(TEETH, 0.9 * (1.0 - 0.7 * r)))
    if o > 0.3:
        tc = mp(0, h_bot - 1.0)
        c.drawOval(skia.Rect(tc[0] - w * 0.55, tc[1] - 3.8 * o, tc[0] + w * 0.55, tc[1] + 4.0), _pt(TONGUE, 0.8))
    c.restore()
    c.drawPath(_spl(skia.Path(), top), _pt(LIPLINE, 0.9, stroke=1.3))
    c.drawPath(_spl(skia.Path(), bot), _pt(LIPLINE, 0.5, stroke=1.0))
    ll = [mp(-6.0, h_bot + 4.5), mp(0, h_bot + 5.5), mp(6.0, h_bot + 4.5)]
    c.drawPath(_spl(skia.Path(), ll), _pt(SKIN_SH, 0.45, stroke=1.6))


def _draw_seams(c, g, seam_a):
    if seam_a < 0.02:
        return
    P = g.P
    for side in (-1.0, 1.0):
        # temple
        pts3 = [(side * 39.0, -26.0), (side * 41.6, -15.0), (side * 42.6, -5.0), (side * 42.0, 3.0)]
        _draw_surface_curve(c, P, pts3, seam_a * 0.9, 0.9)
        # jaw hinge arc in front of the ear
        pts3 = [(side * 43.0, 13.0), (side * 45.5, 20.0), (side * 43.5, 28.0), (side * 39.0, 33.0)]
        _draw_surface_curve(c, P, pts3, seam_a * 0.9, 1.0)


def _draw_surface_curve(c, P, pts2, alpha, width):
    pts = []
    for (x, y) in pts2:
        a, bf, _ = _slice(y)
        z = _face_z(x, y)
        v = P.nz(x / (a * a), z / (bf * bf))
        if v > 0.05:
            pts.append(P.p(x, y, z + 0.3))
    if len(pts) > 1:
        c.drawPath(_spl(skia.Path(), pts), _pt(SEAM, alpha, stroke=width))


def _ear(g, side):
    """Ear geometry: returns (path, inner_lines, nz) or None."""
    P = g.P
    y0 = 8.0
    a, bf, bb = _slice(y0)
    root = P.p(side * (a - 1.0), y0, -5.0)
    nz = P.nz(side * 1.0, 0.0)          # how much the ear's outer face points at the camera
    nxp = side * P.c                    # screen-x of the ear normal
    o = 1.0 if nxp > 0 else -1.0
    if abs(nxp) < 0.15:
        o = -1.0 if P.s > 0 else 1.0
    w = 6.0 + 9.5 * clamp(abs(nz))
    rx = root[0]
    ry = root[1]
    pts = [(rx, ry - 15.0), (rx + o * w * 0.75, ry - 16.5), (rx + o * w, ry - 8.0), (rx + o * w * 0.92, ry + 3.0),
           (rx + o * w * 0.55, ry + 13.0), (rx + o * 1.5, ry + 15.0), (rx - o * 2.0, ry + 6.0), (rx - o * 2.5, ry - 8.0)]
    path = smooth_path(pts, closed=True, tension=0.5)
    inner = [(rx + o * w * 0.35, ry - 11.0), (rx + o * w * 0.68, ry - 9.5), (rx + o * w * 0.72, ry), (rx + o * w * 0.45, ry + 8.0)]
    return path, inner, nz, o, (rx, ry), w


def _draw_ear(c, g, side, front_face):
    e = _ear(g, side)
    path, inner, nz, o, (rx, ry), w = e
    if front_face:
        _cel(c, path, SKIN, SKIN_SH, (4.0, -2.0))
        a_in = clamp(abs(nz) * 2.5)
        if a_in > 0.02:
            c.drawPath(_spl(skia.Path(), inner), _pt(SKIN_SH2, 0.8 * a_in, stroke=1.4))
            cc = (rx + o * w * 0.38, ry + 1.0)
            c.drawOval(skia.Rect(cc[0] - w * 0.18, cc[1] - 4.0, cc[0] + w * 0.18, cc[1] + 4.0), _pt(SKIN_SH, 0.7 * a_in))
    else:
        _cel(c, path, SKIN_SH, SKIN_SH2, (3.0, -2.0))
        c.drawPath(_spl(skia.Path(), inner[:3]), _pt(SKIN_SH2, 0.5, stroke=1.0))


def _surf_curve(P, pts, lift=1.2, thresh=0.04):
    """Project (beta, y) skull points, return list of visible runs of 2D points."""
    runs, cur = [], []
    for (b, y) in pts:
        x3, y3, z3, n = _surf(b, y, lift)
        if P.nz(*n) > thresh:
            cur.append(P.p(x3, y3, z3))
        else:
            if len(cur) > 1:
                runs.append(cur)
            cur = []
    if len(cur) > 1:
        runs.append(cur)
    return runs


def _taper_w(n, wmax, w0=0.3, w1=0.3):
    if n == 2:
        return [w0 + wmax * 0.5, w1 + wmax * 0.3]
    return [w0] + [wmax * (1.0 - 0.35 * abs((i / (n - 1)) * 2 - 1)) for i in range(1, n - 1)] + [w1]


def _draw_hair(c, g, sil):
    P = g.P
    center_x = P.p(0, -20, 0)[0]
    hp = _hair_path(P, center_x)
    if hp is None:
        return None
    hsil = _hair_outline(P, g.jaw)
    g.hair_sil = hsil
    c.save()
    # hair shadow on the forehead / temples
    c.save()
    c.clipPath(sil, skia.ClipOp.kIntersect, True)
    sh = skia.Path(hp)
    sh.offset(0.8, 3.4)
    c.drawPath(sh, _pt(SKIN_SH, 0.75))
    c.restore()
    c.clipPath(hsil, skia.ClipOp.kIntersect, True)
    c.clipPath(hp, skia.ClipOp.kIntersect, True)
    c.drawPath(hsil, _pt(HAIR))
    # shade crescent on the side away from the light (-x) + under-side
    lit = skia.Path(hsil)
    lit.offset(8.0, -3.5)
    c.save()
    c.clipPath(lit, skia.ClipOp.kDifference, True)
    c.drawPath(hsil, _pt(HAIR_SH, 0.95))
    c.restore()
    _rim_edge(c, hsil)
    # thin cool rim on the lit edge
    rim = skia.Path(hsil)
    rim.offset(-2.2, 1.8)
    c.save()
    c.clipPath(rim, skia.ClipOp.kDifference, True)
    c.drawPath(hsil, _pt(HAIR_HI, 0.75))
    c.restore()
    bv = -P.psi                      # azimuth facing the camera
    # side part on Quill's left, strands combed back away from it
    for run in _surf_curve(P, [(24, -44.0), (25, -51.0), (27, -58.0), (30, -64.0), (35, -69.0)], 1.6):
        c.drawPath(_tapered(run, _taper_w(len(run), 0.9, 0.2, 0.5)), _pt(HAIR_SH, 0.95))
        c.drawPath(_spl(skia.Path(), [(x - 1.6, y) for (x, y) in run]), _pt(HAIR_HI, 0.45, stroke=0.8))
    # main sheen band (crescent on the lit upper-front of the skull)
    for run in _surf_curve(P, [(bv - 22, -63.5), (bv - 4, -68.0), (bv + 14, -69.0), (bv + 32, -66.0),
                               (bv + 48, -59.0), (bv + 60, -49.0)], 2.0, 0.08):
        c.drawPath(_tapered(run, _taper_w(len(run), 3.1, 0.4, 0.3)), _pt(HAIR_HI, 0.85))
    # combed-back strand highlights (front) and grooves
    strands = [(-36.0, 0.55, HAIR_HI), (-20.0, 0.5, HAIR_SH), (-6.0, 0.6, HAIR_HI), (9.0, 0.45, HAIR_SH),
               (40.0, 0.55, HAIR_HI), (52.0, 0.5, HAIR_SH)]
    for b0, al, colr in strands:
        sgn = 1.0 if b0 > 24 else -1.0       # sweep away from the part
        pts = [(b0, -45.5), (b0 + sgn * 3.0, -54.0), (b0 + sgn * 7.0, -62.0), (b0 + sgn * 12.0, -68.0),
               (b0 + sgn * 18.0, -71.5)]
        for run in _surf_curve(P, pts, 2.2, 0.1):
            c.drawPath(_tapered(run, _taper_w(len(run), 0.85, 0.25, 0.15)), _pt(colr, al))
    # back of the head: strands from the crown converging to the nape
    for b0 in (156.0, 174.0, 192.0, 208.0):
        d = (b0 - 180.0)
        pts = [(b0 * 0.9 + 18.0, -70.0), (b0, -58.0), (b0 - d * 0.05, -40.0), (b0 - d * 0.15, -18.0),
               (b0 - d * 0.28, 8.0), (b0 - d * 0.36, 30.0), (b0 - d * 0.4, 42.0)]
        for run in _surf_curve(P, pts, 2.0, 0.1):
            c.drawPath(_tapered(run, _taper_w(len(run), 0.8, 0.2, 0.2)), _pt(HAIR_HI, 0.3))
    c.restore()
    return hp


def _ear_front(P, side):
    """True when the camera sees the front (concha side) of this ear."""
    return P.nz(side * 0.7, 0.7) > 0.0


def _draw_head(c, g, seam_a, sil, part="all"):
    """Draw the head in head coords (caller concatenates M_head). part: "skin" (ears behind, skin,
    face features), "top" (hair, ears in front) or "all". Returns the eye geoms for "skin"/"all"."""
    P = g.P
    ears = [(side, P.nz(side, 0.0)) for side in (-1.0, 1.0)]
    eyes = []
    if part in ("all", "skin"):
        for side, nz in ears:
            if -0.6 < nz <= 0.08:
                _draw_ear(c, g, side, front_face=_ear_front(P, side))
        cut = _back_cut_path(P) if part == "skin" and P.c < -0.02 else None
        if cut is not None:
            # back views: below the jaw-neck line the head tapers into the neck (no chin / jaw wings)
            c.save()
            c.clipPath(cut, skia.ClipOp.kDifference, True)
        _cel(c, sil, SKIN, SKIN_SH, (9.0, -5.5), hi=SKIN_HI, hi_off=(-2.5, 2.5), hi_alpha=0.7)
        if cut is not None:
            c.restore()
        if P.c > -0.4:
            c.save()
            c.clipPath(sil, skia.ClipOp.kIntersect, True)
            eyes = [_eye_geom(g, side) for side in (-1.0, 1.0)]
            for E in eyes:
                if E.visible:
                    sock = [(x, y - 1.0) for (x, y) in E.crease]
                    if len(sock) > 1:
                        c.drawPath(_spl(skia.Path(), sock), _pt(SKIN_SH, 0.22 * E.alpha, stroke=5.0))
            _draw_seams(c, g, seam_a)
            # nose + mouth fade out as the face turns away past profile (lost profile)
            fa = smoothstep((P.c + 0.16) / 0.2)
            if fa > 0.01:
                if fa < 0.99:
                    lp = skia.Paint()
                    lp.setAlphaf(fa)
                    c.saveLayer(sil.getBounds(), lp)
                _draw_nose(c, g, seam_a)
                _draw_mouth(c, g)
                if fa < 0.99:
                    c.restore()
            for E in eyes:
                _draw_eye_base(c, E, g)
                _draw_brow(c, E, g)
            _draw_lost_profile(c, g)
            c.restore()
    if part in ("all", "top"):
        _draw_hair(c, g, sil)
        for side, nz in ears:
            if nz > 0.08:
                _draw_ear(c, g, side, front_face=_ear_front(P, side))
    return eyes


_BACK_CUT = ((90, 23), (105, 27), (120, 32), (135, 37), (150, 41), (165, 44), (180, 45), (195, 44), (210, 41),
             (225, 37), (240, 32), (255, 27), (270, 23))


def _back_cut_path(P):
    """Region below the jaw-neck junction on the back half of the head (head coords), rising into
    place as the head turns past profile so there is no pop at the neck/head order switch."""
    f = smoothstep((-P.c - 0.02) / 0.35)
    pts = []
    for b, y in _BACK_CUT:
        x3, y3, z3, _ = _surf(b, lerp(75.0, y, f), 0.5)
        pts.append(P.p(x3, y3, z3))
    path = skia.Path()
    path.moveTo(pts[0][0], 400.0)
    _spl(path, pts, move=False)
    path.lineTo(pts[-1][0], 400.0)
    path.close()
    return path


def _draw_lost_profile(c, g):
    """Past profile only the cheek contour, the end of the brow and a lash tip are left of the face."""
    P = g.P
    lp = smoothstep((P.c + 0.55) / 0.2) * (1.0 - smoothstep((P.c + 0.02) / 0.12))
    if lp < 0.02:
        return
    sg = 1.0 if P.s >= 0 else -1.0

    def edge(y, inset):
        a, bf, _ = _slice(y)
        R = math.sqrt((a * P.c) ** 2 + (bf * P.s) ** 2)
        return (sg * (R - inset), y * P.ct)

    # cheekbone / cheek plane: a soft shade line just inside the contour
    pts = [edge(y, 4.5 + 2.0 * math.sin((y + 8) / 40 * math.pi)) for y in (-8.0, 2.0, 12.0, 22.0, 32.0)]
    c.drawPath(_spl(skia.Path(), pts), _pt(SKIN_SH, 0.55 * lp, stroke=3.0))
    # brow end: a short thin dash at the brow ridge
    b0, b1 = edge(-14.5, 6.5), edge(-13.0, 0.6)
    c.drawPath(_tapered([b0, ((b0[0] + b1[0]) / 2, (b0[1] + b1[1]) / 2 - 0.4), b1], [0.3, 1.3, 0.9]),
               _pt(BROW, 0.95 * lp))
    # lash tip flicking past the cheek
    l0, l1 = edge(-1.5, 2.6), edge(-3.4, -2.4)
    c.drawPath(_tapered([l0, ((l0[0] + l1[0]) / 2, (l0[1] + l1[1]) / 2 + 0.3), l1], [0.6, 0.55, 0.1]),
               _pt(LASH, 0.95 * lp))


def _draw_neck_head(c, g, seam_a):
    """Neck, collar and head in the right order: chin over the neck while the face looks toward the
    camera, neck over the chin / jaw once the head turns past profile (back views)."""
    P = g.P
    sil = _head_outline(P, g.jaw)
    g.head_sil = sil
    if P.c > -0.02:
        if not g.back_view:
            _draw_collar_back(c, g)
        _draw_neck(c, g, seam_a, head_sil=sil)
        _draw_collar(c, g)
        c.save()
        c.concat(g.M_head)
        g.eyes = _draw_head(c, g, seam_a, sil, "all")
        c.restore()
    else:
        c.save()
        c.concat(g.M_head)
        g.eyes = _draw_head(c, g, seam_a, sil, "skin")
        c.restore()
        _draw_neck(c, g, seam_a)
        _draw_collar(c, g)
        c.save()
        c.concat(g.M_head)
        _draw_head(c, g, seam_a, sil, "top")
        c.restore()


# --------------------------------------------------------------------------- main draw


def _seam_alpha(canvas, pose):
    m = canvas.getTotalMatrix()
    sx = math.hypot(m.getScaleX(), m.getSkewY())
    eff = sx  # includes camera zoom and pose.scale (applied before this call)
    return clamp((eff - 1.05) / 1.6) * 0.5 + 0.1


def _draw_body(c, g, seam_a):
    """Everything that is lit by the scene (goes through the light filter)."""
    arms = g.arms
    al, ar = arms["l"], arms["r"]
    chs = [al, ar]
    # legs (far first)
    legs = sorted([-1.0, 1.0], key=lambda sg: _bdepth(g, sg * 22.0, 0.0))
    if g.back_view:
        behind = [ch for ch in chs if ch.behind >= 0.5]
        # just past profile the clasped hands cross-fade in (no pop at the front/back switch)
        xf = smoothstep((g.psb - 92.0) / 16.0) if g.psb <= 180.0 else 1.0
        if behind and xf < 0.999:
            for ch in behind:
                _draw_arm(c, g, ch, "fore", seam_a)
        c.save()
        c.concat(g.M_leg_rel)
        for sg in legs:
            _draw_leg(c, g, sg)
        c.restore()
        for ch in chs:
            if not ch.near and ch.behind < 0.5:
                _draw_arm(c, g, ch, "all", seam_a)
        _draw_torso(c, g, seam_a)
        _draw_shoulder_stripe(c, g)
        for ch in chs:
            if ch.near and ch.behind < 0.5:
                _draw_arm(c, g, ch, "all", seam_a)
        for ch in behind:
            _draw_arm(c, g, ch, "upper", seam_a)
        if behind and xf > 0.001:
            if xf < 0.999:
                lp = skia.Paint()
                lp.setAlphaf(xf)
                c.saveLayer(None, lp)
            if len(behind) == 2:
                _draw_clasped_hands(c, g, behind, seam_a)
            else:
                _draw_arm(c, g, behind[0], "fore", seam_a)
            if xf < 0.999:
                c.restore()
        _draw_neck_head(c, g, seam_a)
        g.front_arms = []
        return
    # ---- front / three-quarter
    for ch in chs:
        if ch.behind >= 0.5:
            _draw_arm(c, g, ch, "fore", seam_a)
    for ch in chs:
        if not ch.front and ch.behind < 0.5 and ch.across < 0.5:
            _draw_arm(c, g, ch, "all", seam_a)
    for ch in chs:
        if not ch.near and ch.behind >= 0.5:
            _draw_arm(c, g, ch, "upper", seam_a)
    c.save()
    c.concat(g.M_leg_rel)
    for sg in legs:
        _draw_leg(c, g, sg)
    c.restore()
    _draw_torso(c, g, seam_a)
    _draw_insignia(c, g)
    _draw_shoulder_stripe(c, g)
    _draw_neck_head(c, g, seam_a)
    g.front_arms = []                       # arms drawn over the face (they occlude the glowing irises)
    for ch in chs:
        if ch.near and ch.behind >= 0.5:
            _draw_arm(c, g, ch, "upper", seam_a)
    for ch in chs:
        if ch.front and ch.behind < 0.5 and ch.across < 0.5:
            _draw_arm(c, g, ch, "all", seam_a)
            g.front_arms.append(ch)
    for ch in chs:
        if ch.across >= 0.5 and ch.behind < 0.5:
            _draw_arm(c, g, ch, "all", seam_a)
            g.front_arms.append(ch)


def _occluders(g):
    """Paths (upper-body coords) of arms/hands drawn in front of the face, if they reach it."""
    out = []
    hs = skia.Path(g.head_sil)
    hs.transform(g.M_head)
    hb = hs.getBounds()
    for ch in getattr(g, "front_arms", []):
        up, fo = _arm_paths(ch)
        parts = [up, fo]
        kind = ch.hand if ch.hand in _PALM else "relaxed"
        hsil = skia.Path(_hand_geom(kind)[1])
        hsil.transform(_hand_frame(ch))
        parts.append(hsil)
        for q in parts:
            if skia.Rect.Intersects(q.getBounds(), hb):
                out.append(q)
    return out


def _darkness(g):
    """0 in normal interior light .. 1 in the dark symphony lighting (light 0.25..0.55 + tint)."""
    eff = clamp(g.light) * (1.0 - 0.6 * clamp(g.tint_amt))
    return clamp((1.0 - eff) / 0.62)


def _draw_emissive(c, g, t, warm):
    """Irises, process rings, bloom and cheek spill - not darkened by the scene light.
    Order: bloom + spill first (screen), then the irises on top, pupil last, then the lash line,
    so glow never fogs the gaze."""
    eyes = [E for E in getattr(g, "eyes", []) if E.visible and E.opening is not None]
    if not eyes:
        return
    pose = g.pose
    proc = clamp(pose.process)
    flick = 1.0 + proc * (0.07 * noise1(t * 23.0, 5) + 0.03 * math.sin(t * 41.0))
    glw = clamp(pose.glow)
    dk = _darkness(g)
    emis = clamp(0.4 + 0.6 * glw + 0.6 * dk + 0.4 * proc)
    if g.light >= 0.999 and g.tint_amt <= 0.001:
        emis = 1.0
    (_, s_mid, _, _, _), gl, _ = _iris_cols(g, warm)
    c.save()
    for q in _occluders(g):
        c.clipPath(q, skia.ClipOp.kDifference, True)
    c.concat(g.M_head)
    # bloom: soft in normal light (~40 %), fuller in the dark
    scale_b = 0.4 + 0.6 * dk
    strength = clamp(0.7 * glw + 0.3 * proc + dk * (0.3 + 0.35 * glw)) * scale_b
    if strength > 0.01:
        rad = (10.0 + 13.0 * glw) * (0.8 + 0.25 * dk)
        for E in eyes:
            open_k = clamp(E.gap / 8.0) * E.alpha
            cx, cy = E.iris_c
            a = strength * open_k * flick
            c.save()
            c.translate(cx, cy)
            c.scale(max(0.45, E.kx_i) * 1.12, 0.8)
            if dk < 0.6:
                # bright surroundings: a soft coloured halo (screen would only grey the pale skin)
                glow(c, 0.0, 0.0, rad, s_mid, 0.5 * a * (1.0 - dk / 0.6), blend=None)
            glow(c, 0.0, 0.0, rad, s_mid, 0.62 * a * min(1.0, dk / 0.6 + 0.35), blend="screen")
            glow(c, 0.0, 0.0, 7.0 + 5.0 * glw, gl, 0.75 * a * (0.3 + 0.7 * glw), blend="screen")
            c.restore()
    # light spill on the cheeks at high glow
    if glw > 0.3:
        c.save()
        c.clipPath(g.head_sil, skia.ClipOp.kIntersect, True)
        for E in eyes:
            cx, cy = E.iris_c
            amt = clamp((glw - 0.3) / 0.7) * clamp(E.gap / 8.0) * E.alpha * (0.55 + 0.45 * dk)
            c.save()
            c.translate(cx, cy + 13.0)
            c.scale(1.3 * max(0.4, E.kx_i), 0.7)
            glow(c, 0.0, 0.0, 20.0, s_mid, 0.2 * amt, blend="screen")
            c.restore()
        c.restore()
    # irises clipped to the head silhouette (the far eye never pokes past the cheek contour)
    c.clipPath(g.head_sil, skia.ClipOp.kIntersect, True)
    for E in eyes:
        _draw_eye_emissive(c, E, g, warm, flick, emis)
    c.restore()


def _local_bounds(g, pad=40.0):
    xs = [-95.0, 95.0]
    ys = [-800.0, 12.0]
    for ch in g.arms.values():
        for q in (ch.S, ch.E, ch.W):
            xs.append(q[0])
            ys.append(q[1])
    r = skia.Rect(min(xs) - 75.0 - pad, min(ys) - 75.0 - pad, max(xs) + 75.0 + pad, max(ys) + pad)
    if abs(g.pose.lean) > 0.01 or abs(g.pose.bounce) > 0.01:
        r = g.M_upper.mapRect(r)
        r.join(skia.Rect(-120 - pad, -800 - pad, 120 + pad, 12 + pad))
    return r


def _alpha_cf(a):
    return skia.ColorFilters.Matrix([1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, clamp(a), 0])


def _glow_paths(g):
    """Rough silhouette (body-upper coords) for the soft rim-light halo."""
    ps = [_torso_path(g)]
    for ch in g.arms.values():
        up, fo = _arm_paths(ch)
        ps += [up, fo]
        f = _dir(ch.ah)
        ps.append(_capsule(ch.W, (ch.W[0] + f[0] * 40.0, ch.W[1] + f[1] * 40.0), 10.0, 7.0))
    hs = _hair_outline(g.P, g.jaw)
    hs.transform(g.M_head)
    ps.append(hs)
    for sg in (-1.0, 1.0):
        hip = _bp(g, sg * 24.0, _HIP_Y, 0.0)
        ps.append(_capsule(hip, (sg * 21.0 * g.cb, -20.0), 22.0, 14.0))
    neck, _ = _neck_geom(g)
    ps.append(neck)
    return _union(ps)


def draw(canvas: skia.Canvas, pose: Pose, t: float, warm: float | None = None) -> None:
    """Draw Quill. canvas is in stage coords (camera already applied).

    warm: 0..1 shifts the iris glow from teal toward amber (the closing smile). None = automatic
          (warms with smile * glow, so the "tiny rare smile" preset glows amber by itself).
    """
    global _LT, _RIM
    g = _layout(pose, t)
    if warm is None:
        warm = clamp((pose.smile - 0.1) / 0.2) * clamp(pose.glow / 0.5) * 0.75
    _LT = (float(pose.light), float(clamp(pose.tint_amt)), tuple(float(v) for v in pose.tint))
    rim = clamp(pose.rim)
    rc = rgb(pose.rim_color) if isinstance(pose.rim_color, str) else tuple(pose.rim_color)[:3]
    _RIM = (rc, min(1.0, rim * 1.25), 2.0) if rim > 0.001 else None
    canvas.save()
    try:
        canvas.concat(g.M_stage)
        seam_a = _seam_alpha(canvas, pose)
        canvas.save()
        canvas.concat(g.M_upper)
        if rim > 0.001:
            canvas.drawPath(_glow_paths(g), paint(rc, 0.55 * rim, blur=9.0, blend="screen"))
        _draw_body(canvas, g, seam_a)
        _draw_emissive(canvas, g, t, warm)
        canvas.restore()
    finally:
        canvas.restore()
        _LT = (1.0, 0.0, (0.0, 0.0, 0.0))
        _RIM = None
