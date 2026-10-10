"""QUILL - the ship's android. Full character rig (BIBLE section 2, contract in anim/rig.py).

Public API
    draw(canvas, pose, t, warm=None)   draw Quill; canvas already in stage coords (camera applied).
                                       warm 0..1 (None = 0): the closing-smile eye warmth - a gold
                                       ring blooms around the pupils and the bloom / catch-lights turn
                                       amber while the irises stay teal. Only set it explicitly (S5).
    head_center(pose) -> (x, y)        stage coords between the eyes (exact for every pose field)
    hand_pos(pose, side) -> (x, y)     stage coords of the palm centre ("l" / "r" = Quill's own side);
                                       for "palm_up" it is the centre of the upturned palm (props hover
                                       above it)
    ARMS                               rest, behind_back, raise_conduct, present, gesture_small, send
    HEIGHT                             770 stage units at scale 1
    EXPRESSIONS, expression(name, **overrides) -> dict of Pose kwargs (face presets)

Conventions
    * facing=-1 is a pure mirror image of facing=+1 (insignia on his left chest, closure seam and
      teal stripe on his right; arm_r is the near arm once he is turned toward `facing`).
    * look_x is screen space (+ = screen-right).
    * pose.back blends the yaw continuously (0.25..0.75): 0 front, 0.5 profile, >= 0.75 full back;
      animating back 1 -> 0 is a real, pop-free turn through profile (arms included).

Construction notes
    * The head is a small 3D model: horizontal elliptical slices (half-width a, front depth bf,
      back depth bb) rotated by a yaw angle and a small pitch (head_nod), then projected
      orthographically. Silhouette, hairline, ears, eyes, brows, nose and mouth are projected
      points, so turn / head_turn / back / head_nod stay coherent from front through profile to back.
    * The torso uses the same slice idea. Hands behind the back are a 3D IK (elbows back and out)
      projected with the body yaw. Free gestures are a true 3D pose near the flat front/back views
      and the classic picture-plane cheat (swing toward the facing side) from three-quarter on; in
      between the hand target is interpolated around the shoulder and the elbow re-solved, so no
      turn ever sweeps an arm through the body.
    * Cel shading: one shade crescent (shape minus shifted shape, via PathOps) + a thin lit edge +
      a thin dark contour (same line weight convention as Rae's rig).
    * pose.light / tint / tint_amt are applied per colour (same maths as core.light_filter, no
      offscreen layer). pose.rim (same recipe as Rae's): a soft two-radius glow of the silhouette
      under the body + a thin bright edge on the OUTER silhouette only (screen-left / top), built
      from the union of the drawn shapes.
    * Irises, process rings and bloom are emissive: drawn unlit after the body so they glow in the
      dark, clipped by any arm that passes in front of the face. In normal light the glow is a
      saturated teal tint + additive lift around the eyes so the "done" flash reads on pale skin.
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
# thin dark contours (same line convention as Rae's rig: ~1.2-1.6 stage units, slightly transparent)
SKIN_LINE, HAIR_LINE, PANTS_LINE, BOOT_LINE, COLLAR_LINE = "#56627A", "#0A0E18", "#0E111A", "#050608", "#127068"

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
    "concern": {"brow_worry": 0.3, "look_y": 0.6, "head_nod": -0.25, "smile": -0.2, "squint": 0.1},
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
_LT = (1.0, 0.0, (0.0, 0.0, 0.0))
#   _SIL = list of silhouette paths (in the coords of the canvas _draw_body starts in) collected while
#          drawing, only when a rim light is requested (None = not collecting)
_SIL = None


def _sil_add(c, path, m=None):
    """Record `path` (drawn on canvas c, optionally under extra matrix m) as part of the outer
    silhouette for the rim light. No-op unless draw() is collecting."""
    if _SIL is None or path is None:
        return
    q = skia.Path(path)
    tm = c.getTotalMatrix()
    if m is not None:
        tm = skia.Matrix.Concat(tm, m)
    if not tm.isIdentity():
        q.transform(tm)
    _SIL.append(q)


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


def _minus_shifted(path, off):
    """path minus (path shifted by off): the crescent on the side opposite `off`."""
    sh = skia.Path(path)
    sh.offset(off[0], off[1])
    return skia.Op(path, sh, skia.PathOp.kDifference_PathOp)


def _cel(c, path, base, shade, off, hi=None, hi_off=None, hi_alpha=1.0, shade_alpha=1.0, sil=True,
         line=None, line_w=1.3, line_a=0.85):
    """Fill path with base colour, shade crescent on the side opposite `off`, optional rim
    highlight crescent on the side opposite `hi_off`, optional thin contour `line`.
    (PathOps: much cheaper than AA clips.) sil: also record the path for the rim-light silhouette."""
    if sil:
        _sil_add(c, path)
    c.drawPath(path, _pt(base))
    r = _minus_shifted(path, off)
    if r is not None:
        c.drawPath(r, _pt(shade, shade_alpha))
    if hi is not None and hi_off is not None:
        r = _minus_shifted(path, hi_off)
        if r is not None:
            c.drawPath(r, _pt(hi, hi_alpha))
    if line is not None:
        c.drawPath(path, _pt(line, line_a, stroke=line_w))


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


def _p2(g, p):
    """Body 3D point (x = Quill's left, y down, z = forward/chest side) -> body-local 2D."""
    return (p[0] * g.cb + p[2] * g.sb, p[1])


def _ik3(S, T, l1, l2, pole):
    """3D two-bone IK: elbow on the side of `pole` (direction) - continuous for any view."""
    d = [T[i] - S[i] for i in range(3)]
    dist = math.sqrt(sum(v * v for v in d)) or 1e-6
    u = [v / dist for v in d]
    dc = clamp(dist, abs(l1 - l2) + 0.5, l1 + l2 - 0.5)
    a = (l1 * l1 + dc * dc - l2 * l2) / (2.0 * dc)
    h = math.sqrt(max(0.0, l1 * l1 - a * a))
    pd = sum(pole[i] * u[i] for i in range(3))
    pp = [pole[i] - u[i] * pd for i in range(3)]
    pn = math.sqrt(sum(v * v for v in pp)) or 1e-6
    E = tuple(S[i] + u[i] * a + pp[i] / pn * h for i in range(3))
    W = tuple(S[i] + u[i] * dc for i in range(3))
    return E, W


def _fore_azimuth(phi):
    """Front-view forearm azimuth (deg, + = outward, - = toward the midline) for a forearm raised
    `phi` deg from hanging: hangs slightly out, offers forward/inward at waist height, opens out
    again when raised high."""
    return 10.0 - 32.0 * smoothstep((phi - 35.0) / 40.0) + 44.0 * smoothstep((phi - 110.0) / 40.0)


def _arm_chain(g, side):
    """Solve one arm (body-local 2D joints S, E, W + drawing hints).

    Free arms: a true 3D pose (raised forward-outward, projected with the body yaw) near the flat
    front / back views, the classic picture-plane cheat (gesture swings toward the facing direction)
    from three-quarter on; in between the HAND TARGET is interpolated and the elbow re-solved by IK,
    so turning while gesturing never sweeps the arm through the body.
    behind > 0: a 3D IK to the small of the back (elbows back and out), projected - continuous from
    the front view through profile to the back view."""
    pose = g.pose
    ap = pose.arm_l if side == "l" else pose.arm_r
    sig = 1.0 if side == "l" else -1.0           # character's left lives on local +x (front view)
    z_sh = _bdepth(g, sig * _SHOULDER_X, 0.0)
    farness = smoothstep(-z_sh / 22.0)           # 0 at the front view .. 1 for the far arm at 3/4
    # the far shoulder tucks slightly behind the chest (front views) / behind the back (back views)
    S3 = (sig * _SHOULDER_X, g.sh_y + 2.0 * farness, -9.0 * farness * clamp(g.cb / 0.3, -1.0, 1.0))
    S = _p2(g, S3)
    near = z_sh > 0.5 or (abs(z_sh) <= 0.5 and sig < 0)
    out = 1.0 if S[0] > 0.01 else (-1.0 if S[0] < -0.01 else sig)
    # three-quarter-ness measured from the nearest flat view (front OR back)
    turn_eff = min(abs(g.psb), abs(180.0 - g.psb)) / TURN_DEG
    k = smoothstep((turn_eff - 0.03) / 0.25)
    fdir = 1.0 if g.sb >= 0.0 else -1.0          # screen-local direction the face points
    th = ap.shoulder
    if pose.walk is not None and ap.behind < 0.5 and ap.across < 0.5:
        # arms swing opposite to the same-side leg
        th += 12.0 * math.sin(2.0 * math.pi * pose.walk + (math.pi if sig > 0 else 0.0)) * (1.0 - clamp(th / 40.0))
    # --- free arm, picture-plane cheat (three-quarter views)
    ur = _rad(th)
    E34 = (S[0] + _L_UP * fdir * math.sin(ur), S[1] + _L_UP * math.cos(ur))
    af34 = th * fdir + fdir * ap.elbow
    d34 = _dir(af34)
    W34 = (E34[0] + _L_FORE * d34[0], E34[1] + _L_FORE * d34[1])
    # --- free arm, true 3D (front / back views): upper arm raised forward-outward, forearm azimuth
    # depends on how high it is raised (see _fore_azimuth)
    au_az = _rad(30.0)
    du = (sig * math.sin(ur) * math.sin(au_az), math.cos(ur), math.sin(ur) * math.cos(au_az))
    E3 = tuple(S3[i] + _L_UP * du[i] for i in range(3))
    phi = th + ap.elbow
    pr, fz = _rad(phi), _rad(_fore_azimuth(phi))
    df = (sig * math.sin(pr) * math.sin(fz), math.cos(pr), math.sin(pr) * math.cos(fz))
    W3 = tuple(E3[i] + _L_FORE * df[i] for i in range(3))
    Ef, Wf = _p2(g, E3), _p2(g, W3)
    if k >= 0.999:
        E, W = E34, W34
    elif k <= 0.001:
        E, W = Ef, Wf
    else:
        # polar interpolation of the hand around the shoulder: raised gestures arc over the top,
        # lower ones swing under, in front of the chest - never straight across the face
        v0 = (Wf[0] - S[0], Wf[1] - S[1])
        v1 = (W34[0] - S[0], W34[1] - S[1])
        a0, a1 = _ang(v0), _ang(v1)
        dlt = _wrap180(a1 - a0)
        if abs(dlt) > 90.0:
            via_up = abs(_wrap180(a0 + dlt * 0.5)) > 90.0
            want_up = (v0[1] + v1[1]) * 0.5 < -60.0
            if via_up != want_up:
                dlt -= 360.0 * (1.0 if dlt > 0 else -1.0)
        a = a0 + dlt * k
        rr = lerp(math.hypot(*v0), math.hypot(*v1), k)
        dd = _dir(a)
        T = (S[0] + rr * dd[0], S[1] + rr * dd[1])
        gp = ((S[0] + T[0]) * 0.5 + out * 20.0, (S[1] + T[1]) * 0.5 + 50.0)
        l1 = lerp(math.hypot(Ef[0] - S[0], Ef[1] - S[1]), _L_UP, k)
        l2 = lerp(math.hypot(Wf[0] - Ef[0], Wf[1] - Ef[1]), _L_FORE, k)
        E, W = _ik(S, T, max(l1, 20.0), max(l2, 20.0), gp)
    # how much the arm reaches forward (toward the camera in front views, away from it from behind)
    fwd = (1.0 - k) * smoothstep((max(th, 0.6 * phi) - 20.0) / 45.0)
    # --- across: hand toward the opposite side of the chest
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
        # hands clasped at the small of the back (3D), elbows back and out
        _, _, bb = _torso_slice(-414.0)
        T3 = (sig * 7.0, -414.0, -bb - 9.0)
        E3b, W3b = _ik3(S3, T3, _L_UP, _L_FORE, (sig * 0.75, 0.3, -1.0))
        Eb, Wb = _p2(g, E3b), _p2(g, W3b)
        if beh >= 1.0:
            E, W = Eb, Wb
        else:
            # transition: the hand travels around the OUTSIDE of the hip on this arm's side
            # (waypoint just past the silhouette), elbow out; from the waypoint the arm swings to the
            # free pose by interpolating joint angles (lengths preserved, no IK elbow flips)
            pw = _p2(g, (sig * (_torso_slice(-440.0)[0] + 24.0), -440.0, -4.0))
            side_gp = _p2(g, (sig * (_SHOULDER_X + 52.0), g.sh_y + 92.0, -20.0))
            l1b, l2b = math.hypot(Eb[0] - S[0], Eb[1] - S[1]), math.hypot(Wb[0] - Eb[0], Wb[1] - Eb[1])
            lw2 = math.hypot(pw[0] - S[0], pw[1] - S[1])
            if beh >= 0.5:
                u = (beh - 0.5) / 0.5
                T = (lerp(pw[0], Wb[0], u), lerp(pw[1], Wb[1], u))
                gq = (lerp(side_gp[0], Eb[0], u), lerp(side_gp[1], Eb[1], u))
                E, W = _ik(S, T, lerp(_L_UP, l1b, u), lerp(_L_FORE * 0.92, l2b, u), gq)
            else:
                Em, Wm = _ik(S, pw, _L_UP, max(_L_FORE * 0.92, lw2 - _L_UP + 1.0), side_gp)
                u = beh / 0.5
                au0 = _ang((E[0] - S[0], E[1] - S[1]))
                af0 = _ang((W[0] - E[0], W[1] - E[1]))
                aum = _ang((Em[0] - S[0], Em[1] - S[1]))
                afm = _ang((Wm[0] - Em[0], Wm[1] - Em[1]))
                lu = lerp(math.hypot(E[0] - S[0], E[1] - S[1]), math.hypot(Em[0] - S[0], Em[1] - S[1]), u)
                lf = lerp(math.hypot(W[0] - E[0], W[1] - E[1]), math.hypot(Wm[0] - Em[0], Wm[1] - Em[1]), u)
                au_ = au0 + _wrap180(aum - au0) * u
                af_ = af0 + _wrap180(afm - af0) * u
                du_, df_ = _dir(au_), _dir(af_)
                E = (S[0] + lu * du_[0], S[1] + lu * du_[1])
                W = (E[0] + lf * df_[0], E[1] + lf * df_[1])
    af = _ang((W[0] - E[0], W[1] - E[1])) if math.hypot(W[0] - E[0], W[1] - E[1]) > 1e-3 else 0.0
    ah = af + ap.wrist * lerp(-sig, fdir, k)
    # thumb side: toward the body midline in flat views (mirrored from behind), forward in 3/4.
    # Passing through 0 the hand would flip: squash it (min 30 % width) instead of popping.
    tf = -sig if g.cb >= 0.0 else sig
    tv = lerp(tf, fdir, k)
    thumb = (1.0 if tv >= 0.0 else -1.0) * max(0.3, abs(tv))
    ch = _G()
    ch.side, ch.sig, ch.S, ch.E, ch.W, ch.ah, ch.af = side, sig, S, E, W, ah, af
    ch.near, ch.out, ch.thumb, ch.hand, ch.across, ch.behind = near, out, thumb, ap.hand, acr, beh
    ch.k = k
    ch.fwd = fwd
    ch.r_sh = 16.5 - 3.0 * farness
    # drawn in front of the torso? front views: the near arm, or any arm reaching toward the camera;
    # back views: the near arm unless it reaches forward (= away from the camera, behind the body)
    if g.cb >= 0.0:
        ch.front = (near or fwd > 0.5) and beh < 0.5
    else:
        ch.front = near and fwd <= 0.5 and beh < 0.5
    return ch


def _hand_frame(ch):
    f = _dir(ch.ah)
    k = _HAND_SCALE
    X = (f[1] * ch.thumb * k, -f[0] * ch.thumb * k)       # |thumb| < 1 squashes a turning hand
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
    _cel(c, p, PANTS, PANTS_SH, (7.0, -4.0), hi="#2B3244", hi_off=(-2.5, 0.0), hi_alpha=0.9, line=PANTS_LINE,
         line_w=1.4)
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
    # three-quarter / profile: foot pointing toward the facing side
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
        front = [(x - 12.5, y0 - 46), (x + 12.5, y0 - 46), (x + 14.6, y0 - 20), (x + 15.2, y0 - 7),
                 (x + 13.0, y0 + 0.5), (x - 13.0, y0 + 0.5), (x - 15.2, y0 - 7), (x - 14.6, y0 - 20)]
    else:
        # flat front view: the toe box comes toward the camera - wider than the ankle, a rounded
        # dome below the trouser hem, toes splayed slightly outward
        o = 1.0 if x >= 0 else -1.0
        front = [(x - 12.0, y0 - 46), (x + 12.0, y0 - 46), (x + 15.4 + o * 0.8, y0 - 22),
                 (x + 18.0 + o * 2.4, y0 - 11), (x + 17.4 + o * 3.0, y0 - 3.0), (x + 14.0 + o * 2.8, y0 + 0.8),
                 (x - 14.0 + o * 2.8, y0 + 0.8), (x - 17.0 + o * 2.2, y0 - 5.0), (x - 15.4 + o * 0.8, y0 - 22)]
    wf = 1.0 - smoothstep(s / 0.4)
    if wf > 0.0:
        pts = [(lerp(px, fx, wf), lerp(py, fy, wf)) for (px, py), (fx, fy) in zip(pts, front)]
    p = smooth_path(pts, closed=True, tension=0.42)
    _cel(c, p, BOOT, "#08090D", (6.0, -3.0), hi=BOOT_HI, hi_off=(-2.0, 2.5), hi_alpha=0.8, line=BOOT_LINE, line_w=1.4)
    if wf > 0.05 and not g.back_view:
        # toe-cap highlight (front view)
        o = 1.0 if x >= 0 else -1.0
        c.drawPath(_spl(skia.Path(), [(x - 7.0 + o * 2.0, y0 - 11.0), (x + o * 2.0, y0 - 13.0), (x + 7.0 + o * 2.0, y0 - 11.0)]),
                   _pt(BOOT_HI, 0.55 * wf, stroke=1.6))
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
    # |cos|: from behind (cos < 0) the shoulder line must not swap sides (the contour would cross
    # itself into a bow-tie across the shoulders)
    top_r = [(x * abs(cc), y) for (x, y) in sh_pts]
    top_l = [(-x * abs(cc), y) for (x, y) in sh_pts]
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
    _cel(c, p, UNI, UNI_SH, (11.0, -5.0), hi=UNI_HI, hi_off=(-3.0, 3.5), hi_alpha=0.95, line=UNI_LINE, line_w=1.4,
         line_a=0.9)
    c.save()
    c.clipPath(p, skia.ClipOp.kIntersect, True)
    if not g.back_view:
        # asymmetric closure seam on his right front (local -x; the whole rig is a pure mirror for
        # facing -1, so it stays on his physical right, opposite the insignia) + matching piping
        pts = []
        for (x, y) in ((-12.0, -606.0), (-20.0, -560.0), (-24.0, -515.0), (-24.0, -470.0), (-23.0, -410.0),
                       (-22.0, -370.0)):
            a, bf, _ = _torso_slice(y)
            q, v = _front_pt(g, x, y, a, bf)
            pts.append(q)
        c.drawPath(_spl(skia.Path(), pts), _pt(UNI_LINE, 0.95, stroke=2.0))
        c.drawPath(_spl(skia.Path(), [(q[0] + 2.2, q[1]) for q in pts]), _pt(UNI_HI, 0.5, stroke=1.0))
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
    # on his physical LEFT chest (local +x) for both facings - the rig is a pure mirror image for
    # facing -1, so it is always on the opposite side from the shoulder stripe and closure seam.
    # The emblem itself is never drawn mirrored (it reads the same way round on screen).
    y = -548.0
    a, bf, _ = _torso_slice(y)
    q, v = _front_pt(g, 32.0, y, a, bf)
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
    side_off = lerp(9.5, 2.0, ch.k) if g.cb >= 0.0 else lerp(9.5, 4.0, ch.k)
    sgn = 1.0 if (nx * o) > 0 else -1.0
    if ch.k > 0.5 and g.cb >= 0.0:
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
        # open palm offered upward, seen from slightly above: palm plane foreshortened (narrow in x),
        # fingers forward with the tips curling gently up (+x = screen-up / far side), thumb on the
        # near side (-x) pointing forward. Same length as the open hand (fingertips at y ~ 49).
        ("blob", [(-6.6, -1.0), (5.2, -1.0), (7.0, 8.0), (7.6, 18.0), (7.4, 26.0), (2.0, 28.6), (-4.2, 28.6),
                  (-8.4, 24.0), (-9.0, 14.0), (-8.4, 5.0)]),
        ("chain", [(5.0, 25.0), (5.6, 33.4), (6.6, 39.4), (8.2, 42.4)], 2.6, 2.2),
        ("chain", [(1.8, 26.4), (2.2, 37.0), (3.2, 44.4), (5.2, 47.6)], 3.0, 2.5),
        ("chain", [(-1.6, 27.0), (-1.6, 38.0), (-0.6, 46.0), (1.6, 50.0)], 3.2, 2.7),
        ("blobhi", [(-5.0, 4.0), (3.6, 3.6), (5.0, 11.0), (4.8, 20.0), (0.6, 23.4), (-5.0, 22.0), (-6.4, 12.0)]),
        ("chain", [(-5.0, 26.0), (-5.4, 36.0), (-4.6, 44.0), (-2.6, 48.4)], 3.1, 2.6),
        ("chain", [(-6.4, 4.0), (-10.8, 12.0), (-12.4, 20.0), (-11.6, 27.6)], 4.1, 2.8),
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
# back of a relaxed hanging hand (back view / held hand of the clasp): broad, fingers together
_HAND_PARTS["relaxed_back"] = [
    ("chain", [(-8.0, 6.0), (-11.4, 13.0), (-12.0, 20.0)], 3.6, 2.8),
    ("blob", [(-9.6, -1.0), (-10.4, 10.0), (-10.4, 22.0), (-9.4, 32.0), (-6.6, 40.0), (-2.6, 44.6), (1.6, 45.4),
              (5.6, 42.6), (8.2, 36.0), (9.4, 26.0), (9.6, 14.0), (8.8, -1.0)]),
]
_HAND_LINES = {
    "relaxed": [([(-8.2, 30.6), (-3.6, 34.4), (2.2, 37.0)], 0.6), ([(-1.4, 38.0), (1.0, 43.0)], 0.35)],
    "open": [([(-4.0, 9.0), (0.5, 15.0), (6.0, 18.0)], 0.3), ([(-8.0, 20.0), (-2.0, 22.0)], 0.25)],
    "palm_out": [([(-4.0, 9.0), (0.5, 15.0), (6.0, 18.0)], 0.4), ([(-8.0, 19.0), (-1.0, 21.0), (4.0, 19.5)], 0.35)],
    "palm_up": [([(6.0, 16.0), (1.0, 19.0), (-5.0, 18.0)], 0.32), ([(-5.6, 5.0), (-4.6, 11.0), (-4.8, 17.0)], 0.28),
                ([(-0.2, 30.0), (-0.4, 37.0)], 0.2), ([(3.4, 30.0), (3.8, 37.0)], 0.2)],
    "point": [([(-9.0, 18.5), (-3.0, 21.0), (3.0, 21.0)], 0.4), ([(-8.0, 25.5), (-2.0, 27.5), (4.0, 26.5)], 0.35)],
    "fist": [([(-9.0, 17.5), (-3.0, 20.0), (4.0, 19.5)], 0.45), ([(-8.0, 24.5), (-2.0, 26.5), (4.5, 25.5)], 0.4)],
}
_HAND_LINES["hold"] = _HAND_LINES["fist"]
_HAND_LINES["relaxed_back"] = [([(-4.6, 28.0), (-4.4, 38.0)], 0.35), ([(0.2, 29.0), (0.4, 41.5)], 0.35),
                               ([(4.6, 28.0), (4.4, 37.0)], 0.35), ([(-8.0, 23.0), (0.0, 25.0), (8.0, 23.0)], 0.15)]
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
    kind = ch.hand if ch.hand in _HAND_PARTS else "relaxed"
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
    outline = _pt(SKIN_LINE, 0.7, stroke=1.0)
    _sil_add(c, sil)
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
    for pts, a in lines:
        c.drawPath(_spl(skia.Path(), pts), _pt(SKIN_SH2, a + 0.2, stroke=0.9))
    if seam_a > 0.02:
        c.drawLine(-8.5, 3.5, 8.0, 3.5, _pt(SEAM, seam_a * 0.8, stroke=0.8))
    c.restore()


# Holding hand of the back-view clasp, in a local frame: origin = the HELD wrist, +u toward the far
# side (from the holding wrist to the held wrist), +v down. Back of the hand + four curled fingers
# wrapping the held wrist (we see their backs and knuckles).
_CLASP_BACK = [(-18.0, -6.4), (-9.0, -8.8), (0.0, -10.2), (7.0, -10.4), (10.6, -8.2), (11.8, -3.0),
               (11.8, 3.0), (10.6, 8.2), (7.0, 10.2), (0.0, 9.8), (-9.0, 8.2), (-18.0, 6.0)]
_CLASP_FINGERS = [  # (points, r0, r1) each finger curls over the held wrist's far edge and down
    ([(10.0, -7.2), (15.0, -6.6), (17.6, -3.6), (17.2, 0.2)], 3.0, 2.5),
    ([(10.8, -2.4), (16.0, -1.2), (18.0, 2.4), (17.0, 6.0)], 3.2, 2.6),
    ([(10.8, 2.6), (15.4, 4.0), (16.6, 7.6), (15.0, 10.6)], 3.0, 2.5),
    ([(9.8, 7.0), (13.4, 8.6), (13.8, 11.6), (12.0, 13.8)], 2.6, 2.2),
]
_CLASP_CACHE = {}


def _clasp_geom():
    if "g" not in _CLASP_CACHE:
        back = smooth_path(_CLASP_BACK, closed=True)
        fingers = [_chain(pts, r0, r1) for pts, r0, r1 in _CLASP_FINGERS]
        _CLASP_CACHE["g"] = (back, fingers, _union([back] + fingers))
    return _CLASP_CACHE["g"]


def _draw_clasped_hands(c, g, chs, seam_a):
    """Hands clasped at the small of the back, seen from behind: the far hand hangs relaxed (back of
    the hand toward us), the near hand wraps across its wrist with curled fingers."""
    order = sorted(chs, key=lambda ch: ch.near)
    held, hold = order[0], order[1]
    for ch in order:
        _draw_arm(c, g, ch, "fore", seam_a, hand=False)
    du, dv = held.W[0] - hold.W[0], held.W[1] - hold.W[1]
    d = math.hypot(du, dv)
    side = 1.0 if (du if abs(du) > 1e-3 else -hold.out) > 0 else -1.0
    # compress across as the view turns away from straight-behind
    kx = clamp(abs(g.cb), 0.35, 1.0)
    # held hand: hangs down, fingers drifting slightly toward the holding side
    h2 = _G()
    h2.__dict__.update(held.__dict__)
    h2.ah = -12.0 * side
    h2.hand = "relaxed_back"
    h2.thumb = -side * kx
    _draw_hand(c, g, h2, seam_a)
    # holding hand: local frame at the held wrist, +u toward the far side
    ang = math.atan2(dv, du) if d > 3.0 else (0.0 if side > 0 else math.pi)
    ang = clamp(ang, -0.5, 0.5) if side > 0 else (math.pi + clamp(_wrap180(math.degrees(ang) - 180.0) / 57.3, -0.5, 0.5))
    ex = (math.cos(ang), math.sin(ang))
    ey = (-ex[1], ex[0]) if ex[0] >= 0 else (ex[1], -ex[0])
    s_ = _HAND_SCALE
    m = skia.Matrix.MakeAll(ex[0] * kx * s_, ey[0] * s_, held.W[0] + 1.5 * side,
                            ex[1] * kx * s_, ey[1] * s_, held.W[1] + 2.0, 0, 0, 1)
    back, fingers, sil = _clasp_geom()
    c.save()
    c.concat(m)
    _sil_add(c, sil)
    outline = _pt(SKIN_LINE, 0.7, stroke=1.0)
    for f in fingers:
        c.drawPath(f, _pt(SKIN))
        c.drawPath(f, outline)
    c.drawPath(back, _pt(SKIN))
    c.drawPath(back, outline)
    # form shade on the lower edge, soft highlight across the back of the hand
    sh = _minus_shifted(sil, (0.0, -3.2))
    if sh is not None:
        c.drawPath(sh, _pt(SKIN_SH, 0.75))
    c.drawPath(_spl(skia.Path(), [(-12.0, -4.2), (-2.0, -5.8), (7.0, -4.6)]), _pt(SKIN_HI, 0.8, stroke=1.6))
    # knuckles: small highlights where the fingers bend over the wrist
    for pts, _, _ in _CLASP_FINGERS:
        q0, q1 = pts[0], pts[1]
        c.drawLine(q0[0] + 1.5, q0[1] - 0.8, q1[0] - 0.5, q1[1] - 1.2, _pt(SKIN_HI, 0.7, stroke=1.0))
    if seam_a > 0.02:
        c.drawLine(-15.0, -5.0, -15.0, 5.0, _pt(SEAM, seam_a * 0.8, stroke=0.8))
    c.restore()


# --------------------------------------------------------------------------- drawing: neck + collar


def _head_edge(P, y, sigma):
    """Projected silhouette point of the head slice at height y on screen side sigma (+1 / -1)."""
    a, bf, bb = _slice(y)
    b = bf if sigma * P.s >= 0 else bb
    R = math.sqrt((a * P.c) ** 2 + (b * P.s) ** 2) or 1e-6
    return P.p(a * (sigma * a * P.c / R), y, b * (sigma * b * P.s / R))


def _neck_geom(g):
    hx = g.neck_x
    m = g.M_head
    P = g.P
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
    # turned past profile the jaw is seen from behind: the face-side neck contour runs from the
    # collar up along the jaw line to just below the ear (sternocleidomastoid), so the visible jaw is
    # a thin crescent meeting the neck - never a detached sliver hanging beside it
    w_ext = smoothstep(-P.c / 0.25) * smoothstep(abs(P.s) / 0.25)
    if w_ext > 0.001:
        sg = 1.0 if P.s >= 0 else -1.0
        jx, jy = _head_edge(P, 27.0, sg)
        cx_, cy_ = _head_edge(P, 56.0, sg)
        J = m.mapXY(jx - sg * 4.5, jy)
        C = m.mapXY(cx_ - sg * 1.5, cy_)
        if sg > 0:
            qt = pts_r[-1]
            mid = pts_r[1]
            pts_r = [pts_r[0], (lerp(mid[0], lerp(C.x(), pts_r[0][0], 0.45), w_ext), mid[1]),
                     (lerp(qt[0], C.x(), w_ext), lerp(qt[1], C.y(), w_ext)),
                     (lerp(qt[0], J.x(), w_ext), lerp(qt[1], J.y(), w_ext))]
        else:
            qt = pts_l[0]
            mid = pts_l[1]
            pts_l = [(lerp(qt[0], J.x(), w_ext), lerp(qt[1], J.y(), w_ext)),
                     (lerp(qt[0], C.x(), w_ext), lerp(qt[1], C.y(), w_ext)),
                     (lerp(mid[0], lerp(C.x(), pts_l[-1][0], 0.45), w_ext), mid[1]), pts_l[-1]]
    p = skia.Path()
    _spl(p, pts_l)
    p.lineTo(*pts_r[0])
    _spl(p, pts_r, move=False)
    p.lineTo(top_c.x(), top_c.y() - 22.0)
    p.close()
    g._neck_sides = (pts_l, pts_r)
    return p, base_y


def _draw_neck(c, g, seam_a, head_sil=None):
    p, base_y = _neck_geom(g)
    _cel(c, p, SKIN, SKIN_SH, (6.0, -2.0))
    ln = _pt(SKIN_LINE, 0.75, stroke=1.3)
    for side_pts in g._neck_sides:
        c.drawPath(_spl(skia.Path(), side_pts), ln)
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
    _cel(c, band, COLLAR, COLLAR_SH, (6.0, 0.0), hi=COLLAR_HI, hi_off=(0.0, 1.6), hi_alpha=0.75, line=COLLAR_LINE,
         line_w=1.1, line_a=0.8)
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
    sq = clamp(pose.squint + max(0.0, pose.smile) * 0.35 + 0.08 * clamp(pose.brow_worry) ** 0.5)
    ly = clamp(pose.look_y, -1.2, 1.2)
    lx = clamp(pose.look_x * g.facing, -1.2, 1.2)
    bw = clamp(pose.brow_worry) ** 0.36         # worry reads early (0.3 is ~65 % of the full, still-small, shape)

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
    # A closing lid is a smooth arc between the projected corners: on the far eye the surface
    # projection compresses the outer corner, which would bend a closed lid into a hook. Blend toward
    # a "billboard" version (uv shape laid uniformly along the projected corner-to-corner chord).
    w_arc = (1.0 - lid) ** 1.2
    if w_arc > 0.01:
        p0, pn = E.up[0], E.up[-1]
        u0, un = up[0][0], up[-1][0]
        # a foreshortened closed lid reads flatter (as an artist would draw it), not as a deep "U"
        sag_k = clamp(math.hypot(pn[0] - p0[0], pn[1] - p0[1]) / 25.0, 0.2, 1.0) ** 0.9

        def bill(curve_uv, pts, w):
            v0, vn = curve_uv[0][1], curve_uv[-1][1]
            out_ = []
            for (u, v), q in zip(curve_uv, pts):
                f = (u - u0) / (un - u0)
                ax, ay = lerp(p0[0], pn[0], f), lerp(p0[1], pn[1], f) + (v - lerp(v0, vn, f)) * P.ct * sag_k
                out_.append((lerp(q[0], ax, w), lerp(q[1], ay, w)))
            return out_
        E.up = bill(up, E.up, w_arc)
        E.lo = bill(lo, E.lo, w_arc * 0.6)
        # keep the upper lid above the lower one after the re-layout
        los = sorted(E.lo)
        E.up = [E.up[0]] + [(x, min(y, _interp_curve(los, x) - 0.05)) for (x, y) in E.up[1:-1]] + [E.up[-1]]
    # lid crease: lowers, flattens and fades as the lid closes (no ghost crease over a closed eye)
    E.crease_a = 0.4 + 0.6 * lid
    E.crease = [es(u, v - (3.2 + wide * 0.6) * (0.45 + 0.55 * lid) + (1.0 - lid) * 0.6, -1.5)
                for (u, v) in up_open[1:-1]]
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
        c.drawPath(_spl(skia.Path(), E.crease), _pt(SKIN_SH2, 0.42 * al * E.crease_a, stroke=1.1))
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


# iris colour stops (inner, mid, outer, dark rim, limbal ring). The irises stay teal at every
# warmth: `warm` only blooms a gold ring around the pupil and turns the glow / catch-lights amber
# (never a fully amber / yellow iris, never through pale or olive).
_IR_TEAL = ((206, 255, 247), (95, 227, 208), (58, 196, 182), (28, 140, 132), (11, 74, 80))
_IR_GOLD_IN = (255, 212, 118)           # the warm ring around the pupil at warm = 1
_GL_TEAL, _GL_WARMWHITE, _GL_AMBER = (150, 255, 238), (248, 240, 218), (255, 190, 105)
_BLOOM_TEAL = (40, 205, 190)            # saturated bloom colour (reads as teal on pale skin)
_BLOOM_WARMWHITE, _BLOOM_AMBER = (236, 226, 196), (255, 168, 72)
_RING_TEAL = (10, 84, 84)


def _route3(a, m, b, w):
    """Colour route a -> m (w = 0.5) -> b (w = 1): teal never mixes straight into amber (olive)."""
    if w <= 0.5:
        return _mixc(a, m, smoothstep(w / 0.5))
    return _mixc(m, b, smoothstep((w - 0.5) / 0.5))


def _iris_cols(g, warm):
    """(stops, inner stop position, glow colour, bloom colour, ring colour) for the warmth."""
    w = clamp(warm)
    if w <= 0.001:
        return _IR_TEAL, 0.16, _GL_TEAL, _BLOOM_TEAL, _RING_TEAL
    s_in, s_mid, s_out, s_dk, s_lim = _IR_TEAL
    stops = (_mixc(s_in, _IR_GOLD_IN, 0.95 * smoothstep(w)), s_mid, s_out, s_dk, s_lim)
    return (stops, 0.16 + 0.16 * smoothstep(w), _route3(_GL_TEAL, _GL_WARMWHITE, _GL_AMBER, w),
            _route3(_BLOOM_TEAL, _BLOOM_WARMWHITE, _BLOOM_AMBER, w), _RING_TEAL)


def _iris_shape(c, E, g, emissive=True, alpha=1.0, warm=0.0, flick=1.0):
    pose = g.pose
    cx, cy = E.iris_c
    r = E.iris_r
    (s_in, s_mid, s_out, s_dk, s_lim), p_in, gl, _, ring = _iris_cols(g, warm)
    glw = clamp(pose.glow)
    proc = clamp(pose.process)
    boost = clamp(0.15 + 0.85 * glw + 0.3 * proc) * flick
    # glow lights the iris from inside: the core goes near-white (cap 0.85 at glow 1), the mid ring
    # brightens toward the core colour; the dark rim + limbal ring keep the iris readable as an iris
    wcore = min(0.85, 0.1 + 0.75 * boost ** 1.2)
    inner = _mixc(s_in, (255, 255, 255), wcore * (1.0 - 0.55 * clamp(warm)))
    mid = _mixc(s_mid, s_in, min(0.62, 0.62 * boost))
    outer = _mixc(s_out, s_mid, 0.4 * boost)
    dk = _mixc(s_dk, s_out, 0.25 * boost)
    lim = s_lim
    pup = PUPIL
    if not emissive:
        inner, mid, outer, dk, lim, gl, ring = (_lc(q) for q in (inner, mid, outer, dk, lim, gl, ring))
        pup = _lc(pup)
    c.save()
    c.translate(cx, cy)
    c.scale(E.kx_i, 1.0)
    sh = skia.GradientShader.MakeRadial((0.0, -0.5), r, [col(inner, alpha), col(mid, alpha), col(outer, alpha),
                                                         col(dk, alpha)], [p_in, 0.52, 0.8, 1.0])
    c.drawCircle(0, 0, r, paint(None, shader=sh))
    c.drawCircle(0, 0, r - 0.45, paint(lim, alpha * 0.9, stroke=0.9))
    # static fine "lens" ring; while processing it lights up (glow colour) between the two
    # spinning rings - the spin-up reads through brightness, not through speed
    c.drawCircle(0, 0, r * 0.64, paint(ring, alpha * 0.28 * (1.0 - (proc if emissive else 0.0)), stroke=0.45))
    if emissive and proc > 0.01:
        c.drawCircle(0, 0, r * 0.64, paint(gl, alpha * 0.7 * proc, stroke=0.45 + 0.35 * proc))
        # two bold, soft-edged dark rings turning slowly at constant speed inside the bright iris
        # (contrast survives any glow level). Few, wide, slow segments keep every frame predictable
        # for the encoder - thin fast rings (and speed tied to `process`) turned into mush at ~380 kbps.
        t = g.t
        for rr, spd, segs, frac, sw in ((0.5, 60.0, 3, 0.55, 1.6), (0.79, -45.0, 4, 0.45, 1.7)):
            rot = (t * spd) % 360.0
            rect = skia.Rect(-r * rr, -r * rr, r * rr, r * rr)
            pth = skia.Path()
            for s_ in range(segs):
                pth.addArc(rect, rot + s_ * 360.0 / segs, 360.0 / segs * frac)
            c.drawPath(pth, paint(ring, alpha * proc * 0.72, stroke=sw, cap="butt", blur=0.35))
    # pupil last (+ thin aperture ring) so gaze always reads
    pr = E.pupil
    c.drawCircle(0, 0.2, pr + 0.6, paint(ring, alpha * 0.55, stroke=0.6))
    c.drawCircle(0, 0.2, pr, paint(pup, alpha))
    # catch-lights (warm with the glow at the closing smile)
    hl = _mixc((255, 255, 255), (255, 228, 176), 0.8 * clamp(warm))
    if not emissive:
        hl = _lc(hl)
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

    # Effective roundness. The lip-sync "round" channel comes from the spectral centroid, which
    # sits low for his whole baritone (round > 0.6 on most open frames), so taken at face value
    # every vowel became a small, tall, dark "O" - a surprised "ooh" that fights his deadpan.
    # Only a modest share of it shapes the mouth; a rounder (still calm) O is kept for clear
    # "oo"/"or" values (r > 0.9, ~5 % of his open frames, and the "oo" expression preset).
    oo = smoothstep(clamp((r - 0.9) / 0.1))
    r_eff = min(0.35, 0.4 * r) + 0.25 * oo
    w = 14.0 * (1.0 - 0.5 * r_eff * min(1.0, o * 3.0 + 0.3)) * (1.0 - 0.22 * o) + 1.0 * max(sm, 0.0)
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
    h_top = -o * (3.4 + r_eff * 1.4)
    # the lower lip drops with the opening but eases into a cap (soft knee), so even his loudest
    # vowels read as a calm, flat oval rather than a gaping hole
    h_bot = o * (8.6 + r_eff * 2.2)
    cap = 6.5 + 1.5 * r_eff + 1.2 * oo
    knee = 1.6
    if h_bot > cap - knee:
        h_bot = cap - knee + knee * (1.0 - math.exp(-(h_bot - (cap - knee)) / knee))
    # corners sit half-way down the opening and the top lip arches over it: an "ah" reads as an
    # oval opening (a calm, deadpan vowel), never as a "D"-shaped grin
    fr = 0.5
    cy0 = h_top + (h_bot - h_top) * fr
    cyr = cy0 + dyr * 0.8
    cyl = cy0 + dyl * 0.8
    sx = 0.62 + 0.2 * r_eff
    # top lip: a soft arch, highest at the centre, curving DOWN into the corners
    tq = lerp(0.55, 0.85, r_eff)
    cr = 0.7 * o + 0.3                      # corners are small rounded ends, not points
    wc = w + 0.6
    top = [mp(-w, cyr - cr), mp(-w * sx, lerp(cyr, h_top, tq) + dyr * 0.2), mp(-w * 0.22, h_top + 0.3),
           mp(0, h_top + 0.12 * (1 - r_eff)), mp(w * 0.22, h_top + 0.3),
           mp(w * sx, lerp(cyl, h_top, tq) + dyl * 0.2), mp(w, cyl - cr)]
    bq = lerp(0.72, 0.9, r_eff)
    bot = [mp(wc, cyl), mp(w, cyl + cr), mp(w * sx, lerp(cyl, h_bot, bq) + dyl * 0.2), mp(0, h_bot),
           mp(-w * sx, lerp(cyr, h_bot, bq) + dyr * 0.2), mp(-w, cyr + cr), mp(-wc, cyr)]
    top = [mp(-wc, cyr)] + top + [mp(wc, cyl)]
    shape = _two_curve_path(top, bot)
    purse = clamp((r_eff - 0.2) / 0.55)
    if purse > 0.02:
        # pursed lips: a soft rim around the opening (only toward a real "oo")
        c.drawPath(shape, _pt(SKIN_SH, 0.45 * purse, stroke=4.2))
    c.drawPath(shape, _pt(MOUTH_IN))
    c.save()
    c.clipPath(shape, skia.ClipOp.kIntersect, True)
    if o > 0.12:
        # a narrow strip of upper teeth (<= 2 units)
        th = min(2.0, 0.9 + o * 1.2) * (1.0 - 0.6 * r_eff)
        teeth = [(x, y + th) for (x, y) in top]
        tp = _two_curve_path(top, teeth[::-1])
        c.drawPath(tp, _pt(TEETH, 0.9 * (1.0 - 0.7 * r_eff)))
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
        _cel(c, path, SKIN, SKIN_SH, (4.0, -2.0), line=SKIN_LINE, line_w=1.1, line_a=0.7)
        a_in = clamp(abs(nz) * 2.5)
        if a_in > 0.02:
            c.drawPath(_spl(skia.Path(), inner), _pt(SKIN_SH2, 0.8 * a_in, stroke=1.4))
            cc = (rx + o * w * 0.38, ry + 1.0)
            c.drawOval(skia.Rect(cc[0] - w * 0.18, cc[1] - 4.0, cc[0] + w * 0.18, cc[1] + 4.0), _pt(SKIN_SH, 0.7 * a_in))
    else:
        _cel(c, path, SKIN_SH, SKIN_SH2, (3.0, -2.0), line=SKIN_LINE, line_w=1.1, line_a=0.7)
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
    if _SIL is not None:
        _sil_add(c, skia.Op(hsil, hp, skia.PathOp.kIntersect_PathOp))
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
    # thin dark contour on the outer edge of the hair (clipped: only the inner half of the stroke)
    c.drawPath(hsil, _pt(HAIR_LINE, 0.85, stroke=2.6))
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
            if _SIL is not None:
                _sil_add(c, skia.Op(sil, cut, skia.PathOp.kDifference_PathOp) or sil)
            c.save()
            c.clipPath(cut, skia.ClipOp.kDifference, True)
        _cel(c, sil, SKIN, SKIN_SH, (9.0, -5.5), hi=SKIN_HI, hi_off=(-2.5, 2.5), hi_alpha=0.7, sil=cut is None,
             line=SKIN_LINE, line_w=1.3, line_a=0.8)
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
                        c.drawPath(_spl(skia.Path(), sock), _pt(SKIN_SH, 0.22 * E.alpha * E.crease_a, stroke=5.0))
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


def _draw_behind_hands(c, g, beh, seam_a):
    """Forearms + hands of the arms that are behind the back (clasped when both are)."""
    if len(beh) == 2:
        ck = smoothstep((min(beh[0].behind, beh[1].behind) - 0.8) / 0.2)
    else:
        ck = 0.0
    if ck < 0.999:
        for ch in beh:
            _draw_arm(c, g, ch, "fore", seam_a)
    if ck > 0.001:
        if ck < 0.999:
            lp = skia.Paint()
            lp.setAlphaf(ck)
            c.saveLayer(None, lp)
        _draw_clasped_hands(c, g, beh, seam_a)
        if ck < 0.999:
            c.restore()


def _draw_body(c, g, seam_a):
    """Everything that is lit by the scene (colours go through the pose light / tint)."""
    arms = g.arms
    chs = [arms["l"], arms["r"]]
    legs = sorted([-1.0, 1.0], key=lambda sg: _bdepth(g, sg * 22.0, 0.0))     # far leg first
    beh = [ch for ch in chs if ch.behind >= 0.5]
    free = [ch for ch in chs if ch.behind < 0.5]
    # hands behind the back are hidden by the torso in front views and lie over the back in back
    # views; past profile they cross-fade (outside the torso both copies coincide -> no pop)
    xf = smoothstep((g.psb - 90.0) / 22.0)
    if beh and xf < 0.999:
        _draw_behind_hands(c, g, beh, seam_a)
    for ch in free:
        if not ch.front and ch.across < 0.5:
            _draw_arm(c, g, ch, "all", seam_a)
    for ch in beh:
        if not ch.near:
            _draw_arm(c, g, ch, "upper", seam_a)
    c.save()
    c.concat(g.M_leg_rel)
    for sg in legs:
        _draw_leg(c, g, sg)
    c.restore()
    _draw_torso(c, g, seam_a)
    _draw_insignia(c, g)
    _draw_shoulder_stripe(c, g)
    g.front_arms = []                       # arms drawn over the face (they occlude the glowing irises)
    if g.back_view:
        for ch in free:
            if ch.front and ch.across < 0.5:
                _draw_arm(c, g, ch, "all", seam_a)
        for ch in beh:
            if ch.near:
                _draw_arm(c, g, ch, "upper", seam_a)
        if beh and xf > 0.001:
            if xf < 0.999:
                lp = skia.Paint()
                lp.setAlphaf(xf)
                c.saveLayer(None, lp)
            _draw_behind_hands(c, g, beh, seam_a)
            if xf < 0.999:
                c.restore()
        _draw_neck_head(c, g, seam_a)
        for ch in free:
            if ch.across >= 0.5:
                _draw_arm(c, g, ch, "all", seam_a)
        return
    _draw_neck_head(c, g, seam_a)
    for ch in beh:
        if ch.near:
            _draw_arm(c, g, ch, "upper", seam_a)
    if beh and xf > 0.001:
        if xf < 0.999:
            lp = skia.Paint()
            lp.setAlphaf(xf)
            c.saveLayer(None, lp)
        _draw_behind_hands(c, g, beh, seam_a)
        if xf < 0.999:
            c.restore()
    for ch in free:
        if ch.front and ch.across < 0.5:
            _draw_arm(c, g, ch, "all", seam_a)
            g.front_arms.append(ch)
    for ch in free:
        if ch.across >= 0.5:
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
        kind = ch.hand if ch.hand in _HAND_PARTS else "relaxed"
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
    Order: bloom + spill first, then the irises on top, pupil last, then the lash line, so the
    glow never fogs the gaze.

    In normal light a pale-teal glow would vanish on Quill's pale skin, so the bloom there is a
    saturated teal tint (normal blend) plus an additive teal lift (~1.6x the eye width); in the dark
    it is a screen-blended halo. Low glow (the 0.1-0.2 idle level) stays invisible."""
    eyes = [E for E in getattr(g, "eyes", []) if E.visible and E.opening is not None]
    if not eyes:
        return
    pose = g.pose
    proc = clamp(pose.process)
    # a tiny flicker only while the lens engages / disengages (process < 0.3); frozen while it
    # spins, so the processing close-up is not new noise on every frame
    eng = clamp(proc / 0.3)
    flick = 1.0 + 0.12 * math.sin(math.pi * eng) * (0.7 * noise1(t * 23.0, 5) + 0.3 * math.sin(t * 41.0))
    glw = clamp(pose.glow)
    dk = _darkness(g)
    emis = clamp(0.4 + 0.6 * glw + 0.6 * dk + 0.4 * proc)
    if g.light >= 0.999 and g.tint_amt <= 0.001:
        emis = 1.0
    _, _, gl, bloom, _ = _iris_cols(g, warm)
    s_light = (1.0 - dk) * clamp(glw ** 1.4 + 0.12 * proc)
    s_dark = dk * clamp(0.3 + 0.7 * glw + 0.3 * proc)
    c.save()
    for q in _occluders(g):
        c.clipPath(q, skia.ClipOp.kDifference, True)
    c.concat(g.M_head)
    if s_light + s_dark > 0.01:
        rad_d = (10.0 + 13.0 * glw) * 1.05
        for E in eyes:
            open_k = clamp(E.gap / 8.0) * E.alpha * flick
            cx, cy = E.iris_c
            c.save()
            c.translate(cx, cy)
            c.scale(max(0.45, E.kx_i), 0.68)
            if s_light > 0.005:
                a = s_light * open_k
                glow(c, 0.0, 0.0, 23.0, bloom, 0.34 * a, blend=None)
                glow(c, 0.0, 0.0, 21.0, bloom, 0.7 * a, blend="add")
            if s_dark > 0.005:
                c.scale(1.12, 0.8 / 0.68)
                glow(c, 0.0, 0.0, rad_d, bloom, 0.62 * s_dark * open_k, blend="screen")
            c.restore()
            core = (0.3 + 0.7 * glw) * (s_dark + 0.85 * s_light) * open_k
            if core > 0.005:
                c.save()
                c.translate(cx, cy)
                c.scale(max(0.45, E.kx_i) * 1.1, 0.85)
                glow(c, 0.0, 0.0, 7.0 + 5.0 * glw, gl, 0.75 * core, blend="screen")
                c.restore()
    # light spill on the cheeks at high glow
    if glw > 0.3:
        c.save()
        c.clipPath(g.head_sil, skia.ClipOp.kIntersect, True)
        for E in eyes:
            cx, cy = E.iris_c
            amt = clamp((glw - 0.3) / 0.7) * clamp(E.gap / 8.0) * E.alpha
            c.save()
            c.translate(cx, cy + 13.0)
            c.scale(1.3 * max(0.4, E.kx_i), 0.7)
            if dk < 0.999:
                glow(c, 0.0, 0.0, 20.0, bloom, 0.16 * amt * (1.0 - dk), blend="add")
            if dk > 0.001:
                glow(c, 0.0, 0.0, 20.0, bloom, 0.2 * amt * dk, blend="screen")
            c.restore()
        c.restore()
    # irises clipped to the head silhouette (the far eye never pokes past the cheek contour)
    c.clipPath(g.head_sil, skia.ClipOp.kIntersect, True)
    for E in eyes:
        _draw_eye_emissive(c, E, g, warm, flick, emis)
    c.restore()


def _body_bounds(g, pad=30.0):
    """Conservative bounds of everything draw() paints, in body coords (after M_stage)."""
    xs = [-80.0, 80.0]
    ys = [-835.0, -360.0]
    for ch in g.arms.values():
        for q in (ch.S, ch.E, ch.W):
            xs.append(q[0])
            ys.append(q[1])
    up = g.M_upper.mapRect(skia.Rect(min(xs) - 62.0 - pad, min(ys) - 62.0 - pad,
                                     max(xs) + 62.0 + pad, max(ys) + 62.0 + pad))
    legs = g.M_legs.mapRect(skia.Rect(-80.0 - pad, -440.0, 80.0 + pad, 8.0 + pad))
    up.join(legs)
    return up


def _union_paths(paths):
    """Union of many paths (PathOps). None if PathOps fails."""
    try:
        b = skia.OpBuilder()
        for q in paths:
            b.add(q, skia.PathOp.kUnion_PathOp)
        return b.resolve()
    except Exception:
        out = paths[0]
        for q in paths[1:]:
            r = skia.Op(out, q, skia.PathOp.kUnion_PathOp)
            if r is None:
                return None
            out = r
        return out


def _draw_rimlit(c, g, seam_a, rim, rc, body_dev):
    """Rim light, same look as Rae's rig: a soft two-radius glow of the silhouette under the
    character + a thin bright edge on the screen-left / top of the OUTER silhouette only (inner
    edges such as arm-over-torso, legs or the collar are never outlined).

    The body is recorded into a picture while its silhouette paths are collected (_SIL) and unioned;
    the glow is mask-blurred from that path at low resolution (bilinear to half resolution, then a
    cheap 2x nearest upscale), the edge is the silhouette minus itself shifted down-right."""
    global _SIL
    M = c.getTotalMatrix()
    dscale = math.sqrt(abs(M.getScaleX() * M.getScaleY() - M.getSkewX() * M.getSkewY()))
    _SIL = []
    try:
        rec = skia.PictureRecorder()
        rcv = rec.beginRecording(skia.Rect(-4000, -4000, 4000, 4000))
        _draw_body(rcv, g, seam_a)
        pic = rec.finishRecordingAsPicture()
        sils = _SIL
    finally:
        _SIL = None
    U = _union_paths(sils) if sils else None
    clipb = c.getDeviceClipBounds()
    rcol = col(rc)
    # ---- glow (under the body)
    pad = 62.0 * dscale
    gx0 = max(math.floor(body_dev.left() - pad), clipb.left() - 2)
    gy0 = max(math.floor(body_dev.top() - pad), clipb.top() - 2)
    gx1 = min(math.ceil(body_dev.right() + pad), clipb.right() + 2)
    gy1 = min(math.ceil(body_dev.bottom() + pad), clipb.bottom() + 2)
    if U is not None and gx1 > gx0 and gy1 > gy0:
        q = max(2.0, 4.0 * dscale)                     # low-res pixel = 4 stage units
        gw, gh = int((gx1 - gx0) / q) + 2, int((gy1 - gy0) / q) + 2
        small = skia.Surface(gw, gh)
        sc = small.getCanvas()
        sc.scale(1.0 / q, 1.0 / q)
        sc.translate(-gx0, -gy0)
        sc.concat(M)
        for sig, a in ((20.0, 0.5 * rim), (7.0, min(1.0, 0.85 * rim))):
            gp = skia.Paint(AntiAlias=True, Color=rcol)
            gp.setAlphaf(a)
            # blur sigma in the canvas' local units (MaskFilter respects the CTM)
            gp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, sig))
            sc.drawPath(U, gp)
        gimg = small.makeImageSnapshot()
        mw, mh = int((gx1 - gx0) / 2) + 2, int((gy1 - gy0) / 2) + 2
        mid = skia.Surface(mw, mh)
        mid.getCanvas().drawImageRect(gimg, skia.Rect(0, 0, gw * q / 2, gh * q / 2),
                                      skia.SamplingOptions(skia.FilterMode.kLinear))
        c.save()
        c.resetMatrix()
        c.drawImageRect(mid.makeImageSnapshot(), skia.Rect(gx0, gy0, gx0 + mw * 2, gy0 + mh * 2),
                        skia.SamplingOptions())
        c.restore()
    # ---- the character
    c.drawPicture(pic)
    # ---- thin edge: silhouette minus the silhouette shifted down-right in SCREEN space (so the rim
    # sits on the same screen side as Rae's whatever the facing)
    if U is not None:
        inv = skia.Matrix()
        if M.invert(inv):
            v = inv.mapVector(max(1.0, 2.6 * dscale), max(1.0, 2.8 * dscale))
            sh = skia.Path(U)
            sh.offset(v.x(), v.y())
            cr = skia.Op(U, sh, skia.PathOp.kDifference_PathOp)
            if cr is not None:
                c.drawPath(cr, paint(rcol, min(1.0, 1.1 * rim)))


def draw(canvas: skia.Canvas, pose: Pose, t: float, warm: float | None = None) -> None:
    """Draw Quill. canvas is in stage coords (camera already applied).

    warm: 0..1 (None = 0) warms the eye glow for the closing smile (S5 `quill_smile`): a gold
          ring blooms around the pupils and the bloom / catch-lights turn amber, while the irises
          themselves stay teal. Scenes animate it explicitly; nothing sets it automatically.
    """
    global _LT
    g = _layout(pose, t)
    warm = 0.0 if warm is None else clamp(float(warm))
    _LT = (float(pose.light), float(clamp(pose.tint_amt)), tuple(float(v) for v in pose.tint))
    rim = clamp(pose.rim)
    canvas.save()
    try:
        canvas.concat(g.M_stage)
        seam_a = _seam_alpha(canvas, pose)
        body_dev = canvas.getTotalMatrix().mapRect(_body_bounds(g)) if rim > 0.001 else None
        canvas.save()
        canvas.concat(g.M_upper)
        if rim > 0.001:
            rc = rgb(pose.rim_color) if isinstance(pose.rim_color, str) else tuple(pose.rim_color)[:3]
            _draw_rimlit(canvas, g, seam_a, rim, rc, body_dev)
        else:
            _draw_body(canvas, g, seam_a)
        _draw_emissive(canvas, g, t, warm)
        canvas.restore()
    finally:
        canvas.restore()
        _LT = (1.0, 0.0, (0.0, 0.0, 0.0))
