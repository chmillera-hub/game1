"""s20c - "He has done it!" - finale under the end card.

The EMPTY cross on Golgotha at sunrise (bookend of s00: same hill, same cross, the light transformed).
A long white linen cloth is draped over the crossbeam - gathered behind the upright, both halves falling
in front of the beam either side of it - and stirs in the morning breeze. The sun breaks through a cloud
bank over Jerusalem with rays bursting upward. The camera starts low at the foot of the cross looking up
at the beam and the cloth ("He has done it!"), then cranes up past the crossbeam and settles (frame ~150)
level with the top of the cross, the sunburst straight above it and the frame centre clear for the end
card ('Psalm 22 . NIV' / 'It is finished.', from ~frame 97).

Cloth: a real cloth simulation with a 60-frame pre-roll, baked in memory inside build() (~50 s), so any
frame list renders correctly; ctx.needs_bake stays False on purpose (a second bake_all would only cost
time). Sky helpers (sky_fx, cull_scatter) are shared with shots/s00.py.
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
def _drape_mesh(width=0.46, tail=1.25, back_y=0.155, z0=3.885, step=0.016, nw=28, gather=0.16, spread=0.2,
                trim_left=0.0, panel_gather=0.72, pleat_cols=8):
    """Initial (pre-simulation) linen strip in the cross root's local frame (core.wooden_cross: beam top
    z = 3.868, beam y = -0.10..0.08, upright |x| < 0.1, |y| < 0.095), lying flat at beam-top height:
    its middle is gathered into a narrow band behind the upright (pinned), from there it runs round both
    sides of the upright over the beam top and sticks out horizontally in front of the beam. In the
    pre-roll the two halves fall over the front edge of the beam and hang as two panels either side of
    the upright, the cloth fanning out of the gathered middle in folds (the classic shroud on the empty
    cross). Returns verts (n, nw+1, 3), pin (n, nw+1), row arc length, column offsets."""
    # plan-view centerline for the right half (x >= 0), mirrored for the left
    ctrl = np.array([(0.0, back_y), (0.10, back_y + 0.005), (0.17, 0.10), (0.22, 0.0), (0.26, -0.12),
                     (0.29, -0.30)] + [(0.29 + spread * (k / 6.0), -0.30 - tail * k / 6.0) for k in range(1, 7)])
    seg = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(ctrl, axis=0), axis=1))]
    sn_h = np.linspace(0.0, seg[-1], int(seg[-1] / step) + 1)
    hx = np.interp(sn_h, seg, ctrl[:, 0])
    hy = np.interp(sn_h, seg, ctrl[:, 1])
    # light smoothing of the polyline
    for _ in range(6):
        hx[1:-1] = 0.25 * hx[:-2] + 0.5 * hx[1:-1] + 0.25 * hx[2:]
        hy[1:-1] = 0.25 * hy[:-2] + 0.5 * hy[1:-1] + 0.25 * hy[2:]
    px = np.r_[-hx[::-1], hx[1:]]
    py = np.r_[hy[::-1], hy[1:]]
    sn = np.r_[-sn_h[::-1], sn_h[1:]]
    P = np.stack([px, py], 1)
    Tg = np.gradient(P, axis=0)
    Tg /= np.linalg.norm(Tg, axis=1, keepdims=True)
    Wd = np.stack([-Tg[:, 1], Tg[:, 0]], 1)
    # width: gathered behind the upright, opening out over the beam top
    # the panels stay partly gathered too (panel_gather < 1): their extra width is stored in soft sine pleats
    # (period pleat_cols columns, phase wandering along the strip), so they hang in real vertical folds
    g = gather + (panel_gather - gather) * np.clip((np.abs(sn) - 0.12) / 0.45, 0.0, 1.0) ** 1.2
    us = np.linspace(-0.5, 0.5, nw + 1) * width
    lam = pleat_cols * width / nw
    amp = (g * lam / np.pi) * np.sqrt(np.clip(1.0 / g - 1.0, 0.0, None))      # keeps the arc length ~ width
    ph = 2 * np.pi * np.arange(nw + 1)[None, :] / pleat_cols + 0.9 * np.sin(sn * 2.7)[:, None] \
        + 0.5 * np.sin(sn * 7.3 + 1.0)[:, None]
    V = np.zeros((len(P), nw + 1, 3))
    V[..., 0] = P[:, None, 0] + Wd[:, None, 0] * us[None, :] * g[:, None]
    V[..., 1] = P[:, None, 1] + Wd[:, None, 1] * us[None, :] * g[:, None]
    V[..., 2] = z0 + 0.03 + amp[:, None] * np.sin(ph)
    pin = ((np.abs(sn) < 0.10)[:, None] & np.ones((1, nw + 1), bool)).astype(float)
    k = int(round(trim_left / step))            # shorter left half: hangs asymmetrically, less "apron"-like
    if k > 0:
        V, pin, sn = V[k:], pin[k:], sn[k:]
    return V, pin, sn - sn[0], us


def linen_swag(ctx, cross_root, width=0.46, preroll=60, wind=None, name="Linen", **drape):
    """Build the linen cloth on a core.wooden_cross root (any location / rot_z): a strip (_drape_mesh)
    simulated with a Cloth modifier (pinned where it is gathered behind the upright), the cross parts as
    colliders and a gusting wind field. The cache starts at 1 - preroll so the drape has settled by frame 1
    (bake_cloth() must run after the scene is complete)."""
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
    st.quality = 6
    st.mass = 0.26
    st.tension_stiffness = st.compression_stiffness = 15.0
    st.shear_stiffness = 3.0
    st.bending_stiffness = 0.025
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


def _frustum_fn(keys, lens, margin_deg=3.0):
    """cull_scatter predicate: True where an instance is outside the frustum of every camera key
    (key = (loc, target, ...)); portrait frame, vertical sensor 36 mm."""
    hh = math.atan(18.0 * 9.0 / 16.0 / lens) + math.radians(margin_deg)
    hv = math.atan(18.0 / lens) + math.radians(margin_deg)

    def pred(x, y, z, size):
        hidden = np.ones(len(x), bool)
        for k in keys:
            loc, tgt = Vector(k[0]), Vector(k[1])
            f = (tgt - loc).normalized()
            r = f.cross(Vector((0, 0, 1))).normalized()
            u = r.cross(f)
            dx, dy, dz = x - loc.x, y - loc.y, z + 0.6 * size - loc.z
            df = dx * f.x + dy * f.y + dz * f.z
            dr = dx * r.x + dy * r.y + dz * r.z
            du = dx * u.x + dy * u.y + dz * u.z
            ext = 1.0 * size
            inside = (df > 0.05) & (np.abs(dr) - ext < df * math.tan(hh)) & (np.abs(du) - ext < df * math.tan(hv))
            hidden &= ~inside
        return hidden
    return pred


SUN_AZ = 170.0                      # sunrise behind the cross, over Jerusalem (core az; 180 = +Y)
LAMP_EL = 7.0                       # sun lamp elevation (HDRI sun ~4.7 deg, hidden in the cloud bank)
CAM0 = ((-1.3, -4.4, 12.05), (0.0, 0.6, 14.45), 28.0)     # low at the foot of the cross, up at the beam
CAM1 = ((-1.08, -5.5, 15.6), (170.0, 8.0), 28.0)         # level with the top of the cross, (core az, pitch):
                                                           # the sun breaks out straight above it
SUNRISE_MAP = [(0.0, (0.9, 0.92, 1.3)), (0.25, (1.05, 0.97, 1.05)), (0.45, (1.3, 0.96, 0.62)),
               (0.65, (1.3, 0.97, 0.62)), (0.85, (1.15, 1.0, 0.8)), (1.0, (1.03, 1.0, 0.95))]
MOVE_F = 150                        # the crane settles here (end card fades in ~frame 97: frame clear by then)


def build(ctx):
    N = ctx.render_frames
    (l0, t0, lens0), (l1, (az1, pitch1), lens1) = CAM0, CAM1
    d0 = Vector(t0) - Vector(l0)
    az0 = _az(d0)
    pitch0 = math.degrees(math.atan2(d0.z, d0.xy.length))
    t1 = tuple(Vector(l1) + _dir(az1, pitch1) * 30.0)
    views = [dict(loc=l0, target=t0, lens=lens0, near=12.0), dict(loc=l1, target=t1, lens=lens1, near=12.0)]
    over = dict(hdri=HDRI, sun_el=LAMP_EL, sun_energy=3.4, key=0.58, strength=0.5, tint=(1.0, 0.88, 0.72), sat=1.3,
                sun_tint=(1.0, 0.72, 0.45), sun_angle=1.2, clamp_sun=None)
    A = E.golgotha(ctx, mood="sunrise", sun_az=SUN_AZ, crosses=1, center_occupied=False, sign=False,
                   sky_over=over, view=views, dust=False, near_detail=0.0, grass=1.0, bushes=0.6, city=False,
                   skull=0.0)                          # the skull cliff is behind the camera all shot
    S = A["sky"]
    info = E.hdri_info(HDRI)
    sun_vis = _dir(SUN_AZ, info["sun_el"])
    # low-lying golden morning haze: softens the plain and the distant city into the sunrise
    E.set_haze(sun_dir=tuple(sun_vis), sun_mix=0.95, sun_power=3.0, density=0.0035, falloff=0.025, start=8.0)
    try:
        from shots.s00 import sky_fx
        sky_fx(S, sun_vis, rays=0.16, ray_keys=[(1, 0.0), (N, 0.5)], grad=0.25, grad_tint=(0.72, 0.66, 0.7),
               glow=0.9, glow_color=(1.55, 1.0, 0.5), glow_width=0.45, gmap=SUNRISE_MAP, gmix=0.3, prefix="sfx20")
    except Exception as e:
        print("s20c: sky_fx unavailable (%s)" % e)

    cross = A["crosses"]["center"]
    beam = Vector(cross["beam"])

    def path(f):
        x = (f - 1) / float(MOVE_F - 1)
        drift = 0.05 * max(0.0, (f - MOVE_F) / float(max(1, N - MOVE_F)))     # keeps drifting after it settles
        u = 0.95 * C.ease_in_out(x) + drift
        loc = Vector(l0).lerp(Vector(l1), u)
        # rise first, tilt down a little later (the cross sinks through the frame, the sunrise opens up)
        ut = 0.95 * C.ease_in_out(min(1.0, max(0.0, (x - 0.08) / 0.92))) + drift
        tgt = loc + _dir(az0 + (az1 - az0) * ut, pitch0 + (pitch1 - pitch0) * ut) * 10.0
        foc = (beam - loc).length
        return (loc, tgt, 0.0, lens0, foc)

    # drop scattered instances the moving camera never sees (frustum test along the whole path)
    try:
        from shots.s00 import cull_scatter
        keys = [path(f) for f in range(1, N + 1, 8)] + [path(N)]
        k = cull_scatter(("Env",), _frustum_fn(keys, lens0))
        print("s20c: culled %d unseen scatter instances" % k)
    except Exception as e:
        print("s20c: scatter cull skipped (%s)" % e)

    cl = linen_swag(ctx, cross["root"], preroll=60, width=0.6, tail=1.45, spread=0.45, gather=0.16, trim_left=0.4,
                    wind=dict(strength=7.0, noise=0.7, dir=(-0.75, 0.55, 0.12)))
    bake_cloth(ctx)

    cam = C.camera(loc=l0, target=t0, lens=lens0, name="Cam", fstop=5.6, focus=4.8)
    C.animate_camera(cam, path, 1, N)

    ctx.samples = 4
    ctx.render_opts.update({"volumetrics": "low", "shadow_scale": 0.5})
    ctx.interp = True
    ctx.post.update({"grade": "gold", "bloom": 0.48, "bloom_threshold": 0.6, "contrast": 1.06, "vignette": 0.12})
