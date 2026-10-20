"""Assemble one shot: set + characters + procedural performance + camera, then save a renderable .blend.

Usage: blender -b -P shotbuild.py -- SHOT_ID [--preview]
Reads /opt/work/timeline.json and shots.py; writes /opt/work/shots/SHOT_ID.blend
(frames render to /opt/work/frames/SHOT_ID/####.png).
"""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import rigtools as rt
import perform as pf
import gestures as gs
from shots import SHOTS, resolve_time, shot_bounds, EYE_H

FPS = 24
TL = json.load(open("/opt/work/timeline.json"))
LINES = {l["id"]: l for l in TL["lines"]}
CHAR_DIR = "/opt/work/chars"
SET_DIR = "/opt/work/sets"

FACE_MESH_SUFFIX = (".body", ".eyebrow", ".eyelashes", ".teeth", ".tongue")
SET_EYE_H = {"upper_room": 0.95, "apartment": 1.05}
CUR_SET = ["colonnade"]


# ----------------------------------------------------------------------------- scene setup

def open_set(name):
    bpy.ops.wm.open_mainfile(filepath=f"{SET_DIR}/{name}.blend")
    scn = bpy.context.scene
    for o in [o for o in scn.objects if o.name.startswith("CAMHINT_")]:
        o.hide_render = True
    return scn


def append_character(name):
    path = f"{CHAR_DIR}/{name}.blend"
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.collections = [c for c in src.collections if c == f"CHAR_{name}"]
    col = dst.collections[0]
    bpy.context.scene.collection.children.link(col)
    rig = bpy.data.objects[name]
    return rig


def char_meshes(rig):
    return [o for o in rig.children if o.type == 'MESH']


def face_meshes(rig):
    # eyeballs are turned by the eye bones; their eyeLook* keys would double the rotation
    return [o for o in char_meshes(rig) if o.data.shape_keys and not o.name.endswith(".high-poly")]


def place(rig, mark_name, offset=(0, 0, 0), rot=0.0, rotz=None):
    mk = bpy.data.objects.get(mark_name)
    if mk is None:
        raise RuntimeError(f"missing mark {mark_name}")
    rig.location = mk.location + Vector(offset)
    z = math.radians(rotz) if rotz is not None else mk.rotation_euler.z + math.radians(rot)
    rig.rotation_euler = (0, 0, z)


def set_clothing(rig, variant):
    """variant 'stand' shows the skirt, 'sit' swaps it for the leg tubes."""
    for o in char_meshes(rig):
        if o.name.endswith(".skirt"):
            o.hide_render = o.hide_viewport = (variant == "sit")
        if o.name.endswith(".robe_legs"):
            o.hide_render = o.hide_viewport = (variant != "sit")


def head_world(rig):
    pb = rig.pose.bones["head"]
    return rig.matrix_world @ (pb.head + (pb.tail - pb.head) * 0.35)


def eyes_world(rig):
    l = rig.matrix_world @ rig.pose.bones["eye.L"].head
    r = rig.matrix_world @ rig.pose.bones["eye.R"].head
    return (l + r) / 2


def forward(rig):
    return (rig.matrix_world.to_3x3() @ Vector((0, -1, 0))).normalized()


# ----------------------------------------------------------------------------- constraints

def empty(name, loc=(0, 0, 0), size=0.05):
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = size
    e.location = loc
    bpy.context.scene.collection.objects.link(e)
    return e


def setup_tracking(rig):
    n = rig.name
    eye_t = empty(f"EYE_TGT_{n}", eyes_world(rig) + forward(rig) * 2.0)
    head_t = empty(f"HEAD_TGT_{n}", eyes_world(rig) + forward(rig) * 2.0)
    for side in ("L", "R"):
        c = rig.pose.bones[f"eye.{side}"].constraints.new('DAMPED_TRACK')
        c.target = eye_t
        c.track_axis = 'TRACK_Y'
    for bone, infl in (("neck01", 0.12), ("neck02", 0.12), ("neck03", 0.18), ("head", 0.55)):
        c = rig.pose.bones[bone].constraints.new('DAMPED_TRACK')
        c.target = head_t
        c.track_axis = 'TRACK_Z' if bone == "head" else 'TRACK_Z'
        c.influence = infl
    return eye_t, head_t


def setup_ik(rig):
    n = rig.name
    out = {}
    for side in ("L", "R"):
        tgt = empty(f"HAND_{side}_{n}", rig.matrix_world @ rig.pose.bones[f"wrist.{side}"].head, 0.03)
        c = rig.pose.bones[f"lowerarm02.{side}"].constraints.new('IK')
        c.target = tgt
        c.chain_count = 4
        c.use_stretch = False
        c.influence = 0.0
        out[side] = (tgt, c)
    return out


# ----------------------------------------------------------------------------- keyframe helpers

def fcurves_of(id_data, create=True):
    """F-curve collection for an ID, handling Blender 4.4+ slotted actions."""
    ad = id_data.animation_data or (id_data.animation_data_create() if create else None)
    if ad is None:
        return None
    act = ad.action
    if act is None:
        if not create:
            return None
        act = bpy.data.actions.new(f"{id_data.name}_act")
        ad.action = act
    if not hasattr(act, "slots"):
        return act.fcurves
    if ad.action_slot is None:
        if len(act.slots) and create:
            ad.action_slot = act.slots[0]
        elif create:
            ad.action_slot = act.slots.new(id_type=id_data.id_type, name=id_data.name)
        else:
            return None
    if len(act.layers) == 0:
        act.layers.new("Layer")
    layer = act.layers[0]
    if len(layer.strips) == 0:
        layer.strips.new(type='KEYFRAME')
    strip = layer.strips[0]
    cb = strip.channelbag(ad.action_slot, ensure=create)
    return cb.fcurves if cb else None


def fcurve_set(id_data, path, index, frames, values):
    fcs = fcurves_of(id_data)
    fc = fcs.find(path, index=index)
    if fc is None:
        fc = fcs.new(path, index=index)
    fc.keyframe_points.clear()
    fc.keyframe_points.add(len(frames))
    co = np.empty(len(frames) * 2, dtype=np.float32)
    co[0::2] = frames
    co[1::2] = values
    fc.keyframe_points.foreach_set("co", co)
    fc.keyframe_points.foreach_set("interpolation", [1] * len(frames))  # LINEAR
    fc.update()
    return fc


def key_shape(rig, keyname, frames, values):
    for o in face_meshes(rig):
        kb = o.data.shape_keys.key_blocks.get(keyname)
        if kb is None:
            continue
        fcurve_set(o.data.shape_keys, f'key_blocks["{keyname}"].value', 0, frames, values)


def key_vec(obj, path, frames, arr):
    for i in range(arr.shape[1]):
        fcurve_set(obj, path, i, frames, arr[:, i])


def key_bone_quat(rig, bone, frames, quats):
    pb = rig.pose.bones[bone]
    pb.rotation_mode = 'QUATERNION'
    for i in range(4):
        fcurve_set(rig, f'pose.bones["{bone}"].rotation_quaternion', i, frames, quats[:, i])


# ----------------------------------------------------------------------------- performance

def words_for(speaker, t0, t1):
    out = []
    for l in TL["lines"]:
        if l["speaker"] != speaker or l["end"] < t0 or l["start"] > t1:
            continue
        for w in l["words"]:
            out.append(dict(w, start=w["start"] - t0, end=w["end"] - t0))
    return out


def lines_in(t0, t1):
    return [l for l in TL["lines"] if l["end"] > t0 and l["start"] < t1]


def speech_envelope(speaker, t0, n):
    """Per-frame loudness for a speaker from the line wavs (0..1)."""
    import wave
    env = np.zeros(n)
    for l in TL["lines"]:
        if l["speaker"] != speaker:
            continue
        a, b = l["start"] - t0, l["end"] - t0
        if b < 0 or a > n / FPS:
            continue
        path = l.get("wav", f"/opt/work/audio/lines/{l['id']}.wav")
        try:
            import soundfile as sf
            y, sr = sf.read(path)
        except Exception:
            with wave.open(path) as w:
                sr = w.getframerate()
                y = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16) / 32768.0
        stretch = (l["end"] - l["start"]) / (len(y) / sr)
        hop = sr / FPS / stretch
        for f in range(n):
            tt = f / FPS - a
            if 0 <= tt <= b - a:
                i = int(tt * sr / stretch)
                seg = y[max(0, i - int(hop)):i + int(hop)]
                if len(seg):
                    env[f] = max(env[f], float(np.sqrt(np.mean(seg ** 2))))
    if env.max() > 0:
        env = np.clip(env / (np.percentile(env[env > 0], 95) + 1e-6), 0, 1)
    return env


def build_performance(shot, name, rig, cast, t0, n, cam_obj):
    spec = cast[name]
    p = pf.Performance(n, FPS, seed=hash((shot["id"], name)) % 10000)
    p.blink_rate = spec.get("blink_rate", 3.6)
    frames = np.arange(n)
    tsec = frames / FPS
    # speech
    words = words_for(name, t0, t0 + n / FPS)
    for lid in spec.get("mouth_lines", []):
        l = LINES[lid]
        span = l["end"] - l["start"]
        # mouth the line silently, starting a beat into the shot
        for w in l["words"]:
            words.append(dict(w, start=w["start"] - l["start"] + 0.6, end=w["end"] - l["start"] + 0.6,
                              emph=0.0, silent=True))
    p.add_speech(words, 0)
    p.set_envelope(speech_envelope(name, t0, n))
    # emotions: default from line emotions while speaking, plus directives
    base_emo = spec.get("emo", "calm")
    p.emotion(0.0, base_emo, spec.get("emo_i", 1.0), 0.01)
    for l in lines_in(t0, t0 + n / FPS):
        if l["speaker"] == name and not spec.get("no_line_emo"):
            p.emotion(max(0.0, l["start"] - t0 - 0.25), l["emotion"], 1.0, 0.45)
    gaze = []  # (t, target)
    head_moves = []
    for act in shot.get("act", []):
        if act[0] != name:
            continue
        kind = act[1]
        t = resolve_time(act[2], LINES) - t0 if isinstance(act[2], str) else act[2]
        if kind == "emo":
            p.emotion(t, act[3], act[4] if len(act) > 4 else 1.0, act[5] if len(act) > 5 else 0.5)
        elif kind == "look":
            gaze.append((t, act[3]))
        elif kind == "blink":
            p.blink(t)
        elif kind in ("nod", "shake", "tilt", "down", "up"):
            head_moves.append((t, kind, act[3] if len(act) > 3 else 1.0, act[4] if len(act) > 4 else 0.5))
        elif kind == "noblink":
            p.no_blink.append((t, resolve_time(act[3], LINES) - t0 if isinstance(act[3], str) else act[3]))
    keys = p.compose(idle=spec.get("idle", 1.0))
    for k, v in keys.items():
        key_shape(rig, k, frames + 1, v)
    return p, gaze, head_moves


def target_point(target, rig, cam_obj, t):
    """Resolve a gaze target spec to a world point."""
    eyes = eyes_world(rig)
    fwd = forward(rig)
    if isinstance(target, (tuple, list)) and len(target) == 3 and all(isinstance(x, (int, float)) for x in target):
        return Vector(target)
    if target == "cam":
        return cam_obj.matrix_world.translation.copy()
    if isinstance(target, str) and target.startswith("@"):
        mk = bpy.data.objects[target[1:]]
        return mk.matrix_world.translation + Vector((0, 0, EYE_H))
    if isinstance(target, str) and target in bpy.data.objects and bpy.data.objects[target].type == 'ARMATURE':
        return eyes_world(bpy.data.objects[target])
    if isinstance(target, str) and target.isupper() and target not in bpy.data.objects:
        # a character who is not in this shot: look at where they stand
        mk = bpy.data.objects.get(f"MARK_{target}") or bpy.data.objects.get(f"MARK_{target}_ST")
        if mk:
            return mk.matrix_world.translation + Vector((0, 0, SET_EYE_H.get(CUR_SET[0], EYE_H)))
    if isinstance(target, str) and target in bpy.data.objects:
        return bpy.data.objects[target].matrix_world.translation.copy()
    side = Vector((-fwd.y, fwd.x, 0)).normalized()  # character's left
    table = {
        "fwd": fwd * 3.0, "down": fwd * 1.2 + Vector((0, 0, -1.4)), "down_far": fwd * 3 + Vector((0, 0, -1.2)),
        "up": fwd * 2.0 + Vector((0, 0, 1.2)), "heaven": fwd * 2.0 + Vector((0, 0, 1.7)),
        "left": side * 2.5 + fwd * 1.0, "right": -side * 2.5 + fwd * 1.0, "far": fwd * 30 + Vector((0, 0, 0.5)),
        "hand_R": None, "hand_L": None,
    }
    if target in ("hand_R", "hand_L"):
        side_c = target[-1]
        return rig.matrix_world @ rig.pose.bones[f"wrist.{side_c}"].head
    if isinstance(target, str) and target.startswith("down_"):
        return eyes + fwd * 0.9 + Vector((0, 0, -1.3)) + side * (0.8 if target.endswith("L") else -0.8)
    return eyes + table.get(target, fwd * 3.0)


def animate_gaze(shot, name, rig, gaze, head_moves, n, cam_obj, speaker_fn):
    """Key eye/head target empties: gaze holds, saccades, head lag, nods."""
    eye_t = bpy.data.objects[f"EYE_TGT_{name}"]
    head_t = bpy.data.objects[f"HEAD_TGT_{name}"]
    rng = np.random.default_rng(abs(hash((shot["id"], name, "gaze"))) % (2 ** 31))
    eyes = eyes_world(rig)
    pts = np.zeros((n, 3))
    gaze = sorted(gaze, key=lambda g: g[0])
    for f in range(n):
        t = f / FPS
        tgt = None
        for (gt, g) in gaze:
            if gt <= t:
                tgt = g
        if tgt is None:
            tgt = speaker_fn(t) or "fwd"
        pts[f] = target_point(tgt, rig, cam_obj, t)
    # saccades: small jumps between points around the target, held 0.3-1.6 s
    sac = np.zeros((n, 3))
    f = 0
    while f < n:
        hold = int(rng.uniform(0.35, 1.6) * FPS)
        dist = np.linalg.norm(pts[f] - np.array(eyes[:])) + 1e-6
        amp = 0.012 * dist / 1.0
        off = rng.normal(0, 1, 3) * amp
        off[2] *= 0.6
        sac[f:f + hold] = off
        f += hold
    eye_pts = pts + sac
    # gaze shifts snap in ~3 frames for eyes, head follows over ~0.45 s
    eye_s = eye_pts.copy()
    for f in range(1, n):
        eye_s[f] = eye_s[f - 1] + (eye_pts[f] - eye_s[f - 1]) * 0.55
    head_s = pts.copy()
    alpha = 1 - math.exp(-1.0 / (0.16 * FPS))
    for f in range(1, n):
        head_s[f] = head_s[f - 1] + (pts[f] - head_s[f - 1]) * alpha
    # nods etc. move the head target
    tsec = np.arange(n) / FPS
    for (t, kind, amt, dur) in head_moves:
        x = (tsec - t) / max(dur, 1e-3)
        env = np.where((x >= 0) & (x <= 1), np.sin(np.pi * np.clip(x, 0, 1)), 0.0)
        d = np.linalg.norm(head_s - np.array(eyes[:]), axis=1)[:, None]
        fwd = forward(rig)
        side = np.array([-fwd.y, fwd.x, 0.0])
        if kind == "nod":
            head_s[:, 2] -= (env * np.sin(np.pi * 2 * np.clip(x, 0, 1)) ** 2 * 0.25 * amt * d[:, 0])
        elif kind == "down":
            head_s[:, 2] -= env * 0.35 * amt * d[:, 0]
        elif kind == "up":
            head_s[:, 2] += env * 0.35 * amt * d[:, 0]
        elif kind == "shake":
            head_s += (side[None, :] * (np.sin(np.pi * 4 * np.clip(x, 0, 1)) * env * 0.12 * amt)[:, None] * d)
    # idle head drift
    for i, freq in enumerate((0.13, 0.11, 0.09)):
        head_s[:, i] += pf.value_noise(n, FPS, freq, 100 + i + hash(name) % 50) * 0.025
    key_vec(eye_t, "location", np.arange(n) + 1, eye_s)
    key_vec(head_t, "location", np.arange(n) + 1, head_s)
    # eyelids follow vertical gaze
    rel = eye_s - np.array(eyes[:])
    pitch = np.arctan2(rel[:, 2], np.linalg.norm(rel[:, :2], axis=1))
    down = np.clip(-pitch / 0.6, 0, 1) * 0.32
    up = np.clip(pitch / 0.5, 0, 1) * 0.4
    for side in ("Left", "Right"):
        key_shape(rig, f"eyeLookDown{side}", np.arange(n) + 1, down)
        key_shape(rig, f"eyeLookUp{side}", np.arange(n) + 1, up)


def animate_breath(rig, n, rate=0.24, amp=1.0, seed=0):
    frames = np.arange(n) + 1
    t = np.arange(n) / FPS
    ph = np.sin(2 * np.pi * rate * t + seed)
    lean = np.array(rig.get("lean", [0.0] * n))[:n]
    if len(lean) < n:
        lean = np.zeros(n)
    for bone, a, lw in (("spine03", 0.010, 0.55), ("spine02", 0.008, 0.45), ("clavicle.L", 0.010, 0.0),
                        ("clavicle.R", 0.010, 0.0)):
        pb = rig.pose.bones[bone]
        base = pb.rotation_quaternion.copy() if pb.rotation_mode == 'QUATERNION' else pb.rotation_euler.to_quaternion()
        qs = np.zeros((n, 4))
        for i in range(n):
            q = base @ Euler((a * amp * ph[i] + lw * lean[i], 0, 0)).to_quaternion()
            qs[i] = q[:]
        key_bone_quat(rig, bone, frames, qs)


# ----------------------------------------------------------------------------- camera

def hint_camera(shot, n):
    cs = shot["cam"]
    src = bpy.data.objects[cs["hint"]]
    src.hide_render = False
    src.name = "SHOTCAM"
    bpy.context.scene.camera = src
    cd = src.data
    cd.sensor_fit = 'VERTICAL'
    cd.sensor_height = 24.0
    if "lens" in cs:
        cd.lens = cs["lens"]
    if cs.get("fstop"):
        cd.dof.use_dof = True
        cd.dof.aperture_fstop = cs["fstop"]
        foc = cs.get("focus")
        if foc and foc in bpy.data.objects:
            ob = bpy.data.objects[foc]
            if ob.type == 'ARMATURE':
                fe = empty(f"FOCUS_{foc}")
                c = fe.constraints.new('COPY_LOCATION'); c.target = ob; c.subtarget = "eye.L"
                ob = fe
            cd.dof.focus_object = ob
    if cs.get("keep_anim"):
        return src
    frames = np.arange(n) + 1
    M = src.matrix_world.copy()
    p0 = M.translation.copy()
    fwdv = (M.to_3x3() @ Vector((0, 0, -1))).normalized()
    dist = (cd.dof.focus_distance if cd.dof.focus_distance > 0.01 else 1.0)
    if cd.dof.focus_object:
        dist = (cd.dof.focus_object.matrix_world.translation - p0).length
    push = cs.get("push", 0.0) * dist
    u = pf.smoothstep(np.linspace(0, 1, n))
    P = np.array(p0[:])[None, :] + np.array(fwdv[:])[None, :] * (u * push)[:, None]
    hh = cs.get("handheld", 0.15)
    seed = abs(hash(shot["id"])) % 1000
    for i in range(3):
        P[:, i] += pf.value_noise(n, FPS, 0.35, seed + i) * 0.004 * hh
    src.animation_data_clear()
    key_vec(src, "location", frames, P)
    e = src.rotation_euler.copy()
    R = np.tile(np.array(e[:]), (n, 1))
    for i in range(2):
        R[:, i] += pf.value_noise(n, FPS, 0.4, seed + 20 + i) * 0.002 * hh
    key_vec(src, "rotation_euler", frames, R)
    return src


def make_camera(shot, n, t0):
    cs = shot["cam"]
    if "hint" in cs:
        return hint_camera(shot, n)
    cd = bpy.data.cameras.new("SHOTCAM")
    cd.sensor_fit = 'VERTICAL'
    cd.sensor_height = 24.0
    cam = bpy.data.objects.new("SHOTCAM", cd)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    cd.lens = cs.get("lens", 50)
    cd.clip_start = 0.02
    cd.clip_end = 600
    pos0, tgt0 = camera_pose(cs, "start")
    pos1, tgt1 = camera_pose(cs, "end")
    frames = np.arange(n) + 1
    u = pf.smoothstep(np.linspace(0, 1, n)) if cs.get("ease", True) else np.linspace(0, 1, n)
    P = np.array(pos0)[None, :] * (1 - u[:, None]) + np.array(pos1)[None, :] * u[:, None]
    T = np.array(tgt0)[None, :] * (1 - u[:, None]) + np.array(tgt1)[None, :] * u[:, None]
    hh = cs.get("handheld", 0.25)
    seed = abs(hash(shot["id"])) % 1000
    for i in range(3):
        P[:, i] += pf.value_noise(n, FPS, 0.35, seed + i) * 0.006 * hh
        T[:, i] += pf.value_noise(n, FPS, 0.5, seed + 10 + i) * 0.012 * hh
    rots = np.zeros((n, 3))
    roll = cs.get("roll", 0.0)
    for f in range(n):
        d = Vector(T[f]) - Vector(P[f])
        q = d.to_track_quat('-Z', 'Y')
        if roll:
            q = q @ Quaternion((0, 0, 1), math.radians(roll))
        e = q.to_euler()
        rots[f] = e[:]
    # unwrap euler to avoid flips
    rots = np.unwrap(rots, axis=0)
    key_vec(cam, "location", frames, P)
    key_vec(cam, "rotation_euler", frames, rots)
    if "lens_end" in cs:
        fcurve_set(cd, "lens", 0, frames, np.linspace(cs["lens"], cs["lens_end"], n))
    # depth of field
    if cs.get("fstop", 0) > 0:
        cd.dof.use_dof = True
        cd.dof.aperture_fstop = cs["fstop"]
        foc = cs.get("focus")
        if foc and foc in bpy.data.objects and bpy.data.objects[foc].type == 'ARMATURE':
            fe = empty(f"FOCUS_{foc}")
            c = fe.constraints.new('COPY_LOCATION')
            c.target = bpy.data.objects[foc]
            c.subtarget = "eye.L"
            cd.dof.focus_object = fe
        elif foc and foc in bpy.data.objects:
            cd.dof.focus_object = bpy.data.objects[foc]
        elif isinstance(foc, (int, float)):
            cd.dof.focus_distance = foc
    return cam


def camera_pose(cs, which):
    spec = cs.get(which, cs.get("start"))
    if "frame" in spec:
        return frame_char(**spec["frame"])
    pos = Vector(spec["pos"])
    tgt = spec["target"]
    if isinstance(tgt, str):
        rig = bpy.data.objects[tgt]
        tgt = eyes_world(rig) + Vector(spec.get("toff", (0, 0, 0)))
    return tuple(pos), tuple(tgt)


def frame_char(char, size="CU", az=0.0, el=0.0, lens=85.0, zoff=0.0, side=0.0, dist=None, look_off=(0, 0, 0)):
    """Camera pose that frames a character's head; az is degrees around the character from its front."""
    rig = bpy.data.objects[char]
    eyes = eyes_world(rig)
    height = {"ECU": 0.22, "CU": 0.42, "MCU": 0.62, "MS": 1.0, "MLS": 1.5, "WS": 2.6}[size]
    fov = 2 * math.atan(12.0 / lens)
    d = dist or (height / 2) / math.tan(fov / 2)
    fwd = forward(rig)
    q = Quaternion((0, 0, 1), math.radians(az))
    dirv = q @ fwd
    center_drop = {"ECU": 0.0, "CU": 0.06, "MCU": 0.14, "MS": 0.28, "MLS": 0.5, "WS": 0.8}[size]
    tgt = eyes - Vector((0, 0, center_drop)) + Vector(look_off)
    pos = tgt + dirv * d * math.cos(math.radians(el)) + Vector((0, 0, d * math.sin(math.radians(el)) + zoff))
    sidev = Vector((-dirv.y, dirv.x, 0))
    pos += sidev * side
    return tuple(pos), tuple(tgt)


# ----------------------------------------------------------------------------- render settings

def render_settings(scn, shot, n, preview=False):
    scn.render.engine = 'CYCLES'
    c = scn.cycles
    c.device = 'CPU'
    c.samples = shot.get("samples", 5) if not preview else 3
    c.use_adaptive_sampling = True
    c.adaptive_threshold = 0.06
    c.use_denoising = True
    c.denoiser = 'OPENIMAGEDENOISE'
    c.denoising_prefilter = 'FAST'
    c.denoising_quality = 'BALANCED'
    c.max_bounces = 4
    c.diffuse_bounces = shot.get("diffuse_bounces", 1)
    c.glossy_bounces = 1
    c.transmission_bounces = 3   # eyes: cornea in + out needs >= 2
    c.transparent_max_bounces = 6
    c.caustics_reflective = False
    c.caustics_refractive = False
    c.blur_glossy = 1.0
    scn.render.use_persistent_data = True
    scn.render.resolution_x = 432 if not preview else 270
    scn.render.resolution_y = 768 if not preview else 480
    scn.cycles_curves.shape = 'RIBBONS'
    # backgrounds are mostly defocused: cap procedural texture detail (big shading-cost saver)
    trees = [m.node_tree for m in bpy.data.materials if m.use_nodes] + list(bpy.data.node_groups) + \
            [w.node_tree for w in bpy.data.worlds if w.use_nodes]
    for nt in trees:
        for nd in nt.nodes:
            if nd.type in ('TEX_NOISE', 'TEX_VORONOI', 'TEX_WAVE') and "Detail" in nd.inputs and \
                    not nd.inputs["Detail"].is_linked:
                nd.inputs["Detail"].default_value = min(nd.inputs["Detail"].default_value, 2.0)
    scn.render.resolution_percentage = 100
    scn.render.fps = FPS
    scn.frame_start = 1
    scn.frame_end = n
    scn.view_settings.view_transform = 'AgX'
    scn.view_settings.look = shot.get("look", 'AgX - Medium High Contrast')
    scn.view_settings.exposure = shot.get("exposure", 0.0)
    scn.render.image_settings.file_format = 'PNG'
    scn.render.image_settings.color_mode = 'RGB'
    scn.render.image_settings.compression = 15
    scn.render.filepath = f"/opt/work/frames/{shot['id']}/"
    scn.render.use_overwrite = False
    scn.render.use_placeholder = True
    scn.frame_step = shot.get("frame_step", 1) if not preview else 1
    for m in bpy.data.materials:
        if m.use_nodes:
            for nd in m.node_tree.nodes:
                if nd.type == 'BSDF_PRINCIPLED':
                    nd.subsurface_method = 'BURLEY'


def add_face_light(shot, rig, cam):
    """Soft motivated key + fill near the camera so faces read; spec in shot['light']."""
    ls = shot.get("light", {})
    if ls.get("none"):
        return
    eyes = eyes_world(rig)
    campos = cam.matrix_world.translation
    to_cam = (campos - eyes)
    to_cam.z = 0
    to_cam.normalize()
    side = Vector((-to_cam.y, to_cam.x, 0))
    kside = ls.get("key_side", 1.0)
    for name, off, energy, size, color in (
            ("FaceKey", to_cam * 1.1 + side * 0.9 * kside + Vector((0, 0, 0.55)), ls.get("key", 18.0), 0.9,
             ls.get("key_color", (1.0, 0.86, 0.72))),
            ("FaceFill", to_cam * 1.4 - side * 1.0 * kside + Vector((0, 0, 0.1)), ls.get("fill", 4.0), 1.6,
             ls.get("fill_color", (0.75, 0.82, 1.0))),
            ("FaceRim", -to_cam * 1.0 - side * 0.6 * kside + Vector((0, 0, 0.6)), ls.get("rim", 12.0), 0.6,
             ls.get("rim_color", (1.0, 0.92, 0.85)))):
        if energy <= 0:
            continue
        l = bpy.data.lights.new(f"{name}_{rig.name}", 'AREA')
        l.energy = energy
        l.size = size
        l.color = color
        o = bpy.data.objects.new(l.name, l)
        bpy.context.scene.collection.objects.link(o)
        o.location = eyes + off
        o.rotation_euler = (eyes - o.location).to_track_quat('-Z', 'Y').to_euler()


# ----------------------------------------------------------------------------- main

def build(shot_id, preview=False):
    shot, t0, t1 = next(b for b in shot_bounds(LINES, TL["duration"]) if b[0]["id"] == shot_id)
    CUR_SET[0] = shot["set"]
    n = max(1, int(round((t1 - t0) * FPS)))
    scn = open_set(shot["set"])
    rigs = {}
    for name, spec in shot.get("cast", {}).items():
        rig = append_character(name)
        place(rig, spec.get("mark", f"MARK_{name}"), spec.get("off", (0, 0, 0)), spec.get("rot", 0.0), spec.get("rotz"))
        rigs[name] = rig
    bpy.context.view_layer.update()
    for name, spec in shot.get("cast", {}).items():
        rig = rigs[name]
        rt.reset(rig)
        gs.base_pose(rig, spec.get("pose", "stand"), spec)
        set_clothing(rig, "sit" if spec.get("pose", "stand").startswith("sit") else "stand")
    bpy.context.view_layer.update()
    for name, rig in rigs.items():
        setup_tracking(rig)
        setup_ik(rig)
    cam = make_camera(shot, n, t0)
    bpy.context.view_layer.update()

    def speaker_at(t):
        for l in TL["lines"]:
            if l["start"] - 0.2 <= t + t0 <= l["end"] + 0.3 and l["speaker"] not in ("NARRATOR",):
                if l["scene"] in ("apartment", "sister", "door") and l["speaker"] == "JESUS":
                    continue
                return l["speaker"]
        return None

    for name, rig in rigs.items():
        spec = shot["cast"][name]
        p, gaze, head_moves = build_performance(shot, name, rig, shot["cast"], t0, n, cam)

        def default_target(t, name=name, spec=spec):
            s = speaker_at(t)
            if s and s != name:
                return s
            if s == name:
                return spec.get("addr")
            return spec.get("look")
        animate_gaze(shot, name, rig, gaze, head_moves, n, cam, default_target)
        gs.animate_gestures(shot, name, rig, n, t0, LINES, resolve_time)
        animate_breath(rig, n, amp=spec.get("breath", 1.0), seed=hash(name) % 7)
    for name, rig in rigs.items():
        if shot.get("light", {}).get("per_char", name == shot["cam"].get("focus")):
            add_face_light(shot, rig, cam)
    if "post" in shot:
        exec(shot["post"], {"bpy": bpy, "Vector": Vector, "math": math, "np": np, "rigs": rigs, "n": n,
                             "t0": t0, "LINES": LINES, "resolve_time": resolve_time, "fcurve_set": fcurve_set})
    render_settings(scn, shot, n, preview)
    os.makedirs("/opt/work/shots", exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=f"/opt/work/shots/{shot_id}{'_prev' if preview else ''}.blend")
    print("SHOT_OK", shot_id, n, "frames", round(t0, 2), round(t1, 2))


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:]
    build(argv[0], preview="--preview" in argv)
