"""Build every shot in preview mode and render 3 key frames each, then make contact sheets.

python3 run_previews.py [--chars] [shot ids...]
"""
import json, os, subprocess, sys

sys.path.insert(0, os.path.dirname(__file__))
from shots import SHOTS, shot_bounds

BL = "/opt/tools/blender-4.5.14-linux-x64/blender"
HERE = os.path.dirname(os.path.abspath(__file__))
TL = json.load(open("/opt/work/timeline.json"))
LINES = {l["id"]: l for l in TL["lines"]}
OUT = "/opt/work/previews"
os.makedirs(OUT, exist_ok=True)


def run(args, log):
    r = subprocess.run(args, capture_output=True, text=True)
    out = r.stdout + r.stderr
    bad = [l for l in out.splitlines() if "Traceback" in l or "Error" in l and "EGL" not in l]
    if bad or r.returncode:
        open(log, "w").write(out)
    return out, bool(bad) or r.returncode != 0


def main():
    args = sys.argv[1:]
    if "--chars" in args:
        args.remove("--chars")
        chars = os.environ.get("CHARS", "JESUS,ELDER,YOUNG,PH2,PH3,PETER,JOHN,WOMAN,SISTER").split(",")
        for c in chars:
            out, bad = run([BL, "-b", "-P", f"{HERE}/blender/charbuild.py", "--", c], f"{OUT}/char_{c}.log")
            print("CHAR", c, "FAIL" if bad else "ok", flush=True)
    bounds = shot_bounds(LINES, TL["duration"])
    if args:
        order = {sid: i for i, sid in enumerate(args)}
        bounds = sorted([b for b in bounds if b[0]["id"] in order], key=lambda b: order[b[0]["id"]])
    for shot, t0, t1 in bounds:
        sid = shot["id"]
        n = max(1, int(round((t1 - t0) * 24)))
        out, bad = run([BL, "-b", "-P", f"{HERE}/blender/shotbuild.py", "--", sid, "--preview"], f"{OUT}/{sid}_build.log")
        if bad:
            print("BUILD_FAIL", sid, flush=True)
            continue
        frames = sorted({1, max(1, n // 2), n})
        for f in frames:
            out, bad = run([BL, "-b", f"/opt/work/shots/{sid}_prev.blend", "-o", f"{OUT}/{sid}_####", "-F", "PNG",
                            "-f", str(f)], f"{OUT}/{sid}_render.log")
        print("SHOT", sid, n, "frames", "render-fail" if bad else "ok", flush=True)


if __name__ == "__main__":
    main()
