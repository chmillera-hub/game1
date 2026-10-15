"""s07b - Mary at the cross: "From birth I was cast on you; from my mother's womb you have been my God."

Match to s07a: the same face, thirty-three years later. Close on Mary (MARY_OLD, veiled in blue-grey) at the
foot of the cross, looking up at her son with tears, hands clasped at her chin, in the dim cold light of the
darkened afternoon. We look past the wooden upright of the cross (a dark, out-of-focus band in the
foreground); behind her the plateau and a few onlookers dissolve into the red-brown eclipse haze.
Slow push-in. On the second phrase a tear rolls down her cheek.

Her eyes sit at the same screen point and size as young Mary's in the last frames of s07a (FACE_SCREEN), and
the camera sits off her left shoulder at the same angle, so the dissolve reads as a match: head bowed to the
child -> head raised to the cross.
"""
import math
import os
import bpy
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from lib import core as C
from lib import env as E
from lib import characters as P

FACE_Y = 0.30              # eyes at 30 % from the top (same as the end of s07a)
CUT_FRAME_H = 0.78         # frame height (m) at her eyes on frame 1 (= s07a's last frames)
LENS = 135.0
FSTOP = 2.0
CAM_ANGLE = 18.0           # camera off her left shoulder (deg from her facing), as in s07a
STAND = 1.90               # metres in front of the cross
UPRIGHT_OFF = 0.15         # upright centre beside the camera line where it crosses the cross plane


def _mat_tear():
    m = bpy.data.materials.get("s07b_tear")
    if m:
        return m
    m = bpy.data.materials.new("s07b_tear")
    m.use_nodes = True
    m.surface_render_method = "BLENDED"
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.35, 0.3, 0.28, 1)
    b.inputs["Roughness"].default_value = 0.04
    b.inputs["Alpha"].default_value = 0.55
    for k in ("Specular IOR Level", "Specular"):
        if k in b.inputs:
            b.inputs[k].default_value = 1.0
            break
    b.inputs["Coat Weight"].default_value = 1.0
    b.inputs["Coat Roughness"].default_value = 0.02
    return m


def _tear(person, side, f0, f1, steps=13, step=0.0042, name="tear"):
    """A tear on the cheek below eye `side` ('L'/'R'): a thin glossy streak that grows down the evaluated
    skin surface between f0 and f1, with a drop at its tip; parented to the head bone."""
    dg = bpy.context.evaluated_depsgraph_get()
    ob = person.body.evaluated_get(dg)
    me = ob.to_mesh()
    mw = person.body.matrix_world
    verts = [mw @ v.co for v in me.vertices]
    polys = [tuple(p.vertices) for p in me.polygons]
    ob.to_mesh_clear()
    bvh = BVHTree.FromPolygons(verts, polys)
    hm = person.rig.matrix_world @ person.rig.pose.bones["head"].matrix
    R = hm.to_3x3().normalized()
    # head frame from the rest frame: bone Y is up the head; face forward = -Y of the rig carried
    rig3 = person.rig.matrix_world.to_3x3().normalized()
    rb = person.rig.pose.bones["head"]
    carry = R @ rb.bone.matrix_local.to_3x3().normalized().inverted()
    hup = (carry @ Vector((0, 0, 1))).normalized()
    hfw = (carry @ Vector((0, -1, 0))).normalized()
    hlt = (carry @ Vector((1, 0, 0))).normalized()
    e = person.bone_world("eye." + side)
    lat = 1.0 if side == "L" else -1.0
    start = e - hup * 0.017 + hlt * lat * 0.004
    hit = bvh.ray_cast(start + hfw * 0.06, -hfw, 0.2)
    if hit[0] is None:
        return None
    p = hit[0]
    pts = [p + hit[1] * 0.0009]
    grav = Vector((0, 0, -1))
    for i in range(steps):
        loc, nrm, idx, dist = bvh.find_nearest(p)
        g = grav - nrm * grav.dot(nrm)
        # tears hug the cheek: bias the flow a little towards the face's own "down"
        d = (g.normalized() * 0.65 + (-hup - nrm * (-hup).dot(nrm)).normalized() * 0.35 - hlt * lat * 0.08).normalized()
        q = p + d * step
        loc, nrm, idx, dist = bvh.find_nearest(q)
        p = loc
        pts.append(loc + nrm * 0.0009)
    cd = bpy.data.curves.new(name, "CURVE")
    cd.dimensions = "3D"
    cd.bevel_depth = 0.00085
    cd.bevel_resolution = 2
    cd.use_fill_caps = True
    sp = cd.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for i, q in enumerate(pts):
        sp.points[i].co = (q.x, q.y, q.z, 1.0)
        sp.points[i].radius = 1.0 - 0.45 * (i / (len(pts) - 1))
    tob = bpy.data.objects.new(name, cd)
    C.link(tob)
    tob.data.materials.append(_mat_tear())
    tob.visible_shadow = False
    # drop at the tip
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.0019, location=pts[-1])
    drop = bpy.context.active_object
    drop.name = name + "_drop"
    drop.scale = (1.0, 1.0, 1.25)
    drop.data.materials.append(_mat_tear())
    drop.visible_shadow = False
    # grow: bevel_factor_end + the drop riding the tip (keys every 2 frames, linear)
    L = [0.0]
    for i in range(1, len(pts)):
        L.append(L[-1] + (pts[i] - pts[i - 1]).length)

    def at(u):
        s = u * L[-1]
        for i in range(1, len(L)):
            if L[i] >= s:
                t = (s - L[i - 1]) / max(1e-9, L[i] - L[i - 1])
                return pts[i - 1].lerp(pts[i], t)
        return pts[-1]
    f = 1
    nr = bpy.context.scene.frame_end
    while f <= nr:
        u = 0.18 + 0.82 * C.smoothstep((f - f0) / float(max(1, f1 - f0))) ** 0.8
        cd.bevel_factor_end = u
        cd.keyframe_insert("bevel_factor_end", frame=f)
        drop.location = at(u)
        drop.keyframe_insert("location", frame=f)
        f += 2
    for o in (tob, drop):
        mw_ = o.matrix_world.copy()
        o.parent = person.rig
        o.parent_type = "BONE"
        o.parent_bone = "head"
        bpy.context.view_layer.update()
    # parent keeping world transform: set inverse so the keyed world positions stay put
    for o in (tob, drop):
        o.matrix_parent_inverse = (person.rig.matrix_world @ person.rig.pose.bones["head"].matrix
                                   @ Matrix.Translation(Vector((0, person.rig.pose.bones["head"].length, 0)))).inverted()
    return tob, drop


def build(ctx):
    N, NR = ctx.nframes, ctx.render_frames
    p0s, p0e = ctx.phrase_frames(0)
    p1s, p1e = ctx.phrase_frames(1)
    # layout: the cross faces -Y; Mary stands on its -Y side, facing it, looking up at her son. The camera is
    # behind the upright, off her left shoulder, on a long lens: the upright passes through the near foreground.
    # (env.golgotha layout is fixed: centre cross at (0, 0.6) facing -Y; pre-compute the camera cone for culling)
    _a = math.radians(CAM_ANGLE)
    _m = Vector((STAND * math.tan(_a) - UPRIGHT_OFF, 0.6 - STAND, 12.4))
    _c = _m + Vector((-math.sin(_a), math.cos(_a), 0)) * (CUT_FRAME_H / (2 * 18.0 / LENS))
    A = E.golgotha(ctx, mood="eclipse", city=False, grass=0.6, bushes=0.5, rocks=0.8, near_detail=0.6,
                   view={"loc": tuple(_c), "target": tuple(_m), "lens": 30.0})
    cc = A["crosses"]["center"]
    base = Vector(cc["base"])
    front = Vector(cc["front"])
    front.z = 0
    front.normalize()
    head_j = Vector(cc["head"])
    # NB: A["ground_z"] (raycast) returned ~21.5 m here (hits something above the plateau); use the analytic
    # terrain height near the cross instead (the trodden plateau has no big rocks).
    gz = lambda x, y: float(np.asarray(A["ground"](x, y)).reshape(-1)[0])
    fw = -front                                           # Mary faces the cross
    left = Vector((-fw.y, fw.x, 0))                       # her left
    ang = math.radians(CAM_ANGLE)
    cdir = (fw * math.cos(ang) + left * math.sin(ang)).normalized()

    # Mary: STAND m metres in front of the cross; lateral offset solved so the camera line passes the upright
    def mary_at(off):
        q = base + front * STAND + left * off
        q.z = gz(q.x, q.y)
        return q
    # camera line from her eyes along cdir crosses the cross plane after STAND/cos(ang); want the upright centre
    # UPRIGHT_OFF metres to the side of that crossing point
    cross_d = STAND / math.cos(ang)
    off = -(cdir * cross_d).dot(left) + UPRIGHT_OFF
    mp = mary_at(off)
    print("S07B mary ground analytic %.3f raycast %.3f cross base %s" % (mp.z, A["ground_z"](mp.x, mp.y), tuple(base)))
    mary = P.make_person("mary", "MARY_OLD", pose=None)
    mary.rig.location = mp
    mary.rig.rotation_euler.z = math.atan2(fw.x, -fw.y) + math.radians(6)
    mary.update()                          # pose() grounds via rig.matrix_world: it must be current
    P.pose(mary, "mourn", ground_z=mp.z)
    look_pt = head_j + Vector((0, 0, -0.1))
    P.look_at(mary, look_pt, amount=1.0)
    P.expression(mary, "sorrow", frame=1)
    P.expression(mary, {"eyebrows-inner-up": 0.95, "eye-slit": 0.25, "mouth-depression": 0.45,
                        "mouth-compression": 0.1, "nose-elevation": 0.12}, frame=int(p0e))
    # restrained weeping: brows knitted up, lids narrowed, lips pressed with the corners pulled down
    P.expression(mary, {"eyebrows-inner-up": 1.0, "eyebrows-down": 0.12, "eye-slit": 0.35, "nose-elevation": 0.18,
                        "mouth-depression": 0.6, "mouth-compression": 0.3, "neck-platysma": 0.25}, frame=int(p1s + 30))
    P.eyes_look(mary, look_pt, frame=1, up_limit=14)
    P.blink(mary, int(ctx.frame(2.75)), duration=7)
    mary.update()

    # ---------------------------------------------------------------- tears
    bpy.context.scene.frame_set(int(p1s + 30))           # build it on the crying face (cheeks raised)
    mary.update()
    t1 = _tear(mary, "L", int(p1s - 6), int(p1e + 6), name="tear_L")
    bpy.context.scene.frame_set(1)

    # ---------------------------------------------------------------- onlookers behind her (lost in the blur)
    import random
    rnd = random.Random(7)
    perp = Vector((-cdir.y, cdir.x, 0))
    pts = []
    for i in range(9):
        dist = 2.6 + i * 1.25 + rnd.uniform(-0.3, 0.3)
        lat_ = rnd.choice((-1, 1)) * (0.45 + rnd.random() * (0.6 + 0.25 * i))
        q = mp - cdir * dist + perp * lat_
        pts.append((q.x, q.y, gz(q.x, q.y)))
    cr = P.crowd(len(pts), positions=pts, seed=11, variety=3, lod="far", face=tuple(head_j),
                 pose=["mourn", "stand_relaxed", "stand"], yaw_jitter=15, women=0.6)

    # ---------------------------------------------------------------- camera
    eye = mary.eye_pos()
    vh = 2 * math.tan(math.atan(18.0 / LENS))            # frame height per metre of distance
    d0 = CUT_FRAME_H / vh
    d1 = d0 - 0.32

    def cam(f):
        u = C.ease_in_out(min(1.0, ctx.u(f)))
        dist = d0 + (d1 - d0) * u
        loc = eye + cdir * dist + Vector((0, 0, -0.05)) + C.shake(f, 0.0025, 0.3, 3)
        tgt = eye - Vector((0, 0, (0.5 - FACE_Y) * vh * dist)) - Vector((0, 0, 0.05))
        return (loc, tgt, 0.0, LENS, (eye - loc).length)

    # cold sky fill from above the camera side (the darkened afternoon), shadowless; also puts a glint in the tears
    C.light("AREA", tuple(eye + cdir * 1.1 + left * 0.35 + Vector((0, 0, 0.9))), 14.0, temp=9000, target=tuple(eye),
            size=1.4, name="SkyFill", shadow=False)
    bpy.context.scene.eevee.bokeh_max_size = 160.0      # the near upright needs a big blur radius

    camo = C.camera(lens=LENS, fstop=FSTOP, name="Cam")
    dbg = os.environ.get("S07_DEBUG", "")
    if dbg:
        a_, b_, c_ = dbg.split(":")
        camo.location = eye + Vector([float(x) for x in a_.split(",")])
        C.look_at(camo, eye + Vector([float(x) for x in b_.split(",")]))
        camo.data.lens = float(c_)
        camo.data.dof.use_dof = False
    else:
        C.animate_camera(camo, cam, 1, NR)

    ctx.samples = 5
    ctx.render_opts.update({"volumetrics": "low"})
    ctx.interp = True
    ctx.post.update({"grade": "eclipse", "temperature": -0.25, "saturation": 0.8, "vignette": 0.3, "bloom": 0.2,
                     "caption": {"y": 0.70}})
