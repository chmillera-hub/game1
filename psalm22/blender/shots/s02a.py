"""s02a - Day and night time-lapse: "My God, I cry out by day, but you do not answer,"

Time-lapse over the Judean hills from a rocky spur, low behind a lone dead tree that stands against the
sky. The afternoon sun races down across the frame towards the hills, the shadows of the tree and the
rocks swing and stretch towards the camera, clouds streak overhead, the sky burns through a blazing
dusk and goes to night with the stars coming out (14-frame dissolve tail into the Gethsemane night of
s02b). A slow motion-control slide gives parallax on the tree.
The env time-lapse sky is used as built (uniform-only animation); the cloud layer is re-tinted here so the
clouds take the sky's colour (blazing at dusk, black against the stars) instead of grey.
"""
import math
import bpy
from mathutils import Vector
from lib import core as C
from lib import env as E

VIEW_AZ = 262.0      # compass; the April sun sets at ~281 deg, so it crosses the frame right of centre


def tint_clouds_by_sky():
    """In the timelapse world, clouds are white x sky luminance (grey at sunset) and their forward-scatter
    glow points at a fixed direction. Re-wire: clouds x sky colour, glow towards env_tl_sun_dir."""
    nt = bpy.context.scene.world.node_tree
    T = E._NT(nt)
    bw = next((n for n in nt.nodes if n.type == "RGBTOBW"), None)
    if bw is None:
        return False
    sky_src = bw.inputs[0].links[0].from_socket
    # bw -> MULTIPLY_ADD chain (lum * 1.1 + 0.02) -> combine -> multiply mix; find the multiply mix
    mul = None
    for l in nt.links:
        if l.from_node == bw:
            n = l.to_node                         # math MULTIPLY (x1.1)
            for l2 in nt.links:
                if l2.from_node == n:
                    n2 = l2.to_node               # math ADD (+0.02)
                    for l3 in nt.links:
                        if l3.from_node == n2:
                            n3 = l3.to_node       # combine xyz
                            for l4 in nt.links:
                                if l4.from_node == n3 and l4.to_node.type == "MIX":
                                    mul = (l4.to_node, l4.to_socket)
    if mul is None:
        return False
    node, sock = mul
    # sky colour (night: dark, day: bright) + the sun-side glow colour of the time-lapse palette (blazing at dusk)
    glow = E._lattr(T, "env_tl_glow", (0.3, 0.25, 0.15))
    boost = T.mix(1.0, sky_src, (1.3, 1.25, 1.2), blend="MULTIPLY")
    boost = T.mix(1.0, boost, T.mix(1.0, glow, (0.55, 0.5, 0.5), blend="MULTIPLY"), blend="ADD")
    boost = T.mix(1.0, boost, (0.01, 0.01, 0.012), blend="ADD")
    nt.links.new(boost, sock)
    # silver lining / forward scatter: follow the animated sun direction
    sd = E._lattr(T, "env_tl_sun_dir", (0.0, 1.0, 0.5))
    for n in nt.nodes:
        if n.type == "VECT_MATH" and n.operation == "DOT_PRODUCT" and not n.inputs[1].is_linked:
            v = tuple(n.inputs[1].default_value)
            if abs(v[0]) < 1e-6 and abs(v[1] - 0.98) < 0.03:      # the cloud layer's fixed (0, 1, 0.2) normalised
                nt.links.new(sd, n.inputs[1])
    return True


def build(ctx):
    N, NR = ctx.nframes, ctx.render_frames
    va = math.radians(VIEW_AZ)
    fwd = Vector((math.sin(va), math.cos(va), 0))
    side = Vector((fwd.y, -fwd.x, 0))
    tp = fwd * 0.5 + side * 1.2                    # judean_hills puts the dead tree here (spur edge)
    # low on the spur, ~11 m behind the tree and left of it: the tree stands on the right third, against the sky
    base0 = tp - fwd * 6.6 - side * 3.1
    base1 = tp - fwd * 6.0 - side * 2.2
    far = tp + fwd * 400.0
    E.set_view([dict(loc=tuple(base0), target=tuple(far), lens=22, margin=12, near=14),
                dict(loc=tuple(base1), target=tuple(far), lens=22, margin=12, near=14)])
    A = E.judean_hills(ctx, timelapse=True, hour0=15.1, hour1=20.7, view_az=VIEW_AZ, clouds=0.6, olives=0.2, grass=0.3)
    E.set_view(None)
    # render cost: the sun moves every frame, so EEVEE re-renders every shadow page of every caster each frame.
    # Far olives / far rocks cast no visible shadows from here, the air box only adds a little depth (the env
    # haze shader already gives the aerial perspective).
    for o in bpy.context.scene.objects:
        if o.name.startswith(("EnvHillOlives", "EnvHillShrubs")):
            o.visible_shadow = False
        if o.name.startswith(("EnvHillAir", "EnvHillBouldersFar")):     # far boulders: invisible from this low eye
            o.hide_render = True
    A["timelapse"]["sun"].data.shadow_maximum_resolution = 0.02     # coarser pages: identical here, -1.5 s/frame
    tint_clouds_by_sky()
    gz = A["ground_z"]
    eye0 = Vector((base0.x, base0.y, gz(base0.x, base0.y) + 1.15))
    eye1 = Vector((base1.x, base1.y, gz(base1.x, base1.y) + 1.25))

    def path(f):
        u = (f - 1) / float(NR - 1)                       # constant slider speed
        loc = eye0.lerp(eye1, u)
        tgt = Vector((far.x, far.y, loc.z + 400.0 * math.tan(math.radians(6.0))))
        return (loc, tgt, 0.0, 22.0)

    cam = C.camera(loc=tuple(eye0), target=tuple(far), lens=22)
    C.animate_camera(cam, path, 1, NR)

    ctx.samples = 4
    ctx.render_opts.update({"volumetrics": "low", "shadow_scale": 0.5})
    ctx.interp = False        # time-lapse: the sky, clouds and shadows change every frame -> render 24 fps
    ctx.post.update({"grade": "neutral", "saturation": 1.05, "bloom": 0.3, "vignette": 0.2,
                     "end": {"grade": "night", "vignette": 0.28}})
