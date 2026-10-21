#!/usr/bin/env python3
"""render.py -- render scenes to video, preview stills, contact sheets and character sheets.

Run from the repo root (/home/user/game1):

    python3 film/render.py --scene 3                    -> film/build/video/s3.mp4
    python3 film/render.py --scene 3 --jobs 4           same, frames split over 4 processes
    python3 film/render.py --scene 3 --preview          -> film/build/preview/s3_t002.50.png ...
    python3 film/render.py --scene 3 --preview --times 0,2.5,10
    python3 film/render.py --scene 3 --contact          -> film/build/preview/s3_contact.png
    python3 film/render.py --all [--jobs 4]             every scene, in parallel
    python3 film/render.py --sheet                      -> film/build/preview/character_sheet_*.png
    python3 film/render.py --scene 3 --frames 0:48      partial render (testing)
    python3 film/render.py --scene 3 --still 12.5 --out /tmp/x.png
    python3 film/render.py --list                       scenes found + durations

Scenes are found by globbing film/scenes/s{N}_*.py and imported as film.scenes.<module>.
Scene contract: SCENE = N; optional setup() -> state (called once per process);
draw(cr, t, state) paints one full 1920x1080 frame at LOCAL time t (seconds).
Video: exactly round(duration * 24) frames, raw BGRA piped to ffmpeg (libx264 crf 16, yuv420p).
Timing source: film/lib/timeline.py (FILM_TIMELINE env var overrides film/timeline.json).
"""

import argparse
import glob
import importlib
import math
import multiprocessing
import os
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import cairocffi as cairo  # noqa: E402

from film.lib import core  # noqa: E402

W, H, FPS = core.W, core.H, core.FPS
BUILD = ROOT / "film" / "build"
VIDEO_DIR = BUILD / "video"
PREVIEW_DIR = BUILD / "preview"


# ----------------------------------------------------------------------------------------
# scene discovery
# ----------------------------------------------------------------------------------------

def scene_files():
    """{scene number: path} for every film/scenes/s{N}_*.py."""
    out = {}
    for p in sorted(glob.glob(str(ROOT / "film" / "scenes" / "s[0-9]*_*.py"))):
        stem = Path(p).stem
        num = ""
        for ch in stem[1:]:
            if ch.isdigit():
                num += ch
            else:
                break
        if not num:
            continue
        n = int(num)
        if n in out:
            raise SystemExit(f"two scene files for scene {n}: {out[n]} and {p}")
        out[n] = Path(p)
    return out


def load_scene(n):
    files = scene_files()
    if n not in files:
        raise SystemExit(f"no scene file film/scenes/s{n}_*.py (found: {sorted(files)})")
    mod = importlib.import_module(f"film.scenes.{files[n].stem}")
    if getattr(mod, "SCENE", n) != n:
        print(f"[render] warning: {files[n].name} declares SCENE={mod.SCENE}", file=sys.stderr)
    if not hasattr(mod, "draw"):
        raise SystemExit(f"{files[n].name} has no draw(cr, t, state)")
    return mod


def scene_duration(n):
    from film.lib import timeline
    return timeline.scene(n).duration


def frame_count(n):
    return int(round(scene_duration(n) * FPS))


# per-process cache: scene number -> (module, state)
_LOADED = {}


def _scene_and_state(n):
    if n not in _LOADED:
        mod = load_scene(n)
        t0 = time.perf_counter()
        state = mod.setup() if hasattr(mod, "setup") else None
        _LOADED[n] = (mod, state, time.perf_counter() - t0)
    return _LOADED[n]


# ----------------------------------------------------------------------------------------
# frame rendering
# ----------------------------------------------------------------------------------------

class Frame:
    """One reusable 1920x1080 ARGB32 surface; render(t) returns it fully painted."""

    def __init__(self):
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)

    def render(self, mod, state, t):
        cr = core.new_context(self.surface)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.set_source_rgb(0, 0, 0)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)
        mod.draw(cr, t, state)
        del cr
        self.surface.flush()
        return self.surface


def _ffmpeg_cmd(out_path, threads=2):
    return ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p",
            "-threads", str(threads), "-movflags", "+faststart", str(out_path)]


def render_chunk(n, f0, f1, out_path, threads=2):
    """Render frames [f0, f1) of scene n into out_path. Returns timing stats."""
    mod, state, setup_s = _scene_and_state(n)
    fr = Frame()
    proc = subprocess.Popen(_ffmpeg_cmd(out_path, threads), stdin=subprocess.PIPE)
    t_draw = 0.0
    t_wall0 = time.perf_counter()
    try:
        for i in range(f0, f1):
            t = i / FPS
            a = time.perf_counter()
            surf = fr.render(mod, state, t)
            t_draw += time.perf_counter() - a
            proc.stdin.write(bytes(surf.get_data()))
    except BaseException:
        proc.stdin.close()
        proc.kill()
        raise
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError(f"ffmpeg failed for {out_path}")
    return {"scene": n, "frames": f1 - f0, "draw_s": t_draw, "wall_s": time.perf_counter() - t_wall0,
            "setup_s": setup_s, "out": str(out_path)}


def _chunk_job(args):
    n, f0, f1, out, threads = args
    try:
        return render_chunk(n, f0, f1, out, threads)
    except Exception:
        return {"scene": n, "error": traceback.format_exc(), "frames": 0}


def _concat(parts, out_path):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        for p in parts:
            f.write(f"file '{p}'\n")
        lst = f.name
    try:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                        "-c", "copy", "-movflags", "+faststart", str(out_path)], check=True)
    finally:
        os.unlink(lst)


def count_frames(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
                        "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    try:
        return int(r.stdout.strip())
    except ValueError:
        return -1


def render_scenes(scenes, jobs=1, frames=None, verify=True):
    """Render whole scenes (or a frame range of one) with `jobs` worker processes."""
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    parts_dir = VIDEO_DIR / "parts"
    parts_dir.mkdir(exist_ok=True)
    tasks, plan = [], {}
    for n in scenes:
        total = frame_count(n)
        f0, f1 = (0, total) if frames is None else (max(0, frames[0]), min(total, frames[1]))
        # split each scene into up to `jobs` chunks (each worker re-runs setup() once per scene)
        min_chunk = 48 if len(scenes) == 1 else 120
        nchunks = max(1, min(jobs, math.ceil((f1 - f0) / min_chunk)))
        size = math.ceil((f1 - f0) / nchunks)
        plan[n] = []
        for k in range(nchunks):
            a, b = f0 + k * size, min(f1, f0 + (k + 1) * size)
            if a >= b:
                continue
            out = parts_dir / f"s{n}_{k:03d}.mp4"
            plan[n].append(out)
            tasks.append((n, a, b, out, 2 if jobs > 1 else 4))
    # longest chunks first for load balance
    tasks.sort(key=lambda x: -(x[2] - x[1]))
    results = []
    t0 = time.perf_counter()
    if jobs <= 1:
        for tk in tasks:
            results.append(_chunk_job(tk))
    else:
        ctx = multiprocessing.get_context("fork")
        with ProcessPoolExecutor(max_workers=jobs, mp_context=ctx) as ex:
            futs = [ex.submit(_chunk_job, tk) for tk in tasks]
            for fu in as_completed(futs):
                results.append(fu.result())
    errors = [r for r in results if "error" in r]
    for r in errors:
        print(f"[render] scene {r['scene']} FAILED:\n{r['error']}", file=sys.stderr)
    ok_scenes = sorted({r["scene"] for r in results if "error" not in r} - {r["scene"] for r in errors})
    for n in ok_scenes:
        out = VIDEO_DIR / (f"s{n}.mp4" if frames is None else f"s{n}_f{frames[0]}-{frames[1]}.mp4")
        if len(plan[n]) == 1:
            shutil.move(str(plan[n][0]), out)
        else:
            _concat(plan[n], out)
            for p in plan[n]:
                os.unlink(p)
        rs = [r for r in results if r["scene"] == n]
        nf = sum(r["frames"] for r in rs)
        draw = sum(r["draw_s"] for r in rs)
        msg = (f"[render] s{n}: {nf} frames -> {out.relative_to(ROOT)}   avg draw {draw / max(1, nf) * 1000:.1f} ms/frame"
               f"   setup {max(r['setup_s'] for r in rs):.2f}s")
        if verify:
            got = count_frames(out)
            msg += f"   verified {got} frames" + ("" if got == nf else "  <-- MISMATCH!")
        print(msg)
    print(f"[render] done in {time.perf_counter() - t0:.1f}s wall")
    return not errors


# ----------------------------------------------------------------------------------------
# previews and contact sheets
# ----------------------------------------------------------------------------------------

def default_times(n):
    from film.lib import timeline
    dur = scene_duration(n)
    ts = set(round(k * 2.0, 4) for k in range(int(dur // 2) + 1))
    for ln in timeline.lines_in(n):
        ts.add(ln.start + 0.3)
    for b in timeline.beats_in(n):
        ts.add(b.t)
    last = (frame_count(n) - 1) / FPS
    return sorted({min(last, max(0.0, round(t * FPS) / FPS)) for t in ts})


def _labels_at(n, t):
    from film.lib import timeline
    out = []
    for b in timeline.beats_in(n):
        if abs(b.t - t) < 0.5 / FPS or (b.end is not None and b.t <= t <= b.end):
            out.append(b.id)
    for ln in timeline.lines_in(n):
        if ln.start <= t <= ln.end + 0.35:
            out.append(f'{ln.id} {ln.speaker}: "{ln.text}"')
    return out


def render_previews(n, times=None):
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    mod, state, _ = _scene_and_state(n)
    times = default_times(n) if times is None else [round(t * FPS) / FPS for t in times]
    fr = Frame()
    paths = []
    for t in times:
        a = time.perf_counter()
        surf = fr.render(mod, state, t)
        ms = (time.perf_counter() - a) * 1000
        p = PREVIEW_DIR / f"s{n}_t{t:06.2f}.png"
        surf.write_to_png(str(p))
        paths.append((t, p))
        print(f"[preview] s{n} t={t:6.2f}  {ms:6.1f} ms  -> {p.relative_to(ROOT)}")
    return paths


def render_contact(n, times=None, cols=4, tw=480):
    from PIL import Image, ImageDraw, ImageFont
    shots = render_previews(n, times)
    th = int(tw * H / W)
    pad, lab = 12, 44
    rows = math.ceil(len(shots) / cols)
    sheet = Image.new("RGB", (cols * (tw + pad) + pad, rows * (th + lab + pad) + pad + 50), (24, 26, 30))
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 15)
        small = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Medium.otf", 12)
        big = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 24)
    except OSError:
        font = small = big = ImageFont.load_default()
    d.text((pad, 12), f"Scene {n} -- contact sheet ({len(shots)} frames)", fill=(235, 235, 235), font=big)
    for i, (t, p) in enumerate(shots):
        r, c = divmod(i, cols)
        x = pad + c * (tw + pad)
        y = 50 + pad + r * (th + lab + pad)
        im = Image.open(p).convert("RGB").resize((tw, th), Image.LANCZOS)
        sheet.paste(im, (x, y))
        d.text((x, y + th + 4), f"t = {t:6.2f}s", fill=(255, 220, 140), font=font)
        lbl = "  |  ".join(_labels_at(n, t))
        if len(lbl) > 70:
            lbl = lbl[:69] + "..."
        d.text((x, y + th + 24), lbl, fill=(190, 196, 204), font=small)
    out = PREVIEW_DIR / f"s{n}_contact.png"
    sheet.save(out)
    print(f"[contact] -> {out.relative_to(ROOT)}")
    return out


def render_still(n, t, out):
    mod, state, _ = _scene_and_state(n)
    surf = Frame().render(mod, state, round(t * FPS) / FPS)
    surf.write_to_png(str(out))
    print(f"[still] s{n} t={t} -> {out}")


# ----------------------------------------------------------------------------------------
# character sheets
# ----------------------------------------------------------------------------------------

SHEET_W, SHEET_H = 1920, 1080


def _sheet_modules():
    """(name, module) for every characters/props/env module with a sheet hook."""
    mods = []
    from film.lib import characters
    for name, err in characters.IMPORT_ERRORS.items():
        print(f"[sheet] WARNING: characters.{name} failed to import:\n{err}", file=sys.stderr)
    mods += [(f"{n}", m) for n, m in characters.sheet_providers()]
    for extra in ("props", "env"):
        try:
            m = importlib.import_module(f"film.lib.{extra}")
        except ModuleNotFoundError:
            continue
        except Exception:
            print(f"[sheet] WARNING: film.lib.{extra} failed to import:\n{traceback.format_exc()}", file=sys.stderr)
            continue
        if hasattr(m, "sheet_items") or hasattr(m, "draw_sheet"):
            mods.append((extra, m))
    return mods


def _sheet_background(cr, title, k, n):
    core.vgrad(cr, 0, 0, SHEET_W, SHEET_H, ["#4d5661", "#3a414a"])
    core.text(cr, title + (f"  ({k}/{n})" if n > 1 else ""), 24, 40, 26, core.SANS_SEMI, "#f0f0f0")
    core.text(cr, "film/render.py --sheet", SHEET_W - 24, 40, 15, core.SANS, "#aab3bd", align="right")


def _pack(items, top=64, margin=18, label_h=26):
    """Shelf-pack SheetItems into pages -> [[(item, x, y), ...], ...]."""
    pages, cur = [], []
    x, y, shelf = margin, top, 0
    for it in items:
        w, h = it.w, it.h + label_h
        if x + w > SHEET_W - margin:
            x, y, shelf = margin, y + shelf + margin, 0
        if y + h > SHEET_H - margin:
            pages.append(cur)
            cur, x, y, shelf = [], margin, top, 0
        cur.append((it, x, y))
        x += w + margin
        shelf = max(shelf, h)
    if cur:
        pages.append(cur)
    return pages


def render_sheets(only=None):
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    outs = []
    for name, mod in _sheet_modules():
        if only and name not in only:
            continue
        t0 = time.perf_counter()
        for old in PREVIEW_DIR.glob(f"character_sheet_{name}_*.png"):      # stale pages
            old.unlink()
        if hasattr(mod, "draw_sheet"):
            surf, cr = core.frame(SHEET_W, SHEET_H)
            _sheet_background(cr, f"{name}", 1, 1)
            mod.draw_sheet(cr, SHEET_W, SHEET_H)
            p = PREVIEW_DIR / f"character_sheet_{name}.png"
            surf.write_to_png(str(p))
            outs.append(p)
        if hasattr(mod, "sheet_items"):
            items = list(mod.sheet_items())
            groups = {}
            for it in items:
                groups.setdefault(getattr(it, "group", "") or "", []).append(it)
            pages = []
            for g, its in groups.items():
                for pg in _pack(its):
                    pages.append((g, pg))
            for k, (g, page) in enumerate(pages, 1):
                surf, cr = core.frame(SHEET_W, SHEET_H)
                _sheet_background(cr, f"{name}" + (f" -- {g}" if g else ""), k, len(pages))
                for it, x, y in page:
                    cr.save()
                    cr.rectangle(x, y, it.w, it.h)
                    cr.clip()
                    cr.translate(x, y)
                    try:
                        it.draw(cr)
                    except Exception:
                        print(f"[sheet] {name}: item '{it.label}' failed:\n{traceback.format_exc()}", file=sys.stderr)
                    cr.restore()
                    core.text(cr, it.label, x + it.w / 2, y + it.h + 18, 14, core.SANS, "#e8e8e8", align="center")
                p = PREVIEW_DIR / f"character_sheet_{name}_{k}.png"
                surf.write_to_png(str(p))
                outs.append(p)
        print(f"[sheet] {name}: {time.perf_counter() - t0:.1f}s")
    if not only or "lineup" in only:
        outs.append(render_lineup())
    for p in outs:
        print(f"[sheet] -> {p.relative_to(ROOT)}")
    return outs


def _measure_top(item, scale=1.0):
    """Draw one line-up creature alone; return its top (px above the ground, all included)."""
    import numpy as np
    w, h = 900, 1000
    surf, cr = core.frame(w, h)
    item.draw(cr, w / 2, h - 40, scale)
    surf.flush()
    a = np.frombuffer(surf.get_data(), np.uint8).reshape(h, surf.get_stride() // 4, 4)[:, :w, 3]
    rows = np.nonzero(a.max(axis=1) > 128)[0]
    return (h - 40 - rows[0]) / scale if len(rows) else 0.0


def render_lineup():
    """character_sheet_lineup.png: every creature with a lineup() hook, side by side at one
    scale, against 100 px guides, the bench seat (125) and the planned CAST_HEIGHTS marks."""
    from film.lib import characters as ch
    items = ch.lineup_items()
    heights = ch.base.CAST_HEIGHTS
    surf, cr = core.frame(SHEET_W, SHEET_H)
    _sheet_background(cr, "cast line-up (scale 1.0 heights; one scale for everyone)", 1, 1)
    ground = SHEET_H - 90
    top_room = ground - 120
    tallest = max([heights.get(it.name, 520) for it in items] + [max(heights.values())]) + 80
    total_w = sum(it.width for it in items) + 60 * max(0, len(items) - 1)
    sc = min(1.0, top_room / tallest, (SHEET_W - 420) / max(total_w, 1.0))
    # guides
    for k in range(0, int(tallest) + 1, 100):
        y = ground - k * sc
        cr.rectangle(60, y - 0.5, SHEET_W - 120, 1.0)
        cr.set_source_rgba(1, 1, 1, 0.12 if k else 0.35)
        cr.fill()
        core.text(cr, f"{k}", 52, y + 5, 13, core.SANS, "#aab3bd", align="right")
    yb = ground - ch.base.BENCH_SEAT_H * sc
    cr.rectangle(60, yb - 1, SHEET_W - 120, 2)
    cr.set_source_rgba(0.8, 0.55, 0.3, 0.45)
    cr.fill()
    core.text(cr, "bench seat 125", SHEET_W - 64, yb - 6, 13, core.SANS, "#e0b48a", align="right")
    # planned heights (right column)
    present = {it.name for it in items}
    for i, (name, hgt) in enumerate(sorted(heights.items(), key=lambda kv: -kv[1])):
        y = ground - hgt * sc
        x0 = SHEET_W - 330 + (i % 2) * 130
        cr.rectangle(x0, y - 1, 40, 2)
        cr.set_source_rgba(0.55, 0.9, 1.0, 0.9 if name in present else 0.45)
        cr.fill()
        core.text(cr, f"{name} {hgt}", x0 + 46, y + 5, 13, core.SANS, "#cfeefa" if name in present else "#8fa4b0")
    # the creatures
    x = 120.0
    for it in items:
        cx = x + it.width * sc / 2
        try:
            it.draw(cr, cx, ground, sc)
            top = _measure_top(it)
            plan = heights.get(it.name)
            lab = f"{it.name}: top {top:.0f}" + (f" / crown plan {plan}" if plan else "")
        except Exception:
            print(f"[sheet] lineup '{it.name}' failed:\n{traceback.format_exc()}", file=sys.stderr)
            lab = f"{it.name}: FAILED"
        core.text(cr, lab, cx, ground + 34, 14, core.SANS, "#e8e8e8", align="center")
        x += (it.width + 60) * sc
    p = PREVIEW_DIR / "character_sheet_lineup.png"
    surf.write_to_png(str(p))
    return p


# ----------------------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description="Render 'The Stone and the Bread' scenes.")
    ap.add_argument("--scene", type=int, action="append", help="scene number (repeatable)")
    ap.add_argument("--all", action="store_true", help="render every scene found")
    ap.add_argument("--jobs", type=int, default=1, help="parallel worker processes")
    ap.add_argument("--preview", action="store_true", help="render PNG keyframes instead of video")
    ap.add_argument("--times", help="comma-separated local times for --preview/--contact")
    ap.add_argument("--contact", action="store_true", help="render a contact sheet of keyframes")
    ap.add_argument("--sheet", action="store_true", help="render the character sheets")
    ap.add_argument("--only", help="--sheet: comma-separated module names")
    ap.add_argument("--frames", help="render only frames a:b (video)")
    ap.add_argument("--still", type=float, help="render one frame at this local time")
    ap.add_argument("--out", help="output path for --still")
    ap.add_argument("--list", action="store_true", help="list scenes")
    ap.add_argument("--no-verify", action="store_true", help="skip the ffprobe frame-count check")
    a = ap.parse_args(argv)

    if a.sheet:
        render_sheets(a.only.split(",") if a.only else None)
        return 0
    if a.list:
        for n, p in sorted(scene_files().items()):
            try:
                print(f"s{n}: {p.relative_to(ROOT)}  {scene_duration(n):.2f}s  {frame_count(n)} frames")
            except Exception as e:
                print(f"s{n}: {p.relative_to(ROOT)}  (timeline: {e})")
        return 0
    scenes = sorted(scene_files()) if a.all else (a.scene or [])
    if not scenes:
        ap.print_help()
        return 1
    times = [float(x) for x in a.times.split(",")] if a.times else None
    if a.still is not None:
        render_still(scenes[0], a.still, a.out or str(PREVIEW_DIR / f"s{scenes[0]}_still.png"))
        return 0
    if a.preview or a.contact:
        for n in scenes:
            if a.contact:
                render_contact(n, times)
            else:
                render_previews(n, times)
        return 0
    frames = None
    if a.frames:
        f0, f1 = a.frames.split(":")
        frames = (int(f0), int(f1))
    ok = render_scenes(scenes, jobs=max(1, a.jobs), frames=frames, verify=not a.no_verify)
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
