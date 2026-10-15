"""s02b - Gethsemane prayer: "...by night, but I find no rest."

Flashback (dissolve in from the s02a night sky). Gethsemane at night: Jesus kneels at the large prayer rock
among the gnarled olive trees, hands clasped on the rock, head bowed. Cold blue moonlight from behind him
rims his hair and shoulders and glows in the drifting mist; a soft cool "sky" key from the front picks out
his bowed face and the clasped hands. A few motes hang in the light. Slow lateral dolly across the front
of the rock (3/4 front, slightly below his eye line). Restlessness: he sways back and lifts his head a little
on a breath, then sinks forward over his hands again.
"""
import math
import bpy
from mathutils import Vector, Matrix
from lib import core as C
from lib import env as E
from lib import characters as P
from lib import wardrobe as W

MOON_AZ, MOON_EL = 20.0, 30.0      # moon behind him (south), backlight + shafts towards the camera
GAP = 0.42                          # knees -> near edge of the rock top (m)


def _hazify_person(p):
    seen = set()
    for o in p.objects():
        if o.type not in ("MESH", "CURVES", "CURVE"):
            continue
        for m in getattr(o.data, "materials", []) or []:
            if m is not None and m.name not in seen:
                seen.add(m.name)
                try:
                    E.hazify(m)
                except Exception:
                    pass



def cull_instancers(names, cam_xy, aim_xy, half_deg, keep_r=6.0):
    """Delete GN-instancer points (env grid trees) outside a horizontal cone around the camera view
    (render-time saver: every tree instance is synced and drawn into the moon's shadow map each frame)."""
    import bmesh
    fwd = (Vector(aim_xy) - Vector(cam_xy)).normalized()
    c = math.cos(math.radians(half_deg))
    n = 0
    for name in names:
        ob = bpy.data.objects.get(name)
        if ob is None or ob.type != "MESH":
            continue
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        mw = ob.matrix_world
        kill = []
        for v in bm.verts:
            p = mw @ v.co
            d = Vector((p.x - cam_xy[0], p.y - cam_xy[1]))
            if d.length > keep_r and d.normalized().dot(fwd) < c:
                kill.append(v)
        bmesh.ops.delete(bm, geom=kill, context="VERTS")
        bm.to_mesh(ob.data)
        bm.free()
        ob.data.update()
        n += len(kill)
    return n


def build(ctx):
    N, NR = ctx.nframes, ctx.render_frames
    sc = bpy.context.scene
    # cull the grove's scatter (far trees, stones, grass) to the camera cone (the rock top is at ~(0, 0.65))
    E.set_view([dict(loc=(3.7, 5.1, 1.35), target=(0.0, 0.5, 0.9), lens=85, margin=22),
                dict(loc=(2.6, 5.7, 1.35), target=(0.0, 0.5, 0.9), lens=85, margin=22)])
    A = E.olive_grove(ctx, moon_az=MOON_AZ, moon_el=MOON_EL, trees=24, motes=False, city_lights=False)
    E.set_view(None)
    # trees behind / far beside the camera: gone (moon shadows from the trees left of frame are kept)
    cull_instancers(["EnvGroveNear", "EnvGroveMid", "EnvGroveFar"], (3.1, 5.4), (0.0, 0.5), 60.0)
    gz = A["ground_z"]
    # the env's prayer rock (2.6 x 1.6 m) hides a kneeling man from any front camera: scale it to a
    # waist-high boulder (~1.45 x 1.0 m) he can lean on. It is rotated 90 deg: local X = world Y.
    rock = A["rock"]
    rock.scale = (rock.scale.x * 0.62, rock.scale.y * 0.55, rock.scale.z * 0.92)
    bpy.context.view_layer.update()
    E.release_bvh()
    rc = Vector(A["rock_top_center"])
    edge = None
    for k in range(80):
        y = rc.y - 0.9 + k * 0.02
        z, _ = E.ground_hit(rc.x, y, [rock])
        if z is not None and z > A["ground"](rc.x, y - 0.6) + 0.5:
            edge = Vector((rc.x, y, z))
            break
    rt = edge if edge is not None else Vector(A["rock_top"])
    print("s02b rock edge", tuple(rt))

    # ------------------------------------------------------------------ Jesus at the rock
    j = P.make_person("jesus", "JESUS_ROBED", pose=None)
    kx, ky = rt.x, rt.y - GAP
    kz = gz(kx, ky)
    # pivot at the knees' ground line so he can sway back on his heels without the knees sliding
    piv = bpy.data.objects.new("S02b_sway", None)
    C.link(piv)
    piv.location = (kx, ky + 0.12, kz)
    j.rig.location = (kx, ky, kz)
    j.rig.rotation_euler.z = math.pi
    j.update()
    hands = (rt.x, rt.y + 0.06, rt.z + 0.03)
    P.pose(j, "kneel_pray", rock=hands)
    try:
        W.drape(j, j.garments, frames=30, ramp=20)
    except Exception as e:
        print("s02b WARNING: drape failed:", e)
    # restless: bowed -> a breath, head lifts a little and he sways back -> sinks forward again
    f_lift = int(round(ctx.frame(0.95)))
    f_sink = int(round(ctx.frame(2.35)))
    P.key_pose(j, 1, "kneel_pray", rock=hands, head="bowed")
    P.key_pose(j, f_lift, "kneel_pray", rock=hands, head="down")
    P.key_pose(j, f_sink, "kneel_pray", rock=hands, head="bowed")
    P.key_pose(j, NR, "kneel_pray", rock=hands, head="bowed")
    P.expression(j, "sorrow", frame=1)
    P.expression(j, "anguish", weight=0.55, frame=f_lift)
    P.expression(j, "sorrow", frame=f_sink + 10)
    _hazify_person(j)
    # sway: parent the rig to the knee pivot, pitch back ~1 deg with the breath
    mw = j.rig.matrix_world.copy()
    j.rig.parent = piv
    j.rig.matrix_parent_inverse = piv.matrix_world.inverted()
    j.rig.matrix_world = mw
    # + about world X tips the top towards -Y = backwards (he faces +Y)
    for f, a in ((1, 0.0), (f_lift, 1.2), (f_sink, -0.3), (NR, 0.0)):
        piv.rotation_euler = (math.radians(a), 0, 0)
        piv.keyframe_insert("rotation_euler", frame=f)

    # ------------------------------------------------------------------ light
    j.update()
    head = Vector(j.head_pos())
    # soft cool "sky" key from the front-left, high (moonlight through a gap in the canopy): face, hands, rock top
    key = C.light("SPOT", loc=(head.x - 1.7, head.y + 2.4, head.z + 2.6), energy=26.0, color=(0.62, 0.74, 1.0),
                  target=(head.x, head.y + 0.1, head.z - 0.05), size=0.5, spot_size=26, spot_blend=0.8,
                  name="S02b_key", volume=0.0)
    # moon rim from behind (same direction as the scene's moon): hair, shoulders, the edge of the mantle
    md = E._dir_from_az_el(MOON_AZ, MOON_EL + 6.0)
    rim = C.light("SPOT", loc=tuple(head + md * 4.5), energy=1100.0, color=(0.7, 0.8, 1.0),
                  target=tuple(head + Vector((0, 0, -0.12))),
                  size=0.25, spot_size=12, spot_blend=0.7, name="S02b_rim", volume=0.0, shadow=False)
    # a shaft of moonlight falling through the branches into the mist behind him (seen against the dark grove)
    sh_tgt = Vector((kx - 3.6, ky - 5.2, kz))
    shaft = C.light("SPOT", loc=tuple(sh_tgt + E._dir_from_az_el(MOON_AZ + 15.0, 58.0) * 11.0), energy=4000.0,
                    color=(0.62, 0.74, 1.0), target=tuple(sh_tgt), size=0.3, spot_size=20, spot_blend=1.0,
                    name="S02b_shaft", volume=1.0, shadow=False)

    # a few motes hanging in the moonlight behind him (env motes would drift right in front of the long lens)
    E.dust_motes(center=(kx - 0.3, ky - 1.9, kz + 1.3), size=(3.6, 2.6, 1.8), count=45, radius=0.003,
                 color=(0.75, 0.85, 1.0), emission=0.5, drift=(0.04, 0.015, 0.01), turbulence=0.15, seed=7,
                 name="S02b_motes")

    # ------------------------------------------------------------------ camera: slow lateral dolly
    # long lens from ~6 m: the rock sits with him instead of swelling in the foreground; the grove compresses
    # behind him. Lateral dolly from 38 to 26 deg off his facing (towards his front), level with his eyes.
    D, TH0, TH1 = 6.0, 38.0, 26.0
    hb = Vector((kx, ky + 0.1, 0.0))
    c0 = hb + Vector((math.sin(math.radians(TH0)), math.cos(math.radians(TH0)), 0)) * D
    c1 = hb + Vector((math.sin(math.radians(TH1)), math.cos(math.radians(TH1)), 0)) * D
    c0.z = c1.z = kz + 1.35
    aim = Vector((kx, ky + 0.35, kz + 0.92))

    def cam_path(f):
        u = C.smoothstep(0.08 + 0.84 * (f - 1) / float(NR - 1))
        loc = c0.lerp(c1, (u - C.smoothstep(0.08)) / (C.smoothstep(0.92) - C.smoothstep(0.08)))
        loc = loc + C.shake(f, 0.004, 0.3, 2)
        return (loc, aim, 0.0, 85.0, (loc - head).length)

    cam = C.camera(loc=tuple(c0), target=tuple(aim), lens=85, fstop=2.8, focus=(c0 - head).length)
    C.animate_camera(cam, cam_path, 1, NR)

    ctx.samples = 5
    ctx.render_opts.update({"volumetrics": "low", "vol_shadows": False})
    ctx.interp = True
    ctx.post.update({"grade": ["flashback", "night"], "vignette": 0.3, "bloom": 0.3})
