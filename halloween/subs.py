"""Burned-in subtitles: speaker tag + karaoke word highlight, plus sound captions."""
import skia

from gfx import W, clamp, fill, font, rgba, stroke

TEXT_FONT = "Fredoka-SemiBold.ttf"
TAG_FONT = "Griffy-Regular.ttf"
SIZE = 58
LINE_H = 74
MAX_W = 900
BASE_Y = 1468          # first baseline (safe from phone UI at the bottom)

# sound captions shown during beats: beat id -> (offset, duration, text)
SOUND_CAPTIONS = {
    "wind1": [(0.1, 1.3, "(the wind whistles... ooooo)")],
    "chimes": [(0.2, 1.1, "BONG..."), (1.45, 1.1, "BONG..."), (2.7, 1.1, "BONG..."), (3.95, 1.5, "BONG!")],
    "oooo": [(0.1, 3.0, "OOOOOooooooo...")],
    "eyes": [(0.6, 1.6, "(something blinks in the dark)")],
    "thumps": [(0.0, 0.9, "THUMP."), (1.1, 0.9, "THUMP."), (2.2, 1.0, "creeeak..."), (3.2, 0.9, "THUMP.")],
    "mrrp": [(0.1, 1.0, "Mrrp.")],
    "hug": [(0.2, 1.1, "(ba-dum... ba-dum...)")],
    "scramble": [(0.2, 2.0, "(scramble!)")],
}


class Subs:
    def __init__(self, T, base_y=None, captions=None, prefer_latest=False):
        self.T = T
        self.prefer_latest = prefer_latest   # back-to-back sung lines: a new line replaces the old one
        self.base_y = BASE_Y if base_y is None else base_y
        self.captions = SOUND_CAPTIONS if captions is None else captions
        self.f = font(TEXT_FONT, SIZE)
        self.ftag = font(TAG_FONT, 50)
        self.fcap = font(TAG_FONT, 54)
        self.pages = {}
        for d in T.lines:
            self.pages[d["id"]] = self._paginate(d)

    def _paginate(self, d):
        pages, lines, cur, curw = [], [], [], 0.0
        sp = self.f.measureText(" ")
        prev_chunk = None
        for i, w in enumerate(d["words"]):
            ww = self.f.measureText(w["text"])
            new_chunk = prev_chunk is not None and w["chunk"] != prev_chunk
            if cur and (curw + sp + ww > MAX_W):
                lines.append(cur)
                cur, curw = [], 0.0
                if len(lines) == 2:
                    pages.append(lines)
                    lines = []
            elif cur and new_chunk and (len(lines) == 1 or curw > MAX_W * 0.55):
                lines.append(cur)
                cur, curw = [], 0.0
                pages.append(lines)
                lines = []
            cur.append(i)
            curw += (sp if curw else 0) + ww
            prev_chunk = w["chunk"]
        if cur:
            lines.append(cur)
        if lines:
            pages.append(lines)
        return pages

    def draw(self, c, t, alpha=1.0):
        T = self.T
        drawn = False
        for d in (reversed(T.lines) if self.prefer_latest else T.lines):
            if not (d["start"] - 0.2 <= t <= d["end"] + 0.5):
                continue
            words = d["words"]
            pages = self.pages[d["id"]]
            for pi, lines in enumerate(pages):
                first = words[lines[0][0]]
                last = words[lines[-1][-1]]
                p0 = first["start"] - (0.15 if pi == 0 else 0.0)
                if pi + 1 < len(pages):
                    p1 = words[pages[pi + 1][0][0]]["start"]
                else:
                    p1 = last["end"] + 0.45
                if p0 <= t < p1:
                    a = alpha * clamp((t - p0) / 0.1) * clamp((p1 - t) / 0.12 if pi + 1 == len(pages) else 1.0)
                    self._draw_page(c, d, lines, t, a)
                    drawn = True
            if drawn:
                break
        if not drawn:
            for bid, caps in self.captions.items():
                b = T.items.get(bid)
                if not b:
                    continue
                for off, dur, txt in caps:
                    t0 = b["start"] + off
                    if t0 <= t <= t0 + dur:
                        a = alpha * clamp((t - t0) / 0.12) * clamp((t0 + dur - t) / 0.2)
                        self._caption(c, txt, a)

    def _caption(self, c, txt, a):
        w = self.fcap.measureText(txt)
        x = W / 2 - w / 2
        y = self.base_y + 10
        c.drawRoundRect(skia.Rect.MakeLTRB(x - 30, y - 62, x + w + 30, y + 26), 26, 26, fill((6, 4, 12), 0.45 * a))
        c.drawString(txt, x, y, self.fcap, stroke((8, 6, 14), 9, a))
        c.drawString(txt, x, y, self.fcap, fill((214, 206, 236), a))

    def _draw_page(self, c, d, lines, t, a):
        words = d["words"]
        f = self.f
        sp = f.measureText(" ")
        widths = []
        for ln in lines:
            widths.append(sum(f.measureText(words[i]["text"]) for i in ln) + sp * (len(ln) - 1))
        box_w = max(widths)
        y0 = self.base_y
        top = y0 - SIZE - 22
        bottom = y0 + LINE_H * (len(lines) - 1) + 24
        if d["who"] != "NARRATOR":
            top -= 52
        c.drawRoundRect(skia.Rect.MakeLTRB(W / 2 - box_w / 2 - 34, top, W / 2 + box_w / 2 + 34, bottom), 30, 30,
                        fill((6, 4, 12), 0.42 * a))
        col = d["color"]
        if d["who"] != "NARRATOR":
            tag = d["label"]
            tw = self.ftag.measureText(tag)
            ty = y0 - SIZE - 14
            c.drawString(tag, W / 2 - tw / 2, ty, self.ftag, stroke((8, 6, 14), 8, a))
            c.drawString(tag, W / 2 - tw / 2, ty, self.ftag, fill(col, a))
        base_col = (246, 242, 252) if d["who"] != "NARRATOR" else (232, 224, 252)
        for li, ln in enumerate(lines):
            x = W / 2 - widths[li] / 2
            y = y0 + li * LINE_H
            for i in ln:
                w = words[i]
                tw = f.measureText(w["text"])
                cur = w["start"] - 0.03 <= t < max(w["end"], w["start"] + 0.12)
                said = t >= w["end"]
                if cur:
                    colw, aw = col, 1.0
                elif said:
                    colw, aw = base_col, 1.0
                else:
                    colw, aw = base_col, 0.62
                c.drawString(w["text"], x, y, f, stroke((8, 6, 14), 10, a * max(aw, 0.8)))
                c.drawString(w["text"], x, y, f, fill(colw, a * aw))
                x += tw + sp
