#!/usr/bin/env python3
"""Build tool for the video.

  python3 build.py tts                 # synthesize voice lines + lipsync + timeline
  python3 build.py timeline            # rebuild timeline from cached durations
  python3 build.py still <sid> <t> [out.png] [--scale 0.5]
  python3 build.py sheet <sid> [--n 12] [--cols 4] [--t0 a --t1 b]   # contact sheet PNG
  python3 build.py scene <sid> [--res 720]   # render scene segment video
  python3 build.py video [--res 720]         # render all scene segments + concat
  python3 build.py audio                     # mix voice + music + sfx -> out/mix.wav
  python3 build.py final [--mb 14.2]         # encode deliverable mp4 under size budget
  python3 build.py all

Scene modules live in scenes/<module>.py and expose:
  def render(ctx, t, info): ...      # draw frame at scene-local time t (seconds)
  SFX(info) -> [(time, name, gain_db), ...]   (optional; scene-local times)
  CAPTION_Y / caption_y(t, info)               (optional)
"""
import argparse
import importlib
import json
import math
import os
import subprocess
import sys
import time
from multiprocessing import Pool

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import cairocffi as cairo  # noqa: E402
from engine import core  # noqa: E402
from engine.timeline import Timeline, build_timeline  # noqa: E402
from engine.captions import draw_captions  # noqa: E402

OUT = os.path.join(ROOT, "out")
PREVIEW = os.path.join(ROOT, "preview")
FPS = core.FPS

os.environ.setdefault("FONTCONFIG_PATH", "/etc/fonts")


def ensure_fonts():
    """Make the bundled fonts visible to fontconfig (idempotent)."""
    dst = os.path.expanduser("~/.local/share/fonts")
    src = os.path.join(ROOT, "assets", "fonts")
    os.makedirs(dst, exist_ok=True)
    changed = False
    for f in os.listdir(src):
        if not os.path.exists(os.path.join(dst, f)):
            subprocess.run(["cp", os.path.join(src, f), dst])
            changed = True
    if changed:
        subprocess.run(["fc-cache", "-f"], stdout=subprocess.DEVNULL)


def load_scene(module):
    return importlib.import_module(f"scenes.{module}")


def render_frame(info, mod, t, out_w, out_h, captions=True):
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, out_w, out_h)
    ctx = cairo.Context(surf)
    ctx.scale(out_w / core.W, out_h / core.H)
    ctx.set_source_rgb(0, 0, 0)
    ctx.paint()
    ctx.save()
    mod.render(ctx, t, info)
    ctx.restore()
    if captions:
        ctx.save()
        draw_captions(ctx, info, t, mod)
        ctx.restore()
    surf.flush()
    return surf


def res_dims(res):
    w = int(res)
    h = int(round(w * 16 / 9))
    return w - (w % 2), h - (h % 2)


# ---------------------------------------------------------------------------
# previews
# ---------------------------------------------------------------------------
def cmd_still(sid, t, out=None, scale=0.5, captions=True):
    ensure_fonts()
    tl = Timeline()
    info = tl.scene(sid)
    mod = load_scene(info.module)
    w, h = int(core.W * scale), int(core.H * scale)
    surf = render_frame(info, mod, float(t), w, h, captions)
    os.makedirs(PREVIEW, exist_ok=True)
    out = out or os.path.join(PREVIEW, f"{sid}_{float(t):07.2f}.png")
    surf.write_to_png(out)
    print(out)
    return out


def cmd_sheet(sid, n=12, cols=4, t0=None, t1=None, out=None, cell_w=270, captions=True,
              times=None):
    """Contact sheet: n evenly spaced frames (or explicit times) with timestamps."""
    ensure_fonts()
    tl = Timeline()
    info = tl.scene(sid)
    mod = load_scene(info.module)
    t0 = 0.0 if t0 is None else t0
    t1 = info.dur - 1 / FPS if t1 is None else t1
    if times is None:
        times = [t0 + (t1 - t0) * i / max(1, n - 1) for i in range(n)]
    n = len(times)
    rows = math.ceil(n / cols)
    cw, ch = cell_w, int(cell_w * 16 / 9)
    pad, lab = 8, 26
    sheet = cairo.ImageSurface(cairo.FORMAT_RGB24, cols * (cw + pad) + pad,
                               rows * (ch + pad + lab) + pad)
    sc = cairo.Context(sheet)
    sc.set_source_rgb(0.12, 0.12, 0.14)
    sc.paint()
    for i, t in enumerate(times):
        r, c = divmod(i, cols)
        x = pad + c * (cw + pad)
        y = pad + r * (ch + pad + lab)
        fr = render_frame(info, mod, t, cw, ch, captions)
        sc.set_source_surface(fr, x, y + lab)
        sc.paint()
        line = info.active_line(t)
        label = f"{t:6.2f}s" + (f"  {line.who}" if line else "")
        core.text(sc, label, x + 4, y + 19, 17, "#dddddd", "mono", "left")
    os.makedirs(PREVIEW, exist_ok=True)
    out = out or os.path.join(PREVIEW, f"sheet_{sid}.png")
    sheet.write_to_png(out)
    print(out)
    return out


# ---------------------------------------------------------------------------
# video
# ---------------------------------------------------------------------------
def _render_chunk(args):
    sid, f0, f1, w, h, path = args
    ensure_fonts()
    tl = Timeline()
    info = tl.scene(sid)
    mod = load_scene(info.module)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr0",
           "-s", f"{w}x{h}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "veryfast", "-qp", "0", "-pix_fmt", "yuv444p", path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(f0, f1):
        surf = render_frame(info, mod, f / FPS, w, h)
        p.stdin.write(bytes(surf.get_data()))
    p.stdin.close()
    p.wait()
    return path


def scene_frames(info):
    return int(round(info.dur * FPS))


def cmd_scene(sid, res=720, procs=4):
    tl = Timeline()
    info = tl.scene(sid)
    w, h = res_dims(res)
    n = scene_frames(info)
    seg_dir = os.path.join(OUT, "seg")
    os.makedirs(seg_dir, exist_ok=True)
    k = max(1, min(procs, n // 24))
    bounds = [round(n * i / k) for i in range(k + 1)]
    jobs = [(sid, bounds[i], bounds[i + 1], w, h, os.path.join(seg_dir, f"{sid}_{i}.mkv"))
            for i in range(k)]
    t = time.time()
    with Pool(k) as pool:
        parts = pool.map(_render_chunk, jobs)
    lst = os.path.join(seg_dir, f"{sid}.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{os.path.basename(p)}'\n" for p in parts)
    out = os.path.join(seg_dir, f"{sid}.mkv")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", lst, "-c", "copy", out], check=True)
    for p in parts:
        os.remove(p)
    print(f"[scene] {sid}: {n} frames in {time.time()-t:.1f}s -> {out}", file=sys.stderr)
    return out


def cmd_video(res=720, only=None):
    tl = Timeline()
    segs = []
    for s in tl.scenes:
        if only and s.id not in only:
            segs.append(os.path.join(OUT, "seg", f"{s.id}.mkv"))
            continue
        segs.append(cmd_scene(s.id, res))
    lst = os.path.join(OUT, "seg", "all.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{os.path.basename(p)}'\n" for p in segs)
    out = os.path.join(OUT, "video_master.mkv")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", lst, "-c", "copy", out], check=True)
    print(out)
    return out


# ---------------------------------------------------------------------------
# audio + final
# ---------------------------------------------------------------------------
def cmd_tts():
    from audio import tts
    durations = tts.run()
    build_timeline(durations)
    tl = Timeline()
    print(f"[timeline] total {tl.total:.2f}s over {len(tl.scenes)} scenes", file=sys.stderr)
    for s in tl.scenes:
        print(f"  {s.id:5s} {s.module:24s} start {s.start:7.2f}  dur {s.dur:6.2f}",
              file=sys.stderr)


def cmd_timeline():
    with open(os.path.join(OUT, "durations.json")) as f:
        build_timeline(json.load(f))
    tl = Timeline()
    print(f"[timeline] total {tl.total:.2f}s", file=sys.stderr)


def cmd_audio():
    from audio import mix
    return mix.run()


def cmd_final(mb=14.2, audio_kbps=80, res=720):
    """Two-pass x264 sized to fit `mb` megabytes (MiB = 2^20 bytes)."""
    tl = Timeline()
    dur = tl.total
    master = os.path.join(OUT, "video_master.mkv")
    mixwav = os.path.join(OUT, "mix.wav")
    total_kbit = mb * 1024 * 1024 * 8 / 1000
    v_kbps = int(total_kbit / dur - audio_kbps - 6)  # 6 kbps container overhead
    print(f"[final] dur {dur:.1f}s -> video {v_kbps} kbps, audio {audio_kbps} kbps",
          file=sys.stderr)
    final = os.path.join(ROOT, "AI_vs_Evil_Genius_portrait.mp4")
    common = ["-c:v", "libx264", "-preset", "veryslow", "-tune", "animation",
              "-profile:v", "high", "-level", "4.0", "-pix_fmt", "yuv420p",
              "-b:v", f"{v_kbps}k", "-maxrate", f"{int(v_kbps*2.5)}k",
              "-bufsize", f"{int(v_kbps*5)}k", "-g", str(FPS * 8), "-keyint_min", str(FPS),
              "-x264-params", "aq-mode=3:aq-strength=0.9:psy-rd=0.8,0.0:deblock=1,1"]
    passlog = os.path.join(OUT, "x264pass")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", master] + common +
                   ["-pass", "1", "-passlogfile", passlog, "-an", "-f", "mp4", "/dev/null"],
                   check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", master, "-i", mixwav] + common +
                   ["-pass", "2", "-passlogfile", passlog,
                    "-c:a", "aac", "-b:a", f"{audio_kbps}k", "-ar", "48000", "-ac", "2",
                    "-movflags", "+faststart", "-shortest", final], check=True)
    size = os.path.getsize(final)
    print(f"[final] {final}: {size/1024/1024:.2f} MiB ({size/1e6:.2f} MB)", file=sys.stderr)
    return final


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("args", nargs="*")
    ap.add_argument("--scale", type=float, default=0.5)
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--t0", type=float)
    ap.add_argument("--t1", type=float)
    ap.add_argument("--times", type=str, help="comma list of times for sheet")
    ap.add_argument("--res", type=int, default=720)
    ap.add_argument("--mb", type=float, default=14.2)
    ap.add_argument("--nocap", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args()
    if a.cmd == "tts":
        cmd_tts()
    elif a.cmd == "timeline":
        cmd_timeline()
    elif a.cmd == "still":
        cmd_still(a.args[0], a.args[1], a.out or (a.args[2] if len(a.args) > 2 else None),
                  a.scale, not a.nocap)
    elif a.cmd == "sheet":
        times = [float(x) for x in a.times.split(",")] if a.times else None
        cmd_sheet(a.args[0], a.n, a.cols, a.t0, a.t1, a.out, captions=not a.nocap, times=times)
    elif a.cmd == "scene":
        cmd_scene(a.args[0], a.res)
    elif a.cmd == "video":
        cmd_video(a.res, a.args or None)
    elif a.cmd == "audio":
        cmd_audio()
    elif a.cmd == "final":
        cmd_final(a.mb, res=a.res)
    elif a.cmd == "all":
        cmd_tts()
        cmd_video(a.res)
        cmd_audio()
        cmd_final(a.mb)
    else:
        ap.error(f"unknown command {a.cmd}")


if __name__ == "__main__":
    main()
