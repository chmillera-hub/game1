"""s10a - Poured out like water: "I am poured out like water, and all my bones are out of joint."

Two setups in one shot, hard cut on the second phrase (both under the darkened eclipse sky):
  A (phrase 1)  slow motion: water pours from the spout of a tilted earthen jar onto parched, cracked
                ground, splashes, spreads, and sinks away into the cracks. Low, backlit by the dull sun
                so the stream, beads and splash glint.
  B (phrase 2)  low wide-angle close-up under the right shoulder of the crucified figure, looking up
                along the arm stretched to the end of the crossbeam against the dim red-brown sky; a slow
                push, fingers slowly tightening. No face in frame.
Setup A lives 30 m east of the cross; each setup is hidden (keyed hide_render) while the other is on
screen, and one camera jumps between them at the cut.
"""
import math
import bpy
from mathutils import Vector, Matrix
from lib import core as C
from lib import fx as FX
from lib import env as E
from lib import assets as A
from lib import characters as P

SUN_AZ = 300.0        # cheated for the close-ups: dull sun from front-left of the cross, 24 deg up
SUN_E = 0.8           # eclipse preset is 0.35; a bit more so form and water glints read
OA = Vector((30.0, 0.0, 0.0))   # setup A origin (ground level)


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


def build(ctx):
    NR = ctx.render_frames
    p0, p1 = ctx.phrases[0], ctx.phrases[1]
    CUT = int(ctx.frame(p1["start"]))            # first frame of setup B (~2.7 s, on "and all my bones")

    # ------------------------------------------------------------------ sky / sun (eclipse, shared)
    sky = E.sky("eclipse", ctx=ctx, sun_az=SUN_AZ)
    sun = sky["sun"]
    sun.data.energy = SUN_E
    sdir = Vector(sky["sun_dir"])

    # ================================================================== SETUP A: the pour
    vh = Vector((sdir.x, sdir.y, 0)).normalized()         # camera looks towards the sun (backlight)
    right = Vector((vh.y, -vh.x, 0))                        # screen right
    d = right                                               # water flows to screen right
    lip_h = 0.52
    L = OA + Vector((0, 0, lip_h)) - d * 0.08
    f_start, f_end = -14, 21                                 # pour (effect frames); stream already falling at f1
    # hero cracked-earth patch (bigger than the FX default so the frame never sees its edge in focus)
    gp = FX.cracked_ground((L.x + d.x * 0.12, L.y + d.y * 0.12, OA.z), size=3.6, res=330, seed=1, name="Cracked")
    # clear, neutral water (FX default is faintly blue; reads as grey plastic in this warm light)
    FX.water_material("FX_water_1", rough=0.015, tint=(1.0, 1.0, 1.0), raytrace=True)
    pour = FX.water_pour(lip=tuple(L), direction=(d.x, d.y), speed=0.5, stream_radius=0.012,
                         start_frame=f_start, end_frame=f_end, time_scale=0.25, ground_z=OA.z, jar=False,
                         ground=None, ground_material=gp.active_material, puddle_radius=0.26, drain_time=0.6,
                         seed=1, name="Pour")
    imp = Vector(pour.impact)
    # surrounding parched ground (below the crack grooves of the hero patch), darker so it doesn't glow
    far_m = C.mat_pbr("brown_mud_dry", scale=1.0 / 0.48, tint=(0.6, 0.5, 0.42), rough_add=0.15, name="s10a_mud")
    far = C.ground_plane(size=40, mat_=far_m, z=OA.z - 0.03, name="MudFar")
    far.location.x, far.location.y = OA.x, OA.y

    # earthen pitcher: spout at the lip, body tilted towards the pour direction (held off-screen)
    jar = A.load("water_jar", variant=1)
    clay = A.mat_clay("terracotta")
    for o in A.children_recursive(jar):
        if o.type == "MESH":
            o.data.materials.clear()
            o.data.materials.append(clay)
    spout = Vector(jar["mouth"])
    piv = bpy.data.objects.new("JarPivot", None)
    C.link(piv)
    jar.parent = piv
    jar.location = -spout
    jar.rotation_euler = (0, 0, 0)
    yaw = math.atan2(d.x, -d.y)
    axis = Vector((0, 0, 1)).cross(d).normalized()

    def jar_rot(f):
        u = C.smoothstep((f - (f_start - 10)) / float(CUT - (f_start - 10)))
        tilt = math.radians(78 + 26 * u)
        return (Matrix.Rotation(tilt, 3, axis) @ Matrix.Rotation(yaw, 3, "Z")).to_euler()
    piv.location = L
    C.key_fn(piv, "rotation_euler", jar_rot, 1, CUT, step=2)
    # glint light: a big soft source low at camera-left, light-linked to the water only, so the stream
    # carries a specular stripe, the beads sparkle and the film shows a sheen (the dull backlit sun alone
    # leaves a thin stream nearly invisible against the ground)
    wl = C.light("AREA", tuple(imp - right * 0.75 - vh * 0.55 + Vector((0, 0, 0.55))), 260, temp=4200,
                 target=tuple(imp.lerp(L, 0.4)), size=0.9, name="WaterGlint", shadow=False)
    wrecv = bpy.data.collections.new("s10a_water_recv")
    for k in ("stream", "droplets", "puddle"):
        o = getattr(pour, k, None)
        if o is not None:
            wrecv.objects.link(o)
    wl.light_linking.receiver_collection = wrecv
    setA = [pour.root, far, piv, gp, wl]
    for k in ("stream", "droplets", "puddle", "ground"):
        o = getattr(pour, k, None)
        if o is not None:
            setA.append(o)

    # ================================================================== SETUP B: the arm on the cross
    cm = C.wood_material("rough_wood", scale=1.2, tint=(0.62, 0.52, 0.42))
    cross = C.wooden_cross(loc=(0, 0, -0.45), height=4.85, material=cm, name="Cross")
    j = P.make_person("jesus", "JESUS_CROSS", pose=None, hair_strands=False)
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
            q0 = pb.rotation_quaternion.copy()
            pb.keyframe_insert("rotation_quaternion", frame=fA)
            amt = (10, 16, 12)[k - 1] if i > 1 else (4, 6, 6)[k - 1]
            P.rotate_bone(j, bn, (amt, 0, 0), frame=fB, mode="ADD")
            pb.rotation_quaternion = q0
    setB = [cross] + j.objects()

    # visibility per setup
    _hide_keys(setA, hidden_from=CUT)
    _hide_keys(setB, visible_from=CUT)

    # ================================================================== camera
    cam = C.camera((0, -1, 1), (0, 0, 1), lens=50, fstop=2.8, name="Cam")
    # A: low, looking towards the sun, down onto the impact, stream in profile
    a_tgt0 = imp.lerp(L, 0.5) - right * 0.03
    pitch = math.radians(24)

    def camA(f):
        u = C.ease_in_out((f - 1) / float(CUT - 1))
        tgt = a_tgt0 + Vector((0, 0, -0.04 * u))
        dist = 1.12 - 0.1 * u
        loc = tgt + (-vh * math.cos(pitch) + Vector((0, 0, math.sin(pitch)))) * dist - right * (0.02 + 0.04 * u)
        loc = loc + C.shake(f, 0.002, 0.5, 11)
        foc = (imp.lerp(L, 0.3) - loc).length
        return (loc, tgt, 0.0, 60, foc)

    # B: under the right shoulder, wide lens up along the arm to the hand on the beam
    def camB(f):
        u = C.ease_in_out((f - CUT) / float(NR - CUT))
        loc = sh + Vector((-0.02, -0.5, -0.62)).lerp(Vector((-0.09, -0.44, -0.52)), u)
        tgt = sh.lerp(hand, 0.52) + Vector((0, 0, 0.07))
        loc = loc + C.shake(f, 0.0015, 0.4, 5)
        foc = (elbow - loc).length
        return (loc, tgt, -2.0 + 3.0 * u, 28, foc)

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

    ctx.samples = 6
    ctx.render_opts.update({"raytracing": True, "volumetrics": "low"})
    ctx.interp = False
    ctx.post.update({"grade": "eclipse", "caption": {"y": 0.74}})
