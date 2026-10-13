"""2.5D anime-style character rig.

Head geometry lives in "head units" (half the face width = 1, y down, z toward
the viewer). Features are 3D anchors rotated by yaw/pitch and projected
orthographically; the face silhouette comes from a stack of elliptical
cross-sections, so any yaw gives a consistent outline. Everything is then
drawn with skia under a matrix that maps head units to pixels.
"""
import math

import numpy as np
import skia

from body import draw_legs
from gfx import (c4, ellipse, fill, hexc, lin_grad, mix, poly, rad_grad, sample_spline,
                 spline, stroke, tapered)

DEFAULT_P = dict(
    yaw=0.0, pitch=0.0, roll=0.0, hx=0.0, hy=0.0,
    byaw=0.0, blean=0.0, bx=0.0, breath=0.0, shrug=0.0,
    eo_l=1.0, eo_r=1.0, lo_l=0.0, lo_r=0.0, gx=0.0, gy=0.0, pupil=1.0,
    wet=0.0, tear_l=0.0, tear_r=0.0, tear_dry_l=0.0, tear_dry_r=0.0, glint=0.0,
    br_l=0.0, br_r=0.0, bi_l=0.0, bi_r=0.0, bfur=0.0,
    m_open=0.0, m_wide=0.0, m_round=0.0, m_smile=0.0, m_smirk=0.0, m_press=0.0,
    m_teeth=0.0, m_tongue=0.0,
    blush=0.0, wind=0.0, hair_dx=0.0, hair_dy=0.0, t=0.0,
    light_x=-0.7, light_y=-0.6, rim=0.0, rim_x=1.0,
    arm_l=None, arm_r=None, walk=0.0, walk_phase=0.0,
)

# Default head slices: (y, half_width, half_depth, center_z)
SLICES = [
    (-1.66, 0.02, 0.10, -0.10),
    (-1.58, 0.42, 0.48, -0.12),
    (-1.42, 0.72, 0.76, -0.13),
    (-1.15, 0.92, 0.94, -0.12),
    (-0.80, 0.99, 1.00, -0.10),
    (-0.40, 1.00, 1.00, -0.08),
    (0.00, 0.99, 0.97, -0.05),
    (0.30, 0.96, 0.92, -0.01),
    (0.55, 0.89, 0.82, 0.04),
    (0.76, 0.77, 0.69, 0.10),
    (0.93, 0.61, 0.55, 0.19),
    (1.06, 0.43, 0.41, 0.30),
    (1.15, 0.27, 0.29, 0.39),
    (1.21, 0.13, 0.19, 0.45),
    (1.235, 0.01, 0.10, 0.48),
]


def rot_points(P3, yaw, pitch, pivot=(0.0, 0.6, -0.3)):
    """Rotate (N,3) head-unit points: pitch about pivot, then yaw about the y axis."""
    P3 = np.asarray(P3, dtype=float)
    x, y, z = P3[:, 0], P3[:, 1], P3[:, 2]
    py, pz = pivot[1], pivot[2]
    cp, sp = math.cos(pitch), math.sin(pitch)
    y1 = py + (y - py) * cp + (z - pz) * sp
    z1 = pz - (y - py) * sp + (z - pz) * cp
    cy, sy = math.cos(yaw), math.sin(yaw)
    x2 = x * cy + z1 * sy
    z2 = -x * sy + z1 * cy
    return np.stack([x2, y1, z2], axis=1)


class Head:
    """Projected head geometry for one frame."""

    def __init__(self, st, P):
        self.st = st
        self.P = P
        self.yaw = math.radians(P["yaw"])
        self.pitch = math.radians(P["pitch"])
        sl = st.get("slices", SLICES)
        self.sl = sl
        self.jaw = P["m_open"] * st.get("jaw_drop", 0.07)
        # the whole head (face, hair, ears, beard) can be drawn a little narrower than it is deep,
        # for a longer, more grown-up face
        self.xs = st.get("head_xscale", 1.0)
        # the skull above the brows can be shortened (smoothly, starting just above the brows), so
        # the eyes sit near the middle of the head as they do on a real one; hair, head cloths and
        # everything else on the head follow, since they are all placed through p3
        self.cs = st.get("crown_scale", 1.0)
        self.cref = st.get("crown_ref", -0.25)

    def surf_z(self, x, y):
        ys = [s[0] for s in self.sl]
        w = np.interp(y, ys, [s[1] for s in self.sl])
        d = np.interp(y, ys, [s[2] for s in self.sl])
        zc = np.interp(y, ys, [s[3] for s in self.sl])
        u = min(abs(x) / max(w, 1e-3), 1.0)
        return zc + d * (1 - u * u) ** 0.42

    def crown_y(self, y):
        """Vertical position after shortening the skull: unchanged below crown_ref, then compressed
        toward crown_scale with a smooth (kink-free) start."""
        if self.cs == 1.0:
            return y
        c, yr, b = self.cs, self.cref, 0.2
        t = np.maximum(yr - y, 0.0)
        g = c * t + (1.0 - c) * b * (1.0 - np.exp(-t / b))
        return np.where(y < yr, yr - g, y)

    def p3(self, pts):
        """3D anchors -> projected 2D (N,2) plus rotated z."""
        P3 = np.array(pts, dtype=float)
        if self.xs != 1.0:
            P3[:, 0] *= self.xs
        if self.cs != 1.0:
            P3[:, 1] = self.crown_y(P3[:, 1])
        R = rot_points(P3, self.yaw, self.pitch)
        return R

    def pt(self, x, y, z=None, dz=0.0):
        if z is None:
            z = self.surf_z(x, y) + dz
        R = self.p3([(x, y, z)])
        return R[0, 0], R[0, 1]

    def fore(self, nx, nz):
        """Foreshortening of a surface element with normal (nx, 0, nz)."""
        n = np.array([[nx, 0.0, nz]])
        R = rot_points(n, self.yaw, self.pitch, pivot=(0, 0, 0))
        return float(np.clip(R[0, 2] / math.hypot(nx, nz), 0.12, 1.0))

    def silhouette(self, jaw=0.0):
        """Closed outline (list of 2D points), right side top->chin then left chin->top."""
        cy, sy = math.cos(self.yaw), math.sin(self.yaw)
        right, left = [], []
        for (y, w, d, zc) in self.sl:
            yy = y + (jaw * max(0.0, (y - 0.55) / 0.68) if y > 0.55 else 0.0)
            t = math.atan2(d * sy, max(w * cy, 1e-6))
            xr, zr = w * math.cos(t), zc + d * math.sin(t)
            xl, zl = -xr, zc - d * math.sin(t)
            right.append((xr, yy, zr))
            left.append((xl, yy, zl))
        R = self.p3(right)
        L = self.p3(left)
        r2 = [tuple(p[:2]) for p in R]
        l2 = [tuple(p[:2]) for p in L]
        # single apex / chin point (avoids tiny self-intersecting loops)
        apex = ((r2[0][0] + l2[0][0]) / 2, (r2[0][1] + l2[0][1]) / 2)
        chin = ((r2[-1][0] + l2[-1][0]) / 2, (r2[-1][1] + l2[-1][1]) / 2)
        pts = [apex] + r2[1:-1] + [chin] + l2[1:-1][::-1]
        return pts

    def face_path(self):
        pts = self.silhouette(self.jaw)
        # drop duplicated chin point
        return spline(pts, closed=True, tension=0.5)


# ----------------------------------------------------------------------------
# Eyes
# ----------------------------------------------------------------------------

def eye_curves(st, o, lo, s):
    """Upper/lower lid polylines in canonical eye space (outer corner at +x*s)."""
    ew = st.get("eye_w", 0.21)
    eh = st.get("eye_h", 0.13)
    el = st.get("eye_low", 0.075)
    tilt = st.get("eye_tilt", 0.0)  # outer corner up (+) / down (-)
    o = max(0.0, o)
    xs = np.array([-1.0, -0.62, -0.2, 0.25, 0.68, 1.0])
    up_open = np.array([0.012, -0.70, -0.98, -1.0, -0.78, -0.05 - tilt / max(eh, 1e-3)]) * eh
    up_open[0] = 0.012
    closed = np.array([0.012, 0.30, 0.52, 0.55, 0.40, 0.05]) * el
    lo_y = np.array([0.012, 0.62, 0.92, 0.95, 0.68, 0.05]) * el
    lo_y = lo_y - lo * np.array([0.0, 0.55, 0.85, 0.9, 0.65, 0.1]) * el * 1.1
    # Upper lid: interpolate between closed line and open shape (allow >1 wide eyes)
    up = closed + (up_open - closed) * o
    # happy squint: when lower lid raised and eye mostly closed, closed line arches up
    if lo > 0.4 and o < 0.35:
        k = (lo - 0.4) / 0.6 * (1 - o / 0.35)
        up = up - k * np.array([0, 0.5, 0.8, 0.8, 0.5, 0]) * el * 1.3
    up = np.minimum(up, lo_y)  # upper never below lower
    X = xs * st.get("eye_w", 0.21)
    upper = [(x * s, y) for x, y in zip(X, up)]
    lower = [(x * s, y) for x, y in zip(X, lo_y)]
    return upper, lower


def draw_eye(cv, H, st, P, side):
    """side: -1 screen-left eye, +1 screen-right eye."""
    s = side  # outer corner direction
    ex = st.get("eye_x", 0.42) * side
    ey = st.get("eye_y", 0.0)
    ez = H.surf_z(ex, ey) + st.get("eye_dz", -0.02)
    cx, cy = H.pt(ex, ey, ez)
    f = H.fore(ex * 0.9, 1.0)
    o = P["eo_l"] if side < 0 else P["eo_r"]
    lo = P["lo_l"] if side < 0 else P["lo_r"]
    # the upper lid follows the eyes: it lifts when looking up and drops when looking down
    o = o * (1.0 - 0.32 * min(max(P["gy"], -0.8), 0.8))
    upper, lower = eye_curves(st, o, lo, s)
    eh = st.get("eye_h", 0.13)
    ew = st.get("eye_w", 0.21)

    cv.save()
    cv.translate(cx, cy)
    cv.scale(f, 1.0)
    # mild perspective tilt of the eye with roll is handled by the head matrix

    U = sample_spline(upper, n=28)
    Lw = sample_spline(lower, n=28)
    opening = spline(U + Lw[::-1][1:-1], closed=True, tension=0.45)
    gap = max(np.max(np.array(Lw)[:, 1] - np.array(U)[:, 1]), 0.0)
    line_col = st.get("line", "#2a1a14")
    lash_col = st.get("lash", "#24150f")

    if gap > 0.006:
        # sclera
        cv.save()
        cv.clipPath(opening, skia.ClipOp.kIntersect, True)
        top = min(p[1] for p in U)
        cv.drawPath(opening, fill("#fffaf6", shader=lin_grad((0, top), (0, top + 0.16), [st.get("sclera_shadow", "#cdbfbe"), "#fffaf6"])))
        # iris
        gx, gy = P["gx"], P["gy"]
        ri_x = st.get("iris_rx", 0.098)
        ri_y = st.get("iris_ry", 0.118)
        icx = gx * ew * 0.55 * (1.0 if True else 1.0)
        icy = 0.006 + gy * 0.07 + st.get("iris_dy", 0.0)
        iris = ellipse(icx, icy, ri_x, ri_y)
        dark, mid, light = st["iris"]
        cv.drawPath(iris, fill(mid, shader=lin_grad((0, icy - ri_y), (0, icy + ri_y), [dark, mid, light], [0.0, 0.55, 1.0])))
        # inner ring glow
        cv.drawPath(ellipse(icx, icy + ri_y * 0.25, ri_x * 0.62, ri_y * 0.55), fill(light, alpha=0.35, blur=0.0))
        # pupil
        ps = P["pupil"]
        cv.drawPath(ellipse(icx, icy - ri_y * 0.05, ri_x * 0.42 * ps, ri_y * 0.46 * ps), fill(st.get("pupil_col", "#160c08")))
        # iris ring
        cv.drawPath(iris, stroke(dark, 0.010, alpha=0.9))
        # a tiny twinkle of light in the pupil
        g = P.get("glint", 0.0)
        if g > 0.01:
            tw = 0.72 + 0.28 * math.sin(P["t"] * 6.5 + side * 1.3)
            rr = ri_x * 0.58 * g * tw
            cv.save()
            cv.translate(icx, icy - ri_y * 0.05)
            cv.rotate(12 + 14 * math.sin(P["t"] * 0.9))
            cv.drawCircle(0, 0, rr * 0.9, fill("#fff6d8", alpha=0.35 * g, blur=rr * 0.5))
            star = [(0, -rr), (rr * 0.16, -rr * 0.16), (rr, 0), (rr * 0.16, rr * 0.16), (0, rr), (-rr * 0.16, rr * 0.16),
                    (-rr, 0), (-rr * 0.16, -rr * 0.16)]
            cv.drawPath(poly(star), fill("#fffdf2", alpha=0.95 * g))
            cv.restore()
        # lid shadow across top of eye
        shadow = spline([(U[0][0], U[0][1] - 0.05)] + U + [(U[-1][0], U[-1][1] - 0.05)], closed=False)
        sp = skia.Path(shadow)
        cv.drawPath(spline(U + [(U[-1][0], U[-1][1] + 0.035), (U[0][0], U[0][1] + 0.035)], closed=True),
                    fill(st.get("lid_shadow", "#5a3b33"), alpha=0.18, blur=0.01))
        # highlights (catchlights) - consistent with key light direction
        lx = -1.0 if P["light_x"] < 0 else 1.0
        hl = 1.0 + 0.6 * P["wet"]
        cv.drawPath(ellipse(icx + lx * ri_x * 0.38, icy - ri_y * 0.42, 0.032 * hl, 0.026 * hl, -20 * lx), fill("#ffffff", alpha=0.95))
        cv.drawPath(ellipse(icx - lx * ri_x * 0.42, icy + ri_y * 0.45, 0.013 * hl, 0.011 * hl), fill("#ffffff", alpha=0.85))
        if P["wet"] > 0.01:
            w = P["wet"]
            ph = P["t"] * 3.0
            # watery sheen along lower lid + sparkles
            low = sample_spline(lower, n=20)
            band = [(x, y - 0.012) for x, y in low[3:-3]]
            cv.drawPath(spline(band, closed=False), stroke("#ffffff", 0.016, alpha=0.55 * w))
            for k in range(3):
                a = 0.4 + 0.6 * (0.5 + 0.5 * math.sin(ph + k * 2.1))
                cv.drawPath(ellipse(icx + (k - 1) * ri_x * 0.55, icy + ri_y * 0.62, 0.012, 0.007), fill("#ffffff", alpha=0.6 * w * a))
            cv.drawPath(opening, fill("#bfe0ff", alpha=0.10 * w))
        cv.restore()

        # upper lash line (tapered, heavier at outer end) + wing
        lash = tapered(U, st.get("lash_in", 0.014), st.get("lash_out", 0.034), wmid=st.get("lash_mid", 0.03))
        cv.drawPath(lash, fill(lash_col))
        ox, oy = U[-1]
        wing = st.get("wing", 0.035)
        if wing > 0:
            wpts = [(ox - s * 0.04, oy - 0.012), (ox + s * wing * 0.7, oy - 0.02 - wing * 0.25), (ox + s * wing, oy - 0.016 - wing * 0.35)]
            cv.drawPath(tapered(sample_spline(wpts, n=8), 0.026, 0.004), fill(lash_col))
        # lower lid line (outer part)
        lw_pts = Lw[len(Lw) // 3:]
        cv.drawPath(tapered(lw_pts, 0.002, st.get("lower_w", 0.011), wmid=0.012), fill(st.get("lower_col", "#6b4436"), alpha=0.85))
        # crease
        if st.get("crease", True):
            cr = [(x, y - 0.055 - 0.02 * (1 - abs(x) / ew)) for x, y in U[6:-3]]
            cr = [(x, y + (1 - o) * 0.05) for x, y in cr]
            cv.drawPath(tapered(cr, 0.002, 0.004, wmid=0.008), fill(st.get("crease_col", "#8a5b48"), alpha=0.6))
        # lower lash hint for female characters
        if st.get("lower_lash", False):
            for k, frac in enumerate((0.55, 0.72, 0.88)):
                i = int(frac * (len(Lw) - 1))
                x, y = Lw[i]
                cv.drawPath(tapered([(x, y), (x + s * 0.012, y + 0.02)], 0.006, 0.0), fill(lash_col, alpha=0.7))
        # top lashes flicks
        for frac, ln in st.get("lash_flicks", []):
            i = int(frac * (len(U) - 1))
            x, y = U[i]
            cv.drawPath(tapered([(x, y), (x + s * ln * 0.6, y - ln * 0.6), (x + s * ln, y - ln * 0.55)], 0.012, 0.0), fill(lash_col))
    else:
        # closed eye: single curved lash line
        mid = [((u[0] + l[0]) / 2, (u[1] + l[1]) / 2) for u, l in zip(U, Lw)]
        cv.drawPath(tapered(mid, 0.010, 0.026, wmid=0.026), fill(lash_col))
        ox, oy = mid[-1]
        if st.get("wing", 0.035) > 0:
            cv.drawPath(tapered([(ox - s * 0.02, oy), (ox + s * 0.03, oy + 0.006)], 0.016, 0.003), fill(lash_col))
        if st.get("lower_lash", False):
            for frac in (0.6, 0.78, 0.92):
                i = int(frac * (len(mid) - 1))
                x, y = mid[i]
                cv.drawPath(tapered([(x, y), (x + s * 0.01, y + 0.024)], 0.007, 0.0), fill(lash_col, alpha=0.8))
    cv.restore()

    # tears
    tear = P["tear_l"] if side < 0 else P["tear_r"]
    dry = P["tear_dry_l"] if side < 0 else P["tear_dry_r"]
    if tear > 0.001 and dry < 0.999:
        draw_tear(cv, H, st, cx, cy, f, side, tear, P, fade=1.0 - dry)


def draw_tear(cv, H, st, cx, cy, f, side, k, P, fade=1.0):
    """A tear that wells at the lower lid and runs down the cheek: one clear, faintly blue drop and
    its wet trail, drawn as a single layer so that as it dries the whole tear fades out together."""
    if fade <= 0.01:
        return
    start = (cx + side * 0.05 * f, cy + 0.08)
    run = min(1.0, k) * 0.42
    x0, y0 = start
    path_pts = [(x0, y0), (x0 + side * 0.012, y0 + run * 0.5), (x0 + side * 0.02, y0 + run)]
    cv.saveLayerAlpha(None, int(255 * min(1.0, fade)))
    if run > 0.02:
        trail = sample_spline(path_pts, n=10)
        cv.drawPath(tapered(trail, 0.01, 0.02), fill("#7fb3dc", alpha=0.35))
        cv.drawPath(tapered(trail, 0.006, 0.012), fill("#bfe0f7", alpha=0.6))
        cv.drawPath(tapered([(x - side * 0.004, y) for x, y in trail], 0.002, 0.004), fill("#ffffff", alpha=0.75))
    dx, dy = path_pts[-1]
    r = 0.018 + 0.008 * min(1, k)
    drop = ellipse(dx, dy, r * 0.8, r)
    cv.drawPath(drop, fill("#a9d2f2", alpha=0.8))
    cv.drawPath(drop, stroke("#5f93bf", 0.004, alpha=0.6))
    cv.drawPath(ellipse(dx - 0.005, dy - 0.006, r * 0.3, r * 0.35), fill("#ffffff", alpha=0.9))
    cv.restore()


def draw_brow(cv, H, st, P, side):
    s = side
    bx = st.get("brow_x", 0.42) * side
    by = st.get("brow_y", -0.30)
    bz = H.surf_z(bx, by)
    cx, cy = H.pt(bx, by, bz)
    f = H.fore(bx * 0.9, 1.0)
    r = P["br_l"] if side < 0 else P["br_r"]
    ir = P["bi_l"] if side < 0 else P["bi_r"]
    fu = P["bfur"]
    inner = st.get("brow_in", -0.22)
    outer = st.get("brow_out", 0.25)
    arch = st.get("brow_arch", 0.035)
    # canonical: inner at negative x
    pts = [
        (inner + fu * 0.035, -r * 0.075 - ir * 0.085 + fu * 0.025),
        ((inner + outer) * 0.5 - 0.05, -arch - r * 0.08 - ir * 0.03 + fu * 0.008),
        (outer * 0.62, -arch * 0.9 - r * 0.075 + ir * 0.02),
        (outer, 0.03 - r * 0.06 + ir * 0.045 - st.get("brow_out_up", 0.0)),
    ]
    pts = [(x * s, y) for x, y in pts]
    cv.save()
    cv.translate(cx, cy)
    cv.scale(f, 1.0)
    sm = sample_spline(pts, n=18)
    cv.drawPath(tapered(sm, st.get("brow_w0", 0.05), st.get("brow_w1", 0.014), wmid=st.get("brow_wm", 0.04)), fill(st.get("brow_col", "#2b1b12")))
    if fu > 0.15:
        # furrow lines between the brows
        a = min(1.0, (fu - 0.15) / 0.6)
        x0 = inner * s + s * 0.02
        cv.drawPath(spline([(x0 - s * 0.03, -0.02), (x0 - s * 0.05, 0.05)], closed=False), stroke(st.get("crease_col", "#8a5b48"), 0.008, alpha=0.5 * a))
    if r > 0.75:
        # a strongly raised brow wrinkles the forehead above it
        a = min(1.0, (r - 0.75) / 0.6)
        for k, (yy, ww) in enumerate(((-0.17, 0.17), (-0.225, 0.13))):
            yy -= r * 0.05
            xm = (inner + outer) * 0.5 * s
            cv.drawPath(spline([(xm - s * ww * 0.9, yy + 0.012), (xm, yy - 0.006), (xm + s * ww, yy + 0.01)], closed=False),
                        stroke(st.get("crease_col", "#8a5b48"), 0.009, alpha=0.55 * a * (1.0 - 0.3 * k)))
    cv.restore()


# ----------------------------------------------------------------------------
# Nose, mouth
# ----------------------------------------------------------------------------

def draw_nose(cv, H, st, P):
    """Nose with a shaded side plane, a rounded tip, nostril wings and nostrils, and a soft
    shadow under it (drawn about 13% larger than the original minimal anime nose)."""
    k = st.get("nose_scale", 1.13)
    ny = st.get("nose_y", 0.40)
    nl = st.get("nose_len", 0.2) * k
    w = st.get("nose_w", 0.05) * 1.15 * k
    yaw = H.yaw
    side = 1.0 if yaw >= 0 else -1.0
    ay = min(1.0, abs(yaw) / 0.6)
    lc = st.get("line", "#2a1a14")
    skin = st["skin"]
    sh = st.get("skin_sh", "#c98f6c")
    sh2 = st.get("skin_sh2", sh)
    lx = P["light_x"]
    sd = -1.0 if lx > 0 else 1.0  # shaded side in a front view
    if abs(yaw) > 0.05:
        sd = side

    def at(x, dy, dz):
        y = ny + dy
        return H.pt(x, y, H.surf_z(x, y) + dz)

    tip = at(0.0, 0.0, nl)
    top = at(0.0, -0.34 * k, 0.025)
    mid = at(0.0, -0.17 * k, nl * 0.42)
    # side plane of the nose on the shaded side, from the brow down to the nostril wing
    plane = [top, at(sd * 0.05 * k, -0.17 * k, nl * 0.3), at(sd * w * 2.0, 0.01, nl * 0.32), at(sd * w * 1.2, 0.035, nl * 0.5),
             (tip[0] + sd * 0.012, tip[1] + 0.012), mid]
    cv.drawPath(spline(plane, closed=True), fill(sh, alpha=0.42, blur=0.018))
    # soft shadow cast under the nose onto the upper lip
    base = at(0.0, 0.07 * k, nl * 0.35)
    cv.drawPath(ellipse(base[0] + sd * 0.012, base[1] + 0.012, w * 2.2, 0.034 * k), fill(sh, alpha=0.38, blur=0.022))
    # bridge line on the far side in a 3/4 view
    if ay > 0.1:
        bl = [(top[0] + side * 0.015, top[1] + 0.06), (mid[0] + side * 0.03, mid[1]), (tip[0] + side * 0.04, tip[1] - 0.025)]
        cv.drawPath(tapered(sample_spline(bl, n=10), 0.002, 0.009), fill(lc, alpha=0.32 * ay))
    # nostril wings: little curves around each side of the tip (the far one hides behind the tip)
    for s in (-1.0, 1.0):
        vis = 1.0 if s * side >= 0 else (1.0 - ay) ** 1.5
        if vis < 0.05:
            continue
        a0 = at(s * w * 1.05, -0.035, nl * 0.5)
        a1 = at(s * w * 1.85, 0.008, nl * 0.32)
        a2 = at(s * w * 1.25, 0.045, nl * 0.4)
        cv.drawPath(tapered(sample_spline([a0, a1, a2], n=10), 0.003, 0.004, wmid=0.011), fill(sh2, alpha=0.62 * vis))
        # nostril
        nx_, ny_ = at(s * w * 0.72, 0.042, nl * 0.5)
        cv.drawPath(ellipse(nx_, ny_, w * 0.42 * (0.55 + 0.45 * vis), 0.011 * k, rot_deg=-s * 12), fill(mix(lc, sh2, 0.35), alpha=0.7 * vis))
    # underside of the tip (columella), a soft line rather than a tick
    w0 = at(-w * 1.05, 0.03, nl * 0.55)
    w1 = at(w * 1.05, 0.03, nl * 0.55)
    cb = (tip[0] + side * 0.006 * ay, tip[1] + 0.048)
    cv.drawPath(tapered(sample_spline([w0, cb, w1], n=12), 0.003, 0.003, wmid=0.010), fill(lc, alpha=0.5))
    # light on the tip and down the lit side of the bridge
    lxs = -1 if lx < 0 else 1
    cv.drawPath(ellipse(tip[0] + lxs * 0.01, tip[1] - 0.018, 0.018 * k, 0.012 * k), fill("#ffffff", alpha=0.22, blur=0.006))
    hl = [(top[0] - sd * 0.018, top[1] + 0.12), (mid[0] - sd * 0.022, mid[1] + 0.02), (tip[0] - sd * 0.016, tip[1] - 0.045)]
    cv.drawPath(tapered(sample_spline(hl, n=8), 0.004, 0.008, wmid=0.026), fill(mix(skin, "#ffffff", 0.45), alpha=0.16, blur=0.012))


def mouth_shape(H, st, P):
    my = st.get("mouth_y", 0.72)
    mz = H.surf_z(0, my) + 0.02
    cx, cy = H.pt(0, my, mz)
    f = H.fore(0.15, 1.0)
    op = max(0.0, P["m_open"])
    wide, rnd, smile = P["m_wide"], P["m_round"], P["m_smile"]
    hw = st.get("mouth_w", 0.13) * (1 + 0.32 * wide - 0.42 * rnd + 0.10 * smile)
    hw = max(hw, 0.035)
    corner_y = -smile * 0.035 + P["m_press"] * 0.0
    smirk = P["m_smirk"]
    h_open = op * st.get("mouth_h", 0.17) * (1 + 0.25 * rnd)
    return cx, cy, f, hw, corner_y, h_open, smirk


def draw_mouth(cv, H, st, P):
    cx, cy, f, hw, cyc, ho, smirk = mouth_shape(H, st, P)
    lc = st.get("line", "#2a1a14")
    rnd = P["m_round"]
    smile = P["m_smile"]
    cv.save()
    cv.translate(cx, cy)
    cv.scale(f, 1.0)
    L = (-hw, cyc - smirk * 0.03)
    R = (hw, cyc + smirk * 0.03 * -1)
    R = (hw, cyc + smirk * -0.03)
    L = (-hw, cyc + smirk * 0.03)
    if ho < 0.012:
        # closed mouth: a gently curved line
        mid_y = 0.012 * (1 - smile) + smile * 0.012 - P["m_press"] * 0.006
        pts = [L, (-hw * 0.45, mid_y * 0.8 + cyc * 0.3), (0, mid_y), (hw * 0.45, mid_y * 0.8 + cyc * 0.3), R]
        sm = sample_spline(pts, n=16)
        cv.drawPath(tapered(sm, 0.004, 0.004, wmid=st.get("mouth_line_w", 0.016) * (1 + 0.4 * P["m_press"])), fill(lc, alpha=0.85))
        # lower lip shading
        lip = [(-hw * 0.4, 0.055 + mid_y * 0.5), (0, 0.065 + mid_y * 0.5), (hw * 0.4, 0.055 + mid_y * 0.5)]
        cv.drawPath(tapered(sample_spline(lip, n=8), 0.002, 0.002, wmid=0.008), fill(st.get("skin_sh", "#c98f6c"), alpha=0.7))
        if st.get("lip_col"):
            lp = [(-hw * 0.6, mid_y + 0.006), (0, mid_y + 0.035), (hw * 0.6, mid_y + 0.006)]
            cv.drawPath(spline(lp + [(0, mid_y + 0.008)], closed=True), fill(st["lip_col"], alpha=0.5))
    else:
        top_y = -ho * 0.18 * (1 + rnd)
        bot_y = ho
        # opening outline
        k = 0.55 + 0.35 * rnd
        up = [L, (-hw * k, top_y - 0.004 + cyc * 0.4), (0, top_y + 0.006 * (1 - rnd)), (hw * k, top_y - 0.004 + cyc * 0.4), R]
        lo = [R, (hw * (0.62 + 0.3 * rnd), bot_y * 0.82 + cyc * 0.2), (0, bot_y), (-hw * (0.62 + 0.3 * rnd), bot_y * 0.82 + cyc * 0.2), L]
        U = sample_spline(up, n=18)
        Lo = sample_spline(lo, n=18)
        mouth = spline(U + Lo[1:-1], closed=True, tension=0.5)
        cv.drawPath(mouth, fill(st.get("mouth_in", "#4a1a1c")))
        cv.save()
        cv.clipPath(mouth, skia.ClipOp.kIntersect, True)
        # tongue
        if ho > 0.03:
            cv.drawPath(ellipse(0, bot_y + 0.01, hw * 0.62, max(0.02, ho * 0.42)), fill(st.get("tongue", "#b9545b")))
        # upper teeth
        teeth = P["m_teeth"]
        if teeth > 0.02:
            th = 0.028 * teeth + 0.006
            cv.drawPath(spline([(-hw, top_y - 0.02), (hw, top_y - 0.02), (hw * 0.9, top_y + th), (-hw * 0.9, top_y + th)], closed=True, corners=[0, 1, 2, 3]), fill("#fbf5ee"))
        cv.restore()
        cv.drawPath(spline(U, closed=False), stroke(lc, 0.013, alpha=0.9))
        cv.drawPath(spline(Lo, closed=False), stroke(lc, 0.008, alpha=0.55))
        # lower lip shadow below the opening
        lip = [(-hw * 0.35, bot_y + 0.045), (0, bot_y + 0.055), (hw * 0.35, bot_y + 0.045)]
        cv.drawPath(tapered(sample_spline(lip, n=8), 0.002, 0.002, wmid=0.008), fill(st.get("skin_sh", "#c98f6c"), alpha=0.7))
        if st.get("lip_col"):
            cv.drawPath(spline([(-hw * 0.55, bot_y + 0.004), (0, bot_y + 0.03), (hw * 0.55, bot_y + 0.004), (0, bot_y + 0.012)], closed=True), fill(st["lip_col"], alpha=0.45))
    # smile/frown corner accents
    if abs(smile) > 0.25 or abs(smirk) > 0.2:
        for sgn, (x, y) in ((-1, L), (1, R)):
            amt = smile + (-smirk if sgn < 0 else smirk) * 0.8
            if amt > 0.25:
                cv.drawPath(spline([(x + sgn * 0.005, y - 0.012), (x + sgn * 0.02, y + 0.008)], closed=False), stroke(lc, 0.007, alpha=min(0.6, (amt - 0.25) * 1.5)))
            elif amt < -0.25:
                cv.drawPath(spline([(x + sgn * 0.004, y + 0.004), (x + sgn * 0.018, y + 0.024)], closed=False), stroke(lc, 0.007, alpha=min(0.6, (-amt - 0.25) * 1.5)))
    cv.restore()


# ----------------------------------------------------------------------------
# Hair / beard / generic 3D shapes
# ----------------------------------------------------------------------------

def project_shape(H, pts3, P, sway=None):
    """Project a list of (x,y,z) head points with secondary hair motion."""
    A = np.asarray(pts3, dtype=float)
    R = H.p3(A)
    if sway is not None:
        sw = np.asarray(sway, dtype=float)
        t = P["t"]
        wx = P["hair_dx"] + P["wind"] * (0.6 * np.sin(t * 1.7 + A[:, 1] * 1.3) + 0.4 * np.sin(t * 2.9 + 1.0 + A[:, 1] * 2.1))
        wy = P["hair_dy"]
        R[:, 0] += sw * wx
        R[:, 1] += sw * wy * 0.5
    return [(float(x), float(y)) for x, y in R[:, :2]]


def auto_sway(pts3, start=0.2, k=0.35):
    return [max(0.0, (p[1] - start)) * k for p in pts3]


def draw_shape(cv, H, P, shape, st):
    pts = project_shape(H, shape["pts"], P, shape.get("sway") or auto_sway(shape["pts"], shape.get("sway_start", 0.2), shape.get("sway_k", 0.3)))
    path = spline(pts, closed=shape.get("closed", True), corners=shape.get("corners", ()), tension=shape.get("tension", 0.5))
    col = st[shape["col"]] if shape["col"] in st else shape["col"]
    cv.drawPath(path, fill(col))
    if shape.get("shade"):
        sh = shape["shade"]
        cv.save()
        cv.clipPath(path, skia.ClipOp.kIntersect, True)
        for sub in sh:
            spts = project_shape(H, sub["pts"], P, auto_sway(sub["pts"], shape.get("sway_start", 0.2), shape.get("sway_k", 0.3)))
            scol = st[sub["col"]] if sub["col"] in st else sub["col"]
            if sub.get("line"):
                cv.drawPath(tapered(sample_spline(spts, n=16), sub.get("w0", 0.006), sub.get("w1", 0.002), wmid=sub.get("wm", 0.016)), fill(scol, alpha=sub.get("a", 1.0)))
            else:
                cv.drawPath(spline(spts, closed=True, corners=sub.get("corners", ())), fill(scol, alpha=sub.get("a", 1.0), blur=sub.get("blur", 0.0)))
        cv.restore()
    if shape.get("outline", True):
        cv.drawPath(path, stroke(st.get("hair_line", st.get("line", "#2a1a14")), shape.get("lw", 0.018), alpha=0.9))
    return path


# ----------------------------------------------------------------------------
# Body
# ----------------------------------------------------------------------------

def body_pts(st, P):
    """Full robe outline in body units (origin = neck base): shoulders, waist, hips, hem."""
    sw = st.get("shoulder_w", 2.1)
    k = st.get("body_scale", 1.0)
    hem = st.get("hem_y", 13.0) * k
    by = P["byaw"] / 60.0
    br = P["breath"]
    up = -0.05 * br - 0.12 * P["shrug"]
    far = 1 - 0.18 * abs(by)
    l = -sw * (far if by > 0 else 1.0)
    r = sw * (far if by < 0 else 1.0)
    ww, hw, hm = st.get("waist_w", 0.80), st.get("hip_w", 0.86), st.get("hem_w", 0.93)
    sway = 0.06 * math.sin(P["t"] * 0.8)
    return [
        (l * 0.30, -0.06 + up * 0.3),
        (l * 0.66, 0.05 + up),
        (l * 0.95, 0.27 + up),
        (l * 1.04, 0.85),
        (l * 0.93, 1.75),
        (l * ww, 4.4 * k),
        (l * hw, 6.6 * k),
        (l * (hw + 0.02), 9.6 * k),
        (l * hm + sway, hem),
        (l * 0.45 + sway, hem + 0.14),
        (0.0 + sway, hem + 0.06),
        (r * 0.45 + sway, hem + 0.14),
        (r * hm + sway, hem),
        (r * (hw + 0.02), 9.6 * k),
        (r * hw, 6.6 * k),
        (r * ww, 4.4 * k),
        (r * 0.93, 1.75),
        (r * 1.04, 0.85),
        (r * 0.95, 0.27 + up),
        (r * 0.66, 0.05 + up),
        (r * 0.30, -0.06 + up * 0.3),
    ]


HEM_CORNERS = [8, 12]


def draw_neck(cv, st, P, head_origin, H):
    """Neck from body (0,0) to under the jaw (in body units)."""
    hx, hy = head_origin
    nw = st.get("neck_w", 0.40)
    top_y = hy + 0.95
    pts = [(-nw, 0.25), (-nw * 0.95, top_y - hy * 0.0 + 0.0), (nw * 0.95, top_y), (nw, 0.25)]
    pts = [(-nw * 1.05, 0.3), (hx - nw * 0.92, top_y), (hx + nw * 0.92, top_y), (nw * 1.05, 0.3)]
    path = spline(pts, closed=True, corners=[0, 1, 2, 3], tension=0.3)
    cv.drawPath(path, fill(st["skin"]))
    cv.drawPath(path, fill(st["skin_sh"], alpha=0.55))
    return path


def draw_body(cv, st, P, outfit):
    pts = body_pts(st, P)
    path = spline(pts, closed=True, corners=[5, 6], tension=0.45)
    outfit(cv, st, P, path, pts)
    return path


# ----------------------------------------------------------------------------
# Character
# ----------------------------------------------------------------------------

def flip_params(P):
    """Mirror a parameter set left-right (for characters drawn flipped)."""
    P = dict(P)
    P["yaw"] = -P["yaw"]
    P["byaw"] = -P["byaw"]
    P["gx"] = -P["gx"]
    P["roll"] = -P["roll"]
    P["hx"] = -P["hx"]
    P["bx"] = -P["bx"]
    P["light_x"] = -P["light_x"]
    P["rim_x"] = -P["rim_x"]
    P["hair_dx"] = -P["hair_dx"]
    P["eo_l"], P["eo_r"] = P["eo_r"], P["eo_l"]
    P["lo_l"], P["lo_r"] = P["lo_r"], P["lo_l"]
    P["br_l"], P["br_r"] = P["br_r"], P["br_l"]
    P["bi_l"], P["bi_r"] = P["bi_r"], P["bi_l"]
    P["tear_l"], P["tear_r"] = P["tear_r"], P["tear_l"]
    P["tear_dry_l"], P["tear_dry_r"] = P["tear_dry_r"], P["tear_dry_l"]
    P["m_smirk"] = -P["m_smirk"]
    P["arm_l"], P["arm_r"] = P["arm_r"], P["arm_l"]
    P["prop_l"], P["prop_r"] = P.get("prop_r"), P.get("prop_l")
    for k in ("arm_l", "arm_r"):
        if P[k]:
            a = dict(P[k])
            tg = list(a["target"])
            tg[0] = -tg[0]
            a["target"] = tuple(tg)
            if a.get("thumb") is not None:
                a["thumb"] = -a["thumb"]
            if a.get("hand_dir") is not None:
                a["hand_dir"] = (-a["hand_dir"][0], a["hand_dir"][1], a["hand_dir"][2])
            P[k] = a
    return P


class Character:
    def __init__(self, name, style, hair_back=(), hair_front=(), outfit=None, beard=None,
                 headwear_back=None, headwear_front=None, extra_face=None, ears=False, arms=None,
                 legs=True, leg_style=None):
        self.name = name
        self.st = style
        self.hair_back = hair_back
        self.hair_front = hair_front
        self.outfit = outfit
        self.beard = beard
        self.headwear_back = headwear_back
        self.headwear_front = headwear_front
        self.extra_face = extra_face
        self.ears = ears
        self.arms = arms
        self.legs = legs
        self.leg_style = leg_style or {}

    def draw(self, cv, P, x, y, S, flip=False, light=None, arms=None):
        """Draw with neck-base at screen (x, y); S = pixels per head unit."""
        st = self.st
        Q = dict(DEFAULT_P)
        Q.update(P)
        P = Q
        cv.save()
        cv.translate(x, y)
        cv.scale(-S if flip else S, S)
        if flip:
            P = flip_params(P)
        if arms is None:
            arms = self.arms
        lean = P["blean"]
        cv.translate(P["bx"], 0)
        cv.rotate(lean)
        neck_len = st.get("neck_len", 1.95)
        hox = P["hx"] + P["yaw"] / 60.0 * 0.08
        hoy = -neck_len + P["hy"] - 0.05 * P["breath"] - 0.08 * P["shrug"]
        H = Head(st, P)

        # head matrix (roll about the neck pivot)
        def head_matrix():
            m = skia.Matrix()
            m.setTranslate(hox, hoy)
            m.preRotate(P["roll"], 0, 0.9)
            return m

        # --- back hair (behind body)
        cv.save()
        cv.concat(head_matrix())
        for sh in self.hair_back:
            if sh.get("layer", "back") == "back":
                draw_shape(cv, H, P, sh, st)
        if self.headwear_back:
            self.headwear_back(cv, H, st, P)
        cv.restore()

        # --- legs and feet (behind the robe hem)
        if self.legs:
            draw_legs(cv, st, P, st.get("hem_y", 13.0) * st.get("body_scale", 1.0), self.leg_style)

        # --- neck and upper chest, one continuous piece of skin drawn before the clothes; the
        # robe's neckline opening frames it, so the throat flows down into the chest
        nw = st.get("neck_w", 0.40)
        nt = hoy + st.get("neck_top", 0.75)
        lc = st.get("line", "#2a1a14")
        # the neck runs in a straight line from where the turned chest holds it to where the head sits
        nb = P["byaw"] / 60.0 * 0.5          # base of the neck moves with the body (as the collar does)
        ntx = hox * 0.8
        def nx_(x0, y):
            u = min(1.0, max(0.0, (y - nt) / (0.06 - nt)))  # 0 at the top of the neck, 1 at its base
            return x0 + ntx * (1 - u) + nb * u
        top_l, top_r = (ntx - nw * 0.92, nt), (ntx + nw * 0.92, nt)
        skin_shape = spline([top_l, (nx_(-nw * 1.0, -0.5), -0.5), (nx_(-nw * 1.12, -0.16), -0.16), (nb - nw * 1.5, 0.06), (nb - 1.0, 0.3), (nb - 1.0, 1.4),
                             (nb + 1.0, 1.4), (nb + 1.0, 0.3), (nb + nw * 1.5, 0.06), (nx_(nw * 1.12, -0.16), -0.16), (nx_(nw * 1.0, -0.5), -0.5), top_r],
                            closed=True, corners=[0, 5, 6, 11], tension=0.4)
        # the throat sits in the shadow of the head and the chest catches the light
        cv.drawPath(skin_shape, fill(st["skin"], shader=lin_grad((0, nt), (0, 0.75), [
            mix(st["skin"], st["skin_sh"], 0.32), mix(st["skin"], st["skin_sh"], 0.18), st["skin"]], [0.0, 0.6, 1.0])))
        cv.save()
        cv.clipPath(skin_shape, skia.ClipOp.kIntersect, True)
        lxs = 1.0 if P["light_x"] < 0 else -1.0
        cv.drawPath(spline([(lxs * nw * 0.35, nt - 0.2), (lxs * nw * 1.4, nt - 0.2), (lxs * nw * 1.5, -0.05), (lxs * nw * 0.55, -0.2)], closed=True),
                    fill(st["skin_sh"], alpha=0.7, blur=0.03))
        cv.concat(head_matrix())
        jaw_sh = H.face_path()
        m = skia.Matrix()
        m.setTranslate(-P["light_x"] * 0.05, 0.22)
        jaw_sh.transform(m)
        cv.drawPath(jaw_sh, fill(st.get("skin_sh2", st["skin_sh"]), alpha=0.9))
        cv.restore()
        # the two neck muscles (sternocleidomastoids) running from behind the ears down to the notch
        # between the collarbones, in a soft V; shaded, not outlined
        cv.save()
        cv.clipPath(skin_shape, skia.ClipOp.kIntersect, True)
        sh2 = st.get("skin_sh2", st["skin_sh"])
        for s_ in (-1, 1):
            m0 = (ntx + s_ * nw * 0.72, nt + 0.12)
            m1 = (nx_(s_ * nw * 0.55, -0.45), -0.45)
            m2 = (nb + s_ * 0.07, 0.12)
            cv.drawPath(tapered(sample_spline([m0, m1, m2], n=14), 0.02, 0.012, wmid=0.05), fill(sh2, alpha=0.22, blur=0.03))
            # light along the front edge of each muscle
            cv.drawPath(tapered(sample_spline([(m0[0] - s_ * 0.06, m0[1] + 0.05), (m1[0] - s_ * 0.07, m1[1]), (m2[0] - s_ * 0.03, m2[1] - 0.04)], n=14),
                                0.01, 0.006, wmid=0.025), fill(mix(st["skin"], "#ffffff", 0.25), alpha=0.2, blur=0.02))
        cv.drawPath(ellipse(nb, 0.16, 0.07, 0.05), fill(sh2, alpha=0.2, blur=0.03))  # the notch at the base of the throat
        cv.restore()
        # outlines down the sides of the throat only, easing out toward the shoulders
        for s_ in (-1, 1):
            edge = [(ntx + s_ * nw * 0.92, nt), (nx_(s_ * nw * 1.0, -0.5), -0.5), (nx_(s_ * nw * 1.1, -0.2), -0.2), (nb + s_ * (nw * 1.12 + 0.1), -0.06)]
            cv.drawPath(tapered(sample_spline(edge, n=14), 0.024, 0.004, wmid=0.022), fill(lc, alpha=0.9))

        # --- body
        if arms:
            arms(cv, st, P, "behind")
        if self.outfit:
            self.outfit(cv, st, P, H, (hox, hoy))
        if arms:
            drape = None
            if self.outfit and getattr(self.outfit, "drape_side", None):
                drape = (self.outfit.drape_side, lambda: self.outfit.drape(cv, st, P, H, (hox, hoy)))
            arms(cv, st, P, "body", drape=drape)
        elif self.outfit and getattr(self.outfit, "drape_side", None):
            self.outfit.drape(cv, st, P, H, (hox, hoy))
        if self.outfit and hasattr(self.outfit, "collar"):
            self.outfit.collar(cv, st, P, H, (hox, hoy))

        # --- head
        cv.save()
        cv.concat(head_matrix())
        for sh in self.hair_back:
            if sh.get("layer") == "mid":
                draw_shape(cv, H, P, sh, st)
        face = H.face_path()
        if self.ears:
            draw_ears(cv, H, st, P)
        cv.drawPath(face, fill(st["skin"]))
        # cel shading: crescent opposite to light
        cv.save()
        cv.clipPath(face, skia.ClipOp.kIntersect, True)
        lx, ly = P["light_x"], P["light_y"]
        off = skia.Matrix()
        off.setTranslate(lx * 0.22, ly * 0.10 + 0.02)
        lit = skia.Path(face)
        lit.transform(off)
        lit.setFillType(skia.PathFillType.kInverseWinding)
        cv.drawPath(lit, fill(st["skin_sh"], alpha=0.75))
        # soft ambient gradient
        cv.drawRect(skia.Rect.MakeLTRB(-2, -2, 2, 2), fill("#000000", shader=lin_grad((0, -1.2), (0, 1.3), [(1.0, 1.0, 1.0, 0.10), (1.0, 1.0, 1.0, 0.0)])))
        # facial structure, as in more grown-up anime: light on the cheekbones, a soft hollow beneath
        # them on the shaded side, and shade under the lower lip and along the jaw
        sxl = 1.0 if lx > 0 else -1.0  # the lit side of the face
        for sx in (-1, 1):
            fx_ = H.fore(0.6 * sx, 0.8)
            cbx, cby = H.pt(0.62 * sx, 0.30)
            if sx == sxl:
                cv.drawPath(ellipse(cbx, cby, 0.2 * fx_, 0.07, -12 * sx), fill("#ffffff", alpha=0.07, blur=0.05))
            else:
                hx_, hy_ = H.pt(0.60 * sx, 0.52)
                cv.drawPath(ellipse(hx_, hy_, 0.17 * fx_, 0.11, 20 * sx), fill(st["skin_sh"], alpha=0.32, blur=0.07))
        my_ = st.get("mouth_y", 0.72)
        lx_, ly_ = H.pt(0.0, my_ + 0.13)
        cv.drawPath(ellipse(lx_, ly_, 0.12, 0.04), fill(st["skin_sh"], alpha=0.28, blur=0.035))
        # blush
        b = st.get("blush_base", 0.12) + P["blush"]
        if b > 0.01:
            for sx in (-1, 1):
                bx, by_ = H.pt(0.55 * sx, 0.43)
                cv.drawPath(ellipse(bx, by_, 0.20 * H.fore(0.55 * sx, 0.8), 0.09), fill(st.get("blush_col", "#e88a7a"), alpha=min(0.6, b), blur=0.05))
        if self.extra_face:
            self.extra_face(cv, H, st, P, "skin")
        if self.headwear_front is not None and hasattr(self.headwear_front, "cast_shadow"):
            self.headwear_front.cast_shadow(cv, H, st, P)
        # under-hair shadow on forehead
        for sh in self.hair_front:
            if sh.get("cast", True):
                pts = project_shape(H, sh["pts"], P, auto_sway(sh["pts"], sh.get("sway_start", 0.2), sh.get("sway_k", 0.3)))
                p = spline(pts, closed=True, corners=sh.get("corners", ()))
                m = skia.Matrix()
                m.setTranslate(-lx * 0.03, 0.07)
                p.transform(m)
                cv.drawPath(p, fill(st["skin_sh"], alpha=0.85))
        cv.restore()
        # rim light
        if P["rim"] > 0.01:
            cv.save()
            cv.clipPath(face, skia.ClipOp.kIntersect, True)
            off = skia.Matrix()
            off.setTranslate(-P["rim_x"] * 0.06, 0.0)
            inner = skia.Path(face)
            inner.transform(off)
            inner.setFillType(skia.PathFillType.kInverseWinding)
            cv.drawPath(inner, fill(st.get("rim_col", "#ffe2b8"), alpha=P["rim"]))
            cv.restore()
        cv.drawPath(face, stroke(st.get("line", "#2a1a14"), st.get("face_lw", 0.022), alpha=0.95))

        if self.beard:
            self.beard(cv, H, st, P)
        draw_nose(cv, H, st, P)
        draw_mouth(cv, H, st, P)
        if self.beard and hasattr(self.beard, "mustache"):
            self.beard.mustache(cv, H, st, P)
        if self.extra_face:
            self.extra_face(cv, H, st, P, "lines")
        # eyes: draw far eye first
        order = (-1, 1) if H.yaw < 0 else (1, -1)
        for side in order:
            draw_eye(cv, H, st, P, side)
        for side in order:
            draw_brow(cv, H, st, P, side)
        for sh in self.hair_front:
            draw_shape(cv, H, P, sh, st)
        if self.headwear_front:
            self.headwear_front(cv, H, st, P)
        cv.restore()
        if arms:
            arms(cv, st, P, "front")
        cv.restore()


def draw_ears(cv, H, st, P):
    for side in (-1, 1):
        f = H.fore(side * 1.0, 0.15)
        if f < 0.2:
            continue
        ex, ey = H.pt(side * 0.97, 0.18, -0.05)
        w = 0.13 * (0.35 + 0.65 * f)
        pts = [(ex, ey - 0.18), (ex + side * w, ey - 0.15), (ex + side * w * 1.15, ey + 0.02), (ex + side * w * 0.7, ey + 0.2), (ex, ey + 0.22)]
        p = spline(pts, closed=True)
        cv.drawPath(p, fill(st["skin"]))
        cv.drawPath(p, fill(st["skin_sh"], alpha=0.35))
        inner = [(ex + side * w * 0.3, ey - 0.1), (ex + side * w * 0.75, ey - 0.06), (ex + side * w * 0.6, ey + 0.1)]
        cv.drawPath(spline(inner, closed=False), stroke(st["skin_sh2"] if "skin_sh2" in st else st["skin_sh"], 0.02))
        cv.drawPath(p, stroke(st.get("line", "#2a1a14"), 0.018))
