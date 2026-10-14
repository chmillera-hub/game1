"""s14a - Light breaks: "But you, Lord, do not be far from me. You are my strength; come quickly to help me."

The turn of the psalm. Fade up from black on the darkened Golgotha (eclipse): the centre cross with the
crucified figure stands against the dim red-brown sky. On the first phrase the clouds part around the sun:
a hole opens in the sky (world-shader mask around the sun direction), a single shaft of golden light comes
down and falls on the cross (a narrow spot light from the sun direction = the light pool + rim on the
figure, and a fake volumetric beam: an additive emissive cylinder - real volumetric god rays cost
~+12 s/frame). On the second phrase more shafts fan down over the land, the sky warms, and the camera
cranes up and tilts toward the light. The figure is only ever a backlit silhouette.
"""
import math
import bpy
from mathutils import Vector
from lib import core as C
from lib import env as E
from lib import characters as P
from lib import wardrobe as W

SUN_AZ = 165.0      # env presets (sun over Jerusalem, behind the crosses seen from the -Y side)
SUN_EL = 30.0


# --------------------------------------------------------------------------------------------- helpers
def _key_prop(idb, name, pairs, interp="BEZIER"):
    """Key a custom float property on an ID (object / scene) at [(frame, value)]."""
    for f, v in pairs:
        idb[name] = float(v)
        idb.keyframe_insert('["%s"]' % name, frame=f)
    ad = idb.animation_data
    for fc in C._fcurves(ad.action):
        if fc.data_path == '["%s"]' % name:
            for kp in fc.keyframe_points:
                kp.interpolation = interp
                if interp == "BEZIER":
                    kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"


def beam_material(name, color=(1.0, 0.78, 0.5), strength=1.0, seed=0.0):
    """Additive 'volumetric' shaft: Transparent + Emission on the front faces of a cylinder (local Z = axis).
    Brightness ~ the view ray's path length through the cylinder (chord / sin(angle to the axis): brighter
    when looking along the shaft, soft round cross-section), x fades at both ends x drifting streaks
    x object property 'beam' (a uniform: keyable without re-evaluating the material)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    T = E._NT(nt)
    out = T.node("ShaderNodeOutputMaterial")
    tc = T.node("ShaderNodeTexCoord")
    geo = T.node("ShaderNodeNewGeometry")
    vt = T.node("ShaderNodeVectorTransform")
    vt.vector_type = "VECTOR"
    vt.convert_from = "WORLD"
    vt.convert_to = "OBJECT"
    T.link(geo.outputs["Incoming"], vt.inputs[0])
    vx, vy, _ = T.sep(T.vmath("NORMALIZE", vt.outputs[0]))
    px, py, _ = T.sep(tc.outputs["Object"])
    vxy = T.math("SQRT", T.math("ADD", T.math("MULTIPLY", vx, vx), T.math("MULTIPLY", vy, vy)))
    crs = T.math("ABSOLUTE", T.math("SUBTRACT", T.math("MULTIPLY", px, vy), T.math("MULTIPLY", py, vx)))
    d = T.math("DIVIDE", crs, T.math("MAXIMUM", vxy, 1e-4))
    rad = T.node("ShaderNodeAttribute")
    rad.attribute_type = "OBJECT"
    rad.attribute_name = "beam_r"
    radius = rad.outputs["Fac"]
    q = T.math("SUBTRACT", 1.0, T.math("POWER", T.math("DIVIDE", d, radius), 2.0), clamp=True)
    prof = T.math("MINIMUM", T.math("DIVIDE", T.math("POWER", q, 1.5), T.math("MAXIMUM", vxy, 0.15)), 4.0)
    g = T.sep(tc.outputs["Generated"])                      # z: 0 at the ground .. 1 at the cloud base
    z = g[2]
    fade = T.math("MULTIPLY", T.smooth(0.0, 0.02, z), T.math("POWER", T.math("SUBTRACT", 1.0, z, clamp=True), 1.4))
    # streaks along the beam that slowly drift (dust/cloud texture inside the shaft)
    ob = T.node("ShaderNodeAttribute")
    ob.attribute_type = "OBJECT"
    ob.attribute_name = "beam_t"
    p = T.vmath("MULTIPLY", tc.outputs["Object"], (0.4, 0.4, 0.02))
    p = T.vmath("ADD", p, T.comb(0.0, 0.0, ob.outputs["Fac"]))
    nz = T.noise(p, scale=0.8, detail=2.0, rough=0.5, w=seed, dims="4D")
    streak = T.math("ADD", 0.35, T.math("MULTIPLY", nz.outputs["Fac"], 1.3))
    k = T.node("ShaderNodeAttribute")
    k.attribute_type = "OBJECT"
    k.attribute_name = "beam"
    amt = T.math("MULTIPLY", T.math("MULTIPLY", T.math("MULTIPLY", prof, fade), streak),
                 T.math("MULTIPLY", k.outputs["Fac"], strength))
    em = T.node("ShaderNodeEmission")
    em.inputs[0].default_value = (*color, 1)
    T.link(amt, em.inputs[1])
    tr = T.node("ShaderNodeBsdfTransparent")
    add = T.node("ShaderNodeAddShader")
    T.link(tr.outputs[0], add.inputs[0])
    T.link(em.outputs[0], add.inputs[1])
    T.link(add.outputs[0], out.inputs["Surface"])
    m.surface_render_method = "BLENDED"
    m.use_backface_culling = True
    return m


def beam(name, foot, sun_dir, radius, top_height, mat_, keys, drift=0.25):
    """Cylinder from `foot` (ground) up along sun_dir to `top_height` metres above the foot."""
    L = top_height / max(0.05, sun_dir.z)
    bpy.ops.mesh.primitive_cylinder_add(vertices=28, radius=radius, depth=L, end_fill_type="NOTHING")
    o = bpy.context.active_object
    o.name = name
    o.rotation_euler = sun_dir.to_track_quat("Z", "Y").to_euler()
    o.location = Vector(foot) + sun_dir * (L / 2)
    for p in o.data.polygons:
        p.use_smooth = True
    o.data.materials.append(mat_)
    o.visible_shadow = False
    o.visible_diffuse = o.visible_glossy = o.visible_transmission = o.visible_volume_scatter = False
    o["beam_r"] = float(radius)
    _key_prop(o, "beam", keys)
    sc = bpy.context.scene
    _key_prop(o, "beam_t", [(sc.frame_start, 0.0), (sc.frame_end + 1, drift * (sc.frame_end + 1 - sc.frame_start) / 24.0)],
              interp="LINEAR")
    return o


def sky_hole(sun_dir, seed=0.3):
    """Open a ragged hole in the darkened sky around the sun: the camera-branch mix factor of the
    sky_transition world becomes max(env_sky_mix, hole) where hole = scene props s14_hole (amount) and
    s14_hole_r (radius, radians) with a noisy edge. Lighting branch untouched."""
    nt = bpy.context.scene.world.node_tree
    ms = next(n for n in nt.nodes if n.type == "MIX_SHADER" and n.inputs[2].is_linked)
    bgc = ms.inputs[2].links[0].from_node
    cam_mix = bgc.inputs[0].links[0].from_node
    fac_src = cam_mix.inputs[0].links[0].from_socket
    T = E._NT(nt)
    tc = T.node("ShaderNodeTexCoord")
    vn = T.vmath("NORMALIZE", tc.outputs["Generated"])
    ang = T.math("ARCCOSINE", T.math("MINIMUM", T.vmath("DOT_PRODUCT", vn, tuple(sun_dir.normalized())), 1.0))
    nz = T.noise(vn, scale=5.0, detail=4.0, rough=0.6, dist=0.4, w=seed, dims="4D")
    angn = T.math("MULTIPLY", ang, T.math("ADD", 0.55, T.math("MULTIPLY", nz.outputs["Fac"], 0.9)))
    r = E._lattr(T, "s14_hole_r", 0.0)
    amt = E._lattr(T, "s14_hole", 0.0)
    soft = T.math("ADD", T.math("MULTIPLY", r, 0.45), 0.01)
    edge = T.math("DIVIDE", T.math("SUBTRACT", r, angn), soft)
    hole = T.math("MULTIPLY", T.smooth(-1.0, 1.0, edge), amt)
    fac = T.math("MAXIMUM", fac_src, hole)
    T.link(fac, cam_mix.inputs[0])
    return hole


def _hazify_person(p):
    seen = set()
    for o in p.objects():
        for m in getattr(o.data, "materials", []) or [] if o.data is not None else []:
            if m is not None and m.name not in seen:
                seen.add(m.name)
                E.hazify(m)


# --------------------------------------------------------------------------------------------- build
def build(ctx):
    N, NR = ctx.nframes, ctx.render_frames
    fr = lambda sec: int(round(ctx.frame(sec)))
    p1s, p1e = ctx.phrases[0]["start"], ctx.phrases[0]["end"]
    p2s, p2e = ctx.phrases[1]["start"], ctx.phrases[1]["end"]
    sc = bpy.context.scene

    cams = [dict(loc=(-1.2, -9.2, 12.0), target=(0.0, 1.0, 13.5), lens=24),
            dict(loc=(-1.0, -8.2, 14.2), target=(4.0, 60.0, 40.0), lens=24)]
    A = E.golgotha(ctx, mood="eclipse", dust=False, grass=0.8, near_detail=0.6, view=cams)
    sun_dir = E._dir_from_az_el(SUN_AZ, SUN_EL)
    disk_a = dict(E.SKY_PRESETS["eclipse"]["sun_disk"], el=SUN_EL)
    # B: the light that breaks through - the same overcast HDRI + cloud layer, but bright and golden
    over_b = dict(sun_az=SUN_AZ, sun_el=SUN_EL, key=0.22, strength=0.45, sun_energy=1.6, tint=(1.0, 0.84, 0.6),
                  sat=1.1, sun_tint=(1.0, 0.78, 0.5), sun_angle=1.0, haze_density=0.0009,
                  haze_tint=(1.0, 0.92, 0.8), exposure=0.3, grade="warm", clouds=0.5,
                  cloud_opts=dict(color=(0.95, 0.78, 0.55), shadow=(0.3, 0.2, 0.14), opacity=0.85, sun_glow=1.2,
                                  speed=(9.0, 3.0)),
                  sun_disk=dict(el=SUN_EL, size=1.0, color=(1.0, 0.88, 0.66), strength=40.0, glow=0.2))
    # global brightening (ambient, sun lamp, haze, exposure) starts on phrase 2, ~40 % done at the end
    g0 = fr(p2s) - 6
    g1 = g0 + int((NR - g0) / 0.4)
    E.sky_transition(ctx, "eclipse", "eclipse", g0, g1,
                     over_a=dict(sun_az=SUN_AZ, sun_el=SUN_EL, sun_disk=disk_a), over_b=over_b)
    sky_hole(sun_dir)
    sc.eevee.shadow_pool_size = "512"   # sky() lowers it to 256 MB; the far narrow spot needs more pages
    h0 = fr(p1s) + 2                 # the clouds start to part
    h1 = fr(p1e)                     # first shaft fully on the cross ("do not be far from me")
    E.scene_prop("s14_hole_r", 0.0, 1)
    E.scene_prop("s14_hole", 0.0, 1)
    _key_prop(sc, "s14_hole", [(h0 - 6, 0.0), (h1, 0.85)])
    _key_prop(sc, "s14_hole_r", [(h0 - 6, 0.01), (h1 - 4, 0.07), (fr(p2s) + 10, 0.09), (NR, 0.2)])

    # --------------------------------------------------------------------- the crosses + crucified
    cx = A["crosses"]
    c = cx["center"]
    cz = c["base"][2]
    j = P.make_person("jesus", "JESUS_CROSS", pose=None, hair_strands=False)
    P.place_on_cross(j, c["root"], head="up", strain=0.7)
    try:
        W.drape(j, [g for g in j.garments if "loincloth" in g.name], frames=25, ramp=15, ground=None)
    except Exception as e:
        print("s14a WARNING: drape failed:", e)
    P.expression(j, "exhausted")
    people = [j]
    for k, seed, head, ks in (("left", 4, "down", -1.0), ("right", 9, "side", 1.0)):
        t = P.make_person("thief_" + k, "CROWD_MAN", seed=seed, outfit=["loincloth"], outfit_colors={"loincloth": "oatmeal"},
                          pose=None, lod="mid", hair_strands=False, dirt=0.5, age_years=30 + seed)
        P.place_on_cross(t, cx[k]["root"], head=head, strain=0.75, knee_side=ks)
        P.expression(t, "exhausted")
        people.append(t)
    for p in people:
        _hazify_person(p)

    # --------------------------------------------------------------------- the light
    gold = (1.0, 0.8, 0.52)
    a0, a1 = fr(p1s) + 8, fr(p1e) - 4
    # key: a narrow strong shaft light-linked to the centre cross + figure (rim / back light)
    target = Vector((c["base"][0], c["base"][1] + 0.1, cz + 2.7))
    spot_d = 160.0
    key = C.light("SPOT", tuple(target + sun_dir * spot_d), 0.0, color=gold, target=tuple(target), size=1.0,
                  name="ShaftKey", spot_size=2 * math.degrees(math.atan(2.0 / spot_d)), spot_blend=0.6)
    key.data.volume_factor = 0.0
    recv = bpy.data.collections.new("s14a_shaft_recv")
    for o in [ch for ch in c["root"].children] + j.objects():
        if o.type in ("MESH", "CURVES", "CURVE"):
            recv.objects.link(o)
    key.light_linking.receiver_collection = recv
    E_key = 4.5                                        # W/m2 (eclipse sun 0.35, golden sun 4.2)
    P_key = E_key * 4 * math.pi * spot_d ** 2
    C.keys(key.data, "energy", [(1, 0.0), (a0, 0.0), (a1, P_key), (NR, P_key * 1.1)])
    # the light pool on the ground (the shaft is broader than the cross): softer, casts the long cross shadow
    gtarget = Vector((c["base"][0], c["base"][1] - 1.5, cz + 0.3))
    pool = C.light("SPOT", tuple(gtarget + sun_dir * spot_d), 0.0, color=gold, target=tuple(gtarget), size=2.5,
                   name="ShaftPool", spot_size=2 * math.degrees(math.atan(2.4 / spot_d)), spot_blend=1.0)
    pool.data.volume_factor = 0.0
    E_pool = 1.3
    P_pool = E_pool * 4 * math.pi * spot_d ** 2
    C.keys(pool.data, "energy", [(1, 0.0), (a0 + 4, 0.0), (a1 + 4, P_pool), (NR, P_pool * 1.2)])
    foot = Vector((c["base"][0], c["base"][1] + 0.2, cz - 0.4))
    beam("ShaftMain", foot, sun_dir, 2.3, 260.0, beam_material("ShaftMain", color=gold, seed=0.2),
         [(1, 0.0), (a0 - 4, 0.0), (a1, 0.2), (fr(p2s), 0.17), (NR, 0.2)])
    beam("ShaftMainHalo", foot, sun_dir, 7.0, 260.0, beam_material("ShaftHalo", color=gold, seed=0.7),
         [(1, 0.0), (a0, 0.0), (a1 + 6, 0.05), (NR, 0.06)])
    # more rays follow (phrase 2): broad shafts fanning down over the land beyond the hill
    others = [((-38.0, 70.0), 7.0, 0), ((32.0, 120.0), 9.0, 6), ((-95.0, 190.0), 13.0, 12), ((80.0, 60.0), 8.0, 18),
              ((10.0, 260.0), 16.0, 9), ((-150.0, 110.0), 12.0, 22), ((140.0, 210.0), 15.0, 15)]
    b0 = fr(p2s) - 4
    bm_o = beam_material("ShaftFar", color=(1.0, 0.82, 0.56), seed=1.3)
    for i, ((x, y), r, off) in enumerate(others):
        z = A["ground"](x, y)
        s0 = b0 + off
        beam("Shaft%d" % i, (x, y, z - 1.0), sun_dir, r, 320.0, bm_o,
             [(1, 0.0), (s0, 0.0), (s0 + 30, 0.1 - 0.006 * i), (NR, 0.12 - 0.006 * i)], drift=0.15)
        sp = C.light("SPOT", tuple(Vector((x, y, z)) + sun_dir * 400.0), 0.0, color=gold, target=(x, y, z),
                     size=4.0, name="ShaftPool%d" % i, spot_size=2 * math.degrees(math.atan(r * 1.2 / 400.0)),
                     spot_blend=0.85, shadow=False)
        sp.data.volume_factor = 0.0
        pw = 1.2 * 4 * math.pi * 400.0 ** 2
        C.keys(sp.data, "energy", [(1, 0.0), (s0, 0.0), (s0 + 30, pw), (NR, pw)])

    # --------------------------------------------------------------------- camera: look up, then rise toward the light
    head = Vector(c["head"])
    c0 = Vector((-1.9, -9.0, cz + 1.0))
    c1 = Vector((-1.6, -8.0, cz + 3.2))
    d_head0 = (head + Vector((0, 0, -0.6)) - c0).normalized()
    m0, m1 = fr(p1e) - 16, NR + 12

    def path(f):
        u = C.smoothstep((f - m0) / float(m1 - m0))
        u = 0.85 * u + 0.15 * C.smoothstep((f - 1) / float(m1 - 1))        # never fully still
        loc = c0.lerp(c1, u)
        dh = (head + Vector((0, 0, -0.6 * (1 - u))) - loc).normalized()
        dv = dh.lerp(sun_dir, 0.36 * C.smoothstep(u * 1.1)).normalized()
        lens = 30.0 - 6.0 * u
        loc = loc + C.shake(f, 0.01, 0.25, 7)
        return (loc, loc + dv * 10.0, 0.0, lens)

    cam = C.camera(loc=tuple(c0), target=tuple(c0 + d_head0), lens=30)
    C.animate_camera(cam, path, 1, NR)

    ctx.samples = 6
    ctx.render_opts.update({"volumetrics": "low"})
    ctx.interp = True
    ctx.post.update({"grade": "eclipse", "bloom": 0.22, "bloom_threshold": 0.66, "halation": 0.08,
                     "end": {"grade": "warm", "exposure": 0.0, "saturation": 0.95, "bloom": 0.42,
                             "bloom_threshold": 0.6, "halation": 0.12, "vignette": 0.24}})
