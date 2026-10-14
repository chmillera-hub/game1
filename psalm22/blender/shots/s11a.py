"""s11a - Potsherd: "My mouth is dried up like a potsherd, and my tongue sticks to the roof of my mouth;"

Macro, harsh white noon sun. A body sherd of a terracotta cooking pot (modelled here: curved 7-8 mm wall,
fresh break faces with a grey under-fired core) lies hollow side up on parched, polygonally cracked mud.
Behind it the dead branches of an acacia-like thorn bush stand against the bleached, shimmering sky,
a broken-off thorn twig lies on the mud. While the first line is spoken cracks creep across the clay;
on the second line the mud itself splits: crack grooves run out from under the sherd and open wide.
Heat haze ripples the mid-ground, the thorns and the horizon (Blender compositor displacement, depth-masked).
Low camera (~6 cm), 50 mm, f/7.1 (~2 cm depth of field at 0.35 m), slow push-in; focus stays on the sherd.
"""
import math
import random
import bpy
import bmesh
import numpy as np
from mathutils import Vector, Matrix, Quaternion, geometry as mgeo
from lib import core as C
from lib import fx as FX

SEED = 11
CELL = 0.085                      # mud plate size (m)
SHARD_AT = Vector((0.0, 0.0, 0.0))
GROUND_TEX = "dry_ground_01"      # pale, finely cracked mud scan (Poly Haven CC0)
GROUND_TINT = (0.9, 0.77, 0.6)
SHERD_TIP, SHERD_YAW = 14.0, 18.0  # deg: outer face tipped toward camera, then turned
BUSH_AT = (-0.16, 0.26, 0.0)


# =============================================================================================
# hero sherd
# =============================================================================================
# outer profile of a storage-jar shoulder -> neck -> everted lip, (r, z) metres, bottom to top
_PROFILE = [(0.095, 0.030), (0.106, 0.050), (0.113, 0.070), (0.116, 0.090), (0.114, 0.110), (0.108, 0.130),
            (0.098, 0.150), (0.085, 0.165)]


def _profile_fn():
    pts = [Vector((r, z)) for r, z in _PROFILE]
    s = [0.0]
    for a, b in zip(pts, pts[1:]):
        s.append(s[-1] + (b - a).length)

    def at(si):
        si = min(max(si, 0.0), s[-1])
        for i in range(len(s) - 1):
            if si <= s[i + 1] or i == len(s) - 2:
                t = (si - s[i]) / max(1e-9, s[i + 1] - s[i])
                p = pts[i].lerp(pts[i + 1], t)
                d = (pts[i + 1] - pts[i]).normalized()
                n = Vector((d.y, -d.x))             # outward normal in (r, z)
                return p, n
    return at, s[-1]


def _point_in_poly(x, y, poly):
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi:
            inside = not inside
        j = i
    return inside


def build_sherd(name="Sherd", seed=SEED, coll=None):
    """Body sherd: closed solid (outer wall, inner wall, fresh break faces). Materials:
    0 outer slip, 1 break, 2 inner wall. Returns (object with origin at its centroid, crack origin)."""
    rnd = random.Random(seed)
    prof, smax = _profile_fn()
    # ---- 2D outline in (u = circumferential arc length, s = profile arc length)
    sm = smax * 0.5
    ctrl = [(-0.050, sm + 0.006), (-0.044, sm - 0.024), (-0.020, sm - 0.042), (0.010, sm - 0.036),
            (0.034, sm - 0.044), (0.052, sm - 0.010), (0.046, sm + 0.020), (0.030, sm + 0.040),
            (0.006, sm + 0.034), (-0.018, sm + 0.044), (-0.040, sm + 0.030)]
    ctrl = ctrl + [ctrl[0]]
    outline = []
    for (x0, y0), (x1, y1) in zip(ctrl, ctrl[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        ph = rnd.random() * 6.28
        k = max(2, int(L / 0.003))
        for j in range(k):
            t = j / k
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t
            if j > 0:
                nx, ny = -(y1 - y0) / L, (x1 - x0) / L
                off = rnd.uniform(-1, 1) * 0.0005 + 0.0009 * math.sin(t * 5.0 + ph)
                x += nx * off
                y += ny * off
            outline.append((x, y, "brk"))
    poly = [(x, y) for x, y, _ in outline]
    nb_ = len(poly)
    # interior points: jittered grid
    pts = list(poly)
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    step = 0.0032
    y = min(ys) + step * 0.5
    while y < max(ys):
        x = min(xs) + step * 0.5
        while x < max(xs):
            jx, jy = x + rnd.uniform(-0.3, 0.3) * step, y + rnd.uniform(-0.3, 0.3) * step
            if _point_in_poly(jx, jy, poly):
                # keep away from the outline
                dmin = min((jx - px) ** 2 + (jy - py) ** 2 for px, py in poly)
                if dmin > (step * 0.55) ** 2:
                    pts.append((jx, jy))
            x += step
        y += step
    edges = [(i, (i + 1) % nb_) for i in range(nb_)]
    res = mgeo.delaunay_2d_cdt([Vector(p) for p in pts], edges, [], 1, 1e-7)
    vco, _, faces2d = res[0], res[1], res[2]
    orig_index = res[3]                    # output vert -> input verts

    def thick(si):
        # 7-8 mm wall
        return 0.0072 + 0.0008 * math.sin(si * 40.0)

    def to3d(u, si, inner=False):
        p, n = prof(si)
        r, z = p.x, p.y
        if inner:
            tk = thick(si)
            r -= n.x * tk
            z -= n.y * tk
        th = u / max(0.02, p.x)
        return Vector((r * math.cos(th), r * math.sin(th), z))

    bm = bmesh.new()
    lay_s = bm.verts.layers.float.new("pv")
    lay_t = bm.verts.layers.float.new("thk")
    outer = []
    inner = []
    for co in vco:
        vo = bm.verts.new(to3d(co.x, co.y))
        vi = bm.verts.new(to3d(co.x, co.y, True))
        vo[lay_s] = co.y / smax
        vi[lay_s] = co.y / smax
        vo[lay_t] = 0.0
        vi[lay_t] = 1.0
        outer.append(vo)
        inner.append(vi)
    for f in faces2d:
        try:
            fo = bm.faces.new([outer[i] for i in f])
            fo.material_index = 0
        except ValueError:
            continue
        try:
            fi = bm.faces.new([inner[i] for i in reversed(f)])
            fi.material_index = 2
        except ValueError:
            pass
    bm.normal_update()
    # map input outline index -> output vertex
    out_of = {}
    for oi, srcs in enumerate(orig_index):
        for s_ in srcs:
            out_of[s_] = oi
    side = []
    for i in range(nb_):
        j = (i + 1) % nb_
        a_, b_ = out_of.get(i), out_of.get(j)
        if a_ is None or b_ is None or a_ == b_:
            continue
        try:
            f = bm.faces.new((outer[b_], outer[a_], inner[a_], inner[b_]))
        except ValueError:
            continue
        lip = outline[i][2] == "lip" and outline[j][2] == "lip"
        f.material_index = 0 if lip else 1
        f.smooth = True
        side.append(f)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in bm.faces:
        f.smooth = True
    for f in side:
        for e in f.edges:
            if any(lf.material_index != f.material_index for lf in e.link_faces):
                e.smooth = False
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = C.link(bpy.data.objects.new(name, me), coll)
    # centre the origin
    cen = sum((v.co for v in me.vertices), Vector()) / len(me.vertices)
    me.transform(Matrix.Translation(-cen))
    # crack origin: a point on the lower break edge (object space)
    ox, oy = ctrl[3]
    origin = to3d(ox, oy) - cen
    return o, origin


def sherd_material(name, kind, craze=False, crack_origin=(0, 0, 0)):
    """Fired clay, sun-bleached and dusty. kind: 'slip' outer, 'break' fresh fracture, 'inner'.
    craze: adds a Value node 'craze' (reveal radius in metres from crack_origin, object space) that
    drives a creeping network of hairline cracks."""
    m, nb, out = FX._new_mat(name)
    oc = nb.n("ShaderNodeTexCoord").outputs["Object"]
    n1 = nb.out(nb.noise(nb.v("SCALE", oc, scale=18.0), scale=1.0, detail=5.0, rough=0.6), "Fac")
    n2 = nb.out(nb.noise(nb.v("SCALE", oc, scale=140.0), scale=1.0, detail=3.0), "Fac")
    if kind == "slip":
        c0, c1 = (0.26, 0.12, 0.055), (0.36, 0.185, 0.09)
    elif kind == "inner":
        c0, c1 = (0.25, 0.125, 0.06), (0.34, 0.18, 0.09)
    else:
        c0, c1 = (0.40, 0.21, 0.12), (0.48, 0.28, 0.16)
    col = nb.mixc(nb.smooth(n1, 0.25, 0.75), c0, c1)
    mott = nb.out(nb.noise(nb.v("SCALE", oc, scale=55.0), scale=1.0, detail=4.0, rough=0.65), "Fac")
    col = nb.mixc(nb.mul(nb.smooth(mott, 0.5, 0.75), 0.45), col, nb.v("SCALE", col, scale=0.62))
    # grey fire-clouding on the outside
    if kind == "slip":
        cloud = nb.smooth(nb.out(nb.noise(nb.v("SCALE", oc, scale=7.0), scale=1.0, detail=3.0), "Fac"), 0.55, 0.72)
        col = nb.mixc(nb.mul(cloud, 0.55), col, (0.30, 0.25, 0.22))
    col = nb.mixc(nb.mul(nb.smooth(n2, 0.45, 0.8), 0.35), col, nb.v("SCALE", col, scale=0.72))
    # white temper grit specks + patchy lime encrustation (sherds that lay long in dry soil)
    spk = nb.out(nb.n("ShaderNodeTexVoronoi", {"Vector": nb.v("SCALE", oc, scale=420.0), "Randomness": 1.0}, feature="F1"), "Distance")
    col = nb.mixc(nb.mul(nb.sub(1.0, nb.smooth(spk, 0.05, 0.14)), 0.5), col, (0.55, 0.52, 0.46))
    if kind != "break":
        lime = nb.smooth(nb.out(nb.noise(nb.v("SCALE", oc, scale=26.0), scale=1.0, detail=6.0, rough=0.7), "Fac"), 0.58, 0.66)
        col = nb.mixc(nb.mul(lime, 0.28), col, (0.52, 0.47, 0.4))
    # pale dust settled on up-facing surfaces (world normal z)
    nz = nb.out(nb.sep(nb.out(nb.n("ShaderNodeNewGeometry"), "Normal")), "Z")
    dust = nb.mul(nb.smooth(nz, 0.4, 0.95), nb.madd(nb.smooth(n1, 0.3, 0.8), 0.25, 0.05))
    col = nb.mixc(dust, col, (0.5, 0.39, 0.27))
    rough = nb.madd(n2, 0.06, 0.92)
    height = nb.mul(n2, 0.4)
    if kind != "break":
        # throwing rings along the profile (attribute pv = profile parameter)
        pv = nb.out(nb.sattr("pv"), "Fac")
        ring = nb.m("SINE", nb.add(nb.mul(pv, 120.0), nb.mul(n1, 4.0)))
        height = nb.add(height, nb.mul(ring, 0.16 if kind == "inner" else 0.06))
        if kind == "inner":
            # fine soil caught in the hollow of the sherd + darker water/soil stains
            stain = nb.smooth(nb.out(nb.noise(nb.v("SCALE", oc, scale=9.0), scale=1.0, detail=5.0, rough=0.6), "Fac"), 0.45, 0.7)
            col = nb.mixc(nb.mul(stain, 0.7), col, nb.v("MULTIPLY", col, (0.55, 0.5, 0.47)))
    else:
        grit = nb.out(nb.noise(nb.v("SCALE", oc, scale=700.0), scale=1.0, detail=2.0, rough=0.7), "Fac")
        height = nb.add(height, nb.mul(grit, 0.5))
        # grey 'sandwich' core of under-fired clay between the oxidised outer layers (ragged edges)
        thk = nb.out(nb.sattr("thk"), "Fac")
        n3 = nb.out(nb.noise(nb.v("SCALE", oc, scale=260.0), scale=1.0, detail=3.0), "Fac")
        cw = nb.add(0.1, nb.add(nb.mul(nb.sub(n1, 0.5), 0.16), nb.mul(nb.sub(n3, 0.5), 0.14)))
        core = nb.sub(1.0, nb.smooth(nb.m("ABSOLUTE", nb.sub(thk, nb.add(0.55, nb.mul(nb.sub(n3, 0.5), 0.1)))), cw, nb.add(cw, 0.06)))
        col = nb.mixc(nb.mul(core, 0.5), col, (0.22, 0.16, 0.12))
    crack = None
    if craze:
        cv = nb.n("ShaderNodeValue")
        cv.name = cv.label = "craze"
        crack_val = cv.outputs[0]
        # craze network (object space), revealed by a front creeping from crack_origin
        q = nb.v("ADD", nb.v("SCALE", oc, scale=17.0),
                 nb.v("SCALE", nb.v("SUBTRACT", nb.out(nb.noise(nb.v("SCALE", oc, scale=14.0), scale=1.0, detail=5.0, rough=0.55), "Color"),
                                    (0.5, 0.5, 0.5)), scale=0.38))
        vor = nb.n("ShaderNodeTexVoronoi", {"Vector": q, "Scale": 1.0, "Randomness": 1.0}, feature="DISTANCE_TO_EDGE")
        de = nb.out(vor, "Distance")
        dist = nb.v("DISTANCE", oc, crack_origin)
        front = nb.sub(nb.add(crack_val, nb.mul(nb.sub(n1, 0.5), 0.03)), dist)
        reveal = nb.smooth(front, 0.0, 0.03)
        width = nb.mul(reveal, 0.014)
        crack = nb.mul(nb.sub(1.0, nb.smooth(de, 0.0, nb.add(width, 0.0001))), nb.smooth(reveal, 0.0, 0.1))
        col = nb.mixc(nb.mul(crack, 0.72), col, (0.07, 0.04, 0.025))
        height = nb.sub(height, nb.mul(crack, 0.9))
    bump = nb.n("ShaderNodeBump", {"Height": height, "Distance": 0.0006, "Strength": 0.6})
    b = nb.n("ShaderNodeBsdfPrincipled", {"Base Color": col, "Roughness": rough, "Specular IOR Level": 0.18,
                                           "Normal": bump})
    nb.links.new(nb.out(b), out.inputs["Surface"])
    return m


# =============================================================================================
# thorn branches (dead acacia, paired white spines)
# =============================================================================================
def build_thorns(name="ThornBush", stems=(), seed=5, view=(0.0, 1.0, 0.0), coll=None):
    """Dead acacia-like thorn branches: zig-zag stems (curve, tapered) with paired white spines at the
    nodes (one mesh, attribute 'tip' 0..1 for the brown tips) and short side shoots.
    stems = [(p0, d0, length, r0, r1), ...] in the root's space. Spines spread mostly across `view`
    so they read in silhouette."""
    rnd = random.Random(seed)
    view = Vector(view).normalized()
    cu = bpy.data.curves.new(name + "_stem", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 1.0
    cu.bevel_resolution = 2
    cu.use_fill_caps = True
    thorn_specs = []

    def stem(p0, d0, L, r0, r1, every, depth=0):
        bend = math.radians(rnd.uniform(-5, 5))
        sp = cu.splines.new("POLY")
        d = Vector(d0).normalized()
        zz = d.cross(view)
        if zz.length < 1e-3:
            zz = d.orthogonal()
        zz.normalize()
        p = Vector(p0)
        pts = [p.copy()]
        n = max(3, int(L / every))
        side = 1
        for i in range(n):
            d = Matrix.Rotation(math.radians(rnd.uniform(8, 22)) * side + bend, 3, zz) @ d
            d = (d + Vector((rnd.uniform(-0.04, 0.04), rnd.uniform(-0.04, 0.04), -0.02 * depth))).normalized()
            side = -side
            p = p + d * (L / n) * rnd.uniform(0.85, 1.15)
            pts.append(p.copy())
        sp.points.add(len(pts) - 1)
        for i, q in enumerate(pts):
            t = i / (len(pts) - 1)
            sp.points[i].co = (q.x, q.y, q.z, 1.0)
            sp.points[i].radius = r0 + (r1 - r0) * t
        for i in range(1, len(pts) - 1):
            t = i / (len(pts) - 1)
            tang = (pts[i + 1] - pts[i - 1]).normalized()
            thorn_specs.append((pts[i], tang, r0 + (r1 - r0) * t, depth))
            if depth < 2 and i >= 2 and rnd.random() < (0.42 if depth == 0 else 0.25):
                sd = Matrix.Rotation(math.radians(rnd.choice((-1, 1)) * rnd.uniform(28, 55)), 3, zz) @ tang
                sd = (sd + Vector((rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), 0))).normalized()
                stem(pts[i], sd, L * rnd.uniform(0.25, 0.45) * (1 - t * 0.5), (r0 + (r1 - r0) * t) * 0.65, 0.0008,
                     every * 0.85, depth + 1)

    for p0, d0, L, r0, r1 in stems:
        stem(Vector(p0), Vector(d0), L, r0, r1, 0.017)
    stem_o = C.link(bpy.data.objects.new(name + "_stem", cu), coll)
    verts, faces, tipv = [], [], []
    segs = 6
    for (p, tang, r, depth) in thorn_specs:
        side = tang.cross(view)
        if side.length < 1e-3:
            side = tang.orthogonal()
        side.normalize()
        side = Matrix.Rotation(math.radians(rnd.uniform(-35, 35)), 3, tang) @ side
        L0 = rnd.uniform(0.02, 0.038) * (0.7 if depth else 1.0)
        spread = math.radians(rnd.uniform(50, 70))
        for sgn in (1, -1):
            dd = (side * sgn * math.sin(spread) + tang * math.cos(spread) * rnd.uniform(0.5, 0.9)).normalized()
            L = L0 * rnd.uniform(0.85, 1.15)
            rb = max(0.0009, r * 0.4)
            base = p + dd * r * 0.6
            a1 = dd.orthogonal().normalized()
            a2 = dd.cross(a1).normalized()
            i0 = len(verts)
            for k in range(segs):
                ang = 2 * math.pi * k / segs
                verts.append(base + (a1 * math.cos(ang) + a2 * math.sin(ang)) * rb)
                tipv.append(0.0)
            for k in range(segs):
                ang = 2 * math.pi * k / segs
                verts.append(base + dd * L * 0.45 + (a1 * math.cos(ang) + a2 * math.sin(ang)) * rb * 0.5)
                tipv.append(0.45)
            verts.append(base + dd * L)
            tipv.append(1.0)
            for k in range(segs):
                k1 = (k + 1) % segs
                faces.append((i0 + k, i0 + k1, i0 + segs + k1, i0 + segs + k))
                faces.append((i0 + segs + k, i0 + segs + k1, i0 + 2 * segs))
    me = bpy.data.meshes.new(name + "_thorns")
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    at = me.attributes.new("tip", "FLOAT", "POINT")
    at.data.foreach_set("value", tipv)
    me.shade_smooth()
    th_o = C.link(bpy.data.objects.new(name + "_thorns", me), coll)
    bark, nb, out = FX._new_mat(name + "_bark")
    oc = nb.n("ShaderNodeTexCoord").outputs["Object"]
    n1 = nb.out(nb.noise(nb.v("MULTIPLY", oc, (60.0, 60.0, 60.0)), scale=1.0, detail=6.0, rough=0.65), "Fac")
    n2 = nb.out(nb.noise(nb.v("MULTIPLY", oc, (300.0, 300.0, 900.0)), scale=1.0, detail=3.0), "Fac")
    col = nb.mixc(nb.smooth(n1, 0.3, 0.75), (0.16, 0.12, 0.10), (0.34, 0.29, 0.25))
    col = nb.mixc(nb.mul(nb.smooth(n2, 0.5, 0.8), 0.6), col, (0.55, 0.51, 0.46))     # bleached grey streaks
    bump = nb.n("ShaderNodeBump", {"Height": nb.add(n2, nb.mul(n1, 0.5)), "Distance": 0.0004, "Strength": 0.8})
    b = nb.n("ShaderNodeBsdfPrincipled", {"Base Color": col, "Roughness": 0.85, "Normal": bump})
    nb.links.new(nb.out(b), out.inputs["Surface"])
    stem_o.data.materials.append(bark)
    tm, tb, tout = FX._new_mat(name + "_spine")
    tip = tb.out(tb.sattr("tip"), "Fac")
    tcol = tb.mixc(tb.smooth(tip, 0.55, 0.95), (0.80, 0.76, 0.68), (0.30, 0.16, 0.09))
    tbsdf = tb.n("ShaderNodeBsdfPrincipled", {"Base Color": tcol, "Roughness": 0.42, "Subsurface Weight": 0.15,
                                               "Subsurface Radius": (0.004, 0.003, 0.002)})
    tb.links.new(tb.out(tbsdf), tout.inputs["Surface"])
    th_o.data.materials.append(tm)
    root = C.link(bpy.data.objects.new(name, None), coll)
    for o in (stem_o, th_o):
        FX._parent(o, root)
    return root


# =============================================================================================
# spreading mud cracks (copy of lib fx._cracks_tree + a growing reveal front)
# =============================================================================================
def _spreading_cracks_tree():
    name = "s11a_SpreadCracks"
    if name in bpy.data.node_groups:
        return bpy.data.node_groups[name]
    t, nb, gi, go = FX._gn_tree(name, [("Geometry", "NodeSocketGeometry"), ("Cell", "NodeSocketFloat", 0.1),
                                       ("Width", "NodeSocketFloat", 0.08), ("Depth", "NodeSocketFloat", 0.015),
                                       ("Curl", "NodeSocketFloat", 0.004), ("Seed", "NodeSocketFloat", 0.0),
                                       ("Origin", "NodeSocketVector", None), ("Radius", "NodeSocketFloat", 0.0),
                                       ("Ramp", "NodeSocketFloat", 0.12), ("Base", "NodeSocketFloat", 0.15),
                                       ("Wobble", "NodeSocketFloat", 0.2)])
    G = lambda k: gi.outputs[k]
    pos = nb.out(nb.n("GeometryNodeInputPosition"))
    q = nb.v("ADD", nb.v("SCALE", pos, scale=nb.div(1.0, G("Cell"))), nb.xyz(G("Seed"), nb.mul(G("Seed"), 0.7), 0.0))
    q = nb.v("ADD", q, nb.v("SCALE", nb.v("SUBTRACT", nb.out(nb.noise(q, scale=0.6, detail=2.0), "Color"), (0.5, 0.5, 0.5)), scale=0.35))
    vor = nb.n("ShaderNodeTexVoronoi", {"Vector": nb.v("MULTIPLY", q, (1.0, 1.0, 0.0)), "Scale": 1.0, "Randomness": 0.9},
               feature="DISTANCE_TO_EDGE")
    dist = nb.out(vor, "Distance")
    # reveal: 1 behind the growing front, 0 ahead of it (noisy, per-region lag)
    rxy = nb.v("LENGTH", nb.v("MULTIPLY", nb.v("SUBTRACT", pos, G("Origin")), (1.0, 1.0, 0.0)))
    wob = nb.mul(nb.sub(nb.out(nb.noise(nb.v("SCALE", pos, scale=3.0), scale=1.0, detail=2.0), "Fac"), 0.5), G("Wobble"))
    reveal = nb.smooth(nb.sub(nb.add(G("Radius"), wob), rxy), 0.0, G("Ramp"))
    # pre-existing (old) cracks are fine hairlines: Base fraction of full width/depth
    amt = nb.add(G("Base"), nb.mul(nb.sub(1.0, G("Base")), reveal))
    w = nb.mul(G("Width"), nb.madd(amt, 0.75, 0.25))
    groove = nb.mul(nb.sub(1.0, nb.smooth(dist, 0.0, w)), nb.smooth(amt, 0.0, 0.2))
    curl = nb.mul(nb.sub(1.0, nb.smooth(dist, w, nb.mul(w, 3.0))), nb.sub(1.0, groove))
    dz = nb.add(nb.mul(groove, nb.mul(nb.mul(G("Depth"), amt), -1.0)), nb.mul(nb.mul(curl, G("Curl")), amt))
    g = nb.out(nb.n("GeometryNodeSetPosition", {"Geometry": G("Geometry"), "Offset": nb.xyz(0.0, 0.0, dz)}))
    g = nb.out(nb.n("GeometryNodeStoreNamedAttribute", {"Geometry": g, "Name": "fx_crack", "Value": groove}, data_type="FLOAT", domain="POINT"))
    g = nb.out(nb.n("GeometryNodeSetShadeSmooth", {"Geometry": g, "Shade Smooth": True}))
    nb.links.new(g, go.inputs[0])
    return t


def _focus_grid(name, x=(-1, 1), y=(-1, 1), n=(200, 200), a=0.35):
    """Grid that is dense around the origin (spacing x a) and coarser toward its edges
    (cubic remap of a uniform parameter), so the macro foreground gets ~2 mm vertices."""
    def axis(lo, hi, k):
        out = []
        for i in range(k + 1):
            t = -1.0 + 2.0 * i / k
            m = a * t + (1 - a) * t ** 3
            out.append(m * (-lo if m < 0 else hi))
        return out
    xs = axis(x[0], x[1], n[0])
    ys = axis(y[0], y[1], n[1])
    nx = len(xs)
    co = np.zeros((len(ys) * nx, 3), np.float32)
    gx, gy = np.meshgrid(np.array(xs, np.float32), np.array(ys, np.float32))
    co[:, 0] = gx.ravel()
    co[:, 1] = gy.ravel()
    ii = np.arange(len(ys) * nx).reshape(len(ys), nx)
    q = np.stack([ii[:-1, :-1], ii[:-1, 1:], ii[1:, 1:], ii[1:, :-1]], -1).reshape(-1, 4)
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(co))
    me.vertices.foreach_set("co", co.ravel())
    me.loops.add(len(q) * 4)
    me.loops.foreach_set("vertex_index", q.ravel().astype(np.int32))
    me.polygons.add(len(q))
    me.polygons.foreach_set("loop_start", (np.arange(len(q)) * 4).astype(np.int32))
    me.update(calc_edges=True)
    return me


# =============================================================================================
# heat haze (compositor): tileable noise image scrolled upward, depth-masked displacement
# =============================================================================================
def _noise_image(name, size=(270, 480), seed=0, cutoff=0.1, aniso=(1.0, 2.4)):
    """Tileable smooth 2-channel noise (R, G = displacement x, y around 0.5); FFT-filtered white noise.
    aniso > 1 on y squashes the features vertically -> horizontal heat ripples."""
    w_, h_ = size
    rng = np.random.default_rng(seed)
    wn = rng.standard_normal((h_, w_, 2))
    fy = np.fft.fftfreq(h_)[:, None] * aniso[1]
    fx = np.fft.fftfreq(w_)[None, :] * aniso[0]
    f = np.sqrt(fx * fx + fy * fy)
    filt = np.exp(-(f / cutoff) ** 2)
    out = np.zeros((h_, w_, 4), np.float32)
    for c in range(2):
        v = np.real(np.fft.ifft2(np.fft.fft2(wn[..., c]) * filt))
        v = v / (3.0 * v.std() + 1e-9)
        out[..., c] = np.clip(0.5 + 0.5 * v, 0.0, 1.0)
    out[..., 3] = 1.0
    im = bpy.data.images.new(name, w_, h_, alpha=True, float_buffer=True)
    im.pixels.foreach_set(out.ravel())
    im.pack()
    return im


def _edge_image(name, size=(270, 480), margin=0.05):
    w_, h_ = size
    x = np.minimum(np.arange(w_), w_ - 1 - np.arange(w_)) / (margin * w_)
    y = np.minimum(np.arange(h_), h_ - 1 - np.arange(h_)) / (margin * w_)
    m = np.clip(np.minimum(x[None, :], y[:, None]), 0, 1).astype(np.float32)
    m = m * m * (3 - 2 * m)
    out = np.stack([m, m, m, np.ones_like(m)], -1)
    im = bpy.data.images.new(name, w_, h_, alpha=True, float_buffer=True)
    im.pixels.foreach_set(out.ravel())
    im.pack()
    return im


def heat_haze_compositor(amount_px=3.0, near=0.7, far=3.5):
    sc = bpy.context.scene
    sc.view_layers[0].use_pass_z = True
    sc.use_nodes = True
    ct = sc.node_tree
    for n in list(ct.nodes):
        ct.nodes.remove(n)
    N = ct.nodes
    L = ct.links
    rl = N.new("CompositorNodeRLayers")
    time = N.new("CompositorNodeSceneTime")
    layers = []
    for i, (spd, seed, cut) in enumerate(((1.6, 1, 0.09), (2.6, 2, 0.045))):
        img = N.new("CompositorNodeImage")
        img.image = _noise_image("s11a_haze%d" % i, (270, 480), seed, cutoff=cut)
        tr = N.new("CompositorNodeTranslate")
        tr.wrap_axis = "BOTH"
        mul = N.new("CompositorNodeMath")
        mul.operation = "MULTIPLY"
        mul.inputs[1].default_value = spd
        L.new(time.outputs["Frame"], mul.inputs[0])
        L.new(img.outputs["Image"], tr.inputs["Image"])
        L.new(mul.outputs[0], tr.inputs["Y"])
        sc_ = N.new("CompositorNodeScale")
        sc_.space = "RENDER_SIZE"
        sc_.frame_method = "STRETCH"
        L.new(tr.outputs["Image"], sc_.inputs["Image"])
        layers.append(sc_)
    add = N.new("CompositorNodeMixRGB")
    add.blend_type = "ADD"
    add.inputs[0].default_value = 1.0
    L.new(layers[0].outputs[0], add.inputs[1])
    L.new(layers[1].outputs[0], add.inputs[2])
    centre = N.new("CompositorNodeMixRGB")          # (a + b) - 1  ->  -1..1
    centre.blend_type = "SUBTRACT"
    centre.inputs[0].default_value = 1.0
    centre.inputs[2].default_value = (1.0, 1.0, 1.0, 1.0)
    L.new(add.outputs[0], centre.inputs[1])
    # depth mask: far ground + sky shimmer, the sherd stays crisp
    mr = N.new("CompositorNodeMapRange")
    mr.inputs["From Min"].default_value = near
    mr.inputs["From Max"].default_value = far
    mr.inputs["To Min"].default_value = 0.0
    mr.inputs["To Max"].default_value = 1.0
    mr.use_clamp = True
    L.new(rl.outputs["Depth"], mr.inputs["Value"])
    # frame-edge falloff (displacement must not pull in black from outside the frame)
    eimg = N.new("CompositorNodeImage")
    eimg.image = _edge_image("s11a_haze_edge")
    esc = N.new("CompositorNodeScale")
    esc.space = "RENDER_SIZE"
    esc.frame_method = "STRETCH"
    L.new(eimg.outputs["Image"], esc.inputs["Image"])
    emul = N.new("CompositorNodeMath")
    emul.operation = "MULTIPLY"
    L.new(mr.outputs[0], emul.inputs[0])
    L.new(esc.outputs[0], emul.inputs[1])
    mask = N.new("CompositorNodeMixRGB")
    mask.blend_type = "MULTIPLY"
    mask.inputs[0].default_value = 1.0
    L.new(centre.outputs[0], mask.inputs[1])
    L.new(emul.outputs[0], mask.inputs[2])
    disp = N.new("CompositorNodeDisplace")
    disp.inputs["X Scale"].default_value = amount_px * 0.6
    disp.inputs["Y Scale"].default_value = amount_px
    L.new(rl.outputs["Image"], disp.inputs["Image"])
    L.new(mask.outputs[0], disp.inputs["Vector"])
    comp = N.new("CompositorNodeComposite")
    L.new(disp.outputs["Image"], comp.inputs["Image"])
    sc.render.use_compositing = True
    return disp


# =============================================================================================
def build(ctx):
    N = ctx.render_frames
    rnd = random.Random(SEED)
    p1s, p1e = ctx.phrase_frames(0)
    p2s, p2e = ctx.phrase_frames(1)

    # ---------------------------------------------------------------- light: harsh white noon sun
    sun_az, sun_el = 78.0, 56.0
    d = Vector((math.sin(math.radians(sun_az)), -math.cos(math.radians(sun_az)), 0))
    C.world_hdri("qwantani_noon_puresky", strength=0.75, saturation=0.28, tint=(1.0, 0.95, 0.86),
                 rotation=FX.hdri_rotation_for_sun((d.x, d.y)), background_strength=3.6)
    C.sun(elevation=sun_el, azimuth=sun_az, energy=4.6, temp=6300, angle=0.5)

    # ---------------------------------------------------------------- ground: parched, cracking mud
    gnd = FX.cracked_ground((0, 0, 0), size=0.2, res=4, cell=CELL, depth=0.014, width=0.06, texture=GROUND_TEX,
                            tint=GROUND_TINT, seed=SEED, name="Mud")
    gm = gnd.active_material
    old = gnd.data
    gnd.data = _focus_grid("MudGrid", x=(-0.8, 0.8), y=(-0.55, 2.6), n=(360, 420), a=0.35)
    bpy.data.meshes.remove(old)
    C.assign(gnd, gm)
    mod = gnd.modifiers["Cracks"]
    mod.node_group = _spreading_cracks_tree()
    FX._mod_set(mod, Cell=CELL, Width=0.06, Depth=0.014, Curl=0.004, Seed=SEED * 13.1, Origin=Vector((0.0, 0.0, 0.0)),
                Ramp=0.10, Base=0.16, Wobble=0.16)
    rkey = FX._mod_path(mod, "Radius")
    for f, r in ((1, 0.0), (int(p1s + 10), 0.02), (int(p2s), 0.14), (int(p2e), 0.7), (N, 0.9)):
        mod[FX._mod_ident(mod, "Radius")] = r
        gnd.keyframe_insert(rkey, frame=f)
    # far ground (blurred) fading into the white heat haze toward the horizon
    far_m = C.mat_pbr(GROUND_TEX, scale=1.0 / (CELL * 4), tint=GROUND_TINT, name="s11a_far")
    nbf = FX.NB(far_m.node_tree)
    bf = C.bsdf(far_m)
    src = bf.inputs["Base Color"].links[0].from_socket
    vd = nbf.out(nbf.n("ShaderNodeCameraData"), "View Distance")
    nbf.links.new(nbf.mixc(nbf.mul(nbf.smooth(vd, 2.0, 90.0), 0.85), src, (0.62, 0.58, 0.52)), bf.inputs["Base Color"])
    C.ground_plane(size=300, mat_=far_m, z=-0.016, name="FarGround")

    # ---------------------------------------------------------------- the sherd
    sherd, origin = build_sherd("Sherd")
    craze_vals = []
    for kind in ("slip", "break", "inner"):
        m = sherd_material("s11a_" + kind, kind, craze=True, crack_origin=origin)
        sherd.data.materials.append(m)
        craze_vals.append(m.node_tree.nodes["craze"].outputs[0])
    for f, r in ((1, 0.0), (int(p1s) + 6, 0.004), (int(p1e) + 10, 0.07), (int(p2e), 0.12), (N, 0.13)):
        for s in craze_vals:
            s.default_value = r
            s.keyframe_insert("default_value", frame=f)
    # pose: concave (inner, wheel-ridged) side up, tipped toward the camera; resting on the mud
    me = sherd.data
    nsum = Vector()
    for poly in me.polygons:
        if poly.material_index == 0:
            nsum += poly.normal * poly.area
    want = Vector((0.0, math.sin(math.radians(SHERD_TIP)), -math.cos(math.radians(SHERD_TIP))))   # outer face down
    q = nsum.normalized().rotation_difference(want)
    u_dir = q @ Vector((0.0, 1.0, 0.0))             # circumferential direction of the sherd
    yaw0 = -math.atan2(u_dir.y, u_dir.x)
    q = Quaternion(want, yaw0 + math.radians(SHERD_YAW)) @ q
    sherd.rotation_mode = "QUATERNION"
    sherd.rotation_quaternion = q
    bpy.context.view_layer.update()
    zmin = min((sherd.matrix_world @ v.co).z for v in me.vertices)
    sherd.location = SHARD_AT + Vector((0, 0, -zmin - 0.0025))

    # ---------------------------------------------------------------- dead thorn bush behind, against the sky
    bush = build_thorns("ThornBush", stems=[
        ((0, 0, -0.01), (0.55, 0.05, 0.75), 0.30, 0.0058, 0.0014),
        ((0.006, 0.004, -0.01), (0.15, 0.25, 1.0), 0.21, 0.0050, 0.0013),
        ((-0.006, 0.0, -0.01), (0.95, -0.2, 0.3), 0.24, 0.0045, 0.0012)], seed=7)
    bush.location = BUSH_AT
    bush.rotation_euler = (0, 0, math.radians(-6))
    # a broken-off thorn twig lying on the mud between sherd and bush
    twig = build_thorns("FallenTwig", stems=[((0, 0, 0.003), (1.0, 0.15, 0.02), 0.2, 0.0035, 0.0011)], seed=3,
                        view=(0.0, 0.3, 1.0))
    twig.location = (0.05, 0.11, 0.0)
    twig.rotation_euler = (0, 0, math.radians(-12))
    # pale limestone grit / pebbles
    rock_m = C.mat_pbr("rock_face_03", scale=14.0, tint=(1.05, 1.0, 0.95), name="s11a_stone", hue_sat_val=(0.5, 0.35, 1.3))
    for i, (x, y, sz) in enumerate(((0.07, 0.13, 0.011), (-0.09, -0.05, 0.006), (0.11, 0.05, 0.008), (0.05, -0.11, 0.004),
                                    (-0.05, 0.10, 0.005), (0.15, 0.22, 0.012), (-0.14, 0.24, 0.01), (0.02, 0.33, 0.009))):
        st = C.prim("ico_sphere", name="Stone%d" % i, subdivisions=3, radius=1.0, loc=(x, y, sz * 0.3))
        st.scale = (sz * rnd.uniform(1.0, 1.5), sz * rnd.uniform(0.8, 1.2), sz * rnd.uniform(0.5, 0.8))
        st.rotation_euler = (0, 0, rnd.uniform(0, 6.28))
        C.displace(st, strength=0.25, scale=0.6, subdiv=0)
        C.assign(st, rock_m)
        C.shade_smooth(st)

    # ---------------------------------------------------------------- camera: low, slow push
    focus = C.link(bpy.data.objects.new("Focus", None))
    focus.location = sherd.location + Vector((0, -0.022, 0.012))
    cam = C.camera((0, -0.46, 0.065), (0, 0, 0.0), lens=50, fstop=7.1, focus=focus)

    def path(f):
        u = C.ease_in_out((f - 1) / (N - 1))
        loc = Vector((0.02 - 0.03 * u, -0.40 + 0.085 * u, 0.062 + 0.008 * u))
        tgt = Vector((0.003 * u, 0.07, 0.016))
        return loc + C.shake(f, 0.0010, 0.35, 3), tgt
    C.animate_camera(cam, path)

    heat_haze_compositor(amount_px=4.0, near=0.5, far=1.6)
    ctx.samples = 4          # 4 vs 6 spp indistinguishable here (DOF + bright light), saves ~3 s/frame
    ctx.render_opts.update({"volumetrics": "low", "exposure": 0.0})
    ctx.post.update({"grade": "warm", "saturation": 0.82, "contrast": 1.02, "lift": 0.012, "exposure": 0.08,
                     "highlights": [0.02, 0.015, 0.0], "bloom": 0.3, "bloom_threshold": 0.72, "halation": 0.08,
                     "vignette": 0.14, "caption": {"y": 0.72, "ink": "dark", "halo": 0.8}})
