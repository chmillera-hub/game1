"""s17b - Bread broken: "The poor will eat and be satisfied; / those who seek the Lord will praise him- /
may your hearts live forever!"

Close-up at a rough lamplit table. Hands in white sleeves (the risen Christ, as at Emmaus; his face stays
above the frame) hold a round flatbread and break it in two on the first phrase - steam curls up from the
torn crumb. On the second phrase he passes one half into the open palm of a young man (dark skin) reaching
in from the right, on the third the other half into the hands of an old woman from the left. Clay cup of wine
on the table, lamp flames as bokeh. Slow push in, f/2.
"""
import math
import bpy
from mathutils import Vector, Euler, noise
from lib import core as C
from lib import sets as S
from lib import characters as P

FLICK_SPEED = 2.2


def _rekey_flicker(ld, base, seed, amount=0.12, n=None):
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


def _cloth_mat(name="s17b_cloth"):
    """Cheap matte cloth (wardrobe dye from Object Info colour) with sheen - the garments are soft, out of focus."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = C.mat(name, (0.5, 0.45, 0.4), rough=0.88)
    nt = m.node_tree
    b = C.bsdf(m)
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    nt.links.new(oi.outputs["Color"], b.inputs["Base Color"])
    for k, v in (("Sheen Weight", 0.5), ("Sheen Roughness", 0.45)):
        if k in b.inputs:
            b.inputs[k].default_value = v
    return m


def _cheapen(p, hide_head=True):
    """Heads are above / outside the frame: hide hair, beard, veil; garments get one cheap cloth shader."""
    _hide_face(p)
    for k in ("hair", "hair_strands", "beard"):
        o = p.parts.get(k)
        if o is not None and hide_head:
            o.hide_render = True
    cm = _cloth_mat()
    for g in p.garments:
        if g.type != "MESH":
            continue
        if hide_head and ("veil" in g.name or "headcloth" in g.name):
            g.hide_render = True
            continue
        for slot in g.material_slots:
            slot.material = cm


def _two_hands_pose():
    """'s17b_hands': standing, leaning over the table, both palms at hand_targets (rig space), with per-side
    pronation / hand shape."""
    def fn(Pp, p, hand_targets=None, bend=12.0, pron=None, shape=None, curl=None, head="down", poles=None, **k):
        P._pose_stand(Pp, p, relaxed=True)
        P._spine_bend(Pp, bend=bend)
        pron = pron or {}
        shape = shape or {}
        curl = curl or {}
        poles = poles or {}
        for s in "LR":
            if not hand_targets or s not in hand_targets:
                continue
            lat = P._lateral(s)
            pole = Vector(poles.get(s, (lat.x * 1.0, 0.35, -1.0)))
            P._arm_ik(Pp, s, Vector(hand_targets[s]), pole=pole, pron=pron.get(s, 60.0), flex=0.0)
            P._hand(Pp, s, shape.get(s, "grip"), amount=curl.get(s, 1.0))
        P._apply_head(Pp, head)
    return fn


def build(ctx):
    N, R = ctx.nframes, ctx.render_frames
    last = R + (1 - R % 2)
    f1a, f1b = [int(round(v)) for v in ctx.phrase_frames(0)]
    f2a, f2b = [int(round(v)) for v in ctx.phrase_frames(1)]
    f3a, f3b = [int(round(v)) for v in ctx.phrase_frames(2)]
    st = S.table_interior(ctx, lamps=3, haze=False, steam=True, seed=31)
    TZ = st["table_top"].z
    bread = st.objects["bread"]
    # bring the loaf towards the host's side of the table (within reach), steam with it
    shift = Vector((0.0, 0.14, 0.0))
    bread.location += shift
    if st.objects.get("steam") is not None:
        st.objects["steam"].location += shift
    # the clay cup of wine into the frame, beside the loaf
    cup = st.objects.get("cup")
    if cup is not None:
        cup.location = Vector((0.25, 0.17, cup.location.z))
    bpy.context.view_layer.update()
    halves = {}
    for ch in list(bread.children):
        if ch.name.startswith("half_a") or ch.name.endswith("_half_a"):
            halves["a"] = ch
        elif ch.name.startswith("half_b") or ch.name.endswith("_half_b"):
            halves["b"] = ch
    for k, h in halves.items():
        mw = h.matrix_world.copy()
        h.parent = None
        h.matrix_world = mw
    B0 = bread.matrix_world.translation.copy()
    print("s17b: bread at", tuple(B0), {k: tuple(h.location) for k, h in halves.items()})
    if "s17b_hands" not in P.POSES:
        P.POSES["s17b_hands"] = _two_hands_pose()

    # ---------------- bread choreography (world positions of each half's origin, rot about its break axis) ----
    fb0, fb1 = f1a + 4, f1a + 40                       # break
    hb0, hb1, hb2 = f2a + 2, f2a + 36, f2b + 6         # half b -> right receiver (lift, carry, placed)
    ha0, ha1, ha2 = f3a - 6, f3a + 30, f3b + 8         # half a -> left receiver
    pa0, pb0 = halves["a"].location.copy(), halves["b"].location.copy()
    HR = Vector((B0.x + 0.14, B0.y - 0.11, TZ + 0.085))  # right receiver's palm (handoff point)
    HL = Vector((B0.x - 0.14, B0.y - 0.09, TZ + 0.08))   # left receiver's palm
    hand_off = Vector((0.0, 0.0, 0.028))

    def keyhalf(h, pairs):
        for f, loc, ry, rz in pairs:
            h.location = loc
            h.rotation_euler = Euler((0.0, math.radians(ry), math.radians(rz)), "XYZ")
            h.keyframe_insert("location", frame=f)
            h.keyframe_insert("rotation_euler", frame=f)
    up = Vector((0, 0, 1))
    keyhalf(halves["b"], [
        (1, pb0, 0, 0), (fb0, pb0, 0, 0),
        (fb0 + 18, pb0 + Vector((0.025, 0.0, 0.025)), -12, 3),
        (fb1, pb0 + Vector((0.045, 0.0, 0.04)), -18, 5),
        (hb0, pb0 + Vector((0.05, 0.0, 0.04)), -18, 5),
        (hb1, HR - Vector((0.045, -0.01, 0.0)) + hand_off + Vector((0, 0, 0.05)), -6, 18),
        (hb2, HR - Vector((0.045, -0.01, 0.0)) + hand_off, 0, 20),
        (R, HR - Vector((0.045, -0.01, 0.0)) + hand_off + Vector((0.015, -0.05, 0.015)), 0, 22),
    ])
    keyhalf(halves["a"], [
        (1, pa0, 0, 0), (fb0, pa0, 0, 0),
        (fb0 + 18, pa0 + Vector((-0.025, 0.0, 0.025)), 12, -3),
        (fb1, pa0 + Vector((-0.045, 0.0, 0.04)), 18, -5),
        (ha0, pa0 + Vector((-0.05, 0.0, 0.04)), 18, -5),
        (ha1, HL + Vector((0.045, 0.01, 0.0)) + hand_off + Vector((0, 0, 0.05)), 6, -18),
        (ha2, HL + Vector((0.045, 0.01, 0.0)) + hand_off, 0, -20),
        (R, HL + Vector((0.045, 0.01, 0.0)) + hand_off + Vector((-0.015, -0.03, 0.015)), 0, -22),
    ])

    def half_world(h, f):
        bpy.context.scene.frame_set(f)
        return h.matrix_world.copy()

    # ---------------- the breaker: white sleeves, hands on the outer rims of the halves ----------------
    P.AUTO_DRAPE = False
    j = P.make_person("s17b_host", "JESUS_RISEN", lod="mid", pose=None, hair_strands=False)
    j.rig.location = (B0.x + 0.02, 0.5, 0.0)
    _cheapen(j)
    grip_b = Vector((0.115, 0.01, 0.012))      # half-local palm points (outer rims)
    grip_a = Vector((-0.115, 0.01, 0.012))
    rest_L = Vector((B0.x + 0.26, B0.y + 0.2, TZ + 0.04))
    rest_R = Vector((B0.x - 0.26, B0.y + 0.2, TZ + 0.04))
    keys = sorted(set([1] + list(range(fb0 - 2, hb2 + 2, 4)) + list(range(ha0 - 4, ha2 + 2, 4)) + [hb2 + 20, ha2 + 20, R]))
    for f in keys:
        mb, ma = half_world(halves["b"], f), half_world(halves["a"], f)
        tL = mb @ grip_b
        tR = ma @ grip_a
        if f > hb2 + 4:                       # let go of half b, hand back to rest
            w = C.smoothstep(min(1.0, (f - hb2 - 4) / 16.0))
            tL = tL.lerp(rest_L, w)
        if f > ha2 + 4:
            w = C.smoothstep(min(1.0, (f - ha2 - 4) / 16.0))
            tR = tR.lerp(rest_R, w)
        bend = 30.0 + 3.0 * math.sin(min(1.0, max(0.0, (f - fb0) / 40.0)) * math.pi)
        P.key_pose(j, f, "s17b_hands", ground=False, hand_targets={"L": tL, "R": tR}, bend=bend,
                   pron={"L": 25.0, "R": 25.0}, shape={"L": "grip", "R": "grip"}, curl={"L": 0.7, "R": 0.7})

    # ---------------- receivers (out of frame but for their forearms and hands) ----------------
    recv = []
    for k, (name, preset, spec, loc, yaw, side, palm, fa, fz) in enumerate((
            ("s17b_youth", "CROWD_MAN", dict(seed=61, age_years=20, ethnicity="african", skin_tone=0.92, beard="none",
                                             outfit=["tunic"], outfit_colors={"tunic": "oatmeal"},
                                             outfit_opts={"tunic": {"sleeves": "elbow"}}),
             (0.5, -0.4, 0.0), 180 + 44, "R", HR, hb0 - 18, hb1 - 6),
            ("s17b_widow", "CROWD_WOMAN", dict(seed=62, age_years=72, skin_tone=0.25, outfit=["tunic", "veil"],
                                               outfit_colors={"tunic": "umber", "veil": "blue_grey"},
                                               outfit_opts={"tunic": {"sleeves": "3q"}}),
             (-0.46, -0.42, 0.0), 180 - 38, "L", HL, ha0 - 20, ha1 - 6))):
        pr = P.make_person(name, preset, lod="mid", pose=None, hair_strands=False, **spec)
        pr.rig.location = loc
        pr.rig.rotation_euler.z = math.radians(yaw)
        _cheapen(pr)
        s = side
        o = "L" if s == "R" else "R"
        rest = Vector(loc) + Vector((0.0, 0.0, 0.85))
        out = Vector(loc).lerp(palm, 0.42)
        out.y, out.z = -0.34, TZ + 0.035          # resting on the table edge before reaching in
        ht0 = {s: out}
        prn = {s: -20.0 if s == "L" else 70.0}
        shp = {s: "cup"}
        P.key_pose(pr, 1, "s17b_hands", ground=False, hand_targets=ht0, bend=4, pron=prn, shape=shp, head="down")
        P.key_pose(pr, fa, "s17b_hands", ground=False, hand_targets=ht0, bend=4, pron=prn, shape=shp, head="down")
        P.key_pose(pr, fz, "s17b_hands", ground=False, hand_targets={s: palm}, bend=24, pron=prn, shape=shp,
                   head="down")
        hold = (hb2 if s == "R" else ha2)
        P.key_pose(pr, hold, "s17b_hands", ground=False, hand_targets={s: palm - Vector((0, 0, 0.004))}, bend=24,
                   pron=prn, shape=shp, head="down")
        drift = Vector((0.015, -0.05, 0.015)) if s == "R" else Vector((-0.015, -0.03, 0.015))
        P.key_pose(pr, R, "s17b_hands", ground=False, hand_targets={s: palm + drift}, bend=22, pron=prn,
                   shape={s: "cup"}, curl={s: 0.85}, head="down")
        recv.append(pr)

    # ---------------- light: flicker on odd frames; a soft warm key from the table lamp side ----------------
    for name, lo in st.lights.items():
        if lo is None or lo.type != "LIGHT":
            continue
        if lo.data.animation_data and lo.data.animation_data.action:
            _rekey_flicker(lo.data, lo.data.energy, seed=abs(hash(name)) % 89, n=R)
    _rekey_flames(R)
    rim = C.light("AREA", loc=(B0.x - 0.3, B0.y + 0.9, TZ + 0.75), energy=6.0, color=C.kelvin(2300),
                  target=(B0.x, B0.y - 0.1, TZ + 0.05), size=0.5, name="s17b_rim", shadow=False)
    rim.data.volume_factor = 1.0

    # ---------------- camera: low three-quarter on the bread, slow push ----------------
    tgt0 = Vector((B0.x + 0.0, B0.y - 0.02, TZ + 0.04))
    cam = C.camera((0.1, -0.66, TZ + 0.84), tgt0, lens=36, fstop=2.0, focus=1.0)

    def cfn(f):
        u = C.ease_in_out(min(1.0, max(0.0, (f - 1) / (R - 1))))
        loc = Vector((0.1 - 0.03 * u, -0.66 + 0.1 * u, TZ + 0.84 - 0.08 * u))
        loc += Vector((0.0015 * math.sin(f * 0.031), 0, 0.001 * math.sin(f * 0.043 + 1)))
        tgt = tgt0 + Vector((0.0, -0.02 * u, 0.01 * u))
        return loc, tgt, 0.0, None, (tgt - loc).length
    C.animate_camera(cam, cfn, 1, last, step=2)
    bpy.context.scene.frame_set(1)

    ctx.samples = 4
    ctx.render_opts = {"volumetrics": "low"}
    ctx.interp = True
    win = st.lights.get("window")
    if win is not None:
        win.data.energy *= 2.5
    ctx.post = {"grade": "warm", "saturation": 0.88, "bloom": 0.3, "halation": 0.08, "vignette": 0.26,
                "caption": {"ink": "light", "halo": 1.2}}
