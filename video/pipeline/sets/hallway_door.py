import sys; sys.path.insert(0, "/home/user/game1/video/pipeline/sets"); from _common import *
import bpy, math, bmesh
PREVIEW = "--preview" in sys.argv
scn = reset_scene()
SET = collection("SET_hallway_door"); LG = collection("LIGHTS_hallway_door")
HW = 0.8; L = 7.0; H = 2.6; WT = 0.15; DX0, DX1 = -0.45, 0.45; DH = 2.05

def nodes_mat(name, c1, c2, rough=(0.5, 0.7), scale=8.0, bump=0.2, kind='NOISE', metallic=0.0, bscale=None):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; Ln = nt.links
    b = N["Principled BSDF"]; b.inputs["Metallic"].default_value = metallic
    tc = N.new("ShaderNodeTexCoord"); 
    t = N.new("ShaderNodeTexNoise"); t.inputs["Scale"].default_value = scale; t.inputs["Detail"].default_value = 3
    Ln.new(tc.outputs["Object"], t.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (*c1, 1); cr.color_ramp.elements[1].color = (*c2, 1)
    Ln.new(t.outputs["Fac"], cr.inputs["Fac"]); Ln.new(cr.outputs["Color"], b.inputs["Base Color"])
    mr = N.new("ShaderNodeMapRange"); mr.inputs[3].default_value = rough[0]; mr.inputs[4].default_value = rough[1]
    Ln.new(t.outputs["Fac"], mr.inputs[0]); Ln.new(mr.outputs[0], b.inputs["Roughness"])
    src = t
    if kind == 'VORONOI':
        v = N.new("ShaderNodeTexVoronoi"); v.inputs["Scale"].default_value = bscale or scale*4
        Ln.new(tc.outputs["Object"], v.inputs["Vector"]); src = v; out = v.outputs["Distance"]
    elif kind == 'WAVE':
        w = N.new("ShaderNodeTexWave"); w.inputs["Scale"].default_value = bscale or 3; w.inputs["Distortion"].default_value = 6
        w.bands_direction = 'Z'
        Ln.new(tc.outputs["Object"], w.inputs["Vector"]); out = w.outputs["Fac"]
        mix = N.new("ShaderNodeMix"); mix.data_type='RGBA'; mix.inputs[0].default_value = 0.06
        Ln.new(cr.outputs["Color"], mix.inputs[6]); Ln.new(w.outputs["Color"], mix.inputs[7])
        Ln.new(mix.outputs[2], b.inputs["Base Color"])
    else:
        t2 = N.new("ShaderNodeTexNoise"); t2.inputs["Scale"].default_value = bscale or scale*20
        Ln.new(tc.outputs["Object"], t2.inputs["Vector"]); out = t2.outputs["Fac"]
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = 0.01
    Ln.new(out, bp.inputs["Height"]); Ln.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m

M_WALL = nodes_mat("M_HallWall", (0.52, 0.55, 0.48), (0.60, 0.62, 0.55), (0.75, 0.9), 3, 0.08)
M_WALL_IN = nodes_mat("M_InteriorWall", (0.75, 0.68, 0.56), (0.80, 0.74, 0.62), (0.7, 0.85), 3, 0.06)
M_CEIL = nodes_mat("M_Ceiling", (0.70, 0.71, 0.68), (0.75, 0.75, 0.72), (0.85, 0.95), 4, 0.05)
M_FLOOR = nodes_mat("M_HallFloor", (0.22, 0.20, 0.18), (0.30, 0.28, 0.25), (0.35, 0.6), 2, 0.1, 'VORONOI', bscale=6)
M_CARPET = nodes_mat("M_Carpet", (0.20, 0.05, 0.05), (0.32, 0.09, 0.07), (0.9, 1.0), 30, 0.4, bscale=400)
M_BASE = nodes_mat("M_Baseboard", (0.80, 0.80, 0.76), (0.85, 0.85, 0.80), (0.3, 0.45), 5, 0.03)
M_DOOR = nodes_mat("M_DoorBlue", (0.02, 0.05, 0.16), (0.03, 0.07, 0.20), (0.25, 0.45), 6, 0.05, 'WAVE', bscale=4)
M_OTHERDOOR = nodes_mat("M_DoorBrown", (0.15, 0.08, 0.04), (0.25, 0.14, 0.07), (0.35, 0.55), 6, 0.05, 'WAVE', bscale=4)
M_FRAME = nodes_mat("M_DoorFrame", (0.78, 0.78, 0.74), (0.84, 0.84, 0.80), (0.3, 0.45), 5, 0.03)
M_BRASS = nodes_mat("M_Brass", (0.6, 0.45, 0.2), (0.75, 0.58, 0.3), (0.2, 0.4), 20, 0.02, metallic=1.0)
M_WOODFLOOR = nodes_mat("M_InteriorFloor", (0.30, 0.17, 0.08), (0.42, 0.25, 0.12), (0.3, 0.5), 3, 0.08, 'WAVE', bscale=2)
M_LAMP = bpy.data.materials.new("M_LampEmit"); M_LAMP.use_nodes = True
e = M_LAMP.node_tree.nodes["Principled BSDF"]; e.inputs["Emission Color"].default_value = (0.85, 1.0, 0.92, 1); e.inputs["Emission Strength"].default_value = 6; M_LAMP.cycles.emission_sampling = "NONE"
M_COAT = principled("M_Coat", (0.12, 0.10, 0.09), 0.8)

def box(name, x0, x1, y0, y1, z0, z1, mat, bevel=0.0, col=SET):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); col.objects.link(o)
    o.location = ((x0+x1)/2, (y0+y1)/2, (z0+z1)/2); o.scale = (x1-x0, y1-y0, z1-z0)
    me.materials.append(mat)
    if bevel:
        bpy.context.view_layer.objects.active = o; o.select_set(True)
        bpy.ops.object.transform_apply(scale=True); o.select_set(False)
        mod = o.modifiers.new("Bevel", 'BEVEL'); mod.width = bevel; mod.segments = 2; mod.limit_method = 'ANGLE'
    return o

# Floor / ceiling / walls
box("HallFloor", -L, L, -HW, HW, -0.05, 0, M_FLOOR)
box("HallCeiling", -L, L, -HW, HW, H, H+0.05, M_CEIL)
box("WallSouth", -L, L, -HW-WT, -HW, 0, H, M_WALL)
box("WallNorth_L", -L, DX0-0.07, HW, HW+WT, 0, H, M_WALL)
box("WallNorth_R", DX1+0.07, L, HW, HW+WT, 0, H, M_WALL)
box("WallNorth_Top", DX0-0.07, DX1+0.07, HW, HW+WT, DH+0.07, H, M_WALL)
box("WallEnd_W", -L-WT, -L, -HW, HW, 0, H, M_WALL); box("WallEnd_E", L, L+WT, -HW, HW, 0, H, M_WALL)
box("CarpetRunner", -L+0.3, L-0.3, -0.5, 0.5, 0, 0.012, M_CARPET, 0.004)
for side, y0, y1 in (("S", -HW, -HW+0.015), ("N", HW-0.015, HW)):
    if side == "S": box("Baseboard_S", -L, L, y0, y1, 0, 0.11, M_BASE, 0.004)
    else:
        box("Baseboard_N_L", -L, DX0-0.07, y0, y1, 0, 0.11, M_BASE, 0.004)
        box("Baseboard_N_R", DX1+0.07, L, y0, y1, 0, 0.11, M_BASE, 0.004)
# Door frame (casing) on hall side
for n, a, b_ in (("L", DX0-0.07, DX0), ("R", DX1, DX1+0.07)):
    box(f"DoorFrame_{n}", a, b_, HW-0.02, HW+WT, 0, DH+0.07, M_FRAME, 0.006)
box("DoorFrame_Top", DX0-0.07, DX1+0.07, HW-0.02, HW+WT, DH, DH+0.07, M_FRAME, 0.006)
box("Threshold", DX0, DX1, HW, HW+WT, 0, 0.015, M_FRAME, 0.003)

# Main door: origin at hinge (x=DX0, y=HW+WT-0.045)
hinge = (DX0+0.005, HW+WT-0.045, 0)
door = bpy.data.objects.new("PROP_DOOR", None); door.empty_display_type = 'ARROWS'; SET.objects.link(door)
door.location = hinge
def door_part(name, x0, x1, y0, y1, z0, z1, mat, bev=0.004):
    o = box(name, x0, x1, y0, y1, z0, z1, mat, bev); o.parent = door; o.location -= Vector(hinge); return o
W = 0.89; T = 0.045; yb = hinge[1]-T/2  # door panel slab in world coords at rest
y0, y1 = hinge[1]-T, hinge[1]
door_part("Door_Slab", DX0+0.005, DX0+0.005+W, y0, y1, 0.005, DH-0.005, M_DOOR)
# raised panels on hall side
for (zz0, zz1) in ((0.15, 0.95), (1.1, 1.9)):
    for (xx0, xx1) in ((0.10, 0.40), (0.49, 0.79)):
        door_part("Door_Panel", DX0+xx0, DX0+xx1, y0-0.012, y0, zz0, zz1, M_DOOR, 0.006)
door_part("Door_Knob", DX0+W-0.08, DX0+W-0.04, y0-0.07, y0, 0.98, 1.02, M_BRASS, 0.015)
door_part("Door_KnobIn", DX0+W-0.08, DX0+W-0.04, y1, y1+0.07, 0.98, 1.02, M_BRASS, 0.015)
door_part("Door_NumberPlate", DX0+0.39, DX0+0.51, y0-0.018, y0-0.012, 1.55, 1.68, M_BRASS, 0.003)
door_part("Door_Peephole", DX0+0.435, DX0+0.465, y0-0.02, y0, 1.45, 1.48, M_BRASS, 0.006)
door.rotation_euler.z = math.radians(70)

# Interior entry
IY0, IY1 = HW+WT, HW+WT+2.2
box("Interior_Floor", -1.2, 1.2, IY0, IY1, -0.05, 0.0, M_WOODFLOOR)
box("Interior_Ceiling", -1.2, 1.2, IY0, IY1, H, H+0.05, M_CEIL)
box("Interior_WallW", -1.35, -1.2, IY0, IY1, 0, H, M_WALL_IN)
box("Interior_WallE", 1.2, 1.35, IY0, IY1, 0, H, M_WALL_IN)
box("Interior_WallBack", -1.2, 1.2, IY1, IY1+0.15, 0, H, M_WALL_IN)
box("Interior_Console", 0.75, 1.18, IY0+0.9, IY0+1.9, 0, 0.8, M_OTHERDOOR, 0.01)
box("Interior_Rug", -0.5, 0.5, IY0+0.2, IY0+1.6, 0, 0.01, M_CARPET, 0.003)
box("Interior_Coat", -1.2, -1.05, IY0+1.2, IY0+1.7, 0.9, 1.7, M_COAT, 0.05)

# Other doors along the corridor
for i, x in enumerate((-4.5, 3.8)):
    box(f"OtherDoor_{i}", x-0.45, x+0.45, HW-0.03, HW, 0, DH, M_OTHERDOOR, 0.005)
    box(f"OtherDoorFrame_{i}", x-0.52, x+0.52, HW-0.035, HW-0.025, 0, DH+0.07, M_FRAME, 0.004)
    box(f"OtherDoorKnob_{i}", x+0.33, x+0.37, HW-0.09, HW-0.03, 0.98, 1.02, M_BRASS, 0.015)
for i, x in enumerate((-2.2, 2.4, 5.5)):
    box(f"OtherDoorS_{i}", x-0.45, x+0.45, -HW, -HW+0.03, 0, DH, M_OTHERDOOR, 0.005)
    box(f"OtherDoorSFrame_{i}", x-0.52, x+0.52, -HW+0.025, -HW+0.035, 0, DH+0.07, M_FRAME, 0.004)
    box(f"OtherDoorSKnob_{i}", x-0.37, x-0.33, -HW+0.03, -HW+0.09, 0.98, 1.02, M_BRASS, 0.015)

# Ceiling fixtures + lights
def area(name, loc, energy, color, size, col=LG, rot=(0,0,0)):
    ld = bpy.data.lights.new(name, 'AREA'); ld.energy = energy; ld.color = color; ld.size = size
    o = bpy.data.objects.new(name, ld); col.objects.link(o); o.location = loc; o.rotation_euler = rot; return o
for n, x in (("HALL_1", -1.2), ("HALL_2", 2.6)):
    box(f"Fixture_{n}", x-0.25, x+0.25, -0.12, 0.12, H-0.04, H, M_LAMP, 0.01)
    area(n, (x, 0, H-0.05), 40, (0.82, 1.0, 0.88), 0.45)
box("Fixture_FarW", -5.5-0.25, -5.5+0.25, -0.12, 0.12, H-0.04, H, M_LAMP)
area("HALL_3", (-5.5, 0, H-0.05), 30, (0.82, 1.0, 0.88), 0.45)
interior = area("INTERIOR", (0, IY0+1.1, H-0.1), 120, (1.0, 0.71, 0.42), 0.6)  # ~2700K
box("Fixture_Interior", -0.15, 0.15, IY0+0.95, IY0+1.25, H-0.03, H, M_LAMP)

# Hooks
ctrl = bpy.data.objects.new("DOOR_CTRL", None); SET.objects.link(ctrl); ctrl.location = (0, HW, DH+0.3)
ctrl["door_open_deg"] = 70.0; ctrl["interior_energy"] = 120.0; ctrl["hall_energy"] = 40.0
def drv(target, path, expr, var_path, idx=-1):
    fc = target.driver_add(path, idx) if idx >= 0 else target.driver_add(path)
    d = fc.driver; d.type = 'SCRIPTED'; v = d.variables.new(); v.name = "v"
    v.targets[0].id = ctrl; v.targets[0].data_path = var_path; d.expression = expr
drv(door, "rotation_euler", "radians(v)", '["door_open_deg"]', 2)
drv(interior.data, "energy", "v", '["interior_energy"]')
for n in ("HALL_1", "HALL_2"): drv(bpy.data.lights[n], "energy", "v", '["hall_energy"]')

# World
w = bpy.data.worlds.new("W_hallway_door"); w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.004, 0.005, 0.006, 1); scn.world = w

# Marks / cams
mark("WOMAN", (0, -0.45, 0), 180, SET); mark("SISTER", (0, 0.35, 0), 0, SET)
camhint("TWO_SHOT", (3.4, -0.6, 1.6), (0, 0.35, 1.3), 35, SET)
camhint("CU_WOMAN", (2.0, 0.55, 1.62), (0, -0.45, 1.45), 85, SET)
camhint("CU_SISTER", (-2.0, -0.6, 1.6), (0, 0.35, 1.42), 85, SET)
camhint("WIDE", (-6.6, -0.5, 1.7), (1.0, 0.3, 1.2), 24, SET)

scn.render.engine = 'CYCLES'; scn.cycles.device = 'CPU'; scn.cycles.samples = 8
c = scn.cycles; c.max_bounces = 4; c.diffuse_bounces = 2; c.glossy_bounces = 1; c.transmission_bounces = 0
c.transparent_max_bounces = 2; c.caustics_reflective = False; c.caustics_refractive = False; c.use_denoising = True
scn.view_settings.view_transform = 'AgX'; scn.view_settings.look = 'AgX - Medium High Contrast'
scn.render.resolution_x, scn.render.resolution_y = 540, 960
if PREVIEW:
    stand_in_figure((0, -0.45), 180, col=SET); stand_in_figure((0, 0.35), 0, height=1.68, col=SET)
    render_previews("hallway_door")
    scn.render.resolution_x, scn.render.resolution_y = 540, 960
save(out_path())
