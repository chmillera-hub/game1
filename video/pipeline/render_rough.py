"""Fast review render: preview-quality shots (270x480, 3 samples), every other frame, into /opt/work/frames_rough."""
import json, os, subprocess, sys

sys.path.insert(0, os.path.dirname(__file__))
from shots import shot_bounds

BL = "/opt/tools/blender-4.5.14-linux-x64/blender"
HERE = os.path.dirname(os.path.abspath(__file__))
TL = json.load(open("/opt/work/timeline.json"))
LINES = {l["id"]: l for l in TL["lines"]}
OUT = "/opt/work/frames_rough"

for shot, t0, t1 in shot_bounds(LINES, TL["duration"]):
    sid = shot["id"]
    n = max(1, int(round((t1 - t0) * 24)))
    d = f"{OUT}/{sid}"
    os.makedirs(d, exist_ok=True)
    need = list(range(1, n + 1, 2)) + ([n] if (n - 1) % 2 else [])
    have = [f for f in need if os.path.exists(f"{d}/{f:04d}.png") and os.path.getsize(f"{d}/{f:04d}.png") > 1000]
    if len(have) == len(need):
        continue
    for f in need:
        p = f"{d}/{f:04d}.png"
        if os.path.exists(p) and os.path.getsize(p) <= 1000:
            os.remove(p)
    blend = f"/opt/work/shots/{sid}_prev.blend"
    if not os.path.exists(blend):
        r = subprocess.run([BL, "-b", "-P", f"{HERE}/blender/shotbuild.py", "--", sid, "--preview"],
                           capture_output=True, text=True)
        if "SHOT_OK" not in r.stdout:
            print("BUILD_FAIL", sid, flush=True)
            continue
    subprocess.run([BL, "-b", blend, "-o", f"{d}/####", "-F", "PNG", "-s", "1", "-e", str(n), "-j", "2", "-a"],
                   capture_output=True, text=True)
    if (n - 1) % 2:
        subprocess.run([BL, "-b", blend, "-o", f"{d}/####", "-F", "PNG", "-f", str(n)], capture_output=True, text=True)
    print("DONE", sid, flush=True)
print("ROUGH_RENDERS_DONE", flush=True)
