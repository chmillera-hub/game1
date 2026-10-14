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
    sky = E.sky("eclipse", ctx=ctx)
    sun = sky["sun"]
    sun.data.energy = 0.25
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
    hero_start = P(0.05, 5.6)
    hero = A.animal("lion", "stalk", loc=tuple(hero_start), rot_z=yaw, speed=1.9, start_frame=1, move=True,
                    end_frame=ROAR + 4, eye_glow=0.55)
    st = A.play(hero, "roar", start_frame=ROAR, replace=False)
    st.repeat = 1.0
    hero_end = hero.location.copy()

    # second male, left, half in the dust; roars later
    l2 = A.animal("lion", "stalk", loc=tuple(P(-2.3, 8.2)), rot_z=yaw - 18, speed=1.6, start_frame=1, move=True,
                  end_frame=int(ctx.frame(3.2)), eye_glow=0.9, fur=0.35, offset=0.7)
    s2 = A.play(l2, "roar", start_frame=int(ctx.frame(2.9)), replace=False)
    s2.repeat = 1.0
    # third, right, further back, walking in
    l3 = A.animal("lion", "stalk", loc=tuple(P(2.6, 10.5)), rot_z=yaw + 24, speed=1.7, start_frame=1, move=True,
                  eye_glow=1.0, fur=0.3, offset=1.3)
    # lioness (static roaring pose) further back right
    l4 = A.load("lion", variant=1, loc=tuple(P(4.2, 13.5)), rot_z=yaw + 35, scale=1.0)
    for a in (hero, l2, l3, l4):
        for o in _cat_parts(a):
            cats.objects.link(o)

    # ------------------------------------------------------------------ light
    # hard warm rims from the dim sun through the dust (linked to the cats only)
    rimL = C.light("AREA", tuple(P(-2.2, 9.0) + Vector((0, 0, 2.6))), 650, color=(1.0, 0.5, 0.25), size=1.6,
                   target=tuple(P(0, 3.0) + Vector((0, 0, 1.1))), name="RimL")
    rimR = C.light("AREA", tuple(P(2.6, 8.5) + Vector((0, 0, 2.0))), 480, color=(1.0, 0.45, 0.22), size=1.4,
                   target=tuple(P(0, 3.0) + Vector((0, 0, 1.1))), name="RimR")
    rimS = C.light("SUN", (0, 0, 20), 2.4, color=(1.0, 0.42, 0.2), name="RimSun", shadow=True)
    rd = (fwd * math.cos(math.radians(18)) + Vector((0, 0, math.sin(math.radians(18))))).normalized()
    rimS.rotation_euler = (-rd).to_track_quat("-Z", "Y").to_euler()
    for L in (rimL, rimR, rimS):
        L.light_linking.receiver_collection = cats
    # faint red-brown fill from low camera-left (sky bounce) so the open mouth and teeth read
    fill = C.light("AREA", tuple(P(-1.6, -0.6) + Vector((0, 0, 0.6))), 26, color=(1.0, 0.62, 0.45), size=2.5,
                   target=tuple(P(0, 3.0) + Vector((0, 0, 1.1))), name="Fill", shadow=False)
    fill.light_linking.receiver_collection = cats

    # ------------------------------------------------------------------ dust
    wind = right * -1.6 + Vector((0, 0, 0.1))
    E.fog_volume(tuple(P(0, 12) + Vector((0, 0, 4))), (40, 34, 8), 0.06, DUST, 0.55, noise_scale=0.18,
                 noise_amount=0.9, height_falloff=0.12, name="DustFar", wind=tuple(wind * 2))
    E.fog_volume(tuple(P(0, 4) + Vector((0, 0, 1.0))), (14, 12, 2.0), 0.05, DUST, 0.4, noise_scale=0.6,
                 noise_amount=1.0, height_falloff=1.2, name="DustLow", wind=tuple(wind * 3))
    E._set_volume_range(60)
    E.dust_motes(center=tuple(P(0, 3.2) + Vector((0, 0, 1.4))), size=(5, 6, 2.8), count=1800, radius=0.0022,
                 color=(1.0, 0.75, 0.5), emission=0.25, drift=tuple(wind), turbulence=0.5, seed=5, name="Motes")
    # roar breath blasts the dust in front of the mouth
    mouth_ground = Vector(hero_end) - fwd * 1.3
    FX.dust_burst((mouth_ground.x, mouth_ground.y, 0.02), int(ctx.frame(p1["start"] - 0.1)), size=0.9,
                  color=DUST, count=40, grains=600, direction=tuple(-fwd * 0.8 + Vector((0, 0, 0.4))),
                  wind=tuple(-fwd * 0.6 + wind * 0.5), opacity=0.5, life=2.4, seed=11, name="RoarDust")

    # ------------------------------------------------------------------ camera: low, slight push, roar shake
    cam_base = P(0.0, -0.2) + Vector((0, 0, 0.95))

    def cam_fn(f):
        u = C.ease_in_out(min(1.0, ctx.u(f)))
        loc = cam_base + fwd * (0.35 * u)
        tgt = P(0.0, 4.0) + Vector((0, 0, 1.16 + 0.05 * u))
        # tremor while the lion roars
        t = ctx.sec(f)
        k = max(0.0, min(1.0, (t - p1["start"]) / 0.25)) * max(0.0, min(1.0, (p1["start"] + 1.6 - t) / 0.5))
        loc = loc + C.shake(f, 0.006 + 0.012 * k, 0.9 + 3.0 * k, 9)
        return (loc, tgt, 0.0, 42, 2.6)

    cam = C.camera(tuple(cam_base), tuple(P(0, 4) + Vector((0, 0, 1.15))), lens=42, fstop=2.8, focus=2.6, name="Cam")
    C.animate_camera(cam, cam_fn, 1, NR)
    # focus follows the hero's head
    dof = cam.data.dof
    for f in range(1, NR + 1, 4):
        hl = Vector(hero_start).lerp(hero_end, min(1.0, (f - 1) / max(1, ROAR + 3)))
        loc = cam_base + fwd * (0.35 * C.ease_in_out(min(1.0, ctx.u(f))))
        dof.focus_distance = max(0.5, (hl - fwd * 1.0 + Vector((0, 0, 1.15)) - loc).length)
        dof.keyframe_insert("focus_distance", frame=f)

    ctx.samples = 6
    ctx.render_opts.update({"volumetrics": "low"})
    ctx.interp = False
    ctx.post.update({"grade": "eclipse", "bloom": 0.3, "vignette": 0.34})
