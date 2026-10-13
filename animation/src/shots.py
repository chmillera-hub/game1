"""Brindle Cross: shot-by-shot performance (runs inside Blender).

Usage: blender -b --python shots.py -- <voice_dir> <out_dir> [preview]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import bpy
from mathutils import Vector, Matrix, Euler, Quaternion

import blib
import env
import perf
import props
import rigctl
from film import Film, fr, FPS, SZ, FY
from character import loft, ellipse
from perf import E

# ------------------------------------------------------------------ geography
EDITH = (2.95, 3.70)
DOOR_X = -0.9
LAMP = env.LAMP_XY
PATCH = env.PATCH_XY
PITCH = (1.35, 1.55)
KNEEL = (2.48, 3.30)
KNEEL_H = math.degrees(math.atan2(EDITH[0] - KNEEL[0], -(EDITH[1] - KNEEL[1])))
CARD = (0.55, FY - 0.02, SZ + 0.82)
WIN_TEDDY = (2.05, 4.16)


def V(*a):
    return Vector(a)


def heading_to(src, dst):
    return math.degrees(math.atan2(dst[0] - src[0], -(dst[1] - src[1])))


# ------------------------------------------------------------------ prop rigging
def bone_rest_world(C, bone):
    return C.arm.matrix_world @ C.arm.data.bones[bone].matrix_local


def setup_props(F):
    O = F.C['oswald']
    # --- bowler: re-parent hat + band under an empty driven by the prop system
    hr = bpy.data.objects.new('osw_hat_root', None)
    F.pc.objects.link(hr)
    hr.matrix_world = bone_rest_world(O, 'head')
    for ob in list(O.coll.objects):
        if ob.name in ('oswald_hat', 'oswald_hatband'):
            ob.parent = hr
            ob.parent_type = 'OBJECT'
            ob.parent_bone = ''
            ob.matrix_parent_inverse = hr.matrix_world.inverted()
            ob.matrix_basis = Matrix.Identity(4)
    F.prop('hat', hr)
    # where the hat sits relative to the head bone (identity at rest)
    F.hat_on = Matrix.Identity(4)
    # brim/crown geometry helpers in head-bone space
    hs = O.s['head_scale']
    F.osw_hs = hs
    # --- cane
    cane = props.cane(F.pc)
    F.prop('cane', cane)
    # --- loaf (whole, main part after tearing, torn end)
    F.prop('rye', props.loaf(F.pc, 'rye'))
    main = props.loaf(F.pc, 'rye_main')
    main.scale = (0.75, 1, 1)
    F.prop('rye_main', main)
    end = props.loaf(F.pc, 'rye_end', paper=False)
    end.scale = (0.32, 1.0, 1.0)
    F.prop('rye_end', end)
    # --- juggling balls (wooden)
    mball = blib.principled('wood_ball', (0.45, 0.22, 0.08), rough=0.35, coat=0.4)
    for i in range(3):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.032, segments=20, ring_count=10)
        b = bpy.context.object
        for c in b.users_collection:
            c.objects.unlink(b)
        F.pc.objects.link(b)
        b.name = 'ball%d' % i
        bpy.ops.object.shade_smooth()
        blib.assign(b, mball)
        F.prop('ball%d' % i, b)
    # --- peels, coins, tray
    p1 = props.banana_peel(F.pc, 'peel1')
    p2 = props.banana_peel(F.pc, 'peel2')
    F.peels = (p1, p2)
    for i in range(3):
        F.prop('coin%d' % i, props.coin(F.pc, 'coin%d' % i))
    tray = make_tray(F)
    F.prop('tray', tray)
    F.prop('basket', props.basket(F.pc, 'basket'))
    F.hat_plan = []
    # --- held coat (in Oswald's hands, 3.17) and Edith's drape
    F.held_coat = make_held_coat(F)
    F.prop('held_coat', F.held_coat)
    F.drape = make_drape(F)
    # --- shoulder/cap snow on Edith
    F.snowline = make_snowline(F)
    # --- tear
    F.tear = make_tear(F)
    F.prop('tear', F.tear)


def make_tray(F):
    m = blib.principled('tray_m', (0.35, 0.33, 0.30), rough=0.4, metallic=0.8)
    bpy.ops.mesh.primitive_cube_add(size=1)
    t = bpy.context.object
    for c in t.users_collection:
        c.objects.unlink(t)
    F.pc.objects.link(t)
    t.name = 'tray'
    t.data.transform(Matrix.Diagonal((0.46, 0.32, 0.015, 1)))
    blib.assign(t, m)
    mb = blib.principled('tray_rye', (0.30, 0.16, 0.06), rough=0.6)
    for i in range(6):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=16, ring_count=8)
        r = bpy.context.object
        for c in r.users_collection:
            c.objects.unlink(r)
        F.pc.objects.link(r)
        r.data.transform(Matrix.Diagonal((0.055, 0.035, 0.03, 1)))
        r.location = (-0.15 + (i % 3) * 0.15, -0.07 + (i // 3) * 0.14, 0.03)
        bpy.ops.object.shade_smooth()
        blib.assign(r, mb)
        r.parent = t
    return t


def make_held_coat(F):
    O = F.C['oswald']
    V_, Fc = [], []
    nu, nv = 14, 10
    for i in range(nv):
        for j in range(nu):
            u = j / (nu - 1) - 0.5
            v = i / (nv - 1)
            V_.append([u * 0.62 + 0.03 * math.sin(v * 3), 0.05 * math.cos(u * 5) * v, -v * 0.62])
    for i in range(nv - 1):
        for j in range(nu - 1):
            a = i * nu + j
            Fc.append((a, a + 1, a + nu + 1, a + nu))
    ob = blib.make_mesh('held_coat', np.array(V_), Fc, coll=F.pc)
    blib.assign(ob, blib.cloth_material('held_mustard', O.s['coat']))
    s = ob.modifiers.new('sol', 'SOLIDIFY')
    s.thickness = 0.01
    blib.subsurf(ob, 1)
    return ob


def make_drape(F):
    """Mustard coat around Edith's shoulders (deforms with her rig)."""
    Ed = F.C['edith']
    O = F.C['oswald']
    s = Ed.s
    top = Ed.neckZ
    R, K = 12, 40
    rings = []
    for i in range(R):
        u = i / (R - 1)                      # 0 at collar, 1 at hem
        z = top + 0.05 - u * 0.62
        a, b, yoff, n = Ed._torso_profile(min(max(z, Ed.hipZ + s['coat_hem']), top))
        ww = np.interp(u, [0, 0.12, 0.3, 1.0], [s['neck_r'] + 0.035, s['shoulder_w'] + 0.075, a + 0.10, a + 0.12])
        dd = np.interp(u, [0, 0.12, 0.3, 1.0], [s['neck_r'] + 0.03, b + 0.04, b + 0.06, b + 0.08])
        ang = np.linspace(np.radians(-150 + 25 * u), np.radians(150 - 25 * u), K)
        x = ww * np.sin(ang)
        y = yoff + dd * np.cos(ang) * 1.0
        rings.append(np.stack([x, y, np.full(K, z)], -1))
    P = np.concatenate(rings)
    Fc = []
    for i in range(R - 1):
        for k in range(K - 1):
            a_ = i * K + k
            Fc.append((a_, a_ + 1, a_ + K + 1, a_ + K))
    segs = {n: (np.array(Ed.J[n][0]), np.array(Ed.J[n][1])) for n in ('chest', 'spine', 'neck')}
    for sd in 'LR':
        segs['clavicle.' + sd] = (np.array(Ed.J['clavicle.' + sd][0]), np.array(Ed.J['clavicle.' + sd][1]))
        segs['upperarm.' + sd] = (np.array(Ed.J['upperarm.' + sd][0]), np.array(Ed.J['upperarm.' + sd][1]))
    W = character_prox(P, segs)
    m = blib.cloth_material('drape_mustard', O.s['coat'])
    ob = Ed._mesh('drape', P, Fc, m, weights=W, sub=1)
    sol = ob.modifiers.new('sol', 'SOLIDIFY')
    sol.thickness = 0.012
    ob.modifiers.move(len(ob.modifiers) - 1, 1)
    return ob


def character_prox(P, segs):
    from character import proximity_weights
    return proximity_weights(P, segs, power=4)


def make_snowline(F):
    Ed = F.C['edith']
    s = Ed.s
    pts = []
    rng = np.random.default_rng(4)
    top = Ed.neckZ
    for sd in (1, -1):
        for k in range(26):
            x = sd * (s['neck_r'] + 0.02 + k * 0.0055)
            a, b, yoff, n = Ed._torso_profile(top - 0.02)
            z = top - 0.012 - 0.12 * max(0, abs(x) - s['shoulder_w'] * 0.5) - 0.002 * k + rng.normal(0, 0.002)
            pts.append((x, yoff + rng.normal(0, 0.01), z + 0.012))
    sn = props.snow_dots(F.pc, 'edith_snow_shoulders', pts, r=0.0075)
    # on the cap: along the top
    hs = s['head_scale']
    capp = []
    for k in range(30):
        a = -1.2 + 2.4 * k / 29
        p = np.array([0.07 * math.sin(a), 0.02 - 0.06 * math.cos(a) * 0.3, 0.115]) * hs + Ed.head_origin
        capp.append(tuple(p + rng.normal(0, 0.003, 3)))
    sc = props.snow_dots(F.pc, 'edith_snow_cap', capp, r=0.007)
    # parent rigidly to bones (rest-pose world coords -> bone space)
    for ob, bone in ((sn, 'chest'), (sc, 'head')):
        blib.parent_to_bone(ob, Ed.arm, bone)
    return (sn, sc)


def make_tear(F):
    m = bpy.data.materials.new('tear')
    m.use_nodes = True
    N = m.node_tree.nodes
    b = N['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.70, 0.85, 1.0, 1)
    b.inputs['Roughness'].default_value = 0.02
    b.inputs['Transmission Weight'].default_value = 0.6
    b.inputs['Coat Weight'].default_value = 1.0
    b.inputs['Emission Color'].default_value = (0.55, 0.75, 1.0, 1)
    b.inputs['Emission Strength'].default_value = 0.25
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=16, ring_count=10)
    t = bpy.context.object
    for c in t.users_collection:
        c.objects.unlink(t)
    F.pc.objects.link(t)
    t.name = 'tear'
    t.data.transform(Matrix.Diagonal((0.0026, 0.0018, 0.0036, 1)))
    bpy.ops.object.shade_smooth()
    blib.assign(t, m)
    return t


# ------------------------------------------------------------------ cameras / constants
DIAL = Vector((env.TOWER[0], env.TOWER[1] - 2.3 - 0.04, env.TOWER[2]))
CAM11 = dict(loc=(1.75, -9.6, 1.2), target=(2.15, 4.0, 3.85), lens=33.0)
# cane in the right hand: shaft along the hand's pinky-side axis (+X for R), crook above the fist
CANE_GRIP = Matrix(((0, 0, -1, -0.05), (0, 1, 0, 0.06), (1, 0, 0, -0.015), (0, 0, 0, 1)))


def cane_hang(F, bone='forearm.L', along=0.55):
    """Cane hooked over a forearm, hanging plumb."""
    def fn(t):
        C = F.C['oswald']
        pb = C.arm.pose.bones[bone]
        p = C.arm.matrix_world @ (pb.head.lerp(pb.tail, along))
        x, y, z, h = F.A['oswald'].root_at(t)
        R = Euler((0, 0, math.radians(h + 90))).to_matrix().to_4x4()
        return Matrix.Translation(p) @ R @ Matrix.Translation((0, 0.05, -0.035))
    return fn


def cane_twirl(F, t0, t1, turns=2.0):
    def fn(t):
        C = F.C['oswald']
        M = C.arm.matrix_world @ C.arm.pose.bones['hand.R'].matrix
        u = perf.ease((t - t0 - 0.25) / max(t1 - t0 - 0.6, 0.1), 'inout')
        ang = 2 * math.pi * turns * u
        piv = Vector((0.0, 0.06, -0.015))
        R = Matrix.Translation(piv) @ Matrix.Rotation(ang, 4, 'Y') @ Matrix.Translation(-piv)
        return M @ R @ CANE_GRIP
    return fn


# ------------------------------------------------------------------ helper gestures
def head_pt(C, p):
    """head-space point (unscaled headgen coords) -> rest armature/world."""
    return tuple(C.hp(p))


def hat_tip_matrix(lift=0.03, ang=18.0, fwd=0.01):
    # head bone local: Y up, Z forward, X left.  Front dips when rotating about +X.
    return Matrix.Translation((0, lift, fwd)) @ Euler((math.radians(ang), 0, 0)).to_matrix().to_4x4()


def tip_hat(F, t, dur=1.0, ang=18.0, lift=0.035, actor='oswald'):
    """Right hand to the brim, lift + dip, back down. Returns (t_up, t_down)."""
    A = F.A[actor]
    C = F.C[actor]
    hs = C.s['head_scale']
    hp = C.H.p
    brim = C.hp((-0.055, -hp['ry'] * 1.02, 0.072))
    A.gesture(t, 'R', ('head', brim, (0.1, -0.4, 1.0), (-0.9, 0.0, 0.2)), dur=dur * 0.3)
    A.fingers(t, 'R', 0.55, thumb=0.6, dur=dur * 0.3)
    t_up = t + dur * 0.3
    t_dn = t + dur * 0.75
    hat_track(F, t_up, hat_tip_matrix(lift, ang), dur=dur * 0.2)
    hat_track(F, t_dn, Matrix.Identity(4), dur=dur * 0.25)
    A.release(t + dur * 0.8, 'R', dur=dur * 0.35)
    A.fingers(t + dur * 0.8, 'R', 0.35, dur=0.3)
    A.nod(t_up, amt=7, dur=dur * 0.6)
    return t_up, t_dn


def hat_track(F, t, local, dur=0.2):
    """Hat on the head with a time-varying local offset (smoothly interpolated)."""
    if not hasattr(F, '_hat_keys'):
        F._hat_keys = []
    F._hat_keys.append((t, local, dur))


def finalize_hat(F, segments):
    """segments: list of (t0, t1, mode, data). modes: 'head' (uses _hat_keys), 'hand', 'drop'/'lift'
    (glide from the last matrix to a target over the segment), 'world'."""
    keys = sorted(getattr(F, '_hat_keys', []), key=lambda k: k[0])
    F._hat_last = [None]

    def head_local(t):
        cur = Matrix.Identity(4)
        for (tk, M, d) in keys:
            if t < tk:
                break
            u = perf.ease((t - tk) / max(d, 1e-3))
            l0, r0, s0 = cur.decompose()
            l1, r1, s1 = M.decompose()
            cur = Matrix.LocRotScale(l0.lerp(l1, u), r0.slerp(r1, u), s0.lerp(s1, u))
        return cur

    def head_now(t):
        C = F.C['oswald']
        pb = C.arm.pose.bones['head']
        return C.arm.matrix_world @ pb.matrix @ head_local(t)

    for (t0, t1, mode, data) in segments:
        if mode == 'head':
            def fn(t):
                M = head_now(t)
                F._hat_last[0] = M
                return M
        elif mode == 'hand':
            def fn(t, d=data):
                M = F._src_matrix(d, t)
                F._hat_last[0] = M
                return M
        elif mode in ('drop', 'lift', 'to_head'):
            def fn(t, d=data, a=t0, b=t1, mode=mode, start=[None]):
                if start[0] is None:
                    start[0] = F._hat_last[0] if F._hat_last[0] is not None else Matrix.Identity(4)
                tgt = head_now(t) if mode == 'to_head' else (F._src_matrix(d, t) if isinstance(d, tuple) else d)
                u = perf.ease((t - a) / max(b - a, 1e-3), 'in' if mode == 'drop' else 'inout')
                l0, r0, s0 = start[0].decompose()
                l1, r1, s1 = tgt.decompose()
                l = l0.lerp(l1, u)
                if mode != 'drop':
                    l.z += 0.08 * math.sin(math.pi * u)
                M = Matrix.LocRotScale(l, r0.slerp(r1, u), s0.lerp(s1, u))
                F._hat_last[0] = M
                return M
        else:
            def fn(t, d=data):
                M = F._src_matrix(d, t)
                F._hat_last[0] = M
                return M
        F.attach('hat', t0, t1, ('fn', fn))


def hand_hold(px=0.0, py=0.0, pz=0.0, rx=0.0, ry=0.0, rz=0.0):
    """Local matrix in the hand bone frame (Y along fingers, Z back of hand, X thumb side for L)."""
    return Matrix.Translation((px, py, pz)) @ Euler((math.radians(rx), math.radians(ry), math.radians(rz))).to_matrix().to_4x4()


def world_m(loc, rot=(0, 0, 0)):
    return Matrix.Translation(loc) @ Euler([math.radians(a) for a in rot]).to_matrix().to_4x4()


def far_away(F, name, t=0.0):
    F.A[name].place(t, 40.0 + len(name), -30.0, 0.0)


# ------------------------------------------------------------------ lighting
def lighting(F):
    W = F.W
    bg = W['bg']
    sun = W['sun']
    pool = F.light('pool', 'AREA', loc=(0.6, 3.15, 2.3), target=(0.9, 2.6, 0.0), energy=0, size=2.2,
                   color=(1.0, 0.62, 0.32))
    F.pool = pool
    # dusk progression keyed on absolute time (filled in after shots know their times)
    return pool


def face_lights(F, t0, t1):
    ed = V(EDITH[0], EDITH[1] - 0.05, SZ + 0.75)
    F.light('key_window', 'AREA', loc=(1.55, 2.95, SZ + 1.25), target=(2.75, 3.45, SZ + 0.80), energy=34, size=0.9,
            color=(1.0, 0.70, 0.45), t0=t0, t1=t1)
    F.light('fill_sky', 'AREA', loc=(3.1, 1.55, SZ + 1.6), target=(2.75, 3.5, SZ + 0.75), energy=16, size=1.6,
            color=(0.62, 0.74, 1.0), t0=t0, t1=t1)
    F.light('rim_edith', 'AREA', loc=(3.75, 3.95, SZ + 1.25), target=tuple(ed), energy=9, size=0.5,
            color=(0.65, 0.78, 1.0), t0=t0, t1=t1)


def time_of_day(F, t, sky, sun, dur=4.0):
    F.key_val(F.W['bg'].inputs['Strength'], 'default_value', t, sky, dur)
    F.key_val(F.W['sun'].data, 'energy', t, sun, dur)


def pool_light(F, t, energy, size=2.2, dur=0.8, reach=0.0):
    F.key_val(F.pool.data, 'energy', t, energy, dur)
    F.key_val(F.pool.data, 'size', t, size, dur)
    # reach > 0 slides the pool toward Edith
    F.key_val(F.pool, 'location', t, 0.6 + reach * 1.6, dur, index=0)


def edith_base(F, t=0.0):
    A = F.A['edith']
    A.place(t, EDITH[0], EDITH[1], 0.0, z=SZ)
    A.posture(t, 'sit_wall', dur=0.01, sill=0.0, knees=0.95, back=0.10, hands='knees')


# ====================================================================== SCENE 1
def s1_1(F):
    T = F.begin('1.1', 'Wide: Brindle Cross')
    Ed, Te, To, Pl = F.A['edith'], F.A['teddy'], F.A['tomas'], F.A['plum']
    F.camera(CAM11['loc'], CAM11['target'], CAM11['lens'])
    edith_base(F, T)
    Ed.head(T, pitch=10, dur=0.01)
    Ed.expr(T, gaze_pitch=-16, lid_L=0.85, lid_R=0.85, brow_in=0.25, smile=-0.15, dur=0.01)
    Ed.hold_eyes(T, T + 4.5)
    Ed.expr(T + 2.3, blink=1.0, dur=0.28)
    Ed.expr(T + 2.62, blink=0.0, dur=0.45)
    Ed.breath_pulse(T + 1.2, dur=1.8, amt=1.4)
    # Teddy, nose to the window, watching the square for the clown
    Te.place(T, WIN_TEDDY[0], WIN_TEDDY[1], 0.0, z=SZ - 0.02)
    Te.posture(T, 'stand', dur=0.01, splay=6, lean=8, toes=0.3)
    for sd, sx in (('L', 1), ('R', -1)):
        Te.gesture(T, sd, ('world', (WIN_TEDDY[0] + sx * 0.17, FY + 0.05, SZ + 0.70), (sx * 0.2, -0.3, 1.0), (0, 1, 0)), dur=0.01)
        Te.fingers(T, sd, 0.25, spread=0.4, dur=0.01)
    Te.look_at(T, V(0.0, -4.0, 1.0), dur=0.01)
    Te.look_at(T + 1.6, V(-1.5, -3.0, 0.9), dur=0.8)
    Te.look_at(T + 3.2, V(1.5, -3.5, 1.1), dur=0.7)
    Te.expr(T, brow=0.35, jaw=0.15, lid_L=1.1, lid_R=1.1, dur=0.01)
    # Tomas at work behind the counter
    To.place(T, 0.7, 5.75, 0.0, z=SZ - 0.02)
    To.posture(T, 'stand', dur=0.01, lean=12, splay=10)
    To.expr(T, lid_L=0.7, lid_R=0.7, press=0.4, dur=0.01)
    # plum-coat woman crosses along the pavement, passing in front of Edith without turning
    Pl.place(T, -1.2, 3.08, -90, z=SZ)
    Pl.posture(T, 'stand', dur=0.01)
    Pl.walk(T + 0.5, T + 5.2, [(-1.2, 3.08), (4.8, 3.02)], stride=0.62, splay=6, z=SZ)
    Pl.look_at(T, V(6.0, 2.5, 1.5), dur=0.01)
    Pl.expr(T, lid_L=0.9, lid_R=0.9, dur=0.01)
    Pl.gesture(T, 'L', ('chest', (0.24, -0.05, Pl.B.hipZ + 0.18), (0.2, -1, 0.2), (1, 0, 0.2)), dur=0.01)
    Pl.fingers(T, 'L', 0.8, dur=0.01)
    F.attach('basket', T, T + 6, ('hand', 'plum', 'L', hand_hold(0.0, 0.05, -0.13, 90, 0, 0)))
    for n in ('oswald', 'flatcap', 'paper'):
        far_away(F, n, T)
    F.door(T - 0.1, 26, 0.01)
    F.clock(T - 0.1, 3, 29)
    pool_light(F, T - 0.1, 120, 2.0, 0.01)
    F.label(T + 0.25, 4.0, 'BRINDLE CROSS', 'A Sunday in November')
    a, b = F.say('N01', T + 0.7)
    F.cue('civic', T, 39.0, gain=-4.0, end='phrase')
    F.sfx('wind', T, gain=-20.0, duration=215.0)
    F.sfx('footsteps_distant', T, gain=-26.0, duration=38.0)
    F.end(T + 4.5)


def s1_2(F):
    T = F.begin('1.2', 'Dial push-in')
    d = DIAL
    F.camera((d.x - 0.6, -4.2, 2.0), d + Vector((0, 0, -0.6)), 48, loc2=(d.x - 0.5, -2.6, 2.6), target2=d + Vector((0, 0, -0.3)), t_move=(T, T + 7.6), ease='linear')
    a, b = F.say('N02', T + 0.4)
    F.label(T + 0.5, 3.4, 'THE CLOCK', 'Tower, 1871')
    F.clock(b + 0.35, 3, 30, dur=0.08)
    F.sfx('clock_clunk', b + 0.35, gain=-6.0)
    a2, b2 = F.say('N03', b + 0.85)
    F.end(b2 + 0.4)


def s1_3(F):
    T = F.begin('1.3', 'Truck along the window to the card, rack to Tomas')
    To = F.A['tomas']
    y, z = FY - 1.05, SZ + 1.32
    a, b = F.say('N04', T + 0.4)
    a2, b2 = F.say('N05', b + 0.45)
    a3, b3 = F.say('N06', b2 + 0.5)
    F.camera((0.05, y, z), (0.05, FY + 1.0, SZ + 1.0), 45, fstop=2.2,
             keys=[(T, (0.05, y, z), (0.05, FY + 1.0, SZ + 1.0)),
                   (T + 3.0, (0.55, y, z), (0.55, FY + 1.0, SZ + 0.95)),
                   (b2 + 0.1, (0.55, y, z), (0.55, FY + 1.0, SZ + 0.95)),
                   (b3 + 0.6, (0.95, y + 0.1, z), (0.95, FY + 1.0, SZ + 1.25))],
             focus_keys=[(-1e9, -1e9, V(0.0, FY + 0.55, SZ + 1.2)),
                         (T + 2.3, T + 2.9, V(*CARD)),
                         (b2 + 0.1, b2 + 0.9, ('actor', 'tomas', 'head'))])
    # Tomas slides a tray of small rye onto the shelf
    To.place(T, 0.95, FY + 1.18, 0.0, z=SZ - 0.02)
    To.posture(T, 'stand', dur=0.01, lean=4, splay=10)
    for sd, sx in (('L', 1), ('R', -1)):
        To.gesture(T, sd, ('world', (0.95 + sx * 0.24, FY + 0.80, SZ + 1.40), (0, -1, 0), (0, 0, 1)), dur=0.01)
        To.gesture(T + 2.8, sd, ('world', (0.95 + sx * 0.24, FY + 0.60, SZ + 1.36), (0, -1, 0), (0, 0, 1)), dur=1.6)
        To.fingers(T, sd, 0.45, thumb=0.2, dur=0.01)
    F.attach('tray', T, T + 9, ('fn', lambda t, T=T: world_m((0.95, FY + 0.80 - 0.22 * perf.ease((t - T - 2.8) / 1.6), SZ + 1.33))))
    To.look_at(T, V(0.95, FY + 0.5, SZ + 1.3), dur=0.01)
    To.expr(T, lid_L=0.62, lid_R=0.62, press=0.55, brow=-0.1, dur=0.01)
    To.expr(a3 + 0.3, brow=-0.45, brow_in=-0.3, dur=0.4)
    To.look_at(a3 + 1.0, V(DOOR_X, FY - 0.2, SZ + 1.2), dur=0.25)
    To.expr(a3 + 1.0, smile=-0.35, lid_L=0.55, lid_R=0.55, dur=0.25)
    To.look_at(a3 + 1.7, V(0.95, FY + 0.5, SZ + 1.3), dur=0.4)
    F.sfx('oven_hum', T, gain=-24.0, duration=8.5)
    F.sfx('tray_clatter', T + 4.2, gain=-16.0)
    F.label(a3, 3.0, 'TOMAS BRANDT', 'Baker')
    F.end(b3 + 0.5)


def s1_4(F):
    T = F.begin('1.4', 'Teddy in the doorway')
    Te, To, Ed = F.A['teddy'], F.A['tomas'], F.A['edith']
    tx, ty = DOOR_X + 0.12, FY - 0.12
    head_z = SZ + 0.98
    cam = (DOOR_X - 1.75, FY - 1.05, SZ + 0.98)
    F.camera(cam, (DOOR_X + 0.6, FY - 0.10, SZ + 0.82), 55, focus=('actor', 'teddy', 'head'), fstop=2.0)
    Te.place(T, tx, ty, -25.0, z=SZ)
    Te.posture(T, 'stand', dur=0.01, splay=10, lean=3)
    # one hand on the door frame
    Te.gesture(T, 'L', ('world', (DOOR_X + 0.47, FY - 0.04, SZ + 0.78), (0.1, 0.2, 1.0), (0.4, -0.9, 0)), dur=0.01)
    Te.fingers(T, 'L', 0.55, dur=0.01)
    # rocking heel to toe
    for k in range(6):
        Te.posture(T + 0.2 + k * 0.62, 'stand', dur=0.3, splay=10, lean=3, toes=0.35 if k % 2 == 0 else 0.0)
    Te.look_at(T, V(-1.5, -2.5, 1.0), dur=0.01)
    Te.look_at(T + 0.9, V(1.8, -2.0, 1.0), dur=0.6)
    Te.expr(T, brow=0.3, jaw=0.18, lid_L=1.1, lid_R=1.1, smile=0.2, dur=0.01)
    a, b = F.say('N07', T + 0.3)
    F.label(a, 4.2, 'TEDDY BRANDT', 'Age 8', correct=dict(t=b + 0.55, text='Age 8 (nearly 9)'))
    t8 = b - 0.45
    Te.expr(t8, brow=-0.3, brow_in=-0.75, jaw=0.0, press=0.5, smile=-0.3, lid_L=0.85, lid_R=0.85, dur=0.25)
    lbl = V(*cam) + (V(DOOR_X + 0.6, FY - 0.1, SZ + 0.82) - V(*cam)).normalized() * 1.2 + V(0, -0.7, -0.05)
    Te.look_at(t8 + 0.05, lbl, dur=0.3)
    F.sfx('typewriter', b + 0.55, gain=-14.0)
    Te.look_at(b + 0.9, lbl, dur=0.2)
    Te.nod(b + 1.05, amt=13, dur=0.55, n=2)
    Te.expr(b + 1.05, brow=0.2, brow_in=0.0, press=0.3, smile=0.45, dur=0.3)
    Te.look_at(b + 1.7, V(1.8, -2.0, 1.0), dur=0.4)
    a2, b2 = F.say('T01', b + 2.0)
    # huge eye-roll with the whole head
    Te.expr(a2 + 0.35, gaze_pitch=22, lid_L=0.8, lid_R=0.8, smile=-0.4, brow=0.3, dur=0.25)
    Te.head(a2 + 0.35, pitch=-12, yaw=-15, roll=-10, dur=0.35)
    Te.head(a2 + 0.75, pitch=-8, yaw=15, roll=10, dur=0.4)
    Te.head(a2 + 1.2, pitch=6, yaw=0, roll=0, dur=0.35)
    Te.expr(a2 + 1.2, gaze_pitch=0, lid_L=0.85, lid_R=0.85, dur=0.3)
    Te.shoulders(a2 + 1.25, -10, dur=0.4)
    Te.chest(a2 + 1.25, pitch=12, dur=0.4)
    Te.release(b2 - 0.1, 'L', dur=0.3)
    Te.walk(b2 + 0.0, b2 + 1.2, [(tx, ty), (DOOR_X + 0.05, FY + 0.65)], stride=0.3, z=SZ)
    F.door(b2 + 0.9, 0, 0.55)
    F.sfx('shop_bell', b2 + 1.42, gain=-8.0)
    F.sfx('door_thunk', b2 + 1.45, gain=-6.0)
    pool_light(F, b2 + 1.45, 70, 1.8, 0.4)
    # background: Edith stays put
    Ed.expr(T, gaze_pitch=-16, dur=0.01)
    To.place(T, 0.3, 5.8, 180.0, z=SZ - 0.02)
    F.end(b2 + 1.9)


def s1_5(F):
    T = F.begin('1.5', 'The lamp')
    F.camera((LAMP[0] - 1.25, LAMP[1] - 2.6, SZ + 1.5), (LAMP[0] - 0.05, LAMP[1], SZ + 1.55), 40,
             focus=V(LAMP[0], LAMP[1], SZ + 1.5), fstop=2.8)
    a, b = F.say('N08', T + 0.3)
    F.label(T + 0.3, 3.0, 'THE LAMP', 'Automatic, 1926')
    Te = F.A['teddy']
    Te.place(T, WIN_TEDDY[0], WIN_TEDDY[1], 0.0, z=SZ - 0.02)
    Te.posture(T, 'stand', dur=0.01, splay=6, lean=8, toes=0.3)
    for sd in 'LR':
        Te.release(T, sd, dur=0.01)
    Te.look_at(T, V(0.5, -3.0, 1.0), dur=0.01)
    F.end(T + 3.5)


def s1_6(F):
    T = F.begin('1.6', "Oswald's entrance")
    O, Fc, Ed = F.A['oswald'], F.A['flatcap'], F.A['edith']
    F.camera((1.25, -4.4, 1.65), (1.7, 2.6, 1.05), 30)
    # Oswald waddles in from frame left with a cane twirl
    start = (-1.6, 0.95)
    O.place(T, start[0], start[1], -90.0)
    O.posture(T, 'stand', dur=0.01, splay=26, knee=0.25, stoop=6)
    O.walk(T + 0.1, T + 2.3, [start, (0.2, 1.3), PITCH], stride=0.38, splay=26, style='waddle', bob=0.028,
           sway=0.024, lift=0.05)
    O.expr(T, smile=0.55, brow=0.25, dur=0.01)
    O.look_at(T, V(0.5, -5, 1.6), dur=0.01)
    F.attach('cane', T, T + 2.3, ('fn', cane_twirl(F, T, T + 2.3)))
    F.attach('cane', T + 2.3, T + 8, ('hand', 'oswald', 'R', CANE_GRIP))
    O.fingers(T, 'R', 0.75, thumb=0.8, dur=0.01)
    O.gesture(T, 'R', ('chest', (-0.30, -0.14, O.B.hipZ + 0.12), (0.0, -0.4, -1.0), (-1, 0.2, 0)), dur=0.01)
    F.label(T + 0.8, 3.0, 'OSWALD BUNCE', 'Entertainer')
    a, b = F.say('N09', T + 0.8)
    # flat-cap man passes; Oswald tips his hat to him
    Fc.place(T, 5.8, 0.65, 90.0)
    Fc.posture(T, 'stand', dur=0.01)
    Fc.walk(T + 0.0, T + 7.2, [(5.8, 0.65), (-3.2, 0.55)], stride=0.66, splay=6)
    Fc.look_at(T, V(-6, 0.4, 1.6), dur=0.01)
    O.turn(T + 2.35, -25.0, dur=0.4)
    O.look_at(T + 2.3, ('actor', 'flatcap', 'head'), dur=0.3)
    tip_hat(F, T + 2.45, dur=1.0)
    O.expr(T + 2.45, smile=0.75, brow=0.45, dur=0.3)
    Fc.look_at(T + 2.5, ('actor', 'oswald', 'head'), dur=0.3)
    Fc.nod(T + 2.95, amt=8, dur=0.5)
    Fc.expr(T + 2.9, smile=0.3, brow=0.2, dur=0.3)
    # ...and with exactly the same courtesy to the empty cobbles behind him
    O.turn(T + 3.45, 175.0, dur=0.5)
    O.look_at(T + 3.45, V(PATCH[0], PATCH[1], 1.62), dur=0.4)
    tip_hat(F, T + 3.95, dur=1.0)
    Fc.look_at(T + 4.3, V(PATCH[0], PATCH[1], 0.4), dur=0.35)
    Fc.expr(T + 4.3, brow_in=0.5, brow_asym=0.5, smile=0.0, dur=0.3)
    Fc.look_at(T + 5.2, V(-6, 0.4, 1.6), dur=0.5)
    Fc.expr(T + 5.2, brow_in=0.0, brow_asym=0.0, dur=0.5)
    # back to his public; hat off and down, upside down at his feet
    O.turn(T + 5.0, 0.0, dur=0.45)
    O.look_at(T + 5.0, V(1.1, -6.0, 1.6), dur=0.4)
    hat_ground = world_m((PITCH[0] + 0.02, PITCH[1] - 0.42, 0.075), (180, 0, 15))
    F.hat_plan.append((0.0, T + 5.15, 'head', None))
    hp = F.C['oswald'].H.p
    brim_top = F.C['oswald'].hp((0.0, -hp['ry'] * 0.2, 0.17))
    O.gesture(T + 5.0, 'R', ('head', brim_top, (0, 0.3, 1), (-1, 0, 0)), dur=0.2)
    O.fingers(T + 5.0, 'R', 0.6, thumb=0.6, dur=0.2)
    O.gesture(T + 5.35, 'R', ('chest', (-0.18, -0.36, O.B.hipZ + 0.10), (0, -0.3, -1), (-1, 0, 0)), dur=0.3)
    F.hat_plan.append((T + 5.15, T + 5.6, 'hand', ('hand', 'oswald', 'R', hand_hold(0.0, 0.08, -0.11, 180, 0, 0))))
    F.hat_plan.append((T + 5.6, T + 5.85, 'drop', hat_ground))
    F.hat_plan.append((T + 5.85, 1e9, 'world', ('world', hat_ground)))
    O.release(T + 5.75, 'R', dur=0.3)
    a2, b2 = F.say('N10', T + 5.3)
    # silent act: big closed-mouth grin, finger to lips, solemn little shake
    O.expr(a2 + 0.2, smile=1.0, press=0.35, brow=0.5, lidlo_L=0.5, lidlo_R=0.5, dur=0.3)
    mouth = F.C['oswald'].hp(F.C['oswald'].hg['mouth_c'] + np.array([-0.004, -0.045, 0.0]))
    O.gesture(a2 + 0.25, 'L', ('head', mouth, (0.05, 0.2, 1.0), (0.3, -0.9, 0.0)), dur=0.35)
    O.fingers(a2 + 0.25, 'L', 0.9, thumb=0.8, per={'index': 0.0, 'middle': 0.95, 'ring': 0.95, 'pinky': 0.95}, dur=0.25)
    O.shake(a2 + 0.7, amt=6, dur=0.8, n=2)
    O.release(b2 + 0.25, 'L', dur=0.4)
    O.fingers(b2 + 0.25, 'L', 0.35, dur=0.3)
    F.sfx('footsteps_waddle', T + 0.1, gain=-12.0, n=6, interval=0.36)
    Ed.expr(T, gaze_pitch=-16, dur=0.01)
    F.end(b2 + 0.4)


# ====================================================================== SCENE 2
CROWD = {'plum': (1.02, -2.2, 182.0), 'flatcap': (1.62, -2.35, 178.0), 'paper': (2.18, -2.15, 186.0)}


def crowd_place(F, T):
    for n, (x, y, h) in CROWD.items():
        a = F.A[n]
        a.place(T, x, y, h)
        a.posture(T, 'stand', dur=0.01, splay=8)
        a.look_at(T, ('actor', 'oswald', 'head'), dur=0.01)
        a.expr(T, smile=0.3, brow=0.2, dur=0.01)


def crowd_laugh(F, t, dur=2.4, big=True):
    for i, n in enumerate(('plum', 'flatcap', 'paper')):
        a = F.A[n]
        d = 0.08 * i
        a.expr(t + d, smile=1.0 if big else 0.6, jaw=0.35 if big else 0.1, lid_L=0.6, lid_R=0.6, lidlo_L=0.7,
               lidlo_R=0.7, brow=0.4, dur=0.2)
        a.bounce(t + d, dur=dur, amt=0.014 if big else 0.008, n=5)
        a.head(t + d, pitch=-10, dur=0.3)
        a.head(t + d + dur, pitch=0, dur=0.6)
        a.expr(t + d + dur, smile=0.35, jaw=0.0, lid_L=1.0, lid_R=1.0, lidlo_L=0.2, lidlo_R=0.2, dur=0.6)
    # plum: glove at the mouth; flatcap: slaps his knee
    pl = F.A['plum']
    mouth = F.C['plum'].hp(F.C['plum'].hg['mouth_c'] + np.array([0.0, -0.05, -0.01]))
    pl.gesture(t + 0.1, 'R', ('head', mouth, (0.2, 0.0, 1.0), (-0.3, -0.9, 0)), dur=0.3)
    pl.release(t + dur, 'R', dur=0.5)
    fc = F.A['flatcap']
    for k in range(3):
        tt = t + 0.2 + k * 0.45
        fc.gesture(tt, 'R', ('chest', (-0.16, -0.30, fc.B.hipZ - 0.12), (0, -0.3, -1), (-1, 0, 0)), dur=0.18)
        fc.gesture(tt + 0.22, 'R', ('chest', (-0.24, -0.24, fc.B.hipZ + 0.10), (0, -0.3, -1), (-1, 0, 0)), dur=0.2)
    fc.release(t + 1.7, 'R', dur=0.4)


JUGGLE = dict(period=1.05, height=0.42)


def juggle_hands(F, t0, t1):
    """Hands make small alternating scoops in front of the chest."""
    O = F.A['oswald']
    hz = O.B.hipZ + 0.30
    t = t0
    k = 0
    while t < t1:
        for sd, sx in (('L', 1), ('R', -1)):
            ph = (k + (0 if sd == 'R' else 0.5)) * JUGGLE['period'] / 2
            up = (k % 2 == 0) == (sd == 'R')
            O.gesture(t, sd, ('chest', (sx * 0.15, -0.33, hz + (0.05 if up else -0.02)), (0, -1, 0.2), (0, 0.2, -1)), dur=0.22)
        t += JUGGLE['period'] / 2
        k += 1
    for sd in 'LR':
        O.fingers(t0, sd, 0.45, thumb=0.4, dur=0.2)


def ball_fn(F, i, t_juggle0, t_clong, landing):
    cache = {}

    def palm(sd):
        C = F.C['oswald']
        M = C.arm.matrix_world @ C.arm.pose.bones['hand.' + sd].matrix
        return M @ Vector((0.0, 0.07, -0.035))

    def fn(t):
        if t < t_clong:
            P = JUGGLE['period']
            u = ((t - t_juggle0) / P + i / 3.0) % 1.0
            a, b = (palm('R'), palm('L')) if u < 0.5 else (palm('L'), palm('R'))
            w = (u % 0.5) / 0.5
            p = a.lerp(b, w)
            p.z += JUGGLE['height'] * 4 * w * (1 - w)
            cache['p'] = p
            return Matrix.Translation(p)
        p0 = cache.get('p', Vector((0, 0, 1)))
        dt = t - t_clong
        # fall with a couple of bounces toward 'landing'
        T1 = 0.45 + 0.05 * i
        if dt < T1:
            u = dt / T1
            p = p0.lerp(Vector(landing[0]), u)
            p.z = p0.z * (1 - u) ** 2 + 0.032
        else:
            dt2 = dt - T1
            u = min(dt2 / 0.6, 1.0)
            p = Vector(landing[0]).lerp(Vector(landing[1]), perf.ease(u, 'out'))
            p.z = 0.032 + 0.10 * abs(math.sin(math.pi * 2 * u)) * (1 - u)
        return Matrix.Translation(p)
    return fn


def s2_1(F):
    T = F.begin('2.1', 'The act: juggling, CLONG')
    O, Ed, Te = F.A['oswald'], F.A['edith'], F.A['teddy']
    F.camera((1.55, -4.05, 2.55), (1.75, 2.6, 0.95), 30)
    crowd_place(F, T)
    Te.place(T, WIN_TEDDY[0], WIN_TEDDY[1], 0.0, z=SZ - 0.02)
    Te.posture(T, 'stand', dur=0.01, splay=6, lean=8, toes=0.3)
    Te.look_at(T, ('actor', 'oswald', 'head'), dur=0.01)
    Te.expr(T, smile=0.7, jaw=0.2, brow=0.4, dur=0.01)
    O.place(T, PITCH[0], PITCH[1], 0.0)
    O.posture(T, 'stand', dur=0.01, splay=24, knee=0.2)
    O.look_at(T, V(1.6, -3, 1.4), dur=0.01)
    O.expr(T, smile=0.55, press=0.45, smirk=0.6, brow=0.35, brow_asym=0.3, dur=0.01)
    # the cane hangs on his left forearm while he juggles
    F.attach('cane', T, T + 3.0, ('fn', cane_hang(F)))
    tj = T
    t_turn = T + 1.15
    t_clong = T + 2.62
    juggle_hands(F, tj, t_clong)
    O.turn(t_turn, 180.0, dur=0.35)
    w = O.walk(t_turn + 0.2, t_clong, [(PITCH[0], PITCH[1]), (LAMP[0] - 0.02, LAMP[1] - 0.17)], stride=0.34,
               splay=24, style='waddle', bob=0.022, sway=0.02, lift=0.045, backward=False)
    O.look_at(t_turn + 0.3, V(1.5, -2.4, 1.5), dur=0.3)     # glancing back over his shoulder
    O.look_at(t_turn + 0.9, V(LAMP[0], LAMP[1] + 2, 1.6), dur=0.2)
    O.look_at(t_turn + 1.2, V(1.2, -2.4, 1.5), dur=0.25)
    landings = [((2.15, 2.45, 0), (2.55, 2.35, 0)), ((2.3, 2.3, 0), (2.85, 2.15, 0)), ((2.05, 2.2, 0), (2.4, 1.95, 0))]
    for i in range(3):
        F.attach('ball%d' % i, T, T + 5.2, ('fn', ball_fn(F, i, tj, t_clong, landings[i])))
    F.set_visible(F.props['ball0'], T, True)
    for i in range(3):
        F.set_visible(F.props['ball%d' % i], T + 5.25, False)
    # CLONG: head snaps back, recoil
    F.sfx('clong', t_clong, gain=-2.0)
    O.pulses_head.add(t_clong, 0.45, lambda u: np.array([-18 * math.sin(math.pi * u), 0, 0]))
    O.expr(t_clong, smile=-0.2, press=0.0, smirk=0.0, jaw=0.25, brow=0.9, lid_L=1.25, lid_R=1.25, dur=0.06)
    for sd in 'LR':
        O.release(t_clong + 0.05, sd, dur=0.25)
    # staggers in a small circle propped on the cane, head wobbling, blinking fast
    cx, cy = LAMP[0] - 0.05, LAMP[1] - 0.55
    circ = [(cx + 0.28 * math.sin(a), cy + 0.28 * math.cos(a)) for a in np.linspace(0, 2 * math.pi, 9)]
    O.walk(t_clong + 0.3, t_clong + 1.8, [(LAMP[0] - 0.02, LAMP[1] - 0.17)] + circ[1:], stride=0.22, splay=20,
           style='waddle', bob=0.03, sway=0.03, lift=0.04)
    F.attach('cane', T + 3.0, T + 7.0, ('hand', 'oswald', 'R', CANE_GRIP))
    O.gesture(t_clong + 0.3, 'R', ('chest', (-0.32, -0.20, O.B.hipZ + 0.05), (0, -1, -0.3), (-1, 0, 0)), dur=0.3)
    O.fingers(t_clong + 0.3, 'R', 0.75, thumb=0.8, dur=0.2)
    for k in range(5):
        O.blink(t_clong + 0.45 + k * 0.22)
    O.pulses_head.add(t_clong + 0.3, 1.6, lambda u: np.array([4 * math.sin(6 * u), 10 * math.sin(9 * u), 9 * math.sin(7 * u)]) * (1 - u))
    O.expr(t_clong + 0.4, jaw=0.15, smile=0.1, brow=0.6, brow_asym=0.6, lid_L=0.8, lid_R=1.1, dur=0.2)
    O.look_at(t_clong + 0.3, V(LAMP[0] + 3, LAMP[1] + 4, 3), dur=0.4, weight=0.6)
    # recover, bow to the crowd scooping the balls into his pockets
    tb = t_clong + 1.9
    O.turn(tb - 0.1, 0.0, dur=0.3)
    O.look_at(tb, V(1.6, -2.5, 1.5), dur=0.3)
    O.expr(tb, smile=0.9, brow=0.5, brow_asym=0.0, lid_L=1.0, lid_R=1.0, jaw=0.0, press=0.3, dur=0.3)
    O.posture(tb + 0.2, 'stand', dur=0.5, splay=24, bow=38, knee=0.3)
    O.gesture(tb + 0.2, 'L', ('chest', (0.10, -0.42, O.B.hipZ - 0.25), (0, -0.3, -1), (0.3, 0.9, 0)), dur=0.4)
    O.gesture(tb + 0.75, 'L', ('chest', (0.22, -0.10, O.B.hipZ + 0.02), (0, 0, -1), (1, 0, 0)), dur=0.3)
    O.release(tb + 1.2, 'L', dur=0.4)
    O.posture(tb + 1.1, 'stand', dur=0.5, splay=24, knee=0.2)
    # laughter
    crowd_laugh(F, t_clong + 0.15, dur=2.6, big=True)
    F.sfx('crowd_laugh', t_clong + 0.15, gain=-6.0, intensity='big', duration=3.0)
    F.sfx('thump_soft', t_clong + 0.45, gain=-10.0, n=3)
    Te.bounce(t_clong + 0.2, dur=2.0, amt=0.012, n=6)
    Te.expr(t_clong + 0.2, smile=1.0, jaw=0.45, lid_L=0.7, lid_R=0.7, lidlo_L=0.8, lidlo_R=0.8, dur=0.2)
    F.sfx('child_giggle', t_clong + 0.35, gain=-10.0)
    # Edith: one startled blink, does not look up
    Ed.blink(t_clong + 0.05)
    Ed.pulses_head.add(t_clong + 0.02, 0.35, lambda u: np.array([-3 * math.sin(math.pi * u), 0, 0]))
    F.cue('rag', T - 0.25, 7.3, gain=-5.0, tempo=112)
    F.end(T + 6.0)


def s2_2(F):
    T = F.begin('2.2', 'Banana peel, not today')
    O = F.A['oswald']
    peel = (0.95, 1.25)
    F.peels[0].location = (peel[0], peel[1], 0.0)
    F.peels[0].rotation_euler = (0, 0, 0.6)
    start = (1.75, 1.62)
    stop = (1.16, 1.40)
    face = V(stop[0] - 0.05, stop[1] - 0.02, 1.62)
    F.camera((0.62, 0.62, 0.13), (peel[0], peel[1], 0.03), 26,
             keys=[(T + 0.55, (0.62, 0.62, 0.13), (peel[0], peel[1], 0.03)),
                   (T + 1.35, (0.66, 0.60, 0.16), face)])
    O.place(T, start[0], start[1], 110.0)
    O.posture(T, 'stand', dur=0.01, splay=26, knee=0.25)
    O.walk(T, T + 0.62, [start, stop], stride=0.36, splay=26, style='waddle', bob=0.03, sway=0.02)
    O.look_at(T, V(peel[0], peel[1], 0.0), dur=0.01)
    # brows shoot up, mouth makes an O
    O.expr(T + 0.62, brow=1.0, round=0.9, jaw=0.25, lid_L=1.25, lid_R=1.25, dur=0.12)
    # points at it, wags a finger at the audience, lips pursed smugly
    O.gesture(T + 1.0, 'R', ('chest', (-0.25, -0.40, O.B.hipZ + 0.15), (0.3, -0.6, -0.8), (-0.9, 0, 0.3)), dur=0.3)
    O.fingers(T + 1.0, 'R', 0.9, thumb=0.8, per={'index': 0.0, 'middle': 0.95, 'ring': 0.95, 'pinky': 0.95}, dur=0.2)
    O.look_at(T + 1.4, V(0.6, 0.3, 0.6), dur=0.25)
    for k in range(3):
        tt = T + 1.55 + k * 0.18
        O.gesture(tt, 'R', ('chest', (-0.22 + (0.05 if k % 2 else -0.05), -0.42, O.B.hipZ + 0.42), (0, -0.2, 1), (-1, 0, 0)), dur=0.12)
    O.expr(T + 1.5, round=0.0, jaw=0.0, pout=0.6, press=0.4, smile=0.35, smirk=0.5, brow=0.6, brow_asym=0.4, lid_L=0.85, lid_R=0.85, dur=0.25)
    O.release(T + 2.2, 'R', dur=0.3)
    O.fingers(T + 2.2, 'R', 0.4, dur=0.3)
    # waddles around it in an exaggerated slow arc
    arc = [stop, (1.22, 1.05), (0.98, 0.82), (0.66, 0.92), (0.58, 1.18)]
    O.walk(T + 2.3, T + 3.5 + 1.2, arc, stride=0.24, splay=30, style='waddle', bob=0.035, sway=0.03, lift=0.09)
    O.look_at(T + 2.3, V(peel[0], peel[1], 0.0), dur=0.3)
    F.cue('tiptoe', T + 0.4, 3.2, gain=-6.0)
    F.end(T + 3.5)


def s2_3(F):
    T = F.begin('2.3', 'The lean, the second peel, the fall')
    O = F.A['oswald']
    F.camera((1.15, -2.25, 1.5), (1.38, 1.55, 0.72), 33)
    pos = (1.42, 2.02)
    peel2 = (1.42, 1.74)
    F.peels[1].location = (peel2[0], peel2[1], 0.0)
    F.peels[1].rotation_euler = (0, 0, -0.4)
    O.place(T, pos[0], pos[1], 0.0)
    O.posture(T, 'stand', dur=0.01, splay=24, knee=0.2)
    O.look_at(T, V(1.3, -2.4, 1.5), dur=0.01)
    O.expr(T, smile=0.85, brow=0.55, lid_L=1.05, lid_R=1.05, dur=0.01)
    # arms wide for applause
    for sd, sx in (('L', 1), ('R', -1)):
        O.gesture(T + 0.15, sd, ('chest', (sx * 0.62, -0.10, O.B.hipZ + 0.52), (sx, -0.1, 0.25), (0, 0.4, 1)), dur=0.35)
        O.fingers(T + 0.15, sd, 0.1, spread=0.6, thumb=0.0, dur=0.3)
    # THE LEAN: shoulders dip forward, up onto his toes, held 16 frames
    tl = T + 0.55
    O.posture(tl, 'stand', dur=0.22, splay=24, lean=16, toes=0.8)
    O.expr(tl, smile=1.0, brow=0.8, dur=0.2)
    t_step = tl + 0.22 + 16 / 24.0
    # the next step lands on the peel: feet up, backside down
    O.walk(t_step, t_step + 0.22, [pos, (pos[0], pos[1] - 0.20)], stride=0.3, splay=20, first='R')
    O.posture(t_step + 0.12, 'fall_air', dur=0.18, e='out')
    O.posture(t_step + 0.38, 'sit_ground', dur=0.16, e='in')
    O.place(t_step + 0.2, pos[0], pos[1] - 0.48, 0.0, dur=0.3)
    O.expr(t_step + 0.12, brow=1.1, jaw=0.5, round=0.6, smile=0.0, lid_L=1.3, lid_R=1.3, dur=0.08)
    for sd in 'LR':
        O.release(t_step + 0.1, sd, dur=0.12)
    t_land = t_step + 0.54
    O.bounce(t_land, dur=0.4, amt=0.02, n=1)
    F.sfx('slide_whistle_down', t_step - 0.05, gain=-6.0)
    F.sfx('thump_fall', t_land, gain=-3.0)
    # one beat. looks at the hat, at the crowd, gestures to it grandly
    O.expr(t_land + 0.1, jaw=0.0, round=0.0, brow=0.3, lid_L=1.0, lid_R=1.0, dur=0.3)
    hat_pt = V(PITCH[0] + 0.02, PITCH[1] - 0.42, 0.08)
    O.look_at(t_land + 0.6, hat_pt, dur=0.35)
    O.look_at(t_land + 1.15, V(1.3, -2.4, 1.4), dur=0.3)
    O.expr(t_land + 1.15, smile=0.8, brow=0.6, brow_asym=0.3, dur=0.3)
    O.gesture(t_land + 1.5, 'R', ('world', (hat_pt.x - 0.18, hat_pt.y + 0.05, 0.42), (-0.4, -1, 0.1), (0, 0, -1)), dur=0.45)
    O.fingers(t_land + 1.5, 'R', 0.05, spread=0.4, thumb=0.0, dur=0.3)
    O.head(t_land + 1.5, pitch=8, yaw=0, roll=-6, dur=0.4)
    F.sfx('woodblock', t_land + 1.6, gain=-6.0)
    F.sfx('crowd_laugh', t_land + 1.7, gain=-5.0, intensity='big', duration=2.6)
    F.attach('cane', T, T + 6.0, ('fn', lambda t: world_m((pos[0] - 0.55, pos[1] - 0.25, 0.012), (0, 90, 70))))
    F.cue('rag', t_land + 1.6, 4.5, gain=-6.0, tempo=112)
    F.end(T + max(4.5, t_land + 2.8 - T))


def s2_4(F):
    T = F.begin('2.4', 'Coins, greed beat, never looks at the wall')
    O, Ed = F.A['oswald'], F.A['edith']
    F.camera((1.0, -0.75, 1.85), (1.75, 1.95, 0.45), 26)
    sit = O.root_at(T)
    hat_pt = V(PITCH[0] + 0.02, PITCH[1] - 0.42, 0.08)
    F.set_visible(F.snowline[0], T, True)
    F.set_visible(F.snowline[1], T, True)
    # coins: three tosses from off-frame into the bowler; he beams at each with a bow of the head
    srcs = [V(0.2, -2.0, 1.3), V(1.6, -2.3, 1.3), V(2.7, -2.0, 1.3)]
    for i in range(3):
        tc = T + 0.3 + 0.62 * i
        def fn(t, i=i, tc=tc):
            u = perf.clamp((t - tc) / 0.55, 0, 1)
            p = srcs[i].lerp(hat_pt + V(0, 0, 0.03), u)
            p.z += 0.6 * math.sin(math.pi * u)
            return Matrix.Translation(p) @ Euler((u * 12, u * 7, 0)).to_matrix().to_4x4()
        F.attach('coin%d' % i, T, T + 3.0, ('fn', fn))
        F.set_visible(F.props['coin%d' % i], tc, True)
        F.set_visible(F.props['coin%d' % i], T + 3.0, False)
        F.sfx('coin_plink', tc + 0.55, gain=-10.0)
        O.look_at(tc - 0.1, srcs[i] + V(0, 0, 0.3), dur=0.25)
        O.nod(tc + 0.5, amt=9, dur=0.45)
        O.expr(tc, smile=1.0, brow=0.5, lidlo_L=0.5, lidlo_R=0.5, dur=0.2)
    # door crack: Teddy shouts, Tomas pulls it shut (heard)
    F.door(T + 1.85, 16, 0.2)
    a, b = F.say('K01', T + 2.0)
    a2, b2 = F.say('T02', T + 2.62)
    F.door(b2 + 0.05, 0, 0.2)
    F.sfx('door_thunk', b2 + 0.28, gain=-8.0)
    # greed beat
    tg = T + 3.0
    for sd, sx in (('L', 1), ('R', -1)):
        pass
    O.gesture(tg, 'L', ('chest', (0.10, -0.38, O.B.hipZ - 0.05), (-0.4, -1, 0), (0, 0, -1)), dur=0.3)
    O.fingers(tg, 'L', 0.25, thumb=0.1, dur=0.2)
    O.look_at(tg, ('actor', 'oswald', 'hand_L', (0, 0, 0)), dur=0.3)
    O.expr(tg + 0.3, smile=0.9, smirk=0.7, brow=0.4, brow_asym=0.5, lid_L=0.75, lid_R=0.75, dur=0.3)
    for k in range(4):
        O.nod(tg + 0.4 + k * 0.22, amt=5, dur=0.2)
    O.gesture(tg + 0.4, 'R', ('chest', (-0.02, -0.38, O.B.hipZ - 0.02), (0.6, -0.6, -0.4), (0, 0.2, 1)), dur=0.2)
    O.fingers(tg + 0.4, 'R', 0.85, per={'index': 0.0, 'middle': 0.9, 'ring': 0.9, 'pinky': 0.9}, thumb=0.7, dur=0.2)
    # rub hands together
    for k in range(4):
        tt = tg + 1.3 + k * 0.15
        for sd, sx in (('L', 1), ('R', -1)):
            O.gesture(tt, sd, ('chest', (sx * (0.03 + 0.015 * (k % 2)), -0.36, O.B.hipZ + 0.06 + 0.02 * (k % 2)), (-sx * 0.8, -0.5, 0.3), (0, -0.3, 1) if sd == 'L' else (0, -0.3, 1)), dur=0.12)
        O.fingers(tt, 'L', 0.2, dur=0.1)
        O.fingers(tt, 'R', 0.2, dur=0.1)
    # claps the bowler back on
    tp = tg + 2.0
    O.gesture(tp, 'R', ('world', (hat_pt.x - 0.05, hat_pt.y + 0.02, hat_pt.z + 0.12), (0, -0.2, -1), (-1, 0, 0)), dur=0.3)
    O.look_at(tp - 0.05, hat_pt, dur=0.25)
    F.hat_plan.append((tp + 0.3, tp + 0.55, 'lift', ('hand', 'oswald', 'R', hand_hold(0.0, 0.08, -0.11, 0, 0, 0))))
    F.hat_plan.append((tp + 0.55, tp + 0.95, 'to_head', None))
    F.hat_plan.append((tp + 0.95, 1e9, 'head', None))
    hp = F.C['oswald'].H.p
    brim_top = F.C['oswald'].hp((0.0, -hp['ry'] * 0.2, 0.17))
    O.gesture(tp + 0.5, 'R', ('head', brim_top, (0, 0.3, 1), (-1, 0, 0)), dur=0.4)
    O.release(tp + 1.0, 'R', dur=0.35)
    O.release(tp + 0.6, 'L', dur=0.4)
    O.pulses_head.add(tp + 0.9, 0.25, lambda u: np.array([5 * math.sin(math.pi * u), 0, 0]))
    F.sfx('cloth_rustle', tp + 0.9, gain=-14.0)
    # looks straight past the lamp to the loaves in the window, lips smacking
    O.look_at(tp + 1.15, V(1.2, FY + 0.5, SZ + 1.0), dur=0.35)
    O.expr(tp + 1.15, smile=0.5, smirk=0.0, brow=0.6, brow_asym=0.0, lid_L=1.1, lid_R=1.1, dur=0.3)
    for k in range(3):
        tt = tp + 1.5 + k * 0.28
        O.expr(tt, press=0.8, pout=0.3, dur=0.1)
        O.expr(tt + 0.13, press=0.0, pout=0.0, jaw=0.15, dur=0.1)
        O.expr(tt + 0.24, jaw=0.0, dur=0.05)
    a3, b3 = F.say('N11', T + 4.0)
    # Edith: still has not looked up
    Ed.expr(T, gaze_pitch=-18, lid_L=0.82, lid_R=0.82, dur=0.01)
    F.cue('vamp', T + 4.6, 9.0, gain=-8.0)
    F.end(max(T + 6.5, b3 + 0.3))


# ====================================================================== SCENE 3
LOAF_PALM = Matrix(((0, 1, 0, 0.0), (1, 0, 0, 0.075), (0, 0, -1, -0.052), (0, 0, 0, 1)))
LOAF_BITE = Matrix(((0, 0, 1, 0.0), (1, 0, 0, 0.08), (0, 1, 0, -0.03), (0, 0, 0, 1)))
# camera setups around Edith (world space); heads are queried live for targets
ED_FACE = V(EDITH[0] - 0.02, EDITH[1] - 0.08, SZ + 0.70)
OS_FACE = V(KNEEL[0] + 0.02, KNEEL[1] + 0.02, SZ + 0.92)
SETUP = {
    'A': dict(loc=(4.15, 1.95, SZ + 0.80), target=(2.72, 3.48, SZ + 0.62), lens=32),
    'B': dict(loc=(3.27, 3.93, SZ + 0.84), target=('actor', 'oswald', 'eyes', (0.0, 0.0, -0.10)), lens=36),
    'C': dict(loc=(2.13, 2.56, SZ + 1.02), target=('actor', 'edith', 'eyes', (0.0, 0.0, -0.05)), lens=55),
    'D': dict(loc=(2.66, 2.66, SZ + 0.80), target=('actor', 'edith', 'eyes', (0.0, 0.0, -0.06)), lens=78),
    'E': dict(loc=(3.55, 3.42, SZ + 0.95), target=('actor', 'oswald', 'eyes', (0.0, 0.0, -0.06)), lens=72),
}


def cam_setup(F, key, **kw):
    s = dict(SETUP[key])
    s.update(kw)
    focus = s.pop('focus', None)
    fstop = s.pop('fstop', None)
    if key in ('C', 'D') and focus is None:
        focus, fstop = ('actor', 'edith', 'eyes'), fstop or 2.2
    if key in ('B', 'E') and focus is None:
        focus, fstop = ('actor', 'oswald', 'eyes'), fstop or 2.4
    return F.camera(s.pop('loc'), s.pop('target'), s.pop('lens'), focus=focus, fstop=fstop, **s)


def edith_lap_loaf(F):
    Ed = F.C['edith']
    M = Ed.arm.matrix_world @ Ed.arm.pose.bones['hips'].matrix
    return M @ Matrix.Translation((0.0, 0.10, -0.24)) @ Euler((math.radians(90), 0, math.radians(90))).to_matrix().to_4x4()


def s3_1(F):
    T = F.begin('3.1', 'Doorway deep staging: the question')
    O, Te, To, Ed = F.A['oswald'], F.A['teddy'], F.A['tomas'], F.A['edith']
    F.camera((2.35, 2.80, SZ + 1.30), (DOOR_X + 0.15, FY - 0.38, SZ + 1.10), 50,
             focus=('actor', 'oswald', 'head'), fstop=3.5)
    for n in ('plum', 'flatcap', 'paper'):
        far_away(F, n, T)
    # Oswald backs out of the door with the rye, cane hooked over his arm
    O.place(T, DOOR_X, FY + 0.45, 180.0, z=SZ)
    O.posture(T, 'stand', dur=0.01, splay=26, knee=0.2)
    F.door(T + 0.0, 70, 0.3)
    F.sfx('shop_bell', T + 0.12, gain=-7.0)
    O.walk(T + 0.2, T + 1.05, [(DOOR_X, FY + 0.45), (DOOR_X + 0.05, FY - 0.35)], stride=0.3, splay=24,
           style='waddle', backward=True, bob=0.02)
    O.turn(T + 1.05, 92.0, dur=0.35)
    path1 = [(DOOR_X + 0.05, FY - 0.35), (-0.35, FY - 0.70), (0.0, FY - 0.98)]
    O.walk(T + 1.4, T + 4.4, path1, stride=0.30, splay=26, style='waddle', bob=0.026, sway=0.022, lift=0.045)
    O.walk(T + 4.45, T + 5.65, [(0.0, FY - 0.98), (0.25, FY - 1.06)], stride=0.26, splay=24, style='waddle',
           bob=0.018, sway=0.014, lift=0.035)
    F.attach('cane', T, T + 14.0, ('fn', cane_hang(F)))
    O.look_at(T + 1.4, V(3.0, FY - 0.9, SZ + 1.2), dur=0.4)
    O.expr(T, smile=0.6, brow=0.4, dur=0.01)
    # loaf: in both hands, peeling the paper back, raising it for a big greedy bite
    O.gesture(T, 'L', ('chest', (0.06, -0.34, O.B.hipZ + 0.20), (-0.5, -0.8, 0.2), (0, 0.3, -1)), dur=0.01)
    O.gesture(T, 'R', ('chest', (-0.08, -0.33, O.B.hipZ + 0.22), (0.5, -0.8, 0.2), (0, 0.3, -1)), dur=0.01)
    for sd in 'LR':
        O.fingers(T, sd, 0.5, thumb=0.4, dur=0.01)
    F.attach('rye', T, T + 3.9, ('hand', 'oswald', 'L', LOAF_PALM))
    for k in range(3):
        tt = T + 1.8 + k * 0.5
        O.gesture(tt, 'R', ('chest', (-0.02, -0.40, O.B.hipZ + 0.26), (0.6, -0.5, 0.3), (0, 0.4, -1)), dur=0.2)
        O.gesture(tt + 0.25, 'R', ('chest', (-0.10, -0.33, O.B.hipZ + 0.20), (0.5, -0.8, 0.2), (0, 0.3, -1)), dur=0.2)
        F.sfx('paper_rustle', tt, gain=-16.0)
    tb = T + 3.9
    mouth = F.C['oswald'].hp(F.C['oswald'].hg['mouth_c'] + np.array([0.0, -0.12, -0.01]))
    O.gesture(tb - 0.4, 'L', ('head', mouth + Vector((0.06, 0.0, -0.03)), (-0.6, -0.3, 0.6), (0.6, 0.6, 0.2)), dur=0.45)
    O.gesture(tb - 0.4, 'R', ('head', mouth + Vector((-0.06, 0.0, -0.05)), (0.6, -0.3, 0.6), (-0.6, 0.6, 0.2)), dur=0.45)
    F.attach('rye', tb, T + 30, ('hand', 'oswald', 'L', LOAF_BITE))
    O.expr(tb - 0.5, smile=0.7, brow=0.7, lid_L=1.15, lid_R=1.15, dur=0.3)
    a, b = F.say('K02', T + 1.8)
    a2, b2 = F.say('T03', b + 0.33)
    # the waddle slows half a step on "Walter's wife"
    a3, b3 = F.say('K03', b2 + 0.22)
    O.expr(a3 - 0.4, jaw=0.62, round=0.15, smile=0.4, brow=0.8, lid_L=1.2, lid_R=1.2, dur=0.3)
    t_freeze = a3 + 0.5
    O.expr(t_freeze, jaw=0.32, smile=0.0, round=0.0, brow=0.25, lid_L=1.0, lid_R=1.0, dur=0.12)
    O.expr(t_freeze, gaze_yaw=-28, dur=0.25)
    O.look_at(t_freeze, V(3.0, FY - 0.9, SZ + 1.2), dur=0.01, weight=1.0)
    O.hold_eyes(t_freeze, t_freeze + 4.0)
    # Teddy pops into the doorway behind him; Tomas comes up behind, wiping his hands
    Te.place(T, DOOR_X + 0.05, FY + 0.9, 0.0, z=SZ - 0.02)
    Te.posture(T, 'stand', dur=0.01, splay=8)
    Te.walk(T + 1.0, T + 1.6, [(DOOR_X + 0.05, FY + 0.9), (DOOR_X + 0.10, FY - 0.02)], stride=0.28, z=SZ)
    Te.look_at(T + 1.2, ('actor', 'oswald', 'head'), dur=0.3)
    Te.tilt(T + 1.9, amt=10, dur=0.5)
    Te.expr(T + 1.6, brow=0.3, jaw=0.1, dur=0.3)
    Te.look_at(a + 0.1, ('actor', 'tomas', 'head'), dur=0.3)
    Te.look_at(b2 + 0.1, ('actor', 'tomas', 'head'), dur=0.2)
    To.place(T, DOOR_X - 0.25, FY + 1.2, 0.0, z=SZ - 0.02)
    To.posture(T, 'stand', dur=0.01, splay=10)
    To.walk(T + 1.6, T + 2.5, [(DOOR_X - 0.25, FY + 1.2), (DOOR_X - 0.18, FY + 0.30)], stride=0.45, z=SZ - 0.01)
    To.look_at(T + 1.6, ('actor', 'oswald', 'head'), dur=0.4)
    To.expr(T, lid_L=0.65, lid_R=0.65, press=0.3, dur=0.01)
    for k in range(6):
        tt = T + 1.7 + k * 0.4
        for sd, sx in (('L', 1), ('R', -1)):
            To.gesture(tt, sd, ('chest', (sx * (0.05 + 0.03 * (k % 2)), -0.33, To.B.hipZ + 0.18 + 0.02 * ((k + (sd == 'L')) % 2)), (-sx * 0.7, -0.6, 0.2), (0, 0.2, 1)), dur=0.18)
    F.cue_stop = None
    F.end(b3 + 0.3)


def s3_2(F):
    T = F.begin('3.2', "Tomas: It's...")
    To = F.A['tomas']
    F.camera((0.30, FY - 1.05, SZ + 1.48), ('actor', 'tomas', 'eyes', (0, 0, -0.08)), 62,
             focus=('actor', 'tomas', 'eyes'), fstop=2.4)
    a, b = F.say('T04', T + 0.3)
    F.music_stop = a + 0.1
    for sd in 'LR':
        To.release(b + 0.15, sd, dur=0.5)
    To.look_at(b + 0.35, ('actor', 'edith', 'head'), dur=0.5)
    To.expr(b + 0.5, lid_L=1.05, lid_R=1.05, brow=0.35, brow_in=0.85, press=0.1, smile=-0.1, dur=0.5)
    To.expr(b + 1.05, blink=1.0, dur=0.22)
    To.expr(b + 1.32, blink=0.0, dur=0.35)
    To.hold_eyes(T, T + 2.6)
    F.sfx('tower_ticks', a + 0.2, gain=-14.0, duration=140.0)
    F.end(T + 2.5)


def s3_3(F):
    T = F.begin('3.3', 'Edith heard')
    Ed = F.A['edith']
    F.camera((2.58, 2.70, SZ + 1.45), ('actor', 'edith', 'eyes', (0, 0, -0.06)), 70,
             focus=('actor', 'edith', 'eyes'), fstop=2.6)
    Ed.hold_eyes(T, T + 2.1)
    Ed.expr(T + 0.2, lid_L=0.88, lid_R=0.88, brow_in=0.35, dur=0.6)
    Ed.expr(T + 0.85, blink=1.0, dur=0.3)
    Ed.expr(T + 1.2, blink=0.0, dur=0.45)
    F.end(T + 2.0)


def s3_4(F):
    T = F.begin('3.4', 'Door, Teddy. The bite never happens.')
    O, Te, To = F.A['oswald'], F.A['teddy'], F.A['tomas']
    F.camera((2.35, 2.80, SZ + 1.30), (DOOR_X + 0.15, FY - 0.38, SZ + 1.10), 50,
             focus=('actor', 'oswald', 'head'), fstop=3.5)
    To.look_at(T + 0.2, V(DOOR_X, FY + 1.5, SZ + 1.0), dur=0.5)
    To.expr(T + 0.2, lid_L=0.6, lid_R=0.6, brow_in=0.3, brow=-0.1, smile=-0.25, dur=0.4)
    To.gesture(T + 0.3, 'R', ('world', (DOOR_X + 0.15, FY - 0.02, SZ + 0.85), (0.3, -0.2, -1), (0, 0, 1)), dur=0.35)
    To.fingers(T + 0.3, 'R', 0.4, dur=0.3)
    To.turn(T + 0.7, 160.0, dur=0.6)
    a, b = F.say('T05', T + 0.8)
    To.walk(T + 1.3, T + 2.2, [(DOOR_X - 0.18, FY + 0.30), (DOOR_X - 0.15, FY + 1.1)], stride=0.45, z=SZ - 0.01)
    Te.turn(T + 0.9, 170.0, dur=0.4)
    Te.walk(T + 1.25, T + 2.0, [(DOOR_X + 0.10, FY - 0.02), (DOOR_X + 0.05, FY + 0.85)], stride=0.28, z=SZ)
    F.door(T + 1.75, 0, 0.55)
    F.sfx('shop_bell', T + 2.3, gain=-16.0)
    F.sfx('door_thunk', T + 2.32, gain=-12.0)
    pool_light(F, T + 2.3, 55, 1.6, 0.4)
    # Oswald, frozen with the crust in his teeth, lowers the loaf unbitten and folds the paper back
    O.expr(T + 0.9, jaw=0.05, dur=0.6)
    O.gesture(T + 0.9, 'L', ('chest', (0.06, -0.33, O.B.hipZ + 0.18), (-0.5, -0.8, 0.2), (0, 0.3, -1)), dur=1.2)
    O.gesture(T + 0.9, 'R', ('chest', (-0.08, -0.33, O.B.hipZ + 0.20), (0.5, -0.8, 0.2), (0, 0.3, -1)), dur=1.2)
    F.attach('rye', T + 1.1, T + 40, ('hand', 'oswald', 'L', LOAF_PALM))
    O.gesture(T + 2.2, 'R', ('chest', (0.02, -0.38, O.B.hipZ + 0.24), (0.6, -0.5, 0.3), (0, 0.4, -1)), dur=0.3)
    O.gesture(T + 2.6, 'R', ('chest', (-0.08, -0.33, O.B.hipZ + 0.20), (0.5, -0.8, 0.2), (0, 0.3, -1)), dur=0.3)
    F.sfx('paper_rustle', T + 2.3, gain=-16.0)
    O.expr(T + 1.0, gaze_yaw=-10, brow_in=0.4, brow=-0.1, dur=0.8)
    O.look_at(T + 1.4, V(1.6, FY - 0.8, SZ + 0.6), dur=0.8)
    F.end(T + 3.0)


def s3_5(F):
    T = F.begin('3.5', 'The body changes: a man, not a clown')
    O = F.A['oswald']
    F.camera((1.75, 0.25, 1.58), (1.95, 3.40, 0.85), 24)
    O.look_at(T, ('actor', 'edith', 'head'), dur=0.8, weight=0.7)
    O.expr(T, gaze_yaw=0, smile=-0.1, brow_in=0.45, dur=0.6)
    t1 = T + 0.7
    O.posture(t1, 'stand', dur=1.1, splay=4, knee=0.0, stoop=0)
    O.shoulders(t1 + 0.2, -9, dur=0.8)
    # cane under his arm, the loaf into both hands
    F.attach('cane', t1 + 0.4, T + 40, ('bone', 'oswald', 'upperarm.R', hand_hold(0.0, 0.10, 0.06, 0, 0, 90)))
    O.gesture(t1 + 0.3, 'R', ('chest', (-0.07, -0.30, O.B.hipZ + 0.10), (0.4, -0.7, 0.3), (0, 0.4, -1)), dur=0.6)
    O.gesture(t1 + 0.3, 'L', ('chest', (0.08, -0.30, O.B.hipZ + 0.10), (-0.4, -0.7, 0.3), (0, 0.4, -1)), dur=0.6)
    O.walk(T + 1.9, T + 4.0, [(0.25, FY - 1.06), (1.15, FY - 0.98), (2.05, FY - 0.92)], stride=0.55, splay=4,
           style='walk', bob=0.012, sway=0.008, lift=0.06, arm=0.0)
    F.sfx('footsteps_cobble', T + 1.95, gain=-14.0, n=5, interval=0.48)
    F.end(T + 4.0)


def s3_6(F):
    T = F.begin('3.6', 'Down to her level (camera at 0.8 m)')
    O, Ed = F.A['oswald'], F.A['edith']
    cam_setup(F, 'A', focus=V(2.70, 3.50, SZ + 0.65), fstop=4.0)
    O.breath_pulse(T + 0.15, dur=1.0, amt=2.2)
    O.shoulders(T + 0.15, 6, dur=0.45)
    O.shoulders(T + 0.65, -9, dur=0.5)
    F.sfx('breath_exhale', T + 0.6, gain=-12.0)
    # lays the cane on the pavement
    O.gesture(T + 0.95, 'R', ('chest', (-0.22, -0.20, O.B.hipZ - 0.30), (0, -0.3, -1), (-1, 0, 0)), dur=0.35)
    cane_ground = world_m((2.02, FY - 1.10, SZ + 0.012), (0, 90, 15))
    F.attach('cane', T + 1.3, T + 60, ('world', cane_ground))
    F.sfx('cane_click', T + 1.3, gain=-12.0)
    O.posture(T + 1.35, 'kneel', dur=0.95, down='R', lean=8)
    F.sfx('knee_stone', T + 2.15, gain=-10.0)
    # shuffles in on the knee to the diagonal, ~0.6 m from her
    O.place(T + 2.35, KNEEL[0], KNEEL[1], KNEEL_H, z=SZ, dur=0.65)
    O.look_at(T + 1.4, ('actor', 'edith', 'head'), dur=0.5)
    O.expr(T + 1.4, brow_in=0.5, brow=0.1, smile=0.0, lid_L=0.95, lid_R=0.95, dur=0.5)
    # holds the wrapped loaf out on a flat, open palm
    O.release(T + 1.6, 'L', dur=0.4)
    O.fingers(T + 1.6, 'L', 0.35, dur=0.3)
    offer = lambda t: ('world', tuple(V(EDITH[0], EDITH[1], 0) + V(-0.32, -0.35, SZ + 0.42)), (0.65, 0.72, 0.1), (0, 0, -1))
    O.gesture(T + 2.75, 'R', offer, dur=0.6)
    O.fingers(T + 2.75, 'R', 0.08, spread=0.25, thumb=0.05, dur=0.4)
    F.attach('rye', T + 1.6, T + 40, ('hand', 'oswald', 'R', LOAF_PALM))
    F.sfx('oven_hum', T, gain=-26.0, duration=125.0)
    F.end(T + 3.5)


def osw_rest(F, t, dur=0.6, sides='LR'):
    O = F.A['oswald']
    knee = lambda t_: ('world', tuple(F.C['oswald'].arm.matrix_world.to_translation()) if False else None)
    for sd in sides:
        if sd == 'L':
            spec = ('hips', (0.13, -0.30, O.B.hipZ + 0.06), (0.1, -0.7, -0.7), (0.4, 0.3, 0.85))
        else:
            spec = ('hips', (0.02, -0.33, O.B.hipZ + 0.04), (0.6, -0.6, -0.5), (-0.2, 0.3, 0.9))
        O.gesture(t, sd, spec, dur=dur)
        O.fingers(t, sd, 0.4, thumb=0.3, dur=dur)


def s3_7(F):
    T = F.begin('3.7', 'Her eyes lift; the social mask')
    O, Ed = F.A['oswald'], F.A['edith']
    cam_setup(F, 'C')
    Ed.look_at(T + 0.25, ('actor', 'oswald', 'hand_R'), dur=0.7)
    Ed.head(T + 0.25, pitch=6, dur=0.7)
    Ed.expr(T + 0.25, gaze_pitch=0, lid_L=0.95, lid_R=0.95, dur=0.6)
    Ed.look_at(T + 1.1, ('actor', 'oswald', 'eyes'), dur=0.5)
    Ed.head(T + 1.1, pitch=-2, dur=0.6)
    Ed.expr(T + 1.2, lid_L=1.12, lid_R=1.12, brow=0.2, brow_in=0.2, dur=0.35)
    # the social mask snaps on
    tm = T + 1.65
    Ed.head(tm, pitch=6, dur=0.2)
    Ed.expr(tm, smile=0.38, press=0.35, brow=0.5, brow_in=0.35, lid_L=0.95, lid_R=0.95, lidlo_L=0.3, lidlo_R=0.3, dur=0.2)
    a, b = F.say('E01', T + 1.9)
    Ed.nod(a + 0.2, amt=4, dur=0.5)
    # pats the brick behind her as evidence
    tp = a + 1.75
    wall = lambda t: ('world', (EDITH[0] + 0.24, FY - 0.02, SZ + 0.36), (0.1, 0.4, 1.0), (0, 1, 0))
    Ed.gesture(tp, 'L', wall, dur=0.35)
    Ed.fingers(tp, 'L', 0.15, dur=0.3)
    for k in range(2):
        Ed.gesture(tp + 0.4 + k * 0.28, 'L', ('world', (EDITH[0] + 0.24, FY - 0.06, SZ + 0.38), (0.1, 0.4, 1.0), (0, 1, 0)), dur=0.1)
        Ed.gesture(tp + 0.52 + k * 0.28, 'L', wall, dur=0.1)
    Ed.release(b - 0.2, 'L', dur=0.5)
    Ed.look_at(b + 0.15, ('actor', 'oswald', 'hand_R'), dur=0.4)
    F.end(b + 0.4)


def s3_8(F):
    T = F.begin('3.8', 'It\'s the small rye.  (his first words)')
    O, Ed = F.A['oswald'], F.A['edith']
    cam_setup(F, 'C')
    # folds back a corner of the paper
    O.gesture(T + 0.3, 'L', ('world', tuple(V(EDITH[0], EDITH[1], 0) + V(-0.36, -0.39, SZ + 0.48)), (0.6, 0.6, 0.0), (0, 0.4, 1)), dur=0.4)
    O.fingers(T + 0.3, 'L', 0.55, thumb=0.6, dur=0.3)
    F.sfx('paper_rustle', T + 0.55, gain=-16.0)
    O.release(T + 1.0, 'L', dur=0.5)
    O.expr(T + 0.8, brow_in=0.35, brow=0.15, smile=0.05, dur=0.4)
    a, b = F.say('O01', T + 1.0, gain=-2.0)
    # her eyes drop to the loaf; grief brow; lips part
    Ed.look_at(b + 0.05, ('actor', 'oswald', 'hand_R'), dur=0.45)
    Ed.expr(b + 0.05, smile=0.0, press=0.0, brow_in=0.95, brow=-0.15, jaw=0.08, lid_L=0.85, lid_R=0.85, lidlo_L=0.0, lidlo_R=0.0, dur=0.5)
    Ed.hold_eyes(b, b + 1.2)
    a2, b2 = F.say('E02', b + 1.1)
    a3, b3 = F.say('O02', b2 + 0.65, gain=-2.0)
    O.expr(a3, smile=0.3, brow=0.35, brow_in=0.2, gaze_pitch=-4, dur=0.5)
    O.look_at(a3 + 0.1, V(1.3, 2.4, 0.6), dur=0.5, weight=0.5)
    O.look_at(a3 + 1.4, ('actor', 'edith', 'eyes'), dur=0.4)
    Ed.look_at(a3 + 0.4, ('actor', 'oswald', 'eyes'), dur=0.5)
    Ed.expr(a3 + 0.4, lid_L=1.05, lid_R=1.05, brow_in=0.6, brow=0.2, jaw=0.0, dur=0.4)
    Ed.shake(a3 + 1.3, amt=4, dur=0.8, n=2)
    Ed.expr(a3 + 1.3, smile=0.15, dur=0.6)
    # "before he'd paid": he tilts his head toward the card; her eyes follow
    tc = b3 - 0.9
    O.head(tc, pitch=0, yaw=18, roll=8, dur=0.35)
    O.head(tc + 0.9, pitch=0, yaw=0, roll=0, dur=0.5)
    Ed.look_at(tc + 0.25, V(*CARD), dur=0.35)
    F.sfx('nasal_laugh', b3 + 0.15, gain=-10.0)
    Ed.expr(b3 + 0.12, smile=0.4, smirk=0.6, brow_in=0.3, lidlo_L=0.4, lidlo_R=0.4, dur=0.3)
    Ed.look_at(b3 + 0.45, ('actor', 'oswald', 'eyes'), dur=0.35)
    a4, b4 = F.say('E03', b3 + 0.5)
    O.expr(a4 + 0.3, smile=0.45, brow=0.3, dur=0.4)
    # she takes the loaf in both hands and holds it in her lap like something warm
    tt = a4 + 0.5
    for sd, sx in (('L', 1), ('R', -1)):
        Ed.gesture(tt, sd, ('world', tuple(V(EDITH[0], EDITH[1], 0) + V(-0.30 + sx * 0.09, -0.33, SZ + 0.44)), (-sx * 0.6, 0.3, -0.5), (sx * 0.5, 0, 0.8)), dur=0.5)
        Ed.fingers(tt, sd, 0.5, thumb=0.4, dur=0.4)
    F.attach('rye', tt + 0.5, tt + 1.4, ('hand', 'edith', 'R', Matrix(((0, 0, 1, -0.08), (1, 0, 0, 0.06), (0, 1, 0, -0.03), (0, 0, 0, 1)))))
    osw_rest(F, tt + 0.55, dur=0.7)
    lap = lambda sd, sx: ('world', tuple(V(EDITH[0], EDITH[1], 0) + V(sx * 0.09, -0.23, SZ + 0.37)), (-sx * 0.6, -0.2, -0.6), (sx * 0.4, -0.2, 0.9))
    for sd, sx in (('L', 1), ('R', -1)):
        Ed.gesture(tt + 0.9, sd, lap(sd, sx), dur=0.6)
    F.attach('rye', tt + 1.4, T + 200, ('fn', lambda t: lap_loaf_matrix(F, t)))
    Ed.look_at(tt + 0.6, ('actor', 'edith', 'root', (0, -0.25, SZ + 0.36)), dur=0.5)
    F.end(b4 + 0.65)


def lap_loaf_matrix(F, t):
    Ed = F.C['edith']
    M = Ed.arm.matrix_world
    return M @ Matrix.Translation((0.0, -0.22, 0.40)) @ Euler((0, 0, math.radians(90))).to_matrix().to_4x4()


def s3_9(F):
    T = F.begin('3.9', 'He stood by the lamp / you lean / never fixed it')
    O, Ed = F.A['oswald'], F.A['edith']
    cam_setup(F, 'B')
    osw_rest(F, T, dur=0.01)
    O.look_at(T + 0.15, V(PATCH[0], PATCH[1], 0.9), dur=0.6)
    O.expr(T + 0.15, smile=0.35, brow=0.25, brow_in=0.2, lid_L=0.92, lid_R=0.92, dur=0.5)
    a, b = F.say('O03', T + 0.8, gain=-2.0)
    O.nod(a + 0.2, amt=6, dur=0.6)
    O.look_at(a + 1.3, ('actor', 'edith', 'eyes'), dur=0.4)
    Ed.look_at(T + 0.3, ('actor', 'oswald', 'eyes'), dur=0.5)
    Ed.expr(T + 0.3, smile=0.2, brow_in=0.4, dur=0.5)
    # her cap tilts, teasing
    Ed.tilt(b + 0.15, amt=-9, dur=0.45)
    Ed.expr(b + 0.15, smile=0.35, smirk=0.5, brow=0.3, brow_asym=0.4, lidlo_L=0.3, lidlo_R=0.3, dur=0.4)
    a2, b2 = F.say('E04', b + 0.45)
    # caught: freezes, blinks twice, sheepish grin, dip of the head, brows up
    O.expr(a2 + 0.45, smile=0.0, brow=0.3, lid_L=1.12, lid_R=1.12, dur=0.12)
    O.blink(a2 + 0.6)
    O.blink(a2 + 0.95)
    O.hold_eyes(a2, b2 + 0.6)
    O.expr(b2 - 0.5, smile=0.7, smirk=0.3, brow=0.7, brow_in=0.4, lid_L=0.95, lid_R=0.95, lidlo_L=0.4, lidlo_R=0.4, dur=0.35)
    O.head(b2 - 0.45, pitch=10, roll=-5, dur=0.35)
    O.head(b2 + 0.3, pitch=2, roll=0, dur=0.5)
    Ed.tilt(b2 + 0.3, amt=0, dur=0.6)
    a3, b3 = F.say('E05', b2 + 0.6)
    Ed.expr(a3, smile=0.3, smirk=0.0, brow_asym=0.0, brow=0.1, brow_in=0.55, lid_L=0.92, lid_R=0.92, dur=0.6)
    # the grin softens; he looks down, slow blink, breath out, eyes back to the lamp; a swallow
    O.expr(b3 - 0.6, smile=0.25, smirk=0.0, brow=0.0, brow_in=0.65, lidlo_L=0.15, lidlo_R=0.15, dur=0.6)
    O.look_at(b3 - 0.5, ('actor', 'edith', 'root', (-0.3, -0.5, 0.2)), dur=0.6)
    O.expr(b3 - 0.1, blink=1.0, dur=0.3)
    O.expr(b3 + 0.25, blink=0.0, dur=0.4)
    O.breath_pulse(b3 + 0.1, dur=1.0, amt=1.5)
    F.sfx('breath_exhale', b3 + 0.35, gain=-16.0)
    O.look_at(b3 + 0.7, V(LAMP[0], LAMP[1], 1.0), dur=0.6)
    O.expr(b3 + 1.15, press=0.7, dur=0.08)
    O.expr(b3 + 1.32, press=0.0, dur=0.12)
    O.pulses_head.add(b3 + 1.15, 0.35, lambda u: np.array([4 * math.sin(math.pi * u), 0, 0]))
    F.end(b3 + 1.6)


def s3_10(F):
    T = F.begin('3.10', 'Thirty-one minutes')
    O, Ed = F.A['oswald'], F.A['edith']
    cam_setup(F, 'B')
    Ed.expr(T + 0.05, smile=0.0, brow_in=0.5, brow=0.0, lid_L=0.9, lid_R=0.9, dur=0.4)
    Ed.head(T + 0.35, pitch=-17, dur=0.6)
    Ed.look_at(T + 0.35, V(EDITH[0] - 0.4, 8.0, 14.0), dur=0.6)
    O.look_at(T + 0.95, V(EDITH[0] - 0.4, 8.0, 14.0), dur=0.6)
    O.expr(T + 0.95, brow=0.2, brow_in=0.4, dur=0.5)
    a, b = F.say('E06', T + 1.0)
    F.end(b + 0.35)


def s3_11(F):
    T = F.begin('3.11', 'The dial, 4:27')
    F.camera((DIAL.x - 0.5, -3.0, 2.4), DIAL + Vector((0, 0, -0.9)), 52)
    F.clock(T - 0.02, 4, 27)
    F.key_val(F.S['dial_mat'].node_tree.nodes['glow'].outputs[0], 'default_value', T - 0.02, 0.35, 0.01)
    a, b = F.say('E07', T + 0.5)
    a2, b2 = F.say('E08', b + 0.35)
    F.cue('cello_note', T + 0.3, 9.5, gain=-12.0)
    F.end(b2 + 0.4)


def s3_12(F):
    T = F.begin('3.12', 'Thirty-one Sundays')
    O, Ed = F.A['oswald'], F.A['edith']
    cam_setup(F, 'E')
    O.look_at(T, V(EDITH[0] - 0.4, 8.0, 14.0), dur=0.01, weight=0.6)
    O.look_at(T + 0.05, ('actor', 'edith', 'root', (-0.2, -0.6, 0.3)), dur=0.3, weight=0.8)
    for k, gy in enumerate((-4, 3, -3, 4, -2)):
        O.gaze_off.set(T + 0.15 + k * 0.2, np.array([gy, 0.0]), 0.05)
    O.gaze_off.set(T + 1.2, np.array([0.0, 0.0]), 0.1)
    O.expr(T + 0.4, brow=0.55, brow_in=0.4, dur=0.25)
    O.expr(T + 0.95, brow=-0.1, brow_in=0.75, jaw=0.06, dur=0.35)
    O.look_at(T + 1.3, ('actor', 'edith', 'eyes'), dur=0.4)
    O.hold_eyes(T, T + 3.2)
    Ed.look_at(T + 0.6, ('actor', 'oswald', 'eyes'), dur=0.5)
    Ed.head(T + 0.6, pitch=4, dur=0.6)
    a, b = F.say('O04', T + 1.5)
    F.end(b + 0.3)


def s3_13(F):
    T = F.begin('3.13', "I don't want it fixed. Isn't that awful? No.")
    O, Ed = F.A['oswald'], F.A['edith']
    cam_setup(F, 'C')
    Ed.expr(T + 0.1, press=0.6, smile=-0.2, brow_in=0.7, dur=0.25)
    Ed.nod(T + 0.15, amt=7, dur=0.5)
    Ed.look_at(T + 0.35, ('actor', 'edith', 'root', (0, -0.25, SZ + 0.38)), dur=0.4)
    a, b = F.say('E09', T + 0.6)
    Ed.expr(a, press=0.0, dur=0.2)
    Ed.look_at(b + 0.12, ('actor', 'oswald', 'eyes'), dur=0.35)
    Ed.head(b + 0.12, pitch=4, yaw=-8, dur=0.4)
    Ed.expr(b + 0.12, brow=0.25, brow_in=0.3, brow_asym=-0.3, lid_L=0.95, lid_R=0.9, smile=-0.05, dur=0.35)
    a2, b2 = F.say('E10', b + 0.4)
    a3, b3 = F.say('O05', b2 + 0.25, gain=-2.0)
    O.shake(a3 - 0.05, amt=5, dur=0.6, n=1)
    O.expr(a3 - 0.1, smile=0.0, brow_in=0.5, brow=0.0, dur=0.2)
    Ed.hold_eyes(b2, b3 + 1.0)
    Ed.shoulders(b3 + 0.35, -7, dur=0.6)
    Ed.expr(b3 + 0.35, brow_asym=0.0, brow_in=0.55, lid_L=0.9, lid_R=0.9, dur=0.6)
    Ed.head(b3 + 0.35, pitch=2, yaw=0, dur=0.6)
    F.end(b3 + 0.8)


def s3_14(F):
    T = F.begin('3.14', 'The minister came twice. Called me Ethel.')
    Ed = F.A['edith']
    cam_setup(F, 'D')
    Ed.look_at(T + 0.15, V(1.8, -2.5, 1.0), dur=0.5)
    Ed.head(T + 0.15, pitch=0, yaw=0, dur=0.5)
    Ed.expr(T + 0.45, smile=0.3, smirk=0.55, brow=0.15, brow_asym=0.55, brow_in=0.2, lid_L=0.92, lid_R=0.92, dur=0.35)
    a, b = F.say('E11', T + 0.8)
    a2, b2 = F.say('E12', b + 0.45)
    Ed.shrug(b2 - 0.65, amt=9, dur=0.6, hold=0.15)
    Ed.expr(b2 + 0.1, smile=0.1, smirk=0.2, brow_asym=0.2, brow_in=0.5, dur=0.6)
    F.end(b2 + 0.7)


def s3_15(F):
    T = F.begin('3.15a', 'Oscar: the joke reflex')
    O, Ed = F.A['oswald'], F.A['edith']
    cam_setup(F, 'E')
    O.look_at(T, ('actor', 'edith', 'eyes'), dur=0.3)
    O.expr(T + 0.15, brow=0.85, smile=0.75, lidlo_L=0.4, lidlo_R=0.4, brow_in=0.0, dur=0.25)
    hp = F.C['oswald'].H.p
    brim = F.C['oswald'].hp((-0.055, -hp['ry'] * 1.02, 0.072))
    O.gesture(T + 0.2, 'R', ('head', brim, (0.1, -0.4, 1.0), (-0.9, 0, 0.2)), dur=0.55)
    O.fingers(T + 0.2, 'R', 0.85, per={'index': 0.0, 'middle': 0.05, 'ring': 0.95, 'pinky': 0.95}, thumb=0.8, dur=0.3)
    a, b = F.say('O06', T + 0.5, gain=-2.0)
    a2, b2 = F.say('E13', b - 2 / 24.0)
    O.expr(a2 + 0.15, smile=0.35, brow=0.4, dur=0.3)
    knee = lambda t: ('chest', (-0.18, -0.36, F.A['oswald'].B.hipZ - 0.10), (0, -0.6, -0.8), (-1, 0, 0))
    O.gesture(a2 + 0.6, 'R', knee, dur=1.0)
    O.fingers(a2 + 0.6, 'R', 0.35, dur=0.6)
    O.expr(a2 + 0.5, smile=0.0, brow=0.0, brow_in=0.55, lidlo_L=0.0, lidlo_R=0.0, dur=1.0)
    O.look_at(b2 + 0.1, ('actor', 'edith', 'root', (-0.25, -0.65, 0.05)), dur=0.6)
    O.expr(b2 + 0.4, press=0.65, dur=0.1)
    O.expr(b2 + 0.58, press=0.0, dur=0.15)
    O.pulses_head.add(b2 + 0.4, 0.4, lambda u: np.array([5 * math.sin(math.pi * u), 0, 0]))
    O.look_at(b2 + 1.35, ('actor', 'edith', 'eyes'), dur=0.5)
    O.expr(b2 + 1.35, brow_in=0.4, brow=0.05, lid_L=1.0, lid_R=1.0, dur=0.5)
    Ed.look_at(T, ('actor', 'oswald', 'eyes'), dur=0.3)
    Ed.expr(a2, smile=0.2, brow_in=0.4, brow=0.1, dur=0.4)
    a3, b3 = F.say('O07', b2 + 1.85, gain=-2.0)
    F.end(b3 + 0.25)
    T2 = F.begin('3.15b', 'I didn\'t know what to say. / Nobody does.')
    cam_setup(F, 'C')
    a4, b4 = F.say('O08', T2 + 0.1, gain=-2.0)
    Ed.expr(a4 + 0.5, lid_L=0.78, lid_R=0.78, brow_in=0.45, brow=0.0, smile=0.22, smirk=0.0, dur=0.8)
    Ed.breath_pulse(a4 + 0.7, dur=1.2, amt=1.4)
    F.sfx('breath_exhale', a4 + 1.1, gain=-18.0)
    a5, b5 = F.say('E14', b4 + 0.45)
    Ed.nod(a5 + 0.1, amt=3, dur=0.5)
    F.end(b5 + 0.5)


def s3_16(F):
    T = F.begin('3.16', 'Snow brushed off. Mr. Bunce. No.')
    O, Ed = F.A['oswald'], F.A['edith']
    cam_setup(F, 'B')
    sh = lambda dx, dz: (lambda t: ('world', tuple(V(EDITH[0] + dx, EDITH[1] - 0.06, SZ + 0.62 + dz)), (0.8, 0.0, -0.4), (0, -0.7, 0.6)))
    O.look_at(T + 0.05, ('actor', 'edith', 'chest', (-0.08, 0, 0.12)), dur=0.3)
    O.gesture(T + 0.3, 'L', sh(-0.16, 0.06), dur=0.3)
    O.fingers(T + 0.3, 'L', 0.15, dur=0.2)
    O.gesture(T + 0.62, 'L', sh(-0.05, 0.10), dur=0.18)
    O.gesture(T + 0.82, 'L', sh(-0.16, 0.06), dur=0.18)
    O.gesture(T + 1.0, 'L', sh(-0.04, 0.10), dur=0.18)
    F.set_visible(F.snowline[0], T + 0.75, False)
    F.set_visible(F.snowline[1], T + 1.05, False)
    osw_rest(F, T + 1.25, dur=0.3, sides='L')
    Ed.look_at(T + 0.35, ('actor', 'oswald', 'hand_L'), dur=0.25)
    Ed.expr(T + 0.35, lid_L=1.1, lid_R=1.1, brow=0.3, brow_in=0.4, smile=0.0, dur=0.25)
    # takes hold of his own lapels
    for sd, sx in (('L', 1), ('R', -1)):
        O.gesture(T + 1.4, sd, ('chest', (sx * 0.07, -0.13, O.B.hipZ + 0.36), (0, 0.1, -1), (sx * 0.3, -1, 0)), dur=0.35)
        O.fingers(T + 1.4, sd, 0.85, thumb=0.7, dur=0.3)
    O.look_at(T + 1.4, ('actor', 'edith', 'eyes'), dur=0.3)
    O.expr(T + 1.4, brow=0.3, press=0.5, dur=0.3)
    Ed.look_at(T + 1.5, ('actor', 'oswald', 'eyes'), dur=0.25)
    Ed.expr(T + 1.6, brow=1.0, brow_in=-0.3, lid_L=1.15, lid_R=1.15, press=0.4, smile=-0.1, dur=0.2)
    a, b = F.say('E15', T + 1.9)
    Ed.nod(a + 0.55, amt=4, dur=0.3)
    # one two-handed tug: the middle button pings off; he rocks back on his heel
    tg = b + 0.1
    for sd, sx in (('L', 1), ('R', -1)):
        O.gesture(tg, sd, ('chest', (sx * 0.12, -0.20, O.B.hipZ + 0.34), (0, 0.1, -1), (sx * 0.3, -1, 0)), dur=0.12)
    F.sfx('wool_strain_ping', tg - 0.25, gain=-8.0)
    btn = [o for o in F.C['oswald'].coll.objects if o.name.startswith('oswald') and 'button' in o.data.materials[0].name] if False else []
    O.posture(tg + 0.1, 'sit_heel', dur=0.35, down='R')
    O.posture(tg + 0.6, 'kneel', dur=0.4, down='R', lean=8)
    Ed.expr(tg + 0.35, smile=0.55, jaw=0.15, brow=0.6, brow_in=0.0, press=0.0, lid_L=1.0, lid_R=1.0, dur=0.12)
    F.sfx('huff_laugh', tg + 0.35, gain=-8.0)
    Ed.bounce(tg + 0.35, dur=0.5, amt=0.008, n=1)
    Ed.expr(tg + 0.75, jaw=0.0, smile=0.3, dur=0.4)
    F.end(tg + 1.4)
    F.t_coat_off = F.t


def s3_17(F):
    T = F.begin('3.17', 'Cut on action: the coat around her shoulders')
    O, Ed = F.A['oswald'], F.A['edith']
    cam_setup(F, 'B')
    # coat already off: shirtsleeves and green waistcoat
    for (mat, node) in F.C['oswald'].coat_off_nodes:
        F.key_val(node.outputs[0], 'default_value', T - 0.01, 1.0, 0.01)
    kb = F.C['oswald'].coat.data.shape_keys.key_blocks['slim']
    F.key_val(kb, 'value', T - 0.01, 1.0, 0.01)
    for ob in F.C['oswald'].coll.objects:
        if 'button' in ob.name:
            F.set_visible(ob, T - 0.01, False)
    # swing the mustard coat around her shoulders
    for sd, sx in (('L', 1), ('R', -1)):
        O.gesture(T, sd, ('world', tuple(V(EDITH[0], EDITH[1], 0) + V(-0.36 + sx * 0.22, -0.40, SZ + 0.95)), (sx * 0.3, 0.3, 1), (0, -1, 0)), dur=0.01)
        O.gesture(T + 0.15, sd, ('world', tuple(V(EDITH[0], EDITH[1], 0) + V(sx * 0.26, -0.05, SZ + 0.86)), (0, 0.2, 1), (0, -1, 0.1)), dur=0.5)
        O.fingers(T, sd, 0.6, thumb=0.6, dur=0.01)
    F.attach('held_coat', T, T + 0.75, ('hand', 'oswald', 'R', hand_hold(0.30, 0.06, 0.0, 0, 0, 0)))
    F.set_visible(F.held_coat, T - 0.01, True)
    F.set_visible(F.held_coat, T + 0.7, False)
    F.set_visible(F.drape, T + 0.68, True)
    F.sfx('cloth_rustle', T + 0.15, gain=-8.0)
    O.look_at(T, ('actor', 'edith', 'chest', (0, 0, 0.15)), dur=0.3)
    Ed.look_at(T + 0.7, ('actor', 'oswald', 'hand_R'), dur=0.3)
    Ed.expr(T + 0.7, smile=0.0, jaw=0.0, brow=0.2, brow_in=0.5, lid_L=0.9, lid_R=0.9, dur=0.3)
    Ed.hold_eyes(T + 0.7, T + 2.2)
    # tucks the collar up under her chin with both hands
    for sd, sx in (('L', 1), ('R', -1)):
        O.gesture(T + 1.0, sd, ('world', tuple(V(EDITH[0], EDITH[1], 0) + V(sx * 0.06, -0.15, SZ + 0.66)), (-sx * 0.3, 0.6, 0.6), (0, -0.8, 0.4)), dur=0.5)
        O.gesture(T + 1.6, sd, ('world', tuple(V(EDITH[0], EDITH[1], 0) + V(sx * 0.05, -0.17, SZ + 0.69)), (-sx * 0.3, 0.6, 0.6), (0, -0.8, 0.4)), dur=0.3)
    Ed.head(T + 1.6, pitch=12, dur=0.5)
    osw_rest(F, T + 2.1, dur=0.5)
    # sits back on his heel, suddenly half his size; a pleased eyebrow flourish
    O.posture(T + 2.15, 'sit_heel', dur=0.6, down='R')
    O.look_at(T + 2.2, ('actor', 'edith', 'eyes'), dur=0.4)
    O.expr(T + 2.5, brow=0.9, smile=0.45, smirk=0.3, dur=0.15)
    O.expr(T + 2.75, brow=0.25, dur=0.3)
    a, b = F.say('O09', T + 2.6, gain=-2.0)
    Ed.look_at(a + 0.2, ('actor', 'oswald', 'eyes'), dur=0.4)
    Ed.head(a + 0.2, pitch=4, dur=0.5)
    tr = a + 1.65
    Ed.expr(tr, blink=1.0, smile=0.75, lidlo_L=0.8, lidlo_R=0.8, jaw=0.12, dur=0.15)
    Ed.bounce(tr, dur=0.45, amt=0.01, n=1)
    F.sfx('laugh_old_woman', tr, gain=-12.0)
    Ed.expr(tr + 0.45, blink=0.0, jaw=0.0, smile=0.5, lidlo_L=0.5, lidlo_R=0.5, dur=0.35)
    F.end(b + 0.45)


def s3_18(F):
    T = F.begin('3.18', 'Edith. ...Please.')
    Ed, O = F.A['edith'], F.A['oswald']
    cam_setup(F, 'D')
    Ed.expr(T + 0.2, smile=0.0, lidlo_L=0.0, lidlo_R=0.0, lid_L=1.02, lid_R=1.02, brow_in=0.65, brow=0.15, dur=0.7)
    Ed.look_at(T + 0.3, ('actor', 'oswald', 'eyes'), dur=0.4)
    Ed.head(T + 0.3, pitch=0, dur=0.6)
    Ed.hold_eyes(T, T + 4.5)
    a, b = F.say('E16', T + 1.0)
    Ed.look_at(b + 0.15, ('actor', 'edith', 'root', (-0.25, -0.6, 0.1)), dur=0.45)
    Ed.head(b + 0.15, pitch=8, dur=0.5)
    Ed.expr(b + 0.15, lid_L=0.82, lid_R=0.82, brow_in=0.8, press=0.2, dur=0.5)
    a2, b2 = F.say('E17', b + 1.15)
    Ed.expr(a2, press=0.0, dur=0.1)
    F.end(b2 + 0.8)


def s3_19(F):
    T = F.begin('3.19', 'Edith.')
    O = F.A['oswald']
    cam_setup(F, 'E')
    O.look_at(T, ('actor', 'edith', 'eyes'), dur=0.01)
    O.expr(T, smile=0.0, brow_in=0.55, brow=0.0, lid_L=0.95, lid_R=0.95, dur=0.01)
    O.expr(T + 0.4, lid_L=0.88, lid_R=0.88, brow_in=0.7, dur=0.5)
    O.hold_eyes(T, T + 2.5)
    O.nod(T + 0.85, amt=6, dur=0.6)
    a, b = F.say('O10', T + 1.3, gain=-3.0)
    F.end(b + 0.7)


def tear_fn(F, t0, t1):
    Ed = F.C['edith']
    H, hg = Ed.H, Ed.hg
    e = hg['eyes']['L']
    r = H.p['eye_r']
    c = e['c']
    mc = hg['mouth_c']
    fr_ = hg['verts'][hg['verts'][:, 1] < -0.02]
    pts = []
    for u in np.linspace(0, 1, 12):
        x = c[0] + 0.004 - u * (c[0] + 0.004 - (H.p['mouth_halfw'] * H.p['ry'] * 1.05))
        z = c[2] - r * 0.95 - u * (c[2] - r * 0.95 - (mc[2] + 0.004))
        d = (fr_[:, 0] - x) ** 2 + (fr_[:, 2] - z) ** 2
        y = fr_[np.argmin(d), 1] - 0.0016
        pts.append(np.array([x, y, z]))
    hs = Ed.s['head_scale']
    rest_w = [Vector(p * hs + Ed.head_origin) for p in pts]
    B = Ed.arm.data.bones['head']
    Rinv = (Ed.arm.matrix_world @ B.matrix_local).inverted()
    local = [Rinv @ p for p in rest_w]

    def fn(t):
        pb = Ed.arm.pose.bones['head']
        M = Ed.arm.matrix_world @ pb.matrix
        well = 0.9
        if t < t0 + well:
            u = 0.0
            s = perf.clamp((t - t0) / well, 0.05, 1.0)
        else:
            u = perf.ease(perf.clamp((t - t0 - well) / (t1 - t0 - well - 0.6), 0, 1), 'inout')
            s = 1.0 - 0.6 * perf.clamp((t - (t1 - 0.6)) / 0.6, 0, 1)
        i = u * (len(local) - 1)
        k = min(int(i), len(local) - 2)
        p = local[k].lerp(local[k + 1], i - k)
        return M @ Matrix.Translation(p) @ Matrix.Diagonal((s, s, s * (1 + 0.3 * u), 1))
    return fn


def s3_20(F):
    T = F.begin('3.20', "Nobody's said it since April. (the tear)")
    Ed = F.A['edith']
    cam_setup(F, 'D', loc2=(2.70, 2.78, SZ + 0.79), target2=('actor', 'edith', 'eyes', (0.0, 0.0, -0.06)),
              t_move=(T, T + 6.8), ease='linear')
    Ed.expr(T + 0.3, blink=1.0, dur=0.6)
    Ed.hold_eyes(T, T + 7.0)
    # the chin trembles once; she presses her lips together to stop it
    for k in range(3):
        tt = T + 1.0 + k * (3 / 24.0)
        Ed.expr(tt, press=0.5 if k % 2 == 0 else 0.0, pout=0.0 if k % 2 == 0 else 0.6, jaw=0.03 if k % 2 else 0.0, dur=0.05)
    Ed.expr(T + 1.38, press=0.65, pout=0.15, jaw=0.0, dur=0.12)
    Ed.expr(T + 1.55, press=0.0, pout=0.0, dur=0.12)
    Ed.expr(T + 0.3, brow_in=0.95, brow=-0.1, smile=-0.25, dur=0.8)
    a, b = F.say('E18', T + 1.6)
    t_tear = a + 1.25
    F.attach('tear', t_tear, T + 30, ('fn', tear_fn(F, t_tear, T + 6.4)))
    F.set_visible(F.tear, t_tear, True)
    F.set_visible(F.tear, T + 6.45, False)
    Ed.breath_pulse(b + 0.3, dur=1.6, amt=1.2)
    F.end(T + 6.5)


def s3_21(F):
    T = F.begin('3.21', 'His hand on her shoulder. You eat too, Oswald.')
    O, Ed = F.A['oswald'], F.A['edith']
    cam_setup(F, 'B')
    O.posture(T, 'kneel', dur=0.4, down='R', lean=8)
    shoulder = lambda t: ('world', tuple(V(EDITH[0] - 0.13, EDITH[1] - 0.05, SZ + 0.66)), (0.7, 0.5, -0.3), (0.1, -0.5, 0.85))
    O.gesture(T + 0.2, 'R', shoulder, dur=0.5)
    O.fingers(T + 0.2, 'R', 0.3, spread=0.2, thumb=0.2, dur=0.4)
    O.look_at(T + 0.2, ('actor', 'edith', 'eyes'), dur=0.4)
    O.expr(T + 0.2, smile=0.0, brow_in=0.6, brow=0.0, lid_L=0.9, lid_R=0.9, dur=0.5)
    t_land = T + 0.7
    F.cue('name_piano', t_land, 30.0, gain=-9.0, with_strings=True, strings_at=1.35)
    # she pats his hand twice
    Ed.gesture(T + 1.8, 'L', ('world', tuple(V(EDITH[0] - 0.17, EDITH[1] - 0.10, SZ + 0.72)), (-0.8, -0.3, -0.2), (0, -0.3, 1)), dur=0.4)
    Ed.fingers(T + 1.8, 'L', 0.15, dur=0.3)
    for k in range(2):
        Ed.gesture(T + 2.2 + k * 0.32, 'L', ('world', tuple(V(EDITH[0] - 0.17, EDITH[1] - 0.10, SZ + 0.70)), (-0.8, -0.3, -0.2), (0, -0.3, 1)), dur=0.1)
        Ed.gesture(T + 2.33 + k * 0.32, 'L', ('world', tuple(V(EDITH[0] - 0.17, EDITH[1] - 0.10, SZ + 0.74)), (-0.8, -0.3, -0.2), (0, -0.3, 1)), dur=0.1)
    Ed.release(T + 2.95, 'L', dur=0.4)
    # opens her eyes, sniffs, sits up straighter: the schoolteacher is back
    Ed.expr(T + 2.8, blink=0.0, lid_L=0.95, lid_R=0.95, brow_in=0.3, brow=0.1, smile=0.05, dur=0.4)
    F.sfx('sniff', T + 3.0, gain=-12.0)
    Ed.chest(T + 3.15, pitch=-6, dur=0.5)
    Ed.head(T + 3.15, pitch=-2, dur=0.5)
    osw_rest(F, T + 3.3, dur=0.6, sides='R')
    # tears the end off the small rye, holds it out to him
    tt = T + 3.6
    Ed.look_at(tt - 0.2, ('actor', 'edith', 'root', (0, -0.25, SZ + 0.38)), dur=0.3)
    for sd, sx in (('L', 1), ('R', -1)):
        Ed.gesture(tt, sd, ('world', tuple(V(EDITH[0], EDITH[1], 0) + V(sx * 0.09, -0.26, SZ + 0.42)), (-sx * 0.5, -0.3, -0.5), (sx * 0.4, -0.2, 0.9)), dur=0.35)
        Ed.fingers(tt, sd, 0.6, thumb=0.5, dur=0.3)
    Ed.gesture(tt + 0.45, 'R', ('world', tuple(V(EDITH[0], EDITH[1], 0) + V(-0.16, -0.27, SZ + 0.45)), (-0.6, -0.3, -0.4), (-0.4, -0.2, 0.9)), dur=0.25)
    F.sfx('crust_crack', tt + 0.5, gain=-6.0)
    F.set_visible(F.props['rye'], tt + 0.5, False)
    F.set_visible(F.props['rye_main'], tt + 0.5, True)
    F.set_visible(F.props['rye_end'], tt + 0.5, True)
    F.attach('rye_main', tt + 0.5, T + 200, ('fn', lambda t: lap_loaf_matrix(F, t) @ Matrix.Translation((0.02, 0, 0))))
    F.attach('rye_end', tt + 0.5, tt + 4.3, ('hand', 'edith', 'R', Matrix(((0, 0, 1, -0.0), (1, 0, 0, 0.07), (0, 1, 0, -0.03), (0, 0, 0, 1)))))
    hold_out = lambda t: ('world', tuple(V(EDITH[0], EDITH[1], 0) + V(-0.34, -0.33, SZ + 0.58)), (-0.7, -0.6, 0.1), (0, 0, 1))
    Ed.gesture(tt + 0.9, 'R', hold_out, dur=0.45)
    Ed.release(tt + 0.9, 'L', dur=0.5)
    Ed.look_at(tt + 0.95, ('actor', 'oswald', 'eyes'), dur=0.35)
    Ed.expr(tt + 0.95, smile=0.0, brow=0.1, brow_in=0.0, lid_L=0.9, lid_R=0.9, press=0.25, dur=0.35)
    a, b = F.say('O11', T + 5.0, gain=-2.0)
    for sd, sx in (('L', 1), ('R', -1)):
        O.gesture(a - 0.1, sd, ('chest', (sx * 0.14, -0.36, O.B.hipZ + 0.24), (sx * 0.2, -0.6, 0.8), (0, 0.7, 0.2)), dur=0.35)
        O.fingers(a - 0.1, sd, 0.05, spread=0.4, thumb=0.0, dur=0.3)
    O.shake(a + 0.1, amt=5, dur=0.6, n=1)
    a2, b2 = F.say('E19', b + 0.55)
    # at his own first name he goes still: inner brows lift, one slow blink
    tn = b2 - 0.45
    O.expr(tn, brow_in=0.85, brow=0.15, smile=0.0, dur=0.25)
    O.hold_eyes(tn - 0.5, tn + 1.5)
    O.expr(tn + 0.35, blink=1.0, dur=0.15)
    O.expr(tn + 0.52, blink=0.0, dur=0.18)
    # then he takes the bread
    tk = b2 + 0.35
    O.gesture(tk, 'R', ('world', tuple(V(EDITH[0], EDITH[1], 0) + V(-0.36, -0.36, SZ + 0.57)), (0.6, 0.6, 0.0), (0, 0, -1)), dur=0.35)
    O.fingers(tk, 'R', 0.45, thumb=0.3, dur=0.3)
    F.attach('rye_end', tt + 4.3, T + 200, ('hand', 'oswald', 'R', LOAF_PALM @ Matrix.Translation((0, 0, 0.0))))
    O.gesture(tk + 0.5, 'R', ('chest', (-0.08, -0.36, O.B.hipZ + 0.10), (0.5, -0.7, 0.2), (0, 0.3, -1)), dur=0.6)
    for sd, sx in (('L', 1), ('R', -1)):
        Ed.gesture(tk + 0.4, sd, ('world', tuple(V(EDITH[0], EDITH[1], 0) + V(sx * 0.09, -0.23, SZ + 0.37)), (-sx * 0.6, -0.2, -0.6), (sx * 0.4, -0.2, 0.9)), dur=0.6)
    osw_rest(F, tk + 1.3, dur=0.4, sides='L')
    for A_ in (O, Ed):
        A_.look_at(tk + 0.8, V(1.6, -3.5, 1.0), dur=0.8)
    Ed.expr(tk + 0.8, smile=0.25, brow_in=0.2, press=0.0, dur=0.8)
    O.expr(tk + 0.8, smile=0.2, brow_in=0.3, dur=0.8)
    F.end(tk + 1.6)


# ====================================================================== SCENE 4
LEAN_SPOT = (1.85, 2.0)


def s4_1(F):
    T = F.begin('4.1', 'Encore: up, shiver, hat tip, the waddle is back')
    O, Ed = F.A['oswald'], F.A['edith']
    F.camera((1.22, 0.80, 1.62), (2.55, 3.35, 0.78), 30)
    O.release(T, 'L', dur=0.3)
    O.release(T, 'R', dur=0.3)
    # picks up his cane and stands; knees crack
    O.gesture(T + 0.1, 'R', ('world', (2.05, FY - 1.10, SZ + 0.06), (0, -1, 0), (-1, 0, 0)), dur=0.35)
    O.fingers(T + 0.1, 'R', 0.75, thumb=0.8, dur=0.3)
    F.attach('cane', T + 0.45, T + 200, ('hand', 'oswald', 'R', CANE_GRIP))
    O.posture(T + 0.35, 'stand', dur=0.75, splay=24, knee=0.2, stoop=4)
    O.place(T + 0.35, KNEEL[0] - 0.12, KNEEL[1] - 0.2, KNEEL_H, z=SZ, dur=0.7)
    O.release(T + 0.6, 'R', dur=0.4)
    O.gesture(T + 0.9, 'R', ('chest', (-0.30, -0.14, O.B.hipZ + 0.12), (0, -1, -0.25), (-1, 0.2, 0)), dur=0.3)
    F.sfx('knee_crack', T + 0.75, gain=-8.0)
    # one theatrical full-body shiver in his shirtsleeves
    O.pulses_chest.add(T + 1.05, 0.5, lambda u: np.array([0, 6 * math.sin(40 * u), 4 * math.sin(36 * u)]) * math.sin(math.pi * u))
    O.pulses_head.add(T + 1.05, 0.5, lambda u: np.array([0, 5 * math.sin(44 * u), 0]) * math.sin(math.pi * u))
    O.expr(T + 1.0, press=0.6, brow=0.5, lid_L=0.7, lid_R=0.7, smile=-0.2, dur=0.15)
    O.expr(T + 1.55, press=0.0, smile=0.5, brow=0.3, lid_L=1.0, lid_R=1.0, dur=0.3)
    O.look_at(T + 1.4, ('actor', 'edith', 'eyes'), dur=0.3)
    tip_hat(F, T + 1.6, dur=0.9)
    Ed.look_at(T + 0.3, ('actor', 'oswald', 'eyes'), dur=0.6)
    Ed.expr(T + 0.3, smile=0.3, brow_in=0.2, lid_L=0.95, lid_R=0.95, dur=0.5)
    Ed.nod(T + 1.95, amt=7, dur=0.7)
    Ed.head(T + 1.95, pitch=2, roll=-4, dur=0.6)
    # sets off with the jaunty waddle, cane twirling, chest puffed out against the cold
    O.turn(T + 2.35, heading_to((KNEEL[0] - 0.12, KNEEL[1] - 0.2), LEAN_SPOT), dur=0.3)
    O.chest(T + 2.4, pitch=-8, dur=0.4)
    O.walk(T + 2.5, T + 4.2, [(KNEEL[0] - 0.12, KNEEL[1] - 0.2), LEAN_SPOT], stride=0.34, splay=26, style='waddle',
           bob=0.03, sway=0.024, lift=0.05, z=None)
    O.place(T + 4.25, LEAN_SPOT[0], LEAN_SPOT[1], heading_to(LEAN_SPOT, EDITH), z=0.0, dur=0.01)
    F.attach('cane', T + 2.5, T + 4.2, ('fn', cane_twirl(F, T + 2.5, T + 4.2, turns=1.5)))
    F.cue('rag_motif', T, 13.0, gain=-6.0, crash_at=None)
    F.end(T + 3.5)


def s4_2(F):
    T = F.begin('4.2', "There's the lean (she laughs first)")
    O, Ed = F.A['oswald'], F.A['edith']
    F.camera((3.25, 3.90, SZ + 0.80), (LEAN_SPOT[0] + 0.15, LEAN_SPOT[1] + 0.2, 0.95), 30, fstop=2.0,
             focus_keys=[(-1e9, -1e9, ('actor', 'edith', 'eyes')),
                         (T + 1.2, T + 1.6, ('actor', 'oswald', 'head')),
                         (T + 3.15, T + 3.5, ('actor', 'edith', 'eyes'))])
    O.place(T, LEAN_SPOT[0], LEAN_SPOT[1], heading_to(LEAN_SPOT, EDITH) + 160, z=0.0, dur=0.01)
    O.turn(T + 1.3, heading_to(LEAN_SPOT, EDITH), dur=0.45)
    O.look_at(T + 1.3, ('actor', 'edith', 'eyes'), dur=0.4)
    Ed.look_at(T, ('actor', 'oswald', 'head'), dur=0.01)
    Ed.expr(T + 0.3, lid_L=0.82, lid_R=0.82, lidlo_L=0.5, lidlo_R=0.5, smile=0.25, dur=0.5)
    # arms wide: the lean, held 16 frames
    for sd, sx in (('L', 1), ('R', -1)):
        O.gesture(T + 1.7, sd, ('chest', (sx * 0.62, -0.10, O.B.hipZ + 0.52), (sx, -0.1, 0.25), (0, 0.4, 1)), dur=0.3)
        O.fingers(T + 1.7, sd, 0.1, spread=0.6, thumb=0.0, dur=0.3)
    F.attach('cane', T, T + 3.0, ('bone', 'oswald', 'upperarm.R', hand_hold(0.0, 0.10, 0.06, 0, 0, 90)))
    O.posture(T + 2.0, 'stand', dur=0.2, splay=24, lean=16, toes=0.8)
    O.posture(T + 2.0 + 0.2 + 16 / 24.0, 'stand', dur=0.3, splay=24, knee=0.2)
    O.expr(T + 1.8, smile=1.0, brow=0.8, dur=0.2)
    F.sfx('laugh_old_woman', T + 2.05, gain=-10.0)
    Ed.expr(T + 2.05, smile=0.8, jaw=0.2, lidlo_L=0.8, lidlo_R=0.8, dur=0.15)
    Ed.bounce(T + 2.05, dur=0.5, amt=0.008, n=2)
    a, b = F.say('E20', T + 2.45)
    Ed.expr(a, jaw=0.0, smile=0.6, dur=0.2)
    F.sfx('laugh_old_woman', b + 0.05, gain=-9.0)
    Ed.expr(b + 0.05, smile=0.9, jaw=0.2, lid_L=0.6, lid_R=0.6, lidlo_L=1.0, lidlo_R=1.0, dur=0.2)
    F.end(T + 4.0)


def s4_3(F):
    T = F.begin('4.3', 'He trips into the lamppost; the lamp lights itself')
    O, Ed = F.A['oswald'], F.A['edith']
    F.camera((1.45, -4.3, 1.6), (2.1, 2.9, 3.95), 26)
    F.clock(T - 0.02, 4, 29)
    O.place(T, LEAN_SPOT[0], LEAN_SPOT[1], heading_to(LEAN_SPOT, EDITH), z=0.0, dur=0.01)
    O.posture(T, 'stand', dur=0.01, splay=24, knee=0.2)
    for sd in 'LR':
        O.release(T, sd, dur=0.2)
    t_post = T + 1.6
    hug = (LAMP[0] + 0.02, LAMP[1] - 0.24)
    O.walk(T + 0.3, T + 0.75, [LEAN_SPOT, (2.18, 2.28)], stride=0.3, splay=24, style='waddle')
    # boot catches a cobble: stumble, arms windmilling
    O.walk(T + 0.8, t_post, [(2.18, 2.28), (2.10, 2.45), hug], stride=0.32, splay=10, bob=0.04, sway=0.03, lift=0.07)
    O.posture(T + 0.75, 'stand', dur=0.2, splay=10, lean=24, knee=0.4)
    for k in range(3):
        tt = T + 0.8 + k * 0.26
        for sd, sx in (('L', 1), ('R', -1)):
            up = (k + (sd == 'L')) % 2
            O.gesture(tt, sd, ('chest', (sx * 0.5, -0.15 + 0.2 * up, O.B.hipZ + (0.85 if up else 0.25)), (sx, 0, 0.5), (0, 0.5, 0.8)), dur=0.13)
    O.expr(T + 0.75, brow=1.0, jaw=0.4, round=0.6, lid_L=1.3, lid_R=1.3, smile=0.0, dur=0.1)
    F.attach('cane', T + 0.8, T + 1.0, ('hand', 'oswald', 'R', CANE_GRIP))
    F.attach('cane', T + 1.0, T + 30, ('world', world_m((2.4, 2.0, 0.012), (0, 90, -40))))
    F.sfx('thump_soft', T + 1.1, gain=-12.0)
    # catches the post with one arm
    O.posture(t_post, 'stand', dur=0.15, splay=10, lean=10, knee=0.2)
    O.turn(t_post - 0.1, heading_to(hug, LAMP), dur=0.15)
    O.gesture(t_post - 0.05, 'L', ('world', (LAMP[0] + 0.06, LAMP[1] + 0.05, 1.25), (-0.5, 0.6, 0.3), (0.5, -0.6, 0.4)), dur=0.12)
    O.release(t_post, 'R', dur=0.2)
    O.fingers(t_post, 'L', 0.8, thumb=0.6, dur=0.1)
    F.lamp(t_post, True, 0.2)
    F.sfx('gas_lamp_on', t_post, gain=-6.0)
    # freezes; looks up at the lamp; at his own arm; lets go very carefully
    O.expr(t_post + 0.1, brow=0.9, jaw=0.0, round=0.0, lid_L=1.25, lid_R=1.25, press=0.5, dur=0.15)
    O.hold_eyes(t_post, t_post + 1.6)
    O.look_at(t_post + 0.6, V(LAMP[0] + 0.4, LAMP[1] - 0.8, 3.6), dur=0.45)
    O.look_at(t_post + 1.2, ('actor', 'oswald', 'hand_L'), dur=0.35)
    O.release(t_post + 1.5, 'L', dur=0.7)
    O.fingers(t_post + 1.5, 'L', 0.35, dur=0.5)
    # turns to Edith and gives a deep, grand bow, as if he had done it on purpose
    O.turn(t_post + 1.75, heading_to(hug, EDITH), dur=0.4)
    O.look_at(t_post + 1.75, ('actor', 'edith', 'eyes'), dur=0.4)
    O.expr(t_post + 1.8, smile=0.85, brow=0.6, press=0.3, lid_L=1.0, lid_R=1.0, dur=0.3)
    O.posture(t_post + 1.95, 'stand', dur=0.55, splay=24, bow=48, knee=0.3)
    O.gesture(t_post + 1.95, 'R', ('chest', (0.05, -0.36, O.B.hipZ + 0.05), (0.7, -0.4, -0.3), (0, 0.6, -0.8)), dur=0.5)
    O.gesture(t_post + 1.95, 'L', ('chest', (0.48, 0.10, O.B.hipZ + 0.35), (1, 0.2, 0.2), (0, 0.3, 1)), dur=0.5)
    Ed.look_at(T, ('actor', 'oswald', 'head'), dur=0.3)
    Ed.expr(t_post + 0.2, smile=0.6, brow=0.4, dur=0.4)
    F.music_crash = t_post + 0.05
    F.end(T + 4.5)


# ====================================================================== SCENE 5
def s5_1(F):
    T = F.begin('5.1', 'Good.')
    To, Te = F.A['tomas'], F.A['teddy']
    F.camera((-0.25, FY - 1.55, SZ + 1.40), (DOOR_X - 0.05, FY - 0.05, SZ + 1.25), 38)
    To.place(T, DOOR_X - 0.1, FY + 0.8, 0.0, z=SZ - 0.01)
    To.posture(T, 'stand', dur=0.01, splay=10)
    for sd in 'LR':
        To.release(T, sd, dur=0.01)
    F.sfx('shop_bell', T + 0.2, gain=-8.0)
    F.door(T + 0.1, 20, 0.3)
    To.walk(T + 0.3, T + 1.0, [(DOOR_X - 0.1, FY + 0.8), (DOOR_X - 0.05, FY + 0.05)], stride=0.45, z=SZ - 0.01)
    To.look_at(T + 1.0, ('actor', 'edith', 'head'), dur=0.4)
    To.expr(T + 1.0, lid_L=0.8, lid_R=0.8, brow_in=0.4, press=0.4, dur=0.4)
    To.gesture(T + 1.1, 'R', ('world', (DOOR_X + 0.25, FY + 0.05, SZ + 1.15), (0, 0.2, 1), (0.3, 1, 0)), dur=0.3)
    To.fingers(T + 1.1, 'R', 0.05, spread=0.3, dur=0.2)
    F.door(T + 1.3, 100, 0.5)
    To.release(T + 1.8, 'R', dur=0.4)
    Te.place(T, DOOR_X + 0.15, FY + 0.95, 0.0, z=SZ - 0.01)
    Te.posture(T, 'stand', dur=0.01, splay=8)
    Te.walk(T + 0.5, T + 1.25, [(DOOR_X + 0.15, FY + 0.95), (DOOR_X + 0.28, FY + 0.15)], stride=0.28, z=SZ - 0.01)
    Te.look_at(T + 1.3, ('actor', 'tomas', 'eyes'), dur=0.3)
    Te.expr(T + 1.3, jaw=0.45, brow=1.0, lid_L=1.25, lid_R=1.25, round=0.4, dur=0.2)
    a, b = F.say('K04', T + 1.55)
    a2, b2 = F.say('T06', b + 0.2)
    To.tilt(b2 - 0.1, amt=-10, dur=0.3)
    To.nod(b2 + 0.05, amt=6, dur=0.4)
    Te.expr(b2 + 0.1, jaw=0.1, round=0.0, smile=0.8, brow=0.6, dur=0.2)
    Te.look_at(b2 + 0.2, ('actor', 'edith', 'head'), dur=0.25)
    Te.walk(b2 + 0.35, b2 + 1.4, [(DOOR_X + 0.28, FY + 0.15), (0.6, FY - 0.55), (1.3, FY - 0.6)], stride=0.42, z=SZ)
    F.sfx('footsteps_cobble', b2 + 0.4, gain=-14.0, n=4, interval=0.25)
    pool_light(F, T + 1.5, 170, 2.6, 1.5, reach=0.5)
    F.end(b2 + 0.6)


def s5_2(F):
    T = F.begin('5.2', 'What\'s your first name?  Congratulations.')
    Te, Ed, O = F.A['teddy'], F.A['edith'], F.A['oswald']
    F.camera((2.72, 1.92, SZ + 0.82), (2.72, 3.66, SZ + 0.55), 36)
    pool_light(F, T, 210, 3.0, 2.0, reach=1.0)
    seat = (EDITH[0] - 0.45, EDITH[1] + 0.03)
    Te.walk(T + 0.0, T + 1.0, [(1.3, FY - 0.6), (seat[0], FY - 0.55)], stride=0.42, z=SZ)
    Te.turn(T + 1.0, 0.0, dur=0.25)
    Te.place(T + 1.05, seat[0], seat[1], 0.0, z=SZ, dur=0.35)
    Te.posture(T + 1.15, 'sit_wall', dur=0.45, sill=0.0, knees=0.95, back=0.10, hands='knees')
    F.sfx('thump_soft', T + 1.55, gain=-14.0)
    Te.look_at(T + 1.9, ('actor', 'edith', 'eyes'), dur=0.3)
    Te.expr(T + 1.9, brow=0.35, jaw=0.05, smile=0.1, lid_L=1.1, lid_R=1.1, dur=0.3)
    Ed.look_at(T + 1.95, ('actor', 'teddy', 'eyes'), dur=0.5)
    Ed.expr(T + 1.95, smile=0.1, brow=0.1, brow_in=0.0, lid_L=0.95, lid_R=0.95, dur=0.5)
    a, b = F.say('K05', T + 2.35)
    a2, b2 = F.say('E21', b + 0.5)
    a3, b3 = F.say('K06', b2 + 0.45)
    Te.nod(b3 - 0.5, amt=10, dur=0.45, n=1)
    Te.expr(a3, brow=0.2, press=0.2, smile=0.2, dur=0.3)
    a4, b4 = F.say('E22', b3 + 0.4)
    Ed.expr(a4, smile=0.0, brow=0.15, press=0.15, dur=0.2)
    Ed.expr(b4 - 0.3, smile=0.55, smirk=0.3, lidlo_L=0.5, lidlo_R=0.5, press=0.0, dur=0.5)
    Te.expr(b4 - 0.05, smile=1.0, lidlo_L=0.7, lidlo_R=0.7, brow=0.4, jaw=0.15, dur=0.3)
    Te.bounce(b4, dur=0.5, amt=0.006, n=1)
    # Oswald, under the lit lamp, a slow cane twirl for an audience of two
    O.place(T, LAMP[0] + 0.1, LAMP[1] - 0.42, heading_to((LAMP[0] + 0.1, LAMP[1] - 0.42), EDITH), z=0.0, dur=0.01)
    O.posture(T, 'stand', dur=0.01, splay=24, knee=0.2)
    F.attach('cane', T, T + 25, ('fn', cane_twirl(F, T, T + 25, turns=9)))
    O.gesture(T, 'R', ('chest', (-0.32, -0.18, O.B.hipZ + 0.18), (0, -1, -0.25), (-1, 0.2, 0)), dur=0.01)
    O.look_at(T, ('actor', 'edith', 'eyes'), dur=0.01)
    O.expr(T, smile=0.6, brow=0.3, dur=0.01)
    F.end(b4 + 0.5)


def s5_3(F):
    T = F.begin('5.3', 'Return to frame 1: This is Edith Lusk.')
    c = CAM11
    loc = V(*c['loc'])
    tgt = V(*c['target'])
    ed = V(EDITH[0], EDITH[1], SZ + 0.70)
    loc2 = loc + (ed - loc) * 0.15
    tgt2 = tgt.lerp(V(EDITH[0], EDITH[1], SZ + 3.0), 0.35)
    F.camera(tuple(loc), tuple(tgt), c['lens'], loc2=tuple(loc2), target2=tuple(tgt2), t_move=(T + 1.5, T + 8.6))
    a, b = F.say('N12', T + 1.0)
    F.label(a, 8.0 - (a - T), 'EDITH LUSK', '')
    a2, b2 = F.say('N13', b + 0.6)
    a3, b3 = F.say('N14', b2 + 0.8)
    F.cue('final_chord', a3 + 0.1, 6.0, gain=-8.0)
    F.end(b3 + 0.65)
    # black card (not rendered: the encoder fills black)
    F.black = (F.t, F.t + 1.6)
    F.label(F.t, 1.6, 'BRINDLE CROSS', 'A Sunday in November')
    F.sfx('tower_tick', F.t + 0.9, gain=-10.0)
    F.t += 1.6


SHOTS = [s1_1, s1_2, s1_3, s1_4, s1_5, s1_6, s2_1, s2_2, s2_3, s2_4,
         s3_1, s3_2, s3_3, s3_4, s3_5, s3_6, s3_7, s3_8, s3_9, s3_10, s3_11, s3_12, s3_13, s3_14, s3_15,
         s3_16, s3_17, s3_18, s3_19, s3_20, s3_21, s4_1, s4_2, s4_3, s5_1, s5_2, s5_3]


def initial_visibility(F):
    hide = ['ball0', 'ball1', 'ball2', 'coin0', 'coin1', 'coin2', 'held_coat', 'tear', 'rye_main', 'rye_end', 'tray']
    for n in hide:
        F.set_visible(F.props[n], -1, False)
    F.set_visible(F.props['tray'], 0.0, False)
    for p in F.peels:
        F.set_visible(p, -1, False)
    F.set_visible(F.drape, -1, False)
    for o in F.snowline:
        F.set_visible(o, -1, False)


def build(voice_dir, out_dir, only=None):
    F = Film(voice_dir)
    setup_props(F)
    lighting(F)
    initial_visibility(F)
    F.music_stop = None
    F.music_crash = None
    for i, fn in enumerate(SHOTS):
        t_before = F.t
        fn(F)
        # per-scene visibility / time-of-day
        name = F.shots[-1]['name']
        if name == '1.3':
            F.set_visible(F.props['tray'], F.shots[-1]['t0'], True)
            F.set_visible(F.props['tray'], F.shots[-1]['t1'], False)
        if name == '2.2':
            F.set_visible(F.peels[0], F.shots[-1]['t0'], True)
        if name == '2.3':
            F.set_visible(F.peels[1], F.shots[-1]['t0'], True)
        if name == '3.1':
            F.set_visible(F.props['rye'], -1, False)
            F.set_visible(F.props['rye'], F.shots[-1]['t0'], True)
    sh = {s['name']: s for s in F.shots}
    # extras leave after the act
    for n in ('plum', 'flatcap', 'paper'):
        far_away(F, n, sh['3.1']['t0'])
    face_lights(F, sh['3.3']['t0'] - 0.01, sh['4.1']['t0'])
    F.light('key_window2', 'AREA', loc=(1.55, 2.95, SZ + 1.25), target=(2.75, 3.45, SZ + 0.70), energy=30, size=0.9,
            color=(1.0, 0.70, 0.45), t0=sh['4.2']['t0'] - 0.01, t1=sh['4.3']['t0'])
    F.light('key_window3', 'AREA', loc=(1.9, 2.8, SZ + 1.1), target=(2.7, 3.6, SZ + 0.55), energy=26, size=1.2,
            color=(1.0, 0.70, 0.45), t0=sh['5.2']['t0'] - 0.01, t1=sh['5.3']['t0'])
    F.light('fill_front_teddy', 'AREA', loc=(DOOR_X - 1.2, FY - 1.6, SZ + 1.4), target=(DOOR_X, FY - 0.1, SZ + 0.9),
            energy=18, size=1.2, color=(0.8, 0.85, 1.0), t0=sh['1.4']['t0'] - 0.01, t1=sh['1.5']['t0'])
    F.light('fill_front_tomas', 'AREA', loc=(0.3, FY - 1.4, SZ + 1.8), target=(DOOR_X, FY, SZ + 1.4),
            energy=16, size=1.2, color=(0.8, 0.85, 1.0), t0=sh['3.2']['t0'] - 0.01, t1=sh['3.3']['t0'])
    F.light('fill_front_51', 'AREA', loc=(0.0, FY - 1.6, SZ + 1.8), target=(DOOR_X, FY, SZ + 1.3),
            energy=16, size=1.2, color=(0.8, 0.85, 1.0), t0=sh['5.1']['t0'] - 0.01, t1=sh['5.2']['t0'])
    # time of day (sky strength, sun energy)
    time_of_day(F, -1, 0.55, 1.6, 0.01)
    time_of_day(F, sh['2.1']['t0'], 0.50, 1.3, 2.0)
    time_of_day(F, sh['3.1']['t0'], 0.42, 0.9, 3.0)
    time_of_day(F, sh['3.9']['t0'], 0.36, 0.55, 20.0)
    time_of_day(F, sh['4.1']['t0'], 0.30, 0.30, 4.0)
    time_of_day(F, sh['5.1']['t0'], 0.24, 0.12, 2.0)
    # the vamp stops dead on "It's" (3.2)
    for m in F.music:
        if m['name'] == 'vamp' and F.music_stop:
            m['dur'] = F.music_stop - m['t']
            m['params']['cut'] = True
        if m['name'] == 'rag_motif' and F.music_crash:
            m['params']['crash_at'] = F.music_crash - m['t']
    finalize_hat(F, F.hat_plan + [])
    out = F.bake_all(os.path.join(out_dir, 'timeline.json'), os.path.join(out_dir, 'film.blend'))
    print('FILM_DURATION', out['duration'], 'SHOTS', len(out['shots']))
    return F


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:]
    os.makedirs(argv[1], exist_ok=True)
    build(argv[0], argv[1])
