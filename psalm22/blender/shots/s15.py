"""s15 - Empty tomb: "I will declare your name to my people; in the assembly I will praise you."

Resurrection morning (flash cut from the beasts turning to dust). Low in Joseph's garden at dawn: a
pale limestone cliff with a rock-cut tomb, olive trees, scrub on the ledges, dawn sky above. The
earth shakes, dust sifts from the facade and the great round stone rolls aside in its groove (0-2 s);
golden light pours through the low doorway. The camera glides in, ducks through the doorway into
the chamber and comes to rest on the grave cloths lying on the bench in a shaft of dawn light - the
tomb is empty (phrase 2).

Built on lib/sets.garden_tomb (+ env olive trees / shrubs, fx dust).
"""
import math
import random
import bpy
from mathutils import Vector
from lib import core as C
from lib import sets as S
from lib import env as E
from lib import fx as FX


def _spline(pts, t):
    """Catmull-Rom through pts (list of Vectors), t in 0..1 (uniform per segment)."""
    n = len(pts) - 1
    u = max(0.0, min(1.0, t)) * n
    i = min(n - 1, int(u))
    s = u - i
    p0 = pts[max(0, i - 1)]
    p1, p2 = pts[i], pts[i + 1]
    p3 = pts[min(n, i + 2)]
    s2, s3 = s * s, s * s * s
    return 0.5 * ((2 * p1) + (-p0 + p2) * s + (2 * p0 - 5 * p1 + 4 * p2 - p3) * s2 + (-p0 + 3 * p1 - 3 * p2 + p3) * s3)


def _grid(name, nx, ny, sx, sy, z_fn=None, coll=None):
    verts, faces = [], []
    for j in range(ny + 1):
        for i in range(nx + 1):
            x = (i / nx - 0.5) * sx
            y = (j / ny - 0.5) * sy
            verts.append((x, y, z_fn(x, y) if z_fn else 0.0))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    return C._new_mesh_obj(name, verts, faces, coll)


def _shroud(tomb, frames=56):
    """Grave cloths by cloth simulation (at build time, then frozen): a long linen sheet settles over
    a body-shaped form on the bench; the form then vanishes and the cloth collapses into soft folds.
    Linen bands are laid onto the result; the face cloth stays folded by itself at the head end."""
    sc = bpy.context.scene
    bench = tomb.objects["bench"]
    bb = [bench.matrix_world @ Vector(c) for c in bench.bound_box]
    x0, x1 = min(v.x for v in bb), max(v.x for v in bb)
    y0, y1 = min(v.y for v in bb), max(v.y for v in bb)
    top = tomb["bench"].z
    for o in list(tomb.coll.objects):
        if o.name.startswith(("grave_linen", "linen_strip")):
            o.hide_render = True
            o.hide_viewport = True
    lin_m = S.linen_material("s15_linen", color=(0.9, 0.86, 0.77))
    cx = (x0 + x1) / 2 - 0.02
    cy = (y0 + y1) / 2 + 0.12
    L, W = 2.05, 1.0
    rnd = random.Random(3)

    def z0(x, y):
        return 0.004 * math.sin(y * 9.0) + 0.003 * math.sin(x * 13.0 + y * 3.0)
    sheet = _grid("s15_shroud_sim", 26, 52, W, L, z0)
    sheet.location = (cx, cy, top + 0.22)
    sheet.rotation_euler = (0, 0, math.radians(-1.5))
    cols = []
    benchc = C.box("s15_col_bench", (x1 - x0 + 0.02, y1 - y0, 0.4), ((x0 + x1) / 2, (y0 + y1) / 2, top - 0.2))
    wall = C.box("s15_col_wall", (0.2, y1 - y0 + 1.0, 1.4), (x1 + 0.1, (y0 + y1) / 2, top + 0.5))
    hump = C.prim("uv_sphere", name="s15_col_body", loc=(cx - 0.02, cy - 0.05, top + 0.02),
                  scale=(0.2, 0.88, 0.13), segments=24, ring_count=12)
    cols = [benchc, wall, hump]
    for o in cols:
        cm = o.modifiers.new("col", "COLLISION")
        o.collision.thickness_outer = 0.006
        o.collision.cloth_friction = 8.0
        o.hide_render = True
    # the form vanishes: shrink into the bench after the cloth has settled over it
    fs = int(frames * 0.42)
    hump.keyframe_insert("scale", frame=fs)
    hump.keyframe_insert("location", frame=fs)
    hump.scale = (0.17, 0.82, 0.01)
    hump.location.z = top - 0.02
    hump.keyframe_insert("scale", frame=fs + 14)
    hump.keyframe_insert("location", frame=fs + 14)
    mod = sheet.modifiers.new("cloth", "CLOTH")
    cs = mod.settings
    cs.quality = 6
    cs.mass = 0.12
    cs.tension_stiffness = 12.0
    cs.compression_stiffness = 12.0
    cs.shear_stiffness = 4.0
    cs.bending_stiffness = 0.06
    cs.air_damping = 1.5
    cc = mod.collision_settings
    cc.collision_quality = 3
    cc.distance_min = 0.004
    cc.use_self_collision = True
    cc.self_distance_min = 0.003
    mod.point_cache.frame_start = 1
    mod.point_cache.frame_end = frames
    f_keep = sc.frame_current
    for f in range(1, frames + 1):
        sc.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(sheet.evaluated_get(dg))
    shroud = bpy.data.objects.new("s15_shroud", me)
    tomb.coll.objects.link(shroud)
    shroud.matrix_world = sheet.matrix_world.copy()
    sc.frame_set(f_keep)
    for o in [sheet] + cols:
        bpy.data.objects.remove(o, do_unlink=True)
    me.materials.clear()
    me.materials.append(lin_m)
    sol = shroud.modifiers.new("thick", "SOLIDIFY")
    sol.thickness = 0.0025
    sol.offset = 1.0
    sub = shroud.modifiers.new("sub", "SUBSURF")
    sub.levels = 0
    sub.render_levels = 1
    for p in me.polygons:
        p.use_smooth = True
    # linen bands (wrappings) lying across the collapsed sheet, conforming to it by ray casts
    bpy.context.view_layer.update()
    sinv = shroud.matrix_world.inverted()
    for k, (by, ang, ln) in enumerate(((-0.55, 8.0, 0.75), (-0.05, -12.0, 0.7), (0.45, 4.0, 0.8))):
        nx, ny = 34, 3
        verts, faces = [], []
        ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        for j in range(ny + 1):
            for i in range(nx + 1):
                lx = (i / nx - 0.5) * ln
                ly = (j / ny - 0.5) * 0.085
                x = cx + lx * ca - ly * sa + rnd.uniform(-0.002, 0.002)
                y = cy + by + lx * sa + ly * ca
                ok, hit, nor, idx = shroud.ray_cast(sinv @ Vector((x, y, top + 0.6)),
                                                    sinv.to_3x3() @ Vector((0, 0, -1)))
                z = ((shroud.matrix_world @ hit).z + 0.0045) if ok else top + 0.003
                verts.append((x, y, z))
        for j in range(ny):
            for i in range(nx):
                a = j * (nx + 1) + i
                faces.append((a, a + 1, a + nx + 2, a + nx + 1))
        st = C._new_mesh_obj("s15_band%d" % k, verts, faces, tomb.coll)
        st.data.materials.append(lin_m)
        s2 = st.modifiers.new("thick", "SOLIDIFY")
        s2.thickness = 0.002
        s2.offset = 1.0
        for p in st.data.polygons:
            p.use_smooth = True
    return shroud


def _lower_cliff(cliff, z0=2.9, k=0.62):
    """Lower the set's 5.5 m cliff to a ~4.3 m garden outcrop (sky visible above it)."""
    me = cliff.data
    for v in me.vertices:
        if v.co.z > z0:
            v.co.z = z0 + (v.co.z - z0) * k
    me.update()


def _hide_after(objs, f):
    for o in objs:
        o.hide_render = False
        o.keyframe_insert("hide_render", frame=1)
        o.hide_render = True
        o.keyframe_insert("hide_render", frame=f)
        o.hide_render = False


def build(ctx):
    n = ctx.nframes
    NR = ctx.render_frames
    fr = ctx.frame
    # ---------------- timing ----------------
    f_roll0 = 5                    # stone starts to move (just after the flash peak)
    f_roll1 = int(fr(2.2))         # stone at rest against the stop
    f_move0 = int(fr(0.3))
    f_move1 = int(fr(6.4))

    SUN_AZ, SUN_EL = -44.0, 9.0
    tomb = S.garden_tomb(ctx, stone_open=[(1, 0.0), (f_roll0, 0.0), (f_roll1, 1.0)], sun_elevation=SUN_EL,
                         sun_azimuth=SUN_AZ, dust_motes=True)
    cliff = tomb.objects["cliff"]
    _lower_cliff(cliff)
    lime = E.limestone_material("s15_limestone", scale=0.55, tint=(1.0, 0.95, 0.87), streaks=0.7, strata=0.4,
                                layers=2, res="1k")
    cliff.data.materials.clear()
    cliff.data.materials.append(lime)
    sun = tomb.lights["sun"]
    sun.data.energy = 5.0
    sun.data.angle = math.radians(0.8)
    shaft = tomb.lights["dawn_shaft"]
    # the real sun now shines through the doorway: keep the spot as a gentle booster along the same line
    lin = tomb["linen"]
    sdir = Vector((math.sin(math.radians(SUN_AZ)) * math.cos(math.radians(SUN_EL)),
                   -math.cos(math.radians(SUN_AZ)) * math.cos(math.radians(SUN_EL)),
                   math.sin(math.radians(SUN_EL))))           # towards the sun
    _shroud(tomb)

    # ---------------- vegetation: olive trees, scrub on the outcrop, spring grass ----------------
    rnd = random.Random(15)
    olive_a = E.olive_tree(seed=4, age=1.1, size=0.95, lod=1)
    olive_b = E.olive_tree(seed=7, age=0.8, size=0.8, lod=1)
    veg = [E.place(olive_a, (-4.6, -2.4, -0.05), rot=(0, 0, 40)),
           E.place(olive_b, (5.2, -3.9, -0.05), rot=(0, 0, 200))]
    bushes = [E.thorn_bush(seed=k, size=0.9 + 0.25 * k, leafy=1.0) for k in range(3)]
    E.add_ground(cliff)
    veg.append(E.scatter(bushes, terrain=cliff, count=260, region=(-9, -1, 9, 9), seed=3, scale=(0.6, 1.3),
                         align=0.4, max_slope=55, zrange=(2.0, 8.0), sink=0.05, name="s15_cliff_scrub"))
    gr_dry = E.grass_protos("dry", n=4, height=0.45)
    gr_green = E.grass_protos("green", n=4, height=0.4)
    veg.append(E.scatter(gr_dry + gr_green, terrain=cliff, count=900, region=(-9, -1, 9, 9), seed=4,
                         scale=(0.7, 1.4), align=0.6, max_slope=60, zrange=(1.5, 8.0), name="s15_cliff_grass",
                         shadows=False))
    gnd = tomb.objects["ground"]
    E.add_ground(gnd)
    veg.append(E.scatter(gr_green + gr_dry, terrain=gnd, count=1400, region=(-7, -8, 7, -0.7), seed=5,
                         scale=(0.6, 1.3), align=0.5, exclude=[(0.0, -0.6, 0.8), (1.3, -0.6, 1.4)],
                         weights=[1, 1, 1, 1, 0.6, 0.6, 0.6, 0.6], name="s15_ground_grass", shadows=False))

    # ---------------- earthquake dust ----------------
    FX.dust_burst((0.1, -0.2, 1.62), f_roll0, size=0.55, color=(0.82, 0.75, 0.66), count=26, grains=700,
                  direction=(0.0, -0.4, -1.0), wind=(0.25, -0.15, -0.1), floor=0.0, opacity=0.5, seed=4)
    FX.dust_burst((0.55, -0.45, 0.04), f_roll0 + 3, size=0.85, color=(0.8, 0.72, 0.62), count=36, grains=700,
                  wind=(0.5, -0.35, 0.05), floor=0.0, opacity=0.6, seed=5)
    FX.dust_burst((2.25 + 0.95, -0.4, 0.06), f_roll1 - 2, size=0.6, color=(0.8, 0.72, 0.62), count=26,
                  grains=400, wind=(0.4, -0.3, 0.05), floor=0.0, opacity=0.55, seed=6)

    # ---------------- camera ----------------
    bz = tomb["bench"].z
    L = [Vector(v) for v in ((-2.9, -5.2, 0.5), (-1.7, -3.1, 0.66), (-0.3, -1.25, 0.8), (0.0, 0.05, 0.8),
                              (0.18, 0.85, 0.7), (0.4, 1.4, 0.6))]
    T = [Vector(v) for v in ((0.15, 0.0, 1.5), (0.15, 0.2, 1.05), (0.15, 1.4, 0.75), (0.55, 2.3, 0.5),
                              (1.05, 2.25, bz + 0.05), (1.22, 2.3, bz + 0.02))]

    def path(f):
        u = (f - f_move0) / float(f_move1 - f_move0)
        u = C.smootherstep(max(0.0, min(1.0, u)))
        loc = _spline(L, u)
        tgt = _spline(T, u)
        # earthquake: strong at the cut, decays over ~1.8 s
        q = max(0.0, 1.0 - (f - 1) / fr(1.8)) ** 2
        loc = loc + C.shake(f, amp=0.03 * q, freq=9.0, seed=2) + C.shake(f, amp=0.006, freq=0.5, seed=7)
        return loc, tgt

    cam = C.camera(loc=L[0], target=T[0], lens=24, fstop=4.0, focus=5.0, name="s15_cam")
    C.animate_camera(cam, path)
    f_door = None
    for f in range(1, NR + 1, 2):
        loc, tgt = path(f)
        cam.data.dof.focus_distance = max(0.4, (tgt - loc).length)
        cam.data.dof.keyframe_insert("focus_distance", frame=f)
        if f_door is None and loc.y > 0.2:
            f_door = f
    f_door = f_door or NR
    # aperture opens up for the close interior (shallow DOF on the cloths)
    cam.data.dof.aperture_fstop = 5.6
    cam.data.dof.keyframe_insert("aperture_fstop", frame=f_door)
    cam.data.dof.aperture_fstop = 2.8
    cam.data.dof.keyframe_insert("aperture_fstop", frame=min(NR, f_door + 30))

    # ---------------- interior light ----------------
    # once inside, the exterior is behind the camera: drop the (shadowed, noisy) sky fill + exterior plants
    skf = tomb.lights["sky_fill"]
    e0 = skf.data.energy
    skf.data.keyframe_insert("energy", frame=max(1, f_door - 6))
    skf.data.energy = e0 * 0.12
    skf.data.keyframe_insert("energy", frame=f_door + 8)
    _hide_after(veg, f_door + 8)
    # warm bounce off the sunlit grave cloths / floor (no GI in EEVEE): soft, shadowless
    bnc = C.light("AREA", loc=(lin.x - 0.25, lin.y - 0.6, bz + 0.05), energy=0.0, temp=3200,
                  target=(lin.x - 1.5, lin.y - 0.2, bz + 1.0), size=1.4, name="s15_cloth_bounce", shadow=False)
    bnc.data.volume_factor = 0.0
    bnc.data.keyframe_insert("energy", frame=f_roll0 + 10)
    bnc.data.energy = 30.0
    bnc.data.keyframe_insert("energy", frame=f_roll1 + 20)

    ctx.samples = 5
    ctx.render_opts = {"volumetrics": "low"}
    ctx.post = {"grade": "dawn", "bloom": 0.3, "caption": {"y": 0.72, "halo": 1.2}}
