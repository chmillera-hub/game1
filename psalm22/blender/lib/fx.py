"""Special effects for Psalm 22 (Blender 4.5, EEVEE Next).  API reference: psalm22/docs/fx.md

Effects (each returns an `FX` handle: .root empty you can move/parent + named parts):
    flame(...)            small animated candle / oil-lamp flame + flickering point light
    lamp_field(points)    hundreds of cheap far-LOD lamp flames (one GN instancer) + a few cluster lights
    torch(...)            hand torch: stick + burning head, licking flames, smoke, embers, light
    campfire(...)         logs + stones, flames, glowing coals, rising sparks, smoke, warm light
    red_sea(ctx, ...)     parted Red Sea: two animated water walls, spray, wet seabed, mist (+ collapse)
    earth_from_space(ctx) Blue/Black Marble globe, clouds, atmosphere, moving sunrise terminator, stars
    ash_disintegrate(obj) mesh blows away as ash particles behind an advancing front
    dust_burst(loc)       one-shot dust puff (hoof impact, falling body, ...)
    dust_pour(hand_loc)   fine dust trickling from an opening hand, carried away by wind
    water_pour(...)       slow-motion stream from a tilted clay jar, splash, wet patch draining away
    melting_candle(...)   time-lapse beeswax candle melting with drips, spreading pool, guttering flame

Design notes
- Everything is *stateless*: particles / deformations are closed-form functions of the scene frame
  evaluated in Geometry Nodes, so any frame renders correctly in isolation (no baking, no
  ctx.needs_bake needed for anything in this module).
- Effect time is in seconds: T = (frame - frame0) / fps * time_scale. Slow motion = time_scale < 1.
- Emissive flames use additive transparency (Emission + Transparent, BLENDED); they cast no shadows.
"""
import bpy, math, os, random
import numpy as np
from mathutils import Vector, Matrix, Euler
from . import core as C

FPS = 24
EARTH_DIR = os.path.join(C.ASSETS, "earth")


# =============================================================================================
# Small infrastructure
# =============================================================================================
class FX:
    """Handle returned by every effect. `root` is an empty (move / parent it); other attributes
    are the effect's parts (objects, lights, materials, modifiers)."""

    def __init__(self, root, **parts):
        self.root = root
        self.__dict__.update(parts)

    def __repr__(self):
        return "FX(%s: %s)" % (self.root.name, ", ".join(k for k in self.__dict__ if k != "root"))


def _fps():
    return bpy.context.scene.render.fps or FPS


def _empty(name, loc=(0, 0, 0), coll=None, size=0.1):
    e = C.link(bpy.data.objects.new(name, None), coll)
    e.empty_display_size = size
    e.location = loc
    return e


def _parent(child, parent):
    child.parent = parent
    child.matrix_parent_inverse = Matrix.Identity(4)
    return child


def _mesh_obj(name, verts, faces=(), coll=None, smooth=False):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.update()
    if smooth:
        me.shade_smooth()
    return C.link(bpy.data.objects.new(name, me), coll)


def _points_obj(name, pos, attrs=None, coll=None):
    """Vertex-only mesh with per-point float / vector attributes (numpy arrays)."""
    pos = np.asarray(pos, dtype=np.float32).reshape(-1, 3)
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(pos))
    me.vertices.foreach_set("co", pos.ravel())
    for k, arr in (attrs or {}).items():
        arr = np.asarray(arr, dtype=np.float32)
        if arr.ndim == 2:
            a = me.attributes.new(k, "FLOAT_VECTOR", "POINT")
            a.data.foreach_set("vector", arr.ravel())
        else:
            a = me.attributes.new(k, "FLOAT", "POINT")
            a.data.foreach_set("value", arr.ravel())
    me.update()
    return C.link(bpy.data.objects.new(name, me), coll)


def _lathe(name, profile, segs=24, coll=None, cap_bottom=False, cap_top=False, smooth=True):
    """Surface of revolution around Z. profile = [(r, z), ...] bottom to top. Points with r == 0
    become poles."""
    verts, faces, rings = [], [], []
    for r, z in profile:
        if r <= 1e-6:
            rings.append([len(verts)])
            verts.append((0, 0, z))
        else:
            idx = []
            for i in range(segs):
                a = 2 * math.pi * i / segs
                idx.append(len(verts))
                verts.append((r * math.cos(a), r * math.sin(a), z))
            rings.append(idx)
    for a, b in zip(rings[:-1], rings[1:]):
        if len(a) == 1 and len(b) > 1:
            for i in range(segs):
                faces.append((a[0], b[i], b[(i + 1) % segs]))
        elif len(b) == 1 and len(a) > 1:
            for i in range(segs):
                faces.append((a[i], b[0], a[(i + 1) % segs])[::-1] if False else (a[(i + 1) % segs], a[i], b[0])[::-1])
        elif len(a) > 1:
            for i in range(segs):
                j = (i + 1) % segs
                faces.append((a[i], a[j], b[j], b[i]))
    if cap_bottom and len(rings[0]) > 1:
        faces.append(tuple(reversed(rings[0])))
    if cap_top and len(rings[-1]) > 1:
        faces.append(tuple(rings[-1]))
    o = _mesh_obj(name, verts, faces, coll, smooth=smooth)
    return o


def _set_fcurves_linear(id_data, needle, extrapolate=True):
    ad = id_data.animation_data
    if not ad or not ad.action:
        return []
    out = []
    for fc in C._fcurves(ad.action):
        if needle in fc.data_path:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
            if extrapolate:
                fc.extrapolation = "LINEAR"
            out.append(fc)
    return out


def _find_fcurve(id_data, data_path, index=0):
    ad = id_data.animation_data
    if not ad or not ad.action:
        return None
    for fc in C._fcurves(ad.action):
        if fc.data_path == data_path and fc.array_index == index:
            return fc
    return None


def _add_noise(fc, scale=8.0, strength=1.0, phase=0.0, depth=1, offset=0.0):
    """F-curve noise modifier (cheap infinite flicker, no python per frame)."""
    m = fc.modifiers.new("NOISE")
    m.scale = scale
    m.strength = strength
    m.phase = phase
    m.offset = offset
    m.depth = depth
    m.blend_type = "ADD"
    return m


def _flicker_prop(id_data, path, base, amount, scale, phase, depth=1, index=-1):
    """Key `path` = base and add an f-curve noise of +-amount/2 (normalised noise is ~[-0.5, 0.5])."""
    if index >= 0:
        getattr(id_data, path)[index] = base
        id_data.keyframe_insert(path, index=index, frame=1)
        fc = _find_fcurve(id_data, path, index)
    else:
        id_data.path_resolve(path)
        _set_by_path(id_data, path, base)
        id_data.keyframe_insert(path, frame=1)
        fc = _find_fcurve(id_data, path, 0)
    if fc is not None and amount:
        _add_noise(fc, scale=scale, strength=amount, phase=phase, depth=depth)
    return fc


def _set_by_path(id_data, path, v):
    if path.startswith("["):
        id_data[path[2:-2]] = v
    elif path.startswith("modifiers["):
        # modifiers["Name"]["Socket_2"]
        mname = path.split('"')[1]
        key = path.split('"')[3]
        id_data.modifiers[mname][key] = v
    else:
        setattr(id_data, path, v)


# ---------------------------------------------------------------------------------------------
# Node builder (works for shader and geometry node trees)
# ---------------------------------------------------------------------------------------------
class NB:
    """Tiny node-graph builder: nb.n(type, {input: value_or_socket}, **props) -> node."""

    def __init__(self, tree):
        self.t = tree
        self.nodes = tree.nodes
        self.links = tree.links

    @staticmethod
    def _sin(nd, key):
        if isinstance(key, int):
            return nd.inputs[key]
        for s in nd.inputs:
            if (s.name == key or s.identifier == key) and s.enabled:
                return s
        for s in nd.inputs:
            if s.name == key or s.identifier == key:
                return s
        raise KeyError("%s has no input %r" % (nd.bl_idname, key))

    @staticmethod
    def out(nd, key=None):
        if isinstance(nd, bpy.types.NodeSocket):
            return nd
        if key is None:
            for s in nd.outputs:
                if s.enabled:
                    return s
            return nd.outputs[0]
        if isinstance(key, int):
            return nd.outputs[key]
        for s in nd.outputs:
            if s.name == key and s.enabled:
                return s
        return nd.outputs[key]

    def set(self, nd, key, v):
        s = self._sin(nd, key)
        if isinstance(v, bpy.types.NodeSocket):
            self.links.new(v, s)
        elif isinstance(v, bpy.types.Node):
            self.links.new(self.out(v), s)
        elif v is None:
            pass
        else:
            dv = s.default_value
            if hasattr(dv, "__len__") and not isinstance(v, (str, bpy.types.ID)):
                if not hasattr(v, "__len__"):
                    v = [v] * len(dv)
                v = list(v)
                if len(dv) == 4 and len(v) == 3:
                    v = v + [1.0]
            s.default_value = v

    def n(self, type_, inputs=None, **props):
        nd = self.nodes.new(type_)
        for k, v in props.items():
            setattr(nd, k, v)
        for k, v in (inputs or {}).items():
            self.set(nd, k, v)
        return nd

    # math sugar ---------------------------------------------------------------------------
    def m(self, op, a, b=0.0, c=0.0, clamp=False):
        nd = self.n("ShaderNodeMath", operation=op, use_clamp=clamp)
        self.set(nd, 0, a)
        self.set(nd, 1, b)
        self.set(nd, 2, c)
        return nd.outputs[0]

    def add(self, a, b):
        return self.m("ADD", a, b)

    def sub(self, a, b):
        return self.m("SUBTRACT", a, b)

    def mul(self, a, b):
        return self.m("MULTIPLY", a, b)

    def div(self, a, b):
        return self.m("DIVIDE", a, b)

    def madd(self, a, b, c):
        return self.m("MULTIPLY_ADD", a, b, c)

    def v(self, op, a, b=None, c=None, scale=None):
        nd = self.n("ShaderNodeVectorMath", operation=op)
        if a is not None:
            self.set(nd, 0, a)
        if b is not None:
            self.set(nd, 1, b)
        if c is not None:
            self.set(nd, 2, c)
        if scale is not None:
            self.set(nd, "Scale", scale)
        return nd.outputs["Value"] if op in ("DOT_PRODUCT", "LENGTH", "DISTANCE") else nd.outputs["Vector"]

    def xyz(self, x=0.0, y=0.0, z=0.0):
        return self.out(self.n("ShaderNodeCombineXYZ", {"X": x, "Y": y, "Z": z}))

    def sep(self, vec):
        return self.n("ShaderNodeSeparateXYZ", {"Vector": vec})

    def maprange(self, val, a, b, c=0.0, d=1.0, clamp=True, interp="LINEAR"):
        nd = self.n("ShaderNodeMapRange", {"Value": val, "From Min": a, "From Max": b, "To Min": c, "To Max": d},
                    clamp=clamp, interpolation_type=interp)
        return nd.outputs["Result"]

    def smooth(self, val, a, b):
        return self.maprange(val, a, b, 0.0, 1.0, True, "SMOOTHSTEP")

    def mixf(self, f, a, b):
        nd = self.n("ShaderNodeMix", data_type="FLOAT")
        self.set(nd, "Factor", f)
        self.set(nd, "A", a)
        self.set(nd, "B", b)
        return self.out(nd, "Result")

    def mixc(self, f, a, b, blend="MIX"):
        nd = self.n("ShaderNodeMix", data_type="RGBA", blend_type=blend)
        self.set(nd, "Factor", f)
        self.set(nd, "A", a)
        self.set(nd, "B", b)
        return self.out(nd, "Result")

    def mixv(self, f, a, b):
        nd = self.n("ShaderNodeMix", data_type="VECTOR")
        self.set(nd, "Factor", f)
        self.set(nd, "A", a)
        self.set(nd, "B", b)
        return self.out(nd, "Result")

    def noise(self, vec=None, scale=1.0, detail=2.0, rough=0.5, w=None, dims=None, distortion=0.0, lac=2.0):
        dims = dims or ("4D" if w is not None else "3D")
        nd = self.n("ShaderNodeTexNoise", noise_dimensions=dims)
        if vec is not None:
            self.set(nd, "Vector", vec)
        if w is not None:
            self.set(nd, "W", w)
        self.set(nd, "Scale", scale)
        self.set(nd, "Detail", detail)
        self.set(nd, "Roughness", rough)
        self.set(nd, "Lacunarity", lac)
        self.set(nd, "Distortion", distortion)
        return nd

    def attr(self, name, dtype="FLOAT"):
        """GN: named attribute output socket."""
        nd = self.n("GeometryNodeInputNamedAttribute", data_type=dtype)
        nd.inputs["Name"].default_value = name
        return nd.outputs["Attribute"]

    def sattr(self, name, kind="GEOMETRY"):
        """Shader: attribute node (kind GEOMETRY / OBJECT / INSTANCER)."""
        return self.n("ShaderNodeAttribute", attribute_name=name, attribute_type=kind)


def _gn_tree(name, inputs, outputs=(("Geometry", "NodeSocketGeometry"),)):
    """New geometry-node group with the given interface. inputs = [(name, socket_type, default), ...]."""
    t = bpy.data.node_groups.new(name, "GeometryNodeTree")
    for nm, st in outputs:
        t.interface.new_socket(nm, in_out="OUTPUT", socket_type=st)
    for spec in inputs:
        nm, st = spec[0], spec[1]
        s = t.interface.new_socket(nm, in_out="INPUT", socket_type=st)
        if len(spec) > 2 and spec[2] is not None and hasattr(s, "default_value"):
            s.default_value = spec[2]
    nb = NB(t)
    gi = nb.n("NodeGroupInput")
    go = nb.n("NodeGroupOutput")
    return t, nb, gi, go


def _mod(obj, tree, name="FX", **values):
    m = obj.modifiers.new(name, "NODES")
    m.node_group = tree
    _mod_set(m, **values)
    return m


def _mod_ident(mod, key):
    for it in mod.node_group.interface.items_tree:
        if getattr(it, "in_out", None) == "INPUT" and it.name == key:
            return it.identifier
    raise KeyError(key)


def _mod_set(mod, **values):
    for k, v in values.items():
        ident = _mod_ident(mod, k.replace("_", " "))
        if isinstance(v, Vector):
            v = tuple(v)
        mod[ident] = v


def _mod_path(mod, key):
    return 'modifiers["%s"]["%s"]' % (mod.name, _mod_ident(mod, key))


def _time_value(nt, name="fx_time", scale=1.0, f0=1):
    """Shader-side clock: Value node keyed linearly = (frame - f0)/fps * scale seconds (extrapolated)."""
    nb = NB(nt) if not isinstance(nt, NB) else nt
    tree = nb.t
    nd = nb.n("ShaderNodeValue")
    nd.name = nd.label = name
    fps = _fps()
    s = nd.outputs[0]
    s.default_value = 0.0
    s.keyframe_insert("default_value", frame=f0)
    s.default_value = 100.0 * scale
    s.keyframe_insert("default_value", frame=f0 + 100 * fps)
    _set_fcurves_linear(tree, 'nodes["%s"]' % name)
    return s


def _blended(m, backface=True, shadow=False):
    m.surface_render_method = "BLENDED"
    m.use_backface_culling = not backface
    m.use_transparent_shadow = True
    try:
        m.use_transparency_overlap = True
    except Exception:
        pass
    return m


def _new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    nb = NB(nt)
    out = nb.n("ShaderNodeOutputMaterial")
    return m, nb, out


def _no_shadow(o):
    o.visible_shadow = False
    return o


# =============================================================================================
# Particles: one generic, stateless (closed-form) GN particle solver
# =============================================================================================
# Per-point attributes (written by _particles):  v0 (vector m/s), birth (s), life (s), size (m),
# rnd (0..1).  Position of the vertex = emission point p0 (object space).
# Motion: linear drag k toward `Wind`, constant `Gravity`:
#   x(t) = p0 + wind*t + (v0-wind)*A + g*B,   A = (1-e^-kt)/k,  B = (t-A)/k   (series for small kt)
# + coherent turbulence (4D noise displacement growing with age).
_PT_TREE = None


def _particle_tree():
    global _PT_TREE
    if _PT_TREE is not None and _PT_TREE.name in bpy.data.node_groups:
        return _PT_TREE
    t, nb, gi, go = _gn_tree("FX_Particles", [
        ("Geometry", "NodeSocketGeometry"),
        ("Frame0", "NodeSocketFloat", 1.0),
        ("FPS", "NodeSocketFloat", 24.0),
        ("Time Scale", "NodeSocketFloat", 1.0),
        ("Gravity", "NodeSocketVector", (0, 0, -9.81)),
        ("Drag", "NodeSocketFloat", 1.0),
        ("Wind", "NodeSocketVector", (0, 0, 0)),
        ("Turb Amp", "NodeSocketFloat", 0.0),
        ("Turb Scale", "NodeSocketFloat", 1.0),
        ("Turb Speed", "NodeSocketFloat", 0.5),
        ("Turb Ramp", "NodeSocketFloat", 1.0),
        ("Floor", "NodeSocketFloat", -1e6),
        ("Floor Mode", "NodeSocketInt", 0),          # 0 none, 1 clamp (settle), 2 kill
        ("Grow", "NodeSocketFloat", 1.0),           # size multiplier at end of life
        ("Fade In", "NodeSocketFloat", 0.05),       # fraction of life
        ("Fade Out", "NodeSocketFloat", 0.3),
        ("Shrink", "NodeSocketBool", False),        # multiply size by fade
        ("Mode", "NodeSocketInt", 0),               # 0 points, 1 instances, 2 velocity-aligned, 3 camera billboards
        ("Instance", "NodeSocketObject"),
        ("Camera", "NodeSocketObject"),
        ("Stretch", "NodeSocketFloat", 0.0),        # streak length = |v| * Stretch (mode 2)
        ("Spin", "NodeSocketFloat", 0.0),           # rad/s random roll (modes 1/3)
        ("Material", "NodeSocketMaterial"),
    ])
    G = lambda k: gi.outputs[k]
    # time
    st = nb.n("GeometryNodeInputSceneTime")
    T = nb.mul(nb.div(nb.sub(st.outputs["Frame"], G("Frame0")), G("FPS")), G("Time Scale"))
    birth, life, size, rnd = nb.attr("birth"), nb.attr("life"), nb.attr("size"), nb.attr("rnd")
    v0 = nb.attr("v0", "FLOAT_VECTOR")
    tau = nb.sub(T, birth)
    age = nb.div(tau, nb.m("MAXIMUM", life, 1e-4))
    taup = nb.m("MAXIMUM", tau, 0.0)
    k = nb.m("MAXIMUM", G("Drag"), 1e-3)
    x = nb.mul(k, taup)
    ex = nb.m("EXPONENT", nb.mul(x, -1.0))
    A_ex = nb.div(nb.sub(1.0, ex), k)
    B_ex = nb.div(nb.sub(taup, A_ex), k)
    # series for small k*t
    t2 = nb.mul(taup, taup)
    A_se = nb.mul(taup, nb.madd(x, nb.madd(x, 1.0 / 6.0, -0.5), 1.0))
    B_se = nb.mul(t2, nb.madd(x, nb.madd(x, 1.0 / 24.0, -1.0 / 6.0), 0.5))
    small = nb.m("LESS_THAN", x, 0.05)
    A = nb.mixf(small, A_ex, A_se)
    B = nb.mixf(small, B_ex, B_se)
    pos = nb.out(nb.n("GeometryNodeInputPosition"))
    lin = nb.v("ADD", pos, nb.v("SCALE", G("Wind"), scale=taup))
    lin = nb.v("ADD", lin, nb.v("SCALE", nb.v("SUBTRACT", v0, G("Wind")), scale=A))
    lin = nb.v("ADD", lin, nb.v("SCALE", G("Gravity"), scale=B))
    # turbulence: 4D noise sampled at the linear position, displacement grows with age
    nz = nb.noise(nb.v("SCALE", lin, scale=G("Turb Scale")), scale=1.0, detail=1.0, w=nb.add(nb.mul(T, G("Turb Speed")), nb.mul(rnd, 0.0)))
    tv = nb.v("SCALE", nb.v("SUBTRACT", nb.out(nz, "Color"), (0.5, 0.5, 0.5)), scale=2.0)
    ramp = nb.m("MINIMUM", nb.div(taup, nb.m("MAXIMUM", G("Turb Ramp"), 1e-3)), 1.0)
    p = nb.v("ADD", lin, nb.v("SCALE", tv, scale=nb.mul(G("Turb Amp"), ramp)))
    # velocity (for alignment): wind + (v0-wind)e^-kt + g*A
    vel = nb.v("ADD", nb.v("ADD", G("Wind"), nb.v("SCALE", nb.v("SUBTRACT", v0, G("Wind")), scale=ex)),
               nb.v("SCALE", G("Gravity"), scale=A))
    # floor
    ps = nb.sep(p)
    zc = nb.m("MAXIMUM", nb.out(ps, "Z"), G("Floor"))
    clampm = nb.n("FunctionNodeCompare", {"A": G("Floor Mode"), "B": 1}, data_type="INT", operation="EQUAL")
    zz = nb.mixf(nb.out(clampm), nb.out(ps, "Z"), zc)
    p = nb.xyz(nb.out(ps, "X"), nb.out(ps, "Y"), zz)
    killm = nb.n("FunctionNodeCompare", {"A": G("Floor Mode"), "B": 2}, data_type="INT", operation="EQUAL")
    below = nb.m("LESS_THAN", nb.out(ps, "Z"), G("Floor"))
    kill_floor = nb.mul(nb.out(killm), below)
    dead = nb.m("MAXIMUM", nb.m("MAXIMUM", nb.m("LESS_THAN", tau, 0.0), nb.m("GREATER_THAN", age, 1.0)), kill_floor)
    # fade + size
    fin = nb.smooth(age, 0.0, nb.m("MAXIMUM", G("Fade In"), 1e-4))
    fout = nb.sub(1.0, nb.smooth(age, nb.sub(1.0, G("Fade Out")), 1.0))
    fade = nb.mul(fin, fout)
    sz = nb.mul(size, nb.mixf(nb.m("MINIMUM", age, 1.0), 1.0, G("Grow")))
    sz = nb.mul(sz, nb.mixf(nb.out(nb.n("FunctionNodeBooleanMath", {0: G("Shrink")}, operation="NOT")), fade, 1.0))
    # geometry pipeline
    g = nb.out(nb.n("GeometryNodeDeleteGeometry", {"Geometry": G("Geometry"), "Selection": nb.m("GREATER_THAN", dead, 0.5)}, domain="POINT"))
    g = nb.out(nb.n("GeometryNodeSetPosition", {"Geometry": g, "Position": p}))
    for nm, val, dt in (("fx_age", age, "FLOAT"), ("fx_fade", fade, "FLOAT"), ("fx_rnd", rnd, "FLOAT"), ("fx_vel", vel, "FLOAT_VECTOR")):
        g = nb.out(nb.n("GeometryNodeStoreNamedAttribute", {"Geometry": g, "Name": nm, "Value": val}, data_type=dt, domain="POINT"))
    # mode 0: points
    pts = nb.out(nb.n("GeometryNodeMeshToPoints", {"Mesh": g, "Radius": sz}, mode="VERTICES"))
    # instances
    io = nb.n("GeometryNodeObjectInfo", {"Object": G("Instance"), "As Instance": True}, transform_space="ORIGINAL")
    # rotation options
    spin = nb.mul(nb.add(nb.mul(T, G("Spin")), nb.mul(rnd, 6.283)), 1.0)
    rot_rand = nb.out(nb.n("FunctionNodeEulerToRotation", {"Euler": nb.xyz(nb.mul(rnd, 17.0), nb.mul(rnd, 29.0), spin)}))
    rot_vel = nb.out(nb.n("FunctionNodeAlignRotationToVector", {"Vector": vel}, axis="Z", pivot_axis="AUTO"))
    cam = nb.n("GeometryNodeObjectInfo", {"Object": G("Camera")}, transform_space="RELATIVE")
    # camera location in this object's space -> direction from each point to the camera
    to_cam = nb.v("SUBTRACT", nb.out(cam, "Location"), nb.out(nb.n("GeometryNodeInputPosition")))
    rot_cam0 = nb.out(nb.n("FunctionNodeAlignRotationToVector", {"Vector": to_cam}, axis="Z", pivot_axis="AUTO"))
    roll = nb.out(nb.n("FunctionNodeEulerToRotation", {"Euler": nb.xyz(0.0, 0.0, spin)}))
    rot_cam = nb.out(nb.n("FunctionNodeRotateRotation", {"Rotation": rot_cam0, "Rotate By": roll}, rotation_space="LOCAL"))
    mode = G("Mode")
    def is_mode(i):
        return nb.out(nb.n("FunctionNodeCompare", {"A": mode, "B": i}, data_type="INT", operation="EQUAL"))
    rot = nb.out(nb.n("GeometryNodeSwitch", {"Switch": is_mode(2), "False": rot_rand, "True": rot_vel}, input_type="ROTATION"))
    rot = nb.out(nb.n("GeometryNodeSwitch", {"Switch": is_mode(3), "False": rot, "True": rot_cam}, input_type="ROTATION"))
    speed = nb.v("LENGTH", vel)
    sz_streak = nb.xyz(sz, sz, nb.m("MAXIMUM", nb.mul(speed, G("Stretch")), sz))
    scl = nb.out(nb.n("GeometryNodeSwitch", {"Switch": is_mode(2), "False": nb.xyz(sz, sz, sz), "True": sz_streak}, input_type="VECTOR"))
    inst = nb.out(nb.n("GeometryNodeInstanceOnPoints", {"Points": g, "Instance": nb.out(io, "Geometry"), "Rotation": rot, "Scale": scl}))
    # attributes are propagated from points to instances automatically
    use_inst = nb.out(nb.n("FunctionNodeCompare", {"A": mode, "B": 0}, data_type="INT", operation="GREATER_THAN"))
    res = nb.out(nb.n("GeometryNodeSwitch", {"Switch": use_inst, "False": pts, "True": inst}, input_type="GEOMETRY"))
    res = nb.out(nb.n("GeometryNodeSetMaterial", {"Geometry": res, "Material": G("Material")}))
    nb.links.new(res, go.inputs[0])
    _PT_TREE = t
    return t


def _particles(name, p0, v0, birth, life, size, material, frame0=1, time_scale=1.0, gravity=(0, 0, -9.81),
               drag=1.0, wind=(0, 0, 0), turb=0.0, turb_scale=1.0, turb_speed=0.5, turb_ramp=1.0,
               floor=-1e6, floor_mode=0, grow=1.0, fade_in=0.05, fade_out=0.3, shrink=False, mode=0,
               instance=None, camera=None, stretch=0.0, spin=0.0, seed=0, coll=None, rnd=None):
    """Create a closed-form particle object. Arrays: p0 (N,3) object-space, v0 (N,3), birth/life/size (N,)."""
    n = len(birth)
    rng = np.random.default_rng(seed)
    rnd = rng.random(n) if rnd is None else rnd
    o = _points_obj(name, p0, {"v0": np.asarray(v0, np.float32), "birth": birth, "life": life, "size": size, "rnd": rnd}, coll)
    if mode == 3 and camera is None:
        camera = bpy.context.scene.camera
    vals = dict(Frame0=float(frame0), FPS=float(_fps()), Time_Scale=float(time_scale), Gravity=tuple(gravity),
                Drag=float(drag), Wind=tuple(wind), Turb_Amp=float(turb), Turb_Scale=float(turb_scale),
                Turb_Speed=float(turb_speed), Turb_Ramp=float(turb_ramp), Floor=float(floor), Floor_Mode=int(floor_mode),
                Grow=float(grow), Fade_In=float(fade_in), Fade_Out=float(fade_out), Shrink=bool(shrink), Mode=int(mode),
                Stretch=float(stretch), Spin=float(spin), Material=material)
    if instance is not None:
        vals["Instance"] = instance
    if camera is not None:
        vals["Camera"] = camera
    m = _mod(o, _particle_tree(), "Particles", **vals)
    _no_shadow(o)
    return o, m


def _hidden_src(name, mesh_fn, coll=None):
    """Instance source object kept out of render (lives far away, hidden)."""
    o = mesh_fn()
    o.name = name
    o.hide_render = True
    o.hide_viewport = True
    o.location = (0, 0, 0)
    return o


def _quad(name="fx_quad", size=1.0, coll=None):
    s = size / 2
    o = _mesh_obj(name, [(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [(0, 1, 2, 3)], coll)
    uv = o.data.uv_layers.new(name="UVMap")
    for i, lp in enumerate(o.data.loops):
        uv.data[i].uv = [(0, 0), (1, 0), (1, 1), (0, 1)][lp.vertex_index]
    return o


def _streak(name="fx_streak", coll=None):
    """Unit-length streak (z in [-0.5, 0.5]) with radius 1 at the middle, tapered ends."""
    return _lathe(name, [(0, -0.5), (0.5, -0.4), (1.0, -0.1), (1.0, 0.1), (0.5, 0.4), (0, 0.5)], segs=6, coll=coll)


def _ico(name="fx_ico", sub=1, coll=None):
    me = bpy.data.meshes.new(name)
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    bm.to_mesh(me)
    bm.free()
    me.shade_smooth()
    return C.link(bpy.data.objects.new(name, me), coll)


def _cached_src(key, maker):
    o = bpy.data.objects.get(key)
    if o is None:
        o = _hidden_src(key, maker)
    return o


# =============================================================================================
# 1. FLAMES
# =============================================================================================
_FLAME_PROFILE = None


def _flame_profile(rings=14, width=0.13, a=0.5, b=1.1):
    """Teardrop profile (normalised height 1, max radius `width`)."""
    peak = (a / (a + b)) ** a * (b / (a + b)) ** b
    prof = [(0.0, 0.0)]
    for i in range(1, rings):
        s = i / rings
        s2 = s
        prof.append((width * (s2 ** a) * ((1 - s2) ** b) / peak, s))
    prof.append((0.0, 1.0))
    return prof


def _flame_mesh(name, kind="near", width=0.13, coll=None):
    if kind == "far":
        prof = _flame_profile(5, width)
        segs = 8
    elif kind == "tongue":
        prof = _flame_profile(16, width, a=0.55, b=0.7)
        segs = 20
    else:
        prof = _flame_profile(14, width)
        segs = 16
    return _lathe(name, prof, segs=segs, coll=coll)


def _flame_motion_tree():
    name = "FX_FlameMotion"
    if name in bpy.data.node_groups:
        return bpy.data.node_groups[name]
    t, nb, gi, go = _gn_tree(name, [
        ("Geometry", "NodeSocketGeometry"),
        ("Frame0", "NodeSocketFloat", 1.0),
        ("FPS", "NodeSocketFloat", 24.0),
        ("Seed", "NodeSocketFloat", 0.0),
        ("Sway", "NodeSocketFloat", 0.04),        # lateral wobble at the tip, fraction of height
        ("Speed", "NodeSocketFloat", 1.0),
        ("Stretch", "NodeSocketFloat", 0.0),      # animated by f-curve noise (flicker)
        ("Wind", "NodeSocketVector", (0, 0, 0)),  # tip lean, fraction of height
        ("Ripple", "NodeSocketFloat", 0.0),       # surface ripple for big flames
    ])
    G = lambda k: gi.outputs[k]
    st = nb.n("GeometryNodeInputSceneTime")
    T = nb.mul(nb.div(nb.sub(st.outputs["Frame"], G("Frame0")), G("FPS")), G("Speed"))
    pos = nb.out(nb.n("GeometryNodeInputPosition"))
    ps = nb.sep(pos)
    z = nb.m("MAXIMUM", nb.out(ps, "Z"), 0.0)
    w = nb.mul(z, z)
    seedv = nb.xyz(nb.mul(G("Seed"), 7.13), nb.mul(G("Seed"), 3.71), 0.0)
    nzv = nb.v("ADD", nb.xyz(0.0, 0.0, nb.sub(nb.mul(z, 1.3), nb.mul(T, 1.5))), seedv)
    nz = nb.noise(nzv, scale=1.0, detail=1.5, w=T)
    c = nb.v("SCALE", nb.v("SUBTRACT", nb.out(nz, "Color"), (0.5, 0.5, 0.5)), scale=2.0)
    cs = nb.sep(c)
    # surface ripple (licking): 3D noise displacement along the normal, growing with height
    rp = nb.noise(nb.v("ADD", nb.v("MULTIPLY", pos, (6.0, 6.0, 3.0)), nb.v("ADD", seedv, nb.xyz(0, 0, nb.mul(T, -4.0)))), scale=1.0, detail=2.0, w=nb.mul(T, 0.7))
    rpv = nb.mul(nb.sub(nb.out(rp, "Fac"), 0.5), nb.mul(G("Ripple"), z))
    nrm = nb.out(nb.n("GeometryNodeInputNormal"))
    stretch = nb.add(1.0, G("Stretch"))
    thin = nb.m("INVERSE_SQRT", nb.m("MAXIMUM", stretch, 0.2))
    wnd = nb.sep(G("Wind"))
    x = nb.add(nb.mul(nb.out(ps, "X"), thin), nb.mul(w, nb.add(nb.mul(nb.out(cs, "X"), G("Sway")), nb.out(wnd, "X"))))
    y = nb.add(nb.mul(nb.out(ps, "Y"), thin), nb.mul(w, nb.add(nb.mul(nb.out(cs, "Y"), G("Sway")), nb.out(wnd, "Y"))))
    zz = nb.mul(nb.out(ps, "Z"), nb.add(stretch, nb.mul(nb.out(wnd, "Z"), 1.0)))
    newp = nb.v("ADD", nb.xyz(x, y, zz), nb.v("SCALE", nrm, scale=rpv))
    g = nb.out(nb.n("GeometryNodeSetPosition", {"Geometry": G("Geometry"), "Position": newp}))
    nb.links.new(g, go.inputs[0])
    return t


def _flame_material(kind="candle", temp=1850, strength=1.0, name=None):
    """Additive emissive flame shader. Object coords are normalised (z 0..1 base->tip).
    kind: 'candle' (smooth teardrop, blue root), 'far' (cheap, no noise), 'tongue' (ragged licking
    flame for torches / campfires), 'gutter' (candle with stronger internal flicker)."""
    key = name or "FX_flame_%s_%d_%.2f" % (kind, temp, strength)
    if key in bpy.data.materials:
        return bpy.data.materials[key]
    m, nb, out = _new_mat(key)
    tc = nb.n("ShaderNodeTexCoord")
    oc = tc.outputs["Object"]
    ps = nb.sep(oc)
    z = nb.out(ps, "Z")
    lw = nb.n("ShaderNodeLayerWeight", {"Blend": 0.5})
    facing = nb.out(lw, "Facing")
    oi = nb.n("ShaderNodeObjectInfo")
    rnd = oi.outputs["Random"]
    inst_rnd = nb.out(nb.sattr("fx_rnd", "INSTANCER"), "Fac")
    rnd = nb.add(rnd, inst_rnd)
    if kind == "far":
        core = nb.m("POWER", nb.sub(1.0, facing), 1.2)
        body = nb.mul(nb.smooth(z, 0.0, 0.2), nb.sub(1.0, nb.smooth(z, 0.45, 1.0)))
        tK = nb.madd(z, -450.0, temp + 250.0)
        bb = nb.n("ShaderNodeBlackbody", {"Temperature": tK})
        inten = nb.mul(nb.mul(core, body), 28.0 * strength)
        em = nb.n("ShaderNodeEmission", {"Color": bb, "Strength": inten})
    elif kind in ("candle", "gutter"):
        T = _time_value(nb, scale=1.0)
        nvec = nb.v("SUBTRACT", nb.v("MULTIPLY", oc, (6.0, 6.0, 2.5)), nb.xyz(0.0, 0.0, nb.mul(T, 3.0 if kind == "candle" else 5.0)))
        n = nb.out(nb.noise(nb.v("ADD", nvec, nb.v("SCALE", (1.0, 1.0, 1.0), scale=nb.mul(rnd, 50.0))), scale=1.0, detail=2.0), "Fac")
        edge = nb.sub(1.0, facing)
        core = nb.m("POWER", edge, 2.2)
        root = nb.smooth(z, 0.05, 0.3)                 # luminous body starts above the blue root
        tip = nb.sub(1.0, nb.smooth(z, 0.32, 1.0))
        body = nb.mul(root, nb.m("POWER", tip, 0.75))
        flick = nb.madd(n, 0.7 if kind == "candle" else 1.2, 0.65)
        # hotter (yellow-white) in the centre, orange at the rim and the tip
        tK = nb.add(nb.add(nb.madd(core, 650.0, temp - 150.0), nb.mul(z, -450.0)), nb.mul(nb.sub(n, 0.5), 250.0))
        bb = nb.n("ShaderNodeBlackbody", {"Temperature": tK})
        yel = nb.mul(body, nb.mul(nb.madd(core, 11.0, 1.6), nb.mul(flick, strength)))
        # dark-ish inner cone around the wick (less luminous) when viewed through the centre
        inner = nb.mul(nb.sub(1.0, nb.smooth(z, 0.1, 0.42)), nb.sub(1.0, nb.smooth(facing, 0.0, 0.45)))
        yel = nb.mul(yel, nb.sub(1.0, nb.mul(inner, 0.5)))
        blue_amt = nb.mul(nb.mul(nb.sub(1.0, nb.smooth(z, 0.12, 0.34)), nb.m("POWER", edge, 0.8)), 1.6 * strength)
        col = nb.mixc(1.0, nb.v("SCALE", nb.out(bb), scale=yel), nb.v("SCALE", (0.1, 0.25, 1.0), scale=blue_amt), "ADD")
        em = nb.n("ShaderNodeEmission", {"Color": col, "Strength": 1.0})
    else:
        raise ValueError("unknown flame kind %r" % kind)
    tr = nb.n("ShaderNodeBsdfTransparent")
    add = nb.n("ShaderNodeAddShader", {0: em, 1: tr})
    nb.links.new(nb.out(add), out.inputs["Surface"])
    _blended(m, backface=False)
    return m


def _light_flicker(light_obj, energy, amount=0.35, scale=5.0, phase=0.0, depth=1):
    ld = light_obj.data
    ld.energy = energy
    ld.keyframe_insert("energy", frame=1)
    fc = _find_fcurve(ld, "energy")
    if fc is not None and amount:
        _add_noise(fc, scale=scale, strength=2 * amount * energy, phase=phase, depth=depth)
    return fc


def _point_light(name, loc, energy, temp, radius, shadow=True, coll=None, volume=1.0):
    ld = bpy.data.lights.new(name, "POINT")
    ld.energy = energy
    ld.color = C.kelvin(temp)
    ld.shadow_soft_size = radius
    ld.use_shadow = shadow
    ld.volume_factor = volume
    o = C.link(bpy.data.objects.new(name, ld), coll)
    o.location = loc
    return o


def flame(loc=(0, 0, 0), size=0.03, color_temp=1850, flicker=True, seed=0, light=True, light_energy=None,
          light_radius=None, shadow=True, lod="near", wind=(0, 0, 0), strength=1.0, style="candle",
          name="Flame", coll=None, parent=None):
    """Small animated flame (candle / oil-lamp wick) + matching flickering point light.

    loc            base of the flame (the wick tip), world space (or parent space if parent given)
    size           flame height in metres (candle 0.025-0.035, oil lamp 0.03-0.045)
    color_temp     Kelvin of the luminous zone (1700 deep orange .. 2200 yellow)
    flicker        False / True / float amount (1.0 = normal draft, 2.5 = guttering)
    lod            'near' (16x14 lathe, internal noise, sway) | 'far' (8x5, no noise: distant lamps)
    wind           (x, y, z) tip lean as a fraction of the height, e.g. (0.15, 0, 0)
    light_energy   W (default 1.2 * (size/0.03)^2 * strength)
    Returns FX(root, mesh, light, modifier, material).
    """
    rnd = random.Random(seed)
    amt = 0.0 if not flicker else (1.0 if flicker is True else float(flicker))
    root = _empty(name, loc, coll, size=size)
    if parent is not None:
        _parent(root, parent)
        root.location = loc
    kind = "far" if lod == "far" else ("gutter" if amt > 1.6 else style)
    me = _flame_mesh(name + "_mesh", "far" if lod == "far" else "near", coll=coll)
    me.scale = (size, size, size)
    _parent(me, root)
    C.assign(me, _flame_material(kind, color_temp, strength))
    _no_shadow(me)
    mod = None
    if lod != "far":
        mod = _mod(me, _flame_motion_tree(), "FlameMotion", Frame0=1.0, FPS=float(_fps()), Seed=float(rnd.random() * 100),
                   Sway=0.03 + 0.035 * amt, Speed=1.0 + 0.4 * amt, Wind=tuple(wind))
        if amt:
            me.keyframe_insert(_mod_path(mod, "Stretch"), frame=1)
            fc = _find_fcurve(me, _mod_path(mod, "Stretch"))
            if fc:
                _add_noise(fc, scale=4.0 + 2.0 / max(amt, 0.3), strength=0.22 * amt, phase=seed * 13.7 + 1, depth=1)
    lo = None
    if light:
        e = light_energy if light_energy is not None else 1.2 * (size / 0.03) ** 2 * strength
        lo = _point_light(name + "_light", (0, 0, size * 0.42), e, color_temp + 150,
                          light_radius if light_radius is not None else size * 0.12, shadow, coll)
        _parent(lo, root)
        lo.location = (wind[0] * size * 0.3, wind[1] * size * 0.3, size * 0.42)
        if amt:
            _light_flicker(lo, e, amount=min(0.45, 0.16 * amt + 0.06), scale=4.0 + 2.0 / max(amt, 0.3), phase=seed * 13.7 + 1)
    return FX(root, mesh=me, light=lo, modifier=mod, material=me.active_material)


def lamp_field(points, size=0.035, color_temp=1850, flicker=True, lights=16, light_energy=None, shadow=False,
               strength=1.0, seed=0, name="LampField", coll=None):
    """Hundreds of cheap distant lamp flames as ONE geometry-nodes instancer (+ a few cluster lights).

    points       list of world positions (flame bases) or a mesh object whose vertices are used
    lights       number of cluster point lights (0 = none). Each represents a group of lamps.
    light_energy W per lamp (summed per cluster); default 1.5 * (size/0.035)^2
    Returns FX(root, obj, lights=[...], material).
    """
    if isinstance(points, bpy.types.Object):
        mw = points.matrix_world
        pts = [mw @ v.co for v in points.data.vertices]
    else:
        pts = [Vector(p) for p in points]
    P = np.array([tuple(p) for p in pts], np.float32).reshape(-1, 3)
    n = len(P)
    rng = np.random.default_rng(seed)
    root = _empty(name, (0, 0, 0), coll)
    src = _cached_src("FX_src_farflame", lambda: _flame_mesh("FX_src_farflame", "far"))
    obj = _points_obj(name + "_pts", P, {"rnd": rng.random(n)}, coll)
    _parent(obj, root)
    tname = "FX_LampField"
    if tname not in bpy.data.node_groups:
        t, nb, gi, go = _gn_tree(tname, [("Geometry", "NodeSocketGeometry"), ("Instance", "NodeSocketObject"),
                                         ("Size", "NodeSocketFloat", 0.035), ("Flicker", "NodeSocketFloat", 1.0),
                                         ("FPS", "NodeSocketFloat", 24.0), ("Material", "NodeSocketMaterial")])
        G = lambda k: gi.outputs[k]
        st = nb.n("GeometryNodeInputSceneTime")
        T = nb.div(st.outputs["Frame"], G("FPS"))
        r = nb.attr("rnd")
        nz = nb.noise(nb.xyz(nb.mul(r, 91.0), nb.mul(r, 17.0), 0.0), scale=1.0, detail=1.0, w=nb.mul(T, 2.5))
        cs = nb.sep(nb.v("SUBTRACT", nb.out(nz, "Color"), (0.5, 0.5, 0.5)))
        fl = G("Flicker")
        sz = nb.mul(G("Size"), nb.madd(r, 0.3, 0.85))
        sc = nb.xyz(sz, sz, nb.mul(sz, nb.add(1.0, nb.mul(nb.out(cs, "Z"), nb.mul(fl, 0.5)))))
        rot = nb.out(nb.n("FunctionNodeEulerToRotation", {"Euler": nb.xyz(nb.mul(nb.out(cs, "X"), nb.mul(fl, 0.35)),
                                                                         nb.mul(nb.out(cs, "Y"), nb.mul(fl, 0.35)), nb.mul(r, 6.28))}))
        io = nb.n("GeometryNodeObjectInfo", {"Object": G("Instance"), "As Instance": True})
        g = nb.out(nb.n("GeometryNodeStoreNamedAttribute", {"Geometry": G("Geometry"), "Name": "fx_rnd", "Value": r}, data_type="FLOAT", domain="POINT"))
        inst = nb.out(nb.n("GeometryNodeInstanceOnPoints", {"Points": g, "Instance": nb.out(io, "Geometry"), "Rotation": rot, "Scale": sc}))
        inst = nb.out(nb.n("GeometryNodeSetMaterial", {"Geometry": inst, "Material": G("Material")}))
        nb.links.new(inst, go.inputs[0])
    amt = 0.0 if not flicker else (1.0 if flicker is True else float(flicker))
    mat = _flame_material("far", color_temp, strength)
    mod = _mod(obj, bpy.data.node_groups[tname], "LampField", Instance=src, Size=float(size), Flicker=amt,
               FPS=float(_fps()), Material=mat)
    _no_shadow(obj)
    los = []
    if lights and n:
        k = min(lights, n)
        # k-means-lite clustering of lamp positions
        cent = P[rng.choice(n, k, replace=False)].copy()
        for _ in range(8):
            d = ((P[:, None, :] - cent[None, :, :]) ** 2).sum(-1)
            lab = d.argmin(1)
            for j in range(k):
                if (lab == j).any():
                    cent[j] = P[lab == j].mean(0)
        e1 = light_energy if light_energy is not None else 1.5 * (size / 0.035) ** 2 * strength
        for j in range(k):
            members = P[lab == j]
            if not len(members):
                continue
            spread = float(np.sqrt(((members - cent[j]) ** 2).sum(-1).mean())) if len(members) > 1 else size
            lo = _point_light("%s_light%d" % (name, j), tuple(cent[j] + np.array([0, 0, size * 0.5])), e1 * len(members),
                              color_temp + 150, max(size * 0.2, min(spread, 2.0)), shadow, coll)
            lo.data.use_soft_falloff = True
            _parent(lo, root)
            if amt:
                _light_flicker(lo, e1 * len(members), amount=0.12 * amt / math.sqrt(len(members)) + 0.03, scale=6.0, phase=j * 7.1 + seed)
            los.append(lo)
    return FX(root, obj=obj, lights=los, material=mat, modifier=mod)


# ---------------------------------------------------------------------------------------------
# Torch / campfire shared parts
# ---------------------------------------------------------------------------------------------
def _ember_material(name="FX_ember", strength=40.0, temp=1500):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    m, nb, out = _new_mat(name)
    fade = nb.add(nb.out(nb.sattr("fx_fade"), "Fac"), nb.out(nb.sattr("fx_fade", "INSTANCER"), "Fac"))
    age = nb.add(nb.out(nb.sattr("fx_age"), "Fac"), nb.out(nb.sattr("fx_age", "INSTANCER"), "Fac"))
    r = nb.add(nb.out(nb.sattr("fx_rnd"), "Fac"), nb.out(nb.sattr("fx_rnd", "INSTANCER"), "Fac"))
    tK = nb.add(nb.madd(age, -500.0, temp + 400.0), nb.mul(r, 300.0))
    bb = nb.n("ShaderNodeBlackbody", {"Temperature": tK})
    # embers cool + dim with age, random twinkle
    inten = nb.mul(nb.mul(fade, strength), nb.madd(r, 0.8, 0.4))
    em = nb.n("ShaderNodeEmission", {"Color": bb, "Strength": inten})
    nb.links.new(nb.out(em), out.inputs["Surface"])
    return m


def _smoke_material(name="FX_smoke", density=1.0, color=(0.12, 0.115, 0.11), rise=0.6, scale=3.0, top=1.0, anis=0.2):
    """Rising wispy smoke column volume. Object coords: base at z=0, top at z=`top` (object units)."""
    m, nb, out = _new_mat(name)
    T = _time_value(nb)
    oc = nb.n("ShaderNodeTexCoord").outputs["Object"]
    ps = nb.sep(oc)
    z = nb.div(nb.out(ps, "Z"), top)
    r = nb.v("LENGTH", nb.v("MULTIPLY", oc, (1.0, 1.0, 0.0)))
    q = nb.v("SUBTRACT", nb.v("MULTIPLY", oc, (scale, scale, scale * 0.5)), nb.xyz(0.0, 0.0, nb.mul(T, rise * scale * 0.5)))
    warp = nb.noise(q, scale=0.6, detail=1.0)
    n = nb.out(nb.noise(nb.v("ADD", q, nb.v("SCALE", nb.out(warp, "Color"), scale=1.5)), scale=1.0, detail=3.0, rough=0.6), "Fac")
    wisps = nb.smooth(n, 0.5, 0.78)
    # column radius widens with height (object units: radius at top ~ 0.5*top*0.45)
    rad = nb.mul(nb.madd(z, 0.85, 0.15), top * 0.22)
    radial = nb.sub(1.0, nb.smooth(nb.div(r, rad), 0.2, 1.0))
    vert = nb.mul(nb.smooth(z, 0.0, 0.08), nb.sub(1.0, nb.smooth(z, 0.15, 1.0)))
    dens = nb.mul(nb.mul(wisps, nb.mul(radial, vert)), density)
    v = nb.n("ShaderNodeVolumePrincipled", {"Color": color, "Density": dens, "Anisotropy": anis})
    nb.links.new(nb.out(v), out.inputs["Volume"])
    return m


def _char_material(name="FX_char", glow=8.0, temp=1300, scale=70.0, hot_frac=0.5):
    """Charred wood / pitch: black alligator-cracked char with glowing embers in some cracks."""
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    m, nb, out = _new_mat(name)
    T = _time_value(nb, scale=1.0)
    oc = nb.n("ShaderNodeTexCoord").outputs["Object"]
    dist = nb.noise(nb.v("SCALE", oc, scale=scale * 0.15), scale=1.0, detail=2.0)
    vq = nb.v("ADD", nb.v("SCALE", oc, scale=scale), nb.v("SCALE", nb.out(dist, "Color"), scale=1.4))
    vor = nb.n("ShaderNodeTexVoronoi", {"Vector": vq, "Scale": 1.0, "Randomness": 1.0}, feature="DISTANCE_TO_EDGE")
    crack = nb.sub(1.0, nb.smooth(nb.out(vor, "Distance"), 0.0, 0.05))
    n = nb.out(nb.noise(nb.v("SCALE", oc, scale=scale * 0.08), scale=1.0, detail=3.0), "Fac")
    pulse = nb.out(nb.noise(nb.v("SCALE", oc, scale=scale * 0.05), scale=1.0, detail=1.0, w=nb.mul(T, 0.5)), "Fac")
    lo = 0.62 - 0.25 * hot_frac
    hot = nb.mul(nb.smooth(n, lo, lo + 0.12), crack)
    hot = nb.mul(hot, nb.madd(pulse, 1.4, 0.1))
    hot = nb.add(hot, nb.mul(nb.smooth(n, lo + 0.1, lo + 0.3), 0.05))       # faint overall ember glow
    bb = nb.n("ShaderNodeBlackbody", {"Temperature": temp})
    rough_tex = nb.out(nb.noise(nb.v("SCALE", oc, scale=scale * 0.6), scale=1.0, detail=4.0), "Fac")
    base_c = nb.mixc(rough_tex, (0.01, 0.009, 0.008), (0.045, 0.04, 0.035))
    base_c = nb.mixc(nb.mul(crack, 0.6), base_c, (0.004, 0.003, 0.003))
    b = nb.n("ShaderNodeBsdfPrincipled", {"Base Color": base_c, "Roughness": 0.8, "Emission Color": bb,
                                           "Emission Strength": nb.mul(hot, glow)})
    bump = nb.n("ShaderNodeBump", {"Height": nb.add(nb.mul(crack, -0.6), nb.mul(rough_tex, 0.4)), "Distance": 0.003, "Strength": 0.7})
    nb.links.new(nb.out(bump), b.inputs["Normal"])
    nb.links.new(nb.out(b), out.inputs["Surface"])
    return m


def _fire_card_material(temp=1800, strength=1.0, name=None):
    """2D procedural fire for camera-facing cards (UV: u across, v up). Additive."""
    key = name or "FX_firecard_%d_%.2f" % (temp, strength)
    if key in bpy.data.materials:
        return bpy.data.materials[key]
    m, nb, out = _new_mat(key)
    T = _time_value(nb, scale=1.0)
    uv = nb.n("ShaderNodeTexCoord").outputs["UV"]
    ps = nb.sep(uv)
    x = nb.mul(nb.sub(nb.out(ps, "X"), 0.5), 2.0)
    y = nb.out(ps, "Y")
    r = nb.mul(nb.out(nb.sattr("fx_rnd", "INSTANCER"), "Fac"), 53.0)
    # big slow sway, growing with height
    n1 = nb.out(nb.noise(nb.xyz(r, nb.sub(nb.mul(y, 1.3), nb.mul(T, 1.4)), 0.0), scale=1.0, detail=1.0), "Fac")
    x1 = nb.add(x, nb.mul(nb.sub(n1, 0.5), nb.mul(nb.m("POWER", y, 1.4), 1.4)))
    # turbulence scrolling upward
    q = nb.xyz(nb.mul(x1, 1.6), nb.sub(nb.mul(y, 1.25), nb.mul(T, 2.4)), r)
    n2 = nb.out(nb.noise(q, scale=2.4, detail=6.0, rough=0.55, distortion=0.35), "Fac")
    # teardrop envelope
    w = nb.mul(nb.m("POWER", nb.m("MAXIMUM", nb.sub(1.0, y), 0.0), 0.65), 0.9)
    shape = nb.m("MAXIMUM", nb.sub(1.0, nb.div(nb.m("ABSOLUTE", x1), nb.m("MAXIMUM", w, 0.02))), 0.0)
    shape = nb.mul(nb.m("POWER", shape, 0.7), nb.smooth(y, 0.0, 0.12))
    f = nb.add(nb.mul(shape, nb.sub(1.2, nb.mul(y, 0.85))), nb.mul(nb.sub(n2, 0.5), nb.madd(y, 0.9, 0.55)))
    I = nb.smooth(f, 0.22, 0.95)
    tK = nb.madd(I, temp - 700.0, 1150.0)
    bb = nb.n("ShaderNodeBlackbody", {"Temperature": tK})
    inten = nb.mul(nb.m("POWER", I, 1.7), 7.0 * strength)
    em = nb.n("ShaderNodeEmission", {"Color": bb, "Strength": inten})
    tr = nb.n("ShaderNodeBsdfTransparent")
    add = nb.n("ShaderNodeAddShader", {0: em, 1: tr})
    nb.links.new(nb.out(add), out.inputs["Surface"])
    _blended(m, backface=True)
    return m


def _fire_card_tree():
    name = "FX_FireCards"
    if name in bpy.data.node_groups:
        return bpy.data.node_groups[name]
    t, nb, gi, go = _gn_tree(name, [("Geometry", "NodeSocketGeometry"), ("Instance", "NodeSocketObject"),
                                    ("Camera", "NodeSocketObject"), ("FPS", "NodeSocketFloat", 24.0),
                                    ("Flicker", "NodeSocketFloat", 1.0), ("Lean", "NodeSocketVector", (0, 0, 0)),
                                    ("Material", "NodeSocketMaterial")])
    G = lambda k: gi.outputs[k]
    st = nb.n("GeometryNodeInputSceneTime")
    T = nb.div(st.outputs["Frame"], G("FPS"))
    r = nb.attr("rnd")
    w, h = nb.attr("w"), nb.attr("h")
    nz = nb.noise(nb.xyz(nb.mul(r, 71.0), 0.0, 0.0), scale=1.0, detail=1.0, w=nb.mul(T, 2.2))
    cs = nb.sep(nb.v("SUBTRACT", nb.out(nz, "Color"), (0.5, 0.5, 0.5)))
    hh = nb.mul(h, nb.add(1.0, nb.mul(nb.out(cs, "Z"), nb.mul(G("Flicker"), 0.45))))
    cam = nb.n("GeometryNodeObjectInfo", {"Object": G("Camera")}, transform_space="RELATIVE")
    d = nb.v("SUBTRACT", nb.out(cam, "Location"), nb.out(nb.n("GeometryNodeInputPosition")))
    d = nb.v("MULTIPLY", d, (-1.0, -1.0, 0.0))
    rot = nb.out(nb.n("FunctionNodeAlignRotationToVector", {"Vector": d}, axis="Y", pivot_axis="Z"))
    # lean (wind): tilt cards slightly
    lean = nb.sep(G("Lean"))
    tilt = nb.out(nb.n("FunctionNodeEulerToRotation", {"Euler": nb.xyz(nb.out(lean, "Y"), nb.mul(nb.out(lean, "X"), -1.0), 0.0)}))
    rot = nb.out(nb.n("FunctionNodeRotateRotation", {"Rotation": rot, "Rotate By": tilt}, rotation_space="GLOBAL"))
    g = nb.out(nb.n("GeometryNodeStoreNamedAttribute", {"Geometry": G("Geometry"), "Name": "fx_rnd", "Value": r}, data_type="FLOAT", domain="POINT"))
    io = nb.n("GeometryNodeObjectInfo", {"Object": G("Instance"), "As Instance": True})
    inst = nb.out(nb.n("GeometryNodeInstanceOnPoints", {"Points": g, "Instance": nb.out(io, "Geometry"), "Rotation": rot,
                                                         "Scale": nb.xyz(w, 1.0, hh)}))
    inst = nb.out(nb.n("GeometryNodeSetMaterial", {"Geometry": inst, "Material": G("Material")}))
    nb.links.new(inst, go.inputs[0])
    return t


def _card_src():
    def mk():
        o = _mesh_obj("FX_src_firecard", [(-0.5, 0, 0), (0.5, 0, 0), (0.5, 0, 1), (-0.5, 0, 1)], [(0, 1, 2, 3)])
        uv = o.data.uv_layers.new(name="UVMap")
        for i, lp in enumerate(o.data.loops):
            uv.data[i].uv = [(0, 0), (1, 0), (1, 1), (0, 1)][lp.vertex_index]
        return o
    return _cached_src("FX_src_firecard", mk)


def fire_cards(name, cards, temp=1800, strength=1.0, flicker=1.0, lean=(0, 0, 0), seed=0, camera=None, coll=None, parent=None):
    """Low-level: a cluster of camera-facing procedural fire cards (one object).
    cards = [(x, y, z, width, height), ...] in the object's space (z = flame base).
    lean = (x, y, 0) radians tilt for wind. Returns the object."""
    rng = np.random.default_rng(seed)
    P = np.array([c[:3] for c in cards], np.float32)
    o = _points_obj(name, P, {"w": [c[3] for c in cards], "h": [c[4] for c in cards], "rnd": rng.random(len(cards))}, coll)
    if parent is not None:
        _parent(o, parent)
    _mod(o, _fire_card_tree(), "FireCards", Instance=_card_src(), Camera=camera or bpy.context.scene.camera,
         FPS=float(_fps()), Flicker=float(flicker), Lean=tuple(lean), Material=_fire_card_material(temp, strength))
    _no_shadow(o)
    return o


def _embers(name, parent, frame_start, frame_end, rate, origin_radius, origin_z, speed, life, size, wind, seed, coll,
            sparks=False, spread=0.35, rise=0.7, turb=0.25, height_z=0.0):
    fps = _fps()
    rng = np.random.default_rng(seed)
    t0 = (frame_start - 1) / fps - life[1]
    t1 = (frame_end - 1) / fps
    n = max(1, int(rate * (t1 - t0)))
    birth = rng.uniform(t0, t1, n)
    a = rng.uniform(0, 2 * math.pi, n)
    r = origin_radius * np.sqrt(rng.random(n))
    p0 = np.stack([r * np.cos(a), r * np.sin(a), origin_z + rng.uniform(0, height_z, n)], 1)
    v0 = np.stack([rng.normal(0, spread, n), rng.normal(0, spread, n), rng.uniform(0.6, 1.4, n) * speed], 1)
    lf = rng.uniform(life[0], life[1], n)
    sz = rng.uniform(size * 0.5, size * 1.4, n)
    mat = _ember_material("FX_spark" if sparks else "FX_ember", strength=60.0 if sparks else 35.0)
    src = _cached_src("FX_src_streak", lambda: _streak("FX_src_streak"))
    o, md = _particles(name, p0, v0, birth, lf, sz, mat, frame0=1, gravity=(0, 0, rise), drag=1.2, wind=wind,
                       turb=turb, turb_scale=2.5, turb_speed=0.8, turb_ramp=0.6, grow=0.5, fade_in=0.03,
                       fade_out=0.5, shrink=False, mode=2, instance=src, stretch=0.035, seed=seed, coll=coll)
    _parent(o, parent)
    return o, md


def torch(loc=(0, 0, 0), flame_height=0.45, color_temp=1750, frame_start=1, frame_end=None, smoke=True, embers=True,
          stick=True, light_energy=60.0, shadow=True, wind=(0.0, 0.0, 0.0), strength=1.0, seed=0, name="Torch",
          coll=None, parent=None):
    """Hand torch: wooden stick, burning pitch-soaked head, licking flame tongues, smoke column,
    rising embers, flickering light.  loc = TOP of the burning head (where flames start).
    wind = (x, y, z) m/s for embers/smoke drift (flames lean by wind*0.08).
    Returns FX(root, flames=[...], light, smoke, embers, stick, head)."""
    frame_end = frame_end or bpy.context.scene.frame_end
    rnd = random.Random(seed)
    root = _empty(name, loc, coll, size=0.2)
    if parent is not None:
        _parent(root, parent)
        root.location = loc
    parts = {}
    if stick:
        st = C.prim("cylinder", name=name + "_stick", radius=0.022, depth=0.75, vertices=10, loc=(0, 0, 0))
        st.location = (0, 0, -0.12 - 0.375)
        C.assign(st, C.wood_material())
        _parent(st, root)
        hd = C.prim("cylinder", name=name + "_head", radius=0.045, depth=0.14, vertices=14, loc=(0, 0, 0))
        hd.location = (0, 0, -0.07)
        C.displace(hd, strength=0.01, scale=0.05)
        C.assign(hd, _char_material("FX_torch_head", glow=3.0 * strength, scale=140.0, hot_frac=0.6))
        C.shade_smooth(hd)
        _parent(hd, root)
        parts.update(stick=st, head=hd)
    lean = tuple(w * 0.08 for w in wind)
    fh = flame_height
    cards = [(0, 0, -0.03, fh * 0.55, fh * 1.0), (0.012, 0.01, -0.03, fh * 0.45, fh * 0.8),
             (-0.012, -0.01, -0.03, fh * 0.42, fh * 0.65), (0.0, 0.015, -0.02, fh * 0.32, fh * 0.5)]
    parts["flames"] = fire_cards(name + "_fire", cards, color_temp, strength, 1.0, lean=(lean[0], lean[1], 0), seed=seed,
                                 coll=coll, parent=root)
    lo = _point_light(name + "_light", (0, 0, flame_height * 0.35), light_energy * strength, color_temp + 200, 0.06, shadow, coll)
    _parent(lo, root)
    _light_flicker(lo, light_energy * strength, amount=0.3, scale=4.0, phase=seed * 3.3, depth=1)
    parts["light"] = lo
    if smoke:
        sh = 1.6
        sm = C.prim("cylinder", name=name + "_smoke", radius=0.4, depth=sh, vertices=12, loc=(0, 0, 0))
        sm.data.transform(Matrix.Translation((0, 0, sh / 2)))
        sm.location = (wind[0] * 0.1, wind[1] * 0.1, flame_height * 0.55)
        C.assign(sm, _smoke_material(name + "_smoke_vol", density=3.0, rise=0.9, scale=4.0, top=sh))
        _parent(sm, root)
        _no_shadow(sm)
        parts["smoke"] = sm
    if embers:
        eo, emd = _embers(name + "_embers", root, frame_start, frame_end, rate=10, origin_radius=0.04, origin_z=0.0,
                          speed=1.3, life=(0.6, 1.8), size=0.0025, wind=wind, seed=seed + 5, coll=coll, rise=0.8, turb=0.2)
        parts["embers"] = eo
    return FX(root, **parts)


def campfire(loc=(0, 0, 0), size=1.0, color_temp=1700, frame_start=1, frame_end=None, logs=6, stones=True,
             smoke=True, sparks=True, light_energy=350.0, shadow=True, wind=(0.0, 0.0, 0.0), strength=1.0, seed=0,
             name="Campfire", coll=None):
    """Campfire on the ground at `loc` (z = ground). size 1.0 = ~0.9 m wide ring, flames ~0.6 m.
    Logs (bark + charred ends with glowing cracks), stone ring, coal bed, licking flame tongues,
    rising sparks (velocity-stretched streaks), smoke wisps, two flickering lights.
    Returns FX(root, flames, logs, stones, coals, sparks, smoke, lights)."""
    frame_end = frame_end or bpy.context.scene.frame_end
    rnd = random.Random(seed)
    s = size
    root = _empty(name, loc, coll, size=0.3 * s)
    parts = {}
    # coal bed
    coal = C.prim("uv_sphere", name=name + "_coals", radius=0.24 * s, segments=24, ring_count=12, loc=(0, 0, 0))
    coal.scale = (1, 1, 0.18)
    C.displace(coal, strength=0.05 * s, scale=0.08 * s)
    C.assign(coal, _char_material("FX_coals", glow=4.0 * strength, temp=1200, scale=45.0, hot_frac=0.8))
    C.shade_smooth(coal)
    _parent(coal, root)
    parts["coals"] = coal
    # logs (teepee + a couple lying)
    bark = C.mat_pbr("bark_willow", scale=3.0, tint=(0.7, 0.62, 0.55), name="FX_bark")
    charm = _char_material("FX_log_char", glow=5.0 * strength, temp=1250, scale=60.0, hot_frac=0.45)
    lg = []
    for i in range(logs):
        L = (0.55 + 0.2 * rnd.random()) * s
        r = (0.035 + 0.02 * rnd.random()) * s
        cyl = C.prim("cylinder", name="%s_log%d" % (name, i), radius=r, depth=L, vertices=12, loc=(0, 0, 0))
        cyl.data.transform(Matrix.Translation((0, 0, L / 2)))  # origin at log base
        C.displace(cyl, strength=0.006 * s, scale=0.03 * s)
        C.assign(cyl, bark)
        cyl.data.materials.append(charm)
        # upper 40% (inside fire) charred
        for p in cyl.data.polygons:
            if p.center.z > L * 0.5:
                p.material_index = 1
        a = 2 * math.pi * i / logs + rnd.uniform(-0.2, 0.2)
        R = 0.34 * s
        cyl.location = (R * math.cos(a), R * math.sin(a), -0.03 * s)
        tilt = math.asin(min(0.95, (R + 0.03 * s) / L)) + math.radians(rnd.uniform(-4, 4))
        # local +Z tilts toward +X, then +X is turned to point at the fire centre -> teepee
        cyl.rotation_euler = (Matrix.Rotation(a + math.pi, 4, "Z") @ Matrix.Rotation(tilt, 4, "Y")).to_euler()
        C.shade_smooth(cyl)
        _parent(cyl, root)
        lg.append(cyl)
    parts["logs"] = lg
    # stones ring
    if stones:
        rock = C.mat_pbr("rock_boulder_dry", scale=4.0, name="FX_campfire_rock", tint=(0.55, 0.5, 0.45))
        sto = []
        n = 11
        for i in range(n):
            a = 2 * math.pi * i / n + rnd.uniform(-0.1, 0.1)
            rr = 0.48 * s
            sz = (0.07 + 0.04 * rnd.random()) * s
            st = C.prim("ico_sphere", name="%s_stone%d" % (name, i), subdivisions=2, radius=sz, loc=(0, 0, 0))
            st.scale = (1.3, 1.0, 0.7)
            st.location = (rr * math.cos(a), rr * math.sin(a), sz * 0.25)
            st.rotation_euler = (0, 0, a + rnd.uniform(-0.4, 0.4))
            C.displace(st, strength=0.3 * sz, scale=0.4 * sz)
            C.assign(st, rock)
            C.shade_smooth(st)
            _parent(st, root)
            sto.append(st)
        parts["stones"] = sto
    # flames
    lean = tuple(w * 0.08 for w in wind)
    cards = [(0, 0, 0.0, 0.5 * s, 1.05 * s)]
    for i in range(10):
        a = 2 * math.pi * i / 10 + rnd.uniform(-0.3, 0.3)
        rr = (0.05 + 0.15 * rnd.random()) * s
        hh = (1.0 - 0.45 * rr / (0.2 * s)) * s * rnd.uniform(0.6, 0.95)
        cards.append((rr * math.cos(a), rr * math.sin(a), 0.0, hh * rnd.uniform(0.45, 0.65), hh))
    parts["flames"] = fire_cards(name + "_fire", cards, color_temp, strength, 1.0, lean=(lean[0], lean[1], 0), seed=seed,
                                 coll=coll, parent=root)
    # lights
    l1 = _point_light(name + "_light", (0, 0, 0.3 * s), light_energy * strength, color_temp + 200, 0.18 * s, shadow, coll)
    _parent(l1, root)
    _light_flicker(l1, light_energy * strength, amount=0.22, scale=5.0, phase=seed * 2.1, depth=1)
    l2 = _point_light(name + "_light2", (0.12 * s, -0.08 * s, 0.55 * s), light_energy * 0.35 * strength, color_temp + 100, 0.25 * s, False, coll)
    _parent(l2, root)
    _light_flicker(l2, light_energy * 0.35 * strength, amount=0.35, scale=3.0, phase=seed * 2.1 + 40, depth=1)
    parts["lights"] = [l1, l2]
    if sparks:
        so, smd = _embers(name + "_sparks", root, frame_start, frame_end, rate=22, origin_radius=0.18 * s, origin_z=0.1 * s,
                          speed=1.8, life=(0.8, 2.6), size=0.003, wind=wind, seed=seed + 11, coll=coll, sparks=True,
                          spread=0.4, rise=1.0, turb=0.35)
        parts["sparks"] = so
    if smoke:
        sh = 2.8 * s
        sm = C.prim("cylinder", name=name + "_smoke", radius=0.7 * s, depth=sh, vertices=14, loc=(0, 0, 0))
        sm.data.transform(Matrix.Translation((0, 0, sh / 2)))
        sm.location = (wind[0] * 0.1, wind[1] * 0.1, 0.5 * s)
        C.assign(sm, _smoke_material(name + "_smoke_vol", density=1.5, rise=0.7, scale=2.2 / s, top=sh))
        _parent(sm, root)
        _no_shadow(sm)
        parts["smoke"] = sm
    return FX(root, **parts)


# =============================================================================================
# 3. EARTH FROM SPACE
# =============================================================================================
EARTH_FILES = {
    "day": "bluemarble_apr_4096.jpg",                     # NASA Blue Marble NG, April 2004 (public domain), resized
    "night": "dnb_land_ocean_ice.2012.3600x1800.jpg",     # NASA Black Marble 2012 (public domain)
    "clouds": "clouds_4096.jpg",                           # NASA Blue Marble clouds (cloud_combined_8192, PD)
    "water": "water_mask_2700.png",                        # derived from the day map
}
EARTH_URLS = {
    "world.topo.bathy.200404.3x5400x2700.jpg": "https://eoimages.gsfc.nasa.gov/images/imagerecords/73000/73655/world.topo.bathy.200404.3x5400x2700.jpg",
    "dnb_land_ocean_ice.2012.3600x1800.jpg": "https://eoimages.gsfc.nasa.gov/images/imagerecords/79000/79765/dnb_land_ocean_ice.2012.3600x1800.jpg",
    "cloud_combined_2048.jpg": "https://eoimages.gsfc.nasa.gov/images/imagerecords/57000/57747/cloud_combined_2048.jpg",
}


def _earth_file(key):
    """Local path of an Earth texture (cache /opt/assets/earth). Downloads the NASA original if the
    cached file is missing (the original is used directly when no resized copy exists)."""
    fn = EARTH_FILES[key]
    p = os.path.join(EARTH_DIR, fn)
    if os.path.exists(p):
        return p
    os.makedirs(EARTH_DIR, exist_ok=True)
    from . import polyhaven as ph
    src = {"day": "world.topo.bathy.200404.3x5400x2700.jpg", "night": "dnb_land_ocean_ice.2012.3600x1800.jpg",
           "clouds": "cloud_combined_2048.jpg"}.get(key)
    if src is None:
        return None          # water mask: optional
    q = os.path.join(EARTH_DIR, src)
    try:
        return ph._download(EARTH_URLS[src], q)
    except Exception as e:  # offline: earth renders without this layer
        print("fx.earth: missing texture", key, e)
        return None


def _equirect_uv(nb, oc):
    """Object-space position on a sphere -> equirect UV (lon 0 = +X, 90E = +Y, north = +Z)."""
    nrm = nb.v("NORMALIZE", oc)
    ps = nb.sep(nrm)
    lon = nb.m("ARCTAN2", nb.out(ps, "Y"), nb.out(ps, "X"))
    lat = nb.m("ARCSINE", nb.m("MINIMUM", nb.m("MAXIMUM", nb.out(ps, "Z"), -1.0), 1.0))
    u = nb.madd(lon, 1.0 / (2 * math.pi), 0.5)
    v = nb.madd(lat, 1.0 / math.pi, 0.5)
    return nb.xyz(u, v, 0.0), nrm


def _img(nb, path, vec, noncolor=False, interp="Cubic", ext="EXTEND"):
    t = nb.n("ShaderNodeTexImage", interpolation=interp, extension=ext)
    t.image = bpy.data.images.load(path, check_existing=True)
    if noncolor:
        t.image.colorspace_settings.name = "Non-Color"
    nb.set(t, "Vector", vec)
    return t


def _sun_local(nb, lon_sock, decl):
    """Sun direction in globe-local space from sub-solar longitude (radians, socket) + declination (deg)."""
    cd, sd = math.cos(math.radians(decl)), math.sin(math.radians(decl))
    return nb.xyz(nb.mul(nb.m("COSINE", lon_sock), cd), nb.mul(nb.m("SINE", lon_sock), cd), sd)


def _stars_world(strength=1.0, density=1.0, milky=0.0, bg=(0.0, 0.0, 0.0)):
    """Procedural star field world (two voronoi layers + faint milky band)."""
    w = bpy.context.scene.world
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    nb = NB(nt)
    out = nb.n("ShaderNodeOutputWorld")
    d = nb.n("ShaderNodeTexCoord").outputs["Generated"]
    d = nb.v("NORMALIZE", nb.out(nb.n("ShaderNodeNewGeometry"), "Incoming"))
    d = nb.v("SCALE", d, scale=-1.0)
    col = None
    total = None
    for sc, thr, gain, seedo in ((420.0 * density ** 0.5, 0.075, 1.0, 0.0), (160.0, 0.05, 4.0, 3.3), (900.0 * density ** 0.5, 0.09, 0.35, 7.7)):
        vor = nb.n("ShaderNodeTexVoronoi", {"Vector": nb.v("ADD", d, (seedo, seedo, seedo)), "Scale": sc, "Randomness": 1.0}, feature="F1")
        dist = nb.out(vor, "Distance")
        rc = nb.out(vor, "Color")
        rv = nb.sep(rc)
        b = nb.m("POWER", nb.out(rv, "X"), 6.0)          # most stars faint, few bright
        spot = nb.sub(1.0, nb.smooth(dist, 0.0, thr))
        s = nb.mul(nb.mul(spot, b), gain)
        tint = nb.mixc(nb.out(rv, "Y"), (0.75, 0.82, 1.0), (1.0, 0.88, 0.72))
        c = nb.v("SCALE", tint, scale=s)
        col = c if col is None else nb.v("ADD", col, c)
    # faint milky way band
    band_n = nb.v("NORMALIZE", (0.3, 0.55, 0.78))
    lat = nb.m("ABSOLUTE", nb.v("DOT_PRODUCT", d, band_n))
    mw = nb.mul(nb.sub(1.0, nb.smooth(lat, 0.0, 0.28)), nb.out(nb.noise(nb.v("SCALE", d, scale=3.0), scale=1.0, detail=6.0), "Fac"))
    mw = nb.mul(nb.smooth(mw, 0.25, 0.75), milky)
    col = nb.v("ADD", col, nb.v("SCALE", (0.55, 0.6, 0.75), scale=mw))
    col = nb.v("ADD", col, bg)
    bgn = nb.n("ShaderNodeBackground", {"Color": col, "Strength": strength})
    nb.links.new(nb.out(bgn), out.inputs["Surface"])
    return bgn


def earth_from_space(ctx=None, radius=6.371, center=(0, 0, 0), focus=(32.0, 27.0), sunrise_lon=(58.0, -12.0),
                     declination=6.0, frame_start=1, frame_end=None, ease=True, clouds=True, night_lights=True,
                     atmosphere=True, stars=True, camera=True, cam_dist=(4.1, 3.4), cam_offset=(0.0, -0.12),
                     lens=35, sun_energy=4.5, night_strength=3.5, cloud_spin=0.6, name="Earth", coll=None):
    """Earth globe seen from space with a sweeping sunrise terminator (s18a).

    radius        globe radius in scene units (6.371 => 1 unit = 1000 km)
    focus         (lon, lat) degrees turned toward the camera (default: Levant / Arabia / Egypt)
    sunrise_lon   (start, end) longitude of the *morning terminator* at the equator. Sunrise reaches the
                  Middle East first (55E), then Africa / Europe as it sweeps west (to -12).
    declination   sub-solar latitude (April ~ +6)
    camera        True: build an animated camera; cam_dist (start, end) in radii from the centre,
                  cam_offset (x, z) shifts the look-at point in radii (positive z -> globe sits lower).
    Returns FX(root, globe, clouds, atmosphere, sun, camera, sun_lon(frame) -> radians).
    The globe root is rotated so `focus` faces -Y (toward a default camera at -Y).
    """
    fps = _fps()
    sc = bpy.context.scene
    frame_end = frame_end or (ctx.render_frames if ctx else sc.frame_end)
    R = radius
    root = _empty(name, center, coll, size=R * 1.2)
    lon0, lat0 = focus
    root.rotation_euler = (Matrix.Rotation(math.radians(lat0), 4, "X") @ Matrix.Rotation(math.radians(-90 - lon0), 4, "Z")).to_euler()

    def sun_lon(f):
        u = (f - frame_start) / max(1, frame_end - frame_start)
        u = min(1.0, max(0.0, u))
        if ease:
            u = 0.5 - 0.5 * math.cos(math.pi * u) if ease == "inout" else u * (1.15 - 0.15 * u)
        lon = sunrise_lon[0] + (sunrise_lon[1] - sunrise_lon[0]) * u
        return math.radians(lon + 90.0)   # sub-solar longitude = sunrise longitude + 90

    # ---- globe
    bpy.ops.mesh.primitive_uv_sphere_add(segments=160, ring_count=80, radius=R)
    g = bpy.context.active_object
    g.name = name + "_globe"
    g.data.shade_smooth()
    _parent(g, root)
    m, nb, out = _new_mat("FX_earth")
    oc = nb.n("ShaderNodeTexCoord").outputs["Object"]
    uv, nrm = _equirect_uv(nb, oc)
    slon = nb.n("ShaderNodeValue")
    slon.name = slon.label = "sun_lon"
    L = _sun_local(nb, slon.outputs[0], declination)
    ndl = nb.v("DOT_PRODUCT", nrm, L)
    day = _img(nb, _earth_file("day"), uv)
    water = _earth_file("water")
    wm = nb.out(_img(nb, water, uv, noncolor=True), "Color") if water else 0.6
    wmf = nb.out(nb.n("ShaderNodeRGBToBW", {"Color": wm})) if water else 0.6
    # grazing haze + terminator warmth on the surface
    lw = nb.n("ShaderNodeLayerWeight", {"Blend": 0.35})
    haze = nb.mul(nb.m("POWER", nb.out(lw, "Facing"), 2.2), 0.55)
    base = nb.mixc(haze, nb.out(day, "Color"), (0.32, 0.5, 0.95))
    warm = nb.mul(nb.smooth(ndl, -0.02, 0.06), nb.sub(1.0, nb.smooth(ndl, 0.06, 0.28)))
    base = nb.mixc(nb.mul(warm, 0.45), base, (1.0, 0.55, 0.3), "MULTIPLY")
    rough = nb.mixf(wmf, 0.85, 0.32)
    spec = nb.mixf(wmf, 0.2, 0.75)
    b = nb.n("ShaderNodeBsdfPrincipled", {"Base Color": base, "Roughness": rough, "Specular IOR Level": spec})
    if night_lights and _earth_file("night"):
        night = _img(nb, _earth_file("night"), uv)
        nl = nb.out(night, "Color")
        # isolate the city lights (bright, yellow) from the faint blue land backdrop
        nlb = nb.out(nb.n("ShaderNodeRGBToBW", {"Color": nl}))
        cities = nb.m("POWER", nb.smooth(nlb, 0.12, 0.9), 1.6)
        dark = nb.sub(1.0, nb.smooth(ndl, -0.12, 0.04))
        ecol = nb.v("ADD", nb.v("SCALE", (1.0, 0.62, 0.28), scale=nb.mul(cities, night_strength)),
                    nb.v("SCALE", nl, scale=0.025))
        nb.set(b, "Emission Color", nb.v("SCALE", ecol, scale=dark))
        nb.set(b, "Emission Strength", 1.0)
    nb.links.new(nb.out(b), out.inputs["Surface"])
    C.assign(g, m)
    parts = {"globe": g}
    # ---- clouds
    if clouds and _earth_file("clouds"):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=160, ring_count=80, radius=R * 1.006)
        cl = bpy.context.active_object
        cl.name = name + "_clouds"
        cl.data.shade_smooth()
        _parent(cl, root)
        cm, cnb, cout = _new_mat("FX_earth_clouds")
        coc = cnb.n("ShaderNodeTexCoord").outputs["Object"]
        cuv, _ = _equirect_uv(cnb, coc)
        ctex = _img(cnb, _earth_file("clouds"), cuv, noncolor=True)
        a = cnb.m("POWER", cnb.smooth(cnb.out(cnb.n("ShaderNodeRGBToBW", {"Color": cnb.out(ctex, "Color")})), 0.08, 0.85), 1.1)
        bsd = cnb.n("ShaderNodeBsdfPrincipled", {"Base Color": (0.95, 0.95, 0.97), "Roughness": 0.9, "Specular IOR Level": 0.1,
                                                 "Alpha": cnb.mul(a, 0.95)})
        cnb.links.new(cnb.out(bsd), cout.inputs["Surface"])
        cm.surface_render_method = "BLENDED"
        cm.use_backface_culling = True
        C.assign(cl, cm)
        cl.visible_shadow = False
        # slow drift
        cl.rotation_euler = (0, 0, 0)
        C.keys(cl, "rotation_euler", [(1, (0, 0, 0)), (frame_end, (0, 0, math.radians(cloud_spin)))], interp="LINEAR", index=-1)
        parts["clouds"] = cl
    # ---- atmosphere shell
    if atmosphere:
        Rs = R * 1.032
        bpy.ops.mesh.primitive_uv_sphere_add(segments=160, ring_count=80, radius=Rs)
        at = bpy.context.active_object
        at.name = name + "_atmosphere"
        at.data.shade_smooth()
        _parent(at, root)
        am, anb, aout = _new_mat("FX_earth_atmo")
        geo = anb.n("ShaderNodeNewGeometry")
        cos = anb.m("ABSOLUTE", anb.v("DOT_PRODUCT", anb.out(geo, "Normal"), anb.out(geo, "Incoming")))
        bratio = anb.m("SQRT", anb.m("MAXIMUM", anb.sub(1.0, anb.mul(cos, cos)), 0.0))
        k = R / Rs
        h = anb.div(anb.sub(bratio, k), 1.0 - k)           # 0 at the Earth's limb, 1 at the shell edge, <0 over the disc
        outer = anb.mul(anb.m("EXPONENT", anb.mul(anb.m("MAXIMUM", h, 0.0), -5.5)), anb.sub(1.0, anb.smooth(h, 0.85, 1.0)))
        inner = anb.mul(anb.smooth(h, -0.9, 0.0), 0.35)
        prof = anb.mixf(anb.m("GREATER_THAN", h, 0.0), inner, outer)
        aoc = anb.n("ShaderNodeTexCoord").outputs["Object"]
        anrm = anb.v("NORMALIZE", aoc)
        aslon = anb.n("ShaderNodeValue")
        aslon.name = aslon.label = "sun_lon"
        aL = _sun_local(anb, aslon.outputs[0], declination)
        andl = anb.v("DOT_PRODUCT", anrm, aL)
        lit = anb.smooth(andl, -0.22, 0.3)
        twi = anb.mul(anb.smooth(andl, -0.16, -0.01), anb.sub(1.0, anb.smooth(andl, -0.01, 0.14)))
        colr = anb.v("ADD", anb.v("SCALE", (0.28, 0.55, 1.0), scale=lit), anb.v("SCALE", (1.0, 0.42, 0.12), scale=anb.mul(twi, 0.55)))
        em = anb.n("ShaderNodeEmission", {"Color": colr, "Strength": anb.mul(prof, 3.2)})
        tr = anb.n("ShaderNodeBsdfTransparent")
        ad = anb.n("ShaderNodeAddShader", {0: em, 1: tr})
        anb.links.new(anb.out(ad), aout.inputs["Surface"])
        _blended(am, backface=False)
        C.assign(at, am)
        _no_shadow(at)
        parts["atmosphere"] = at
    # ---- sun lamp + shared sun_lon animation
    sun = C.link(bpy.data.objects.new(name + "_sun", bpy.data.lights.new(name + "_sun", "SUN")), coll)
    sun.data.energy = sun_energy
    sun.data.color = C.kelvin(5800)
    sun.data.angle = math.radians(0.6)
    sun.data.use_shadow = False      # a globe needs no shadow maps (and animated sun shadows grow memory per frame)
    mats = [m] + ([parts["atmosphere"].active_material] if atmosphere else [])
    Rg = root.matrix_world.to_3x3() if root.parent is None else root.matrix_world.to_3x3()
    Rg = (Matrix.Rotation(math.radians(lat0), 3, "X") @ Matrix.Rotation(math.radians(-90 - lon0), 3, "Z"))
    cd, sd = math.cos(math.radians(declination)), math.sin(math.radians(declination))
    for f in range(1, frame_end + 1):
        a = sun_lon(f)
        for mm in mats:
            s = mm.node_tree.nodes["sun_lon"].outputs[0]
            s.default_value = a
            s.keyframe_insert("default_value", frame=f)
        Lw = Rg @ Vector((math.cos(a) * cd, math.sin(a) * cd, sd))
        sun.rotation_euler = (-Lw).to_track_quat("-Z", "Y").to_euler()
        sun.keyframe_insert("rotation_euler", frame=f)
    for mm in mats:
        _set_fcurves_linear(mm.node_tree, "sun_lon", extrapolate=False)
    C._set_interp(sun, "rotation_euler", "LINEAR")
    parts["sun"] = sun
    if stars:
        _stars_world(strength=1.0 if stars is True else float(stars))
    cam = None
    if camera:
        cam = C.camera((0, -R * cam_dist[0], 0), (0, 0, 0), lens=lens, clip_end=R * 50)
        cam.data.clip_start = R * 0.01

        def path(f):
            u = (f - 1) / max(1, frame_end - 1)
            u = 0.5 - 0.5 * math.cos(math.pi * u)
            d = cam_dist[0] + (cam_dist[1] - cam_dist[0]) * u
            loc = Vector(center) + Vector((R * cam_offset[0] * 0.3, -R * d, R * cam_offset[1] * 0.3))
            tgt = Vector(center) + Vector((R * cam_offset[0], 0, R * cam_offset[1]))
            return loc, tgt
        C.animate_camera(cam, path, 1, frame_end)
        parts["camera"] = cam
    fx = FX(root, **parts)
    fx.sun_lon = sun_lon
    return fx


# =============================================================================================
# Shared: wetness injection, spray billboards, HDRI alignment
# =============================================================================================
def _macro_variation(m, scale=0.015, amount=0.4, tint=(0.8, 0.8, 0.8)):
    """Break visible texture tiling: multiply base colour by large-scale world-space noise and tint."""
    nt = m.node_tree
    nb = NB(nt)
    b = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled")
    s = b.inputs["Base Color"]
    if not s.is_linked:
        return m
    src = s.links[0].from_socket
    pos = nb.out(nb.n("ShaderNodeNewGeometry"), "Position")
    n = nb.out(nb.noise(nb.v("SCALE", pos, scale=scale), scale=1.0, detail=3.0), "Fac")
    n2 = nb.out(nb.noise(nb.v("SCALE", pos, scale=scale * 4.0), scale=1.0, detail=2.0), "Fac")
    f = nb.smooth(nb.add(n, nb.mul(nb.sub(n2, 0.5), 0.5)), 0.3, 0.7)
    col = nb.mixc(nb.mul(f, amount), src, nb.v("MULTIPLY", src, tint))
    col = nb.v("SCALE", col, scale=nb.madd(n2, 0.35, 0.82))
    nb.links.new(col, s)
    return m


def hdri_rotation_for_sun(sun_azimuth_dir=(0.0, 1.0), sun_u=0.600):
    """Degrees for core.world_hdri(rotation=...) that put a Poly Haven HDRI's sun (image u = sun_u; 0.600
    for almost every Poly Haven sky) in the world direction sun_azimuth_dir = (x, y).
    Blender equirect: u = 0.5 - atan2(y, x) / 2pi; the Mapping node rotates the lookup vector."""
    phi_img = (0.5 - sun_u) * 2 * math.pi
    theta_t = math.atan2(sun_azimuth_dir[1], sun_azimuth_dir[0])
    return math.degrees(phi_img - theta_t)


def wet_material(m, wetness=0.8, puddles=0.35, puddle_scale=0.06, ripples=0.0, ripple_dir=(1.0, 0.0),
                 ripple_len=0.45, darken=0.45, mask=None):
    """Inject wetness into an existing Principled material (e.g. core.mat_pbr): darker albedo, lower
    roughness, mirror-flat puddles in the noise lows (world space), optional sand ripples (bump).
    mask: optional callable(nb) -> float socket (0..1) limiting the effect (e.g. an animated wet patch).
    Returns the material (modified in place)."""
    nt = m.node_tree
    nb = NB(nt)
    b = nt.nodes.get("Principled BSDF") or next(n for n in nt.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled")

    def src(name):
        s = b.inputs[name]
        if s.is_linked:
            return s.links[0].from_socket
        return s.default_value if not hasattr(s.default_value, "__len__") else tuple(s.default_value)

    pos = nb.out(nb.n("ShaderNodeNewGeometry"), "Position")
    wet = wetness if mask is None else nb.mul(mask(nb), wetness)
    n = nb.out(nb.noise(nb.v("SCALE", pos, scale=puddle_scale), scale=1.0, detail=3.0, rough=0.55), "Fac")
    pud = nb.smooth(n, 0.62 - 0.35 * puddles, 0.66 - 0.35 * puddles) if puddles > 0 else 0.0
    if puddles > 0 and mask is not None:
        pud = nb.mul(pud, mask(nb))
    if not isinstance(wet, float) or wet:
        base = src("Base Color")
        dark = nb.mixc(nb.add(nb.mul(wet, 1.0), 0.0) if not isinstance(wet, float) else wet, base, nb.v("SCALE", base, scale=darken), "MIX")
        dark = nb.mixc(pud, dark, nb.v("SCALE", base, scale=darken * 0.6))
        nb.links.new(dark, b.inputs["Base Color"])
        r = src("Roughness")
        r2 = nb.mixf(wet, r, nb.mul(r, 0.25))
        r2 = nb.mixf(pud, r2, 0.03)
        nb.links.new(r2, b.inputs["Roughness"])
    nrm = b.inputs["Normal"].links[0].from_socket if b.inputs["Normal"].is_linked else None
    flat = nb.out(nb.n("ShaderNodeNewGeometry"), "Normal")
    if ripples:
        d = nb.v("NORMALIZE", (ripple_dir[0], ripple_dir[1], 0.0))
        ph = nb.v("DOT_PRODUCT", pos, d)
        wob = nb.out(nb.noise(nb.v("SCALE", pos, scale=0.35), scale=1.0, detail=2.0), "Fac")
        wave = nb.m("SINE", nb.add(nb.mul(ph, 2 * math.pi / ripple_len), nb.mul(wob, 6.0)))
        wave = nb.m("POWER", nb.madd(wave, 0.5, 0.5), 1.6)
        bump = nb.n("ShaderNodeBump", {"Height": wave, "Distance": 0.012 * ripples, "Strength": 1.0})
        if nrm is not None:
            nb.links.new(nrm, bump.inputs["Normal"])
        nrm = nb.out(bump)
    if nrm is not None or puddles > 0:
        base_n = nrm if nrm is not None else flat
        fin = nb.mixv(pud, base_n, flat) if puddles > 0 else base_n
        nb.links.new(fin, b.inputs["Normal"])
    return m


def _spray_material(name="FX_spray", color=(0.92, 0.95, 1.0), opacity=0.55, glow=0.0, soft=1.0):
    """Soft noisy billboard puff (quad UVs), lit (diffuse + translucent for backlight), alpha by fx_fade."""
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    m, nb, out = _new_mat(name)
    uv = nb.n("ShaderNodeTexCoord").outputs["UV"]
    c = nb.v("SUBTRACT", uv, (0.5, 0.5, 0.0))
    r = nb.mul(nb.v("LENGTH", c), 2.0)
    rr = nb.out(nb.sattr("fx_rnd", "INSTANCER"), "Fac")
    fade = nb.out(nb.sattr("fx_fade", "INSTANCER"), "Fac")
    age = nb.out(nb.sattr("fx_age", "INSTANCER"), "Fac")
    nq = nb.v("ADD", nb.v("SCALE", uv, scale=3.0), nb.xyz(nb.mul(rr, 31.0), nb.mul(age, 0.8), nb.mul(rr, 7.0)))
    n = nb.out(nb.noise(nq, scale=1.4, detail=5.0, rough=0.6, distortion=0.3), "Fac")
    blob = nb.sub(1.0, nb.smooth(r, 0.15 * soft, 1.0))
    a = nb.mul(nb.smooth(nb.add(nb.mul(blob, 0.9), nb.mul(nb.sub(n, 0.5), 1.3)), 0.25, 0.85), nb.mul(fade, opacity))
    dif = nb.n("ShaderNodeBsdfDiffuse", {"Color": color})
    trl = nb.n("ShaderNodeBsdfTranslucent", {"Color": color})
    mx = nb.n("ShaderNodeMixShader", {0: 0.55, 1: dif, 2: trl})
    if glow:
        em = nb.n("ShaderNodeEmission", {"Color": color, "Strength": glow})
        mx = nb.n("ShaderNodeAddShader", {0: mx, 1: em})
    tr = nb.n("ShaderNodeBsdfTransparent")
    fin = nb.n("ShaderNodeMixShader", {0: a, 1: tr, 2: mx})
    nb.links.new(nb.out(fin), out.inputs["Surface"])
    _blended(m, backface=True)
    return m


# =============================================================================================
# 2. RED SEA
# =============================================================================================
class _SeaFloor:
    """Seabed height: 0 in the middle of the crossing, rising smoothly to sea level (= wall height H)
    at both shores, then dry land beyond. Corridor runs along +Y."""

    def __init__(self, H, y0, y1, slope, land=3.0):
        self.H, self.y0, self.y1, self.slope, self.land = H, y0, y1, slope, land

    def __call__(self, x, y):
        H, y0, y1, sl = self.H, self.y0, self.y1, self.slope

        def ss(t):
            t = min(1.0, max(0.0, t))
            return t * t * (3 - 2 * t)
        up = max(ss((y - (y1 - sl)) / sl), ss(((y0 + sl) - y) / sl))
        z = (H + self.land) * up
        # gentle cross-profile: slightly lower in the middle, small undulation
        z += 0.25 * (abs(x) / 30.0) ** 2 + 0.35 * math.sin(x * 0.11 + y * 0.037) * math.sin(y * 0.021)
        return z


def _sea_wall_tree():
    name = "FX_SeaWall"
    if name in bpy.data.node_groups:
        return bpy.data.node_groups[name]
    t, nb, gi, go = _gn_tree(name, [
        ("Geometry", "NodeSocketGeometry"),
        ("Frame0", "NodeSocketFloat", 1.0), ("FPS", "NodeSocketFloat", 24.0), ("Time Scale", "NodeSocketFloat", 1.0),
        ("Side", "NodeSocketFloat", 1.0), ("Amp", "NodeSocketFloat", 1.6), ("Crest Amp", "NodeSocketFloat", 2.2),
        ("Half Width", "NodeSocketFloat", 18.0), ("Height", "NodeSocketFloat", 45.0),
        ("Collapse T0", "NodeSocketFloat", 1e6), ("Collapse Dur", "NodeSocketFloat", 3.0),
        ("Zip Y0", "NodeSocketFloat", 0.0), ("Zip Speed", "NodeSocketFloat", 1e6),
        ("Material", "NodeSocketMaterial"),
    ])
    G = lambda k: gi.outputs[k]
    st = nb.n("GeometryNodeInputSceneTime")
    T = nb.mul(nb.div(nb.sub(st.outputs["Frame"], G("Frame0")), G("FPS")), G("Time Scale"))
    pos = nb.out(nb.n("GeometryNodeInputPosition"))
    ps = nb.sep(pos)
    x, y, z = nb.out(ps, "X"), nb.out(ps, "Y"), nb.out(ps, "Z")
    k = nb.attr("fx_k")          # 0 foot .. 1 crest (face), >1 top surface
    top = nb.attr("fx_top")      # 0 face .. 1 flat top
    hgt = nb.attr("fx_h")        # local wall height (m)
    face = nb.sub(1.0, top)
    crest = nb.mul(nb.smooth(k, 0.7, 0.98), nb.sub(1.0, nb.smooth(top, 0.3, 1.0)))
    # big slow bulges + medium churn (flowing upward on the face)
    q1 = nb.v("ADD", nb.v("MULTIPLY", pos, (0.035, 0.035, 0.05)), nb.xyz(0.0, nb.mul(T, 0.02), nb.mul(T, -0.08)))
    n1 = nb.out(nb.noise(q1, scale=1.0, detail=1.0, w=nb.mul(T, 0.07)), "Fac")
    q2 = nb.v("ADD", nb.v("MULTIPLY", pos, (0.14, 0.14, 0.18)), nb.xyz(0.0, 0.0, nb.mul(T, -0.45)))
    n2 = nb.out(nb.noise(q2, scale=1.0, detail=2.0, w=nb.mul(T, 0.3)), "Fac")
    scale_h = nb.m("MINIMUM", nb.div(hgt, 30.0), 1.0)
    dface = nb.mul(nb.add(nb.mul(nb.sub(n1, 0.5), 2.0), nb.mul(nb.sub(n2, 0.5), 0.9)), nb.mul(G("Amp"), nb.mul(face, scale_h)))
    dface = nb.mul(dface, nb.madd(crest, 1.2, 0.5))
    # crest: rolling, heaving lip
    q3 = nb.v("ADD", nb.v("MULTIPLY", pos, (0.06, 0.06, 0.06)), nb.xyz(0.0, nb.mul(T, 0.35), 0.0))
    n3 = nb.out(nb.noise(q3, scale=1.0, detail=2.0, w=nb.mul(T, 0.25)), "Fac")
    dz = nb.mul(nb.mul(nb.sub(n3, 0.5), 2.0), nb.mul(G("Crest Amp"), nb.mul(crest, scale_h)))
    dx = nb.mul(G("Side"), nb.add(dface, nb.mul(nb.mul(nb.sub(n3, 0.45), -1.6), nb.mul(crest, scale_h))))
    # collapse (zipper along Y): c 0..1
    tl = nb.sub(nb.sub(T, G("Collapse T0")), nb.div(nb.m("ABSOLUTE", nb.sub(y, G("Zip Y0"))), G("Zip Speed")))
    c = nb.smooth(nb.div(tl, G("Collapse Dur")), 0.0, 1.0)
    c = nb.mul(c, c)
    kk = nb.m("MINIMUM", k, 1.0)
    # walls move inward (tops lead -> topple), and slump downward
    inward = nb.mul(nb.mul(G("Side"), -1.0), nb.mul(c, nb.mul(G("Half Width"), nb.madd(kk, 0.9, 0.55))))
    inward = nb.mul(inward, nb.sub(1.0, top))
    slump = nb.mul(nb.mul(c, c), nb.mul(nb.sub(z, nb.sub(z, nb.mul(hgt, kk))), -0.55))
    newp = nb.xyz(nb.add(nb.add(x, dx), inward), y, nb.add(nb.add(z, dz), slump))
    g = nb.out(nb.n("GeometryNodeSetPosition", {"Geometry": G("Geometry"), "Position": newp}))
    g = nb.out(nb.n("GeometryNodeStoreNamedAttribute", {"Geometry": g, "Name": "fx_c", "Value": c}, data_type="FLOAT", domain="POINT"))
    g = nb.out(nb.n("GeometryNodeSetShadeSmooth", {"Geometry": g, "Shade Smooth": True}))
    g = nb.out(nb.n("GeometryNodeSetMaterial", {"Geometry": g, "Material": G("Material")}))
    nb.links.new(g, go.inputs[0])
    return t


def _sea_wall_material(name="FX_seawall", glow=1.0, foam=1.0, deep=(0.002, 0.016, 0.02), teal=(0.02, 0.4, 0.33)):
    """Water-wall shader: dark deep body, glossy large-scale chop, emerald translucency near the crest with
    vertical light shafts, crest / foot foam and sparse foam streaks. (Kept to 4 noise lookups for speed.)"""
    m, nb, out = _new_mat(name)
    T = _time_value(nb)
    pos = nb.n("ShaderNodeTexCoord").outputs["Object"]
    k = nb.out(nb.sattr("fx_k"), "Fac")
    top = nb.out(nb.sattr("fx_top"), "Fac")
    c = nb.out(nb.sattr("fx_c"), "Fac")
    kk = nb.m("MINIMUM", k, 1.0)
    face = nb.sub(1.0, top)
    # large-scale chop (bump), flowing upward slowly
    q = nb.v("ADD", nb.v("SCALE", pos, scale=0.28), nb.xyz(0.0, 0.0, nb.mul(T, -0.25)))
    h1 = nb.out(nb.noise(q, scale=1.0, detail=3.0, rough=0.5), "Fac")
    # foam / bubbles: one noise for blotches, one vertically stretched for streaks
    fq2 = nb.v("ADD", nb.v("MULTIPLY", pos, (0.45, 0.45, 0.45)), nb.xyz(0.0, nb.mul(T, 0.25), nb.mul(T, -0.35)))
    blot = nb.out(nb.noise(fq2, scale=1.0, detail=3.0, rough=0.6), "Fac")
    fq = nb.v("ADD", nb.v("SCALE", pos, scale=0.09), nb.xyz(0.0, nb.mul(T, 0.03), nb.mul(T, -0.05)))
    streak = nb.out(nb.noise(fq, scale=1.0, detail=3.0, rough=0.55, distortion=1.2), "Fac")
    crest_f = nb.mul(nb.smooth(kk, 0.86, 0.98), nb.smooth(blot, 0.38, 0.55))
    crest_f = nb.mul(crest_f, nb.sub(1.0, nb.smooth(top, 0.5, 1.0)))
    foot_f = nb.mul(nb.sub(1.0, nb.smooth(kk, 0.0, 0.06)), nb.smooth(blot, 0.42, 0.55))
    face_f = nb.mul(nb.mul(nb.mul(nb.smooth(streak, 0.66, 0.7), nb.smooth(blot, 0.5, 0.6)), face), nb.mul(nb.smooth(kk, 0.3, 0.9), 0.6))
    top_f = nb.mul(top, nb.smooth(blot, 0.62, 0.72))
    # collapse whitewater: leading crest + lower half as the walls meet
    churn = nb.mul(nb.smooth(c, 0.1, 0.7), nb.smooth(blot, 0.36, 0.5))
    churn = nb.mul(churn, nb.add(nb.smooth(kk, 0.75, 0.95), nb.mul(nb.smooth(c, 0.6, 0.95), 0.7)))
    fm = nb.m("MINIMUM", nb.mul(nb.add(nb.add(nb.add(crest_f, foot_f), nb.add(face_f, top_f)), churn), foam), 1.0)
    # translucent glow: light entering through the crest, vertical shafts inside the water
    # depth variation: large swirling lighter / darker masses inside the water (reuses the swirl noise)
    g = nb.madd(nb.m("POWER", kk, 2.6), 1.0, 0.025)
    g = nb.mul(g, nb.madd(nb.smooth(streak, 0.3, 0.7), 1.3, 0.25))
    g = nb.mul(g, face)
    ecol = nb.v("SCALE", teal, scale=nb.mul(g, glow))
    base = nb.mixc(nb.mul(nb.m("POWER", kk, 2.5), 0.5), deep, nb.v("SCALE", teal, scale=0.2))
    base = nb.mixc(fm, base, (0.72, 0.8, 0.8))
    rough = nb.mixf(fm, 0.1, 0.6)
    # without ray tracing the probe reflects only the bright sky; the lower wall would really mirror the
    # dark opposite wall + seabed -> fade the specular toward the foot (set raytracing for true reflections)
    spec = nb.mixf(fm, nb.mixf(top, nb.madd(nb.smooth(kk, 0.15, 0.95), 0.36, 0.05), 0.5), 0.5)
    b = nb.n("ShaderNodeBsdfPrincipled", {"Base Color": base, "Roughness": rough, "IOR": 1.33, "Specular IOR Level": spec,
                                           "Emission Color": ecol, "Emission Strength": nb.sub(1.0, nb.mul(fm, 0.8))})
    bump = nb.n("ShaderNodeBump", {"Height": h1, "Distance": 0.4, "Strength": 0.3})
    nb.links.new(nb.out(bump), b.inputs["Normal"])
    nb.links.new(nb.out(b), out.inputs["Surface"])
    return m


def _sea_wall_mesh(name, side, floor, W2, H, y0, y1, dy=1.25, coll=None):
    """Wall mesh following the seabed. side +1 = right wall (x > 0)."""
    face_ctrl = [(-2.6, -0.03), (-1.8, 0.0), (-0.7, 0.025), (0.0, 0.08), (0.45, 0.3), (0.65, 0.55), (0.55, 0.75),
                 (0.25, 0.88), (-0.35, 0.95), (-0.95, 0.985), (-1.15, 1.0)]
    top_ctrl = [(-0.6, 1.012), (0.6, 1.02), (2.5, 1.01), (6.0, 1.0), (14.0, 1.0), (30.0, 1.0), (60.0, 1.0)]
    ny = int((y1 - y0) / dy) + 1
    # fixed sample count per control segment (from the full height) -> identical topology on every row
    nsegs = []
    for (dxa, ka), (dxb, kb) in zip(face_ctrl[:-1], face_ctrl[1:]):
        nsegs.append(max(1, int(math.hypot((dxb - dxa) * 1.6, (kb - ka) * H) / 1.1)))
    verts, attrs_k, attrs_top, attrs_h = [], [], [], []
    for j in range(ny):
        y = y0 + (y1 - y0) * j / (ny - 1)
        fz = floor(side * W2, y)
        h = max(0.0, H - fz)
        sc = min(1.0, h / 30.0) * (h / 45.0) ** 0.3 if h > 0 else 0.0
        pts = [(dx * max(sc, 0.05) * 1.6, fz + kk * h) for dx, kk in face_ctrl]
        row = []
        for si, ((a, b), (ka, kb)) in enumerate(zip(zip(pts[:-1], pts[1:]), zip([k for _, k in face_ctrl][:-1], [k for _, k in face_ctrl][1:]))):
            n = nsegs[si]
            for i in range(n):
                t = i / n
                row.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, ka + (kb - ka) * t, 0.0))
        for dx, kk in top_ctrl:
            row.append((dx * (1.6 if dx < 3 else 1.0) * max(sc, 0.05), fz + kk * h if h > 0 else H, kk,
                        min(1.0, max(0.0, (dx - 1.0) / 6.0))))
        for px, pz, kk, tp in row:
            verts.append((side * (W2 + px), y, pz))
            attrs_k.append(kk)
            attrs_top.append(tp)
            attrs_h.append(h)
    maxn = len(verts) // ny
    faces = []
    for j in range(ny - 1):
        for i in range(maxn - 1):
            a = j * maxn + i
            b = a + maxn
            faces.append((a, a + 1, b + 1, b) if side > 0 else (a, b, b + 1, a + 1))
    o = _mesh_obj(name, verts, faces, coll)
    me = o.data
    for nm, arr in (("fx_k", attrs_k), ("fx_top", attrs_top), ("fx_h", attrs_h)):
        at = me.attributes.new(nm, "FLOAT", "POINT")
        at.data.foreach_set("value", np.asarray(arr, np.float32))
    return o


def red_sea(ctx=None, length=640.0, width=36.0, height=45.0, center_y=0.0, shore_slope=150.0, lighting=True,
            sun_elevation=7.0, spray=True, spray_rate=0.12, mist=True, mist_density=0.0022, haze=0.0006, collapse=None,
            zipper=(None, 60.0), seabed="coast_sand_rocks_02", seabed_scale=0.25, puddles=0.12, glow=1.0, foam=1.0,
            frame_start=1, frame_end=None, wind=(0.0, 2.0, 0.6), seed=0, name="RedSea", coll=None):
    """The parted Red Sea (s04a / s04b). Corridor along +Y (toward the far shore and the dawn sun),
    centred on x = 0, seabed z = 0 at the deepest point, walls `height` m (top = sea level).

    length       distance between the two shorelines (m); the seabed rises over `shore_slope` m at each end
    width        corridor width at the floor (m)
    lighting     True: sunrise HDRI (sun low over the far shore, +Y) + matching sun lamp
    spray        crest spray billboards blown into the corridor (spray_rate: puffs per metre of crest per s)
    mist         low fog volume along the corridor (core.fog_box)
    collapse     None or (start_frame, duration_frames): walls crash together (s04b). zipper = (y_start, m/s)
                 makes the collapse start at y_start and travel along the corridor (y_start None = far end).
    Returns FX(root, walls=[L, R], seabed, sea, spray, mist, sun, floor_at(x, y) -> z, corridor dict).
    """
    sc = bpy.context.scene
    fps = _fps()
    frame_end = frame_end or (ctx.render_frames if ctx else sc.frame_end)
    rng = np.random.default_rng(seed)
    root = _empty(name, (0, 0, 0), coll, size=5)
    H, W2 = height, width / 2
    y0, y1 = center_y - length / 2, center_y + length / 2
    floor = _SeaFloor(H, y0, y1, shore_slope)
    parts = {}
    # ---- seabed (corridor + under walls + dry land beyond both shores)
    xs = np.concatenate([np.linspace(-W2 - 70, -W2 - 6, 12), np.arange(-W2 - 6, W2 + 6.01, 1.0), np.linspace(W2 + 6, W2 + 70, 12)[1:]])
    xs = np.unique(np.round(xs, 3))
    ys = np.arange(y0 - 120, y1 + 120.01, 1.5)
    V = [(x, y, floor(x, y)) for y in ys for x in xs]
    nx = len(xs)
    F = [(j * nx + i, j * nx + i + 1, (j + 1) * nx + i + 1, (j + 1) * nx + i) for j in range(len(ys) - 1) for i in range(nx - 1)]
    bed = _mesh_obj(name + "_seabed", V, F, coll, smooth=True)
    bm = C.mat_pbr(seabed, scale=seabed_scale, name="FX_seabed", tint=(0.5, 0.44, 0.36), bump=1.0)
    _macro_variation(bm, scale=0.012, amount=0.45, tint=(0.75, 0.8, 0.85))
    wet_material(bm, wetness=0.9, puddles=puddles, puddle_scale=0.16, ripples=1.0, ripple_dir=(1.0, 0.15), ripple_len=0.6,
                 darken=0.4)
    C.assign(bed, bm)
    _parent(bed, root)
    parts["seabed"] = bed
    # ---- walls
    wm = _sea_wall_material(name + "_wallmat", glow=glow, foam=foam)
    walls = []
    T0 = 1e6
    zip_y, zip_v = zipper
    if collapse:
        T0 = (collapse[0] - frame_start) / fps
    for side in (-1, 1):
        w = _sea_wall_mesh("%s_wall%s" % (name, "L" if side < 0 else "R"), side, floor, W2, H, y0 - 10, y1 + 10, coll=coll)
        md = _mod(w, _sea_wall_tree(), "SeaWall", Frame0=float(frame_start), FPS=float(fps), Side=float(side),
                  Half_Width=float(W2), Height=float(H), Collapse_T0=float(T0),
                  Collapse_Dur=float((collapse[1] / fps) if collapse else 3.0),
                  Zip_Y0=float(zip_y if zip_y is not None else center_y - length * 0.2), Zip_Speed=float(zip_v or 1e6),
                  Material=wm)
        C.assign(w, wm)
        _parent(w, root)
        walls.append(w)
    parts["walls"] = walls
    # ---- open sea beyond the walls (sea level plane with gentle waves)
    sea = C.prim("plane", name=name + "_sea", size=1.0, loc=(0, center_y, H + 0.05))
    sea.scale = (4000, 4000, 1)
    smat = C.mat("FX_open_sea", (0.006, 0.03, 0.035), rough=0.06, ior=1.33)
    snb = NB(smat.node_tree)
    sp = snb.out(snb.n("ShaderNodeNewGeometry"), "Position")
    sh = snb.out(snb.noise(snb.v("MULTIPLY", sp, (0.15, 0.3, 0.0)), scale=1.0, detail=6.0, rough=0.6), "Fac")
    sbump = snb.n("ShaderNodeBump", {"Height": sh, "Distance": 0.3, "Strength": 0.5})
    snb.links.new(snb.out(sbump), C.bsdf(smat).inputs["Normal"])
    C.assign(sea, smat)
    # hide the plane where it would cut through the corridor: cut a slot with a boolean-free trick (two planes)
    sea.scale = (1, 1, 1)
    bpy.data.objects.remove(sea, do_unlink=True)
    seas = []
    for side in (-1, 1):
        s_ = C.prim("plane", name="%s_sea%s" % (name, "L" if side < 0 else "R"), size=1.0, loc=(0, 0, 0))
        s_.scale = (2000, 4000, 1)
        s_.location = (side * (W2 + 50 + 1000), center_y, H + 0.05)
        C.assign(s_, smat)
        _parent(s_, root)
        seas.append(s_)
    parts["sea"] = seas
    # ---- spray off the crests
    if spray:
        t_a = (frame_start - 1) / fps - 4.0
        t_b = (frame_end - 1) / fps + 0.5
        crest_len = (y1 - y0) - 2 * shore_slope * 0.6
        n = int(spray_rate * crest_len * (t_b - t_a) * 2)
        n = min(n, 14000)
        side = rng.choice([-1, 1], n)
        yy = rng.uniform(y0 + shore_slope * 0.6, y1 - shore_slope * 0.6, n)
        fz = np.array([floor(s * W2, y) for s, y in zip(side, yy)])
        hh = np.maximum(H - fz, 0)
        p0 = np.stack([side * (W2 - 0.5 + rng.uniform(-1, 1.5, n)), yy, fz + hh * 0.985 + rng.uniform(-1, 1, n)], 1)
        p0[:, 2] += 0.6
        v0 = np.stack([-side * rng.uniform(0.5, 2.5, n), rng.normal(0, 1.0, n), rng.uniform(2.0, 6.0, n)], 1)
        birth = rng.uniform(t_a, t_b, n)
        life = rng.uniform(2.0, 4.0, n)
        size = rng.uniform(2.0, 4.5, n) * np.clip(hh / 40.0, 0.2, 1.0)
        src = _cached_src("FX_src_quad", lambda: _quad("FX_src_quad"))
        so, smd = _particles(name + "_spray", p0, v0, birth, life, size, _spray_material(opacity=0.25), frame0=frame_start,
                             gravity=(0, 0, -0.35), drag=0.8, wind=(wind[0], wind[1], wind[2] + 0.6), turb=2.0,
                             turb_scale=0.08, turb_speed=0.3, turb_ramp=2.0, grow=2.5, fade_in=0.15, fade_out=0.6, mode=3,
                             instance=src, spin=0.3, seed=seed + 1, coll=coll)
        _parent(so, root)
        parts["spray"] = so
    # ---- collapse burst
    if collapse:
        f0c, dc = collapse
        tc0 = (f0c - frame_start) / fps
        n = 2500
        yy = rng.uniform(y0 + shore_slope * 0.4, y1 - shore_slope * 0.4, n)
        zy = zip_y if zip_y is not None else center_y - length * 0.2
        # moment the two walls meet at y (c ~ 0.75)
        meet = tc0 + np.abs(yy - zy) / (zip_v or 1e6) + 0.8 * dc / fps
        fz = np.array([floor(0, y) for y in yy])
        hh = np.maximum(H - fz, 0)
        p0 = np.stack([rng.normal(0, W2 * 0.3, n), yy, fz + hh * rng.uniform(0.2, 0.7, n)], 1)
        v0 = np.stack([rng.normal(0, 6, n), rng.normal(0, 4, n), rng.uniform(8, 26, n) * np.clip(hh / 40, 0.3, 1.0)], 1)
        birth = meet + rng.uniform(-0.2, 0.6, n)
        life = rng.uniform(3.0, 6.0, n)
        size = rng.uniform(4.0, 9.0, n) * np.clip(hh / 40.0, 0.3, 1.0)
        src = _cached_src("FX_src_quad", lambda: _quad("FX_src_quad"))
        bo, bmd = _particles(name + "_crash", p0, v0, birth, life, size, _spray_material("FX_spray_dense", opacity=0.75),
                             frame0=frame_start, gravity=(0, 0, -4.0), drag=0.5, wind=wind, turb=3.0, turb_scale=0.05,
                             turb_speed=0.3, turb_ramp=2.0, grow=2.2, fade_in=0.08, fade_out=0.55, mode=3, instance=src,
                             spin=0.2, seed=seed + 2, coll=coll)
        _parent(bo, root)
        parts["crash"] = bo
    # ---- mist
    if mist:
        mo = C.fog_box(center=(0, center_y, 5.0), size=(width + 16, length - shore_slope, 12.0), density=mist_density,
                       color=(0.85, 0.9, 0.95), anisotropy=0.4, noise_scale=0.06, name=name + "_mist", coll=coll)
        _parent(mo, root)
        parts["mist"] = mo
    if haze:
        ho = C.fog_box(center=(0, center_y + length * 0.25, H * 0.75), size=(width + 140, length * 1.6, H * 1.5 + 30),
                       density=haze, color=(0.9, 0.88, 0.85), anisotropy=0.5, name=name + "_haze", coll=coll)
        _parent(ho, root)
        parts["haze"] = ho
    # ---- lighting
    if lighting:
        el = sun_elevation if sun_elevation is not None else 2.1
        C.world_hdri("qwantani_sunrise_puresky", strength=0.7, rotation=hdri_rotation_for_sun((0.0, 1.0)))
        su = C.sun(elevation=max(el, 1.0), azimuth=180, energy=3.5, temp=3600, angle=1.5)
        parts["sun"] = su
    fx = FX(root, **parts)
    fx.floor_at = floor
    fx.corridor = {"x": (-W2, W2), "y": (y0, y1), "H": H, "shore_slope": shore_slope}
    return fx
