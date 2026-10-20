"""s17a - Great assembly: "From you comes the theme of my praise in the great assembly; / before those who
fear you I will fulfill my vows."

Dusk in a stone courtyard. We begin low behind two worshippers holding oil lamps (dark silhouettes, backs
to us); on the first phrase the nearer one lifts the lamp high. The camera cranes up over their heads and
glides forward over the assembly: people stand still among hundreds of small lamp flames set on the
flagstones, the steps and the colonnade ledges, all facing the lamplit portico - seen only from behind as
dark shapes against the glow (no faces). On the second phrase the other worshipper raises his lamp too.
"""
import math
import random
import bpy
from mathutils import Vector, noise
from lib import core as C
from lib import sets as S
from lib import characters as P

FLICK_SPEED = 2.2


# ------------------------------------------------------------------ flicker (interp-friendly, odd frames)
def _rekey_flicker(ld, base, seed, amount=0.14, n=None):
    if ld.animation_data:
        ld.animation_data_clear()
    n = n or bpy.context.scene.frame_end

    def fn(f):
        t = f / 24.0 * FLICK_SPEED
        v = noise.noise(Vector((t, seed * 3.1, 0.5))) * 0.75 + noise.noise(Vector((t * 2.1, seed, 4.2))) * 0.25
        return base * max(0.3, 1.0 + amount * 2.0 * v)
    C.key_fn(ld, "energy", fn, 1, n + (1 - n % 2), step=2)
    if ld.animation_data and ld.animation_data.action:
        for fc in C._fcurves(ld.animation_data.action):
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"


def _rekey_flames(n):
    """Flame shader noise 'time': slower, linear (smooth under 12 fps + RIFE)."""
    last = n + (1 - n % 2)
    for m in bpy.data.materials:
        if not m.use_nodes or m.node_tree is None:
            continue
        tv = m.node_tree.nodes.get("time")
        if tv is None or tv.type != "VALUE":
            continue
        nt = m.node_tree
        if nt.animation_data:
            nt.animation_data_clear()
        sock = tv.outputs[0]
        for f in (1, last):
            sock.default_value = (f - 1) / 24.0 * FLICK_SPEED
            sock.keyframe_insert("default_value", frame=f)
        if nt.animation_data and nt.animation_data.action:
            for fc in C._fcurves(nt.animation_data.action):
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"


def _hide_face(p):
    for k in ("eyes", "eyebrows", "eyelashes", "teeth", "tongue", "mouth"):
        o = p.parts.get(k)
        if o is not None:
            o.hide_render = True


def _silhouette_mat(name="s17_silhouette", dim=0.07):
    """One cheap shader for the distant assembly: clothing colour (baked obj_rgb attribute) darkened, matte,
    a little sheen so the lamp glow rims the shoulders. Skin parts (no obj_rgb) come out a dark umber."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = C.mat(name, (0.05, 0.035, 0.025), rough=0.85)
    nt = m.node_tree
    b = C.bsdf(m)
    at = nt.nodes.new("ShaderNodeAttribute")
    at.attribute_name = "obj_rgb"
    mx = nt.nodes.new("ShaderNodeMix")
    mx.data_type = "RGBA"
    mx.blend_type = "MULTIPLY"
    mx.inputs["Factor"].default_value = 1.0
    nt.links.new(at.outputs["Color"], mx.inputs[6])
    mx.inputs[7].default_value = (dim, dim * 0.92, dim * 0.85, 1.0)
    add = nt.nodes.new("ShaderNodeMix")
    add.data_type = "RGBA"
    add.blend_type = "ADD"
    add.inputs["Factor"].default_value = 1.0
    nt.links.new(mx.outputs[2], add.inputs[6])
    add.inputs[7].default_value = (0.006, 0.004, 0.003, 1.0)
    nt.links.new(add.outputs[2], b.inputs["Base Color"])
    for k, v in (("Sheen Weight", 0.12), ("Sheen Roughness", 0.35)):
        if k in b.inputs:
            b.inputs[k].default_value = v
    return m


def _skin_mat(name="s17_skin"):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = C.mat(name, (0.36, 0.2, 0.13), rough=0.55)
    b = C.bsdf(m)
    if "Subsurface Weight" in b.inputs:
        b.inputs["Subsurface Weight"].default_value = 0.0
    return m


def _hair_mat(name="s17_hair"):
    m = bpy.data.materials.get(name)
    if m:
        return m
    return C.mat(name, (0.018, 0.013, 0.01), rough=0.65)


def _cloth_mat(name="s17_cloth", dim=0.35):
    """Cheap cloth for the live foreground people: wardrobe dye from Object Info colour, matte + sheen."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = C.mat(name, (0.1, 0.07, 0.05), rough=0.9)
    nt = m.node_tree
    b = C.bsdf(m)
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    mx = nt.nodes.new("ShaderNodeMix")
    mx.data_type = "RGBA"
    mx.blend_type = "MULTIPLY"
    mx.inputs["Factor"].default_value = 1.0
    nt.links.new(oi.outputs["Color"], mx.inputs[6])
    mx.inputs[7].default_value = (dim, dim, dim, 1.0)
    nt.links.new(mx.outputs[2], b.inputs["Base Color"])
    for k, v in (("Sheen Weight", 0.4), ("Sheen Roughness", 0.4)):
        if k in b.inputs:
            b.inputs[k].default_value = v
    return m


def _simplify_people(objs, mat_fn):
    """Swap every material of these objects for cheap opaque ones (mat_fn(material_name) -> material)."""
    for o in objs:
        if o.type == "CURVES":
            o.hide_render = True
            continue
        if o.type != "MESH":
            continue
        for slot in o.material_slots:
            slot.material = mat_fn(slot.material.name if slot.material else "")
        for i in range(len(o.data.materials)):
            mm = o.data.materials[i]
            o.data.materials[i] = mat_fn(mm.name if mm else "")


def _simplify_crowd(cr):
    sil = _silhouette_mat()
    seen = set()
    objs = list(cr.collection.all_objects) if cr.collection else []
    for o in objs:
        if o.type == "CURVES":
            o.hide_render = True
            continue
        if o.type != "MESH":
            continue
        for slot in o.material_slots:
            if slot.link == "OBJECT":
                slot.material = sil
        if o.data.name in seen:
            continue
        seen.add(o.data.name)
        for i in range(len(o.data.materials)):
            o.data.materials[i] = sil


def build(ctx):
    import os
    DBG = os.environ.get("S17_DBG", "")
    N, R = ctx.nframes, ctx.render_frames
    f1a, f1b = ctx.phrase_frames(0)
    f2a, f2b = ctx.phrase_frames(1)
    st = S.courtyard_assembly(ctx, lamps=700, stands=6, seed=21, glow=0.45)
    before = set(bpy.context.scene.objects)
    rnd = random.Random(17)

    # ---------------- the assembly: still, dark figures among the lamps (far LOD, baked) ----------------
    P.AUTO_DRAPE = False
    spots = [(Vector(p), yw) for p, yw in st.extra["crowd_spots"]]
    pos = []
    for p, yw in spots:
        if p.y < 1.2 or p.y > 12.6:
            continue
        if rnd.random() < 0.42:
            pos.append((p.x + rnd.uniform(-0.15, 0.15), p.y, 0.0))
    poses = ["stand_relaxed", ("stand", {"head": "up"}), "mourn", ("arms_raised", {"spread": 22, "head": "up"}),
             "stand_relaxed", ("stand", {"head": "bowed"})]
    cr = P.crowd(len(pos), positions=pos, seed=5, variety=5, lod="far", pose=poses, face=(0, 24, 1.6),
                 yaw_jitter=8, ground_z=0.0, name="s17_assembly")
    _simplify_crowd(cr)
    sil = _silhouette_mat()
    _simplify_people([o for o in bpy.context.scene.objects if o not in before and o.type in ("MESH", "CURVES")],
                     lambda n: sil)
    print("s17a: assembly of %d" % len(pos))
    # tone the set's broad fills down: the lamps (and their cluster lights) should carry the light
    for k, s_ in (("crowd_glow", 0.0), ("crowd_key", 0.1), ("wall_glow_L", 0.5), ("wall_glow_R", 0.5)):
        lo = st.lights.get(k)
        if lo is not None:
            lo.data.energy *= s_
    # more lamps set down on the flagstones between the people (each worshipper brought one)
    floor = []
    occupied = [(x, y) for x, y, _ in pos]
    tries = 0
    while len(floor) < 380 and tries < 8000:
        tries += 1
        x, y = rnd.uniform(-6.2, 6.2), rnd.uniform(-1.5, 14.8)
        if abs(x) < 0.45 or any((x - a) ** 2 + (y - b) ** 2 < 0.3 ** 2 for a, b in occupied):
            continue
        floor.append((x, y, 0.0, rnd.uniform(0, 360)))
    st.extra["add_lamps"](floor, name="s17_floor_lamps")
    # the gate of the portico stands open on a lamplit hall: the bright source the assembly is silhouetted against
    gate = bpy.data.objects.get("court_gate")
    if gate is not None:
        gm = C.mat_emission("s17_gate_glow", C.kelvin(1900), 4.5)
        gate.data.materials.clear()
        gate.data.materials.append(gm)
    pz = st["portico"]
    hall = C.light("AREA", loc=(0.0, pz.y + 1.0, pz.z + 2.6), energy=900.0, color=C.kelvin(2100),
                   target=(0.0, 6.0, 0.8), size=3.0, name="s17_hall_glow", shadow=False)
    hall.data.volume_factor = 0.6

    # ---------------- two worshippers in the foreground (backs to camera) ----------------
    front = []
    for k, (x, y, pre, sd, cols, extra) in enumerate((
            (-0.62, -0.75, "CROWD_MAN", 41, {"tunic": "umber", "mantle": "dark_brown"}, dict(age_years=36, beard="full")),
            (0.95, 0.7, "CROWD_MAN", 44, {"tunic": "brown", "mantle": "charcoal"}, dict(age_years=58)))):
        pr = P.make_person("s17_front%d" % k, pre, seed=sd, lod="mid", pose=None, hair_strands=False,
                           outfit_colors=cols, **extra)
        pr.rig.location = (x, y, 0.0)
        pr.rig.rotation_euler.z = math.radians(180 + (-6 if k == 0 else 8))
        _hide_face(pr)
        skin, cloth = _skin_mat(), _cloth_mat()
        _simplify_people([o for o in pr.objects()],
                         lambda n: skin if "skin" in n.lower() else (_hair_mat() if ("hair" in n.lower() or "brow" in n.lower())
                                                                     else cloth))
        front.append(pr)
    # lamp poses: held at the chest, then lifted high (phrase 1 for the near man, phrase 2 for the other)
    lifts = ((front[0], "R", f1a + 6, 52), (front[1], "L", f2a + 4, 50))
    lamps = []
    for k, (pr, side, fa, dur) in enumerate(lifts):
        bpy.context.view_layer.update()
        sx = -1 if side == "R" else 1           # character's right = -X in rig space; rig turned 180 deg
        base = pr.rig.location
        fwd = Vector((0, 1, 0))                 # the worshippers face +Y
        lat = Vector((-sx, 0, 0))               # world lateral offset of the lamp hand
        yaw = pr.rig.rotation_euler.z - math.pi
        rot = lambda v: Vector((v.x * math.cos(yaw) - v.y * math.sin(yaw), v.x * math.sin(yaw) + v.y * math.cos(yaw), v.z))
        low = base + rot(fwd * 0.30 + lat * 0.24) + Vector((0, 0, pr.height * 0.64))
        high = base + rot(fwd * 0.22 + lat * 0.3) + Vector((0, 0, pr.height * 1.1))
        P.key_pose(pr, 1, "reach", target=low, side=side, hand="cup")
        P.key_pose(pr, fa, "reach", target=low, side=side, hand="cup")
        P.key_pose(pr, fa + int(dur * 0.6), "reach", target=low.lerp(high, 0.8) + Vector((0, 0.04, 0)), side=side,
                   hand="cup")
        P.key_pose(pr, fa + dur, "reach", target=high, side=side, hand="cup")
        lamp, flame, lo = S.oil_lamp((0, 0, 0), rot_z=90, energy=14.0, seed=31 + k, shadow=False,
                                     name="s17_handlamp%d" % k)
        lamps.append((pr, side, lamp, lo))
    # lamp follows the palm (keyed on odd frames, linear)
    sc = bpy.context.scene
    last = R + (1 - R % 2)
    for f in range(1, last + 1, 2):
        sc.frame_set(f)
        for pr, side, lamp, lo in lamps:
            hp = pr.hand_pos(side)
            lamp.location = hp + Vector((0, 0.0, 0.035))
            lamp.keyframe_insert("location", frame=f)
    for pr, side, lamp, lo in lamps:
        C._set_interp(lamp, "location", "LINEAR")
        if lo is not None:
            _rekey_flicker(lo.data, lo.data.energy, seed=hash(lamp.name) % 97, amount=0.12, n=R)
    sc.frame_set(1)

    # set flicker -> odd frames / slower flame noise
    for name, lo in st.lights.items():
        if name.startswith("stand") and lo is not None:
            _rekey_flicker(lo.data, lo.data.energy, seed=int(name[5:] or 0) + 7, amount=0.16, n=R)
    _rekey_flames(R)

    if "nocrowd" in DBG:
        for o in cr.collection.all_objects:
            o.hide_render = True
    if "nofront" in DBG:
        for pr in front:
            for o in pr.objects():
                o.hide_render = True
    # ---------------- camera: crane up over the worshippers, glide forward over the lamps ----------------
    cam = C.camera((0.25, -3.9, 1.45), (0.0, 12.0, 1.6), lens=30, fstop=4.0, focus=4.0)

    def cfn(f):
        u = C.ease_in_out(min(1.0, max(0.0, (f - 1) / (R - 1))))
        ur = C.smoothstep(min(1.0, max(0.0, (f - 10) / (R - 60))))
        loc = Vector((0.15 - 0.15 * u, -3.7 + 5.9 * u, 1.4 + 2.8 * ur))
        tgt = Vector((0.0, 12.0 + 2.5 * u, 1.2 - 1.3 * ur))
        foc = 3.4 + 6.5 * ur
        return loc, tgt, 0.0, None, foc
    C.animate_camera(cam, cfn, 1, last, step=2)

    ctx.samples = 4
    ctx.render_opts = {"volumetrics": "low", "shadow_scale": 0.5}
    ctx.interp = True
    ctx.post = {"grade": "candle", "bloom": 0.38, "bloom_radius": 1.2, "halation": 0.1, "vignette": 0.24,
                "caption": {"ink": "light", "halo": 1.2}}
