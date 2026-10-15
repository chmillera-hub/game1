"""s09b - Roaring lions: "Roaring lions that tear their prey open their mouths wide against me."

Continuation of the s09a nightmare (eclipse darkness, red-brown dust). Out of the dark dust, lions
emerge with glinting eyes; the male lion stalks straight at the low camera, draws back and roars into
the lens, jaw wide open on "open their mouths wide" (~2.6-4.1 s), the breath blasting the dust on the
ground. Two more lions and a lioness loom behind in the haze. Hard warm rim light from the dim sun
behind them (light-linked to the cats), a faint red fill from the side, eyeshine.
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from lib import core as C
from lib import env as E
from lib import assets as A
from lib import fx as FX

DUST = (0.5, 0.33, 0.22)
DUST_DARK = (0.3, 0.19, 0.13)
TINT = (-0.3, -0.34, -0.36)          # darker, dustier coats in the gloom


def _hide_eyes(arm):
    for c in arm.children:
        if c.name.startswith("eyes"):
            c.hide_render = True


def _cat_parts(arm):
    return [c for c in arm.children if c.type in ("MESH", "CURVES") and not c.name.startswith("eyes")]


def build(ctx):
    NR = ctx.render_frames
    fps = ctx.fps
    p0, p1 = ctx.phrases[0], ctx.phrases[1]

    # ------------------------------------------------------------------ world: the darkened sun, dust
    sky = E.sky("eclipse", ctx=ctx, bg=0.3)       # darker visible sky: the lions come out of the dark
    sun = sky["sun"]
    sun.data.energy = 0.25
    sun.data.use_shadow = False          # dim; its shadows don't read in the dust (saves a lot of frame time)
    sdir = Vector(sky["sun_dir"])
    hv = Vector((sdir.x, sdir.y)).normalized()
    # camera looks along +Y-ish towards the sun (lions backlit); rotate the layout so that holds exactly
    fwd = Vector((hv.x, hv.y, 0))                 # camera -> lions
    right = Vector((fwd.y, -fwd.x, 0))
    yaw = math.degrees(math.atan2(-fwd.x, fwd.y))   # animal rot_z facing the camera (front = -Y)

    gmat = C.mat_pbr("dry_ground_rocks", scale=0.45, tint=(0.62, 0.45, 0.36), name="s09b_ground")
    E.hazify(gmat)
    g = C.ground_plane(size=160, mat_=gmat, z=0.0, name="Ground")
    E.add_ground(g)
    # a few boulders out in the dust
    E.scatter(E.rock_protos("boulders"), count=26, seed=3, scale=(0.4, 1.3), align=0.6, sink=-0.3,
              region=(-25, 4, 25, 40), exclude=[(0, 6, 3.5)], name="Boulders")
    E.scatter(E.rock_protos("rocks"), count=220, seed=4, scale=(0.6, 1.6), align=0.9, sink=-0.3,
              region=(-12, -2, 12, 30), exclude=[(0, 4, 1.4)], name="Rocks")
    E.release_bvh()

    def P(dx, dy):                       # layout coordinates: x = right, y = away from the camera
        return right * dx + fwd * dy

    # ------------------------------------------------------------------ lions
    cats = bpy.data.collections.new("s09b_cats")
    bpy.context.scene.collection.children.link(cats)
    ROAR = int(round(ctx.frame(p1["start"] - 1.05)))     # jaw fully open ~0.45 s after the phrase starts
    hero_start = P(0.1, 5.3)
    hero = A.animal("lion", "stalk", loc=tuple(hero_start), rot_z=yaw, speed=2.5, start_frame=1, move=True,
                    end_frame=ROAR + 4, eye_glow=0.55, fur=0.65, tint=TINT)
    st = A.play(hero, "roar", start_frame=ROAR, replace=False)
    st.repeat = 1.0
    hero_end = hero.location.copy()

    # second male, left, half in the dust; roars later
    l2 = A.animal("lion", "stalk", loc=tuple(P(-1.9, 8.4)), rot_z=yaw - 14, speed=1.8, start_frame=1, move=True,
                  end_frame=int(ctx.frame(3.2)), eye_glow=1.0, fur=False, offset=0.7, tint=TINT)
    s2 = A.play(l2, "roar", start_frame=int(ctx.frame(2.9)), replace=False)
    s2.repeat = 1.0
    # third, right, further back, walking in
    l3 = A.animal("lion", "stalk", loc=tuple(P(2.1, 10.2)), rot_z=yaw + 20, speed=1.8, start_frame=1, move=True,
                  eye_glow=1.0, fur=False, offset=1.3, tint=TINT)
    # lioness (static roaring pose) further back right
    l4 = A.load("lion", variant=1, loc=tuple(P(3.4, 13.0)), rot_z=yaw + 35, scale=1.0)
    for a in (hero, l2, l3, l4):
        for o in _cat_parts(a):
            cats.objects.link(o)

    # ------------------------------------------------------------------ light
    # hard warm rims from the dim sun through the dust (linked to the cats only; little fog glow)
    tg = P(0.2, 3.4) + Vector((0, 0, 1.0))
    rimL = C.light("AREA", tuple(P(-1.8, 7.5) + Vector((0, 0, 2.4))), 700, color=(1.0, 0.5, 0.25), size=1.2,
                   target=tuple(tg), name="RimL", volume=0.0, shadow=False)
    rimR = C.light("AREA", tuple(P(2.2, 7.2) + Vector((0, 0, 2.0))), 520, color=(1.0, 0.45, 0.22), size=1.0,
                   target=tuple(tg), name="RimR", volume=0.0, shadow=False)
    rimS = C.light("SUN", (0, 0, 20), 2.4, color=(1.0, 0.42, 0.2), name="RimSun", shadow=False, volume=0.3)
    rd = (fwd * math.cos(math.radians(18)) + Vector((0, 0, math.sin(math.radians(18))))).normalized()
    rimS.rotation_euler = (-rd).to_track_quat("-Z", "Y").to_euler()
    for L in (rimL, rimR, rimS):
        L.light_linking.receiver_collection = cats
    # the cats walk out of the dark into the light
    for L, e in ((rimL, 700), (rimR, 520), (rimS, 2.4)):
        L.data.energy = e * 0.25
        L.data.keyframe_insert("energy", frame=1)
        L.data.energy = e
        L.data.keyframe_insert("energy", frame=int(ctx.frame(1.4)))
    # dim red-brown fill from low camera-left (sky bounce) so the open mouth and teeth read
    fill = C.light("AREA", tuple(P(-1.2, 0.6) + Vector((0, 0, 0.45))), 14, color=(1.0, 0.6, 0.42), size=1.5,
                   target=tuple(tg + Vector((0, 0, 0.2))), name="Fill", shadow=False, volume=0.0)
    fill.light_linking.receiver_collection = cats
    fill.data.energy = 3
    fill.data.keyframe_insert("energy", frame=1)
    fill.data.energy = 14
    fill.data.keyframe_insert("energy", frame=int(ctx.frame(1.6)))

    # ------------------------------------------------------------------ dust
    wind = right * -1.6 + Vector((0, 0, 0.1))
    E.fog_volume(tuple(P(0, 12) + Vector((0, 0, 4))), (40, 34, 8), 0.07, DUST_DARK, 0.55, noise_scale=0.18,
                 noise_amount=0.9, height_falloff=0.12, name="DustFar", wind=tuple(wind * 2))
    E.fog_volume(tuple(P(0, 6) + Vector((0, 0, 1.0))), (14, 10, 2.0), 0.035, DUST, 0.4, noise_scale=0.6,
                 noise_amount=1.0, height_falloff=1.2, name="DustLow", wind=tuple(wind * 3))
    E._set_volume_range(60)
    E.dust_motes(center=tuple(P(0, 4.2) + Vector((0, 0, 1.4))), size=(5, 5, 2.8), count=700, radius=0.0016,
                 color=(1.0, 0.75, 0.5), emission=0.25, drift=tuple(wind), turbulence=0.5, seed=5, name="Motes")
    # roar breath blasts the dust in front of the mouth
    mouth_ground = Vector(hero_end) - fwd * 1.3
    FX.dust_burst((mouth_ground.x, mouth_ground.y, 0.02), int(ctx.frame(p1["start"] - 0.1)), size=0.9,
                  color=DUST, count=40, grains=0, direction=tuple(-fwd * 0.8 + Vector((0, 0, 0.4))),
                  wind=tuple(-fwd * 0.6 + wind * 0.5), opacity=0.5, life=2.4, seed=11, name="RoarDust")

    # ------------------------------------------------------------------ camera: low, slight push, roar shake
    cam_base = P(-0.38, -0.2) + Vector((0, 0, 0.72))         # a little left: the lion comes in 3/4

    def cam_fn(f):
        u = C.ease_in_out(min(1.0, ctx.u(f)))
        loc = cam_base + fwd * (0.3 * u)
        tgt = P(0.02, 3.6) + Vector((0, 0, 1.12 + 0.06 * u))
        # tremor while the lion roars
        t = ctx.sec(f)
        k = max(0.0, min(1.0, (t - p1["start"]) / 0.25)) * max(0.0, min(1.0, (p1["start"] + 1.6 - t) / 0.5))
        loc = loc + C.shake(f, 0.005 + 0.01 * k, 0.9 + 3.0 * k, 9)
        return (loc, tgt, 0.0, 40)

    cam = C.camera(tuple(cam_base), tuple(P(0, 4) + Vector((0, 0, 1.15))), lens=40, fstop=2.8, focus=2.6, name="Cam")
    C.animate_camera(cam, cam_fn, 1, NR)
    # focus follows the hero's head
    dof = cam.data.dof
    for f in range(1, NR + 1, 3):
        hl = Vector(hero_start).lerp(Vector(hero_end), min(1.0, (f - 1) / max(1, ROAR + 3)))
        loc = cam_base + fwd * (0.3 * C.ease_in_out(min(1.0, ctx.u(f))))
        dof.focus_distance = max(0.5, (hl - fwd * 1.0 + Vector((0, 0, 1.15)) - loc).length)
        dof.keyframe_insert("focus_distance", frame=f)
    # during the roar the head turns towards the lens (mouth wide straight at us)
    hb = hero.pose.bones["head"]
    tr = hb.constraints.new("DAMPED_TRACK")
    tr.target = cam
    tr.track_axis = "TRACK_Y"
    for f, v in ((1, 0.0), (ROAR + 6, 0.0), (ROAR + 18, 0.6), (ROAR + 62, 0.6), (ROAR + 80, 0.25)):
        tr.influence = v
        tr.keyframe_insert("influence", frame=f)

    ctx.samples = 5
    ctx.render_opts.update({"volumetrics": "low", "shadow_scale": 0.5})
    ctx.interp = True        # validated: RIFE on draft 41-65 (stalk + roar) warp_err 1.3-1.8, 37.7 dB mean
    ctx.post.update({"grade": "eclipse", "exposure": 0.0, "bloom": 0.3, "vignette": 0.34})
