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
from mathutils import Vector, noise
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


def _linen_mat(name="s15_linen", color=(0.80, 0.75, 0.64)):
    """Matte aged linen: ivory, rough, sheen, a little translucency, fine slub/crease bump (no regular
    weave pattern: it moires at this distance)."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, Lk = nt.nodes, nt.links
    b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0, 6.0, 1.0)       # slubs stretched along the threads
    Lk.new(tc.outputs["Object"], mp.inputs["Vector"])
    nf = N.new("ShaderNodeTexNoise")
    nf.inputs["Scale"].default_value = 160.0
    nf.inputs["Detail"].default_value = 3.0
    Lk.new(mp.outputs[0], nf.inputs["Vector"])
    nz = N.new("ShaderNodeTexNoise")                     # uneven yarn tone + faint old stains
    nz.inputs["Scale"].default_value = 9.0
    nz.inputs["Detail"].default_value = 5.0
    Lk.new(tc.outputs["Object"], nz.inputs["Vector"])
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.12
    bump.inputs["Distance"].default_value = 0.0005
    Lk.new(nf.outputs["Fac"], bump.inputs["Height"])
    Lk.new(bump.outputs["Normal"], b.inputs["Normal"])
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.3
    ramp.color_ramp.elements[0].color = (color[0] * 0.88, color[1] * 0.86, color[2] * 0.8, 1)
    ramp.color_ramp.elements[1].position = 0.72
    ramp.color_ramp.elements[1].color = (*color, 1)
    Lk.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    Lk.new(ramp.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.92
    b.inputs["Specular IOR Level"].default_value = 0.2
    b.inputs["Sheen Weight"].default_value = 0.6
    b.inputs["Sheen Roughness"].default_value = 0.45
    b.inputs["Sheen Tint"].default_value = (1.0, 0.95, 0.85, 1)
    b.inputs["Subsurface Weight"].default_value = 0.1
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.9, 0.7)
    b.inputs["Subsurface Scale"].default_value = 0.004
    return m


def _folded_sheet(name, W, L, nx, ny, r=0.012, bottom=0.56, seed=0, ripple=0.012, droop=0.0):
    """Linen sheet of width W (across X) and length L (along Y), folded once lengthwise: bottom layer, a
    soft round fold of radius r on +X, a shorter top layer coming back (free edge short of the bottom
    one). Soft cloth undulations are modelled directly (ripples running across the sheet with
    varying wavelength/amplitude, a wavy free edge, slight lift of the top layer over the fold)."""
    so = Vector((seed * 1.7, 0.3, 2.2))
    Lb = bottom * W
    Lt = W - Lb - math.pi * r
    b_ = Lb / 2.0
    verts, faces = [], []
    for j in range(ny + 1):
        t = (j / ny - 0.5) * L
        # ripple field along the length: two wave trains + noise (soft folds of linen at rest)
        ph = 2.0 * noise.noise(Vector((t * 1.1, 0.0, 3.0)) + so)
        rip = (math.sin(t * 2 * math.pi / 0.23 + ph) * 0.6 + math.sin(t * 2 * math.pi / 0.41 + 1.7 * ph) * 0.4)
        amp_t = ripple * (0.55 + 0.45 * noise.noise(Vector((t * 2.3, 1.0, 0.5)) + so))
        for i in range(nx + 1):
            s_ = i / nx * W
            u = s_ / W
            if s_ <= Lb:
                x, z = -Lb / 2 + s_, 0.0
                lay = 0.35 + 0.65 * (s_ / Lb)          # bottom layer: flatter towards its open edge
            elif s_ <= Lb + math.pi * r:
                th = -math.pi / 2 + (s_ - Lb) / r
                x, z = b_ + r * math.cos(th), r + r * math.sin(th)
                lay = 1.0
            else:
                q = (s_ - Lb - math.pi * r) / max(1e-6, Lt)
                x, z = b_ - (s_ - Lb - math.pi * r), 2 * r
                lay = 1.0 - 0.3 * q
                x += 0.025 * noise.noise(Vector((t * 4.0, 0.0, 7.0)) + so) * q      # wavy free edge
            ripple_z = max(-0.6 * r, rip * amp_t * lay * (1.0 if z > 0.5 * r else 0.45))
            z += ripple_z + 0.003 * noise.noise(Vector((t * 9.0, s_ * 7.0, 1.0)) + so)
            if z > 1.5 * r:                            # the top layer rests on ridges of the bottom one
                z = max(z, 2 * r + 0.004 * noise.noise(Vector((t * 6.0, s_ * 6.0, 4.0)) + so))
            if droop and (j == 0 or j == ny):
                z -= droop
            verts.append((x, t + 0.012 * noise.noise(Vector((s_ * 3.0, t, 2.0)) + so) * (1 - abs(2 * u - 1)), z))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    return C._new_mesh_obj(name, verts, faces)


def _shroud(tomb):
    """Grave cloths: the long linen shroud lies folded once lengthwise along the bench in soft folds;
    the face cloth lies folded by itself at the head end (John 20:7). Procedural (no simulation)."""
    bench = tomb.objects["bench"]
    bb = [bench.matrix_world @ Vector(c) for c in bench.bound_box]
    x0, x1 = min(v.x for v in bb), max(v.x for v in bb)
    y0, y1 = min(v.y for v in bb), max(v.y for v in bb)
    top = tomb["bench"].z
    for o in list(tomb.coll.objects):
        if o.name.startswith(("grave_linen", "linen_strip", "napkin")):
            o.hide_render = True
            o.hide_viewport = True
    lin_m = _linen_mat()
    cx = (x0 + x1) / 2 - 0.04
    objs = []
    sheet = _folded_sheet("s15_shroud", 1.02, 1.8, 56, 150, r=0.016, bottom=0.57, seed=1, ripple=0.011)
    sheet.location = (cx, y0 + 1.06, top + 0.004)
    sheet.rotation_euler = (0, 0, math.radians(1.5))
    objs.append(sheet)
    nap = _folded_sheet("s15_facecloth", 0.46, 0.3, 24, 20, r=0.01, bottom=0.53, seed=2, ripple=0.004)
    nap.location = (cx + 0.06, y1 - 0.36, top + 0.004)
    nap.rotation_euler = (0, 0, math.radians(-76))
    nap.scale = (1.0, 1.0, 1.35)
    objs.append(nap)
    for i, o in enumerate(objs):
        tomb.coll.objects.link(o)
        bpy.context.scene.collection.objects.unlink(o)
        o.data.materials.append(lin_m)
        sol = o.modifiers.new("thick", "SOLIDIFY")
        sol.thickness = 0.0025
        sol.offset = 0.0
        sub = o.modifiers.new("sub", "SUBSURF")
        sub.levels = 0
        sub.render_levels = 1
        for p in o.data.polygons:
            p.use_smooth = True
    return sheet


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
    f_move1 = int(fr(6.9))

    SUN_AZ, SUN_EL = -44.0, 9.0
    tomb = S.garden_tomb(ctx, stone_open=[(1, 0.0), (f_roll0, 0.0), (f_roll1, 1.0)], sun_elevation=SUN_EL,
                         sun_azimuth=SUN_AZ, dust_motes=True)
    cliff = tomb.objects["cliff"]
    _lower_cliff(cliff)
    # pale Jerusalem limestone: desaturate the set's warm rock materials (the dawn light adds the warmth)
    for mn, sat, val in (("set_tomb_face", 0.38, 1.16), ("set_tomb_cut", 0.14, 1.55), ("set_tomb_rock", 0.38, 1.15),
                         ("set_tomb_stone", 0.35, 1.15), ("set_tomb_ground", 0.45, 1.05)):
        for m in bpy.data.materials:
            if not m.name.startswith(mn) or not m.use_nodes:
                continue
            for nd in m.node_tree.nodes:
                if nd.bl_idname == "ShaderNodeHueSaturation":
                    nd.inputs["Saturation"].default_value = sat
                    nd.inputs["Value"].default_value = val
    sun = tomb.lights["sun"]
    sun.data.energy = 5.0
    sun.data.color = C.kelvin(4100)
    sun.data.angle = math.radians(0.8)
    cf = tomb.lights["chamber_fill"]
    cf.data.color = C.kelvin(5600)
    cf.data["base_e"] = cf.data.get("base_e", 12.0) * 0.75
    if cf.data.animation_data and cf.data.animation_data.action:
        for fc in C._fcurves(cf.data.animation_data.action):
            for kp in fc.keyframe_points:
                kp.co[1] *= 0.75
                kp.handle_left[1] *= 0.75
                kp.handle_right[1] *= 0.75
    # denser dust in the chamber -> visible sun shaft through the doorway; finer motes
    for o in tomb.coll.objects:
        if o.name.startswith("tomb_dust") and not o.name.startswith("tomb_dust_motes"):
            o.hide_render = True          # replaced by a uniform chamber haze below (the noisy one hid the shaft)
        if o.name.startswith("tomb_dust_motes"):
            for nd in o.modifiers[0].node_group.nodes:
                if nd.bl_idname == "GeometryNodeMeshIcoSphere":
                    nd.inputs["Radius"].default_value = 0.0013
            mm = bpy.data.materials.get("tomb_dust_motes_mat")
            if mm:
                C.bsdf(mm).inputs["Base Color"].default_value = (0.45, 0.42, 0.38, 1)
    shaft = tomb.lights["dawn_shaft"]
    # the real sun now shines through the doorway: keep the spot as a gentle booster along the same line
    lin = tomb["linen"]
    sdir = Vector((math.sin(math.radians(SUN_AZ)) * math.cos(math.radians(SUN_EL)),
                   -math.cos(math.radians(SUN_AZ)) * math.cos(math.radians(SUN_EL)),
                   math.sin(math.radians(SUN_EL))))           # towards the sun
    _shroud(tomb)
    ch = tomb["chamber"]
    haze = C.fog_box(center=(ch.x + 0.25, ch.y - 0.15, 0.75), size=(3.3, 3.25, 2.2), density=0.2,
                     color=(0.95, 0.9, 0.84), anisotropy=-0.15, name="s15_chamber_haze", coll=tomb.coll)
    haze.visible_shadow = False
    # the exterior air box costs ~7 CPU-s/frame for no visible gain at 5-10 m: drop it; the chamber haze is
    # only needed once the doorway is close
    for o in tomb.coll.objects:
        if o.name.startswith("tomb_haze"):
            o.hide_render = True
    haze.hide_render = True
    haze.keyframe_insert("hide_render", frame=1)
    haze.hide_render = False
    haze.keyframe_insert("hide_render", frame=int(ctx.frame(2.6)))
    # re-aim the set's booster spot along the real sun ray through the doorway
    door_c = tomb["door_center"] + Vector((0, 0.1, -0.1))
    shaft.location = door_c + sdir * 2.2
    C.look_at(shaft, door_c - sdir)
    shaft.data.spot_size = math.radians(24)
    shaft.data.volume_factor = 3.0

    # ---------------- vegetation: olive trees, scrub on the outcrop, spring grass ----------------
    rnd = random.Random(15)
    olive_a = E.olive_tree(seed=4, age=1.1, size=0.95, lod=0)
    olive_b = E.olive_tree(seed=7, age=0.8, size=0.8, lod=1)
    veg = [E.place(olive_a, (-4.6, -2.4, -0.05), rot=(0, 0, 40)),
           E.place(olive_b, (5.2, -3.9, -0.05), rot=(0, 0, 200))]
    bushes = [E.thorn_bush(seed=k, size=0.9 + 0.25 * k, leafy=1.0) for k in range(3)]
    E.add_ground(cliff)
    veg.append(E.scatter(bushes, terrain=cliff, count=260, region=(-9, -1, 9, 9), seed=3, scale=(0.6, 1.3),
                         align=0.4, max_slope=55, zrange=(2.0, 8.0), sink=0.05, name="s15_cliff_scrub"))
    gr_dry = E.grass_protos("dry", n=4, height=0.3)
    gr_green = E.grass_protos("green", n=4, height=0.28)
    veg.append(E.scatter(gr_dry + gr_green, terrain=cliff, count=900, region=(-9, -1, 9, 9), seed=4,
                         scale=(0.7, 1.4), align=0.6, max_slope=60, zrange=(1.5, 8.0), name="s15_cliff_grass",
                         shadows=False))
    gnd = tomb.objects["ground"]
    E.add_ground(gnd)
    veg.append(E.scatter(gr_green + gr_dry, terrain=gnd, count=1000, region=(-7, -8, 7, -0.7), seed=5,
                         scale=(0.6, 1.3), align=0.5, exclude=[(0.0, -0.6, 0.8), (1.3, -0.6, 1.4)],
                         weights=[1, 1, 1, 1, 0.6, 0.6, 0.6, 0.6], name="s15_ground_grass", shadows=False))

    # ---------------- earthquake dust ----------------
    FX.dust_burst((0.55, -0.45, 0.04), f_roll0 + 3, size=0.85, color=(0.8, 0.72, 0.62), count=18, grains=160,
                  wind=(0.5, -0.35, 0.05), floor=0.0, opacity=0.6, seed=5)
    FX.dust_burst((2.25 + 0.95, -0.4, 0.06), f_roll1 - 2, size=0.6, color=(0.8, 0.72, 0.62), count=12,
                  grains=100, wind=(0.4, -0.3, 0.05), floor=0.0, opacity=0.55, seed=6)

    # ---------------- camera ----------------
    bz = tomb["bench"].z
    L = [Vector(v) for v in ((-2.9, -5.2, 0.5), (-1.7, -3.1, 0.66), (-0.35, -1.3, 0.82), (0.0, 0.0, 0.92),
                              (-0.12, 0.62, 1.08), (-0.26, 1.08, 1.24), (-0.3, 1.2, 1.3))]
    T = [Vector(v) for v in ((0.15, 0.0, 1.5), (0.15, 0.2, 1.05), (0.12, 1.4, 0.85), (0.5, 2.5, 0.6),
                              (0.9, 2.55, 0.5), (1.18, 2.3, bz + 0.04), (1.2, 2.28, bz + 0.02))]
    # arc-length parameterisation of the spline so the speed follows `prof` only
    NS = 400
    us = [i / NS for i in range(NS + 1)]
    pts = [_spline(L, u) for u in us]
    acc = [0.0]
    for i in range(NS):
        acc.append(acc[-1] + (pts[i + 1] - pts[i]).length)
    tot = acc[-1]

    def u_at(sn):
        d = sn * tot
        lo, hi = 0, NS
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if acc[mid] < d:
                lo = mid
            else:
                hi = mid
        t = (d - acc[lo]) / max(1e-9, acc[hi] - acc[lo])
        return us[lo] + (us[hi] - us[lo]) * t

    def prof(t):
        # already gliding at the cut, steady, then a long gentle settle inside the chamber
        return 1.0 - (1.0 - t) ** 1.8 if t < 1 else 1.0

    def path(f):
        t = max(0.0, min(1.0, (f - 1) / float(f_move1 - 1)))
        u = u_at(prof(t))
        loc = _spline(L, u)
        tgt = _spline(T, u)
        # earthquake: strong at the cut, decays over ~1.8 s
        q = max(0.0, 1.0 - (f - 1) / fr(1.8)) ** 2
        loc = loc + C.shake(f, amp=0.03 * q, freq=9.0, seed=2) + C.shake(f, amp=0.004, freq=0.5, seed=7)
        lz = 24.0 + 6.0 * C.smoothstep(max(0.0, min(1.0, (t - 0.62) / 0.38)))     # 24 -> 30 mm inside
        return loc, tgt, 0.0, lz

    cam = C.camera(loc=L[0], target=T[0], lens=24, name="s15_cam")      # no DOF: wide lens, ~4 CPU-s/frame saved
    C.animate_camera(cam, path)
    f_door = None
    for f in range(1, NR + 1):
        loc = path(f)[0]
        if f_door is None and loc.y > 0.2:
            f_door = f
    f_door = f_door or NR
    # aperture opens up for the close interior (shallow DOF on the cloths)

    # ---------------- interior light ----------------
    # once inside, the exterior is behind the camera: drop the (shadowed, noisy) sky fill + exterior plants
    skf = tomb.lights["sky_fill"]
    e0 = skf.data.energy
    skf.data.keyframe_insert("energy", frame=max(1, f_door - 6))
    skf.data.energy = e0 * 0.12
    skf.data.keyframe_insert("energy", frame=f_door + 8)
    _hide_after(veg, f_door + 8)
    # warm bounce off the sunlit grave cloths / floor (no GI in EEVEE): soft, shadowless
    bnc = C.light("AREA", loc=(lin.x - 0.25, lin.y - 0.6, bz + 0.05), energy=0.0, temp=3900,
                  target=(lin.x - 1.5, lin.y - 0.2, bz + 1.0), size=1.4, name="s15_cloth_bounce", shadow=False)
    bnc.data.volume_factor = 0.0
    bnc.data.keyframe_insert("energy", frame=f_roll0 + 10)
    bnc.data.energy = 12.0
    bnc.data.keyframe_insert("energy", frame=f_roll1 + 20)

    ee = bpy.context.scene.eevee
    ee.use_volume_custom_range = True          # froxel slices where the shaft is (default 100 m wastes them)
    ee.volumetric_start = 0.1
    ee.volumetric_end = 16.0
    ee.volumetric_sample_distribution = 0.85
    ctx.samples = 4
    ctx.interp = True
    ctx.render_opts = {"volumetrics": "low", "shadow_scale": 0.5}
    ctx.post = {"grade": "dawn", "bloom": 0.3, "caption": {"y": 0.72, "halo": 1.2}}
