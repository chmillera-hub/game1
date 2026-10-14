"""s03 - "Yet you are enthroned as the Holy One; you are the one Israel praises."

Holy of Holies (flashback / symbolic). Low-key Holy Place: the great embroidered veil glows from
behind, a hairline of gold light at its seam, incense rising from the golden altar. On "Yet you are
enthroned" the veil parts and the light floods out through the smoke; the camera glides past the
altar and through the opening towards the Ark - the cherubim kneel in silhouette against the glory
between their wings, rays fanning through the incense. On "Israel praises" the glory swells; at the
end the camera rises into it and the frame blooms to near-white (flash cut to s04a).
"""
import math
from mathutils import Vector
from lib import core as C
from lib import sets as S


def _hermite(keys, f):
    """Cubic Hermite spline through [(frame, Vector)] with Catmull-Rom tangents (non-uniform)."""
    if f <= keys[0][0]:
        return Vector(keys[0][1])
    if f >= keys[-1][0]:
        return Vector(keys[-1][1])
    n = len(keys)

    def tan(i):
        if i == 0:
            return (keys[1][1] - keys[0][1]) / (keys[1][0] - keys[0][0])
        if i == n - 1:
            return (keys[-1][1] - keys[-2][1]) / (keys[-1][0] - keys[-2][0])
        return (keys[i + 1][1] - keys[i - 1][1]) / (keys[i + 1][0] - keys[i - 1][0])
    for i in range(n - 1):
        f0, p0 = keys[i]
        f1, p1 = keys[i + 1]
        if f0 <= f <= f1:
            h = f1 - f0
            t = (f - f0) / h
            t2, t3 = t * t, t * t * t
            m0, m1 = tan(i) * h, tan(i + 1) * h
            return (p0 * (2 * t3 - 3 * t2 + 1) + m0 * (t3 - 2 * t2 + t) + p1 * (-2 * t3 + 3 * t2) +
                    m1 * (t3 - t2))
    return Vector(keys[-1][1])


def _key_energy(light, pairs):
    for f, e in pairs:
        light.data.energy = e
        light.data.keyframe_insert("energy", frame=f)


def _key_energy(light, pairs):
    for f, e in pairs:
        light.data.energy = e
        light.data.keyframe_insert("energy", frame=f)


def build(ctx):
    import bpy
    n, N = ctx.nframes, ctx.render_frames
    p1a, p1b = ctx.phrase_frames(0)                  # "Yet you are enthroned as the Holy One;"
    p2a, p2b = ctx.phrase_frames(1)                  # "you are the one Israel praises."
    V = lambda *a: Vector(a)

    hoh = S.holy_of_holies(ctx, veil_open=0.0, glory=1.0, smoke=True, shafts=True, holy_place=True)
    L, O = hoh.lights, hoh.objects
    ark = hoh["ark"]

    # ---------------- relight: low-key room, the glory is the key ----------------
    bg = bpy.context.scene.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.05, 0.03, 0.012, 1)
    L["room_fill"].data.energy = 5.0
    L["glory_fill"].data.energy = 35.0
    L["glory"].data.energy = 520.0
    L["veil_front"].data.energy = 30.0
    for k in ("shaft0", "shaft1"):
        L[k].data.energy = 2600.0
    # floor: darker, more satin gold so the glory's pool of light doesn't shout in the caption zone
    fm = bpy.data.materials.get("set_gold_floor")
    if fm:
        b = fm.node_tree.nodes.get("Principled BSDF")
        b.inputs["Base Color"].default_value = (0.5, 0.33, 0.13, 1)
        for nd in fm.node_tree.nodes:
            if nd.type == "MAP_RANGE":
                nd.inputs["To Min"].default_value = 0.38
                nd.inputs["To Max"].default_value = 0.62
    # light linking: the glory's point light skips the floors (its pool of light shouted in the caption zone);
    # a soft shadowless floor-only glow replaces it
    fl = bpy.data.collections.new("s03_floor_rx")
    for nm in ("hoh_floor", "hp_floor"):
        ob = bpy.data.objects.get(nm)
        if ob:
            fl.objects.link(ob)
    L["glory"].light_linking.receiver_collection = fl
    for co in fl.collection_objects:
        co.light_linking.link_state = "EXCLUDE"
    fg = C.light("POINT", loc=tuple(hoh["glory"]), energy=6.0, temp=5200, size=0.6, shadow=False, name="floor_glow")
    fg.data.volume_factor = 0.0
    fl2 = bpy.data.collections.new("s03_floor_only")
    for ob in fl.objects:
        fl2.objects.link(ob)
    fg.light_linking.receiver_collection = fl2
    # the Ark and cherubim get no fill: they stand in silhouette (rim-lit) against the glory
    arkset = bpy.data.collections.new("s03_ark_rx")
    for ob in hoh.coll.objects:
        if ob.type == "MESH" and ob.name.startswith("cherub"):
            arkset.objects.link(ob)
    for k in ("room_fill", "glory_fill", "veil_front", "menorah"):
        L[k].light_linking.receiver_collection = arkset
        for co in arkset.collection_objects:
            co.light_linking.link_state = "EXCLUDE"
    L["glory"].data.color = C.kelvin(5000)
    for k in ("shaft0", "shaft1"):
        L[k].data.diffuse_factor = 0.0
        L[k].data.specular_factor = 0.0
    # the cloud of incense over the mercy seat (Lev 16:2,13), lit from within by the glory
    cloud = C.box("s03_glory_cloud", (2.3, 1.7, 2.0), (0.0, ark.y, 1.55), coll=hoh.coll)
    cloud.data.materials.append(S._smoke_material("s03_cloud", density=1.2, color=(1.0, 0.95, 0.86), scale=2.4,
                                                  rise=0.18, anisotropy=0.35, shape="sphere", falloff=0.9))
    cloud.visible_shadow = True
    # veil look: less glow through the weave, softer colours, raking lamplight across the pleats,
    # a faint cool fill that keeps the blue ground alive (and echoes the moonlit s02b it dissolves from)
    vm = bpy.data.materials.get("set_veil")
    if vm:
        nt = vm.node_tree
        for nd in nt.nodes:
            if nd.type == "MIX_SHADER":
                nd.inputs[0].default_value = 0.1
        img = next((nd for nd in nt.nodes if nd.type == "TEX_IMAGE" and "color" in nd.image.name), None)
        if img:
            hs = nt.nodes.new("ShaderNodeHueSaturation")
            hs.inputs["Saturation"].default_value = 0.85
            hs.inputs["Value"].default_value = 0.95
            nt.links.new(img.outputs["Color"], hs.inputs["Color"])
            nt.links.new(hs.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    L["menorah"].location = (-3.6, -1.0, 2.0)
    L["menorah"].data.energy = 500.0
    L["veil_front"].data.color = C.kelvin(11000)
    # backlight behind the closed veil: the glory glowing through the weave
    vb = C.light("AREA", loc=(0.0, 1.3, 3.2), energy=450.0, temp=4300, target=(0.0, -2.0, 3.0), size=5.0,
                 shadow=False, name="veil_back")
    vb.data.volume_factor = 0.0
    # blade of light through the seam / the parting (shadowed by the veil) into the Holy Place incense
    blade = C.light("SPOT", loc=(0.0, 2.2, 1.7), energy=900.0, temp=5600, target=(-1.3, -3.0, 1.2), size=0.05,
                    spot_size=75, spot_blend=0.5, shadow=True, name="seam_blade")
    blade.data.volume_factor = 1.6
    # the incense altar is a plain box up close: keep only its smoke and ember glow (it stays below frame)
    for ob in hoh.coll.objects:
        if ob.name.startswith(("incense_altar", "altar_horn", "incense_coals")):
            ob.hide_render = True
    # altar smoke + ember glow moved right of the axis so the camera glides past, not through, it
    for nm in ("altar_smoke", "altar_glow"):
        ob = bpy.data.objects.get(nm)
        if ob:
            ob.location.x = 0.55
    # thinner Holy Place haze so the reveal reads through it
    for nd in bpy.data.materials["set_incense_hp"].node_tree.nodes:
        if nd.type == "MAP_RANGE" and abs(nd.inputs["To Max"].default_value - 0.05) < 1e-4:
            nd.inputs["To Max"].default_value = 0.032
    # incense: censer + column beside the Ark (right-front), clouding the mercy seat (Lev 16:13)
    if bpy.data.objects.get("censer"):
        bpy.data.objects["censer"].hide_render = True
    for nm in ("censer", "hoh_incense_column"):
        ob = bpy.data.objects.get(nm)
        if ob:
            ob.location.x, ob.location.y = 0.75, 5.25

    # ---------------- veil: hairline of light, then parting on "enthroned" ----------------
    f_open0 = p1a + 6
    f_open1 = p1b + 2
    # a slit first (the glory seen through it), wide enough to slip through when the camera arrives,
    # then fully drawn aside behind the camera
    S.animate_veil(hoh, [(1, 0.018), (int(f_open0), 0.03), (int(p1a + 0.65 * (p1b - p1a)), 0.085),
                         (int(p1b + 4), 0.13), (int(p2a + 20), 0.3), (int(p2b), 1.0)])
    _key_energy(vb, [(1, 450.0), (int(f_open0), 450.0), (int(f_open0 + 0.6 * (f_open1 - f_open0)), 0.0)])
    _key_energy(L["veil_front"], [(1, 30.0), (int(p1b + 10), 30.0), (int(p2a + 20), 0.0)])
    _key_energy(blade, [(1, 900.0), (int(f_open0 + 0.5 * (f_open1 - f_open0)), 700.0), (int(f_open1 + 20), 0.0)])

    # ---------------- glory ----------------
    f_end0 = p2b + 4                                 # whiteout begins after the last phrase
    S.set_glory(hoh, [(1, 0.8), (int(f_open0), 0.85), (int(f_open1), 1.15), (int(p2a), 1.2),
                      (int((p2a + p2b) / 2), 1.45), (int(f_end0), 1.6), (n, 9.0), (N, 9.0)])
    gv = O.get("glory_volume")
    if gv:
        for f, sc in ((1, 1.0), (int(f_end0), 1.15), (n, 4.0)):
            gv.scale = (sc, sc, sc)
            gv.keyframe_insert("scale", frame=f)

    # ---------------- camera: oblique glide from the left, through the parting, arcing round ----------------
    cam_keys = [
        (1, V(0.0, -3.1, 1.45)),
        (p1a + 24, V(0.0, -2.1, 1.5)),
        (p1b + 4, V(-0.15, 0.0, 1.62)),           # slipping through the parting
        (p2a + 15, V(-0.6, 0.7, 1.85)),
        (f_end0, V(-0.95, 1.4, 2.1)),
        (n, V(-0.6, 2.1, 2.9)),                   # rising into the light
    ]
    tgt_keys = [
        (1, V(0.0, 0.0, 2.1)),
        (p1a + 24, V(0.0, 4.5, 1.5)),
        (p1b + 4, V(0.0, 4.5, 1.15)),
        (p2a + 15, V(0.0, 4.5, 0.95)),
        (f_end0, V(0.0, 4.5, 0.95)),
        (n, V(0.0, 4.5, 1.5)),
    ]
    veil_pt = V(0.0, 0.0, 1.9)
    ark_pt = V(0.0, ark.y, 1.1)

    def focus_at(f, loc):
        k = C.smoothstep((f - f_open0) / max(1.0, (p1b - f_open0)))
        fp = veil_pt.lerp(ark_pt, k)
        return max(0.5, (fp - loc).length)

    def path(f):
        loc = _hermite(cam_keys, f) + C.shake(f, 0.006, 0.5, 3)
        tgt = _hermite(tgt_keys, f)
        return loc, tgt, 0.0, 32, focus_at(f, loc)
    cam = C.camera(loc=tuple(cam_keys[0][1]), target=tuple(tgt_keys[0][1]), lens=32, fstop=2.8, focus=4.0)
    C.animate_camera(cam, path)

    ctx.samples = 6
    ctx.render_opts = {"volumetrics": "low"}
    ctx.interp = True
    ctx.post.update({"grade": "gold", "temperature": 0.2, "bloom": 0.42, "vignette": 0.22,
                     "caption": {"halo": 1.2},
                     "end": {"bloom": 0.6}})
