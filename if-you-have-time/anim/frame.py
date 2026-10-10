"""Render one frame of the film at absolute time t -> skia Image / numpy RGBA."""
import skia

from anim import scenes, subtitles
from anim.core import timeline


def scene_at(t):
    tl = timeline()
    for s in tl["scenes"]:
        if s["start"] <= t < s["end"]:
            return s["id"]
    return tl["scenes"][-1]["id"]


def render_frame(surface: skia.Surface, t: float):
    c = surface.getCanvas()
    c.resetMatrix()
    c.clear(skia.ColorBLACK)
    sid = scene_at(t)
    c.save()
    scenes.get(sid).render(c, t)
    c.restore()
    c.resetMatrix()
    subtitles.draw(c, t)
    return surface
