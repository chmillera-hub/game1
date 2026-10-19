"""s20a - "Posterity will serve him; future generations will be told about the Lord."

Night by a small campfire (sets.camp_night). A grandfather (ELDER) sits on a low boulder with an open
Psalm scroll across his lap, his right hand resting on it; in his left hand a lit clay oil lamp (fx.flame)
lights his beard and the scroll. A young boy (CHILD) sits on a stone at his side, turned towards him,
listening in awe. On "future generations will be told" the old man reaches the lamp across; the boy
cups both hands under it, takes it and draws it to his chest - the little flame now lights HIS face -
while the old man withdraws his hand to his knee and watches him with a quiet smile.
Fire in the left foreground (soft, out of focus), sparks rising, dark hills and stars behind, cool moon
rim from behind.

Lamp hand-off: the lamp carries two Child Of constraints (grandfather's wrist.L / boy's wrist.R) whose
inverse matrices are computed from the keyed pose states at the hand-off frame, then switched with
CONSTANT influence keys at that frame - so it sits in each hand exactly and never jumps.
Fire + sparks + flame flicker -> 24 fps (no interp).
"""
import math
import bpy
from mathutils import Vector, Matrix
from lib import core as C, sets as S, fx as FX, assets as A
from lib import characters as P

ARM_KEYS = ("clavicle", "shoulder", "upperarm", "lowerarm", "wrist", "finger", "metacarpal")


def _yaw_to(d):
    return math.atan2(d[0], -d[1])


def _find(sub):
    for o in bpy.data.objects:
        if sub in o.name:
            return o
    return None


def _ground_z(gnd, x, y):
    """Height of the camp ground mesh at (x, y) (object ray cast)."""
    if gnd is None:
        return 0.0
    mi = gnd.matrix_world.inverted()
    o = mi @ Vector((x, y, 5.0))
    d = (mi.to_3x3() @ Vector((0, 0, -1))).normalized()
    hit, loc, n, i = gnd.ray_cast(o, d)
    return (gnd.matrix_world @ loc).z if hit else 0.0


def _bones_for(St):
    return [n for n in St.names if n.startswith(ARM_KEYS)] + list(P.SPINE)


def _reset_fingers(St, s):
    for i in range(1, 6):
        for j in range(1, 4):
            n = "finger%d-%d.%s" % (i, j, s)
            if n in St.rot:
                St.rot[n] = Matrix.Identity(3)
    St._c.clear()


def arm_state(p, base, hands, lean=0.0, twist=0.0):
    """Copy of the static (seated) pose with arms IK'd to world targets.
    hands: {side: dict(T=world point (palm centre), pole=rig-space elbow dir, pron, flex, shape)}"""
    St = base.copy()
    if lean or twist:
        P._spine_bend(St, bend=lean, twist=twist)
    for s, h in hands.items():
        T = P._to_rig_space(p, h["T"])
        lat = 1.0 if s == "L" else -1.0
        pole = Vector(h.get("pole", (0.6 * lat, 0.3, -1.0)))
        _reset_fingers(St, s)
        P._arm_ik(St, s, T, pole, pron=h.get("pron", 0.0), flex=h.get("flex", 0.0), dev=h.get("dev", 0.0))
        P._hand(St, s, h.get("shape", "relaxed"))
    return St


def key_state(p, St, frames):
    names = _bones_for(St)
    for f in frames:
        St.write(frame=f, bones=names)


def bone_world(p, St, bone):
    return p.rig.matrix_world @ St.pm(bone)


def seat_under(p, seat, gz, back=0.03):
    """Fit a set boulder under a seated person's buttocks (top = lowest skinned point near the hips)."""
    import numpy as np
    p.update()
    mw = p.rig.matrix_world
    pts = P.lbs_points(p)
    W = np.array([tuple(mw @ Vector(q)) for q in pts[::2]])
    hip = (p.bone_world("upperleg01.L") + p.bone_world("upperleg01.R")) * 0.5
    d = np.hypot(W[:, 0] - hip.x, W[:, 1] - hip.y)
    m = (d < 0.13) & (W[:, 2] < hip.z)
    top = float(W[m, 2].min()) if m.any() else hip.z - 0.08
    if seat is None:
        return top
    seat.location.z = gz - 0.03
    bb = [seat.matrix_world.to_3x3() @ Vector(c) for c in seat.bound_box]
    hz = max(v.z for v in bb) - min(v.z for v in bb)
    seat.scale.z *= (top + 0.004 - (gz - 0.03)) / max(hz, 1e-3)
    fwd = (mw.to_3x3() @ Vector((0, -1, 0)))
    seat.location.x = hip.x - fwd.x * back
    seat.location.y = hip.y - fwd.y * back
    return top


def _hide_thighs(p):
    """Seated knees poked through the robe lap: hide the thigh/knee skin that the robe covers anyway."""
    from lib import wardrobe as W
    body = p.body
    gi = {g.index for g in body.vertex_groups
          if g.name.startswith(("upperleg01", "upperleg02", "lowerleg01", "pelvis"))}
    idx = [v.index for v in body.data.vertices if any(x.group in gi and x.weight > 0.25 for x in v.groups)]
    W.hide_body(p, idx)


def build(ctx):
    N = ctx.render_frames
    nf = ctx.nframes
    st = S.camp_night(ctx, fire_size=0.6, fire_energy=0.62, seed=41)
    gnd = _find("camp_ground")

    # ---------------- layout (fire at the origin, camera from -Y) ----------------
    g_pos = Vector((0.0, 0.95))
    c_pos = Vector((0.68, 0.64))
    g_fwd = Vector((0.5, -0.866))                   # grandfather turned towards camera-right (the boy)
    c_fwd = Vector((-0.5, -0.85)).normalized()     # boy turned towards him
    gz_g = _ground_z(gnd, g_pos.x, g_pos.y - 0.4)
    gz_c = _ground_z(gnd, c_pos.x - 0.15, c_pos.y - 0.25)

    # ---------------- people ----------------
    G = P.make_person("elder", "ELDER", pose=None, expression=None)
    G.rig.location = (g_pos.x, g_pos.y, gz_g)
    G.rig.rotation_euler.z = _yaw_to(g_fwd)
    Ch = P.make_person("child", "CHILD", pose=None, expression=None)
    Ch.rig.location = (c_pos.x, c_pos.y, gz_c)
    Ch.rig.rotation_euler.z = _yaw_to(c_fwd)
    for p, gz in ((G, gz_g), (Ch, gz_c)):
        p.update()
        P.pose(p, "sit", ground_z=gz)
        _hide_thighs(p)
    gs = _find("grandfather_seat")
    if gs is not None:
        gs.scale.x *= 0.72
        gs.scale.y *= 0.75
    seat_under(G, gs, gz_g)
    seat_under(Ch, _find("child_seat"), gz_c)
    baseG = G._pose.copy()
    baseC = Ch._pose.copy()

    gy = G.rig.rotation_euler.z
    g_left = Vector((math.cos(gy), math.sin(gy), 0.0))      # grandfather's left (character +X rotated by his yaw)
    g_f3 = Vector((g_fwd.x, g_fwd.y, 0.0))

    # ---------------- scroll across the grandfather's lap ----------------
    hipG = (G.bone_world("upperleg01.L") + G.bone_world("upperleg01.R")) * 0.5
    kneeG = (G.bone_world("lowerleg01.L") + G.bone_world("lowerleg01.R")) * 0.5
    lap = hipG.lerp(kneeG, 0.55)
    lap.z = max(hipG.z, kneeG.z) + 0.075
    scroll = A.load("scroll", open_width=0.2)
    sc_s = 0.78
    ez = g_f3.normalized()
    ey = Vector((0, 0, -1))
    ex = ey.cross(ez)
    R = Matrix((ex, ey, ez)).transposed()
    scroll.matrix_world = Matrix.Translation(lap - R @ Vector((0, 0, 0.26 * sc_s)) + Vector((0, 0, 0.02))) \
        @ R.to_4x4() @ Matrix.Scale(sc_s, 4)
    scroll_right = lap + (-g_left) * 0.13 + Vector((0, 0, 0.03))     # his right roller

    # ---------------- lamp positions ----------------
    lamp_hold = Vector((g_pos.x, g_pos.y, 0)) + g_f3 * 0.27 + g_left * 0.07
    lamp_hold.z = gz_g + 0.80
    lamp_hand = Vector((0.36, 0.66, gz_g + 0.74))                   # the hand-off point
    lamp_child = Vector((c_pos.x, c_pos.y, 0)) + Vector((c_fwd.x, c_fwd.y, 0)) * 0.24 + Vector((-0.04, 0.02, 0))
    lamp_child.z = gz_c + 0.60
    kneeGL = G.bone_world("lowerleg01.L")
    kneeGR = G.bone_world("lowerleg01.R")

    # timing (24 fps): phrase 2 "future generations will be told..." starts ~ f67
    p2 = ctx.phrase_frames(1)[0] if len(ctx.phrases) > 1 else 67
    f_ext0, f_ext1 = int(p2 - 4), int(p2 + 24)              # grandfather reaches out
    f_c0, f_c1 = int(p2 + 8), int(p2 + 29)                  # boy's hands come up
    H = int(p2 + 33)                                        # hand-off (parent switch)
    f_w0, f_w1 = H + 4, H + 28                              # grandfather withdraws
    f_d0, f_d1 = H + 6, H + 34                              # boy draws the lamp to his chest

    # grandfather: right hand on the scroll throughout, left hand holds/extends/withdraws
    up = Vector((0, 0, 1))
    right_on_scroll = dict(T=scroll_right, pron=95, flex=8, shape="relaxed", pole=(-0.7, 0.4, -1.0))
    hold = dict(T=lamp_hold - up * 0.018, pron=-5, flex=-8, shape="cup", pole=(0.7, 0.35, -1.0))
    reach = dict(T=lamp_hand - up * 0.018, pron=-8, flex=-12, shape="cup", pole=(0.8, 0.2, -0.8))
    rest = dict(T=kneeGL + Vector((0, 0, 0.06)) + g_f3 * 0.02, pron=95, flex=5, shape="relaxed", pole=(0.7, 0.5, -1.0))
    GA = arm_state(G, baseG, {"L": hold, "R": right_on_scroll})
    GB = arm_state(G, baseG, {"L": reach, "R": right_on_scroll}, lean=7)
    GCs = arm_state(G, baseG, {"L": rest, "R": right_on_scroll}, lean=2)
    key_state(G, GA, [1, f_ext0])
    key_state(G, GB, [f_ext1, f_w0])
    key_state(G, GCs, [f_w1, N])

    # boy: hands on knees -> cupped under the lamp -> lamp at his chest
    kL, kR = Ch.bone_world("lowerleg01.L"), Ch.bone_world("lowerleg01.R")
    c_left = Vector((math.cos(Ch.rig.rotation_euler.z), math.sin(Ch.rig.rotation_euler.z), 0))
    knees = {"L": dict(T=kL + Vector((0, 0, 0.04)), pron=95, shape="relaxed", pole=(0.8, 0.5, -1.0)),
             "R": dict(T=kR + Vector((0, 0, 0.04)), pron=95, shape="relaxed", pole=(-0.8, 0.5, -1.0))}
    under = {"R": dict(T=lamp_hand - up * 0.03 - c_left * 0.035, pron=5, flex=-6, shape="cup", pole=(-0.7, 0.3, -1.0)),
             "L": dict(T=lamp_hand - up * 0.035 + c_left * 0.04 + Vector((0, 0, 0)), pron=5, flex=-6, shape="cup",
                       pole=(0.7, 0.3, -1.0))}
    chest = {"R": dict(T=lamp_child - up * 0.03 - c_left * 0.035, pron=5, flex=-8, shape="cup", pole=(-0.6, 0.4, -1.0)),
             "L": dict(T=lamp_child - up * 0.035 + c_left * 0.04, pron=5, flex=-8, shape="cup", pole=(0.6, 0.4, -1.0))}
    CA = arm_state(Ch, baseC, knees)
    CB = arm_state(Ch, baseC, under, lean=6)
    CC = arm_state(Ch, baseC, chest, lean=3)
    key_state(Ch, CA, [1, f_c0])
    key_state(Ch, CB, [f_c1, f_d0])
    key_state(Ch, CC, [f_d1, N])

    # ---------------- the lamp (parent switch at H) ----------------
    lamp, lflame, _ = S.oil_lamp(loc=(0, 0, 0), light=False, flicker=0, name="handoff_lamp")
    lflame.hide_render = True
    lflame.hide_viewport = True
    fl = FX.flame(loc=tuple(S.LAMP_TIP + Vector((0.002, 0, -0.002))), size=0.034, flicker=1.0, seed=7,
                  light_energy=9.0, light_radius=0.006, parent=lamp, name="HandoffFlame")
    noz = Vector((-0.35, -1.0, 0)).normalized()             # nozzle (+X local) towards the camera side
    L0 = Matrix.Translation(lamp_hand) @ Matrix.Rotation(math.atan2(noz.y, noz.x), 4, "Z")
    lamp.matrix_world = L0
    cg = lamp.constraints.new("CHILD_OF")
    cg.target, cg.subtarget = G.rig, "wrist.L"
    cg.inverse_matrix = bone_world(G, GB, "wrist.L").inverted()
    cc = lamp.constraints.new("CHILD_OF")
    cc.target, cc.subtarget = Ch.rig, "wrist.R"
    cc.inverse_matrix = bone_world(Ch, CB, "wrist.R").inverted()
    for con, a, b in ((cg, 1.0, 0.0), (cc, 0.0, 1.0)):
        con.influence = a
        con.keyframe_insert("influence", frame=1)
        con.influence = b
        con.keyframe_insert("influence", frame=H)
    for fc in (lamp.animation_data.action.fcurves if lamp.animation_data else []):
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT"

    # ---------------- faces: looks, expressions, speech ----------------
    def look(p, base, tgt, f):
        p._pose = base
        P.look_at(p, tgt, frame=f)

    G.update(); Ch.update()
    g_eye, c_eye = G.eye_pos(), Ch.eye_pos()
    for f in (1, f_ext0):
        look(G, baseG, c_eye, f)
    look(G, baseG, lamp_hand + Vector((0.05, 0, 0.12)), f_ext1)
    look(G, baseG, lamp_hand + Vector((0.08, 0, 0.18)), H)
    for f in (f_w1, N):
        look(G, baseG, c_eye + Vector((0, 0, -0.05)), f)
    for f in (1, f_c0 - 6):
        look(Ch, baseC, g_eye, f)
    for f in (f_c1, f_d1 + 10):
        look(Ch, baseC, lamp_hand.lerp(lamp_child, 0.5), f)
    for f in (f_d1 + 30, N):
        look(Ch, baseC, g_eye, f)
    G._pose, Ch._pose = baseG, baseC

    # grandfather speaks softly through phrase 1 (mouth mostly hidden by the beard), then smiles
    t0 = 10
    talk = [2.5, 5.0, 1.5, 4.5, 3.0, 6.0, 1.0, 4.0, 2.0, 5.0, 1.5]
    for i, j in enumerate(talk):
        P.expression(G, "peace", weight=0.7, frame=t0 + i * 5, extra={"jaw": j})
    P.expression(G, "peace", weight=0.75, frame=t0 + len(talk) * 5 + 3, extra={"jaw": 0.5})
    P.expression(G, "peace", weight=1.0, frame=H + 12)
    P.expression(Ch, "awe", weight=0.8, frame=1)
    P.expression(Ch, "awe", weight=1.0, frame=H)
    P.expression(Ch, {"mouth-corner-puller": 0.35, "eyebrows-up": 0.3, "eyebrows-inner-up": 0.2, "eye-opened-up": 0.2,
                      "jaw": 3}, weight=1.0, frame=H + 50)
    for p, fs in ((G, (38, H + 20)), (Ch, (f_c0 - 10, H + 44))):
        for f in fs:
            P.blink(p, f)

    # ---------------- camera ----------------
    focus = bpy.data.objects.new("focus", None)
    C.link(focus)
    focus.location = lamp_hand + Vector((0.0, 0.05, 0.12))
    cam = C.camera((0.78, -1.85, 1.02), (0.36, 0.72, 0.84), lens=40, fstop=2.2, focus=focus)
    a0, a1 = Vector((0.80, -1.88, 1.03)), Vector((0.66, -1.42, 0.97))
    t0v, t1v = Vector((0.36, 0.74, 0.86)), Vector((0.40, 0.70, 0.80))

    def path(f):
        u = C.ease_in_out(min(1.0, (f - 1) / max(1, N - 1)))
        sh = Vector((C.shake(f, 0.004, 0.25, 3).x, 0, C.shake(f, 0.003, 0.22, 9).z))
        return a0.lerp(a1, u) + sh, t0v.lerp(t1v, u)
    C.animate_camera(cam, path, 1, N)

    # a touch of cool rim to separate the heads from the night
    rim = C.light("AREA", loc=(0.9, 3.2, 2.6), energy=26, temp=9000, target=(0.3, 0.8, 1.0), size=2.0,
                  name="rim_moon", shadow=False)
    rim.data.volume_factor = 0.0

    ctx.samples = 4
    ctx.render_opts = {"volumetrics": "low"}
    ctx.interp = True   # lead: half-rate to fit the render budget (sparks may soften slightly)
    ctx.post = {"grade": "candle", "vignette": 0.32, "bloom": 0.3, "caption": {"ink": "light"}}
