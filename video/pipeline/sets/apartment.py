import sys; sys.path.insert(0, "/home/user/game1/video/pipeline/sets"); from _common import *
import numpy as np

PREVIEW = "--preview" in sys.argv
scn = reset_scene()
SET = collection("SET_apartment"); LIG = collection("LIGHTS_apartment")

# ---------- placeholder images ----------
def make_png(path, w, h, fn):
    if os.path.exists(path): return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    rgb = fn(xx / w, 1 - yy / h)  # u,v with v up in image space
    img = bpy.data.images.new(os.path.basename(path), w, h)
    a = np.ones((h, w, 1), np.float32)
    px = np.concatenate([rgb, a], 2)[::-1]  # blender pixel rows bottom-up
    img.pixels = px.ravel().tolist()
    img.filepath_raw = path; img.file_format = 'PNG'; img.save()
    bpy.data.images.remove(img)

def photo_fn(u, v):
    bg = np.stack([0.55 + 0.25*v, 0.42 + 0.2*v, 0.30 + 0.1*v], -1)
    for cx, cy, r in ((0.35, 0.45, 0.17), (0.65, 0.42, 0.16)):
        d = np.sqrt((u-cx)**2 + ((v-cy)*0.8)**2); m = np.clip(1 - d/r, 0, 1)[..., None]**0.5
        bg = bg*(1-m) + np.array([0.85, 0.55, 0.38])*m
        dh = np.sqrt((u-cx)**2 + (v-cy-0.22)**2); mh = np.clip(1 - dh/0.08, 0, 1)[..., None]**0.4
        bg = bg*(1-mh) + np.array([0.9, 0.7, 0.55])*mh
    return bg.astype(np.float32)
make_png("/opt/work/props/sisters_photo.png", 512, 640, photo_fn)

def screen_fn(u, v):
    c = np.zeros(u.shape + (3,), np.float32) + 0.06
    H = 844; row = (1 - v) * H
    lines = (row > 140) & (row < 800) & (((row - 140) % 26) < 9) & (u > 0.08) & (u < 0.92 - 0.25*((((row-140)//26) % 5) == 4))
    c[lines] = 0.78
    title = (row > 80) & (row < 108) & (u > 0.08) & (u < 0.6); c[title] = 0.95
    return c
make_png("/opt/work/props/phone_screen.png", 390, 844, screen_fn)

# ---------- material helpers ----------
def mat(name, col, rough=0.5, var=0.15, scale=8.0, bump=0.2, metallic=0.0, col2=None, vor=False):
    m = principled(name, col, rough, metallic); nt = m.node_tree; N = nt.nodes; L = nt.links
    b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale; nz.inputs["Detail"].default_value = 6
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*[c*(1-var) for c in col], 1)
    ramp.color_ramp.elements[1].color = (*(col2 or [min(1, c*(1+var)) for c in col]), 1)
    L.new(nz.outputs["Fac"], ramp.inputs["Fac"]); L.new(ramp.outputs["Color"], b.inputs["Base Color"])
    mr = N.new("ShaderNodeMapRange"); mr.inputs[3].default_value = rough*0.8; mr.inputs[4].default_value = min(1, rough*1.2)
    L.new(nz.outputs["Fac"], mr.inputs[0]); L.new(mr.outputs[0], b.inputs["Roughness"])
    bn = N.new("ShaderNodeBump"); bn.inputs["Strength"].default_value = bump; bn.inputs["Distance"].default_value = 0.01
    src = nz
    if vor:
        v = N.new("ShaderNodeTexVoronoi"); v.inputs["Scale"].default_value = scale*12
        L.new(tc.outputs["Object"], v.inputs["Vector"]); src = v
        L.new(v.outputs["Distance"], bn.inputs["Height"])
    else:
        L.new(nz.outputs["Fac"], bn.inputs["Height"])
    L.new(bn.outputs["Normal"], b.inputs["Normal"])
    return m

def wood(name, col):
    m = principled(name, col, 0.45); nt = m.node_tree; N = nt.nodes; L = nt.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (0.3, 6, 0.3)
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    w = N.new("ShaderNodeTexWave"); w.wave_type = 'BANDS'; w.bands_direction = 'X'
    w.inputs["Scale"].default_value = 1.5; w.inputs["Distortion"].default_value = 1.5; w.inputs["Detail"].default_value = 4
    L.new(mp.outputs["Vector"], w.inputs["Vector"])
    r = N.new("ShaderNodeValToRGB"); r.color_ramp.elements[0].color = (*[c*0.6 for c in col], 1); r.color_ramp.elements[1].color = (*col, 1)
    L.new(w.outputs["Fac"], r.inputs["Fac"]); L.new(r.outputs["Color"], b.inputs["Base Color"])
    bn = N.new("ShaderNodeBump"); bn.inputs["Strength"].default_value = 0.08
    L.new(w.outputs["Fac"], bn.inputs["Height"]); L.new(bn.outputs["Normal"], b.inputs["Normal"])
    return m

M_WALL = mat("M_wall", (0.62, 0.6, 0.56), 0.85, 0.05, 3, 0.05)
M_FLOOR = wood("M_floor", (0.33, 0.2, 0.11))
M_FAB = mat("M_couch_fabric", (0.17, 0.21, 0.25), 0.95, 0.12, 40, 0.3, vor=True)
M_BLANKET = mat("M_blanket", (0.45, 0.38, 0.3), 1.0, 0.15, 30, 0.4, vor=True)
M_PILLOW = mat("M_pillow", (0.55, 0.45, 0.32), 0.9, 0.1, 30, 0.3, vor=True)
M_RUG = mat("M_rug", (0.32, 0.3, 0.28), 1.0, 0.2, 60, 0.5, vor=True)
M_WOOD = wood("M_wood", (0.25, 0.15, 0.08))
M_LWOOD = wood("M_lightwood", (0.5, 0.36, 0.22))
M_METAL = principled("M_black_metal", (0.03, 0.03, 0.03), 0.35, 1.0)
M_CERAM = mat("M_ceramic", (0.75, 0.72, 0.66), 0.15, 0.03, 10, 0.02)
M_PAPER = mat("M_paper", (0.8, 0.76, 0.66), 0.8, 0.05, 20, 0.05)
M_COVER = mat("M_book_cover", (0.35, 0.08, 0.07), 0.6, 0.1, 15, 0.05)
M_LEAF = mat("M_leaf", (0.06, 0.16, 0.05), 0.5, 0.25, 6, 0.1)
M_POT = mat("M_pot", (0.4, 0.38, 0.35), 0.7, 0.1, 10, 0.2)
M_FRAME = principled("M_window_frame", (0.08, 0.08, 0.08), 0.4)
M_GLASS_BLK = principled("M_phone_glass", (0.005, 0.005, 0.006), 0.05)
M_ALU = principled("M_phone_metal", (0.5, 0.5, 0.52), 0.3, 1.0)
books = [mat(f"M_book{i}", c, 0.7, 0.1, 10, 0.05) for i, c in enumerate(
    [(0.4, 0.1, 0.08), (0.1, 0.18, 0.3), (0.6, 0.55, 0.45), (0.15, 0.25, 0.15), (0.5, 0.35, 0.15), (0.12, 0.12, 0.12)])]

shade = bpy.data.materials.new("M_lampshade"); shade.use_nodes = True
sb = shade.node_tree.nodes["Principled BSDF"]; sb.inputs["Base Color"].default_value = (0.9, 0.8, 0.65, 1)
sb.inputs["Roughness"].default_value = 0.9
sb.inputs["Emission Color"].default_value = (1.0, 0.6, 0.3, 1); sb.inputs["Emission Strength"].default_value = 1.5

def emis_img_mat(name, node_name, path, strength=None):
    m = principled(name, (0.1, 0.1, 0.1), 0.15 if strength else 0.4); N = m.node_tree.nodes; L = m.node_tree.links
    t = N.new("ShaderNodeTexImage"); t.name = t.label = node_name; t.image = bpy.data.images.load(path)
    b = N["Principled BSDF"]
    L.new(t.outputs["Color"], b.inputs["Base Color"])
    if strength:
        b.inputs["Base Color"].default_value = (0, 0, 0, 1)
        L.remove(b.inputs["Base Color"].links[0])
        L.new(t.outputs["Color"], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = strength
    return m
M_PHOTO = emis_img_mat("M_photo", "PHOTO_TEX", "/opt/work/props/sisters_photo.png")
M_SCREEN = emis_img_mat("M_phone_screen", "SCREEN_TEX", "/opt/work/props/phone_screen.png", 1.2)

def city_mat(name, scale, seed, thresh):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    N.remove(N["Principled BSDF"]); out = N["Material Output"]
    tc = N.new("ShaderNodeTexCoord")
    v = N.new("ShaderNodeTexVoronoi"); v.inputs["Scale"].default_value = scale; v.inputs["Randomness"].default_value = 1
    mp = N.new("ShaderNodeMapping"); mp.inputs["Location"].default_value = (seed, seed*1.7, 0)
    L.new(tc.outputs["Object"], mp.inputs["Vector"]); L.new(mp.outputs["Vector"], v.inputs["Vector"])
    # mask out top (sky) via gradient on z with noise skyline
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.5; L.new(mp.outputs["Vector"], nz.inputs["Vector"])
    # dots
    lt = N.new("ShaderNodeMath"); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = thresh
    L.new(v.outputs["Distance"], lt.inputs[0])
    rnd = N.new("ShaderNodeMath"); rnd.operation = 'GREATER_THAN'; rnd.inputs[1].default_value = 0.45
    L.new(v.outputs["Color"], rnd.inputs[0])  # color->float avg
    sky = N.new("ShaderNodeMath"); sky.operation = 'LESS_THAN'
    L.new(sep.outputs["Z"], sky.inputs[0])
    sk = N.new("ShaderNodeMath"); sk.operation = 'MULTIPLY_ADD'; sk.inputs[1].default_value = 0.8; sk.inputs[2].default_value = 0.1
    L.new(nz.outputs["Fac"], sk.inputs[0]); L.new(sk.outputs[0], sky.inputs[1])
    m1 = N.new("ShaderNodeMath"); m1.operation = 'MULTIPLY'; L.new(lt.outputs[0], m1.inputs[0]); L.new(sky.outputs[0], m1.inputs[1])
    m2 = N.new("ShaderNodeMath"); m2.operation = 'MULTIPLY'; L.new(m1.outputs[0], m2.inputs[0]); L.new(rnd.outputs[0], m2.inputs[1])
    mix = N.new("ShaderNodeMix"); mix.data_type = 'RGBA'
    mix.inputs[6].default_value = (1.0, 0.6, 0.3, 1); mix.inputs[7].default_value = (0.55, 0.7, 1.0, 1)
    sepc = N.new("ShaderNodeSeparateColor"); L.new(v.outputs["Color"], sepc.inputs[0])
    gt = N.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.7; L.new(sepc.outputs[0], gt.inputs[0])
    L.new(gt.outputs[0], mix.inputs[0])
    em = N.new("ShaderNodeEmission"); L.new(mix.outputs[2], em.inputs["Color"])
    st = N.new("ShaderNodeMath"); st.operation = 'MULTIPLY'; st.inputs[1].default_value = 25
    L.new(m2.outputs[0], st.inputs[0]); L.new(st.outputs[0], em.inputs["Strength"])
    # dark building silhouette base
    bg = N.new("ShaderNodeEmission"); bg.inputs["Color"].default_value = (0.01, 0.012, 0.02, 1)
    bgs = N.new("ShaderNodeMath"); bgs.operation = 'MULTIPLY'; bgs.inputs[1].default_value = 0.3
    L.new(sky.outputs[0], bgs.inputs[0]); L.new(bgs.outputs[0], bg.inputs["Strength"])
    add = N.new("ShaderNodeAddShader"); L.new(em.outputs[0], add.inputs[0]); L.new(bg.outputs[0], add.inputs[1])
    tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
    L.new(sky.outputs[0], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(add.outputs[0], mx.inputs[2])
    L.new(add.outputs[0], out.inputs["Surface"])
    return m

# ---------- geometry helpers ----------
def box(name, loc, size, m, bevel=0.0, segs=2, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        md = o.modifiers.new("bevel", 'BEVEL'); md.width = bevel; md.segments = segs; md.limit_method = 'ANGLE'
    o.data.materials.append(m); link(o, SET)
    for p in o.data.polygons: p.use_smooth = bool(bevel)
    if bevel: o.data.shade_smooth() if hasattr(o.data, "shade_smooth") else None
    return o

def cyl(name, loc, r, d, m, verts=24, bevel=0.0, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.data.materials.append(m); link(o, SET)
    if bevel:
        md = o.modifiers.new("bevel", 'BEVEL'); md.width = bevel; md.segments = 2; md.limit_method = 'ANGLE'
    bpy.ops.object.shade_auto_smooth()
    return o

def parent(children, p):
    for c in children:
        mw = c.matrix_world.copy(); c.parent = p; c.matrix_world = mw

# ---------- room ----------
WY = 1.6   # back wall
box("floor", (0, -0.5, -0.05), (6.5, 6.0, 0.1), M_FLOOR)
box("ceiling", (0, -0.5, 2.65), (6.5, 6.0, 0.1), M_WALL)
# back wall with window opening x[-1.3,1.3] z[0.75,2.35]
box("wall_back_L", (-2.25, WY + 0.1, 1.3), (1.9, 0.2, 2.6), M_WALL)
box("wall_back_R", (2.25, WY + 0.1, 1.3), (1.9, 0.2, 2.6), M_WALL)
box("wall_back_low", (0, WY + 0.1, 0.375), (2.6, 0.2, 0.75), M_WALL)
box("wall_back_top", (0, WY + 0.1, 2.475), (2.6, 0.2, 0.25), M_WALL)
box("wall_left", (-3.2, -0.5, 1.3), (0.2, 6.0, 2.6), M_WALL)
box("wall_right", (3.2, -0.5, 1.3), (0.2, 6.0, 2.6), M_WALL)
box("baseboard", (0, WY - 0.01, 0.05), (6.4, 0.02, 0.1), M_CERAM)
# window frame
for nm, l, s in [("win_sill", (0, WY - 0.03, 0.74), (2.7, 0.18, 0.04)), ("win_mullion", (0, WY + 0.1, 1.55), (0.05, 0.06, 1.6)),
                 ("win_frame_L", (-1.3, WY + 0.1, 1.55), (0.06, 0.1, 1.6)), ("win_frame_R", (1.3, WY + 0.1, 1.55), (0.06, 0.1, 1.6)),
                 ("win_frame_T", (0, WY + 0.1, 2.35), (2.6, 0.1, 0.06)), ("win_frame_B", (0, WY + 0.1, 0.77), (2.6, 0.1, 0.06)),
                 ("win_transom", (0, WY + 0.1, 1.95), (2.6, 0.06, 0.04))]:
    box(nm, l, s, M_FRAME, 0.005)
# city planes
for i, (d, sc, th, w) in enumerate([(30, 3.0, 0.07, 60), (70, 1.8, 0.06, 140), (150, 1.0, 0.06, 300)]):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, d, 0), rotation=(math.radians(90), 0, 0))
    p = bpy.context.object; p.name = f"city_plane_{i}"; p.scale = (w, d*0.25, 1)
    bpy.ops.object.transform_apply(scale=True)
    p.location.z = -d*0.03 + 1.5
    p.data.materials.append(city_mat(f"M_city_{i}", sc, i*3.1, th)); link(p, SET)
    p.visible_shadow = False

# rug
box("rug", (0, -0.5, 0.005), (2.6, 1.9, 0.01), M_RUG, 0.004)

# ---------- couch ----------
couch = bpy.data.objects.new("couch", None); SET.objects.link(couch)
parts = []
parts.append(box("couch_base", (0, 0.5, 0.22), (2.1, 0.85, 0.24), M_FAB, 0.03, 3))
for i, x in enumerate((-0.62, 0, 0.62)):
    parts.append(box(f"couch_cushion_{i}", (x, 0.43, 0.395), (0.6, 0.66, 0.11), M_FAB, 0.045, 4))
    parts.append(box(f"couch_back_{i}", (x, 0.85, 0.66), (0.6, 0.2, 0.42), M_FAB, 0.07, 4, rot=(math.radians(-10), 0, 0)))
parts.append(box("couch_backframe", (0, 0.97, 0.48), (2.1, 0.12, 0.62), M_FAB, 0.03, 3))
for s in (-1, 1):
    parts.append(box(f"couch_arm_{'L' if s<0 else 'R'}", (s*1.13, 0.5, 0.36), (0.16, 0.88, 0.52), M_FAB, 0.05, 4))
    for y in (0.15, 0.85):
        parts.append(cyl("couch_leg", (s*1.1, y, 0.05), 0.02, 0.1, M_WOOD, 12))
parent(parts, couch)
# blanket draped over left arm/seat
bl = box("blanket", (-0.85, 0.45, 0.47), (0.55, 0.7, 0.025), M_BLANKET, 0.01, 2, rot=(0, math.radians(8), math.radians(4)))
md = bl.modifiers.new("sub", 'SUBSURF'); md.levels = 1; md.render_levels = 1
md = bl.modifiers.new("lumps", 'DISPLACE'); tx = bpy.data.textures.new("blanket_lumps", 'CLOUDS'); tx.noise_scale = 0.15; md.texture = tx; md.strength = 0.03
bl.modifiers.move(0, 1) if False else None
# throw pillow
pl = box("throw_pillow", (0.82, 0.68, 0.62), (0.42, 0.14, 0.4), M_PILLOW, 0.06, 4, rot=(math.radians(-18), 0, math.radians(-12)))
md = pl.modifiers.new("sub", 'SUBSURF'); md.levels = 1; md.render_levels = 1

# ---------- coffee table ----------
CT = (0, -0.55)
box("coffee_table_top", (CT[0], CT[1], 0.42), (1.1, 0.55, 0.04), M_LWOOD, 0.008)
box("coffee_table_shelf", (CT[0], CT[1], 0.12), (1.0, 0.48, 0.02), M_LWOOD, 0.004)
for sx in (-1, 1):
    for sy in (-1, 1):
        box("coffee_table_leg", (CT[0] + sx*0.51, CT[1] + sy*0.24, 0.2), (0.035, 0.035, 0.40), M_LWOOD, 0.004)
# mug
mug = cyl("mug", (-0.25, -0.45, 0.49), 0.042, 0.095, M_CERAM, 24, 0.004)
bpy.ops.mesh.primitive_torus_add(major_radius=0.028, minor_radius=0.007, location=(-0.205, -0.45, 0.49), rotation=(math.radians(90), 0, 0))
h = bpy.context.object; h.name = "mug_handle"; h.data.materials.append(M_CERAM); link(h, SET); h.parent = mug; h.location = (0.045, 0, 0)
cof = cyl("mug_coffee", (0, 0, 0.04), 0.038, 0.002, principled("M_coffee", (0.05, 0.025, 0.01), 0.05), 24); cof.parent = mug; cof.location = (0, 0, 0.04)
# paperback
bk = box("paperback", (0.22, -0.62, 0.455), (0.13, 0.198, 0.024), M_COVER, 0.002, 1, rot=(0, 0, math.radians(14)))
pg = box("paperback_pages", (0, 0, 0), (0.125, 0.19, 0.02), M_PAPER); pg.parent = bk; pg.location = (0.003, 0, 0)
pg.scale = (1, 1, 1.02)
# phone
ph = box("PROP_PHONE", (-0.05, -0.62, 0.444), (0.071, 0.147, 0.008), M_ALU, 0.0, 1, rot=(0, 0, math.radians(-8)))
md = ph.modifiers.new("corners", 'BEVEL'); md.width = 0.009; md.segments = 6; md.affect = 'EDGES'
ph.data.materials.clear(); ph.data.materials.append(M_ALU)
bev = ph.modifiers.new("edge", 'BEVEL'); bev.width = 0.0015; bev.segments = 2; bev.limit_method = 'ANGLE'
# make only vertical edges get big bevel: use bevel weights
import bmesh
bm = bmesh.new(); bm.from_mesh(ph.data)
bw = bm.edges.layers.float.new("bevel_weight_edge")
for e in bm.edges:
    v = e.verts[0].co - e.verts[1].co
    e[bw] = 1.0 if abs(v.z) > 0.004 else 0.0
bm.to_mesh(ph.data); bm.free()
md.limit_method = 'WEIGHT'
for p in ph.data.polygons: p.use_smooth = True
glass = box("PROP_PHONE_glass", (0, 0, 0), (0.0695, 0.1455, 0.0004), M_GLASS_BLK); glass.parent = ph; glass.location = (0, 0, 0.0040)
gm = glass.modifiers.new("corners", 'BEVEL'); gm.width = 0.0085; gm.segments = 6; gm.limit_method = 'WEIGHT'
bm = bmesh.new(); bm.from_mesh(glass.data); bw = bm.edges.layers.float.new("bevel_weight_edge")
for e in bm.edges:
    v = e.verts[0].co - e.verts[1].co; e[bw] = 1.0 if abs(v.z) > 0.0002 else 0.0
bm.to_mesh(glass.data); bm.free()
bpy.ops.mesh.primitive_plane_add(size=1); scr = bpy.context.object; scr.name = "PROP_PHONE_screen"
scr.scale = (0.066, 0.142, 1); bpy.ops.object.transform_apply(scale=True)
scr.data.materials.append(M_SCREEN); link(scr, SET); scr.parent = ph; scr.location = (0, 0, 0.00425)
ph["screen_on"] = 1.0  # hook: drive M_phone_screen emission strength
for o in (glass, scr): o.matrix_parent_inverse.identity()

# ---------- side table + lamp + photo ----------
ST = (1.5, 0.45)
cyl("side_table_top", (ST[0], ST[1], 0.56), 0.24, 0.03, M_WOOD, 40, 0.005)
cyl("side_table_stem", (ST[0], ST[1], 0.28), 0.025, 0.54, M_METAL, 16)
cyl("side_table_foot", (ST[0], ST[1], 0.01), 0.18, 0.02, M_METAL, 32, 0.004)
cyl("lamp_base", (ST[0] + 0.06, ST[1] + 0.08, 0.66), 0.06, 0.17, M_CERAM, 32, 0.01)
cyl("lamp_stem", (ST[0] + 0.06, ST[1] + 0.08, 0.82), 0.008, 0.18, M_METAL, 12)
bpy.ops.mesh.primitive_cone_add(vertices=40, radius1=0.17, radius2=0.12, depth=0.22, end_fill_type='NOTHING', location=(ST[0] + 0.06, ST[1] + 0.08, 0.95))
sh = bpy.context.object; sh.name = "lamp_shade"; sh.data.materials.append(shade); link(sh, SET)
sh.modifiers.new("thick", 'SOLIDIFY').thickness = 0.003; sh.visible_shadow = False
# photo frame, angled toward couch center
pf = bpy.data.objects.new("PROP_PHOTO", None); SET.objects.link(pf)
pf.location = (ST[0] - 0.1, ST[1] - 0.1, 0.575)
pf.rotation_euler = (0, 0, math.radians(-50))  # face toward couch (-X,-Y)
fr = box("PROP_PHOTO_frame", (0, 0, 0), (0.17, 0.015, 0.22), M_WOOD, 0.003)
pic = box("PROP_PHOTO_picture", (0, 0, 0), (0.15, 0.002, 0.2), M_PHOTO)
leg = box("PROP_PHOTO_stand", (0, 0, 0), (0.03, 0.005, 0.18), M_WOOD)
for c in (fr, pic, leg): c.parent = pf
fr.location = (0, 0, 0.11); fr.rotation_euler = (math.radians(-12), 0, 0)
pic.location = (0, -0.009, 0.112); pic.rotation_euler = (math.radians(-12), 0, 0)
leg.location = (0, 0.05, 0.09); leg.rotation_euler = (math.radians(20), 0, 0)
# UV for picture front: map so image upright on -Y face
pic.data.uv_layers.active
bpy.context.view_layer.objects.active = pic
for p in pic.data.polygons:
    for li in p.loop_indices:
        co = pic.data.vertices[pic.data.loops[li].vertex_index].co
        pic.data.uv_layers.active.data[li].uv = (co.x/0.15 + 0.5, co.z/0.2 + 0.5)
# phone screen UVs default plane OK (0..1)

# ---------- bookshelf ----------
BS = (-2.55, 0.9)
bsh = bpy.data.objects.new("bookshelf", None); SET.objects.link(bsh); bparts = []
for s in (-1, 1): bparts.append(box("shelf_side", (BS[0] + s*0.39, BS[1], 0.9), (0.025, 0.32, 1.8), M_WOOD, 0.003))
for k, z in enumerate((0.04, 0.45, 0.85, 1.25, 1.65, 1.79)):
    bparts.append(box("shelf_board", (BS[0], BS[1], z), (0.76, 0.32, 0.025), M_WOOD, 0.003))
bparts.append(box("shelf_back", (BS[0], BS[1] + 0.155, 0.9), (0.78, 0.01, 1.8), M_WOOD))
import random; random.seed(7)
for z in (0.465, 0.865, 1.265):
    x = BS[0] - 0.36
    while x < BS[0] + 0.25:
        w = random.uniform(0.02, 0.045); hgt = random.uniform(0.2, 0.3)
        bparts.append(box("book", (x + w/2, BS[1] + 0.02, z + hgt/2), (w, random.uniform(0.15, 0.22), hgt), random.choice(books), 0.002, 1))
        x += w + 0.002
bparts.append(cyl("shelf_vase", (BS[0] + 0.15, BS[1], 1.75), 0.05, 0.18, M_CERAM, 24, 0.01) if False else cyl("shelf_vase", (BS[0] + 0.15, BS[1], 1.36), 0.05, 0.2, M_POT, 24, 0.005))
parent(bparts, bsh)

# ---------- plant ----------
PL = (2.5, 1.1)
cyl("plant_pot", (PL[0], PL[1], 0.2), 0.18, 0.4, M_POT, 32, 0.01)
cyl("plant_soil", (PL[0], PL[1], 0.39), 0.17, 0.01, principled("M_soil", (0.05, 0.035, 0.02), 0.95), 24)
random.seed(3)
for i in range(22):
    a = random.uniform(0, 2*math.pi); tilt = random.uniform(15, 55); L_ = random.uniform(0.35, 0.8)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=6, radius=1)
    lf = bpy.context.object; lf.name = "plant_leaf"; lf.scale = (0.05, 0.012, L_*0.35)
    lf.rotation_euler = (0, math.radians(tilt), a)
    d = Vector((0, 0, L_*0.35)); d.rotate(lf.rotation_euler)
    lf.location = Vector((PL[0], PL[1], 0.4)) + d
    lf.data.materials.append(M_LEAF); link(lf, SET); bpy.ops.object.shade_smooth()

# ---------- lights ----------
def light(name, kind, loc, energy, color, **kw):
    ld = bpy.data.lights.new(name, kind); ld.energy = energy; ld.color = color
    for k, v in kw.items(): setattr(ld, k, v)
    o = bpy.data.objects.new(name, ld); o.location = loc; LIG.objects.link(o); return o
lamp = light("TABLE_LAMP", 'POINT', (ST[0] + 0.06, ST[1] + 0.08, 0.95), 30, (1.0, 0.63, 0.32), shadow_soft_size=0.06)
wf = light("WINDOW_FILL", 'AREA', (0, WY - 0.05, 1.55), 45, (0.55, 0.68, 1.0), shape='RECTANGLE', size=2.5, size_y=1.55)
wf.rotation_euler = (math.radians(-90), 0, 0)  # -Z -> -Y? area emits along -Z
look_at(wf, (0, -1.0, 1.0))
rim = light("CITY_RIM", 'AREA', (-1.2, WY - 0.2, 2.2), 15, (0.5, 0.62, 1.0), size=0.6)
look_at(rim, (0, 0.4, 1.0))
fill = light("ROOM_BOUNCE", 'AREA', (0.5, -3.0, 2.3), 6, (0.8, 0.82, 0.9), size=2.0)
look_at(fill, (0, 0.3, 0.8))
for o in LIG.objects: o["energy_scale"] = 1.0

w = bpy.data.worlds.new("W_apartment"); w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.006, 0.009, 0.02, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
scn.world = w

# ---------- marks / cameras ----------
mark("WOMAN", (0, 0.35, 0), 0, SET)
cu = camhint("CU_WOMAN", (0.25, -1.75, 1.12), (0, 0.42, 1.08), 85, SET)
md_ = camhint("MED_WOMAN", (0.55, -2.35, 1.15), (0, 0.3, 0.72), 35, SET)
PT = tuple(pf.location + Vector((0, 0, 0.11)))
pc = camhint("PHOTO_CU", (0.6, -0.85, 0.9), PT, 100, SET)
ots = camhint("OTS_PHONE", (-0.55, 0.78, 1.42), (0.05, 0.12, 0.55), 50, SET)
for cam, tgt, f in ((cu, (0, 0.42, 1.08), 1.8), (md_, (0, 0.3, 0.9), 2.8), (pc, PT, 2.8), (ots, (0.05, 0.12, 0.55), 2.8)):
    cam.data.dof.use_dof = True; cam.data.dof.focus_distance = (Vector(tgt) - cam.location).length; cam.data.dof.aperture_fstop = f
    cam.data.clip_end = 400

scn.render.engine = 'CYCLES'; scn.cycles.device = 'CPU'
scn.render.resolution_x, scn.render.resolution_y = 540, 960
scn.cycles.samples = 8; scn.cycles.use_denoising = True
scn.cycles.max_bounces = 4; scn.cycles.diffuse_bounces = 2; scn.cycles.glossy_bounces = 1; scn.cycles.transparent_max_bounces = 4
scn.view_settings.view_transform = 'AgX'; scn.view_settings.look = 'AgX - Medium High Contrast'
scn.camera = md_

if PREVIEW:
    stand_in_figure((0, 0.35, 0), 0, 1.3, SET)
    render_previews("apartment")
    scn.camera = md_
nf = sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH')
print("FACES", nf)
save(out_path())
