"""s06b - He trusts in the Lord: '"He trusts in the Lord," they say, "let the Lord rescue him.
Let him deliver him, since he delights in him."'

Low angle in the crowd at the foot of the centre cross. A chief priest in rich robes, prayer shawl and
turban plays to the onlookers: he waves a contemptuous hand back at the crucified ("He trusts in the
Lord"), flings an open palm up at the darkened sky ("let the Lord rescue him"), then spreads both arms
in mock piety and laughs ("since he delights in him"). Two other leaders nod beside him; Roman
soldiers laugh at the foot of the cross behind. Above everything the dark cross with the placard
(Aramaic / Latin / Greek: 'Jesus of Nazareth, King of the Jews'), the hanging figure backlit in partial
silhouette by the dull red eclipse sun. The camera orbits the priest slowly; on the last phrase the focus
racks from the priest to the cross.
"""
import math
import random
import os
import bpy
from mathutils import Vector
from lib import core as C
from lib import env as E
from lib import characters as P
from lib import assets as AS

SUN_AZ = 176.0
SUN_EL = 27.0
SUN_E = 0.9
LENS = 45.0

FONT_DIRS = ["/usr/share/fonts/truetype", "/home/user/game1/psalm22/comp/fonts"]
TITULUS = [
    # (text in visual order, font candidates, relative height)
    ("ישוע הנצרי מלך היהודים"[::-1], ["ezra/SILEOT.ttf", "freefont/FreeSerif.ttf", "dejavu/DejaVuSans.ttf"], 1.0),
    ("IESVS NAZARENVS REX IVDAEORVM", ["Cinzel-VF.ttf", "freefont/FreeSerif.ttf", "dejavu/DejaVuSerif-Bold.ttf"], 0.9),
    ("ΙΗΣΟΥΣ Ο ΝΑΖΩΡΑΙΟΣ Ο ΒΑΣΙΛΕΥΣ ΤΩΝ ΙΟΥΔΑΙΩΝ", ["freefont/FreeSerif.ttf", "dejavu/DejaVuSerif-Bold.ttf"], 0.85),
]


def _font(cands):
    for c in cands:
        for d in FONT_DIRS:
            p = os.path.join(d, c)
            if os.path.exists(p):
                return bpy.data.fonts.load(p, check_existing=True)
    return None


def _hazify_person(p):
    seen = set()
    objs = p.objects() if hasattr(p, "objects") else [p] + list(p.children_recursive)
    for o in objs:
        if o.type not in ("MESH", "CURVES", "CURVE", "FONT"):
            continue
        for m in getattr(o.data, "materials", []) or []:
            if m is not None and m.name not in seen:
                seen.add(m.name)
                E.hazify(m)


def _preload(p, names):
    for n in names:
        P.expression(p, n, 1.0)
    P.expression(p, "neutral", 0.0)


def titulus(cross_root, scale=(1.3, 1.0, 1.45)):
    """Limewashed placard with the trilingual title painted on (text curves on the front face).
    Returns the sign object (or None)."""
    sign = next((o for o in cross_root.children if o.name.endswith("_sign")), None)
    if sign is None:
        return None
    sign.scale = scale
    W, H, T = 0.55, 0.22, 0.03
    # limewash over the worn wood
    m = sign.active_material.copy()
    m.name = "s06_titulus_wood"
    sign.data.materials[0] = m
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    src = b.inputs["Base Color"].links[0].from_socket if b.inputs["Base Color"].is_linked else None
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 9.0
    nz.inputs["Detail"].default_value = 6.0
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.38
    ramp.color_ramp.elements[0].color = (0.25, 0.25, 0.25, 1)
    ramp.color_ramp.elements[1].position = 0.62
    ramp.color_ramp.elements[1].color = (0.85, 0.85, 0.85, 1)
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[7].default_value = (0.56, 0.52, 0.45, 1)       # limewash (dusty)
    if src is not None:
        nt.links.new(src, mix.inputs[6])
    else:
        mix.inputs[6].default_value = (0.3, 0.22, 0.15, 1)
    nt.links.new(ramp.outputs["Color"], mix.inputs[0])
    nt.links.new(mix.outputs[2], b.inputs["Base Color"])
    # painted letters (parented to the cross root so the sign's non-uniform scale doesn't stretch them)
    paint = C.mat("s06_titulus_paint", (0.018, 0.014, 0.012), rough=0.75)
    E.hazify(paint)
    Wd, Hd = W * scale[0], H * scale[2]
    sl = sign.location
    rows = len(TITULUS)
    margin_x, margin_y = 0.04, 0.035
    avail_w = Wd - 2 * margin_x
    row_h = (Hd - 2 * margin_y) / rows
    for i, (txt, fonts, rel) in enumerate(TITULUS):
        cu = bpy.data.curves.new("titulus_%d" % i, "FONT")
        cu.body = txt
        f = _font(fonts)
        if f is not None:
            cu.font = f
        cu.align_x = "CENTER"
        cu.align_y = "CENTER"
        cu.size = row_h * 0.9 * rel
        ob = C.link(bpy.data.objects.new("titulus_%d" % i, cu))
        ob.data.materials.append(paint)
        bpy.context.view_layer.update()
        wdt = max(1e-4, ob.dimensions.x)
        if wdt > avail_w:
            cu.size *= avail_w / wdt
        ob.parent = cross_root
        ob.matrix_parent_inverse.identity()
        zc = sl.z + Hd / 2 - margin_y - row_h * (i + 0.5)
        ob.location = (sl.x, sl.y - T * scale[1] / 2 - 0.0015, zc)
        ob.rotation_euler = (math.radians(90), 0, 0)
    return sign


def build(ctx):
    N, NR = ctx.nframes, ctx.render_frames
    rnd = random.Random(ctx.seed)
    ph = [tuple(int(round(x)) for x in ctx.phrase_frames(i)) for i in range(len(ctx.phrases))]
    (a1, b1), (a2, b2), (a3, b3) = ph[0], ph[1], ph[2]

    # ------------------------------------------------------------------ set
    priest_xy = Vector((0.55, -3.7))
    cam_r = 5.3
    az0, az1 = math.radians(-26.0), math.radians(-6.0)    # camera bearing around the priest (0 = straight -Y)
    views = []
    for k in range(3):
        a = az0 + (az1 - az0) * k / 2.0
        loc = (priest_xy.x + cam_r * math.sin(a), priest_xy.y - cam_r * math.cos(a), 12.2)
        views.append(dict(loc=loc, target=(0.0, 0.6, 13.5), lens=LENS, margin=25))
    A = E.golgotha(ctx, mood="eclipse", sun_az=SUN_AZ, view=views, near_detail=0.7, grass=0.8,
                   sky_over=dict(sun_el=SUN_EL, sun_disk=dict(E.SKY_PRESETS["eclipse"]["sun_disk"], el=SUN_EL)))
    gzf = A["ground_z"]
    cx = A["crosses"]
    c = cx["center"]
    cz = c["base"][2]
    sun = A["sky"]["sun"]
    sun.data.energy = SUN_E
    sign = titulus(c["root"])

    # ------------------------------------------------------------------ the crucified (backlit, mid LOD)
    j = P.make_person("jesus", "JESUS_CROSS", pose=None, lod="mid", hair_strands=False)
    P.place_on_cross(j, c["root"], head="down", strain=0.62)
    P.expression(j, "exhausted")
    _hazify_person(j)
    def ground(x, y):
        return gzf(x, y)

    def place(p, xy, face_to=None, yaw_deg=None):
        z = ground(xy[0], xy[1])
        p.rig.location = (xy[0], xy[1], z)
        if face_to is not None:
            yaw = math.atan2(face_to[0] - xy[0], -(face_to[1] - xy[1]))
        else:
            yaw = math.radians(yaw_deg or 0.0)
        p.rig.rotation_euler = (0, 0, yaw)
        return z

    cam_mid = Vector((priest_xy.x + cam_r * math.sin((az0 + az1) / 2), priest_xy.y - cam_r * math.cos((az0 + az1) / 2),
                      cz + 1.15))
    jesus_head = Vector(j.head_pos())
    sky_pt = Vector((priest_xy.x - 1.2, priest_xy.y + 2.0, cz + 9.0))

    # ------------------------------------------------------------------ chief priest (hero)
    pr = P.make_person("chief", "PRIEST", pose=None, expression=None, lod="hero")
    crowd_pt = Vector((priest_xy.x - 6.0, priest_xy.y - 4.0, cz + 1.6))     # the onlookers to his front-left
    gz = place(pr, priest_xy, face_to=(priest_xy.x - 3.0, priest_xy.y - 2.4))
    _preload(pr, ["sneer", "mock", "laugh"])
    sh = Vector(pr.bone_world("upperarm01.R"))
    to_cross = (Vector((c["chest"][0], c["chest"][1], sh.z + 0.25)) - sh).normalized()
    present = sh + to_cross * 0.55 + Vector((0, 0, -0.05))
    heaven = sh + (Vector((-0.15, 0.25, 1.0)).normalized()) * 0.62
    P.key_pose(pr, 1, "reach", ground_z=gz, target=tuple(present), side="R", hand="open")
    P.key_pose(pr, a1 + 4, "reach", ground_z=gz, target=tuple(present + Vector((0.0, 0.05, 0.08))), side="R", hand="open")
    P.key_pose(pr, b1 + 2, "stand_relaxed", ground_z=gz)
    P.key_pose(pr, a2 + 6, "reach", ground_z=gz, target=tuple(heaven), side="R", hand="open")
    P.key_pose(pr, b2, "reach", ground_z=gz, target=tuple(heaven + Vector((0.02, 0.05, 0.03))), side="R", hand="open")
    P.key_pose(pr, a3 + 8, "arms_raised", ground_z=gz, spread=58, head="up", hands="open")
    P.key_pose(pr, a3 + 40, "arms_raised", ground_z=gz, spread=62, head="up", hands="open")
    P.key_pose(pr, b3 + 4, "stand_relaxed", ground_z=gz)
    P.key_pose(pr, NR, "stand_relaxed", ground_z=gz)
    # head: to the crowd on "they say", up to the sky, back to the crowd for the jibe
    looks = [(1, jesus_head), (a1 + 22, crowd_pt), (b1 + 4, crowd_pt), (a2 + 10, sky_pt), (b2 - 4, sky_pt),
             (a3 + 12, sky_pt + Vector((0, 0, 2))), (a3 + 44, crowd_pt), (NR, cam_mid)]
    for f, tgt in looks:
        bpy.context.scene.frame_set(f)
        P.look_at(pr, tuple(tgt), frame=f)
    bpy.context.scene.frame_set(1)
    P.expression(pr, "sneer", 0.8, frame=1)
    P.expression(pr, "mock", 0.9, frame=a1 + 18)
    P.expression(pr, "sneer", 1.0, frame=a2 + 6)
    P.expression(pr, "mock", 1.0, frame=a3 + 10)
    P.laugh(pr, a3 + 46, min(NR - 6, b3 + 30), amount=0.8)
    P.blink(pr, a1 + 30)
    P.blink(pr, a3 + 2)
    _hazify_person(pr)

    # ------------------------------------------------------------------ the other leaders (nodding)
    leaders = []
    for k, (xy, spec, nodf) in enumerate([
            ((priest_xy.x - 1.35, priest_xy.y + 0.55), dict(seed=31, outfit=["robe_rich", "turban"], age_years=62,
                                                         beard="long", build="heavy",
                                                         outfit_colors={"mantle": "indigo", "turban": "linen"}), 0),
            ((priest_xy.x + 1.25, priest_xy.y + 0.9), dict(seed=44, outfit=["robe", "headcloth"], age_years=50,
                                                        beard="full", outfit_colors={"tunic": "white_linen",
                                                                                     "mantle": "blue_grey",
                                                                                     "headcloth": "white_linen"}), 1)]):
        sp = dict(lod="mid", hair_strands=False, pose=None, expression=None)
        sp.update(spec)
        L = P.make_person("lead%d" % k, "CROWD_MAN", **sp)
        lz = place(L, xy, face_to=(crowd_pt.x * 0.5 + priest_xy.x * 0.5, crowd_pt.y * 0.5 + priest_xy.y * 0.5))
        _preload(L, ["sneer", "mock", "laugh"])
        P.pose(L, "stand" if k == 0 else "stand_relaxed", ground_z=lz)
        bpy.context.scene.frame_set(1)
        P.look_at(L, tuple(Vector(pr.head_pos())), frame=1)
        P.look_at(L, tuple(Vector(pr.head_pos())), frame=a2)
        P.expression(L, "sneer", 0.7, frame=1)
        P.expression(L, "mock", 0.9, frame=a2 + 10)
        P.nod(L, a2 + 2 + 6 * k, b2 + 10, amount=0.9, freq=1.1 + 0.2 * k)
        bpy.context.scene.frame_set(a3 + 20)
        P.look_at(L, tuple(crowd_pt), frame=a3 + 20)
        bpy.context.scene.frame_set(1)
        P.nod(L, a3 + 14 + 6 * k, b3 - 6, amount=0.7, freq=0.9 + 0.2 * k)
        _hazify_person(L)
        leaders.append(L)

    # ------------------------------------------------------------------ Roman soldiers laughing at the cross foot
    soldiers = []
    for k, (xy, spec, lf) in enumerate([
            ((-1.25, -0.45), dict(), (a1 + 20, b3 + 10)),
            ((1.45, -0.75), dict(age_years=36, skin_tone=0.55, beard="short",
                                 face={"nose/nose-hump-decr|incr": 0.4, "head/head-square": 0.4,
                                       "chin/chin-width-decr|incr": 0.3}), (a2 + 4, b3 + 20))]):
        sp = dict(lod="mid", pose=None, expression=None, hair_strands=False)
        sp.update(spec)
        S = P.make_person("soldier%d" % k, "SOLDIER", **sp)
        sz = place(S, xy, face_to=(priest_xy.x + 0.3 * (k - 0.5), priest_xy.y))
        _preload(S, ["laugh", "mock"])
        P.pose(S, "stand_relaxed" if k == 0 else "stand", ground_z=sz)
        bpy.context.scene.frame_set(1)
        P.look_at(S, tuple(Vector(pr.head_pos()) + Vector((0, 0, 0.3))), frame=1)
        P.expression(S, "mock", 0.6, frame=1)
        P.laugh(S, lf[0], min(NR, lf[1]), amount=1.0, freq=2.6 + 0.6 * k)
        _hazify_person(S)
        soldiers.append(S)
    # a spear planted by the first soldier
    try:
        sp_root = AS.load("spear", loc=(-1.6, -0.25, ground(-1.6, -0.25) - 0.15), rot_z=0, variant=0, upright=True)
        for o in AS.children_recursive(sp_root):
            if o.type == "MESH":
                for m in o.data.materials:
                    E.hazify(m)
    except Exception as e:
        print("s06b WARNING: spear failed:", e)

    # ------------------------------------------------------------------ onlookers (baked, edges of frame)
    pts = []
    for k in range(40):
        x = rnd.uniform(-6.5, 6.5)
        y = rnd.uniform(-8.5, -2.2)
        if (Vector((x, y)) - priest_xy).length < 1.3:
            continue
        # keep the camera corridor clear (camera ~ (priest + 5.3 m towards -Y))
        if y < priest_xy.y - 1.0 and abs(x - (priest_xy.x - 1.2)) < 2.4:
            continue
        if any((x - q[0]) ** 2 + (y - q[1]) ** 2 < 0.7 ** 2 for q in pts):
            continue
        pts.append((x, y))
    cposes = [("stand", {"look": (0.0, -5.0, 3.6)}), ("stand_relaxed", {"look": (0.5, -4.0, 2.4)}),
              ("mourn", {}), ("stand", {"head": "up"})]
    cexpr = ["sneer", "mock", "sorrow", "neutral"]

    def cpose(per, i):
        nm, kw = cposes[i % len(cposes)]
        P.pose(per, nm, **kw)
        if cexpr[i % len(cexpr)] != "neutral":
            P.expression(per, cexpr[i % len(cexpr)], 0.8)

    cr = P.crowd(len(pts), positions=pts, seed=ctx.seed % 89, variety=4, lod="mid",
                 face=(0.0, 0.6, cz), yaw_jitter=25, height_fn=lambda x, y: ground(x, y),
                 pose_fn=cpose, name="OnlookersB")
    for o in cr.sources:
        _hazify_person(o)

    # ------------------------------------------------------------------ light: soft bounce fill on the priest's face
    fill = C.light("AREA", tuple(cam_mid + Vector((-1.0, 0.6, 0.9))), 40.0, temp=3400, target=tuple(pr.head_pos()),
                   size=2.5, name="FaceFill", shadow=False)

    # ------------------------------------------------------------------ camera: slow orbit, rack focus to the cross
    head0 = Vector(pr.head_pos())
    cross_focus = Vector(c["chest"]) + Vector((0, 0, 0.6))
    f_rack0, f_rack1 = a3 + 52, min(NR - 8, b3 + 6)
    cam = C.camera(loc=tuple(cam_mid), target=tuple(head0), lens=LENS, fstop=2.8)

    def path(f):
        u = C.ease_in_out((f - 1) / float(NR - 1))
        a = az0 + (az1 - az0) * u
        loc = Vector((priest_xy.x + cam_r * math.sin(a), priest_xy.y - cam_r * math.cos(a), cz + 1.12 + 0.12 * u))
        loc += C.shake(f, 0.006, 0.35, 11)
        # aim between the priest's head and the placard
        tgt = head0.lerp(Vector(c["sign"]), 0.42) + Vector((0.0, 0.0, -0.2))
        r = C.smoothstep((f - f_rack0) / float(max(1, f_rack1 - f_rack0)))
        foc = (head0 - loc).length * (1 - r) + (cross_focus - loc).length * r
        return (loc, tgt, 0.0, LENS, foc)

    C.animate_camera(cam, path, 1, NR)

    ctx.samples = 6
    ctx.render_opts.update({"volumetrics": "low"})
    ctx.interp = False
    ctx.post.update({"grade": "eclipse", "vignette": 0.24, "bloom": 0.22, "caption": {"y": 0.72}})
