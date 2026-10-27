"""Burned-in subtitles (phrase cards with the spoken word highlighted) + SRT export."""
import os
import re

import skia

import paths
from anchors import tl
from gfx import clamp, font, hexc, stroke
from script import LINES

COLORS = {"HALE": "#ffc46b", "KAI": "#7fe3c4", "NARRATOR": "#a9c8ff", "ANCHOR": "#e2e6f0"}
FONT_SIZE = 52
LINE_H = 64
MAX_W = 880
BASE_Y = 1592  # baseline of the last line

_norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())


def _display_tokens(text):
    text = re.sub(r"\s*\{[0-9.]+\}\s*", " ", text)
    return text.split()


def build_cards():
    script_chunks = {lid: [c[0] for c in chunks] for lid, sp, chunks, _, _ in LINES}
    cards = []
    for ln in tl()["lines"]:
        words = ln["words"]
        wi = 0
        for ci, ctext in enumerate(script_chunks[ln["id"]]):
            toks = _display_tokens(ctext)
            timed = []
            for tok in toks:
                n = _norm(tok)
                if not n:
                    continue
                # match next timed word (tolerate tokenizer differences)
                if wi < len(words):
                    w = words[wi]
                    timed.append((tok, w["start"], w["end"]))
                    wi += 1
                    # kokoro may split one display token into two words (e.g. "nine-tenths")
                    while wi < len(words) and _norm(words[wi - 1]["text"]) != n and \
                            n.startswith(_norm(words[wi - 1]["text"])) and \
                            _norm(words[wi - 1]["text"] + words[wi]["text"]) in n:
                        timed[-1] = (tok, timed[-1][1], words[wi]["end"])
                        wi += 1
                else:
                    last = timed[-1][2] if timed else ln["start"]
                    timed.append((tok, last, last + 0.2))
            # split long chunks into cards
            groups = [timed]
            if len(ctext) > 58:
                groups = _split(timed)
            for g in groups:
                if g:
                    cards.append(dict(speaker=ln["speaker"], words=g, start=g[0][1] - 0.08, end=g[-1][2] + 0.35))
    # tidy overlaps / flicker
    for a, b in zip(cards, cards[1:]):
        if b["start"] - a["end"] < 0.5:
            a["end"] = min(a["end"] + 0.5, b["start"] - 0.02)
        if a["end"] > b["start"] - 0.02:
            a["end"] = b["start"] - 0.02
    return cards


def _split(timed):
    text = " ".join(w[0] for w in timed)
    if len(text) <= 58:
        return [timed]
    # prefer a comma near the middle
    best, bestscore = None, 1e9
    total = len(text)
    acc = 0
    for i, w in enumerate(timed[:-1]):
        acc += len(w[0]) + 1
        score = abs(acc - total / 2) - (25 if w[0].endswith(",") else 0)
        if score < bestscore:
            best, bestscore = i, score
    left, right = timed[: best + 1], timed[best + 1:]
    return _split(left) + _split(right)


def _wrap(words, f):
    """Balanced wrap into at most two lines."""
    texts = [w[0] for w in words]
    full = " ".join(texts)
    if f.measureText(full) <= MAX_W:
        return [list(range(len(words)))]
    best, bestw = None, 1e9
    for k in range(1, len(words)):
        l1 = " ".join(texts[:k])
        l2 = " ".join(texts[k:])
        w = max(f.measureText(l1), f.measureText(l2))
        if w < bestw:
            best, bestw = k, w
    return [list(range(best)), list(range(best, len(words)))]


_CARDS = None


def cards():
    global _CARDS
    if _CARDS is None:
        _CARDS = build_cards()
    return _CARDS


def draw(c, t):
    f = font(FONT_SIZE, "extrabold")
    sp = f.measureText(" ")
    for card in cards():
        if not (card["start"] <= t <= card["end"]):
            continue
        a = min(clamp((t - card["start"]) / 0.1), clamp((card["end"] - t) / 0.12))
        col = COLORS[card["speaker"]]
        lines = _wrap(card["words"], f)
        n = len(lines)
        for li, idxs in enumerate(lines):
            y = BASE_Y - (n - 1 - li) * LINE_H
            widths = [f.measureText(card["words"][i][0]) for i in idxs]
            total = sum(widths) + sp * (len(idxs) - 1)
            x = 540 - total / 2
            # soft dark backdrop for readability
            shadow = skia.Paint(AntiAlias=True, Color=hexc("#050816", 0.55 * a))
            shadow.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 16))
            c.drawRoundRect(skia.Rect.MakeLTRB(x - 18, y - 46, x + total + 18, y + 16), 18, 18, shadow)
            for i, wdt in zip(idxs, widths):
                tok, ws, we = card["words"][i]
                nxt = card["words"][i + 1][1] if i + 1 < len(card["words"]) else we + 0.25
                active = ws - 0.03 <= t < nxt - 0.03
                spoken = t >= ws - 0.03
                c.drawString(tok, x, y, f, stroke(hexc("#0b0f1e", 0.9 * a), 9))
                if active:
                    fillc = hexc(col, a)
                elif spoken:
                    fillc = hexc("#ffffff", a)
                else:
                    fillc = hexc("#ffffff", 0.78 * a)
                c.drawString(tok, x, y, f, skia.Paint(AntiAlias=True, Color=fillc))
                x += wdt + sp


def write_srt(path):
    def ts(x):
        x = max(0.0, x)
        h = int(x // 3600)
        m = int(x % 3600 // 60)
        s = x % 60
        return f"{h:02d}:{m:02d}:{int(s):02d},{int(round((s - int(s)) * 1000)) % 1000:03d}"

    names = {"HALE": "HALE", "KAI": "KAI", "NARRATOR": "NARRATOR", "ANCHOR": "TV NEWS"}
    out = []
    for i, cd in enumerate(cards(), 1):
        text = " ".join(w[0] for w in cd["words"])
        out.append(f"{i}\n{ts(cd['start'])} --> {ts(cd['end'])}\n{names[cd['speaker']]}: {text}\n")
    open(path, "w").write("\n".join(out))


if __name__ == "__main__":
    cs = cards()
    print(len(cs), "cards")
    for cd in cs[:12]:
        print(round(cd["start"], 2), round(cd["end"], 2), cd["speaker"], " ".join(w[0] for w in cd["words"]))
    write_srt(os.path.join(paths.OUTPUT, "what_if_no_force.srt"))
