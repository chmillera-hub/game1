import sys; sys.path.insert(0, "/home/user/game1/video/pipeline/sets"); from _common import *
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, noise
from mathutils.bvhtree import BVHTree

random.seed(7)
scn = reset_scene()
SET = collection("SET_hillside"); LIT = collection("LIGHTS_hillside")
SUN_EL, SUN_AZ = 6.0, -1.0   # sun toward +Y, slightly +X

# ---------------- material helpers ----------------
def nodes_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; return m, nt, nt.nodes, nt.links, nt.nodes["Principled BSDF"]

def tex(nodes, kind, scale, detail=4.0, coord=None, links=None):
    t = nodes.new(kind); t.inputs["Scale"].default_value = scale
    if "Detail" in t.inputs: t.inputs["Detail"].default_value = detail
    if coord is not None: links.new(coord, t.inputs["Vector"])
    return t

def ramp(nodes, links, fac, stops):
    r = nodes.new("ShaderNodeValToRGB"); links.new(fac, r.inputs["Fac"])
    els = r.color_ramp.elements
    while len(els) < len(stops): els.new(0.5)
    for e, (p, c) in zip(els, stops): e.position = p; e.color = (*c, 1)
    return r

def bump(nodes, links, h, strength, dist, bsdf):
    b = nodes.new("ShaderNodeBump"); b.inputs["Strength"].default_value = strength
    b.inputs["Distance"].default_value = dist
    links.new(h, b.inputs["Height"]); links.new(b.outputs["Normal"], bsdf.inputs["Normal"]); return b

def mat_ground():
    m, nt, N, L, b = nodes_mat("M_dry_grass")
    tc = N.new("ShaderNodeTexCoord").outputs["Object"]
    n1 = tex(N, "ShaderNodeTexNoise", 0.08, 5, tc, L)
    n2 = tex(N, "ShaderNodeTexNoise", 0.9, 6, tc, L)
    mix = N.new("ShaderNodeMix"); mix.data_type = 'FLOAT'; mix.inputs[0].default_value = 0.35
    L.new(n1.outputs["Fac"], mix.inputs[2]); L.new(n2.outputs["Fac"], mix.inputs[3])
    r = ramp(N, L, mix.outputs[0], [(0.30, (0.10, 0.07, 0.035)), (0.45, (0.30, 0.19, 0.06)),
                                    (0.58, (0.42, 0.28, 0.09)), (0.72, (0.20, 0.17, 0.07))])
    L.new(r.outputs["Color"], b.inputs["Base Color"])
    fine = tex(N, "ShaderNodeTexNoise", 40, 8, tc, L)
    streak = N.new("ShaderNodeTexWave"); streak.inputs["Scale"].default_value = 60; streak.inputs["Distortion"].default_value = 25; streak.inputs["Detail"].default_value = 6; L.new(tc, streak.inputs["Vector"])
    vor = tex(N, "ShaderNodeTexVoronoi", 18, 0, tc, L)
    ad = N.new("ShaderNodeMath"); ad.operation = 'ADD'
    L.new(streak.outputs["Fac"], ad.inputs[0]); L.new(vor.outputs["Distance"], ad.inputs[1])
    bump(N, L, ad.outputs[0], 1.0, 0.08, b)
    mm = N.new("ShaderNodeMix"); mm.data_type = 'RGBA'; mm.blend_type = 'MULTIPLY'; mm.inputs[0].default_value = 0.6
    L.new(r.outputs["Color"], mm.inputs[6]); L.new(streak.outputs["Color"], mm.inputs[7]); L.new(mm.outputs[2], b.inputs["Base Color"])
    rr = N.new("ShaderNodeMapRange"); L.new(fine.outputs["Fac"], rr.inputs[0])
    rr.inputs[3].default_value = 0.75; rr.inputs[4].default_value = 0.95
    L.new(rr.outputs[0], b.inputs["Roughness"])
    return m

def mat_simple_var(name, c1, c2, scale, rough, bstr, bdist, sheen=0.0, sss=0.0, vor=False):
    m, nt, N, L, b = nodes_mat(name)
    tc = N.new("ShaderNodeTexCoord").outputs["Object"]
    n = tex(N, "ShaderNodeTexNoise", scale, 6, tc, L)
    r = ramp(N, L, n.outputs["Fac"], [(0.35, c1), (0.65, c2)])
    L.new(r.outputs["Color"], b.inputs["Base Color"])
    h = tex(N, "ShaderNodeTexVoronoi" if vor else "ShaderNodeTexNoise", scale * 8, 8, tc, L)
    bump(N, L, h.outputs["Distance" if vor else "Fac"], bstr, bdist, b)
    rr = N.new("ShaderNodeMapRange"); L.new(n.outputs["Fac"], rr.inputs[0])
    rr.inputs[3].default_value = rough - 0.1; rr.inputs[4].default_value = min(1, rough + 0.1)
    L.new(rr.outputs[0], b.inputs["Roughness"])
    if sheen: b.inputs["Sheen Weight"].default_value = sheen
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss
        b.inputs["Subsurface Radius"].default_value = (0.1, 0.06, 0.04)
        b.inputs["Subsurface Scale"].default_value = 0.05
    return m

def mat_wool():
    m, nt, N, L, b = nodes_mat("M_wool")
    tc = N.new("ShaderNodeTexCoord").outputs["Object"]
    n = tex(N, "ShaderNodeTexNoise", 3, 5, tc, L)
    r = ramp(N, L, n.outputs["Fac"], [(0.3, (0.52, 0.45, 0.34)), (0.7, (0.74, 0.67, 0.53))])
    L.new(r.outputs["Color"], b.inputs["Base Color"])
    v = tex(N, "ShaderNodeTexVoronoi", 30, 0, tc, L)
    f = tex(N, "ShaderNodeTexNoise", 90, 10, tc, L)
    ad = N.new("ShaderNodeMath"); ad.operation = 'MULTIPLY_ADD'
    L.new(v.outputs["Distance"], ad.inputs[0]); ad.inputs[1].default_value = 1.0
    L.new(f.outputs["Fac"], ad.inputs[2])
    bump(N, L, ad.outputs[0], 0.9, 0.02, b)
    b.inputs["Roughness"].default_value = 0.95
    b.inputs["Sheen Weight"].default_value = 0.6
    b.inputs["Sheen Tint"].default_value = (1.0, 0.9, 0.75, 1)
    b.inputs["Subsurface Weight"].default_value = 0.15
    b.inputs["Subsurface Scale"].default_value = 0.03
    return m

def mat_leaves():
    m, nt, N, L, b = nodes_mat("M_olive_leaves")
    tc = N.new("ShaderNodeTexCoord").outputs["Object"]
    v = tex(N, "ShaderNodeTexVoronoi", 9, 0, tc, L)
    n = tex(N, "ShaderNodeTexNoise", 2.0, 4, tc, L)
    r = ramp(N, L, n.outputs["Fac"], [(0.35, (0.10, 0.13, 0.07)), (0.65, (0.27, 0.30, 0.20))])
    L.new(r.outputs["Color"], b.inputs["Base Color"])
    bump(N, L, v.outputs["Distance"], 1.0, 0.15, b)
    b.inputs["Roughness"].default_value = 0.55
    b.inputs["Sheen Weight"].default_value = 0.5
    b.inputs["Sheen Tint"].default_value = (0.8, 0.85, 0.8, 1)
    return m

M_GROUND = mat_ground()
M_ROCK = mat_simple_var("M_limestone", (0.50, 0.46, 0.39), (0.70, 0.66, 0.57), 1.5, 0.85, 0.5, 0.06, vor=True)
M_BARK = mat_simple_var("M_olive_bark", (0.12, 0.10, 0.08), (0.28, 0.25, 0.21), 3.0, 0.9, 0.8, 0.04)
M_LEAF = mat_leaves()
M_WOOL = mat_wool()
M_DARK = mat_simple_var("M_sheep_dark", (0.025, 0.02, 0.018), (0.07, 0.055, 0.045), 20, 0.7, 0.2, 0.004, sheen=0.4, sss=0.1)
M_LIGHT = mat_simple_var("M_sheep_face", (0.48, 0.38, 0.30), (0.62, 0.52, 0.42), 20, 0.7, 0.2, 0.004, sheen=0.4, sss=0.2)
M_HOOF = principled("M_hoof", (0.03, 0.025, 0.02), 0.5)
M_EYE = principled("M_eye", (0.01, 0.008, 0.005), 0.15)
M_HILLS = mat_simple_var("M_far_hills", (0.10, 0.075, 0.05), (0.17, 0.12, 0.07), 0.01, 0.9, 0.3, 0.5)
M_TUFT = mat_simple_var("M_grass_tuft", (0.40, 0.28, 0.10), (0.68, 0.53, 0.25), 2, 0.6, 0.0, 0.01, sss=0.0)
M_TUFT.node_tree.nodes["Principled BSDF"].inputs["Transmission Weight"].default_value = 0.0

def new_obj(name, me, col=SET):
    o = bpy.data.objects.new(name, me); col.objects.link(o); return o

def smooth(me):
    for p in me.polygons: p.use_smooth = True

# ---------------- terrain ----------------
bpy.ops.mesh.primitive_grid_add(x_subdivisions=110, y_subdivisions=110, size=200)
terr = bpy.context.object; terr.name = "TERRAIN"; terr.data.name = "TERRAIN"; link(terr, SET)
terr.data.materials.append(M_GROUND); smooth(terr.data)
vg = terr.vertex_groups.new(name="falloff")
for v in terr.data.vertices:
    r = Vector((v.co.x, v.co.y)).length
    vg.add([v.index], max(0.12, min(1.0, (r - 6) / 45)), 'REPLACE')
tx = bpy.data.textures.new("T_terrain", 'CLOUDS'); tx.noise_scale = 35; tx.noise_depth = 2
d = terr.modifiers.new("Displace", 'DISPLACE'); d.texture = tx; d.strength = 9; d.vertex_group = "falloff"
d.texture_coords = 'GLOBAL'
tx2 = bpy.data.textures.new("T_terrain_small", 'CLOUDS'); tx2.noise_scale = 6; tx2.noise_depth = 1
d2 = terr.modifiers.new("Displace_small", 'DISPLACE'); d2.texture = tx2; d2.strength = 0.6; d2.texture_coords = 'GLOBAL'
dg = bpy.context.evaluated_depsgraph_get()
bvh = BVHTree.FromObject(terr, dg)
def h_at(x, y):
    hit = bvh.ray_cast(Vector((x, y, 500)), Vector((0, 0, -1)))
    return hit[0].z if hit[0] else 0.0
z0 = h_at(0, 0)
terr.location.z = -z0
def ground(x, y): return h_at(x, y) - z0
def gnormal(x, y):
    hit = bvh.ray_cast(Vector((x, y, 500)), Vector((0, 0, -1)))
    return hit[1] if hit[1] else Vector((0, 0, 1))

# ---------------- distant hills (ring) ----------------
def far_hills():
    bm = bmesh.new(); segs, rings = 96, 6
    rows = []
    for j in range(rings):
        rad = 140 + j * 90
        row = []
        for i in range(segs):
            a = 2 * math.pi * i / segs
            p = Vector((math.cos(a), math.sin(a), 0))
            hgt = (noise.noise(p * 2.2 + Vector((j * 0.3, 0, 0))) * 0.5 + 0.5) * (18 + j * 14) + 2
            if j == 0 or j == rings - 1: hgt *= 0.3 if j == 0 else 0.8
            row.append(bm.verts.new((p.x * rad, p.y * rad, hgt - 6)))
        rows.append(row)
    for j in range(rings - 1):
        for i in range(segs):
            bm.faces.new((rows[j][i], rows[j][(i + 1) % segs], rows[j + 1][(i + 1) % segs], rows[j + 1][i]))
    me = bpy.data.meshes.new("FAR_HILLS"); bm.to_mesh(me); bm.free(); smooth(me)
    me.materials.append(M_HILLS); return new_obj("FAR_HILLS", me)
far_hills()

# ---------------- rocks ----------------
def rock_mesh(i):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    off = Vector((i * 3.1, i * 1.7, 0.5))
    for v in bm.verts:
        c = v.co.copy()
        v.co = c * (1 + 0.35 * noise.noise(c * 1.2 + off) + 0.08 * noise.noise(c * 4 + off))
        v.co.z *= 0.55
        # flatten facets a little for a limestone break
        v.co.z = max(v.co.z, -0.15)
    me = bpy.data.meshes.new(f"ROCK_mesh_{i}"); bm.to_mesh(me); bm.free(); smooth(me)
    me.materials.append(M_ROCK); return me
rmeshes = [rock_mesh(i) for i in range(4)]
rk = 0
for _ in range(60):
    a = random.uniform(0, 2 * math.pi); r = random.uniform(4, 60)
    x, y = math.cos(a) * r, math.sin(a) * r
    if abs(x) < 1.8 and -16 < y < 2: continue
    s = random.uniform(0.25, 1.1) * (1.6 if r > 25 else 1)
    o = new_obj(f"ROCK_{rk:02d}", random.choice(rmeshes)); rk += 1
    o.location = (x, y, ground(x, y) - 0.1 * s); o.scale = (s, s * random.uniform(0.7, 1.3), s)
    o.rotation_euler = (random.uniform(-.15, .15), random.uniform(-.15, .15), random.uniform(0, 6.3))

# ---------------- olive trees ----------------
def olive(name, loc, seed, scale=1.0):
    rnd = random.Random(seed)
    cu = bpy.data.curves.new(name + "_trunk", 'CURVE'); cu.dimensions = '3D'
    cu.bevel_depth = 1.0; cu.bevel_resolution = 2; cu.resolution_u = 4; cu.use_fill_caps = True
    tips = []
    def branch(start, direction, length, radius, depth):
        sp = cu.splines.new('BEZIER'); n = 4
        sp.bezier_points.add(n - 1)
        p = Vector(start); d = Vector(direction).normalized()
        for k, bp in enumerate(sp.bezier_points):
            bp.co = p; bp.handle_left_type = bp.handle_right_type = 'AUTO'
            bp.radius = radius * (1 - 0.55 * k / (n - 1))
            d = (d + Vector((rnd.uniform(-.5, .5), rnd.uniform(-.5, .5), rnd.uniform(-.1, .3)))).normalized()
            p = p + d * (length / (n - 1))
        end = sp.bezier_points[-1].co.copy(); endr = sp.bezier_points[-1].radius
        if depth > 0:
            for _ in range(rnd.choice((2, 3))):
                nd = (d + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(0.2, .8)))).normalized()
                branch(end, nd, length * 0.7, endr * 0.9, depth - 1)
        else:
            tips.append(end)
    # twisted trunk: two intertwined stems
    branch((0.08, 0, -0.2), (0.25, 0.1, 1), 1.9, 0.26, 1)
    branch((-0.1, 0.05, -0.2), (-0.3, -0.1, 1), 1.6, 0.2, 1)
    tr = new_obj(name, cu); tr.data.materials.append(M_BARK)
    tr.location = loc; tr.scale = (scale,) * 3
    # canopy clumps
    bm = bmesh.new()
    for t in tips:
        for _ in range(6):
            c = t + Vector((rnd.uniform(-.9, .9), rnd.uniform(-.9, .9), rnd.uniform(0.0, .9)))
            rr = rnd.uniform(0.45, 0.8)
            g = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=rr, matrix=Matrix.Translation(c))
            for v in g["verts"]:
                v.co = c + (v.co - c) * (1 + 0.35 * noise.noise((v.co) * 1.7 + Vector((seed, 0, 0))))
                v.co.z = c.z + (v.co.z - c.z) * 0.7
    me = bpy.data.meshes.new(name + "_CANOPY"); bm.to_mesh(me); bm.free(); smooth(me)
    me.materials.append(M_LEAF)
    cp = new_obj(name + "_CANOPY", me); cp.parent = tr
    return tr
for i, (x, y, s) in enumerate([(-7.5, 9.0, 1.15), (11.0, 4.0, 1.0), (-13.0, -7.0, 1.05), (24.0, 22.0, 1.3), (-28.0, 30.0, 1.2)]):
    olive(f"OLIVE_{i+1}", (x, y, ground(x, y)), 11 + i, s)

# ---------------- grass tufts (near camera area) ----------------
def tuft_mesh():
    bm = bmesh.new(); rnd = random.Random(3)
    for _ in range(11):
        a = rnd.uniform(0, 6.283); lean = rnd.uniform(0.1, 0.5); hgt = rnd.uniform(0.18, 0.42); w = 0.012
        base = Vector((rnd.uniform(-.05, .05), rnd.uniform(-.05, .05), 0))
        dirv = Vector((math.cos(a) * lean, math.sin(a) * lean, 1)).normalized()
        side = Vector((-math.sin(a), math.cos(a), 0)) * w
        tip = base + dirv * hgt
        v1 = bm.verts.new(base - side); v2 = bm.verts.new(base + side)
        v3 = bm.verts.new(base + dirv * hgt * 0.5 + side * 0.7); v4 = bm.verts.new(base + dirv * hgt * 0.5 - side * 0.7)
        v5 = bm.verts.new(tip + Vector((math.cos(a), math.sin(a), 0)) * hgt * 0.15)
        bm.faces.new((v1, v2, v3, v4)); bm.faces.new((v4, v3, v5))
    me = bpy.data.meshes.new("TUFT_mesh"); bm.to_mesh(me); bm.free(); smooth(me)
    me.materials.append(M_TUFT); return me
tm = tuft_mesh()
TUF = collection("SET_hillside_tufts"); bpy.context.scene.collection.children.unlink(TUF); SET.children.link(TUF)
for i in range(800):
    x = random.uniform(-10, 10); y = random.uniform(-30, 5)
    if (x - 1.0) ** 2 + (y + 27) ** 2 < 16 or (x + 0.5) ** 2 + (y + 13.6) ** 2 < 4: continue
    o = new_obj(f"TUFT_{i:03d}", tm, TUF)
    s = random.uniform(0.6, 1.4)
    o.location = (x, y, ground(x, y) - 0.01); o.scale = (s, s, s * random.uniform(0.8, 1.3))
    o.rotation_euler = (0, 0, random.uniform(0, 6.3))

# ---------------- sheep ----------------
def add_sphere(bm, center, radii, mi, segs=(16, 10), rough=0.0, seed=0):
    g = bmesh.ops.create_uvsphere(bm, u_segments=segs[0], v_segments=segs[1], radius=1.0)
    for v in g["verts"]:
        c = v.co.copy()
        if rough: c = c * (1 + rough * noise.noise(c * 2.5 + Vector((seed, 0, 0))) + rough * 0.5 * noise.noise(c * 6))
        v.co = Vector((c.x * radii[0], c.y * radii[1], c.z * radii[2])) + Vector(center)
    for f in {f for v in g["verts"] for f in v.link_faces}: f.material_index = mi; f.smooth = True
    return g

def add_cyl(bm, p0, p1, r0, r1, mi, segs=8):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0
    m = Matrix.Translation((p0 + p1) / 2) @ d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
    g = bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r0, radius2=r1, depth=d.length, matrix=m)
    for f in {f for v in g["verts"] for f in v.link_faces}: f.material_index = mi; f.smooth = True

NECK = Vector((0, -0.5, 0.66))
def sheep_body_mesh(name, dark_legs, seed):
    bm = bmesh.new()  # mats: 0 wool, 1 legs, 2 hoof
    add_sphere(bm, (0, 0, 0.64), (0.34, 0.56, 0.31), 0, (24, 16), rough=0.07, seed=seed)
    add_sphere(bm, (0, -0.42, 0.66), (0.26, 0.2, 0.25), 0, (16, 10), rough=0.06, seed=seed + 1)  # chest
    add_sphere(bm, (0, 0.58, 0.64), (0.07, 0.08, 0.12), 0, (10, 6), rough=0.1, seed=seed + 2)  # tail
    for sx in (-1, 1):
        for sy, yy in ((-1, -0.36), (1, 0.36)):
            add_cyl(bm, (sx * 0.15, yy, 0.46), (sx * 0.15, yy, 0.06), 0.055, 0.036, 1)
            add_cyl(bm, (sx * 0.15, yy, 0.06), (sx * 0.15, yy - 0.01, 0.0), 0.034, 0.038, 2)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m in (M_WOOL, M_DARK if dark_legs else M_LIGHT, M_HOOF): me.materials.append(m)
    return me

def sheep_head_mesh(name, dark):
    # head object is rotated 180 deg about Z, so geometry points to local +Y
    bm = bmesh.new()  # mats: 0 skin, 1 wool, 2 eye
    add_cyl(bm, (0, -0.05, 0.0), (0, 0.22, 0.10), 0.16, 0.12, 1, 12)  # woolly neck
    add_sphere(bm, (0, 0.24, 0.14), (0.13, 0.12, 0.13), 1, (14, 8), rough=0.08)  # poll wool
    add_sphere(bm, (0, 0.36, 0.08), (0.095, 0.17, 0.105), 0, (16, 10))           # face
    add_sphere(bm, (0, 0.47, 0.03), (0.062, 0.06, 0.058), 0, (12, 8))             # muzzle
    for sx in (-1, 1):
        add_sphere(bm, (sx * 0.12, 0.29, 0.15), (0.06, 0.025, 0.03), 0, (8, 6))  # ears
        add_sphere(bm, (sx * 0.088, 0.33, 0.11), (0.017, 0.017, 0.017), 2, (8, 6))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m in (M_DARK if dark else M_LIGHT, M_WOOL, M_EYE): me.materials.append(m)
    return me

bodies = [sheep_body_mesh("SHEEP_body_dark", True, 1), sheep_body_mesh("SHEEP_body_light", False, 5)]
heads = [sheep_head_mesh("SHEEP_head_dark", True), sheep_head_mesh("SHEEP_head_light", False)]

def make_sheep(name, x, y, facing_deg, scale, dark, graze):
    body = new_obj(name, bodies[0 if dark else 1])
    nrm = gnormal(x, y)
    body.location = (x, y, ground(x, y) - 0.02 * scale)
    body.rotation_euler = (math.atan2(nrm.y, nrm.z) * 0.5, -math.atan2(nrm.x, nrm.z) * 0.5, math.radians(facing_deg))
    body.scale = (scale,) * 3
    head = new_obj(name + "_HEAD", heads[0 if dark else 1])
    head.parent = body; head.location = NECK
    head.rotation_euler = (math.radians(-60 if graze else random.uniform(-8, 6)), 0, math.pi)
    body["grazing"] = bool(graze)
    return body

# (x, y, facing, scale, dark, graze); facing is degrees about Z (0 = faces -Y)
FLOCK = [
    (-1.0, -8.6, 80, 1.0, True, False),     # MED foreground head, profile
    (1.0, -6.5, -100, 0.95, False, False),  # MED mid head
    (2.6, -4.2, 70, 1.0, False, True),
    (-3.0, -3.5, -40, 1.05, True, False),
    (3.8, -9.5, 20, 0.95, False, True),
    (-2.4, -10.8, -20, 1.0, False, False),
    (1.2, -12.8, 120, 1.05, True, True),
    (-5.5, -7.8, -90, 0.9, False, True),
    (6.5, -6.2, 45, 1.0, True, False),
    (-1.5, -14.5, 10, 0.95, False, True),
    (5.2, -13.6, -60, 1.0, False, False),
    (-7.2, -12.6, 30, 1.0, True, True),
]
for i, (x, y, f, s, dk, g) in enumerate(FLOCK):
    make_sheep(f"SHEEP_{i+1}", x, y, f, s, dk, g)
make_sheep("PROP_LAMB", -1.6, -5.0, -120, 0.6, False, False)

# ---------------- flock control hook ----------------
ctrl = bpy.data.objects.new("FLOCK_CTRL", None); SET.objects.link(ctrl)
ctrl.empty_display_type = 'PLAIN_AXES'; ctrl.location = (0, -8, 0)
ctrl["note"] = "Head hooks: rotate SHEEP_<n>_HEAD / PROP_LAMB_HEAD about local X: 0=up, -60deg=grazing"

# ---------------- world & sun ----------------
w = bpy.data.worlds.new("W_hillside"); scn.world = w; w.use_nodes = True
wn = w.node_tree.nodes; bg = wn["Background"]
sky = wn.new("ShaderNodeTexSky"); sky.sky_type = 'NISHITA'
sky.sun_elevation = math.radians(SUN_EL); sky.sun_rotation = math.radians(SUN_AZ)
sky.sun_disc = True; sky.sun_size = math.radians(1.2); sky.sun_intensity = 0.4
sky.altitude = 300; sky.air_density = 1.6; sky.dust_density = 3.0
w.node_tree.links.new(sky.outputs["Color"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = 0.16

sd = bpy.data.lights.new("SUN", 'SUN'); sd.energy = 4.0; sd.color = (1.0, 0.62, 0.32); sd.angle = math.radians(1.0)
sun = new_obj("SUN", sd, LIT)
SUN_ROT = math.radians(SUN_AZ)
sun.rotation_euler = (math.radians(-(90 - SUN_EL)), 0, -SUN_ROT)

# ---------------- marks & cameras ----------------
mark("SHEPHERD", (0, 0, 0), 0, SET)
camhint("WIDE", (1.0, -27.0, ground(1.0, -27) + 0.6), (0.0, 0.0, 2.6), 35, SET)
med = camhint("MED", (-0.5, -13.6, ground(-0.5, -13.6) + 0.75), (0.25, -3.0, 0.95), 85, SET)
med.data.dof.use_dof = True; med.data.dof.focus_distance = 5.0; med.data.dof.aperture_fstop = 1.8

scn.render.resolution_x, scn.render.resolution_y = 540, 960
scn.render.engine = 'CYCLES'; scn.cycles.samples = 8
scn.view_settings.view_transform = 'AgX'; scn.view_settings.look = 'AgX - Medium High Contrast'

if "--preview" in sys.argv:
    stand_in_figure((0, 0, 0), 0, col=SET)
    render_previews("hillside")
save(out_path())
