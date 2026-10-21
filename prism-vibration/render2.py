"""Part 2 video: patterns (circle, square, star...) at different vibration speeds.

usage: python3 render2.py AUDIO_DIR OUT_DIR [scene ...] [--still t1,t2]
Frames are composed with PIL; the light on each panel comes from prism3d.
"""
import json, os, subprocess, sys, textwrap
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter
import matplotlib
from prism_sim import n_glass, cmf, planck, XYZ2RGB, WHITE_BALANCE
from prism3d import Bench3D, DEG, min_dev_incidence

W, H, FPS = 1920, 1080, 30
SLOW = 10.0                          # eye scenes play 10x slower than real time
BG = (10, 13, 20)
FG = (232, 236, 243)
MUTED = (138, 147, 166)
ACCENT = (255, 204, 102)
FONT_DIR = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf")


def font(size, bold=False, mono=False):
    name = "DejaVuSansMono.ttf" if mono else ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size)


# ------------------------------------------------------------------ light sources
def white_source(bench, n_pts=420):
    """Wavelength samples spaced evenly in still screen position, so wide
    stretches of the spectrum (violet) get as many samples as narrow ones."""
    lam = np.linspace(395, 700, 4000)
    u, _ = bench.wall(n_glass(lam))
    u = np.asarray(u)
    order = np.argsort(u)
    targets = np.linspace(u.min(), u.max(), n_pts)
    lam_s = np.interp(targets, u[order], lam[order])
    lam_s = np.sort(lam_s)
    edges = np.concatenate([[lam_s[0]], (lam_s[1:] + lam_s[:-1]) / 2, [lam_s[-1]]])
    dl = np.diff(edges)
    xyz = cmf(lam_s) * (planck(lam_s) * dl)[:, None]
    return lam_s, xyz / xyz[:, 1].sum()


HG = np.array([404.7, 435.8, 546.1, 577.0, 579.1])
HG_W = np.array([0.6, 1.0, 1.0, 0.45, 0.5])


def mercury_source():
    xyz = cmf(HG) * HG_W[:, None]
    return HG, xyz / xyz[:, 1].sum()


# ------------------------------------------------------------------ motion patterns
SHAPES = {
    "square": np.array([[1, 1], [-1, 1], [-1, -1], [1, -1]], float),
    "triangle": np.array([[0, 1], [-1, -1], [1, -1]], float),
    "star": np.array([[np.cos(np.pi / 2 + k * 2 * np.pi / 5), (np.sin(np.pi / 2 + k * 2 * np.pi / 5) + 0.095) / 1.095]
                      for k in [0, 2, 4, 1, 3]]),
}


def pattern(kind, s, mode="steady"):
    """Position (h, v) in [-1, 1] at fraction s of a lap. mode: steady, smooth (eases into
    corners) or snap (jumps between corners)."""
    s = np.mod(s, 1.0)
    if kind in ("circle", "figure8"):
        if mode == "snap":
            s = np.floor(s * 8) / 8
        a = 2 * np.pi * s
        return (np.cos(a), np.sin(a)) if kind == "circle" else (np.sin(a), np.sin(2 * a))
    P = SHAPES[kind]
    n = len(P)
    x = s * n
    k = np.floor(x).astype(int) % n
    f = x - np.floor(x)
    if mode == "snap":
        f = np.zeros_like(f)
    elif mode == "smooth":
        f = (1 - np.cos(np.pi * f)) / 2
    A, B = P[k], P[(k + 1) % n]
    p = A + (B - A) * f[..., None]
    return p[..., 0], p[..., 1]


# ------------------------------------------------------------------ eye and camera
TAU_EYE = 0.008                       # s, three-stage low-pass ~ visual persistence
_S = np.arange(0, 0.15, 0.00005)
EYE_W = _S ** 2 / (2 * TAU_EYE ** 3) * np.exp(-_S / TAU_EYE)
EYE_W /= EYE_W.sum()


class Panel:
    """One wall view: a light source moved along a pattern at a given rate."""
    K = 720                           # phase samples per lap

    def __init__(self, px_w, px_h, window, freq, positions, spec, sigma_mm=1.3):
        self.w, self.h, self.freq = px_w, px_h, freq
        u0, u1, v0, v1 = window
        self.s = max((u1 - u0) / px_w, (v1 - v0) / px_h)
        cu, cv = (u0 + u1) / 2, (v0 + v1) / 2
        self.u0, self.vtop = cu - self.s * px_w / 2, cv + self.s * px_h / 2
        U, V = positions(np.arange(self.K) / self.K)          # (K, n_lambda)
        self.px = (U - self.u0) / self.s
        self.py = (self.vtop - V) / self.s
        self.spec = spec
        self.sigma = sigma_mm / self.s
        self.grid = self._grid()

    def _grid(self):
        g = np.zeros((self.h, self.w, 3), np.float32)
        uA, vB = self.u0, self.vtop - self.s * self.h
        for step, val in [(10, 0.05), (50, 0.12)]:
            for u in np.arange(np.ceil(uA / step) * step, uA + self.s * self.w, step):
                x = int(round((u - uA) / self.s))
                if 0 <= x < self.w:
                    g[:, x] = val
            for v in np.arange(np.ceil(vB / step) * step, self.vtop, step):
                y = int(round((self.vtop - v) / self.s))
                if 0 <= y < self.h:
                    g[y, :] = val
        return g

    def xyz(self, phase_w):
        """Image for a weight per phase sample (sums to 1)."""
        keep = phase_w > phase_w.max() * 1e-4
        px, py, w = self.px[keep], self.py[keep], phase_w[keep]
        ok = np.isfinite(px) & np.isfinite(py)
        X = np.broadcast_to(px, px.shape)[ok]
        Y = np.broadcast_to(py, py.shape)[ok]
        Wt = np.broadcast_to(w[:, None], px.shape)[ok]
        L = np.broadcast_to(np.arange(px.shape[1]), px.shape)[ok]
        i0, j0 = np.floor(X).astype(int), np.floor(Y).astype(int)
        fx, fy = X - i0, Y - j0
        img = np.zeros((3, self.h * self.w))
        for di, dj, ww in [(0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)), (0, 1, (1 - fx) * fy), (1, 1, fx * fy)]:
            ii, jj = i0 + di, j0 + dj
            inb = (ii >= 0) & (ii < self.w) & (jj >= 0) & (jj < self.h)
            idx = jj[inb] * self.w + ii[inb]
            base = (Wt * ww)[inb]
            for c in range(3):
                img[c] += np.bincount(idx, base * self.spec[L[inb], c], minlength=self.h * self.w)
        img = img.reshape(3, self.h, self.w)
        img = np.stack([gaussian_filter(img[c], self.sigma) for c in range(3)], -1)
        return img

    # weights over the phase samples
    def w_average(self):
        return np.full(self.K, 1.0 / self.K)

    def w_eye(self, t):
        ph = np.mod(self.freq * (t - _S), 1.0)
        return np.bincount((ph * self.K).astype(int) % self.K, EYE_W, minlength=self.K)

    def w_camera(self, t, exposure=1 / 60):
        ts = t + np.linspace(0, exposure, 400, endpoint=False)
        ph = np.mod(self.freq * ts, 1.0)
        return np.bincount((ph * self.K).astype(int) % self.K, minlength=self.K) / len(ts)

    def rgb(self, xyz, ex):
        lin = xyz @ XYZ2RGB.T / WHITE_BALANCE * ex
        lin = lin - np.minimum(lin.min(-1, keepdims=True), 0)
        mx = lin.max(-1, keepdims=True)
        soft = 0.75 + 0.25 * np.tanh((mx - 0.75) / 0.25)
        lin = np.where(mx > 0.75, lin * soft / np.maximum(mx, 1e-12), lin)
        lin = np.clip(lin + self.grid, 0, 1)
        out = np.where(lin <= 0.0031308, 12.92 * lin, 1.055 * lin ** (1 / 2.4) - 0.055)
        return (out * 255).astype(np.uint8)


def exposure_for(panel):
    xyz = panel.xyz(panel.w_average())
    lin = (xyz @ XYZ2RGB.T / WHITE_BALANCE).max(-1)
    v = np.percentile(lin[lin > 0], 99.7)
    return 1.0 / v


# ------------------------------------------------------------------ experiment setups
def prism_motion(bench, n, kind, mode, rock_deg, nod_deg, target="prism"):
    def positions(s):
        h, v = pattern(kind, s, mode)
        h, v = np.asarray(h)[:, None], np.asarray(v)[:, None]
        u, vv = bench.wall(n[None, :], target, turnH=rock_deg * DEG * h[..., 0], turnV=nod_deg * DEG * v[..., 0])
        return u, vv
    return positions


def setup(light, theta, kind, mode, rock, nod, target="prism"):
    bench = Bench3D(theta)
    lam, spec = mercury_source() if light == "mercury" else white_source(bench)
    return bench, n_glass(lam), spec, prism_motion(bench, n_glass(lam), kind, mode, rock, nod, target)


def dot_positions(radius):
    def positions(s):
        h, v = pattern("circle", s)
        return (radius * np.asarray(h))[:, None], (radius * np.asarray(v))[:, None]
    return positions


# ------------------------------------------------------------------ frame composition
class Frame:
    def __init__(self):
        self.im = Image.new("RGB", (W, H), BG)
        self.d = ImageDraw.Draw(self.im)

    def header(self, kicker, title):
        self.d.text((58, 30), kicker, font=font(26, True), fill=ACCENT)
        self.d.text((58, 66), title, font=font(48, True), fill=FG)

    def panel(self, arr, x, y, label=None, sub=None):
        img = Image.fromarray(arr)
        self.im.paste(img, (x, y))
        self.d.rectangle([x - 1, y - 1, x + img.width, y + img.height], outline=(42, 50, 66), width=2)
        if label:
            self.d.text((x + 2, y - 44), label, font=font(30, True), fill=FG)
        if sub:
            self.d.text((x + img.width, y - 38), sub, font=font(22), fill=MUTED, anchor="ra")

    def badge(self, x, y, text, color=ACCENT):
        f = font(22, True)
        box = self.d.textbbox((x, y), text, font=f)
        self.d.rounded_rectangle([box[0] - 10, box[1] - 7, box[2] + 10, box[3] + 7], 8, fill=color)
        self.d.text((x, y), text, font=f, fill=(0, 0, 0))

    def subtitle(self, t, cues):
        k = -1
        for i, c in enumerate(cues):
            if t >= c[0] - 0.15:
                k = i
        if k < 0 or t > cues[k][1] + 0.6:
            return
        lines = textwrap.wrap(cues[k][2], 88)
        f = font(31)
        hh = 40 * len(lines)
        y0 = H - 34 - hh
        wmax = max(self.d.textlength(l, font=f) for l in lines)
        self.d.rounded_rectangle([W / 2 - wmax / 2 - 18, y0 - 10, W / 2 + wmax / 2 + 18, y0 + hh + 6], 10, fill=(0, 0, 0))
        for i, l in enumerate(lines):
            self.d.text((W / 2, y0 + 40 * i), l, font=f, fill=(255, 255, 255), anchor="ma")

    def text(self, xy, s, size=24, color=FG, bold=False, anchor="la"):
        self.d.text(xy, s, font=font(size, bold), fill=color, anchor=anchor)


def cue_index(t, cues):
    k = -1
    for i, c in enumerate(cues):
        if t >= c[0] - 0.15:
            k = i
    return k


GRID4 = [(60, 210), (990, 210), (60, 620), (990, 620)]      # 2x2 panel origins
P4W, P4H = 870, 330


class SpeedGrid:
    """2 x 2 comparison of one setup at four rates, through the eye model (slowed) or a camera."""

    def __init__(self, timing, kicker, title, positions, spec, window, freqs, mode="eye", sigma=1.3, reveal=None):
        self.timing, self.kicker, self.title, self.mode = timing, kicker, title, mode
        self.panels = [Panel(P4W, P4H, window, f, positions, spec, sigma) for f in freqs]
        self.ex = exposure_for(self.panels[-1])
        self.freqs = freqs
        self.reveal = reveal or [0, 0, 0, 0]

    def frame(self, t):
        fr = Frame()
        fr.header(self.kicker, self.title)
        k = cue_index(t, self.timing["cues"])
        for i, (p, (x, y)) in enumerate(zip(self.panels, GRID4)):
            if k < self.reveal[i]:
                continue
            if self.mode == "eye":
                xyz = p.xyz(p.w_eye(t / SLOW))
            else:
                xyz = p.xyz(p.w_camera(np.floor(t * FPS) / FPS))
            fr.panel(p.rgb(xyz, self.ex), x, y, f"{p.freq:g} times a second", "1 cm grid")
        if self.mode == "eye":
            fr.badge(1490, 52, "PLAYBACK SLOWED 10×")
            fr.text((1862, 100), "eye blur computed at real speed", 20, MUTED, anchor="ra")
        else:
            fr.badge(1430, 52, "REAL SPEED · PHONE CAMERA", (255, 122, 168))
            fr.text((1862, 100), "30 frames/s, 1/60 s exposure", 20, MUTED, anchor="ra")
        fr.subtitle(t, self.timing["cues"])
        return fr.im


class StillGrid:
    """Steady (fast) results laid out in a grid, revealed cue by cue."""

    def __init__(self, timing, kicker, title, items, cols, pw, ph, origin, gap, common_ex=True):
        self.timing, self.kicker, self.title = timing, kicker, title
        self.items = []
        panels = [Panel(pw, ph, win, 100, pos, spec, 1.3) for (_, _, pos, spec, win, _) in items]
        exs = [exposure_for(p) for p in panels]
        ex_c = min(exs)
        for (label, sub, _, _, _, cue), p, e in zip(items, panels, exs):
            arr = p.rgb(p.xyz(p.w_average()), ex_c if common_ex else e)
            self.items.append((label, sub, arr, cue))
        self.cols, self.pw, self.ph, self.origin, self.gap = cols, pw, ph, origin, gap

    def frame(self, t):
        fr = Frame()
        fr.header(self.kicker, self.title)
        k = cue_index(t, self.timing["cues"])
        for i, (label, sub, arr, cue) in enumerate(self.items):
            if k < cue:
                continue
            r, c = divmod(i, self.cols)
            x = self.origin[0] + c * (self.pw + self.gap[0])
            y = self.origin[1] + r * (self.ph + self.gap[1])
            fr.panel(arr, x, y, label, sub)
        fr.badge(1560, 52, "100 TIMES A SECOND")
        fr.subtitle(t, self.timing["cues"])
        return fr.im


class TitleScene:
    def __init__(self, timing):
        self.timing = timing
        bench, n, spec, pos = setup("mercury", 64, "star", "steady", 1.2, 1.2, "light")
        self.p = Panel(1800, 420, (-150, 50, -40, 40), 100, pos, spec)
        self.ex = exposure_for(self.p)
        self.arr = self.p.rgb(self.p.xyz(self.p.w_average()), self.ex)

    def frame(self, t):
        fr = Frame()
        fr.panel(self.arr, 60, 540)
        fr.text((60, 150), "Shake a Rainbow, part 2", 34, ACCENT, True)
        fr.text((60, 200), "Patterns and speed", 92, FG, True)
        fr.text((60, 330), "Moving a prism in circles, squares and stars, from 5 to 100 times a second",
                34, MUTED)
        fr.text((60, 990), "Mercury-lamp light, light source moving in a star at 100 times a second", 22, MUTED)
        fr.subtitle(t, self.timing["cues"])
        return fr.im


class EyeScene(SpeedGrid):
    def __init__(self, timing):
        spec = np.array([[0.95, 1.0, 1.09]])     # a single white dot
        SpeedGrid.__init__(self, timing, "FIRST, YOUR EYE", "How a moving dot looks at different speeds",
                           dot_positions(15.0), spec, (-30, 30, -20, 20), [5, 20, 50, 100], "eye", sigma=1.6)

    def frame(self, t):
        im = SpeedGrid.frame(self, t)
        return im


class Summary:
    def __init__(self, timing):
        self.timing = timing

    def frame(self, t):
        fr = Frame()
        fr.header("SUMMARY", "Patterns and speed")
        k = cue_index(t, self.timing["cues"])
        items = [
            ("5 times a second", "you see the rainbow move around the shape"),
            ("20 times a second", "comets: your eye catches part of each lap"),
            ("50 and up", "closed, steady shapes; going faster changes nothing"),
            ("Size", "small shapes thicken the rainbow; big ones overlap into new colours"),
            ("Corners", "steady = even outline · slowing = bright corners · snapping = separate rainbows"),
            ("Each colour", "draws its own stretched copy, sometimes going round the other way"),
        ]
        show = {1: 3, 2: 5, 3: 6}.get(k, 0 if k < 1 else 6)
        for i, (a, b) in enumerate(items[:show]):
            y = 230 + i * 105
            fr.text((80, y), a, 36, ACCENT, True)
            fr.text((560, y + 4), b, 32, FG)
        fr.subtitle(t, self.timing["cues"])
        return fr.im


def build_scene(name, timing):
    md436 = float(min_dev_incidence(435.8))
    if name == "title":
        return TitleScene(timing)
    if name == "eye":
        return EyeScene(timing)
    if name == "circle":
        _, _, spec, pos = setup("mercury", md436, "circle", "steady", 3, 1)
        return SpeedGrid(timing, "EXPERIMENT 1", "Prism moving in a circle · mercury lamp", pos, spec,
                         (-140, 35, -28, 28), [5, 20, 50, 100], "eye")
    if name == "square":
        _, _, spec, pos = setup("white", 75, "square", "steady", 2, 2)
        return SpeedGrid(timing, "EXPERIMENT 2", "Prism moving in a square · white light", pos, spec,
                         (-140, 70, -38, 38), [5, 20, 50, 100], "eye")
    if name == "star":
        _, _, spec, pos = setup("mercury", 64, "star", "steady", 1.2, 1.2, "light")
        return SpeedGrid(timing, "EXPERIMENT 3", "Light source moving in a star · mercury lamp", pos, spec,
                         (-165, 50, -30, 30), [5, 20, 50, 100], "eye")
    if name == "camera":
        _, _, spec, pos = setup("mercury", md436, "circle", "steady", 3, 1)
        return SpeedGrid(timing, "WHAT A PHONE RECORDS", "The same circle, filmed", pos, spec,
                         (-140, 35, -28, 28), [20, 30, 50, 100], "camera")
    if name == "gallery":
        items = []
        win = (-175, 50, -32, 32)
        for i, kind in enumerate(["circle", "square", "triangle", "star", "figure8"]):
            _, _, spec, pos = setup("mercury", 64, kind, "steady", 1.2, 1.2, "light")
            label = {"figure8": "Figure 8"}.get(kind, kind.capitalize())
            items.append((label, "mercury lamp", pos, spec, win, 1 if i < 3 else 2))
        bench, n, spec, pos = setup("white", 64, "circle", "steady", 1.2, 1.2, "light")
        items.append(("Circle", "white light", pos, spec, (-160, 70, -38, 38), 3))
        return StillGrid(timing, "THE GALLERY", "Light source moving along each shape", items, 3, 570, 290,
                         (60, 230), (45, 120), common_ex=False)
    if name == "size":
        items = []
        for i, a in enumerate([0.5, 1.5, 3.0]):
            _, _, spec, pos = setup("white", 75, "square", "steady", a, a)
            items.append((f"Square ±{a:g}°", "white light, prism", pos, spec, (-152, 75, -50, 50), i + 1))
        return StillGrid(timing, "SIZE", "Small, medium and large squares", items, 3, 570, 400,
                         (60, 260), (45, 0), common_ex=False)
    if name == "corners":
        items = []
        for i, (mode, lab) in enumerate([("steady", "Steady speed"), ("smooth", "Slows into each corner"),
                                         ("snap", "Snaps corner to corner")]):
            _, _, spec, pos = setup("white", 75, "square", mode, 4.5, 1.5)
            items.append((lab, "±4.5° × ±1.5°", pos, spec, (-150, 118, -45, 45), i + 1))
        return StillGrid(timing, "CORNERS", "Going round the corners of a square", items, 3, 570, 400,
                         (60, 260), (45, 0), common_ex=False)
    if name == "summary":
        return Summary(timing)
    raise KeyError(name)


SCENES = ["title", "eye", "circle", "square", "star", "camera", "gallery", "size", "corners", "summary"]


def render(name, audio_dir, out_dir, still=None):
    timing = json.load(open(f"{audio_dir}/timings.json"))[name]
    scene = build_scene(name, timing)
    if still is not None:
        for s in still:
            scene.frame(s).save(f"{out_dir}/{name}_{s:05.1f}.png")
        return
    n = int(np.ceil(timing["dur"] * FPS))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", f"{audio_dir}/{name}.wav",
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2", "-shortest", f"{out_dir}/{name}.mp4"]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(scene.frame(i / FPS).tobytes())
    p.stdin.close()
    p.wait()
    print("done", name, n, "frames", flush=True)


if __name__ == "__main__":
    audio_dir, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    args = sys.argv[3:]
    still = None
    if "--still" in args:
        i = args.index("--still")
        still = [float(v) for v in args[i + 1].split(",")]
        args = args[:i] + args[i + 2:]
    for name in args or SCENES:
        render(name, audio_dir, out_dir, still)
