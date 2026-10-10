"""Render the whole film (or a time range) to a high-quality intermediate video.

    python3 -m anim.render [--start S] [--end E] [--jobs N] [--out build/video_master.mkv]

Frames are split into N contiguous chunks rendered by separate processes, each piped
to its own ffmpeg (x264 crf 10, ultrafast) and then concatenated losslessly.
"""
import argparse
import os
import subprocess
import time
from multiprocessing import Process

import skia

from config import BUILD, FPS, H, W


def _worker(idx, f0, f1, path):
    from anim.frame import render_frame
    from anim.preview import frame_rgb
    surf = skia.Surface(W, H)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "8",
           "-pix_fmt", "yuv444p", path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    for f in range(f0, f1):
        render_frame(surf, f / FPS)
        p.stdin.write(frame_rgb(surf).tobytes())
        if (f - f0) % 240 == 0:
            el = time.time() - t0
            print(f"[job {idx}] frame {f} ({f - f0}/{f1 - f0}) {el:.0f}s", flush=True)
    p.stdin.close()
    p.wait()


def main():
    from anim.core import timeline
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float, default=None)
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2)))
    ap.add_argument("--out", default=str(BUILD / "video_master.mkv"))
    a = ap.parse_args()
    end = a.end if a.end is not None else timeline()["duration"]
    f0, f1 = int(round(a.start * FPS)), int(round(end * FPS))
    n = f1 - f0
    chunk = (n + a.jobs - 1) // a.jobs
    parts, procs = [], []
    tmp = BUILD / "render_parts"
    tmp.mkdir(parents=True, exist_ok=True)
    for i in range(a.jobs):
        s, e = f0 + i * chunk, min(f1, f0 + (i + 1) * chunk)
        if s >= e:
            break
        path = str(tmp / f"part{i:02d}.mkv")
        parts.append(path)
        pr = Process(target=_worker, args=(i, s, e, path))
        pr.start()
        procs.append(pr)
    for pr in procs:
        pr.join()
        if pr.exitcode != 0:
            raise SystemExit(f"render job failed with exit code {pr.exitcode}")
    lst = tmp / "list.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in parts))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c", "copy", a.out], check=True)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
