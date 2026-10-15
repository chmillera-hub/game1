"""s13a - They stare: "All my bones are on display; people stare and gloat over me."

Hard cut in from s12b (the hammer and the nail). From behind the crowd on the plateau, at eye level:
the backs of heads and shoulders of onlookers - veils, head cloths, mantles - are dark, soft-focus
silhouettes in the foreground, all turned up towards the centre cross in the dim red-brown eclipse
light. Between them, sharp, in the middle distance: the crucified figure, a partial silhouette rimmed by
the dull sun behind the cross, body exposed on the beam ("all my bones are on display").
A slow, breathing push-in between the heads.
On "people stare and gloat over me" a man standing just in front of us, arms crossed, turns his head
into profile towards his neighbour with a satisfied smirk; focus racks from the cross to his face.
"""
import math
import os
import random
import bpy
from mathutils import Vector
from lib import core as C
from lib import env as E
from lib import characters as P

SUN_AZ = 172.0       # from behind the crosses (backlight): onlookers' backs and the figure's front in shadow
SUN_EL = 22.0
LENS = 55.0


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


# ------------------------------------------------------------------ arms crossed (custom pose)
def _pose_arms_crossed(Pz, p, head="level", turn=0.0, **k):
    """Standing with the weight on one leg, arms folded across the chest (right forearm in front)."""
    P._pose_stand(Pz, p, relaxed=True, head=head, turn=turn)
    h = p.height / 1.75
    sh = (Pz.head("upperarm01.L") + Pz.head("upperarm01.R")) * 0.5
    # right palm on the left upper arm, left hand tucked under the right upper arm
    tr = sh + Vector((0.135 * h, -0.115 * h, -0.215 * h))
    tl = sh + Vector((-0.125 * h, -0.075 * h, -0.255 * h))
    P._arm_ik(Pz, "R", tr, pole=Vector((-1.0, -0.15, -0.6)).normalized(), pron=95, flex=8, shrug=3)
    P._hand(Pz, "R", "cup")
    P._arm_ik(Pz, "L", tl, pole=Vector((1.0, -0.1, -0.7)).normalized(), pron=80, flex=-6, shrug=2)
    P._hand(Pz, "L", "relaxed")


P.POSES["s13a_arms_crossed"] = _pose_arms_crossed
P.GROUNDED.add("s13a_arms_crossed")

SMIRK = {"nose-left-elevation": 0.32, "mouth-corner-puller": 0.5, "mouth-upward-retraction": 0.12,
         "eye-slit": 0.38, "eyebrows-left-up": 0.32, "eyebrows-down": 0.12, "mouth-compression": 0.15}


def build(ctx):
    N, NR = ctx.nframes, ctx.render_frames
    rnd = random.Random(ctx.seed)
    a1, b1 = (int(x) for x in ctx.phrase_frames(0))     # "All my bones are on display;"
    a2, b2 = (int(x) for x in ctx.phrase_frames(1))     # "people stare and gloat over me."
    sc = bpy.context.scene

    # ------------------------------------------------------------------ set
    cam_xy = Vector((-0.25, -8.7))
    view = dict(loc=(cam_xy.x, cam_xy.y, 11.0), target=(0.0, 0.6, 13.5), lens=LENS, margin=14)
    disk = dict(E.SKY_PRESETS["eclipse"]["sun_disk"], el=SUN_EL)
    A = E.golgotha(ctx, mood="eclipse", sun_az=SUN_AZ, view=view, near_detail=0.3, grass=0.5, bushes=0.5,
                   dust=False, sky_over=dict(sun_el=SUN_EL, sun_disk=disk))
    gzf = A["ground_z"]
    c = A["crosses"]["center"]
    cz = c["base"][2]
    gcam = gzf(cam_xy.x, cam_xy.y)
    print("S13A cross base", c["base"], "cam ground", gcam)

    # the crucified: mid-distance, rim-lit silhouette
    j = P.make_person("jesus", "JESUS_CROSS", pose=None, lod="mid", hair_strands=False)
    P.place_on_cross(j, c["root"], head="side", strain=0.75)
    P.expression(j, "exhausted")
    _hazify_person(j)
    fig = Vector(c["chest"]) + Vector((0, -0.05, 0.1))

    # ------------------------------------------------------------------ the gloater (arms crossed, turns to profile)
    AX = (Vector(c["base"][:2]) - cam_xy).normalized()      # camera axis (ground plane)
    RT = Vector((AX.y, -AX.x))                                  # screen right

    def rel(d, x):
        q = cam_xy + AX * d + RT * x
        return Vector((q.x, q.y))

    G = rel(2.1, 0.3)
    gl = P.make_person("gloater", "CROWD_MAN", seed=52, lod="hero", pose=None, expression=None, age_years=46,
                       beard="short", build="heavy", outfit=["tunic", "mantle", "headcloth"],
                       outfit_colors={"tunic": "umber", "mantle": "dark_brown", "headcloth": "oatmeal"})
    gz = gzf(G.x, G.y)
    gl.rig.location = (G.x, G.y, gz)
    face_dir = (Vector(c["base"][:2]) - G).normalized()
    gl.rig.rotation_euler = (0, 0, math.atan2(face_dir.x, -face_dir.y) + math.radians(8))
    gl.update()        # key_pose(ground_z=...) reads rig.matrix_world: refresh it after moving the rig
    up_look = Vector(c["head"]) + Vector((0, 0, -0.2))
    nb2 = rel(1.75, -0.7)
    neigh = Vector((nb2.x, nb2.y, gz + 1.5))                 # his neighbour, to his right and a little behind
    t_turn = a2 + 4
    P.key_pose(gl, 1, "s13a_arms_crossed", ground_z=gz)
    P.key_pose(gl, NR, "s13a_arms_crossed", ground_z=gz)
    for f, tgt in ((1, up_look), (t_turn - 2, up_look), (t_turn + 14, neigh), (b2 - 2, neigh + Vector((0.2, 0, 0.05))),
                   (NR, neigh + Vector((0.35, 0.2, 0.1)))):
        sc.frame_set(f)
        P.look_at(gl, tuple(tgt), frame=f)
    sc.frame_set(1)
    P.expression(gl, SMIRK, 1.0)                 # load the units first so the neutral keys include them
    P.expression(gl, "neutral", frame=1)
    P.expression(gl, "neutral", frame=t_turn)
    P.expression(gl, SMIRK, 1.0, frame=t_turn + 12)
    P.expression(gl, SMIRK, 1.15, frame=b2 + 4)
    P.nod(gl, t_turn + 18, min(NR - 2, t_turn + 44), amount=0.45, freq=1.4)
    P.blink(gl, a1 + 6)
    P.blink(gl, t_turn + 30)
    _hazify_person(gl)

    # ------------------------------------------------------------------ foreground backs (soft focus)
    fg = []
    FG = [  # (name, preset, seed, (d, x) along/across the camera axis, colours, outfit, look offset)
        ("fgL", "CROWD_WOMAN", 9, (0.85, -0.24), {"tunic": "umber", "veil": "charcoal"}, None, (-0.3, 0, 0)),
        ("fgR", "CROWD_MAN", 33, (1.05, 0.27), {"tunic": "sand", "mantle": "black_wool", "headcloth": "camel"},
         ["tunic", "mantle", "headcloth"], (0.4, 0, 0.3)),
        ("fgC", "CROWD_MAN", 71, (1.6, -0.14), {"tunic": "brown", "mantle": "umber", "headcloth": "linen"},
         ["tunic", "mantle", "headcloth"], (0.1, 0, 0)),
        ("midL", "CROWD_WOMAN", 21, (3.1, -0.45), {"tunic": "linen", "veil": "indigo"}, None, (-0.2, 0, 0)),
        ("midR", "CROWD_MAN", 14, (3.5, 0.5), {"tunic": "oatmeal", "mantle": "rust", "headcloth": "sand"},
         ["tunic", "mantle", "headcloth"], (0.3, 0, 0.2)),
    ]
    FG = [(a, b_, c_, tuple(rel(*d)), e, f_, g) for a, b_, c_, d, e, f_, g in FG]
    for i, (nm, pre, sd, xy, cols, outfit, lo) in enumerate(FG):
        sp = dict(lod="mid", hair_strands=False, pose=None, expression=None, seed=sd, outfit_colors=cols)
        if outfit:
            sp["outfit"] = outfit
        p = P.make_person(nm, pre, **sp)
        z = gzf(xy[0], xy[1])
        p.rig.location = (xy[0], xy[1], z)
        d = (Vector(c["base"][:2]) - Vector(xy)).normalized()
        p.rig.rotation_euler = (0, 0, math.atan2(d.x, -d.y) + math.radians(rnd.uniform(-10, 10)))
        p.update()
        tgt = Vector(c["head"]) + Vector(lo) + Vector((0, 0, -0.4))
        stand = "stand" if i % 2 else "stand_relaxed"
        if nm == "midR":       # one of them shakes his head slowly in disgust on the second line (stays live)
            P.key_pose(p, 1, stand, ground_z=z, look=tuple(tgt))
            P.key_pose(p, NR, stand, ground_z=z, look=tuple(tgt + Vector((0.2, 0, -0.1))))
            P.head_shake(p, a2 + 6, min(NR - 2, b2 + 4), amount=0.6, freq=0.9)
            _hazify_person(p)
            fg.append(p)
            continue
        # static onlookers: bake (no per-frame skinning), then a slow weight-shift sway of the whole body
        P.pose(p, stand, ground_z=z, look=tuple(tgt))
        _hazify_person(p)
        b = P.bake_static(p, name=nm + "_baked")
        z0 = b.rotation_euler.z
        amp = math.radians(rnd.uniform(0.6, 1.2))
        ph_ = rnd.uniform(0, 6.28)
        C.key_fn(b, "rotation_euler", lambda f, z0=z0, amp=amp, ph_=ph_:
                 (amp * 0.5 * math.sin(ph_ + 6.283 * 0.17 * f / 24.0), amp * math.sin(ph_ + 1.3 + 6.283 * 0.13 * f / 24.0),
                  z0 + amp * 1.5 * math.sin(ph_ + 6.283 * 0.09 * f / 24.0)), 1, NR, step=4)
        fg.append(b)

    # ------------------------------------------------------------------ the crowd between us and the cross (baked)
    pts = []
    taken = [(G.x, G.y)] + [tuple(x[3]) for x in FG]
    for k in range(900):
        d = rnd.uniform(3.6, 8.2)
        x = rnd.uniform(-2.6, 2.6) * (0.5 + d / 8.0)
        if abs(x) < 0.4 + 0.05 * d and d < 7.0:     # keep a gap to the figure between the heads
            continue
        q = rel(d, x)
        if any((q.x - a) ** 2 + (q.y - b) ** 2 < 0.62 ** 2 for a, b in taken + pts):
            continue
        pts.append((q.x, q.y))
        if len(pts) >= 18:
            break
    look_up = (0.0, -6.0, 3.5)
    cposes = [("stand", {"look": look_up}), ("stand_relaxed", {"look": (0.5, -5.0, 3.8)}), ("mourn", {}),
              ("stand", {"head": "up"}), ("stand_relaxed", {"look": (-0.6, -5.5, 3.6)})]

    def cpose(per, i):
        nm, kw = cposes[i % len(cposes)]
        P.pose(per, nm, **kw)

    cr = P.crowd(len(pts), positions=pts, seed=ctx.seed % 89, variety=5, lod="mid",
                 face=(c["base"][0], c["base"][1], cz), yaw_jitter=14, height_fn=lambda x, y: gzf(x, y),
                 pose_fn=cpose, name="StareCrowd")
    for o in cr.sources:
        _hazify_person(o)
    try:
        bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
    except Exception as e:
        print("s13a: purge failed", e)

    # ------------------------------------------------------------------ camera: slow breathing push between the heads
    cam0 = Vector((cam_xy.x, cam_xy.y, gcam + 1.58))
    cam1 = cam0 + Vector((AX.x, AX.y, 0)) * 0.25 + Vector((0, 0, 0.03))
    tgt = Vector(c["feet"]) + Vector((0, 0, 0.45))
    gface = Vector(gl.head_pos())
    cam = C.camera(loc=tuple(cam0), target=tuple(tgt), lens=LENS, fstop=2.8, focus=(fig - cam0).length)
    f_r0, f_r1 = t_turn + 4, t_turn + 26

    def path(f):
        u = C.ease_in_out(ctx.u(f))
        loc = cam0.lerp(cam1, u) + C.shake(f, 0.006, 0.45, 5)
        loc.z += 0.004 * math.sin(2 * math.pi * 0.21 * (f - 1) / 24.0)
        r = C.smootherstep(min(1.0, max(0.0, (f - f_r0) / (f_r1 - f_r0))))
        fd = (fig - loc).length * (1 - r) + (gface - loc).length * r
        tg = tgt + Vector((0.0, 0.0, 0.05 * u))
        return (loc, tg, 0.0, LENS, fd)

    C.animate_camera(cam, path, 1, NR)
    dbg = os.environ.get("S13A_CAM", "")
    if dbg:        # layout checks: look at the gloater from the front / side
        hp = Vector(gl.head_pos())
        fwd = Vector((math.sin(gl.rig.rotation_euler.z), -math.cos(gl.rig.rotation_euler.z), 0))
        side = Vector((-fwd.y, fwd.x, 0))
        off = {"front": fwd * 1.8, "side": side * 1.8, "back": -fwd * 1.8}[dbg]
        cam.animation_data_clear()
        cam.data.animation_data_clear()
        cam.location = hp + off + Vector((0, 0, -0.25))
        C.look_at(cam, hp + Vector((0, 0, -0.35)))
        cam.data.lens = 50
        cam.data.dof.use_dof = False

    if os.environ.get("S13A_DEBUG"):
        bpy.context.view_layer.update()
        print("S13A cam", tuple(cam.location), cam.data.lens, "tgt", tuple(tgt))
        for p in [gl] + [q for q in fg if hasattr(q, "rig")]:
            ob = p.rig
            print("S13A person", p.name, tuple(ob.location), "hidden", ob.hide_render, ob.hide_get(),
                  "head", tuple(p.head_pos()), "kids", len(ob.children),
                  [(ch.name, ch.hide_render, ch.type) for ch in ob.children][:4])

    ctx.samples = 5
    ctx.render_opts.update({"volumetrics": "low"})
    ctx.interp = True        # slow push, slow head turn, no particles (dust off): 12 fps + RIFE
    ctx.post.update({"grade": "eclipse", "vignette": 0.3, "caption": {"y": 0.70}})
