"""Small Blender helpers shared by the character, set and shot builders."""
import bpy
import numpy as np
from mathutils import Matrix, Vector


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def link(obj, coll=None):
    (coll or bpy.context.scene.collection).objects.link(obj)
    return obj


def make_mesh(name, verts, faces, smooth=True, coll=None, recalc=True):
    me = bpy.data.meshes.new(name)
    verts = np.asarray(verts, dtype=np.float64)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(int(i) for i in f) for f in faces])
    me.validate(clean_customdata=False)
    if recalc:
        import bmesh
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
    me.update()
    if smooth:
        me.shade_smooth()
    ob = bpy.data.objects.new(name, me)
    link(ob, coll)
    return ob


def set_shape_keys(ob, shapes):
    if ob.data.shape_keys is None:
        ob.shape_key_add(name='Basis', from_mix=False)
    for name, co in shapes.items():
        k = ob.shape_key_add(name=name, from_mix=False)
        k.data.foreach_set('co', np.asarray(co, dtype=np.float32).reshape(-1))
        k.slider_min = -1.0
        k.slider_max = 1.5


def set_color_attr(ob, name, cols):
    me = ob.data
    cols = np.asarray(cols, dtype=np.float32)
    if cols.shape[1] == 3:
        cols = np.concatenate([cols, np.ones((len(cols), 1), np.float32)], 1)
    a = me.color_attributes.new(name=name, type='FLOAT_COLOR', domain='POINT')
    a.data.foreach_set('color', cols.reshape(-1))
    return a


def set_weights(ob, weights, thresh=1e-3):
    """weights: dict group -> per-vertex array. Batched by quantised weight."""
    for g, w in weights.items():
        w = np.asarray(w)
        vg = ob.vertex_groups.get(g) or ob.vertex_groups.new(name=g)
        idx = np.nonzero(w > thresh)[0]
        if len(idx) == 0:
            continue
        q = np.round(w[idx] * 200) / 200
        for val in np.unique(q):
            sel = idx[q == val]
            vg.add([int(i) for i in sel], float(val), 'REPLACE')


def subsurf(ob, levels=1, render=None):
    m = ob.modifiers.new('Subsurf', 'SUBSURF')
    m.levels = levels
    m.render_levels = levels if render is None else render
    m.quality = 2
    return m


# ---------------------------------------------------------------- materials
def _nodes(mat):
    mat.use_nodes = True
    nt = mat.node_tree
    return nt, nt.nodes, nt.links


def principled(name, color, rough=0.5, sss=0.0, sss_radius=(1.0, 0.4, 0.25), sss_scale=0.01,
               coat=0.0, sheen=0.0, spec=0.5, metallic=0.0, emission=None, estr=0.0):
    mat = bpy.data.materials.new(name)
    nt, N, L = _nodes(mat)
    b = N['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metallic
    b.inputs['Specular IOR Level'].default_value = spec
    if sss:
        b.inputs['Subsurface Weight'].default_value = sss
        b.inputs['Subsurface Radius'].default_value = sss_radius
        b.inputs['Subsurface Scale'].default_value = sss_scale
    if coat:
        b.inputs['Coat Weight'].default_value = coat
        b.inputs['Coat Roughness'].default_value = 0.05
    if sheen:
        b.inputs['Sheen Weight'].default_value = sheen
    if emission is not None:
        b.inputs['Emission Color'].default_value = (*emission, 1)
        b.inputs['Emission Strength'].default_value = estr
    return mat


def attr_node(N, name, x=-900, y=0):
    a = N.new('ShaderNodeAttribute')
    a.attribute_name = name
    a.location = (x, y)
    return a


def mix_rgb(N, L, fac_socket, c1, c2, x=-400, y=0, blend='MIX'):
    m = N.new('ShaderNodeMix')
    m.data_type = 'RGBA'
    m.blend_type = blend
    m.location = (x, y)
    if isinstance(fac_socket, (int, float)):
        m.inputs['Factor'].default_value = fac_socket
    else:
        L.new(fac_socket, m.inputs['Factor'])
    for sock, c in ((m.inputs[6], c1), (m.inputs[7], c2)):
        if isinstance(c, tuple) or isinstance(c, list):
            sock.default_value = (*c[:3], 1)
        else:
            L.new(c, sock)
    return m


def skin_material(name, skin, lip, blush, blush_amt=0.35, interior=(0.22, 0.05, 0.05)):
    mat = principled(name, skin, rough=0.48, sss=0.12, sss_scale=0.004, spec=0.45)
    nt, N, L = _nodes(mat)
    b = N['Principled BSDF']
    a = attr_node(N, 'mask')
    sep = N.new('ShaderNodeSeparateColor')
    sep.location = (-700, 0)
    L.new(a.outputs['Color'], sep.inputs[0])
    # subtle mottling so skin is not plastic
    tex = N.new('ShaderNodeTexNoise')
    tex.location = (-900, -300)
    tex.inputs['Scale'].default_value = 180.0
    tex.inputs['Detail'].default_value = 3.0
    mott = mix_rgb(N, L, 0.06, skin, tuple(np.array(skin) * 0.85), x=-650, y=-250)
    L.new(tex.outputs['Fac'], mott.inputs['Factor'])
    m1 = mix_rgb(N, L, sep.outputs['Green'], mott.outputs[2], blush, x=-450, y=-100)
    # blush amount scaling
    mm = N.new('ShaderNodeMath')
    mm.operation = 'MULTIPLY'
    mm.inputs[1].default_value = blush_amt
    mm.location = (-600, -100)
    L.new(sep.outputs['Green'], mm.inputs[0])
    L.new(mm.outputs[0], m1.inputs['Factor'])
    m2 = mix_rgb(N, L, sep.outputs['Red'], m1.outputs[2], lip, x=-250, y=0)
    m3 = mix_rgb(N, L, sep.outputs['Blue'], m2.outputs[2], interior, x=-100, y=100)
    L.new(m3.outputs[2], b.inputs['Base Color'])
    # interior should not glint
    rr = N.new('ShaderNodeMapRange')
    rr.location = (-250, -350)
    L.new(sep.outputs['Blue'], rr.inputs['Value'])
    rr.inputs['To Min'].default_value = 0.45
    rr.inputs['To Max'].default_value = 0.85
    L.new(rr.outputs[0], b.inputs['Roughness'])
    # pore bump
    bump = N.new('ShaderNodeBump')
    bump.location = (-250, -550)
    bump.inputs['Strength'].default_value = 0.05
    bump.inputs['Distance'].default_value = 0.0005
    L.new(tex.outputs['Fac'], bump.inputs['Height'])
    L.new(bump.outputs['Normal'], b.inputs['Normal'])
    return mat


def lid_material(name, skin, lash=(0.05, 0.03, 0.025)):
    mat = principled(name, skin, rough=0.66, sss=0.10, sss_scale=0.004, spec=0.28)
    nt, N, L = _nodes(mat)
    b = N['Principled BSDF']
    a = attr_node(N, 'lash')
    m = mix_rgb(N, L, a.outputs['Fac'], skin, lash, x=-300)
    L.new(m.outputs[2], b.inputs['Base Color'])
    return mat


def eye_material(name, iris=(0.25, 0.42, 0.20), iris_ang=0.70, pupil_ang=0.30):
    """Eyeball shader in object space: forward is local -Y."""
    mat = principled(name, (0.92, 0.90, 0.86), rough=0.15, coat=1.0, spec=0.6)
    nt, N, L = _nodes(mat)
    b = N['Principled BSDF']
    tc = N.new('ShaderNodeTexCoord')
    tc.location = (-1400, 0)
    nrm = N.new('ShaderNodeVectorMath')
    nrm.operation = 'NORMALIZE'
    nrm.location = (-1200, 0)
    L.new(tc.outputs['Object'], nrm.inputs[0])
    dot = N.new('ShaderNodeVectorMath')
    dot.operation = 'DOT_PRODUCT'
    dot.location = (-1000, 0)
    dot.inputs[1].default_value = (0, -1, 0)
    L.new(nrm.outputs[0], dot.inputs[0])
    c = dot.outputs['Value']
    ci, cp = float(np.cos(iris_ang)), float(np.cos(pupil_ang))

    def ramp(lo, hi, x, y):
        mr = N.new('ShaderNodeMapRange')
        mr.interpolation_type = 'SMOOTHSTEP'
        mr.location = (x, y)
        L.new(c, mr.inputs['Value'])
        mr.inputs['From Min'].default_value = lo
        mr.inputs['From Max'].default_value = hi
        return mr.outputs[0]

    iris_m = ramp(ci - 0.012, ci + 0.008, -800, 200)
    pupil_m = ramp(cp - 0.01, cp + 0.006, -800, 0)
    limbal = ramp(ci, ci + 0.05, -800, -200)  # 0 at edge -> 1 inward
    # iris colour: dark limbal ring + radial streaks
    noise = N.new('ShaderNodeTexNoise')
    noise.location = (-1000, -400)
    noise.inputs['Scale'].default_value = 40.0
    L.new(tc.outputs['Object'], noise.inputs['Vector'])
    iris_dark = tuple(np.array(iris) * 0.35)
    ic = mix_rgb(N, L, limbal, iris_dark, iris, x=-600, y=-200)
    iris_light = tuple(np.clip(np.array(iris) * 1.5 + 0.05, 0, 1))
    ic2 = mix_rgb(N, L, noise.outputs['Fac'], ic.outputs[2], iris_light, x=-450, y=-250)
    ic2.inputs['Factor'].default_value = 0.0
    fm = N.new('ShaderNodeMath')
    fm.operation = 'MULTIPLY'
    fm.inputs[1].default_value = 0.45
    fm.location = (-600, -450)
    L.new(noise.outputs['Fac'], fm.inputs[0])
    L.new(fm.outputs[0], ic2.inputs['Factor'])
    # sclera slightly warmer toward the back
    white = mix_rgb(N, L, ramp(-0.2, 0.6, -800, 400), (0.82, 0.70, 0.66), (0.95, 0.94, 0.91), x=-600, y=300)
    e1 = mix_rgb(N, L, iris_m, white.outputs[2], ic2.outputs[2], x=-300, y=100)
    e2 = mix_rgb(N, L, pupil_m, e1.outputs[2], (0.01, 0.01, 0.012), x=-150, y=100)
    L.new(e2.outputs[2], b.inputs['Base Color'])
    return mat


def hair_material(name, color, rough=0.45):
    mat = bpy.data.materials.new(name)
    nt, N, L = _nodes(mat)
    for n in list(N):
        if n.type == 'BSDF_PRINCIPLED':
            N.remove(n)
    h = N.new('ShaderNodeBsdfHairPrincipled')
    h.location = (-200, 0)
    h.parametrization = 'COLOR'
    h.inputs['Color'].default_value = (*color, 1)
    h.inputs['Roughness'].default_value = rough
    h.inputs['Radial Roughness'].default_value = 0.6
    for k, v in (('Coat', 0.1), ('Random Color', 0.08), ('Random Roughness', 0.2)):
        if k in h.inputs:
            try:
                h.inputs[k].default_value = v
            except Exception:
                pass
    L.new(h.outputs[0], N['Material Output'].inputs['Surface'])
    return mat


def cloth_material(name, color, rough=0.85, sheen=0.4, scale=220.0, bump_str=0.18, stripe=None):
    mat = principled(name, color, rough=rough, sheen=sheen, spec=0.25)
    nt, N, L = _nodes(mat)
    b = N['Principled BSDF']
    tc = N.new('ShaderNodeTexCoord')
    tc.location = (-1200, -300)
    w = N.new('ShaderNodeTexWave')
    w.location = (-900, -300)
    w.inputs['Scale'].default_value = scale
    w.inputs['Distortion'].default_value = 2.0
    w.bands_direction = 'DIAGONAL'
    L.new(tc.outputs['Object'], w.inputs['Vector'])
    n = N.new('ShaderNodeTexNoise')
    n.location = (-900, -550)
    n.inputs['Scale'].default_value = 18.0
    n.inputs['Detail'].default_value = 4.0
    L.new(tc.outputs['Object'], n.inputs['Vector'])
    add = N.new('ShaderNodeMath')
    add.operation = 'ADD'
    add.location = (-650, -400)
    L.new(w.outputs['Fac'], add.inputs[0])
    L.new(n.outputs['Fac'], add.inputs[1])
    bump = N.new('ShaderNodeBump')
    bump.location = (-400, -400)
    bump.inputs['Strength'].default_value = bump_str
    bump.inputs['Distance'].default_value = 0.002
    L.new(add.outputs[0], bump.inputs['Height'])
    L.new(bump.outputs['Normal'], b.inputs['Normal'])
    # wear / colour variation
    var = mix_rgb(N, L, n.outputs['Fac'], tuple(np.array(color) * 0.82), tuple(np.clip(np.array(color) * 1.12, 0, 1)), x=-400, y=100)
    L.new(var.outputs[2], b.inputs['Base Color'])
    return mat


def assign(ob, mat):
    ob.data.materials.clear()
    ob.data.materials.append(mat)


# ---------------------------------------------------------------- parenting
def parent_to_bone(ob, arm, bone_name):
    """Rigidly parent ob to a bone, keeping its (unparented) transform."""
    mw = ob.matrix_basis.copy()
    ob.parent = arm
    ob.parent_type = 'BONE'
    ob.parent_bone = bone_name
    b = arm.data.bones[bone_name]
    tail = arm.matrix_world @ b.matrix_local @ Matrix.Translation((0, b.length, 0))
    ob.matrix_parent_inverse = tail.inverted()
    ob.matrix_basis = mw


def armature_mod(ob, arm):
    m = ob.modifiers.new('Armature', 'ARMATURE')
    m.object = arm
    m.use_vertex_groups = True
    m.use_deform_preserve_volume = False
    return m
