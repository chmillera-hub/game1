"""Render the explainer video, one scene per process.

usage: python3 render.py AUDIO_DIR OUT_DIR [scene ...] [--still t]
"""
import json, os, subprocess, sys, textwrap
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, FancyBboxPatch
from prism_sim import *

W, H, FPS = 1920, 1080, 30
BG, PANEL, FG, MUTED, ACCENT = "#0a0d14", "#121824", "#e8ecf3", "#8a93a6", "#ffcc66"
SCREEN_BG = "#040507"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "text.color": FG, "axes.labelcolor": MUTED,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.edgecolor": "#2a3242",
    "axes.facecolor": PANEL, "font.size": 15,
})
TWO_PI = 2 * np.pi


# ------------------------------------------------------------------ helpers
def spectral_rgb(lam):
    """Bright display colour for a single wavelength."""
    c = cmf(np.atleast_1d(lam)) @ XYZ2RGB.T
    c = c - np.minimum(c.min(-1, keepdims=True), 0)
    c = c / c.max(-1, keepdims=True)
    return np.where(c <= 0.0031308, 12.92 * c, 1.055 * c ** (1 / 2.4) - 0.055).clip(0, 1)


DIAG_LAM = np.linspace(400, 700, 16)
DIAG_RGB = spectral_rgb(DIAG_LAM)
D_DRAW = 150.0       # where the screen is drawn in the lab sketch (really 1 m)


def cue_index(t, cues):
    i = -1
    for k, c in enumerate(cues):
        if t >= c[0] - 0.15:
            i = k
    return i


def since(t, cues, k):
    return t - cues[k][0] if k < len(cues) else -1


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def header(fig, kicker, title):
    fig.text(0.03, 0.955, kicker, fontsize=17, color=ACCENT, weight="bold", va="center")
    fig.text(0.03, 0.912, title, fontsize=32, color=FG, weight="bold", va="center")


def subtitle(fig, t, cues):
    k = cue_index(t, cues)
    if k < 0 or t > cues[k][1] + 0.6:
        return
    txt = "\n".join(textwrap.wrap(cues[k][2], 92))
    fig.text(0.5, 0.045, txt, ha="center", va="center", fontsize=23, color="white",
             bbox=dict(boxstyle="round,pad=0.45", fc="black", ec="none", alpha=0.6))


def badge(ax_or_fig, x, y, text, color=ACCENT, size=15, transform=None, ha="left"):
    kw = dict(fontsize=size, color="black", weight="bold", ha=ha, va="center",
              bbox=dict(boxstyle="round,pad=0.35", fc=color, ec="none"))
    if transform is not None:
        kw["transform"] = transform
    ax_or_fig.text(x, y, text, **kw)


def style_plot(ax, title=None):
    ax.set_facecolor(PANEL)
    ax.grid(color="#222a38", lw=0.8)
    for s in ax.spines.values():
        s.set_color("#2a3242")
    if title:
        ax.set_title(title, color=FG, fontsize=17, loc="left", pad=10)


def draw_lab(ax, bench, rot, shift=(0.0, 0.0), beam_angle=0.0, pivot=None, ghosts=(),
             ray_alpha=1.0, extra_rots=(), label_screen=True, lims=None):
    ax.set_facecolor(BG)
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    axis, u = bench.axis, bench.u
    sc = D_DRAW * axis
    a, b = sc - 60 * u, sc + 60 * u
    ax.plot([a[0], b[0]], [a[1], b[1]], color="#d8dde8", lw=5, solid_capstyle="round", zorder=1)
    if label_screen:
        lp = sc + 0 * u + 22 * axis
        ang = np.degrees(np.arctan2(u[1], u[0]))
        ang = (ang + 90) % 180 - 90
        ax.text(lp[0], lp[1], "screen\n(really 1 m away)", color=MUTED, fontsize=13,
                ha="center", va="center", rotation=ang)
    for g in ghosts:
        V = prism_vertices(*g)
        ax.add_patch(Polygon(V, closed=True, fc="none", ec="#7f9cc4", lw=1.2, ls="--", alpha=0.7, zorder=2))

    def rays(r, sh, ba, alpha, lw):
        d0 = np.array([np.cos(ba), np.sin(ba)])
        p0 = BEAM_START if pivot is None else np.asarray(pivot) - 80 * d0
        p1, p2, d2, ok = trace(p0, d0, n_glass(DIAG_LAM), r, sh)
        far = p1[0] - 250 * d0
        ax.plot([far[0], p1[0, 0]], [far[1], p1[0, 1]], color="white", lw=lw + 2, alpha=alpha, zorder=3,
                solid_capstyle="butt")
        for i in range(len(DIAG_LAM)):
            if not ok[i]:
                continue
            t = ((sc - p2[i]) @ axis) / (d2[i] @ axis)
            q = p2[i] + t * d2[i]
            ax.plot([p1[i, 0], p2[i, 0]], [p1[i, 1], p2[i, 1]], color=DIAG_RGB[i], lw=lw * 0.6,
                    alpha=0.7 * alpha, zorder=4)
            ax.plot([p2[i, 0], q[0]], [p2[i, 1], q[1]], color=DIAG_RGB[i], lw=lw, alpha=alpha, zorder=4)

    for r in extra_rots:
        rays(r, shift, beam_angle, 0.12, 1.6)
    rays(rot, shift, beam_angle, ray_alpha, 2.2)
    V = prism_vertices(rot, shift)
    ax.add_patch(Polygon(V, closed=True, fc=(0.55, 0.75, 0.95, 0.22), ec=(0.8, 0.9, 1.0), lw=2, zorder=5))
    if lims is None:
        lims = (-110, 140, -185, 55)
    ax.set_xlim(lims[0], lims[1]); ax.set_ylim(lims[2], lims[3])


def strip_image(xyz, ex, rows=48):
    prof = np.clip(1 - np.abs(np.linspace(-1, 1, rows)) ** 6, 0, 1)
    return xyz_to_srgb(xyz[None, :, :] * prof[:, None, None], ex)


def draw_strip(ax, xyz, px, ex, title=None, lam_ticks=None, bench=None, half_h=14, ruler=True, pad=8):
    ax.set_facecolor(SCREEN_BG)
    img = strip_image(xyz, ex)
    ax.imshow(img, extent=[px[0], px[-1], -half_h, half_h], aspect="auto", interpolation="bilinear")
    ax.set_xlim(px[0], px[-1]); ax.set_ylim(-half_h - 2, half_h + 2)
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color("#2a3242")
    if ruler:
        ticks = np.arange(np.ceil(px[0] / 20) * 20, px[-1] + 1, 20)
        ax.set_xticks(ticks)
        ax.set_xticklabels([f"{t / 10:+.0f}" if t else "0" for t in ticks], fontsize=12)
        ax.set_xlabel("position on screen (cm)", fontsize=13)
    else:
        ax.set_xticks([])
    if title:
        ax.set_title(title, color=FG, fontsize=17, loc="left", pad=28 if lam_ticks is not None else pad)
    if lam_ticks is not None and bench is not None:
        xs = bench.positions(n=n_glass(np.array(lam_ticks, float)))
        for l, x in zip(lam_ticks, xs):
            ax.text(x, half_h + 3.5, f"{l:.0f}", ha="center", va="bottom", fontsize=11, color=MUTED,
                    clip_on=False)


def arrival_spectrum(xs, x_star, sigma=2.0):
    """Time-averaged power per wavelength landing at screen position x_star."""
    w = np.exp(-0.5 * ((x_star - xs) / sigma) ** 2).mean(0)
    return w * planck(LAM) / planck(LAM).max()


def draw_arrival(ax, w, title):
    style_plot(ax, title)
    cols = spectral_rgb(LAM)
    ax.bar(LAM, w / max(w.max(), 1e-12), width=LAM[1] - LAM[0], color=cols, edgecolor="none")
    ax.set_xlim(390, 700); ax.set_ylim(0, 1.15)
    ax.set_xlabel("wavelength (nm)"); ax.set_yticks([])
    ax.set_ylabel("light received")


def magenta_spot(xyz, px, ex):
    rgb = xyz @ XYZ2RGB.T / WHITE_BALANCE * ex
    lum = xyz[:, 1] * ex
    score = np.minimum(rgb[:, 0], rgb[:, 2]) - rgb[:, 1]
    score[lum < 0.2 * lum.max()] = -1e9
    return px[np.argmax(score)]


def avg_xyz(bench, rots=None, shifts=None, n=N_LAM, px=None, sigma=2.0, spec=None):
    xs = bench.positions(rots, n=n) if shifts is None else bench.positions(shift=shifts, n=n)
    return screen_xyz_avg(xs, px, sigma, spec), xs


# ------------------------------------------------------------------ scenes
class Scene:
    def __init__(self, fig, timing):
        self.fig, self.dur, self.cues = fig, timing["dur"], timing["cues"]

    def frame(self, t):
        self.fig.clear()
        self.fig.set_facecolor(BG)
        self.draw(t)
        subtitle(self.fig, t, self.cues)


# A: lab sketch on the left, screen top right, plot bottom right
LAB_BOX = [0.02, 0.12, 0.38, 0.76]
SCR_BOX = [0.44, 0.63, 0.53, 0.20]
PLOT_BOX = [0.47, 0.17, 0.48, 0.34]


class Title(Scene):
    def __init__(self, fig, timing):
        super().__init__(fig, timing)
        self.th = 64.0
        self.bench = Bench(rot_for_incidence(self.th))
        self.px = np.linspace(-160, 80, 1200)
        self.ex = 1.0 / (screen_xyz(self.bench.positions(), self.px) @ XYZ2RGB.T).max()

    def draw(self, t):
        f = self.fig
        wob = 1.2 * smooth((t - 6) / 3) * np.sin(TWO_PI * 0.35 * t)
        rot = rot_for_incidence(self.th + wob)
        draw_lab(f.add_axes([0.0, 0.08, 0.45, 0.86]), self.bench, rot, label_screen=False)
        f.text(0.47, 0.70, "What happens when you\nshake a rainbow?", fontsize=50, weight="bold",
               color=FG, va="center", linespacing=1.15)
        f.text(0.47, 0.53, "Simulated experiments with a vibrating prism", fontsize=26, color=MUTED)
        ax = f.add_axes([0.47, 0.30, 0.48, 0.13])
        x = self.bench.positions(rot)
        draw_strip(ax, screen_xyz(x, self.px), self.px, self.ex, ruler=False)
        f.text(0.47, 0.25, "Exact ray tracing  ·  SF11 flint glass dispersion  ·  CIE 1931 colour vision",
               fontsize=16, color=MUTED)


class Setup(Scene):
    def __init__(self, fig, timing):
        super().__init__(fig, timing)
        self.th = 64.0
        self.bench = Bench(rot_for_incidence(self.th))
        self.px = np.linspace(-160, 80, 1200)
        self.xyz = screen_xyz(self.bench.positions(), self.px)
        self.ex = 1.0 / (self.xyz @ XYZ2RGB.T).max()

    def draw(self, t):
        f, c = self.fig, self.cues
        k = cue_index(t, c)
        header(f, "THE SETUP", "A prism, a beam of white light, and a screen")
        ax = f.add_axes(LAB_BOX)
        draw_lab(ax, self.bench, self.bench.ref_rot)
        ax.text(-100, 18, "white light", color="white", fontsize=15)
        ax.text(-40, 48, "60° prism, SF11 flint glass", color="#bcd3f5", fontsize=15)
        if k >= 1:
            ax.text(-5, -150, "violet bends\nthe most", color=spectral_rgb(420)[0], fontsize=14, ha="center")
            ax.text(118, -150, "red bends\nthe least", color=spectral_rgb(660)[0], fontsize=14, ha="center")
        if k >= 1:
            a2 = f.add_axes(PLOT_BOX)
            style_plot(a2, "Refractive index of SF11 glass")
            lam = np.linspace(390, 700, 300)
            cols = spectral_rgb(lam)
            a2.scatter(lam, n_glass(lam), c=cols, s=14, lw=0)
            a2.set_xlabel("wavelength (nm)"); a2.set_ylabel("n")
            a2.set_xlim(390, 700)
            a2.text(560, 1.835, "higher index → bends more", color=MUTED, fontsize=14)
        if k >= 2:
            a3 = f.add_axes(SCR_BOX)
            draw_strip(a3, self.xyz, self.px, self.ex, "What the screen shows",
                       lam_ticks=[400, 450, 500, 550, 600, 650, 700], bench=self.bench)
        if k >= 3:
            badge(f, 0.97, 0.955, "Snell's law  ·  Sellmeier glass data  ·  additive colour mixing", size=15, ha="right")


class Shake(Scene):
    LAMS = np.array([410.0, 470.0, 530.0, 650.0])

    def __init__(self, fig, timing):
        super().__init__(fig, timing)
        self.th = 64.0
        self.bench = Bench(rot_for_incidence(self.th))
        self.px = np.linspace(-160, 80, 1200)
        self.ex = 1.0 / (screen_xyz(self.bench.positions(), self.px) @ XYZ2RGB.T).max()
        self.rest = self.bench.positions(n=n_glass(self.LAMS))
        self.f = 0.5

    def shift(self, t):
        amp = 5.0 * smooth((t - self.cues[0][0]) / 1.5)
        return np.array([0.0, amp * np.sin(TWO_PI * self.f * (t - self.cues[0][0]))])

    def draw(self, t):
        f = self.fig
        header(f, "EXPERIMENT 1", "Shake the prism sideways (±5 mm)")
        sh = self.shift(t)
        ax = f.add_axes(LAB_BOX)
        draw_lab(ax, self.bench, self.bench.ref_rot, shift=sh, ghosts=[(self.bench.ref_rot, (0, 0))])
        badge(ax, 0.03, 0.95, "SLOW MOTION", transform=ax.transAxes)
        a3 = f.add_axes(SCR_BOX)
        x = self.bench.positions(shift=sh)
        draw_strip(a3, screen_xyz(x, self.px), self.px, self.ex, "Screen")
        for xr in self.rest:
            a3.plot([xr, xr], [14.5, 17], color="white", lw=1.5, clip_on=False)
        a2 = f.add_axes(PLOT_BOX)
        style_plot(a2, "How far each colour moves on the screen")
        tt = np.linspace(max(0, t - 6), t, 200)
        shs = np.stack([np.zeros_like(tt), [self.shift(s)[1] for s in tt]], -1)
        xs = self.bench.positions(shift=shs, n=n_glass(self.LAMS)) - self.rest
        for i, l in enumerate(self.LAMS):
            a2.plot(tt - t, xs[:, i], color=spectral_rgb(l)[0], lw=2.5, label=f"{l:.0f} nm")
        a2.plot(tt - t, shs[:, 1], color="white", lw=1.2, ls="--", label="prism")
        a2.set_xlim(-6, 0); a2.set_ylim(-40, 40)
        a2.set_xlabel("time (s, slow motion)"); a2.set_ylabel("displacement (mm)")
        a2.legend(loc="upper left", fontsize=12, facecolor=PANEL, edgecolor="#2a3242", ncol=5)
        if cue_index(t, self.cues) >= 2:
            a2.text(-5.8, -33, "the whole spectrum is 180 mm wide — these shifts are tiny and nearly equal",
                    color=ACCENT, fontsize=14)


class Rock(Scene):
    LAMS = np.array([410.0, 470.0, 530.0, 650.0])

    def __init__(self, fig, timing):
        super().__init__(fig, timing)
        self.th, self.amp = 75.0, 4.5
        self.bench = Bench(rot_for_incidence(self.th))
        self.px = np.linspace(-175, 115, 1300)
        self.ex = 1.0 / (screen_xyz(self.bench.positions(), self.px) @ XYZ2RGB.T).max()
        ph = np.linspace(0, TWO_PI, 1440, endpoint=False)
        self.avg, self.xs_avg = avg_xyz(self.bench, rot_for_incidence(self.th + self.amp * np.sin(ph)), px=self.px)
        self.ex_avg = 1.5 * self.ex
        self.xm = magenta_spot(self.avg, self.px, self.ex_avg)
        self.arr = arrival_spectrum(self.xs_avg, self.xm)
        self.f = 0.4

    def ang(self, t):
        t0 = self.cues[0][0]
        return self.th + self.amp * smooth((t - t0) / 1.5) * np.sin(TWO_PI * self.f * (t - t0))

    def draw(self, t):
        f, c = self.fig, self.cues
        k = cue_index(t, c)
        header(f, "EXPERIMENT 2", "Rock the prism back and forth (±4.5°)")
        fast = k >= 2
        ax = f.add_axes(LAB_BOX)
        if not fast:
            draw_lab(ax, self.bench, rot_for_incidence(self.ang(t)))
            badge(ax, 0.03, 0.95, "SLOW MOTION  ·  0.4 swings / s", transform=ax.transAxes)
        else:
            jit = self.th + self.amp * np.sin(TWO_PI * 7.37 * t)
            ex_rots = [rot_for_incidence(self.th + self.amp * np.sin(p)) for p in np.linspace(0, TWO_PI, 10)]
            draw_lab(ax, self.bench, rot_for_incidence(jit), ray_alpha=0.6, extra_rots=ex_rots,
                     ghosts=[(rot_for_incidence(self.th - self.amp),), (rot_for_incidence(self.th + self.amp),)])
            badge(ax, 0.03, 0.95, "REAL SPEED  ·  100 swings / s", color="#ff7aa8", transform=ax.transAxes)
        a3 = f.add_axes(SCR_BOX)
        inst = screen_xyz(self.bench.positions(rot_for_incidence(self.ang(t))), self.px)
        if fast:
            m = smooth(since(t, c, 2) / 1.5)
            xyz = (1 - m) * inst * self.ex + m * self.avg * self.ex_avg
            draw_strip(a3, xyz, self.px, 1.0, "What your eye sees" if m > 0.5 else "Screen")
        else:
            draw_strip(a3, inst, self.px, self.ex, "Screen")
        if k >= 3:
            a3.annotate("pink!", xy=(self.xm, 14), xytext=(self.xm + 30, 27), color="#ff9ccf", fontsize=20,
                        weight="bold", ha="center", annotation_clip=False,
                        arrowprops=dict(arrowstyle="-|>", color="#ff9ccf", lw=2.5))
        a2 = f.add_axes(PLOT_BOX)
        if k < 3:
            style_plot(a2, "Where each colour lands over time")
            tt = np.linspace(max(0, t - 6), t, 240)
            xs = self.bench.positions(rot_for_incidence(np.array([self.ang(s) for s in tt])), n=n_glass(self.LAMS))
            for i, l in enumerate(self.LAMS):
                a2.plot(tt - t, xs[:, i], color=spectral_rgb(l)[0], lw=2.5, label=f"{l:.0f} nm")
            a2.set_xlim(-6, 0); a2.set_ylim(-175, 115)
            a2.set_xlabel("time (s, slow motion)"); a2.set_ylabel("screen position (mm)")
            a2.legend(loc="lower left", fontsize=12, facecolor=PANEL, edgecolor="#2a3242", ncol=4)
            if fast:
                a2.text(-5.8, 95, "at 100 swings/s this all happens in 10 ms per swing", color=ACCENT, fontsize=14)
        else:
            draw_arrival(a2, self.arr, "Light arriving at the pink spot (time-averaged)")
            a2.text(545, 0.95, "lots of red + lots of violet\n= pink", color="#ff9ccf", fontsize=16, ha="center")


class Why(Scene):
    def __init__(self, fig, timing):
        super().__init__(fig, timing)
        r = Rock.__new__(Rock)
        Rock.__init__(r, fig, timing | {"cues": [[0, 0, ""]] * 5})
        self.r = r
        b = r.bench
        self.g1 = screen_xyz(b.positions(rot_for_incidence(r.th - r.amp)), r.px)
        self.g2 = screen_xyz(b.positions(rot_for_incidence(r.th + r.amp)), r.px)

    def draw(self, t):
        f, c, r = self.fig, self.cues, self.r
        k = cue_index(t, c)
        header(f, "WHY PINK?", "Vibrating things linger at the ends of their swing")
        # dwell-time plot
        a1 = f.add_axes([0.05, 0.50, 0.30, 0.32])
        style_plot(a1, "Position of a vibrating object")
        a1h = f.add_axes([0.36, 0.50, 0.07, 0.32])
        style_plot(a1h)
        T = max(0.0, t - (c[1][0] if len(c) > 1 else 0))
        T = T * 0.6
        tt = np.linspace(0, max(T, 1e-3), 800)
        y = np.sin(TWO_PI * tt)
        a1.plot(tt, y, color="#9ec5ff", lw=2.5)
        a1.plot([tt[-1]], [y[-1]], "o", color="white", ms=12)
        a1.set_xlim(0, max(4.0, T)); a1.set_ylim(-1.25, 1.25)
        a1.set_xlabel("time"); a1.set_yticks([-1, 0, 1]); a1.set_yticklabels(["end", "middle", "end"])
        hist, edges = np.histogram(y, bins=25, range=(-1, 1))
        a1h.barh((edges[:-1] + edges[1:]) / 2, hist, height=edges[1] - edges[0], color="#9ec5ff")
        a1h.set_ylim(-1.25, 1.25); a1h.set_yticks([]); a1h.set_xticks([])
        a1h.set_title("time spent", fontsize=14, color=FG)
        # ghosts + average
        a3 = f.add_axes([0.47, 0.67, 0.50, 0.09])
        draw_strip(a3, r.avg, r.px, r.ex_avg, "Time-averaged screen", ruler=False)
        if k >= 2:
            ga = f.add_axes([0.47, 0.80, 0.50, 0.05])
            draw_strip(ga, self.g1, r.px, r.ex, ruler=False)
            ga.text(r.px[0] + 3, 0, "ghost at one end of the swing ", color="white", fontsize=12, va="center")
            gb = f.add_axes([0.47, 0.58, 0.50, 0.05])
            draw_strip(gb, self.g2, r.px, r.ex, ruler=False)
            gb.text(r.px[0] + 3, 0, "ghost at the other end", color="white", fontsize=12, va="center")
        if k >= 3:
            for axx in [a3] + ([ga, gb] if k >= 2 else []):
                axx.axvline(r.xm, color="#ff9ccf", lw=2, ls="--")
            a2 = f.add_axes([0.52, 0.17, 0.43, 0.32])
            draw_arrival(a2, r.arr, "Light arriving at the dashed line")
            a2.text(545, 1.0, "red from one ghost, violet from the other", color="#ff9ccf", fontsize=14, ha="center")
        if k >= 1:
            f.text(0.05, 0.40, "Near the ends it slows down and turns around,\nso it spends most of its time there.",
                   fontsize=19, color=FG, va="top", linespacing=1.4)


class Waveform(Scene):
    def __init__(self, fig, timing):
        super().__init__(fig, timing)
        self.th, self.amp = 75.0, 4.5
        self.bench = Bench(rot_for_incidence(self.th))
        self.px = np.linspace(-175, 115, 1300)
        still = screen_xyz(self.bench.positions(), self.px)
        self.still = still
        self.ex = 1.0 / (still @ XYZ2RGB.T).max()
        ph = np.linspace(0, TWO_PI, 2000, endpoint=False)
        self.waves = [("constant speed (triangle)", 2 / np.pi * np.arcsin(np.sin(ph))),
                      ("smooth (sine)", np.sin(ph)),
                      ("snapping (square)", np.sign(np.sin(ph)))]
        self.avgs = [avg_xyz(self.bench, rot_for_incidence(self.th + self.amp * w), px=self.px)[0]
                     for _, w in self.waves]
        self.xm = magenta_spot(self.avgs[2], self.px, 1.6 * self.ex)

    def draw(self, t):
        f, c = self.fig, self.cues
        k = cue_index(t, c)
        header(f, "THE SHAPE OF THE SHAKE", "Same amplitude, three ways of moving")
        y0 = 0.73
        a = f.add_axes([0.40, y0, 0.57, 0.08])
        draw_strip(a, self.still, self.px, self.ex, "Still prism", ruler=False)
        for i, (name, w) in enumerate(self.waves):
            if k < i + 1:
                continue
            yb = 0.53 - i * 0.165
            aw = f.add_axes([0.04, yb, 0.16, 0.11])
            style_plot(aw)
            ph = np.linspace(0, 2, len(w))
            aw.plot(ph, np.concatenate([w[::2], w[::2]]), color="#9ec5ff", lw=2.2)
            aw.set_xticks([]); aw.set_yticks([]); aw.set_ylim(-1.3, 1.3)
            aw.set_title(name, fontsize=14, color=FG, loc="left")
            ah = f.add_axes([0.215, yb, 0.06, 0.11])
            style_plot(ah)
            hist, e = np.histogram(w, bins=21, range=(-1.05, 1.05))
            ah.barh((e[:-1] + e[1:]) / 2, hist, height=e[1] - e[0], color="#9ec5ff")
            ah.set_xticks([]); ah.set_yticks([]); ah.set_ylim(-1.3, 1.3)
            ah.set_title("time spent", fontsize=12, color=MUTED)
            asx = f.add_axes([0.40, yb + 0.01, 0.57, 0.09])
            draw_strip(asx, self.avgs[i], self.px, 1.6 * self.ex, ruler=False)
            if i == 2 and k >= 3:
                asx.annotate("vivid magenta", xy=(self.xm, -16), xytext=(self.xm, -36), color="#ff6ad5",
                             fontsize=18, weight="bold", ha="center", annotation_clip=False,
                             arrowprops=dict(arrowstyle="-|>", color="#ff6ad5", lw=2.5))
            if i == 0 and k >= 1:
                asx.text(self.px[-1] - 4, 22, "evenly smeared → greyish middle", color=MUTED, fontsize=13, ha="right")
            if i == 1 and k >= 2:
                asx.text(self.px[-1] - 4, 22, "lingers at the ends → dusky pink", color=MUTED, fontsize=13, ha="right")
            if i == 2 and k >= 3:
                asx.text(self.px[-1] - 4, 22, "only two positions → two crisp rainbows", color=MUTED, fontsize=13, ha="right")


class AmpMap(Scene):
    def __init__(self, fig, timing):
        super().__init__(fig, timing)
        self.th, self.amax = 75.0, 8.0
        self.bench = Bench(rot_for_incidence(self.th))
        self.px = np.linspace(-185, 125, 900)
        ph = np.linspace(0, TWO_PI, 600, endpoint=False)
        self.amps = np.linspace(0, self.amax, 200)
        self.map = np.array([avg_xyz(self.bench, rot_for_incidence(self.th + a * np.sin(ph)), px=self.px)[0]
                             for a in self.amps])
        self.ex = 1.0 / (self.map[0] @ XYZ2RGB.T).max()
        # brightness compensates for the light spreading out as the swing grows
        self.rowgain = 1 + 0.7 * self.amps / self.amax
        self.img = xyz_to_srgb(self.map * (self.ex * self.rowgain)[:, None, None])

    def draw(self, t):
        f, c = self.fig, self.cues
        k = cue_index(t, c)
        header(f, "EVERY AMPLITUDE AT ONCE", "Smooth (sine) rocking, from still to ±8°")
        ax = f.add_axes([0.08, 0.30, 0.86, 0.52])
        ax.imshow(self.img, extent=[self.px[0], self.px[-1], 0, self.amax], aspect="auto", origin="lower",
                  interpolation="bilinear")
        ax.set_xlabel("position on screen (mm)"); ax.set_ylabel("rocking amplitude (± degrees)")
        prog = smooth((t - c[1][0]) / max(1.0, self.dur - c[1][0] - 2)) if k >= 1 else 0
        a_now = prog * self.amax
        ax.axhline(a_now, color="white", lw=1.5, ls="--")
        ax.text(self.px[-1] - 3, a_now + 0.15, f"±{a_now:.1f}°", color="white", ha="right", va="bottom", fontsize=15)
        if k >= 2:
            ax.text(-15, 6.6, "pink / grey", color="white", fontsize=17, ha="center", weight="bold")
            ax.text(95, 3.0, "pure red\nedge", color="#ff6b6b", fontsize=16, ha="center")
            ax.text(-150, 3.0, "pure violet\nedge", color="#b58cff", fontsize=16, ha="center")
        a2 = f.add_axes([0.08, 0.13, 0.86, 0.08])
        i = int(round(a_now / self.amax * (len(self.amps) - 1)))
        a2.imshow(strip_image(self.map[i], self.ex * self.rowgain[i]), extent=[self.px[0], self.px[-1], -14, 14],
                  aspect="auto", interpolation="bilinear")
        a2.set_xticks([]); a2.set_yticks([])
        a2.set_title("what the screen looks like at the dashed line", fontsize=14, color=MUTED, loc="left")


class Freeze(Scene):
    LAMS = np.array([405.0, 480.0, 650.0])
    FROZEN = 480.0
    EXAG = 4.0

    def __init__(self, fig, timing):
        super().__init__(fig, timing)
        self.th, self.amp = float(min_dev_incidence(self.FROZEN)), 1.5
        self.bench = Bench(rot_for_incidence(self.th))
        self.px = np.linspace(-160, 80, 1200)
        self.ex = 1.0 / (screen_xyz(self.bench.positions(), self.px) @ XYZ2RGB.T).max()
        self.rest = self.bench.positions(n=n_glass(self.LAMS))
        self.f = 0.3

    def ang(self, t):
        t0 = self.cues[1][0]
        return self.th + self.amp * smooth((t - t0) / 1.5) * np.sin(TWO_PI * self.f * (t - t0))

    def draw(self, t):
        f, c = self.fig, self.cues
        k = cue_index(t, c)
        header(f, "EXPERIMENT 3", "Rock near minimum deviation: one colour freezes")
        ax = f.add_axes(LAB_BOX)
        draw_lab(ax, self.bench, rot_for_incidence(self.ang(t)))
        badge(ax, 0.03, 0.95, "SLOW MOTION", transform=ax.transAxes)
        a3 = f.add_axes(SCR_BOX)
        xs = self.bench.positions(rot_for_incidence(self.ang(t)), n=n_glass(self.LAMS))
        draw_strip(a3, screen_xyz(self.bench.positions(rot_for_incidence(self.ang(t))), self.px),
                   self.px, self.ex, f"Screen   (markers show motion exaggerated {self.EXAG:.0f}×)")
        for l, x, xr in zip(self.LAMS, xs, self.rest):
            a3.plot([xr, xr], [-14, 14], color="white", lw=1, ls=":", alpha=0.8)
            a3.plot([xr + self.EXAG * (x - xr)], [9], marker="v", ms=15, color="white", mec="black")
        if k >= 2:
            a3.text(self.rest[1], -9, f"frozen\n({self.FROZEN:.0f} nm)", color="white", ha="center", fontsize=13,
                    va="center", weight="bold")
        a2 = f.add_axes([0.47, 0.17, 0.43, 0.34])
        if k < 5:
            style_plot(a2, "Displacement of each colour")
            tt = np.linspace(max(0, t - 8), t, 300)
            xx = self.bench.positions(rot_for_incidence(np.array([self.ang(s) for s in tt])), n=n_glass(self.LAMS))
            names = ["violet 405 nm", f"{self.FROZEN:.0f} nm", "red 650 nm"]
            for i, l in enumerate(self.LAMS):
                y = xx[:, i] - self.rest[i]
                a2.plot(tt - t, y, color=spectral_rgb(l)[0], lw=3.5 if l == self.FROZEN else 2.2)
                a2.text(0.15, y[-1], names[i], color=spectral_rgb(l)[0] * 0.6 + 0.4, fontsize=13, va="center",
                        clip_on=False)
            tilt = np.array([self.ang(s) for s in tt]) - self.th
            a2.plot(tt - t, tilt * 4, color="white", lw=1, ls="--", alpha=0.6)
            a2.text(-7.9, -7.3, "dashed: prism tilt", color=MUTED, fontsize=12)
            a2.set_xlim(-8, 0); a2.set_ylim(-8.5, 8.5)
            a2.set_xlabel("time (s, slow motion)"); a2.set_ylabel("displacement on screen (mm)")
            if k >= 3:
                a2.text(-7.9, 7.2, f"{self.FROZEN:.0f} nm: tiny, one-sided, twice per swing", color=ACCENT, fontsize=14)
            if k >= 4:
                a2.text(-3.6, 7.2, "violet and red: opposite directions", color=ACCENT, fontsize=14)
        else:
            style_plot(a2, "Which colour freezes, for each prism tilt")
            lam = np.linspace(400, 700, 300)
            a2.scatter(min_dev_incidence(lam), lam, c=spectral_rgb(lam), s=16, lw=0)
            p = (np.sin(TWO_PI * 0.15 * since(t, c, 5)) + 1) / 2
            l_now = 400 + 300 * p
            a2.plot([min_dev_incidence(l_now)], [l_now], "o", ms=16, mfc="none", mec="white", mew=2.5)
            a2.set_xlabel("incidence angle at the prism (°)"); a2.set_ylabel("frozen wavelength (nm)")


class Mercury(Scene):
    def __init__(self, fig, timing):
        super().__init__(fig, timing)
        self.th = float(min_dev_incidence(435.8))
        self.amax = 3.5
        self.bench = Bench(rot_for_incidence(self.th))
        self.px = np.linspace(-130, 40, 1400)
        self.nl = n_glass(HG_LINES)
        ph = np.linspace(0, TWO_PI, 900, endpoint=False)
        self.amps = np.linspace(0, self.amax, 160)
        self.map = np.array([screen_xyz_avg(self.bench.positions(rot_for_incidence(self.th + a * np.sin(ph)), n=self.nl),
                                            self.px, 0.5, HG_XYZ) for a in self.amps])
        self.ex = 0.9 / (self.map[0] @ XYZ2RGB.T).max()
        self.img = xyz_to_srgb(self.map * self.ex)
        self.rest = self.bench.positions(n=self.nl)

    def amp_now(self, t):
        c = self.cues
        if cue_index(t, c) < 1:
            return 0.0
        return self.amax * smooth(since(t, c, 1) / 9.0)

    def draw(self, t):
        f, c = self.fig, self.cues
        k = cue_index(t, c)
        header(f, "EXPERIMENT 4", "A mercury lamp: spectral lines split into fake pairs")
        a = self.amp_now(t)
        ax = f.add_axes(LAB_BOX)
        if a > 0.05:
            ex_rots = [rot_for_incidence(self.th + a * np.sin(p)) for p in np.linspace(0, TWO_PI, 10)]
            draw_lab(ax, self.bench, rot_for_incidence(self.th + a * np.sin(TWO_PI * 7.37 * t)),
                     extra_rots=ex_rots, ray_alpha=0.6,
                     ghosts=[(rot_for_incidence(self.th - a),), (rot_for_incidence(self.th + a),)])
            badge(ax, 0.03, 0.95, f"REAL SPEED  ·  ±{a:.1f}°", color="#ff7aa8", transform=ax.transAxes)
        else:
            draw_lab(ax, self.bench, self.bench.ref_rot)
        i = int(round(a / self.amax * (len(self.amps) - 1)))
        a3 = f.add_axes(SCR_BOX)
        draw_strip(a3, self.map[i], self.px, self.ex, "Screen (time-averaged)", pad=30)
        for lab, x, ha in [("405", self.rest[0], "center"), ("436", self.rest[1], "center"),
                           ("546", self.rest[2], "right"), ("577/579", self.rest[3] + 1, "left")]:
            a3.text(x, 18, lab + " nm", color=MUTED, fontsize=12, ha=ha, clip_on=False)
        a2 = f.add_axes([0.47, 0.17, 0.48, 0.36])
        a2.imshow(self.img, extent=[self.px[0], self.px[-1], 0, self.amax], aspect="auto", origin="lower",
                  interpolation="bilinear")
        a2.axhline(a, color="white", lw=1.2, ls="--")
        a2.set_xlabel("position on screen (mm)"); a2.set_ylabel("rocking amplitude (±°)")
        a2.set_title("Each line traced as the amplitude grows", color=FG, fontsize=17, loc="left", pad=8)
        if k >= 2:
            a2.annotate("stays sharp", xy=(self.rest[1], 2.6), xytext=(self.rest[1] + 25, 3.0), color="white",
                        fontsize=15, arrowprops=dict(arrowstyle="-|>", color="white"))
            a2.text(self.rest[2] - 2, 0.35, "splits", color="white", fontsize=15, ha="right")


class Light(Scene):
    LAMS = np.array([405.0, 450.0, 520.0, 650.0])

    def __init__(self, fig, timing):
        super().__init__(fig, timing)
        self.th = 64.0
        self.bench = Bench(rot_for_incidence(self.th))
        self.px = np.linspace(-175, 95, 1300)
        self.ex = 1.0 / (screen_xyz(self.bench.positions(), self.px) @ XYZ2RGB.T).max()
        self.pivot = self.bench.entry
        self.rest = self.bench.positions(n=n_glass(self.LAMS))
        self.f, self.amp = 0.35, np.radians(1.0)

    def ba(self, t):
        t0 = self.cues[0][0]
        return self.amp * smooth((t - t0) / 1.5) * np.sin(TWO_PI * self.f * (t - t0))

    def draw(self, t):
        f, c = self.fig, self.cues
        k = cue_index(t, c)
        header(f, "VIBRATING THE LIGHT", "Wiggle the beam instead of the prism")
        ba = self.ba(t)
        ax = f.add_axes(LAB_BOX)
        draw_lab(ax, self.bench, self.bench.ref_rot, beam_angle=ba, pivot=self.pivot)
        badge(ax, 0.03, 0.95, "SLOW MOTION  ·  beam tilts ±1°", transform=ax.transAxes)
        a3 = f.add_axes(SCR_BOX)
        x = self.bench.positions(beam_angle=ba, beam_pivot=self.pivot)
        draw_strip(a3, screen_xyz(x, self.px), self.px, self.ex, "Screen")
        a2 = f.add_axes(PLOT_BOX)
        if k < 2:
            style_plot(a2, "Displacement of each colour")
            tt = np.linspace(max(0, t - 8), t, 300)
            bas = np.array([self.ba(s) for s in tt])
            xx = self.bench.positions(beam_angle=bas, beam_pivot=self.pivot, n=n_glass(self.LAMS)) - self.rest
            for i, l in enumerate(self.LAMS):
                a2.plot(tt - t, xx[:, i], color=spectral_rgb(l)[0], lw=2.4, label=f"{l:.0f} nm")
            a2.set_xlim(-8, 0); a2.set_ylim(-30, 30)
            a2.set_xlabel("time (s, slow motion)"); a2.set_ylabel("mm")
            a2.legend(loc="lower left", fontsize=12, facecolor=PANEL, edgecolor="#2a3242", ncol=4)
            if k >= 1:
                a2.text(-7.8, 24, "all colours move together; violet moves most; none freezes", color=ACCENT,
                        fontsize=14)
        elif k < 4:
            a2.set_facecolor(PANEL); a2.set_xticks([]); a2.set_yticks([])
            a2.set_title("The Doppler effect", color=FG, fontsize=17, loc="left", pad=10)
            lines = [("vibration speed", "1 m/s"),
                     ("frequency shift  Δf / f = v / c", "3.3 × 10⁻⁹"),
                     ("colour shift at 550 nm", "0.000002 nm"),
                     ("movement on the screen", "≈ 0.8 nanometres")]
            for j, (a_, b_) in enumerate(lines):
                if k >= 3 or j < 2:
                    a2.text(0.04, 0.80 - j * 0.2, a_, fontsize=19, color=MUTED, transform=a2.transAxes)
                    a2.text(0.96, 0.80 - j * 0.2, b_, fontsize=21, color=FG, weight="bold", ha="right",
                            transform=a2.transAxes)
        else:
            style_plot(a2, "Two colours overlapping: 500 nm + 600 nm")
            tfs = np.linspace(0, 40, 3000)            # femtoseconds
            f1, f2 = 299.79 / 500, 299.79 / 600       # cycles per fs
            e = np.cos(TWO_PI * f1 * tfs) + np.cos(TWO_PI * f2 * tfs)
            a2.plot(tfs, e, color="#c9d6ff", lw=1.2)
            a2.plot(tfs, 2 * np.abs(np.cos(np.pi * (f1 - f2) * tfs)), color=ACCENT, lw=2, ls="--")
            a2.set_xlabel("time (femtoseconds)"); a2.set_yticks([])
            a2.set_xlim(0, 40); a2.set_ylim(-2.4, 2.9)
            a2.text(1, 2.45, "beats every 10 fs (100 trillion per second) → averages out; intensities just add",
                    color=ACCENT, fontsize=14)


class Camera(Scene):
    def __init__(self, fig, timing):
        super().__init__(fig, timing)
        self.th, self.amp = 75.0, 3.0
        self.bench = Bench(rot_for_incidence(self.th))
        self.px = np.linspace(-160, 100, 900)
        # lookup table of instantaneous screens over the swing
        self.tab_a = np.linspace(-self.amp, self.amp, 401)
        xs = self.bench.positions(rot_for_incidence(self.th + self.tab_a))
        self.tab = np.array([screen_xyz(x, self.px) for x in xs])
        self.ex = 1.0 / (self.tab[200] @ XYZ2RGB.T).max()
        ph = np.linspace(0, TWO_PI, 1000, endpoint=False)
        self.avg = screen_xyz_avg(self.bench.positions(rot_for_incidence(self.th + self.amp * np.sin(ph))), self.px)
        self.rows = 300

    def look(self, a):
        i = np.clip(np.round((a + self.amp) / (2 * self.amp) * 400).astype(int), 0, 400)
        return self.tab[i]

    def draw(self, t):
        f, c = self.fig, self.cues
        k = cue_index(t, c)
        header(f, "A WARNING FOR FILMMAKERS", "Cameras see things your eye doesn't")
        a1 = f.add_axes([0.05, 0.50, 0.42, 0.30])
        img = strip_image(self.avg, 1.5 * self.ex, rows=self.rows)
        a1.imshow(img, extent=[self.px[0], self.px[-1], 0, 1], aspect="auto", interpolation="bilinear")
        a1.set_xticks([]); a1.set_yticks([])
        a1.set_title("What your eye sees", color=FG, fontsize=18, loc="left")
        if k < 3:
            a2 = f.add_axes([0.53, 0.50, 0.42, 0.30])
            fvib, readout = 243.0, 0.030
            frame = np.floor(t * FPS) / FPS
            trow = frame + np.linspace(0, readout, self.rows)
            a = self.amp * np.sin(TWO_PI * fvib * trow)
            prof = np.clip(1 - np.abs(np.linspace(-1, 1, self.rows)) ** 6, 0, 1)
            im = xyz_to_srgb(self.look(a) * prof[:, None, None], self.ex)
            if k >= 2:
                a2.imshow(im, extent=[self.px[0], self.px[-1], 0, 1], aspect="auto", interpolation="bilinear")
            a2.set_xticks([]); a2.set_yticks([])
            a2.set_facecolor(SCREEN_BG)
            a2.set_title("Phone camera (rolling shutter)", color=FG, fontsize=18, loc="left")
            f.text(0.53, 0.44, "rows read top→bottom over 30 ms; prism rocks 243 times/s", color=MUTED, fontsize=15)
        else:
            a2 = f.add_axes([0.53, 0.62, 0.42, 0.18])
            fvib = 30.5
            frame = np.floor(t * FPS) / FPS
            a = self.amp * np.sin(TWO_PI * fvib * frame)
            a2.imshow(strip_image(self.look(np.array(a)), self.ex), extent=[self.px[0], self.px[-1], -1, 1],
                      aspect="auto", interpolation="bilinear")
            a2.set_xticks([]); a2.set_yticks([])
            a2.set_title("Camera at 30 frames/s, prism at 30.5 swings/s", color=FG, fontsize=18, loc="left")
            a3 = f.add_axes([0.53, 0.20, 0.42, 0.33])
            style_plot(a3, "True motion vs. what the camera samples")
            tt = np.linspace(frame - 1.0, frame, 3000)
            a3.plot(tt - frame, np.sin(TWO_PI * fvib * tt), color="#5f6b82", lw=0.8)
            fr = np.arange(np.ceil((frame - 1.0) * FPS), np.floor(frame * FPS) + 1) / FPS
            a3.plot(fr - frame, np.sin(TWO_PI * fvib * fr), "o", color=ACCENT, ms=6)
            a3.plot(tt - frame, np.sin(TWO_PI * fvib * tt[-1] + TWO_PI * 0.5 * (tt - tt[-1])), color=ACCENT,
                    lw=1.5, ls="--")
            a3.set_xlim(-1, 0); a3.set_ylim(-1.3, 1.3)
            a3.set_xlabel("time (s)"); a3.set_yticks([])
            a3.text(-0.98, 1.08, "grey: real 30.5 Hz shaking   gold: frames → looks like 0.5 Hz", color=MUTED,
                    fontsize=13)


class Summary(Scene):
    def __init__(self, fig, timing):
        super().__init__(fig, timing)

    def draw(self, t):
        f, c = self.fig, self.cues
        k = cue_index(t, c)
        header(f, "SUMMARY", "What happens when you shake a rainbow")
        items = [
            ("Slide the prism", "almost nothing: every colour shifts by the same few mm"),
            ("Rock the prism", "colours overlap → pink & magenta, which are in no rainbow"),
            ("Shape of the shake", "constant speed → grey · sine → dusky pink · snapping → vivid magenta"),
            ("Rock at minimum deviation", "one colour freezes (quivering at 2×), the rest breathe like an accordion"),
            ("Spectral lines", "split into fake pairs, except the frozen one"),
            ("Cameras", "rolling shutter turns bands into snakes; strobing makes fast shaking look slow"),
            ("Vibrating the light", "no frozen colour; Doppler shift < 1 nanometre on the screen; no fringes"),
        ]
        show = {1: 1, 2: 3, 3: 4, 4: 6, 5: 7}.get(k, 0 if k < 1 else 7)
        for i, (a, b) in enumerate(items[:show]):
            y = 0.80 - i * 0.085
            f.text(0.06, y, a, fontsize=24, color=ACCENT, weight="bold", va="center")
            f.text(0.36, y, b, fontsize=21, color=FG, va="center")
        if k >= 5:
            f.text(0.06, 0.15, "Simulation: exact 2D ray tracing (vector Snell's law), Schott SF11 Sellmeier dispersion,\n"
                   "CIE 1931 colour matching, additive light mixing, time-averaging for persistence of vision.",
                   fontsize=15, color=MUTED, va="center", linespacing=1.5)


SCENE_CLASSES = {"title": Title, "setup": Setup, "shake": Shake, "rock": Rock, "why": Why,
                 "waveform": Waveform, "map": AmpMap, "freeze": Freeze, "mercury": Mercury,
                 "light": Light, "camera": Camera, "summary": Summary}


def render_scene(name, audio_dir, out_dir, still=None):
    timing = json.load(open(f"{audio_dir}/timings.json"))[name]
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
    scene = SCENE_CLASSES[name](fig, timing)
    if still is not None:
        for s in still:
            scene.frame(s)
            fig.savefig(f"{out_dir}/{name}_{s:05.1f}.png", dpi=100, facecolor=BG)
        return
    n = int(np.ceil(timing["dur"] * FPS))
    out = f"{out_dir}/{name}.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", f"{audio_dir}/{name}.wav",
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2", "-shortest", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(n):
        scene.frame(i / FPS)
        fig.canvas.draw()
        p.stdin.write(fig.canvas.buffer_rgba())
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
    for name in args or list(SCENE_CLASSES):
        render_scene(name, audio_dir, out_dir, still)
