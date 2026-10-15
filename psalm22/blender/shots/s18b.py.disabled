"""s18b "Nations bow" — 147 frames, dissolve in from s18a (Earth from space, sunrise over Africa/Europe).

"for dominion belongs to the Lord / and he rules over the nations."

From behind, telephoto: a sea of people of many nations — African, East Asian, South Asian, European,
Arab, Latin — in varied dyed garments, kneeling (upright, praying, bowed to the ground) on the dawn
plain, all facing a distant hill where the EMPTY cross stands against the rising sun. The camera rises
slowly behind them (1.5 m -> 5.5 m) so the multitude unrolls towards the hill.

Build: env.plain_dawn('sunrise'); 8 hand-picked variants (characters crowd specs, wardrobe colours),
kneeling skirts cloth-settled (drape) once per variant, baked, then ~1000 linked duplicates in three LOD
tiers (near: baked variants; mid: 35 % decimated; far: 10 % decimated, no shadows). Per-instance dye
variation through a hue/saturation tweak in the baked fabric materials (driven by obj.color).
"""
import bpy, math, random, time
from mathutils import Vector
from lib import core as C, env as E, characters as P

LENS = 70.0
SUN_AZ = 170.0
CROSS_SCALE = 1.45        # the far cross reads at telephoto (5.6 m -> ~8 m: symbolic, monumental)

# (preset, spec overrides, outfit, colours, pose, pose params)
VARIANTS = [
    ("CROWD_MAN", dict(ethnicity="african", hair="afro01", hair_color="black", beard="short", age_years=34),
     ["tunic", "mantle"], {"tunic": "saffron", "mantle": "madder", "belt": "dark_brown"}, "kneel_pray", {}),
    ("CROWD_WOMAN", dict(ethnicity="east_asian", hair="ponytail01", hair_color="black", age_years=27),
     ["tunic", "mantle"], {"tunic": "white_linen", "mantle": "tekhelet"}, "kneel", {"head": "level"}),
    ("CROWD_MAN", dict(ethnicity="european", hair="short02", hair_color="light_brown", beard="short", age_years=45),
     ["tunic", "mantle"], {"tunic": "oatmeal", "mantle": "woad"}, "kneel_bow", {}),
    ("CROWD_WOMAN", dict(ethnicity="south_asian", age_years=38),
     ["tunic", "veil"], {"tunic": "scarlet", "veil": "saffron"}, "kneel_pray", {}),
    ("CROWD_MAN", dict(ethnicity="arab", beard="full", age_years=52),
     ["tunic", "mantle", "headcloth"], {"tunic": "bleached", "mantle": "camel", "headcloth": "white_linen"}, "kneel_bow", {}),
    ("CROWD_WOMAN", dict(ethnicity="latin", hair="braid01", hair_color="dark_brown", age_years=31),
     ["tunic", "mantle"], {"tunic": "ochre", "mantle": "purple"}, "kneel", {"head": "bowed"}),
    ("CROWD_MAN", dict(ethnicity="east_asian", hair="short01", hair_color="black", beard="none", age_years=24),
     ["tunic", "mantle"], {"tunic": "olive", "mantle": "rust"}, "kneel_pray", {}),
    ("CROWD_WOMAN", dict(ethnicity="african", age_years=44),
     ["tunic", "headcloth"], {"tunic": "woad", "headcloth": "ochre"}, "kneel", {"head": "bowed"}),
]


def _vary_fabrics(mats):
    """Baked fabric materials read the dye from the 'obj_rgb' attribute: put a Hue/Saturation/Value on it
    driven by the instance's obj.color (r = hue, g*2 = saturation, b*2 = value; (0.5, 0.5, 0.5) = as dyed)."""
    for m in mats:
        if m is None or not m.use_nodes or m.get("s18b_vary"):
            continue
        nt = m.node_tree
        ats = [n for n in nt.nodes if n.bl_idname == "ShaderNodeAttribute" and n.attribute_name == "obj_rgb"]
        if not ats:
            continue
        m["s18b_vary"] = 1
        oi = nt.nodes.new("ShaderNodeObjectInfo")
        sep = nt.nodes.new("ShaderNodeSeparateColor")
        nt.links.new(oi.outputs["Color"], sep.inputs["Color"])
        ms = nt.nodes.new("ShaderNodeMath")
        ms.operation = "MULTIPLY"
        ms.inputs[1].default_value = 2.0
        nt.links.new(sep.outputs["Green"], ms.inputs[0])
        mv = nt.nodes.new("ShaderNodeMath")
        mv.operation = "MULTIPLY"
        mv.inputs[1].default_value = 2.0
        nt.links.new(sep.outputs["Blue"], mv.inputs[0])
        for at in ats:
            links = list(at.outputs["Color"].links)
            hsv = nt.nodes.new("ShaderNodeHueSaturation")
            nt.links.new(at.outputs["Color"], hsv.inputs["Color"])
            nt.links.new(sep.outputs["Red"], hsv.inputs["Hue"])
            nt.links.new(ms.outputs[0], hsv.inputs["Saturation"])
            nt.links.new(mv.outputs[0], hsv.inputs["Value"])
            for l in links:
                nt.links.new(hsv.outputs["Color"], l.to_socket)


def _decimated(src, ratio, name, coll):
    me = src.data.copy()
    me.name = name
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    dm = o.modifiers.new("dec", "DECIMATE")
    dm.ratio = ratio
    with bpy.context.temp_override(object=o, active_object=o):
        bpy.ops.object.modifier_apply(modifier=dm.name)
    o.location = (0, 0, -500)
    o.hide_render = o.hide_viewport = True
    return o


def build(ctx):
    t0 = time.time()
    N, NR = ctx.nframes, ctx.render_frames
    rnd = random.Random(ctx.seed + 18)

    # ------------------------------------------------------------------ set
    A = E.plain_dawn(ctx, "sunrise", hillside=0.45, sun_az=SUN_AZ, grass=1.0)
    gz = A["ground_z"]
    sky = A["sky"]
    print("s18b: sun_el %.2f sun_az %.1f energy %.2f" % (sky.get("sun_el", -1), SUN_AZ, sky.get("sun_energy", -1)))
    croot = bpy.data.objects.get("Cross_far")
    hx, hy, htop = A["cross_hill_top"]
    if croot is not None and CROSS_SCALE != 1.0:
        croot.scale = (CROSS_SCALE,) * 3
    cross_top = Vector((hx, hy, htop - 0.5 + 5.6 * CROSS_SCALE))
    cross_mid = Vector((hx, hy, htop - 0.5 + 3.4 * CROSS_SCALE))

    # ------------------------------------------------------------------ camera rig (needed for the crowd wedge)
    cam0 = Vector((0.4, -13.0, 0.0))
    cam0.z = gz(cam0.x, cam0.y) + 1.45
    cam1 = Vector((0.3, -15.5, 0.0))
    cam1.z = gz(cam1.x, cam1.y) + 5.6
    axis = Vector((hx - cam0.x, hy - cam0.y, 0)).normalized()
    side = Vector((axis.y, -axis.x, 0))

    # ------------------------------------------------------------------ the people (variants -> baked)
    src_coll = C.collection("NationsSrc")
    srcs = []
    tb = time.time()
    for i, (pre, sp, outfit, cols, pz, pkw) in enumerate(VARIANTS):
        spec = dict(sp)
        spec.update(lod="mid", hair_strands=False, pose=None, expression=None, seed=180 + i * 7,
                    outfit=outfit, outfit_colors=cols)
        p = P.make_person("nat%d" % i, pre, **spec)
        P.pose(p, pz, drape=True, **pkw)
        b = P.bake_static(p, name="nat_src%d" % i, coll=src_coll)
        for ch in list(b.children):        # beard curves: invisible from behind, skip their cost
            bpy.data.objects.remove(ch, do_unlink=True)
        b.location = (0, 0, -500)
        b.hide_render = b.hide_viewport = True
        srcs.append(b)
        print("s18b: variant %d built %.1fs (%d verts)" % (i, time.time() - tb, len(b.data.vertices)))
    mats = {m for s in srcs for m in s.data.materials if m is not None}
    for m in mats:
        E.hazify(m)
    _vary_fabrics(mats)
    mid = [_decimated(s, 0.35, s.name + "_mid", src_coll) for s in srcs]
    far = [_decimated(s, 0.1, s.name + "_far", src_coll) for s in srcs]
    print("s18b: crowd sources %.1fs" % (time.time() - tb))

    # ------------------------------------------------------------------ placements: loose rows in the view wedge
    coll = C.collection("Nations")
    pts = []
    d = 4.2
    row = 0
    while d < 105.0:
        half = d * 0.135 + 1.6 + (0.0 if d < 30 else d * 0.02)
        dx = 0.95 if d < 30 else 1.05
        off = (row % 2) * dx * 0.5
        u = -half + off
        while u < half:
            if d > 18 and rnd.random() < 0.06:          # small gaps / family groups
                u += dx
                continue
            q = Vector((cam0.x, cam0.y, 0)) + axis * (d + rnd.uniform(-0.25, 0.25)) + side * (u + rnd.uniform(-0.22, 0.22))
            pts.append((q.x, q.y, d))
            u += dx * rnd.uniform(0.92, 1.1)
        row += 1
        d += 1.2 if d < 30 else 1.35
    order = []
    while len(order) < len(pts):
        blk = list(range(len(srcs)))
        rnd.shuffle(blk)
        order += blk
    face = Vector((hx, hy))
    nt = [0, 0, 0]
    for k, (x, y, dd) in enumerate(pts):
        tier = 0 if dd < 15 else (1 if dd < 38 else 2)
        src = (srcs, mid, far)[tier][order[k]]
        o = src.copy()
        coll.objects.link(o)
        o.hide_render = o.hide_viewport = False
        z = gz(x, y)
        yw = math.atan2(face.x - x, -(face.y - y)) + math.radians(rnd.uniform(-7, 7))
        o.location = (x, y, z - 0.01)
        o.rotation_euler = (0, 0, yw)
        s = rnd.uniform(0.95, 1.05)
        o.scale = (s, s, s)
        if tier == 0:
            o.color = (0.5, 0.5, 0.5, 1.0)                 # near: the dyes as chosen
        else:
            o.color = (rnd.random(), rnd.uniform(0.45, 0.62), rnd.uniform(0.42, 0.58), 1.0)
        if tier == 2:
            o.visible_shadow = False
        nt[tier] += 1
    print("s18b: %d people (near %d, mid %d, far %d)" % (len(pts), *nt))

    # ------------------------------------------------------------------ camera: slow rise behind them
    tgt0 = Vector((hx, hy, htop + 1.0))
    tgt1 = Vector((hx, hy, htop - 6.0))
    focus_d = 26.0
    cam = C.camera(loc=tuple(cam0), target=tuple(tgt0), lens=LENS, fstop=5.6, focus=focus_d)

    def path(f):
        u = C.ease_in_out((f - 1) / max(1, NR - 1))
        loc = cam0.lerp(cam1, u) + C.shake(f, 0.012, 0.35, 18)
        tg = tgt0.lerp(tgt1, u)
        return (loc, tg, 0.0, LENS, focus_d + 4.0 * u)

    C.animate_camera(cam, path, 1, NR)

    # ------------------------------------------------------------------ render settings / post
    ctx.samples = 5
    ctx.interp = True
    ctx.render_opts = {"volumetrics": "low", "shadow_scale": 0.5}
    ctx.post = {"grade": "dawn", "bloom": 0.34, "bloom_threshold": 0.66, "vignette": 0.18,
                "caption": {"halo": 1.2}}
    print("s18b: build %.1fs" % (time.time() - t0))
