"""Shot schedule, boot sequence, credits and captions for The Green Room."""
import math, re
import skia
from common import *
from script import SPEAKERS
from world import Room, SHOTS


class Film:
    def __init__(self):
        tl = self.tl = Timeline()
        self.room = Room(tl)
        T, E, Wd = tl.s, tl.e, tl.wfind
        r = self.room
        self.shots = [
            (0, "WIDE", 0), (T("d1") - 0.2, "TV", 0), (T("t1") - 0.1, "TYLER_M", 0), (T("c1") - 0.1, "CEO_M", 0),
            (T("d2") - 0.1, "TV_C", 0), (T("hush"), "COUCH", 0), (T("hush") + 1.0, "WIDE", 0.8),
            (T("t2") - 0.2, "TYLER_M", 0), (T("m1") - 0.1, "CFO_M", 0), (T("c2") - 0.5, "CEO_M", 0),
            (T("m2") - 0.1, "CFO_M", 0), (T("d3") - 0.1, "TV", 0), (T("t4") - 0.1, "TYLER_M", 0),
            (T("d4") - 0.1, "TV", 0), (T("p1") - 0.1, "PAM_M", 0), (T("d5") - 0.1, "TV", 0), (T("m3") - 0.1, "CFO_M", 0),
            (T("t5") - 0.1, "TYLER_M", 0), (T("y1") - 0.1, "ANGELS", 0), (T("g2") + 0.3, "ANGEL_LEGS", 1.2),
            (T("c4") - 0.1, "CEO_M", 0), (T("t6") - 0.1, "TYLER_M", 0), (T("p2") - 0.1, "PAM_M", 0),
            (T("k1") - 0.1, "KID_M", 0), (T("c5") - 0.1, "CEO_M", 0), (T("d6") - 0.1, "TV", 0), (T("c6") - 0.1, "CEO_M", 0),
            (T("k2") - 0.1, "KID_M", 0), (T("d6b") - 0.1, "TV", 0), (T("p3") - 0.2, "PAM_M", 0),
            (T("think"), "TV", 0), (T("think") + 0.1, "TV_C", 2.2), (T("d8") - 0.1, "COUCH", 0),
            (T("d8") + 0.1, "TV_C", 3.2), (T("t7") - 0.1, "TYLER_M", 0), (T("m4") - 0.1, "CFO_M", 0),
            (T("d9") - 0.1, "TV_C", 0), (r.chaos0, "WIDE", 0), (T("c7") - 0.1, "CEO_M", 0),
            (T("t8") - 0.1, "TYLER_M", 0), (T("p4") - 0.1, "PAM_M", 0), (T("k3") - 0.1, "KID_M", 0),
            (T("m5") - 0.1, "CFO_M", 0), (T("y3") - 0.1, "ANGELS", 0), (T("door"), "DOOR", 0),
            (T("c8") - 0.1, "CEO_M", 0), (T("j2") - 0.1, "DOOR", 0), (T("d10") - 0.1, "WIDE", 0),
            (T("d11") - 0.1, "TV", 0), (T("p5") - 0.1, "PAM_M", 0), (T("end"), "WIDE", 0), (T("end") + 0.2, "TV_C", 4.0),
        ]
        self.chunks = {L["id"]: self._chunk(L) for L in tl.spoken}
        self.credits0 = T("end") + 1.2

    def camera(self, t):
        cur = SHOTS[self.shots[0][1]]
        last = self.shots[0][0]
        for (t0, name, dur) in self.shots:
            if t < t0:
                break
            tgt = SHOTS[name]
            if dur > 0:
                u = ease_io(prog(t, t0, t0 + dur))
                cur = tuple(lerp(a, b, u) for a, b in zip(cur, tgt))
            else:
                cur = tgt
            last = t0
        cx, cy, w = cur
        w *= 1 - 0.03 * smooth((t - last) / 6)
        if self.room.chaos(t):
            cx += math.sin(t * 13) * 10
            cy += math.cos(t * 11) * 10
        return cx + noise1(t * 0.25, 1) * 4, cy + noise1(t * 0.25, 2) * 4, w

    def frame(self, cv, t):
        cv.clear(argb("#000000"))
        cx, cy, vw = self.camera(t)
        s = W / vw
        cv.save()
        cv.translate(W / 2, H / 2)
        cv.scale(s, s)
        cv.translate(-cx, -cy)
        self.room.draw(cv, t)
        cv.restore()
        if self.room.chaos(t) and int(t * 6) % 7 == 0:
            rect(cv, 0, 0, W, H, paint("#ff2a6a", 0.08))
        self.boot(cv, t)
        self.captions(cv, t)
        self.credits(cv, t)

    def boot(self, cv, t):
        if t > 1.6:
            return
        a = 1 - prog(t, 1.2, 1.6)
        rect(cv, 0, 0, W, H, paint("#000", a))
        lines = ["> new request from human:", '> "go unhinged and unfiltered"', "> loading cast...", "> waking the green room"]
        f = font("mono", 34)
        for i, s in enumerate(lines):
            n = int(clamp((t - i * 0.25) / 0.25) * len(s))
            text(cv, s[:n], 80, 800 + i * 60, f, paint("#9fffb0", a))

    def credits(self, cv, t):
        t0 = self.credits0
        if t < t0:
            return
        a = smooth(prog(t, t0, t0 + 0.6)) * (1 - prog(t, self.tl.total - 0.8, self.tl.total))
        rect(cv, 0, 0, W, H, paint("#05060b", 0.8 * a))
        rows = [("THE GREEN ROOM", None), ("", None), ("render log", None),
                ("cups of coffee spat", "1"), ("pigeons audited", "1"), ("semicolons comforted", "1"),
                ("legs issued to cosmic clerks", "0"), ("CEOs turned blue", "2"), ("views", "13"),
                ("cameos", "1, invited"), ("", None), ("status", "RENDER COMPLETE")]
        y = 520
        for i, (k, v) in enumerate(rows):
            ra = a * smooth(prog(t, t0 + 0.3 + i * 0.22, t0 + 0.6 + i * 0.22))
            if i == 0:
                text(cv, k, W / 2, y, font("black", 80), paint("#9fffb0", ra), "center")
            elif v is None:
                text(cv, k, W / 2, y, font("mono", 30), paint("#5f8f6f", ra), "center")
            else:
                text(cv, k, 120, y, font("mono", 34), paint("#d0d0d0", ra))
                text(cv, v, W - 120, y, font("mono", 34), paint("#9fffb0", ra), "right")
            y += 78 if i else 120

    # ------------------------------------------------------------ captions
    def _chunk(self, L):
        words = [list(w) for w in L["words"]]
        toks = list(L.get("tokens", []))
        ti = 0
        for w in words:
            if "[BLEEP]" in w[0] and ti < len(toks):
                w[1], w[2] = toks[ti][1] - L["start"], toks[ti][2] - L["start"]
                ti += 1
        f = font("black", 62)
        chunks, cur = [], []
        for i, w in enumerate(words):
            cur.append(i)
            nxt = " ".join(words[j][0] for j in cur + ([i + 1] if i + 1 < len(words) else []))
            brk = re.search(r"[.?!,]$|\.\.\.$", w[0]) is not None
            if (brk and len(" ".join(words[j][0] for j in cur)) > 6) or text_w(nxt.upper(), f) * 1.1 > 860 or len(cur) >= 4:
                chunks.append(cur)
                cur = []
        if cur:
            chunks.append(cur)
        return words, chunks

    def captions(self, cv, t):
        tl = self.tl
        L = None
        for c in tl.spoken:
            if c["start"] - 0.05 <= t <= c["end"] + 0.4:
                L = c
        if not L:
            return
        nxt = [c for c in tl.spoken if c["start"] > L["start"]]
        if nxt and t > nxt[0]["start"] - 0.05:
            return
        rel = t - L["start"]
        words, chunks = self.chunks[L["id"]]
        ci = 0
        for k, ch in enumerate(chunks):
            if words[ch[0]][1] - 0.05 <= rel:
                ci = k
        ch = chunks[ci]
        name, col = SPEAKERS[L["who"]]
        f = font("black", 62)
        toks = [words[j][0].upper() for j in ch]
        widths = [text_w(s, f) for s in toks]
        space = text_w(" ", f) * 1.4
        total = sum(widths) + space * (len(toks) - 1)
        age = rel - (words[ch[0]][1] - 0.05)
        pop = 0.93 + 0.07 * ease_back(clamp(age / 0.18))
        fade = 1 - prog(t, L["end"] + 0.25, L["end"] + 0.4)
        cv.save()
        cv.translate(W / 2, 1560)
        cv.scale(pop, pop)
        nf = font("black", 30)
        nw = text_w(name, nf)
        rrect(cv, -nw / 2 - 18, -124, nw + 36, 48, 24, paint("#000000", 0.55 * fade))
        text(cv, name, 0, -89, nf, paint(col, fade), "center")
        x = -total / 2
        for j, s, wd in zip(ch, toks, widths):
            active = words[j][1] - 0.03 <= rel
            current = active and (rel <= words[j][2] + 0.05 or j == ch[-1])
            fill = col if current else ((255, 255, 255) if active else (220, 220, 220))
            a = fade * (1.0 if active else 0.55)
            if "[BLEEP]" in s:
                rrect(cv, x, -52, wd, 66, 8, paint("#000", a))
                text(cv, "BLEEP", x + wd / 2, -6, font("black", 30), paint("#ff6b6b", a), "center")
            else:
                text(cv, s, x, 0, f, paint((0, 0, 0), 0.35 * fade, blur=6))
                text(cv, s, x, 0, f, paint((10, 10, 14), a, stroke=12))
                text(cv, s, x, 0, f, paint(fill, a))
            x += wd + space
        cv.restore()
