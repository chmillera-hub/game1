"""Base poses and hand gestures (IK targets) for MakeHuman 'default' rigs.

Character-local frame: -Y forward, +X = the character's LEFT, Z up, origin at the feet.
Gesture actions in shots.py: (CHAR, "gest", time, SIDE, NAME, ramp) with SIDE in "L", "R", "LR".
Other body actions: (CHAR, "lean", time, degrees, ramp), (CHAR, "move", t0, t1, (dx, dy, dz)),
(CHAR, "tremble", t0, t1, amount), (CHAR, "prop", time, PROP_OBJECT, SIDE) to put an object in a hand,
(CHAR, "drop", time, PROP_OBJECT) to let it fall.
"""
import bpy, math
import numpy as np
from mathutils import Vector, Quaternion, Euler, Matrix
import rigtools as rt
import perform as pf

FPS = 24


def L(rig, v):
    """character-local -> world point"""
    return rig.matrix_world @ Vector(v)


def Ld(rig, v):
    return (rig.matrix_world.to_3x3() @ Vector(v)).normalized()


def aim_local(rig, bone, d):
    rt.aim(rig, bone, Ld(rig, d))


def height_scale(rig):
    eye = rig.matrix_world.inverted() @ (rig.matrix_world @ rig.pose.bones["eye.L"].head)
    return eye.z / 1.65


# ----------------------------------------------------------------------------- base poses

def base_pose(rig, pose, spec):
    rt.reset(rig)
    hs = 1.0
    if pose in ("stand", "stand_clasped", "lean_in"):
        rt.arms_down(rig, out=0.10, forward=0.05, elbow=0.22)
        if pose == "lean_in":
            rt.rotate_world(rig, "spine03", Ld(rig, (1, 0, 0)), math.radians(6))
    elif pose == "sit_floor":
        drop = spec.get("drop", 0.74)
        rig.location.z -= drop
        bpy.context.view_layer.update()
        for side, s in (("L", 1), ("R", -1)):
            aim_local(rig, f"upperleg01.{side}", (0.55 * s, -0.83, 0.05))
            aim_local(rig, f"upperleg02.{side}", (0.55 * s, -0.83, 0.05))
            aim_local(rig, f"lowerleg01.{side}", (-0.88 * s, -0.35, -0.12))
            aim_local(rig, f"lowerleg02.{side}", (-0.88 * s, -0.35, -0.12))
            aim_local(rig, f"foot.{side}", (-0.5 * s, -0.6, -0.4))
        rt.rotate_world(rig, "spine05", Ld(rig, (1, 0, 0)), math.radians(4))
        rt.arms_down(rig, out=0.18, forward=0.6, elbow=0.9)
    elif pose == "sit_couch":
        drop = spec.get("drop", 0.43)
        rig.location.z -= drop
        bpy.context.view_layer.update()
        for side, s in (("L", 1), ("R", -1)):
            aim_local(rig, f"upperleg01.{side}", (0.08 * s, -1.0, 0.04))
            aim_local(rig, f"upperleg02.{side}", (0.08 * s, -1.0, 0.04))
            aim_local(rig, f"lowerleg01.{side}", (0.03 * s, -0.18, -1.0))
            aim_local(rig, f"lowerleg02.{side}", (0.03 * s, -0.18, -1.0))
            aim_local(rig, f"foot.{side}", (0.0, -0.9, -0.3))
        rt.rotate_world(rig, "spine05", Ld(rig, (1, 0, 0)), math.radians(-8))
        rt.rotate_world(rig, "spine03", Ld(rig, (1, 0, 0)), math.radians(6))
        rt.arms_down(rig, out=0.12, forward=0.5, elbow=0.9)
    elif pose == "crouch":
        rig.location.z -= spec.get("drop", 0.42)
        bpy.context.view_layer.update()
        for side, s in (("L", 1), ("R", -1)):
            aim_local(rig, f"upperleg01.{side}", (0.14 * s, -0.85, -0.22))
            aim_local(rig, f"upperleg02.{side}", (0.14 * s, -0.85, -0.22))
            aim_local(rig, f"lowerleg01.{side}", (0.02 * s, 0.25, -1.0))
            aim_local(rig, f"lowerleg02.{side}", (0.02 * s, 0.25, -1.0))
            aim_local(rig, f"foot.{side}", (0.0, -0.9, -0.35))
        rt.rotate_world(rig, "spine05", Ld(rig, (1, 0, 0)), math.radians(38))
        rt.rotate_world(rig, "spine03", Ld(rig, (1, 0, 0)), math.radians(18))
        rt.arms_down(rig, out=0.10, forward=0.6, elbow=0.3)
    rt.update()
    # remember FK pose quats so other layers can compose with them
    rig["base_quats"] = {pb.name: list(pb.rotation_quaternion) for pb in rig.pose.bones}


# ----------------------------------------------------------------------------- gesture library

def chest_z(rig):
    return (rig.matrix_world.inverted() @ (rig.matrix_world @ rig.pose.bones["spine01"].head)).z


def gesture_targets(rig, name, side):
    """Return (local target point or None for FK, finger curl, wrist euler) for one hand."""
    s = 1 if side == "L" else -1
    eye_l = rig.matrix_world.inverted() @ (rig.matrix_world @ rig.pose.bones["eye.L"].head)
    ez = eye_l.z
    cz = chest_z(rig)
    tbl = {
        "rest": (None, 0.25, (0, 0, 0)),
        "chest": ((0.03 * s, -0.17, cz - 0.08), 0.15, (0, 0, 0)),
        "heart": ((0.06 * s, -0.16, cz - 0.1), 0.2, (0, 0, 0)),
        "palms_open": ((0.27 * s, -0.33, cz - 0.42), 0.05, (0, -1.3 * s, 0)),
        "palm_up": ((0.12 * s, -0.36, cz - 0.3), 0.05, (0, -1.4 * s, 0)),
        "offer": ((0.18 * s, -0.42, cz - 0.25), 0.08, (0, -1.0 * s, 0)),
        "stone_hold": ((0.10 * s, -0.27, cz - 0.42), 0.62, (0, 0, 0)),
        "stone_chest": ((0.08 * s, -0.30, cz - 0.2), 0.62, (0, 0, 0)),
        "stone_raise": ((0.24 * s, -0.08, ez + 0.02), 0.62, (0, 0, 0)),
        "stone_open": ((0.10 * s, -0.29, cz - 0.42), 0.0, (0, -0.4 * s, 0)),
        "point": ((0.12 * s, -0.58, cz - 0.05), "point", (0, 0, 0)),
        "reach": ((0.10 * s, -0.66, cz - 0.08), 0.1, (0, 0, 0)),
        "grab": ((0.10 * s, -0.66, cz - 0.08), 1.0, (0, 0, 0)),
        "fist": ((0.10 * s, -0.30, cz - 0.38), 1.0, (0, 0, 0)),
        "knuckles_mouth": ((0.02 * s, -0.13, ez - 0.10), 0.85, (0, 0, 0)),
        "fingers_mouth": ((0.015 * s, -0.12, ez - 0.09), 0.3, (0, 0, 0)),
        "phone_face": ((0.035 * s, -0.30, ez - 0.30), 0.45, (0, -0.6 * s, 0)),
        "phone_low": ((0.06 * s, -0.33, ez - 0.48), 0.45, (0, -0.8 * s, 0)),
        "phone_ear": ((0.09 * s, -0.04, ez - 0.03), 0.55, (0, 0, 0)),
        "lap": ((0.10 * s, -0.30, cz - 0.55), 0.35, (0, -0.4 * s, 0)),
        "table": ((0.17 * s, -0.42, cz - 0.42), 0.25, (0, 0, 0)),
        "pray": ((0.01 * s, -0.25, cz - 0.15), 0.15, (0, 0, 0)),
        "clasp": ((0.04 * s, -0.20, cz - 0.45), 0.5, (0, 0, 0)),
    }
    return tbl.get(name, tbl["rest"])


def finger_curl(rig, side, curl):
    """Return dict bone -> quaternion for a curl amount or preset."""
    out = {}
    for i in range(1, 6):
        if curl == "point":
            c = 0.0 if i == 2 else (0.5 if i == 1 else 0.95)
        else:
            c = float(curl) * (0.45 if i == 1 else 1.0)
        for j in range(1, 4):
            a = c * (1.2 if j > 1 else 0.85) * math.radians(75)
            out[f"finger{i}-{j}.{side}"] = Euler((a, 0, 0)).to_quaternion()
    return out


def world_target(rig, tspec):
    """('bone', CHAR, BONE, (dx,dy,dz)) -> world point (offset in that char's local frame)."""
    _, ch, bone, off = tspec
    other = bpy.data.objects[ch]
    p = other.matrix_world @ other.pose.bones[bone].head
    return p + other.matrix_world.to_3x3() @ Vector(off)


def animate_gestures(shot, name, rig, n, t0, LINES, resolve_time):
    acts = [a for a in shot.get("act", []) if a[0] == name]
    tsec = np.arange(n) / FPS
    frames = np.arange(n) + 1

    def T(x):
        return resolve_time(x, LINES) - t0 if isinstance(x, str) else float(x)

    spec = shot["cast"][name]
    init = spec.get("hands", {})
    for side in ("L", "R"):
        events = []
        g0 = init.get(side, "rest") if isinstance(init, dict) else init
        events.append((-1.0, g0, 0.01))
        for a in acts:
            if a[1] == "gest" and side in a[3]:
                events.append((T(a[2]), a[4], a[5] if len(a) > 5 else 0.5))
        events.sort(key=lambda e: e[0])
        pos = np.zeros((n, 3))
        infl = np.zeros(n)
        curl = {}
        wrist = np.zeros((n, 4))
        states = []
        for (t, g, ramp) in events:
            if isinstance(g, tuple) and g[0] == "bone":
                p = world_target(rig, g)
                states.append((t, ramp, p, 1.0, 0.3, (0, 0, 0)))
                continue
            lp, c, we = gesture_targets(rig, g, side)
            if lp is None:
                hand = rig.matrix_world @ rig.pose.bones[f"wrist.{side}"].head
                states.append((t, ramp, hand, 0.0, c, we))
            else:
                states.append((t, ramp, L(rig, lp), 1.0, c, we))
        base = rig.get("base_quats", {})
        fingers_seq = [finger_curl(rig, side, st[4]) for st in states]
        fbones = list(fingers_seq[0].keys())
        fq = {b: np.zeros((n, 4)) for b in fbones}
        for f in range(n):
            t = tsec[f]
            k = 0
            for i, st in enumerate(states):
                if st[0] <= t:
                    k = i
            cur = states[k]
            prev = states[k - 1] if k > 0 else cur
            u = float(pf.smoothstep(np.array([(t - cur[0]) / max(cur[1], 1e-3)]))[0]) if k > 0 else 1.0
            pp = prev[2] if prev[3] > 0 or cur[3] == 0 else cur[2]
            pc = cur[2] if cur[3] > 0 or prev[3] == 0 else prev[2]
            pos[f] = np.array(pp) * (1 - u) + np.array(pc) * u
            infl[f] = prev[3] * (1 - u) + cur[3] * u
            wq = Euler(prev[5]).to_quaternion().slerp(Euler(cur[5]).to_quaternion(), u)
            bw = Quaternion(base.get(f"wrist.{side}", (1, 0, 0, 0)))
            wrist[f] = (bw @ wq)[:]
            for b in fbones:
                q = fingers_seq[k - 1 if k > 0 else k][b].slerp(fingers_seq[k][b], u)
                fq[b][f] = q[:]
        # trembling / body moves that affect hands
        for a in acts:
            if a[1] == "tremble" and (len(a) < 6 or side in a[5]):
                ta, tb, amt = T(a[2]), T(a[3]), a[4]
                m = (tsec >= ta) & (tsec <= tb)
                for i in range(3):
                    pos[m, i] += pf.value_noise(n, FPS, 7.0, 300 + i + (side == "L"))[m] * 0.004 * amt
        tgt = bpy.data.objects[f"HAND_{side}_{name}"]
        from shotbuild import key_vec, fcurve_set, key_bone_quat
        key_vec(tgt, "location", frames, pos)
        fcurve_set(rig, f'pose.bones["lowerarm02.{side}"].constraints["IK"].influence', 0, frames, infl)
        key_bone_quat(rig, f"wrist.{side}", frames, wrist)
        for b in fbones:
            key_bone_quat(rig, b, frames, fq[b])
    # root moves (steps, escape) and leaning
    from shotbuild import key_vec
    loc = np.tile(np.array(rig.location[:]), (n, 1))
    moved = False
    for a in acts:
        if a[1] == "move":
            ta, tb, d = T(a[2]), T(a[3]), a[4]
            u = pf.smoothstep((tsec - ta) / max(tb - ta, 1e-3))
            wd = np.array((rig.matrix_world.to_3x3() @ Vector(d))[:])
            loc += u[:, None] * wd[None, :]
            if a[5:] and a[5] == "walk":
                walking = (tsec > ta) & (tsec < tb)
                loc[walking, 2] += np.abs(np.sin(np.pi * 2 * 0.9 * (tsec[walking] - ta))) * 0.025
            moved = True
    if moved:
        key_vec(rig, "location", frames, loc)
    lean = np.zeros(n)
    for a in acts:
        if a[1] == "lean":
            t, deg, ramp = T(a[2]), a[3], a[4] if len(a) > 4 else 0.6
            lean = lean * (1 - pf.smoothstep((tsec - t) / ramp)) + math.radians(deg) * pf.smoothstep((tsec - t) / ramp)
    rig["lean"] = lean.tolist()
    # props in hands
    for a in acts:
        if a[1] == "prop":
            ob = bpy.data.objects[a[3]]
            side = a[4]
            c = ob.constraints.new('CHILD_OF')
            c.target = rig
            c.subtarget = f"wrist.{side}"
            c.set_inverse_pending = False
            # place object in the palm: offset along the hand bone
            pb = rig.pose.bones[f"wrist.{side}"]
            M = rig.matrix_world @ pb.matrix
            palm = M @ Vector((0, pb.length * 0.9, -0.02))
            c.inverse_matrix = M.inverted()
            ob.location = palm
        if a[1] == "drop":
            ob = bpy.data.objects[a[3]]
            td = T(a[2])
            fd = int(td * FPS) + 1
            for c in ob.constraints:
                if c.type == 'CHILD_OF':
                    fcurve_set_local(c, "influence", [1, fd - 1, fd], [1.0, 1.0, 0.0])
            # free fall after release (world space), with a small bounce
            start = Vector(a[4]) if len(a) > 4 else ob.matrix_world.translation.copy()
            fl = []
            vals = []
            for f in range(fd, n + 1):
                tt = (f - fd) / FPS
                z = start.z - 0.5 * 9.81 * tt * tt
                if z < 0.06:
                    z = 0.06
                fl.append(f)
                vals.append((start.x, start.y, z))
            if fl:
                from shotbuild import fcurve_set
                for i in range(3):
                    fcurve_set(ob, "location", i, np.array(fl), np.array([v[i] for v in vals]))


def fcurve_set_local(con, prop, frames, values):
    for f, v in zip(frames, values):
        setattr(con, prop, v)
        con.keyframe_insert(prop, frame=f)
