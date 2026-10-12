"""Frame renderer: composes plate + characters + effects + grade + subtitles.

Usage:
  python3 render.py frame <t_seconds> out.png      # single frame preview
  python3 render.py sheet out.png [n]               # contact sheet across the film
  python3 render.py all                             # full parallel render to segments
"""
import math
import os
import subprocess
import sys
import time

import numpy as np
import skia

import bg
import body
import chars
import extras
import fx
import subs
from config import FPS, H, W, WORK
from direction import SHOTS, T, build_perfs
from gfx import ease_io, fill
from rig import DEFAULT_P, flip_params

VOICE = os.path.join(WORK, "voice")
N_FRAMES = int(math.ceil(T.total * FPS))
BREAD_SPLIT = 1.0  # palm distance (body units) at which the loaf comes apart


class Renderer:
    def __init__(self):
        t0 = time.time()
        self.perfs = build_perfs()
        self.tracks = {}
        self.arms = {}
        for name, pf in self.perfs.items():
            self.tracks[name], self.arms[name] = pf.evaluate(N_FRAMES, T, VOICE)
        self.chars = dict(chars.CHARS)
        self.chars["man2"] = extras.make_extra(77, female=False)
        self.cues = subs.build_cues(T)
        self.shot_t = [s["t0"] for s in SHOTS]
        print(f"renderer ready in {time.time() - t0:.1f}s", file=sys.stderr)

    def shot_index(self, t):
        i = 0
        for k, t0 in enumerate(self.shot_t):
            if t0 <= t + 1e-6:
                i = k
        return i

    def params(self, who, f, shot, extra=None):
        tr = self.tracks[who]
        f = min(f, N_FRAMES - 1)
        P = {k: float(v[f]) for k, v in tr.items() if k in DEFAULT_P}
        speak = float(tr["speak"][f])
        for k in ("arm_l", "arm_r"):
            a = self.arms[who][k][f]
            # a held gesture keeps moving a little with the rhythm of speech
            if a is not None and not a.get("still") and speak > 0.01:
                a = dict(a, beat=0.75 * speak)
            P[k] = a
        P.update(shot["light"])
        if extra:
            P.update(extra)
        return P

    def draw_shot(self, cv, i, f):
        shot = SHOTS[i]
        t = f / FPS
        t0 = shot["t0"]
        t1 = SHOTS[i + 1]["t0"] if i + 1 < len(SHOTS) else T.total
        u = ease_io((t - t0) / max(t1 - t0, 1e-3))
        cam = shot["cam"]
        z = cam.get("z0", 1.0) + (cam.get("z1", 1.0) - cam.get("z0", 1.0)) * u
        fxp, fyp = cam.get("fx", W / 2), cam.get("fy", H / 2)
        cv.save()
        cv.translate(fxp, fyp)
        cv.scale(z, z)
        cv.translate(-fxp, -fyp)
        info = bg.draw_plate(cv, shot["plate"], shot["pcam"], W, H, shot["blur"])
        effects = shot["fx"]
        pcam = shot["pcam"]
        # --- background effects
        if "sun_glow" in effects:
            fx.sun_glow(cv, W, H, t, info, pcam, 0.8)
        if "sun_glow_strong" in effects:
            fx.sun_glow(cv, W, H, t, info, pcam, 1.25)
        if "sun_glow_dusk" in effects:
            fx.sun_glow(cv, W, H, t, info, pcam, 1.0, col="#ffc48a")
        if "water_sparkle" in effects:
            fx.water_sparkle(cv, W, H, t, info, pcam, "#ffffff" if shot["grade"] != "dusk" else "#ffd8a8")
        if "boats_moving" in effects:
            fx.boats_moving(cv, W, H, t, t0, info, pcam)
        if "bokeh_water" in effects:
            fx.bokeh(cv, W, H, t, 7, ["#fff6e0", "#ffffff", "#ffe2b0"], n=16, region=(0.0, 0.5, 1.0, 1.0), alpha=0.22)
        if "bokeh_land" in effects:
            fx.bokeh(cv, W, H, t, 8, ["#fff1d0", "#e8f0ff"], n=8, region=(0.0, 0.1, 1.0, 0.5), rmin=14, rmax=34, alpha=0.12)
        if "bokeh_dusk" in effects:
            fx.bokeh(cv, W, H, t, 9, ["#ffb070", "#ffd49a", "#ff8a6a"], n=16, region=(0.0, 0.3, 1.0, 1.0), alpha=0.22)
        if "dusk_figures" in effects:
            fx.dusk_figures(cv, W, H, t, pcam)
        if "leaving" in effects:
            fx.leaving(cv, W, H, t, t0, pcam)
        # --- crowd groups and characters, far to near
        layers = [(c["S"], 1, k) for k, c in enumerate(shot["chars"])]
        layers += [(g["z"], 0, k) for k, g in enumerate(shot["crowd"])]
        for depth, kind, k in sorted(layers):
            if kind == 0:
                g = shot["crowd"][k]
                light = dict(shot["light"])
                light.update(g["light"])
                extras.draw_crowd(cv, t, g["members"], g["mood"], g["focus"], g["t0"], light=light, blur=g["blur"])
                continue
            c = shot["chars"][k]
            who = c["who"]
            P = self.params(who, f, shot, c.get("P"))
            ch = self.chars[who]
            if c.get("blur", 0) > 0:
                p = skia.Paint()
                p.setImageFilter(skia.ImageFilters.Blur(c["blur"], c["blur"], skia.TileMode.kDecal))
                cv.saveLayer(None, p)
                ch.draw(cv, P, c["x"], c["y"], c["S"], flip=c.get("flip", False))
                if c.get("bread"):
                    self.draw_bread(cv, c, P)
                cv.restore()
            else:
                ch.draw(cv, P, c["x"], c["y"], c["S"], flip=c.get("flip", False))
                if c.get("bread"):
                    self.draw_bread(cv, c, P)
        # --- foreground light
        if "god_rays" in effects:
            fx.god_rays(cv, W, H, t, info, pcam, 0.9)
        if "beams" in effects:
            fx.beams(cv, W, H, t, 1.0)
        if "beams_strong" in effects:
            fx.beams(cv, W, H, t, 1.6)
        if "dust" in effects:
            fx.dust(cv, W, H, t)
        cv.restore()
        fx.grade(cv, W, H, shot["grade"])
        return shot

    def palm(self, c, P, side):
        """Screen position of the palm centre of one hand (side -1 = left arm, +1 = right arm)."""
        st = self.chars[c["who"]].st
        Q = dict(DEFAULT_P)
        Q.update(P)
        flip = c.get("flip", False)
        if flip:
            Q = flip_params(Q)
            side = -side
        spec = Q["arm_l" if side < 0 else "arm_r"]
        _, E, Wr = body.arm_geometry(st, Q, side, spec)
        hd = body.hand_direction(E, Wr, spec, side)
        k = st.get("body_scale", 1.0)
        length = st.get("hand_len", 2.15) * k * (spec or {}).get("hand_scale", 1.0)
        fore = math.hypot(hd[0], hd[1])
        reach = length * (0.62 + 0.38 * min(fore, 1.0))
        d = (hd[0] / (fore + 1e-9), hd[1] / (fore + 1e-9))
        px = Wr[0] - hd[0] * 0.25 + d[0] * reach * 0.42
        py = Wr[1] - hd[1] * 0.25 + d[1] * reach * 0.42
        lean = math.radians(Q["blean"])
        bx = px * math.cos(lean) - py * math.sin(lean) + Q["bx"]
        by = px * math.sin(lean) + py * math.cos(lean)
        return c["x"] + (-bx if flip else bx) * c["S"], c["y"] + by * c["S"]

    def draw_bread(self, cv, c, P):
        """c["bread"] = "both" (a loaf held in both hands that breaks as they part)
        or a list of (hand, half) with hand "l"/"r" and half -1 (left half) / +1 (right half)."""
        S = c["S"]
        s = 0.72 * S
        spec = c["bread"]
        if spec == "both":
            lx, ly = self.palm(c, P, -1)
            rx, ry = self.palm(c, P, 1)
            spread = math.hypot(rx - lx, ry - ly) / S
            if spread < BREAD_SPLIT:
                fx.bread(cv, (rx + lx) / 2, (ry + ly) / 2 - 0.1 * S, s)
                return
            spec = [("l", -1), ("r", 1)]
        for hand, half in spec:
            x, y = self.palm(c, P, -1 if hand == "l" else 1)
            cv.save()
            cv.translate(x - half * 0.5 * s, y - 0.1 * S)
            fx.bread(cv, 0, 0, s, broken=1.0, side_only=half)
            cv.restore()

    def render(self, f):
        t = f / FPS
        surf = skia.Surface(W, H)
        cv = surf.getCanvas()
        cv.clear(skia.ColorBLACK)
        i = self.shot_index(t)
        shot = SHOTS[i]
        tr = shot.get("trans")
        if tr and tr[0] == "dissolve" and i > 0 and t < shot["t0"] + tr[1]:
            self.draw_shot(cv, i - 1, f)
            a = ease_io((t - shot["t0"]) / tr[1])
            cv.saveLayerAlpha(None, int(255 * a))
            self.draw_shot(cv, i, f)
            cv.restore()
        else:
            self.draw_shot(cv, i, f)
        # titles
        if shot.get("title") and i == 0:
            a = 1.0 if t < 3.6 else max(0.0, 1 - (t - 3.6) / 1.2)
            subs.title(cv, W, H, shot["title"], "John 6", a)
        if shot.get("title") and i == len(SHOTS) - 1:
            a = ease_io(min(1.0, max(0.0, (t - shot["t0"] - 0.8) / 2.2)))
            subs.title(cv, W, H, "The Bread of Life", "John 6:24-69", a, y=210)
        subs.draw_subs(cv, W, H, self.cues, t)
        # fade to black at the very end
        if t > T.total - 1.0:
            a = min(1.0, (t - (T.total - 1.0)) / 1.0)
            cv.drawRect(skia.Rect.MakeWH(W, H), fill("#000000", alpha=a))
        return surf.makeImageSnapshot()


def frame_rgb(img):
    return img.toarray(colorType=skia.kRGBA_8888_ColorType)[:, :, :3]


_R = None


def _worker(args):
    seg, f0, f1, path = args
    global _R
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "ultrafast", "-qp", "0",
           "-pix_fmt", "yuv444p", path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    for f in range(f0, f1):
        img = _R.render(f)
        p.stdin.write(np.ascontiguousarray(frame_rgb(img)).tobytes())
    p.stdin.close()
    p.wait()
    return seg, time.time() - t0


def render_all(workers=4, seg_len=240, only=None):
    import multiprocessing as mp
    global _R
    _R = Renderer()
    out = os.path.join(WORK, "segments")
    os.makedirs(out, exist_ok=True)
    jobs = []
    for k, f0 in enumerate(range(0, N_FRAMES, seg_len)):
        f1 = min(N_FRAMES, f0 + seg_len)
        path = os.path.join(out, f"seg{k:03d}.mkv")
        if only is not None and k not in only:
            continue
        jobs.append((k, f0, f1, path))
    ctx = mp.get_context("fork")
    with ctx.Pool(workers) as pool:
        for seg, dt in pool.imap_unordered(_worker, jobs):
            print(f"segment {seg} done in {dt:.1f}s", flush=True)
    with open(os.path.join(out, "list.txt"), "w") as fl:
        for k in range(0, (N_FRAMES + seg_len - 1) // seg_len):
            fl.write(f"file 'seg{k:03d}.mkv'\n")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "frame":
        R = Renderer()
        t = float(sys.argv[2])
        R.render(int(round(t * FPS))).save(sys.argv[3], skia.kPNG)
    elif cmd == "frames":
        R = Renderer()
        out = sys.argv[2]
        ts = [float(x) for x in sys.argv[3:]]
        cols = min(4, len(ts))
        rows = (len(ts) + cols - 1) // cols
        sc = 0.5
        surf = skia.Surface(int(W * sc * cols), int(H * sc * rows))
        cv = surf.getCanvas()
        for k, t in enumerate(ts):
            img = R.render(int(round(t * FPS)))
            r, c = divmod(k, cols)
            cv.save()
            cv.translate(c * W * sc, r * H * sc)
            cv.scale(sc, sc)
            cv.drawImage(img, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear))
            cv.restore()
        surf.makeImageSnapshot().save(out, skia.kPNG)
    elif cmd == "sheet":
        R = Renderer()
        out = sys.argv[2]
        idx = [int(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 else list(range(len(SHOTS)))
        cols = 6
        rows = (len(idx) + cols - 1) // cols
        sc = 0.3
        surf = skia.Surface(int(W * sc * cols), int(H * sc * rows))
        cv = surf.getCanvas()
        for k, i in enumerate(idx):
            s = SHOTS[i]
            t1 = SHOTS[i + 1]["t0"] if i + 1 < len(SHOTS) else T.total
            t = (s["t0"] + t1) / 2
            img = R.render(int(t * FPS))
            r, c = divmod(k, cols)
            cv.save()
            cv.translate(c * W * sc, r * H * sc)
            cv.scale(sc, sc)
            cv.drawImage(img, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear))
            cv.restore()
        surf.makeImageSnapshot().save(out, skia.kPNG)
    elif cmd == "all":
        only = None
        if len(sys.argv) > 2:
            only = set(int(x) for x in sys.argv[2].split(","))
        render_all(only=only)
