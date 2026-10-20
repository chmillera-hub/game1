"""Replace the hillside flock with better procedural sheep (woolly lumpy body, long narrow face, side ears).

blender -b --factory-startup /opt/work/sets/hillside.blend -P sheep.py
Keeps the SHEEP_n / SHEEP_n_HEAD naming and transforms (head origin at the neck; rotate X to graze).
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix


def mat_wool(name, base=(0.72, 0.65, 0.52)):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.95
    b.inputs["Sheen Weight"].default_value = 1.0
    b.inputs["Sheen Roughness"].default_value = 0.6
    b.inputs["Specular IOR Level"].default_value = 0.2
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.feature = 'SMOOTH_F1' if hasattr(vor, "feature") else vor.feature
    vor.inputs["Scale"].default_value = 55.0
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 9.0
    nz.inputs["Detail"].default_value = 2.0
    nt.links.new(tc.outputs["Object"], vor.inputs["Vector"])
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (base[0] * 0.7, base[1] * 0.66, base[2] * 0.6, 1)
    ramp.color_ramp.elements[1].color = (*base, 1)
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.8
    bump.inputs["Distance"].default_value = 0.02
    nt.links.new(vor.outputs["Distance"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def mat_skin(name, col):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = 0.75
    b.inputs["Sheen Weight"].default_value = 0.5
    return m


def blob_mesh(name, seed, n=14, size=(0.42, 0.62, 0.34), lump=0.12):
    """Woolly body: a fused cluster of metaballs converted to a mesh."""
    rnd = random.Random(seed)
    mb = bpy.data.metaballs.new(name + "_mb")
    mb.resolution = 0.06
    mb.render_resolution = 0.05
    for i in range(n):
        e = mb.elements.new()
        e.type = 'BALL'
        u = rnd.uniform(-1, 1)
        v = rnd.uniform(0, 2 * math.pi)
        r = math.sqrt(max(0.0, 1 - u * u))
        e.co = (size[0] * 0.55 * r * math.cos(v), size[1] * 0.6 * u, size[2] * 0.5 * r * math.sin(v))
        e.radius = rnd.uniform(0.16, 0.22)
    core = mb.elements.new()
    core.type = 'ELLIPSOID'
    core.co = (0, 0, 0)
    core.radius = 0.32
    core.size_x, core.size_y, core.size_z = size[0] * 0.8, size[1] * 0.9, size[2] * 0.8
    ob = bpy.data.objects.new(name + "_tmp", mb)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bpy.data.objects.remove(ob)
    bpy.data.metaballs.remove(mb)
    me.name = name
    return me


def head_mesh(name, black):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=1.0)
    for v in bm.verts:
        x, y, z = v.co
        # long narrow skull: y is forward (-y = nose)
        t = (-y + 1) / 2  # 0 back, 1 nose
        v.co = Vector((x * 0.075 * (1 - 0.45 * t), y * 0.15, z * 0.085 * (1 - 0.35 * t) - 0.02 * t))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    return me


def build_sheep(old, idx, wool, face_black, face_white, leg_mat, eye_mat):
    loc, rot = old.location.copy(), old.rotation_euler.copy()
    scale = old.scale.copy()
    grazing = bool(old.get("grazing", False))
    lamb = old.name == "PROP_LAMB"
    s = 0.62 if lamb else 1.0
    black = (idx % 3 == 0) and not lamb
    # remove old hierarchy
    for c in list(old.children_recursive):
        bpy.data.objects.remove(c, do_unlink=True)
    name = old.name
    col = old.users_collection[0]
    bpy.data.objects.remove(old, do_unlink=True)
    body_me = blob_mesh(name + "_body", idx * 7 + 3)
    body = bpy.data.objects.new(name, body_me)
    col.objects.link(body)
    body.data.materials.append(wool)
    for p in body_me.polygons:
        p.use_smooth = True
    disp = body.modifiers.new("WoolLumps", 'DISPLACE')
    tex = bpy.data.textures.get("WOOL_TEX") or bpy.data.textures.new("WOOL_TEX", 'CLOUDS')
    tex.noise_scale = 0.06
    disp.texture = tex
    disp.strength = 0.035
    disp.texture_coords = 'LOCAL'
    # body sits at shoulder height
    body.location = loc
    body.rotation_euler = rot
    body.scale = (s, s, s)
    body["grazing"] = grazing
    hz = 0.58
    for o in [body]:
        pass
    # offset geometry so the object origin is on the ground
    for v in body_me.vertices:
        v.co.z += hz
    # legs
    for (lx, ly) in ((0.13, -0.24), (-0.13, -0.24), (0.13, 0.24), (-0.13, 0.24)):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.028, depth=0.42, location=(0, 0, 0))
        leg = bpy.context.object
        leg.name = f"{name}_leg"
        for c in list(leg.users_collection):
            c.objects.unlink(leg)
        col.objects.link(leg)
        leg.data.materials.append(leg_mat if black or idx % 2 else face_white)
        leg.parent = body
        leg.location = (lx, ly, 0.21)
    # tail
    tail = bpy.data.objects.new(f"{name}_tail", blob_mesh(f"{name}_tailm", idx + 99, n=3, size=(0.08, 0.1, 0.1)))
    col.objects.link(tail)
    tail.data.materials.append(wool)
    tail.parent = body
    tail.location = (0, 0.36, hz + 0.02)
    # head with neck pivot
    head = bpy.data.objects.new(f"{name}_HEAD", None)
    head.empty_display_size = 0.1
    col.objects.link(head)
    head.parent = body
    head.location = (0, -0.33, hz + 0.1)
    skull = bpy.data.objects.new(f"{name}_skull", head_mesh(f"{name}_skullm", black))
    col.objects.link(skull)
    skull.data.materials.append(face_black if black else face_white)
    skull.parent = head
    skull.location = (0, -0.14, 0.05)
    skull.rotation_euler = (math.radians(-25), 0, 0)
    # woolly topknot / neck
    neck = bpy.data.objects.new(f"{name}_neck", blob_mesh(f"{name}_neckm", idx + 51, n=4, size=(0.16, 0.18, 0.16)))
    col.objects.link(neck)
    neck.data.materials.append(wool)
    neck.parent = head
    neck.location = (0, -0.02, 0.0)
    for sx in (1, -1):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=10, ring_count=6)
        ear = bpy.context.object
        ear.name = f"{name}_ear"
        for c in list(ear.users_collection):
            c.objects.unlink(ear)
        col.objects.link(ear)
        ear.scale = (0.055, 0.022, 0.012)
        ear.data.materials.append(face_black if black else face_white)
        ear.parent = skull
        ear.location = (0.075 * sx, 0.06, 0.03)
        ear.rotation_euler = (0, math.radians(-20 * sx), math.radians(30 * sx))
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.011, segments=8, ring_count=6)
        eye = bpy.context.object
        eye.name = f"{name}_eye"
        for c in list(eye.users_collection):
            c.objects.unlink(eye)
        col.objects.link(eye)
        eye.data.materials.append(eye_mat)
        eye.parent = skull
        eye.location = (0.052 * sx, -0.03, 0.035)
    head.rotation_euler = (math.radians(-60) if grazing else 0.0, 0, 0)
    return body


def main():
    wool = mat_wool("M_wool_new")
    face_black = mat_skin("M_sheep_face_black", (0.025, 0.022, 0.02))
    face_white = mat_skin("M_sheep_face_white", (0.55, 0.47, 0.38))
    leg_mat = mat_skin("M_sheep_leg", (0.05, 0.045, 0.04))
    eye_mat = mat_skin("M_sheep_eye", (0.01, 0.008, 0.006))
    olds = [o for o in bpy.data.objects if (o.name.startswith("SHEEP_") and o.parent is None) or o.name == "PROP_LAMB"]
    for i, o in enumerate(sorted(olds, key=lambda o: o.name)):
        build_sheep(o, i, wool, face_black, face_white, leg_mat, eye_mat)
    bpy.ops.wm.save_as_mainfile(filepath="/opt/work/sets/hillside.blend")
    print("SHEEP_OK", len(olds))


main()
