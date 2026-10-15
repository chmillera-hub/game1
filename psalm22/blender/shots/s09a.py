"""s09a - Bulls of Bashan: "Many bulls surround me; strong bulls of Bashan encircle me."

Symbolic nightmare. A red-brown dust storm on Golgotha under the darkened sun: massive black bulls
(Cape-buffalo 'bulls of Bashan') circle the crosses on the hill top. The camera sits almost on the
ground on the plateau, looking up at the cross with the dull red sun disk behind the crossbeam, and
slowly orbits (with a slow roll) against the herd's direction. Near bulls walk heavily through the
foreground (horns cutting across the red disk), an outer ring gallops in the haze behind the cross;
every hoof fall throws up dust.
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

DUST = (0.5, 0.33, 0.22)
R_CAM = 9.0


def _loc_at(obj, f):
    """World location of an object keyed by follow_path, evaluated from its f-curves (no frame_set)."""
    ad = obj.animation_data
    v = Vector(obj.location)
    if ad and ad.action:
        for fc in C._fcurves(ad.action):
            if fc.data_path == "location":
                v[fc.array_index] = fc.evaluate(f)
    return v


def _ring(center, r, a0_deg, ccw, n=96, turns=1.3):
    return A.circle_path(center, r, start_deg=a0_deg, turns=turns, clockwise=not ccw, n=n)


def _hoof_dust(events, fps, wind, seed=0):
    """All hoof-fall dust of the shot as ONE closed-form particle object (fx particle tree):
    events = [(x, y, z, frame, size, heading_vec)] -> soft billboard puffs kicked out and up,
    growing, drifting with the storm wind and fading."""
    rng = np.random.default_rng(seed)
    P0, V0, B, L, S = [], [], [], [], []
    for (x, y, z, f, size, fwd) in events:
        n = 9
        rd = rng.normal(0, 1, (n, 3))
        rd /= np.linalg.norm(rd, axis=1, keepdims=True)
        rd[:, 2] = np.abs(rd[:, 2]) * 0.5 + 0.2
        v = rd * rng.uniform(0.8, 2.6, (n, 1)) * size
        v[:, :2] -= np.array(fwd[:2]) * 0.6          # thrown back from the hooves
        p = np.array([x, y, z]) + rng.normal(0, 0.35, (n, 3)) * np.array([1, 1, 0.1]) * size
        p[:, 0] += np.array(fwd[0]) * rng.uniform(-0.9, 0.6, n)
        p[:, 1] += np.array(fwd[1]) * rng.uniform(-0.9, 0.6, n)
        P0.append(p)
        V0.append(v)
        B.append((f - 1) / fps + rng.uniform(0, 0.12, n))
        L.append(rng.uniform(1.8, 3.0, n))
        S.append(rng.uniform(0.25, 0.5, n) * size)
    P0, V0 = np.concatenate(P0), np.concatenate(V0)
    B, L, S = np.concatenate(B), np.concatenate(L), np.concatenate(S)
    mat = FX._spray_material("s09a_dust", color=DUST, opacity=0.55, glow=0.14, soft=1.4)
    src = FX._cached_src("FX_src_quad", lambda: FX._quad("FX_src_quad"))
    o, _ = FX._particles("HoofDust", P0, V0, B, L, S, mat, gravity=(0, 0, 0.05), drag=2.2, wind=wind,
                         turb=0.45, turb_scale=0.6, turb_speed=0.4, grow=3.2, fade_in=0.08, fade_out=0.65,
                         mode=3, instance=src, spin=0.3, seed=seed + 1)
    return o



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
    # layout is relative to the eclipse sun (camera looks into it); known before the env is built
    az = math.radians(E.SKY_PRESETS["eclipse"]["sun_az"])
    hv0 = Vector((math.sin(az), -math.cos(az)))
    c0 = Vector((0.0, 0.6))
    side0 = math.degrees(math.atan2(-hv0.y, -hv0.x))
    views = []
    for da in (15, 0, -15):
        a = math.radians(side0 + da)
        lo = c0 + Vector((math.cos(a), math.sin(a))) * R_CAM
        views.append(dict(loc=(lo.x, lo.y, 11.0), target=(c0.x, c0.y, 13.0), lens=30, margin=22, near=6.0))
    # the storm hides everything beyond ~30 m: no city, no far shrubs/olives, sparse grass
    G = E.golgotha(ctx, mood="eclipse", crosses=3, grass=0.4, bushes=0.0, rocks=0.45, near_detail=0.0,
                   city=False, view=views,
                   sky_over=dict(sun_disk=dict(el=24, size=3.2, color=(1.0, 0.28, 0.07), strength=40.0, glow=0.5)))
    ground = G["ground"]
    cr = G["crosses"]["center"]
    base = Vector(cr["base"])
    cxy = Vector((base.x, base.y))
    sky = G["sky"]
    sdir = Vector(sky["sun_dir"])
    hv = Vector((sdir.x, sdir.y)).normalized()  # horizontal direction towards the sun
    gz = lambda x, y: float(ground(x, y))

    # ------------------------------------------------------------------ the crucified figure (silhouette)
    j = P.make_person("jesus", "JESUS_CROSS", lod="mid", hair_strands=False)
    P.place_on_cross(j, cr["root"], head="side", strain=0.75)
    _lean_baked(P.bake_static(j, decimate=0.5))   # distant: one frozen mesh, no rig/garments/beard/SSS

    # ------------------------------------------------------------------ dust storm
    top = G["hill_top"][2]
    wdir = Vector((1.0, 0.35, 0.0)).normalized()
    E.dust_storm(ctx, color=DUST, density=0.036, speed=7.0, center=(0, -5, top - 6), size=(120, 120, 30),
                 direction=tuple(wdir), motes=False)

    # ------------------------------------------------------------------ bulls
    bull_coll = bpy.data.collections.new("s09a_bulls")
    bpy.context.scene.collection.children.link(bull_coll)
    bulls = []
    cam_side = math.degrees(math.atan2(-hv.y, -hv.x))      # angle of the camera side (opposite the sun)
    R1 = 6.4                                     # outside the side crosses (~4.7 m)
    # phases: the shot opens on the cross + sun, the first bull crosses close on "many bulls"
    inner = [(cam_side - 84, 1.25, 1.18), (cam_side - 26, 1.35, 1.25), (cam_side + 40, 1.2, 1.12),
             (cam_side + 104, 1.3, 1.2), (cam_side + 165, 1.25, 1.15), (cam_side - 144, 1.3, 1.16)]
    for i, (a0, spd, scl) in enumerate(inner):
        arm = A.animal("bull", "walk", speed=spd, scale=scl, tint=(-0.35, -0.35, -0.33), offset=i * 0.31)
        v = A.ground_speed("bull", "walk", 0, spd) * scl
        A.follow_path(arm, _ring(cxy, R1 + 0.3 * (i % 2), a0, True), v, 1, NR, ground=gz)
        bulls.append((arm, "walk", spd, scl))
    R2 = 11.0
    outer = [(cam_side + 160, 0.8, 1.15), (cam_side + 205, 0.75, 1.1), (cam_side + 250, 0.8, 1.2),
             (cam_side + 295, 0.78, 1.12)]                 # far side only (the near side is the cliff edge)
    for i, (a0, spd, scl) in enumerate(outer):
        arm = A.animal("bull", "run", speed=spd, scale=scl, tint=(-0.35, -0.35, -0.33), offset=i * 0.17)
        v = A.ground_speed("bull", "run", 0, spd) * scl
        A.follow_path(arm, _ring(cxy, R2 + 0.6 * i, a0, False, turns=0.8), v, 1, NR, ground=gz)
        bulls.append((arm, "run", spd, scl))
    for arm, *_ in bulls:
        for ch in arm.children:
            if ch.type == "MESH" and not ch.name.startswith("eyes"):
                bull_coll.objects.link(ch)

    # hoof dust (one particle object for the whole herd)
    wind = tuple(wdir * 2.6 + Vector((0, 0, 0.2)))
    events = []
    for k, (arm, act, spd, scl) in enumerate(bulls):
        T = (1.45 if act == "walk" else 0.6) / spd
        step = T / 2.0
        t = (k % 3) * 0.11 - 1.0                      # start before the shot: dust already hanging
        while t < NR / fps:
            f = 1 + t * fps
            p = _loc_at(arm, max(1, f))
            p2 = _loc_at(arm, max(1, f) + 2)
            fwd = (p2 - p)
            fwd = fwd.normalized() if fwd.length > 1e-6 else Vector((0, -1, 0))
            if f < 1:
                p = p - fwd * (1 - f) / fps * A.ground_speed("bull", act, 0, spd) * scl
            events.append((p.x, p.y, gz(p.x, p.y) + 0.05, f, 0.8 if act == "walk" else 1.0, tuple(fwd)))
            t += step
    _hoof_dust(events, fps, wind, seed=ctx.seed)

    # ------------------------------------------------------------------ light: dull sun + rim on the herd
    sun = sky["sun"]
    sun.data.energy = 0.8
    sun.data.use_shadow = False      # dim backlight: its shadows are invisible in the dust, but cost ~50% of the frame
    rim = C.light("SUN", (0, 0, 30), energy=6.0, color=(1.0, 0.45, 0.2), name="BullRim", shadow=False)
    rd = (Vector((hv.x, hv.y, 0)) * math.cos(math.radians(14)) + Vector((0, 0, math.sin(math.radians(14))))).normalized()
    rim.rotation_euler = (-rd).to_track_quat("-Z", "Y").to_euler()
    rim.data.angle = math.radians(4)
    rim.light_linking.receiver_collection = bull_coll

    # ------------------------------------------------------------------ camera: ground level, slow orbit + roll
    look_z = cr["beam_z"] + 0.05
    R_cam = R_CAM

    gzx = lambda x, y: float(G["ground_z"](x, y))           # exact (terrain + cliff top) for the camera

    def cam_fn(f):
        u = C.ease_in_out(min(1.0, max(0.0, ctx.u(f))))
        a = math.radians(cam_side + 15 - 30 * u)
        loc = Vector((cxy.x + math.cos(a) * R_cam, cxy.y + math.sin(a) * R_cam, 0))
        loc.z = gzx(loc.x, loc.y) + 0.42
        tgt = Vector((cxy.x, cxy.y, look_z - 0.3))
        loc = loc + C.shake(f, 0.012, 0.7, 3)
        roll = -4.0 + 8.0 * u
        return (loc, tgt, roll, 30)

    cam = C.camera((0, -8, top), (0, 0, top + 3), lens=30, name="Cam")
    C.animate_camera(cam, cam_fn, 1, NR)

    ctx.samples = 4
    ctx.render_opts.update({"volumetrics": "low", "shadow_scale": 0.5})
    ctx.interp = False
    ctx.post.update({"grade": "eclipse", "bloom": 0.25, "vignette": 0.3})
