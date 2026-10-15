"""s14b - Sword falls: "Deliver me from the sword, my precious life from the power of the dogs."

Ground level on the Golgotha plateau, moments after the light broke through (s14a). A Roman gladius lies
in the dust, receding from the lens; a soldier's hand (he crouches just out of frame) is still closed on
its grip. The edge of the cloud shadow creeps in from the left: golden light runs down the blade from the
tip to the hilt (it flares), and the hand opens and withdraws ("Deliver me from the sword"). The light
keeps spreading to the right, over the ground where the dogs of s12a lurk with glinting eyes; as it
touches them they wheel round and scatter into the remaining darkness ("...from the power of the dogs"),
the focus racking after them. Dust specks light up as the sun reaches them.

Light: the eclipse sky / ambience stays (dark), plus a golden sun from the s14a direction whose light is
masked by a huge camera-invisible 'cloud' plane high above; its ragged edge slides to the right -> a soft
moving shadow front on the ground. The soldier's body is invisible to the camera (it still casts its
shadow); a masked linked copy of the body shows only his forearm + hand.
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

SUN_AZ, SUN_EL = 165.0, 30.0          # core.sun convention, = s14a (the light that broke through)
VIEW_AZ = 60.0                        # compass az of the view (0 = +Y)
CAM_XY = (3.0, -4.6)
CAM_H = 0.28
LENS = 40.0
TILT = 13.0
GOLD = (1.0, 0.76, 0.46)


def _az(az):
    a = math.radians(az)
    return Vector((math.sin(a), math.cos(a), 0.0))


# ------------------------------------------------------------------------------------- custom pose
def _pose_hold(Ps, p, target=None, hand="grip", side="L", pron=150.0, flex=0.0, lean=30.0, **k):
    """Deep crouch (library crouch legs/spine) leaning forward from the hips, one palm at `target` (rig space)."""
    P._pose_crouch(Ps, p, throw=0.0)
    Ps.turn("root", bend=lean, frame_of="root")
    for s in "LR":
        Ps.turn("upperleg01." + s, bend=-lean, frame_of="root")
    if target is not None:
        lat = P._lateral(side)
        P._arm_ik(Ps, side, Vector(target), pole=(lat * 0.8 + Vector((0, 0.3, -0.6))).normalized(), pron=pron,
                  flex=flex, shrug=4)
        P._hand(Ps, side, hand)
    P._apply_head(Ps, "down", amount=0.7)


P.POSES["s14b_hold"] = _pose_hold
P.GROUNDED.add("s14b_hold")


def _arm_only(person, side="L"):
    """The camera sees only one arm: every object of the person is hidden from the camera and casts no
    shadow; linked copies of the body and of the garments, masked to the vertices weighted to the arm
    bones (upper arm .. fingertips, i.e. bare forearm/hand + mail/tunic sleeve), are camera-visible and
    cast the arm's shadow."""
    s = side
    keep = ["clavicle.", "shoulder01.", "upperarm01.", "upperarm02.", "lowerarm01.", "lowerarm02.", "wrist.",
            "metacarpal1.", "metacarpal2.", "metacarpal3.", "metacarpal4."]
    keep += ["finger%d-%d." % (i, j) for i in range(1, 6) for j in range(1, 4)]
    keep = set(k + s for k in keep)
    out = []
    for o in person.objects():
        if o.type not in ("MESH", "CURVES"):
            continue
        o.visible_camera = False
        o.visible_glossy = False
        o.visible_shadow = False
        if o.type != "MESH" or not any(m.type == "ARMATURE" for m in o.modifiers):
            continue
        gi = {g.index: g.name for g in o.vertex_groups}
        idx = [v.index for v in o.data.vertices
               if sum(g.weight for g in v.groups if gi.get(g.group) in keep) > 0.5]
        if len(idx) < 8:
            continue
        vg = o.vertex_groups.get("s14b_arm") or o.vertex_groups.new(name="s14b_arm")
        vg.add(idx, 1.0, "REPLACE")
        c = o.copy()
        o.users_collection[0].objects.link(c)
        c.name = o.name + "_arm"
        c.parent = o.parent
        c.matrix_parent_inverse = o.matrix_parent_inverse.copy()
        c.matrix_basis = o.matrix_basis.copy()
        for m in list(c.modifiers):
            if m.type == "MASK":
                c.modifiers.remove(m)
        mk = c.modifiers.new("ArmOnly", "MASK")
        mk.vertex_group = "s14b_arm"
        mk.threshold = 0.5
        c.visible_camera = True
        c.visible_glossy = True
        c.visible_shadow = False
        out.append(c)
    return out


# ------------------------------------------------------------------------------------- cloud blocker
def _blocker(name, size=9000.0, edge_amp=0.35, seed=3):
    """Huge horizontal plane covering local +X (from a ragged edge along local Y at x~0); camera-invisible,
    casts shadows only."""
    rnd = random.Random(seed)
    bm = bmesh.new()
    n = 400
    span = 200.0
    ys = [-span / 2 + span * i / n for i in range(n + 1)]
    ph = [rnd.uniform(0, 6.28) for _ in range(4)]
    edge = [edge_amp * (0.6 * math.sin(y / 9.0 + ph[0]) + 0.3 * math.sin(y / 4.3 + ph[1]) +
                        0.1 * math.sin(y / 2.1 + ph[2])) for y in ys]
    ys = [-size / 2] + ys + [size / 2]
    edge = [edge[0]] + edge + [edge[-1]]
    vin = [bm.verts.new((edge[i], y, 0.0)) for i, y in enumerate(ys)]
    vout = [bm.verts.new((size, y, 0.0)) for y in ys]
    for i in range(len(ys) - 1):
        bm.faces.new((vin[i], vin[i + 1], vout[i + 1], vout[i]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.visible_camera = False
    o.visible_diffuse = o.visible_glossy = o.visible_transmission = o.visible_volume_scatter = False
    o.data.materials.append(C.mat("cloud_block", (0.1, 0.1, 0.1), rough=1.0))
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
    Cx = Vector((CAM_XY[0], CAM_XY[1], 0.0))
    view = dict(loc=(Cx.x, Cx.y, 11.0), target=tuple(Cx + fwd * 30 + Vector((0, 0, 10))), lens=LENS - 4, margin=30)
    G = E.golgotha(ctx, mood="eclipse", view=view, grass=0.8, near_detail=1.0, dust=False)
    gz = lambda x, y: float(G["ground_z"](x, y))
    Cx.z = gz(Cx.x, Cx.y)
    cam_loc = Cx + Vector((0, 0, CAM_H))

    # ------------------------------------------------------------------ the sword (across the view, tip receding left)
    S = Cx + fwd * 0.80 - right * 0.17                     # blade centre (hilt right of centre, tip exits left)
    sdir = (-right * math.cos(math.radians(25)) + fwd * math.sin(math.radians(25))).normalized()   # hilt -> tip
    sword = A.load("gladius", loc=(0, 0, 0))
    yaw = math.atan2(sdir.y, sdir.x)
    # lie on the uneven ground: pitch to the slope between pommel and tip, lowest contact on the ground
    root0 = S - sdir * 0.355
    g_p = gz(root0.x, root0.y)
    tipxy = root0 + sdir * 0.71
    g_t = gz(tipxy.x, tipxy.y)
    pitch = math.atan2(g_t - g_p, 0.71)
    R = Matrix.Rotation(yaw, 4, "Z") @ Matrix.Rotation(-pitch, 4, "Y")
    bpy.context.view_layer.update()
    pts = []
    for o in A.children_recursive(sword):
        if o.type == "MESH":
            Ml = o.matrix_local if o.parent == sword else (sword.matrix_world.inverted() @ o.matrix_world)
            pts += [Ml @ v.co for v in list(o.data.vertices)[::7]]
    rz = -1e9
    for q in pts:
        w_ = R @ q
        gxy = Vector((root0.x + w_.x, root0.y + w_.y))
        rz = max(rz, gz(gxy.x, gxy.y) - w_.z)
    sword.matrix_world = Matrix.Translation((root0.x, root0.y, rz - 0.003)) @ R
    bpy.context.view_layer.update()
    grip_w = A.anchor(sword, "grip")
    tip_w = A.anchor(sword, "tip")
    blade_c = (grip_w + tip_w) * 0.5

    # ------------------------------------------------------------------ golden sun + moving cloud edge
    sun_dir = E._dir_from_az_el(SUN_AZ, SUN_EL).normalized() if hasattr(E, "_dir_from_az_el") else None
    gold = C.sun(elevation=SUN_EL, azimuth=SUN_AZ, energy=3.2, color=GOLD, angle=1.0)
    if sun_dir is None:
        el, az = math.radians(SUN_EL), math.radians(SUN_AZ)
        sun_dir = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
    gold.data.shadow_maximum_resolution = 0.002
    G["sky"]["sun"].data.use_shadow = False                # the dim eclipse sun: its shadows are invisible here
    mdir = (right * math.cos(math.radians(15)) + fwd * math.sin(math.radians(15))).normalized()   # left -> right
    hb = 30.0
    sxy = Vector((sun_dir.x, sun_dir.y, 0.0))
    off = sxy * (hb / max(0.05, sun_dir.z))
    blk = _blocker("CloudEdge")
    blk.rotation_euler = (0, 0, math.atan2(mdir.y, mdir.x))
    speed = 0.84 / fps                                     # m per frame along mdir
    t_tip = fr(p1s) + 5                                    # light reaches the tip of the blade
    s_tip = (tip_w - Cx).dot(mdir)

    def front(f):                                          # mdir coordinate (rel. to the camera) of the front
        return s_tip + (f - t_tip) * speed
    for f in (1, NR):
        p0 = Cx + mdir * front(f)
        blk.location = p0 + off + Vector((0, 0, hb))
        blk.keyframe_insert("location", frame=f)
    C._set_interp(blk, "location", "LINEAR")
    t_hilt = t_tip + ((grip_w - Cx).dot(mdir) - s_tip) / speed

    # ------------------------------------------------------------------ the soldier: crouched right of the lens
    sol = P.make_person("soldier", "SOLDIER", lod="hero", pose=None, expression=None, hair_strands=False)
    face = (fwd * 0.55 - right * 0.85).normalized()         # facing the sword from its right
    base = grip_w + right * 0.40 - fwd * 0.04
    sol.rig.location = (base.x, base.y, gz(base.x, base.y))
    sol.rig.rotation_euler = (0, 0, math.atan2(face.x, -face.y))
    bpy.context.view_layer.update()
    g0 = grip_w + Vector((0, 0, 0.018))
    rel0 = int(t_hilt) + 3                                 # fingers start to open once the light is on them
    rel1 = rel0 + 9
    up1 = rel1 + 20
    P.key_pose(sol, 1, "s14b_hold", target=g0, hand="grip")
    P.key_pose(sol, rel0, "s14b_hold", target=g0, hand="grip")
    P.key_pose(sol, rel1, "s14b_hold", target=g0 + Vector((0, 0, 0.025)), hand="open")
    P.key_pose(sol, up1, "s14b_hold", target=g0 + Vector((0, 0, 0.40)) + right * 0.18 - fwd * 0.04, hand="relaxed")
    arm_objs = _arm_only(sol, "L")
    for o in sol.objects():
        for m in (getattr(o.data, "materials", None) or []) if o.data is not None else []:
            if m is not None:
                E.hazify(m)

    # ------------------------------------------------------------------ dogs in the right background
    rnd = random.Random(7)
    # (along fwd, along right, heading deg rel. to facing the camera, tint, scale, glow)
    dogs = [(4.2, 0.35, 25, (-0.32, -0.48, -0.66), 0.92, 0.9),
            (5.4, 0.95, -15, (-0.66, -0.68, -0.7), 1.0, 1.0),
            (6.6, -0.2, 40, (-0.5, -0.54, -0.58), 0.88, 0.8),
            (7.4, 1.6, 5, (-0.32, -0.48, -0.66), 0.95, 0.9)]
    for i, (a, b, hd, tint, scl, glow) in enumerate(dogs):
        p0 = Cx + fwd * a + right * b
        f_hit = t_tip + ((p0 - Cx).dot(mdir) - s_tip) / speed + rnd.uniform(-2, 4)
        to_cam = Cx - p0
        h0 = math.degrees(math.atan2(to_cam.x, -to_cam.y)) + hd
        arm = A.animal("dog", "prowl", loc=(p0.x, p0.y, gz(p0.x, p0.y)), rot_z=h0, speed=1.1, scale=scl,
                       offset=i * 0.37, eye_glow=glow, tint=tint, start_frame=1)
        A.set_eye_glow(arm, glow, color=(1.0, 0.86, 0.5))
        flee = (right * 0.8 + fwd * 0.6).normalized()
        flee = Vector((flee.x + rnd.uniform(-0.2, 0.2), flee.y + rnd.uniform(-0.2, 0.2), 0)).normalized()
        v_prowl = A.ground_speed("dog", "prowl", 0, 1.1) * scl / fps
        v_run = A.ground_speed("dog", "run", 0, 1.0) * scl / fps
        pos = Vector(p0)
        head = math.radians(h0)
        turn_f = int(f_hit) + 2
        flee_h = math.atan2(flee.x, -flee.y)
        while flee_h - head > math.pi:
            flee_h -= 2 * math.pi
        while flee_h - head < -math.pi:
            flee_h += 2 * math.pi
        gone = None
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
            if gone is None and (pos - Cx).length > 16.0:
                gone = f
        A.play(arm, "run", start_frame=turn_f, replace=False, blend_in=5)
        if gone:                                           # far off-screen: stop rendering it
            for o in [arm] + A.children_recursive(arm):
                o.hide_render = False
                o.keyframe_insert("hide_render", frame=gone - 1)
                o.hide_render = True
                o.keyframe_insert("hide_render", frame=gone)

    # ------------------------------------------------------------------ glint (specular-only, linked to the blade)
    to_cam = (cam_loc - blade_c).normalized()
    refl = Vector((-to_cam.x, -to_cam.y, to_cam.z))          # mirror direction over a flat blade
    glint = C.light("AREA", tuple(blade_c + refl * 2.5), 0.0, color=(1.0, 0.84, 0.6), size=0.5,
                    target=tuple(blade_c), name="Glint", shadow=False)
    glint.data.diffuse_factor = 0.0
    glint.data.volume_factor = 0.0
    recv = bpy.data.collections.new("s14b_blade")
    for o in A.children_recursive(sword):
        recv.objects.link(o)
    glint.light_linking.receiver_collection = recv
    t_mid = int((t_tip + t_hilt) / 2)
    C.keys(glint.data, "energy", [(1, 0.0), (t_tip - 2, 0.0), (t_mid + 2, 40.0), (t_mid + 12, 10.0), (NR, 7.0)])

    # ------------------------------------------------------------------ camera: low, slow push, focus rack to the dogs
    rack0, rack1 = fr(p2s) - 4, fr(p2s) + 12
    d_grip = (grip_w - cam_loc).length

    def cam_fn(f):
        u = C.ease_in_out(min(1.0, ctx.u(f)))
        loc = cam_loc + fwd * (0.08 * u) + C.shake(f, 0.002, 0.6, 2)
        k = C.smoothstep((f - rack0) / float(rack1 - rack0))
        tgt = loc + fwd * 3.0 + Vector((0, 0, -3.0 * math.tan(math.radians(TILT - 1.5 * k)))) + right * (0.06 * k)
        fd = (d_grip - 0.08 * u) * (1 - k) + 5.3 * k
        return (loc, tgt, 0.0, LENS, fd)

    look0 = cam_loc + fwd * 3.0 + Vector((0, 0, -3.0 * math.tan(math.radians(TILT))))
    cam = C.camera(tuple(cam_loc), tuple(look0), lens=LENS, fstop=2.8, focus=d_grip, name="Cam")
    C.animate_camera(cam, cam_fn, 1, NR)

    ctx.samples = 5
    ctx.render_opts.update({"volumetrics": "low"})
    ctx.interp = False
    ctx.post.update({"grade": "eclipse", "bloom": 0.26, "vignette": 0.26,
                     "end": {"grade": "warm", "bloom": 0.36, "bloom_threshold": 0.62, "halation": 0.1}})
