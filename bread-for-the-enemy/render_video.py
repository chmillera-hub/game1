"""Render all frames in parallel segments, then encode the delivery MP4(s).

  python3 render_video.py master          # frames -> <work>/master.mkv (near-lossless)
  python3 render_video.py encode [kbps]   # master + mix.wav -> output/*.mp4 under 15 MB
"""
import json
import math
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.environ.get("BFE_WORK", os.path.join(HERE, "..", ".bfe_work"))
OUT = os.path.join(HERE, "output")
W, H, FPS = 720, 1280, 24


def master(workers=4):
    tl = json.load(open(os.path.join(WORK, "timeline.json")))
    total = int(math.ceil(tl["duration"] * FPS))
    per = int(math.ceil(total / workers))
    procs = []
    t0 = time.time()
    for k in range(workers):
        f0, f1 = k * per, min(total, (k + 1) * per)
        seg = os.path.join(WORK, f"seg{k}.mkv")
        node = subprocess.Popen(["node", os.path.join(HERE, "render", "render.js"), "--timeline", os.path.join(WORK, "timeline.json"),
                                 "--from", str(f0), "--to", str(f1), "--width", str(W)], stdout=subprocess.PIPE)
        ff = subprocess.Popen(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
                               "-r", str(FPS), "-i", "pipe:0", "-c:v", "libx264", "-preset", "veryfast", "-crf", "8", "-pix_fmt", "yuv420p", seg],
                              stdin=node.stdout)
        node.stdout.close()
        procs.append((node, ff, seg))
    for node, ff, seg in procs:
        ff.wait()
        node.wait()
        if node.returncode or ff.returncode:
            raise SystemExit(f"segment failed: {seg}")
    lst = os.path.join(WORK, "segs.txt")
    with open(lst, "w") as f:
        for _, _, seg in procs:
            f.write(f"file '{seg}'\n")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                    os.path.join(WORK, "master.mkv")], check=True)
    print(f"master rendered: {total} frames in {time.time() - t0:.0f}s")


def encode_h264(name, vk, ak=64, scale=None, preset="veryslow"):
    os.makedirs(OUT, exist_ok=True)
    src = os.path.join(WORK, "master.mkv")
    vf = ["-vf", f"scale={scale}:flags=lanczos"] if scale else []
    common = ["-c:v", "libx264", "-preset", preset, "-tune", "animation", "-b:v", f"{vk}k", "-maxrate", f"{int(vk * 2.2)}k",
              "-bufsize", f"{int(vk * 4)}k", "-g", "240", "-keyint_min", "24", "-x264-params", "aq-mode=3:aq-strength=0.9:deblock=1,1",
              "-pix_fmt", "yuv420p"]
    log = os.path.join(WORK, f"{name}_2pass")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", src, *vf, *common, "-pass", "1", "-passlogfile", log,
                    "-an", "-f", "mp4", os.devnull], check=True)
    out = os.path.join(OUT, name)
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", src, "-i", os.path.join(WORK, "mix.wav"), *vf, *common,
                    "-pass", "2", "-passlogfile", log, "-c:a", "aac", "-b:a", f"{ak}k", "-ac", "2", "-ar", "48000",
                    "-movflags", "+faststart", "-shortest", out], check=True)
    return out


def encode_hevc(name, vk, ak=64, scale=None, preset="slow"):
    os.makedirs(OUT, exist_ok=True)
    src = os.path.join(WORK, "master.mkv")
    vf = ["-vf", f"scale={scale}:flags=lanczos"] if scale else []
    params = "keyint=240:min-keyint=24:aq-mode=3:psy-rd=1.0:log-level=error"
    log = os.path.join(WORK, f"{name}_x265")
    common = ["-c:v", "libx265", "-preset", preset, "-b:v", f"{vk}k", "-pix_fmt", "yuv420p", "-tag:v", "hvc1"]
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", src, *vf, *common,
                    "-x265-params", f"pass=1:stats={log}:{params}", "-an", "-f", "mp4", os.devnull], check=True)
    out = os.path.join(OUT, name)
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", src, "-i", os.path.join(WORK, "mix.wav"), *vf, *common,
                    "-x265-params", f"pass=2:stats={log}:{params}", "-c:a", "aac", "-b:a", f"{ak}k", "-ac", "2", "-ar", "48000",
                    "-movflags", "+faststart", "-shortest", out], check=True)
    return out


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "master"
    if cmd == "master":
        master(int(os.environ.get("BFE_WORKERS", "4")))
    elif cmd == "h264":
        p = encode_h264(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]) if len(sys.argv) > 4 else 64, sys.argv[5] if len(sys.argv) > 5 else None)
        print(p, os.path.getsize(p))
    elif cmd == "hevc":
        p = encode_hevc(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]) if len(sys.argv) > 4 else 64, sys.argv[5] if len(sys.argv) > 5 else None)
        print(p, os.path.getsize(p))
