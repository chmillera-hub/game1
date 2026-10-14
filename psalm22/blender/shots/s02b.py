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


def build(ctx):
    N, NR = ctx.nframes, ctx.render_frames
    sc = bpy.context.scene
    A = E.olive_grove(ctx, moon_az=MOON_AZ, moon_el=MOON_EL)
    gz = A["ground_z"]
    rt = Vector(A["rock_top"])

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
    back = Vector((1, 0, 0))     # pitch axis: his left-right (world X, he faces +Y)
    for f, a in ((1, 0.0), (f_lift, -1.2), (f_sink, 0.3), (NR, 0.0)):
        piv.rotation_euler = (math.radians(a), 0, 0)
        piv.keyframe_insert("rotation_euler", frame=f)

    # ------------------------------------------------------------------ light
    j.update()
    head = Vector(j.head_pos())
    # soft cool "sky" key from the front-left, high (moonlight through a gap in the canopy)
    key = C.light("AREA", loc=(head.x - 1.6, head.y + 2.6, head.z + 2.4), energy=40.0, color=(0.62, 0.74, 1.0),
                  target=tuple(head), size=1.6, name="S02b_key")
    # rim from behind (the moon's direction, a touch stronger on him than the scene's moonlight)

    # ------------------------------------------------------------------ camera: slow lateral dolly
    c0 = Vector((kx + 2.1, ky + 2.25, kz + 1.0))
    c1 = Vector((kx + 1.15, ky + 2.75, kz + 1.0))
    aim = Vector((kx, ky + 0.15, kz + 0.98))

    def cam_path(f):
        u = C.smoothstep(0.08 + 0.84 * (f - 1) / float(NR - 1))
        loc = c0.lerp(c1, (u - C.smoothstep(0.08)) / (C.smoothstep(0.92) - C.smoothstep(0.08)))
        loc = loc + C.shake(f, 0.004, 0.3, 2)
        return (loc, aim, 0.0, 45.0, (loc - head).length)

    cam = C.camera(loc=tuple(c0), target=tuple(aim), lens=45, fstop=2.2, focus=(c0 - head).length)
    C.animate_camera(cam, cam_path, 1, NR)

    ctx.samples = 6
    ctx.render_opts.update({"volumetrics": "low"})
    ctx.interp = True
    ctx.post.update({"grade": ["flashback", "night"], "vignette": 0.3, "bloom": 0.3})
