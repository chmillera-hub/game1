"""Film assembly framework (runs inside Blender).

Builds the scene, then shot scripts (shots.py) place performances, cameras,
lines, sounds, labels and set-state keys on one global timeline.
"""
import json
import math
import os
import sys

import numpy as np
import bpy
from mathutils import Vector, Matrix, Euler, Quaternion

import blib
import env
import character
import chars
import perf
import props
import rigctl

FPS = 24
SZ = env.SIDEWALK_Z
FY = env.FACADE_Y
SPEAKER = {'O': 'oswald', 'E': 'edith', 'T': 'tomas', 'K': 'teddy', 'N': None}


def fr(t):
    return int(round(t * FPS))


def look_quat(loc, target, roll=0.0):
    d = Vector(target) - Vector(loc)
    q = d.to_track_quat('-Z', 'Y')
    if roll:
        q = q @ Euler((0, 0, math.radians(roll))).to_quaternion()
    return q


class Film:
    def __init__(self, voice_dir, cast=('oswald', 'edith', 'tomas', 'teddy', 'plum', 'flatcap', 'paper')):
        blib.clear_scene()
        self.sc = bpy.context.scene
        self.sc.render.fps = FPS
        self.voice_dir = voice_dir
        self.lines = json.load(open(os.path.join(voice_dir, 'lines.json')))
        self.S = env.build_set()
        self.W = env.setup_world('afternoon')
        self.pc = bpy.data.collections.new('PROPS')
        self.sc.collection.children.link(self.pc)
        self.snow = props.snowfall(self.pc)
        self.C, self.A = {}, {}
        for i, n in enumerate(cast):
            C = character.Character(chars.SPECS[n])
            self.C[n] = C
            a = perf.Actor(C, n, seed=11 + i, breath=1.0 if n != 'edith' else 0.8)
            self.A[n] = a
            perf.RES.actors[n] = a
        self.t = 0.0
        self.shots = []
        self.audio = []
        self.subs = []
        self.labels = []
        self.music = []
        self.sfx_ev = []
        self.props = {}
        self.prop_segs = {}
        self.vis_keys = []
        self.cur = None
        self._cams = []
        self._light_keys = []

    # ------------------------------------------------------------ shots
    def begin(self, name, note=''):
        self.cur = dict(name=name, t0=self.t, note=note)
        return self.t

    def end(self, t_end):
        d = round((t_end - self.cur['t0']) * FPS) / FPS
        self.cur['t1'] = self.cur['t0'] + d
        self.shots.append(self.cur)
        self.t = self.cur['t1']
        self.cur = None

    def camera(self, loc, target, lens=35.0, loc2=None, target2=None, t_move=None, ease='inout', roll=0.0,
               focus=None, fstop=None, focus2=None, t_focus=None, sensor=36.0, shift_y=0.0, keys=None, focus_keys=None):
        """Camera for the current shot.

        keys: [(t, loc, target)] extra waypoints (eased between consecutive ones).
        focus_keys: [(t_start, t_end, spec)] rack focus to spec over [t_start, t_end].
        """
        name = 'cam_' + self.cur['name']
        cd = bpy.data.cameras.new(name)
        cam = bpy.data.objects.new(name, cd)
        self.sc.collection.objects.link(cam)
        cd.lens = lens
        cd.sensor_width = sensor
        cd.clip_start = 0.05
        cd.clip_end = 200
        cd.shift_y = shift_y
        t0 = self.cur['t0']
        R = lambda v: self._resolve(v, t0 + 0.05)
        self._pending_cam = True
        wp = [(t0, loc, target)]
        if loc2 is not None:
            ta, tb = t_move if t_move else (t0, None)
            wp = [(ta, loc, target), (tb, loc2, target2 if target2 is not None else target)]
        if keys:
            wp += list(keys)
        fk = []
        if focus is not None:
            fk.append((-1e9, -1e9, focus))
        if focus2 is not None and t_focus:
            fk.append((t_focus[0], t_focus[1], focus2))
        if focus_keys:
            fk += list(focus_keys)
        self.cur['cam'] = cam
        self.cur['cam_spec'] = dict(wp=wp, ease=ease, roll=roll, fstop=fstop, fk=fk)
        self._cams.append(self.cur)
        return cam

    def _resolve(self, v, t):
        if isinstance(v, tuple) and len(v) and isinstance(v[0], str):
            return perf.world_point(v, t)
        return Vector(v)

    def _cam_at(self, c, t, t_end):
        wp = sorted(c['wp'], key=lambda w: (w[0] if w[0] is not None else t_end))
        wp = [(w[0] if w[0] is not None else t_end, w[1], w[2]) for w in wp]
        loc, tgt = wp[0][1], wp[0][2]
        for i in range(1, len(wp)):
            ta, tb = wp[i - 1][0], wp[i][0]
            if t >= tb:
                loc, tgt = wp[i][1], wp[i][2]
            elif t > ta:
                u = perf.ease((t - ta) / max(tb - ta, 1e-3), c['ease'])
                loc = wp[i - 1][1].lerp(wp[i][1], u)
                tgt = wp[i - 1][2].lerp(wp[i][2], u)
                break
            else:
                break
        return loc, tgt

    def _bake_cameras(self):
        for sh in self._cams:
            cam = sh['cam']
            c = sh['cam_spec']
            t0 = sh['t0'] + 0.05
            c['wp'] = [(t, self._resolve(l, t0), self._resolve(g, t0)) for (t, l, g) in c['wp']]
            f0, f1 = fr(sh['t0']), fr(sh['t1'])
            cam.rotation_mode = 'QUATERNION'
            prevq = None
            for f in range(f0, f1 + 1):
                t = f / FPS
                loc, tgt = self._cam_at(c, t, sh['t1'])
                cam.location = loc
                q = look_quat(loc, tgt, c['roll'])
                if prevq is not None and prevq.dot(q) < 0:
                    q = -q
                prevq = q
                cam.rotation_quaternion = q
                cam.keyframe_insert('location', frame=f)
                cam.keyframe_insert('rotation_quaternion', frame=f)
                if c['fstop'] and c['fk']:
                    cam.data.dof.use_dof = True
                    cam.data.dof.aperture_fstop = c['fstop']
                    dist = None
                    for (ta, tb, spec) in sorted(c['fk'], key=lambda k: k[0]):
                        p = perf.world_point(spec, t)
                        dd = (p - loc).length
                        if dist is None or t >= tb:
                            dist = dd
                        elif t > ta:
                            dist = dist + (dd - dist) * perf.ease((t - ta) / max(tb - ta, 1e-3))
                    cam.data.dof.focus_distance = dist
                    cam.data.dof.keyframe_insert('focus_distance', frame=f)
            m = self.sc.timeline_markers.new(sh['name'], frame=f0)
            m.camera = cam

    # ------------------------------------------------------------ sound & text
    def say(self, lid, t, sub=True, gain=0.0):
        r = self.lines[lid]
        who = SPEAKER[r['speaker']]
        dur = r['dur']
        g = gain + (-8.0 if r.get('hushed') else 0.0)
        self.audio.append(dict(kind='line', id=lid, t=t, dur=dur, gain=g, speaker=r['speaker']))
        if r.get('hushed'):
            self.sfx_ev.append(dict(name='breath_exhale', t=t - 0.35, gain=-14.0))
        if sub:
            self.subs.append(dict(t0=t, t1=t + dur, text=r['subtitle'], style='narr' if r['speaker'] == 'N' else 'dlg'))
        if who and who in self.A:
            self.A[who].say(t, r['visemes'])
        return t, t + dur

    def dur(self, lid):
        return self.lines[lid]['dur']

    def sfx(self, name, t, gain=0.0, **params):
        self.sfx_ev.append(dict(name=name, t=t, gain=gain, params=params))

    def cue(self, name, t, dur, gain=0.0, **params):
        self.music.append(dict(name=name, t=t, dur=dur, gain=gain, params=params))

    def label(self, t, dur, title, desc='', correct=None):
        self.labels.append(dict(t0=t, t1=t + dur, title=title, desc=desc, correct=correct))

    # ------------------------------------------------------------ set state
    def key_val(self, owner, path, t, value, dur=0.0, index=-1):
        """Key a property to reach value at t+dur, holding before t."""
        self._light_keys.append((owner, path, t, value, dur, index))

    def _bake_keys(self):
        groups = {}
        for (owner, path, t, value, dur, index) in self._light_keys:
            groups.setdefault((id(owner), path, index), (owner, []))[1].append((t, value, dur))
        for (oid, path, index), (owner, keys) in groups.items():
            keys.sort(key=lambda k: k[0])
            cur = None
            for (t, value, dur) in keys:
                if cur is None:
                    if fr(t) > 0:
                        init = getattr(owner, path)[index] if index >= 0 else getattr(owner, path)
                        try:
                            init = float(init)
                        except TypeError:
                            pass
                        owner.keyframe_insert(path, frame=0, index=index)
                        cur = init
                    else:
                        cur = value
                        self._set(owner, path, value, index)
                        owner.keyframe_insert(path, frame=0, index=index)
                        continue
                # a change shorter than a frame lands on fr(t + dur); the hold key goes one
                # frame earlier so the two never collapse onto one frame (which would leave
                # a ramp from the previous key instead of a cut)
                f0 = fr(t)
                f1 = fr(t + dur) if dur > 0 else f0 + 1
                if f1 <= f0:
                    f0 = f1 - 1
                self._set(owner, path, cur, index)
                owner.keyframe_insert(path, frame=f0, index=index)
                self._set(owner, path, value, index)
                owner.keyframe_insert(path, frame=f1, index=index)
                cur = value

    @staticmethod
    def _set(owner, path, value, index):
        if index >= 0:
            getattr(owner, path)[index] = value
        else:
            setattr(owner, path, value)

    def door(self, t, angle, dur=0.6):
        self.key_val(self.S['door_hinge'], 'rotation_euler', t, math.radians(angle), dur, index=2)

    def lamp(self, t, on, dur=0.25):
        L = self.S['lamp_light'].data
        self.key_val(L, 'energy', t, 60.0 if on else 0.0, dur)
        node = self.S['lamp_mat'].node_tree.nodes['Emission']
        self.key_val(node.inputs['Strength'], 'default_value', t, 9.0 if on else 0.0, dur)

    def clock(self, t, h, m, dur=0.0):
        hands = self.S['tower']['hands']
        self.key_val(hands['minute'], 'rotation_euler', t, math.radians(m / 60 * 360), dur, index=1)
        self.key_val(hands['hour'], 'rotation_euler', t, math.radians((h % 12 + m / 60) / 12 * 360), dur, index=1)

    def light(self, name, kind='AREA', loc=(0, 0, 3), target=(0, 0, 0), energy=50, size=1.0, color=(1, 1, 1),
              t0=None, t1=None, spot=None, shadow=True):
        """A light that exists only during [t0, t1] (energy keyed to 0 outside)."""
        ld = bpy.data.lights.new(name, kind)
        ld.color = color
        if kind == 'AREA':
            ld.size = size
        elif kind == 'SPOT':
            ld.spot_size = math.radians(spot or 60)
            ld.spot_blend = 0.8
            ld.shadow_soft_size = size
        else:
            ld.shadow_soft_size = size
        ld.use_shadow = shadow
        ob = bpy.data.objects.new(name, ld)
        self.sc.collection.objects.link(ob)
        ob.location = loc
        ob.rotation_mode = 'QUATERNION'
        ob.rotation_quaternion = look_quat(loc, target)
        if t0 is not None:
            self.key_val(ld, 'energy', -1, 0.0)
            self.key_val(ld, 'energy', t0, energy)
            self.key_val(ld, 'energy', t1, 0.0)
        else:
            ld.energy = energy
        return ob

    def set_visible(self, ob, t, visible):
        self.vis_keys.append((ob, t, visible))

    def _bake_vis(self):
        by = {}
        for (ob, t, v) in self.vis_keys:
            by.setdefault(ob.name, (ob, []))[1].append((t, v))
        for name, (ob0, ks) in by.items():
            ks.sort(key=lambda k: k[0])
            # children (e.g. a loaf's paper) follow their parent's visibility
            for ob in [ob0, *ob0.children_recursive]:
                ob.hide_render = not ks[0][1]
                ob.keyframe_insert('hide_render', frame=0)
                for (t, v) in ks:
                    ob.hide_render = not v
                    ob.keyframe_insert('hide_render', frame=fr(t))
                fc = ob.animation_data.action.fcurves.find('hide_render')
                for kp in fc.keyframe_points:
                    kp.interpolation = 'CONSTANT'

    # ------------------------------------------------------------ props
    def prop(self, name, ob):
        self.props[name] = ob
        self.prop_segs[name] = []
        return ob

    def attach(self, name, t0, t1, src):
        """src: ('hand', actor, side, local Matrix) | ('world', Matrix) | ('fn', fn(t)->Matrix) |
        ('bone', actor, bone, local Matrix)."""
        self.prop_segs[name].append((t0, t1, src))

    def _bake_props(self, f0, f1):
        names = [n for n in self.props if self.prop_segs[n]]
        if not names:
            return
        hidden = []
        for ob in bpy.data.objects:
            if ob.type in ('MESH', 'CURVES', 'FONT', 'CURVE') and not ob.hide_viewport:
                ob.hide_viewport = True
                hidden.append(ob)
        data = {n: [] for n in names}
        for f in range(f0, f1 + 1):
            self.sc.frame_set(f)
            t = f / FPS
            for n in names:
                segs = self.prop_segs[n]
                act = None
                for (a, b, src) in segs:
                    if a <= t < b:
                        act = src
                if act is None:
                    # hold the nearest previous segment end
                    prev = [s for s in segs if s[1] <= t]
                    if prev:
                        a, b, src = prev[-1]
                        if data[n]:
                            data[n].append((f, data[n][-1][1]))
                            continue
                    act = segs[0][2]
                M = self._src_matrix(act, t)
                data[n].append((f, M))
        for ob in hidden:
            ob.hide_viewport = False
        for n in names:
            ob = self.props[n]
            ob.rotation_mode = 'QUATERNION'
            act = bpy.data.actions.new(n + '_act')
            curves = {}
            for i in range(3):
                curves[('location', i)] = act.fcurves.new('location', index=i)
            for i in range(4):
                curves[('rotation_quaternion', i)] = act.fcurves.new('rotation_quaternion', index=i)
            for i in range(3):
                curves[('scale', i)] = act.fcurves.new('scale', index=i)
            rows = {k: [] for k in curves}
            prevq = None
            for (f, M) in data[n]:
                l, r, s_ = M.decompose()
                if prevq is not None and prevq.dot(r) < 0:
                    r = -r
                prevq = r
                for i in range(3):
                    rows[('location', i)].append((f, l[i]))
                    rows[('scale', i)].append((f, s_[i]))
                for i in range(4):
                    rows[('rotation_quaternion', i)].append((f, r[i]))
            for k, fc in curves.items():
                arr = np.array(rows[k], dtype=np.float32).reshape(-1)
                fc.keyframe_points.add(len(rows[k]))
                fc.keyframe_points.foreach_set('co', arr)
                fc.keyframe_points.foreach_set('interpolation', np.ones(len(rows[k]), dtype=np.int32))
                fc.update()
            ob.animation_data_create().action = act

    def _src_matrix(self, src, t):
        kind = src[0]
        if kind == 'world':
            return Matrix(src[1])
        if kind == 'fn':
            return src[1](t)
        if kind == 'hand':
            a, side, local = src[1], src[2], src[3]
            C = self.C[a]
            pb = C.arm.pose.bones['hand.' + side]
            M = C.arm.matrix_world @ pb.matrix
            return M @ local
        if kind == 'bone':
            a, bone, local = src[1], src[2], src[3]
            C = self.C[a]
            pb = C.arm.pose.bones[bone]
            M = C.arm.matrix_world @ pb.matrix
            return M @ local
        raise ValueError(kind)

    # ------------------------------------------------------------ finish
    def bake_all(self, export_json, blend_path=None):
        T = self.t
        f1 = fr(T) + 2
        self.sc.frame_start = 0
        self.sc.frame_end = fr(T) - 1
        for n, a in self.A.items():
            if a.postures or a.walks or a.speech or a.root.keys:
                perf.bake(a, 0, f1)
        self._bake_cameras()
        self._bake_keys()
        self._bake_vis()
        self._bake_props(0, f1)
        out = dict(fps=FPS, duration=T, shots=[dict(name=s['name'], t0=s['t0'], t1=s['t1'], note=s.get('note', ''))
                                               for s in self.shots],
                   audio=self.audio, subs=self.subs, labels=self.labels, music=self.music, sfx=self.sfx_ev)
        json.dump(out, open(export_json, 'w'), indent=1)
        if blend_path:
            bpy.ops.wm.save_as_mainfile(filepath=blend_path)
        return out
