"""Psalm 22 - delivery encode: 10-bit mezzanine (from composite.py) + audio -> size-capped MP4.

  python comp/encode.py                                  # $WORK/comp/mezz.mp4 -> $WORK/comp/psalm22.mp4 (H.264)
  python comp/encode.py --codec hevc                     # HEVC/x265 two-pass, hvc1 tag -> psalm22_hevc.mp4
  python comp/encode.py --codec both --metrics           # both + SSIM/PSNR against the mezzanine
  python comp/encode.py --mezz M.mkv --out O.mp4 --audio A.wav --max-mb 15 --margin 0.045

Video: H.264 High@4.0, yuv420p 8-bit, 720x1280, 24 fps, two-pass ABR with the bitrate computed from the
duration so that video + audio + container stay under --max-mb (default 15 MB = 15,000,000 bytes) with
--margin headroom; pass 2 is re-run at a lower rate if the file still comes out too big.
10 -> 8 bit conversion uses zimg with a light dither (--dither, default 'ordered') to fight banding in dark
gradients; x264 runs with aq-mode 3 (dark-scene bias), which matters more than the dither at this rate.
Audio: AAC-LC 48 kHz, 64 kbps mono / 80 kbps stereo (or --abr), padded/trimmed to the video length.
+faststart; the first frame is an IDR (x264 always opens with one; verified with ffprobe).
"""
import argparse, json, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WORK = os.environ.get("WORK", "/opt/work/psalm22")

X264_PARAMS = ("keyint=240:min-keyint=24:scenecut=40:aq-mode=3:aq-strength=0.9:"
               "rc-lookahead=60:bframes=4:b-adapt=2:ref=4:deblock=0,0:psy-rd=1.0,0.10")
X265_PARAMS = ("keyint=240:min-keyint=24:aq-mode=3:aq-strength=0.9:rc-lookahead=40:bframes=4:"
               "no-sao=1:deblock=-1,-1:psy-rd=1.5:psy-rdoq=1.0")
COLOR = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv"]


def run(cmd, quiet=True):
    t = time.time()
    r = subprocess.run(cmd, stdout=subprocess.PIPE if quiet else None, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-3000:])
        raise SystemExit("command failed: " + " ".join(cmd[:12]))
    return r, time.time() - t


def probe(path):
    r, _ = run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path])
    return json.loads(r.stdout)


def video_info(path):
    j = probe(path)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    num, den = (int(x) for x in v.get("r_frame_rate", "24/1").split("/"))
    fps = num / den
    dur = float(v.get("duration") or j["format"]["duration"])
    nb = int(v["nb_frames"]) if v.get("nb_frames") else int(round(dur * fps))
    return {"fps": fps, "frames": nb, "duration": nb / fps, "w": v["width"], "h": v["height"]}


def find_audio():
    for name in ("mix.wav", "narration.wav"):
        p = os.path.join(WORK, "audio", name)
        if os.path.exists(p):
            return p
    return None


def encode_audio(src, dst, duration, offset=0.0, kbps=None):
    """AAC-LC; returns (bytes, kbps, channels)."""
    ch = 2
    if src:
        a = next((s for s in probe(src)["streams"] if s["codec_type"] == "audio"), None)
        ch = min(2, int(a.get("channels", 2))) if a else 2
    kbps = kbps or (64 if ch == 1 else 80)
    if src:
        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
        if offset > 0:
            cmd += ["-ss", "%.3f" % offset]
        cmd += ["-i", src, "-af", "apad", "-t", "%.3f" % duration, "-ac", str(ch), "-ar", "48000",
                "-c:a", "aac", "-b:a", "%dk" % kbps, dst]
    else:   # silent track keeps players/platforms happy
        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
               "anullsrc=r=48000:cl=mono", "-t", "%.3f" % duration, "-c:a", "aac", "-b:a", "32k", dst]
        ch, kbps = 1, 32
    run(cmd)
    return os.path.getsize(dst), kbps, ch


def vfilter(dither, w=720, h=1280):
    """10-bit mezzanine -> 8-bit 4:2:0 with zimg dithering ('none'|'ordered'|'random'|'error_diffusion')."""
    if dither == "sws":
        return "format=yuv420p"
    return ("zscale=w=%d:h=%d:dither=%s:filter=lanczos:matrixin=709:matrix=709:transferin=709:transfer=709:"
            "primariesin=709:primaries=709:rangein=limited:range=limited,format=yuv420p" % (w, h, dither))


def video_args(codec, kbps, preset, pass_no, logbase, maxrate=True):
    if codec == "h264":
        a = ["-c:v", "libx264", "-preset", preset or "slow", "-b:v", "%dk" % kbps,
             "-profile:v", "high", "-level:v", "4.0", "-x264-params", X264_PARAMS,
             "-pass", str(pass_no), "-passlogfile", logbase]
        if maxrate:
            a += ["-maxrate", "%dk" % int(kbps * 3), "-bufsize", "%dk" % int(kbps * 6)]
        return a
    p = X265_PARAMS + ":pass=%d:stats=%s.x265stats" % (pass_no, logbase)
    return ["-c:v", "libx265", "-preset", preset or "medium", "-b:v", "%dk" % kbps,
            "-x265-params", p, "-tag:v", "hvc1", "-profile:v", "main"]


def two_pass(mezz, audio_m4a, out, codec, kbps, preset, dither, logbase, info, skip_pass1=False):
    vf = vfilter(dither, info["w"], info["h"])
    t1 = 0.0
    if not skip_pass1:
        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", mezz, "-vf", vf, "-an",
               "-r", "%g" % info["fps"]] + video_args(codec, kbps, preset, 1, logbase) + ["-f", "null", os.devnull]
        if codec == "hevc":
            cmd = [c for c in cmd if c not in ("-tag:v", "hvc1")]
        _, t1 = run(cmd)
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", mezz]
    if audio_m4a:
        cmd += ["-i", audio_m4a]
    cmd += ["-map", "0:v:0"] + (["-map", "1:a:0", "-c:a", "copy"] if audio_m4a else [])
    cmd += ["-vf", vf, "-r", "%g" % info["fps"], "-pix_fmt", "yuv420p"] + \
        video_args(codec, kbps, preset, 2, logbase) + COLOR + \
        ["-movflags", "+faststart", "-metadata", "title=Psalm 22", "-metadata:s:v", "language=eng",
         "-t", "%.4f" % info["duration"], out]
    _, t2 = run(cmd)
    return t1, t2


def first_frame_is_idr(path):
    r, _ = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-read_intervals", "%+#1",
                "-show_entries", "frame=key_frame,pict_type,pts_time", "-of", "json", path])
    fr = json.loads(r.stdout).get("frames", [])
    return bool(fr) and int(fr[0].get("key_frame", 0)) == 1 and fr[0].get("pict_type") == "I"


def metrics(dist, ref, seconds=None):
    """SSIM (all) and PSNR(Y) of `dist` vs the 10-bit mezzanine (both compared in 10-bit)."""
    lim = ["-t", "%.2f" % seconds] if seconds else []
    sync = "format=yuv420p10le,settb=1/24,setpts=N"          # pair frames by index, not by timestamp
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-y"] + lim + ["-i", dist] + lim + ["-i", ref, "-lavfi",
           "[0:v]%s,split[a][c];[1:v]%s,split[b][d];[a][b]ssim;[c][d]psnr" % (sync, sync),
           "-f", "null", "-"]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    ssim = psnr = None
    for ln in r.stderr.splitlines():
        if "SSIM" in ln and "All:" in ln:
            ssim = float(ln.split("All:")[1].split()[0])
        if "PSNR" in ln and "y:" in ln:
            psnr = float(ln.split("y:")[1].split()[0])
    return ssim, psnr


def encode(mezz, out, codec="h264", audio=None, audio_offset=0.0, max_mb=15.0, margin=0.045,
           preset=None, dither="ordered", abr=None, do_metrics=False, metrics_seconds=None, verbose=True):
    info = video_info(mezz)
    dur = info["duration"]
    tmp = os.path.join(os.path.dirname(os.path.abspath(out)), ".enc_" + os.path.basename(out))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    m4a = tmp + ".m4a"
    a_bytes, a_kbps, ch = encode_audio(audio, m4a, dur, audio_offset, abr)
    limit = max_mb * 1e6
    target = limit * (1 - margin)
    overhead = 40000 + info["frames"] * 12           # moov/stts/stsz/stco + mdat headers, generous
    kbps = int((target - a_bytes - overhead) * 8 / dur / 1000)
    if verbose:
        print("encode %s: %d frames %.2fs  audio %s %dk %dch = %.0f kB  -> video %d kbps (target %.2f MB, limit %.2f MB)" %
              (codec, info["frames"], dur, os.path.basename(audio) if audio else "silence", a_kbps, ch,
               a_bytes / 1e3, kbps, target / 1e6, limit / 1e6))
    t0 = time.time()
    t1, t2 = two_pass(mezz, m4a, out, codec, kbps, preset, dither, tmp, info)
    size = os.path.getsize(out)
    tries = 0
    while size > limit * 0.995 and tries < 3:
        kbps = int(kbps * (limit * 0.97 - a_bytes - overhead) / max(1, size - a_bytes - overhead))
        print("  %.2f MB is over the limit -> pass 2 again at %d kbps" % (size / 1e6, kbps))
        _, t2b = two_pass(mezz, m4a, out, codec, kbps, preset, dither, tmp, info, skip_pass1=True)
        t2 += t2b
        size = os.path.getsize(out)
        tries += 1
    res = {"codec": codec, "out": out, "bytes": size, "mb": round(size / 1e6, 3), "video_kbps": kbps,
           "audio_kbps": a_kbps, "duration": round(dur, 3), "pass1_s": round(t1, 1), "pass2_s": round(t2, 1),
           "total_kbps": round(size * 8 / dur / 1000, 1), "first_frame_idr": first_frame_is_idr(out),
           "dither": dither}
    if do_metrics:
        ssim, psnr = metrics(out, mezz, metrics_seconds)
        res.update(ssim=ssim, psnr_y=psnr)
    for f in os.listdir(os.path.dirname(os.path.abspath(out))):
        if f.startswith(".enc_" + os.path.basename(out)):
            try:
                os.remove(os.path.join(os.path.dirname(os.path.abspath(out)), f))
            except OSError:
                pass
    if verbose:
        print("  -> %s  %.3f MB  (%.0f kbps total)  pass1 %.0fs pass2 %.0fs  first-frame IDR: %s%s" %
              (out, size / 1e6, res["total_kbps"], t1, t2, res["first_frame_idr"],
               ("  SSIM %.4f PSNR-Y %.2f dB" % (res["ssim"], res["psnr_y"])) if do_metrics and res.get("ssim") else ""))
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mezz", default=os.path.join(WORK, "comp", "mezz.mp4"))
    ap.add_argument("--out", help="output mp4 (default $WORK/comp/psalm22.mp4; _hevc suffix for HEVC)")
    ap.add_argument("--audio", help="audio file (default $WORK/audio/mix.wav, else narration.wav)")
    ap.add_argument("--audio-offset", type=float, default=0.0, help="seconds to skip in the audio (partial renders)")
    ap.add_argument("--no-audio", action="store_true")
    ap.add_argument("--codec", default="h264", choices=("h264", "hevc", "both"))
    ap.add_argument("--max-mb", type=float, default=15.0, help="hard size limit in MB (1e6 bytes)")
    ap.add_argument("--margin", type=float, default=0.045, help="safety margin below the limit")
    ap.add_argument("--preset", help="x264 preset (default slow) / x265 preset (default medium)")
    ap.add_argument("--dither", default="ordered", choices=("none", "ordered", "random", "error_diffusion", "sws"))
    ap.add_argument("--abr", type=int, help="audio kbps (default 64 mono / 80 stereo)")
    ap.add_argument("--metrics", action="store_true", help="SSIM/PSNR vs the mezzanine")
    ap.add_argument("--metrics-seconds", type=float)
    ap.add_argument("--json", help="write results json here")
    a = ap.parse_args(argv)
    audio = None if a.no_audio else (a.audio or find_audio())
    base = a.out or os.path.join(WORK, "comp", "psalm22.mp4")
    results = []
    for codec in (("h264", "hevc") if a.codec == "both" else (a.codec,)):
        out = base if codec == "h264" or a.codec == "hevc" else base.replace(".mp4", "_hevc.mp4")
        results.append(encode(a.mezz, out, codec, audio, a.audio_offset, a.max_mb, a.margin,
                              a.preset if (a.codec != "both" or codec == "h264") else None, a.dither, a.abr,
                              a.metrics, a.metrics_seconds))
    if a.json:
        json.dump(results, open(a.json, "w"), indent=1)
    return results


if __name__ == "__main__":
    main()
