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
    boost = T.mix(1.0, sky_src, (1.35, 1.25, 1.2), blend="MULTIPLY")
    boost = T.mix(1.0, boost, (0.012, 0.012, 0.014), blend="ADD")
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
    A = E.judean_hills(ctx, timelapse=True, hour0=15.1, hour1=20.7, view_az=VIEW_AZ, clouds=0.5)
    tint_clouds_by_sky()

    va = math.radians(VIEW_AZ)
    fwd = Vector((math.sin(va), math.cos(va), 0))
    side = Vector((fwd.y, -fwd.x, 0))
    tp = Vector(A["dead_tree_pos"])
    gz = A["ground_z"]
    # low, a few metres behind the tree, a little left of it: the tree stands on the right third against the sky
    base0 = tp - fwd * 5.2 - side * 2.0
    base1 = tp - fwd * 4.7 - side * 1.15
    eye0 = Vector((base0.x, base0.y, gz(base0.x, base0.y) + 1.35))
    eye1 = Vector((base1.x, base1.y, gz(base1.x, base1.y) + 1.5))
    far = tp + fwd * 400.0

    def path(f):
        u = C.smoothstep(0.1 + 0.8 * (f - 1) / float(NR - 1)) * 1.25 - 0.125   # constant-ish slider speed
        loc = eye0.lerp(eye1, u)
        tgt = Vector((far.x, far.y, loc.z + 400.0 * math.tan(math.radians(7.0))))
        return (loc, tgt, 0.0, 22.0)

    cam = C.camera(loc=tuple(eye0), target=tuple(far), lens=22)
    C.animate_camera(cam, path, 1, NR)

    ctx.samples = 5
    ctx.render_opts.update({"volumetrics": "low"})
    ctx.interp = False        # time-lapse: the sky, clouds and shadows change every frame -> render 24 fps
    ctx.post.update({"grade": "neutral", "saturation": 1.05, "bloom": 0.3, "vignette": 0.2,
                     "end": {"grade": "night", "vignette": 0.28}})
