"""Full-body parts: 3D-IK arms with natural elbows and wrists, detailed hands,
lower legs with sandaled feet, and ground contact shadows.

Body units: origin at the neck base, y down, z toward the viewer. A standing
adult is about 7 heads tall: shoulders ~0.5, elbow ~3.8, waist ~4.4,
wrist ~6.7, knee ~10.8, ankle ~16.3, sole ~16.9.
"""
import math

import numpy as np
import skia

from gfx import ellipse, fill, lin_grad, mix, rad_grad, sample_spline, spline, stroke, tapered

ANKLE_Y = 16.3
SOLE_Y = 16.95
# Elbow bend direction (x is outward from the body): elbows drop down and a little back,
# staying near the side of the torso the way a relaxed arm does when it gestures.
DEFAULT_POLE = (0.12, 1.0, -0.55)


def arm_dims(st):
    k = st.get("body_scale", 1.0)
    return st.get("upper_arm", 3.15) * k, st.get("forearm", 2.8) * k


def shoulder_pt(st, P, side):
    sw = st.get("shoulder_w", 2.1)
    by = P["byaw"] / 60.0
    far = 1 - 0.18 * abs(by) if side * by < 0 else 1.0
    up = -0.05 * P["breath"] - 0.12 * P["shrug"]
    return np.array([side * sw * 0.84 * far, 0.62 + up, -0.05])


def rest_target(st, P, side):
    S = shoulder_pt(st, P, side)
    l1, l2 = arm_dims(st)
    sway = 0.04 * math.sin(P["t"] * 0.9 + side)
    return np.array([S[0] + side * 0.22 + sway, S[1] + (l1 + l2) * 0.955, 0.45])


def ik3(S, T, l1, l2, pole):
    """Two-bone IK in 3D. Elbow bends toward `pole` (a direction)."""
    D = T - S
    d = float(np.linalg.norm(D))
    d = min(max(d, abs(l1 - l2) + 1e-3), l1 + l2 - 1e-3)
    u = D / (np.linalg.norm(D) + 1e-9)
    a = (l1 * l1 + d * d - l2 * l2) / (2 * d)
    h = math.sqrt(max(l1 * l1 - a * a, 0.0))
    p = np.asarray(pole, float)
    v = p - np.dot(p, u) * u
    nv = np.linalg.norm(v)
    if nv < 1e-6:
        v = np.array([0.0, 1.0, 0.0]) - u[1] * u
        nv = np.linalg.norm(v) + 1e-9
    v /= nv
    E = S + a * u + h * v
    W = S + d * u
    return E, W


# ---------------------------------------------------------------------------
# Hands
# ---------------------------------------------------------------------------
HAND_POSES = {
    #          index middle ring pinky curls, thumb abduction (deg), spread
    "open": dict(curl=(0.06, 0.04, 0.08, 0.12), thumb=38, spread=1.0),
    "relaxed": dict(curl=(0.30, 0.38, 0.44, 0.50), thumb=22, spread=0.35),
    "fist": dict(curl=(1.0, 1.0, 1.0, 1.0), thumb=8, spread=0.0),
    "point": dict(curl=(0.0, 1.0, 1.0, 1.0), thumb=12, spread=0.2),
    "hold": dict(curl=(0.55, 0.6, 0.66, 0.72), thumb=48, spread=0.3),
    "flat": dict(curl=(0.02, 0.02, 0.04, 0.06), thumb=14, spread=0.25),
    "cup": dict(curl=(0.28, 0.3, 0.32, 0.36), thumb=30, spread=0.15),
}

FINGERS = [  # base x (thumb at +x), base y, phalanx lengths, base width, tip width, spread angle
    (0.150, 0.475, (0.190, 0.112, 0.082), 0.098, 0.074, -7.0),
    (0.050, 0.500, (0.210, 0.128, 0.090), 0.104, 0.080, -1.5),
    (-0.050, 0.490, (0.198, 0.120, 0.086), 0.097, 0.075, 3.5),
    (-0.142, 0.455, (0.152, 0.092, 0.074), 0.084, 0.064, 9.0),
]


def _pose(name, name_b=None, t=0.0):
    A = HAND_POSES.get(name, HAND_POSES["relaxed"])
    B = HAND_POSES.get(name_b or name, A)
    return (tuple(a + (b - a) * t for a, b in zip(A["curl"], B["curl"])),
            A["thumb"] + (B["thumb"] - A["thumb"]) * t, A["spread"] + (B["spread"] - A["spread"]) * t)


def _capsule_chain(pts, w0, w1):
    return tapered(pts, w0, w1, wmid=(w0 + w1) * 0.5 * 1.04)


def draw_hand(cv, st, pose, x, y, ang_deg, length, thumb_side=1, view="back", pose_b=None, pose_t=0.0,
              squash=1.0, foreshorten=1.0, light_x=-0.7):
    """Hand with the wrist at (x, y) pointing along ang_deg (0 = down, +90 = screen-left).

    length: wrist to middle fingertip in body units. thumb_side: +1 thumb toward +x of
    the hand's local frame. view: "back" (knuckles/nails) or "palm"."""
    curls, thumb_ab, spread = _pose(pose, pose_b, pose_t)
    lc = st.get("line", "#2a1a14")
    skin, sh = st["skin"], st["skin_sh"]
    sh2 = st.get("skin_sh2", sh)
    cv.save()
    cv.translate(x, y)
    cv.rotate(ang_deg)
    cv.scale(length * squash * thumb_side, length * (0.62 + 0.38 * min(max(foreshorten, 0.0), 1.0)))
    lw = 0.024 / max(length, 1e-3)
    # --- fingers (projected curl: each phalanx tilts out of the palm plane)
    finger_parts = []  # (path, folded, tip_info)
    for k, (bx, by, lens, w0, w1, spr) in enumerate(FINGERS):
        c = curls[k]
        angs = [c * 72.0, c * 168.0, c * 232.0]
        a0 = math.radians(spr * spread)
        pts = [(bx, by)]
        px, py = bx, by
        folded = False
        for L, ang in zip(lens, angs):
            proj = math.cos(math.radians(ang))
            if proj < 0:
                folded = True
            px += math.sin(a0) * L * abs(proj) * (1 if proj >= 0 else 0.3)
            py += math.cos(a0) * L * proj
            pts.append((px, py))
        # keep folded tips inside the palm silhouette
        pts = [(px_, max(py_, 0.22)) for px_, py_ in pts]
        sm = sample_spline(pts, n=10)
        path = _capsule_chain(sm, w0, w1 * (1.0 + 0.25 * c))
        finger_parts.append((path, folded, pts, w1, c, k))
    # --- thumb
    ta = math.radians(thumb_ab)
    tb = (0.165, 0.11)
    seg = [0.20, 0.135, 0.11]
    tpts = [tb]
    ang = ta
    px, py = tb
    for i, L in enumerate(seg):
        px += math.sin(ang) * L
        py += math.cos(ang) * L
        tpts.append((px, py))
        ang -= math.radians(12 + 10 * curls[0])
    thumb = _capsule_chain(sample_spline(tpts, n=10), 0.13, 0.085)
    palm_pts = [(-0.175, 0.0), (0.175, 0.0), (0.215, 0.20), (0.205, 0.45), (0.10, 0.505), (-0.02, 0.51),
                (-0.13, 0.49), (-0.205, 0.44), (-0.218, 0.20)]
    palm = spline(palm_pts, closed=True, corners=[0, 1], tension=0.5)
    # draw order: back view hides folded fingers behind the palm; palm view shows them over it
    back_parts = [p for p in finger_parts if not p[1]]
    folded_parts = [p for p in finger_parts if p[1]]
    order = []
    if view == "back":
        order = [("finger", p) for p in folded_parts] + [("palm", palm)] + [("finger", p) for p in back_parts] + [("thumb", thumb)]
    else:
        order = [("thumb", thumb), ("palm", palm)] + [("finger", p) for p in back_parts + folded_parts]
    paths = [o[1][0] if o[0] == "finger" else o[1] for o in order]
    # outline underlay -> single clean silhouette
    for p in paths:
        cv.drawPath(p, stroke(lc, lw * 2.0))
    for p in paths:
        cv.drawPath(p, fill(skin))
    # shading: side away from light, and soft gradient toward the fingertips
    full = skia.Path()
    for p in paths:
        full.addPath(p)
    cv.save()
    cv.clipPath(full, skia.ClipOp.kIntersect, True)
    shade_x = 1.0 if light_x * thumb_side < 0 else -1.0
    cv.drawPath(spline([(shade_x * 0.12, -0.1), (shade_x * 0.6, -0.1), (shade_x * 0.6, 1.2), (shade_x * 0.08, 1.2)], closed=True),
                fill(sh, alpha=0.45, blur=0.03))
    cv.drawRect(skia.Rect.MakeLTRB(-0.6, -0.1, 0.6, 1.3), fill("#000000", shader=lin_grad((0, 0.0), (0, 1.0), [(1, 1, 1, 0.07), (0, 0, 0, 0.0)])))
    cv.restore()
    # inner lines: separations between neighbouring fingers, knuckles, nails, palm creases
    for (path, folded, pts, w1, c, k) in finger_parts:
        if view == "back" and not folded:
            if c < 0.6:
                # nail
                tip = pts[-1]
                prev = pts[-2]
                dx, dy = tip[0] - prev[0], tip[1] - prev[1]
                n = math.hypot(dx, dy) + 1e-9
                nx_, ny_ = tip[0] - dx / n * 0.035, tip[1] - dy / n * 0.035
                cv.drawPath(ellipse(nx_, ny_, w1 * 0.32, 0.03), fill(mix(skin, "#ffffff", 0.35), alpha=0.85))
                cv.drawPath(ellipse(nx_, ny_, w1 * 0.32, 0.03), stroke(sh, lw * 0.7, alpha=0.6))
            # knuckle crease at the middle joint
            j = pts[2]
            cv.drawPath(spline([(j[0] - 0.025, j[1] - 0.004), (j[0], j[1] + 0.008), (j[0] + 0.025, j[1] - 0.004)], closed=False),
                        stroke(sh2, lw * 0.75, alpha=0.55))
        if folded:
            # curled finger: crease line along the fold
            j = pts[1]
            cv.drawPath(spline([(j[0] - 0.04, j[1]), (j[0] + 0.04, j[1])], closed=False), stroke(lc, lw * 0.8, alpha=0.6))
    for k in range(3):
        # separations between adjacent fingers near their bases
        a = FINGERS[k]
        b = FINGERS[k + 1]
        mx = (a[0] + b[0]) / 2
        my = min(a[1], b[1]) + 0.02
        if max(curls[k], curls[k + 1]) < 0.75:
            cv.drawPath(spline([(mx, my), (mx + 0.004, my + 0.07)], closed=False), stroke(lc, lw * 0.9, alpha=0.7))
    if view == "palm":
        cv.drawPath(spline([(-0.16, 0.30), (0.0, 0.36), (0.16, 0.28)], closed=False), stroke(sh2, lw * 0.8, alpha=0.45))
        cv.drawPath(spline([(0.12, 0.12), (0.04, 0.24), (0.02, 0.40)], closed=False), stroke(sh2, lw * 0.8, alpha=0.4))
    else:
        for k in range(4):
            bx, by_ = FINGERS[k][0], FINGERS[k][1]
            cv.drawPath(ellipse(bx, by_ - 0.01, 0.022, 0.012), fill(mix(skin, "#ffffff", 0.25), alpha=0.5))
    cv.restore()


# ---------------------------------------------------------------------------
# Arms
# ---------------------------------------------------------------------------

def arm_geometry(st, P, side, spec):
    S = shoulder_pt(st, P, side)
    l1, l2 = arm_dims(st)
    rest = rest_target(st, P, side)
    if spec is None:
        T = rest
    else:
        tx, ty = spec["target"][:2]
        tz = spec["target"][2] if len(spec["target"]) > 2 else spec.get("z", 0.6)
        T = np.array([tx, ty, tz])
        rb = spec.get("rest_blend", 0.0)
        if rb > 0:
            T = T + (rest - T) * rb
        # small "talking" motion while a gesture is held
        beat = spec.get("beat", 0.0)
        if beat > 0:
            t = P["t"]
            T = T + beat * np.array([0.10 * math.sin(t * 2.3 + side), 0.08 * math.sin(t * 3.1), 0.06 * math.sin(t * 1.7)])
    px, py, pz = (spec or {}).get("pole") or DEFAULT_POLE
    E, W = ik3(S, T, l1, l2, (side * px, py, pz))
    return S, E, W


def hand_direction(E, W, spec, side):
    """3D hand direction: forearm direction with a natural wrist bend (never hyperextended)."""
    f = W - E
    f = f / (np.linalg.norm(f) + 1e-9)
    bend = math.radians((spec or {}).get("wrist", 8.0))
    # bend toward the body's "palm side": rotate within the plane spanned by f and down/in
    ref = np.array([-side * 0.3, 0.2, 1.0])
    ref = ref - np.dot(ref, f) * f
    nr = np.linalg.norm(ref)
    if nr < 1e-6:
        return f
    ref /= nr
    d = f * math.cos(bend) + ref * math.sin(bend)
    # optional in-plane tilt of the hand outward (e.g. a pointing finger aimed at the horizon)
    tilt = math.radians(side * (spec or {}).get("tilt", 0.0))
    if tilt:
        c, s = math.cos(tilt), math.sin(tilt)
        d = np.array([d[0] * c - d[1] * s, d[0] * s + d[1] * c, d[2]])
    return d / (np.linalg.norm(d) + 1e-9)


def draw_arm(cv, st, P, side, spec, sty):
    """Sleeved arm from shoulder to wrist plus the hand."""
    S, E, W = arm_geometry(st, P, side, spec)
    lc = st.get("line", "#2a1a14")
    scol = sty.get("sleeve", st.get("sleeve", "#efe5d3"))
    ssh = sty.get("sleeve_sh", st.get("sleeve_sh", "#c9b89c"))
    k = st.get("body_scale", 1.0)
    w_up, w_el, w_cuff = st.get("sleeve_w", (0.95, 0.9, 1.05))
    w_up, w_el, w_cuff = w_up * k, w_el * k, w_cuff * k
    s2, e2, w2 = (float(S[0]), float(S[1])), (float(E[0]), float(E[1])), (float(W[0]), float(W[1]))
    hd = hand_direction(E, W, spec, side)
    hang = math.degrees(math.atan2(-hd[0], hd[1]))
    fore = math.hypot(hd[0], hd[1])
    hand_len = st.get("hand_len", 2.15) * (spec or {}).get("hand_scale", 1.0) * k
    pose = (spec or {}).get("hand", "relaxed")
    show_hand = pose != "none" and (spec or {}).get("hand_b") != "none" and hand_len > 0.05
    thumb = (spec or {}).get("thumb", -side)
    view = (spec or {}).get("view", "back")
    # wrist sits a little inside the cuff
    wrist = (w2[0] - hd[0] * 0.25, w2[1] - hd[1] * 0.25)

    def hand():
        if show_hand:
            draw_hand(cv, st, pose, wrist[0], wrist[1], hang, hand_len, thumb_side=thumb, view=view,
                      pose_b=(spec or {}).get("hand_b"), pose_t=(spec or {}).get("hand_t", 0.0),
                      squash=(spec or {}).get("squash", 1.0), foreshorten=fore, light_x=P["light_x"])

    hand_behind = (spec or {}).get("hand_under", False) or (hd[2] < -0.45)
    if hand_behind:
        hand()
    # one continuous sleeve from shoulder through the elbow to the cuff (cloth bends smoothly)
    pts = sample_spline([s2, e2, w2], n=20)
    sleeve = tapered(pts, w_up, w_cuff, wmid=w_el)
    lx = P["light_x"]
    cv.drawPath(sleeve, stroke(lc, 0.05))
    cv.drawPath(sleeve, fill(scol))
    cv.save()
    cv.clipPath(sleeve, skia.ClipOp.kIntersect, True)
    off = 0.3 if lx < 0 else -0.3
    sh_pts = []
    for i in range(len(pts)):
        p0 = pts[max(i - 1, 0)]
        p1 = pts[min(i + 1, len(pts) - 1)]
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        n = math.hypot(dx, dy) + 1e-9
        sh_pts.append((pts[i][0] - dy / n * off * w_el * 1.3, pts[i][1] + dx / n * off * w_el * 1.3))
    cv.drawPath(tapered(sh_pts, w_up * 0.7, w_cuff * 0.7, wmid=w_el * 0.7), fill(ssh, alpha=0.75))
    # folds gathering at the elbow
    for t_ in (-0.18, 0.0, 0.18):
        cv.drawPath(spline([(e2[0] + t_ - 0.12, e2[1] - 0.35), (e2[0] + t_ * 0.5, e2[1]), (e2[0] + t_ + 0.1, e2[1] + 0.35)], closed=False),
                    stroke(ssh, 0.035, alpha=0.8))
    cv.restore()
    cv.drawPath(sleeve, stroke(lc, 0.022, alpha=0.9))
    # cuff opening (dark inside)
    dx, dy = w2[0] - e2[0], w2[1] - e2[1]
    n = math.hypot(dx, dy) + 1e-9
    nx_, ny_ = -dy / n, dx / n
    cw = w_cuff * 0.5
    cuff = spline([(w2[0] + nx_ * cw, w2[1] + ny_ * cw), (w2[0] + dx / n * 0.10, w2[1] + dy / n * 0.10), (w2[0] - nx_ * cw, w2[1] - ny_ * cw),
                   (w2[0] - dx / n * 0.06, w2[1] - dy / n * 0.06)], closed=True)
    cv.drawPath(cuff, fill(mix(ssh, "#000000", 0.35), alpha=0.85))
    cv.drawPath(cuff, stroke(lc, 0.02, alpha=0.8))
    if not hand_behind:
        hand()
    return E, W


def make_arms(arm_style=None):
    """Arms painter for Character.draw; P['arm_l'] / P['arm_r'] hold gesture specs (None = at rest)."""
    arm_style = arm_style or {}

    def arms(cv, st, P, layer):
        order = ((-1, "arm_l"), (1, "arm_r"))
        # draw the arm that is further back first (crossed arms etc.)
        specs = {k: P.get(k) for _, k in order}
        if specs["arm_r"] and specs["arm_r"].get("under", False):
            order = ((1, "arm_r"), (-1, "arm_l"))
        for side, key in order:
            spec = specs[key]
            sp_layer = (spec or {}).get("layer", "body")
            if sp_layer != layer:
                continue
            draw_arm(cv, st, P, side, spec, arm_style.get(side, {}))

    return arms


# ---------------------------------------------------------------------------
# Legs and feet
# ---------------------------------------------------------------------------

def legs_pose(P):
    """Returns (left_foot, right_foot) offsets for standing / walking."""
    walk = P.get("walk", 0.0)
    if walk <= 0:
        return (0.0, 0.0), (0.0, 0.0)
    ph = P.get("walk_phase", 0.0) * 2 * math.pi
    lift_l = max(0.0, math.sin(ph)) * 0.55 * walk
    lift_r = max(0.0, math.sin(ph + math.pi)) * 0.55 * walk
    return (0.0, -lift_l), (0.0, -lift_r)


def draw_legs(cv, st, P, hem_y, sty=None):
    """Lower legs below the hem with sandals; draws the ground shadow too."""
    sty = sty or {}
    if hem_y >= ANKLE_Y - 0.1:
        exposed = False
    else:
        exposed = True
    lc = st.get("line", "#2a1a14")
    skin, sh = st["skin"], st["skin_sh"]
    k = st.get("body_scale", 1.0)
    stance = st.get("stance", 0.72) * k
    by = P["byaw"] / 60.0
    (lfx, lfy), (rfx, rfy) = legs_pose(P)
    sole = SOLE_Y * k
    ankle = ANKLE_Y * k
    # contact shadow
    cv.drawPath(ellipse(by * 0.4, sole + 0.05, stance * 2.2, 0.42), fill("#000000", alpha=0.22, blur=0.25))
    sandal = sty.get("sandal", "#6b4a2e")
    for side, (fx_, fy_) in ((-1, (lfx, lfy)), (1, (rfx, rfy))):
        ax = side * stance + by * 0.35 * side * 0.0 + by * 0.25
        knee = (side * stance * 0.85 + by * 0.25, hem_y - 1.0)
        ank = (ax + fx_, ankle + fy_)
        if exposed:
            calf = (knee[0] + (ank[0] - knee[0]) * 0.35 + side * 0.07, knee[1] + (ank[1] - knee[1]) * 0.35)
            low = (knee[0] + (ank[0] - knee[0]) * 0.75 + side * 0.02, knee[1] + (ank[1] - knee[1]) * 0.75)
            leg = tapered(sample_spline([knee, calf, low, ank], n=12), 0.66 * k, 0.36 * k, wmid=0.74 * k)
            cv.drawPath(leg, stroke(lc, 0.05))
            cv.drawPath(leg, fill(skin))
            cv.save()
            cv.clipPath(leg, skia.ClipOp.kIntersect, True)
            sx = 1.0 if P["light_x"] < 0 else -1.0
            cv.drawPath(tapered([(knee[0] + sx * 0.22, knee[1]), (ank[0] + sx * 0.14, ank[1])], 0.3, 0.2), fill(sh, alpha=0.7))
            cv.restore()
        # foot (seen from the front, slightly turned out), sandal sole and straps
        toe_dir = side * 0.25
        foot = [(ank[0] - 0.24 * k, ank[1] - 0.05), (ank[0] + 0.24 * k, ank[1] - 0.05),
                (ank[0] + (0.34 + toe_dir * 0.4) * k, ank[1] + 0.45 * k), (ank[0] + (0.30 + toe_dir) * k, ank[1] + 0.66 * k),
                (ank[0] + toe_dir * k, ank[1] + 0.72 * k), (ank[0] - (0.30 - toe_dir) * k, ank[1] + 0.66 * k),
                (ank[0] - (0.34 - toe_dir * 0.4) * k, ank[1] + 0.45 * k)]
        fp = spline(foot, closed=True, corners=[0, 1])
        sole_p = ellipse(ank[0] + toe_dir * 0.6 * k, ank[1] + 0.66 * k, 0.40 * k, 0.12 * k)
        cv.drawPath(sole_p, fill(sandal))
        cv.drawPath(fp, stroke(lc, 0.05))
        cv.drawPath(fp, fill(skin))
        cv.drawPath(fp, fill(sh, alpha=0.3))
        # toes
        for t in range(4):
            tx = ank[0] + (toe_dir - 0.21 + t * 0.14) * k
            cv.drawPath(spline([(tx, ank[1] + 0.58 * k), (tx + 0.01, ank[1] + 0.69 * k)], closed=False), stroke(sh, 0.025, alpha=0.7))
        # straps
        cv.drawPath(spline([(ank[0] - 0.3 * k, ank[1] + 0.33 * k), (ank[0] + toe_dir * 0.5 * k, ank[1] + 0.40 * k), (ank[0] + 0.32 * k, ank[1] + 0.33 * k)], closed=False), stroke(sandal, 0.09 * k))
        cv.drawPath(spline([(ank[0] - 0.2 * k, ank[1] + 0.02), (ank[0], ank[1] + 0.06), (ank[0] + 0.2 * k, ank[1] + 0.02)], closed=False), stroke(sandal, 0.08 * k))
        cv.drawPath(sole_p, stroke(lc, 0.03))
