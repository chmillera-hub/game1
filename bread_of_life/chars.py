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
        if neckline == "v":
            nk = [(ncx - 0.42, -0.1), (ncx - 0.24, 0.28), (ncx, 0.62 + 0.04 * P["breath"]), (ncx + 0.24, 0.28), (ncx + 0.42, -0.1)]
        else:
            nk = [(ncx - 0.52, -0.1), (ncx - 0.4, 0.3), (ncx, 0.45), (ncx + 0.4, 0.3), (ncx + 0.52, -0.1)]
        npath = spline(nk, closed=True, corners=[0, 4])
        opening = skia.Path(npath)
        opening.addRect(skia.Rect.MakeLTRB(nk[0][0], -3.0, nk[-1][0], -0.1 + 1e-3))
        body = skia.Op(spline(pts, closed=True, corners=HEM_CORNERS, tension=0.45), opening, skia.PathOp.kDifference_PathOp)
        hi = mix(base, "#ffffff", 0.35)
        cv.drawPath(body, fill(base, shader=lin_grad((0, -0.2), (0, hem), [mix(base, "#ffffff", 0.12), base, mix(base, base_sh, 0.45)], [0.0, 0.35, 1.0])))
        cv.drawPath(body, stroke(lc, 0.024))
        cv.save()
        cv.clipPath(body, skia.ClipOp.kIntersect, True)
        lx = P["light_x"]
        sx = 1.0 if lx < 0 else -1.0
        sw = st.get("shoulder_w", 2.1)
        cv.drawPath(spline([(sx * sw * 1.4, -0.5), (sx * sw * 0.55, 0.2), (sx * sw * 0.42, 2.0), (sx * sw * 0.5, hem + 1), (sx * sw * 1.4, hem + 1)], closed=True), fill(base_sh, alpha=0.8))
        if clavi:
            for s_ in (-1, 1):
                x = s_ * sw * 0.40 + by * 0.4
                cv.drawPath(spline([(x - 0.08, -0.2), (x + 0.08, -0.2), (x + 0.14, hem + 0.5), (x - 0.04, hem + 0.5)], closed=True, corners=[0, 1, 2, 3]), fill(clavi, alpha=0.85))
        # chest/drape folds
        folds = [[(-0.95, 0.35), (-0.8, 1.3), (-0.95, 2.6)], [(0.95, 0.35), (0.85, 1.4), (1.0, 2.7)],
                 [(-0.5, 0.9), (-0.42, 1.8), (-0.6, 3.2)], [(0.55, 1.0), (0.5, 2.0), (0.7, 3.4)],
                 [(-0.15, 1.6), (0.0, 2.6), (-0.1, 3.9)]]
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
            sp = [(-1.55 * sw / 2.05 + by * 0.3, 0.25), (-1.2 * sw / 2.05 + by * 0.3, 0.2), (1.6 * sw / 2.05 + by * 0.3, 3.9), (1.2 * sw / 2.05 + by * 0.3, 4.2)]
            band = spline(sp, closed=True, corners=[0, 1, 2, 3])
            cv.drawPath(band, fill(sc))
            cv.drawPath(band, stroke(lc, 0.02))
        cv.restore()
        # chest seen through the neckline: collarbones, and the soft shadow of the robe's edge
        cv.save()
        cv.clipPath(npath, skia.ClipOp.kIntersect, True)
        sh2 = st.get("skin_sh2", st["skin_sh"])
        cv.drawPath(spline([(ncx - 0.34, 0.1), (ncx - 0.2, 0.14), (ncx - 0.08, 0.2)], closed=False), stroke(sh2, 0.016, alpha=0.45))
        cv.drawPath(spline([(ncx + 0.34, 0.1), (ncx + 0.2, 0.14), (ncx + 0.08, 0.2)], closed=False), stroke(sh2, 0.016, alpha=0.45))
        cv.drawPath(spline(nk, closed=False), stroke(st["skin_sh"], 0.14, alpha=0.4, blur=0.04))
        cv.restore()
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

    return outfit


def mantle_painter(col, col_sh, side=1, lining=None):
    """A himation draped over one shoulder (side=+1 screen-right), crossing the chest and
    hanging to the knees."""

    def paint(cv, st, P, H, ho, pts):
        by = P["byaw"] / 60.0
        s = side
        sw = st.get("shoulder_w", 2.1)
        k = st.get("body_scale", 1.0)
        up = -0.05 * P["breath"] - 0.12 * P["shrug"]
        lc = st.get("line", "#2a1a14")
        ncx = by * 0.55
        knee = 10.6 * k
        sway = 0.06 * math.sin(P["t"] * 0.8 + 1)
        outer = [
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
        cv.drawPath(spline([(sx * sw * 1.6, -0.5), (sx * sw * 0.65, 0.3), (sx * sw * 0.5, 2.0), (sx * sw * 0.55, knee + 1), (sx * sw * 1.6, knee + 1)], closed=True), fill(col_sh, alpha=0.5))
        edge = [outer[13], outer[12], outer[11], outer[10], outer[9], outer[8]]
        cv.drawPath(tapered(sample_spline([(x + s * 0.14, y) for x, y in edge], n=20), 0.12, 0.16, wmid=0.16), fill(col_sh, alpha=0.6, blur=0.03))
        cv.drawPath(tapered(sample_spline([outer[0], (s * sw * 0.58, 0.1 + up), (s * sw * 0.92, 0.45 + up)], n=10), 0.01, 0.01, wmid=0.09), fill("#ffffff", alpha=0.16))
        cv.restore()
        if lining:
            cv.drawPath(tapered(sample_spline(edge, n=20), 0.05, 0.07, wmid=0.065), fill(lining))
            cv.drawPath(tapered(sample_spline([(x - s * 0.02, y) for x, y in edge], n=20), 0.012, 0.016, wmid=0.016), fill("#fff0c0", alpha=0.6))
            cv.drawPath(tapered(sample_spline([outer[6], outer[7], outer[8]], n=12), 0.06, 0.06), fill(lining))
        cv.drawPath(path, stroke(lc, 0.024))

    return paint


# ---------------------------------------------------------------------------
# Jesus
# ---------------------------------------------------------------------------
JESUS_ST = dict(
    skin="#ba976c", skin_sh="#a0764c", skin_sh2="#845b38", blush_col="#b76e57", blush_base=0.07,
    line="#3a2016", lash="#26140d", brow_col="#3a2216", lower_col="#6b442d", crease_col="#926646",
    iris=("#2a170a", "#80501f", "#e2b26a"), lid_shadow="#5a3020",
    hair="#432a1a", hair_sh="#28170d", hair_hl="#82593c", hair_line="#1e1009", hair_rim="#d39a63",
    beard="#4a2e1d", beard_sh="#2c180e",
    eye_x=0.43, eye_y=0.03, eye_w=0.235, eye_h=0.162, eye_low=0.092, eye_tilt=-0.004,
    iris_rx=0.118, iris_ry=0.140, sclera_shadow="#e3d6d0",
    lash_in=0.012, lash_out=0.036, lash_mid=0.032, wing=0.018,
    brow_x=0.43, brow_y=-0.28, brow_in=-0.23, brow_out=0.27, brow_arch=0.055,
    brow_w0=0.056, brow_wm=0.046, brow_w1=0.014,
    mouth_w=0.135, mouth_y=0.655, mouth_h=0.21, nose_y=0.37, nose_len=0.18, jaw_drop=0.07,
    shoulder_w=2.1, neck_w=0.44, neck_len=1.72, neck_top=0.8, face_lw=0.02,
    hem_y=13.2, waist_w=0.80, hip_w=0.85, hem_w=0.95, upper_arm=3.15, forearm=2.8, hand_len=2.15,
    sleeve_w=(0.95, 0.9, 1.08), stance=0.72,
    rim_col="#ffe1b0",
    slices=[
        (-1.70, 0.02, 0.10, -0.12), (-1.62, 0.45, 0.50, -0.12), (-1.46, 0.74, 0.78, -0.13),
        (-1.20, 0.93, 0.95, -0.12), (-0.85, 1.00, 1.00, -0.10), (-0.45, 1.02, 1.01, -0.08),
        (0.00, 1.00, 0.97, -0.05), (0.28, 0.96, 0.92, -0.01), (0.50, 0.89, 0.83, 0.04),
        (0.68, 0.78, 0.71, 0.10), (0.83, 0.63, 0.58, 0.18), (0.95, 0.46, 0.44, 0.28),
        (1.04, 0.29, 0.31, 0.36), (1.10, 0.14, 0.20, 0.42), (1.125, 0.01, 0.10, 0.45),
    ],
)

JESUS = Character(
    "jesus", JESUS_ST,
    outfit=tunic_outfit("#efe5d3", "#c9b89c", neckline="v", trim="#b89a6a", clavi="#9a5a44", belt=("#8a6a3e", "#5e4426"),
                        mantle=mantle_painter("#2f557c", "#1f3b5a", side=1, lining="#c8a45a")),
    beard=hair.Beard(),
    headwear_back=hair.LongHair(layer="back"),
    headwear_front=hair.LongHair(layer="front"),
    arms=make_arms({-1: dict(sleeve="#efe5d3", sleeve_sh="#c9b89c"), 1: dict(sleeve="#2f557c", sleeve_sh="#1f3b5a")}),
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
    eye_x=0.44, eye_y=0.03, eye_w=0.225, eye_h=0.140, eye_low=0.085, eye_tilt=-0.01,
    iris_rx=0.108, iris_ry=0.128, lash_in=0.014, lash_out=0.036, lash_mid=0.032, wing=0.012,
    brow_x=0.44, brow_y=-0.25, brow_in=-0.25, brow_out=0.28, brow_arch=0.03,
    brow_w0=0.075, brow_wm=0.065, brow_w1=0.025,
    mouth_w=0.15, mouth_y=0.67, nose_y=0.38, nose_len=0.22, nose_w=0.07,
    shoulder_w=2.35, neck_w=0.52, neck_len=1.70, neck_top=0.8, hem_y=12.3, hand_len=2.3,
    upper_arm=3.2, forearm=2.85, stance=0.8,
    slices=[
        (-1.66, 0.02, 0.10, -0.12), (-1.58, 0.47, 0.50, -0.12), (-1.42, 0.78, 0.80, -0.13),
        (-1.15, 0.96, 0.96, -0.12), (-0.80, 1.02, 1.00, -0.10), (-0.40, 1.04, 1.01, -0.08),
        (0.00, 1.03, 0.98, -0.05), (0.28, 1.00, 0.93, -0.01), (0.52, 0.95, 0.85, 0.04),
        (0.72, 0.85, 0.74, 0.10), (0.88, 0.70, 0.60, 0.18), (1.00, 0.52, 0.46, 0.28),
        (1.08, 0.33, 0.33, 0.36), (1.13, 0.16, 0.22, 0.42), (1.15, 0.01, 0.10, 0.45),
    ],
)

def peter_outfit():
    return tunic_outfit("#8a6744", "#634529", neckline="round", sash=("#cdb98f", "#9d8a62"), belt=("#c9b48a", "#8f7d55"))

PETER = Character(
    "peter", PETER_ST, outfit=peter_outfit(),
    beard=hair.CurlyBeard(vol=0.06, chin=0.14, inner=[(0.98, 0.0), (0.95, 0.28), (0.85, 0.47), (0.66, 0.58), (0.42, 0.64), (0.26, 0.70), (0.13, 0.76), (0.0, 0.78)]),
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
    eye_x=0.43, eye_y=0.06, eye_w=0.245, eye_h=0.19, eye_low=0.105, eye_tilt=0.004,
    iris_rx=0.128, iris_ry=0.158, lash_in=0.016, lash_out=0.05, lash_mid=0.04, wing=0.05,
    lash_flicks=[(0.82, 0.05), (0.95, 0.06)], lower_lash=True,
    brow_x=0.43, brow_y=-0.24, brow_in=-0.22, brow_out=0.26, brow_arch=0.05,
    brow_w0=0.035, brow_wm=0.03, brow_w1=0.008,
    mouth_w=0.115, mouth_y=0.66, mouth_h=0.17, nose_y=0.38, nose_len=0.15, nose_w=0.04,
    lip_col="#d06a6a", shoulder_w=1.8, neck_w=0.34, neck_len=1.62, neck_top=0.78,
    hem_y=16.0, waist_w=0.74, hip_w=0.9, hem_w=1.0, upper_arm=2.95, forearm=2.6, hand_len=1.85,
    sleeve_w=(0.8, 0.76, 0.92), stance=0.5, body_scale=0.95,
    slices=[
        (-1.62, 0.02, 0.10, -0.12), (-1.55, 0.44, 0.48, -0.12), (-1.40, 0.74, 0.77, -0.13),
        (-1.14, 0.93, 0.94, -0.12), (-0.80, 0.99, 0.99, -0.10), (-0.40, 1.00, 1.00, -0.08),
        (0.00, 0.98, 0.96, -0.05), (0.28, 0.93, 0.90, -0.01), (0.50, 0.84, 0.80, 0.05),
        (0.66, 0.71, 0.68, 0.12), (0.79, 0.55, 0.54, 0.20), (0.90, 0.37, 0.40, 0.29),
        (0.98, 0.21, 0.28, 0.37), (1.02, 0.09, 0.18, 0.42), (1.035, 0.01, 0.10, 0.44),
    ],
)

MIRIAM = Character(
    "miriam", MIRIAM_ST,
    outfit=tunic_outfit("#6f8197", "#4f6075", neckline="round", belt=("#d9c7a5", "#a8946e")),
    headwear_back=hair.HeadCloth(layer="back", vol=0.22, flare=0.7),
    headwear_front=hair.HeadCloth(layer="front", vol=0.22, flare=0.7, hair_fringe=True,
                                  edge=[(0.0, -1.20), (0.38, -1.14), (0.70, -0.95), (0.92, -0.62), (1.02, -0.24), (1.04, 0.12), (1.0, 0.40)]),
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
    eye_x=0.42, eye_y=0.04, eye_w=0.215, eye_h=0.125, eye_low=0.08, eye_tilt=-0.012,
    iris_rx=0.1, iris_ry=0.118, lash_in=0.012, lash_out=0.028, lash_mid=0.026, wing=0.0,
    brow_x=0.42, brow_y=-0.27, brow_in=-0.23, brow_out=0.27, brow_arch=0.04,
    brow_w0=0.075, brow_wm=0.06, brow_w1=0.03, brow_out_up=-0.02,
    mouth_w=0.13, mouth_y=0.68, nose_y=0.40, nose_len=0.24, nose_w=0.065,
    shoulder_w=2.0, neck_w=0.42, neck_len=1.72, neck_top=0.8, hem_y=15.9, hand_len=2.1,
)

ELI = Character(
    "eli", ELI_ST,
    outfit=tunic_outfit("#5d6140", "#40442b", neckline="round", belt=("#3d3a2a", "#25231a")),
    beard=hair.Beard(vol=0.06, chin=0.42, grey=0.6, alpha=0.97, tuft_len=0.05,
                     inner=[(0.97, 0.0), (0.95, 0.24), (0.86, 0.44), (0.68, 0.56), (0.44, 0.63), (0.27, 0.70), (0.14, 0.77), (0.0, 0.79)]),
    headwear_back=hair.HeadCloth(layer="back", col="cloth", col_sh="cloth_sh", vol=0.2, flare=0.6),
    headwear_front=hair.HeadCloth(layer="front", col="cloth", col_sh="cloth_sh", vol=0.2, flare=0.6,
                                  stripes=[(0.16, 0.22, "#3e5d86"), (0.27, 0.30, "#3e5d86")],
                                  edge=[(0.0, -0.98), (0.38, -0.95), (0.68, -0.82), (0.90, -0.56), (1.0, -0.22), (1.03, 0.12), (1.0, 0.40)]),
    extra_face=hair.wrinkles,
    arms=make_arms({-1: dict(sleeve="#5d6140", sleeve_sh="#40442b"), 1: dict(sleeve="#5d6140", sleeve_sh="#40442b")}),
)

CHARS = {"jesus": JESUS, "peter": PETER, "miriam": MIRIAM, "eli": ELI}
