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

SUN_AZ, SUN_EL = -32.0, 10.0      # low morning sun, in front of him on his right (screen left): short lighting
CAM_AZ = -28.0                    # camera bearing around the face, degrees towards the character's RIGHT (-: his left)
CAM_EL = -10.0
D0, D1 = 0.92, 0.74
LENS0, LENS1 = 60.0, 62.0
FSTOP = 2.4
AIM_DZ = -0.06
SUN_E = 4.0                       # sun lamp W/m2 once clear of the cloud
SUN_RGB = (1.0, 0.78, 0.56)       # warm gold (the HDRI's measured sunrise colour turns skin orange)
EDGE = (0.5, -0.3)                # sunlight edge relative to the eyes (m, along 'up'): start -> end of the sweep
OCC_DIST, OCC_SUN_ANGLE = 6.0, 3.0  # cloud card distance (m) and sun angular diameter (deg) -> ~0.3 m penumbra
LIGHTS = dict(fill=45.0, rim=40.0, bounce=6.0)
SKYLIGHT = 0.5                    # sky dome lighting (visible sky unchanged)
HAIR_N, BEARD_D = 6000, 0.75
ROBE_K = 0.6
LAST = {}


def _lean(j):
    """Render-cost trims for the close-up (hair strands + shadows dominate the frame time)."""
    for g in j.garments:
        if "sandal" in g.name:
            g.hide_render = True
    for m in j.body.modifiers:
        if m.type == "SUBSURF":
            m.render_levels = 0
    try:
        old = j.parts.pop("hair_strands", None)
        if old is not None:
            bpy.data.objects.remove(old, do_unlink=True)
        P.make_hair_strands(j, count=HAIR_N, points=10, flyaways=0.0)
        old = j.parts.pop("beard", None)
        if old is not None:
            bpy.data.objects.remove(old, do_unlink=True)
        P.make_beard(j, density=BEARD_D)
    except Exception as e:
        print("s16c WARNING: hair/beard rebuild failed:", e)
    for k in ("teeth", "tongue"):              # lips stay closed: the lit teeth showed as a white line
        if k in j.parts:
            j.parts[k].hide_render = True
    for g in j.garments:                       # bleached robe -> soft cream: no blown-out white under the face
        if "sandal" not in g.name:
            g.color = (g.color[0] * ROBE_K, g.color[1] * ROBE_K * 0.98, g.color[2] * ROBE_K * 0.94, 1.0)


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


def _occluder(face, sun_dir, f0, f1, sun):
    """The last cloud bank in front of the sun, as a camera-invisible opaque card with a wavy top edge
    standing OCC_DIST m towards the sun. It sinks so the edge of sunlight sweeps down over his face
    (brow -> beard) between f0 and f1. Opaque geometry + the sun's angular size give a clean soft
    penumbra (OCC_DIST * sun angle ~ 0.3 m); a dithered alpha edge was noisy (bad for 12 fps + RIFE)."""
    import numpy as np
    s = Vector(sun_dir).normalized()
    side = s.cross(Vector((0, 0, 1))).normalized()
    up = side.cross(s).normalized()
    if up.z < 0:
        up, side = -up, -side
    n = 48
    xs = np.linspace(-4.0, 4.0, n)
    top = 0.05 * np.sin(xs * 2.3 + 0.7) + 0.03 * np.sin(xs * 5.1 + 2.0)      # wavy cloud edge (m)
    verts, faces = [], []
    for i, x in enumerate(xs):
        verts.append((float(x), float(top[i]), 0.0))
        verts.append((float(x), -7.0, 0.0))
    for i in range(n - 1):
        a0, b0, a1, b1 = 2 * i, 2 * i + 1, 2 * i + 2, 2 * i + 3
        faces.append((a0, b0, b1, a1))
    me = bpy.data.meshes.new("SunCloud")
    me.from_pydata(verts, [], faces)
    o = bpy.data.objects.new("SunCloud", me)
    bpy.context.scene.collection.objects.link(o)
    C.assign(o, C.mat("SunCloud_mat", (0, 0, 0), rough=1.0))
    for k in ("visible_camera", "visible_diffuse", "visible_glossy", "visible_volume_scatter", "visible_transmission"):
        setattr(o, k, False)
    from mathutils import Matrix
    R = Matrix((side, up, s)).transposed().to_4x4()
    centre = Vector(face) + s * OCC_DIST
    for f, e in ((f0, EDGE[0]), (f1, EDGE[1])):
        o.matrix_world = Matrix.Translation(centre + up * e) @ R
        o.keyframe_insert("location", frame=f)
        o.keyframe_insert("rotation_euler", frame=f)
    sun.data.angle = math.radians(OCC_SUN_ANGLE)
    return o


def build(ctx):
    N, NR = ctx.nframes, ctx.render_frames
    S = E.sky("sunrise", sun_az=SUN_AZ, ctx=ctx, sun_el=SUN_EL, sun_energy=SUN_E, clouds=0.45,
              strength=SKYLIGHT,
              cloud_opts=dict(color=(1.0, 0.86, 0.74), shadow=(0.42, 0.36, 0.42), opacity=0.8, sun_glow=1.6,
                              speed=(5.0, 1.5)))
    sun = S["sun"]
    sun.data.color = SUN_RGB
    sun_dir = Vector(S["sun_dir"])

    j = P.make_person("jesus", "JESUS_RISEN", pose=None)
    P.pose(j, "stand", head="level")
    _lean(j)
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
                    tilt=2.0 - 4.0 * lift + 0.4 * nz.y, turn=-2.0 - 12.0 * lift + 0.5 * nz.z, breath=breath)
    _key_body(j, base, list(range(1, NR + 1, 2)) + ([NR] if NR % 2 == 0 else []), body_fn)

    rest = {"eye-closure": 1.0, "eyebrows-inner-up": 0.15, "mouth-corner-puller": 0.12, "mouth-compression": 0.3}
    awake = {"eye-closure": 0.06, "eyebrows-up": 0.12, "eyebrows-inner-up": 0.15, "eye-opened-up": 0.08,
             "mouth-corner-puller": 0.18, "mouth-compression": 0.3}
    smile = {"eye-closure": 0.04, "eye-slit": 0.1, "eyebrows-up": 0.08, "eyebrows-inner-up": 0.1, "eye-opened-up": 0.06,
             "mouth-corner-puller": 0.42, "mouth-elevation": 0.06, "mouth-compression": 0.25}
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
        tgt_rest = e + Vector((-0.6, -3.0, -0.6))
        tgt_up = e + Vector((-1.0, -3.0, 1.3))                          # towards the light, up
        P.eyes_look(j, tgt_rest.lerp(tgt_up, u), frame=f, up_limit=7.0)
    sc.frame_set(1)
    e_start = j.eye_pos()
    sc.frame_set(int(f_lift1))
    e_end = j.eye_pos()
    sc.frame_set(1)
    face_c = (e_start + e_end) * 0.5

    # ------------------------------------------------------------------ light
    occ = _occluder(face_c, sun_dir, f_wash0, f_wash1, sun)
    for f, k in ((1, 0.55), (int(f_wash0), 0.7), (int(f_wash1), 1.0)):     # cloud thinning
        sun.data.energy = SUN_E * k
        sun.data.keyframe_insert("energy", frame=f)
    L = LIGHTS
    # cool morning sky on the shadow side (camera side), soft
    fill = C.light("SPOT", face_c + Vector((1.5, -1.2, 0.5)), L["fill"], color=(0.6, 0.72, 1.0),
                   target=face_c + Vector((0, 0, 0.06)), size=0.8, spot_size=30, spot_blend=1.0, name="FillSky",
                   shadow=False)
    # bright sky behind his left shoulder: separates hair and cheek from the background
    rim = C.light("AREA", face_c + Vector((1.0, 1.0, 0.7)), L["rim"], color=(0.85, 0.82, 1.0), target=face_c,
                  size=1.0, name="RimSky", shadow=False)
    bounce = C.light("AREA", face_c + Vector((-0.6, -1.0, -1.3)), L["bounce"], color=(1.0, 0.75, 0.55),
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

    ctx.samples = 5
    ctx.render_opts.update({"volumetrics": "low"})
    ctx.interp = True
    ctx.post.update({"grade": "dawn", "bloom": 0.3, "vignette": 0.2,
                     "end": {"grade": ["dawn", "glory"], "bloom": 0.38, "vignette": 0.18}})
