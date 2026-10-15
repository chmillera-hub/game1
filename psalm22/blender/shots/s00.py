"""s00 - Golgotha, title shot (frame 1 = the social-media thumbnail).

Three crosses with small crucified silhouettes on the skull-faced hill, seen from the plain at golden
light. The sun hangs low just right of the centre cross, partly veiled; crepuscular rays fan out of it
through the haze, towering clouds stand to the left and a dark storm front creeps in from the left
(the darkness of s01a+ is coming). Slow push-in and gentle rise. The upper-middle sky stays calm for the
'PSALM 22 / A Psalm of David' title (added by the compositor).
"""
import math
import bpy
import numpy as np
from mathutils import Vector
from lib import core as C, env as E

HDRI = "table_mountain_2_puresky"
VIS_SUN_OFF = (2.6, None)        # visible sun: degrees right of the view axis, elevation (None = HDRI's)
LAMP = (152.0, 13.0)             # sun lamp (core az, el): back-right, low -> rims + raking light on the cliff
CAM0 = ((0.0, -59.5, 7.5), (0.0, 0.6, 16.7), 70.0)    # loc, target, lens at frame 1
CAM1 = ((0.0, -53.0, 8.6), (0.0, 0.6, 17.0), 70.0)     # at the end of the tail
GOLD_MAP = [(0.0, (0.85, 0.95, 1.35)), (0.2, (1.0, 0.98, 1.05)), (0.4, (1.35, 0.95, 0.55)),
            (0.6, (1.4, 0.93, 0.45)), (0.8, (1.25, 0.97, 0.65)), (1.0, (1.05, 1.0, 0.92))]


def _dir(az, el):
    a, e = math.radians(az), math.radians(el)
    return Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))


def _az(d):
    return math.degrees(math.atan2(d.x, -d.y))


def _uniform(T, name, value, keys=None):
    """Scene-property uniform (cheap to animate). keys = [(frame, value), ...] -> linear."""
    E.scene_prop(name, value)
    if keys:
        for f, v in keys:
            E.scene_prop(name, v, f)
        E._linear_keys(bpy.context.scene)
    return E._lattr(T, name, value)


def sky_fx(S, sun_vis, rays=0.55, ray_keys=None, storm=0.0, storm_keys=None, storm_tint=(0.30, 0.27, 0.29),
           grad=0.35, grad_tint=(0.62, 0.55, 0.52), veil=0.0, gmap=None, gmix=0.75, gk=0.5, glow=0.0,
           glow_color=(1.5, 1.0, 0.55), glow_width=0.35, prefix="sfx"):
    """Camera-only sky treatment spliced in front of the env sky's background shader:
    crepuscular rays radiating from sun_vis, a graduated darkening of the upper sky, and a dark storm
    front from screen-left (edge animated through `storm_keys` = [(frame, edge)])."""
    nt = bpy.context.scene.world.node_tree
    T = E._NT(nt)
    bg = S["nodes"]["bg"]
    src = bg.inputs[0].links[0].from_socket
    tc = T.node("ShaderNodeTexCoord")
    vn = T.vmath("NORMALIZE", tc.outputs["Generated"])
    vx, vy, vz = T.sep(vn)
    s = Vector(sun_vis).normalized()
    a = s.cross(Vector((0, 0, 1))).normalized()          # screen-right around the sun
    b = a.cross(s).normalized()                           # up around the sun
    da = T.vmath("DOT_PRODUCT", vn, tuple(a))
    db = T.vmath("DOT_PRODUCT", vn, tuple(b))
    ds = T.vmath("DOT_PRODUCT", vn, tuple(s))
    col = src
    # --- crepuscular rays ----------------------------------------------------------------------
    if rays:
        # seamless: noise sampled on a circle around the sun (angle only -> radial shafts)
        q = T.vmath("NORMALIZE", T.comb(da, T.math("MULTIPLY", db, -1.0), 0.0))
        th = T.math("ARCCOSINE", T.math("MINIMUM", T.math("MAXIMUM", ds, -1.0), 1.0))
        drift = _uniform(T, prefix + "_ray_drift", 0.0, ray_keys)
        n1 = T.noise(T.vmath("ADD", T.vmath("SCALE", q, scale=2.2), T.comb(0.0, 0.0, drift)),
                     scale=1.0, detail=1.0, rough=0.5)
        n2 = T.noise(T.vmath("ADD", T.vmath("SCALE", q, scale=6.5), T.comb(3.1, 0.0, T.math("MULTIPLY", drift, 1.7))),
                     scale=1.0, detail=0.0, rough=0.5)
        r1 = T.smooth(0.36, 0.64, n1.outputs["Fac"])
        r2 = T.smooth(0.36, 0.66, n2.outputs["Fac"])
        r = T.math("ADD", T.math("MULTIPLY", r1, 0.62), T.math("MULTIPLY", r2, 0.38))
        f_in = T.smooth(0.015, 0.09, th)
        f_out = T.math("SUBTRACT", 1.0, T.smooth(0.25, 0.95, th))
        fall = T.math("MULTIPLY", f_in, f_out)
        amt = _uniform(T, prefix + "_rays", rays)
        m = T.math("ADD", 1.0, T.math("MULTIPLY", T.math("MULTIPLY", T.math("SUBTRACT", r, 0.42), fall), amt))
        warm = T.comb(m, T.math("MULTIPLY_ADD", m, 0.97, 0.03), T.math("MULTIPLY_ADD", m, 0.9, 0.1))
        col = T.mix(1.0, col, warm, blend="MULTIPLY")
    # --- veil: thin cloud streaks crossing the sun ------------------------------------------------
    if veil:
        # coordinates on a plane through the sun: (da, db) ~ angular offsets (radians)
        pv = T.comb(T.math("MULTIPLY", da, 3.0), T.math("MULTIPLY", db, 22.0), 0.0)
        nv = T.noise(pv, scale=1.0, detail=4.0, rough=0.55, dist=0.3)
        dens = T.math("MULTIPLY", T.smooth(0.46, 0.70, nv.outputs["Fac"]),
                      T.math("SUBTRACT", 1.0, T.smooth(0.03, 0.10, T.math("ABSOLUTE", db))))
        dens = T.math("MULTIPLY", dens, T.math("SUBTRACT", 1.0, T.smooth(0.10, 0.25, T.math("ABSOLUTE", da))))
        dens = T.math("MULTIPLY", dens, veil)
        vc = T.mix(T.math("MULTIPLY", dens, 0.85), col, (0.55, 0.36, 0.22), blend="MULTIPLY")
        col = vc
    # --- graduated darkening of the upper sky -------------------------------------------------
    if grad:
        g = T.math("MULTIPLY", T.smooth(0.10, 0.48, vz), grad)
        col = T.mix(g, col, tuple(grad_tint), blend="MULTIPLY")
    # --- storm front from screen-left ------------------------------------------------------------
    if storm:
        t = T.math("DIVIDE", 1.0, T.math("MAXIMUM", vz, 0.035))
        pc = T.comb(T.math("MULTIPLY", vx, t), T.math("MULTIPLY", vy, t), 0.0)
        tw = _uniform(T, prefix + "_storm_time", 0.0, None)
        pc = T.vmath("ADD", T.vmath("SCALE", pc, scale=0.9), T.comb(tw, 0.0, T.math("MULTIPLY", tw, 0.3)))
        cn = T.noise(pc, scale=1.0, detail=6.0, rough=0.6, dist=0.25).outputs["Fac"]
        edge = _uniform(T, prefix + "_storm_edge", 0.1, storm_keys)
        x = T.math("ADD", T.math("MULTIPLY", da, -1.0), T.math("MULTIPLY", vz, 0.45))
        x = T.math("ADD", x, T.math("MULTIPLY", T.math("SUBTRACT", cn, 0.5), 0.22))
        # smoothstep with an animated edge: (x - edge) / width
        u = T.math("DIVIDE", T.math("SUBTRACT", x, edge), 0.09)
        sm = T.smooth(0.0, 1.0, u)
        sm = T.math("MULTIPLY", sm, storm)
        dark = T.mix(T.smooth(0.35, 0.75, cn), tuple(storm_tint), tuple(c * 1.9 for c in storm_tint))
        sat = T.node("ShaderNodeHueSaturation")
        sat.inputs["Saturation"].default_value = 0.55
        T.link(col, sat.inputs["Color"])
        dcol = T.mix(1.0, sat.outputs["Color"], dark, blend="MULTIPLY")
        col = T.mix(sm, col, dcol)
    # --- warm glow around the sun (golden-hour air) ------------------------------------------------
    if glow:
        th2 = T.math("ARCCOSINE", T.math("MINIMUM", T.math("MAXIMUM", ds, -1.0), 1.0))
        gf = T.math("MULTIPLY", T.math("EXPONENT", T.math("MULTIPLY", th2, -1.0 / glow_width)), glow)
        col = T.mix(gf, col, tuple(glow_color), blend="MULTIPLY")
    # --- gradient map: recolour the sky by its own (display) luminance, keeping its tonal structure ----
    if gmap:
        bgv = float(bg.inputs[1].default_value)
        lum = T.node("ShaderNodeRGBToBW")
        T.link(col, lum.inputs[0])
        L = lum.outputs[0]
        Ld = T.math("MULTIPLY", L, bgv)
        x = T.math("DIVIDE", Ld, T.math("ADD", Ld, gk))
        rp = T.ramp(x, gmap, interp="B_SPLINE" if len(gmap) > 3 else "LINEAR")
        cg = T.mix(1.0, rp.outputs["Color"], T.comb(L, L, L), blend="MULTIPLY")
        col = T.mix(gmix, col, cg)
    T.link(col, bg.inputs[0])
    return T


def cull_scatter(names, pred):
    """Delete GN-scattered instances (env.scatter point clouds) of objects whose name starts with one of
    `names` where pred(x, y, z, size) is True (numpy arrays, world space). Returns the number removed."""
    import numpy as np
    removed = 0
    for ob in list(bpy.data.objects):
        if "n_instances" not in ob.keys() or not any(ob.name.startswith(n) for n in names):
            continue
        me = ob.data
        nv = len(me.vertices)
        if nv == 0:
            continue
        co = np.zeros(nv * 3, np.float32)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        M = np.array(ob.matrix_world)
        wc = co @ M[:3, :3].T + M[:3, 3]
        attrs = {}
        for at in me.attributes:
            if at.domain != "POINT" or at.name == "position" or at.name.startswith("."):
                continue
            if at.data_type == "FLOAT_VECTOR":
                arr = np.zeros(nv * 3, np.float32)
                at.data.foreach_get("vector", arr)
                arr = arr.reshape(-1, 3)
            elif at.data_type == "INT":
                arr = np.zeros(nv, np.int32)
                at.data.foreach_get("value", arr)
            elif at.data_type == "FLOAT":
                arr = np.zeros(nv, np.float32)
                at.data.foreach_get("value", arr)
            else:
                continue
            attrs[at.name] = (at.data_type, arr)
        size = attrs["scl"][1].max(axis=1) if "scl" in attrs else np.ones(nv, np.float32)
        keep = ~pred(wc[:, 0], wc[:, 1], wc[:, 2], size)
        k = int(keep.sum())
        if k == nv:
            continue
        removed += nv - k
        nm = bpy.data.meshes.new(me.name + "_cull")
        nm.vertices.add(k)
        nm.vertices.foreach_set("co", co[keep].ravel())
        for name, (dt, arr) in attrs.items():
            at = nm.attributes.new(name, dt, "POINT")
            if dt == "FLOAT_VECTOR":
                at.data.foreach_set("vector", arr[keep].ravel())
            else:
                at.data.foreach_set("value", arr[keep])
        nm.update()
        ob.data = nm
        ob["n_instances"] = k
        if k == 0:
            ob.hide_render = True
    return removed


def _occluded_fn(cams, edge=(-11.0, 10.2), margin_deg=2.5):
    """Predicate for cull_scatter: True where an instance is invisible from every camera key: behind
    the skull-cliff crest below the line of sight, outside the horizontal frustum, or under the frame."""
    import numpy as np

    def pred(x, y, z, size):
        hidden = np.ones(len(x), bool)
        for (loc, tgt, lens) in cams:
            cx, cy, cz = loc
            fx, fy = tgt[0] - cx, tgt[1] - cy
            yaw = math.atan2(fx, fy)
            half = math.atan(18.0 * 9.0 / 16.0 / lens) + math.radians(margin_deg)
            ang = np.arctan2(x - cx, y - cy) - yaw
            out_side = np.abs(ang) > half
            slope = (edge[1] - cz) / (edge[0] - cy)
            behind = (y > edge[0] + 0.5) & (z + 2.0 * size < cz + slope * (y - cy))
            pitch = math.atan2(tgt[2] - cz, math.hypot(fx, fy))
            low = math.atan(18.0 / lens) - pitch + math.radians(margin_deg)       # bottom ray below horizon
            d = np.hypot(x - cx, y - cy)
            under = (y < edge[0]) & ((cz - (z + 2.0 * size)) / np.maximum(d, 0.1) > math.tan(low))
            hidden &= out_side | behind | under
        return hidden
    return pred


def figures(A, lod="mid"):
    """Jesus on the centre cross, the two thieves (CROWD_MAN variants) on the side crosses."""
    from lib import characters as P
    out = []
    try:
        j = P.make_person("jesus", "JESUS_CROSS", pose=None, lod=lod, hair_strands=False)
    except Exception as e:                     # wardrobe in flux: fall back to an undressed figure
        print("s00: dressed JESUS_CROSS failed (%s) - undressed" % e)
        j = P.make_person("jesus", "JESUS_CROSS", pose=None, lod=lod, hair_strands=False, outfit=None)
    P.place_on_cross(j, A["crosses"]["center"]["root"], head="down", strain=0.55)
    P.expression(j, "anguish")
    out.append(j)
    for k, seed, side, head in (("left", 5, 1.0, "side"), ("right", 11, -1.0, "down")):
        if k not in A["crosses"]:
            continue
        kw = dict(seed=seed, pose=None, lod="far", hair_strands=False)
        try:
            t = P.make_person("thief_" + k, "CROWD_MAN", outfit=["loincloth"], **kw)
        except Exception as e:
            print("s00: dressed thief failed (%s) - undressed" % e)
            t = P.make_person("thief_" + k, "CROWD_MAN", outfit=None, **kw)
        P.place_on_cross(t, A["crosses"][k]["root"], head=head, strain=0.85, knee_side=side)
        out.append(t)
    return [simplify_person(p) for p in out]


def _simple_mat(name, color, rough=0.7, sheen=0.0):
    m = bpy.data.materials.get(name) or C.mat(name, color=color, rough=rough, sheen=sheen)
    E.hazify(m)
    return m


def simplify_person(p):
    """At ~50 px tall the figures are silhouettes: freeze each into one mesh (bake_static) and swap the
    hero shaders (SSS skin, layered eyes, blended lashes, hair curves) for plain opaque materials.
    Measured: the three live people cost ~19 s/frame at final quality, baked + simple ~1-2 s."""
    from lib import characters as P
    ob = P.bake_static(p, delete=True)
    for ch in list(ob.children):
        if ch.type != "MESH":
            bpy.data.objects.remove(ch, do_unlink=True)
    skin = _simple_mat("S00_Skin", (0.30, 0.19, 0.13), 0.55)
    hair = _simple_mat("S00_Hair", (0.025, 0.018, 0.013), 0.7)
    cloth = _simple_mat("S00_Cloth", (0.55, 0.48, 0.38), 0.9, sheen=0.3)
    thorn = _simple_mat("S00_Thorn", (0.10, 0.07, 0.045), 0.9)
    names = []
    for i, m in enumerate(ob.data.materials):
        n = (m.name if m else "").lower()
        names.append(n)
        if any(k in n for k in ("hair", "brow", "lash", "beard")):
            ob.data.materials[i] = hair
        elif any(k in n for k in ("thorn", "crown")):
            ob.data.materials[i] = thorn
        elif any(k in n for k in ("linen", "fabric", "cloth", "wool", "loin", "garment", "tunic", "hessian")):
            ob.data.materials[i] = cloth
        else:
            ob.data.materials[i] = skin
    print("s00: simplified %s materials: %s" % (ob.name, ", ".join(names)))
    return ob


def build(ctx):
    N = ctx.render_frames
    (l0, t0, lens0), (l1, t1, lens1) = CAM0, CAM1
    view0 = Vector(t0) - Vector(l0)
    info = E.hdri_info(HDRI)
    vis_el = VIS_SUN_OFF[1] if VIS_SUN_OFF[1] is not None else info["sun_el"]
    vis_az = _az(view0) - VIS_SUN_OFF[0]
    over = dict(hdri=HDRI, sun_el=LAMP[1], key=0.42, strength=0.38, clamp_sun=1.5, sat=1.25, tint=(1.0, 0.8, 0.55),
                sun_disk=dict(el=vis_el, size=0.75, color=(1.0, 0.86, 0.62), strength=60.0, glow=0.10))
    cams = [dict(loc=l0, target=t0, lens=lens0), dict(loc=l1, target=t1, lens=lens1)]
    A = E.golgotha(ctx, mood="golden", sun_az=vis_az, sky_over=over, view=cams, near_detail=0.0,
                   city=False, dust=False, skull=0.8)
    # boulders on the plateau would silhouette as blobs on the hill line next to the crosses
    k = cull_scatter(("EnvBoulders", "EnvTalus"), lambda x, y, z, s: (np.abs(x) < 16) & (y > -10.5) & (y < 14) & (z > 8.5))
    print("s00: culled %d plateau boulders" % k)
    # everything the camera cannot see (behind the crest, outside the narrow 70 mm frustum, under the frame)
    k = cull_scatter(("Env",), _occluded_fn([CAM0, CAM1]))
    print("s00: culled %d hidden scatter instances" % k)
    S = A["sky"]
    sun_vis = _dir(vis_az, vis_el)
    # lamp cheated to the back-right; haze glow stays on the visible sun
    S["sun"].rotation_euler = (-_dir(*LAMP)).to_track_quat("-Z", "Y").to_euler()
    E.set_haze(sun_dir=tuple(sun_vis), sun_mix=0.9, sun_power=4.0, density=0.0014, start=20.0)
    # faint warm bounce from the sunlit plain behind the camera: models the shadowed skull cliff
    # (light-linked to the cliff + terrain only: crosses and figures stay backlit silhouettes)
    fill = C.sun(elevation=18, azimuth=-20, energy=0.22, color=(1.0, 0.78, 0.55), angle=8)
    fill.data.use_shadow = False
    fill.name = "S00Bounce"
    recv = bpy.data.collections.new("S00BounceRecv")
    for o in (A.get("cliff"), A.get("terrain")):
        if o is not None:
            recv.objects.link(o)
    fill.light_linking.receiver_collection = recv
    sky_fx(S, sun_vis, rays=0.45, veil=0.8, ray_keys=[(1, 0.0), (N, 0.35)], storm=0.9,
           storm_keys=[(1, 0.16), (N, 0.10)], storm_tint=(0.3, 0.3, 0.32), gmap=GOLD_MAP, gmix=0.8)
    E.scene_prop("sfx_storm_time", 0.0, 1)
    E.scene_prop("sfx_storm_time", 0.25, N)
    E._linear_keys(bpy.context.scene)

    figures(A)

    cam = C.camera(loc=l0, target=t0, lens=lens0, name="Cam")

    def path(f):
        u = C.ease_in_out((f - 1) / max(1, N - 1))
        loc = Vector(l0).lerp(Vector(l1), u)
        tgt = Vector(t0).lerp(Vector(t1), u)
        return (loc, tgt, 0.0)
    C.animate_camera(cam, path, 1, N)

    ctx.samples = 4
    ctx.render_opts.update({"volumetrics": "low", "shadow_scale": 0.5})
    ctx.interp = True
    ctx.post.update({"grade": "gold", "bloom": 0.42, "vignette": 0.18,
                     "title": {"ink": "dark"}})          # verified: umber title over the bright golden sky
