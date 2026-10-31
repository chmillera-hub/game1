"""Render frames. Usage:
  render.py preview t1 t2 ...     -> contact sheet PNG of those times
  render.py video                 -> lossless-ish segments + concat into BUILD/video.mp4
"""
import math, os, subprocess, sys
from multiprocessing import Pool
import cairo
from common import W, H, FPS, DUR, BUILD, TL, LINES, SCENES, clamp, hexc, rgba

SUB_COL = {"N": hexc("ffffff"), "Z": hexc("ffd98a"), "HA": hexc("9fdcff"), "HB": hexc("b8f0a8")}
FONT = "Inter"


def wrap(ctx, text, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if ctx.text_extents(test).x_advance > maxw and cur:
            lines.append(cur)
            cur = w
        else:
            cur = test
    if cur:
        lines.append(cur)
    return lines


def draw_subs(ctx, t):
    for lid in TL["order"]:
        d = LINES[lid]
        if d.get("thought") or not (d["t0"] - 0.1 <= t <= d["t1"] + 0.5):
            continue
        for i, sb in enumerate(d["subs"]):
            last = i == len(d["subs"]) - 1
            if sb["t0"] - 0.05 <= t < (sb["t1"] + (0.5 if last else 0.0)):
                spk = d["spk"]
                ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL,
                                     cairo.FONT_WEIGHT_BOLD if spk != "N" else cairo.FONT_WEIGHT_NORMAL)
                ctx.set_font_size(37 if spk != "N" else 35)
                lines = wrap(ctx, sb["text"], 610)
                lh = 47
                y0 = 925 - (len(lines) - 1) * lh / 2
                for k, ln in enumerate(lines):
                    ext = ctx.text_extents(ln)
                    x = (W - ext.x_advance) / 2
                    y = y0 + k * lh
                    ctx.new_path()
                    ctx.move_to(x, y)
                    ctx.text_path(ln)
                    rgba(ctx, (0.04, 0.03, 0.06), 0.85)
                    ctx.set_line_width(7)
                    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
                    ctx.stroke_preserve()
                    rgba(ctx, SUB_COL[spk])
                    ctx.fill()
                return


def draw_title(ctx, t):
    a = 0.0
    if t < 3.6:
        a = 1.0 - clamp((t - 3.0) / 0.6)
    end0 = LINES["e2"]["t1"] + 0.3
    if t > end0:
        a = clamp((t - end0) / 1.2)
    if a <= 0:
        return
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(46)
    txt = "THE FIRST WITNESS"
    # letter-spaced
    sp = 7
    widths = [ctx.text_extents(c).x_advance for c in txt]
    total = sum(widths) + sp * (len(txt) - 1)
    x = (W - total) / 2
    y = 190
    for c, wd in zip(txt, widths):
        ctx.new_path(); ctx.move_to(x, y); ctx.text_path(c)
        rgba(ctx, (0.05, 0.03, 0.08), 0.7 * a); ctx.set_line_width(6); ctx.stroke_preserve()
        rgba(ctx, hexc("ffe6b0"), a); ctx.fill()
        x += wd + sp


def make_frame(t):
    import shots
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
    ctx = cairo.Context(surf)
    ctx.set_source_rgb(0, 0, 0)
    ctx.paint()
    ctx.save()
    name = shots.render_frame(ctx, t)
    ctx.restore()
    draw_title(ctx, t)
    draw_subs(ctx, t)
    return surf, name


def render_segment(args):
    idx, f0, f1 = args
    out = f"{BUILD}/{os.environ.get('SEG_PREFIX', 'seg')}_{idx:02d}.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "10", "-pix_fmt", "yuv420p", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(f0, f1):
        surf, _ = make_frame(f / FPS)
        surf.flush()
        p.stdin.write(bytes(surf.get_data()))
        if (f - f0) % 240 == 0:
            print(f"seg {idx}: {f - f0}/{f1 - f0}", flush=True)
    p.stdin.close()
    p.wait()
    return out


def main():
    mode = sys.argv[1]
    if mode == "preview":
        ts = [float(x) for x in sys.argv[2:]]
        cols = min(4, len(ts))
        rows = math.ceil(len(ts) / cols)
        sc = 0.5
        sheet = cairo.ImageSurface(cairo.FORMAT_RGB24, int(W * sc * cols), int(H * sc * rows))
        c = cairo.Context(sheet)
        for i, t in enumerate(ts):
            surf, name = make_frame(t)
            c.save()
            c.translate((i % cols) * W * sc, (i // cols) * H * sc)
            c.scale(sc, sc)
            c.set_source_surface(surf)
            c.paint()
            c.restore()
            c.set_source_rgb(1, 1, 0)
            c.select_font_face(FONT)
            c.set_font_size(16)
            c.move_to((i % cols) * W * sc + 6, (i // cols) * H * sc + 18)
            c.show_text(f"{t:.1f} {name}")
        out = f"{BUILD}/preview.png"
        sheet.write_to_png(out)
        print(out)
        return
    n = int(DUR * FPS) + 1
    start = int(float(sys.argv[2]) * FPS) if len(sys.argv) > 2 else 0
    end = int(float(sys.argv[3]) * FPS) if len(sys.argv) > 3 else n
    workers = int(os.environ.get("WORKERS", "4"))
    nseg = workers * 3
    bounds = [start + (end - start) * k // nseg for k in range(nseg + 1)]
    jobs = [(k, bounds[k], bounds[k + 1]) for k in range(nseg)]
    with Pool(workers) as pool:
        outs = pool.map(render_segment, jobs, chunksize=1)
    prefix = os.environ.get("SEG_PREFIX", "seg")
    with open(f"{BUILD}/{prefix}s.txt", "w") as f:
        for o in outs:
            f.write(f"file '{o}'\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{BUILD}/{prefix}s.txt",
                    "-c", "copy", f"{BUILD}/video.mp4" if prefix == "seg" else f"{BUILD}/{prefix}.mp4"], check=True)
    print("video ok")


if __name__ == "__main__":
    main()
