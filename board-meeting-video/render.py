"""Render all frames in parallel chunks, then encode the final MP4.

usage: BUILD=... python3 render.py [workers]
"""
import math, os, subprocess, sys, time
from multiprocessing import Process
import skia
from common import W, H, FPS, BUILD


def render_chunk(i, f0, f1):
    import film
    f = film.Film()
    out = f"{BUILD}/chunk_{i:02d}.mkv"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "ultrafast",
                          "-qp", "0", "-pix_fmt", "yuv444p", out], stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    t_start = time.time()
    for n in range(f0, f1):
        cv = surf.getCanvas()
        f.frame(cv, n / FPS)
        p.stdin.write(surf.makeImageSnapshot().tobytes())
        if (n - f0) % 300 == 0:
            el = time.time() - t_start
            print(f"[{i}] {n - f0}/{f1 - f0} frames, {el:.0f}s", flush=True)
    p.stdin.close()
    p.wait()


if __name__ == "__main__":
    from common import Timeline
    nw = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    total = Timeline().total
    nf = int(math.ceil(total * FPS))
    step = math.ceil(nf / nw)
    procs = []
    for i in range(nw):
        pr = Process(target=render_chunk, args=(i, i * step, min(nf, (i + 1) * step)))
        pr.start()
        procs.append(pr)
    for pr in procs:
        pr.join()
    with open(f"{BUILD}/chunks.txt", "w") as fh:
        for i in range(nw):
            fh.write(f"file 'chunk_{i:02d}.mkv'\n")
    print("frames done", nf)
