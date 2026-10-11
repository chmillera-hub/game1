"""Keyframe timeline: tweened tracks per actor + automatic life (blinks,
saccades, breathing, lip-sync hooks, walking, eating)."""
import bisect
import math
import random
from rig import DEFAULTS, DISCRETE, DESIGNS, state_for, _arm_points
from robot import BOT_DEFAULTS, BOT_DISCRETE
from gfx import hash01, noise1


def ease(u, kind='io'):
    u = max(0.0, min(1.0, u))
    if kind == 'lin':
        return u
    if kind == 'in':
        return u * u * u
    if kind == 'out':
        return 1 - (1 - u) ** 3
    if kind == 'back':        # overshoot
        c1, c3 = 1.70158, 2.70158
        return 1 + c3 * (u - 1) ** 3 + c1 * (u - 1) ** 2
    if kind == 'snap':
        return 1 - (1 - u) ** 5
    return u * u * (3 - 2 * u)


class Track:
    def __init__(self, default):
        self.default = default
        self.segs = []      # (t0, t1, target, kind)
        self.starts = None

    def add(self, t0, t1, v, kind):
        self.segs.append((t0, t1, v, kind))
        self.starts = None

    def finalize(self):
        self.segs.sort(key=lambda s: s[0])
        self.t0s = [s[0] for s in self.segs]
        self.starts = []
        for i, (t0, t1, v, k) in enumerate(self.segs):
            self.starts.append(self._eval(t0, i))

    def _eval(self, t, upto):
        # value at time t using segments [0, upto)
        j = bisect.bisect_right(self.t0s, t, 0, upto) - 1
        if j < 0:
            return self.default
        t0, t1, v, k = self.segs[j]
        v0 = self.starts[j]
        if t1 <= t0 or t >= t1:
            return v
        return v0 + (v - v0) * ease((t - t0) / (t1 - t0), k)

    def value(self, t):
        if self.starts is None:
            self.finalize()
        return self._eval(t, len(self.segs))


class Discrete:
    def __init__(self, default):
        self.default = default
        self.keys = []

    def add(self, t, v):
        self.keys.append((t, v))
        self.keys.sort(key=lambda k: k[0])

    def value(self, t):
        v = self.default
        for tk, vk in self.keys:
            if tk <= t:
                v = vk
            else:
                break
        return v


# --------------------------------------------------------------------------
EXPR = {
    'neutral': {},
    'happy': dict(brow_y=.3, brow_tilt=.1, lid_t=.15, lid_b=.28, smile=.8),
    'grin': dict(brow_y=.35, lid_t=.12, lid_b=.38, smile=1.0, open=.32, mw=1.15),
    'smug': dict(brow_l=.55, lid_t=.38, lid_b=.15, smile=.55, skew=.45),
    'suspicious': dict(brow_y=-.3, brow_tilt=-.45, lid_t=.45, lid_b=.22, smile=-.15, mw=.8, skew=-.2),
    'uneasy': dict(brow_y=.2, brow_tilt=.55, lid_t=.18, lid_b=.05, smile=-.2, mw=.75, skew=.25),
    'worried': dict(brow_y=.45, brow_tilt=.9, lid_t=.08, smile=-.45, mw=.8),
    'scared': dict(brow_y=.9, brow_tilt=.85, lid_t=-.12, pupil=.6, smile=-.5, open=.3, mw=.7),
    'terrified': dict(brow_y=1.0, brow_tilt=1.0, lid_t=-.16, pupil=.42, smile=-.6, open=.55, mw=.55),
    'angry': dict(brow_y=-.5, brow_tilt=-1.0, lid_t=.3, lid_tilt=.8, smile=-.6, open=.12),
    'furious': dict(brow_y=-.6, brow_tilt=-1.0, lid_t=.2, lid_tilt=1.0, smile=-.7, open=.4, teeth=1, mw=1.2),
    'shout': dict(brow_y=.35, brow_tilt=-.3, lid_t=-.05, smile=-.35, open=.3, mw=1.1),
    'panic': dict(brow_y=.9, brow_tilt=.9, lid_t=-.15, pupil=.5, smile=-.5, open=.35, mw=.9),
    'deadpan': dict(brow_y=-.15, lid_t=.56, lid_b=.08, smile=-.05),
    'skeptical': dict(brow_l=.75, brow_r=-.3, lid_t=.36, lid_b=.15, smile=-.1, skew=.4),
    'stunned': dict(brow_y=.75, lid_t=-.06, pupil=.75, smile=-.1, open=.22, mw=.6),
    'stare': dict(brow_y=-.1, lid_t=.22, pupil=.35, iris_dim=1.0, smile=-.2, open=.14, mw=.8),
    'laugh': dict(brow_y=.45, brow_tilt=.55, lid_t=.5, lid_b=.62, smile=1.0, open=.7, mw=1.15),
    'hold_laugh': dict(brow_y=.25, brow_tilt=.6, lid_t=.32, lid_b=.38, smile=.35, open=0, mw=.55, skew=.3),
    'soft': dict(brow_y=.15, brow_tilt=.35, lid_t=.24, lid_b=.16, smile=.35),
    'tender': dict(brow_y=.2, brow_tilt=.55, lid_t=.3, lid_b=.2, smile=.45),
    'sad': dict(brow_y=.2, brow_tilt=.9, lid_t=.36, lid_tilt=-.5, smile=-.4),
    'proud': dict(brow_y=.25, lid_t=.36, lid_b=.15, smile=.55, skew=.15),
    'alarmed': dict(brow_y=.8, brow_tilt=.3, lid_t=-.1, pupil=.7, smile=-.3, open=.35, mw=.75),
    'confused': dict(brow_l=.7, brow_r=-.4, brow_tilt=.3, lid_t=.2, smile=-.25, skew=-.3, mw=.8),
    'whisper': dict(brow_y=.2, brow_tilt=.6, lid_t=.22, smile=-.25, mw=.8),
    'grimace': dict(brow_y=.3, brow_tilt=.7, lid_t=.25, lid_b=.2, smile=-.3, open=.1, teeth=1, mw=1.1),
    'awkward': dict(brow_y=.35, brow_tilt=.55, lid_t=.2, lid_b=.15, smile=.25, mw=.9, skew=.35, teeth=0),
    'determined': dict(brow_y=-.2, brow_tilt=-.35, lid_t=.28, smile=.05),
    'shocked_o': dict(brow_y=1.0, brow_tilt=.2, lid_t=-.16, pupil=.55, smile=0, open=.65, mw=.45),
    'warm': dict(brow_y=.2, brow_tilt=.25, lid_t=.22, lid_b=.25, smile=.65),
}
FACE_KEYS = ['brow_y', 'brow_tilt', 'brow_l', 'brow_r', 'lid_t', 'lid_b', 'lid_tilt', 'pupil',
             'iris_dim', 'smile', 'open', 'mw', 'teeth', 'skew']


def arm_anchor(name, part, st=None):
    """torso-space target points for IK."""
    d = DESIGNS[name]
    th = d['torso_h']
    hy = -th - d['neck'] - d['head_h'] * 0.88
    if part == 'mouth':
        return (0, hy + d['mouth_y'])
    if part == 'face':
        return (0, hy + 10)
    if part == 'brow':
        return (0, hy - 20)
    if part == 'head_top':
        return (0, hy - d['head_h'] * 0.8)
    if part == 'head_side':
        return (d['head_w'] * 0.95, hy - 10)
    if part == 'chest':
        return (0, -th * 0.7)
    if part == 'belly':
        return (0, -th * 0.3)
    if part == 'lap':
        return (0, 10)
    raise KeyError(part)


def ik(name, side, tx, ty, elbow_out=True):
    d = DESIGNS[name]
    th = d['torso_h']
    sw = d['sh_w'] / 2
    sx, sy = side * (sw - d['arm_th'] * 0.45), -th + d['arm_th'] * 0.5
    L1, L2 = d['arm1'], d['arm2']
    dx, dy = tx - sx, ty - sy
    D = math.hypot(dx, dy)
    D = max(abs(L1 - L2) + 1, min(L1 + L2 - 0.5, D))
    phi = math.atan2(dy, dx)
    alpha = math.acos(max(-1, min(1, (L1 * L1 + D * D - L2 * L2) / (2 * L1 * D))))
    # choose elbow away from body midline / downward
    cands = []
    for sgn in (1, -1):
        ang = phi + sgn * alpha
        ex, ey = sx + math.cos(ang) * L1, sy + math.sin(ang) * L1
        cands.append((ex * side + ey * 0.3, ang, ex, ey))
    cands.sort(reverse=elbow_out)
    _, ang, ex, ey = cands[0]
    ux, uy = math.cos(ang), math.sin(ang)
    a1 = math.degrees(math.atan2(ux * side, uy))
    fx, fy = tx - ex, ty - ey
    r2 = math.degrees(math.atan2(fx * side, fy))
    a2 = a1 - r2
    return a1, a2


POSES = {
    'rest': dict(la1=8, la2=20, ra1=8, ra2=20, lh='open', rh='open'),
    'lap': dict(la1=4, la2=48, ra1=4, ra2=48, lh='open', rh='open'),
    'cross': dict(la1=14, la2=128, ra1=14, ra2=128, lh='fist', rh='fist'),
    'hands_up': dict(la1=155, la2=-15, ra1=155, ra2=-15, lh='splay', rh='splay'),
    'hands_out': dict(la1=70, la2=-30, ra1=70, ra2=-30, lh='splay', rh='splay'),
    'shrug': dict(la1=28, la2=-75, ra1=28, ra2=-75, lh='open', rh='open'),
    'fists': dict(la1=22, la2=110, ra1=22, ra2=110, lh='fist', rh='fist'),
}


class Timeline:
    def __init__(self):
        self.tr = {}        # actor -> param -> Track/Discrete
        self.kind = {}      # actor -> 'char' | 'bot' | 'cam' | 'fx'
        self.lines = []
        self.sfx = []
        self.music = []
        self.bursts = []
        self.overlays = []
        self.end = 0.0
        self.blinks = {}

    # ---- registration
    def actor(self, name, kind='char', **init):
        self.kind[name] = kind
        self.tr[name] = {}
        if kind == 'char':
            base = state_for(name)
        elif kind == 'bot':
            base = dict(BOT_DEFAULTS)
        else:
            base = {}
        base.update(init)
        self.base = getattr(self, 'base', {})
        self.base[name] = base
        self.extra_defaults = getattr(self, 'extra_defaults', {})
        self.extra_defaults[name] = dict(autoblink=1.0, saccade=1.0)

    def _track(self, a, p):
        if p not in self.tr[a]:
            disc = p in DISCRETE or p in BOT_DISCRETE or p in ('world', 'text')
            if self.kind[a] == 'char' and p not in DISCRETE and p in ('world',):
                disc = True
            dflt = self.base[a].get(p, self.extra_defaults[a].get(p, 0.0))
            if isinstance(dflt, str):
                disc = True
            self.tr[a][p] = Discrete(dflt) if disc else Track(dflt)
        return self.tr[a][p]

    # ---- authoring
    def key(self, a, t, dur=0.3, kind='io', **params):
        for p, v in params.items():
            tr = self._track(a, p)
            if isinstance(tr, Discrete):
                tr.add(t, v)
            else:
                tr.add(t, t + max(0.0, dur), float(v), kind)
        self.end = max(self.end, t + dur)

    def set(self, a, t, **params):
        self.key(a, t, 0.0, **params)

    def expr(self, a, t, name, dur=0.3, kind='io', **over):
        base = self.base[a]
        vals = {}
        for k in FACE_KEYS:
            vals[k] = base.get(k, DEFAULTS[k])
        vals.update(EXPR[name])
        vals.update(over)
        self.key(a, t, dur, kind, **vals)

    def pose(self, a, t, name, dur=0.4, kind='io', **over):
        vals = dict(POSES[name])
        vals.update(over)
        self.key(a, t, dur, kind, **vals)

    def reach(self, a, t, side, part, dur=0.35, dx=0.0, dy=0.0, hand=None, kind='io', elbow_out=True):
        tx, ty = arm_anchor(a, part)
        tx = tx + dx * (1 if side > 0 else 1)
        a1, a2 = ik(a, side, tx, ty + dy, elbow_out)
        kw = {('la1' if side < 0 else 'ra1'): a1, ('la2' if side < 0 else 'ra2'): a2}
        if hand:
            kw['lh' if side < 0 else 'rh'] = hand
        self.key(a, t, dur, kind, **kw)

    def pulse(self, a, t, param, v, t_in=0.1, hold=0.2, t_out=0.3, back=None):
        tr = self._track(a, param)
        b = tr.value(t) if back is None else back
        self.key(a, t, t_in, **{param: v})
        self.key(a, t + t_in + hold, t_out, **{param: b})

    def nod(self, a, t, n=2, amp=9, period=0.32):
        for i in range(n):
            self.key(a, t + i * period, period * 0.45, head_nod=amp)
            self.key(a, t + i * period + period * 0.5, period * 0.45, head_nod=0)

    def headshake(self, a, t, n=3, amp=0.35, period=0.3):
        for i in range(n):
            self.key(a, t + i * period, period * 0.5, head_turn=amp * (1 if i % 2 == 0 else -1))
        self.key(a, t + n * period, period * 0.5, head_turn=0)

    def blink(self, a, t, dur=0.16):
        self.blinks.setdefault(a, []).append((t, dur))

    def say_line(self, line):
        self.lines.append(line)
        self.end = max(self.end, line['t1'])

    def add_sfx(self, name, t, gain=1.0, **kw):
        self.sfx.append(dict(name=name, t=t, gain=gain, **kw))

    def burst(self, t, x, y, n=12, spread=260, up=520, floor=0.0, seed=0, world='aud', size=1.0):
        self.bursts.append(dict(t=t, x=x, y=y, n=n, spread=spread, up=up, floor=floor, seed=seed,
                                world=world, size=size))

    def overlay(self, kind, t0, t1, **kw):
        self.overlays.append(dict(kind=kind, t0=t0, t1=t1, **kw))

    # ---- evaluation
    def finalize(self):
        for a in self.tr:
            for p, tr in self.tr[a].items():
                if isinstance(tr, Track):
                    tr.finalize()
        # auto blink schedule
        self.auto_blinks = {}
        for a in self.tr:
            rnd = random.Random(hash(a) % 10007 + 17)
            t = rnd.uniform(0.5, 2.5)
            lst = []
            while t < self.end + 5:
                lst.append(t)
                r = rnd.random()
                t += 0.25 if r < 0.12 else rnd.uniform(2.2, 5.0)    # occasional double blink
            self.auto_blinks[a] = lst
        self.line_index = {}
        for ln in self.lines:
            self.line_index.setdefault(ln['actor'], []).append(ln)

    def raw(self, a, t):
        st = dict(self.base[a])
        st.update(self.extra_defaults[a])
        for p, tr in self.tr[a].items():
            st[p] = tr.value(t)
        return st

    def _blink_amt(self, a, t, st):
        amt = 0.0
        if st.get('autoblink', 1.0) > 0.5:
            lst = self.auto_blinks.get(a, [])
            i = bisect.bisect_right(lst, t) - 1
            if i >= 0:
                amt = max(amt, _blink_curve(t - lst[i], 0.17))
        for (tb, dur) in self.blinks.get(a, []):
            if tb <= t <= tb + dur + 0.05:
                amt = max(amt, _blink_curve(t - tb, dur))
        return amt

    def talk_env(self, a, t):
        for ln in self.line_index.get(a, []):
            if ln['t0'] <= t < ln['t1'] and not ln.get('voiceover'):
                fi = int((t - ln['t0']) * ln['fps'])
                env = ln['env']
                if 0 <= fi < len(env):
                    return env[fi], ln['round'][fi], ln
        return 0.0, 0.0, None

    def state(self, a, t):
        st = self.raw(a, t)
        kind = self.kind[a]
        if kind not in ('char', 'bot'):
            return st
        # blinking
        st['blink'] = self._blink_amt(a, t, st)
        # lip sync
        env, rnd, ln = self.talk_env(a, t)
        st['talk'] = env * st.get('talk_gain', 1.0)
        st['talk_round'] = rnd
        if kind == 'bot':
            return st
        # talking body language: small head bobs and brow lifts with the voice
        if ln is not None:
            slow = 0.0
            fi = int((t - ln['t0']) * ln['fps'])
            lo = max(0, fi - 6)
            seg = ln['env'][lo:fi + 1]
            if len(seg):
                slow = sum(seg) / len(seg)
            st['head_nod'] += env * 3.5 * ln.get('bob', 1.0)
            st['brow_y'] += slow * 0.25 * ln.get('brow', 1.0)
            st['head_tilt'] += noise1(t * 1.3, 9.1) * 2.5 * ln.get('bob', 1.0)
        # saccades
        sc = st.get('saccade', 1.0)
        if sc > 0.01:
            seg = math.floor(t / 0.9 + hash01(len(a)) * 7)
            jitter_t = (seg + hash01(seg, len(a))) * 0.9
            ox = (hash01(seg, 3, len(a)) - 0.5) * 0.22
            oy = (hash01(seg, 5, len(a)) - 0.5) * 0.14
            st['look_x'] += ox * sc
            st['look_y'] += oy * sc
        # walking from x velocity
        dt = 0.04
        x0 = self.tr[a]['x'].value(t - dt) if 'x' in self.tr[a] else st['x']
        x1 = self.tr[a]['x'].value(t + dt) if 'x' in self.tr[a] else st['x']
        v = (x1 - x0) / (2 * dt)
        if st.get('stand', 0) > 0.7 and abs(v) > 20:
            st['walk'] = min(1.0, abs(v) / 160.0)
            st['walk_phase'] = st['x'] * 0.05
        # eating cycle: hand from tub to mouth
        if st.get('eat', 0) > 0.01 and a == 'anger':
            per = 3.0
            ph = (t % per) / per
            if ph < 0.22:
                u = ease(ph / 0.22)
            elif ph < 0.45:
                u = 1.0
            elif ph < 0.62:
                u = 1 - ease((ph - 0.45) / 0.17)
            else:
                u = 0.0
            m = arm_anchor('anger', 'mouth')
            tub = (60, -70)
            tx = tub[0] + (m[0] - 12 - tub[0]) * u
            ty = tub[1] + (m[1] + 6 - tub[1]) * u
            a1, a2 = ik('anger', -1, tx, ty)
            e = st['eat']
            st['la1'] = st['la1'] * (1 - e) + a1 * e
            st['la2'] = st['la2'] * (1 - e) + a2 * e
            st['lh'] = 'fist'
            if 0.0 < ph < 0.24:
                st['prop_l'] = 'kernel'
            if 0.2 < ph < 0.75:
                st['chew'] = max(st.get('chew', 0), e)
            st['look_y'] -= 0.0
        return st


def _blink_curve(dt, dur):
    if dt < 0 or dt > dur:
        return 0.0
    c = dur * 0.4
    if dt < c:
        return dt / c
    if dt < c + dur * 0.15:
        return 1.0
    return max(0.0, 1 - (dt - c - dur * 0.15) / (dur * 0.45))
