"""Render all segments in parallel, then encode the final portrait MP4 under a size cap.

  python encode.py render            # parallel render -> build/video/mezzanine.mkv
  python encode.py final             # 2-pass x264 (+HEVC alt) with build/audio/mix.wav
"""
import json
import os
import subprocess
import sys
import time

import paths

N_SEG = int(os.environ.get("WHATIF_SEGS", "4"))
CAP_BYTES = 14_600_000          # stay safely under 15 MB
AUDIO_KBPS = 64
OUT_BASENAME = "what_if_earth_shrank"


def run(cmd, **kw):
    print("+", " ".join(cmd[:8]), "...", flush=True)
    return subprocess.run(cmd, check=True, **kw)


def render_all():
    py = sys.executable
    t0 = time.time()
    procs = [subprocess.Popen([py, "render.py", "--seg", str(k), str(N_SEG)], cwd=paths.SRC)
             for k in range(N_SEG)]
    rc = [p.wait() for p in procs]
    if any(rc):
        raise SystemExit(f"segment render failed: {rc}")
    lst = os.path.join(paths.VIDEO, "segs.txt")
    with open(lst, "w") as f:
        for k in range(N_SEG):
            f.write(f"file '{os.path.join(paths.VIDEO, f'seg_{k:02d}.mkv')}'\n")
    mez = os.path.join(paths.VIDEO, "mezzanine.mkv")
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", mez])
    print(f"rendered in {time.time() - t0:.0f}s -> {mez}")


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", path],
                         capture_output=True, text=True, check=True).stdout
    return float(json.loads(out)["format"]["duration"])


def ssim(dist, ref):
    out = subprocess.run(["ffmpeg", "-i", dist, "-i", ref, "-lavfi", "[0:v][1:v]ssim", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    for tok in out.split():
        if tok.startswith("All:"):
            return float(tok[4:])
    return None


def encode_final(codec="h264", cap=CAP_BYTES):
    mez = os.path.join(paths.VIDEO, "mezzanine.mkv")
    mix = os.path.join(paths.AUDIO, "mix.wav")
    dur = duration(mez)
    total_kbit = cap * 8 / 1000
    vk = int(total_kbit / dur - AUDIO_KBPS - 6)  # ~6 kbps container overhead
    tag = "" if codec == "h264" else "_hevc"
    out = os.path.join(paths.OUTPUT, f"{OUT_BASENAME}{tag}.mp4")
    log = os.path.join(paths.VIDEO, f"pass_{codec}")
    for attempt in range(4):
        if codec == "h264":
            vopt = ["-c:v", "libx264", "-preset", "veryslow", "-tune", "animation", "-profile:v", "high",
                    "-level", "4.1", "-b:v", f"{vk}k", "-maxrate", f"{vk * 3}k", "-bufsize", f"{vk * 6}k",
                    "-g", "240", "-keyint_min", "24", "-pix_fmt", "yuv420p", "-passlogfile", log]
            p1 = vopt + ["-pass", "1"]
            p2 = vopt + ["-pass", "2"]
        else:
            xp = f"log-level=error:stats={log}.log"
            vopt = ["-c:v", "libx265", "-preset", "slow", "-b:v", f"{vk}k", "-pix_fmt", "yuv420p", "-tag:v", "hvc1"]
            p1 = vopt + ["-x265-params", xp + ":pass=1"]
            p2 = vopt + ["-x265-params", xp + ":pass=2"]
        run(["ffmpeg", "-v", "error", "-y", "-i", mez] + p1 + ["-an", "-f", "null", "/dev/null"])
        run(["ffmpeg", "-v", "error", "-y", "-i", mez, "-i", mix, "-map", "0:v", "-map", "1:a"] + p2 +
            ["-c:a", "aac", "-b:a", f"{AUDIO_KBPS}k", "-ar", "48000", "-movflags", "+faststart", "-shortest", out])
        size = os.path.getsize(out)
        print(f"{codec}: video {vk} kbps -> {size / 1e6:.2f} MB")
        if size <= cap:
            break
        vk = int(vk * cap / size * 0.98)
    q = ssim(out, mez)
    print(f"{codec}: SSIM vs mezzanine = {q}")
    return out, size, q, vk


def poster():
    mez = os.path.join(paths.VIDEO, "mezzanine.mkv")
    out = os.path.join(paths.OUTPUT, f"{OUT_BASENAME}_first_frame.png")
    run(["ffmpeg", "-v", "error", "-y", "-i", mez, "-frames:v", "1", out])


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("render", "all"):
        render_all()
    if what in ("final", "all"):
        res = {"h264": encode_final("h264")}
        if os.environ.get("WHATIF_HEVC", "1") == "1":
            res["hevc"] = encode_final("hevc")
        poster()
        json.dump({k: dict(path=v[0], bytes=v[1], ssim=v[2], video_kbps=v[3]) for k, v in res.items()},
                  open(os.path.join(paths.BUILD, "encode_report.json"), "w"), indent=1)
        print(json.dumps(res, indent=1))
