"""Render the animation.

  python3 render.py --test 12.5 40 ...   -> build/test/frame_<t>.png stills
  python3 render.py                      -> build/video_master.mkv (lossless-ish master, no audio)
"""
import multiprocessing as mp
import os
import subprocess
import sys
import time

import numpy as np
import skia

from anim import FPS, H, HERE, W, clamp, font, paint, ramp, text_w, wrap
import scenes
from scenes import TL

BUILD = os.path.join(HERE, "build")
CAP_Y = 1018          # caption block centre; clear of phone UI at the bottom
CAPTIONS = os.environ.get("CAPTIONS", "1") == "1"

STYLES = {
    "narration": ("italic", 37, 560, (250, 244, 232)),
    "dialogue": ("serif", 37, 640, (255, 255, 255)),
    "god": ("italic", 42, 600, (255, 222, 150)),
    "fear": ("italic", 37, 560, (176, 186, 214)),
}


def caption(cv, t):
    for it in TL.lines:
        if not (it["start"] - 0.05 <= t <= it["end"] + 0.4):
            continue
        caps = it["caps"]
        k = 0
        for i, (cs, _) in enumerate(caps):
            if t >= cs - 0.05:
                k = i
        start = caps[k][0]
        stop = caps[k + 1][0] if k + 1 < len(caps) else it["end"] + 0.4
        a = clamp((t - start + 0.05) / 0.15) * clamp((stop - t) / 0.15 if k + 1 == len(caps) else 1)
        name, size, wght, col = STYLES[it["style"]]
        f = font(name, size, wght)
        lines = wrap(caps[k][1], f, 620)
        lh = size * 1.18
        y0 = CAP_Y - (len(lines) - 1) * lh / 2
        top, bot = y0 - size * 1.4, y0 + (len(lines) - 1) * lh + size * 0.9
        cv.drawRect(skia.Rect.MakeLTRB(0, top, W, bot), paint(shader=skia.GradientShader.MakeLinear(
            [skia.Point(0, top), skia.Point(0, bot)],
            [skia.ColorSetARGB(0, 0, 0, 0), skia.ColorSetARGB(int(95 * a), 0, 0, 0),
             skia.ColorSetARGB(int(95 * a), 0, 0, 0), skia.ColorSetARGB(0, 0, 0, 0)], [0, 0.3, 0.7, 1])))
        for j, ln in enumerate(lines):
            x = (W - text_w(ln, f)) / 2
            y = y0 + j * lh
            cv.drawString(ln, x, y + 2, f, paint((0, 0, 0), 0.75 * a, blur=5))
            cv.drawString(ln, x, y, f, paint((0, 0, 0), 0.7 * a, stroke=4.5))
            if it["style"] == "god":
                cv.drawString(ln, x, y, f, paint((255, 190, 90), 0.6 * a, blur=8))
            cv.drawString(ln, x, y, f, paint(col, a))
        return


def frame(cv, t):
    cv.clear(skia.ColorBLACK)
    cv.save()
    scenes.draw_frame(cv, t)
    cv.restore()
    if CAPTIONS:
        caption(cv, t)
    total = TL.marks["total"]
    fade = max(1 - ramp(t, 0, 0.8), ramp(t, total - 1.4, total - 0.1))
    if fade > 0:
        cv.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), fade))


_surface = None


def render_index(i):
    global _surface
    if _surface is None:
        _surface = skia.Surface(W, H)
    cv = _surface.getCanvas()
    frame(cv, i / FPS)
    return _surface.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)[:, :, :3].tobytes()


def test(times):
    os.makedirs(os.path.join(BUILD, "test"), exist_ok=True)
    s = skia.Surface(W, H)
    for t in times:
        t0 = time.time()
        frame(s.getCanvas(), float(t))
        s.makeImageSnapshot().save(os.path.join(BUILD, "test", f"frame_{float(t):06.2f}.png"), skia.kPNG)
        print(f"t={t} rendered in {time.time() - t0:.3f}s")


def main(start=0.0, end=None):
    total = TL.marks["total"] if end is None else end
    n0, n1 = int(start * FPS), int(round(total * FPS))
    out = os.path.join(BUILD, "video_master.mkv")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "8",
                            "-pix_fmt", "yuv444p", out], stdin=subprocess.PIPE)
    t0 = time.time()
    with mp.Pool(os.cpu_count()) as pool:
        for k, buf in enumerate(pool.imap(render_index, range(n0, n1), chunksize=8)):
            enc.stdin.write(buf)
            if k % 240 == 0:
                el = time.time() - t0
                print(f"frame {n0 + k}/{n1}  {el:.0f}s elapsed  {(k + 1) / max(el, 1e-3):.1f} fps", flush=True)
    enc.stdin.close()
    enc.wait()
    print(f"done in {time.time() - t0:.0f}s -> {out}")


if __name__ == "__main__":
    if "--test" in sys.argv:
        test(sys.argv[sys.argv.index("--test") + 1:])
    else:
        main()
