"""s18a - Ends of the earth: "All the ends of the earth will remember and turn to the Lord, and all the
families of the nations will bow down before him,"

Earth from orbit at night. The camera hangs ~3000 km above West Africa looking east along the dark
globe: city lights of the Maghreb, the Nile and the Levant, the curved limb with its thin blue/orange
atmosphere. On "remember" the glow on the eastern limb swells and the sun bursts over the horizon
above the Persian Gulf (sunburst via the Blender compositor glare). On "turn to the Lord" morning light
pours west over Iran, Arabia, the Levant and Egypt; through "all the families of the nations" the camera
rises and pulls back, the terminator sweeps on across Africa and Europe and the shot ends on a bright,
sunlit Middle East / Africa / Europe (dissolve to s18b, kneeling nations at dawn).

Built on lib/fx.earth_from_space (globe, clouds, night lights, atmosphere, stars). This file adds:
 * its own terminator sweep (re-keys the lib's `sun_lon` nodes + sun lamp; slow approach, crest at a
   chosen frame, accelerating sweep afterwards),
 * a visible sun disc + corona in the world shader (camera rays only),
 * a forward-scattering limb-glow shell (the bright halo where the sun is about to rise),
 * its own camera (quaternion keys every frame) aimed at the sunrise point, then at the globe,
 * compositor fog-glow + streak glare driven by the sun disc only.
"""
import math
import bpy
from mathutils import Vector, Matrix, Quaternion
from lib import core as C
from lib import fx as FX

R = 6.371
FOCUS = (35.0, 30.0)        # globe root orientation (lib convention: this lon/lat faces -Y)
DECL = -8.0                 # sub-solar latitude: puts the sunrise point over the Persian Gulf for this camera
LENS = 32.0
CREST_SEC = 3.15            # sun clears the limb (end of "remember")
# terminator sweep speed (deg of longitude per frame): slow approach -> fast sweep -> ease out
RATE = dict(r0=0.12, r1=0.42, r2=0.25, ra=80, rb=115, rc=185, rd=235)
# camera: distance (radii) and sub-camera point (lon, lat) start -> end
CAM = dict(d0=1.45, d1=2.7, da=90, lon0=-8.0, lat0=28.0, lon1=22.0, lat1=22.0,
           qx=0.56, qy=0.32,                 # where the sunrise point sits in frame (0..1, y down)
           end_lon=22.0, end_lat=22.0, end_off=0.0,    # late aim: point inside the globe
           wa=95, roll0=-7.0, roll1=0.0)
NIGHT_CROP = ("/opt/assets/earth/dnb_2012_crop_w40e90_s20n66.jpg", (-40.0, 90.0, -20.0, 66.0))  # 13500-px Black Marble crop


def _ease(x):
    x = min(1.0, max(0.0, x))
    return 0.5 - 0.5 * math.cos(math.pi * x)


def _sharper_night(m):
    """Overlay a 13500-px Black Marble crop (Europe / Africa / Middle East) on the lib's 3600-px night
    map: the close orbital view at the start resolves single cities. Falls back silently if missing."""
    import os
    path, (lo0, lo1, la0, la1) = NIGHT_CROP
    nt = m.node_tree
    night = next((n for n in nt.nodes if n.type == "TEX_IMAGE" and n.image and "dnb" in n.image.name), None)
    if night is None or not os.path.exists(path):
        print("s18a: night crop not used")
        return
    nb = FX.NB(nt)
    uv = night.inputs["Vector"].links[0].from_socket
    # global equirect uv -> crop uv
    cuv = nb.v("MULTIPLY_ADD", uv, (360.0 / (lo1 - lo0), 180.0 / (la1 - la0), 1.0),
               (-(180.0 + lo0) / (lo1 - lo0), -(90.0 + la0) / (la1 - la0), 0.0))
    crop = FX._img(nb, path, cuv, ext="CLIP")
    sx = nb.sep(cuv)
    inside = nb.mul(nb.mul(nb.smooth(nb.out(sx, "X"), 0.0, 0.04), nb.sub(1.0, nb.smooth(nb.out(sx, "X"), 0.96, 1.0))),
                    nb.mul(nb.smooth(nb.out(sx, "Y"), 0.0, 0.05), nb.sub(1.0, nb.smooth(nb.out(sx, "Y"), 0.95, 1.0))))
    links = [l for l in nt.links if l.from_socket == night.outputs["Color"]]
    mixed = nb.mixc(inside, nb.out(night, "Color"), nb.out(crop, "Color"))
    for l in links:
        to = l.to_socket
        nt.links.remove(l)
        nt.links.new(mixed, to)


def build(ctx):
    N = ctx.render_frames
    nf = ctx.nframes
    fc = int(round(ctx.frame(CREST_SEC)))

    e = FX.earth_from_space(ctx, focus=FOCUS, declination=DECL, camera=False, stars=1.0,
                            night_strength=4.5, sun_energy=4.5, cloud_spin=0.8)
    Rg = (Matrix.Rotation(math.radians(FOCUS[1]), 3, "X") @ Matrix.Rotation(math.radians(-90 - FOCUS[0]), 3, "Z"))

    def geo(lon, lat, r=1.0):
        lo, la = math.radians(lon), math.radians(lat)
        return Rg @ Vector((math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la))) * r

    cd, sd = math.cos(math.radians(DECL)), math.sin(math.radians(DECL))
    _sharper_night(e.globe.active_material)
    # faint moonlight so the night hemisphere has shape (clouds / coasts barely readable)
    moon = C.sun(elevation=0, azimuth=0, energy=0.12, color=(0.5, 0.62, 1.0), angle=0.5)
    moon.data.use_shadow = False
    moon.rotation_euler = (-geo(-40.0, 42.0)).to_track_quat("-Z", "Y").to_euler()

    # ------------------------------------------------------------------ terminator sweep (own timing)
    def rate(f):
        r = RATE["r0"] + (RATE["r1"] - RATE["r0"]) * _ease((f - RATE["ra"]) / (RATE["rb"] - RATE["ra"]))
        return r + (RATE["r2"] - RATE["r1"]) * _ease((f - RATE["rc"]) / (RATE["rd"] - RATE["rc"]))
    cum = [0.0]
    for f in range(2, N + 1):
        cum.append(cum[-1] + 0.5 * (rate(f - 1) + rate(f)))

    def cam_pos(f):
        u = (f - 1) / (nf - 1)
        d = CAM["d0"] + (CAM["d1"] - CAM["d0"]) * _ease((f - CAM["da"]) / (nf - CAM["da"]))
        k = _ease(u)
        return geo(CAM["lon0"] + (CAM["lon1"] - CAM["lon0"]) * k, CAM["lat0"] + (CAM["lat1"] - CAM["lat0"]) * k, d * R)

    def sun_dir(f, L0):
        a = math.radians(L0 - cum[min(f, N) - 1] + 90.0)
        return Rg @ Vector((math.cos(a) * cd, math.sin(a) * cd, sd))

    def above_limb(f, L0):
        P = cam_pos(f)
        S = sun_dir(f, L0)
        return math.acos(max(-1, min(1, S.dot(-P.normalized())))) - math.asin(R / P.length)

    # sunrise longitude at frame 1 such that the sun clears the limb exactly at frame fc
    grid = [x * 0.5 for x in range(-120, 400)]
    lo = hi = None
    prev = above_limb(fc, grid[0])
    for x0, x1 in zip(grid, grid[1:]):
        v1 = above_limb(fc, x1)
        if prev > 0 and v1 <= 0:
            lo, hi = x0, x1
            break
        prev = v1
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if above_limb(fc, mid) > 0:
            lo = mid
        else:
            hi = mid
    L0 = 0.5 * (lo + hi)
    print("s18a: sunrise lon %.1f -> %.1f, crest frame %d" % (L0, L0 - cum[-1], fc))

    mats = [e.globe.active_material, e.atmosphere.active_material]
    for f in range(1, N + 1):
        a = math.radians(L0 - cum[f - 1] + 90.0)
        for m in mats:
            s = m.node_tree.nodes["sun_lon"].outputs[0]
            s.default_value = a
            s.keyframe_insert("default_value", frame=f)
        Lw = Rg @ Vector((math.cos(a) * cd, math.sin(a) * cd, sd))
        e.sun.rotation_euler = (-Lw).to_track_quat("-Z", "Y").to_euler()
        e.sun.keyframe_insert("rotation_euler", frame=f)
    for m in mats:
        FX._set_fcurves_linear(m.node_tree, "sun_lon", extrapolate=False)
    C._set_interp(e.sun, "rotation_euler", "LINEAR")
    e.sun_lon = lambda f: math.radians(L0 - cum[max(1, min(N, int(f))) - 1] + 90.0)

    # ------------------------------------------------------------------ sun disc + corona in the world
    wnt = bpy.context.scene.world.node_tree
    nb = FX.NB(wnt)
    bg = next(n for n in wnt.nodes if n.type == "BACKGROUND")
    star_col = bg.inputs["Color"].links[0].from_socket
    sdir = nb.n("ShaderNodeCombineXYZ")
    sdir.name = sdir.label = "sun_dir"
    starfade = nb.n("ShaderNodeValue")
    starfade.name = starfade.label = "star_fade"
    vdir = nb.v("SCALE", nb.v("NORMALIZE", nb.out(nb.n("ShaderNodeNewGeometry"), "Incoming")), scale=-1.0)
    mu = nb.v("DOT_PRODUCT", vdir, nb.out(sdir))
    rad = math.radians(0.42)                          # disc radius (a touch larger than life)
    disc = nb.smooth(mu, math.cos(rad * 1.25), math.cos(rad * 0.8))
    mu0 = nb.m("MAXIMUM", mu, 0.0)
    corona = nb.add(nb.mul(nb.m("POWER", mu0, 9000.0), 30.0), nb.mul(nb.m("POWER", mu0, 600.0), 1.6))
    sun_rgb = nb.v("ADD", nb.v("SCALE", (1.0, 0.93, 0.82), scale=nb.mul(disc, 400.0)),
                   nb.v("SCALE", (1.0, 0.8, 0.55), scale=corona))
    cam_only = nb.out(nb.n("ShaderNodeLightPath"), "Is Camera Ray")
    sun_gain = nb.n("ShaderNodeValue")
    sun_gain.name = sun_gain.label = "sun_gain"
    sun_rgb = nb.v("SCALE", sun_rgb, scale=nb.out(sun_gain))
    col = nb.v("ADD", nb.v("SCALE", star_col, scale=nb.out(starfade)), nb.v("SCALE", sun_rgb, scale=cam_only))
    nb.links.new(col, bg.inputs["Color"])

    # ------------------------------------------------------------------ forward-scatter limb glow shell
    Rs = R * 1.045
    bpy.ops.mesh.primitive_uv_sphere_add(segments=128, ring_count=64, radius=Rs)
    halo = bpy.context.active_object
    halo.name = "Earth_halo"
    halo.data.shade_smooth()
    FX._parent(halo, e.root)
    hm, hb, hout = FX._new_mat("s18a_halo")
    geom = hb.n("ShaderNodeNewGeometry")
    inc = hb.out(geom, "Incoming")
    cosn = hb.m("ABSOLUTE", hb.v("DOT_PRODUCT", hb.out(geom, "Normal"), inc))
    b = hb.m("SQRT", hb.m("MAXIMUM", hb.sub(1.0, hb.mul(cosn, cosn)), 0.0))
    k = R / Rs
    h = hb.div(hb.sub(b, k), 1.0 - k)                 # 0 at the solid limb, 1 at the shell edge, < 0 over the disc
    prof = hb.mul(hb.m("EXPONENT", hb.mul(hb.m("MAXIMUM", h, 0.0), -6.0)), hb.smooth(h, -0.06, 0.0))
    prof = hb.mul(prof, hb.sub(1.0, hb.smooth(h, 0.8, 1.0)))
    hsd = hb.n("ShaderNodeCombineXYZ")
    hsd.name = hsd.label = "sun_dir"
    hmu = hb.v("DOT_PRODUCT", hb.v("SCALE", hb.v("NORMALIZE", inc), scale=-1.0), hb.out(hsd))
    hmu0 = hb.m("MAXIMUM", hmu, 0.0)
    phase = hb.add(hb.add(hb.mul(hb.m("POWER", hmu0, 7.0), 0.9), hb.mul(hb.m("POWER", hmu0, 60.0), 5.0)),
                   hb.mul(hb.m("POWER", hmu0, 900.0), 40.0))
    # only atmosphere that the sun actually reaches (shell point near / past the terminator)
    lit = hb.smooth(hb.v("DOT_PRODUCT", hb.out(geom, "Normal"), hb.out(hsd)), -0.42, 0.05)
    warm = hb.mixc(hb.smooth(h, 0.0, 0.35), (1.0, 0.42, 0.13), (1.0, 0.78, 0.5))
    warm = hb.mixc(hb.m("POWER", hmu0, 400.0), warm, (1.0, 0.92, 0.8))
    glow = hb.v("SCALE", warm, scale=hb.mul(hb.mul(prof, phase), lit))
    # thin green-blue airglow line around the whole limb (defines the night limb against space)
    ag = hb.mul(hb.sub(1.0, hb.smooth(hb.m("ABSOLUTE", hb.sub(h, 0.22)), 0.0, 0.1)), hb.smooth(h, 0.0, 0.05))
    glow = hb.v("ADD", glow, hb.v("SCALE", (0.16, 0.42, 0.3), scale=hb.mul(ag, 0.22)))
    em = hb.n("ShaderNodeEmission", {"Color": glow, "Strength": 1.0})
    tr = hb.n("ShaderNodeBsdfTransparent")
    hb.links.new(hb.out(hb.n("ShaderNodeAddShader", {0: em, 1: tr})), hout.inputs["Surface"])
    FX._blended(hm, backface=False)
    C.assign(halo, hm)
    FX._no_shadow(halo)

    # key the world-space sun direction (world + halo) and the star fade
    for f in range(1, N + 1):
        S = sun_dir(f, L0)
        for node in (sdir, hsd):
            for i, c in enumerate(S):
                node.inputs[i].default_value = c
                node.inputs[i].keyframe_insert("default_value", frame=f)
        # stars fade as the sun clears the limb (eye / exposure adaptation)
        starfade.outputs[0].default_value = 1.0 - 0.85 * C.smoothstep((f - (fc - 30)) / 45.0)
        starfade.outputs[0].keyframe_insert("default_value", frame=f)
    for tree in (wnt, hm.node_tree):
        FX._set_fcurves_linear(tree, "sun_dir", extrapolate=False)
    FX._set_fcurves_linear(wnt, "star_fade", extrapolate=False)

    # ------------------------------------------------------------------ camera
    Pc = cam_pos(fc)
    Sc = sun_dir(fc, L0)
    c_ = Pc.normalized()
    t_ = (Sc - Sc.dot(c_) * c_).normalized()
    g_ = math.acos(R / Pc.length)
    Q = (math.cos(g_) * c_ + math.sin(g_) * t_) * R          # sunrise point on the limb at the crest
    north = Rg @ Vector((0, 0, 1))
    fy = LENS / 18.0
    ax = math.atan((CAM["qx"] - 0.5) * 2 * (9 / 16) / fy)
    ay = math.atan((0.5 - CAM["qy"]) * 2 / fy)

    def aim(P, target, up):
        fwd = (target - P).normalized()
        x = fwd.cross(up).normalized()
        y = x.cross(fwd)
        f2 = Quaternion(y, ax) @ fwd
        f2 = Quaternion(f2.cross(up).normalized(), -ay) @ f2
        return f2.normalized()

    cam = C.camera((0, -R * 3, 0), (0, 0, 0), lens=LENS, clip_end=R * 40)
    cam.data.clip_start = R * 0.01
    cam.rotation_mode = "QUATERNION"
    prevq = None
    for f in range(1, N + 1):
        P = cam_pos(f)
        upr = P.normalized()
        w = _ease((f - CAM["wa"]) / (nf - CAM["wa"]))
        F1 = aim(P, Q, upr)
        F2 = (geo(CAM["end_lon"], CAM["end_lat"], R * CAM["end_off"]) - P).normalized()
        F = (F1 * (1 - w) + F2 * w).normalized()
        up = (upr * (1 - w) + north * w).normalized()
        x = F.cross(up).normalized()
        y = x.cross(F)
        m = Matrix((x, y, -F)).transposed()
        q = m.to_quaternion()
        roll = CAM["roll0"] + (CAM["roll1"] - CAM["roll0"]) * w
        q = q @ Quaternion((0, 0, 1), math.radians(roll))
        if prevq is not None and q.dot(prevq) < 0:
            q.negate()
        prevq = q.copy()
        cam.location = P
        cam.rotation_quaternion = q
        cam.keyframe_insert("location", frame=f)
        cam.keyframe_insert("rotation_quaternion", frame=f)
    C._set_interp(cam, "location", "LINEAR")
    C._set_interp(cam, "rotation_quaternion", "LINEAR")

    # the compositor glare only sees in-frame pixels: fade the sun disc as it nears the frame edge so
    # the starburst dies away smoothly instead of popping off when the disc leaves the frame
    gsock = sun_gain.outputs[0]
    for f in range(1, N + 1):
        bpy.context.scene.frame_set(f)
        v = cam.matrix_world.to_3x3().inverted() @ sun_dir(f, L0)
        g = 0.0
        if v.z < 0:
            xi = 0.5 + (v.x / -v.z) * fy / (2 * 9 / 16)
            yi = 0.5 - (v.y / -v.z) * fy / 2
            margin = min(xi, 1 - xi, yi, 1 - yi)
            g = 0.05 + 0.95 * C.smoothstep((margin + 0.01) / 0.24)
        gsock.default_value = g
        gsock.keyframe_insert("default_value", frame=f)
    bpy.context.scene.frame_set(1)
    FX._set_fcurves_linear(wnt, "sun_gain", extrapolate=False)

    # ------------------------------------------------------------------ compositor glare (sun only)
    sc = bpy.context.scene
    sc.use_nodes = True
    ct = sc.node_tree
    for n in list(ct.nodes):
        ct.nodes.remove(n)
    rl = ct.nodes.new("CompositorNodeRLayers")
    fog = ct.nodes.new("CompositorNodeGlare")
    fog.glare_type = "BLOOM"
    fog.quality = "MEDIUM"
    fog.inputs["Threshold"].default_value = 8.0
    fog.inputs["Strength"].default_value = 0.5
    fog.inputs["Size"].default_value = 0.8
    st = ct.nodes.new("CompositorNodeGlare")
    st.glare_type = "STREAKS"
    st.quality = "MEDIUM"
    st.inputs["Threshold"].default_value = 60.0
    st.inputs["Strength"].default_value = 0.16
    st.inputs["Streaks"].default_value = 8
    st.inputs["Streaks Angle"].default_value = math.radians(14)
    st.inputs["Fade"].default_value = 0.86
    out = ct.nodes.new("CompositorNodeComposite")
    ct.links.new(rl.outputs["Image"], fog.inputs["Image"])
    ct.links.new(fog.outputs["Image"], st.inputs["Image"])
    ct.links.new(st.outputs["Image"], out.inputs["Image"])
    sc.render.use_compositing = True

    ctx.samples = 6
    ctx.interp = True      # slow, coherent motion; RIFE validated on the sunburst (32 dB @3spp, warp_err < 3.6)
    ctx.render_opts.update({"volumetrics": "low"})
    ctx.post.update({"grade": "space", "bloom": 0.35, "bloom_threshold": 0.62, "halation": 0.1,
                     "vignette": 0.12, "caption": {"halo": 1.15},
                     "end": {"exposure": 0.12, "temperature": 0.12}})
