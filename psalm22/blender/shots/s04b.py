"""s04b - Moses with staff (WIP v2)."""
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
    W, H, L, SL = 34.0, 52.0, 900.0, 200.0
    n = ctx.nframes
    p1a, p1b = ctx.phrase_frames(0)
    p2a, p2b = ctx.phrase_frames(1)
    fc = int(float(EV("FC", str(p1b - 10))))
    sea = FX.red_sea(ctx, width=W, height=H, length=L, shore_slope=SL, lighting=False, spray=True, spray_rate=0.2,
                     collapse=(fc, 70), zipper=(float(EV("ZIP", "60")), 55.0), seed=5,
                     wall_shadows=EV("WSH", "0") == "1", mist=False, haze=0.0)
    wm = A4.wall_material(spec=float(EV("SPEC", "0.35")))
    for w in sea.walls:
        w.data.materials.clear()
        w.data.materials.append(wm)
        for md in w.modifiers:
            if md.type == "NODES":
                FX._mod_set(md, Material=wm)
    y1 = sea.corridor["y"][1]
    fl = sea.floor_at
    cx, cy = float(EV("CX", "-1.0")), y1 - float(EV("CY", "12.0"))
    cz = fl(cx, cy) + float(EV("CH", "0.6"))
    rx, ry = float(EV("RX", "0.8")), y1 - float(EV("RY", "30.0"))
    rz = fl(rx, ry)
    sun_az = float(EV("SUNAZ", "3"))
    sun_el = float(EV("SUNEL", "8"))
    if EV("MTN", "1") == "1":
        A4.far_mountains(sea.corridor["y"][0], toward=-1.0, height=(120.0, 380.0))
    sky = E.sky("sunrise", sun_az=sun_az, hdri=EV("HDRI", "kloppenheim_06_puresky"), ctx=ctx, sun_el=sun_el,
                strength=float(EV("SKYLIGHT", "0.16")),
                sun_disk=dict(el=sun_el, size=1.2, color=(1.0, 0.72, 0.42), strength=80.0, glow=0.15))
    A4.hazify_sea(sea)
    A4.glow_spray(sea, opacity=float(EV("SPRAYOP", "0.42")), glow=float(EV("SPRAYGLOW", "1.1")))
    E.set_haze(density=float(EV("HAZE", "0.0012")), color=(1.15, 0.98, 0.85))
    # Moses' outcrop: a cliff piece on the slope just left of the corridor mouth + boulders at its foot
    cl = E.rock_protos("cliff", tint=(0.62, 0.55, 0.48), value=0.7)
    proto = cl[int(EV("CLIFF", "1")) % len(cl)]
    hgt = float(EV("RH", "3.2"))
    sc = hgt / max(0.1, proto.dimensions.z)
    sxy = float(EV("RXY", "0.26"))
    rock = E.place(proto, (rx, ry, rz), rot=(0, 0, float(EV("RROT", "30"))), scale=(sc * sxy, sc * sxy, sc),
                   name="moses_rock")
    bpy.context.view_layer.update()
    bb = [rock.matrix_world @ Vector(c) for c in rock.bound_box]
    rock.location.z += rz - 0.4 - min(v.z for v in bb)
    rock.location.x += rx - 0.5 * (min(v.x for v in bb) + max(v.x for v in bb))
    rock.location.y += ry - 0.5 * (min(v.y for v in bb) + max(v.y for v in bb))
    bpy.context.view_layer.update()
    robjs = [rock]
    bp = E.rock_protos("boulders", tint=(0.62, 0.55, 0.48), value=0.7)
    for i, (dx, dy, s_) in enumerate([(-1.9, 0.9, 0.7), (1.7, 1.2, 0.55), (0.3, 2.0, 0.45), (-0.9, -1.6, 0.6)]):
        b_ = E.place(bp[i % len(bp)], (rx + dx, ry + dy, fl(rx + dx, ry + dy) - 0.25), rot=(0, 0, 70 * i), scale=s_)
    top = _top_z(robjs, rx, ry, rz + hgt)
    bb = [rock.matrix_world @ Vector(c) for c in rock.bound_box]
    print("[s04b] rock top %.2f (ground %.2f) cam z %.2f size %.1f x %.1f x %.1f" % (
        top, rz, cz, max(v.x for v in bb) - min(v.x for v in bb), max(v.y for v in bb) - min(v.y for v in bb),
        max(v.z for v in bb) - min(v.z for v in bb)))
    moses = P.make_person("moses", "MOSES", lod=EV("MLOD", "mid"), pose=None)
    moses.rig.location = (rx, ry, top)
    moses.rig.rotation_euler.z = math.radians(float(EV("MYAW", "20")))
    moses.update()
    st = getattr(moses, "staff", None)
    if st is not None:
        st.rotation_mode = "QUATERNION"
    fr0, fr1 = 4, int(p1a + 30)

    def key(frame, name, **kw):
        moses._pose = P.key_pose(moses, frame, name, ground_z=top, **kw)
        if st is not None:
            P.hold_staff(moses, grip=0.40, ground_z=top)
            st.keyframe_insert("location", frame=frame)
            st.keyframe_insert("rotation_quaternion", frame=frame)
    if EV("RAISE", "1") == "1":
        key(fr0, "staff", head="level")
        key(fr1, "staff_raised", reach=1.0)
        key(n + 4, "staff_raised", reach=1.06)
    else:
        P.pose(moses, "staff_raised", ground_z=top)
    if EV("CROWD", "1") == "1":
        cf, sf = A4.walker_protos("far", 0.5, "WKF")
        A4.tint_instances(cf)
        A4.hazify_protos(cf)
        for o in cf.objects:                    # no walker shadows (cost ~2x, invisible against the sun)
            o.visible_shadow = False
        rnd = random.Random(5)
        ppl = []
        fps = ctx.fps
        T = ctx.render_frames / fps
        tries = 0
        while len(ppl) < int(EV("NPPL", "160")) and tries < 5000:
            tries += 1
            yy = rnd.uniform(y1 - 200.0, y1 - 12.0)
            xx = max(-11.0, min(11.0, rnd.gauss(0.0, 5.0)))
            tx = xx * 2.2 + rnd.gauss(0.0, 6.0) - (6.0 if xx > -2.0 else 0.0)
            hd = math.atan2(tx - xx, (y1 + 80.0) - yy)
            v = rnd.randrange(len(A4.VARIANTS))
            sp = sf[v] * fps / A4.WALK_K
            ok = True
            for k in range(0, 9):
                t = T * k / 8.0
                px, py = xx + math.sin(hd) * sp * t, yy + math.cos(hd) * sp * t
                if (px - cx) ** 2 + (py - cy) ** 2 < 3.0 ** 2 or (px - rx) ** 2 + (py - ry) ** 2 < 4.0 ** 2:
                    ok = False
                    break
                if py > y1 - 20.0 and abs(px) > 40.0:
                    ok = False
                    break
            if ok and all((xx - q["x"]) ** 2 + (yy - q["y"]) ** 2 > 0.8 for q in ppl):
                ppl.append(dict(x=xx, y=yy, var=v, dir=hd, scl=rnd.uniform(0.95, 1.05)))
        A4.walker_field("WalkersShore", cf, sf, ppl, sea.seabed)
        print("[s04b] people", len(ppl))
    lens = float(EV("LENS", "65"))
    tgt0 = Vector((cx + float(EV("TX", "3.6")), cy - 100.0, cz + float(EV("TZ", "-3.0"))))
    cam = C.camera((cx, cy, cz), tgt0, lens=lens)
    push = float(EV("PUSH", "1.6"))

    def campath(f):
        u = C.ease_in_out(min(1.0, (f - 1) / max(1, ctx.render_frames - 1)))
        sh = C.shake(f, amp=0.012, freq=0.3, seed=7)
        loc = Vector((cx + 0.35 * u + sh[0], cy - push * u, cz + 0.15 * u + sh[2] * 0.5))
        return loc, tgt0 + Vector((0.0, 0.0, 0.6 * u))
    C.animate_camera(cam, campath, 1, ctx.render_frames)
    ctx.samples = int(EV("SAMPLES", "4"))
    ctx.render_opts = {"volumetrics": "low", "raytracing": EV("RT", "0") == "1"}
    ctx.interp = EV("INTERP", "1") == "1"
    ctx.post = {"grade": ["dawn", "flashback"], "saturation": 0.95, "bloom": 0.42, "vignette": 0.24,
                "caption": {"y": 0.72}}
