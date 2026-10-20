"""Resumable render queue: build each shot's final .blend (if needed) and render its missing frames.

nohup python3 render_all.py [shot ids...] > /opt/work/render.log 2>&1 &
"""
import json, os, subprocess, sys, time

sys.path.insert(0, os.path.dirname(__file__))
from shots import SHOTS, shot_bounds

BL = "/opt/tools/blender-4.5.14-linux-x64/blender"
HERE = os.path.dirname(os.path.abspath(__file__))
TL = json.load(open("/opt/work/timeline.json"))
LINES = {l["id"]: l for l in TL["lines"]}


def frames_needed(n, step):
    return [f for f in range(1, n + 1, step)] + ([n] if (n - 1) % step else [])


def main():
    want = sys.argv[1:]
    bounds = shot_bounds(LINES, TL["duration"])
    if want:
        order = {s: i for i, s in enumerate(want)}
        bounds = sorted([b for b in bounds if b[0]["id"] in order], key=lambda b: order[b[0]["id"]])
    for shot, t0, t1 in bounds:
        sid = shot["id"]
        n = max(1, int(round((t1 - t0) * 24)))
        step = shot.get("frame_step", 1)
        need = frames_needed(n, step)
        d = f"/opt/work/frames/{sid}"
        os.makedirs(d, exist_ok=True)
        done = [f for f in need if os.path.exists(f"{d}/{f:04d}.png") and os.path.getsize(f"{d}/{f:04d}.png") > 1000]
        if len(done) == len(need):
            print("SKIP", sid, flush=True)
            continue
        # clear zero-byte placeholders left by an interrupted run
        for f in need:
            p = f"{d}/{f:04d}.png"
            if os.path.exists(p) and os.path.getsize(p) <= 1000:
                os.remove(p)
        blend = f"/opt/work/shots/{sid}.blend"
        if not os.path.exists(blend) or "--rebuild" in os.environ.get("RENDER_FLAGS", ""):
            r = subprocess.run([BL, "-b", "-P", f"{HERE}/blender/shotbuild.py", "--", sid], capture_output=True, text=True)
            if "SHOT_OK" not in r.stdout:
                open(f"/opt/work/build_{sid}.log", "w").write(r.stdout + r.stderr)
                print("BUILD_FAIL", sid, flush=True)
                continue
        t = time.time()
        subprocess.run([BL, "-b", blend, "-a"], capture_output=True, text=True)
        if (n - 1) % step:
            subprocess.run([BL, "-b", blend, "-f", str(n)], capture_output=True, text=True)
        dt = time.time() - t
        got = len([f for f in need if os.path.exists(f"{d}/{f:04d}.png") and os.path.getsize(f"{d}/{f:04d}.png") > 1000])
        print(f"DONE {sid} {got}/{len(need)} frames in {dt:.0f}s ({dt / max(1, got - len(done)):.1f}s/frame)", flush=True)


if __name__ == "__main__":
    main()
