"""Render review contact sheets for the whole film (for directors/critics).

    python3 tools/review_sheets.py [--workers 2]
      -> out/review/sNN.jpg (one sheet per scene), out/review/cuts.jpg (frame pairs around every cut),
         out/review/firstframe.jpg (frame 0 with the burned-in title, as the social preview will look)
"""
import json, os, subprocess, sys, shutil, math
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out/review")
TMP = os.path.join(OUT, "frames")

def stills(times, prefix):
    ts = ",".join(f"{t:.2f}" for t in times)
    subprocess.run(["node", "tools/render.js", "stills", "--t", ts, "--out", os.path.relpath(TMP, ROOT), "--prefix", prefix],
                   cwd=ROOT, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return [os.path.join(TMP, f"{prefix}_{t:.2f}.jpg") for t in times]

def main():
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 2
    tl = json.load(open(os.path.join(ROOT, "data/timeline.json")))
    sc = tl["scenes"]
    os.makedirs(TMP, exist_ok=True)
    jobs = []
    for i, s in enumerate(sc):
        end = sc[i + 1]["start"] if i + 1 < len(sc) else tl["duration"]
        dur = end - s["start"]
        n = max(8, min(20, int(math.ceil(dur / 1.6))))
        ts = [round(s["start"] + 0.08 + (dur - 0.2) * k / (n - 1), 2) for k in range(n)]
        jobs.append((s["id"], ts))
    cut_ts = []
    for i in range(1, len(sc)):
        c = sc[i]["start"]
        cut_ts += [round(c - 0.05, 2), round(c + 0.05, 2)] if sc[i]["transition_in"] != "dissolve" else [round(c - 0.6, 2), round(c + 0.6, 2)]
    jobs.append(("cuts", cut_ts))
    # split the work into `workers` lists of jobs (one browser each)
    buckets = [[] for _ in range(workers)]
    for k, j in enumerate(jobs):
        buckets[k % workers].append(j)
    def run(bucket):
        for name, ts in bucket:
            stills(ts, name)
    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(run, buckets))
    def sheet(name, ts, cols, scale=30):
        files = []
        for t in ts:
            f = os.path.join(TMP, f"{name}_{t:.2f}.jpg")
            g = f.replace(".jpg", "_l.jpg")
            subprocess.run(["convert", f, "-resize", f"{scale}%", "-gravity", "North", "-fill", "yellow", "-undercolor", "#000a",
                            "-pointsize", "15", "-annotate", "+0+3", f"{t:.2f}s", g], check=True)
            files.append(g)
        subprocess.run(["montage", *files, "-tile", f"{cols}x", "-geometry", "+2+2", "-background", "#222",
                        os.path.join(OUT, f"{name}.jpg")], check=True)
    for name, ts in jobs:
        sheet(name, ts, 2 * 3 if name == "cuts" else 5)
    # first frame with the burned-in title
    f0 = stills([0.0], "first")[0]
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f0, "-vf", "subtitles=out/subs.ass:fontsdir=assets/fonts",
                    os.path.join(OUT, "firstframe.jpg")], cwd=ROOT, check=True)
    print("review sheets ->", OUT)

if __name__ == "__main__":
    main()
