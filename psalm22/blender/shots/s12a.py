"""s12a - Dogs surround: "Dogs surround me, a pack of villains encircles me;"

Darkness at midday on the Golgotha plateau (eclipse). The camera sits low in the dust (~0.4 m, the
eye of a man thrown down) and looks out over the brow of the hill towards the dull red sun and the
hazy city. A pack of wild dogs (tawny jackal / dark pariah tints) prowls in a ring around the lens,
heads low, turning to stare into it with glinting eyes; one slinks past very close near the end.
Closer to the lens the legs of Roman soldiers (red tunic hems, studded apron straps, caligae) stride
round the other way, cropped at the shoulders by the frame top - faceless villains - their long
shadows sweeping over the ground towards the lens. Back light from the dim sun + a warm rim lamp edge
the animals and legs; a faint front bounce lets the eyeshine read. Handheld drift + a slow counter-pan.
Actors outside the view cone are hidden per frame (render cost).
"""
import math
import bpy
from mathutils import Vector
from lib import core as C
from lib import env as E
from lib import assets as A
from lib import characters as P

# layout ---------------------------------------------------------------------------------------
CAM_XY = (8.6, -2.2)          # on the plateau, east of the crosses (they stay out of frame)
LOOK_AZ = 18.0                # compass az of the view (0 = +Y) - towards the eclipse sun (15 deg E of N)
CAM_H = 0.38                  # lens height above the ground
LENS = 28.0
TILT = 5.0                    # deg down
HFOV2 = math.degrees(math.atan(10.125 / LENS))     # half horizontal FOV (portrait, 36 mm vertical sensor)


def _az_vec(az):
    a = math.radians(az)
    return Vector((math.sin(a), math.cos(a), 0.0))


def _pan_az(ctx, f):
    u = C.ease_in_out(min(1.0, ctx.u(f)))
    return LOOK_AZ - 7.0 + 14.0 * u            # pans right, against the dogs' right-to-left circling


def _cull(objs, positions, ctx, cam_xy, margin=16.0):
    """Key hide_render so an actor only renders while it is inside the (panning) view cone + margin."""
    NR = ctx.render_frames
    state = None
    for f in range(1, NR + 1):
        p = positions(f)
        d = Vector((p.x - cam_xy.x, p.y - cam_xy.y))
        az = math.degrees(math.atan2(d.x, d.y))
        rel = (az - _pan_az(ctx, f) + 180.0) % 360.0 - 180.0
        vis = abs(rel) < HFOV2 + margin or d.length < 0.9
        if vis != state:
            for o in objs:
                o.hide_render = not vis
                o.keyframe_insert("hide_render", frame=f)
            state = vis
    for o in objs:
        ad = o.animation_data
        if ad and ad.action:
            for fc in C._fcurves(ad.action):
                if fc.data_path == "hide_render":
                    for kp in fc.keyframe_points:
                        kp.interpolation = "CONSTANT"


def build(ctx):
    NR = ctx.render_frames
    sc = bpy.context.scene
    fwd = _az_vec(LOOK_AZ)
    c0 = Vector((CAM_XY[0], CAM_XY[1], 0.0))
    view = dict(loc=(c0.x, c0.y, 11.0), target=tuple(c0 + fwd * 30 + Vector((0, 0, 10.5))), lens=LENS - 2, margin=40)
    G = E.golgotha(ctx, mood="eclipse", view=view, grass=0.7, near_detail=1.0)
    for k_, c_ in G["crosses"].items():                    # behind the camera's back: not rendered
        for o in [c_["root"]] + list(c_["root"].children_recursive):
            o.hide_render = True
    ground = G["ground"]
    gz = lambda x, y: float(ground(x, y))
    cz = gz(c0.x, c0.y)
    cam_base = Vector((c0.x, c0.y, cz + CAM_H))
    view_az = math.atan2(fwd.y, fwd.x)       # math angle of the view direction (CCW = to the left)

    cam = C.camera(tuple(cam_base), tuple(cam_base + fwd * 4), lens=LENS, fstop=2.8, focus=3.4, name="Cam")
    cam_target = bpy.data.objects.new("s12a_eyes_target", None)
    sc.collection.objects.link(cam_target)
    cam_target.parent = cam

    # ------------------------------------------------------------------ dogs (CCW ring = right-to-left in frame)
    pack = bpy.data.collections.new("s12a_pack")
    sc.collection.children.link(pack)
    JACKAL, DARK, GREY = (-0.32, -0.48, -0.66), (-0.66, -0.68, -0.7), (-0.5, -0.54, -0.58)
    # (radius, angle rel. to the view at frame 1 (+ = left), action, speed, scale, tint, eye glow, offset, r drift)
    dogs = [(2.7, -8, "prowl", 1.5, 0.92, JACKAL, 0.9, 0.0, -0.35),
            (3.9, -24, "prowl", 1.35, 1.0, DARK, 1.0, 0.4, -0.2),
            (5.6, 4, "walk", 0.9, 0.9, GREY, 0.8, 0.9, 0.0),
            (3.2, -44, "prowl", 1.45, 0.95, JACKAL, 0.9, 0.2, -0.3),
            (7.2, -30, "trot", 0.7, 1.0, DARK, 0.9, 1.3, 0.0),
            (4.6, -58, "walk", 1.0, 0.88, JACKAL, 0.8, 0.6, -0.2),
            (2.5, 15, "prowl", 1.4, 0.9, GREY, 0.9, 1.7, -0.2),
            (1.6, -138, "walk", 1.25, 1.0, DARK, 1.0, 0.8, 0.0)]
    for i, (r, a1, act, spd, scl, tint, glow, off, dr) in enumerate(dogs):
        v = A.ground_speed("dog", act, 0, spd) * scl
        a_start = view_az + math.radians(a1)
        n = 60
        pts = []
        s_tot = v * (NR + 10) / ctx.fps          # path length; radius drifts (closing in)
        ang = 0.0
        for k in range(n + 1):
            t = k / n
            rr = r + dr * t
            a = a_start + ang
            x, y = c0.x + math.cos(a) * rr, c0.y + math.sin(a) * rr
            pts.append((x, y, gz(x, y)))
            ang += (s_tot / n) / rr
        arm = A.animal("dog", act, speed=spd, scale=scl, path=pts, offset=off, eye_glow=glow, tint=tint,
                       start_frame=1, end_frame=NR)
        A.set_eye_glow(arm, glow, color=(1.0, 0.86, 0.5))
        pb = arm.pose.bones.get("head")          # heads turn to stare at the lens
        if pb is not None:
            con = pb.constraints.new("DAMPED_TRACK")
            con.target = cam_target
            con.track_axis = "TRACK_Y"
            con.influence = 0.5 if i != 7 else 0.65
        kids = [o for o in A.children_recursive(arm)]
        for o in kids:
            if o.type == "MESH":
                pack.objects.link(o)
        arm_ = arm

        def pos(f, arm_=arm_):
            fc = {fc.array_index: fc for fc in C._fcurves(arm_.animation_data.action) if fc.data_path == "location"}
            return Vector((fc[0].evaluate(f), fc[1].evaluate(f), 0))
        _cull([arm] + kids, pos, ctx, c0)

    # one dog stands its ground right of centre and snarls into the lens
    a = view_az - math.radians(12)
    sp = Vector((c0.x + math.cos(a) * 3.4, c0.y + math.sin(a) * 3.4, 0))
    to_c = c0 - sp
    sn = A.animal("dog", "snarl", loc=(sp.x, sp.y, gz(sp.x, sp.y)), rot_z=math.degrees(math.atan2(to_c.x, -to_c.y)) + 18,
                  scale=1.02, eye_glow=1.0, tint=DARK, offset=0.5, start_frame=1)
    A.set_eye_glow(sn, 1.0, color=(1.0, 0.86, 0.5))
    pb = sn.pose.bones.get("head")
    if pb is not None:
        con = pb.constraints.new("DAMPED_TRACK")
        con.target = cam_target
        con.track_axis = "TRACK_Y"
        con.influence = 0.4
    for o in A.children_recursive(sn):
        if o.type == "MESH":
            pack.objects.link(o)
    # out-of-focus stones in the near foreground (depth layering below the pack)
    rocks = E.rock_protos("rocks")
    for k, (dl, dr_, sc_, rz) in enumerate(((0.95, -0.42, 0.9, 20), (1.15, 0.38, 1.3, 140), (0.8, 0.18, 0.55, 75))):
        x, y = c0.x + fwd.x * dl + fwd.y * dr_, c0.y + fwd.y * dl - fwd.x * dr_
        pr = rocks[(k * 2 + 1) % len(rocks)]
        s_ = 0.16 * sc_ / max(1e-3, max(pr.dimensions))
        E.place(pr, (x, y, gz(x, y) - 0.25 * pr.dimensions.z * s_), rot=(0, 0, rz), scale=s_, name="FgRock%d" % k)

    # ------------------------------------------------------------------ soldiers (CW ring = left-to-right, close)
    sold_coll = bpy.data.collections.new("s12a_legs")
    sc.collection.children.link(sold_coll)
    base = P.make_person("legion0", "SOLDIER", lod="mid", pose=None, expression=None, hair_strands=False)
    people = [base]
    # (radius, speed m/s, frame it crosses the view centre)
    plan = [(1.9, 1.15, 20), (2.05, 1.05, 86)]
    for i in range(1, len(plan)):
        q = P.clone(base, loc=(0, 0, 0), name="legion%d" % i)
        # workaround: clone() does not carry the cached body analysis the pose engine needs (walk/pose)
        for k in ("_co", "_w", "_anat", "_lbs", "_ground_offset", "mats", "expr_keys"):
            if hasattr(base, k):
                setattr(q, k, getattr(base, k))
        # workaround: clone() re-assigns .parent, which resets matrix_parent_inverse -> bone-parented parts
        # (helmet, studs) float away. Restore them from the source objects (matched by shared data).
        src = {o.data: o for o in base.objects()[1:] if o.data is not None}
        for c in q.objects()[1:]:
            o = src.get(c.data)
            if o is not None and o.parent_type == "BONE":
                c.parent_type = "BONE"
                c.parent_bone = o.parent_bone
                c.matrix_parent_inverse = o.matrix_parent_inverse.copy()
                c.matrix_basis = o.matrix_basis.copy()
        if q.rig.animation_data is None:
            q.rig.animation_data_create()
        q.rig.animation_data.action = None
        people.append(q)
    for p, (r, v, fc) in zip(people, plan):
        w = v / r / ctx.fps
        a_start = view_az + w * (fc - 1)                          # CW: angle decreases with time
        n = 40
        pts = []
        for k in range(n + 1):
            a = a_start - w * (NR - 1) * k / n
            pts.append((c0.x + math.cos(a) * r, c0.y + math.sin(a) * r))
        P.walk(p, pts, 1, NR, height_fn=gz)
        objs = p.objects()
        for o in objs:
            if o.type == "MESH":
                try:
                    sold_coll.objects.link(o)
                except RuntimeError:
                    pass
            for m in (getattr(o.data, "materials", None) or []) if o.data is not None else []:
                if m is not None:
                    E.hazify(m)
        rig = p.rig

        def spos(f, rig=rig):
            fc = {fc.array_index: fc for fc in C._fcurves(rig.animation_data.action) if fc.data_path == "location"}
            return Vector((fc[0].evaluate(f), fc[1].evaluate(f), 0))
        _cull(objs, spos, ctx, c0, margin=22.0)
    if __import__("os").environ.get("S12A_DEBUG"):
        for f in (1, 22, 44, 65, 87, 108):
            sc.frame_set(f)
            for o in bpy.data.objects:
                if "galea" in o.name:
                    print("DBG f%d %s parent=%s/%s at %s hide=%s" % (f, o.name, o.parent and o.parent.name, o.parent_bone,
                          tuple(round(c, 2) for c in o.matrix_world.translation), o.hide_render))
        sc.frame_set(1)

    # ------------------------------------------------------------------ light
    sky = G["sky"]
    sun_dir = Vector(sky["sun_dir"])
    recv = bpy.data.collections.new("s12a_rimrecv")
    for o in list(pack.objects) + list(sold_coll.objects):
        recv.objects.link(o)
    # warm rim from the low sun side (linked to animals + legs only)
    rim = C.light("SUN", (0, 0, 20), 3.2, color=(1.0, 0.4, 0.16), name="Rim", shadow=False)   # shadowless: -5 s/frame
    rd = (Vector((sun_dir.x, sun_dir.y, 0)).normalized() * math.cos(math.radians(12)) +
          Vector((0, 0, math.sin(math.radians(12))))).normalized()
    rim.rotation_euler = (-rd).to_track_quat("-Z", "Y").to_euler()
    rim.data.angle = math.radians(3.0)
    rim.light_linking.receiver_collection = recv
    # faint warm front bounce (just enough for the eyes / faces to read)
    fill = C.light("AREA", tuple(cam_base + Vector((0, 0, 0.5)) - fwd * 1.0), 9, color=(1.0, 0.62, 0.42), size=3.0,
                   target=tuple(cam_base + fwd * 4), name="Fill", shadow=False)
    fill.light_linking.receiver_collection = recv

    # ------------------------------------------------------------------ camera: low, handheld, slow counter-pan
    def cam_fn(f):
        d = _az_vec(_pan_az(ctx, f))
        loc = cam_base + C.shake(f, 0.018, 1.1, 3) + C.shake(f, 0.005, 4.0, 5)
        tgt = loc + d * 4.0 + Vector((0, 0, -4.0 * math.tan(math.radians(TILT)))) + C.shake(f, 0.05, 0.8, 11)
        roll = 2.5 * math.sin(f / 37.0) + 1.5
        return (loc, tgt, roll)
    C.animate_camera(cam, cam_fn, 1, NR)

    ctx.samples = 4
    ctx.render_opts.update({"volumetrics": "low"})
    ctx.interp = False
    ctx.post.update({"grade": "eclipse", "bloom": 0.3, "vignette": 0.3})
