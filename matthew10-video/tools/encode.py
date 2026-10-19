"""Final encode under a size budget, with quality measured against the master.

Usage: python encode.py BUILD_DIR OUT.mp4 [--budget-bytes 14500000] [--abr 80]

Steps: loudness-normalise the mix (EBU R128, -14 LUFS, -1.5 dBTP), encode AAC,
derive the video bitrate that fits the budget, two-pass H.264 at 1080x1920 and
720x1280, score each with SSIM against the near-lossless master (720p is
upscaled before comparing so resolution loss counts), keep the better one, mux.
"""
import json
import re
import subprocess
import sys
from pathlib import Path


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def duration(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)]).stdout
    return float(out.strip())


def measure(src):
    p = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(src), "-af",
                        "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    return json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", p.stderr, re.S).group(0))


def loudnorm(src, dst, target=-14.0):
    """Gain up to the target, limit peaks at -1.5 dBFS, then a final linear trim."""
    m1 = measure(src)
    g = target - float(m1["input_i"]) + 0.4
    pre = Path(str(dst) + ".pre.wav")
    run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af",
         f"volume={g:.2f}dB,alimiter=limit=0.82:attack=3:release=60:level=false", "-ar", "48000", str(pre)])
    m2 = measure(pre)
    trim = min(target - float(m2["input_i"]), -1.5 - float(m2["input_tp"]))
    run(["ffmpeg", "-v", "error", "-y", "-i", str(pre), "-af", f"volume={trim:.2f}dB", "-ar", "48000", str(dst)])
    m3 = measure(dst)
    pre.unlink()
    return {"before": m1, "after": m3}


def ssim(dist, ref, scale_to=None):
    vf = f"[0:v]scale={scale_to}:flags=lanczos[d];[d][1:v]ssim" if scale_to else "[0:v][1:v]ssim"
    p = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(dist), "-i", str(ref), "-lavfi", vf, "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.search(r"All:([0-9.]+)", p.stderr)
    return float(m.group(1)) if m else 0.0


def x264(src, dst, kbps, size, work):
    common = ["-vf", f"scale={size}:flags=lanczos", "-c:v", "libx264", "-preset", "veryslow", "-tune", "animation",
              "-b:v", f"{kbps}k", "-maxrate", f"{int(kbps * 2.2)}k", "-bufsize", f"{int(kbps * 4)}k",
              "-g", "240", "-keyint_min", "24", "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.1",
              "-x264-params", "aq-mode=3"]
    log = str(work / f"x264_{size.replace(':', 'x')}")
    run(["ffmpeg", "-v", "error", "-y", "-i", str(src), *common, "-pass", "1", "-passlogfile", log, "-an", "-f", "mp4", "/dev/null"])
    run(["ffmpeg", "-v", "error", "-y", "-i", str(src), *common, "-pass", "2", "-passlogfile", log, "-an", str(dst)])


def main():
    build, out = Path(sys.argv[1]), Path(sys.argv[2])
    args = sys.argv[3:]
    budget = int(args[args.index("--budget-bytes") + 1]) if "--budget-bytes" in args else 14_500_000
    abr = int(args[args.index("--abr") + 1]) if "--abr" in args else 80
    work = build / "enc"
    work.mkdir(exist_ok=True)
    master = build / "master_video.mp4"
    dur = duration(master)

    meas = loudnorm(build / "mix.wav", work / "mix_norm.wav")
    run(["ffmpeg", "-v", "error", "-y", "-i", str(work / "mix_norm.wav"), "-c:a", "aac", "-b:a", f"{abr}k",
         "-ac", "2", str(work / "audio.m4a")])
    audio_bytes = (work / "audio.m4a").stat().st_size
    overhead = 0.012 * budget
    vkbps = int((budget - audio_bytes - overhead) * 8 / dur / 1000)
    print(f"duration {dur:.1f}s  audio {audio_bytes/1e6:.2f} MB  -> video budget {vkbps} kbps")

    results = []
    for size in ["1080:1920", "720:1280"]:
        dst = work / f"v_{size.replace(':', 'x')}.mp4"
        x264(master, dst, vkbps, size, work)
        s = ssim(dst, master, scale_to="1080:1920" if size != "1080:1920" else None)
        results.append({"size": size, "path": str(dst), "bytes": dst.stat().st_size, "ssim": s})
        print(f"  {size}: {dst.stat().st_size/1e6:.2f} MB  SSIM {s:.4f}")
    best = max(results, key=lambda r: r["ssim"])
    run(["ffmpeg", "-v", "error", "-y", "-i", best["path"], "-i", str(work / "audio.m4a"), "-c", "copy",
         "-map", "0:v:0", "-map", "1:a:0", "-movflags", "+faststart", "-shortest", str(out)])
    # first frame must be a real image, not black
    ff = work / "first_frame.png"
    run(["ffmpeg", "-v", "error", "-y", "-i", str(out), "-frames:v", "1", str(ff)])
    from PIL import Image, ImageStat
    yavg = ImageStat.Stat(Image.open(ff).convert("L")).mean[0]
    report = {"output": str(out), "bytes": out.stat().st_size, "duration": dur, "video": best,
              "candidates": results, "audio_kbps": abr, "loudness_in": meas, "first_frame_yavg": round(yavg, 1)}
    (build / "encode_report.json").write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
