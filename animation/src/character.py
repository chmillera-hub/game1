"""Procedural rigged character builder (runs inside Blender).

Each character = one armature object + meshes deformed by it (analytic
weights) + rigid parts parented to bones (eyes, lids, teeth, hair, hat).
"""
import math
import numpy as np
import bpy
from mathutils import Matrix, Vector, Euler, Quaternion

import blib
import headgen
from headgen import smoothstep


def V(*a):
    return Vector(a)


# ====================================================================== loft
def frame_from(t, up_hint):
    t = t / np.linalg.norm(t)
    n = up_hint - np.dot(up_hint, t) * t
    if np.linalg.norm(n) < 1e-6:
        n = np.array([1.0, 0, 0]) - t[0] * t
    n = n / np.linalg.norm(n)
    b = np.cross(t, n)
    return t, n, b


def loft(centers, sections, up_hint=(0, -1, 0), cap_start=True, cap_end=True, tangents=None):
    """centers: (R,3); sections: list of (K,2) offsets in (n,b) plane per ring.

    Returns verts (R*K[+caps],3), faces, ring index per vertex."""
    C = np.asarray(centers, float)
    R = len(C)
    K = len(sections[0])
    up = np.asarray(up_hint, float)
    verts = []
    for i in range(R):
        if tangents is not None:
            t = np.asarray(tangents[i], float)
        elif i == 0:
            t = C[1] - C[0]
        elif i == R - 1:
            t = C[-1] - C[-2]
        else:
            t = C[i + 1] - C[i - 1]
        t, n, b = frame_from(t, up)
        sec = np.asarray(sections[i])
        verts.append(C[i] + sec[:, 0:1] * n + sec[:, 1:2] * b)
    verts = np.concatenate(verts)
    faces = []
    for i in range(R - 1):
        for k in range(K):
            a = i * K + k
            b_ = i * K + (k + 1) % K
            faces.append((a, b_, b_ + K, a + K))
    ring = np.repeat(np.arange(R), K)
    extra = []
    if cap_start:
        extra.append(C[0])
        ci = len(verts) + len(extra) - 1
        for k in range(K):
            faces.append((ci, (k + 1) % K, k))
    if cap_end:
        extra.append(C[-1])
        ci = len(verts) + len(extra) - 1
        base = (R - 1) * K
        for k in range(K):
            faces.append((ci, base + k, base + (k + 1) % K))
    if extra:
        verts = np.concatenate([verts, np.array(extra)])
        ring = np.concatenate([ring, [0] * cap_start + [R - 1] * cap_end])
    return verts, faces, ring


def ellipse(K, a, b, n=2.0, phase=0.0):
    t = np.linspace(0, 2 * np.pi, K, endpoint=False) + phase
    c, s = np.cos(t), np.sin(t)
    x = a * np.sign(c) * np.abs(c) ** (2.0 / n)
    y = b * np.sign(s) * np.abs(s) ** (2.0 / n)
    return np.stack([x, y], -1)


def seg_dist(P, A, B):
    AB = B - A
    t = np.clip(((P - A) @ AB) / max(AB @ AB, 1e-12), 0, 1)
    return np.linalg.norm(P - (A + t[:, None] * AB), axis=1), t


def proximity_weights(P, segs, power=8.0):
    """segs: dict name -> (A,B). Smooth nearest-segment weights."""
    names = list(segs)
    D = np.stack([seg_dist(P, np.array(segs[n][0]), np.array(segs[n][1]))[0] for n in names], 1)
    D = np.maximum(D, 1e-4)
    w = 1.0 / D ** power
    w /= w.sum(1, keepdims=True)
    return {n: w[:, i] for i, n in enumerate(names)}


# ================================================================ defaults
BASE = dict(
    name='char',
    head=dict(),
    head_scale=1.0,
    leg_len=0.80, torso_len=0.50, neck_len=0.035,
    hip_w=0.085, shoulder_w=0.165,
    upper_arm=0.27, fore_arm=0.25, hand_scale=1.0,
    thigh_r=0.075, calf_r=0.060, hem_r=0.066,
    upperarm_r=0.050, forearm_r=0.044, cuff_r=0.040,
    chest_a=0.150, chest_b=0.105, waist_a=0.140, waist_b=0.100, belly=0.0,
    hip_a=0.150, hip_b=0.105,
    coat_hem=-0.05,       # metres below the hip joint where the coat ends
    coat_flare=0.012,
    neck_r=0.047,
    coat=(0.06, 0.06, 0.07), trousers=(0.20, 0.17, 0.14), shoes=(0.05, 0.035, 0.03),
    shirt=(0.85, 0.82, 0.74), cuff=(0.85, 0.82, 0.74),
    hair_color=(0.08, 0.05, 0.03), hair_style='short', brow_color=(0.06, 0.04, 0.03),
    hat=None, hat_color=(0.04, 0.04, 0.045),
    iris=(0.25, 0.40, 0.20),
    shoe_scale=1.0, bowtie=None, buttons=(0.6, 0.5, 0.3), scarf=None, apron=None,
    beard=None, lapels=True,
    sleeve_end=1.0, under_sleeve='shirt', vneck=None, coat_swap=None, gloves=None,
    freckles=0.0, flour=0.0, towel=None, bun=None, hat_brim=0.0, pompom=None, hat_band=None,
    stockings=None, hair_color2=None,
)


class Character:
    def __init__(self, spec):
        s = dict(BASE)
        s.update(spec)
        self.s = s
        self.name = s['name']
        self.coll = bpy.data.collections.new(self.name)
        bpy.context.scene.collection.children.link(self.coll)
        self.H = headgen.Head(**s['head'])
        self.hg = self.H.build()
        self._layout()
        self._build_armature()
        self._materials()
        self._build_head()
        self._build_body()
        self._build_hands()
        self._build_legs()
        self._build_extras()
        self._build_hair()

    # -------------------------------------------------------------- layout
    def _layout(self):
        s = self.s
        hs = s['head_scale']
        self.hipZ = s['leg_len']
        self.neckZ = s['leg_len'] + s['torso_len']
        self.neckTop = self.neckZ + s['neck_len']
        # head-space origin in world (rest)
        self.head_origin = np.array([0.0, -0.014, self.neckTop + 0.080 * hs])
        J = {}
        J['hips'] = (V(0, 0, self.hipZ), V(0, 0, self.hipZ + 0.12))
        J['spine'] = (V(0, 0, self.hipZ + 0.12), V(0, 0.005, self.hipZ + 0.30))
        J['chest'] = (V(0, 0.005, self.hipZ + 0.30), V(0, 0.0, self.neckZ))
        J['neck'] = (V(0, 0.0, self.neckZ), V(0, -0.006, self.neckTop))
        J['head'] = (V(0, -0.006, self.neckTop), V(0, -0.006, self.neckTop + 0.22 * hs))
        for side, sx in (('L', 1), ('R', -1)):
            sh = V(sx * s['shoulder_w'], 0.012, self.neckZ - 0.035)
            J['clavicle.' + side] = (V(sx * 0.025, -0.01, self.neckZ - 0.025), sh)
            a = math.radians(52)
            d1 = Vector((sx * math.sin(a), 0.03, -math.cos(a))).normalized()
            el = sh + d1 * s['upper_arm']
            d2 = Vector((sx * math.sin(a) * 0.85, -0.18, -math.cos(a))).normalized()
            wr = el + d2 * s['fore_arm']
            J['upperarm.' + side] = (sh, el)
            J['forearm.' + side] = (el, wr)
            hl = 0.095 * s['hand_scale']
            J['hand.' + side] = (wr, wr + d2 * hl)
            hip = V(sx * s['hip_w'], 0.0, self.hipZ)
            knee = V(sx * (s['hip_w'] + 0.004), -0.012, self.hipZ * 0.52)
            ankle = V(sx * (s['hip_w'] + 0.006), 0.012, 0.085 * s['shoe_scale'])
            ball = V(sx * (s['hip_w'] + 0.012), -0.085 * s['shoe_scale'], 0.025)
            toe = V(sx * (s['hip_w'] + 0.016), -0.15 * s['shoe_scale'], 0.025)
            J['thigh.' + side] = (hip, knee)
            J['shin.' + side] = (knee, ankle)
            J['foot.' + side] = (ankle, ball)
            J['toe.' + side] = (ball, toe)
        self.J = J

    def hp(self, p):
        """head-space point -> world rest position."""
        return Vector(np.asarray(p) * self.s['head_scale'] + self.head_origin)

    # ------------------------------------------------------------ armature
    def _build_armature(self):
        s = self.s
        ad = bpy.data.armatures.new(self.name + '_rig')
        arm = bpy.data.objects.new(self.name + '_rig', ad)
        self.coll.objects.link(arm)
        self.arm = arm
        ad.display_type = 'STICK'
        bpy.context.view_layer.objects.active = arm
        arm.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        E = ad.edit_bones

        def bone(name, h, t, parent=None, roll_to=None, deform=True):
            b = E.new(name)
            b.head = h
            b.tail = t
            if roll_to is not None:
                b.align_roll(Vector(roll_to))
            if parent:
                b.parent = E[parent]
            b.use_deform = deform
            return b

        J = self.J
        bone('root', V(0, 0, 0), V(0, 0.25, 0), deform=False)
        bone('hips', *J['hips'], parent='root', roll_to=(0, -1, 0))
        bone('spine', *J['spine'], parent='hips', roll_to=(0, -1, 0))
        bone('chest', *J['chest'], parent='spine', roll_to=(0, -1, 0))
        bone('neck', *J['neck'], parent='chest', roll_to=(0, -1, 0))
        bone('head', *J['head'], parent='neck', roll_to=(0, -1, 0))
        hg = self.hg
        jp = self.hp(hg['jaw_pivot'])
        chin = self.hp(hg['mouth_c'] + np.array([0, -0.01, -0.05]))
        bone('jaw', jp, chin, parent='head', roll_to=(0, 0, 1))
        r = self.H.p['eye_r'] * s['head_scale']
        for key, e in hg['eyes'].items():
            c = self.hp(e['c'])
            f = Vector(e['fwd'])
            bone('eye_' + key, c, c + f * r * 2.0, parent='head', roll_to=(0, 0, 1))
            bone('lid_up_' + key, c, c + f * r * 1.6, parent='head', roll_to=(0, 0, 1))
            bone('lid_lo_' + key, c, c + f * r * 1.4, parent='head', roll_to=(0, 0, 1))
            for i, nm in enumerate(('in', 'mid', 'out')):
                bx, bz = hg['brows'][key][i]
                fr = hg['verts'][hg['verts'][:, 1] < -0.02]
                d = (fr[:, 0] - bx) ** 2 + (fr[:, 2] - bz) ** 2
                by = fr[np.argmin(d), 1]
                bp = self.hp([bx, by, bz])
                bone('brow_%s_%s' % (nm, key), bp, bp + V(0, -0.02, 0), parent='head', roll_to=(0, 0, 1))
        for side, sx in (('L', 1), ('R', -1)):
            bone('clavicle.' + side, *J['clavicle.' + side], parent='chest', roll_to=(0, -1, 0))
            bone('upperarm.' + side, *J['upperarm.' + side], parent='clavicle.' + side, roll_to=(0, 1, 0))
            bone('forearm.' + side, *J['forearm.' + side], parent='upperarm.' + side, roll_to=(0, 1, 0))
            hb = bone('hand.' + side, *J['hand.' + side], parent='forearm.' + side, roll_to=(sx, 0, 0))
            hb.use_connect = False
            bone('thigh.' + side, *J['thigh.' + side], parent='hips', roll_to=(0, -1, 0))
            bone('shin.' + side, *J['shin.' + side], parent='thigh.' + side, roll_to=(0, -1, 0))
            bone('foot.' + side, *J['foot.' + side], parent='shin.' + side, roll_to=(0, 0, 1))
            bone('toe.' + side, *J['toe.' + side], parent='foot.' + side, roll_to=(0, 0, 1))
            # IK controls (non-deforming), parented to root
            wr, ht = J['hand.' + side]
            bone('hand_ik.' + side, wr, ht, parent='root', roll_to=(sx, 0, 0), deform=False)
            el = J['upperarm.' + side][1]
            bone('arm_pole.' + side, el + V(sx * 0.15, 0.30, -0.25), el + V(sx * 0.15, 0.40, -0.25), parent='root', deform=False)
            an, ba = J['foot.' + side]
            bone('foot_ik.' + side, an, ba, parent='root', roll_to=(0, 0, 1), deform=False)
            kn = J['thigh.' + side][1]
            bone('knee_pole.' + side, kn + V(0, -0.45, 0), kn + V(0, -0.55, 0), parent='root', deform=False)
        # finger bones are added in _build_hands (needs the hand frame)
        self._hand_frames = {}
        for side, sx in (('L', 1), ('R', -1)):
            hb = E['hand.' + side]
            M = hb.matrix.copy()   # armature space, Y along bone, Z toward roll target
            self._hand_frames[side] = M
            self._add_finger_bones(E, side, sx, M)
        bpy.ops.object.mode_set(mode='OBJECT')
        # IK constraints
        pb = arm.pose.bones
        for side in ('L', 'R'):
            c = pb['forearm.' + side].constraints.new('IK')
            c.target = arm
            c.subtarget = 'hand_ik.' + side
            c.pole_target = arm
            c.pole_subtarget = 'arm_pole.' + side
            c.pole_angle = math.radians(90)
            c.chain_count = 2
            cr = pb['hand.' + side].constraints.new('COPY_ROTATION')
            cr.target = arm
            cr.subtarget = 'hand_ik.' + side
            c = pb['shin.' + side].constraints.new('IK')
            c.target = arm
            c.subtarget = 'foot_ik.' + side
            c.pole_target = arm
            c.pole_subtarget = 'knee_pole.' + side
            c.pole_angle = math.radians(90)
            c.chain_count = 2
            cr = pb['foot.' + side].constraints.new('COPY_ROTATION')
            cr.target = arm
            cr.subtarget = 'foot_ik.' + side
        for b in pb:
            b.rotation_mode = 'QUATERNION'

    # canonical hand (left-hand frame): thumb +X, fingers +Y, back of hand +Z
    FINGERS = {
        'index': ((0.029, 0.090, 0.002), (0.034, 0.022, 0.019), 0.0102),
        'middle': ((0.009, 0.094, 0.003), (0.037, 0.025, 0.020), 0.0106),
        'ring': ((-0.011, 0.090, 0.002), (0.035, 0.023, 0.019), 0.0101),
        'pinky': ((-0.029, 0.082, 0.0), (0.027, 0.018, 0.016), 0.0090),
    }
    THUMB = [(0.020, 0.018, -0.010), (0.044, 0.046, -0.022), (0.058, 0.074, -0.026), (0.064, 0.096, -0.026)]

    def _hand_to_arm(self, side, p):
        """canonical hand point -> armature space (rest)."""
        M = self._hand_frames[side]
        sx = 1 if side == 'L' else -1
        hs = self.s['hand_scale']
        x, y, z = p
        # bone matrix columns: X, Y(along), Z(roll target = +X for L / -X for R)
        # canonical: Y along fingers, Z back of hand, X thumb side
        # back of hand faces outward (+sx world X) = bone Z; thumb = bone X*sign
        loc = Vector((x * hs * sx, y * hs, z * hs))
        # map canonical (thumb X, along Y, back Z) to bone local (X, Y, Z)
        bl = Vector((-loc.x, loc.y, loc.z)) if False else Vector((loc.x, loc.y, loc.z))
        return M @ bl

    def _add_finger_bones(self, E, side, sx, M):
        hs = self.s['hand_scale']
        self._finger_joints = getattr(self, '_finger_joints', {})
        fj = {}
        for fname, (base, lens, rad) in self.FINGERS.items():
            pts = [np.array(base)]
            d = np.array([0.0, 1.0, 0.0])
            d = np.array([pts[0][0] * 0.25, 1.0, -0.06])
            d /= np.linalg.norm(d)
            for L in lens:
                pts.append(pts[-1] + d * L)
                # natural slight curl
                d = d + np.array([0, 0, -0.22])
                d /= np.linalg.norm(d)
            fj[fname] = pts
            prev = 'hand.' + side
            for i in range(3):
                h = self._hand_to_arm(side, pts[i])
                t = self._hand_to_arm(side, pts[i + 1])
                b = E.new('%s%d.%s' % (fname, i + 1, side))
                b.head, b.tail = h, t
                back = (self._hand_to_arm(side, pts[i] + np.array([0, 0, 1.0])) - h)
                b.align_roll(back)
                b.parent = E[prev]
                prev = b.name
        pts = [np.array(p) for p in self.THUMB]
        fj['thumb'] = pts
        prev = 'hand.' + side
        for i in range(3):
            h = self._hand_to_arm(side, pts[i])
            t = self._hand_to_arm(side, pts[i + 1])
            b = E.new('thumb%d.%s' % (i + 1, side))
            b.head, b.tail = h, t
            back = (self._hand_to_arm(side, pts[i] + np.array([-0.6, 0, 0.8])) - h)
            b.align_roll(back)
            b.parent = E[prev]
            prev = b.name
        self._finger_joints[side] = fj

    # ----------------------------------------------------------- materials
    def _materials(self):
        s = self.s
        hp = self.H.p
        n = self.name
        self.m_skin = blib.skin_material(n + '_skin', hp['skin'], hp['lip_color'], hp['blush'], hp['blush_amt'])
        self.m_lid = blib.lid_material(n + '_lid', hp['skin'])
        self.m_eye = blib.eye_material(n + '_eye', iris=s['iris'])
        self.m_teeth = blib.principled(n + '_teeth', (0.90, 0.88, 0.80), rough=0.3)
        self.m_tongue = blib.principled(n + '_tongue', (0.55, 0.18, 0.18), rough=0.4)
        self.m_brow = blib.cloth_material(n + '_brow', s['brow_color'], rough=0.6, scale=900, bump_str=0.4, sheen=0.2)
        self.m_coat = blib.cloth_material(n + '_coat', s['coat'])
        self.coat_off_nodes = []
        if s['vneck'] or s['coat_swap']:
            self.m_coat = self._swap_material(n + '_coat', s['coat'], s['vneck'] or s['coat'], s['coat_swap'] or s['coat'], use_mask=bool(s['vneck']))
            self.m_sleeve = self._swap_material(n + '_sleeve', s['coat'], s['coat'], s['shirt'] if s['coat_swap'] else s['coat'], use_mask=False)
        else:
            self.m_sleeve = self.m_coat
        self.m_trousers = blib.cloth_material(n + '_trousers', s['trousers'])
        self.m_shoes = blib.principled(n + '_shoes', s['shoes'], rough=0.35, coat=0.3)
        self.m_shirt = blib.cloth_material(n + '_shirt', s['shirt'], rough=0.7, sheen=0.2, scale=400, bump_str=0.08)
        self.m_cuff = blib.cloth_material(n + '_cuff', s['cuff'], rough=0.7, sheen=0.2, scale=400, bump_str=0.08)
        self.m_inner = blib.principled(n + '_inner', tuple(np.array(s['coat']) * 0.35), rough=0.9)
        # lining of the coat hem / sleeve ends: follows the coat-off swap so no mustard lip stays behind
        self.m_coat_inner = self.m_sleeve_inner = self.m_inner
        if s['coat_swap']:
            dk = lambda c: tuple(np.array(c) * 0.35)
            self.m_coat_inner = self._swap_material(n + '_coat_inner', dk(s['coat']), dk(s['coat']), dk(s['coat_swap']), use_mask=False)
            self.m_sleeve_inner = self._swap_material(n + '_sleeve_inner', dk(s['coat']), dk(s['coat']), tuple(np.array(s['shirt']) * 0.6), use_mask=False)
        self.m_sock = blib.cloth_material(n + '_sock', tuple(np.array(s['stockings'] or s['trousers']) * 0.55), rough=0.9, sheen=0.3)
        self.m_hair = blib.hair_material(n + '_hair', s['hair_color'])
        self.m_hand = self.m_skin
        if s['gloves']:
            self.m_hand = blib.cloth_material(n + '_gloves', s['gloves'], rough=0.95, sheen=0.6, scale=300, bump_str=0.35)
        if s['stockings']:
            self.m_trousers = blib.cloth_material(n + '_stock', s['stockings'], rough=0.8, sheen=0.5, scale=500, bump_str=0.1)
        self.m_forearm = self.m_skin
        if s['flour']:
            self.m_forearm = blib.skin_material(n + '_forearm', hp['skin'], hp['lip_color'], hp['blush'], 0.0)
            self._skin_extras(self.m_forearm, 0.0, s['flour'])
        if s['freckles']:
            self._skin_extras(self.m_skin, s['freckles'], 0.0)

    def _swap_material(self, name, base, masked, swapped, use_mask=True):
        """Cloth material: base colour, V-neck mask colour, and an animated 'coat_off' swap."""
        mat = blib.cloth_material(name, base)
        N = mat.node_tree.nodes
        L = mat.node_tree.links
        b = N['Principled BSDF']
        src = b.inputs['Base Color'].links[0].from_socket
        val = N.new('ShaderNodeValue')
        val.name = 'coat_off'
        val.outputs[0].default_value = 0.0
        self.coat_off_nodes.append((mat, val))
        fac = val.outputs[0]
        if use_mask:
            a = blib.attr_node(N, 'vneck')
            mx = N.new('ShaderNodeMath')
            mx.operation = 'MAXIMUM'
            L.new(a.outputs['Fac'], mx.inputs[0])
            L.new(val.outputs[0], mx.inputs[1])
            m1 = blib.mix_rgb(N, L, a.outputs['Fac'], src, masked, x=-150, y=200)
            m2 = blib.mix_rgb(N, L, val.outputs[0], m1.outputs[2], swapped, x=-50, y=200)
        else:
            m2 = blib.mix_rgb(N, L, fac, src, swapped, x=-50, y=200)
        L.new(m2.outputs[2], b.inputs['Base Color'])
        return mat

    def _skin_extras(self, mat, freckles, flour):
        N = mat.node_tree.nodes
        L = mat.node_tree.links
        b = N['Principled BSDF']
        src = b.inputs['Base Color'].links[0].from_socket
        out = src
        tc = N.new('ShaderNodeTexCoord')
        if freckles:
            vor = N.new('ShaderNodeTexVoronoi')
            vor.inputs['Scale'].default_value = 900.0
            vor.inputs['Randomness'].default_value = 1.0
            L.new(tc.outputs['Object'], vor.inputs['Vector'])
            mr = N.new('ShaderNodeMapRange')
            mr.inputs['From Min'].default_value = 0.0
            mr.inputs['From Max'].default_value = 0.22
            mr.inputs['To Min'].default_value = 1.0
            mr.inputs['To Max'].default_value = 0.0
            L.new(vor.outputs['Distance'], mr.inputs['Value'])
            a = blib.attr_node(N, 'mask')
            sep = N.new('ShaderNodeSeparateColor')
            L.new(a.outputs['Color'], sep.inputs[0])
            m = N.new('ShaderNodeMath')
            m.operation = 'MULTIPLY'
            L.new(mr.outputs[0], m.inputs[0])
            L.new(sep.outputs['Green'], m.inputs[1])
            m2 = N.new('ShaderNodeMath')
            m2.operation = 'MULTIPLY'
            m2.inputs[1].default_value = freckles
            L.new(m.outputs[0], m2.inputs[0])
            mix = blib.mix_rgb(N, L, m2.outputs[0], out, (0.25, 0.09, 0.04), x=-120, y=300)
            out = mix.outputs[2]
        if flour:
            n = N.new('ShaderNodeTexNoise')
            n.inputs['Scale'].default_value = 60.0
            n.inputs['Detail'].default_value = 6.0
            L.new(tc.outputs['Object'], n.inputs['Vector'])
            mr = N.new('ShaderNodeMapRange')
            mr.inputs['From Min'].default_value = 0.55
            mr.inputs['From Max'].default_value = 0.75
            mr.inputs['To Max'].default_value = flour
            L.new(n.outputs['Fac'], mr.inputs['Value'])
            mix = blib.mix_rgb(N, L, mr.outputs[0], out, (0.85, 0.83, 0.78), x=-60, y=300)
            out = mix.outputs[2]
        L.new(out, b.inputs['Base Color'])

    def _mesh(self, name, verts, faces, mat, weights=None, sub=1, mats=None):
        ob = blib.make_mesh(self.name + '_' + name, verts, faces, coll=self.coll)
        if mats:
            for m in mats:
                ob.data.materials.append(m)
        else:
            blib.assign(ob, mat)
        if weights is not None:
            blib.set_weights(ob, weights)
            ob.parent = self.arm
            blib.armature_mod(ob, self.arm)
        if sub:
            blib.subsurf(ob, sub)
        return ob

    def _rigid(self, ob, bone):
        blib.parent_to_bone(ob, self.arm, bone)

    # ---------------------------------------------------------------- head
    def _build_head(self):
        s, hg, H = self.s, self.hg, self.H
        hs = s['head_scale']
        P = hg['verts'] * hs + self.head_origin
        shapes = {k: v * hs + self.head_origin for k, v in hg['shapes'].items()}
        ob = self._mesh('head', P, hg['faces'], self.m_skin, weights=hg['weights'], sub=1)
        blib.set_color_attr(ob, 'mask', hg['colors'])
        blib.set_shape_keys(ob, shapes)
        ob.modifiers['Subsurf'].render_levels = 2
        self.head = ob
        r = H.p['eye_r'] * hs
        self.eyes, self.lids = {}, {}
        for key, e in hg['eyes'].items():
            c = self.hp(e['c'])
            bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=40, ring_count=20, location=c)
            eo = bpy.context.object
            bpy.context.scene.collection.objects.unlink(eo)
            self.coll.objects.link(eo)
            eo.name = self.name + '_eye_' + key
            bpy.ops.object.shade_smooth()
            blib.assign(eo, self.m_eye)
            q = Vector((0, -1, 0)).rotation_difference(Vector(e['fwd']))
            eo.rotation_euler = q.to_euler()
            self._rigid(eo, 'eye_' + key)
            self.eyes[key] = eo
            for up in (True, False):
                Vv, F, lash = H.lid(key, upper=up)
                nm = 'lid_%s_%s' % ('up' if up else 'lo', key)
                lo = blib.make_mesh(self.name + '_' + nm, Vv * hs, F, coll=self.coll)
                blib.set_color_attr(lo, 'lash', np.stack([lash] * 3, -1))
                blib.assign(lo, self.m_lid)
                lo.location = c
                lo.rotation_euler = q.to_euler()
                blib.subsurf(lo, 1)
                self._rigid(lo, nm)
                self.lids[nm] = lo
        for side in (1, -1):
            Vv, F = H.ear(side)
            eo = blib.make_mesh(self.name + '_ear', Vv * hs + self.head_origin, F, coll=self.coll)
            blib.assign(eo, self.m_skin)
            blib.subsurf(eo, 1)
            self._rigid(eo, 'head')
        for up in (True, False):
            Vv, F = H.teeth(up)
            t = blib.make_mesh(self.name + '_teeth', Vv * hs + self.head_origin, F, coll=self.coll)
            blib.assign(t, self.m_teeth)
            blib.subsurf(t, 1)
            self._rigid(t, 'head' if up else 'jaw')
        c, rr = H.tongue()
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=24, ring_count=12, location=self.hp(c))
        tg = bpy.context.object
        bpy.context.scene.collection.objects.unlink(tg)
        self.coll.objects.link(tg)
        tg.scale = tuple(rr * hs)
        bpy.ops.object.shade_smooth()
        blib.assign(tg, self.m_tongue)
        self._rigid(tg, 'jaw')
        # brows
        for key in ('L', 'R'):
            Vv, F, W = self._brow_mesh(key)
            self._mesh('brow_' + key, Vv, F, self.m_brow, weights=W, sub=1)

    def _brow_mesh(self, key):
        H, hg = self.H, self.hg
        hs = self.s['head_scale']
        pts = H.brows[key]
        t = np.linspace(0, 1, 22)
        P0, P1, P2 = pts
        C = 2 * P1 - 0.5 * (P0 + P2)
        xz = ((1 - t) ** 2)[:, None] * P0 + (2 * (1 - t) * t)[:, None] * C + (t ** 2)[:, None] * P2
        fr = hg['verts'][hg['verts'][:, 1] < -0.02]
        verts, faces = [], []
        ns = 8
        th = self.s.get('brow_thick', 1.0)
        for i, (x, z) in enumerate(xz):
            d = (fr[:, 0] - x) ** 2 + (fr[:, 2] - z) ** 2
            y = fr[np.argmin(d), 1] - 0.0016
            h = (0.0085 * (1 - t[i]) + 0.0042 * t[i]) * th
            h *= np.sin(np.pi * np.clip(t[i] * 0.92 + 0.08, 0, 1)) ** 0.35
            tk = 0.0034
            for k in range(ns):
                a = 2 * np.pi * k / ns
                verts.append([x, y + tk * np.cos(a) * 0.6 - 0.0006, z + h * 0.5 * np.sin(a)])
        n = len(xz)
        for i in range(n - 1):
            for k in range(ns):
                a = i * ns + k
                b = i * ns + (k + 1) % ns
                faces.append((a, b, b + ns, a + ns))
        faces.append(tuple(range(ns))[::-1])
        faces.append(tuple(range((n - 1) * ns, n * ns)))
        Vv = np.array(verts)
        tt = np.repeat(t, ns)
        w_in = np.clip(1 - tt * 2, 0, 1)
        w_out = np.clip(tt * 2 - 1, 0, 1)
        w_mid = 1 - w_in - w_out
        W = {'brow_in_' + key: w_in, 'brow_mid_' + key: w_mid, 'brow_out_' + key: w_out}
        return Vv * hs + self.head_origin, faces, W

    # ---------------------------------------------------------------- body
    def _torso_profile(self, z):
        """Cross-section (a, b, yoff, n) of the coat at world height z."""
        s = self.s
        h0 = self.hipZ + s['coat_hem']
        top = self.neckZ
        t = (z - h0) / (top - h0)
        keys = [  # t, a, b, yoff
            (0.00, s['hip_a'] + s['coat_flare'], s['hip_b'] + s['coat_flare'] * 0.6, 0.0),
            (0.18, s['hip_a'], s['hip_b'], 0.0),
            (0.42, s['waist_a'], s['waist_b'] + s['belly'], -s['belly'] * 0.8),
            (0.72, s['chest_a'], s['chest_b'], -0.004),
            (0.86, s['shoulder_w'] - 0.005, s['chest_b'] * 0.90, 0.002),
            (0.95, s['shoulder_w'] * 0.70, s['chest_b'] * 0.74, 0.006),
            (1.00, s['neck_r'] + 0.022, s['neck_r'] + 0.018, 0.006),
        ]
        ts = [k[0] for k in keys]
        a = np.interp(t, ts, [k[1] for k in keys])
        b = np.interp(t, ts, [k[2] for k in keys])
        y = np.interp(t, ts, [k[3] for k in keys])
        n = np.interp(t, [0, 0.6, 0.9, 1.0], [2.1, 2.15, 2.3, 2.0])
        return a, b, y, n

    def _build_body(self):
        s = self.s
        h0 = self.hipZ + s['coat_hem']
        top = self.neckZ + 0.012
        R = 34
        K = 48
        zs = h0 + (top - h0) * (np.linspace(0, 1, R) ** 0.9)
        verts = []
        for z in zs:
            a, b, yoff, n = self._torso_profile(min(z, self.neckZ))
            sec = ellipse(K, a, b, n, phase=-np.pi / 2)
            # slight shoulder slope: lower the outer points near the top
            pts = np.stack([sec[:, 0], sec[:, 1] + yoff, np.full(K, z)], -1)
            tt = (z - h0) / (top - h0)
            slope = smoothstep(0.80, 1.0, tt) * (np.abs(sec[:, 0]) / max(a, 1e-3)) ** 2 * 0.035
            pts[:, 2] -= slope
            verts.append(pts)
        P = np.concatenate(verts)
        faces = []
        for i in range(R - 1):
            for k in range(K):
                a_ = i * K + k
                b_ = i * K + (k + 1) % K
                faces.append((a_, a_ + K, b_ + K, b_))
        # hem: turn inward to show thickness, then cap high inside (hidden)
        hem = P[:K].copy()
        inner = hem.copy()
        inner[:, 0] *= 0.93
        inner[:, 1] *= 0.93
        # the lining runs up a short way inside the shell; take it from the shell ring at that
        # height (scaled in) so it can never cross the outside where the coat narrows above the hem
        i2 = int(np.argmin(np.abs(zs - (h0 + 0.06))))
        inner2 = P[i2 * K:(i2 + 1) * K].copy()
        inner2[:, 0] *= 0.84
        inner2[:, 1] *= 0.84
        base = len(P)
        P = np.concatenate([P, inner, inner2])
        for k in range(K):
            a_ = k
            b_ = (k + 1) % K
            faces.append((base + k, a_, b_, base + (k + 1) % K))
            faces.append((base + K + k, base + k, base + (k + 1) % K, base + K + (k + 1) % K))
        # top cap
        ci = len(P)
        P = np.concatenate([P, [[0, 0.004, top]]])
        for k in range(K):
            a_ = (R - 1) * K + k
            b_ = (R - 1) * K + (k + 1) % K
            faces.append((ci, b_, a_))
        segs = {n: (np.array(self.J[n][0]), np.array(self.J[n][1])) for n in ('hips', 'spine', 'chest', 'clavicle.L', 'clavicle.R')}
        segs['thigh.L'] = (np.array(self.J['thigh.L'][0]), np.array(self.J['thigh.L'][1]))
        segs['thigh.R'] = (np.array(self.J['thigh.R'][0]), np.array(self.J['thigh.R'][1]))
        W = proximity_weights(P, segs, power=4)
        # keep thighs to the lower front of the coat only
        z = P[:, 2]
        for side in ('L', 'R'):
            W['thigh.' + side] *= smoothstep(self.hipZ + 0.02, self.hipZ - 0.06, z) * 0.6
            W['clavicle.' + side] *= smoothstep(self.neckZ - 0.12, self.neckZ - 0.04, z)
        tot = sum(W.values())
        for k in W:
            W[k] = W[k] / tot
        nhem = 2 * K
        mats = [self.m_coat, self.m_coat_inner]
        ob = self._mesh('coat', P, faces, None, weights=W, sub=1, mats=mats)
        # V-neck: waistcoat/shirt showing at the chest front, under the collar
        top = self.neckZ
        vz = (P[:, 2] - (top - 0.20)) / 0.20
        vx = np.abs(P[:, 0]) / (0.012 + 0.06 * np.clip(vz, 0, 1))
        vm = ((vz > 0) & (vx < 1.0) & (P[:, 1] < -0.02)).astype(float)
        vm = vm * np.clip((1 - vx) * 4, 0, 1)
        blib.set_color_attr(ob, 'vneck', np.stack([vm] * 3, -1))
        # 'slim' shape key: the garment without its bulk (coat removed)
        c = np.array([0, 0.0, 0])
        slim = P.copy()
        slim[:, 0] *= 0.92
        slim[:, 1] = slim[:, 1] * 0.92
        blib.set_shape_keys(ob, {'slim': slim})
        # inner faces -> material 1
        nf = len(faces)
        for i, poly in enumerate(ob.data.polygons):
            if (R - 1) * K <= i < (R - 1) * K + 2 * K:
                poly.material_index = 1 if (i - (R - 1) * K) % 2 == 1 else 0
        self.coat = ob
        self._build_neck()
        self._build_arms()

    def _build_neck(self):
        s = self.s
        hs = s['head_scale']
        bot = np.array([0, 0.004, self.neckZ - 0.03])
        topc = self.head_origin + np.array([0, 0.018, -0.070]) * hs
        R, K = 14, 36
        centers = [bot + (topc - bot) * t for t in np.linspace(0, 1, R)]
        secs = []
        for i, t in enumerate(np.linspace(0, 1, R)):
            r = s['neck_r'] * (1.05 - 0.08 * t + 0.10 * smoothstep(0.8, 1.0, t))
            ang = np.linspace(0, 2 * np.pi, K, endpoint=False)
            # ang=0 -> front (-Y)
            rr = np.full(K, r)
            # sternocleidomastoid: from behind the ear (top, +-110deg) to the sternal notch (bottom, +-18deg)
            for sgn in (1, -1):
                line = np.radians(18 + (110 - 18) * t) * sgn
                da = np.angle(np.exp(1j * (ang - line)))
                rr += 0.0050 * np.exp(-(da / 0.24) ** 2) * (0.4 + 0.6 * np.sin(np.pi * np.clip(t * 1.1, 0, 1)))
            # trachea/front softness and slightly flatter back
            rr *= 1 - 0.06 * np.cos(ang) ** 2 * (np.cos(ang) < 0)
            sec = np.stack([np.sin(ang) * rr, -np.cos(ang) * rr], -1)
            secs.append(sec)
        Vv, F, ring = loft(centers, secs, up_hint=(1, 0, 0), cap_start=True, cap_end=True)
        # loft frame: n ~ +X, b = t x n; t ~ +Z => b = Z x X = +Y.  sec (x, y) maps to (n, b) = (+X, +Y)
        t = ring / (R - 1)
        W = {'chest': np.clip(1 - t * 3, 0, 1), 'head': np.clip((t - 0.65) / 0.35, 0, 1)}
        W['neck'] = np.clip(1 - W['chest'] - W['head'], 0, 1)
        self.neck = self._mesh('neck', Vv, F, self.m_skin, weights=W, sub=1)
        # collar ring (shirt)
        c = np.array([0, 0.002, self.neckZ + 0.004])
        R2, K2 = 4, 40
        cs, ss = [], []
        for i, dz in enumerate((-0.02, 0.0, 0.010, 0.014)):
            r = s['neck_r'] + (0.014, 0.010, 0.007, 0.0045)[i]
            cs.append(c + np.array([0, 0, dz]))
            ang = np.linspace(0, 2 * np.pi, K2, endpoint=False)
            ss.append(np.stack([np.sin(ang) * r, -np.cos(ang) * r * 0.97], -1))
        Vv, F, ring = loft(cs, ss, up_hint=(1, 0, 0), cap_start=False, cap_end=False)
        W = {'chest': np.clip(1 - ring / 3 * 0.6, 0, 1), 'neck': np.clip(ring / 3 * 0.6, 0, 1)}
        self._mesh('collar', Vv, F, self.m_shirt, weights=W, sub=1)

    def _limb(self, pts, radii, K=24, open_end=True, cuff_mat=False):
        """Tube along a polyline with per-point radius; open hollow end."""
        P = np.asarray(pts, float)
        secs = [np.stack([np.cos(a) * r, np.sin(a) * r], -1) for r in radii for a in [np.linspace(0, 2 * np.pi, K, endpoint=False)]]
        tang = [P[1] - P[0]] + [P[i + 1] - P[i - 1] for i in range(1, len(P) - 1)] + [P[-1] - P[-2]]
        if open_end:
            # lip at the end then back inside
            d = P[-1] - P[-2]
            d /= np.linalg.norm(d)
            r_end = radii[-1]
            extra_c = [P[-1] + d * 0.004, P[-1] + d * 0.002, P[-1] - d * 0.03]
            extra_r = [r_end * 0.97, r_end * 0.90, r_end * 0.86]
            P = np.concatenate([P, extra_c])
            for r in extra_r:
                a = np.linspace(0, 2 * np.pi, K, endpoint=False)
                secs.append(np.stack([np.cos(a) * r, np.sin(a) * r], -1))
                tang.append(tang[-1])
        Vv, F, ring = loft(P, secs, up_hint=(0, -1, 0), cap_start=True, cap_end=True, tangents=tang)
        return Vv, F, ring

    def _build_arms(self):
        s = self.s
        se = s['sleeve_end']
        for side, sx in (('L', 1), ('R', -1)):
            sh, el = self.J['upperarm.' + side]
            _, wr = self.J['forearm.' + side]
            sh, el, wr = np.array(sh), np.array(el), np.array(wr)
            start = sh + (sh - el) / np.linalg.norm(sh - el) * 0.045 + np.array([-sx * 0.015, 0, 0.0])
            n1, n2 = 10, 9
            pts, radii = [], []
            for i in range(n1):
                t = i / n1
                pts.append(start + (el - start) * t)
                cap = np.sqrt(np.clip(t / 0.12, 0, 1)) * 0.75 + 0.25
                radii.append(s['upperarm_r'] * (1.12 - 0.22 * t) * cap)
            end_pt = el + (wr - el) * se
            for i in range(n2 + 1):
                t = i / n2
                pts.append(el + (end_pt - el) * t)
                r = s['forearm_r'] * (1.0 - 0.10 * t * se)
                if se >= 0.99 and t > 0.82:
                    r = s['cuff_r']
                if se < 0.99 and t > 0.85:
                    r = s['forearm_r'] * 1.02
                radii.append(r)
            Vv, F, ring = self._limb(pts, radii, K=24, open_end=True)
            nreal = len(pts)
            segs = {'upperarm.' + side: (sh, el), 'forearm.' + side: (el, wr), 'clavicle.' + side: (np.array(self.J['clavicle.' + side][0]), sh)}
            W = proximity_weights(Vv, segs, power=6)
            ob = self._mesh('sleeve_' + side, Vv, F, None, weights=W, sub=1, mats=[self.m_sleeve, self.m_sleeve_inner])
            K = 24
            for i, poly in enumerate(ob.data.polygons):
                if i >= (nreal + 1) * K and i < (nreal + 2) * K:
                    poly.material_index = 1
            d = (wr - el) / np.linalg.norm(wr - el)
            if se < 0.99:
                # what shows below a short sleeve: a shirt sleeve with cuff, or a bare forearm
                a = el + (wr - el) * (se - 0.12)
                if s['under_sleeve'] == 'skin':
                    cpts = [a, el + (wr - el) * 0.6, wr - d * 0.01, wr + d * 0.03]
                    crad = [s['forearm_r'] * 0.80, s['forearm_r'] * 0.74, s['cuff_r'] * 0.62, s['cuff_r'] * 0.55]
                    Vc, Fc, rc = self._limb(cpts, crad, K=20, open_end=False)
                    Wc = proximity_weights(Vc, {'forearm.' + side: (el, wr), 'hand.' + side: (wr, wr + d * 0.08)}, power=8)
                    fo = self._mesh('forearm_' + side, Vc, Fc, self.m_forearm, weights=Wc, sub=1)
                    blib.set_color_attr(fo, 'mask', np.zeros((len(Vc), 3)))
                else:
                    cpts = [a, el + (wr - el) * 0.75, wr - d * 0.03, wr + d * 0.006]
                    crad = [s['forearm_r'] * 0.86, s['forearm_r'] * 0.80, s['cuff_r'] * 0.86, s['cuff_r'] * 0.84]
                    Vc, Fc, rc = self._limb(cpts, crad, K=20, open_end=True)
                    Wc = {'forearm.' + side: np.ones(len(Vc))}
                    self._mesh('shirtsleeve_' + side, Vc, Fc, self.m_cuff, weights=Wc, sub=1)
            else:
                cpts = [wr - d * 0.05, wr - d * 0.005, wr + d * 0.010]
                Vc, Fc, rc = self._limb(cpts, [s['cuff_r'] * 0.86, s['cuff_r'] * 0.86, s['cuff_r'] * 0.84], K=20, open_end=True)
                Wc = {'forearm.' + side: np.ones(len(Vc))}
                self._mesh('shirtcuff_' + side, Vc, Fc, self.m_cuff, weights=Wc, sub=1)

    # --------------------------------------------------------------- hands
    def _build_hands(self):
        s = self.s
        hs = s['hand_scale']
        for side, sx in (('L', 1), ('R', -1)):
            fj = self._finger_joints[side]
            parts_v, parts_f, weights = [], [], []
            off = 0
            # palm: loft along canonical Y from inside the cuff to the knuckles
            ys = np.linspace(-0.045, 0.092, 12)
            secs, cents = [], []
            for y in ys:
                t = (y + 0.045) / 0.137
                w = np.interp(t, [0, 0.30, 0.45, 0.8, 1.0], [0.021, 0.024, 0.037, 0.043, 0.038])
                th = np.interp(t, [0, 0.3, 0.6, 1.0], [0.017, 0.016, 0.018, 0.014])
                xo = np.interp(t, [0, 0.4, 1.0], [0.0, 0.002, -0.001])
                cents.append(np.array([xo, y, -0.002]))
                secs.append(ellipse(20, w, th, 2.4))
            Vp, Fp, rp = loft(cents, secs, up_hint=(1, 0, 0))
            # loft frame for +Y tangent with up hint +X: n=+X, b = Y x X = -Z.  fine (symmetric section)
            parts_v.append(Vp)
            parts_f += [tuple(i + off for i in f) for f in Fp]
            off += len(Vp)
            # fingers
            for fname, pts in list(fj.items()):
                if fname == 'thumb':
                    radius = [0.0125, 0.0105, 0.0095, 0.0085]
                    P = [np.array(p) for p in pts]
                    start = P[0] + (P[0] - P[1]) * 0.3
                else:
                    rad = self.FINGERS[fname][2]
                    radius = [rad, rad * 0.96, rad * 0.90, rad * 0.82]
                    P = [np.array(p) for p in pts]
                    start = P[0] - (P[1] - P[0]) / np.linalg.norm(P[1] - P[0]) * 0.012
                cpts, crad = [start], [radius[0] * 0.95]
                for i in range(3):
                    for t in (0.0, 0.5):
                        cpts.append(P[i] + (P[i + 1] - P[i]) * t)
                        crad.append(radius[i] + (radius[i + 1] - radius[i]) * t)
                cpts.append(P[3] - (P[3] - P[2]) / np.linalg.norm(P[3] - P[2]) * radius[3] * 0.4)
                crad.append(radius[3] * 0.95)
                cpts.append(P[3] + (P[3] - P[2]) / np.linalg.norm(P[3] - P[2]) * radius[3] * 0.25)
                crad.append(radius[3] * 0.55)
                secs = [ellipse(12, r * 0.92, r * 1.04, 2.0) for r in crad]
                Vf, Ff, rf = loft(cpts, secs, up_hint=(0, 0, 1))
                parts_v.append(Vf)
                parts_f += [tuple(i + off for i in f) for f in Ff]
                off += len(Vf)
            Vc = np.concatenate(parts_v)
            # weights by proximity to the hand + finger bones (canonical space)
            segs = {'hand.' + side: (np.array([0, -0.06, 0]), np.array([0, 0.075, 0]))}
            for fname, pts in fj.items():
                for i in range(3):
                    segs['%s%d.%s' % (fname, i + 1, side)] = (np.array(pts[i]), np.array(pts[i + 1]))
            W = proximity_weights(Vc, segs, power=10)
            # canonical -> armature space (rest)
            Vw = np.array([tuple(self._hand_to_arm(side, p)) for p in Vc])
            if side == 'R':
                parts_f = [f[::-1] for f in parts_f]
            ob = self._mesh('hand_' + side, Vw, parts_f, self.m_hand, weights=W, sub=1)
            blib.set_color_attr(ob, 'mask', np.zeros((len(Vw), 3)))

    # ---------------------------------------------------------------- legs
    def _build_legs(self):
        s = self.s
        for side, sx in (('L', 1), ('R', -1)):
            hip, knee = [np.array(v) for v in self.J['thigh.' + side]]
            _, ankle = [np.array(v) for v in self.J['shin.' + side]]
            top = hip + np.array([-sx * 0.03, 0, 0.10])
            pts, radii = [], []
            for i in range(6):
                t = i / 6
                pts.append(top + (hip - top) * t)
                radii.append(s['thigh_r'] * (0.80 + 0.20 * t))
            for i in range(7):
                t = i / 7
                pts.append(hip + (knee - hip) * t)
                radii.append(s['thigh_r'] + (s['calf_r'] * 1.02 - s['thigh_r']) * t)
            for i in range(8):
                t = i / 7
                pts.append(knee + (ankle + np.array([0, 0, 0.02]) - knee) * t)
                radii.append(s['calf_r'] + (s['hem_r'] - s['calf_r']) * t)
            Vv, F, ring = self._limb(pts, radii, K=28, open_end=True)
            segs = {'hips': (np.array(self.J['hips'][0]) + np.array([0, 0, -0.05]), np.array(self.J['hips'][1])),
                    'thigh.' + side: (hip, knee), 'shin.' + side: (knee, ankle)}
            W = proximity_weights(Vv, segs, power=6)
            ob = self._mesh('trouser_' + side, Vv, F, None, weights=W, sub=1, mats=[self.m_trousers, self.m_inner])
            # shoes
            Vs, Fs, Ws = self._shoe(side, sx)
            self._mesh('shoe_' + side, Vs, Fs, self.m_shoes, weights=Ws, sub=1)
            # sock/ankle filling the cuff, so a leg seen end-on has no empty tube
            ab = ankle + np.array([0, 0, 0.0])
            Va, Fa, ra = loft([ab - np.array([0, 0, 0.02]), ab + np.array([0, 0, 0.06])],
                              [ellipse(16, s['hem_r'] * 0.84, s['hem_r'] * 0.84)] * 2, up_hint=(1, 0, 0))
            self._mesh('sock_' + side, Va, Fa, self.m_sock, weights={'shin.' + side: np.ones(len(Va))}, sub=0)

    def _shoe(self, side, sx):
        s = self.s
        ss = s['shoe_scale']
        ankle, ball = [np.array(v) for v in self.J['foot.' + side]]
        _, toe = [np.array(v) for v in self.J['toe.' + side]]
        heel = np.array([ankle[0], ankle[1] + 0.045 * ss, 0.0])
        tip = np.array([toe[0], toe[1] - 0.02 * ss, 0.0])
        L = np.linalg.norm(tip[:2] - heel[:2])
        n = 18
        cents, secs = [], []
        for i in range(n):
            t = i / (n - 1)
            c = heel + (tip - heel) * t
            w = np.interp(t, [0, 0.1, 0.5, 0.75, 0.92, 1.0], [0.020, 0.040, 0.044, 0.052, 0.042, 0.010]) * ss
            h = np.interp(t, [0, 0.08, 0.3, 0.55, 0.8, 0.95, 1.0], [0.03, 0.075, 0.085, 0.055, 0.045, 0.030, 0.012]) * ss
            c = c + np.array([0, 0, h * 0.5 + 0.004])
            cents.append(c)
            secs.append(ellipse(20, h * 0.5, w, 2.6))
        Vv, F, ring = loft(cents, secs, up_hint=(0, 0, 1))
        t = ring / (n - 1)
        W = {'foot.' + side: np.clip(1.6 - t * 1.6, 0, 1)}
        W['toe.' + side] = 1 - W['foot.' + side]
        W['foot.' + side] = np.where(t < 0.6, 1.0, W['foot.' + side])
        W['toe.' + side] = 1 - W['foot.' + side]
        return Vv, F, W

    # -------------------------------------------------------------- extras
    def _build_extras(self):
        s = self.s
        if s['hat'] == 'bowler':
            self._bowler()
        elif s['hat'] in ('cloche', 'bobble', 'beanie'):
            self._knit_hat(s['hat'])
        elif s['hat'] == 'flatcap':
            self._flatcap()
        if s['bun']:
            self._bun()
        if s['towel']:
            self._towel()
        # buttons
        if s['buttons']:
            mb = blib.principled(self.name + '_button', s['buttons'], rough=0.3, coat=0.5)
            for i, frac in enumerate((0.30, 0.45, 0.60)):
                z = self.hipZ + s['coat_hem'] + (self.neckZ - self.hipZ - s['coat_hem']) * frac
                a, b, yoff, n = self._torso_profile(z)
                bpy.ops.mesh.primitive_uv_sphere_add(radius=0.009, segments=16, ring_count=8, location=(0, yoff - b - 0.002, z))
                bo = bpy.context.object
                bpy.context.scene.collection.objects.unlink(bo)
                self.coll.objects.link(bo)
                bo.scale = (1, 0.45, 1)
                bpy.ops.object.shade_smooth()
                blib.assign(bo, mb)
                self._rigid(bo, 'spine' if frac < 0.5 else 'chest')
        if s['bowtie']:
            mt = blib.cloth_material(self.name + '_tie', s['bowtie'], rough=0.6, sheen=0.3, scale=500, bump_str=0.05)
            c = np.array([0, -s['neck_r'] - 0.012, self.neckZ + 0.008])
            for sxx in (1, -1):
                bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=20, ring_count=10, location=tuple(c + np.array([sxx * 0.018, 0, 0])))
                bo = bpy.context.object
                bpy.context.scene.collection.objects.unlink(bo)
                self.coll.objects.link(bo)
                bo.scale = (0.020, 0.008, 0.013)
                bpy.ops.object.shade_smooth()
                blib.assign(bo, mt)
                self._rigid(bo, 'chest')
            bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=16, ring_count=8, location=tuple(c + np.array([0, -0.002, 0])))
            bo = bpy.context.object
            bpy.context.scene.collection.objects.unlink(bo)
            self.coll.objects.link(bo)
            bo.scale = (0.008, 0.008, 0.009)
            bpy.ops.object.shade_smooth()
            blib.assign(bo, mt)
            self._rigid(bo, 'chest')
        if s['scarf']:
            self._scarf()
        if s['apron']:
            self._apron()

    def _lathe(self, name, prof, mat, K=48, center=None, scale_xy=(1, 1)):
        """prof: list of (r, z). Returns object in world space around center."""
        verts, faces = [], []
        P = len(prof)
        for (r, z) in prof:
            for k in range(K):
                a = 2 * np.pi * k / K
                verts.append([r * np.cos(a) * scale_xy[0], r * np.sin(a) * scale_xy[1], z])
        for i in range(P - 1):
            for k in range(K):
                a_ = i * K + k
                b_ = i * K + (k + 1) % K
                faces.append((a_, b_, b_ + K, a_ + K))
        Vv = np.array(verts) + (center if center is not None else 0)
        ob = blib.make_mesh(self.name + '_' + name, Vv, faces, coll=self.coll)
        blib.assign(ob, mat)
        return ob

    def _bowler(self):
        s = self.s
        hs = s['head_scale']
        hp = self.H.p
        zb = 0.066
        rxh = hp['rx'] * np.sqrt(max(1 - (zb / hp['rz_top']) ** 2, 0.05))
        ryh = hp['ry'] * np.sqrt(max(1 - (zb / hp['rz_top']) ** 2, 0.05))
        R = 1.0
        prof = [(0.0, 0.118)]
        for t in np.linspace(0.06, 1, 11):
            ang = t * np.pi / 2
            prof.append((0.93 * np.sin(ang), 0.030 + 0.088 * np.cos(ang)))
        prof += [(0.975, 0.016), (1.0, 0.002), (1.25, -0.002), (1.36, 0.008),
                 (1.38, 0.003), (1.32, -0.006), (0.99, -0.008), (0.955, 0.02), (0.85, 0.07)]
        K = 56
        verts, faces = [], []
        for (r, z) in prof:
            for k in range(K):
                a = 2 * np.pi * k / K
                verts.append([r * np.cos(a) * (rxh + 0.008), r * np.sin(a) * (ryh + 0.008), z])
        P = len(prof)
        for i in range(P - 1):
            for k in range(K):
                a_ = i * K + k
                b_ = i * K + (k + 1) % K
                faces.append((a_, b_, b_ + K, a_ + K))
        Vv = np.array(verts)
        tilt = np.radians(-9)
        Ry = np.array([[1, 0, 0], [0, np.cos(tilt), -np.sin(tilt)], [0, np.sin(tilt), np.cos(tilt)]])
        Vv = Vv @ Ry.T
        Vv = Vv + np.array([0, 0.004, zb])
        Vv = Vv * hs + self.head_origin
        m = blib.cloth_material(self.name + '_hat', s['hat_color'], rough=0.55, sheen=0.5, scale=600, bump_str=0.05)
        ob = blib.make_mesh(self.name + '_hat', Vv, faces, coll=self.coll)
        blib.assign(ob, m)
        blib.subsurf(ob, 1)
        # band
        bp = [(0.977, 0.003), (0.984, 0.010), (0.972, 0.022)]
        bv = []
        for (r, z) in bp:
            for k in range(K):
                a = 2 * np.pi * k / K
                bv.append([r * 1.012 * np.cos(a) * (rxh + 0.008), r * 1.012 * np.sin(a) * (ryh + 0.008), z])
        bf = []
        for i in range(2):
            for k in range(K):
                a_ = i * K + k
                b_ = i * K + (k + 1) % K
                bf.append((a_, b_, b_ + K, a_ + K))
        bv = (np.array(bv) @ Ry.T + np.array([0, 0.004, zb])) * hs + self.head_origin
        mband = blib.principled(self.name + '_band', (0.015, 0.015, 0.015), rough=0.35)
        band = blib.make_mesh(self.name + '_hatband', bv, bf, coll=self.coll)
        blib.assign(band, mband)
        blib.subsurf(band, 1)
        for o in (ob, band):
            self._rigid(o, 'head')
        self.hat = ob

    def _beanie(self):
        s = self.s
        hs = s['head_scale']
        hp = self.H.p
        rx, ry, rz = hp['rx'] * hs, hp['ry'] * hs, hp['rz_top'] * hs
        c = self.head_origin
        verts, faces = [], []
        K, Rr = 48, 16
        for i in range(Rr):
            el = np.radians(np.interp(i, [0, Rr - 1], [8, 90]))
            for k in range(K):
                a = 2 * np.pi * k / K
                r = 1.06 + (0.03 if i < 3 else 0.0)
                verts.append([rx * r * np.cos(el) * np.sin(a), -ry * r * np.cos(el) * np.cos(a) + 0.004, rz * 1.06 * np.sin(el) + 0.0])
        for i in range(Rr - 1):
            for k in range(K):
                a_ = i * K + k
                b_ = i * K + (k + 1) % K
                faces.append((a_, b_, b_ + K, a_ + K))
        Vv = np.array(verts)
        # tilt: lower at the back, higher at the forehead
        Vv[:, 2] += -0.018 * hs + 0.02 * np.clip(Vv[:, 1] / ry, -1, 1) * hs * 0.6
        Vv = Vv + c
        m = blib.cloth_material(self.name + '_beanie', s['hat_color'], rough=0.95, sheen=0.6, scale=140, bump_str=0.5)
        ob = blib.make_mesh(self.name + '_beanie', Vv, faces, coll=self.coll)
        blib.assign(ob, m)
        blib.subsurf(ob, 1)
        self._rigid(ob, 'head')

    def _hat_rings(self, zf, zs, zb, scale=1.045, rows=18, K=56):
        """Dome over the cranium down to a bottom line given by front/side/back z (head space)."""
        hp = self.H.p
        rx, ry, rzt, rzb = hp['rx'], hp['ry'], hp['rz_top'], hp['rz_bot']
        verts = []
        az = np.linspace(0, 2 * np.pi, K, endpoint=False)   # 0 = front (-Y)
        c = np.cos(az)
        zbot = np.where(c > 0, zs + (zf - zs) * c ** 1.5, zs + (zb - zs) * (-c) ** 1.2)
        for i in range(rows):
            u = i / (rows - 1)
            row = []
            for k in range(K):
                z0 = zbot[k]
                rz = rzt if z0 >= 0 else rzb
                el0 = np.arcsin(np.clip(z0 / rz, -0.95, 0.95))
                el = el0 + (np.pi / 2 - el0) * (u ** 0.9)
                rzz = rzt if np.sin(el) >= 0 else rzb
                p = np.array([rx * np.cos(el) * np.sin(az[k]), -ry * np.cos(el) * np.cos(az[k]), rzz * np.sin(el)]) * scale
                row.append(p)
            verts.append(row)
        return np.array(verts), az

    def _grid_faces(self, R, K, wrap=True):
        F = []
        for i in range(R - 1):
            for k in range(K if wrap else K - 1):
                a = i * K + k
                b = i * K + (k + 1) % K
                F.append((a, b, b + K, a + K))
        return F

    def _knit_hat(self, kind):
        s = self.s
        hs = s['head_scale']
        hp = self.H.p
        ez = hp['eye_z'] + hp['eye_r'] * 1.7
        if kind == 'cloche':
            dome, az = self._hat_rings(ez + 0.032, 0.030, -0.030, scale=1.05)
        else:
            dome, az = self._hat_rings(ez + 0.028, 0.030, -0.020, scale=1.05)
        R, K = dome.shape[0], dome.shape[1]
        # brim / cuff rings below the bottom row, pushed outward
        bot = dome[0]
        n_out = bot.copy()
        n_out[:, 2] = 0
        n_out = n_out / np.linalg.norm(n_out, axis=1, keepdims=True)
        rings = []
        if kind == 'cloche':
            # felt bell: the brim turns down rather than out
            for (dz, out) in ((-0.003, 0.005), (-0.009, 0.009), (-0.015, 0.012), (-0.016, 0.015), (-0.006, 0.010)):
                rings.append(bot + n_out * out + np.array([0, 0, dz]))
        else:
            for (dz, out) in ((-0.002, 0.004), (0.002, 0.010), (0.030, 0.011), (0.034, 0.004)):
                rings.append(bot + n_out * out + np.array([0, 0, dz]))
        allr = np.concatenate([np.array(rings[::-1]), dome])
        Vv = allr.reshape(-1, 3)
        F = self._grid_faces(allr.shape[0], K)
        top = len(Vv)
        Vv = np.concatenate([Vv, [dome[-1].mean(0) + np.array([0, 0, 0.001])]])
        last = (allr.shape[0] - 1) * K
        for k in range(K):
            F.append((last + k, last + (k + 1) % K, top))
        Vv = Vv * hs + self.head_origin
        if kind == 'cloche':
            m = blib.cloth_material(self.name + '_felt', s['hat_color'], rough=0.9, sheen=0.12, scale=420, bump_str=0.12)
        else:
            m = blib.cloth_material(self.name + '_knit', s['hat_color'], rough=0.95, sheen=0.7, scale=160, bump_str=0.6)
        if kind == 'cloche' and s['hat_band']:
            # grosgrain band over the lowest rows of the crown
            band = dome[1:5].copy()
            nb = band.copy()
            nb[..., 2] = 0
            nb = nb / np.linalg.norm(nb, axis=-1, keepdims=True)
            band = band + nb * 0.0022
            Vb = band.reshape(-1, 3) * hs + self.head_origin
            mb = blib.cloth_material(self.name + '_band', s['hat_band'], rough=0.55, sheen=0.1, scale=900, bump_str=0.05)
            bo = blib.make_mesh(self.name + '_hatband', Vb, self._grid_faces(band.shape[0], K), coll=self.coll)
            blib.assign(bo, mb)
            blib.subsurf(bo, 1)
            self._rigid(bo, 'head')
            self.hat_band = bo
        ob = blib.make_mesh(self.name + '_hat', Vv, F, coll=self.coll)
        blib.assign(ob, m)
        blib.subsurf(ob, 1)
        self._rigid(ob, 'head')
        self.hat = ob
        if kind == 'bobble':
            topc = (dome[-1].mean(0) + np.array([0, 0.0, 0.03])) * hs + self.head_origin
            bpy.ops.mesh.primitive_ico_sphere_add(radius=0.042 * hs, subdivisions=3, location=tuple(topc))
            pp = bpy.context.object
            for cc in pp.users_collection:
                cc.objects.unlink(pp)
            self.coll.objects.link(pp)
            bpy.ops.object.shade_smooth()
            mp = blib.cloth_material(self.name + '_pom', s['pompom'] or s['hat_color'], rough=1.0, sheen=1.0, scale=400, bump_str=1.0)
            blib.assign(pp, mp)
            self._rigid(pp, 'head')

    def _flatcap(self):
        s = self.s
        hs = s['head_scale']
        hp = self.H.p
        ez = hp['eye_z'] + hp['eye_r'] * 1.7
        dome, az = self._hat_rings(ez + 0.024, 0.044, 0.004, scale=1.09)
        zb = dome[0][:, 2].min()
        dome[:, :, 1] -= 0.008
        R, K = dome.shape[:2]
        Vv = dome.reshape(-1, 3)
        F = self._grid_faces(R, K)
        top = len(Vv)
        Vv = np.concatenate([Vv, [dome[-1].mean(0)]])
        for k in range(K):
            F.append(((R - 1) * K + k, (R - 1) * K + (k + 1) % K, top))
        # visor: half disc from the front bottom edge
        front = [k for k in range(K) if np.cos(az[k]) > 0.35]
        base = len(Vv)
        vis = []
        for k in front:
            p = dome[0][k]
            d = np.array([p[0] * 0.15, -1.0, 0])
            d /= np.linalg.norm(d)
            vis.append(p + d * 0.045 * np.cos(az[k]) ** 0.5 + np.array([0, 0, -0.006]))
        Vv = np.concatenate([Vv, np.array(vis)])
        for i in range(len(front) - 1):
            F.append((front[i], front[i + 1], base + i + 1, base + i))
        Vv = Vv * hs + self.head_origin
        m = blib.cloth_material(self.name + '_cap', s['hat_color'], rough=0.9, sheen=0.5, scale=250, bump_str=0.3)
        ob = blib.make_mesh(self.name + '_hat', Vv, F, coll=self.coll)
        blib.assign(ob, m)
        sol = ob.modifiers.new('sol', 'SOLIDIFY')
        sol.thickness = 0.004
        blib.subsurf(ob, 1)
        self._rigid(ob, 'head')

    def _bun(self):
        s = self.s
        hs = s['head_scale']
        y, z, r = s['bun']
        c = np.array([0, y, z]) * hs + self.head_origin
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r * hs, segments=32, ring_count=16, location=tuple(c))
        b = bpy.context.object
        for cc in b.users_collection:
            cc.objects.unlink(b)
        self.coll.objects.link(b)
        b.scale = (1.15, 0.85, 0.9)
        bpy.ops.object.shade_smooth()
        m = blib.cloth_material(self.name + '_bunm', s['hair_color'], rough=0.45, sheen=0.3, scale=900, bump_str=0.5)
        blib.assign(b, m)
        self._rigid(b, 'head')

    def _towel(self):
        s = self.s
        m = blib.principled(self.name + '_towelm', (0.6, 0.6, 0.6), rough=0.9)
        N = m.node_tree.nodes
        L = m.node_tree.links
        ch = N.new('ShaderNodeTexChecker')
        ch.inputs['Scale'].default_value = 7.0
        ch.inputs['Color1'].default_value = (*s['towel'], 1)
        ch.inputs['Color2'].default_value = (0.82, 0.80, 0.74, 1)
        tc = N.new('ShaderNodeTexCoord')
        L.new(tc.outputs['UV'] if False else tc.outputs['Object'], ch.inputs['Vector'])
        L.new(ch.outputs['Color'], N['Principled BSDF'].inputs['Base Color'])
        sx = 1
        x0 = sx * s['shoulder_w'] * 0.55
        top = self.neckZ + 0.012
        a0, b0, y0, n0 = self._torso_profile(self.neckZ - 0.22)
        a1, b1, y1, n1 = self._torso_profile(self.neckZ - 0.02)
        path = []
        for t in np.linspace(0, 1, 16):
            ang = np.pi * t   # front (0) -> over the top -> back (pi)
            yy = -np.cos(ang) * (b1 + 0.012)
            zz = top - 0.005 + np.sin(ang) * 0.0 - (1 - np.sin(ang)) * 0.20
            path.append([x0, yy, zz])
        path = np.array(path)
        W_ = 0.13
        Vv = []
        for p in path:
            for w in (-W_ / 2, -W_ / 4, 0, W_ / 4, W_ / 2):
                Vv.append(p + np.array([w, 0, 0]) * np.array([1, 1, 1]))
        Vv = np.array(Vv)
        # follow the shoulder slope
        Vv[:, 2] -= np.clip(np.abs(Vv[:, 0]) - s['shoulder_w'] * 0.4, 0, 1) * 0.35
        F = []
        for i in range(len(path) - 1):
            for k in range(4):
                a = i * 5 + k
                F.append((a, a + 1, a + 6, a + 5))
        segs = {'chest': (np.array(self.J['chest'][0]), np.array(self.J['chest'][1])),
                'clavicle.L': (np.array(self.J['clavicle.L'][0]), np.array(self.J['clavicle.L'][1]))}
        Wt = proximity_weights(Vv, segs, power=3)
        ob = self._mesh('towel', Vv, F, m, weights=Wt, sub=1)
        sol = ob.modifiers.new('sol', 'SOLIDIFY')
        sol.thickness = 0.006
        sol.offset = 1.0
        ob.modifiers.move(len(ob.modifiers) - 1, 1)

    def _scarf(self):
        s = self.s
        m = blib.cloth_material(self.name + '_scarf', s['scarf'], rough=0.95, sheen=0.6, scale=120, bump_str=0.5)
        c = np.array([0, 0.004, self.neckZ + 0.012])
        cs, ss = [], []
        for i, dz in enumerate((-0.02, -0.005, 0.012, 0.03, 0.04)):
            r = s['neck_r'] + (0.024, 0.030, 0.030, 0.024, 0.014)[i]
            cs.append(c + np.array([0, 0, dz]))
            ang = np.linspace(0, 2 * np.pi, 40, endpoint=False)
            ss.append(np.stack([np.sin(ang) * r, -np.cos(ang) * r], -1))
        Vv, F, ring = loft(cs, ss, up_hint=(1, 0, 0), cap_start=False, cap_end=False)
        W = {'chest': np.full(len(Vv), 0.6), 'neck': np.full(len(Vv), 0.4)}
        self._mesh('scarf', Vv, F, m, weights=W, sub=1)
        # hanging tail on the chest
        top = c + np.array([0.03, -s['chest_b'] * 0.75, -0.01])
        pts = [top + np.array([0.004 * i, -0.004 * i, -0.04 * i]) for i in range(6)]
        Vt, Ft, rt = loft(pts, [ellipse(12, 0.007, 0.028)] * 6, up_hint=(0, -1, 0))
        self._mesh('scarftail', Vt, Ft, m, weights={'chest': np.ones(len(Vt))}, sub=1)

    def _apron(self):
        s = self.s
        m = blib.cloth_material(self.name + '_apron', s['apron'], rough=0.8, sheen=0.3, scale=300, bump_str=0.1)
        z0 = self.hipZ - 0.42
        z1 = self.neckZ - 0.08
        R, K = 22, 30
        verts = []
        for i in range(R):
            z = z0 + (z1 - z0) * i / (R - 1)
            a, b, yoff, n = self._torso_profile(min(max(z, self.hipZ + s['coat_hem']), self.neckZ))
            if z < self.hipZ + s['coat_hem']:
                a, b, yoff, n = self._torso_profile(self.hipZ + s['coat_hem'])
                b = b + (self.hipZ + s['coat_hem'] - z) * 0.25
                a = a + (self.hipZ + s['coat_hem'] - z) * 0.18
            half = np.interp(z, [z0, self.hipZ, self.hipZ + 0.2, z1], [0.85, 0.8, 0.55, 0.45])
            ang = np.linspace(-half * np.pi / 2, half * np.pi / 2, K)
            x = (a + 0.006) * np.sin(ang)
            y = yoff - (b + 0.008) * np.cos(ang)
            verts.append(np.stack([x, y, np.full(K, z)], -1))
        Vv = np.concatenate(verts)
        F = []
        for i in range(R - 1):
            for k in range(K - 1):
                a_ = i * K + k
                F.append((a_, a_ + 1, a_ + K + 1, a_ + K))
        segs = {n: (np.array(self.J[n][0]), np.array(self.J[n][1])) for n in ('hips', 'spine', 'chest')}
        W = proximity_weights(Vv, segs, power=4)
        ob = self._mesh('apron', Vv, F, m, weights=W, sub=1)
        sol = ob.modifiers.new('Solidify', 'SOLIDIFY')
        sol.thickness = 0.004
        ob.modifiers.move(len(ob.modifiers) - 1, 1)

    # ---------------------------------------------------------------- hair
    def _build_hair(self):
        s = self.s
        style = s['hair_style']
        if not style:
            return
        import hair
        hs = s['head_scale']
        pts, rad = hair.groom(self.H, self.hg, style, seed=sum(map(ord, self.name)), under_hat=bool(s['hat']),
                              bun=s['bun'][:2] if s['bun'] else None, keep_top=s.get('hair_top', False))
        if pts is None:
            return
        pts = pts * hs + self.head_origin
        rad = rad * hs
        self.hair_under_hat = self._hair_objects('hair', pts, rad)
        self.hair_hatless = []
        if s['hat'] and s.get('hair_top'):
            # a full groom for the hatless beats (hidden; the shot toggles it against the under-hat one)
            fp, fr = hair.groom(self.H, self.hg, style, seed=sum(map(ord, self.name)) + 1, under_hat=False)
            self.hair_hatless = self._hair_objects('hairfree', fp * hs + self.head_origin, fr * hs)
            for ob in self.hair_hatless:
                ob.hide_render = True
                ob.hide_viewport = True
        if s.get('beard'):
            bp, br = hair.groom(self.H, self.hg, s['beard'], seed=7)
            bp = bp * hs + self.head_origin
            self._hair_objects('beard', bp, br * hs)

    def _hair_objects(self, nm, pts, rad):
        import hair
        s = self.s
        if s['hair_color2']:
            rng = np.random.default_rng(5)
            sel = rng.random(len(pts)) < 0.4
            parts = [(pts[~sel], rad[~sel], self.m_hair)]
            if not hasattr(self, 'm_hair2'):
                self.m_hair2 = blib.hair_material(self.name + '_hair2', s['hair_color2'])
            parts.append((pts[sel], rad[sel], self.m_hair2))
        else:
            parts = [(pts, rad, self.m_hair)]
        obs = []
        for i, (p, r, m) in enumerate(parts):
            if len(p) == 0:
                continue
            ob = hair.make_curves('%s_%s%d' % (self.name, nm, i), p, r, self.coll)
            ob.data.materials.append(m)
            self._rigid(ob, 'head')
            obs.append(ob)
        return obs
