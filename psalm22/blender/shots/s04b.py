"""s04b - Moses with staff (WIP v1)."""
import math
import os
import random
import bpy
from mathutils import Vector, Matrix
from lib import core as C
from lib import fx as FX
from lib import env as E
from shots import s04a as A4

EV = os.environ.get


def _top_z(objs, x, y, default):
    """Highest surface point of the given mesh objects under (x, y) (object ray casts)."""
    best = None
    for o in objs:
        if o.type != "MESH":
            continue
        mi = o.matrix_world.inverted()
        org = mi @ Vector((x, y, 1000.0))
        d = (mi.to_3x3() @ Vector((0, 0, -1))).normalized()
        ok, loc, nrm, idx = o.ray_cast(org, d)
        if ok:
            z = (o.matrix_world @ loc).z
            best = z if best is None else max(best, z)
    return default if best is None else best


def build(ctx):
    from lib import characters as P
    W, H, L, SL = 34.0, 52.0, 640.0, 130.0
    n = ctx.nframes
    p1a, p1b = ctx.phrase_frames(0)
    p2a, p2b = ctx.phrase_frames(1)
    fc = int(float(EV("FC", str(p1b - 10))))
    sea = FX.red_sea(ctx, width=W, height=H, length=L, shore_slope=SL, lighting=False, spray=True, spray_rate=0.2,
                     collapse=(fc, 70), zipper=(float(EV("ZIP", "-60")), 55.0), seed=5)
    wm = A4.wall_material()
    for w in sea.walls:
        w.data.materials.clear()
        w.data.materials.append(wm)
        for md in w.modifiers:
            if md.type == "NODES":
                FX._mod_set(md, Material=wm)
    sun_az = float(EV("SUNAZ", "4"))
    sun_el = float(EV("SUNEL", "6"))
    E.sky("sunrise", sun_az=sun_az, hdri=EV("HDRI", "qwantani_sunrise_puresky"), ctx=ctx, sun_el=sun_el,
          sun_disk=dict(el=sun_el, size=1.2, color=(1.0, 0.72, 0.42), strength=80.0, glow=0.15))
    y1 = sea.corridor["y"][1]
    fl = sea.floor_at
    # Moses' rock: on the shore just right of the corridor mouth
    rx, ry = float(EV("RX", "9.0")), y1 - float(EV("RY", "6.0"))
    rz = fl(rx, ry)
    rock, robjs = C.ph_model("namaqualand_boulder_03", loc=(rx, ry, rz - 0.6), scale=float(EV("RS", "2.4")))
    bpy.context.view_layer.update()
    top = _top_z(robjs, rx, ry, rz + 2.0)
    print("[s04b] rock top %.2f (ground %.2f)" % (top, rz))
    moses = P.make_person("moses", "MOSES", lod=EV("MLOD", "mid"), pose=None)
    moses.rig.location = (rx, ry, top)
    moses.rig.rotation_euler.z = math.radians(float(EV("MYAW", "-10")))
    P.pose(moses, "staff_raised", ground_z=top)
    cx, cy = float(EV("CX", "12.5")), y1 + float(EV("CY", "6.0"))
    cz = fl(cx, cy) + float(EV("CH", "1.0"))
    lens = float(EV("LENS", "40"))
    cam = C.camera((cx, cy, cz), (rx - 3.0, ry - 120.0, top + 2.0), lens=lens)
    ctx.samples = 6
    ctx.render_opts = {"volumetrics": "low", "raytracing": EV("RT", "1") == "1"}
    ctx.post = {"grade": "flashback"}
