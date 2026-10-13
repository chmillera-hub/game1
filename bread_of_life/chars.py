"""Character designs: Jesus, Peter, Miriam, Eli (+ crowd extras)."""
import math

import numpy as np
import skia

import hair
from body import make_arms
from gfx import ellipse, fill, lin_grad, mix, rad_grad, sample_spline, spline, stroke, tapered
from rig import HEM_CORNERS, Character, body_pts


def _fold(cv, pts, dark, light, w=0.05, alpha=0.7):
    """Cel-shaded cloth fold: a dark crease with a soft highlight beside it."""
    sm = sample_spline(pts, n=16)
    cv.drawPath(tapered(sm, 0.004, 0.004, wmid=w), fill(dark, alpha=alpha))
    hl = [(x + 0.05, y + 0.01) for x, y in sm]
    cv.drawPath(tapered(hl, 0.003, 0.003, wmid=w * 0.6), fill(light, alpha=alpha * 0.35))


def _cut_neckline(robe, nk):
    """The robe with its neckline opening removed (one clean contour running up from the
    neckline curve). PathOps can reject near-degenerate input, so retry with a tiny nudge and
    fall back to the uncut robe rather than fail a frame."""
    for eps in (0.0, 1e-3, -1.7e-3, 3.1e-3):
        pts = [(nk[0][0] - eps, -3.0)] + [(x, y + eps) for x, y in nk] + [(nk[-1][0] + eps, -3.0)]
        opening = spline(pts, closed=True, corners=[0, 1, len(pts) - 2, len(pts) - 1])
        try:
            return skia.Op(robe, opening, skia.PathOp.kDifference_PathOp)
        except RuntimeError:
            continue
    return robe


def tunic_outfit(base, base_sh, trim=None, neckline="v", mantle=None, belt=None, scarf=None, sash=None, clavi=None):
    """Full-length tunic (shoulders to hem) with folds, belt and optional mantle."""

    def outfit(cv, st, P, H, ho):
        pts = body_pts(st, P)
        by = P["byaw"] / 60.0
        k = st.get("body_scale", 1.0)
        hem = st.get("hem_y", 13.0) * k
        lc = st.get("line", "#2a1a14")
        # the neckline is an opening in the robe: the throat and chest show through it, and the
        # robe's outline follows the neckline instead of running across the neck
        ncx = by * 0.55 + ho[0] * 0.3
        # the collar sits round the base of the neck, a little wider than it, never cutting into it
        hw = max(0.5, st.get("neck_w", 0.4) * 1.12 + 0.16)
        if neckline == "v":
            nk = [(ncx - hw, -0.12), (ncx - hw * 0.55, 0.3), (ncx, 0.66 + 0.04 * P["breath"]), (ncx + hw * 0.55, 0.3), (ncx + hw, -0.12)]
        else:
            nk = [(ncx - hw, -0.12), (ncx - hw * 0.8, 0.3), (ncx, 0.48), (ncx + hw * 0.8, 0.3), (ncx + hw, -0.12)]
        npath = spline(nk, closed=True, corners=[0, 4])
        robe = spline(pts, closed=True, corners=HEM_CORNERS, tension=0.45)
        body = _cut_neckline(robe, nk)
        hi = mix(base, "#ffffff", 0.35)
        cv.drawPath(body, fill(base, shader=lin_grad((0, -0.2), (0, hem), [mix(base, "#ffffff", 0.12), base, mix(base, base_sh, 0.45)], [0.0, 0.35, 1.0])))
        cv.drawPath(body, stroke(lc, 0.024))
        cv.save()
        cv.clipPath(body, skia.ClipOp.kIntersect, True)
        lx = P["light_x"]
        sx = 1.0 if lx < 0 else -1.0
        sw = st.get("shoulder_w", 2.1)
        cv.drawPath(spline([(sx * sw * 1.4, -0.5), (sx * sw * 0.55, 0.2), (sx * sw * 0.42, 2.0), (sx * sw * 0.5, hem + 1), (sx * sw * 1.4, hem + 1)], closed=True),
                    fill(base_sh, alpha=0.62, blur=0.22))
        if clavi:
            for s_ in (-1, 1):
                x = s_ * sw * 0.40 + by * 0.4
                cv.drawPath(spline([(x - 0.08, -0.2), (x + 0.08, -0.2), (x + 0.14, hem + 0.5), (x - 0.04, hem + 0.5)], closed=True, corners=[0, 1, 2, 3]), fill(clavi, alpha=0.85))
        # the chest is full and lifted: light across it, a soft shadow beneath it
        cv.drawPath(ellipse(by * 0.5 - sx * sw * 0.08, 1.05, sw * 0.62, 0.75), fill(mix(base, "#ffffff", 0.3), alpha=0.32, blur=0.35))
        cv.drawPath(ellipse(by * 0.5, 2.25, sw * 0.7, 0.32), fill(base_sh, alpha=0.28, blur=0.3))
        # drape folds, falling from below the chest
        folds = [[(-1.05, 0.9), (-0.92, 1.8), (-1.0, 2.9)], [(1.05, 0.95), (0.95, 1.9), (1.05, 3.0)],
                 [(-0.5, 2.0), (-0.45, 2.8), (-0.6, 3.6)], [(0.55, 2.1), (0.5, 2.9), (0.7, 3.8)],
                 [(-0.15, 2.4), (0.0, 3.1), (-0.1, 4.0)]]
        for f in folds:
            _fold(cv, [(x * sw / 1.8 + by * 0.5, y) for x, y in f], base_sh, hi, w=0.05, alpha=0.6)
        # skirt folds from the belt to the hem
        rng = np.random.default_rng(int(sum(map(ord, base))))
        for j in range(7):
            u = -0.78 + j * 0.26 + rng.uniform(-0.05, 0.05)
            x0 = u * sw * 0.78 + by * 0.4
            x1 = u * sw * 0.92 + by * 0.4 + 0.05 * math.sin(P["t"] * 0.8 + j)
            _fold(cv, [(x0, 4.9 * k), (x0 * 0.98 + (x1 - x0) * 0.5, (4.9 * k + hem) / 2), (x1, hem - 0.15)], base_sh, hi, w=0.08, alpha=0.55)
        # hem band
        cv.drawPath(spline([(-sw * 1.2, hem - 0.25), (0, hem - 0.18), (sw * 1.2, hem - 0.25)], closed=False), stroke(trim or base_sh, 0.12, alpha=0.6))
        if sash:
            sc, ssh2 = sash
            sp = [(-1.38 * sw / 2.05 + by * 0.3, -0.6), (-0.98 * sw / 2.05 + by * 0.3, -0.62), (1.6 * sw / 2.05 + by * 0.3, 3.9), (1.2 * sw / 2.05 + by * 0.3, 4.2)]
            band = spline(sp, closed=True, corners=[0, 1, 2, 3])
            cv.drawPath(band, fill(sc))
            cv.drawPath(band, stroke(lc, 0.02))
        cv.restore()
        # chest seen through the neckline: collarbones and the notch between them
        cv.save()
        cv.clipPath(npath, skia.ClipOp.kIntersect, True)
        sh2 = st.get("skin_sh2", st["skin_sh"])
        for s_ in (-1, 1):
            cv.drawPath(tapered(sample_spline([(ncx + s_ * hw * 0.85, 0.06), (ncx + s_ * 0.24, 0.14), (ncx + s_ * 0.07, 0.2)], n=10), 0.004, 0.006, wmid=0.016),
                        fill(sh2, alpha=0.4))
        cv.drawPath(ellipse(ncx, 0.25, 0.05, 0.035), fill(sh2, alpha=0.25, blur=0.02))
        cv.restore()
        cv.drawPath(body, stroke(lc, 0.024))  # keep the robe's outline crisp over anything drawn on it
        # collar band along the neckline
        cv.drawPath(spline(nk, closed=False), stroke(trim or base_sh, 0.07, alpha=0.75))
        cv.drawPath(spline(nk, closed=False), stroke(lc, 0.02, alpha=0.95))
        if belt:
            bc, bsh = belt
            yb = 4.45 * k
            band = spline([(-sw, yb - 0.22), (0, yb - 0.12), (sw, yb - 0.22), (sw, yb + 0.2), (0, yb + 0.3), (-sw, yb + 0.2)], closed=True, corners=[0, 2, 3, 5])
            cv.save()
            cv.clipPath(body, skia.ClipOp.kIntersect, True)
            cv.drawPath(band, fill(bc))
            cv.drawPath(spline([(-sw, yb + 0.1), (0, yb + 0.2), (sw, yb + 0.1)], closed=False), stroke(bsh, 0.06, alpha=0.8))
            cv.restore()
            kx = sw * 0.25 + by * 0.4
            knot = ellipse(kx, yb + 0.05, 0.22, 0.2)
            cv.drawPath(knot, fill(bc))
            cv.drawPath(knot, stroke(lc, 0.02))
            for dx in (-0.08, 0.1):
                end = tapered([(kx + dx, yb + 0.15), (kx + dx * 1.6, yb + 1.0), (kx + dx * 1.2 + 0.05 * math.sin(P["t"] * 1.3), yb + 1.9)], 0.16, 0.12)
                cv.drawPath(end, fill(bc))
                cv.drawPath(end, stroke(lc, 0.018))
        if mantle:
            mantle(cv, st, P, H, ho, pts)
        if scarf:
            scarf(cv, st, P, H, ho, pts)

    def collar(cv, st, P, H, ho):
        """Drawn after the arms: the cloth that lies over a shoulder, on top of the sleeve (the
        sash over Peter's shoulder, the fold of a mantle over its shoulder)."""
        if not sash:
            return
        pts = body_pts(st, P)
        by = P["byaw"] / 60.0
        sw = st.get("shoulder_w", 2.1)
        lc = st.get("line", "#2a1a14")
        sc, ssh2 = sash
        sp = [(-1.38 * sw / 2.05 + by * 0.3, -0.6), (-0.98 * sw / 2.05 + by * 0.3, -0.62), (1.6 * sw / 2.05 + by * 0.3, 3.9), (1.2 * sw / 2.05 + by * 0.3, 4.2)]
        band = spline(sp, closed=True, corners=[0, 1, 2, 3])
        robe = spline(pts, closed=True, corners=HEM_CORNERS, tension=0.45)
        cv.save()
        cv.clipPath(robe, skia.ClipOp.kIntersect, True)
        cv.clipRect(skia.Rect.MakeLTRB(-sw * 1.3, -1.0, -sw * 0.25 + by * 0.3, 0.75), skia.ClipOp.kIntersect, True)
        cv.drawPath(band, fill(sc))
        cv.drawPath(spline([sp[0], sp[3]], closed=False), stroke(ssh2, 0.06, alpha=0.6))
        cv.drawPath(band, stroke(lc, 0.02))
        cv.restore()

    outfit.collar = collar
    if mantle is not None and hasattr(mantle, "over"):
        outfit.drape_side = mantle.side
        outfit.drape = mantle.over
    return outfit


def mantle_painter(col, col_sh, side=1, lining=None):
    """A himation wrapped round the body: over one shoulder (side=+1 screen-right), across the
    chest and hanging to the knees. The arm on that side keeps its tunic sleeve; the cloth over
    the shoulder (paint.over, drawn after the arms) lies over the top of that arm and moves with it."""

    def over(cv, st, P, H, ho):
        import body as _body
        s = side
        sw = st.get("shoulder_w", 2.1)
        k = st.get("body_scale", 1.0)
        up = -0.05 * P["breath"] - 0.12 * P["shrug"]
        lc = st.get("line", "#2a1a14")
        by = P["byaw"] / 60.0
        ncx = by * 0.55
        spec = P.get("arm_r" if s > 0 else "arm_l")
        S, E, W = _body.arm_geometry(st, P, s, spec)
        s2, e2 = np.array(S[:2]), np.array(E[:2])
        L = float(np.linalg.norm(e2 - s2)) + 1e-9
        u = (e2 - s2) / L
        n = np.array([-u[1], u[0]])
        if n[0] * s < 0:
            n = -n  # n points away from the body
        hw = st.get("sleeve_w", (0.95, 0.9, 1.05))[0] * k * 0.5
        reach = 0.42 * L
        drape = [
            (ncx + s * 0.38, -0.12 + up * 0.3),
            (s * sw * 0.68, 0.0 + up),
            tuple(s2 + n * (hw + 0.05) - u * 0.12),
            tuple(s2 + n * (hw + 0.05) + u * reach * 0.6),
            tuple(s2 + n * (hw + 0.03) + u * reach),
            tuple(s2 + u * (reach + 0.12)),
            tuple(s2 - n * (hw + 0.02) + u * reach * 0.85),
            (s * sw * 0.52 + by * 0.4, 1.05),
            (ncx + s * 0.22, 0.75),
        ]
        path = spline(drape, closed=True, corners=[4, 6], tension=0.45)
        body_path = spline(outline(st, P), closed=True, corners=[6, 8], tension=0.45)
        hi = mix(col, "#ffffff", 0.3)
        # the same cloth as the mantle, continuing over the top of the arm (drawn with the mantle's
        # own gradient, so where it lies over the mantle no edge shows)
        cloth = fill(col, shader=lin_grad((0, -0.2), (0, 10.6 * k), [mix(col, "#ffffff", 0.14), col, mix(col, col_sh, 0.5)], [0.0, 0.35, 1.0]))
        cv.drawPath(path, cloth)
        cv.save()
        cv.clipPath(path, skia.ClipOp.kIntersect, True)
        lx = P["light_x"]
        sx = 1.0 if lx < 0 else -1.0
        knee = 10.6 * k
        cv.drawPath(spline([(sx * sw * 1.6, -0.5), (sx * sw * 0.65, 0.3), (sx * sw * 0.5, 2.0), (sx * sw * 0.55, knee + 1), (sx * sw * 1.6, knee + 1)], closed=True),
                    fill(col_sh, alpha=0.45, blur=0.2))
        # folds hanging from the shoulder: they run over the top of the arm and on down into the mantle
        for j in range(4):
            f = 0.2 + 0.2 * j
            a_ = s2 - n * (hw * 0.4) + u * reach * f
            b_ = s2 + u * reach * (f + 0.1) + n * 0.05
            c_ = s2 + n * (hw + 0.05) + u * reach * (f + 0.05)
            _fold(cv, [tuple(a_), tuple(b_), tuple(c_)], col_sh, hi, w=0.04, alpha=0.4)
        for j in range(3):
            y0 = 0.25 + 0.18 * j
            _fold(cv, [(s * sw * 0.52, y0), (s * sw * 0.78, y0 + 0.12), (s * sw * 1.0, y0 + 0.35)], col_sh, hi, w=0.045, alpha=0.6)
        cv.drawPath(tapered(sample_spline([(ncx + s * 0.38, -0.12 + up * 0.3), (s * sw * 0.58, 0.1 + up), (s * sw * 0.92, 0.45 + up)], n=10), 0.01, 0.01, wmid=0.09),
                    fill("#ffffff", alpha=0.16))
        cv.restore()
        # a soft shadow where the fold's end hangs over the sleeve
        end = [tuple(s2 + n * (hw + 0.03) + u * reach), tuple(s2 + u * (reach + 0.12)), tuple(s2 - n * (hw + 0.02) + u * reach * 0.85)]
        cv.save()
        cv.clipPath(body_path, skia.ClipOp.kDifference, True)
        cv.drawPath(tapered(sample_spline([(x + u[0] * 0.06, y + u[1] * 0.06) for x, y in end], n=10), 0.03, 0.03, wmid=0.08), fill("#000000", alpha=0.18, blur=0.04))
        # the fold's outline, only where it lies over the sleeve or the background
        cv.drawPath(path, stroke(lc, 0.024))
        cv.restore()

    def outline(st, P):
        by = P["byaw"] / 60.0
        s = side
        sw = st.get("shoulder_w", 2.1)
        k = st.get("body_scale", 1.0)
        up = -0.05 * P["breath"] - 0.12 * P["shrug"]
        ncx = by * 0.55
        knee = 10.6 * k
        sway = 0.06 * math.sin(P["t"] * 0.8 + 1)
        return [
            (ncx + s * 0.38, -0.12 + up * 0.3),
            (s * sw * 0.72, 0.05 + up),
            (s * sw * 1.0, 0.42 + up),
            (s * sw * 1.1, 1.3),
            (s * sw * 1.02, 4.4 * k),
            (s * sw * 1.02, 7.5 * k),
            (s * sw * 1.0 + sway, knee),
            (s * sw * 0.2 + sway, knee + 0.35),
            (-s * sw * 0.78 + sway, knee - 0.6),
            (-s * sw * 0.82, 7.0 * k),
            (-s * sw * 0.78 + by * 0.4, 4.6 * k),
            (-s * sw * 0.35 + by * 0.4, 3.2 * k),
            (ncx - s * 0.05, 1.95),
            (ncx + s * 0.22, 0.75),
        ]

    def paint(cv, st, P, H, ho, pts):
        by = P["byaw"] / 60.0
        s = side
        sw = st.get("shoulder_w", 2.1)
        k = st.get("body_scale", 1.0)
        up = -0.05 * P["breath"] - 0.12 * P["shrug"]
        lc = st.get("line", "#2a1a14")
        ncx = by * 0.55
        knee = 10.6 * k
        outer = outline(st, P)
        path = spline(outer, closed=True, corners=[6, 8], tension=0.45)
        hi = mix(col, "#ffffff", 0.3)
        cv.drawPath(path, fill(col, shader=lin_grad((0, -0.2), (0, knee), [mix(col, "#ffffff", 0.14), col, mix(col, col_sh, 0.5)], [0.0, 0.35, 1.0])))
        cv.save()
        cv.clipPath(path, skia.ClipOp.kIntersect, True)
        # long folds following the drape
        for j in range(7):
            t = 0.08 + j * 0.13
            a = (ncx + s * (0.25 + t * 0.75), 0.35 + t * 0.7)
            b = (-s * sw * 0.25 + s * t * sw * 0.9, 3.2 + t * 1.6)
            c = (-s * sw * 0.6 + s * t * sw * 1.55, knee - 0.3)
            _fold(cv, [a, b, c], col_sh, hi, w=0.08, alpha=0.75)
        for j in range(3):
            y0 = 0.25 + 0.18 * j
            _fold(cv, [(s * sw * 0.52, y0), (s * sw * 0.78, y0 + 0.12), (s * sw * 1.0, y0 + 0.35)], col_sh, hi, w=0.045, alpha=0.6)
        lx = P["light_x"]
        sx = 1.0 if lx < 0 else -1.0
        cv.drawPath(spline([(sx * sw * 1.6, -0.5), (sx * sw * 0.65, 0.3), (sx * sw * 0.5, 2.0), (sx * sw * 0.55, knee + 1), (sx * sw * 1.6, knee + 1)], closed=True),
                    fill(col_sh, alpha=0.45, blur=0.2))
        edge = [outer[13], outer[12], outer[11], outer[10], outer[9], outer[8]]
        cv.drawPath(tapered(sample_spline([(x + s * 0.14, y) for x, y in edge], n=20), 0.12, 0.16, wmid=0.16), fill(col_sh, alpha=0.6, blur=0.03))
        cv.drawPath(tapered(sample_spline([outer[0], (s * sw * 0.58, 0.1 + up), (s * sw * 0.92, 0.45 + up)], n=10), 0.01, 0.01, wmid=0.09), fill("#ffffff", alpha=0.16))
        cv.restore()
        if lining:
            cv.drawPath(tapered(sample_spline(edge, n=20), 0.05, 0.07, wmid=0.065), fill(lining))
            cv.drawPath(tapered(sample_spline([(x - s * 0.02, y) for x, y in edge], n=20), 0.012, 0.016, wmid=0.016), fill("#fff0c0", alpha=0.6))
            cv.drawPath(tapered(sample_spline([outer[6], outer[7], outer[8]], n=12), 0.06, 0.06), fill(lining))
        cv.drawPath(path, stroke(lc, 0.024))

    paint.over = over
    paint.side = side
    return paint


# ---------------------------------------------------------------------------
# Jesus
# ---------------------------------------------------------------------------
JESUS_ST = dict(
    skin="#bf9b7d", skin_sh="#a47958", skin_sh2="#885d41", blush_col="#b9705c", blush_base=0.07,
    line="#3a2016", lash="#26140d", brow_col="#3a2216", lower_col="#6c4632", crease_col="#94684f",
    iris=("#2a170a", "#80501f", "#e2b26a"), lid_shadow="#5a3020",
    hair="#432a1a", hair_sh="#28170d", hair_hl="#82593c", hair_line="#1e1009", hair_rim="#d39a63",
    beard="#4a2e1d", beard_sh="#2c180e",
    head_xscale=0.88, eye_x=0.49, eye_y=0.06, eye_w=0.248, eye_h=0.136, eye_low=0.09, eye_tilt=-0.006,
    iris_rx=0.113, iris_ry=0.122, sclera_shadow="#e3d6d0",
    lash_in=0.012, lash_out=0.03, lash_mid=0.026, wing=0.01,
    brow_x=0.49, brow_y=-0.21, brow_in=-0.25, brow_out=0.30, brow_arch=0.038,
    brow_w0=0.066, brow_wm=0.056, brow_w1=0.016,
    mouth_w=0.175, mouth_y=0.74, mouth_h=0.21, nose_y=0.43, nose_len=0.23, nose_w=0.058, jaw_drop=0.07,
    shoulder_w=2.1, neck_w=0.44, neck_len=1.82, neck_top=0.8, face_lw=0.02,
    hem_y=13.2, waist_w=0.80, hip_w=0.85, hem_w=0.95, upper_arm=3.15, forearm=2.8, hand_len=2.15,
    sleeve_w=(0.95, 0.9, 1.08), stance=0.72,
    rim_col="#ffe1b0",
    slices=[
        (-1.700, 0.020, 0.100, -0.12), (-1.620, 0.450, 0.500, -0.12), (-1.460, 0.740, 0.780, -0.13),
        (-1.200, 0.930, 0.950, -0.12), (-0.850, 1.000, 1.000, -0.10), (-0.450, 1.020, 1.010, -0.08),
        (0.000, 1.000, 0.970, -0.05), (0.314, 1.001, 0.936, -0.01), (0.560, 0.958, 0.856, 0.04),
        (0.762, 0.858, 0.738, 0.10), (0.930, 0.693, 0.603, 0.18), (1.064, 0.506, 0.458, 0.28),
        (1.165, 0.319, 0.322, 0.36), (1.232, 0.140, 0.200, 0.42), (1.260, 0.010, 0.100, 0.45),
    ],
)

JESUS = Character(
    "jesus", JESUS_ST,
    outfit=tunic_outfit("#efe5d3", "#c9b89c", neckline="v", trim="#d6c9ae", clavi="#9a5a44", belt=("#8a6a3e", "#5e4426"),
                        mantle=mantle_painter("#2f557c", "#1f3b5a", side=1)),
    beard=hair.Beard(),
    headwear_back=hair.LongHair(layer="back"),
    headwear_front=hair.LongHair(layer="front"),
    arms=make_arms({-1: dict(sleeve="#efe5d3", sleeve_sh="#c9b89c"), 1: dict(sleeve="#efe5d3", sleeve_sh="#c9b89c")}),
)


# ---------------------------------------------------------------------------
PETER_HAIR = hair.ShortCurly()

# Simon Peter: broad fisherman, short curly black hair, full beard
# ---------------------------------------------------------------------------
PETER_ST = dict(JESUS_ST)
PETER_ST.update(
    skin="#d39a6e", skin_sh="#b0744f", skin_sh2="#8e5a3d", blush_col="#d0705a", blush_base=0.10,
    line="#2c1910", lash="#1e110a", brow_col="#1d140f", lower_col="#6b4030", crease_col="#93604a",
    iris=("#1d1109", "#4d3016", "#9a6a3c"), lid_shadow="#4a2a1a",
    hair="#231a15", hair_sh="#120c08", hair_hl="#5a4636", hair_line="#0d0805",
    beard="#33271f", beard_sh="#1a120d",
    head_xscale=0.9, eye_x=0.5, eye_y=0.06, eye_w=0.24, eye_h=0.121, eye_low=0.083, eye_tilt=-0.012,
    iris_rx=0.106, iris_ry=0.115, lash_in=0.014, lash_out=0.03, lash_mid=0.028, wing=0.006,
    brow_x=0.5, brow_y=-0.2, brow_in=-0.27, brow_out=0.31, brow_arch=0.022,
    brow_w0=0.08, brow_wm=0.07, brow_w1=0.028,
    mouth_w=0.19, mouth_y=0.75, nose_y=0.44, nose_len=0.27, nose_w=0.085,
    shoulder_w=2.35, neck_w=0.52, neck_len=1.80, neck_top=0.8, hem_y=12.3, hand_len=2.3,
    upper_arm=3.2, forearm=2.85, stance=0.8,
    slices=[
        (-1.660, 0.020, 0.100, -0.12), (-1.580, 0.470, 0.500, -0.12), (-1.420, 0.780, 0.800, -0.13),
        (-1.150, 0.960, 0.960, -0.12), (-0.800, 1.020, 1.000, -0.10), (-0.400, 1.040, 1.010, -0.08),
        (0.000, 1.030, 0.980, -0.05), (0.314, 1.043, 0.946, -0.01), (0.582, 1.026, 0.877, 0.04),
        (0.806, 0.935, 0.770, 0.10), (0.986, 0.770, 0.624, 0.18), (1.120, 0.572, 0.478, 0.28),
        (1.210, 0.363, 0.343, 0.36), (1.266, 0.160, 0.220, 0.42), (1.288, 0.010, 0.100, 0.45),
    ],
)

def peter_outfit():
    return tunic_outfit("#8a6744", "#634529", neckline="round", sash=("#cdb98f", "#9d8a62"), belt=("#c9b48a", "#8f7d55"))

PETER = Character(
    "peter", PETER_ST, outfit=peter_outfit(),
    beard=hair.CurlyBeard(vol=0.06, chin=0.14, inner=[(1.0, 0.09), (0.97, 0.37), (0.88, 0.56), (0.69, 0.67), (0.44, 0.73), (0.27, 0.79), (0.13, 0.85), (0.0, 0.87)]),
    headwear_front=PETER_HAIR, headwear_back=PETER_HAIR.back, ears=True,
    arms=make_arms({-1: dict(sleeve="#8a6744", sleeve_sh="#634529"), 1: dict(sleeve="#8a6744", sleeve_sh="#634529")}),
)

# ---------------------------------------------------------------------------
# Miriam: young mother, headscarf, big expressive eyes
# ---------------------------------------------------------------------------
MIRIAM_ST = dict(JESUS_ST)
MIRIAM_ST.update(
    skin="#efbe98", skin_sh="#d0906c", skin_sh2="#ad6e50", blush_col="#ec7f74", blush_base=0.16,
    line="#3a1f16", lash="#1f0f0a", brow_col="#3b2218", lower_col="#6e3e30", crease_col="#b77a62",
    iris=("#2b160b", "#7c4a1e", "#e8b46e"), lid_shadow="#5a2c20",
    hair="#3a2216", hair_sh="#22130b", hair_hl="#7a5236", hair_line="#1a0c06",
    cloth="#b8654e", cloth_sh="#8a4334",
    head_xscale=0.9, eye_x=0.48, eye_y=0.07, eye_w=0.255, eye_h=0.158, eye_low=0.1, eye_tilt=0.004,
    iris_rx=0.12, iris_ry=0.136, lash_in=0.015, lash_out=0.042, lash_mid=0.034, wing=0.035,
    lash_flicks=[(0.82, 0.05), (0.95, 0.06)], lower_lash=True,
    brow_x=0.48, brow_y=-0.19, brow_in=-0.24, brow_out=0.29, brow_arch=0.048,
    brow_w0=0.038, brow_wm=0.033, brow_w1=0.009,
    mouth_w=0.15, mouth_y=0.73, mouth_h=0.17, nose_y=0.43, nose_len=0.19, nose_w=0.05,
    lip_col="#d06a6a", shoulder_w=1.8, neck_w=0.34, neck_len=1.70, neck_top=0.78,
    hem_y=16.0, waist_w=0.74, hip_w=0.9, hem_w=1.0, upper_arm=2.95, forearm=2.6, hand_len=1.85,
    sleeve_w=(0.8, 0.76, 0.92), stance=0.5, body_scale=0.95,
    slices=[
        (-1.620, 0.020, 0.100, -0.12), (-1.550, 0.440, 0.480, -0.12), (-1.400, 0.740, 0.770, -0.13),
        (-1.140, 0.930, 0.940, -0.12), (-0.800, 0.990, 0.990, -0.10), (-0.400, 1.000, 1.000, -0.08),
        (0.000, 0.980, 0.960, -0.05), (0.314, 0.970, 0.916, -0.01), (0.560, 0.905, 0.825, 0.05),
        (0.739, 0.781, 0.707, 0.12), (0.885, 0.605, 0.562, 0.20), (1.008, 0.407, 0.416, 0.29),
        (1.098, 0.231, 0.291, 0.37), (1.142, 0.090, 0.180, 0.42), (1.159, 0.010, 0.100, 0.44),
    ],
)

MIRIAM = Character(
    "miriam", MIRIAM_ST,
    outfit=tunic_outfit("#6f8197", "#4f6075", neckline="round", belt=("#d9c7a5", "#a8946e")),
    headwear_back=hair.HeadCloth(layer="back", vol=0.22, flare=0.7),
    headwear_front=hair.HeadCloth(layer="front", vol=0.22, flare=0.7, hair_fringe=True,
                                  edge=[(0.0, -0.98), (0.38, -0.94), (0.70, -0.8), (0.92, -0.54), (1.02, -0.21), (1.04, 0.14), (1.0, 0.44)]),
    arms=make_arms({-1: dict(sleeve="#6f8197", sleeve_sh="#4f6075"), 1: dict(sleeve="#6f8197", sleeve_sh="#4f6075")}),
)

# ---------------------------------------------------------------------------
# Eli: elder, grey beard, prayer shawl over the head
# ---------------------------------------------------------------------------
ELI_ST = dict(JESUS_ST)
ELI_ST.update(
    skin="#dca67d", skin_sh="#b97f5b", skin_sh2="#966041", blush_col="#d27a62", blush_base=0.10,
    line="#33201a", lash="#2a1a14", brow_col="#8e8880", lower_col="#7a4e3c", crease_col="#9a654e",
    iris=("#2a2420", "#5c5248", "#a39a8c"), lid_shadow="#5a3a2c",
    hair="#a19b92", hair_sh="#6e6961", hair_hl="#e2ded6", hair_line="#3a3632",
    beard="#a8a39b", beard_sh="#6d6861",
    cloth="#e8dfca", cloth_sh="#b9ad94",
    head_xscale=0.89, eye_x=0.48, eye_y=0.07, eye_w=0.23, eye_h=0.113, eye_low=0.08, eye_tilt=-0.016,
    iris_rx=0.099, iris_ry=0.108, lash_in=0.012, lash_out=0.026, lash_mid=0.024, wing=0.0,
    brow_x=0.48, brow_y=-0.2, brow_in=-0.25, brow_out=0.30, brow_arch=0.032,
    brow_w0=0.075, brow_wm=0.06, brow_w1=0.03, brow_out_up=-0.02,
    mouth_w=0.165, mouth_y=0.76, nose_y=0.45, nose_len=0.29, nose_w=0.078,
    shoulder_w=2.0, neck_w=0.42, neck_len=1.82, neck_top=0.8, hem_y=15.9, hand_len=2.1,
)

ELI = Character(
    "eli", ELI_ST,
    outfit=tunic_outfit("#5d6140", "#40442b", neckline="round", belt=("#3d3a2a", "#25231a")),
    beard=hair.Beard(vol=0.06, chin=0.42, grey=0.6, alpha=0.97, tuft_len=0.05,
                     inner=[(0.99, 0.09), (0.97, 0.33), (0.89, 0.53), (0.71, 0.65), (0.46, 0.72), (0.28, 0.79), (0.14, 0.86), (0.0, 0.88)]),
    headwear_back=hair.HeadCloth(layer="back", col="cloth", col_sh="cloth_sh", vol=0.2, flare=0.6),
    headwear_front=hair.HeadCloth(layer="front", col="cloth", col_sh="cloth_sh", vol=0.2, flare=0.6,
                                  stripes=[(0.16, 0.22, "#3e5d86"), (0.27, 0.30, "#3e5d86")],
                                  edge=[(0.0, -0.86), (0.38, -0.83), (0.68, -0.73), (0.90, -0.5), (1.0, -0.19), (1.03, 0.14), (1.0, 0.44)]),
    extra_face=hair.wrinkles,
    arms=make_arms({-1: dict(sleeve="#5d6140", sleeve_sh="#40442b"), 1: dict(sleeve="#5d6140", sleeve_sh="#40442b")}),
)

CHARS = {"jesus": JESUS, "peter": PETER, "miriam": MIRIAM, "eli": ELI}
