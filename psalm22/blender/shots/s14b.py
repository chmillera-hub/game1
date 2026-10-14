"""s14b - Sword falls: "Deliver me from the sword, my precious life from the power of the dogs."

Ground level on the Golgotha plateau, moments after the light broke through (s14a). A Roman gladius
lies in the dust, a crouching soldier's hand still closed on its grip. The edge of the cloud shadow
slides in from the left: golden light floods across the ground, reaches the blade (it flares) and the
hand opens and withdraws ("Deliver me from the sword"). The light keeps spreading towards the right
background where the dogs of s12a lurk with glinting eyes; as it touches them they wheel round and
scatter into the remaining darkness ("...from the power of the dogs"), focus racking after them.
Dust motes light up as the sun reaches them.

Light: base = eclipse ambience mid-way to the golden sky (continues the s14a sky transition); a golden
sun (s14a direction) whose light is masked by an invisible, camera-hidden cloud plane high above with a
ragged edge that slides across the plateau -> a soft, moving shadow front on the ground.
"""
import math
import random
import bpy
import bmesh
from mathutils import Vector, Matrix
from lib import core as C
from lib import env as E
from lib import assets as A
from lib import characters as P

SUN_AZ, SUN_EL = 165.0, 30.0          # = s14a (the light that broke through)
VIEW_AZ = 60.0                        # compass az of the view (0 = +Y)
SWORD_XY = (3.6, -4.2)
CAM_H = 0.27
GOLD = (1.0, 0.78, 0.5)


def _az(az):
    a = math.radians(az)
    return Vector((math.sin(a), math.cos(a), 0.0))


# ------------------------------------------------------------------------------------- custom pose
def _pose_hold(Ps, p, target=None, hand="grip", side="L", pron=150.0, flex=0.0, **k):
    """Deep crouch (library crouch legs/spine) with one palm at `target` (rig space)."""
    P._pose_crouch(Ps, p, throw=0.0)
    if target is not None:
        T = Vector(target)
        lat = P._lateral(side)
        P._arm_ik(Ps, side, T, pole=(lat * 0.8 + Vector((0, 0.3, -0.6))).normalized(), pron=pron, flex=flex,
                  shrug=4)
        P._hand(Ps, side, hand)
    P._apply_head(Ps, "down", amount=0.7)


P.POSES["s14b_hold"] = _pose_hold
P.GROUNDED.add("s14b_hold")


# ------------------------------------------------------------------------------------- cloud blocker
def _blocker(name, size=600.0, edge_amp=3.0, seed=3):
    """Big horizontal plane (+X half-space from x=0) with a ragged edge along local Y; camera-invisible,
    casts shadows only. Local +X = the shadowed (cloud) side."""
    rnd = random.Random(seed)
    bm = bmesh.new()
    n = 160
    ys = [-size / 2 + size * i / n for i in range(n + 1)]
    # ragged edge: sum of sines
    ph = [rnd.uniform(0, 6.28) for _ in range(4)]
    edge = [edge_amp * (0.55 * math.sin(y / 9.0 + ph[0]) + 0.3 * math.sin(y / 3.7 + ph[1]) +
                        0.15 * math.sin(y / 1.6 + ph[2])) for y in ys]
    vin = [bm.verts.new((edge[i], y, 0.0)) for i, y in enumerate(ys)]
    vout = [bm.verts.new((size, y, 0.0)) for y in ys]
    for i in range(n):
        bm.faces.new((vin[i], vin[i + 1], vout[i + 1], vout[i]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.visible_camera = False
    o.visible_diffuse = o.visible_glossy = o.visible_transmission = o.visible_volume_scatter = False
    m = C.mat("cloud_block", (0.1, 0.1, 0.1), rough=1.0)
    o.data.materials.append(m)
    return o


def build(ctx):
    NR = ctx.render_frames
    fps = ctx.fps
    sc = bpy.context.scene
    fr = lambda s: int(round(ctx.frame(s)))
    p1s, p1e = ctx.phrases[0]["start"], ctx.phrases[0]["end"]
    p2s, p2e = ctx.phrases[1]["start"], ctx.phrases[1]["end"]

    fwd = _az(VIEW_AZ)
    right = Vector((fwd.y, -fwd.x, 0.0))
    S = Vector((SWORD_XY[0], SWORD_XY[1], 0.0))
    view = dict(loc=(S.x - fwd.x, S.y - fwd.y, 11.0), target=tuple(S + fwd * 30 + Vector((0, 0, 10))), lens=32,
                margin=30)
    G = E.golgotha(ctx, mood="eclipse", view=view, grass=0.8, near_detail=1.0)
    gz = lambda x, y: float(G["ground_z"](x, y))
    S.z = gz(S.x, S.y)

    # ------------------------------------------------------------------ sky: continue the s14a transition
    disk_a = dict(E.SKY_PRESETS["eclipse"]["sun_disk"], el=SUN_EL)
    over_b = dict(sun_az=SUN_AZ, sun_el=SUN_EL, key=0.22, strength=0.45, sun_energy=1.6, tint=(1.0, 0.84, 0.6),
                  sat=1.1, sun_tint=(1.0, 0.78, 0.5), sun_angle=1.0, haze_density=0.0009,
                  haze_tint=(1.0, 0.92, 0.8), exposure=0.3, grade="warm", clouds=0.5,
                  cloud_opts=dict(color=(0.95, 0.78, 0.55), shadow=(0.3, 0.2, 0.14), opacity=0.85, sun_glow=1.2,
                                  speed=(9.0, 3.0)),
                  sun_disk=dict(el=SUN_EL, size=1.0, color=(1.0, 0.88, 0.66), strength=40.0, glow=0.2))
    m0, m1 = 0.40, 0.72                          # transition amount at the first / last frame
    span = (NR - 1) / (m1 - m0)
    f0 = 1 - m0 * span
    f1 = f0 + span
    T = E.sky_transition(ctx, "eclipse", "eclipse", f0, f1, over_a=dict(sun_az=SUN_AZ, sun_el=SUN_EL, sun_disk=disk_a),
                         over_b=over_b, ease=False)
    sun = T["sun"]
    sun_dir = Vector(T["b"]["sun_dir"]).normalized()
    # the transition sun lights everything uniformly -> it becomes the golden key, masked by the cloud plane
    ad = sun.data.animation_data
    if ad and ad.action:
        for fc in C._fcurves(ad.action):
            if fc.data_path == "energy":
                for kp in fc.keyframe_points:
                    kp.co[1] = kp.handle_left[1] = kp.handle_right[1] = 3.2
            elif fc.data_path == "color":
                for kp in fc.keyframe_points:
                    kp.co[1] = kp.handle_left[1] = kp.handle_right[1] = GOLD[fc.array_index]
    sun.data.energy = 3.2
    sun.data.color = GOLD
    sun.data.angle = math.radians(2.5)

    # ------------------------------------------------------------------ moving shadow front (cloud edge)
    mdir = (right * math.cos(math.radians(40)) + fwd * math.sin(math.radians(40))).normalized()
    hb = 32.0                                        # cloud plane height above the sword
    sxy = Vector((sun_dir.x, sun_dir.y, 0.0))
    off = sxy * (hb / math.tan(math.asin(sun_dir.z)) / max(1e-6, sxy.length))
    blk = _blocker("CloudEdge")
    blk.rotation_euler = (0, 0, math.atan2(mdir.y, mdir.x))
    t_sword = fr(p1s) + 14                           # the light reaches the blade
    speed = 1.9 / fps                                # m per frame along mdir

    def front(f):
        return (f - t_sword) * speed
    for f in (1, NR):
        p0 = S + mdir * front(f)
        blk.location = p0 + off + Vector((0, 0, hb))
        blk.keyframe_insert("location", frame=f)
    C._set_interp(blk, "location", "LINEAR")

    # ------------------------------------------------------------------ the sword
    sdir = (-right * math.cos(math.radians(35)) + fwd * math.sin(math.radians(35))).normalized()   # hilt -> tip
    hilt = S - sdir * 0.26
    sword = A.load("gladius", loc=(0, 0, 0))
    yaw = math.atan2(sdir.y, sdir.x)
    sword.rotation_euler = (0, 0, yaw)
    sword.location = (hilt.x - sdir.x * 0.09, hilt.y - sdir.y * 0.09, S.z - 0.004)
    bpy.context.view_layer.update()
    grip_w = A.anchor(sword, "grip")

    # ------------------------------------------------------------------ the soldier (crouched, right of the hilt)
    sol = P.make_person("soldier", "SOLDIER", lod="hero", pose=None, expression=None, hair_strands=False)
    face = fwd * 0.95 - right * 0.3                  # crouched right of the camera, facing into the shot
    face.normalize()
    base = S + right * 0.62 - fwd * 0.40
    sol.rig.location = (base.x, base.y, gz(base.x, base.y))
    sol.rig.rotation_euler = (0, 0, math.atan2(face.x, -face.y))
    bpy.context.view_layer.update()
    g0 = grip_w + Vector((0, 0, 0.012))
    rel0 = fr(p1s) + 16                              # fingers start to open
    rel1 = rel0 + 10
    up0 = rel1 + 2
    up1 = up0 + 18
    P.key_pose(sol, 1, "s14b_hold", target=g0, hand="grip")
    P.key_pose(sol, rel0, "s14b_hold", target=g0, hand="grip")
    P.key_pose(sol, rel1, "s14b_hold", target=g0 + Vector((0, 0, 0.02)), hand="open")
    P.key_pose(sol, up1, "s14b_hold", target=g0 + Vector((0, 0, 0.55)) - face * 0.2 + right * 0.15, hand="relaxed")
    for o in sol.objects():
        for m in (getattr(o.data, "materials", None) or []) if o.data is not None else []:
            if m is not None:
                E.hazify(m)

    # ------------------------------------------------------------------ dogs in the right background
    rnd = random.Random(7)
    pack = []
    # (along fwd, along right, heading deg rel to facing the camera, tint, scale, glow)
    dogs = [(4.2, 0.9, 20, (-0.25, -0.42, -0.62), 0.92, 0.9),
            (5.4, 1.6, -10, (-0.6, -0.62, -0.65), 1.0, 1.0),
            (6.3, 0.2, 35, (-0.3, -0.45, -0.6), 0.88, 0.8),
            (7.5, 1.9, 5, (-0.45, -0.5, -0.55), 0.95, 0.9)]
    cam_xy = S - fwd * 0.95 + right * 0.04
    for i, (a, b, hd, tint, scl, glow) in enumerate(dogs):
        p0 = S + fwd * a + right * b
        s_at = (p0 - S).dot(mdir)
        f_hit = t_sword + s_at / speed + rnd.uniform(-3, 4)       # frame the light reaches it
        to_cam = (cam_xy - p0)
        h0 = math.degrees(math.atan2(to_cam.x, -to_cam.y)) + hd    # heading: roughly facing the camera/sword
        arm = A.animal("dog", "prowl", loc=(p0.x, p0.y, gz(p0.x, p0.y)), rot_z=h0, speed=1.2, scale=scl,
                       offset=i * 0.37, eye_glow=glow, tint=tint, start_frame=1)
        A.set_eye_glow(arm, glow, color=(1.0, 0.86, 0.5))
        # root motion: prowl slowly forward, wheel away from the light and run off to the right/back
        flee = (right * 0.75 + fwd * 0.66).normalized()
        flee = Vector((flee.x + rnd.uniform(-0.25, 0.25), flee.y + rnd.uniform(-0.25, 0.25), 0)).normalized()
        v_prowl = A.ground_speed("dog", "prowl", 0, 1.2) * scl / fps
        v_run = A.ground_speed("dog", "run", 0, 1.0) * scl / fps
        hv = Vector((math.sin(math.radians(h0)), -math.cos(math.radians(h0)), 0))   # forward of the animal
        pos = Vector(p0)
        head = math.radians(h0)
        turn_f = int(f_hit) + 2
        flee_h = math.atan2(flee.x, -flee.y)
        while flee_h - head > math.pi:
            flee_h -= 2 * math.pi
        while flee_h - head < -math.pi:
            flee_h += 2 * math.pi
        for f in range(1, NR + 1):
            if f < turn_f:
                v, h = v_prowl, head
            else:
                k = min(1.0, (f - turn_f) / 7.0)
                h = head + (flee_h - head) * C.smoothstep(k)
                v = v_prowl + (v_run - v_prowl) * C.smoothstep(min(1.0, (f - turn_f) / 10.0))
            d = Vector((math.sin(h), -math.cos(h), 0))
            if f > 1:
                pos = pos + d * v
            arm.location = (pos.x, pos.y, gz(pos.x, pos.y))
            arm.rotation_euler = (0, 0, h)
            arm.keyframe_insert("location", frame=f)
            arm.keyframe_insert("rotation_euler", frame=f)
        st = A.play(arm, "run", start_frame=turn_f, replace=False, blend_in=5)
        pack.append(arm)

    # ------------------------------------------------------------------ dust motes in the air near the ground
    E.dust_motes(center=tuple(S + fwd * 1.8 + Vector((0, 0, 0.5))), size=(4.0, 5.0, 1.0), count=900, radius=0.0016,
                 color=(1.0, 0.85, 0.6), emission=0.0, drift=tuple(mdir * 0.12 + Vector((0, 0, 0.02))),
                 turbulence=0.35, seed=4, name="Motes")

    # ------------------------------------------------------------------ glint (specular-only, linked to the blade)
    cam_loc = Vector((cam_xy.x, cam_xy.y, S.z + CAM_H))
    to_cam = (cam_loc - S).normalized()
    refl = Vector((-to_cam.x, -to_cam.y, to_cam.z))          # mirror direction over a flat blade
    glint = C.light("AREA", tuple(S + refl * 3.0), 0.0, color=(1.0, 0.86, 0.62), size=0.6, target=tuple(S),
                    name="Glint", shadow=False)
    glint.data.diffuse_factor = 0.0
    glint.data.volume_factor = 0.0
    recv = bpy.data.collections.new("s14b_blade")
    for o in sword.children:
        recv.objects.link(o)
    glint.light_linking.receiver_collection = recv
    C.keys(glint.data, "energy", [(1, 0.0), (t_sword - 3, 0.0), (t_sword + 3, 90.0), (t_sword + 14, 25.0), (NR, 18.0)])

    # ------------------------------------------------------------------ camera: low, slow push, focus rack to the dogs
    rack0, rack1 = fr(p2s) + 2, fr(p2s) + 16
    look0 = S + Vector((0, 0, 0.03)) + fwd * 0.6
    def cam_fn(f):
        u = C.ease_in_out(min(1.0, ctx.u(f)))
        loc = cam_loc + fwd * (0.12 * u) + C.shake(f, 0.004, 0.6, 2)
        tgt = look0 + fwd * (0.4 * C.smoothstep((f - rack0) / 30.0)) + Vector((0, 0, 0.0))
        k = C.smoothstep((f - rack0) / float(rack1 - rack0))
        fd = (S - loc).length * (1 - k) + 4.6 * k
        return (loc, tgt, 0.0, 30, fd)

    cam = C.camera(tuple(cam_loc), tuple(look0), lens=30, fstop=2.8, focus=(S - cam_loc).length, name="Cam")
    C.animate_camera(cam, cam_fn, 1, NR)

    ctx.samples = 6
    ctx.render_opts.update({"volumetrics": "low"})
    ctx.interp = False
    ctx.post.update({"grade": "eclipse", "bloom": 0.26, "vignette": 0.26,
                     "end": {"grade": "warm", "bloom": 0.38, "bloom_threshold": 0.62, "halation": 0.1}})
