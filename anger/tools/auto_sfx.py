"""Collect motion-locked SFX from every scene's optional sfx_events() -> build/auto_sfx.json."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from anim import scenes  # noqa: E402
from config import BUILD  # noqa: E402


def main():
    events = []
    for sid in scenes.SCENE_IDS:
        try:
            mod = scenes.get(sid)
        except Exception as e:  # a scene that does not import yet contributes nothing
            print(f"auto_sfx: {sid} skipped ({e.__class__.__name__}: {e})")
            continue
        fn = getattr(mod, "sfx_events", None)
        if fn:
            ev = list(fn())
            events += ev
            print(f"auto_sfx: {sid} {len(ev)} events")
    (BUILD / "auto_sfx.json").write_text(json.dumps(sorted(events, key=lambda e: e["start"]), indent=1))


if __name__ == "__main__":
    main()
