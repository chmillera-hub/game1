"""s14c - Beasts to dust: "Rescue me from the mouth of the lions; save me from the horns of the wild oxen."

Golgotha, the light has broken. On the plateau stand two silhouettes made of dark ash: a lion roaring
(right, further) and a great wild ox with its horns lowered (left, nearer), both facing the coming
light. The edge of the clouds' shadow sweeps across the ground from the right; where the golden sun
touches them they burn at the edge and crumble into ash that blows away - the lion on the first phrase,
the ox on the second. The camera trucks left with the light, then rises towards the lit cross and the
sun (victory).

Light sweep: an invisible cloud-shadow occluder plane (shadow only) high above slides along `n`; the
ash front of each beast is computed from the exact time the sun-shadow edge reaches each vertex.
"""
import math
import numpy as np
import bpy
from mathutils import Vector, Matrix
from lib import core as C
from lib import env as E
from lib import assets as A
from lib import characters as P
from lib import fx as FX

ASH = (0.022, 0.02, 0.019)
GOLD = (1.0, 0.72, 0.36)


def _ash_material(name="s14c_ash"):
    """Dark charcoal / ash statue: matte black, fine crumbly bump, slight golden sheen at grazing light."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 38.0
    nz.inputs["Detail"].default_value = 8.0
    nz.inputs["Roughness"].default_value = 0.7
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = (ASH[0] * 0.6, ASH[1] * 0.6, ASH[2] * 0.6, 1)
    ramp.color_ramp.elements[1].position = 0.75
    ramp.color_ramp.elements[1].color = (ASH[0] * 2.2, ASH[1] * 2.1, ASH[2] * 2.0, 1)
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.45
    bump.inputs["Distance"].default_value = 0.01
    nt.links.new(nz.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = 0.92
    b.inputs["Sheen Weight"].default_value = 0.5
    b.inputs["Sheen Roughness"].default_value = 0.35
    b.inputs["Sheen Tint"].default_value = (1.0, 0.8, 0.55, 1)
    return m


def _body(arm):
    return next(c for c in arm.children if c.type == "MESH" and not c.name.startswith("eyes"))


def _world_verts(obj):
    me = obj.data
    co = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    M = np.array(obj.matrix_world, np.float32)
    return co @ M[:3, :3].T + M[:3, 3]


def _occluder(name, n, H, L=900.0, seed=0):
    """Huge horizontal plane (local +X = motion direction n, edge at local x ~ 0 with a soft cloud-like
    wobble) casting the cloud shadow; invisible to camera/rays except shadows."""
    rng = np.random.default_rng(seed)
    ys = np.linspace(-L, L, 241)
    wob = np.zeros_like(ys)
    for k, amp in ((0.012, 6.0), (0.05, 1.8), (0.17, 0.5)):
        ph = rng.uniform(0, 6.28)
        wob += amp * np.sin(ys * k + ph)
    verts = [(float(w), float(y), 0.0) for w, y in zip(wob, ys)] + [(2 * L, float(y), 0.0) for y in ys]
    N = len(ys)
    faces = [(i, i + 1, N + i + 1, N + i) for i in range(N - 1)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    o = C.link(bpy.data.objects.new(name, me))
    o.rotation_euler = (0, 0, math.atan2(n.y, n.x))
    o.location = (0, 0, H)
    o.visible_camera = False
    o.visible_diffuse = False
    o.visible_glossy = False
    o.visible_transmission = False
    o.visible_volume_scatter = False
    o.visible_shadow = True
    m = C.mat("s14c_cloud", (0.1, 0.1, 0.1), rough=1.0)
    C.assign(o, m)
    return o


def build(ctx):
    NR = ctx.render_frames
    fps = ctx.fps
    p0, p1 = ctx.phrases[0], ctx.phrases[1]
    G = E.golgotha(ctx, mood="golden", crosses=3, grass=0.8, near_detail=0.6)
    gz = G["ground_z"]
    cr = G["crosses"]["center"]
    base = Vector(cr["base"])
    sky = G["sky"]
    sun = sky["sun"]
    sdir = Vector(sky["sun_dir"]).normalized()
    hv = Vector((sdir.x, sdir.y, 0)).normalized()        # camera looks towards the sun (backlight)
    right = Vector((hv.y, -hv.x, 0))

    def at(dx, dy):                                         # layout: dx screen-right, dy towards the sun
        p = Vector((base.x, base.y, 0)) + right * dx + hv * dy
        p.z = gz(p.x, p.y)
        return p

    def yaw_facing(d):                                      # animal rot_z so its front (-Y) points along d
        return math.degrees(math.atan2(d.x, -d.y))

    # ------------------------------------------------------------------ the figure on the cross (distant)
    j = P.make_person("jesus", "JESUS_CROSS", lod="mid", hair_strands=False)
    P.place_on_cross(j, cr["root"], head="up", strain=0.6)

    # ------------------------------------------------------------------ the ash beasts
    ashm = _ash_material()
    face_light = (right * 0.82 - hv * 0.57).normalized()
    lion = A.animal("lion", "roar", loc=tuple(at(1.15, -4.3)), rot_z=yaw_facing(face_light), fur=False)
    st = A.play(lion, "roar", start_frame=1, speed=0.001, offset=1.75)        # frozen mid-roar, jaw wide
    ox = A.animal("bull", "toss", loc=tuple(at(-1.55, -5.9)), rot_z=yaw_facing((right * 0.9 - hv * 0.44).normalized()),
                  scale=1.18)
    A.play(ox, "toss", start_frame=1, speed=0.001, offset=0.42)               # frozen: horns lowered
    for a in (lion, ox):
        for c in a.children:
            if c.name.startswith("eyes"):
                c.hide_render = True
            elif c.type == "MESH":
                c.data = c.data.copy()
                c.data.materials.clear()
                c.data.materials.append(ashm)
    bpy.context.view_layer.update()

    # ------------------------------------------------------------------ the light front (cloud shadow edge)
    H = 26.0
    n = (-right * 0.86 - hv * 0.5).normalized()             # front travels right -> left and towards camera
    c_ = sdir.dot(n) / sdir.z
    D = n - Vector((0, 0, c_))                              # arrival-distance gradient (see module doc)
    Dn = D.normalized()

    def arrival(obj):                                        # (min, max) of the arrival distance over the mesh
        W = _world_verts(obj)
        a = W @ np.array(D, np.float32) + H * c_
        return float(a.min()), float(a.max()), W

    lb, ob = _body(lion), _body(ox)
    la0, la1, Wl = arrival(lb)
    oa0, oa1, Wo = arrival(ob)
    # front schedule: (frame, edge position along n)
    fL0, fL1 = ctx.frame(p0["start"] + 0.05), ctx.frame(p0["end"] - 0.1)
    fO0, fO1 = ctx.frame(p1["start"] + 0.05), ctx.frame(p1["end"] - 0.1)
    vL = (la1 - la0) / (fL1 - fL0)
    vO = (oa1 - oa0) / (fO1 - fO0)
    sched = [(1 - 40, la0 - 40 * vL), (fL0, la0), (fL1, la1), (fO0, oa0), (fO1, oa1), (NR + 40, oa1 + (NR + 40 - fO1) * vO * 1.6)]
    occ = _occluder("CloudShadow", n, H, seed=ctx.seed)
    for f, e in sched:
        occ.location = n * e + Vector((0, 0, H))
        occ.keyframe_insert("location", frame=f)
    C._set_interp(occ, "location", "LINEAR")
    # ash: release follows the arrival distance exactly (lib maps d linearly over [dmin, dmax] along Dn)
    for body, (a0, a1), (f0, f1), cnt, fs, seed in ((lb, (la0, la1), (fL0, fL1), 30000, 0.011, 1),
                                                   (ob, (oa0, oa1), (fO0, fO1), 36000, 0.013, 2)):
        wind = tuple(-right * 1.9 + hv * 0.9 + Vector((0, 0, 1.35)))
        FX.ash_disintegrate(body, start_frame=f0, duration=(f1 - f0), direction=tuple(Dn), wind=wind, count=cnt,
                            flake_size=fs, life=3.2, jitter=0.12, glow_color=GOLD, glow=5.0, ash_color=(0.03, 0.027, 0.024),
                            turbulence=0.5, gravity=-0.15, seed=seed)

    # ------------------------------------------------------------------ camera: truck left with the light, rise
    look_l = at(1.0, -4.4) + Vector((0, 0, 1.0))
    look_o = at(-1.4, -5.9) + Vector((0, 0, 1.0))
    look_c = Vector(cr["beam"]) + Vector((0, 0, 0.6))
    cam0 = at(0.9, -10.0)

    def cam_fn(f):
        t = (f - 1) / float(NR - 1)
        a = C.smoothstep(min(1.0, max(0.0, (f - fL0 + 10) / (fO0 + 25 - fL0))))      # lion -> ox
        b = C.ease_in_out(min(1.0, max(0.0, (f - (fO1 - 20)) / (NR - (fO1 - 20)))))  # ox -> cross / sun
        loc = cam0 - right * (2.1 * a) + right * (1.0 * b) - hv * 0.3 * t
        loc = loc + Vector((0, 0, 1.05 + 0.9 * b))
        tgt = look_l.lerp(look_o, a).lerp(look_c, b)
        loc = loc + C.shake(f, 0.006, 0.5, 21)
        return (loc, tgt, 0.0, 32)

    cam = C.camera(tuple(cam0 + Vector((0, 0, 1.05))), tuple(look_l), lens=32, name="Cam")
    C.animate_camera(cam, cam_fn, 1, NR)

    ctx.samples = 6
    ctx.render_opts.update({"volumetrics": "low"})
    ctx.interp = False
    ctx.post.update({"grade": "gold", "bloom": 0.42, "exposure": -0.25, "end": {"exposure": 0.05, "bloom": 0.5}})
