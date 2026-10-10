"""Burned-in subtitles (drawn by anim/frame.py over every frame) and an .srt export.

Placement follows the safe area of vertical-video apps: the caption block sits above the
bottom ~22 % of the frame (app captions / buttons) and keeps clear of the right-hand icon
column. Whispered lines (script_data.WHISPER) are set in italics.

    python3 -m anim.subtitles            # writes out/if_you_have_time.srt
"""
from functools import lru_cache

import skia

from anim.core import clamp, timeline
from config import OUT, W

FONT_SIZE = 31
LINE_GAP = 39            # baseline-to-baseline
BOTTOM_BASELINE = 990    # baseline of the last caption line (frame px)
CENTER_X = W / 2 - 14    # nudged left of centre, away from the right-hand icon column
MAX_WIDTH = 520
LEAD_IN = 0.05           # caption appears this long before the voice
HOLD = 0.45              # ...and stays this long after it
MIN_DUR = 1.1
FADE = 0.08


def _typeface(italic):
    style = skia.FontStyle(600, skia.FontStyle.kNormal_Width,
                           skia.FontStyle.kItalic_Slant if italic else skia.FontStyle.kUpright_Slant)
    return skia.Typeface.MakeFromName("Inter", style)


@lru_cache(maxsize=2)
def _font(italic):
    f = skia.Font(_typeface(italic), FONT_SIZE)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    f.setSubpixel(True)
    return f


def _wrap(text, font):
    """One line if it fits, else the most balanced two-line split, preferring a
    break right after punctuation."""
    if font.measureText(text) <= MAX_WIDTH:
        return [text]
    words = text.split()
    best = None
    for k in range(1, len(words)):
        a, b = " ".join(words[:k]), " ".join(words[k:])
        cost = max(font.measureText(a), font.measureText(b))
        if a[-1] not in ".,?!—…;:":
            cost += 60
        if best is None or cost < best[0]:
            best = (cost, [a, b])
    return best[1]


@lru_cache(maxsize=1)
def cues():
    """[(start, end, text, italic)] in film time, non-overlapping."""
    try:
        from script_data import WHISPER
    except ImportError:
        WHISPER = {}
    lines = sorted(timeline()["lines"], key=lambda l: l["start"])
    out = []
    for i, ln in enumerate(lines):
        st = max(0.0, ln["start"] - LEAD_IN)
        en = max(ln["end"] + HOLD, st + MIN_DUR)
        if i + 1 < len(lines):
            en = min(en, lines[i + 1]["start"] - LEAD_IN - 0.02)
        en = max(en, ln["end"])  # never cut a caption before its line ends
        out.append((st, en, ln["text"], ln["id"] in WHISPER))
    # an interrupting line can start before the previous one ends: trim the earlier caption
    for i in range(len(out) - 1):
        if out[i][1] > out[i + 1][0]:
            out[i] = (out[i][0], out[i + 1][0], out[i][2], out[i][3])
    return out


def draw(canvas, t):
    """Draw the active caption (screen space; call with an identity matrix)."""
    for st, en, text, italic in cues():
        if st <= t <= en:
            a = min(clamp((t - st) / FADE), clamp((en - t) / FADE))
            _draw_block(canvas, text, italic, a)
            return


def _draw_block(canvas, text, italic, alpha):
    font = _font(italic)
    lines = _wrap(text, font)
    n = len(lines)
    stroke = skia.Paint(AntiAlias=True, Color=skia.Color(8, 8, 14, int(235 * alpha)),
                        Style=skia.Paint.kStroke_Style, StrokeWidth=6.0,
                        StrokeJoin=skia.Paint.kRound_Join)
    shadow = skia.Paint(AntiAlias=True, Color=skia.Color(0, 0, 0, int(120 * alpha)),
                        MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 5.0))
    fill = skia.Paint(AntiAlias=True, Color=skia.Color(255, 255, 255, int(255 * alpha)))
    for i, s in enumerate(lines):
        y = BOTTOM_BASELINE - (n - 1 - i) * LINE_GAP
        x = CENTER_X - font.measureText(s) / 2
        blob = skia.TextBlob.MakeFromString(s, font)
        canvas.drawTextBlob(blob, x + 1.5, y + 3, shadow)
        canvas.drawTextBlob(blob, x, y, stroke)
        canvas.drawTextBlob(blob, x, y, fill)


def _ts(sec):
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_srt(path=None):
    path = path or (OUT / "if_you_have_time.srt")
    OUT.mkdir(exist_ok=True)
    blocks = []
    for i, (st, en, text, italic) in enumerate(cues(), 1):
        body = "\n".join(_wrap(text, _font(italic)))
        if italic:
            body = "\n".join(f"<i>{b}</i>" for b in body.split("\n"))
        blocks.append(f"{i}\n{_ts(st)} --> {_ts(en)}\n{body}\n")
    path.write_text("\n".join(blocks), encoding="utf-8")
    return path


if __name__ == "__main__":
    print(write_srt())
