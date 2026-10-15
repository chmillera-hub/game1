"""s14c - Beasts to dust: "Rescue me from the mouth of the lions; save me from the horns of the wild oxen."

Golgotha, the light has broken. On the plateau below the three crosses stand two silhouettes made of dark
ash: a lion roaring (right) and a great wild ox tossing its horns (left), both facing the coming
light. The edge of the clouds' shadow sweeps across the ground from the right; where the golden sun
touches them they burn at the edge and crumble into ash that blows away - the lion on the first phrase,
the ox on the second; the crosses catch the light in turn. Low camera, slow push-in, finally tilting up
to the centre cross in the golden light (victory).

Light sweep: an invisible cloud-shadow occluder plane (shadow only) high above slides along `n` (screen
right -> left, perpendicular to the backlight, so the edge is a vertical plane on the beasts); its keyed
motion is solved so the shadow edge crosses each beast exactly while the ash front does.
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from lib import core as C
from lib import env as E
from lib import assets as A
from lib import characters as P
from lib import fx as FX

ASH = (0.022, 0.02, 0.019)
GOLD = (1.0, 0.72, 0.36)
FLAKE_GLOW = (1.0, 0.55, 0.2)
EDGE_GLOW = 3.2
GOLD_SUN = (1.0, 0.78, 0.5)            # = s14b
SUN_AZ, SUN_EL = 165.0, 30.0           # = s14a / s14b (the light that broke through)
CAM_D0, CAM_D1 = 10.4, 9.2          # camera distance in front of the centre cross (start, end of the push)


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
    b.inputs["Roughness"].default_value = 0.9
    b.inputs["Specular IOR Level"].default_value = 0.3
    b.inputs["Sheen Weight"].default_value = 0.15
    b.inputs["Sheen Roughness"].default_value = 0.5
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
    """Huge horizontal plane (local +X = motion direction n, edge at local x = wob(local y): a soft,
    slightly wavy cloud edge) casting the cloud shadow; invisible to camera/rays except shadows.
    Returns (object, wob function of the local y)."""
    rng = np.random.default_rng(seed)
    terms = [(k, amp, rng.uniform(0, 6.28)) for k, amp in ((0.012, 5.0), (0.05, 1.2), (0.17, 0.35))]

    def wob(y):
        return sum(amp * np.sin(np.asarray(y) * k + ph) for k, amp, ph in terms)
    ys = np.linspace(-L, L, 481)
    w = wob(ys)
    verts = [(float(a), float(y), 0.0) for a, y in zip(w, ys)] + [(2 * L, float(y), 0.0) for y in ys]
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
    C.assign(o, C.mat("s14c_cloud", (0.1, 0.1, 0.1), rough=1.0))
    return o, wob



def _lean_baked(obj):
    """Distant baked figure: drop the frozen beard curves child and the skin SSS (screen-space pass)."""
    if obj is None:
        return
    for c in list(obj.children):
        if c.type == "CURVES":
            bpy.data.objects.remove(c)
    for m in obj.data.materials:
        if m and m.use_nodes:
            for n in m.node_tree.nodes:
                if n.bl_idname == "ShaderNodeBsdfPrincipled" and "Subsurface Weight" in n.inputs:
                    if not n.inputs["Subsurface Weight"].is_linked:
                        n.inputs["Subsurface Weight"].default_value = 0.0

def build(ctx):
    NR = ctx.render_frames
    fps = ctx.fps
    p0, p1 = ctx.phrases[0], ctx.phrases[1]
    az = math.radians(SUN_AZ)
    hv0 = Vector((math.sin(az), -math.cos(az), 0))
    r0 = Vector((hv0.y, -hv0.x, 0))
    c0 = Vector((0.0, 0.6, 0))
    views = [dict(loc=tuple(c0 - hv0 * d + r0 * 0.3 + Vector((0, 0, 11.5))), target=tuple(c0 + Vector((0, 0, 12.5))),
                  lens=30, margin=15, near=5.0) for d in (CAM_D0, CAM_D1)]
    G = E.golgotha(ctx, mood="eclipse", dust=False, grass=0.45, bushes=0.3, rocks=0.45, near_detail=0.0, view=views)
    gz = G["ground_z"]
    cr = G["crosses"]["center"]
    base = Vector(cr["base"])
    # sky: continue the s14a/s14b transition (eclipse -> warm golden break, same overrides) to its end
    disk_a = dict(E.SKY_PRESETS["eclipse"]["sun_disk"], el=SUN_EL)
    over_b = dict(sun_az=SUN_AZ, sun_el=SUN_EL, key=0.22, strength=0.45, sun_energy=1.6, tint=(1.0, 0.84, 0.6),
                  sat=1.1, sun_tint=(1.0, 0.78, 0.5), sun_angle=1.0, haze_density=0.0009,
                  haze_tint=(1.0, 0.92, 0.8), exposure=0.3, grade="warm", clouds=0.5,
                  cloud_opts=dict(color=(0.95, 0.78, 0.55), shadow=(0.3, 0.2, 0.14), opacity=0.85, sun_glow=1.2,
                                  speed=(9.0, 3.0)),
                  sun_disk=dict(el=SUN_EL, size=1.0, color=(1.0, 0.88, 0.66), strength=40.0, glow=0.2))
    m0 = 0.72                                    # where s14b ends; fully golden ~75 % into this shot
    f1 = int(NR * 0.75)
    f0 = 1 - m0 * (f1 - 1) / (1 - m0)
    T = E.sky_transition(ctx, "eclipse", "eclipse", f0, f1, over_a=dict(sun_az=SUN_AZ, sun_el=SUN_EL, sun_disk=disk_a),
                         over_b=over_b, ease=False)
    sun = T["sun"]
    # the sun is the golden key everywhere; the cloud plane masks it (as in s14b)
    ad = sun.data.animation_data
    if ad and ad.action:
        for fc in C._fcurves(ad.action):
            if fc.data_path == "energy":
                for kp in fc.keyframe_points:
                    kp.co[1] = kp.handle_left[1] = kp.handle_right[1] = 3.2
            elif fc.data_path == "color":
                for kp in fc.keyframe_points:
                    kp.co[1] = kp.handle_left[1] = kp.handle_right[1] = GOLD_SUN[fc.array_index]
    sun.data.energy = 3.2
    sun.data.color = GOLD_SUN
    sun.data.angle = math.radians(2.5)
    sdir = Vector(T["b"]["sun_dir"]).normalized()
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
    _lean_baked(P.bake_static(j, decimate=0.5))   # distant: one frozen mesh, no rig/garments/beard/SSS

    # ------------------------------------------------------------------ the ash beasts
    ashm = _ash_material()
    lion = A.animal("lion", "roar", loc=tuple(at(0.95, -3.6)), rot_z=yaw_facing((right * 0.7 - hv * 0.7).normalized()),
                    fur=False, scale=1.05)
    A.play(lion, "roar", start_frame=1, speed=0.001, offset=1.75)        # frozen mid-roar, jaw wide
    ox = A.animal("bull", "toss", loc=tuple(at(-1.15, -3.3)), rot_z=yaw_facing((right * 0.75 - hv * 0.66).normalized()),
                  scale=1.0)
    A.play(ox, "toss", start_frame=1, speed=0.001, offset=1.3)                # frozen: head up, horns hooking high
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
    # The front sweeps screen right -> left (n = -right, perpendicular to the backlight), so on the beasts
    # it is a vertical plane: it reaches the lion's open mouth and the ox's horns first.
    top = G["hill_top"][2]
    H = top + 16.0
    n = -right
    Y = Vector((-n.y, n.x, 0))                              # occluder local +Y in world

    def arrival(obj):
        W = _world_verts(obj)
        return float((W @ np.array(n, np.float32)).min()), float((W @ np.array(n, np.float32)).max()), W

    def wob_at(W, wob):                                      # edge offset at the beast (sun-projected centre)
        c = Vector(W.mean(axis=0))
        q = c + sdir * ((H - c.z) / sdir.z)
        return float(wob(q.dot(Y)))

    occ, wob = _occluder("CloudShadow", n, H, seed=ctx.seed)
    lb, ob = _body(lion), _body(ox)
    la0, la1, Wl = arrival(lb)
    oa0, oa1, Wo = arrival(ob)
    wl, wo = wob_at(Wl, wob), wob_at(Wo, wob)
    fL0, fL1 = ctx.frame(p0["start"] + 0.05), ctx.frame(p0["end"] - 0.1)
    fO0, fO1 = ctx.frame(p1["start"] + 0.05), ctx.frame(p1["end"] - 0.1)
    vL = (la1 - la0) / (fL1 - fL0)
    vO = (oa1 - oa0) / (fO1 - fO0)
    # (frame, edge position along n): lit where P.n < e + wob
    # after the ox the front runs on out of frame, then stops (a static occluder lets EEVEE keep its
    # sun shadow pages -> cheaper last ~40 frames)
    fS = min(NR - 10, fO1 + 36)
    sched = [(1 - 60, la0 - wl - 60 * vL), (fL0, la0 - wl), (fL1, la1 - wl), (fO0, oa0 - wo), (fO1, oa1 - wo),
             (fS, oa1 - wo + (fS - fO1) * vO * 1.5), (NR + 40, oa1 - wo + (fS - fO1) * vO * 1.5)]
    for f, e in sched:
        occ.location = n * e + Vector((0, 0, H))
        occ.keyframe_insert("location", frame=f)
    C._set_interp(occ, "location", "LINEAR")
    # ash: the lib releases linearly along n over [min, max] of the mesh -> same schedule as the shadow edge
    wind = (-right * 1.7 + hv * 1.1 + Vector((0, 0, 1.4)))
    ash_col = (0.06, 0.052, 0.046)
    for body, (f0, f1), cnt, fs, seed in ((lb, (fL0, fL1), 14000, 0.009, 1), (ob, (fO0, fO1), 17000, 0.01, 2)):
        # pre-build the flake material under the lib's name so the gold glow lasts ~45 % of a flake's life
        nm = "FX_ash_%d_%s" % (seed, "_".join("%.2f" % c for c in tuple(ash_col) + tuple(GOLD) + (EDGE_GLOW,)))
        FX._ash_material(nm, ash_col, FLAKE_GLOW, 1.4, glow_age=0.3)   # embers: orange, not white sparks
        FX.ash_disintegrate(body, start_frame=f0, duration=(f1 - f0), direction=tuple(n), wind=tuple(wind), count=cnt,
                            flake_size=fs, life=3.0, jitter=0.12, glow_color=GOLD, glow=EDGE_GLOW, ash_color=ash_col,
                            turbulence=0.55, gravity=-0.1, seed=seed)

    # ------------------------------------------------------------------ camera: truck left with the light, rise
    look0 = at(0.15, -4.2) + Vector((0, 0, 0.75))           # slightly down: beasts mid-frame, crosses above
    look1 = Vector(cr["beam"]) + Vector((0, 0, 0.2))

    def cam_fn(f):
        u = C.ease_in_out(min(1.0, max(0.0, ctx.u(f))))
        b = C.ease_in_out(min(1.0, max(0.0, (f - (fO1 - 10)) / float(NR - (fO1 - 10)))))  # after the ox: tilt up
        d = CAM_D0 + (CAM_D1 - CAM_D0) * u
        loc = at(0.1 - 0.1 * u, -d) + Vector((0, 0, 1.0 + 0.35 * b))
        tgt = look0.lerp(look1, 0.55 * b)
        loc = loc + C.shake(f, 0.005, 0.45, 21)
        return (loc, tgt, 0.0, 30)

    cam = C.camera(tuple(at(0.1, -CAM_D0) + Vector((0, 0, 1.0))), tuple(look0), lens=30, name="Cam")
    C.animate_camera(cam, cam_fn, 1, NR)

    ctx.samples = 4
    ctx.render_opts.update({"volumetrics": "low", "shadow_scale": 0.5})
    ctx.interp = False
    ctx.post.update({"grade": "warm", "bloom": 0.38, "bloom_threshold": 0.62, "halation": 0.1, "caption": {"y": 0.72},
                     "end": {"grade": "gold", "bloom": 0.48}})
