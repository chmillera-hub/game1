import sys; sys.path.insert(0, "/home/user/game1/video/pipeline/sets"); from _common import *
import bpy, math
from mathutils import Vector

N = "sister_kitchen"
scn = reset_scene()
SET = collection(f"SET_{N}"); LIG = collection(f"LIGHTS_{N}")

def mat(name, color, rough=0.5, metal=0.0, var=0.1, scale=8.0, bump=0.05, rough_var=0.15, vein=None):
    m = principled(name, color, rough, metal)
    nt = m.node_tree; nd = nt.nodes; L = nt.links
    b = nd["Principled BSDF"]
    tc = nd.new("ShaderNodeTexCoord")
    nz = nd.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale; nz.inputs["Detail"].default_value = 6
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    cr = nd.new("ShaderNodeMix"); cr.data_type = 'RGBA'
    cr.inputs["Factor"].default_value = 1.0
    c0 = tuple(max(0, c * (1 - var)) for c in color); c1 = tuple(min(1, c * (1 + var)) for c in color)
    ramp = nd.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*c0, 1); ramp.color_ramp.elements[1].color = (*c1, 1)
    L.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    col_out = ramp.outputs["Color"]
    if vein:
        w = nd.new("ShaderNodeTexWave"); w.inputs["Scale"].default_value = 1.2
        w.inputs["Distortion"].default_value = 9; w.inputs["Detail"].default_value = 6
        L.new(tc.outputs["Object"], w.inputs["Vector"])
        vr = nd.new("ShaderNodeValToRGB"); vr.color_ramp.elements[0].position = 0.0
        vr.color_ramp.elements[1].position = 0.08
        vr.color_ramp.elements[0].color = (1,1,1,1); vr.color_ramp.elements[1].color = (0,0,0,1)
        L.new(w.outputs["Fac"], vr.inputs["Fac"])
        mx = nd.new("ShaderNodeMix"); mx.data_type = 'RGBA'
        L.new(vr.outputs["Color"], mx.inputs["Factor"])
        L.new(col_out, mx.inputs[6]); mx.inputs[7].default_value = (*vein, 1)
        col_out = mx.outputs[2]
    L.new(col_out, b.inputs["Base Color"])
    mr = nd.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = max(0.02, rough - rough_var); mr.inputs["To Max"].default_value = min(1, rough + rough_var)
    nz2 = nd.new("ShaderNodeTexNoise"); nz2.inputs["Scale"].default_value = scale * 3
    L.new(tc.outputs["Object"], nz2.inputs["Vector"])
    L.new(nz2.outputs["Fac"], mr.inputs["Value"]); L.new(mr.outputs["Result"], b.inputs["Roughness"])
    if bump:
        bp = nd.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = 0.002
        L.new(nz2.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m

M = dict(
    wall=mat("M_wall", (0.62, 0.58, 0.52), 0.85, var=0.05, scale=3, bump=0.03),
    floor=mat("M_floor_wood", (0.30, 0.19, 0.11), 0.45, var=0.25, scale=2, bump=0.08),
    sage=mat("M_cabinet_sage", (0.30, 0.38, 0.30), 0.6, var=0.04, scale=5, bump=0.02),
    stone=mat("M_counter_stone", (0.78, 0.76, 0.72), 0.22, var=0.06, scale=4, bump=0.01, vein=(0.42, 0.40, 0.38)),
    brass=mat("M_brass", (0.85, 0.62, 0.30), 0.3, 1.0, var=0.08, scale=20, bump=0.02),
    steel=mat("M_steel", (0.75, 0.75, 0.76), 0.25, 1.0, var=0.03, scale=30, bump=0.01),
    fridge=mat("M_fridge", (0.80, 0.80, 0.79), 0.3, 0.0, var=0.02, scale=10, bump=0.005),
    ceramic=mat("M_ceramic", (0.88, 0.87, 0.83), 0.12, var=0.03, scale=10, bump=0.0),
    kettle=mat("M_kettle", (0.12, 0.13, 0.14), 0.35, 0.6, var=0.05, scale=15, bump=0.01),
    tile=mat("M_backsplash", (0.86, 0.85, 0.80), 0.18, var=0.05, scale=12, bump=0.04),
    ceil=mat("M_ceiling", (0.7, 0.68, 0.64), 0.9, var=0.02, scale=2, bump=0.0),
    frame=mat("M_window_frame", (0.85, 0.84, 0.80), 0.5, var=0.02),
)
# night view: dark blue emission + glossy reflection
m = bpy.data.materials.new("M_window_night"); m.use_nodes = True
nt = m.node_tree; nd = nt.nodes; nd.clear()
out = nd.new("ShaderNodeOutputMaterial"); em = nd.new("ShaderNodeEmission")
tc = nd.new("ShaderNodeTexCoord"); nz = nd.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3
rp = nd.new("ShaderNodeValToRGB")
rp.color_ramp.elements[0].color = (0.005, 0.01, 0.035, 1); rp.color_ramp.elements[1].color = (0.02, 0.04, 0.10, 1)
nt.links.new(tc.outputs["Generated"], nz.inputs["Vector"]); nt.links.new(nz.outputs["Fac"], rp.inputs["Fac"])
nt.links.new(rp.outputs["Color"], em.inputs["Color"]); em.inputs["Strength"].default_value = 0.35
gl = nd.new("ShaderNodeBsdfGlossy"); gl.inputs["Roughness"].default_value = 0.03
fr = nd.new("ShaderNodeFresnel"); fr.inputs["IOR"].default_value = 1.5
ad = nd.new("ShaderNodeMixShader")
nt.links.new(fr.outputs[0], ad.inputs[0]); nt.links.new(em.outputs[0], ad.inputs[1]); nt.links.new(gl.outputs[0], ad.inputs[2])
nt.links.new(ad.outputs[0], out.inputs[0]); M["night"] = m

def box(name, size, loc, material, bevel=0.006, rot_z=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object; o.name = name; o.scale = size; o.rotation_euler.z = math.radians(rot_z)
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        bv = o.modifiers.new("bevel", 'BEVEL'); bv.width = bevel; bv.segments = 2; bv.limit_method = 'ANGLE'
    o.data.materials.append(material); link(o, SET)
    for p in o.data.polygons: p.use_smooth = True
    o.data.shade_auto_smooth if hasattr(o.data, "shade_auto_smooth") else None
    return o

def cyl(name, r, d, loc, material, verts=32, rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d, vertices=verts, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.data.materials.append(material); link(o, SET)
    bpy.ops.object.shade_smooth_by_angle(); return o

# room: back wall y=1.30, x -2.2..2.2
WY = 1.30; H = 2.6
box("floor", (4.4, 5.0, 0.02), (0, -1.2, -0.01), M["floor"], 0)
box("ceiling", (4.4, 5.0, 0.02), (0, -1.2, H + 0.01), M["ceil"], 0)
box("wall_L", (0.1, 5.0, H), (-2.25, -1.2, H / 2), M["wall"], 0)
box("wall_R", (0.1, 5.0, H), (2.25, -1.2, H / 2), M["wall"], 0)
# back wall with window hole at x -0.95..-0.05, z 1.15..2.05
WX0, WX1, WZ0, WZ1 = -1.0, -0.1, 1.12, 2.02
box("wall_back_L", (WX0 + 2.2, 0.1, H), ((WX0 - 2.2) / 2, WY + 0.05, H / 2), M["wall"], 0)
box("wall_back_R", (2.2 - WX1, 0.1, H), ((WX1 + 2.2) / 2, WY + 0.05, H / 2), M["wall"], 0)
box("wall_back_low", (WX1 - WX0, 0.1, WZ0), ((WX0 + WX1) / 2, WY + 0.05, WZ0 / 2), M["wall"], 0)
box("wall_back_top", (WX1 - WX0, 0.1, H - WZ1), ((WX0 + WX1) / 2, WY + 0.05, (H + WZ1) / 2), M["wall"], 0)
wx = (WX0 + WX1) / 2; ww = WX1 - WX0; wh = WZ1 - WZ0
box("window_glass", (ww, 0.01, wh), (wx, WY + 0.08, (WZ0 + WZ1) / 2), M["night"], 0)
for i, (sx, sz, lx, lz) in enumerate([(ww, 0.05, wx, WZ0 + 0.025), (ww, 0.05, wx, WZ1 - 0.025),
                                      (0.05, wh, WX0 + 0.025, (WZ0+WZ1)/2), (0.05, wh, WX1 - 0.025, (WZ0+WZ1)/2),
                                      (0.03, wh, wx, (WZ0+WZ1)/2), (ww, 0.03, wx, (WZ0+WZ1)/2 + 0.1)]):
    box(f"window_frame_{i}", (sx, 0.06, sz), (lx, WY + 0.06, lz), M["frame"], 0.004)
box("window_sill", (ww + 0.1, 0.12, 0.03), (wx, WY - 0.02, WZ0 - 0.015), M["stone"], 0.004)

# base cabinets x -2.2..1.0, depth 0.6
CD = 0.6; CF = WY - CD; CH = 0.88
BX0, BX1 = -2.2, 1.0
box("base_cabinets_carcass", (BX1 - BX0, CD - 0.02, CH - 0.1), ((BX0 + BX1) / 2, WY - CD / 2 + 0.01, 0.1 + (CH - 0.1) / 2), M["sage"], 0.003)
box("base_kick", (BX1 - BX0, 0.5, 0.1), ((BX0 + BX1) / 2, WY - 0.3, 0.05), M["kettle"], 0)
nd_ = 6; dw = (BX1 - BX0) / nd_
for i in range(nd_):
    x = BX0 + dw * (i + 0.5)
    box(f"base_door_{i}", (dw - 0.006, 0.02, CH - 0.12), (x, CF - 0.01, 0.1 + (CH - 0.1) / 2), M["sage"], 0.004)
    hx = x + (dw / 2 - 0.06) * (1 if i % 2 else -1)
    cyl(f"handle_base_{i}", 0.006, 0.16, (hx, CF - 0.04, CH - 0.15), M["brass"], 12)
    for dz in (-0.07, 0.07):
        cyl(f"handle_post_{i}", 0.004, 0.025, (hx, CF - 0.028, CH - 0.15 + dz), M["brass"], 8, (math.pi/2, 0, 0))
# countertop with sink cut (sink basin as separate box, top split)
TT = 0.04; TZ = CH + TT / 2
SX0, SX1 = wx - 0.3, wx + 0.3
top_d = CD + 0.03; ty = WY - top_d / 2
box("counter_L", (SX0 - BX0, top_d, TT), ((SX0 + BX0) / 2, ty, TZ), M["stone"], 0.006)
box("counter_R", (BX1 - SX1, top_d, TT), ((SX1 + BX1) / 2, ty, TZ), M["stone"], 0.006)
box("counter_front_strip", (SX1 - SX0, 0.09, TT), (wx, CF - 0.03 + 0.045, TZ), M["stone"], 0.006)
box("counter_back_strip", (SX1 - SX0, 0.07, TT), (wx, WY - 0.035, TZ), M["stone"], 0.006)
box("sink_basin_floor", (0.6, 0.47, 0.01), (wx, WY - 0.07 - 0.235, CH - 0.2), M["steel"], 0)
for i, (s, l) in enumerate([((0.6, 0.01, 0.2), (wx, CF + 0.06, CH - 0.1)), ((0.6, 0.01, 0.2), (wx, WY - 0.07, CH - 0.1)),
                            ((0.01, 0.47, 0.2), (SX0, WY - 0.305, CH - 0.1)), ((0.01, 0.47, 0.2), (SX1, WY - 0.305, CH - 0.1))]):
    box(f"sink_wall_{i}", s, l, M["steel"], 0)
# faucet
cyl("faucet_base", 0.025, 0.06, (wx, WY - 0.05, CH + TT + 0.03), M["steel"])
cyl("faucet_riser", 0.012, 0.3, (wx, WY - 0.05, CH + TT + 0.2), M["steel"], 16)
cyl("faucet_spout", 0.011, 0.2, (wx, WY - 0.15, CH + TT + 0.35), M["steel"], 16, (math.pi/2, 0, 0))
# backsplash
box("backsplash", (BX1 - BX0, 0.012, 0.5), ((BX0 + BX1) / 2, WY - 0.006, CH + TT + 0.25), M["tile"], 0.002)
# wall cabinets left and right of window
UZ0, UZ1 = 1.45, 2.2; UD = 0.34
for side, (x0, x1) in (("L", (-2.2, WX0 - 0.12)), ("R", (WX1 + 0.12, 1.0))):
    box(f"wall_cab_{side}", (x1 - x0, UD - 0.02, UZ1 - UZ0), ((x0 + x1) / 2, WY - UD / 2 + 0.01, (UZ0 + UZ1) / 2), M["sage"], 0.003)
    n = max(1, round((x1 - x0) / 0.45)); w = (x1 - x0) / n
    for i in range(n):
        x = x0 + w * (i + 0.5)
        box(f"wall_door_{side}{i}", (w - 0.006, 0.02, UZ1 - UZ0 - 0.006), (x, WY - UD - 0.01, (UZ0 + UZ1) / 2), M["sage"], 0.004)
        hx = x + (w / 2 - 0.05) * (1 if i % 2 else -1)
        cyl(f"handle_wall_{side}{i}", 0.006, 0.12, (hx, WY - UD - 0.04, UZ0 + 0.12), M["brass"], 12)
# fridge
box("fridge", (0.75, 0.68, 2.0), (1.5, WY - 0.36, 1.0), M["fridge"], 0.02)
box("fridge_gap", (0.74, 0.005, 0.006), (1.5, WY - 0.7, 1.3), M["kettle"], 0)
cyl("fridge_handle_top", 0.012, 0.5, (1.18, WY - 0.75, 1.65), M["steel"], 12)
cyl("fridge_handle_bot", 0.012, 0.5, (1.18, WY - 0.75, 0.95), M["steel"], 12)
box("tall_panel", (0.06, 0.62, 2.2), (1.09, WY - 0.31, 1.1), M["sage"], 0.003)
# kettle (lathe-like: stacked cylinders + spout)
KX, KY, KZ = 0.55, WY - 0.3, CH + TT
cyl("PROP_KETTLE", 0.09, 0.18, (KX, KY, KZ + 0.09), M["kettle"])
k = bpy.data.objects["PROP_KETTLE"]
cyl("kettle_lid", 0.06, 0.02, (KX, KY, KZ + 0.19), M["kettle"]).parent = k
cyl("kettle_knob", 0.015, 0.03, (KX, KY, KZ + 0.21), M["brass"], 12).parent = k
cyl("kettle_spout", 0.015, 0.12, (KX - 0.12, KY, KZ + 0.12), M["kettle"], 12, (0, math.radians(-50), 0)).parent = k
bpy.ops.mesh.primitive_torus_add(major_radius=0.07, minor_radius=0.012, location=(KX + 0.09, KY, KZ + 0.14), rotation=(math.pi/2, 0, 0))
h = bpy.context.object; h.name = "kettle_handle"; h.data.materials.append(M["kettle"]); link(h, SET); h.parent = k
for o in [o for o in SET.objects if o.parent == k]:
    o.matrix_parent_inverse = k.matrix_world.inverted()
# dishes: stack of plates + bowl + mugs
for i in range(4):
    cyl(f"plate_{i}", 0.12, 0.012, (-1.5, WY - 0.3, CH + TT + 0.006 + i * 0.014), M["ceramic"], 40)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.09, location=(-1.2, WY - 0.25, CH + TT + 0.09), segments=32, ring_count=16)
bw = bpy.context.object; bw.name = "bowl"; bw.scale.z = 0.6; bw.data.materials.append(M["ceramic"]); link(bw, SET)
bpy.ops.object.shade_smooth()
cyl("PROP_MUG", 0.04, 0.095, (0.25, WY - 0.45, CH + TT + 0.048), M["ceramic"])
cyl("mug_2", 0.04, 0.095, (-1.75, WY - 0.2, CH + TT + 0.048), M["sage"])
box("cutting_board", (0.35, 0.02, 0.25), (-1.95, WY - 0.03, CH + TT + 0.125), M["floor"], 0.005)

# pendant
PZ = 1.95; PY = 0.75
cyl("pendant_cord", 0.004, H - PZ - 0.15, (0, PY, (H + PZ + 0.15) / 2), M["kettle"], 8)
bpy.ops.mesh.primitive_cone_add(radius1=0.18, radius2=0.04, depth=0.18, vertices=40, location=(0, PY, PZ + 0.09))
sh = bpy.context.object; sh.name = "pendant_shade"; sh.data.materials.append(M["brass"]); link(sh, SET)
sol = sh.modifiers.new("solid", 'SOLIDIFY'); sol.thickness = 0.004
bpy.ops.object.shade_smooth()
bm = bpy.data.materials.new("M_bulb"); bm.use_nodes = True
bb = bm.node_tree.nodes["Principled BSDF"]; bb.inputs["Emission Color"].default_value = (1, 0.65, 0.35, 1); bb.inputs["Emission Strength"].default_value = 15
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04, location=(0, PY, PZ + 0.03)); bu = bpy.context.object
bu.name = "pendant_bulb"; bu.data.materials.append(bm); link(bu, SET)

# lights
def kelvin(k):
    return {2700: (1.0, 0.66, 0.38), 4000: (1, 0.82, 0.66), 8000: (0.72, 0.82, 1.0)}[k]
def light(name, typ, energy, loc, color, size=0.1, rot=None, target=None):
    ld = bpy.data.lights.new(name, typ); ld.energy = energy; ld.color = color
    if typ == 'AREA': ld.size = size
    else: ld.shadow_soft_size = size
    o = bpy.data.objects.new(name, ld); o.location = loc; LIG.objects.link(o)
    if target: look_at(o, target)
    return o
P = light("PENDANT", 'POINT', 60, (0, PY, PZ + 0.02), kelvin(2700), 0.04)
P["energy_CTRL"] = 60.0
light("FILL", 'AREA', 25, (0.6, -2.5, 2.3), kelvin(4000), 2.0, target=(0, 0.3, 1.0))
light("WINDOW_RIM", 'AREA', 18, (wx, WY + 0.4, (WZ0 + WZ1) / 2), kelvin(8000), 0.9, target=(0, 0, 1.5))
light("UNDERCAB", 'AREA', 6, (1.0 - 0.6, WY - 0.2, UZ0 - 0.02), kelvin(2700), 0.5, target=(0.4, WY - 0.2, 0))

w = bpy.data.worlds.new(f"W_{N}"); w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.004, 0.006, 0.015, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
scn.world = w

mark("SISTER", (0, 0, 0), 0)
camhint("CU_SISTER", (0.15, -2.2, 1.63), (0, 0, 1.58), 85)
camhint("MED_SISTER", (0.45, -2.9, 1.45), (0, 0.3, 1.2), 35)
scn.render.resolution_x, scn.render.resolution_y = 540, 960

if "--preview" in sys.argv:
    stand_in_figure((0, 0, 0), col=SET)
    render_previews(N)
save(out_path())
