"""Burned-in subtitles and titles (drawn with skia so they match the frame)."""
import skia

from gfx import FONT_DIR, font

_fonts = {}


def F(name, size):
    key = (name, size)
    if key not in _fonts:
        _fonts[key] = font(FONT_DIR + name, size)
    return _fonts[key]


SUB_COLOR = {"JESUS": (1.0, 0.93, 0.76, 1.0), "NARRATOR": (0.93, 0.93, 0.93, 1.0)}


def build_cues(T):
    cues = []
    for lid in T.order:
        m = T.lines[lid]
        for s in m["segments"]:
            for c in s["subs"]:
                cues.append(dict(start=m["start"] + c["start"], end=m["start"] + c["end"], text=c["text"],
                                 speaker=m["speaker"]))
    cues.sort(key=lambda c: c["start"])
    # hold each cue a little after it is spoken, without overlapping the next one
    for i, c in enumerate(cues):
        nxt = cues[i + 1]["start"] if i + 1 < len(cues) else c["end"] + 2
        c["end"] = min(max(c["end"] + 0.45, c["start"] + 1.1), nxt - 0.04)
    return cues


def wrap(text, fnt, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if fnt.measureText(test) <= max_w or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    # balance two lines
    if len(lines) == 2:
        allw = text.split()
        best = None
        for k in range(1, len(allw)):
            a, b = " ".join(allw[:k]), " ".join(allw[k:])
            wa, wb = fnt.measureText(a), fnt.measureText(b)
            if wa <= max_w and wb <= max_w:
                score = abs(wa - wb)
                if best is None or score < best[0]:
                    best = (score, [a, b])
        if best:
            lines = best[1]
    return lines


def draw_cue(cv, W, H, cue, t):
    alpha = min(1.0, (t - cue["start"]) / 0.12, (cue["end"] - t) / 0.12)
    if alpha <= 0:
        return
    italic = cue["speaker"] == "NARRATOR"
    fnt = F("NotoSans-BoldItalic.ttf" if italic else "NotoSans-Bold.ttf", 31)
    lines = wrap(cue["text"], fnt, W * 0.84)
    lh = 40
    y0 = H * 0.715 - (len(lines) - 1) * lh / 2
    col = SUB_COLOR.get(cue["speaker"], (1, 1, 1, 1))
    for i, ln in enumerate(lines):
        w = fnt.measureText(ln)
        x = (W - w) / 2
        y = y0 + i * lh
        blob = skia.TextBlob(ln, fnt)
        sh = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, 0.55 * alpha))
        sh.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 4))
        cv.drawTextBlob(blob, x + 1, y + 3, sh)
        st = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0.05, 0.03, 0.02, 0.9 * alpha))
        st.setStyle(skia.Paint.kStroke_Style)
        st.setStrokeWidth(5)
        st.setStrokeJoin(skia.Paint.kRound_Join)
        cv.drawTextBlob(blob, x, y, st)
        fp = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(col[0], col[1], col[2], alpha))
        cv.drawTextBlob(blob, x, y, fp)


def draw_subs(cv, W, H, cues, t):
    for c in cues:
        if c["start"] - 0.01 <= t <= c["end"]:
            draw_cue(cv, W, H, c, t)


def spaced(cv, text, fnt, cx, y, spacing, paint):
    widths = [fnt.measureText(ch) for ch in text]
    total = sum(widths) + spacing * (len(text) - 1)
    x = cx - total / 2
    for ch, w in zip(text, widths):
        cv.drawString(ch, x, y, fnt, paint)
        x += w + spacing


def title(cv, W, H, text, sub, alpha, y=190):
    if alpha <= 0:
        return
    band = skia.Paint(AntiAlias=True)
    band.setShader(skia.GradientShader.MakeLinear([skia.Point(0, y - 140), skia.Point(0, y + 110)],
                   [skia.Color4f(0, 0, 0, 0.0).toColor(), skia.Color4f(0.05, 0.03, 0.02, 0.32 * alpha).toColor(), skia.Color4f(0, 0, 0, 0.0).toColor()], [0.0, 0.5, 1.0]))
    cv.drawRect(skia.Rect.MakeLTRB(0, y - 140, W, y + 110), band)
    f1 = F("NotoSerif-Bold.ttf", 50)
    f2 = F("NotoSerif-Italic.ttf", 26)
    glow = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0.15, 0.08, 0.02, 0.55 * alpha))
    glow.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 9))
    spaced(cv, text.upper(), f1, W / 2, y, 5, glow)
    p = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1.0, 0.95, 0.84, alpha))
    spaced(cv, text.upper(), f1, W / 2, y, 5, p)
    if sub:
        g2 = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0.1, 0.05, 0.0, 0.5 * alpha))
        g2.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6))
        spaced(cv, sub, f2, W / 2, y + 46, 3, g2)
        p2 = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1.0, 0.93, 0.8, 0.95 * alpha))
        spaced(cv, sub, f2, W / 2, y + 46, 3, p2)
    line = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1.0, 0.9, 0.7, 0.7 * alpha))
    cv.drawRect(skia.Rect.MakeXYWH(W / 2 - 60, y + 14, 120, 1.6), line)
