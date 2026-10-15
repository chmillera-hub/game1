"""s13b - Casting lots: "They divide my clothes among them and cast lots for my garment."

At the foot of the centre cross, in the eclipse darkness, three Roman soldiers kneel round a red army
cloak (sagum) spread on the rocky ground. A torch planted off-screen left throws warm, flickering light
across it (the only warm light in the dim red-brown day). Camera: low three-quarter view over the cloak,
the soldiers' knees / forearms / hands framing the folded cream tunic in the middle.

  * "They divide my clothes among them": the soldier on the right drags the folded madder mantle off the
    cloak to his knees.
  * "and cast lots for my garment": the far soldier, who has been shaking the bones in his fist, throws -
    two bone dice and two astragali tumble in slow motion across the seamless tunic and come to rest on
    the cloak in front of it (Bullet rigid-body sim run inside build() in a scratch scene at time scale
    0.3, baked to keyframes: no bake needed at render time).
  * The winner on the left snatches the tunic up and away; the bones lie on the empty cloak.
"""
import math
import os
import random
import bpy
import bmesh
import numpy as np
from mathutils import Vector, Matrix, Euler, Quaternion, noise
from lib import core as C
from lib import env as E
from lib import assets as A
from lib import characters as P
from lib import wardrobe as W

CLOTH_C = (0.05, -1.30)      # cloak centre (world xy): inside the rock-free keep-out in front of the centre cross
SLOWMO = 0.3
DICE_SEED = 1                # throw variation chosen with S13B_TUNE=N (see dice_candidates)


# ============================================================================================ geometry
def _box_uv(me):
    """Box-projected UVs in metres (the wardrobe fabric material expects metric UVs)."""
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uv = me.uv_layers[0].data
    for poly in me.polygons:
        n = poly.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uv[li].uv = (co.x, co.y) if ax == 2 else ((co.x, co.z) if ax == 1 else (co.y, co.z))


def folded_cloth(name, w, d, h, layers=4, seed=0, color="cream", fabric="linen", wrinkle=1.0, coll=None):
    """A folded garment lying on the ground. Rounded fold rolls on the long (+-x) sides, flatter open ends
    (+-y) showing the stacked layers, irregular outline, soft lumps + creases on top.
    Origin at the bottom centre; size w (x) x d (y) x h."""
    rnd = random.Random(seed)
    so = rnd.uniform(0, 100)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=26, use_grid_fill=True)
    rx, ry, rz = h * 0.5, h * 0.28, h * 0.5
    for v in bm.verts:
        p = Vector((v.co.x * w, v.co.y * d, v.co.z * h))
        ix = w / 2 - rx + 0.005 * noise.noise(Vector((so, p.y * 9.0, 0.5)))
        iy = d / 2 - ry + 0.006 * noise.noise(Vector((p.x * 7.0, so, 1.5)))
        q = Vector((max(-ix, min(ix, p.x)), max(-iy, min(iy, p.y)), 0.0))
        dv = p - q
        if dv.length < 1e-9:
            dv = Vector((0, 0, 1))
        e = Vector((dv.x / rx, dv.y / ry, dv.z / rz)).normalized()
        off = Vector((e.x * rx, e.y * ry, e.z * rz))
        # layer grooves where the folded layers meet (strongest on the open ends)
        side = math.sqrt(e.x * e.x + e.y * e.y)
        endw = abs(e.y) / max(1e-6, side) if side > 1e-6 else 0.0
        zz = (q.z + off.z) / h + 0.5
        groove = 0.5 + 0.5 * math.cos(zz * layers * 2 * math.pi)
        off *= 1.0 - side ** 2 * groove * (0.05 + 0.18 * endw)
        p = q + off
        p.z += h * 0.5
        top = max(0.0, min(1.0, (p.z - h * 0.55) / (h * 0.45)))
        lump = noise.noise(Vector((p.x * 8 + so, p.y * 8, 0.3))) * 0.003 * wrinkle
        crease = noise.noise(Vector((p.x * 2.5 + so, p.y * 16, 1.7))) * 0.0018 * wrinkle
        crease += abs(noise.noise(Vector((p.x * 18 + so, p.y * 5, 5.1)))) * -0.0016 * wrinkle
        sag = -0.004 * (1 - (2 * p.x / w) ** 2) * (1 - (2 * p.y / d) ** 2)
        p.z += (lump + crease * top + sag * top) * (0.25 + 0.75 * top)
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
    wa.data.foreach_set("value", [0.3] * len(me.vertices))
    return o


def cloak(name, center, w, d, gzf, res=0.012, seed=2, color=(0.42, 0.12, 0.08), coll=None):
    """Wool army cloak spread on the ground: follows the terrain, rumpled, irregular frayed outline,
    edges curling up a little."""
    nx, ny = int(w / res), int(d / res)
    rnd = random.Random(seed)
    so = rnd.uniform(0, 50)
    cx, cy = center
    V = []
    keep = []
    for j in range(ny + 1):
        for i in range(nx + 1):
            x = -w / 2 + w * i / nx
            y = -d / 2 + d * j / ny
            # irregular outline: distance to the (noisy) border
            bx = w / 2 - 0.03 * (0.5 + 0.5 * noise.noise(Vector((so, y * 4.0, 0.2))))
            by = d / 2 - 0.03 * (0.5 + 0.5 * noise.noise(Vector((x * 4.0, so, 0.7))))
            e = min(bx - abs(x), by - abs(y))
            keep.append(e > 0)
            z = gzf(cx + x, cy + y) + 0.008
            z += 0.006 * noise.noise(Vector((x * 2.5 + so, y * 2.5, 0.5)))
            z += 0.003 * abs(noise.noise(Vector((x * 7 + so, y * 3, 2.5))))
            z += 0.002 * noise.noise(Vector((x * 4 + so, y * 14, 4.5)))
            z += 0.012 * max(0.0, 1.0 - max(0.0, e) / 0.05) ** 2 * (0.5 + 0.5 * noise.noise(Vector((x * 9, y * 9, so))))
            V.append((x, y, z))
    F = []
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            q = (a, a + 1, a + nx + 2, a + nx + 1)
            if all(keep[k] for k in q):
                F.append(q)
    me = bpy.data.meshes.new(name)
    me.from_pydata(V, [], F)
    me.update()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.to_mesh(me)
    bm.free()
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
    so_.thickness = 0.003
    so_.offset = -1.0
    o.data.materials.append(W.fabric_material("wool"))
    o.color = (*W.color(color), 1.0)
    wa = me.attributes.new("wear", "FLOAT", "POINT")
    wa.data.foreach_set("value", [0.45] * len(me.vertices))
    return o


# ============================================================================================ poses
def _pose_kneel2(Ps, p, lean=22.0, seat=0.5, rt=None, lt=None, rhand="relaxed", lhand="relaxed",
                 rpron=95.0, lpron=95.0, head="down", twist=0.0, **k):
    """Kneeling on both knees, sitting back towards the heels (seat 0..1), torso leaning forward;
    either hand to a target (rig space) or resting on the thigh."""
    for s in "LR":
        lat = P._lateral(s)
        t = Vector((lat.x * 0.08, -0.12 - 0.8 * seat, -1 + 0.45 * seat))
        sh = P._leg(Ps, s, t, P.FWD + lat * 0.08, 100 + 45 * seat)
        # seiza feet: the foot continues the shin backwards (instep on the ground) - no tiptoe lift
        Ps.aim("foot." + s, (sh + Vector((0, 0, -0.25))).normalized())
    # forward lean = hip flexion (pitch the pelvis, legs kept in place) + spine flexion
    hb = 0.5 * lean
    Ps.turn("root", bend=hb, frame_of="root")
    for s in "LR":
        Ps.turn("upperleg01." + s, bend=-hb, frame_of="root")
    P._spine_bend(Ps, bend=lean - hb, twist=twist)
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


def _rig_targets(person, kw):
    for key in ("rt", "lt"):
        if kw.get(key) is not None:
            kw[key] = person.rig.matrix_world.inverted() @ Vector(kw[key])
    return kw


def _kp(person, f, **kw):
    """key_pose with world targets for rt / lt (the generic converter handles 'target' only)."""
    return P.key_pose(person, f, "s13b_kneel", **_rig_targets(person, kw))


def _static(person, drape=True, **kw):
    """Static pose (cloth-settling the skirts: kneeling skinned tunics balloon) before keying."""
    kw = _rig_targets(person, kw)
    try:
        return P.pose(person, "s13b_kneel", drape=drape, **kw)
    except TypeError:                     # older characters.pose without drape=
        return P.pose(person, "s13b_kneel", **kw)


def _child_of_hand(obj, person, bone, f_on):
    """obj follows a hand bone from frame f_on on (Child Of, inverse computed at f_on)."""
    sc = bpy.context.scene
    sc.frame_set(f_on)
    con = obj.constraints.new("CHILD_OF")
    con.target = person.rig
    con.subtarget = bone
    con.inverse_matrix = (person.rig.matrix_world @ person.rig.pose.bones[bone].matrix).inverted()
    con.set_inverse_pending = False
    con.influence = 0.0
    con.keyframe_insert("influence", frame=f_on - 1)
    con.influence = 1.0
    con.keyframe_insert("influence", frame=f_on)
    for fc in C._fcurves(obj.animation_data.action):
        if "influence" in fc.data_path:
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"
    sc.frame_set(1)
    return con


# ============================================================================================ dice sim
def dice_sim(ctx, bodies, colliders, f_rel, n_frames, frictions=(0.7, 0.5)):
    """Bullet sim in a scratch scene (only the colliders + bodies -> fast, independent of the heavy set)
    at SLOWMO time scale from f_rel. bodies = [(obj, start_matrix, lin_vel, ang_vel)] (real m/s, rad/s).
    Returns {obj: [(frame, matrix_world), ...]}; the scratch scene and all rigid-body data are removed."""
    main = bpy.context.scene
    dg0 = bpy.context.evaluated_depsgraph_get()
    sim = bpy.data.scenes.new("DiceSim")
    sim.render.fps = main.render.fps
    sim.frame_start, sim.frame_end = f_rel - 3, f_rel + n_frames
    vl = sim.view_layers[0]
    cols = []
    for o in colliders:
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg0))
        c = bpy.data.objects.new(o.name + "_col", me)
        c.matrix_world = o.matrix_world.copy()
        sim.collection.objects.link(c)
        cols.append(c)
    for (o, _, _, _) in bodies:
        sim.collection.objects.link(o)
    ov = dict(scene=sim, view_layer=vl)
    with bpy.context.temp_override(**ov):
        bpy.ops.rigidbody.world_add()
    rbw = sim.rigidbody_world
    rbw.time_scale = SLOWMO
    rbw.substeps_per_frame = 40
    rbw.solver_iterations = 30
    rbw.point_cache.frame_start = f_rel - 3
    rbw.point_cache.frame_end = f_rel + n_frames
    dt = SLOWMO / ctx.fps
    for o, fr_ in zip(cols, frictions):
        with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o], **ov):
            bpy.ops.rigidbody.object_add(type="PASSIVE")
        o.rigid_body.collision_shape = "MESH"
        o.rigid_body.friction = fr_
        o.rigid_body.restitution = 0.3
        o.rigid_body.collision_margin = 0.0005
    for (o, M0, v, w) in bodies:
        with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o], **ov):
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
        loc0, rot0 = M0.to_translation(), M0.to_quaternion()
        ax = Vector(w)
        for k, f in enumerate((f_rel - 2, f_rel - 1, f_rel)):      # kinematic launch at the release velocity
            tt = (k - 2) * dt
            o.location = loc0 + Vector(v) * tt + Vector((0, 0, -0.5 * 9.81 * tt * tt))
            q = rot0.copy()
            if ax.length > 1e-6:
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
        sim.frame_set(f)
        dg = vl.depsgraph
        for (o, _, _, _) in bodies:
            out[o].append((f, o.evaluated_get(dg).matrix_world.copy()))
    for o in [b[0] for b in bodies] + cols:
        with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o], **ov):
            bpy.ops.rigidbody.object_remove()
    coll = rbw.collection
    with bpy.context.temp_override(**ov):
        bpy.ops.rigidbody.world_remove()
    for (o, _, _, _) in bodies:
        o.animation_data_clear()
        sim.collection.objects.unlink(o)
    for c in cols:
        me = c.data
        bpy.data.objects.remove(c, do_unlink=True)
        bpy.data.meshes.remove(me)
    if coll is not None and coll.name in bpy.data.collections:
        bpy.data.collections.remove(coll)
    bpy.data.scenes.remove(sim)
    if bpy.context.window is not None:
        bpy.context.window.scene = main
    main.frame_set(1)
    return out


def dice_candidates(seed, rel_pt, n):
    """Spawn matrices + velocities for the n bones out of the opening fist (deterministic per seed).
    Spawn slots are >= 3.5 cm apart (overlapping convex hulls explode apart in Bullet)."""
    rnd = random.Random(1000 + seed)
    vy = -0.95 - 0.4 * rnd.random()
    vz = -0.15 + 0.2 * rnd.random()
    slots = [(-0.036, 0.0, 0.0), (0.0, 0.018, 0.034), (0.036, -0.008, 0.004), (0.004, -0.034, -0.022)]
    out = []
    for i in range(n):
        sx, sy, sz = slots[i % len(slots)]
        off = Vector((sx + rnd.uniform(-0.004, 0.004), sy + rnd.uniform(-0.004, 0.004), sz + rnd.uniform(-0.003, 0.003)))
        rot = Euler((rnd.uniform(0, 6.28), rnd.uniform(0, 6.28), rnd.uniform(0, 6.28))).to_quaternion()
        M0 = Matrix.Translation(rel_pt + off) @ rot.to_matrix().to_4x4()
        v = Vector((rnd.uniform(-0.08, 0.08), vy * rnd.uniform(0.9, 1.1), vz + rnd.uniform(-0.04, 0.04)))
        w = Vector((rnd.uniform(-30, 30), rnd.uniform(-30, 30), rnd.uniform(-12, 12)))
        out.append((M0, v, w))
    return out


def score_throw(track, tunic):
    """How good a throw looks: all bones end in front of the tunic inside the frame, most of them roll
    over the tunic on the way, nicely spread, settled."""
    Mi = tunic.matrix_world.inverted()
    top = max(v.co.z for v in tunic.data.vertices)
    ends, crossed, settled = [], 0, 0
    for o, seq in track.items():
        pl = [Mi @ M.to_translation() for f, M in seq]
        e = pl[-1]
        ends.append(e)
        if any(abs(p.x) < 0.13 and abs(p.y) < 0.11 and p.z > top - 0.004 for p in pl):
            crossed += 1
        if (pl[-1] - pl[-6]).length < 0.001:
            settled += 1
    inside = sum(1 for e in ends if abs(e.x) < 0.16 and -0.34 < e.y < -0.14)
    spread = min(((a - b).length for i, a in enumerate(ends) for b in ends[i + 1:]), default=0)
    s = inside * 10 + crossed * 3 + settled * 2 + min(spread, 0.05) * 60
    return s, dict(inside=inside, crossed=crossed, settled=settled, spread=round(spread, 3),
                   ends=[tuple(round(c, 3) for c in e) for e in ends])


# ============================================================================================ build
def build(ctx):
    NR = ctx.render_frames
    sc = bpy.context.scene
    fr = lambda s: int(round(ctx.frame(s)))
    p1s, p1e = ctx.phrases[0]["start"], ctx.phrases[0]["end"]
    p2s, p2e = ctx.phrases[1]["start"], ctx.phrases[1]["end"]

    Cc = Vector((CLOTH_C[0], CLOTH_C[1], 0.0))
    view = dict(loc=(Cc.x, Cc.y - 0.7, 11.6), target=(Cc.x, Cc.y + 3, 11.0), lens=28, margin=60)
    G = E.golgotha(ctx, mood="eclipse", view=view, grass=0.8, near_detail=1.0, dust=False)
    gz = lambda x, y: float(G["ground_z"](x, y))
    Cc.z = gz(Cc.x, Cc.y)
    for o in bpy.data.objects:
        if o.name.startswith("EnvWedges") or o.name.startswith("EnvBoulders"):
            o.hide_render = True

    # ------------------------------------------------------------------ cloak, tunic, mantle
    props = bpy.data.collections.new("s13b_props")
    sc.collection.children.link(props)
    bl = cloak("Sagum", (Cc.x, Cc.y), 1.3, 1.05, gz, coll=props)
    bpy.context.view_layer.update()

    def top_z(x, y):
        dg = bpy.context.evaluated_depsgraph_get()
        ob = bl.evaluated_get(dg)
        hit, loc, nrm, idx = ob.ray_cast(ob.matrix_world.inverted() @ Vector((x, y, 50.0)), Vector((0, 0, -1)))
        return (ob.matrix_world @ loc).z if hit else Cc.z + 0.01

    T = Cc + Vector((-0.01, 0.04, 0))
    tunic = folded_cloth("Tunic", 0.30, 0.25, 0.032, layers=4, seed=3, color="cream", fabric="linen", coll=props)
    tunic.location = (T.x, T.y, top_z(T.x, T.y) - 0.002)
    tunic.rotation_euler = (0, 0, math.radians(6))
    M = Cc + Vector((0.21, -0.17, 0))
    mantle = folded_cloth("Mantle", 0.27, 0.30, 0.045, layers=3, seed=8, color="madder", fabric="wool", coll=props)
    mantle.location = (M.x, M.y, top_z(M.x, M.y) - 0.002)
    mantle.rotation_euler = (0, 0, math.radians(-24))
    bpy.context.view_layer.update()

    # ------------------------------------------------------------------ dice (slow-motion sim, baked to keys)
    f_rel = fr(p2s) + 5                         # the fist opens over the tunic
    specs = [("dice", 0, dict(top=3)), ("dice", 2, dict(top=5)), ("astragalus", 1, {}), ("astragalus", 3, {})]
    rel_pt = Vector(tunic.location) + Vector((0.0, 0.16, 0.15))
    dice = []
    for (nm, var, opt) in specs:
        root = A.load(nm, loc=(0, 0, 0), variant=var, coll=props, **opt)
        mesh = next(o for o in A.children_recursive(root) if o.type == "MESH")
        bpy.context.view_layer.update()
        mw = mesh.matrix_world.copy()
        mesh.parent = None
        mesh.matrix_world = mw
        bpy.data.objects.remove(root, do_unlink=True)
        dice.append(mesh)
    seed = DICE_SEED
    ntune = int(os.environ.get("S13B_TUNE", "0"))
    if ntune:
        best = None
        for s_ in range(ntune):
            cand = dice_candidates(s_, rel_pt, len(dice))
            tr = dice_sim(ctx, [(o, *c) for o, c in zip(dice, cand)], [bl, tunic], f_rel, 60)
            sc_, info = score_throw(tr, tunic)
            print("S13B_TUNE seed %d score %.1f %s" % (s_, sc_, info), flush=True)
            if best is None or sc_ > best[0]:
                best = (sc_, s_)
        seed = best[1]
        print("S13B_TUNE best seed", seed, flush=True)
    cand = dice_candidates(seed, rel_pt, len(dice))
    track = dice_sim(ctx, [(o, *c) for o, c in zip(dice, cand)], [bl, tunic], f_rel, 60)
    print("s13b throw seed %d: %s" % (seed, score_throw(track, tunic)))
    for o, seq in track.items():
        o.rotation_mode = "QUATERNION"
        for f, Mw in seq:
            o.matrix_world = Mw
            o.keyframe_insert("location", frame=f)
            o.keyframe_insert("rotation_quaternion", frame=f)
        o.hide_render = True
        o.keyframe_insert("hide_render", frame=f_rel - 1)
        o.hide_render = False
        o.keyframe_insert("hide_render", frame=f_rel)
    sc.frame_set(1)

    # ------------------------------------------------------------------ soldiers
    def soldier(name, loc, yaw, **kw):
        p = P.make_person(name, "SOLDIER", lod="mid", pose=None, expression="neutral", hair_strands=False, **kw)
        p.rig.location = (loc.x, loc.y, gz(loc.x, loc.y))
        p.rig.rotation_euler = (0, 0, math.radians(yaw))
        bpy.context.view_layer.update()
        return p
    a_loc = Cc + Vector((0.02, 0.66, 0))                 # A: far side, facing the camera (-Y)
    b_loc = Cc + Vector((-0.66, -0.02, 0))               # B: left, facing +X (the winner)
    c_loc = Cc + Vector((0.70, -0.06, 0))                # C: right, facing -X (takes the mantle)
    sA = soldier("legA", a_loc, 0, seed=1)
    sB = soldier("legB", b_loc, 90, seed=2, skin_tone=0.6)
    sC = soldier("legC", c_loc, -90, seed=3, skin_tone=0.35)
    people = [sA, sB, sC]

    # A: shaking the bones in his fist above the far edge, throws at f_rel
    fist = rel_pt + Vector((0.0, 0.07, 0.07))
    _static(sA, drape=False, lean=50, seat=0.55, rt=fist, rhand="fist", rpron=40)
    _kp(sA, 1, lean=50, seat=0.55, rt=fist, rhand="fist", rpron=40)
    for k, f in enumerate(range(8, f_rel - 10, 6)):
        _kp(sA, f, lean=50, seat=0.55, rt=fist + Vector((0, 0.008, 0.03 * (1 if k % 2 else -1))), rhand="fist",
            rpron=40)
    _kp(sA, f_rel - 6, lean=50, seat=0.55, rt=fist + Vector((0, 0.04, 0.05)), rhand="fist", rpron=40)
    _kp(sA, f_rel, lean=58, seat=0.55, rt=rel_pt + Vector((0, 0.05, 0.04)), rhand="open", rpron=150)
    _kp(sA, f_rel + 30, lean=56, seat=0.55, rt=rel_pt + Vector((0.02, 0.07, -0.03)), rhand="relaxed", rpron=140)
    # C: drags the mantle to himself during phrase 1 (left hand = camera side)
    c0, c1, c2 = fr(p1s) + 1, fr(p1s) + 13, fr(p1s) + 36
    grab_m = Vector(mantle.location) + Vector((0.09, -0.02, 0.05))
    _static(sC, drape=False, lean=24, seat=0.5)
    _kp(sC, 1, lean=24, seat=0.5)
    _kp(sC, c0, lean=26, seat=0.5)
    _kp(sC, c1, lean=68, seat=0.5, lt=grab_m, lhand="claw", lpron=110)
    _kp(sC, c1 + 4, lean=68, seat=0.5, lt=grab_m + Vector((0, 0, -0.012)), lhand="grip", lpron=110)
    _kp(sC, c2, lean=22, seat=0.5, lt=Vector((c_loc.x - 0.24, c_loc.y - 0.16, Cc.z + 0.32)), lhand="grip", lpron=110)
    # B: rests, then snatches the tunic (the winner)
    b0 = fr(p2e) + 6
    b1 = b0 + 9
    b2 = b1 + 16
    grab_t = Vector(tunic.location) + Vector((-0.12, -0.02, 0.04))
    _static(sB, drape=False, lean=24, seat=0.6)
    _kp(sB, 1, lean=24, seat=0.6)
    _kp(sB, b0 - 4, lean=26, seat=0.6)
    _kp(sB, b1, lean=72, seat=0.6, rt=grab_t, rhand="claw", rpron=120)
    _kp(sB, b1 + 3, lean=72, seat=0.6, rt=grab_t + Vector((0, 0, -0.012)), rhand="fist", rpron=120)
    _kp(sB, b2, lean=20, seat=0.6, rt=Vector((b_loc.x + 0.2, b_loc.y - 0.06, Cc.z + 0.5)), rhand="fist", rpron=120)
    for p in people:
        for o in p.objects():
            for m in (getattr(o.data, "materials", None) or []) if o.data is not None else []:
                if m is not None:
                    E.hazify(m)
    for f in (1, f_rel, NR):
        sc.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        for p in people:
            for o in p.objects():
                if o.type != "MESH" or o.hide_render:
                    continue
                ev = o.evaluated_get(dg)
                bb = [ev.matrix_world @ Vector(c) for c in ev.bound_box]
                ext = max((max(v[i] for v in bb) - min(v[i] for v in bb)) for i in range(3))
                if ext > 2.2:
                    print("s13b WARNING: hiding exploded part %s (extent %.1f m at f%d)" % (o.name, ext, f))
                    o.hide_render = True
    sc.frame_set(1)
    _child_of_hand(mantle, sC, "wrist.L", c1 + 4)
    _child_of_hand(tunic, sB, "wrist.R", b1 + 3)

    # ------------------------------------------------------------------ light
    # torch planted off-screen left-back: the warm, flickering key (slow flicker)
    tl = Cc + Vector((-1.2, 0.5, 0))
    tl.z = gz(tl.x, tl.y) + 1.3
    torch = C.light("POINT", tuple(tl), 48.0, color=C.kelvin(1850), size=0.08, name="TorchKey")
    tk = torch.data
    tk.keyframe_insert("energy", frame=1)
    mod = C._fcurves(tk.animation_data.action)[0].modifiers.new("NOISE")
    mod.scale, mod.strength, mod.phase = 5.0, 14.0, 3.0
    # dim red-brown sky fill from above (the eclipse day) so the shadows are not black
    C.light("AREA", tuple(Cc + Vector((0.3, -0.4, 3.0))), 22.0, color=(0.75, 0.48, 0.38), size=4.0,
            target=tuple(Cc), name="SkyFill", shadow=False)
    # rim from the dim sun behind the far soldier (linked to soldiers + props)
    recv = bpy.data.collections.new("s13b_rim")
    for p in people:
        for o in p.objects():
            if o.type in ("MESH", "CURVES"):
                recv.objects.link(o)
    for o in [tunic, mantle] + dice:
        recv.objects.link(o)
    rim = C.light("SUN", (0, 0, 20), 1.2, color=(1.0, 0.45, 0.22), name="Rim", shadow=False)
    rd = Vector((0.15, 1.0, 0.45)).normalized()
    rim.rotation_euler = (-rd).to_track_quat("-Z", "Y").to_euler()
    rim.data.angle = math.radians(4)
    rim.light_linking.receiver_collection = recv

    # ------------------------------------------------------------------ camera
    tgt0 = Vector(tunic.location) + Vector((0, -0.01, 0.012))
    loc0 = Cc + Vector((0.0, -0.66, 0.0))
    loc0.z = Cc.z + 0.44
    loc1 = loc0 + (tgt0 - loc0) * 0.24
    push_end = f_rel + 30

    def cam_fn(f):
        u = C.ease_in_out(min(1.0, (f - 1) / float(max(2, push_end - 1))))
        loc = loc0.lerp(loc1, u) + C.shake(f, 0.003, 0.5, 4)
        tgt = tgt0 + Vector((0, -0.05 * u, 0)) + C.shake(f, 0.004, 0.4, 9)
        return (loc, tgt, 0.0, 32, (tgt0 - loc).length - 0.02)

    cam = C.camera(tuple(loc0), tuple(tgt0), lens=32, fstop=2.8, focus=(tgt0 - loc0).length, name="Cam")
    C.animate_camera(cam, cam_fn, 1, NR)

    ctx.samples = 5
    ctx.render_opts.update({"volumetrics": "low"})
    ctx.interp = False
    ctx.post.update({"grade": "eclipse", "bloom": 0.22, "vignette": 0.3})
