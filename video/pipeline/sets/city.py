import sys; sys.path.insert(0, "/home/user/game1/video/pipeline/sets"); from _common import *
import bpy, bmesh, random, math
from mathutils import Vector
random.seed(17)
scn = reset_scene()
SET = collection("SET_city"); LIT = collection("LIGHTS_city")
PREVIEW = "--preview" in sys.argv

def nodes(m): return m.node_tree.nodes, m.node_tree.links

def box(name, size, loc, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        b = o.modifiers.new("bev", 'BEVEL'); b.width = bevel; b.segments = 2
    o.data.materials.append(mat); link(o, SET); return o

def plane(name, w, h, loc, mat, col=SET):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    vs = [bm.verts.new((x, 0, z)) for x, z in ((-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2))]
    bm.faces.new(vs); bm.to_mesh(me); bm.free()
    me.uv_layers.new(); 
    for i, l in enumerate(me.loops): me.uv_layers[0].data[i].uv = [(0,0),(1,0),(1,1),(0,1)][i]
    o = bpy.data.objects.new(name, me); o.location = loc; col.objects.link(o)
    me.materials.append(mat); return o

# ---------- materials
def brick_mat(name, c1, c2):
    m = principled(name); N, L = nodes(m); b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); br = N.new("ShaderNodeTexBrick")
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Brick Width"].default_value = 0.25; br.inputs["Row Height"].default_value = 0.075
    br.inputs["Mortar Size"].default_value = 0.008
    br.inputs["Color1"].default_value = (*c1, 1); br.inputs["Color2"].default_value = (*c2, 1)
    br.inputs["Mortar"].default_value = (0.25, 0.24, 0.22, 1)
    mp = N.new("ShaderNodeMapping"); L.new(tc.outputs["Object"], mp.inputs["Vector"])
    mp.inputs["Rotation"].default_value = (math.radians(90), 0, 0)
    L.new(mp.outputs["Vector"], br.inputs["Vector"])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.6; nz.inputs["Detail"].default_value = 3
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
    mx.inputs["Factor"].default_value = 0.5
    L.new(br.outputs["Color"], mx.inputs["A"]); L.new(nz.outputs["Color"], mx.inputs["B"])
    L.new(mx.outputs["Result"], b.inputs["Base Color"])
    rr = N.new("ShaderNodeMapRange"); rr.inputs["To Min"].default_value = 0.65; rr.inputs["To Max"].default_value = 0.95
    L.new(nz.outputs["Fac"], rr.inputs["Value"]); L.new(rr.outputs["Result"], b.inputs["Roughness"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.5; bp.invert = True
    L.new(br.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m

def concrete_mat(name, c):
    m = principled(name, c, 0.85); N, L = nodes(m); b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3; nz.inputs["Detail"].default_value = 3
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (*[x*0.6 for x in c], 1)
    cr.color_ramp.elements[1].color = (*c, 1)
    L.new(nz.outputs["Fac"], cr.inputs["Fac"]); L.new(cr.outputs["Color"], b.inputs["Base Color"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.15
    L.new(nz.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m

def window_mat(name, col, strength, glow=True):
    """Lit interior: vertical curtain gradient + soft lamp hotspot, emission."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N, L = nodes(m); N.clear()
    out = N.new("ShaderNodeOutputMaterial"); em = N.new("ShaderNodeEmission")
    tc = N.new("ShaderNodeTexCoord"); sx = N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["UV"], sx.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB")   # curtain folds in X
    wv = N.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.bands_direction = 'X'
    wv.inputs["Scale"].default_value = 4; wv.inputs["Distortion"].default_value = 1.5
    L.new(tc.outputs["UV"], wv.inputs["Vector"])
    cr.color_ramp.elements[0].color = (0.55, 0.55, 0.55, 1); cr.color_ramp.elements[1].color = (1, 1, 1, 1)
    L.new(wv.outputs["Fac"], cr.inputs["Fac"])
    gr = N.new("ShaderNodeMapRange"); gr.inputs["To Min"].default_value = 1.0; gr.inputs["To Max"].default_value = 0.35
    L.new(sx.outputs["Y"], gr.inputs["Value"])   # brighter low (lamp), darker top
    mul = N.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'
    L.new(cr.outputs["Color"], mul.inputs[0]); L.new(gr.outputs["Result"], mul.inputs[1])
    tint = N.new("ShaderNodeMix"); tint.data_type = 'RGBA'; tint.blend_type = 'MULTIPLY'
    tint.inputs["Factor"].default_value = 1; tint.inputs["A"].default_value = (*col, 1)
    L.new(mul.outputs["Value"], tint.inputs["B"])
    L.new(tint.outputs["Result"], em.inputs["Color"])
    em.inputs["Strength"].default_value = strength
    L.new(em.outputs["Emission"], out.inputs["Surface"])
    m["_em"] = em.name
    m.cycles.emission_sampling = 'NONE'  # perf: windows only seen directly
    return m

glass_dark = principled("M_city_glass_dark", (0.01, 0.012, 0.016), 0.08)
gN, gL = nodes(glass_dark)
gnz = gN.new("ShaderNodeTexNoise"); gnz.inputs["Scale"].default_value = 8
gr = gN.new("ShaderNodeMapRange"); gr.inputs["To Min"].default_value = 0.03; gr.inputs["To Max"].default_value = 0.2
gL.new(gnz.outputs["Fac"], gr.inputs["Value"]); gL.new(gr.outputs["Result"], gN["Principled BSDF"].inputs["Roughness"])
frame_m = principled("M_city_frame", (0.12, 0.11, 0.1), 0.6)
sil_m = principled("M_city_silhouette", (0.005, 0.005, 0.006), 0.9)
lamp_m = principled("M_city_lamp_metal", (0.03, 0.03, 0.03), 0.4, 1.0)
bulb_m = bpy.data.materials.new("M_city_lamp_bulb"); bulb_m.cycles.emission_sampling = 'NONE'; bulb_m.use_nodes = True
bb = bulb_m.node_tree.nodes["Principled BSDF"]
bb.inputs["Emission Color"].default_value = (1.0, 0.62, 0.3, 1); bb.inputs["Emission Strength"].default_value = 40
lit_mats = [window_mat("M_city_win_warm", (1.0, 0.55, 0.22), 2.2),
            window_mat("M_city_win_warm2", (1.0, 0.72, 0.42), 1.8),
            window_mat("M_city_win_cool", (0.55, 0.7, 1.0), 1.3),
            window_mat("M_city_win_tv", (0.4, 0.55, 0.9), 0.8)]

# ---------- buildings (facades at y=FY, street toward -Y)
FY = 16.0
bldgs = [  # x0, width, floors, material
    (-12.5, 8.5, 6, brick_mat("M_city_brick_red", (0.28, 0.1, 0.06), (0.2, 0.08, 0.05)), 4),
    (-4.0, 8.0, 8, concrete_mat("M_city_concrete", (0.32, 0.31, 0.29)), 4),
    (4.0, 9.0, 7, brick_mat("M_city_brick_brown", (0.2, 0.13, 0.09), (0.15, 0.1, 0.07)), 4),
]
FH = 3.0; WW, WH = 1.2, 1.6
wins = []
for i, (x0, w, fl, mat, cols) in enumerate(bldgs):
    H = fl * FH + 1.0
    box(f"BLDG_{i}", (w, 10, H), (x0 + w/2, FY + 5, H/2), mat)
    box(f"BLDG_{i}_cornice", (w + 0.3, 0.35, 0.4), (x0 + w/2, FY - 0.15, H), frame_m, 0.03)
    for f in range(1, fl):  # ground floor = shopfront band, no windows
        for c in range(cols):
            x = x0 + w * (c + 0.5) / cols
            z = f * FH + 1.5
            wins.append((i, f, c, x, z))
    box(f"BLDG_{i}_base", (w, 0.2, 2.6), (x0 + w/2, FY - 0.1, 1.3), frame_m, 0.02)

# special window: building 1 (concrete), floor 4, column 1
special = next(wv for wv in wins if wv[0] == 1 and wv[1] == 4 and wv[2] == 1)
pool = [wv for wv in wins if wv is not special]
lit = set(random.sample(range(len(pool)), int(len(pool) * 0.3)))
sil_idx = set(random.sample(sorted(lit), 8))

def silhouette(name, w_sh=0.5, h=0.75, sitting=False):
    bm = bmesh.new()
    sh = h * 0.55
    pts = [(-w_sh/2, 0), (w_sh/2, 0), (w_sh/2*0.9, sh*0.7), (w_sh*0.3, sh), (w_sh*0.1, sh*1.02),
           (-w_sh*0.1, sh*1.02), (-w_sh*0.3, sh), (-w_sh/2*0.9, sh*0.7)]
    bm.faces.new([bm.verts.new((x, 0, z)) for x, z in pts])
    r = h * 0.2; cz = sh + r * 1.05
    bm.faces.new([bm.verts.new((r*0.85*math.cos(a), 0, cz + r*math.sin(a)))
                  for a in [k * 2*math.pi/16 for k in range(16)]])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.materials.append(sil_m)
    o = bpy.data.objects.new(name, me); SET.objects.link(o); return o

for k, (i, f, c, x, z) in enumerate(pool):
    y = FY - 0.03
    plane(f"WIN_{i}_{f}_{c}_frame", WW + 0.16, WH + 0.16, (x, y + 0.005, z), frame_m)
    box(f"WIN_{i}_{f}_{c}_sill", (WW + 0.3, 0.18, 0.08), (x, FY - 0.09, z - WH/2 - 0.1), frame_m, 0.01)
    if k in lit:
        p = plane(f"WIN_{i}_{f}_{c}", WW, WH, (x, y - 0.002, z), random.choices(lit_mats, weights=[4, 3, 1.5, 1])[0])
        if k in sil_idx:
            s = silhouette(f"SILH_{i}_{f}_{c}", sitting=random.random() < 0.5)
            s.location = (x + random.uniform(-0.3, 0.3), y - 0.01, z - WH/2 + random.choice([0.0, 0.3]))
    else:
        plane(f"WIN_{i}_{f}_{c}", WW, WH, (x, y - 0.002, z), glass_dark)

# special window
_, _, _, sx_, sz_ = special
sp_m = window_mat("M_city_win_special", (1.0, 0.62, 0.3), 0.0)
plane("WIN_SPECIAL_frame", WW + 0.16, WH + 0.16, (sx_, FY - 0.025, sz_), frame_m)
box("WIN_SPECIAL_sill", (WW + 0.3, 0.18, 0.08), (sx_, FY - 0.09, sz_ - WH/2 - 0.1), frame_m, 0.01)
win_sp = plane("WIN_SPECIAL", WW, WH, (sx_, FY - 0.032, sz_), sp_m)
ctrl = bpy.data.objects.new("CITY_CTRL", None); SET.objects.link(ctrl)
ctrl.location = (sx_, FY - 1.0, sz_)
ctrl["special_on"] = 0.0
ctrl.id_properties_ui("special_on").update(min=0.0, max=1.0, soft_min=0.0, soft_max=1.0)
em = sp_m.node_tree.nodes[sp_m["_em"]]
fc = em.inputs["Strength"].driver_add("default_value"); d = fc.driver; d.type = 'SCRIPTED'
v = d.variables.new(); v.name = "on"; v.type = 'SINGLE_PROP'
v.targets[0].id_type = 'OBJECT'; v.targets[0].id = ctrl; v.targets[0].data_path = '["special_on"]'
d.expression = "on*2.4"
for fr, val in ((1, 0.0), (24, 0.0), (36, 1.0)):
    ctrl["special_on"] = val; ctrl.keyframe_insert('["special_on"]', frame=fr)
sils = []
for nm, side in (("SIL_A", -1), ("SIL_B", 1)):
    s = silhouette(nm, w_sh=0.42, h=0.8)
    s.location = (sx_ + side * 0.38, FY - 0.04, sz_ - WH/2)
    s.keyframe_insert("location", index=0, frame=40)
    s.location.x = sx_ + side * 0.17
    s.keyframe_insert("location", index=0, frame=110)
    sils.append(s)
scn.frame_start, scn.frame_end = 1, 120

# ---------- street, sidewalks, lamps
pave = principled("M_city_asphalt_wet", (0.02, 0.02, 0.022), 0.2); N, L = nodes(pave); b = N["Principled BSDF"]
tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.4
nz.inputs["Detail"].default_value = 2; L.new(tc.outputs["Object"], nz.inputs["Vector"])
rr = N.new("ShaderNodeMapRange"); rr.inputs["From Min"].default_value = 0.45; rr.inputs["From Max"].default_value = 0.6
rr.inputs["To Min"].default_value = 0.04; rr.inputs["To Max"].default_value = 0.45   # puddles
L.new(nz.outputs["Fac"], rr.inputs["Value"]); L.new(rr.outputs["Result"], b.inputs["Roughness"])
vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 60
L.new(tc.outputs["Object"], vo.inputs["Vector"])
bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.08
L.new(vo.outputs["Distance"], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
box("STREET", (90, 50, 0.1), (0, -9, -0.05), pave)
curb = concrete_mat("M_city_sidewalk", (0.09, 0.09, 0.09))
box("SIDEWALK_far", (80, 3.5, 0.15), (0, FY - 1.75, 0.075), curb, 0.02)
box("SIDEWALK_near", (80, 3.0, 0.15), (0, -15, 0.075), curb, 0.02)
for k, lx in enumerate((-7.0, 1.5, 9.5)):
    ly = FY - 3.1
    box(f"LAMP_{k}_pole", (0.12, 0.12, 5.5), (lx, ly, 2.75), lamp_m, 0.02)
    box(f"LAMP_{k}_arm", (0.08, 0.9, 0.08), (lx, ly - 0.4, 5.45), lamp_m, 0.01)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.18, location=(lx, ly - 0.8, 5.3), segments=16, ring_count=8)
    g = bpy.context.object; g.name = f"LAMP_{k}_globe"; g.data.materials.append(bulb_m); link(g, SET)
    ld = bpy.data.lights.new(f"L_city_lamp_{k}", 'POINT'); ld.energy = 400; ld.color = (1, 0.65, 0.35)
    ld.shadow_soft_size = 0.2
    lo = bpy.data.objects.new(f"L_city_lamp_{k}", ld); lo.location = (lx, ly - 0.8, 5.05); LIT.objects.link(lo)

# moon/sky fill
sd = bpy.data.lights.new("L_city_skyfill", 'SUN'); sd.energy = 0.03; sd.color = (0.5, 0.6, 1.0); sd.angle = 0.3
so = bpy.data.objects.new("L_city_skyfill", sd); so.rotation_euler = (math.radians(60), 0, math.radians(200)); LIT.objects.link(so)
# soft glow out of the special window into the street side (driven too)
ad = bpy.data.lights.new("L_city_special_spill", 'AREA'); ad.energy = 0; ad.size = 1.2; ad.color = (1, 0.65, 0.35)
ao = bpy.data.objects.new("L_city_special_spill", ad); ao.location = (sx_, FY - 0.3, sz_)
ao.rotation_euler = (math.radians(-90), 0, 0); LIT.objects.link(ao)
fc = ad.driver_add("energy"); d = fc.driver; d.type = 'SCRIPTED'
v = d.variables.new(); v.name = "on"; v.type = 'SINGLE_PROP'
v.targets[0].id_type = 'OBJECT'; v.targets[0].id = ctrl; v.targets[0].data_path = '["special_on"]'
d.expression = "on*40.0"

# ---------- world: dark blue with city-glow near horizon
W = bpy.data.worlds.new("W_city"); W.use_nodes = True; scn.world = W
N, L = W.node_tree.nodes, W.node_tree.links; bg = N["Background"]
tc = N.new("ShaderNodeTexCoord"); sxyz = N.new("ShaderNodeSeparateXYZ")
L.new(tc.outputs["Generated"], sxyz.inputs["Vector"])
cr = N.new("ShaderNodeValToRGB")
cr.color_ramp.elements[0].position = 0.0; cr.color_ramp.elements[0].color = (0.09, 0.06, 0.06, 1)
cr.color_ramp.elements[1].position = 0.45; cr.color_ramp.elements[1].color = (0.004, 0.007, 0.02, 1)
e = cr.color_ramp.elements.new(0.08); e.color = (0.05, 0.04, 0.06, 1)
L.new(sxyz.outputs["Z"], cr.inputs["Fac"]); L.new(cr.outputs["Color"], bg.inputs["Color"])
bg.inputs["Strength"].default_value = 1.0

# ---------- marks & cameras
mark("WATCHER", (2.2, -15.0, 0.15), 180, SET)   # on near sidewalk, facing the facades (+Y)
camhint("WIDE", (0.5, -21.0, 1.6), (0.0, FY, 10.5), 35, SET)
camhint("MED", (sx_ + 0.6, -14.0, 1.6), (sx_, FY, sz_), 85, SET)

if PREVIEW:
    stand_in_figure((2.2, -15.0, 0.15), 180, col=SET)
    scn.frame_set(100); render_previews("city"); scn.frame_set(1)
save(out_path())
