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


def ik3(S, T, l1, l2, pole, fallback=(1.0, 0.3, -0.3)):
    """Two-bone IK in 3D. The elbow bends toward `pole` (a direction); when the pole lines up with
    the reach direction the bend direction eases over to `fallback`, so the elbow never flips."""
    D = T - S
    d = float(np.linalg.norm(D))
    d = min(max(d, abs(l1 - l2) + 1e-3), l1 + l2 - 1e-3)
    u = D / (np.linalg.norm(D) + 1e-9)
    a = (l1 * l1 + d * d - l2 * l2) / (2 * d)
    h = math.sqrt(max(l1 * l1 - a * a, 0.0))
    p = np.asarray(pole, float)
    p = p / (np.linalg.norm(p) + 1e-9)
    v = p - np.dot(p, u) * u
    nv = float(np.linalg.norm(v))
    q = np.asarray(fallback, float)
    q = q / (np.linalg.norm(q) + 1e-9)
    v2 = q - np.dot(q, u) * u
    nv2 = float(np.linalg.norm(v2))
    w = min(1.0, max(0.0, (nv - 0.08) / 0.3))
    w = w * w * (3 - 2 * w)
    v = (v / (nv + 1e-9)) * w + (v2 / (nv2 + 1e-9)) * (1 - w)
    v = v / (np.linalg.norm(v) + 1e-9)
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
              squash=1.0, foreshorten=1.0, light_x=-0.7, thumb_front=None):
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
    # the thumb sits on the palm side: in front when the palm faces us, behind when we see the back
    if thumb_front is None:
        thumb_front = view == "palm"
    if view == "back":
        order = [("finger", p) for p in folded_parts] + [("palm", palm)] + [("finger", p) for p in back_parts]
    else:
        order = [("palm", palm)] + [("finger", p) for p in back_parts + folded_parts]
    order = order + [("thumb", thumb)] if thumb_front else [("thumb", thumb)] + order
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

def _smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def natural_pole(S, T, side):
    """Outward-relative elbow direction that suits where the hand is: the elbow hangs down and a
    little back for hands below the shoulder, and swings out to the side as the hand rises toward
    the head (scratching the head, raising a hand)."""
    rise = S[1] - T[1]  # > 0 when the hand is above the shoulder (y points down)
    h = _smooth((rise + 1.2) / 3.4)
    down = np.array(DEFAULT_POLE)
    out = np.array([1.0, 0.2, -0.25])
    return down * (1 - h) + out * h


def resolve_pole(spec, S, T, side):
    """Absolute pole vector for the IK, blending explicit and natural poles during transitions."""
    nat = natural_pole(S, T, side)
    spec = spec or {}
    pm = spec.get("pole_mix")
    if pm is not None:
        pa, pb, x = pm
        pa = nat if pa is None else np.array(pa, float)
        pb = nat if pb is None else np.array(pb, float)
        p = pa + (pb - pa) * x
    elif spec.get("pole") is not None:
        p = np.array(spec["pole"], float)
    else:
        p = nat
    return np.array([side * p[0], p[1], p[2]])


def arm_target(st, P, side, spec):
    rest = rest_target(st, P, side)
    if spec is None:
        return rest
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
    return T


def arm_geometry(st, P, side, spec):
    S = shoulder_pt(st, P, side)
    l1, l2 = arm_dims(st)
    T = arm_target(st, P, side, spec)
    # a hand moving between poses travels in front of the body, never through the shoulder joint
    r_min = 0.32 * (l1 + l2)
    gap = r_min - float(np.linalg.norm(T - S))
    if gap > 0:
        T = T + np.array([0.0, 0.0, 1.2 * gap])
    pole = resolve_pole(spec, S, T, side)
    E, W = ik3(S, T, l1, l2, pole, fallback=(side * 1.0, 0.3, -0.3))
    return S, E, W


# Direction from a body toward the camera (slightly above the hands, looking a little down).
CAM_DIR = np.array([0.0, -0.26, 0.966])

# Palm orientation hints (outward-relative x: + away from the body's midline; y: + down;
# z: + toward the viewer). A relaxed hanging hand faces the thigh, turned partly backward.
REST_PALM = (-0.7, 0.0, -0.7)
PALM_HINTS = {"up": (0.0, -1.0, 0.0), "down": (0.0, 1.0, 0.0), "fwd": (0.0, 0.0, 1.0), "body": (0.0, 0.0, -1.0),
              "in": (-1.0, 0.0, 0.0), "out": (1.0, 0.0, 0.0)}


def palm_vec(h):
    if h is None:
        return REST_PALM
    if isinstance(h, str):
        return PALM_HINTS[h]
    return tuple(h)


def palm_hint_abs(spec, side):
    h = palm_vec((spec or {}).get("palm"))
    return np.array([side * h[0], h[1], h[2]], float)


def _perp(v, f):
    v = v - np.dot(v, f) * f
    n = np.linalg.norm(v)
    return v / n if n > 1e-6 else None


def hand_direction(E, W, spec, side, use_override=True):
    """3D hand direction. The hand lies across its palm direction (a palm turned toward someone
    with the forearm pointing at them means the wrist bends back and the fingers rise), as close to
    the forearm line as a wrist allows; the gesture's wrist angle then curls it toward the palm."""
    if use_override and (spec or {}).get("hand_dir") is not None:
        d = np.asarray(spec["hand_dir"], float)
        return d / (np.linalg.norm(d) + 1e-9)
    f = W - E
    f = f / (np.linalg.norm(f) + 1e-9)
    nh = palm_hint_abs(spec, side)
    nh = nh / (np.linalg.norm(nh) + 1e-9)
    # partial projection: the hand turns into its palm plane without ever flipping sides
    d0 = f - 0.88 * np.dot(f, nh) * nh
    nd = float(np.linalg.norm(d0))
    up = np.array([0.0, -1.0, 0.0]) - np.dot(np.array([0.0, -1.0, 0.0]), nh) * nh
    up = up / (np.linalg.norm(up) + 1e-9)
    w = _smooth((nd - 0.12) / 0.4)  # forearm nearly along the palm direction: fingers rise
    d = (d0 / (nd + 1e-9)) * w + up * (1 - w)
    d = d / (np.linalg.norm(d) + 1e-9)
    # a wrist bends at most ~80 degrees away from the forearm line
    cosb = float(np.dot(d, f))
    lim = math.cos(math.radians(80))
    if cosb < lim:
        perp = d - cosb * f
        perp = perp / (np.linalg.norm(perp) + 1e-9)
        d = f * lim + perp * math.sin(math.radians(80))
    bend = math.radians((spec or {}).get("wrist", 8.0))
    ref = _perp(nh, d)
    if ref is not None and bend:
        d = d * math.cos(bend) + ref * math.sin(bend)
    tilt = math.radians(side * (spec or {}).get("tilt", 0.0))
    if tilt:
        c, s = math.cos(tilt), math.sin(tilt)
        d = np.array([d[0] * c - d[1] * s, d[0] * s + d[1] * c, d[2]])
    return d / (np.linalg.norm(d) + 1e-9)


def hand_screen_dir(hd):
    """Direction and length of a 3D hand direction as seen by the slightly raised camera:
    a hand pointing at the viewer appears to point a little downward, foreshortened."""
    x = float(hd[0])
    y = float(hd[1]) * CAM_DIR[2] - float(hd[2]) * CAM_DIR[1]
    L = math.hypot(x, y)
    if L < 1e-6:
        return 0.0, 1.0, 0.0
    return x / L, y / L, min(1.0, L)


def hand_frame(hd, spec, side):
    """Palm normal and thumb direction for a hand pointing along hd.

    side -1 is the screen-left arm, which is the character's anatomical right arm (they face us).
    Palm up -> the thumb points away from the body; palm down or toward someone -> it points
    toward the body's midline."""
    n = _perp(palm_hint_abs(spec, side), hd)
    if n is None:
        n = _perp(np.array([-side * 1.0, 0.0, -0.35]), hd)
    if n is None:
        n = np.array([0.0, 0.0, -1.0])
    # cross products in a right-handed frame (flip y, which points down in body units)
    dR = np.array([hd[0], -hd[1], hd[2]])
    nR = np.array([n[0], -n[1], n[2]])
    tR = np.cross(dR, nR) if side < 0 else np.cross(nR, dR)
    t = np.array([tR[0], -tR[1], tR[2]])
    return n, t / (np.linalg.norm(t) + 1e-9)


def _seg_shape(a, b, wa, wb, round_a=1.0, round_b=1.0, bulge=0.0, n=9):
    """Tapered limb segment a->b. Returns (closed fill path, outline without the a-end cap)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    L = float(np.linalg.norm(d))
    if L < 1e-6:
        d = np.array([0.0, 1.0])
        L = 1e-6
    d = d / L
    nrm = np.array([-d[1], d[0]])
    ts = np.linspace(0.0, 1.0, n)
    w = wa + (wb - wa) * ts + bulge * np.sin(np.pi * ts)
    mids = a[None, :] + ts[:, None] * (b - a)[None, :]
    left = mids + nrm * (w[:, None] / 2)
    right = mids - nrm * (w[:, None] / 2)

    def cap(c, axis, r, k):
        # half-ellipse from +nrm side around `axis` to the -nrm side
        out = []
        for ang in np.linspace(0.0, math.pi, 7)[1:-1]:
            out.append(c + nrm * (r * math.cos(ang)) + axis * (r * k * math.sin(ang)))
        return out

    cap_b = cap(b, d, wb / 2, round_b)
    # the a-end cap runs from the right side back round to the left side
    cap_a_pts = [a - nrm * (wa / 2 * math.cos(ang)) - d * (wa / 2 * round_a * math.sin(ang)) for ang in np.linspace(0.0, math.pi, 7)[1:-1]]
    ring = list(left) + cap_b + list(right[::-1]) + cap_a_pts
    closed = spline([tuple(p) for p in ring], closed=True, tension=0.5)
    open_pts = list(left) + cap_b + list(right[::-1])
    outline = spline([tuple(p) for p in open_pts], closed=False, tension=0.5)
    return closed, outline, left, right


def _shade_segment(cv, path, a, b, w, ssh, lx):
    """Cel shadow along the side of a sleeve segment away from the key light."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    L = float(np.linalg.norm(d)) + 1e-9
    d = d / L
    nrm = np.array([-d[1], d[0]])
    # the side whose normal points away from the light gets the shadow
    side_sign = 1.0 if nrm[0] * lx > 0 else -1.0
    off = nrm * side_sign * w * 0.42
    band = [tuple(a + off), tuple(b + off)]
    cv.save()
    cv.clipPath(path, skia.ClipOp.kIntersect, True)
    cv.drawPath(tapered(sample_spline(band, n=6), w * 0.75, w * 0.75), fill(ssh, alpha=0.75))
    cv.restore()


def draw_arm(cv, st, P, side, spec, sty):
    """Sleeved arm (upper arm and forearm drawn in depth order, so the nearer part hides the
    one behind it) plus an anatomically oriented hand."""
    S, E, W = arm_geometry(st, P, side, spec)
    lc = st.get("line", "#2a1a14")
    scol = sty.get("sleeve", st.get("sleeve", "#efe5d3"))
    ssh = sty.get("sleeve_sh", st.get("sleeve_sh", "#c9b89c"))
    k = st.get("body_scale", 1.0)
    w_up, w_el, w_cuff = st.get("sleeve_w", (0.95, 0.9, 1.05))
    w_up, w_el, w_cuff = w_up * k, w_el * k, w_cuff * k
    s2, e2, w2 = np.array(S[:2]), np.array(E[:2]), np.array(W[:2])
    hd = hand_direction(E, W, spec, side)
    sx, sy, fore = hand_screen_dir(hd)
    hang = math.degrees(math.atan2(-sx, sy))
    hand_len = st.get("hand_len", 2.15) * (spec or {}).get("hand_scale", 1.0) * k
    pose = (spec or {}).get("hand", "relaxed")
    show_hand = pose != "none" and (spec or {}).get("hand_b") != "none" and hand_len > 0.05
    # palm and thumb from the 3D hand frame, seen by a camera at about eye height (so hands
    # below the face are seen a little from above)
    n, t = hand_frame(hd, spec, side)
    view = "palm" if float(np.dot(n, CAM_DIR)) > 0.0 else "back"
    ca, sa = math.cos(math.radians(hang)), math.sin(math.radians(hang))
    t_img = (t[0], t[1] * CAM_DIR[2] + t[2] * -CAM_DIR[1])  # apparent thumb direction in the picture
    ts = t_img[0] * ca + t_img[1] * sa  # thumb direction across the hand in the picture
    thumb = 1 if ts >= 0 else -1
    # a hand seen edge-on still shows its thickness and thumb, so it never thins to a blade
    squash = (0.62 + 0.38 * min(1.0, abs(ts))) * (spec or {}).get("squash", 1.0)
    thumb_front = view == "palm"
    lx = P["light_x"]
    # wrist sits a little inside the cuff
    wrist = (w2[0] - sx * fore * 0.25, w2[1] - sy * fore * 0.25)

    def hand():
        if show_hand:
            draw_hand(cv, st, pose, wrist[0], wrist[1], hang, hand_len, thumb_side=thumb, view=view,
                      pose_b=(spec or {}).get("hand_b"), pose_t=(spec or {}).get("hand_t", 0.0),
                      squash=squash, foreshorten=fore, light_x=lx, thumb_front=thumb_front)

    up_closed, up_open, _, _ = _seg_shape(s2, e2, w_up, w_el, round_a=0.55, round_b=1.0, bulge=0.04 * k)
    fo_closed, fo_open, _, _ = _seg_shape(e2, w2, w_el, w_cuff, round_a=1.0, round_b=0.25, bulge=0.03 * k)
    # the forearm's elbow end is its "a" end; the upper arm's elbow end is its "b" end
    up_open_noelbow = _seg_shape(e2, s2, w_el, w_up, round_a=1.0, round_b=0.55, bulge=0.04 * k)[1]
    forearm_front = W[2] >= S[2]
    hand_behind = (spec or {}).get("hand_under", False) or (hd[2] < -0.45)
    if hand_behind:
        hand()
    if forearm_front:
        layers = [(up_closed, up_closed, s2, e2, w_el), (fo_closed, fo_open, e2, w2, w_el)]
    else:
        layers = [(fo_closed, fo_closed, e2, w2, w_el), (up_closed, up_open_noelbow, s2, e2, w_el)]
    for closed, outline, a, b_, w in layers:
        cv.drawPath(outline, stroke(lc, 0.05))
        cv.drawPath(closed, fill(scol))
        _shade_segment(cv, closed, a, b_, w, ssh, lx)
        cv.drawPath(outline, stroke(lc, 0.022, alpha=0.9))
    # folds gathering on the inside of a bent elbow (on the nearer segment)
    v1, v2 = s2 - e2, w2 - e2
    cosang = float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-9))
    if cosang > -0.85:
        inner = (v1 / (np.linalg.norm(v1) + 1e-9) + v2 / (np.linalg.norm(v2) + 1e-9))
        inner = inner / (np.linalg.norm(inner) + 1e-9)
        cv.save()
        cv.clipPath(layers[1][0], skia.ClipOp.kIntersect, True)
        for t_ in (-0.16, 0.0, 0.16):
            base = e2 + inner * (0.18 + t_)
            perp = np.array([-inner[1], inner[0]])
            pts = [tuple(base - perp * 0.28), tuple(base + inner * 0.06), tuple(base + perp * 0.28)]
            cv.drawPath(spline(pts, closed=False), stroke(ssh, 0.035, alpha=0.75))
        cv.restore()
    # cuff opening (dark inside)
    dx, dy = w2[0] - e2[0], w2[1] - e2[1]
    nn = math.hypot(dx, dy) + 1e-9
    nx_, ny_ = -dy / nn, dx / nn
    cw = w_cuff * 0.5
    cuff = spline([(w2[0] + nx_ * cw, w2[1] + ny_ * cw), (w2[0] + dx / nn * 0.10, w2[1] + dy / nn * 0.10), (w2[0] - nx_ * cw, w2[1] - ny_ * cw),
                   (w2[0] - dx / nn * 0.06, w2[1] - dy / nn * 0.06)], closed=True)
    cv.drawPath(cuff, fill(mix(ssh, "#000000", 0.35), alpha=0.85))
    cv.drawPath(cuff, stroke(lc, 0.02, alpha=0.8))
    if not hand_behind:
        hand()
    return E, W


def make_arms(arm_style=None):
    """Arms painter for Character.draw; P['arm_l'] / P['arm_r'] hold gesture specs (None = at rest).
    Within a layer the arm whose forearm is further from the viewer is drawn first."""
    arm_style = arm_style or {}

    def arms(cv, st, P, layer):
        items = []
        for side, key in ((-1, "arm_l"), (1, "arm_r")):
            spec = P.get(key)
            if (spec or {}).get("layer", "body") != layer:
                continue
            _, E, W = arm_geometry(st, P, side, spec)
            depth = float(E[2] + W[2]) + (5.0 if (spec or {}).get("over") else 0.0)
            items.append((depth, side, spec))
        for _, side, spec in sorted(items, key=lambda it: it[0]):
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
