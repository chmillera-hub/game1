"""Render the film's frames.

  python3 render.py --stills 0 60.5 120     # PNG stills at given seconds
  python3 render.py --workers 4             # all frames -> build/chunks/*.mkv (lossless)
"""
import argparse
import bisect
import math
import os
import subprocess
import sys
import time

import numpy as np
import skia

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from gfx import H, W  # noqa: E402
import timeline  # noqa: E402

FPS = 24
BUILD = os.path.join(HERE, "build")


class Film:
    def __init__(self):
        import shots
        from subs import Subs
        self.T = timeline.get()
        self.shots = shots.build(self.T)
        self.starts = [s[0] for s in self.shots]
        self.subs = Subs(self.T)
        self.surface = skia.Surface(W, H)
        self.n_frames = int(math.ceil(self.T.duration * FPS))

    def frame(self, t):
        c = self.surface.getCanvas()
        c.clear(skia.Color(0, 0, 0))
        i = max(0, bisect.bisect_right(self.starts, t) - 1)
        t0, view, cam = self.shots[i]
        c.save()
        view.draw(c, t, cam.at(t))
        c.restore()
        self.subs.draw(c, t)
        return self.surface

    def pixels(self, t, buf):
        s = self.frame(t)
        s.readPixels(skia.ImageInfo.Make(W, H, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType), buf, W * 4)
        return buf


def render_chunk(args):
    idx, f0, f1, out = args
    film = Film()
    buf = np.empty((H, W, 4), np.uint8)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "ultrafast", "-qp", "0", "-pix_fmt", "yuv420p", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t_start = time.time()
    for f in range(f0, f1):
        film.pixels(f / FPS, buf)
        p.stdin.write(buf.tobytes())
        if (f - f0) % 240 == 0:
            el = time.time() - t_start
            print(f"[chunk {idx}] frame {f - f0}/{f1 - f0}  {el:.0f}s", flush=True)
    p.stdin.close()
    p.wait()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stills", nargs="*", type=float)
    ap.add_argument("--out", default=os.path.join(BUILD, "stills"))
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--range", nargs=2, type=float)
    ap.add_argument("--chunk-dir", default=os.path.join(BUILD, "chunks"))
    args = ap.parse_args()
    if args.stills:
        os.makedirs(args.out, exist_ok=True)
        film = Film()
        for t in args.stills:
            t0 = time.time()
            s = film.frame(t)
            path = os.path.join(args.out, f"t{t:07.2f}.png")
            s.makeImageSnapshot().save(path, skia.kPNG)
            print(path, f"{(time.time() - t0) * 1000:.0f} ms")
        return
    film = Film()
    n = film.n_frames
    f_lo, f_hi = 0, n
    if args.range:
        f_lo, f_hi = int(args.range[0] * FPS), min(n, int(args.range[1] * FPS))
    del film
    chunk_dir = os.path.abspath(args.chunk_dir)
    os.makedirs(chunk_dir, exist_ok=True)
    k = args.workers
    bounds = [f_lo + (f_hi - f_lo) * i // k for i in range(k + 1)]
    jobs = [(i, bounds[i], bounds[i + 1], os.path.join(chunk_dir, f"c{i:02d}.mkv")) for i in range(k)]
    from multiprocessing import Pool
    t0 = time.time()
    with Pool(k) as pool:
        outs = pool.map(render_chunk, jobs)
    with open(os.path.join(chunk_dir, "list.txt"), "w") as f:
        for o in outs:
            f.write(f"file '{o}'\n")
    print(f"rendered {f_hi - f_lo} frames in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
