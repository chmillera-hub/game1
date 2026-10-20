"""Posing helpers for the MakeHuman 'default' rig (armature space, Z up, character faces -Y).

All functions work on pose bones by assigning armature-space matrices, parent-first, so callers can
think in world directions: aim_chain(rig, ["upperarm01.L", "upperarm02.L"], Vector((0.1, 0, -1))).
"""
import bpy
from mathutils import Vector, Matrix, Quaternion, Euler

ARM_CHAIN = ["upperarm01", "upperarm02"]
FOREARM_CHAIN = ["lowerarm01", "lowerarm02"]
SPINE = ["spine05", "spine04", "spine03", "spine02", "spine01"]
NECK = ["neck01", "neck02", "neck03"]
FINGERS = [f"finger{i}-{j}" for i in range(1, 6) for j in range(1, 4)]


def update():
    bpy.context.view_layer.update()


def reset(rig):
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)
        pb.scale = (1, 1, 1)
    update()


def rig_space(rig, v):
    """World direction -> armature-space direction (rigs are only rotated about Z)."""
    return (rig.matrix_world.to_3x3().inverted() @ Vector(v)).normalized()


def aim(rig, bone, direction, roll_keep=True):
    pb = rig.pose.bones[bone]
    M = pb.matrix.copy()
    cur = Vector(M.col[1][:3]).normalized()
    d = rig_space(rig, direction)
    q = cur.rotation_difference(d)
    R = q.to_matrix().to_4x4() @ Matrix(M.to_3x3()).to_4x4()
    R.translation = M.translation
    pb.matrix = R
    update()


def aim_chain(rig, bones, direction):
    for b in bones:
        aim(rig, b, direction)


def rotate_world(rig, bone, axis, angle):
    """Rotate a bone about a world axis through its head (keeps children following)."""
    pb = rig.pose.bones[bone]
    M = pb.matrix.copy()
    q = Quaternion(rig_space(rig, axis), angle)
    R = q.to_matrix().to_4x4() @ Matrix(M.to_3x3()).to_4x4()
    R.translation = M.translation
    pb.matrix = R
    update()


def curl_fingers(rig, side, amount=0.4, thumb=0.2, spread=0.0):
    """Curl fingers by rotating about each bone's local X (MakeHuman finger bones bend about X)."""
    import math
    for i in range(1, 6):
        for j in range(1, 4):
            pb = rig.pose.bones.get(f"finger{i}-{j}.{side}")
            if not pb:
                continue
            pb.rotation_mode = 'QUATERNION'
            a = (thumb if i == 1 else amount) * (1.25 if j > 1 else 0.9) * math.radians(70)
            pb.rotation_quaternion = Euler((a, 0, 0)).to_quaternion()
    update()


def arms_down(rig, out=0.12, forward=0.06, elbow=0.25):
    for side, s in (("L", 1), ("R", -1)):
        aim_chain(rig, [f"{b}.{side}" for b in ARM_CHAIN], Vector((out * s, forward * 0.3, -1)))
        aim_chain(rig, [f"{b}.{side}" for b in FOREARM_CHAIN], Vector((out * 0.4 * s, -elbow, -1)))
        aim(rig, f"wrist.{side}", Vector((out * 0.3 * s, -elbow * 0.6, -1)))
        curl_fingers(rig, side, 0.25, 0.1)


def key_pose(rig, frame, bones=None):
    for pb in rig.pose.bones:
        if bones and pb.name not in bones:
            continue
        pb.keyframe_insert("rotation_quaternion", frame=frame)
