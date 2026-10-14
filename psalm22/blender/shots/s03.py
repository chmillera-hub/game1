"""s03 - "Yet you are enthroned as the Holy One; you are the one Israel praises."

Holy of Holies (symbolic flashback), built on lib/sets.holy_of_holies.
Low-key Holy Place: the great embroidered veil, raked by lamplight, a slit of light at its seam with
the glory glimpsed through it and incense curling in front. On "Yet you are enthroned" the slit widens
and the camera glides through the parting (the curtain edges slide past the frame); inside, the Ark
with two kneeling cherubim, their gilded wings rising into a pointed arch over the mercy seat, the
cherubim in silhouette rim-lit by the glory and wrapped in a glowing incense cloud. On "Israel praises"
the glory swells; then the camera rises into it and the frame blooms to near-white (flash cut to s04a).

Changes to the set made here (no lib edits): rebuilt wings (S._wing, upswept, feathers outward) instead
of the forward-arched ones that read as a heart from the front; light linking keeps the glory's pool of
light off the floor and the fills off the cherubim; altar box and censer hidden (smoke kept); darker
satin floor; calmer veil material; extra lights: wing kicker, glory-up (volume only), slit spill,
veil backlight, end whiteout.
"""
import math
from mathutils import Vector, Matrix
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


def _link(light, objs, state):
    """Light linking (EEVEE Next): restrict `light` to / exclude it from `objs`."""
    import bpy
    col = bpy.data.collections.new("s03_rx_" + light.name)
    for o in objs:
        col.objects.link(o)
    light.light_linking.receiver_collection = col
    for co in col.collection_objects:
        co.light_linking.link_state = state


def _set_map_range_max(mat, old, new):
    for nd in mat.node_tree.nodes:
        if nd.type == "MAP_RANGE" and abs(nd.inputs["To Max"].default_value - old) < 1e-4:
            nd.inputs["To Max"].default_value = new


def build(ctx):
    import bpy
    n, N = ctx.nframes, ctx.render_frames
    p1a, p1b = ctx.phrase_frames(0)                  # "Yet you are enthroned as the Holy One;"
    p2a, p2b = ctx.phrase_frames(1)                  # "you are the one Israel praises."
    V = lambda *a: Vector(a)
    ob_ = bpy.data.objects.get

    hoh = S.holy_of_holies(ctx, veil_open=0.0, glory=1.0, smoke=True, shafts=True, holy_place=True)
    L, O = hoh.lights, hoh.objects
    ark = hoh["ark"]
    glory = hoh["glory"]

    # ================= dressing =================
    # Cherubim wings "spread upward, overshadowing the cover" (Ex 25:20). The set's forward-arched wings read
    # as a heart from the front, so rebuild them with the set's own feathered-wing generator: the leading
    # edges rise from the shoulders into a pointed arch over the mercy seat (tips meeting high above the
    # glory) and the feathers fan outward - the kneeling cherubim and the light sit inside a gothic arch.
    lid_mat = bpy.data.materials.get("set_gold_lid")
    wb = S._B("s03_wings", (0, 0, 0), 0.0, hoh.coll, 5)
    for w in list(hoh.coll.objects):
        if w.name.startswith("cherub_wing"):
            w.hide_render = w.hide_viewport = True
    wings = []
    for chn in ("cherub_L", "cherub_R"):
        ch = ob_(chn)
        if ch is None:
            continue
        for sy in (-1, 1):
            spine = [(-0.07, sy * 0.08, 0.44), (-0.12, sy * 0.17, 0.64), (-0.08, sy * 0.24, 0.88),
                     (0.02, sy * 0.27, 1.1), (0.13, sy * 0.26, 1.27), (0.24, sy * 0.23, 1.38)]
            wg = S._wing("s03_wing", wb, lid_mat, spine, side=sy, chord=(0.12, 0.22, 0.24, 0.13),
                         center=(-0.7, sy * 0.25, 0.7))
            wg.parent = ch
            wings.append(wg)
    cherubim = [o for o in (ob_("cherub_L"), ob_("cherub_R")) if o] + wings
    # the incense altar is a plain box up close: keep only its smoke and ember glow (below frame); move
    # them right of the axis so the camera glides past, not through, the smoke
    for o in hoh.coll.objects:
        if o.name.startswith(("incense_altar", "altar_horn", "incense_coals")):
            o.hide_render = True
    for nm in ("altar_smoke", "altar_glow"):
        if ob_(nm):
            ob_(nm).location.x = 0.32
    # the censer's smoke column rises behind the Ark (backlit by the glory); the censer itself is hidden
    if ob_("censer"):
        ob_("censer").hide_render = True
    for nm in ("censer", "hoh_incense_column"):
        if ob_(nm):
            ob_(nm).location.x, ob_(nm).location.y = 0.75, 5.25
    # thinner Holy Place haze so the reveal reads through it
    _set_map_range_max(bpy.data.materials["set_incense_hp"], 0.05, 0.032)
    # the cloud of incense over the mercy seat (Lev 16:2,13), lit from within by the glory
    cloud = C.box("s03_glory_cloud", (2.3, 1.7, 2.0), (0.0, ark.y, 1.55), coll=hoh.coll)
    cloud.data.materials.append(S._smoke_material("s03_cloud", density=1.2, color=(1.0, 0.95, 0.86), scale=2.4,
                                                  rise=0.18, anisotropy=0.35, shape="sphere", falloff=0.9))
    # floor: darker, satin gold
    fm = bpy.data.materials.get("set_gold_floor")
    if fm:
        fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.5, 0.33, 0.13, 1)
        for nd in fm.node_tree.nodes:
            if nd.type == "MAP_RANGE":
                nd.inputs["To Min"].default_value = 0.38
                nd.inputs["To Max"].default_value = 0.62
    # veil: less glow through the weave, softer colours (the embroidery read as neon)
    vm = bpy.data.materials.get("set_veil")
    if vm:
        nt = vm.node_tree
        for nd in nt.nodes:
            if nd.type == "MIX_SHADER":
                nd.inputs[0].default_value = 0.06
        img = next((nd for nd in nt.nodes if nd.type == "TEX_IMAGE" and "color" in nd.image.name), None)
        if img:
            hs = nt.nodes.new("ShaderNodeHueSaturation")
            hs.inputs["Saturation"].default_value = 0.85
            hs.inputs["Value"].default_value = 0.95
            nt.links.new(img.outputs["Color"], hs.inputs["Color"])
            nt.links.new(hs.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
        hi = next((nd for nd in nt.nodes if nd.type == "TEX_IMAGE" and "height" in nd.image.name), None)
        if hi:                                       # gold-thread embroidery glints (smoother than the wool)
            mr = nt.nodes.new("ShaderNodeMapRange")
            mr.inputs["From Min"].default_value = 0.3
            mr.inputs["From Max"].default_value = 0.6
            mr.inputs["To Min"].default_value = 0.78
            mr.inputs["To Max"].default_value = 0.32
            nt.links.new(hi.outputs["Color"], mr.inputs["Value"])
            nt.links.new(mr.outputs["Result"], nt.nodes["Principled BSDF"].inputs["Roughness"])

    # ================= light: low-key room, the glory is the key =================
    bg = bpy.context.scene.world.node_tree.nodes.get("Background")
    if bg:                                           # dimmer uniform environment for the gold reflections
        bg.inputs[0].default_value = (0.05, 0.03, 0.012, 1)
    L["room_fill"].data.energy = 5.0
    L["glory_fill"].data.energy = 35.0
    L["glory"].data.energy = 520.0
    L["glory"].data.color = C.kelvin(5000)
    for k in ("shaft0", "shaft1"):                   # corner shafts: volume only (they pooled on the floor)
        L[k].data.energy = 2600.0
        L[k].data.diffuse_factor = L[k].data.specular_factor = 0.0
    # Holy Place: raking lamplight across the veil's pleats + a faint cool fill that keeps the blue ground
    # alive (and echoes the moonlit s02b it dissolves from)
    L["menorah"].location = (-3.6, -1.0, 2.0)
    L["menorah"].data.energy = 260.0
    L["veil_front"].data.color = C.kelvin(11000)
    # the glory's point light skips the floors (its pool of light shouted in the caption zone); a faint
    # shadowless floor-only glow replaces it
    floors = [o for o in (ob_("hoh_floor"), ob_("hp_floor")) if o]
    _link(L["glory"], floors, "EXCLUDE")
    fg = C.light("POINT", loc=tuple(glory), energy=6.0, temp=5200, size=0.6, shadow=False, name="floor_glow")
    fg.data.volume_factor = 0.0
    _link(fg, floors, "INCLUDE")
    # the cherubim get no fill: they kneel in silhouette, rim-lit by the glory between them; the wings keep
    # the soft top light so their feathers read as gold, not black paper
    bodies = [o for o in (ob_("cherub_L"), ob_("cherub_R")) if o]
    for k in ("room_fill", "veil_front", "menorah"):
        _link(L[k], cherubim, "EXCLUDE")
    _link(L["glory_fill"], bodies, "EXCLUDE")
    L["glory"].data.shadow_soft_size = 0.45          # broader, softer highlights on the bowed heads
    # a soft high side light only for the wings, so the feathers read as gilded and modelled
    wk = C.light("AREA", loc=(-1.6, 2.2, 3.8), energy=260.0, temp=4800, target=(0.0, ark.y, 1.8), size=3.0,
                 shadow=False, name="wing_kick")
    wk.data.volume_factor = 0.0
    _link(wk, wings, "INCLUDE")
    # the glory rising: a volume-only spot from the mercy seat lights the incense above the wings
    g0 = glory + V(0, 0, 0.08)
    up = C.light("SPOT", loc=tuple(g0), energy=6000.0, temp=5200, target=tuple(g0 + V(0, 0, 1)), size=0.08,
                 spot_size=34, spot_blend=0.7, shadow=False, name="glory_up")
    up.data.diffuse_factor = up.data.specular_factor = 0.0
    # backlight behind the closed veil: the glory glowing through the weave
    vb = C.light("AREA", loc=(0.0, 1.3, 3.2), energy=450.0, temp=4300, target=(0.0, -2.0, 3.0), size=5.0,
                 shadow=False, name="veil_back")
    vb.data.volume_factor = 0.0
    # light spilling through the slit / the parting (shadowed by the veil) into the Holy Place incense
    blade = C.light("SPOT", loc=(0.0, 2.2, 1.7), energy=900.0, temp=5600, target=(-1.3, -3.0, 1.2), size=0.05,
                    spot_size=75, spot_blend=0.5, shadow=True, name="seam_blade")
    blade.data.volume_factor = 1.6

    # ================= timing =================
    # veil: a slit (the glory seen through it), widening on "enthroned"; just wide enough to slip through
    # when the camera arrives, then drawn fully aside behind the camera
    f_open0 = p1a + 6
    f_open1 = p1b + 2
    S.animate_veil(hoh, [(1, 0.018), (int(f_open0), 0.03), (int(p1a + 0.65 * (p1b - p1a)), 0.085),
                         (int(p1b + 4), 0.13), (int(p2a + 20), 0.3), (int(p2b), 1.0)])
    _key_energy(vb, [(1, 450.0), (int(f_open0), 450.0), (int(f_open0 + 0.6 * (f_open1 - f_open0)), 0.0)])
    _key_energy(L["veil_front"], [(1, 15.0), (int(p1b + 10), 15.0), (int(p2a + 20), 0.0)])
    _key_energy(blade, [(1, 900.0), (int(f_open0 + 0.5 * (f_open1 - f_open0)), 700.0), (int(f_open1 + 20), 0.0)])
    # shadowed lights are the main render cost here: switch the slit light off once it has faded out
    for f, h in ((1, False), (int(f_open1 + 21), True)):
        blade.hide_render = h
        blade.keyframe_insert("hide_render", frame=f)
    # glory: swells through "Israel praises", then blooms to near-white (flash cut to s04a)
    f_end0 = p2b + 4
    S.set_glory(hoh, [(1, 0.8), (int(f_open0), 0.85), (int(f_open1), 1.15), (int(p2a), 1.2),
                      (int((p2a + p2b) / 2), 1.45), (int(f_end0), 1.6), (int(f_end0 + 0.45 * (n - f_end0)), 2.6),
                      (n, 9.0), (N, 9.0)])
    _key_energy(up, [(1, 4000.0), (int(p1b), 5000.0), (int(f_end0), 9000.0), (n, 30000.0)])
    gv = O.get("glory_volume")
    if gv:
        for f, sc in ((1, 1.0), (int(f_end0), 1.15), (n, 5.5)):
            gv.scale = (sc, sc, sc)
            gv.keyframe_insert("scale", frame=f)

    # the whiteout: a broad shadowless front light floods everything (wings included) in the last second
    wl = C.light("AREA", loc=(0.0, 0.6, 2.6), energy=0.0, temp=5000, target=tuple(glory), size=4.0, shadow=False,
                 name="whiteout")
    _key_energy(wl, [(1, 0.0), (int(f_end0 + 4), 0.0), (n, 2500.0)])
    _key_energy(wk, [(1, 260.0), (int(f_end0), 260.0), (n, 900.0)])

    # ================= camera =================
    # centred on the slit, gliding through the parting, a slight drift left inside for parallax, then
    # rising into the light. 28 mm, f/2.8, focus racks from the veil to the Ark as it opens.
    cam_keys = [
        (1, V(0.0, -3.1, 1.45)),
        (p1a + 24, V(0.0, -2.1, 1.5)),
        (p1b + 4, V(-0.1, 0.0, 1.62)),            # slipping through the parting
        (p2a + 15, V(-0.25, 0.35, 1.7)),
        (f_end0, V(-0.35, 0.9, 1.85)),
        (n, V(-0.15, 1.9, 2.7)),                  # rising into the light
    ]
    tgt_keys = [
        (1, V(0.0, 0.0, 2.1)),
        (p1a + 24, V(0.0, 4.5, 1.55)),
        (p1b + 4, V(0.0, 4.5, 1.3)),
        (p2a + 15, V(0.0, 4.5, 1.15)),
        (f_end0, V(0.0, 4.5, 1.15)),
        (n, V(0.0, 4.5, 1.75)),
    ]
    veil_pt = V(0.0, 0.0, 1.9)
    ark_pt = V(0.0, ark.y, 1.1)

    def focus_at(f, loc):
        k = C.smoothstep((f - f_open0) / max(1.0, (p1b - f_open0)))
        return max(0.5, (veil_pt.lerp(ark_pt, k) - loc).length)

    def path(f):
        loc = _hermite(cam_keys, f) + C.shake(f, 0.006, 0.5, 3)
        return loc, _hermite(tgt_keys, f), 0.0, 28, focus_at(f, loc)
    cam = C.camera(loc=tuple(cam_keys[0][1]), target=tuple(tgt_keys[0][1]), lens=28, fstop=2.8, focus=4.0)
    C.animate_camera(cam, path)

    # ================= render / post =================
    ctx.samples = 6
    ctx.render_opts = {"volumetrics": "low", "shadow_scale": 0.5}   # half-res shadow maps: same look, -0.5 s
    ctx.interp = True
    ctx.post.update({"grade": "gold", "temperature": 0.2, "bloom": 0.42, "vignette": 0.22,
                     "caption": {"halo": 1.2},
                     "end": {"bloom": 0.6}})
