"""s13b - Casting lots: "They divide my clothes among them and cast lots for my garment."

At the foot of the centre cross, in the eclipse darkness, three Roman soldiers kneel round a dark wool
blanket spread on the rocky ground. A torch planted off-screen left throws warm, flickering light across
it (the only warm light in the dim red-brown day). Camera: low three-quarter top view over the blanket,
hands / forearms / knees of the soldiers framing the folded cream tunic in the middle.

  * "They divide my clothes among them": the soldier on the right drags the folded madder mantle off
    the blanket to his knees; the left one already has the sash.
  * "and cast lots for my garment": the far soldier, who has been shaking the knucklebones in his fist,
    throws - two bone dice and two astragali tumble in slow motion across the seamless tunic and come
    to rest on the blanket (Bullet rigid-body sim run inside build() at time scale 0.3, baked to keys).
  * The winner on the left snatches the tunic up and away; the dice lie on the empty blanket.
"""
import math
import random
import bpy
import bmesh
import numpy as np
from mathutils import Vector, Matrix, Euler, noise
from lib import core as C
from lib import env as E
from lib import assets as A
from lib import characters as P
from lib import wardrobe as W

CLOTH_C = (0.05, -0.95)      # blanket centre (world xy): in the keep-out area in front of the centre cross
SLOWMO = 0.3


# ============================================================================================ geometry
def _box_uv(me, scale=1.0):
    """Box-projected UVs in metres (the wardrobe fabric material expects metric UVs)."""
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uv = me.uv_layers[0].data
    for poly in me.polygons:
        n = poly.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            if ax == 2:
                uv[li].uv = (co.x * scale, co.y * scale)
            elif ax == 1:
                uv[li].uv = (co.x * scale, co.z * scale)
            else:
                uv[li].uv = (co.y * scale, co.z * scale)


def folded_cloth(name, w, d, h, layers=4, seed=0, color="cream", fabric="linen", wrinkle=1.0, coll=None):
    """A folded garment lying on the ground: rounded slab (fold rolls on the long sides), soft layer grooves
    on the sides, gentle sag and creases on top. Origin at the bottom centre, size w (x) x d (y) x h."""
    rnd = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=22, use_grid_fill=True)
    r = h * 0.5
    ix, iy = w / 2 - r, d / 2 - r * 0.6
    so = rnd.uniform(0, 100)
    for v in bm.verts:
        p = Vector((v.co.x * w, v.co.y * d, v.co.z * h))
        q = Vector((max(-ix, min(ix, p.x)), max(-iy, min(iy, p.y)), 0.0))
        dv = p - q
        if dv.length < 1e-9:
            dv = Vector((0, 0, 1))
        rr = r
        # layer grooves on the sides (between the folded layers)
        side = min(1.0, max(0.0, (Vector((dv.x, dv.y, 0)).length / max(1e-6, dv.length)) - 0.3) / 0.7)
        rr *= 1.0 - 0.06 * side * (0.5 + 0.5 * math.cos((p.z / h + 0.5) * layers * 2 * math.pi))
        if abs(dv.y) > abs(dv.x) * 1.4:            # the open (short) ends are flatter / less round
            dv.y *= 0.7
        p = q + dv.normalized() * rr
        p.z += r
        # sag in the middle + soft lumps + creases on top
        top = max(0.0, (p.z - h * 0.6) / (h * 0.4))
        lump = noise.noise(Vector((p.x * 9 + so, p.y * 9, 0.3))) * 0.0035 * wrinkle
        crease = noise.noise(Vector((p.x * 3 + so, p.y * 22, 1.7))) * 0.002 * wrinkle * top
        crease += noise.noise(Vector((p.x * 26 + so, p.y * 4, 5.1))) * 0.0012 * wrinkle * top
        p.z += (lump + crease) * (0.3 + 0.7 * top) - 0.006 * top * (1 - (2 * p.x / w) ** 2) * (1 - (2 * p.y / d) ** 2)
        p.z = max(0.0, p.z)
        v.co = p
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for poly in me.polygons:
        poly.use_smooth = True
    _box_uv(me)
    o = bpy.data.objects.new(name, me)
    (coll or bpy.context.scene.collection).objects.link(o)
    o.data.materials.append(W.fabric_material(fabric))
    o.color = (*W.color(color), 1.0)
    wa = me.attributes.new("wear", "FLOAT", "POINT")
    wa.data.foreach_set("value", [0.25] * len(me.vertices))
    return o


def blanket(name, center, w, d, gzf, res=0.012, seed=2, color="dark_brown", coll=None):
    """Wool blanket spread on the ground (follows the terrain + rumpled folds)."""
    nx, ny = int(w / res), int(d / res)
    xs = np.linspace(-w / 2, w / 2, nx + 1)
    ys = np.linspace(-d / 2, d / 2, ny + 1)
    X, Y = np.meshgrid(xs, ys)
    rnd = random.Random(seed)
    so = rnd.uniform(0, 50)
    V = []
    cx, cy = center
    for j in range(ny + 1):
        for i in range(nx + 1):
            x, y = X[j, i], Y[j, i]
            z = gzf(cx + x, cy + y) + 0.007
            e = min(1.0, min(w / 2 - abs(x), d / 2 - abs(y)) / 0.12)     # rumples stronger near the edges
            z += 0.006 * noise.noise(Vector((x * 2.5 + so, y * 2.5, 0.5)))
            z += 0.004 * (1.2 - e) * abs(noise.noise(Vector((x * 7 + so, y * 3, 2.5))))
            z += 0.0025 * noise.noise(Vector((x * 4 + so, y * 14, 4.5)))
            V.append((x, y, z))
    F = []
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            F.append((a, a + 1, a + nx + 2, a + nx + 1))
    me = bpy.data.meshes.new(name)
    me.from_pydata(V, [], F)
    me.update()
    for poly in me.polygons:
        poly.use_smooth = True
    uvl = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uvl.data[li].uv = (co.x, co.y)
    o = bpy.data.objects.new(name, me)
    (coll or bpy.context.scene.collection).objects.link(o)
    o.location = (cx, cy, 0.0)
    so_ = o.modifiers.new("thick", "SOLIDIFY")
    so_.thickness = 0.004
    so_.offset = -1.0
    o.data.materials.append(W.fabric_material("wool"))
    o.color = (*W.color(color), 1.0)
    wa = me.attributes.new("wear", "FLOAT", "POINT")
    wa.data.foreach_set("value", [0.5] * len(me.vertices))
    return o


# ============================================================================================ poses
def _pose_kneel2(Ps, p, lean=22.0, seat=0.5, rt=None, lt=None, rhand="relaxed", lhand="relaxed",
                 rpron=95.0, lpron=95.0, head="down", look=None, twist=0.0, **k):
    """Kneeling on both knees, sitting back towards the heels (seat 0..1), torso leaning forward;
    either hand to a target (rig space) or resting on the thigh."""
    h = p.height / 1.75
    for s in "LR":
        lat = P._lateral(s)
        t = Vector((lat.x * 0.08, -0.12 - 0.8 * seat, -1 + 0.45 * seat))
        sh = P._leg(Ps, s, t, P.FWD + lat * 0.08, 100 + 45 * seat)
        P._flatten_foot_to(Ps, s, sh)
    P._spine_bend(Ps, bend=lean, twist=twist)
    for s, T, hs, pr in (("R", rt, rhand, rpron), ("L", lt, lhand, lpron)):
        lat = P._lateral(s)
        if T is None:
            knee = Ps.head("lowerleg01." + s)
            T = knee + Vector((lat.x * 0.02, 0.06, 0.05))
            pr = 95
        P._arm_ik(Ps, s, Vector(T), pole=(lat * 0.7 + Vector((0, 0.35, -0.6))).normalized(), pron=pr, shrug=4)
        P._hand(Ps, s, hs)
    P._apply_head(Ps, head, amount=0.6)


P.POSES["s13b_kneel"] = _pose_kneel2
P.GROUNDED.add("s13b_kneel")


def _kp(person, f, **kw):
    """key_pose wrapper converting world targets for rt / lt (the generic converter handles 'target' only)."""
    for key in ("rt", "lt"):
        if kw.get(key) is not None:
            kw[key] = person.rig.matrix_world.inverted() @ Vector(kw[key])
    return P.key_pose(person, f, "s13b_kneel", **kw)


def _child_of_hand(obj, person, bone, frame, f_on):
    """Make obj follow a hand bone from frame f_on on (Child Of, inverse computed at f_on)."""
    sc = bpy.context.scene
    sc.frame_set(f_on)
    bpy.context.view_layer.update()
    con = obj.constraints.new("CHILD_OF")
    con.target = person.rig
    con.subtarget = bone
    pm = person.rig.matrix_world @ person.rig.pose.bones[bone].matrix
    con.inverse_matrix = pm.inverted()
    con.set_inverse_pending = False
    con.influence = 0.0
    con.keyframe_insert("influence", frame=f_on - 1)
    con.influence = 1.0
    con.keyframe_insert("influence", frame=f_on)
    ad = obj.animation_data
    for fc in C._fcurves(ad.action):
        if "influence" in fc.data_path:
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"
    sc.frame_set(1)
    return con


# ============================================================================================ dice sim
def dice_sim(ctx, bodies, colliders, f_rel, n_frames, launch, seed=1):
    """Bullet sim at SLOWMO time scale from f_rel; bodies = [(obj, start_matrix, lin_vel, ang_vel)].
    Velocities in real m/s and rad/s. Returns {obj: [(frame, matrix_world), ...]} and removes the sim."""
    sc = bpy.context.scene
    with bpy.context.temp_override(scene=sc):
        bpy.ops.rigidbody.world_add()
    rbw = sc.rigidbody_world
    rbw.time_scale = SLOWMO
    rbw.substeps_per_frame = 40
    rbw.solver_iterations = 30
    rbw.point_cache.frame_start = f_rel - 3
    rbw.point_cache.frame_end = f_rel + n_frames
    dt = SLOWMO / ctx.fps
    for o in colliders:
        with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o]):
            bpy.ops.rigidbody.object_add(type="PASSIVE")
        o.rigid_body.collision_shape = "MESH"
        o.rigid_body.mesh_source = "FINAL"
        o.rigid_body.friction = 0.9
        o.rigid_body.restitution = 0.25
        o.rigid_body.collision_margin = 0.0005
    for (o, M0, v, w) in bodies:
        with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o]):
            bpy.ops.rigidbody.object_add(type="ACTIVE")
        rb = o.rigid_body
        rb.collision_shape = "CONVEX_HULL"
        rb.mass = 0.008
        rb.friction = 0.6
        rb.restitution = 0.35
        rb.collision_margin = 0.0003
        rb.linear_damping = 0.05
        rb.angular_damping = 0.15
        rb.use_deactivation = False
        o.rotation_mode = "QUATERNION"
        # kinematic launch: two keyed frames moving at the release velocity, then dynamic
        loc0, rot0 = M0.to_translation(), M0.to_quaternion()
        for k, f in enumerate((f_rel - 2, f_rel - 1, f_rel)):
            tt = (k - 2) * dt
            o.location = loc0 + Vector(v) * tt + Vector((0, 0, -0.5 * 9.81 * tt * tt))
            ax = Vector(w)
            q = rot0.copy()
            if ax.length > 1e-6:
                from mathutils import Quaternion
                q = Quaternion(ax.normalized(), ax.length * tt) @ rot0
            o.rotation_quaternion = q
            o.keyframe_insert("location", frame=f)
            o.keyframe_insert("rotation_quaternion", frame=f)
            rb.kinematic = True
            rb.keyframe_insert("kinematic", frame=f)
        rb.kinematic = False
        rb.keyframe_insert("kinematic", frame=f_rel + 1)
        for fc in C._fcurves(o.animation_data.action):
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
    out = {o: [] for (o, _, _, _) in bodies}
    for f in range(f_rel - 3, f_rel + n_frames + 1):
        sc.frame_set(f)
        for (o, _, _, _) in bodies:
            out[o].append((f, o.matrix_world.copy()))
    # remove the sim, keep the motion as keys
    for (o, _, _, _) in bodies:
        o.animation_data_clear()
        with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o]):
            bpy.ops.rigidbody.object_remove()
    for o in colliders:
        with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o]):
            bpy.ops.rigidbody.object_remove()
    coll = rbw.collection
    with bpy.context.temp_override(scene=sc):
        bpy.ops.rigidbody.world_remove()
    if coll is not None and coll.name in bpy.data.collections:
        bpy.data.collections.remove(coll)
    sc.frame_set(1)
    return out


# ============================================================================================ build
def build(ctx):
    NR = ctx.render_frames
    sc = bpy.context.scene
    fr = lambda s: int(round(ctx.frame(s)))
    p1s, p1e = ctx.phrases[0]["start"], ctx.phrases[0]["end"]
    p2s, p2e = ctx.phrases[1]["start"], ctx.phrases[1]["end"]

    Cc = Vector((CLOTH_C[0], CLOTH_C[1], 0.0))
    cam_loc0 = Cc + Vector((0.02, -0.80, 0.0))
    view = dict(loc=(cam_loc0.x, cam_loc0.y, 11.8), target=(Cc.x, Cc.y + 3, 11.0), lens=30, margin=60)
    G = E.golgotha(ctx, mood="eclipse", view=view, grass=0.8, near_detail=1.0, dust=False)
    gz = lambda x, y: float(G["ground_z"](x, y))
    Cc.z = gz(Cc.x, Cc.y)

    # ------------------------------------------------------------------ cloths
    props = bpy.data.collections.new("s13b_props")
    sc.collection.children.link(props)
    bl = blanket("Blanket", (Cc.x, Cc.y), 1.25, 1.0, gz, color=(0.30, 0.20, 0.14), coll=props)
    bpy.context.view_layer.update()

    def top_z(x, y):
        """Blanket surface height (raycast against the blanket mesh)."""
        dg = bpy.context.evaluated_depsgraph_get()
        ob = bl.evaluated_get(dg)
        mi = ob.matrix_world.inverted()
        o_ = mi @ Vector((x, y, 50.0))
        hit, loc, nrm, idx = ob.ray_cast(o_, Vector((0, 0, -1)))
        return (ob.matrix_world @ loc).z if hit else Cc.z + 0.01

    tun_c = Cc + Vector((-0.02, 0.06, 0))
    tunic = folded_cloth("Tunic", 0.36, 0.29, 0.055, layers=5, seed=3, color="cream", fabric="linen", coll=props)
    tunic.location = (tun_c.x, tun_c.y, top_z(tun_c.x, tun_c.y) - 0.002)
    tunic.rotation_euler = (0, 0, math.radians(7))
    man_c = Cc + Vector((0.38, 0.12, 0))
    mantle = folded_cloth("Mantle", 0.30, 0.34, 0.07, layers=4, seed=8, color="madder", fabric="wool", coll=props)
    mantle.location = (man_c.x, man_c.y, top_z(man_c.x, man_c.y) - 0.002)
    mantle.rotation_euler = (0, 0, math.radians(-12))
    bpy.context.view_layer.update()

    # ------------------------------------------------------------------ dice (slow-motion sim, baked to keys)
    f_rel = fr(p2s) + 5                         # the fist opens over the tunic
    dice = []
    specs = [("dice", 0, dict(top=3)), ("dice", 2, dict(top=5)), ("astragalus", 1, {}), ("astragalus", 3, {})]
    rnd = random.Random(ctx.seed)
    rel_pt = tun_c + Vector((0.0, 0.26, 0.0))
    rel_pt.z = tunic.location.z + 0.20
    bodies = []
    for i, (nm, var, opt) in enumerate(specs):
        root = A.load(nm, loc=(0, 0, 0), variant=var, coll=props, **opt)
        mesh = next(o for o in A.children_recursive(root) if o.type == "MESH")
        bpy.context.view_layer.update()
        mw = mesh.matrix_world.copy()
        mesh.parent = None
        mesh.matrix_world = mw
        bpy.data.objects.remove(root, do_unlink=True)
        # spawn: a small cluster in the opening fist, each with its own spin
        off = Vector((rnd.uniform(-0.02, 0.02), rnd.uniform(-0.015, 0.015), rnd.uniform(-0.01, 0.01)))
        rot = Euler((rnd.uniform(0, 6.28), rnd.uniform(0, 6.28), rnd.uniform(0, 6.28))).to_quaternion()
        M0 = Matrix.Translation(rel_pt + off) @ rot.to_matrix().to_4x4()
        v = Vector((rnd.uniform(-0.08, 0.08), -1.15 + rnd.uniform(-0.12, 0.12), -0.35))
        w = Vector((rnd.uniform(-25, 25), rnd.uniform(-25, 25), rnd.uniform(-10, 10)))
        bodies.append((mesh, M0, v, w))
        dice.append(mesh)
    track = dice_sim(ctx, bodies, [bl, tunic], f_rel, 60, None)
    for o, seq in track.items():
        o.rotation_mode = "QUATERNION"
        for f, M in seq:
            o.matrix_world = M
            o.keyframe_insert("location", frame=f)
            o.keyframe_insert("rotation_quaternion", frame=f)
        o.hide_render = True
        o.keyframe_insert("hide_render", frame=f_rel - 1)
        o.hide_render = False
        o.keyframe_insert("hide_render", frame=f_rel)
        print("s13b die %s rest at %s" % (o.name, tuple(round(c, 3) for c in seq[-1][1].to_translation())))

    # ------------------------------------------------------------------ soldiers
    people = []
    # A: far side, facing the camera (-Y), shaking the dice in his right fist, then throwing
    a_loc = Cc + Vector((0.03, 0.78, 0))
    sA = P.make_person("legA", "SOLDIER", lod="hero", pose=None, expression="neutral", hair_strands=False, seed=1)
    sA.rig.location = (a_loc.x, a_loc.y, gz(a_loc.x, a_loc.y))
    sA.rig.rotation_euler = (0, 0, 0)
    # B: left, facing +X; C: right, facing -X
    b_loc = Cc + Vector((-0.78, 0.02, 0))
    sB = P.make_person("legB", "SOLDIER", lod="hero", pose=None, expression="neutral", hair_strands=False, seed=2,
                       skin_tone=0.6)
    sB.rig.location = (b_loc.x, b_loc.y, gz(b_loc.x, b_loc.y))
    sB.rig.rotation_euler = (0, 0, math.radians(90))     # faces +X
    c_loc = Cc + Vector((0.80, 0.10, 0))
    sC = P.make_person("legC", "SOLDIER", lod="hero", pose=None, expression="neutral", hair_strands=False, seed=3,
                       skin_tone=0.35)
    sC.rig.location = (c_loc.x, c_loc.y, gz(c_loc.x, c_loc.y))
    sC.rig.rotation_euler = (0, 0, math.radians(-90))    # faces -X
    people = [sA, sB, sC]
    bpy.context.view_layer.update()

    # A: shake (fist bobbing above the far edge of the blanket), throw at f_rel
    fist = rel_pt + Vector((0.0, 0.12, 0.10))
    _kp(sA, 1, lean=26, seat=0.55, rt=fist, rhand="fist", rpron=40)
    for k, f in enumerate(range(8, f_rel - 10, 7)):
        _kp(sA, f, lean=26, seat=0.55, rt=fist + Vector((0, 0.01, 0.035 * (1 if k % 2 else -1))), rhand="fist",
            rpron=40)
    _kp(sA, f_rel - 6, lean=27, seat=0.55, rt=fist + Vector((0, 0.04, 0.06)), rhand="fist", rpron=40)
    _kp(sA, f_rel, lean=31, seat=0.55, rt=rel_pt + Vector((0, 0.02, 0.0)), rhand="open", rpron=150)
    _kp(sA, f_rel + 30, lean=30, seat=0.55, rt=rel_pt + Vector((0.02, 0.06, -0.04)), rhand="relaxed", rpron=140)
    # C: drags the mantle to himself during phrase 1
    c0, c1, c2 = fr(p1s) + 2, fr(p1s) + 14, fr(p1s) + 38
    grab_m = Vector(mantle.location) + Vector((-0.10, 0.0, 0.06))
    _kp(sC, 1, lean=18, seat=0.5)
    _kp(sC, c0, lean=20, seat=0.5)
    _kp(sC, c1, lean=30, seat=0.5, rt=grab_m, rhand="claw", rpron=110)
    _kp(sC, c1 + 4, lean=30, seat=0.5, rt=grab_m + Vector((0, 0, -0.01)), rhand="grip", rpron=110)
    _kp(sC, c2, lean=16, seat=0.5, rt=Vector(c_loc) + Vector((-0.22, -0.02, 0.0)) + Vector((0, 0, Cc.z + 0.32)),
        rhand="grip", rpron=110)
    # B: rests, then snatches the tunic (the winner)
    b0 = fr(p2e) + 6
    b1 = b0 + 9
    b2 = b1 + 16
    grab_t = Vector(tunic.location) + Vector((-0.12, -0.02, 0.06))
    _kp(sB, 1, lean=20, seat=0.6)
    _kp(sB, b0 - 4, lean=20, seat=0.6)
    _kp(sB, b1, lean=32, seat=0.6, rt=grab_t, rhand="claw", rpron=120)
    _kp(sB, b1 + 3, lean=32, seat=0.6, rt=grab_t + Vector((0, 0, -0.012)), rhand="fist", rpron=120)
    _kp(sB, b2, lean=12, seat=0.6, rt=Vector(b_loc) + Vector((0.18, -0.05, Cc.z + 0.55 - b_loc.z)), rhand="fist",
        rpron=120)
    for p in people:
        P.expression(p, "neutral")
        for o in p.objects():
            for m in (getattr(o.data, "materials", None) or []) if o.data is not None else []:
                if m is not None:
                    E.hazify(m)
    # garments follow the hands
    _child_of_hand(mantle, sC, "wrist.R", None, c1 + 4)
    _child_of_hand(tunic, sB, "wrist.R", None, b1 + 3)

    # ------------------------------------------------------------------ light
    # torch planted off-screen left-back: the warm, flickering key
    tl = Cc + Vector((-1.25, 0.55, 0))
    tl.z = gz(tl.x, tl.y) + 1.35
    torch = C.light("POINT", tuple(tl), 55.0, color=C.kelvin(1800), size=0.08, name="TorchKey")
    tk = torch.data
    tk.keyframe_insert("energy", frame=1)
    fc = C._fcurves(tk.animation_data.action)[0]
    mod = fc.modifiers.new("NOISE")
    mod.scale = 3.0
    mod.strength = 18.0
    mod.phase = 3.0
    # rim from the dim sun behind the far soldier (linked to soldiers + props)
    recv = bpy.data.collections.new("s13b_rim")
    for p in people:
        for o in p.objects():
            if o.type in ("MESH", "CURVES"):
                recv.objects.link(o)
    for o in [tunic, mantle] + dice:
        recv.objects.link(o)
    rim = C.light("SUN", (0, 0, 20), 1.2, color=(1.0, 0.45, 0.22), name="Rim", shadow=True)
    rd = Vector((0.15, 1.0, 0.45)).normalized()
    rim.rotation_euler = (-rd).to_track_quat("-Z", "Y").to_euler()
    rim.data.angle = math.radians(4)
    rim.light_linking.receiver_collection = recv

    # ------------------------------------------------------------------ camera
    tgt0 = Vector(tunic.location) + Vector((0, 0.06, 0.02))
    loc0 = Vector((cam_loc0.x, cam_loc0.y, Cc.z + 0.62))
    loc1 = loc0 + (tgt0 - loc0) * 0.22

    def cam_fn(f):
        u = C.ease_in_out(min(1.0, (f - 1) / float(max(2, f_rel + 40 - 1))))
        loc = loc0.lerp(loc1, u) + C.shake(f, 0.004, 0.5, 4)
        tgt = tgt0 + Vector((0, -0.04 * u, 0)) + C.shake(f, 0.006, 0.4, 9)
        return (loc, tgt, 0.0, 34, (tgt0 - loc).length)

    cam = C.camera(tuple(loc0), tuple(tgt0), lens=34, fstop=2.8, focus=(tgt0 - loc0).length, name="Cam")
    C.animate_camera(cam, cam_fn, 1, NR)

    ctx.samples = 6
    ctx.render_opts.update({"volumetrics": "low"})
    ctx.interp = False
    ctx.post.update({"grade": "eclipse", "bloom": 0.22, "vignette": 0.3})
