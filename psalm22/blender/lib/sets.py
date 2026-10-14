"""Interior / built sets for Psalm 22 (Blender 4.5, EEVEE Next).

Every set builder has the signature   set_fn(ctx, loc=(0,0,0), rot_z=0, ...)  and returns a `SetInfo`:

    info.root       Empty that parents the whole set (move/rotate it to re-place the set)
    info.coll       Collection holding every object of the set
    info.anchors    {name: Vector}  WORLD-space positions (floor-level unless stated)
    info.facing     {name: yaw_deg} WORLD yaw for characters/animals at an anchor (0 = facing +Y)
    info.cameras    {name: {"loc": Vector, "target": Vector, "lens": float}}  WORLD-space suggestions
    info.lights     {name: light object}
    info.objects    {name: object}
    info.camera(name, **camera_kwargs) -> creates + activates a core.camera at a suggestion

Local axes of every set: floor at z=0, the "audience" looks from -Y towards +Y (the main camera
suggestion), X to the right. `loc`/`rot_z` (degrees) place the set in the world.

Public builders: stable_cave, garden_tomb, holy_of_holies, courtyard_assembly, table_interior,
camp_night. Reusable props: oil_lamp, lamp_field, night_world, dust, straw_scatter, flicker_light.
"""
import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix, Euler, noise
from . import core as C

TAU = math.tau


# ============================================================================================
# Result object + builder
# ============================================================================================
class SetInfo:
    def __init__(self, name, root, coll, matrix):
        self.name = name
        self.root = root
        self.coll = coll
        self.matrix = matrix
        self.anchors = {}
        self.facing = {}
        self.cameras = {}
        self.lights = {}
        self.objects = {}
        self.materials = {}
        self.extra = {}

    def __getitem__(self, k):
        return self.anchors[k]

    def __repr__(self):
        return "<SetInfo %s anchors=%s cameras=%s>" % (self.name, sorted(self.anchors), sorted(self.cameras))

    def camera(self, name="wide", fstop=None, focus=None, **kw):
        """Create + activate a core.camera from a suggestion. Extra kwargs go to core.camera."""
        s = self.cameras[name]
        kw.setdefault("lens", s["lens"])
        return C.camera(loc=tuple(s["loc"]), target=tuple(s["target"]), fstop=fstop, focus=focus, **kw)

    def to_world(self, p):
        return self.matrix @ Vector(p)


class _B:
    """Set builder: creates objects in local set coordinates, parented to the root empty."""

    def __init__(self, name, loc, rot_z, coll=None, seed=0):
        parent = coll if isinstance(coll, bpy.types.Collection) else None
        self.coll = C.collection(name, parent)
        self.root = bpy.data.objects.new(name, None)
        self.root.empty_display_size = 0.5
        self.coll.objects.link(self.root)
        self.loc = Vector(loc)
        self.rot_z = math.radians(rot_z)
        self.M = Matrix.Translation(self.loc) @ Matrix.Rotation(self.rot_z, 4, "Z")
        self.info = SetInfo(name, self.root, self.coll, self.M)
        self.rnd = random.Random(seed)
        self.name = name

    def add(self, o, key=None, parent=None):
        if self.coll not in o.users_collection:
            for c in list(o.users_collection):
                c.objects.unlink(o)
            self.coll.objects.link(o)
        if o.parent is None and o is not self.root:
            o.parent = parent or self.root
        if key:
            self.info.objects[key] = o
        return o

    def w(self, p):
        return self.M @ Vector(p)

    def anchor(self, key, p, yaw=None):
        self.info.anchors[key] = self.w(p)
        if yaw is not None:
            self.info.facing[key] = (yaw + math.degrees(self.rot_z)) % 360.0

    def cam(self, key, loc, target, lens=35):
        self.info.cameras[key] = {"loc": self.w(loc), "target": self.w(target), "lens": lens}

    def light(self, key, kind, loc, energy, temp=None, color=(1, 1, 1), target=None, size=0.1, **kw):
        o = C.light(kind, loc=loc, energy=energy, color=color, target=target, size=size, temp=temp, name=key, **kw)
        self.add(o)
        self.info.lights[key] = o
        return o

    def finish(self):
        self.root.location = self.loc
        self.root.rotation_euler = (0, 0, self.rot_z)
        bpy.context.view_layer.update()
        return self.info


# ============================================================================================
# Mesh helpers
# ============================================================================================
def _mesh_obj(name, verts, faces, b=None, smooth=True, mat=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    o = bpy.data.objects.new(name, me)
    if b:
        b.add(o)
    else:
        bpy.context.scene.collection.objects.link(o)
    if smooth:
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    if mat:
        me.materials.append(mat)
    return o


def _bm_obj(name, bm, b=None, smooth=True, mat=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    if b:
        b.add(o)
    else:
        bpy.context.scene.collection.objects.link(o)
    if smooth:
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    if mat:
        me.materials.append(mat)
    return o


def _lathe(profile, segs=24, name="lathe", b=None, mat=None, cap_bottom=True, cap_top=False):
    """Revolve [(r, z), ...] around Z. Returns object."""
    verts, faces = [], []
    n = len(profile)
    for i in range(segs):
        a = TAU * i / segs
        ca, sa = math.cos(a), math.sin(a)
        for r, z in profile:
            verts.append((r * ca, r * sa, z))
    for i in range(segs):
        i2 = (i + 1) % segs
        for j in range(n - 1):
            faces.append((i * n + j, i2 * n + j, i2 * n + j + 1, i * n + j + 1))
    if cap_bottom and profile[0][0] > 1e-5:
        c = len(verts)
        verts.append((0, 0, profile[0][1]))
        for i in range(segs):
            faces.append((c, ((i + 1) % segs) * n, i * n))
    if cap_top and profile[-1][0] > 1e-5:
        c = len(verts)
        verts.append((0, 0, profile[-1][1]))
        for i in range(segs):
            faces.append((c, i * n + n - 1, ((i + 1) % segs) * n + n - 1))
    return _mesh_obj(name, verts, faces, b, True, mat)


def _rock_block(name, size, loc, b, mat, rot=(0, 0, 0), noise_amp=0.03, noise_scale=3.0, cuts=6, seed=0.0,
                bevel=0.0):
    """Subdivided box with organic noise displacement (chiselled stone / boulders)."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    if bevel:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=2, affect="EDGES", profile=0.5)
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=cuts, use_grid_fill=True)
    for v in bm.verts:
        p = v.co
        d = noise.noise(p * noise_scale + Vector((seed, seed * 0.7, seed * 1.3)))
        d += 0.5 * noise.noise(p * noise_scale * 2.3 + Vector((seed + 3, 1, 2)))
        n = p.normalized() if p.length > 1e-6 else Vector((0, 0, 1))
        v.co = p + n * d * noise_amp
    o = _bm_obj(name, bm, b, True, mat)
    o.location = loc
    o.rotation_euler = [math.radians(a) for a in rot]
    return o


def _boulder(name, size, loc, b, mat, seed=0.0, rot_z=0.0, rough=0.18, flat=0.35, subdiv=3):
    """Natural rounded rock: displaced ico-sphere scaled to `size` (x, y, z metres), flattened bottom
    (origin at the bottom centre)."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1.0)
    so = Vector((seed * 1.37, seed * 0.71, seed * 2.11))
    for v in bm.verts:
        p = v.co.copy()
        d = rough * C.fbm(p.x * 1.2 + so.x, p.y * 1.2 + p.z * 0.8 + so.y, 4, seed=so.z)
        d += rough * 0.35 * noise.noise(p * 3.5 + so)
        p = p * (1.0 + d)
        p.z = max(p.z, -1.0 + flat)
        v.co = Vector((p.x * size[0] / 2, p.y * size[1] / 2, (p.z + 1.0 - flat) * size[2] / (2.0 - flat)))
    o = _bm_obj(name, bm, b, True, mat)
    o.location = loc
    o.rotation_euler = (0, 0, math.radians(rot_z))
    return o


def _add_straw_layer(m, attr="straw", strength=1.0):
    """Blend a procedural straw-litter fibre layer into a (PBR) floor material, masked by the float
    mesh attribute `attr` (0..1). Modifies `m` in place."""
    nt = m.node_tree
    b, src = _base_color_socket(m)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    fib = None
    for k, ang in enumerate((0.3, 1.4, 2.4, 3.0)):
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Rotation"].default_value = (0, 0, ang)
        mp.inputs["Scale"].default_value = (1, 1, 1)
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        mp2 = nt.nodes.new("ShaderNodeMapping")
        mp2.inputs["Scale"].default_value = (3.0, 55.0, 4.0)
        mp2.inputs["Location"].default_value = (k * 3.1, k * 1.7, 0)
        nt.links.new(mp.outputs[0], mp2.inputs["Vector"])
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 1.0
        nz.inputs["Detail"].default_value = 1.0
        nt.links.new(mp2.outputs[0], nz.inputs["Vector"])
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = 0.56
        mr.inputs["From Max"].default_value = 0.68
        nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
        if fib is None:
            fib = mr.outputs["Result"]
        else:
            mx = nt.nodes.new("ShaderNodeMath")
            mx.operation = "MAXIMUM"
            nt.links.new(fib, mx.inputs[0])
            nt.links.new(mr.outputs["Result"], mx.inputs[1])
            fib = mx.outputs[0]
    at = nt.nodes.new("ShaderNodeAttribute")
    at.attribute_type = "GEOMETRY"
    at.attribute_name = attr
    # coverage = mask, with fibres poking through at lower mask values
    cov = nt.nodes.new("ShaderNodeMath")
    cov.operation = "MULTIPLY_ADD"
    nt.links.new(fib, cov.inputs[0])
    nt.links.new(at.outputs["Fac"], cov.inputs[1])
    nt.links.new(at.outputs["Fac"], cov.inputs[2])
    cl = nt.nodes.new("ShaderNodeMath")
    cl.operation = "MULTIPLY"
    cl.use_clamp = True
    cl.inputs[1].default_value = strength * 0.75
    nt.links.new(cov.outputs[0], cl.inputs[0])
    vn = nt.nodes.new("ShaderNodeTexNoise")
    vn.inputs["Scale"].default_value = 9.0
    nt.links.new(tc.outputs["Object"], vn.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.30, 0.20, 0.09, 1)
    ramp.color_ramp.elements[1].color = (0.70, 0.55, 0.28, 1)
    nt.links.new(vn.outputs["Fac"], ramp.inputs["Fac"])
    dark = nt.nodes.new("ShaderNodeMixRGB")
    dark.blend_type = "MULTIPLY"
    dark.inputs[0].default_value = 1.0
    nt.links.new(ramp.outputs["Color"], dark.inputs[1])
    dark.inputs[2].default_value = (0.4, 0.36, 0.3, 1)
    shade = nt.nodes.new("ShaderNodeMixRGB")
    nt.links.new(fib, shade.inputs[0])
    nt.links.new(dark.outputs[0], shade.inputs[1])
    nt.links.new(ramp.outputs["Color"], shade.inputs[2])
    mix = nt.nodes.new("ShaderNodeMixRGB")
    nt.links.new(cl.outputs[0], mix.inputs[0])
    if src is not None:
        nt.links.new(src, mix.inputs[1])
    nt.links.new(shade.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], b.inputs["Base Color"])
    return m


def _stone_trough(name, size, b, mat, seed=0, wall=0.11, depth=0.3):
    """Rough-hewn stone trough/manger (origin bottom centre): rounded, slightly tapered, chipped."""
    sx, sy, sz = size
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector((sx, sy, sz)), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector((0, 0, sz / 2)), verts=bm.verts)
    topf = [f for f in bm.faces if f.normal.z > 0.9][0]
    bmesh.ops.inset_region(bm, faces=[topf], thickness=wall, depth=0.0)
    bmesh.ops.translate(bm, vec=Vector((0, 0, -depth)), verts=topf.verts)
    bmesh.ops.scale(bm, vec=Vector(((sx - 2 * wall - 0.06) / (sx - 2 * wall), (sy - 2 * wall - 0.08) / (sy - 2 * wall), 1)),
                    verts=topf.verts, space=Matrix.Translation(Vector((0, 0, -(sz - depth)))))
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.05, segments=3, affect="EDGES", profile=0.6)
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=4, use_grid_fill=True)
    so = Vector((seed * 0.37, seed * 0.11, 3.3))
    for v in bm.verts:
        p = v.co.copy()
        t = p.z / sz
        p.x *= 0.93 + 0.07 * t
        p.y *= 0.9 + 0.1 * t
        d = Vector((noise.noise(p * 3 + so), noise.noise(p * 3 + so + Vector((5, 1, 2))),
                    noise.noise(p * 3 + so + Vector((9, 4, 7))))) * 0.03
        d += Vector((noise.noise(p * 11 + so), noise.noise(p * 11 + so + Vector((2, 2, 2))),
                     noise.noise(p * 11 + so + Vector((6, 3, 1))))) * 0.008
        if t > 0.9:     # chipped rim
            d.z -= 0.035 * max(0.0, noise.noise(p * 7 + so + Vector((1, 7, 3))))
        v.co = p + d
    o = _bm_obj(name, bm, b, True, mat)
    return o


def _set_smooth_by_angle(o, angle=40):
    try:
        mod = o.modifiers.new("smooth_by_angle", "NODES")
        mod.node_group = _smooth_by_angle_group()
        mod["Input_1"] = math.radians(angle)
    except Exception:
        pass


_SBA = {}


def _smooth_by_angle_group():
    try:
        if "g" in _SBA and _SBA["g"].name in bpy.data.node_groups:
            return _SBA["g"]
    except ReferenceError:
        pass
    ng = bpy.data.node_groups.new("sets_smooth_by_angle", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    gi = ng.nodes.new("NodeGroupInput")
    go = ng.nodes.new("NodeGroupOutput")
    ss = ng.nodes.new("GeometryNodeSetShadeSmooth")
    ea = ng.nodes.new("GeometryNodeInputMeshEdgeAngle")
    cmp = ng.nodes.new("FunctionNodeCompare")
    cmp.data_type = "FLOAT"
    cmp.operation = "LESS_THAN"
    cmp.inputs[1].default_value = math.radians(40)
    ss.domain = "EDGE"
    ng.links.new(gi.outputs[0], ss.inputs["Geometry"])
    ng.links.new(ea.outputs["Unsigned Angle"], cmp.inputs[0])
    ng.links.new(cmp.outputs[0], ss.inputs["Shade Smooth"])
    ng.links.new(ss.outputs[0], go.inputs[0])
    _SBA["g"] = ng
    return ng


# ============================================================================================
# Materials
# ============================================================================================
_MATS = {}


def _cached(key, fn):
    m = _MATS.get(key)
    if m is not None:
        try:
            m.name  # still valid?
            return m
        except ReferenceError:
            pass
    m = fn()
    _MATS[key] = m
    return m


def _pbr(asset, scale=1.0, tint=None, name=None, rough_mult=1.0, rough_add=0.0, bump=1.0, hsv=None, blend=0.3):
    key = ("pbr", asset, scale, tint, name, rough_mult, rough_add, bump, hsv)
    return _cached(key, lambda: C.mat_pbr(asset, scale=scale, tint=tint, name=name or ("set_" + asset),
                                          rough_mult=rough_mult, rough_add=rough_add, bump=bump,
                                          hue_sat_val=hsv, blend=blend))


def _base_color_socket(m):
    b = C.bsdf(m)
    return b, (b.inputs["Base Color"].links[0].from_socket if b.inputs["Base Color"].links else None)


def _grime(m, axis="z", lo=1.6, hi=2.8, color=(0.12, 0.09, 0.07), amount=0.7, invert=False, noise_scale=1.5):
    """Darken a material's base colour along an object-space axis (soot on ceilings, damp at the
    wall foot ...). Modifies the material in place."""
    nt = m.node_tree
    b, src = _base_color_socket(m)
    tc = next((n for n in nt.nodes if n.type == "TEX_COORD"), None) or nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = noise_scale
    nz.inputs["Detail"].default_value = 4
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    add = nt.nodes.new("ShaderNodeMath")
    add.operation = "MULTIPLY_ADD"
    nt.links.new(nz.outputs["Fac"], add.inputs[0])
    add.inputs[1].default_value = (hi - lo) * 0.6
    add.inputs[2].default_value = -(hi - lo) * 0.3
    add2 = nt.nodes.new("ShaderNodeMath")
    add2.operation = "ADD"
    nt.links.new(sep.outputs["XYZ".index(axis.upper())], add2.inputs[0])
    nt.links.new(add.outputs[0], add2.inputs[1])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = hi if invert else lo
    mr.inputs["From Max"].default_value = lo if invert else hi
    mr.inputs["To Max"].default_value = amount
    nt.links.new(add2.outputs[0], mr.inputs["Value"])
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MIX"
    nt.links.new(mr.outputs["Result"], mix.inputs[0])
    if src is not None:
        nt.links.new(src, mix.inputs[1])
    else:
        mix.inputs[1].default_value = b.inputs["Base Color"].default_value
    mix.inputs[2].default_value = (*color, 1)
    nt.links.new(mix.outputs[0], b.inputs["Base Color"])
    return m


def _mat_simple(name, color, rough=0.6, metal=0.0, bump=0.0, bump_scale=30.0, var=0.0, var_scale=4.0, sheen=0.0,
                coat=0.0, spec=0.5, sss=0.0, sss_radius=(1.0, 0.4, 0.2)):
    """Principled material with optional procedural bump + colour variation (object coords)."""
    def mk():
        m = C.mat(name, color, rough=rough, metal=metal, sheen=sheen, coat=coat, spec=spec, sss=sss, sss_radius=sss_radius)
        nt = m.node_tree
        b = C.bsdf(m)
        tc = nt.nodes.new("ShaderNodeTexCoord")
        if var:
            nz = nt.nodes.new("ShaderNodeTexNoise")
            nz.inputs["Scale"].default_value = var_scale
            nz.inputs["Detail"].default_value = 5
            nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
            mr = nt.nodes.new("ShaderNodeMapRange")
            mr.inputs["To Min"].default_value = 1 - var
            mr.inputs["To Max"].default_value = 1 + var * 0.6
            nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
            mul = nt.nodes.new("ShaderNodeVectorMath")
            mul.operation = "SCALE"
            mul.inputs[0].default_value = color[:3]
            nt.links.new(mr.outputs["Result"], mul.inputs["Scale"])
            nt.links.new(mul.outputs[0], b.inputs["Base Color"])
        if bump:
            nz2 = nt.nodes.new("ShaderNodeTexNoise")
            nz2.inputs["Scale"].default_value = bump_scale
            nz2.inputs["Detail"].default_value = 8
            nt.links.new(tc.outputs["Object"], nz2.inputs["Vector"])
            bp = nt.nodes.new("ShaderNodeBump")
            bp.inputs["Strength"].default_value = bump
            bp.inputs["Distance"].default_value = 0.01
            nt.links.new(nz2.outputs["Fac"], bp.inputs["Height"])
            nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
        return m
    return _cached(("simple", name), mk)


def _flame_material(name="lamp_flame", strength=18.0, flicker=None):
    """Emissive flame with hot core and transparent tip (object-space Z gradient of a unit flame)."""
    def mk():
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        m.surface_render_method = "BLENDED"
        try:
            m.use_transparent_shadow = True
        except Exception:
            pass
        nt = m.node_tree
        for n in list(nt.nodes):
            if n.type != "OUTPUT_MATERIAL":
                nt.nodes.remove(n)
        out = nt.nodes["Material Output"]
        tc = nt.nodes.new("ShaderNodeTexCoord")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(tc.outputs["Generated"], sep.inputs[0])
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        cr = ramp.color_ramp
        cr.elements[0].position = 0.0
        cr.elements[0].color = (0.35, 0.55, 1.0, 1)   # blue base
        cr.elements[1].position = 1.0
        cr.elements[1].color = (1.0, 0.25, 0.03, 1)   # red-orange tip
        e = cr.elements.new(0.12)
        e.color = (1.0, 0.95, 0.8, 1)                  # white-hot core
        e = cr.elements.new(0.45)
        e.color = (1.0, 0.62, 0.18, 1)
        nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
        em = nt.nodes.new("ShaderNodeEmission")
        nt.links.new(ramp.outputs["Color"], em.inputs["Color"])
        st = nt.nodes.new("ShaderNodeValue")
        st.name = "strength"
        st.outputs[0].default_value = strength
        # per-instance flicker: noise(time + random)
        oi = nt.nodes.new("ShaderNodeObjectInfo")
        tval = nt.nodes.new("ShaderNodeValue")
        tval.name = "time"
        tval.outputs[0].default_value = 0.0
        madd = nt.nodes.new("ShaderNodeMath")
        madd.operation = "MULTIPLY_ADD"
        nt.links.new(oi.outputs["Random"], madd.inputs[0])
        madd.inputs[1].default_value = 97.0
        nt.links.new(tval.outputs[0], madd.inputs[2])
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.noise_dimensions = "1D"
        nz.inputs["Scale"].default_value = 1.0
        nz.inputs["Detail"].default_value = 2
        nt.links.new(madd.outputs[0], nz.inputs["W"])
        fl = nt.nodes.new("ShaderNodeMapRange")
        fl.inputs["From Min"].default_value = 0.3
        fl.inputs["From Max"].default_value = 0.7
        fl.inputs["To Min"].default_value = 0.65
        fl.inputs["To Max"].default_value = 1.25
        nt.links.new(nz.outputs["Fac"], fl.inputs["Value"])
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        nt.links.new(st.outputs[0], mul.inputs[0])
        nt.links.new(fl.outputs["Result"], mul.inputs[1])
        nt.links.new(mul.outputs[0], em.inputs["Strength"])
        # alpha: fade out at the tip and the very bottom
        a = nt.nodes.new("ShaderNodeFloatCurve")
        cv = a.mapping.curves[0]
        cv.points[0].location = (0.0, 0.35)
        cv.points[1].location = (1.0, 0.0)
        cv.points.new(0.15, 1.0)
        cv.points.new(0.7, 0.75)
        a.mapping.update()
        nt.links.new(sep.outputs["Z"], a.inputs["Value"])
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mix = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(a.outputs[0], mix.inputs[0])
        nt.links.new(tr.outputs[0], mix.inputs[1])
        nt.links.new(em.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs["Surface"])
        return m
    m = _cached(("flame", name), mk)
    _animate_flame_time(m)
    return m


def _animate_flame_time(m):
    """Key the material's 'time' value linearly so flame flicker animates (idempotent)."""
    nt = m.node_tree
    tv = nt.nodes.get("time")
    if tv is None or m.get("_time_keyed"):
        return
    sc = bpy.context.scene
    f0, f1 = 1, max(2, sc.frame_end)
    sock = tv.outputs[0]
    sock.default_value = 0.0
    sock.keyframe_insert("default_value", frame=f0)
    sock.default_value = (f1 - f0) / 24.0 * 7.0   # ~7 noise units / second
    sock.keyframe_insert("default_value", frame=f1)
    ad = nt.animation_data
    if ad and ad.action:
        for fc in C._fcurves(ad.action):
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
            fc.extrapolation = "LINEAR"
    m["_time_keyed"] = True


def clay_material(name="set_clay", color=(0.42, 0.22, 0.12), rough=0.75):
    """Fired terracotta (lamps, jars, cups)."""
    return _mat_simple(name, color, rough=rough, bump=0.25, bump_scale=60, var=0.25, var_scale=8)


def gold_material(name="set_gold", color=(1.0, 0.71, 0.29), rough=0.26, relief=None, relief_scale=(1, 1),
                  relief_strength=0.6, patina=0.35, hammered=0.15):
    """Burnished gold. relief = path of a height image (UV mapped) used as bump + cavity patina."""
    key = ("gold", name, color, rough, relief, relief_scale, relief_strength, patina, hammered)

    def mk():
        m = C.mat(name, color, rough=rough, metal=1.0)
        nt = m.node_tree
        b = C.bsdf(m)
        tc = nt.nodes.new("ShaderNodeTexCoord")
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 6
        nz.inputs["Detail"].default_value = 6
        nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
        rr = nt.nodes.new("ShaderNodeMapRange")
        rr.inputs["To Min"].default_value = rough * 0.6
        rr.inputs["To Max"].default_value = rough * 1.5
        nt.links.new(nz.outputs["Fac"], rr.inputs["Value"])
        nt.links.new(rr.outputs["Result"], b.inputs["Roughness"])
        col_out = None
        height = None
        if relief:
            img = nt.nodes.new("ShaderNodeTexImage")
            img.image = bpy.data.images.load(relief, check_existing=True)
            img.image.colorspace_settings.name = "Non-Color"
            mp = nt.nodes.new("ShaderNodeMapping")
            mp.inputs["Scale"].default_value = (relief_scale[0], relief_scale[1], 1)
            nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
            nt.links.new(mp.outputs[0], img.inputs["Vector"])
            height = img.outputs["Color"]
            # cavity patina: darker, rougher in the recesses
            pr = nt.nodes.new("ShaderNodeMapRange")
            pr.inputs["From Min"].default_value = 0.0
            pr.inputs["From Max"].default_value = 0.35
            pr.inputs["To Min"].default_value = patina
            pr.inputs["To Max"].default_value = 0.0
            nt.links.new(height, pr.inputs["Value"])
            mix = nt.nodes.new("ShaderNodeMixRGB")
            nt.links.new(pr.outputs["Result"], mix.inputs[0])
            mix.inputs[1].default_value = (*color, 1)
            mix.inputs[2].default_value = (color[0] * 0.35, color[1] * 0.22, color[2] * 0.1, 1)
            nt.links.new(mix.outputs[0], b.inputs["Base Color"])
        if hammered or height is not None:
            bp = nt.nodes.new("ShaderNodeBump")
            bp.inputs["Distance"].default_value = 0.02
            if height is not None:
                bp.inputs["Strength"].default_value = relief_strength
                nt.links.new(height, bp.inputs["Height"])
                if hammered:
                    bp2 = nt.nodes.new("ShaderNodeBump")
                    bp2.inputs["Strength"].default_value = hammered
                    vor = nt.nodes.new("ShaderNodeTexVoronoi")
                    vor.inputs["Scale"].default_value = 40
                    nt.links.new(tc.outputs["Object"], vor.inputs["Vector"])
                    nt.links.new(vor.outputs["Distance"], bp2.inputs["Height"])
                    nt.links.new(bp2.outputs["Normal"], bp.inputs["Normal"])
            else:
                bp.inputs["Strength"].default_value = hammered
                vor = nt.nodes.new("ShaderNodeTexVoronoi")
                vor.inputs["Scale"].default_value = 40
                nt.links.new(tc.outputs["Object"], vor.inputs["Vector"])
                nt.links.new(vor.outputs["Distance"], bp.inputs["Height"])
            nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
        return m
    return _cached(key, mk)


def straw_material(name="set_straw"):
    def mk():
        m = C.mat(name, (0.62, 0.46, 0.22), rough=0.62, spec=0.25, sheen=0.08)
        nt = m.node_tree
        b = C.bsdf(m)
        oi = nt.nodes.new("ShaderNodeObjectInfo")
        at = nt.nodes.new("ShaderNodeAttribute")
        at.attribute_type = "GEOMETRY"
        at.attribute_name = "strand_rand"
        ad = nt.nodes.new("ShaderNodeMath")
        ad.operation = "ADD"
        nt.links.new(oi.outputs["Random"], ad.inputs[0])
        nt.links.new(at.outputs["Fac"], ad.inputs[1])
        fr = nt.nodes.new("ShaderNodeMath")
        fr.operation = "FRACT"
        nt.links.new(ad.outputs[0], fr.inputs[0])
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        cr = ramp.color_ramp
        cr.elements[0].color = (0.36, 0.24, 0.10, 1)
        cr.elements[1].color = (0.80, 0.64, 0.34, 1)
        e = cr.elements.new(0.55)
        e.color = (0.66, 0.50, 0.24, 1)
        nt.links.new(fr.outputs[0], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
        b.inputs["Subsurface Weight"].default_value = 0.15
        b.inputs["Subsurface Radius"].default_value = (0.4, 0.3, 0.1)
        return m
    return _cached(("straw", name), mk)


def linen_material(name="set_linen", color=(0.86, 0.82, 0.72)):
    def mk():
        m = C.mat_pbr("rough_linen", scale=5.0, tint=color, name=name, bump=0.5, projection="BOX",
                      hue_sat_val=(0.5, 0.0, 1.6))
        b = C.bsdf(m)
        b.inputs["Sheen Weight"].default_value = 0.4
        b.inputs["Subsurface Weight"].default_value = 0.08
        return m
    return _cached(("linen", name, color), mk)


# ============================================================================================
# Geometry-node utilities (scatter, dust, lamp instancing)
# ============================================================================================
def _gn_group(name):
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    gi = ng.nodes.new("NodeGroupInput")
    go = ng.nodes.new("NodeGroupOutput")
    return ng, gi, go


def _rand(ng, kind, lo, hi, seed, id_sock=None):
    r = ng.nodes.new("FunctionNodeRandomValue")
    r.data_type = kind
    if kind == "FLOAT_VECTOR":
        r.inputs[0].default_value = lo
        r.inputs[1].default_value = hi
        out = r.outputs[0]
    else:
        r.inputs[2].default_value = lo
        r.inputs[3].default_value = hi
        out = r.outputs[1]
    r.inputs["Seed"].default_value = seed
    if id_sock is not None:
        ng.links.new(id_sock, r.inputs["ID"])
    return out


def _straw_strand_mesh(length=0.16, radius=0.0022, bend=0.02, name="straw_strand"):
    me = bpy.data.meshes.get(name)
    if me:
        return me
    segs, sides = 4, 3
    verts, faces = [], []
    for i in range(segs + 1):
        t = i / segs
        x = (t - 0.5) * length
        z = bend * (1 - (2 * t - 1) ** 2)
        r = radius * (1.0 - 0.35 * abs(2 * t - 1))
        for k in range(sides):
            a = TAU * k / sides
            verts.append((x, r * math.cos(a), z + r * math.sin(a)))
    for i in range(segs):
        for k in range(sides):
            k2 = (k + 1) % sides
            faces.append((i * sides + k, i * sides + k2, (i + 1) * sides + k2, (i + 1) * sides + k))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    return me


def straw_scatter(carrier, density=1500, seed=0, mat=None, length=0.16, keep_surface=True, tilt=0.35,
                  density_attr=None, realize=True):
    """Turn `carrier` (a mesh object) into a straw-covered surface via a Geometry Nodes modifier.
    density = strands per m^2. density_attr = optional vertex-group name scaling the density 0..1.
    The strands lie mostly flat (random yaw, +-tilt rad pitch/roll)."""
    mat = mat or straw_material()
    me = _straw_strand_mesh(length=length)
    if not me.materials:
        me.materials.append(mat)
    src = bpy.data.objects.get("straw_strand_src")
    if src is None:
        src = bpy.data.objects.new("straw_strand_src", me)
        bpy.context.scene.collection.objects.link(src)
        src.hide_render = True
        src.hide_viewport = True
    ng, gi, go = _gn_group("straw_scatter_%s" % carrier.name)
    dist = ng.nodes.new("GeometryNodeDistributePointsOnFaces")
    dist.distribute_method = "RANDOM"
    dist.inputs["Density"].default_value = density
    dist.inputs["Seed"].default_value = seed
    ng.links.new(gi.outputs[0], dist.inputs["Mesh"])
    if density_attr:
        na = ng.nodes.new("GeometryNodeInputNamedAttribute")
        na.data_type = "FLOAT"
        na.inputs["Name"].default_value = density_attr
        mul = ng.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        mul.inputs[1].default_value = density
        ng.links.new(na.outputs[0], mul.inputs[0])
        ng.links.new(mul.outputs[0], dist.inputs["Density"])
    oi = ng.nodes.new("GeometryNodeObjectInfo")
    oi.inputs["Object"].default_value = src
    oi.inputs["As Instance"].default_value = False
    inst = ng.nodes.new("GeometryNodeInstanceOnPoints")
    ng.links.new(dist.outputs["Points"], inst.inputs["Points"])
    ng.links.new(oi.outputs["Geometry"], inst.inputs["Instance"])
    rot = _rand(ng, "FLOAT_VECTOR", (-tilt, -tilt, 0), (tilt, tilt, TAU), seed + 1)
    ng.links.new(rot, inst.inputs["Rotation"])
    sc = _rand(ng, "FLOAT", 0.55, 1.35, seed + 2)
    ng.links.new(sc, inst.inputs["Scale"])
    res = inst.outputs[0]
    if realize:     # one mesh syncs/draws far faster in EEVEE than thousands of instances
        # keep per-strand colour variation: store a random value the material reads as 'strand_rand'
        st = ng.nodes.new("GeometryNodeStoreNamedAttribute")
        st.data_type = "FLOAT"
        st.domain = "INSTANCE"
        st.inputs["Name"].default_value = "strand_rand"
        rv = _rand(ng, "FLOAT", 0.0, 1.0, seed + 9)
        ng.links.new(rv, st.inputs["Value"])
        ng.links.new(res, st.inputs["Geometry"])
        rl = ng.nodes.new("GeometryNodeRealizeInstances")
        ng.links.new(st.outputs[0], rl.inputs["Geometry"])
        res = rl.outputs[0]
    if keep_surface:
        join = ng.nodes.new("GeometryNodeJoinGeometry")
        ng.links.new(gi.outputs[0], join.inputs[0])
        ng.links.new(res, join.inputs[0])
        ng.links.new(join.outputs[0], go.inputs[0])
    else:
        ng.links.new(res, go.inputs[0])
    mod = carrier.modifiers.new("straw", "NODES")
    mod.node_group = ng
    return mod


def dust(center=(0, 0, 1.5), size=(3, 3, 2), count=600, radius=0.0035, color=(1.0, 0.93, 0.82),
         emission=0.0, speed=0.08, amp=0.25, seed=0, b=None, name="dust"):
    """Floating dust motes with Geometry Nodes (no particle bake needed; drift is driven by scene
    time). They are lit by scene lights, so they sparkle inside light shafts. emission > 0 makes
    them self-lit (use ~0.5-3 for a magical glitter). Returns the object."""
    me = bpy.data.meshes.new(name)
    o = bpy.data.objects.new(name, me)
    if b:
        b.add(o)
    else:
        bpy.context.scene.collection.objects.link(o)
    o.location = center
    m = C.mat(name + "_mat", color, rough=0.9, emission=color if emission else None, emission_strength=emission)
    ng, gi, go = _gn_group(name + "_gn")
    pts = ng.nodes.new("GeometryNodePoints")
    pts.inputs["Count"].default_value = count
    idx = ng.nodes.new("GeometryNodeInputIndex")
    pos = _rand(ng, "FLOAT_VECTOR", tuple(-s / 2 for s in size), tuple(s / 2 for s in size), seed, idx.outputs[0])
    ng.links.new(pos, pts.inputs["Position"])
    t = ng.nodes.new("GeometryNodeInputSceneTime")
    tw = ng.nodes.new("ShaderNodeMath")
    tw.operation = "MULTIPLY"
    tw.inputs[1].default_value = speed
    ng.links.new(t.outputs["Seconds"], tw.inputs[0])
    nz = ng.nodes.new("ShaderNodeTexNoise")
    nz.noise_dimensions = "4D"
    nz.inputs["Scale"].default_value = 0.6
    nz.inputs["Detail"].default_value = 1
    p_in = ng.nodes.new("GeometryNodeInputPosition")
    ng.links.new(p_in.outputs[0], nz.inputs["Vector"])
    ng.links.new(tw.outputs[0], nz.inputs["W"])
    sub = ng.nodes.new("ShaderNodeVectorMath")
    sub.operation = "SUBTRACT"
    sub.inputs[1].default_value = (0.5, 0.5, 0.5)
    ng.links.new(nz.outputs["Color"], sub.inputs[0])
    scl = ng.nodes.new("ShaderNodeVectorMath")
    scl.operation = "SCALE"
    scl.inputs["Scale"].default_value = amp * 2
    ng.links.new(sub.outputs[0], scl.inputs[0])
    # slow upward drift
    up = ng.nodes.new("ShaderNodeVectorMath")
    up.operation = "MULTIPLY_ADD"
    up.inputs[1].default_value = (0.004, 0.002, 0.012)
    ng.links.new(t.outputs["Seconds"], up.inputs[0])
    ng.links.new(scl.outputs[0], up.inputs[2])
    setp = ng.nodes.new("GeometryNodeSetPosition")
    ng.links.new(pts.outputs[0], setp.inputs["Geometry"])
    ng.links.new(up.outputs[0], setp.inputs["Offset"])
    ico = ng.nodes.new("GeometryNodeMeshIcoSphere")
    ico.inputs["Radius"].default_value = radius
    ico.inputs["Subdivisions"].default_value = 1
    sm = ng.nodes.new("GeometryNodeSetMaterial")
    sm.inputs["Material"].default_value = m
    ng.links.new(ico.outputs["Mesh"], sm.inputs["Geometry"])
    inst = ng.nodes.new("GeometryNodeInstanceOnPoints")
    ng.links.new(setp.outputs[0], inst.inputs["Points"])
    ng.links.new(sm.outputs[0], inst.inputs["Instance"])
    sc = _rand(ng, "FLOAT", 0.4, 1.4, seed + 5)
    ng.links.new(sc, inst.inputs["Scale"])
    ng.links.new(inst.outputs[0], go.inputs[0])
    mod = o.modifiers.new("dust", "NODES")
    mod.node_group = ng
    return o


# ============================================================================================
# Lights
# ============================================================================================
def flicker_light(light_obj, base=None, amount=0.18, speed=9.0, seed=0, f0=1, f1=None):
    """Key a candle/oil-lamp flicker on a light's energy (per frame, smooth noise)."""
    ld = light_obj.data
    base = ld.energy if base is None else base
    f1 = f1 or bpy.context.scene.frame_end

    def fn(f):
        t = f / 24.0 * speed
        n = noise.noise(Vector((t, seed * 3.1, 0.5))) * 0.7 + noise.noise(Vector((t * 2.7, seed, 4.2))) * 0.3
        return base * max(0.2, 1.0 + amount * 2.0 * n)
    C.key_fn(ld, "energy", fn, f0, f1)
    return light_obj


# ============================================================================================
# World: night sky with stars (cheap, procedural)
# ============================================================================================
def night_world(strength=1.0, zenith=(0.0025, 0.004, 0.012), horizon=(0.012, 0.022, 0.045), stars=1.0,
                star_dir=None, star_strength=60.0, glow=(0.006, 0.011, 0.022)):
    """Dark-blue night sky gradient + star field (+ optional single bright star in direction
    `star_dir` (vector), e.g. the star of Bethlehem). Returns the Background node."""
    w, nt, out = C._world()
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nrm = nt.nodes.new("ShaderNodeVectorMath")
    nrm.operation = "NORMALIZE"
    nt.links.new(tc.outputs["Generated"], nrm.inputs[0])
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(nrm.outputs[0], sep.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.elements[0].position = 0.0
    cr.elements[0].color = (*horizon, 1)
    cr.elements[1].position = 0.6
    cr.elements[1].color = (*zenith, 1)
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    col = ramp.outputs["Color"]
    if stars:
        vor = nt.nodes.new("ShaderNodeTexVoronoi")
        vor.feature = "F1"
        vor.inputs["Scale"].default_value = 140.0
        nt.links.new(nrm.outputs[0], vor.inputs["Vector"])
        sz = nt.nodes.new("ShaderNodeMapRange")       # star core: distance < 0.15 cell
        sz.inputs["From Min"].default_value = 0.16
        sz.inputs["From Max"].default_value = 0.02
        nt.links.new(vor.outputs["Distance"], sz.inputs["Value"])
        sepc = nt.nodes.new("ShaderNodeSeparateColor")
        nt.links.new(vor.outputs["Color"], sepc.inputs[0])
        pw = nt.nodes.new("ShaderNodeMath")            # brightness distribution: few bright ones
        pw.operation = "POWER"
        pw.inputs[1].default_value = 9.0
        nt.links.new(sepc.outputs[0], pw.inputs[0])
        m1 = nt.nodes.new("ShaderNodeMath")
        m1.operation = "MULTIPLY"
        nt.links.new(sz.outputs["Result"], m1.inputs[0])
        nt.links.new(pw.outputs[0], m1.inputs[1])
        hz = nt.nodes.new("ShaderNodeMapRange")       # fade near horizon
        hz.inputs["From Min"].default_value = 0.02
        hz.inputs["From Max"].default_value = 0.25
        hz.inputs["To Max"].default_value = 3.0 * stars
        nt.links.new(sep.outputs["Z"], hz.inputs["Value"])
        m2 = nt.nodes.new("ShaderNodeMath")
        m2.operation = "MULTIPLY"
        nt.links.new(m1.outputs[0], m2.inputs[0])
        nt.links.new(hz.outputs["Result"], m2.inputs[1])
        # faint milky band of tiny stars
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 2.5
        nz.inputs["Detail"].default_value = 6
        nt.links.new(nrm.outputs[0], nz.inputs["Vector"])
        add = nt.nodes.new("ShaderNodeMixRGB")
        add.blend_type = "ADD"
        add.inputs[0].default_value = 1.0
        nt.links.new(col, add.inputs[1])
        sc = nt.nodes.new("ShaderNodeCombineColor")
        nt.links.new(m2.outputs[0], sc.inputs[0])
        nt.links.new(m2.outputs[0], sc.inputs[1])
        m3 = nt.nodes.new("ShaderNodeMath")
        m3.operation = "MULTIPLY"
        m3.inputs[1].default_value = 1.15
        nt.links.new(m2.outputs[0], m3.inputs[0])
        nt.links.new(m3.outputs[0], sc.inputs[2])
        nt.links.new(sc.outputs[0], add.inputs[2])
        col = add.outputs[0]
    if star_dir is not None:
        d = Vector(star_dir).normalized()
        dot = nt.nodes.new("ShaderNodeVectorMath")
        dot.operation = "DOT_PRODUCT"
        dot.inputs[1].default_value = d
        nt.links.new(nrm.outputs[0], dot.inputs[0])
        core_ = nt.nodes.new("ShaderNodeMath")
        core_.operation = "POWER"
        core_.inputs[1].default_value = 60000.0
        nt.links.new(dot.outputs["Value"], core_.inputs[0])
        halo = nt.nodes.new("ShaderNodeMath")
        halo.operation = "POWER"
        halo.inputs[1].default_value = 700.0
        nt.links.new(dot.outputs["Value"], halo.inputs[0])
        mh = nt.nodes.new("ShaderNodeMath")
        mh.operation = "MULTIPLY_ADD"
        mh.inputs[1].default_value = 0.04
        nt.links.new(halo.outputs[0], mh.inputs[0])
        nt.links.new(core_.outputs[0], mh.inputs[2])
        ms = nt.nodes.new("ShaderNodeMath")
        ms.operation = "MULTIPLY"
        ms.inputs[1].default_value = star_strength
        nt.links.new(mh.outputs[0], ms.inputs[0])
        add2 = nt.nodes.new("ShaderNodeMixRGB")
        add2.blend_type = "ADD"
        nt.links.new(ms.outputs[0], add2.inputs[0])
        nt.links.new(col, add2.inputs[1])
        add2.inputs[2].default_value = (0.85, 0.92, 1.0, 1)
        col = add2.outputs[0]
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs[1].default_value = strength
    nt.links.new(col, bg.inputs[0])
    nt.links.new(bg.outputs[0], out.inputs["Surface"])
    return bg


def sky_world(sun_elevation=8.0, sun_rotation=0.0, strength=0.4, light_strength=None, air=1.2, dust=2.0, ozone=1.0,
              tint=None):
    """Nishita sky whose LIGHTING strength (`light_strength`) is separate from what the camera sees
    (`strength`). Returns the lighting Background node; key its inputs[1] to dim world light when
    the camera goes inside a closed room (EEVEE world light otherwise leaks through walls)."""
    sky, bg = C.world_sky(sun_elevation=sun_elevation, sun_rotation=sun_rotation, strength=strength, air=air,
                          dust=dust, ozone=ozone, tint=tint)
    nt = bpy.context.scene.world.node_tree
    out = next(n for n in nt.nodes if n.type == "OUTPUT_WORLD")
    src = bg.inputs[0].links[0].from_socket
    bgl = nt.nodes.new("ShaderNodeBackground")
    bgl.name = "light_bg"
    bgl.inputs[1].default_value = strength if light_strength is None else light_strength
    nt.links.new(src, bgl.inputs[0])
    lp = nt.nodes.new("ShaderNodeLightPath")
    ms = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Camera Ray"], ms.inputs[0])
    nt.links.new(bgl.outputs[0], ms.inputs[1])
    nt.links.new(bg.outputs[0], ms.inputs[2])
    nt.links.new(ms.outputs[0], out.inputs["Surface"])
    return bgl


def world_light_keys(pairs):
    """Key the world LIGHTING strength (see sky_world): pairs = [(frame, strength), ...]."""
    nt = bpy.context.scene.world.node_tree
    bgl = nt.nodes.get("light_bg")
    if bgl is None:
        return
    for f, v in pairs:
        bgl.inputs[1].default_value = v
        bgl.inputs[1].keyframe_insert("default_value", frame=f)


def _add_chisel(m, strength=0.35, scale=9.0):
    """Add diagonal chisel/tool-mark bump to a material (object coords)."""
    nt = m.node_tree
    b = C.bsdf(m)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wv = nt.nodes.new("ShaderNodeTexWave")
    wv.wave_type = "BANDS"
    wv.bands_direction = "DIAGONAL"
    wv.inputs["Scale"].default_value = scale
    wv.inputs["Distortion"].default_value = 6.0
    wv.inputs["Detail"].default_value = 3.0
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = strength
    bp.inputs["Distance"].default_value = 0.01
    nt.links.new(wv.outputs["Fac"], bp.inputs["Height"])
    nl = b.inputs["Normal"].links
    if nl:
        nt.links.new(nl[0].from_socket, bp.inputs["Normal"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


# ============================================================================================
# Oil lamp (Herodian clay lamp) + many-lamp instancing
# ============================================================================================
def _lamp_body_mesh(name="oil_lamp_body"):
    me = bpy.data.meshes.get(name)
    if me:
        return me
    bm = bmesh.new()
    # body: squashed sphere
    bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=10, radius=1.0)
    for v in bm.verts:
        x, y, z = v.co
        z = z * 0.42 + 0.42 * 0.95
        # flatter top with a sunken filling basin
        r = math.hypot(x, y)
        if z > 0.6:
            z -= 0.25 * max(0.0, 1 - r * 1.6)
        # spatulate nozzle pulled out towards +X (Herodian 'knife-pared' lamp)
        if x > 0.15:
            k = (x - 0.15) / 0.85
            x += 0.95 * k ** 1.5
            y *= 1.0 - 0.45 * k
            z = 0.42 * 0.95 + (z - 0.42 * 0.95) * (1.0 - 0.35 * k)
        v.co = Vector((x * 0.035, y * 0.033, z * 0.034))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    return me


def _flame_mesh(name="oil_lamp_flame", h=0.034, r=0.0055):
    me = bpy.data.meshes.get(name)
    if me:
        return me
    prof = []
    n = 12
    for j in range(n + 1):
        t = j / n
        rr = r * (math.sin(math.pi * min(1.0, t * 1.25)) ** 0.6) * (1 - t) ** 0.35 if t < 1 else 0.0
        prof.append((max(rr, 1e-4 if 0 < t < 1 else 0.0), t * h))
    verts, faces = [], []
    segs = 10
    for i in range(segs):
        a = TAU * i / segs
        for rr, z in prof:
            verts.append((rr * math.cos(a), rr * math.sin(a), z))
    m = len(prof)
    for i in range(segs):
        i2 = (i + 1) % segs
        for j in range(m - 1):
            faces.append((i * m + j, i2 * m + j, i2 * m + j + 1, i * m + j + 1))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    return me


LAMP_TIP = Vector((0.0655, 0.0, 0.026))   # nozzle tip (flame root) in lamp-local coords (scale 1)


def oil_lamp(loc=(0, 0, 0), rot_z=0.0, scale=1.0, light=True, energy=12.0, temp=2300, flame_strength=18.0,
             flicker=0.18, seed=0, b=None, name="oil_lamp", shadow=True, light_radius=0.012, parent=None):
    """Clay oil lamp with a flickering flame (+ optional warm point light at the flame).
    Returns (lamp_obj, flame_obj, light_obj_or_None). The lamp origin is its base; the flame sits at
    the nozzle tip (+X). Animate by moving/parenting `lamp_obj` (flame + light are its children)."""
    clay = clay_material()
    body = bpy.data.objects.new(name, _lamp_body_mesh())
    if not body.data.materials:
        body.data.materials.append(clay)
    (b.add(body, parent=parent) if b else bpy.context.scene.collection.objects.link(body))
    if parent is not None and not b:
        body.parent = parent
    body.location = loc
    body.rotation_euler = (0, 0, math.radians(rot_z))
    body.scale = (scale,) * 3
    fm = _flame_material(strength=flame_strength)
    fl = bpy.data.objects.new(name + "_flame", _flame_mesh())
    if not fl.data.materials:
        fl.data.materials.append(fm)
    (b.add(fl, parent=body) if b else bpy.context.scene.collection.objects.link(fl))
    fl.parent = body
    fl.location = LAMP_TIP + Vector((0.002, 0, -0.002))
    fl.visible_shadow = False
    lo = None
    if light:
        ld = bpy.data.lights.new(name + "_light", "POINT")
        ld.energy = energy
        ld.color = C.kelvin(temp)
        ld.shadow_soft_size = light_radius
        ld.use_shadow = shadow
        lo = bpy.data.objects.new(name + "_light", ld)
        (b.add(lo, parent=body) if b else bpy.context.scene.collection.objects.link(lo))
        lo.parent = body
        lo.location = LAMP_TIP + Vector((0.0, 0, 0.022))
        if flicker:
            flicker_light(lo, energy, amount=flicker, seed=seed)
    # wick flame wobble: tiny scale flicker
    if flicker:
        def sfn(f, s=seed):
            n = noise.noise(Vector((f / 24.0 * 6.0, s * 1.7, 2.0)))
            return 1.0 + 0.18 * n
        C.key_fn(fl, "scale", lambda f: (1.0, 1.0, sfn(f)), 1, bpy.context.scene.frame_end, step=2)
    return body, fl, lo


def lamp_field(points, b=None, name="lamp_field", scale=1.0, flame_strength=16.0, yaw_random=True, seed=0):
    """Hundreds of instanced (geometry-nodes) clay lamps with flickering emissive flames and NO
    lights (cheap). points = list of (x, y, z) or (x, y, z, yaw_deg) in the parent's local space.
    Returns the carrier object. Light the area with a few area/point lights to fake their glow."""
    rnd = random.Random(seed)
    verts = []
    yaws = []
    for p in points:
        verts.append(tuple(p[:3]))
        yaws.append(math.radians(p[3]) if len(p) > 3 else (rnd.random() * TAU if yaw_random else 0.0))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], [])
    attr = me.attributes.new("yaw", "FLOAT", "POINT")
    attr.data.foreach_set("value", yaws)
    me.update()
    o = bpy.data.objects.new(name, me)
    (b.add(o) if b else bpy.context.scene.collection.objects.link(o))
    # source lamp (body + flame joined as one instance geometry with 2 materials)
    src_name = "lamp_inst_src"
    src = bpy.data.objects.get(src_name)
    if src is None:
        bm = bmesh.new()
        bm.from_mesh(_lamp_body_mesh())
        fl = bmesh.new()
        fl.from_mesh(_flame_mesh())
        bmesh.ops.translate(fl, vec=LAMP_TIP + Vector((0.002, 0, -0.002)), verts=fl.verts)
        tmp = bpy.data.meshes.new("_tmpflame")
        fl.to_mesh(tmp)
        fl.free()
        for f in bm.faces:
            f.material_index = 0
        nb = len(bm.faces)
        bm.from_mesh(tmp)
        for f in bm.faces[nb:] if hasattr(bm.faces, "__getitem__") else []:
            pass
        bm.faces.ensure_lookup_table()
        for i in range(nb, len(bm.faces)):
            bm.faces[i].material_index = 1
        bpy.data.meshes.remove(tmp)
        sme = bpy.data.meshes.new(src_name)
        bm.to_mesh(sme)
        bm.free()
        sme.polygons.foreach_set("use_smooth", [True] * len(sme.polygons))
        sme.materials.append(clay_material())
        sme.materials.append(_flame_material(strength=flame_strength))
        src = bpy.data.objects.new(src_name, sme)
        bpy.context.scene.collection.objects.link(src)
        src.hide_render = True
        src.hide_viewport = True
    ng, gi, go = _gn_group(name + "_gn")
    m2p = ng.nodes.new("GeometryNodeMeshToPoints")
    ng.links.new(gi.outputs[0], m2p.inputs["Mesh"])
    oi = ng.nodes.new("GeometryNodeObjectInfo")
    oi.inputs["Object"].default_value = src
    inst = ng.nodes.new("GeometryNodeInstanceOnPoints")
    ng.links.new(m2p.outputs[0], inst.inputs["Points"])
    ng.links.new(oi.outputs["Geometry"], inst.inputs["Instance"])
    na = ng.nodes.new("GeometryNodeInputNamedAttribute")
    na.data_type = "FLOAT"
    na.inputs["Name"].default_value = "yaw"
    ce = ng.nodes.new("ShaderNodeCombineXYZ")
    ng.links.new(na.outputs[0], ce.inputs["Z"])
    ng.links.new(ce.outputs[0], inst.inputs["Rotation"])
    sc = _rand(ng, "FLOAT", 0.9 * scale, 1.1 * scale, seed + 3)
    ng.links.new(sc, inst.inputs["Scale"])
    ng.links.new(inst.outputs[0], go.inputs[0])
    mod = o.modifiers.new("lamps", "NODES")
    mod.node_group = ng
    return o


# ============================================================================================
# Small props
# ============================================================================================
def clay_jar(loc, height=0.55, b=None, name="jar", rot_z=0.0, mat=None, handles=True):
    """Storage jar (lathe). Returns object (origin at base)."""
    h = height
    prof = [(0.0001, 0.0), (0.10 * h, 0.0), (0.22 * h, 0.06 * h), (0.32 * h, 0.30 * h), (0.33 * h, 0.45 * h),
            (0.28 * h, 0.70 * h), (0.16 * h, 0.86 * h), (0.11 * h, 0.92 * h), (0.12 * h, 0.98 * h),
            (0.14 * h, 1.0 * h), (0.12 * h, 1.0 * h), (0.10 * h, 0.94 * h), (0.09 * h, 0.75 * h)]
    o = _lathe(prof, 28, name, b, mat or clay_material())
    o.location = loc
    o.rotation_euler = (0, 0, math.radians(rot_z))
    return o


def clay_cup(loc, b=None, name="cup", wine=True, mat=None, height=0.085):
    h = height
    prof = [(0.0001, 0.0), (0.024 * h / 0.085, 0.0), (0.03 * h / 0.085, 0.01 * h / 0.085),
            (0.038 * h / 0.085, 0.05 * h / 0.085), (0.042 * h / 0.085, h), (0.038 * h / 0.085, h),
            (0.034 * h / 0.085, 0.05 * h / 0.085), (0.026 * h / 0.085, 0.012 * h / 0.085), (0.0001, 0.012 * h / 0.085)]
    o = _lathe(prof, 32, name, b, mat or clay_material("set_clay_cup", (0.36, 0.18, 0.1), 0.55))
    o.location = loc
    if wine:
        wm = _cached(("wine",), lambda: C.mat("set_wine", (0.09, 0.005, 0.012), rough=0.04, spec=0.6, coat=0.3))
        w = _lathe([(0.0001, 0.0), (0.0365 * h / 0.085, 0.0)], 32, name + "_wine", b, wm, cap_bottom=False)
        w.parent = o
        w.location = (0, 0, h * 0.78)
    return o


# ============================================================================================
# 1. STABLE CAVE (s07a nativity)
# ============================================================================================
# ============================================================================================
# 1. STABLE CAVE (s07a nativity)
# ============================================================================================
def _shell(b, name, rx, ry, H, cx, cy, mat, seed, nt_=192, np_=52, amp=0.32, z_floor=-0.12, strata=0.03,
           ceil_flat=0.5, thickness=0.45, door=None):
    """Irregular, inward-facing cave dome with a Solidify modifier (closed, so Boolean cutters can
    open doorways). Returns (obj, wall_fn); wall_fn(theta, z) -> (point_on_wall, inward_normal)."""
    rs = random.Random(seed)
    so = Vector((rs.random() * 50, rs.random() * 50, rs.random() * 50))

    def raw(th, ph):
        if ph < 0:
            return Vector((cx + rx * math.cos(th), cy + ry * math.sin(th), z_floor * (-ph / 0.1)))
        hr = max(0.0, math.cos(ph)) ** ceil_flat
        z = (math.sin(ph) ** 0.85) * H
        return Vector((cx + rx * hr * math.cos(th), cy + ry * hr * math.sin(th), z))

    def disp(p):
        q = p * 0.5 + so
        d = amp * C.fbm(q.x, q.y + q.z * 0.7, octaves=4, seed=so.z)
        d += 0.11 * noise.noise(p * 1.6 + so)
        d += 0.04 * noise.noise(p * 4.0 + so)
        d += 0.015 * noise.noise(p * 9.0 + so)
        d += strata * math.sin(p.z * 7.0 + 2.5 * noise.noise(p * 0.7 + so))   # limestone bedding
        return d

    def normal_in(p):
        c = Vector((cx, cy, min(p.z, H * 0.55) * 0.6))
        n = (c - p)
        n.z *= 0.6
        return n.normalized()

    phis = [-0.1] + [(math.pi / 2) * (j / (np_ - 1)) ** 0.9 * 0.985 for j in range(np_)]
    verts = []
    for ph in phis:
        for i in range(nt_):
            th = TAU * i / nt_
            p = raw(th, ph)
            verts.append(p - normal_in(p) * disp(p))
    top = Vector((cx, cy, H)) - Vector((0, 0, 1)) * (disp(Vector((cx, cy, H))) * 0.6)
    verts.append(top)
    faces = []
    nj = len(phis)
    for j in range(nj - 1):
        for i in range(nt_):
            i2 = (i + 1) % nt_
            faces.append((j * nt_ + i, (j + 1) * nt_ + i, (j + 1) * nt_ + i2, j * nt_ + i2))
    t = len(verts) - 1
    for i in range(nt_):
        faces.append(((nj - 1) * nt_ + i, t, (nj - 1) * nt_ + (i + 1) % nt_))
    door_info = None
    if door:
        dth, hw, dh = door
        p = raw(dth, 0.0)
        dpt = p - normal_in(p) * disp(p)
        dpt.z = 0.0
        n0 = normal_in(raw(dth, 0.3))
        odir = Vector((-n0.x, -n0.y, 0)).normalized()
        side = Vector((0, 0, 1)).cross(odir).normalized()
        spring = dh - hw * 0.85

        def local(q):
            d = q - dpt
            return d.dot(side), q.z, d.dot(odir)

        def hw_at(u, z):
            return hw * (1.0 + 0.09 * noise.noise(Vector((u * 2.5, z * 2.5, seed + 0.5))))

        def inside(u, z):
            w = hw_at(u, z)
            if z < spring:
                return abs(u) < w
            return (u / w) ** 2 + ((z - spring) / (dh - spring)) ** 2 < 1.0

        def snap(u, z):
            w = hw_at(u, z)
            if z < spring:
                return (w if u > 0 else -w), z
            a = math.atan2((z - spring) / (dh - spring), u / w)
            a = max(0.0, min(math.pi, a))
            return math.cos(a) * w, spring + math.sin(a) * (dh - spring)

        keep = []
        for f in faces:
            c = sum((verts[k] for k in f), Vector()) / len(f)
            u, z, dd = local(c)
            keep.append(not (abs(dd) < 1.2 and inside(u, z)))
        used = set()
        faces = [f for f, k in zip(faces, keep) if k]
        # boundary vertices of the hole: verts used by both kept and removed faces
        removed_v = set()
        for f, k in zip([f for f in faces], [True] * len(faces)):
            used.update(f)
        door_info = (dpt, odir, side, local, snap, inside)
    o = _mesh_obj(name, verts, faces, b, True, mat)
    me = o.data
    if door_info:
        dpt, odir, side, local, snap, inside = door_info
        bm = bmesh.new()
        bm.from_mesh(me)
        for v in bm.verts:
            if v.is_boundary and v.co.z > 0.0:
                u, z, dd = local(v.co)
                if abs(dd) < 1.2 and abs(u) < door[1] * 2.5:
                    nu, nz = snap(u, z)
                    v.co = v.co + side * (nu - u) + Vector((0, 0, nz - z))
        loose = [v for v in bm.verts if not v.link_faces]
        bmesh.ops.delete(bm, geom=loose, context="VERTS")
        bm.to_mesh(me)
        bm.free()
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    p0 = me.polygons[len(me.polygons) // 3]
    if (Vector((cx, cy, H * 0.4)) - p0.center).dot(p0.normal) < 0:
        me.flip_normals()
    o["shell_thickness"] = thickness

    def wall_fn(th, z):
        z = max(0.0, min(H * 0.98, z))
        ph = math.asin(min(1.0, (z / H) ** (1 / 0.85)))
        p = raw(th, ph)
        n = normal_in(p)
        return p - n * disp(p), n
    return o, wall_fn


def _arch_cutter(name, b, center, out_dir, half_w, height, depth=(-0.7, 1.3), seed=0, jag=0.07, rings=5):
    """Closed prism with a rough round-arched outline, extruded along out_dir (for doorways)."""
    out_dir = Vector(out_dir).normalized()
    side = Vector((0, 0, 1)).cross(out_dir).normalized()
    outline = []
    K = 28
    spring = height - half_w * 0.9
    for k in range(K + 1):                   # left jamb up, arch over, right jamb down
        a = math.pi * k / K
        u = -math.cos(a)
        z = spring + math.sin(a) * (height - spring)
        outline.append((u * half_w, z))
    outline = [(-half_w, -0.4), (-half_w, spring * 0.5)] + outline + [(half_w, spring * 0.5), (half_w, -0.4)]
    so = Vector((seed, seed * 1.3, 0.7))
    verts, faces = [], []
    n = len(outline)
    for r in range(rings):
        d = depth[0] + (depth[1] - depth[0]) * r / (rings - 1)
        for (u, z) in outline:
            j = jag * noise.noise(Vector((u * 3.0, z * 3.0, d * 2.0)) + so)
            jz = jag * noise.noise(Vector((u * 3.0 + 5, z * 3.0, d * 2.0)) + so) if z > 0 else 0.0
            p = Vector(center) + side * (u * (1 + j)) + out_dir * d + Vector((0, 0, z + jz))
            verts.append(p)
    for r in range(rings - 1):
        for k in range(n):
            k2 = (k + 1) % n
            faces.append((r * n + k, r * n + k2, (r + 1) * n + k2, (r + 1) * n + k))
    faces.append(tuple(range(n))[::-1])
    faces.append(tuple(range((rings - 1) * n, rings * n)))
    o = _mesh_obj(name, verts, faces, b, False)
    o.hide_render = True
    o.display_type = "WIRE"
    return o


def _cut(target, cutter, solver="EXACT", hole_tolerant=True):
    m = target.modifiers.new("cut_" + cutter.name, "BOOLEAN")
    m.operation = "DIFFERENCE"
    m.object = cutter
    m.solver = solver
    if solver == "EXACT":
        m.use_hole_tolerant = hole_tolerant
    return m


def _solidify(o, thickness, offset=-1.0):
    sol = o.modifiers.new("thick", "SOLIDIFY")
    sol.thickness = thickness
    sol.offset = offset    # -1: grow behind the normals (shell normals point into the room)
    sol.use_rim = True
    return sol


def stable_cave(ctx, loc=(0, 0, 0), rot_z=0.0, coll=None, world=True, lamps=2, starlight=1.0, lamp_energy=1.0,
                fog=True, dust_motes=True, straw=True, straw_density=900, manger="stone", seed=7, props=True,
                straw_shadows=False):
    """Bethlehem stable cave at night (s07a). Local layout (metres, floor z=0):
        cave interior ~6.6 x 7.4 m, ceiling ~2.75 m, soot-darkened; arched doorway in the back-left
        wall with silver starlight streaming in (spot + volumetric haze + dust); carved stone manger
        filled with straw centre-right; oil lamp on a rock ledge (right wall) and one on a stone by
        Mary; straw-littered floor; clay jars, hay heap, shepherd's staff.
    Anchors: mary (top of her seat stone; yaw faces the manger), mary_head (approx eye height
    seated), manger (centre top of the straw), baby_manger (where a swaddled baby lies),
    ox (lying, back right), donkey (standing, back left), doorway (threshold centre),
    lamp_ledge, lamp_floor (flame positions), star (far point along the star direction).
    Cameras: wide, mary_close, manger_close, doorway_view, low_straw.
    Lights: lamp_ledge, lamp_floor (flickering points), starlight (cool volumetric spot), door_fill,
    bounce (warm ceiling fill), floor_bounce (warm up-light from the straw).
    world=True installs night_world() with the star visible through the doorway.
    """
    b = _B("StableCave", loc, rot_z, coll, seed)
    rnd = b.rnd
    cx, cy, rx, ry, H = 0.0, 1.6, 3.3, 3.7, 2.75
    door_th = math.radians(104)            # back-left
    rock = _cached(("cave_rock",), lambda: _grime(_grime(
        C.mat_pbr("worn_rock_natural_01", scale=0.9, tint=(0.95, 0.9, 0.84), name="set_cave_rock", bump=1.5,
                  hue_sat_val=(0.5, 0.75, 1.0)),
        "z", 1.55, 2.9, (0.035, 0.028, 0.024), 0.88), "z", 0.4, -0.05, (0.16, 0.11, 0.07), 0.45, noise_scale=2.0))
    shell, wall = _shell(b, "cave_shell", rx, ry, H, cx, cy, rock, seed, door=(door_th, 0.62, 1.85))
    _solidify(shell, 0.45)
    b.info.objects["shell"] = shell
    dp, dn = wall(door_th, 0.0)
    dn3 = wall(door_th, 0.3)[1]
    out_dir = Vector((-dn3.x, -dn3.y, 0)).normalized()
    door_c = Vector((dp.x, dp.y, 0.0))

    # ---------- floor: straw mask attribute + scattered strands ----------
    def straw_mask(x, y):
        d = 0.0
        for (px, py, rad) in ((0.5, 2.3, 1.5), (-0.5, 2.0, 1.1), (1.9, 3.6, 1.3), (-1.6, 3.8, 1.1), (2.2, 4.6, 1.0)):
            d = max(d, 1.0 - math.hypot(x - px, y - py) / rad)
        return max(0.0, min(1.0, d * 1.5 + 0.4 * noise.noise(Vector((x * 1.7, y * 1.7, 5.0))) - 0.05))
    floor_m = _cached(("cave_floor",), lambda: _add_straw_layer(
        C.mat_pbr("dirt", scale=0.8, tint=(0.6, 0.48, 0.36), name="set_cave_floor")))
    n = 150
    S_, ox_, oy_ = 15.0, 0.0, 3.0
    verts, faces, mask = [], [], []
    for j in range(n + 1):
        for i in range(n + 1):
            x = ox_ - S_ / 2 + S_ * i / n
            y = oy_ - S_ / 2 + S_ * j / n
            r_out = max(0.0, math.hypot((x - cx) / rx, (y - cy) / ry) - 1.1)
            z = 0.025 * noise.noise(Vector((x * 2.5, y * 2.5, 1.0))) - 0.6 * r_out ** 1.5
            verts.append((x, y, z))
            mask.append(straw_mask(x, y))
    for j in range(n):
        for i in range(n):
            a = j * (n + 1) + i
            faces.append((a, a + 1, a + n + 2, a + n + 1))
    fl = _mesh_obj("cave_floor", verts, faces, b, True, floor_m)
    at = fl.data.attributes.new("straw", "FLOAT", "POINT")
    at.data.foreach_set("value", mask)
    b.info.objects["floor"] = fl
    if straw:
        straw_scatter(fl, density=straw_density, seed=seed + 3, keep_surface=True, density_attr="straw", tilt=0.22)
    fl.visible_shadow = False      # nothing below the floor; saves the straw in every shadow map

    hills_m = _mat_simple("set_hills", (0.03, 0.03, 0.035), rough=0.95)
    hv, hf = [], []
    for i in range(61):
        a = math.radians(30 + 120 * i / 60)
        x, y = math.cos(a) * 70.0, math.sin(a) * 70.0 + 3
        hgt = 3.0 + 6.0 * (0.5 + 0.5 * C.fbm(i * 0.08, 0.3, 4, seed=seed))
        hv += [(x, y, -20.0), (x, y, hgt)]
    for i in range(60):
        hf.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
    _mesh_obj("distant_hills", hv, hf, b, False, hills_m)

    # ---------- manger ----------
    mg_loc = Vector((0.55, 2.35, 0.0))
    stone_m = _pbr("rock_boulder_dry", scale=1.6, tint=(0.88, 0.82, 0.74), name="set_manger_stone", bump=1.3,
                   hsv=(0.5, 0.7, 1.0))
    if manger == "wood":
        wood = _pbr("weathered_planks", scale=1.6, tint=(0.75, 0.62, 0.5), name="set_manger_wood")
        trough_z = 0.62
        for sx in (-0.5, 0.5):
            for sgn in (-1, 1):
                leg = C.box("manger_leg", (0.07, 0.07, 0.8), (0, 0, 0), (sgn * 18, 0, 0), wood, 0.008, b.coll)
                b.add(leg)
                leg.location = mg_loc + Vector((sx, sgn * 0.12, 0.36))
        for sgn in (-1, 1):
            side = C.box("manger_side", (1.15, 0.035, 0.3), (0, 0, 0), (sgn * -22, 0, 0), wood, 0.006, b.coll)
            b.add(side)
            side.location = mg_loc + Vector((0, sgn * 0.2, trough_z))
        bot = C.box("manger_bottom", (1.1, 0.22, 0.03), (0, 0, 0), (0, 0, 0), wood, 0.005, b.coll)
        b.add(bot)
        bot.location = mg_loc + Vector((0, 0, trough_z - 0.13))
        straw_top = trough_z + 0.1
        mound_c = mg_loc + Vector((0, 0, trough_z - 0.08))
        mound_r = (0.55, 0.2, 0.18)
        b.info.objects["manger"] = bot
    else:
        tr = _stone_trough("manger", (1.1, 0.6, 0.48), b, stone_m, seed=seed)
        tr.location = mg_loc + Vector((0, 0, 0.12))
        tr.rotation_euler = (0, 0, math.radians(-6))
        _set_smooth_by_angle(tr, 35)
        for k, sx in enumerate((-0.36, 0.38)):
            _boulder("manger_support%d" % k, (0.36, 0.55, 0.2), mg_loc + Vector((sx, 0, -0.03)), b, stone_m,
                     seed=3 + k * 7, rot_z=rnd.uniform(-20, 20))
        b.info.objects["manger"] = tr
        straw_top = 0.12 + 0.46 + 0.04
        mound_c = mg_loc + Vector((0, 0, 0.12 + 0.46 - 0.13))
        mound_r = (0.5, 0.25, 0.2)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=28, v_segments=14, radius=1.0)
    for v in bm.verts:
        p = v.co
        v.co = Vector((p.x * mound_r[0], p.y * mound_r[1], max(p.z, -0.2) * mound_r[2] + 0.025 * noise.noise(p * 4)))
    mound = _bm_obj("manger_straw", bm, b, True, straw_material())
    mound.location = mound_c
    mound.rotation_euler = (0, 0, math.radians(-6))
    if straw:
        straw_scatter(mound, density=4500, seed=seed + 11, tilt=0.95)
        mound.visible_shadow = straw_shadows

    # ---------- Mary's seat, wall ledge, lamps ----------
    _boulder("mary_seat", (0.7, 0.55, 0.42), (-0.55, 1.95, -0.03), b, stone_m, seed=5.0, rot_z=20, rough=0.3,
             flat=0.7, subdiv=4)
    th_ledge = math.radians(-12)
    p, nrm = wall(th_ledge, 1.2)
    yaw_n = math.degrees(math.atan2(nrm.y, nrm.x))
    ledge_pos = p + nrm * 0.17
    _rock_block("lamp_ledge", (0.34, 0.5, 0.11), ledge_pos + Vector((0, 0, -0.055)) - nrm * 0.08, b, rock,
                noise_amp=0.025, seed=9.0, rot=(0, 0, yaw_n), bevel=0.03)
    lamp_l = oil_lamp(ledge_pos + nrm * 0.02, rot_z=yaw_n + 25, light=True, energy=55.0 * lamp_energy, seed=1, b=b,
                      name="lamp_ledge")
    b.info.lights["lamp_ledge"] = lamp_l[2]
    lamp_floor_pos = Vector((-0.02, 1.5, 0.0))
    if lamps >= 2:
        _boulder("lamp_stone", (0.3, 0.28, 0.2), lamp_floor_pos + Vector((0, 0, -0.01)), b, stone_m, seed=13.0)
        lamp_f = oil_lamp(lamp_floor_pos + Vector((0, 0, 0.185)), rot_z=115, light=True, energy=35.0 * lamp_energy,
                          seed=2, b=b, name="lamp_floor")
        b.info.lights["lamp_floor"] = lamp_f[2]

    # ---------- starlight through the doorway ----------
    star_dir = (out_dir * 1.0 + Vector((0, 0, 0.8))).normalized()
    spot_loc = door_c + star_dir * 5.0
    tgt = Vector((0.15, 2.0, 0.0))
    if starlight:
        sl = b.light("starlight", "SPOT", tuple(spot_loc), 3800.0 * starlight, temp=10000, target=tuple(tgt),
                     size=0.15, spot_size=17, spot_blend=0.5)
        df = b.light("door_fill", "AREA", tuple(door_c + Vector((0, 0, 1.0)) - out_dir * 0.4), 30.0 * starlight,
                     temp=11000, target=(0.3, 1.5, 0.5), size=1.2, shadow=False)
        df.data.volume_factor = 0.0
    bo = b.light("bounce", "AREA", (0.3, 1.9, 2.4), 30.0 * lamp_energy, temp=2400, target=(0.3, 1.9, 0), size=3.2,
                 shadow=False)
    bo.data.volume_factor = 0.0
    fb = b.light("floor_bounce", "AREA", (0.3, 2.2, 0.25), 22.0 * lamp_energy, temp=2300, target=(0.3, 2.2, 3.0),
                 size=4.0, shadow=False)
    fb.data.volume_factor = 0.0

    # ---------- atmosphere ----------
    if fog:
        f = C.fog_box(center=(cx, cy - 0.3, 1.4), size=(rx * 2 + 0.6, ry * 2 + 0.2, 2.9), density=0.022,
                      color=(0.85, 0.82, 0.78), anisotropy=0.3, noise_scale=1.2, name="cave_haze", coll=b.coll)
        b.add(f, "fog")
    if dust_motes:
        mid = (door_c + tgt) * 0.5
        dust(center=(mid.x, mid.y, 1.0), size=(2.0, 3.0, 2.0), count=500, radius=0.0022, seed=seed, b=b,
             name="cave_dust")

    # ---------- props ----------
    if props:
        for k, (th, sc_) in enumerate(((math.radians(-38), 0.62), (math.radians(-46), 0.46), (math.radians(196), 0.55))):
            p, n_ = wall(th, 0.3)
            jl = p + Vector((n_.x, n_.y, 0)).normalized() * 0.42
            clay_jar((jl.x, jl.y, 0.0), height=sc_, b=b, name="jar%d" % k, rot_z=rnd.random() * 360)
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=10, radius=1.0)
        for v in bm.verts:
            p = v.co
            v.co = Vector((p.x * 0.95, p.y * 0.65, max(p.z, -0.1) * 0.5 + 0.06 * noise.noise(p * 3)))
        hp, hn = wall(math.radians(52), 0.2)
        heap = _bm_obj("hay_heap", bm, b, True, straw_material())
        heap.location = Vector((hp.x, hp.y, 0)) + Vector((hn.x, hn.y, 0)).normalized() * 0.8
        heap.rotation_euler = (0, 0, math.atan2(hn.y, hn.x) + math.pi / 2)
        if straw:
            straw_scatter(heap, density=3000, seed=seed + 21, tilt=0.9)
            heap.visible_shadow = straw_shadows
        for k, (th, sz) in enumerate(((math.radians(160), (0.7, 0.5, 0.45)), (math.radians(235), (0.9, 0.6, 0.5)),
                                      (math.radians(20), (0.6, 0.6, 0.35)))):
            p, n_ = wall(th, 0.1)
            q = p + Vector((n_.x, n_.y, 0)).normalized() * 0.25
            _boulder("cave_rock%d" % k, sz, (q.x, q.y, -0.05), b, rock, seed=20 + k, rot_z=rnd.uniform(0, 360))
        wood = _pbr("weathered_planks", scale=2.0, tint=(0.6, 0.5, 0.42), name="set_staff_wood")
        sp_, sn_ = wall(door_th - 0.42, 0.0)
        staff = _lathe([(0.017, 0), (0.016, 1.55), (0.013, 1.62), (0.0, 1.63)], 10, "staff", b, wood)
        sn2 = Vector((sn_.x, sn_.y, 0)).normalized()
        staff.location = Vector((sp_.x, sp_.y, 0)) + sn2 * 0.3
        tilt_axis = Vector((0, 0, 1)).cross(sn2)
        staff.rotation_euler = Matrix.Rotation(math.radians(-11), 3, tilt_axis).to_euler()
        # rocks outside the doorway
        for k in range(5):
            q = door_c + out_dir * (1.5 + k * 0.9) + Vector((0, 0, 1)).cross(out_dir) * rnd.uniform(-2.5, 2.5)
            _boulder("out_rock%d" % k, (rnd.uniform(0.4, 1.2), rnd.uniform(0.4, 1.0), rnd.uniform(0.3, 0.8)),
                     (q.x, q.y, -0.25), b, rock, seed=40 + k, rot_z=rnd.uniform(0, 360))

    if world:
        night_world(strength=1.0, star_dir=star_dir, star_strength=80.0)

    # ---------- anchors / cameras ----------
    b.anchor("mary", (-0.55, 1.95, 0.38), yaw=-60)
    b.anchor("mary_head", (-0.55, 1.95, 1.12))
    b.anchor("manger", (mg_loc.x, mg_loc.y, straw_top))
    b.anchor("baby_manger", (mg_loc.x - 0.05, mg_loc.y, straw_top + 0.04))
    b.anchor("ox", (1.95, 3.75, 0.0), yaw=115)
    b.anchor("donkey", (-1.75, 3.6, 0.0), yaw=-115)
    b.anchor("doorway", tuple(door_c))
    b.anchor("lamp_ledge", tuple(ledge_pos + nrm * 0.02 + Vector((0, 0, 0.05))))
    b.anchor("lamp_floor", tuple(lamp_floor_pos + Vector((0, 0, 0.23))))
    b.anchor("star", tuple(door_c + star_dir * 200))
    R = b.M.to_3x3()
    b.info.extra.update({"door_dir": R @ out_dir, "star_dir": R @ star_dir, "wall_fn_local": wall})
    b.cam("wide", (1.55, -1.3, 1.5), (-0.25, 2.7, 0.8), 26)
    b.cam("mary_close", (0.6, 0.55, 1.2), (-0.55, 1.95, 1.0), 55)
    b.cam("manger_close", (1.1, 1.1, 1.2), (0.5, 2.35, 0.62), 45)
    b.cam("doorway_view", (1.5, 0.4, 1.3), tuple(door_c + Vector((0, 0, 1.1))), 32)
    b.cam("low_straw", (0.95, 0.15, 0.28), (-0.3, 2.5, 0.75), 30)
    return b.finish()


# ============================================================================================
# 2. GARDEN TOMB (s15 resurrection morning)
# ============================================================================================
def _grid_obj(name, nu, nv, fn, b, mat=None, smooth=True, keep=None):
    """Mesh from a parametric grid: fn(u, v) -> Vector with u, v in 0..1. keep(u, v) -> bool for faces."""
    verts = [fn(i / nu, j / nv) for j in range(nv + 1) for i in range(nu + 1)]
    faces = []
    for j in range(nv):
        for i in range(nu):
            if keep and not keep((i + 0.5) / nu, (j + 0.5) / nv):
                continue
            a = j * (nu + 1) + i
            faces.append((a, a + 1, a + nu + 2, a + nu + 1))
    o = _mesh_obj(name, verts, faces, b, smooth, mat)
    loose_cleanup(o)
    return o


def loose_cleanup(o):
    me = o.data
    bm = bmesh.new()
    bm.from_mesh(me)
    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context="VERTS")
        bm.to_mesh(me)
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    bm.free()


def _box_room(name, x0, x1, y0, y1, z0, z1, b, mat, open_face=None, cuts=8, rough=0.03, seed=0, bevel=0.0):
    """Inward-facing chiselled room (box) with noisy walls. open_face in ('-y', ...) is left open."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector((x1 - x0, y1 - y0, z1 - z0)), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)), verts=bm.verts)
    if open_face:
        ax = "xyz".index(open_face[1])
        sg = -1 if open_face[0] == "-" else 1
        bm.faces.ensure_lookup_table()
        rm = [f for f in bm.faces if f.normal[ax] * sg > 0.9]
        bmesh.ops.delete(bm, geom=rm, context="FACES_ONLY")
    if bevel:
        bmesh.ops.bevel(bm, geom=[e for e in bm.edges if len(e.link_faces) == 2], offset=bevel, segments=2,
                        affect="EDGES")
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=cuts, use_grid_fill=True)
    so = Vector((seed, seed * 0.5, 1.7))
    for v in bm.verts:
        p = v.co
        n = Vector((noise.noise(p * 1.5 + so), noise.noise(p * 1.5 + so + Vector((3, 0, 0))),
                    noise.noise(p * 1.5 + so + Vector((0, 3, 0)))))
        v.co = p + n * rough
    bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
    return _bm_obj(name, bm, b, True, mat)


def _cloth_sheet(name, length, width, b, mat, fold_amp=0.012, droop=0.05, seed=0, nu=72, nv=20, thickness=0.004,
                 hollow=0.0):
    """Linen sheet lying flat (origin centre, along X), soft wrinkles, edges drooping."""
    so = Vector((seed, 2.0, 0.3))

    def fn(u, v):
        x = (u - 0.5) * length
        y = (v - 0.5) * width
        z = fold_amp * (math.sin(u * 23 + 3 * noise.noise(Vector((u * 3, v * 3, 0)) + so)) * 0.5 +
                        noise.noise(Vector((u * 9, v * 4, 1.0)) + so))
        z += 0.6 * fold_amp * noise.noise(Vector((u * 25, v * 9, 2.0)) + so)
        e = min(u, 1 - u, v, 1 - v)
        z -= droop * max(0.0, 1 - e / 0.08) ** 2
        z -= hollow * math.sin(math.pi * v) * math.sin(math.pi * u) ** 0.3
        return Vector((x, y, z))
    o = _grid_obj(name, nu, nv, fn, b, mat)
    so_ = o.modifiers.new("thick", "SOLIDIFY")
    so_.thickness = thickness
    so_.offset = -1
    return o


def _folded_cloth(name, size, b, mat, layers=4, seed=0):
    """Neatly folded napkin/cloth: a stack of rounded layers with fold edges on one side."""
    sx, sy, sz = size
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector((sx, sy, sz)), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector((0, 0, sz / 2)), verts=bm.verts)
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=min(sx, sy, sz) * 0.35, segments=3, affect="EDGES", profile=0.7)
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=5, use_grid_fill=True)
    so = Vector((seed, 1.0, 2.0))
    for v in bm.verts:
        p = v.co
        z = p.z / sz
        # fold grooves along the stacked layers on the +x (folded) side
        groove = 0.006 * math.cos(z * layers * math.pi * 2) if p.x > sx * 0.2 else 0.0
        top = (0.004 * noise.noise(p * 30 + so)) if z > 0.9 else 0.0
        sag = -0.012 * (abs(p.x) / sx + abs(p.y) / sy) if z > 0.5 else 0.0
        v.co = p + Vector((groove, 0, top + sag)) + Vector((noise.noise(p * 12 + so), noise.noise(p * 12 + so + Vector((1, 1, 1)))
                                                           , 0)) * 0.004
    return _bm_obj(name, bm, b, True, mat)


def _grass_tufts(carrier, density=60, seed=0, height=0.25, color=(0.22, 0.25, 0.1), dry=0.5):
    """Sparse grass/weed tufts scattered on `carrier` (GN instances of a blade fan)."""
    name = "grass_tuft_src"
    src = bpy.data.objects.get(name)
    if src is None:
        verts, faces = [], []
        rnd = random.Random(3)
        for k in range(9):
            a = rnd.uniform(0, TAU)
            lean = rnd.uniform(0.15, 0.6)
            hgt = rnd.uniform(0.6, 1.0)
            w = 0.012
            base = len(verts)
            dx, dy = math.cos(a), math.sin(a)
            px, py = -dy, dx
            for s_ in range(5):
                t = s_ / 4
                cx_, cy_ = dx * lean * t * t * 0.4, dy * lean * t * t * 0.4
                ww = w * (1 - t) + 0.001
                verts.append((cx_ - px * ww, cy_ - py * ww, t * hgt))
                verts.append((cx_ + px * ww, cy_ + py * ww, t * hgt))
            for s_ in range(4):
                a0 = base + s_ * 2
                faces.append((a0, a0 + 1, a0 + 3, a0 + 2))
        me = bpy.data.meshes.new(name)
        me.from_pydata(verts, [], faces)
        me.update()
        gm = _cached(("grassmat", color, dry), lambda: _grass_mat(color, dry))
        me.materials.append(gm)
        src = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(src)
        src.hide_render = True
        src.hide_viewport = True
    ng, gi, go = _gn_group("grass_%s" % carrier.name)
    dist = ng.nodes.new("GeometryNodeDistributePointsOnFaces")
    dist.inputs["Density"].default_value = density
    dist.inputs["Seed"].default_value = seed
    ng.links.new(gi.outputs[0], dist.inputs["Mesh"])
    dn = ng.nodes.new("ShaderNodeTexNoise")       # clumping: only where noise is high
    dn.inputs["Scale"].default_value = 0.35
    pin = ng.nodes.new("GeometryNodeInputPosition")
    ng.links.new(pin.outputs[0], dn.inputs["Vector"])
    cmp = ng.nodes.new("FunctionNodeCompare")
    cmp.data_type = "FLOAT"
    cmp.operation = "GREATER_THAN"
    cmp.inputs[1].default_value = 0.52
    ng.links.new(dn.outputs["Fac"], cmp.inputs[0])
    ng.links.new(cmp.outputs[0], dist.inputs["Selection"])
    oi = ng.nodes.new("GeometryNodeObjectInfo")
    oi.inputs["Object"].default_value = src
    inst = ng.nodes.new("GeometryNodeInstanceOnPoints")
    ng.links.new(dist.outputs["Points"], inst.inputs["Points"])
    ng.links.new(oi.outputs["Geometry"], inst.inputs["Instance"])
    rot = _rand(ng, "FLOAT_VECTOR", (-0.15, -0.15, 0), (0.15, 0.15, TAU), seed + 1)
    ng.links.new(rot, inst.inputs["Rotation"])
    sc = _rand(ng, "FLOAT", height * 0.5, height * 1.3, seed + 2)
    ng.links.new(sc, inst.inputs["Scale"])
    join = ng.nodes.new("GeometryNodeJoinGeometry")
    ng.links.new(gi.outputs[0], join.inputs[0])
    ng.links.new(inst.outputs[0], join.inputs[0])
    ng.links.new(join.outputs[0], go.inputs[0])
    mod = carrier.modifiers.new("grass", "NODES")
    mod.node_group = ng
    return mod


def _grass_mat(color, dry):
    m = C.mat("set_grass", color, rough=0.6, sss=0.1, sss_radius=(0.3, 0.5, 0.1))
    nt = m.node_tree
    b = C.bsdf(m)
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*color, 1)
    ramp.color_ramp.elements[1].color = (0.45, 0.38, 0.2, 1)
    ramp.color_ramp.elements[0].position = 1.0 - dry
    nt.links.new(oi.outputs["Random"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    try:
        m.use_backface_culling = False
    except Exception:
        pass
    return m


def garden_tomb(ctx, loc=(0, 0, 0), rot_z=0.0, coll=None, stone_open=0.0, world=True, sun=True, sun_elevation=8.0,
                sun_azimuth=-40.0, fog=True, interior_fill=1.0, garden=True, dust_motes=True, seed=11, roll_dist=2.25):
    """Rock-cut garden tomb at dawn (s15). Local layout (metres, ground z=0, face at y~0 facing -Y):
        limestone cliff 16 m wide x ~5.5 m high with a dressed facade; low doorway (0.95 x 1.4 m)
        at x=0; round rolling stone (r=1.0 m, 0.32 m thick) in a carved groove in front of the face,
        rolls to +X by `roll_dist` m when stone_open=1; chamber behind the door (3.2 x 3.0 x 2.1 m,
        floor 0.3 m below the threshold) with a carved bench along the right (+X) wall; the folded
        linen grave cloths lie on the bench, the face-cloth (napkin) folded separately at the head end.
    stone_open: float 0..1, or a list of (frame, value) keys (animated roll). Use
        animate_tomb_stone(info, [(f, v), ...]) to add keys later.
    Anchors: entrance (threshold centre), door_center (centre of the opening), stone (stone centre,
    closed), bench (top centre), linen, napkin, chamber (chamber floor centre), angel_seat (on the
    stone when open), garden_path (front ground).
    Cameras: wide, approach, stone_low, interior, bench_close. extra['move_in'] = list of
    (loc, target) waypoints from outside to the bench (feed to a spline / lerp).
    Lights: sun (dawn), chamber_fill (warm bounce inside; keyed to the stone opening), sky_fill.
    """
    b = _B("GardenTomb", loc, rot_z, coll, seed)
    rnd = b.rnd
    face_m = _cached(("tomb_face",), lambda: _grime(
        C.mat_pbr("worn_rock_natural_01", scale=0.4, tint=(0.97, 0.93, 0.86), name="set_tomb_face", bump=1.5,
                  hue_sat_val=(0.5, 0.7, 1.08)), "z", 0.5, -0.2, (0.3, 0.27, 0.22), 0.45))
    cut_m = _cached(("tomb_cut",), lambda: _add_chisel(C.mat_pbr(
        "worn_rock_natural_01", scale=0.9, tint=(0.97, 0.94, 0.88), name="set_tomb_cut", bump=0.8,
        hue_sat_val=(0.5, 0.55, 1.1)), 0.3, 7.0))
    stone_m = _cached(("tomb_stone",), lambda: _add_chisel(C.mat_pbr(
        "rock_boulder_dry", scale=0.9, tint=(0.93, 0.9, 0.84), name="set_tomb_stone", bump=1.3,
        hue_sat_val=(0.5, 0.55, 1.05)), 0.25, 5.0))
    ground_m = _pbr("rocky_trail_02", scale=0.45, tint=(0.8, 0.76, 0.68), name="set_tomb_ground",
                    hsv=(0.5, 0.65, 1.0))
    DW, DH, PASS = 0.95, 1.4, 0.55          # door width, height, passage depth
    R, TH = 1.0, 0.32                         # stone radius, thickness
    GY = -0.27                                # stone centre-plane y
    GROOVE = 0.12                             # groove depth
    so = Vector((seed * 0.3, 1.1, 2.2))

    # ---------- cliff (face + top, one parametric sheet) ----------
    W = 18.0

    def cliff(u, v):
        x = (u - 0.5) * W
        # v: 0..0.62 the vertical face, 0.62..1 the top rolling back
        if v < 0.62:
            t = v / 0.62
            z = -0.4 + t * 5.9
            y = 0.0 + 0.25 * t * t
        else:
            t = (v - 0.62) / 0.38
            z = 5.5 + 1.4 * math.sin(t * math.pi / 2) + 0.6 * t
            y = 0.25 + 9.0 * t
        p = Vector((x, y, z))
        dressed = max(0.0, 1.0 - max(abs(x) / 1.9, abs(z - 1.1) / 1.8))    # flat chiselled facade
        rough = 1.0 - min(1.0, dressed * 2.5)
        q = p * 0.3 + so
        d = 0.95 * C.fbm(q.x, q.z + q.y * 0.5, 5, seed=so.z) + 0.18 * noise.noise(p * 1.1 + so)
        d += 0.35 * abs(noise.noise(Vector((x * 0.9, z * 0.18, 4.0)) + so))      # vertical fractures
        d += 0.05 * math.sin(z * 3.1 + 2.5 * noise.noise(p * 0.4 + so))     # bedding
        d += 0.03 * noise.noise(p * 4 + so)
        plan = 0.9 * C.fbm(x * 0.12 + 7, 0.5, 3, seed=so.x)                # face undulates in plan
        if v < 0.62:
            p.y += (-d + plan) * rough - 0.25 * (abs(x) / 9.0) ** 1.4 * rough
            p.y += 0.05 * dressed
        else:
            p.z += d * 0.9
            p.y += plan * 0.5
        return p

    def keep(u, v):
        p = cliff(u, v)
        return not (abs(p.x) < DW / 2 and -0.5 < p.z < DH and v < 0.62)
    face = _grid_obj("tomb_cliff", 180, 110, cliff, b, face_m, keep=keep)
    # snap doorway hole boundary onto a crisp (slightly irregular) rectangle
    me = face.data
    bm = bmesh.new()
    bm.from_mesh(me)
    for v in bm.verts:
        if v.is_boundary and abs(v.co.x) < DW and v.co.z < DH + 0.3 and v.co.y < 1.0 and v.co.z > -0.3:
            x, z = v.co.x, v.co.z
            dx = DW / 2 - abs(x)
            dz = DH - z
            if dz < dx and z > 0.3:
                v.co.z = DH + 0.01 * noise.noise(v.co * 9)
            else:
                v.co.x = math.copysign(DW / 2, x) + 0.01 * noise.noise(v.co * 9)
            v.co.y = 0.0
    bm.to_mesh(me)
    bm.free()
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    b.info.objects["cliff"] = face
    # passage (jambs, lintel, threshold) + chamber
    pv = []
    hw = DW / 2
    jam = [(-hw, 0.0, -0.32), (-hw, PASS, -0.32), (-hw, PASS, DH), (-hw, 0.0, DH)]
    jam2 = [(hw, 0.0, -0.32), (hw, 0.0, DH), (hw, PASS, DH), (hw, PASS, -0.32)]
    lin = [(-hw, 0.0, DH), (-hw, PASS, DH), (hw, PASS, DH), (hw, 0.0, DH)]
    thr = [(-hw, 0.0, 0.0), (hw, 0.0, 0.0), (hw, PASS, 0.0), (-hw, PASS, 0.0)]
    for k, quad in enumerate((jam, jam2, lin, thr)):
        o = _mesh_obj("tomb_passage%d" % k, quad, [(0, 1, 2, 3)], b, False, cut_m)
        if k == 3:
            o.data.flip_normals()
        if k == 2:
            o.data.flip_normals()
        if k == 0:
            o.data.flip_normals()
        if k == 1:
            o.data.flip_normals()
        o.modifiers.new("sub", "SUBSURF").levels = 0
    CX0, CX1, CY0, CY1, CZ0, CZ1 = -1.5, 1.7, PASS, PASS + 3.0, -0.32, 1.85
    room = _box_room("tomb_chamber", CX0, CX1, CY0, CY1, CZ0, CZ1, b, cut_m, cuts=10, rough=0.025, seed=seed)
    # front wall of the chamber has the doorway: cut faces inside the door rectangle
    me = room.data
    bm = bmesh.new()
    bm.from_mesh(me)
    rm = [f for f in bm.faces if abs(f.calc_center_median().y - CY0) < 0.08 and
          abs(f.calc_center_median().x) < hw and f.calc_center_median().z < DH]
    bmesh.ops.delete(bm, geom=rm, context="FACES")
    for v in bm.verts:
        if v.is_boundary and abs(v.co.y - CY0) < 0.1 and abs(v.co.x) < hw + 0.2 and v.co.z < DH + 0.2:
            if abs(v.co.z - DH) < hw - abs(v.co.x) and v.co.z > 0.3:
                v.co.z = DH
            else:
                v.co.x = math.copysign(hw, v.co.x)
            v.co.y = CY0
    bm.to_mesh(me)
    bm.free()
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    # threshold step down into the chamber
    step = C.box("tomb_step", (DW, 0.3, 0.32), (0, PASS + 0.15, -0.16), (0, 0, 0), cut_m, 0.01, b.coll)
    b.add(step)
    # bench along the right wall
    BX0, BX1, BY0, BY1, BZ = 0.75, CX1, PASS + 0.35, CY1, CZ0 + 0.6
    bench = _rock_block("tomb_bench", (BX1 - BX0 + 0.1, BY1 - BY0, BZ - CZ0), ((BX0 + BX1) / 2 + 0.05, (BY0 + BY1) / 2,
                        (CZ0 + BZ) / 2), b, cut_m, noise_amp=0.01, cuts=6, seed=3, bevel=0.02)
    b.info.objects["bench"] = bench
    # ---------- grave cloths ----------
    lin_m = linen_material()
    sheet = _cloth_sheet("grave_linen", 1.75, 0.5, b, lin_m, fold_amp=0.01, droop=0.03, seed=seed, hollow=0.012)
    sheet.location = ((BX0 + BX1) / 2 + 0.02, (BY0 + BY1) / 2 + 0.2, BZ + 0.035)
    sheet.rotation_euler = (0, 0, math.radians(90 + 2))
    # wrapping strips lying collapsed on the sheet
    for k in range(3):
        st = _cloth_sheet("linen_strip%d" % k, 0.55, 0.09, b, lin_m, fold_amp=0.006, droop=0.004, seed=seed + k, nu=30,
                          nv=4)
        st.location = (sheet.location.x + rnd.uniform(-0.08, 0.08), sheet.location.y - 0.5 + k * 0.4, BZ + 0.055)
        st.rotation_euler = (0, 0, math.radians(rnd.uniform(-25, 25)))
    nap = _folded_cloth("napkin", (0.28, 0.24, 0.05), b, lin_m, seed=seed)
    nap.location = ((BX0 + BX1) / 2 + 0.05, BY1 - 0.25, BZ + 0.005)
    nap.rotation_euler = (0, 0, math.radians(-8))
    b.info.objects["linen"] = sheet
    b.info.objects["napkin"] = nap

    # ---------- groove + rolling stone ----------
    gx0, gx1 = -1.45, roll_dist + 1.35
    gr = C.box("groove_floor", (gx1 - gx0, 0.5, 0.05), ((gx0 + gx1) / 2, GY, -GROOVE - 0.025), (0, 0, 0), cut_m, 0.0,
               b.coll)
    b.add(gr)
    lip = _rock_block("groove_lip", (gx1 - gx0 + 0.5, 0.35, 0.3), ((gx0 + gx1) / 2, GY - 0.43, 0.02), b, cut_m,
                      noise_amp=0.015, cuts=8, seed=5, bevel=0.03)
    stop = _rock_block("groove_stop", (0.35, 0.6, 0.45), (gx1 + 0.12, GY, 0.1), b, cut_m, noise_amp=0.02, seed=6,
                       bevel=0.04)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=72, radius1=R, radius2=R, depth=TH)
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "X"), verts=bm.verts)
    bmesh.ops.bevel(bm, geom=[e for e in bm.edges if e.calc_face_angle(0) > 0.5], offset=0.04, segments=3,
                    affect="EDGES")
    bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if e.calc_length() > 0.15], cuts=2, use_grid_fill=True)
    for v in bm.verts:
        p = v.co
        rr = math.hypot(p.x, p.z)
        d = 0.012 * noise.noise(p * 4 + so) + 0.006 * noise.noise(p * 12 + so)
        if rr > R * 0.9:
            d -= 0.02 * max(0.0, noise.noise(p * 3 + so + Vector((2, 2, 2))))
        v.co = p + (Vector((p.x, 0, p.z)).normalized() if rr > 1e-3 else Vector()) * d + Vector((0, d * 0.5, 0))
    stone = _bm_obj("rolling_stone", bm, b, True, stone_m)
    _set_smooth_by_angle(stone, 50)
    b.info.objects["stone"] = stone
    b.info.extra["stone_params"] = {"R": R, "y": GY, "z": R - GROOVE, "roll": roll_dist}

    # ---------- ground + garden ----------
    def gfn(u, v):
        x = (u - 0.5) * 40
        y = -22 + 22.5 * v
        z = 0.08 * C.fbm(x * 0.3, y * 0.3, 3, seed=seed) - 0.004 * max(0.0, -y - 6) ** 1.6
        if abs(x) < 3.5 and -1.2 < y < 0.5:
            z *= 0.2
        return Vector((x, y, z))

    gnd = _grid_obj("tomb_ground", 120, 70, gfn, b, ground_m)
    b.info.objects["ground"] = gnd
    if garden:
        _grass_tufts(gnd, density=9.0, seed=seed, height=0.3)
        for k in range(9):
            side = -1 if k % 2 else 1
            x = side * rnd.uniform(2.8, 8.5)
            y = rnd.uniform(-7, -0.6)
            _boulder("tomb_boulder%d" % k, (rnd.uniform(0.4, 1.4), rnd.uniform(0.4, 1.1), rnd.uniform(0.3, 0.9)),
                     (x, y, -0.1), b, face_m, seed=50 + k, rot_z=rnd.uniform(0, 360))
    # ---------- light ----------
    if sun:
        s_ = C.sun(elevation=sun_elevation, azimuth=sun_azimuth, energy=5.0, temp=3000, angle=1.0)
        b.add(s_)
        b.info.lights["sun"] = s_
    cf = b.light("chamber_fill", "AREA", (0.0, PASS + 0.4, 1.6), 12.0 * interior_fill, temp=3400, target=(1.0, 2.6, 0.0),
                 size=1.2, shadow=False)
    cf.data.volume_factor = 0.0
    if fog:
        f1 = C.fog_box(center=(0.1, (CY0 + CY1) / 2 - 0.25, 0.75), size=(CX1 - CX0 + 0.2, CY1 - CY0 + 0.9, 2.2),
                       density=0.05, color=(0.95, 0.9, 0.85), anisotropy=0.5, noise_scale=2.0, name="tomb_dust",
                       coll=b.coll)
        b.add(f1)
        f2 = C.fog_box(center=(0, -10, 3), size=(40, 22, 7), density=0.006, color=(0.95, 0.85, 0.75), anisotropy=0.4,
                       name="tomb_haze", coll=b.coll)
        b.add(f2)
    if dust_motes:
        dust(center=(0.2, PASS + 1.2, 0.8), size=(1.6, 2.6, 1.5), count=450, radius=0.0025, seed=seed, b=b,
             name="tomb_dust_motes")
    if world:
        sky_world(sun_elevation=sun_elevation, sun_rotation=180 + sun_azimuth, strength=0.3, light_strength=0.3,
                  air=1.6, dust=3.0, ozone=1.2)
    # ---------- animation ----------
    if isinstance(stone_open, (list, tuple)):
        animate_tomb_stone(b.info, stone_open, _local=True)
    else:
        _place_stone(b.info, float(stone_open))
    # ---------- anchors / cameras ----------
    b.anchor("entrance", (0, 0.1, 0.0), yaw=180)
    b.anchor("door_center", (0, 0.0, DH / 2))
    b.anchor("stone", (0, GY, R - GROOVE))
    b.anchor("stone_open", (roll_dist, GY, R - GROOVE))
    b.anchor("angel_seat", (roll_dist, GY, 2 * R - GROOVE + 0.02), yaw=0)
    b.anchor("bench", ((BX0 + BX1) / 2, (BY0 + BY1) / 2, BZ))
    b.anchor("linen", tuple(sheet.location))
    b.anchor("napkin", tuple(nap.location))
    b.anchor("chamber", ((CX0 + CX1) / 2 - 0.3, (CY0 + CY1) / 2, CZ0), yaw=90)
    b.anchor("garden_path", (0.0, -4.0, 0.0), yaw=0)
    b.cam("wide", (1.2, -10.0, 1.7), (0.6, 0.0, 1.5), 30)
    b.cam("approach", (0.25, -3.6, 1.15), (0.1, 1.0, 0.75), 32)
    b.cam("stone_low", (-2.6, -2.3, 0.35), (0.3, GY, 1.0), 28)
    b.cam("interior", (-0.6, PASS + 0.45, 1.05), (1.1, CY1 - 1.0, BZ), 24)
    b.cam("bench_close", (0.2, PASS + 1.0, 0.95), ((BX0 + BX1) / 2, CY1 - 0.7, BZ), 35)
    waypoints = [((0.3, -4.5, 1.3), (0.0, 1.0, 0.8)), ((0.1, -1.6, 0.95), (0.1, 1.5, 0.6)),
                 ((0.0, 0.2, 0.75), (0.6, 2.3, BZ)), ((-0.2, PASS + 0.6, 0.85), (1.1, CY1 - 0.9, BZ))]
    b.info.extra["move_in"] = [(b.w(l), b.w(t)) for l, t in waypoints]
    return b.finish()


def _place_stone(info, u):
    st = info.objects["stone"]
    p = info.extra["stone_params"]
    x = max(0.0, min(1.0, u)) * p["roll"]
    st.location = (x, p["y"], p["z"])
    st.rotation_euler = (0, x / p["R"], 0)


def animate_tomb_stone(info, pairs, interp="BEZIER", _local=False):
    """Key the rolling stone: pairs = [(frame, open_0_to_1), ...]. Location + rolling rotation."""
    st = info.objects["stone"]
    for f, u in pairs:
        _place_stone(info, u)
        st.keyframe_insert("location", frame=f)
        st.keyframe_insert("rotation_euler", frame=f)
    C._set_interp(st, "location", interp)
    C._set_interp(st, "rotation_euler", interp)
    fill = info.lights.get("chamber_fill")
    if fill is not None:
        e = fill.data.energy if not fill.data.animation_data else fill.data["base_e"]
        fill.data["base_e"] = e
        for f, u in pairs:
            fill.data.energy = e * (0.05 + 0.95 * max(0.0, min(1.0, u)) ** 0.7)
            fill.data.keyframe_insert("energy", frame=f)


# ============================================================================================
# 3. HOLY OF HOLIES (s03)
# ============================================================================================
CACHE_DIR = os.path.join(C.WORK, "cache", "sets")


class _Canvas:
    """Tiny numpy raster for procedural relief / embroidery maps (origin bottom-left, 0..1 coords)."""

    def __init__(self, w, h):
        import numpy as np
        self.np = np
        self.w, self.h = w, h
        self.h_ = np.zeros((h, w), np.float32)
        ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
        self.X = (xs + 0.5) / w
        self.Y = (ys + 0.5) / h
        self.asp = w / h

    def _bbox(self, x0, y0, x1, y1):
        np = self.np
        i0 = max(0, int(x0 * self.w) - 2)
        i1 = min(self.w, int(x1 * self.w) + 3)
        j0 = max(0, int(y0 * self.h) - 2)
        j1 = min(self.h, int(y1 * self.h) + 3)
        return slice(j0, j1), slice(i0, i1)

    def ellipse(self, cx, cy, rx, ry, hgt=1.0, rot=0.0, target=None, mode="max", soft=0.5):
        np = self.np
        t = self.h_ if target is None else target
        r = max(rx, ry) * 1.05
        sj, si = self._bbox(cx - r, cy - r * self.asp, cx + r, cy + r * self.asp)
        X = self.X[sj, si] - cx
        Y = (self.Y[sj, si] - cy) / self.asp
        c, s = math.cos(rot), math.sin(rot)
        u = (X * c + Y * s) / rx
        v = (-X * s + Y * c) / ry
        d = np.clip(1 - (u * u + v * v), 0, 1)
        val = hgt * d ** soft
        if mode == "max":
            t[sj, si] = np.maximum(t[sj, si], val)
        else:
            t[sj, si] += val
        return t

    def stroke(self, pts, w0, w1, hgt=1.0, target=None, soft=0.5):
        """Tapered stroke along a polyline pts [(x, y)] (y in 0..1 of height). Widths in x units."""
        np = self.np
        t = self.h_ if target is None else target
        n = len(pts)
        for k in range(n - 1):
            ax, ay = pts[k]
            bx, by = pts[k + 1]
            wa = w0 + (w1 - w0) * k / (n - 1)
            wb = w0 + (w1 - w0) * (k + 1) / (n - 1)
            wm = max(wa, wb)
            sj, si = self._bbox(min(ax, bx) - wm, min(ay, by) - wm * self.asp, max(ax, bx) + wm,
                                max(ay, by) + wm * self.asp)
            X = self.X[sj, si]
            Y = self.Y[sj, si]
            dx, dy = bx - ax, (by - ay) / self.asp
            L2 = dx * dx + dy * dy + 1e-12
            tt = np.clip(((X - ax) * dx + (Y - ay) / self.asp * dy) / L2, 0, 1)
            px = X - (ax + tt * dx)
            py = (Y - ay) / self.asp - tt * dy
            dist = np.sqrt(px * px + py * py)
            w = wa + (wb - wa) * tt
            val = hgt * np.clip(1 - (dist / w) ** 2, 0, 1) ** soft
            t[sj, si] = np.maximum(t[sj, si], val)
        return t

    def blur(self, arr, r=2):
        np = self.np
        out = arr.copy()
        for _ in range(r):
            out = (out + np.roll(out, 1, 0) + np.roll(out, -1, 0) + np.roll(out, 1, 1) + np.roll(out, -1, 1)) / 5.0
        return out


def _curve(p0, p1, p2, n=12):
    out = []
    for i in range(n + 1):
        t = i / n
        a = (1 - t) ** 2
        b_ = 2 * (1 - t) * t
        c = t * t
        out.append((a * p0[0] + b_ * p1[0] + c * p2[0], a * p0[1] + b_ * p1[1] + c * p2[1]))
    return out


def _motif_cherub(cv, cx, cy, s, target=None, hgt=1.0, parts=None):
    """Frontal cherub, robed, with two great wings outspread and raised (relief / embroidery).
    s = wing span-ish size in x units. parts: optional dict of separate masks {'wings','body','head'}."""
    A = cv.asp
    tw = parts["wings"] if parts else target
    tb = parts["body"] if parts else target
    th = parts["head"] if parts else target
    for side in (-1, 1):
        root = (cx + side * 0.05 * s, cy + 0.14 * s * A)
        ctrl = (cx + side * 0.26 * s, cy + 0.5 * s * A)
        tip = (cx + side * 0.6 * s, cy + 0.42 * s * A)
        edge = _curve(root, ctrl, tip, 18)
        n = 14
        for k in range(n, 0, -1):                 # feathers hang from the leading edge
            u = k / n
            px, py = edge[min(len(edge) - 1, int(u * (len(edge) - 1)))]
            ln = s * (0.1 + 0.3 * u ** 1.3)
            dx = side * (0.1 + 0.8 * u ** 1.5)
            dy = -(1.0 - 0.45 * u)
            nn = math.hypot(dx, dy)
            dx, dy = dx / nn, dy / nn
            end = (px + dx * ln, py + dy * ln * A)
            mid = (px + dx * ln * 0.55 + side * 0.012 * s, py + dy * ln * 0.55 * A)
            cv.stroke(_curve((px, py), mid, end, 6), 0.026 * s, 0.01 * s, hgt * (0.65 + 0.15 * (k % 2)), tw)
        for k in range(10):                      # covert row
            u = (k + 0.5) / 10 * 0.85
            px, py = edge[int(u * (len(edge) - 1))]
            cv.ellipse(px + side * 0.01 * s, py - 0.035 * s * A, 0.035 * s, 0.02 * s, hgt * 0.85,
                       rot=side * (0.3 + 0.9 * u), target=tw)
        cv.stroke(edge, 0.032 * s, 0.012 * s, hgt * 0.95, tw)
    # robe (widening to the hem), arms folded, head
    cv.stroke([(cx, cy + 0.14 * s * A), (cx, cy - 0.12 * s * A), (cx, cy - 0.34 * s * A)], 0.042 * s, 0.078 * s, hgt, tb)
    cv.stroke([(cx - 0.05 * s, cy + 0.06 * s * A), (cx + 0.05 * s, cy + 0.02 * s * A)], 0.018 * s, 0.018 * s,
              hgt * 1.05, tb)
    cv.ellipse(cx, cy + 0.21 * s * A, 0.045 * s, 0.055 * s, hgt, target=th)
    return target


def _motif_palm(cv, cx, cy, s, target=None, hgt=1.0):
    A = cv.asp
    t = target
    pts = [(cx + 0.015 * s * math.sin(k * 0.7), cy - 0.45 * s * A + k * 0.0875 * s * A) for k in range(9)]
    cv.stroke(pts, 0.05 * s, 0.035 * s, hgt * 0.75, t)
    for k in range(16):       # trunk leaf-scars (cross-hatched)
        y = cy - 0.44 * s * A + k * 0.046 * s * A
        cv.ellipse(cx + 0.012 * s * math.sin(k * 0.35), y, 0.045 * s, 0.012 * s, hgt * 0.82, rot=0.35 * (1 if k % 2 else -1),
                   target=t)
    top = (cx + 0.015 * s * math.sin(5.6), cy + 0.33 * s * A)
    for k in range(11):
        a = math.radians(-15 + 21 * k)
        ln = 0.34 * s * (0.8 + 0.2 * math.sin(a))
        ex = top[0] + math.cos(a) * ln
        ey = top[1] + (math.sin(a) * 0.45 - 0.35) * ln * A
        mx = top[0] + math.cos(a) * ln * 0.5
        my = top[1] + (math.sin(a) * 0.9 + 0.25) * ln * A * 0.55
        fr = _curve(top, (mx, my), (ex, ey), 12)
        cv.stroke(fr, 0.014 * s, 0.004 * s, hgt * 0.78, t)
        for q in range(2, 12, 2):                 # leaflets
            px, py = fr[q]
            qx, qy = fr[q + 1]
            dx, dy = qx - px, (qy - py) / A
            nn = math.hypot(dx, dy) + 1e-9
            for sg in (-1, 1):
                lx = px + (-dy / nn * sg * 0.6 + dx / nn * 0.5) * 0.05 * s
                ly = py + ((dx / nn * sg * 0.6 + dy / nn * 0.5) * 0.05 * s - 0.02 * s) * A
                cv.stroke([(px, py), (lx, ly)], 0.008 * s, 0.003 * s, hgt * 0.7, t)
    cv.ellipse(top[0], top[1] - 0.02 * s * A, 0.04 * s, 0.03 * s, hgt * 0.85, target=t)   # date cluster
    return t


def _motif_flower(cv, cx, cy, r, target=None, hgt=1.0, petals=8):
    t = target
    for k in range(petals):
        a = TAU * k / petals
        cv.ellipse(cx + math.cos(a) * r * 0.55, cy + math.sin(a) * r * 0.55 * cv.asp, r * 0.42, r * 0.18, hgt * 0.8,
                   rot=a, target=t)
    cv.ellipse(cx, cy, r * 0.3, r * 0.3, hgt, target=t)
    return t


def _save_gray(arr, path):
    import numpy as np
    h, w = arr.shape
    img = bpy.data.images.new(os.path.basename(path), w, h, alpha=False, float_buffer=False)
    rgba = np.ones((h, w, 4), np.float32)
    a = np.clip(arr, 0, 1)
    rgba[..., 0] = a
    rgba[..., 1] = a
    rgba[..., 2] = a
    img.pixels.foreach_set(rgba.ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


def _save_rgb(rgb, path):
    import numpy as np
    h, w, _ = rgb.shape
    img = bpy.data.images.new(os.path.basename(path), w, h, alpha=False)
    rgba = np.ones((h, w, 4), np.float32)
    rgba[..., :3] = np.clip(rgb, 0, 1)
    img.pixels.foreach_set(rgba.ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


def temple_relief_map(force=False):
    """Height map (1024^2 tile = one 2.25 m panel pair): framed panels with a palm tree and a
    cherub, open-flower band below (1 Kings 6:29). Cached in WORK/cache/sets."""
    path = os.path.join(CACHE_DIR, "temple_relief_v4.png")
    if os.path.exists(path) and not force:
        return path
    os.makedirs(CACHE_DIR, exist_ok=True)
    import numpy as np
    cv = _Canvas(1024, 1024)
    H = cv.h_
    # panel frames (two panels side by side) + flower band at the bottom
    X, Y = cv.X, cv.Y
    for x0 in (0.0, 0.5):
        u = (X - x0) / 0.5
        d = np.minimum(np.minimum(u, 1 - u) * 0.5, np.minimum(Y - 0.2, 1 - Y))
        frame = np.clip(1 - np.abs(d - 0.022) / 0.014, 0, 1) ** 0.5
        H[:] = np.maximum(H, frame * ((Y > 0.19) & (u > 0) & (u < 1)))
    band = (Y < 0.2)
    H[band] = np.maximum(H[band], 0.15)
    H[:] = np.maximum(H, np.clip(1 - np.abs(Y - 0.195) / 0.008, 0, 1) * 0.9)
    H[:] = np.maximum(H, np.clip(1 - np.abs(Y - 0.012) / 0.01, 0, 1) * 0.9)
    for k in range(4):
        _motif_flower(cv, 0.125 + 0.25 * k, 0.1, 0.075, hgt=0.85)
    for k in range(4):
        _motif_flower(cv, 0.25 * k, 0.1, 0.035, hgt=0.6, petals=6)
    _motif_palm(cv, 0.25, 0.58, 0.6, hgt=0.85)
    _motif_cherub(cv, 0.75, 0.56, 0.62, hgt=0.9)
    H[:] = cv.blur(H, 3)
    _save_gray(H, path)
    return path


def veil_texture(force=False):
    """Embroidered veil (one half, 1024 x 2048): blue ground with purple/scarlet bands and a lattice
    of gold-and-scarlet cherubim (Exodus 26:31). Returns (color_path, height_path)."""
    cpath = os.path.join(CACHE_DIR, "veil_color_v4.png")
    hpath = os.path.join(CACHE_DIR, "veil_height_v4.png")
    if os.path.exists(cpath) and os.path.exists(hpath) and not force:
        return cpath, hpath
    os.makedirs(CACHE_DIR, exist_ok=True)
    import numpy as np
    W, Hh = 1024, 2048
    cv = _Canvas(W, Hh)
    X, Y = cv.X, cv.Y
    rng = np.random.default_rng(3)
    blue = np.array([0.035, 0.07, 0.30], np.float32)
    purple = np.array([0.22, 0.05, 0.28], np.float32)
    scarlet = np.array([0.55, 0.04, 0.05], np.float32)
    gold = np.array([0.85, 0.6, 0.2], np.float32)
    linen = np.array([0.8, 0.75, 0.62], np.float32)
    rgb = np.empty((Hh, W, 3), np.float32)
    rgb[:] = blue
    # woven mottling
    nz = rng.random((Hh // 8, W // 8)).astype(np.float32)
    nz = np.kron(nz, np.ones((8, 8), np.float32))
    nz = cv.blur(nz, 4)
    rgb *= (0.85 + 0.3 * nz)[..., None]
    hmap = np.zeros((Hh, W), np.float32)

    def band(mask, col):
        rgb[mask] = col

    # vertical bands at the outer edge (x ~ 0) and horizontal bands top/bottom
    for (a, b_, col) in ((0.0, 0.035, scarlet), (0.035, 0.06, gold), (0.06, 0.11, purple), (0.11, 0.12, gold)):
        band((X >= a) & (X < b_), col)
        band((Y >= a / 2) & (Y < b_ / 2), col)
        band((Y <= 1 - a / 2) & (Y > 1 - b_ / 2), col)
    # lozenge lattice of gold thread with rosettes at the crossings
    cell = 0.38
    u = (X - 0.13) / cell
    v = (Y - 0.065) / (cell * cv.asp)
    d1 = np.abs(((u + v) % 1.0) - 0.5)
    d2 = np.abs(((u - v) % 1.0) - 0.5)
    inner = (X > 0.125) & (Y > 0.062) & (Y < 0.938)
    lat = (np.maximum(d1, d2) > 0.488) & inner
    lat2 = (np.maximum(d1, d2) > 0.474) & (np.maximum(d1, d2) < 0.479) & inner
    rgb[lat2] = scarlet
    rgb[lat] = gold
    hmap[lat] = 0.55
    wing_m = np.zeros((Hh, W), np.float32)
    body_m = np.zeros((Hh, W), np.float32)
    head_m = np.zeros((Hh, W), np.float32)
    parts = {"wings": wing_m, "body": body_m, "head": head_m}
    for r in range(-2, 12):
        vv = r * 0.5
        for i in range(-1, 5):
            uu = i + (0.5 if r % 2 == 0 else 0.0)
            cx = 0.13 + uu * cell
            cy = 0.065 + vv * cell * cv.asp
            if not (0.2 < cx < 1.1 and 0.1 < cy < 0.9):
                continue
            _motif_cherub(cv, cx, cy - 0.012, cell * 0.62, parts=parts)
            cv.ellipse(cx, cy + 0.5 * cell * cv.asp, 0.022, 0.022 * 1.0, 1.0, target=head_m)   # rosette at crossing
    wm = wing_m > 0.04
    rgb[wm] = gold[None, :] * (0.55 + 0.6 * wing_m[wm])[..., None]
    bm_ = body_m > 0.04
    rgb[bm_] = scarlet[None, :] * (0.8 + 0.4 * body_m[bm_])[..., None]
    hm = head_m > 0.04
    rgb[hm] = linen * (0.8 + 0.3 * head_m[hm])[..., None]
    allm = np.maximum(np.maximum(wing_m, body_m), head_m)
    edge = (allm > 0.0) & (allm < 0.06)
    rgb[edge] = purple * 0.7
    hmap = np.maximum(hmap, allm * 0.9)
    # fine thread noise
    tn = rng.random((Hh, W)).astype(np.float32)
    rgb *= (0.93 + 0.12 * tn)[..., None]
    rgb = rgb[::-1].copy()       # numpy row 0 = top in our drawing convention? keep bottom-left origin
    hmap = cv.blur(hmap, 2)[::-1].copy()
    _save_rgb(rgb[::-1], cpath)
    _save_gray(hmap[::-1], hpath)
    return cpath, hpath


def _uv_box_mapping(o, scale=(1.0, 1.0), axis="auto"):
    """Planar UVs for wall-like meshes: u along the dominant horizontal axis, v = z (metres*scale)."""
    me = o.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uv = me.uv_layers.active.data
    for poly in me.polygons:
        n = poly.normal
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            if abs(n.z) > 0.7:
                u_, w_ = v.x, v.y
            elif abs(n.x) > abs(n.y):
                u_, w_ = v.y, v.z
            else:
                u_, w_ = v.x, v.z
            uv[li].uv = (u_ * scale[0], w_ * scale[1])


def _veil_material():
    def mk():
        cpath, hpath = veil_texture()
        m = bpy.data.materials.new("set_veil")
        m.use_nodes = True
        nt = m.node_tree
        b = nt.nodes["Principled BSDF"]
        tc = nt.nodes.new("ShaderNodeTexCoord")
        ci = nt.nodes.new("ShaderNodeTexImage")
        ci.image = bpy.data.images.load(cpath, check_existing=True)
        nt.links.new(tc.outputs["UV"], ci.inputs["Vector"])
        hi = nt.nodes.new("ShaderNodeTexImage")
        hi.image = bpy.data.images.load(hpath, check_existing=True)
        hi.image.colorspace_settings.name = "Non-Color"
        nt.links.new(tc.outputs["UV"], hi.inputs["Vector"])
        nt.links.new(ci.outputs["Color"], b.inputs["Base Color"])
        b.inputs["Roughness"].default_value = 0.75
        b.inputs["Sheen Weight"].default_value = 0.7
        b.inputs["Sheen Roughness"].default_value = 0.4
        b.inputs["Specular IOR Level"].default_value = 0.35
        # weave micro-bump + embroidery relief
        wv = nt.nodes.new("ShaderNodeTexWave")
        wv.inputs["Scale"].default_value = 900
        wv.wave_profile = "SIN"
        nt.links.new(tc.outputs["UV"], wv.inputs["Vector"])
        wv2 = nt.nodes.new("ShaderNodeTexWave")
        wv2.inputs["Scale"].default_value = 900
        wv2.bands_direction = "Y"
        nt.links.new(tc.outputs["UV"], wv2.inputs["Vector"])
        mx = nt.nodes.new("ShaderNodeMath")
        mx.operation = "MULTIPLY"
        nt.links.new(wv.outputs["Fac"], mx.inputs[0])
        nt.links.new(wv2.outputs["Fac"], mx.inputs[1])
        bp = nt.nodes.new("ShaderNodeBump")
        bp.inputs["Strength"].default_value = 0.25
        bp.inputs["Distance"].default_value = 0.002
        nt.links.new(mx.outputs[0], bp.inputs["Height"])
        bp2 = nt.nodes.new("ShaderNodeBump")
        bp2.inputs["Strength"].default_value = 0.6
        bp2.inputs["Distance"].default_value = 0.01
        nt.links.new(hi.outputs["Color"], bp2.inputs["Height"])
        nt.links.new(bp.outputs["Normal"], bp2.inputs["Normal"])
        nt.links.new(bp2.outputs["Normal"], b.inputs["Normal"])
        # gold-thread embroidery is metallic + shinier: drive from embroidery height
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = 0.3
        mr.inputs["From Max"].default_value = 0.6
        mr.inputs["To Max"].default_value = 0.65
        nt.links.new(hi.outputs["Color"], mr.inputs["Value"])
        nt.links.new(mr.outputs["Result"], b.inputs["Metallic"])
        # light glows through the weave from behind
        tl = nt.nodes.new("ShaderNodeBsdfTranslucent")
        br = nt.nodes.new("ShaderNodeMixRGB")
        br.blend_type = "MULTIPLY"
        br.inputs[0].default_value = 1.0
        br.inputs[2].default_value = (1.6, 1.2, 1.0, 1)
        nt.links.new(ci.outputs["Color"], br.inputs[1])
        nt.links.new(br.outputs[0], tl.inputs["Color"])
        ms = nt.nodes.new("ShaderNodeMixShader")
        ms.inputs[0].default_value = 0.22
        nt.links.new(b.outputs[0], ms.inputs[1])
        nt.links.new(tl.outputs[0], ms.inputs[2])
        nt.links.new(ms.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
        return m
    return _cached(("veil",), mk)


def _veil_half(name, side, width, height, b, mat, top_z, nu=46, nv=64, pleat=0.07, seed=0):
    """One half of the veil (side=-1 left, +1 right). Hangs from y=0 between x=0 and side*width.
    Shape key 'open' gathers it towards the outer edge (drawn aside)."""
    verts, faces, opened = [], [], []
    so = Vector((seed, side * 3.0, 0.5))
    for j in range(nv + 1):
        v = j / nv
        z = top_z - v * height
        for i in range(nu + 1):
            u = i / nu                               # 0 = centre seam, 1 = outer edge
            x = side * u * width
            ph = u * width / 0.38 * TAU
            amp = pleat * (0.75 + 0.35 * noise.noise(Vector((u * 4, v * 2, 0)) + so))
            y = amp * math.sin(ph + 0.6 * noise.noise(Vector((u * 2, v * 1.5, 1)) + so))
            y += 0.04 * v * noise.noise(Vector((u * 1.5, 5, 0)) + so)
            verts.append(Vector((x, y, z)))
            # opened: inner part pulled towards the outer edge, most at ~1/3 height from the floor
            g = math.sin(math.pi * min(1.0, max(0.0, (1 - v) * 1.15))) ** 0.6     # 0 at the rod, 1 near floor
            g = 0.25 + 0.75 * g
            pull = (1 - u) * 0.82 * g
            uo = u + pull
            xo = side * min(1.0, uo) * width
            pho = ph
            ampo = amp * (1.0 + 2.2 * pull)
            yo = ampo * math.sin(pho + 0.6 * noise.noise(Vector((u * 2, v * 1.5, 1)) + so)) - 0.25 * pull * (1 - v)
            zo = z + 0.12 * pull * (1 - v)
            opened.append(Vector((xo, yo, zo)))
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i
            faces.append((a, a + 1, a + nu + 2, a + nu + 1) if side > 0 else (a, a + nu + 1, a + nu + 2, a + 1))
    o = _mesh_obj(name, verts, faces, b, True, mat)
    me = o.data
    uvl = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index
            j, i = divmod(vi, nu + 1)
            uvl.data[li].uv = (1.0 - i / nu if side < 0 else i / nu, 1.0 - j / nv) if False else (
                (1.0 - i / nu), 1.0 - j / nv)
    o.shape_key_add(name="Basis")
    sk = o.shape_key_add(name="open")
    for k, p in enumerate(opened):
        sk.data[k].co = p
    sol = o.modifiers.new("thick", "SOLIDIFY")
    sol.thickness = 0.012
    return o, sk


def animate_veil(info, pairs, interp="BEZIER"):
    """Key the veil opening: pairs = [(frame, 0..1), ...] (0 closed, 1 drawn fully aside)."""
    for key in ("veil_L", "veil_R"):
        o = info.objects.get(key)
        if not o:
            continue
        kb = o.data.shape_keys.key_blocks["open"]
        for f, v in pairs:
            kb.value = v
            kb.keyframe_insert("value", frame=f)
        C._set_interp(o.data.shape_keys, "value", interp)


def _metaball_mesh(name, elems, b, mat, resolution=0.012, threshold=0.6, radius_scale=1.65):
    """Build a metaball from elements [(type, co, radius, (size_x,size_y,size_z), rot_euler_rad, stiffness)]
    and convert it to a smooth mesh."""
    mb = bpy.data.metaballs.new(name + "_mb")
    mb.resolution = resolution
    mb.render_resolution = resolution
    mb.threshold = threshold
    for typ, co, rad, sz, rot, stiff in elems:
        e = mb.elements.new(type=typ)
        e.co = co
        e.radius = rad * radius_scale      # the iso-surface sits at ~0.58 r for threshold 0.6
        e.stiffness = stiff
        if typ in ("ELLIPSOID", "CAPSULE", "CUBE"):
            e.size_x, e.size_y, e.size_z = sz
        e.rotation = Euler(rot).to_quaternion()
    mo = bpy.data.objects.new(name + "_mbobj", mb)
    bpy.context.scene.collection.objects.link(mo)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(mo.evaluated_get(dg))
    bpy.data.objects.remove(mo)
    bpy.data.metaballs.remove(mb)
    me.name = name
    o = bpy.data.objects.new(name, me)
    b.add(o)
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    if mat:
        me.materials.append(mat)
    return o


def _capsule_between(p0, p1, r, stiff=2.0):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    rot = d.to_track_quat("X", "Z").to_euler()
    return ("CAPSULE", (p0 + p1) / 2, r, (d.length / 2, 1, 1), tuple(rot), stiff)


def _cherub_body(name, b, mat):
    """Kneeling (sitting back on the heels), robed cherub facing +X, torso upright, head bowed towards
    the mercy seat, forearms raised forward in adoration (metaball sculpt -> smooth mesh).
    Origin = floor under the figure. Height ~0.66 m at scale 1."""
    E = []
    ell = lambda co, r, sz, rot=(0, 0, 0), st=2.0: E.append(("ELLIPSOID", co, r, sz, rot, st))
    # robe pooled on the ground + folded legs (seiza) under it
    ell((-0.03, 0, 0.055), 0.2, (1.0, 0.82, 0.34))
    ell((0.04, 0, 0.12), 0.14, (1.05, 0.78, 0.55))           # thighs/lap
    ell((-0.12, 0, 0.09), 0.1, (0.8, 0.95, 0.6))            # heels / seat
    ell((0.13, 0, 0.06), 0.09, (0.7, 0.95, 0.4))            # robe over the knees
    # upright torso
    ell((-0.02, 0, 0.26), 0.11, (0.8, 0.95, 1.0))           # waist
    ell((-0.015, 0, 0.37), 0.11, (0.78, 1.05, 0.85))        # chest
    ell((-0.03, 0, 0.43), 0.095, (0.62, 1.35, 0.5))         # shoulders
    E.append(_capsule_between((-0.01, 0, 0.47), (0.02, 0, 0.53), 0.03))   # neck
    ell((0.05, 0, 0.585), 0.066, (1.02, 0.86, 1.12), (0, math.radians(28), 0))   # head, bowed
    ell((0.1, 0, 0.575), 0.018, (1.0, 0.6, 1.5), (0, math.radians(28), 0))      # nose / face plane
    ell((0.07, 0, 0.545), 0.03, (0.9, 1.1, 0.7), (0, math.radians(28), 0))      # chin / jaw
    ell((0.02, 0, 0.605), 0.07, (1.05, 0.98, 0.95), (0, math.radians(28), 0))   # hair mass
    ell((-0.035, 0, 0.53), 0.06, (0.8, 1.15, 1.25))         # hair falling to the shoulders
    for s_ in (-1, 1):
        sh = (-0.02, s_ * 0.115, 0.43)
        el = (0.055, s_ * 0.125, 0.33)
        hd = (0.165, s_ * 0.05, 0.44)
        E.append(_capsule_between(sh, el, 0.034))
        E.append(_capsule_between(el, hd, 0.03))
        ell(((el[0] + hd[0]) / 2, el[1] * 0.9, (el[2] + hd[2]) / 2 - 0.015), 0.045, (1.2, 0.8, 0.7))   # sleeve
        ell(hd, 0.028, (1.2, 0.5, 1.15), (0, math.radians(-35), 0))                                  # open hand
    o = _metaball_mesh(name, E, b, mat, resolution=0.009)
    d = o.modifiers.new("robe_folds", "DISPLACE")
    tex = bpy.data.textures.get("robe_folds_tex") or bpy.data.textures.new("robe_folds_tex", "WOOD")
    tex.wood_type = "BANDNOISE"
    tex.noise_scale = 0.08
    tex.turbulence = 4.0
    d.texture = tex
    d.strength = 0.004
    d.texture_coords = "LOCAL"
    return o


def _feather_mesh(length, width, curl=0.15, nl=7):
    """Feather blade along +X (root at 0), width along Y, normal +Z; returns (verts, faces)."""
    verts, faces = [], []
    for i in range(nl + 1):
        t = i / nl
        w = width * (math.sin(math.pi * min(1.0, 0.15 + t * 0.95)) ** 0.5) * (1 - 0.35 * t)
        z = curl * length * t * t
        verts.append((t * length, -w * 0.5, z - 0.08 * w))
        verts.append((t * length, 0.0, z + 0.06 * w))        # rachis ridge
        verts.append((t * length, w * 0.55, z - 0.1 * w))
    for i in range(nl):
        a = i * 3
        faces.append((a, a + 3, a + 4, a + 1))
        faces.append((a + 1, a + 4, a + 5, a + 2))
    return verts, faces


def _wing(name, b, mat, spine, side, span_scale=1.0, chord=(0.15, 0.25, 0.23, 0.11), rows=3, center=(0.05, 0, 0.55)):
    """Feathered wing along the leading edge `spine` (points root..tip). A lofted membrane hangs from
    the leading edge (in the wing plane, 'down' = away from the arch) with overlapping rows of
    feathers shingled on its outer face; the last row overhangs as the serrated trailing edge."""
    pts = [Vector(p) for p in spine]

    def spline(t):
        n = len(pts) - 1
        x = max(0.0, min(1.0, t)) * n
        i = min(n - 1, int(x))
        f = x - i
        p0 = pts[max(0, i - 1)]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[min(n, i + 2)]
        return 0.5 * ((2 * p1) + (-p0 + p2) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f * f +
                      (-p0 + 3 * p1 - 3 * p2 + p3) * f * f * f)

    def chord_at(t):
        c = chord
        x = t * (len(c) - 1)
        i = min(len(c) - 2, int(x))
        f = x - i
        return (c[i] * (1 - f) + c[i + 1] * f) * span_scale

    side_axis = Vector((0, side, 0))

    def frame(t):
        p = spline(t)
        tan = (spline(t + 0.01) - spline(t - 0.01)).normalized()
        down = Vector((-tan.z, 0.0, tan.x)).normalized()  # in the wing plane, perpendicular to the edge
        if (Vector(center) - p).dot(down) < 0:            # feathers hang towards the arch interior
            down = -down
        # near the tip the feathers sweep towards the tip
        out = side_axis
        return p, tan, down, out

    verts, faces = [], []
    # membrane (thin lofted surface, slightly bowed outward)
    NU, NV = 28, 6
    base = len(verts)
    for i in range(NU + 1):
        t = i / NU
        p, tan, down, out = frame(t)
        c = chord_at(t)
        for j in range(NV + 1):
            v = j / NV
            sweep = (down * (1 - 0.6 * t ** 2) + tan * (0.6 * t ** 2)).normalized()
            verts.append(p + sweep * c * v + out * (0.012 * math.sin(math.pi * v)))
    for i in range(NU):
        for j in range(NV):
            a = base + i * (NV + 1) + j
            f = (a, a + NV + 1, a + NV + 2, a + 1)
            faces.append(f if side > 0 else f[::-1])

    def add_feather(t, v, length, width, lift):
        p, tan, down, out = frame(t)
        c = chord_at(t)
        sweep = (down * (1 - 0.6 * t ** 2) + tan * (0.6 * t ** 2)).normalized()
        q = p + sweep * c * v
        d = (sweep * 0.85 + tan * 0.15 * (1 - t) + tan * 0.35 * t).normalized()
        nrm = out
        side_v = nrm.cross(d).normalized()
        fv, ff = _feather_mesh(length, width, curl=-0.05, nl=9)
        b0 = len(verts)
        for (x, y, z) in fv:
            verts.append(q + d * x + side_v * y + nrm * (z * side + lift))
        for f in ff:
            faces.append(tuple(b0 + k for k in (f if side > 0 else f[::-1])))

    # rows from the trailing edge (drawn first, innermost) to the leading-edge coverts (outermost)
    for r in range(rows):
        v = 1.0 - (r + 0.5) / rows * 0.95           # position of the feather root along the chord
        n = int(22 + 6 * r)
        for k in range(n):
            t = (k + 0.5 * (r % 2) + 0.25) / n
            if t > 1.0:
                continue
            c = chord_at(t)
            ln = c * (0.75 if r > 0 else 0.8) + 0.02 * span_scale
            if r == 0:
                ln *= 1.25 + 0.6 * t                 # long flight feathers, longest at the tip
            wd = c / rows * 0.95 + 0.008 * span_scale
            add_feather(t, max(0.0, v - 0.25 / rows), ln, wd, lift=0.004 + 0.006 * r)
    # leading-edge roll (wing 'arm')
    ring, nseg = 8, 28
    for i in range(nseg + 1):
        t = i / nseg
        p, tan, down, out = frame(t)
        r_ = 0.02 * span_scale * (1 - 0.6 * t) + 0.005
        b0 = len(verts)
        for k in range(ring):
            a = TAU * k / ring
            verts.append(p + (down * math.cos(a) + out * math.sin(a)) * r_ + down * r_ * 0.4 + out * 0.006)
        if i:
            for k in range(ring):
                k2 = (k + 1) % ring
                faces.append((b0 - ring + k, b0 - ring + k2, b0 + k2, b0 + k))
    o = _mesh_obj(name, verts, faces, b, True, mat)
    return o


def _ark(b, mat_box, mat_lid, center, yaw=0.0, seed=0):
    """Ark of the Covenant (2.5 x 1.5 x 1.5 cubits), crown moulding, feet, 4 rings, 2 poles,
    mercy-seat lid and two kneeling cherubim with arched wings. Returns (root_empty, lid_top_z)."""
    root = bpy.data.objects.new("Ark", None)
    b.add(root)
    root.location = center
    root.rotation_euler = (0, 0, math.radians(yaw))
    L, W, Hb = 1.15, 0.69, 0.66
    parts = []

    def add(o):
        o.parent = root
        parts.append(o)
        return o
    body = add(C.box("ark_body", (L, W, Hb - 0.1), (0, 0, 0.05 + (Hb - 0.1) / 2 + 0.04), mat_=mat_box, bevel=0.008,
                     coll=b.coll))
    # inset side panels (raised frames)
    for sy in (-1, 1):
        add(C.box("ark_panel", (L - 0.14, 0.012, Hb - 0.26), (0, sy * (W / 2 + 0.004), 0.05 + Hb / 2 + 0.0),
                  mat_=mat_box, bevel=0.004, coll=b.coll))
    for sx in (-1, 1):
        add(C.box("ark_panel_end", (0.012, W - 0.14, Hb - 0.26), (sx * (L / 2 + 0.004), 0, 0.05 + Hb / 2),
                  mat_=mat_box, bevel=0.004, coll=b.coll))
    # crown moulding (zer) and base plinth
    add(C.box("ark_crown", (L + 0.05, W + 0.05, 0.045), (0, 0, Hb + 0.035), mat_=mat_box, bevel=0.012, coll=b.coll))
    add(C.box("ark_crown2", (L + 0.03, W + 0.03, 0.03), (0, 0, Hb - 0.005), mat_=mat_box, bevel=0.01, coll=b.coll))
    add(C.box("ark_plinth", (L + 0.03, W + 0.03, 0.05), (0, 0, 0.075), mat_=mat_box, bevel=0.01, coll=b.coll))
    for sx in (-1, 1):
        for sy in (-1, 1):
            f = add(_lathe([(0.045, 0.0), (0.05, 0.015), (0.035, 0.05), (0.04, 0.06)], 16, "ark_foot", b, mat_box,
                           cap_top=True))
            f.location = (sx * (L / 2 - 0.06), sy * (W / 2 - 0.06), 0.0)
    # rings (on the long sides near the feet) + poles
    for sx in (-1, 1):
        for sy in (-1, 1):
            tor = _torus("ark_ring", 0.05, 0.011, b, mat_box)
            add(tor)
            tor.location = (sx * (L / 2 - 0.2), sy * (W / 2 + 0.02), 0.2)
            tor.rotation_euler = (0, math.pi / 2, 0)
    for sy in (-1, 1):
        pole = add(_lathe([(0.0, -1.2), (0.026, -1.2), (0.03, -1.18), (0.03, 1.18), (0.026, 1.2), (0.0, 1.2)], 16,
                          "ark_pole", b, mat_box))
        pole.rotation_euler = (0, math.pi / 2, 0)
        pole.location = (0, sy * (W / 2 + 0.02), 0.2)
    # mercy seat
    lid_z = Hb + 0.06
    add(C.box("mercy_seat", (L + 0.01, W + 0.01, 0.05), (0, 0, lid_z + 0.025), mat_=mat_lid, bevel=0.01, coll=b.coll))
    top = lid_z + 0.05
    # cherubim (one at each end, facing the centre)
    for sx in (-1, 1):
        ch = _cherub_body("cherub_%s" % ("L" if sx < 0 else "R"), b, mat_lid)
        add(ch)
        ch.location = (sx * (L / 2 - 0.2), 0, top)
        ch.rotation_euler = (0, 0, 0 if sx < 0 else math.pi)
        ch.scale = (1.3, 1.3, 1.3)
        for sy in (-1, 1):
            # spine in cherub-local coords (facing +X): from the shoulder blade up, then arching forward
            spine = [(-0.07, sy * 0.08, 0.44), (-0.15, sy * 0.17, 0.66), (-0.1, sy * 0.24, 0.88),
                     (0.05, sy * 0.25, 0.99), (0.2, sy * 0.21, 0.95), (0.285, sy * 0.17, 0.86)]
            wg = _wing("cherub_wing", b, mat_lid, spine, side=sy, center=(0.05, sy * 0.2, 0.6))
            wg.parent = ch
    b.info.objects["ark"] = root
    return root, top


def _torus(name, R, r, b, mat, seg=24, rseg=10):
    verts, faces = [], []
    for i in range(seg):
        a = TAU * i / seg
        for j in range(rseg):
            c = TAU * j / rseg
            verts.append(((R + r * math.cos(c)) * math.cos(a), (R + r * math.cos(c)) * math.sin(a), r * math.sin(c)))
    for i in range(seg):
        for j in range(rseg):
            i2, j2 = (i + 1) % seg, (j + 1) % rseg
            faces.append((i * rseg + j, i2 * rseg + j, i2 * rseg + j2, i * rseg + j2))
    return _mesh_obj(name, verts, faces, b, True, mat)


def _smoke_material(name, density=0.3, color=(0.9, 0.88, 0.85), scale=1.6, rise=0.25, anisotropy=0.4,
                    shape="box", falloff=0.5, emission=None, emission_strength=0.0):
    """Animated wispy volume (4D noise with keyed W + rising offset). shape 'box' fills the
    object; 'column' fades radially from the object's Z axis; 'sphere' fades from the centre."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    v = nt.nodes.new("ShaderNodeVolumePrincipled")
    v.inputs["Color"].default_value = (*color, 1)
    v.inputs["Anisotropy"].default_value = anisotropy
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.name = "smoke_map"
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.name = "smoke_noise"
    nz.noise_dimensions = "4D"
    nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = 4
    nz.inputs["Roughness"].default_value = 0.6
    nz.inputs["Distortion"].default_value = 0.6
    nt.links.new(mp.outputs[0], nz.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.45
    mr.inputs["From Max"].default_value = 0.8
    mr.inputs["To Max"].default_value = density
    nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
    dens = mr.outputs["Result"]
    if shape in ("column", "sphere"):
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(tc.outputs["Generated"], sep.inputs[0])
        cmb = nt.nodes.new("ShaderNodeCombineXYZ")
        sub = nt.nodes.new("ShaderNodeVectorMath")
        sub.operation = "SUBTRACT"
        nt.links.new(tc.outputs["Generated"], sub.inputs[0])
        sub.inputs[1].default_value = (0.5, 0.5, 0.5)
        if shape == "column":
            sep2 = nt.nodes.new("ShaderNodeSeparateXYZ")
            nt.links.new(sub.outputs[0], sep2.inputs[0])
            nt.links.new(sep2.outputs["X"], cmb.inputs["X"])
            nt.links.new(sep2.outputs["Y"], cmb.inputs["Y"])
            ln = nt.nodes.new("ShaderNodeVectorMath")
            ln.operation = "LENGTH"
            nt.links.new(cmb.outputs[0], ln.inputs[0])
        else:
            ln = nt.nodes.new("ShaderNodeVectorMath")
            ln.operation = "LENGTH"
            nt.links.new(sub.outputs[0], ln.inputs[0])
        fr = nt.nodes.new("ShaderNodeMapRange")
        fr.inputs["From Min"].default_value = 0.5
        fr.inputs["From Max"].default_value = 0.5 * (1 - falloff)
        nt.links.new(ln.outputs["Value"], fr.inputs["Value"])
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        nt.links.new(dens, mul.inputs[0])
        nt.links.new(fr.outputs["Result"], mul.inputs[1])
        dens = mul.outputs[0]
        if shape == "column":      # thin out towards the top
            tz = nt.nodes.new("ShaderNodeMapRange")
            tz.inputs["From Min"].default_value = 0.0
            tz.inputs["From Max"].default_value = 1.0
            tz.inputs["To Min"].default_value = 1.0
            tz.inputs["To Max"].default_value = 0.35
            nt.links.new(sep.outputs["Z"], tz.inputs["Value"])
            mul2 = nt.nodes.new("ShaderNodeMath")
            mul2.operation = "MULTIPLY"
            nt.links.new(dens, mul2.inputs[0])
            nt.links.new(tz.outputs["Result"], mul2.inputs[1])
            dens = mul2.outputs[0]
    nt.links.new(dens, v.inputs["Density"])
    if emission:
        v.inputs["Emission Color"].default_value = (*emission, 1)
        em = nt.nodes.new("ShaderNodeMath")
        em.operation = "MULTIPLY"
        em.inputs[1].default_value = emission_strength
        nt.links.new(dens, em.inputs[0])
        nt.links.new(em.outputs[0], v.inputs["Emission Strength"])
    nt.links.new(v.outputs[0], nt.nodes["Material Output"].inputs["Volume"])
    # animate: W evolves, field rises
    sc = bpy.context.scene
    f1 = max(2, sc.frame_end)
    w = nz.inputs["W"]
    w.default_value = 0.0
    w.keyframe_insert("default_value", frame=1)
    w.default_value = (f1 - 1) / 24.0 * 0.12
    w.keyframe_insert("default_value", frame=f1)
    loc = mp.inputs["Location"]
    loc.default_value = (0, 0, 0)
    loc.keyframe_insert("default_value", frame=1)
    loc.default_value = (0, 0, -(f1 - 1) / 24.0 * rise)
    loc.keyframe_insert("default_value", frame=f1)
    ad = nt.animation_data
    if ad and ad.action:
        for fc in C._fcurves(ad.action):
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
    return m


def _glory_material(name="set_glory", strength=40.0, color=(1.0, 0.9, 0.7)):
    """Soft spherical emissive volume (shekinah glory)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    v = nt.nodes.new("ShaderNodeVolumePrincipled")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sub = nt.nodes.new("ShaderNodeVectorMath")
    sub.operation = "SUBTRACT"
    nt.links.new(tc.outputs["Generated"], sub.inputs[0])
    sub.inputs[1].default_value = (0.5, 0.5, 0.5)
    ln = nt.nodes.new("ShaderNodeVectorMath")
    ln.operation = "LENGTH"
    nt.links.new(sub.outputs[0], ln.inputs[0])
    fr = nt.nodes.new("ShaderNodeMapRange")
    fr.inputs["From Min"].default_value = 0.5
    fr.inputs["From Max"].default_value = 0.0
    nt.links.new(ln.outputs["Value"], fr.inputs["Value"])
    pw = nt.nodes.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = 4.0
    nt.links.new(fr.outputs["Result"], pw.inputs[0])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.noise_dimensions = "4D"
    nz.inputs["Scale"].default_value = 3.0
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = 0.6
    mr.inputs["To Max"].default_value = 1.3
    nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    nt.links.new(pw.outputs[0], mul.inputs[0])
    nt.links.new(mr.outputs["Result"], mul.inputs[1])
    st = nt.nodes.new("ShaderNodeMath")
    st.name = "glory_strength"
    st.operation = "MULTIPLY"
    st.inputs[1].default_value = strength
    nt.links.new(mul.outputs[0], st.inputs[0])
    v.inputs["Emission Color"].default_value = (*color, 1)
    nt.links.new(st.outputs[0], v.inputs["Emission Strength"])
    dn = nt.nodes.new("ShaderNodeMath")
    dn.operation = "MULTIPLY"
    dn.inputs[1].default_value = 0.12
    nt.links.new(mul.outputs[0], dn.inputs[0])
    nt.links.new(dn.outputs[0], v.inputs["Density"])
    v.inputs["Color"].default_value = (1, 0.95, 0.85, 1)
    nt.links.new(v.outputs[0], nt.nodes["Material Output"].inputs["Volume"])
    sc = bpy.context.scene
    f1 = max(2, sc.frame_end)
    w = nz.inputs["W"]
    w.default_value = 0.0
    w.keyframe_insert("default_value", frame=1)
    w.default_value = (f1 - 1) / 24.0 * 0.5
    w.keyframe_insert("default_value", frame=f1)
    return m


def holy_of_holies(ctx, loc=(0, 0, 0), rot_z=0.0, coll=None, veil_open=0.0, glory=1.0, smoke=True, shafts=True,
                   holy_place=True, room=9.0, probe=True, seed=3):
    """Temple inner sanctuary (s03). Local layout (metres):
        Veil (two halves, blue/purple/scarlet with embroidered gold cherubim) hangs across y=0,
        x -4.5..4.5, up to z 8.6. The Holy of Holies is the cube y 0..9 behind it with gold-overlaid
        cedar walls carved with cherubim, palm trees and open flowers. The Ark stands at (0, 4.5, 0),
        long axis along X, two kneeling golden cherubim on the mercy seat, wings arched towards each
        other; the glory (radiant emissive volume + point light) hovers between them. In front of
        the veil (y<0) a stretch of the Holy Place with the golden altar of incense.
    veil_open: float 0..1 or [(frame, value), ...]  (also animate_veil(info, pairs) later).
    glory: brightness multiplier (key info.lights['glory'].data.energy / use set_glory()).
    Anchors: ark, mercy_seat (top centre of the lid), glory (centre of the light), veil (centre of
    the seam at eye height), altar (incense altar top), high_priest (standing spot in front of ark).
    Cameras: approach, through, ark_wide, cherubim, glory_rise. extra['path'] = waypoint list
    from the Holy Place through the veil, rising into the glory.
    """
    b = _B("HolyOfHolies", loc, rot_z, coll, seed)
    S_ = room
    relief = temple_relief_map()
    gold_wall = gold_material("set_gold_wall", color=(0.95, 0.68, 0.3), rough=0.33, relief=relief,
                              relief_scale=(1 / 2.25, 1 / 2.25), relief_strength=0.9, patina=0.5, hammered=0.08)
    gold_ark = gold_material("set_gold_ark", color=(1.0, 0.74, 0.34), rough=0.2, hammered=0.12)
    gold_lid = gold_material("set_gold_lid", color=(1.0, 0.78, 0.4), rough=0.16, hammered=0.06)
    gold_floor = gold_material("set_gold_floor", color=(0.78, 0.55, 0.24), rough=0.34, hammered=0.0)
    cedar = _pbr("weathered_planks", scale=0.8, tint=(0.4, 0.25, 0.15), name="set_cedar")

    def wall(name, verts, mat, uv_scale=(1.0, 1.0)):
        o = _mesh_obj(name, verts, [(0, 1, 2, 3)], b, False, mat)
        _uv_box_mapping(o, uv_scale)
        return o
    hw = S_ / 2
    y0, y1 = 0.0, S_
    wall("hoh_back", [(-hw, y1, 0), (hw, y1, 0), (hw, y1, S_), (-hw, y1, S_)], gold_wall)
    wall("hoh_left", [(-hw, y0, 0), (-hw, y1, 0), (-hw, y1, S_), (-hw, y0, S_)], gold_wall)
    wall("hoh_right", [(hw, y1, 0), (hw, y0, 0), (hw, y0, S_), (hw, y1, S_)], gold_wall)
    wall("hoh_floor", [(-hw, y0, 0), (hw, y0, 0), (hw, y1, 0), (-hw, y1, 0)], gold_floor)
    wall("hoh_ceiling", [(-hw, y0, S_), (-hw, y1, S_), (hw, y1, S_), (hw, y0, S_)], gold_wall)
    # pilasters on the walls (gold-overlaid posts every 2.25 m)
    for k in range(5):
        x = -hw + 2.25 * k
        if -hw < x < hw:
            p = C.box("pilaster", (0.22, 0.12, S_), (x, y1 - 0.06, S_ / 2), mat_=gold_ark, bevel=0.02, coll=b.coll)
            b.add(p)
        y = 2.25 * k
        if 0 < y < S_:
            for sx in (-1, 1):
                p = C.box("pilaster", (0.12, 0.22, S_), (sx * (hw - 0.06), y, S_ / 2), mat_=gold_ark, bevel=0.02,
                          coll=b.coll)
                b.add(p)
    # lintel wall above the veil
    top_z = S_ - 0.4
    lw = wall("hoh_lintel", [(-hw, 0.02, top_z - 0.15), (hw, 0.02, top_z - 0.15), (hw, 0.02, S_), (-hw, 0.02, S_)],
              gold_wall)
    rod = _lathe([(0.0, -hw), (0.05, -hw), (0.05, hw), (0.0, hw)], 16, "veil_rod", b, gold_ark)
    rod.rotation_euler = (0, math.pi / 2, 0)
    rod.location = (0, 0.0, top_z)
    # ---------- the veil ----------
    vm = _veil_material()
    vl, skl = _veil_half("veil_L", -1, hw, top_z, b, vm, top_z, seed=seed)
    vr, skr = _veil_half("veil_R", 1, hw, top_z, b, vm, top_z, seed=seed + 1)
    b.info.objects["veil_L"] = vl
    b.info.objects["veil_R"] = vr
    # ---------- Holy Place in front ----------
    if holy_place:
        hp0 = -7.0
        wall("hp_left", [(-hw, hp0, 0), (-hw, 0, 0), (-hw, 0, S_), (-hw, hp0, S_)], gold_wall)
        wall("hp_right", [(hw, 0, 0), (hw, hp0, 0), (hw, hp0, S_), (hw, 0, S_)], gold_wall)
        wall("hp_floor", [(-hw, hp0, 0), (hw, hp0, 0), (hw, 0, 0), (-hw, 0, 0)], gold_floor)
        wall("hp_ceiling", [(-hw, hp0, S_), (-hw, 0, S_), (hw, 0, S_), (hw, hp0, S_)], gold_wall)
        wall("hp_front", [(hw, hp0, 0), (-hw, hp0, 0), (-hw, hp0, S_), (hw, hp0, S_)], gold_wall)
        # altar of incense: gold box with horns + crown
        alt = C.box("incense_altar", (0.46, 0.46, 0.85), (0, -1.6, 0.425), mat_=gold_ark, bevel=0.01, coll=b.coll)
        b.add(alt)
        cr = C.box("incense_altar_crown", (0.52, 0.52, 0.05), (0, -1.6, 0.86), mat_=gold_ark, bevel=0.01, coll=b.coll)
        b.add(cr)
        for sx in (-1, 1):
            for sy in (-1, 1):
                h_ = _lathe([(0.03, 0), (0.025, 0.06), (0.0, 0.1)], 10, "altar_horn", b, gold_ark)
                h_.location = (sx * 0.2, -1.6 + sy * 0.2, 0.88)
        coal = C.box("incense_coals", (0.3, 0.3, 0.02), (0, -1.6, 0.9),
                     mat_=C.mat_emission("set_coals", (1.0, 0.35, 0.08), 6.0), coll=b.coll)
        b.add(coal)
        ml = b.light("menorah", "POINT", (-3.2, -3.5, 1.9), 350.0, temp=2300, size=0.3)
        vf = b.light("veil_front", "AREA", (1.5, -4.0, 3.5), 120.0, temp=4500, target=(0, 0, 3.0), size=3.0,
                     shadow=False)
        vf.data.volume_factor = 0.0
        ml.data.volume_factor = 1.0
        al = b.light("altar_glow", "POINT", (0, -1.6, 1.0), 25.0, temp=1800, size=0.15)
        b.anchor("altar", (0, -1.6, 0.9))
    # ---------- Ark, cherubim, glory ----------
    ark_c = Vector((0, S_ / 2, 0))
    ark, lid_top = _ark(b, gold_ark, gold_lid, ark_c)
    gz = lid_top + 0.45
    gl = bpy.data.objects.new("glory_volume", None)
    gbox = C.box("glory_volume", (1.1, 1.1, 1.1), (ark_c.x, ark_c.y, gz), coll=b.coll)
    b.add(gbox)
    gbox.data.materials.append(_glory_material(strength=22.0 * glory))
    gbox.visible_shadow = False
    glight = b.light("glory", "POINT", (ark_c.x, ark_c.y, gz), 450.0 * glory, temp=6200, size=0.2)
    glight.data.volume_factor = 1.0
    gfill = b.light("glory_fill", "AREA", (ark_c.x, ark_c.y, S_ - 0.5), 90.0 * glory, temp=5600,
                    target=(ark_c.x, ark_c.y, 0), size=6.0, shadow=False)
    gfill.data.volume_factor = 0.0
    rfill = b.light("room_fill", "AREA", (0, 0.4, 4.5), 50.0, temp=5000, target=(0, S_, 3.0), size=7.0, shadow=False)
    rfill.data.volume_factor = 0.0
    if shafts:
        for k, sx in enumerate((-1, 1)):
            sp = b.light("shaft%d" % k, "SPOT", (sx * 3.6, S_ - 1.0, S_ - 0.3), 1500.0, temp=5800,
                         target=(sx * 0.35, S_ / 2 + 0.1, 1.0), size=0.15, spot_size=8, spot_blend=0.35)
    # ---------- incense smoke ----------
    if smoke:
        fz = C.box("hoh_incense", (S_ - 0.2, S_ - 0.2, S_ * 0.85), (0, S_ / 2, S_ * 0.85 / 2), coll=b.coll)
        b.add(fz)
        fz.data.materials.append(_smoke_material("set_incense", density=0.045, color=(0.95, 0.92, 0.86), scale=0.9,
                                                 rise=0.12, anisotropy=0.55))
        col = C.box("hoh_incense_column", (1.2, 1.2, 4.0), (0.0, S_ / 2 - 1.1, 2.0), coll=b.coll)
        b.add(col)
        col.data.materials.append(_smoke_material("set_incense_col", density=0.5, color=(0.95, 0.92, 0.88), scale=2.2,
                                                  rise=0.35, shape="column", falloff=0.8, anisotropy=0.5))
        censer = _lathe([(0.0, 0.0), (0.09, 0.0), (0.12, 0.06), (0.13, 0.1), (0.0, 0.1)], 20, "censer", b, gold_ark)
        censer.location = (0.0, S_ / 2 - 1.1, 0.0)
        if holy_place:
            hc = C.box("hp_incense", (S_ - 0.2, 6.8, S_ * 0.8), (0, -3.5, S_ * 0.4), coll=b.coll)
            b.add(hc)
            hc.data.materials.append(_smoke_material("set_incense_hp", density=0.05, color=(0.95, 0.92, 0.86),
                                                     scale=0.8, rise=0.1, anisotropy=0.5))
            ac = C.box("altar_smoke", (0.8, 0.8, 3.0), (0, -1.6, 2.4), coll=b.coll)
            b.add(ac)
            ac.data.materials.append(_smoke_material("set_altar_smoke", density=0.6, color=(0.95, 0.93, 0.9),
                                                     scale=2.5, rise=0.4, shape="column", falloff=0.85))
    if probe:
        for k, (py, rad) in enumerate(((S_ / 2, S_ * 0.75), (-3.5, 4.5))):
            if py < 0 and not holy_place:
                continue
            pd = bpy.data.lightprobes.new("hoh_probe%d" % k, "SPHERE")
            pd.influence_distance = rad
            po = bpy.data.objects.new("hoh_probe%d" % k, pd)
            b.add(po)
            po.location = (0, py, 2.0)
    world_bg = C.world_color((0.03, 0.018, 0.008), 1.0)
    # ---------- veil animation ----------
    if isinstance(veil_open, (list, tuple)):
        animate_veil(b.info, veil_open)
    else:
        skl.value = skr.value = float(veil_open)
    # ---------- anchors / cameras ----------
    b.anchor("ark", tuple(ark_c))
    b.anchor("mercy_seat", (ark_c.x, ark_c.y, lid_top))
    b.anchor("glory", (ark_c.x, ark_c.y, gz))
    b.anchor("veil", (0, 0, 1.7))
    b.anchor("high_priest", (0, ark_c.y - 1.6, 0), yaw=0)
    b.cam("approach", (0.0, -5.5, 1.75), (0, 4.5, 1.6), 30)
    b.cam("through", (0.0, -0.6, 1.65), (0, 4.5, 1.2), 28)
    b.cam("ark_wide", (2.4, 1.4, 1.9), (0, ark_c.y, 1.0), 28)
    b.cam("cherubim", (0.0, ark_c.y - 2.2, 1.3), (0, ark_c.y, 1.15), 40)
    b.cam("glory_rise", (0.0, ark_c.y - 1.3, 2.4), (0, ark_c.y, gz), 30)
    wps = [((0, -5.5, 1.75), (0, 4.5, 1.6)), ((0, -1.2, 1.7), (0, 4.5, 1.4)), ((0, 1.5, 1.6), (0, ark_c.y, 1.2)),
           ((0, ark_c.y - 1.6, 1.9), (0, ark_c.y, gz)), ((0, ark_c.y - 0.6, gz + 0.2), (0, ark_c.y + 2.0, gz + 0.3))]
    b.info.extra["path"] = [(b.w(l), b.w(t)) for l, t in wps]
    return b.finish()


def set_glory(info, pairs):
    """Key the glory brightness multiplier: pairs = [(frame, mult), ...] (1 = default)."""
    gl = info.lights.get("glory")
    base = gl.data.get("base_e", gl.data.energy)
    gl.data["base_e"] = base
    for f, v in pairs:
        gl.data.energy = base * v
        gl.data.keyframe_insert("energy", frame=f)
    core = info.coll.objects.get("glory_core") if hasattr(info.coll.objects, "get") else None


# ============================================================================================
# 4a. COURTYARD ASSEMBLY (s17a)
# ============================================================================================
def _column(name, b, mat, loc, height=5.5, radius=0.32):
    """Classical column: base, slightly tapered fluted-look shaft, capital. Origin at the base."""
    prof = [(0.0, 0.0), (radius * 1.45, 0.0), (radius * 1.45, 0.12), (radius * 1.3, 0.16), (radius * 1.25, 0.22),
            (radius * 1.08, 0.28), (radius, 0.34), (radius * 0.88, height - 0.5), (radius * 0.95, height - 0.42),
            (radius * 1.0, height - 0.36), (radius * 1.25, height - 0.25), (radius * 1.5, height - 0.18),
            (radius * 1.5, height), (0.0, height)]
    o = _lathe(prof, 24, name, b, mat)
    o.location = loc
    return o


def courtyard_assembly(ctx, loc=(0, 0, 0), rot_z=0.0, coll=None, lamps=420, world=True, crowd_rows=14, crowd_cols=18,
                       glow=1.0, haze=True, seed=21, columns=True, sun_elevation=-2.5, sun_azimuth=200.0):
    """Stone courtyard at dusk with hundreds of small oil-lamp flames (s17a). Local layout:
        flagstone court x -13..13, y -8..24; portico of columns on a stepped platform at the back
        (y ~ 19..23); ashlar side walls with a parapet; lamps (instanced, emissive, flickering, no
        lights) line the steps, parapets, wall niches and the crowd perimeter. The crowd area is
        x -7.5..7.5, y 0..14 (people stand facing +Y towards the portico).
    Anchors: crowd_center, portico (top of the steps centre), steps_front, leader (spot on the
    steps facing the crowd). extra['crowd_spots'] = [(Vector world, yaw_deg), ...] jittered grid
    (crowd_rows x crowd_cols); extra['lamp_points'] = list of world lamp positions;
    extra['add_lamps'](points) adds more instanced lamps (points in set-local coords).
    Cameras: wide, glide_start, glide_end, faces, lamps_close. extra['glide'] = waypoints.
    Lights: sky (dusk), wall_glow_L/R/B (warm areas), crowd_glow (upward warm area at hand height),
    crowd_key (warm front), moon (cool rim).
    """
    b = _B("CourtyardAssembly", loc, rot_z, coll, seed)
    rnd = b.rnd
    floor_m = _pbr("stone_floor", scale=0.35, tint=(0.82, 0.76, 0.68), name="set_court_floor", hsv=(0.5, 0.75, 1.0))
    wall_m = _pbr("sandstone_blocks_08", scale=0.45, tint=(0.9, 0.82, 0.7), name="set_court_wall", hsv=(0.5, 0.8, 1.0))
    col_m = _pbr("worn_rock_natural_01", scale=1.2, tint=(0.95, 0.9, 0.82), name="set_court_column",
                 hsv=(0.5, 0.6, 1.1))
    X0, X1, Y0, Y1 = -13.0, 13.0, -8.0, 24.0
    fl = _mesh_obj("court_floor", [(X0, Y0, 0), (X1, Y0, 0), (X1, Y1, 0), (X0, Y1, 0)], [(0, 1, 2, 3)], b, False,
                   floor_m)
    lamp_pts = []
    # side walls with parapet + niches
    for sx in (-1, 1):
        w = C.box("court_wall", (1.0, Y1 - Y0, 4.2), (sx * (X1 + 0.5), (Y0 + Y1) / 2, 2.1), mat_=wall_m, bevel=0.02,
                  coll=b.coll)
        b.add(w)
        cp = C.box("court_coping", (1.2, Y1 - Y0, 0.18), (sx * (X1 + 0.5), (Y0 + Y1) / 2, 4.29), mat_=wall_m, bevel=0.03,
                   coll=b.coll)
        b.add(cp)
        bench = C.box("court_bench", (0.6, Y1 - Y0 - 4, 0.45), (sx * (X1 - 0.3), (Y0 + Y1) / 2 - 1, 0.225), mat_=wall_m,
                      bevel=0.02, coll=b.coll)
        b.add(bench)
        for k in range(int((Y1 - Y0 - 4) / 0.55)):
            y = Y0 + 1.0 + k * 0.55 + rnd.uniform(-0.08, 0.08)
            lamp_pts.append((sx * (X1 - 0.3 + rnd.uniform(-0.12, 0.12)), y, 0.45, 90 * -sx + rnd.uniform(-30, 30)))
        for k in range(int((Y1 - Y0) / 2.2)):
            y = Y0 + 1.1 + k * 2.2
            nz = 1.7
            n = C.box("court_niche", (0.3, 0.6, 0.7), (sx * X1 + sx * 0.12, y, nz + 0.35),
                      mat_=_mat_simple("set_niche_dark", (0.08, 0.06, 0.05), rough=0.9), coll=b.coll)
            b.add(n)
            lamp_pts.append((sx * (X1 - 0.05), y, nz, 90 * -sx))
    # front wall (behind the camera side) low
    fw = C.box("court_front", (X1 - X0 + 2, 1.0, 3.0), (0, Y0 - 0.5, 1.5), mat_=wall_m, bevel=0.02, coll=b.coll)
    b.add(fw)
    # stepped platform + portico at the back
    steps = 6
    sy0 = 17.5
    for k in range(steps):
        st = C.box("court_step", (X1 - X0, 0.42 * (steps - k), 0.18), (0, sy0 + 0.21 * (steps + k) + 0.0, 0.09 + 0.18 * k),
                   mat_=wall_m, bevel=0.015, coll=b.coll)
        b.add(st)
        nl = int((X1 - X0 - 2) / 0.45)
        for i in range(nl):
            if rnd.random() < 0.82:
                x = X0 + 1 + i * 0.45 + rnd.uniform(-0.1, 0.1)
                lamp_pts.append((x, sy0 + 0.42 * k + 0.15 + rnd.uniform(-0.05, 0.05), 0.18 * (k + 1), 90 + rnd.uniform(-40, 40)))
    plat_z = 0.18 * steps
    plat = C.box("court_platform", (X1 - X0, Y1 - (sy0 + 0.42 * steps), plat_z), (0, (Y1 + sy0 + 0.42 * steps) / 2,
                 plat_z / 2), mat_=wall_m, coll=b.coll)
    b.add(plat)
    back = C.box("court_back", (X1 - X0 + 2, 1.0, 9.0), (0, Y1 + 0.5, 4.5), mat_=wall_m, bevel=0.02, coll=b.coll)
    b.add(back)
    if columns:
        cy = sy0 + 0.42 * steps + 1.0
        for i in range(9):
            x = -10.4 + i * 2.6
            _column("court_col", b, col_m, (x, cy, plat_z), height=6.0)
            lamp_pts.append((x + 0.55, cy - 0.5, plat_z, 90))
            lamp_pts.append((x - 0.55, cy - 0.5, plat_z, 90))
        ent = C.box("court_entablature", (X1 - X0, 1.6, 1.0), (0, cy, plat_z + 6.5), mat_=col_m, bevel=0.03, coll=b.coll)
        b.add(ent)
        roof = C.box("court_roof", (X1 - X0, Y1 - cy + 1, 0.4), (0, (cy + Y1) / 2, plat_z + 7.2), mat_=wall_m,
                     coll=b.coll)
        b.add(roof)
    # perimeter lamps around the crowd area + scattered clusters
    for k in range(70):
        a = TAU * k / 70
        x, y = 8.6 * math.cos(a), 7.0 + 8.4 * math.sin(a)
        if Y0 + 1 < y < sy0 - 0.3:
            lamp_pts.append((x + rnd.uniform(-0.2, 0.2), y + rnd.uniform(-0.2, 0.2), 0.0, rnd.uniform(0, 360)))
    while len(lamp_pts) < lamps:
        x, y = rnd.uniform(X0 + 1.5, X1 - 1.5), rnd.uniform(Y0 + 1, sy0 - 0.5)
        if abs(x) > 8.0 or y < -1.0:
            lamp_pts.append((x, y, 0.0, rnd.uniform(0, 360)))
    lf = lamp_field(lamp_pts[:max(lamps, 1)] if lamps else [], b=b, name="court_lamps", seed=seed, flame_strength=22.0)
    b.info.objects["lamps"] = lf
    b.info.extra["lamp_points"] = [b.w(p[:3]) for p in lamp_pts]

    def add_lamps(points, name="court_lamps_extra"):
        return lamp_field(points, b=None, name=name, seed=seed + 1)
    b.info.extra["add_lamps"] = add_lamps
    # crowd spots
    spots = []
    for r in range(crowd_rows):
        for c_ in range(crowd_cols):
            x = -7.0 + 14.0 * c_ / max(1, crowd_cols - 1) + rnd.uniform(-0.22, 0.22)
            y = 0.5 + 13.0 * r / max(1, crowd_rows - 1) + rnd.uniform(-0.22, 0.22)
            spots.append((b.w((x, y, 0.0)), (rnd.uniform(-12, 12) + math.degrees(b.rot_z)) % 360))
    b.info.extra["crowd_spots"] = spots
    # ---------- lighting ----------
    g = glow
    for key, lpos, tgt, size, e in (("wall_glow_L", (X0 + 2.0, 6, 0.6), (X0 - 1, 6, 2.5), (3.0, Y1 - Y0 - 6), 300),
                                     ("wall_glow_R", (X1 - 2.0, 6, 0.6), (X1 + 1, 6, 2.5), (3.0, Y1 - Y0 - 6), 300),
                                     ("wall_glow_B", (0, sy0 - 1.2, 0.3), (0, Y1, 3.5), (X1 - X0 - 2, 2.0), 450)):
        lo = b.light(key, "AREA", lpos, e * g, temp=2000, target=tgt, size=1.0, shadow=False)
        lo.data.shape = "RECTANGLE"
        lo.data.size, lo.data.size_y = size
        lo.data.volume_factor = 0.0
    cg = b.light("crowd_glow", "AREA", (0, 7.0, 1.0), 900.0 * g, temp=2100, target=(0, 7.0, 3.0), size=1.0, shadow=False)
    cg.data.shape = "RECTANGLE"
    cg.data.size, cg.data.size_y = 15.0, 14.0
    cg.data.volume_factor = 0.0
    ck = b.light("crowd_key", "AREA", (0, 17.0, 2.0), 700.0 * g, temp=2200, target=(0, 6.0, 1.5), size=1.0, shadow=False)
    ck.data.shape = "RECTANGLE"
    ck.data.size, ck.data.size_y = 18.0, 2.0
    ck.data.volume_factor = 0.3
    mn = C.sun(elevation=25, azimuth=150, energy=0.12, temp=9000, angle=1.0)
    b.add(mn)
    b.info.lights["moon"] = mn
    if haze:
        hz = C.fog_box(center=(0, 8, 3.5), size=(X1 - X0, Y1 - Y0, 7.0), density=0.012, color=(0.9, 0.85, 0.8),
                       anisotropy=0.4, noise_scale=0.3, name="court_haze", coll=b.coll)
        b.add(hz)
    if world:
        sky_world(sun_elevation=sun_elevation, sun_rotation=sun_azimuth, strength=1.6, light_strength=0.6, air=1.0,
                  dust=1.5, ozone=2.5)
    # ---------- anchors / cameras ----------
    b.anchor("crowd_center", (0, 7.0, 0), yaw=0)
    b.anchor("portico", (0, sy0 + 0.42 * steps + 0.4, plat_z), yaw=180)
    b.anchor("steps_front", (0, sy0 - 0.2, 0))
    b.anchor("leader", (0, sy0 + 0.42 * 3 + 0.2, 0.18 * 3), yaw=180)
    b.cam("wide", (0.0, -6.5, 5.5), (0, 12.0, 1.5), 26)
    b.cam("glide_start", (0.0, -4.0, 4.2), (0, 9.0, 1.4), 28)
    b.cam("glide_end", (0.0, 9.0, 3.4), (0, 20.0, 2.0), 28)
    b.cam("faces", (1.2, 15.8, 1.75), (0.4, 9.0, 1.55), 45)
    b.cam("lamps_close", (-3.0, sy0 - 1.6, 0.6), (0.5, sy0 + 0.6, 0.5), 50)
    b.info.extra["glide"] = [(b.w(l), b.w(t)) for l, t in (((0, -4.0, 4.2), (0, 9.0, 1.4)), ((0, 3.0, 3.8), (0, 13.0, 1.6)),
                                                            ((0, 9.0, 3.4), (0, 20.0, 2.0)))]
    return b.finish()


# ============================================================================================
# 4b. TABLE INTERIOR (s17b)
# ============================================================================================
def _try_asset(name, **kw):
    try:
        from . import assets as A
        return A.load(name, **kw)
    except Exception as e:  # assets module missing / failing: caller falls back
        print("sets: assets.load(%s) unavailable: %s" % (name, e))
        return None


def _flatbread(name, b, loc, radius=0.12, seed=0):
    """Fallback flatbread loaf (two halves 'half_a' (-X) / 'half_b' (+X) parented to an empty)."""
    root = bpy.data.objects.new(name, None)
    b.add(root)
    root.location = loc
    crust = _cached(("bread",), lambda: _bread_mat())
    so = Vector((seed, 2.0, 1.0))
    for k, side in enumerate((-1, 1)):
        verts, faces = [], []
        nr, na = 10, 24
        for i in range(nr + 1):
            r = radius * i / nr
            for j in range(na + 1):
                a = -math.pi / 2 + math.pi * j / na
                x = side * abs(math.cos(a)) * r
                y = math.sin(a) * r
                brk = 0.008 * noise.noise(Vector((y * 40, 0, seed)))
                if i == nr:
                    pass
                x = x if abs(x) > 0.004 else side * (0.002 + abs(brk))
                t = r / radius
                z = 0.032 * (1 - t ** 2.5) ** 0.6 + 0.003 * noise.noise(Vector((x * 40, y * 40, 0)) + so)
                verts.append((x, y, z))
        for i in range(nr):
            for j in range(na):
                a_ = i * (na + 1) + j
                f = (a_, a_ + 1, a_ + na + 2, a_ + na + 1)
                faces.append(f if side > 0 else f[::-1])
        o = _mesh_obj(name + ("_half_a" if side < 0 else "_half_b"), verts, faces, b, True, crust)
        sol = o.modifiers.new("thick", "SOLIDIFY")
        sol.thickness = 0.012
        sol.offset = 1
        o.parent = root
        o.location = (side * 0.002, 0, 0.012)
    return root


def _bread_mat():
    m = C.mat("set_bread", (0.62, 0.38, 0.17), rough=0.75, sss=0.15, sss_radius=(0.5, 0.3, 0.15))
    nt = m.node_tree
    b = C.bsdf(m)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 45
    nt.links.new(tc.outputs["Object"], vor.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 30
    nz.inputs["Detail"].default_value = 6
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.elements[0].position = 0.35
    cr.elements[0].color = (0.82, 0.62, 0.36, 1)      # pale dough / flour
    cr.elements[1].position = 0.75
    cr.elements[1].color = (0.18, 0.08, 0.03, 1)      # charred blisters
    e = cr.elements.new(0.55)
    e.color = (0.55, 0.3, 0.12, 1)
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.5
    nt.links.new(vor.outputs["Distance"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


def table_interior(ctx, loc=(0, 0, 0), rot_z=0.0, coll=None, world=True, use_assets=True, lamps=3, lamp_energy=1.0,
                   haze=True, seed=31, steam=True):
    """Lamplit room with a rough wooden table for breaking bread (s17b). Local layout:
        room x -2.6..2.6, y -2.4..2.6, ceiling 2.7 m with timber beams; plastered stone walls,
        small night window (back-left), wall niche with a lamp (right); heavy plank table
        2.1 x 0.86 m, top at z=0.76, centred at the origin, long axis along X; benches on both
        sides. On the table: round flatbread loaf (two halves, animate apart), clay cup of wine,
        clay jug, wooden bowl of olives, oil lamps.
    Anchors: table_top (centre of the top surface), bread, cup, jug, lamp_table, seat_N0..2
    (far side, facing -Y), seat_S0..2 (near side, facing +Y), hands_zone (above the bread).
    objects['bread'] = bread root (children half_a/half_b, or assets' halves).
    Cameras: bread_close (high 3/4 close-up, use fstop ~2.8), table_wide, low_side.
    Lights: lamp_table (+ lamp_table2), lamp_niche (flicker points), bounce (warm), window (cool).
    """
    b = _B("TableInterior", loc, rot_z, coll, seed)
    rnd = b.rnd
    plaster = _cached(("plaster",), lambda: _grime(C.mat_pbr("clay_plaster", scale=0.7, tint=(0.92, 0.84, 0.72),
                                                             name="set_plaster", bump=1.0, hue_sat_val=(0.5, 0.8, 1.0)),
                                                   "z", 1.9, 2.8, (0.12, 0.09, 0.07), 0.7))
    floor_m = _pbr("brown_mud_dry", scale=0.6, tint=(0.62, 0.52, 0.42), name="set_room_floor", hsv=(0.5, 0.8, 1.0))
    wood = _pbr("wood_table_worn", scale=1.1, tint=(0.75, 0.6, 0.48), name="set_table_wood", rough_add=0.08)
    beam_m = _pbr("weathered_planks", scale=0.9, tint=(0.4, 0.3, 0.22), name="set_beams")
    RX0, RX1, RY0, RY1, RH = -2.6, 2.6, -2.4, 2.6, 2.7
    room = _box_room("room", RX0, RX1, RY0, RY1, -0.01, RH, b, plaster, cuts=12, rough=0.02, seed=seed)
    fl = _mesh_obj("room_floor", [(RX0, RY0, 0), (RX1, RY0, 0), (RX1, RY1, 0), (RX0, RY1, 0)], [(0, 1, 2, 3)], b, False,
                   floor_m)
    for k in range(5):
        bm_ = C.box("ceiling_beam", (RX1 - RX0, 0.18, 0.2), (0, RY0 + 0.6 + k * 1.05, RH - 0.1), (0, 0, rnd.uniform(-1, 1)),
                    beam_m, 0.01, b.coll)
        b.add(bm_)
        C.displace(bm_, strength=0.01, scale=0.2)
    # window (back-left): dark night opening with a frame
    win = C.box("window_frame", (0.7, 0.3, 0.6), (-1.3, RY1 - 0.1, 1.65), mat_=beam_m, bevel=0.01, coll=b.coll)
    b.add(win)
    winglass = _mesh_obj("window_sky", [(-1.6, RY1 - 0.26, 1.38), (-1.0, RY1 - 0.26, 1.38), (-1.0, RY1 - 0.26, 1.92),
                                        (-1.6, RY1 - 0.26, 1.92)], [(0, 1, 2, 3)], b, False,
                         C.mat_emission("set_window_night", (0.05, 0.08, 0.18), 1.0))
    # niche with lamp (right wall)
    niche = C.box("niche", (0.25, 0.5, 0.45), (RX1 - 0.1, 0.9, 1.5), mat_=_mat_simple("set_niche", (0.1, 0.075, 0.06),
                                                                                         rough=0.9), coll=b.coll)
    b.add(niche)
    # ---------- table ----------
    TL, TW, TZ = 2.1, 0.86, 0.76
    planks = 4
    for k in range(planks):
        w = TW / planks - 0.006
        y = -TW / 2 + (k + 0.5) * TW / planks
        pl = _rock_block("table_plank%d" % k, (TL + rnd.uniform(-0.03, 0.03), w, 0.055),
                         (rnd.uniform(-0.015, 0.015), y, TZ - 0.0275 + rnd.uniform(-0.003, 0.003)), b, wood,
                         noise_amp=0.0025, noise_scale=6.0, cuts=8, seed=k + 3, bevel=0.006)
        _set_smooth_by_angle(pl, 40)
    for sx in (-1, 1):
        for sy in (-1, 1):
            leg = C.box("table_leg", (0.09, 0.09, TZ - 0.055), (sx * (TL / 2 - 0.15), sy * (TW / 2 - 0.1), (TZ - 0.055) / 2),
                        (rnd.uniform(-1.5, 1.5), rnd.uniform(-1.5, 1.5), 0), wood, 0.008, b.coll)
            b.add(leg)
        ap = C.box("table_apron", (0.07, TW - 0.25, 0.1), (sx * (TL / 2 - 0.15), 0, TZ - 0.11), mat_=wood, bevel=0.006,
                   coll=b.coll)
        b.add(ap)
    st = C.box("table_stretcher", (TL - 0.3, 0.07, 0.07), (0, 0, 0.18), mat_=wood, bevel=0.006, coll=b.coll)
    b.add(st)
    for sy in (-1, 1):
        bench = _rock_block("bench", (TL - 0.1, 0.3, 0.05), (0, sy * 0.78, 0.45), b, wood, noise_amp=0.002, cuts=6,
                            seed=7 + sy, bevel=0.005)
        for sx in (-1, 1):
            bl = C.box("bench_leg", (0.06, 0.24, 0.43), (sx * (TL / 2 - 0.25), sy * 0.78, 0.215), mat_=wood, bevel=0.005,
                       coll=b.coll)
            b.add(bl)
    # ---------- table dressing ----------
    bread_loc = Vector((0.0, -0.06, TZ))
    bread = None
    if use_assets:
        bread = _try_asset("flatbread", loc=(0, 0, 0), variant=1)
        if bread is not None:
            b.add(bread)
            bread.location = bread_loc
    if bread is None:
        bread = _flatbread("bread", b, bread_loc, seed=seed)
    b.info.objects["bread"] = bread
    cup_loc = Vector((0.36, 0.14, TZ))
    cup = _try_asset("clay_cup", loc=(0, 0, 0), wine=True) if use_assets else None
    if cup is not None:
        b.add(cup)
        cup.location = cup_loc
    else:
        cup = clay_cup(cup_loc, b=b)
    b.info.objects["cup"] = cup
    jug_loc = Vector((0.62, 0.24, TZ))
    jug = _try_asset("water_jar", loc=(0, 0, 0), variant=1) if use_assets else None
    if jug is not None:
        b.add(jug)
        jug.location = jug_loc
    else:
        jug = clay_jar(tuple(jug_loc), height=0.28, b=b, name="jug")
    bowl = _lathe([(0.0, 0.0), (0.05, 0.0), (0.085, 0.03), (0.095, 0.055), (0.088, 0.058), (0.078, 0.032), (0.0, 0.02)],
                  28, "olive_bowl", b, _pbr("wood_table_worn", scale=4.0, tint=(0.55, 0.4, 0.28), name="set_bowl_wood"))
    bowl.location = (-0.45, 0.2, TZ)
    om = _mat_simple("set_olive", (0.05, 0.06, 0.02), rough=0.25, coat=0.4)
    for k in range(14):
        a = rnd.uniform(0, TAU)
        r = rnd.uniform(0, 0.055)
        ol = C.prim("uv_sphere", "olive", loc=(-0.45 + r * math.cos(a), 0.2 + r * math.sin(a), TZ + 0.035 + rnd.uniform(0, 0.02)),
                    segments=10, ring_count=6, radius=0.011)
        ol.scale = (1.0, 1.0, 1.35)
        ol.rotation_euler = (rnd.uniform(0, 3), rnd.uniform(0, 3), 0)
        ol.data.materials.append(om)
        b.add(ol)
    # crumbs
    crm = _cached(("crumb",), lambda: C.mat("set_crumb", (0.7, 0.5, 0.28), rough=0.8))
    for k in range(22):
        a = rnd.uniform(0, TAU)
        r = rnd.uniform(0.14, 0.32)
        cb = C.prim("ico_sphere", "crumb", loc=(bread_loc.x + r * math.cos(a), bread_loc.y + r * math.sin(a), TZ + 0.003),
                    subdivisions=1, radius=rnd.uniform(0.003, 0.008))
        cb.scale = (1, 1, 0.6)
        cb.data.materials.append(crm)
        b.add(cb)
    # lamps
    lt = oil_lamp((-0.32, -0.16, TZ), rot_z=20, energy=40.0 * lamp_energy, seed=3, b=b, name="lamp_table")
    b.info.lights["lamp_table"] = lt[2]
    if lamps >= 2:
        lt2 = oil_lamp((0.75, -0.12, TZ), rot_z=160, energy=30.0 * lamp_energy, seed=4, b=b, name="lamp_table2")
        b.info.lights["lamp_table2"] = lt2[2]
    if lamps >= 3:
        ln_ = oil_lamp((RX1 - 0.18, 0.9, 1.28), rot_z=180, energy=25.0 * lamp_energy, seed=5, b=b, name="lamp_niche")
        b.info.lights["lamp_niche"] = ln_[2]
    bo = b.light("bounce", "AREA", (0, 0, RH - 0.25), 45.0 * lamp_energy, temp=2400, target=(0, 0, 0), size=2.5,
                 shadow=False)
    bo.data.volume_factor = 0.0
    wl = b.light("window", "AREA", (-1.3, RY1 - 0.3, 1.65), 12.0, temp=12000, target=(0, 0, 0.6), size=0.6,
                 shadow=True)
    wl.data.volume_factor = 0.3
    if haze:
        hz = C.fog_box(center=(0, 0.1, 1.35), size=(RX1 - RX0 - 0.1, RY1 - RY0 - 0.1, RH - 0.05), density=0.025,
                       color=(0.9, 0.86, 0.8), anisotropy=0.4, noise_scale=1.5, name="room_haze", coll=b.coll)
        b.add(hz)
    if steam:
        sm = C.box("bread_steam", (0.3, 0.3, 0.5), (bread_loc.x, bread_loc.y, TZ + 0.27), coll=b.coll)
        b.add(sm)
        sm.data.materials.append(_smoke_material("set_bread_steam", density=0.6, color=(1, 1, 1), scale=8.0, rise=0.35,
                                                 shape="column", falloff=0.8, anisotropy=0.3))
        b.info.objects["steam"] = sm
    if world:
        night_world(strength=0.5, stars=0.6)
    # ---------- anchors / cameras ----------
    b.anchor("table_top", (0, 0, TZ))
    b.anchor("bread", tuple(bread_loc))
    b.anchor("cup", tuple(cup_loc))
    b.anchor("jug", tuple(jug_loc))
    b.anchor("lamp_table", (-0.32, -0.16, TZ + 0.05))
    b.anchor("hands_zone", (bread_loc.x, bread_loc.y, TZ + 0.12))
    for k, x in enumerate((-0.65, 0.0, 0.65)):
        b.anchor("seat_N%d" % k, (x, 0.78, 0.475), yaw=180)
        b.anchor("seat_S%d" % k, (x, -0.78, 0.475), yaw=0)
    b.cam("bread_close", (0.25, -0.62, 1.28), (0.0, -0.04, TZ + 0.02), 50)
    b.cam("table_wide", (1.9, -2.1, 1.65), (0.0, 0.1, 0.85), 30)
    b.cam("low_side", (-1.05, -0.5, 0.92), (0.1, 0.0, TZ + 0.05), 40)
    return b.finish()


# ============================================================================================
# 4c. CAMP NIGHT (s20a)
# ============================================================================================
def _fallback_fire(b, loc, size=1.0, energy=300.0, seed=0):
    """Simple campfire: stone ring, logs, emissive flame cones and a flickering light."""
    rnd = random.Random(seed)
    root = bpy.data.objects.new("campfire", None)
    b.add(root)
    root.location = loc
    stone_m = _pbr("rock_boulder_dry", scale=2.0, tint=(0.6, 0.56, 0.5), name="set_fire_stones")
    for k in range(11):
        a = TAU * k / 11 + rnd.uniform(-0.1, 0.1)
        st = _boulder("fire_stone", (0.2 * size, 0.16 * size, 0.13 * size), (math.cos(a) * 0.42 * size, math.sin(a) * 0.42 * size, -0.02),
                      b, stone_m, seed=seed + k, rot_z=math.degrees(a))
        st.parent = root
    wood = _pbr("weathered_planks", scale=3.0, tint=(0.35, 0.25, 0.18), name="set_fire_logs")
    for k in range(5):
        a = TAU * k / 5 + 0.3
        lg = _lathe([(0.0, 0.0), (0.04 * size, 0.0), (0.04 * size, 0.55 * size), (0.0, 0.55 * size)], 10, "fire_log", b, wood)
        lg.parent = root
        lg.location = (math.cos(a) * 0.25 * size, math.sin(a) * 0.25 * size, 0.02)
        lg.rotation_euler = Euler((0, math.radians(-62), a + math.pi), "XYZ")
    fm = _cached(("campflame",), lambda: _flame_material("set_campflame", strength=8.0))
    for k in range(6):
        fl = bpy.data.objects.new("fire_flame", _flame_mesh())
        fl.data.materials.clear()
        fl.data.materials.append(fm)
        b.add(fl)
        fl.parent = root
        fl.location = (rnd.uniform(-0.08, 0.08) * size, rnd.uniform(-0.08, 0.08) * size, 0.05 * size)
        s_ = size * rnd.uniform(11.0, 17.0)
        fl.scale = (s_ * 0.9, s_ * 0.9, s_ * 1.1)
        fl.visible_shadow = False
        C.key_fn(fl, "scale", lambda f, s_=s_, k=k: (s_ * 0.9, s_ * 0.9, s_ * (1.1 + 0.25 * noise.noise(Vector((f / 24 * 5, k, 0.3))))),
                 1, bpy.context.scene.frame_end, step=2)
    ld = bpy.data.lights.new("fire_light", "POINT")
    ld.energy = energy
    ld.color = C.kelvin(1800)
    ld.shadow_soft_size = 0.12 * size
    lo = bpy.data.objects.new("fire_light", ld)
    b.add(lo)
    lo.parent = root
    lo.location = (0, 0, 0.35 * size)
    flicker_light(lo, energy, amount=0.25, speed=7, seed=seed)
    return root, lo


def camp_night(ctx, loc=(0, 0, 0), rot_z=0.0, coll=None, world=True, fire=True, fire_size=0.8, fire_energy=1.0,
               moon=True, seed=41, use_fx=True, grass=True):
    """Open ground at night around a small campfire (s20a). Local layout: fire at the origin;
    grandfather's seat (a low boulder) at (-0.95, 0.35) facing the child; child's seat (small
    stone) at (0.75, 0.55); rolling dark hills and scattered rocks, dry grass, a starry sky and
    cool moonlight from behind (+Y) for rim light.
    The fire uses lib/fx.py campfire() when available (use_fx=True) else a built-in fallback.
    Anchors: fire, grandfather (seat top; yaw faces the child/fire), child (seat top), handoff
    (between them at hand height, where the lamp is passed), scroll_spot.
    Cameras: two_shot, over_shoulder, fire_low, wide. Lights: fire (flickering point), moon (sun),
    fire_bounce (warm, no shadow).
    """
    b = _B("CampNight", loc, rot_z, coll, seed)
    rnd = b.rnd
    ground_m = _pbr("rocky_trail_02", scale=0.5, tint=(0.62, 0.56, 0.48), name="set_camp_ground", hsv=(0.5, 0.7, 1.0))
    rock_m = _pbr("rock_boulder_dry", scale=1.2, tint=(0.75, 0.7, 0.62), name="set_camp_rock", hsv=(0.5, 0.6, 1.0))

    def gfn(u, v):
        x = (u - 0.5) * 60
        y = (v - 0.5) * 60 + 10
        d = math.hypot(x, y)
        z = 0.06 * C.fbm(x * 0.6, y * 0.6, 3, seed=seed) + 2.2 * max(0.0, (d - 8) / 22.0) ** 1.6 * (
            0.6 + 0.4 * C.fbm(x * 0.05, y * 0.05, 3, seed=seed + 1))
        return Vector((x, y, z))
    gnd = _grid_obj("camp_ground", 120, 120, gfn, b, ground_m)
    if grass:
        _grass_tufts(gnd, density=6.0, seed=seed, height=0.28, color=(0.3, 0.27, 0.15), dry=0.8)
    hv, hf = [], []
    for i in range(81):
        a = math.radians(-30 + 240 * i / 80)
        x, y = math.cos(a) * 90.0, math.sin(a) * 90.0
        hgt = 4.0 + 9.0 * (0.5 + 0.5 * C.fbm(i * 0.06, 0.7, 4, seed=seed))
        hv += [(x, y, -10.0), (x, y, hgt)]
    for i in range(80):
        hf.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
    _mesh_obj("camp_hills", hv, hf, b, False, _mat_simple("set_camp_hills", (0.02, 0.022, 0.03), rough=0.95))
    gseat = _boulder("grandfather_seat", (0.75, 0.55, 0.42), (-0.95, 0.35, -0.04), b, rock_m, seed=3, rot_z=15, rough=0.25,
                     flat=0.7, subdiv=4)
    cseat = _boulder("child_seat", (0.45, 0.4, 0.26), (0.75, 0.55, -0.03), b, rock_m, seed=7, rot_z=-20, rough=0.25,
                     flat=0.7, subdiv=3)
    for k in range(10):
        a = rnd.uniform(0, TAU)
        r = rnd.uniform(2.5, 9.0)
        _boulder("camp_rock%d" % k, (rnd.uniform(0.3, 1.3), rnd.uniform(0.3, 1.0), rnd.uniform(0.2, 0.7)),
                 (math.cos(a) * r, math.sin(a) * r + 1.0, -0.08), b, rock_m, seed=20 + k, rot_z=rnd.uniform(0, 360))
    fire_obj = None
    if fire:
        if use_fx:
            try:
                from . import fx
                fxr = fx.campfire(loc=(0, 0, 0), size=fire_size, light_energy=350.0 * fire_energy, seed=seed,
                                  coll=b.coll)
                fire_obj = getattr(fxr, "root", None)
                if fire_obj is not None:
                    b.add(fire_obj)
                b.info.extra["fx"] = fxr
            except Exception as e:
                print("sets.camp_night: fx.campfire unavailable (%s) - using fallback fire" % e)
                fire_obj = None
        if fire_obj is None:
            fire_obj, flo = _fallback_fire(b, (0, 0, 0), fire_size, 300.0 * fire_energy, seed)
            b.info.lights["fire"] = flo
        b.info.objects["fire"] = fire_obj
    fb = b.light("fire_bounce", "AREA", (0, 0, 0.15), 60.0 * fire_energy, temp=1900, target=(0, 0, 3), size=2.0,
                 shadow=False)
    fb.data.volume_factor = 0.0
    if moon:
        mn = C.sun(elevation=28, azimuth=165, energy=0.18, temp=10000, angle=0.6)
        b.add(mn)
        b.info.lights["moon"] = mn
    if world:
        night_world(strength=1.0, stars=1.0)
    hz = C.fog_box(center=(0, 6, 2.5), size=(40, 40, 5), density=0.006, color=(0.8, 0.82, 0.9), anisotropy=0.3,
                   name="camp_haze", coll=b.coll)
    b.add(hz)
    b.anchor("fire", (0, 0, 0))
    b.anchor("grandfather", (-0.95, 0.35, 0.38), yaw=-110)
    b.anchor("child", (0.75, 0.55, 0.23), yaw=110)
    b.anchor("handoff", (-0.1, 0.5, 0.75))
    b.anchor("scroll_spot", (-0.7, 0.2, 0.75))
    b.cam("two_shot", (0.0, -2.4, 1.05), (-0.1, 0.45, 0.7), 35)
    b.cam("over_shoulder", (1.35, 1.25, 1.0), (-0.9, 0.3, 0.85), 45)
    b.cam("fire_low", (0.3, -1.3, 0.3), (-0.2, 0.5, 0.6), 28)
    b.cam("wide", (2.5, -5.5, 2.2), (0, 0.5, 0.5), 30)
    return b.finish()
