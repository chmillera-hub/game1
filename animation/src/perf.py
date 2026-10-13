"""Performance engine: tracks of intentions -> per-frame bone/shape channels.

All times are in seconds on the global film timeline.  Character-local
("armature") space: character faces -Y, left is +X, Z up, origin on the
ground between the feet.  World placement is the armature object transform
(root track: x, y, z, heading in degrees; heading 0 = facing world -Y).
"""
import math
import numpy as np
from mathutils import Vector, Quaternion, Euler, Matrix

import rigctl

FPS = 24


def clamp(x, a, b):
    return a if x < a else b if x > b else x


def ease(u, kind='inout'):
    u = clamp(u, 0.0, 1.0)
    if kind == 'linear':
        return u
    if kind == 'in':
        return u * u * u
    if kind == 'out':
        return 1 - (1 - u) ** 3
    if kind == 'snap':
        return 1 - (1 - u) ** 5
    if kind == 'step':
        return 1.0 if u >= 1 else 0.0
    return u * u * u * (u * (6 * u - 15) + 10)  # smootherstep


def lerp(a, b, w):
    return a + (b - a) * w


def qlerp(a, b, w):
    return a.slerp(b, w)


def E(x=0, y=0, z=0):
    return Euler((math.radians(x), math.radians(y), math.radians(z))).to_quaternion()


# ---------------------------------------------------------------- tracks
class Track:
    """Latest-transition-wins keyed values.  set(t, v, dur, ease)."""

    def __init__(self, init, kind='float'):
        self.init = init
        self.kind = kind
        self.keys = []   # (start, dur, value, ease)
        self._sorted = True

    def set(self, t, v, dur=0.3, e='inout'):
        self.keys.append((float(t), max(float(dur), 1e-4), v, e))
        self._sorted = False
        return self

    def _sort(self):
        if not self._sorted:
            self.keys.sort(key=lambda k: k[0])
            self._starts = []
            self._sorted = True
            # start values
            self._sv = []
            for i, (s, d, v, e) in enumerate(self.keys):
                self._sv.append(self._eval_upto(i - 1, s))

    def _mix(self, a, b, w):
        if self.kind == 'quat':
            return a.slerp(b, w)
        if self.kind == 'float':
            return a + (b - a) * w
        return a + (b - a) * w

    def _eval_upto(self, i, t):
        if i < 0:
            return self.init
        s, d, v, e = self.keys[i]
        if t >= s + d:
            return v
        return self._mix(self._sv[i], v, ease((t - s) / d, e))

    def __call__(self, t):
        self._sort()
        # last key with start <= t
        lo, hi = 0, len(self.keys)
        while lo < hi:
            mid = (lo + hi) // 2
            if self.keys[mid][0] <= t:
                lo = mid + 1
            else:
                hi = mid
        return self._eval_upto(lo - 1, t)


class Pulse:
    """Additive one-shot shapes (nods, shakes, bounces) summed over time."""

    def __init__(self):
        self.items = []   # (t0, dur, fn) fn(u)->value (np array / float)

    def add(self, t0, dur, fn):
        self.items.append((t0, dur, fn))

    def __call__(self, t, zero):
        out = zero
        for (t0, d, fn) in self.items:
            if t0 <= t <= t0 + d:
                out = out + fn((t - t0) / d)
        return out


# ---------------------------------------------------------------- poses
class Pose(dict):
    """Body pose in armature space."""

    def blend(self, other, w):
        if w <= 0:
            return self
        if w >= 1:
            return other
        out = Pose()
        for k, a in self.items():
            b = other[k]
            if isinstance(a, Quaternion):
                out[k] = a.slerp(b, w)
            elif isinstance(a, tuple) and len(a) == 3:  # ('arm', pos, quat)
                out[k] = ('arm', a[1].lerp(b[1], w), a[2].slerp(b[2], w))
            elif isinstance(a, tuple):  # (pos, quat)
                out[k] = (a[0].lerp(b[0], w), a[1].slerp(b[1], w))
            elif isinstance(a, Vector):
                out[k] = a.lerp(b, w)
            else:
                out[k] = a + (b - a) * w
        return out

    def copy(self):
        out = Pose()
        for k, v in self.items():
            if isinstance(v, (Vector, Quaternion)):
                out[k] = v.copy()
            elif isinstance(v, tuple) and len(v) == 3:
                out[k] = (v[0], v[1].copy(), v[2].copy())
            elif isinstance(v, tuple):
                out[k] = (v[0].copy(), v[1].copy())
            elif isinstance(v, np.ndarray):
                out[k] = v.copy()
            else:
                out[k] = v
        return out


def hand_rot(fingers_dir, back_dir):
    return rigctl.hand_matrix((0, 0, 0), fingers_dir, back_dir).to_quaternion()


class Body:
    """Rest-pose geometry helpers for one character."""

    def __init__(self, C):
        self.C = C
        A = C.arm
        self.arm = A
        self.rest = {b.name: b.matrix_local.copy() for b in A.data.bones}
        self.J = C.J
        s = C.s
        self.upper = s['upper_arm']
        self.fore = s['fore_arm']
        self.armlen = self.upper + self.fore
        self.thigh = (Vector(C.J['thigh.L'][1]) - Vector(C.J['thigh.L'][0])).length
        self.shin = (Vector(C.J['shin.L'][1]) - Vector(C.J['shin.L'][0])).length
        self.hipZ = C.hipZ
        self.foot_rest = {}
        for sd in 'LR':
            m = self.rest['foot_ik.' + sd]
            self.foot_rest[sd] = (m.translation.copy(), m.to_quaternion())
        self.chain = ['hips', 'spine', 'chest', 'neck', 'head']

    def shoulder(self, sd):
        return Vector(self.J['upperarm.' + sd][0])

    def fk(self, rots, hips_loc):
        """Posed armature-space matrices of the spine chain."""
        out = {}
        parent_pose = None
        parent_rest = None
        for name in self.chain:
            R = self.rest[name]
            q = rots.get(name, Quaternion())
            if name == 'hips':
                local_off = R.to_3x3().inverted() @ hips_loc
                basis = Matrix.Translation(local_off) @ q.to_matrix().to_4x4()
                M = R @ basis
            else:
                M = parent_pose @ (parent_rest.inverted() @ R) @ q.to_matrix().to_4x4()
            out[name] = M
            parent_pose, parent_rest = M, R
        return out

    def chest_frame(self, fkm):
        """(origin, rotation) mapping rest-chest-relative offsets to posed."""
        Rr = self.rest['chest']
        Mp = fkm['chest']
        rot = (Mp.to_3x3() @ Rr.to_3x3().inverted())
        return Mp.translation.copy(), rot, Rr.translation.copy()


# ------------------------------------------------------------ postures
def _armify(B, p):
    """Convert any chest-relative hand entries of a posture into armature space."""
    need = [k for k in ('hand_L', 'hand_R') if p[k][0] == 'chest']
    if not need:
        return p
    fkm = B.fk({k: p[k] for k in ('hips', 'spine', 'chest', 'neck', 'head')}, p['hips_loc'])
    corg, crot, crest = B.chest_frame(fkm)
    for k in need:
        _, pos, rq = p[k]
        p[k] = ('arm', corg + crot @ (Vector(pos) - crest), crot.to_quaternion() @ rq)
    return p


def P_stand(B, splay=8.0, width=0.0, knee=0.0, lean=0.0, hands='hang', hips_shift=0.0, sx_bias=0.0, toes=0.0,
            bow=0.0, stoop=0.0):
    J = B.J
    p = Pose()
    p['hips_loc'] = Vector((hips_shift, 0.03 * bow / 40.0, -knee * 0.06 + toes * 0.07))
    p['hips'] = E(-lean * 0.3 + bow * 0.35)
    p['spine'] = E(lean * 0.5 + bow * 0.35 + stoop * 0.5)
    p['chest'] = E(lean * 0.5 + bow * 0.3 + stoop * 0.5)
    p['neck'] = E(-lean * 0.4 - bow * 0.15 - stoop * 0.3)
    p['head'] = E(-lean * 0.3 - bow * 0.1 - stoop * 0.2)
    p['clavicle.L'] = Quaternion()
    p['clavicle.R'] = Quaternion()
    for sd, sx in (('L', 1), ('R', -1)):
        pos, rq = B.foot_rest[sd]
        pos = pos + Vector((sx * width, 0, toes * 0.07))
        rot = E(0, 0, sx * splay) @ E(-toes * 38, 0, 0) @ rq
        p['foot_' + sd] = (pos, rot)
        kn = Vector(J['thigh.' + sd][1])
        p['kpole_' + sd] = Vector((kn.x + sx * splay * 0.006, -0.6, kn.z))
        p['apole_' + sd] = Vector((sx * 0.45, 0.45, B.hipZ + 0.25))
        p['hand_' + sd] = ('chest',) + HANDS[hands](B, sd, sx)
        p['fing_' + sd] = np.array([0.35, 0.0, 0.25])
    return _armify(B, p)


def _hang(B, sd, sx):
    sh = B.shoulder(sd)
    pos = sh + Vector((sx * 0.07, 0.035, -B.armlen * 0.92))
    return (pos, hand_rot((sx * 0.08, -0.12, -1.0), (sx, 0.15, 0)))


def _hips_hands(B, sd, sx):   # fists on hips
    pos = Vector((sx * 0.20, 0.0, B.hipZ + 0.05))
    return (pos, hand_rot((-sx * 0.6, -0.2, -0.5), (sx * 0.4, 0.2, 0.8)))


def _lap(B, sd, sx):
    pos = Vector((sx * 0.07, -0.30, B.hipZ - 0.05))
    return (pos, hand_rot((-sx * 0.3, -1.0, -0.2), (0, 0, 1)))


HANDS = {'hang': _hang, 'hips': _hips_hands, 'lap': _lap}


def P_sit_wall(B, sill=0.30, knees=0.85, back=0.12, hands='knees'):
    """Sitting on a low sill against a wall, knees drawn up (character-local)."""
    J = B.J
    p = Pose()
    hip_h = sill + 0.075
    p['hips_loc'] = Vector((0, back, hip_h - B.hipZ))
    p['hips'] = E(-62)                  # pelvis rolls back, thighs forward-up
    p['spine'] = E(30)
    p['chest'] = E(18)
    p['neck'] = E(8)
    p['head'] = E(2)
    p['clavicle.L'] = E(0, 0, -4)
    p['clavicle.R'] = E(0, 0, 4)
    for sd, sx in (('L', 1), ('R', -1)):
        pos0, rq = B.foot_rest[sd]
        fy = back - (B.thigh * 0.62 + 0.06) * knees
        pos = Vector((sx * 0.11, fy, pos0.z))
        p['foot_' + sd] = (pos, E(0, 0, sx * 6) @ rq)
        p['kpole_' + sd] = Vector((sx * 0.25, fy - 0.4, hip_h + 0.6))
        p['apole_' + sd] = Vector((sx * 0.5, 0.3, hip_h + 0.1))
        kz = hip_h + B.thigh * 0.55 * knees
        if hands == 'knees':
            p['hand_' + sd] = ('arm', Vector((sx * 0.10, fy + 0.10, kz - 0.02)), hand_rot((-sx * 0.4, -0.6, -0.6), (sx * 0.2, -0.3, 0.9)))
        else:
            p['hand_' + sd] = ('arm', Vector((sx * 0.06, back - 0.16, hip_h + 0.10)), hand_rot((-sx * 0.5, -0.8, 0.1), (0, 0, 1)))
        p['fing_' + sd] = np.array([0.45, 0.0, 0.35])
    return p


def P_kneel(B, down='R', lean=6.0, hands='hang'):
    """Kneeling on one knee ('down' knee on the ground)."""
    J = B.J
    p = Pose()
    hip_h = B.shin * 0.98 + 0.07
    p['hips_loc'] = Vector((0, 0.06, hip_h - B.hipZ))
    p['hips'] = E(-4)
    p['spine'] = E(lean * 0.6)
    p['chest'] = E(lean * 0.5)
    p['neck'] = E(-lean * 0.3)
    p['head'] = E(-lean * 0.2)
    p['clavicle.L'] = Quaternion()
    p['clavicle.R'] = Quaternion()
    for sd, sx in (('L', 1), ('R', -1)):
        pos0, rq = B.foot_rest[sd]
        if sd == down:
            # knee on ground under the hip, shin back, toes tucked
            pos = Vector((sx * 0.10, 0.06 + B.shin * 0.92, 0.07))
            p['foot_' + sd] = (pos, E(-48) @ rq)
            p['kpole_' + sd] = Vector((sx * 0.12, -0.6, 0.0))
        else:
            pos = Vector((sx * 0.13, 0.06 - B.thigh * 0.95, pos0.z))
            p['foot_' + sd] = (pos, E(0, 0, sx * 10) @ rq)
            p['kpole_' + sd] = Vector((sx * 0.15, -1.0, hip_h + 0.3))
        p['apole_' + sd] = Vector((sx * 0.45, 0.4, hip_h + 0.3))
        p['hand_' + sd] = ('chest',) + HANDS[hands](B, sd, sx)
        p['fing_' + sd] = np.array([0.35, 0.0, 0.25])
    return _armify(B, p)


def P_sit_ground(B, legs=0.9):
    p = Pose()
    hip_h = 0.09
    p['hips_loc'] = Vector((0, 0.10, hip_h - B.hipZ))
    p['hips'] = E(-70)
    p['spine'] = E(40)
    p['chest'] = E(18)
    p['neck'] = E(6)
    p['head'] = E(2)
    p['clavicle.L'] = Quaternion()
    p['clavicle.R'] = Quaternion()
    for sd, sx in (('L', 1), ('R', -1)):
        pos0, rq = B.foot_rest[sd]
        L = (B.thigh + B.shin) * legs
        pos = Vector((sx * 0.16, 0.10 - L * 0.95, 0.10))
        p['foot_' + sd] = (pos, E(-75, 0, sx * 20) @ rq)
        p['kpole_' + sd] = Vector((sx * 0.3, -0.5, 1.0))
        p['apole_' + sd] = Vector((sx * 0.5, 0.4, 0.6))
        p['hand_' + sd] = ('arm', Vector((sx * 0.26, 0.05, 0.05)), hand_rot((sx * 0.3, 0.2, -1.0), (sx * 0.5, 0.5, 0.3)))
        p['fing_' + sd] = np.array([0.2, 0.2, 0.1])
    return p


def P_fall_air(B):
    """Mid-slip: feet flying up, backside dropping, arms out."""
    p = P_sit_ground(B, legs=0.9)
    p['hips_loc'] = Vector((0, 0.15, 0.42 - B.hipZ))
    p['hips'] = E(-55)
    p['spine'] = E(20)
    p['chest'] = E(5)
    p['neck'] = E(10)
    p['head'] = E(8)
    for sd, sx in (('L', 1), ('R', -1)):
        pos, rq = B.foot_rest[sd]
        p['foot_' + sd] = (Vector((sx * 0.15, -0.55, 0.62)), E(-110, 0, sx * 15) @ rq)
        p['kpole_' + sd] = Vector((sx * 0.3, -0.8, 1.2))
        p['hand_' + sd] = ('arm', Vector((sx * 0.55, 0.05, 0.95)), hand_rot((sx, 0.2, 0.4), (0, 0.3, 1)))
        p['fing_' + sd] = np.array([0.05, 0.6, 0.0])
    return p


def P_sit_heel(B, down='R'):
    """Kneeling, sat back on the heel."""
    p = P_kneel(B, down=down, lean=2.0)
    p['hips_loc'] = p['hips_loc'] + Vector((0, 0.10, -0.12))
    p['spine'] = E(-4)
    return p


POSTURES = {'stand': P_stand, 'sit_wall': P_sit_wall, 'kneel': P_kneel, 'sit_ground': P_sit_ground,
            'fall_air': P_fall_air, 'sit_heel': P_sit_heel}


# ------------------------------------------------------------------ walk
class Walk:
    """Footstep-planted walk along a world-space polyline."""

    def __init__(self, B, t0, t1, path, stride=0.55, splay=8.0, lift=0.07, bob=0.018, sway=0.012,
                 arm=0.10, backward=False, first='L', style='walk', settle=0.25, knee=0.0, toe_pitch=12.0):
        self.B = B
        self.t0, self.t1 = t0, t1
        P = [np.array(p[:2], float) for p in path]
        self.pts = P
        seg = [np.linalg.norm(P[i + 1] - P[i]) for i in range(len(P) - 1)]
        self.cum = np.concatenate([[0], np.cumsum(seg)])
        self.L = self.cum[-1]
        self.n = max(1, int(math.ceil(self.L / stride)))
        self.step = self.L / self.n
        self.splay, self.lift, self.bob, self.sway, self.arm = splay, lift, bob, sway, arm
        self.backward = backward
        self.first = first
        self.style = style
        self.knee = knee
        self.toe_pitch = toe_pitch
        # timing: n steps, each foot moves in its own phase
        self.T = t1 - t0
        self.dstep = self.T / (self.n + 1)
        self.half_w = B.C.s['hip_w'] + 0.02

    def pos_at_dist(self, d):
        d = clamp(d, 0, self.L)
        i = int(np.searchsorted(self.cum, d, side='right') - 1)
        i = min(i, len(self.pts) - 2)
        u = (d - self.cum[i]) / max(self.cum[i + 1] - self.cum[i], 1e-9)
        p = self.pts[i] + (self.pts[i + 1] - self.pts[i]) * u
        tan = self.pts[i + 1] - self.pts[i]
        tan = tan / max(np.linalg.norm(tan), 1e-9)
        return p, tan

    def heading_of(self, tan):
        h = math.degrees(math.atan2(tan[0], -tan[1]))  # facing direction
        if self.backward:
            h += 180.0
        return h

    def dist(self, t):
        u = clamp((t - self.t0) / self.T, 0, 1)
        # mostly constant speed with short ease at both ends
        a = 0.12
        if u < a:
            f = (u * u) / (2 * a * (1 - a))
        elif u > 1 - a:
            v = 1 - u
            f = 1 - (v * v) / (2 * a * (1 - a))
        else:
            f = (u - a / 2) / (1 - a)
        return self.L * f

    def root(self, t):
        p, tan = self.pos_at_dist(self.dist(t))
        return p, self.heading_of(tan)

    def _moves(self):
        if hasattr(self, '_mv'):
            return self._mv
        other = 'R' if self.first == 'L' else 'L'
        mv = []
        last = {'L': 0.0, 'R': 0.0}
        for k in range(self.n + 1):
            foot = self.first if k % 2 == 0 else other
            tgt = min((k + 1) * self.step, self.L) if k < self.n else self.L
            mv.append((foot, last[foot], tgt))
            last[foot] = tgt
        self._mv = mv
        return mv

    def foot(self, sd, t):
        """World (x, y), lift, pitch, yaw_world of foot sd at time t."""
        mv = self._moves()
        u = (t - self.t0) / self.dstep
        k = int(math.floor(u))
        frac = u - k
        d, lift, pitch = 0.0, 0.0, 0.0
        for i, (foot, a, b) in enumerate(mv):
            if foot != sd:
                continue
            if i < k:
                d = b
            elif i == k and b > a + 1e-6:
                w = ease(frac, 'inout')
                d = a + (b - a) * w
                lift = math.sin(math.pi * frac) * self.lift
                pitch = self.toe_pitch * math.sin(2 * math.pi * frac) * 0.6
            elif i == k:
                d = b
        if t >= self.t1:
            d = self.L
            lift = pitch = 0.0
        p, tan = self.pos_at_dist(d)
        f = -tan if self.backward else tan
        left = np.array([-f[1], f[0]])
        lat = 1 if sd == 'L' else -1
        q = p + left * lat * self.half_w
        return (q[0], q[1]), lift, pitch, self.heading_of(tan)

    def phase(self, t):
        return (t - self.t0) / self.dstep

    def body(self, t, base):
        """Modify a stand pose for walking at time t."""
        p = base.copy()
        u = self.phase(t)
        env = clamp(min(t - self.t0, self.t1 - t) / 0.25, 0, 1)
        stance = 'L' if (math.floor(u) - (0 if self.first == 'L' else 1)) % 2 else 'R'
        ph = 2 * math.pi * u
        bob = -abs(math.sin(math.pi * u)) * self.bob + self.bob * 0.5
        sway = math.sin(math.pi * u + (0 if self.first == 'R' else math.pi)) * self.sway
        p['hips_loc'] = p['hips_loc'] + Vector((sway, 0, bob)) * env
        roll = math.degrees(sway) * (3.0 if self.style == 'waddle' else 1.2)
        p['hips'] = p['hips'] @ E(0, -roll * 0.8 * env, 0) if False else p['hips'] @ E(0, 0, 0)
        twist = math.sin(math.pi * u + (0 if self.first == 'R' else math.pi)) * (6 if self.style != 'waddle' else 3) * env
        p['hips'] = p['hips'] @ E(0, twist, roll * env)
        p['chest'] = p['chest'] @ E(0, -twist * 1.4, -roll * 0.8 * env)
        p['head'] = p['head'] @ E(0, twist * 0.4, roll * 0.5 * env)
        for sd, sx in (('L', 1), ('R', -1)):
            kind, pos, rq = p['hand_' + sd]
            sgn = math.sin(math.pi * u + (0 if sd == self.first else math.pi))
            if self.backward:
                sgn = -sgn
            pos = pos + Vector((0, -sgn * self.arm, abs(sgn) * self.arm * 0.25)) * env
            p['hand_' + sd] = (kind, pos, rq)
        return p


# ------------------------------------------------------------------ actor
class Actor:
    def __init__(self, C, name, seed=0, blink_rate=(2.2, 5.0), breath=1.0):
        self.C = C
        self.name = name
        self.B = Body(C)
        self.rng = np.random.default_rng(seed)
        self.root = Track(np.array([0.0, 0.0, 0.0, 0.0]), 'vec')   # x, y, z, heading
        self.walks = []
        self.postures = []    # (start, dur, fn_name, params, ease)
        self.hand = {sd: Track(None, 'obj') for sd in 'LR'}       # gesture targets
        self.hand_w = {sd: Track(0.0) for sd in 'LR'}
        self.fing = {sd: Track(None, 'obj') for sd in 'LR'}
        self.fing_w = {sd: Track(0.0) for sd in 'LR'}
        self.look = Track(None, 'obj')
        self.look_w = Track(0.0)
        self.head_add = Track(np.zeros(3), 'vec')       # pitch(+down), yaw(+left), roll(+right) degrees
        self.chest_add = Track(np.zeros(3), 'vec')
        self.hips_add = Track(np.zeros(3), 'vec')       # loc offset
        self.clav_add = {sd: Track(0.0) for sd in 'LR'}  # shrug degrees
        self.pulses_head = Pulse()
        self.pulses_chest = Pulse()
        self.pulses_hips = Pulse()
        self.face = {k: Track(v) for k, v in rigctl.FACE_DEFAULT.items()}
        self.gaze_off = Track(np.zeros(2), 'vec')       # extra yaw/pitch for eyes
        self.speech = []       # (t0, visemes dict, fps)
        self.blinks = []       # forced blink times
        self.no_auto_blink = []  # (t0, t1)
        self.breath = breath
        self.blink_rate = blink_rate
        self.tears = []

    # ------------------------------------------------ authoring helpers
    def place(self, t, x, y, heading, z=0.0, dur=0.0001, e='inout'):
        self.root.set(t, np.array([x, y, z, heading], float), dur, e)

    def turn(self, t, heading, dur=0.5):
        cur = self.root(t)
        self.root.set(t, np.array([cur[0], cur[1], cur[2], heading]), dur)

    def posture(self, t, name, dur=0.6, e='inout', **params):
        self.postures.append((t, max(dur, 1e-4), name, params, e))

    def walk(self, t0, t1, path, **kw):
        z = kw.pop('z', None)
        w = Walk(self.B, t0, t1, path, **kw)
        w.z = z
        self.walks.append(w)
        p, h = w.root(t1)
        cur = self.root(t0)
        self.root.set(t1, np.array([p[0], p[1], cur[2] if z is None else z, h]), 1e-4)
        return w

    def gesture(self, t, sd, target, dur=0.5, e='inout', weight=1.0):
        """target: ('world'|'arm'|'chest', pos, fingers_dir, back_dir)."""
        self.hand[sd].set(t, target, 1e-4, 'step')
        prev = self.hand_w[sd](t)
        if prev > 0.01:
            # cross-fade between two gesture targets: keep weight, blend positions
            self.hand[sd].keys[-1] = (t, dur, target, e)
        self.hand_w[sd].set(t, weight, dur, e)

    def release(self, t, sd, dur=0.5):
        self.hand_w[sd].set(t, 0.0, dur)

    def fingers(self, t, sd, curl, spread=0.0, thumb=None, dur=0.3, per=None):
        self.fing[sd].set(t, (curl, spread, curl * 0.7 if thumb is None else thumb, per), dur)
        self.fing_w[sd].set(t, 1.0, dur)

    def look_at(self, t, target, dur=0.4, weight=1.0, e='inout'):
        self.look.set(t, target, dur, e)
        self.look_w.set(t, weight, dur, e)
        self.blinks.append(t + 0.02)

    def expr(self, t, dur=0.4, e='inout', **ch):
        for k, v in ch.items():
            self.face[k].set(t, v, dur, e)

    def nod(self, t, amt=6.0, dur=0.5, n=1):
        self.pulses_head.add(t, dur, lambda u, a=amt, n=n: np.array([a * math.sin(math.pi * u * n) * (1 - u * 0.3), 0, 0]))

    def shake(self, t, amt=7.0, dur=0.7, n=2):
        self.pulses_head.add(t, dur, lambda u, a=amt, n=n: np.array([0, a * math.sin(2 * math.pi * u * n) * math.sin(math.pi * u), 0]))

    def tilt(self, t, amt=8.0, dur=0.8):
        self.head_add.set(t, np.array([0, 0, amt]), dur)

    def head(self, t, pitch=0.0, yaw=0.0, roll=0.0, dur=0.5, e='inout'):
        self.head_add.set(t, np.array([pitch, yaw, roll], float), dur, e)

    def chest(self, t, pitch=0.0, yaw=0.0, roll=0.0, dur=0.6, e='inout'):
        self.chest_add.set(t, np.array([pitch, yaw, roll], float), dur, e)

    def shrug(self, t, amt=12.0, dur=0.6, hold=0.2):
        for sd in 'LR':
            self.clav_add[sd].set(t, amt, dur * 0.4)
            self.clav_add[sd].set(t + dur * 0.4 + hold, 0.0, dur * 0.6)

    def shoulders(self, t, amt, dur=0.6):
        for sd in 'LR':
            self.clav_add[sd].set(t, amt, dur)

    def bounce(self, t, dur=1.0, amt=0.012, n=3):
        self.pulses_hips.add(t, dur, lambda u, a=amt, n=n: np.array([0, 0, a * abs(math.sin(math.pi * u * n)) * (1 - u)]))
        self.pulses_chest.add(t, dur, lambda u, a=amt, n=n: np.array([-120 * a * abs(math.sin(math.pi * u * n)) * (1 - u), 0, 0]))

    def breath_pulse(self, t, dur=1.4, amt=1.0):
        self.pulses_chest.add(t, dur, lambda u, a=amt: np.array([-2.5 * a * math.sin(math.pi * u), 0, 0]))
        for sd in 'LR':
            pass

    def blink(self, t):
        self.blinks.append(t)

    def say(self, t0, vis, fps=24):
        self.speech.append((t0, vis, fps))

    def hold_eyes(self, t0, t1):
        self.no_auto_blink.append((t0, t1))

    # ------------------------------------------------ evaluation
    def _posture_at(self, t, idx):
        s, d, name, params, e = self.postures[idx]
        p = POSTURES[name](self.B, **params)
        return p

    def body_pose(self, t):
        if not self.postures:
            base = P_stand(self.B)
        else:
            ps = sorted(self.postures, key=lambda k: k[0])
            k = -1
            for i, item in enumerate(ps):
                if item[0] <= t:
                    k = i
            if k < 0:
                base = POSTURES[ps[0][2]](self.B, **ps[0][3])
            else:
                base = POSTURES[ps[k][2]](self.B, **ps[k][3])
                # blend from previous chain
                cur = base
                s, d, name, params, e = ps[k]
                if t < s + d and k > 0:
                    prev = self._chain(ps, k - 1, t)
                    cur = prev.blend(base, ease((t - s) / d, e))
                base = cur
        # walking overrides
        for w in self.walks:
            if w.t0 - 0.3 <= t <= w.t1 + 0.3:
                env = clamp(min(t - (w.t0 - 0.3), (w.t1 + 0.3) - t) / 0.3, 0, 1)
                wp = w.body(clamp(t, w.t0, w.t1), base)
                base = base.blend(wp, ease(env)) if env < 1 else wp
        return base

    def _chain(self, ps, k, t):
        s, d, name, params, e = ps[k]
        p = POSTURES[name](self.B, **params)
        if t < s + d and k > 0:
            return self._chain(ps, k - 1, t).blend(p, ease((t - s) / d, e))
        return p

    def root_at(self, t):
        r = self.root(t)
        x, y, z, h = r
        for w in self.walks:
            if w.t0 <= t <= w.t1:
                p, hh = w.root(t)
                x, y, h = p[0], p[1], hh
                if w.z is not None:
                    z = w.z
        return x, y, z, h

    def root_matrix(self, t):
        x, y, z, h = self.root_at(t)
        return Matrix.Translation((x, y, z)) @ Euler((0, 0, math.radians(h))).to_matrix().to_4x4()


# ----------------------------------------------------------------- mapped tracks
def mapped(track, t, fn, mix):
    """Evaluate an 'obj' track whose values are mapped by fn(value, t) and blended by mix."""
    track._sort_obj()
    keys = track.keys
    lo, hi = 0, len(keys)
    while lo < hi:
        mid = (lo + hi) // 2
        if keys[mid][0] <= t:
            lo = mid + 1
        else:
            hi = mid
    def val(i):
        if i < 0:
            return fn(track.init, t)
        s, d, v, e = keys[i]
        cur = fn(v, t)
        if t < s + d:
            return mix(val(i - 1), cur, ease((t - s) / d, e))
        return cur
    return val(lo - 1)


def _sort_obj(self):
    if not self._sorted:
        self.keys.sort(key=lambda k: k[0])
        self._sorted = True


Track._sort_obj = _sort_obj


def _mix_pq(a, b, w):
    if a is None:
        return b
    if b is None:
        return a
    return (a[0].lerp(b[0], w), a[1].slerp(b[1], w))


def _mix_vec(a, b, w):
    if a is None:
        return b
    if b is None:
        return a
    return a.lerp(b, w)


def _mix_arr(a, b, w):
    if a is None:
        return b
    if b is None:
        return a
    return a + (b - a) * w


# ----------------------------------------------------------------- evaluation
class Resolver:
    """Resolves world-space targets that may refer to other actors."""

    def __init__(self):
        self.actors = {}
        self.cache = {}

    def head_world(self, name, t):
        key = (name, round(t * 1000))
        if key in self.cache:
            return self.cache[key]
        a = self.actors[name]
        v = a.head_world(t)
        self.cache[key] = v
        return v


RES = Resolver()


def world_point(spec, t):
    """spec: Vector | ('actor', name, part, offset) | callable(t)."""
    if spec is None:
        return None
    if callable(spec):
        return Vector(spec(t))
    if isinstance(spec, (Vector, tuple, list)) and len(spec) == 3 and not isinstance(spec[0], str):
        return Vector(spec)
    if spec[0] == 'actor':
        name, part = spec[1], spec[2]
        off = Vector(spec[3]) if len(spec) > 3 else Vector()
        a = RES.actors[name]
        if part == 'head':
            return a.head_world(t) + off
        if part == 'eyes':
            return a.head_world(t) + Vector((0, 0, 0.02)) + off
        if part == 'chest':
            M = a.root_matrix(t)
            return M @ (Vector((0, -0.08, a.B.C.neckZ - 0.12))) + off
        if part in ('hand_L', 'hand_R'):
            return a.hand_world(t, part[-1]) + off
        if part == 'root':
            M = a.root_matrix(t)
            return M.translation + off
    raise ValueError(spec)


def _actor_head_world(self, t):
    M = self.root_matrix(t)
    pose = self.body_pose(t)
    fkm = self.B.fk({k: pose[k] for k in ('hips', 'spine', 'chest', 'neck', 'head')}, pose['hips_loc'])
    h = fkm['head']
    eye = h @ Vector((0, 0.09 * self.C.s['head_scale'], 0))
    return M @ eye


def _actor_hand_world(self, t, sd):
    ev = self.evaluate(t, light=True)
    return self.root_matrix(t) @ ev['hand_arm'][sd][0]


Actor.head_world = _actor_head_world
Actor.hand_world = _actor_hand_world


def _auto_blinks(self, t_end):
    if hasattr(self, '_blink_times'):
        return self._blink_times
    times = []
    t = float(self.rng.uniform(0.3, 2.0))
    while t < t_end:
        if not any(a <= t <= b for (a, b) in self.no_auto_blink):
            times.append(t)
        t += float(self.rng.uniform(*self.blink_rate))
    times += self.blinks
    times.sort()
    # drop blinks closer than 0.35 s to the previous
    out = []
    for x in times:
        if not out or x - out[-1] > 0.35:
            out.append(x)
    self._blink_times = out
    # saccades
    sac = []
    t = 0.0
    while t < t_end:
        t += float(self.rng.uniform(0.5, 1.7))
        sac.append((t, float(self.rng.normal(0, 1.6)), float(self.rng.normal(0, 0.9))))
    self._sacc = sac
    return out


def _blink_val(self, t):
    v = 0.0
    for b in _auto_blinks(self, 10000.0):
        dt = t - b
        if -0.001 <= dt < 0.30:
            if dt < 0.07:
                x = dt / 0.07
            elif dt < 0.11:
                x = 1.0
            else:
                x = 1 - (dt - 0.11) / 0.19
            v = max(v, clamp(x, 0, 1))
        elif dt < -0.5:
            break
    return v


def _sacc_val(self, t):
    _auto_blinks(self, 10000.0)
    yaw = pitch = 0.0
    prev = (0.0, 0.0)
    for (ts, y, p) in self._sacc:
        if ts <= t:
            w = clamp((t - ts) / 0.05, 0, 1)
            yaw = prev[0] + (y - prev[0]) * w
            pitch = prev[1] + (p - prev[1]) * w
            prev = (y, p) if w >= 1 else prev
            if w < 1:
                break
        else:
            break
    return yaw, pitch


def evaluate(self, t, light=False):
    """Compute all channels at time t. Returns dict."""
    B = self.B
    C = self.C
    hs = C.s['head_scale']
    Mroot = self.root_matrix(t)
    Minv = Mroot.inverted()
    Rinv = Minv.to_quaternion()
    x, y, z, heading = self.root_at(t)
    pose = self.body_pose(t)
    # procedural idle: breathing + sway
    br = math.sin(2 * math.pi * t / 4.3 + self.rng.uniform(0, 0.01)) * self.breath
    hips_loc = pose['hips_loc'] + Vector(self.hips_add(t)) + Vector(self.pulses_hips(t, np.zeros(3)))
    hips_loc = hips_loc + Vector((0.004 * math.sin(2 * math.pi * t / 6.7 + len(self.name)), 0, 0))
    ca = self.chest_add(t) + self.pulses_chest(t, np.zeros(3))
    rots = {
        'hips': pose['hips'],
        'spine': pose['spine'] @ E(ca[0] * 0.4, ca[1] * 0.4, ca[2] * 0.4),
        'chest': pose['chest'] @ E(ca[0] * 0.6 - 0.9 * br, ca[1] * 0.6, ca[2] * 0.6),
        'neck': pose['neck'] @ E(0.5 * br, 0, 0),
        'head': pose['head'],
    }
    # walking feet
    feet = {}
    for sd, sx in (('L', 1), ('R', -1)):
        feet[sd] = pose['foot_' + sd]
    for w in self.walks:
        if w.t0 <= t <= w.t1:
            for sd, sx in (('L', 1), ('R', -1)):
                (fx, fy), lift, pitch, yaw_w = w.foot(sd, t)
                rest_pos, rq = B.foot_rest[sd]
                gz = z
                pw = Vector((fx, fy, gz + rest_pos.z + lift))
                pa = Minv @ pw
                yaw_rel = yaw_w - heading + sx * w.splay
                feet[sd] = (pa, E(0, 0, yaw_rel) @ E(pitch, 0, 0) @ rq)
    # look-at (head/neck/chest distribution)
    lw = self.look_w(t)
    look_pt = None
    if lw > 1e-3 and self.look.keys and not light:
        look_pt = mapped(self.look, t, lambda v, tt: world_point(v, tt) if v is not None else None, _mix_vec)
    fk0 = B.fk(rots, hips_loc)
    head_pos = fk0['head'] @ Vector((0, 0.09 * hs, 0))
    hd = self.head_add(t) + self.pulses_head(t, np.zeros(3))
    yaw_l = pitch_l = 0.0
    if look_pt is not None:
        tgt = Minv @ look_pt
        d = tgt - head_pos
        yaw_l = math.degrees(math.atan2(d.x, -d.y))
        pitch_l = math.degrees(math.atan2(d.z, math.hypot(d.x, d.y)))
        # existing posture orientation of the head (approx: chest forward)
        hm = fk0['head'].to_3x3()
        fwd = hm @ Vector((0, 0, 1))  # head bone local Z is forward
        cur_yaw = math.degrees(math.atan2(fwd.x, -fwd.y))
        cur_pitch = math.degrees(math.atan2(fwd.z, math.hypot(fwd.x, fwd.y)))
        yaw_l = clamp(((yaw_l - cur_yaw + 180) % 360) - 180, -80, 80) * lw
        pitch_l = clamp(pitch_l - cur_pitch, -40, 35) * lw
    # distribute (head conventions: +Y yaw left, +X pitch down)
    rots['chest'] = rots['chest'] @ E(0, yaw_l * 0.18, 0)
    rots['neck'] = rots['neck'] @ E(-pitch_l * 0.35, yaw_l * 0.32, 0)
    sway_h = 0.7 * math.sin(2 * math.pi * t / 5.3 + 1.3 * len(self.name))
    rots['head'] = rots['head'] @ E(-pitch_l * 0.6 + hd[0], yaw_l * 0.45 + hd[1] + sway_h * 0.4, hd[2] + sway_h * 0.3)
    fkm = B.fk(rots, hips_loc)
    corg, crot, crest = B.chest_frame(fkm)

    def to_arm(spec):
        kind, pos, rq = spec[0], spec[1], spec[2]
        if kind == 'arm':
            return (Vector(pos), rq)
        if kind == 'chest':
            return (corg + crot @ (Vector(pos) - crest), crot.to_quaternion() @ rq)
        if kind == 'world':
            return (Minv @ Vector(pos), Rinv @ rq)
        raise ValueError(kind)

    hands = {}
    for sd, sx in (('L', 1), ('R', -1)):
        base = to_arm(pose['hand_' + sd])
        gw = self.hand_w[sd](t)
        if gw > 1e-3 and self.hand[sd].keys:
            def fn(v, tt):
                if v is None:
                    return None
                v2 = v
                if callable(v):
                    v2 = v(tt)
                kind, pos, fd, bd = v2
                rq = hand_rot(fd, bd)
                if kind == 'world':
                    return (Minv @ Vector(pos), Rinv @ rq)
                if kind == 'chest':
                    return (corg + crot @ (Vector(pos) - crest), crot.to_quaternion() @ rq)
                if kind in ('head', 'neck', 'spine', 'hips'):
                    Mb = fkm[kind] @ B.rest[kind].inverted()
                    return (Mb @ Vector(pos), Mb.to_quaternion() @ rq)
                return (Vector(pos), rq)
            g = mapped(self.hand[sd], t, fn, _mix_pq)
            if g is not None:
                base = (base[0].lerp(g[0], gw), base[1].slerp(g[1], gw))
        # reach clamp
        sh = fkm['chest'] @ (B.rest['chest'].inverted() @ Vector(B.shoulder(sd)).to_4d()).to_3d() if False else None
        hands[sd] = base
    if light:
        return {'hand_arm': hands}
    # fingers
    fing = {}
    for sd in 'LR':
        base = pose['fing_' + sd]
        fw = self.fing_w[sd](t)
        per = None
        if fw > 1e-3 and self.fing[sd].keys:
            g = mapped(self.fing[sd], t, lambda v, tt: None if v is None else np.array(v[:3], float), _mix_arr)
            last = [k for k in self.fing[sd].keys if k[0] <= t]
            per = last[-1][2][3] if last else None
            if g is not None:
                base = base + (g - base) * fw
        fing[sd] = (base, per)
    # face
    f = {k: tr(t) for k, tr in self.face.items()}
    for (t0, vis, fps) in self.speech:
        i = int(round((t - t0) * fps))
        if 0 <= i < len(vis['jaw']):
            f['jaw'] = f['jaw'] + vis['jaw'][i] * 0.95
            f['wide'] = max(f['wide'], 0) + vis['wide'][i] * 0.7
            f['round'] = f['round'] + vis['round'][i] * 0.8
            f['press'] = max(f['press'], vis['press'][i])
            f['lip_raise'] = f['lip_raise'] + vis['lip_raise'][i] * 0.5
            f['brow'] = f['brow'] + 0.10 * vis['jaw'][i]
    bl = _blink_val(self, t)
    f['blink'] = max(f['blink'], bl)
    # eyes: aim at the look target from the posed head
    sy, sp = _sacc_val(self, t)
    go = self.gaze_off(t)
    gyaw, gpitch = f['gaze_yaw'] + sy + go[0], f['gaze_pitch'] + sp + go[1]
    if look_pt is not None:
        tgt = Minv @ look_pt
        Mh = fkm['head']
        Rh = B.rest['head']
        for side in ('L',):
            Re = B.rest['eye_' + side]
            Me = Mh @ (Rh.inverted() @ Re)
            loc = Me.inverted() @ tgt
            ey = math.degrees(math.atan2(-loc.x, loc.y))
            ep = math.degrees(math.atan2(loc.z, math.hypot(loc.x, loc.y)))
            gyaw += clamp(ey, -35, 35) * lw
            gpitch += clamp(ep, -30, 30) * lw
    f['gaze_yaw'], f['gaze_pitch'] = gyaw, gpitch
    bones, shapes = rigctl.face_to_channels(f, hs)
    out_b = {}
    for b, (kind, v) in bones.items():
        out_b[b] = (kind, v)
    # spine chain
    for n in ('hips', 'spine', 'chest', 'neck', 'head'):
        out_b[n] = ('rot', rots[n])
    out_b['hips'] = ('locrot', (B.rest['hips'].to_3x3().inverted() @ hips_loc, rots['hips']))
    shrug = {sd: self.clav_add[sd](t) for sd in 'LR'}
    out_b['clavicle.L'] = ('rot', pose['clavicle.L'] @ E(0, 0, shrug['L'] + 0.8 * br))
    out_b['clavicle.R'] = ('rot', pose['clavicle.R'] @ E(0, 0, -shrug['R'] - 0.8 * br))
    # IK controls
    def ik(name, pos, rq=None):
        R = B.rest[name]
        M = (rq.to_matrix().to_4x4() if rq is not None else R.to_3x3().to_4x4())
        M.translation = pos
        basis = R.inverted() @ M
        l, r, s_ = basis.decompose()
        out_b[name] = ('locrot', (l, r))
    for sd in 'LR':
        ik('hand_ik.' + sd, hands[sd][0], hands[sd][1])
        ik('foot_ik.' + sd, feet[sd][0], feet[sd][1])
        ik('knee_pole.' + sd, pose['kpole_' + sd])
        ap = pose['apole_' + sd]
        ik('arm_pole.' + sd, corg + crot @ (ap - crest) if True else ap)
    # fingers
    for sd in 'LR':
        (curl, spread, thumb), per = fing[sd]
        for i, fn_ in enumerate(('index', 'middle', 'ring', 'pinky')):
            c = per.get(fn_, curl) if per else curl
            sp_ = spread * (1.5 - i) * 6.0
            out_b['%s1.%s' % (fn_, sd)] = ('rot', E(-c * 70, 0, sp_ if sd == 'L' else -sp_))
            out_b['%s2.%s' % (fn_, sd)] = ('rot', E(-c * 85))
            out_b['%s3.%s' % (fn_, sd)] = ('rot', E(-c * 55))
        out_b['thumb1.' + sd] = ('rot', E(-thumb * 20))
        out_b['thumb2.' + sd] = ('rot', E(-thumb * 35))
        out_b['thumb3.' + sd] = ('rot', E(-thumb * 40))
    return {'root': (x, y, z, heading), 'bones': out_b, 'shapes': shapes, 'hand_arm': hands,
            'head_world': Mroot @ head_pos}


Actor.evaluate = evaluate


# ----------------------------------------------------------------- baking
def bake(actor, f0, f1, fps=FPS):
    """Write keyframes for frames f0..f1 (inclusive) on the actor's rig."""
    import bpy
    C = actor.C
    arm = C.arm
    frames = list(range(f0, f1 + 1))
    data = {}
    def put(path, idx, grp, f, v):
        data.setdefault((path, idx, grp), []).append((f, v))
    for fr in frames:
        t = fr / fps
        ev = actor.evaluate(t)
        x, y, z, h = ev['root']
        put('location', 0, 'root', fr, x)
        put('location', 1, 'root', fr, y)
        put('location', 2, 'root', fr, z)
        put('rotation_euler', 2, 'root', fr, math.radians(h))
        for b, (kind, v) in ev['bones'].items():
            pb = 'pose.bones["%s"]' % b
            if kind == 'rot':
                for i in range(4):
                    put(pb + '.rotation_quaternion', i, b, fr, v[i])
            elif kind == 'loc':
                for i in range(3):
                    put(pb + '.location', i, b, fr, v[i])
            else:
                l, r = v
                for i in range(3):
                    put(pb + '.location', i, b, fr, l[i])
                for i in range(4):
                    put(pb + '.rotation_quaternion', i, b, fr, r[i])
        for k, v in ev['shapes'].items():
            put('key_blocks["%s"].value' % k, 0, 'SHAPE', fr, v)
    act = bpy.data.actions.new(actor.name + '_act')
    sact = bpy.data.actions.new(actor.name + '_shapes')
    for (path, idx, grp), kv in data.items():
        a = sact if grp == 'SHAPE' else act
        fc = a.fcurves.new(path, index=idx, action_group=grp if grp != 'SHAPE' else 'shapes')
        arr = np.array(kv, dtype=np.float32).reshape(-1)
        fc.keyframe_points.add(len(kv))
        fc.keyframe_points.foreach_set('co', arr)
        fc.keyframe_points.foreach_set('interpolation', np.ones(len(kv), dtype=np.int32))
        fc.update()
    arm.animation_data_create().action = act
    key = C.head.data.shape_keys
    key.animation_data_create().action = sact
    return act
