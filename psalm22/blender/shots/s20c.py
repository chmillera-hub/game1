"""s20c - "He has done it!" - finale under the end card.

The EMPTY cross on Golgotha at sunrise (bookend of s00: same hill, same cross, the light transformed).
A long white linen cloth is draped over the crossbeam - a swag in front of the upright, both ends hanging
behind the arms - and stirs in the morning breeze (short cloth simulation, baked in build()). The sun
breaks through a cloud bank behind the cross with rays bursting upward. The camera starts low at the foot
of the cross looking up at the beam and the cloth, then cranes up past the crossbeam into the light: the
sunrise over Jerusalem fills the frame for the end card ('Psalm 22 . NIV' / 'It is finished.').
"""
import math
import bpy
import numpy as np
from mathutils import Vector
from lib import core as C, env as E

HDRI = "kloppenheim_06_puresky"


def _dir(az, el):
    a, e = math.radians(az), math.radians(el)
    return Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))


def _az(d):
    return math.degrees(math.atan2(d.x, -d.y))


# ------------------------------------------------------------------------------------------------
# The linen cloth
# ------------------------------------------------------------------------------------------------
def _drape_mesh(length=4.4, width=0.5, swag=0.95, pin_x=(0.5, 0.72), z0=3.885, y0=-0.01, step=0.02, nw=24,
                gather=0.3, gather_len=0.3, front=-0.13):
    """Initial (pre-simulation) linen piece in the cross root's local frame (core.wooden_cross: beam top
    z = 3.868, beam y = -0.10..0.08, upright |x| < 0.1), lying flat and horizontal at beam-top height.
    Rows run along x. Outside the tie points it is a strip lying along the arms (and sticking out past the
    arm tips); between the ties it is a crescent (cut like a window swag): the inner edge runs just in
    front of the beam (little slack -> the top edge hangs nearly straight), the outer edge bulges `swag` m
    forward (lots of slack -> the deep curve of the swag). At the ties the width is gathered into accordion
    pleats (edge lengths preserved) so folds fan out of them. The tie zones on the beam top are pinned.
    Returns verts (n, nw+1, 3), pin (n, nw+1), row arc length, column offsets."""
    xs = np.linspace(-length / 2, length / 2, int(length / step) + 1)
    xm = 0.5 * (pin_x[0] + pin_x[1])
    xb = pin_x[0]
    d = np.minimum(np.abs(xs - xm), np.abs(xs + xm))
    g = 1.0 - (1.0 - gather) * np.clip(1.0 - d / gather_len, 0.0, 1.0) ** 1.5
    inside = np.abs(xs) < xb
    t = np.where(inside, 0.5 + 0.5 * np.cos(np.pi * xs / xb), 0.0)          # 0 at the ties, 1 at the centre
    w = width * g
    y_in = y0 + 0.5 * w
    y_out = y0 - 0.5 * w
    k = np.clip(t / 0.55, 0.0, 1.0)
    k = k * k * (3 - 2 * k)
    y_in = np.where(inside, (1 - k) * y_in + k * front, y_in)
    y_out = np.where(inside, np.minimum(y_in - w, y_out) - swag * t ** 0.85, y_out)
    us = np.linspace(0.0, 1.0, nw + 1)
    V = np.zeros((len(xs), nw + 1, 3))
    V[..., 0] = xs[:, None]
    V[..., 1] = y_in[:, None] + (y_out - y_in)[:, None] * us[None, :]
    # accordion pleats across the gathered tie zones (keep each cross edge about its ungathered length)
    du = (width / nw)
    span = np.abs(y_out - y_in) / nw
    amp = 0.5 * np.sqrt(np.clip(du * du - span * span, 0.0, None)) * (g < 0.999)
    alt = np.where(np.arange(nw + 1) % 2 == 0, 1.0, -1.0)
    V[..., 2] = z0 + 0.012 + amp[:, None] * alt[None, :]
    ax = np.abs(V[..., 0])
    on_beam = np.abs(V[..., 1] - y0) < 0.085
    pin = ((ax > pin_x[0] + 0.03) & (ax < pin_x[1] - 0.03) & on_beam).astype(float)
    sn = xs - xs[0]
    return V, pin, sn, (us - 0.5) * width


def linen_swag(ctx, cross_root, width=0.48, preroll=60, wind=None, name="Linen", **drape):
    """Build the linen cloth on a core.wooden_cross root (any location / rot_z): a strip (_drape_mesh)
    simulated with a Cloth modifier pinned at two tie points on the beam top, the cross parts as colliders
    and a gusting wind field. The cache starts at 1 - preroll so the drape has settled by frame 1."""
    V, pin, sn, us = _drape_mesh(width=width, **drape)
    n, nw1 = V.shape[0], V.shape[1]
    nw = nw1 - 1
    verts = V.reshape(-1, 3)
    faces = []
    for i in range(n - 1):
        for j in range(nw):
            a = i * nw1 + j
            faces.append((a, a + nw1, a + nw1 + 1, a + 1))
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    uv = me.uv_layers.new(name="UVMap")
    lo = np.array([l.vertex_index for l in me.loops])
    vi, vj = lo // nw1, lo % nw1
    uvs = np.stack([us[vj], sn[vi]], 1).astype(np.float32)
    uv.data.foreach_set("uv", uvs.ravel())
    ob = C.link(bpy.data.objects.new(name, me))
    ob.parent = cross_root
    for p in me.polygons:
        p.use_smooth = True
    vg = ob.vertex_groups.new(name="pin")
    pw = pin.reshape(-1)
    idx = [int(i) for i in np.nonzero(pw > 0)[0]]
    if idx:
        vg.add(idx, 1.0, "REPLACE")
    ob.data.materials.append(linen_material())
    # colliders: the cross parts
    for ch in cross_root.children:
        if ch.type == "MESH" and not any(m.type == "COLLISION" for m in ch.modifiers):
            ch.modifiers.new("Collision", "COLLISION")
            ch.collision.thickness_outer = 0.012
            ch.collision.cloth_friction = 8.0
    sc = bpy.context.scene
    m = ob.modifiers.new("Cloth", "CLOTH")
    st = m.settings
    st.quality = 7
    st.mass = 0.15
    st.tension_stiffness = st.compression_stiffness = 15.0
    st.shear_stiffness = 5.0
    st.bending_stiffness = 0.08
    st.air_damping = 1.0
    st.tension_damping = st.compression_damping = 5.0
    st.bending_damping = 0.5
    st.vertex_group_mass = "pin"
    st.pin_stiffness = 1.0
    st.effector_weights.gravity = 1.0
    cs = m.collision_settings
    cs.use_collision = True
    cs.distance_min = 0.006
    cs.collision_quality = 3
    cs.use_self_collision = False
    m.point_cache.frame_start = 1 - preroll
    m.point_cache.frame_end = ctx.render_frames
    so = ob.modifiers.new("Thick", "SOLIDIFY")
    so.thickness = 0.0025
    so.offset = 0.0
    sub = ob.modifiers.new("Smooth", "SUBSURF")
    sub.levels = sub.render_levels = 1
    # breeze: a wind field with turbulence, gusting slowly (strength keyed with a smooth noise)
    w = wind or dict(strength=9.0, noise=0.6, dir=(-0.8, 0.45, 0.1))
    bpy.ops.object.effector_add(type="WIND", location=(0, 0, 0))
    fo = bpy.context.active_object
    fo.name = name + "_Wind"
    fo.field.shape = "PLANE"
    fo.field.noise = w["noise"]
    fo.field.seed = 7
    fo.field.flow = 0.6
    d = Vector(w["dir"]).normalized()
    fo.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    fo.location = cross_root.matrix_world @ Vector((0, 0, 3.6)) - d * 3.0
    fo.field.falloff_type = "SPHERE"
    fo.field.use_max_distance = True
    fo.field.distance_max = 4.0
    fs = fo.field
    for f in range(1 - preroll, ctx.render_frames + 1, 6):
        g = 0.65 + 0.35 * math.sin(f * 0.045) + 0.25 * math.sin(f * 0.11 + 1.3)
        fs.strength = w["strength"] * max(0.25, g)
        fs.keyframe_insert("strength", frame=f)
    return ob


def linen_material():
    """Bleached linen: rough, faint weave bump, strong translucency (glows when backlit)."""
    m = bpy.data.materials.get("S20c_Linen")
    if m:
        return m
    try:
        m = C.mat_pbr("rough_linen", scale=2.2, projection="UV", tint=(1.0, 1.0, 1.0), name="S20c_Linen", bump=0.6,
                      hue_sat_val=(0.5, 0.15, 1.35))
    except Exception as e:
        print("s20c: linen texture unavailable (%s)" % e)
        m = C.mat("S20c_Linen", color=(0.86, 0.84, 0.78), rough=0.85)
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Sheen Weight"].default_value = 0.35
    b.inputs["Specular IOR Level"].default_value = 0.25
    out = nt.nodes["Material Output"]
    tr = nt.nodes.new("ShaderNodeBsdfTranslucent")
    tr.inputs["Color"].default_value = (0.95, 0.88, 0.74, 1)
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs[0].default_value = 0.38
    nt.links.new(b.outputs[0], mix.inputs[1])
    nt.links.new(tr.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    m.use_backface_culling = False
    E.hazify(m)
    return m


def bake_cloth(ctx):
    sc = bpy.context.scene
    fc = sc.frame_current
    t = __import__("time").time()
    try:
        with bpy.context.temp_override(scene=sc):
            bpy.ops.ptcache.bake_all(bake=True)
    except Exception as e:
        print("s20c: cloth bake warning:", e)
    sc.frame_set(fc)
    print("s20c: cloth baked in %.1fs" % (__import__("time").time() - t), flush=True)


SUN_AZ = 170.0                      # sunrise behind the cross, over Jerusalem (core az; 180 = +Y)
LAMP_EL = 7.0                       # sun lamp elevation (HDRI sun ~4.7 deg, hidden in the cloud bank)
CAM0 = ((-1.3, -4.4, 12.05), (0.0, 0.6, 14.45), 28.0)     # low at the foot of the cross, up at the beam
CAM1 = ((-0.9, -4.6, 15.9), (172.0, 7.0), 28.0)           # above the crossbeam: (core az, pitch) into the sun
SUNRISE_MAP = [(0.0, (0.9, 0.92, 1.3)), (0.25, (1.05, 0.97, 1.05)), (0.45, (1.3, 0.96, 0.62)),
               (0.65, (1.3, 0.97, 0.62)), (0.85, (1.15, 1.0, 0.8)), (1.0, (1.03, 1.0, 0.95))]
MOVE_END = 0.93                     # fraction of the shot where the crane settles


def build(ctx):
    N = ctx.render_frames
    (l0, t0, lens0), (l1, (az1, pitch1), lens1) = CAM0, CAM1
    d0 = Vector(t0) - Vector(l0)
    az0 = _az(d0)
    pitch0 = math.degrees(math.atan2(d0.z, d0.xy.length))
    t1 = tuple(Vector(l1) + _dir(az1, pitch1) * 30.0)
    views = [dict(loc=l0, target=t0, lens=lens0, near=12.0), dict(loc=l1, target=t1, lens=lens1, near=12.0)]
    over = dict(hdri=HDRI, sun_el=LAMP_EL, sun_energy=3.4, key=0.62, tint=(1.0, 0.88, 0.72), sat=1.2,
                sun_tint=(1.0, 0.72, 0.45), sun_angle=1.2, clamp_sun=None)
    A = E.golgotha(ctx, mood="sunrise", sun_az=SUN_AZ, crosses=1, center_occupied=False, sign=False,
                   sky_over=over, view=views, dust=False, near_detail=1.0)
    S = A["sky"]
    info = E.hdri_info(HDRI)
    sun_vis = _dir(SUN_AZ, info["sun_el"])
    E.set_haze(sun_dir=tuple(sun_vis), sun_mix=0.9, sun_power=4.0)
    try:
        from shots.s00 import sky_fx
        sky_fx(S, sun_vis, rays=0.16, ray_keys=[(1, 0.0), (N, 0.5)], grad=0.25, grad_tint=(0.72, 0.66, 0.7),
               glow=0.55, glow_color=(1.45, 1.0, 0.6), glow_width=0.4, gmap=SUNRISE_MAP, gmix=0.45, prefix="sfx20")
    except Exception as e:
        print("s20c: sky_fx unavailable (%s)" % e)

    cross = A["crosses"]["center"]
    cl = linen_swag(ctx, cross["root"], preroll=60, width=0.5, length=4.4, swag=0.95, pin_x=(0.5, 0.72), gather=0.3,
                    wind=dict(strength=9.0, noise=0.7, dir=(-0.75, 0.55, 0.12)))
    bake_cloth(ctx)

    cam = C.camera(loc=l0, target=t0, lens=lens0, name="Cam", fstop=5.6, focus=4.8)
    beam = Vector(cross["beam"])

    def path(f):
        u = C.ease_in_out((f - 1) / max(1.0, (N - 1) * MOVE_END))
        loc = Vector(l0).lerp(Vector(l1), u)
        # rise first, tilt down a little later (the cross sinks through the frame, the sunrise opens up)
        ut = C.ease_in_out(min(1.0, max(0.0, ((f - 1) / max(1.0, (N - 1) * MOVE_END) - 0.08) / 0.92)))
        tgt = loc + _dir(az0 + (az1 - az0) * ut, pitch0 + (pitch1 - pitch0) * ut) * 10.0
        foc = (beam - loc).length + 25.0 * max(0.0, ut - 0.55)
        return (loc, tgt, 0.0, lens0, foc)
    C.animate_camera(cam, path, 1, N)

    ctx.samples = 6
    ctx.render_opts.update({"volumetrics": "low"})
    ctx.interp = True
    ctx.post.update({"grade": "glory", "bloom": 0.5, "vignette": 0.12})
