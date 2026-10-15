"""s01a - "Face on the cross": "My God, my God, why have you forsaken me?"

Dissolve in from s00 (bright golden wide of Golgotha). Low three-quarter close-up of Jesus on the
centre cross (JESUS_CROSS: crown of thorns, long dark hair, full beard, sweat, dust, a thread of blood at
the brow). The camera sits down-sun (the axis s01b starts on), so the veiled sun hangs above the frame
behind his head: warm rim on the hair, crown and shoulders, a soft warm key on the far side of the face
(short lighting), cool sky fill on the near side, the dark upright of the cross behind his head.
Head bowed and eyes lowered at first; on "My God, my God" the eyes lead, the head lifts to the sky and
the mouth opens as if crying out; through "why have you forsaken me?" he holds the gaze upward in
anguish while the light dims (sky: first third of the eclipse darkening, continued by s01b).
Slow push-in, shallow depth of field.
"""
import json
import math
import os
import bpy
from mathutils import Vector
from lib import core as C
from lib import env as E
from lib import characters as P

SUN_AZ, SUN_EL = 140.0, 30.0      # = s01b (the cut continues on the same axis)
SKYLIGHT = 0.12                   # world (sky dome) lighting multiplier: the lamps shape the face
CAM_AZ = 22.0                     # camera bearing around the face, degrees towards the character's RIGHT (-X)
CAM_EL = -5.0                     # degrees below the eyes
D0, D1 = 1.0, 0.8                 # camera distance (m) start -> end (push-in)
LENS0, LENS1 = 60.0, 62.0
FSTOP = 2.4
EYE_UP = 8.0                      # eye pitch limit (deg, head frame): more and the iris rolls under the lid
AIM_DZ = -0.06                    # aim point below the eyes (puts the eyes at ~0.42 H)
HAIR_N, BEARD_D = 6000, 0.75      # hero strands thinned (cost) - indistinguishable at this size
LIGHTS = dict(key=300.0, rim=320.0, fill=60.0, bounce=4.0, cross=70.0)
SHADOW_RES = 0.004               # coarse shadow texels (m): soft area shadows need no detail, hair shadows are costly
LAST = {}                         # handles for dev tools


def _s01b_dark_window():
    """Frames (in s01a's own numbering) of s01b's darkening ramp, so the cut lands exactly where s01b
    starts (35 % into the warm-overcast -> eclipse cross-fade). Mirrors s01b.build()."""
    tl = json.load(open(os.path.join(C.ROOT, "timeline.json")))
    me = next(s for s in tl["shots"] if s["id"] == "s01a")
    nb = next(s for s in tl["shots"] if s["id"] == "s01b")
    f_dark = int(1 + nb["phrases"][-1]["end"] * tl["fps"]) + 2
    f0 = int(round((1 - 0.40 * f_dark) / 0.60))
    off = me["nframes"]                 # s01b frame 1 == s01a frame nframes + 1
    return f0 + off, f_dark + off


def _sky(ctx):
    # s01b's sky (eclipse -> eclipse: bright warm thin overcast -> eclipse), shifted in time; only the
    # lighting strength of the dome differs (visible sky identical)
    over_a = dict(sun_az=SUN_AZ, sun_el=SUN_EL, key=0.36, strength=0.55 * SKYLIGHT, sun_energy=3.4,
                  tint=(1.0, 0.82, 0.6), sat=1.0, sun_tint=(1.0, 0.8, 0.56), sun_angle=1.2, haze_density=0.0005,
                  haze_tint=(1.0, 0.95, 0.88), fog=(1.0, 0.84, 0.62), exposure=0.0, grade="warm", clouds=0.55,
                  cloud_opts=dict(color=(0.8, 0.72, 0.64), shadow=(0.3, 0.25, 0.22), opacity=0.85, sun_glow=1.2,
                                  speed=(9.0, 3.0)),
                  sun_disk=dict(el=SUN_EL, size=0.9, color=(1.0, 0.86, 0.62), strength=70.0, glow=0.3))
    over_b = dict(sun_az=SUN_AZ, sun_el=SUN_EL, strength=E.SKY_PRESETS["eclipse"]["strength"] * SKYLIGHT,
                  sun_disk=dict(E.SKY_PRESETS["eclipse"]["sun_disk"], el=SUN_EL))
    f0, f1 = _s01b_dark_window()
    tr = E.sky_transition(ctx, "eclipse", "eclipse", f0, f1, over_a=over_a, over_b=over_b)
    return tr, f0, f1


def _lean(j):
    """Render-cost trims for the close-up (measured: hair strands + shadows dominate)."""
    for g in j.garments:                       # off-screen below the chest
        if "loincloth" in g.name:
            g.hide_render = True
    for m in j.body.modifiers:                 # the beard hides the jaw line; -10 % frame time
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
    except Exception as e:                     # library in flux: keep whatever exists
        print("s01a WARNING: hair/beard rebuild failed:", e)
    # mouth: the lit MPFB teeth read as dentures/braces at this size; without them the open mouth is a
    # dark cavity (tongue kept), which reads as a cry
    if "teeth" in j.parts:
        j.parts["teeth"].hide_render = True


def _ease(a, b, f):
    return C.smoothstep(min(1.0, max(0.0, (f - a) / float(b - a))))


# ----------------------------------------------------------------------------------------------
# performance: head / eyes / face
# ----------------------------------------------------------------------------------------------
NECK_W = (("neck01", 0.22), ("neck02", 0.24), ("neck03", 0.24), ("head", 0.30))


def _key_body(j, base, frames, fn):
    """fn(f) -> dict(pitch, tilt, turn, breath) degrees. Keys neck/head/upper spine/clavicles on top of
    the static base pose (place_on_cross)."""
    bones = [n for n, _ in NECK_W] + ["spine02", "spine01", "clavicle.L", "clavicle.R"]
    for f in frames:
        a = fn(f)
        Pz = base.copy()
        br = a.get("breath", 0.0)
        Pz.turn("spine02", bend=-0.8 * br)
        Pz.turn("spine01", bend=-1.0 * br)
        for s in "LR":
            Pz.turn("clavicle." + s, side=(-1.4 * br if s == "L" else 1.4 * br))   # shrug up
        for n, w in NECK_W:
            Pz.turn(n, bend=a["pitch"] * w, side=a.get("tilt", 0.0) * w, twist=a.get("turn", 0.0) * w)
        Pz.write(frame=f, bones=bones)


def _expr_keys(j, keys):
    """keys: [(frame, unit dict, weight)]. All units are created first so every key sets every unit."""
    allu = set()
    for _, d, _w in keys:
        allu |= set(P._expand_units(d))
    P._ensure_units(j, sorted(allu))
    for f, d, w in keys:
        P.expression(j, d, w, frame=f)


def _lights(face_c, df0, df1, N, NR, person):
    L = LIGHTS
    # key: the bright overcast above him - a big soft top-front light (cool-neutral). Lifting his face to
    # the sky turns it into this light. Spot, so it falls off on the chest; lights the person only.
    key = C.light("SPOT", face_c + Vector((0.45, -1.25, 1.55)), L["key"], color=(0.86, 0.9, 1.0),
                  target=face_c + Vector((0, 0, 0.1)), size=0.35, spot_size=34, spot_blend=1.0, name="KeySky")
    # kicker: the veiled sun from behind his left (screen right): far cheek, beard edge, hair, shoulder
    rim = C.light("SPOT", face_c + Vector((1.15, 0.28, 0.5)), L["rim"], color=(1.0, 0.72, 0.45), target=face_c,
                  size=0.25, spot_size=40, spot_blend=0.8, name="KickSun", shadow=False)
    # fill: cool sky from the camera side, broad, no shadows
    fill = C.light("SPOT", face_c + Vector((-1.5, -1.5, 0.3)), L["fill"], color=(0.62, 0.74, 1.0), target=face_c,
                   size=0.8, spot_size=36, spot_blend=1.0, name="FillSky", shadow=False)
    # warm bounce from the sunlit hill below
    bounce = C.light("AREA", face_c + Vector((-0.3, -1.0, -1.4)), L["bounce"], color=(1.0, 0.72, 0.5),
                     target=face_c, size=1.5, name="Bounce", shadow=False)
    # the wood of the cross: soft sky light only (no key), so it reads as dark weathered wood, not a cut-out
    xfill = C.light("AREA", face_c + Vector((-0.8, -1.6, 0.9)), L["cross"], color=(0.9, 0.85, 0.8),
                    target=face_c + Vector((0, 0.3, 0)), size=2.0, name="CrossFill", shadow=False)
    xr = bpy.data.collections.new("S01aCrossRecv")
    for o in bpy.data.objects:
        if o.name.startswith("Cross_center"):
            xr.objects.link(o)
    xfill.light_linking.receiver_collection = xr
    recv = bpy.data.collections.new("S01aKeyRecv")
    for o in person.objects():
        if o.type in ("MESH", "CURVES"):
            recv.objects.link(o)
    for ob in (key, rim):
        ob.light_linking.receiver_collection = recv
    # the light dims with the sky (key/kicker/bounce follow the sun, fill stays)
    for f in sorted(set((1, max(1, int(df0)), N, NR))):
        d = C.smoothstep(min(1.0, max(0.0, (f - df0) / float(df1 - df0))))
        for ob, e0, k in ((key, L["key"], 1.7), (rim, L["rim"], 1.8), (bounce, L["bounce"], 1.4)):
            ob.data.energy = e0 * max(0.0, 1.0 - k * d)
            ob.data.keyframe_insert("energy", frame=f)
        rim.data.color = Vector((1.0, 0.72, 0.45)).lerp(Vector((1.0, 0.42, 0.2)), min(1.0, 2.2 * d))
        rim.data.keyframe_insert("color", frame=f)
    key.data.shadow_maximum_resolution = SHADOW_RES
    flag = _flag(key.location, face_c + Vector((0, 0, -0.16)))
    return dict(key=key, rim=rim, fill=fill, bounce=bounce, xfill=xfill, flag=flag)


def _flag(light_pos, edge_pt, dist=0.35, w=1.2, h=0.8):
    """Camera-invisible black flag that cuts the key off below `edge_pt` (the chin): the chest falls
    into a soft shadow instead of being the brightest skin in the frame."""
    d = (Vector(light_pos) - Vector(edge_pt)).normalized()
    side = d.cross(Vector((0, 0, 1))).normalized()
    up = side.cross(d).normalized()                    # 'up' in the flag plane
    if up.z < 0:
        up = -up
    o = C.prim("plane", name="KeyFlag", size=1.0)
    o.scale = (w, h, 1.0)
    from mathutils import Matrix
    R = Matrix((side, up, d)).transposed()
    o.matrix_world = Matrix.Translation(Vector(edge_pt) + d * dist - up * (h / 2)) @ R.to_4x4() @ Matrix.Diagonal((w, h, 1, 1))
    C.assign(o, C.mat("KeyFlag_mat", (0, 0, 0), rough=1.0))
    for k in ("visible_camera", "visible_diffuse", "visible_glossy", "visible_volume_scatter", "visible_transmission"):
        setattr(o, k, False)
    return o


def build(ctx):
    N, NR = ctx.nframes, ctx.render_frames
    tr, df0, df1 = _sky(ctx)
    tr["sun"].data.use_shadow = False          # back light only (faces away from it); saves ~2 s/frame

    # ------------------------------------------------------------------ the centre cross of Golgotha
    H = E.golgotha_height(city=True, seed=0)
    gz = float(H(0.0, 0.6))
    cm = C.wood_material("rough_wood", scale=1.2, tint=(0.62, 0.52, 0.42))
    root = C.wooden_cross(loc=(0.0, 0.6, gz - 0.45), height=4.4 + 0.45, name="Cross_center", material=cm, sign=True)
    bpy.context.view_layer.update()

    # ------------------------------------------------------------------ Jesus
    j = P.make_person("jesus", "JESUS_CROSS", pose=None, blood=0.65)
    P.place_on_cross(j, root, head="level", strain=0.6)
    _lean(j)
    base = j._pose.copy()
    j.update()

    # timing from the narration ("My God, my God," 0.6-1.95 s, pause, "why have you forsaken me?" 2.4-3.9 s)
    ps = ctx.phrases[0]["start"] if ctx.phrases else 0.58
    fw = lambda sec: ctx.frame(ps + sec)
    f_cry0, f_cry1 = fw(0.05), fw(1.35)        # "My God, my God,"
    f_why0 = fw(1.85)                          # "why have you forsaken me?"
    f_lift0, f_lift1 = fw(-0.1), fw(1.75)      # head lift
    f_eye0, f_eye1 = fw(-0.25), fw(0.9)        # eyes lead the head

    def body_fn(f):
        lift = _ease(f_lift0, f_lift1, f)
        pitch = 7.0 - 34.0 * lift - 3.0 * _ease(f_lift1, NR, f)          # + = chin down
        breath = 0.5 - 0.5 * math.cos(2 * math.pi * (f - 1) / 58.0)        # laboured, ~2.4 s
        nz = C.shake(f, 1.0, 0.5, 7)
        return dict(pitch=pitch + 0.9 * nz.x - 0.8 * breath, tilt=-2.0 + 3.0 * lift + 0.7 * nz.y,
                    turn=-4.0 + 2.0 * lift + 0.8 * nz.z, breath=breath)
    _key_body(j, base, list(range(1, NR + 1, 2)) + ([NR] if NR % 2 == 0 else []), body_fn)

    # expressions (dicts of MakeHuman units, see characters.EXPRESSIONS)
    low = {"eyebrows-inner-up": 0.55, "eyebrows-down": 0.25, "eye-closure": 0.22, "eye-slit": 0.12,
           "mouth-depression": 0.18, "mouth-open": 0.04, "nose-elevation": 0.15, "neck-platysma": 0.2, "jaw": 4}
    cry = {"eyebrows-inner-up": 1.0, "eyebrows-down": 0.28, "eye-slit": 0.2, "eye-opened-up": 0.25,
           "mouth-open": 0.18, "mouth-retraction": 0.12, "mouth-depression": 0.12, "nose-elevation": 0.3,
           "neck-platysma": 0.5, "jaw": 8}
    ang = {"eyebrows-inner-up": 0.95, "eyebrows-down": 0.3, "eye-slit": 0.15, "eye-opened-up": 0.35,
           "nose-elevation": 0.25, "mouth-depression": 0.22, "mouth-open": 0.04, "neck-platysma": 0.32, "jaw": 4}
    keys = [(1, low, 1.0), (int(f_cry0) - 2, low, 1.0), (int(f_cry0) + 8, cry, 0.85),
            (int((f_cry0 + f_cry1) / 2), cry, 0.7), (int(f_cry1) - 2, cry, 1.0), (int(f_cry1) + 9, ang, 1.0),
            (int(f_why0) + 6, ang, 1.15), (int(f_why0) + 22, ang, 1.0), (NR, ang, 1.05)]
    _expr_keys(j, keys)
    # one slow blink in the pause
    fb = int(f_cry1 + 0.5 * (f_why0 - f_cry1)) | 1
    for f, v in ((fb - 3, 0.0), (fb, 1.0), (fb + 4, 0.0)):
        P.eyes_closed(j, v, frame=f)

    # eyes: lowered -> lifted to the sky (lead the head)
    sc = bpy.context.scene
    for f in sorted(set([1] + list(range(int(f_eye0), int(f_eye1) + 4, 4)) + [int(f_lift1), NR])):
        sc.frame_set(f)
        e = j.eye_pos()
        u = _ease(f_eye0, f_eye1, f)
        tgt_low = e + Vector((0.4, -3.0, -1.3))
        tgt_up = e + Vector((0.5, -2.0, 3.0))
        P.eyes_look(j, tgt_low.lerp(tgt_up, u), frame=f, up_limit=EYE_UP)
    sc.frame_set(1)
    e_start = j.eye_pos()
    sc.frame_set(int(f_lift1))
    e_end = j.eye_pos()
    sc.frame_set(1)

    lights = _lights((e_start + e_end) * 0.5, df0, df1, N, NR, j)

    # ------------------------------------------------------------------ camera
    cam_dir = Vector((-math.sin(math.radians(CAM_AZ)), -math.cos(math.radians(CAM_AZ)), 0.0))
    cam_dir = (cam_dir * math.cos(math.radians(CAM_EL)) + Vector((0, 0, math.sin(math.radians(CAM_EL))))).normalized()
    focus = bpy.data.objects.new("FocusEye", None)
    sc.collection.objects.link(focus)
    focus.parent = j.rig
    focus.parent_type = "BONE"
    focus.parent_bone = "eye.R"            # near eye (camera on the character's right)
    focus.location = (0, 0, 0)
    cam = C.camera(loc=e_start + cam_dir * D0, target=e_start, lens=LENS0, fstop=FSTOP, focus=focus)

    def path(f):
        u = C.ease_in_out(min(1.0, (f - 1) / float(NR - 1)))
        k = _ease(f_lift0 - 6, f_lift1 + 10, f)
        eye = e_start.lerp(e_end, k)
        d = D0 + (D1 - D0) * u
        loc = eye + cam_dir * d + C.shake(f, 0.004, 0.35, 3)
        return (loc, eye + Vector((0, 0, AIM_DZ)), 0.0, LENS0 + (LENS1 - LENS0) * u)
    C.animate_camera(cam, path, 1, NR)

    LAST.update(j=j, cam=cam, root=root, sky=tr, e_start=e_start, e_end=e_end, **lights)

    ctx.samples = 5
    ctx.render_opts.update({"volumetrics": "low"})
    ctx.interp = True
    ctx.post.update({"grade": "warm", "bloom": 0.22, "vignette": 0.24,
                     "end": {"grade": "eclipse", "saturation": 0.85, "vignette": 0.24, "bloom": 0.25},
                     "caption": {"y": 0.72}})
