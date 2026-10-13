"""Full-body parts: 3D-IK arms with natural elbows and wrists, detailed hands,
lower legs with sandaled feet, and ground contact shadows.

Body units: origin at the neck base, y down, z toward the viewer. A standing
adult is about 7 heads tall: shoulders ~0.5, elbow ~3.8, waist ~4.4,
wrist ~6.7, knee ~10.8, ankle ~16.3, sole ~16.9.
"""
import math

import numpy as np
import skia

from gfx import ellipse, fill, hexc, lin_grad, mix, sample_spline, spline, stroke, tapered

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
    t = P["t"]
    # resting arms hang against the body but are never frozen: they sway a little with the
    # weight shifts and breathing
    sway = 0.05 * math.sin(t * 0.9 + side) + 0.03 * math.sin(t * 0.37 + 2.0 * side)
    swing = 0.06 * math.sin(t * 0.6 + 1.3 * side)
    return np.array([S[0] + side * 0.22 + sway, S[1] + (l1 + l2) * 0.955 - 0.03 * P["breath"], 0.45 + swing])


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
# A hand is modelled in 3D in its own frame, in units of hand length with the wrist at the
# origin: x across the hand toward the thumb, y along it toward the fingertips, z out of the
# back of the hand. Fingers are chains of capsules bent at their knuckles, the thumb is a
# curved chain that can reach across the palm or over a held object, and the palm is a thin
# slab. Everything is projected through the slightly raised camera and drawn back to front,
# so a curled finger, a thumb wrapped over bread or a fingertip behind the palm is drawn
# exactly where it would be seen.
HAND_POSES = {
    # finger curls (index, middle, ring, pinky: 0 straight .. 1 tight fist), finger spread,
    # extra knuckle bend (deg), thumb tip position (hand frame)
    "open": dict(curl=(0.05, 0.05, 0.08, 0.12), spread=0.75, mcp=0.0, thumb=(0.39, 0.37, -0.08)),
    "relaxed": dict(curl=(0.26, 0.32, 0.38, 0.44), spread=0.35, mcp=4.0, thumb=(0.27, 0.41, -0.16)),
    "flat": dict(curl=(0.01, 0.01, 0.02, 0.03), spread=0.06, mcp=0.0, thumb=(0.175, 0.46, -0.08)),
    "soft": dict(curl=(0.10, 0.13, 0.16, 0.20), spread=0.14, mcp=3.0, thumb=(0.175, 0.43, -0.07)),
    "point": dict(curl=(0.0, 0.93, 0.96, 0.98), spread=0.12, mcp=0.0, thumb=(0.035, 0.43, -0.265)),
    "hold": dict(curl=(0.24, 0.27, 0.30, 0.33), spread=0.22, mcp=14.0, thumb=(0.10, 0.57, -0.25)),
    "cup": dict(curl=(0.20, 0.22, 0.25, 0.28), spread=0.12, mcp=8.0, thumb=(0.25, 0.46, -0.15)),
    "fist": dict(curl=(0.97, 0.99, 1.0, 1.0), spread=0.0, mcp=0.0, thumb=(0.0, 0.41, -0.275)),
}

FINGERS = [  # knuckle (x, y), phalanx lengths, radii at knuckle / middle joint / end joint / tip, spread (deg)
    ((0.142, 0.468), (0.192, 0.116, 0.084), (0.050, 0.044, 0.039, 0.034), 7.0),
    ((0.048, 0.497), (0.212, 0.132, 0.090), (0.052, 0.046, 0.040, 0.035), 1.5),
    ((-0.046, 0.487), (0.198, 0.124, 0.086), (0.049, 0.043, 0.038, 0.033), -4.0),
    ((-0.136, 0.452), (0.155, 0.094, 0.076), (0.043, 0.038, 0.034, 0.030), -10.0),
]
THUMB_BASE = (0.125, 0.085, -0.035)
THUMB_LENS = (0.205, 0.150, 0.118)
THUMB_RADII = (0.078, 0.056, 0.048, 0.042)
PALM_OUTLINE = [(-0.150, 0.0), (-0.182, 0.10), (-0.192, 0.26), (-0.186, 0.40), (-0.160, 0.452), (-0.095, 0.488),
                (0.0, 0.505), (0.095, 0.495), (0.160, 0.466), (0.188, 0.40), (0.190, 0.26), (0.176, 0.10), (0.140, 0.0)]
PALM_Z = (0.035, -0.065)  # back and palm faces of the palm slab
KNUCKLE_Z = -0.015


def _hand_pose(name, name_b=None, t=0.0):
    A = HAND_POSES.get(name, HAND_POSES["relaxed"])
    B = HAND_POSES.get(name_b or name, A)

    def lerp(a, b):
        if isinstance(a, tuple):
            return tuple(x + (y - x) * t for x, y in zip(a, b))
        return a + (b - a) * t

    return {k: lerp(A[k], B[k]) for k in A}


def _arc_chain(base, tip, lens, bulge_ref):
    """Joint positions of a chain of segments `lens` from `base` to `tip`, bent along one circular
    arc that bulges toward `bulge_ref`. Returns (joints, outward normal at each joint)."""
    base, tip = np.asarray(base, float), np.asarray(tip, float)
    c = tip - base
    cl = float(np.linalg.norm(c))
    u = c / (cl + 1e-9)
    s = float(sum(lens))
    ref = np.asarray(bulge_ref, float)
    b = ref - np.dot(ref, u) * u
    b = b / (np.linalg.norm(b) + 1e-9)
    if cl >= s * 0.9995:
        pts = [base]
        for L in lens:
            pts.append(pts[-1] + u * L)
        return pts, [b] * len(pts)
    ratio = s / cl
    lo, hi = 1e-4, 2 * math.pi - 1e-3
    for _ in range(60):
        th = 0.5 * (lo + hi)
        if (th / 2) / math.sin(th / 2) < ratio:
            lo = th
        else:
            hi = th
    th = 0.5 * (lo + hi)
    R = s / th
    center = (base + tip) / 2 - b * R * math.cos(th / 2)
    e1 = -u * math.sin(th / 2) + b * math.cos(th / 2)
    e2 = u * math.cos(th / 2) + b * math.sin(th / 2)
    pts, nrm = [], []
    acc = 0.0
    for L in (0.0,) + tuple(lens):
        acc += L
        a = acc / R
        p = center + R * (math.cos(a) * e1 + math.sin(a) * e2)
        pts.append(p)
        nrm.append((p - center) / R)
    return pts, nrm


def hand_local(pose, pose_b=None, pose_t=0.0):
    """3D joints of a hand pose in the hand frame."""
    hp = _hand_pose(pose, pose_b, pose_t)
    fingers = []
    for k, ((bx, by), lens, radii, spr) in enumerate(FINGERS):
        c = hp["curl"][k]
        a = math.radians(spr * hp["spread"])
        flex = [min(c * 80.0 + hp["mcp"] * min(1.0, c * 4.0 + 0.3), 92.0), min(c * 100.0, 108.0), min(c * 66.0, 74.0)]
        joints = [np.array([bx, by, KNUCKLE_Z])]
        dorsal = []
        phi = 0.0
        for L, f in zip(lens, flex):
            phi += math.radians(f)
            d = np.array([math.sin(a) * math.cos(phi), math.cos(a) * math.cos(phi), -math.sin(phi)])
            joints.append(joints[-1] + d * L)
            dorsal.append(np.array([math.sin(a) * math.sin(phi), math.cos(a) * math.sin(phi), math.cos(phi)]))
        fingers.append(dict(joints=joints, radii=radii, flex=flex, dorsal=dorsal))
    tpts, tn = _arc_chain(THUMB_BASE, hp["thumb"], THUMB_LENS, (0.75, -0.55, 0.25))
    thumb = dict(joints=tpts, radii=THUMB_RADII, dorsal=tn[1:])
    cavg = sum(hp["curl"]) / 4.0
    grip = np.array([0.03, 0.55 + 0.08 * min(cavg, 0.6), -0.10 - 0.14 * min(cavg * 2.0, 1.0)])
    return dict(fingers=fingers, thumb=thumb, grip=grip)


def _hull(pts):
    pts = sorted(set((round(p[0], 6), round(p[1], 6)) for p in pts))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def _capsule2d(a, b, ra, rb):
    """Closed outline of a 2D capsule (two circles joined by their outer tangents)."""
    ax, ay = float(a[0]), float(a[1])
    bx, by = float(b[0]), float(b[1])
    dx, dy = bx - ax, by - ay
    d = math.hypot(dx, dy)
    p = skia.Path()
    if d <= abs(ra - rb) + 1e-6:
        cx, cy, r = (ax, ay, ra) if ra >= rb else (bx, by, rb)
        p.addCircle(cx, cy, r)
        return p
    th = math.atan2(dy, dx)
    al = math.asin(max(-1.0, min(1.0, (ra - rb) / d)))
    n1 = th + math.pi / 2 + al
    n2 = th - math.pi / 2 - al
    p.moveTo(ax + ra * math.cos(n1), ay + ra * math.sin(n1))
    p.lineTo(bx + rb * math.cos(n1), by + rb * math.sin(n1))
    p.arcTo(skia.Rect.MakeLTRB(bx - rb, by - rb, bx + rb, by + rb), math.degrees(n1), -math.degrees(math.pi + 2 * al), False)
    p.lineTo(ax + ra * math.cos(n2), ay + ra * math.sin(n2))
    p.arcTo(skia.Rect.MakeLTRB(ax - ra, ay - ra, ax + ra, ay + ra), math.degrees(n2), -math.degrees(math.pi - 2 * al), False)
    p.close()
    return p


def _union(paths):
    out = None
    for p in paths:
        if out is None:
            out = p
            continue
        merged = None
        for eps in (0.0, 1e-4, -2.3e-4):
            q = skia.Path(p)
            if eps:
                q.offset(eps, eps * 0.7)
            try:
                merged = skia.Op(out, q, skia.PathOp.kUnion_PathOp)
                break
            except RuntimeError:
                continue
        if merged is None:  # PathOps gave up: overlapping contours still fill the same shape
            merged = skia.Path(out)
            merged.addPath(p)
        out = merged
    return out if out is not None else skia.Path()


def hand_frame_vectors(hd, spec, side):
    """(thumb, along, back-of-hand) unit vectors of a hand pointing along hd."""
    n, t = hand_frame(hd, spec, side)
    return t, np.asarray(hd, float) / (np.linalg.norm(hd) + 1e-9), -n


def _proj(o):
    """Body-space offset -> (screen dx, screen dy, depth toward the camera)."""
    return float(o[0]), float(o[1] * CAM_DIR[2] - o[2] * CAM_DIR[1]), float(np.dot(o, CAM_DIR))


def draw_hand3d(cv, st, geo, wrist, T3, D3, B3, L, light_x=-0.7, prop=None):
    """Draw a hand. geo from hand_local; wrist: 2D wrist point; T3/D3/B3: 3D thumb, along and
    back-of-hand directions; L: hand length (body units); prop: optional dict(draw=fn(cv, x, y))
    for an object held in the hand, drawn between the parts behind it and those in front."""
    lc = st.get("line", "#2a1a14")
    skin, sh = st["skin"], st["skin_sh"]
    M = np.stack([T3, D3, B3], axis=1) * L  # local -> body offset

    def P2(p):
        x, y, z = _proj(M @ np.asarray(p, float))
        return (wrist[0] + x, wrist[1] + y), z

    back_vis = float(np.dot(B3, CAM_DIR))  # > 0: the back of the hand faces the camera
    vis = 1.0 if back_vis >= 0 else -1.0
    edge = abs(back_vis) < 0.12
    zc = 0.5 * (PALM_Z[0] + PALM_Z[1])

    def behind(zloc):
        return (not edge) and (zloc - zc) * vis < -0.012

    parts = []
    # palm slab
    pp = []
    for z in PALM_Z:
        for (x, y) in PALM_OUTLINE:
            pp.append(P2((x * (1.0 if z > 0 else 0.95), y, z))[0])
    hull = _hull(pp)
    palm_path = spline(hull, closed=True, tension=0.35)
    palm_depth = P2((0.0, 0.25, zc))[1]
    parts.append(dict(kind="palm", path=palm_path, depth=palm_depth, behind=False, base=None, caps=[]))
    # fingers: split each finger where a knuckle bends sharply, so a curled finger shows its folds
    for k, fg in enumerate(geo["fingers"]):
        J, R = fg["joints"], fg["radii"]
        groups, cur = [], [0]
        for i in range(1, 3):
            if fg["flex"][i] > 42.0:
                groups.append(cur)
                cur = [i]
            else:
                cur.append(i)
        groups.append(cur)
        for gi, g in enumerate(groups):
            caps = []
            for i in g:
                a2, za = P2(J[i])
                b2, zb = P2(J[i + 1])
                caps.append((a2, b2, R[i] * L, R[i + 1] * L, 0.5 * (za + zb)))
            path = _union([_capsule2d(c[0], c[1], c[2], c[3]) for c in caps])
            if gi == 0:
                zt = J[0][2] + 0.25 * (J[1][2] - J[0][2])
            else:
                zt = 0.5 * (J[g[0]][2] + J[g[-1] + 1][2])
            depth = float(np.mean([c[4] for c in caps]))
            parts.append(dict(kind="finger", k=k, path=path, depth=depth + 0.0005 * gi, behind=behind(zt),
                              base=(caps[0][0], caps[0][2]), caps=caps, idx=g))
    # thumb: the fleshy base (behind the palm when we see the back of the hand), then the digit
    tj, tr = geo["thumb"]["joints"], geo["thumb"]["radii"]
    for g in ([0], [1, 2]):
        caps = []
        for i in g:
            a2, za = P2(tj[i])
            b2, zb = P2(tj[i + 1])
            caps.append((a2, b2, tr[i] * L, tr[i + 1] * L, 0.5 * (za + zb)))
        path = _union([_capsule2d(c[0], c[1], c[2], c[3]) for c in caps])
        zt = 0.5 * (tj[g[0]][2] + tj[g[-1] + 1][2])
        parts.append(dict(kind="thumb", path=path, depth=float(np.mean([c[4] for c in caps])), behind=behind(zt),
                          base=(caps[0][0], caps[0][2]) if g[0] > 0 else None, caps=caps, idx=g))
    order = sorted([p for p in parts if p["behind"]], key=lambda p: p["depth"])
    order += [parts[0]]
    order += sorted([p for p in parts[1:] if not p["behind"]], key=lambda p: p["depth"])
    if prop is not None:
        g2, gz = P2(geo["grip"])
        item = dict(kind="prop", depth=gz, behind=behind(float(geo["grip"][2])), at=g2)
        if item["behind"]:
            idx = next((i for i, p in enumerate(order) if p["kind"] == "palm"), 0)
        else:
            idx = len(order)
            for i, p in enumerate(order):
                if p["kind"] != "palm" and not p["behind"] and p["depth"] > gz:
                    idx = i
                    break
        order.insert(idx, item)

    w_out = 0.052
    shade_dir = -1.0 if light_x > 0 else 1.0  # screen side of the cel shadow

    def underlay(items):
        for p in items:
            if p["kind"] != "prop":
                cv.drawPath(p["path"], stroke(lc, w_out))

    # One clean silhouette line around the whole hand; inside it the hand is modelled with tone,
    # not lines: no line where a finger or the thumb joins the palm, a soft shadow where one part
    # lies over another, and a faint edge only along the free side of an overlapping finger.
    underlay(order)
    palm_side_col = mix(skin, "#f3cfb2", 0.16) if back_vis < 0 else skin
    sh2 = st.get("skin_sh2", sh)
    drawn = skia.Path()
    for i, p in enumerate(order):
        if p["kind"] == "prop":
            prop["draw"](cv, p["at"][0], p["at"][1])
            cv.save()
            if not drawn.isEmpty():
                cv.clipPath(drawn, skia.ClipOp.kDifference, True)
            underlay(order[i + 1:])
            cv.restore()
            drawn.addPath(_prop_mask(p["at"], L))
            continue
        if p["kind"] == "palm":
            col = palm_side_col
        elif p["behind"]:
            col = mix(skin, sh, 0.24)  # fingers curling away behind the palm sit in its shade
        else:
            col = skin
        thenar = p["kind"] == "thumb" and p.get("idx") == [0]
        if p["kind"] != "palm" and not thenar and not drawn.isEmpty():
            # soft contact shadow on whatever this part lies over (none round the root of a finger,
            # which grows out of the hand rather than lying on it)
            cv.save()
            cv.clipPath(drawn, skia.ClipOp.kIntersect, True)
            if p.get("base") is not None:
                (bx_, by_), br_ = p["base"]
                root = skia.Path()
                root.addCircle(bx_, by_, br_ * 2.6)
                cv.clipPath(root, skia.ClipOp.kDifference, True)
            sp_ = skia.Path(p["path"])
            m_ = skia.Matrix()
            m_.setTranslate(-shade_dir * 0.012 * L, 0.018 * L)
            sp_.transform(m_)
            cv.drawPath(sp_, fill(sh2, alpha=0.22, blur=0.05 * L))
            cv.restore()
        cv.drawPath(p["path"], fill(col))
        cv.save()
        cv.clipPath(p["path"], skia.ClipOp.kIntersect, True)
        if p["kind"] == "palm":
            b = p["path"].getBounds()
            cx = b.centerX() + shade_dir * b.width() * 0.62
            cv.drawPath(ellipse(cx, b.centerY(), b.width() * 0.42, b.height() * 0.8), fill(sh, alpha=0.32, blur=0.05))
        else:
            for (a2, b2, ra, rb, _) in p["caps"]:
                dx, dy = b2[0] - a2[0], b2[1] - a2[1]
                n = math.hypot(dx, dy)
                if n < 1e-6:
                    continue
                nx, ny = -dy / n, dx / n
                if nx * shade_dir < 0:
                    nx, ny = -nx, -ny
                r = 0.5 * (ra + rb)
                cv.drawPath(spline([(a2[0] + nx * r * 0.85, a2[1] + ny * r * 0.85), (b2[0] + nx * r * 0.85, b2[1] + ny * r * 0.85)], closed=False),
                            stroke(sh, r * 0.9, alpha=0.34, blur=r * 0.25))
        cv.restore()
        if p["kind"] in ("finger", "thumb") and p.get("base") is not None and not drawn.isEmpty():
            # a faint edge where this part overlaps the hand behind it, fading out toward its base
            (bx, by), br = p["base"]
            a2, b2 = p["caps"][0][0], p["caps"][0][1]
            dx, dy = b2[0] - a2[0], b2[1] - a2[1]
            n = math.hypot(dx, dy)
            ux, uy = (dx / n, dy / n) if n > 1e-6 else (0.0, 1.0)
            fade = max(br * 2.2, 0.35 * n)
            ep = stroke(lc, 0.013, alpha=1.0, blur=0.003)
            ep.setShader(lin_grad((bx, by), (bx + ux * fade, by + uy * fade), [mix_a(lc, 0.0), mix_a(lc, 0.42)]))
            cv.save()
            cv.clipPath(drawn, skia.ClipOp.kIntersect, True)
            cv.drawPath(p["path"], ep)
            cv.restore()
        drawn.addPath(p["path"])
        # surface detail belonging to this part, drawn with it so anything in front still covers it
        _part_details(cv, st, geo, p, P2, M, back_vis, L)


def _prop_mask(at, L):
    """Rough area a held prop covers (so the parts over it cast their shadow on it too)."""
    m = skia.Path()
    m.addOval(skia.Rect.MakeLTRB(at[0] - 0.45 * L, at[1] - 0.3 * L, at[0] + 0.45 * L, at[1] + 0.25 * L))
    return m


def mix_a(col, a):
    """Colour tuple with alpha."""
    c = hexc(col) if isinstance(col, str) else col
    return (c[0], c[1], c[2], a)


def _part_details(cv, st, geo, p, P2, M, back_vis, L):
    skin, sh = st["skin"], st["skin_sh"]
    sh2 = st.get("skin_sh2", sh)
    if p["kind"] == "palm":
        _hand_details(cv, st, geo, P2, M, back_vis, L)
        return
    if p["kind"] == "finger":
        k = p["k"]
        fg = geo["fingers"][k]
        J, R, Dn = fg["joints"], fg["radii"], fg["dorsal"]
        if 0 in p["idx"] and back_vis > 0.12:
            # knuckles: a soft rise of light on each knuckle, a little shade in the valley beside it
            a = min(1.0, (back_vis - 0.12) / 0.35)
            cv.save()
            cv.clipPath(p["path"], skia.ClipOp.kIntersect, True)
            (kx, ky), _ = P2(J[0] + np.array([0.0, 0.0, R[0] * 0.85]))
            cv.drawPath(ellipse(kx, ky, R[0] * L * 0.6, R[0] * L * 0.4), fill(mix(skin, "#ffffff", 0.3), alpha=0.2 * a, blur=0.022 * L))
            cv.restore()
            if k < 3:
                nxt = geo["fingers"][k + 1]["joints"][0]
                (vx, vy), _ = P2((J[0] + nxt) / 2 + np.array([0.0, -0.015, R[0] * 0.5]))
                cv.drawPath(ellipse(vx, vy, R[0] * L * 0.35, R[0] * L * 0.55), fill(sh2, alpha=0.12 * a, blur=0.03 * L))
            if fg["flex"][1] < 35.0:
                # fine skin creases over the middle joint of a straightened finger
                cv.save()
                cv.clipPath(p["path"], skia.ClipOp.kIntersect, True)
                d = J[2] - J[1]
                d = d / (np.linalg.norm(d) + 1e-9)
                lat = np.cross(d, Dn[1])
                lat = lat / (np.linalg.norm(lat) + 1e-9)
                for off in (-0.012, 0.012):
                    c0 = J[1] + d * off + Dn[0] * R[1] * 0.9
                    pts = [P2(c0 + lat * R[1] * s_ * 0.55 + d * 0.006 * abs(s_))[0] for s_ in (-1, 0, 1)]
                    cv.drawPath(spline(pts, closed=False), stroke(sh2, 0.008 * L, alpha=0.24 * a, blur=0.004 * L))
                cv.restore()
        if 2 in p["idx"]:
            _nail(cv, st, P2, M, J[2], J[3], R[2], R[3], Dn[2], L, p["path"])
    elif p["kind"] == "thumb" and 2 in p["idx"]:
        tj, tn, tr = geo["thumb"]["joints"], geo["thumb"]["dorsal"], geo["thumb"]["radii"]
        _nail(cv, st, P2, M, tj[2], tj[3], tr[2], tr[3], tn[2], L, p["path"], wide=1.1)


def _hand_details(cv, st, geo, P2, M, back_vis, L):
    """Palm creases, drawn on the palm when it faces the camera."""
    sh = st["skin_sh"]
    sh2 = st.get("skin_sh2", sh)
    lw = 0.014
    if back_vis < -0.15:
        a = min(1.0, (-back_vis - 0.15) / 0.35)
        z = PALM_Z[1]
        for line, al in (([(-0.185, 0.36), (-0.06, 0.395), (0.10, 0.435)], 0.5),
                         ([(0.175, 0.305), (0.06, 0.285), (-0.11, 0.25)], 0.42),
                         ([(0.165, 0.33), (0.085, 0.24), (0.07, 0.12), (0.08, 0.035)], 0.42)):
            pts = [P2((x, y, z))[0] for x, y in line]
            cv.drawPath(spline(pts, closed=False), stroke(sh2, lw * 1.3, alpha=al * a * 0.8, blur=lw * 0.5))


def _nail(cv, st, P2, M, j0, j1, r0, r1, dorsal, L, clip, wide=1.0):
    """Fingernail: a plate that spans the width of the fingertip, with an arched cuticle and an
    arched free edge, wrapping over the curve of the finger (only where its back faces us)."""
    skin, sh = st["skin"], st["skin_sh"]
    dorsal = np.asarray(dorsal, float)
    dn = M @ dorsal
    dn = dn / (np.linalg.norm(dn) + 1e-9)
    v = float(np.dot(dn, CAM_DIR))
    if v < 0.08:
        return
    j0, j1 = np.asarray(j0, float), np.asarray(j1, float)
    d = j1 - j0
    dl = float(np.linalg.norm(d))
    if dl < 1e-6:
        return
    d = d / dl
    lat = np.cross(d, dorsal)
    lat = lat / (np.linalg.norm(lat) + 1e-9)
    r = r1
    ln = dl * 0.62 + r * 0.55          # nail length along the finger
    tip = j1 + d * r * 0.55            # free edge sits just short of the fingertip
    hw = r * 0.86 * wide               # it spans almost the whole width of the finger

    def surf(u, s):
        # point on the top of the finger: u back from the free edge, s across (-1..1)
        x = s * hw
        h = math.sqrt(max(r * r - x * x, 0.0))
        return tip - d * u + lat * x + dorsal * h * 1.01

    ring = []
    for s in np.linspace(-1, 1, 9):                       # free edge, arching toward the tip
        ring.append(surf(0.22 * ln * s * s, s))
    for s in np.linspace(1, -1, 9):                       # cuticle, arching toward the knuckle
        ring.append(surf(ln - 0.28 * ln * (1 - s * s), s))
    pts = [P2(q)[0] for q in ring]
    path = spline(pts, closed=True, corners=[0, 8, 9, 17], tension=0.4)
    a = min(1.0, (v - 0.08) / 0.3)
    cv.save()
    cv.clipPath(clip, skia.ClipOp.kIntersect, True)
    cv.drawPath(path, fill(mix(skin, "#f2d6c8", 0.45), alpha=0.8 * a, blur=0.002 * L))
    # pale free edge and a soft gloss
    edge = [P2(surf(0.1 * ln + 0.22 * ln * s * s, s))[0] for s in np.linspace(-0.9, 0.9, 7)]
    cv.drawPath(spline(edge, closed=False), stroke(mix(skin, "#ffffff", 0.6), 0.008 * L, alpha=0.6 * a))
    gl = [P2(surf(ln * u_, -0.35))[0] for u_ in (0.3, 0.55, 0.75)]
    cv.drawPath(spline(gl, closed=False), stroke("#ffffff", 0.007 * L, alpha=0.35 * a))
    cuticle = [P2(surf(ln - 0.28 * ln * (1 - s * s), s))[0] for s in np.linspace(-0.85, 0.85, 7)]
    cv.drawPath(spline(cuticle, closed=False), stroke(sh, 0.006 * L, alpha=0.35 * a))
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
    hm = (spec or {}).get("hand_dir_mix")
    if hm is not None:
        da, db, x = hm
        base = {k: v for k, v in spec.items() if k != "hand_dir_mix"}
        nat = None
        if da is None or db is None:
            nat = hand_direction(E, W, base, side, use_override=False)
        va = nat if da is None else np.asarray(da, float) / (np.linalg.norm(da) + 1e-9)
        vb = nat if db is None else np.asarray(db, float) / (np.linalg.norm(db) + 1e-9)
        c = float(np.clip(np.dot(va, vb), -1.0, 1.0))
        th = math.acos(c)
        xs = x * x * (3 - 2 * x)
        if th < 1e-4:
            return va
        d = (math.sin((1 - xs) * th) * va + math.sin(xs * th) * vb) / math.sin(th)
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
    cv.drawPath(tapered(sample_spline(band, n=6), w * 0.75, w * 0.75), fill(ssh, alpha=0.6, blur=w * 0.14))
    cv.restore()


def hand_anchor(st, P, side, spec, which="grip"):
    """2D point (body units, before the body lean) of a hand's grip (where a held object sits) or
    palm centre, computed exactly as draw_arm places the hand."""
    S, E, W = arm_geometry(st, P, side, spec)
    k = st.get("body_scale", 1.0)
    hd = hand_direction(E, W, spec, side)
    sx, sy, fore = hand_screen_dir(hd)
    hand_len = st.get("hand_len", 2.15) * (spec or {}).get("hand_scale", 1.0) * k
    wrist = (W[0] - sx * fore * 0.25, W[1] - sy * fore * 0.25)
    T3, D3, B3 = hand_frame_vectors(hd, spec, side)
    pose = (spec or {}).get("hand", "relaxed")
    geo = hand_local(pose, (spec or {}).get("hand_b"), (spec or {}).get("hand_t", 0.0))
    p = geo["grip"] if which == "grip" else np.array([0.0, 0.3, -0.03])
    M = np.stack([T3, D3, B3], axis=1) * hand_len
    x, y, _ = _proj(M @ p)
    return wrist[0] + x, wrist[1] + y


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
    hand_len = st.get("hand_len", 2.15) * (spec or {}).get("hand_scale", 1.0) * k
    pose = (spec or {}).get("hand", "relaxed")
    show_hand = pose != "none" and (spec or {}).get("hand_b") != "none" and hand_len > 0.05
    lx = P["light_x"]
    # wrist sits a little inside the cuff
    wrist = (w2[0] - sx * fore * 0.25, w2[1] - sy * fore * 0.25)
    prop = P.get("prop_l" if side < 0 else "prop_r")

    def hand():
        if show_hand:
            T3, D3, B3 = hand_frame_vectors(hd, spec, side)
            geo = hand_local(pose, (spec or {}).get("hand_b"), (spec or {}).get("hand_t", 0.0))
            draw_hand3d(cv, st, geo, wrist, T3, D3, B3, hand_len, light_x=lx, prop=prop)

    up_closed, up_open, _, _ = _seg_shape(s2, e2, w_up, w_el, round_a=0.55, round_b=1.0, bulge=0.04 * k)
    fo_closed, fo_open, _, _ = _seg_shape(e2, w2, w_el, w_cuff, round_a=1.0, round_b=0.25, bulge=0.03 * k)
    forearm_front = W[2] >= S[2]
    hand_behind = (spec or {}).get("hand_under", False) or (hd[2] < -0.45)
    if hand_behind:
        hand()
    # The sleeve grows out of the robe at the shoulder: the upper arm has no outline round its
    # shoulder end, and its side lines fade in a little way down, so the shoulder reads as one
    # piece of cloth with the body rather than a separate tube.
    fade = (s2, s2 + (e2 - s2) * 0.38)
    if forearm_front:
        layers = [(up_closed, up_open, s2, e2, w_el, fade), (fo_closed, fo_open, e2, w2, w_el, None)]
    else:
        layers = [(fo_closed, fo_closed, e2, w2, w_el, None), (up_closed, up_open, s2, e2, w_el, fade)]
    for closed, outline, a, b_, w, fd in layers:
        under = stroke(lc, 0.05)
        line = stroke(lc, 0.022, alpha=0.9)
        if fd is not None:
            under.setShader(lin_grad(tuple(fd[0]), tuple(fd[1]), [mix_a(lc, 0.0), mix_a(lc, 1.0)]))
            line.setShader(lin_grad(tuple(fd[0]), tuple(fd[1]), [mix_a(lc, 0.0), mix_a(lc, 0.9)]))
        cv.drawPath(outline, under)
        cv.drawPath(closed, fill(scol))
        _shade_segment(cv, closed, a, b_, w, ssh, lx)
        cv.drawPath(outline, line)
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
        if show_hand and hd[2] < 0.35:
            # the end of the sleeve laps over the wrist, so the hand always comes out of the sleeve
            c0 = w2 + (e2 - w2) / (np.linalg.norm(e2 - w2) + 1e-9) * 0.42 * k
            wc0 = w_cuff - (w_cuff - w_el) * 0.42 * k / (np.linalg.norm(w2 - e2) + 1e-9)
            band, band_open, _, _ = _seg_shape(c0, w2, wc0, w_cuff, round_a=1.0, round_b=0.25, bulge=0.0)
            cv.drawPath(band_open, stroke(lc, 0.05))
            cv.drawPath(band, fill(scol))
            _shade_segment(cv, band, c0, w2, w_cuff, ssh, lx)
            cv.drawPath(band_open, stroke(lc, 0.022, alpha=0.9))
    return E, W


def make_arms(arm_style=None):
    """Arms painter for Character.draw; P['arm_l'] / P['arm_r'] hold gesture specs (None = at rest).
    Within a layer the arm whose forearm is further from the viewer is drawn first."""
    arm_style = arm_style or {}

    def arms(cv, st, P, layer, drape=None):
        """drape: optional (side, painter) for cloth lying over one shoulder (a mantle's fold). It is
        drawn right after that side's arm, and the other arm comes after it, so a hand moving in
        front of the chest is never hidden under the cloth on the opposite shoulder."""
        items = []
        for side, key in ((-1, "arm_l"), (1, "arm_r")):
            spec = P.get(key)
            if (spec or {}).get("layer", "body") != layer:
                continue
            _, E, W = arm_geometry(st, P, side, spec)
            depth = float(E[2] + W[2]) + (5.0 if (spec or {}).get("over") else 0.0)
            items.append((depth, side, spec))
        items.sort(key=lambda it: it[0])
        if drape is not None:
            dside, painter = drape
            mine = [it for it in items if it[1] == dside]
            others = [it for it in items if it[1] != dside]
            for _, side, spec in mine:
                draw_arm(cv, st, P, side, spec, arm_style.get(side, {}))
            painter()
            items = others
        for _, side, spec in items:
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
        _draw_foot(cv, st, ank, side, k, sandal, P["light_x"], by)


def _draw_foot(cv, st, ank, side, k, sandal, light_x, by=0.0):
    """A sandaled foot seen from the front and a little above: instep, five toes (the big toe on the
    inside), a leather sole with visible thickness, a toe loop, straps crossing the instep and a
    tie round the ankle."""
    lc = st.get("line", "#2a1a14")
    skin, sh = st["skin"], st["skin_sh"]
    sh2 = st.get("skin_sh2", sh)
    ax, ay = ank
    turn = side * 0.22 + by * 0.9  # toes turned a little outward, and toward where the body faces
    inner = -side               # the big toe is on the inner side of each foot

    def P_(u, v):
        # u across the foot (-1 inner .. +1 outer, mirrored per foot), v down the foot (0 ankle .. 1 toe tips)
        x = ax + (-inner * u) * (0.20 + 0.13 * v) * k + turn * v * k
        return (x, ay + v * 0.74 * k)

    # sole: a leather slab a little larger than the foot, its front edge showing its thickness
    rim = [P_(-1.25, 0.18), P_(-1.3, 0.62), P_(-1.05, 1.06), P_(0.0, 1.13), P_(1.05, 1.04), P_(1.3, 0.6), P_(1.22, 0.18)]
    sole_top = spline(rim, closed=True, tension=0.5)
    edge = [(x, y + 0.075 * k) for x, y in rim[1:6]]
    sole_side = spline(rim[1:6] + edge[::-1], closed=True, corners=[0, 4, 5, 9], tension=0.4)
    cv.drawPath(sole_side, fill(mix(sandal, "#000000", 0.35)))
    cv.drawPath(sole_side, stroke(lc, 0.02))
    cv.drawPath(sole_top, fill(mix(sandal, "#ffffff", 0.18)))
    cv.drawPath(sole_top, stroke(lc, 0.02))
    # foot: narrow at the ankle, widening to the ball, with five rounded toes along the front
    toes = [(-0.74, 0.93, 0.27, 0.085), (-0.26, 0.92, 0.19, 0.07), (0.12, 0.895, 0.17, 0.066), (0.47, 0.865, 0.155, 0.062), (0.80, 0.82, 0.14, 0.058)]
    body_pts_ = [P_(-0.95, 0.0), P_(-1.0, 0.35), P_(-1.06, 0.7), P_(-0.9, 0.9), P_(0.0, 0.9), P_(0.95, 0.82), P_(1.06, 0.62), P_(1.0, 0.35), P_(0.95, 0.0)]
    parts = [spline(body_pts_, closed=True, tension=0.45)]
    for (u, v, w, h) in toes:
        tx, ty = P_(u, v)
        parts.append(ellipse(tx, ty, (0.20 + 0.13 * v) * k * w * 1.05, h * k))
    for p_ in parts:
        cv.drawPath(p_, stroke(lc, 0.045))
    foot = skia.Path()
    for p_ in parts:
        cv.drawPath(p_, fill(skin))
        foot.addPath(p_)
    cv.save()
    cv.clipPath(foot, skia.ClipOp.kIntersect, True)
    sx = 1.0 if light_x < 0 else -1.0
    cv.drawPath(ellipse(ax + sx * 0.28 * k, ay + 0.4 * k, 0.2 * k, 0.6 * k), fill(sh, alpha=0.55, blur=0.06 * k))
    cv.drawPath(ellipse(ax + turn * 0.4 * k, ay + 0.3 * k, 0.12 * k, 0.28 * k), fill(mix(skin, "#ffffff", 0.3), alpha=0.35, blur=0.05 * k))
    # soft creases between the toes, and toenails
    for i in range(4):
        u = (toes[i][0] + toes[i + 1][0]) / 2
        v = (toes[i][1] + toes[i + 1][1]) / 2
        cv.drawPath(spline([P_(u, v - 0.06), P_(u, v + 0.04)], closed=False), stroke(sh2, 0.016 * k, alpha=0.55))
    for (u, v, w, h) in toes[:4]:
        nx, ny = P_(u, v + 0.012)
        cv.drawPath(ellipse(nx, ny, (0.2 + 0.13 * v) * k * w * 0.55, h * k * 0.5), fill(mix(skin, "#f2d6c8", 0.5), alpha=0.8))
    cv.restore()
    # straps: a loop round the big toe, two straps crossing the instep, a tie round the ankle
    sc = sandal
    hi = mix(sandal, "#ffffff", 0.25)

    def strap(pts, w):
        path = tapered(sample_spline(pts, n=14), w, w, wmid=w)
        cv.drawPath(path, stroke(lc, 0.035))
        cv.drawPath(path, fill(sc))
        cv.drawPath(spline([(x, y - w * 0.25) for x, y in pts], closed=False), stroke(hi, w * 0.3, alpha=0.6))

    sw_ = 0.07 * k
    strap([P_(-1.15, 0.62), P_(-0.7, 0.68), P_(-0.45, 0.78)], sw_)            # toe loop
    strap([P_(-1.05, 0.45), P_(-0.1, 0.36), P_(1.08, 0.18)], sw_)              # across the instep
    strap([P_(1.08, 0.48), P_(0.1, 0.38), P_(-1.0, 0.16)], sw_)
    strap([P_(-1.0, 0.0), P_(0.0, 0.06), P_(1.0, 0.0)], sw_ * 1.05)           # round the ankle
    kx, ky = P_(-0.95, 0.02)
    cv.drawPath(ellipse(kx, ky, 0.06 * k, 0.05 * k), fill(sc))
    cv.drawPath(ellipse(kx, ky, 0.06 * k, 0.05 * k), stroke(lc, 0.02))
