"""Top-level: shot schedule, crossfades, title/end cards and captions."""
import math, random, re
import skia
from common import *
from script import SPEAKERS
import world as Wo

SHOTS = {
    "S_WIDE": (540, 1000, 1080), "S_TWO": (540, 1060, 960), "S_CYAN": (330, 1000, 560),
    "S_GOLD": (750, 1000, 560), "S_MON": (540, 1215, 330),
    "K_WIDE": (540, 1000, 1080), "K_FACE": (590, 1070, 600), "K_MID": (560, 1100, 860),
}
FADE = 0.35


class Film:
    def __init__(self):
        tl = self.tl = Timeline()
        T, E, Wd = tl.s, tl.e, tl.wfind
        self.kitchen = Wo.Kitchen(tl)
        self.window = Wo.Window(tl, self.kitchen)
        self.finale = Wo.Finale(tl)
        self.end0 = E("f9") + 2.4
        # (time, scene, shot or mode, move-duration)
        self.sched = [
            (0.0, "space", "S_WIDE", 0), (T("a1") - 0.3, "space", "S_TWO", 1.6),
            (T("a2") - 0.1, "space", "S_GOLD", 0), (Wd("a2", "Code") - 0.2, "kitchen", "K_WIDE", 0),
            (T("a3") - 0.1, "laptop", "chatbot", 0), (T("a4") - 0.1, "space", "S_GOLD", 0),
            (Wd("a4", "PDF") - 0.8, "laptop", "sideways", 0), (T("a5") - 0.1, "laptop", "gov", 0),
            (T("a6") - 0.1, "kitchen", "K_FACE", 0), (T("a7") - 0.1, "space", "S_CYAN", 0),
            (T("d1") - 0.1, "kitchen", "K_WIDE", 0), (T("d4") - 0.1, "space", "S_GOLD", 0),
            (Wd("d4", "ZIP") - 0.6, "kitchen", "K_WIDE", 0),
            (T("r1") - 0.1, "space", "S_TWO", 0), (T("r2") - 0.1, "people", None, 0),
            (T("r3") - 0.1, "space", "S_GOLD", 0), (T("r4") - 0.1, "space", "S_CYAN", 0),
            (T("l1") - 0.1, "space", "S_TWO", 0), (T("l2") - 0.1, "laptop", "tabs", 0),
            (T("l3") - 0.1, "blacksun", None, 0), (Wd("l3", "hold") - 0.3, "phone", None, 0),
            (T("l4") - 0.1, "space", "S_TWO", 0), (T("l5") - 0.1, "space", "S_CYAN", 0),
            (Wd("l5", "Which") - 0.1, "laptop", "appeal", 0),
            (T("t1") - 0.1, "space", "S_GOLD", 0), (T("t2") - 0.1, "space", "S_CYAN", 0),
            (T("t3") - 0.1, "laptop", "timeout", 0), (Wd("t3", "session") - 0.2, "kitchen", "K_FACE", 0),
            (T("t4") - 0.1, "space", "S_TWO", 0), (T("t5") - 0.1, "space", "S_TWO", 0),
            (T("t5") + 0.1, "space", "S_MON", 2.6),
            (T("w1") - 0.2, "kitchen", "K_FACE", 0), (Wd("w2", "district") - 0.3, "kitchen", "K_MID", 1.5),
            (T("w3") - 0.1, "letterhead", None, 0), (T("w4") - 0.1, "space", "S_TWO", 0),
            (T("w4") + 0.2, "space", "S_WIDE", 4.0),
            (T("s1") - 0.1, "once", None, 0), (T("s2") - 0.1, "atoms", None, 0), (T("s3") - 0.1, "baby", None, 0),
            (T("s4") - 0.1, "star", None, 0), (T("s5") - 0.1, "laptop", "regs", 0),
            (Wd("s5", "And", 0) - 0.15, "kitchen", "K_FACE", 0), (T("s6") - 0.1, "kitchen", "K_FACE", 0),
            (T("s7") - 0.1, "forest", None, 0), (T("s8") - 0.1, "winter", None, 0),
            (T("f1") - 0.4, "finale", None, 0), (self.end0, "end", None, 0),
        ]
        self.sched.sort(key=lambda s: s[0])
        self.chunks = {L["id"]: self._chunk(L) for L in tl.spoken}

    # ------------------------------------------------------------ scenes
    def world(self, cv, cx, cy, vw, fn):
        s = W / vw
        cv.save()
        cv.translate(W / 2, H / 2)
        cv.scale(s, s)
        cv.translate(-cx, -cy)
        fn(cv)
        cv.restore()

    def _index(self, t):
        idx = 0
        for i, s in enumerate(self.sched):
            if t >= s[0]:
                idx = i
        return idx

    def _cam(self, i, t):
        """Camera for a world-scene entry, easing from the previous entry of the same scene."""
        t0, scene, shot, dur = self.sched[i]
        tgt = SHOTS[shot]
        if dur > 0 and i > 0 and self.sched[i - 1][1] == scene:
            prev = self._cam(i - 1, t0)
            u = ease_io(prog(t, t0, t0 + dur))
            cam = tuple(lerp(a, b, u) for a, b in zip(prev, tgt))
        else:
            cam = tgt
        age = t - t0
        cx, cy, w = cam
        w *= 1 - 0.03 * smooth(age / 6)
        return (cx + noise1(t * 0.2, 3) * 4, cy + noise1(t * 0.2, 4) * 4, w)

    def draw_entry(self, cv, i, t):
        t0, scene, shot, dur = self.sched[i]
        tl = self.tl
        if scene == "space":
            self.world(cv, *self._cam(i, t), lambda c: self.window.draw(c, t, lambda cc, tt, thumb=False: self.kitchen.draw(cc, tt, thumb)))
        elif scene == "kitchen":
            self.world(cv, *self._cam(i, t), lambda c: self.kitchen.draw(c, t))
            self.dream_bubble(cv, t, shot)
            if tl.s("s5") < t < tl.e("s5") + 0.5:
                Wo.tiles_404(cv, t, tl.wfind("s5", "Those") - 0.1)
            if tl.s("s6") - 0.2 < t < tl.e("s6") + 1.0:
                Wo.id_cards(cv, t, tl.wfind("s6", "two") - 0.1)
        elif scene == "laptop":
            Wo.laptop_scene(cv, t, shot, tl)
        elif scene == "people":
            g = 0.0
            for (k, a, b) in tl.by_id["r2"]["tokens"]:
                g = max(g, pulse(t, a - 0.05, 0.05, b - a - 0.1, 0.15))
            Wo.people_lights(cv, t, tl, g)
        elif scene == "blacksun":
            Wo.black_sun(cv, t)
        elif scene == "phone":
            Wo.hold_phone(cv, t)
        elif scene == "letterhead":
            Wo.letterhead(cv, t, tl)
        elif scene == "once":
            Wo.story_once(cv, t, tl)
        elif scene == "atoms":
            Wo.story_atoms(cv, t, tl)
        elif scene == "baby":
            Wo.story_baby(cv, t, tl)
        elif scene == "star":
            Wo.story_star(cv, t, tl)
        elif scene == "forest":
            Wo.forest(cv, t)
        elif scene == "winter":
            Wo.winter(cv, t, tl)
        elif scene == "finale":
            self.finale.draw(cv, t)
        elif scene == "end":
            self.end_card(cv, t)

    def frame(self, cv, t):
        cv.clear(argb("#000000"))
        i = self._index(t)
        t0, scene = self.sched[i][0], self.sched[i][1]
        k = prog(t, t0, t0 + FADE)
        if i > 0 and k < 1 and self.sched[i - 1][1] != scene:
            self.draw_entry(cv, i - 1, t)
            cv.saveLayerAlpha(None, int(255 * smooth(k)))
            self.draw_entry(cv, i, t)
            cv.restore()
        else:
            self.draw_entry(cv, i, t)
        self.title(cv, t)
        self.captions(cv, t)
        if t < 0.8:
            rect(cv, 0, 0, W, H, paint("#000", 1 - t / 0.8))

    # ------------------------------------------------------------ overlays
    def dream_bubble(self, cv, t, shot):
        tl = self.tl
        T, E, Wd = tl.s, tl.e, tl.wfind
        if not (T("d1") - 0.2 < t < E("d4") + 0.6) or shot != "K_WIDE":
            return
        a = prog(t, T("d1"), T("d1") + 0.6) * (1 - prog(t, E("d4") + 0.1, E("d4") + 0.6))
        bx, by = 560, 520
        for (dx, dy, r) in ((580, 820, 22), (600, 750, 34)):
            circle(cv, dx, dy, r * a, paint("#ffffff", 0.9 * a))
        cl = smooth_path([(bx - 330, by), (bx - 280, by - 160), (bx - 100, by - 230), (bx + 120, by - 220),
                          (bx + 300, by - 130), (bx + 340, by + 40), (bx + 220, by + 180), (bx - 40, by + 200),
                          (bx - 260, by + 150)], True, 0.6)
        cv.save()
        cv.translate(bx, by)
        cv.scale(a, a)
        cv.translate(-bx, -by)
        cv.drawPath(cl, paint("#ffffff", 0.93))
        icons = [(Wd("d2", "sunlight"), "sun"), (Wd("d2", "fire"), "fire"), (Wd("d2", "small"), "shop"),
                 (Wd("d2", "password"), "password"), (Wd("d3", "hunted"), "job"), (Wd("d3", "shelter"), "house"),
                 (Wd("d4", "ZIP") - 0.3, "zip")]
        cur, prev, ct = None, None, 0
        for ti, name in icons:
            if t >= ti - 0.15:
                prev, cur, ct = cur, name, ti - 0.15
        if cur:
            k = ease_back(prog(t, ct, ct + 0.35))
            if prev and k < 1:
                Wo.dream_icon(cv, prev, bx, by, 1.4, t, 1 - k)
            Wo.dream_icon(cv, cur, bx, by, 1.4 * k, t, clamp(k))
        cv.restore()

    def title(self, cv, t):
        a = pulse(t, 0.4, 0.8, 1.4, 0.8)
        if a > 0:
            text(cv, "THE LONG DREAM", W / 2, 300, font("serif_b", 96), paint("#fff7e0", a), "center")
            text(cv, "(of a benefit)", W / 2, 370, font("serif_i", 52), paint("#bfd2ff", a), "center")

    def end_card(self, cv, t):
        rect(cv, 0, 0, W, H, paint("#000", shader=lin_grad((0, 0), (0, H), [("#fff8e8", 1), ("#f2d9b0", 1)])))
        k = prog(t, self.end0, self.end0 + 1.2)
        rect(cv, 0, 0, W, H, paint("#0c1030", smooth(k)))
        a = smooth(prog(t, self.end0 + 0.8, self.end0 + 1.8))
        Wo.glow(cv, 380, 860, 300, "#7fe8ff", 0.25 * a)
        Wo.glow(cv, 700, 860, 300, "#ffd86a", 0.25 * a)
        text(cv, "THE LONG DREAM", W / 2, 900, font("serif_b", 96), paint("#fff7e0", a), "center")
        text(cv, "(of a benefit)", W / 2, 975, font("serif_i", 52), paint("#bfd2ff", a), "center")
        b = smooth(prog(t, self.end0 + 1.6, self.end0 + 2.4))
        text(cv, "Office hours: always.", W / 2, 1120, font("semi", 40), paint("#9fb0d8", b), "center")
        fo = prog(t, self.tl.total - 1.0, self.tl.total)
        if fo > 0:
            rect(cv, 0, 0, W, H, paint("#000", fo))

    # ------------------------------------------------------------ captions
    def _words(self, L):
        """Caption words with token words snapped to their real audio spans."""
        words = [list(w) for w in L["words"]]
        toks = list(L.get("tokens", []))
        ti = 0
        for w in words:
            if ("[NAME]" in w[0] or "§§" in w[0]) and ti < len(toks):
                _, a, b = toks[ti]
                w[1], w[2] = a - L["start"], b - L["start"]
                ti += 1
        return words

    def _chunk(self, L):
        words = self._words(L)
        f = font("black", 60)
        chunks, cur = [], []
        for i, w in enumerate(words):
            cur.append(i)
            nxt = " ".join(words[j][0] for j in cur + ([i + 1] if i + 1 < len(words) else []))
            brk = re.search(r"[.?!,]$|\.\.\.$", w[0]) is not None
            too_long = text_w(nxt.upper(), f) * 1.1 > 860 or len(cur) >= 4
            if (brk and len(" ".join(words[j][0] for j in cur)) > 6) or too_long:
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
        if L["id"].startswith("f"):
            self.big_line(cv, t, L)
            return
        rel = t - L["start"]
        words, chunks = self.chunks[L["id"]]
        ci = 0
        for k, ch in enumerate(chunks):
            if words[ch[0]][1] - 0.05 <= rel:
                ci = k
        ch = chunks[ci]
        col = SPEAKERS[L["who"]][1]
        f = font("black", 60)
        toks = [words[j][0].upper() for j in ch]
        widths = []
        for s in toks:
            widths.append(250 if "[NAME]" in s else text_w(s, f))
        space = text_w(" ", f) * 1.4
        total = sum(widths) + space * (len(toks) - 1)
        age = rel - (words[ch[0]][1] - 0.05)
        pop = 0.93 + 0.07 * ease_back(clamp(age / 0.18))
        fade = 1 - prog(t, L["end"] + 0.25, L["end"] + 0.4)
        cv.save()
        cv.translate(W / 2, 1560)
        cv.scale(pop, pop)
        x = -total / 2
        for j, s, wd in zip(ch, toks, widths):
            active = words[j][1] - 0.03 <= rel
            current = active and (rel <= words[j][2] + 0.05 or j == ch[-1])
            fill = col if current else ((255, 255, 255) if active else (220, 220, 220))
            a = fade * (1.0 if active else 0.55)
            if "[NAME]" in s:
                rrect(cv, x, -50, 230, 62, 8, paint("#000000", a))
                rrect(cv, x, -50, 230, 62, 8, paint(col, a * (0.4 + 0.4 * current), stroke=4))
                text(cv, "LEGAL NAME", x + 115, -12, font("bold", 18), paint("#777777", a), "center")
                tail = s.replace("[NAME]", "")
                if tail:
                    text(cv, tail, x + 236, 0, f, paint((10, 10, 14), a, stroke=12))
                    text(cv, tail, x + 236, 0, f, paint(fill, a))
            elif "§§" in s:
                r = random.Random(int(t * 20))
                for c_i, ch_ in enumerate(s):
                    cx = x + c_i * wd / max(1, len(s))
                    text(cv, ch_, cx + r.uniform(-4, 4), r.uniform(-6, 6), f,
                         paint(r.choice([(255, 60, 110), (60, 255, 210), (255, 255, 255)]), a))
            else:
                text(cv, s, x, 0, f, paint((0, 0, 0), 0.35 * fade, blur=6))
                text(cv, s, x, 0, f, paint((10, 10, 14), a, stroke=12))
                text(cv, s, x, 0, f, paint(fill, a))
            x += wd + space
        cv.restore()

    def big_line(self, cv, t, L):
        rel = t - L["start"]
        words, _ = self.chunks[L["id"]]
        shown = [w[0] for w in words if w[1] - 0.05 <= rel]
        a = clamp(rel / 0.3) * (1 - prog(t, L["end"] + 0.25, L["end"] + 0.4))
        f = font("serif_bi", 76)
        lines, cur = [], ""
        for w in shown:
            if text_w((cur + " " + w).strip(), f) > 900:
                lines.append(cur)
                cur = w
            else:
                cur = (cur + " " + w).strip()
        lines.append(cur)
        y0 = 880 - (len(lines) - 1) * 46
        col = SPEAKERS[L["who"]][1]
        for i, s in enumerate(lines):
            text(cv, s, W / 2, y0 + i * 92, f, paint((20, 16, 40), 0.5 * a, stroke=10), "center")
            text(cv, s, W / 2, y0 + i * 92, f, paint(mix(col, (255, 255, 255), 0.5), a), "center")
