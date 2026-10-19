"""Psalm 22 - compositor: frames -> grade -> transitions -> film look -> upscale -> captions -> video.

Usage (see docs/comp.md):
  python comp/composite.py                         # whole film -> $WORK/comp/mezz.mp4 (10-bit) + final encode
  python comp/composite.py --no-encode             # only the 10-bit mezzanine
  python comp/composite.py --stills 0,1500,6200 --stills-dir /tmp/st   # PNG stills of global frames
  python comp/composite.py --direct out.mp4 --shots s00,s01a            # quick single-pass preview with audio
  python comp/composite.py --frames 0-479 --mezz /tmp/m.mp4 --no-encode

Frame sources per shot: $WORK/frames/<shot>/<quality>/NNNN.png (1-based shot frames, nframes + tail).
Per frame the best quality that has exactly that frame wins (final > draft > preview); missing frames
are interpolated (cross-blend) between the nearest rendered frames of the best-covering quality, so
sparse test renders already play as an animatic.  Shots with no frames get a labelled placeholder card.
Grading hints come from post.json next to the frames (newest one wins) - keys in docs/comp.md.
"""
import argparse, bisect, json, math, os, subprocess, sys, time
import multiprocessing as mp
from collections import OrderedDict

import numpy as np
import cv2
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WORK = os.environ.get("WORK", "/opt/work/psalm22")
sys.path.insert(0, HERE)
import captions as CAP  # noqa: E402

cv2.setNumThreads(1)
QUALITIES = ("final", "draft", "preview")
DISSOLVE = 14
FLASH_PRE, FLASH_POST = 3, 10          # frames of white bloom before / after a flash cut
FB_OUT, FB_IN = 6, 9                   # fade_black: frames down / frames up
LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)
_LUMA_M = LUMA.reshape(1, 3)
# BT.709 R'G'B' -> Y', Cb, Cr (unscaled)
_YUV_M = np.array([[0.2126, 0.7152, 0.0722],
                   [-0.2126 / 1.8556, -0.7152 / 1.8556, 0.9278 / 1.8556],
                   [0.7874 / 1.5748, -0.7152 / 1.5748, -0.0722 / 1.5748]], np.float32)


def luma(F):
    """Fast BT.709 luma of a float32 RGB image (cv2.transform beats numpy matmul here)."""
    return cv2.transform(F, _LUMA_M)

# ----------------------------------------------------------------------------------------------
# grading parameters
# ----------------------------------------------------------------------------------------------
LOOK_DEFAULT = {          # gentle global film look (every shot unless post.json overrides)
    "bloom": 0.16, "bloom_threshold": 0.70, "bloom_radius": 1.0,
    "halation": 0.06, "vignette": 0.16, "sharpen": 0.35, "grain": 0.0,
}
GRADE_DEFAULT = {
    "exposure": 0.0, "contrast": 1.0, "pivot": 0.45, "saturation": 1.0,
    "temperature": 0.0, "tint": 0.0, "lift": 0.0, "gamma": 1.0, "gain": 1.0,
    "shadows": 0.0, "highlights": 0.0,
}
PRESETS = {
    "neutral": {},
    "warm": {"temperature": 0.25, "saturation": 1.04, "highlights": [0.02, 0.01, -0.012], "bloom": 0.22},
    "gold": {"temperature": 0.45, "tint": 0.03, "saturation": 1.08, "gain": [1.04, 1.0, 0.9],
             "highlights": [0.03, 0.015, -0.02], "bloom": 0.4, "bloom_threshold": 0.62, "halation": 0.12},
    "cool": {"temperature": -0.3, "saturation": 0.92, "shadows": [-0.01, 0.0, 0.025]},
    "night": {"exposure": -0.25, "temperature": -0.55, "tint": -0.05, "saturation": 0.72, "contrast": 1.06,
              "shadows": [-0.005, 0.005, 0.03], "bloom": 0.25, "bloom_threshold": 0.55},
    "eclipse": {"exposure": -0.15, "temperature": 0.15, "saturation": 0.62, "contrast": 1.12,
                "gain": [1.04, 0.93, 0.86], "shadows": [0.012, 0.0, -0.005], "vignette": 0.3},
    "flashback": {"lift": 0.035, "contrast": 0.92, "saturation": 0.86, "temperature": 0.18,
                  "bloom": 0.38, "bloom_threshold": 0.6, "vignette": 0.26},
    "glory": {"exposure": 0.12, "temperature": 0.3, "saturation": 1.04, "lift": 0.015,
              "bloom": 0.5, "bloom_threshold": 0.58, "halation": 0.14},
    "bleak": {"saturation": 0.6, "temperature": -0.12, "contrast": 1.08, "vignette": 0.24},
    "dawn": {"temperature": 0.2, "tint": 0.05, "saturation": 1.05, "shadows": [0.0, 0.0, 0.02],
             "highlights": [0.03, 0.01, -0.01], "bloom": 0.3},
    "dusk": {"temperature": 0.35, "tint": 0.06, "exposure": -0.1, "shadows": [-0.005, 0.0, 0.02], "bloom": 0.28},
    "candle": {"temperature": 0.55, "saturation": 1.05, "exposure": -0.05, "bloom": 0.35,
               "bloom_threshold": 0.55, "halation": 0.12, "vignette": 0.3},
    "space": {"contrast": 1.1, "saturation": 1.05, "temperature": -0.05, "bloom": 0.3,
              "bloom_threshold": 0.6, "vignette": 0.1},
}
NUM_KEYS = set(LOOK_DEFAULT) | set(GRADE_DEFAULT)


def resolve_post(post):
    """post.json dict -> (params at shot start, params at shot end)."""
    p = dict(GRADE_DEFAULT)
    p.update(LOOK_DEFAULT)
    names = post.get("grade") or []
    if isinstance(names, str):
        names = [names]
    for n in names:
        p.update(PRESETS.get(n, {}))
    for k, v in post.items():
        if k in NUM_KEYS:
            p[k] = v
    p["grain"] = min(float(p.get("grain") or 0), 0.03)
    e = dict(p)
    for k, v in (post.get("end") or {}).items():
        if k in NUM_KEYS:
            e[k] = v
        elif k == "grade":
            for n in ([v] if isinstance(v, str) else v):
                e.update(PRESETS.get(n, {}))
    return p, e


def lerp_params(a, b, w):
    if w <= 0 or a is b:
        return a
    out = {}
    for k, va in a.items():
        vb = b.get(k, va)
        if isinstance(va, (list, tuple)) or isinstance(vb, (list, tuple)):
            out[k] = list(np.asarray(va, np.float32) * (1 - w) + np.asarray(vb, np.float32) * w)
        elif isinstance(va, (int, float)) and isinstance(vb, (int, float)):
            out[k] = va * (1 - w) + vb * w
        else:
            out[k] = vb if w >= 0.5 else va
    return out


def vec3(v):
    return np.asarray(v if isinstance(v, (list, tuple, np.ndarray)) else [v] * 3, np.float32)


SHADOW_LIFT = float(os.environ.get("SHADOW_LIFT", "0.05"))
SHADOW_STRETCH = float(os.environ.get("SHADOW_STRETCH", "1.8"))


def grade(F, p):
    """Per-shot grade on a display-referred float RGB image (in place where possible)."""
    t, tn, ex = float(p["temperature"]), float(p["tint"]), float(p["exposure"])
    g_lin = np.array([1 + 0.16 * t, 1 - 0.10 * tn, 1 - 0.16 * t], np.float32)
    g_lin = g_lin / float(g_lin @ LUMA) * (2.0 ** ex)
    gain = vec3(p["gain"]) * g_lin ** (1 / 2.2)            # linear gain == display gain^(1/2.2)
    lift = vec3(p["lift"])
    if np.any(gain != 1):
        F *= gain
    if np.any(lift != 0):
        F *= (1 - lift)
        F += lift
    gam = vec3(p["gamma"])
    if np.any(gam != 1):
        np.maximum(F, 0, out=F)
        F[:] = np.power(F, 1.0 / gam)
    c = float(p["contrast"])
    if c != 1:
        pv = float(p["pivot"])
        F -= pv
        F *= c
        F += pv
    sh, hi = vec3(p["shadows"]), vec3(p["highlights"])
    if np.any(sh != 0) or np.any(hi != 0):
        L = np.clip(luma(F), 0, 1)[..., None]
        F += sh * (1 - L) ** 2 + hi * L * L
    s = float(p["saturation"])
    if s != 1:
        L = luma(F)[..., None]
        F -= L
        F *= s
        F += L
    np.maximum(F, 0, out=F)
    # global shadow lift: the darkest tones come up ~10% so silhouettes in the dark scenes keep readable form
    # on phone screens; mids/highlights barely move ((1-x)^6 falls off fast). Override per shot: "shadow_lift".
    a = float(p.get("shadow_lift", SHADOW_LIFT)) if hasattr(p, "get") else SHADOW_LIFT
    if a > 0:
        F += a * np.power(np.clip(1.0 - F, 0, 1), 6)
    # shadow stretch: brightens dark detail (zero at pure black, so no milky blacks), fades out by the mids
    st = float(p.get("shadow_stretch", SHADOW_STRETCH)) if hasattr(p, "get") else SHADOW_STRETCH
    if st > 0:
        G = np.clip(F, 0, 1)
        F += st * G * np.power(1.0 - G, 4)
    m = F > 0.86
    if m.any():
        F[m] = 0.86 + 0.14 * np.tanh((F[m] - 0.86) / 0.14)
    return F


def bloom_layer(F540, p, flash=0.0):
    """Bloom + halation glow (small res, float RGB) or None."""
    amt = float(p["bloom"]) + 1.4 * flash
    hal = float(p["halation"])
    if amt <= 0.001 and hal <= 0.001:
        return None
    h, w = F540.shape[:2]
    small = cv2.resize(F540, (w // 4, h // 4), interpolation=cv2.INTER_AREA)
    L = luma(small)
    thr = float(p["bloom_threshold"]) * (1 - 0.45 * flash)
    # display-referred input: only the top of the range blooms (squared knee), so bright skies
    # keep their contrast while sun discs, glints and flames glow
    k = np.clip((L - thr) / max(0.05, 1.0 - thr), 0, 1)
    k *= k
    bright = small * k[..., None]
    r = float(p["bloom_radius"])
    b1 = cv2.GaussianBlur(bright, (0, 0), 2.2 * r)
    s2 = cv2.resize(bright, (w // 8, h // 8), interpolation=cv2.INTER_AREA)
    b2 = cv2.resize(cv2.GaussianBlur(s2, (0, 0), 4.5 * r), (w // 4, h // 4), interpolation=cv2.INTER_LINEAR)
    glow = (0.5 * b1 + 0.5 * b2) * (amt * 1.6)
    if hal > 0.001:
        hl = cv2.GaussianBlur(bright, (0, 0), 1.0) * np.array([1.0, 0.42, 0.18], np.float32)
        glow += hl * hal
    return glow


# ----------------------------------------------------------------------------------------------
# frame sources
# ----------------------------------------------------------------------------------------------
class Source:
    def __init__(self, shot, quality="auto", rw=540, rh=960):
        self.shot = shot
        self.id = shot["id"]
        self.rw, self.rh = rw, rh
        base = os.path.join(WORK, "frames", self.id)
        qs = QUALITIES if quality == "auto" else (quality,)
        self.avail = {}
        posts = []
        for q in qs:
            d = os.path.join(base, q)
            if not os.path.isdir(d):
                continue
            fr = sorted(int(n[:-4]) for n in os.listdir(d) if n.endswith(".png") and n[:-4].isdigit())
            if fr:
                self.avail[q] = fr
            pj = os.path.join(d, "post.json")
            if os.path.exists(pj):
                posts.append((os.path.getmtime(pj), pj))
        self.post = {}
        if posts:
            try:
                self.post = json.load(open(max(posts)[1]))
            except Exception:
                self.post = {}
        self.sets = {q: set(v) for q, v in self.avail.items()}
        self.placeholder = not self.avail
        self.cover = None
        if self.avail:
            N = shot["render_frames"]

            def maxgap(fr):
                pts = [0] + [f for f in fr if f <= N] + [N + 1]
                return max(b - a for a, b in zip(pts, pts[1:]))
            self.cover = min(self.avail, key=lambda q: (maxgap(self.avail[q]), QUALITIES.index(q)))
        self.params = resolve_post(self.post)

    def describe(self):
        if self.placeholder:
            return "placeholder"
        return ", ".join("%s:%d" % (q, len(v)) for q, v in self.avail.items()) + " (cover %s)" % self.cover

    def plan(self, f):
        """-> [(quality, frame, weight)]"""
        for q in QUALITIES:
            if q in self.sets and f in self.sets[q]:
                return [(q, f, 1.0)]
        fr = self.avail[self.cover]
        i = bisect.bisect_left(fr, f)
        if i == 0:
            return [(self.cover, fr[0], 1.0)]
        if i >= len(fr):
            return [(self.cover, fr[-1], 1.0)]
        a, b = fr[i - 1], fr[i]
        w = (f - a) / float(b - a)
        return [(self.cover, a, 1 - w), (self.cover, b, w)]

    def path(self, q, f):
        return os.path.join(WORK, "frames", self.id, q, "%04d.png" % f)


_raw_cache = OrderedDict()


def load_png(path, rw, rh):
    v = _raw_cache.get(path)
    if v is not None:
        _raw_cache.move_to_end(path)
        return v
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if im is None:
        raise IOError("cannot read " + path)
    scale = 65535.0 if im.dtype == np.uint16 else 255.0
    if im.ndim == 2:
        im = np.repeat(im[..., None], 3, axis=2)
    im = im[..., :3][..., ::-1].astype(np.float32) * np.float32(1.0 / scale)
    if im.shape[1] != rw or im.shape[0] != rh:
        interp = cv2.INTER_CUBIC if im.shape[1] < rw else cv2.INTER_AREA
        im = np.clip(cv2.resize(im, (rw, rh), interpolation=interp), 0, 1)
    _raw_cache[path] = im
    if len(_raw_cache) > 6:
        _raw_cache.popitem(last=False)
    return im


# ----------------------------------------------------------------------------------------------
# placeholder cards
# ----------------------------------------------------------------------------------------------
PALETTES = [  # (keywords, top rgb, bottom rgb, glow rgb)
    (("space", "earth seen"), (0.02, 0.03, 0.07), (0.05, 0.08, 0.16), (0.5, 0.6, 0.9)),
    (("night", "moonlight", "torch", "fire", "darkness", "dark hills"), (0.05, 0.07, 0.14), (0.12, 0.12, 0.18), (0.55, 0.62, 0.85)),
    (("storm", "menace", "terror", "dust storm", "lions", "bulls", "hunted", "dusk"), (0.22, 0.12, 0.08), (0.10, 0.06, 0.05), (0.8, 0.45, 0.25)),
    (("gold", "glory", "sunrise", "dawn", "lamp", "warm", "holy", "triumph", "jubilant"), (0.85, 0.66, 0.38), (0.45, 0.30, 0.16), (1.0, 0.85, 0.55)),
    (("sea", "water"), (0.30, 0.50, 0.58), (0.10, 0.20, 0.26), (0.7, 0.9, 1.0)),
    (("harsh white sun", "dry", "potsherd", "desolate", "vast"), (0.78, 0.74, 0.66), (0.50, 0.42, 0.33), (1, 1, 0.95)),
]
DEFAULT_PAL = ((0.50, 0.45, 0.40), (0.25, 0.21, 0.18), (0.95, 0.85, 0.7))


def palette_for(shot):
    txt = (shot.get("mood", "") + " " + shot.get("visual", "") + " " + shot.get("title", "")).lower()
    best, score = DEFAULT_PAL, 0
    for kws, a, b, c in PALETTES:
        s = sum(txt.count(k) for k in kws)
        if s > score:
            best, score = (a, b, c), s
    return best


_ph_cache = {}


def placeholder_card(shot, rw, rh):
    if shot["id"] in _ph_cache:
        return _ph_cache[shot["id"]]
    top, bot, glow = palette_for(shot)
    y = np.linspace(0, 1, rh, dtype=np.float32)[:, None, None]
    F = np.asarray(top, np.float32) * (1 - y) + np.asarray(bot, np.float32) * y
    F = np.broadcast_to(F, (rh, rw, 3)).copy()
    yy, xx = np.mgrid[0:rh, 0:rw].astype(np.float32)
    r = np.sqrt(((xx - rw * 0.5) / (rw * 0.55)) ** 2 + ((yy - rh * 0.40) / (rh * 0.35)) ** 2)
    F += (np.exp(-r * r * 1.6) * 0.22)[..., None] * np.asarray(glow, np.float32)
    img = Image.fromarray((np.clip(F, 0, 1) * 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    lum = float(np.mean(np.asarray(top) * LUMA.sum()))
    ink = (40, 32, 24) if lum > 0.55 else (235, 228, 215)
    f1 = CAP.get_font("caps", 26)
    f2 = CAP.get_font("body", 30)
    f3 = CAP.get_font("alt", 17)
    d.text((rw / 2, 70), "%s  ·  %s" % (shot["id"].upper(), shot.get("block", "")), font=f1, fill=ink, anchor="ms")
    d.text((rw / 2, 112), shot.get("title", ""), font=f2, fill=ink, anchor="ms")
    words, lines, cur = shot.get("visual", "").split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if f3.getlength(t) > rw - 80:
            lines.append(cur)
            cur = w_
        else:
            cur = t
    if cur:
        lines.append(cur)
    for i, ln in enumerate(lines[:12]):
        d.text((40, 150 + i * 22), ln, font=f3, fill=ink)
    d.text((rw / 2, 150 + min(12, len(lines)) * 22 + 30), "[ placeholder — not rendered yet ]  " + shot.get("mood", ""),
           font=CAP.get_font("italic", 18), fill=ink, anchor="ms")
    card = np.asarray(img, np.float32) / 255.0
    _ph_cache[shot["id"]] = (card, ink)
    return _ph_cache[shot["id"]]


def placeholder_frame(shot, f, rw, rh):
    card, ink = placeholder_card(shot, rw, rh)
    F = card.copy()
    # timing bar + frame counter (top area, away from captions)
    u = (f - 1) / max(1, shot["nframes"] - 1)
    col = np.asarray(ink, np.float32) / 255.0
    y0 = 24
    F[y0:y0 + 2, 30:rw - 30] = F[y0:y0 + 2, 30:rw - 30] * 0.6 + col * 0.4
    x1 = 30 + int((rw - 60) * min(1.0, u))
    F[y0 - 2:y0 + 4, 30:x1] = col
    patch = Image.new("L", (160, 22), 0)
    ImageDraw.Draw(patch).text((0, 0), "f %d / %d%s" % (f, shot["nframes"], " tail" if f > shot["nframes"] else ""),
                                font=CAP.get_font("alt", 16), fill=255)
    a = (np.asarray(patch, np.float32) / 255.0)[..., None]
    F[32:54, 30:190] = F[32:54, 30:190] * (1 - a) + col * a
    return F


# ----------------------------------------------------------------------------------------------
# film
# ----------------------------------------------------------------------------------------------
class Film:
    def __init__(self, quality="auto", captions=True, burnin=False, timeline=None, phrases=None):
        self.tl = timeline or json.load(open(os.path.join(ROOT, "timeline.json")))
        self.fps = self.tl["fps"]
        self.rw, self.rh = self.tl.get("render_resolution", [540, 960])
        self.W, self.H = self.tl.get("final_resolution", [720, 1280])
        self.shots = self.tl["shots"]
        self.N = self.tl["total_frames"]
        self.sources = [Source(s, quality, self.rw, self.rh) for s in self.shots]
        self.shot_of = np.zeros(self.N, np.int32)
        for k, s in enumerate(self.shots):
            self.shot_of[s["start_frame"]:s["start_frame"] + s["nframes"]] = k
        self.flash = np.zeros(self.N, np.float32)
        self.black = np.zeros(self.N, np.float32)
        for k, s in enumerate(self.shots):
            c = s["start_frame"]
            if k == 0 or c <= 0:
                continue                      # never a transition at the very start
            tr = s.get("transition_in", "cut")
            if tr == "flash":
                for i in range(-FLASH_PRE, FLASH_POST + 1):
                    g = c + i
                    if 0 < g < self.N:
                        v = math.exp(-((i + 0.3) / 1.6) ** 2) if i < 0 else math.exp(-i / 3.2)
                        self.flash[g] = max(self.flash[g], v)
            elif tr == "fade_black":
                for i in range(FB_OUT):
                    g = c - FB_OUT + i
                    if g > 0:
                        x = (i + 1) / FB_OUT
                        self.black[g] = max(self.black[g], x * x * (3 - 2 * x))
                for i in range(FB_IN):
                    g = c + i
                    x = 1 - i / FB_IN
                    self.black[g] = max(self.black[g], x * x * (3 - 2 * x))
        # end of film: fade the end card + picture out
        ff = int(CAP.ENDCARD["final_fade"] * self.fps)
        for i in range(ff):
            g = self.N - ff + i
            x = (i + 1) / ff
            self.black[g] = max(self.black[g], x * x * (3 - 2 * x) * 0.97)
        self.vig = self._vignette()
        self._vig_cache = {}
        self.captions = None
        if captions:
            if phrases is None:
                phrases = load_phrases()
            ph = phrases["phrases"] if isinstance(phrases, dict) else phrases
            s0 = self.shots[0]
            title_end = min((s0["start_frame"] + s0["nframes"]) / self.fps - 0.15,
                            ph[0]["start"] - 0.5 if ph else 99)
            self.captions = CAP.CaptionTrack(ph, self.N / self.fps, title_end=title_end, hints=self.hints_at)
            self.captions.fps = self.fps
            self.captions.ref_fn = lambda g: self.frame(g, overlays=False)
            last = self.sources[-1].post.get("endcard", {}) if self.sources else {}
            self.captions.endcard_ink = last.get("ink", "auto") if isinstance(last, dict) else "auto"
        self.burnin = burnin
        self._graded = OrderedDict()

    def _vignette(self):
        yy, xx = np.mgrid[0:self.H, 0:self.W].astype(np.float32)
        r = np.sqrt(((xx - self.W / 2) / (self.W * 0.62)) ** 2 + ((yy - self.H * 0.47) / (self.H * 0.60)) ** 2)
        v = np.clip((r - 0.45) / 0.75, 0, 1)
        return (v * v * (3 - 2 * v)).astype(np.float32)

    def _vig_factor(self, v):
        v = round(float(v), 3)
        f = self._vig_cache.get(v)
        if f is None:
            if len(self._vig_cache) > 8:
                self._vig_cache.clear()
            f = self._vig_cache[v] = (1 - np.float32(v) * self.vig)[..., None].astype(np.float32)
        return f

    def hints_at(self, t):
        g = min(self.N - 1, max(0, int(round(t * self.fps))))
        return self.sources[self.shot_of[g]].post

    def params(self, k, f):
        a, b = self.sources[k].params
        if a is b or a == b:
            return a
        n = self.shots[k]["nframes"]
        return lerp_params(a, b, min(1.0, max(0.0, (f - 1) / max(1, n - 1))))

    def graded(self, k, f):
        key = (k, f)
        v = self._graded.get(key)
        if v is not None:
            return v
        src = self.sources[k]
        shot = self.shots[k]
        if src.placeholder:
            F = placeholder_frame(shot, f, self.rw, self.rh)
        else:
            plan = src.plan(f)
            if len(plan) == 1:
                F = load_png(src.path(plan[0][0], plan[0][1]), self.rw, self.rh).copy()
            else:
                (qa, fa, wa), (qb, fb, wb) = plan
                F = load_png(src.path(qa, fa), self.rw, self.rh) * np.float32(wa) + \
                    load_png(src.path(qb, fb), self.rw, self.rh) * np.float32(wb)
        F = grade(F, self.params(k, f))
        self._graded[key] = F
        if len(self._graded) > 4:
            self._graded.popitem(last=False)
        return F

    def frame(self, g, overlays=True):
        """Global frame index (0-based) -> float32 (H,W,3) display RGB."""
        k = int(self.shot_of[g])
        s = self.shots[k]
        f = g - s["start_frame"] + 1
        F = self.graded(k, f)
        p = self.params(k, f)
        if k > 0 and s.get("transition_in") == "dissolve" and f <= DISSOLVE:
            prev = self.shots[k - 1]
            pf = prev["nframes"] + f
            # tail frames that were not rendered fall back to holds / interpolation inside Source.plan
            w = (f - 0.5) / DISSOLVE
            w = w * w * (3 - 2 * w)
            P = self.graded(k - 1, pf)
            F = P * np.float32(1 - w) + F * np.float32(w)
            p = lerp_params(self.params(k - 1, pf), p, w)
        flash, black = float(self.flash[g]), float(self.black[g])
        glow = bloom_layer(F, p, flash)
        U = cv2.resize(F, (self.W, self.H), interpolation=cv2.INTER_LANCZOS4)
        sh = float(p.get("sharpen", 0.35))
        if sh > 0:                                   # unsharp mask: U + sh*(U - blur(U))
            B = cv2.GaussianBlur(U, (0, 0), 1.0)
            U *= np.float32(1 + sh)
            B *= np.float32(sh)
            U -= B
        np.clip(U, 0, 1, out=U)
        if glow is not None:                         # screen blend: U + G - U*G
            G = cv2.resize(glow, (self.W, self.H), interpolation=cv2.INTER_LINEAR)
            np.clip(G, 0, 1, out=G)
            UG = U * G
            U += G
            U -= UG
        v = float(p.get("vignette", 0))
        if v > 0:
            U *= self._vig_factor(v)
        if flash > 0:
            U *= np.float32(1 - 0.9 * flash)
            U += np.float32(0.9 * flash)
        gr = float(p.get("grain", 0))
        if gr > 0:
            rng = np.random.default_rng(g)
            n = rng.standard_normal((self.H // 2, self.W // 2), dtype=np.float32)
            n = cv2.resize(n, (self.W, self.H), interpolation=cv2.INTER_LINEAR)   # soft, luma-only grain
            U += n[..., None] * np.float32(gr)
        if self.captions is not None and overlays:
            self.captions.render(U, g / self.fps)
        if black > 0:
            U *= np.float32(1 - black)
        if self.burnin:
            self._burnin(U, g, k, f)
        return np.clip(U, 0, 1, out=U)

    def _burnin(self, U, g, k, f):
        src = self.sources[k]
        tag = "placeholder" if src.placeholder else "+".join(sorted({q for q, _, _ in src.plan(f)}))
        txt = "%s f%d  g%d  %05.2fs  %s" % (self.shots[k]["id"], f, g, g / self.fps, tag)
        im = Image.new("L", (330, 20), 0)
        ImageDraw.Draw(im).text((2, 1), txt, font=CAP.get_font("alt", 15), fill=255)
        a = (np.asarray(im, np.float32) / 255.0)[..., None]
        R = U[8:28, 8:338]
        R *= (1 - 0.5 * np.clip(a * 4, 0, 1))
        R += a * 0.95


# ----------------------------------------------------------------------------------------------
# output conversion
# ----------------------------------------------------------------------------------------------
def to_yuv420(F, bits=10, dither=0.0, seed=0):
    """float RGB (display, 0..1) -> planar BT.709 limited-range YUV 4:2:0 bytes."""
    YUV = cv2.transform(F, _YUV_M)
    Y = YUV[..., 0]
    C2 = YUV[0::2, 0::2, 1:] + YUV[1::2, 0::2, 1:]          # 2x2 box average (centre-sited)
    C2 += YUV[0::2, 1::2, 1:]
    C2 += YUV[1::2, 1::2, 1:]
    C2 *= np.float32(0.25)
    Cb, Cr = C2[..., 0], C2[..., 1]
    if bits == 10:
        ys, yo, cs, co, top, dt = 876.0, 64.0, 896.0, 512.0, 1023, np.uint16
    else:
        ys, yo, cs, co, top, dt = 219.0, 16.0, 224.0, 128.0, 255, np.uint8
    Yq = Y * np.float32(ys) + np.float32(yo)
    Bq = Cb * np.float32(cs) + np.float32(co)
    Rq = Cr * np.float32(cs) + np.float32(co)
    if dither > 0:
        rng = np.random.default_rng(seed)
        for P in (Yq, Bq, Rq):     # TPDF dither, +-dither LSB
            P += (rng.random(P.shape, dtype=np.float32) - rng.random(P.shape, dtype=np.float32)) * np.float32(dither)
    out = []
    for P in (Yq, Bq, Rq):
        np.rint(P, out=P)
        np.clip(P, 0, top, out=P)
        out.append(P.astype(dt).tobytes())
    return b"".join(out)


# ----------------------------------------------------------------------------------------------
# multiprocessing
# ----------------------------------------------------------------------------------------------
_film = None
_job = {}


def _init(opts):
    global _film, _job
    cv2.setNumThreads(1)
    _job = opts
    _film = Film(quality=opts["quality"], captions=opts["captions"], burnin=opts["burnin"])


def _work(rng):
    g0, g1 = rng
    out = []
    for g in range(g0, g1):
        F = _film.frame(g)
        if _job["fmt"] == "rgb24":
            out.append((F * 255 + 0.5).astype(np.uint8).tobytes())
        else:
            out.append(to_yuv420(F, _job["bits"], _job["dither"], seed=g))
    return b"".join(out)


def chunks(film, frames, size=12):
    """Split sorted global frames into contiguous chunks that do not cross shots."""
    out = []
    cur = []
    for g in frames:
        if cur and (g != cur[-1] + 1 or len(cur) >= size or film_shot(film, g) != film_shot(film, cur[0])):
            out.append((cur[0], cur[-1] + 1))
            cur = []
        cur.append(g)
    if cur:
        out.append((cur[0], cur[-1] + 1))
    return out


def film_shot(film, g):
    return int(film.shot_of[g])


def load_phrases():
    for name in ("phrases.json",):
        p = os.path.join(WORK, "audio", name)
        if os.path.exists(p):
            return json.load(open(p))
    return {"phrases": []}


def find_audio():
    for name in ("mix.wav", "narration.wav"):
        p = os.path.join(WORK, "audio", name)
        if os.path.exists(p):
            return p
    return None


def parse_frames(spec, film):
    if not spec:
        return list(range(film.N))
    out = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-")
            out += list(range(int(a), min(film.N - 1, int(b)) + 1))
        else:
            out.append(int(part))
    return sorted(set(g for g in out if 0 <= g < film.N))


def run(args):
    t_start = time.time()
    film = Film(quality=args.quality, captions=not args.no_captions, burnin=args.burnin)
    for s, src in zip(film.shots, film.sources):
        if args.verbose or not src.placeholder:
            print("  %-5s %s" % (s["id"], src.describe()))
    if args.shots:
        ids = args.shots.split(",")
        frames = []
        for s in film.shots:
            if s["id"] in ids:
                frames += list(range(s["start_frame"], s["start_frame"] + s["nframes"]))
        frames = sorted(set(frames))
    elif args.stills:
        frames = parse_frames(args.stills, film)
    else:
        frames = parse_frames(args.frames, film)
    W, H, fps = film.W, film.H, film.fps
    opts = {"quality": args.quality, "captions": not args.no_captions, "burnin": args.burnin,
            "fmt": "yuv", "bits": 10, "dither": 0.0}

    if args.stills:
        os.makedirs(args.stills_dir, exist_ok=True)
        for g in frames:
            F = film.frame(g)
            p = os.path.join(args.stills_dir, "g%05d.png" % g)
            Image.fromarray((F * 255 + 0.5).astype(np.uint8)).save(p)
            print(p)
        return

    t0 = frames[0] / fps
    dur = len(frames) / fps
    if args.direct:
        opts.update(bits=8, dither=0.6)
        audio = None if args.no_audio else (args.audio or find_audio())
        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
               "-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", "%dx%d" % (W, H), "-r", str(fps), "-i", "-"]
        if audio:
            cmd += ["-ss", "%.3f" % t0, "-t", "%.3f" % dur, "-i", audio]
        cmd += ["-map", "0:v"] + (["-map", "1:a", "-c:a", "aac", "-b:a", "96k"] if audio else [])
        cmd += ["-c:v", "libx264", "-preset", args.preset or "fast", "-crf", str(args.crf or 21),
                "-pix_fmt", "yuv420p", "-profile:v", "high", "-movflags", "+faststart",
                "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
                "-t", "%.3f" % dur, args.direct]
        out_path = args.direct
    else:
        out_path = args.mezz or os.path.join(WORK, "comp", "mezz.mp4")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
               "-f", "rawvideo", "-pix_fmt", "yuv420p10le", "-s", "%dx%d" % (W, H), "-r", str(fps), "-i", "-",
               "-c:v", "libx264", "-preset", args.mezz_preset, "-crf", str(args.mezz_crf),
               "-pix_fmt", "yuv420p10le", "-x264-params", "keyint=48:min-keyint=1",
               "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
               out_path]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    jobs = chunks(film, frames, args.chunk)
    done = 0
    tl = time.time()
    workers = max(1, args.workers)
    print("compositing %d frames (%.1fs from %.2fs) with %d workers -> %s" % (len(frames), dur, t0, workers, out_path))
    if workers == 1:
        _init(opts)
        it = map(_work, jobs)
        pool = None
    else:
        ctx = mp.get_context("fork")
        pool = ctx.Pool(workers, initializer=_init, initargs=(opts,))
        it = pool.imap(_work, jobs)
    try:
        for (g0, g1), data in zip(jobs, it):
            ff.stdin.write(data)
            done += g1 - g0
            if time.time() - tl > 10 or done == len(frames):
                el = time.time() - t_start
                print("  %5d/%d frames  %.1f fps  elapsed %.0fs  eta %.0fs" %
                      (done, len(frames), done / el, el, (len(frames) - done) / max(1e-6, done / el)), flush=True)
                tl = time.time()
    finally:
        if pool:
            pool.close()
            pool.join()
        ff.stdin.close()
        ff.wait()
    el = time.time() - t_start
    print("composite done: %d frames in %.1fs (%.2f fps) -> %s (%.1f MB)" %
          (len(frames), el, len(frames) / el, out_path, os.path.getsize(out_path) / 1e6))
    if ff.returncode != 0:
        raise SystemExit("ffmpeg failed")
    if not args.direct and not args.no_encode:
        import encode
        ea = ["--mezz", out_path]
        if args.out:
            ea += ["--out", args.out]
        if args.audio:
            ea += ["--audio", args.audio]
        if frames[0] > 0:
            ea += ["--audio-offset", "%.3f" % t0]
        encode.main(ea + (args.encode_args.split() if args.encode_args else []))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quality", default="auto", choices=("auto",) + QUALITIES)
    ap.add_argument("--frames", help="global 0-based frames, e.g. 0-479 or 0-100,2000-2100")
    ap.add_argument("--shots", help="comma list of shot ids")
    ap.add_argument("--stills", help="global frames to write as PNG (no video)")
    ap.add_argument("--stills-dir", default=os.path.join(WORK, "comp", "stills"))
    ap.add_argument("--mezz", help="mezzanine path (default $WORK/comp/mezz.mp4)")
    ap.add_argument("--mezz-crf", type=int, default=8)
    ap.add_argument("--mezz-preset", default="veryfast")
    ap.add_argument("--direct", help="single-pass preview mp4 instead of mezzanine")
    ap.add_argument("--crf", type=int)
    ap.add_argument("--preset")
    ap.add_argument("--out", help="final mp4 (passed to encode.py)")
    ap.add_argument("--audio")
    ap.add_argument("--no-audio", action="store_true")
    ap.add_argument("--no-encode", action="store_true")
    ap.add_argument("--encode-args", help="extra args for encode.py, quoted")
    ap.add_argument("--no-captions", action="store_true")
    ap.add_argument("--burnin", action="store_true", help="debug overlay: shot/frame/source")
    ap.add_argument("--workers", type=int, default=min(4, os.cpu_count() or 1))
    ap.add_argument("--chunk", type=int, default=12)
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)
    run(args)


if __name__ == "__main__":
    main()
