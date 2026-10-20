import sys; sys.path.insert(0, "/home/user/game1/video/pipeline/sets"); from _common import *
import bpy, math

scn = reset_scene()
scn.render.fps = 24; scn.frame_start = 1; scn.frame_end = 192
scn.render.resolution_x, scn.render.resolution_y = 540, 960
SET = collection("SET_cosmos"); LIG = collection("LIGHTS_cosmos")

ctrl = bpy.data.objects.new("COSMOS_CTRL", None); SET.objects.link(ctrl)
ctrl["reveal"] = 0.0
ctrl.id_properties_ui("reveal").update(min=0.0, max=1.0, soft_min=0.0, soft_max=1.0)
for f, v in ((1, 0.0), (192, 1.0)):
    ctrl["reveal"] = v; ctrl.keyframe_insert('["reveal"]', frame=f)
for fc in ctrl.animation_data.action.fcurves:
    k = fc.keyframe_points[0]; k.interpolation = 'SINE'; k.easing = 'EASE_IN'

def drv_value(nt, expr, label):
    """Value node driven by COSMOS_CTRL['reveal'] (variable r)."""
    n = nt.nodes.new("ShaderNodeValue"); n.label = label
    d = n.outputs[0].driver_add("default_value").driver
    d.type = 'SCRIPTED'
    v = d.variables.new(); v.name = "r"; v.type = 'SINGLE_PROP'
    v.targets[0].id = ctrl; v.targets[0].data_path = '["reveal"]'
    d.expression = expr
    return n.outputs[0]

def M(nt, op, a, b=None, clamp=False):
    n = nt.nodes.new("ShaderNodeMath"); n.operation = op; n.use_clamp = clamp
    for i, x in enumerate((a, b)):
        if x is None: continue
        if isinstance(x, (int, float)): n.inputs[i].default_value = x
        else: nt.links.new(x, n.inputs[i])
    return n.outputs[0]

def ramp(nt, fac, stops):
    n = nt.nodes.new("ShaderNodeValToRGB"); el = n.color_ramp.elements
    el[0].position, el[0].color = stops[0][0], (*stops[0][1], 1)
    el[1].position, el[1].color = stops[-1][0], (*stops[-1][1], 1)
    for p, c in stops[1:-1]:
        e = el.new(p); e.color = (*c, 1)
    nt.links.new(fac, n.inputs[0]); return n.outputs[0]

def emissive_transparent(name, color_sock_fn, alpha_fn):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    col, strength = color_sock_fn(nt)
    alpha = alpha_fn(nt)
    em = nt.nodes.new("ShaderNodeEmission"); nt.links.new(col, em.inputs[0]); nt.links.new(strength, em.inputs[1])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    ad = nt.nodes.new("ShaderNodeAddShader")
    # emission added on top of transparency (additive glow), alpha only scales emission
    mul = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(alpha, mul.inputs[0])
    nt.links.new(tr.outputs[0], ad.inputs[0]); nt.links.new(em.outputs[0], ad.inputs[1])
    nt.links.new(tr.outputs[0], mul.inputs[1]); nt.links.new(ad.outputs[0], mul.inputs[2])
    nt.links.new(mul.outputs[0], out.inputs[0])
    return m

def plane(name, loc, size, rot=(90, 0, 0), mat=None):
    bpy.ops.mesh.primitive_plane_add(size=size, location=loc)
    o = bpy.context.object; o.name = name
    o.rotation_euler = [math.radians(a) for a in rot]
    link(o, SET); o.data.materials.append(mat)
    o.visible_shadow = False
    o.visible_diffuse = False; o.visible_glossy = False
    return o

# ---------------- world starfield ----------------
w = bpy.data.worlds.new("W_cosmos"); scn.world = w; w.use_nodes = True
nt = w.node_tree; nt.nodes.clear()
wo = nt.nodes.new("ShaderNodeOutputWorld"); bg = nt.nodes.new("ShaderNodeBackground")
tc = nt.nodes.new("ShaderNodeTexCoord")
def stars(scale, size, thresh):
    v = nt.nodes.new("ShaderNodeTexVoronoi"); v.inputs["Scale"].default_value = scale
    v.inputs["Randomness"].default_value = 1.0
    nt.links.new(tc.outputs["Generated"], v.inputs["Vector"])
    core = M(nt, 'SUBTRACT', 1.0, M(nt, 'DIVIDE', v.outputs["Distance"], size), clamp=True)
    core = M(nt, 'POWER', core, 3.0)
    sep = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(v.outputs["Color"], sep.inputs[0])
    keep = M(nt, 'GREATER_THAN', sep.outputs[0], thresh)
    bright = M(nt, 'POWER', sep.outputs[1], 3.0)
    return M(nt, 'MULTIPLY', M(nt, 'MULTIPLY', core, keep), M(nt, 'ADD', M(nt, 'MULTIPLY', bright, 6.0), 0.3)), sep.outputs[2]
s1, hue = stars(110.0, 0.17, 0.5)
s2, _ = stars(320.0, 0.2, 0.35)
dens = nt.nodes.new("ShaderNodeTexNoise"); dens.inputs["Scale"].default_value = 3.0; dens.inputs["Detail"].default_value = 4
nt.links.new(tc.outputs["Generated"], dens.inputs["Vector"])
dmask = M(nt, 'POWER', M(nt, 'MULTIPLY', dens.outputs["Fac"], 1.6, clamp=True), 2.5)
st = M(nt, 'MULTIPLY', M(nt, 'ADD', s1, M(nt, 'MULTIPLY', s2, 0.6)), M(nt, 'ADD', dmask, 0.15))
starcol = ramp(nt, hue, [(0.0, (1.0, 0.75, 0.55)), (0.5, (1, 1, 1)), (1.0, (0.65, 0.8, 1.0))])
mixc = nt.nodes.new("ShaderNodeVectorMath"); mixc.operation = 'SCALE'
nt.links.new(starcol, mixc.inputs[0]); nt.links.new(st, mixc.inputs["Scale"])
k = drv_value(nt, "max(0.0,(r-0.3)/0.7)**1.6*5.0", "star_strength")
nt.links.new(mixc.outputs[0], bg.inputs[0]); nt.links.new(k, bg.inputs[1])
nt.links.new(bg.outputs[0], wo.inputs[0])

# ---------------- nebula planes ----------------
def nebula(name, loc, size, rot, c1, c2, scale, seed, expr, vor=False):
    def col(nt):
        tc = nt.nodes.new("ShaderNodeTexCoord")
        n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = scale
        n.inputs["Detail"].default_value = 8; n.inputs["Roughness"].default_value = 0.62
        n.noise_dimensions = '4D'; n.inputs["Distortion"].default_value = 0.6; n.inputs["W"].default_value = seed
        nt.links.new(tc.outputs["Object"], n.inputs["Vector"])
        nt["_n"] = 0
        c = ramp(nt, n.outputs["Fac"], [(0.35, c2), (0.6, c1), (0.75, (1.0, 0.95, 0.85))])
        return c, drv_value(nt, expr, "neb_strength")
    def alpha(nt):
        tc = [x for x in nt.nodes if x.type == 'TEX_COORD'][0]
        n = [x for x in nt.nodes if x.type == 'TEX_NOISE'][0]
        a = M(nt, 'MULTIPLY', M(nt, 'SUBTRACT', n.outputs["Fac"], 0.42), 3.0, clamp=True)
        if vor:
            v = nt.nodes.new("ShaderNodeTexVoronoi"); v.feature = 'F1'; v.inputs["Scale"].default_value = scale * 1.6
            nt.links.new(tc.outputs["Object"], v.inputs["Vector"])
            a = M(nt, 'MULTIPLY', a, M(nt, 'ADD', M(nt, 'MULTIPLY', v.outputs["Distance"], 1.2), 0.2, clamp=True))
        # radial falloff so the plane edges vanish
        g = nt.nodes.new("ShaderNodeTexGradient"); g.gradient_type = 'QUADRATIC_SPHERE'
        mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (2.0, 2.0, 2.0)
        nt.links.new(tc.outputs["Object"], mp.inputs[0]); nt.links.new(mp.outputs[0], g.inputs[0])
        sx = nt.nodes.new("ShaderNodeVectorMath"); sx.operation = 'SCALE'
        nt.links.new(tc.outputs["Object"], sx.inputs[0]); sx.inputs["Scale"].default_value = 2.0 / size
        nt.links.new(sx.outputs[0], g.inputs[0])
        return M(nt, 'MULTIPLY', a, M(nt, 'POWER', g.outputs[1], 1.5))
    m = emissive_transparent("M_" + name, col, alpha)
    return plane(name, loc, size, rot, m)

NEB = "max(0.0,(r-0.35)/0.65)**1.3*{k}"
nebula("NEB_violet", (-10, 160, 20), 240, (90, 0, 15), (0.35, 0.08, 0.9), (0.04, 0.0, 0.12), 0.012, 1.3, NEB.format(k=0.9))
nebula("NEB_teal", (25, 120, -15), 170, (90, 0, -30), (0.05, 0.75, 0.75), (0.0, 0.08, 0.12), 0.016, 4.2, NEB.format(k=1.1), vor=True)
nebula("NEB_gold", (-12, 90, 8), 120, (90, 0, 50), (1.0, 0.6, 0.15), (0.2, 0.05, 0.0), 0.022, 7.7, NEB.format(k=1.5))
# swirling dust: faint at reveal 0, rotates via driver on rotation
dust = nebula("NEB_dust", (0, 60, 0), 80, (90, 0, 0), (0.55, 0.45, 0.4), (0.03, 0.02, 0.03), 0.04, 2.0, "0.16+0.2*r", vor=True)
fc = dust.driver_add("rotation_euler", 1); fc.driver.expression = "frame*0.004"

# ---------------- spiral galaxies ----------------
def galaxy(name, loc, size, rot, tint, expr, arms=2):
    def col(nt):
        tc = nt.nodes.new("ShaderNodeTexCoord")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Generated"], sep.inputs[0])
        x = M(nt, 'SUBTRACT', sep.outputs[0], 0.5); y = M(nt, 'SUBTRACT', sep.outputs[1], 0.5)
        r = M(nt, 'MULTIPLY', M(nt, 'SQRT', M(nt, 'ADD', M(nt, 'MULTIPLY', x, x), M(nt, 'MULTIPLY', y, y))), 2.0)
        ang = M(nt, 'ARCTAN2', y, x)
        n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 9; n.inputs["Detail"].default_value = 5
        nt.links.new(tc.outputs["Generated"], n.inputs["Vector"])
        ph = M(nt, 'ADD', M(nt, 'MULTIPLY', ang, float(arms)), M(nt, 'MULTIPLY', M(nt, 'LOGARITHM', M(nt, 'ADD', r, 0.02), 2.718), -7.0))
        ph = M(nt, 'ADD', ph, M(nt, 'MULTIPLY', n.outputs["Fac"], 2.0))
        arm = M(nt, 'POWER', M(nt, 'MULTIPLY', M(nt, 'ADD', M(nt, 'SINE', ph), 1.0), 0.5), 3.0)
        fall = M(nt, 'POWER', M(nt, 'SUBTRACT', 1.0, r, clamp=True), 2.0)
        core = M(nt, 'POWER', M(nt, 'SUBTRACT', 1.0, M(nt, 'MULTIPLY', r, 5.0), clamp=True), 2.0)
        inten = M(nt, 'ADD', M(nt, 'MULTIPLY', M(nt, 'MULTIPLY', arm, fall), M(nt, 'MULTIPLY', n.outputs["Fac"], 1.4)), M(nt, 'MULTIPLY', core, 3.0))
        nt["_inten"] = 1
        cm = nt.nodes.new("ShaderNodeMix"); cm.data_type = 'RGBA'
        cm.inputs[6].default_value = (*tint, 1); cm.inputs[7].default_value = (1.0, 0.85, 0.6, 1)
        nt.links.new(core, cm.inputs[0])
        sc = nt.nodes.new("ShaderNodeVectorMath"); sc.operation = 'SCALE'
        nt.links.new(cm.outputs[2], sc.inputs[0]); nt.links.new(inten, sc.inputs["Scale"])
        galaxy.inten = inten
        return sc.outputs[0], drv_value(nt, expr, "gal_strength")
    def alpha(nt):
        return M(nt, 'MULTIPLY', galaxy.inten, 1.5, clamp=True)
    return plane(name, loc, size, rot, emissive_transparent("M_" + name, col, alpha))

GAL = "max(0.0,(r-0.45)/0.55)*{k}"
galaxy("GALAXY_A", (14, 140, 32), 30, (70, 10, 30), (0.6, 0.75, 1.0), GAL.format(k=3.0))
galaxy("GALAXY_B", (-20, 175, -30), 22, (60, -20, -40), (0.9, 0.7, 1.0), GAL.format(k=2.5), arms=3)

# ---------------- central light ----------------
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.6, location=(0, 40, 0), segments=32, ring_count=16)
sph = bpy.context.object; sph.name = "LIGHT_CORE"; link(sph, SET)
m = bpy.data.materials.new("M_core"); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission")
em.inputs[0].default_value = (1.0, 0.9, 0.75, 1)
CORE = "min(1.0,max(0.0,(r-0.1)/0.12))*(25+40*r)"
nt.links.new(drv_value(nt, CORE, "core_strength"), em.inputs[1]); nt.links.new(em.outputs[0], out.inputs[0])
sph.data.materials.append(m)
sc = sph.driver_add("scale")
for f in sc:
    f.driver.type = 'SCRIPTED'; v = f.driver.variables.new(); v.name = "r"
    v.targets[0].id = ctrl; v.targets[0].data_path = '["reveal"]'
    f.driver.expression = "max(0.05,min(1.0,(r-0.1)/0.15))"

def halo_col(nt):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    l = nt.nodes.new("ShaderNodeVectorMath"); l.operation = 'LENGTH'
    nt.links.new(tc.outputs["Object"], l.inputs[0])
    d = M(nt, 'DIVIDE', 1.0, M(nt, 'ADD', M(nt, 'MULTIPLY', M(nt, 'POWER', l.outputs["Value"], 2.0), 0.25), 0.04))
    edge = M(nt, 'SUBTRACT', 1.0, M(nt, 'DIVIDE', l.outputs["Value"], 15.0), clamp=True)
    halo_col.d = M(nt, 'MULTIPLY', d, M(nt, 'MULTIPLY', edge, edge))
    c = nt.nodes.new("ShaderNodeVectorMath"); c.operation = 'SCALE'
    c.inputs[0].default_value = (1.0, 0.82, 0.6)
    nt.links.new(halo_col.d, c.inputs["Scale"])
    return c.outputs[0], drv_value(nt, "min(1.0,max(0.0,(r-0.1)/0.15))*(0.12+0.15*r)", "halo_strength")
hm = emissive_transparent("M_halo", halo_col, lambda nt: M(nt, 'MULTIPLY', halo_col.d, 1.0, clamp=True))
halo = plane("LIGHT_HALO", (0, 40.7, 0), 30, (90, 0, 0), hm)

# faint fill point light (for any characters later); driven energy
pl = bpy.data.lights.new("KEY_core", 'POINT'); pl.energy = 0; pl.shadow_soft_size = 0.6
plo = bpy.data.objects.new("KEY_core", pl); LIG.objects.link(plo); plo.location = (0, 38.5, 0)
fd = pl.driver_add("energy").driver; v = fd.variables.new(); v.name = "r"
v.targets[0].id = ctrl; v.targets[0].data_path = '["reveal"]'
fd.expression = "min(1.0,max(0.0,(r-0.1)/0.15))*200000"

# ---------------- camera ----------------
cam = camhint("MAIN", (0, -6, 0), (0, 40, 0), lens=35.0, col=SET)
cam.data.clip_end = 1000
scn.camera = cam
for f, y, roll in ((1, -6.0, -2.0), (192, 6.0, 3.0)):
    cam.location.y = y; cam.rotation_euler = (math.radians(90), math.radians(roll), 0)
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)
for fc in cam.animation_data.action.fcurves:
    for kp in fc.keyframe_points: kp.interpolation = 'BEZIER'

scn.cycles.transparent_max_bounces = 8
w.cycles.sampling_method = "NONE"
for mm in bpy.data.materials:
    if mm.name != "M_core": mm.cycles.emission_sampling = "NONE"
scn.render.film_transparent = False

frames = [int(a) for a in os.environ.get("PREV", "").split(",") if a]
for f in frames:
    scn.frame_set(f); render_previews(f"cosmos_f{f:03d}")
p = out_path()
if p: save(p)
