"""Per-frame scene context, captions and transitions."""
import bisect
import math
import random

from draw import (INK, WHITE, W, H, POSES, Pose, blend_params, clamp, draw_char, emo_params,
                  font, lerp, pose_lerp, rgba, rrect, smooth, star, text, text_w, wrap, fill_stroke,
                  ease_out_back, ramp)
from script import VOICES
from voice import norm

FPS = 30
_blinks = {}
_scene_beats = {}
_chunks = {}


def blink_value(name, t):
    if name not in _blinks:
        r = random.Random(sum(map(ord, name)) * 31 + 7)
        ts, x = [], r.uniform(0.5, 2.0)
        while x < 2000:
            ts.append(x)
            x += r.uniform(2.0, 4.8)
            if r.random() < 0.15:  # occasional double blink
                ts.append(x)
                x += 0.3
        _blinks[name] = ts
    ts = _blinks[name]
    i = bisect.bisect_right(ts, t) - 1
    if i < 0:
        return 0.0
    d = t - ts[i]
    if d > 0.17:
        return 0.0
    return 1 - abs(d - 0.085) / 0.085


def cam(ctx, zoom, cx, cy):
    ctx.translate(cx, cy)
    ctx.scale(zoom, zoom)
    ctx.translate(-cx, -cy)


class S:
    def __init__(self, ctx, tl, mouth, rnd, si, t):
        self.ctx, self.tl, self.si, self.t = ctx, tl, si, t
        self.sc = tl["scenes"][si]
        self.t0 = self.sc["start"]
        self.lt = t - self.t0
        self.dur = self.sc["end"] - self.t0
        if si not in _scene_beats:
            _scene_beats[si] = [b for b in tl["beats"] if b["scene"] == si]
        self.beats = _scene_beats[si]
        self.tags = {b["tag"]: b for b in self.beats if b["tag"]}
        self.mouth, self.rnd = mouth, rnd
        self.f = int(round(t * FPS))

    # --- timing
    def tb(self, tag):
        return self.tags[tag]["start"] - self.t0

    def te(self, tag):
        return self.tags[tag]["end"] - self.t0

    def since(self, tag):
        return self.lt - self.tb(tag)

    def wt(self, tag, word, nth=0, end=False):
        """Local time at which a given word is spoken inside a beat."""
        b = self.tags[tag]
        hits = [w for w in b["words"] if norm(w[0]).startswith(norm(word))]
        if not hits:
            return self.tb(tag)
        w = hits[min(nth, len(hits) - 1)]
        return (w[2] if end else w[1]) - self.t0

    def during(self, tag, pad=0.0):
        return self.tb(tag) - pad <= self.lt <= self.te(tag) + pad

    def speaking(self, name):
        return any(b["who"] == name and b["start"] <= self.t <= b["end"] for b in self.beats)

    def current_speaker(self):
        for b in self.beats:
            if b["who"] and b["start"] <= self.t <= b["end"]:
                return b["who"]
        return None

    # --- characters
    def emo(self, name, extra=None, blend=0.35):
        keys = [(b["start"] - self.t0, b["emo"][name]) for b in self.beats if name in b["emo"]]
        if extra:
            keys = sorted(keys + list(extra), key=lambda k: k[0])
        if not keys:
            return emo_params("neutral")
        prev = cur = keys[0][1]
        tch = -10.0
        for tk, e in keys:
            if self.lt >= tk:
                if e != cur:
                    prev, cur, tch = cur, e, tk
        k = smooth((self.lt - tch) / blend)
        return blend_params(emo_params(prev), emo_params(cur), k)

    def arms(self, spec, blend=0.3):
        """spec: pose name, explicit angle tuple, or a list of (local_time, pose) keys."""
        if isinstance(spec, list):
            prev = cur = spec[0][1]
            tch = -10.0
            for tk, p in spec:
                if self.lt >= tk:
                    prev, cur, tch = cur, p, tk
            k = smooth((self.lt - tch) / blend)
            arms = pose_lerp(prev, cur, k)
            cur_name = cur if isinstance(cur, str) else None
        else:
            cur_name = spec if isinstance(spec, str) else None
            arms = POSES[spec] if isinstance(spec, str) else spec
        if cur_name in ("wave", "wave2"):
            wig = math.sin(self.t * 11) * 22
            arms = (arms[0] if cur_name == "wave" else (arms[0][0], arms[0][1] + wig),
                    (arms[1][0], arms[1][1] + wig))
        return arms

    def pose(self, name, arms="down", look=(0.0, 0.1), emo=None, extra_emo=None, blink=None,
             **kw):
        if isinstance(emo, str):
            e = emo_params(emo)
        elif emo is None:
            e = self.emo(name, extra_emo)
        else:
            e = emo
        m = self.mouth.get(name)
        r = self.rnd.get(name)
        f = min(self.f, len(m) - 1) if m is not None else 0
        return Pose(emo=e, mouth=float(m[f]) if m is not None else 0.0,
                    rnd=float(r[f]) if r is not None else 0.0, look=look,
                    blink=blink_value(name, self.t) if blink is None else blink,
                    arms=self.arms(arms), t=self.t, **kw)

    def char(self, name, x, y, s=1.0, **kw):
        return draw_char(self.ctx, name, x, y, s, self.pose(name, **kw))

    def lumi(self, x, y, s=0.7, look=(0.0, 0.15), **kw):
        return draw_char(self.ctx, "lumi", x, y, s, self.pose("lumi", look=look, **kw))

    def shake(self, at, dur=0.35, amp=10):
        d = self.lt - at
        if 0 <= d <= dur:
            k = (1 - d / dur) * amp
            return (math.sin(d * 80) * k, math.cos(d * 67) * k)
        return (0, 0)

    def pop(self, at, dur=0.45):
        """Scale for a springy pop-in starting at `at`."""
        return ease_out_back(clamp((self.lt - at) / dur))


def walk_x(lt, keys):
    """Return (x, phase, amount) for a character walking between keyframes (linear)."""
    if lt <= keys[0][0]:
        return keys[0][1], 0.0, 0.0
    for (t0, x0), (t1, x1) in zip(keys, keys[1:]):
        if lt <= t1:
            k = clamp((lt - t0) / (t1 - t0)) if t1 > t0 else 1
            x = lerp(x0, x1, k)
            moving = x0 != x1
            return x, abs(x - keys[0][1]) * 0.045, (1.0 if moving else 0.0)
    return keys[-1][1], abs(keys[-1][1] - keys[0][1]) * 0.045, 0.0


# ------------------------------------------------------------------ captions
CAP_SIZE = 58
CAP_MAXW = 800
CAP_Y = 1345
CAP_H = 210


def _chunks_for(ctx, beat):
    """Split a line into caption cards: sentences wrap to lines, lines pair into cards."""
    key = (beat["scene"], beat["idx"])
    if key in _chunks:
        return _chunks[key]
    font(ctx, CAP_SIZE)
    words = beat["words"]
    phrases, cur = [], []
    for i, (w, s, e) in enumerate(words):
        cur.append(i)
        if w[-1] in ".?!" and i < len(words) - 1:
            phrases.append(cur)
            cur = []
    if cur:
        phrases.append(cur)
    # merge very short sentences into their neighbour ("Hey! Who left this here?")
    merged = []
    for ph in phrases:
        if merged and (len(ph) <= 2 or len(merged[-1]) <= 2):
            merged[-1] = merged[-1] + ph
        else:
            merged.append(ph)
    chunks = []
    for ph in merged:
        lines, line = [], []
        for i in ph:
            trial = " ".join(words[j][0] for j in line + [i])
            if line and text_w(ctx, trial) > CAP_MAXW:
                lines.append(line)
                line = [i]
            else:
                line.append(i)
        if line:
            lines.append(line)
        group = [lines[k:k + 2] for k in range(0, len(lines), 2)]
        if len(group) > 1 and len(group[-1]) == 1 and len(group[-1][0]) <= 2:
            group[-2] = group[-2] + group[-1]
            group.pop()
        chunks.extend(group)
    _chunks[key] = chunks
    return chunks


def draw_captions(ctx, tl, t):
    beat = None
    for b in tl["beats"]:
        if b["who"] and b["start"] - 0.12 <= t <= b["end"] + 0.35:
            beat = b
            if t <= b["end"]:
                break
    if beat is None or not beat["words"]:
        return
    a = clamp((t - (beat["start"] - 0.12)) / 0.12) * clamp((beat["end"] + 0.35 - t) / 0.15)
    chunks = _chunks_for(ctx, beat)
    words = beat["words"]
    ci = 0
    for i, ch in enumerate(chunks):
        if words[ch[0][0]][1] - 0.05 <= t:
            ci = i
    chunk = chunks[ci]
    cur = -1
    for i, (w, s, e) in enumerate(words):
        if s - 0.03 <= t:
            cur = i
    name, color = VOICES[beat["who"]][2], VOICES[beat["who"]][3]
    x0, w0 = 80, W - 160
    y0 = CAP_Y
    ctx.save()
    if a < 1:
        ctx.push_group()
    box_h = CAP_H if len(chunk) <= 2 else CAP_H + 70
    rrect(ctx, x0 + 6, y0 + 10, w0, box_h, 40)
    rgba(ctx, (0, 0, 0), 0.18)
    ctx.fill()
    rrect(ctx, x0, y0, w0, box_h, 40)
    fill_stroke(ctx, WHITE, INK, 5)
    # name tag
    font(ctx, 34)
    nw = text_w(ctx, name) + 44
    rrect(ctx, x0 + 36, y0 - 26, nw, 54, 27)
    fill_stroke(ctx, color, INK, 4.5)
    text(ctx, name, x0 + 36 + nw / 2, y0 + 12, 34, INK)
    # words
    font(ctx, CAP_SIZE)
    nl = len(chunk)
    lh = CAP_SIZE * 1.22
    ty = y0 + box_h / 2 - (nl * lh) / 2 + CAP_SIZE * 0.82
    for li, idxs in enumerate(chunk):
        line = " ".join(words[i][0] for i in idxs)
        lw = text_w(ctx, line)
        x = W / 2 - lw / 2
        for i in idxs:
            wtxt = words[i][0]
            ww = text_w(ctx, wtxt)
            if i == cur:
                rrect(ctx, x - 8, ty + li * lh - CAP_SIZE * 0.86, ww + 16, CAP_SIZE * 1.12, 14)
                rgba(ctx, color, 0.55)
                ctx.fill()
            col = INK if i <= cur else (0.45, 0.45, 0.55)
            text(ctx, wtxt, x, ty + li * lh, CAP_SIZE, col, align="left")
            x += ww + text_w(ctx, " ")
    if a < 1:
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)
    ctx.restore()


# ------------------------------------------------------------------ transitions
WIPE = 0.32
WIPE_COLORS = [(1.0, 0.76, 0.18), (0.27, 0.76, 0.69), (0.98, 0.6, 0.46), (0.56, 0.53, 0.82),
               (0.64, 0.84, 0.32)]


def draw_wipe(ctx, tl, t):
    for si, sc in enumerate(tl["scenes"]):
        if si == 0:
            continue
        c = sc["start"] + 0.2
        if abs(t - c) < WIPE:
            k = (t - (c - WIPE)) / (2 * WIPE)
            k = smooth(k) * 0.6 + k * 0.4
            left = lerp(W + 80, -1.7 * W - 80, k)
            col = WIPE_COLORS[si % len(WIPE_COLORS)]
            ctx.save()
            ctx.move_to(left + 220, 0)
            ctx.line_to(left + 1.7 * W, 0)
            ctx.line_to(left + 1.7 * W - 220, H)
            ctx.line_to(left, H)
            ctx.close_path()
            rgba(ctx, col)
            ctx.fill_preserve()
            rgba(ctx, INK)
            ctx.set_line_width(10)
            ctx.stroke()
            for i in range(9):
                sx = left + 300 + (i * 237) % int(1.4 * W)
                sy = 200 + (i * 431) % 1500
                star(ctx, sx, sy, 26 + (i % 3) * 10, WHITE, 0.8)
            ctx.restore()
            return


def scene_at(tl, t):
    idx = 0
    for i, sc in enumerate(tl["scenes"]):
        if t >= sc["start"] + (0.2 if i else 0):
            idx = i
    return idx
