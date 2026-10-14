"""s07a - Nativity (flashback): "Yet you brought me out of the womb; you made me trust in you, even at my
mother's breast."

Bethlehem stable cave at night, lit like a de La Tour nativity: young Mary sits on a stone by the wooden
manger cradling the swaddled newborn at her breast, gazing down at him in the warm glow of a clay oil lamp;
behind her the doorway glows with silver starlight, the donkey stands in it, the ox rests in the shadows.
Slow push-in from a medium shot to a close-up of Mary's face with the baby's face below it. On the second
phrase ("you made me trust in you") the baby opens his eyes and looks up at his mother; she smiles and
bows her head a little closer.

The end framing (close on Mary's face, 3/4, eyes lowered) is designed to match-dissolve into s07b (the older
Mary at the foot of the cross: same face position and size, looking up).

Interp: the lamp flicker is re-keyed on odd frames only (linear, slow noise) so 12 fps + RIFE reproduces it.
"""
import math
import os
import bpy
import numpy as np
from mathutils import Vector, Matrix, noise
from lib import core as C
from lib import sets as S
from lib import characters as P
from lib import assets as A

FLICK_SPEED = 3.0      # lamp flicker noise speed (units/s); keyed on odd frames only
FACE_SCREEN = (0.50, 0.36)   # where Mary's eyes sit in the final close-up (x, y from top) - shared with s07b


# ------------------------------------------------------------------------------------------ pose
def _sit_cradle(Pp, p, lean=9.0, tl=None, tr=None, side=-2.0, **k):
    """Seated on a low stone (feet on the floor) holding a swaddled baby at the breast: legs of 'sit',
    arms of 'cradle' (baby's head in the LEFT elbow crook). tl/tr = rig-space palm targets (optional).
    Registered in P.POSES so pose()/key_pose() ground it; head via the generic look= parameter."""
    h = p.height / 1.75
    P._spine_bend(Pp, bend=lean, side=side)
    for s in "LR":
        lat = P._lateral(s)
        P._leg(Pp, s, Vector((lat.x * 0.13, -1, -0.10)), P.UP + lat * 0.18, 95)
        P._flatten_foot(Pp, s)
    chest = Pp.head("spine02")
    TL = Vector(tl) if tl is not None else chest + Vector((-0.12 * h, -0.25 * h, -0.10 * h))
    TR = Vector(tr) if tr is not None else chest + Vector((0.03 * h, -0.30 * h, 0.02 * h))
    P._arm_ik(Pp, "L", TL, pole=Vector((1, 0.25, -0.7)), pron=-15, flex=5)
    P._arm_ik(Pp, "R", TR, pole=Vector((-1, 0.2, -0.9)), pron=75, flex=10)
    P._hand(Pp, "L", "cup")
    P._hand(Pp, "R", "cup", 0.8)
    P._apply_head(Pp, "down", amount=0.6, tilt=-4)


# ------------------------------------------------------------------------------------------ flicker
def _rekey_flicker(ld, base, seed, amount=0.14, n=None):
    """Replace a lamp light's per-frame flicker with a slower one keyed on ODD frames only (linear), so the
    12 fps + RIFE path reproduces it exactly (docs/interp.md, 'what it handles badly' #1)."""
    if ld.animation_data:
        ld.animation_data_clear()
    n = n or bpy.context.scene.frame_end

    def fn(f):
        t = f / 24.0 * FLICK_SPEED
        v = noise.noise(Vector((t, seed * 3.1, 0.5))) * 0.75 + noise.noise(Vector((t * 2.1, seed, 4.2))) * 0.25
        return base * max(0.3, 1.0 + amount * 2.0 * v)
    C.key_fn(ld, "energy", fn, 1, n + (1 - n % 2), step=2)


def _rekey_flames(n):
    """Flame shader noise 'time' (shared lamp_flame material): slower, keyed on odd frames (linear)."""
    last = n + (1 - n % 2)
    for m in bpy.data.materials:
        if not m.use_nodes or m.node_tree is None:
            continue
        tv = m.node_tree.nodes.get("time")
        if tv is None or tv.type != "VALUE":
            continue
        nt = m.node_tree
        if nt.animation_data:
            nt.animation_data_clear()
        sock = tv.outputs[0]
        for f in (1, last):
            sock.default_value = (f - 1) / 24.0 * 2.2
            sock.keyframe_insert("default_value", frame=f)
        if nt.animation_data and nt.animation_data.action:
            for fc in C._fcurves(nt.animation_data.action):
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"


def _parent_keep(child, parent, bone=None):
    mw = child.matrix_world.copy()
    child.parent = parent
    if bone:
        child.parent_type = "BONE"
        child.parent_bone = bone
    bpy.context.view_layer.update()
    child.matrix_world = mw
    bpy.context.view_layer.update()


def _shift_seat(st, mary, seat_top):
    """Raise/lower the seat stone so its top meets the underside of Mary's thighs (seated pose)."""
    pts = P.lbs_points(mary)
    mw = mary.rig.matrix_world
    pw = np.array([tuple(mw @ Vector(q)) for q in pts[::3]])
    pel = mary.bone_world("root")
    near = pw[(np.hypot(pw[:, 0] - pel.x, pw[:, 1] - pel.y) < 0.14)]
    sit_z = float(near[:, 2].min()) if len(near) else seat_top
    for o in st.coll.objects:
        if o.name.startswith("mary_seat"):
            o.location.z += (sit_z - seat_top) - 0.012


# ------------------------------------------------------------------------------------------ build
def build(ctx):
    N, NR = ctx.nframes, ctx.render_frames
    p0s, p0e = ctx.phrase_frames(0)
    p1s, p1e = ctx.phrase_frames(1)

    st = S.stable_cave(ctx, manger="wood", straw_density=480, lamp_energy=1.0, starlight=1.0)

    # ---------------------------------------------------------------- Mary on her seat stone
    P.POSES["sit_cradle"] = _sit_cradle
    P.GROUNDED.add("sit_cradle")
    seat = Vector(st["mary"])
    mary = P.make_person("mary", "MARY_YOUNG", pose=None)
    cam_side = Vector((0.05, -1.0, 0.0)).normalized()        # from Mary towards the camera (doorway behind her)
    a = math.radians(-32)                                     # camera sits 32 deg off her left shoulder
    F = Vector((cam_side.x * math.cos(a) - cam_side.y * math.sin(a),
                cam_side.x * math.sin(a) + cam_side.y * math.cos(a), 0))
    mary.rig.location = (seat.x, seat.y, 0.0)
    mary.rig.rotation_euler.z = math.atan2(F.x, -F.y)
    P.pose(mary, "sit_cradle", ground_z=0.0)
    _shift_seat(st, mary, seat.z)

    # ---------------------------------------------------------------- the baby along her left forearm
    baby = P.make_person("baby", "BABY")
    mary.update()
    E = mary.bone_world("lowerarm01.L")
    W = mary.bone_world("wrist.L")
    ax = (E - W).normalized()                       # baby's head direction (towards the elbow crook)
    up = Vector((0, 0, 1))
    n_up = (up - ax * up.dot(ax)).normalized()
    eye0 = mary.eye_pos()
    face = (eye0 - (E + W) * 0.5)
    face = (face - ax * face.dot(ax)).normalized()  # baby faces up towards her face
    side = face.cross(ax).normalized()
    face = ax.cross(side).normalized()
    R = Matrix((side, -face, ax)).transposed()      # baby rig: +Z head, -Y face
    bm0 = baby.rig.matrix_world.copy()
    hb_local = bm0.inverted() @ baby.head_pos()
    head_c = E + n_up * 0.055 - ax * 0.005 + face * 0.0
    baby.rig.matrix_world = Matrix.Translation(head_c - R @ hb_local) @ R.to_4x4()
    baby.update()
    # her right hand rests on the bundle near its middle
    mid_b = head_c - ax * 0.24 + face * 0.05
    tr = mary.rig.matrix_world.inverted() @ (mid_b + Vector((0, 0, 0.0)))
    P.pose(mary, "sit_cradle", ground_z=0.0, tr=tr)
    mary.update()
    _parent_keep(baby.rig, mary.rig, "lowerarm01.L")
    baby.update()

    # ---------------------------------------------------------------- performance: Mary looks at the baby
    bface = baby.eye_pos()
    look0 = bface + Vector((0, 0, 0.0))
    lean_keys = [(1, 8.0, 0.0), (int(p0e), 8.6, 0.0), (int(p1s + 26), 10.5, 0.03), (NR, 10.8, 0.03)]
    for f, ln, dz in lean_keys:
        P.key_pose(mary, f, "sit_cradle", ground_z=0.0, tr=tr, lean=ln, look=tuple(look0 + Vector((0, 0, -dz))))
    for f in (1, NR):
        P.eyes_look(mary, bface, frame=f)
    P.expression(mary, "peace", frame=1)
    P.expression(mary, "peace", frame=int(p1s + 14))
    P.expression(mary, {"eye-closure": 0.14, "mouth-corner-puller": 0.55, "eyebrows-inner-up": 0.18,
                        "mouth-elevation": 0.06}, frame=int(p1s + 34))
    P.blink(mary, int(ctx.frame(1.6)))
    P.blink(mary, int(ctx.frame(5.9)))

    # baby: asleep, then opens his eyes and looks up at her ("you made me trust in you")
    f_open = int(p1s + 10)
    P.expression(baby, "sleep", frame=1)
    P.expression(baby, "sleep", frame=f_open)
    P.expression(baby, {"eye-closure": 0.3, "mouth-corner-puller": 0.12}, frame=f_open + 12)
    P.eyes_look(baby, mary.eye_pos(), frame=f_open)

    # ---------------------------------------------------------------- practical key: oil lamp on a jar
    Mloc = Vector((seat.x, seat.y, 0))
    left = Vector((-F.y, F.x, 0))                   # her left
    jar_pos = Mloc + left * 0.55 + F * 0.42
    jar = S.clay_jar((jar_pos.x, jar_pos.y, 0.0), height=0.5, name="key_jar", rot_z=40)
    lamp, flame, klight = S.oil_lamp((jar_pos.x, jar_pos.y, 0.5), rot_z=math.degrees(math.atan2(-left.y, -left.x)),
                                     energy=26.0, shadow=True, light_radius=0.03, seed=5, name="key_lamp")
    # the set's floor lamp sits right in front of her: keep it as a low warm fill
    if st.lights.get("lamp_floor") is not None:
        st.lights["lamp_floor"].data.energy *= 0.5

    # ---------------------------------------------------------------- animals in the shadows behind
    ox = A.animal("ox", "idle", loc=(0.75, 4.35, 0.0), rot_z=180 + 160, tint=(-0.6, -0.6, -0.58))
    donkey = A.animal("donkey", "idle", loc=(-1.45, 4.05, 0.0), rot_z=180 - 140, tint=(-0.55, -0.6, -0.66),
                      offset=1.3)

    # ---------------------------------------------------------------- camera: slow push-in
    eye = mary.eye_pos()
    bh = baby.head_pos()
    d0, d1 = 2.05, 0.80
    cam_dir = (cam_side + Vector((0, 0, -0.10))).normalized()

    def cam(f):
        u = C.ease_in_out(min(1.0, ctx.u(f)) * 0.97 + 0.03 * min(1.0, ctx.u(f)) ** 2)
        dist = d0 + (d1 - d0) * u
        tgt = eye.lerp(bh, 0.62 - 0.32 * u)
        loc = tgt + cam_dir * dist + C.shake(f, 0.003, 0.3, 7)
        return (loc, tgt, 0.0, 50, (eye - loc).length)

    camo = C.camera(lens=50, fstop=2.0, name="Cam")
    dbg = os.environ.get("S07_DEBUG", "")
    if dbg:
        if dbg == "wide":
            w = st.cameras["wide"]
        else:   # "x,y,z:tx,ty,tz:lens" relative to Mary's eyes
            a_, b_, c_ = dbg.split(":")
            w = {"loc": eye + Vector([float(x) for x in a_.split(",")]),
                 "target": eye + Vector([float(x) for x in b_.split(",")]), "lens": float(c_)}
        camo.location = w["loc"]
        C.look_at(camo, w["target"])
        camo.data.lens = w["lens"]
        camo.data.dof.use_dof = False
    else:
        C.animate_camera(camo, cam, 1, NR)

    # ---------------------------------------------------------------- flicker keyed on odd frames
    lights = dict(st.lights)
    lights["key_lamp"] = klight
    for k, (name, lo) in enumerate(sorted(lights.items())):
        if lo is None or lo.type != "LIGHT":
            continue
        ad = lo.data.animation_data
        if ad and ad.action:
            base = lo.data.energy
            fcs = [fc for fc in C._fcurves(ad.action) if fc.data_path == "energy"]
            if fcs:
                vals = [kp.co[1] for kp in fcs[0].keyframe_points]
                base = sum(vals) / len(vals)
            _rekey_flicker(lo.data, base, seed=k + 1)
    _rekey_flames(NR)

    ctx.samples = 5
    ctx.render_opts.update({"volumetrics": "low"})
    ctx.interp = True
    ctx.post.update({"grade": ["night", "flashback"], "temperature": 0.25, "bloom": 0.3, "vignette": 0.28,
                     "caption": {"y": 0.72}})
