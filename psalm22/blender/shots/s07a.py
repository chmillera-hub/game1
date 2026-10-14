"""s07a - Nativity (flashback): "Yet you brought me out of the womb; you made me trust in you, even at my
mother's breast."

Bethlehem stable cave at night in warm golden lamplight. Young Mary sits on a stone by the wooden manger,
cradling the swaddled newborn against her breast, gazing down at him; an ox and a donkey rest in the
shadows behind; silver starlight streams in through the doorway. Slow push-in from a medium shot to a
close-up of Mary's face with the baby's face below it. On the second phrase the baby opens his eyes and
looks up at his mother ("you made me trust in you"), she smiles and bows her head closer.

The last frames (close on Mary's face, 3/4, head inclined to screen right) are designed to match-dissolve
into s07b (the older Mary at the foot of the cross, same face position and size, looking up).
"""
import math
import os
import bpy
from mathutils import Vector, noise
from lib import core as C
from lib import sets as S
from lib import characters as P
from lib import assets as A

FLICK_SPEED = 3.2      # lamp flicker noise speed (units/s) - slow enough to be keyed on odd frames only


def _sit_cradle(Pp, p, lean=9.0, head_amt=0.95, tilt=-7.0, **k):
    """Seated on a low stone (feet on the floor) holding a swaddled baby at the chest: legs of 'sit',
    arms/head of 'cradle'. Registered as a custom pose (P.POSES) so pose()/key_pose() ground it."""
    h = p.height / 1.75
    P._spine_bend(Pp, bend=lean, side=-2)
    for s in "LR":
        lat = P._lateral(s)
        P._leg(Pp, s, Vector((lat.x * 0.13, -1, -0.10)), P.UP + lat * 0.18, 95)
        P._flatten_foot(Pp, s)
    chest = Pp.head("spine02")
    TL = chest + Vector((-0.13 * h, -0.26 * h, -0.13 * h))
    TR = chest + Vector((0.03 * h, -0.31 * h, 0.0))
    P._arm_ik(Pp, "L", TL, pole=Vector((1, 0.25, -0.7)), pron=-15, flex=5)
    P._arm_ik(Pp, "R", TR, pole=Vector((-1, 0.2, -0.9)), pron=75, flex=10)
    P._hand(Pp, "L", "cup")
    P._hand(Pp, "R", "cup")
    P._apply_head(Pp, "down", amount=head_amt, tilt=tilt)
    Pp.cradle = chest + Vector((-0.02 * h, -0.24 * h, -0.07 * h))


def _rekey_flicker(ld, base, seed, amount=0.16, n=None):
    """Replace a lamp light's per-frame flicker by a slower flicker keyed on ODD frames only (linear), so the
    12 fps + RIFE path reproduces it exactly (docs/interp.md)."""
    if ld.animation_data:
        ld.animation_data_clear()
    n = n or bpy.context.scene.frame_end

    def fn(f):
        t = f / 24.0 * FLICK_SPEED
        v = noise.noise(Vector((t, seed * 3.1, 0.5))) * 0.75 + noise.noise(Vector((t * 2.1, seed, 4.2))) * 0.25
        return base * max(0.3, 1.0 + amount * 2.0 * v)
    C.key_fn(ld, "energy", fn, 1, n + (1 - n % 2), step=2)


def _rekey_flame_time(n):
    """Flame shader noise 'time': slower and keyed on odd frames (linear)."""
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
        for f in (1, n + (1 - n % 2)):
            sock.default_value = (f - 1) / 24.0 * 2.5
            sock.keyframe_insert("default_value", frame=f)
        if nt.animation_data and nt.animation_data.action:
            for fc in C._fcurves(nt.animation_data.action):
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"


def build(ctx):
    N, NR = ctx.nframes, ctx.render_frames
    p0s, p0e = ctx.phrase_frames(0)
    p1s, p1e = ctx.phrase_frames(1)

    st = S.stable_cave(ctx, manger="wood", straw_density=520, lamp_energy=1.0, starlight=1.0)

    # ------------------------------------------------------------------ Mary on her seat stone
    P.POSES["sit_cradle"] = _sit_cradle
    P.GROUNDED.add("sit_cradle")
    seat = Vector(st["mary"])
    mary = P.make_person("mary", "MARY_YOUNG", pose=None)
    # she faces the camera side (-Y), turned 30 deg to her right so the camera sits off her left shoulder
    cam_side = Vector((0.38, -1.0, 0.0)).normalized()          # direction from Mary towards the camera
    a = math.radians(-30)
    F = Vector((cam_side.x * math.cos(a) - cam_side.y * math.sin(a), cam_side.x * math.sin(a) + cam_side.y * math.cos(a), 0))
    yaw = math.atan2(F.x, -F.y)
    mary.rig.location = (seat.x, seat.y, 0.0)
    mary.rig.rotation_euler.z = yaw
    P.pose(mary, "sit_cradle", ground_z=0.0)
    # the pose stored the cradle point before grounding moved the root: recompute it in the grounded pose
    hh = mary.height / 1.75
    mary._pose.cradle = mary._pose.head("spine02") + Vector((-0.02 * hh, -0.24 * hh, -0.07 * hh))
    P.expression(mary, "peace")

    # the seat stone: move its top up/down to the underside of her thighs/buttocks
    import numpy as np
    pts = P.lbs_points(mary)
    mw = mary.rig.matrix_world
    pw = np.array([tuple(mw @ Vector(q)) for q in pts[::4]])
    pel = mary.bone_world("root")
    near = pw[(np.hypot(pw[:, 0] - pel.x, pw[:, 1] - pel.y) < 0.16)]
    sit_z = float(near[:, 2].min()) if len(near) else 0.40
    for o in st.coll.objects:
        if o.name.startswith("mary_seat"):
            o.location.z += (sit_z - 0.38) - 0.012

    baby = P.make_person("baby", "BABY")
    P.place_baby(baby, mary)

    # ------------------------------------------------------------------ animals (in the shadows behind)
    ox = A.animal("ox", "idle", loc=(1.25, 4.15, 0.0), rot_z=180 + 150, tint=(-0.55, -0.55, -0.55))
    donkey = A.animal("donkey", "idle", loc=(-1.75, 3.75, 0.0), rot_z=180 - 120, tint=(-0.55, -0.58, -0.62),
                      offset=1.3)

    # ------------------------------------------------------------------ camera
    eye = mary.eye_pos()
    bh = baby.head_pos()
    mid = eye.lerp(bh, 0.35)
    d0, d1 = 2.25, 0.92
    cam_dir = (cam_side + Vector((0, 0, -0.05))).normalized()

    def cam(f):
        u = C.ease_in_out(min(1.0, ctx.u(f)))
        dist = d0 + (d1 - d0) * u
        tgt = (eye.lerp(bh, 0.55)).lerp(mid, u) + Vector((0, 0, -0.05 * (1 - u)))
        loc = tgt + cam_dir * dist + C.shake(f, 0.004, 0.35, 7)
        foc = (eye - loc).length
        return (loc, tgt, 0.0, 50, foc)

    camo = C.camera(lens=50, fstop=2.0, name="Cam")
    dbg = os.environ.get("S07_DEBUG", "")
    if dbg:
        if dbg == "wide":
            w = st.cameras["wide"]
        else:   # "x,y,z:tx,ty,tz:lens" (relative to Mary's eyes)
            a_, b_, c_ = dbg.split(":")
            w = {"loc": eye + Vector([float(x) for x in a_.split(",")]),
                 "target": eye + Vector([float(x) for x in b_.split(",")]), "lens": float(c_)}
        camo.location = w["loc"]
        C.look_at(camo, w["target"])
        camo.data.lens = w["lens"]
        camo.data.dof.use_dof = False
    else:
        C.animate_camera(camo, cam, 1, NR)

    # ------------------------------------------------------------------ flicker keyed on odd frames
    for k, (name, lo) in enumerate(st.lights.items()):
        if lo is None or lo.type != "LIGHT":
            continue
        ad = lo.data.animation_data
        if ad and ad.action:
            base = lo.data.energy
            fc = [fc for fc in C._fcurves(ad.action) if fc.data_path == "energy"]
            if fc:
                vals = [kp.co[1] for kp in fc[0].keyframe_points]
                base = sum(vals) / len(vals)
            _rekey_flicker(lo.data, base, seed=k + 1)
    _rekey_flame_time(NR)

    ctx.samples = 6
    ctx.render_opts.update({"volumetrics": "low"})
    ctx.interp = True
    ctx.post.update({"grade": ["night", "flashback"], "temperature": 0.25, "bloom": 0.3, "vignette": 0.28})
