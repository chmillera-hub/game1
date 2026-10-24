"""Render frames from build/states.pkl and pipe them to ffmpeg.

  python3 render.py stills 0 120.5 ...   -> PNG stills at given seconds
  python3 render.py video                -> build/video_raw.mkv (lossless-ish intermediate)
"""
import os, pickle, subprocess, sys
from multiprocessing import Pool
import cairo
from scenes import W, H, draw_kitchen, draw_card, draw_subtitle, draw_title, draw_end, vignette
from visions import draw_vision

SHOTS = {  # world point, zoom, screen anchor
    "two": (360, 690, 1.15, 360, 640),
    "two_push": (360, 700, 1.15, 360, 650),
    "m": (205, 660, 2.0, 360, 560),
    "mm": (205, 648, 3.0, 360, 540),
    "a": (520, 640, 2.0, 360, 560),
    "aa": (520, 625, 3.0, 360, 540),
    "window": (200, 300, 2.0, 360, 520),
    "cam": (205, 665, 2.35, 360, 570),
}

STATES = None


def load():
    global STATES
    if STATES is None:
        STATES = pickle.load(open("build/states.pkl", "rb"))["states"]
    return STATES


def draw_frame(S):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    shot = S["shot"]
    if shot.startswith("vis:"):
        draw_vision(ctx, S, shot[4:])
    else:
        cx, cy, z, ax, ay = SHOTS[shot]
        if shot == "two_push":
            u = min(1, S["shot_t"] / max(1.0, S["shot_dur"]))
            z = 1.15 + 0.16 * (u * u * (3 - 2 * u))
        if S.get("card") and shot in ("m", "mm", "a", "aa", "cam"):
            ay += 80
        ctx.save()
        ctx.translate(ax, ay); ctx.scale(z, z); ctx.translate(-cx, -cy)
        draw_kitchen(ctx, S)
        ctx.restore()
    vignette(ctx)
    draw_title(ctx, S)
    draw_card(ctx, S)
    draw_end(ctx, S)
    draw_subtitle(ctx, S)
    return surf


def frame_bytes(i):
    st = load()
    surf = draw_frame(st[i])
    return bytes(surf.get_data())


def stills(times):
    st = load()
    os.makedirs("build/stills", exist_ok=True)
    for tt in times:
        i = min(len(st) - 1, int(float(tt) * 24))
        surf = draw_frame(st[i])
        p = f"build/stills/s_{float(tt):07.2f}.png"
        surf.write_to_png(p)
        print(p, st[i]["shot"])


def video(out="build/video_raw.mkv"):
    st = load()
    n = len(st)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", "24",
           "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "8", "-pix_fmt", "yuv420p", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for k, b in enumerate(pool.imap(frame_bytes, range(n), chunksize=8)):
            p.stdin.write(b)
            if k % 480 == 0:
                print(f"frame {k}/{n}", flush=True)
    p.stdin.close(); p.wait()
    print("done", out)


if __name__ == "__main__":
    if sys.argv[1] == "stills":
        stills(sys.argv[2:])
    else:
        video()
