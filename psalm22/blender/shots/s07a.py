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
from lib import wardrobe as W

FLICK_SPEED = 3.0      # lamp flicker noise speed (units/s); keyed on odd frames only
FACE_Y = 0.30         # Mary's eyes at 30 % from the top in the last frames (s07b starts the same)
CUT_FRAME_H = 0.78    # frame height (m) at Mary's eyes in the last frames (s07b starts the same)
LENS = 50.0
CAM_ANGLE = 18.0      # camera azimuth off Mary's facing, towards her left (s07b uses the same)


# ------------------------------------------------------------------------------------------ pose
def _sit_cradle(Pp, p, lean=3.0, tl=None, tr=None, side=-2.0, pitch=26.0, turn=16.0, tilt=7.0, **k):
    """Seated on a low stone (feet on the floor) holding a swaddled baby at the breast: legs of 'sit',
    arms of 'cradle' (baby's head in the LEFT elbow crook). tl/tr = rig-space palm targets; head: pitch (deg
    down), turn (deg to her left), tilt (deg towards her left shoulder). Registered in P.POSES so
    pose()/key_pose() ground it."""
    h = p.height / 1.75
    P._spine_bend(Pp, bend=lean, side=side)
    for s in "LR":
        lat = P._lateral(s)
        P._leg(Pp, s, Vector((lat.x * 0.13, -1, -0.10)), P.UP + lat * 0.18, 95)
        P._flatten_foot(Pp, s)
    chest = Pp.head("spine02")
    # tl/tr are offsets from the chest (rig axes): pose() grounds AFTER this function by moving the root, so
    # absolute rig-space targets would end up ~0.4 m lower in a seated pose
    TL = chest + Vector(tl) if tl is not None else chest + Vector((-0.08 * h, -0.28 * h, -0.13 * h))
    TR = chest + Vector(tr) if tr is not None else chest + Vector((0.03 * h, -0.30 * h, -0.04 * h))
    P._arm_ik(Pp, "L", TL, pole=Vector((1, 0.15, -0.8)), pron=-15, flex=5)
    P._arm_ik(Pp, "R", TR, pole=Vector((-1, 0.2, -0.9)), pron=75, flex=10)
    P._hand(Pp, "L", "cup")
    P._hand(Pp, "R", "cup", 0.8)
    P._apply_head(Pp, "down", amount=pitch / 30.0, tilt=tilt, turn=turn)


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


def _hide_behind(cam, objs, frames, margin=0.4, keep=("shell", "floor")):
    """Hide (render) mesh objects whose bounding box lies entirely behind the camera on all `frames`."""
    sc = bpy.context.scene
    planes = []
    for f in frames:
        sc.frame_set(f)
        mw = cam.matrix_world
        planes.append((mw.translation.copy(), -(mw.to_3x3() @ Vector((0, 0, 1)))))
    sc.frame_set(1)
    hidden = []
    for o in objs:
        if o.type not in ("MESH", "CURVES", "CURVE") or o.hide_render or any(k in o.name for k in keep):
            continue
        corners = [o.matrix_world @ Vector(c) for c in o.bound_box]
        if all(all((c - p).dot(d) < -margin for c in corners) for p, d in planes):
            o.hide_render = True
            hidden.append(o.name)
    return hidden


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
    mary = P.make_person("mary", "MARY_YOUNG", pose=None, outfit=None)
    # dressed here (not via the preset) for a floor-length, long-sleeved tunic: modest, and it keeps the
    # seated legs covered; colours: muted madder tunic, deep blue veil
    W.dress(mary, ["tunic", "veil"], colors={"tunic": (0.36, 0.19, 0.16), "veil": (0.15, 0.25, 0.50), "belt": "umber"},
            seed=0, detail="hero", tunic={"length": "floor", "sleeves": "long"})
    cam_side = Vector((0.05, -1.0, 0.0)).normalized()        # from Mary towards the camera (doorway behind her)
    a = math.radians(-CAM_ANGLE)                              # camera sits off her left shoulder
    F = Vector((cam_side.x * math.cos(a) - cam_side.y * math.sin(a),
                cam_side.x * math.sin(a) + cam_side.y * math.cos(a), 0))
    mary.rig.location = (seat.x, seat.y, 0.0)
    mary.rig.rotation_euler.z = math.atan2(F.x, -F.y)
    P.pose(mary, "sit_cradle", ground_z=0.0)
    _shift_seat(st, mary, seat.z)

    # ---------------------------------------------------------------- the baby, held at her breast
    # placed where it reads (relative to her eyes: below, in front, towards her left elbow), then her arms are
    # solved to hold it and the bundle is parented to her left forearm (it follows her breathing/leaning).
    baby = P.make_person("baby", "BABY", outfit_colors={"swaddle": "undyed"})
    mary.update()
    up = Vector((0, 0, 1))
    left = Vector((-F.y, F.x, 0))                   # her left
    eye0 = mary.eye_pos()
    cam_h = cam_side.copy()
    bh_eye = eye0 - up * 0.27 + F * 0.11 + left * 0.15        # baby's eyes
    perp = Vector((-cam_h.y, cam_h.x, 0))
    perp = perp if perp.dot(left) > 0 else -perp                # across the frame, head towards her left
    ax = (perp * 0.4 + left * 0.6).normalized()
    ax = (ax + up * 0.22).normalized()                        # baby's feet -> head
    face = (eye0 - bh_eye).normalized().lerp(cam_h, 0.55)     # up at her, turned towards the camera
    face = (face - ax * face.dot(ax)).normalized()
    side_ = face.cross(ax).normalized()
    face = ax.cross(side_).normalized()
    R = Matrix((side_, -face, ax)).transposed()               # baby rig: +Z head, -Y face
    bm0 = baby.rig.matrix_world.copy()
    be_local = bm0.inverted() @ baby.eye_pos()
    baby.rig.matrix_world = Matrix.Translation(bh_eye - R @ be_local) @ R.to_4x4()
    baby.update()
    head_c = baby.head_pos()
    back = -face
    # left forearm under the bundle (elbow at the head), palm under the bottom; right hand on top of the hips
    tl_w = head_c - ax * 0.30 + back * 0.075 - up * 0.02
    tr_w = head_c - ax * 0.24 + face * 0.075
    im3 = mary.rig.matrix_world.to_3x3().inverted()
    chest_w = mary.bone_world("spine02")
    tl, tr = im3 @ (tl_w - chest_w), im3 @ (tr_w - chest_w)
    P.pose(mary, "sit_cradle", ground_z=0.0, tl=tl, tr=tr)
    mary.update()
    # settle the dress over the knees and the seat stone (skinned skirts balloon in a seated pose)
    if os.environ.get("S07_NODRAPE") != "1":
        seat_objs = [o for o in st.coll.objects if o.name.startswith("mary_seat")]
        for o in seat_objs:
            o.modifiers.new("DrapeCollision", "COLLISION")
        W.drape(mary, mary.garments, frames=24, ramp=14, ground=0.0)
        for o in seat_objs:
            m_ = o.modifiers.get("DrapeCollision")
            if m_:
                o.modifiers.remove(m_)
    _parent_keep(baby.rig, mary.rig, "lowerarm01.L")
    baby.update()

    # ---------------------------------------------------------------- performance: Mary looks at the baby
    bface = baby.eye_pos()
    # (frame, lean, pitch, turn, tilt): breathing-slow settle, then on the 2nd phrase she bows a little closer
    keys = [(1, 3.0, 30.0, 15.0, 6.0), (int(p0e), 3.4, 31.0, 16.0, 7.0), (int(p1s + 26), 4.6, 35.0, 18.0, 9.0),
            (NR, 4.8, 35.5, 18.0, 9.5)]
    for f, ln, pi, tu, ti in keys:
        P.key_pose(mary, f, "sit_cradle", ground_z=0.0, tl=tl, tr=tr, lean=ln, pitch=pi, turn=tu, tilt=ti)
    for f in (1, int(p1s + 26)):
        bpy.context.scene.frame_set(f)
        P.eyes_look(mary, baby.eye_pos(), frame=f, down_limit=28)
    bpy.context.scene.frame_set(1)
    # lids lowered with the gaze (the lids do not follow the eyeballs), a faint smile that grows
    calm = {"eye-closure": 0.40, "mouth-corner-puller": 0.28, "eyebrows-inner-up": 0.10}
    P.expression(mary, calm, frame=1)
    P.expression(mary, calm, frame=int(p1s + 14))
    P.expression(mary, {"eye-closure": 0.44, "mouth-corner-puller": 0.58, "eyebrows-inner-up": 0.2,
                        "mouth-elevation": 0.06}, frame=int(p1s + 34))
    P.blink(mary, int(ctx.frame(1.6)))
    P.blink(mary, int(ctx.frame(5.9)))

    # baby: asleep, then opens his eyes and looks up at her ("you made me trust in you")
    f_open = int(p1s + 10)
    P.expression(baby, "sleep", frame=1)
    P.expression(baby, "sleep", frame=f_open)
    P.expression(baby, {"eye-closure": 0.3, "mouth-corner-puller": 0.12}, frame=f_open + 12)
    P.eyes_look(baby, mary.eye_pos(), frame=f_open)

    # the set's floor lamp sits right in front of her: keep it as a low warm fill
    if st.lights.get("lamp_floor") is not None:
        st.lights["lamp_floor"].data.energy *= 0.15
    # cool starlight rim from the doorway behind her (her right shoulder / veil edge), shadowless
    rim_pos = eye0 - cam_h * 1.6 - left * 0.9 + up * 0.7
    rim = C.light("SPOT", tuple(rim_pos), 40.0, temp=9500, target=tuple(eye0 - up * 0.25), size=0.2,
                  spot_size=30, spot_blend=0.6, shadow=False, name="StarRim")
    rim.data.volume_factor = 0.0

    # ---------------------------------------------------------------- animals in the shadows behind
    ox = A.animal("ox", "idle", loc=(0.75, 4.35, 0.0), rot_z=180 + 160, tint=(-0.6, -0.6, -0.58))
    donkey = A.animal("donkey", "idle", loc=(-1.45, 4.05, 0.0), rot_z=180 - 140, tint=(-0.55, -0.6, -0.66),
                      offset=1.3)

    # ---------------------------------------------------------------- camera: slow push-in
    eye = mary.eye_pos()
    bh = baby.eye_pos()
    vh = 2 * math.tan(math.atan(18.0 / LENS))           # frame height per metre of distance
    d1 = CUT_FRAME_H / vh
    d0 = 2.25 * d1

    def cam(f):
        u = C.ease_in_out(min(1.0, ctx.u(f)))
        dist = d0 + (d1 - d0) * u
        fh = vh * dist
        el = math.radians(-10.0 - 6.0 * u)              # a little below her eyes (looking up into the veil)
        loc = eye + (cam_side * math.cos(el) + up * math.sin(el)) * dist
        # start: mother + child centred; end: her eyes at FACE_Y
        t0 = eye - up * (0.12 * fh)                      # eyes at 38 % at the start
        t1 = eye - up * ((0.5 - FACE_Y) * fh)
        tgt = t0.lerp(t1, C.smoothstep(min(1.0, ctx.u(f) * 1.15)))
        loc = loc + (tgt - eye) * 0.0 + C.shake(f, 0.0025, 0.3, 7)
        return (loc, tgt, 0.0, LENS, (eye - loc).length)

    # ---------------------------------------------------------------- practical key: oil lamp on a tall jar
    # placed at the right edge of the opening frame, between camera and Mary, flame at baby height
    c1 = cam(1)
    v1 = (Vector(c1[1]) - Vector(c1[0]))
    v1.z = 0
    v1.normalize()
    r1 = Vector((v1.y, -v1.x, 0))
    jp = Vector(c1[0]) + v1 * 1.25 + r1 * 0.30
    jar = S.clay_jar((jp.x, jp.y, 0.0), height=0.72, name="key_jar", rot_z=40)
    lamp, flame, klight = S.oil_lamp((jp.x, jp.y, 0.72), rot_z=math.degrees(math.atan2(-r1.y, -r1.x)) + 20,
                                     energy=16.0, temp=2650, shadow=False, light_radius=0.03, seed=5,
                                     name="key_lamp")
    # off-screen key: a second lamp on a ledge at her left, below eye level (sculpts face + baby)
    kpos = eye0 + left * 0.62 + F * 0.30 - up * 0.22
    lamp2, flame2, klight2 = S.oil_lamp(tuple(kpos - Vector((0, 0, 0.05))), rot_z=0, energy=28.0, temp=2600,
                                        shadow=True, light_radius=0.035, seed=9, name="key_lamp2")
    lamp2.hide_render = True
    flame2.hide_render = True
    for k_ in ("bounce", "floor_bounce"):
        if st.lights.get(k_) is not None:
            st.lights[k_].data.energy *= 0.35

    camo = C.camera(lens=LENS, fstop=2.0, name="Cam")
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
        hid = _hide_behind(camo, list(st.coll.all_objects), (1, NR // 2, NR))
        print("S07A hidden behind camera:", hid)

    # ---------------------------------------------------------------- flicker keyed on odd frames
    lights = dict(st.lights)
    lights["key_lamp"] = klight
    lights["key_lamp2"] = klight2
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
    ctx.post.update({"grade": ["flashback", "candle"], "temperature": 0.2, "saturation": 0.88, "bloom": 0.35,
                     "vignette": 0.3, "caption": {"y": 0.72}})
