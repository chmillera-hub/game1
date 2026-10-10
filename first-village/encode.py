"""Final encode: H.264 + AAC MP4 sized to fit a byte budget (default 14.3 MB).

  python3 encode.py [--target-mb 14.3] [--audio-kbps 64] [--out the_first_village.mp4]
"""
import argparse
import json
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True, check=True).stdout
    return float(out)


def loudnorm_filter(wav, target=-15.0):
    """Two-pass EBU R128 normalisation (linear), for phones and social platforms."""
    res = subprocess.run(["ffmpeg", "-hide_banner", "-i", wav, "-af",
                          f"loudnorm=I={target}:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                         capture_output=True, text=True)
    m = json.loads(re.findall(r"\{[^{}]+\}", res.stderr)[-1])
    return (f"loudnorm=I={target}:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
            f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:"
            f"linear=true")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target-mb", type=float, default=14.3)
    ap.add_argument("--audio-kbps", type=int, default=64)
    ap.add_argument("--out", default=os.path.join(BUILD, "the_first_village.mp4"))
    a = ap.parse_args()

    video, wav = os.path.join(BUILD, "video_master.mkv"), os.path.join(BUILD, "mix.wav")
    dur = duration(video)
    budget_bits = a.target_mb * 1e6 * 8 * 0.985 - a.audio_kbps * 1000 * dur   # ~1.5% container overhead
    vk = int(budget_bits / dur / 1000)
    print(f"duration {dur:.1f}s -> video {vk} kbps + audio {a.audio_kbps} kbps")

    aac = os.path.join(BUILD, "audio.m4a")
    run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-af", loudnorm_filter(wav), "-ar", "48000", "-c:a", "aac",
         "-b:a", f"{a.audio_kbps}k", aac])

    x264 = ["-c:v", "libx264", "-preset", "veryslow", "-tune", "animation", "-b:v", f"{vk}k",
            "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.0", "-g", "240", "-keyint_min", "24",
            "-x264-params", "aq-mode=3:aq-strength=0.9:deblock=1,1"]
    log = os.path.join(BUILD, "x264pass")
    run(["ffmpeg", "-v", "error", "-y", "-i", video, *x264, "-pass", "1", "-passlogfile", log, "-an",
         "-f", "null", os.devnull])
    run(["ffmpeg", "-v", "error", "-y", "-i", video, "-i", aac, "-map", "0:v", "-map", "1:a", *x264,
         "-pass", "2", "-passlogfile", log, "-c:a", "copy", "-movflags", "+faststart",
         "-metadata", "title=The First Village", a.out])
    size = os.path.getsize(a.out)
    print(f"{a.out}: {size / 1e6:.2f} MB ({size / 1048576:.2f} MiB)")


if __name__ == "__main__":
    main()
