"""Per-shot effects and prop animation, called from a shot's 'post' hook (times are shot-local seconds)."""
import bpy, math
import numpy as np
from mathutils import Vector, Matrix, Euler, Quaternion
import perform as pf

FPS = 24
PROPS = "/opt/work/props"


def _keys(obj, path, frames, values, index=-1):
    from shotbuild import fcurve_set
    if index < 0:
        fcurve_set(obj, path, 0, np.array(frames, dtype=float), np.array(values, dtype=float))
    else:
        fcurve_set(obj, path, index, np.array(frames, dtype=float), np.array(values, dtype=float))


def _ramp(n, t0, t1, v0, v1):
    t = np.arange(n) / FPS
    u = pf.smoothstep((t - t0) / max(t1 - t0, 1e-3))
    return v0 + (v1 - v0) * u


def _frames(n):
    return np.arange(n) + 1


# ------------------------------------------------------------------------------- light effects

def sun_break(n, t0, t1, target=None):
    ctrl = bpy.data.objects.get("LIGHT_CTRL")
    sun = bpy.data.objects.get("SUN")
    if ctrl is not None and "sun_energy" in ctrl:
        base = float(ctrl["sun_energy"])
        _keys(ctrl, '["sun_energy"]', _frames(n), _ramp(n, t0, t1, base * 0.35, base * 1.6))
    elif sun is not None:
        base = sun.data.energy
        _keys(sun.data, "energy", _frames(n), _ramp(n, t0, t1, base * 0.35, base * 1.6))


def hand_glow(char, n):
    rig = bpy.data.objects[char]
    hand = rig.matrix_world @ rig.pose.bones["wrist.R"].head
    l = bpy.data.lights.new("HAND_GLOW", 'AREA')
    l.shape = 'DISK'
    l.size = 0.45
    l.color = (1.0, 0.78, 0.45)
    o = bpy.data.objects.new("HAND_GLOW", l)
    bpy.context.scene.collection.objects.link(o)
    o.location = hand + Vector((0.0, -0.08, 0.32))
    o.rotation_euler = (hand - o.location).to_track_quat('-Z', 'Y').to_euler()
    _keys(l, "energy", _frames(n), _ramp(n, 0.3, 2.4, 0.0, 9.0))
    l2 = bpy.data.lights.new("HAND_GLOW_B", 'POINT')
    l2.color = (1.0, 0.85, 0.6)
    l2.shadow_soft_size = 0.2
    o2 = bpy.data.objects.new("HAND_GLOW_B", l2)
    bpy.context.scene.collection.objects.link(o2)
    o2.location = hand + Vector((0.05, -0.12, 0.08))
    _keys(l2, "energy", _frames(n), _ramp(n, 0.6, 2.6, 0.0, 2.5))


def lamp_bloom(n, t0, t1, gain=2.0):
    for i in (1, 2, 3):
        lamp = bpy.data.objects.get(f"LAMP_{i}")
        if lamp is None:
            continue
        base = lamp.data.energy
        from shotbuild import fcurves_of
        fcs = fcurves_of(lamp.data, create=False)
        mods = []
        if fcs:
            for fc in fcs:
                if fc.data_path == "energy":
                    mods = [(m.type, getattr(m, "scale", None), getattr(m, "strength", None), getattr(m, "phase", None))
                            for m in fc.modifiers]
        fc = _set_with_noise(lamp.data, "energy", _frames(n), _ramp(n, t0, t1, base, base * gain), mods)
    for o in bpy.data.objects:
        if o.type == 'LIGHT' and o.name.startswith("FaceKey"):
            base = o.data.energy
            _keys(o.data, "energy", _frames(n), _ramp(n, t0, t1, base, base * 1.5))


def _set_with_noise(data, path, frames, values, mods):
    from shotbuild import fcurve_set
    fc = fcurve_set(data, path, 0, np.array(frames, dtype=float), np.array(values, dtype=float))
    for (typ, scale, strength, phase) in mods:
        if typ == 'NOISE':
            m = fc.modifiers.new('NOISE')
            m.scale = scale or 6.0
            m.strength = strength or 1.0
            m.blend_type = 'MULTIPLY' if False else m.blend_type
    return fc


# ------------------------------------------------------------------------------- stones

def _child_of_hand(ob, rig, side, frame=1, offset=(0.0, 0.0, 0.0)):
    """Rigidly attach ob to the hand bone with the object sitting in the palm."""
    pb = rig.pose.bones[f"wrist.{side}"]
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    M = rig.matrix_world @ pb.matrix
    palm = M @ Vector((0.0, pb.length * 1.05, 0.0)) + (M.to_3x3() @ Vector(offset))
    for c in list(ob.constraints):
        ob.constraints.remove(c)
    ob.animation_data_clear()
    ob.parent = None
    ob.location = palm
    c = ob.constraints.new('CHILD_OF')
    c.target = rig
    c.subtarget = f"wrist.{side}"
    c.inverse_matrix = M.inverted()
    return c


def stone_in_hand(char, stone, side="R"):
    rig = bpy.data.objects[char]
    ob = bpy.data.objects[stone]
    side_sign = 1 if side == "L" else -1
    _child_of_hand(ob, rig, side, 1, offset=(0.0, 0.0, 0.035 * side_sign * 0 - 0.025))


def drop_stone(char, stone, t_release, n):
    rig = bpy.data.objects[char]
    ob = bpy.data.objects[stone]
    fr = int(t_release * FPS) + 1
    scn = bpy.context.scene
    scn.frame_set(fr)
    bpy.context.view_layer.update()
    W = ob.matrix_world.copy()
    start = W.translation.copy()
    # keyframe: attached until fr-1, then world-space free fall
    for c in ob.constraints:
        if c.type == 'CHILD_OF':
            c.influence = 1.0
            c.keyframe_insert("influence", frame=fr - 1)
            c.influence = 0.0
            c.keyframe_insert("influence", frame=fr)
    ob.rotation_mode = 'XYZ'
    floor = 0.055
    frames, locs, rots = [], [], []
    vz = 0.0
    z = start.z
    rx, ry = 0.0, 0.0
    bounced = False
    for f in range(fr, n + 1):
        dt = 1.0 / FPS
        if f > fr:
            vz -= 9.81 * dt
            z += vz * dt
            rx += 0.25
            ry += 0.12
        if z < floor:
            z = floor
            if not bounced:
                vz = -vz * 0.18
                bounced = True
                _impact_dust(Vector((start.x, start.y, floor)), f, n)
            else:
                vz = 0.0
        frames.append(f)
        locs.append((start.x, start.y, z))
        rots.append((rx, ry, 0.0))
    # before release the location channel holds the rest position used by the Child Of inverse
    pre = ob.location.copy()
    from shotbuild import fcurve_set
    allf = [1, fr - 1] + frames
    for i in range(3):
        vals = [pre[i], pre[i]] + [p[i] for p in locs]
        fcurve_set(ob, "location", i, np.array(allf, dtype=float), np.array(vals))
        rv = [0.0, 0.0] + [r[i] for r in rots]
        fcurve_set(ob, "rotation_euler", i, np.array(allf, dtype=float), np.array(rv))
    from shotbuild import fcurves_of
    for fc in fcurves_of(ob):
        for kp in fc.keyframe_points:
            kp.interpolation = 'CONSTANT' if kp.co[0] <= fr - 1 else 'LINEAR'


def _impact_dust(p, f, n):
    pass


def place_dropped_stone(stone):
    ob = bpy.data.objects[stone]
    young = bpy.data.objects.get("YOUNG")
    for c in list(ob.constraints):
        ob.constraints.remove(c)
    if young:
        fwd = young.matrix_world.to_3x3() @ Vector((0, -1, 0))
        ob.location = young.location + fwd * 0.32 + Vector((0.08, 0, 0.055))
    ob.rotation_euler = (0.6, 0.3, 1.1)


def pick_stone(char, stone, n, t_reach, t_lift):
    """Hand comes down into frame, closes on the stone, lifts it."""
    rig = bpy.data.objects[char]
    ob = bpy.data.objects[stone]
    tgt = bpy.data.objects[f"HAND_R_{char}"]
    sp = ob.location.copy()
    # stand the character just behind the stone, facing it, right hand side over it
    fwd = rig.matrix_world.to_3x3() @ Vector((0, -1, 0))
    side = rig.matrix_world.to_3x3() @ Vector((-1, 0, 0))
    rig.location = Vector((sp.x, sp.y, rig.location.z)) - fwd * 0.38 - side * 0.12
    bpy.context.view_layer.update()
    fr_grab = int(t_reach * FPS) + 1
    t = np.arange(n) / FPS
    above = sp + Vector((0.0, 0.05, 0.42))
    at = sp + Vector((0.0, 0.03, 0.07))
    lifted = sp + Vector((0.0, 0.15, 0.55))
    P = np.zeros((n, 3))
    for f in range(n):
        if t[f] < t_reach:
            u = float(pf.smoothstep(np.array([t[f] / t_reach]))[0])
            p = above.lerp(at, u)
        else:
            u = float(pf.smoothstep(np.array([(t[f] - t_lift) / 0.7]))[0])
            p = at.lerp(lifted, u)
        P[f] = p[:]
    from shotbuild import key_vec, fcurve_set, key_bone_quat
    key_vec(tgt, "location", _frames(n), P)
    fcurve_set(rig, 'pose.bones["lowerarm02.R"].constraints["IK"].influence', 0, _frames(n), np.ones(n))
    import gestures as gs
    op = gs.finger_curl(rig, "R", 0.05)
    gr = gs.finger_curl(rig, "R", 0.7)
    for b in op:
        qs = np.zeros((n, 4))
        for f in range(n):
            u = float(pf.smoothstep(np.array([(t[f] - t_reach + 0.1) / 0.25]))[0])
            qs[f] = op[b].slerp(gr[b], u)[:]
        key_bone_quat(rig, b, _frames(n), qs)
    # stone follows the hand after the grab (world-space keys)
    bpy.context.view_layer.update()
    frames = list(range(1, n + 1))
    locs = []
    for f in range(n):
        if t[f] < t_reach:
            locs.append(sp[:])
        else:
            locs.append((P[f][0], P[f][1] - 0.02, P[f][2] - 0.05))
    from shotbuild import fcurve_set as fs
    for i in range(3):
        fs(ob, "location", i, np.array(frames, dtype=float), np.array([l[i] for l in locs]))


# ------------------------------------------------------------------------------- inserts

def scroll_unroll(n):
    ctrl = bpy.data.objects.get("SCROLL_CTRL")
    if ctrl is not None and "unroll" in ctrl:
        _keys(ctrl, '["unroll"]', _frames(n), _ramp(n, 0.0, min(2.2, n / FPS * 0.6), 0.15, 1.0))


def break_bread(char, n):
    a = bpy.data.objects.get("PROP_BREAD_A")
    b = bpy.data.objects.get("PROP_BREAD_B")
    rig = bpy.data.objects[char]
    if not (a and b):
        return
    pa, pb_ = a.location.copy(), b.location.copy()
    mid = (pa + pb_) / 2
    sep = (pb_ - pa).normalized()
    # start pressed together, then pull apart and lift a little
    t = np.arange(n) / FPS
    u = pf.smoothstep((t - 0.4) / 1.0)
    lift = np.sin(np.clip((t - 0.2) / 1.6, 0, 1) * math.pi) * 0.05
    A = np.array([(mid - sep * (0.005 + 0.05 * k))[:] for k in u])
    B = np.array([(mid + sep * (0.005 + 0.05 * k))[:] for k in u])
    A[:, 2] = pa.z + lift
    B[:, 2] = pb_.z + lift
    from shotbuild import key_vec, fcurve_set
    key_vec(a, "location", _frames(n), A)
    key_vec(b, "location", _frames(n), B)
    for side, arr in (("R", A), ("L", B)):
        tgt = bpy.data.objects[f"HAND_{side}_{char}"]
        H = arr.copy()
        H[:, 2] += 0.035
        key_vec(tgt, "location", _frames(n), H)
        fcurve_set(rig, f'pose.bones["lowerarm02.{side}"].constraints["IK"].influence', 0, _frames(n), np.ones(n))


def cosmos_reveal(n):
    ctrl = bpy.data.objects.get("COSMOS_CTRL")
    if ctrl is not None and "reveal" in ctrl:
        _keys(ctrl, '["reveal"]', _frames(n), _ramp(n, 0.0, n / FPS * 0.92, 0.0, 1.0))
    cam = bpy.context.scene.camera
    from shotbuild import fcurves_of
    fcs = fcurves_of(cam, create=False) if cam else None
    if fcs:
        # stretch the set's 192-frame camera move over this shot
        for fc in fcs:
            for kp in fc.keyframe_points:
                kp.co[0] = 1 + (kp.co[0] - 1) * (n - 1) / 191.0
                kp.handle_left[0] = 1 + (kp.handle_left[0] - 1) * (n - 1) / 191.0
                kp.handle_right[0] = 1 + (kp.handle_right[0] - 1) * (n - 1) / 191.0


def city_window(n):
    ctrl = bpy.data.objects.get("CITY_CTRL")
    if ctrl is not None and "special_on" in ctrl:
        _keys(ctrl, '["special_on"]', _frames(n), _ramp(n, 0.9, 1.4, 0.0, 1.0))
    a, b = bpy.data.objects.get("SIL_A"), bpy.data.objects.get("SIL_B")
    if a and b:
        ax, bx = a.location.x, b.location.x
        mid = (ax + bx) / 2
        gap = abs(bx - ax) * 0.12
        _keys(a, "location", _frames(n), _ramp(n, 1.6, n / FPS * 0.85, ax, mid - gap * np.sign(bx - ax)), 0)
        _keys(b, "location", _frames(n), _ramp(n, 1.6, n / FPS * 0.85, bx, mid + gap * np.sign(bx - ax)), 0)


def door_open(n, t0, t1):
    ctrl = bpy.data.objects.get("DOOR_CTRL")
    if ctrl is not None and "door_open_deg" in ctrl:
        _keys(ctrl, '["door_open_deg"]', _frames(n), _ramp(n, t0, t1, 4.0, 72.0))
        if "interior_energy" in ctrl:
            base = float(ctrl["interior_energy"])
            _keys(ctrl, '["interior_energy"]', _frames(n), _ramp(n, t0, t1, base * 0.15, base))


def hug(n, t_start, dur):
    w = bpy.data.objects["WOMAN"]
    s = bpy.data.objects["SISTER"]
    t = np.arange(n) / FPS
    u = pf.smoothstep((t - t_start) / max(dur, 1e-3))
    from shotbuild import key_vec, fcurve_set
    pw, ps = w.location.copy(), s.location.copy()
    d = (ps - pw)
    d.z = 0
    dist = d.length
    dn = d.normalized()
    close = max(0.0, dist - 0.34) / 2
    key_vec(w, "location", _frames(n), np.array([(pw + dn * close * k)[:] for k in u]))
    key_vec(s, "location", _frames(n), np.array([(ps - dn * close * k)[:] for k in u]))
    bpy.context.view_layer.update()
    for me, other, hz in ((w, s, 0.12), (s, w, 0.32)):
        for side, sgn in (("L", 1), ("R", -1)):
            tgt = bpy.data.objects[f"HAND_{side}_{me.name}"]
            P = np.zeros((n, 3))
            for f in range(n):
                op = other.matrix_world @ other.pose.bones["spine01"].head
                # other's back: behind their chest, offset to my hand's side
                oback = other.matrix_world.to_3x3() @ Vector((0, 0.13, 0))
                mside = me.matrix_world.to_3x3() @ Vector((0.13 * sgn, 0, 0))
                p_end = op + oback + mside - Vector((0, 0, hz)) + dn * close * float(u[f]) * (1 if me == w else -1) * 0
                hand0 = me.matrix_world @ me.pose.bones[f"wrist.{side}"].head
                P[f] = (hand0.lerp(p_end, float(u[f])))[:]
            key_vec(tgt, "location", _frames(n), P)
            fcurve_set(me, f'pose.bones["lowerarm02.{side}"].constraints["IK"].influence', 0, _frames(n), u)
        # heads tilt to the side over the partner's shoulder
        ht = bpy.data.objects.get(f"HEAD_TGT_{me.name}")
        if ht:
            side_off = me.matrix_world.to_3x3() @ Vector((0.6, 0, -0.25))
            from shotbuild import fcurves_of
            fcs = fcurves_of(ht, create=False)
            if fcs:
                for fc in fcs:
                    i = fc.array_index
                    for kp in fc.keyframe_points:
                        f = int(kp.co[0]) - 1
                        if 0 <= f < n:
                            kp.co[1] += side_off[i] * float(u[f])


# ------------------------------------------------------------------------------- phones

def _make_phone(name="PROP_PHONE"):
    import bmesh
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.scale = (0.071, 0.147, 0.008)
    bpy.context.scene.collection.objects.link(ob)
    bev = ob.modifiers.new("Bevel", 'BEVEL')
    bev.width = 0.08
    bev.segments = 3
    m = bpy.data.materials.new("phone_body")
    m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.01, 0.01, 0.012, 1)
    m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.2
    me.materials.append(m)
    # screen plane
    sm = bpy.data.meshes.new(name + "_screen")
    sm.from_pydata([(-0.47, -0.48, 0.51), (0.47, -0.48, 0.51), (0.47, 0.48, 0.51), (-0.47, 0.48, 0.51)], [], [(0, 1, 2, 3)])
    uv = sm.uv_layers.new()
    for i, c in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]):
        uv.data[i].uv = c
    so = bpy.data.objects.new(name + "_screen", sm)
    bpy.context.scene.collection.objects.link(so)
    so.parent = ob
    mat = bpy.data.materials.new("M_phone_screen_gen")
    mat.use_nodes = True
    nt = mat.node_tree
    for nd in list(nt.nodes):
        if nd.type != 'OUTPUT_MATERIAL':
            nt.nodes.remove(nd)
    em = nt.nodes.new("ShaderNodeEmission")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.name = "SCREEN_TEX"
    em.inputs["Strength"].default_value = 1.4
    nt.links.new(tex.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs[0])
    sm.materials.append(mat)
    return ob


def _screen_node():
    for m in bpy.data.materials:
        if m.use_nodes:
            for nd in m.node_tree.nodes:
                if nd.type == 'TEX_IMAGE' and nd.name == "SCREEN_TEX":
                    return m, nd
    return None, None


def phone_screen(mode):
    m, nd = _screen_node()
    if nd is None:
        return
    nd.image = bpy.data.images.load(f"{PROPS}/phone_{mode}.png", check_existing=True)


def phone_screen_sequence(n):
    """contact list -> locked -> contact -> calling, by mixing four images with keyed factors."""
    m, nd = _screen_node()
    if nd is None:
        return
    nt = m.node_tree
    out_link = nd.outputs["Color"].links[0]
    dest = out_link.to_socket
    imgs = ["contact", "locked", "contact", "calling"]
    times = [0.0, 0.42, 0.55, 0.78]
    prev = None
    nodes = []
    for i, im in enumerate(imgs):
        tn = nd if i == 0 else nt.nodes.new("ShaderNodeTexImage")
        tn.image = bpy.data.images.load(f"{PROPS}/phone_{im}.png", check_existing=True)
        if hasattr(nd, "interpolation"):
            tn.interpolation = nd.interpolation
        if i > 0:
            for l in nd.inputs["Vector"].links:
                nt.links.new(l.from_socket, tn.inputs["Vector"])
        nodes.append(tn)
    cur = nodes[0].outputs["Color"]
    T = n / FPS
    for i in range(1, len(nodes)):
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = 'RGBA'
        nt.links.new(cur, mix.inputs["A"])
        nt.links.new(nodes[i].outputs["Color"], mix.inputs["B"])
        tt = times[i] * T
        fr = int(tt * FPS) + 1
        mix.inputs["Factor"].default_value = 0.0
        mix.inputs["Factor"].keyframe_insert("default_value", frame=max(1, fr - 1))
        mix.inputs["Factor"].default_value = 1.0
        mix.inputs["Factor"].keyframe_insert("default_value", frame=fr)
        cur = mix.outputs["Result"]
    nt.links.new(cur, dest)


def phone_in_hand(char, side="R"):
    ob = bpy.data.objects.get("PROP_PHONE") or _make_phone()
    rig = bpy.data.objects[char]
    for c in list(ob.constraints):
        ob.constraints.remove(c)
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    pb = rig.pose.bones[f"wrist.{side}"]
    M = rig.matrix_world @ pb.matrix
    eyes = (rig.matrix_world @ rig.pose.bones["eye.L"].head + rig.matrix_world @ rig.pose.bones["eye.R"].head) / 2
    palm = M @ Vector((0.0, pb.length * 1.0, -0.015))
    palm = palm + (eyes - palm).normalized() * 0.03 + Vector((0, 0, 0.05))
    ob.parent = None
    ob.animation_data_clear()
    ob.location = palm
    # screen (+Z of the phone) faces the eyes, long axis roughly up
    zdir = (eyes - palm).normalized()
    q = zdir.to_track_quat('Z', 'Y')
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = q
    bpy.context.view_layer.update()
    c = ob.constraints.new('CHILD_OF')
    c.target = rig
    c.subtarget = f"wrist.{side}"
    c.inverse_matrix = M.inverted()
    # the screen's glow on the face
    gl = bpy.data.lights.new("PHONE_GLOW", 'AREA')
    gl.energy = 1.2
    gl.size = 0.12
    gl.color = (0.78, 0.86, 1.0)
    go = bpy.data.objects.new("PHONE_GLOW", gl)
    bpy.context.scene.collection.objects.link(go)
    go.location = palm + (eyes - palm).normalized() * 0.04
    go.rotation_euler = (eyes - go.location).to_track_quat('-Z', 'Y').to_euler()
    cg = go.constraints.new('CHILD_OF')
    cg.target = rig
    cg.subtarget = f"wrist.{side}"
    cg.inverse_matrix = M.inverted()


def sister_phone(n):
    phone_in_hand("SISTER", "R")
    phone_screen("incoming")
    ob = bpy.data.objects.get("PROP_PHONE")
    # buzz: small rotation jitter for the first second
    if ob:
        t = np.arange(n) / FPS
        buzz = np.where(((t % 0.9) < 0.45) & (t < 1.8), np.sin(t * 2 * math.pi * 28) * 0.012, 0.0)
        ob.rotation_mode = 'QUATERNION'
        q0 = ob.rotation_quaternion.copy()
        from shotbuild import key_bone_quat, fcurve_set
        for i in range(4):
            vals = []
            for f in range(n):
                q = q0 @ Euler((0, 0, buzz[f])).to_quaternion()
                vals.append(q[i])
            fcurve_set(ob, "rotation_quaternion", i, _frames(n), np.array(vals))


def add_area(name, loc, target, energy, size=1.0, color=(1, 1, 1)):
    l = bpy.data.lights.new(name, 'AREA')
    l.energy = energy
    l.size = size
    l.color = color
    o = bpy.data.objects.new(name, l)
    bpy.context.scene.collection.objects.link(o)
    o.location = Vector(loc)
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return o
