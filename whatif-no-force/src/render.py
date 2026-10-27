"""Frame renderer + segment encoder.

  python render.py --png 12.5 40.0          # still frames at given seconds
  python render.py --seg 0 4                # render segment 0 of 4 to build/video
"""
import argparse
import importlib
import os
import subprocess
import sys
import time

import numpy as np
import skia

import paths
import shots_diner
import subtitles
from anchors import resolve, total
from direction import SHOTS
from gfx import draw_text, font, hexc

W, H, FPS = paths.W, paths.H, paths.FPS


def _load(name):
    try:
        return importlib.import_module(name)
    except Exception as e:  # noqa
        print(f"[render] module {name} unavailable: {e}", file=sys.stderr)
        return None


SKETCH = _load("scene_sketch")


def resolved_shots():
    out = []
    starts = [resolve(s["start"]) for s in SHOTS]
    T = total()
    for i, s in enumerate(SHOTS):
        st = starts[i]
        en = starts[i + 1] if i + 1 < len(SHOTS) else T
        d = dict(s)
        d["start"], d["end"] = st, en
        d["cue_t"] = {k: resolve(v) - st for k, v in s.get("cues", {}).items()}
        out.append(d)
    return out


SHOT_LIST = None


def shot_at(t):
    global SHOT_LIST
    if SHOT_LIST is None:
        SHOT_LIST = resolved_shots()
    for s in reversed(SHOT_LIST):
        if t >= s["start"]:
            return s
    return SHOT_LIST[0]


def placeholder(c, s, t):
    c.clear(hexc("#141b33"))
    draw_text(c, s["scene"], 540, 900, font(60), hexc("#ffffff"))
    draw_text(c, f"{t - s['start']:.2f}s", 540, 980, font(40), hexc("#9fb0d8"))


_AUX = None


def render_frame(c, t):
    """Render the frame at time t; shots with trans=('fade', d) dissolve from the previous shot."""
    global _AUX
    s = shot_at(t)
    tr = s.get("trans")
    if tr and tr[0] == "fade" and t < s["start"] + tr[1]:
        idx = SHOT_LIST.index(s)
        prev = SHOT_LIST[idx - 1] if idx > 0 else None
        if prev is not None:
            if _AUX is None:
                arr = np.zeros((H, W, 4), np.uint8)
                _AUX = (arr, skia.Surface(arr))
            arr, surf = _AUX
            c2 = surf.getCanvas()
            c2.save()
            c2.clear(hexc("#000000"))
            _render_shot(c2, prev, t)
            c2.restore()
            _render_shot(c, s, t)
            u = (t - s["start"]) / tr[1]
            a = 1.0 - u * u * (3 - 2 * u)
            img = skia.Image.fromarray(arr, colorType=skia.kRGBA_8888_ColorType)
            c.drawImage(img, 0, 0, skia.SamplingOptions(), skia.Paint(Alphaf=a))
            subtitles.draw(c, t)
            return
    _render_shot(c, s, t)
    subtitles.draw(c, t)


def _render_shot(c, s, t):
    scene = s["scene"]
    lt = t - s["start"]
    dur = s["end"] - s["start"]
    if scene == "diner":
        shots_diner.render(c, t, s)
    else:
        fn = None
        for mod in (SKETCH,):
            if mod is not None and scene in getattr(mod, "SCENES", {}):
                fn = mod.SCENES[scene]
        if fn is None:
            placeholder(c, s, t)
        else:
            c.save()
            fn(c, lt, dur, s["cue_t"], s.get("params", {}))
            c.restore()


def frame_count():
    return int(round(total() * FPS))


def render_segment(k, n, crf=8):
    N = frame_count()
    a = N * k // n
    b = N * (k + 1) // n
    out = os.path.join(paths.VIDEO, f"seg_{k:02d}.mkv")
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", str(crf),
           "-pix_fmt", "yuv420p", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    arr = np.zeros((H, W, 4), np.uint8)
    surf = skia.Surface(arr)
    c = surf.getCanvas()
    t0 = time.time()
    for i in range(a, b):
        c.save()
        c.clear(hexc("#000000"))
        render_frame(c, i / FPS)
        c.restore()
        p.stdin.write(arr.tobytes())
        if (i - a) % 240 == 0:
            el = time.time() - t0
            print(f"[seg {k}] {i - a}/{b - a} frames, {el:.0f}s", flush=True)
    p.stdin.close()
    p.wait()
    print(f"[seg {k}] done {b - a} frames in {time.time() - t0:.0f}s -> {out}", flush=True)


def render_pngs(times, outdir):
    from PIL import Image
    os.makedirs(outdir, exist_ok=True)
    arr = np.zeros((H, W, 4), np.uint8)
    surf = skia.Surface(arr)
    c = surf.getCanvas()
    for t in times:
        c.save()
        c.clear(hexc("#000000"))
        t0 = time.time()
        render_frame(c, t)
        c.restore()
        fn = os.path.join(outdir, f"f_{t:07.2f}.png")
        Image.fromarray(arr[:, :, :3].copy()).save(fn)
        print(f"{fn}  {1000 * (time.time() - t0):.0f} ms  [{shot_at(t)['id']} {shot_at(t)['scene']}]")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--png", nargs="*", type=float)
    ap.add_argument("--out", default=os.path.join(paths.BUILD, "stills"))
    ap.add_argument("--seg", nargs=2, type=int)
    ap.add_argument("--crf", type=int, default=8)
    args = ap.parse_args()
    if args.png:
        render_pngs(args.png, args.out)
    elif args.seg:
        render_segment(args.seg[0], args.seg[1], args.crf)
