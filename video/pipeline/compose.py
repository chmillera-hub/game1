"""Assemble rendered shots into the final portrait video.

python3 compose.py [--master-only]
  1. per-shot grade + upscale 432x768 -> 540x960, piped to a lossless FFV1 master with burned subtitles
  2. two-pass H.264 (and HEVC) encodes sized under 15 MB, SSIM measured against the master
"""
import json, os, re, subprocess, sys
import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, os.path.dirname(__file__))
from shots import shot_bounds

W, H, FPS = 540, 960, 24
TL = json.load(open("/opt/work/timeline.json"))
LINES = {l["id"]: l for l in TL["lines"]}
DUR = TL["duration"]
NF = int(round(DUR * FPS))
FRAMES = "/opt/work/frames"
OUTDIR = "/home/user/game1/video"
MASTER = "/opt/work/master.mkv"

GRADE = {  # (lift rgb, gain rgb, saturation, contrast)
    "colonnade": ((0.012, 0.016, 0.022), (1.00, 0.99, 0.97), 0.95, 1.06),
    "hillside": ((0.02, 0.012, 0.0), (1.04, 0.99, 0.92), 1.05, 1.04),
    "scroll": ((0.015, 0.01, 0.0), (1.03, 1.0, 0.94), 1.0, 1.05),
    "upper_room": ((0.006, 0.006, 0.014), (1.05, 0.99, 0.90), 1.02, 1.08),
    "apartment": ((0.004, 0.008, 0.018), (0.97, 0.99, 1.04), 0.92, 1.06),
    "sister_kitchen": ((0.01, 0.008, 0.004), (1.03, 1.0, 0.95), 0.96, 1.05),
    "hallway_door": ((0.008, 0.008, 0.01), (1.03, 1.0, 0.96), 0.98, 1.05),
    "cosmos": ((0.0, 0.0, 0.006), (1.0, 1.0, 1.02), 1.05, 1.04),
    "city": ((0.0, 0.004, 0.016), (0.97, 0.99, 1.05), 1.0, 1.06),
}


def vignette():
    y, x = np.mgrid[0:H, 0:W]
    r = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
    return np.clip(1.0 - 0.28 * np.clip(r - 0.55, 0, None) ** 1.6, 0.6, 1.0)[..., None]


VIG = vignette()


def grade(img, set_name):
    lift, gain, sat, con = GRADE.get(set_name, GRADE["colonnade"])
    a = np.asarray(img, dtype=np.float32) / 255.0
    a = a * np.array(gain) + np.array(lift)
    lum = (a * np.array([0.2126, 0.7152, 0.0722])).sum(axis=2, keepdims=True)
    a = lum + (a - lum) * sat
    a = (a - 0.5) * con + 0.5
    a = a * VIG
    return (np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)


def shot_frame(sid, f, n, step=1):
    p = f"{FRAMES}/{sid}/{f:04d}.png"
    if os.path.exists(p):
        return Image.open(p).convert("RGB")
    # frame-stepped shots: blend the two neighbours
    lo = ((f - 1) // step) * step + 1
    hi = min(lo + step, n)
    a, b = f"{FRAMES}/{sid}/{lo:04d}.png", f"{FRAMES}/{sid}/{hi:04d}.png"
    if os.path.exists(a) and os.path.exists(b) and hi != lo:
        u = (f - lo) / (hi - lo)
        return Image.blend(Image.open(a).convert("RGB"), Image.open(b).convert("RGB"), u)
    if os.path.exists(a):
        return Image.open(a).convert("RGB")
    # nearest existing frame of the shot, else black
    d = f"{FRAMES}/{sid}"
    if os.path.isdir(d):
        fs = sorted(os.listdir(d))
        if fs:
            nums = [int(x[:4]) for x in fs if x[:4].isdigit()]
            k = min(nums, key=lambda q: abs(q - f))
            return Image.open(f"{d}/{k:04d}.png").convert("RGB")
    return Image.new("RGB", (432, 768), (0, 0, 0))


# ----------------------------------------------------------------------------- subtitles
def ass_time(t):
    t = max(0.0, t)
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def chunks(line, maxc=34):
    """Split a line into subtitle chunks of <= 2 lines of maxc chars, timed from its words."""
    text = line["text"]
    words_t = line["words"]
    toks = text.split()
    # map text tokens to timed words in order (lengths match closely; fall back to proportional)
    times = []
    j = 0
    for i, tk in enumerate(toks):
        clean = re.sub(r"[^a-z']", "", tk.lower())
        found = None
        for k in range(j, min(j + 4, len(words_t))):
            if re.sub(r"[^a-z']", "", words_t[k]["word"].lower()) == clean:
                found = k
                break
        if found is not None:
            times.append((words_t[found]["start"], words_t[found]["end"]))
            j = found + 1
        else:
            frac0, frac1 = i / len(toks), (i + 1) / len(toks)
            times.append((line["start"] + (line["end"] - line["start"]) * frac0,
                          line["start"] + (line["end"] - line["start"]) * frac1))
    out, cur, cur_t = [], [], []
    for tk, tt in zip(toks, times):
        trial = " ".join(cur + [tk])
        if len(trial) > maxc * 2 - 2 and cur:
            out.append((cur, cur_t))
            cur, cur_t = [], []
        cur.append(tk)
        cur_t.append(tt)
        if re.search(r"[.?!;]$", tk) and len(" ".join(cur)) > maxc * 0.9:
            out.append((cur, cur_t))
            cur, cur_t = [], []
    if cur:
        out.append((cur, cur_t))
    res = []
    for ws, ts in out:
        s = " ".join(ws)
        if len(s) > maxc:  # break into two balanced lines
            best = min(range(1, len(ws)), key=lambda k: abs(len(" ".join(ws[:k])) - len(" ".join(ws[k:]))))
            s = " ".join(ws[:best]) + r"\N" + " ".join(ws[best:])
        res.append((s, ts[0][0], ts[-1][1]))
    return res


def write_ass(path):
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,DejaVu Sans,29,&H00FFFFFF,&H000000FF,&H00101010,&H80000000,1,0,0,0,100,100,0,0,1,2.2,1.2,2,36,36,250,1
Style: Narr,DejaVu Serif,29,&H00E8F4FF,&H000000FF,&H00101010,&H80000000,0,1,0,0,100,100,0,0,1,2.2,1.2,2,36,36,250,1
Style: Title,DejaVu Serif,64,&H00FFFFFF,&H000000FF,&H00202020,&H80000000,1,0,0,0,100,100,8,0,1,2.5,2,8,30,30,120,1
Style: Small,DejaVu Serif,24,&H00E0E0E0,&H000000FF,&H00202020,&H80000000,0,1,0,0,100,100,2,0,1,1.8,1,8,30,30,200,1
Style: End,DejaVu Serif,30,&H00FFFFFF,&H000000FF,&H00202020,&H80000000,0,1,0,0,100,100,1,0,1,2,1.5,8,30,30,180,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    # title on the very first frame (no fade-in so the thumbnail shows it), fades out
    ev.append(f"Dialogue: 1,{ass_time(0)},{ass_time(3.6)},Title,,0,0,0,,{{\\fad(0,700)}}ONE")
    ev.append(f"Dialogue: 1,{ass_time(0)},{ass_time(3.6)},Small,,0,0,0,,{{\\fad(0,700)}}John 10 · John 17")
    for l in TL["lines"]:
        style = "Narr" if l["speaker"] == "NARRATOR" else "Sub"
        italic_vo = l["speaker"] == "JESUS" and l["scene"] in ("apartment", "cosmos", "city", "door")
        for txt, a, b in chunks(l):
            t0 = a - 0.08
            t1 = b + 0.35
            pre = "{\\i1}" if italic_vo else ""
            ev.append(f"Dialogue: 0,{ass_time(t0)},{ass_time(t1)},{style},,0,0,0,,{pre}{txt}")
    end0 = LINES["L052"]["end"] + 0.4
    ev.append(f"Dialogue: 1,{ass_time(end0)},{ass_time(DUR)},End,,0,0,0,,{{\\fad(600,0)}}John 10:25–39  ·  John 17:20–26")
    # avoid overlapping subtitle events: trim each to the next start
    open(path, "w").write(head + "\n".join(ev) + "\n")
    return path


def fix_overlaps(path):
    lines = open(path).read().splitlines()
    evs = [(i, l) for i, l in enumerate(lines) if l.startswith("Dialogue: 0,")]

    def parse(t):
        h, m, s = t.split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)
    for k in range(len(evs) - 1):
        i, l = evs[k]
        parts = l.split(",", 9)
        nxt = evs[k + 1][1].split(",", 9)
        if parse(parts[2]) > parse(nxt[1]):
            parts[2] = nxt[1]
            lines[i] = ",".join(parts)
    open(path, "w").write("\n".join(lines) + "\n")


def write_srt(path):
    out = []
    k = 1
    for l in TL["lines"]:
        for txt, a, b in chunks(l):
            def st(t):
                return f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{int(t % 60):02d},{int(t * 1000 % 1000):03d}"
            out.append(f"{k}\n{st(max(0, a - 0.08))} --> {st(b + 0.35)}\n{txt.replace(chr(92) + 'N', chr(10))}\n")
            k += 1
    open(path, "w").write("\n".join(out))


# ----------------------------------------------------------------------------- master
def build_master():
    ass = write_ass("/opt/work/subs.ass")
    fix_overlaps(ass)
    write_srt(f"{OUTDIR}/one_john10_john17.srt")
    bounds = shot_bounds(LINES, DUR)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", "/opt/work/audio/final_mix.wav",
           "-vf", f"subtitles={ass}", "-c:v", "ffv1", "-level", "3", "-pix_fmt", "yuv420p",
           "-c:a", "pcm_s16le", "-shortest", MASTER]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    total = 0
    for shot, t0, t1 in bounds:
        f0 = int(round(t0 * FPS))
        f1 = int(round(t1 * FPS))
        n = max(1, int(round((t1 - t0) * FPS)))
        step = shot.get("frame_step", 1)
        for k in range(f1 - f0):
            f = min(n, k + 1)
            img = shot_frame(shot["id"], f, n, step)
            img = img.resize((W, H), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.2, percent=40, threshold=2))
            p.stdin.write(grade(img, shot["set"]).tobytes())
            total += 1
    while total < NF:
        p.stdin.write(grade(img, shot["set"]).tobytes())
        total += 1
    p.stdin.close()
    p.wait()
    print("MASTER_OK", total, "frames")


# ----------------------------------------------------------------------------- delivery encodes
def encode(target_mb=14.2, audio_kbps=80, codec="h264"):
    dur = DUR
    video_kbps = int((target_mb * 8 * 1024 * 1024 / 1000 - audio_kbps * dur - 60) / dur)
    out = f"{OUTDIR}/one_john10_john17{'_hevc' if codec == 'hevc' else ''}.mp4"
    if codec == "h264":
        venc = ["-c:v", "libx264", "-preset", "veryslow", "-tune", "animation", "-profile:v", "high",
                "-x264-params", "aq-mode=3:aq-strength=0.9:psy-rd=0.8,0.0:deblock=-1,-1:ref=6:bframes=5"]
    else:
        venc = ["-c:v", "libx265", "-preset", "slow", "-tag:v", "hvc1"]
    log = f"/opt/work/pass_{codec}"
    base = ["ffmpeg", "-y", "-loglevel", "error", "-i", MASTER, "-pix_fmt", "yuv420p"] + venc + \
           ["-b:v", f"{video_kbps}k", "-maxrate", f"{int(video_kbps * 2.2)}k", "-bufsize", f"{video_kbps * 4}k",
            "-g", "240", "-keyint_min", "24"]
    if codec == "h264":
        subprocess.run(base + ["-pass", "1", "-passlogfile", log, "-an", "-f", "mp4", "/dev/null"], check=True)
        subprocess.run(base + ["-pass", "2", "-passlogfile", log, "-c:a", "aac", "-b:a", f"{audio_kbps}k", "-ac", "2",
                               "-movflags", "+faststart", out], check=True)
    else:
        subprocess.run(base + ["-x265-params", f"pass=1:stats={log}.log:aq-mode=3:psy-rd=1.0", "-an", "-f", "mp4",
                               "/dev/null"], check=True)
        subprocess.run(base + ["-x265-params", f"pass=2:stats={log}.log:aq-mode=3:psy-rd=1.0", "-c:a", "aac", "-b:a",
                               f"{audio_kbps}k", "-ac", "2", "-movflags", "+faststart", out], check=True)
    size = os.path.getsize(out) / 1024 / 1024
    ssim = subprocess.run(["ffmpeg", "-i", out, "-i", MASTER, "-lavfi", "[0:v][1:v]ssim", "-f", "null", "-"],
                          capture_output=True, text=True).stderr
    m = re.search(r"All:([0-9.]+)", ssim)
    print(f"ENCODED {out} {size:.2f} MB video {video_kbps} kbps SSIM {m.group(1) if m else '?'}")
    return out, size, m.group(1) if m else None


if __name__ == "__main__":
    if "--encode-only" not in sys.argv:
        build_master()
    if "--master-only" not in sys.argv:
        encode(codec="h264")
        encode(codec="hevc", target_mb=11.0)
