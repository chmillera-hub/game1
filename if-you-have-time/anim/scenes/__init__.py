"""Scene registry. Each scene module exposes  render(canvas, t)  for absolute time t
inside its span (see build/timeline.json). The canvas arrives with an identity matrix,
cleared to black; scenes apply their own Camera."""
import importlib

SCENE_IDS = ["s0", "s1", "s2", "s3", "s4", "s5"]


def get(sid):
    return importlib.import_module(f"anim.scenes.{sid}")
