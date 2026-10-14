"""s15 - Empty tomb (baseline test)."""
from mathutils import Vector
from lib import core as C
from lib import sets as S


def build(ctx):
    n = ctx.nframes
    tomb = S.garden_tomb(ctx, stone_open=[(1, 0.0), (int(n * 0.45), 1.0)])
    wps = tomb.extra["move_in"]

    def path(f):
        u = C.ease_in_out(min(1.0, ctx.u(f))) * (len(wps) - 1)
        i = min(len(wps) - 2, int(u))
        t = u - i
        return wps[i][0].lerp(wps[i + 1][0], t), wps[i][1].lerp(wps[i + 1][1], t)
    C.animate_camera(tomb.camera("approach"), path)
    ctx.samples = 6
    ctx.render_opts = {"volumetrics": "low"}
