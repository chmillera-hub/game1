"""Psalm 22 - caption / title / end-card renderer for the compositor.

Everything is drawn at the delivery resolution (720x1280) onto a float32 RGB frame in display space
(0..1, sRGB/BT.709 transfer).  Text masks are rendered once with PIL (raqm layout: kerning + ligatures)
and cached; per frame only small regions around the text are touched (fade, rise, effects, halo).

Typography (SIL OFL fonts in comp/fonts, downloaded on demand by ensure_fonts()):
  captions  Cormorant Garamond SemiBold   (variable font, wght 600)
  title     Cinzel SemiBold               "PSALM 22"  + Cormorant Garamond Italic subtitle
  emphasis  Cinzel                        "He has done it!"
  end card  Cinzel + Cormorant Garamond Italic

Safe zone (TikTok / Reels / Shorts): nothing below 82% of the height, nothing in the right 12%.
Captions are centred at x = 0.48 W, block centre around y = 0.68 H (post.json caption.y may move it
within 0.60..0.74), max 2 balanced lines, auto font-size fit.

Meaning-driven effects (subtle, readability first - most of them play on the exit):
  drift     "...why have you forsaken me?"   words drift apart as the line fades (loneliness)
  holy      "...enthroned as the Holy One;"   warm gold-white ink with a softly breathing gold glow
  ripple    "I am poured out like water,"    "like water" undulates; the line dissolves in ripples
  melt      "it has melted within me."       "melted" softens, then the line sags, blurs and drips away
  crumble   "...the dust of death."          letters crumble into sand grains that fall and blow away
  triumph   "He has done it!"                larger Cinzel, gold glow, slow scale-in, one light sweep
"""
import json, math, os, urllib.request
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFont

try:
    import cv2
    cv2.setNumThreads(1)
except Exception:  # pragma: no cover - cv2 is installed in /opt/venv; fallback keeps things importable
    cv2 = None

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "fonts")
FONT_SRC = "https://raw.githubusercontent.com/google/fonts/main/ofl/"
FONT_FILES = {   # local name -> path in google/fonts
    "CormorantGaramond-VF.ttf": "cormorantgaramond/CormorantGaramond%5Bwght%5D.ttf",
    "CormorantGaramond-Italic-VF.ttf": "cormorantgaramond/CormorantGaramond-Italic%5Bwght%5D.ttf",
    "OFL-CormorantGaramond.txt": "cormorantgaramond/OFL.txt",
    "EBGaramond-VF.ttf": "ebgaramond/EBGaramond%5Bwght%5D.ttf",
    "EBGaramond-Italic-VF.ttf": "ebgaramond/EBGaramond-Italic%5Bwght%5D.ttf",
    "OFL-EBGaramond.txt": "ebgaramond/OFL.txt",
    "Cinzel-VF.ttf": "cinzel/Cinzel%5Bwght%5D.ttf",
    "OFL-Cinzel.txt": "cinzel/OFL.txt",
}
# role -> (file, weight)
ROLES = {
    "body": ("CormorantGaramond-VF.ttf", 600),
    "italic": ("CormorantGaramond-Italic-VF.ttf", 600),
    "italic_light": ("CormorantGaramond-Italic-VF.ttf", 500),
    "title": ("Cinzel-VF.ttf", 600),
    "caps": ("Cinzel-VF.ttf", 500),
    "alt": ("EBGaramond-VF.ttf", 500),
}

W, H = 720, 1280
FPS = 24

# --- caption layout / timing constants -----------------------------------------------------------
CAP_CX = 0.48            # caption centre x (fraction of W): keeps clear of the right-side UI column
CAP_MAXW = 0.75          # max line width (fraction of W) -> 540 px
CAP_Y = 0.68             # block centre (fraction of H)
CAP_Y_RANGE = (0.60, 0.74)
CAP_SIZE = 46            # preferred size (px at 720 wide); shrinks to CAP_MIN_SIZE for long phrases
CAP_MIN_SIZE = 36
CAP_LINE = 1.14          # line height (x size)
LEAD = 0.12              # caption appears this long before the voice
IN_DUR = 0.28
OUT_DUR = 0.24
HOLD_AFTER = 0.55        # linger after the phrase ends when the next one is far away
RISE = 12.0              # px rise during fade-in
INK = (1.0, 0.985, 0.955)            # warm white
DARK_INK = (0.13, 0.095, 0.06)       # deep umber (title/end card over very bright skies)
INK_DARK_ABOVE = 0.66                # title/end card switch to dark ink above this background luma
HALO_DARK = (0.035, 0.028, 0.022)
GOLD = (1.0, 0.80, 0.46)
SAND = (0.86, 0.77, 0.63)

# substring -> effect (exact NIV text; first match wins)
EFFECTS = [
    ("why have you forsaken me?", "drift"),
    ("enthroned as the Holy One", "holy"),
    ("poured out like water", "ripple"),
    ("melted within me", "melt"),
    ("dust of death", "crumble"),
    ("He has done it!", "triumph"),
]
EFFECT_TARGET = {"ripple": "like water", "melt": "melted", "holy": "Holy One"}
EXIT_DUR = {"drift": 0.7, "ripple": 0.6, "melt": 1.1, "crumble": 1.5}
EFFECT_PAD = {"drift": 72, "ripple": 44, "melt": 56, "crumble": 84, "triumph": 48}   # room for motion + halo

TITLE = {"text": "PSALM 22", "sub": "A Psalm of David", "y": 0.315, "hold": 2.9, "fade": 1.1}
ENDCARD = {"line1": "PSALM 22  ·  NIV", "line2": "It is finished.", "line3": "— John 19:30",
           "y": 0.44, "fade_in": 1.1, "lead_after_last": 2.6, "final_fade": 1.1}


# ================================================================================================
# fonts
# ================================================================================================
def ensure_fonts(verbose=False):
    os.makedirs(FONT_DIR, exist_ok=True)
    for name, src in FONT_FILES.items():
        p = os.path.join(FONT_DIR, name)
        if os.path.exists(p) and os.path.getsize(p) > 0:
            continue
        if verbose:
            print("downloading font", name)
        urllib.request.urlretrieve(FONT_SRC + src, p)


@lru_cache(maxsize=64)
def get_font(role, size):
    fname, weight = ROLES[role]
    path = os.path.join(FONT_DIR, fname)
    if not os.path.exists(path):
        ensure_fonts()
    f = ImageFont.truetype(path, int(round(size)))
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


# ================================================================================================
# small math helpers
# ================================================================================================
def clamp01(x):
    return max(0.0, min(1.0, x))


def smoothstep(a, b, x):
    t = clamp01((x - a) / (b - a)) if b != a else float(x >= b)
    return t * t * (3 - 2 * t)


def ease_out(t):
    t = clamp01(t)
    return 1 - (1 - t) ** 3


def ease_in(t):
    t = clamp01(t)
    return t * t


def blur(a, sigma):
    if sigma <= 0:
        return a
    if cv2 is not None:
        return cv2.GaussianBlur(a, (0, 0), sigma)
    from scipy.ndimage import gaussian_filter
    return gaussian_filter(a, sigma)


def dilate(a, r):
    if r <= 0:
        return a
    if cv2 is not None:
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
        return cv2.dilate(a, k)
    from scipy.ndimage import grey_dilation
    return grey_dilation(a, size=(2 * r + 1, 2 * r + 1))


def remap(a, mx, my):
    if cv2 is not None:
        return cv2.remap(a, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    from scipy.ndimage import map_coordinates
    return map_coordinates(a, [my, mx], order=1, cval=0).astype(np.float32)


def affine(a, scale=1.0, dx=0.0, dy=0.0):
    """Scale about the centre + subpixel translate (mask arrays)."""
    if scale == 1.0 and dx == 0 and dy == 0:
        return a
    h, w = a.shape[:2]
    cx, cy = w / 2.0, h / 2.0
    m = np.float32([[scale, 0, cx - scale * cx + dx], [0, scale, cy - scale * cy + dy]])
    if cv2 is not None:
        return cv2.warpAffine(a, m, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    return remap(a, (xx - m[0, 2]) / scale, (yy - m[1, 2]) / scale)


_LUMA_M = np.array([[0.2126, 0.7152, 0.0722]], np.float32)


def luma(img):
    if cv2 is not None and img.dtype == np.float32 and img.ndim == 3:
        return cv2.transform(np.ascontiguousarray(img), _LUMA_M)
    return img[..., 0] * 0.2126 + img[..., 1] * 0.7152 + img[..., 2] * 0.0722


# ================================================================================================
# text layout
# ================================================================================================
def line_width(font, text, tracking=0.0):
    return font.getlength(text) + tracking * max(0, len(text) - 1)


WEAK_END = {"the", "a", "an", "of", "to", "from", "in", "and", "my", "your", "his", "their", "for",
            "on", "at", "by", "with", "is", "are", "be", "will", "who", "that", "“he"}


def _split_cost(w1, w2, prev_word, n1, n2, maxw):
    """Lower is better: balanced lines, break after punctuation, never end line 1 on a weak word."""
    cost = max(w1, w2)
    if prev_word and prev_word.rstrip("”\"")[-1:] in (",", ";", ":", "—", "!", "?"):
        cost -= 0.11 * maxw
    elif prev_word and prev_word.lower() in WEAK_END:
        cost += 0.14 * maxw
    if w1 > w2 + 0.22 * maxw:          # mild preference for bottom-heavy (pyramid) two-liners
        cost += 0.03 * maxw
    if n1 == 1 or n2 == 1:             # avoid orphans
        cost += 0.25 * maxw
    return cost


def wrap(text, font, maxw, max_lines=2, tracking=0.0, one_line_max=None):
    """Return list of lines (balanced), or None if it does not fit in max_lines."""
    words = text.split()
    full = line_width(font, text, tracking)
    if full <= (one_line_max or maxw):
        return [text]
    if max_lines < 2 or len(words) < 2:
        return None
    best = None
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        w1, w2 = line_width(font, a, tracking), line_width(font, b, tracking)
        if max(w1, w2) > maxw:
            continue
        c = _split_cost(w1, w2, words[i - 1], i, len(words) - i, maxw)
        if best is None or c < best[0]:
            best = (c, [a, b])
    return best[1] if best else None


class Block:
    """A rendered text block: float32 alpha mask + word boxes (mask coordinates)."""

    def __init__(self, mask, words, cx, cy, pad):
        self.A = mask
        self.h, self.w = mask.shape
        self.words = words      # [(word, x0, y0, x1, y1)]
        self.cx, self.cy = cx, cy   # frame position of the block centre
        self.pad = pad
        self._halo = None

    @property
    def x0(self):
        return self.cx - self.w / 2.0

    @property
    def y0(self):
        return self.cy - self.h / 2.0

    def target_weight(self, phrase, feather=10.0):
        """Soft weight map (h,w) covering the words of `phrase` (case-sensitive, in order)."""
        tw = phrase.split()
        names = [w[0].strip(",;:.!?“”—") for w in self.words]
        m = np.zeros((self.h, self.w), np.float32)
        for i in range(len(names) - len(tw) + 1):
            if [n for n in names[i:i + len(tw)]] == [t.strip(",;:.!?") for t in tw]:
                for _, x0, y0, x1, y1 in self.words[i:i + len(tw)]:
                    m[int(y0):int(y1), int(x0):int(x1)] = 1.0
        return np.clip(blur(m, feather / 2.0) * 1.6, 0, 1) if m.any() else m

    def halo(self):
        if self._halo is None:
            self._halo = halo_layers(self.A)
        return self._halo


def render_lines(lines, font, tracking=0.0, line_h=None, pad=28, cx=W / 2, cy=H / 2):
    """Render centred lines with PIL. lines: [str] or [(str, font, tracking, gap_before)]."""
    items = []
    for ln in lines:
        if isinstance(ln, tuple):
            items.append(ln)
        else:
            items.append((ln, font, tracking, None))
    widths, heights, asc = [], [], []
    for text, f, tr, gap in items:
        a, d = f.getmetrics()
        widths.append(line_width(f, text, tr) if text != "---" else 0)
        lh = gap if gap is not None else (line_h or f.size * CAP_LINE)
        heights.append(lh)
        asc.append(a)
    bw = int(math.ceil(max(widths))) + 2 * pad
    first_f = items[0][1]
    a0, d0 = first_f.getmetrics()
    total_h = sum(heights[1:]) + a0 + d0 * 0.6
    bh = int(math.ceil(total_h)) + 2 * pad
    img = Image.new("L", (bw, bh), 0)
    dr = ImageDraw.Draw(img)
    words = []
    y = pad + a0                      # baseline of first line
    for k, ((text, f, tr, gap), wdt) in enumerate(zip(items, widths)):
        if k > 0:
            y += heights[k]
        if text.startswith("---"):    # hairline rule: '---<width px>'
            rw = int(text[3:] or 120)
            yy = int(round(y - f.size * 0.32))
            dr.rectangle([bw / 2 - rw / 2, yy, bw / 2 + rw / 2, yy + 1], fill=200)
            continue
        x = bw / 2.0 - wdt / 2.0
        if tr == 0:
            dr.text((x, y), text, font=f, fill=255, anchor="ls")
        else:
            for i, ch in enumerate(text):
                xi = x + f.getlength(text[:i]) + tr * i
                dr.text((xi, y), ch, font=f, fill=255, anchor="ls")
        # word boxes (for targeted effects)
        pos = 0
        for wd in text.split(" "):
            i0 = text.index(wd, pos)
            x0 = x + f.getlength(text[:i0]) + tr * i0
            x1 = x + f.getlength(text[:i0 + len(wd)]) + tr * (i0 + len(wd))
            asc_, desc_ = f.getmetrics()
            words.append((wd, x0, y - asc_, x1, y + desc_ * 0.7))
            pos = i0 + len(wd)
    mask = np.asarray(img, np.float32) / 255.0
    return Block(mask, words, cx, cy, pad)


def halo_layers(A):
    """(drop shadow, wide soft halo) for a text mask."""
    sh = blur(A, 1.6)
    sh = np.roll(sh, 2, axis=0)
    g = blur(dilate(A, 3), 9.0)
    g = np.clip(g / 0.55, 0, 1)
    return sh, g


# ================================================================================================
# compositing a block onto the frame
# ================================================================================================
def composite(F, x0, y0, layers, op, ink_mode=0.0, halo_k=None, shadow_k=None, glow=None,
              halo=None, bg_luma=None):
    """Composite text onto F (H,W,3 float32 display RGB) in place.

    layers: [(alpha mask (h,w), ink rgb)] drawn in order, all sharing one halo (from the first mask
            unless `halo` is given as (shadow, wide)).
    ink_mode: 0 = light ink + dark halo, 1 = dark ink + light halo (may be fractional: crossfade).
    glow: optional (rgb, strength, mask) additive coloured glow (screen-blended).
    """
    if op <= 0.002:
        return
    h, w = layers[0][0].shape
    xi, yi = int(math.floor(x0)), int(math.floor(y0))
    fx0, fy0 = max(0, xi), max(0, yi)
    fx1, fy1 = min(F.shape[1], xi + w), min(F.shape[0], yi + h)
    if fx1 <= fx0 or fy1 <= fy0:
        return
    sx0, sy0 = fx0 - xi, fy0 - yi
    sl = (slice(sy0, sy0 + fy1 - fy0), slice(sx0, sx0 + fx1 - fx0))
    R = F[fy0:fy1, fx0:fx1]
    if halo is None:
        halo = halo_layers(layers[0][0])
    sh, wide = halo[0][sl], halo[1][sl]
    if bg_luma is None:
        bg_luma = float(luma(R[::4, ::4]).mean())
    if halo_k is None:
        halo_k = 0.20 + 0.36 * smoothstep(0.25, 0.85, bg_luma)
    if shadow_k is None:
        shadow_k = 0.50 + 0.25 * smoothstep(0.30, 0.85, bg_luma)
    light = 1.0 - ink_mode
    if light > 0:
        k1 = (halo_k * op * light) * wide
        k2 = (shadow_k * op * light) * sh
        dk = np.asarray(HALO_DARK, np.float32)
        R[:] = R * (1 - k1[..., None]) + dk * k1[..., None]
        R[:] = R * (1 - k2[..., None]) + dk * k2[..., None]
    if ink_mode > 0:
        k1 = (0.55 * op * ink_mode) * wide
        R[:] = R + (1 - R) * k1[..., None] * np.float32(0.9)
    if glow is not None:
        gcol, gk, gmask = glow
        g = (gk * op) * gmask[sl]
        R[:] = 1 - (1 - R) * (1 - g[..., None] * np.asarray(gcol, np.float32))
    for A, ink in layers:
        a = (op * A[sl])[..., None]
        if ink is None:
            ink = INK
        ink_arr = np.asarray(ink, np.float32)
        if ink_mode > 0 and ink is INK:
            ink_arr = ink_arr * (1 - ink_mode) + np.asarray(DARK_INK, np.float32) * ink_mode
        R[:] = R * (1 - a) + ink_arr * a


# ================================================================================================
# caption events
# ================================================================================================
class Event:
    def __init__(self, text, start, end, t_in, t_out, effect=None, exit_dur=OUT_DUR, index=0):
        self.text, self.start, self.end = text, start, end
        self.t_in, self.t_out = t_in, t_out          # visible interval (fade in starts / fade out ends)
        self.effect = effect
        self.exit_dur = exit_dur
        self.index = index


def effect_for(text):
    for sub, eff in EFFECTS:
        if sub in text:
            return eff
    return None


def build_events(phrases):
    ev = []
    for i, p in enumerate(phrases):
        eff = effect_for(p["text"])
        nxt = phrases[i + 1]["start"] - LEAD if i + 1 < len(phrases) else None
        t_in = p["start"] - LEAD
        want_exit = EXIT_DUR.get(eff, OUT_DUR)
        if eff == "triumph":
            t_out, exit_dur = None, 0.6          # handled by the outro schedule
        else:
            t_out = p["end"] + HOLD_AFTER + want_exit
            exit_dur = want_exit
            if nxt is not None and t_out > nxt + 0.02:
                # not enough room: be gone just as the next caption starts rising in (no muddle)
                t_out = nxt + 0.02
                exit_dur = min(want_exit, max(0.2, t_out - p["end"]))
        ev.append(Event(p["text"], p["start"], p["end"], t_in, t_out, eff, exit_dur, i))
    return ev


class CaptionTrack:
    """All text overlays of the film: title, phrase captions, emphasis line, end card."""

    def __init__(self, phrases, total_seconds, title_end=None, hints=None):
        ensure_fonts()
        self.phrases = phrases
        self.total = total_seconds
        self.events = build_events(phrases)
        self.last_end = phrases[-1]["end"] if phrases else total_seconds - 8
        self.title_end = title_end if title_end is not None else min(4.2, phrases[0]["start"] - 0.6 if phrases else 4.2)
        self.hints = hints or (lambda t: {})
        self._blocks = {}
        self._cache = {}
        self.endcard_ink = "auto"
        self.ref_fn = None        # optional: global frame -> picture without overlays (set by the Film)
        self.fps = FPS
        self.end_card_t = self.last_end + ENDCARD["lead_after_last"]
        if self.events and self.events[-1].effect == "triumph":
            self.events[-1].t_out = self.end_card_t + 0.5

    # ---------------------------------------------------------------- blocks
    def caption_block(self, ev, y_frac):
        key = ("cap", ev.index, round(y_frac, 3))
        b = self._blocks.get(key)
        if b is not None:
            return b
        if ev.effect == "triumph":
            f = get_font("title", 60)
            tr = 0.05 * 60
            lines = wrap(ev.text, f, W * CAP_MAXW, tracking=tr)
            b = render_lines(lines, f, tracking=tr, pad=EFFECT_PAD["triumph"], cx=W * CAP_CX, cy=H * y_frac)
        else:
            maxw = W * CAP_MAXW
            lines, f = None, None
            for size in range(CAP_SIZE, CAP_MIN_SIZE - 1, -2):
                f = get_font("body", size)
                lines = wrap(ev.text, f, maxw)
                if lines:
                    break
            if lines is None:          # still too long: hard 2-line split at the min size
                words = ev.text.split()
                h2 = len(words) // 2
                lines = [" ".join(words[:h2]), " ".join(words[h2:])]
            b = render_lines(lines, f, pad=EFFECT_PAD.get(ev.effect, 30), cx=W * CAP_CX, cy=H * y_frac)
            b.size = f.size
        self._blocks[key] = b
        return b

    def title_block(self, y_frac):
        key = ("title", y_frac)
        if key not in self._blocks:
            ft = get_font("title", 92)
            fs = get_font("italic", 40)
            lines = [(TITLE["text"], ft, 0.12 * 92, None),
                     ("---150", fs, 0, 46),
                     (TITLE["sub"], fs, 0.01 * 40, 54)]
            self._blocks[key] = render_lines(lines, ft, pad=44, cx=W / 2, cy=H * y_frac)
        return self._blocks[key]

    def end_block(self):
        key = ("end",)
        if key not in self._blocks:
            f1 = get_font("title", 50)
            f2 = get_font("italic", 50)
            f3 = get_font("body", 32)
            lines = [(ENDCARD["line1"], f1, 0.10 * 50, None),
                     ("---120", f2, 0, 54),
                     (ENDCARD["line2"], f2, 0, 74),
                     (ENDCARD["line3"], f3, 0.06 * 32, 50)]
            self._blocks[key] = render_lines(lines, f1, pad=44, cx=W / 2, cy=H * ENDCARD["y"])
        return self._blocks[key]

    # ---------------------------------------------------------------- per-frame
    def render(self, F, t):
        """Draw every overlay active at time t (seconds) onto F in place."""
        if t < self.title_end + 0.05:
            th = (self.hints(0.0) or {}).get("title", {})
            self._title(F, t, th if isinstance(th, dict) else {})
        for ev in self.events:
            if ev.t_in <= t <= (ev.t_out if ev.t_out is not None else 1e9):
                # hints of the shot where the phrase STARTS: a caption never jumps at a cut
                ch = (self.hints(ev.start) or {}).get("caption", {})
                ch = ch if isinstance(ch, dict) else {}
                if not ch.get("hide"):
                    self._caption(F, t, ev, ch)
        if t >= self.end_card_t - 0.01:
            self._endcard(F, t)

    def _ink_mode(self, F, block, x0, y0, mode, ref_g=None, key=None):
        """0 = light ink (dark halo), 1 = dark ink (light halo).

        'auto' decides ONCE per overlay from a reference frame (ref_g, rendered without overlays) so
        every worker agrees and the ink never flickers or lands in a muddy grey in-between."""
        if mode == "light":
            return 0.0
        if mode == "dark":
            return 1.0
        if ref_g is not None and self.ref_fn is not None:
            ck = ("ink", key)
            if ck not in self._cache:
                R = self.ref_fn(ref_g)
                self._cache[ck] = 1.0 if self._glyph_luma(R, block, x0, y0) > INK_DARK_ABOVE else 0.0
            return self._cache[ck]
        return smoothstep(INK_DARK_ABOVE - 0.03, INK_DARK_ABOVE + 0.03, self._glyph_luma(F, block, x0, y0))

    def _glyph_luma(self, F, block, x0, y0):
        h, w = block.A.shape
        ys, xs = max(0, int(y0)), max(0, int(x0))
        region = F[ys:ys + h:4, xs:xs + w:4]
        if region.size == 0:
            return 0.5
        # coverage-weighted luminance under the glyphs (dilated), not the whole box
        m = block.halo()[1][::4, ::4][:region.shape[0], :region.shape[1]]
        return float((luma(region) * m).sum() / max(1e-3, m.sum()))

    def _title(self, F, t, hint):
        y = float(hint.get("y", TITLE["y"]))
        b = self.title_block(y)
        hold, fade = TITLE["hold"], TITLE["fade"]
        end = min(self.title_end, hold + fade)
        op = 1.0 if t <= hold else 1.0 - smoothstep(hold, end, t)
        if op <= 0:
            return
        scale = 1.0 + 0.022 * smoothstep(0.0, end, t)       # slow push, crisp at frame 1
        dy = -6.0 * smoothstep(hold, end, t)
        A = affine(b.A, scale, 0, dy)
        mode = self._ink_mode(F, b, b.x0, b.y0, hint.get("ink", "auto"), ref_g=0, key="title")
        halo = halo_layers(A) if scale != 1.0 or dy else b.halo()
        gl = (GOLD, 0.35 * (1 - mode), blur(A, 6.0))
        composite(F, b.x0, b.y0, [(A, INK)], op, ink_mode=mode, halo=halo, glow=gl)

    def _endcard(self, F, t):
        b = self.end_block()
        t0 = self.end_card_t
        op = smoothstep(t0, t0 + ENDCARD["fade_in"], t)
        dy = 8.0 * (1 - ease_out((t - t0) / ENDCARD["fade_in"]))
        A = affine(b.A, 1.0, 0, dy)
        ref_g = int(round(min(self.total - ENDCARD["final_fade"] - 0.2, t0 + 1.5) * self.fps))
        mode = self._ink_mode(F, b, b.x0, b.y0, self.endcard_ink, ref_g=ref_g, key="end")
        composite(F, b.x0, b.y0, [(A, INK)], op, ink_mode=mode, halo=halo_layers(A),
                  glow=(GOLD, 0.28 * (1 - mode), blur(A, 6.0)))

    def _caption(self, F, t, ev, hint):
        y = float(hint.get("y", CAP_Y))
        y = min(CAP_Y_RANGE[1], max(CAP_Y_RANGE[0], y))
        if ev.effect == "triumph":
            y = min(y, 0.64)
        b = self.caption_block(ev, y)
        p_in = ease_out((t - ev.t_in) / IN_DUR)
        out_start = (ev.t_out - ev.exit_dur) if ev.t_out is not None else 1e9
        p_out = clamp01((t - out_start) / ev.exit_dur) if t > out_start else 0.0
        p_hold = clamp01((t - ev.start) / max(0.3, ev.end - ev.start))
        op = p_in
        dy = RISE * (1 - p_in)
        ink_mode = {"light": 0.0, "dark": 1.0}.get(hint.get("ink", "light"), 0.0)
        A = b.A
        layers = None
        glow = None
        eff = ev.effect
        halo_scale = float(hint.get("halo", 1.0))
        if eff is None or eff in ("holy",):
            op *= 1 - ease_in(p_out) if p_out > 0 else 1
            dy -= 4.0 * p_out
            if dy:
                A = affine(A, 1.0, 0, dy)
            if eff == "holy":
                breathe = 0.80 + 0.20 * math.sin(2 * math.pi * (t - ev.start) / 2.6)
                wgt = self._cached(("tw", ev.index, y), lambda: b.target_weight(EFFECT_TARGET["holy"]))
                gmask = blur(A, 7.0) * (0.55 + 0.45 * affine(wgt, 1, 0, dy))
                glow = (GOLD, 0.65 * breathe, gmask)
                layers = [(A, (1.0, 0.965, 0.87))]
        elif eff == "drift":
            op *= 1 - ease_in(p_out) * 0.98
            A = fx_drift(b, ease_out(p_out) if p_out > 0 else 0.0)
            A = affine(A, 1.0, 0, dy - 3.0 * p_out)
        elif eff == "ripple":
            op *= 1 - ease_in(p_out)
            wgt = self._cached(("tw", ev.index, y), lambda: b.target_weight(EFFECT_TARGET["ripple"], 14))
            A = fx_ripple(b.A, wgt, t - ev.start, p_hold, p_out)
            A = affine(A, 1.0, 0, dy)
        elif eff == "melt":
            wgt = self._cached(("tw", ev.index, y), lambda: b.target_weight(EFFECT_TARGET["melt"], 12))
            A = fx_melt(b, wgt, p_hold, p_out, self._cached(("noise", ev.index), lambda: _noise1d(b.w, 7)))
            op *= 1 - ease_in(p_out) ** 1.3 * 1.0
            A = affine(A, 1.0, 0, dy)
        elif eff == "crumble":
            st = self._cached(("crumble", ev.index, y), lambda: crumble_setup(b.A, seed=ev.index))
            if p_out > 0:
                stay, dust = fx_crumble(st, p_out)
                stay = affine(stay, 1.0, 0, dy)
                dust = affine(dust, 1.0, 0, dy)
                layers = [(stay, INK), (dust, SAND)]
                halo = halo_layers(stay)
                composite(F, b.x0, b.y0, layers, op * (1 - smoothstep(0.75, 1.0, p_out)),
                          ink_mode=ink_mode, halo=halo, halo_k=None)
                return
            A = affine(A, 1.0, 0, dy)
        elif eff == "triumph":
            p_tin = ease_out((t - ev.t_in) / 0.8)
            op = p_tin
            if ev.t_out is not None:
                op *= 1 - smoothstep(ev.t_out - 0.7, ev.t_out, t)
            scale = 0.94 + 0.06 * p_tin + 0.012 * smoothstep(ev.start, ev.start + 4.0, t)
            A = affine(b.A, scale, 0, 6 * (1 - p_tin))
            # one slow light sweep across the letters
            s = (t - ev.start - 0.25) / 1.4
            band = None
            if -0.2 < s < 1.25:
                hh, ww = A.shape
                xx = np.arange(ww, dtype=np.float32)[None, :] + 0.45 * np.arange(hh, dtype=np.float32)[:, None]
                c = -80 + s * (ww + 160)
                band = np.exp(-((xx - c) / 46.0) ** 2).astype(np.float32)
            g = blur(A, 8.0)
            gk = 0.85 + (0.9 * band.max() if band is not None else 0)
            gmask = g * (1 + 1.6 * band) if band is not None else g
            glow = (GOLD, min(1.0, 0.75 if band is None else 0.75), np.clip(gmask, 0, 1.6))
            ink = (1.0, 0.95, 0.80)
            layers = [(A, ink)]
            if band is not None:
                layers.append((A * band * 0.85, (1.0, 1.0, 0.97)))
            bgl = float(luma(F[int(b.y0):int(b.y0) + b.h:4, int(b.x0):int(b.x0) + b.w:4]).mean())
            composite(F, b.x0, b.y0, layers, op, ink_mode=0.0, halo=halo_layers(A), glow=glow,
                      halo_k=0.30 + 0.38 * smoothstep(0.3, 0.85, bgl), shadow_k=0.6 + 0.2 * smoothstep(0.3, 0.85, bgl))
            return
        if layers is None:
            layers = [(A, INK)]
        halo = b.halo() if A is b.A else halo_layers(layers[0][0])
        if halo_scale != 1.0:
            halo = (halo[0] * halo_scale, np.clip(halo[1] * halo_scale, 0, 1))
        composite(F, b.x0, b.y0, layers, op, ink_mode=ink_mode, halo=halo, glow=glow)

    def _cached(self, key, fn):
        v = self._cache.get(key)
        if v is None:
            v = self._cache[key] = fn()
        return v


# ================================================================================================
# effects
# ================================================================================================
def _noise1d(n, seed, scale=18.0):
    rng = np.random.default_rng(seed)
    k = int(n / scale) + 3
    v = rng.random(k).astype(np.float32)
    x = np.arange(n, dtype=np.float32) / scale
    i = np.floor(x).astype(int)
    f = x - i
    f = f * f * (3 - 2 * f)
    return v[i] * (1 - f) + v[i + 1] * f


def fx_drift(b, p):
    """Words move apart horizontally (from each line's centre) - integer copy per word."""
    if p <= 0:
        return b.A
    out = np.zeros_like(b.A)
    lines = {}
    for wd in b.words:
        lines.setdefault(round(wd[4]), []).append(wd)
    for ws in lines.values():
        lc = (ws[0][1] + ws[-1][3]) / 2.0
        lw = max(1.0, ws[-1][3] - ws[0][1])
        for _, x0, y0, x1, y1 in ws:
            c = (x0 + x1) / 2.0
            dx = int(round((c - lc) / lw * 2.0 * 22.0 * p))
            xa, xb = int(x0) - 2, int(math.ceil(x1)) + 2
            ya, yb = max(0, int(y0) - 4), min(b.h, int(math.ceil(y1)) + 8)
            xa, xb = max(0, xa), min(b.w, xb)
            ta, tb = max(0, xa + dx), min(b.w, xb + dx)
            if tb <= ta:
                continue
            src = b.A[ya:yb, ta - dx:tb - dx]
            np.maximum(out[ya:yb, ta:tb], src, out=out[ya:yb, ta:tb])
    return out


def fx_ripple(A, wgt, tt, p_hold, p_out):
    h, w = A.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    ramp = smoothstep(0.0, 0.6, tt)
    amp = 1.05 * ramp * wgt + 5.0 * ease_in(p_out)
    ph = 2 * math.pi * 1.1 * tt
    dy = amp * np.sin(2 * math.pi * xx / 62.0 - ph)
    dx = 0.35 * amp * np.sin(2 * math.pi * yy / 24.0 - 1.3 * ph)
    if p_out > 0:            # the line slides down a little, like water running off
        dy += 7.0 * ease_in(p_out) * (0.5 + 0.5 * np.sin(xx / 23.0))
    out = remap(A, xx - dx, yy - dy)
    if p_out > 0:
        out = blur(out, 1.4 * p_out)
    return out


def fx_melt(b, wgt, p_hold, p_out, noise):
    A = b.A
    if p_hold > 0 and p_out <= 0:
        s = 0.9 * smoothstep(0.3, 1.0, p_hold)       # "melted" softens while it is spoken
        if s > 0.05:
            A = A * (1 - wgt * s / 0.9) + blur(A, s) * (wgt * s / 0.9)
        return A
    if p_out <= 0:
        return A
    h, w = A.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    rel = np.clip((yy - b.pad) / max(1.0, h - 2 * b.pad), 0, 1.4)
    sag = (p_out ** 1.7) * (3.0 + 26.0 * noise[None, :]) * rel ** 1.5
    out = remap(A, xx, yy - sag)
    return blur(out, 0.4 + 2.0 * p_out)


def crumble_setup(A, seed=0, cell=3):
    ys, xs = np.nonzero(A > 0.02)
    vals = A[ys, xs].astype(np.float32)
    h, w = A.shape
    rng = np.random.default_rng(1234 + seed)
    ch, cw = h // cell + 1, w // cell + 1
    # release order: left-to-right sweep + smooth noise (organic chunks) + a little per-grain jitter
    coarse = rng.random((ch // 4 + 2, cw // 4 + 2)).astype(np.float32)
    smooth = cv2.resize(coarse, (cw, ch), interpolation=cv2.INTER_CUBIC) if cv2 is not None else \
        np.kron(coarse, np.ones((4, 4), np.float32))[:ch, :cw]
    r1 = np.clip(0.8 * smooth + 0.2 * rng.random((ch, cw)).astype(np.float32), 0, 1)
    r2 = rng.random((ch, cw)).astype(np.float32)
    r3 = rng.random((ch, cw)).astype(np.float32)
    cy, cx = ys // cell, xs // cell
    xn = xs.astype(np.float32) / w
    return {"shape": (h, w), "ys": ys, "xs": xs, "vals": vals,
            "release": 0.70 * xn + 0.30 * r1[cy, cx], "r2": r2[cy, cx], "r3": r3[cy, cx]}


def fx_crumble(st, p):
    """Return (still-attached mask, falling dust mask) at exit progress p."""
    h, w = st["shape"]
    q = np.clip((p * 1.45 - st["release"]) / 0.42, 0, 1)
    moving = q > 0
    stay = np.zeros((h, w), np.float32)
    keep = ~moving
    stay[st["ys"][keep], st["xs"][keep]] = st["vals"][keep]
    dust = np.zeros((h, w), np.float32)
    if moving.any():
        qm = q[moving]
        r2, r3 = st["r2"][moving], st["r3"][moving]
        ny = st["ys"][moving] + (qm ** 2) * (16 + 40 * r2) - 3.0 * qm * (1 - qm) * r3
        nx = st["xs"][moving] + qm * (8 + 30 * r3) + 4.0 * np.sin(qm * 6.0 + r2 * 6.28)
        a = st["vals"][moving] * (1 - qm) ** 1.3 * (0.75 + 0.25 * r3)
        ny = np.clip(np.round(ny).astype(int), 0, h - 1)
        nx = np.clip(np.round(nx).astype(int), 0, w - 1)
        np.maximum.at(dust, (ny, nx), a)
        dust = np.clip(blur(dust, 0.7) * 1.8, 0, 1)
    return stay, dust


# ================================================================================================
# CLI: render a caption specimen sheet for review
# ================================================================================================
def specimen(out_png, bg=None):
    """Write a contact sheet of every caption at its mid time over a grey/bright/dark gradient."""
    phr = json.load(open(os.path.join(os.environ.get("WORK", "/opt/work/psalm22"), "audio", "phrases.json")))
    track = CaptionTrack(phr["phrases"], phr["total"])
    tiles = []
    for i, ev in enumerate(track.events):
        F = np.zeros((H, W, 3), np.float32)
        g = np.linspace(0.08, 0.95, H, dtype=np.float32)[:, None, None] if i % 2 else \
            np.linspace(0.9, 0.12, H, dtype=np.float32)[:, None, None]
        F[:] = g * np.array([1.0, 0.92, 0.8], np.float32)
        track.render(F, (ev.start + ev.end) / 2)
        tiles.append(Image.fromarray((np.clip(F[760:980], 0, 1) * 255).astype(np.uint8)))
    cols = 3
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * W // 2, rows * 110), (20, 20, 20))
    for i, tile in enumerate(tiles):
        sheet.paste(tile.resize((W // 2, 110)), ((i % cols) * W // 2, (i // cols) * 110))
    sheet.save(out_png)
    print(out_png)


if __name__ == "__main__":
    import sys
    ensure_fonts(verbose=True)
    work = os.environ.get("WORK", "/opt/work/psalm22")
    os.makedirs(os.path.join(work, "comp"), exist_ok=True)
    specimen(sys.argv[1] if len(sys.argv) > 1 else os.path.join(work, "comp", "caption_specimen.png"))
