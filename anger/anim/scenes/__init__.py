"""Scene registry. Each scene module exposes  render(canvas, t)  for absolute time t
inside its span (see build/timeline.json). The canvas arrives with an identity matrix,
cleared to black; scenes apply their own Camera.

A scene may also expose  sfx_events() -> [{"name", "start", "gain_db"}, ...]  for sounds that
must lock to its animation (footsteps, armor clanks, ...). tools/auto_sfx.py collects them into
build/auto_sfx.json, which audio/mix.py merges with the timeline's SFX."""
import importlib

SCENE_IDS = ["s1", "s2", "s3", "s4", "s5", "s6"]


def get(sid):
    return importlib.import_module(f"anim.scenes.{sid}")
