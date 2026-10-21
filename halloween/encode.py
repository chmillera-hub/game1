"""Final encode: lossless master chunks + mix.wav -> phone-ready MP4 under a size budget.

  python3 encode.py --target-mb 14.4 [--height 1920] [--audio-kbps 64]
  python3 encode.py --build song/build --chunks mv_chunks --mix song_mix.wav --outdir song/out \
      --audio-kbps 128 --limit 0.66 --static-gain --name clickety_clack.mp4 --title "Clickety-Clack"
"""
import argparse
import json
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
OUTDIR = os.path.join(HERE, "out")


def run(cmd, capture=False):
    print("+", " ".join(cmd)[:200])
    if capture:
        return subprocess.run(cmd, check=True, capture_output=True, text=True)
    subprocess.run(cmd, check=True)


def probe_duration(path):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", path], capture=True)
    return float(json.loads(r.stdout)["format"]["duration"])


def master(chunks="chunks"):
    m = os.path.join(BUILD, "master.mkv")
    if not os.path.exists(m):
        run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i",
             os.path.join(BUILD, chunks, "list.txt"), "-c", "copy", m])
    return m


def audio(kbps, mix="mix.wav", limit=0.56, static_gain=False):
    """Two-pass loudness normalisation to -14 LUFS / -1.5 dBTP, then AAC.

    static_gain: one fixed gain to -14 LUFS and let the peak limiter catch the rest, instead of
    loudnorm's dynamic fallback (keeps a song's quiet intro quiet)."""
    src = os.path.join(BUILD, mix)
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", src, "-af",
             "loudnorm=I=-14:TP=-1.5:LRA=9:print_format=json", "-f", "null", "-"], capture=True)
    js = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S).group(0))
    if static_gain:
        af = f"volume={-14.0 - float(js['input_i']):.2f}dB"
    else:
        af = ("loudnorm=I=-14:TP=-1.5:LRA=9:measured_I={input_i}:measured_TP={input_tp}:measured_LRA={input_lra}:"
              "measured_thresh={input_thresh}:offset={target_offset}:linear=true").format(**js)
    out = os.path.join(BUILD, f"audio_{kbps}k.m4a")
    # brick-wall the peaks so AAC overshoot at low bitrates stays under 0 dBFS
    af += f",aresample=192000,alimiter=limit={limit}:attack=1:release=80:level=false,aresample=48000"
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-af", af, "-c:a", "aac",
         "-b:a", f"{kbps}k", "-ac", "2", out])
    return out


def video(m, height, kbps, preset, tag):
    width = height * 9 // 16
    # the master was converted from RGB with the BT.601 matrix; deliver BT.709 like phones expect
    scale = ["-vf", f"scale={width}:{height}:flags=lanczos:in_color_matrix=bt601:out_color_matrix=bt709"]
    out = os.path.join(BUILD, f"video_{tag}.mp4")
    common = ["-c:v", "libx264", "-preset", preset, "-tune", "animation", "-profile:v", "high", "-pix_fmt", "yuv420p",
              "-b:v", f"{kbps}k", "-maxrate", f"{int(kbps * 2.2)}k", "-bufsize", f"{int(kbps * 6)}k",
              "-x264-params", "aq-mode=3:aq-strength=0.9:keyint=240:min-keyint=24",
              "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-r", "24"]
    plog = os.path.join(BUILD, f"x264_{tag}")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", m] + scale + common +
        ["-pass", "1", "-passlogfile", plog, "-an", "-f", "mp4", os.devnull])
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", m] + scale + common +
        ["-pass", "2", "-passlogfile", plog, "-an", out])
    return out


def mux(v, a, out, title="TOO MOM - a Halloween tale"):
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", v, "-i", a, "-map", "0:v:0", "-map", "1:a:0", "-c", "copy",
         "-movflags", "+faststart", "-metadata", f"title={title}", out])


def ssim(enc, m, height):
    # pair frames by index: the master's millisecond MKV timestamps can otherwise
    # match an encoded frame with its neighbour (a different drawing when animating on twos)
    ref = "[1:v]setpts=N/(24*TB),scale=in_color_matrix=bt601:out_color_matrix=bt709[r]"
    if height != 1920:
        vf = f"[0:v]setpts=N/(24*TB),scale=1080:1920:flags=bicubic[a];{ref};[a][r]ssim"
    else:
        vf = f"[0:v]setpts=N/(24*TB)[a];{ref};[a][r]ssim"
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", enc, "-i", m, "-lavfi", vf, "-f", "null", "-"],
            capture=True)
    line = [ln for ln in r.stderr.splitlines() if "SSIM" in ln][-1]
    return line.split("SSIM")[1].strip()


def main():
    global BUILD
    ap = argparse.ArgumentParser()
    ap.add_argument("--target-mb", type=float, default=14.4)
    ap.add_argument("--height", type=int, default=1920)
    ap.add_argument("--audio-kbps", type=int, default=64)
    ap.add_argument("--preset", default="slower")
    ap.add_argument("--name", default="too_mom_halloween.mp4")
    ap.add_argument("--remux", action="store_true", help="reuse the encoded video, redo audio + mux only")
    ap.add_argument("--build", default=BUILD, help="build directory holding the chunks and the mix")
    ap.add_argument("--chunks", default="chunks")
    ap.add_argument("--mix", default="mix.wav")
    ap.add_argument("--outdir", default=OUTDIR)
    ap.add_argument("--limit", type=float, default=0.56, help="peak limiter ceiling (linear) before AAC")
    ap.add_argument("--title", default="TOO MOM - a Halloween tale")
    ap.add_argument("--static-gain", action="store_true", help="fixed gain + limiter instead of loudnorm")
    args = ap.parse_args()
    BUILD = os.path.abspath(args.build)
    os.makedirs(args.outdir, exist_ok=True)
    m = master(args.chunks)
    dur = probe_duration(m)
    total_kbps = args.target_mb * 1e6 * 8 / 1000 / dur
    vkbps = int((total_kbps - args.audio_kbps) * 0.985)
    print(f"duration {dur:.2f}s  total {total_kbps:.0f} kbps  video {vkbps} kbps")
    a = audio(args.audio_kbps, args.mix, args.limit, args.static_gain)
    v = os.path.join(BUILD, f"video_{args.height}p.mp4")
    if not (args.remux and os.path.exists(v)):
        v = video(m, args.height, vkbps, args.preset, f"{args.height}p")
    out = os.path.join(args.outdir, args.name)
    mux(v, a, out, args.title)
    size = os.path.getsize(out)
    print(f"output {out}  {size / 1e6:.2f} MB")
    print("SSIM vs lossless master:", ssim(out, m, args.height))


if __name__ == "__main__":
    main()
