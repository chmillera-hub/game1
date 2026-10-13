"""Props and effects (run inside Blender)."""
import math
import numpy as np
import bpy
from mathutils import Vector, Matrix, Euler

import blib
from character import loft, ellipse


def _new(name, V, F, mat, coll, sub=1, smooth=True):
    ob = blib.make_mesh(name, V, F, coll=coll, smooth=smooth)
    if mat:
        blib.assign(ob, mat)
    if sub:
        blib.subsurf(ob, sub)
    return ob


def cane(coll, length=0.88):
    """Bamboo cane in local space: shaft along -Z from the crook at origin, crook curls toward -Y."""
    m = blib.principled('bamboo', (0.55, 0.40, 0.18), rough=0.35, coat=0.3)
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    tc = N.new('ShaderNodeTexCoord')
    w = N.new('ShaderNodeTexWave')
    w.bands_direction = 'Z'
    w.inputs['Scale'].default_value = 3.2
    w.wave_profile = 'SAW'
    L.new(tc.outputs['Object'], w.inputs['Vector'])
    mr = N.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = 0.93
    mr.inputs['From Max'].default_value = 0.98
    L.new(w.outputs['Fac'], mr.inputs['Value'])
    c = blib.mix_rgb(N, L, mr.outputs[0], (0.55, 0.40, 0.18), (0.25, 0.15, 0.06))
    L.new(c.outputs[2], N['Principled BSDF'].inputs['Base Color'])
    pts = []
    # crook: semicircle of radius 0.05 starting at the top of the shaft
    R = 0.05
    for a in np.linspace(0, np.pi * 1.05, 14):
        pts.append([0, -R + R * np.cos(a) * -1 + 0.0, R * np.sin(a)])
    pts = pts[::-1]
    pts = [[0, -R - R * np.cos(a), R * np.sin(a)] for a in np.linspace(np.pi * 1.05, 0, 14)]
    for z in np.linspace(0, -length, 16)[1:]:
        pts.append([0, 0.0, z])
    pts = np.array(pts)
    secs = [ellipse(10, 0.011, 0.011) for _ in pts]
    V, F, ring = loft(pts, secs, up_hint=(1, 0, 0))
    ob = _new('cane', V, F, m, coll)
    # black tape on the crook
    mt = blib.principled('tape', (0.015, 0.015, 0.015), rough=0.6)
    tp = pts[3:12]
    V2, F2, _ = loft(tp, [ellipse(10, 0.0125, 0.0125) for _ in tp], up_hint=(1, 0, 0))
    t = _new('cane_tape', V2, F2, mt, coll)
    t.parent = ob
    return ob


def loaf(coll, name='rye', torn=False, paper=True):
    """Small seeded rye (about 22 cm) in brown paper. Origin at the loaf centre, long axis X."""
    mb = blib.principled(name + '_crust', (0.30, 0.16, 0.06), rough=0.65, coat=0.15)
    N, L = mb.node_tree.nodes, mb.node_tree.links
    tc = N.new('ShaderNodeTexCoord')
    vor = N.new('ShaderNodeTexVoronoi')
    vor.inputs['Scale'].default_value = 140.0
    L.new(tc.outputs['Object'], vor.inputs['Vector'])
    mr = N.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = 0.0
    mr.inputs['From Max'].default_value = 0.12
    mr.inputs['To Min'].default_value = 1.0
    mr.inputs['To Max'].default_value = 0.0
    L.new(vor.outputs['Distance'], mr.inputs['Value'])
    c = blib.mix_rgb(N, L, mr.outputs[0], (0.30, 0.16, 0.06), (0.62, 0.52, 0.32))
    L.new(c.outputs[2], N['Principled BSDF'].inputs['Base Color'])
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=32, ring_count=16)
    ob = bpy.context.object
    for cc in ob.users_collection:
        cc.objects.unlink(ob)
    coll.objects.link(ob)
    ob.name = name
    ob.data.transform(Matrix.Diagonal((0.11, 0.055, 0.045, 1)))
    for v in ob.data.vertices:
        if v.co.z < 0:
            v.co.z *= 0.5
    bpy.ops.object.shade_smooth()
    blib.assign(ob, mb)
    parts = [ob]
    if paper:
        mp = blib.cloth_material(name + '_paper', (0.52, 0.38, 0.22), rough=0.8, sheen=0.1, scale=60, bump_str=0.25)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=32, ring_count=16)
        pp = bpy.context.object
        for cc in pp.users_collection:
            cc.objects.unlink(pp)
        coll.objects.link(pp)
        pp.name = name + '_paper'
        pp.data.transform(Matrix.Diagonal((0.085, 0.064, 0.052, 1)))
        for v in pp.data.vertices:
            v.co.x -= 0.035
            if v.co.z < 0:
                v.co.z *= 0.55
            # crumple
            v.co *= 1 + 0.05 * math.sin(v.co.x * 180) * math.sin(v.co.y * 140)
        bpy.ops.object.shade_smooth()
        blib.assign(pp, mp)
        pp.parent = ob
        parts.append(pp)
    return ob


def roll(coll, name='roll', r=0.035):
    m = blib.principled(name + '_m', (0.55, 0.30, 0.10), rough=0.5, coat=0.2)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=20, ring_count=10)
    ob = bpy.context.object
    for cc in ob.users_collection:
        cc.objects.unlink(ob)
    coll.objects.link(ob)
    ob.name = name
    ob.scale = (1.2, 1.0, 0.85)
    bpy.ops.object.shade_smooth()
    blib.assign(ob, m)
    return ob


def banana_peel(coll, name='peel'):
    m = blib.principled(name + '_m', (0.75, 0.55, 0.06), rough=0.5, coat=0.2)
    N, L = m.node_tree.nodes, m.node_tree.links
    n = N.new('ShaderNodeTexNoise')
    n.inputs['Scale'].default_value = 25
    mr = N.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = 0.55
    mr.inputs['From Max'].default_value = 0.7
    L.new(n.outputs['Fac'], mr.inputs['Value'])
    c = blib.mix_rgb(N, L, mr.outputs[0], (0.75, 0.55, 0.06), (0.25, 0.15, 0.03))
    L.new(c.outputs[2], N['Principled BSDF'].inputs['Base Color'])
    V, F = [], []
    # four petals radiating from a stub
    for k, ang in enumerate((0.3, 1.9, 3.4, 4.9)):
        pts = []
        for i, t in enumerate(np.linspace(0, 1, 8)):
            r = 0.02 + 0.09 * t
            z = 0.018 * (1 - t) ** 1.5 + 0.004
            pts.append([r * math.cos(ang + 0.15 * t), r * math.sin(ang + 0.15 * t), z])
        secs = [ellipse(8, 0.004, 0.016 * math.sin(math.pi * min(0.95, 0.15 + i / 8)) + 0.003) for i in range(len(pts))]
        Vp, Fp, _ = loft(pts, secs, up_hint=(0, 0, 1))
        off = len(V)
        V += list(Vp)
        F += [tuple(j + off for j in f) for f in Fp]
    stub = [[0, 0, 0.004], [0, 0, 0.03], [0.006, 0, 0.045]]
    Vs, Fs, _ = loft(stub, [ellipse(8, 0.012, 0.012), ellipse(8, 0.009, 0.009), ellipse(8, 0.005, 0.005)], up_hint=(1, 0, 0))
    off = len(V)
    V += list(Vs)
    F += [tuple(j + off for j in f) for f in Fs]
    return _new(name, np.array(V), F, m, coll)


def coin(coll, name='coin'):
    m = blib.principled(name + '_m', (0.75, 0.55, 0.25), rough=0.3, metallic=1.0)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=0.002, vertices=16)
    ob = bpy.context.object
    for cc in ob.users_collection:
        cc.objects.unlink(ob)
    coll.objects.link(ob)
    ob.name = name
    blib.assign(ob, m)
    return ob


def sack(coll, name='sack'):
    m = blib.cloth_material(name + '_m', (0.70, 0.64, 0.50), rough=0.95, scale=200, bump_str=0.4)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=24, ring_count=12)
    ob = bpy.context.object
    for cc in ob.users_collection:
        cc.objects.unlink(ob)
    coll.objects.link(ob)
    ob.name = name
    ob.data.transform(Matrix.Diagonal((0.20, 0.13, 0.30, 1)))
    for v in ob.data.vertices:
        if v.co.z < -0.15:
            v.co.z = -0.15 - (v.co.z + 0.15) * 0.3
        if v.co.z > 0.18:
            v.co.x *= 0.6
            v.co.y *= 0.6
    bpy.ops.object.shade_smooth()
    blib.assign(ob, m)
    blib.subsurf(ob, 1)
    return ob


def basket(coll, name='basket'):
    m = blib.cloth_material(name + '_m', (0.45, 0.30, 0.14), rough=0.8, scale=90, bump_str=0.8)
    prof = [(0.10, 0.0), (0.13, 0.13), (0.125, 0.13), (0.095, 0.01)]
    V, F = [], []
    K = 28
    for (r, z) in prof:
        for k in range(K):
            a = 2 * np.pi * k / K
            V.append([r * np.cos(a) * 1.3, r * np.sin(a), z])
    for i in range(len(prof) - 1):
        for k in range(K):
            a_ = i * K + k
            b_ = i * K + (k + 1) % K
            F.append((a_, b_, b_ + K, a_ + K))
    ob = _new(name, np.array(V), F, m, coll)
    # handle
    pts = [[0.16 * math.cos(a) * 1.0, 0, 0.13 + 0.14 * math.sin(a)] for a in np.linspace(0, np.pi, 12)]
    Vh, Fh, _ = loft(pts, [ellipse(8, 0.008, 0.008)] * len(pts), up_hint=(0, 1, 0))
    h = _new(name + '_handle', Vh, Fh, m, coll)
    h.parent = ob
    return ob


def newspaper(coll, name='paper_prop'):
    m = blib.principled(name + '_m', (0.72, 0.70, 0.64), rough=0.85)
    N, L = m.node_tree.nodes, m.node_tree.links
    tc = N.new('ShaderNodeTexCoord')
    w = N.new('ShaderNodeTexWave')
    w.bands_direction = 'Y'
    w.inputs['Scale'].default_value = 60
    L.new(tc.outputs['Object'], w.inputs['Vector'])
    c = blib.mix_rgb(N, L, w.outputs['Fac'], (0.72, 0.70, 0.64), (0.45, 0.44, 0.40))
    c.inputs['Factor'].default_value = 0.3
    L.new(c.outputs[2], N['Principled BSDF'].inputs['Base Color'])
    V = np.array([[-0.14, -0.10, 0], [0.14, -0.10, 0], [0.14, 0.10, 0], [-0.14, 0.10, 0]])
    ob = _new(name, V, [(0, 1, 2, 3)], m, coll, sub=0)
    s = ob.modifiers.new('sol', 'SOLIDIFY')
    s.thickness = 0.012
    return ob


def snow_dots(coll, name, pts, r=0.006):
    """Static clump of snow (e.g. on shoulders): small spheres at given points (world space)."""
    m = blib.principled(name + '_m', (0.92, 0.94, 0.98), rough=0.6, sss=0.2, sss_scale=0.002)
    V, F = [], []
    for p in pts:
        bpy_v = None
        off = len(V)
        n = 6
        for i in range(n + 1):
            th = math.pi * i / n
            for k in range(8):
                ph = 2 * math.pi * k / 8
                V.append([p[0] + r * math.sin(th) * math.cos(ph), p[1] + r * math.sin(th) * math.sin(ph), p[2] + r * 0.6 * math.cos(th)])
        for i in range(n):
            for k in range(8):
                a = off + i * 8 + k
                b = off + i * 8 + (k + 1) % 8
                F.append((a, b, b + 8, a + 8))
    return _new(name, np.array(V), F, m, coll, sub=0)


# ------------------------------------------------------------------ snowfall
def snowfall(coll, center=(0, 1.0, 0), size=(14, 12, 7), count=9000, speed=0.45, seed=3):
    """Falling snow via geometry nodes driven by scene time (deterministic, no cache)."""
    me = bpy.data.meshes.new('snow_base')
    ob = bpy.data.objects.new('snowfall', me)
    coll.objects.link(ob)
    ob.location = center
    mod = ob.modifiers.new('snow', 'NODES')
    ng = bpy.data.node_groups.new('SnowGN', 'GeometryNodeTree')
    mod.node_group = ng
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    N, L = ng.nodes, ng.links
    out = N.new('NodeGroupOutput')
    pts = N.new('GeometryNodePoints')
    pts.inputs['Count'].default_value = count
    idx = N.new('GeometryNodeInputIndex')
    rnd = N.new('FunctionNodeRandomValue')
    rnd.data_type = 'FLOAT_VECTOR'
    rnd.inputs['Min'].default_value = (-size[0] / 2, -size[1] / 2, 0.0)
    rnd.inputs['Max'].default_value = (size[0] / 2, size[1] / 2, size[2])
    rnd.inputs['Seed'].default_value = seed
    L.new(idx.outputs[0], rnd.inputs['ID'])
    rsp = N.new('FunctionNodeRandomValue')
    rsp.data_type = 'FLOAT'
    rsp.inputs[2].default_value = 0.75
    rsp.inputs[3].default_value = 1.25
    rsp.inputs['Seed'].default_value = seed + 1
    L.new(idx.outputs[0], rsp.inputs['ID'])
    time = N.new('GeometryNodeInputSceneTime')
    sep = N.new('ShaderNodeSeparateXYZ')
    L.new(rnd.outputs['Value'], sep.inputs[0])
    # z = mod(z0 - speed*rs*t, H)
    mul = N.new('ShaderNodeMath')
    mul.operation = 'MULTIPLY'
    L.new(time.outputs['Seconds'], mul.inputs[0])
    L.new(rsp.outputs[1], mul.inputs[1])
    mul2 = N.new('ShaderNodeMath')
    mul2.operation = 'MULTIPLY'
    mul2.inputs[1].default_value = speed
    L.new(mul.outputs[0], mul2.inputs[0])
    sub = N.new('ShaderNodeMath')
    sub.operation = 'SUBTRACT'
    L.new(sep.outputs['Z'], sub.inputs[0])
    L.new(mul2.outputs[0], sub.inputs[1])
    md = N.new('ShaderNodeMath')
    md.operation = 'FLOORED_MODULO'
    md.inputs[1].default_value = size[2]
    L.new(sub.outputs[0], md.inputs[0])
    # drift in x: x0 + 0.12*sin(t*1.3 + z0*2)
    ph = N.new('ShaderNodeMath')
    ph.operation = 'MULTIPLY_ADD'
    ph.inputs[1].default_value = 1.3
    L.new(time.outputs['Seconds'], ph.inputs[0])
    L.new(sep.outputs['Z'], ph.inputs[2])
    sn = N.new('ShaderNodeMath')
    sn.operation = 'SINE'
    L.new(ph.outputs[0], sn.inputs[0])
    dx = N.new('ShaderNodeMath')
    dx.operation = 'MULTIPLY_ADD'
    dx.inputs[1].default_value = 0.10
    L.new(sn.outputs[0], dx.inputs[0])
    L.new(sep.outputs['X'], dx.inputs[2])
    comb = N.new('ShaderNodeCombineXYZ')
    L.new(dx.outputs[0], comb.inputs['X'])
    L.new(sep.outputs['Y'], comb.inputs['Y'])
    L.new(md.outputs[0], comb.inputs['Z'])
    L.new(comb.outputs[0], pts.inputs['Position'])
    rr = N.new('FunctionNodeRandomValue')
    rr.data_type = 'FLOAT'
    rr.inputs[2].default_value = 0.0028
    rr.inputs[3].default_value = 0.0065
    rr.inputs['Seed'].default_value = seed + 2
    L.new(idx.outputs[0], rr.inputs['ID'])
    L.new(rr.outputs[1], pts.inputs['Radius'])
    ico = N.new('GeometryNodeMeshIcoSphere')
    ico.inputs['Radius'].default_value = 1.0
    ico.inputs['Subdivisions'].default_value = 1
    inst = N.new('GeometryNodeInstanceOnPoints')
    L.new(pts.outputs['Points'], inst.inputs['Points'])
    L.new(ico.outputs['Mesh'], inst.inputs['Instance'])
    rad = N.new('GeometryNodeInputRadius')
    sc = N.new('ShaderNodeCombineXYZ')
    L.new(rad.outputs[0], sc.inputs['X'])
    L.new(rad.outputs[0], sc.inputs['Y'])
    mz = N.new('ShaderNodeMath')
    mz.operation = 'MULTIPLY'
    mz.inputs[1].default_value = 1.5
    L.new(rad.outputs[0], mz.inputs[0])
    L.new(mz.outputs[0], sc.inputs['Z'])
    L.new(sc.outputs[0], inst.inputs['Scale'])
    mat = blib.principled('snowflake', (0.95, 0.96, 1.0), rough=0.5, emission=(0.9, 0.92, 1.0), estr=0.15)
    # cull flakes close to the active camera (they would render as huge blobs)
    camn = N.new('GeometryNodeInputActiveCamera')
    oi = N.new('GeometryNodeObjectInfo')
    oi.transform_space = 'RELATIVE'
    L.new(camn.outputs[0], oi.inputs['Object'])
    pos = N.new('GeometryNodeInputPosition')
    dist = N.new('ShaderNodeVectorMath')
    dist.operation = 'DISTANCE'
    L.new(pos.outputs[0], dist.inputs[0])
    L.new(oi.outputs['Location'], dist.inputs[1])
    lt = N.new('FunctionNodeCompare')
    lt.data_type = 'FLOAT'
    lt.operation = 'LESS_THAN'
    lt.inputs[1].default_value = 1.6
    L.new(dist.outputs['Value'], lt.inputs[0])
    dele = N.new('GeometryNodeDeleteGeometry')
    dele.domain = 'POINT'
    L.new(pts.outputs['Points'], dele.inputs['Geometry'])
    L.new(lt.outputs['Result'], dele.inputs['Selection'])
    L.new(dele.outputs['Geometry'], inst.inputs['Points'])
    setm = N.new('GeometryNodeSetMaterial')
    setm.inputs['Material'].default_value = mat
    L.new(inst.outputs['Instances'], setm.inputs['Geometry'])
    L.new(setm.outputs['Geometry'], out.inputs[0])
    ob.visible_shadow = False
    return ob
