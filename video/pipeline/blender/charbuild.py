"""Build one character .blend from a spec: MPFB human + face shape keys + grooming + clothing.

Usage: blender -b -P charbuild.py -- NAME [--preview]
Output: /opt/work/chars/NAME.blend with collection CHAR_NAME containing NAME.rig and its meshes.
"""
import bpy, bmesh, sys, os, math, random
import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(__file__))
from charspecs import SPECS
from bl_ext.user_default.mpfb.services import HumanService, FaceService

OUT = "/opt/work/chars"

TORSO = {"root", "spine01", "spine02", "spine03", "spine04", "spine05", "clavicle.L", "clavicle.R",
         "shoulder01.L", "shoulder01.R", "breast.L", "breast.R", "pelvis.L", "pelvis.R"}
ARMS = {"upperarm01.L", "upperarm01.R", "upperarm02.L", "upperarm02.R",
        "lowerarm01.L", "lowerarm01.R", "lowerarm02.L", "lowerarm02.R"}
NECK = {"neck01", "neck02", "neck03"}
LEGS = {"upperleg01.L", "upperleg01.R", "upperleg02.L", "upperleg02.R",
        "lowerleg01.L", "lowerleg01.R", "lowerleg02.L", "lowerleg02.R"}


# ----------------------------------------------------------------------------- utilities

def clear():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)


def mix_coords(obj):
    """Rest-pose vertex coordinates with the current shape-key mix applied."""
    me = obj.data
    n = len(me.vertices)
    kb = me.shape_keys.key_blocks if me.shape_keys else None
    co = np.zeros(n * 3, dtype=np.float32)
    if not kb:
        me.vertices.foreach_get("co", co)
        return co.reshape(n, 3)
    basis = np.zeros(n * 3, dtype=np.float32)
    kb[0].data.foreach_get("co", basis)
    co[:] = basis
    tmp = np.zeros(n * 3, dtype=np.float32)
    for k in kb[1:]:
        if abs(k.value) > 1e-6 and not k.mute:
            k.data.foreach_get("co", tmp)
            co += k.value * (tmp - basis)
    return co.reshape(n, 3)


def bone_weights(obj):
    """Return (names, W) where W[v, g] = weight of vertex v in group g."""
    names = [g.name for g in obj.vertex_groups]
    W = np.zeros((len(obj.data.vertices), len(names)), dtype=np.float32)
    for v in obj.data.vertices:
        for g in v.groups:
            W[v.index, g.group] = g.weight
    return names, W


def group_weight(names, W, subset):
    idx = [i for i, n in enumerate(names) if n in subset]
    return W[:, idx].sum(axis=1) if idx else np.zeros(W.shape[0])


def dominant(names, W, bone_set):
    """For each vertex, the name of its strongest weighted bone among deform bones."""
    deform = [i for i, n in enumerate(names) if not n.startswith(("joint-", "helper-")) and n not in
              ("HelperGeometry", "JointCubes", "Left", "Mid", "Right", "body", "nippleTip", "nipple", "lips", "ears", "scalp", "genitals")]
    sub = W[:, deform]
    best = np.argmax(sub, axis=1)
    return np.array([names[deform[b]] for b in best]), sub.max(axis=1)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def set_vgroup(obj, name, weights, threshold=1e-3):
    vg = obj.vertex_groups.get(name) or obj.vertex_groups.new(name=name)
    for i, w in enumerate(weights):
        if w > threshold:
            vg.add([i], float(min(1.0, w)), 'REPLACE')
    return vg


def bone_head(rig, name):
    return rig.matrix_world @ rig.data.bones[name].head_local


def make_material(name, color, rough=0.8, sheen=0.4, bump_scale=900.0, bump_strength=0.25, fold_strength=0.0,
                  stripes=None, knit=False, emission=None):
    """Fabric: base color with subtle weave noise, sheen, optional object-space stripes."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nodes, links = nt.nodes, nt.links
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Sheen Weight"].default_value = sheen
    bsdf.inputs["Sheen Roughness"].default_value = 0.5
    bsdf.inputs["Specular IOR Level"].default_value = 0.25
    tc = nodes.new("ShaderNodeTexCoord")
    # color variation
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 6.0
    noise.inputs["Detail"].default_value = 4.0
    links.new(tc.outputs["Object"], noise.inputs["Vector"])
    ramp = nodes.new("ShaderNodeValToRGB")
    c = color
    ramp.color_ramp.elements[0].color = (c[0] * 0.78, c[1] * 0.78, c[2] * 0.78, 1)
    ramp.color_ramp.elements[1].color = (min(1, c[0] * 1.12), min(1, c[1] * 1.12), min(1, c[2] * 1.12), 1)
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    color_out = ramp.outputs["Color"]
    if stripes:
        # stripes: list of (z0, z1, rgb) bands in object space (Z), applied over base
        for (z0, z1, rgb) in stripes:
            sep = nodes.new("ShaderNodeSeparateXYZ")
            links.new(tc.outputs["Object"], sep.inputs["Vector"])
            m1 = nodes.new("ShaderNodeMath"); m1.operation = 'GREATER_THAN'; m1.inputs[1].default_value = z0
            m2 = nodes.new("ShaderNodeMath"); m2.operation = 'LESS_THAN'; m2.inputs[1].default_value = z1
            links.new(sep.outputs["Z"], m1.inputs[0]); links.new(sep.outputs["Z"], m2.inputs[0])
            mul = nodes.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'
            links.new(m1.outputs[0], mul.inputs[0]); links.new(m2.outputs[0], mul.inputs[1])
            mix = nodes.new("ShaderNodeMix"); mix.data_type = 'RGBA'
            links.new(mul.outputs[0], mix.inputs["Factor"])
            links.new(color_out, mix.inputs["A"])
            mix.inputs["B"].default_value = (*rgb, 1)
            color_out = mix.outputs["Result"]
    links.new(color_out, bsdf.inputs["Base Color"])
    # weave / knit bump + large soft folds
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = bump_strength
    if knit:
        wave = nodes.new("ShaderNodeTexWave")
        wave.wave_type = 'BANDS'; wave.bands_direction = 'Z'
        wave.inputs["Scale"].default_value = 260.0
        wave.inputs["Distortion"].default_value = 2.0
        links.new(tc.outputs["Object"], wave.inputs["Vector"])
        h = wave.outputs["Fac"]
    else:
        fine = nodes.new("ShaderNodeTexNoise")
        fine.inputs["Scale"].default_value = bump_scale
        fine.inputs["Detail"].default_value = 2.0
        links.new(tc.outputs["Object"], fine.inputs["Vector"])
        h = fine.outputs["Fac"]
    if fold_strength > 0:
        folds = nodes.new("ShaderNodeTexNoise")
        folds.inputs["Scale"].default_value = 3.0
        folds.inputs["Detail"].default_value = 1.5
        mapping = nodes.new("ShaderNodeMapping")
        mapping.inputs["Scale"].default_value = (4.0, 4.0, 0.6)
        links.new(tc.outputs["Object"], mapping.inputs["Vector"])
        links.new(mapping.outputs["Vector"], folds.inputs["Vector"])
        add = nodes.new("ShaderNodeMath"); add.operation = 'MULTIPLY_ADD'
        add.inputs[1].default_value = fold_strength
        links.new(folds.outputs["Fac"], add.inputs[0]); links.new(h, add.inputs[2])
        h = add.outputs[0]
    links.new(h, bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


# ----------------------------------------------------------------------------- human

def build_human(name, spec):
    info = HumanService._create_default_human_info_dict()
    info["phenotype"].update(spec["phenotype"])
    info.update({
        "rig": "default",
        "eyes": "high-poly.mhclo",
        "eyebrows": spec.get("eyebrows", "eyebrow001") + ".mhclo",
        "eyelashes": spec.get("eyelashes", "eyelashes01") + ".mhclo",
        "teeth": "teeth_base.mhclo",
        "tongue": "tongue01.mhclo",
        "hair": (spec["hair"] + ".mhclo") if spec.get("hair") else "",
        "skin_mhmat": spec["skin"] + ".mhmat",
        "skin_material_type": "ENHANCED_SSS",
        "eyes_material_type": "PROCEDURAL_EYES",
    })
    s = HumanService.get_default_deserialization_settings()
    s["subdiv_levels"] = 1
    body = HumanService.deserialize_from_dict(info, s)
    FaceService.load_targets(body, load_microsoft_visemes=True, load_meta_visemes=False, load_arkit_faceunits=True)
    FaceService.interpolate_targets(body)
    rig = body.parent
    rig.name = name
    body.name = f"{name}.body"
    for o in rig.children:
        if o != body:
            base = o.name.split(".")[-1]
            o.name = f"{name}.{base}"
    return rig, body


def tune_materials(name, spec, rig):
    body = bpy.data.objects[f"{name}.body"]
    for slot in body.material_slots:
        m = slot.material
        if not m or not m.use_nodes:
            continue
        for n in m.node_tree.nodes:
            if n.type == 'GROUP' and "colorMixIn" in n.inputs:
                m.name = f"{name}.skin"
                n.node_tree = n.node_tree.copy()
                n.node_tree.name = f"{name}.skin_group"
                mixn = next((x for x in n.node_tree.nodes if x.type == 'MIX_RGB'), None)
                mult = spec.get("skin_mult")
                if mult and mixn:
                    mixn.blend_type = 'MULTIPLY'
                    n.inputs["colorMixIn"].default_value = (*mult, 1)
                    n.inputs["colorMixInStrength"].default_value = 1.0
                n.inputs["Brightness"].default_value = spec.get("skin_brightness", 0.0)
                n.inputs["Contrast"].default_value = spec.get("skin_contrast", 0.0)
                n.inputs["Roughness"].default_value = spec.get("skin_rough", 0.5)
                n.inputs["SSS strength"].default_value = 0.35
                if "Pore strength" in n.inputs:
                    n.inputs["Pore strength"].default_value = spec.get("pores", 0.25)
    for o in rig.children:
        for slot in o.material_slots:
            m = slot.material
            if not m or not m.use_nodes:
                continue
            nt = m.node_tree
            for n in nt.nodes:
                if n.type == 'GROUP' and "IrisMajorColor" in n.inputs:
                    major, minor = spec.get("iris", ((0.18, 0.09, 0.035), (0.06, 0.03, 0.012)))
                    n.inputs["IrisMajorColor"].default_value = (*major, 1)
                    n.inputs["IrisMinorColor"].default_value = (*minor, 1)
            if o.name.endswith((".long01", ".short01", ".short02", ".short03", ".short04", ".bob01", ".bob02",
                                ".ponytail01", ".braid01", ".afro01")) or ".eyebrow" in o.name:
                tint_hair(nt, spec.get("hair_color", (0.05, 0.03, 0.02)), spec.get("hair_value", 1.0))


def tint_hair(nt, rgb, value=1.0):
    bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if not bsdf or not bsdf.inputs["Base Color"].is_linked:
        return
    src = bsdf.inputs["Base Color"].links[0].from_socket
    hsv = nt.nodes.new("ShaderNodeHueSaturation")
    hsv.inputs["Saturation"].default_value = 0.0
    hsv.inputs["Value"].default_value = value
    nt.links.new(src, hsv.inputs["Color"])
    mul = nt.nodes.new("ShaderNodeMix"); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'
    mul.inputs["Factor"].default_value = 1.0
    nt.links.new(hsv.outputs["Color"], mul.inputs["A"])
    # normalize so mid-grey texture maps to the target color
    mul.inputs["B"].default_value = (min(1, rgb[0] * 2.2), min(1, rgb[1] * 2.2), min(1, rgb[2] * 2.2), 1)
    nt.links.new(mul.outputs["Result"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.58
    bsdf.inputs["Specular IOR Level"].default_value = 0.18


# ----------------------------------------------------------------------------- particle hair (beards, short hair)

def hair_material(name, melanin, redness, rough=0.35, gray=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL':
            nt.nodes.remove(n)
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    h = nt.nodes.new("ShaderNodeBsdfHairPrincipled")
    h.parametrization = 'MELANIN'
    h.inputs["Melanin"].default_value = melanin
    h.inputs["Melanin Redness"].default_value = redness
    h.inputs["Roughness"].default_value = rough
    h.inputs["Radial Roughness"].default_value = 0.4
    h.inputs["Random Color"].default_value = 0.15
    h.inputs["Random Roughness"].default_value = 0.2
    if gray > 0:
        # per-strand random graying
        info = nt.nodes.new("ShaderNodeHairInfo")
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = gray - 0.05
        ramp.color_ramp.elements[1].position = gray + 0.05
        ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
        ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
        nt.links.new(info.outputs["Random"], ramp.inputs["Fac"])
        mapr = nt.nodes.new("ShaderNodeMapRange")
        mapr.inputs["To Min"].default_value = melanin
        mapr.inputs["To Max"].default_value = 0.12
        nt.links.new(ramp.outputs["Color"], mapr.inputs["Value"])
        nt.links.new(mapr.outputs["Result"], h.inputs["Melanin"])
    nt.links.new(h.outputs[0], out.inputs[0])
    return m


def face_landmarks(body, rig, co, names, W):
    eyeL = bone_head(rig, "eye.L"); eyeR = bone_head(rig, "eye.R")
    E = (eyeL + eyeR) / 2
    lips = np.array([w > 0.3 for w in group_weight(names, W, {"lips"})])
    M = Vector(co[lips].mean(axis=0)) if lips.any() else E - Vector((0, 0, 0.07))
    return E, M, lips


def add_beard(name, body, rig, spec):
    b = spec["beard"]
    co = mix_coords(body)
    names, W = bone_weights(body)
    E, M, lips = face_landmarks(body, rig, co, names, W)
    headw = group_weight(names, W, {"head", "jaw"})
    neckw = group_weight(names, W, NECK)
    bodyw = group_weight(names, W, {"body"})
    x, y, z = co[:, 0], co[:, 1], co[:, 2]
    ax = np.abs(x)
    front = y < (E.y + 0.075)
    # upper boundary: sideburn high near the ear, dropping toward the mustache corner
    t = smoothstep(0.028, 0.066, ax)
    zmax = (M.z + b.get("mustache_top", 0.019)) * (1 - t) + (E.z - b.get("cheek_drop", 0.018)) * t
    upper = 1.0 - smoothstep(zmax - 0.006, zmax + 0.006, z)
    # lower boundary: down the neck to about the larynx
    zmin = M.z - b.get("neck_depth", 0.095)
    lower = smoothstep(zmin - 0.01, zmin + 0.01, z)
    torsow = group_weight(names, W, TORSO | ARMS | LEGS)
    region = ((1.0 - torsow) > 0.6).astype(float)
    dens = upper * lower * front * region * (bodyw > 0.5)
    # under the jaw: only the front of the throat
    under = 1.0 - smoothstep(M.z - 0.045, M.z - 0.075, z) * smoothstep(E.y + 0.035, E.y + 0.065, y)
    dens *= under
    # clear the lips and a gap below the lower lip center (soul patch optional)
    lipd = np.sqrt(((x - M.x) / 0.027) ** 2 + ((z - M.z) / 0.0085) ** 2 + ((y - M.y) / 0.03) ** 2)
    dens *= smoothstep(0.92, 1.08, lipd)
    dens[lips] = 0
    # nose / nostrils: nothing that protrudes in front of the lips above the mouth
    nose = (z > M.z + 0.021) & (y < M.y - 0.004) & (ax < 0.03)
    dens[nose] = 0
    # behind the jaw angle fades out
    dens *= 1.0 - smoothstep(E.y + 0.045, E.y + 0.08, y)
    cheek = smoothstep(0.03, 0.06, ax) * smoothstep(M.z - 0.01, M.z + 0.03, z)
    dens *= 1.0 - 0.45 * cheek
    dens = np.clip(dens * b.get("density", 1.0), 0, 1)
    chin = np.exp(-((z - (M.z - 0.05)) / 0.028) ** 2)
    length = np.clip(0.38 + 0.62 * chin * (1 - smoothstep(0.02, 0.06, ax)) - 0.2 * smoothstep(M.z - 0.07, M.z - 0.1, z), 0.2, 1.0)
    length = length * (dens > 0.01)
    set_vgroup(body, "beard_density", dens)
    add_stubble(name, body, rig, spec, np.clip(dens * 1.4, 0, 1))
    if b.get("stubble_only"):
        return
    set_vgroup(body, "beard_length", length)
    psys_hair(body, "Beard", "beard_density", "beard_length", count=b.get("count", 4000),
              length=b.get("length", 0.025), align_down=b.get("down", 0.012), normal=b.get("normal", 0.004),
              children=b.get("children", 10), clump=0.35, kink=b.get("kink", 0.0), rough=0.004,
              radius=b.get("radius", 0.00045),
              mat=hair_material(f"{name}.beard_mat", b["melanin"], b.get("redness", 0.3), 0.4, b.get("gray", 0.0)))


def add_stubble(name, body, rig, spec, dens):
    """Darken the skin under beards (and for stubble-only faces) via a color attribute inside the skin group."""
    me = body.data
    attr = me.color_attributes.get("stubble") or me.color_attributes.new("stubble", 'FLOAT_COLOR', 'POINT')
    for i, d in enumerate(dens):
        attr.data[i].color = (d, d, d, 1.0)
    amount = spec.get("stubble", 0.55)
    for slot in body.material_slots:
        m = slot.material
        if not m or not m.use_nodes:
            continue
        for n in m.node_tree.nodes:
            if n.type == 'GROUP' and n.node_tree and "colorMixIn" in n.inputs:
                g = n.node_tree
                bc = next(x for x in g.nodes if x.type == 'BRIGHTCONTRAST')
                pr = next(x for x in g.nodes if x.type == 'BSDF_PRINCIPLED')
                at = g.nodes.new("ShaderNodeAttribute"); at.attribute_name = "stubble"
                noise = g.nodes.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = 900.0
                mul = g.nodes.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'
                g.links.new(at.outputs["Fac"], mul.inputs[0])
                ramp = g.nodes.new("ShaderNodeMapRange")
                ramp.inputs["To Min"].default_value = 0.6; ramp.inputs["To Max"].default_value = 1.0
                g.links.new(noise.outputs["Fac"], ramp.inputs["Value"])
                g.links.new(ramp.outputs["Result"], mul.inputs[1])
                fac = g.nodes.new("ShaderNodeMath"); fac.operation = 'MULTIPLY'; fac.inputs[1].default_value = amount
                g.links.new(mul.outputs[0], fac.inputs[0])
                mix = g.nodes.new("ShaderNodeMix"); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
                g.links.new(fac.outputs[0], mix.inputs["Factor"])
                g.links.new(bc.outputs["Color"], mix.inputs["A"])
                mix.inputs["B"].default_value = (0.22, 0.2, 0.2, 1)
                g.links.new(mix.outputs["Result"], pr.inputs["Base Color"])


def add_scalp_hair(name, body, rig, spec):
    h = spec["scalp_hair"]
    names, W = bone_weights(body)
    scalp = group_weight(names, W, {"scalp"})
    co = mix_coords(body)
    E = (bone_head(rig, "eye.L") + bone_head(rig, "eye.R")) / 2
    # hairline: forehead boundary a bit above the brows
    z = co[:, 2]; y = co[:, 1]
    hairline = smoothstep(E.z + h.get("hairline", 0.055), E.z + h.get("hairline", 0.055) + 0.012, z)
    behind = smoothstep(E.y + 0.02, E.y + 0.05, y)
    dens = np.clip(np.maximum(scalp * hairline, scalp * behind), 0, 1)
    set_vgroup(body, "scalp_density", dens)
    psys_hair(body, "ScalpHair", "scalp_density", None, count=h.get("count", 6000), length=h.get("length", 0.04),
              align_down=h.get("down", 0.02), normal=h.get("normal", 0.012), children=h.get("children", 10),
              clump=0.5, kink=h.get("kink", 0.6), rough=0.006, radius=0.0006,
              mat=hair_material(f"{name}.scalp_mat", h["melanin"], h.get("redness", 0.3), 0.35, h.get("gray", 0.0)))


def psys_hair(body, label, dens_group, len_group, count, length, align_down, normal, children, clump, kink, rough,
              radius, mat):
    body.data.materials.append(mat)
    mod = body.modifiers.new(label, 'PARTICLE_SYSTEM')
    # place right after the armature so hair follows shape keys + skinning
    while body.modifiers.find(mod.name) > 1:
        bpy.context.view_layer.objects.active = body
        bpy.ops.object.modifier_move_up(modifier=mod.name)
    ps = mod.particle_system
    ps.vertex_group_density = dens_group
    if len_group:
        ps.vertex_group_length = len_group
    st = ps.settings
    st.name = f"{body.name}.{label}"
    st.type = 'HAIR'
    st.count = count
    st.hair_length = length
    st.use_advanced_hair = True
    st.emit_from = 'FACE'
    st.use_emit_random = True
    st.normal_factor = normal
    st.object_align_factor = (0.0, -0.002, -align_down)
    st.factor_random = 0.002
    st.hair_step = 5
    st.display_step = 3
    st.render_step = 4
    st.child_type = 'INTERPOLATED'
    st.child_percent = 2
    st.rendered_child_count = children
    st.virtual_parents = 0.0
    st.clump_factor = clump
    st.clump_shape = -0.2
    st.roughness_1 = rough
    st.roughness_1_size = 1.0
    st.roughness_endpoint = rough * 0.6
    st.roughness_end_shape = 1.0
    st.child_length = 1.0
    if kink > 0:
        st.kink = 'CURL'
        st.kink_amplitude = 0.003 * kink
        st.kink_frequency = 6.0
    st.material_slot = mat.name
    st.root_radius = 1.0
    st.tip_radius = 0.15
    st.radius_scale = radius
    st.shape = 0.0
    st.use_close_tip = True
    return ps


# ----------------------------------------------------------------------------- clothing

def body_copy(name, body, label):
    """Duplicate the basemesh with the phenotype baked; keep vertex groups and the armature modifier."""
    ob = body.copy()
    ob.data = body.data.copy()
    ob.name = f"{name}.{label}"
    for c in body.users_collection:
        c.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    ob.select_set(True)
    if ob.data.shape_keys:
        # bake only the modelling (phenotype) mix; face keys are all zero here
        bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
    for m in list(ob.modifiers):
        if m.type != 'ARMATURE':
            ob.modifiers.remove(m)
    ob.data.materials.clear()
    return ob


def presmooth(ob, iters=40, factor=0.5):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    inner = [v for v in bm.verts if not v.is_boundary]
    for _ in range(iters):
        bmesh.ops.smooth_vert(bm, verts=inner, factor=factor, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    bm.to_mesh(ob.data)
    bm.free()


def drape_front(ob, rig, reach=0.24, width=0.03):
    """Cloth hangs from the bust/chest instead of following the body inward below it."""
    me = ob.data
    n = len(me.vertices)
    co = np.zeros(n * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(n, 3)
    ny = rig.data.bones["neck01"].head_local.y
    hip = bone_head(rig, "upperleg01.L").z
    front = (co[:, 1] < ny) & (co[:, 2] > hip) & (np.abs(co[:, 0]) < 0.2)
    idx = np.where(front)[0]
    if len(idx) == 0:
        return
    P = co[idx]
    dx = np.abs(P[:, None, 0] - P[None, :, 0]) < width
    dz = (P[None, :, 2] >= P[:, None, 2]) & (P[None, :, 2] <= P[:, None, 2] + reach)
    m = dx & dz
    ys = np.where(m, P[None, :, 1], np.inf).min(axis=1)
    newy = np.minimum(P[:, 1], ys + 0.003)
    co[idx, 1] = newy
    me.vertices.foreach_set("co", co.ravel())
    me.update()


def keep_vertices(ob, keep_mask):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    dead = [v for v in bm.verts if not keep_mask[v.index]]
    bmesh.ops.delete(bm, geom=dead, context='VERTS')
    # drop loose bits and slivers that would spike under offsets
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bmesh.ops.dissolve_degenerate(bm, dist=1e-4, edges=bm.edges[:])
    bm.to_mesh(ob.data)
    bm.free()


def add_cloth_modifiers(ob, offset, smooth_iter=12, solid=0.003, vg=None, folds=0.004, subsurf=1):
    sm = ob.modifiers.new("Smooth", 'SMOOTH'); sm.factor = 1.0; sm.iterations = smooth_iter
    d = ob.modifiers.new("Offset", 'DISPLACE'); d.direction = 'NORMAL'; d.strength = offset; d.mid_level = 0.0
    if vg:
        d.vertex_group = vg
    if folds > 0:
        tex = bpy.data.textures.new(f"{ob.name}.folds", 'CLOUDS')
        tex.noise_scale = 0.09
        tex.noise_depth = 1
        f = ob.modifiers.new("Folds", 'DISPLACE'); f.texture = tex; f.texture_coords = 'LOCAL'
        f.direction = 'NORMAL'; f.strength = folds; f.mid_level = 0.5
    sm2 = ob.modifiers.new("Smooth2", 'SMOOTH'); sm2.factor = 0.5; sm2.iterations = 2
    if solid > 0:
        so = ob.modifiers.new("Solidify", 'SOLIDIFY'); so.thickness = solid; so.offset = 1.0
        so.use_even_offset = False
        so.use_quality_normals = True
    ss = ob.modifiers.new("Subsurf", 'SUBSURF'); ss.levels = 0; ss.render_levels = subsurf
    for m in ob.modifiers:
        m.show_viewport = True
    ob.modifiers.new("WeightedNormal", 'WEIGHTED_NORMAL') if False else None


def make_top(name, body, rig, cfg, mat):
    """Tunic / sweater: torso + arms (to wrist or elbow), neckline cut, hem at hips/knee."""
    ob = body_copy(name, body, cfg.get("label", "tunic"))
    names, W = bone_weights(ob)
    dom, dw = dominant(names, W, None)
    co = np.array([v.co[:] for v in ob.data.vertices])
    bodyw = group_weight(names, W, {"body"}) > 0.5
    neck_z = bone_head(rig, "neck01").z
    wrist_l = bone_head(rig, "wrist.L"); wrist_r = bone_head(rig, "wrist.R")
    elbow_l = bone_head(rig, "lowerarm01.L")
    keep = np.isin(dom, list(TORSO | ARMS | (LEGS if cfg.get("legs") else set())))
    keep &= bodyw
    # neckline: a round opening around the neck (shoulders stay covered), optional V in front
    neck_cut = neck_z - cfg.get("neck_drop", 0.01)
    vdepth = cfg.get("v_neck", 0.0)
    ax = np.abs(co[:, 0])
    ny = rig.data.bones["neck01"].head_local.y
    dxy = np.sqrt(co[:, 0] ** 2 + ((co[:, 1] - ny) * 1.15) ** 2)
    r_open = cfg.get("collar_r", 0.092)
    front = co[:, 1] < ny - 0.02
    vline = neck_cut - vdepth * np.clip(1 - ax / 0.06, 0, 1) * front
    in_open = dxy < r_open + 0.02 * smoothstep(neck_cut - 0.04, neck_cut + 0.06, co[:, 2])
    keep &= ~(in_open & (co[:, 2] > vline))
    keep &= co[:, 2] < neck_z + 0.05
    # sleeves: cut before the wrist (or at the elbow for short sleeves)
    sleeve_end = cfg.get("sleeve", 0.94)  # fraction elbow->wrist
    for sgn, wr in ((1, wrist_l), (-1, wrist_r)):
        el = Vector((elbow_l.x * sgn, elbow_l.y, elbow_l.z))
        axis = (wr - el)
        L = axis.length
        axis.normalize()
        rel = co - np.array(el[:])
        proj = rel @ np.array(axis[:])
        side = (co[:, 0] * sgn) > 0.15
        keep &= ~(side & (proj > sleeve_end * L))
    # hem
    keep &= co[:, 2] > cfg.get("hem_z", 0.82)
    keep_vertices(ob, keep)
    presmooth(ob, cfg.get("presmooth", 45))
    drape_front(ob, rig)
    presmooth(ob, 8)
    # flare: looser toward the hem and sleeve ends
    co2 = np.array([v.co[:] for v in ob.data.vertices])
    hem = cfg.get("hem_z", 0.82)
    flare = 0.35 + 0.65 * smoothstep(hem + 0.35, hem, co2[:, 2])
    armness = smoothstep(0.2, 0.45, np.abs(co2[:, 0]))
    flare = np.maximum(flare, armness * (0.4 + 0.6 * smoothstep(0.25, 0.5, np.abs(co2[:, 0]))))
    near_neck = smoothstep(neck_cut - 0.09, neck_cut - 0.01, co2[:, 2]) * (np.abs(co2[:, 0]) < 0.16)
    flare *= (1.0 - 0.8 * near_neck)
    set_vgroup(ob, "flare", flare)
    add_cloth_modifiers(ob, cfg.get("offset", 0.014), vg="flare", folds=cfg.get("folds", 0.005),
                        solid=cfg.get("solid", 0.003), smooth_iter=cfg.get("smooth", 26))
    ob["neckline_z"] = float(neck_cut - vdepth)
    ob["collar_r"] = float(r_open)
    ob["neck_y"] = float(ny)
    ob.data.materials.append(mat)
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


def make_band(name, body, rig, cfg, mat):
    """Mantle / sash / shawl: a band region of the torso surface, offset further out than the tunic."""
    ob = body_copy(name, body, cfg["label"])
    names, W = bone_weights(ob)
    dom, _ = dominant(names, W, None)
    co = np.array([v.co[:] for v in ob.data.vertices])
    bodyw = group_weight(names, W, {"body"}) > 0.5
    keep = np.isin(dom, list(TORSO | ARMS | ({"upperleg01.L", "upperleg01.R"} if cfg.get("hips") else set()))) & bodyw
    neck_z = bone_head(rig, "neck01").z
    keep &= co[:, 2] < neck_z - cfg.get("neck_drop", 0.0)
    kind = cfg["kind"]
    x, y, z = co[:, 0], co[:, 1], co[:, 2]
    if kind == "diagonal":
        # band from (sx, sz) over a shoulder to (ex, ez) on the opposite hip, front and back
        sx, sz, ex, ez, wid = cfg["line"]
        p0 = np.array([sx, sz]); p1 = np.array([ex, ez])
        d = (p1 - p0) / np.linalg.norm(p1 - p0)
        rel = np.stack([x, z], 1) - p0
        perp = np.abs(rel[:, 0] * d[1] - rel[:, 1] * d[0])
        along = rel @ d
        inband = (perp < wid) & (along > -0.12) & (along < np.linalg.norm(p1 - p0) + 0.1)
        # cover the whole near shoulder and upper arm top
        keep &= inband
    elif kind == "shawl":
        # yoke over the shoulders + two front panels hanging to the waist
        yoke = z > cfg.get("yoke_z", 1.36)
        panels = (np.abs(x) > 0.035) & (np.abs(x) < cfg.get("panel_w", 0.15)) & (y < 0.0) & (z > cfg.get("panel_end", 0.98))
        back = (y > 0.0) & (z > cfg.get("back_end", 1.12)) & (np.abs(x) < 0.2)
        armmask = np.abs(x) < 0.27
        keep &= (yoke | panels | back) & armmask
    elif kind == "stole":
        # prayer shawl worn as a stole: over the shoulders, two strips down the front, a panel on the back
        nz = neck_z
        front = (y < 0.0) & (np.abs(x) > cfg.get("inner", 0.04)) & (np.abs(x) < cfg.get("outer", 0.13)) & \
                (z > cfg.get("end", 0.97))
        over = (z > nz - 0.085) & (np.abs(x) < cfg.get("outer", 0.13) + 0.03)
        backp = (y > 0.0) & (z > cfg.get("back_end", 1.18)) & (np.abs(x) < 0.17)
        keep &= front | over | backp
    elif kind == "belt":
        keep &= (z > cfg["z0"]) & (z < cfg["z1"])
    keep_vertices(ob, keep)
    add_cloth_modifiers(ob, cfg.get("offset", 0.026), folds=cfg.get("folds", 0.006), solid=cfg.get("solid", 0.004),
                        smooth_iter=cfg.get("smooth", 14))
    ob.data.materials.append(mat)
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


def make_skirt(name, body, rig, cfg, mat):
    """Long robe skirt lofted from the waist to the ankles, skinned to hips/legs with damping."""
    co = mix_coords(body)
    names, W = bone_weights(body)
    dom, _ = dominant(names, W, None)
    bodyw = group_weight(names, W, {"body"}) > 0.5
    lower = np.isin(dom, list(LEGS | {"root", "spine05", "pelvis.L", "pelvis.R", "spine04"})) & bodyw
    pts = co[lower]
    z_top = cfg.get("top", 1.02)
    z_bot = cfg.get("bottom", 0.07)
    rings, segs = 26, 56
    hip = bone_head(rig, "upperleg01.L")
    knee = bone_head(rig, "lowerleg01.L")
    rng = random.Random(cfg.get("seed", 3))
    phase = [rng.uniform(0, math.tau) for _ in range(4)]
    verts, weights = [], []
    prev_rx = prev_ry = 0.0
    for i in range(rings):
        t = i / (rings - 1)
        zz = z_top + (z_bot - z_top) * t
        sl = pts[np.abs(pts[:, 2] - zz) < 0.025]
        if len(sl) < 10:
            cx, cy, rx, ry = 0.0, 0.0, prev_rx, prev_ry
        else:
            cx = 0.0
            cy = float((sl[:, 1].max() + sl[:, 1].min()) / 2)
            rx = float(np.abs(sl[:, 0]).max())
            ry = float((sl[:, 1].max() - sl[:, 1].min()) / 2)
        flare = cfg.get("flare", 0.12) * t ** 1.4
        margin = 0.004 + 0.03 * float(smoothstep(0.0, 0.3, np.array([t]))[0])
        rx = max(rx * 0.92 + margin + flare, prev_rx)
        ry = max(ry * 0.92 + margin + flare * 0.8, prev_ry * 0.98)
        prev_rx, prev_ry = rx, ry
        amp = 0.004 + cfg.get("fold_amp", 0.05) * t ** 1.2
        for j in range(segs):
            th = j / segs * math.tau
            fold = (math.sin(9 * th + phase[0] + 2.5 * t) * 0.6 + math.sin(14 * th + phase[1]) * 0.3 +
                    math.sin(5 * th + phase[2] + 4 * t) * 0.4)
            r = 1.0 + amp * fold
            px = cx + rx * r * math.cos(th)
            py = cy + ry * r * math.sin(th)
            verts.append((px, py, zz))
            # skin weights: upper rings follow the root, lower rings blend legs per side
            s = float(smoothstep(-0.07, 0.07, np.array([px]))[0])
            legf = float(smoothstep(z_top - 0.05, hip.z - 0.12, np.array([zz]))[0]) * cfg.get("leg_follow", 0.55)
            kn = float(smoothstep(knee.z + 0.1, knee.z - 0.1, np.array([zz]))[0])
            w = {"root": 1.0 - legf}
            for side, sw in (("L", s), ("R", 1 - s)):
                w[f"upperleg01.{side}"] = legf * sw * (1 - kn) * 0.5
                w[f"upperleg02.{side}"] = legf * sw * (1 - kn) * 0.5
                w[f"lowerleg01.{side}"] = legf * sw * kn
            weights.append(w)
    faces = []
    for i in range(rings - 1):
        for j in range(segs):
            a = i * segs + j
            b = i * segs + (j + 1) % segs
            faces.append((a, b, b + segs, a + segs))
    me = bpy.data.meshes.new(f"{name}.skirt")
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new(f"{name}.skirt", me)
    for c in body.users_collection:
        c.objects.link(ob)
    ob.parent = rig
    for vi, w in enumerate(weights):
        for bn, val in w.items():
            if val > 1e-3:
                vg = ob.vertex_groups.get(bn) or ob.vertex_groups.new(name=bn)
                vg.add([vi], val, 'REPLACE')
    arm = ob.modifiers.new("Armature", 'ARMATURE'); arm.object = rig
    so = ob.modifiers.new("Solidify", 'SOLIDIFY'); so.thickness = 0.004; so.offset = 1.0
    ss = ob.modifiers.new("Subsurf", 'SUBSURF'); ss.levels = 0; ss.render_levels = 1
    me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True
    return ob


def make_headcover(name, body, rig, cfg, mat):
    """Head covering: scalp/back-of-head region pushed out, lower boundary extruded into a drape."""
    ob = body_copy(name, body, cfg.get("label", "headcover"))
    names, W = bone_weights(ob)
    co = np.array([v.co[:] for v in ob.data.vertices])
    bodyw = group_weight(names, W, {"body"}) > 0.5
    headw = group_weight(names, W, {"head"})
    scalp = group_weight(names, W, {"scalp"})
    ears = group_weight(names, W, {"ears"})
    E = (bone_head(rig, "eye.L") + bone_head(rig, "eye.R")) / 2
    z, y, x = co[:, 2], co[:, 1], co[:, 0]
    top = z > E.z + cfg.get("brow", 0.04)
    back = (y > E.y + 0.06) & (z > E.z - 0.11)
    sides = (np.abs(x) > 0.058) & (z > E.z - 0.06) & (y > E.y + 0.025)
    keep = bodyw & ((headw + group_weight(names, W, NECK)) > 0.3) & (top | back | sides | (scalp > 0.3))
    keep_vertices(ob, keep)
    # extrude the lower boundary downward into a drape over the neck/shoulders
    drop = cfg.get("drape", 0.14)
    bm = bmesh.new(); bm.from_mesh(ob.data)
    boundary = [e for e in bm.edges if e.is_boundary]
    bverts = {v for e in boundary for v in e.verts}
    low = [e for e in boundary if all(v.co.z < E.z - 0.0 for v in e.verts)]
    if low and drop > 0:
        ret = bmesh.ops.extrude_edge_only(bm, edges=low)
        new_v = [g for g in ret["geom"] if isinstance(g, bmesh.types.BMVert)]
        dw = bm.verts.layers.deform.verify()
        neck_idx = ob.vertex_groups["neck01"].index
        head_idx = ob.vertex_groups["head"].index
        for v in new_v:
            out = Vector((v.co.x, v.co.y - E.y - 0.05, 0)).normalized() * 0.05
            v.co += Vector((out.x, out.y, -drop))
            v[dw].clear()
            v[dw][neck_idx] = 0.7
            v[dw][head_idx] = 0.3
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-4)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-4, edges=bm.edges[:])
    bm.to_mesh(ob.data); bm.free()
    add_cloth_modifiers(ob, cfg.get("offset", 0.018), smooth_iter=6, folds=0.006, solid=0.003)
    ob.data.materials.append(mat)
    for p in ob.data.polygons:
        p.use_smooth = True
    if False and cfg.get("band"):
        # a wrapped band around the head at forehead level
        r = 0.105
        bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=0.016, major_segments=40, minor_segments=10,
                                         location=(0, E.y + 0.035, E.z + 0.055))
        band = bpy.context.object
        band.name = f"{name}.headband"
        band.scale = (0.85, 1.05, 1.0)
        band.rotation_euler = (math.radians(-12), 0, 0)
        for c in list(band.users_collection):
            c.objects.unlink(band)
        for c in body.users_collection:
            c.objects.link(band)
        band.data.materials.append(cfg["band"])
        bpy.context.view_layer.objects.active = band
        band.select_set(True)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        band.parent = rig
        band.parent_type = 'BONE'
        band.parent_bone = "head"
        band.matrix_parent_inverse = (rig.matrix_world @ rig.pose.bones["head"].matrix @
                                      __import__("mathutils").Matrix.Translation((0, rig.data.bones["head"].length, 0))).inverted()
        for p in band.data.polygons:
            p.use_smooth = True
    return ob


def make_legs(name, body, rig, mat, label="trousers", offset=0.008):
    ob = body_copy(name, body, label)
    names, W = bone_weights(ob)
    dom, _ = dominant(names, W, None)
    co = np.array([v.co[:] for v in ob.data.vertices])
    bodyw = group_weight(names, W, {"body"}) > 0.5
    ankle = bone_head(rig, "foot.L").z
    keep = np.isin(dom, list(LEGS | {"root", "spine05", "pelvis.L", "pelvis.R"})) & bodyw & (co[:, 2] > ankle + 0.03)
    keep &= co[:, 2] < bone_head(rig, "spine04").z + 0.14
    keep_vertices(ob, keep)
    presmooth(ob, 12)
    add_cloth_modifiers(ob, offset, smooth_iter=6, folds=0.003, solid=0.002)
    ob.data.materials.append(mat)
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


def add_mhclo(name, body, asset, subdir="clothes"):
    from bl_ext.user_default.mpfb.services import AssetService
    path = AssetService.find_asset_absolute_path(asset + ".mhclo", subdir)
    HumanService.add_mhclo_asset(path, body, asset_type="Clothes", subdiv_levels=1, material_type="MAKESKIN")


def dress(name, spec, rig, body):
    mats = {}
    for key, m in spec.get("materials", {}).items():
        mats[key] = make_material(f"{name}.{key}", **m)
    made = []
    for item in spec.get("clothes", []):
        kind = item["type"]
        mat = mats[item["mat"]] if "mat" in item else None
        if kind == "top":
            made.append(make_top(name, body, rig, item, mat))
        elif kind == "band":
            made.append(make_band(name, body, rig, item, mat))
        elif kind == "skirt":
            made.append(make_skirt(name, body, rig, item, mat))
        elif kind == "headcover":
            cfg = dict(item)
            if "band_mat" in item:
                cfg["band"] = mats[item["band_mat"]]
            made.append(make_headcover(name, body, rig, cfg, mat))
        elif kind == "legs":
            made.append(make_legs(name, body, rig, mat, item.get("label", "trousers"), item.get("offset", 0.008)))
        elif kind == "mhclo":
            add_mhclo(name, body, item["asset"])
    for ob in made:
        ob.parent = rig
        if ob.get("skip_mask") is None and kind != "skirt":
            pass
    # hide body skin under opaque clothes to save render time and avoid poke-through
    hide = spec.get("hide_body")
    if hide:
        names, W = bone_weights(body)
        co = mix_coords(body)
        dom, _ = dominant(names, W, None)
        bones = set()
        for k in hide.get("bones", []):
            bones |= {"TORSO": TORSO, "ARMS": ARMS, "LEGS": LEGS}.get(k, {k})
        m = np.isin(dom, list(bones))
        tops = [o for o in made if o.get("neckline_z") is not None]
        zmax = min([hide.get("zmax", 9.0)] + [o["neckline_z"] - 0.022 for o in tops])
        if tops:
            t0 = tops[0]
            dxy = np.sqrt(co[:, 0] ** 2 + ((co[:, 1] - t0["neck_y"]) * 1.15) ** 2)
            m &= (co[:, 2] < zmax) | (dxy > t0["collar_r"] + 0.015)
        else:
            m &= co[:, 2] < zmax
        if "zmin" in hide:
            m &= co[:, 2] > hide["zmin"]
        wrist = min(bone_head(rig, "wrist.L").x, 1.0)
        m &= ~(np.abs(co[:, 0]) > hide.get("arm_x", wrist - 0.06))
        set_vgroup(body, "hidden_by_clothes", m.astype(float), threshold=0.5)
        msk = body.modifiers.new("ClothMask", 'MASK')
        msk.vertex_group = "hidden_by_clothes"
        msk.invert_vertex_group = True
        while body.modifiers.find(msk.name) > 1:
            bpy.context.view_layer.objects.active = body
            bpy.ops.object.modifier_move_up(modifier=msk.name)


# ----------------------------------------------------------------------------- main

def build(name):
    spec = SPECS[name]
    clear()
    rig, body = build_human(name, spec)
    tune_materials(name, spec, rig)
    if spec.get("beard"):
        add_beard(name, body, rig, spec)
    if spec.get("scalp_hair"):
        add_scalp_hair(name, body, rig, spec)
    dress(name, spec, rig, body)
    col = bpy.data.collections.new(f"CHAR_{name}")
    bpy.context.scene.collection.children.link(col)
    for o in [rig] + list(rig.children_recursive):
        for c in list(o.users_collection):
            c.objects.unlink(o)
        col.objects.link(o)
    rig["char_name"] = name
    os.makedirs(OUT, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=f"{OUT}/{name}.blend")
    return rig


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:]
    build(argv[0])
    print("BUILT_OK", argv[0])
