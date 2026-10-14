"""s01b - "So far": "Why are you so far from saving me, so far from my cries of anguish?"

Cut in from s01a (close-up of the face on the cross as the light dims). The camera starts on a
medium-wide of the crucified figure, low on the plateau and directly down-sun, so the figure hangs
against the dimming sun; it then pulls straight away from the sun - rising and receding (log-distance,
i.e. a constant rate of shrinking) over the skull cliff until the three crosses are a speck on the hill
beneath a vast sky. The sky keeps darkening (golden -> eclipse cross-fade, already ~1/3 through at the
cut) and the sun ends as a dull red disk behind clouds, straight above the tiny crosses.
"""
import math
import bpy
from mathutils import Vector
from lib import core as C
from lib import env as E
from lib import characters as P
from lib import wardrobe as W

SUN_AZ = 140.0     # presets use 165 (over Jerusalem); 25 deg further west so the down-sun pull-back sees the
                   # skull scarp obliquely (frontal, it reads as a flat box from afar)
SUN_EL = 30.0      # a little higher than the presets (24): the disk sits well above the far crosses


def _hazify_person(p):
    seen = set()
    for o in p.objects():
        if o.type not in ("MESH", "CURVES", "CURVE"):
            continue
        for m in getattr(o.data, "materials", []) or []:
            if m is not None and m.name not in seen:
                seen.add(m.name)
                E.hazify(m)


def clamp_camera_sky(tr, side="a", mult=1.5):
    """sky_transition() does not apply the presets' clamp_sun to the camera branch, so the golden HDRI's
    own (low, 7 deg) sun shows next to the procedural disk. Insert the same DARKEN clamp sky() uses."""
    nt = bpy.context.scene.world.node_tree
    ms = next(n for n in nt.nodes if n.type == "MIX_SHADER" and n.inputs[2].is_linked)
    bgc = ms.inputs[2].links[0].from_node
    cam_mix = bgc.inputs[0].links[0].from_node
    scaled = cam_mix.inputs[6 if side == "a" else 7].links[0].from_node
    src = scaled.inputs[6].links[0].from_socket
    cc = nt.nodes.new("ShaderNodeMix")
    cc.data_type = "RGBA"
    cc.blend_type = "DARKEN"
    cc.inputs[0].default_value = 1.0
    cv = max(tr[side]["clamp"], 1e-3) * mult
    cc.inputs[7].default_value = (cv, cv, cv, 1)
    nt.links.new(src, cc.inputs[6])
    nt.links.new(cc.outputs[2], scaled.inputs[6])
    return cc


def _dressed(p, part="loincloth"):
    return any(str(o.get("wardrobe", "")) == part or part in o.name for o in p.garments)


def build(ctx):
    N, NR = ctx.nframes, ctx.render_frames

    # ------------------------------------------------------------------ environment + sky
    A = E.golgotha(ctx, mood="eclipse", grass=0.6, dust=False, near_detail=0.4)
    # The darkening is built as eclipse -> eclipse: side A is the same overcast HDRI + cloud layer, but bright,
    # warm and thin (the veiled sun at the end of s01a); side B is the env 'eclipse' preset. One HDRI and one
    # cloud pattern for both sides: the clouds thicken in place and there is only ever one sun disk
    # (the golden preset's HDRI has its own sun at 7 deg, which sky_transition shows next to the disk).
    over_a = dict(sun_az=SUN_AZ, sun_el=SUN_EL, key=0.36, strength=0.55, sun_energy=3.4, tint=(1.0, 0.82, 0.6),
                  sat=1.0, sun_tint=(1.0, 0.8, 0.56), sun_angle=1.2, haze_density=0.0005,
                  haze_tint=(1.0, 0.95, 0.88), fog=(1.0, 0.84, 0.62), exposure=0.0, grade="warm", clouds=0.55,
                  cloud_opts=dict(color=(0.8, 0.72, 0.64), shadow=(0.3, 0.25, 0.22), opacity=0.85, sun_glow=1.2,
                                  speed=(9.0, 3.0)),
                  sun_disk=dict(el=SUN_EL, size=0.9, color=(1.0, 0.86, 0.62), strength=70.0, glow=0.3))
    over_b = dict(sun_az=SUN_AZ, sun_el=SUN_EL,
                  sun_disk=dict(E.SKY_PRESETS["eclipse"]["sun_disk"], el=SUN_EL))
    # darkening already ~35 % through at the cut (s01a dims the light), complete by the end of phrase 2.
    # Two Bezier keys = smoothstep; place f0 before the shot so frame 1 sits at 0.35.
    f_dark = int(ctx.frame(ctx.phrases[-1]["end"])) + 2
    f0 = int(round((1 - 0.40 * f_dark) / 0.60))
    E.sky_transition(ctx, "eclipse", "eclipse", f0, f_dark, over_a=over_a, over_b=over_b)
    sun_dir = E._dir_from_az_el(SUN_AZ, SUN_EL)

    # ------------------------------------------------------------------ the crucified
    cx = A["crosses"]
    j = P.make_person("jesus", "JESUS_CROSS", pose=None, hair_strands=False)
    P.place_on_cross(j, cx["center"]["root"], head="up", strain=0.65)
    try:   # settle the loincloth on the hanging pose (the skinned rest fit pokes the crossed thigh through)
        W.drape(j, [g for g in j.garments if "loincloth" in g.name], frames=25, ramp=15, ground=None)
    except Exception as e:
        print("s01b WARNING: drape failed:", e)
    P.expression(j, "anguish")
    P.eyes_look(j, j.eye_pos() + Vector((0.2, 1.0, 4.0)))
    thieves = []
    for k, seed, head, expr, ks in (("left", 4, "down", "exhausted", -1.0), ("right", 9, "side", "pain", 1.0)):
        t = P.make_person("thief_" + k, "CROWD_MAN", seed=seed, outfit=["loincloth"], outfit_colors={"loincloth": "oatmeal"},
                          pose=None, lod="mid", hair_strands=False, dirt=0.5, sweat=0.4, age_years=30 + seed)
        P.place_on_cross(t, cx[k]["root"], head=head, strain=0.75, knee_side=ks)
        P.expression(t, expr)
        thieves.append(t)
    for p in [j] + thieves:
        _hazify_person(p)
    dressed = _dressed(j) and all(_dressed(t) for t in thieves)
    if not dressed:
        print("s01b WARNING: wardrobe failed - starting wider (silhouettes only)")

    # ------------------------------------------------------------------ camera: pull away from the sun
    c = cx["center"]
    cz = c["base"][2]
    base = Vector((c["base"][0], c["base"][1], 0))
    chest = Vector(c["chest"]) + Vector((0, 0, 0.2))
    top = Vector((c["base"][0], c["base"][1], cz + 3.2))
    sun_h = math.atan2(sun_dir.x, -sun_dir.y)                    # core azimuth of the sun (radians)
    d0 = 6.3 if dressed else 18.0
    d1 = 88.0
    lens0, lens1 = 34.0, 20.0
    f_end = N + 6

    def path(f):
        u = min(1.0, max(0.0, (f - 1) / float(f_end - 1)))
        # log-distance (constant shrink rate) with a soft start (cut on motion) and a long glide out
        s = 0.2 * u + 0.8 * C.smoothstep(1.0 - (1.0 - u) ** 1.6)
        d = d0 * (d1 / d0) ** s
        az = sun_h + math.radians(7.0) * (1.0 - C.smoothstep(min(1.0, s * 1.4)))   # 3/4 -> straight down-sun
        away = -Vector((math.sin(az), -math.cos(az), 0))
        loc = base + away * d
        # off the edge of the plateau (the ground falls away 11 m beneath the camera, a sudden rise),
        # then sinking towards the plain so the three crosses end up above the city skyline, against the sky
        rise = 1.0 * C.smoothstep((d - d0) / 9.0)
        drop = (cz + 2.6 - 4.6) * C.smoothstep((d - 15.0) / (d1 - 15.0))
        loc.z = cz + 1.6 + rise - drop
        lens = lens0 + (lens1 - lens0) * C.smoothstep(s)
        w = C.smoothstep(min(1.0, s * 2.2))
        tgt = chest.lerp(top, w)
        # lift the aim so the crosses settle low in the frame (~0.6 H) under a vast sky
        tgt = tgt + Vector((0, 0, (loc - tgt).length * 0.17 * C.smoothstep(s)))
        loc = loc + C.shake(f, 0.008 + 0.04 * s, 0.3, 3)
        return (loc, tgt, 0.0, lens)

    cam = C.camera(loc=(0, -6, cz + 1), target=tuple(chest), lens=lens0, clip_end=20000)
    C.animate_camera(cam, path, 1, NR)

    ctx.samples = 5
    ctx.render_opts.update({"volumetrics": "low"})
    ctx.interp = True
    ctx.post.update({"grade": "eclipse", "saturation": 0.85, "vignette": 0.2, "bloom": 0.25,
                     "end": {"saturation": 0.62, "vignette": 0.32, "bloom": 0.16},
                     "caption": {"y": 0.72}})
