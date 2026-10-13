"""Hair, beards and head cloths built from the rotated head silhouette.

Outer edges come from an expanded copy of the head's cross-section stack, so
hair always encloses the skull at any yaw; inner edges (hairlines, cloth
edges) are 3D points on the face surface that rotate with the head and are
clamped against the face silhouette so far-side hair never covers the face.
"""
import math

import numpy as np
import skia

from gfx import ellipse, fill, lin_grad, mix, rad_grad, sample_spline, spline, stroke, tapered


def _interp_slices(H, y):
    sl = H.sl
    ys = [s[0] for s in sl]
    return (np.interp(y, ys, [s[1] for s in sl]), np.interp(y, ys, [s[2] for s in sl]),
            np.interp(y, ys, [s[3] for s in sl]))


def extents(H, ys, vol, jaw=0.0):
    """Expanded silhouette extents at heights ys -> (right2d, left2d)."""
    cy, sy = math.cos(H.yaw), math.sin(H.yaw)
    R3, L3 = [], []
    for y in ys:
        w, d, zc = _interp_slices(H, y)
        v = vol(y) if callable(vol) else vol
        w2, d2 = w + v, d + v
        t = math.atan2(d2 * sy, max(w2 * cy, 1e-6))
        yy = y + (jaw * max(0.0, (y - 0.5) / 0.65) if y > 0.5 else 0.0)
        R3.append((w2 * math.cos(t), yy, zc + d2 * math.sin(t)))
        L3.append((-w2 * math.cos(t), yy, zc - d2 * math.sin(t)))
    R = H.p3(R3)
    L = H.p3(L3)
    return [tuple(map(float, p[:2])) for p in R], [tuple(map(float, p[:2])) for p in L]


def top_point(H, vol):
    y0 = H.sl[0][0]
    zc = H.sl[0][3]
    R = H.p3([(0.0, y0 - vol, zc)])
    return (float(R[0, 0]), float(R[0, 1]))


def surf_pts(H, pts2, dz=0.03):
    P3 = [(x, y, H.surf_z(x, y) + dz) for x, y in pts2]
    R = H.p3(P3)
    return [(float(p[0]), float(p[1])) for p in R]


def interp_x(pts, y):
    ys = [p[1] for p in pts]
    xs = [p[0] for p in pts]
    if ys[0] > ys[-1]:
        ys, xs = ys[::-1], xs[::-1]
    return float(np.interp(y, ys, xs))


def sway_offset(P, y, k=0.30, start=0.3):
    amt = max(0.0, y - start) * k
    t = P["t"]
    wx = P["hair_dx"] + P["wind"] * (0.6 * math.sin(t * 1.7 + y * 1.3) + 0.4 * math.sin(t * 2.9 + 1.0 + y * 2.1))
    return amt * wx, amt * P["hair_dy"] * 0.4


def far_margin(H, side, base=0.07):
    """How much hair may overlap the face edge on a side; negative keeps a gap on the far side.
    The near side is not limited (returns a large margin)."""
    yaw_deg = math.degrees(H.yaw)
    far = side * yaw_deg  # >0 => this side turns away
    if far <= 0:
        return base + 5.0 * min(1.0, -far / 6.0)
    return base - 0.10 * min(1.0, far / 14.0)


def clamp_inner(pts, H, side, margin, y_from=-0.7, ramp=0.25):
    """Keep an inner hair edge from covering more than `margin` of the face silhouette.

    The clamp fades in over `ramp` around y_from, so a point drifting across that
    height as the head nods moves smoothly instead of jumping."""
    R, L = extents(H, list(np.linspace(-1.2, 1.15, 16)), 0.0)
    edge = R if side > 0 else L
    out = []
    for x, y in pts:
        u = min(1.0, max(0.0, (y - (y_from - ramp / 2)) / ramp))
        w = u * u * (3 - 2 * u)
        if w > 0:
            fx = interp_x(edge, y)
            cx = max(x, fx - margin) if side > 0 else min(x, fx + margin)
            x = x + (cx - x) * w
        out.append((x, y))
    return out


def edge_tufts(edge, seed, r_lo, r_hi, step=(0.035, 0.07), jitter=0.015):
    """Irregular tufts of curls along an edge (a polyline): blobs of varying size and spacing at
    fixed fractions along the edge, so they stay put from frame to frame."""
    pts = np.asarray(edge, float)
    if len(pts) < 2:
        return []
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    total = cum[-1]
    if total < 1e-6:
        return []
    rng = np.random.default_rng(seed)
    out = []
    t = rng.uniform(0.0, step[0])
    while t < 1.0:
        s = t * total
        i = min(int(np.searchsorted(cum, s, side="right")) - 1, len(seg) - 1)
        f = (s - cum[i]) / max(seg[i], 1e-9)
        p = pts[i] + (pts[i + 1] - pts[i]) * f
        d = (pts[i + 1] - pts[i]) / max(seg[i], 1e-9)
        n = np.array([-d[1], d[0]])
        r = rng.uniform(r_lo, r_hi)
        p = p + n * rng.uniform(-jitter, jitter)
        out.append(ellipse(float(p[0]), float(p[1]), r, r * rng.uniform(0.72, 0.95), rng.uniform(0, 180)))
        t += rng.uniform(*step)
    return out


def wavy_edge(pts, seed, amp, away_from, n_per=6, outward=True):
    """Resample a polyline and push it out (or in) along its normal by an irregular, curl-like
    amount: a natural curly edge drawn as one continuous line."""
    pts = np.asarray(pts, float)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    total = cum[-1]
    if total < 1e-6:
        return [tuple(p) for p in pts]
    n = max(8, int(total / 0.03))
    rng = np.random.default_rng(seed)
    f1, f2 = rng.uniform(55, 75), rng.uniform(120, 160)
    p1, p2 = rng.uniform(0, 6.28, 2)
    c = np.asarray(away_from, float)
    out = []
    for k in range(n + 1):
        s = total * k / n
        i = min(int(np.searchsorted(cum, s, side="right")) - 1, len(seg) - 1)
        f = (s - cum[i]) / max(seg[i], 1e-9)
        p = pts[i] + (pts[i + 1] - pts[i]) * f
        d = (pts[i + 1] - pts[i]) / max(seg[i], 1e-9)
        nrm = np.array([-d[1], d[0]])
        if np.dot(nrm, p - c) < 0:
            nrm = -nrm
        if not outward:
            nrm = -nrm
        u = s / total
        bump = 0.55 * abs(math.sin(u * f1 + p1)) + 0.45 * abs(math.sin(u * f2 + p2)) ** 2
        taper = min(1.0, u / 0.04, (1 - u) / 0.04)  # meet the ends exactly
        out.append(tuple(p + nrm * amp * bump * taper))
    return out


def coil(cx, cy, r, turns=1.15, phase=0.0, squash=0.8):
    """A small tight curl: a spiral that closes in on itself."""
    pts = []
    n = 14
    for k in range(n):
        u = k / (n - 1)
        th = phase + u * turns * 2 * math.pi
        rr = r * (1.0 - 0.45 * u)
        pts.append((cx + rr * math.cos(th), cy + rr * math.sin(th) * squash))
    return spline(pts, closed=False)


class LongHair:
    """Center-parted, shoulder-length wavy hair (Jesus)."""

    def __init__(self, layer="front", vol_top=0.16, vol_side=0.20, y_hang=0.40, tip_y=2.35,
                 hairline=None, wave=0.03):
        self.layer = layer
        self.vol_top = vol_top
        self.vol_side = vol_side
        self.y_hang = y_hang
        self.tip_y = tip_y
        self.wave = wave
        self.hairline = hairline or [(0.0, -0.93), (0.18, -0.86), (0.40, -0.76), (0.62, -0.63),
                                     (0.80, -0.45), (0.90, -0.21), (0.93, 0.08), (0.91, 0.40)]

    def vol(self, y):
        return self.vol_top + (self.vol_side - self.vol_top) * min(1.0, max(0.0, (y + 1.2) / 1.5))

    def __call__(self, cv, H, st, P):
        if self.layer == "back":
            self.draw_back(cv, H, st, P)
        else:
            self.draw_front(cv, H, st, P)

    def lock(self, H, P, side, outer_anchor, inner_anchor):
        s = side
        ox, oy = outer_anchor
        ix, iy = inner_anchor
        tip = self.tip_y
        w = self.wave
        outer = []
        for y in np.linspace(oy, tip - 0.35, 6)[1:]:
            u = (y - oy) / (tip - oy)
            x = ox + s * (0.08 * math.sin(u * math.pi) + 0.05 * u) + s * w * math.sin(y * 5.0)
            dx, dy = sway_offset(P, y)
            outer.append((x + dx, y + dy))
        # three pointed tips with notches between
        base_x = ox + s * 0.06
        tips = []
        spec = [(0.0, 0.02, True), (-0.16, -0.16, False), (-0.30, -0.10, True)]
        for (dxk, dyk, is_tip) in spec:
            y = tip + dyk
            dx, dy = sway_offset(P, y)
            tips.append((base_x + s * dxk + dx, y + dy))
        inner = []
        for y in np.linspace(tip - 0.45, iy, 6)[:-1]:
            u = (y - iy) / max(tip - iy, 1e-3)
            x = ix + s * (0.04 * u) - s * w * 0.5 * math.sin(y * 4.6 + 1.0)
            dx, dy = sway_offset(P, y)
            inner.append((x + dx, y + dy))
        return outer, tips, inner

    def geometry(self, H, P):
        ys = list(np.linspace(-1.66, self.y_hang, 16))
        R, L = extents(H, ys, self.vol)
        top = top_point(H, self.vol_top)
        hl_r = surf_pts(H, self.hairline, dz=0.04)
        hl_l = surf_pts(H, [(-x, y) for x, y in self.hairline], dz=0.04)
        hl_r = clamp_inner(hl_r, H, 1, far_margin(H, 1))
        hl_l = clamp_inner(hl_l, H, -1, far_margin(H, -1))
        # never let the hairline cross the outer edge
        hl_r = [(min(x, interp_x(R, y) - 0.05), y) for x, y in hl_r]
        hl_l = [(max(x, interp_x(L, y) + 0.05), y) for x, y in hl_l]
        r_out, r_tips, r_in = self.lock(H, P, 1, R[-1], hl_r[-1])
        l_out, l_tips, l_in = self.lock(H, P, -1, L[-1], hl_l[-1])
        r_in = clamp_inner(r_in, H, 1, far_margin(H, 1, 0.0) - 0.02, y_from=0.0)
        l_in = clamp_inner(l_in, H, -1, far_margin(H, -1, 0.0) - 0.02, y_from=0.0)
        return dict(top=top, R=R, L=L, hl_r=hl_r, hl_l=hl_l, r=(r_out, r_tips, r_in), l=(l_out, l_tips, l_in))

    def front_path(self, g):
        top, R, L = g["top"], g["R"], g["L"]
        r_out, r_tips, r_in = g["r"]
        l_out, l_tips, l_in = g["l"]
        seq = [top] + R[1:] + r_out
        corners = []
        n0 = len(seq)
        seq += r_tips
        corners += list(range(n0, n0 + len(r_tips)))
        seq += r_in + g["hl_r"][::-1]
        corners.append(len(seq) - 1)  # the part
        seq += g["hl_l"][1:] + l_in[::-1]
        n1 = len(seq)
        seq += l_tips[::-1]
        corners += list(range(n1, n1 + len(l_tips)))
        seq += l_out[::-1] + L[::-1][1:-1]
        return spline(seq, closed=True, corners=corners, tension=0.5)

    def draw_front(self, cv, H, st, P):
        g = self.geometry(H, P)
        path = self.front_path(g)
        lc = st.get("hair_line", "#1e1009")
        cv.drawPath(path, fill(st["hair"]))
        cv.save()
        cv.clipPath(path, skia.ClipOp.kIntersect, True)
        lx = P["light_x"]
        sx = 1.0 if lx < 0 else -1.0
        # broad, soft shadow on the side away from the key light + darker toward the bottom
        cv.drawPath(spline([(sx * 0.1, -2.2), (sx * 2.3, -2.2), (sx * 2.3, 3.0), (sx * 0.85, 3.0), (sx * 0.8, 0.2), (sx * 0.45, -1.2)], closed=True),
                    fill(st["hair_sh"], alpha=0.45, blur=0.18))
        cv.drawRect(skia.Rect.MakeLTRB(-3, 0.6, 3, 3.2), fill("#000000", shader=lin_grad((0, 0.6), (0, 2.6), [(0, 0, 0, 0), (0.05, 0.02, 0.0, 0.35)])))
        # inner shadow along the hairline
        for hl in (g["hl_r"], g["hl_l"]):
            cv.drawPath(tapered(sample_spline(hl, n=20), 0.04, 0.12, wmid=0.12), fill(st["hair_sh"], alpha=0.85, blur=0.025))
        # clump separation lines
        for s in (1, -1):
            side = g["R"] if s > 0 else g["L"]
            out, tips, inner = g["r"] if s > 0 else g["l"]
            for k in range(3):
                a = surf_pts(H, [(s * (0.10 + 0.13 * k), -1.30 + 0.06 * k)], dz=0.13)[0]
                yb = -0.55 + 0.32 * k
                b = (interp_x(side, yb) - s * (0.22 - 0.03 * k), yb)
                tip = tips[2 * (2 - k)] if 2 * (2 - k) < len(tips) else tips[-1]
                c = ((b[0] + tip[0]) / 2 + s * 0.04, (b[1] + tip[1]) / 2)
                cv.drawPath(tapered(sample_spline([a, b, c, (tip[0] - s * 0.02, tip[1] - 0.18)], n=26), 0.003, 0.002, wmid=0.026), fill(st["hair_sh"], alpha=0.8))
            # highlight band ("angel ring"): soft sheen across the crown with a few glints
            us = np.linspace(0.10, 0.95, 9)
            band_top = [surf_pts(H, [(s * u * 0.98, -1.70 + 0.30 * u * u)], dz=0.17)[0] for u in us]
            band_bot = [surf_pts(H, [(s * u * 0.98, -1.70 + 0.30 * u * u + 0.07 + 0.02 * math.sin(u * 9))], dz=0.17)[0] for u in us]
            cv.drawPath(spline(band_top + band_bot[::-1], closed=True, corners=[0, len(us) - 1, len(us), 2 * len(us) - 1]), fill(st["hair_hl"], alpha=0.42, blur=0.012))
            for k in range(3):
                u = 0.25 + 0.22 * k
                a = surf_pts(H, [(s * u, -1.66 + 0.30 * u * u)], dz=0.18)[0]
                cv.drawPath(tapered([a, (a[0] + s * 0.05, a[1] + 0.012), (a[0] + s * 0.10, a[1] + 0.035)], 0.004, 0.0, wmid=0.016), fill("#ffffff", alpha=0.22))
        # backlight: only a faint sheen hugging the very edge of the hair (a broad tan band read
        # as a smear of mud)
        if P["rim"] > 0.01:
            rs = 1 if P["rim_x"] > 0 else -1
            side = g["R"] if rs > 0 else g["L"]
            rim = [(x - rs * 0.006, y) for x, y in side[2:-2]]
            cv.drawPath(tapered(sample_spline(rim, n=24), 0.002, 0.002, wmid=0.012), fill(st["hair_hl"], alpha=0.35 * P["rim"], blur=0.006))
        cv.restore()
        cv.drawPath(path, stroke(lc, 0.02))
        # loose strands over the forehead and outside the silhouette
        t = P["t"]
        for s in (1, -1):
            dx, _ = sway_offset(P, 0.8, k=0.05)
            a = surf_pts(H, [(s * 0.04, -1.24), (s * 0.20, -0.95), (s * 0.17, -0.72)], dz=0.06)
            a[2] = (a[2][0] + dx, a[2][1])
            wisp = sample_spline(a, n=12)
            cv.drawPath(tapered([(x + 0.01, y + 0.02) for x, y in wisp], 0.03, 0.0, wmid=0.024), fill(st["skin_sh"], alpha=0.35, blur=0.012))
            cv.drawPath(tapered(wisp, 0.03, 0.0, wmid=0.024), fill(st["hair"]))
            cv.drawPath(tapered([(x - s * 0.004, y) for x, y in wisp], 0.008, 0.0, wmid=0.006), fill(st["hair_hl"], alpha=0.5))
            side = g["R"] if s > 0 else g["L"]
            p0 = side[4]
            dx2, dy2 = sway_offset(P, 1.0, k=0.25)
            strand = [(p0[0] - s * 0.03, p0[1]), (p0[0] - s * 0.01, p0[1] + 0.35), (p0[0] - s * 0.02 + dx2 * 0.5, p0[1] + 0.8)]
            cv.drawPath(spline(strand, closed=False), stroke(lc, 0.006, alpha=0.45))

    def cast_shadow(self, cv, H, st, P):
        """Shadow the front hair casts onto the face (call while clipped to the face)."""
        if self.layer != "front":
            return
        g = self.geometry(H, P)
        path = self.front_path(g)
        m = skia.Matrix()
        m.setTranslate(-P["light_x"] * 0.03, 0.075)
        path.transform(m)
        cv.drawPath(path, fill(st["skin_sh"], alpha=0.85, blur=0.016))

    def draw_back(self, cv, H, st, P):
        """The hair falling behind the shoulders: soft locks with strand texture, lighter where it
        catches the light at the sides, shadowed behind the neck, ending in uneven wavy tips."""
        ys = list(np.linspace(-1.66, self.y_hang, 14))
        R, L = extents(H, ys, lambda y: self.vol(y) + 0.05)
        top = top_point(H, self.vol_top + 0.04)
        rb, lb = [], []
        for y in np.linspace(self.y_hang + 0.3, self.tip_y - 0.1, 5):
            dx, dy = sway_offset(P, y, k=0.22)
            u = (y - self.y_hang) / (self.tip_y - self.y_hang)
            rb.append((R[-1][0] + 0.16 * math.sin(u * 2.4) + 0.14 + dx, y + dy))
            lb.append((L[-1][0] - 0.16 * math.sin(u * 2.4) - 0.14 + dx, y + dy))
        # uneven locks along the bottom: each tip a slightly different length, curling outward
        bottom = []
        xr, xl = rb[-1][0], lb[-1][0]
        n_tips = 7
        lens = [0.16, 0.30, 0.10, 0.24, 0.12, 0.28, 0.18]
        for k in range(n_tips):
            for half in (0, 1):
                u = (k + 0.5 * half + 0.25) / n_tips
                x = xr + (xl - xr) * u
                if half == 0:
                    y = self.tip_y + lens[k] + 0.04 * math.sin(u * math.pi)
                    x += 0.05 * (1 if x > 0 else -1)
                else:
                    y = self.tip_y - 0.06 + 0.04 * math.sin(u * math.pi)
                dx, dy = sway_offset(P, y, k=0.22)
                bottom.append((x + dx, y + dy))
        pts = [top] + R[1:] + rb + bottom + lb[::-1] + L[::-1][1:-1]
        corners = list(range(1 + len(R) - 1 + len(rb), 1 + len(R) - 1 + len(rb) + len(bottom), 2))
        path = spline(pts, closed=True, corners=corners, tension=0.5)
        lc = st.get("hair_line", "#1e1009")
        cv.drawPath(path, fill(mix(st["hair"], st["hair_sh"], 0.55)))
        cv.save()
        cv.clipPath(path, skia.ClipOp.kIntersect, True)
        # volume: the outer sides catch light, the hair right behind the neck sits in soft shadow
        for side, pts_ in ((1, R[4:] + rb), (-1, L[4:] + lb)):
            cv.drawPath(tapered(sample_spline(pts_, n=24), 0.10, 0.22, wmid=0.30), fill(st["hair"], alpha=0.55, blur=0.06))
        cv.drawPath(ellipse(0.0, self.y_hang + 0.9, 0.55, 1.2), fill("#000000", alpha=0.16, blur=0.25))
        # locks hanging straight down behind the neck, from below the ears
        for side in (1, -1):
            for k in range(5):
                x0 = side * (0.42 + 0.11 * k)
                y0 = 0.15 + 0.05 * k
                dx, dy = sway_offset(P, self.tip_y, k=0.22)
                lock = sample_spline([(x0, y0), (x0 + side * 0.04, (y0 + self.tip_y) / 2), (x0 + side * 0.10 + dx, self.tip_y - 0.1 * (k % 2))], n=12)
                light = k % 2 == 0
                cv.drawPath(tapered(lock, 0.005, 0.0, wmid=0.02 if light else 0.016),
                            fill(st["hair_hl"] if light else lc, alpha=0.32 if light else 0.5))
        # strands flowing from the crown down to the tips
        for side, edge, hang in ((1, R, rb), (-1, L, lb)):
            for k in range(9):
                f = (k + 0.5) / 9
                i0 = 2 + int(f * (len(edge) - 4))
                a = edge[i0]
                ex = hang[min(len(hang) - 1, 1 + int(f * 3))]
                y_end = self.tip_y + 0.05 - 0.12 * (k % 3)
                inward = 0.25 + 0.5 * f
                b = (a[0] - side * (0.10 + 0.05 * k % 2), (a[1] + y_end) * 0.45)
                c = (ex[0] - side * inward, y_end)
                dx, dy = sway_offset(P, y_end, k=0.22)
                c = (c[0] + dx, c[1] + dy)
                strand = sample_spline([a, b, c], n=14)
                col = lc if k % 3 != 1 else st["hair_hl"]
                cv.drawPath(tapered(strand, 0.004, 0.0, wmid=0.016 if k % 3 != 1 else 0.012),
                            fill(col, alpha=0.5 if k % 3 != 1 else 0.3))
        cv.restore()
        cv.drawPath(path, stroke(lc, 0.02))


class Beard:
    """Short trimmed beard hugging the jaw, plus a mustache."""

    def __init__(self, vol=0.035, chin=0.07, inner=None, col="beard", col_sh="beard_sh", grey=0.0,
                 alpha=0.92, mustache=True, tuft_len=0.035, top=0.0):
        self.top = top
        self.vol_ = vol
        self.chin = chin
        self.inner = inner or [(0.97, 0.10), (0.95, 0.35), (0.87, 0.54), (0.69, 0.66), (0.44, 0.73),
                               (0.26, 0.79), (0.13, 0.845), (0.0, 0.86)]
        self.col = col
        self.col_sh = col_sh
        self.grey = grey
        self.alpha = alpha
        self.has_mustache = mustache
        self.tuft_len = tuft_len
        b = self

        class _M:
            def __call__(self_, cv, H, st, P):
                if b.has_mustache:
                    b.draw_mustache(cv, H, st, P)
        self.mustache = _M()

    def geometry(self, H, P):
        jaw = H.jaw
        ys = list(np.linspace(self.top, H.sl[-1][0] - 0.01, 11))

        def vol(y):
            v = self.vol_ + self.chin * max(0.0, (y - 0.6) / 0.5) ** 1.5
            if self.top > 0.0:  # a beard that starts low on the cheek thickens toward the jaw
                v *= 0.25 + 0.75 * float(np.clip((y - self.top) / 0.35, 0, 1))
            return v
        R, L = extents(H, ys, vol, jaw=jaw)
        chin_y = H.sl[-1][0] + self.chin * 1.1
        _, _, zc_end = _interp_slices(H, H.sl[-1][0])
        bot = H.p3([(0.0, chin_y + jaw, zc_end + 0.04)])[0]
        bot = (float(bot[0]), float(bot[1]))
        mo = P["m_open"] * self.mouth_h(H)
        inner_r = [(x, y + (mo if y > 0.7 else 0.0)) for x, y in self.inner]
        IR = surf_pts(H, inner_r, dz=0.02)
        IL = surf_pts(H, [(-x, y) for x, y in inner_r], dz=0.02)
        IR = [(min(x, interp_x(R, y) - 0.025), y) for x, y in IR]
        IL = [(max(x, interp_x(L, y) + 0.025), y) for x, y in IL]
        return R, L, bot, IR, IL

    def mouth_h(self, H):
        return H.st.get("mouth_h", 0.17)

    def __call__(self, cv, H, st, P):
        R, L, bot, IR, IL = self.geometry(H, P)
        ring = R + [bot] + L[::-1] + IL + IR[::-1][1:]
        n_out = len(R) + 1 + len(L)
        path = spline(ring, closed=True, corners=[0, n_out - 1, n_out], tension=0.5)
        col = st[self.col]
        # soft edge then solid body
        cv.drawPath(path, fill(col, alpha=0.45 * self.alpha, blur=0.025))
        cv.drawPath(path, fill(col, alpha=self.alpha))
        cv.save()
        cv.clipPath(path, skia.ClipOp.kIntersect, True)
        lx = P["light_x"]
        sx = 1.0 if lx < 0 else -1.0
        cv.drawPath(spline([(sx * 0.1, 0.2), (sx * 1.5, 0.0), (sx * 1.5, 1.8), (sx * 0.2, 1.6)], closed=True), fill(st[self.col_sh], alpha=0.45))
        rng = np.random.default_rng(7)
        for k in range(30):
            u = rng.uniform(-0.9, 0.9)
            y0 = 0.25 + rng.uniform(0, 0.95)
            p0 = surf_pts(H, [(u, y0)], dz=0.05)[0]
            ln = 0.05 + rng.uniform(0, 0.05)
            cv.drawPath(tapered([p0, (p0[0] - u * 0.03, p0[1] + ln)], 0.007, 0.0), fill(st[self.col_sh], alpha=0.5))
        if self.grey > 0:
            for k in range(36):
                u = rng.uniform(-0.9, 0.9)
                y0 = 0.3 + rng.uniform(0, 0.95)
                p0 = surf_pts(H, [(u, y0)], dz=0.05)[0]
                cv.drawPath(tapered([p0, (p0[0] - u * 0.03, p0[1] + 0.08)], 0.007, 0.0), fill("#ecebe6", alpha=0.55 * self.grey))
        cv.restore()
        lc = st.get("hair_line", "#1e1009")
        edge = R[2:] + [bot] + L[::-1][:-2]
        cv.drawPath(spline(edge, closed=False), stroke(lc, 0.016, alpha=0.85))
        if self.tuft_len > 0:
            for i in range(1, len(edge) - 1, 2):
                x, y = edge[i]
                d = 0.015 if x < bot[0] else -0.015
                cv.drawPath(tapered([(x, y - 0.02), (x + d, y + self.tuft_len)], 0.014, 0.0), fill(lc, alpha=0.75))

    def draw_mustache(self, cv, H, st, P):
        my = st.get("mouth_y", 0.66)
        mo = P["m_open"]
        sm = P["m_smile"]
        mw = st.get("mouth_w", 0.13)
        # right half outline: top edge from center to corner, then lower edge back to center
        top = [(0.0, my - 0.105), (0.10, my - 0.10), (0.20, my - 0.075), (mw + 0.11, my - 0.01 - sm * 0.03)]
        corner = (mw + 0.13, my + 0.075 - sm * 0.02)
        bottom = [(mw + 0.04, my + 0.005 - sm * 0.02), (0.10, my - 0.022 - mo * 0.012), (0.0, my - 0.02 - mo * 0.016)]
        R = surf_pts(H, top + [corner] + bottom, dz=0.05)
        Lp = surf_pts(H, [(-x, y) for x, y in top + [corner] + bottom], dz=0.05)
        mid_b = ((R[7][0] + Lp[7][0]) / 2, (R[7][1] + Lp[7][1]) / 2)
        mid_t = ((R[0][0] + Lp[0][0]) / 2, (R[0][1] + Lp[0][1]) / 2)
        ring = [mid_t, R[1], R[2], R[3], R[4], R[5], R[6], mid_b, Lp[6], Lp[5], Lp[4], Lp[3], Lp[2], Lp[1]]
        path = spline(ring, closed=True, corners=[4, 10], tension=0.45)
        cv.drawPath(path, fill(st[self.col], alpha=0.5, blur=0.012))
        cv.drawPath(path, fill(st[self.col], alpha=0.92))
        cv.save()
        cv.clipPath(path, skia.ClipOp.kIntersect, True)
        for sgn in (1, -1):
            for k in range(4):
                x0 = sgn * (0.04 + 0.06 * k)
                p0 = surf_pts(H, [(x0, my - 0.09)], dz=0.06)[0]
                p1 = surf_pts(H, [(x0 + sgn * 0.05, my - 0.02)], dz=0.06)[0]
                cv.drawPath(tapered([p0, p1], 0.006, 0.0), fill(st[self.col_sh], alpha=0.6))
        cv.restore()
        lc = st.get("hair_line", "#1e1009")
        cv.drawPath(spline([R[3], R[2], R[1], mid_t, Lp[1], Lp[2], Lp[3]], closed=False), stroke(lc, 0.009, alpha=0.45))


class ShortCurly:
    """Short curly hair cap (Peter): scalloped outline made of curls."""

    def __init__(self, vol=0.13, hairline=None, y_side=0.30, curl_r=0.062, sideburn=None, side_taper=None):
        self.side_taper = side_taper  # (y_full, y_tucked): below y_full the sides thin toward the ear
        self.vol = vol
        self.y_side = y_side
        self.curl_r = curl_r
        self.sideburn = sideburn  # (x, y_top, y_bottom, width): short strip in front of the ear
        self.hairline = hairline or [(0.0, -0.88), (0.30, -0.86), (0.58, -0.8), (0.80, -0.63),
                                     (0.93, -0.39), (0.97, -0.10), (0.98, 0.30)]

    def geometry(self, H, P):
        ys = list(np.linspace(-1.66, self.y_side, 14))
        vol = self.vol
        if self.side_taper:
            y0, y1 = self.side_taper
            vol = lambda y: self.vol * (1.0 - 0.85 * float(np.clip((y - y0) / (y1 - y0), 0, 1)) ** 1.5)
        R, L = extents(H, ys, vol)
        top = top_point(H, self.vol)
        hl_r = surf_pts(H, self.hairline, dz=0.04)
        hl_l = surf_pts(H, [(-x, y) for x, y in self.hairline], dz=0.04)
        # short hair hugs the head: its edge always overlaps the face a little, even on the side
        # turned away (there is no hair behind it to fill a gap)
        hl_r = clamp_inner(hl_r, H, 1, max(0.03, far_margin(H, 1, 0.03)))
        hl_l = clamp_inner(hl_l, H, -1, max(0.03, far_margin(H, -1, 0.03)))
        hl_r = [(min(x, interp_x(R, y) - 0.04), y) for x, y in hl_r]
        hl_l = [(max(x, interp_x(L, y) + 0.04), y) for x, y in hl_l]
        return top, R, L, hl_r, hl_l

    def path(self, g):
        top, R, L, hl_r, hl_l = g
        seq = [top] + R[1:] + hl_r[::-1][:-1] + [((hl_r[0][0] + hl_l[0][0]) / 2, (hl_r[0][1] + hl_l[0][1]) / 2)] + hl_l[1:] + L[::-1][1:-1]
        n = len([top] + R[1:])
        return spline(seq, closed=True, corners=[n - 1, n, len(seq) - len(L[::-1][1:-1]) - 1, len(seq) - len(L[::-1][1:-1])], tension=0.5)

    def __call__(self, cv, H, st, P):
        g = self.geometry(H, P)
        top, R, L, hl_r, hl_l = g
        path = self.path(g)
        lc = st.get("hair_line", "#120c08")
        col, sh, hl = st["hair"], st["hair_sh"], st["hair_hl"]
        r = self.curl_r
        # irregular tufts round the outside and smaller ones along the hairline; outlined only as one
        # silhouette, so the hair reads as a single springy mass rather than a ring of balls
        # one irregular curly outline: curls push out round the head and dip onto the forehead
        face_c = H.pt(0.0, -0.2)
        outer = wavy_edge(R[::-1] + [top] + L[1:], 5, r * 1.1, face_c)
        line = wavy_edge(hl_r[::-1] + [((hl_r[0][0] + hl_l[0][0]) / 2, (hl_r[0][1] + hl_l[0][1]) / 2)] + hl_l[1:], 9, r * 0.75, face_c, outward=False)
        mass = spline(outer + line[::-1], closed=True, corners=[0, len(outer) - 1, len(outer), len(outer) + len(line) - 1], tension=0.4)
        if self.sideburn:
            # a short sideburn in front of each ear, thinning out downward: the hair stops here and
            # the beard begins lower down, so the two read as separate growths
            sbx, y0, y1, sbw = self.sideburn
            for s_ in (1, -1):
                ex = interp_x(R if s_ > 0 else L, y0)
                pts = surf_pts(H, [(s_ * sbx, y0), (s_ * sbx, (y0 + y1) / 2), (s_ * (sbx + 0.01), y1)], dz=0.03)
                pts = [(min(x, ex - 0.01) if s_ > 0 else max(x, ex + 0.01), y) for x, y in pts]
                strip = tapered(sample_spline(pts, n=10), sbw, sbw * 0.25, wmid=sbw * 0.85)
                cv.drawPath(strip, fill(col, alpha=0.9))
                cv.drawPath(strip, fill(sh, alpha=0.3, blur=0.01))
        cv.drawPath(mass, stroke(lc, 0.028, alpha=0.9))
        cv.drawPath(mass, fill(col))
        cv.save()
        cv.clipPath(mass, skia.ClipOp.kIntersect, True)
        lx = P["light_x"]
        sx = 1.0 if lx < 0 else -1.0
        cv.drawPath(spline([(sx * 0.1, -2.3), (sx * 2.2, -2.3), (sx * 2.2, 1.0), (sx * 0.7, 1.0), (sx * 0.4, -1.2)], closed=True), fill(sh, alpha=0.5, blur=0.06))
        # depth near the face, sheen across the crown
        for hl_edge in (hl_r, hl_l):
            cv.drawPath(tapered(sample_spline(hl_edge, n=14), 0.05, 0.08, wmid=0.1), fill(sh, alpha=0.55, blur=0.04))
        crown = [surf_pts(H, [(u, -1.5 + 0.35 * u * u)], dz=self.vol + 0.03)[0] for u in np.linspace(-0.75, 0.75, 9)]
        cv.drawPath(tapered(sample_spline(crown, n=20), 0.02, 0.02, wmid=0.12), fill(hl, alpha=0.32, blur=0.05))
        # the texture of tight curls, built up softly: clumps of shade and light first, then short open
        # curl strokes (no closed loops, which read as little circles)
        rng = np.random.default_rng(3)
        for k in range(26):
            u = rng.uniform(-0.95, 0.95)
            v = rng.uniform(-1.7, -0.95 + 0.9 * abs(u) ** 2)
            p = surf_pts(H, [(u, v)], dz=self.vol + 0.02)[0]
            rr = rng.uniform(0.07, 0.13)
            light = k % 3 == 0
            cv.drawPath(ellipse(p[0], p[1], rr, rr * 0.75, rng.uniform(0, 180)),
                        fill(hl if light else sh, alpha=0.18 if light else 0.32, blur=rr * 0.5))
        for k in range(70):
            u = rng.uniform(-0.98, 0.98)
            v = rng.uniform(-1.72, -0.9 + 0.95 * abs(u) ** 2)
            p = surf_pts(H, [(u, v)], dz=self.vol + 0.02)[0]
            rc = rng.uniform(0.022, 0.038)
            arc = skia.Path()
            arc.addArc(skia.Rect.MakeXYWH(p[0] - rc, p[1] - rc * 0.8, rc * 2, rc * 1.6), rng.uniform(0, 360), rng.uniform(110, 190))
            cv.drawPath(arc, stroke(sh, rng.uniform(0.006, 0.01), alpha=0.45))
            if k % 3 == 0:
                hp = skia.Path()
                hp.addArc(skia.Rect.MakeXYWH(p[0] - rc * 0.9, p[1] - rc, rc * 1.8, rc * 1.5), rng.uniform(190, 230), rng.uniform(60, 100))
                cv.drawPath(hp, stroke(hl, 0.007, alpha=0.35))
        cv.restore()

    def back(self, cv, H, st, P):
        """Solid hair mass behind the head, so no background shows between the curls and the face."""
        top, R, L, hl_r, hl_l = self.geometry(H, P)
        r = self.curl_r * 0.8
        pts = [top] + [(x - r, y) for x, y in R[1:]] + [(x + r, y) for x, y in L[1:]][::-1]
        cv.drawPath(spline(pts, closed=True, tension=0.5), fill(st["hair"]))

    def cast_shadow(self, cv, H, st, P):
        g = self.geometry(H, P)
        path = self.path(g)
        m = skia.Matrix()
        m.setTranslate(-P["light_x"] * 0.03, 0.07)
        path.transform(m)
        cv.drawPath(path, fill(st["skin_sh"], alpha=0.7, blur=0.025))


class CurlyBeard(Beard):
    """Full curly beard (Peter): close and dense on the cheeks, fuller at the chin, with coarse
    hairs growing downward - a different texture from the curls on his head."""

    def __call__(self, cv, H, st, P):
        R, L, bot, IR, IL = self.geometry(H, P)
        col, sh = st[self.col], st[self.col_sh]
        lc = st.get("hair_line", "#120c08")
        edge = R[1:] + [bot] + L[::-1][:-1]
        ring = R + [bot] + L[::-1] + IL + IR[::-1][1:]
        n_out = len(R) + 1 + len(L)
        path = spline(ring, closed=True, corners=[0, n_out - 1, n_out], tension=0.5)
        face_c = H.pt(0.0, 0.2)
        curly = wavy_edge(edge, 21, 0.05, face_c)
        inner = IL + IR[::-1][1:]
        mass = spline([R[0]] + curly + [L[0]] + inner, closed=True, tension=0.45)
        cv.drawPath(mass, stroke(lc, 0.024, alpha=0.85))
        cv.drawPath(mass, fill(col, alpha=0.5, blur=0.03))
        cv.drawPath(mass, fill(col))
        cv.save()
        cv.clipPath(mass, skia.ClipOp.kIntersect, True)
        lx = P["light_x"]
        sx = 1.0 if lx < 0 else -1.0
        cv.drawPath(spline([(sx * 0.1, 0.2), (sx * 1.6, 0.0), (sx * 1.6, 2.0), (sx * 0.2, 1.8)], closed=True), fill(sh, alpha=0.5, blur=0.05))
        rng = np.random.default_rng(11)
        # coarse hairs growing down and slightly out along the jaw
        for k in range(70):
            u = rng.uniform(-0.98, 0.98)
            v = rng.uniform(0.25, 1.4)
            p = surf_pts(H, [(u, v)], dz=0.08)[0]
            ln = rng.uniform(0.035, 0.06)
            ang = math.radians(rng.uniform(-25, 25) + 12 * u)
            q = (p[0] + math.sin(ang) * ln, p[1] + math.cos(ang) * ln)
            mid = ((p[0] + q[0]) / 2 + 0.008 * math.cos(ang), (p[1] + q[1]) / 2)
            cv.drawPath(tapered([p, mid, q], 0.008, 0.002), fill(sh if k % 3 else mix(col, "#ffffff", 0.18), alpha=0.75))
        # soft clumps where the beard is fullest, at the chin and along the jaw
        for k in range(10):
            u = rng.uniform(-0.8, 0.8)
            v = rng.uniform(0.7, 1.4)
            p = surf_pts(H, [(u, v)], dz=0.1)[0]
            rr = rng.uniform(0.06, 0.1)
            cv.drawPath(ellipse(p[0], p[1], rr, rr * 0.7), fill(sh if k % 2 else mix(col, "#ffffff", 0.12), alpha=0.25, blur=rr * 0.5))
        cv.restore()


class HeadCloth:
    """A cloth draped over the head and shoulders (prayer shawl / headscarf)."""

    def __init__(self, layer="front", col="cloth", col_sh="cloth_sh", vol=0.20, edge=None,
                 y_hang=0.35, drape_y=2.2, flare=0.55, stripes=None, hair_fringe=False):
        self.layer = layer
        self.col = col
        self.col_sh = col_sh
        self.vol_ = vol
        self.y_hang = y_hang
        self.drape_y = drape_y
        self.flare = flare
        self.stripes = stripes
        self.hair_fringe = hair_fringe
        self.edge = edge or [(0.0, -0.88), (0.36, -0.85), (0.66, -0.74), (0.88, -0.52), (0.98, -0.22),
                             (1.01, 0.12), (0.98, 0.44)]

    def vol(self, y):
        # the cloth lies close over the crown and stands off the head more where it falls past the ears
        crown = 0.5 + 0.5 * min(1.0, max(0.0, (y + 1.6) / 1.2))
        return self.vol_ * crown + 0.06 * min(1.0, max(0.0, (y + 0.6) / 1.0))

    def __call__(self, cv, H, st, P):
        if self.layer == "back":
            self.draw_back(cv, H, st, P)
        else:
            self.draw_front(cv, H, st, P)

    def geometry(self, H, P):
        ys = list(np.linspace(-1.66, self.y_hang, 14))
        R, L = extents(H, ys, self.vol)
        top = top_point(H, self.vol_ * 0.5)
        er = surf_pts(H, self.edge, dz=0.05)
        el = surf_pts(H, [(-x, y) for x, y in self.edge], dz=0.05)
        er = clamp_inner(er, H, 1, far_margin(H, 1, 0.05))
        el = clamp_inner(el, H, -1, far_margin(H, -1, 0.05))
        er = [(min(x, interp_x(R, y) - 0.08), y) for x, y in er]
        el = [(max(x, interp_x(L, y) + 0.08), y) for x, y in el]
        # drape below y_hang: falls onto the shoulders, flaring outward
        def drape(side, outer_anchor, inner_anchor):
            s = side
            ox, oy = outer_anchor
            ix, iy = inner_anchor
            out = []
            for y in np.linspace(oy + 0.3, self.drape_y, 4):
                u = (y - oy) / (self.drape_y - oy)
                dx, dy = sway_offset(P, y, k=0.12)
                out.append((ox + s * self.flare * u ** 1.3 + dx, y + dy))
            dx, dy = sway_offset(P, self.drape_y + 0.1, k=0.12)
            bottom = [(ox + s * self.flare + dx, self.drape_y + 0.12 + dy), (ix + s * 0.05 + dx, self.drape_y + 0.02 + dy)]
            inn = []
            for y in np.linspace(self.drape_y - 0.2, iy + 0.2, 4):
                u = (y - iy) / (self.drape_y - iy)
                dx, dy = sway_offset(P, y, k=0.12)
                inn.append((ix + s * 0.08 * u + dx, y + dy))
            return out, bottom, inn
        r_out, r_bot, r_in = drape(1, R[-1], er[-1])
        l_out, l_bot, l_in = drape(-1, L[-1], el[-1])
        r_in = clamp_inner(r_in, H, 1, far_margin(H, 1, 0.0) - 0.02, y_from=0.0)
        l_in = clamp_inner(l_in, H, -1, far_margin(H, -1, 0.0) - 0.02, y_from=0.0)
        return dict(top=top, R=R, L=L, er=er, el=el, r=(r_out, r_bot, r_in), l=(l_out, l_bot, l_in))

    def front_path(self, g):
        top, R, L = g["top"], g["R"], g["L"]
        r_out, r_bot, r_in = g["r"]
        l_out, l_bot, l_in = g["l"]
        seq = [top] + R[1:] + r_out
        c1 = len(seq)
        seq += r_bot
        corners = [c1, c1 + 1]
        seq += r_in + g["er"][::-1]
        seq += g["el"][1:] + l_in[::-1]
        c2 = len(seq)
        seq += l_bot[::-1]
        corners += [c2, c2 + 1]
        seq += l_out[::-1] + L[::-1][1:-1]
        return spline(seq, closed=True, corners=corners, tension=0.5)

    def edge_path(self, g):
        r_out, r_bot, r_in = g["r"]
        l_out, l_bot, l_in = g["l"]
        seq = r_in[::-1] + g["er"][::-1] + g["el"][1:] + l_in
        return spline(seq, closed=False)

    def draw_front(self, cv, H, st, P):
        g = self.geometry(H, P)
        path = self.front_path(g)
        col, sh = st[self.col], st[self.col_sh]
        lc = st.get("line", "#2a1a14")
        if self.hair_fringe:
            self.draw_fringe(cv, H, st, P, g)
        cv.drawPath(path, fill(col))
        cv.save()
        cv.clipPath(path, skia.ClipOp.kIntersect, True)
        lx = P["light_x"]
        sx = 1.0 if lx < 0 else -1.0
        shade = spline([(sx * 0.2, -2.4), (sx * 2.6, -2.4), (sx * 2.6, 3.0), (sx * 1.0, 3.0), (sx * 0.9, 0.2), (sx * 0.6, -1.2)], closed=True)
        # soft, rounded shading: the cloth turns away from the light, it is not split into two colours
        cv.drawPath(shade, fill(sh, alpha=0.45, blur=0.16))
        cv.drawPath(ellipse(-sx * 0.25, -1.25, 0.55, 0.32), fill(mix(col, "#ffffff", 0.4), alpha=0.28, blur=0.12))
        if self.stripes:
            ep = self.edge_path(g)
            for (d0, d1, scol) in self.stripes:
                cv.drawPath(ep, stroke(scol, 2 * d1, cap="butt"))
                cv.drawPath(ep, stroke(col, 2 * d0, cap="butt"))
            cv.drawPath(shade, fill(sh, alpha=0.3, blur=0.16))
        # folds: soft creases where the cloth gathers over the crown and falls past the ears
        hi = mix(col, "#ffffff", 0.35)
        for s in (1, -1):
            out, bot, inn = g["r"] if s > 0 else g["l"]
            side = g["R"] if s > 0 else g["L"]
            for k in range(3):
                a = side[5 + k * 2]
                b = out[min(len(out) - 1, 1 + k)]
                a2 = (a[0] - s * 0.15, a[1])
                pts = [a2, ((a2[0] + b[0]) / 2 - s * 0.05, (a2[1] + b[1]) / 2), (b[0] - s * 0.12, b[1])]
                cv.drawPath(tapered(sample_spline(pts, n=14), 0.004, 0.01, wmid=0.04), fill(sh, alpha=0.5, blur=0.012))
                cv.drawPath(tapered(sample_spline([(x + s * 0.05, y) for x, y in pts], n=14), 0.003, 0.006, wmid=0.025), fill(hi, alpha=0.3, blur=0.01))
            for k in range(2):
                c0 = surf_pts(H, [(s * (0.15 + 0.2 * k), -1.62 + 0.05 * k)], dz=self.vol_ * 0.5 + 0.02)[0]
                c1 = surf_pts(H, [(s * (0.42 + 0.22 * k), -1.2 + 0.1 * k)], dz=self.vol_ * 0.8)[0]
                c2 = surf_pts(H, [(s * (0.7 + 0.18 * k), -0.75 + 0.12 * k)], dz=self.vol_)[0]
                cv.drawPath(tapered(sample_spline([c0, c1, c2], n=14), 0.002, 0.004, wmid=0.022), fill(sh, alpha=0.32, blur=0.01))
        # the folded hem round the face: a band of shade with a light edge, so the cloth has thickness
        ep = self.edge_path(g)
        cv.drawPath(ep, stroke(sh, 0.12, alpha=0.45, blur=0.03))
        cv.drawPath(ep, stroke(hi, 0.02, alpha=0.5))
        cv.restore()
        cv.drawPath(path, stroke(lc, 0.02))

    def draw_fringe(self, cv, H, st, P, g):
        # a little hair visible under the scarf: center part sweeping to the temples
        er, el = g["er"], g["el"]
        hl = [(0.0, -0.99), (0.20, -0.94), (0.44, -0.84), (0.66, -0.65), (0.82, -0.39), (0.90, -0.12)]
        pr = surf_pts(H, hl, dz=0.03)
        pl = surf_pts(H, [(-x, y) for x, y in hl], dz=0.03)
        pr = clamp_inner(pr, H, 1, far_margin(H, 1, 0.05))
        pl = clamp_inner(pl, H, -1, far_margin(H, -1, 0.05))
        seq = er[:6] + pr[::-1] + pl[1:] + el[:6][::-1][:-1]
        path = spline(seq, closed=True)
        cv.drawPath(path, fill(st["hair"]))
        cv.save()
        cv.clipPath(path, skia.ClipOp.kIntersect, True)
        for s in (1, -1):
            for k in range(3):
                a = surf_pts(H, [(s * 0.02, -0.98)], dz=0.04)[0]
                b = surf_pts(H, [(s * (0.35 + 0.18 * k), -0.84 + 0.06 * k)], dz=0.04)[0]
                c = surf_pts(H, [(s * (0.62 + 0.12 * k), -0.5 + 0.1 * k)], dz=0.04)[0]
                cv.drawPath(tapered(sample_spline([a, b, c], n=12), 0.002, 0.002, wmid=0.016), fill(st["hair_sh"], alpha=0.8))
            a = surf_pts(H, [(s * 0.25, -0.9)], dz=0.05)[0]
            cv.drawPath(tapered([a, (a[0] + s * 0.12, a[1] + 0.03), (a[0] + s * 0.2, a[1] + 0.1)], 0.004, 0.0, wmid=0.02), fill(st["hair_hl"], alpha=0.6))
        cv.restore()
        cv.drawPath(spline(pr[::-1] + pl[1:], closed=False), stroke(st.get("hair_line", "#1e1009"), 0.014))

    def cast_shadow(self, cv, H, st, P):
        g = self.geometry(H, P)
        path = self.front_path(g)
        m = skia.Matrix()
        m.setTranslate(-P["light_x"] * 0.04, 0.08)
        path.transform(m)
        cv.drawPath(path, fill(st["skin_sh"], alpha=0.85))

    def draw_back(self, cv, H, st, P):
        ys = list(np.linspace(-1.66, self.y_hang, 12))
        R, L = extents(H, ys, lambda y: self.vol(y) + 0.04)
        top = top_point(H, self.vol_ + 0.04)
        rb, lb = [], []
        for y in np.linspace(self.y_hang + 0.4, self.drape_y + 0.4, 4):
            u = (y - self.y_hang) / (self.drape_y + 0.4 - self.y_hang)
            dx, dy = sway_offset(P, y, k=0.1)
            rb.append((R[-1][0] + (self.flare + 0.25) * u + dx, y + dy))
            lb.append((L[-1][0] - (self.flare + 0.25) * u + dx, y + dy))
        pts = [top] + R[1:] + rb + lb[::-1] + L[::-1][1:-1]
        path = spline(pts, closed=True, corners=[len(R) + len(rb) - 1, len(R) + len(rb)])
        cv.drawPath(path, fill(st[self.col_sh]))
        cv.drawPath(path, stroke(st.get("line", "#2a1a14"), 0.02))


def wrinkles(cv, H, st, P, layer):
    """Age lines for an older face (forehead, crow's feet, nasolabial folds, eye bags)."""
    if layer != "lines":
        return
    lc = st.get("crease_col", "#8a5b48")
    br = (P["br_l"] + P["br_r"]) * 0.5
    a = 0.45 + 0.35 * max(0.0, br)
    de = st.get("eye_y", 0.04) - 0.04      # features sit lower on the more lifelike face
    dm = st.get("mouth_y", 0.68) - 0.68
    for k in range(3):
        y = -0.62 - 0.11 * k + de * 1.1
        pts = surf_pts(H, [(-0.42 + 0.05 * k, y + 0.02), (0.0, y - 0.025 * br), (0.42 - 0.05 * k, y + 0.02)], dz=0.0)
        cv.drawPath(tapered(sample_spline(pts, n=12), 0.002, 0.002, wmid=0.012), fill(lc, alpha=a * (0.8 - 0.2 * k)))
    for s in (-1, 1):
        ex = 0.43 * s
        for k in range(2):
            p = surf_pts(H, [(ex + s * 0.27, -0.01 + 0.05 * k + de), (ex + s * 0.34, -0.03 + 0.08 * k + de)], dz=0.0)
            cv.drawPath(tapered(p, 0.008, 0.0), fill(lc, alpha=0.55))
        bag = surf_pts(H, [(ex - s * 0.12, 0.13 + de), (ex, 0.165 + de), (ex + s * 0.14, 0.13 + de)], dz=0.0)
        cv.drawPath(tapered(sample_spline(bag, n=10), 0.002, 0.002, wmid=0.01), fill(lc, alpha=0.5))
        nl = surf_pts(H, [(s * 0.17, 0.44 + de), (s * 0.28, 0.56 + dm), (s * 0.31, 0.70 + dm)], dz=0.0)
        cv.drawPath(tapered(sample_spline(nl, n=10), 0.012, 0.002), fill(lc, alpha=0.55 + 0.3 * max(0, P["m_smile"])))
