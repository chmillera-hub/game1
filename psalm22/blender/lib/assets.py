"""Non-human asset catalog + loader for "Psalm 22": animals (rigged, with procedural gait / roar cycles)
and period props (procedural or Poly Haven / Objaverse models), all in real-world size.

    import sys; sys.path.insert(0, "/home/user/game1/psalm22/blender")
    from lib import assets as A
    A.names()                         # every asset name; A.names("animal") / A.names("prop")
    A.info("gladius")                 # catalog entry: description, size, variants, source, credit
    sword = A.load("gladius", loc=(0, 0, 0), rot_z=30)            # -> root object
    lion = A.animal("lion", "walk", loc=(0, 6, 0), rot_z=0, start_frame=1, speed=1.0, move=True)
    A.list_actions("lion")            # ['idle', 'walk', 'stalk', 'run', 'roar', ...]

Conventions (every asset):
- metres, Z up, origin at the base (on the ground plane z=0 when loc z=0), "front" faces -Y
  (i.e. toward a default camera standing at -Y looking +Y). rot_z is in DEGREES (like core.py).
- props return an EMPTY root with the parts parented to it; animals return the ARMATURE object.
- anchors are stored on the root as custom properties in root-local coordinates, e.g.
  root["grip"], root["tip"], root["flame"] (wick tip for lamps/candles), root["mouth"].
- materials are Principled BSDF tuned for EEVEE Next and shared between instances (A_* names).
- downloaded / converted model files live in /opt/assets/models (cache/ holds normalised .blends,
  rebuilt automatically when missing).
Full reference: psalm22/docs/assets.md.
"""
import math, os, random, json, time, subprocess, sys, zlib

try:
    import bpy, bmesh
    from mathutils import Vector, Matrix, Euler, Quaternion, noise
    from . import core as C
    from . import polyhaven as ph
except ImportError:          # plain-python mode (texture generation: python assets.py --textures)
    bpy = None

MODELS = "/opt/assets/models"
CACHE = os.path.join(MODELS, "cache")
TEX = os.path.join(MODELS, "textures")
FONTS = os.path.join(MODELS, "fonts")
OBJAVERSE = os.path.join(MODELS, "objaverse", "glbs")
BUILD_VERSION = 4            # bump to invalidate cached normalised animal blends

# --------------------------------------------------------------------------------------------
# Catalog
# --------------------------------------------------------------------------------------------
# size = approximate (x, y, z) extent in metres at scale 1 for variant 0.
CATALOG = {
    # ---------------- animals ----------------
    "lion": dict(kind="animal", desc="Adult male lion with mane (variant 0) / lioness (variant 1). Rigged; "
                 "the sculpt has a roaring open mouth, idle/walk close it.", variants=2, size=(0.55, 2.45, 1.15),
                 source="objaverse"),
    "bull": dict(kind="animal", desc="Massive dark bull (Cape-buffalo build, 'bull of Bashan'). Variant 1 = "
                 "dark wildebeest-like wild ox (lighter build).", variants=2, size=(0.9, 3.0, 1.55), source="objaverse"),
    "ox": dict(kind="animal", desc="Domestic brown ox / cow for the nativity stable (short horns).", variants=1,
               size=(0.6, 2.3, 1.45), source="objaverse"),
    "dog": dict(kind="animal", desc="Wild dog for the pack: variant 0 African wild dog (mottled), variant 1 grey "
                "wolf, variants 2.. = colour/size variations of 0/1 for pack variety.", variants=4,
                size=(0.3, 1.1, 0.75), source="objaverse"),
    "donkey": dict(kind="animal", desc="Grey donkey (wild-ass build) for the nativity.", variants=1,
                   size=(0.45, 1.95, 1.35), source="objaverse"),
    "sheep": dict(kind="animal", desc="Woolly sheep (static sculpt, rigged for idle/walk).", variants=1,
                  size=(0.45, 1.2, 0.85), source="objaverse"),
    "dove": dict(kind="animal", desc="Dove: variant 0 white dove (CC0 museum scan, perched, static), variant 1 "
                 "rock pigeon with spread wings (static).", variants=2, size=(0.15, 0.32, 0.25), source="objaverse"),
    # ---------------- props ----------------
    "gladius": dict(kind="prop", desc="Roman gladius (Pompeii type): steel blade, wooden guard/pommel, bone grip. "
                    "Lying flat, tip toward +X. opts: upright=True (pommel on ground, tip up).",
                    size=(0.70, 0.08, 0.06)),
    "spear": dict(kind="prop", desc="Roman spear (hasta, variant 0) / pilum (variant 1). Lying along +X (head at "
                  "+X). opts: upright=True, length=2.1", variants=2, size=(2.1, 0.05, 0.03)),
    "nail": dict(kind="prop", desc="Hand-forged square iron nail/spike, rusty. Lying along +X (tip at +X). "
                 "opts: upright=True (tip down at origin, head up), length=0.17, bend=0..1", variants=4,
                 size=(0.17, 0.03, 0.03)),
    "hammer": dict(kind="prop", desc="Iron hammer with ash handle (variant 0, Roman carpenter's type), wooden "
                   "mallet (variant 1). Lying, handle along +X, head at +X. opts: upright=True (handle down, head "
                   "up, striking face toward -Y)", variants=2, size=(0.36, 0.14, 0.04)),
    "astragalus": dict(kind="prop", desc="Sheep knucklebone (astragalus) game piece, polished bone.", variants=4,
                       size=(0.028, 0.019, 0.016)),
    "dice": dict(kind="prop", desc="Roman bone cube die with dot-and-circle pips (opposite faces sum 7). "
                 "opts: top=1..6 (face pointing up)", variants=4, size=(0.016, 0.016, 0.016)),
    "water_jar": dict(kind="prop", desc="Earthen clay water jar: v0 two-handled storage jar (~0.48 m), v1 "
                      "one-handled pitcher/jug for pouring (~0.30 m), v2 small round jug. Spout/mouth anchor "
                      "root['mouth'].", variants=3, size=(0.34, 0.30, 0.48)),
    "amphora": dict(kind="prop", desc="Tall two-handled amphora with pointed toe (stands on its toe; lean it).",
                    size=(0.36, 0.30, 0.95)),
    "oil_lamp": dict(kind="prop", desc="Herodian wheel-made clay oil lamp, nozzle toward -Y. Flame anchor "
                     "root['flame'] (wick tip). v1 = darker grey-buff clay.", variants=2, size=(0.075, 0.12, 0.035)),
    "candle": dict(kind="prop", desc="Straight beeswax candle with wick and a few drips. opts: height=0.22, "
                   "radius=0.011, drips=True, holder=False. Flame anchor root['flame']. Children 'body', 'top', "
                   "'puddle' for melt_candle().", size=(0.03, 0.03, 0.23)),
    "potsherd": dict(kind="prop", desc="Broken pottery shard (curved, fresh lighter break edges). Each variant "
                     "is a different random shard; opts: size=0.08", variants=12, size=(0.08, 0.06, 0.02)),
    "crown": dict(kind="prop", desc="Golden crown: v0 radiate spikes + gems, v1 fleuron points, v2 Roman gold "
                  "laurel wreath, v3 arched royal crown with velvet cap.", variants=4, size=(0.2, 0.2, 0.12)),
    "goblet": dict(kind="prop", desc="Jewelled gold goblet/chalice: v0 tall chalice, v1 wide goblet, v2 two-handled "
                   "kantharos, v3 squat jewelled cup. opts: wine=False", variants=4, size=(0.11, 0.11, 0.19)),
    "scroll": dict(kind="prop", desc="Torah-style scroll: two wooden rollers with turned handles, parchment with "
                   "Hebrew text of Psalm 22 (Stam script). Rollers upright, open text facing -Y. opts: "
                   "open_width=0.32, lying=False, closed=False", size=(0.42, 0.10, 0.52)),
    "flatbread": dict(kind="prop", desc="Round flatbread loaf (v0 whole). v1 = broken in two halves: children "
                      "'half_a' (-X) and 'half_b' (+X), animate them apart. v2 = whole, flatter/charred.",
                      variants=3, size=(0.23, 0.23, 0.035)),
    "clay_cup": dict(kind="prop", desc="Simple wheel-thrown clay drinking cup. opts: wine=False", variants=2,
                     size=(0.09, 0.09, 0.085)),
    "table": dict(kind="prop", desc="Rough plank table: v0 dining height 0.75 m (1.7 x 0.8), v1 low table 0.42 m "
                  "(1.4 x 0.7). Top surface height in root['top'].", variants=2, size=(1.7, 0.8, 0.75)),
    "rope": dict(kind="prop", desc="Three-strand hemp rope: v0 loose coil on the ground, v1 straight 1.2 m length "
                 "lying along X. For a rope through arbitrary points use rope_curve().", variants=2,
                 size=(0.45, 0.45, 0.06)),
    "hyssop": dict(kind="prop", desc="Hyssop reed (~1.2 m) with a sponge tied to the top. Lying along +X (sponge at "
                   "+X); opts: upright=True", size=(1.25, 0.08, 0.06)),
}

# Poly Haven models usable through the same API: load("ph:<asset>") or these aliases.
PH_ALIASES = {
    "ph_hammer": "cross_pein_hammer", "ph_mallet": "wooden_hammer_01", "ph_pot": "ceramic_pot",
    "ph_jug": "jug_01", "ph_goblets": "brass_goblets", "ph_candlestick": "wooden_candlestick",
    "ph_diya": "brass_diya_lantern", "ph_bowl": "wooden_bowl_01", "ph_plate": "carved_wooden_plate",
    "ph_bucket": "wooden_bucket_01", "ph_lion_head": "lion_head", "ph_bull_head": "bull_head",
}


def names(kind=None):
    """All catalog names (optionally only kind='animal' / 'prop')."""
    return sorted(k for k, v in CATALOG.items() if kind is None or v["kind"] == kind)


def info(name):
    e = dict(CATALOG[name])
    if name in ANIMALS:
        a = ANIMALS[name]
        e["variants_detail"] = [dict(uid=v["uid"], title=v.get("title"), author=v.get("author"),
                                     license=v.get("license")) for v in a]
        e["actions"] = list_actions(name)
    return e


def credits():
    """List of (asset, title, author, license, url) for every non-CC0 model the catalog can load."""
    out = []
    for n, vs in ANIMALS.items():
        for v in vs:
            out.append((n, v.get("title"), v.get("author"), v.get("license"),
                        "https://sketchfab.com/3d-models/" + v["uid"]))
    return out


# --------------------------------------------------------------------------------------------
# Public loader
# --------------------------------------------------------------------------------------------
def load(name, loc=(0, 0, 0), rot_z=0.0, scale=1.0, coll=None, variant=0, **opts):
    """Create an asset instance. Returns the root object (EMPTY for props, ARMATURE for animals).
    name: catalog name, a PH alias ('ph_jug') or 'ph:<polyhaven_asset>'.
    loc: base position; rot_z: degrees about Z; scale: uniform multiplier of the real-world size."""
    if name.startswith("ph:") or name in PH_ALIASES:
        root = _load_polyhaven(PH_ALIASES.get(name, name[3:]), coll, **opts)
    elif name in ANIMALS:
        root = _animal_instance(name, variant, coll, **opts)
    elif name in CATALOG:
        key = (name, variant, json.dumps(opts, sort_keys=True, default=str))
        src = _PROP_CACHE.get(key)
        try:
            ok = src is not None and bpy.data.objects.get(src.name) is src and src.users > 0
        except ReferenceError:
            ok = False
        if ok:
            root = _copy_hierarchy(src, coll)       # linked duplicate: shares meshes/materials
        else:
            builder = globals()["_build_" + name]
            rnd = random.Random(zlib.crc32(("%s|%d" % (name, variant)).encode()))
            root = _new_root(name, coll)
            parts = builder(variant=variant, rnd=rnd, coll=coll, root=root, **opts)
            for p in parts:
                if p.parent is None:
                    p.parent = root
            _PROP_CACHE[key] = root
    else:
        raise KeyError("unknown asset %r; see assets.names()" % name)
    root["asset"] = name
    root["variant"] = variant
    root.location = loc
    root.rotation_euler = (0, 0, math.radians(rot_z))
    s = scale if isinstance(scale, (tuple, list)) else (scale, scale, scale)
    root.scale = s
    return root


_PROP_CACHE = {}


def _copy_hierarchy(src, coll):
    """Duplicate an asset hierarchy (objects copied, mesh data shared) keeping custom properties."""
    def cp(o, parent):
        d = o.copy()
        d.animation_data_clear()
        C.link(d, coll)
        if parent is not None:
            d.parent = parent
            d.matrix_parent_inverse = o.matrix_parent_inverse.copy()
        for c in o.children:
            cp(c, d)
        return d
    r = cp(src, None)
    r.location = (0, 0, 0)
    r.rotation_euler = (0, 0, 0)
    r.scale = (1, 1, 1)
    return r


def _new_root(name, coll):
    r = bpy.data.objects.new(name, None)
    r.empty_display_type = "PLAIN_AXES"
    r.empty_display_size = 0.1
    C.link(r, coll)
    return r


def _obj(name, me, coll):
    o = bpy.data.objects.new(name, me)
    C.link(o, coll)
    return o


def children_recursive(root):
    out = []
    for c in root.children:
        out.append(c)
        out += children_recursive(c)
    return out


def set_visible_frames(root, f_in=None, f_out=None):
    """Keyframe render/viewport visibility of a whole asset hierarchy (shown from f_in, hidden from f_out)."""
    for o in [root] + children_recursive(root):
        if f_in is not None:
            o.hide_render = True
            o.keyframe_insert("hide_render", frame=f_in - 1)
            o.hide_render = False
            o.keyframe_insert("hide_render", frame=f_in)
        if f_out is not None:
            o.hide_render = False
            o.keyframe_insert("hide_render", frame=f_out - 1)
            o.hide_render = True
            o.keyframe_insert("hide_render", frame=f_out)


def bounds(root):
    """World-space (min, max) Vector bounds of all meshes under root (evaluated, posed)."""
    dg = bpy.context.evaluated_depsgraph_get()
    mn = Vector((1e9, 1e9, 1e9))
    mx = -mn
    for o in [root] + children_recursive(root):
        if o.type != "MESH":
            continue
        for c in o.evaluated_get(dg).bound_box:
            p = o.matrix_world @ Vector(c)
            mn = Vector(map(min, mn, p))
            mx = Vector(map(max, mx, p))
    return mn, mx


def anchor(root, key):
    """World position of an anchor stored on root (e.g. 'flame', 'grip', 'tip', 'mouth')."""
    return root.matrix_world @ Vector(root[key])


# --------------------------------------------------------------------------------------------
# Mesh helpers
# --------------------------------------------------------------------------------------------
def _bm_to_obj(name, bm, coll, smooth=True):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    return _obj(name, me, coll)


def _lathe(name, profile, seg=48, coll=None, smooth=True, wobble=0.0, seed=0, ellip=(1.0, 1.0),
           uv=True, axis_offset=(0.0, 0.0)):
    """Surface of revolution around Z. profile: [(r, z), ...] in order; r==0 at an end -> cap to a
    point. wobble adds hand-made irregularity (fraction of r). ellip scales x/y."""
    bm = bmesh.new()
    rings = []
    rnd = random.Random(seed)
    ph1, ph2 = rnd.random() * 6.28, rnd.random() * 6.28
    for (r, z) in profile:
        ring = []
        if r <= 1e-7:
            ring = [bm.verts.new((axis_offset[0], axis_offset[1], z))]
        else:
            for i in range(seg):
                a = 2 * math.pi * i / seg
                w = 1.0 + wobble * (math.sin(2 * a + ph1 + z * 9) * 0.6 + math.sin(3 * a + ph2 - z * 5) * 0.4)
                ring.append(bm.verts.new((axis_offset[0] + math.cos(a) * r * w * ellip[0],
                                          axis_offset[1] + math.sin(a) * r * w * ellip[1], z)))
        rings.append(ring)
    bm.verts.ensure_lookup_table()
    # cumulative length for v
    L = [0.0]
    for i in range(1, len(profile)):
        L.append(L[-1] + math.hypot(profile[i][0] - profile[i - 1][0], profile[i][1] - profile[i - 1][1]))
    tot = L[-1] or 1.0
    faces = []
    for k in range(len(rings) - 1):
        a, b = rings[k], rings[k + 1]
        if len(a) == 1 and len(b) == 1:
            continue
        if len(a) == 1:
            for i in range(seg):
                faces.append((bm.faces.new((a[0], b[i], b[(i + 1) % seg])), k, i))
        elif len(b) == 1:
            for i in range(seg):
                faces.append((bm.faces.new((a[i], b[0], a[(i + 1) % seg])), k, i))
        else:
            for i in range(seg):
                faces.append((bm.faces.new((a[i], b[i], b[(i + 1) % seg], a[(i + 1) % seg])), k, i))
    if uv:
        lay = bm.loops.layers.uv.new("UVMap")
        for f, k, i in faces:
            for lp in f.loops:
                v = lp.vert
                # find ring index
                z = v.co.z
                kk = k if abs(z - profile[k][1]) < abs(z - profile[min(k + 1, len(profile) - 1)][1]) else k + 1
                ang = math.atan2(v.co.y - axis_offset[1], v.co.x - axis_offset[0]) % (2 * math.pi)
                u = ang / (2 * math.pi)
                if i == seg - 1 and u < 0.5:
                    u += 1.0
                lp[lay].uv = (u, L[kk] / tot)
    bm.normal_update()
    o = _bm_to_obj(name, bm, coll, smooth)
    _recalc_normals(o)
    return o


def _recalc_normals(o, inside=False):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if inside:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(o.data)
    bm.free()


def _loft(name, sections, coll=None, cap_start=True, cap_end=True, smooth=True, closed=True):
    """Loft through cross-sections: list of lists of 3D points (same count). Caps with n-gons."""
    bm = bmesh.new()
    rings = [[bm.verts.new(p) for p in s] for s in sections]
    n = len(sections[0])
    for k in range(len(rings) - 1):
        a, b = rings[k], rings[k + 1]
        for i in range(n if closed else n - 1):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
    if cap_start:
        bm.faces.new(list(reversed(rings[0])))
    if cap_end:
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _bm_to_obj(name, bm, coll, smooth)


def _tube(name, pts, radius, coll=None, seg=12, cap=True, radius_fn=None):
    """Mesh tube along a polyline (radius or radius_fn(t))."""
    pts = [Vector(p) for p in pts]
    secs = []
    up = Vector((0, 0, 1))
    for i, p in enumerate(pts):
        t = i / (len(pts) - 1)
        d = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        a = d.cross(up)
        if a.length < 1e-4:
            a = d.cross(Vector((1, 0, 0)))
        a.normalize()
        b = d.cross(a).normalized()
        r = radius_fn(t) if radius_fn else radius
        secs.append([p + (a * math.cos(2 * math.pi * k / seg) + b * math.sin(2 * math.pi * k / seg)) * r
                     for k in range(seg)])
    return _loft(name, secs, coll, cap, cap)


def _apply_mods(o):
    """Apply all modifiers (context-free)."""
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    old = o.data
    o.modifiers.clear()
    o.data = me
    if old.users == 0:
        bpy.data.meshes.remove(old)
    return o


def _remesh(o, voxel, smooth=True, adaptivity=0.0):
    m = o.modifiers.new("remesh", "REMESH")
    m.mode = "VOXEL"
    m.voxel_size = voxel
    m.adaptivity = adaptivity
    m.use_smooth_shade = smooth
    return _apply_mods(o)


def _join(objs, name=None):
    """Join mesh objects into the first one (context-free via bmesh)."""
    bpy.context.view_layer.update()
    base = objs[0]
    bm = bmesh.new()
    mats = []
    for o in objs:
        me = o.data
        tmp = me.copy()
        tmp.transform(base.matrix_world.inverted() @ o.matrix_world)
        # remap material indices
        remap = []
        for m in me.materials:
            if m not in mats:
                mats.append(m)
            remap.append(mats.index(m))
        if remap:
            for p in tmp.polygons:
                p.material_index = remap[p.material_index] if p.material_index < len(remap) else 0
        bm.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
    me = bpy.data.meshes.new(name or base.name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    old = base.data
    base.data = me
    for o in objs[1:]:
        d = o.data
        bpy.data.objects.remove(o)
        if d.users == 0:
            bpy.data.meshes.remove(d)
    if old.users == 0:
        bpy.data.meshes.remove(old)
    if name:
        base.name = name
    return base


def _noise_displace(o, amp, scale, seed=0.0, along_normal=True, fn=None):
    """Displace vertices by mathutils fbm noise (deterministic). Normals are sampled once up front
    (accessing v.normal while editing coordinates would recompute them every time)."""
    import numpy as np
    me = o.data
    n = len(me.vertices)
    co = np.empty(n * 3, np.float32)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    nr = np.empty(n * 3, np.float32)
    me.vertices.foreach_get("normal", nr)
    nr = nr.reshape(-1, 3)
    off = Vector((seed * 13.1, seed * 7.7, seed * 3.3))
    fr = noise.fractal
    if along_normal:
        vals = np.array([fr(Vector(c) * scale + off, 0.5, 2.0, 4) if fn is None else fn(Vector(c)) for c in co],
                        np.float32)
        co += nr * (vals[:, None] * amp)
    else:
        nz = noise.noise
        d = np.array([(nz(Vector(c) * scale + off), nz(Vector(c) * scale + off + Vector((5.2, 1.3, 2.8))),
                       nz(Vector(c) * scale + off + Vector((1.7, 9.2, 3.4)))) for c in co], np.float32)
        co += d * amp
    me.vertices.foreach_set("co", co.ravel())
    me.update()


def _assign(o, m):
    o.data.materials.clear()
    o.data.materials.append(m)
    return o


def _smooth(o, angle=None):
    for p in o.data.polygons:
        p.use_smooth = True
    if angle is not None:
        try:
            m = o.modifiers.new("autosmooth", "NODES")
            m.node_group = _smooth_by_angle_group()
            m["Input_1"] = math.radians(angle)
        except Exception:
            pass
    return o


def _smooth_by_angle_group():
    g = bpy.data.node_groups.get("A_SmoothByAngle")
    if g:
        return g
    g = bpy.data.node_groups.new("A_SmoothByAngle", "GeometryNodeTree")
    gi = g.nodes.new("NodeGroupInput")
    go = g.nodes.new("NodeGroupOutput")
    g.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    s = g.interface.new_socket("Angle", in_out="INPUT", socket_type="NodeSocketFloat")
    s.default_value = math.radians(30)
    g.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    ea = g.nodes.new("GeometryNodeInputMeshEdgeAngle")
    cmp = g.nodes.new("FunctionNodeCompare")
    cmp.data_type = "FLOAT"
    cmp.operation = "GREATER_THAN"
    ss = g.nodes.new("GeometryNodeSetShadeSmooth")
    ss.domain = "EDGE"
    nt = g.links
    nt.new(ea.outputs["Unsigned Angle"], cmp.inputs[0])
    nt.new(gi.outputs[1], cmp.inputs[1])
    nt.new(gi.outputs[0], ss.inputs["Geometry"])
    inv = g.nodes.new("FunctionNodeBooleanMath")
    inv.operation = "NOT"
    nt.new(cmp.outputs[0], inv.inputs[0])
    nt.new(inv.outputs[0], ss.inputs["Shade Smooth"])
    nt.new(ss.outputs[0], go.inputs[0])
    return g


def _bevel(o, width, segments=2, limit="ANGLE", angle=40):
    m = o.modifiers.new("bevel", "BEVEL")
    m.width = width
    m.segments = segments
    m.limit_method = limit
    if limit == "ANGLE":
        m.angle_limit = math.radians(angle)
    m.harden_normals = False
    return m


def _subsurf(o, levels=1, render=None):
    m = o.modifiers.new("subsurf", "SUBSURF")
    m.levels = levels
    m.render_levels = levels if render is None else render
    return m


# --------------------------------------------------------------------------------------------
# Materials (shared per scene by name)
# --------------------------------------------------------------------------------------------
def _new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m, m.node_tree.nodes, m.node_tree.links, m.node_tree.nodes["Principled BSDF"]


def _pmat(name, c1, c2=None, scale=10.0, detail=6.0, rough=0.5, rough2=None, metal=0.0, metal2=None,
          bump=0.0, bump_scale=None, bump_dist=0.002, sss=0.0, sss_radius=(1.0, 0.5, 0.25), sss_scale=0.01,
          spec=0.5, coat=0.0, coat_rough=0.1, sheen=0.0, ramp=(0.3, 0.7), c3=None, c3_scale=2.0, c3_amount=0.0,
          c3_rough=None, c3_metal=None, stretch=(1, 1, 1), ior=1.45, voronoi_bump=0.0, voronoi_scale=40.0,
          emission=None, emission_strength=0.0):
    """Procedural two/three-tone Principled material in object space (no UVs needed).
    c1/c2 mixed by fbm noise (ramp positions), optional c3 patches (large-scale noise), bump from noise."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m, N, L, b = _new_mat(name)
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = stretch
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    nz = N.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = detail
    nz.inputs["Roughness"].default_value = 0.6
    L.new(mp.outputs["Vector"], nz.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].position = ramp[0]
    cr.color_ramp.elements[1].position = ramp[1]
    L.new(nz.outputs["Fac"], cr.inputs["Fac"])
    fac = cr.outputs["Color"]

    def mixf(a, bb, f):
        n = N.new("ShaderNodeMix")
        n.data_type = "FLOAT"
        n.inputs[2].default_value = a
        n.inputs[3].default_value = bb
        L.new(f, n.inputs[0])
        return n.outputs[0]

    def mixc(a, bb, f):
        n = N.new("ShaderNodeMix")
        n.data_type = "RGBA"
        if isinstance(a, tuple):
            n.inputs[6].default_value = (*a[:3], 1)
        else:
            L.new(a, n.inputs[6])
        if isinstance(bb, tuple):
            n.inputs[7].default_value = (*bb[:3], 1)
        else:
            L.new(bb, n.inputs[7])
        L.new(f, n.inputs[0])
        return n.outputs[2]

    col = mixc(tuple(c1), tuple(c2 or c1), fac)
    rgh = mixf(rough, rough if rough2 is None else rough2, fac)
    mtl = mixf(metal, metal if metal2 is None else metal2, fac)
    if c3 is not None and c3_amount > 0:
        nz3 = N.new("ShaderNodeTexNoise")
        nz3.inputs["Scale"].default_value = c3_scale
        nz3.inputs["Detail"].default_value = 8
        L.new(mp.outputs["Vector"], nz3.inputs["Vector"])
        cr3 = N.new("ShaderNodeValToRGB")
        cr3.color_ramp.elements[0].position = 1.0 - c3_amount
        cr3.color_ramp.elements[1].position = min(1.0, 1.0 - c3_amount + 0.12)
        L.new(nz3.outputs["Fac"], cr3.inputs["Fac"])
        f3 = cr3.outputs["Color"]
        col = mixc(col, tuple(c3), f3)
        if c3_rough is not None:
            rgh = mixf(0, c3_rough, f3) if False else _mix_sock(N, L, rgh, c3_rough, f3)
        if c3_metal is not None:
            mtl = _mix_sock(N, L, mtl, c3_metal, f3)
    L.new(col, b.inputs["Base Color"])
    L.new(rgh, b.inputs["Roughness"])
    L.new(mtl, b.inputs["Metallic"])
    b.inputs["Specular IOR Level"].default_value = spec
    b.inputs["IOR"].default_value = ior
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss
        b.inputs["Subsurface Radius"].default_value = sss_radius
        b.inputs["Subsurface Scale"].default_value = sss_scale
    if coat:
        b.inputs["Coat Weight"].default_value = coat
        b.inputs["Coat Roughness"].default_value = coat_rough
    if sheen:
        b.inputs["Sheen Weight"].default_value = sheen
    if emission:
        b.inputs["Emission Color"].default_value = (*emission, 1)
        b.inputs["Emission Strength"].default_value = emission_strength
    hgt = None
    if bump:
        nzb = N.new("ShaderNodeTexNoise")
        nzb.inputs["Scale"].default_value = bump_scale or scale * 4
        nzb.inputs["Detail"].default_value = 8
        L.new(mp.outputs["Vector"], nzb.inputs["Vector"])
        hgt = nzb.outputs["Fac"]
    if voronoi_bump:
        vo = N.new("ShaderNodeTexVoronoi")
        vo.feature = "DISTANCE_TO_EDGE" if False else "F1"
        vo.inputs["Scale"].default_value = voronoi_scale
        L.new(mp.outputs["Vector"], vo.inputs["Vector"])
        mth = N.new("ShaderNodeMath")
        mth.operation = "MULTIPLY_ADD"
        mth.inputs[1].default_value = voronoi_bump
        if hgt is not None:
            L.new(hgt, mth.inputs[2])
        L.new(vo.outputs["Distance"], mth.inputs[0])
        hgt = mth.outputs[0]
    if hgt is not None:
        bp = N.new("ShaderNodeBump")
        bp.inputs["Strength"].default_value = min(1.0, bump if bump else 0.5)
        bp.inputs["Distance"].default_value = bump_dist
        L.new(hgt, bp.inputs["Height"])
        L.new(bp.outputs["Normal"], b.inputs["Normal"])
        if coat:
            L.new(bp.outputs["Normal"], b.inputs["Coat Normal"]) if False else None
    return m


def _mix_sock(N, L, a_sock, bval, f):
    n = N.new("ShaderNodeMix")
    n.data_type = "FLOAT"
    L.new(a_sock, n.inputs[2])
    n.inputs[3].default_value = bval
    L.new(f, n.inputs[0])
    return n.outputs[0]


def mat_clay(kind="terracotta"):
    """Fired clay: 'terracotta' (orange-red), 'buff' (pale), 'grey' (grey-buff), 'dark' (sooty brown),
    'break' (fresh broken edge, lighter), 'slip' (burnished red slip). Includes fire-clouding, throwing
    rings (bump bands along Z), and grime toward the base (object z < 8 cm)."""
    name = "A_clay_" + kind
    m = bpy.data.materials.get(name)
    if m:
        return m
    P = {"terracotta": ((0.36, 0.14, 0.065), (0.50, 0.23, 0.11), (0.13, 0.065, 0.04)),
         "buff": ((0.45, 0.30, 0.18), (0.58, 0.42, 0.27), (0.20, 0.13, 0.08)),
         "grey": ((0.27, 0.23, 0.19), (0.38, 0.33, 0.27), (0.10, 0.09, 0.08)),
         "dark": ((0.20, 0.10, 0.055), (0.29, 0.155, 0.085), (0.06, 0.045, 0.035)),
         "break": ((0.55, 0.30, 0.16), (0.66, 0.40, 0.22), (0.42, 0.23, 0.12)),
         "slip": ((0.32, 0.085, 0.04), (0.42, 0.13, 0.06), (0.12, 0.05, 0.03))}[kind]
    m = _pmat(name, P[0], P[1], scale=9.0, rough=0.8 if kind != "slip" else 0.5, rough2=0.92,
              bump=0.35, bump_scale=110.0, bump_dist=0.0006, c3=P[2], c3_scale=2.2, c3_amount=0.3, c3_rough=0.95,
              voronoi_bump=0.12, voronoi_scale=220.0, spec=0.35, ramp=(0.25, 0.75))
    N, L = m.node_tree.nodes, m.node_tree.links
    b = N["Principled BSDF"]
    tc = next(n for n in N if n.type == "TEX_COORD")
    # grime toward the base
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Object"], sep.inputs[0])
    mr = N.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.0
    mr.inputs["From Max"].default_value = 0.09
    mr.inputs["To Min"].default_value = 0.55
    mr.inputs["To Max"].default_value = 1.0
    L.new(sep.outputs["Z"], mr.inputs["Value"])
    src = b.inputs["Base Color"].links[0].from_socket
    mul = N.new("ShaderNodeMix")
    mul.data_type = "RGBA"
    mul.blend_type = "MULTIPLY"
    mul.inputs[0].default_value = 1.0
    L.new(src, mul.inputs[6])
    cmb = N.new("ShaderNodeCombineXYZ")
    for i in range(3):
        L.new(mr.outputs["Result"], cmb.inputs[i])
    L.new(cmb.outputs[0], mul.inputs[7])
    L.new(mul.outputs[2], b.inputs["Base Color"])
    # throwing rings: wave bands along Z added to the bump height
    bp = b.inputs["Normal"].links[0].from_node if b.inputs["Normal"].links else None
    if bp is not None and bp.type == "BUMP":
        wv = N.new("ShaderNodeTexWave")
        wv.wave_type = "BANDS"
        wv.bands_direction = "Z"
        wv.inputs["Scale"].default_value = 40.0
        wv.inputs["Distortion"].default_value = 2.0
        wv.inputs["Detail"].default_value = 1.0
        L.new(tc.outputs["Object"], wv.inputs["Vector"])
        add = N.new("ShaderNodeMath")
        add.operation = "MULTIPLY_ADD"
        add.inputs[1].default_value = 0.6
        L.new(wv.outputs["Fac"], add.inputs[0])
        L.new(bp.inputs["Height"].links[0].from_socket, add.inputs[2])
        L.new(add.outputs[0], bp.inputs["Height"])
    return m


def mat_iron(rust=0.5, scale=60.0):
    """Hand-forged iron: dark metal with rust patches (rust 0..1). scale = noise frequency in object space
    (use ~60 for nails/small parts, ~25 for larger pieces)."""
    key = "A_iron_%02d_%d" % (int(rust * 10), int(scale))
    return _pmat(key, (0.085, 0.080, 0.076), (0.15, 0.135, 0.12), scale=scale, rough=0.42, rough2=0.66, metal=0.8,
                 metal2=0.55, bump=0.5, bump_scale=scale * 7, bump_dist=0.0003, c3=(0.24, 0.085, 0.03),
                 c3_scale=scale * 0.6, c3_amount=0.12 + 0.5 * rust, c3_rough=0.9, c3_metal=0.0,
                 voronoi_bump=0.3, voronoi_scale=scale * 12)


def mat_steel(worn=0.3):
    return _pmat("A_steel", (0.62, 0.61, 0.60), (0.50, 0.49, 0.48), scale=8.0, rough=0.3, rough2=0.42, metal=1.0,
                 bump=0.12, bump_scale=60.0, bump_dist=0.0002, stretch=(1, 30, 30), c3=(0.2, 0.15, 0.11),
                 c3_scale=10.0, c3_amount=0.14 * worn / 0.3, c3_rough=0.75, c3_metal=0.5)


def mat_gold(tone="yellow"):
    c = {"yellow": ((1.0, 0.66, 0.22), (0.95, 0.56, 0.15)), "red": ((1.0, 0.55, 0.24), (0.92, 0.46, 0.18)),
         "pale": ((1.0, 0.74, 0.34), (0.95, 0.66, 0.26))}[tone]
    return _pmat("A_gold_" + tone, c[0], c[1], scale=4.0, rough=0.16, rough2=0.3, metal=1.0, bump=0.1,
                 bump_scale=45.0, bump_dist=0.0003, c3=(0.35, 0.22, 0.10), c3_scale=8.0, c3_amount=0.08,
                 c3_rough=0.55)


def mat_gem(kind="ruby"):
    c = {"ruby": (0.45, 0.005, 0.02), "emerald": (0.01, 0.30, 0.08), "sapphire": (0.01, 0.04, 0.45),
         "amethyst": (0.22, 0.03, 0.35), "pearl": (0.85, 0.82, 0.76), "garnet": (0.25, 0.01, 0.015),
         "topaz": (0.8, 0.45, 0.05)}[kind]
    name = "A_gem_" + kind
    m = bpy.data.materials.get(name)
    if m:
        return m
    m, N, L, b = _new_mat(name)
    b.inputs["Base Color"].default_value = (*c, 1)
    if kind == "pearl":
        b.inputs["Roughness"].default_value = 0.25
        b.inputs["Coat Weight"].default_value = 0.6
        b.inputs["Sheen Weight"].default_value = 0.4
        b.inputs["Subsurface Weight"].default_value = 0.3
    else:
        b.inputs["Roughness"].default_value = 0.03
        b.inputs["IOR"].default_value = 1.77
        b.inputs["Specular IOR Level"].default_value = 1.0
        b.inputs["Coat Weight"].default_value = 1.0
        b.inputs["Coat Roughness"].default_value = 0.0
        b.inputs["Subsurface Weight"].default_value = 0.6
        b.inputs["Subsurface Radius"].default_value = c
        b.inputs["Subsurface Scale"].default_value = 0.004
        b.inputs["Emission Color"].default_value = (*c, 1)
        b.inputs["Emission Strength"].default_value = 0.15
    return m


def mat_bone(tone=0.0, scale=80.0):
    """Polished bone / ivory (tone 0 = pale, 1 = darker, handled & stained)."""
    return _pmat("A_bone_%d_%d" % (int(tone * 10), int(scale)), (0.56 - 0.12 * tone, 0.47 - 0.12 * tone, 0.33 - 0.11 * tone),
                 (0.66 - 0.08 * tone, 0.58 - 0.09 * tone, 0.43 - 0.1 * tone), scale=scale, rough=0.36, rough2=0.5,
                 bump=0.2, bump_scale=scale * 8, bump_dist=0.0001, sss=0.3, sss_radius=(1.0, 0.7, 0.45),
                 sss_scale=0.003, c3=(0.30, 0.20, 0.10), c3_scale=scale * 0.8, c3_amount=0.18, c3_rough=0.55, spec=0.5)


def mat_wax():
    return _pmat("A_beeswax", (0.80, 0.46, 0.10), (0.88, 0.58, 0.16), scale=8.0, rough=0.38, rough2=0.5,
                 bump=0.2, bump_scale=60.0, bump_dist=0.0004, sss=1.0, sss_radius=(1.0, 0.55, 0.18), sss_scale=0.025,
                 spec=0.5)


def mat_wood(kind="boxwood"):
    """Small-prop woods from Poly Haven scans (box-projected, no UVs needed):
    boxwood (pale), ash (light brown), olive (warm, figured), dark (dark brown)."""
    P = {"boxwood": ("fine_grained_wood", 5.0, (1.05, 0.88, 0.62)), "ash": ("fine_grained_wood", 3.5, (0.78, 0.66, 0.52)),
         "olive": ("fine_grained_wood", 3.0, (0.62, 0.48, 0.34)), "dark": ("dark_wood", 3.0, (0.8, 0.7, 0.6))}[kind]
    name = "A_wood_" + kind
    m = bpy.data.materials.get(name)
    if m:
        return m
    try:
        return C.mat_pbr(P[0], scale=P[1], tint=P[2], name=name, blend=0.3)
    except Exception:
        return _pmat(name, (0.40, 0.29, 0.18), (0.52, 0.40, 0.26), scale=4.0, detail=10, rough=0.55, rough2=0.7,
                     bump=0.25, bump_scale=120.0, bump_dist=0.0004, stretch=(1, 14, 14), spec=0.4)


def mat_wood_pbr(asset="rough_wood", scale=2.0, tint=(0.8, 0.68, 0.55)):
    return C.mat_pbr(asset, scale=scale, tint=tint, name="A_wpbr_" + asset)


def mat_rope():
    return _pmat("A_rope", (0.24, 0.17, 0.10), (0.36, 0.27, 0.16), scale=60.0, rough=0.9, bump=0.6,
                 bump_scale=400.0, bump_dist=0.0005, sheen=0.4, spec=0.3)


def mat_sponge():
    return _pmat("A_sponge", (0.55, 0.40, 0.18), (0.70, 0.55, 0.28), scale=20.0, rough=0.9, bump=0.9,
                 voronoi_bump=0.8, voronoi_scale=220.0, bump_dist=0.002, sss=0.2, sss_scale=0.005)


def mat_reed():
    return _pmat("A_reed", (0.42, 0.40, 0.20), (0.55, 0.50, 0.28), scale=3.0, rough=0.5, rough2=0.62,
                 bump=0.3, bump_scale=200.0, stretch=(1, 1, 30), spec=0.5)


def mat_velvet(color=(0.25, 0.01, 0.03)):
    m = _pmat("A_velvet", color, tuple(c * 0.6 for c in color), scale=40.0, rough=0.85, sheen=1.0, spec=0.2,
              bump=0.2, bump_scale=600.0)
    try:
        C.bsdf(m).inputs["Sheen Tint"].default_value = (1.0, 0.6, 0.6, 1)
    except Exception:
        pass
    return m


def mat_wine():
    m = bpy.data.materials.get("A_wine")
    if m:
        return m
    m, N, L, b = _new_mat("A_wine")
    b.inputs["Base Color"].default_value = (0.06, 0.0, 0.012, 1)
    b.inputs["Roughness"].default_value = 0.04
    b.inputs["Specular IOR Level"].default_value = 0.8
    b.inputs["Coat Weight"].default_value = 1.0
    b.inputs["Coat Roughness"].default_value = 0.02
    return m


def mat_water():
    m = bpy.data.materials.get("A_water")
    if m:
        return m
    m, N, L, b = _new_mat("A_water")
    b.inputs["Base Color"].default_value = (0.5, 0.6, 0.62, 1)
    b.inputs["Roughness"].default_value = 0.02
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["IOR"].default_value = 1.33
    return m


def mat_bread(part="crust", char=0.25):
    if part == "crumb":
        return _pmat("A_bread_crumb", (0.80, 0.66, 0.42), (0.90, 0.78, 0.55), scale=30.0, rough=0.85,
                     voronoi_bump=1.0, voronoi_scale=180.0, bump=0.8, bump_scale=90.0, bump_dist=0.002,
                     sss=0.35, sss_radius=(1.0, 0.8, 0.5), sss_scale=0.006, spec=0.3)
    name = "A_bread_crust_%d" % int(char * 10)
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = _pmat(name, (0.36, 0.16, 0.045), (0.62, 0.36, 0.12), scale=9.0, rough=0.62, rough2=0.8, bump=0.7,
              bump_scale=55.0, bump_dist=0.0015, c3=(0.09, 0.035, 0.012), c3_scale=14.0, c3_amount=0.18 + char * 0.5,
              c3_rough=0.9, sss=0.2, sss_radius=(1.0, 0.6, 0.3), sss_scale=0.004, spec=0.3)
    # flour dusting: pale patches on top surfaces (normal.z)
    N, L = m.node_tree.nodes, m.node_tree.links
    b = N["Principled BSDF"]
    src = b.inputs["Base Color"].links[0].from_socket
    geo = N.new("ShaderNodeNewGeometry")
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(geo.outputs["Normal"], sep.inputs[0])
    nzf = N.new("ShaderNodeTexNoise")
    nzf.inputs["Scale"].default_value = 18.0
    nzf.inputs["Detail"].default_value = 6
    crf = N.new("ShaderNodeValToRGB")
    crf.color_ramp.elements[0].position = 0.68
    crf.color_ramp.elements[1].position = 0.8
    L.new(nzf.outputs["Fac"], crf.inputs["Fac"])
    mul = N.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    L.new(crf.outputs["Color"], mul.inputs[0])
    L.new(sep.outputs["Z"], mul.inputs[1])
    mx = N.new("ShaderNodeMix")
    mx.data_type = "RGBA"
    L.new(mul.outputs[0], mx.inputs[0])
    L.new(src, mx.inputs[6])
    mx.inputs[7].default_value = (0.80, 0.72, 0.60, 1)
    L.new(mx.outputs[2], b.inputs["Base Color"])
    return m


def mat_parchment(text=True):
    name = "A_parchment_text" if text else "A_parchment"
    m = bpy.data.materials.get(name)
    if m:
        return m
    m, N, L, b = _new_mat(name)
    img = None
    if text:
        p = texture_path("scroll_psalm22.png")
        if p:
            img = bpy.data.images.load(p, check_existing=True)
    if img is not None:
        t = N.new("ShaderNodeTexImage")
        t.image = img
        uvn = N.new("ShaderNodeUVMap")
        L.new(uvn.outputs["UV"], t.inputs["Vector"])
        L.new(t.outputs["Color"], b.inputs["Base Color"])
    else:
        nz = N.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 6
        cr = N.new("ShaderNodeValToRGB")
        cr.color_ramp.elements[0].color = (0.62, 0.50, 0.33, 1)
        cr.color_ramp.elements[1].color = (0.78, 0.67, 0.48, 1)
        L.new(nz.outputs["Fac"], cr.inputs["Fac"])
        L.new(cr.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.62
    b.inputs["Subsurface Weight"].default_value = 0.25
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.7, 0.4)
    b.inputs["Subsurface Scale"].default_value = 0.002
    b.inputs["Sheen Weight"].default_value = 0.2
    nzb = N.new("ShaderNodeTexNoise")
    nzb.inputs["Scale"].default_value = 140.0
    bp = N.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.15
    bp.inputs["Distance"].default_value = 0.0005
    L.new(nzb.outputs["Fac"], bp.inputs["Height"])
    L.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


# --------------------------------------------------------------------------------------------
# Generated textures (numpy inside Blender; PIL text via the venv for the scroll)
# --------------------------------------------------------------------------------------------
def texture_path(fname):
    p = os.path.join(TEX, fname)
    if os.path.exists(p):
        return p
    if fname == "scroll_psalm22.png":
        try:
            subprocess.run(["/opt/venv/bin/python", os.path.abspath(__file__).replace(".pyc", ".py"),
                            "--textures"], check=True, timeout=300)
        except Exception as e:
            print("assets: scroll texture generation failed:", e)
    return p if os.path.exists(p) else None


def _dice_image():
    """3x2 atlas (bone ground, dot-and-circle pips) generated with numpy; cached as PNG."""
    import numpy as np
    p = os.path.join(TEX, "dice_atlas.png")
    name = "A_dice_atlas"
    if bpy.data.images.get(name):
        return bpy.data.images[name]
    if not os.path.exists(p):
        os.makedirs(TEX, exist_ok=True)
        T = 256
        W, H = 3 * T, 2 * T
        rnd = np.random.default_rng(5)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        img = np.zeros((H, W, 4), np.float32)
        base = np.array([0.70, 0.60, 0.43])
        g = np.zeros((H, W), np.float32)
        for k, amp in ((6, 0.6), (24, 0.3), (96, 0.15)):
            small = rnd.random((k, k * 3 // 2 + 1)).astype(np.float32)
            iy = np.linspace(0, small.shape[0] - 1.001, H)
            ix = np.linspace(0, small.shape[1] - 1.001, W)
            y0, x0 = iy.astype(int), ix.astype(int)
            fy, fx = (iy - y0)[:, None], (ix - x0)[None, :]
            a = small[y0][:, x0] * (1 - fx) + small[y0][:, x0 + 1] * fx
            b = small[y0 + 1][:, x0] * (1 - fx) + small[y0 + 1][:, x0 + 1] * fx
            g += amp * (a * (1 - fy) + b * fy)
        grain = g / 1.05
        img[..., :3] = base * (0.82 + 0.25 * grain[..., None])
        img[..., 3] = 1.0
        pipmask = np.zeros((H, W), np.float32)
        layouts = {1: [(0, 0)], 2: [(-1, -1), (1, 1)], 3: [(-1, -1), (0, 0), (1, 1)],
                   4: [(-1, -1), (1, -1), (-1, 1), (1, 1)], 5: [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)],
                   6: [(-1, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (1, 1)]}
        for f in range(6):
            tx, ty = f % 3, f // 3
            cx0, cy0 = tx * T + T / 2, ty * T + T / 2
            for (px, py) in layouts[f + 1]:
                cx = cx0 + px * T * 0.27 + rnd.normal() * 2
                cy = cy0 + py * T * 0.27 + rnd.normal() * 2
                d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
                ring = np.clip(1.0 - np.abs(d - T * 0.085) / (T * 0.018), 0, 1)
                dot = np.clip((T * 0.032 - d) / 2.0, 0, 1)
                pipmask = np.maximum(pipmask, np.maximum(ring, dot))
        img[..., :3] = img[..., :3] * (1 - pipmask[..., None]) + np.array([0.08, 0.05, 0.03]) * pipmask[..., None]
        img[..., 3] = 1.0 - 0.9 * pipmask        # alpha channel = height (pips are recessed)
        im = bpy.data.images.new(name, W, H, alpha=True)
        im.pixels.foreach_set(img[::-1].ravel())          # Blender rows go bottom-up
        im.filepath_raw = p
        im.file_format = "PNG"
        im.save()
        return im
    im = bpy.data.images.load(p, check_existing=True)
    im.name = name
    return im


def mat_dice():
    m = bpy.data.materials.get("A_dice")
    if m:
        return m
    m, N, L, b = _new_mat("A_dice")
    t = N.new("ShaderNodeTexImage")
    t.image = _dice_image()
    t.interpolation = "Cubic"
    uvn = N.new("ShaderNodeUVMap")
    L.new(uvn.outputs["UV"], t.inputs["Vector"])
    # bone variation
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 160
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    mx = N.new("ShaderNodeMix")
    mx.data_type = "RGBA"
    mx.blend_type = "MULTIPLY"
    mx.inputs[0].default_value = 0.2
    L.new(t.outputs["Color"], mx.inputs[6])
    L.new(nz.outputs["Color"], mx.inputs[7])
    L.new(mx.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.42
    b.inputs["Subsurface Weight"].default_value = 0.2
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.7, 0.45)
    b.inputs["Subsurface Scale"].default_value = 0.002
    bp = N.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.8
    bp.inputs["Distance"].default_value = 0.0006
    L.new(t.outputs["Alpha"], bp.inputs["Height"])
    L.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


# --------------------------------------------------------------------------------------------
# Long-prop orientation helper
# --------------------------------------------------------------------------------------------
def _lay_down(parts, upright, lift, extra_rot=None, pre_z=0.0):
    """Parts are modelled upright along +Z (base at z=0). Unless upright, rotate so +Z -> +X and lift so
    the lowest point touches z=0 (lift = half-thickness). pre_z: spin about the long axis first (deg)."""
    if upright:
        return
    R = Matrix.Rotation(math.radians(90), 4, "Y") @ Matrix.Rotation(math.radians(pre_z), 4, "Z")
    if extra_rot is not None:
        R = extra_rot @ R
    for p in parts:
        if p.parent is None:
            p.matrix_basis = Matrix.Translation((0, 0, lift)) @ R @ p.matrix_basis


def _ground(parts):
    """Translate parent-less parts so the lowest evaluated point is at z=0."""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    zmin = 1e9
    for p in parts:
        for o in [p] + children_recursive(p):
            if o.type == "MESH":
                oe = o.evaluated_get(dg)
                me = oe.to_mesh()
                for v in me.vertices:
                    zmin = min(zmin, (oe.matrix_world @ v.co).z)
                oe.to_mesh_clear()
    for p in parts:
        if p.parent is None:
            p.location.z -= zmin
    return zmin


# --------------------------------------------------------------------------------------------
# Procedural props
# --------------------------------------------------------------------------------------------
def _build_gladius(variant=0, rnd=None, coll=None, root=None, upright=False, **o):
    parts = []
    # dimensions (Pompeii type)
    zp0, zp1, zg1, zgd1, zb1 = 0.0, 0.045, 0.135, 0.16, 0.71
    tipL, hw = 0.075, 0.025
    secs = []
    n = 34
    for i in range(n + 1):
        t = i / n
        z = zgd1 + (zb1 - zgd1) * t
        dt = zb1 - z
        w = hw if dt > tipL else hw * (dt / tipL) ** 0.85
        w = max(w, 0.0006)
        if dt <= tipL:
            w *= 1.0
        th = 0.0042 * (1 - 0.45 * t) * max(0.25, min(1.0, dt / 0.03))
        bev = min(0.0055, w * 0.45)
        secs.append([(w, 0, z), (w - bev, th * 0.55, z), (0, th, z), (-w + bev, th * 0.55, z), (-w, 0, z),
                     (-w + bev, -th * 0.55, z), (0, -th, z), (w - bev, -th * 0.55, z)])
    blade = _loft("gladius_blade", secs, coll, cap_start=True, cap_end=True, smooth=True)
    _assign(blade, mat_steel())
    _smooth(blade, 35)
    parts.append(blade)
    # guard (oval wooden block)
    g = _lathe("gladius_guard", [(0, zg1), (0.036, zg1), (0.041, zg1 + 0.006), (0.041, zgd1 - 0.008),
                                 (0.032, zgd1), (0, zgd1)], seg=40, coll=coll, ellip=(1.0, 0.55))
    _assign(g, mat_wood("boxwood"))
    parts.append(g)
    # grip with 4 finger ridges
    prof = [(0, zp1)]
    for i in range(25):
        t = i / 24
        z = zp1 + (zg1 - zp1) * t
        r = 0.0135 + 0.0022 * abs(math.sin(t * math.pi * 4)) + 0.001 * math.sin(t * math.pi)
        prof.append((r, z))
    prof.append((0, zg1))
    gr = _lathe("gladius_grip", prof, seg=28, coll=coll, ellip=(1.0, 0.82))
    _assign(gr, mat_bone(0.3))
    parts.append(gr)
    # pommel
    pp = [(0, zp0 + 0.004)]
    for i in range(1, 16):
        a = math.pi * i / 16
        pp.append((0.03 * math.sin(a) * (1 + 0.1 * math.sin(a * 2)), zp0 + 0.004 + (zp1 - zp0 - 0.004) * (1 - math.cos(a)) / 2))
    pp.append((0, zp1))
    pm = _lathe("gladius_pommel", pp, seg=36, coll=coll, ellip=(1.0, 0.78))
    _assign(pm, mat_wood("boxwood"))
    parts.append(pm)
    nub = _lathe("gladius_nub", [(0, 0), (0.007, 0.0), (0.008, 0.003), (0.006, 0.006), (0, 0.006)], seg=16, coll=coll)
    _assign(nub, mat_iron(0.2))
    parts.append(nub)
    if not upright:
        _lay_down(parts, False, 0.0, pre_z=90)
        _ground(parts)
        root["grip"] = [0.09, 0, 0.02]
        root["tip"] = [0.71, 0, 0.02]
    else:
        root["grip"] = [0, 0, 0.09]
        root["tip"] = [0, 0, 0.71]
    return parts


def _build_spear(variant=0, rnd=None, coll=None, root=None, upright=False, length=None, **o):
    parts = []
    L = length or (2.1 if variant == 0 else 1.95)
    if variant == 0:
        fer = 0.08
        head = 0.25
        sock = 0.08
        shaft_end = L - head
        ferr = _lathe("spear_ferrule", [(0, 0), (0.004, 0.006), (0.009, 0.04), (0.0145, fer), (0, fer)], 16, coll)
        _assign(ferr, mat_iron(0.4))
        parts.append(ferr)
        sh = _lathe("spear_shaft", [(0, fer - 0.005), (0.0145, fer - 0.005), (0.0135, L * 0.5), (0.0125, shaft_end + 0.02),
                                    (0, shaft_end + 0.02)], 16, coll, wobble=0.03, seed=3)
        _assign(sh, mat_wood("ash"))
        parts.append(sh)
        so = _lathe("spear_socket", [(0, shaft_end), (0.0155, shaft_end), (0.0148, shaft_end + 0.01),
                                     (0.0085, shaft_end + sock), (0, shaft_end + sock + 0.005)], 18, coll)
        _assign(so, mat_iron(0.35))
        parts.append(so)
        # leaf head with midrib
        z0 = shaft_end + sock - 0.01
        hl = L - z0
        secs = []
        for i in range(29):
            t = i / 28
            z = z0 + hl * t
            w = 0.023 * math.sin(math.pi * min(1, t * 1.25) ** 0.8) * (1 - t) ** 0.35 + 0.0007
            th = 0.0045 * (1 - t) + 0.0006
            secs.append([(w, 0, z), (0.0, th, z), (-w, 0, z), (0, -th, z)])
        hd = _loft("spear_head", secs, coll)
        _assign(hd, mat_iron(0.3))
        _smooth(hd, 30)
        parts.append(hd)
        tip = L
    else:  # pilum: wooden shaft, pyramidal block, long thin iron shank, pyramid tip
        shaft_end = L * 0.62
        sh = _lathe("pilum_shaft", [(0, 0), (0.014, 0), (0.0145, 0.02), (0.016, shaft_end - 0.1), (0, shaft_end)],
                    16, coll, wobble=0.03, seed=4)
        _assign(sh, mat_wood("ash"))
        parts.append(sh)
        blk = C.box("pilum_block", (0.045, 0.04, 0.09), (0, 0, shaft_end - 0.04), coll=coll)
        _bevel(blk, 0.004, 2)
        _assign(blk, mat_wood("ash"))
        parts.append(blk)
        for zz in (shaft_end - 0.07, shaft_end - 0.015):
            bd = C.box("pilum_ferrule", (0.048, 0.043, 0.012), (0, 0, zz), coll=coll)
            _assign(bd, mat_iron(0.4))
            parts.append(bd)
        sk = _lathe("pilum_shank", [(0, shaft_end - 0.03), (0.0055, shaft_end - 0.03), (0.0045, L - 0.04),
                                    (0, L - 0.04)], 8, coll)
        _assign(sk, mat_iron(0.3))
        parts.append(sk)
        tp = _lathe("pilum_tip", [(0, L - 0.045), (0.009, L - 0.04), (0, L)], 4, coll, smooth=False)
        _assign(tp, mat_iron(0.25))
        parts.append(tp)
        tip = L
    if not upright:
        _lay_down(parts, False, 0.0, pre_z=90)
        _ground(parts)
        root["tip"] = [tip, 0, 0.015]
        root["grip"] = [L * 0.45, 0, 0.015]
    else:
        root["tip"] = [0, 0, tip]
        root["grip"] = [0, 0, L * 0.45]
    return parts


def _build_nail(variant=0, rnd=None, coll=None, root=None, upright=False, length=None, bend=None, **o):
    rnd = rnd or random.Random(variant)
    L = length or (0.17 + 0.03 * ((variant * 37) % 4) / 3 - 0.015)
    bend = (0.15 + 0.5 * rnd.random()) if bend is None else bend
    secs = []
    n = 28
    tw = rnd.uniform(-0.4, 0.4)
    for i in range(n + 1):
        t = i / n                      # 0 = tip (z=0), 1 = under head
        z = L * t
        s = 0.0006 + 0.0052 * (t ** 0.7) * (1 + 0.06 * math.sin(t * 17 + variant))
        bx = bend * 0.006 * math.sin(math.pi * t) + bend * 0.004 * (1 - t) ** 2
        ang = tw * t
        ca, sa = math.cos(ang), math.sin(ang)
        sq = [(s, s), (-s, s), (-s, -s), (s, -s)]
        sec = []
        for (x, y) in sq:
            x2, y2 = x * ca - y * sa, x * sa + y * ca
            sec.append((x2 + bx, y2, z))
        secs.append(sec)
    shank = _loft("nail_shank", secs, coll)
    _bevel(shank, 0.0008, 2, limit="ANGLE", angle=50)
    _assign(shank, mat_iron(0.6))
    # head: hammered irregular disc
    hr = 0.012 + 0.002 * rnd.random()
    prof = [(0, L - 0.001), (hr * 0.55, L - 0.0012), (hr, L + 0.0012), (hr * 0.96, L + 0.0035),
            (hr * 0.6, L + 0.0055), (0, L + 0.006)]
    head = _lathe("nail_head", prof, 18, coll, wobble=0.12, seed=variant + 3)
    _noise_displace(head, 0.0008, 300.0, seed=variant)
    _assign(head, mat_iron(0.6))
    parts = [shank, head]
    if upright:
        root["tip"] = [0, 0, 0]
        root["head"] = [0, 0, L + 0.006]
    else:
        _lay_down(parts, False, 0.0, extra_rot=Matrix.Rotation(math.radians(180), 4, "Z"))
        _ground(parts)
        # after: head at -X... shift so head at x=0, tip at +X
        for p in parts:
            p.location.x += L + 0.006
        root["tip"] = [L + 0.006, 0, 0.005]
        root["head"] = [0, 0, 0.01]
    return parts


def _build_hammer(variant=0, rnd=None, coll=None, root=None, upright=False, **o):
    parts = []
    if variant == 0:
        HL = 0.36
        hd = _lathe("hammer_handle", [(0, 0), (0.0145, 0.0), (0.0155, 0.02), (0.0135, 0.15), (0.0125, HL - 0.03),
                                      (0.0115, HL + 0.012), (0, HL + 0.012)], 20, coll, ellip=(1.0, 0.72),
                    wobble=0.03, seed=2)
        _assign(hd, mat_wood("ash"))
        parts.append(hd)
        # iron head along Y: flat square face toward -Y, tapering claw/peen toward +Y
        z = HL - 0.012
        secs = []
        prof = [(-0.058, 0.0125, 0.0125), (-0.05, 0.0135, 0.0135), (-0.03, 0.0118, 0.0118), (-0.012, 0.0128, 0.0155),
                (0.0, 0.0132, 0.0165), (0.012, 0.0128, 0.0155), (0.03, 0.0112, 0.0095), (0.05, 0.0118, 0.0045),
                (0.066, 0.0125, 0.0013)]
        for (y, hx, hz) in prof:
            secs.append([(hx, y, z - hz), (hx, y, z + hz), (-hx, y, z + hz), (-hx, y, z - hz)])
        head = _loft("hammer_head", secs, coll)
        _bevel(head, 0.0015, 2)
        _assign(head, mat_iron(0.35))
        _noise_displace(head, 0.0006, 200.0, seed=1)
        parts.append(head)
        wedge = C.box("hammer_wedge", (0.022, 0.004, 0.004), (0, 0, HL + 0.012), coll=coll)
        _assign(wedge, mat_iron(0.5))
        parts.append(wedge)
        root["grip"] = [0, 0, 0.08]
        root["face"] = [0, -0.055, z]
    else:   # wooden mallet
        HL = 0.34
        hd = _lathe("mallet_handle", [(0, 0), (0.015, 0), (0.0155, 0.03), (0.0135, HL), (0.0125, HL + 0.04),
                                      (0, HL + 0.045)], 18, coll, wobble=0.04, seed=5)
        _assign(hd, mat_wood("olive"))
        parts.append(hd)
        mh = _lathe("mallet_head", [(0, -0.07), (0.042, -0.07), (0.046, -0.06), (0.048, 0.0), (0.046, 0.06),
                                    (0.042, 0.07), (0, 0.07)], 32, coll, wobble=0.03, seed=6)
        mh.rotation_euler = (math.radians(90), 0, 0)
        mh.location = (0, 0, HL + 0.035)
        _assign(mh, mat_wood("olive"))
        parts.append(mh)
        root["grip"] = [0, 0, 0.08]
        root["face"] = [0, -0.07, HL + 0.035]
    if not upright:
        _lay_down(parts, False, 0.0, extra_rot=Matrix.Rotation(math.radians(0), 4, "X"))
        # head axis was Y -> still Y after rotating about Y. good.
        _ground(parts)
        g = root["grip"]
        root["grip"] = [g[2], 0, 0.015]
        root["face"] = [HL, -0.055, 0.02]
    return parts


def _metaball_mesh(name, elements, resolution, coll, threshold=0.6):
    """Metaball blend of elements -> mesh object. element: (type, co, radius, size_xyz, rot_euler_deg,
    negative[, stiffness]). type in BALL, CAPSULE, ELLIPSOID, CUBE, PLANE."""
    mb = bpy.data.metaballs.new("A_mb_tmp")
    mb.resolution = mb.render_resolution = resolution
    mb.threshold = threshold
    for e in elements:
        typ, co, r, sz, rot, neg = e[:6]
        el = mb.elements.new(type=typ)
        el.co = co
        el.radius = r
        if sz is not None:
            el.size_x, el.size_y, el.size_z = sz
        if rot:
            el.rotation = Euler([math.radians(x) for x in rot]).to_quaternion()
        el.use_negative = neg
        if len(e) > 6:
            el.stiffness = e[6]
    ob = bpy.data.objects.new("A_mb_tmp_%d" % random.randint(0, 10 ** 9), mb)
    C.link(ob, coll)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bpy.data.objects.remove(ob)
    bpy.data.metaballs.remove(mb)
    me.name = name
    o = _obj(name, me, coll)
    _smooth(o)
    return o


def _build_astragalus(variant=0, rnd=None, coll=None, root=None, **o):
    """Sheep astragalus (knucklebone) ~27x18x15 mm: blocky bone with pulley-shaped (trochlear) ends,
    a waist, a concave plantar face and a deep lateral pit; metaball-sculpted, polished-bone material."""
    rnd = rnd or random.Random(variant)
    j = lambda a: a * (1 + rnd.uniform(-0.08, 0.08))
    mm = 0.001
    els = [
        ("ELLIPSOID", (0, 0, 0), j(9.5 * mm), (1.35, 0.95, 0.78), None, False),
        ("CAPSULE", (j(8.5 * mm), 0, j(1.5 * mm)), j(5.2 * mm), (j(4.5 * mm), 1, 1), (0, 0, 90), False),
        ("CAPSULE", (-j(9 * mm), 0, -j(1.0 * mm)), j(4.8 * mm), (j(4.0 * mm), 1, 1), (0, 0, 90), False),
        ("BALL", (j(10.5 * mm), j(0.5 * mm), j(6.8 * mm)), j(3.6 * mm), None, None, True),        # proximal groove
        ("CAPSULE", (j(11.5 * mm), 0, j(0.5 * mm)), j(2.2 * mm), (j(2.5 * mm), 1, 1), (0, 90, 0), True),
        ("BALL", (-j(11 * mm), 0, -j(5.5 * mm)), j(3.2 * mm), None, None, True),                # distal groove
        ("ELLIPSOID", (j(1 * mm), -j(10.5 * mm), j(0.5 * mm)), j(4.6 * mm), (1.5, 0.55, 0.9), None, True),  # lateral pit
        ("ELLIPSOID", (j(0.5 * mm), 0, -j(9 * mm)), j(5 * mm), (1.7, 1.0, 0.45), None, True),   # concave face
        ("ELLIPSOID", (-j(2 * mm), j(8.5 * mm), j(2.5 * mm)), j(3.2 * mm), (1.6, 0.6, 0.8), None, False),  # ridge
        ("BALL", (j(3 * mm), j(6 * mm), -j(6 * mm)), j(2.0 * mm), None, None, True),
    ]
    o_ = _metaball_mesh("astragalus", els, 0.0006, coll)
    _noise_displace(o_, 0.00025, 600.0, seed=variant + 0.5)
    _noise_displace(o_, 0.0004, 150.0, seed=variant + 1.5)
    _assign(o_, mat_bone(0.2 + 0.25 * (variant % 3), scale=300.0))
    o_.rotation_euler = (0, 0, rnd.uniform(-0.3, 0.3))
    _ground([o_])
    return [o_]


def _build_dice(variant=0, rnd=None, coll=None, root=None, top=None, size=0.016, **o):
    rnd = rnd or random.Random(variant)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    uvl = bm.loops.layers.uv.new("UVMap")
    # face -> pip value; opposite faces sum to 7. +Z=1? choose mapping by normal
    val = {(0, 0, 1): 1, (0, 0, -1): 6, (1, 0, 0): 2, (-1, 0, 0): 5, (0, 1, 0): 3, (0, -1, 0): 4}
    for f in bm.faces:
        nrm = tuple(int(round(c)) for c in f.normal)
        k = val[nrm] - 1
        tx, ty = k % 3, k // 3
        # local 2D axes on the face
        n = f.normal
        a = Vector((1, 0, 0)) if abs(n.x) < 0.9 else Vector((0, 1, 0))
        bvec = n.cross(a)
        for lp in f.loops:
            p = lp.vert.co
            u = (p.dot(a) + 0.5)
            v = (p.dot(bvec) + 0.5)
            lp[uvl].uv = ((tx + 0.03 + 0.94 * u) / 3, 1 - (ty + 0.03 + 0.94 * (1 - v)) / 2)
    s = size
    sc = (s * rnd.uniform(0.96, 1.03), s * rnd.uniform(0.95, 1.02), s * rnd.uniform(0.93, 1.0))
    bmesh.ops.scale(bm, vec=sc, verts=bm.verts)
    o_ = _bm_to_obj("die", bm, coll, smooth=False)
    bv = _bevel(o_, s * 0.12, 3, limit="NONE")
    bv.harden_normals = False
    _apply_mods(o_)
    _smooth(o_)
    _noise_displace(o_, s * 0.012, 260.0, seed=variant + 1)
    _assign(o_, mat_dice())
    o_.location.z = sc[2] / 2
    if top is not None:
        rot = {1: (0, 0), 6: (180, 0), 2: (0, 90), 5: (0, -90), 3: (-90, 0), 4: (90, 0)}[int(top)]
        o_.rotation_euler = (math.radians(rot[0]), math.radians(rot[1]), rnd.uniform(-0.5, 0.5))
        _ground([o_])
    return [o_]


def _vessel_profile(outer, thick, floor):
    """Build a hollow lathe profile from an outer profile [(r, z)] that starts at (0, 0) and ends at the
    rim; the inner wall is offset by `thick`, the inner floor is at z=floor."""
    prof = list(outer)
    rim_r, rim_z = outer[-1]
    inner = []
    for (r, z) in reversed(outer[1:]):
        if z < floor:
            continue
        inner.append((max(0.0005, r - thick), z if z < rim_z else rim_z - 0.0005))
    # rounded lip
    prof.append((rim_r - thick * 0.5, rim_z + thick * 0.35))
    prof += inner
    prof.append((0, floor))
    return prof


def _handle(name, p0, p1, bulge, r, coll, mat, n=16, flat=0.65):
    """Loop handle from p0 to p1 bulging outward along `bulge` vector (strap handle, elliptical section)."""
    p0, p1, bulge = Vector(p0), Vector(p1), Vector(bulge)
    pts = []
    for i in range(n + 1):
        t = i / n
        p = p0.lerp(p1, t) + bulge * math.sin(math.pi * t) * 1.0
        pts.append(p)
    h = _tube(name, pts, r, coll, seg=10)
    # flatten section toward the radial direction (strap)
    _assign(h, mat)
    return h


def _jar_handles(prof_fn, z0, z1, r_out, coll, mat, count=2, size=0.012, out=0.05, ang0=0.0):
    hs = []
    for k in range(count):
        a = ang0 + 2 * math.pi * k / count
        d = Vector((math.cos(a), math.sin(a), 0))
        p0 = d * (prof_fn(z0) - 0.004) + Vector((0, 0, z0))
        p1 = d * (prof_fn(z1) - 0.004) + Vector((0, 0, z1))
        hs.append(_handle("handle", p0, p1, d * out, size, coll, mat))
    return hs


def _interp_profile(outer):
    def f(z):
        for i in range(len(outer) - 1):
            (r0, z0), (r1, z1) = outer[i], outer[i + 1]
            if z0 <= z <= z1 and z1 > z0:
                return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
        return outer[-1][0]
    return f


def _build_water_jar(variant=0, rnd=None, coll=None, root=None, **o):
    rnd = rnd or random.Random(variant)
    parts = []
    if variant == 0:     # two-handled storage / water jar ~48 cm
        outer = [(0, 0), (0.05, 0), (0.07, 0.012), (0.12, 0.06), (0.155, 0.15), (0.165, 0.23), (0.155, 0.30),
                 (0.125, 0.36), (0.075, 0.395), (0.055, 0.41), (0.05, 0.44), (0.054, 0.465), (0.062, 0.475)]
        thick, mk = 0.009, "terracotta"
    elif variant == 1:   # pitcher / jug ~30 cm
        outer = [(0, 0), (0.045, 0), (0.055, 0.01), (0.085, 0.05), (0.098, 0.11), (0.092, 0.17), (0.07, 0.215),
                 (0.045, 0.245), (0.04, 0.27), (0.044, 0.29), (0.05, 0.30)]
        thick, mk = 0.006, "buff"
    else:                # round small jug ~22 cm
        outer = [(0, 0), (0.035, 0), (0.05, 0.01), (0.085, 0.06), (0.095, 0.10), (0.085, 0.145), (0.05, 0.175),
                 (0.032, 0.19), (0.03, 0.205), (0.036, 0.218)]
        thick, mk = 0.005, "dark"
    # throwing rings (wheel marks)
    ringed = []
    for (r, z) in outer:
        ringed.append((r, z))
    prof = _vessel_profile(ringed, thick, thick * 1.6)
    body = _lathe("jar_body", prof, 56, coll, wobble=0.012, seed=variant + 1)
    _subsurf(body, 1)
    # wheel ridges via displacement on Z
    _apply_mods(body)
    me = body.data
    for v in me.vertices:
        rr = math.hypot(v.co.x, v.co.y)
        if rr > 0.01:
            f = 1 + 0.004 * math.sin(v.co.z * 260 + variant)
            v.co.x *= f
            v.co.y *= f
    m = mat_clay(mk)
    _assign(body, m)
    parts.append(body)
    pf = _interp_profile(outer)
    zt = outer[-1][1]
    if variant == 0:
        parts += _jar_handles(pf, 0.30, 0.40, 0, coll, m, 2, 0.011, 0.045, ang0=0.0)
        root["mouth"] = [0, 0, zt]
    elif variant == 1:
        h = _handle("handle", Vector((-(pf(0.15) - 0.004), 0, 0.15)), Vector((-(pf(0.265) - 0.003), 0, 0.27)),
                    Vector((-0.07, 0, 0.01)), 0.009, coll, m)
        parts.append(h)
        # pinch a spout at +X... front is -Y: put spout toward -Y, handle +Y
        for p in parts:
            p.rotation_euler.z = math.radians(90)
        me = body.data
        for v in me.vertices:
            if v.co.z > 0.27 and v.co.y < 0:
                k = min(1, (v.co.z - 0.27) / 0.03) * max(0, -v.co.y / 0.05) ** 2
                v.co.y -= 0.014 * k
                v.co.z += 0.006 * k
        root["mouth"] = [0, -0.06, 0.3]
    else:
        h = _handle("handle", Vector((pf(0.12) - 0.004, 0, 0.12)), Vector((pf(0.19) - 0.003, 0, 0.195)),
                    Vector((0.05, 0, 0.02)), 0.007, coll, m)
        parts.append(h)
        root["mouth"] = [0, 0, zt]
    return parts


def _build_amphora(variant=0, rnd=None, coll=None, root=None, **o):
    outer = [(0, 0), (0.012, 0.0), (0.02, 0.04), (0.06, 0.16), (0.13, 0.38), (0.165, 0.55), (0.16, 0.66),
             (0.12, 0.72), (0.07, 0.75), (0.055, 0.8), (0.052, 0.88), (0.06, 0.915), (0.065, 0.93)]
    prof = _vessel_profile(outer, 0.01, 0.08)
    body = _lathe("amphora_body", prof, 56, coll, wobble=0.01, seed=7)
    _subsurf(body, 1)
    _apply_mods(body)
    m = mat_clay("terracotta")
    _assign(body, m)
    pf = _interp_profile(outer)
    hs = []
    for k in range(2):
        a = math.pi * k
        d = Vector((math.cos(a), math.sin(a), 0))
        p0 = d * (pf(0.70) - 0.005) + Vector((0, 0, 0.70))
        p1 = d * (pf(0.86) - 0.004) + Vector((0, 0, 0.86))
        pts = [p0, p0 + d * 0.06 + Vector((0, 0, 0.06)), p0 + d * 0.07 + Vector((0, 0, 0.14)),
               p1 + d * 0.035 + Vector((0, 0, 0.02)), p1]
        # smooth polyline
        sm = []
        for i in range(len(pts) - 1):
            for j in range(6):
                t = j / 6
                sm.append(pts[i].lerp(pts[i + 1], t))
        sm.append(pts[-1])
        h = _tube("amphora_handle", sm, 0.013, coll, seg=10)
        _subsurf(h, 1)
        _assign(h, m)
        hs.append(h)
    root["mouth"] = [0, 0, 0.93]
    return [body] + hs


def _build_oil_lamp(variant=0, rnd=None, coll=None, root=None, **o):
    """Herodian lamp: round wheel-made body, flat-ish top with large filling hole, spatulate nozzle (-Y)."""
    R, H = 0.036, 0.028
    # body as lathe (closed, then remesh union with nozzle, then cut holes)
    prof = [(0, 0.0), (0.016, 0.0), (0.02, 0.0015), (0.03, 0.006), (R, 0.014), (R * 0.97, 0.021),
            (0.031, 0.025), (0.024, 0.0265), (0.018, 0.024), (0, 0.022)]
    body = _lathe("lamp_body", prof, 48, coll)
    # nozzle loft (along -Y)
    secs = []
    n = 12
    for i in range(n + 1):
        t = i / n
        y = -0.012 - 0.050 * t
        # spatulate: narrow at the neck, splayed at the end with concave sides
        hw = 0.011 + 0.003 * math.sin(math.pi * t) * 0 + (0.0085 * (t ** 3)) - 0.003 * math.sin(math.pi * t * 0.9)
        hw = max(0.0075, hw)
        zb = 0.006 + 0.004 * t
        zt = 0.0215 - 0.003 * t
        k = 12
        sec = []
        for j in range(k):
            a = 2 * math.pi * j / k
            sec.append((hw * math.cos(a), y, (zb + zt) / 2 + (zt - zb) / 2 * math.sin(a)))
        secs.append(sec)
    nz = _loft("lamp_nozzle", secs, coll)
    lamp = _join([body, nz], "oil_lamp")
    _remesh(lamp, 0.0009)
    # cut filling hole + wick hole with bmesh (delete verts inside cylinders) then smooth
    bm = bmesh.new()
    bm.from_mesh(lamp.data)
    wick = Vector((0, -0.057, 0.0185))
    kill = [v for v in bm.verts if (math.hypot(v.co.x, v.co.y) < 0.0078 and v.co.z > 0.015)
            or ((Vector((v.co.x, v.co.y, 0)) - Vector((wick.x, wick.y, 0))).length < 0.0045 and v.co.z > 0.014)]
    bmesh.ops.delete(bm, geom=kill, context="VERTS")
    # thicken: solidify later
    bm.to_mesh(lamp.data)
    bm.free()
    sol = lamp.modifiers.new("solid", "SOLIDIFY")
    sol.thickness = 0.0028
    sol.offset = -1
    _apply_mods(lamp)
    _noise_displace(lamp, 0.00025, 400.0, seed=variant + 2)
    _smooth(lamp)
    m = _lamp_material(variant)
    _assign(lamp, m)
    root["flame"] = [0, -0.057, 0.024]
    return [lamp]


def _lamp_material(variant):
    """Clay with soot darkening near the wick (object-space distance)."""
    name = "A_lamp_clay_%d" % variant
    m = bpy.data.materials.get(name)
    if m:
        return m
    base = mat_clay("buff" if variant == 0 else "grey")
    m = base.copy()
    m.name = name
    N, L = m.node_tree.nodes, m.node_tree.links
    b = N["Principled BSDF"]
    src = b.inputs["Base Color"].links[0].from_socket
    tc = N.new("ShaderNodeTexCoord")
    vd = N.new("ShaderNodeVectorMath")
    vd.operation = "DISTANCE"
    vd.inputs[1].default_value = (0, -0.057, 0.02)
    L.new(tc.outputs["Object"], vd.inputs[0])
    mr = N.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.006
    mr.inputs["From Max"].default_value = 0.022
    mr.inputs["To Min"].default_value = 0.92
    mr.inputs["To Max"].default_value = 0.0
    L.new(vd.outputs["Value"], mr.inputs["Value"])
    mx = N.new("ShaderNodeMix")
    mx.data_type = "RGBA"
    L.new(mr.outputs["Result"], mx.inputs[0])
    L.new(src, mx.inputs[6])
    mx.inputs[7].default_value = (0.02, 0.015, 0.012, 1)
    L.new(mx.outputs[2], b.inputs["Base Color"])
    return m


def _build_candle(variant=0, rnd=None, coll=None, root=None, height=0.22, radius=0.011, drips=True,
                  holder=False, **o):
    rnd = rnd or random.Random(variant + 11)
    h, r = height, radius
    parts = []
    z0 = 0.0
    if holder:
        hp = [(0, 0), (0.045, 0), (0.048, 0.004), (0.04, 0.008), (0.016, 0.012), (0.014, 0.03), (0.017, 0.034), (0.0, 0.034)]
        hd = _lathe("candle_holder", hp, 40, coll)
        _assign(hd, mat_clay("terracotta"))
        parts.append(hd)
        z0 = 0.026
    # body (scale-z animatable for melting): origin at its base
    prof = [(0, 0), (r * 1.02, 0), (r, 0.01)]
    for i in range(1, 12):
        prof.append((r * (1 - 0.03 * i / 12) * (1 + 0.012 * math.sin(i * 1.7)), h * i / 12))
    prof.append((0, h))
    body = _lathe("body", prof, 36, coll, wobble=0.015, seed=variant)
    body.location.z = z0
    wax = mat_wax()
    _assign(body, wax)
    parts.append(body)
    # top: melted cup + wick (moves with the top of the body)
    rt = r * 0.97
    tp = [(0, -0.0035), (rt * 0.7, -0.003), (rt * 0.93, -0.0005), (rt * 1.02, 0.0012), (rt * 0.98, 0.0022),
          (rt * 0.88, 0.0014), (rt * 0.6, -0.0012), (0, -0.0018)]
    top = _lathe("top", tp, 36, coll, wobble=0.05, seed=variant + 5)
    top.location.z = z0 + h
    _assign(top, wax)
    parts.append(top)
    wpts = [Vector((0, 0, -0.002)), Vector((0.0004, 0, 0.004)), Vector((0.0013, 0.0002, 0.009)),
            Vector((0.0026, 0.0004, 0.0125))]
    wk = _tube("wick", wpts, 0.00055, coll, seg=6)
    _assign(wk, C.mat("A_wick", (0.015, 0.012, 0.01), rough=0.9) if not bpy.data.materials.get("A_wick")
            else bpy.data.materials["A_wick"])
    wk.parent = top
    # drips down the side
    if drips:
        for k in range(rnd.randint(3, 5)):
            a = rnd.uniform(0, 2 * math.pi)
            L_ = rnd.uniform(0.015, 0.06)
            zt = h - 0.0005
            pts = []
            for i in range(9):
                t = i / 8
                pts.append(Vector((math.cos(a) * (r * 0.99), math.sin(a) * (r * 0.99), zt - L_ * t)) +
                           Vector((math.cos(a), math.sin(a), 0)) * 0.0006)
            d = _tube("drip", pts, 0.0016, coll, seg=8, radius_fn=lambda t: 0.0011 + 0.0011 * math.sin(math.pi * (0.25 + 0.75 * t)))
            _assign(d, wax)
            d.parent = top
            d.location = (0, 0, -h)        # relative to top (top sits at h)
    # puddle at the base (scale to animate melting)
    pp = [(0, 0), (r * 2.4, 0.0), (r * 2.45, 0.0012), (r * 2.2, 0.0026), (r * 1.2, 0.0034), (0, 0.0036)]
    pu = _lathe("puddle", pp, 40, coll, wobble=0.18, seed=variant + 9)
    pu.location.z = z0
    pu.scale = (0.45, 0.45, 0.6)
    _assign(pu, wax)
    parts.append(pu)
    root["flame"] = [0.0026, 0.0004, z0 + h + 0.0125]
    root["height"] = h
    return parts


def melt_candle(root, f0, f1, amount=0.75, ease=True):
    """Animate a load('candle') instance melting between frames f0..f1: the body shortens by `amount`
    (fraction of its height), the top cup (with wick and drips) follows, the puddle spreads. Updates
    nothing else - re-read A.anchor(root, 'flame') per frame for the flame (or parent the flame to the
    child object named 'top*', whose origin is the wax surface centre)."""
    body = next(c for c in root.children if c.name.startswith("body"))
    top = next(c for c in root.children if c.name.startswith("top"))
    pud = next(c for c in root.children if c.name.startswith("puddle"))
    h = root["height"]
    z0 = body.location.z
    for f in range(int(f0), int(f1) + 1, 2):
        u = (f - f0) / max(1, f1 - f0)
        e = C.ease_in_out(u) if ease else u
        k = 1 - amount * e
        body.scale = (1 + 0.04 * e, 1 + 0.04 * e, k)
        body.keyframe_insert("scale", frame=f)
        top.location = (0, 0, z0 + h * k)
        top.keyframe_insert("location", frame=f)
        s = 0.45 + 1.1 * e
        pud.scale = (s, s * (1 + 0.1 * math.sin(e * 3)), 0.6 + 0.8 * e)
        pud.keyframe_insert("scale", frame=f)


def _build_potsherd(variant=0, rnd=None, coll=None, root=None, size=0.08, **o):
    """Curved shard cut from a jar wall; fresh break edges get the lighter 'break' clay."""
    rnd = rnd or random.Random(variant * 7 + 1)
    R = rnd.uniform(0.12, 0.2)                 # vessel radius at the shard
    th = rnd.uniform(0.006, 0.009)
    # irregular outline polygon in (s, t) metres
    nv = rnd.randint(5, 8)
    outline = []
    for i in range(nv):
        a = 2 * math.pi * i / nv + rnd.uniform(-0.25, 0.25)
        rr = size * 0.5 * rnd.uniform(0.55, 1.0)
        outline.append((math.cos(a) * rr, math.sin(a) * rr * rnd.uniform(0.6, 1.0)))
    # densify outline with jaggedness
    pts2 = []
    for i in range(nv):
        p, q = outline[i], outline[(i + 1) % nv]
        for j in range(5):
            t = j / 5
            x = p[0] + (q[0] - p[0]) * t + rnd.uniform(-1, 1) * size * 0.012
            y = p[1] + (q[1] - p[1]) * t + rnd.uniform(-1, 1) * size * 0.012
            pts2.append((x, y))
    bm = bmesh.new()
    top = [bm.verts.new((x, y, th)) for x, y in pts2]
    bot = [bm.verts.new((x, y, 0)) for x, y in pts2]
    ft = bm.faces.new(top)
    fb = bm.faces.new(list(reversed(bot)))
    sides = []
    n = len(pts2)
    for i in range(n):
        j = (i + 1) % n
        sides.append(bm.faces.new((bot[i], bot[j], top[j], top[i])))
    for f in sides:
        f.material_index = 1
    bmesh.ops.triangulate(bm, faces=[ft, fb])
    bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if not (e.verts[0].co.z != e.verts[1].co.z)],
                              cuts=3, use_grid_fill=False)
    # bend onto the vessel radius (cylinder around Y axis at z=-R) plus vertical curvature
    curv_v = rnd.uniform(-0.6, 1.2) / R
    for v in bm.verts:
        x, y, z = v.co
        ang = x / R
        rr = R + z
        v.co = Vector((math.sin(ang) * rr, y, math.cos(ang) * rr - R - 0.5 * curv_v * y * y))
    o_ = _bm_to_obj("potsherd", bm, coll, smooth=True)
    _noise_displace(o_, 0.0006, 180.0, seed=variant + 0.3)
    outer = mat_clay(rnd.choice(["terracotta", "slip", "buff", "grey"]))
    o_.data.materials.append(outer)
    o_.data.materials.append(mat_clay("break"))
    _smooth(o_, 40)
    # lie on the ground in a random stable way (convex side down mostly)
    flip = rnd.random() < 0.35
    o_.rotation_euler = (math.radians(180) if flip else 0, rnd.uniform(-0.15, 0.15), rnd.uniform(0, 6.28))
    _ground([o_])
    return [o_]


# ---- crowns ----
def _ring_band(name, r, h, th, coll, mat, seg=96, z0=0.0, flare=0.0):
    prof = [(r, z0), (r + th, z0), (r + th + flare, z0 + h), (r + flare, z0 + h)]
    bm = bmesh.new()
    rings = []
    for (rr, z) in prof:
        rings.append([bm.verts.new((math.cos(2 * math.pi * i / seg) * rr, math.sin(2 * math.pi * i / seg) * rr, z))
                      for i in range(seg)])
    for k in range(4):
        a, b = rings[k], rings[(k + 1) % 4]
        for i in range(seg):
            j = (i + 1) % seg
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o_ = _bm_to_obj(name, bm, coll)
    _assign(o_, mat)
    _bevel(o_, th * 0.3, 2)
    return o_


def _torus(name, R, r, coll, mat, z=0.0, seg=96, mseg=10, beads=0):
    bm = bmesh.new()
    rings = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        rr = r * (1 + (0.35 * abs(math.sin(a * beads / 2)) if beads else 0))
        c = Vector((math.cos(a) * R, math.sin(a) * R, z))
        d = Vector((math.cos(a), math.sin(a), 0))
        rings.append([bm.verts.new(c + d * math.cos(2 * math.pi * j / mseg) * rr + Vector((0, 0, 1)) * math.sin(2 * math.pi * j / mseg) * rr)
                      for j in range(mseg)])
    for i in range(seg):
        a, b = rings[i], rings[(i + 1) % seg]
        for j in range(mseg):
            k = (j + 1) % mseg
            bm.faces.new((a[j], b[j], b[k], a[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o_ = _bm_to_obj(name, bm, coll)
    _assign(o_, mat)
    return o_


def _gem(name, r, coll, kind, cabochon=True, setting_mat=None):
    """Cabochon (dome) or faceted gem with a gold bezel ring; local +Z = outward normal."""
    objs = []
    if cabochon:
        prof = [(0, 0)] + [(r * math.cos(a), r * 0.75 * math.sin(a)) for a in
                           [math.pi / 2 * (1 - i / 8) for i in range(9)]][::-1][:-1] + [(0, r * 0.75)]
        prof = [(0, 0), (r, 0)] + [(r * math.cos(math.pi / 2 * i / 8), r * 0.8 * math.sin(math.pi / 2 * i / 8))
                                   for i in range(1, 9)]
        prof[-1] = (0, r * 0.8)
        g = _lathe(name, prof, 24, coll)
    else:
        prof = [(0, -r * 0.6), (r, 0), (r * 0.62, r * 0.35), (0, r * 0.35)]
        g = _lathe(name, prof, 8, coll, smooth=False)
    _assign(g, mat_gem(kind))
    objs.append(g)
    if setting_mat is not None:
        s = _torus(name + "_bezel", r * 1.05, r * 0.2, coll, setting_mat, z=r * 0.08, seg=24, mseg=6)
        s.parent = g
        objs.append(s)
    return g


def _place_on_band(obj, r, ang, z, tilt=0.0):
    obj.location = (math.cos(ang) * r, math.sin(ang) * r, z)
    obj.rotation_euler = (0, math.radians(90) - tilt, ang)


def _build_crown(variant=0, rnd=None, coll=None, root=None, **o):
    rnd = rnd or random.Random(variant + 21)
    gold = mat_gold("yellow" if variant != 2 else "pale")
    parts = []
    R = 0.092
    gems = ["ruby", "emerald", "sapphire", "ruby", "amethyst", "emerald", "garnet", "sapphire"]
    if variant in (0, 1, 3):
        H = 0.04 if variant != 3 else 0.035
        band = _ring_band("crown_band", R, H, 0.0035, coll, gold, flare=0.006 if variant != 3 else 0.0)
        parts.append(band)
        parts.append(_torus("crown_rim_lo", R + 0.0035, 0.0028, coll, gold, z=0.002, beads=48))
        parts.append(_torus("crown_rim_hi", R + 0.0035 + (0.006 if variant != 3 else 0), 0.0024, coll, gold, z=H - 0.001,
                            beads=48))
        ng = 8
        for k in range(ng):
            a = 2 * math.pi * k / ng + math.pi / 2
            g = _gem("gem", 0.0075 if k % 2 == 0 else 0.0055, coll, gems[k % len(gems)], cabochon=(k % 2 == 0),
                     setting_mat=gold)
            _place_on_band(g, R + 0.0055 + 0.003, a, H * 0.5, tilt=-0.08)
            parts.append(g)
        for k in range(ng):         # pearls between gems
            a = 2 * math.pi * (k + 0.5) / ng + math.pi / 2
            pbm = C.prim("uv_sphere", name="pearl", radius=0.0028, segments=12, ring_count=8)
            _place_on_band(pbm, R + 0.0062, a, H * 0.5)
            _assign(pbm, mat_gem("pearl"))
            parts.append(pbm)
    if variant == 0:      # radiate spikes
        n = 12
        for k in range(n):
            a = 2 * math.pi * k / n + math.pi / 2
            hgt = 0.06 if k % 2 == 0 else 0.042
            w = 0.013
            secs = []
            for i in range(9):
                t = i / 8
                ww = w * (1 - t) ** 1.1 + 0.0008
                th_ = 0.0025 * (1 - 0.6 * t)
                z = 0.036 + hgt * t
                secs.append([(-ww, 0, z), (0, th_, z), (ww, 0, z), (0, -th_, z)])
            sp = _loft("spike", secs, coll)
            rr = R + 0.004 + 0.006 * (0.036 + 0.0) / 0.04
            sp.location = (math.cos(a) * (R + 0.008), math.sin(a) * (R + 0.008), 0)
            sp.rotation_euler = (0, 0, a + math.pi / 2)
            sp.rotation_euler.rotate_axis("X", math.radians(-7))
            _assign(sp, gold)
            parts.append(sp)
            pr = C.prim("uv_sphere", name="pearl", radius=0.004 if k % 2 == 0 else 0.0032, segments=12, ring_count=8)
            tipz = 0.036 + hgt + 0.002
            pr.location = (math.cos(a) * (R + 0.008 + 0.007 * hgt / 0.06), math.sin(a) * (R + 0.008 + 0.007 * hgt / 0.06), tipz)
            _assign(pr, mat_gem("pearl") if k % 2 else gold)
            parts.append(pr)
    elif variant in (1, 3):   # fleurons (trefoil points)
        n = 8 if variant == 1 else 4
        for k in range(n):
            a = 2 * math.pi * k / n + math.pi / 2
            big = (k % 2 == 0) or variant == 3
            s = 1.0 if big else 0.7
            fl = []
            stem = _tube("fleur_stem", [(0, 0, 0.034), (0, 0, 0.034 + 0.03 * s)], 0.0035 * s, coll, seg=8)
            fl.append(stem)
            for (dx, dz, rr) in ((0, 0.036 * s, 0.0085), (-0.011 * s, 0.024 * s, 0.0068), (0.011 * s, 0.024 * s, 0.0068)):
                lobe = C.prim("uv_sphere", name="fleur_lobe", radius=rr * s, segments=16, ring_count=10)
                lobe.location = (dx, 0, 0.034 + dz)
                lobe.scale = (0.8, 0.45, 1.25 if dx == 0 else 1.0)
                fl.append(lobe)
            f = _join(fl, "fleuron")
            _assign(f, gold)
            f.location = (math.cos(a) * (R + 0.006), math.sin(a) * (R + 0.006), 0)
            f.rotation_euler = (0, 0, a + math.pi / 2)
            f.rotation_euler.rotate_axis("X", math.radians(-6))
            parts.append(f)
            g = _gem("gem", 0.0045 * s, coll, gems[(k + 3) % len(gems)], cabochon=True, setting_mat=gold)
            g.location = (math.cos(a) * (R + 0.0115), math.sin(a) * (R + 0.0115), 0.034 + 0.02 * s)
            g.rotation_euler = (0, math.radians(90) + math.radians(6), a)
            parts.append(g)
        if variant == 3:     # two crossing arches + orb, velvet cap
            for k in range(2):
                pts = []
                for i in range(33):
                    t = i / 32
                    ang = math.pi * t
                    x = math.cos(ang) * (R + 0.004)
                    z = 0.06 + math.sin(ang) * 0.085 * (1 - 0.18 * math.sin(ang) ** 4)
                    pts.append((x, 0, z))
                arc = _tube("arch", pts, 0.0045, coll, seg=10)
                _assign(arc, gold)
                arc.rotation_euler = (0, 0, math.pi / 4 + k * math.pi / 2)
                parts.append(arc)
                for i in range(1, 12):
                    t = i / 12
                    ang = math.pi * t
                    pr = C.prim("uv_sphere", name="pearl", radius=0.003, segments=10, ring_count=6)
                    pr.location = Matrix.Rotation(math.pi / 4 + k * math.pi / 2, 3, "Z") @ Vector(
                        (math.cos(ang) * (R + 0.004), 0, 0.06 + math.sin(ang) * 0.085 * (1 - 0.18 * math.sin(ang) ** 4) + 0.006))
                    _assign(pr, mat_gem("pearl"))
                    parts.append(pr)
            orb = C.prim("uv_sphere", name="orb", radius=0.012, segments=24, ring_count=14)
            orb.location = (0, 0, 0.06 + 0.085 * 0.82 + 0.012)
            _assign(orb, gold)
            parts.append(orb)
            fin = C.prim("uv_sphere", name="finial", radius=0.006, segments=16, ring_count=10)
            fin.location = (0, 0, orb.location.z + 0.016)
            _assign(fin, mat_gem("ruby"))
            parts.append(fin)
            cap = _lathe("velvet_cap", [(R - 0.001, 0.005)] + [(R * math.cos(t * math.pi / 2) * 0.98 + 0.0001,
                                                                 0.03 + 0.055 * math.sin(t * math.pi / 2))
                                                                for t in [i / 10 for i in range(11)]], 48, coll)
            _assign(cap, mat_velvet())
            parts.append(cap)
    elif variant == 2:    # gold laurel wreath (Roman corona): two branches meeting at the front (-Y)
        leaf_m = gold
        n = 15
        z0 = 0.016
        Z = Vector((0, 0, 1))
        for side in (-1, 1):
            stem_pts = []
            for k in range(n):
                t = k / (n - 1)
                phi = math.radians(90) - side * math.radians(8 + 160 * t)     # back (+Y) -> front (-Y)
                p0 = Vector((math.cos(phi) * R, math.sin(phi) * R, z0))
                T = Vector((math.sin(phi), -math.cos(phi), 0)) * side
                Nout = Vector((math.cos(phi), math.sin(phi), 0))
                for j, alpha in enumerate((32, -28)):
                    sz = 1.0 - 0.3 * t
                    lf = _leaf("laurel", 0.036 * sz, 0.0085 * sz, coll)
                    _assign(lf, leaf_m)
                    a_ = math.radians(alpha + rnd.uniform(-6, 6))
                    d = (T * math.cos(a_) + Z * math.sin(a_)).normalized()
                    nrm = (Nout + Z * (0.25 if alpha > 0 else -0.1)).normalized()
                    w = d.cross(nrm).normalized()
                    nrm = w.cross(d).normalized()
                    M = Matrix((w, d, nrm)).transposed().to_4x4()
                    lf.matrix_basis = Matrix.Translation(p0 + Nout * 0.002 * j) @ M
                    parts.append(lf)
                stem_pts.append(p0 - Nout * 0.001)
            st = _tube("laurel_stem", stem_pts, 0.0022, coll, seg=8)
            _assign(st, gold)
            parts.append(st)
        for k in range(8):
            phi = math.radians(90 + (k - 3.5) * 22)
            if abs(k - 3.5) < 1:
                continue
            b_ = C.prim("uv_sphere", name="berry", radius=0.0035, segments=10, ring_count=6)
            b_.location = (math.cos(phi) * R * 1.06, math.sin(phi) * R * 1.06, z0 + 0.004)
            _assign(b_, gold)
            parts.append(b_)
        # ribbon tie at the back
        for side in (-1, 1):
            rb = _tube("ribbon", [(side * 0.004, R, z0), (side * 0.012, R + 0.02, z0 - 0.02), (side * 0.016, R + 0.026, z0 - 0.05)],
                       0.0025, coll, seg=8)
            _assign(rb, gold)
            parts.append(rb)
    for p in parts:
        if p.type == "MESH" and p.name.startswith(("crown_", "spike", "fleuron", "arch")):
            _smooth(p)
    _ground([p for p in parts if p.parent is None])
    return parts


def _leaf(name, length, width, coll):
    """Lanceolate leaf along +Y (width X, normal +Z) with a midrib fold and slight curl."""
    secs = []
    for i in range(11):
        t = i / 10
        w = width * math.sin(math.pi * min(1.0, t * 1.02)) ** 0.75 + 0.0002
        y = length * t
        c = 0.0025 * math.sin(math.pi * t) - 0.002 * t * t
        secs.append([(-w, y, c - 0.0012 * (w / width)), (0, y, c + 0.0009), (w, y, c - 0.0012 * (w / width)),
                     (0, y, c - 0.0003)])
    lf = _loft(name, secs, coll)
    return lf


def _build_goblet(variant=0, rnd=None, coll=None, root=None, wine=False, **o):
    gold = mat_gold("yellow" if variant != 3 else "red")
    parts = []
    gems = ["ruby", "emerald", "sapphire", "amethyst"]
    if variant == 0:      # tall chalice
        outer = [(0, 0), (0.05, 0), (0.052, 0.004), (0.045, 0.01), (0.02, 0.025), (0.009, 0.045), (0.008, 0.06),
                 (0.018, 0.07), (0.019, 0.078), (0.009, 0.088), (0.008, 0.1), (0.016, 0.108), (0.034, 0.118),
                 (0.044, 0.135), (0.048, 0.16), (0.049, 0.185)]
        floor, band_z, band_r = 0.112, 0.15, 0.047
    elif variant == 1:    # wide goblet, low stem
        outer = [(0, 0), (0.042, 0), (0.044, 0.005), (0.03, 0.012), (0.011, 0.025), (0.01, 0.04), (0.02, 0.046),
                 (0.011, 0.054), (0.03, 0.06), (0.055, 0.075), (0.064, 0.095), (0.066, 0.115)]
        floor, band_z, band_r = 0.056, 0.098, 0.064
    elif variant == 2:    # kantharos: deep cup, two high handles
        outer = [(0, 0), (0.035, 0), (0.037, 0.005), (0.015, 0.016), (0.01, 0.03), (0.022, 0.04), (0.04, 0.05),
                 (0.046, 0.075), (0.044, 0.1), (0.05, 0.12)]
        floor, band_z, band_r = 0.045, 0.085, 0.045
    else:                 # squat jewelled cup
        outer = [(0, 0), (0.035, 0), (0.036, 0.008), (0.03, 0.012), (0.045, 0.03), (0.055, 0.055), (0.056, 0.075),
                 (0.052, 0.085)]
        floor, band_z, band_r = 0.016, 0.055, 0.055
    prof = _vessel_profile(outer, 0.0022, floor)
    body = _lathe("goblet", prof, 64, coll)
    _subsurf(body, 1)
    _assign(body, gold)
    parts.append(body)
    # bead rim + band of gems
    parts.append(_torus("goblet_rim", outer[-1][0] - 0.0011, 0.0016, coll, gold, z=outer[-1][1] + 0.0004, seg=64, mseg=8))
    parts.append(_torus("goblet_band", band_r + 0.0006, 0.0018, coll, gold, z=band_z - 0.012, seg=64, mseg=8, beads=40))
    parts.append(_torus("goblet_band2", band_r + 0.0012, 0.0018, coll, gold, z=band_z + 0.012, seg=64, mseg=8, beads=40))
    ng = 6 if variant != 3 else 8
    pf = _interp_profile(outer)
    for k in range(ng):
        a = 2 * math.pi * k / ng + math.pi / 2
        g = _gem("gem", 0.006 if variant != 3 else 0.0065, coll, gems[k % 4], cabochon=(k % 2 == 0), setting_mat=gold)
        _place_on_band(g, pf(band_z) + 0.001, a, band_z)
        parts.append(g)
    if variant == 2:
        for side in (-1, 1):
            pts = [(side * 0.044, 0, 0.11), (side * 0.07, 0, 0.13), (side * 0.085, 0, 0.1), (side * 0.07, 0, 0.065),
                   (side * 0.04, 0, 0.055)]
            sm = []
            for i in range(len(pts) - 1):
                for j in range(5):
                    sm.append(Vector(pts[i]).lerp(Vector(pts[i + 1]), j / 5))
            sm.append(Vector(pts[-1]))
            h = _tube("handle", sm, 0.0035, coll, seg=10)
            _subsurf(h, 1)
            _assign(h, gold)
            parts.append(h)
    if wine:
        rz = floor + (outer[-1][1] - floor) * 0.7
        wd = _lathe("wine", [(0, rz), (pf(rz) - 0.0025, rz), (0, rz)][:2] + [(0, rz)], 48, coll)
        wd = C.prim("circle", name="wine", vertices=48, radius=pf(rz) - 0.0024, fill_type="NGON", loc=(0, 0, rz))
        _assign(wd, mat_wine())
        parts.append(wd)
    root["mouth"] = [0, 0, outer[-1][1]]
    return parts


def _build_clay_cup(variant=0, rnd=None, coll=None, root=None, wine=False, **o):
    if variant == 0:
        outer = [(0, 0), (0.026, 0), (0.03, 0.006), (0.036, 0.03), (0.04, 0.06), (0.043, 0.082)]
        mk = "terracotta"
    else:
        outer = [(0, 0), (0.022, 0), (0.025, 0.005), (0.03, 0.012), (0.044, 0.03), (0.048, 0.05), (0.047, 0.06)]
        mk = "slip"
    prof = _vessel_profile(outer, 0.0045, 0.008)
    cup = _lathe("clay_cup", prof, 48, coll, wobble=0.02, seed=variant + 3)
    _subsurf(cup, 1)
    _apply_mods(cup)
    for v in cup.data.vertices:
        rr = math.hypot(v.co.x, v.co.y)
        if rr > 0.01:
            f = 1 + 0.006 * math.sin(v.co.z * 400)
            v.co.x *= f
            v.co.y *= f
    _assign(cup, mat_clay(mk))
    parts = [cup]
    if wine:
        pf = _interp_profile(outer)
        rz = outer[-1][1] * 0.72
        wd = C.prim("circle", name="wine", vertices=48, radius=pf(rz) - 0.0042, fill_type="NGON", loc=(0, 0, rz))
        _assign(wd, mat_wine())
        parts.append(wd)
    root["mouth"] = [0, 0, outer[-1][1]]
    return parts


def _build_scroll(variant=0, rnd=None, coll=None, root=None, open_width=0.32, lying=False, closed=False, **o):
    """Two rollers (atzei chayim) + parchment. Rollers upright (axis Z) standing on their lower handles,
    open sheet between them facing -Y."""
    parts = []
    PH = 0.30                         # parchment height
    z0 = 0.105                         # parchment bottom (above lower handle + disc)
    rr = 0.026 if not closed else 0.04  # parchment roll radius
    gap = 0.0 if closed else open_width
    wood = mat_wood("olive")
    for side in (-1, 1):
        x = side * (gap / 2 + rr)
        # roller rod with turned handles + discs
        prof = [(0, 0), (0.012, 0), (0.016, 0.01), (0.012, 0.03), (0.018, 0.05), (0.011, 0.07), (0.01, 0.085),
                (0.045, 0.088), (0.046, 0.095), (0.01, 0.098), (0.009, z0 + PH + 0.008), (0.042, z0 + PH + 0.01),
                (0.043, z0 + PH + 0.017), (0.009, z0 + PH + 0.02), (0.011, z0 + PH + 0.04), (0.017, z0 + PH + 0.06),
                (0.012, z0 + PH + 0.085), (0.015, z0 + PH + 0.1), (0.008, z0 + PH + 0.11), (0, z0 + PH + 0.112)]
        rod = _lathe("roller", prof, 32, coll, axis_offset=(x, 0))
        _assign(rod, wood)
        parts.append(rod)
        # parchment roll (outer surface plain parchment)
        roll = _lathe("roll", [(0, z0), (rr, z0), (rr * 1.01, z0 + PH * 0.5), (rr, z0 + PH), (0, z0 + PH)], 40, coll,
                      axis_offset=(x, 0), wobble=0.02, seed=side + 2)
        _assign(roll, mat_parchment(False))
        parts.append(roll)
    if not closed:
        # open sheet: leaves each roll tangentially on the -Y side, sags slightly toward +Y (concave to viewer)
        nu, nv = 40, 6
        bm = bmesh.new()
        uvl = bm.loops.layers.uv.new("UVMap")
        vs = []
        x0, x1 = -(gap / 2 + rr), (gap / 2 + rr)
        for j in range(nv + 1):
            row = []
            z = z0 + PH * j / nv
            for i in range(nu + 1):
                t = i / nu
                x = x0 + (x1 - x0) * t
                y = -rr + 0.025 * math.sin(math.pi * t) + 0.002 * math.sin(t * 19 + j)
                row.append(bm.verts.new((x, y, z)))
            vs.append(row)
        u0, u1 = 0.18, 0.18 + 0.82 * min(1.0, (x1 - x0) / 0.9)
        for j in range(nv):
            for i in range(nu):
                f = bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
                for lp, (ii, jj) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                    lp[uvl].uv = (u1 - (u1 - u0) * ii / nu, jj / nv)
        sheet = _bm_to_obj("sheet", bm, coll)
        sol = sheet.modifiers.new("solid", "SOLIDIFY")
        sol.thickness = 0.0008
        _recalc_normals(sheet)
        sheet.data.materials.append(mat_parchment(True))
        parts.append(sheet)
    if lying:
        R = Matrix.Rotation(math.radians(90), 4, "X")
        for p in parts:
            p.matrix_world = R @ p.matrix_world
        _ground(parts)
    return parts


def _build_flatbread(variant=0, rnd=None, coll=None, root=None, radius=0.11, **o):
    rnd = rnd or random.Random(variant + 31)
    R = radius
    T = 0.036 if variant != 2 else 0.024
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=1.0)
    ph1 = rnd.random() * 6
    for v in bm.verts:
        x, y, z = v.co
        a = math.atan2(y, x)
        rr = R * (1 + 0.04 * math.sin(3 * a + ph1) + 0.025 * math.sin(5 * a + 2 * ph1))
        # domed top, flat bottom with rounded edge
        rad = math.sqrt(x * x + y * y)
        zz = T * ((0.55 + 0.35 * (1 - rad) ** 0.5) * z if z > 0 else 0.28 * z)
        v.co = Vector((x * rr, y * rr, zz))
    o_ = _bm_to_obj("bread", bm, coll)
    _remesh(o_, 0.0028)
    # blisters / irregular surface
    _noise_displace(o_, 0.0028, 22.0, seed=variant + 1.3)
    _noise_displace(o_, 0.0008, 90.0, seed=variant + 2.1)
    _smooth(o_)
    o_.data.materials.append(mat_bread("crust", 0.25 if variant != 2 else 0.55))
    o_.data.materials.append(mat_bread("crumb"))
    if variant == 1:
        a_, b_ = _split_bread(o_, rnd, coll)
        a_.name, b_.name = "half_a", "half_b"
        a_.location.x -= 0.004
        b_.location.x += 0.004
        b_.rotation_euler.z = math.radians(-4)
        for p in (a_, b_):
            _ground([p])
        return [a_, b_]
    _ground([o_])
    return [o_]


def _split_bread(o_, rnd, coll):
    """Tear a loaf in two along a jagged line (x ~ 0): boolean with a wobbly slab, crumb on the faces."""
    pieces = []
    for side in (-1, 1):
        d = o_.copy()
        d.data = o_.data.copy()
        C.link(d, coll)
        # cutter: big box on the opposite side with a jagged face at x ~ 0
        bm = bmesh.new()
        ny, nz = 26, 6
        verts = []
        for j in range(nz + 1):
            row = []
            for i in range(ny + 1):
                y = -0.2 + 0.4 * i / ny
                z = -0.05 + 0.12 * j / nz
                x = 0.006 * math.sin(y * 70 + rnd.random()) + 0.004 * (rnd.random() - 0.5) + 0.01 * math.sin(y * 18)
                row.append(bm.verts.new((x, y, z)))
            verts.append(row)
        far = [[bm.verts.new((side * 0.3, -0.2 + 0.4 * i / ny, -0.05 + 0.12 * j / nz)) for i in range(ny + 1)]
               for j in range(nz + 1)]
        for j in range(nz):
            for i in range(ny):
                bm.faces.new((verts[j][i], verts[j][i + 1], verts[j + 1][i + 1], verts[j + 1][i]))
                bm.faces.new((far[j][i], far[j + 1][i], far[j + 1][i + 1], far[j][i + 1]))
        for j in range(nz):
            for row_a, row_b in ((verts, far),):
                bm.faces.new((row_a[j][0], row_a[j + 1][0], row_b[j + 1][0], row_b[j][0]))
                bm.faces.new((row_a[j][ny], row_b[j][ny], row_b[j + 1][ny], row_a[j + 1][ny]))
        for i in range(ny):
            bm.faces.new((verts[0][i], far[0][i], far[0][i + 1], verts[0][i + 1]))
            bm.faces.new((verts[nz][i], verts[nz][i + 1], far[nz][i + 1], far[nz][i]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        cut = _bm_to_obj("cutter", bm, coll, smooth=False)
        cut.data.materials.append(mat_bread("crumb"))
        bo = d.modifiers.new("cut", "BOOLEAN")
        bo.operation = "DIFFERENCE"
        bo.solver = "EXACT"
        bo.object = cut
        try:
            bo.material_mode = "TRANSFER"
        except Exception:
            pass
        _apply_mods(d)
        bpy.data.objects.remove(cut)
        # roughen the torn crumb faces
        me = d.data
        mi = [i for i, m in enumerate(me.materials) if m and m.name.startswith("A_bread_crumb")]
        if mi:
            for p in me.polygons:
                if p.material_index in mi:
                    for vi in p.vertices:
                        v = me.vertices[vi]
                        v.co.x += 0.0025 * noise.noise(v.co * 160) * (-side)
        pieces.append(d)
    bpy.data.objects.remove(o_)
    return pieces[0], pieces[1]


def _build_table(variant=0, rnd=None, coll=None, root=None, **o):
    rnd = rnd or random.Random(variant + 41)
    if variant == 0:
        W, D, H, top_t = 1.7, 0.8, 0.75, 0.055
    else:
        W, D, H, top_t = 1.4, 0.7, 0.42, 0.05
    wood = mat_wood_pbr("rough_wood", 2.0, (0.72, 0.6, 0.48))
    wood2 = mat_wood_pbr("wood_table_worn", 1.5, (0.8, 0.7, 0.6))
    parts = []
    nplank = 4
    pw = D / nplank
    for k in range(nplank):
        y = -D / 2 + pw * (k + 0.5)
        dz = rnd.uniform(-0.003, 0.003)
        pl = C.box("plank", (W + rnd.uniform(-0.02, 0.02), pw - 0.006, top_t), (rnd.uniform(-0.01, 0.01), y, H - top_t / 2 + dz),
                   coll=coll)
        bm = pl.modifiers.new("subd", "SUBSURF")
        bm.levels = bm.render_levels = 0
        _bevel(pl, 0.008, 3, limit="NONE")
        _apply_mods(pl)
        # warp + worn edges
        for v in pl.data.vertices:
            v.co.z += 0.004 * math.sin(v.co.x * 2.1 + k) * (1 if v.co.z > 0 else 1)
        _assign(pl, wood if k % 2 == 0 else wood2)
        _smooth(pl, 35)
        pl.rotation_euler.z = rnd.uniform(-0.004, 0.004)
        parts.append(pl)
    # legs + aprons
    lx, ly = W / 2 - 0.12, D / 2 - 0.08
    for sx in (-1, 1):
        for sy in (-1, 1):
            lg = C.box("leg", (0.08, 0.08, H - top_t), (sx * lx, sy * ly, (H - top_t) / 2), coll=coll)
            _bevel(lg, 0.008, 2, limit="NONE")
            _assign(lg, wood)
            lg.rotation_euler = (rnd.uniform(-0.01, 0.01), rnd.uniform(-0.01, 0.01), rnd.uniform(-0.03, 0.03))
            parts.append(lg)
    for sy in (-1, 1):
        ap = C.box("apron", (2 * lx, 0.035, 0.09), (0, sy * ly, H - top_t - 0.045), coll=coll)
        _bevel(ap, 0.006, 2, limit="NONE")
        _assign(ap, wood2)
        parts.append(ap)
    for sx in (-1, 1):
        ap = C.box("apron", (0.035, 2 * ly, 0.09), (sx * lx, 0, H - top_t - 0.045), coll=coll)
        _bevel(ap, 0.006, 2, limit="NONE")
        _assign(ap, wood2)
        parts.append(ap)
    st = C.box("stretcher", (2 * lx, 0.05, 0.05), (0, 0, 0.12 if variant == 0 else 0.08), coll=coll)
    _bevel(st, 0.006, 2, limit="NONE")
    _assign(st, wood)
    parts.append(st)
    for sx in (-1, 1):
        s2 = C.box("stretcher", (0.05, 2 * ly, 0.05), (sx * lx, 0, 0.12 if variant == 0 else 0.08), coll=coll)
        _bevel(s2, 0.006, 2, limit="NONE")
        _assign(s2, wood)
        parts.append(s2)
    root["top"] = H
    return parts


def rope_curve(points, radius=0.009, coll=None, name="rope", twist=None):
    """Three-strand rope following a polyline (list of 3D points, world/root space). Returns a mesh
    object. radius = overall rope radius."""
    pts = [Vector(p) for p in points]
    # resample evenly
    dense = [pts[0]]
    step = radius * 0.8
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        n = max(1, int((b - a).length / step))
        for j in range(1, n + 1):
            dense.append(a.lerp(b, j / n))
    twist = twist or (1.0 / (radius * 7.5))
    strands = []
    s_acc = [0.0]
    for i in range(1, len(dense)):
        s_acc.append(s_acc[-1] + (dense[i] - dense[i - 1]).length)
    up = Vector((0, 0, 1))
    frames = []
    for i, p in enumerate(dense):
        d = (dense[min(i + 1, len(dense) - 1)] - dense[max(i - 1, 0)]).normalized()
        a = d.cross(up)
        if a.length < 1e-3:
            a = d.cross(Vector((1, 0, 0)))
        a.normalize()
        b = d.cross(a).normalized()
        frames.append((a, b))
    objs = []
    for k in range(3):
        sp = []
        for i, p in enumerate(dense):
            a, b = frames[i]
            ang = s_acc[i] * twist * 2 * math.pi + k * 2 * math.pi / 3
            sp.append(p + (a * math.cos(ang) + b * math.sin(ang)) * radius * 0.48)
        st = _tube(name + "_strand", sp, radius * 0.56, coll, seg=8)
        objs.append(st)
    r = _join(objs, name)
    _assign(r, mat_rope())
    return r


def _build_rope(variant=0, rnd=None, coll=None, root=None, length=None, radius=0.009, **o):
    rnd = rnd or random.Random(variant + 51)
    if variant == 0:
        pts = []
        turns = 4.5
        n = 360
        for i in range(n + 1):
            t = i / n
            ang = 2 * math.pi * turns * t
            rr = 0.11 + 0.1 * t + 0.008 * math.sin(ang * 3.1)
            layer = 0.012 * math.sin(ang * 0.5) ** 2 * (1 if (i // 40) % 2 else 0.5)
            pts.append((math.cos(ang) * rr, math.sin(ang) * rr, radius + layer))
        # loose tail
        last = Vector(pts[-1])
        for j in range(1, 30):
            pts.append((last.x + 0.012 * j, last.y - 0.006 * j + 0.03 * math.sin(j * 0.2), radius))
        r = rope_curve(pts, radius, coll)
    else:
        L = length or 1.2
        pts = [(x, 0.03 * math.sin(x * 4.1) + 0.015 * math.sin(x * 9.3), radius) for x in
               [L * i / 60 - L / 2 for i in range(61)]]
        r = rope_curve(pts, radius, coll)
    return [r]


def _build_hyssop(variant=0, rnd=None, coll=None, root=None, upright=False, **o):
    rnd = rnd or random.Random(61)
    L = 1.15
    parts = []
    pts = [(0.004 * math.sin(z * 3), 0, z) for z in [L * i / 30 for i in range(31)]]
    stalk = _tube("hyssop_stalk", pts, 0.006, coll, seg=10, radius_fn=lambda t: 0.0065 - 0.0025 * t)
    _assign(stalk, mat_reed())
    parts.append(stalk)
    for k in range(5):     # nodes
        z = L * (0.15 + 0.17 * k)
        nd = _torus("node", 0.0058 - 0.0005 * k, 0.0012, coll, mat_reed(), z=z, seg=16, mseg=6)
        parts.append(nd)
    sp = C.prim("ico_sphere", name="sponge", subdivisions=4, radius=0.04)
    sp.location = (0, 0, L + 0.025)
    sp.scale = (1.0, 0.85, 1.25)
    _apply_scale(sp)
    _noise_displace(sp, 0.009, 30.0, seed=2.0)
    _noise_displace(sp, 0.003, 120.0, seed=3.0)
    _smooth(sp)
    _assign(sp, mat_sponge())
    parts.append(sp)
    # a few hyssop sprigs (small leaves) near the sponge
    for k in range(10):
        lf = _leaf("hyssop_leaf", 0.022, 0.004, coll)
        _assign(lf, _pmat("A_hyssop_leaf", (0.13, 0.17, 0.06), (0.22, 0.26, 0.1), rough=0.6, sss=0.2))
        a = rnd.uniform(0, 6.28)
        lf.location = (math.cos(a) * 0.006, math.sin(a) * 0.006, L - 0.03 - 0.07 * rnd.random())
        lf.rotation_euler = (math.radians(rnd.uniform(-70, -20)), 0, a + math.pi / 2)
        parts.append(lf)
    root["tip"] = [0, 0, L + 0.025]
    if not upright:
        _lay_down(parts, False, 0.0)
        _ground(parts)
        root["tip"] = [L + 0.025, 0, 0.04]
    return parts


def _apply_scale(o):
    me = o.data
    me.transform(Matrix.Diagonal((*o.scale, 1)))
    o.scale = (1, 1, 1)
    me.update()


# --------------------------------------------------------------------------------------------
# Poly Haven models
# --------------------------------------------------------------------------------------------
def _load_polyhaven(asset, coll, res="1k", **o):
    root, objs = C.ph_model(asset, res=res, coll=coll, name="ph_" + asset)
    bpy.context.view_layer.update()
    # origin at base: shift children so min z = 0 and centred in xy
    mn, mx = bounds(root)
    off = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
    for c in root.children:
        c.location -= off
    return root


# --------------------------------------------------------------------------------------------
# Animals: catalog of source models + rig landmarks
# --------------------------------------------------------------------------------------------
# Each variant: Objaverse/Sketchfab uid, attribution, normalisation (rot_z to face -Y, target bbox
# height in metres), rig landmarks in the normalised model space (metres, facing -Y, ground z=0), gait.
# Landmarks: spine [pelvis, mid, withers], neck [withers, skull], head [skull, snout], jaw [pivot, chin],
# tail [base .. tip], legs FL/HL [top, joint1, joint2, ground] for the LEFT (+X) legs (right = mirrored),
# eyes [left eye centre] (mirrored).
ANIMALS = {}       # filled below by _def_animal()


def _def_animal(name, **v):
    ANIMALS.setdefault(name, []).append(v)


def list_actions(name, variant=0):
    """Names of the actions available for an animal (procedural cycles built on its rig)."""
    a = ANIMALS[name][variant % len(ANIMALS[name])]
    if a.get("static"):
        return ["static"]
    return sorted(_gaits(a).keys())


def ground_speed(name, action, variant=0, speed=1.0):
    """Ground speed (m/s) of a locomotion action at the given playback speed (0 for in-place actions)."""
    a = ANIMALS[name][variant % len(ANIMALS[name])]
    g = _gaits(a).get(action)
    if not g or not g.get("stride"):
        return 0.0
    return g["stride"] / (g["duty"] * g["T"]) * speed


def animal(name, action="idle", loc=(0, 0, 0), rot_z=0.0, start_frame=1, speed=1.0, coll=None, variant=0,
           scale=1.0, move=False, path=None, end_frame=None, eye_glow=0.0, tint=None, offset=0.0, **opts):
    """Create a rigged animal playing a looping action.
    action: one of list_actions(name). start_frame: scene frame where the cycle starts (earlier frames
    hold the first pose). speed: playback speed multiplier (2.0 = twice as fast).
    move=True: the root walks forward (-Y of the animal, rotated by rot_z) at ground_speed().
    path=[(x, y), ...] or [(x, y, z), ...]: walk along this polyline at ground speed, facing the direction
    of travel (overrides move). offset: cycle phase offset in seconds (pack variety).
    eye_glow: 0..1 eyeshine strength (glinting eyes in the dark). tint: (r, g, b) colour multiplier offset,
    e.g. (-0.3, -0.3, -0.3) darker. Returns the armature object (root)."""
    arm = load(name, loc=loc, rot_z=rot_z, scale=scale, coll=coll, variant=variant)
    if eye_glow:
        set_eye_glow(arm, eye_glow)
    if tint is not None:
        arm["tint"] = tuple(tint)
        for c in arm.children:
            c["tint"] = tuple(tint)
    if action and action != "static":
        play(arm, action, start_frame=start_frame, speed=speed, offset=offset)
    sc = bpy.context.scene
    end_frame = end_frame or sc.frame_end
    v = ground_speed(name, action, variant, speed) * (scale if not isinstance(scale, (tuple, list)) else scale[0])
    if path:
        follow_path(arm, path, v, start_frame, end_frame)
    elif move and v > 0:
        a = math.radians(rot_z)
        d = Vector((math.sin(a), -math.cos(a), 0))
        p0 = Vector(loc)
        fps = sc.render.fps
        for f in (start_frame, end_frame):
            arm.location = p0 + d * v * (f - start_frame) / fps
            arm.keyframe_insert("location", frame=f)
        C._set_interp(arm, "location", "LINEAR")
    return arm


def play(arm, action, start_frame=1, speed=1.0, offset=0.0, blend_in=0, replace=True):
    """(Re)assign a looping action to an animal armature from start_frame. Call several times with
    replace=False to sequence actions (later strips override earlier ones from their start)."""
    name = arm["asset"]
    act = _get_action(arm, action)
    ad = arm.animation_data or arm.animation_data_create()
    if replace:
        for t in list(ad.nla_tracks):
            ad.nla_tracks.remove(t)
        ad.action = None
    tr = ad.nla_tracks.new()
    tr.name = action
    fr = act.frame_range
    L = fr[1] - fr[0]
    sc = bpy.context.scene
    need = (sc.frame_end - start_frame + 200) * speed
    st = tr.strips.new(action, int(start_frame), act)
    try:
        if act.slots:
            st.action_slot = act.slots[0]
    except Exception:
        pass
    st.scale = 1.0 / max(1e-3, speed)
    off_frames = (offset * sc.render.fps) % L if L > 0 else 0
    if off_frames:
        st.action_frame_start = fr[0] + off_frames
        st.action_frame_end = fr[1] + off_frames
    st.repeat = max(1.0, need / max(1.0, L))
    st.extrapolation = "HOLD" if replace else "HOLD_FORWARD"
    st.blend_type = "REPLACE"
    if blend_in:
        st.blend_in = blend_in
    return st


def follow_path(obj, points, speed, f0=1, f1=None, smooth=0.25, ground=None):
    """Key obj location + heading along a polyline at constant speed (m/s), facing the travel direction
    (-Y forward). ground(x, y) -> z optional terrain height function."""
    sc = bpy.context.scene
    f1 = f1 or sc.frame_end
    pts = [Vector((p[0], p[1], p[2] if len(p) > 2 else 0.0)) for p in points]
    seg = [(pts[i + 1] - pts[i]).length for i in range(len(pts) - 1)]
    total = sum(seg)
    fps = sc.render.fps

    def at(s):
        s = min(max(s, 0.0), total - 1e-6)
        for i, L in enumerate(seg):
            if s <= L:
                return pts[i].lerp(pts[i + 1], s / L if L else 0)
            s -= L
        return pts[-1]
    prev_h = None
    for f in range(int(f0), int(f1) + 1):
        s = speed * (f - f0) / fps
        p = at(s)
        q = at(s + max(0.3, speed * smooth))
        dvec = q - at(s - max(0.3, speed * smooth))
        if dvec.length > 1e-5:
            h = math.atan2(dvec.x, -dvec.y)
            if prev_h is not None:
                while h - prev_h > math.pi:
                    h -= 2 * math.pi
                while h - prev_h < -math.pi:
                    h += 2 * math.pi
            prev_h = h
        h = prev_h or 0.0
        if ground:
            p.z = ground(p.x, p.y)
        obj.location = p
        obj.rotation_euler = (0, 0, h)
        obj.keyframe_insert("location", frame=f)
        obj.keyframe_insert("rotation_euler", frame=f)
    C._set_interp(obj, "location", "LINEAR")
    C._set_interp(obj, "rotation_euler", "LINEAR")


def circle_path(center=(0, 0), radius=5.0, start_deg=0.0, turns=1.0, clockwise=False, n=72):
    """Points of a circle for follow_path / animal(path=...)."""
    out = []
    for i in range(int(n * turns) + 1):
        a = math.radians(start_deg) + (-1 if clockwise else 1) * 2 * math.pi * i / n
        out.append((center[0] + math.cos(a) * radius, center[1] + math.sin(a) * radius))
    return out


def set_eye_glow(arm, strength=1.0, color=(1.0, 0.85, 0.45)):
    """Eyeshine (tapetum glint) on the eye spheres of an animal: emission strength (animatable via
    arm['eye_glow'] driver-free: call again or keyframe the material input yourself)."""
    for c in arm.children:
        if c.name.startswith("eyes"):
            m = c.data.materials[0].copy()
            b = m.node_tree.nodes["Principled BSDF"]
            b.inputs["Emission Color"].default_value = (*color, 1)
            b.inputs["Emission Strength"].default_value = 6.0 * strength
            c.data = c.data.copy()
            c.data.materials[0] = m
            return m
    return None


# --------------------------------------------------------------------------------------------
# Texture generation (plain python + PIL):  /opt/venv/bin/python lib/assets.py --textures
# --------------------------------------------------------------------------------------------
PSALM22_HE = """למנצח על אילת השחר מזמור לדוד
אלי אלי למה עזבתני רחוק מישועתי דברי שאגתי
אלהי אקרא יומם ולא תענה ולילה ולא דומיה לי
ואתה קדוש יושב תהלות ישראל
בך בטחו אבתינו בטחו ותפלטמו
אליך זעקו ונמלטו בך בטחו ולא בושו
ואנכי תולעת ולא איש חרפת אדם ובזוי עם
כל ראי ילעגו לי יפטירו בשפה יניעו ראש
גל אל יהוה יפלטהו יצילהו כי חפץ בו
כי אתה גחי מבטן מבטיחי על שדי אמי
עליך השלכתי מרחם מבטן אמי אלי אתה
אל תרחק ממני כי צרה קרובה כי אין עוזר
סבבוני פרים רבים אבירי בשן כתרוני
פצו עלי פיהם אריה טרף ושאג
כמים נשפכתי והתפרדו כל עצמותי היה לבי כדונג נמס בתוך מעי
יבש כחרש כחי ולשוני מדבק מלקוחי ולעפר מות תשפתני
כי סבבוני כלבים עדת מרעים הקיפוני כארי ידי ורגלי
אספר כל עצמותי המה יביטו יראו בי
יחלקו בגדי להם ועל לבושי יפילו גורל
ואתה יהוה אל תרחק אילותי לעזרתי חושה
הצילה מחרב נפשי מיד כלב יחידתי
הושיעני מפי אריה ומקרני רמים עניתני
אספרה שמך לאחי בתוך קהל אהללך
יראי יהוה הללוהו כל זרע יעקב כבדוהו וגורו ממנו כל זרע ישראל
כי לא בזה ולא שקץ ענות עני ולא הסתיר פניו ממנו ובשועו אליו שמע
מאתך תהלתי בקהל רב נדרי אשלם נגד יראיו
יאכלו ענוים וישבעו יהללו יהוה דרשיו יחי לבבכם לעד
יזכרו וישבו אל יהוה כל אפסי ארץ וישתחוו לפניך כל משפחות גוים
כי ליהוה המלוכה ומשל בגוים
אכלו וישתחוו כל דשני ארץ לפניו יכרעו כל יורדי עפר ונפשו לא חיה
זרע יעבדנו יספר לאדני לדור
יבאו ויגידו צדקתו לעם נולד כי עשה"""


def _make_textures():
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    os.makedirs(TEX, exist_ok=True)
    W, H = 4096, 1024
    rnd = np.random.default_rng(3)

    def smooth_noise(scale, octaves=4):
        out = np.zeros((H, W), np.float32)
        amp, tot = 1.0, 0.0
        for o in range(octaves):
            s = max(2, int(scale * 2 ** o))
            small = rnd.random((max(2, H * s // W + 1), s)).astype(np.float32)
            im = Image.fromarray((small * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
            out += amp * np.asarray(im, np.float32) / 255.0
            tot += amp
            amp *= 0.5
        return out / tot
    base = np.array([0.80, 0.70, 0.53])
    n1, n2 = smooth_noise(6), smooth_noise(40, 3)
    img = base[None, None, :] * (0.86 + 0.22 * n1[..., None]) * (0.95 + 0.08 * n2[..., None])
    yy = np.linspace(-1, 1, H)[:, None]
    img *= np.clip(1 - (np.abs(yy) - 0.82) * 4, 0.55, 1)[..., None]
    st = smooth_noise(3, 2)
    img *= (1 - 0.18 * np.clip((st - 0.62) * 5, 0, 1))[..., None]
    im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    font = ImageFont.truetype(os.path.join(FONTS, "StamSefaradCLM.ttf"), int(H * 0.034))
    words = " ".join(PSALM22_HE.split("\n")).split(" ")
    ncol = 7
    colw = W // ncol
    margin = int(colw * 0.12)
    top, lh = int(H * 0.10), int(H * 0.040)
    nl = int((H * 0.80) / lh)
    wi = 0
    space = d.textlength(" ", font=font)
    for c in range(ncol):
        x1 = W - c * colw - margin
        width = colw - 2 * margin
        for l in range(nl):
            line = []
            while True:
                wd = words[wi % len(words)]
                trial = " ".join(line + [wd])
                if d.textlength(trial, font=font, direction="rtl") > width and line:
                    break
                line.append(wd)
                wi += 1
            ws = [d.textlength(w_, font=font, direction="rtl") for w_ in line]
            gap = (width - sum(ws)) / max(1, len(line) - 1) if len(line) > 1 else space
            gap = min(gap, space * 4)
            x = x1
            ink = (int(26 + rnd.random() * 10), int(20 + rnd.random() * 8), int(16 + rnd.random() * 6))
            for w_, wl in zip(line, ws):       # right-to-left word placement (justified)
                d.text((x - wl, top + l * lh), w_, font=font, fill=ink, direction="rtl")
                x -= wl + gap
    im = im.filter(ImageFilter.GaussianBlur(0.6))
    im.save(os.path.join(TEX, "scroll_psalm22.png"))
    print("wrote", os.path.join(TEX, "scroll_psalm22.png"))


if __name__ == "__main__" and "--textures" in sys.argv:
    _make_textures()


# --------------------------------------------------------------------------------------------
# Animal build pipeline: import -> normalise -> rig -> weights -> procedural actions -> cache .blend
# --------------------------------------------------------------------------------------------
_MASTERS = {}        # (name, variant) -> (arm, [children]) appended in the current file


def _variant(name, variant):
    vs = ANIMALS[name]
    return vs[variant % len(vs)], variant % len(vs)


def _cache_path(name, vi):
    return os.path.join(CACHE, "%s_v%d_b%d.blend" % (name, vi, BUILD_VERSION))


def _glb_path(uid):
    p = os.path.join(OBJAVERSE, uid + ".glb")
    if not os.path.exists(p):
        import gzip, urllib.request, ssl
        os.makedirs(OBJAVERSE, exist_ok=True)
        idx = os.path.join(MODELS, "objaverse", "object-paths.json.gz")
        base = "https://huggingface.co/datasets/allenai/objaverse/resolve/main/"
        if not os.path.exists(idx):
            ph._download(base + "object-paths.json.gz", idx)
        rel = json.load(gzip.open(idx))[uid]
        ph._download(base + rel, p)
    return p


def _animal_instance(name, variant, coll, **o):
    a, vi = _variant(name, variant)
    key = (name, vi)
    m = _MASTERS.get(key)
    try:
        alive = m is not None and bpy.data.objects.get(m[0].name) is m[0] and all(bpy.data.objects.get(k.name) is k for k in m[1])
    except ReferenceError:
        alive = False
    if not alive:
        path = _cache_path(name, vi)
        if not os.path.exists(path):
            _build_animal_cache(name, vi)
        with bpy.data.libraries.load(path, link=False) as (src, dst):
            dst.objects = list(src.objects)
            dst.actions = list(src.actions)
        objs = [x for x in dst.objects if x is not None]
        arm = next(x for x in objs if x.type in ("ARMATURE", "EMPTY") and x.parent is None)
        for x in objs:
            C.link(x, coll)
        _MASTERS[key] = (arm, [x for x in objs if x is not arm])
        arm["_master"] = True
        return arm
    # further instances: copy objects, share mesh/armature data + actions
    src_arm, kids = m
    arm = src_arm.copy()
    arm.animation_data_clear()
    arm.data = src_arm.data
    for k in list(arm.keys()):
        if k.startswith("_"):
            del arm[k]
    C.link(arm, coll)
    for k in kids:
        d = k.copy()
        d.animation_data_clear()
        C.link(d, coll)
        d.parent = arm
        d.matrix_parent_inverse = k.matrix_parent_inverse.copy()
        for md in d.modifiers:
            if md.type == "ARMATURE":
                md.object = arm
    return arm


def _get_action(arm, action):
    name = arm["asset"]
    vi = arm.get("variant_index", 0)
    an = "%s%d|%s" % (name, vi, action)
    act = bpy.data.actions.get(an)
    if act is None:
        raise KeyError("animal %s has no action %r (have %s)" % (name, action, list_actions(name, vi)))
    return act


def _build_animal_cache(name, vi):
    """Import the source model into a temporary collection of the current scene, normalise, rig,
    animate, write the cache .blend, then delete the temporary objects."""
    a = ANIMALS[name][vi]
    t0 = time.time()
    os.makedirs(CACHE, exist_ok=True)
    sc = bpy.context.scene
    vl = bpy.context.view_layer
    tmpc = bpy.data.collections.new("_asset_build")
    sc.collection.children.link(tmpc)
    prev_alc = vl.active_layer_collection
    vl.active_layer_collection = vl.layer_collection.children[tmpc.name]
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=_glb_path(a["uid"]))
    vl.active_layer_collection = prev_alc
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:            # drop source rigs / animation: we build our own
        o.animation_data_clear()
    vl.update()
    meshes = [o for o in new if o.type == "MESH" and not o.name.startswith("Icosphere")]
    dg = bpy.context.evaluated_depsgraph_get()
    parts = []
    for o in meshes:
        if a.get("drop") and any(x in o.name for x in a["drop"]):
            continue
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
        me.transform(o.matrix_world)
        parts.append(me)
    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)
    body = bpy.data.objects.new("%s%d_body" % (name, vi), parts[0])
    tmpc.objects.link(body)
    for me in parts[1:]:
        ob = bpy.data.objects.new("tmp", me)
        tmpc.objects.link(ob)
        _join([body, ob])
    me = body.data
    # normalise: rotate to face -Y, scale to target height, base at z=0, centred
    me.transform(Matrix.Rotation(math.radians(a.get("rot", 0.0)), 4, "Z"))
    if a.get("rot_x"):
        me.transform(Matrix.Rotation(math.radians(a["rot_x"]), 4, "X"))
    import numpy as np
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    if a.get("crop_z") is not None:     # remove a base / stand below crop_z (fraction of height)
        z0, z1 = co[:, 2].min(), co[:, 2].max()
        cz = z0 + (z1 - z0) * a["crop_z"]
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < cz], context="VERTS")
        bm.to_mesh(me)
        bm.free()
        co = np.empty(len(me.vertices) * 3)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
    mn, mx = co.min(0), co.max(0)
    ph_ = a.get("plot_height", a["height"])
    s = ph_ / (mx[2] - mn[2])
    k = a["height"] / ph_
    me.transform(Matrix.Diagonal((k, k, k, 1)) @ Matrix.Translation((-a.get("x_shift", 0.0), 0, 0)) @
                 Matrix.Diagonal((s, s, s, 1)) @ Matrix.Translation((-float(np.median(co[:, 0])), -(mn[1] + mx[1]) / 2, -mn[2])))
    me.update()
    a = _xf_landmarks(a)
    for p in me.polygons:
        p.use_smooth = True
    _fix_animal_materials(me, a)
    root_obj = None
    if a.get("static") or not a.get("rig"):
        root_obj = bpy.data.objects.new("%s%d" % (name, vi), None)
        tmpc.objects.link(root_obj)
        body.parent = root_obj
        if a.get("eyes"):
            _add_eyes(root_obj, a, None, tmpc)
    else:
        root_obj = _make_rig(name, vi, a, body, tmpc)
        _make_actions(name, vi, a, root_obj)
    root_obj["variant_index"] = vi
    root_obj["source_uid"] = a["uid"]
    # write cache
    objs = [root_obj] + children_recursive(root_obj)
    acts = [x for x in bpy.data.actions if x.name.startswith("%s%d|" % (name, vi))]
    tmpfile = _cache_path(name, vi) + ".part%d" % os.getpid()
    bpy.data.libraries.write(tmpfile, set(objs) | set(acts), fake_user=True, compress=True)
    os.replace(tmpfile, _cache_path(name, vi))
    # clean up (instances are appended from the cache afterwards)
    for o in objs:
        bpy.data.objects.remove(o, do_unlink=True)
    for x in acts:
        bpy.data.actions.remove(x)
    bpy.data.collections.remove(tmpc)
    print("assets: built %s v%d cache in %.1fs" % (name, vi, time.time() - t0))


def _xf_landmarks(a):
    """Landmarks are measured in the plot frame (median-x centred, scaled to plot_height); map them to
    the final frame (x shifted by x_shift, scaled to height)."""
    a = dict(a)
    ph_ = a.get("plot_height", a["height"])
    k = a["height"] / ph_
    xs = a.get("x_shift", 0.0)

    def f(p):
        return ((p[0] - xs) * k, p[1] * k, p[2] * k)
    if a.get("eyes"):
        a["eyes"] = f(a["eyes"])
        a["eye_x_shift"] = 0.0
    if a.get("rig"):
        R = dict(a["rig"])
        for key in ("spine", "neck", "head", "jaw", "tail"):
            if R.get(key):
                R[key] = [f(p) for p in R[key]]
        R["legs"] = {lk: [f(p) for p in pts] for lk, pts in R["legs"].items()}
        if R.get("stance"):
            R["stance"] = {lk: (v[0] * k, v[1] * k) for lk, v in R["stance"].items()}
        if R.get("mouth_z") is not None:
            R["mouth_z"] = R["mouth_z"] * k
        if R.get("jaw_halfwidth"):
            R["jaw_halfwidth"] = R["jaw_halfwidth"] * k
        a["rig"] = R
    return a


def _fix_animal_materials(me, a):
    """Opaque, non-metallic, fur-like roughness + sheen; optional tint & object 'tint' attribute."""
    for i, m in enumerate(me.materials):
        if m is None:
            continue
        m = m.copy()
        me.materials[i] = m
        m.name = "A_%s_%d" % (a["uid"][:6], i)
        try:
            m.surface_render_method = "DITHERED"
            m.blend_method = "OPAQUE"
        except Exception:
            pass
        N, L = m.node_tree.nodes, m.node_tree.links
        b = N.get("Principled BSDF")
        if not b:
            continue
        for sock in ("Metallic",):
            for l in list(b.inputs[sock].links):
                L.remove(l)
            b.inputs[sock].default_value = 0.0
        rl = b.inputs["Roughness"].links
        if rl:
            mr = N.new("ShaderNodeMapRange")
            mr.inputs["To Min"].default_value = a.get("rough_min", 0.55)
            mr.inputs["To Max"].default_value = 1.0
            L.new(rl[0].from_socket, mr.inputs["Value"])
            L.new(mr.outputs["Result"], b.inputs["Roughness"])
        else:
            b.inputs["Roughness"].default_value = max(0.6, b.inputs["Roughness"].default_value)
        for l in list(b.inputs["Alpha"].links):
            L.remove(l)
        b.inputs["Alpha"].default_value = 1.0
        b.inputs["Sheen Weight"].default_value = a.get("sheen", 0.35)
        b.inputs["Sheen Roughness"].default_value = 0.4
        b.inputs["Specular IOR Level"].default_value = 0.35
        # colour: optional hue/sat/value tweak + per-object tint attribute (obj['tint'] = (r, g, b) offsets)
        bl = b.inputs["Base Color"].links
        if bl:
            src = bl[0].from_socket
            if a.get("hsv"):
                hs = N.new("ShaderNodeHueSaturation")
                hs.inputs["Hue"].default_value, hs.inputs["Saturation"].default_value, hs.inputs["Value"].default_value = a["hsv"]
                L.new(src, hs.inputs["Color"])
                src = hs.outputs["Color"]
            at = N.new("ShaderNodeAttribute")
            at.attribute_type = "OBJECT"
            at.attribute_name = "tint"
            add = N.new("ShaderNodeVectorMath")
            add.operation = "ADD"
            add.inputs[1].default_value = (1, 1, 1)
            L.new(at.outputs["Vector"], add.inputs[0])
            mul = N.new("ShaderNodeVectorMath")
            mul.operation = "MULTIPLY"
            L.new(src, mul.inputs[0])
            L.new(add.outputs[0], mul.inputs[1])
            L.new(mul.outputs[0], b.inputs["Base Color"])
        if a.get("sss"):
            b.inputs["Subsurface Weight"].default_value = a["sss"]
            b.inputs["Subsurface Radius"].default_value = (1.0, 0.45, 0.25)
            b.inputs["Subsurface Scale"].default_value = 0.01


def _mirror(p):
    return (-p[0], p[1], p[2])


def _make_rig(name, vi, a, body, coll):
    """Build a quadruped armature from landmarks, skin the body with automatic weights (plus a clean
    jaw region), add eye spheres. Returns the armature object."""
    R = a["rig"]
    ad = bpy.data.armatures.new("%s%d_rig" % (name, vi))
    arm = bpy.data.objects.new("%s%d" % (name, vi), ad)
    coll.objects.link(arm)
    ad.display_type = "STICK"
    vl = bpy.context.view_layer
    with bpy.context.temp_override(active_object=arm, object=arm,
                                   selected_objects=[arm], selected_editable_objects=[arm]):
        vl.objects.active = arm
        bpy.ops.object.mode_set(mode="EDIT")
        eb = ad.edit_bones

        def bone(n, h, t, parent=None, deform=True, connect=False, roll_x=True):
            b = eb.new(n)
            b.head, b.tail = Vector(h), Vector(t)
            if roll_x:
                b.align_roll(Vector((0, 0, 1)) if abs((b.tail - b.head).normalized().z) < 0.9 else Vector((0, -1, 0)))
            if parent:
                b.parent = eb[parent]
                b.use_connect = connect
            b.use_deform = deform
            return b
        sp, nk, hd = R["spine"], R["neck"], R["head"]
        mid = Vector(sp[1])
        bone("root", (0, 0, 0), (0, 0.3, 0), deform=False)
        bone("body", mid, mid + Vector((0, 0.25, 0)), "root", deform=False)
        eb["body"].roll = 0
        bone("spine1", sp[0], sp[1], "body")
        bone("spine2", sp[1], sp[2], "spine1", connect=True)
        nmid = (Vector(nk[0]) + Vector(nk[1])) / 2
        bone("neck1", nk[0], nmid, "spine2")
        bone("neck2", nmid, nk[1], "neck1", connect=True)
        bone("head", hd[0], hd[1], "neck2")
        if R.get("jaw"):
            bone("jaw", R["jaw"][0], R["jaw"][1], "head")
        prev = "spine1"
        for i in range(len(R["tail"]) - 1):
            bone("tail%d" % (i + 1), R["tail"][i], R["tail"][i + 1], prev, connect=(i > 0))
            prev = "tail%d" % (i + 1)
        for leg in ("FL", "FR", "HL", "HR"):
            mir = leg[1] == "R"
            src = R["legs"].get(leg) or R["legs"][leg[0] + "L"]
            pts = [Vector(_mirror(p) if (mir and leg not in R["legs"]) else p) for p in src]
            x = sum(p.x for p in pts) / len(pts)
            for p in pts:
                p.x = x
            par = "spine2" if leg[0] == "F" else "spine1"
            bone(leg + "1", pts[0], pts[1], par)
            bone(leg + "2", pts[1], pts[2], leg + "1", connect=True)
            bone(leg + "3", pts[2], pts[3], leg + "2", connect=True)
            # IK target at the neutral standing foot position (fixes asymmetric sculpt poses)
            st = R.get("stance", {}).get(leg)
            if st is None:
                st = (pts[3].y, pts[3].z) if leg[0] + "L" == leg or leg in R["legs"] else (pts[3].y, pts[3].z)
            foot = Vector((x, st[0], st[1]))
            bone("IK_" + leg, foot, foot + Vector((0, 0.12 * a["height"], 0)), "root", deform=False, roll_x=False)
            eb["IK_" + leg].roll = 0
        bpy.ops.object.mode_set(mode="OBJECT")
    # fix leg rolls so that local X == world +X for planar IK (compute in object mode via edit again)
    with bpy.context.temp_override(active_object=arm, object=arm,
                                   selected_objects=[arm], selected_editable_objects=[arm]):
        bpy.ops.object.mode_set(mode="EDIT")
        for b in ad.edit_bones:
            if b.name[:2] in ("FL", "FR", "HL", "HR") or b.name.startswith(("spine", "neck", "head", "jaw", "tail")):
                d = (b.tail - b.head).normalized()
                # roll so the bone's X axis is world X (bones lie ~in the YZ plane)
                best, br = -2, 0
                for r in range(0, 360, 2):
                    b.roll = math.radians(r)
                    xa = b.x_axis
                    if xa.x > best:
                        best, br = xa.x, r
                b.roll = math.radians(br)
        bpy.ops.object.mode_set(mode="OBJECT")
    # IK constraints with planar locks
    for n in ("FL", "FR", "HL", "HR"):
        pb = arm.pose.bones[n + "3"]
        c = pb.constraints.new("IK")
        c.target = arm
        c.subtarget = "IK_" + n
        c.chain_count = 3
        c.use_stretch = False
        for k in (1, 2, 3):
            p = arm.pose.bones[n + str(k)]
            p.lock_ik_y = p.lock_ik_z = True
            p.ik_stretch = 0.0
    for pb in arm.pose.bones:
        pb.rotation_mode = "XYZ"
    # skin
    body.parent = arm
    with bpy.context.temp_override(active_object=arm, object=arm,
                                   selected_objects=[arm, body], selected_editable_objects=[arm, body]):
        for o in vl.objects:
            o.select_set(o in (arm, body))
        vl.objects.active = arm
        try:
            bpy.ops.object.parent_set(type="ARMATURE_AUTO")
        except Exception as e:
            print("assets: auto weights failed:", e)
    if not any(m.type == "ARMATURE" for m in body.modifiers):
        md = body.modifiers.new("Armature", "ARMATURE")
        md.object = arm
    _repair_weights(body, arm, a)
    cs = body.modifiers.new("CorrectiveSmooth", "CORRECTIVE_SMOOTH")
    cs.rest_source = "ORCO"
    cs.smooth_type = "LENGTH_WEIGHTED"
    cs.iterations = a.get("smooth_iter", 6)
    cs.factor = 0.5
    cs.use_only_smooth = False
    if a.get("eyes"):
        _add_eyes(arm, a, "head", coll)
    arm["ik_bones"] = ["IK_FL", "IK_FR", "IK_HL", "IK_HR"]
    return arm


def _repair_weights(body, arm, a):
    """Give unweighted vertices the nearest bone, rebuild a clean jaw region, normalise."""
    R = a["rig"]
    vg = body.vertex_groups
    me = body.data
    deform = [b for b in arm.data.bones if b.use_deform]
    segs = [(b.name, arm.matrix_world @ b.head_local, arm.matrix_world @ b.tail_local) for b in deform]

    def seg_dist(p, a_, b_):
        ab = b_ - a_
        t = max(0.0, min(1.0, (p - a_).dot(ab) / max(1e-9, ab.length_squared)))
        return (a_ + ab * t - p).length
    for n, _, _ in segs:
        if n not in vg:
            vg.new(name=n)
    jaw = R.get("jaw")
    jg = vg.get("jaw")
    if jaw and jg:
        pv, ct = Vector(jaw[0]), Vector(jaw[1])
        mouth_z = R.get("mouth_z")          # plane between upper and lower jaw at the snout
        for v in me.vertices:
            p = v.co
            for g in v.groups:
                if g.group == jg.index:
                    g.weight = 0.0
            # lower jaw region: forward of the pivot, below the mouth line (linear from pivot to snout)
            if p.y < pv.y + 0.02 * a["height"] and abs(p.x) < R.get("jaw_halfwidth", 0.12):
                t = (pv.y - p.y) / max(1e-6, pv.y - ct.y)
                zl = pv.z + (mouth_z - pv.z) * max(0.0, min(1.0, t)) if mouth_z is not None else pv.z
                if p.z < zl and p.z > ct.z - 0.25 * (pv.z - ct.z) - 0.03 * a["height"] and t > -0.15:
                    w = max(0.0, min(1.0, (t + 0.15) / 0.35))
                    jg.add([v.index], w, "REPLACE")
                    hg = vg.get("head")
                    if hg:
                        hg.add([v.index], 1.0 - w, "REPLACE")
                    for g in v.groups:
                        if g.group not in (jg.index, hg.index if hg else -1):
                            g.weight = 0.0
    for v in me.vertices:
        tot = sum(g.weight for g in v.groups)
        if tot < 1e-4:
            p = v.co
            n = min(segs, key=lambda s_: seg_dist(p, s_[1], s_[2]))[0]
            vg[n].add([v.index], 1.0, "REPLACE")
    _island_weights(body)


def _island_weights(body, frac=0.04):
    """Small disconnected parts (eyes, teeth, claws, tufts) copy the weights of the nearest vertex of the
    big islands so they ride along rigidly instead of flying off with a wrong bone."""
    import numpy as np
    from mathutils.kdtree import KDTree
    me = body.data
    n = len(me.vertices)
    parent = np.arange(n)

    def find(i):
        r = i
        while parent[r] != r:
            r = parent[r]
        while parent[i] != r:
            parent[i], i = r, parent[i]
        return r
    ev = np.empty(len(me.edges) * 2, np.int64)
    me.edges.foreach_get("vertices", ev)
    for a_, b_ in ev.reshape(-1, 2):
        ra, rb = find(a_), find(b_)
        if ra != rb:
            parent[ra] = rb
    roots = np.array([find(i) for i in range(n)])
    ids, counts = np.unique(roots, return_counts=True)
    big = set(ids[counts >= frac * n])
    if not big:
        return
    kd_idx = [i for i in range(n) if roots[i] in big]
    kd = KDTree(len(kd_idx))
    for j, i in enumerate(kd_idx):
        kd.insert(me.vertices[i].co, j)
    kd.balance()
    vg = body.vertex_groups
    for i in range(n):
        if roots[i] in big:
            continue
        v = me.vertices[i]
        _, j, _ = kd.find(v.co)
        src = me.vertices[kd_idx[j]]
        for g in list(v.groups):
            vg[g.group].remove([i])
        for g in src.groups:
            vg[g.group].add([i], g.weight, "REPLACE")


def _add_eyes(arm, a, bone, coll):
    """Small glossy eye spheres at the eye landmarks (parented to the head bone): give a wet glint and
    can glow (set_eye_glow) for eyeshine in the dark."""
    e = a["eyes"]
    r = a.get("eye_r", 0.012 * a["height"])
    m = bpy.data.materials.get("A_eye") or C.mat("A_eye", (0.02, 0.015, 0.01), rough=0.04, coat=1.0, spec=0.8)
    objs = []
    for p in (e, _mirror(e)):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=r)
        bmesh.ops.translate(bm, verts=bm.verts, vec=Vector(p))
        objs.append(bm)
    bm = objs[0]
    tmpme = bpy.data.meshes.new("t")
    objs[1].to_mesh(tmpme)
    objs[1].free()
    bm.from_mesh(tmpme)
    bpy.data.meshes.remove(tmpme)
    ob = _bm_to_obj("eyes", bm, coll)
    _assign(ob, m)
    if bone:
        ob.parent = arm
        ob.parent_type = "BONE"
        ob.parent_bone = bone
        pb = arm.data.bones[bone]
        ob.matrix_parent_inverse = (arm.matrix_world @ Matrix.Translation(pb.tail_local) @ pb.matrix_local.to_3x3().to_4x4()).inverted()
    else:
        ob.parent = arm
    return ob


# --------------------------------------------------------------------------------------------
# Procedural actions
# --------------------------------------------------------------------------------------------
def _gaits(a):
    """Action definitions for an animal variant (merged defaults + per-animal overrides)."""
    H = a["height"]
    kind = a.get("kind", "quadruped")
    base = {
        "idle": dict(type="idle", T=6.0),
        "walk": dict(type="gait", T=1.25, duty=0.64, stride=0.62 * H, lift=0.09 * H,
                     phase=dict(HL=0.0, FL=0.25, HR=0.5, FR=0.75), bob=0.012 * H, head_bob=4.0, tail=6.0),
        "run": dict(type="gait", T=0.52, duty=0.36, stride=0.95 * H, lift=0.16 * H,
                    phase=dict(HL=0.0, HR=0.1, FR=0.45, FL=0.56), bob=0.05 * H, pitch=7.0, flex=10.0,
                    head_bob=6.0, tail=10.0, gallop=True),
    }
    extra = a.get("actions", {})
    out = {}
    for k, v in base.items():
        out[k] = dict(v)
    for k, v in extra.items():
        d = dict(out.get(v.get("base", k), {}))
        d.update(v)
        out[k] = d
    for k in a.get("no_actions", []):
        out.pop(k, None)
    return out


def _make_actions(name, vi, a, arm):
    G = _gaits(a)
    fps = 24
    for an, g in G.items():
        act = bpy.data.actions.new("%s%d|%s" % (name, vi, an))
        act.use_fake_user = True
        ad = arm.animation_data or arm.animation_data_create()
        ad.action = act
        T = g["T"]
        N = max(2, int(round(T * fps)))
        for f in range(0, N + 1):
            t = f / N
            pose = _pose_at(a, g, t, T)
            for bn, ch in pose.items():
                pb = arm.pose.bones.get(bn)
                if pb is None:
                    continue
                if "rot" in ch:
                    pb.rotation_euler = [math.radians(x) for x in ch["rot"]]
                    pb.keyframe_insert("rotation_euler", frame=1 + f)
                if "loc" in ch:
                    pb.location = ch["loc"]
                    pb.keyframe_insert("location", frame=1 + f)
        # make cyclic (smooth loop) unless one-shot
        for fc in C._fcurves(act):
            if not g.get("once"):
                fc.modifiers.new("CYCLES")
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR" if g["type"] == "gait" else "BEZIER"
        act.frame_range = (1, 1 + N)
        try:
            act.use_frame_range = True
            act.use_cyclic = not g.get("once")
        except Exception:
            pass
        ad.action = None
        for pb in arm.pose.bones:
            pb.location = (0, 0, 0)
            pb.rotation_euler = (0, 0, 0)


def _smooth01(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def _pose_at(a, g, t, T):
    """Pose (bone -> {'rot': (deg x, y, z), 'loc': (x, y, z)}) for normalised cycle time t in [0, 1]."""
    H = a["height"]
    two = 2 * math.pi
    P = {}
    typ = g["type"]
    jaw_closed = a.get("jaw_closed", 0.0)        # jaw rotation (deg about X) that closes the sculpted mouth
    if typ == "gait":
        S, duty, lift = g["stride"], g["duty"], g["lift"]
        legs = {}
        for leg in ("FL", "FR", "HL", "HR"):
            ph_ = g["phase"].get(leg, 0.0)
            p = (t - ph_) % 1.0
            if p < duty:
                u = p / duty
                y = -S / 2 + S * u
                z = 0.0
            else:
                u = (p - duty) / (1 - duty)
                y = S / 2 - S * _smooth01(u)
                z = lift * math.sin(math.pi * min(1.0, u * 1.1)) ** 1.2
            if leg[0] == "F":
                y -= g.get("front_reach", 0.0) * S
            P["IK_" + leg] = {"loc": (0.0, y, z)}
            legs[leg] = (y, z)
        bob = g.get("bob", 0.0)
        crouch = g.get("crouch", 0.0) * H
        if g.get("gallop"):
            zb = bob * math.sin(two * t + 0.6) - crouch
            pitch = g.get("pitch", 0.0) * math.sin(two * t)
            flex = g.get("flex", 0.0) * math.sin(two * t + 1.2)
            P["body"] = {"loc": (0, 0, zb), "rot": (pitch, 0, 0)}
            P["spine1"] = {"rot": (flex * 0.6, 0, 0)}
            P["spine2"] = {"rot": (-flex, 0, 0)}
            hb = g.get("head_bob", 0) * math.sin(two * t + 2.2)
            P["neck1"] = {"rot": (g.get("neck", 0.0) - pitch * 0.6 + hb * 0.5, 0, 0)}
            P["head"] = {"rot": (g.get("head", 0.0) - pitch * 0.5 + hb * 0.5, 0, 0)}
        else:
            zb = bob * math.cos(2 * two * t) - crouch
            roll = g.get("roll", 1.5) * math.sin(two * t)
            yaw = g.get("yaw", 1.5) * math.sin(two * t + 0.5)
            P["body"] = {"loc": (0.0, 0.0, zb), "rot": (g.get("body_pitch", 0.0), roll, yaw)}
            P["spine2"] = {"rot": (0, 0, -yaw * 1.2)}
            hb = g.get("head_bob", 0.0) * math.cos(2 * two * t + 0.8)
            P["neck1"] = {"rot": (g.get("neck", 0.0) + hb, 0, yaw * 0.8)}
            P["neck2"] = {"rot": (g.get("neck2", 0.0), 0, 0)}
            P["head"] = {"rot": (g.get("head", 0.0) - hb * 0.6, 0, -yaw * 0.6)}
        tail_amp = g.get("tail", 5.0)
        for i in range(1, 6):
            P["tail%d" % i] = {"rot": (g.get("tail_lift", 0.0) / i + 2.0 * math.sin(two * t * (2 if not g.get("gallop") else 1) + i * 0.7),
                                       0, tail_amp * math.sin(two * t + i * 0.8))}
        if "jaw" in a["rig"] or a["rig"].get("jaw"):
            P["jaw"] = {"rot": (jaw_closed + g.get("jaw_open", 0.0) * (0.5 + 0.5 * math.sin(two * t * 2)), 0, 0)}
    elif typ == "idle":
        br = math.sin(two * t * 2)                        # breathing (x2 per cycle)
        look = math.sin(two * t) * g.get("look", 12.0)
        P["body"] = {"loc": (0, 0, 0.003 * H * br - g.get("crouch", 0.0) * H), "rot": (0, 0, 0)}
        P["spine2"] = {"rot": (0.8 * br, 0, 0)}
        P["neck1"] = {"rot": (g.get("neck", 0.0) + 1.5 * math.sin(two * t * 3 + 1), 0, look * 0.5)}
        P["head"] = {"rot": (g.get("head", 0.0) + 2.0 * math.sin(two * t + 2.0), look * 0.15, look * 0.5)}
        for i in range(1, 6):
            P["tail%d" % i] = {"rot": (g.get("tail_lift", 0.0) / i + 1.5 * math.sin(two * t * 2 + i * 0.6), 0,
                                       g.get("tail", 6.0) * math.sin(two * t * 3 + i * 0.9))}
        if a["rig"].get("jaw"):
            chew = g.get("chew", 0.0) * max(0.0, math.sin(two * t * 6))
            pant = g.get("pant", 0.0) * (0.5 + 0.5 * math.sin(two * t * 12))
            P["jaw"] = {"rot": (jaw_closed + chew + pant, 0, 0)}
        for leg in ("FL", "FR", "HL", "HR"):
            P["IK_" + leg] = {"loc": (0, 0, 0)}
    elif typ == "graze":
        br = math.sin(two * t * 2)
        P["body"] = {"loc": (0, 0, 0.002 * H * br), "rot": (g.get("body_pitch", 3.0), 0, 0)}
        sway = math.sin(two * t) * 6
        P["neck1"] = {"rot": (g.get("neck", 35.0) + 2 * math.sin(two * t * 4), 0, sway)}
        P["neck2"] = {"rot": (g.get("neck2", 15.0), 0, sway * 0.5)}
        P["head"] = {"rot": (g.get("head", 10.0) + 3 * math.sin(two * t * 8), 0, 0)}
        if a["rig"].get("jaw"):
            P["jaw"] = {"rot": (jaw_closed + 4 * max(0, math.sin(two * t * 8)), 0, 0)}
        for i in range(1, 6):
            P["tail%d" % i] = {"rot": (2 * math.sin(two * t * 2 + i * 0.6), 0, 8 * math.sin(two * t * 3 + i * 0.9))}
        for leg in ("FL", "FR", "HL", "HR"):
            P["IK_" + leg] = {"loc": (0, 0, 0)}
    elif typ == "roar":
        # 0..0.2 draw back + inhale, 0.2..0.35 thrust + open, 0.35..0.8 hold (tremor), 0.8..1 close/relax
        def env(t0, t1, t2, t3):
            if t < t0 or t > t3:
                return 0.0
            if t < t1:
                return _smooth01((t - t0) / (t1 - t0))
            if t < t2:
                return 1.0
            return 1.0 - _smooth01((t - t2) / (t3 - t2))
        draw = env(0.0, 0.18, 0.24, 0.36)
        open_ = env(0.2, 0.34, 0.78, 0.95)
        trem = math.sin(two * t * 22) * 1.2 * open_
        P["body"] = {"loc": (0, -0.03 * H * open_ + 0.02 * H * draw, -0.01 * H * open_), "rot": (2 * draw - 3 * open_, 0, 0)}
        P["spine2"] = {"rot": (-3 * draw + 2 * open_, 0, 0)}
        P["neck1"] = {"rot": (-12 * draw + g.get("neck", 6.0) * open_, 0, 0)}
        P["neck2"] = {"rot": (-6 * draw + 4 * open_, 0, 0)}
        P["head"] = {"rot": (-10 * draw + g.get("head", -14.0) * open_ + trem, 0, 0)}
        if a["rig"].get("jaw"):
            P["jaw"] = {"rot": (jaw_closed * (1 - open_) + g.get("jaw_extra", 4.0) * open_ + trem * 0.5, 0, 0)}
        for i in range(1, 6):
            P["tail%d" % i] = {"rot": (3 * open_ / i, 0, 10 * math.sin(two * t * 2 + i * 0.8))}
        for leg in ("FL", "FR", "HL", "HR"):
            P["IK_" + leg] = {"loc": (0, 0, 0)}
    elif typ == "toss":     # bull head toss / hook with the horns
        k1 = math.sin(math.pi * min(1, t / 0.45)) if t < 0.45 else 0.0
        k2 = math.sin(math.pi * max(0, (t - 0.4) / 0.4)) if 0.4 < t < 0.8 else 0.0
        P["body"] = {"loc": (0, -0.02 * H * k1, -0.01 * H * k1), "rot": (2 * k1, 2 * k2, 0)}
        P["neck1"] = {"rot": (14 * k1 - 22 * k2, 0, 12 * k2)}
        P["neck2"] = {"rot": (6 * k1 - 8 * k2, 0, 6 * k2)}
        P["head"] = {"rot": (10 * k1 - 14 * k2, 18 * k2, 10 * k2)}
        for i in range(1, 6):
            P["tail%d" % i] = {"rot": (5 * k2, 0, 12 * math.sin(two * t * 2 + i * 0.8))}
        for leg in ("FL", "FR", "HL", "HR"):
            P["IK_" + leg] = {"loc": (0, 0, 0)}
    elif typ == "paw":      # scrape the ground with the front right hoof/paw
        sc_ = math.sin(two * t * 2)
        lift = max(0.0, math.sin(two * t * 2 + 1.2))
        P["IK_FR"] = {"loc": (0, 0.12 * H * sc_, 0.05 * H * lift)}
        for leg in ("FL", "HL", "HR"):
            P["IK_" + leg] = {"loc": (0, 0, 0)}
        P["body"] = {"loc": (0, 0, -0.01 * H), "rot": (3, -2, 0)}
        P["neck1"] = {"rot": (18 + 3 * sc_, 0, 0)}
        P["head"] = {"rot": (10, 0, 0)}
        for i in range(1, 6):
            P["tail%d" % i] = {"rot": (2, 0, 10 * math.sin(two * t + i * 0.8))}
    return P


# --------------------------------------------------------------------------------------------
# Animal definitions (landmarks measured on the normalised meshes; see docs/assets.md)
# --------------------------------------------------------------------------------------------
_def_animal(
    "lion", uid="48fc306182ea411a92eb10ceb32a7ca9", title="Lion", author="hendrikReyneke (Sketchfab)",
    license="CC-BY-4.0", rot=0.0, height=1.38, sheen=0.45, rough_min=0.6,
    eyes=(0.095, -1.0, 1.265), eye_r=0.017, jaw_closed=-30.0,
    rig=dict(
        spine=[(0, 0.68, 0.98), (0, 0.05, 0.86), (0, -0.52, 0.98)],
        neck=[(0, -0.52, 1.0), (0, -0.86, 1.15)],
        head=[(0, -0.86, 1.15), (0, -1.22, 1.2)],
        jaw=[(0, -0.93, 1.12), (0, -1.16, 0.93)], mouth_z=1.07, jaw_halfwidth=0.14,
        tail=[(0, 0.86, 0.98), (-0.05, 0.95, 0.72), (-0.15, 1.0, 0.45), (-0.3, 1.08, 0.22), (-0.45, 1.2, 0.07)],
        legs=dict(FL=[(0.19, -0.58, 0.82), (0.19, -0.47, 0.5), (0.19, -0.6, 0.16), (0.19, -0.72, 0.03)],
                  FR=[(-0.19, -0.58, 0.82), (-0.19, -0.47, 0.5), (-0.19, -0.62, 0.16), (-0.19, -0.74, 0.03)],
                  HL=[(0.2, 0.68, 0.8), (0.2, 0.58, 0.5), (0.2, 0.86, 0.32), (0.2, 0.74, 0.03)],
                  HR=[(-0.2, 0.68, 0.8), (-0.2, 0.52, 0.5), (-0.2, 0.8, 0.3), (-0.2, 0.6, 0.03)]),
        stance=dict(FL=(-0.72, 0.03), FR=(-0.72, 0.03), HL=(0.68, 0.03), HR=(0.68, 0.03))),
    actions=dict(
        idle=dict(type="idle", T=6.0, look=10.0, tail=8.0),
        walk=dict(T=1.35, duty=0.62, stride=0.9, lift=0.13, bob=0.015, head_bob=3.0, tail=7.0, neck=4.0),
        stalk=dict(base="walk", T=2.1, duty=0.7, stride=0.62, lift=0.1, crouch=0.09, neck=14.0, head=-12.0,
                   bob=0.008, head_bob=1.0, tail=4.0, tail_lift=-6.0),
        run=dict(T=0.46, duty=0.32, stride=1.0, lift=0.2, bob=0.05, pitch=6.0, flex=9.0, head_bob=5.0, tail=8.0),
        roar=dict(type="roar", T=3.2, neck=6.0, head=-16.0, jaw_extra=5.0),
    ))
_def_animal(
    "lion", uid="67574bbf86f64b83a16399798ceb3b23", title="Lioness", author="hendrikReyneke (Sketchfab)",
    license="CC-BY-4.0", rot=0.0, height=1.15, static=True)
_def_animal(
    "bull", uid="14d376df3070448ba82e423c2392057b", title="Buffalo", author="hendrikReyneke (Sketchfab)",
    license="CC-BY-4.0", rot=0.0, height=1.6, sheen=0.3, rough_min=0.55,
    eyes=(0.17, -1.19, 0.64), eye_r=0.018,
    rig=dict(
        spine=[(0, 1.0, 1.3), (0, 0.2, 1.3), (0, -0.45, 1.3)],
        neck=[(0, -0.45, 1.25), (0, -0.98, 0.98)],
        head=[(0, -0.98, 0.98), (0, -0.98, 0.45)],
        tail=[(0, 1.15, 1.45), (0, 1.28, 1.3), (0, 1.3, 1.05), (0, 1.35, 0.8), (0, 1.45, 0.6)],
        legs=dict(FL=[(0.25, -0.5, 1.0), (0.25, -0.42, 0.68), (0.25, -0.43, 0.32), (0.25, -0.5, 0.02)],
                  FR=[(-0.25, -0.5, 1.0), (-0.25, -0.46, 0.68), (-0.25, -0.75, 0.35), (-0.25, -0.83, 0.05)],
                  HL=[(0.27, 0.95, 1.15), (0.27, 0.82, 0.72), (0.27, 1.02, 0.42), (0.27, 0.92, 0.02)],
                  HR=[(-0.27, 0.95, 1.15), (-0.27, 0.82, 0.72), (-0.27, 1.04, 0.42), (-0.27, 0.95, 0.02)]),
        stance=dict(FL=(-0.52, 0.02), FR=(-0.52, 0.02), HL=(0.93, 0.02), HR=(0.93, 0.02))),
    actions=dict(
        idle=dict(type="idle", T=7.0, look=8.0, tail=12.0, neck=-10.0),
        walk=dict(T=1.45, duty=0.64, stride=1.0, lift=0.14, bob=0.015, head_bob=3.0, tail=6.0, neck=-12.0),
        run=dict(T=0.6, duty=0.36, stride=1.25, lift=0.24, bob=0.06, pitch=5.0, flex=6.0, head_bob=4.0, tail=10.0,
                 neck=-4.0),
        toss=dict(type="toss", T=2.2),
        paw=dict(type="paw", T=1.6),
    ))
_def_animal(
    "bull", uid="f01175538f7b4ffe8e2648d772e94c5c", title="Wildebeest", author="hendrikReyneke (Sketchfab)",
    license="CC-BY-4.0", rot=0.0, height=1.5, static=True, hsv=(0.5, 0.5, 0.55))
_def_animal(
    "dog", uid="1de9441cb0744c0d8459ce957b8d0a57", title="Italian White Wolf", author="sdpm (Sketchfab)",
    license="CC-BY-4.0", rot=0.0, height=0.85, sheen=0.5, rough_min=0.6, hsv=(0.5, 1.0, 0.85),
    eyes=(0.042, -0.6, 0.715), eye_r=0.009,
    rig=dict(
        spine=[(0, 0.4, 0.62), (0, 0.0, 0.6), (0, -0.3, 0.65)],
        neck=[(0, -0.3, 0.65), (0, -0.48, 0.75)],
        head=[(0, -0.48, 0.75), (0, -0.69, 0.64)],
        jaw=[(0, -0.52, 0.66), (0, -0.66, 0.6)], mouth_z=0.62, jaw_halfwidth=0.06,
        tail=[(0, 0.48, 0.6), (0, 0.55, 0.5), (0, 0.62, 0.38), (0, 0.67, 0.27), (0, 0.7, 0.2)],
        legs=dict(FL=[(0.09, -0.25, 0.55), (0.09, -0.2, 0.36), (0.09, -0.22, 0.1), (0.09, -0.29, 0.02)],
                  HL=[(0.095, 0.33, 0.55), (0.095, 0.24, 0.36), (0.095, 0.37, 0.19), (0.095, 0.3, 0.02)])),
    actions=dict(
        idle=dict(type="idle", T=5.0, look=14.0, tail=6.0, pant=6.0),
        walk=dict(T=0.9, duty=0.62, stride=0.45, lift=0.08, bob=0.01, head_bob=3.0, tail=8.0),
        prowl=dict(base="walk", T=1.5, duty=0.7, stride=0.36, lift=0.07, crouch=0.07, neck=16.0, head=-12.0,
                   bob=0.006, head_bob=1.5, tail=4.0, tail_lift=-12.0),
        trot=dict(base="walk", T=0.56, duty=0.45, stride=0.5, lift=0.09, bob=0.012,
                  phase=dict(HL=0.0, FR=0.0, HR=0.5, FL=0.5), head_bob=2.0, tail=6.0),
        run=dict(T=0.38, duty=0.3, stride=0.6, lift=0.13, bob=0.035, pitch=6.0, flex=12.0, head_bob=5.0, tail=8.0),
        snarl=dict(type="roar", T=2.6, neck=10.0, head=-6.0, jaw_extra=22.0),
    ))
_def_animal(
    "ox", uid="dc8185e4e21747fb8b394e40d3ec125a", title="Cow", author="hendrikReyneke (Sketchfab)",
    license="CC-BY-4.0", rot=0.0, height=1.45, plot_height=1.55, sheen=0.25, rough_min=0.6,
    hsv=(0.5, 0.72, 0.62), eyes=(0.12, -1.3, 1.29), eye_r=0.017,
    rig=dict(
        spine=[(0, 0.75, 1.32), (0, 0.1, 1.3), (0, -0.6, 1.35)],
        neck=[(0, -0.6, 1.3), (0, -1.25, 1.35)],
        head=[(0, -1.25, 1.35), (0, -1.52, 1.05)],
        jaw=[(0, -1.28, 1.15), (0, -1.45, 0.97)], mouth_z=1.02, jaw_halfwidth=0.1,
        tail=[(0, 0.82, 1.38), (0, 1.0, 1.25), (0, 1.2, 1.05), (0, 1.45, 0.88), (0, 1.7, 0.75)],
        legs=dict(FL=[(0.144, -0.45, 1.05), (0.144, -0.4, 0.68), (0.144, -0.43, 0.3), (0.144, -0.55, 0.03)],
                  HL=[(0.3, 0.75, 1.15), (0.3, 0.68, 0.72), (0.33, 0.82, 0.42), (0.354, 0.67, 0.03)])),
    actions=dict(
        idle=dict(type="idle", T=8.0, look=8.0, tail=8.0, tail_lift=-42.0, chew=5.0),
        walk=dict(T=1.5, duty=0.65, stride=0.9, lift=0.12, bob=0.012, head_bob=3.0, tail=5.0, tail_lift=-42.0),
        graze=dict(type="graze", T=6.0, neck=38.0, neck2=12.0, head=8.0),
    ), no_actions=["run"])
_def_animal(
    "donkey", uid="54b3933b79a84b608c6e498c072061a9", title="Wild Ass", author="hendrikReyneke (Sketchfab)",
    license="CC-BY-4.0", rot=0.0, height=1.4, plot_height=1.5, x_shift=0.06, sheen=0.35, rough_min=0.6,
    hsv=(0.505, 0.9, 0.62), eyes=(0.16, -0.84, 1.2), eye_r=0.016,
    rig=dict(
        spine=[(0.06, 0.8, 1.2), (0.06, 0.2, 1.15), (0.06, -0.35, 1.25)],
        neck=[(0.06, -0.35, 1.2), (0.06, -0.82, 1.35)],
        head=[(0.06, -0.82, 1.35), (0.06, -0.9, 0.82)],
        tail=[(0.06, 0.95, 1.2), (0.06, 1.02, 1.0), (0.06, 1.05, 0.85), (0.06, 1.08, 0.7)],
        legs=dict(FL=[(0.25, -0.25, 1.0), (0.25, -0.15, 0.72), (0.25, -0.22, 0.3), (0.25, -0.36, 0.03)],
                  FR=[(-0.13, -0.2, 1.0), (-0.13, -0.1, 0.72), (-0.13, -0.12, 0.3), (-0.13, -0.16, 0.03)],
                  HL=[(0.25, 0.85, 1.05), (0.25, 0.75, 0.68), (0.25, 0.98, 0.45), (0.25, 0.8, 0.03)],
                  HR=[(-0.13, 0.85, 1.05), (-0.13, 0.72, 0.68), (-0.13, 0.88, 0.45), (-0.13, 0.63, 0.03)]),
        stance=dict(FL=(-0.27, 0.03), FR=(-0.27, 0.03), HL=(0.72, 0.03), HR=(0.72, 0.03))),
    actions=dict(
        idle=dict(type="idle", T=7.0, look=10.0, tail=10.0, neck=-6.0),
        walk=dict(T=1.25, duty=0.64, stride=0.75, lift=0.1, bob=0.012, head_bob=4.0, tail=5.0, neck=-6.0),
        graze=dict(type="graze", T=6.0, neck=30.0, neck2=8.0, head=0.0),
    ), no_actions=["run"])
_def_animal(
    "sheep", uid="67abff7459f34afca11e3effab62c761", title="Sheep", author="hendrikReyneke (Sketchfab)",
    license="CC-BY-4.0", rot=0.0, height=0.8, plot_height=0.85, sheen=0.6, rough_min=0.7,
    eyes=(0.05, -0.52, 0.76), eye_r=0.008,
    rig=dict(
        spine=[(0, 0.45, 0.68), (0, 0.05, 0.65), (0, -0.25, 0.68)],
        neck=[(0, -0.25, 0.66), (0, -0.45, 0.78)],
        head=[(0, -0.45, 0.78), (0, -0.62, 0.66)],
        jaw=[(0, -0.47, 0.66), (0, -0.6, 0.6)], mouth_z=0.64, jaw_halfwidth=0.05,
        tail=[(0, 0.52, 0.62), (0, 0.58, 0.58), (0, 0.65, 0.53), (0, 0.7, 0.51)],
        legs=dict(FL=[(0.086, -0.15, 0.48), (0.086, -0.1, 0.3), (0.086, -0.13, 0.1), (0.086, -0.19, 0.02)],
                  HL=[(0.093, 0.4, 0.5), (0.093, 0.33, 0.32), (0.093, 0.45, 0.17), (0.093, 0.39, 0.02)])),
    actions=dict(
        idle=dict(type="idle", T=6.0, look=12.0, tail=10.0, chew=4.0),
        walk=dict(T=0.95, duty=0.62, stride=0.4, lift=0.06, bob=0.008, head_bob=3.0, tail=6.0),
        graze=dict(type="graze", T=5.0, neck=34.0, neck2=10.0, head=10.0),
    ), no_actions=["run"])
_def_animal(
    "dove", uid="cc36e7c5445a4270b301f7ef938e671a", title="Dove Roman white (Columba livia)",
    author="darwinmuseum.ru (State Darwin Museum)", license="CC0-1.0", rot=0.0, height=0.25, static=True,
    crop_z=0.1)
_def_animal(
    "dove", uid="8cdbd8890ed84c228191cbe6241b420d", title="Pigeon", author="hendrikReyneke (Sketchfab)",
    license="CC-BY-4.0", rot=0.0, height=0.3, static=True)
