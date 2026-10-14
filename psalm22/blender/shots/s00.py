"""s00 - Golgotha title shot (prototype for pipeline validation)."""
import math
from mathutils import Vector
from lib import core as C


def build(ctx):
    C.world_hdri("qwantani_sunset_puresky", strength=1.0, rotation=200)
    C.sun(elevation=12, azimuth=170, energy=3.5, temp=3800)
    hill = C.golgotha_hill(peak=7, radius=30, cy=40)
    ground = C.mat_pbr("dry_ground_rocks", scale=0.5, tint=(0.95, 0.85, 0.75))
    C.terrain(size=300, res=150, height=1.2, scale=0.03, height_fn=hill, mat_=ground)
    top = C.height_at("Terrain", 0, 40)
    for x, rz in ((-4.5, 8), (0, 0), (4.5, -6)):
        C.wooden_cross(loc=(x, 40 + abs(x) * 0.3, C.height_at("Terrain", x, 40) - 0.3), rot_z=rz)
    cam = C.camera(lens=30, loc=(0, -2, 2.0), target=(0, 40, top + 3))

    def path(f):
        u = C.ease_in_out(ctx.u(f))
        return (Vector((0, -2 + 8 * u, 2.0 + 1.5 * u)), Vector((0, 40, top + 3.0 + 0.5 * u)))
    C.animate_camera(cam, path)
    C.atmosphere(0.004, (0.9, 0.75, 0.6), 0.5)
    ctx.post.update({"grade": "warm", "bloom": 0.35})
