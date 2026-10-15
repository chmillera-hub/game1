"""s10a - Poured out like water: "I am poured out like water, and all my bones are out of joint."

Two setups in one shot, hard cut on the second phrase (both under the darkened eclipse sky):
  A (phrase 1)  slow motion (0.35x): water pours from the spout of a tilted earthen pitcher onto parched,
                cracked ground, splashes and soaks away into the cracks (the wet patch darkens and
                spreads; plates dry again while the cracks stay wet). Low camera looking towards the
                dull sun; light-linked strip lights give the stream its liquid edge highlights.
  B (phrase 2)  from just in front of the crucified figure's right shoulder, looking up and out along the
                stretched arm to the clenched hand at the end of the crossbeam, silhouetted against the
                dim red-brown sky with the darkened sun beside it; slow push, rack focus shoulder -> hand,
                fingers slowly tightening. No face in frame.
Setup A lives 30 m east of the cross; each setup is hidden (keyed hide_render) while the other is on
screen, and one camera jumps between them at the cut.
Render: 12 fps + RIFE (ctx.interp) with the splash window and the frame before the cut kept at full
rate via ctx.interp_keep (honoured by render_shot.py in odd/auto mode).
"""
import math
import bpy
import numpy as np
from mathutils import Vector, Matrix
from lib import core as C
from lib import fx as FX
from lib import env as E
from lib import assets as A
from lib import characters as P

SUN_AZ = 245.0        # dull eclipse sun behind the figure's right hand (seen from the shoulder in setup B)
SUN_EL = 36.0         # raised from the preset's 24 so the disk sits beside the hand in the upward view
SUN_E = 0.8           # eclipse preset is 0.35; a bit more so rims and water glints read
OA = Vector((30.0, 0.0, 0.0))   # setup A origin (ground level)
LOD = "mid"           # person LOD for the arm close-up


def _hide_keys(objs, visible_from=None, hidden_from=None):
    """Key hide_render (constant) so objs render only inside [visible_from, hidden_from)."""
    seen = set()
    allo = []
    for o in objs:
        for x in [o] + list(o.children_recursive):
            if x.name not in seen:
                seen.add(x.name)
                allo.append(x)
    for o in allo:
        if visible_from is not None:
            o.hide_render = True
            o.keyframe_insert("hide_render", frame=1)
            o.hide_render = False
            o.keyframe_insert("hide_render", frame=visible_from)
        if hidden_from is not None:
            o.hide_render = False
            o.keyframe_insert("hide_render", frame=1 if visible_from is None else visible_from)
            o.hide_render = True
            o.keyframe_insert("hide_render", frame=hidden_from)
    return allo


def _fall_time(h, vz_down):
    """Seconds for water leaving the lip with downward speed vz_down to fall h metres."""
    return (vz_down + math.sqrt(vz_down * vz_down + 19.62 * h)) / 9.81


def _lean_material(m):
    for nd in m.node_tree.nodes:
        if nd.type == "TEX_IMAGE" and nd.projection == "BOX":
            nd.projection = "FLAT"
        elif nd.type == "TEX_NOISE":
            nd.inputs["Detail"].default_value = min(nd.inputs["Detail"].default_value, 1.0)


def build(ctx):
    NR = ctx.render_frames
    p0, p1 = ctx.phrases[0], ctx.phrases[1]
    CUT = int(ctx.frame(p1["start"]))            # first frame of setup B (~2.7 s, on "and all my bones")

    # ------------------------------------------------------------------ sky / sun (eclipse, shared)
    sd = dict(E.SKY_PRESETS["eclipse"]["sun_disk"])
    sd["el"] = SUN_EL
    sky = E.sky("eclipse", ctx=ctx, sun_az=SUN_AZ, sun_el=SUN_EL, sun_disk=sd)
    sun = sky["sun"]
    sun.data.energy = SUN_E
    sdir = Vector(sky["sun_dir"])

    # ================================================================== SETUP A: the pour
    # camera looks 22 deg off the sun (back-side light): rim on the stream and sheen on the wet crust, but the
    # sun's mirror image in the flat water film stays out of frame (it read as an orange blob)
    vh = Matrix.Rotation(math.radians(22), 3, "Z") @ Vector((sdir.x, sdir.y, 0)).normalized()
    right = Vector((vh.y, -vh.x, 0))                        # screen right
    d = right                                               # water flows to screen right
    lip_h = 0.45
    L = OA + Vector((0, 0, lip_h)) - d * 0.08
    f_start, f_end = -8, 27                                  # pour (effect frames); stream already falling at f1
    # hero cracked-earth patch (bigger than the FX default so the frame never sees its edge in focus)
    gp = FX.cracked_ground((L.x + d.x * 0.12, L.y + d.y * 0.12, OA.z), size=3.6, res=330, seed=1, name="Cracked")
    # clear, neutral water (FX default is faintly blue; reads as grey plastic in this warm light)
    FX.water_material("FX_water_1", rough=0.015, tint=(1.0, 1.0, 1.0), raytrace=True)
    pour = FX.water_pour(lip=tuple(L), direction=(d.x, d.y), speed=0.38, stream_radius=0.014,
                         start_frame=f_start, end_frame=f_end, time_scale=0.35, ground_z=OA.z, jar=False,
                         ground=None, ground_material=gp.active_material, puddle_radius=0.26, drain_time=0.5,
                         seed=1, name="Pour")
    imp = Vector(pour.impact)
    # the FX water film is mostly hidden under the curled plates here, mirrors the sun as a blob and costs
    # ~40% of the frame (blended 4D-noise ripples): the wet-patch in the ground material carries the look
    if getattr(pour, "puddle", None) is not None:
        bpy.data.objects.remove(pour.puddle, do_unlink=True)
        pour.puddle = None
    # surrounding parched ground (below the crack grooves of the hero patch), darker so it doesn't glow
    far_m = C.mat_pbr("brown_mud_dry", scale=1.0 / 0.48, tint=(0.6, 0.5, 0.42), rough_add=0.5, name="s10a_mud")
    far = C.ground_plane(size=40, mat_=far_m, z=OA.z - 0.03, name="MudFar")
    far.location.x, far.location.y = OA.x, OA.y

    # camera A: low, looking towards the sun, down onto the impact, stream in profile
    a_tgt0 = imp.lerp(L, 0.42) - right * 0.03 - Vector((0, 0, 0.03))
    pitch = math.radians(24)

    def camA(f):
        u = C.ease_in_out((f - 1) / float(CUT - 1))
        tgt = a_tgt0 + Vector((0, 0, -0.09 * u))
        dist = 1.12 - 0.06 * u
        loc = tgt + (-vh * math.cos(pitch) + Vector((0, 0, math.sin(pitch)))) * dist - right * (0.02 + 0.04 * u)
        loc = loc + C.shake(f, 0.002, 0.5, 11)
        foc = (imp.lerp(L, 0.3) - loc).length
        return (loc, tgt, 0.0, 45, foc)

    # earthen pitcher: spout at the lip, body tilted towards the pour direction (held off-screen).
    # NB assets water_jar v1: the spout pinch is at root +X but the handle comes out at -Y (and the
    # 'mouth' anchor sits over the handle) -> put the handle back opposite the spout, pour from +X.
    jar = A.load("water_jar", variant=1)
    clay = A.mat_clay("terracotta")
    jar_meshes = []
    for o in A.children_recursive(jar):
        if o.type == "MESH":
            o.data.materials.clear()
            o.data.materials.append(clay)
            jar_meshes.append(o)
            if o.name.startswith("handle"):
                o.rotation_euler.z = 0.0
    spout = Vector((0.064, 0.0, 0.305))
    piv = bpy.data.objects.new("JarPivot", None)
    C.link(piv)
    jar.parent = piv
    jar.location = -spout
    jar.rotation_euler = (0, 0, 0)
    yaw = math.atan2(d.y, d.x)
    axis = Vector((0, 0, 1)).cross(d).normalized()

    def jar_rot(f):
        u = C.smoothstep((f - (f_start - 10)) / float(CUT - (f_start - 10)))
        tilt = math.radians(78 + 26 * u)
        return (Matrix.Rotation(tilt, 3, axis) @ Matrix.Rotation(yaw, 3, "Z")).to_euler()
    piv.location = L
    C.key_fn(piv, "rotation_euler", jar_rot, 1, CUT, step=2)
    # glint lights (light-linked to the water only): two low soft strips at the front-left / front-right.
    # Seen from above, a near-vertical stream mirrors the ground below it, so with only the dull sun it
    # reads as a dark rod; low strips give it the two bright edge highlights of a liquid and sparkle on
    # the splash beads.
    wrecv = bpy.data.collections.new("s10a_water_recv")
    for k in ("stream", "droplets", "puddle"):
        o = getattr(pour, k, None)
        if o is not None:
            wrecv.objects.link(o)
    mid = imp.lerp(L, 0.45)
    glints = []
    for side, e, k in ((-1, 220, 4600), (1, 110, 3600)):
        wl = C.light("AREA", tuple(imp + right * (0.55 * side) - vh * 0.55 + Vector((0, 0, 0.06))), e, temp=k,
                     target=tuple(mid), size=0.6, name="WaterGlint%d" % (side + 1), shadow=False)
        wl.data.shape = "RECTANGLE"
        wl.data.size, wl.data.size_y = 0.12, 0.9
        wl.light_linking.receiver_collection = wrecv
        glints.append(wl)

    # smoother stream (the default bead ripple reads as a dashed rod at this size)
    FX._mod_set(pour.stream.modifiers["Stream"], Ripple=0.09)
    # a fuller splash crown at the impact (the FX splash is fine spray only)
    ts = 0.35
    T_hit = _fall_time(L.z - OA.z, 0.15)
    T_stop = (f_end - f_start) / 24.0 * ts
    rng = np.random.default_rng(5)
    n = 300
    birth = np.where(rng.random(n) < 0.35, T_hit + rng.uniform(0.0, 0.06, n), rng.uniform(T_hit, T_hit + T_stop, n))
    ang = rng.uniform(0, 2 * math.pi, n)
    up = rng.uniform(0.5, 1.7, n)
    out = rng.uniform(0.25, 1.1, n)
    p0, v0 = [], []
    for a, u_, o_ in zip(ang, up, out):
        rr = Vector((math.cos(a), math.sin(a), 0))
        p0.append(tuple(imp + rr * rng.uniform(0.004, 0.018) + Vector((0, 0, 0.004))))
        v0.append(tuple(rr * o_ + Vector((0, 0, u_)) + d * 0.3))
    crown, _ = FX._particles("PourCrown", np.array(p0), np.array(v0), birth, np.full(n, 1.0),
                             rng.uniform(0.0012, 0.0034, n), bpy.data.materials["FX_water_1"], frame0=f_start,
                             time_scale=ts, gravity=(0, 0, -9.81), drag=0.05, floor=OA.z, floor_mode=2, fade_in=0.0,
                             fade_out=0.0, mode=2, stretch=0.0025,
                             instance=FX._cached_src("FX_src_ico", lambda: FX._ico("FX_src_ico", 1)), seed=6)
    wrecv.objects.link(crown)
    # less glitter on the wet crust: halve the normal-map relief of the cracked-ground texture
    for nd in gp.active_material.node_tree.nodes:
        if nd.type == "NORMAL_MAP":
            nd.inputs["Strength"].default_value *= 0.5
    # render cost (llvmpipe): the ground fills the frame; top-down texture projection instead of
    # 3-way box mapping and 1-octave procedural noise cut its per-pixel cost a lot (looks the same here)
    for m in (gp.active_material, far_m):
        _lean_material(m)
    sun.data.angle = math.radians(6.0)    # hazy eclipse sun: broader, softer highlights

    # soft warm fill on the jar from camera-left so the clay reads (it is backlit by the sun)
    jf = C.light("AREA", tuple(L - right * 0.7 - vh * 0.6 + Vector((0, 0, 0.35))), 3.0, temp=3200,
                 target=tuple(L), size=0.8, name="JarFill", shadow=False)
    jrecv = bpy.data.collections.new("s10a_jar_recv")
    for o in jar_meshes:
        jrecv.objects.link(o)
    jf.light_linking.receiver_collection = jrecv
    setA = [pour.root, far, piv, gp, jf, crown] + glints
    for k in ("stream", "droplets", "puddle", "ground"):
        o = getattr(pour, k, None)
        if o is not None:
            setA.append(o)

    # ================================================================== SETUP B: the arm on the cross
    cm = C.wood_material("rough_wood", scale=1.2, tint=(0.62, 0.52, 0.42))
    cross = C.wooden_cross(loc=(0, 0, -0.45), height=4.85, material=cm, name="Cross")
    # only the right arm/shoulder is ever in frame: no beard/hair strands/crown (off camera), and the
    # head parts are hidden below (render cost: the person was ~6 s of a 15 s frame)
    j = P.make_person("jesus", "JESUS_CROSS", pose=None, hair_strands=False, beard="none", outfit=["loincloth"],
                      lod=LOD)
    cont = P.place_on_cross(j, cross, head="down", strain=0.8)
    P.expression(j, "exhausted")
    j.update()
    sh = Vector(j.bone_world("upperarm01.R"))
    hand = Vector(cont["hand_R"])
    elbow = Vector(j.bone_world("lowerarm01.R"))
    # fingers slowly tighten on "out of joint"
    fA, fB = CUT, NR
    for i in range(1, 6):
        for k in (1, 2, 3):
            bn = "finger%d-%d.R" % (i, k)
            if bn not in j.rig.pose.bones:
                continue
            pb = j.rig.pose.bones[bn]
            # the 'cross' hand leaves thumb + index nearly straight: from this POV it reads as pointing
            if i == 2:
                P.rotate_bone(j, bn, ((34, 44, 28)[k - 1], 0, 0), mode="ADD")
            elif i == 1:
                P.rotate_bone(j, bn, ((30, 30, 20)[k - 1], 0, 0), mode="ADD")
            q0 = pb.rotation_quaternion.copy()
            pb.keyframe_insert("rotation_quaternion", frame=fA)
            amt = (10, 16, 12)[k - 1] if i > 1 else (4, 6, 6)[k - 1]
            P.rotate_bone(j, bn, (amt, 0, 0), frame=fB, mode="ADD")
            pb.rotation_quaternion = q0
    for key in ("eyes", "eyebrows", "eyelashes", "teeth", "tongue", "hair"):
        o = j.parts.get(key)
        if o is not None:
            o.hide_render = True
    setB = [cross] + [o for o in j.objects() if not o.hide_render]

    # visibility per setup
    _hide_keys(setA, hidden_from=CUT)
    _hide_keys(setB, visible_from=CUT)

    # ================================================================== camera
    cam = C.camera((0, -1, 1), (0, 0, 1), lens=50, fstop=2.8, name="Cam")
    # B: from just in front of the right shoulder/chest, looking up and out along the stretched arm to
    # the hand at the end of the beam, the darkened sun glowing beside it. Slow push towards the hand and a
    # rack focus from the shoulder (near) to the hand on "out of joint".
    def camB(f):
        u = C.ease_in_out((f - CUT) / float(NR - CUT))
        loc = sh + Vector((0.12, -0.31, -0.33)).lerp(Vector((0.07, -0.27, -0.27)), u)
        tgt = hand.lerp(elbow, 0.12) + Vector((0, 0, -0.02))
        loc = loc + C.shake(f, 0.0012, 0.4, 5)
        r = C.smoothstep((f - CUT - 6) / 40.0)
        foc = (sh.lerp(elbow, 0.35) - loc).length * (1 - r) + (hand - loc).length * r
        return (loc, tgt, -4.0 + 2.0 * u, 32, foc)

    C.animate_camera(cam, lambda f: camA(f) if f < CUT else camB(f), 1, NR)
    cam.data.dof.aperture_fstop = 2.8
    cam.data.dof.keyframe_insert("aperture_fstop", frame=1)
    cam.data.dof.aperture_fstop = 4.0
    cam.data.dof.keyframe_insert("aperture_fstop", frame=CUT)
    C._set_interp(cam.data, "aperture_fstop", "CONSTANT")
    # the cut must not interpolate the camera between the setups
    for fc in C._fcurves(cam.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT"
    if cam.data.animation_data and cam.data.animation_data.action:
        for fc in C._fcurves(cam.data.animation_data.action):
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"

    ctx.samples = 4
    ctx.render_opts.update({"raytracing": False, "volumetrics": "low", "shadow_scale": 0.5})
    # 12 fps + RIFE: slow-motion stream / slow camera moves. The hard cut can't be bridged by RIFE, so the
    # even frame beside it is rendered too (render_shot.py honours ctx.interp_keep in odd/auto mode).
    ctx.interp = True
    # the splash crown's small droplets twinkle when synthesised: keep the splash window at 24 fps too
    f_hit = int(f_start + T_hit / ts * 24)
    f_last = min(CUT - 1, int(f_end + T_hit / ts * 24) + 2)
    ctx.interp_keep = sorted(set([f for f in range(f_hit, f_last + 1) if f % 2 == 0] + [CUT - 1 if CUT % 2 else CUT]))
    ctx.post.update({"grade": "eclipse", "caption": {"y": 0.74}})
