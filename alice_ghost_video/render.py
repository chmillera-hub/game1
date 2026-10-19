"""Draw every frame with Cairo and stream it to ffmpeg.

    python render.py                 # full render -> build/video_lossless.mkv
    python render.py --still 0 12.5  # PNG stills at those times (build/stills/)

Everything is vector-drawn: the ghost from the original drawing (dome head,
three-lobed hem with little foot dots, tall oval eyes and mouth), the
grandmotherly cauldron with its three-ringed rim and U-shaped smile, the
crooked gothic town, the striped kitchen, the Moon Supper table.
"""
import json
import math
import os
import subprocess
import sys
from functools import lru_cache
from multiprocessing import Pool

import cairo
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, 'build')
W, H = 1080, 1920
FPS = 24

TL = json.load(open(os.path.join(BUILD, 'timeline.json')))
LIPS = dict(np.load(os.path.join(BUILD, 'lipsync.npz')))
DURATION = TL['duration']

SUB_FONT = 'Patrick Hand'
TITLE_FONT = 'Mountains of Christmas'
HAND_FONT = 'Schoolbell'

INK = (0.07, 0.06, 0.09)
GHOST = (0.95, 0.94, 0.91)
SUB_COLORS = {'N': (0.93, 0.87, 0.68), 'A': (0.97, 0.95, 1.0), 'S': (1.0, 0.76, 0.48)}


# ── small helpers ────────────────────────────────────────────────────────────
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    return a + (b - a) * t


def smooth(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_out_back(t, s=1.9):
    t = clamp(t) - 1
    return t * t * ((s + 1) * t + s) + 1


def hexc(h, a=None):
    h = h.lstrip('#')
    c = tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return c if a is None else c + (a,)


def hash01(i, seed=0):
    x = math.sin(i * 127.1 + seed * 311.7) * 43758.5453
    return x - math.floor(x)


def vnoise(x, seed=0):
    i = math.floor(x)
    f = x - i
    a, b = hash01(i, seed), hash01(i + 1, seed)
    return lerp(a, b, f * f * (3 - 2 * f)) * 2 - 1


def spline(ctx, pts, closed=True, corners=None, tension=1.0):
    n = len(pts)
    ctx.move_to(*pts[0])
    for i in range(n if closed else n - 1):
        p0 = pts[(i - 1) % n] if (closed or i > 0) else pts[i]
        p1, p2 = pts[i], pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if (closed or i + 2 < n) else p2
        c1 = (0, 0) if corners and corners[i] else ((p2[0] - p0[0]) / 6 * tension, (p2[1] - p0[1]) / 6 * tension)
        c2 = (0, 0) if corners and corners[(i + 1) % n] else ((p3[0] - p1[0]) / 6 * tension, (p3[1] - p1[1]) / 6 * tension)
        ctx.curve_to(p1[0] + c1[0], p1[1] + c1[1], p2[0] - c2[0], p2[1] - c2[1], p2[0], p2[1])
    if closed:
        ctx.close_path()


def ellipse(ctx, x, y, rx, ry, rot=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.scale(max(rx, 0.01), max(ry, 0.01))
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()


def radial(ctx, x, y, r, stops):
    g = cairo.RadialGradient(x, y, 0, x, y, r)
    for off, col in stops:
        g.add_color_stop_rgba(off, *col)
    return g


def linear(x0, y0, x1, y1, stops):
    g = cairo.LinearGradient(x0, y0, x1, y1)
    for off, col in stops:
        g.add_color_stop_rgba(off, *col)
    return g


def heart_path(ctx, x, y, s):
    ctx.move_to(x, y + 0.35 * s)
    ctx.curve_to(x - 0.05 * s, y + 0.25 * s, x - 0.55 * s, y + 0.05 * s, x - 0.5 * s, y - 0.2 * s)
    ctx.curve_to(x - 0.45 * s, y - 0.5 * s, x - 0.05 * s, y - 0.5 * s, x, y - 0.22 * s)
    ctx.curve_to(x + 0.05 * s, y - 0.5 * s, x + 0.45 * s, y - 0.5 * s, x + 0.5 * s, y - 0.2 * s)
    ctx.curve_to(x + 0.55 * s, y + 0.05 * s, x + 0.05 * s, y + 0.25 * s, x, y + 0.35 * s)
    ctx.close_path()


def text_center(ctx, txt, x, y, font, size, fill, outline=None, ow=8, bold=False):
    ctx.select_font_face(font, cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    ext = ctx.text_extents(txt)
    ctx.move_to(x - ext.x_advance / 2, y)
    ctx.text_path(txt)
    if outline:
        ctx.set_source_rgba(*outline)
        ctx.set_line_width(ow)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.stroke_preserve()
    ctx.set_source_rgba(*fill)
    ctx.fill()


# ── timeline lookups ─────────────────────────────────────────────────────────
def last_event(events, t, default=None):
    """(time, value, previous value) of the newest event at or before t."""
    prev, cur, ct = default, default, -1e9
    for et, val in events:
        if et > t:
            break
        prev, cur, ct = cur, val, et
    return ct, cur, prev


SCENE_EV = [(t, s) for t, s in TL['scenes']]
SHOT_EV = [(t, s) for t, s in TL['shots']]
ACTS = {}
for _t, _name, _dur in TL['acts']:
    ACTS.setdefault(_name, []).append((_t, _dur))


def act_time(name, k=0):
    lst = ACTS.get(name, [])
    return lst[k] if k < len(lst) else (1e9, 0)


def act_local(name, t, k=0):
    t0, d = act_time(name, k)
    return t - t0, d


SCENE_START = {s: t for t, s in SCENE_EV}

# extra emotion / gaze keys that live inside actions
EXTRA = {
    'eat_fail_1': {'A': [(0.0, 'eager'), (0.95, 'blissful'), (1.12, 'surprised')],
                   'A.gaze': [(0.0, 'hand'), (1.1, 'candy')]},
    'eat_fail_2': {'A': [(0.0, 'determined'), (0.45, 'eager'), (0.72, 'surprised')],
                   'A.gaze': [(0.0, 'hand'), (0.7, 'candy')]},
    'simmer_wakes': {'S': [(0.0, 'sleepy')]},
    'fetch_drop': {'A': [(0.0, 'eager'), (3.25, 'happy')],
                   'A.gaze': [(0.0, 'floor'), (1.6, 'pot'), (3.9, 'S')],
                   'S': [(3.2, 'gleeful')], 'S.gaze': [(0.0, 'A'), (2.6, 'pot'), (3.9, 'A')]},
    'inhale': {'A': [(0.0, 'curious'), (1.1, 'inhale')], 'A.gaze': [(0.0, 'steam')]},
}
EMO = {c: list(map(tuple, TL['emo'][c])) for c in 'AS'}
GAZE = {c: list(map(tuple, TL['gaze'][c])) for c in 'AS'}
for name, keys in EXTRA.items():
    for t0, _ in ACTS.get(name, []):
        for k, lst in keys.items():
            for dt, val in lst:
                (GAZE if k.endswith('.gaze') else EMO)[k[0]].append((t0 + dt, val))
for c in 'AS':
    EMO[c].sort(key=lambda e: e[0])
    GAZE[c].sort(key=lambda e: e[0])
POSEV = {c: list(map(tuple, TL['pos'][c])) for c in 'AS'}


def scene_at(t):
    return last_event(SCENE_EV, t, 'night')[1]


# ── emotions ─────────────────────────────────────────────────────────────────
A_DEF = dict(brow_y=0, brow_tilt=0, brow_asym=0, lid_top=0.03, lid_tilt=0, lid_bot=0.05, eye_scale=1.0,
             happy=0, smile=0.3, open=0, mouth_w=1.0, squash=0, tilt=0, armL=65, armR=65,
             chestL=0, chestR=0, mouthL=0, mouthR=0, bob=1.0, blush=0.1, glint=1.0)
A_EMO = {
    'content': dict(smile=.45, lid_top=.06, lid_bot=.1, blush=.15),
    'dreamy': dict(brow_y=10, brow_tilt=5, lid_top=.14, lid_bot=.26, smile=.55, tilt=5, blush=.35, bob=1.25, armL=55, armR=55),
    'shy': dict(brow_y=5, brow_tilt=5, lid_top=.22, lid_bot=.22, smile=.5, blush=.75, tilt=-5, chestL=.6),
    'happy': dict(brow_y=6, lid_top=.02, lid_bot=.25, smile=.72, blush=.3, armL=45, armR=45),
    'curious': dict(brow_y=4, brow_asym=10, lid_top=.08, smile=.12, mouth_w=.8, tilt=9),
    'eager': dict(brow_y=9, lid_top=0, eye_scale=1.07, smile=.8, open=.12, armL=25, armR=25, squash=.03, blush=.25, bob=1.2),
    'surprised': dict(brow_y=16, lid_top=0, eye_scale=1.16, open=.5, smile=-.1, mouth_w=.65, squash=.06, armL=-20, armR=-20),
    'deflated': dict(brow_y=-2, brow_tilt=10, lid_top=.45, lid_tilt=6, smile=-.5, squash=-.07, armL=85, armR=85, tilt=-3, bob=.45),
    'determined': dict(brow_y=-6, brow_tilt=-11, lid_top=.32, lid_tilt=-5, smile=-.05, mouth_w=.7, armL=15, armR=15, squash=.03),
    'startled': dict(brow_y=20, brow_tilt=3, lid_top=0, eye_scale=1.2, open=.6, smile=-.15, mouth_w=.65, squash=.09, armL=-35, armR=-35, bob=.6),
    'embarrassed': dict(brow_y=6, brow_tilt=11, lid_top=.25, lid_bot=.15, smile=.12, blush=.85, tilt=-6, mouthL=.8, mouthR=.8),
    'hurt': dict(brow_y=3, brow_tilt=14, lid_top=.38, lid_tilt=8, smile=-.4, squash=-.03, armL=80, chestR=.95, bob=.7, glint=1.15),
    'sad': dict(brow_y=2, brow_tilt=13, lid_top=.42, lid_tilt=8, smile=-.45, squash=-.035, armL=80, armR=80, bob=.7, glint=1.15),
    'wistful': dict(brow_y=4, brow_tilt=9, lid_top=.3, lid_tilt=4, smile=.08, armL=72, armR=72, chestR=.5),
    'wistful_smile': dict(brow_y=5, brow_tilt=8, lid_top=.3, lid_bot=.15, lid_tilt=3, smile=.38, armL=70, armR=70, chestR=.5),
    'hopeful': dict(brow_y=11, brow_tilt=8, lid_top=.04, eye_scale=1.08, smile=.22, glint=1.45, chestL=.5, chestR=.5),
    'realizing': dict(brow_y=15, brow_tilt=4, lid_top=0, eye_scale=1.15, open=.35, smile=.05, mouth_w=.6, glint=1.5, squash=.04),
    'amazed': dict(brow_y=14, lid_top=.04, eye_scale=1.12, open=.3, smile=.32, glint=1.5, armL=-5, armR=-5, blush=.4),
    'inhale': dict(lid_top=1.0, brow_y=7, brow_tilt=2, smile=.15, open=.28, mouth_w=.5, squash=.07, armL=40, armR=40, bob=.4),
    'joyful': dict(brow_y=13, happy=.95, smile=1.0, open=.45, squash=.05, armL=-50, armR=-50, blush=.75, bob=1.5),
    'giggly': dict(brow_y=8, happy=.85, smile=.9, open=.2, blush=.85, tilt=6, mouthL=.9, mouthR=.3),
    'blissful': dict(brow_y=8, happy=1.0, smile=.85, blush=.55, tilt=8, bob=1.2, chestL=.5, chestR=.5),
    'touched': dict(brow_y=9, brow_tilt=9, lid_top=.3, lid_bot=.3, smile=.5, blush=.6, chestL=.8, chestR=.8, glint=1.4),
    'beaming': dict(brow_y=10, happy=.65, smile=1.0, open=.3, armL=-25, armR=-25, blush=.55, bob=1.3),
}
S_DEF = dict(lid_top=.3, lid_bot=.15, lid_tilt=0, brow_y=0, brow_tilt=0, brow_asym=0, happy=0, smile=.4,
             open=0, mouth_w=1.0, squash=0, tilt=0, glow=.6, glint=1.0)
S_EMO = {
    'asleep': dict(lid_top=1, smile=.25, glow=.35, brow_y=-3),
    'sleepy': dict(lid_top=.62, lid_bot=.1, smile=.3, glow=.45),
    'amused': dict(lid_top=.38, lid_bot=.2, brow_asym=9, smile=.6),
    'curious': dict(lid_top=.15, brow_y=7, brow_asym=11, smile=.2),
    'gentle': dict(lid_top=.32, lid_bot=.25, brow_tilt=5, smile=.5),
    'concerned': dict(lid_top=.3, brow_y=4, brow_tilt=13, smile=.02),
    'sad': dict(lid_top=.45, brow_tilt=13, lid_tilt=6, smile=-.3, glow=.45),
    'thoughtful': dict(lid_top=.3, brow_y=6, brow_asym=7, smile=.15),
    'warm': dict(lid_top=.28, lid_bot=.32, brow_y=4, brow_tilt=3, smile=.65, glow=.7),
    'mischievous': dict(lid_top=.36, lid_bot=.22, brow_asym=15, brow_tilt=-6, smile=.85, glow=.75),
    'gleeful': dict(happy=.6, brow_y=9, smile=.95, open=.2, glow=.9, squash=.03),
    'tender': dict(lid_top=.36, lid_bot=.36, brow_tilt=7, smile=.55, glow=.75),
    'laughing': dict(happy=1, brow_y=10, smile=1, open=.65, glow=1.0),
}


def emo_params(c, t):
    base, table, default = (A_DEF, A_EMO, 'content') if c == 'A' else (S_DEF, S_EMO, 'asleep')
    events = EMO[c]
    # walk the events, blending each new emotion in over BLEND seconds
    BLEND = 0.4
    cur = dict(base, **table[default])
    for et, name in events:
        if et > t:
            break
        target = dict(base, **table[name])
        w = smooth((t - et) / BLEND)
        cur = {k: lerp(cur[k], target[k], w) for k in base}
    return cur


GAZE_DIR = {'cam': (0, 0.05), 'up': (0.1, -1), 'floor': (0.15, 1), 'away': (0.85, 0.45),
            'chest': (0.05, 1), 'self': (0.45, 0.85)}


def gaze_vec(c, t, look_targets, me):
    """Blend between gaze targets with quick, saccade-like 0.15 s moves."""
    events = GAZE[c]
    cur = (0.0, 0.05)
    for et, name in events:
        if et > t:
            break
        tgt = resolve_gaze(name, look_targets, me)
        w = smooth((t - et) / 0.16)
        cur = (lerp(cur[0], tgt[0], w), lerp(cur[1], tgt[1], w))
    # tiny idle saccades keep the eyes alive
    k = math.floor(t / 1.3 + hash01(int(t / 1.3), 9) * 0.5)
    cur = (cur[0] + 0.07 * (hash01(k, 3 if c == 'A' else 4) - 0.5), cur[1] + 0.05 * (hash01(k, 5) - 0.5))
    return cur


def resolve_gaze(name, targets, me):
    if name in GAZE_DIR:
        return GAZE_DIR[name]
    p = targets.get(name)
    if p is None:
        return (0, 0.05)
    dx, dy = p[0] - me[0], p[1] - me[1]
    d = math.hypot(dx, dy) + 1e-6
    k = min(1.0, d / 160)
    return (dx / d * k, dy / d * k)


def blink_amount(c, t):
    """0 = open, 1 = closed; random natural blinks plus blinks on emotion changes."""
    period_seed = 11 if c == 'A' else 23
    dur = 0.16 if c == 'A' else 0.24
    # random schedule
    k = int(t / 3.3)
    best = 0.0
    for kk in (k - 1, k, k + 1):
        bt = kk * 3.3 + hash01(kk, period_seed) * 2.6
        u = (t - bt) / dur
        if 0 <= u <= 1:
            best = max(best, math.sin(math.pi * u) ** 0.7)
    for et, _ in EMO[c]:
        if et - 0.1 < t < et + dur + 0.1 and hash01(int(et * 10), period_seed) < 0.65:
            u = (t - et - 0.04) / dur
            if 0 <= u <= 1:
                best = max(best, math.sin(math.pi * u) ** 0.7)
    return best


def lip(c, t):
    rate = int(LIPS['rate'])
    i = t * rate
    i0 = int(i)
    arr, br = LIPS[c], LIPS[c + 'b']
    if i0 + 1 >= len(arr) or i0 < 0:
        return 0.0, 0.5
    f = i - i0
    return lerp(arr[i0], arr[i0 + 1], f), lerp(br[i0], br[i0 + 1], f)


def speaking_env(c, t):
    """Slow 'am I mid-line' envelope used for body emphasis."""
    for st, spk, _, dur, _ in TL['speech']:
        if spk == c and st - 0.1 <= t <= st + dur + 0.1:
            return 1.0
    return 0.0


def listener_nod(c, t):
    """Small acknowledging nod shortly after the other character finishes a line."""
    other = 'S' if c == 'A' else 'A'
    for st, spk, _, dur, _ in TL['speech']:
        if spk == other:
            u = (t - (st + dur + 0.15)) / 0.55
            if 0 <= u <= 1:
                return math.sin(math.pi * u)
    return 0.0


# ── world layout ─────────────────────────────────────────────────────────────
POS = {
    'night': {'A': (540, 1000)},
    'kitchen': {'A': (600, 885), 'S': (300, 1240)},
    'supper': {'A': (730, 1110), 'S': (350, 1268)},
    'end': {'A': (850, 1500)},
}
SCALE = {'night': {'A': 0.95}, 'kitchen': {'A': 0.82, 'S': 1.0}, 'supper': {'A': 0.74, 'S': 0.84},
         'end': {'A': 0.42}}
NAMED = {'table': (600, 885), 'talk': (600, 900), 'window': (660, 830), 'by_pot': (545, 905),
         'steam': (420, 845)}
KITCHEN = dict(plate=(880, 1078), window=(790, 430), pot_rim=(300, 1128), floor=1330)
FLOOR_SPOT = {'E': (445, 1350), 'M': (398, 1360)}       # where the sweets end up after rolling
DROP_SPOT = {'M': (285, 975), 'E': (318, 975)}         # where Alice lets go of them over the pot
MOON = {'night': (770, 600), 'supper': (540, 500), 'kitchen': (790, 430)}
BUBBLES = {'L': (245, 560), 'R': (835, 455)}
WISP = (300, 800)


def base_pos(c, t, scene):
    p = POS[scene].get(c)
    if p is None:
        return None
    t_scene = SCENE_START.get(scene, 0)
    cur = p
    for et, name in POSEV[c]:
        if et > t:
            break
        if et < t_scene:
            continue
        tgt = NAMED[name]
        w = smooth((t - et) / 1.1)
        cur = (lerp(cur[0], tgt[0], w), lerp(cur[1], tgt[1], w))
    return cur


# ── candies ──────────────────────────────────────────────────────────────────
def draw_candy(ctx, kind, x, y, r, rot=0.0, alpha=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.push_group()
    if kind == 'E':                                            # eyeball gobstopper
        ctx.arc(0, 0, r, 0, 2 * math.pi)
        ctx.set_source(radial(ctx, -r * .35, -r * .4, r * 1.4, [(0, hexc('#ffffff', 1)), (1, hexc('#d9d2c4', 1))]))
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(max(1.5, r * 0.09))
        ctx.stroke()
        ctx.set_source_rgba(*hexc('#b3263a', 0.85))
        ctx.set_line_width(max(1, r * 0.05))
        for k in range(9):                                     # squiggly veins, like the drawing
            a = k * 2 * math.pi / 9 + 0.3
            ctx.move_to(math.cos(a) * r * .38, math.sin(a) * r * .38)
            for j in range(1, 5):
                rr = r * (.38 + .14 * j)
                aa = a + 0.12 * math.sin(j * 2.1 + k)
                ctx.line_to(math.cos(aa) * rr, math.sin(aa) * rr)
            ctx.stroke()
        ctx.arc(0, 0, r * .4, 0, 2 * math.pi)
        ctx.set_source_rgb(*hexc('#3f9b6e'))
        ctx.fill()
        ctx.arc(0, 0, r * .2, 0, 2 * math.pi)
        ctx.set_source_rgb(*INK)
        ctx.fill()
        ctx.arc(-r * .12, -r * .12, r * .07, 0, 2 * math.pi)
        ctx.set_source_rgb(1, 1, 1)
        ctx.fill()
    else:                                                      # stripey moon-mint
        ctx.arc(0, 0, r, 0, 2 * math.pi)
        ctx.set_source_rgb(*hexc('#f3eadb'))
        ctx.fill_preserve()
        ctx.save()
        ctx.clip()
        ctx.set_source_rgb(*hexc('#6b3a8f'))
        for k in range(-3, 4):
            x0 = k * r * 0.32
            ctx.move_to(x0, -r)
            for j in range(9):
                yy = -r + j * r / 4
                ctx.line_to(x0 + math.sin(j * 1.6) * r * 0.09, yy)
            ctx.set_line_width(r * 0.15)
            ctx.stroke()
        ctx.restore()
        ctx.arc(0, 0, r, 0, 2 * math.pi)
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(max(1.5, r * 0.09))
        ctx.stroke()
        ctx.arc(-r * .35, -r * .4, r * .18, 0, 2 * math.pi)
        ctx.set_source_rgba(1, 1, 1, 0.6)
        ctx.fill()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(alpha)
    ctx.restore()


def bounce_path(u, start, end, times, heights):
    """A gravity drop from `start` to the floor, then shrinking hops to `end`; (x, y, rot)."""
    if u <= times[0]:
        return None
    total = times[-1] - times[0]
    for i in range(len(times) - 1):
        a, b = times[i], times[i + 1]
        if a <= u <= b:
            f = (u - a) / (b - a)
            x0 = lerp(start[0], end[0], (a - times[0]) / total)
            x1 = lerp(start[0], end[0], (b - times[0]) / total)
            if i == 0:
                return lerp(x0, x1, f), lerp(start[1], end[1], f * f), -u * 9
            return lerp(x0, x1, f), end[1] - heights[i] * 4 * f * (1 - f), -u * 9
    return end[0], end[1], -times[-1] * 9


# ── the ghost ────────────────────────────────────────────────────────────────
GHOST_PTS = [(0, -268), (128, -212), (180, -60), (196, 110), (214, 196), (182, 250), (122, 182),
             (96, 262), (34, 300), (-22, 262), (-48, 178), (-92, 272), (-160, 292), (-226, 238),
             (-198, 150), (-182, -50), (-132, -208)]
GHOST_CORNERS = [False] * len(GHOST_PTS)
GHOST_CORNERS[6] = GHOST_CORNERS[10] = True
FEET = [(178, 222, 0.5), (36, 270, 0.0), (-160, 262, -0.3)]


def ghost_outline(g, t, frame):
    sq = g['squash']
    boil = (frame // 3)
    pts = []
    for i, (x, y) in enumerate(GHOST_PTS):
        if y > 120:                                       # the hem ripples
            x += 7 * math.sin(t * 2.3 + y * 0.03 + i)
            y += 5 * math.sin(t * 3.1 + x * 0.025 + i * 0.7)
        x += 1.2 * (hash01(i, boil) - 0.5)
        y += 1.2 * (hash01(i + 40, boil) - 0.5)
        pts.append((x * (1 - sq * 0.55), y * (1 + sq) - sq * 30))
    return pts


def fpos(g, x, y):
    sq = g['squash']
    return x * (1 - sq * 0.55), y * (1 + sq) - sq * 30


def draw_arm(ctx, root, tip, side, width=27):
    dx, dy = tip[0] - root[0], tip[1] - root[1]
    d = math.hypot(dx, dy) + 1e-6
    nx, ny = -dy / d, dx / d
    r = 23
    a = (root[0] + nx * width, root[1] + ny * width)
    b = (root[0] - nx * width, root[1] - ny * width)
    ang = math.atan2(dy, dx)
    ctx.new_path()
    ctx.move_to(*b)
    ctx.curve_to(b[0] + dx * 0.5, b[1] + dy * 0.5, tip[0] - nx * r - dx / d * 10, tip[1] - ny * r - dy / d * 10,
                 tip[0] - nx * r, tip[1] - ny * r)
    ctx.arc(tip[0], tip[1], r, ang - math.pi / 2, ang + math.pi / 2)
    ctx.curve_to(tip[0] + nx * r - dx / d * 10, tip[1] + ny * r - dy / d * 10, a[0] + dx * 0.5, a[1] + dy * 0.5, *a)
    path = ctx.copy_path()
    ctx.close_path()
    ctx.set_source_rgb(*GHOST)
    ctx.fill()
    ctx.new_path()
    ctx.append_path(path)
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(6.5)
    ctx.stroke()


def draw_ghost(ctx, g, t, frame, inside=()):
    ctx.save()
    ctx.translate(g['x'], g['y'])
    ctx.rotate(math.radians(g['tilt']))
    ctx.scale(g['s'] * g.get('flip', 1.0), g['s'])

    # spectral glow
    ctx.arc(0, 0, 420, 0, 2 * math.pi)
    ctx.set_source(radial(ctx, 0, 0, 420, [(0, (0.75, 0.88, 1.0, 0.22 * g.get('glow', 1))),
                                           (1, (0.75, 0.88, 1.0, 0))]))
    ctx.fill()

    pts = ghost_outline(g, t, frame)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)

    def body_path():
        ctx.new_path()
        spline(ctx, pts, corners=GHOST_CORNERS)

    body_path()
    ctx.set_source(radial(ctx, -50, -140, 430, [(0, hexc('#ffffff', 1)), (0.55, GHOST + (1,)),
                                                (1, hexc('#b9c4d6', 1))]))
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(6.5)
    ctx.stroke()

    # inner warmth after the steam soup
    if g.get('inner', 0) > 0.01:
        body_path()
        ctx.save()
        ctx.clip()
        ctx.arc(0, 80, 260, 0, 2 * math.pi)
        ctx.set_source(radial(ctx, 0, 80, 260, [(0, (1.0, 0.82, 0.55, 0.38 * g['inner'])),
                                                (1, (1.0, 0.82, 0.55, 0))]))
        ctx.fill()
        ctx.restore()

    # things seen through the sheet (a swallowed candy falling straight through)
    for kind, x, y, r, rot in inside:
        body_path()
        ctx.save()
        ctx.clip()
        draw_candy(ctx, kind, x, y, r, rot, alpha=0.55)
        ctx.restore()

    # little foot dots
    ctx.set_source_rgb(*INK)
    for fx, fy, rot in FEET:
        x, y = fpos(g, fx, fy)
        x += 7 * math.sin(t * 2.3 + fy * 0.03)
        ellipse(ctx, x, y, 9, 14, rot)
        ctx.fill()

    draw_ghost_face(ctx, g, t)

    # chest heart: hollow outline, later filled with warm light
    if g.get('heart', 0) > 0.01:
        hx, hy = fpos(g, 4, 132)
        a = g['heart']
        fill = g.get('heart_fill', 0)
        pulse = 1 + 0.06 * math.sin(t * 6) * fill
        if fill > 0.01:
            ctx.arc(hx, hy, 90, 0, 2 * math.pi)
            ctx.set_source(radial(ctx, hx, hy, 90, [(0, (1, 0.45, 0.4, 0.45 * fill * a)), (1, (1, 0.45, 0.4, 0))]))
            ctx.fill()
            heart_path(ctx, hx, hy, 62 * pulse)
            ctx.set_source_rgba(*hexc('#e5485e'), a * fill)
            ctx.fill()
        heart_path(ctx, hx, hy, 62 * pulse)
        ctx.set_source_rgba(*hexc('#5a1622'), a)
        ctx.set_line_width(4.5)
        ctx.stroke()

    # arms (drawn over the body edge so they read as part of the sheet)
    for side in (-1, 1):
        key = 'L' if side < 0 else 'R'
        root = fpos(g, side * 176, 12)
        ang = math.radians(g['arm' + key])
        tip = (root[0] + side * 78 * math.cos(ang), root[1] + 78 * math.sin(ang))
        chest = fpos(g, side * 42, 112)
        mouth = fpos(g, side * 36, 40)
        tip = (lerp(tip[0], chest[0], g['chest' + key]), lerp(tip[1], chest[1], g['chest' + key]))
        tip = (lerp(tip[0], mouth[0], g['mouth' + key]), lerp(tip[1], mouth[1], g['mouth' + key]))
        if g.get('tip' + key):
            tip = g['tip' + key]
        draw_arm(ctx, root, tip, side)
        held = g.get('hold' + key)
        if held:
            cx_, cy_ = tip[0] + side * 4, tip[1] + 18
            if key == 'R' and g.get('feed'):
                mx, my = fpos(g, 2, 32)
                cx_, cy_ = lerp(cx_, mx + 6, g['feed']), lerp(cy_, my + 4, g['feed'])
            draw_candy(ctx, held, cx_, cy_, 26)
    ctx.restore()


def draw_eye(ctx, cx, cy, rx, ry, rot, p, gaze, side, blink, body_col=GHOST):
    happy = p['happy']
    lid_top = clamp(max(p['lid_top'], blink, happy * 1.4 - 0.4))
    if happy > 0.5:
        # ^ ^ smiling eyes
        ctx.new_path()
        ctx.move_to(cx - rx * 1.25, cy + ry * 0.15)
        ctx.curve_to(cx - rx * 0.7, cy - ry * 0.75, cx + rx * 0.7, cy - ry * 0.75, cx + rx * 1.25, cy + ry * 0.15)
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(9)
        ctx.stroke()
        return
    if lid_top > 0.93:
        ctx.new_path()
        ctx.move_to(cx - rx * 1.2, cy + ry * 0.05)
        ctx.curve_to(cx - rx * 0.6, cy + ry * 0.45, cx + rx * 0.6, cy + ry * 0.45, cx + rx * 1.2, cy + ry * 0.05)
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(7)
        ctx.stroke()
        return
    ex, ey = cx + gaze[0] * 6, cy + gaze[1] * 5
    ctx.save()
    ellipse(ctx, ex, ey, rx, ry, rot)
    ctx.clip()
    ctx.set_source_rgb(*INK)
    ctx.paint()
    # glint shows where she is looking
    gr = p['glint']
    ellipse(ctx, ex - rx * 0.32 + gaze[0] * rx * 0.55, ey - ry * 0.42 + gaze[1] * ry * 0.4, 6.5 * gr, 11 * gr, rot)
    ctx.set_source_rgb(1, 1, 1)
    ctx.fill()
    ellipse(ctx, ex + rx * 0.28 + gaze[0] * rx * 0.4, ey + ry * 0.3 + gaze[1] * ry * 0.3, 3 * gr, 4 * gr, 0)
    ctx.fill()
    # eyelids, in body colour; lid_tilt > 0 droops the outer corner (sad)
    top = ey - ry
    ly = top + 2 * ry * lid_top
    slope = side * p['lid_tilt'] * 2.4 / rx

    def lid_y(x):
        return ly + slope * (x - ex)
    ctx.set_source_rgb(*body_col)
    ctx.new_path()
    ctx.move_to(ex - rx * 2, lid_y(ex - rx * 2))
    ctx.line_to(ex - rx * 2, top - 60)
    ctx.line_to(ex + rx * 2, top - 60)
    ctx.line_to(ex + rx * 2, lid_y(ex + rx * 2))
    ctx.close_path()
    ctx.fill()
    bot = p['lid_bot']
    if bot > 0.02:
        by = ey + ry - 2 * ry * bot * 0.8
        ctx.new_path()
        ctx.move_to(ex - rx * 2, ey + ry + 40)
        ctx.line_to(ex - rx * 2, by + ry * 0.25)
        ctx.curve_to(ex - rx * 0.6, by - ry * 0.25 * bot, ex + rx * 0.6, by - ry * 0.25 * bot, ex + rx * 2, by + ry * 0.25)
        ctx.line_to(ex + rx * 2, ey + ry + 40)
        ctx.close_path()
        ctx.fill()
    ctx.restore()
    if lid_top > 0.08:
        ctx.new_path()
        ctx.move_to(ex - rx * 1.15, lid_y(ex - rx * 1.15))
        ctx.line_to(ex + rx * 1.15, lid_y(ex + rx * 1.15))
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(4)
        ctx.stroke()


def draw_mouth(ctx, cx, cy, open_, w, smile, depth=118, tongue=True, inner=None):
    hw = w / 2
    lift = smile * 16
    if open_ < 0.06:
        ctx.new_path()
        ctx.move_to(cx - hw * 0.8, cy - lift)
        ctx.curve_to(cx - hw * 0.3, cy + smile * 10, cx + hw * 0.3, cy + smile * 10, cx + hw * 0.8, cy - lift)
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(6.5)
        ctx.stroke()
        return
    h = depth * open_
    top_c = cy - h * 0.38 + smile * 5
    bot_c = cy + h * 0.62 + smile * 10
    ctx.new_path()
    ctx.move_to(cx - hw, cy - lift)
    ctx.curve_to(cx - hw * 0.85, top_c - h * 0.22, cx + hw * 0.85, top_c - h * 0.22, cx + hw, cy - lift)
    ctx.curve_to(cx + hw * 1.0, bot_c + h * 0.3, cx - hw * 1.0, bot_c + h * 0.3, cx - hw, cy - lift)
    ctx.close_path()
    path = ctx.copy_path()
    ctx.set_source_rgb(*(inner or hexc('#1b0c12')))
    ctx.fill()
    if tongue and open_ > 0.3:
        ctx.save()
        ctx.append_path(path)
        ctx.clip()
        ellipse(ctx, cx + hw * 0.1, bot_c + h * 0.12, hw * 0.75, h * 0.32)
        ctx.set_source_rgb(*hexc('#a43a55'))
        ctx.fill()
        ctx.restore()
    ctx.append_path(path)
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(5)
    ctx.stroke()


def draw_ghost_face(ctx, g, t):
    p = g
    es = p['eye_scale']
    gaze = g['gaze']
    ctx.save()
    ctx.translate(gaze[0] * 16, gaze[1] * 9)        # a little head-turn toward what she looks at
    for side, (ex, ey, rot) in ((-1, (-62, -104, 0.10)), (1, (62, -109, -0.10))):
        x, y = fpos(g, ex + gaze[0] * 3, ey + gaze[1] * 2)
        draw_eye(ctx, x, y, 26.5 * es, 50 * es, rot, p, gaze, side, g['blink'])
        # eyebrows
        by = y - 50 * es - 24 - p['brow_y'] + (-p['brow_asym'] if side > 0 else p['brow_asym'] * 0.3)
        tilt = p['brow_tilt'] * 1.3
        inner = (x - side * 22, by - tilt * 0.5)
        outer = (x + side * 24, by + tilt * 0.5)
        ctx.new_path()
        ctx.move_to(*outer)
        ctx.curve_to(lerp(outer[0], inner[0], 0.35), outer[1] - 7, lerp(outer[0], inner[0], 0.7), inner[1] - 6, *inner)
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(7.5)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()
    # blush
    if p['blush'] > 0.02:
        for side in (-1, 1):
            x, y = fpos(g, side * 98, -28)
            ellipse(ctx, x, y, 30, 15)
            ctx.set_source(radial(ctx, x, y, 30, [(0, hexc('#ff8fa8', 0.55 * p['blush'])), (1, hexc('#ff8fa8', 0))]))
            ctx.fill()
    # tear
    tear = g.get('tear', 0)
    if tear > 0:
        x, y = fpos(g, -88, -70)
        prog = clamp((tear - 0.2) / 0.8)
        ty = y + prog * 110
        a = 1 - clamp((tear - 0.85) / 0.15)
        sz = 7 + 5 * clamp(tear / 0.2)
        ctx.new_path()
        ctx.move_to(x, ty - sz * 1.8)
        ctx.curve_to(x + sz, ty - sz * 0.2, x + sz, ty + sz, x, ty + sz)
        ctx.curve_to(x - sz, ty + sz, x - sz, ty - sz * 0.2, x, ty - sz * 1.8)
        ctx.set_source_rgba(*hexc('#a9dcff'), 0.9 * a)
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexc('#2a4f73'), 0.8 * a)
        ctx.set_line_width(2)
        ctx.stroke()
        ellipse(ctx, x - sz * 0.3, ty, sz * 0.25, sz * 0.4)
        ctx.set_source_rgba(1, 1, 1, 0.9 * a)
        ctx.fill()
    mx, my = fpos(g, 2 + gaze[0] * 3, 32)
    draw_mouth(ctx, mx, my, p['open'], 58 * p['mouth_w'], p['smile'])
    ctx.restore()


# ── the cauldron ─────────────────────────────────────────────────────────────
POT = hexc('#2d2b3a')


def draw_cauldron(ctx, c, t, frame):
    ctx.save()
    ctx.translate(c['x'], c['y'])
    ctx.rotate(math.radians(c['tilt']))
    sq = c['squash']
    ctx.scale(c['s'] * (1 - sq * 0.5), c['s'] * (1 + sq))
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    glow = c['glow']
    gcol = c.get('gcol', (0.55, 1.0, 0.78))
    boil = frame // 3

    def jit(i, a=1.3):
        return a * (hash01(i, boil) - 0.5)

    # glow from the brew
    ctx.arc(0, -150, 300, 0, 2 * math.pi)
    ctx.set_source(radial(ctx, 0, -150, 300, [(0, gcol + (0.28 * glow,)), (1, gcol + (0,))]))
    ctx.fill()
    # stubby feet
    for fx in (-100, 0, 100):
        ellipse(ctx, fx, 122 + (8 if fx == 0 else 0), 30, 22)
        ctx.set_source_rgb(*hexc('#1d1b26'))
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(5)
        ctx.stroke()
    # side handles
    for side in (-1, 1):
        ctx.new_path()
        ctx.arc(side * 160, -78, 26, 0, 2 * math.pi)
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(9)
        ctx.stroke()
    # belly
    pts = [(-150 + jit(1), -100), (-176 + jit(2), -20), (-160 + jit(3), 70), (-95, 125 + jit(4)), (0, 140 + jit(5)),
           (95, 125 + jit(6)), (160 + jit(7), 70), (176 + jit(8), -20), (150 + jit(9), -100)]
    ctx.new_path()
    spline(ctx, pts, closed=True)
    ctx.set_source(radial(ctx, -70, -50, 260, [(0, hexc('#5c5a72', 1)), (0.45, POT + (1,)), (1, hexc('#121019', 1))]))
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(6.5)
    ctx.stroke()
    # warm firelight from below
    ctx.new_path()
    spline(ctx, pts, closed=True)
    ctx.save()
    ctx.clip()
    ctx.arc(0, 190, 200, 0, 2 * math.pi)
    ctx.set_source(radial(ctx, 0, 190, 200, [(0, (1, 0.55, 0.2, 0.35 * c.get('fire', 1))), (1, (1, 0.55, 0.2, 0))]))
    ctx.fill()
    ctx.restore()
    # shine
    ctx.new_path()
    ctx.arc(-40, 0, 125, math.radians(195), math.radians(245))
    ctx.set_source_rgba(1, 1, 1, 0.22)
    ctx.set_line_width(10)
    ctx.stroke()
    # rim + brew
    ellipse(ctx, 0, -108, 162, 40)
    ctx.set_source_rgb(*hexc('#3a384b'))
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(6.5)
    ctx.stroke()
    ellipse(ctx, 0, -112, 134, 26)
    bright = clamp(0.45 + 0.55 * glow)
    ctx.set_source(radial(ctx, 0, -112, 140, [(0, (lerp(0.2, 0.85, bright), 1.0, lerp(0.6, 0.9, bright), 1)),
                                              (1, (gcol[0] * 0.45, gcol[1] * 0.6, gcol[2] * 0.5, 1))]))
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(4)
    ctx.stroke()
    # surface bubbles
    for k in range(6):
        ph = (t * (0.6 + 0.25 * glow) + hash01(k, 1)) % 1.0
        bx = -95 + 190 * hash01(k + int(t * (0.6 + 0.25 * glow) + hash01(k, 1)), 2)
        r = 5 + 9 * ph
        ellipse(ctx, bx, -112 + 10 * hash01(k, 4), r, r * 0.6)
        ctx.set_source_rgba(0.9, 1, 0.95, 0.75 * (1 - ph))
        ctx.set_line_width(2.5)
        ctx.stroke()
    # big "blorp" bubbles when she wakes / when sweets go in
    for bt in c.get('blorps', ()):
        u = t - bt
        if 0 <= u <= 0.7:
            r = 16 + 40 * u
            ellipse(ctx, 20, -122 - 30 * u, r, r * 0.8)
            ctx.set_source_rgba(0.85, 1, 0.92, 0.85 * (1 - u / 0.7))
            ctx.set_line_width(4)
            ctx.stroke()
    # the three rings on the rim, as in the drawing
    for k, rx in enumerate((-92, 0, 92)):
        ry = -82 if rx else -70
        ctx.new_path()
        ctx.arc(rx, ry, 12, 0, 2 * math.pi)
        ctx.set_source_rgb(*hexc('#4a4860'))
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(4.5)
        ctx.stroke()

    # face
    p = c
    gaze = c['gaze']
    ctx.save()
    ctx.translate(gaze[0] * 12, gaze[1] * 6)
    for side in (-1, 1):
        ex, ey = side * 52 + gaze[0] * 5, -12 + gaze[1] * 4
        draw_eye(ctx, ex, ey, 14, 19, 0, p, gaze, side, c['blink'], body_col=hexc('#3a3848'))
        # spectacles
        ctx.new_path()
        ctx.arc(ex, ey + 2, 27, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexc('#d9be7a'), 0.95)
        ctx.set_line_width(4)
        ctx.stroke()
        ctx.new_path()
        ctx.arc(ex - 8, ey - 6, 18, math.radians(200), math.radians(250))
        ctx.set_source_rgba(1, 1, 1, 0.35)
        ctx.set_line_width(3)
        ctx.stroke()
        # bushy grey brows
        by = ey - 40 - p['brow_y'] + (-p['brow_asym'] if side > 0 else p['brow_asym'] * 0.3)
        tilt = p['brow_tilt'] * 1.2
        inner = (ex - side * 20, by - tilt * 0.5)
        outer = (ex + side * 26, by + tilt * 0.5 + 3)
        ctx.new_path()
        ctx.move_to(*outer)
        ctx.curve_to(lerp(outer[0], inner[0], 0.35), outer[1] - 9, lerp(outer[0], inner[0], 0.7), inner[1] - 7, *inner)
        ctx.set_source_rgb(*hexc('#b9b6c6'))
        ctx.set_line_width(10)
        ctx.stroke()
    ctx.new_path()
    ctx.move_to(-27, -10)
    ctx.curve_to(-15, -18, 15, -18, 27, -10)
    ctx.set_source_rgba(*hexc('#d9be7a'), 0.95)
    ctx.set_line_width(3.5)
    ctx.stroke()
    # rosy cheeks
    for side in (-1, 1):
        ellipse(ctx, side * 92, 30, 24, 13)
        ctx.set_source(radial(ctx, side * 92, 30, 24, [(0, hexc('#ff8f8f', 0.35)), (1, hexc('#ff8f8f', 0))]))
        ctx.fill()
    # the U-shaped smile from the drawing
    open_ = p['open']
    w = 104 * p['mouth_w']
    smile = p['smile']
    hw = w / 2
    lift = smile * 14
    cy = 52
    depth = 16 + 46 * open_ + 10 * max(0, smile)
    ctx.new_path()
    ctx.move_to(-hw, cy - lift)
    ctx.curve_to(-hw * 0.6, cy - lift + 6 - open_ * 10, hw * 0.6, cy - lift + 6 - open_ * 10, hw, cy - lift)
    ctx.curve_to(hw * 0.95, cy + depth * 1.3, -hw * 0.95, cy + depth * 1.3, -hw, cy - lift)
    ctx.close_path()
    path = ctx.copy_path()
    ctx.set_source(radial(ctx, 0, cy + depth, hw * 1.2, [(0, (0.95, 0.45, 0.15, 1)), (1, (0.22, 0.06, 0.05, 1))]))
    ctx.fill()
    ctx.save()
    ctx.append_path(path)
    ctx.clip()
    ellipse(ctx, 6, cy + depth * 0.95, hw * 0.55, depth * 0.35)
    ctx.set_source_rgb(*hexc('#b8435a'))
    ctx.fill()
    ctx.restore()
    ctx.append_path(path)
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(5.5)
    ctx.stroke()
    ctx.restore()
    ctx.restore()


def draw_steam_squiggles(ctx, x, y, s, t, alpha=0.6):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    for k, dx in enumerate((-55, 0, 55)):
        ctx.new_path()
        for j in range(18):
            yy = -j * 9
            xx = dx + 11 * math.sin(j * 0.55 - t * 3.2 + k * 1.7) * (0.4 + j / 18)
            (ctx.line_to if j else ctx.move_to)(xx, yy - 130)
        ctx.set_source(linear(0, -130, 0, -290, [(0, (0.92, 0.95, 1, alpha)), (1, (0.92, 0.95, 1, 0))]))
        ctx.set_line_width(6)
        ctx.stroke()
    ctx.restore()


# ── backgrounds ──────────────────────────────────────────────────────────────
def stars(ctx, n, y1, seed):
    for i in range(n):
        x = hash01(i, seed) * W
        y = hash01(i, seed + 1) * y1
        r = 0.8 + 1.8 * hash01(i, seed + 2) ** 3
        ctx.arc(x, y, r, 0, 2 * math.pi)
        ctx.set_source_rgba(1, 0.97, 0.88, 0.35 + 0.5 * hash01(i, seed + 3))
        ctx.fill()


def moon(ctx, x, y, r):
    ctx.arc(x, y, r * 2.2, 0, 2 * math.pi)
    ctx.set_source(radial(ctx, x, y, r * 2.2, [(0, hexc('#f6ecc9', 0.35)), (0.45, hexc('#f6ecc9', 0.12)), (1, hexc('#f6ecc9', 0))]))
    ctx.fill()
    ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.set_source(radial(ctx, x - r * .3, y - r * .3, r * 1.4, [(0, hexc('#fbf3da', 1)), (1, hexc('#e3cf9f', 1))]))
    ctx.fill()
    for i in range(7):
        cx = x + (hash01(i, 77) - 0.5) * r * 1.3
        cy = y + (hash01(i, 78) - 0.5) * r * 1.3
        if math.hypot(cx - x, cy - y) > r * 0.8:
            continue
        ellipse(ctx, cx, cy, r * (0.06 + 0.1 * hash01(i, 79)), r * (0.05 + 0.08 * hash01(i, 79)))
        ctx.set_source_rgba(0.72, 0.62, 0.42, 0.22)
        ctx.fill()


def curly_tree(ctx, x, y, h, flip=1, col=hexc('#07070c')):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(flip, 1)
    ctx.set_source_rgb(*col)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    # trunk
    ctx.new_path()
    ctx.move_to(-38, 0)
    ctx.curve_to(-30, -h * 0.4, 10, -h * 0.6, -5, -h)
    ctx.curve_to(20, -h * 0.6, 22, -h * 0.35, 40, 0)
    ctx.close_path()
    ctx.fill()

    def branch(x0, y0, ang, length, width, depth):
        x1 = x0 + math.cos(ang) * length
        y1 = y0 + math.sin(ang) * length
        ctx.new_path()
        ctx.move_to(x0, y0)
        ctx.curve_to(x0 + math.cos(ang - 0.3) * length * 0.5, y0 + math.sin(ang - 0.3) * length * 0.5,
                     x1 - math.cos(ang + 0.4) * length * 0.3, y1 - math.sin(ang + 0.4) * length * 0.3, x1, y1)
        ctx.set_line_width(width)
        ctx.stroke()
        if depth == 0:
            # curl the tip into a little spiral
            r = length * 0.22
            a0 = ang + math.pi / 2
            ctx.new_path()
            for k in range(40):
                f = k / 39
                a = a0 + f * 4.2
                rr = r * (1 - f * 0.85)
                (ctx.line_to if k else ctx.move_to)(x1 + math.cos(a) * rr - math.cos(a0) * r,
                                                     y1 + math.sin(a) * rr - math.sin(a0) * r)
            ctx.set_line_width(max(2, width * 0.8))
            ctx.stroke()
            return
        branch(x1, y1, ang - 0.55, length * 0.68, width * 0.6, depth - 1)
        branch(x1, y1, ang + 0.5, length * 0.6, width * 0.55, depth - 1)

    branch(-5, -h, -math.pi / 2 - 0.35, h * 0.32, 16, 2)
    branch(-8, -h * 0.75, -math.pi / 2 - 1.1, h * 0.3, 12, 2)
    branch(5, -h * 0.65, -math.pi / 2 + 1.0, h * 0.28, 11, 2)
    ctx.restore()


def crooked_house(ctx, x, y, w, h, lean, roof, col, win_col, seed):
    ctx.save()
    ctx.translate(x, y)
    ctx.new_path()
    ctx.move_to(0, 0)
    ctx.line_to(lean * h * 0.1, -h)
    ctx.line_to(w * 0.5 + lean * h * 0.25, -h - roof)
    ctx.line_to(w + lean * h * 0.1, -h)
    ctx.line_to(w, 0)
    ctx.close_path()
    ctx.set_source_rgb(*col)
    ctx.fill()
    for i in range(3):
        if hash01(i, seed) < 0.55:
            wx = w * (0.2 + 0.25 * i) + lean * h * 0.05
            wy = -h * (0.35 + 0.3 * hash01(i, seed + 1))
            ctx.rectangle(wx, wy, w * 0.13, h * 0.13)
            ctx.set_source_rgb(*win_col)
            ctx.fill()
    ctx.restore()


def tombstone(ctx, x, y, w, h, rot, cross=False):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.new_path()
    if cross:
        ctx.rectangle(-w * 0.12, -h, w * 0.24, h)
        ctx.rectangle(-w * 0.45, -h * 0.75, w * 0.9, w * 0.22)
    else:
        ctx.move_to(-w / 2, 0)
        ctx.line_to(-w / 2, -h + w / 2)
        ctx.arc(0, -h + w / 2, w / 2, math.pi, 0)
        ctx.line_to(w / 2, 0)
        ctx.close_path()
    ctx.set_source_rgb(*hexc('#2a3140'))
    ctx.fill_preserve()
    ctx.set_source_rgb(*hexc('#0c0e14'))
    ctx.set_line_width(4)
    ctx.stroke()
    if not cross:
        ctx.move_to(-w * 0.25, -h * 0.55)
        ctx.line_to(w * 0.25, -h * 0.55)
        ctx.move_to(-w * 0.2, -h * 0.42)
        ctx.line_to(w * 0.2, -h * 0.42)
        ctx.set_source_rgba(0.05, 0.06, 0.08, 0.6)
        ctx.set_line_width(3)
        ctx.stroke()
    ctx.restore()


def fence(ctx, x0, x1, y, h):
    ctx.set_source_rgb(*hexc('#090a10'))
    ctx.set_line_width(5)
    ctx.move_to(x0, y - h * 0.25)
    ctx.line_to(x1, y - h * 0.25 + 6)
    ctx.move_to(x0, y - h * 0.75)
    ctx.line_to(x1, y - h * 0.75 + 4)
    ctx.stroke()
    x = x0
    i = 0
    while x < x1:
        lean = (hash01(i, 5) - 0.5) * 0.08
        ctx.save()
        ctx.translate(x, y)
        ctx.rotate(lean)
        ctx.move_to(0, 0)
        ctx.line_to(0, -h)
        ctx.set_line_width(5)
        ctx.stroke()
        # curly finial
        ctx.new_path()
        for k in range(20):
            f = k / 19
            a = -math.pi / 2 + f * 5.5
            r = 11 * (1 - f * 0.7)
            (ctx.line_to if k else ctx.move_to)(math.cos(a) * r, -h - 11 + math.sin(a) * r + 11)
        ctx.set_line_width(3.5)
        ctx.stroke()
        ctx.restore()
        x += 46
        i += 1


def pumpkin(ctx, x, y, r, t=0.0, lit=1.0):
    ctx.save()
    ctx.translate(x, y)
    for k, dx in enumerate((-0.45, 0.45, 0.0)):
        ellipse(ctx, dx * r, 0, r * 0.62, r * 0.78)
        ctx.set_source_rgb(*(hexc('#d4661c') if k < 2 else hexc('#e8792a')))
        ctx.fill_preserve()
        ctx.set_source_rgb(*hexc('#3a1606'))
        ctx.set_line_width(3)
        ctx.stroke()
    ctx.rectangle(-r * 0.08, -r * 0.95, r * 0.16, r * 0.25)
    ctx.set_source_rgb(*hexc('#2f3d1c'))
    ctx.fill()
    # carved face
    flick = 0.8 + 0.2 * lit
    face = hexc('#ffd36b')
    ctx.set_source_rgba(*face, flick)
    for side in (-1, 1):
        ctx.move_to(side * r * 0.35, -r * 0.3)
        ctx.line_to(side * r * 0.15, -r * 0.05)
        ctx.line_to(side * r * 0.5, -r * 0.05)
        ctx.close_path()
        ctx.fill()
    ctx.move_to(-r * 0.5, r * 0.2)
    ctx.curve_to(-r * 0.2, r * 0.55, r * 0.2, r * 0.55, r * 0.5, r * 0.2)
    ctx.line_to(r * 0.25, r * 0.3)
    ctx.line_to(r * 0.1, r * 0.2)
    ctx.line_to(-r * 0.1, r * 0.32)
    ctx.line_to(-r * 0.3, r * 0.22)
    ctx.close_path()
    ctx.fill()
    ctx.restore()


def vignette(ctx, strength=0.55):
    ctx.rectangle(0, 0, W, H)
    g = cairo.RadialGradient(W / 2, H * 0.45, H * 0.32, W / 2, H * 0.45, H * 0.78)
    g.add_color_stop_rgba(0, 0, 0, 0.02, 0)
    g.add_color_stop_rgba(1, 0, 0, 0.02, strength)
    ctx.set_source(g)
    ctx.fill()


def bg_night(ctx, moon_xy=MOON['night'], moon_r=250, town=True, ground=True):
    ctx.rectangle(0, 0, W, H)
    ctx.set_source(linear(0, 0, 0, 1350, [(0, hexc('#0a0b1d', 1)), (0.6, hexc('#1f3150', 1)), (1, hexc('#3f6172', 1))]))
    ctx.fill()
    stars(ctx, 140, 1000, 3)
    moon(ctx, moon_xy[0], moon_xy[1], moon_r)
    # thin clouds
    for i, (cx, cy, rx) in enumerate(((620, 700, 260), (930, 520, 200), (230, 380, 220))):
        ellipse(ctx, cx, cy, rx, 16 + 6 * i)
        ctx.set_source_rgba(0.12, 0.16, 0.26, 0.55)
        ctx.fill()
    if town:
        # far hills
        ctx.new_path()
        ctx.move_to(0, 1180)
        for x in range(0, W + 60, 60):
            ctx.line_to(x, 1110 + 40 * math.sin(x * 0.006 + 1) + 20 * math.sin(x * 0.017))
        ctx.line_to(W, H)
        ctx.line_to(0, H)
        ctx.close_path()
        ctx.set_source_rgb(*hexc('#17263a'))
        ctx.fill()
        # crooked town on the ridge
        houses = [(40, 1125, 70, 110, 0.4, 60), (120, 1110, 60, 150, -0.6, 70), (200, 1118, 80, 90, 0.2, 50),
                  (600, 1100, 70, 170, 0.8, 90), (690, 1095, 60, 120, -0.4, 60), (760, 1100, 90, 100, 0.3, 50),
                  (860, 1110, 55, 200, -0.7, 110), (930, 1115, 75, 120, 0.5, 60), (1010, 1120, 70, 90, -0.3, 45)]
        for i, (x, y, w, h, lean, roof) in enumerate(houses):
            crooked_house(ctx, x, y, w, h, lean, roof, hexc('#0f1826'), hexc('#ffb54d'), i)
        # nearer hill
        ctx.new_path()
        ctx.move_to(0, 1330)
        ctx.curve_to(300, 1240, 650, 1300, W, 1260)
        ctx.line_to(W, H)
        ctx.line_to(0, H)
        ctx.close_path()
        ctx.set_source_rgb(*hexc('#131c29'))
        ctx.fill()
    if ground:
        curly_tree(ctx, 120, 1420, 620, 1)
        for x, y, w, h, rot, cr in ((300, 1350, 60, 110, -0.1, False), (420, 1330, 40, 90, 0.12, True),
                                    (760, 1320, 70, 120, 0.08, False), (900, 1345, 50, 95, -0.15, True),
                                    (990, 1330, 60, 105, 0.1, False)):
            tombstone(ctx, x, y, w, h, rot, cr)
        fence(ctx, 160, 1080, 1460, 120)
        ctx.new_path()
        ctx.move_to(0, 1470)
        ctx.curve_to(400, 1430, 700, 1480, W, 1450)
        ctx.line_to(W, H)
        ctx.line_to(0, H)
        ctx.close_path()
        ctx.set_source(linear(0, 1450, 0, H, [(0, hexc('#10161f', 1)), (1, hexc('#05070b', 1))]))
        ctx.fill()
        for i in range(26):
            gx = hash01(i, 41) * W
            gy = 1480 + hash01(i, 42) * 400
            ctx.move_to(gx - 10, gy)
            ctx.line_to(gx - 4, gy - 22)
            ctx.line_to(gx, gy)
            ctx.line_to(gx + 6, gy - 28)
            ctx.line_to(gx + 10, gy)
            ctx.set_source_rgb(*hexc('#1a2430'))
            ctx.fill()


def bg_kitchen(ctx):
    # striped, slightly crooked wallpaper
    ctx.rectangle(0, 0, W, 1190)
    ctx.set_source_rgb(*hexc('#2a2034'))
    ctx.fill()
    for i in range(-2, 22):
        x = i * 62
        ctx.move_to(x, 0)
        ctx.line_to(x + 31, 0)
        ctx.line_to(x + 31 - 38, 1190)
        ctx.line_to(x - 38, 1190)
        ctx.close_path()
        ctx.set_source_rgb(*hexc('#34283f'))
        ctx.fill()
    # window
    wx, wy = KITCHEN['window']
    ctx.save()
    ellipse(ctx, wx, wy, 165, 175, 0.05)
    ctx.clip()
    ctx.rectangle(0, 0, W, H)
    ctx.set_source(linear(0, wy - 180, 0, wy + 180, [(0, hexc('#0b0d22', 1)), (1, hexc('#2f4b66', 1))]))
    ctx.fill()
    stars(ctx, 40, 700, 9)
    moon(ctx, wx + 40, wy - 40, 62)
    curly_tree(ctx, wx - 60, wy + 260, 300, -1, hexc('#05050a'))
    ctx.restore()
    ellipse(ctx, wx, wy, 165, 175, 0.05)
    ctx.set_source_rgb(*hexc('#140c12'))
    ctx.set_line_width(26)
    ctx.stroke()
    ctx.move_to(wx - 4, wy - 175)
    ctx.line_to(wx + 6, wy + 175)
    ctx.move_to(wx - 165, wy + 6)
    ctx.line_to(wx + 165, wy - 6)
    ctx.set_line_width(12)
    ctx.stroke()
    # tattered curtains
    for side in (-1, 1):
        ctx.new_path()
        x0 = wx + side * 150
        ctx.move_to(x0 - side * 30, wy - 230)
        ctx.line_to(x0 + side * 80, wy - 230)
        ctx.curve_to(x0 + side * 90, wy, x0 + side * 70, wy + 150, x0 + side * 85, wy + 260)
        for k in range(5):
            ctx.line_to(x0 + side * (85 - k * 22), wy + 230 + (25 if k % 2 else 0))
        ctx.curve_to(x0 - side * 10, wy + 100, x0 + side * 10, wy - 50, x0 - side * 30, wy - 230)
        ctx.set_source_rgb(*hexc('#4b2554'))
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(4)
        ctx.stroke()
    # shelf with jars and bottles
    ctx.rectangle(30, 560, 420, 20)
    ctx.set_source_rgb(*hexc('#3b2a22'))
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(4)
    ctx.stroke()
    for x, w, h, col in ((70, 70, 110, '#5f9c7d'), (165, 55, 150, '#8c5aa8'), (240, 80, 90, '#c58f3e'),
                         (345, 50, 130, '#4f7fa8')):
        ctx.new_path()
        ctx.rectangle(x, 560 - h, w, h)
        ctx.set_source_rgba(*hexc(col), 0.75)
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.stroke()
        ctx.rectangle(x + w * 0.2, 560 - h - 18, w * 0.6, 18)
        ctx.set_source_rgb(*hexc('#2b1c16'))
        ctx.fill()
    for k in range(3):                       # a jar of eyeballs
        draw_candy(ctx, 'E', 92 + k * 16, 520 - k * 22, 13, k)
    # cobweb
    ctx.set_source_rgba(0.85, 0.85, 0.95, 0.35)
    ctx.set_line_width(2)
    for k in range(6):
        a = k * math.pi / 2 / 5
        ctx.move_to(0, 0)
        ctx.line_to(math.cos(a) * 240, math.sin(a) * 240)
    ctx.stroke()
    for r in (60, 110, 160, 210):
        ctx.new_path()
        for k in range(6):
            a = k * math.pi / 2 / 5
            pt = (math.cos(a) * r, math.sin(a) * r)
            if k == 0:
                ctx.move_to(*pt)
            else:
                pa = (k - 0.5) * math.pi / 2 / 5
                ctx.curve_to(math.cos(pa) * r * 0.86, math.sin(pa) * r * 0.86, math.cos(pa) * r * 0.86,
                             math.sin(pa) * r * 0.86, *pt)
        ctx.stroke()
    # stone hearth arch behind the cauldron
    ctx.new_path()
    ctx.move_to(60, 1330)
    ctx.line_to(60, 1020)
    ctx.curve_to(60, 840, 540, 840, 540, 1020)
    ctx.line_to(540, 1330)
    ctx.close_path()
    ctx.set_source_rgb(*hexc('#3d3540'))
    ctx.fill()
    ctx.new_path()
    ctx.move_to(110, 1330)
    ctx.line_to(110, 1040)
    ctx.curve_to(110, 900, 490, 900, 490, 1040)
    ctx.line_to(490, 1330)
    ctx.close_path()
    ctx.set_source(linear(0, 900, 0, 1330, [(0, hexc('#0b080c', 1)), (1, hexc('#2a1310', 1))]))
    ctx.fill()
    for i in range(14):                       # stones
        a = math.pi + i * math.pi / 13
        x = 300 + math.cos(a) * 215
        y = 1020 + math.sin(a) * 150
        ellipse(ctx, x, y, 26, 17, a)
        ctx.set_source_rgb(*hexc('#4d4450'))
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(3)
        ctx.stroke()
    # floor: crooked black & white diamonds in perspective
    ctx.save()
    ctx.rectangle(0, 1190, W, H - 1190)
    ctx.clip()
    ctx.set_source_rgb(*hexc('#1a1720'))
    ctx.paint()
    vx, vy = 540, 700
    rows = [1190 + (H - 1190) * ((k / 9) ** 1.6) for k in range(11)]
    for r in range(len(rows) - 1):
        y0, y1 = rows[r], rows[r + 1]
        f0 = (y0 - vy) / (H - vy)
        f1 = (y1 - vy) / (H - vy)
        for c in range(-12, 13):
            if (r + c) % 2:
                continue
            xa0 = vx + (c * 120) * f0
            xb0 = vx + ((c + 1) * 120) * f0
            xa1 = vx + (c * 120) * f1
            xb1 = vx + ((c + 1) * 120) * f1
            ctx.move_to(xa0, y0)
            ctx.line_to(xb0, y0)
            ctx.line_to(xb1, y1)
            ctx.line_to(xa1, y1)
            ctx.close_path()
        ctx.set_source_rgb(*hexc('#5c5464'))
        ctx.fill()
    ctx.rectangle(0, 1190, W, H - 1190)
    ctx.set_source(linear(0, 1190, 0, H, [(0, (0.02, 0.01, 0.04, 0.55)), (0.5, (0.02, 0.01, 0.04, 0.2)),
                                          (1, (0.02, 0.01, 0.04, 0.6))]))
    ctx.fill()
    ctx.restore()
    ctx.rectangle(0, 1180, W, 14)
    ctx.set_source_rgb(*hexc('#120d14'))
    ctx.fill()
    # crooked table with a striped cloth
    ctx.set_source_rgb(*hexc('#2a1a14'))
    for lx, lean in ((640, -0.04), (1010, 0.05)):
        ctx.save()
        ctx.translate(lx, 1100)
        ctx.rotate(lean)
        ctx.rectangle(-12, 0, 24, 240)
        ctx.fill()
        ctx.restore()
    ctx.new_path()
    ctx.move_to(600, 1080)
    ctx.line_to(1060, 1072)
    ctx.line_to(1068, 1180)
    for k in range(10):
        ctx.line_to(1068 - (k + 1) * 47, 1180 + (14 if k % 2 == 0 else 0))
    ctx.close_path()
    ctx.save()
    ctx.clip_preserve()
    ctx.set_source_rgb(*hexc('#e9e1d2'))
    ctx.fill()
    for k in range(12):
        x = 600 + k * 42
        ctx.rectangle(x, 1060, 20, 140)
    ctx.set_source_rgb(*hexc('#5a2f6e'))
    ctx.fill()
    ctx.restore()
    ctx.new_path()
    ctx.move_to(600, 1080)
    ctx.line_to(1060, 1072)
    ctx.line_to(1068, 1180)
    for k in range(10):
        ctx.line_to(1068 - (k + 1) * 47, 1180 + (14 if k % 2 == 0 else 0))
    ctx.close_path()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(4.5)
    ctx.stroke()
    # plate
    px, py = KITCHEN['plate']
    ellipse(ctx, px, py, 92, 22)
    ctx.set_source_rgb(*hexc('#f2efe6'))
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(4)
    ctx.stroke()
    ellipse(ctx, px, py, 62, 13)
    ctx.set_source_rgba(0.6, 0.6, 0.7, 0.5)
    ctx.set_line_width(2)
    ctx.stroke()
    # candle stub on the table
    ctx.rectangle(1004, 960, 32, 112)
    ctx.set_source_rgb(*hexc('#e6dcc3'))
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(3.5)
    ctx.stroke()
    # warm firelight on the floor
    ctx.rectangle(0, 0, W, H)
    ctx.set_source(radial(ctx, 300, 1380, 700, [(0, (1, 0.55, 0.2, 0.22)), (1, (1, 0.55, 0.2, 0))]))
    ctx.fill()


def flame(ctx, x, y, s, t, seed):
    f = 1 + 0.12 * vnoise(t * 9, seed) + 0.06 * vnoise(t * 17, seed + 1)
    sway = 6 * vnoise(t * 5, seed + 2) * s
    ctx.arc(x, y - 20 * s, 60 * s, 0, 2 * math.pi)
    ctx.set_source(radial(ctx, x, y - 20 * s, 60 * s, [(0, (1, 0.75, 0.3, 0.35)), (1, (1, 0.75, 0.3, 0))]))
    ctx.fill()
    for k, (col, sc) in enumerate((('#ff7a1a', 1.0), ('#ffd166', 0.6))):
        h = 46 * s * f * sc
        w = 15 * s * sc
        ctx.new_path()
        ctx.move_to(x, y)
        ctx.curve_to(x - w * 1.3, y - h * 0.2, x - w * 0.5 + sway, y - h * 0.7, x + sway * 1.4, y - h)
        ctx.curve_to(x + w * 0.5 + sway, y - h * 0.7, x + w * 1.3, y - h * 0.2, x, y)
        ctx.set_source_rgb(*hexc(col))
        ctx.fill()


def dyn_kitchen(ctx, t):
    # fire under the pot
    for k, dx in enumerate((-45, 0, 42)):
        flame(ctx, 300 + dx, 1395, 1.25 - 0.2 * abs(dx) / 45, t, k * 3)
    ctx.set_source_rgb(*hexc('#2a1a12'))
    for k in range(3):
        ctx.save()
        ctx.translate(300, 1400)
        ctx.rotate(-0.3 + k * 0.3)
        ctx.rectangle(-70, -10, 140, 20)
        ctx.fill()
        ctx.restore()
    flame(ctx, 1020, 960, 0.6, t, 31)


def bg_supper(ctx):
    bg_night(ctx, MOON['supper'], 230, town=True, ground=False)
    ctx.rectangle(0, 1250, W, H - 1250)
    ctx.set_source(linear(0, 1250, 0, H, [(0, hexc('#111823', 1)), (1, hexc('#05070b', 1))]))
    ctx.fill()
    # lanterns
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(2.5)
    ctx.move_to(-20, 760)
    ctx.curve_to(300, 900, 780, 900, 1100, 760)
    ctx.stroke()
    # silhouetted neighbours along both sides, far ones first
    folk = [(-1, 0.32, 'hat'), (1, 0.36, 'pumpkin'), (-1, 0.54, 'hood'), (1, 0.57, 'cat'), (-1, 0.72, 'tall'),
            (1, 0.75, 'hat'), (-1, 0.87, 'pumpkin'), (1, 0.89, 'hood')]
    for side, depth, kind in sorted(folk, key=lambda f: -f[1]):
        y = lerp(1400, 1030, depth) + 10
        half = lerp(620, 95, depth)
        x = 540 + side * (half + lerp(40, 14, depth))
        s = lerp(1.25, 0.3, depth)
        silhouette(ctx, x, y, s, kind, side)
    # the long table, receding toward the town
    ctx.new_path()
    ctx.move_to(-60, 1400)
    ctx.line_to(1140, 1400)
    ctx.line_to(632, 1030)
    ctx.line_to(448, 1030)
    ctx.close_path()
    ctx.save()
    ctx.clip_preserve()
    ctx.set_source_rgb(*hexc('#2b2036'))
    ctx.fill()
    for k in range(-8, 9):
        ctx.move_to(540 + k * 18, 1030)
        ctx.line_to(540 + k * 150, 1400)
        ctx.line_to(540 + k * 150 + 70, 1400)
        ctx.line_to(540 + k * 18 + 8, 1030)
        ctx.close_path()
    ctx.set_source_rgb(*hexc('#3d2a4d'))
    ctx.fill()
    ctx.rectangle(0, 1020, W, 390)
    ctx.set_source(linear(0, 1030, 0, 1400, [(0, (0.02, 0.02, 0.06, 0.55)), (1, (0.02, 0.02, 0.06, 0.0))]))
    ctx.fill()
    ctx.restore()
    # a bowl in front of every neighbour
    for side, depth, kind in folk:
        y = lerp(1400, 1030, depth) + 4
        half = lerp(620, 95, depth)
        x = 540 + side * (half - lerp(70, 18, depth))
        s = lerp(1.2, 0.3, depth)
        ellipse(ctx, x, y, 46 * s, 14 * s)
        ctx.set_source_rgb(*hexc('#cfc6b6'))
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(3 * s)
        ctx.stroke()
        ctx.new_path()
        ctx.arc(x, y, 46 * s, 0, math.pi)
        ctx.set_source_rgb(*hexc('#9a8f80'))
        ctx.fill()


def silhouette(ctx, x, y, s, kind, side):
    col = hexc('#0b0e16')
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.push_group()
    ctx.set_source_rgb(*col)
    ctx.new_path()
    ctx.move_to(-70, 0)
    ctx.curve_to(-70, -120, 70, -120, 70, 0)
    ctx.close_path()
    ctx.fill()
    hy = -150
    if kind == 'pumpkin':
        ellipse(ctx, 0, hy, 62, 50)
        ctx.fill()
        ctx.rectangle(-6, hy - 66, 12, 20)
        ctx.fill()
    elif kind == 'cat':
        ellipse(ctx, 0, hy + 20, 42, 38)
        ctx.fill()
        for e in (-1, 1):
            ctx.move_to(e * 38, hy)
            ctx.line_to(e * 26, hy - 50)
            ctx.line_to(e * 8, hy - 12)
            ctx.fill()
    elif kind == 'hood':
        ctx.move_to(-50, hy + 40)
        ctx.curve_to(-55, hy - 40, -10, hy - 80, 10, hy - 90)
        ctx.curve_to(40, hy - 50, 55, hy, 50, hy + 40)
        ctx.close_path()
        ctx.fill()
    else:
        ellipse(ctx, 0, hy, 40, 46)
        ctx.fill()
        if kind == 'hat':
            ellipse(ctx, 0, hy - 36, 80, 12)
            ctx.fill()
            ctx.move_to(-38, hy - 40)
            ctx.line_to(14, hy - 170)
            ctx.line_to(36, hy - 40)
            ctx.fill()
        else:
            ctx.rectangle(-30, hy - 110, 60, 75)
            ctx.fill()
            ellipse(ctx, 0, hy - 36, 62, 10)
            ctx.fill()
    shape = ctx.pop_group()
    # moonlit rim so each neighbour reads against the night
    ctx.save()
    ctx.translate(-4, -4)
    ctx.set_source_rgba(0.55, 0.65, 0.85, 0.55)
    ctx.mask(shape)
    ctx.restore()
    ctx.set_source(shape)
    ctx.paint()
    for e in (-1, 1):
        ellipse(ctx, e * 15 - side * 8, hy + 2 + (20 if kind == 'cat' else 0), 7, 9)
        ctx.set_source_rgb(*hexc('#ffd36b'))
        ctx.fill()
    ctx.new_path()
    ctx.move_to(-14 - side * 8, hy + 22 + (20 if kind == 'cat' else 0))
    ctx.curve_to(-6 - side * 8, hy + 30, 6 - side * 8, hy + 30, 14 - side * 8, hy + 22 + (20 if kind == 'cat' else 0))
    ctx.set_source_rgba(*hexc('#ffd36b'), 0.8)
    ctx.set_line_width(3)
    ctx.stroke()
    ctx.restore()


def dyn_supper(ctx, t):
    for i, x in enumerate((60, 230, 420, 660, 850, 1020)):
        y = 760 + 140 * math.sin(math.pi * (x + 20) / 1120) ** 1.2 + 6
        ctx.arc(x, y + 34, 70, 0, 2 * math.pi)
        ctx.set_source(radial(ctx, x, y + 34, 70, [(0, (1, 0.6, 0.2, 0.25 + 0.05 * vnoise(t * 3, i))),
                                                   (1, (1, 0.6, 0.2, 0))]))
        ctx.fill()
        ellipse(ctx, x, y + 34, 26, 32)
        ctx.set_source_rgb(*hexc('#ff9a3c'))
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(3)
        ctx.stroke()
        for k in (-1, 0, 1):
            ctx.move_to(x + k * 13, y + 6)
            ctx.line_to(x + k * 13, y + 62)
        ctx.set_line_width(2)
        ctx.stroke()
    for i, d in enumerate((0.3, 0.55, 0.8)):
        y = lerp(1400, 1030, d)
        s = lerp(1.0, 0.35, d)
        ctx.rectangle(540 - 9 * s, y - 70 * s, 18 * s, 70 * s)
        ctx.set_source_rgb(*hexc('#e6dcc3'))
        ctx.fill()
        flame(ctx, 540, y - 70 * s, 0.55 * s, t, 50 + i)


def fg_supper(ctx):
    # the near edge of the table, in front of the pot and Alice's hem
    ctx.new_path()
    ctx.move_to(-60, 1390)
    ctx.line_to(1140, 1390)
    ctx.line_to(1140, 1600)
    for k in range(16):
        ctx.line_to(1140 - (k + 1) * 75, 1600 + (26 if k % 2 == 0 else 0))
    ctx.close_path()
    ctx.save()
    ctx.clip_preserve()
    ctx.set_source_rgb(*hexc('#e9e1d2'))
    ctx.fill()
    for k in range(16):
        ctx.rectangle(-60 + k * 80, 1380, 40, 260)
    ctx.set_source_rgb(*hexc('#5a2f6e'))
    ctx.fill()
    ctx.rectangle(-60, 1390, 1200, 300)
    ctx.set_source(linear(0, 1390, 0, 1640, [(0, (0.05, 0.05, 0.12, 0.25)), (1, (0.05, 0.05, 0.12, 0.7))]))
    ctx.fill()
    ctx.restore()
    ctx.new_path()
    ctx.move_to(-60, 1390)
    ctx.line_to(1140, 1390)
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(5)
    ctx.stroke()


PHOTO = None


def photo_surface():
    global PHOTO
    if PHOTO is None:
        from PIL import Image, ImageOps
        im = ImageOps.exif_transpose(Image.open(os.path.join(HERE, 'assets', 'original_drawing.jpg'))).convert('RGB')
        w, h = im.size
        im = im.crop((int(w * 0.02), 0, int(w * 0.885), h))          # leave the thumb out
        im = im.resize((560, int(560 * im.size[1] / im.size[0])), Image.LANCZOS)
        arr = np.array(im)
        a = np.zeros((arr.shape[0], arr.shape[1], 4), dtype=np.uint8)
        a[..., 0], a[..., 1], a[..., 2], a[..., 3] = arr[..., 2], arr[..., 1], arr[..., 0], 255
        PHOTO = cairo.ImageSurface.create_for_data(memoryview(a.copy()), cairo.FORMAT_RGB24, a.shape[1], a.shape[0])
    return PHOTO


def bg_end(ctx):
    ctx.rectangle(0, 0, W, H)
    ctx.set_source(linear(0, 0, 0, H, [(0, hexc('#1e1527', 1)), (1, hexc('#0b0910', 1))]))
    ctx.fill()
    stars(ctx, 90, H, 21)
    for i in range(18):                      # stripes, like wallpaper behind a picture frame
        ctx.rectangle(i * 64, 0, 32, H)
    ctx.set_source_rgba(1, 1, 1, 0.025)
    ctx.fill()


# ── per-frame state ──────────────────────────────────────────────────────────
def shot_camera(t, scene, apos, spos):
    st, shot, _ = last_event(SHOT_EV, t, 'night_wide')
    fixed = {
        'night_wide': (540, 960, 1.0), 'night_mid': (540, 930, 1.18), 'night_bubbles': (540, 820, 1.12),
        'kitchen_wide': (540, 960, 1.0), 'kitchen_table': (720, 960, 1.38), 'window_two': (690, 760, 1.3),
        'steam_shot': (420, 1000, 1.32), 'supper_wide': (540, 960, 1.0), 'end': (540, 960, 1.0),
    }
    if shot in fixed:
        cx, cy, z = fixed[shot]
    elif shot == 'alice_close' and apos:
        cx, cy, z = apos[0], apos[1] + 40, 1.8
    elif shot == 'simmer_close' and spos:
        cx, cy, z = spos[0] + 50, spos[1] - 90, 1.9
    elif shot == 'two_shot' and apos and spos:
        cx, cy, z = (apos[0] + spos[0]) / 2, (apos[1] + spos[1]) / 2 - 30, 1.32
    elif shot == 'supper_two' and apos and spos:
        cx, cy, z = (apos[0] + spos[0]) / 2, (apos[1] + spos[1]) / 2 - 20, 1.5
    else:
        cx, cy, z = 540, 960, 1.0
    hw, hh = W / 2 / z, H / 2 / z
    cx = clamp(cx, hw, W - hw)
    cy = clamp(cy, hh, H - hh)
    return round(cx, 1), round(cy, 1), round(z, 4)


def alice_state(t, scene, frame, look):
    p = emo_params('A', t)
    base = base_pos('A', t, scene)
    s = SCALE[scene]['A']
    g = dict(p)
    x, y = base
    sp = speaking_env('A', t)
    op, br = lip('A', t)
    # floating
    g['tilt'] = p['tilt'] + 2.2 * math.sin(t * 0.9) + sp * 2.0 * vnoise(t * 1.7, 4)
    y += p['bob'] * 12 * math.sin(t * 2 * math.pi * 0.42)
    x += 4 * math.sin(t * 0.7)
    nod = listener_nod('A', t)
    y += 7 * nod
    g['squash'] = p['squash'] + 0.018 * op + 0.012 * math.sin(t * 2 * math.pi * 0.42)
    g['brow_y'] = p['brow_y'] + 5 * op * sp
    g['open'] = clamp(p['open'] * (1 - 0.5 * op) + 0.85 * op)
    g['mouth_w'] = p['mouth_w'] * (0.72 + 0.45 * br) if op > 0.05 else p['mouth_w']
    g['smile'] = p['smile'] * (1 - 0.35 * op)
    g['blink'] = blink_amount('A', t)
    g['flip'] = 1.0
    g['glow'] = 1.0 if scene in ('night', 'supper', 'end') else 0.6
    inside = []

    # ── actions ──
    u, d = act_local('wave', t)
    if 0 <= u <= 1.8:
        w = smooth(u / 0.25) * smooth((1.8 - u) / 0.3)
        g['armR'] = lerp(g['armR'], -60 + 28 * math.sin(u * 2 * math.pi * 2.6), w)
    for k, name in enumerate(('eat_fail_1', 'eat_fail_2')):
        u, d = act_local(name, t)
        if not (0 <= u <= d):
            continue
        fast = name == 'eat_fail_2'
        sc = 0.62 if fast else 1.0
        kind = 'E' if not fast else 'M'
        px, py = KITCHEN['plate']
        dip = 70 * math.sin(math.pi * clamp(u / (0.75 * sc)))
        y += dip
        x += 45 * math.sin(math.pi * clamp(u / (0.75 * sc)))
        grab, mouth_t, gulp = 0.4 * sc, 0.85 * sc, 1.0 * sc
        local = lambda wx, wy: ((wx - x) / s, (wy - y) / s)
        if u < grab:
            g['tipR'] = local(lerp(x + 176 * s + 60 * s, px - 10, smooth(u / grab)), lerp(y + 60 * s, py - 18, smooth(u / grab)))
        elif u < gulp:
            f = smooth((u - grab) / (mouth_t - grab))
            mx, my = fpos(g, 2, 32)
            sx_, sy_ = local(px - 10, py - 18)
            g['tipR'] = (lerp(sx_, mx + 62, f), lerp(sy_, my - 4, f))
            g['holdR'] = kind
            g['feed'] = f
            g['open'] = max(g['open'], clamp((u - grab) / (mouth_t - grab)) * 0.95)
            g['mouth_w'] = 0.95
        else:
            fall = clamp((u - gulp) / (0.6 * sc))
            g['open'] = 0.0 if u < gulp + 0.12 else g['open']
            if fall < 1:
                cy_ = lerp(40, 340, fall ** 2)
                inside.append((kind, 10, cy_, 26, u * 4))
    g['inside'] = inside

    u, d = act_local('fetch_drop', t)
    if 0 <= u <= d:
        start = NAMED['talk']
        low = (470, 1165)
        above = (440, 845)
        end = NAMED['by_pot']
        if u < 1.1:
            f = smooth(u / 1.1)
            x, y = lerp(start[0], low[0], f), lerp(start[1], low[1], f) + 0 * math.sin(math.pi * f)
            g['tilt'] += -12 * math.sin(math.pi * f)
        elif u < 1.6:
            x, y = low
            f = smooth((u - 1.1) / 0.4)
            fl = FLOOR_SPOT
            g['tipL'] = (lerp(-230, (fl['M'][0] - 4 - x) / s, f), lerp(60, (fl['M'][1] - 18 - y) / s, f))
            g['tipR'] = (lerp(230, (fl['E'][0] - 4 - x) / s, f), lerp(60, (fl['E'][1] - 18 - y) / s, f))
            if u > 1.5:
                g['holdL'], g['holdR'] = 'M', 'E'
        elif u < 2.6:
            f = smooth((u - 1.6) / 1.0)
            x, y = lerp(low[0], above[0], f), lerp(low[1], above[1], f)
            g['holdL'], g['holdR'] = 'M', 'E'
            g['armL'], g['armR'] = 35, 35
        else:
            x, y = above
            for key, kind, t_in, t_rel in (('L', 'M', 2.6, 2.9), ('R', 'E', 3.05, 3.4)):
                drop = DROP_SPOT[kind]
                w = smooth((u - t_in) / 0.25) * (1 - smooth((u - t_rel - 0.15) / 0.35))
                rest = (lerp(-1, 1, key == 'R') * 230, 60)
                tgt = ((drop[0] - 4 - x) / s, (drop[1] - 18 - y) / s)
                g['tip' + key] = (lerp(rest[0], tgt[0], w), lerp(rest[1], tgt[1], w))
                if u < t_rel:
                    g['hold' + key] = kind
            if u > 3.7:
                f = smooth((u - 3.7) / 0.9)
                x, y = lerp(above[0], end[0], f), lerp(above[1], end[1], f)
    u, d = act_local('inhale', t)
    if 0 <= u <= d + 0.01:
        a, b = NAMED['by_pot'], NAMED['steam']
        f = smooth(u / 1.2) - smooth((u - 3.4) / 1.0)
        x, y = lerp(a[0], b[0], f) + 4 * math.sin(t * 0.7), lerp(a[1], b[1], f) + p['bob'] * 12 * math.sin(t * 2 * math.pi * 0.42)
        if 1.2 < u < 3.3:
            g['squash'] += 0.04 * smooth((u - 1.2) / 2.0)
    u, d = act_local('spin', t)
    if 0 <= u <= 0.75:
        f = u / 0.75
        g['flip'] = math.cos(f * 2 * math.pi)
        if abs(g['flip']) < 0.08:
            g['flip'] = 0.08 if g['flip'] >= 0 else -0.08
        y -= 45 * math.sin(math.pi * f)
    if scene == 'supper' and t >= act_time('lean')[0]:
        f = smooth((t - act_time('lean')[0]) / 1.2)
        g['tilt'] += -9 * f
        x -= 30 * f
    # heart / tear / inner warmth
    th = act_time('heart_show')[0]
    tf = act_time('heart_fill')[0]
    if t >= th and scene in ('kitchen', 'supper'):
        g['heart'] = smooth((t - th) / 0.6) * (0.8 if scene == 'supper' else 1.0)
        g['heart_fill'] = smooth((t - tf) / 1.1)
    tt = act_time('tear')[0]
    if tt <= t <= tt + 3.2:
        g['tear'] = (t - tt) / 3.2
    ti, di = act_time('inhale')
    if t >= ti + 1.6:
        g['inner'] = smooth((t - ti - 1.6) / 1.8) * (1 - 0.6 * smooth((t - ti - 8) / 4))
    g['gaze'] = gaze_vec('A', t, look, (x, y - 100 * s))
    g['tilt'] += 3 * g['gaze'][0]
    g.update(x=x, y=y, s=s)
    return g


def simmer_state(t, scene, frame, look, apos):
    p = emo_params('S', t)
    base = base_pos('S', t, scene)
    if base is None:
        return None
    s = SCALE[scene]['S']
    c = dict(p)
    x, y = base
    op, br = lip('S', t)
    sp = speaking_env('S', t)
    c['squash'] = p['squash'] + 0.015 * math.sin(t * 2 * math.pi * 0.3) + 0.03 * op
    c['tilt'] = 1.5 * math.sin(t * 0.5) + sp * 1.5 * vnoise(t * 1.5, 7)
    if p['happy'] > 0.9 and p['open'] > 0.5:                        # laughing jiggle
        c['squash'] += 0.03 * math.sin(t * 2 * math.pi * 7)
    y += 6 * listener_nod('S', t)
    c['open'] = clamp(p['open'] * (1 - 0.5 * op) + 0.8 * op)
    c['mouth_w'] = p['mouth_w'] * (0.8 + 0.35 * br) if op > 0.05 else p['mouth_w']
    c['brow_y'] = p['brow_y'] + 4 * op * sp
    c['blink'] = blink_amount('S', t)
    c['blorps'] = []
    tw, _ = act_time('simmer_wakes')
    c['blorps'] += [tw + 0.3, tw + 0.95]
    tfd, _ = act_time('fetch_drop')
    c['blorps'] += [tfd + 3.2, tfd + 3.7, tfd + 3.95]
    for bt in (tfd + 3.2, tfd + 3.7):
        u = t - bt
        if 0 <= u < 0.6:
            c['squash'] += 0.07 * math.sin(math.pi * u / 0.6) * math.cos(u * 18)
    u, d = act_local('simmer_wakes', t)
    if 0 <= u <= d:
        c['squash'] += 0.06 * math.sin(math.pi * clamp((u - 0.5) / 0.8))
    glow_boost = smooth((t - tfd - 3.2) / 0.5) * 0.35
    c['glow'] = clamp(p['glow'] + glow_boost, 0, 1.3)
    if t > tfd + 3.2:
        mix = smooth((t - tfd - 3.2) / 1.5)
        c['gcol'] = (lerp(0.55, 0.85, mix), lerp(1.0, 0.75, mix), lerp(0.78, 1.0, mix))
    c['fire'] = 1.0 if scene == 'kitchen' else 0.0
    c['gaze'] = gaze_vec('S', t, look, (x, y - 20 * s))
    c.update(x=x, y=y, s=s)
    return c


def candies_state(t, scene):
    """World positions of the two sweets in the kitchen (or None when hidden)."""
    if scene != 'kitchen':
        return {}
    out = {}
    px, py = KITCHEN['plate']
    plate_pos = {'E': (px - 22, py - 18), 'M': (px + 30, py - 16)}
    floor = FLOOR_SPOT
    tfd, _ = act_time('fetch_drop')
    for name, kind, times, heights in (('eat_fail_1', 'E', (1.6, 1.68, 2.12, 2.45, 2.68), (0, 110, 60, 30, 10)),
                                       ('eat_fail_2', 'M', (1.1, 1.15, 1.45, 1.68, 1.86, 2.0), (0, 90, 55, 30, 15, 6))):
        t0, d = act_time(name)
        u = t - t0
        if u < 0:
            out[kind] = plate_pos[kind] + (0.0,)
        elif u < times[0]:
            continue        # in Alice's hand or falling through her
        elif t < tfd + 1.5:
            start = (POS['kitchen']['A'][0] + 25, POS['kitchen']['A'][1] + 300 * 0.82)
            mid = (lerp(start[0], floor[kind][0], 0.55), floor[kind][1] - 8)
            ub = u
            hop = bounce_path(ub, start, mid, times, heights)
            if hop is None:
                continue
            if ub > times[-1]:
                f = smooth((ub - times[-1]) / 0.9)
                hx = lerp(mid[0], floor[kind][0], f)
                hy = lerp(mid[1], floor[kind][1], f)
                out[kind] = (hx, hy, -times[-1] * 9 - f * 6)
            else:
                out[kind] = hop
    # dropped into the pot
    for kind, rel, land in (('M', 2.9, 3.2), ('E', 3.4, 3.7)):
        u = t - tfd
        if rel <= u < land:
            f = (u - rel) / (land - rel)
            sx, sy = DROP_SPOT[kind]
            out[kind] = (lerp(sx, 300 + (14 if kind == 'E' else -14), f), lerp(sy, KITCHEN['pot_rim'][1] - 8, f ** 2), f * 5)
    return out


alice_cache = {}


def look_targets(scene, apos, spos, candies, t):
    m = MOON.get(scene, (540, 500))
    tg = {'moon': m, 'window': KITCHEN['window'], 'plate': KITCHEN['plate'], 'steam': WISP,
          'pot': KITCHEN['pot_rim'], 'bubbleL': BUBBLES['L'], 'bubbleR': BUBBLES['R']}
    if apos:
        tg['A'] = (apos[0], apos[1] - 90)
        tg['hand'] = (apos[0] + 60, apos[1] + 20)
    if spos:
        tg['S'] = (spos[0], spos[1] - 20)
    for k in ('E', 'M'):
        if k in candies:
            tg['candy'] = candies[k][:2]
    if 'candy' not in tg:
        tg['candy'] = (500, 1380)
    return tg


# ── overlays ─────────────────────────────────────────────────────────────────
def draw_bubble_cloud(ctx, cx, cy, rx, ry, seed):
    pts = []
    n = 9
    for i in range(n):
        a = i / n * 2 * math.pi
        bump = 1 + 0.12 * math.sin(a * 3 + seed)
        pts.append((cx + math.cos(a) * rx * bump, cy + math.sin(a) * ry * bump))
    ctx.new_path()
    ctx.move_to(*pts[0])
    for i in range(n):
        p0, p1 = pts[i], pts[(i + 1) % n]
        mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
        ox, oy = mx - cx, my - cy
        ctx.curve_to(p0[0] + ox * 0.45, p0[1] + oy * 0.45, p1[0] + ox * 0.45, p1[1] + oy * 0.45, *p1)
    ctx.close_path()
    ctx.set_source_rgba(0.97, 0.96, 0.93, 0.95)
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(5)
    ctx.stroke()


def draw_thought_bubbles(ctx, t, head):
    t0, _ = act_time('bubbles_in')
    u = t - t0
    if u < 0:
        return
    for k, (key, kind, label) in enumerate((('L', 'E', 'eat yum!'), ('R', 'M', 'eat yum'))):
        bx, by = BUBBLES[key]
        # trail of dots from her head
        for j in range(3):
            f = (j + 1) / 4
            dx = lerp(head[0], bx, f)
            dy = lerp(head[1], by + 120, f)
            sc = ease_out_back((u - 0.08 * j - 0.35 * k) / 0.25)
            if sc <= 0:
                continue
            ellipse(ctx, dx, dy, (9 + 7 * j) * sc, (6 + 5 * j) * sc)
            ctx.set_source_rgb(*INK)
            ctx.fill()
        sc = ease_out_back((u - 0.3 - 0.35 * k) / 0.3)
        if sc <= 0:
            continue
        ctx.save()
        ctx.translate(bx, by + 6 * math.sin(t * 1.3 + k))
        ctx.scale(sc, sc)
        draw_bubble_cloud(ctx, 0, 0, 175, 135, k)
        draw_candy(ctx, kind, 0, -28, 46, 0.2 * math.sin(t * 1.5 + k))
        ctx.select_font_face(HAND_FONT)
        ctx.set_font_size(46)
        ext = ctx.text_extents(label)
        ctx.move_to(-ext.x_advance / 2, 72)
        ctx.set_source_rgb(*INK)
        ctx.show_text(label)
        ctx.restore()


def draw_hearts(ctx, x, y, s, t, alpha=1.0):
    """The two hearts from the drawing: one hollow, one filled in."""
    for k, (dx, filled) in enumerate(((-42, False), (42, True))):
        hx = x + dx * s
        hy = y + 8 * math.sin(t * 2 + k) * s
        heart_path(ctx, hx, hy, 60 * s)
        if filled:
            ctx.set_source_rgba(*hexc('#e5485e'), alpha)
            ctx.fill_preserve()
            ctx.set_source_rgba(*INK, alpha)
        else:
            ctx.set_source_rgba(*hexc('#f4e6c4'), alpha)
        ctx.set_line_width(5 * s)
        ctx.stroke()


def draw_subtitle(ctx, t):
    cur = None
    for s0, s1, spk, text in TL['subs']:
        if s0 <= t <= s1:
            cur = (s0, s1, spk, text)
            break
    if not cur:
        return
    s0, s1, spk, text = cur
    size = 58
    ctx.select_font_face(SUB_FONT)
    ctx.set_font_size(size)
    words = text.split()
    lines, line = [], ''
    for w in words:
        trial = (line + ' ' + w).strip()
        if ctx.text_extents(trial).x_advance > 900 and line:
            lines.append(line)
            line = w
        else:
            line = trial
    lines.append(line)
    if len(lines) == 2:                                # balance two lines
        best = None
        for i in range(1, len(words)):
            a, b = ' '.join(words[:i]), ' '.join(words[i:])
            wa, wb = ctx.text_extents(a).x_advance, ctx.text_extents(b).x_advance
            if max(wa, wb) <= 900 and (best is None or max(wa, wb) < best[0]):
                best = (max(wa, wb), [a, b])
        if best:
            lines = best[1]
    lh = size * 1.12
    bottom = 1530
    top = bottom - lh * len(lines)
    widest = max(ctx.text_extents(l).x_advance for l in lines)
    pad = 26
    a = clamp((t - s0) / 0.08) * clamp((s1 - t) / 0.08)
    x0, x1 = W / 2 - widest / 2 - pad, W / 2 + widest / 2 + pad
    y0, y1 = top - 14, bottom + 22
    r = 26
    ctx.new_path()
    ctx.arc(x0 + r, y0 + r, r, math.pi, 1.5 * math.pi)
    ctx.arc(x1 - r, y0 + r, r, 1.5 * math.pi, 2 * math.pi)
    ctx.arc(x1 - r, y1 - r, r, 0, 0.5 * math.pi)
    ctx.arc(x0 + r, y1 - r, r, 0.5 * math.pi, math.pi)
    ctx.close_path()
    ctx.set_source_rgba(0.03, 0.02, 0.06, 0.55 * a)
    ctx.fill()
    col = SUB_COLORS[spk]
    for i, l in enumerate(lines):
        y = top + lh * (i + 1) - 12
        text_center(ctx, l, W / 2, y, SUB_FONT, size, col + (a,), outline=(0.02, 0.01, 0.04, a), ow=7)


def draw_title(ctx, t):
    a = 1 - smooth((t - 5.6) / 0.9)
    if a <= 0:
        return
    y = 250 + 6 * math.sin(t * 1.4)
    ctx.save()
    text_center(ctx, 'Alice', W / 2 + 4, y + 8, TITLE_FONT, 210, (0, 0, 0, 0.45 * a), bold=True)
    text_center(ctx, 'Alice', W / 2, y, TITLE_FONT, 210, hexc('#f4e6c4', a), outline=hexc('#120c18', a), ow=14, bold=True)
    # a dangling spider on a thread from the i
    sx = W / 2 + 128
    sy = 120 + 30 * math.sin(t * 1.1) + 40
    ctx.move_to(sx, 0)
    ctx.line_to(sx, sy)
    ctx.set_source_rgba(0.9, 0.9, 0.95, 0.5 * a)
    ctx.set_line_width(1.5)
    ctx.stroke()
    ctx.restore()
    ctx.arc(sx, sy + 8, 9, 0, 2 * math.pi)
    ctx.set_source_rgba(*INK, a)
    ctx.fill()
    for k in range(4):
        for side in (-1, 1):
            ctx.move_to(sx, sy + 6 + k * 3)
            ctx.line_to(sx + side * 16, sy + k * 6)
            ctx.line_to(sx + side * 20, sy + 10 + k * 6)
    ctx.set_line_width(2)
    ctx.stroke()


def draw_bats(ctx, t):
    t0, _ = act_time('bats')
    u = t - t0
    if not (0 <= u <= 4.5):
        return
    for k in range(3):
        f = (u - k * 0.35) / 3.6
        if not (0 <= f <= 1):
            continue
        x = lerp(1150, -80, f)
        y = 520 + 60 * k - 120 * math.sin(math.pi * f) + 15 * math.sin(u * 3 + k)
        flap = math.sin(u * 2 * math.pi * 6 + k)
        s = 0.8 - 0.15 * k
        ctx.save()
        ctx.translate(x, y)
        ctx.scale(s, s)
        ctx.set_source_rgb(*hexc('#06060a'))
        ellipse(ctx, 0, 0, 10, 14)
        ctx.fill()
        for side in (-1, 1):
            ctx.move_to(0, -4)
            ctx.curve_to(side * 20, -20 - 20 * flap, side * 40, -10 - 25 * flap, side * 58, -6 - 22 * flap)
            ctx.curve_to(side * 46, 6, side * 34, -2, side * 24, 10)
            ctx.curve_to(side * 16, 4, side * 8, 8, 0, 6)
            ctx.close_path()
            ctx.fill()
        ctx.restore()


def draw_fog(ctx, t, y0, alpha=0.1):
    for k in range(3):
        x = ((t * (8 + 4 * k) + k * 400) % (W + 900)) - 450
        ellipse(ctx, x, y0 + k * 60, 420, 60)
        ctx.set_source(radial(ctx, x, y0 + k * 60, 420, [(0, (0.75, 0.82, 0.95, alpha)), (1, (0.75, 0.82, 0.95, 0))]))
        ctx.fill()


def draw_wisp(ctx, t, look_face=0.0):
    t0, d = act_time('steam_rise')
    ti, di = act_time('inhale')
    if t < t0 or t > ti + 3.3:
        return
    grow = smooth((t - t0) / 3.0)
    gone = smooth((t - ti - 1.3) / 1.9)
    s = 0.36 * grow * (1 - gone)
    if s <= 0.005:
        return
    # rising column of vapour from the rim
    for k in range(7):
        f = ((t * 0.35 + k / 7) % 1.0)
        yy = lerp(KITCHEN['pot_rim'][1] - 20, WISP[1] + 40, f)
        xx = WISP[0] + 30 * math.sin(f * 6 + k + t)
        r = 50 + 40 * f
        ctx.arc(xx, yy, r, 0, 2 * math.pi)
        ctx.set_source(radial(ctx, xx, yy, r, [(0, (0.92, 0.95, 1, 0.22 * grow * (1 - gone))), (1, (0.92, 0.95, 1, 0))]))
        ctx.fill()
    # drift toward Alice while she breathes it in
    ax, ay = NAMED['steam'][0], NAMED['steam'][1] + 25 * 0.82
    wx = lerp(WISP[0], ax, gone)
    wy = lerp(WISP[1], ay, gone) + 10 * math.sin(t * 1.6)
    ctx.save()
    ctx.translate(wx, wy)
    ctx.scale(s, s)
    for k in range(4):
        pts = [(x * (1 + 0.05 * k) + 6 * math.sin(t * 2 + i), y * (1 + 0.05 * k)) for i, (x, y) in enumerate(GHOST_PTS)]
        ctx.new_path()
        spline(ctx, pts, corners=GHOST_CORNERS)
        ctx.set_source_rgba(0.93, 0.96, 1.0, 0.16)
        ctx.fill()
    if look_face > 0:
        for side in (-1, 1):
            ellipse(ctx, side * 60, -100, 18, 30)
            ctx.set_source_rgba(0.22, 0.26, 0.4, 0.85 * look_face)
            ctx.fill()
        ctx.new_path()
        ctx.move_to(-30, 20)
        ctx.curve_to(-10, 45, 10, 45, 30, 20)
        ctx.set_source_rgba(0.22, 0.26, 0.4, 0.85 * look_face)
        ctx.set_line_width(9)
        ctx.stroke()
    ctx.restore()


def draw_inhale_stream(ctx, t, g):
    t0, d = act_time('inhale')
    u = t - t0
    if not (1.1 <= u <= 3.4):
        return
    mx, my = g['x'] + 2 * g['s'], g['y'] + 32 * g['s']
    strength = smooth((u - 1.1) / 0.4) * (1 - smooth((u - 3.0) / 0.4))
    for k in range(14):
        f = ((u * 0.9 + k / 14) % 1.0)
        sx, sy = WISP[0] - 20, WISP[1] + 60
        x = lerp(sx, mx, f) + 25 * math.sin(f * 7 + k) * (1 - f)
        y = lerp(sy, my, f) - 40 * math.sin(math.pi * f)
        r = lerp(16, 4, f)
        ctx.arc(x, y, r, 0, 2 * math.pi)
        ctx.set_source(radial(ctx, x, y, r, [(0, (0.95, 0.97, 1, 0.7 * strength)), (1, (0.95, 0.97, 1, 0))]))
        ctx.fill()


def draw_burst_hearts(ctx, t, ax, ay):
    t0, _ = act_time('hearts_burst')
    u = t - t0
    if not (0 <= u <= 2.6):
        return
    for k in range(9):
        a = -math.pi / 2 + (k - 4) * 0.33
        dist = 80 + 260 * (1 - math.exp(-u * 2.2))
        x = ax + math.cos(a) * dist
        y = ay - 60 + math.sin(a) * dist - 40 * u
        s = 22 + 10 * hash01(k, 3)
        al = 1 - smooth((u - 1.6) / 1.0)
        heart_path(ctx, x, y, s * 2 * ease_out_back(u / 0.3))
        ctx.set_source_rgba(*hexc('#e5485e'), al)
        ctx.fill_preserve()
        ctx.set_source_rgba(*INK, al)
        ctx.set_line_width(3)
        ctx.stroke()


def draw_yum(ctx, t, x, y, t0=None):
    t0 = act_time('yum_text')[0] if t0 is None else t0
    u = t - t0
    if u < 0 or u > 3.5:
        return
    sc = ease_out_back(u / 0.35)
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(-0.12 + 0.04 * math.sin(t * 2))
    ctx.scale(sc, sc)
    text_center(ctx, 'Yum!', 0, 0, HAND_FONT, 120, hexc('#f4e6c4'), outline=hexc('#120c18'), ow=10)
    ctx.restore()


# ── frame ────────────────────────────────────────────────────────────────────
BG_CACHE = {}


def background_surface(scene, cam):
    key = (scene, cam)
    if key in BG_CACHE:
        return BG_CACHE[key]
    if len(BG_CACHE) > 24:
        BG_CACHE.clear()
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
    ctx = cairo.Context(surf)
    apply_cam(ctx, cam)
    {'night': bg_night, 'kitchen': bg_kitchen, 'supper': bg_supper, 'end': bg_end}[scene](ctx)
    BG_CACHE[key] = surf
    return surf


def apply_cam(ctx, cam):
    cx, cy, z = cam
    ctx.translate(W / 2, H / 2)
    ctx.scale(z, z)
    ctx.translate(-cx, -cy)


def render_frame(frame):
    t = frame / FPS
    scene = scene_at(t)
    apos = base_pos('A', t, scene)
    spos = base_pos('S', t, scene)
    # alice first (candies depend on her), using a provisional look-target set
    look = look_targets(scene, apos, spos, {}, t)
    g = alice_state(t, scene, frame, look)
    alice_cache.clear()
    alice_cache[round(t, 4)] = g
    candies = candies_state(t, scene)
    look = look_targets(scene, (g['x'], g['y']), spos, candies, t)
    g['gaze'] = gaze_vec('A', t, look, (g['x'], g['y'] - 100 * g['s']))
    c = simmer_state(t, scene, frame, look, (g['x'], g['y']))

    cam = shot_camera(t, scene, apos if apos else None, spos)
    if scene == 'kitchen' and last_event(SHOT_EV, t)[1] == 'alice_close':
        cam = shot_camera(t, scene, (round(g['x'] - 4 * math.sin(t * 0.7), 0), round(apos[1], 0)), spos)

    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
    ctx = cairo.Context(surf)
    ctx.set_source_surface(background_surface(scene, cam), 0, 0)
    ctx.paint()
    ctx.save()
    apply_cam(ctx, cam)

    if scene == 'night':
        draw_bats(ctx, t)
        pumpkin(ctx, 880, 1610, 62, t, 0.5 + 0.5 * vnoise(t * 6, 1))
        pumpkin(ctx, 190, 1700, 48, t, 0.5 + 0.5 * vnoise(t * 6, 2))
        draw_fog(ctx, t, 1430, 0.09)
    elif scene == 'kitchen':
        dyn_kitchen(ctx, t)
    elif scene == 'supper':
        dyn_supper(ctx, t)

    if c:
        draw_cauldron(ctx, c, t, frame)
        if scene == 'kitchen':
            draw_steam_squiggles(ctx, c['x'], c['y'], c['s'], t, 0.5)
    if scene == 'kitchen':
        tw, _ = act_time('wisp_face')
        face = smooth((t - tw) / 0.4) * (1 - smooth((t - tw - 3.0) / 0.6))
        draw_wisp(ctx, t, face)
        for kind, pos in candies.items():
            draw_candy(ctx, kind, pos[0], pos[1], 22, pos[2])
    if scene == 'night':
        draw_thought_bubbles(ctx, t, (g['x'], g['y'] - 250 * g['s']))
    if scene != 'end':
        draw_ghost(ctx, g, t, frame, inside=g['inside'])
    if scene == 'kitchen':
        draw_inhale_stream(ctx, t, g)
    if scene == 'night':
        draw_yum(ctx, t, 235, 950)
    if scene == 'kitchen':
        draw_burst_hearts(ctx, t, g['x'], g['y'])

    if scene == 'supper':
        fg_supper(ctx)
        th, _ = act_time('hearts_float')
        if t >= th:
            f = smooth((t - th) / 0.8)
            draw_hearts(ctx, g['x'] + 175, g['y'] - 170 - 25 * (t - th), 0.9 * f, t, f)
    if scene == 'end':
        draw_end(ctx, t, g, frame)
    ctx.restore()

    if scene != 'end':
        vignette(ctx, 0.5 if scene != 'kitchen' else 0.6)
    if t < 7:
        draw_title(ctx, t)
    # later "Yum!"s pop in screen space so close-ups never clip them
    if scene == 'kitchen':
        draw_yum(ctx, t, 270, 430, act_time('hearts_burst')[0])
    if scene == 'supper':
        draw_yum(ctx, t, 250, 360, act_time('hearts_float')[0])
    draw_subtitle(ctx, t)
    return surf


def draw_end(ctx, t, g, frame):
    t0 = SCENE_START['end']
    u = t - t0
    # the original drawing, pinned up like a treasured picture
    ph = photo_surface()
    pw, phh = ph.get_width(), ph.get_height()
    sc = 0.92
    ctx.save()
    ctx.translate(540, 860 + 30 * (1 - smooth(u / 0.8)))
    ctx.rotate(-0.045)
    ctx.scale(sc, sc)
    ctx.rectangle(-pw / 2 - 22, -phh / 2 - 22, pw + 44, phh + 70)
    ctx.set_source_rgba(0, 0, 0, 0.4)
    ctx.fill()
    ctx.rectangle(-pw / 2 - 26, -phh / 2 - 26, pw + 52, phh + 74)
    ctx.set_source_rgb(*hexc('#f4efe4'))
    ctx.fill()
    ctx.set_source_surface(ph, -pw / 2, -phh / 2)
    ctx.paint()
    ctx.rectangle(-30, -phh / 2 - 46, 60, 34)
    ctx.set_source_rgba(0.9, 0.85, 0.65, 0.75)
    ctx.fill()
    ctx.restore()
    text_center(ctx, 'Alice', 540, 210, TITLE_FONT, 150, hexc('#f4e6c4'), outline=hexc('#120c18'), ow=12, bold=True)
    a = smooth((u - 0.6) / 0.8)
    text_center(ctx, 'grown from an original drawing by Alice', 540, 1395, SUB_FONT, 50, hexc('#e9dcae', a))
    # Alice herself, small and waving, with the two hearts from the drawing
    gg = dict(g)
    gg.update(x=840, y=1600 + 10 * math.sin(t * 2.6), s=0.42, tilt=4 * math.sin(t * 1.2), flip=1.0, inside=[],
              heart=0)
    gg['armR'] = -60 + 28 * math.sin(u * 2 * math.pi * 1.4)
    cc = dict(S_DEF, **S_EMO['warm'])
    cc.update(x=250, y=1640, s=0.5, tilt=2 * math.sin(t * 0.8), squash=0.015 * math.sin(t * 1.9), blink=blink_amount('S', t),
              gaze=(0.5, -0.1), glow=0.9, gcol=(0.85, 0.75, 1.0), fire=0.0, blorps=[])
    draw_cauldron(ctx, cc, t, frame)
    draw_steam_squiggles(ctx, 250, 1640, 0.5, t, 0.5)
    draw_ghost(ctx, gg, t, frame)
    draw_hearts(ctx, 545, 1560 - 6 * math.sin(t * 1.3), 0.85, t, smooth((u - 1.0) / 0.6))


def render_range(args):
    start, end, path = args
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr0', '-s', f'{W}x{H}',
           '-r', str(FPS), '-i', '-', '-c:v', 'libx264rgb', '-qp', '0', '-preset', 'ultrafast', path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(start, end):
        surf = render_frame(f)
        surf.flush()
        proc.stdin.write(bytes(surf.get_data()))
        if (f - start) % 240 == 0:
            print(f'  [{start}-{end}] frame {f}', file=sys.stderr, flush=True)
    proc.stdin.close()
    proc.wait()
    return path


def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--still':
        os.makedirs(os.path.join(BUILD, 'stills'), exist_ok=True)
        for ts in sys.argv[2:]:
            f = int(float(ts) * FPS)
            render_frame(f).write_to_png(os.path.join(BUILD, 'stills', f'still_{float(ts):07.2f}.png'))
        return
    total = int(math.ceil(DURATION * FPS))
    workers = int(os.environ.get('WORKERS', os.cpu_count() or 4))
    nseg = workers * 3
    bounds = [round(total * i / nseg) for i in range(nseg + 1)]
    seg_dir = os.path.join(BUILD, 'segments')
    os.makedirs(seg_dir, exist_ok=True)
    jobs = [(bounds[i], bounds[i + 1], os.path.join(seg_dir, f'seg{i:02d}.mkv')) for i in range(nseg)]
    with Pool(workers) as pool:
        paths = pool.map(render_range, jobs, chunksize=1)
    with open(os.path.join(seg_dir, 'list.txt'), 'w') as fh:
        for p in paths:
            fh.write(f"file '{p}'\n")
    print(f'rendered {total} frames in {nseg} segments')


if __name__ == '__main__':
    main()
