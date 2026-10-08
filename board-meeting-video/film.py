"""Top-level: picks the scene for time t, applies the camera, draws title and captions."""
import math, re
import skia
from common import *
from script import SPEAKERS
from boardroom import Board
from opening import Opening
from epilogue import Epilogue

NO_CAPTION = {"c1", "c2", "c3", "c4"}


class Film:
    def __init__(self):
        self.tl = Timeline()
        self.board = Board(self.tl)
        self.opening = Opening(self.tl)
        self.epi = Epilogue(self.tl, self.board, self.opening)
        self.title0 = self.tl.e("n9") + 0.3
        self.title1 = self.tl.e("title")
        self.chunks = {L["id"]: self._chunk(L) for L in self.tl.spoken}

    # ------------------------------------------------------------ frame
    def frame(self, cv, t):
        cv.clear(argb("#000000"))
        tl, ep = self.tl, self.epi
        if t < self.title0:
            self.opening.draw(cv, t, self.world)
        elif t < self.title1 - 0.35:
            self.title(cv, t)
        elif t < ep.doomed0:
            cx, cy, w = self.board.camera(t)
            self.world(cv, cx, cy, w, lambda c: (self.board.draw(c, t), ep.draw_world(c, t) if t > ep.sprout0 else None))
            if t < self.title1:
                a = 1 - prog(t, self.title1 - 0.35, self.title1)
                cv.saveLayerAlpha(None, int(255 * a))
                self.title(cv, t)
                cv.restore()
        elif t < ep.doomed1:
            from boardroom import SHOTS
            self.world(cv, *SHOTS["SCREEN"], lambda c: self.board.draw(c, t))
            k = 0.5 + 0.5 * math.sin(t * 6)
            rect(cv, 0, 0, W, H, paint("#ff2a1a", 0.05 * k))
        elif t < ep.wheel0:
            self.world(cv, *ep.camera(t), lambda c: ep.draw_world(c, t))
            ep.draw_overlay(cv, t)
            # fade to the wheel insert
            a = prog(t, ep.wheel0 - 0.5, ep.wheel0)
            if a > 0:
                rect(cv, 0, 0, W, H, paint("#000", a))
        elif t < ep.dawn0:
            ep.draw_wheel_stop(cv, t, self.world)
            a = 1 - prog(t, ep.wheel0, ep.wheel0 + 0.4)
            if a > 0:
                rect(cv, 0, 0, W, H, paint("#000", a))
        elif t < ep.end0:
            ep.draw_dawn(cv, t, self.world)
            a = max(1 - prog(t, ep.dawn0, ep.dawn0 + 0.3), prog(t, ep.end0 - 0.6, ep.end0))
            if a > 0:
                rect(cv, 0, 0, W, H, paint("#000", a))
        else:
            ep.draw_end(cv, t)
        # record-scratch flash into the title
        fl = pulse(t, self.title0 - 0.08, 0.06, 0.04, 0.35)
        if fl > 0:
            rect(cv, 0, 0, W, H, paint("#ffffff", fl))
        self.captions(cv, t)

    def world(self, cv, cx, cy, vw, fn):
        s = W / vw
        cv.save()
        cv.translate(W / 2, H / 2)
        cv.scale(s, s)
        cv.translate(-cx, -cy)
        fn(cv)
        cv.restore()

    # ------------------------------------------------------------ title card
    def title(self, cv, t):
        t0 = self.title0
        rect(cv, 0, 0, W, H, paint("#000", shader=lin_grad((0, 0), (W, H), [("#15203a", 1), ("#1f2b47", 1)])))
        for k in range(-20, 30):
            x = k * 90 + (t - t0) * 40
            line(cv, x, 0, x - 900, H, paint("#c9a227", 0.05, stroke=3))
        u = ease_back(prog(t, t0 + 0.05, t0 + 0.6))
        cv.save()
        cv.translate(W / 2, 640)
        cv.scale(u, u)
        cv.rotate(45 + (1 - u) * 180)
        rrect(cv, -95, -95, 190, 190, 26, paint("#c9a227"))
        cv.restore()
        if u > 0:
            text(cv, "$", W / 2, 640 + 62, font("black", 170 * u), paint("#15203a"), "center")
        a1 = smooth(prog(t, t0 + 0.4, t0 + 0.9))
        a2 = smooth(prog(t, t0 + 0.9, t0 + 1.4))
        a3 = smooth(prog(t, t0 + 1.6, t0 + 2.2))
        text(cv, "MAMMON CAPITAL", W / 2, 900, font("black", 92), paint("#ffffff", a1), "center")
        text(cv, "QUARTERLY GROWTH REVIEW", W / 2, 975, font("bold", 40), paint("#c9a227", a2), "center")
        line(cv, W / 2 - 220 * a3, 1060, W / 2 + 220 * a3, 1060, paint("#c9a227", a3, stroke=3))
        text(cv, "Agenda item 7:", W / 2, 1150, font("semi", 44), paint("#aab6cc", a3), "center")
        text(cv, "THE KINGDOM", W / 2, 1250, font("black", 96), paint("#ffe9a8", a3), "center")
        text(cv, "OF HEAVEN", W / 2, 1350, font("black", 96), paint("#ffe9a8", a3), "center")
        a4 = smooth(prog(t, t0 + 2.4, t0 + 2.9))
        text(cv, "Q3  ·  30 A.D.", W / 2, 1460, font("semi", 40), paint("#7f8db5", a4), "center")

    # ------------------------------------------------------------ captions
    def _chunk(self, L):
        words = L["words"]
        f = font("black", 64)
        chunks, cur = [], []
        for i, w in enumerate(words):
            cur.append(i)
            txt = " ".join(words[j][0] for j in cur)
            brk = re.search(r"[.?!,]$|\.\.\.$", w[0]) is not None
            nxt = " ".join(words[j][0] for j in cur + ([i + 1] if i + 1 < len(words) else []))
            too_long = text_w(nxt.upper(), f) * 1.08 > 860 or len(cur) >= 4
            if brk and len(cur) >= 1 and (len(txt) > 6 or w[0].endswith(("?", "!", "..."))) or too_long:
                chunks.append(cur)
                cur = []
        if cur:
            chunks.append(cur)
        return chunks

    def captions(self, cv, t):
        tl = self.tl
        L = None
        for cand in tl.spoken:
            nxt_start = None
            if cand["start"] - 0.05 <= t <= cand["end"] + 0.4:
                L = cand
        if not L or L["id"] in NO_CAPTION:
            return
        nxt = [c for c in tl.spoken if c["start"] > L["start"]]
        if nxt and t > nxt[0]["start"] - 0.05:
            return
        rel = t - L["start"]
        words = L["words"]
        chunks = self.chunks[L["id"]]
        ci = 0
        for k, ch in enumerate(chunks):
            if words[ch[0]][1] - 0.05 <= rel:
                ci = k
        ch = chunks[ci]
        name, col = SPEAKERS[L["who"]]
        hl = col if L["who"] != "NARR" else (255, 225, 77)
        f = font("black", 64)
        toks = [words[j][0].upper() for j in ch]
        widths = [text_w(s, f) for s in toks]
        space = text_w(" ", f) * 1.45
        total = sum(widths) + space * (len(toks) - 1)
        y = 1490
        age = rel - (words[ch[0]][1] - 0.05)
        pop = 0.92 + 0.08 * ease_back(clamp(age / 0.18))
        fade = 1 - prog(t, L["end"] + 0.25, L["end"] + 0.4)
        cv.save()
        cv.translate(W / 2, y)
        cv.scale(pop, pop)
        if name:
            nf = font("black", 30)
            nw = text_w(name, nf)
            rrect(cv, -nw / 2 - 18, -122, nw + 36, 48, 24, paint("#000000", 0.55 * fade))
            text(cv, name, 0, -87, nf, paint(col, fade), "center")
        x = -total / 2
        for j, (s, wd) in zip(ch, zip(toks, widths)):
            active = words[j][1] - 0.03 <= rel
            current = active and (rel <= words[j][2] + 0.05 or j == ch[-1])
            fill = hl if current else ((255, 255, 255) if active else (225, 225, 225))
            a = fade * (1.0 if active else 0.55)
            text(cv, s, x, 0, f, paint((0, 0, 0), 0.35 * fade, blur=6))
            text(cv, s, x, 0, f, paint((10, 10, 14), a, stroke=12))
            text(cv, s, x, 0, f, paint(fill, a))
            x += wd + space
        cv.restore()
