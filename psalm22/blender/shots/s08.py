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

MOON_AZ, MOON_EL = 245.0, 38.0       # shared with s02b: moon in the west-north-west, behind the mob
XLOD = "far"                          # extras: silhouettes at 5-20 m
WALK_SPEED = 1.5                      # m/s (fx torches: keep < 2 m/s, embers are emitted in local space)


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


# --------------------------------------------------------------------------------------------- build
def build(ctx):
    N, NR = ctx.nframes, ctx.render_frames
    sc = bpy.context.scene
    A = E.olive_grove(ctx, moon_az=MOON_AZ, moon_el=MOON_EL)
    gz = A["ground_z"]
    path = Poly([(q[0], q[1]) for q in A["mob_path"]])

    # ---- where things are
    J = Vector((-2.2, -1.3))                       # Jesus stands in the clearing, west of the rock
    # lead torch arc length: x ~ -23 at frame 1, ~ -14 at the end
    s_lead0 = None
    for k in range(400):
        s = k * 0.25
        if path.at(s)[0].x >= -24.5:
            s_lead0 = s
            break
    s_lead0 = s_lead0 if s_lead0 is not None else path.L * 0.6
    dist = WALK_SPEED * (NR - 1) / ctx.fps
    mob_mid, _ = path.at(s_lead0 + dist * 0.5 - 1.5)
    Fv = (mob_mid - J).normalized()                 # Jesus faces the mob
    Rv = Vector((Fv.y, -Fv.x))                      # his right

    # ---- Jesus
    j = P.make_person("jesus", "JESUS_ROBED", pose=None)
    j.rig.location = (J.x, J.y, gz(J.x, J.y))
    j.rig.rotation_euler.z = math.atan2(Fv.x, -Fv.y)
    j.update()
    look0 = (mob_mid.x, mob_mid.y, gz(mob_mid.x, mob_mid.y) + 1.8)
    lead_end, _ = path.at(s_lead0 + dist)
    look1 = (lead_end.x, lead_end.y, gz(lead_end.x, lead_end.y) + 1.6)
    P.key_pose(j, 1, "stand", look=look0)
    P.key_pose(j, NR, "stand", look=look1)
    P.expression(j, "sorrow", weight=0.7)

    # ---- the mob: 3 sources (soldier + two townsmen), linked clones with their own walk
    sol = P.make_person("guard", "SOLDIER", pose=None, lod=XLOD, hair_strands=False)
    ma = P.make_person("mobA", "CROWD_MAN", seed=11, pose=None, lod=XLOD, hair_strands=False,
                       outfit_colors={"tunic": "umber", "mantle": "charcoal"})
    mb = P.make_person("mobB", "CROWD_MAN", seed=23, pose=None, lod=XLOD, hair_strands=False,
                       outfit_colors={"tunic": "oatmeal", "mantle": "brown"})
    srcs = {"S": sol, "A": ma, "B": mb}
    mz = {k: _stand_offset(v) for k, v in srcs.items()}
    # (source, lag m behind the lead, lateral m (+ = left of the path heading), prop, torch shadow)
    plan = [("S", 0.0, 0.5, "torch", True), ("A", 0.9, -0.9, "torch", True), ("S", 1.7, 1.3, "spear", False),
            ("B", 2.3, -0.1, "torch", True), ("S", 3.1, 0.8, "torch_spear", False), ("A", 3.7, -1.4, "club", False),
            ("B", 4.6, 0.3, "torch", False), ("S", 5.4, -0.6, "spear", False)]
    used = {k: False for k in srcs}
    members = []
    for i, (k, lag, lat, prop, shadow) in enumerate(plan):
        if not used[k]:
            p = srcs[k]
            used[k] = True
        else:
            p = _clone(srcs[k], "%s_m%d" % (srcs[k].name, i))
        members.append((p, k, lag, lat, prop, shadow))
    wood = C.wood_material()
    iron = C.mat("S08_iron", color=(0.05, 0.05, 0.055), rough=0.35, metal=1.0)
    torches = []
    for i, (p, k, lag, lat, prop, shadow) in enumerate(members):
        pts = path.offset_points(s_lead0 - lag, s_lead0 - lag + dist, lat, n=24)
        arms = []
        if "torch" in prop:
            arms.append(lambda Q: _arm_torch(Q, "R"))
        if "spear" in prop or prop == "club":
            arms.append(lambda Q: _arm_spear(Q, "L"))
        walk_keys(p, pts, 1, NR, mz[k], gz, arms=arms, phase=1.7 * i)
    sc.frame_set(1)
    for i, (p, k, lag, lat, prop, shadow) in enumerate(members):
        sc.frame_set(1)
        p.update()
        if "torch" in prop:
            hp = Vector(p.hand_pos("R"))
            t = FX.torch(loc=(0, 0, 0), flame_height=0.42, light_energy=110.0 if shadow else 70.0, shadow=shadow,
                         wind=(-1.2, 0.25, 0.0), seed=11 + i, name="Torch%d" % i, frame_end=NR)
            attach(t.root, p, "wrist.R", Matrix.Translation(hp + Vector((0, 0, 0.42))), 1)
            torches.append(t)
        if "spear" in prop or prop == "club":
            hp = Vector(p.hand_pos("L"))
            o = spear("Spear%d" % i, mat_wood=wood, mat_iron=iron) if "spear" in prop else club("Club%d" % i, mat_wood=wood)
            attach(o, p, "wrist.L", Matrix.Translation(hp), 1)

    # ---- the disciples flee (run away from the torches into the dark)
    d1 = P.make_person("disc1", "CROWD_MAN", seed=31, pose=None, lod=XLOD, hair_strands=False,
                       outfit_colors={"tunic": "sand", "mantle": "olive"})
    d2 = P.make_person("disc2", "CROWD_MAN", seed=47, pose=None, lod=XLOD, hair_strands=False,
                       outfit_colors={"tunic": "oatmeal", "mantle": "indigo"})
    d3 = _clone(d1, "disc3")
    mzd = _stand_offset(d1)
    mzd2 = _stand_offset(d2)
    runs = [
        (d1, mzd, [(-6.0, 0.4), (-3.5, 3.5), (0.5, 8.0), (4.0, 12.5)], 1, 90),
        (d2, mzd2, [(-5.0, -3.2), (-3.0, -6.5), (0.5, -10.5), (3.0, -14.0)], 8, 95),
        (d3, mzd, [(-8.5, 2.4), (-7.0, 6.5), (-5.0, 11.0), (-3.5, 16.0)], 18, 110),
    ]
    for i, (p, m, pts, f0, f1) in enumerate(runs):
        walk_keys(p, pts, f0, f1, m, gz, run=True, phase=2.3 * i)
        p.set_visible(True, frame=1)
        p.set_visible(False, frame=f1 + 1)

    # ---- fill: faint cool bounce from the camera side so his back reads
    fill = C.light("AREA", loc=(J.x - Fv.x * 4.0 + Rv.x * 2.0, J.y - Fv.y * 4.0 + Rv.y * 2.0, gz(J.x, J.y) + 2.2),
                   energy=12.0, color=(0.6, 0.72, 1.0), target=(J.x, J.y, gz(J.x, J.y) + 1.2), size=3.0, name="S08_fill",
                   shadow=False)
    for p in [j, d1, d2] + list(srcs.values()):
        _hazify_person(p)

    # ---- camera: over his right shoulder, creeping in on the lost profile
    hz = gz(J.x, J.y)
    head = Vector((J.x, J.y, hz + 1.62))
    c0 = Vector((J.x, J.y, 0)) - Fv.to_3d() * 3.4 + Rv.to_3d() * 1.35
    c1 = Vector((J.x, J.y, 0)) - Fv.to_3d() * 2.4 + Rv.to_3d() * 1.0
    c0.z = hz + 1.68
    c1.z = hz + 1.62
    aim0 = head + Fv.to_3d() * 6.0 - Rv.to_3d() * 1.4 + Vector((0, 0, -0.15))
    aim1 = head + Fv.to_3d() * 6.0 - Rv.to_3d() * 1.0 + Vector((0, 0, -0.1))

    def cam_path(f):
        u = C.ease_in_out(min(1.0, (f - 1) / float(NR - 1)))
        loc = c0.lerp(c1, u) + C.shake(f, 0.012, 0.45, 5)
        tgt = aim0.lerp(aim1, u)
        return (loc, tgt, 0.0, 35.0, (loc - head).length)

    cam = C.camera(loc=tuple(c0), target=tuple(aim0), lens=35, fstop=2.8, focus=(c0 - head).length)
    C.animate_camera(cam, cam_path, 1, NR)

    ctx.samples = 6
    ctx.render_opts.update({"volumetrics": "low"})
    ctx.interp = False
    ctx.post.update({"grade": ["flashback", "night"], "bloom": 0.4, "bloom_threshold": 0.55, "vignette": 0.3,
                     "temperature": -0.35})
