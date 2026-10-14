"""s16c - "His face in the light": "he has not hidden his face from him / but has listened to his cry for help."

Dissolve in from s16b (the nail-scarred open hand in warm sunlight). Bookend of s01a: the same low
three-quarter close-up, mirrored (camera on his left), of the risen Jesus (JESUS_RISEN: clean, white
robe, no crown). Dawn: at first his face rests in the cool shade of the morning sky, eyes closed, head a
little bowed. The sun clears the last cloud bank: a soft edge of warm, low sunlight washes down over his
face from the brow to the beard ("he has not hidden his face"), his eyes open into the light and lift
with a slight lift of the head; on "but has listened to his cry for help" a quiet smile. The background
is the cool blue-violet morning sky away from the sun (warm face against cool sky). Slow push-in,
shallow depth of field.
"""
import math
import bpy
from mathutils import Vector
from lib import core as C
from lib import env as E
from lib import characters as P

SUN_AZ, SUN_EL = 42.0, 9.0        # low morning sun, in front of him, on the camera side (broad light)
CAM_AZ = -28.0                    # camera bearing around the face, degrees towards the character's RIGHT (-: his left)
CAM_EL = -7.0
D0, D1 = 1.0, 0.8
LENS0, LENS1 = 60.0, 62.0
FSTOP = 2.4
AIM_DZ = -0.06
SUN_E = 4.0                       # sun lamp W/m2 once clear of the cloud
LIGHTS = dict(fill=14.0, rim=30.0, bounce=6.0)
LAST = {}


def _ease(a, b, f):
    return C.smoothstep(min(1.0, max(0.0, (f - a) / float(b - a))))


NECK_W = (("neck01", 0.22), ("neck02", 0.24), ("neck03", 0.24), ("head", 0.30))


def _key_body(j, base, frames, fn):
    bones = [n for n, _ in NECK_W] + ["spine02", "spine01", "clavicle.L", "clavicle.R"]
    for f in frames:
        a = fn(f)
        Pz = base.copy()
        br = a.get("breath", 0.0)
        Pz.turn("spine02", bend=-0.5 * br)
        Pz.turn("spine01", bend=-0.6 * br)
        for s in "LR":
            Pz.turn("clavicle." + s, side=(-0.8 * br if s == "L" else 0.8 * br))
        for n, w in NECK_W:
            Pz.turn(n, bend=a["pitch"] * w, side=a.get("tilt", 0.0) * w, twist=a.get("turn", 0.0) * w)
        Pz.write(frame=f, bones=bones)


def _expr_keys(j, keys):
    allu = set()
    for _, d, _w in keys:
        allu |= set(P._expand_units(d))
    allu |= {"eye-left-closure", "eye-right-closure"}
    P._ensure_units(j, sorted(allu))
    for f, d, w in keys:
        P.expression(j, d, w, frame=f)


def _occluder(face, sun_dir, f0, f1):
    """Camera-invisible soft-edged 'cloud' between the sun and the face; it slides down so the edge of
    sunlight sweeps over the face from the brow to the chin between f0 and f1 (soft alpha ramp)."""
    dist = 3.0
    s = Vector(sun_dir).normalized()
    up = (Vector((0, 0, 1)) - s * s.z).normalized()          # 'down the face' direction in the plane
    o = C.prim("plane", name="SunCloud", size=6.0)
    m = bpy.data.materials.new("SunCloud_mat")
    m.use_nodes = True
    nt = m.node_tree
    bs = nt.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (0, 0, 0, 1)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    # wavy cloud edge: y + noise
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 0.9
    nz.inputs["Detail"].default_value = 3.0
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    add = nt.nodes.new("ShaderNodeMath")
    add.operation = "MULTIPLY_ADD"
    nt.links.new(nz.outputs["Fac"], add.inputs[0])
    add.inputs[1].default_value = 0.35
    nt.links.new(sep.outputs["Y"], add.inputs[2])
    mr = nt.nodes.new("ShaderNodeMapRange")           # alpha 1 (cloud) below the edge, 0 above
    mr.interpolation_type = "SMOOTHSTEP"
    nt.links.new(add.outputs[0], mr.inputs["Value"])
    mr.inputs["From Min"].default_value = 0.0
    mr.inputs["From Max"].default_value = 0.45
    mr.inputs["To Min"].default_value = 1.0
    mr.inputs["To Max"].default_value = 0.0
    nt.links.new(mr.outputs[0], bs.inputs["Alpha"])
    m.surface_render_method = "DITHERED"
    m.use_transparent_shadow = True
    C.assign(o, m)
    for k in ("visible_camera", "visible_diffuse", "visible_glossy", "visible_volume_scatter", "visible_transmission"):
        setattr(o, k, False)
    # orient: plane normal along the sun direction, local +Y = 'up' in the plane
    o.rotation_euler = s.to_track_quat("Z", "Y").to_euler()
    bpy.context.view_layer.update()
    ly = (o.matrix_world.to_3x3() @ Vector((0, 1, 0))).normalized()
    centre = Vector(face) + s * dist
    # edge (local y ~ 0.15 incl. noise midpoint) starts above the head, ends below the chin
    for f, off in ((f0, 0.38), (f1, -0.42)):
        o.location = centre + ly * (off - 0.2)
        o.keyframe_insert("location", frame=f)
    return o


def build(ctx):
    N, NR = ctx.nframes, ctx.render_frames
    S = E.sky("sunrise", sun_az=SUN_AZ, ctx=ctx, sun_el=SUN_EL, sun_energy=SUN_E, clouds=0.25,
              cloud_opts=dict(color=(1.0, 0.86, 0.74), shadow=(0.42, 0.36, 0.42), opacity=0.8, sun_glow=1.6,
                              speed=(5.0, 1.5)))
    sun = S["sun"]
    sun_dir = Vector(S["sun_dir"])

    j = P.make_person("jesus", "JESUS_RISEN", pose=None)
    P.pose(j, "stand", head="level")
    for g in j.garments:
        if "sandal" in g.name:
            g.hide_render = True
    base = j._pose.copy()
    j.update()

    # narration: "he has not hidden his face from him" 0.28-2.50 s, "but has listened to his cry for help." 2.80-5.04 s
    ph = ctx.phrases if ctx.phrases else [dict(start=0.28, end=2.5), dict(start=2.8, end=5.04)]
    fr = lambda sec: ctx.frame(sec)
    f_wash0, f_wash1 = fr(ph[0]["start"] + 0.55), fr(ph[0]["end"] - 0.15)          # light sweeps over the face
    f_open0, f_open1 = fr(ph[0]["start"] + 1.35), fr(ph[0]["start"] + 1.85)        # eyes open on "his face"
    f_lift0, f_lift1 = fr(ph[0]["end"] - 0.3), fr(ph[1]["start"] + 1.6)
    f_smile0, f_smile1 = fr(ph[1]["start"] + 0.5), fr(ph[1]["end"] + 0.2)

    def body_fn(f):
        lift = _ease(f_lift0, f_lift1, f)
        breath = 0.5 - 0.5 * math.cos(2 * math.pi * (f - 1) / 92.0)       # calm, ~3.8 s
        nz = C.shake(f, 1.0, 0.35, 11)
        return dict(pitch=9.0 - 21.0 * lift - 2.0 * _ease(f_lift1, NR, f) + 0.5 * nz.x - 0.5 * breath,
                    tilt=3.0 - 2.0 * lift + 0.4 * nz.y, turn=4.0 + 3.0 * lift + 0.5 * nz.z, breath=breath)
    _key_body(j, base, list(range(1, NR + 1, 2)) + ([NR] if NR % 2 == 0 else []), body_fn)

    rest = {"eye-closure": 1.0, "eyebrows-inner-up": 0.15, "mouth-corner-puller": 0.12}
    awake = {"eye-closure": 0.08, "eyebrows-up": 0.12, "eyebrows-inner-up": 0.15, "eye-opened-up": 0.08,
             "mouth-corner-puller": 0.18}
    smile = {"eye-closure": 0.06, "eye-slit": 0.12, "eyebrows-up": 0.08, "eyebrows-inner-up": 0.1,
             "mouth-corner-puller": 0.42, "mouth-elevation": 0.06}
    keys = [(1, rest, 1.0), (int(f_open0), rest, 1.0), (int(f_open1), awake, 1.0), (int(f_smile0), awake, 1.0),
            (int(f_smile1), smile, 1.0), (NR, smile, 1.0)]
    _expr_keys(j, keys)
    # a soft blink later on (alive)
    fb = int(f_smile1 + 14) | 1
    if fb + 4 < NR:
        for f, v in ((fb - 3, smile["eye-closure"]), (fb, 1.0), (fb + 4, smile["eye-closure"])):
            P.eyes_closed(j, v, frame=f)

    sc = bpy.context.scene
    for f in sorted(set([1, int(f_open0)] + list(range(int(f_open0), int(f_lift1) + 4, 4)) + [NR])):
        sc.frame_set(f)
        e = j.eye_pos()
        u = _ease(f_open0, f_lift1, f)
        tgt_rest = e + Vector((-0.3, -3.0, -0.6))
        tgt_up = e + sun_dir * 3.0 + Vector((0.0, 0.0, 1.3))           # into the light, up
        P.eyes_look(j, tgt_rest.lerp(tgt_up, u), frame=f)
    sc.frame_set(1)
    e_start = j.eye_pos()
    sc.frame_set(int(f_lift1))
    e_end = j.eye_pos()
    sc.frame_set(1)
    face_c = (e_start + e_end) * 0.5

    # ------------------------------------------------------------------ light
    occ = _occluder(face_c + Vector((0, 0, -0.05)), sun_dir, f_wash0, f_wash1)
    for f, k in ((1, 0.55), (int(f_wash0), 0.7), (int(f_wash1), 1.0)):     # cloud thinning
        sun.data.energy = SUN_E * k
        sun.data.keyframe_insert("energy", frame=f)
    L = LIGHTS
    fill = C.light("AREA", face_c + Vector((-1.6, -1.0, 0.6)), L["fill"], color=(0.6, 0.72, 1.0), target=face_c,
                   size=2.5, name="FillSky", shadow=False)
    rim = C.light("AREA", face_c + Vector((-0.9, 1.1, 0.7)), L["rim"], color=(0.85, 0.82, 1.0), target=face_c,
                  size=1.0, name="RimSky")
    bounce = C.light("AREA", face_c + Vector((0.6, -1.0, -1.3)), L["bounce"], color=(1.0, 0.75, 0.55),
                     target=face_c, size=1.5, name="Bounce", shadow=False)
    for f, k in ((1, 0.35), (int(f_wash0), 0.45), (int(f_wash1), 1.0)):     # ground bounce follows the sun
        bounce.data.energy = L["bounce"] * k
        bounce.data.keyframe_insert("energy", frame=f)

    # ------------------------------------------------------------------ camera
    cam_dir = Vector((-math.sin(math.radians(CAM_AZ)), -math.cos(math.radians(CAM_AZ)), 0.0))
    cam_dir = (cam_dir * math.cos(math.radians(CAM_EL)) + Vector((0, 0, math.sin(math.radians(CAM_EL))))).normalized()
    focus = bpy.data.objects.new("FocusEye", None)
    sc.collection.objects.link(focus)
    focus.parent = j.rig
    focus.parent_type = "BONE"
    focus.parent_bone = "eye.L" if CAM_AZ < 0 else "eye.R"       # the near eye
    cam = C.camera(loc=e_start + cam_dir * D0, target=e_start, lens=LENS0, fstop=FSTOP, focus=focus)

    def path(f):
        u = C.ease_in_out(min(1.0, (f - 1) / float(NR - 1)))
        k = _ease(f_lift0 - 6, f_lift1 + 10, f)
        eye = e_start.lerp(e_end, k)
        d = D0 + (D1 - D0) * u
        loc = eye + cam_dir * d + C.shake(f, 0.003, 0.3, 5)
        return (loc, eye + Vector((0, 0, AIM_DZ)), 0.0, LENS0 + (LENS1 - LENS0) * u)
    C.animate_camera(cam, path, 1, NR)

    LAST.update(j=j, cam=cam, sun=sun, occ=occ, fill=fill, rim=rim, bounce=bounce, e_start=e_start, e_end=e_end)

    ctx.samples = 6
    ctx.render_opts.update({"volumetrics": "low"})
    ctx.interp = True
    ctx.post.update({"grade": "dawn", "bloom": 0.3, "vignette": 0.2,
                     "end": {"grade": ["dawn", "glory"], "bloom": 0.38, "vignette": 0.18}})
