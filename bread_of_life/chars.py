"""Character designs: Jesus, Peter, Miriam, Eli (+ crowd extras)."""
import math

import numpy as np
import skia

import hair
from limbs import make_arms
from gfx import ellipse, fill, lin_grad, mix, rad_grad, sample_spline, spline, stroke, tapered
from rig import Character, body_pts


def _fold(cv, pts, dark, light, w=0.05, alpha=0.7):
    """Cel-shaded cloth fold: a dark crease with a soft highlight beside it."""
    sm = sample_spline(pts, n=16)
    cv.drawPath(tapered(sm, 0.004, 0.004, wmid=w), fill(dark, alpha=alpha))
    hl = [(x + 0.05, y + 0.01) for x, y in sm]
    cv.drawPath(tapered(hl, 0.003, 0.003, wmid=w * 0.6), fill(light, alpha=alpha * 0.35))


def tunic_outfit(base, base_sh, trim=None, neckline="v", mantle=None, belt=None, scarf=None, sash=None, clavi=None):
    """Returns an outfit painter: tunic with optional mantle draped over one shoulder."""

    def outfit(cv, st, P, H, ho):
        pts = body_pts(st, P)
        by = P["byaw"] / 60.0
        body = spline(pts, closed=True, corners=[6, 7], tension=0.45)
        lc = st.get("line", "#2a1a14")
        hi = mix(base, "#ffffff", 0.35)
        cv.drawPath(body, fill(base, shader=lin_grad((0, -0.2), (0, 5.0), [mix(base, "#ffffff", 0.12), base, mix(base, base_sh, 0.35)], [0.0, 0.45, 1.0])))
        cv.drawPath(body, stroke(lc, 0.024))
        cv.save()
        cv.clipPath(body, skia.ClipOp.kIntersect, True)
        # side shading away from light
        lx = P["light_x"]
        sx = 1.0 if lx < 0 else -1.0
        cv.drawPath(spline([(sx * 2.4, -0.5), (sx * 1.05, 0.2), (sx * 0.8, 2.0), (sx * 1.0, 5.0), (sx * 2.4, 5.0)], closed=True), fill(base_sh, alpha=0.85))
        # clavi: two narrow vertical stripes from the shoulders (Roman-era tunic)
        if clavi:
            for s_ in (-1, 1):
                x = s_ * 0.78 + by * 0.4
                cv.drawPath(spline([(x - 0.07, -0.2), (x + 0.07, -0.2), (x + 0.1, 5.2), (x - 0.04, 5.2)], closed=True, corners=[0, 1, 2, 3]), fill(clavi, alpha=0.85))
        # drape folds from the shoulders and across the chest
        folds = [[(-0.95, 0.35), (-0.8, 1.3), (-0.95, 2.6)], [(0.95, 0.35), (0.85, 1.4), (1.0, 2.7)],
                 [(-0.5, 0.9), (-0.42, 1.8), (-0.6, 3.2)], [(0.55, 1.0), (0.5, 2.0), (0.7, 3.4)],
                 [(-0.15, 1.6), (0.0, 2.6), (-0.1, 3.9)], [(-1.3, 1.2), (-1.25, 2.4), (-1.35, 3.8)],
                 [(1.3, 1.2), (1.28, 2.5), (1.36, 3.9)]]
        for f in folds:
            _fold(cv, [(x + by * 0.5, y) for x, y in f], base_sh, hi, w=0.045, alpha=0.6)
        # neckline
        ncx = by * 0.55 + ho[0] * 0.3
        if neckline == "v":
            nk = [(ncx - 0.42, -0.1), (ncx - 0.24, 0.28), (ncx, 0.62 + 0.04 * P["breath"]), (ncx + 0.24, 0.28), (ncx + 0.42, -0.1)]
        else:
            nk = [(ncx - 0.52, -0.1), (ncx - 0.4, 0.3), (ncx, 0.45), (ncx + 0.4, 0.3), (ncx + 0.52, -0.1)]
        npath = spline(nk, closed=True, corners=[0, 4])
        cv.drawPath(npath, fill(st["skin"]))
        cv.drawPath(npath, fill(st["skin_sh"], alpha=0.45))
        # collarbone hint
        cv.drawPath(spline([(ncx - 0.3, 0.12), (ncx - 0.12, 0.2)], closed=False), stroke(st["skin_sh2"] if "skin_sh2" in st else st["skin_sh"], 0.016, alpha=0.5))
        cv.drawPath(spline([(ncx + 0.3, 0.12), (ncx + 0.12, 0.2)], closed=False), stroke(st["skin_sh2"] if "skin_sh2" in st else st["skin_sh"], 0.016, alpha=0.5))
        cv.drawPath(spline(nk[0:], closed=False), stroke(lc, 0.02))
        # neckline hem / trim
        cv.drawPath(spline(nk, closed=False), stroke(trim or base_sh, 0.07, alpha=0.75))
        cv.drawPath(spline(nk, closed=False), stroke(lc, 0.018, alpha=0.9))
        if belt:
            cv.drawPath(spline([(-2.5, 3.9), (0, 4.05), (2.5, 3.9), (2.5, 4.2), (0, 4.35), (-2.5, 4.2)], closed=True), fill(belt))
        if sash:
            sc, ssh2 = sash
            sp = [(-1.55 + by * 0.3, 0.25), (-1.2 + by * 0.3, 0.2), (1.6 + by * 0.3, 3.7), (1.2 + by * 0.3, 4.0)]
            band = spline([sp[0], sp[1], sp[2], sp[3]], closed=True, corners=[0, 1, 2, 3])
            cv.drawPath(band, fill(sc))
            cv.drawPath(band, stroke(lc, 0.02))
            cv.drawPath(spline([(-1.3 + by * 0.3, 0.4), (1.35 + by * 0.3, 3.75)], closed=False), stroke(ssh2, 0.04, alpha=0.7))
        cv.restore()
        if mantle:
            mantle(cv, st, P, H, ho, pts)
        if scarf:
            scarf(cv, st, P, H, ho, pts)

    return outfit


def mantle_painter(col, col_sh, side=1, lining=None):
    """A cloak draped over one shoulder (side=+1 screen-right) crossing the chest."""

    def paint(cv, st, P, H, ho, pts):
        by = P["byaw"] / 60.0
        s = side
        sw = st.get("shoulder_w", 1.75)
        up = -0.05 * P["breath"] - 0.12 * P["shrug"]
        lc = st.get("line", "#2a1a14")
        ncx = by * 0.55
        outer = [
            (ncx + s * 0.38, -0.12 + up * 0.3),
            (s * sw * 0.75, 0.05 + up),
            (s * sw * 1.02, 0.42 + up),
            (s * sw * 1.16, 1.2),
            (s * sw * 1.2, 2.6),
            (s * sw * 1.18, 4.9),
            (-s * sw * 0.9, 4.9),
            (-s * sw * 0.55 + by * 0.4, 3.6),
            (ncx - s * 0.05, 1.95),
            (ncx + s * 0.22, 0.75),
        ]
        path = spline(outer, closed=True, corners=[5, 6], tension=0.45)
        hi = mix(col, "#ffffff", 0.3)
        cv.drawPath(path, fill(col, shader=lin_grad((0, -0.2), (0, 4.9), [mix(col, "#ffffff", 0.14), col, mix(col, col_sh, 0.5)], [0.0, 0.4, 1.0])))
        cv.save()
        cv.clipPath(path, skia.ClipOp.kIntersect, True)
        # long folds following the drape (crease + highlight)
        for k in range(6):
            t = 0.12 + k * 0.15
            a = (ncx + s * (0.25 + t * 0.75), 0.35 + t * 0.7)
            b = (-s * sw * 0.15 + s * t * 1.7, 2.7 + t * 1.1)
            c = (s * sw * (0.1 + t * 1.05), 4.9)
            _fold(cv, [a, b, c], col_sh, hi, w=0.07, alpha=0.75)
        # shoulder bunching
        for k in range(3):
            y0 = 0.25 + 0.18 * k
            _fold(cv, [(s * sw * 0.55, y0), (s * sw * 0.8, y0 + 0.12), (s * sw * 1.05, y0 + 0.35)], col_sh, hi, w=0.04, alpha=0.6)
        lx = P["light_x"]
        sx = 1.0 if lx < 0 else -1.0
        cv.drawPath(spline([(sx * 2.6, -0.5), (sx * 1.25, 0.3), (sx * 1.0, 2.0), (sx * 1.1, 5.0), (sx * 2.6, 5.0)], closed=True), fill(col_sh, alpha=0.55))
        # inner shadow along the diagonal edge (the cloth turns under)
        edge = [outer[9], outer[8], outer[7], outer[6]]
        cv.drawPath(tapered(sample_spline([(x + s * 0.12, y) for x, y in edge], n=16), 0.1, 0.14, wmid=0.14), fill(col_sh, alpha=0.6, blur=0.03))
        # highlight along the top edge
        cv.drawPath(tapered(sample_spline([outer[0], (s * sw * 0.6, 0.1 + up), (s * sw * 0.95, 0.45 + up)], n=10), 0.01, 0.01, wmid=0.09), fill("#ffffff", alpha=0.16))
        cv.restore()
        # lining / trim along the diagonal
        if lining:
            cv.drawPath(tapered(sample_spline(edge, n=16), 0.05, 0.07, wmid=0.065), fill(lining))
            cv.drawPath(tapered(sample_spline([(x - s * 0.02, y) for x, y in edge], n=16), 0.012, 0.016, wmid=0.016), fill("#fff0c0", alpha=0.6))
        cv.drawPath(path, stroke(lc, 0.024))

    return paint


# ---------------------------------------------------------------------------
# Jesus
# ---------------------------------------------------------------------------
JESUS_ST = dict(
    skin="#ebb993", skin_sh="#cc8b67", skin_sh2="#a9694d", blush_col="#e07f6c", blush_base=0.07,
    line="#3a2016", lash="#26140d", brow_col="#3a2216", lower_col="#7a4a36", crease_col="#a66b52",
    iris=("#2a170a", "#80501f", "#e2b26a"), lid_shadow="#5a3020",
    hair="#432a1a", hair_sh="#28170d", hair_hl="#82593c", hair_line="#1e1009", hair_rim="#d39a63",
    beard="#4a2e1d", beard_sh="#2c180e",
    eye_x=0.43, eye_y=0.03, eye_w=0.235, eye_h=0.162, eye_low=0.092, eye_tilt=-0.004,
    iris_rx=0.118, iris_ry=0.140, sclera_shadow="#e3d6d0",
    lash_in=0.012, lash_out=0.036, lash_mid=0.032, wing=0.018,
    brow_x=0.43, brow_y=-0.28, brow_in=-0.23, brow_out=0.27, brow_arch=0.055,
    brow_w0=0.056, brow_wm=0.046, brow_w1=0.014,
    mouth_w=0.135, mouth_y=0.655, mouth_h=0.21, nose_y=0.37, nose_len=0.18, jaw_drop=0.07,
    shoulder_w=1.80, neck_w=0.44, neck_len=1.72, neck_top=0.8, face_lw=0.02,
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
    outfit=tunic_outfit("#efe5d3", "#c9b89c", neckline="v", trim="#b89a6a", clavi="#9a5a44",
                        mantle=mantle_painter("#2f557c", "#1f3b5a", side=1, lining="#c8a45a")),
    beard=hair.Beard(),
    headwear_back=hair.LongHair(layer="back"),
    headwear_front=hair.LongHair(layer="front"),
    arms=make_arms({-1: dict(sleeve="#efe5d3", sleeve_sh="#c9b89c"), 1: dict(sleeve="#2f557c", sleeve_sh="#1f3b5a")}),
)


# ---------------------------------------------------------------------------
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
    shoulder_w=2.05, neck_w=0.52, neck_len=1.70, neck_top=0.8,
    slices=[
        (-1.66, 0.02, 0.10, -0.12), (-1.58, 0.47, 0.50, -0.12), (-1.42, 0.78, 0.80, -0.13),
        (-1.15, 0.96, 0.96, -0.12), (-0.80, 1.02, 1.00, -0.10), (-0.40, 1.04, 1.01, -0.08),
        (0.00, 1.03, 0.98, -0.05), (0.28, 1.00, 0.93, -0.01), (0.52, 0.95, 0.85, 0.04),
        (0.72, 0.85, 0.74, 0.10), (0.88, 0.70, 0.60, 0.18), (1.00, 0.52, 0.46, 0.28),
        (1.08, 0.33, 0.33, 0.36), (1.13, 0.16, 0.22, 0.42), (1.15, 0.01, 0.10, 0.45),
    ],
)

def peter_outfit():
    return tunic_outfit("#8a6744", "#634529", neckline="round", sash=("#cdb98f", "#9d8a62"))

PETER = Character(
    "peter", PETER_ST, outfit=peter_outfit(),
    beard=hair.CurlyBeard(vol=0.06, chin=0.14, inner=[(0.98, 0.0), (0.95, 0.28), (0.85, 0.47), (0.66, 0.58), (0.42, 0.64), (0.26, 0.70), (0.13, 0.76), (0.0, 0.78)]),
    headwear_front=hair.ShortCurly(), ears=True,
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
    lip_col="#d06a6a", shoulder_w=1.55, neck_w=0.34, neck_len=1.62, neck_top=0.78,
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
    outfit=tunic_outfit("#6f8197", "#4f6075", neckline="round"),
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
    shoulder_w=1.75, neck_w=0.42, neck_len=1.72, neck_top=0.8,
)

ELI = Character(
    "eli", ELI_ST,
    outfit=tunic_outfit("#5d6140", "#40442b", neckline="round"),
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
