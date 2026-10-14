"""Final encode: H.264 + AAC MP4 for phones/social media, kept under 15 MB.

Two-pass x264 aimed at a fixed file size, 1080x1920 at 30 fps, faststart
(the moov atom sits at the front so uploads and previews start at once).

Usage: python encode.py [--cartoon] [--mb 14.3] [--abr 128]
"""
import argparse
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build")
OUT = os.path.join(ROOT, "Bunny_Girl_and_Wolf_Dog.mp4")
OUT_CARTOON = os.path.join(ROOT, "Bunny_Girl_and_Wolf_Dog_Cartoon.mp4")


def probe_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mb", type=float, default=14.3, help="target size in MB (10^6 bytes)")
    ap.add_argument("--abr", type=int, default=128, help="audio bitrate, kbps")
    ap.add_argument("--preset", default="veryslow")
    ap.add_argument("--cartoon", action="store_true", help="encode the cartoon version")
    args = ap.parse_args()

    if args.cartoon:
        video, audio, out = (os.path.join(BUILD, "cartoon_noaudio.mp4"), os.path.join(BUILD, "mix_cartoon.wav"), OUT_CARTOON)
    else:
        video, audio, out = os.path.join(BUILD, "video_noaudio.mp4"), os.path.join(BUILD, "mix.wav"), OUT
    dur = probe_duration(video)
    budget_bits = args.mb * 1e6 * 8 - args.abr * 1000 * dur - 0.12e6 * 8  # minus audio + mp4 overhead
    vbr = int(budget_bits / dur / 1000)
    print(f"duration {dur:.2f}s -> video {vbr} kbps + audio {args.abr} kbps")

    x264 = ["-c:v", "libx264", "-preset", args.preset, "-profile:v", "high", "-level:v", "4.0",
            "-pix_fmt", "yuv420p", "-b:v", f"{vbr}k", "-maxrate", f"{int(vbr * 2.6)}k", "-bufsize", f"{vbr * 4}k",
            "-g", "120", "-keyint_min", "15", "-x264-params", "aq-mode=3:aq-strength=0.9:deblock=1,1",
            "-r", "30", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709"]
    log = os.path.join(BUILD, "x264pass")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", video, *x264,
                    "-pass", "1", "-passlogfile", log, "-an", "-f", "mp4", os.devnull], check=True)
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", video, "-i", audio,
                    "-map", "0:v:0", "-map", "1:a:0", *x264, "-pass", "2", "-passlogfile", log,
                    "-c:a", "aac", "-b:a", f"{args.abr}k", "-ar", "48000", "-ac", "2",
                    "-shortest", "-movflags", "+faststart",
                    "-metadata", "title=Bunny Girl and Wolf Dog", out], check=True)
    for f in os.listdir(BUILD):
        if f.startswith("x264pass"):
            os.remove(os.path.join(BUILD, f))
    size = os.path.getsize(out)
    print(f"{out}: {size / 1e6:.2f} MB ({size / 2**20:.2f} MiB)")


if __name__ == "__main__":
    main()
