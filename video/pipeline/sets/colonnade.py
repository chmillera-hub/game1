"""Solomon's Colonnade set (John 10 / 17). Run: blender -b --factory-startup -P colonnade.py -- out.blend [--preview]"""
import sys; sys.path.insert(0, "/home/user/game1/video/pipeline/sets"); from _common import *
import bmesh, random
from mathutils import Matrix

random.seed(7)
PREVIEW = "--preview" in sys.argv
scn = reset_scene()
SET = collection("SET_colonnade"); LIG = collection("LIGHTS_colonnade")

# ---------------- materials ----------------
def nodes_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; return m, nt, nt.nodes, nt.links, nt.nodes["Principled BSDF"]

def ramp(nodes, c0, c1, p0=0.3, p1=0.7):
    r = nodes.new("ShaderNodeValToRGB"); e = r.color_ramp.elements
    e[0].position, e[0].color = p0, (*c0, 1); e[1].position, e[1].color = p1, (*c1, 1); return r

def noise(nodes, scale, detail=6, rough=0.6, coord=None, links=None):
    n = nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail; n.inputs["Roughness"].default_value = rough
    if coord is not None: links.new(coord, n.inputs["Vector"])
    return n

def stone_mat(name, c0, c1, rough=(0.55, 0.85), bscale=6.0, bstr=0.25, brick=None, cracks=False):
    """Limestone: object-space noise colour, roughness variation, bump. brick=(w,h,mortar,offset) adds joints."""
    m, nt, N, L, b = nodes_mat(name)
    tc = N.new("ShaderNodeTexCoord"); co = tc.outputs["Object"]
    n1 = noise(N, 1.2, 3, 0.6, co, L); n2 = noise(N, 9.0, 3, 0.65, co, L)
    r1 = ramp(N, c0, c1, 0.35, 0.68); L.new(n1.outputs["Fac"], r1.inputs["Fac"])
    mix = N.new("ShaderNodeMix"); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
    mix.inputs["Factor"].default_value = 0.5
    L.new(r1.outputs["Color"], mix.inputs[6]); L.new(n2.outputs["Color"], mix.inputs[7])
    col = mix.outputs[2]
    rr = N.new("ShaderNodeMapRange"); rr.inputs[3].default_value, rr.inputs[4].default_value = rough
    L.new(n2.outputs["Fac"], rr.inputs[0]); rough_out = rr.outputs[0]
    bump = N.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = bstr
    bump.inputs["Distance"].default_value = 0.02
    n3 = noise(N, bscale, 4, 0.7, co, L)
    height = n3.outputs["Fac"]
    if brick:
        w, h, mort, off = brick[:4]
        bt = N.new("ShaderNodeTexBrick"); bt.offset = off
        bt.inputs["Scale"].default_value = 1.0; bt.inputs["Brick Width"].default_value = w
        bt.inputs["Row Height"].default_value = h; bt.inputs["Mortar Size"].default_value = mort
        bt.inputs["Mortar Smooth"].default_value = 0.3
        bt.inputs["Color1"].default_value = (1, 1, 1, 1); bt.inputs["Color2"].default_value = (0.8, 0.8, 0.8, 1)
        L.new(co, bt.inputs["Vector"])
        # per-block tint
        m2 = N.new("ShaderNodeMix"); m2.data_type = 'RGBA'; m2.blend_type = 'MULTIPLY'; m2.inputs["Factor"].default_value = 1
        L.new(col, m2.inputs[6]); L.new(bt.outputs["Color"], m2.inputs[7])
        dark = N.new("ShaderNodeMix"); dark.data_type = 'RGBA'
        L.new(bt.outputs["Fac"], dark.inputs["Factor"]); L.new(m2.outputs[2], dark.inputs[6])
        dark.inputs[7].default_value = (c0[0]*0.45, c0[1]*0.42, c0[2]*0.4, 1)
        col = dark.outputs[2]
        mx = N.new("ShaderNodeMath"); mx.operation = 'MAXIMUM'
        L.new(bt.outputs["Fac"], mx.inputs[0]); mx.inputs[1].default_value = 0
        rmax = N.new("ShaderNodeMath"); rmax.operation = 'MAXIMUM'
        L.new(rough_out, rmax.inputs[0]); L.new(bt.outputs["Fac"], rmax.inputs[1]); rough_out = rmax.outputs[0]
        hs = N.new("ShaderNodeMath"); hs.operation = 'MULTIPLY_ADD'
        L.new(bt.outputs["Fac"], hs.inputs[0]); hs.inputs[1].default_value = -1.5; L.new(height, hs.inputs[2])
        height = hs.outputs[0]
        if len(brick) > 4:  # drafted margin: second brick slightly wider mortar = recessed band
            bt2 = N.new("ShaderNodeTexBrick"); bt2.offset = off
            for k, v in (("Scale", 1.0), ("Brick Width", w), ("Row Height", h), ("Mortar Size", brick[4]), ("Mortar Smooth", 0.1)):
                bt2.inputs[k].default_value = v
            L.new(co, bt2.inputs["Vector"])
            h2 = N.new("ShaderNodeMath"); h2.operation = 'MULTIPLY_ADD'
            L.new(bt2.outputs["Fac"], h2.inputs[0]); h2.inputs[1].default_value = -0.5; L.new(height, h2.inputs[2])
            height = h2.outputs[0]
            # boss face a bit rougher/darker
            bt.inputs["Mortar Smooth"].default_value = 0.1
    if cracks:
        v = N.new("ShaderNodeTexVoronoi"); v.feature = 'DISTANCE_TO_EDGE'; v.inputs["Scale"].default_value = 1.3
        v.inputs["Randomness"].default_value = 1.0
        wn = noise(N, 3.0, 4, 0.5, co, L)
        vm = N.new("ShaderNodeVectorMath"); vm.operation = 'MULTIPLY_ADD'
        L.new(wn.outputs["Color"], vm.inputs[0]); vm.inputs[1].default_value = (0.15, 0.15, 0.15); L.new(co, vm.inputs[2])
        L.new(vm.outputs[0], v.inputs["Vector"])
        cr = N.new("ShaderNodeMapRange"); cr.inputs[1].default_value = 0.0; cr.inputs[2].default_value = 0.012
        cr.inputs[3].default_value = 1.0; cr.inputs[4].default_value = 0.0
        L.new(v.outputs["Distance"], cr.inputs[0])
        mask = noise(N, 0.8, 2, 0.5, co, L)
        mr = N.new("ShaderNodeMapRange"); mr.inputs[1].default_value = 0.5; mr.inputs[2].default_value = 0.6
        L.new(mask.outputs["Fac"], mr.inputs[0])
        cm = N.new("ShaderNodeMath"); cm.operation = 'MULTIPLY'
        L.new(cr.outputs[0], cm.inputs[0]); L.new(mr.outputs[0], cm.inputs[1])
        dc = N.new("ShaderNodeMix"); dc.data_type = 'RGBA'; L.new(cm.outputs[0], dc.inputs["Factor"])
        L.new(col, dc.inputs[6]); dc.inputs[7].default_value = (0.12, 0.1, 0.08, 1); col = dc.outputs[2]
        h3 = N.new("ShaderNodeMath"); h3.operation = 'MULTIPLY_ADD'
        L.new(cm.outputs[0], h3.inputs[0]); h3.inputs[1].default_value = -0.6; L.new(height, h3.inputs[2]); height = h3.outputs[0]
        # worn polish: smoother patches
        wr = noise(N, 0.35, 3, 0.5, co, L)
        wm = N.new("ShaderNodeMapRange"); wm.inputs[1].default_value = 0.4; wm.inputs[2].default_value = 0.65
        wm.inputs[3].default_value = 0.0; wm.inputs[4].default_value = -0.25
        L.new(wr.outputs["Fac"], wm.inputs[0])
        ad = N.new("ShaderNodeMath"); ad.operation = 'ADD'; L.new(rough_out, ad.inputs[0]); L.new(wm.outputs[0], ad.inputs[1])
        rough_out = ad.outputs[0]
    L.new(height, bump.inputs["Height"])
    L.new(col, b.inputs["Base Color"]); L.new(rough_out, b.inputs["Roughness"]); L.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m

LIME = (0.55, 0.48, 0.37); LIME2 = (0.72, 0.66, 0.54)
M_COL = stone_mat("M_ColumnLimestone", LIME, LIME2, (0.5, 0.75), 5.0, 0.2)
M_FLOOR = stone_mat("M_FloorSlabs", (0.42, 0.38, 0.3), (0.68, 0.62, 0.5), (0.45, 0.9), 8.0, 0.35,
                    brick=(1.3, 1.0, 0.01, 0.37), cracks=True)
M_COURT = stone_mat("M_CourtPaving", (0.58, 0.53, 0.44), (0.76, 0.70, 0.59), (0.5, 0.85), 6.0, 0.2,
                    brick=(2.4, 1.5, 0.015, 0.5))
M_WALL = stone_mat("M_HerodianAshlar", (0.55, 0.49, 0.38), (0.74, 0.67, 0.54), (0.6, 0.9), 4.0, 0.4,
                   brick=(3.2, 1.05, 0.012, 0.31, 0.09))
M_STREETWALL = stone_mat("M_StreetStone", (0.48, 0.42, 0.33), (0.66, 0.6, 0.48), (0.65, 0.95), 5.0, 0.4,
                         brick=(0.9, 0.45, 0.02, 0.5))
M_PLASTER = stone_mat("M_HousePlaster", (0.6, 0.55, 0.46), (0.75, 0.70, 0.60), (0.75, 0.95), 3.0, 0.3)
M_ROCK = stone_mat("M_LooseStone", (0.38, 0.34, 0.27), (0.68, 0.62, 0.5), (0.6, 0.9), 14.0, 0.5)

def cedar():
    m, nt, N, L, b = nodes_mat("M_CedarCoffer")
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1, 12, 1)
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    w = N.new("ShaderNodeTexWave"); w.inputs["Scale"].default_value = 3; w.inputs["Distortion"].default_value = 6
    w.inputs["Detail"].default_value = 4; L.new(mp.outputs[0], w.inputs["Vector"])
    r = ramp(N, (0.16, 0.07, 0.035), (0.36, 0.17, 0.08), 0.2, 0.9); L.new(w.outputs["Fac"], r.inputs["Fac"])
    L.new(r.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.55
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.1
    L.new(w.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m
M_CEDAR = cedar()
M_DARK = principled("M_DoorwayShadow", (0.03, 0.025, 0.02), 0.9)
M_WOODDOOR = principled("M_WoodDoor", (0.18, 0.1, 0.05), 0.7)

# ---------------- geometry helpers ----------------
def obj_from_bm(name, bm, mat, smooth_angle=None, col=SET):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me); col.objects.link(o)
    if smooth_angle:
        for p in me.polygons: p.use_smooth = True
        me.set_sharp_from_angle(angle=math.radians(smooth_angle))
    return o

def box(bm, center, size):
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation(center) @ Matrix.Diagonal((*size, 1)))

def box_obj(name, center, size, mat, bevel=0.0, col=SET):
    bm = bmesh.new(); box(bm, center, size); o = obj_from_bm(name, bm, mat, col=col)
    if bevel:
        md = o.modifiers.new("Bevel", 'BEVEL'); md.width = bevel; md.segments = 2; md.limit_method = 'ANGLE'
    return o

def lathe(bm, profile, seg=32):
    rings = []
    for r, z in profile:
        ring = [bm.verts.new((r*math.cos(2*math.pi*i/seg), r*math.sin(2*math.pi*i/seg), z)) for i in range(seg)]
        rings.append(ring)
    for a, b2 in zip(rings, rings[1:]):
        for i in range(seg):
            j = (i+1) % seg; bm.faces.new((a[i], a[j], b2[j], b2[i]))
    bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])

# ---------------- column (one shared mesh, linked instances) ----------------
H_COL = 9.0
def column_mesh():
    bm = bmesh.new()
    box(bm, (0, 0, 0.15), (1.3, 1.3, 0.3))                       # plinth
    prof = [(0.62, 0.3), (0.62, 0.36), (0.6, 0.42), (0.56, 0.47), (0.5, 0.5), (0.5, 0.53), (0.54, 0.58),
            (0.54, 0.62), (0.49, 0.68), (0.47, 0.72), (0.45, 0.76)]
    shaft = []
    for k in range(9):
        t = k/8; shaft.append((0.45 - 0.05*t + 0.02*math.sin(math.pi*t), 0.76 + t*(7.55-0.76)))
    cap = [(0.43, 7.62), (0.45, 7.66), (0.41, 7.72), (0.43, 7.9), (0.5, 8.15), (0.6, 8.4), (0.72, 8.58), (0.78, 8.65)]
    lathe(bm, prof + shaft + cap, 32)
    # acanthus-ish leaves: small wedges around bell
    for i in range(8):
        a = 2*math.pi*i/8
        for lvl, (z, rad, hgt) in enumerate(((7.95, 0.48, 0.35), (8.25, 0.58, 0.3))):
            aa = a + (math.pi/8 if lvl else 0)
            m = Matrix.Translation((rad*math.cos(aa), rad*math.sin(aa), z)) @ Matrix.Rotation(aa, 4, 'Z') @ \
                Matrix.Rotation(math.radians(-25), 4, 'Y') @ Matrix.Diagonal((0.08, 0.22, hgt, 1))
            bmesh.ops.create_cube(bm, size=1.0, matrix=m)
    box(bm, (0, 0, 8.775), (1.7, 1.7, 0.25))                     # abacus
    me = bpy.data.meshes.new("ME_Column"); bm.to_mesh(me); bm.free()
    me.materials.append(M_COL)
    for p in me.polygons: p.use_smooth = True
    me.set_sharp_from_angle(angle=math.radians(35))
    return me
ME_COL = column_mesh()
XS = [-18 + 4*i for i in range(10)]
for row, y in (("IN", 1.8), ("OUT", -2.2)):
    for i, x in enumerate(XS):
        o = bpy.data.objects.new(f"COLUMN_{row}_{i+1:02d}", ME_COL); SET.objects.link(o)
        o.location = (x, y, 0); o.rotation_euler.z = random.uniform(0, 1)

# ---------------- floor, wall, ceiling ----------------
box_obj("FLOOR_Colonnade", (0.5, 0.4, -0.75), (41.0, 6.6, 1.5), M_FLOOR, 0.02)       # x -20..21, y -2.9..3.7
box_obj("WALL_Herodian", (0, 4.6, 6.5), (44.0, 1.8, 13.0), M_WALL)                     # face at y=3.7
box_obj("CURB_Court", (-19.5, -3.0, 0.08), (79, 0.3, 0.16), M_COURT, 0.03)
box_obj("ARCHITRAVE_Out", (0.5, -2.2, 9.35), (41.0, 1.4, 0.7), M_COL, 0.03)
box_obj("ARCHITRAVE_In", (0.5, 1.8, 9.35), (41.0, 1.4, 0.7), M_COL, 0.03)
box_obj("CORNICE_Out", (0.5, -2.45, 9.85), (41.2, 1.3, 0.3), M_COL, 0.03)
box_obj("ROOF_Slab", (0.5, 0.75, 10.15), (41.4, 7.0, 0.3), M_COL)
bm = bmesh.new()
box(bm, (0.5, 0.75, 9.9), (41.0, 7.0, 0.2))                    # cedar deck
for i in range(42):                                            # cross beams
    box(bm, (-20 + i, 0.75, 9.72), (0.22, 7.0, 0.18))
for y in (-0.6, 0.75, 2.4):                                    # longitudinal beams (coffers)
    box(bm, (0.5, y, 9.7), (41.0, 0.26, 0.24))
CEIL = obj_from_bm("CEILING_Cedar", bm, M_CEDAR)
md = CEIL.modifiers.new("Bevel", 'BEVEL'); md.width = 0.015; md.segments = 1

# ---------------- court & distant city ----------------
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1,
                                       matrix=Matrix.Translation((-20, -63, 0)) @ Matrix.Diagonal((82, 60, 1, 1)))
obj_from_bm("COURT_Paving", bm, M_COURT)
def haze_mat(i, t):
    base = Vector((0.66, 0.6, 0.5)); sky = Vector((0.72, 0.78, 0.86))
    c = base.lerp(sky, t)
    m = principled(f"M_Haze_{i}", tuple(c), 0.9)
    m.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (*c, 1)
    m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 0.25*t
    return m
for i in range(18):
    d = random.uniform(55, 170); x = random.uniform(-110, 70)
    t = min(1, (d-50)/130)
    w, dp, h = random.uniform(8, 30), random.uniform(6, 15), random.uniform(5, 18)
    box_obj(f"DISTANT_Building_{i+1:02d}", (x, -d, h/2), (w, dp, h), haze_mat(i, 0.25+0.6*t)).visible_shadow = False
box_obj("DISTANT_Sanctuary", (-30, -85, 22), (24, 30, 44), haze_mat(99, 0.45)).visible_shadow = False
box_obj("COURT_Soreg", (-20, -30, 0.7), (60, 0.4, 1.4), M_COURT, 0.04)   # low balustrade
box_obj("COURT_FarWall", (-20, -95, 8), (200, 3, 16), haze_mat(98, 0.6)).visible_shadow = False

# ---------------- street end (x=+21) ----------------
ZS = -1.5
bm = bmesh.new()
for k in range(6):
    top = -0.25*(k+1); x0 = 21 + 0.4*k
    box(bm, (x0 + 0.2, 0.4, (top + ZS - 0.3)/2), (0.4, 5.0, top - (ZS - 0.3)))
o = obj_from_bm("STEPS_Street", bm, M_FLOOR); m_ = o.modifiers.new("Bevel", 'BEVEL'); m_.width = 0.02; m_.segments = 2
box_obj("STREET_Paving", (29.4, 0.0, ZS - 0.15), (16.8, 7.0, 0.3), M_STREETWALL)       # x 21..37.8
box_obj("STREET_CityWall", (30, 3.4, ZS + 4.5), (18, 1.6, 9.0), M_STREETWALL)
box_obj("STREET_WallParapet", (30, 3.0, ZS + 9.25), (18, 0.8, 0.5), M_STREETWALL, 0.03)
box_obj("STREET_SideWall_S", (21.0, -2.6, ZS + 0.9), (0.4, 1.4, 4.8), M_STREETWALL)
for i, (x, w, h) in enumerate([(24.5, 3.4, 5.2), (28.2, 3.8, 6.4), (32.0, 3.5, 4.6), (35.6, 3.6, 5.8)]):
    box_obj(f"HOUSE_{i+1}", (x, -4.6, ZS + h/2), (w, 3.6, h), M_PLASTER, 0.04)
    box_obj(f"HOUSE_{i+1}_Door", (x - 0.6, -2.82, ZS + 1.0), (0.95, 0.1, 2.0), M_WOODDOOR)
    box_obj(f"HOUSE_{i+1}_Window", (x + 0.8, -2.82, ZS + h - 1.6), (0.5, 0.1, 0.7), M_DARK)
    box_obj(f"HOUSE_{i+1}_Lintel", (x - 0.6, -2.75, ZS + 2.12), (1.3, 0.2, 0.25), M_STREETWALL, 0.02)
box_obj("STREET_EndHouse", (39, 0, ZS + 3.5), (2, 7, 7), M_PLASTER, 0.04)

# ---------------- stones ----------------
def rock(name, loc, size):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    sx, sy, sz = size*random.uniform(0.8, 1.2), size*random.uniform(0.7, 1.1), size*random.uniform(0.5, 0.8)
    for v in bm.verts:
        v.co *= 1 + random.uniform(-0.12, 0.12)
        v.co.x *= sx; v.co.y *= sy; v.co.z *= sz
    bm.transform(Matrix.Rotation(random.uniform(0, 6.28), 4, 'Z'))
    o = obj_from_bm(name, bm, M_ROCK, smooth_angle=50)
    o.location = (loc[0], loc[1], sz*0.7)
    return o
n = 0
for x in XS:
    for y in (1.8, -2.2):
        if random.random() < 0.55:
            for _ in range(random.randint(1, 2)):
                a = random.uniform(0, 6.28); n += 1
                rock(f"STONE_Loose_{n:02d}", (x + 0.85*math.cos(a), y + 0.85*math.sin(a)), random.uniform(0.04, 0.07))
while n < 26:
    n += 1; rock(f"STONE_Loose_{n:02d}", (random.uniform(-19, 19), random.uniform(3.2, 3.6)), random.uniform(0.04, 0.07))
for i, p in enumerate([(0.85, -1.95), (1.55, -1.0), (-0.85, -1.75), (-1.7, -0.7)]):
    rock(f"PROP_STONE_{i+1}", p, random.uniform(0.05, 0.065))

# ---------------- marks ----------------
MARKS = {"JESUS": (0, 0, 0), "ELDER": (0.35, -1.25, 180), "YOUNG": (-0.55, -1.65, 170), "PH2": (1.15, -1.5, 200),
         "PH3": (-1.25, -1.1, 150), "JOHN": (-0.9, 0.55, -20), "PETER": (-1.55, 0.35, -30)}
ST = {"JESUS_ST": (24, -0.5, 90), "PETER_ST": (23.2, -0.9, -80), "JOHN_ST": (23.4, 0.2, -110)}
for r, (x, y, a) in MARKS.items(): mark(r, (x, y, 0), a, SET)
for r, (x, y, a) in ST.items(): mark(r, (x, y, ZS), a, SET)

# ---------------- lighting ----------------
W = bpy.data.worlds.new("W_colonnade"); scn.world = W; W.use_nodes = True
N = W.node_tree.nodes; bg = N["Background"]
sky = N.new("ShaderNodeTexSky"); sky.sky_type = 'NISHITA'
ELEV, AZ = math.radians(18), math.radians(58)      # sun from -Y, swung 58 deg toward +X
sky.sun_elevation = ELEV; sky.sun_rotation = math.radians(180) - AZ  # sun dir = (sin r? ) tuned visually
sky.sun_disc = False; sky.air_density = 1.6; sky.dust_density = 3.0; sky.altitude = 750
ov = N.new("ShaderNodeMix"); ov.data_type = "RGBA"; ov.inputs["Factor"].default_value = 0.55
W.node_tree.links.new(sky.outputs["Color"], ov.inputs[6]); ov.inputs[7].default_value = (5.5, 5.8, 6.6, 1)
W.node_tree.links.new(ov.outputs[2], bg.inputs["Color"]); bg.inputs["Strength"].default_value = 0.13
sd = bpy.data.lights.new("SUN", 'SUN'); sd.energy = 6.0; sd.color = (1.0, 0.86, 0.68); sd.angle = math.radians(1.5)
sun = bpy.data.objects.new("SUN", sd); LIG.objects.link(sun)
dfrom = Vector((math.sin(AZ)*math.cos(ELEV), -math.cos(AZ)*math.cos(ELEV), math.sin(ELEV)))
sun.rotation_euler = (-dfrom).to_track_quat('-Z', 'Y').to_euler(); sun.location = (5, -20, 15)
# animation hook empties
ctrl = bpy.data.objects.new("LIGHT_CTRL", None); LIG.objects.link(ctrl); ctrl.location = (0, -3, 12)
ctrl["sun_energy"] = 6.0; ctrl["sky_strength"] = 0.13
for prop, path, tgt in (("sun_energy", "energy", sd), ("sky_strength", 'nodes["Background"].inputs[1].default_value', W.node_tree)):
    fc = tgt.driver_add(path); d = fc.driver; d.type = 'AVERAGE'
    v = d.variables.new(); v.name = "x"; v.targets[0].id = ctrl; v.targets[0].data_path = f'["{prop}"]'

# ---------------- cameras ----------------
camhint("CU_JESUS", (-0.15, -2.3, 1.62), (0, 0, 1.6), 85, SET)
camhint("CU_ELDER", (0.45, 0.75, 1.68), (0.35, -1.25, 1.6), 85, SET)
camhint("WIDE_TINY", (5.0, -24.0, 1.3), (0, 0, 4.2), 24, SET)
camhint("STONES_CU", (0.3, -2.75, 0.2), (0.85, -1.95, 0.05), 50, SET)
camhint("STREET", (31.0, -2.0, ZS + 2.0), (23.6, -0.2, ZS + 1.4), 35, SET)
scn.camera = bpy.data.objects["CAMHINT_WIDE_TINY"]

# render defaults
scn.render.engine = 'CYCLES'; scn.cycles.device = 'CPU'; scn.cycles.samples = 8; scn.cycles.use_denoising = True
scn.cycles.max_bounces = 3; scn.cycles.diffuse_bounces = 1; scn.cycles.glossy_bounces = 1; scn.cycles.transmission_bounces = 0; scn.cycles.use_light_tree = False
scn.render.resolution_x, scn.render.resolution_y = 540, 960
scn.view_settings.view_transform = 'AgX'; scn.view_settings.look = 'AgX - Medium High Contrast'

if PREVIEW:
    for r, (x, y, a) in MARKS.items(): stand_in_figure((x, y), a, col=SET)
    for r, (x, y, a) in ST.items():
        for o in stand_in_figure((x, y), a, col=SET): o.location.z += ZS
    render_previews("colonnade")
save(out_path())
