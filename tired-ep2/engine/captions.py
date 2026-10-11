"""Burned-in, word-highlighted captions (most mobile viewers watch muted).

Drawn by the renderer on top of every scene. A scene module can override:
  CAPTION_Y = 1450            # baseline of the caption's LAST line (logical px)
  def caption_y(t, info): ... # per-frame override (return None to hide)
"""
import re
from .core import W, text, text_width, set_font, clamp, seg, ease_out_back, saved

SPEAKER = {
    "tired": {"hl": "#9fb4ff", "tag": None},     # Tiredness: sleepy periwinkle
    "embar": {"hl": "#ff8fb8", "tag": None},     # Embarrassment: blush pink
    "boss": {"hl": "#7ff0d0", "tag": None},      # the Boss: cold mint
    "guard": {"hl": "#ffc857", "tag": None},
    "guard2": {"hl": "#ffa07a", "tag": None},
    "recep": {"hl": "#d6a8ff", "tag": None},
    "narrator": {"hl": "#ffffff", "tag": None},
}
SIZE = 66
MAX_W = 860
MAX_WORDS = 6
DEFAULT_Y = 1450


def _chunks(words):
    """Split words into display chunks (<= MAX_WORDS, break at punctuation)."""
    chunks, cur = [], []
    for i, w in enumerate(words):
        cur.append(i)
        end_punct = re.search(r"[.!?…,;:—]$", w) is not None
        if len(cur) >= MAX_WORDS or (end_punct and len(cur) >= 3) or re.search(r"[.!?…]$", w):
            chunks.append(cur)
            cur = []
    if cur:
        if chunks and len(cur) <= 1:
            chunks[-1].extend(cur)
        else:
            chunks.append(cur)
    return chunks


def _layout(ctx, words, idxs, font, size):
    """Greedy wrap chunk words into <= 2 rows. Returns list of rows of idx."""
    rows, cur, cur_w = [], [], 0.0
    sp = text_width(ctx, " ", font, size)
    for i in idxs:
        ww = text_width(ctx, words[i], font, size)
        if cur and cur_w + sp + ww > MAX_W:
            rows.append(cur)
            cur, cur_w = [i], ww
        else:
            cur_w = cur_w + (sp if cur else 0) + ww
            cur.append(i)
    if cur:
        rows.append(cur)
    # no orphan word alone on the second row: move one word down if it fits
    if len(rows) == 2 and len(rows[1]) == 1 and len(rows[0]) >= 3:
        cand = [rows[0][-1]] + rows[1]
        w2 = sum(text_width(ctx, words[i], font, size) for i in cand) + sp * (len(cand) - 1)
        if w2 <= MAX_W:
            rows = [rows[0][:-1], cand]
    return rows


def draw_captions(ctx, info, t, scene_mod=None):
    # during an interruption (overlapping lines) show the newest speaker
    active = [l for l in info.lines if l.start <= t < l.end]
    line = max(active, key=lambda l: l.start) if active else None
    if line is None:
        # hold the last caption briefly after the line ends (reading time)
        last = info.last_line(t)
        if last is None or t - last.end > 0.2:
            return
        line = last
    if line.nocap or not line.caption:
        return
    y = DEFAULT_Y
    if scene_mod is not None:
        y = getattr(scene_mod, "CAPTION_Y", y)
        fn = getattr(scene_mod, "caption_y", None)
        if fn is not None:
            y = fn(t, info)
            if y is None:
                return
    words = line.caption.split()
    if not words:
        return
    wi = info.word_at(min(t, line.end - 1e-3), line.id)
    wi = max(0, min(wi, len(words) - 1))
    chunks = _chunks(words)
    ci = next((k for k, c in enumerate(chunks) if wi in c), len(chunks) - 1)
    chunk = chunks[ci]
    # chunk start time for pop-in animation
    env_ws = info._lip.get(line.id, {}).get("word_starts", [])
    c_t0 = line.start + (env_ws[chunk[0]] if chunk[0] < len(env_ws) else 0)
    font = "black"
    size = SIZE
    italic = line.who == "narrator"
    rows = _layout(ctx, words, chunk, font, size)
    sty = SPEAKER.get(line.who, SPEAKER["narrator"])
    lh = size * 1.18
    sp = text_width(ctx, " ", font, size)
    k = ease_out_back(seg(t, c_t0 - 0.02, c_t0 + 0.16))
    scale = 0.86 + 0.14 * k
    top = y - (len(rows) - 1) * lh
    with saved(ctx, W / 2, top - size * 0.35, scale) as c:
        for r, row in enumerate(rows):
            widths = [text_width(c, words[i], font, size) for i in row]
            total = sum(widths) + sp * (len(row) - 1)
            x = -total / 2
            yy = r * lh + size * 0.35
            for i, ww in zip(row, widths):
                active = i == wi and line.start <= t <= line.end
                spoken = i <= wi
                col = sty["hl"] if active else "#ffffff"
                text(c, words[i], x, yy, size, col, font, "left",
                     outline="#0a0612", outline_w=11, italic=italic,
                     shadow=(0, 5, (0, 0, 0, 0.45)))
                x += ww + sp
