"""s16a - Praise him: "You who fear the Lord, praise him! / All you descendants of Jacob, honor him! /
Revere him, all you descendants of Israel!"

Sunrise on a grassy ridge. We look up the slope into a blazing low sun; people stand on the crest and on
the slope below it as dark, rim-lit silhouettes (backs to us, facing the sun). The action builds with the
narration: phrase 1 - the two nearest figures lift their hands; phrase 2 - the people along the crest
join, a wave of raised arms; phrase 3 ("Revere him") - the elder in the middle sinks to his knees and
bows, uncovering the sun behind him. The camera cranes slowly up and forward towards the sun.
Silhouettes only: no faces are seen (mid LOD people, crowd-detail clothing).
"""
import math
import random
import numpy as np
import bpy
from mathutils import Vector
from lib import core as C
from lib import env as E
from lib import characters as P

SUN_AZ = 180.0                       # sun straight ahead (+Y)
CREST_Y = 20.0


def _H(X, Y):
    """Ridge: gentle rise from the camera (y ~ 0) to an undulating crest at y ~ 20, falling away beyond;
    rolling hills far out."""
    X = np.asarray(X, float)
    Y = np.asarray(Y, float)
    crest = CREST_Y + 1.2 * E.fbm(X / 30.0, 0.0 * X, 2, seed=5)
    up = 3.2 * E.smoothstep(-10.0, crest, Y)
    down = -22.0 * E.smoothstep(crest, crest + 70.0, Y) ** 1.4
    h = up + down
    h += 0.35 * E.fbm(X * 0.08, Y * 0.08, 3, seed=7) * E.smoothstep(crest + 2, crest - 6, Y)
    h += 0.06 * E.fbm(X * 0.5, Y * 0.5, 2, seed=9)
    r = np.sqrt(X ** 2 + (Y - 20.0) ** 2)
    h += E.smoothstep(600.0, 2600.0, r) * (60.0 + 80.0 * E.fbm(X / 900.0, Y / 900.0, 3, seed=11))
    return h


def _gz(x, y):
    return float(_H(np.array([x]), np.array([y]))[0])


def _hz_person(p):
    for o in p.objects():
        for ms in getattr(getattr(o, "data", None), "materials", []) or []:
            if ms is not None:
                E.hazify(ms)


def _hide_face(p):
    """Seen from behind against the sun: eyes / brows / lashes / teeth / tongue / mouth never show."""
    for k in ("eyes", "eyebrows", "eyelashes", "teeth", "tongue", "mouth"):
        o = p.parts.get(k)
        if o is not None:
            o.hide_render = True


def build(ctx):
    N, R = ctx.nframes, ctx.render_frames
    f1a, f1b = ctx.phrase_frames(0)
    f2a, f2b = ctx.phrase_frames(1)
    f3a, f3b = ctx.phrase_frames(2)

    # ---------------- sky + ground ----------------
    p = E.sky_preset("sunrise", sun_az=SUN_AZ, strength=0.4, sat=1.45, tint=(1.0, 0.84, 0.66))
    sk = E.sky(cfg=p, ctx=ctx)
    sun = sk["sun"]
    gm = E.ground_material("S16Ground", style="plain")
    E.terrain_grid("S16Ridge", _H, center=(0, 12), core=70, cell=0.35, extent=4000, growth=1.08, mat_=gm,
                   attrs_fn=lambda X, Y, Z: dict(rock=np.clip((E.fbm(X * 0.06, Y * 0.06, 3, seed=81) - 0.35) * 2, 0, 1) * 0.5,
                                                 path=np.zeros_like(Z), cav=np.zeros_like(Z), dust=np.zeros_like(Z)))
    gr = E.grass_protos("dry", height=0.45) + E.grass_protos("green", height=0.35)
    # crest grass (silhouetted against the sun) + slope grass + dark foreground tufts
    E.scatter(gr, count=3200, seed=4, scale=(0.7, 1.5), align=0.6, sink=0.02, region=(-9, 15, 9, 26),
              name="S16GrassCrest", realize=False, shadows=False)
    E.scatter(gr, count=3000, seed=5, scale=(0.6, 1.3), align=0.6, sink=0.02, region=(-7, -1, 7, 15),
              name="S16GrassSlope", realize=False, shadows=False)
    E.scatter(E.rock_protos("rocks"), count=120, seed=8, scale=(0.4, 1.2), align=0.9, sink=-0.3,
              region=(-8, 0, 8, 24), name="S16Rocks", realize=False, shadows=False)
    sh = [E.shrub_blob(seed=i, size=1.0 + 0.3 * i) for i in range(3)]
    E.scatter(sh, count=160, seed=6, scale=(0.8, 1.6), align=0.3, sink=0.05, region=("ring", 0, 20, 40, 400),
              name="S16Shrubs", realize=False, shadows=False)

    # ---------------- people ----------------
    P.AUTO_DRAPE = False
    rnd = random.Random(16)
    people = []

    def person(name, preset, seed, x, y, colors, **spec):
        pr = P.make_person(name, preset, seed=seed, lod="mid", pose=None, hair_strands=False,
                           outfit_colors=colors, **spec)
        z = _gz(x, y)
        pr.rig.location = (x, y, z)
        pr.rig.rotation_euler.z = math.radians(180 + rnd.uniform(-8, 8))
        _hz_person(pr)
        _hide_face(pr)
        people.append(pr)
        return pr, z

    def raise_arms(pr, z, fa, dur=26, spread=35, head="up", start="stand_relaxed", hold_head="down"):
        P.key_pose(pr, 1, start, ground_z=z, head=hold_head)
        P.key_pose(pr, max(2, fa), start, ground_z=z, head=hold_head)
        P.key_pose(pr, fa + int(dur * 0.55), "arms_raised", ground_z=z, spread=spread * 0.6, head=head)
        P.key_pose(pr, fa + dur, "arms_raised", ground_z=z, spread=spread, head=head)

    # near pair (phrase 1)
    a, za = person("s16_near_m", "CROWD_MAN", 3, -0.75, 6.4, {"tunic": "oatmeal", "mantle": "brown"},
                   age_years=34, height_cm=176, build="average", beard="full", hair="short02")
    raise_arms(a, za, f1a + 2, dur=30, spread=30)
    b, zb = person("s16_near_w", "CROWD_WOMAN", 5, 0.8, 7.6, {"tunic": "umber", "veil": "sand"},
                   age_years=30, height_cm=160)
    raise_arms(b, zb, f1a + 14, dur=30, spread=40)
    # elder in the middle distance: hands raised already on phrase 1-2, kneels + bows on phrase 3
    e, ze = person("s16_elder", "CROWD_MAN", 11, -0.45, 12.0, {"tunic": "linen", "mantle": "camel"},
                   age_years=66, height_cm=170, build="lean", beard="long", outfit=["tunic"],
                   outfit_opts={"tunic": {"length": "below_knee", "sleeves": "long"}})
    raise_arms(e, ze, f1b - 6, dur=34, spread=28)
    P.key_pose(e, f3a + 4, "arms_raised", ground_z=ze, spread=26, head="up")
    P.key_pose(e, f3a + 30, "kneel", ground_z=ze, head="up")
    P.key_pose(e, f3a + 52, "kneel_bow", ground_z=ze)
    P.key_pose(e, R, "kneel_bow", ground_z=ze)

    # crest: sources + clones, a wave of raised hands on phrase 2
    srcs = []
    for k, (pre, sd, cols, extra) in enumerate((
            ("CROWD_MAN", 21, {"tunic": "linen", "mantle": "dark_brown"}, {}),
            ("CROWD_WOMAN", 22, {"tunic": "sand", "veil": "oatmeal"}, {}),
            ("CROWD_MAN", 23, {"tunic": "brown", "mantle": "umber"}, dict(age_years=24)),
            ("CHILD", 24, {"tunic": "oatmeal"}, dict(lod="mid", hair_strands=False)))):
        x, y = (-2.2, -0.4, 1.6, 3.2)[k], CREST_Y + (0.4, -0.3, 0.2, -0.5)[k]
        if pre == "CHILD":
            pr = P.make_person("s16_crest%d" % k, "CHILD", lod="mid", pose=None, hair_strands=False, outfit_colors=cols,
                               expression="neutral")
            z = _gz(x, y)
            pr.rig.location = (x, y, z)
            pr.rig.rotation_euler.z = math.radians(176)
            _hz_person(pr)
            _hide_face(pr)
        else:
            pr, z = person("s16_crest%d" % k, pre, sd, x, y, cols, **extra)
        fa = f2a + 4 + k * 14
        raise_arms(pr, z, fa, dur=30, spread=30 + 6 * k)
        srcs.append((pr, z, fa))
    # clones further along the crest (same body / outfit, other places, offset timing)
    for k, (x, dy, src, off) in enumerate(((-3.8, 0.8, 0, 26), (0.7, 0.9, 2, -20), (-1.3, 1.6, 1, 34),
                                           (4.6, 0.6, 1, 8), (2.6, 1.4, 0, 46))):
        pr, z0, fa0 = srcs[src]
        y = CREST_Y + dy
        z = _gz(x, y)
        c = P.clone(pr, loc=(x, y, z + (pr.rig.location.z - z0) * 0.0), yaw=math.radians(180 + rnd.uniform(-10, 10)),
                    name="s16_cl%d" % k, action_offset=off)
        people.append(c)

    # ---------------- light ----------------
    # rim lights: from behind the people towards the camera, a little off the sun axis (left / right)
    for k, (x, y, z, en) in enumerate(((-3.2, 15.0, 4.2, 420.0), (3.4, 15.5, 3.8, 360.0))):
        lo = C.light("AREA", loc=(x, y, z), energy=en, color=C.kelvin(2500), target=(x * -0.1, 4.0, 2.4),
                     size=3.0, name="s16_rim%d" % k, shadow=False)
        lo.data.volume_factor = 0.0
    # faint cool front fill so the silhouettes keep a hint of form (bounce from the western sky)
    ff = C.light("AREA", loc=(0, -6, 4), energy=40.0, color=C.kelvin(8000), target=(0, 10, 1.5), size=8.0,
                 name="s16_fill")
    ff.data.use_shadow = False
    ff.data.volume_factor = 0.0

    # ---------------- camera ----------------
    z0 = _gz(0.0, 0.0)
    cam = C.camera((0.3, 0.0, z0 + 1.0), (0.0, 30.0, 2.4), lens=50, fstop=5.6, focus=12.0)

    def cfn(f):
        u = C.ease_in_out(min(1.0, max(0.0, (f - 1) / (R - 1))))
        loc = Vector((0.3 - 0.25 * u, 0.0 + 2.2 * u, z0 + 1.0 + 1.05 * u))
        loc.z += 0.01 * math.sin(f * 0.05)
        tgt = Vector((0.0, 30.0, loc.z + 30.0 * math.tan(math.radians(3.6 - 0.8 * u))))
        return loc, tgt, 0.0, None, (12.5 - loc.y) * 0.0 + 12.0 - 2.2 * u
    C.animate_camera(cam, cfn, 1, R, step=2)
    cam.data.dof.focus_distance = 12.0

    ctx.samples = 4
    ctx.render_opts = {"volumetrics": "low"}
    ctx.interp = True
    ctx.post = {"grade": "warm", "bloom": 0.42, "bloom_radius": 1.4, "halation": 0.1, "vignette": 0.22,
                "contrast": 1.05, "caption": {"ink": "light", "halo": 1.2}}
