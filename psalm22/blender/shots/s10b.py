"""s10b - Heart of wax: "My heart has turned to wax; it has melted within me."

Time-lapse: a single beeswax pillar candle melts down in deep darkness on a rough limestone ledge at
the foot of the cross. The guttering flame sinks with the top, drips run down the sides and the wax
spreads into a pool. Behind it, out of focus, the rough-hewn upright of the cross catches the warm
flicker so the frame is never a void. Slow push-in / tilt that keeps the sinking flame in place.

Lighting: the candle's own flickering flame lamp (FX) lights everything; a second lamp at the flame,
light-linked to the set only and flickering in sync, lifts the stone + wood without blowing out the
wax; a weak warm bounce (linked to the wax only) gives the body volume; a tiny shadowless lamp low
inside the candle imitates light leaking through the wax onto the pool.
"""
import math
import random
import bpy
from mathutils import Vector
from lib import core as C
from lib import fx as FX

SEED = 3
H0, H1 = 0.15, 0.04          # candle height start / end (m)
WAX = (0.78, 0.40, 0.085)    # honey beeswax
LIGHT_K = 3000               # lamp colour "as white-balanced by the camera" (the flame mesh keeps its own
                             # 1850 K blackbody); 1850 K lamps x orange wax went deep red -> salmon in AgX
FLICKER = 2.4                # guttering


def _linked(light, objs, name):
    coll = bpy.data.collections.new(name)
    for o in objs:
        coll.objects.link(o)
    light.light_linking.receiver_collection = coll
    return coll


def build(ctx):
    N = ctx.nframes
    # ---------------------------------------------------------------- world: near black, faintly warm
    C.world_color((0.0012, 0.0010, 0.0009), 1.0)

    # ---------------------------------------------------------------- set: stone ledge + cross upright
    set_objs = []
    ledge_mat = C.mat_pbr("rock_boulder_dry", scale=2.2, tint=(0.32, 0.27, 0.21), bump=1.0, name="s10b_ledge")
    # stone block; its front edge runs just in front of the candle so the lower frame (captions) is the
    # dark, rough front face of the block falling away into darkness
    ledge = C.box("Ledge", (1.3, 1.25, 0.5), (0.05, -0.115 + 0.625, -0.25), mat_=ledge_mat, bevel=0.015)
    C.displace(ledge, strength=0.016, scale=0.12, subdiv=4)
    set_objs.append(ledge)
    wood = C.wood_material("rough_wood", scale=2.0, tint=(0.42, 0.32, 0.24))
    upright = C.box("CrossUpright", (0.21, 0.2, 2.2), (-0.15, 0.62, 0.9), rot=(0, 0, 6), mat_=wood, bevel=0.012)
    C.displace(upright, strength=0.006, scale=0.06, subdiv=0)
    set_objs.append(upright)
    # a few loose stones / grit on the ledge so the surface reads as real
    stone_m = C.mat_pbr("rock_face_03", scale=12.0, tint=(0.5, 0.43, 0.36), name="s10b_pebble")
    rnd = random.Random(7)
    placed = 0
    while placed < 12:
        a = rnd.uniform(0, 2 * math.pi)
        r = rnd.uniform(0.11, 0.45)
        x, y = math.cos(a) * r, math.sin(a) * r * 0.9 + 0.05
        if y < -0.085:
            continue
        placed += 1
        i = placed
        s = rnd.uniform(0.005, 0.015)
        p = C.prim("ico_sphere", name="Pebble%d" % i, subdivisions=2, radius=1.0, loc=(x, y, s * 0.25))
        p.scale = (s * rnd.uniform(0.9, 1.6), s * rnd.uniform(0.8, 1.3), s * rnd.uniform(0.45, 0.8))
        p.rotation_euler = (0, 0, rnd.uniform(0, 6.28))
        C.assign(p, stone_m)
        C.shade_smooth(p)
        set_objs.append(p)

    # ---------------------------------------------------------------- the candle
    # pre-create the wax materials (melting_candle reuses materials by name): redder amber, softer glow
    FX.wax_material("FX_beeswax_%d" % SEED, WAX, glow_color=(1.0, 0.42, 0.08), glow=0.4, glow_depth=0.009,
                    rough=0.36, sss=0.4)
    FX.wax_material("FX_beeswax_pool_%d" % SEED, (0.45, 0.23, 0.045), glow_color=(1.0, 0.4, 0.08), glow=0.04,
                    glow_depth=0.004, rough=0.07, sss=0.08)
    f_end = N - 6
    e_flame = 1.8
    cand = FX.melting_candle((0, 0, 0), start_frame=1, end_frame=f_end, height=(H0, H1), radius=0.024,
                             drips=7, pool_radius=0.066, flame_size=0.032, flicker=FLICKER, light_energy=e_flame,
                             color=WAX, seed=SEED)

    # set lamp: rides with the flame, flickers in sync (same f-curve noise params as flame()), set only
    # (shadowless: a real flame is a big soft emitter and the wax is translucent, so the shadow ring the
    #  point lamp throws around the candle must stay soft and filled)
    cand.flame.light.data.shadow_soft_size = 0.010
    cand.flame.light.data.color = C.kelvin(LIGHT_K)
    # the wax body/drips don't block the flame lamp: a point lamp 2 cm above the rim would throw a hard
    # 20 cm black ring around the base that a real (tall, soft) flame through translucent wax never does
    for o in (cand.body, cand.drips):
        o.visible_shadow = False
    env_l = FX._point_light("SetLight", (0, 0, 0.032 * 0.42), 1.4, LIGHT_K, 0.02, False)
    FX._parent(env_l, cand.flame.root)
    env_l.location = (0, 0, 0.032 * 0.42)
    FX._light_flicker(env_l, 1.4, amount=min(0.45, 0.16 * FLICKER + 0.06), scale=4.0 + 2.0 / max(FLICKER, 0.3),
                      phase=SEED * 13.7 + 1)
    _linked(env_l, [upright], "s10b_set_recv")

    # warm bounce off the lit ledge onto the front of the wax (otherwise a black slab)
    bounce = C.light("AREA", (0.04, -0.3, 0.02), 0.22, temp=LIGHT_K - 400, target=(0, 0, 0.05), size=0.3, name="Bounce",
                     shadow=False)
    _linked(bounce, [cand.body, cand.drips, cand.pool], "s10b_wax_recv")
    # light through the wax: low inside the candle, weak, soft (the FX default is too hot at the base)
    gl = cand.glow_light
    if gl.animation_data:
        gl.animation_data_clear()
    gl.location = (0, 0, 0.012)
    gl.data.energy = 0.02
    gl.data.color = C.kelvin(LIGHT_K - 600)
    gl.data.shadow_soft_size = 0.02

    # ---------------------------------------------------------------- camera: push + tilt with the top
    cam = C.camera((0, -0.72, 0.16), (0, 0, 0.06), lens=60, fstop=4.0)

    def path(f):
        h = cand.height_at(min(f, f_end))
        m = (H0 - h) / (H0 - H1)                     # melt progress 0..1 (linear in time)
        u = C.ease_in_out(min(1.0, ctx.u(f))) * 0.6 + m * 0.4
        dist = 0.72 + (0.43 - 0.72) * u
        cz = 0.16 + (0.10 - 0.16) * u
        tz = 0.047 + (0.006 - 0.047) * u             # block edge stays above the caption band
        loc = Vector((0.015 * math.sin(u * 2.2), -dist, cz)) + C.shake(f, 0.0012, 0.4, 3)
        tgt = Vector((0, 0, tz))
        # focus on the flame / wick (the candle axis), slightly in front
        return (loc, tgt, 0.0, None, (Vector((0, 0, h)) - loc).length - 0.004)
    C.animate_camera(cam, path, 1, ctx.render_frames)

    ctx.samples = 4
    ctx.render_opts = {"volumetrics": "low", "exposure": 0.0, "shadow_scale": 0.5}
    # 12 fps + RIFE: the flame/lamp flicker is smooth f-curve noise (~5 Hz) and the melt is slow; validated
    # on a full-rate draft range (frames 41-55): mean 43.0 dB / SSIM 0.994 vs the real even frames, warp_err < 2
    ctx.interp = True
    ctx.post = {"grade": "candle", "bloom": 0.3, "vignette": 0.32, "caption": {"y": 0.72}}
