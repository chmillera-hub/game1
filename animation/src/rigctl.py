"""High-level controls: face params and body pose -> bone/shape-key values.

Conventions (verified by probing the rig):
  jaw opens with NEGATIVE local-X rotation
  eye: +Z = look to the character's left, +X = look up
  lids: +X moves the lid edge up (upper lid opens / lower lid rises)
  head/neck/spine: +X = bend forward, +Y = turn to character's left, +Z = tilt to character's right
  fingers: negative X = curl toward the palm
  IK poles: pole_angle 90 so the elbow/knee points at its pole bone
"""
import math
import numpy as np
from mathutils import Euler, Quaternion, Matrix, Vector

FACE_DEFAULT = dict(
    jaw=0.0, wide=0.0, round=0.0, press=0.0, pout=0.0, lip_raise=0.0,
    smile=0.0, smirk=0.0,
    brow=0.0, brow_in=0.0, brow_asym=0.0,
    lid_L=1.0, lid_R=1.0, lidlo_L=0.0, lidlo_R=0.0, blink=0.0,
    gaze_yaw=0.0, gaze_pitch=0.0,
    sneer=0.0,
)

UP_CLOSE = 46.0   # degrees to fully close the upper lid
LO_RAISE = 14.0


def q(x=0.0, y=0.0, z=0.0):
    return Euler((math.radians(x), math.radians(y), math.radians(z))).to_quaternion()


def face_to_channels(f, hs=1.0):
    """Return dict: bone -> ('rot', quat) / ('loc', vec); shape -> value."""
    out_b, out_s = {}, {}
    k = 2.4 * hs
    out_b['jaw'] = ('rot', q(-18.0 * f['jaw'] - 2.0 * f['round'] * 0.0))
    sm = f['smile']
    sL = max(sm, 0) * (1 + f['smirk'])
    sR = max(sm, 0) * (1 - f['smirk'])
    fL = max(-sm, 0) * (1 + f['smirk'] * 0.5)
    fR = max(-sm, 0) * (1 - f['smirk'] * 0.5)
    out_s.update(dict(wide=f['wide'], round=f['round'], press=f['press'], pout=f['pout'],
                      lip_raise=f['lip_raise'] + f['sneer'], smile_L=sL, smile_R=sR, frown_L=fL, frown_R=fR))
    # brows: in/mid/out bone translation (local Z = up, metres)
    for side, sg in (('L', 1), ('R', -1)):
        b = f['brow'] + sg * f['brow_asym']
        bi = f['brow_in']
        out_b['brow_in_' + side] = ('loc', Vector((0, 0, k * (0.0060 * b + 0.0060 * bi))))
        out_b['brow_mid_' + side] = ('loc', Vector((0, 0, k * (0.0070 * b + 0.0018 * bi))))
        out_b['brow_out_' + side] = ('loc', Vector((0, 0, k * (0.0050 * b - 0.0032 * bi))))
    # eyes
    yaw, pitch = f['gaze_yaw'], f['gaze_pitch']
    for side in ('L', 'R'):
        out_b['eye_' + side] = ('rot', q(pitch, 0, yaw))
        op = f['lid_' + side] * (1 - f['blink'])
        up = -(1 - op) * UP_CLOSE if op <= 1 else (op - 1) * 30.0
        # the last stretch of a close overshoots so the lids seal at the centre
        c = min(max((1 - op - 0.75) / 0.25, 0.0), 1.0)
        up -= 11.0 * c * c * (3 - 2 * c)
        # lids follow the gaze up/down so the iris stays framed; the coupling fades out as the lid
        # closes, so a blink (or shut eyes) seals the same way whatever the eyes are doing
        g = min(max(op, 0.0), 1.0)
        up += (0.50 * min(pitch, 0) + 0.65 * max(pitch, 0)) * g
        lo = f['lidlo_' + side] * LO_RAISE * (1 - f['blink']) + f['blink'] * 8.0
        lo += (0.3 * min(pitch, 0) + 0.2 * max(pitch, 0)) * g + max(f['smile'], 0) * 5.0
        out_b['lid_up_' + side] = ('rot', q(up))
        out_b['lid_lo_' + side] = ('rot', q(lo))
    return out_b, out_s


def apply_face(C, f):
    ff = dict(FACE_DEFAULT)
    ff.update(f)
    ob, os_ = face_to_channels(ff, C.s['head_scale'])
    pb = C.arm.pose.bones
    for b, (kind, v) in ob.items():
        if kind == 'rot':
            pb[b].rotation_quaternion = v
        else:
            pb[b].location = v
    kb = C.head.data.shape_keys.key_blocks
    for k, v in os_.items():
        kb[k].value = v


def set_bone_matrix_rootchild(arm, name, M_arm):
    """For bones parented to the (never posed) root: basis = rest^-1 @ M."""
    b = arm.data.bones[name]
    basis = b.matrix_local.inverted() @ M_arm
    pb = arm.pose.bones[name]
    loc, rot, sc = basis.decompose()
    pb.location = loc
    pb.rotation_quaternion = rot
    return loc, rot


def hand_matrix(pos, fingers_dir, back_dir):
    """Armature-space matrix for a hand_ik bone: Y along fingers, Z = back of hand."""
    y = Vector(fingers_dir).normalized()
    z = Vector(back_dir)
    z = (z - y * z.dot(y)).normalized()
    x = y.cross(z)
    M = Matrix((x, y, z)).transposed().to_4x4()
    M.translation = Vector(pos)
    return M


def foot_matrix(arm, side, pos, yaw=0.0, pitch=0.0):
    b = arm.data.bones['foot_ik.' + side]
    R = Euler((math.radians(pitch), 0, math.radians(yaw))).to_matrix().to_4x4()
    rest = b.matrix_local.copy()
    rot = R @ rest.to_3x3().to_4x4()
    rot.translation = Vector(pos)
    return rot


def finger_curl(pb, side, curl, spread=0.0, thumb=None, per=None):
    """curl 0..1 for all fingers (or per-finger dict)."""
    for i, f in enumerate(('index', 'middle', 'ring', 'pinky')):
        c = per.get(f, curl) if per else curl
        sp = spread * (1.5 - i) * 6.0
        pb['%s1.%s' % (f, side)].rotation_quaternion = q(-c * 70, 0, sp if side == 'L' else -sp)
        pb['%s2.%s' % (f, side)].rotation_quaternion = q(-c * 85)
        pb['%s3.%s' % (f, side)].rotation_quaternion = q(-c * 55)
    t = curl * 0.6 if thumb is None else thumb
    pb['thumb1.' + side].rotation_quaternion = q(-t * 20, 0, 0)
    pb['thumb2.' + side].rotation_quaternion = q(-t * 35)
    pb['thumb3.' + side].rotation_quaternion = q(-t * 40)
