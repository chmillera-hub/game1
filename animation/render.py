"""Renders the animation frames in headless Chromium and encodes the videos.

    python3 render.py                 # both parts -> out/part1.mp4, out/part2.mp4
    python3 render.py 2               # just part 2
    python3 render.py --stills 1 10 55.5 120   # PNG stills of part 1 at those times
"""
import base64
import json
import os
import subprocess
import sys
from multiprocessing import Process

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
OUT = os.path.join(HERE, "out")
CHROME = os.environ.get("CHROME", "/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
WORKERS = int(os.environ.get("WORKERS", "4"))
BATCH = 12


def open_page(p, part):
    browser = p.chromium.launch(executable_path=CHROME if os.path.exists(CHROME) else None)
    page = browser.new_page(viewport={"width": 1280, "height": 720})
    page.goto("file://" + os.path.join(HERE, "scene.html"))
    with open(os.path.join(BUILD, f"timeline_part{part}.json")) as f:
        page.evaluate("tl => setup(tl)", json.load(f))
    return browser, page


GRAB = """([t0, n, fps]) => {
  const out = [];
  for (let i = 0; i < n; i++) { renderFrame(t0 + i / fps); out.push(document.getElementById('c').toDataURL('image/jpeg', 0.93)); }
  return out;
}"""


def worker(part, f0, f1, fps, seg_path):
    enc = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-vcodec", "mjpeg", "-r", str(fps), "-i", "-",
         "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", seg_path],
        stdin=subprocess.PIPE)
    with sync_playwright() as p:
        browser, page = open_page(p, part)
        f = f0
        while f < f1:
            n = min(BATCH, f1 - f)
            for url in page.evaluate(GRAB, [f / fps, n, fps]):
                enc.stdin.write(base64.b64decode(url.split(",", 1)[1]))
            f += n
            if (f - f0) % (BATCH * 20) == 0:
                print(f"  part {part} [{f0}-{f1}] {100 * (f - f0) / (f1 - f0):.0f}%", flush=True)
        browser.close()
    enc.stdin.close()
    enc.wait()


def render_part(part):
    with open(os.path.join(BUILD, f"timeline_part{part}.json")) as f:
        tl = json.load(f)
    fps, total = tl["fps"], int(round(tl["duration"] * tl["fps"]))
    os.makedirs(OUT, exist_ok=True)
    bounds = [round(i * total / WORKERS) for i in range(WORKERS + 1)]
    segs = [os.path.join(BUILD, f"seg{part}_{i}.mp4") for i in range(WORKERS)]
    procs = [Process(target=worker, args=(part, bounds[i], bounds[i + 1], fps, segs[i])) for i in range(WORKERS)]
    for pr in procs:
        pr.start()
    for pr in procs:
        pr.join()
        if pr.exitcode:
            raise SystemExit(f"worker failed ({pr.exitcode})")
    lst = os.path.join(BUILD, f"segs{part}.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{s}'\n" for s in segs)
    out = os.path.join(OUT, f"part{part}.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                    "-i", os.path.join(BUILD, f"part{part}.wav"), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", out], check=True)
    print(f"wrote {out}")


def stills(part, times):
    os.makedirs(os.path.join(BUILD, "stills"), exist_ok=True)
    with sync_playwright() as p:
        browser, page = open_page(p, part)
        msgs = []
        page.on("console", lambda m: msgs.append(m.text))
        page.on("pageerror", lambda e: msgs.append(str(e)))
        for t in times:
            url = page.evaluate("t => { renderFrame(t); return document.getElementById('c').toDataURL('image/png'); }", t)
            path = os.path.join(BUILD, "stills", f"p{part}_{t:07.2f}.png")
            with open(path, "wb") as f:
                f.write(base64.b64decode(url.split(",", 1)[1]))
            print(path)
        for m in msgs:
            print("console:", m)
        browser.close()


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--stills":
        stills(int(args[1]), [float(a) for a in args[2:]])
    else:
        for part in [int(a) for a in args] or [1, 2]:
            render_part(part)
