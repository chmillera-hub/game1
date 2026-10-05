"""Timeline builder + renderer.

A Part is a list of Shots. Each Shot has a set, a camera, actors and timed events. Script code
moves a cursor (`shot.t`) forward with `say`, `think`, `narr`, `wait`; dialogue timing comes from
the real synthesized voice clips, so the animation is always in sync with the audio."""
import math
import os
import random
import subprocess
import multiprocessing as mp
import numpy as np
import cairo

from .keys import Keyed, State
from .characters import draw_actor
from .sets import SETS
from .draw import (OUT, TAU, hexc, src, ell, rrect, fs, fill, text, wrap, cloud, heart, star, poly, line,
                   radial, lin)
from . import audio

W, H = 1080, 1920
FPS = 30

SPEAKERS = {
    "cartman": ("CARTMAN", "#d8382b"),
    "pc": ("PC PRINCIPAL", "#2a7fd0"),
    "chad": ("EMOTIONAL CHAD", "#ff4f8e"),
    "narrator": ("NARRATOR", "#b8902a"),
    "broA": ("GYM BRO #1", "#6a707c"),
    "broB": ("GYM BRO #2", "#3a3a48"),
    "friend1": ("FRIEND", "#8b4fd0"),
    "friend2": ("OTHER FRIEND", "#3f9e5a"),
    "heckler": ("HECKLER", "#e07a14"),
    "hecklerpal": ("HECKLER'S BUDDY", "#606a7a"),
    "kid1": ("KID", "#4a6a8a"),
    "kid2": ("KID", "#4a6a8a"),
    "kid3": ("KID", "#4a6a8a"),
    "kid4": ("KID", "#4a6a8a"),
}

HEAD_TOP = {"cartman": 335, "pc": 600, "chad": 610, "broA": 640, "broB": 640, "slug": 260}


class Actor(Keyed):
    def __init__(self, kind, voice=None, **init):
        init.setdefault("layer", 0)
        super().__init__(**init)
        self.kind = kind
        self.voice = voice or kind
        self.phase = random.Random(hash(kind) % 1000 + len(init)).random() * 10
        self.lines = []  # (t0, env, dur)

    def talk_at(self, t):
        for t0, env, dur in self.lines:
            if t0 <= t < t0 + dur:
                i = int((t - t0) * FPS)
                return float(env[min(i, len(env) - 1)])
        return 0.0

    def head_top(self):
        return HEAD_TOP.get(self.kind, 290)


class Line:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def envelope(x):
    hop = audio.SR // FPS
    n = max(1, len(x) // hop)
    rms = np.array([np.sqrt(np.mean(x[i * hop:(i + 1) * hop] ** 2)) for i in range(n)])
    if rms.max() > 0:
        rms = rms / np.percentile(rms, 95)
    rms = np.clip(rms * 1.1, 0, 1)
    # open-close flutter so the mouth doesn't just hang open on long vowels
    flutter = 0.75 + 0.25 * np.sin(np.arange(n) * 2.1)
    rms = rms * flutter
    rms[rms < 0.12] = 0
    return rms


class Shot:
    def __init__(self, _owner, _set_name, **params):
        self.part = _owner
        self.set = _set_name
        self.P = Keyed(**params)
        self.cam = Keyed(cx=540.0, cy=960.0, zoom=1.0, rot=0.0, shake=0.0)
        self.actors = []
        self.t = 0.0
        self.lines = []
        self.sfx_ev = []
        self.music_ev = []
        self.overlays = []
        self.dur = None
        self.t0 = 0.0

    # -- building -------------------------------------------------------------------------
    def actor(self, _kind, voice=None, **init):
        a = Actor(_kind, voice, **init)
        self.actors.append(a)
        return a

    def camera(self, t=None, dur=0.0, ease="inout", **kv):
        t = self.t if t is None else t
        if dur > 0:
            self.cam.to(t, dur, ease, **kv)
        else:
            self.cam.set(t, **kv)
        return self

    def param(self, t=None, dur=0.0, ease="inout", **kv):
        t = self.t if t is None else t
        if dur > 0:
            self.P.to(t, dur, ease, **kv)
        else:
            self.P.set(t, **kv)
        return self

    def say(self, who, text, style="say", gap=0.2, pre=0.0, caption=None, voice=None, fx=None,
            speed=None, pitch=None, at=None, advance=True, **expr):
        """`who` is an Actor or a voice key string (off-screen speaker)."""
        if isinstance(who, Actor):
            vkey = voice or who.voice
        else:
            vkey = voice or who
        if fx is None:
            fx = {"think": "thought", "whisper": "whisper", "mutter": "whisper", "shout": "shout"}.get(style)
        x = audio.tts(vkey, text, fx=fx, speed=speed, pitch=pitch)
        dur = len(x) / audio.SR
        t0 = (self.t if at is None else at) + pre
        if isinstance(who, Actor):
            if expr:
                who.set(t0, **expr)
            if style != "think":
                who.lines.append((t0, envelope(x), dur))
        cap = caption if caption is not None else text.replace("[bleep]", "[BLEEP]")
        import re
        cap = re.sub(r"\[bleep:[0-9.]+\]", "[BLEEP]", cap)
        ln = Line(t0=t0, dur=dur, audio=x, who=who, vkey=vkey, text=cap, style=style)
        self.lines.append(ln)
        if style == "think" and isinstance(who, Actor):
            self.overlays.append(dict(kind="bubble", t0=t0 - 0.1, dur=dur + 0.3, actor=who, icon="..."))
        if advance:
            self.t = t0 + dur + gap
        return t0, t0 + dur

    def think(self, who, text, icon="...", **kw):
        kw.setdefault("gap", 0.3)
        t0, t1 = self.say(who, text, style="think", **kw)
        self.overlays[-1]["icon"] = icon
        return t0, t1

    def narr(self, text, **kw):
        kw.setdefault("gap", 0.35)
        return self.say("narrator", text, style="narr", **kw)

    def wait(self, d):
        self.t += d
        return self

    def sfx(self, name, at=None, gain=1.0, d=None):
        t = self.t if at is None else at
        x = audio.get_sfx(name, d)
        self.sfx_ev.append((t, x, gain))
        return len(x) / audio.SR

    def music(self, cue, at=None, gain=0.5, fade=0.4):
        t = self.t if at is None else at
        self.music_ev.append((t, cue, gain, fade))
        return self

    def overlay(self, kind, at=None, dur=1.0, **params):
        t = self.t if at is None else at
        self.overlays.append(dict(kind=kind, t0=t, dur=dur, **params))
        return self

    def cc(self, text, dur=1.5, at=None):
        """Closed-caption style description of a non-speech sound."""
        t = self.t if at is None else at
        self.lines.append(Line(t0=t, dur=dur, audio=None, who=None, vkey=None, text=text, style="cc"))
        return self

    def end(self, tail=0.0):
        self.dur = self.t + tail
        return self


DEFAULT_THEME = dict(
    cap_box=(0.07, 0.06, 0.1, 0.72), cap_text=(1, 1, 1), shout_text="#ffe14a", whisper_text="#cfd6ff",
    think_box=(1, 1, 1, 0.92), think_text=None, narr_box=(0.1, 0.08, 0.05, 0.72), narr_text="#ffe9a8",
    cc_box=(0, 0, 0, 0.55), cc_text="#d8d8e0", tag_font="Luckiest Guy", tag_text=(1, 1, 1),
    chip_box=(0, 0, 0, 0.45), chip_text="#f4c430", chip_font="Luckiest Guy", post=None, twos=False,
    cap_border=None,
)


class Part:
    def __init__(self, num, subtitle, slug, theme=None):
        self.theme = dict(DEFAULT_THEME, **(theme or {}))
        self.num = num
        self.subtitle = subtitle
        self.slug = slug
        self.shots = []
        self.total = 0.0
        self.captions = []

    def shot(self, set_name, **params):
        if self.shots and self.shots[-1].dur is None:
            self.shots[-1].end()
        s = Shot(self, set_name, **params)
        self.shots.append(s)
        return s

    def finalize(self):
        if self.shots and self.shots[-1].dur is None:
            self.shots[-1].end()
        t = 0.0
        for s in self.shots:
            s.t0 = t
            t += s.dur
            # mood_at helper for crowd ripple
            s.P.set(0, mood_at=_mood_fn(s.P))
        self.total = t
        self._build_captions()
        return self

    # -- captions ---------------------------------------------------------------------------
    def _build_captions(self):
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 10, 10)
        c = cairo.Context(surf)
        caps = []
        for s in self.shots:
            for ln in s.lines:
                style = ln.style
                fam, size, maxw = ("Patrick Hand", 60, 880) if style == "think" else ("Fredoka", 52, 900)
                if style == "narr":
                    fam, size, maxw = "Fredoka", 46, 900
                if style == "cc":
                    fam, size, maxw = "Fredoka", 44, 900
                lines = wrap(c, ln.text, size, maxw, fam, bold=(fam == "Fredoka"))
                pages = [lines[i:i + 2] for i in range(0, len(lines), 2)]
                total_chars = sum(len(" ".join(p)) for p in pages) or 1
                t = s.t0 + ln.t0
                end = s.t0 + ln.t0 + ln.dur
                for p in pages:
                    d = (end - (s.t0 + ln.t0)) * len(" ".join(p)) / total_chars
                    caps.append(dict(t0=t, t1=t + d, lines=p, style=style, vkey=ln.vkey, fam=fam, size=size,
                                     full=ln.text))
                    t += d
        self.captions = caps

    def shot_at(self, t):
        for s in self.shots:
            if s.t0 <= t < s.t0 + s.dur:
                return s
        return self.shots[-1]

    # -- audio ------------------------------------------------------------------------------
    def build_audio(self, path):
        dia, fx, mev = [], [], []
        for s in self.shots:
            for ln in s.lines:
                if ln.audio is not None:
                    dia.append((s.t0 + ln.t0, ln.audio, 1.0))
            for t, x, g in s.sfx_ev:
                fx.append((s.t0 + t, x, g))
            for t, cue, g, f in s.music_ev:
                mev.append((s.t0 + t, cue, g, f))
        mev.sort(key=lambda e: e[0])
        segs = []
        for i, (t, cue, g, f) in enumerate(mev):
            if cue is None:
                continue
            if i + 1 < len(mev):
                t1, _, _, f1 = mev[i + 1]
            else:
                t1, f1 = self.total, 1.0
            segs.append((t, t1, cue, g, f, max(0.03, f1)))
        audio.mix(self.total, dia, fx, segs, path)

    # -- subtitles / screenplay ---------------------------------------------------------------
    def write_srt(self, path):
        def ts(x):
            ms = int(round(x * 1000))
            return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
        out = []
        k = 1
        for s in self.shots:
            for ln in s.lines:
                name = SPEAKERS.get(ln.vkey, ("", ""))[0] if ln.vkey else ""
                prefix = f"{name}: " if name and ln.style not in ("cc",) else ""
                if ln.style == "think":
                    prefix = f"{name} (thinking): "
                out.append(f"{k}\n{ts(s.t0 + ln.t0)} --> {ts(s.t0 + ln.t0 + ln.dur)}\n{prefix}{ln.text}\n")
                k += 1
        with open(path, "w") as f:
            f.write("\n".join(out))


def _mood_fn(P):
    return lambda tt: P.get("mood", tt)


# =============================================================================================
# Rendering
# =============================================================================================
def draw_actors(c, shot, lt, layer, tglobal):
    items = []
    for a in shot.actors:
        S = a.state(lt)
        if (S.layer or 0) != layer or not S.visible:
            continue
        items.append((S.z or 0, a, S))
    items.sort(key=lambda it: it[0])
    for _, a, S in items:
        S["_t"] = lt + a.phase
        talk = a.talk_at(lt)
        if talk > 0:
            S["talk"] = talk
        if S.autoblink and S.eyes not in ("closed", "happy", "squeeze", "spiral", "dots"):
            if (lt + a.phase) % 4.3 < 0.13:
                S["blink"] = 1.0
        x = S.x + (S.shiver or 0) * 5 * math.sin(lt * 70)
        y = S.y - (S.hop or 0)
        sc = S.scale
        breathe = 1 + 0.008 * math.sin(lt * 2.4 + a.phase) * (S.bob or 0)
        if S.walk:
            y -= abs(math.sin((lt + a.phase) * 9)) * 8 * S.walk
        c.save()
        c.translate(x, y)
        if S.rot:
            piv = a.head_top() * sc * 0.45
            c.translate(0, -piv)
            c.rotate(S.rot)
            c.translate(0, piv)
        c.scale(sc * S.facing * S.sx, sc * S.sy * breathe)
        if S.lean:
            c.transform(cairo.Matrix(1, 0, -S.lean, 1, 0, 0))
        if S.alpha < 1:
            c.push_group()
            draw_actor(c, a.kind, S)
            c.pop_group_to_source()
            c.paint_with_alpha(max(0, S.alpha))
        else:
            draw_actor(c, a.kind, S)
        c.restore()


def actor_head(a, lt):
    S = a.state(lt)
    return S.x, S.y - a.head_top() * S.scale, S.scale


def world_to_screen(cam, x, y):
    return (x - cam.cx) * cam.zoom + W / 2, (y - cam.cy) * cam.zoom + H / 2


def draw_bubble(c, ov, lt, cam):
    """Thought bubble drawn in screen space at a constant size, anchored to the actor's head."""
    a = ov["actor"]
    u = (lt - ov["t0"]) / ov["dur"]
    if u < 0 or u > 1:
        return
    hx, hy, sc = actor_head(a, lt)
    sx, sy = world_to_screen(cam, hx, hy)
    k = min(1.0, (lt - ov["t0"]) / 0.25) * min(1.0, (ov["t0"] + ov["dur"] - lt) / 0.2)
    if k <= 0.05:
        return
    side = ov.get("side", 1 if sx < W / 2 + 60 else -1)
    bw, bh = 300 * k, 190 * k
    bx = min(max(sx + side * 230, 175), W - 175)
    by = min(max(sy - 170, 330), 1250)
    # trail of little puffs from the head to the bubble
    for i, r in enumerate((14, 22)):
        f = (i + 1) / 3
        px = sx + (bx - sx) * f * 0.8
        py = sy + (by + bh * 0.4 - sy) * f * 0.8
        ell(c, px, py, r * k, r * k)
        fs(c, (1, 1, 1), lw=4)
    cloud(c, bx, by, bw, bh, 9)
    fs(c, (1, 1, 1), lw=5)
    icon = ov.get("icon", "...")
    wob = math.sin(lt * 6) * 3
    text(c, icon, bx, by + 22 + wob, (78 if len(icon) < 4 else 56) * k, "Luckiest Guy", OUT)


def draw_overlay(c, ov, lt, shot, part):
    kind = ov["kind"]
    u = (lt - ov["t0"]) / max(ov["dur"], 1e-6)
    if u < 0 or u > 1:
        return
    age = lt - ov["t0"]
    left = ov["t0"] + ov["dur"] - lt
    if kind == "sfx":
        pop = min(1.0, age / 0.12)
        s = (0.3 + 0.7 * pop) * (1 + 0.04 * math.sin(age * 30))
        a = min(1.0, left / 0.2)
        c.save(); c.translate(ov.get("x", 540), ov.get("y", 700)); c.rotate(ov.get("rot", -0.12)); c.scale(s, s)
        text(c, ov["text"], 0, 0, ov.get("size", 120), "Bangers", hexc(ov.get("color", "#ffe14a")), OUT, 16,
             valign="middle", alpha=a)
        c.restore()
    elif kind == "label":
        pop = min(1.0, age / 0.2)
        a = min(1.0, left / 0.25)
        lines = ov["text"] if isinstance(ov["text"], list) else [ov["text"]]
        size = ov.get("size", 44)
        x, y = ov.get("x", 540), ov.get("y", 300)
        wmax = max(len(ln) for ln in lines) * size * 0.58 + 60
        hh = len(lines) * size * 1.25 + 40
        c.save(); c.translate(x, y); c.scale(0.7 + 0.3 * pop, 0.7 + 0.3 * pop); c.rotate(ov.get("rot", -0.03))
        rrect(c, -wmax / 2, -hh / 2, wmax, hh, 18)
        src(c, hexc(ov.get("bg", "#fff3a0")), a); c.fill_preserve(); src(c, OUT, a); c.set_line_width(6); c.stroke()
        yy = -hh / 2 + 20 + size
        for ln in lines:
            text(c, ln, 0, yy, size, "Luckiest Guy", hexc(ov.get("color", "#1d1a24")), alpha=a)
            yy += size * 1.25
        c.restore()
    elif kind == "vignette":
        st = ov.get("strength", 0.6) * min(1.0, age / 0.4) * min(1.0, left / 0.3 + (0 if ov.get("hold") else 0))
        g = radial(540, 900, 1250, (0, 0, 0, 0), (0, 0, 0, st))
        g.add_color_stop_rgba(0.55, 0, 0, 0, 0)
        c.set_source(g); c.paint()
    elif kind == "tint":
        col = hexc(ov.get("color", "#000000"))
        a = ov.get("alpha", 0.3) * min(1.0, age / ov.get("fin", 0.3)) * min(1.0, left / ov.get("fout", 0.3))
        c.rectangle(0, 0, W, H); src(c, col, a); c.fill()
    elif kind == "flash":
        a = (1 - u) * ov.get("alpha", 0.9)
        c.rectangle(0, 0, W, H); src(c, hexc(ov.get("color", "#ffffff")), a); c.fill()
    elif kind == "fade":  # fade from/to black: dir=in|out
        a = (1 - u) if ov.get("dir", "in") == "in" else u
        c.rectangle(0, 0, W, H); src(c, (0, 0, 0), a); c.fill()
    elif kind == "lines":
        cx, cy = ov.get("x", 540), ov.get("y", 800)
        rng = random.Random(int(age * 12))
        for i in range(36):
            a0 = TAU * i / 36 + rng.uniform(-0.05, 0.05)
            r0 = rng.uniform(380, 520)
            poly(c, [(cx + math.cos(a0) * r0, cy + math.sin(a0) * r0),
                     (cx + math.cos(a0 - 0.02) * 1600, cy + math.sin(a0 - 0.02) * 1600),
                     (cx + math.cos(a0 + 0.02) * 1600, cy + math.sin(a0 + 0.02) * 1600)])
            src(c, hexc(ov.get("color", "#1d1a24")), 0.55); c.fill()
    elif kind == "bars":
        k = min(1.0, age / 0.4) * min(1.0, left / 0.3)
        hgt = 170 * k
        c.rectangle(0, 0, W, hgt); fill(c, (0, 0, 0))
        c.rectangle(0, H - hgt, W, hgt); fill(c, (0, 0, 0))
    elif kind == "hearts":
        rng = random.Random(ov.get("seed", 1))
        for i in range(ov.get("n", 10)):
            x0 = rng.uniform(ov.get("x0", 200), ov.get("x1", 880))
            sp = rng.uniform(120, 240)
            y = ov.get("y", 900) - (age * sp + rng.uniform(0, 200))
            a = max(0.0, min(1.0, 1 - (ov.get("y", 900) - y) / 700)) * min(1.0, left / 0.3)
            x = x0 + math.sin(age * 3 + i) * 20
            heart(c, x, y, rng.uniform(18, 34))
            src(c, hexc(rng.choice(["#ff6fa8", "#ff4f7e", "#ffb3c7"])), a); c.fill()
    elif kind == "sparkles":
        rng = random.Random(ov.get("seed", 2))
        for i in range(ov.get("n", 12)):
            x = rng.uniform(ov.get("x0", 150), ov.get("x1", 930))
            y = rng.uniform(ov.get("y0", 500), ov.get("y1", 1200))
            k = max(0.0, math.sin(age * 5 + i * 1.7))
            star(c, x, y, 26 * k, 8 * k, 4)
            src(c, hexc("#fff3a0"), min(1.0, left / 0.3)); c.fill()
    elif kind == "glance":
        # dotted 'knowing look' line between two actors' eyes with a sparkle midpoint
        a1, a2 = ov["a"], ov["b"]
        x1, y1, s1 = actor_head(a1, lt)
        x2, y2, s2 = actor_head(a2, lt)
        y1 += ov.get("dy1", 140) * s1
        y2 += ov.get("dy2", 140) * s2
        k = min(1.0, age / 0.4) * min(1.0, left / 0.3)
        n = 14
        for i in range(1, n):
            uu = i / n
            if uu > k:
                break
            px, py = x1 + (x2 - x1) * uu, y1 + (y2 - y1) * uu - math.sin(uu * math.pi) * 60
            ell(c, px, py, 6, 6); src(c, hexc("#fff3a0")); c.fill()
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2 - 60
        s = k * (0.9 + 0.2 * math.sin(age * 8))
        star(c, mx, my, 34 * s, 12 * s, 4); fs(c, hexc("#fff3a0"), lw=4)
    elif kind == "text":
        a = min(1.0, age / 0.25) * min(1.0, left / 0.25)
        text(c, ov["text"], ov.get("x", 540), ov.get("y", 400), ov.get("size", 70), ov.get("font", "Luckiest Guy"),
             hexc(ov.get("color", "#ffffff")), OUT, ov.get("ow", 10), alpha=a)


def draw_caption(c, cap, t, th=DEFAULT_THEME):
    style = cap["style"]
    vkey = cap["vkey"]
    name, col = SPEAKERS.get(vkey, ("", "#555555")) if vkey else ("", "#555555")
    lines = cap["lines"]
    size = cap["size"]
    fam = cap["fam"]
    lh = size * 1.22
    age = t - cap["t0"]
    pop = min(1.0, age / 0.1)
    boxw = 960
    boxh = len(lines) * lh + 36
    if style == "narr":
        y0 = 250
    elif style == "cc" and th.get("cc_high"):
        y0 = 1370
    else:
        y0 = 1500
    x0 = (W - boxw) / 2
    c.save()
    def col_(v):
        return hexc(v) if isinstance(v, str) else v
    border = th.get("cap_border")
    if style == "think":
        rrect(c, x0, y0, boxw, boxh, 36)
        src(c, th["think_box"]); c.fill_preserve(); src(c, hexc(col)); c.set_line_width(6)
        c.set_dash([18, 12]); c.stroke(); c.set_dash([])
        tcol, ow = col_(th["think_text"]) if th["think_text"] else OUT, 0
    elif style == "narr":
        rrect(c, x0, y0, boxw, boxh, 18)
        src(c, th["narr_box"]); c.fill()
        tcol, ow = col_(th["narr_text"]), 0
    elif style == "cc":
        rrect(c, x0 + 120, y0, boxw - 240, boxh, 18)
        src(c, th["cc_box"]); c.fill()
        tcol, ow = col_(th["cc_text"]), 0
    else:
        rrect(c, x0, y0, boxw, boxh, 22)
        src(c, th["cap_box"]); c.fill_preserve()
        if border:
            src(c, col_(border)); c.set_line_width(4); c.stroke()
        else:
            c.new_path()
        tcol, ow = col_(th["cap_text"]), 0
        if style == "shout":
            tcol = col_(th["shout_text"])
        if style in ("whisper", "mutter"):
            tcol = col_(th["whisper_text"])
    # name tag
    if name and style != "cc":
        tag = name + {"think": " (THINKING)", "whisper": " (WHISPERING)", "mutter": " (MUTTERING)"}.get(style, "")
        tw = len(tag) * 21 + 44
        rrect(c, x0 + 20, y0 - 34, tw, 52, 26)
        fs(c, hexc(col), lw=4)
        text(c, tag, x0 + 20 + tw / 2, y0 + 3, 34, th["tag_font"], col_(th["tag_text"]))
    y = y0 + 22 + size * 0.95
    for ln in lines:
        disp = ln
        if style == "cc":
            disp = ln
        text(c, disp, W / 2, y, size, fam, tcol, OUT, ow, bold=(fam == "Fredoka"), alpha=pop)
        y += lh
    c.restore()


def draw_chip(c, part, t):
    th = part.theme
    rrect(c, W - 240, 150, 200, 58, 29)
    src(c, th["chip_box"]); c.fill()
    tc = th["chip_text"]
    text(c, f"PART {part.num}", W - 140, 192, 36, th["chip_font"], hexc(tc) if isinstance(tc, str) else tc)


def render_frame(c, part, t):
    shot = part.shot_at(t)
    lt = t - shot.t0
    P = shot.P.state(lt)
    cam = shot.cam.state(lt)
    c.save()
    c.set_source_rgb(0, 0, 0)
    c.paint()
    sh = cam.shake or 0
    sx = math.sin(lt * 53) * sh + math.sin(lt * 31) * sh * 0.5
    sy = math.cos(lt * 47) * sh + math.sin(lt * 23) * sh * 0.5
    c.translate(W / 2, H / 2)
    if cam.rot:
        c.rotate(cam.rot)
    c.scale(cam.zoom, cam.zoom)
    c.translate(-cam.cx + sx, -cam.cy + sy)
    alt = math.floor(lt * 15) / 15 if part.theme.get("twos") else lt
    SETS[shot.set](c, lt, P, lambda layer: draw_actors(c, shot, alt, layer, t))
    c.restore()
    for ov in shot.overlays:
        if ov["kind"] == "bubble":
            draw_bubble(c, ov, lt, cam)
        else:
            draw_overlay(c, ov, lt, shot, part)
    if shot.set != "card":
        draw_chip(c, part, t)
    if part.theme.get("post"):
        part.theme["post"](c, t, shot, lt)
    for cap in part.captions:
        if cap["t0"] <= t < cap["t1"]:
            draw_caption(c, cap, t, part.theme)
    # global fade in/out of the part
    if t < 0.3:
        c.rectangle(0, 0, W, H); src(c, (0, 0, 0), 1 - t / 0.3); c.fill()
    if t > part.total - 0.6:
        c.rectangle(0, 0, W, H); src(c, (0, 0, 0), min(1, (t - (part.total - 0.6)) / 0.6)); c.fill()


# ---------------------------------------------------------------------------------------------
_PART = None


def _render_range(args):
    part = _PART
    i0, i1, path, crf = args
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    c = cairo.Context(surf)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "pipe:0", "-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p",
           "-g", str(FPS * 2), path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(i0, i1):
        render_frame(c, part, i / FPS)
        surf.flush()
        p.stdin.write(bytes(surf.get_data()))
    p.stdin.close()
    p.wait()
    return path


def render_video(part, out_path, workdir, workers=4, crf=20, frames=None):
    global _PART
    _PART = part
    os.makedirs(workdir, exist_ok=True)
    n = frames or int(math.ceil(part.total * FPS))
    k = workers
    bounds = [int(n * j / k) for j in range(k + 1)]
    jobs = [(bounds[j], bounds[j + 1], os.path.join(workdir, f"seg{j:02d}.mp4"), crf) for j in range(k)]
    ctx = mp.get_context("fork")
    with ctx.Pool(k) as pool:
        segs = pool.map(_render_range, jobs)
    lst = os.path.join(workdir, "segs.txt")
    with open(lst, "w") as f:
        for s in segs:
            f.write(f"file '{os.path.abspath(s)}'\n")
    wav = os.path.join(workdir, "audio.wav")
    part.build_audio(wav)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", wav,
                    "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k",
                    "-ar", "48000", "-shortest", "-movflags", "+faststart", out_path], check=True)
    return out_path


def render_still(part, t, path):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    c = cairo.Context(surf)
    render_frame(c, part, t)
    surf.write_to_png(path)
