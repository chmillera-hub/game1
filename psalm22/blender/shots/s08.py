"""s08 - "Trouble is near": "Do not be far from me, for trouble is near / and there is no one to help."

Flashback, Gethsemane at night (same grove, rock and moon as s02b). Over Jesus's right shoulder: he stands
alone in the clearing, facing west, while the torches of an armed mob (temple guards / soldiers, spears,
clubs) advance towards him along the path through the twisted olive trees, backlit by the moon in the
mist. The disciples' silhouettes break and flee past him into the darkness. The camera creeps in on
his lost profile; the warm torchlight grows on him, smoke and embers drift up from the torches.
Torches flicker per frame and throw embers -> rendered at 24 fps (no interpolation).
"""
import math
import bpy
from mathutils import Vector, Matrix
from lib import core as C
from lib import env as E
from lib import characters as P
from lib import fx as FX

MOON_AZ, MOON_EL = 245.0, 38.0       # moon in the west-north-west, behind the mob (backlight)
XLOD = "far"                          # extras: silhouettes at 5-20 m
WALK_SPEED = 1.4                      # m/s (fx torches: keep < 2 m/s, embers are emitted in local space)


# --------------------------------------------------------------------------------------------- helpers
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


class Poly:
    """Arc-length parameterised 2D polyline (x, y)."""

    def __init__(self, pts):
        self.p = [Vector((q[0], q[1])) for q in pts]
        self.s = [0.0]
        for a, b in zip(self.p, self.p[1:]):
            self.s.append(self.s[-1] + (b - a).length)
        self.L = self.s[-1]

    def at(self, s):
        s = max(-50.0, min(self.L + 50.0, s))
        if s <= 0:
            d = (self.p[1] - self.p[0]).normalized()
            return self.p[0] + d * s, d
        if s >= self.L:
            d = (self.p[-1] - self.p[-2]).normalized()
            return self.p[-1] + d * (s - self.L), d
        i = 0
        while self.s[i + 1] < s:
            i += 1
        t = (s - self.s[i]) / max(1e-9, self.s[i + 1] - self.s[i])
        d = (self.p[i + 1] - self.p[i]).normalized()
        return self.p[i].lerp(self.p[i + 1], t), d

    def offset_points(self, s0, s1, lateral, n=24):
        out = []
        for k in range(n):
            s = s0 + (s1 - s0) * k / (n - 1)
            q, d = self.at(s)
            nrm = Vector((-d.y, d.x))
            out.append(q + nrm * lateral)
        return out


def _clone(src, name):
    q = P.clone(src, src.rig.location.copy(), src.rig.rotation_euler.z, name=name)
    for k in ("_w", "_co", "_lbs", "_anat", "_pmaps"):
        if hasattr(src, k):
            setattr(q, k, getattr(src, k))
    return q


def _stand_offset(p):
    P0 = P._build_pose(p, "stand", {})
    return float(P.lbs_points(p, P0)[:, 2].min())


def _arm_torch(Q, s="R"):
    lat = P._lateral(s)
    u = (lat * 0.5 + P.FWD * 0.7 + P.UP * (-0.3)).normalized()
    P._arm(Q, s, u, P.UP, 108, pron=15)
    P._hand(Q, s, "grip")


def _arm_spear(Q, s="L"):
    lat = P._lateral(s)
    u = (lat * 0.18 + P.FWD * 0.12 - P.UP).normalized()
    P._arm(Q, s, u, P.FWD, 78, pron=70)
    P._hand(Q, s, "grip")


def walk_keys(p, pts, f0, f1, mz, hfn, run=False, arms=(), phase=0.0, step=1):
    """Like characters.walk(), but arms in `arms` (callables Q -> None) are overridden every frame
    (a torch held up, a spear held steady) and the gait phase can be offset."""
    rig = p.rig
    pts = [Vector((q[0], q[1], 0.0)) for q in pts]
    seg = [(pts[i + 1] - pts[i]).length for i in range(len(pts) - 1)]
    total = sum(seg) or 1e-6
    stride = p.height * 0.5 * (1.35 if not run else 2.4)
    prev = None
    f = f0
    while f <= f1:
        u = (f - f0) / max(1, f1 - f0)
        d = u * total
        i = 0
        while i < len(seg) - 1 and d > seg[i]:
            d -= seg[i]
            i += 1
        a, b = pts[i], pts[min(i + 1, len(pts) - 1)]
        tt = d / seg[i] if seg[i] > 0 else 0
        pos = a.lerp(b, min(1, tt))
        pos.z = hfn(pos.x, pos.y)
        dv = b - a
        yaw = math.atan2(dv.x, -dv.y) if dv.length > 1e-6 else (prev or 0.0)
        if prev is not None:
            while yaw - prev > math.pi:
                yaw -= 2 * math.pi
            while yaw - prev < -math.pi:
                yaw += 2 * math.pi
        prev = yaw
        ph = (u * total) / stride * 2 * math.pi + phase
        Q = P._Pose(p)
        P._pose_walk_frame(Q, p, ph, 2.2 if run else 1.0)
        for fn in arms:
            fn(Q)
        bob = (0.012 if not run else 0.035) * abs(math.cos(ph)) - 0.006
        Q.loc.z += -mz + bob
        Q.write(frame=f)
        rig.location = pos
        rig.rotation_euler = (0, 0, yaw)
        rig.keyframe_insert("location", frame=f)
        rig.keyframe_insert("rotation_euler", frame=f)
        f += step
    C._set_interp(rig, "location", "LINEAR")


def attach(obj, person, bone, world_matrix, frame):
    """Parent obj to a pose bone keeping world_matrix at `frame`."""
    sc = bpy.context.scene
    sc.frame_set(frame)
    bpy.context.view_layer.update()
    obj.parent = person.rig
    obj.parent_type = "BONE"
    obj.parent_bone = bone
    obj.matrix_parent_inverse = Matrix.Identity(4)
    bpy.context.view_layer.update()
    obj.matrix_world = world_matrix
    bpy.context.view_layer.update()


def spear(name, length=2.3, mat_wood=None, mat_iron=None):
    sh = C.prim("cylinder", name=name, radius=0.014, depth=length, vertices=8, loc=(0, 0, 0))
    sh.data.transform(Matrix.Translation((0, 0, length * 0.5 - 0.75)))   # grip 0.75 m above the butt
    C.assign(sh, mat_wood)
    tip = C.prim("cone", name=name + "_tip", radius1=0.028, radius2=0.0, depth=0.24, vertices=6, loc=(0, 0, 0))
    tip.location = (0, 0, length - 0.75 + 0.1)
    tip.scale = (1.0, 0.35, 1.0)
    C.assign(tip, mat_iron)
    tip.parent = sh
    return sh


def club(name, mat_wood=None):
    c = C.prim("cylinder", name=name, radius=0.03, depth=0.75, vertices=8, loc=(0, 0, 0))
    c.data.transform(Matrix.Translation((0, 0, 0.25)))
    C.assign(c, mat_wood)
    return c




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

# --------------------------------------------------------------------------------------------- build
def build(ctx):
    N, NR = ctx.nframes, ctx.render_frames
    sc = bpy.context.scene
    # trees=24: the ring of trees the torches light up is mid LOD (real branches) instead of far blob crowns
    E.set_view(dict(loc=(0.45, -0.7, 1.5), target=(-10.0, -0.9, 0.5), lens=50, margin=25))   # cull scatter to the camera
    A = E.olive_grove(ctx, moon_az=MOON_AZ, moon_el=MOON_EL, trees=24, rays=False, motes=False, city_lights=False)
    E.set_view(None)
    gz = A["ground_z"]
    path = Poly([(q[0], q[1]) for q in A["mob_path"]])

    # ---- where things are
    J = Vector((-2.2, -1.3))                       # Jesus stands in the clearing, west of the rock
    # the lead torch comes up the path from x ~ -19.5 to ~ -10 (7 m from him at the end)
    s_lead0 = next((k * 0.25 for k in range(400) if path.at(k * 0.25)[0].x >= -19.5), path.L * 0.6)
    dist = WALK_SPEED * (NR - 1) / ctx.fps
    mob_mid, _ = path.at(s_lead0 + dist * 0.5 - 1.5)
    Fv = (mob_mid - J).normalized()                 # Jesus faces the mob
    Rv = Vector((Fv.y, -Fv.x))                      # his right
    hz = gz(J.x, J.y)

    cull_instancers(["EnvGroveNear", "EnvGroveMid"], (0.45, -0.7), (-10.0, -0.9), 50.0)
    # the far-LOD blob crowns read as orange balls once the torches light them: drop that ring
    if bpy.data.objects.get("EnvGroveFar") is not None:
        bpy.data.objects["EnvGroveFar"].hide_render = True

    # ---- two old twisted olive trees flanking the path: the torches come between them
    protos = [E.olive_tree(seed=21, age=1.2, size=1.1, lod=1), E.olive_tree(seed=30, age=0.8, size=0.95, lod=1)]
    for (x, y, rz, scl, k) in ((-14.5, -5.0, 40.0, 0.95, 0), (-18.5, 3.4, 200.0, 1.0, 1)):
        E.place(protos[k], (x, y, gz(x, y) - 0.12), rot=(0, 0, rz), scale=scl, name="S08_olive%d" % k)

    # ---- Jesus
    j = P.make_person("jesus", "JESUS_ROBED", pose=None)
    j.rig.location = (J.x, J.y, hz)
    j.rig.rotation_euler.z = math.atan2(Fv.x, -Fv.y)
    j.update()
    look0 = (mob_mid.x, mob_mid.y, gz(mob_mid.x, mob_mid.y) + 1.8)
    lead_end, _ = path.at(s_lead0 + dist)
    look1 = (lead_end.x, lead_end.y, gz(lead_end.x, lead_end.y) + 1.7)
    P.key_pose(j, 1, "stand", look=look0)
    P.key_pose(j, NR, "stand", look=look1)
    P.expression(j, "sorrow", weight=0.7)
    if j.parts.get("beard") is not None:          # seen from behind: the beard never shows, skip its cost
        j.parts["beard"].hide_render = True

    # ---- the mob: 3 sources (soldier + two townsmen, far LOD), linked clones with their own walk
    sol = P.make_person("guard", "SOLDIER", pose=None, lod=XLOD, hair_strands=False)
    ma = P.make_person("mobA", "CROWD_MAN", seed=11, pose=None, lod=XLOD, hair_strands=False,
                       outfit_colors={"tunic": "umber", "mantle": "charcoal"})
    mb = P.make_person("mobB", "CROWD_MAN", seed=23, pose=None, lod=XLOD, hair_strands=False,
                       outfit_colors={"tunic": "oatmeal", "mantle": "brown"})
    srcs = {"S": sol, "A": ma, "B": mb}
    mz = {k: _stand_offset(v) for k, v in srcs.items()}
    # (source, lag m behind the lead, lateral m (+ = left of the path heading), prop)
    # the front rank carries spears/clubs and reads as silhouettes against the torches of the men behind
    plan = [("S", 0.0, 0.5, "spear"), ("A", 0.7, -0.9, "club"), ("S", 1.3, 1.3, "spear"),
            ("B", 2.1, -0.2, "torch"), ("S", 2.8, 0.8, "torch"), ("A", 3.5, -1.3, "torch"),
            ("B", 4.4, 0.4, "torch_spear")]
    used = {k: False for k in srcs}
    members = []
    for i, (k, lag, lat, prop) in enumerate(plan):
        if not used[k]:
            p = srcs[k]
            used[k] = True
        else:
            p = _clone(srcs[k], "%s_m%d" % (srcs[k].name, i))
        members.append((p, k, lag, lat, prop))
    wood = C.wood_material()
    iron = C.mat("S08_iron", color=(0.05, 0.05, 0.055), rough=0.35, metal=1.0)
    for i, (p, k, lag, lat, prop) in enumerate(members):
        pts = path.offset_points(s_lead0 - lag, s_lead0 - lag + dist, lat, n=24)
        arms = []
        if "torch" in prop:
            arms.append(lambda Q: _arm_torch(Q, "R"))
        if "spear" in prop or prop == "club":
            arms.append(lambda Q: _arm_spear(Q, "L"))
        walk_keys(p, pts, 1, NR, mz[k], gz, arms=arms, phase=1.7 * i)
    torches = []
    for i, (p, k, lag, lat, prop) in enumerate(members):
        sc.frame_set(1)
        p.update()
        if "torch" in prop:
            hp = Vector(p.hand_pos("R"))
            t = FX.torch(loc=(0, 0, 0), flame_height=0.42, light_energy=45.0, shadow=False, smoke=len(torches) < 3,
                         wind=(-1.2, 0.25, 0.0), seed=11 + i, name="Torch%d" % i, frame_end=NR)
            attach(t.root, p, "wrist.R", Matrix.Translation(hp + Vector((0, 0, 0.42))), 1)
            torches.append(t)
        if "spear" in prop or prop == "club":
            hp = Vector(p.hand_pos("L"))
            o = spear("Spear%d" % i, mat_wood=wood, mat_iron=iron) if "spear" in prop else club("Club%d" % i, mat_wood=wood)
            attach(o, p, "wrist.L", Matrix.Translation(hp), 1)
    # the combined spill of the torches: a soft warm light just behind the leading men lights the ground
    # and trunks around them from behind (keeps the men as silhouettes), no shadow
    glow = C.light("AREA", loc=(0, 0, 0), energy=45.0, color=C.kelvin(1800), size=3.0, name="S08_mobglow",
                   shadow=False, volume=0.0)
    for f in range(1, NR + 1, 6):
        q, d = path.at(s_lead0 - 3.4 + dist * (f - 1) / (NR - 1))
        loc = Vector((q.x, q.y, gz(q.x, q.y) + 1.7))
        glow.location = loc
        glow.rotation_euler = C.look_rot(loc, loc + d.to_3d() * 3.0 + Vector((0, 0, -1.7)))
        glow.keyframe_insert("location", frame=f)
        glow.keyframe_insert("rotation_euler", frame=f)
    # torchlight finding him: a narrow warm spot from the leading torches onto his figure, growing as they come
    # (the one shadow-casting local light: his shadow stretches back towards the camera)
    tl = C.light("SPOT", loc=(0, 0, 0), energy=0.0, color=C.kelvin(1850), size=0.6, spot_size=16.0, spot_blend=0.9,
                 name="S08_torch_on_him", volume=0.0, shadow=True)
    for f in range(1, NR + 1, 4):
        q, _ = path.at(s_lead0 - 2.5 + dist * (f - 1) / (NR - 1))     # the first torches
        loc = Vector((q.x, q.y, gz(q.x, q.y) + 2.0))
        tl.location = loc
        tl.rotation_euler = C.look_rot(loc, (J.x, J.y, hz + 1.25))
        dd = (loc - Vector((J.x, J.y, hz + 1.25))).length
        tl.data.energy = 2600.0 * (9.0 / dd) ** 2 * C.smoothstep(min(1.0, (f - 1) / (NR * 0.6)))
        tl.keyframe_insert("location", frame=f)
        tl.keyframe_insert("rotation_euler", frame=f)
        tl.data.keyframe_insert("energy", frame=f)

    # ---- the disciples flee: from in front of the torches, past him on either side, into the dark
    d1 = P.make_person("disc1", "CROWD_MAN", seed=31, pose=None, lod=XLOD, hair_strands=False,
                       outfit_colors={"tunic": "sand", "mantle": "olive"})
    d2 = P.make_person("disc2", "CROWD_MAN", seed=47, pose=None, lod=XLOD, hair_strands=False,
                       outfit_colors={"tunic": "oatmeal", "mantle": "indigo"})
    d3 = _clone(d1, "disc3")
    mzd = _stand_offset(d1)
    mzd2 = _stand_offset(d2)
    runs = [
        (d1, mzd, [(-11.0, 0.3), (-5.0, -3.0), (0.0, -5.5)], 1, 70),     # towards camera-left, past his left side
        (d2, mzd2, [(-13.0, -1.8), (-8.0, -4.5), (-3.0, -8.0)], 1, 80),  # deeper, off to the left
        (d3, mzd, [(-12.0, 0.8), (-7.0, 2.0), (-2.0, 3.5)], 1, 65),      # off to the right
    ]
    for i, (p, m, pts, f0, f1) in enumerate(runs):
        walk_keys(p, pts, f0, f1, m, gz, run=True, phase=2.3 * i)
        p.set_visible(True, frame=1)
        p.set_visible(False, frame=f1 + 1)
    for p in [j, d1, d2] + list(srcs.values()):
        _hazify_person(p)

    # ---- camera: over his right shoulder, creeping in; focus racks from the torches to him
    head = Vector((J.x, J.y, hz + 1.62))
    c0 = Vector((J.x, J.y, 0)) - Fv.to_3d() * 2.6 + Rv.to_3d() * 0.75
    c1 = Vector((J.x, J.y, 0)) - Fv.to_3d() * 2.25 + Rv.to_3d() * 0.6
    c0.z = hz + 1.52
    c1.z = hz + 1.5
    aim0 = head + Fv.to_3d() * 8.0 - Rv.to_3d() * 0.9 + Vector((0, 0, -0.75))
    aim1 = head + Fv.to_3d() * 8.0 - Rv.to_3d() * 0.45 + Vector((0, 0, -0.7))
    f_rack0 = ctx.frame(ctx.phrases[0]["end"] - 0.4) if ctx.phrases else NR * 0.5
    f_rack1 = ctx.frame(ctx.phrases[1]["start"] + 0.3) if len(ctx.phrases) > 1 else NR * 0.6

    def cam_path(f):
        u = C.ease_in_out(min(1.0, (f - 1) / float(NR - 1)))
        loc = c0.lerp(c1, u) + C.shake(f, 0.01, 0.45, 5)
        tgt = aim0.lerp(aim1, u)
        q, _ = path.at(s_lead0 - 1.0 + dist * (f - 1) / (NR - 1))
        d_mob = (Vector((q.x, q.y, hz + 1.5)) - loc).length
        d_him = (head - loc).length
        r = C.smoothstep(min(1.0, max(0.0, (f - f_rack0) / max(1.0, f_rack1 - f_rack0))))
        return (loc, tgt, 0.0, 50.0, d_mob + (d_him - d_mob) * r)

    cam = C.camera(loc=tuple(c0), target=tuple(aim0), lens=50, fstop=2.8, focus=10.0)
    C.animate_camera(cam, cam_path, 1, NR)

    # render budget (profiled): shadow-casting point lights cost ~2/3 of the frame here -> torches cast no
    # shadows (the moon does); no moon-shaft fog layer; no volumetric shadows
    ctx.samples = 4
    ctx.render_opts.update({"volumetrics": "low", "vol_shadows": False})
    ctx.interp = False            # torch flicker + embers: 24 fps
    ctx.post.update({"grade": ["flashback", "night"], "bloom": 0.4, "bloom_threshold": 0.55, "vignette": 0.3,
                     "temperature": -0.3})
