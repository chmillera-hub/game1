"""s06a - Mocking crowd: "All who see me mock me; they hurl insults, shaking their heads."

Cut in from s05 (the camera rising up the cross towards the crucified figure). Reverse angle: his
point of view from the cross, looking steeply down into the crowd packed on the plateau below him.
Religious leaders in rich robes, fine robes and mantles, onlookers in mantles, head cloths and veils
fill the frame; they look up into the lens, sneer, point and laugh, and on "shaking their heads" the
heads shake. Harsh, dim, red-brown light of the darkened sun from behind the cross, dust in the air.
A dozen animated people (fore/mid ground) placed by where their faces fall in the frame, baked
instances fill the gaps and the back. POV camera: slow sinking gaze drifting across the faces, a faint
breathing sway, shallow focus on the chief priest.
"""
import math
import random
import bpy
from mathutils import Vector
from lib import core as C
from lib import env as E
from lib import characters as P

SUN_AZ = 255.0     # low side light from screen right (behind-right of the cross): faces half in shadow
SUN_EL = 28.0
SUN_E = 1.5        # eclipse preset 0.35: harsher, so faces and shadows read (graded dim in comp)
LENS = 50.0
PITCH0, PITCH1 = -34.0, -37.5     # gaze sinks
YAW0, YAW1 = 2.5, -3.0            # and drifts across the crowd (deg, + = screen left)
N_BAKED = 24
SHADOW_RES = 0.01  # sun shadow_maximum_resolution (env sets 2 mm: far too costly with ~20 people close by)


def _hazify_person(p):
    seen = set()
    objs = p.objects() if hasattr(p, "objects") else [p] + list(p.children_recursive)
    for o in objs:
        if o.type not in ("MESH", "CURVES", "CURVE"):
            continue
        for m in getattr(o.data, "materials", []) or []:
            if m is not None and m.name not in seen:
                seen.add(m.name)
                E.hazify(m)


def _preload(p, names):
    """Load the expression units used later so that the first keys include them (at zero)."""
    for n in names:
        P.expression(p, n, 1.0)
    P.expression(p, "neutral", 0.0)


def shrink_textures(skin=1024, other=512):
    """MPFB skin/hair/teeth/eye maps are 2k; at these face sizes 1k/0.5k is plenty (saves ~0.4 GB RAM)."""
    for im in bpy.data.images:
        fp = (im.filepath or "").lower()
        if "mpfb" not in fp and "makehuman" not in fp:
            continue
        try:
            w, h = im.size
            mx = skin if ("skinned" in im.name or "skin" in fp) else other
            if max(w, h) > mx and w > 0:
                im.scale(mx, max(1, int(round(mx * h / w))))
        except Exception as e:
            print("shrink_textures:", im.name, e)


def _cam_dir(pitch_deg, yaw_deg):
    pi, yw = math.radians(pitch_deg), math.radians(yaw_deg)
    return Vector((math.sin(yw) * math.cos(pi), -math.cos(yw) * math.cos(pi), math.sin(pi)))


# (key, preset, spec, screen x (-1..1), screen y of the face (0 top .. 1 bottom), behaviour)
CAST = [
    ("chief", "PRIEST", dict(outfit_colors={"mantle": "purple", "turban": "white_linen"}), 0.3, 0.41, "shake"),
    ("shout", "CROWD_MAN", dict(seed=21, outfit=["tunic", "mantle", "headcloth"], age_years=34, beard_color="brown",
                                outfit_colors={"tunic": "oatmeal", "mantle": "umber", "headcloth": "sand"}),
     -0.55, 0.47, "point"),
    ("lead2", "CROWD_MAN", dict(seed=31, outfit=["robe_rich"], age_years=60, beard="long", build="heavy",
                                outfit_colors={"mantle": "camel", "turban": "oatmeal", "shawl": "linen"}), -0.18, 0.28, "shake"),
    ("woman1", "CROWD_WOMAN", dict(seed=5, outfit_colors={"tunic": "linen", "veil": "madder"}), 0.62, 0.25, "laugh"),
    ("fist", "CROWD_MAN", dict(seed=8, age_years=27, beard="short", beard_color="dark_brown",
                               outfit_colors={"tunic": "brown", "mantle": "charcoal"}), -0.85, 0.20, "fist"),
    ("phar", "CROWD_MAN", dict(seed=44, outfit=["robe", "headcloth"], age_years=50, beard="full", beard_color="grey",
                               outfit_colors={"tunic": "white_linen", "mantle": "blue_grey", "headcloth": "white_linen"}),
     0.2, 0.15, "shake"),
    ("laugh2", "CROWD_MAN", dict(seed=12, beard_color="brown", outfit_colors={"tunic": "sand", "mantle": "olive"}),
     -0.42, 0.10, "laugh"),
    ("woman2", "CROWD_WOMAN", dict(seed=17, outfit_colors={"tunic": "umber", "veil": "oatmeal"}), 0.78, 0.06, "mock"),
]


def build(ctx):
    N, NR = ctx.nframes, ctx.render_frames
    rnd = random.Random(ctx.seed)
    a1, b1 = (int(x) for x in ctx.phrase_frames(0))     # "All who see me mock me;"
    a2, b2 = (int(x) for x in ctx.phrase_frames(1))     # "they hurl insults, shaking their heads."
    sc = bpy.context.scene

    # ------------------------------------------------------------------ set + the eye on the cross
    # centre cross at (0, 0.6) facing -Y, head anchor ~ (0, 0.38, cz + 3.45), hill top cz ~ 11
    view = dict(loc=(0.0, 0.25, 14.4), target=(0.0, -6.0, 10.6), lens=LENS, margin=22)
    A = E.golgotha(ctx, mood="eclipse", sun_az=SUN_AZ, view=view, near_detail=0.4, grass=0.4, bushes=0.0, dust=False,
                   city=False,
                   sky_over=dict(sun_el=SUN_EL, sun_disk=dict(E.SKY_PRESETS["eclipse"]["sun_disk"], el=SUN_EL)))
    gzf = A["ground_z"]
    c = A["crosses"]["center"]
    cz = c["base"][2]
    sun = A["sky"]["sun"]
    sun.data.energy = SUN_E
    sun.data.angle = math.radians(1.8)
    sun.data.shadow_maximum_resolution = SHADOW_RES

    # his eyes: the head anchor of the centre cross (the figure itself is never seen; its shadow falls
    # behind the crowd, out of frame, so it is not built)
    eye = Vector(c["head"]) + Vector((0, 0, -0.06))
    cam0 = eye + Vector((0, -0.12, 0.02))
    dmid = _cam_dir(0.5 * (PITCH0 + PITCH1), 0.5 * (YAW0 + YAW1))
    rgt = dmid.cross(Vector((0, 0, 1))).normalized()
    upv = rgt.cross(dmid).normalized()
    tan_v = 18.0 / LENS
    tan_h = tan_v * 9.0 / 16.0

    def ground_from_screen(sx, sy, h=1.5):
        """World ground point of a person whose eyes (height h) appear at screen (sx, sy)."""
        dr = dmid + rgt * (sx * tan_h) + upv * ((0.5 - sy) * 2 * tan_v)
        z = cz + h
        t = (z - cam0.z) / dr.z
        q = cam0 + dr * t
        return Vector((q.x, q.y, gzf(q.x, q.y)))

    look_pt = cam0.copy()

    # ------------------------------------------------------------------ the mockers (animated)
    built = []
    for i, (key, preset, spec, sx, sy, beh) in enumerate(CAST):
        sp = dict(lod="mid", hair_strands=False)
        sp.update(spec)
        sp["pose"] = None
        sp["expression"] = None
        p = P.make_person("m_" + key, preset, **sp)
        loc = ground_from_screen(sx, sy, h=p.height - 0.12)
        p.rig.location = loc
        yaw = math.atan2(cam0.x - loc.x, -(cam0.y - loc.y)) + math.radians(rnd.uniform(-14, 14))
        p.rig.rotation_euler = (0, 0, yaw)
        p.update()          # key_pose() grounds with rig.matrix_world: it must be current
        built.append((p, sx, sy, beh, i))

    for p, sx, sy, beh, i in built:
        gz = p.rig.location.z
        ph = (i * 0.37) % 1.0
        _preload(p, ["sneer", "mock", "laugh", "anger", "cry_out"])
        stand = "stand_relaxed" if i % 2 else "stand"
        t_look = max(2, a1 - 8 + int(ph * 16))          # they turn up to him on "All who see me"
        if beh in ("point", "fist"):
            lift = Vector((0, 0, 1.4 if beh == "fist" else 0.0))
            P.key_pose(p, 1, stand, ground_z=gz)
            P.key_pose(p, t_look, stand, ground_z=gz)
            fp = t_look + 12
            P.key_pose(p, fp, "point", ground_z=gz, target=tuple(look_pt + lift))
            P.key_pose(p, a2 + 6, "point", ground_z=gz, target=tuple(look_pt + lift + Vector((0.3, 0, 0.9))))
            P.key_pose(p, a2 + 17, "point", ground_z=gz, target=tuple(look_pt + lift))
            P.key_pose(p, a2 + 34, "point", ground_z=gz, target=tuple(look_pt + lift + Vector((-0.2, 0, 0.7))))
            P.key_pose(p, a2 + 45, "point", ground_z=gz, target=tuple(look_pt + lift))
            P.key_pose(p, NR, "point", ground_z=gz, target=tuple(look_pt + lift + Vector((0.1, 0, 0.2))))
            looks = [(1, None), (t_look, None)]
        else:
            P.key_pose(p, 1, stand, ground_z=gz)
            P.key_pose(p, NR, stand, ground_z=gz)
            looks = [(1, None), (t_look, None), (t_look + 11, look_pt), (NR, look_pt)]
        away = look_pt + rgt * (-3.0 if sx < 0 else 3.0) + Vector((0, 0, -2.6))
        for f, tgt in looks:
            sc.frame_set(f)
            P.look_at(p, tuple(tgt if tgt is not None else (away if f == 1 else away.lerp(look_pt, 0.25))), frame=f)
        sc.frame_set(1)
        # faces + behaviour
        P.expression(p, "neutral", frame=1)
        P.expression(p, "neutral", frame=t_look)
        if beh == "shake":
            P.expression(p, "sneer", 0.95, frame=t_look + 12)
            P.head_shake(p, a2 + 2 + int(ph * 10), min(NR - 2, b2 + 6), amount=1.1 + 0.4 * ph, freq=1.3 + 0.5 * ph)
            P.expression(p, "mock", 0.9, frame=a2 + 22)
            P.expression(p, "sneer", 1.0, frame=b2)
        elif beh in ("laugh", "mock"):
            P.laugh(p, t_look + 6, b1 + 20, amount=0.9, freq=2.8 + 0.6 * ph)
            P.expression(p, "mock", 0.95, frame=b1 + 28)
            P.head_shake(p, a2 + 8, min(NR - 2, b2 + 2), amount=0.9, freq=1.6)
        else:   # point / fist: shouting the insults
            P.expression(p, "anger", 0.8, frame=t_look + 12)
            P.expression(p, "cry_out", 0.75, frame=a2 + 4)
            P.expression(p, "anger", 0.9, frame=a2 + 14)
            P.expression(p, "cry_out", 0.65, frame=a2 + 30)
            P.expression(p, "sneer", 0.9, frame=b2 + 2)
        P.blink(p, 26 + int(ph * 70))
        _hazify_person(p)

    # ------------------------------------------------------------------ the crowd around/behind (baked)
    pts = []
    taken = [(p.rig.location.x, p.rig.location.y) for p, *_ in built] + [(c["base"][0], c["base"][1])]
    for k in range(400):
        sx = rnd.uniform(-1.4, 1.4)
        sy = rnd.uniform(-0.75, 0.75)
        if sy > 0.6 and abs(sx) < 0.55:      # keep the lower middle (under the captions) to the cast + ground
            continue
        q = ground_from_screen(sx, sy, 1.5)
        if q.y < -9.8 or q.y > -0.9 or abs(q.x) > 7.5:
            continue
        if any((q.x - a[0]) ** 2 + (q.y - a[1]) ** 2 < 0.62 ** 2 for a in taken + pts):
            continue
        pts.append((q.x, q.y))
        if len(pts) >= N_BAKED:
            break
    look_up = (0.0, -6.0, 3.6)        # relative to a source built at the origin facing -Y
    cposes = [("stand", {"look": look_up}), ("point", {"target": (0.3, -4.0, 4.4)}),
              ("stand_relaxed", {"look": (0.8, -5.0, 3.8)}), ("stand", {"head": "up"}),
              ("point", {"target": (-0.4, -3.0, 4.8)}), ("stand_relaxed", {"look": look_up})]
    cexpr = ["sneer", "anger", "mock", "sneer", "cry_out", "laugh"]

    def cpose(per, i):
        nm, kw = cposes[i % len(cposes)]
        P.pose(per, nm, **kw)
        try:
            P.expression(per, cexpr[i % len(cexpr)], 0.85)
        except Exception as e:
            print("s06a: crowd expression skipped", e)

    cr = P.crowd(len(pts), positions=pts, seed=ctx.seed % 97, variety=4, lod="mid",
                 face=(c["base"][0], c["base"][1] - 1.0, cz), yaw_jitter=16, height_fn=lambda x, y: gzf(x, y),
                 pose_fn=cpose, name="MockCrowd")
    for o in cr.sources:
        _hazify_person(o)
    for inst in cr.instances:
        if (Vector((inst.location.x, inst.location.y)) - Vector((cam0.x, cam0.y))).length > 6.0:
            inst.visible_shadow = False
            for ch in inst.children:
                ch.visible_shadow = False
    # slow weight shifts on the instances (a static crowd reads as a photo)
    for inst in cr.instances:
        z0 = inst.rotation_euler.z
        amp = math.radians(rnd.uniform(1.5, 3.0))
        phs = rnd.uniform(0, 6.28)
        fr = rnd.uniform(0.2, 0.45)
        C.key_fn(inst, "rotation_euler", lambda f, z0=z0, amp=amp, phs=phs, fr=fr:
                 (0, 0, z0 + amp * math.sin(phs + 6.283 * fr * f / 24.0)), 1, NR, step=6)
    try:
        bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
    except Exception as e:
        print("s06a: purge failed", e)
    shrink_textures()
    # the cornea (BLENDED) costs a forward pass per person (~35 % of the frame here); dithered looks the same
    for m in bpy.data.materials:
        if m.surface_render_method == "BLENDED":
            m.surface_render_method = "DITHERED"

    # ------------------------------------------------------------------ camera (his POV)
    chief = built[0][0]
    foc_pt = Vector(chief.head_pos())
    cam = C.camera(loc=tuple(cam0), target=tuple(cam0 + dmid), lens=LENS, fstop=3.5,
                   focus=(foc_pt - cam0).length, clip_end=20000)

    def path(f):
        u = C.ease_in_out(ctx.u(f))
        dvec = _cam_dir(PITCH0 + (PITCH1 - PITCH0) * u, YAW0 + (YAW1 - YAW0) * u)
        breath = 0.01 * math.sin(2 * math.pi * 0.22 * (f - 1) / 24.0)
        loc = cam0 + Vector((0, 0, breath - 0.04 * u)) + C.shake(f, 0.004, 0.35, 7)
        roll = 1.2 * math.sin(2 * math.pi * 0.09 * (f - 1) / 24.0) - 2.5 * u
        return (loc, loc + dvec * 6.0, roll)

    C.animate_camera(cam, path, 1, NR)

    ctx.samples = 4
    ctx.render_opts.update({"volumetrics": "low"})
    ctx.interp = True       # head shakes / laughs / slow POV drift: 12 fps + RIFE is clean (no particles, no flicker)
    ctx.post.update({"grade": "eclipse", "exposure": 0.0, "vignette": 0.26, "caption": {"y": 0.70}})
