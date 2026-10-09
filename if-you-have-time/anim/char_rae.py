"""RAE - the human crew member (BIBLE.md section 2). Full procedural 2D rig.

Rig contract (anim/rig.py):
    draw(canvas, pose, t)            draw Rae; canvas already carries the camera (stage units)
    head_center(pose) -> (x, y)      stage point between the eyes
    hand_pos(pose, side) -> (x, y)   stage point at the palm centre of Rae's 'l' / 'r' hand
    ARMS                             ArmPose presets (rest, hold_mug, sip, mug_raise, point, hand_on_chest,
                                     wipe_eye, cover_mouth, hands_up, grip_knee, reach_back, shrug,
                                     hug_self, knee_rest)
    HEIGHT                           floor -> top of the hair puff at scale 1
Extras:
    draw_mug(canvas, x, y, scale=1.0, angle=0.0, flip=False)   the mug standing on its base at (x, y)
    mug_pose(pose) -> (x, y, scale, angle, flip) or None        where the held mug is (feed to draw_mug)
    EXPR                             face presets: name -> dict of Pose overrides
    expr(pose, name, amount=1.0)     pose with a face preset blended in
    mouth_pos(pose) -> (x, y)        stage point at the centre of the mouth

Conventions specific to Rae (on top of rig.py):
    * pose.x is the body axis (pelvis centre). Standing, the feet are under it; seated they rest ~95
      units forward of it (toward `facing`); kneeling, the shins point backward.
    * bounce is a vertical body offset in stage y (+ = down, like Quill's rig); legs bend to absorb it.
    * smirk > 0 lifts the mouth corner on the `facing` side (and cocks the opposite brow).
    * ArmPose.across 0..1 pulls the hand toward the opposite shoulder (0.5 ~ body midline);
      across < 0 (Rae extension) spreads the arm outward instead of forward (shrug).
    * Arm angles swing toward `facing` once turn >= ~0.25; in a pure front view (turn 0) they come
      forward toward the camera (slightly inward, foreshortened).
    * facing=-1 is a pure mirror image (as in Quill's rig): arm_r / lid_r / tear_r always belong to the
      side nearer the camera once Rae is turned (screen-left of the body for facing +1, screen-right
      for facing -1).
    * light: pose.light/tint/tint_amt go through core.light_filter applied to every paint (equivalent
      to a filtered layer, without the offscreen cost), with a perceptual curve light**0.65 so Rae's
      dark-brown skin still reads at light 0.25; eye catch-lights are re-drawn un-darkened in low light.

Local drawing frame: facing=+1 orientation, origin = floor point under the pelvis, y down.
"Near" side = -x (Rae's right), "far" side = +x.
"""
from __future__ import annotations

import math

import skia

from anim.core import auto_blink, breathe, clamp, col, lerp, light_filter, mix_col, noise1, smooth_path, smoothstep
from anim.core import paint as _core_paint
from anim.rig import ArmPose, Pose

# --------------------------------------------------------------------------- proportions
HIP_H = 326.0           # standing hip-joint height
HIP_LAT = 25.0          # half distance between hip joints
THIGH, SHIN = 158.0, 148.0
ANKLE_H = 22.0
SEAT_OFF = 20.0         # hip joint above the seat surface
KNEEL_HIP = 168.0
SIT_FOOT = 82.0         # seated: ankles this far forward of the hips
KNEEL_FOOT = -128.0     # kneeling: ankles this far behind
STRIDE, LIFT = 34.0, 8.0
SH_Y = -136.0           # shoulder joints (relative to pelvis)
SH_A = 52.0
UPPER, FORE = 104.0, 94.0
NECK_PIVOT = -184.0     # head pivot (relative to pelvis)
PIVOT_HL = 46.0         # pivot position in head-local y (eye line = 0)
HEAD_S = 0.92           # head-local units -> body units
HAND_S = 1.3            # hand-local units -> body units
TURN_DEG = 82.0

HEIGHT = 725.0         # floor -> top of the hair puff (head top without the puff ~ 640)

# --------------------------------------------------------------------------- palette
C_SKIN = col("r_skin")
C_SKIN_SH = col("r_skin_shade")
C_SKIN_HI = col("r_skin_hi")
C_SKIN_LINE = col("#58301A")
C_SKIN_DEEP = col("#6A3E22")
C_LID = mix_col("r_skin", "r_skin_shade", 0.38)
C_PALM = col("#B98863")
C_HAIR = col("r_hair")
C_HAIR_HI = col("r_hair_hi")
C_HAIR_SH = col("#170D08")
C_HAIR_SHEEN = col("#6E4A35")
C_BROW = col("#22130C")
C_LASH = col("#150B07")
C_SCLERA = col("#F3EDE7")
C_SCLERA_SH = col("#BCA698")
C_IRIS = col("r_iris")
C_IRIS_LT = col("#9C6638")
C_IRIS_MID = col("#64391D")
C_PUPIL = col("#0C0604")
C_MOUTH = col("#3A1015")
C_TEETH = col("#F7F2EC")
C_TONGUE = col("#B4434D")
C_LIP = col("r_lips")
C_LIP_HI = col("#A3594A")
C_LIP_LINE = col("#43160F")
C_SHIRT = col("r_shirt")
C_SHIRT_SH = col("#B3742A")
C_JACKET = col("r_jacket")
C_JACKET_SH = col("r_jacket_shade")
C_JACKET_HI = col("#535B7D")
C_JACKET_LINE = col("#1B1E2C")
C_ZIP = col("#8D94B0")
C_PANTS = col("r_pants")
C_PANTS_SH = col("#1F2336")
C_PANTS_LINE = col("#151826")
C_SHOE = col("#3C3444")
C_SHOE_SH = col("#2A2430")
C_SHOE_LINE = col("#1A161E")
C_SOLE = col("#E7E1D5")
C_TIE = col("#D98A3A")
C_TIE_SH = col("#A3602A")
C_TEAR = col("tear")
C_BLUSH = col("blush")
C_STUD = col("#F2C86E")
C_PATCH = col("#2EC4B6")
C_MUG = col("mug")
C_MUG_SH = col("#C8C6BE")
C_MUG_LINE = col("#8A877F")
C_LOGO = col("mug_text")
C_COFFEE = col("#4B2A19")
WHITE = col("#FFFFFF")

D2R = math.pi / 180.0

# Colour filter applied to every paint while the body is drawn (lighting). Filtering each paint is
# equivalent to filtering the composite for this affine colour matrix, and avoids an offscreen layer.
_CF = None


_CF_KEY = None


def paint(color, alpha=1.0, **kw):
    p = _core_paint(color, alpha, **kw)
    if _CF is not None:
        p.setColorFilter(_CF)
    return p


_PIC_CACHE = {}


def _cached(c, key, bounds, fn):
    """Record fn(canvas) into a skia.Picture cached under key (+ current lighting) and replay it.
    Used for parts that depend only on a few quantised parameters (hair puff, hair cap)."""
    k = (key, _CF_KEY)
    pic = _PIC_CACHE.get(k)
    if pic is None:
        rec = skia.PictureRecorder()
        fn(rec.beginRecording(bounds))
        pic = rec.finishRecordingAsPicture()
        if len(_PIC_CACHE) > 400:
            _PIC_CACHE.clear()
        _PIC_CACHE[k] = pic
    c.drawPicture(pic)


# --------------------------------------------------------------------------- small geometry helpers
class _NS:
    pass


def _cr(path, pts, move=True, tension=0.5):
    """Append an open Catmull-Rom curve through pts (same maths as core.smooth_path)."""
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


def _closed2(a, b):
    """Closed path: curve through a, then curve through b (b traversed as given)."""
    p = skia.Path()
    _cr(p, a)
    _cr(p, b, move=False)
    p.close()
    return p


def _norm(x, y):
    d = math.hypot(x, y)
    if d < 1e-9:
        return 0.0, 0.0
    return x / d, y / d


def _ribbon(center, widths):
    """Closed tapered ribbon around a polyline; widths are full widths per point."""
    n = len(center)
    L, R = [], []
    for i in range(n):
        a = center[max(i - 1, 0)]
        b = center[min(i + 1, n - 1)]
        nx, ny = _norm(-(b[1] - a[1]), b[0] - a[0])
        w = widths[i] * 0.5
        L.append((center[i][0] + nx * w, center[i][1] + ny * w))
        R.append((center[i][0] - nx * w, center[i][1] - ny * w))
    return _closed2(L, R[::-1])


def _capsule(path, a, b, ra, rb, bulge=0.0, bulge_at=0.5):
    """Add a tapered capsule (round ends) to `path` (CCW sub-paths; Simplify() before stroking)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    ux, uy = _norm(dx, dy)
    if ux == 0 and uy == 0:
        path.addCircle(a[0], a[1], max(ra, rb), skia.PathDirection.kCCW)
        return path
    nx, ny = -uy, ux
    m = (a[0] + dx * bulge_at, a[1] + dy * bulge_at)
    rm = lerp(ra, rb, bulge_at) + bulge
    s1 = [(a[0] + nx * ra, a[1] + ny * ra), (m[0] + nx * rm, m[1] + ny * rm), (b[0] + nx * rb, b[1] + ny * rb)]
    s2 = [(b[0] - nx * rb, b[1] - ny * rb), (m[0] - nx * rm, m[1] - ny * rm), (a[0] - nx * ra, a[1] - ny * ra)]
    _cr(path, s1)
    _cr(path, s2, move=False)
    path.close()
    path.addCircle(a[0], a[1], ra, skia.PathDirection.kCCW)
    path.addCircle(b[0], b[1], rb, skia.PathDirection.kCCW)
    return path


def _fill(c, path, color, alpha=1.0, blur=0.0):
    c.drawPath(path, paint(color, alpha, blur=blur))


def _stroke(c, path, color, width, alpha=1.0, blur=0.0):
    c.drawPath(path, paint(color, alpha, stroke=width, blur=blur))


def _cel(c, path, base, shade, dx, dy, blur=0.0, line=None, line_w=1.3, line_a=0.8):
    """Cel shading: fill with shade, then the base colour shifted toward the light, clipped.
    The shade shows as a crescent on the side opposite to (dx, dy). The contour is drawn as an
    underlay stroke (so unions of overlapping sub-paths need no path simplification)."""
    if line is not None:
        c.drawPath(path, paint(line, line_a, stroke=line_w * 2.0))
    _fill(c, path, shade)
    c.save()
    c.clipPath(path, doAntiAlias=True)
    c.translate(dx, dy)
    _fill(c, path, base, blur=blur)
    c.restore()
    return path


def _ik(a, b, l1, l2, prefer):
    """2-bone IK: joint between a and b. `prefer(j1, j2)` picks one of the two solutions."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = math.hypot(dx, dy)
    if d < 1e-6:
        return (a[0] + l1, a[1])
    if d >= l1 + l2 - 1e-6:
        r = l1 / (l1 + l2)
        return (a[0] + dx * r, a[1] + dy * r)
    d = max(d, abs(l1 - l2) + 1e-4)
    ca = clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1.0, 1.0)
    ang = math.acos(ca)
    base = math.atan2(dy, dx)
    j1 = (a[0] + l1 * math.cos(base + ang), a[1] + l1 * math.sin(base + ang))
    j2 = (a[0] + l1 * math.cos(base - ang), a[1] + l1 * math.sin(base - ang))
    return prefer(j1, j2)


def _cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


# --------------------------------------------------------------------------- head geometry
# Head-local frame: origin on the head's vertical axis at eye level, y down (scaled by HEAD_S).
# Each horizontal cross-section is two half-ellipses: half-width a, front depth zf, back depth zb.
_FACE_TAB = [  # y, a, zf, zb
    (-20, 61.0, 58.0, 72.0), (-8, 61.0, 59.0, 70.0), (4, 60.5, 60.0, 65.0), (14, 59.0, 60.0, 58.0),
    (24, 56.0, 59.0, 50.0), (32, 52.0, 58.0, 43.0), (40, 47.5, 56.5, 36.0), (47, 42.0, 55.0, 29.0),
    (53, 35.5, 53.0, 22.0), (58, 28.0, 50.5, 16.0), (62, 20.0, 47.5, 10.0), (65, 12.0, 44.0, 6.0),
    (67, 4.0, 40.0, 2.0)]
_CR_CY, _CR_RY, _CR_A, _CR_ZF, _CR_ZB = -20.0, 70.0, 61.0, 58.0, 72.0
_OUT_YS = [-90, -87, -81, -72, -60, -46, -32, -20, -10, -2, 6, 14, 22, 30, 38, 46, 53, 58, 62, 65]
EX = 28.5               # eye centre offset from the face centre line
EW = 16.6               # eye half width
HU0, HL0 = 11.4, 9.0    # upper / lower lid heights when open
RI = 11.0               # iris radius
MOUTH_Y = 42.5


def _prof(y):
    if y <= _CR_CY:
        q = (y - _CR_CY) / _CR_RY
        k = math.sqrt(max(0.0, 1.0 - q * q))
        return _CR_A * k, _CR_ZF * k, _CR_ZB * k
    tab = _FACE_TAB
    if y >= tab[-1][0]:
        return tab[-1][1], tab[-1][2], tab[-1][3]
    for i in range(1, len(tab)):
        if y < tab[i][0]:
            y0, a0, f0, b0 = tab[i - 1]
            y1, a1, f1, b1 = tab[i]
            u = (y - y0) / (y1 - y0)
            return a0 + (a1 - a0) * u, f0 + (f1 - f0) * u, b0 + (b1 - b0) * u
    return tab[-1][1], tab[-1][2], tab[-1][3]


def _jaw_dy(H, y):
    return H.jaw * 7.0 * (y - 30.0) / 38.0 if y > 30.0 else 0.0


def _hx(H, x0, y, dz=0.0):
    """Project a face-surface point given in front-view coords (x0, y) (+ extra depth dz)
    -> (x, y, depth, fs) in head-local coords; fs = horizontal foreshortening factor."""
    a, zf, _ = _prof(y)
    u = clamp(x0 / max(a, 1e-3), -0.995, 0.995)
    z = zf * math.sqrt(1.0 - u * u) + dz
    x = x0 * H.c + z * H.s
    dep = -x0 * H.s + z * H.c
    phi = math.asin(u)
    fs = clamp(math.cos(phi + H.th * 0.92) / max(math.cos(phi), 0.25), 0.1, 1.15)
    return x, y + H.nod_dy * (dep / 60.0), dep, fs


def _surf_az(H, phi_deg, y):
    """Point on the head surface at azimuth phi (0 = front centre, +90 = local +x side), level y.
    Returns (x, y, visibility); visibility > 0 when the surface faces the camera."""
    a, zf, zb = _prof(y)
    ph = phi_deg * D2R
    sp, cp = math.sin(ph), math.cos(ph)
    zz = zf if cp >= 0 else zb
    x0, z = a * sp, zz * cp
    x = x0 * H.c + z * H.s
    dep = -x0 * H.s + z * H.c
    vis = (-H.s * sp / max(a, 1e-3) + H.c * cp / max(zz, 1e-3)) * 60.0
    return x, y + H.nod_dy * (dep / 60.0), vis


_PBUMP = [(-62, 0.0), (-42, 1.2), (-26, 3.8), (-17, 3.4), (-8, 0.8), (0, -0.3), (7, 1.4), (13, 3.0), (20, 2.2),
          (30, 0.6), (44, -0.6), (54, 0.2), (62, 0.8), (70, 0.0)]


def _bump_k(s):
    """How much of the brow-ridge / cheekbone profile shows (0 front view .. 1 from turn ~0.25)."""
    return min(1.0, abs(s) * 2.5)


def _profile_bump(y):
    """Small offsets that give the leading cheek edge brow-ridge / eye-socket / cheekbone shape."""
    tab = _PBUMP
    if y <= tab[0][0] or y >= tab[-1][0]:
        return 0.0
    for i in range(1, len(tab)):
        if y < tab[i][0]:
            y0, v0 = tab[i - 1]
            y1, v1 = tab[i]
            u = (y - y0) / (y1 - y0)
            return v0 + (v1 - v0) * u
    return 0.0


def _head_outline(H, grow=0.0):
    s, c = H.s, H.c
    R, L = [], []
    for y in _OUT_YS:
        a, zf, zb = _prof(y)
        g = grow * clamp((18.0 - y) / 30.0)
        a, zf, zb = a + g, zf + g, zb + g
        if s >= 0:
            r = math.sqrt(a * a * c * c + zf * zf * s * s)
            l = -math.sqrt(a * a * c * c + zb * zb * s * s)
        else:
            r = math.sqrt(a * a * c * c + zb * zb * s * s)
            l = -math.sqrt(a * a * c * c + zf * zf * s * s)
        yy = y + _jaw_dy(H, y)
        if y > 40:
            yy += H.nod_dy * 0.55 * (y - 40) / 28.0
        bump = _profile_bump(y) * _bump_k(s)
        if s >= 0:
            r += bump
        else:
            l -= bump
        R.append((r, yy))
        L.append((l, yy))
    top = (0.0, -90.0 - grow)
    chin = (40.0 * s * 0.98, 67.0 + _jaw_dy(H, 67.0) + H.nod_dy * 0.6)
    nose_k = smoothstep((abs(s) - 0.45) / 0.3)
    if nose_k > 0:
        # nose breaks the silhouette in near-profile views
        edge = R if s >= 0 else L
        sg = 1.0 if s >= 0 else -1.0
        nd = H.nod_dy * 0.95
        nose = [(5.0, 0.0), (15.0, 4.0), (22.0, 9.5), (26.0, 6.0), (28.5, 0.0)]
        new = []
        for (x, y) in edge:
            new.append((x, y))
        for ny, dz in nose:
            a_, zf_, _ = _prof(ny)
            ex = sg * math.sqrt(a_ * a_ * c * c + zf_ * zf_ * s * s)
            nx = sg * (zf_ + dz) * abs(s)
            px = ex + (nx - ex) * nose_k if sg * (nx - ex) > 0 else ex
            new.append((px, ny + nd))
        new.sort(key=lambda q: q[1])
        if s >= 0:
            R = new
        else:
            L = new
    pts = [top] + R[1:] + [chin] + L[1:][::-1]
    return smooth_path(pts, closed=True)


def _sil_x(H, y, side):
    """x of the head silhouette at head-local level y on the +x (side=+1) or -x (side=-1) edge,
    including the brow-ridge / cheekbone bumps on the leading edge (same maths as _head_outline)."""
    a, zf, zb = _prof(y)
    s, c = H.s, H.c
    lead = (s >= 0) == (side > 0)
    z = zf if lead else zb
    x = math.sqrt(a * a * c * c + z * z * s * s)
    if lead:
        x += _profile_bump(y) * _bump_k(s)
    return side * x


# hairline loop on the head surface: (azimuth deg, y)
_HAIRLINE = [(0, -52.0), (14, -51.0), (28, -47.0), (42, -39.0), (54, -29.0), (64, -18.0), (73, -7.0),
             (80, 4.0), (86, 5.0), (91, -5.0), (97, -10.0), (104, -6.0), (114, 6.0), (130, 20.0),
             (150, 28.0), (180, 31.0)]


def _hairline_y(phi):
    """Catmull-Rom interpolation of the (symmetric) hairline table."""
    a = abs(phi)
    tab = _HAIRLINE
    n = len(tab)
    for i in range(1, n):
        if a <= tab[i][0]:
            p0, y1 = tab[i - 1]
            p1, y2 = tab[i]
            y0 = tab[i - 2][1] if i >= 2 else tab[1][1]
            y3 = tab[i + 1][1] if i + 1 < n else y2
            u = (a - p0) / (p1 - p0)
            u2, u3 = u * u, u * u * u
            return 0.5 * ((2 * y1) + (-y0 + y2) * u + (2 * y0 - 5 * y1 + 4 * y2 - y3) * u2 + (-y0 + 3 * y1 - 3 * y2 + y3) * u3)
    return tab[-1][1]


def _hair_region(H):
    """Polygon covering everything above the visible part of the hairline (clip with the head)."""
    samp = []
    start = -H.th / D2R + 180.0          # start opposite the view direction so the visible run is contiguous
    for i in range(91):
        ph = start + i * 4.0
        ph = (ph + 180.0) % 360.0 - 180.0
        samp.append(_surf_az(H, ph, _hairline_y(ph)))
    idx = [i for i, sm in enumerate(samp) if sm[2] > 0]
    if not idx:
        return None, None
    i0, i1 = idx[0], idx[-1]
    pts = [(samp[i][0], samp[i][1]) for i in range(i0, i1 + 1)]

    def cross(ia, ib):
        va, vb = samp[ia][2], samp[ib][2]
        u = va / (va - vb) if va != vb else 0.5
        return (lerp(samp[ia][0], samp[ib][0], u), lerp(samp[ia][1], samp[ib][1], u))
    if i0 > 0:
        pts.insert(0, cross(i0, i0 - 1))
    if i1 < len(samp) - 1:
        pts.append(cross(i1, i1 + 1))
    xl, yl = pts[0]
    xr, yr = pts[-1]
    path = skia.Path()
    _cr(path, pts)
    path.lineTo(xr + 30, yr - 6)
    path.lineTo(xr + 40, -260)
    path.lineTo(xl - 40, -260)
    path.lineTo(xl - 30, yl - 6)
    path.close()
    return path, pts


# --------------------------------------------------------------------------- pose solving
def _solve(p: Pose, t):
    R = _NS()
    fac = 1.0 if p.facing >= 0 else -1.0
    R.fac = fac
    back = p.back > 0.5
    R.back = back
    turn = clamp(p.turn, -0.45, 0.85)
    R.turn = turn
    th = turn * TURN_DEG * D2R
    if back:
        th = math.pi - th
    R.th, R.s, R.c = th, math.sin(th), math.cos(th)
    br = p.breath if p.breath is not None else (breathe(t, 0.2, 2) if t is not None else 0.0)
    R.br = br
    k = clamp(p.kneel)
    sw = clamp(p.sit) * (1.0 - k)
    stw = max(0.0, 1.0 - sw - k)
    R.k, R.sw, R.stw = k, sw, stw
    seat_h = (p.y - p.seat_y) / max(p.scale, 1e-4)
    walking = p.walk is not None
    ph = (p.walk or 0.0)
    R.walking, R.ph = walking, ph
    bob = 2.6 * (0.5 - 0.5 * math.cos(4 * math.pi * ph)) if walking else 0.0
    hv_st = HIP_H - (6.0 if walking else 0.0) + bob
    hv = stw * hv_st + sw * (seat_h + SEAT_OFF) + k * KNEEL_HIP - p.bounce
    R.hv = hv
    lean = p.lean + (3.0 if walking else 0.0) * stw
    R.lean = lean
    MU = skia.Matrix()
    MU.preTranslate(0.0, -hv)
    MU.preRotate(lean)
    R.MU = MU
    su = clamp(p.shoulders_up)
    R.su = su
    s, c = R.s, R.c

    # ---------------- legs (side plane f = forward, v = up; projected with the body turn)
    th_leg = th
    if not back:
        tgt = (52.0 * (sw + k) + (68.0 * stw if walking else 0.0)) / max(1e-6, sw + k + (stw if walking else 0.0))
        th_leg = lerp(th, max(th, tgt * D2R), clamp(sw + k + (stw if walking else 0.0)) * smoothstep((turn - 0.04) / 0.26))
    R.sl, R.cl = math.sin(th_leg), math.cos(th_leg)
    sl_, cl_ = R.sl, R.cl
    tap = 0.0
    if p.foot_tap > 0 and t is not None:
        tap = p.foot_tap * 21.0 * max(0.0, math.sin(2 * math.pi * 2.5 * t)) ** 0.7
    legs = {}
    for o in (-1, 1):
        L = _NS()
        if walking:
            lp = (ph + (0.0 if o < 0 else 0.5)) % 1.0
            if lp < 0.5:
                f_w, lift, toe = lerp(STRIDE, -STRIDE, lp / 0.5), 0.0, 0.0
            else:
                q = (lp - 0.5) / 0.5
                f_w = lerp(-STRIDE, STRIDE, smoothstep(q))
                lift = math.sin(math.pi * q) * LIFT
                toe = -14.0 * math.sin(math.pi * min(1.0, q * 1.6))
        else:
            f_w, lift, toe = 0.0, 0.0, 0.0
        fa = stw * f_w + sw * SIT_FOOT + k * KNEEL_FOOT
        va = stw * (ANKLE_H + lift) + sw * ANKLE_H + k * 16.0
        fwd = (lambda j1, j2: j1 if j1[0] >= j2[0] else j2)
        kn = _ik((0.0, hv), (fa, va), THIGH, SHIN, fwd)
        foot_ang = 0.0
        if k > 0:
            shin0 = math.atan2(fa - kn[0], -(va - kn[1])) / D2R
            foot_ang = smoothstep(k) * (shin0 - 72.0)
            # floor constraint: lift the ankle so the rotated shoe never sinks into the floor
            ca_, sa_ = math.cos(foot_ang * D2R), math.sin(foot_ang * D2R)
            low = min(f_ * sa_ + v_ * ca_ for f_, v_ in _SHOE)
            if va + low < 0:
                va = -low
                kn = _ik((0.0, hv), (fa, va), THIGH, SHIN, fwd)
        lat_h = o * HIP_LAT
        lat_k = o * (stw * 24.0 + sw * 31.0 + k * 27.0)
        lat_a = o * (stw * 21.0 + sw * 28.0 + k * 26.0)
        L.hip = (lat_h * cl_, -hv)
        L.knee = (lat_k * cl_ + kn[0] * sl_, -kn[1])
        L.ankle = (lat_a * cl_ + fa * sl_, -va)
        L.foot_ang = foot_ang + stw * toe
        L.tap = tap if o < 0 else 0.0
        L.o = o
        legs[o] = L
    R.legs = legs

    # ---------------- head
    H = _NS()
    tt = clamp(turn + p.head_turn, -0.6, 0.9)
    H.th = tt * TURN_DEG * D2R
    if back:
        H.th = math.pi - H.th
    H.s, H.c = math.sin(H.th), math.cos(H.th)
    H.nod = clamp(p.head_nod, -1.0, 1.0)
    H.nod_dy = -H.nod * 13.0      # features slide up (chin up) / down on the head sphere
    H.jaw = clamp(p.mouth_open) * (1.0 - 0.3 * clamp(p.mouth_round))
    MHr = skia.Matrix()        # head frame relative to the upper-body frame
    # chin down also drops the head a little so the jaw tucks over the collar
    MHr.preTranslate(4.0 * s, NECK_PIVOT - br * 1.1 + su * 2.0 + max(0.0, -H.nod) * 5.0)
    # nod pitches the head about the neck pivot (visible as a rotation in 3/4 views) ...
    MHr.preRotate(p.head_tilt - H.nod * 14.0 * H.s)
    # ... and foreshortens the face vertically when seen from the front
    MHr.preScale(HEAD_S, HEAD_S * (1.0 - 0.07 * abs(H.nod) * abs(H.c)))
    MHr.preTranslate(0.0, -PIVOT_HL)
    R.MHr = MHr
    R.MH = skia.Matrix.Concat(MU, MHr)
    R.H = H
    face_x = MHr.mapXY(_hx(H, 0.0, 30.0)[0], 30.0).fX

    # ---------------- arms (upper-body frame)
    arms = {}
    sw_amp = 8.0 * stw if walking else 0.0
    for o in (-1, 1):
        A = _NS()
        side = "r" if o < 0 else "l"       # facing=-1 is a pure mirror (same as Quill's rig)
        A.side = side
        ap = p.arm_r if side == "r" else p.arm_l
        A.ap = ap
        S = (o * SH_A * c - 3.0 * s, SH_Y - su * 12.0 - br * 1.1)
        A.S = S
        d = lerp(-o * 0.3, 1.0, smoothstep((turn - 0.02) / 0.23))
        if ap.across < 0:
            d = lerp(d, float(o), min(1.0, -ap.across))
        swing = -o * sw_amp * math.cos(2 * math.pi * ph) * (1.0 - clamp(ap.across * 2.0))
        a1 = (ap.shoulder + swing) * D2R
        a2 = a1 + ap.elbow * D2R
        v1 = (math.sin(a1) * d, math.cos(a1))
        v2 = (math.sin(a2) * d, math.cos(a2))
        fl1, fl2 = math.hypot(*v1), math.hypot(*v2)
        if fl1 < 0.5:
            v1 = _norm(v1[0] - 1e-4 * o, v1[1])
            v1, fl1 = (v1[0] * 0.5, v1[1] * 0.5), 0.5
        if fl2 < 0.5:
            v2 = _norm(v2[0] - 1e-4 * o, v2[1])
            v2, fl2 = (v2[0] * 0.5, v2[1] * 0.5), 0.5
        l1, l2 = UPPER * fl1, FORE * fl2
        E = (S[0] + v1[0] * UPPER, S[1] + v1[1] * UPPER)
        W = (E[0] + v2[0] * FORE, E[1] + v2[1] * FORE)
        flex = _norm(math.cos(a2) * d, -math.sin(a2))
        if flex == (0.0, 0.0):
            flex = (1.0, 0.0)
        v2n = _norm(*v2)
        rot_sense = 1.0 if _cross(v2n, flex) >= 0 else -1.0
        tx, ty = W
        if ap.across > 0:
            opp_x = -o * SH_A * c * 0.92 + 30.0 * s
            mid_x = lerp(30.0 * s, face_x, smoothstep((SH_Y + 10.0 - W[1]) / 45.0))
            if ap.across <= 0.5:
                tx = lerp(W[0], mid_x, ap.across * 2.0)
            else:
                tx = lerp(mid_x, opp_x, (ap.across - 0.5) * 2.0)
        if ap.behind > 0:
            tx = lerp(tx, -24.0 * s - 6.0 * o * c, ap.behind)
            ty = lerp(ty, -40.0, ap.behind * 0.6)
        if ap.across > 0 or ap.behind > 0:
            Efk = E

            def pref(j1, j2, Efk=Efk):
                d1 = (j1[0] - Efk[0]) ** 2 + (j1[1] - Efk[1]) ** 2
                d2 = (j2[0] - Efk[0]) ** 2 + (j2[1] - Efk[1]) ** 2
                return j1 if d1 <= d2 else j2
            E = _ik(S, (tx, ty), l1, l2, pref)
            dx, dy = tx - E[0], ty - E[1]
            dd = math.hypot(dx, dy)
            v2n = _norm(dx, dy)
            W = (E[0] + v2n[0] * min(dd, l2), E[1] + v2n[1] * min(dd, l2))
            flex = (-v2n[1] * rot_sense, v2n[0] * rot_sense)
        A.E, A.W = E, W
        wa = ap.wrist * D2R
        hd = _norm(v2n[0] * math.cos(wa) + flex[0] * math.sin(wa), v2n[1] * math.cos(wa) + flex[1] * math.sin(wa))
        fx = (-hd[1], hd[0])
        if fx[0] * flex[0] + fx[1] * flex[1] < 0:
            fx = (hd[1], -hd[0])
        A.hd, A.fx = hd, fx
        A.palm = (W[0] + hd[0] * 15.0 * HAND_S, W[1] + hd[1] * 15.0 * HAND_S)
        if ap.behind > 0.5:
            A.layer = "behind"
        elif o < 0:
            A.layer = "front"
        elif ap.across > 0.3:
            A.layer = "over"
        else:
            A.layer = "back"
        A.hand = ap.hand
        A.o = o
        arms[o] = A
    R.arms = arms

    MS = skia.Matrix()
    MS.preTranslate(p.x, p.y)
    MS.preScale(fac * p.scale, p.scale)
    R.MS = MS

    # ---------------- mug (upper-body frame)
    R.mug = None
    if p.mug in ("l", "r"):
        A = arms[-1] if arms[-1].side == p.mug else arms[1]
        mx = A.W[0] + A.hd[0] * 19.0
        my = A.W[1] + A.hd[1] * 19.0
        mouth = MHr.mapXY(_hx(H, 0.0, MOUTH_Y)[0], MOUTH_Y)
        dist = math.hypot(mx - mouth.fX, (my - 14.0) - mouth.fY)
        tilt = 1.0 - smoothstep((dist - 16.0) / 46.0)
        ang = -40.0 * tilt
        a = ang * D2R
        M = _NS()
        M.x = mx - math.sin(a) * 16.0     # body centre -> bottom centre (mug is 32 tall)
        M.y = my + math.cos(a) * 16.0
        M.ang = ang
        M.hand_side = -1.0 if A.W[0] < mx else 1.0
        M.flip = M.hand_side > 0
        M.arm = A
        M.tilt = tilt
        R.mug = M
    return R


# --------------------------------------------------------------------------- public queries
def _to_stage(R, pt):
    q = R.MS.mapXY(pt.fX, pt.fY) if isinstance(pt, skia.Point) else R.MS.mapXY(pt[0], pt[1])
    return (q.fX, q.fY)


def head_center(pose: Pose):
    """Stage coords of the point between the eyes."""
    R = _solve(pose, None)
    x, y, _, _ = _hx(R.H, 0.0, 0.0)
    return _to_stage(R, R.MH.mapXY(x, y))


def mouth_pos(pose: Pose):
    """Stage coords of the centre of the mouth."""
    R = _solve(pose, None)
    x, y, _, _ = _hx(R.H, 0.0, MOUTH_Y)
    return _to_stage(R, R.MH.mapXY(x, y))


def hand_pos(pose: Pose, side: str):
    """Stage coords of the palm centre of Rae's 'l' or 'r' hand."""
    R = _solve(pose, None)
    A = R.arms[-1] if R.arms[-1].side == side else R.arms[1]
    return _to_stage(R, R.MU.mapXY(*A.palm))


def mug_pose(pose: Pose):
    """(x, y, scale, angle, flip) of the held mug in stage coords (bottom centre), or None.
    draw_mug(canvas, *mug_pose(pose)) reproduces the in-hand mug exactly."""
    R = _solve(pose, None)
    if R.mug is None:
        return None
    x, y = _to_stage(R, R.MU.mapXY(R.mug.x, R.mug.y))
    ang = (R.mug.ang + R.lean) * R.fac
    flip = R.mug.flip if R.fac > 0 else (not R.mug.flip)
    return (x, y, pose.scale, ang, flip)


# --------------------------------------------------------------------------- mug
def _mug_local(c, flip=False):
    """Mug in its own frame: bottom centre at origin, 32 tall, handle on +x (or -x if flip)."""
    if flip:
        c.scale(-1, 1)
    w, h = 13.0, 32.0
    hp = skia.Path()
    _cr(hp, [(w - 1, -26.0), (w + 8.5, -25.5), (w + 10.5, -17.0), (w + 7.0, -9.5), (w - 1, -8.5)])
    _stroke(c, hp, C_MUG_LINE, 6.6)
    _stroke(c, hp, C_MUG, 4.4)
    body = skia.Path()
    _cr(body, [(-w, -h), (-w, -12.0), (-w + 0.6, -3.0), (-w + 4.0, 0.0)])
    _cr(body, [(w - 4.0, 0.0), (w - 0.6, -3.0), (w, -12.0), (w, -h)], move=False)
    body.close()
    _fill(c, body, C_MUG_SH)
    c.save()
    c.clipPath(body, doAntiAlias=True)
    c.translate(-4.5, 0)
    _fill(c, body, C_MUG)
    c.restore()
    lx, ly = -1.5, -15.5
    c.drawCircle(lx, ly, 6.2, paint(C_LOGO, stroke=1.4))
    hp2 = skia.Path()
    hp2.moveTo(lx, ly + 3.6)
    hp2.cubicTo(lx - 5.2, ly - 0.4, lx - 3.0, ly - 4.6, lx, ly - 2.0)
    hp2.cubicTo(lx + 3.0, ly - 4.6, lx + 5.2, ly - 0.4, lx, ly + 3.6)
    hp2.close()
    _fill(c, hp2, C_LOGO)
    _stroke(c, body, C_MUG_LINE, 1.3, 0.9)
    rim = skia.Rect(-w, -h - 3.6, w, -h + 3.6)
    c.drawOval(rim, paint(C_MUG))
    c.drawOval(skia.Rect(-w + 2.2, -h - 2.2, w - 2.2, -h + 2.2), paint(C_COFFEE))
    c.drawOval(skia.Rect(-w + 4.0, -h - 1.2, -1.0, -h + 0.6), paint(WHITE, 0.18))
    c.drawOval(rim, paint(C_MUG_LINE, 0.9, stroke=1.2))
    c.drawRoundRect(skia.Rect(-w + 3.0, -h + 6.0, -w + 5.6, -6.0), 1.3, 1.3, paint(WHITE, 0.55))


def draw_mug(canvas, x, y, scale=1.0, angle=0.0, flip=False):
    """Rae's off-white mug (red heart-in-circle logo). (x, y) = bottom centre where it rests,
    `angle` degrees (rotation about the bottom centre), flip=True puts the handle on the left."""
    canvas.save()
    canvas.translate(x, y)
    canvas.rotate(angle)
    canvas.scale(scale, scale)
    _mug_local(canvas, flip)
    canvas.restore()


# --------------------------------------------------------------------------- hands
_HAND_CACHE = {}


def _hand_paths(shape):
    """[(path, kind)] in hand-local coords (wrist at 0,0, fingers toward +y, thumb toward +x)."""
    if shape in _HAND_CACHE:
        return _HAND_CACHE[shape]
    out = []
    if shape in ("relaxed", "hold"):
        main = smooth_path([(-7.2, -1.0), (-8.8, 8.5), (-9.2, 17.5), (-8.2, 26.0), (-5.2, 32.0), (-0.6, 34.6),
                            (3.4, 33.4), (5.0, 29.0), (5.4, 23.5), (7.2, 16.0), (8.4, 8.0), (7.4, 0.0)])
        out.append((main, "skin"))
        out.append((_curve([(-4.0, 20.5), (-3.8, 26.0), (-2.6, 31.0)]), "crease"))
        out.append((_curve([(0.0, 21.0), (0.4, 26.0), (1.6, 30.5)]), "crease"))
        out.append((skia.Simplify(_capsule(skia.Path(), (6.6, 8.0), (8.4, 20.5), 3.7, 2.9)), "skin"))
    elif shape in ("fist", "point"):
        main = smooth_path([(-7.6, -1.0), (-9.4, 9.0), (-9.6, 18.0), (-7.6, 24.6), (-2.0, 27.2), (4.4, 26.6),
                            (9.0, 21.5), (9.8, 12.0), (8.4, 2.0), (5.0, -1.6)])
        out.append((main, "skin"))
        out.append((_curve([(-8.0, 17.6), (-1.0, 19.6), (6.5, 18.6)]), "crease"))
        out.append((_curve([(-3.2, 19.4), (-2.9, 25.6)]), "crease"))
        out.append((_curve([(1.6, 19.6), (1.9, 26.0)]), "crease"))
        if shape == "point":
            out.append((skia.Simplify(_capsule(skia.Path(), (5.4, 18.0), (6.0, 40.0), 3.4, 2.8)), "skin"))
            out.append((_curve([(3.8, 28.5), (6.0, 29.5), (8.2, 28.8)]), "crease"))
        out.append((skia.Simplify(_capsule(skia.Path(), (8.8, 6.0), (4.2, 16.0), 3.9, 3.3)), "skin"))
    elif shape in ("open", "palm_out"):
        spread = 1.0 if shape == "open" else 1.5
        path = smooth_path([(-7.6, -1.0), (-9.4, 8.0), (-9.6, 16.5), (-4.0, 18.6), (4.0, 18.8), (9.0, 15.8),
                            (8.8, 5.0), (5.4, -1.6)])
        for fxp, ln, ang in ((-7.0, 13.0, -12.0), (-2.5, 16.5, -4.0), (2.1, 17.5, 3.0), (6.4, 15.5, 9.0)):
            a = ang * spread * D2R
            b = (fxp, 15.0)
            e = (fxp + math.sin(a) * ln, 15.0 + math.cos(a) * ln)
            _capsule(path, b, e, 2.95, 2.5)
        out.append((skia.Simplify(path), "palm" if shape == "palm_out" else "skin"))
        ta = (50.0 if shape == "open" else 64.0) * D2R
        out.append((skia.Simplify(_capsule(skia.Path(), (7.2, 4.5),
                                           (7.2 + math.sin(ta) * 13.5, 4.5 + math.cos(ta) * 13.5), 3.7, 3.0)), "skin"))
        if shape == "palm_out":
            out.append((_curve([(-6.5, 11.0), (0.0, 8.5), (6.0, 11.5)]), "crease"))
            out.append((_curve([(3.6, 1.5), (1.4, 7.0), (2.2, 13.0)]), "crease"))
        else:
            for x in (-4.6, -0.1, 4.3):
                out.append((_curve([(x, 9.0), (x + 0.3, 14.0)]), "crease"))
    elif shape == "palm_up":
        main = smooth_path([(-4.6, -1.0), (-5.6, 10.0), (-5.6, 22.0), (-4.6, 31.0), (-2.0, 35.6), (1.6, 35.0),
                            (3.0, 30.0), (4.0, 22.0), (6.0, 13.0), (6.2, 4.0), (3.6, -1.6)])
        out.append((main, "skin"))
        out.append((_curve([(2.6, 14.0), (2.4, 24.0), (1.2, 32.0)]), "palmline"))
        out.append((skia.Simplify(_capsule(skia.Path(), (4.6, 5.0), (10.0, 14.0), 3.4, 2.9)), "skin"))
    else:
        return _hand_paths("relaxed")
    _HAND_CACHE[shape] = out
    return out


def _draw_hand(c, A):
    W, hd, fx = A.W, A.hd, A.fx
    m = skia.Matrix.MakeAll(fx[0], hd[0], W[0], fx[1], hd[1], W[1], 0, 0, 1)
    c.save()
    c.concat(m)
    c.scale(HAND_S, HAND_S)
    for path, kind in _hand_paths(A.hand):
        if kind == "crease":
            _stroke(c, path, C_SKIN_SH, 1.1, 0.8)
        elif kind == "palmline":
            _stroke(c, path, C_PALM, 2.6, 0.9)
        else:
            base = C_PALM if kind == "palm" else C_SKIN
            _cel(c, path, base, C_SKIN_SH, -2.2, -1.4, line=C_SKIN_LINE, line_w=1.25, line_a=0.8)
    c.restore()


def _draw_held_mug(c, R):
    """Mug plus the gripping hand (fingers wrapped over the mug body)."""
    M = R.mug
    A = M.arm
    c.save()
    c.translate(M.x, M.y)
    c.rotate(M.ang)
    hs = M.hand_side
    a = -M.ang * D2R
    wx, wy = A.W[0] - M.x, A.W[1] - M.y
    wl = (wx * math.cos(a) - wy * math.sin(a), wx * math.sin(a) + wy * math.cos(a))
    c.save()
    _mug_local(c, flip=M.flip)
    c.restore()
    side_x = hs * 12.0
    hand = skia.Path()
    _capsule(hand, wl, (side_x + hs * 2.0, -16.0), 8.6, 11.0)
    _cel(c, hand, C_SKIN, C_SKIN_SH, -2.0, -1.5, line=C_SKIN_LINE, line_w=1.2, line_a=0.8)
    fingers = skia.Path()
    for fy, ln in ((-24.5, 14.0), (-17.5, 17.0), (-10.5, 16.5), (-4.0, 13.0)):
        x0 = side_x - hs * 1.0
        _capsule(fingers, (x0, fy), (x0 - hs * ln, fy + 0.6), 3.7, 3.3)
    _cel(c, fingers, C_SKIN, C_SKIN_SH, -1.6, -1.6, line=C_SKIN_LINE, line_w=1.15, line_a=0.85)
    th = _capsule(skia.Path(), (side_x + hs * 1.0, -25.5), (side_x - hs * 7.0, -31.0), 4.1, 3.5)
    _cel(c, th, C_SKIN, C_SKIN_SH, -1.5, -1.5, line=C_SKIN_LINE, line_w=1.15, line_a=0.85)
    c.restore()


# --------------------------------------------------------------------------- legs / hips / shoes
def _draw_leg(c, L, R):
    p = skia.Path()
    _capsule(p, L.hip, L.knee, 23.0, 16.5, bulge=1.2, bulge_at=0.4)
    _capsule(p, L.knee, L.ankle, 16.5, 13.0, bulge=0.8, bulge_at=0.35)
    kneel_order = R.k > 0.5
    if kneel_order:
        _draw_shoe(c, L, R)
    _cel(c, p, C_PANTS, C_PANTS_SH, -4.0, -2.0, line=C_PANTS_LINE, line_w=1.4, line_a=0.85)
    ax, ay = L.ankle
    kx, ky = L.knee
    ux, uy = _norm(ax - kx, ay - ky)
    nx, ny = -uy, ux
    hem = _curve([(ax - ux * 6 + nx * 11, ay - uy * 6 + ny * 11), (ax - ux * 3, ay - uy * 3),
                  (ax - ux * 6 - nx * 11, ay - uy * 6 - ny * 11)])
    _stroke(c, hem, C_PANTS_LINE, 1.1, 0.5)
    if R.sw > 0.3 or R.k > 0.3:
        hx_, hy_ = L.hip
        ux2, uy2 = _norm(kx - hx_, ky - hy_)
        _stroke(c, _curve([(kx - ux2 * 12 - uy2 * 8, ky - uy2 * 12 + ux2 * 8), (kx - ux2 * 4, ky - uy2 * 4),
                           (kx - ux2 * 12 + uy2 * 8, ky - uy2 * 12 - ux2 * 8)]), C_PANTS_SH, 1.6, 0.8)
    if not kneel_order:
        _draw_shoe(c, L, R)


_SHOE = [(-13.0, 7.0), (-1.0, 9.5), (8.0, 8.0), (18.0, 3.0), (31.0, -4.0), (40.0, -10.0), (43.5, -16.0),
         (41.0, -21.5), (32.0, -23.0), (-12.0, -23.0), (-16.5, -19.0), (-16.5, -8.0), (-15.0, 2.0)]
_SOLE = [(-16.8, -17.0), (42.6, -17.0), (43.2, -18.5), (41.0, -21.5), (32.0, -23.0), (-12.0, -23.0), (-16.5, -19.0)]
# cross-section slices (f, half-width, v_bottom, v_top) -> give the shoe its width in front views
_SLICES = [(-9.0, 11.5, -23.0, 8.0), (6.0, 12.5, -23.0, 8.0), (20.0, 12.5, -23.0, 1.0), (32.0, 11.0, -23.0, -6.0),
           (39.0, 8.5, -22.0, -11.0)]


def _draw_shoe(c, L, R):
    """Sneaker-boot: side profile in the side plane (f forward, v up) relative to the ankle, rotated by the
    foot angle (and the toe tap about the heel), projected with the body turn; slices add width."""
    s, cc = R.sl, R.cl
    ang = L.foot_ang * D2R
    tap = L.tap * D2R
    ca_, sa_ = math.cos(ang), math.sin(ang)
    ct_, st_ = math.cos(tap), math.sin(tap)

    def tf(f, v):
        if tap:
            hf, hv = -14.0, -23.0
            f0, v0 = f - hf, v - hv
            f, v = hf + f0 * ct_ - v0 * st_, hv + f0 * st_ + v0 * ct_
        return f * ca_ - v * sa_, f * sa_ + v * ca_

    ax, ay = L.ankle
    prof = [tf(f, v) for f, v in _SHOE]
    sole = [tf(f, v) for f, v in _SOLE]
    rotated = abs(L.foot_ang) > 12.0 or abs(L.tap) > 6.0
    lats = (-11.0, 0.0, 11.0) if (abs(s) > 0.15 and not rotated) else (0.0,)
    pieces, soles = [], []
    for lat in lats:
        pieces.append(smooth_path([(ax + lat * cc + f * s, ay - v) for f, v in prof], closed=True))
        soles.append(smooth_path([(ax + lat * cc + f * s, ay - v) for f, v in sole], closed=True, tension=0.3))
    if abs(cc) > 0.3 and not rotated:
        # cross-section slices swept sideways give the shoe width in front views
        for f, w, vb, vt in _SLICES:
            hw = w * abs(cc)
            fb, vb2 = tf(f, vb + 2.0)
            ft, vt2 = tf(f, vt - 2.0)
            x0, y0, x1, y1 = ax + fb * s, ay - vb2, ax + ft * s, ay - vt2
            q = skia.Path()
            q.addRRect(skia.RRect.MakeRectXY(skia.Rect(min(x0, x1) - hw, min(y0, y1) - 2.0, max(x0, x1) + hw,
                                                       max(y0, y1) + 2.0), min(hw, 7.0), 6.0))
            pieces.append(q)
            q2 = skia.Path()
            q2.addRRect(skia.RRect.MakeRectXY(skia.Rect(min(x0, x1) - hw + 0.5, y0 - 3.5, max(x0, x1) + hw - 0.5,
                                                        y0 + 2.0), 3.0, 3.0))
            soles.append(q2)
    pl = paint(C_SHOE_LINE, stroke=2.6)
    for q in pieces:
        c.drawPath(q, pl)
    pf = paint(C_SHOE)
    for q in pieces:
        c.drawPath(q, pf)
    ps = paint(C_SOLE)
    for q in soles:
        c.drawPath(q, ps)
    tfx, tfv = tf(28.0, -8.0)
    c.drawOval(skia.Rect(ax + tfx * s - 6, ay - tfv - 3.5, ax + tfx * s + 4, ay - tfv + 1.5), paint(WHITE, 0.10))
    if abs(s) > 0.25 and not rotated:
        f1, v1 = tf(9.0, 5.5)
        f2, v2 = tf(23.0, -0.5)
        lat = 11.0 * cc
        for kk in (0.0, 0.5, 1.0):
            fx_ = lerp(f1, f2, kk)
            fv_ = lerp(v1, v2, kk)
            c.drawLine(ax + lat + fx_ * s - 2.5, ay - fv_ - 1.5, ax + lat + fx_ * s + 2.5, ay - fv_ + 1.5,
                       paint(C_SOLE, 0.55, stroke=1.2))


def _draw_hips(c, R):
    s, cc = R.s, R.c
    hv = R.hv

    def edge(x, y, b):
        sg = 1 if x > 0 else -1
        return (sg * math.sqrt(x * x * cc * cc + b * b * s * s), y - hv)

    def surf(x, y, z):
        return (x * cc + z * s, y - hv)

    pts = [edge(-47, -40, 28), edge(-53, -6, 31), edge(-50, 20, 30), surf(-24, 42, 20), surf(0, 38, 30),
           surf(24, 42, 20), edge(50, 20, 30), edge(53, -6, 31), edge(47, -40, 28)]
    p = smooth_path(pts, closed=True)
    _cel(c, p, C_PANTS, C_PANTS_SH, -4.0, -2.5, line=C_PANTS_LINE, line_w=1.4, line_a=0.85)


# --------------------------------------------------------------------------- torso / neck / arms
def _torso_geo(R):
    s, cc = R.s, R.c
    su = R.su
    br = R.br

    def edge(x, y, b):
        sg = 1 if x > 0 else -1
        return (sg * math.sqrt(x * x * cc * cc + b * b * s * s), y)

    def surf(x, y, z):
        return (x * cc + z * s, y)

    def chest(pt):
        x, y = pt
        if y < -76:
            return (x * (1 + 0.008 * br), y - br * 1.1)
        return pt
    nk = 4.0 * s
    hem_up = 8.0 * R.sw
    out = [
        (nk - 19.0, -151.0 - su * 5),
        surf(-40, -147 - su * 9, 8),
        edge(-60, -131 - su * 12, 24),
        edge(-58.5, -104, 30),
        edge(-55, -84, 34),
        edge(-46.5, -46, 28),
        edge(-51.5, -8, 31),
        edge(-53.5, 14 - hem_up, 31),
        surf(0, 17 - hem_up, 33),
        edge(53.5, 14 - hem_up, 31),
        edge(51.5, -8, 31),
        edge(46.5, -46, 28),
        edge(55, -84, 34),
        edge(58.5, -104, 30),
        edge(60, -131 - su * 12, 24),
        surf(40, -147 - su * 9, 8),
        (nk + 19.0, -151.0 - su * 5),
        (nk + 9.0 + 14 * s, -141.0),
        surf(0, -137.5, 22),
        (nk - 9.0 + 14 * s, -141.0),
    ]
    out = [chest(q) for q in out]
    if s > 0.05:
        out[12] = (out[12][0] + 3.0 * s, out[12][1])
    near_e = [chest(surf(x, y, z)) for x, y, z in [(-13, -147, 20), (-17, -120, 31), (-19, -84, 33),
                                                     (-18, -44, 27), (-16, 15 - hem_up, 32)]]
    far_e = [chest(surf(x, y, z)) for x, y, z in [(13, -147, 20), (17, -120, 31), (19, -84, 33),
                                                    (18, -44, 27), (16, 15 - hem_up, 32)]]
    return out, near_e, far_e


def _draw_torso(c, R):
    s = R.s
    out, near_e, far_e = _torso_geo(R)
    torso = smooth_path(out, closed=True, tension=0.45)
    _cel(c, torso, C_JACKET, C_JACKET_SH, -5.0 - 7.0 * max(s, 0), -3.0, blur=0.0)
    if R.back:
        _stroke(c, torso, C_JACKET_LINE, 1.5, 0.85)
        return
    neck_mid = out[18]
    band = skia.Path()
    _cr(band, near_e)
    _cr(band, far_e[::-1], move=False)
    _cr(band, [far_e[0], out[17], neck_mid, out[19], near_e[0]], move=False)
    band.close()
    c.save()
    c.clipPath(torso, doAntiAlias=True)
    _fill(c, band, C_SHIRT)
    c.save()
    c.clipPath(band, doAntiAlias=True)
    y_ub = -70.0 - R.br
    c.drawRect(skia.Rect(-80, y_ub - 4, 80, y_ub + 9), paint(C_SHIRT_SH, 0.45, blur=4))
    sh = skia.Path()
    _cr(sh, [(x - 1.0, y) for x, y in far_e])
    _cr(sh, [(x - 7.5, y) for x, y in far_e[::-1]], move=False)
    sh.close()
    _fill(c, sh, C_SHIRT_SH, 0.75, blur=1.5)
    c.drawOval(skia.Rect(neck_mid[0] - 24, neck_mid[1] - 10, neck_mid[0] + 24, neck_mid[1] + 7),
               paint(C_SHIRT_SH, 0.6, blur=3))
    c.restore()
    _stroke(c, _curve([out[17], neck_mid, out[19]]), C_SHIRT_SH, 2.4, 0.9)
    for e, sg in ((near_e, -1), (far_e, 1)):
        _stroke(c, _curve(e), C_JACKET_LINE, 3.0, 0.95)
        _stroke(c, _curve([(x + sg * 1.6, y) for x, y in e[1:]]), C_ZIP, 1.0, 0.55)
    # stand-up collar ends, folded open at the front
    for e, sg, top in ((near_e, -1, out[0]), (far_e, 1, out[16])):
        x0, y0 = e[0]
        k = 1.0 if sg < 0 else max(0.45, R.c)
        flap = smooth_path([(x0 - sg * 0.5, y0 - 1.0), (top[0] + sg * 2.0, top[1] - 6.0),
                            (top[0] + sg * 9.0 * k, top[1] - 3.0), (x0 + sg * 12.0 * k, y0 + 9.0),
                            (x0 + sg * 3.0 * k, y0 + 14.0)], closed=True, tension=0.4)
        _fill(c, flap, C_JACKET_HI)
        _stroke(c, flap, C_JACKET_LINE, 1.2, 0.85)
    if s < 0.75:
        px = -36.0 * R.c + 20 * s
        _stroke(c, _curve([(px - 9, -22), (px + 4, -10)]), C_JACKET_LINE, 2.0, 0.7)
    c.restore()
    _stroke(c, torso, C_JACKET_LINE, 1.5, 0.85)


def _draw_neck(c, R):
    s = R.s
    nx = 4.0 * s
    collar = smooth_path([(nx - 27, -146), (nx - 25, -163), (nx, -169), (nx + 25, -163), (nx + 27, -146),
                          (nx, -150)], closed=True)
    _fill(c, collar, C_JACKET_SH)
    _stroke(c, collar, C_JACKET_LINE, 1.2, 0.8)
    neck = skia.Path()
    neck.addRRect(skia.RRect.MakeRectXY(skia.Rect(nx - 16.5, -205.0, nx + 16.5, -133.0), 8, 8))
    _fill(c, neck, C_SKIN)
    c.save()
    c.clipPath(neck, doAntiAlias=True)
    # jaw shadow falls on the neck (drawn in the head frame so it follows tilts)
    c.concat(R.MHr)
    chin_y = 68.0 + _jaw_dy(R.H, 68.0)
    cx = 30.0 * R.H.s
    c.drawOval(skia.Rect(cx - 52, chin_y - 40, cx + 52, chin_y + 13), paint(C_SKIN_SH, 0.95, blur=3.0))
    c.restore()
    c.save()
    c.clipPath(neck, doAntiAlias=True)
    c.drawRect(skia.Rect(nx + 8.0, -210, nx + 30, -120), paint(C_SKIN_SH, 0.5, blur=3.0))
    c.restore()
    _stroke(c, neck, C_SKIN_LINE, 1.2, 0.55)


def _limb_band(a, b, u0, u1, r):
    """Rounded band across the segment a->b between fractions u0..u1 with half-width r."""
    ux, uy = _norm(b[0] - a[0], b[1] - a[1])
    nx, ny = -uy, ux
    p0 = (a[0] + (b[0] - a[0]) * u0, a[1] + (b[1] - a[1]) * u0)
    p1 = (a[0] + (b[0] - a[0]) * u1, a[1] + (b[1] - a[1]) * u1)
    pts = [(p0[0] + nx * r, p0[1] + ny * r), (p1[0] + nx * (r + 0.5), p1[1] + ny * (r + 0.5)),
           (p1[0] + ux * 1.2, p1[1] + uy * 1.2),
           (p1[0] - nx * (r + 0.5), p1[1] - ny * (r + 0.5)), (p0[0] - nx * r, p0[1] - ny * r),
           (p0[0] - ux * 1.2, p0[1] - uy * 1.2)]
    return smooth_path(pts, closed=True, tension=0.25)


def _arm_occluder(A, R):
    """Rough silhouette (upper-body frame) of an arm drawn over the face, to mask eye glints."""
    S, E, W = A.S, A.E, A.W
    occ = skia.Path()
    _capsule(occ, S, E, 16.0, 15.0)
    _capsule(occ, E, W, 11.0, 8.0)
    occ.addCircle(A.palm[0], A.palm[1], 15.0 * HAND_S, skia.PathDirection.kCCW)
    if R.mug is not None and R.mug.arm is A:
        m = skia.Matrix()
        m.setRotate(R.mug.ang, R.mug.x, R.mug.y)
        mp = skia.Path()
        mp.addRect(skia.Rect(R.mug.x - 24, R.mug.y - 37, R.mug.x + 24, R.mug.y + 1))
        mp.transform(m)
        occ.addPath(mp)
    return occ


def _draw_arm(c, A, R):
    S, E, W = A.S, A.E, A.W
    ux, uy = _norm(E[0] - S[0], E[1] - S[1])
    fore = skia.Path()
    _capsule(fore, (E[0] - ux * 2, E[1] - uy * 2), W, 10.8, 7.6, bulge=1.4, bulge_at=0.3)
    _cel(c, fore, C_SKIN, C_SKIN_SH, -3.0, -2.0, line=C_SKIN_LINE, line_w=1.25, line_a=0.75)
    if R.mug is not None and R.mug.arm is A:
        _draw_held_mug(c, R)
    else:
        _draw_hand(c, A)
    sl = skia.Path()
    Ee = (E[0] + ux * 4, E[1] + uy * 4)
    _capsule(sl, S, Ee, 15.0, 13.6, bulge=1.0, bulge_at=0.35)
    _cel(c, sl, C_JACKET, C_JACKET_SH, -4.0, -2.5, line=C_JACKET_LINE, line_w=1.4, line_a=0.85)
    _stroke(c, _curve([(E[0] - ux * 14 - uy * 7, E[1] - uy * 14 + ux * 7), (E[0] - ux * 9, E[1] - uy * 9),
                       (E[0] - ux * 12 + uy * 6, E[1] - uy * 12 - ux * 6)]), C_JACKET_SH, 1.4, 0.8)
    seg_len = max(1.0, math.hypot(Ee[0] - S[0], Ee[1] - S[1]))
    u0 = 1.0 - 11.0 / seg_len
    cuff = _limb_band(S, Ee, u0, 1.0, 15.2)
    _cel(c, cuff, C_JACKET_HI, C_JACKET, -2.0, -2.0, line=C_JACKET_LINE, line_w=1.3, line_a=0.85)
    um = lerp(u0, 1.0, 0.5)
    mx, my = S[0] + (Ee[0] - S[0]) * um, S[1] + (Ee[1] - S[1]) * um
    _stroke(c, _curve([(mx - uy * 14.5, my + ux * 14.5), (mx + ux * 0.8, my + uy * 0.8),
                       (mx + uy * 14.5, my - ux * 14.5)]), C_JACKET_LINE, 1.0, 0.55)
    if A.o < 0 and A.layer == "front" and R.s < 0.65 and not R.back:
        px, py = S[0] + ux * 30 - uy * 3, S[1] + uy * 30 + ux * 3
        c.drawCircle(px, py, 5.2, paint(C_PATCH))
        c.drawCircle(px, py, 5.2, paint(C_JACKET_LINE, 0.8, stroke=1.0))
        c.drawCircle(px - 0.8, py - 0.8, 1.6, paint(WHITE, 0.85))


# --------------------------------------------------------------------------- eyes
def _bump(s, pk, e):
    q = (s - pk) / (1.0 - pk) if s >= pk else (s - pk) / (1.0 + pk)
    v = 1.0 - q * q
    return v ** e if v > 0 else 0.0


_SS = [-1.0, -0.82, -0.6, -0.36, -0.12, 0.12, 0.36, 0.6, 0.8, 0.93, 1.0]
_PU = [_bump(s, -0.1, 0.6) for s in _SS]
_PL = [_bump(s, 0.15, 0.75) for s in _SS]
_BASE = [lerp(2.2, -2.6, (s + 1) / 2) for s in _SS]


_OUTER = [smoothstep((s - 0.15) / 0.7) for s in _SS]     # weight of the outer third of the eye


def _eye_curves(op, squint, wide, gy, worry=0.0):
    hu = HU0 * (1.0 + 0.6 * wide)
    hl = HL0 * (1.0 + 0.14 * wide)
    if gy > 0:
        hu *= 1.0 - 0.28 * gy
    else:
        hu *= 1.0 - 0.1 * gy
    U, LL = [], []
    for b, pu, pl, wo in zip(_BASE, _PU, _PL, _OUTER):
        # worry: the outer third of the upper lid droops (sad eyes), the lower lid follows a little
        u = b - hu * pu + worry * 3.4 * wo * pu
        l_ = b + hl * pl - squint * (hl + 0.45 * HU0) * (pl ** 0.9) - max(0.0, -gy) * 1.4 * pl
        l_ += worry * 1.6 * wo * squint
        l_ = max(l_, u + 0.6 * pu)
        U.append(u)
        LL.append(l_)
    ope = clamp(op) * (1.0 - 0.16 * squint)
    UL = [l_ + (u - l_) * ope for u, l_ in zip(U, LL)]
    return U, LL, UL, ope


def _draw_eye(c, H, P, slot, t):
    """slot = -1 (eye at local -x) or +1. P = per-eye params."""
    x0 = slot * EX
    ex, ey, dep, fs = _hx(H, x0, 0.0)
    if dep < -6:
        return
    sd = float(slot)
    U, LL, UL, ope = _eye_curves(P.lid, P.squint, P.wide, P.gy, P.bworry)
    # far eye near the silhouette: squash its outer half so the corner (and lash flick) stays inside the
    # cheek outline instead of being sliced by it
    fso = fs
    far = slot * H.s > 0.02
    if far:
        lim = sd * _sil_x(H, -2.0, slot) - 5.0
        fso = clamp((lim - sd * ex) / (EW + 2.0), 0.12, fs)
    P.gsc = fso / max(fs, 1e-3) if far else 1.0

    def m(u, v):
        return (ex + sd * u * (fso if u > 0 else fs), ey + v)

    us = [s * EW for s in _SS]
    pU = [m(u, v) for u, v in zip(us, U)]
    pLL = [m(u, v) for u, v in zip(us, LL)]
    pUL = [m(u, v) for u, v in zip(us, UL)]
    # under-eye: tired shading + sniffle puffiness
    bag = _closed2([(x, y + 2.0) for x, y in pLL[2:-1]], [(x, y + 6.0 + 2.0 * P.sniffle) for x, y in pLL[2:-1]][::-1])
    _fill(c, bag, C_SKIN_SH, 0.2 + 0.12 * P.sniffle, blur=2.0)
    if P.sniffle > 0:
        _fill(c, bag, C_BLUSH, 0.45 * P.sniffle, blur=2.2)
        _stroke(c, _curve([(x, y + 4.8 + 1.5 * P.sniffle) for x, y in pLL[3:-2]]), C_SKIN_SH, 1.2, 0.45 * P.sniffle)
    # socket shading above the lid (form of the brow ridge)
    sock = _closed2([(x, y - 2.0) for x, y in pU[1:-1]], [(x, y - 8.0) for x, y in pU[1:-1]][::-1])
    _fill(c, sock, C_SKIN_SH, 0.22, blur=2.5)
    # lid skin that came down over the eye
    if ope < 0.985:
        lid = _closed2(pU, pUL[::-1])
        _fill(c, lid, C_LID)
    crease = [m(u, v - 4.4 - 1.0 * pu - 1.6 * P.wide) for u, v, pu in zip(us[1:-1], U[1:-1], _PU[1:-1])]
    _stroke(c, _curve(crease), C_SKIN_DEEP, 1.3, 0.55 * (0.45 + 0.55 * ope))
    closed = ope < 0.03
    if not closed:
        opening = _closed2(pUL, pLL[::-1])
        _fill(c, opening, C_SCLERA)
        c.save()
        c.clipPath(opening, doAntiAlias=True)
        c.drawCircle(m(-EW, 0)[0], ey, 7.5, paint(C_SCLERA_SH, 0.35, blur=4))
        c.drawCircle(m(EW, 0)[0], ey - 1, 7.5, paint(C_SCLERA_SH, 0.3, blur=4))
        if P.sniffle > 0:
            c.drawCircle(m(-EW + 2, 1)[0], ey + 1, 6.5, paint("#E08A84", 0.5 * P.sniffle, blur=3))
            c.drawCircle(m(EW - 2, 1)[0], ey + 1, 5.5, paint("#E08A84", 0.3 * P.sniffle, blur=3))
        fsi = lerp(1.0, fs, 0.6)
        ix = ex + P.gx * 7.0 * (fso if P.gx * sd > 0 else fs)
        if far:     # keep the iris centre inside the squashed outer corner
            ix = sd * min(sd * ix, sd * ex + EW * fso - 1.5)
        iy = ey + 0.6 + P.gy * 3.6
        rx, ry = RI * fsi, RI
        iris = skia.Rect(ix - rx, iy - ry, ix + rx, iy + ry)
        c.drawOval(iris, paint(C_IRIS))
        ip = skia.Path()
        ip.addOval(iris)
        c.save()
        c.clipPath(ip, doAntiAlias=True)
        c.drawOval(skia.Rect(ix - rx * 0.78, iy - ry * 0.78, ix + rx * 0.78, iy + ry * 0.78), paint(C_IRIS_MID, blur=1.6))
        c.drawOval(skia.Rect(ix - rx * 0.8, iy + 0.5, ix + rx * 0.8, iy + ry * 1.2),
                   paint(C_IRIS_LT, 0.8 + 0.2 * P.shine, blur=2.6))
        pr = 4.5 * P.pupil
        c.drawOval(skia.Rect(ix - pr * fsi, iy - pr + 0.3, ix + pr * fsi, iy + pr + 0.3), paint(C_PUPIL))
        if P.shine > 0:
            c.drawOval(skia.Rect(ix - rx * 0.76, iy - ry * 0.76, ix + rx * 0.76, iy + ry * 0.76),
                       paint(C_IRIS_LT, 0.5 * P.shine, stroke=1.2))
        c.restore()
        c.drawOval(iris, paint(C_PUPIL, 0.75, stroke=1.2))
        shadow = _closed2(pUL, [(x, y + 5.0) for x, y in pUL[::-1]])
        _fill(c, shadow, C_SCLERA_SH, 0.75, blur=1.8)
        if P.tears > 0:
            pool = _closed2([(x, y - 2.8 * P.tears) for x, y in pLL[1:-1]], pLL[1:-1][::-1])
            _fill(c, pool, C_TEAR, 0.5 * P.tears)
        glint = (lambda cc, ix=ix, iy=iy, fsi=fsi, P=P: _eye_glints(cc, ix, iy, fsi, P))
        glint(c)
        c.restore()
        if P.emit is not None:
            P.emit.append((opening, glint))
        _stroke(c, _curve(pLL[3:]), C_LASH, 1.3, 0.5 * clamp(ope * 3))
        if P.sniffle > 0:
            _stroke(c, _curve(pLL[2:]), "#B45A50", 1.6, 0.55 * P.sniffle)
        if P.tears > 0:
            _stroke(c, _curve([(x, y - 1.0) for x, y in pLL[2:-1]]), WHITE, 1.2, 0.85 * P.tears)
            _stroke(c, _curve([(x, y + 0.7) for x, y in pLL[1:-1]]), C_TEAR, 1.8, 0.6 * P.tears)

    def lash(c):
        # lash line (upper lid edge) with an outer flick
        th = [lerp(1.0, 4.0, ((s + 1) / 2) ** 0.5) for s in _SS]
        if closed:
            th = [w * 0.85 for w in th]
        base = pUL
        top = [(x, y - w) for (x, y), w in zip(base, th)]
        bo = _BASE[-1]
        # the flick keeps some length on the far eye so it can poke past the cheek silhouette
        fk = max(fso, min(fs + 0.2, 0.8)) if far else fs
        e0 = m(EW, 0.0)[0]
        flick_tip = (e0 + sd * 6.0 * fk, ey + bo - 4.6 - 1.4 * P.wide + (1.5 if closed else 0.0))
        lash = skia.Path()
        _cr(lash, base)
        q1 = (e0 + sd * 2.8 * fk, ey + bo - 0.6)
        lash.quadTo(q1[0], q1[1], flick_tip[0], flick_tip[1])
        q2 = (e0 + sd * 1.0 * fk, ey + bo - 4.4 - P.wide)
        lash.quadTo(q2[0], top[-1][1] - 0.6, top[-1][0], top[-1][1])
        _cr(lash, top[::-1], move=False)
        lash.close()
        _fill(c, lash, C_LASH)
        if not closed:
            for k, (u, ln, ang) in enumerate(((0.66, 2.8, -40.0), (0.86, 3.6, -22.0))):
                i = min(range(len(_SS)), key=lambda j: abs(_SS[j] - u))
                px, py = top[i]
                dx = math.cos(ang * D2R) * ln * sd * fs
                dy = math.sin(ang * D2R) * ln
                _fill(c, _ribbon([(px - sd * 0.8 * fs, py + 0.8), (px + dx * 0.6, py + dy * 0.6), (px + dx, py + dy)],
                                 [1.6, 1.1, 0.3]), C_LASH)
        if closed:
            for u in (0.3, 0.62, 0.9):
                i = min(range(len(_SS)), key=lambda j: abs(_SS[j] - u))
                px, py = base[i]
                _stroke(c, _curve([(px, py), (px + sd * 1.4 * fs, py + 2.8)]), C_LASH, 1.0, 0.7)
        if ope < 0.4 and P.squint > 0.35:
            # squeezed shut: little creases fanning from the outer corner
            k = clamp((P.squint - 0.35) / 0.4) * clamp((0.4 - ope) / 0.3)
            ox_, oy_ = m(EW * 0.95, LL[-1])
            for dy_, ln in ((3.4, 6.0), (7.4, 4.6)):
                _stroke(c, _curve([(ox_ - sd * 1.0 * fs, oy_ + dy_ - 1.6), (ox_ + sd * ln * 0.55 * fso, oy_ + dy_),
                                   (ox_ + sd * ln * fso, oy_ + dy_ - 1.8)]), C_SKIN_DEEP, 1.2, 0.55 * k)

    if getattr(P, "lash_out", None) is not None:
        P.lash_out.append(lash)
    else:
        lash(c)
    if P.tear_roll > 0:
        _draw_tear(c, H, slot, P.tear_roll)


def _eye_glints(c, ix, iy, fsi, P):
    """Catch-lights / wet glints (also replayed un-darkened in low light)."""
    big = 1.0 + 0.45 * P.tears + 0.25 * P.shine
    g = getattr(P, "gsc", 1.0)      # < 1 on the squashed far eye: keep the glint off the outer corner
    hx, hy = ix + 3.4 * fsi * g - (1.0 - g) * 1.5, iy - 4.0
    c.drawOval(skia.Rect(hx - 3.3 * big * fsi, hy - 2.8 * big, hx + 3.3 * big * fsi, hy + 2.8 * big), paint(WHITE, 0.97))
    sm = 1.0 + 0.35 * P.tears
    c.drawCircle(ix - 3.6 * fsi, iy + 3.8, 1.4 * sm, paint(WHITE, 0.9))
    if P.tears > 0:
        arc = skia.Path()
        arc.addArc(skia.Rect(ix - (RI - 2.4) * fsi, iy - RI + 2.4, ix + (RI - 2.4) * fsi, iy + RI - 2.4), 25, 130)
        _stroke(c, arc, WHITE, 1.4, 0.55 * P.tears)
        c.drawCircle(ix + 5.0 * fsi, iy + 2.4, 0.9 * P.tears + 0.25, paint(WHITE, 0.85 * P.tears))
    if P.shine > 0:
        sx, sy = ix - 5.0 * fsi, iy - 5.4
        r = 3.0 * P.shine
        star = skia.Path()
        star.moveTo(sx, sy - r)
        star.quadTo(sx, sy, sx + r * 0.75, sy)
        star.quadTo(sx, sy, sx, sy + r)
        star.quadTo(sx, sy, sx - r * 0.75, sy)
        star.quadTo(sx, sy, sx, sy - r)
        _fill(c, star, WHITE, 0.9)


def _draw_tear(c, H, slot, prog):
    """A droplet rolling from the lower lid down the cheek, leaving a shiny trail."""
    pts = []
    for x0, y in ((slot * (EX + 4.0), 11.5), (slot * (EX + 6.5), 21.0), (slot * (EX + 7.5), 32.0),
                  (slot * (EX + 5.0), 44.0), (slot * (EX + 0.5), 55.0)):
        x, yy, _, _ = _hx(H, x0, y, 1.0)
        pts.append((x, yy))
    path = _curve(pts)
    meas = skia.PathMeasure(path, False)
    total = meas.getLength()
    p = clamp(prog)
    d = total * min(1.0, p * 1.08)
    if d < 1:
        return
    seg = skia.Path()
    meas.getSegment(0, d, seg, True)
    fade = 1.0 - smoothstep((p - 0.88) / 0.12)
    _stroke(c, seg, C_TEAR, 3.2, 0.45)
    _stroke(c, seg, WHITE, 1.1, 0.7)
    pos, _ = meas.getPosTan(d)
    x, y = pos.fX, pos.fY
    r = 3.0 + 0.7 * min(1.0, p * 3)
    drop = skia.Path()
    drop.moveTo(x, y - r * 2.1)
    drop.cubicTo(x + r * 0.5, y - r * 1.0, x + r, y - r * 0.2, x + r, y + r * 0.35)
    drop.cubicTo(x + r, y + r * 1.25, x - r, y + r * 1.25, x - r, y + r * 0.35)
    drop.cubicTo(x - r, y - r * 0.2, x - r * 0.5, y - r * 1.0, x, y - r * 2.1)
    drop.close()
    _fill(c, drop, C_TEAR, 0.88 * fade)
    _stroke(c, drop, "#7FB3D6", 0.9, 0.75 * fade)
    c.drawCircle(x - r * 0.35, y - r * 0.05, r * 0.38, paint(WHITE, 0.95 * fade))


def _draw_brow(c, H, P, slot):
    x0 = slot * EX
    ex, _, dep, fs = _hx(H, x0, -24.0)
    if dep < -6:
        return
    ey = H.nod_dy * (dep / 60.0)
    sd = float(slot)
    r, w, f = P.braise, P.bworry, P.bfurrow
    fso = fs
    if slot * H.s > 0.02:
        lim = sd * _sil_x(H, -24.0, slot) - 2.5
        fso = clamp((lim - sd * ex) / (EW * 1.18), 0.2, fs)
    pts, ths = [], []
    n = 7
    for i in range(n):
        s = i / (n - 1)
        u = lerp(-EW * 0.92, EW * 1.18, s)
        # worry flattens the arch and tilts the whole brow (inner end up, outer end down)
        v = -23.5 - 4.2 * (1.0 - 0.45 * w) * math.sin(math.pi * min(1.0, s * 1.08)) + 1.6 * s
        th = lerp(6.4, 1.6, s ** 1.1)
        if r >= 0:
            v -= r * (6.5 + 2.8 * math.sin(math.pi * s))
        else:
            v -= r * 5.0
        v -= w * 10.5 * (1 - s) ** 1.25
        v += w * 4.2 * s ** 1.3
        u -= w * 1.4 * (1 - s)
        v += f * 6.8 * (1 - s) ** 1.5
        v -= f * 1.4 * s
        u -= f * 3.0 * (1 - s)
        th *= 1.0 + 0.12 * f + 0.1 * w * (1 - s)
        v += P.squint * 2.0
        pts.append((ex + sd * u * (fso if u > 0 else fs), ey + v))
        ths.append(th)
    p0, p1 = pts[0], pts[1]
    dx, dy = _norm(p0[0] - p1[0], p0[1] - p1[1])
    pts.insert(0, (p0[0] + dx * 2.0, p0[1] + dy * 2.0 + 0.6))
    ths.insert(0, ths[0] * 0.8)
    path = _ribbon(pts, ths)
    _fill(c, path, C_BROW)
    _stroke(c, _curve([(x, y - 0.8) for x, y in pts[2:5]]), C_HAIR_HI, 1.0, 0.4)


# --------------------------------------------------------------------------- nose / mouth / ears
def _draw_nose(c, H, P):
    s = H.s
    tx, ty, _, _ = _hx(H, 0.0, 22.5, 8.0 + 4.0 * smoothstep((abs(s) - 0.3) / 0.4))
    nd = H.nod_dy * 0.95
    bx = _hx(H, 0.0, 6.0, 3.0)[0]
    side = _curve([(bx + 3.0 + 1.5 * s, 0.0 + nd), (tx + 4.5 + 1.2 * s, 13.0 + nd), (tx + 5.5, 20.5 + nd)])
    _stroke(c, side, C_SKIN_SH, 4.5, 0.32 + 0.25 * min(1.0, abs(s) * 2), blur=2.0)
    c.drawOval(skia.Rect(tx - 6.0 + 3.0 * s, 24.0 + nd, tx + 7.5 + 2.0 * s, 29.5 + nd), paint(C_SKIN_SH, 0.5, blur=2.2))
    pts = []
    for x0, y, dz in ((-6.6, 21.6, 2.0), (-7.4, 24.4, 3.0), (-5.0, 26.6, 5.0), (-1.8, 26.9, 8.0), (0.8, 26.3, 9.0)):
        x, yy, _, _ = _hx(H, x0, y, dz)
        pts.append((x, yy))
    _stroke(c, _curve(pts), C_SKIN_LINE, 1.6, 0.72)
    pts2 = []
    for x0, y, dz in ((2.8, 26.7, 8.0), (5.6, 26.2, 5.0), (7.2, 23.6, 2.5)):
        x, yy, _, _ = _hx(H, x0, y, dz)
        pts2.append((x, yy))
    _stroke(c, _curve(pts2), C_SKIN_LINE, 1.6, 0.5 * clamp(1 - s * 1.6))
    for x0 in (-3.6, 3.6):
        x, yy, dep, fs = _hx(H, x0, 25.6, 5.5)
        if x0 > 0 and s > 0.35:
            continue
        c.drawOval(skia.Rect(x - 1.8 * fs, yy - 0.9, x + 1.8 * fs, yy + 0.9), paint(C_SKIN_LINE, 0.45))
    c.drawOval(skia.Rect(tx - 4.8, ty - 4.0, tx + 0.8, ty - 0.6), paint(C_SKIN_HI, 0.65, blur=1.0))
    if P.sniffle > 0:
        c.drawCircle(tx + 0.5, ty + 1.5, 8.5, paint(C_BLUSH, 0.6 * P.sniffle, blur=4.0))


def _draw_mouth(c, H, p, t):
    y0 = MOUTH_Y
    op = clamp(p.mouth_open)
    rd = clamp(p.mouth_round)
    sm = clamp(p.smile, -1.0, 1.0)
    sk = clamp(p.smirk, -1.0, 1.0)
    tr = clamp(p.mouth_tremble)
    W = 15.0 * (1 + 0.24 * max(sm, 0) - 0.05 * max(-sm, 0)) * (1 - 0.42 * rd) * (1 + 0.08 * op) * (1 - 0.1 * tr)
    qL = qR = qM = 0.0
    if tr > 0 and t is not None:
        qL = noise1(t * 13.0, 5) * tr * 1.6
        qR = noise1(t * 12.0, 9) * tr * 1.6
        qM = noise1(t * 16.0, 2) * tr * 2.0
    cyL = y0 - sm * 4.8 + tr * 2.0 + qL + max(sk, 0) * 1.0 - max(-sk, 0) * 5.6
    cyR = y0 - sm * 4.8 + tr * 2.0 + qR - max(sk, 0) * 5.6 + max(-sk, 0) * 1.0
    cxL = -W - max(-sk, 0) * 2.0
    cxR = W + max(sk, 0) * 2.0
    up_m = y0 - 0.6 - op * (2.6 + 2.8 * rd) - max(sm, 0) * 0.8 * op
    lo_m = y0 + 0.8 + op * 16.5 * (1 - 0.18 * rd) + max(sm, 0) * op * 3.0 + qM
    lo_m = max(lo_m, up_m + 0.8)
    # round shapes morph toward an ellipse: corners at mid height, quarter points on the ellipse (O / OO)
    yc, hb = (up_m + lo_m) * 0.5, (lo_m - up_m) * 0.5
    rdo = rd * smoothstep(op / 0.25)
    cyL = lerp(cyL, yc, rdo * 0.85)
    cyR = lerp(cyR, yc, rdo * 0.85)

    def upq(cy):
        return lerp(lerp(cy, up_m, 0.78) - 0.3, yc - 0.87 * hb, rdo)

    def loq(cy):
        return lerp(lerp(cy, lo_m, 0.8), yc + 0.87 * hb, rdo)
    U = [(cxL, cyL), (cxL * 0.5, upq(cyL)), (0.0, up_m), (cxR * 0.5, upq(cyR)), (cxR, cyR)]
    Lw = [(cxL, cyL), (cxL * 0.55, loq(cyL)), (0.0, lo_m), (cxR * 0.55, loq(cyR)), (cxR, cyR)]
    if op < 0.06:
        k = 1 - op / 0.06
        mid = y0 + sm * 1.4 - abs(sk) * 0.4 + qM * 0.5
        U[2] = (0.0, lerp(up_m, mid, k))
        U[1] = (U[1][0], lerp(U[1][1], (cyL + mid) / 2 + sm * 1.0, k))
        U[3] = (U[3][0], lerp(U[3][1], (cyR + mid) / 2 + sm * 1.0, k))
    nd = H.nod_dy * 0.9

    def pj(pt):
        return (_hx(H, pt[0], y0)[0], pt[1] + nd)
    pU = [pj(q) for q in U]
    pL = [pj(q) for q in Lw]
    lo_y = pL[2][1]
    _stroke(c, _curve([(pL[2][0] - 6.0, lo_y + 8.5), (pL[2][0], lo_y + 10.0), (pL[2][0] + 6.0, lo_y + 8.5)]),
            C_SKIN_SH, 2.0, 0.4, blur=0.8)
    lip = _closed2([pL[0], pL[1], pL[2], pL[3], pL[4]],
                   [(pL[3][0], pL[3][1] + 3.0), (pL[2][0], pL[2][1] + 6.6), (pL[1][0], pL[1][1] + 3.0)])
    _fill(c, lip, C_LIP, 0.88, blur=0.4)
    c.drawOval(skia.Rect(pL[2][0] - 4.4, pL[2][1] + 1.8, pL[2][0] + 2.4, pL[2][1] + 4.0), paint(C_LIP_HI, 0.7, blur=0.8))
    ulip = _closed2([pU[0], pU[1], pU[2], pU[3], pU[4]],
                    [(pU[3][0], pU[3][1] - 2.4), (pU[2][0] + 2.0, pU[2][1] - 3.6), (pU[2][0], pU[2][1] - 2.7),
                     (pU[2][0] - 2.0, pU[2][1] - 3.6), (pU[1][0], pU[1][1] - 2.4)])
    _fill(c, ulip, C_LIP, 0.62, blur=0.4)
    if op >= 0.03:
        # corners split vertically for round shapes -> rounded sides instead of pointed corners
        gapc = (pL[2][1] - pU[2][1]) * 0.22 * rd
        inner = smooth_path([(pU[0][0] + 0.8 * rd, pU[0][1] - gapc * 0.5), pU[1], pU[2], pU[3],
                             (pU[4][0] - 0.8 * rd, pU[4][1] - gapc * 0.5), (pL[4][0] - 0.8 * rd, pL[4][1] + gapc * 0.5),
                             pL[3], pL[2], pL[1], (pL[0][0] + 0.8 * rd, pL[0][1] + gapc * 0.5)], closed=True)
        _fill(c, inner, C_MOUTH)
        c.save()
        c.clipPath(inner, doAntiAlias=True)
        gap = pL[2][1] - pU[2][1]
        tth = min(4.6, 0.42 * gap) * (1.0 - 0.55 * rd)
        if op > 0.08:
            teeth = _closed2([(x, y - 2) for x, y in pU],
                             [(x, y + tth * (0.55 + 0.45 * (1 - abs(i - 2) / 2.0))) for i, (x, y) in enumerate(pU)][::-1])
            _fill(c, teeth, C_TEETH)
        if op > 0.18:
            ta = smoothstep((op - 0.18) / 0.25)
            tx = pL[2][0]
            tw = abs(pU[4][0] - pU[0][0]) * 0.36
            c.drawOval(skia.Rect(tx - tw, pL[2][1] - 6.5, tx + tw, pL[2][1] + 3.0), paint(C_TONGUE, ta))
        c.restore()
        _stroke(c, inner, C_LIP_LINE, 1.3, 0.9)
    _fill(c, _ribbon(pU, [0.9, 2.1, 2.6, 2.1, 0.9]), C_LIP_LINE, 0.95)
    for sgn, (cx, cy), amt in ((-1, pU[0], max(sm, 0) + max(-sk, 0)), (1, pU[4], max(sm, 0) + max(sk, 0))):
        if amt > 0.2:
            a = clamp((amt - 0.2) / 0.6)
            _stroke(c, _curve([(cx + sgn * 0.6, cy - 2.8), (cx + sgn * 2.8, cy - 0.4), (cx + sgn * 2.0, cy + 2.4)]),
                    C_SKIN_LINE, 1.3, 0.6 * a)
        if sm < -0.2:
            a = clamp((-sm - 0.2) / 0.5)
            _stroke(c, _curve([(cx, cy), (cx + sgn * 1.6, cy + 3.2)]), C_SKIN_LINE, 1.1, 0.45 * a)


def _draw_ear(c, H, slot):
    x, y, vis = _surf_az(H, slot * 90.0, 3.0)
    k = clamp(abs(H.s) * 1.3) if (slot * H.s) < 0 else 0.0
    w = lerp(9.0, 13.0, k)
    o = float(slot)
    if k > 0.2:
        o = -1.0 if H.s > 0 else 1.0
    pts = [(0.0, -14.0), (0.45 * w, -17.0), (0.92 * w, -11.0), (w, 0.0), (0.8 * w, 10.0), (0.45 * w, 18.0),
           (0.1 * w, 20.0), (-1.0, 12.0)]
    path = smooth_path([(x + o * px, y + py) for px, py in pts], closed=True)
    _fill(c, path, C_SKIN)
    _stroke(c, path, C_SKIN_LINE, 1.3, 0.7)
    inner = _curve([(x + o * 0.62 * w, y - 10.0), (x + o * 0.74 * w, y), (x + o * 0.5 * w, y + 8.5),
                    (x + o * 0.2 * w, y + 9.5)])
    _stroke(c, inner, C_SKIN_SH, 2.2, 0.9)
    c.drawCircle(x + o * 0.32 * w, y + 17.0, 2.0, paint(C_STUD))
    c.drawCircle(x + o * 0.32 * w - 0.5, y + 16.5, 0.75, paint(WHITE, 0.9))


# --------------------------------------------------------------------------- hair
def _puff_geom(H):
    s = H.s
    cx = -10.0 * s - H.nod * 10.0 * s
    cy = -128.0 - H.nod_dy * 0.45
    ph = H.th * 0.9
    lobes = []
    n = 12
    for i in range(n):
        a = 2 * math.pi * i / n + ph
        r = 19.0 + 3.0 * math.sin(i * 2.3 + 1.0)
        lobes.append((cx + 48 * math.cos(a), cy + 38 * math.sin(a), r, a))
    return cx, cy, lobes


def _draw_puff(c, H):
    cx, cy, lobes = _puff_geom(H)
    path = skia.Path()
    path.addOval(skia.Rect(cx - 54, cy - 43, cx + 54, cy + 43), skia.PathDirection.kCCW)
    for bx, by, r, a in lobes:
        path.addCircle(bx, by, r, skia.PathDirection.kCCW)
    c.drawPath(path, paint(C_HAIR_SH, 0.85, stroke=2.6))
    sh = skia.GradientShader.MakeLinear([(cx, cy - 40), (cx, cy + 60)], [C_HAIR, C_HAIR, C_HAIR_SH], [0.0, 0.45, 1.0])
    c.drawPath(path, paint(None, shader=sh))
    hl = skia.GradientShader.MakeRadial((cx - 16, cy - 20), 32, [col(C_HAIR_HI, 0.55), col(C_HAIR_HI, 0.0)])
    c.drawCircle(cx - 16, cy - 20, 32, paint(None, shader=hl))
    for bx, by, r, a in lobes:
        lit = -math.sin(a) * 0.75 - math.cos(a) * 0.55
        arc = skia.Path()
        rr = r * 0.6
        arc.addArc(skia.Rect(bx - rr, by - rr, bx + rr, by + rr), 160, 140)
        if lit > 0.0:
            _stroke(c, arc, C_HAIR_HI, 2.3, 0.85 * min(1.0, lit + 0.2))
        else:
            _stroke(c, arc, C_HAIR_SH, 2.0, 0.5)
    for (ix, iy, rr, a0) in ((-22, -16, 9, 150), (8, -24, 10, 170), (26, -2, 9, 190), (-6, 4, 10, 160),
                             (-34, 8, 8, 150), (16, 18, 8, 200)):
        arc = skia.Path()
        arc.addArc(skia.Rect(cx + ix - rr, cy + iy - rr, cx + ix + rr, cy + iy + rr), a0, 130)
        _stroke(c, arc, C_HAIR_HI if iy < 0 else C_HAIR_SH, 2.0, 0.55)


def _draw_hair_cap(c, H, head_out, head_grow):
    region, hl_pts = _hair_region(H)
    if region is None:
        return None
    hair = skia.Op(head_grow, region, skia.PathOp.kIntersect_PathOp)
    sh_reg = skia.Path(region)
    sh_reg.offset(-0.8, 3.6)
    shadow = skia.Op(head_out, sh_reg, skia.PathOp.kIntersect_PathOp)
    _fill(c, shadow, C_SKIN_SH, 0.55, blur=1.2)
    gx = -26.0 - 14.0 * H.s
    sh = skia.GradientShader.MakeRadial((gx, -58.0), 118.0, [C_HAIR, C_HAIR, C_HAIR_SH], [0.0, 0.55, 1.0])
    c.drawPath(hair, paint(None, shader=sh))
    s = H.s
    tie = (-4.0 * s, -90.0 - H.nod_dy * 0.4)
    for ph in (-60, -44, -28, -12, 4, 20, 36, 52, 66):
        x, y, vis = _surf_az(H, ph, _hairline_y(ph) - 2.0)
        if vis <= 0.15:
            continue
        mx, my, _ = _surf_az(H, ph * 0.8, -72.0)
        _stroke(c, _curve([(x, y - 3.0), (mx, my), (tie[0] + ph * 0.16, tie[1] + 6)]), C_HAIR_HI, 1.1,
                0.28 + 0.12 * math.sin(ph * 0.7))
    # curved sheen band following the skull contour (light from the upper left)
    lx0 = -_sil_x(H, -20.0, -1)
    rx0 = _sil_x(H, -20.0, 1)
    gcx, gcy, grx, gry = (rx0 - lx0) * 0.5, -22.0, (rx0 + lx0) * 0.5, 68.0
    sp = []
    for i in range(7):
        a = (198.0 + i * 13.0) * D2R
        sp.append((gcx + grx * 0.84 * math.cos(a), gcy + gry * 0.84 * math.sin(a)))
    widths = [1.0 + 9.0 * math.sin(math.pi * (i + 0.15) / 6.3) ** 1.3 for i in range(7)]
    _fill(c, _ribbon(sp, widths), C_HAIR_HI, 0.85, blur=2.6)
    _fill(c, _ribbon(sp[1:-1], [w * 0.35 for w in widths[1:-1]]), C_HAIR_SHEEN, 0.55, blur=1.0)
    _stroke(c, hair, C_HAIR_SH, 1.5, 0.75)
    for sg in (-1, 1):
        x, y, vis = _surf_az(H, sg * 60.0, _hairline_y(60.0) + 0.5)
        if vis > 0.3:
            d = 1.0 if (sg > 0) else -1.0
            _stroke(c, _curve([(x - d * 4, y - 3), (x - d * 1, y + 1.5), (x + d * 3, y + 1.0), (x + d * 1.5, y - 1.5),
                               (x - d * 0.5, y + 0.3)]), C_HAIR, 1.1, 0.85)
    return hl_pts


def _lock(c, x, y, out, length, width, phase, sway, waves=1.15, amp=4.6):
    """One chunky S-shaped curl: a tapered ribbon whose centre line snakes side to side, ending in a
    small hook, with a soft highlight on the bulges that face the light (upper-left)."""
    n = 16
    pts, wid = [], []
    for i in range(n + 1):
        u = i / n
        a = phase + u * 2.0 * math.pi * waves
        am = amp * (1.0 - 0.3 * u)
        pts.append((x + out * (1.0 + 5.5 * u) + am * math.sin(a) * out + sway * u * u, y + u * length))
        wid.append(width * min(1.0, 0.4 + u * 4.0) * (1.0 - 0.7 * u ** 1.3))
    # pointed root tucked into the hairline
    r0, r1 = pts[0], pts[1]
    dx, dy = _norm(r0[0] - r1[0], r0[1] - r1[1])
    pts.insert(0, (r0[0] + dx * 3.5, r0[1] + dy * 3.5))
    wid.insert(0, 0.8)
    # tip hook: curls back under itself
    tx, ty = pts[-1]
    hk = -out if math.cos(phase + 2.0 * math.pi * waves) * out > 0 else out
    pts.append((tx + hk * 2.6, ty + 2.4))
    pts.append((tx + hk * 3.4, ty + 0.4))
    wid += [wid[-1] * 0.8, 0.6]
    rib = _ribbon(pts, wid)
    c.drawPath(rib, paint(C_HAIR_SH, 0.9, stroke=1.6))
    _fill(c, rib, C_HAIR)
    # highlight on the lit side of each bulge (where the curl turns toward the light)
    for i in range(2, n):
        a = phase + ((i - 1) / n) * 2.0 * math.pi * waves
        lit = -math.cos(a) * out
        if lit > 0.3:
            q0, q1 = pts[i - 1], pts[i + 1]
            w = wid[i] * 0.2
            _stroke(c, _curve([(q0[0] - w, q0[1] - 0.4), (pts[i][0] - w, pts[i][1] - 0.4),
                               (q1[0] - w, q1[1] - 0.4)]), C_HAIR_SHEEN, max(0.9, wid[i] * 0.28),
                    0.6 * min(1.0, lit + 0.2))


def _draw_ringlet(c, H, slot, t, far=False):
    """Loose curls framing the face at the temple: two S-shaped locks. The far-side locks hang from
    behind the cheek (drawn before the skin so only the part outside the silhouette shows)."""
    s = abs(H.s)
    ph = slot * (66.0 + (40.0 * s if far else 0.0))
    x, y, vis = _surf_az(H, ph, _hairline_y(ph) - 1.0)
    if not far and vis < -0.1:
        return
    sway = math.sin(t * 1.6 + slot) * 1.4
    out = float(slot)
    _lock(c, x + out * 1.5, y + 1.0, out, 32.0, 6.2, 1.9 + slot * 0.4, sway * 0.7, waves=1.0, amp=4.0)
    _lock(c, x - out * 1.0, y + 1.0, out, 50.0, 8.6, 0.3, sway, waves=1.3, amp=5.4)


def _draw_bang(c, H, t):
    """One loose curl springing from the hairline onto the forehead."""
    x, y, vis = _surf_az(H, -16.0, _hairline_y(-16.0) - 3.0)
    if vis <= 0.25:
        return
    sw = math.sin(t * 1.3) * 0.7
    pts = []
    for i in range(14):
        u = i / 13.0
        a = -0.6 + u * 5.2
        r = 6.2 * (1.0 - 0.55 * u)
        pts.append((x - 3.0 + sw * u + r * math.cos(a) * 0.85, y + 6.0 + u * 5.0 + r * math.sin(a)))
    pts.insert(0, (x + 1.0, y - 1.5))
    widths = [lerp(4.6, 1.4, (i / (len(pts) - 1)) ** 0.8) for i in range(len(pts))]
    _fill(c, _ribbon(pts, widths), C_HAIR)
    _stroke(c, _curve(pts[1:7]), C_HAIR_HI, 0.9, 0.6)


def _draw_cap_and_tie(c, H, head_out, head_grow):
    _draw_hair_cap(c, H, head_out, head_grow)
    s = H.s
    tx, ty = -4.0 * s, -91.0 - H.nod_dy * 0.4
    # fabric scrunchie: a ruffled band with a few soft gathers (wraps around the base of the puff)
    ph0 = H.th * 1.6
    hw, hh = 25.0, 7.6
    top, bot = [], []
    for i in range(9):
        u = i / 8.0
        x = tx - hw + 2 * hw * u
        e = math.sqrt(max(0.0, 1.0 - (2 * u - 1) ** 2))
        ruf = 1.3 * math.sin(u * math.pi * 4.0 + ph0)
        top.append((x, ty - hh * (0.35 + 0.65 * e) - ruf * e))
        bot.append((x, ty + hh * (0.3 + 0.6 * e) + ruf * 0.6 * e))
    band = _closed2(top, bot[::-1])
    c.drawPath(band, paint(C_HAIR_SH, 0.85, stroke=1.8))
    sh = skia.GradientShader.MakeLinear([(tx, ty - hh), (tx, ty + hh)], [C_TIE, C_TIE, C_TIE_SH], [0.0, 0.45, 1.0])
    c.drawPath(band, paint(None, shader=sh))
    for k in range(4):
        u = (k + 0.5 + 0.15 * math.sin(ph0 + k)) / 4.0
        x = tx - hw + 2 * hw * u
        e = math.sqrt(max(0.0, 1.0 - (2 * u - 1) ** 2))
        _stroke(c, _curve([(x - 1.5, ty - hh * 0.75 * e), (x + 1.2, ty - 0.5), (x - 0.5, ty + hh * 0.7 * e)]),
                C_TIE_SH, 1.2, 0.7)
    c.drawOval(skia.Rect(tx - hw * 0.75, ty - hh * 0.8, tx + hw * 0.1, ty - hh * 0.25), paint(WHITE, 0.2, blur=1.6))


# --------------------------------------------------------------------------- head assembly
def _draw_head(c, R, p, t):
    H = R.H
    tt = t if t is not None else 0.0
    P = _NS()
    P.squint = clamp(p.squint + 0.22 * max(0.0, p.smile))
    P.wide = clamp(p.eye_wide)
    P.gx = clamp(p.look_x * R.fac, -1.2, 1.2)
    P.gy = clamp(p.look_y, -1.0, 1.0)
    P.pupil = clamp(p.pupil, 0.5, 1.6)
    P.tears = clamp(p.tears)
    P.shine = clamp(p.eye_shine)
    P.sniffle = clamp(p.sniffle)
    blink = auto_blink(t, seed=11, rate=3.7) if t is not None else 1.0
    lids = {s_: (clamp(v) if v is not None else blink) for s_, v in (("l", p.lid_l), ("r", p.lid_r))}
    head_out = _head_outline(H)
    head_grow = _head_outline(H, grow=4.0)
    hkey = (round(H.th, 3), round(H.nod_dy, 2))
    _cached(c, ("puff",) + hkey, skia.Rect(-140, -230, 140, -40), lambda cv: _draw_puff(cv, H))
    far_slots = [sl for sl in (-1, 1) if sl * H.s > 0.08] if not R.back else []
    for slot in far_slots:
        _draw_ringlet(c, H, slot, tt, far=True)
    for slot in (-1, 1):
        if H.s * slot > 0.12 or abs(H.s) <= 0.12:
            _draw_ear(c, H, slot)
    # skin with a soft cel-like form shadow on the far side / jaw: an elliptical radial gradient
    # centred toward the light (no clipping needed)
    ys = (-90.0, 67.0)
    a0 = _prof(0.0)[0]
    lft = -math.sqrt(a0 * a0 * H.c * H.c + _prof(0.0)[2] ** 2 * max(H.s, 0) ** 2)
    rgt = math.sqrt(a0 * a0 * H.c * H.c + _prof(0.0)[1] ** 2 * max(H.s, 0) ** 2)
    rx, ry = (rgt - lft) * 0.5, (ys[1] - ys[0]) * 0.5
    fcx = (lft + rgt) * 0.5 - 0.1 * rx - 3.0 * max(H.s, 0.0)
    fcy = (ys[0] + ys[1]) * 0.5 - 0.1 * ry + H.nod_dy * 0.3
    lm = skia.Matrix()
    lm.setScale(rx / ry, 1.0, fcx, fcy)
    shade = skia.GradientShader.MakeRadial((fcx, fcy), ry * 1.06, [C_SKIN, C_SKIN, C_SKIN_SH, C_SKIN_SH],
                                           [0.0, 0.88, 0.95, 1.0], skia.TileMode.kClamp, 0, lm)
    c.drawPath(head_out, paint(None, shader=shade))
    c.save()
    c.clipPath(head_out, doAntiAlias=False)
    if not R.back:
        for slot in (-1, 1):
            bx, by, dep, fs = _hx(H, slot * 34.0, 24.0)
            if dep > -5:
                a = 0.12 + 0.5 * clamp(p.blush) + 0.3 * P.sniffle
                rr = 13.0
                sh = skia.GradientShader.MakeRadial((bx, by), rr, [col(C_BLUSH, a), col(C_BLUSH, 0.0)])
                c.save()
                c.translate(bx, by)
                c.scale(max(fs, 0.3), 0.62)
                c.translate(-bx, -by)
                c.drawCircle(bx, by, rr, paint(None, shader=sh))
                c.restore()
        hx_, hy_, _, _ = _hx(H, -31.0, 13.0)
        c.drawOval(skia.Rect(hx_ - 9, hy_ - 4, hx_ + 6, hy_ + 3), paint(C_SKIN_HI, 0.4, blur=4))
        fx_, fy_, _, _ = _hx(H, -14.0, -36.0)
        c.drawOval(skia.Rect(fx_ - 13, fy_ - 6, fx_ + 11, fy_ + 5), paint(C_SKIN_HI, 0.3, blur=6))
        cx_, cy_, _, _ = _hx(H, -4.0, 62.0)
        c.drawOval(skia.Rect(cx_ - 6, cy_ - 2.5, cx_ + 4, cy_ + 2), paint(C_SKIN_HI, 0.3, blur=2.5))
    c.restore()
    _stroke(c, head_out, C_SKIN_LINE, 1.6, 0.8)
    _cached(c, ("cap",) + hkey, skia.Rect(-120, -140, 120, 60), lambda cv: _draw_cap_and_tie(cv, H, head_out, head_grow))
    for slot in (-1, 1):
        if H.s * slot < -0.12:
            _draw_ear(c, H, slot)
    if R.back:
        return
    c.save()
    c.clipPath(head_out, doAntiAlias=True)
    lashes = []
    for slot in (-1, 1):
        side = "r" if slot < 0 else "l"
        E = _NS()
        E.__dict__.update(P.__dict__)
        E.lash_out = lashes
        E.lid = lids[side]
        E.emit = R.emit
        E.tear_roll = clamp(p.tear_r if side == "r" else p.tear_l)
        xs = 1.0 if slot > 0 else -1.0
        E.braise = clamp(p.brow_raise + 0.25 * P.wide - 0.45 * p.smirk * xs, -1.2, 1.4)
        E.bworry = clamp(p.brow_worry)
        E.bfurrow = clamp(p.brow_furrow)
        _draw_eye(c, H, E, slot, t)
        _draw_brow(c, H, E, slot)
    _draw_nose(c, H, P)
    _draw_mouth(c, H, p, t)
    c.restore()
    for lash in lashes:          # upper lash lines are not clipped: the far flick may poke past the cheek
        lash(c)
    for slot in (-1, 1):
        if slot not in far_slots:
            _draw_ringlet(c, H, slot, tt)
    _draw_bang(c, H, tt)


# --------------------------------------------------------------------------- main draw
def _draw_body(c, R, p, t):
    near, far = R.arms[-1], R.arms[1]
    legs = R.legs
    seated_front = R.sw > 0.5 and abs(R.turn) < 0.15     # knees toward camera: legs over the jacket hem
    c.save()
    c.concat(R.MU)
    for A in (far, near):
        if A.layer == "behind":
            _draw_arm(c, A, R)
    if far.layer == "back":
        _draw_arm(c, far, R)
    c.restore()
    _draw_leg(c, legs[1], R)
    _draw_hips(c, R)
    if not seated_front:
        _draw_leg(c, legs[-1], R)
    c.save()
    c.concat(R.MU)
    _draw_neck(c, R)
    _draw_torso(c, R)
    c.restore()
    if seated_front:
        _draw_leg(c, legs[-1], R)
    c.save()
    c.concat(R.MH)
    _draw_head(c, R, p, t)
    c.restore()
    c.save()
    c.concat(R.MU)
    R.occluders = []
    for A in (far, near):
        if (A is far and A.layer == "over") or (A is near and A.layer == "front"):
            _draw_arm(c, A, R)
            if R.emit is not None:
                R.occluders.append(_arm_occluder(A, R))
    c.restore()


def _light_cf(pose):
    # perceptual response: light 0.25 still leaves faces readable (~0.41 linear) in the dark scenes
    return light_filter(max(0.0, pose.light) ** 0.65, pose.tint, pose.tint_amt)


def _bounds(R):
    """Tight local-frame bounding rect of the character (for layers)."""
    pts = []
    for x, y in ((-80, -190), (80, -190), (-80, 85), (80, 85)):
        q = R.MH.mapXY(x, y)
        pts.append((q.fX, q.fY))
    for A in R.arms.values():
        for x, y in (A.S, A.E, A.W, A.palm):
            q = R.MU.mapXY(x, y)
            pts.append((q.fX, q.fY))
    if R.mug is not None:
        q = R.MU.mapXY(R.mug.x, R.mug.y - 16.0)
        pts.append((q.fX, q.fY))
    for L in R.legs.values():
        pts += [L.hip, L.knee, L.ankle]
    pad = 50.0
    xs = [q[0] for q in pts]
    ys = [q[1] for q in pts]
    return skia.Rect(min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)


def _draw_rimlit(c, R, pose, t, lit):
    """Rim-lit render. The character is drawn once into an offscreen image (device pixels, tight
    bounds); a soft glow is blurred at 1/8 resolution, the light-filtered image is composited and a
    thin bright rim edge (silhouette minus a shifted silhouette, half resolution) goes on top."""
    M = c.getTotalMatrix()
    dscale = math.sqrt(abs(M.getScaleX() * M.getScaleY() - M.getSkewX() * M.getSkewY()))
    rim = clamp(pose.rim)
    rc = col(pose.rim_color)
    dev = M.mapRect(_bounds(R))
    clipb = c.getDeviceClipBounds()
    bx0 = max(math.floor(dev.left()), clipb.left())
    by0 = max(math.floor(dev.top()), clipb.top())
    bx1 = min(math.ceil(dev.right()), clipb.right())
    by1 = min(math.ceil(dev.bottom()), clipb.bottom())
    if bx1 <= bx0 or by1 <= by0:
        return
    w, h = int(bx1 - bx0), int(by1 - by0)
    surf = skia.Surface(w, h)
    oc = surf.getCanvas()
    oc.translate(-bx0, -by0)
    oc.concat(M)
    _draw_body(oc, R, pose, t)
    img = surf.makeImageSnapshot()
    lin = skia.SamplingOptions(skia.FilterMode.kLinear)
    tint = skia.Paint()
    tint.setColorFilter(skia.ColorFilters.Blend(rc, skia.BlendMode.kSrcIn))
    # glow (1/8 resolution, two blur radii)
    q = 4.0
    padg = 40.0 * dscale
    gx0, gy0 = bx0 - padg, by0 - padg
    gw, gh = int((w + 2 * padg) / q) + 2, int((h + 2 * padg) / q) + 2
    small = skia.Surface(gw, gh)
    sc = small.getCanvas()
    sc.scale(1.0 / q, 1.0 / q)
    sc.drawImage(img, padg, padg, lin, tint)
    sil = small.makeImageSnapshot()
    glow = skia.Surface(gw, gh)
    gc = glow.getCanvas()
    for sig, a in ((20.0 * dscale, 0.55 * rim), (7.0 * dscale, min(1.0, 0.9 * rim))):
        gp = skia.Paint()
        gp.setImageFilter(skia.ImageFilters.Blur(sig / q, sig / q))
        gp.setAlphaf(a)
        gc.drawImage(sil, 0, 0, skia.SamplingOptions(), gp)
    c.save()
    c.resetMatrix()
    # nearest is visually fine for the soft glow at normal sizes; bilinear for close-ups
    gs = lin if dscale > 1.6 else skia.SamplingOptions()
    c.drawImageRect(glow.makeImageSnapshot(), skia.Rect(gx0, gy0, gx0 + gw * q, gy0 + gh * q), gs)
    # the character itself (already light-filtered while drawing)
    c.drawImage(img, bx0, by0, skia.SamplingOptions())
    # thin rim edge on the top / back side: tinted silhouette minus a shifted silhouette
    off = M.mapVector(3.0, 3.2)
    ox, oy = max(1, round(off.fX)) if off.fX >= 0 else min(-1, round(off.fX)), max(1, round(off.fY))
    eh = skia.Surface(w, h)
    ec = eh.getCanvas()
    ec.drawImage(img, 0, 0, skia.SamplingOptions(), tint)
    dp = skia.Paint()
    dp.setBlendMode(skia.BlendMode.kDstOut)
    ec.drawImage(img, ox, oy, skia.SamplingOptions(), dp)
    ep = skia.Paint()
    ep.setAlphaf(min(1.0, 1.1 * rim))
    c.drawImage(eh.makeImageSnapshot(), bx0, by0, skia.SamplingOptions(), ep)
    c.restore()


def draw(canvas, pose: Pose, t: float):
    """Draw Rae. The canvas must already carry the camera transform (stage coordinates)."""
    global _CF, _CF_KEY
    R = _solve(pose, t)
    c = canvas
    c.save()
    c.concat(R.MS)
    lit = pose.light != 1.0 or pose.tint_amt > 0
    R.emit = [] if pose.light < 0.95 else None
    _CF = _light_cf(pose) if lit else None
    _CF_KEY = (round(pose.light, 3), tuple(pose.tint), round(pose.tint_amt, 3)) if lit else None
    try:
        if pose.rim > 0.001:
            _draw_rimlit(c, R, pose, t, lit)
        else:
            _draw_body(c, R, pose, t)
    finally:
        _CF = None
        _CF_KEY = None
    if R.emit:
        # eye glints stay bright in low light (reflections of the window / ribbons)
        a = clamp(0.85 * (1.0 - pose.light) / 0.75)
        c.concat(R.MH)
        inv = skia.Matrix()
        occ = []
        if getattr(R, "occluders", None) and R.MHr.invert(inv):
            for o_ in R.occluders:
                q = skia.Path(o_)
                q.transform(inv)
                occ.append(q)
        for opening, glint in R.emit:
            c.save()
            c.clipPath(opening, doAntiAlias=True)
            for q in occ:
                c.clipPath(q, skia.ClipOp.kDifference, True)
            c.saveLayerAlpha(None, int(255 * a))
            glint(c)
            c.restore()
            c.restore()
    c.restore()


# --------------------------------------------------------------------------- presets
ARMS = {
    "rest": ArmPose(shoulder=5.0, elbow=12.0, wrist=0.0, hand="relaxed"),
    "hold_mug": ArmPose(shoulder=10.0, elbow=84.0, wrist=0.0, hand="hold", across=0.22),
    "sip": ArmPose(shoulder=56.0, elbow=104.0, wrist=0.0, hand="hold", across=0.38),
    "mug_raise": ArmPose(shoulder=48.0, elbow=78.0, wrist=0.0, hand="hold", across=0.0),
    "point": ArmPose(shoulder=76.0, elbow=10.0, wrist=0.0, hand="point"),
    "hand_on_chest": ArmPose(shoulder=12.0, elbow=118.0, wrist=10.0, hand="open", across=0.58),
    "wipe_eye": ArmPose(shoulder=88.0, elbow=130.0, wrist=16.0, hand="fist", across=0.3),
    "cover_mouth": ArmPose(shoulder=60.0, elbow=100.0, wrist=4.0, hand="open", across=0.48),
    "hands_up": ArmPose(shoulder=28.0, elbow=104.0, wrist=-14.0, hand="palm_out", across=-0.25),
    "grip_knee": ArmPose(shoulder=26.0, elbow=30.0, wrist=10.0, hand="fist"),
    "reach_back": ArmPose(shoulder=-42.0, elbow=14.0, wrist=-10.0, hand="open"),
    "shrug": ArmPose(shoulder=14.0, elbow=96.0, wrist=-12.0, hand="palm_up", across=-0.8),
    "hug_self": ArmPose(shoulder=8.0, elbow=100.0, wrist=6.0, hand="relaxed", across=0.95),
    "knee_rest": ArmPose(shoulder=36.0, elbow=14.0, wrist=24.0, hand="relaxed"),
}

# Face presets: Pose field overrides (scenes: pose.copy(**EXPR["awe"]) or expr(pose, "awe", 0.5)).
EXPR = {
    "neutral": dict(),
    "tired": dict(lid_l=0.52, lid_r=0.5, brow_raise=-0.15, brow_worry=0.15, smile=-0.1, look_y=0.15, head_nod=-0.15),
    "skeptical": dict(smirk=0.7, smile=0.1, brow_furrow=0.2, lid_l=0.72, lid_r=0.72, look_y=0.05, head_tilt=-3.0),
    "frozen_sip": dict(lid_l=0.8, lid_r=0.8, look_x=0.85, look_y=-0.05, brow_raise=0.15),
    "confused": dict(brow_furrow=0.55, brow_raise=0.45, mouth_open=0.18, mouth_round=0.5, smile=-0.15, head_tilt=-6.0,
                     squint=0.1),
    "shocked": dict(eye_wide=1.0, brow_raise=1.0, mouth_open=0.7, mouth_round=0.55, pupil=0.85),
    "awe": dict(pupil=1.3, eye_shine=1.0, brow_raise=0.5, brow_worry=0.35, mouth_open=0.22, mouth_round=0.25,
                lid_l=0.95, lid_r=0.95, look_y=-0.3, head_nod=0.25),
    "moved": dict(tears=0.7, brow_worry=0.8, brow_raise=0.2, pupil=1.2, eye_shine=0.6, mouth_open=0.1, smile=-0.1,
                  look_y=-0.25, lid_l=0.9, lid_r=0.9),
    "tear_smile": dict(tears=0.8, tear_r=0.6, brow_worry=0.75, smile=0.45, mouth_tremble=0.7, eye_shine=0.5,
                       pupil=1.15, squint=0.2, lid_l=0.85, lid_r=0.85),
    "laugh_cry": dict(smile=0.95, mouth_open=0.55, squint=0.65, tears=0.75, brow_worry=0.6, brow_raise=0.25,
                      lid_l=0.55, lid_r=0.55, tear_l=0.4, blush=0.4),
    "sob": dict(squint=0.8, brow_worry=1.0, brow_furrow=0.25, lid_l=0.05, lid_r=0.05, mouth_open=0.4, smile=-0.7,
                mouth_tremble=0.8, tears=0.9, tear_r=0.7, blush=0.35, sniffle=0.5),
    "rapid_blink": dict(lid_l=0.18, lid_r=0.22, brow_raise=0.7, eye_wide=0.0),
    "sniffly_point": dict(sniffle=0.85, tears=0.45, brow_furrow=0.35, brow_worry=0.3, lid_l=0.78, lid_r=0.78, smile=0.05,
                          mouth_open=0.12),
    "dread": dict(eye_wide=0.5, brow_worry=0.7, brow_raise=0.4, smile=-0.35, mouth_open=0.08, look_y=0.1),
    "grin": dict(smile=1.0, mouth_open=0.35, squint=0.35, brow_raise=0.3, blush=0.2),
}


def expr(pose: Pose, name: str, amount: float = 1.0) -> Pose:
    """Blend face preset `name` into pose by `amount` (lid None counts as 1 when blending)."""
    kw = {}
    for k, v in EXPR[name].items():
        cur = getattr(pose, k)
        if cur is None:
            cur = 1.0
        kw[k] = lerp(cur, v, amount)
    return pose.copy(**kw)
