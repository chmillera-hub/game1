"""s12a - Dogs surround: "Dogs surround me, a pack of villains encircles me;"

Darkness at midday on the Golgotha plateau (eclipse). The camera sits low in the dust (~0.45 m, the
height of a man thrown down) and looks out over the brow of the hill towards the dull red sun and
the hazy city. A pack of wild dogs (tawny jackal / dark pariah tints) prowls in a ring around the
lens, heads low, turning to stare into it with glinting eyes; closer to the lens the legs of Roman
soldiers (red tunic hems, studded apron straps, caligae) stride round the other way, cropped at the
waist by the frame top - faceless villains. Back light from the dim sun rims the animals and legs;
a faint front bounce lets the eyeshine read. Handheld drift + a slow counter-pan so the circling reads.
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
LOOK_AZ = 18.0                # compass az of the view (0 = +Y) - towards the eclipse sun (az 165 core = 15 deg E of N)
CAM_H = 0.45                  # lens height above the ground


def _az_vec(az):
    a = math.radians(az)
    return Vector((math.sin(a), math.cos(a), 0.0))


def build(ctx):
    NR = ctx.render_frames
    sc = bpy.context.scene
    fwd = _az_vec(LOOK_AZ)
    c0 = Vector((CAM_XY[0], CAM_XY[1], 0.0))
    view = dict(loc=(c0.x, c0.y, 11.0), target=tuple(c0 + fwd * 30 + Vector((0, 0, 10.5))), lens=24, margin=40)
    G = E.golgotha(ctx, mood="eclipse", view=view, grass=0.7, near_detail=1.0)
    ground = G["ground"]
    gz = lambda x, y: float(ground(x, y))
    cz = gz(c0.x, c0.y)
    cam_base = Vector((c0.x, c0.y, cz + CAM_H))

    # ------------------------------------------------------------------ dogs (CCW ring)
    pack = bpy.data.collections.new("s12a_pack")
    sc.collection.children.link(pack)
    # (radius, frame it crosses the view centre, action, speed, tint, scale, eye glow, cycle offset)
    # CCW seen from above = right-to-left through the frame
    dogs = [
        (3.0, 40, "prowl", 1.45, (-0.25, -0.42, -0.62), 0.92, 0.9, 0.0),
        (3.4, 95, "prowl", 1.35, (-0.6, -0.62, -0.65), 1.0, 1.0, 0.4),
        (3.2, -15, "prowl", 1.4, (-0.3, -0.45, -0.6), 0.88, 0.8, 0.9),
        (4.1, 70, "walk", 1.0, (-0.45, -0.5, -0.55), 0.95, 0.9, 0.2),
        (4.3, 10, "walk", 1.05, (-0.25, -0.42, -0.62), 0.9, 0.7, 1.3),
        (5.0, 55, "trot", 0.8, (-0.6, -0.62, -0.65), 1.02, 0.9, 0.6),
        (5.3, 120, "trot", 0.85, (-0.3, -0.45, -0.6), 0.9, 0.8, 1.7),
    ]
    view_az = math.atan2(fwd.y, fwd.x)       # math angle of the view direction
    cam_target = bpy.data.objects.new("s12a_eyes_target", None)
    sc.collection.objects.link(cam_target)
    arms = []
    for i, (r, fc, act, spd, tint, scl, glow, off) in enumerate(dogs):
        v = A.ground_speed("dog", act, 0, spd) * scl
        w = v / r / ctx.fps                                       # rad per frame
        a_start = view_az - w * (fc - 1)                          # CCW: angle increases with time
        n = 60
        pts = []
        for k in range(n + 1):
            a = a_start + w * (NR + 10) * k / n
            x, y = c0.x + math.cos(a) * r, c0.y + math.sin(a) * r
            pts.append((x, y, gz(x, y)))
        arm = A.animal("dog", act, speed=spd, scale=scl, path=pts, offset=off, eye_glow=glow, tint=tint,
                       start_frame=1, end_frame=NR)
        A.set_eye_glow(arm, glow, color=(1.0, 0.86, 0.5))
        # heads turn to stare at the lens
        pb = arm.pose.bones.get("head")
        if pb is not None:
            con = pb.constraints.new("DAMPED_TRACK")
            con.target = cam_target
            con.track_axis = "TRACK_Y"
            con.influence = 0.45
        for o in arm.children:
            if o.type == "MESH":
                pack.objects.link(o)
        arms.append(arm)

    # ------------------------------------------------------------------ soldiers (CW ring, close)
    sold_coll = bpy.data.collections.new("s12a_legs")
    sc.collection.children.link(sold_coll)
    base = P.make_person("legion0", "SOLDIER", lod="mid", pose=None, expression=None, hair_strands=False)
    people = [base]
    # (radius, speed m/s, frame it crosses the view centre) - CW seen from above = left-to-right in frame
    plan = [(2.05, 1.15, 22), (2.35, 1.05, 88), (2.2, 1.1, 150), (2.5, 1.0, -45)]
    for i in range(1, len(plan)):
        q = P.clone(base, loc=(0, 0, 0), name="legion%d" % i)
        # workaround: clone() does not carry the cached body analysis the pose engine needs (walk/pose)
        for k in ("_co", "_w", "_anat", "_lbs", "_ground_offset", "mats", "expr_keys"):
            if hasattr(base, k) and not hasattr(q, k + "__skip"):
                setattr(q, k, getattr(base, k))
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
        for o in p.objects():
            if o.type == "MESH":
                try:
                    sold_coll.objects.link(o)
                except RuntimeError:
                    pass
    for p in people:
        for o in p.objects():
            for m in (getattr(o.data, "materials", None) or []) if o.data is not None else []:
                if m is not None:
                    E.hazify(m)

    # ------------------------------------------------------------------ light
    sky = G["sky"]
    sun_dir = Vector(sky["sun_dir"])
    # rim: low warm sun-ish key from behind (linked to animals + legs only)
    rim = C.light("SUN", (0, 0, 20), 1.6, color=(1.0, 0.42, 0.18), name="Rim", shadow=True)
    rd = (Vector((sun_dir.x, sun_dir.y, 0)).normalized() * math.cos(math.radians(14)) +
          Vector((0, 0, math.sin(math.radians(14))))).normalized()
    rim.rotation_euler = (-rd).to_track_quat("-Z", "Y").to_euler()
    rim.data.angle = math.radians(3.0)
    recv = bpy.data.collections.new("s12a_rimrecv")
    for o in list(pack.objects) + list(sold_coll.objects):
        recv.objects.link(o)
    rim.light_linking.receiver_collection = recv
    # faint warm front bounce (makes the eyes / faces read in the dark)
    fill = C.light("AREA", tuple(cam_base + Vector((0, 0, 0.6)) - fwd * 1.0), 60, color=(1.0, 0.6, 0.4), size=3.0,
                   target=tuple(cam_base + fwd * 4), name="Fill", shadow=False)
    fill.light_linking.receiver_collection = recv

    # low ground dust drifting through the pack
    E.fog_volume(tuple(cam_base + fwd * 6 + Vector((0, 0, 0.2))), (18, 18, 1.6), 0.05, (0.55, 0.32, 0.2), 0.5,
                 noise_scale=0.5, noise_amount=0.9, height_falloff=1.4, name="GroundDust",
                 wind=tuple(_az_vec(LOOK_AZ - 90) * 1.2))

    # ------------------------------------------------------------------ camera: low, handheld, slow counter-pan
    def cam_fn(f):
        u = C.ease_in_out(min(1.0, ctx.u(f)))
        az = LOOK_AZ - 7.0 + 14.0 * u                 # pans right, against the dogs' right-to-left circling
        d = _az_vec(az)
        loc = cam_base + C.shake(f, 0.018, 1.1, 3) + C.shake(f, 0.006, 4.0, 5)
        tgt = loc + d * 4.0 + Vector((0, 0, -0.42)) + C.shake(f, 0.05, 0.8, 11)
        roll = 3.0 * math.sin(f / 37.0) + 1.5
        return (loc, tgt, roll)

    cam = C.camera(tuple(cam_base), tuple(cam_base + fwd * 4), lens=26, fstop=2.8, focus=3.2, name="Cam")
    C.animate_camera(cam, cam_fn, 1, NR)
    cam_target.parent = cam
    cam_target.location = (0, 0, 0)

    ctx.samples = 6
    ctx.render_opts.update({"volumetrics": "low"})
    ctx.interp = False
    ctx.post.update({"grade": "eclipse", "bloom": 0.3, "vignette": 0.3})
