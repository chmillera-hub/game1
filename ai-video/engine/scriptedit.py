"""Safe, locked edits of ONE scene's timing beats in script.json.

Scene builders run in parallel, so never rewrite script.json directly. Use:

    from engine.scriptedit import update_scene
    def fn(scene):                      # scene = the dict for your scene
        scene["beats"].insert(3, {"t": "pause", "dur": 0.8, "cue": "wall_done"})
        scene["tail"] = 0.6
    update_scene("s04", fn)            # locks, edits, rebuilds out/timeline.json

Only pause/cue beats and head/tail/min_dur/music fields may change here.
Line text/voice changes need new TTS: report them instead.
"""
import fcntl
import json
import os

from .timeline import ROOT, SCRIPT, build_timeline

LOCK = os.path.join(ROOT, "out", ".script.lock")
DURS = os.path.join(ROOT, "out", "durations.json")


def _line_sig(scene):
    return [(b["id"], b["who"], b["text"], b.get("say"), b.get("voice"), b.get("speed"),
             b.get("pitch")) for b in scene["beats"] if b.get("t", "line") == "line"]


def update_scene(sid, fn):
    os.makedirs(os.path.dirname(LOCK), exist_ok=True)
    with open(LOCK, "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        with open(SCRIPT) as f:
            script = json.load(f)
        scene = next(s for s in script["scenes"] if s["id"] == sid)
        before = _line_sig(scene)
        fn(scene)
        if _line_sig(scene) != before:
            raise ValueError("update_scene may not change spoken lines (TTS needed); "
                             "report line changes instead")
        tmp = SCRIPT + ".tmp"
        with open(tmp, "w") as f:
            json.dump(script, f, indent=1, ensure_ascii=False)
        os.replace(tmp, SCRIPT)
        with open(DURS) as f:
            build_timeline(json.load(f))
        fcntl.flock(lk, fcntl.LOCK_UN)
