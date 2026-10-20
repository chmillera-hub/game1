import sys; sys.path.insert(0, "/home/user/game1/video/pipeline/sets"); from _common import *
import bpy, math, random
from mathutils import Vector
random.seed(7)
PREVIEW = "--preview" in sys.argv
scn = reset_scene()
SET = collection("SET_upper_room"); LIG = collection("LIGHTS_upper_room")

def proc_mat(name, c1, c2, rough=(0.6, 0.9), scale=4.0, bump=0.3, detail=6, voronoi=False):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; L = nt.links
    b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = detail; nz.inputs["Roughness"].default_value = 0.6
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].color = (*c1, 1); cr.color_ramp.elements[1].color = (*c2, 1)
    cr.color_ramp.elements[0].position = 0.3; cr.color_ramp.elements[1].position = 0.7
    L.new(nz.outputs["Fac"], cr.inputs["Fac"]); L.new(cr.outputs["Color"], b.inputs["Base Color"])
    mr = N.new("ShaderNodeMapRange")
    mr.inputs[3].default_value, mr.inputs[4].default_value = rough
    L.new(nz.outputs["Fac"], mr.inputs[0]); L.new(mr.outputs[0], b.inputs["Roughness"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump
    src = nz.outputs["Fac"]
    if voronoi:
        vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = scale * 3
        vo.feature = 'DISTANCE_TO_EDGE'; L.new(tc.outputs["Object"], vo.inputs["Vector"])
        mx = N.new("ShaderNodeMath"); mx.operation = 'ADD'
        L.new(nz.outputs["Fac"], mx.inputs[0]); L.new(vo.outputs["Distance"], mx.inputs[1]); src = mx.outputs[0]
    n2 = N.new("ShaderNodeTexNoise"); n2.inputs["Scale"].default_value = scale * 12
    L.new(tc.outputs["Object"], n2.inputs["Vector"])
    ad = N.new("ShaderNodeMath"); ad.operation = 'MULTIPLY_ADD'; ad.inputs[1].default_value = 0.3
    L.new(n2.outputs["Fac"], ad.inputs[0]); L.new(src, ad.inputs[2])
    L.new(ad.outputs[0], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m

def wood_mat(name, c1, c2):
    m = proc_mat(name, c1, c2, (0.55, 0.85), 3.0, 0.25)
    N = m.node_tree.nodes; L = m.node_tree.links
    nz = [n for n in N if n.bl_idname == "ShaderNodeTexNoise"][0]
    mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (0.15, 3.0, 3.0)
    L.new(N["Texture Coordinate"].outputs["Object"], mp.inputs["Vector"]); L.new(mp.outputs[0], nz.inputs["Vector"])
    nz.inputs["Distortion"].default_value = 3.0
    return m

M_PLASTER = proc_mat("M_plaster", (0.55, 0.45, 0.33), (0.72, 0.62, 0.48), (0.8, 0.95), 1.5, 0.5, voronoi=True)
M_FLOOR = proc_mat("M_floor", (0.20, 0.15, 0.10), (0.34, 0.27, 0.19), (0.75, 0.95), 2.0, 0.6, voronoi=True)
M_BEAM = wood_mat("M_beam", (0.07, 0.045, 0.025), (0.18, 0.12, 0.07))
M_TABLE = wood_mat("M_table", (0.12, 0.07, 0.035), (0.26, 0.16, 0.08))
M_CLAY = proc_mat("M_clay", (0.32, 0.14, 0.07), (0.50, 0.25, 0.13), (0.6, 0.85), 8.0, 0.2)
M_BREAD = proc_mat("M_bread", (0.45, 0.28, 0.12), (0.80, 0.62, 0.38), (0.7, 0.95), 10.0, 0.4)
M_RUG1 = proc_mat("M_rug_red", (0.25, 0.05, 0.03), (0.45, 0.18, 0.08), (0.9, 1.0), 30.0, 0.5)
M_RUG2 = proc_mat("M_rug_blue", (0.06, 0.08, 0.14), (0.30, 0.25, 0.18), (0.9, 1.0), 30.0, 0.5)
M_CUSH = proc_mat("M_cushion", (0.30, 0.22, 0.12), (0.48, 0.36, 0.20), (0.85, 1.0), 20.0, 0.3)
M_CUSH2 = proc_mat("M_cushion2", (0.22, 0.10, 0.06), (0.38, 0.20, 0.10), (0.85, 1.0), 20.0, 0.3)
M_WINE = principled("M_wine", (0.08, 0.005, 0.01), 0.05)
M_FLAME = bpy.data.materials.new("M_flame"); M_FLAME.use_nodes = True
fn = M_FLAME.node_tree.nodes; fn.remove(fn["Principled BSDF"])
em = fn.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 3
bb = fn.new("ShaderNodeBlackbody"); bb.inputs[0].default_value = 1900
M_FLAME.node_tree.links.new(bb.outputs[0], em.inputs[0])
M_FLAME.node_tree.links.new(em.outputs[0], fn["Material Output"].inputs[0])

def box(name, loc, dims, mat, bevel=0.0, col=SET):
    bpy.ops.mesh.primitive_cube_add(location=loc); o = bpy.context.object
    o.name = name; o.scale = (dims[0]/2, dims[1]/2, dims[2]/2)
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        md = o.modifiers.new("bev", 'BEVEL'); md.width = bevel; md.segments = 2
    o.data.materials.append(mat); link(o, col); return o

def smooth(o):
    for p in o.data.polygons: p.use_smooth = True

def lathe(name, prof, loc, mat, seg=24):
    import bmesh
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    rings = []
    for r, z in prof:
        rings.append([bm.verts.new((r*math.cos(2*math.pi*i/seg), r*math.sin(2*math.pi*i/seg), z)) for i in range(seg)])
    for a, b2 in zip(rings, rings[1:]):
        for i in range(seg):
            j = (i+1) % seg; bm.faces.new((a[i], a[j], b2[j], b2[i]))
    bm.faces.new(rings[0][::-1])
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); SET.objects.link(o); o.location = loc
    o.data.materials.append(mat); smooth(o); return o

# --- room shell: x -3..3, y -2.5..2.5, h 2.8
W, D, H, T = 6.0, 5.0, 2.8, 0.3
box("FLOOR", (0, 0, -0.05), (W+2*T, D+2*T, 0.1), M_FLOOR)
box("CEILING", (0, 0, H+0.05), (W+2*T, D+2*T, 0.1), M_BEAM)
box("WALL_PX", (W/2+T/2, 0, H/2), (T, D, H), M_PLASTER, 0.03)
box("WALL_PY", (0, D/2+T/2, H/2), (W+2*T, T, H), M_PLASTER, 0.03)
box("WALL_NY", (0, -D/2-T/2, H/2), (W+2*T, T, H), M_PLASTER, 0.03)
# -X wall with window opening y 0.6..1.2, z 1.9..2.4
wx = -W/2-T/2; y0, y1, z0, z1 = 0.6, 1.3, 1.85, 2.4
box("WALL_NX_A", (wx, (-D/2+y0)/2, H/2), (T, y0+D/2, H), M_PLASTER, 0.03)
box("WALL_NX_B", (wx, (y1+D/2)/2, H/2), (T, D/2-y1, H), M_PLASTER, 0.03)
box("WALL_NX_C", (wx, (y0+y1)/2, z0/2), (T, y1-y0, z0), M_PLASTER, 0.03)
box("WALL_NX_D", (wx, (y0+y1)/2, (z1+H)/2), (T, y1-y0, H-z1), M_PLASTER, 0.03)
box("WINDOW_BAR", (wx, (y0+y1)/2, (z0+z1)/2), (0.05, 0.05, z1-z0), M_BEAM, 0.01)
box("WINDOW_LINTEL", (wx+0.02, (y0+y1)/2, z1+0.06), (T+0.04, y1-y0+0.4, 0.12), M_BEAM, 0.01)
# beams across X
for i, y in enumerate([-1.9, -0.95, 0.0, 0.95, 1.9]):
    b = box(f"BEAM_{i+1}", (0, y+random.uniform(-.05,.05), H-0.11), (W, 0.2+random.uniform(-.02,.03), 0.22), M_BEAM, 0.02)
    b.rotation_euler = (random.uniform(-.01,.01), random.uniform(-.006,.006), random.uniform(-.01,.01))
# niche shelf + stone ledge on +Y wall for depth
box("SHELF", (1.6, D/2-0.12, 1.2), (1.0, 0.24, 0.06), M_BEAM, 0.01)
lathe("JAR_SHELF", [(0.0,0),(0.08,0.005),(0.11,0.08),(0.09,0.2),(0.05,0.24),(0.06,0.27),(0.0,0.27)], (1.4, D/2-0.12, 1.23), M_CLAY, 16)
lathe("JAR_FLOOR", [(0.0,0),(0.14,0.01),(0.22,0.25),(0.18,0.5),(0.09,0.58),(0.11,0.63),(0.0,0.63)], (2.5, 2.1, 0), M_CLAY, 20)

# rugs
for name, loc, dims, mat in [("RUG_1", (0, -0.45, 0.004), (3.4, 2.2, 0.008), M_RUG1), ("RUG_2", (-1.9, 1.3, 0.004), (1.4, 0.9, 0.008), M_RUG2)]:
    r = box(name, loc, dims, mat); r.rotation_euler.z = math.radians(random.uniform(-3, 3))

# table centered (0,-0.55), top at 0.38
TX, TY, TH = 0.0, -0.55, 0.38
box("TABLE_TOP", (TX, TY, TH-0.03), (2.2, 0.9, 0.06), M_TABLE, 0.012)
for sx in (-1, 1):
    for sy in (-1, 1):
        box("TABLE_LEG", (TX+sx*0.98, TY+sy*0.36, (TH-0.06)/2), (0.08, 0.08, TH-0.06), M_TABLE, 0.008)
box("TABLE_APRON_F", (TX, TY-0.4, TH-0.09), (2.0, 0.04, 0.06), M_TABLE, 0.005)
box("TABLE_APRON_B", (TX, TY+0.4, TH-0.09), (2.0, 0.04, 0.06), M_TABLE, 0.005)

# cushions under marks + extras
marks = {"JESUS": ((0, 0.05, 0), 0), "JOHN": ((-0.8, 0.0, 0), -10), "PETER": ((0.8, 0.0, 0), 10),
         "D4": ((-1.35, -1.15, 0), 150), "D5": ((1.35, -1.15, 0), 210)}
cush_pos = [v[0] for v in marks.values()] + [(-1.6, -0.2, 0), (1.6, -0.2, 0), (0, -1.35, 0)]
for i, p in enumerate(cush_pos):
    c = box(f"CUSHION_{i+1}", (p[0], p[1], 0.07), (0.62, 0.55, 0.14), M_CUSH if i % 2 == 0 else M_CUSH2, 0.05)
    c.modifiers["bev"].segments = 3; smooth(c); c.rotation_euler.z = math.radians(random.uniform(-12, 12))
for k, (p, r) in marks.items():
    mark(k, p, r, SET)

# table props, z = TH
def lamp(i, x, y, rz):
    body = lathe(f"OIL_LAMP_{i}", [(0.0,0),(0.035,0.002),(0.055,0.015),(0.05,0.03),(0.02,0.04),(0.012,0.042),(0.0,0.042)], (x, y, TH), M_CLAY, 20)
    body.scale = (1.5, 1, 1); body.rotation_euler.z = rz
    nx, ny = x + 0.07*math.cos(rz), y + 0.07*math.sin(rz)
    spout = box(f"OIL_LAMP_{i}_SPOUT", (x + 0.05*math.cos(rz), y + 0.05*math.sin(rz), TH+0.02), (0.06, 0.025, 0.02), M_CLAY, 0.008)
    spout.rotation_euler.z = rz
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.008, segments=12, ring_count=8, location=(nx, ny, TH+0.04))
    f = bpy.context.object; f.name = f"FLAME_{i}"; link(f, SET)
    for v in f.data.vertices:
        if v.co.z > 0: v.co.z *= 1 + 3.5 * (v.co.z / 0.008) ** 1.5; v.co.x *= 1 - 0.6*(v.co.z/0.036); v.co.y *= 1 - 0.6*(v.co.z/0.036)
    f.data.materials.append(M_FLAME); smooth(f)
    f.visible_shadow = False
    ld = bpy.data.lights.new(f"LAMP_{i}", 'POINT'); ld.energy = 5; ld.shadow_soft_size = 0.02
    ld.color = (1.0, 0.50, 0.16)
    lo = bpy.data.objects.new(f"LAMP_{i}", ld); LIG.objects.link(lo); lo.location = (nx, ny, TH+0.07)
    flick(lo.data, "energy", [-1], 5, 0.25, i); flick(f, "scale", [0, 1, 2], 1.0, 0.12, i)
    return f

def flick(idb, path, idxs, base, strength, seed):
    for ix in idxs:
        if ix < 0: idb.keyframe_insert(path, frame=1)
        else: idb.keyframe_insert(path, index=ix, frame=1)
    act = idb.animation_data.action
    try: fcs = act.fcurves
    except Exception:
        fcs = act.layers[0].strips[0].channelbag(act.slots[0]).fcurves
    for fc in fcs:
        if fc.data_path != path: continue
        md = fc.modifiers.new('NOISE'); md.scale = 6; md.strength = base * strength
        md.phase = seed * 13.7 + fc.array_index * 3.1; md.blend_in = 0

lamp(1, -0.55, -0.42, 0.4); lamp(2, 0.45, -0.38, 2.6); lamp(3, 0.05, -0.78, -1.5)

def bread(name, x, y, r=0.11, half=0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=r, depth=0.02, location=(x, y, TH+0.011))
    o = bpy.context.object; o.name = name; link(o, SET); o.scale.z = 1
    if half:
        import bmesh
        bm = bmesh.new(); bm.from_mesh(o.data)
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:]+bm.edges[:]+bm.faces[:], plane_co=(0.01*half,0,0), plane_no=(half,0,0), clear_inner=True)
        e = [e for e in bm.edges if e.is_boundary]; bmesh.ops.holes_fill(bm, edges=e)
        bm.to_mesh(o.data); bm.free()
    md = o.modifiers.new("bev", 'BEVEL'); md.width = 0.008; md.segments = 2
    o.data.materials.append(M_BREAD); smooth(o); return o
bread("BREAD_WHOLE", -0.2, -0.5)
bread("BREAD_WHOLE_2", 0.75, -0.62, 0.1)
ba = bread("PROP_BREAD_A", 0.12, -0.42, 0.11, -1); ba.location.x -= 0.0; ba.rotation_euler.z = 0.2
bb_ = bread("PROP_BREAD_B", 0.135, -0.44, 0.11, 1); bb_.rotation_euler.z = -0.15

cup = [(0.0,0),(0.03,0.0),(0.042,0.06),(0.045,0.085),(0.04,0.085),(0.036,0.01),(0.0,0.01)]
for i, (x, y) in enumerate([(-0.35, -0.25), (0.32, -0.22), (-0.85, -0.7), (0.9, -0.3), (-0.1, -0.85)]):
    lathe(f"PROP_CUP_{i+1}", cup, (x, y, TH), M_CLAY, 16)
lathe("PROP_JUG", [(0.0,0),(0.05,0),(0.08,0.06),(0.085,0.12),(0.05,0.2),(0.03,0.24),(0.04,0.27),(0.035,0.27),(0.025,0.24),(0.0,0.24)], (-0.95, -0.35, TH), M_CLAY, 20)
lathe("PROP_BOWL", [(0.0,0),(0.05,0),(0.11,0.04),(0.13,0.065),(0.122,0.065),(0.10,0.04),(0.0,0.012)], (0.6, -0.8, TH), M_CLAY, 24)
w = lathe("WINE_IN_CUP", [(0.0,0.06),(0.04,0.06),(0.0,0.0605)], (-0.35, -0.25, TH), M_WINE, 16)

# lights
moon = bpy.data.lights.new("MOON", 'AREA'); moon.energy = 140; moon.size = 0.6; moon.color = (0.55, 0.68, 1.0)
mo = bpy.data.objects.new("MOON", moon); LIG.objects.link(mo); mo.location = (-4.2, 1.0, 3.0); look_at(mo, (-0.5, 0.2, 0.0))
fd = bpy.data.lights.new("FILL_COOL", 'AREA'); fd.energy = 6; fd.size = 3; fd.color = (0.5, 0.6, 0.9)
fo = bpy.data.objects.new("FILL_COOL", fd); LIG.objects.link(fo); fo.location = (0, -2.2, 2.5); look_at(fo, (0, 0.5, 0.8))
wd = bpy.data.lights.new("BOUNCE_WARM", 'POINT'); wd.energy = 10; wd.color = (1.0, 0.55, 0.25); wd.shadow_soft_size = 0.8
wo = bpy.data.objects.new("BOUNCE_WARM", wd); LIG.objects.link(wo); wo.location = (0, -0.5, 1.6)

wr = bpy.data.worlds.new("W_upper_room"); wr.use_nodes = True
bg = wr.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.02, 0.03, 0.06, 1); bg.inputs[1].default_value = 0.4
scn.world = wr

# camera hints
camhint("CU_JESUS", (0.05, -2.3, 0.95), (0, 0.05, 0.85), 85, SET)
camhint("TWO_SHOT", (-0.4, -2.25, 1.0), (-0.4, 0.0, 0.75), 50, SET)
c = camhint("LAMP_CU", (-0.66, -0.85, 0.5), (-0.48, -0.42, 0.42), 100, SET)
c.data.dof.use_dof = True; c.data.dof.focus_object = bpy.data.objects["FLAME_1"]; c.data.dof.aperture_fstop = 2.0
camhint("BREAD_CU", (0.15, -0.95, 1.3), (0.15, -0.42, TH), 50, SET)

scn.render.engine = 'CYCLES'; scn.cycles.device = 'CPU'; scn.cycles.samples = 8
scn.render.resolution_x, scn.render.resolution_y = 540, 960
scn.view_settings.view_transform = 'AgX'; scn.view_settings.look = 'AgX - Medium High Contrast'
scn.frame_start, scn.frame_end = 1, 120

if PREVIEW:
    for k, (p, r) in marks.items():
        stand_in_figure(p, r, height=1.05, col=SET)
    render_previews("upper_room")
save(out_path())
print("FACES", sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH'))
