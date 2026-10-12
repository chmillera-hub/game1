"""Render frames in parallel and encode them with ffmpeg."""
import os
import subprocess
import sys
from multiprocessing import Process

import cairo

import engine
import scenes
import timeline
from draw import W, H

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
TL_PATH = os.path.join(BUILD, "timeline")


def render_frame(ctx, tl, mouth, rnd, t):
    si = engine.scene_at(tl, t)
    ctx.save()
    S = engine.S(ctx, tl, mouth, rnd, si, t)
    scenes.draw_scene(S)
    ctx.restore()
    engine.draw_wipe(ctx, tl, t)
    engine.draw_captions(ctx, tl, t)


def still(t, path):
    tl, mouth, rnd = timeline.load(TL_PATH)
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
    ctx = cairo.Context(surf)
    render_frame(ctx, tl, mouth, rnd, t)
    surf.write_to_png(path)


def worker(f0, f1, out):
    tl, mouth, rnd = timeline.load(TL_PATH)
    fps = tl["fps"]
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra",
           "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "medium",
           "-crf", "19", "-pix_fmt", "yuv420p", "-g", str(fps * 2), out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(f0, f1):
        ctx = cairo.Context(surf)
        render_frame(ctx, tl, mouth, rnd, f / fps)
        surf.flush()
        p.stdin.write(bytes(surf.get_data()))
        if (f - f0) % 300 == 0:
            print(f"  worker {f0}: frame {f - f0}/{f1 - f0}", flush=True)
    p.stdin.close()
    p.wait()
    if p.returncode:
        raise SystemExit(f"ffmpeg failed for {out}")


def render_video(out_path, workers=4):
    tl, _, _ = timeline.load(TL_PATH)
    n = tl["nframes"]
    seg_dir = os.path.join(BUILD, "segments")
    os.makedirs(seg_dir, exist_ok=True)
    bounds = [round(n * i / workers) for i in range(workers + 1)]
    procs, parts = [], []
    for i in range(workers):
        part = os.path.join(seg_dir, f"part{i:02d}.mp4")
        parts.append(part)
        pr = Process(target=worker, args=(bounds[i], bounds[i + 1], part))
        pr.start()
        procs.append(pr)
    for pr in procs:
        pr.join()
        if pr.exitcode:
            raise SystemExit("a render worker failed")
    lst = os.path.join(seg_dir, "list.txt")
    with open(lst, "w") as f:
        for part in parts:
            f.write(f"file '{part}'\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c", "copy", out_path], check=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "still":
        for a in sys.argv[2:]:
            t = float(a)
            still(t, os.path.join(BUILD, f"still_{t:07.2f}.png"))
    else:
        render_video(os.path.join(BUILD, "video_only.mp4"))
