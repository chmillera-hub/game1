"""Arms (2-bone IK) with robe sleeves, and stylized hands in a few poses."""
import math

import numpy as np
import skia

from gfx import ellipse, fill, sample_spline, spline, stroke, tapered


def ik(S, T, l1, l2, side):
    sx, sy = S
    tx, ty = T
    dx, dy = tx - sx, ty - sy
    d = math.hypot(dx, dy)
    d = min(max(d, abs(l1 - l2) + 1e-3), l1 + l2 - 1e-3)
    a = math.atan2(dy, dx)
    cos_t = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)
    t = math.acos(max(-1.0, min(1.0, cos_t)))
    cands = []
    for sgn in (1, -1):
        ang = a + sgn * t
        E = (sx + l1 * math.cos(ang), sy + l1 * math.sin(ang))
        cands.append(E)
    # elbow prefers outward and down
    E = max(cands, key=lambda e: e[1] * 0.6 + side * e[0])
    W = (sx + dx / max(math.hypot(dx, dy), 1e-6) * d, sy + dy / max(math.hypot(dx, dy), 1e-6) * d)
    return E, W


HAND_POSES = {
    # finger (curl 0..1) for index, middle, ring, pinky; thumb angle (deg), spread
    "open": dict(curl=(0.05, 0.0, 0.05, 0.1), thumb=40, spread=7),
    "relaxed": dict(curl=(0.35, 0.45, 0.5, 0.55), thumb=25, spread=3),
    "fist": dict(curl=(1.0, 1.0, 1.0, 1.0), thumb=10, spread=0),
    "point": dict(curl=(0.0, 1.0, 1.0, 1.0), thumb=15, spread=2),
    "hold": dict(curl=(0.6, 0.65, 0.7, 0.75), thumb=55, spread=2),
    "flat": dict(curl=(0.0, 0.0, 0.0, 0.0), thumb=12, spread=1),
}


def _lerp_pose(a, b, t):
    A, B = HAND_POSES[a], HAND_POSES[b]
    return dict(curl=tuple(x + (y - x) * t for x, y in zip(A["curl"], B["curl"])),
                thumb=A["thumb"] + (B["thumb"] - A["thumb"]) * t,
                spread=A["spread"] + (B["spread"] - A["spread"]) * t)


def draw_hand(cv, st, pose, x, y, ang_deg, scale=1.0, thumb_side=1, palm=True, pose_b=None, pose_t=0.0):
    """Hand with wrist at (x, y) pointing along ang_deg (0 = down)."""
    hp = _lerp_pose(pose, pose_b or pose, pose_t)
    lc = st.get("line", "#2a1a14")
    skin, sh = st["skin"], st["skin_sh"]
    cv.save()
    cv.translate(x, y)
    cv.rotate(ang_deg)
    cv.scale(scale, scale)
    ts = thumb_side
    # palm
    palm_pts = [(-0.17, 0.0), (0.17, 0.0), (0.21, 0.30), (0.20, 0.42), (-0.20, 0.42), (-0.21, 0.30)]
    palm_path = spline(palm_pts, closed=True, corners=[0, 1], tension=0.5)
    # thumb
    ta = math.radians(hp["thumb"])
    tb = (ts * 0.17, 0.10)
    t1 = (tb[0] + ts * math.sin(ta) * 0.17, tb[1] + math.cos(ta) * 0.17)
    t2 = (t1[0] + ts * math.sin(ta * 0.6) * 0.14, t1[1] + math.cos(ta * 0.6) * 0.14)
    thumb = tapered([tb, t1, t2], 0.15, 0.085, wmid=0.12)
    # fingers
    xs = [-0.15, -0.05, 0.05, 0.15]
    lens = [0.30, 0.33, 0.31, 0.25]
    order = [0, 1, 2, 3] if ts > 0 else [3, 2, 1, 0]
    finger_paths = []
    for i, k in enumerate(order):
        c = hp["curl"][i]
        fx = xs[k] * (1 + hp["spread"] * 0.03)
        base = (fx, 0.40)
        sp = math.radians((xs[k] / 0.15) * hp["spread"])
        L = lens[i] * (1 - 0.45 * c)
        p1 = (base[0] + math.sin(sp) * L * 0.55, base[1] + math.cos(sp) * L * 0.55)
        bend = c * 1.6
        p2 = (p1[0] + math.sin(sp) * L * 0.45 * math.cos(bend), p1[1] + L * 0.45 * math.cos(bend) - L * 0.3 * math.sin(bend) * 0.5)
        if c > 0.6:
            p2 = (p1[0], p1[1] - 0.04 * (c - 0.6))
        finger_paths.append(tapered([base, p1, p2], 0.095, 0.075, wmid=0.09))
    # outline underlay: stroke every part, then fill them all, so only the outer silhouette shows
    parts = finger_paths + [palm_path, thumb]
    for p in parts:
        cv.drawPath(p, stroke(lc, 0.05))
    for p in parts:
        cv.drawPath(p, fill(skin))
    cv.drawPath(palm_path, fill(sh, alpha=0.18))
    # subtle finger separations (only between extended fingers)
    for i, fp in enumerate(finger_paths[1:3]):
        b0 = finger_paths[i + 1].getBounds()
    for k in (-0.05, 0.05):
        cv.drawPath(spline([(k * 1.0, 0.43), (k * 1.05, 0.55)], closed=False), stroke(sh, 0.014, alpha=0.7))
    cv.drawPath(thumb, stroke(sh, 0.012, alpha=0.4))
    if palm:
        cv.drawPath(spline([(-0.1, 0.18), (0.0, 0.26), (0.12, 0.22)], closed=False), stroke(sh, 0.014, alpha=0.5))
    cv.restore()


def draw_arm(cv, st, P, side, spec):
    """side +1 = screen-right arm. spec: target (x,y) wrist in body units, hand pose etc."""
    sw = st.get("shoulder_w", 1.75)
    up = -0.05 * P["breath"] - 0.12 * P["shrug"]
    S = (side * sw * 0.86, 0.55 + up)
    l1 = st.get("upper_arm", 1.62)
    l2 = st.get("forearm", 1.62)
    T = spec["target"]
    E, W = ik(S, T, l1, l2, side)
    lc = st.get("line", "#2a1a14")
    scol = spec.get("sleeve", st.get("sleeve", "#efe5d3"))
    ssh = spec.get("sleeve_sh", st.get("sleeve_sh", "#c9b89c"))
    # hand first if it is behind the sleeve opening (pointing back toward the body)
    hand_ang = spec.get("hand_ang", None)
    fa = math.degrees(math.atan2(W[0] - E[0], W[1] - E[1]))
    if hand_ang is None:
        hand_ang = -fa
    hs = spec.get("hand_scale", 1.0) * st.get("hand_scale", 1.45)

    def hand():
        if spec.get("hand") == "none" or spec.get("hand_b") == "none":
            return
        if hs <= 0.02:
            return
        draw_hand(cv, st, spec.get("hand", "relaxed"), W[0], W[1], hand_ang, hs,
                  thumb_side=spec.get("thumb", -side), pose_b=spec.get("hand_b"), pose_t=spec.get("hand_t", 0.0))

    if spec.get("hand_under", False):
        hand()
    # sleeve: upper arm + forearm as a tapered tube, widening at the cuff
    pts = [S, E, W]
    sm = sample_spline(pts, n=16)
    sleeve = tapered(sm, st.get("sleeve_w0", 0.74), st.get("sleeve_w1", 0.86), wmid=st.get("sleeve_wm", 0.66))
    cv.drawPath(sleeve, fill(scol))
    cv.save()
    cv.clipPath(sleeve, skia.ClipOp.kIntersect, True)
    lx = P["light_x"]
    off = 0.18 if lx < 0 else -0.18
    sh_pts = [(x + off, y + 0.05) for x, y in sm]
    cv.drawPath(tapered(sh_pts, 0.3, 0.4, wmid=0.3), fill(ssh, alpha=0.8))
    # fold lines at the elbow
    ex, ey = E
    for k in (-1, 1):
        cv.drawPath(spline([(ex + k * 0.1, ey - 0.2), (ex + k * 0.04, ey), (ex + k * 0.12, ey + 0.2)], closed=False), stroke(ssh, 0.03, alpha=0.9))
    cv.restore()
    cv.drawPath(sleeve, stroke(lc, 0.022))
    # cuff opening
    d = (W[0] - E[0], W[1] - E[1])
    n = math.hypot(*d) + 1e-6
    nx, ny = -d[1] / n, d[0] / n
    cw = st.get("sleeve_w1", 0.86) * 0.5
    cv.drawPath(spline([(W[0] + nx * cw, W[1] + ny * cw), (W[0] + d[0] / n * 0.05, W[1] + d[1] / n * 0.05), (W[0] - nx * cw, W[1] - ny * cw)], closed=False), stroke(ssh, 0.05))
    if not spec.get("hand_under", False):
        hand()
    return E, W


def draw_rest_sleeve(cv, st, P, side, sty):
    """Arm hanging at the side inside a loose sleeve (part of the silhouette)."""
    sw = st.get("shoulder_w", 1.75)
    by = P["byaw"] / 60.0
    far = 1 - 0.18 * abs(by) if side * by < 0 else 1.0
    up = -0.05 * P["breath"] - 0.12 * P["shrug"]
    s = side * far
    lc = st.get("line", "#2a1a14")
    scol = sty.get("sleeve", st.get("sleeve", "#efe5d3"))
    ssh = sty.get("sleeve_sh", st.get("sleeve_sh", "#c9b89c"))
    pts = [(s * sw * 0.80, 0.22 + up), (s * sw * 1.02, 0.40 + up), (s * sw * 1.17, 1.0), (s * sw * 1.20, 2.4),
           (s * sw * 1.24, 4.2), (s * sw * 0.86, 4.25), (s * sw * 0.84, 2.4), (s * sw * 0.86, 1.2)]
    path = spline(pts, closed=True, corners=[4, 5], tension=0.5)
    from gfx import lin_grad, mix
    cv.drawPath(path, fill(scol, shader=lin_grad((0, 0.2), (0, 4.3), [mix(scol, "#ffffff", 0.12), scol, mix(scol, ssh, 0.4)], [0.0, 0.4, 1.0])))
    cv.save()
    cv.clipPath(path, skia.ClipOp.kIntersect, True)
    lx = P["light_x"]
    shade_side = 1 if lx < 0 else -1
    if shade_side == side:
        cv.drawPath(path, fill(ssh, alpha=0.75))
    else:
        cv.drawPath(spline([(s * sw * 0.80, 1.0), (s * sw * 0.98, 1.0), (s * sw * 1.0, 4.3), (s * sw * 0.8, 4.3)], closed=True), fill(ssh, alpha=0.7))
    for k in range(2):
        x0 = s * sw * (0.95 + 0.1 * k)
        cv.drawPath(tapered([(x0, 1.4 + 0.5 * k), (x0 + s * 0.03, 2.6 + 0.4 * k), (x0 - s * 0.02, 3.8)], 0.004, 0.006, wmid=0.035), fill(ssh, alpha=0.8))
    cv.restore()
    cv.drawPath(path, stroke(lc, 0.022))


def make_arms(arm_style=None):
    """Returns an arms painter for Character.draw: uses P['arm_l'] / P['arm_r'] specs."""

    def arms(cv, st, P, layer):
        for side, key in ((-1, "arm_l"), (1, "arm_r")):
            spec = P.get(key)
            if layer == "rest":
                if not spec or spec.get("rest_sleeve", False):
                    st2 = (arm_style or {}).get(side, {})
                    draw_rest_sleeve(cv, st, P, side, st2)
                continue
            if not spec:
                continue
            if spec.get("layer", "front") != layer:
                continue
            sp = dict(spec)
            if arm_style:
                st2 = arm_style.get(side, {})
                for k, v in st2.items():
                    sp.setdefault(k, v)
            draw_arm(cv, st, P, side, sp)

    return arms
