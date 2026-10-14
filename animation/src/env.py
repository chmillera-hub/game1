"""Town square set (run inside Blender).

Layout (metres): street runs along X; the shop row faces -Y with its facade
plane at y = 4.0; the sidewalk spans y = 2.6 .. 4.0 at z = 0.14.
The bakery door is centred at x = -0.9, the bakery window spans x = 0.0 .. 2.2,
the spot by the bakery wall where someone sits is around x = 2.9, y = 3.7.
Lamppost at x = 1.9, y = 2.85.  Clock tower behind the roofs at x = 3.5, y = 14.
"""
import math
import numpy as np
import bpy
from mathutils import Vector, Matrix, Euler

import blib
from blib import _nodes, mix_rgb

SIDEWALK_Z = 0.14
FACADE_Y = 4.0
LAMP_XY = (1.9, 4.0 - 1.15)
LAMP_EXPOSURE = 1.5             # lamp_light power scale (2^x) over the watts film.lamp keys
SILL_X = None
SILL_H = 0.0
TOWER = (2.6, 9.0, 13.2)      # x, y, dial-centre height (cheated per shot)
DIAL_R = 1.9
EDITH_XY = (2.95, 4.0 - 0.30)
PATCH_XY = (1.3, 2.4)
BENCH_XY = (-3.2, 4.0 - 0.62)


def _obj_from_ops(coll):
    ob = bpy.context.object
    for c in ob.users_collection:
        c.objects.unlink(ob)
    coll.objects.link(ob)
    return ob


def box(coll, name, size, loc, mat, rot=(0, 0, 0), bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    ob = _obj_from_ops(coll)
    ob.name = name
    ob.data.transform(Matrix.Diagonal((*size, 1.0)))
    if bevel:
        m = ob.modifiers.new('bev', 'BEVEL')
        m.width = bevel
        m.segments = 2
        m.limit_method = 'ANGLE'
    if mat:
        blib.assign(ob, mat)
    return ob


def cyl(coll, name, r, depth, loc, mat, verts=24, rot=(0, 0, 0), smooth=True):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc, vertices=verts, rotation=rot)
    ob = _obj_from_ops(coll)
    ob.name = name
    if smooth:
        bpy.ops.object.shade_smooth()
    if mat:
        blib.assign(ob, mat)
    return ob


# ------------------------------------------------------------------ materials
def _math(N, L, op, a, b=None, c=None):
    """Math node; a/b/c are sockets or numbers."""
    m = N.new('ShaderNodeMath')
    m.operation = op
    for i, v in enumerate((a, b, c)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            m.inputs[i].default_value = v
        else:
            L.new(v, m.inputs[i])
    return m.outputs[0]


def _remap(N, L, sock, a, b, c, d, smooth=True):
    """Map Range sock [a, b] -> [c, d] (clamped)."""
    m = N.new('ShaderNodeMapRange')
    if smooth:
        m.interpolation_type = 'SMOOTHSTEP'
    for k, v in (('From Min', a), ('From Max', b), ('To Min', c), ('To Max', d)):
        m.inputs[k].default_value = v
    L.new(sock, m.inputs['Value'])
    return m.outputs['Result']


def _noise(N, L, vec, scale, detail=2.0, rough=0.5):
    n = N.new('ShaderNodeTexNoise')
    n.inputs['Scale'].default_value = scale
    n.inputs['Detail'].default_value = detail
    n.inputs['Roughness'].default_value = rough
    L.new(vec, n.inputs['Vector'])
    return n


def _mul(N, L, col, other, fac=1.0):
    """Multiply-blend a colour socket by another colour/float socket (or a constant colour)."""
    m = N.new('ShaderNodeMix')
    m.data_type = 'RGBA'
    m.blend_type = 'MULTIPLY'
    if isinstance(fac, (int, float)):
        m.inputs['Factor'].default_value = fac
    else:
        L.new(fac, m.inputs['Factor'])
    L.new(col, m.inputs[6])
    if isinstance(other, tuple):
        m.inputs[7].default_value = (*other[:3], 1)
    else:
        L.new(other, m.inputs[7])
    return m.outputs[2]


def brick_mat(name, base=(0.34, 0.15, 0.10), mortar=(0.19, 0.175, 0.155), scale=1.0):
    """Weathered brick in world space (facade plane x+y / z): per-brick tone, hand-laid courses,
    mottling, soot and streaky rising damp above the pavement.  Nodes and noise octaves are
    kept few (the height graph runs 3x for the bump) so it costs about what the plain one did."""
    mat = bpy.data.materials.new(name)
    nt, N, L = _nodes(mat)
    b = N['Principled BSDF']
    geo = N.new('ShaderNodeNewGeometry')
    mp = N.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (scale, scale, scale)
    L.new(geo.outputs['Position'], mp.inputs['Vector'])
    P = mp.outputs['Vector']
    # brick texture works in XY: map the facade plane (x, z) -> (x, y)
    sep = N.new('ShaderNodeSeparateXYZ')
    L.new(P, sep.inputs[0])
    comb = N.new('ShaderNodeCombineXYZ')
    L.new(_math(N, L, 'ADD', sep.outputs['X'], sep.outputs['Y']), comb.inputs['X'])
    L.new(sep.outputs['Z'], comb.inputs['Y'])
    # hand-laid courses: the joints wander by a few millimetres
    wob = _noise(N, L, comb.outputs[0], 7.0, 0.0)
    bv = N.new('ShaderNodeVectorMath')
    bv.operation = 'MULTIPLY_ADD'
    L.new(wob.outputs['Fac'], bv.inputs[0])
    bv.inputs[1].default_value = (0.014, 0.008, 0.0)
    L.new(comb.outputs[0], bv.inputs[2])

    def bricks(vec, c1, c2, mort):
        br = N.new('ShaderNodeTexBrick')
        br.inputs['Scale'].default_value = 2.0
        br.inputs['Mortar Size'].default_value = 0.014
        br.inputs['Mortar Smooth'].default_value = 0.9
        br.inputs['Bias'].default_value = 0.0
        br.inputs['Brick Width'].default_value = 0.42
        br.inputs['Row Height'].default_value = 0.13
        br.offset = 0.5
        br.inputs['Color1'].default_value = (*c1, 1)
        br.inputs['Color2'].default_value = (*c2, 1)
        br.inputs['Mortar'].default_value = (*mort, 1)
        L.new(vec, br.inputs['Vector'])
        return br
    br = bricks(bv.outputs[0], base, tuple(np.array(base) * (0.80, 0.70, 0.68)), mortar)
    # a second, independent random value per brick: the same grid shifted by whole bricks
    # (5 bricks across, an even 6 courses up, so the half-brick bond stays aligned)
    sh = N.new('ShaderNodeVectorMath')
    sh.operation = 'ADD'
    L.new(bv.outputs[0], sh.inputs[0])
    sh.inputs[1].default_value = (5 * 0.21, 6 * 0.065, 0.0)
    rnd = bricks(sh.outputs[0], (0, 0, 0), (1, 1, 1), (0.6, 0.6, 0.6))
    tone = N.new('ShaderNodeValToRGB')
    cr = tone.color_ramp
    cr.elements[0].position = 0.0
    cr.elements[0].color = (0.45, 0.40, 0.42, 1)      # over-fired, purple-brown
    cr.elements[1].position = 1.0
    cr.elements[1].color = (1.12, 1.0, 0.80, 1)       # paler, sandier
    for pos, c in ((0.10, (0.66, 0.60, 0.60)), (0.40, (0.90, 0.88, 0.86)), (0.80, (1.0, 0.95, 0.88))):
        e = cr.elements.new(pos)
        e.color = (*c, 1)
    L.new(rnd.outputs['Color'], tone.inputs['Fac'])
    col = _mul(N, L, br.outputs['Color'], tone.outputs['Color'])
    # mottling inside each brick
    mot = _noise(N, L, P, 18.0, 2.0, 0.6)
    col = _mul(N, L, col, _remap(N, L, mot.outputs['Fac'], 0.3, 0.7, 0.78, 1.08, smooth=False))
    # soot / grime, patchy from hand size up to the whole pier
    grime = _noise(N, L, P, 1.8, 4.0, 0.62)
    gr = N.new('ShaderNodeValToRGB')
    gr.color_ramp.elements[0].position = 0.36
    gr.color_ramp.elements[0].color = (0.40, 0.37, 0.35, 1)
    gr.color_ramp.elements[1].position = 0.64
    gr.color_ramp.elements[1].color = (1, 1, 1, 1)
    L.new(grime.outputs['Fac'], gr.inputs['Fac'])
    col = _mul(N, L, col, gr.outputs['Color'], 0.9)
    # rising damp: darker and a little glossier above the pavement, its edge wicking up in
    # vertical streaks (noise stretched along z)
    st = N.new('ShaderNodeMapping')
    st.inputs['Scale'].default_value = (11.0, 0.9, 1.0)
    L.new(comb.outputs[0], st.inputs['Vector'])
    dn = _noise(N, L, st.outputs['Vector'], 1.6, 2.0)
    zz = _math(N, L, 'MULTIPLY_ADD', dn.outputs['Fac'], 0.5, sep.outputs['Z'])
    damp = _remap(N, L, zz, 0.55, 1.15, 1.0, 0.0)
    col = _mul(N, L, col, (0.56, 0.54, 0.54), _math(N, L, 'MULTIPLY', damp, 0.85))
    L.new(col, b.inputs['Base Color'])
    L.new(_remap(N, L, damp, 0.0, 1.0, 0.92, 0.72, smooth=False), b.inputs['Roughness'])
    # relief: recessed joints, fine pitting
    fine = _noise(N, L, P, 60.0, 2.0)
    h = _math(N, L, 'ADD', br.outputs['Fac'], _math(N, L, 'MULTIPLY', fine.outputs['Fac'], 0.5))
    bump = N.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.6
    bump.inputs['Distance'].default_value = 0.005     # shallow, soft joints: steeper reads as drawn outlines
    bump.invert = True
    L.new(h, bump.inputs['Height'])
    L.new(bump.outputs['Normal'], b.inputs['Normal'])
    return mat


def plaster_mat(name, color, stain=0.35):
    mat = bpy.data.materials.new(name)
    nt, N, L = _nodes(mat)
    b = N['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.9
    tc = N.new('ShaderNodeNewGeometry')
    n1 = N.new('ShaderNodeTexNoise')
    n1.inputs['Scale'].default_value = 1.6
    n1.inputs['Detail'].default_value = 5.0      # finer octaves are sub-pixel in every shot
    L.new(tc.outputs['Position'], n1.inputs['Vector'])
    ramp = N.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.4
    ramp.color_ramp.elements[0].color = (*(np.array(color) * (1 - stain)), 1)
    ramp.color_ramp.elements[1].position = 0.7
    ramp.color_ramp.elements[1].color = (*color, 1)
    L.new(n1.outputs['Fac'], ramp.inputs[0])
    # streaks running down (water stains)
    w = N.new('ShaderNodeTexWave')
    w.wave_type = 'BANDS'
    w.bands_direction = 'X'
    w.inputs['Scale'].default_value = 3.0
    w.inputs['Distortion'].default_value = 6.0
    w.inputs['Detail'].default_value = 4.0
    L.new(tc.outputs['Position'], w.inputs['Vector'])
    m = N.new('ShaderNodeMix')
    m.data_type = 'RGBA'
    m.blend_type = 'MULTIPLY'
    m.inputs['Factor'].default_value = 0.12
    L.new(ramp.outputs[0], m.inputs[6])
    L.new(w.outputs['Color'], m.inputs[7])
    L.new(m.outputs[2], b.inputs['Base Color'])
    n2 = N.new('ShaderNodeTexNoise')
    n2.inputs['Scale'].default_value = 40.0
    L.new(tc.outputs['Position'], n2.inputs['Vector'])
    bump = N.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.25
    L.new(n2.outputs['Fac'], bump.inputs['Height'])
    L.new(bump.outputs['Normal'], b.inputs['Normal'])
    return mat


def cobble_mat(name):
    mat = bpy.data.materials.new(name)
    nt, N, L = _nodes(mat)
    b = N['Principled BSDF']
    tc = N.new('ShaderNodeTexCoord')
    vor = N.new('ShaderNodeTexVoronoi')
    vor.feature = 'DISTANCE_TO_EDGE'
    vor.inputs['Scale'].default_value = 11.0
    vor.inputs['Randomness'].default_value = 0.65
    L.new(tc.outputs['Object'], vor.inputs['Vector'])
    vc = N.new('ShaderNodeTexVoronoi')
    vc.inputs['Scale'].default_value = 11.0
    vc.inputs['Randomness'].default_value = 0.65
    L.new(tc.outputs['Object'], vc.inputs['Vector'])
    edge = N.new('ShaderNodeMapRange')
    edge.interpolation_type = 'SMOOTHSTEP'
    edge.inputs['From Min'].default_value = 0.0
    edge.inputs['From Max'].default_value = 0.13
    L.new(vor.outputs['Distance'], edge.inputs['Value'])
    stone = N.new('ShaderNodeValToRGB')
    stone.color_ramp.elements[0].color = (0.17, 0.155, 0.14, 1)
    stone.color_ramp.elements[1].color = (0.36, 0.33, 0.29, 1)
    L.new(vc.outputs['Color'], stone.inputs[0])
    gap = mix_rgb(N, L, edge.outputs[0], (0.06, 0.055, 0.05), stone.outputs[0], x=-200, y=0)
    n = N.new('ShaderNodeTexNoise')
    n.inputs['Scale'].default_value = 30.0
    n.inputs['Detail'].default_value = 6.0
    L.new(tc.outputs['Object'], n.inputs['Vector'])
    dirt = N.new('ShaderNodeMix')
    dirt.data_type = 'RGBA'
    dirt.blend_type = 'MULTIPLY'
    dirt.inputs['Factor'].default_value = 0.35
    L.new(gap.outputs[2], dirt.inputs[6])
    L.new(n.outputs['Color'], dirt.inputs[7])
    L.new(dirt.outputs[2], b.inputs['Base Color'])
    rr = N.new('ShaderNodeMapRange')
    rr.inputs['To Min'].default_value = 0.95
    rr.inputs['To Max'].default_value = 0.55
    L.new(edge.outputs[0], rr.inputs['Value'])
    L.new(rr.outputs[0], b.inputs['Roughness'])
    hgt = N.new('ShaderNodeMath')
    hgt.operation = 'ADD'
    L.new(edge.outputs[0], hgt.inputs[0])
    nm = N.new('ShaderNodeMath')
    nm.operation = 'MULTIPLY'
    nm.inputs[1].default_value = 0.15
    L.new(n.outputs['Fac'], nm.inputs[0])
    L.new(nm.outputs[0], hgt.inputs[1])
    bump = N.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.45
    bump.inputs['Distance'].default_value = 0.01
    L.new(hgt.outputs[0], bump.inputs['Height'])
    L.new(bump.outputs['Normal'], b.inputs['Normal'])
    return mat


def slab_mat(name):
    mat = bpy.data.materials.new(name)
    nt, N, L = _nodes(mat)
    b = N['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.85
    tc = N.new('ShaderNodeTexCoord')
    br = N.new('ShaderNodeTexBrick')
    br.inputs['Scale'].default_value = 1.1
    br.inputs['Mortar Size'].default_value = 0.01
    br.inputs['Brick Width'].default_value = 0.9
    br.inputs['Row Height'].default_value = 0.6
    br.inputs['Color1'].default_value = (0.30, 0.29, 0.27, 1)
    br.inputs['Color2'].default_value = (0.24, 0.23, 0.22, 1)
    br.inputs['Mortar'].default_value = (0.08, 0.075, 0.07, 1)
    L.new(tc.outputs['Object'], br.inputs['Vector'])
    n = N.new('ShaderNodeTexNoise')
    n.inputs['Scale'].default_value = 12.0
    n.inputs['Detail'].default_value = 5
    L.new(tc.outputs['Object'], n.inputs['Vector'])
    m = N.new('ShaderNodeMix')
    m.data_type = 'RGBA'
    m.blend_type = 'MULTIPLY'
    m.inputs['Factor'].default_value = 0.4
    L.new(br.outputs['Color'], m.inputs[6])
    L.new(n.outputs['Color'], m.inputs[7])
    L.new(m.outputs[2], b.inputs['Base Color'])
    bump = N.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.4
    bump.invert = True
    L.new(br.outputs['Fac'], bump.inputs['Height'])
    L.new(bump.outputs['Normal'], b.inputs['Normal'])
    return mat


def wood_mat(name, color=(0.20, 0.10, 0.05)):
    mat = bpy.data.materials.new(name)
    nt, N, L = _nodes(mat)
    b = N['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.6
    tc = N.new('ShaderNodeTexCoord')
    w = N.new('ShaderNodeTexWave')
    w.wave_type = 'BANDS'
    w.bands_direction = 'Z'
    w.inputs['Scale'].default_value = 6.0
    w.inputs['Distortion'].default_value = 8.0
    w.inputs['Detail'].default_value = 3.0
    L.new(tc.outputs['Object'], w.inputs['Vector'])
    c = mix_rgb(N, L, w.outputs['Fac'], tuple(np.array(color) * 0.6), color)
    L.new(c.outputs[2], b.inputs['Base Color'])
    return mat


def glass_mat(name, interior=None, strength=0.0, tint=(0.05, 0.06, 0.07)):
    """Window: dark reflective glass, optionally lit from inside."""
    mat = bpy.data.materials.new(name)
    nt, N, L = _nodes(mat)
    b = N['Principled BSDF']
    b.inputs['Base Color'].default_value = (*tint, 1)
    b.inputs['Roughness'].default_value = 0.05
    b.inputs['Specular IOR Level'].default_value = 0.9
    if interior is not None:
        # a room behind the glass, not a flat card: lit back wall, darker floor band,
        # curtains at the sides, a little furniture mottling (Generated coords of the pane)
        tc = N.new('ShaderNodeTexCoord')
        sep = N.new('ShaderNodeSeparateXYZ')
        L.new(tc.outputs['Generated'], sep.inputs[0])
        dx = _math(N, L, 'ABSOLUTE', _math(N, L, 'SUBTRACT', sep.outputs['X'], 0.5))
        cur = _remap(N, L, dx, 0.28, 0.42, 1.0, 0.35)
        vert = N.new('ShaderNodeValToRGB')
        cr = vert.color_ramp
        cr.elements[0].position = 0.0
        cr.elements[0].color = (0.30, 0.30, 0.30, 1)
        cr.elements[1].position = 1.0
        cr.elements[1].color = (0.80, 0.80, 0.80, 1)
        for pos, v in ((0.32, 0.50), (0.55, 1.0)):
            e = cr.elements.new(pos)
            e.color = (v, v, v, 1)
        L.new(sep.outputs['Z'], vert.inputs['Fac'])
        blot = _noise(N, L, tc.outputs['Generated'], 2.5, 2.0)
        pat = _mul(N, L, vert.outputs['Color'], _math(N, L, 'MULTIPLY', cur, _remap(N, L, blot.outputs['Fac'], 0.4, 0.65, 0.72, 1.0)))
        L.new(_mul(N, L, pat, tuple(interior)), b.inputs['Emission Color'])
        b.inputs['Emission Strength'].default_value = strength * 1.25
    return mat


def pane_mat(name, tint=(0.86, 0.84, 0.76)):
    """Clear shop-door glass: see-through to the real interior (Transparent BSDF, so no
    refraction cost), Fresnel reflection of the street, a faint uneven film of grime
    (in the transmission tint, so it adds no lit closure)."""
    mat = bpy.data.materials.new(name)
    nt, N, L = _nodes(mat)
    for n in list(N):
        if n.type == 'BSDF_PRINCIPLED':
            N.remove(n)
    tc = N.new('ShaderNodeTexCoord')
    n = _noise(N, L, tc.outputs['Object'], 9.0, 2.0)
    tr = N.new('ShaderNodeBsdfTransparent')
    L.new(_mul(N, L, _remap(N, L, n.outputs['Fac'], 0.35, 0.7, 1.0, 0.82), tint), tr.inputs['Color'])
    gl = N.new('ShaderNodeBsdfGlossy')
    gl.inputs['Roughness'].default_value = 0.04
    fr = N.new('ShaderNodeFresnel')
    fr.inputs['IOR'].default_value = 1.6
    mx = N.new('ShaderNodeMixShader')
    L.new(fr.outputs[0], mx.inputs[0])
    L.new(tr.outputs[0], mx.inputs[1])
    L.new(gl.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], N['Material Output'].inputs['Surface'])
    return mat


def lamp_glass_mat(name, hot=(1.0, 0.68, 0.30), edge=(1.0, 0.38, 0.10), gain=0.15):
    """Lantern panes: dark glass when unlit; lit (strength of node 'Emission', keyed 0 -> 9 by
    film.lamp) they glow amber, hottest at mantle height in the middle of each pane.  gain scales
    the keyed strength so 9 lands at ~1.35 in the hot core (amber, not clipped white)."""
    mat = bpy.data.materials.new(name)
    nt, N, L = _nodes(mat)
    for n in list(N):
        if n.type == 'BSDF_PRINCIPLED':
            N.remove(n)
    tc = N.new('ShaderNodeTexCoord')
    sep = N.new('ShaderNodeSeparateXYZ')
    L.new(tc.outputs['Object'], sep.inputs[0])
    rr = _math(N, L, 'SQRT', _math(N, L, 'ADD', _math(N, L, 'MULTIPLY', sep.outputs['X'], sep.outputs['X']),
                                   _math(N, L, 'MULTIPLY', sep.outputs['Y'], sep.outputs['Y'])))
    rad = _remap(N, L, rr, 0.147, 0.17, 1.0, 0.45)
    ver = _remap(N, L, _math(N, L, 'ABSOLUTE', sep.outputs['Z']), 0.03, 0.21, 1.0, 0.35)
    k = _math(N, L, 'MULTIPLY', rad, ver)
    ramp = N.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.15
    ramp.color_ramp.elements[0].color = (*edge, 1)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (*hot, 1)
    L.new(k, ramp.inputs['Fac'])
    ec = _mul(N, L, ramp.outputs['Color'], _math(N, L, 'MULTIPLY', k, gain))
    e = N.new('ShaderNodeEmission')
    e.name = 'Emission'
    L.new(ec, e.inputs['Color'])
    e.inputs['Strength'].default_value = 0.0
    # unlit: smoky dark glass with a sharp reflection
    df = N.new('ShaderNodeBsdfDiffuse')
    df.inputs['Color'].default_value = (0.03, 0.028, 0.025, 1)
    gl = N.new('ShaderNodeBsdfGlossy')
    gl.inputs['Roughness'].default_value = 0.06
    fr = N.new('ShaderNodeFresnel')
    fr.inputs['IOR'].default_value = 1.5
    mx = N.new('ShaderNodeMixShader')
    L.new(fr.outputs[0], mx.inputs[0])
    L.new(df.outputs[0], mx.inputs[1])
    L.new(gl.outputs[0], mx.inputs[2])
    ad = N.new('ShaderNodeAddShader')
    L.new(mx.outputs[0], ad.inputs[0])
    L.new(e.outputs[0], ad.inputs[1])
    L.new(ad.outputs[0], N['Material Output'].inputs['Surface'])
    return mat


def dial_mat(name):
    """Cream clock dial that can glow from behind (animate node 'glow')."""
    mat = bpy.data.materials.new(name)
    nt, N, L = _nodes(mat)
    b = N['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.82, 0.76, 0.60, 1)
    b.inputs['Roughness'].default_value = 0.5
    b.inputs['Emission Color'].default_value = (1.0, 0.86, 0.62, 1)
    v = N.new('ShaderNodeValue')
    v.name = 'glow'
    v.outputs[0].default_value = 0.0
    L.new(v.outputs[0], b.inputs['Emission Strength'])
    return mat


def emission_mat(name, color, strength):
    mat = bpy.data.materials.new(name)
    nt, N, L = _nodes(mat)
    for n in list(N):
        if n.type == 'BSDF_PRINCIPLED':
            N.remove(n)
    e = N.new('ShaderNodeEmission')
    e.inputs['Color'].default_value = (*color, 1)
    e.inputs['Strength'].default_value = strength
    L.new(e.outputs[0], N['Material Output'].inputs['Surface'])
    return mat


def stripe_mat(name, c1, c2, scale=8.0):
    mat = bpy.data.materials.new(name)
    nt, N, L = _nodes(mat)
    b = N['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.85
    b.inputs['Sheen Weight'].default_value = 0.4
    tc = N.new('ShaderNodeTexCoord')
    w = N.new('ShaderNodeTexWave')
    w.bands_direction = 'X'
    w.inputs['Scale'].default_value = scale
    w.wave_profile = 'SAW'
    L.new(tc.outputs['Object'], w.inputs['Vector'])
    g = N.new('ShaderNodeMath')
    g.operation = 'GREATER_THAN'
    g.inputs[1].default_value = 0.5
    L.new(w.outputs['Fac'], g.inputs[0])
    c = mix_rgb(N, L, g.outputs[0], c1, c2)
    L.new(c.outputs[2], b.inputs['Base Color'])
    return mat


# ------------------------------------------------------------------ builders
def text_obj(coll, text, loc, size, mat, rot=(math.radians(90), 0, 0), font_path=None, extrude=0.01):
    cu = bpy.data.curves.new('txt', 'FONT')
    cu.body = text
    cu.size = size
    cu.align_x = 'CENTER'
    cu.align_y = 'CENTER'
    cu.extrude = extrude
    if font_path:
        cu.font = bpy.data.fonts.load(font_path)
    ob = bpy.data.objects.new('txt_' + text[:8], cu)
    coll.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = rot
    ob.data.materials.append(mat)
    return ob


def window(coll, x, z, w, h, M, glass, frame_y=FACADE_Y, muntins=True, sill=True):
    """Window on the facade plane (facing -Y)."""
    y = frame_y
    fw = 0.07
    box(coll, 'win_glass', (w, 0.02, h), (x, y + 0.03, z), glass)
    for (sx, sz, px, pz) in ((w + 2 * fw, fw, x, z + h / 2 + fw / 2), (w + 2 * fw, fw, x, z - h / 2 - fw / 2),
                             (fw, h, x - w / 2 - fw / 2, z), (fw, h, x + w / 2 + fw / 2, z)):
        box(coll, 'win_frame', (sx, 0.10, sz), (px, y - 0.02, pz), M['frame'])
    if muntins:
        box(coll, 'win_mun', (0.035, 0.05, h), (x, y, z), M['frame'])
        box(coll, 'win_mun', (w, 0.05, 0.035), (x, y, z + h * 0.1), M['frame'])
    if sill:
        box(coll, 'win_sill', (w + 0.25, 0.20, 0.06), (x, y - 0.08, z - h / 2 - 0.10), M['stone'], bevel=0.01)


def bakery_facade(coll, M, x0, x1, h):
    SZ = SIDEWALK_Z
    d0, d1, dtop = -1.36, -0.44, SZ + 2.0
    w0, w1, wbot, wtop = -0.17, 2.37, SZ + 0.55, SZ + 2.27
    T = 0.3
    yc = FACADE_Y + T / 2
    def slab(xa, xb, za, zb):
        box(coll, 'bldg', (xb - xa, T, zb - za), ((xa + xb) / 2, yc, (za + zb) / 2), M['brick'])
    slab(x0, d0, 0, h)
    slab(d0, d1, dtop, h)
    slab(d1, w0, 0, h)
    slab(w0, w1, wtop, h)
    slab(w0, w1, 0, wbot)
    slab(w1, x1, 0, h)
    # upper floors / back of the building
    box(coll, 'bldg', (x1 - x0, 2.7 - T, h - (SZ + 2.9)), ((x0 + x1) / 2, FACADE_Y + T + (2.7 - T) / 2, (SZ + 2.9 + h) / 2), M['brick'])
    # shop interior room
    ix0, ix1 = -1.5, 2.5
    yb = FACADE_Y + 2.4
    warm = plaster_mat('bakery_wall', (0.75, 0.55, 0.32), stain=0.2)
    box(coll, 'in_back', (ix1 - ix0, 0.1, 2.9), ((ix0 + ix1) / 2, yb, SZ + 1.45), warm)
    box(coll, 'in_floor', (ix1 - ix0, yb - FACADE_Y, 0.05), ((ix0 + ix1) / 2, (FACADE_Y + yb) / 2, SZ - 0.02), M['wood'])
    box(coll, 'in_ceil', (ix1 - ix0, yb - FACADE_Y, 0.08), ((ix0 + ix1) / 2, (FACADE_Y + yb) / 2, SZ + 2.9), warm)
    box(coll, 'in_side', (0.1, yb - FACADE_Y, 2.9), (ix0, (FACADE_Y + yb) / 2, SZ + 1.45), warm)
    box(coll, 'in_side', (0.1, yb - FACADE_Y, 2.9), (ix1, (FACADE_Y + yb) / 2, SZ + 1.45), warm)
    # counter
    box(coll, 'counter', (2.2, 0.6, 0.95), (1.0, FACADE_Y + 1.6, SZ + 0.475), M['wood'], bevel=0.01)
    # ceiling lamp glow
    lamp_m = emission_mat('in_lamp', (1.0, 0.75, 0.45), 6.0)
    cyl(coll, 'in_lamp', 0.12, 0.06, (0.6, FACADE_Y + 1.1, SZ + 2.7), lamp_m)


def build_set(font_path='/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf', bakery_name='BRANDT & SON  ·  BAKERS'):
    coll = bpy.data.collections.new('SET')
    bpy.context.scene.collection.children.link(coll)
    M = {}
    M['cobble'] = cobble_mat('cobble')
    M['slab'] = slab_mat('slab')
    M['brick'] = brick_mat('brick')
    M['brick2'] = brick_mat('brick2', base=(0.28, 0.13, 0.09))
    M['plaster_y'] = plaster_mat('plaster_y', (0.62, 0.48, 0.28))
    M['plaster_b'] = plaster_mat('plaster_b', (0.30, 0.40, 0.42))
    M['plaster_r'] = plaster_mat('plaster_r', (0.55, 0.30, 0.22))
    M['plaster_w'] = plaster_mat('plaster_w', (0.60, 0.57, 0.50))
    M['stone'] = plaster_mat('stone', (0.42, 0.40, 0.36), stain=0.4)
    M['frame'] = blib.principled('frame', (0.75, 0.72, 0.65), rough=0.6)
    M['frame_g'] = blib.principled('frame_g', (0.08, 0.20, 0.14), rough=0.5)
    M['wood'] = wood_mat('wood')
    M['wood_door'] = plaster_mat('wood_door', (0.07, 0.17, 0.11), stain=0.25)
    M['wood_door'].node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.45
    M['iron'] = blib.principled('iron', (0.025, 0.025, 0.028), rough=0.45, metallic=0.8)
    M['brass'] = blib.principled('brass', (0.55, 0.38, 0.14), rough=0.3, metallic=1.0)
    M['roof'] = plaster_mat('roof', (0.18, 0.12, 0.10), stain=0.5)
    M['glass_dark'] = glass_mat('glass_dark')
    M['glass_warm'] = glass_mat('glass_warm', interior=(1.0, 0.62, 0.30), strength=0.6, tint=(0.25, 0.15, 0.08))
    M['bakery_glass'] = glass_mat('bakery_glass', interior=(1.0, 0.65, 0.32), strength=0.0, tint=(0.02, 0.02, 0.02))
    M['bakery_inside'] = emission_mat('bakery_inside', (1.0, 0.62, 0.32), 1.2)
    M['awning'] = stripe_mat('awning', (0.45, 0.06, 0.06), (0.75, 0.68, 0.55), scale=6)
    M['sign'] = blib.principled('sign', (0.08, 0.16, 0.12), rough=0.5)
    M['gold'] = blib.principled('gold', (0.8, 0.55, 0.18), rough=0.35, metallic=1.0)
    M['bread'] = blib.principled('bread', (0.55, 0.28, 0.08), rough=0.55, coat=0.2)
    M['lampglass'] = lamp_glass_mat('lampglass')
    M['door_glass'] = pane_mat('door_glass')
    M['clockface'] = blib.principled('clockface', (0.85, 0.82, 0.72), rough=0.5)

    # ground
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    g = _obj_from_ops(coll)
    g.name = 'street'
    g.data.transform(Matrix.Diagonal((40, 40, 1, 1)))
    blib.assign(g, M['cobble'])
    # sidewalk (in front of the shop row) + curb
    box(coll, 'sidewalk', (24, 1.45, SIDEWALK_Z), (0, FACADE_Y - 0.72, SIDEWALK_Z / 2), M['slab'])
    box(coll, 'curb', (24, 0.18, SIDEWALK_Z + 0.02), (0, FACADE_Y - 1.45, SIDEWALK_Z / 2), M['stone'], bevel=0.02)
    # far sidewalk for reverse shots
    box(coll, 'sidewalk2', (24, 1.4, SIDEWALK_Z), (0, -12.3, SIDEWALK_Z / 2), M['slab'])

    # ---------------- shop row (facing -Y) ----------------
    shops = [
        # x0, x1, height, wall material, trim
        (-8.5, -4.2, 7.6, 'plaster_b'),
        (-4.2, 4.1, 6.9, 'brick'),       # bakery building (brick pier right of the window)
        (4.1, 7.2, 7.2, 'plaster_y'),
        (7.2, 11.0, 8.2, 'brick2'),
    ]
    for (x0, x1, h, wm) in shops:
        w = x1 - x0
        if wm == 'brick':
            bakery_facade(coll, M, x0, x1, h)
        else:
            box(coll, 'bldg', (w, 3.0, h), ((x0 + x1) / 2, FACADE_Y + 1.5, h / 2), M[wm])
        # cornice + roof
        box(coll, 'cornice', (w + 0.1, 0.35, 0.25), ((x0 + x1) / 2, FACADE_Y - 0.1, h - 0.1), M['stone'], bevel=0.03)
        bpy.ops.mesh.primitive_cube_add(size=1, location=((x0 + x1) / 2, FACADE_Y + 1.5, h + 0.6))
        r = _obj_from_ops(coll)
        r.name = 'roof'
        me = r.data
        for v in me.vertices:
            if v.co.z > 0:
                v.co.y = 0.05
                v.co.x *= 0.98
        me.transform(Matrix.Diagonal((w + 0.05, 3.4, 1.2, 1)))
        blib.assign(r, M['roof'])
        # string course between floors
        box(coll, 'course', (w, 0.12, 0.10), ((x0 + x1) / 2, FACADE_Y - 0.04, 3.3), M['stone'])
        # upper windows
        nwin = max(2, int(w / 1.6))
        for i in range(nwin):
            x = x0 + (i + 0.5) * w / nwin
            for z in (4.6, 6.6):
                if z + 1.0 > h - 0.4:
                    continue
                lit = (i + int(z)) % 3 == 0
                window(coll, x, z, 0.85, 1.25, M, M['glass_warm'] if lit else M['glass_dark'])
    # bakery storefront (on the brick building)
    box(coll, 'shopfront_base', (2.6, 0.16, 0.55), (1.1, FACADE_Y - 0.05, SIDEWALK_Z + 0.27), M['frame_g'], bevel=0.01)
    for px in (-0.12, 1.1, 2.32):
        box(coll, 'shop_post', (0.10, 0.14, 1.75), (px, FACADE_Y - 0.03, SIDEWALK_Z + 1.37), M['frame_g'])
    box(coll, 'shop_lintel', (2.6, 0.16, 0.14), (1.1, FACADE_Y - 0.04, SIDEWALK_Z + 2.2), M['frame_g'])
    # interior glow + shelves with bread
    for sz in (0.75, 1.25):
        box(coll, 'shelf', (2.2, 0.35, 0.04), (1.1, FACADE_Y + 0.55, SIDEWALK_Z + sz), M['wood'])
        for i in range(7):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(0.2 + i * 0.3, FACADE_Y + 0.53, SIDEWALK_Z + sz + 0.07))
            lo = _obj_from_ops(coll)
            lo.scale = (1.2, 0.7, 0.6) if i % 2 else (0.8, 0.8, 0.65)
            bpy.ops.object.shade_smooth()
            blib.assign(lo, M['bread'])
    pl = bpy.data.lights.new('bakery_light', 'AREA')
    pl.energy = 220
    pl.size = 2.0
    pl.color = (1.0, 0.7, 0.42)
    plo = bpy.data.objects.new('bakery_light', pl)
    coll.objects.link(plo)
    plo.location = (0.6, FACADE_Y + 1.2, SIDEWALK_Z + 2.6)
    plo.rotation_euler = (0, 0, 0)  # shines down into the shop
    # door (hinged on its left edge)
    dx, dw, dh = -0.9, 0.92, 2.0
    for (sx, sz, px, pz) in ((dw + 0.24, 0.12, dx, SIDEWALK_Z + dh + 0.06), (0.12, dh, dx - dw / 2 - 0.06, SIDEWALK_Z + dh / 2),
                             (0.12, dh, dx + dw / 2 + 0.06, SIDEWALK_Z + dh / 2)):
        box(coll, 'door_frame', (sx, 0.14, sz), (px, FACADE_Y - 0.03, pz), M['frame_g'])
    hinge = bpy.data.objects.new('door_hinge', None)
    coll.objects.link(hinge)
    hinge.location = (dx - dw / 2, FACADE_Y + 0.02, SIDEWALK_Z)
    # stiles and rails around a real glass pane (the shop shows through it)
    gw, gh, gz = dw * 0.6, 0.7, dh * 0.68
    gx0, gx1, gz0, gz1 = (dw - gw) / 2, (dw + gw) / 2, gz - gh / 2, gz + gh / 2
    for (xa, xb, za, zb) in ((0, gx0, 0, dh), (gx1, dw, 0, dh), (gx0, gx1, 0, gz0), (gx0, gx1, gz1, dh)):
        door = box(coll, 'door', (xb - xa, 0.05, zb - za), ((xa + xb) / 2, 0, (za + zb) / 2), M['wood_door'], bevel=0.01)
        door.parent = hinge
    dwin = box(coll, 'door_window', (gw, 0.012, gh), (dw / 2, 0, gz), M['door_glass'])
    dwin.visible_shadow = False     # clear glass: light passes, no shader work on shadow rays
    dwin.parent = hinge
    bw = 0.025
    for sy in (-1, 1):
        for (sx, sz, px, pz) in ((gw + 2 * bw, bw, dw / 2, gz1), (gw + 2 * bw, bw, dw / 2, gz0), (bw, gh, gx0, gz), (bw, gh, gx1, gz)):
            bead = box(coll, 'door_bead', (sx, 0.014, sz), (px, sy * 0.028, pz), M['wood_door'])
            bead.parent = hinge
    # gold-leaf name on the glass
    M['gold_leaf'] = blib.principled('gold_leaf', (0.85, 0.58, 0.20), rough=0.3, metallic=0.45)
    gl_txt = text_obj(coll, 'BRANDT & SON', (dw / 2, -0.008, gz1 - 0.085), 0.045, M['gold_leaf'], font_path=font_path, extrude=0.0004)
    gl_txt.parent = hinge
    for (pz, ph) in ((dh * 0.25, dh * 0.32),):
        pnl = box(coll, 'door_panel', (dw * 0.62, 0.03, ph), (dw / 2, -0.03, pz), M['wood_door'], bevel=0.01)
        pnl.parent = hinge
    knob = cyl(coll, 'knob', 0.03, 0.06, (dw - 0.1, -0.05, dh * 0.47), M['brass'], rot=(math.radians(90), 0, 0))
    knob.parent = hinge
    # bell above the door (inside the frame)
    bpy.ops.mesh.primitive_cone_add(radius1=0.06, radius2=0.02, depth=0.08, location=(dx + 0.25, FACADE_Y + 0.05, SIDEWALK_Z + dh - 0.06))
    bell = _obj_from_ops(coll)
    bell.name = 'door_bell'
    blib.assign(bell, M['brass'])
    # awning over the window
    bpy.ops.mesh.primitive_plane_add(size=1, location=(1.1, FACADE_Y - 0.55, SIDEWALK_Z + 2.55))
    aw = _obj_from_ops(coll)
    aw.name = 'awning'
    aw.data.transform(Matrix.Diagonal((2.8, 1.1, 1, 1)))
    aw.rotation_euler = (math.radians(-28), 0, 0)
    blib.assign(aw, M['awning'])
    sol = aw.modifiers.new('sol', 'SOLIDIFY')
    sol.thickness = 0.02
    # scalloped valance
    for i in range(14):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.02, vertices=16,
                                            location=(1.1 - 1.3 + i * 0.2, FACADE_Y - 1.03, SIDEWALK_Z + 2.24),
                                            rotation=(math.radians(90), 0, 0))
        sc_ = _obj_from_ops(coll)
        blib.assign(sc_, M['awning'])
    # sign
    box(coll, 'signboard', (2.7, 0.08, 0.5), (1.1, FACADE_Y - 0.06, SIDEWALK_Z + 3.0), M['sign'], bevel=0.02)
    text_obj(coll, bakery_name, (1.1, FACADE_Y - 0.11, SIDEWALK_Z + 3.0), 0.17, M['gold'], font_path=font_path)
    # window card
    mcard = blib.principled('card', (0.85, 0.82, 0.72), rough=0.8)
    box(coll, 'card', (0.36, 0.01, 0.22), (0.55, FACADE_Y - 0.02, SIDEWALK_Z + 0.82), mcard)
    mink = blib.principled('ink', (0.05, 0.04, 0.04), rough=0.6)
    text_obj(coll, 'KINDLY PAY', (0.55, FACADE_Y - 0.03, SIDEWALK_Z + 0.86), 0.045, mink,
             font_path='/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf', extrude=0.0005)
    text_obj(coll, 'BEFORE EATING', (0.55, FACADE_Y - 0.03, SIDEWALK_Z + 0.79), 0.045, mink,
             font_path='/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf', extrude=0.0005)
    # bakery-side ground floor windows on other shops
    window(coll, -6.0, SIDEWALK_Z + 1.4, 1.2, 1.5, M, M['glass_dark'])
    box(coll, 'door2', (0.95, 0.06, 2.1), (-6.9, FACADE_Y - 0.01, SIDEWALK_Z + 1.05), M['wood_door'])
    window(coll, 5.6, SIDEWALK_Z + 1.4, 1.6, 1.5, M, M['glass_warm'])
    window(coll, 9.0, SIDEWALK_Z + 1.4, 1.6, 1.5, M, M['glass_dark'])
    # drainpipe
    cyl(coll, 'pipe', 0.045, 7.0, (4.1, FACADE_Y - 0.08, 3.5), M['iron'], verts=12)

    # ---------------- lamppost (crook arm, hanging lantern) ----------------
    lx, ly = LAMP_XY
    lamp = bpy.data.objects.new('lamppost', None)
    coll.objects.link(lamp)
    lamp.location = (lx, ly, SIDEWALK_Z)
    cyl(coll, 'lp_base', 0.17, 0.32, (lx, ly, SIDEWALK_Z + 0.16), M['iron'], verts=8, smooth=False)
    cyl(coll, 'lp_base2', 0.12, 0.34, (lx, ly, SIDEWALK_Z + 0.48), M['iron'], verts=16)
    cyl(coll, 'lp_pole', 0.052, 3.1, (lx, ly, SIDEWALK_Z + 2.15), M['iron'], verts=16)
    for zz in (0.85, 1.9, 3.55):
        cyl(coll, 'lp_ring', 0.075, 0.05, (lx, ly, SIDEWALK_Z + zz), M['iron'], verts=16)
    cyl(coll, 'lp_finial', 0.035, 0.18, (lx, ly, SIDEWALK_Z + 3.78), M['iron'], verts=12)
    # crook arm: rises, curls over and down toward the street
    adir = Vector((0.45, -0.89, 0)).normalized()
    pts = []
    for a in np.linspace(0, np.pi * 1.25, 22):
        r = 0.32
        d = r - r * math.cos(a)
        h = r * math.sin(a)
        p = Vector((lx, ly, SIDEWALK_Z + 3.45)) + adir * d + Vector((0, 0, h))
        pts.append(p)
    from character import loft as _loft, ellipse as _ell
    Va, Fa, _ = _loft([tuple(p) for p in pts], [_ell(10, 0.024, 0.024) for _ in pts], up_hint=(0, 0, 1))
    arm_ob = blib.make_mesh('lp_arm', Va, Fa, coll=coll)
    blib.assign(arm_ob, M['iron'])
    # little scroll under the arm
    sc_pts = []
    for a in np.linspace(0, np.pi * 2.2, 26):
        r = 0.10 * (1 - a / (np.pi * 2.6))
        sc_pts.append(tuple(Vector((lx, ly, SIDEWALK_Z + 3.25)) + adir * (0.10 + r * math.sin(a)) + Vector((0, 0, r * math.cos(a)))))
    Vs, Fs, _ = _loft(sc_pts, [_ell(8, 0.012, 0.012) for _ in sc_pts], up_hint=(0, 0, 1))
    blib.assign(blib.make_mesh('lp_scroll', Vs, Fs, coll=coll), M['iron'])
    tip = pts[-1]
    lpos = tip + Vector((0, 0, -0.42))
    cyl(coll, 'lp_hanger', 0.012, 0.14, tuple(tip + Vector((0, 0, -0.07))), M['iron'], verts=8)
    lz = lpos.z
    # the light sits inside the glass: panes, base plate and bars must not shadow it
    # (only the smoke cap above does, so the glow falls down and out, not up the facade)
    cage = cyl(coll, 'lp_cage', 0.17, 0.42, (lpos.x, lpos.y, lz), M['lampglass'], verts=6, smooth=False)
    cage.visible_shadow = False
    bpy.ops.mesh.primitive_cone_add(radius1=0.26, radius2=0.03, depth=0.24, vertices=6, location=(lpos.x, lpos.y, lz + 0.32))
    blib.assign(_obj_from_ops(coll), M['iron'])
    cyl(coll, 'lp_bottom', 0.13, 0.06, (lpos.x, lpos.y, lz - 0.24), M['iron'], verts=6, smooth=False).visible_shadow = False
    for k in range(6):
        a = k * math.pi / 3 + math.pi / 6
        cyl(coll, 'lp_bar', 0.011, 0.44, (lpos.x + 0.165 * math.cos(a), lpos.y + 0.165 * math.sin(a), lz), M['iron'], verts=6).visible_shadow = False
    ll = bpy.data.lights.new('lamp_light', 'POINT')
    ll.energy = 0.0             # keyed by film.lamp (0 -> 60 W)
    ll.exposure = LAMP_EXPOSURE  # x2^exposure on top of the keyed watts
    ll.color = (1.0, 0.64, 0.34)
    ll.shadow_soft_size = 0.15
    llo = bpy.data.objects.new('lamp_light', ll)
    coll.objects.link(llo)
    llo.location = (lpos.x, lpos.y, lz - 0.02)


    # ---------------- clock tower (town hall behind the bakery roofline) ----------------
    tx, ty, tz = TOWER
    TW = 4.6
    box(coll, 'tower', (TW, TW, tz + 3.5), (tx, ty, (tz + 3.5) / 2), M['stone'])
    box(coll, 'tower_cornice', (TW + 0.35, TW + 0.35, 0.35), (tx, ty, tz + 1.9), M['stone'], bevel=0.03)
    box(coll, 'tower_belfry', (TW * 0.82, TW * 0.82, 2.4), (tx, ty, tz + 3.2), M['stone'])
    bpy.ops.mesh.primitive_cone_add(radius1=TW * 0.74, radius2=0.05, depth=3.6, vertices=4, location=(tx, ty, tz + 6.2), rotation=(0, 0, math.radians(45)))
    rf = _obj_from_ops(coll)
    blib.assign(rf, M['roof'])
    DR = DIAL_R
    fy = ty - TW / 2
    M['dial'] = dial_mat('dial')
    cyl(coll, 'clockface', DR, 0.06, (tx, fy - 0.04, tz), M['dial'], verts=64, rot=(math.radians(90), 0, 0))
    cyl(coll, 'clockrim', DR + 0.09, 0.05, (tx, fy - 0.02, tz), M['gold'], verts=64, rot=(math.radians(90), 0, 0))
    numerals = ['XII', 'I', 'II', 'III', 'IIII', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI']
    for i, nm in enumerate(numerals):
        a = i * math.pi / 6
        r = DR * 0.80
        t_ = text_obj(coll, nm, (tx + r * math.sin(a), fy - 0.08, tz + r * math.cos(a)), 0.20, M['iron'],
                      rot=(math.radians(90), 0, -a * 0), font_path=font_path, extrude=0.004)
        t_.rotation_euler = (math.radians(90), -a, 0)
    piv = Vector((tx, fy - 0.10, tz))
    hands = {}
    for nm, (w_, l_) in (('hour', (0.07, DR * 0.55)), ('minute', (0.045, DR * 0.82))):
        e = bpy.data.objects.new('clock_' + nm, None)
        coll.objects.link(e)
        e.location = piv + Vector((0, -0.01 if nm == 'minute' else 0, 0))
        hnd = box(coll, 'hand_' + nm, (w_, 0.015, l_), (0, 0, l_ / 2 - 0.08), M['iron'])
        hnd.parent = e
        hands[nm] = e
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.06, location=tuple(piv + Vector((0, -0.03, 0))))
    blib.assign(_obj_from_ops(coll), M['gold'])
    tower_info = dict(center=Vector((tx, fy, tz)), radius=DR, hands=hands)

    # ---------------- side + far buildings ----------------
    for sx in (-1, 1):
        box(coll, 'side_bldg', (3.0, 22.0, 10.0), (sx * 11.5, -3.0, 5.0), M['plaster_r' if sx < 0 else 'plaster_w'])
    far = [(-9, -3, 8.0, 'plaster_w'), (-3, 3, 9.0, 'brick2'), (3, 9, 8.5, 'plaster_b')]
    for (x0, x1, h, wm) in far:
        box(coll, 'far_bldg', (x1 - x0, 3.0, h), ((x0 + x1) / 2, -14.5, h / 2), M[wm])
        for i in range(3):
            x = x0 + (i + 0.5) * (x1 - x0) / 3
            for z in (1.6, 4.6, 6.6):
                box(coll, 'far_win', (0.9, 0.05, 1.2), (x, -13.0, z), M['glass_warm'] if (i + int(z)) % 2 else M['glass_dark'])
    # far tower silhouette for depth
    box(coll, 'church', (3, 3, 18), (-7, 22, 9), M['stone'])
    for o in coll.objects:
        if o.name.startswith(('far_', 'side_bldg')):
            o.visible_shadow = False

    # ---------------- props ----------------
    # bench (left of the bakery door)
    bx, by = BENCH_XY
    sz = SIDEWALK_Z
    box(coll, 'bench_seat', (1.5, 0.42, 0.05), (bx, by, sz + 0.45), M['wood'], bevel=0.01)
    box(coll, 'bench_back', (1.5, 0.05, 0.38), (bx, by + 0.22, sz + 0.75), M['wood'], bevel=0.01)
    for px in (bx - 0.65, bx + 0.65):
        box(coll, 'bench_leg', (0.05, 0.42, 0.45), (px, by, sz + 0.22), M['iron'])
    # crates by the bakery wall (left of the sitting spot)
    box(coll, 'crate', (0.5, 0.4, 0.4), (3.85, FACADE_Y - 0.28, SIDEWALK_Z + 0.2), M['wood'], bevel=0.01, rot=(0, 0, 0.1))
    box(coll, 'crate2', (0.45, 0.4, 0.35), (3.9, FACADE_Y - 0.28, SIDEWALK_Z + 0.58), M['wood'], bevel=0.01, rot=(0, 0, -0.15))
    # potted plant by the door
    cyl(coll, 'pot', 0.18, 0.35, (-2.25, FACADE_Y - 0.3, SIDEWALK_Z + 0.175), M['plaster_r'], verts=16)
    bpy.ops.mesh.primitive_ico_sphere_add(radius=0.3, subdivisions=2, location=(-2.25, FACADE_Y - 0.3, SIDEWALK_Z + 0.55))
    bush = _obj_from_ops(coll)
    blib.assign(bush, blib.principled('leaf', (0.08, 0.14, 0.05), rough=0.8))
    return dict(coll=coll, M=M, door_hinge=hinge, lamp_light=llo, lamp_mat=M['lampglass'], bakery_light=plo,
                bakery_glass=M['bakery_glass'], bell=bell, tower=tower_info, dial_mat=M['dial'])


def setup_world(time='afternoon'):
    """Overcast pewter sky with a warm glow low behind the tower (+Y)."""
    sc = bpy.context.scene
    w = bpy.data.worlds.new('sky')
    sc.world = w
    w.use_nodes = True
    N = w.node_tree.nodes
    L = w.node_tree.links
    bg = N['Background']
    tc = N.new('ShaderNodeTexCoord')
    sep = N.new('ShaderNodeSeparateXYZ')
    L.new(tc.outputs['Generated'], sep.inputs[0])
    ramp = N.new('ShaderNodeValToRGB')
    cr = ramp.color_ramp
    cr.elements[0].position = 0.0
    cr.elements[0].color = (0.62, 0.55, 0.47, 1)
    cr.elements[1].position = 0.45
    cr.elements[1].color = (0.20, 0.23, 0.28, 1)
    e = cr.elements.new(0.12)
    e.color = (0.42, 0.42, 0.44, 1)
    L.new(sep.outputs['Z'], ramp.inputs[0])
    # warm glow toward the low sun behind the tower
    dot = N.new('ShaderNodeVectorMath')
    dot.operation = 'DOT_PRODUCT'
    dot.inputs[1].default_value = (0.0, 0.97, 0.18)
    L.new(tc.outputs['Generated'], dot.inputs[0])
    pw = N.new('ShaderNodeMath')
    pw.operation = 'POWER'
    pw.inputs[1].default_value = 6.0
    mx = N.new('ShaderNodeMath')
    mx.operation = 'MAXIMUM'
    mx.inputs[1].default_value = 0.0
    L.new(dot.outputs['Value'], mx.inputs[0])
    L.new(mx.outputs[0], pw.inputs[0])
    glow = N.new('ShaderNodeMix')
    glow.data_type = 'RGBA'
    glow.blend_type = 'ADD'
    L.new(pw.outputs[0], glow.inputs['Factor'])
    L.new(ramp.outputs[0], glow.inputs[6])
    glow.inputs[7].default_value = (1.0, 0.62, 0.30, 1)
    L.new(glow.outputs[2], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = 0.55
    bpy.ops.object.light_add(type='SUN')
    sun = bpy.context.object
    for c in sun.users_collection:
        c.objects.unlink(sun)
    sc.collection.objects.link(sun)
    sun.name = 'sun'
    sun.data.energy = 1.6
    sun.data.color = (1.0, 0.70, 0.42)
    sun.data.angle = math.radians(4)
    elev = 9.0
    d = Vector((0.18, -math.cos(math.radians(elev)), -math.sin(math.radians(elev)))).normalized()
    sun.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return dict(world=w, bg=bg, sun=sun, ramp=ramp, glow=glow)
