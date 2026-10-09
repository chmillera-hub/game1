"""s13 - Bookend + title card ("NICE TRY, MY GUY.").  Music: resolve.

Every time is derived from cues / line timings (see _T).

  A  polaroid..title   CORKBOARD close-up (hard cut from s12's town square).
                       The lair corkboard, header now reads "PARTY PLANS" (s12's
                       sticky).  The old science-fair photo (empty chairs) is
                       pinned left; at +0.1 s a Polaroid of the block party
                       SLAPS in beside it (squash, impact ticks), a red pin
                       pops in, and the red string draws from the old photo to
                       the new one.  Slow push-in.
                       s13_l01 (narrator): on "AI" the camera slides down-left
                       (0.8 s, ease_in_out, pulling back a touch) to reveal the
                       cardboard robot cutout ($19.99, PROP) leaning on the wall
                       in a crooked party hat with a red balloon.  On "bad" its
                       visor blinks on for ONE ominous frame (+1 afterglow).
                       The AI pops in beside it (squash/stretch + sparkles),
                       gives the cutout a dry half-lid look, then (s13_l02,
                       "...be a good guy.") warmly straightens the party hat
                       with its left mitten, eyes to camera on "good guy",
                       slow blink.
  B  title..end        Hard cut: TITLE CARD on ai_bg.  Static sunburst,
                       "NICE TRY," / "MY GUY." letters drop in (Luckiest Guy),
                       taglines "A wall for harm." (brick red) and "A door for
                       everything else." (gold) slide up, a small wall builds
                       (3 thuds) and its service window rolls open (a heart
                       inside).  The AI pops in under the wall watching the
                       bricks; Malvo rises from the bottom-right waving (FOR
                       EFFORT star on his lapel); Hissy peeks in from the left
                       in a tiny party hat.  s13_l03 (nocap): AI looks at Malvo
                       on "Nice try," (Malvo sheepish), eyes to camera on "my
                       guy" + thumbs up, WINK + sparkle on "guy"; Malvo REAL
                       SMILE, Hissy nods.  hold: everything eases to a stop;
                       the last 1.0 s is static except blinks (thumbnail).
"""
import math

from engine import core
from engine.core import (W, H, text, text_width, saved, seg, clamp, lerp, ease_out_back,
                         ease_in_out, ease_out, ease_in, smoothstep, rrect, fill_stroke,
                         circle, ellipse, poly, hash01, noise1, blink_amount,
                         radial_glow)
from engine import props as P
from engine import ai_char as AI
from engine.ai_char import draw_ai
from engine import villain as V
from engine.villain import draw_villain
from engine import snake as SN

INK = "ink"

# ===========================================================================
# layout (logical px)
# ===========================================================================
# --- shot A: world coordinates of the lair corner ---------------------------
BOARD = (40.0, 150.0, 1060.0, 1080.0)     # corkboard outer frame x0, y0, x1, y1
OLD = (300.0, 560.0, 280.0, 215.0, -0.05)  # science-fair photo cx, cy, w, h, rot
POL = (660.0, 600.0, 300.0, 350.0, 0.06)   # party Polaroid cx, cy, w, h, rot
HEADER = (480.0, 268.0)
FLOOR_Y = 2205.0                           # lair floor line (world)
CUT = (-270.0, 1550.0, 0.7, -0.045)        # cutout head centre x, y, scale, lean
BALLOON = (-478.0, 1318.0)                 # balloon centre (world)
AIA = (24.0, 1318.0, 0.48)                 # AI beside the cutout (world)

# camera: screen = (world - C) * Z + S
CAM_S = (495.0, 760.0)
CAM_C0, CAM_Z0 = (480.0, 610.0), 1.3       # corkboard close-up
CAM_C1, CAM_Z1 = (-105.0, 1510.0), 1.0     # cutout two-shot after the slide
WORLD_RECT = (-680.0, -60.0, 1700.0, 2800.0)

# --- shot B: title card (screen coords) --------------------------------------
TX = 495.0                                 # composition centre x
T1_Y, T2_Y, T_SIZE = 368.0, 535.0, 150.0   # title lines (baselines) and size
TAG1_Y, TAG2_Y = 650.0, 730.0
WALL = (300.0, 810.0, 390.0, 240.0)
BURST_C = (495.0, 450.0)
WIN = (125.0, 60.0, 140.0, 120.0)
AIB = (440.0, 1192.0, 0.40)                # AI under the wall
HIS = (182.0, 1150.0, 0.68)                # Hissy head (peeking in from the left)
MAL = (795.0, 1505.0, 0.45)                # Malvo (waist; covered by the stage lip)
STAGE_Y = 1532.0                           # top of the foreground stage lip

# colours
CORK, CORK_DK, CORK_HI = "#c79a5b", "#a97c42", "#d8ae72"
FRAME, FRAME_HI, FRAME_DK = "#6b3f22", "#8c5a33", "#4a2a16"
STRING, STRING_DK = "#ff3b5c", "#7d0c2a"
PAPER, PAPER_DK = "#f6ecd6", "#e2cfa6"
PHOTO_W = "#f3efe6"
POL_W = "#fbfaf4"
BRICK_RED = "#e0674f"
GOLD, GOLD_DK = "#ffcf3a", "#d99a12"
HAT_COLS = ("#ff6fa8", "#ffd166", "#13a8a0")

# robot palette (prop bible 6.1 -- same as s01/s02)
CHROME, CHROME_SH, CHROME_DK = "#9aa3b5", "#6b7385", "#5d6474"
CHROME_HI, SHOULDER = "#c7cdd9", "#7d8496"
BEZEL, SLOT = "#262a35", "#1a1d26"
VISOR_ON, CORE = "#ff3b5c", "#ffd0d8"
CARD, CARD_DK = "#a5754a", "#7d5432"

# custom poses / expressions (registered under s13_ names; built-ins untouched)
_WAVE_A = V._arm(-300, -268, -296, -484, -math.pi / 2 - 0.30, cu=0.04, th=-0.25, sp=0.95,
                 pm=1.0, tf=-1)
_WAVE_B = V._arm(-306, -262, -338, -472, -math.pi / 2 + 0.24, cu=0.04, th=-0.25, sp=0.95,
                 pm=1.0, tf=-1)
V.ARM_POSES.setdefault("s13_wave_a", V._pose(_WAVE_A, V._REST_B))
V.ARM_POSES.setdefault("s13_wave_b", V._pose(_WAVE_B, V._REST_B))

AIX = {
    "half": {k: lerp(AI.EXPR["neutral"][k], AI.EXPR["unimpressed"][k], 0.6)
             for k in AI.EXPR["neutral"]},
}


# ===========================================================================
# timing (all from cues / lines)
# ===========================================================================
def _ws(info, lid, k):
    """Scene time the k-th word of line `lid` starts (fallback: even split)."""
    L = info.line(lid)
    try:
        return L.start + info._lip[lid]["word_starts"][k]
    except (KeyError, IndexError, TypeError):
        n = max(1, len(L.text.split()))
        return L.start + L.dur * min(k, n - 1) / n


_TCACHE = {}


def _T(info):
    key = (info.id, info.dur, tuple(sorted(info.cues.items())))
    if key in _TCACHE:
        return _TCACHE[key]
    L1, L2, L3 = info.line("s13_l01"), info.line("s13_l02"), info.line("s13_l03")
    T = {}
    T["pol"] = info.cue("polaroid")
    T["slap"] = T["pol"] + 0.10
    T["pin"] = T["pol"] + 0.15
    T["str0"] = T["pol"] + 0.42
    T["str1"] = T["str0"] + 0.45
    T["l1s"], T["l1e"] = L1.start, L1.end
    T["slide0"] = max(T["str1"] + 0.1, _ws(info, "s13_l01", 3) - 0.08)     # on "AI"
    T["slide1"] = T["slide0"] + 0.8
    T["bad"] = max(T["slide0"] + 0.5, _ws(info, "s13_l01", 7))             # "bad"
    T["l2s"], T["l2e"] = L2.start, L2.end
    T["ai_in"] = max(T["bad"] + 0.42, L2.start - 0.78)
    T["reach"] = L2.start + 0.04                 # mitten goes to the hat
    T["fix0"] = L2.start + 0.22                  # hat gets straightened
    T["fix1"] = T["fix0"] + 0.30
    T["good"] = max(_ws(info, "s13_l02", 3) - 0.06, T["fix1"] - 0.12)   # eyes to camera
    T["let_go"] = max(T["fix1"] + 0.12, L2.end - 0.25)
    T["title"] = info.cue("title")
    # slow warm blink, finished (eyes open, to camera) before the hard cut
    T["sblink"] = min(L2.end - 0.05, T["title"] - 0.55)
    T["title"] = info.cue("title")
    tt = T["title"]
    T["t1_in"] = tt - 0.03
    T["t2_in"] = tt + 0.45
    T["last_land"] = T["t2_in"] + (len("MY GUY.") - 1) * 0.045 + 0.10
    T["wall0"] = tt + 0.2
    T["tag1"] = tt + 0.6
    T["tag2"] = tt + 0.9
    T["win_open"] = tt + 1.0
    T["heart"] = tt + 1.38
    T["l3s"], T["l3e"] = L3.start, L3.end
    T["ai2_in"] = tt + 0.28
    T["mal_in"] = min(tt + 0.70, L3.start - 0.35)
    T["his_in"] = min(tt + 0.95, L3.start - 0.1)
    T["nice"] = L3.start
    T["my"] = _ws(info, "s13_l03", 2)
    T["guy"] = _ws(info, "s13_l03", 3)
    T["unwink"] = max(T["guy"] + 0.7, L3.end + 0.2)
    T["hold"] = info.cue("hold")
    T["end"] = info.dur
    T["fz1"] = info.dur - 1.0                    # from here: static except blinks
    T["fz0"] = max(T["unwink"] + 0.6, T["fz1"] - 0.75)
    _TCACHE[key] = T
    return T


def _tw(t, T):
    """Ambient/rig time: real time, then decelerates to a full stop at fz1."""
    f0, f1 = T["fz0"], T["fz1"]
    if t <= f0:
        return t
    d = max(1e-3, f1 - f0)
    u = min(t, f1) - f0
    return f0 + u - u * u / (2 * d)


def keyed(t, keys, trans=0.25):
    """[(time, name[, trans])...] -> (from, to, blend) with per-key transitions."""
    keys = sorted(keys, key=lambda k: k[0])
    prev, cur, start, tr = keys[0][1], keys[0][1], -1e9, trans
    for k in keys:
        if t >= k[0]:
            prev, cur, start = cur, k[1], k[0]
            tr = k[2] if len(k) > 2 else trans
        else:
            break
    return prev, cur, smoothstep(seg(t, start, start + tr))


def keyed_v(t, keys, trans=0.2):
    """[(time, (x, y)[, trans])...] -> eased vector."""
    keys = sorted(keys, key=lambda k: k[0])
    prev, cur, start, tr = keys[0][1], keys[0][1], -1e9, trans
    for k in keys:
        if t >= k[0]:
            prev, cur, start = cur, k[1], k[0]
            tr = k[2] if len(k) > 2 else trans
        else:
            break
    u = ease_in_out(seg(t, start, start + tr))
    return (lerp(prev[0], cur[0], u), lerp(prev[1], cur[1], u))


def slow_blink(t, t0, close=0.12, hold=0.08, open_=0.12):
    if t < t0 or t > t0 + close + hold + open_:
        return 0.0
    if t < t0 + close:
        return smoothstep((t - t0) / close)
    if t < t0 + close + hold:
        return 1.0
    return 1.0 - smoothstep((t - t0 - close - hold) / open_)


def _pop_squash(t, t0, dur=0.5):
    """(scale, sx, sy): pop from 0 with overshoot plus a squash/stretch wobble."""
    if t < t0:
        return 0.0, 1.0, 1.0
    k = ease_out_back(seg(t, t0, t0 + 0.28), 2.2)
    u = seg(t, t0, t0 + dur)
    w = math.sin(u * math.pi * 3.0) * (1 - u) * 0.16
    return k, 1 - w, 1 + w


# ===========================================================================
# small drawing helpers
# ===========================================================================
def _fs(ctx, fc, sc=INK, w=5.0):
    fill_stroke(ctx, fc, sc, w)


def _round_poly(ctx, pts, r):
    n = len(pts)
    ctx.new_sub_path()
    for i in range(n):
        x0, y0 = pts[i - 1]
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        d1 = math.hypot(x0 - x1, y0 - y1)
        d2 = math.hypot(x2 - x1, y2 - y1)
        rr = min(r, d1 / 2, d2 / 2)
        ax, ay = x1 + (x0 - x1) * rr / d1, y1 + (y0 - y1) * rr / d1
        bx, by = x1 + (x2 - x1) * rr / d2, y1 + (y2 - y1) * rr / d2
        if i == 0:
            ctx.move_to(ax, ay)
        else:
            ctx.line_to(ax, ay)
        ctx.curve_to(ax + (x1 - ax) * 0.55, ay + (y1 - ay) * 0.55,
                     bx + (x1 - bx) * 0.55, by + (y1 - by) * 0.55, bx, by)
    ctx.close_path()


def _capsule(ctx, cx, cy, w, h):
    rrect(ctx, cx - w / 2, cy - h / 2, w, h, h / 2)


def _rot(px, py, a):
    c, s = math.cos(a), math.sin(a)
    return px * c - py * s, px * s + py * c


def _qbez(p0, p1, p2, n=28):
    return [((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0],
             (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1])
            for u in (i / n for i in range(n + 1))]


def _partial(ctx, pts, p):
    """Path along the first fraction p of a polyline; returns the tip."""
    lens = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])]
    want = sum(lens) * clamp(p)
    ctx.move_to(*pts[0])
    acc, tip = 0.0, pts[0]
    for (a, b), L in zip(zip(pts, pts[1:]), lens):
        if acc + L >= want:
            f = (want - acc) / L if L > 1e-9 else 1.0
            tip = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
            ctx.line_to(*tip)
            return tip
        ctx.line_to(*b)
        acc += L
        tip = b
    return tip


def _pin(ctx, x, y, col, s=1.0):
    circle(ctx, x + 3 * s, y + 4 * s, 11 * s)
    core.fill(ctx, (0, 0, 0, 0.35))
    circle(ctx, x, y, 11 * s)
    _fs(ctx, col, INK, 3 * s)
    circle(ctx, x - 3.5 * s, y - 3.5 * s, 3.4 * s)
    core.fill(ctx, (1, 1, 1, 0.9))


def _red_string(ctx, pts, p=1.0):
    for w, col in ((6.5, STRING_DK), (3.6, STRING)):
        _partial(ctx, pts, p)
        core.stroke(ctx, col, w)


def _string_pts(a, b, sag=34):
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + sag
    return _qbez(a, (mx, my), b)


def _star5_path(c, x, y, r, rot=0.0, inner=0.47):
    c.new_sub_path()
    for i in range(10):
        a = rot - math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * inner
        px, py = x + math.cos(a) * rr, y + math.sin(a) * rr
        if i == 0:
            c.move_to(px, py)
        else:
            c.line_to(px, py)
    c.close_path()


def _gold_star(c, x, y, r, rot=0.0, lw=5.0):
    """FOR EFFORT gold star (same drawing as s09)."""
    _star5_path(c, x, y, r, rot)
    c.set_line_join(1)
    fill_stroke(c, GOLD, "ink", lw)
    c.save()
    _star5_path(c, x, y, r, rot)
    c.clip()
    _star5_path(c, x + r * 0.16, y + r * 0.2, r, rot)
    c.rectangle(x - 2 * r, y - 2 * r, 4 * r, 4 * r)
    c.set_fill_rule(1)
    core.set_color(c, GOLD_DK)
    c.fill()
    c.set_fill_rule(0)
    c.restore()
    _star5_path(c, x, y, r, rot)
    core.stroke(c, "ink", lw)
    ellipse(c, x - r * 0.2, y - r * 0.3, r * 0.17, r * 0.1, -0.6)
    c.set_source_rgba(1, 1, 1, 0.85)
    c.fill()


def party_hat(c, x, y, s, rot, h=170.0, b=118.0):
    """Prop bible 6.19: striped cone (pink/yellow/teal) with a pom-pom.
    (x, y) = centre of the hat's base."""
    with saved(c, x, y, s, rot) as cc:
        def cone():
            cc.move_to(-b / 2, 0)
            cc.line_to(-5, -h + 4)
            cc.curve_to(-2, -h - 2, 2, -h - 2, 5, -h + 4)
            cc.line_to(b / 2, 0)
            cc.curve_to(b / 4, 12, -b / 4, 12, -b / 2, 0)
            cc.close_path()
        cone()
        core.fill(cc, HAT_COLS[0])
        cc.save()
        cone()
        cc.clip()
        for i in range(-3, 9):
            y0 = -h + i * 34
            poly(cc, [(-b, y0 + 28), (b, y0 - 14), (b, y0 + 2), (-b, y0 + 44)])
            core.fill(cc, HAT_COLS[1 + (i % 2)])
        cc.rectangle(-b, -14, 2 * b, 30)                       # one shadow tone
        core.fill(cc, (0, 0, 0, 0.14))
        cc.restore()
        cone()
        core.stroke(cc, INK, 5)
        # pom-pom
        for (px, py, r) in ((0, -h - 6, 20), (-12, -h + 2, 11), (12, -h + 2, 11)):
            circle(cc, px, py, r)
            _fs(cc, "#fff6d6", INK, 4)
        circle(cc, 0, -h - 6, 20)
        core.fill(cc, "#fff6d6")
        circle(cc, -6, -h - 12, 5)
        core.fill(cc, "white")


def balloon(c, x, y, s, rot, knot_to):
    """Prop bible 6.4: red balloon 90x110, knot, curly string to knot_to."""
    kx, ky = x - math.sin(rot) * -58 * s, y + math.cos(rot) * 58 * s
    # string (curly)
    tx, ty = knot_to
    pts = []
    for i in range(17):
        u = i / 16
        px = lerp(kx, tx, u) + math.sin(u * math.pi * 3.0) * 12 * s * (1 - u * 0.4)
        py = lerp(ky, ty, u)
        pts.append((px, py))
    core.smooth_path(c, pts)
    core.stroke(c, INK, 3)
    with saved(c, x, y, s, rot) as cc:
        poly(cc, [(0, 52), (-11, 66), (11, 66)])
        _fs(cc, "#c41f3d", INK, 3.5)
        ellipse(cc, 0, 0, 45, 55)
        _fs(cc, "#e8314f", INK, 5)
        cc.save()
        ellipse(cc, 0, 0, 45, 55)
        cc.clip()
        ellipse(cc, 14, 14, 44, 54)
        cc.rectangle(-60, -70, 120, 140)
        cc.set_fill_rule(1)
        core.fill(cc, "#b81d39")
        cc.set_fill_rule(0)
        cc.restore()
        ellipse(cc, 0, 0, 45, 55)
        core.stroke(cc, INK, 5)
        ellipse(cc, -15, -22, 8, 14, 0.5)
        core.fill(cc, (1, 1, 1, 0.75))


# ===========================================================================
# THE ROBOT cutout (prop bible 6.1; same drawing as s02's cutout)
# local origin = head centre, s = 1
# ===========================================================================
HEAD = [(-210, -190), (210, -190), (165, 190), (-165, 190)]
SH_PTS = [(-310, 385), (-306, 268), (-205, 232), (205, 232), (306, 268), (310, 385)]


def _robot_silhouette(ctx, dx=0.0, dy=0.0):
    rrect(ctx, -235 + dx, 330 + dy, 470, 640, 40)
    _round_poly(ctx, [(x + dx, y + dy) for x, y in SH_PTS], 46)
    _round_poly(ctx, [(x + dx, y + dy) for x, y in HEAD], 60)
    for sx in (-1, 1):
        circle(ctx, sx * 202 + dx, -8 + dy, 46)
        circle(ctx, sx * 128 + dx, -250 + dy, 17)
        ctx.rectangle(sx * 128 - 12 + dx, -244 + dy, 24, 64)


def draw_cutout(ctx, on=0.0):
    """Cardboard robot cutout. on: 0 = printed visor, 1 = OMINOUS visor frame."""
    # kickstand (behind), then the cardboard thickness (right + bottom)
    core.poly(ctx, [(150, 520), (330, 970), (150, 970)])
    _fs(ctx, CARD_DK, INK, 5)
    _robot_silhouette(ctx, 12, 12)
    core.fill(ctx, CARD)
    _robot_silhouette(ctx, 12, 12)
    core.stroke(ctx, INK, 5)
    # torso + neck + shoulders
    rrect(ctx, -235, 330, 470, 640, 40)
    _fs(ctx, CHROME_DK)
    ctx.move_to(0, 400)
    ctx.line_to(0, 900)
    core.stroke(ctx, INK, 4)
    for sx in (-1, 1):
        circle(ctx, sx * 150, 450, 11)
        _fs(ctx, CHROME_SH, INK, 3)
    rrect(ctx, -86, 170, 172, 90, 14)
    _fs(ctx, CHROME_SH)
    for yy in (200, 226):
        ctx.move_to(-80, yy)
        ctx.line_to(80, yy)
    core.stroke(ctx, INK, 3.5)
    _round_poly(ctx, SH_PTS, 46)
    _fs(ctx, SHOULDER)
    ctx.save()
    _round_poly(ctx, SH_PTS, 46)
    ctx.clip()
    ctx.rectangle(-320, 330, 640, 80)
    core.fill(ctx, CHROME_SH)
    ctx.restore()
    _round_poly(ctx, SH_PTS, 46)
    core.stroke(ctx, INK, 5)
    for sx in (-1, 1):
        ctx.move_to(sx * 120, 240)
        ctx.line_to(sx * 132, 380)
        core.stroke(ctx, INK, 3.5)
        for yy in (290, 345):
            circle(ctx, sx * 250, yy, 9)
            _fs(ctx, CHROME_HI, INK, 3)
    # stencilled "PROP" on the screen-left shoulder plate
    with saved(ctx, -205, 352, 1.0, -0.05) as c:
        text(c, "PROP", 0, 0, 62, (0.12, 0.1, 0.14, 0.72), "black")
        for xx in (-52, -14, 22, 58):
            c.rectangle(xx, -50, 5, 54)
        core.fill(c, SHOULDER)
    # antennae + ear discs
    for sx in (-1, 1):
        rrect(ctx, sx * 128 - 12, -244, 24, 64, 6)
        _fs(ctx, CHROME_SH, INK, 4)
        circle(ctx, sx * 128, -250, 17)
        _fs(ctx, CHROME, INK, 4)
        if on > 0.02:
            circle(ctx, sx * 128, -250, 9)
            core.fill(ctx, core.alpha(VISOR_ON, on))
    for sx in (-1, 1):
        circle(ctx, sx * 202, -8, 46)
        _fs(ctx, SHOULDER)
        circle(ctx, sx * 202, -8, 22)
        _fs(ctx, CHROME_SH, INK, 3.5)
    # head
    _round_poly(ctx, HEAD, 60)
    core.fill(ctx, CHROME)
    ctx.save()
    _round_poly(ctx, HEAD, 60)
    ctx.clip()
    ctx.move_to(-260, 26)
    ctx.curve_to(-120, 44, 120, 44, 260, 26)
    ctx.line_to(260, 260)
    ctx.line_to(-260, 260)
    ctx.close_path()
    core.fill(ctx, CHROME_SH)
    ctx.move_to(-190, -168)
    ctx.line_to(-120, -168)
    ctx.line_to(-176, -112)
    ctx.line_to(-200, -112)
    ctx.close_path()
    core.fill(ctx, CHROME_HI)
    ctx.move_to(-230, -128)
    ctx.line_to(230, -128)
    for sx in (-1, 1):
        ctx.move_to(sx * 172, 18)
        ctx.line_to(sx * 132, 190)
    core.stroke(ctx, INK, 3.5)
    ctx.restore()
    _round_poly(ctx, HEAD, 60)
    core.stroke(ctx, INK, 5.5)
    for (rx, ry) in ((-176, -158), (176, -158), (-140, 150), (140, 150)):
        circle(ctx, rx, ry, 8)
        _fs(ctx, CHROME_HI, INK, 3)
    # mouth grille
    rrect(ctx, -100, 62, 200, 78, 18)
    _fs(ctx, CHROME_SH, INK, 4)
    for k in range(5):
        rrect(ctx, -64 + k * 32 - 9, 76, 18, 50, 9)
        core.fill(ctx, SLOT)
    # visor (printed red; `on` = the one ominous frame)
    vx, vy = 0.0, -30.0
    _capsule(ctx, vx, vy, 344, 106)
    _fs(ctx, BEZEL, INK, 5)
    ctx.save()
    _capsule(ctx, vx, vy, 300, 70)
    ctx.clip()
    core.bg(ctx, core.mixc(VISOR_ON, "#ff8a9c", on * 0.6))
    ctx.move_to(vx - 118, vy)
    ctx.line_to(vx + 118, vy)
    core.stroke(ctx, core.mixc(CORE, "#ffffff", on), 7 + 6 * on)
    circle(ctx, vx, vy, 40)
    core.fill(ctx, core.mixc("#c41f3d", "#ff3b5c", on))
    ctx.set_line_width(9)
    core.set_color(ctx, CORE)
    for k in range(3):
        a0 = k * 2 * math.pi / 3 + 0.4
        ctx.new_sub_path()
        ctx.arc(vx, vy, 30, a0 + 0.32, a0 + 2 * math.pi / 3 - 0.32)
    ctx.stroke()
    circle(ctx, vx, vy, 12 + 4 * on)
    core.fill(ctx, "white")
    ctx.move_to(vx - 128, vy - 22)
    ctx.line_to(vx - 70, vy - 22)
    core.stroke(ctx, (1, 1, 1, 0.42), 6)
    ctx.restore()
    _capsule(ctx, vx, vy, 300, 70)
    core.stroke(ctx, INK, 4)
    # angry brow plates
    ctx.save()
    _round_poly(ctx, HEAD, 60)
    ctx.clip()
    brow = [(-215, -124), (-24, -92), (24, -92), (215, -124), (215, -100), (26, -70),
            (-26, -70), (-215, -100)]
    _round_poly(ctx, brow, 8)
    _fs(ctx, CHROME_SH, INK, 4.5)
    ctx.restore()
    # price tag on a string from the screen-right antenna
    ctx.move_to(128, -250)
    ctx.curve_to(190, -250, 230, -200, 252, -150)
    core.stroke(ctx, INK, 3)
    with saved(ctx, 262, -118, 1.0, 0.32) as c:
        _round_poly(c, [(-62, -30), (50, -30), (66, 0), (50, 30), (-62, 30)], 8)
        _fs(c, "#f6ecd6", INK, 4)
        circle(c, 44, 0, 6)
        _fs(c, CARD_DK, INK, 2.5)
        text(c, "$19.99", -6, 11, 30, "ink", "round")


# ===========================================================================
# photos
# ===========================================================================
def _chair(c, x, y, s=1.0, col="#7d7a84"):
    """Tiny grey folding chair seen from the back (empty)."""
    c.rectangle(x - 9 * s, y - 16 * s, 18 * s, 11 * s)
    core.fill(c, col)
    c.rectangle(x - 9 * s, y - 3 * s, 18 * s, 4 * s)
    core.fill(c, col)
    c.move_to(x - 8 * s, y + 1 * s)
    c.line_to(x - 10 * s, y + 10 * s)
    c.move_to(x + 8 * s, y + 1 * s)
    c.line_to(x + 10 * s, y + 10 * s)
    core.stroke(c, col, 2.2 * s)


def science_photo(c, w, h):
    """Prop bible 6.9, medium version: faded snapshot, kid Malvo + bulb robot,
    three rows of EMPTY folding chairs, limp PARTICIPANT ribbon.
    Drawn centred on (0, 0)."""
    rrect(c, -w / 2 + 7, -h / 2 + 9, w, h, 4)
    core.fill(c, (0, 0, 0, 0.32))
    rrect(c, -w / 2, -h / 2, w, h, 4)
    _fs(c, PHOTO_W, INK, 4)
    px0, py0, pw, ph = -w / 2 + 12, -h / 2 + 12, w - 24, h - 44
    c.save()
    c.rectangle(px0, py0, pw, ph)
    c.clip()
    core.bg(c, "#b9b0c2")                                   # faded gym wall
    for k in range(5):                                      # wall panels
        c.move_to(px0 + pw * (k + 0.5) / 5, py0)
        c.line_to(px0 + pw * (k + 0.5) / 5, py0 + ph * 0.5)
    core.stroke(c, "#aaa1b4", 2)
    # pennant string
    for k in range(9):
        fx = px0 + 10 + k * (pw - 20) / 8
        fy = py0 + 10 + 6 * math.sin(k / 8 * math.pi)
        poly(c, [(fx - 9, fy), (fx + 9, fy), (fx, fy + 15)])
        core.fill(c, ["#c9a3a3", "#a9b8c9", "#c9c19a"][k % 3])
    c.move_to(px0, py0 + 10)
    c.curve_to(px0 + pw * 0.3, py0 + 18, px0 + pw * 0.7, py0 + 18, px0 + pw, py0 + 10)
    core.stroke(c, "#8a8494", 1.5)
    c.rectangle(px0, py0 + ph * 0.5, pw, ph)
    core.fill(c, "#a59c90")                                  # floor
    # kid Malvo behind the table: tiny cape, bald head, monocle, proud smile
    kx, ky = px0 + pw * 0.34, py0 + ph * 0.30
    poly(c, [(kx - 19, ky + 12), (kx + 19, ky + 12), (kx + 25, ky + 46), (kx - 25, ky + 46)])
    _fs(c, "#7d5f86", "#4a3a44", 2)
    poly(c, [(kx - 19, ky + 12), (kx - 30, ky + 20), (kx - 27, ky + 46), (kx - 22, ky + 46)])
    core.fill(c, "#9a5a64")
    circle(c, kx, ky, 15)
    _fs(c, "#e6cdb6", "#4a3a44", 2)
    circle(c, kx + 6, ky - 1, 4.6)
    core.stroke(c, "#c9a84f", 1.8)
    circle(c, kx - 5, ky - 1, 1.6)
    circle(c, kx + 6, ky - 1, 1.6)
    core.fill(c, "#4a3a44")
    c.arc(kx, ky + 4, 5.5, 0.3, math.pi - 0.3)
    core.stroke(c, "#4a3a44", 1.6)
    # homemade robot with a light bulb on its head
    rx_, ry_ = px0 + pw * 0.64, py0 + ph * 0.33
    c.rectangle(rx_ - 15, ry_ - 2, 30, 30)
    _fs(c, "#9aa0a8", "#4a4650", 2)
    c.rectangle(rx_ - 11, ry_ + 6, 9, 6)
    c.rectangle(rx_ + 2, ry_ + 6, 9, 6)
    core.fill(c, "#6a707c")
    c.rectangle(rx_ - 3, ry_ - 8, 6, 6)
    core.fill(c, "#8a8f98")
    circle(c, rx_, ry_ - 15, 8)
    _fs(c, "#f2e6a0", "#4a4650", 1.6)
    for a in (-2.4, -1.57, -0.74):
        c.move_to(rx_ + math.cos(a) * 12, ry_ - 15 + math.sin(a) * 12)
        c.line_to(rx_ + math.cos(a) * 18, ry_ - 15 + math.sin(a) * 18)
    core.stroke(c, "#d8cc86", 1.6)
    # folding table + limp ribbon
    ty = py0 + ph * 0.50
    c.rectangle(px0 + pw * 0.12, ty, pw * 0.70, 8)
    _fs(c, "#8a7f74", "#4a4650", 1.6)
    for lx in (0.16, 0.78):
        c.move_to(px0 + pw * lx, ty + 8)
        c.line_to(px0 + pw * lx, ty + 26)
    core.stroke(c, "#6f6860", 2)
    rbx, rby = px0 + pw * 0.48, ty + 16
    circle(c, rbx, rby, 6.5)
    core.fill(c, "#7f9bc4")
    poly(c, [(rbx - 4, rby + 4), (rbx - 7, rby + 18), (rbx, rby + 15)])
    poly(c, [(rbx + 2, rby + 4), (rbx + 3, rby + 19), (rbx + 7, rby + 15)])
    core.fill(c, "#7f9bc4")
    # three rows of EMPTY grey folding chairs
    for row in range(3):
        yy = py0 + ph * (0.74 + row * 0.115)
        for k in range(7):
            xx = px0 + 16 + k * (pw - 32) / 6 + (row % 2) * 6
            _chair(c, xx, yy, 0.9 + row * 0.12)
    # fade wash
    c.rectangle(px0, py0, pw, ph)
    core.fill(c, (0.95, 0.92, 0.85, 0.16))
    c.restore()
    c.rectangle(px0, py0, pw, ph)
    core.stroke(c, "#d8d2c4", 1.5)
    text(c, "science fair", -w / 2 + 18, h / 2 - 11, 20, "#8a8494", "round", "left")


def _townsfolk(c, x, y, r, skin, body, hap=1.0, arms_up=False, ph=0.0):
    """Tiny happy person (prop bible 6.3, mini): body + round head."""
    bw, bh = r * 1.9, r * 2.4
    if arms_up:
        for sx in (-1, 1):
            c.move_to(x + sx * bw * 0.35, y + r * 1.3)
            c.line_to(x + sx * bw * 0.75, y - r * 0.6 + sx * ph)
        core.stroke(c, INK, r * 0.5)
        for sx in (-1, 1):
            c.move_to(x + sx * bw * 0.35, y + r * 1.3)
            c.line_to(x + sx * bw * 0.75, y - r * 0.6 + sx * ph)
        core.stroke(c, body, r * 0.3)
    ellipse(c, x, y + r * 0.9 + bh * 0.45, bw / 2, bh / 2)
    _fs(c, body, INK, 2)
    circle(c, x, y, r)
    _fs(c, skin, INK, 2)
    for sx in (-1, 1):
        c.arc(x + sx * r * 0.38, y - r * 0.05, r * 0.2, math.pi + 0.3, 2 * math.pi - 0.3)
        core.stroke(c, INK, 1.6)
    c.arc(x, y + r * 0.22, r * 0.38, 0.25, math.pi - 0.25)
    core.stroke(c, INK, 1.6)


def party_photo(c, w, h):
    """The block-party Polaroid (§6.18 simplified). Centred on (0, 0)."""
    rrect(c, -w / 2, -h / 2, w, h, 5)
    _fs(c, POL_W, INK, 4)
    m = 18
    px0, py0, pw = -w / 2 + m, -h / 2 + m, w - 2 * m
    ph = pw
    c.save()
    c.rectangle(px0, py0, pw, ph)
    c.clip()
    core.vgradient(c, "#6a3d8f", "#ff9e7a", px0, py0, pw, ph * 0.75)
    c.rectangle(px0, py0 + ph * 0.75, pw, ph)
    core.fill(c, "#ff9e7a")
    # house fronts with lit windows
    houses = [(-0.02, 0.50, 0.24, "#f2b5c4"), (0.21, 0.44, 0.22, "#a9d8c9"),
              (0.43, 0.52, 0.20, "#f6d38a"), (0.62, 0.46, 0.22, "#b6b4e8"),
              (0.83, 0.53, 0.2, "#f2b5c4")]
    for (hx, hy, hw, col) in houses:
        x0, y0, ww = px0 + pw * hx, py0 + ph * hy, pw * hw
        c.rectangle(x0, y0, ww, ph)
        _fs(c, col, INK, 2)
        poly(c, [(x0 - 4, y0), (x0 + ww / 2, y0 - ww * 0.4), (x0 + ww + 4, y0)])
        _fs(c, "#8a4a5a", INK, 2)
        c.rectangle(x0 + ww * 0.3, y0 + 10, ww * 0.4, 13)
        _fs(c, "#ffe9a0", INK, 1.5)
    # string lights
    for (y0, sag, n, ph0) in ((py0 + 16, 26, 9, 0), (py0 + 44, 20, 8, 1)):
        pts = _qbez((px0 - 4, y0), (px0 + pw / 2, y0 + sag * 2), (px0 + pw + 4, y0), 16)
        core.smooth_path(c, pts)
        core.stroke(c, "#3a2440", 1.6)
        for k in range(n):
            u = (k + 0.5 + ph0 * 0.5) / (n + 0.5)
            lx = lerp(px0, px0 + pw, u)
            ly = y0 + 4 * sag * u * (1 - u) * 1.0 + 4
            circle(c, lx, ly, 4.2)
            core.fill(c, ["#ffd98a", "#ff8fb8", "#8ff0ff"][k % 3])
    # banner
    with saved(c, 0, py0 + 90, 1.0, -0.03) as cc:
        poly(cc, [(-98, -16), (98, -16), (92, 16), (-92, 16)])
        _fs(cc, "#d8283f", INK, 2.5)
        text(cc, "BLOCK PARTY!", 0, 8, 22, "white", "comic")
    # the AI lantern, top right
    with saved(c, px0 + pw * 0.83, py0 + 60, 1.0) as cc:
        ellipse(cc, 0, -24, 14, 4)
        core.stroke(cc, "ai_rim", 2.2)
        rrect(cc, -20, -16, 40, 32, 9)
        _fs(cc, "ai_body", INK, 2)
        rrect(cc, -15, -11, 30, 22, 6)
        core.fill(cc, "ai_screen")
        for sx in (-1, 1):
            cc.arc(sx * 6, -1, 4, math.pi + 0.2, 2 * math.pi - 0.2)
            core.stroke(cc, "ai_eye", 2)
        cc.arc(0, 2, 5, 0.3, math.pi - 0.3)
        core.stroke(cc, "ai_eye", 2)
    # crowd row + Malvo in the middle (everyone came)
    folks = [(-0.43, 0.83, 15, "#f1c7a0", "#9fd8c8", True), (-0.29, 0.86, 16, "#c68a5e", "#f6c2d4", False),
             (-0.16, 0.81, 15, "#8d5a3b", "#ffe08a", True), (0.17, 0.82, 15, "#f1c7a0", "#b7c4f2", True),
             (0.30, 0.86, 16, "#8d5a3b", "#c9f0a8", False), (0.43, 0.83, 15, "#c68a5e", "#ffb7a0", True)]
    for i, (fx, fy, r, sk, bd, up) in enumerate(folks):
        _townsfolk(c, fx * pw, py0 + ph * fy, r, sk, bd, arms_up=up, ph=3 * (i % 2))
    # Malvo (tiny, happy, party hat) with Hissy on his shoulder
    mx, my = 0.0, py0 + ph * 0.70
    poly(c, [(mx - 34, my + 20), (mx + 34, my + 20), (mx + 46, my + 90), (mx - 46, my + 90)])
    _fs(c, "suit", INK, 2.2)
    poly(c, [(mx - 30, my + 18), (mx - 44, my + 4), (mx - 26, my + 34)])
    poly(c, [(mx + 30, my + 18), (mx + 44, my + 4), (mx + 26, my + 34)])
    _fs(c, "cape_in", INK, 2)
    for sx in (-1, 1):                                       # arms up, cheering
        c.move_to(mx + sx * 30, my + 30)
        c.line_to(mx + sx * 50, my - 12)
    core.stroke(c, INK, 9)
    for sx in (-1, 1):
        c.move_to(mx + sx * 30, my + 30)
        c.line_to(mx + sx * 50, my - 12)
    core.stroke(c, "suit", 6)
    for sx in (-1, 1):
        circle(c, mx + sx * 51, my - 16, 6)
        _fs(c, "glove", INK, 1.6)
    circle(c, mx, my, 24)
    _fs(c, "skin", INK, 2.4)
    for sx in (-1, 1):                                       # hair tufts
        poly(c, [(mx + sx * 22, my - 8), (mx + sx * 32, my - 14), (mx + sx * 25, my + 2)])
        _fs(c, "hair", INK, 1.4)
        c.arc(mx + sx * 9, my - 2, 4.4, math.pi + 0.25, 2 * math.pi - 0.25)
        core.stroke(c, INK, 2)
    circle(c, mx + 9, my - 2, 7.5)
    core.stroke(c, "monocle", 2)
    c.move_to(mx - 10, my + 7)
    c.curve_to(mx - 4, my + 4, mx - 1, my + 6, mx, my + 7)
    c.curve_to(mx + 1, my + 6, mx + 4, my + 4, mx + 10, my + 7)
    core.stroke(c, "mustache", 2.6)
    c.arc(mx, my + 10, 7, 0.2, math.pi - 0.2)
    core.stroke(c, INK, 2)
    party_hat(c, mx + 4, my - 21, 0.17, 0.12)
    circle(c, mx - 33, my + 10, 9)                           # Hissy
    _fs(c, "snake", INK, 2)
    for sx in (-1, 1):
        c.arc(mx - 33 + sx * 3.5, my + 9, 2.4, math.pi, 2 * math.pi)
        core.stroke(c, INK, 1.4)
    # static confetti
    for i in range(16):
        cx_ = px0 + 8 + hash01(i, 71) * (pw - 16)
        cy_ = py0 + 60 + hash01(i, 72) * (ph * 0.55)
        with saved(c, cx_, cy_, 1.0, hash01(i, 73) * 3) as cc:
            cc.rectangle(-3.5, -2, 7, 4)
            core.fill(cc, ["#ff6fa8", "#ffd166", "#5ee7ff", "#3ddc84"][i % 4])
    c.restore()
    c.rectangle(px0, py0, pw, ph)
    core.stroke(c, INK, 2)
    with saved(c, 0, py0 + ph + (h / 2 - (py0 + ph)) * 0.5 + 12, 1.0, -0.03) as cc:
        text(cc, "EVERYONE CAME!", -10, 0, 38, "#2b2a4a", "comic")
        # little doodle heart
        hx, hy = 112, -12
        cc.move_to(hx, hy + 9)
        cc.curve_to(hx - 14, hy - 2, hx - 6, hy - 14, hx, hy - 5)
        cc.curve_to(hx + 6, hy - 14, hx + 14, hy - 2, hx, hy + 9)
        core.fill(cc, "#e8314f")


# ===========================================================================
# shot A static world layer (cached)
# ===========================================================================
def _stones(c, x0, y0, x1, y1):
    rh = 112.0
    row = 0
    yy = y0
    while yy < y1:
        x = x0 - hash01(row, 11) * 140
        i = 0
        while x < x1:
            bw = 170 + hash01(row * 31 + i, 12) * 130
            bx, by = x + 5, yy + 5
            h_ = min(rh - 10, y1 - by - 4)
            if h_ > 12:
                rrect(c, bx, by, bw - 10, h_, 12)
                core.fill(c, "lair_stone")
                rrect(c, bx + 5, by + 6, bw - 15, h_ - 8, 10)
                core.fill(c, "lair_bg2")
                k = hash01(row * 57 + i, 13)
                if k < 0.16 and h_ > 60:
                    cx_, cy_ = bx + bw * (0.3 + 0.4 * hash01(i, row)), by + 14
                    c.move_to(cx_, cy_)
                    c.line_to(cx_ + 10, cy_ + 22)
                    c.line_to(cx_ + 2, cy_ + 38)
                    c.line_to(cx_ + 14, cy_ + 56)
                    core.stroke(c, "lair_bg", 4)
            x += bw
            i += 1
        yy += rh
        row += 1


def _paper(c, x, y, w, h, rot, col, draw=None):
    with saved(c, x, y, 1.0, rot) as cc:
        rrect(cc, -w / 2 + 6, -h / 2 + 8, w, h, 3)
        core.fill(cc, (0, 0, 0, 0.3))
        rrect(cc, -w / 2, -h / 2, w, h, 3)
        _fs(cc, col, INK, 3.5)
        if draw:
            draw(cc, w, h)


def _pin_pos(cx, cy, w, h, rot, fx=0.5, fy=0.06):
    lx, ly = (fx - 0.5) * w, (fy - 0.5) * h
    dx, dy = _rot(lx, ly, rot)
    return cx + dx, cy + dy


OLD_PIN = _pin_pos(*OLD, fy=0.05)
POL_PIN = _pin_pos(*POL, fy=0.045)
STEP_P = (170.0, 935.0, 150.0, 190.0, 0.07)
PLANB_P = (885.0, 975.0, 150.0, 132.0, -0.06)
STEP_PIN = _pin_pos(*STEP_P, fy=0.07)
PLANB_PIN = _pin_pos(*PLANB_P, fy=0.1)


def _world_static(c):
    x0, y0, ww, hh = WORLD_RECT
    core.bg(c, "lair_bg")
    _stones(c, x0 - 40, y0 - 40, x0 + ww + 40, FLOOR_Y)
    # floor
    c.rectangle(x0, FLOOR_Y, ww, y0 + hh - FLOOR_Y)
    core.fill(c, "lair_stone_dk")
    c.rectangle(x0, FLOOR_Y - 4, ww, 26)
    core.fill(c, "#1a0d2b")
    c.move_to(x0, FLOOR_Y - 4)
    c.line_to(x0 + ww, FLOOR_Y - 4)
    core.stroke(c, INK, 5)
    for yy in (FLOOR_Y + 80, FLOOR_Y + 190, FLOOR_Y + 330, FLOOR_Y + 520):
        c.move_to(x0, yy)
        c.line_to(x0 + ww, yy)
    core.stroke(c, "#2f1a4a", 4)
    vx, vy = -60.0, FLOOR_Y - 600
    for i in range(-6, 7):
        bx = vx + i * 300
        c.move_to(vx + (bx - vx) * 0.25, FLOOR_Y + 22)
        c.line_to(vx + (bx - vx) * 1.6, FLOOR_Y + 900)
    core.stroke(c, "#2f1a4a", 4)

    # corkboard + frame
    bx0, by0, bx1, by1 = BOARD
    rrect(c, bx0 + 14, by0 + 16, bx1 - bx0, by1 - by0, 14)
    core.fill(c, (0, 0, 0, 0.35))
    rrect(c, bx0, by0, bx1 - bx0, by1 - by0, 14)
    _fs(c, FRAME, INK, 6)
    c.move_to(bx0 + 12, by0 + 11)
    c.line_to(bx1 - 12, by0 + 11)
    core.stroke(c, FRAME_HI, 6)
    c.move_to(bx0 + 12, by1 - 10)
    c.line_to(bx1 - 12, by1 - 10)
    core.stroke(c, FRAME_DK, 6)
    rrect(c, bx0 + 30, by0 + 30, bx1 - bx0 - 60, by1 - by0 - 60, 5)
    _fs(c, CORK, INK, 4)
    for i in range(150):                                # cork speckles
        sx = bx0 + 40 + hash01(i, 151) * (bx1 - bx0 - 80)
        sy = by0 + 40 + hash01(i, 152) * (by1 - by0 - 80)
        circle(c, sx, sy, 1.8 + 2.6 * hash01(i, 153))
        core.fill(c, CORK_DK if i % 3 else CORK_HI)
    # old pin holes
    for i in range(10):
        sx = bx0 + 60 + hash01(i, 161) * (bx1 - bx0 - 120)
        sy = by0 + 60 + hash01(i, 162) * (by1 - by0 - 120)
        circle(c, sx, sy, 2.4)
        core.fill(c, "#6e4a24")

    # header strip: "EVIL PLANS" with s12's yellow "PARTY" sticky over EVIL
    with saved(c, HEADER[0], HEADER[1], 1.0, -0.025) as cc:
        rrect(cc, -200 + 6, -46 + 8, 400, 92, 4)
        core.fill(cc, (0, 0, 0, 0.3))
        rrect(cc, -200, -46, 400, 92, 4)
        _fs(cc, PAPER, INK, 4)
        tw = text_width(cc, "EVIL PLANS", "title", 62)
        text(cc, "EVIL PLANS", 0, 23, 62, "danger", "title")
        ex = -tw / 2 + text_width(cc, "EVIL", "title", 62) / 2
        with saved(cc, ex - 2, -2, 1.0, -0.08) as c2:
            c2.rectangle(-84 + 5, -50 + 7, 168, 100)
            core.fill(c2, (0, 0, 0, 0.3))
            c2.rectangle(-84, -50, 168, 100)
            _fs(c2, "#ffe066", INK, 3.5)
            c2.rectangle(-84, -50, 168, 18)
            core.fill(c2, "#f2cf3a")
            c2.rectangle(-84, -50, 168, 100)
            core.stroke(c2, INK, 3.5)
            text(c2, "PARTY", 0, 22, 56, "ink", "comic")
    for px in (-186, 186):
        _pin(c, HEADER[0] + px, HEADER[1] - 30 + px * 0.025, "#3a3a4a", 0.8)

    # lower papers (callbacks to the lair board)
    def lined(cc, pw, ph):
        for k in range(8):
            yy = -ph / 2 + 34 + k * 19
            cc.move_to(-pw / 2 + 8, yy)
            cc.line_to(pw / 2 - 8, yy)
        core.stroke(cc, "#7aa7e0", 1.6)
        for k in range(4):
            yy = -ph / 2 + 31 + k * 19
            ww_ = 60 + 40 * hash01(k, 61)
            cc.move_to(-pw / 2 + 14, yy)
            for j in range(6):
                cc.line_to(-pw / 2 + 14 + ww_ * (j + 1) / 6, yy + (3 if j % 2 else -3))
        core.stroke(cc, INK, 2.2)
        text(cc, "STEP 3:", -pw / 2 + 12, ph / 2 - 52, 22, "ink", "round", "left")
        text(cc, "???", 0, ph / 2 - 16, 36, "danger", "comic")

    def sticky(cc, pw, ph):
        cc.rectangle(-pw / 2, -ph / 2, pw, 18)
        core.fill(cc, "#f2cf3a")
        text(cc, "PLAN B", 0, 10, 36, "ink", "comic")
        cc.move_to(-44, 30)
        cc.curve_to(-18, 22, 14, 36, 44, 26)
        core.stroke(cc, "ink", 3)

    _paper(c, *STEP_P, "#f4f1e8", lined)
    _paper(c, *PLANB_P, "#ffe066", sticky)

    # the old science-fair photo
    cx, cy, w, h, rot = OLD
    with saved(c, cx, cy, 1.0, rot) as cc:
        science_photo(cc, w, h)

    # old red strings (static): old photo -> STEP 3 -> PLAN B
    _red_string(c, _string_pts(OLD_PIN, STEP_PIN, 30))
    _red_string(c, _string_pts(STEP_PIN, PLANB_PIN, 60))
    for (px, py, col) in ((STEP_PIN[0], STEP_PIN[1], "safe"),
                          (PLANB_PIN[0], PLANB_PIN[1], "ai_rim"),
                          (OLD_PIN[0], OLD_PIN[1], "ai_rim")):
        _pin(c, px, py, col)


# ===========================================================================
# shot A: corkboard -> cutout
# ===========================================================================
def _cam(t, T):
    k = ease_in_out(seg(t, T["slide0"], T["slide1"]))
    cx = lerp(CAM_C0[0], CAM_C1[0], k)
    cy = lerp(CAM_C0[1], CAM_C1[1], k)
    z = lerp(CAM_Z0, CAM_Z1, k)
    # (no idle push-ins: a constantly scaling textured frame costs bitrate;
    #  the slap, the string, the slide and the characters carry the motion)
    return cx, cy, z


def _draw_polaroid(c, t, T):
    cx, cy, w, h, rot = POL
    if t < T["pol"]:
        return
    # flight: from up-right, big and twisted, accelerating into the slap
    u = seg(t, T["pol"] - 0.04, T["slap"])
    f = ease_in(u)
    x = lerp(cx + 170, cx, f)
    y = lerp(cy - 240, cy, f)
    s = lerp(1.55, 1.0, f)
    r = lerp(0.42, rot, f)
    sx = sy = 1.0
    if t >= T["slap"]:
        q = seg(t, T["slap"], T["slap"] + 0.34)
        wv = math.sin(q * math.pi * 2.5) * (1 - q) ** 1.5
        sx, sy = 1 + 0.08 * wv, 1 - 0.08 * wv
        r = rot - 0.03 * wv
    lift = (1 - f) * 34                                  # shadow grows while airborne
    with saved(c, x + lift * 0.6, y + lift, s * 1.0, r) as cc:
        rrect(cc, -w / 2 + 6, -h / 2 + 9, w, h, 5)
        core.fill(cc, (0, 0, 0, 0.32 - 0.12 * (1 - f)))
    with saved(c, x, y, (s * sx, s * sy), r) as cc:
        party_photo(cc, w, h)
    # impact ticks
    if T["slap"] <= t < T["slap"] + 0.26:
        q = seg(t, T["slap"], T["slap"] + 0.26)
        for k in range(8):
            a = k * math.pi / 4 + 0.39
            r0 = 200 + 60 * ease_out(q)
            r1 = r0 + 44 * (1 - q)
            c.move_to(cx + math.cos(a) * r0 * 0.8, cy + math.sin(a) * r0)
            c.line_to(cx + math.cos(a) * r1 * 0.8, cy + math.sin(a) * r1)
        core.stroke(c, (1, 0.97, 0.88, 1 - q), 7)
    # red pin pokes in
    if t >= T["pin"]:
        k = ease_out_back(seg(t, T["pin"], T["pin"] + 0.22), 2.6)
        dy = (1 - smoothstep(seg(t, T["pin"], T["pin"] + 0.12))) * -26
        with saved(c, POL_PIN[0], POL_PIN[1] + dy, max(0.01, k)) as cc:
            _pin(cc, 0, 0, "danger", 1.15)


def _draw_new_string(c, t, T):
    if t < T["str0"]:
        return
    p = ease_in_out(seg(t, T["str0"], T["str1"]))
    pts = _string_pts(OLD_PIN, POL_PIN, 40)
    tip = pts[-1]
    _red_string(c, pts, p)
    if p < 1:
        tip = _partial(c, pts, p)
        c.new_path()
        circle(c, tip[0], tip[1], 5)
        core.fill(c, STRING)
    # re-pin both ends on top of the string
    _pin(c, OLD_PIN[0], OLD_PIN[1], "ai_rim")
    if t >= T["pin"] + 0.2:
        _pin(c, POL_PIN[0], POL_PIN[1], "danger", 1.15)


def _ai_a_state(t, T):
    """AI beside the cutout: expr, look, hands, blink."""
    ai_in, reach, fix0, fix1 = T["ai_in"], T["reach"], T["fix0"], T["fix1"]
    good, let_go, sb = T["good"], T["let_go"], T["sblink"]
    expr = keyed(t, [(-9, "happy"), (ai_in + 0.2, AIX["half"], 0.25),
                     (reach - 0.06, "warm", 0.25), (fix1, "happy", 0.2),
                     (good + 0.05, "warm", 0.3)])
    look = keyed_v(t, [(-9, (0.15, 0.05)), (ai_in + 0.2, (-0.85, 0.25), 0.12),
                       (reach - 0.05, (-0.9, -0.3), 0.15), (good, (0.0, 0.0), 0.15)])
    hands = keyed(t, [(-9, "idle"), (reach - 0.12, "present_l", 0.26),
                      (let_go, "idle", 0.35)])
    bl = None
    if t >= sb - 0.01:
        bl = max(blink_amount(t, 2), slow_blink(t, sb, 0.14, 0.1, 0.16))
    return expr, look, hands, bl


def _hat_state(t, T):
    """Cutout party hat: crooked -> straightened by the AI (spring)."""
    q0 = seg(t, T["fix0"], T["fix1"])
    k = ease_in_out(q0)
    off = (95.0, -178.0, 0.75)                          # crooked: slid right, tipped
    on = (4.0, -196.0, -0.04)
    x = lerp(off[0], on[0], k)
    y = lerp(off[1], on[1], k) - math.sin(k * math.pi) * 22
    r = lerp(off[2], on[2], k)
    if t > T["fix1"]:
        q = seg(t, T["fix1"], T["fix1"] + 0.6)
        r += math.sin(q * math.pi * 3) * (1 - q) ** 1.6 * 0.12
    elif t < T["fix0"]:
        r += math.sin(t * 2 * math.pi * 0.7) * 0.02         # droops a little
    return x, y, r


def _shot_a(ctx, t, info, T):
    cx, cy, z = _cam(t, T)
    ctx.save()
    ctx.translate(*CAM_S)
    ctx.scale(z, z)
    ctx.translate(-cx, -cy)
    P._cached_layer(ctx, "s13_world", _world_static, rect=WORLD_RECT, opaque=True)
    _draw_new_string(ctx, t, T)
    _draw_polaroid(ctx, t, T)
    if t >= T["slide0"] - 0.05:
        _draw_cutout_group(ctx, t, info, T)
    ctx.restore()
    # one ominous frame: the room drops to dark red, the visor sears
    on = _visor_on(t, T)
    if on > 0:
        P.flash(ctx, 0.62 * on, "#16000a")
        with saved(ctx, 0, 0, 1.0) as c:
            c.translate(*CAM_S)
            c.scale(z, z)
            c.translate(-cx, -cy)
            _cutout_xf(c, t, T)
            _visor_overlay(c, on)


def _cutout_xf(c, t, T):
    """Apply the cutout's local transform (head-centre origin, s = 1 units)."""
    hx, hy, s, lean = CUT
    q = seg(t, T["bad"], T["bad"] + 0.9)
    rock = math.sin(q * math.pi * 3) * (1 - q) ** 1.4 * 0.025 if t >= T["bad"] else 0.0
    c.translate(hx, hy + 970 * s)
    c.rotate(lean + rock)
    c.translate(0, -970 * s)
    c.scale(s, s)
    return rock


def _visor_overlay(c, on):
    """The ominous visor, drawn OVER the darkened frame (searing red)."""
    vx, vy = 0.0, -30.0
    radial_glow(c, vx, vy, 420, "#ff1f3d", 0.6 * on)
    for k in range(12):                                   # light spill rays
        a = k * math.pi / 6 + 0.26
        ca, sa = math.cos(a), math.sin(a)
        c.move_to(vx + ca * 185, vy + sa * 52)
        c.line_to(vx + ca * (185 + 190 * on), vy + sa * (52 + 70 * on))
    core.stroke(c, core.alpha("#ff5a72", 0.85 * on), 10)
    _capsule(c, vx, vy, 344, 106)
    _fs(c, BEZEL, INK, 5)
    _capsule(c, vx, vy, 300, 70)
    core.fill(c, "#ff4d66")
    _capsule(c, vx, vy, 260, 34)
    core.fill(c, core.alpha("#ffd0d8", on))
    c.move_to(vx - 118, vy)
    c.line_to(vx + 118, vy)
    core.stroke(c, "white", 10)
    circle(c, vx, vy, 30)
    core.fill(c, "white")
    circle(c, vx, vy, 30)
    core.stroke(c, "#ff3b5c", 7)
    _capsule(c, vx, vy, 300, 70)
    core.stroke(c, INK, 4)
    for sx in (-1, 1):                                    # antenna lights
        circle(c, sx * 128, -250, 26)
        core.fill(c, core.alpha("#ff1f3d", 0.45 * on))
        circle(c, sx * 128, -250, 10)
        core.fill(c, "#ff8a9c")


def _visor_on(t, T):
    df = round((t - T["bad"]) * core.FPS)
    return 1.0 if df == 0 else 0.35 if df == 1 else 0.0


def _draw_cutout_group(ctx, t, info, T):
    hx, hy, s, lean = CUT
    # after the visor blink the cardboard rocks a hair (see _cutout_xf)
    q = seg(t, T["bad"], T["bad"] + 0.9)
    rock = math.sin(q * math.pi * 3) * (1 - q) ** 1.4 * 0.025 if t >= T["bad"] else 0.0
    base = (hx, hy + 970 * s)
    on = _visor_on(t, T)
    if t >= T["ai_in"]:                                  # the AI's cyan light on the wall
        ga = 0.16 * smoothstep(seg(t, T["ai_in"], T["ai_in"] + 0.4))
        radial_glow(ctx, AIA[0] - 20, AIA[1] + 60, 470, "ai_rim", ga)
    # balloon (behind the cutout), tied to the screen-left shoulder plate
    bt = t
    bx = BALLOON[0] + math.sin(bt * 2 * math.pi * 0.37) * 7
    by = BALLOON[1] + math.sin(bt * 2 * math.pi * 0.5 + 1.0) * 9
    brot = math.sin(bt * 2 * math.pi * 0.37 + 0.6) * 0.07 - 0.08
    knot = _rot(-292 * s, (330 - 970) * s, lean + rock)
    balloon(ctx, bx, by, 1.0, brot, (base[0] + knot[0], base[1] + knot[1]))
    with saved(ctx, 0, 0, 1.0) as c:
        _cutout_xf(c, t, T)
        draw_cutout(c, on)
        hxp, hyp, hr = _hat_state(t, T)
        party_hat(c, hxp, hyp, 1.0, hr)
    # the AI pops in beside it
    if t >= T["ai_in"]:
        k, sx, sy = _pop_squash(t, T["ai_in"], 0.55)
        expr, look, hands, bl = _ai_a_state(t, T)
        ax, ay, s_ai = AIA
        push = math.sin(math.pi * seg(t, T["fix0"] - 0.08, T["fix1"] + 0.15)) * 26
        ax -= push
        ay += push * 0.3
        with saved(ctx, ax, ay, (max(0.01, k * sx), max(0.01, k * sy))) as c:
            draw_ai(c, 0, 0, s_ai, t, expr=expr, look=look, mouth=info.mouth("ai", t),
                    hands=hands, blink=bl, aura=0.55, glow=1.0)
        # pop sparkle ring
        u = seg(t, T["ai_in"], T["ai_in"] + 0.5)
        if u < 1:
            circle(ctx, ax, ay, 90 + 160 * ease_out(u))
            core.stroke(ctx, core.alpha("ai_rim", 0.8 * (1 - u)), 8 * (1 - u) + 1)
        if t < T["ai_in"] + 0.6:                         # sparkles burst around, off the face
            u = seg(t, T["ai_in"], T["ai_in"] + 0.6)
            for i in range(6):
                a = i * math.pi / 3 + 0.4
                rr = 150 + 120 * ease_out(u)
                P._star4(ctx, ax + math.cos(a) * rr, ay + math.sin(a) * rr * 0.85,
                         (22 - 6 * (i % 2)) * (1 - u), u * 3)
                core.fill(ctx, "white" if i % 2 else "ai_accent")
    # ting! when the hat is straight
    if T["fix1"] - 0.05 <= t < T["fix1"] + 0.7:
        hxp, hyp, _ = _hat_state(T["fix1"] + 0.6, T)
        wx, wy = _rot(hxp * s, (hyp - 120) * s - 970 * s, lean)
        P.sparkles(ctx, base[0] + wx, base[1] + wy, 70, t, n=4, seed=21,
                   color="white", size=0.8)


# ===========================================================================
# shot B: title card
# ===========================================================================
def _burst(c, t, T):
    if t < T["title"]:
        return
    with saved(c, BURST_C[0], BURST_C[1], 1.0) as cc:            # static (bitrate)
        for j in range(16):
            a0 = j * 2 * math.pi / 16
            poly(cc, [(0, 0), (math.cos(a0) * 1300, math.sin(a0) * 1300),
                      (math.cos(a0 + 0.2) * 1300, math.sin(a0 + 0.2) * 1300)])
        core.fill(cc, core.alpha("ai_rim", 0.09))


def _tagline(c, t, t_in, txt, y, col):
    if t < t_in:
        return
    q = ease_out(seg(t, t_in, t_in + 0.35))
    a = clamp(q * 1.4)
    ink = core.hexc(INK)
    cc = core.hexc(col)
    text(c, txt, TX, y + (1 - q) * 34, 54, (cc[0], cc[1], cc[2], a), "round",
         outline=(ink[0], ink[1], ink[2], a), outline_w=10,
         shadow=(0, 5, (0, 0, 0, 0.4 * a)))


def _heart(c, x, y, r):
    c.move_to(x, y + r * 0.9)
    c.curve_to(x - r * 1.5, y - r * 0.1, x - r * 0.7, y - r * 1.3, x, y - r * 0.45)
    c.curve_to(x + r * 0.7, y - r * 1.3, x + r * 1.5, y - r * 0.1, x, y + r * 0.9)
    c.close_path()


def _window_heart(c, t, tb, T, win_rect):
    if t < T["heart"] or win_rect is None:
        return
    X, Y, WW, WH = win_rect
    k = ease_out_back(seg(t, T["heart"], T["heart"] + 0.35), 2.2)
    beat = 1 + 0.06 * max(0.0, math.sin(tb * 2 * math.pi * 1.1)) ** 4
    with saved(c, X + WW / 2, Y + WH * 0.56, k * beat) as cc:
        _heart(cc, 0, 0, 30)
        _fs(cc, "#ff4f6d", INK, 5)
        ellipse(cc, -14, -16, 7, 4.5, -0.6)
        core.fill(cc, (1, 1, 1, 0.8))


def _stage(c):
    """Static foreground lip that hides Malvo's cut-off waist (UI zone)."""
    rrect(c, -40, STAGE_Y, W + 80, H - STAGE_Y + 60, 40)
    core.fill(c, "#0a1226")
    c.move_to(30, STAGE_Y + 2)
    c.line_to(W - 30, STAGE_Y + 2)
    core.stroke(c, core.alpha("ai_rim", 0.55), 5)


def _hissy_head_xf(c, x, y, s, t, expr):
    """Replicates draw_snake_head's head motion (for the party hat)."""
    p = SN.resolve_expr(expr)
    seed = 5
    nod = p["nod"]
    nod_phase = math.sin(t * 2 * math.pi * 1.6)
    nod_dy = nod * (max(0.0, nod_phase) * 16 - 3)
    nod_rot = nod * 0.09 * max(0.0, nod_phase)
    bob = math.sin(t * 2 * math.pi * 0.45 + seed) * 2.5
    sway = noise1(t * 0.6, seed + 3) * 0.035
    wob = p["wob"] * math.sin(t * 2 * math.pi * 7) * 0.02
    c.translate(x, y)
    c.scale(s, s)
    c.translate(0, p["hy"] + bob + nod_dy)
    c.rotate(p["tilt"] + sway + nod_rot + wob)


def _draw_hissy(ctx, t, tb, T):
    if t < T["his_in"]:
        return
    u = seg(t, T["his_in"], T["his_in"] + 0.42)
    k = ease_out_back(u, 1.8)
    hx = lerp(-160, HIS[0], k)
    hy = HIS[1] + (1 - smoothstep(u)) * 30
    s = HIS[2]
    nice, my = T["nice"], T["my"]
    expr = keyed(t, [(-9, "happy"), (nice + 0.05, "side_eye", 0.2), (my, "nod", 0.15),
                     (T["unwink"], "happy", 0.3)])
    look = keyed_v(t, [(-9, (0.6, -0.4)), (nice + 0.05, (1.0, 0.0), 0.15),
                       (my, (0.6, 0.2), 0.2)])
    tongue = None
    if nice + 0.45 <= t < nice + 0.7:                   # side-eye ends in a tongue flick
        tongue = True
    bl = blink_amount(t, 5, rate=0.22) if t >= T["fz0"] else None
    # body from off-screen left
    body = [(hx - 330, hy + 175), (hx - 200, hy + 150), (hx - 90, hy + 120), (hx - 22, hy + 70),
            (hx, hy + 20)]
    with saved(ctx, 0, 0, 1.0) as c:
        c.translate(hx, hy)
        c.scale(s, s)
        c.translate(-hx, -hy)
        Pts = SN.coil_points([(hx + (px - hx) / s, hy + (py - hy) / s) for px, py in body], 6)
        SN.draw_tube(c, Pts, [52] * len(Pts), 0, len(Pts) - 1, cap0=False, cap1=False,
                     belly_side=-1, spot_phase=10)
    if t >= T["fz0"] or (T["nice"] - 1.0 < t < T["nice"] + 0.45):
        tongue = False
    SN.draw_snake_head(ctx, hx, hy, s, tb, expr=expr, look=look, tongue=tongue,
                       blink=bl, neck=False)
    # tiny party hat riding on his head
    with saved(ctx, 0, 0, 1.0) as c:
        _hissy_head_xf(c, hx, hy, s, tb, expr)
        party_hat(c, 24, -56, 0.48, 0.28)


def _vstate(t, expr, arms, mouth, seed=1):
    """Replicates the villain rig's torso motion so the lapel star rides on it."""
    p = V.resolve_expr(expr)
    _a, _b, a_shy, a_hdy, a_tilt = V.resolve_arms(arms, t)
    breath = math.sin(t * 2 * math.pi / 3.6 + seed * 1.3)
    shy = p["shy"] + a_shy - breath * 2.5
    return shy


def _malvo_state(t, tb, T):
    nice, my, guy, unwink = T["nice"], T["my"], T["guy"], T["unwink"]
    expr = keyed(t, [(-9, "excited"), (nice + 0.12, "sheepish", 0.22),
                     (my + 0.05, "happy", 0.3)])
    look = keyed_v(t, [(-9, (-0.3, -0.5)), (min(T["mal_in"] + 0.35, nice - 0.2), (0.0, 0.0), 0.2),
                       (nice + 0.05, (-0.95, -0.3), 0.14), (my + 0.1, (-0.3, -0.1), 0.2),
                       (guy + 0.15, (0.0, 0.0), 0.2)])
    # ta-da (present) -> [waves at camera, if there's room] -> caught on
    # "Nice try" (arm drops, sheepish) -> waves goodbye again from the hold on.
    # The wave is ONE live pose (wave_a<->wave_b blended by the oscillator,
    # re-registered every frame) so every transition into / out of it is a
    # plain 2-pose blend and never pops.
    w0 = T["mal_in"] + 0.55
    drop0 = nice + 0.1
    wave_ok = w0 + 0.3 <= drop0                        # room to wave before "Nice try"?
    osc = 0.5 + 0.5 * math.sin((tb - w0) * 2 * math.pi * 1.7 - math.pi / 2)
    amp = 1.0 - smoothstep(seg(t, T["fz0"] - 0.5, T["fz0"]))
    wv = osc * amp + 0.5 * (1 - amp)
    V.ARM_POSES["s13_wave"] = V._pose(V._blend_arm(_WAVE_A, _WAVE_B, wv), V._REST_B)
    if t < drop0:
        if wave_ok and t >= w0:
            arms = ("present", "s13_wave", smoothstep(seg(t, w0, w0 + 0.3)))
        else:
            arms = "present"
    elif t < unwink:
        arms = ("s13_wave" if wave_ok else "present", "rest",
                smoothstep(seg(t, drop0, drop0 + 0.3)))
    else:
        arms = ("rest", "s13_wave", smoothstep(seg(t, unwink, unwink + 0.35)))
    bl = None
    if t >= my + 0.05:                                   # REAL SMILE: relaxed lids
        # QA: 0.3 on top of "happy"'s own lids read as a sly half-lidded smirk
        # at this size; a lighter relax keeps the final smile genuine.
        bl = max(0.12 * smoothstep(seg(t, my + 0.05, my + 0.35)),
                 _tail_blink(t, 1, 0.24, T["end"]))
    elif t >= T["fz0"]:
        bl = _tail_blink(t, 1, 0.24, T["end"])
    return expr, look, arms, bl


def _tail_blink(t, seed, rate, end, guard=0.3):
    """blink_amount, but no blink may START in the last `guard` s, so the
    film's final (thumbnail) frame never lands mid-blink."""
    if t >= end - guard and blink_amount(end - guard, seed, rate=rate) < 0.01:
        return 0.0
    return blink_amount(t, seed, rate=rate)


def _draw_malvo(ctx, t, tb, T):
    if t < T["mal_in"]:
        return
    u = seg(t, T["mal_in"], T["mal_in"] + 0.45)
    y = MAL[1] + (1 - ease_out_back(u, 1.6)) * 520
    x, s = MAL[0], MAL[2]
    expr, look, arms, bl = _malvo_state(t, tb, T)
    draw_villain(ctx, x, y, s, tb, expr=expr, look=look, mouth=(0, 0), arms=arms, blink=bl)
    shy = _vstate(tb, expr, arms, (0, 0))
    lx, ly = x + 100 * s, y + (-318 + shy * 0.5) * s
    _gold_star(ctx, lx, ly, 40 * s, 0.0, 5.0 * s * 1.3)


def _ai_b_state(t, T):
    nice, my, guy, unwink = T["nice"], T["my"], T["guy"], T["unwink"]
    expr = keyed(t, [(-9, "happy"), (T["win_open"] + 0.2, "warm", 0.3),
                     (nice - 0.05, "amused", 0.2), (my, "happy", 0.18),
                     (guy, "wink", 0.08), (unwink, "happy", 0.25)])
    look = keyed_v(t, [(-9, (0.05, -0.9)), (T["win_open"], (-0.1, -1.0), 0.3),
                       (nice - 0.05, (0.95, 0.35), 0.14), (my - 0.02, (0.0, 0.0), 0.12)])
    hands = keyed(t, [(-9, "idle"), (nice, "present", 0.25), (my, "thumbs_up", 0.22),
                      (unwink + 0.15, "wave", 0.3)])
    bl = blink_amount(t, 2) if t >= T["fz0"] else None
    return expr, look, hands, bl


def _draw_ai_b(ctx, t, tb, info, T):
    if t < T["ai2_in"]:
        return
    k, sx, sy = _pop_squash(t, T["ai2_in"], 0.5)
    expr, look, hands, bl = _ai_b_state(t, T)
    x, y, s = AIB
    with saved(ctx, x, y, (max(0.01, k * sx), max(0.01, k * sy))) as c:
        out = draw_ai(c, 0, 0, s, tb, expr=expr, look=look, mouth=info.mouth("ai", t),
                      hands=hands, blink=bl, aura=0.7)
    # WINK sparkle by the closed (screen-left) eye
    if t >= T["guy"]:
        ex, ey = out["eyeL"]
        P.emote(ctx, "sparkle", x + (ex - 52 * s) * k, y + (ey - 40 * s) * k, 0.6,
                min(tb, T["fz1"]), T["guy"], t_out=T["unwink"] + 0.1)


def _shot_b(ctx, t, info, T):
    tb = _tw(t, T)
    P.ai_bg(ctx, tb, motes=6)
    _burst(ctx, t, T)
    with saved(ctx, TX - W / 2, 0, 1.0) as c:
        P.title_card(c, t, T["t1_in"], "NICE TRY,", y=T1_Y, size=T_SIZE, color="white")
        P.title_card(c, t, T["t2_in"], "MY GUY.", y=T2_Y, size=T_SIZE, color="ai_accent")
    _tagline(ctx, t, T["tag1"], "A wall for harm.", TAG1_Y, BRICK_RED)
    _tagline(ctx, t, T["tag2"], "A door for everything else.", TAG2_Y, "ai_accent")
    wx, wy, ww, wh = WALL
    # drop=260: the bricks start below "MY GUY." instead of falling through it
    res = P.brick_wall(ctx, wx, wy, ww, wh, t, T["wall0"], rows=4, speed=2.0, drop=260,
                       window={"rect": WIN, "t_open": T["win_open"], "fill": "#ffe9b0",
                               "awning": True, "sign": "OPEN"})
    _window_heart(ctx, t, tb, T, res["window"] if t >= T["win_open"] else None)
    _draw_hissy(ctx, t, tb, T)
    _draw_ai_b(ctx, t, tb, info, T)
    _draw_malvo(ctx, t, tb, T)
    _stage(ctx)


# ===========================================================================
# entry points
# ===========================================================================
def render(ctx, t, info):
    T = _T(info)
    if t < T["title"]:
        _shot_a(ctx, t, info, T)
    else:
        _shot_b(ctx, t, info, T)


def caption_y(t, info):
    T = _T(info)
    if t >= T["title"]:
        return None              # the title card carries its own text
    return 1450


def SFX(info):
    T = _T(info)
    out = [
        (T["slap"], "stamp", -8),
        (T["pin"], "pop", -8),
        (T["slide0"] + 0.1, "whoosh", -15),
        (T["bad"] - 0.18, "glitch", -14),
        (T["ai_in"], "sparkle", -8),
        (T["fix1"] - 0.04, "pop", -12),
        (T["title"] - 0.2, "whoosh", -8),
        (T["ai2_in"], "pop", -10),
        (T["last_land"] - 0.15, "ta_da", -4),        # the fanfare's "DA" = last letter
        (T["his_in"] + 0.1, "pop", -16),
        (T["guy"], "sparkle", -10),
    ]
    for lt in P.brick_wall_land_times(T["wall0"], 4, 2.0)[:3]:
        out.append((lt - 0.03, "brick_thud", -5))
    return out
