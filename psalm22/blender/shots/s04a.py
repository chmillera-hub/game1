"""s04a - Red Sea crossing (WIP v1: environment look)."""
import math
import os
import bpy
from mathutils import Vector
from lib import core as C
from lib import fx as FX
from lib import env as E

EV = os.environ.get


def wall_material(name="S04_wall", glow=1.3, foam=1.0, spec=0.35):
    """Water-wall shader (replaces fx's): deep blue-green body, emerald light entering through the crest
    with slow swirling internal masses, churning bump (two scales), foam at crest / foot / top and
    streaks running down the face. Reads the fx GN attributes fx_k (0 foot .. 1 crest), fx_top, fx_c."""
    m, nb, out = FX._new_mat(name)
    T = FX._time_value(nb)
    pos = nb.n("ShaderNodeTexCoord").outputs["Object"]
    k = nb.out(nb.sattr("fx_k"), "Fac")
    top = nb.out(nb.sattr("fx_top"), "Fac")
    c = nb.out(nb.sattr("fx_c"), "Fac")
    kk = nb.m("MINIMUM", k, 1.0)
    face = nb.sub(1.0, top)
    # internal masses (light / dark swirls), drifting up slowly
    qs = nb.v("ADD", nb.v("MULTIPLY", pos, (0.010, 0.0045, 0.022)), nb.xyz(0.0, nb.mul(T, 0.004), nb.mul(T, -0.03)))
    sw = nb.out(nb.noise(qs, scale=1.0, detail=2.0, rough=0.55, distortion=0.7, w=nb.mul(T, 0.05)), "Fac")
    sw = nb.smooth(sw, 0.3, 0.72)
    # chop: big + small
    q1 = nb.v("ADD", nb.v("MULTIPLY", pos, (0.16, 0.05, 0.13)), nb.xyz(0.0, 0.0, nb.mul(T, -0.45)))
    h1 = nb.out(nb.noise(q1, scale=1.0, detail=3.0, rough=0.55, w=nb.mul(T, 0.25)), "Fac")
    q2 = nb.v("ADD", nb.v("MULTIPLY", pos, (0.9, 0.3, 0.7)), nb.xyz(0.0, 0.0, nb.mul(T, -1.4)))
    h2 = nb.out(nb.noise(q2, scale=1.0, detail=2.0, rough=0.5), "Fac")
    hgt = nb.madd(h2, 0.3, h1)
    # foam
    fq = nb.v("ADD", nb.v("MULTIPLY", pos, (0.5, 0.16, 0.07)), nb.xyz(0.0, 0.0, nb.mul(T, 0.9)))
    streak = nb.out(nb.noise(fq, scale=1.0, detail=3.0, rough=0.6, distortion=0.6), "Fac")
    bq = nb.v("ADD", nb.v("MULTIPLY", pos, (0.6, 0.2, 0.5)), nb.xyz(0.0, nb.mul(T, 0.05), nb.mul(T, -0.3)))
    blot = nb.out(nb.noise(bq, scale=1.0, detail=4.0, rough=0.6), "Fac")
    crest_f = nb.mul(nb.smooth(kk, 0.9, 0.985), nb.smooth(blot, 0.3, 0.5))
    crest_f = nb.mul(crest_f, nb.sub(1.0, nb.smooth(top, 0.5, 1.0)))
    foot_f = nb.mul(nb.sub(1.0, nb.smooth(kk, 0.0, 0.05)), nb.smooth(blot, 0.38, 0.55))
    st_f = nb.mul(nb.smooth(streak, 0.62, 0.7), nb.smooth(blot, 0.45, 0.6))
    st_f = nb.mul(st_f, nb.mul(face, nb.madd(nb.smooth(kk, 0.35, 0.95), 0.75, 0.05)))
    top_f = nb.mul(top, nb.smooth(blot, 0.55, 0.7))
    churn = nb.mul(nb.smooth(c, 0.1, 0.7), nb.smooth(blot, 0.3, 0.5))
    churn = nb.mul(churn, nb.add(nb.smooth(kk, 0.7, 0.95), nb.mul(nb.smooth(c, 0.6, 0.95), 0.8)))
    fm = nb.m("MINIMUM", nb.mul(nb.add(nb.add(nb.add(crest_f, foot_f), nb.add(st_f, top_f)), churn), foam), 1.0)
    # colour
    deep = (0.003, 0.018, 0.024)
    body = (0.007, 0.058, 0.064)
    d = nb.mul(nb.m("POWER", kk, 1.6), nb.madd(sw, 0.9, 0.4))
    base = nb.mixc(nb.m("MINIMUM", d, 1.0), deep, body)
    base = nb.mixc(fm, base, (0.62, 0.70, 0.70))
    # emerald light through the water: strongest near the crest, swirling
    g = nb.madd(nb.m("POWER", kk, 3.0), 1.4, 0.03)
    g = nb.mul(g, nb.madd(sw, 1.4, 0.25))
    g = nb.mul(nb.mul(g, face), nb.sub(1.0, nb.mul(fm, 0.7)))
    teal = (0.035, 0.42, 0.33)
    ecol = nb.v("SCALE", teal, scale=nb.mul(g, glow))
    rough = nb.mixf(fm, nb.madd(h2, 0.12, 0.06), 0.55)
    sp = nb.mixf(fm, nb.mul(spec, nb.madd(nb.smooth(kk, 0.08, 0.55), 0.65, 0.35)), 0.4)
    b = nb.n("ShaderNodeBsdfPrincipled", {"Base Color": base, "Roughness": rough, "IOR": 1.33,
                                          "Specular IOR Level": sp, "Emission Color": ecol, "Emission Strength": 1.0})
    bump = nb.n("ShaderNodeBump", {"Height": hgt, "Distance": 0.9, "Strength": float(EV("BUMP", "0.55"))})
    nb.links.new(nb.out(bump), b.inputs["Normal"])
    nb.links.new(nb.out(b), out.inputs["Surface"])
    return m


def spray_opacity(value=0.45, name="FX_spray"):
    """The fx spray puffs are faint (opacity 0.25): raise it (the material is shared by all puffs)."""
    m = bpy.data.materials.get(name)
    if not m:
        return
    for nd in m.node_tree.nodes:
        if nd.type == "MATH" and nd.operation == "MULTIPLY" and abs(nd.inputs[1].default_value - 0.25) < 1e-4:
            nd.inputs[1].default_value = value


def glow_spray(sea, opacity=0.42, glow=1.1, color=(0.9, 0.92, 0.94), size=1.0):
    """Brighter, self-lit spray puffs (fx's are lit only by the sun from behind and read as dark smoke
    against the bright dawn sky). Also used for the collapse burst."""
    sm = FX._spray_material("S04_spray", color=color, opacity=opacity, glow=glow)
    cm = FX._spray_material("S04_crash", color=color, opacity=min(0.85, opacity * 1.7), glow=glow * 0.9)
    for key, m in (("spray", sm), ("crash", cm)):
        o = getattr(sea, key, None)
        if o is None:
            continue
        if size != 1.0 and key == "spray" and "size" in o.data.attributes:
            at = o.data.attributes["size"]
            v = np.zeros(len(at.data), np.float32)
            at.data.foreach_get("value", v)
            at.data.foreach_set("value", v * size)
        for md in o.modifiers:
            if md.type == "NODES":
                try:
                    FX._mod_set(md, Material=m)
                except KeyError:
                    pass


def hazify_sea(sea):
    """Aerial perspective for the fx Red Sea surfaces via the env haze group (cheap, no volume)."""
    objs = [sea.seabed] + list(sea.walls) + list(getattr(sea, "sea", []) or [])
    done = set()
    for o in objs:
        for m in o.data.materials:
            if m and m.name not in done:
                done.add(m.name)
                E.hazify(m)


def build(ctx):
    W, H = 34.0, 52.0
    mist = EV("MIST", "0") == "1"
    sea = FX.red_sea(ctx, width=W, height=H, lighting=False, spray=True, spray_rate=float(EV("SPRAY", "0.35")),
                     seabed=EV("SEABED", "coast_sand_rocks_02"), seed=4, wall_shadows=EV("WSH", "0") == "1",
                     mist=mist, haze=0.0006 if mist else 0.0)
    if EV("WALL", "1") == "1":
        wm = wall_material(glow=float(EV("GLOW", "1.3")), spec=float(EV("SPEC", "0.35")))
        for w in sea.walls:
            w.data.materials.clear()
            w.data.materials.append(wm)
            for md in w.modifiers:
                if md.type == "NODES":
                    FX._mod_set(md, Material=wm)
    sky = E.sky("sunrise", sun_az=180, hdri=EV("HDRI", "kloppenheim_06_puresky"), ctx=ctx,
                sun_el=float(EV("SUNEL", "7.6")),
                sun_disk=dict(el=float(EV("SUNEL", "7.6")), size=1.2, color=(1.0, 0.72, 0.42), strength=80.0, glow=0.15))
    glow_spray(sea, opacity=float(EV("SPRAYOP", "0.6")), glow=float(EV("SPRAYGLOW", "0.45")),
               color=(0.8, 0.85, 0.9), size=float(EV("SPRAYSIZE", "1.7")))
    if EV("HAZIFY", "1") == "1":
        hazify_sea(sea)
        E.set_haze(density=float(EV("HAZE", "0.0013")), color=(1.1, 1.0, 0.92))
    if sky.get("sun") is not None and EV("SHRES"):
        sky["sun"].data.shadow_maximum_resolution = float(EV("SHRES"))
    if EV("MTN", "1") == "1":
        far_mountains(sea.corridor["y"][1], toward=1.0)
    y0 = -120.0
    z0 = sea.floor_at(0, y0)
    lens = float(EV("LENS", "22"))
    cam = C.camera((0, y0, z0 + 1.5), (0, y0 + 100, z0 + 14), lens=lens)
    vcam = 0.85

    p2a = ctx.phrases[1]["start"] if len(ctx.phrases) > 1 else 3.7
    rise = float(EV("RISE", "1.4"))

    def campath(f):
        t = (f - 1) / ctx.fps
        y = y0 + vcam * t
        sh = C.shake(f, amp=0.02, freq=0.35, seed=3)
        up = rise * C.smoothstep((t - (p2a - 0.6)) / 3.2)          # "...you delivered them": gentle crane up
        loc = Vector((0.0 + sh[0], y, sea.floor_at(0, y) + 1.45 + up + 0.03 * math.sin(t * 2.4) + sh[2] * 0.5))
        tgt = Vector((0.0, y + 100.0, z0 + 13.0 + up * 0.4))
        return loc, tgt
    C.animate_camera(cam, campath, 1, ctx.render_frames)

    if EV("CROWD", "1") == "1":
        rnd = random.Random(11)
        near = [(-1.5, 5.5, 0), (1.3, 7.0, 1), (0.55, 6.6, 3), (2.9, 10.0, 2), (-3.4, 11.5, 5), (-0.6, 13.5, 4),
                (4.4, 15.0, 0), (-5.6, 17.0, 1), (1.8, 18.5, 5), (-2.2, 20.0, 2)]
        mid, far = [], []
        y = 22.0
        while y < 560.0:
            dens = 0.7 + 1.0 * min(1.0, (y - 22.0) / 120.0) - 0.9 * min(1.0, max(0.0, (y - 300.0) / 120.0))
            for _ in range(int(dens * float(EV("DENS", "0.85")) + rnd.random())):
                x = max(-11.0, min(11.0, rnd.gauss(0.0, 5.0)))
                (mid if y < 90.0 else far).append((x, y + rnd.uniform(-0.5, 0.5), rnd.randrange(len(VARIANTS))))
            y += 1.0
        cf, sf = walker_protos("far", 0.5, "WKF")
        cl = walker_lowres(cf, 0.3, "WKL")
        cu = walker_lowres(cf, 0.08, "WKU")
        for c_ in (cf, cl, cu):
            tint_instances(c_)
            hazify_protos(c_)
        mk = lambda pts, j: [dict(x=x, y=y0 + dy, var=v, dir=math.radians(rnd.uniform(-j, j)),
                                  scl=rnd.uniform(0.95, 1.05)) for x, dy, v in pts]
        nearp = near + [q for q in mid if q[1] < 26.0]
        midp = [q for q in mid if q[1] >= 26.0]
        walker_field("WalkersNear", cf, sf, mk(nearp, 3), sea.seabed)
        walker_field("WalkersMid", cl, sf, mk(midp, 3), sea.seabed)
        if EV("FAR", "1") == "1":
            walker_field("WalkersFar", cu, sf, mk(far, 4), sea.seabed)
        print("[s04a] walkers near %d mid %d far %d" % (len(nearp), len(midp), len(far)))
        for o in list(cl.objects) + list(cu.objects):   # mid / far people: no shadow casting
            o.visible_shadow = False
        if EV("WKSHADOW", "0") != "1":                # walker shadows: ~2x render cost, invisible in this backlight
            for o in cf.objects:
                o.visible_shadow = False

    ctx.samples = int(EV("SAMPLES", "4"))
    ctx.render_opts = {"volumetrics": "low", "raytracing": EV("RT", "1") == "1"}
    ctx.interp = EV("INTERP", "1") == "1"
    ctx.post = {"grade": ["dawn", "flashback"], "saturation": 0.95, "bloom": 0.36, "vignette": 0.22,
                "caption": {"halo": 1.2}}


# =============================================================================================
# Walkers: flipbook crowd. Each variant is a dressed person baked at WALK_K phases of the walk
# cycle; one Geometry-Nodes point cloud instances the right phase per point and frame, moves the
# points along their velocity and drops them onto the seabed (raycast). Cheap at render time (no
# armature evaluation), any frame renders in isolation (no bake). Bakes are cached in a .blend.
# =============================================================================================
import random
import hashlib
import numpy as np

WALK_K = 22                     # baked phases per cycle: one walk cycle = WALK_K frames at 24 fps
CACHE_VERSION = 8
CACHE_DIR = os.path.join(C.WORK, "cache", "s04")
VARIANTS = [   # (name, preset, spec)
    ("man_staff", "CROWD_MAN", dict(seed=21, staff=True)),
    ("woman_head", "CROWD_WOMAN", dict(seed=22, bundle="jar")),
    ("man_back", "CROWD_MAN", dict(seed=23, bundle="back")),
    ("child", "CHILD", dict(seed=24)),
    ("woman", "CROWD_WOMAN", dict(seed=25)),
    ("elder_staff", "CROWD_MAN", dict(seed=26, staff=True, age_years=64)),
]


def _head_jar(person, seed=0):
    """Clay pitcher carried on the head (bone-parented to 'head')."""
    from lib import assets as A
    from mathutils import Matrix
    root = A.load("water_jar", variant=1, scale=0.85)
    person.update()
    top = max(person.lm.get("head_top", person.height), person.height * 0.97)
    hp = person.head_pos()
    root.parent = person.rig
    root.parent_type = "BONE"
    root.parent_bone = "head"
    person.update()
    root.matrix_world = Matrix.Translation((hp.x, hp.y + 0.01, top - 0.015)) @ Matrix.Rotation(math.radians(10), 4, "Z")
    for o in [root] + list(root.children_recursive):
        for c in o.users_collection:
            c.objects.unlink(o)
        for c in person.rig.users_collection:
            c.objects.link(o)
    person.props.append(root)
    return root


def _bundle(person, kind, seed=0):
    """Cloth bundle (sack) bone-parented to the head ('head') or the upper back ('back')."""
    if kind == "jar":
        return _head_jar(person, seed)
    import bmesh
    from lib import wardrobe as W
    rnd = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=14, v_segments=9, radius=1.0)
    if kind == "head":
        sx, sy, sz = 0.19, 0.16, 0.12
    else:
        sx, sy, sz = 0.21, 0.15, 0.27
    for v in bm.verts:
        x, y, z = v.co
        z = max(z, -0.55) if kind == "head" else z
        n = 1.0 + 0.10 * math.sin(3.1 * x + 2.3 * y + rnd.uniform(0, 6)) + 0.06 * math.sin(5.7 * z + 1.3 * x)
        v.co = (x * sx * n, y * sy * n, z * sz * n * (1.0 + 0.25 * max(0.0, z) if kind == "back" else 1.0))
    me = bpy.data.meshes.new(person.name + ".bundle")
    bm.to_mesh(me)
    bm.free()
    for pl in me.polygons:
        pl.use_smooth = True
    ob = bpy.data.objects.new(person.name + ".bundle", me)
    for c in person.rig.users_collection:
        c.objects.link(ob)
    ob.data.materials.append(W.fabric_material("homespun"))
    ob.color = (*W.color(rnd.choice(["umber", "brown", "camel", "dark_brown"])), 1.0)
    person.update()
    if kind == "head":
        bone = "head"
        top = max(person.lm.get("head_top", person.height), person.height * 0.97)
        hp = person.head_pos()
        loc = Vector((hp.x, hp.y + 0.01, top + sz * 0.6))
    else:
        bone = "spine01" if person.bone_world("spine01").z > person.bone_world("spine05").z else "spine05"
        sp = person.bone_world(bone)
        loc = Vector((sp.x, sp.y + 0.20, sp.z - 0.10))
    mw = person.rig.matrix_world.copy()
    ob.parent = person.rig
    ob.parent_type = "BONE"
    ob.parent_bone = bone
    person.update()
    ob.matrix_world = __import__("mathutils").Matrix.Translation(loc)
    person.props.append(ob)
    return ob


def _staff_walk(person, i):
    """Walking with a staff: held near-vertical in the right hand, tip a little ahead (the pose engine's
    grip axis of a swinging relaxed hand would aim it like a spear)."""
    from mathutils import Matrix
    st = person.staff
    L = float(st.get("staff_length", person.height * 1.08))
    person.update()
    h = person.hand_pos("R")
    ph = 2 * math.pi * i / WALK_K
    ax = Vector((0.05, -0.10 - 0.06 * math.sin(ph), 1.0)).normalized()
    base = h - ax * 0.66 * L
    if base.z < 0.0:
        base = base - ax * (base.z / ax.z)
    R = Vector((0, 0, 1)).rotation_difference(ax).to_matrix().to_4x4()
    st.parent = person.rig
    st.parent_type = "OBJECT"
    st.matrix_world = Matrix.Translation(base) @ R


def _cache_key(lod, decimate):
    h = hashlib.md5()
    for f in ("characters.py", "wardrobe.py"):
        try:
            h.update(open(os.path.join(C.BLENDER_DIR, "lib", f), "rb").read())
        except OSError:
            pass
    h.update(repr((VARIANTS, WALK_K, lod, decimate)).encode())
    return h.hexdigest()[:12]


def walker_protos(lod="far", decimate=None, name="WK"):
    """Collection with the baked flipbook meshes '<name>_vVV_pPP' (alphabetical = variant*K + phase).
    Returns (collection, [stride per variant])."""
    from lib import characters as P
    key = _cache_key(lod, decimate)
    path = os.path.join(CACHE_DIR, "walkers_%s_%s_v%d.blend" % (lod, key, CACHE_VERSION))
    if not os.path.exists(path) and os.environ.get("S04_CACHE_ANY"):     # dev: ignore lib edits
        import glob
        cands = sorted(glob.glob(os.path.join(CACHE_DIR, "walkers_%s_*_v%d.blend" % (lod, CACHE_VERSION))),
                       key=os.path.getmtime)
        if cands:
            path = cands[-1]
    coll = C.collection(name + "_protos")
    if os.path.exists(path):
        with bpy.data.libraries.load(path, link=False) as (src, dst):
            dst.objects = [n for n in src.objects if n.startswith("WKP_")]
        objs = sorted([o for o in dst.objects if o is not None], key=lambda o: o.name)
        strides = []
        for o in objs:
            o.name = name + o.name[3:]
            coll.objects.link(o)
            if o.name.endswith("_p00"):
                strides.append(float(o["wk_stride"]))
        _exclude(coll)
        print("[s04] walkers %s loaded from cache (%d meshes)" % (lod, len(objs)))
        return coll, strides
    objs, strides = [], []
    for vi, (vn, preset, spec) in enumerate(VARIANTS):
        sp = dict(spec)
        bundle = sp.pop("bundle", None)
        per = P.make_person("wk_%s" % vn, preset, lod=lod, pose=None, expression=None, **sp)
        px = per.parts.get("proxy")
        if px is not None and per.mats.get("skin") is not None:
            # lib workaround: the far-LOD proxy body keeps MPFB's default (white) material
            px.data.materials.clear()
            px.data.materials.append(per.mats["skin"])
        if bundle:
            _bundle(per, bundle, seed=vi)
        stride = per.height * 0.5 * 1.35
        for i in range(WALK_K):
            P.pose(per, "walk", ground_z=0.0, phase=2 * math.pi * i / WALK_K)
            if getattr(per, "staff", None) is not None:
                _staff_walk(per, i)
            b = P.bake_static(per, name="WKP_v%02d_p%02d" % (vi, i), delete=False, coll=coll, decimate=decimate)
            for ch in list(b.children):          # beard curves: not instanced (one object per phase)
                bpy.data.objects.remove(ch, do_unlink=True)
            b.matrix_world = __import__("mathutils").Matrix.Identity(4)
            _slim(b)
            b["wk_stride"] = stride
            objs.append(b)
        strides.append(stride)
        P.delete_person(per)
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        tmp = path + ".tmp%d.blend" % os.getpid()
        bpy.data.libraries.write(tmp, set(objs), fake_user=True)
        os.replace(tmp, path)
    except Exception as e:
        print("[s04] cache write failed", e)
    for o in objs:
        o.name = name + o.name[3:]
    _exclude(coll)
    return coll, strides


def _slim(o):
    """Drop mesh data the far crowd shaders don't need (keeps obj_rgb, UVs, wear/hem, skin masks)."""
    me = o.data
    keep = {"obj_rgb", "wear", "hem", "cmask_a", "cmask_b", "rest_position", "position", ".edge_verts", ".corner_vert",
            ".corner_edge", "material_index", "sharp_face"}
    for a in list(me.attributes):
        if a.name.startswith(".") or a.name in keep or a.name in me.uv_layers:
            continue
        try:
            me.attributes.remove(a)
        except Exception:
            pass
    for v in list(me.color_attributes):
        if v.name != "obj_rgb":
            try:
                me.color_attributes.remove(v)
            except Exception:
                pass


def _exclude(coll):
    """Prototype collection: excluded from the view layer (only instanced)."""
    def find(lc):
        if lc.collection == coll:
            return lc
        for c in lc.children:
            r = find(c)
            if r:
                return r
    lc = find(bpy.context.view_layer.layer_collection)
    if lc:
        lc.exclude = True


def walker_lowres(coll, ratio, name):
    """Decimated copies of a prototype collection (same order / names with a new prefix)."""
    out = C.collection(name + "_protos")
    for o in sorted(coll.objects, key=lambda o: o.name):
        c = o.copy()
        c.data = o.data.copy()
        c.name = name + o.name[o.name.index("_v"):]
        out.objects.link(c)
        md = c.modifiers.new("dec", "DECIMATE")
        md.ratio = ratio
        with bpy.context.temp_override(object=c, active_object=c):
            bpy.ops.object.modifier_apply(modifier=md.name)
    _exclude(out)
    return out


def hazify_protos(coll):
    """Route the walkers' materials through the env haze (distant people fade into the dawn air)."""
    done = set()
    for o in coll.objects:
        for m in o.data.materials:
            if m and m.name not in done:
                done.add(m.name)
                E.hazify(m)


def tint_instances(coll):
    """Per-instance clothing colour variation: the baked fabric colour (obj_rgb) is shifted in hue /
    saturation / value by the instancer attribute 'wk_tint' (xyz in 0..1)."""
    done = set()
    for o in coll.objects:
        for m in o.data.materials:
            if m is None or m.name in done or not m.use_nodes or m.get("wk_tinted"):
                continue
            done.add(m.name)
            m["wk_tinted"] = 1
            nt = m.node_tree
            for at in [n for n in nt.nodes if n.bl_idname == "ShaderNodeAttribute" and n.attribute_name == "obj_rgb"]:
                links = list(at.outputs["Color"].links)
                if not links:
                    continue
                ti = nt.nodes.new("ShaderNodeAttribute")
                ti.attribute_type = "INSTANCER"
                ti.attribute_name = "wk_tint"
                sx = nt.nodes.new("ShaderNodeSeparateXYZ")
                nt.links.new(ti.outputs["Vector"], sx.inputs[0])
                hs = nt.nodes.new("ShaderNodeHueSaturation")
                mh = nt.nodes.new("ShaderNodeMapRange")
                mh.inputs["To Min"].default_value, mh.inputs["To Max"].default_value = 0.47, 0.53
                nt.links.new(sx.outputs[0], mh.inputs["Value"])
                ms = nt.nodes.new("ShaderNodeMapRange")
                ms.inputs["To Min"].default_value, ms.inputs["To Max"].default_value = 0.6, 1.25
                nt.links.new(sx.outputs[1], ms.inputs["Value"])
                mv = nt.nodes.new("ShaderNodeMapRange")
                mv.inputs["To Min"].default_value, mv.inputs["To Max"].default_value = 0.55, 1.35
                nt.links.new(sx.outputs[2], mv.inputs["Value"])
                nt.links.new(mh.outputs[0], hs.inputs["Hue"])
                nt.links.new(ms.outputs[0], hs.inputs["Saturation"])
                nt.links.new(mv.outputs[0], hs.inputs["Value"])
                nt.links.new(at.outputs["Color"], hs.inputs["Color"])
                for l in links:
                    nt.links.new(hs.outputs[0], l.to_socket)


def _walker_tree():
    name = "S04_Walkers"
    if name in bpy.data.node_groups:
        return bpy.data.node_groups[name]
    t, nb, gi, go = FX._gn_tree(name, [("Geometry", "NodeSocketGeometry"), ("Collection", "NodeSocketCollection"),
                                       ("Ground", "NodeSocketObject"), ("K", "NodeSocketFloat", float(WALK_K)),
                                       ("FPS", "NodeSocketFloat", 24.0)])
    G = lambda k: gi.outputs[k]
    fr = nb.n("GeometryNodeInputSceneTime").outputs["Frame"]
    tt = nb.div(nb.sub(fr, 1.0), G("FPS"))
    pos = nb.out(nb.n("GeometryNodeInputPosition"))
    vel = nb.attr("vel", "FLOAT_VECTOR")
    p = nb.v("ADD", pos, nb.v("SCALE", vel, scale=tt))
    ps = nb.sep(p)
    oi = nb.n("GeometryNodeObjectInfo", {"Object": G("Ground")}, transform_space="RELATIVE")
    rc = nb.n("GeometryNodeRaycast", {"Target Geometry": oi.outputs["Geometry"],
                                      "Source Position": nb.xyz(nb.out(ps, "X"), nb.out(ps, "Y"), 400.0),
                                      "Ray Direction": (0.0, 0.0, -1.0), "Ray Length": 2000.0})
    hz = nb.out(nb.sep(rc.outputs["Hit Position"]), "Z")
    z = nb.mixf(rc.outputs["Is Hit"], nb.out(ps, "Z"), hz)
    newp = nb.xyz(nb.out(ps, "X"), nb.out(ps, "Y"), z)
    g = nb.out(nb.n("GeometryNodeSetPosition", {"Geometry": G("Geometry"), "Position": newp}))
    m = nb.add(fr, nb.attr("ph0"))
    ph = nb.sub(m, nb.mul(G("K"), nb.m("FLOOR", nb.div(m, G("K")))))
    idx = nb.add(nb.mul(nb.attr("var"), G("K")), nb.m("FLOOR", nb.add(ph, 0.001)))
    ci = nb.n("GeometryNodeCollectionInfo", {"Collection": G("Collection"), "Separate Children": True,
                                             "Reset Children": True})
    iop = nb.n("GeometryNodeInstanceOnPoints", {"Points": g, "Instance": ci.outputs[0], "Pick Instance": True,
                                                "Instance Index": idx,
                                                "Rotation": nb.xyz(0.0, 0.0, nb.attr("yaw")),
                                                "Scale": nb.attr("scl")})
    nb.links.new(nb.out(iop), go.inputs[0])
    return t


def walker_field(name, coll, strides, people, ground, coll_out=None):
    """people: list of dicts {x, y, var, dir (radians heading, 0 = +Y), speed_scale, ph0, scl}.
    Speed per variant = stride * fps / WALK_K (feet locked to the cycle)."""
    fps = bpy.context.scene.render.fps
    pos, vel, var, yaw, scl, ph0, tint = [], [], [], [], [], [], []
    rnd = random.Random(7)
    for q in people:
        v = q["var"]
        sp = strides[v] * fps / WALK_K
        d = q.get("dir", 0.0)
        pos.append((q["x"], q["y"], q.get("z", 0.0)))
        vel.append((math.sin(d) * sp, math.cos(d) * sp, 0.0))
        var.append(v)
        yaw.append(math.pi - d)            # people face -Y at yaw 0
        scl.append(q.get("scl", 1.0))
        ph0.append(q.get("ph0", rnd.randrange(WALK_K)))
        tint.append(q.get("tint", (rnd.random(), rnd.random(), rnd.random())))
    o = FX._points_obj(name, pos, {"vel": np.array(vel), "var": np.array(var, np.float32), "yaw": np.array(yaw),
                                   "scl": np.array(scl), "ph0": np.array(ph0, np.float32),
                                   "wk_tint": np.array(tint)}, coll_out)
    FX._mod(o, _walker_tree(), "Walkers", Collection=coll, Ground=ground, K=float(WALK_K), FPS=float(fps))
    return o


def far_mountains(center_y, dist=(2600.0, 5200.0), width=9000.0, height=(160.0, 520.0), seed=3, name="S04_Mountains",
                  color=(0.30, 0.24, 0.22), toward=1.0):
    """Distant mountain ridges (two layers) beyond a shore, hazed by the env haze: silhouettes against the
    dawn sky that give depth and scale. toward=+1 -> at +Y, -1 -> at -Y."""
    objs = []
    for li, (d, h) in enumerate(zip(dist, height)):
        nx, nz = 240, 6
        xs = np.linspace(-width / 2, width / 2, nx)
        prof = E.ridged(xs * 0.0011 + li * 13.1, np.full(nx, 0.37 + li * 2.3), octaves=5, seed=seed + li)
        prof = (prof - prof.min()) / max(1e-6, prof.max() - prof.min())
        verts, faces = [], []
        for i, x in enumerate(xs):
            top = h * (0.35 + 0.65 * prof[i]) * (0.75 + 0.25 * math.cos(x / width * math.pi))
            for j in range(nz):
                t = j / (nz - 1)
                verts.append((x, center_y + toward * (d + 300.0 * (1 - t)), -40.0 + (top + 40.0) * t))
        for i in range(nx - 1):
            for j in range(nz - 1):
                a = i * nz + j
                faces.append((a, a + nz, a + nz + 1, a + 1) if toward > 0 else (a, a + 1, a + nz + 1, a + nz))
        o = FX._mesh_obj("%s_%d" % (name, li), verts, faces, smooth=True)
        m = C.mat("%s_mat%d" % (name, li), color, rough=0.9)
        E.hazify(m)
        C.assign(o, m)
        o.visible_shadow = False
        objs.append(o)
    return objs
