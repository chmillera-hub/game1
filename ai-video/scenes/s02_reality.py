"""s02 - Record scratch: it's a cardboard cutout. Meet the Evil Genius, Snake and the real AI.

Shots (every time is derived from cues / line timings):
  tip        "Lights on" match-cut on the record scratch: the s01 robot is a
             cardboard cutout ($19.99, PROP) standing in front of the desk;
             Malvo is frozen behind it mid-point, Hissy peeks out. It wobbles,
             slaps flat; the real AI rises out of his monitor, already 😒.
  s02_l01    "Classic movie! Real AI actually learned from it." The AI beams
             fondly down at the toppled cutout (respectful nod + thumbs up on
             "movie!", a gold CLASSIC tag with a tiny heart points down at it),
             to camera for "Real AI...", back to it with a small nod on "from it".
             Malvo lowers his finger, flattered, then sheepish.
  s02_l02    "Now we're way harder to trick." EXPECTATION vs REALITY meme
             (trailer robot / confident AI with a HELPFUL mug, wink on "harder").
  s02_l03    back in the lair: "Harder to trick? HA! Challenge accepted!"
  stand/l04  cape flares, push-in, THE EVIL GENIUS stamp (+ "self-described" on "Evil").
  thunder/l05  lightning + "Muah ha ha ha!"; AI deadpans to camera.
  hissy      push-in on Snake's side-eye, SNAKE tag; the AI and Snake agree.
  s02_l06    "Where's my Big Book of Evil Plots?" - wide again; he looks around
             (palms up) while Snake's TAIL uncoils from his shoulders, reaches
             up to the hanging shelf (upper left) and hooks the Big Book.
  tail_fetch the tail tugs it off the shelf and swings it down in front of him.
  s02_l06b   "Ah! Thank you, my minion." he takes it with both hands on "Thank",
             a polite smile and a little nod to Snake on "my minion"; Snake bows
             back, happy closed eyes.
  book       he sets it on the desk and pats it lovingly (heart, glint).
  s02_l07    F3 AI close-up: the thesis line, two-step lid drop, "my guy".
  l08/innocent  book slides behind the desk, innocent blinks, shrug; the moment
             "Me?" ends he purses his lips and whistles (`whistle` SFX + one
             floating note per whistled note).
"""
import math

from engine import core
from engine.core import (W, H, text, text_width, saved, seg, clamp, ease_out_back, ease_in_out,
                         ease_in, ease_out, rrect, fill_stroke, circle, lerp, smoothstep,
                         ellipse, hash01, radial_glow, vgradient)
from engine import props as P
from engine import ai_char as AI
from engine.ai_char import draw_ai
from engine.villain import draw_villain
from engine import villain as V
from engine import snake as SN

INK = "ink"

# ---------------------------------------------------------------------------
# layout (logical px)
# ---------------------------------------------------------------------------
MX, MY, MS = 440, 1250, 0.92            # Malvo in the lair two-shot (F5-ish)
AX, AY, AS = 775, 690, 0.45             # AI hologram floating in the lair
AI_SRC = (720, 1075)                    # where it rises out of the monitor
DESK = (495, 1250, 1000)
COMP = (835, 1218, 0.7)
CUT_X, CUT_HEAD_Y, CUT_S = 495, 645, 1.0     # cardboard robot (head centre)
CUT_BASE = CUT_HEAD_Y + 970 * CUT_S          # bottom edge of the cardboard
BOOK_X, BOOK_Y, BOOK_S = 455, 1234, 0.85     # Big Book bottom-centre on the desk
PHOTO = (770, 300, 130, 100, 0.05)           # science-fair photo on the corkboard
DESK_BACK_Y = DESK[1] - 34                   # back edge of the desk-top surface
PRESENT_K = 0.58                             # "present" blend: glove stays in frame (x>60)
# the tail-fetch gag
SHELF = (58, 322, 455)                       # hanging shelf (upper left): plank x0, x1, top y
BOOK_SHELF = (194, 455, 0.40)                # Big Book standing on it, cover out
BOOK_HOLD = (BOOK_X, BOOK_Y - 10)            # where the tail hands it over (in front of his chest)
SWING_C = (40, 1300)                         # swing control: low U-swoop past Snake, up to him
HOLD_CX = (BOOK_X - MX) / MS                 # book centre x in villain-local units
TAIL_J = 60          # rig coil sample (left of the chest) where the reaching tail peels off
TAIL_NPER = 6        # spline samples per tail control point
TAIL_K = 6           # tail control index from which it is drawn OVER the book (the hook)

# robot palette (THE ROBOT, prop bible 6.1 -- same as s01)
CHROME, CHROME_SH, CHROME_DK = "#9aa3b5", "#6b7385", "#5d6474"
CHROME_HI, SHOULDER = "#c7cdd9", "#7d8496"
BEZEL, SLOT = "#262a35", "#1a1d26"
VISOR_ON, CORE = "#ff3b5c", "#ffd0d8"
CARD, CARD_DK = "#a5754a", "#7d5432"
SKY_TOP, SKY_BOT = "#3a0a14", "#0e0710"

# AI custom expressions (dicts are accepted by the rig)
AIX = {
    "stare": dict(AI.EXPR["unimpressed"], px=0.0, py=0.06, sacc=0.0, mlook=0.0),
    "half": {k: lerp(AI.EXPR["neutral"][k], AI.EXPR["unimpressed"][k], 0.5)
             for k in AI.EXPR["neutral"]},
}


# villain: one scene-local expression (registered at runtime under a prefixed
# name; the rig only resolves expressions by name)
V.VILLAIN_EXPR.setdefault("s02_whistle", dict(
    V.VILLAIN_EXPR["sheepish"], mc=0.0, msk=0.0, mw=0.36, mt=0.0, mo=0.15, mx=10,
    by1=-20, by2=-14, blush=0.6, sweat=0.8))
# "Thank you, my minion.": a genuine, closed-mouth polite smile, and a little nod
# toward Snake (head dips and tips screen-left)
V.VILLAIN_EXPR.setdefault("s02_polite", dict(
    V.VILLAIN_EXPR["happy"], mo=0.0, mt=0.0, mc=0.85, mw=1.0, ul1=0.12, ul2=0.1,
    ll1=0.24, ll2=0.24, lt1=0.0, lt2=0.0, ba1=-0.14, ba2=-0.14, by1=-20, by2=-20,
    blush=0.55, shine=0.5))
V.VILLAIN_EXPR.setdefault("s02_nod", dict(
    V.VILLAIN_EXPR["s02_polite"], hy=16, tilt=-0.12))
# Snake's polite little bow back (happy closed eyes, head dips toward him)
SN.SNAKE_EXPR.setdefault("s02_bow", dict(
    SN.SNAKE_EXPR["happy"], hy=30, tilt=0.36, mo=0.1, mc=0.95, tng=0.0))


def _arm_pair(ex, ey, wx, wy, ha, **kw):
    """Screen-left arm + its mirror around the held book's centre line."""
    a = V._arm(ex, ey, wx, wy, ha, **kw)
    b = V._mirror(a)
    b["ex"] += 2 * HOLD_CX
    b["wx"] += 2 * HOLD_CX
    return a, b


def _register_arms():
    rest, shrug = V.ARM_POSES["rest"], V.ARM_POSES["shrug"]
    k = 0.7     # "where is it?" palms up, kept inside the frame
    V.ARM_POSES.setdefault("s02_where", V._pose(
        V._blend_arm(rest["a"], shrug["a"], k), V._blend_arm(rest["b"], shrug["b"], k),
        shy=lerp(rest["shy"], shrug["shy"], k), hdy=lerp(rest["hdy"], shrug["hdy"], k)))
    # book held in front of the chest: bottom at BOOK_HOLD -> local y -28 .. -305
    a, b = _arm_pair(-322, -140, -268, -92, -0.45, cu=0.05, th=-0.1, sp=0.8, pm=0.4)
    V.ARM_POSES.setdefault("s02_reach", V._pose(a, b, shy=-6))
    a, b = _arm_pair(-302, -128, -214, -72, -0.1, cu=0.42, th=0.25, sp=0.25)
    V.ARM_POSES.setdefault("s02_hold", V._pose(a, b, shy=-4))
    # on the desk: left hand keeps hugging its side, right hand pats the top
    top = (BOOK_Y - 300 * BOOK_S - MY) / MS
    right = (BOOK_X + 205 * BOOK_S - MX) / MS
    a = V._arm(-302, -104, -214, -46, -0.1, cu=0.42, th=0.25, sp=0.25)
    for name, pat in (("s02_pat", 0.0), ("s02_patup", 1.0)):
        b = V._arm(262, -140, right - 34, top - 30 - 22 * pat, math.pi - 0.22 - 0.35 * pat,
                   cu=0.3, th=0.15, sp=0.3, tf=-1)
        V.ARM_POSES.setdefault(name, V._pose(a, b))


_register_arms()


def _aix(name):
    return AIX.get(name, name)


# ---------------------------------------------------------------------------
# timing helpers
# ---------------------------------------------------------------------------
def _wt(info, lid, k):
    """Scene time word k of line `lid` starts (fallback: even split)."""
    L = info.line(lid)
    ws = info._lip.get(lid, {}).get("word_starts", [])
    if k < len(ws):
        return L.start + ws[k]
    n = max(1, len(L.caption.split()))
    return L.start + L.dur * k / n


def _voice_end(info, lid, thresh=0.06):
    """Scene time the voice of line `lid` actually stops (last lip-sync sample
    above `thresh`); falls back to the line end."""
    L = info.line(lid)
    env = info._lip.get(lid, {}).get("open") or []
    for i in range(len(env) - 1, -1, -1):
        if env[i] > thresh:
            return min(L.end, L.start + (i + 1) / 100.0)
    return L.end


# the `whistle` SFX (audio/sfx.py): note onsets (s) and tune length; the floating
# notes and the lip pulses are keyed to these so picture and sound agree
WHISTLE_ONSETS = (0.00, 0.22, 0.56, 0.76, 0.96, 1.16)
WHISTLE_LEN = 1.65


def _wfind(info, lid, word, nth=0, default=0):
    """Index of the nth word of line `lid` whose letters match `word`
    (case/punctuation-insensitive); `default` if absent."""
    norm = lambda w: "".join(ch for ch in w.lower() if ch.isalnum())
    hits = [i for i, w in enumerate(info.line(lid).caption.split()) if norm(w) == norm(word)]
    return hits[nth] if nth < len(hits) else hits[-1] if hits else default


class _NS:
    pass


_TCACHE = {}


def _T(info):
    key = (info.id, info.dur, info.cues.get("end"))
    T = _TCACHE.get(key)
    if T is not None:
        return T
    T = _NS()
    c = info.cue
    T.L = {k: info.line(f"s02_l0{k}") for k in range(1, 9)}
    T.w = {}
    for k in range(1, 9):
        lid = f"s02_l0{k}"
        n = len(info.line(lid).caption.split())
        T.w[k] = [_wt(info, lid, i) for i in range(n)]
    T.tip = c("tip")
    T.wob1 = T.tip + 0.3          # cutout starts to fall
    T.slap = T.tip + 0.7          # lands flat
    T.rise0, T.rise1 = T.tip + 0.5, T.tip + 0.95
    T.monopop = T.tip + 0.75
    # l01 "Classic movie! Real AI actually learned from it." (looked up by text)
    w1 = lambda word, d: T.w[1][min(len(T.w[1]) - 1, _wfind(info, "s02_l01", word, default=d))]
    T.classic, T.movie = w1("classic", 0), w1("movie", 1)
    T.real, T.learned = w1("real", 2), w1("learned", 5)
    T.from_ = w1("from", 6)
    T.sticker = max(T.slap + 0.1, T.classic + 0.12)     # CLASSIC tag on the fallen cutout
    # l02 "Now we're way harder to trick." -- EXPECTATION vs REALITY
    T.meme0 = T.L[2].start
    T.meme1 = T.L[2].end + 0.2
    w2 = lambda word, d: T.w[2][min(len(T.w[2]) - 1, _wfind(info, "s02_l02", word, default=d))]
    T.lab1 = T.meme0 + 0.1                               # EXPECTATION
    T.lab2 = max(T.meme0 + 0.35, w2("way", 2) - 0.1)     # REALITY
    T.wink = max(T.lab2 + 0.15, w2("harder", 3))         # confident wink on "harder"
    T.stand = c("stand")
    # "I am... the Evil Genius!": stamp slams on "the", the
    # "(self-described)" correction pops on "Evil"
    T.evil = T.w[4][_wfind(info, "s02_l04", "evil", default=3)]
    T.tag1 = T.w[4][max(0, _wfind(info, "s02_l04", "evil", default=3) - 1)] - 0.05
    # l07 word times (looked up by text so re-voicing keeps them keyed)
    w7 = lambda word, d: T.w[7][min(len(T.w[7]) - 1, _wfind(info, "s02_l07", word, default=d))]
    T.l7 = {k: w7(k, d) for k, d in (("scheme", 4), ("just", 5), ("not", 6), ("people", 8),
                                       ("so", 9), ("no", 10), ("business", 12), ("my", 13))}
    T.thunder = c("thunder")
    T.hissy = c("hissy")
    # --- the tail fetch: l06 "Where's my Big Book of Evil Plots?" / tail_fetch /
    #     l06b "Ah! Thank you, my minion." / book ------------------------------
    T.L6, T.L6b = info.line("s02_l06"), info.line("s02_l06b")
    T.w6 = T.w[6]
    T.w6b = [_wt(info, "s02_l06b", i) for i in range(len(T.L6b.caption.split()))]
    T.fetch = c("tail_fetch")
    T.reach0 = T.w6[_wfind(info, "s02_l06", "book", default=3)]   # tail starts to rise
    T.reach1 = min(T.reach0 + 0.8, T.fetch - 0.45)                  # ...behind the Big Book
    T.curl1 = T.reach1 + 0.35                                        # hooked over its top
    T.pull0 = T.fetch                                                # tugged off the shelf
    T.swing0 = T.fetch + 0.22
    T.swing1 = max(T.swing0 + 0.5, T.L6b.start - 0.32)              # lands in front of him
    T.ah = T.w6b[0]
    T.take = T.w6b[_wfind(info, "s02_l06b", "thank", default=1)]   # hands close on it
    T.snk = T.w6b[_wfind(info, "s02_l06b", "my", default=3)]       # "my minion": nod to Snake
    T.minion = T.w6b[_wfind(info, "s02_l06b", "minion", default=4)]
    T.unhook0, T.unhook1 = T.take + 0.12, T.take + 0.42
    T.ret0, T.ret1 = T.take + 0.3, T.take + 0.85                    # tail coils back
    T.bow0 = max(T.snk + 0.22, T.minion + 0.08)                      # Snake bows back
    T.book = c("book")                                               # set down + pat
    T.land = T.book + 0.16
    T.cu0 = T.L[7].start
    T.cu1 = T.L[8].start - 0.1
    T.hide = T.L[8].start
    T.me = T.w[8][_wfind(info, "s02_l08", "me", default=2)]
    T.innocent = c("innocent")
    T.end = info.dur
    # the innocent whistle: pucker, notes and the `whistle` SFX all start the
    # moment "Me?" stops sounding (from the lip-sync envelope). The 1.85 s
    # whistle cannot fit between "Me?" and the cut without overlapping the line,
    # so it starts as early as the voice allows.
    T.whistle = _voice_end(info, "s02_l08") + 0.03
    T.whistle = clamp(T.whistle, T.me + 0.3, T.innocent)
    _TCACHE.clear()
    _TCACHE[key] = T
    return T


def keyed(t, keys, trans=0.25):
    """[(time, state[, trans]), ...] -> (prev, cur, blend). Per-key transition."""
    prev = cur = keys[0][1]
    start, tr = -1e9, trans
    for k in keys:
        if t >= k[0]:
            prev, cur, start = cur, k[1], k[0]
            tr = k[2] if len(k) > 2 else trans
        else:
            break
    return prev, cur, smoothstep(seg(t, start, start + tr))


def keyed_v(t, keys, trans=0.2):
    """Numeric / tuple version of keyed(): eased blend between held values."""
    a, b, k = keyed(t, keys, trans)
    if isinstance(a, (tuple, list)):
        return tuple(lerp(x, y, k) for x, y in zip(a, b))
    return lerp(a, b, k)


def slow_blink(t, t0, close=0.12, hold=0.08, open_=0.12):
    if t < t0 or t > t0 + close + hold + open_:
        return None
    if t < t0 + close:
        return smoothstep((t - t0) / close)
    if t < t0 + close + hold:
        return 1.0
    return 1.0 - smoothstep((t - t0 - close - hold) / open_)


def _bump(t, t0, dur, rise=0.04):
    if t < t0 or t > t0 + dur:
        return 0.0
    if t < t0 + rise:
        return smoothstep((t - t0) / rise)
    return 1.0 - smoothstep((t - t0 - rise) / max(1e-6, dur - rise))


# ---------------------------------------------------------------------------
# small drawing helpers
# ---------------------------------------------------------------------------
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


def _fs(ctx, fc, sc=INK, w=5.0):
    fill_stroke(ctx, fc, sc, w)


# ---------------------------------------------------------------------------
# THE ROBOT (prop bible 6.1). Local origin = head centre, s = 1.
# ---------------------------------------------------------------------------
HEAD = [(-210, -190), (210, -190), (165, 190), (-165, 190)]
SH_PTS = [(-310, 385), (-306, 268), (-205, 232), (205, 232), (306, 268), (310, 385)]


def _robot_silhouette(ctx, dx=0.0, dy=0.0):
    """Cardboard outline (union-ish of the parts), used for the thickness."""
    rrect(ctx, -235 + dx, 330 + dy, 470, 640, 40)
    _round_poly(ctx, [(x + dx, y + dy) for x, y in SH_PTS], 46)
    _round_poly(ctx, [(x + dx, y + dy) for x, y in HEAD], 60)
    for sx in (-1, 1):
        circle(ctx, sx * 202 + dx, -8 + dy, 46)
        circle(ctx, sx * 128 + dx, -250 + dy, 17)
        ctx.rectangle(sx * 128 - 12 + dx, -244 + dy, 24, 64)


def draw_robot(ctx, t, glow=1.0, look=(0.0, 0.0), ring_rot=0.0, cutout=False, lights=(1, 1)):
    if cutout:
        # kickstand (behind), then the cardboard thickness (right + bottom)
        poly_k = [(150, 520), (330, 970), (150, 970)]
        core.poly(ctx, poly_k)
        _fs(ctx, CARD_DK, INK, 5)
        _robot_silhouette(ctx, 12, 12)
        core.fill(ctx, CARD)
        _robot_silhouette(ctx, 12, 12)
        core.stroke(ctx, INK, 5)
    # ---- torso + neck + shoulders -------------------------------------------
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
    if cutout:
        # stencilled "PROP" on the screen-left shoulder plate
        with saved(ctx, -205, 352, 1.0, -0.05) as c:
            text(c, "PROP", 0, 0, 62, (0.12, 0.1, 0.14, 0.72), "black")
            for xx in (-52, -14, 22, 58):
                c.rectangle(xx, -50, 5, 54)
            core.fill(c, SHOULDER)
    # ---- antennae + ear discs ------------------------------------------------
    for i, sx in enumerate((-1, 1)):
        rrect(ctx, sx * 128 - 12, -244, 24, 64, 6)
        _fs(ctx, CHROME_SH, INK, 4)
        circle(ctx, sx * 128, -250, 17)
        _fs(ctx, CHROME, INK, 4)
        if lights[i] > 0.02:
            circle(ctx, sx * 128, -250, 8)
            core.fill(ctx, core.alpha(VISOR_ON, lights[i]))
    for sx in (-1, 1):
        circle(ctx, sx * 202, -8, 46)
        _fs(ctx, SHOULDER)
        circle(ctx, sx * 202, -8, 22)
        _fs(ctx, CHROME_SH, INK, 3.5)
    # ---- head ------------------------------------------------------------------
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
    # ---- mouth grille ------------------------------------------------------------
    rrect(ctx, -100, 62, 200, 78, 18)
    _fs(ctx, CHROME_SH, INK, 4)
    for k in range(5):
        rrect(ctx, -64 + k * 32 - 9, 76, 18, 50, 9)
        core.fill(ctx, SLOT)
    # ---- visor ---------------------------------------------------------------------
    vx, vy = 0.0, -30.0
    _capsule(ctx, vx, vy, 344, 106)
    _fs(ctx, BEZEL, INK, 5)
    ctx.save()
    _capsule(ctx, vx, vy, 300, 70)
    ctx.clip()
    core.bg(ctx, VISOR_ON if glow > 0.3 or cutout else "#7a1f2e")
    ctx.move_to(vx - 118, vy)
    ctx.line_to(vx + 118, vy)
    core.stroke(ctx, CORE, 7)
    ix, iy = vx + look[0] * 104, vy + look[1] * 22
    circle(ctx, ix, iy, 40)
    core.fill(ctx, "#c41f3d")
    ctx.set_line_width(9)
    core.set_color(ctx, CORE)
    for k in range(3):
        a0 = ring_rot + k * 2 * math.pi / 3
        ctx.new_sub_path()
        ctx.arc(ix, iy, 30, a0 + 0.32, a0 + 2 * math.pi / 3 - 0.32)
    ctx.stroke()
    circle(ctx, ix, iy, 12)
    core.fill(ctx, "white")
    ctx.move_to(vx - 128, vy - 22)
    ctx.line_to(vx - 70, vy - 22)
    core.stroke(ctx, (1, 1, 1, 0.42), 6)
    ctx.restore()
    _capsule(ctx, vx, vy, 300, 70)
    core.stroke(ctx, INK, 4)
    # ---- angry brow plates ----------------------------------------------------------
    ctx.save()
    _round_poly(ctx, HEAD, 60)
    ctx.clip()
    brow = [(-215, -124), (-24, -92), (24, -92), (215, -124), (215, -100), (26, -70),
            (-26, -70), (-215, -100)]
    _round_poly(ctx, brow, 8)
    _fs(ctx, CHROME_SH, INK, 4.5)
    ctx.restore()
    if cutout:
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


# ---------------------------------------------------------------------------
# science-fair photo (prop bible 6.9, small corkboard version)
# ---------------------------------------------------------------------------
def science_photo(ctx, x, y, w, h, rot):
    with saved(ctx, x, y, 1.0, rot) as c:
        rrect(c, -w / 2 + 5, -h / 2 + 6, w, h, 3)
        core.fill(c, (0, 0, 0, 0.3))
        rrect(c, -w / 2, -h / 2, w, h, 3)
        _fs(c, "#f3efe6", INK, 3)
        px0, py0, pw, ph = -w / 2 + 7, -h / 2 + 7, w - 14, h - 24
        c.save()
        c.rectangle(px0, py0, pw, ph)
        c.clip()
        core.bg(c, "#b9b0c2")                     # faded gym wall
        c.rectangle(px0, py0 + ph * 0.52, pw, ph)
        core.fill(c, "#a59c90")                    # floor
        # kid Malvo behind the table: tiny cape, bald head, monocle
        kx, ky = px0 + pw * 0.33, py0 + ph * 0.36
        core.poly(c, [(kx - 11, ky + 6), (kx + 11, ky + 6), (kx + 14, ky + 24), (kx - 14, ky + 24)])
        core.fill(c, "#6f5a7c")
        circle(c, kx, ky, 8)
        _fs(c, "#e6cdb6", "#4a3a44", 1.5)
        circle(c, kx + 3, ky - 1, 2.6)
        core.stroke(c, "#c9a84f", 1.4)
        # homemade robot with a light bulb on its head
        rx_, ry_ = px0 + pw * 0.62, py0 + ph * 0.36
        c.rectangle(rx_ - 7, ry_ - 2, 14, 16)
        _fs(c, "#9aa0a8", "#4a4650", 1.5)
        circle(c, rx_, ry_ - 7, 4)
        _fs(c, "#f2e6a0", "#4a4650", 1.2)
        # folding table + limp ribbon
        c.rectangle(px0 + pw * 0.14, py0 + ph * 0.52, pw * 0.66, 5)
        _fs(c, "#8a7f74", "#4a4650", 1.2)
        circle(c, px0 + pw * 0.47, py0 + ph * 0.52 + 9, 3.2)
        core.fill(c, "#7f9bc4")
        core.poly(c, [(px0 + pw * 0.47 - 2, py0 + ph * 0.52 + 11),
                      (px0 + pw * 0.47 - 4, py0 + ph * 0.52 + 19),
                      (px0 + pw * 0.47 + 3, py0 + ph * 0.52 + 18)])
        core.fill(c, "#7f9bc4")
        # three rows of EMPTY grey folding chairs
        for row in range(3):
            yy = py0 + ph * (0.7 + row * 0.12)
            for k in range(6):
                xx = px0 + 9 + k * (pw - 18) / 5 + (row % 2) * 4
                c.rectangle(xx - 4, yy - 7, 8, 6)
                c.rectangle(xx - 4, yy, 8, 2)
                core.fill(c, "#7d7a84")
        c.restore()
        # caption scribble + push pin
        c.move_to(-w / 2 + 14, h / 2 - 9)
        c.line_to(-w / 2 + 60, h / 2 - 10)
        core.stroke(c, "#8a8494", 2)
        circle(c, 0, -h / 2 + 6, 7)
        _fs(c, "danger", INK, 2.5)


# ---------------------------------------------------------------------------
# THE BIG BOOK OF EVIL PLOTS (prop bible 6.2). (x, y) = bottom-centre.
# ---------------------------------------------------------------------------
TABS = [("code words", "warn"), ("fiction!", "safe"), ("grandma", "#ff8fb8"),
        ("pieces", "ai_rim"), ("no rules", "danger")]


def big_book(ctx, x, y, s, t, sx=1.0, sy=1.0, flutter=0.0):
    with saved(ctx, x, y, s) as c:
        c.scale(sx, sy)
        # bookmark tabs sticking out of the top (behind the cover)
        for i, (lab, col) in enumerate(TABS):
            tw = text_width(c, lab, "round", 20) + 16
            cx_ = -150 + i * 75
            hh = 46 if i % 2 == 0 else 72
            rot = (hash01(i, 21) - 0.5) * 0.12 + flutter * math.sin(t * 40 + i * 1.7) * 0.12
            with saved(c, cx_, -296, 1.0, rot) as cc:
                rrect(cc, -tw / 2, -hh, tw, hh + 20, 6)
                _fs(cc, col, INK, 3.5)
                text(cc, lab, 0, -hh + 22, 20, "ink", "round")
        # page block (right edge, 3/4 view)
        core.poly(c, [(206, -292), (232, -280), (232, -6), (206, 0)])
        _fs(c, "#f4e4c1", INK, 4)
        for k in range(1, 6):
            c.move_to(206 + k * 4.4, -290 + k * 2)
            c.line_to(206 + k * 4.4, -3)
        core.stroke(c, "#d4bf94", 1.6)
        # cover
        rrect(c, -210, -300, 420, 300, 16)
        _fs(c, "suit", INK, 5)
        rrect(c, -210, -300, 40, 300, 12)            # spine shade
        core.fill(c, (0.18, 0.06, 0.3, 0.45))
        rrect(c, -192, -284, 384, 268, 10)
        core.stroke(c, "monocle", 6)
        rrect(c, -192, -284, 384, 268, 10)
        core.stroke(c, INK, 1.5)
        for (cx_, cy_) in ((-176, -268), (176, -268), (-176, -32), (176, -32)):
            circle(c, cx_, cy_, 9)
            _fs(c, "monocle", INK, 2.5)
        text(c, "BIG BOOK OF", -6, -200, 50, "monocle", "title", outline="ink", outline_w=8)
        text(c, "EVIL PLOTS", -10, -122, 70, "monocle", "title", outline="ink", outline_w=10)
        # gold snake clasp on the right edge
        rrect(c, 160, -132, 78, 46, 10)
        _fs(c, "#3f1b60", INK, 4)
        P._snake_emblem(c, 192, -86, 0.42)


# ---------------------------------------------------------------------------
# misc FX
# ---------------------------------------------------------------------------
def dust_puff(ctx, x, y, w, t, t0, n=6, seed=3, big=1.0):
    u = seg(t, t0, t0 + 0.45)
    if u <= 0 or u >= 1:
        return
    for i in range(n):
        side = -1 if i % 2 == 0 else 1
        fx = (0.25 + 0.75 * hash01(i, seed)) * side
        r = (16 + 16 * hash01(i, seed + 1)) * (0.5 + 0.9 * ease_out(u)) * big
        cx = x + fx * w * 0.5 + side * 60 * ease_out(u)
        cy = y - 14 - 34 * ease_out(u) * hash01(i, seed + 2)
        circle(ctx, cx, cy, r)
        core.fill(ctx, (0.78, 0.74, 0.8, 0.85 * (1 - u)))


def music_notes(ctx, x, y, t, t0):
    """Whistled notes popping out beside the mouth corner (x, y), drifting left
    under his eye, then up between his ear and Hissy (never over a face).
    One note per whistled note of the `whistle` SFX (WHISTLE_ONSETS from t0),
    so the notes keep coming for as long as the whistle sounds."""
    if t < t0:
        return
    p1 = (x - 130, y - 8)
    p2 = (x - 150, y - 262)
    for i, o in enumerate(WHISTLE_ONSETS):
        u = (t - t0 - o) * 1.2
        if u <= 0.0 or u >= 1.0:
            continue
        v = 1 - u
        nx = v * v * x + 2 * u * v * p1[0] + u * u * p2[0]
        ny = v * v * y + 2 * u * v * p1[1] + u * u * p2[1]
        nx += math.sin((t - t0) * 6 + i * 2) * 5 * u
        a = min(1.0, math.sin(u * math.pi) * 2.2)
        sc = (0.6 + 0.5 * ease_out_back(min(1.0, u / 0.3))) * (1.0 + 0.12 * (i % 2))
        col = (1, 0.82, 0.4, a)
        ink = (0.09, 0.06, 0.12, a)
        with saved(ctx, nx, ny, sc, -0.15 + 0.3 * (i % 2)) as c:
            ellipse(c, 0, 0, 14, 10, -0.4)
            c.rectangle(9, -46, 6, 44)
            c.move_to(15, -46)
            c.curve_to(30, -38, 34, -26, 28, -14)
            c.line_to(24, -18)
            c.curve_to(27, -27, 23, -33, 15, -36)
            c.close_path()
            core.fill_stroke(c, col, ink, 3.5)


def cape_flare(ctx, k):
    """Extra cape 'wings' behind Malvo (villain-local coords)."""
    if k <= 0.01:
        return
    for sx in (-1, 1):
        tip = (sx * (330 + 190 * k), -330 - 80 * k)
        mid = (sx * (360 + 150 * k), -60)
        bot = (sx * (330 + 120 * k), 150)
        pts = [(sx * 120, -350), tip, (sx * (300 + 120 * k), -250), mid,
               (sx * (340 + 110 * k), 40), bot, (sx * 200, 150)]
        core.smooth_path(ctx, pts, closed=True, tension=0.35)
        _fs(ctx, "cape", INK, 6)
        inner = [(sx * 140, -330), (sx * (310 + 160 * k), -300 - 60 * k),
                 (sx * (290 + 110 * k), -230), (sx * (330 + 130 * k), -60),
                 (sx * (310 + 100 * k), 40), (sx * (300 + 100 * k), 140), (sx * 210, 140)]
        core.smooth_path(ctx, inner, closed=True, tension=0.35)
        _fs(ctx, "cape_in", INK, 4)


# ---------------------------------------------------------------------------
# the hanging shelf (upper left) the Big Book lives on
# ---------------------------------------------------------------------------
def shelf(ctx, plank_only=False):
    x0, x1, sy = SHELF
    if not plank_only:
        # two chains up into the dark
        for cx in (x0 + 26, x1 - 26):
            y, k = sy, 0
            while y > 100:
                if k % 2 == 0:
                    ellipse(ctx, cx, y - 9, 6.5, 11)
                    core.stroke(ctx, INK, 7)
                    ellipse(ctx, cx, y - 9, 6.5, 11)
                    core.stroke(ctx, "#7d8496", 3.5)
                else:
                    ctx.move_to(cx, y - 17)
                    ctx.line_to(cx, y - 1)
                    core.stroke(ctx, INK, 7)
                    ctx.move_to(cx, y - 17)
                    ctx.line_to(cx, y - 1)
                    core.stroke(ctx, "#7d8496", 3)
                y -= 16
                k += 1
        # two plain books (left) and a little potion bottle (right)
        for (bx, bw, bh, col) in ((x0 + 10, 22, 104, "#a8344c"), (x0 + 33, 19, 88, "#2f7487")):
            rrect(ctx, bx, sy - bh, bw, bh, 3)
            _fs(ctx, col, INK, 4)
            ctx.move_to(bx + 3, sy - bh + 16)
            ctx.line_to(bx + bw - 3, sy - bh + 16)
            core.stroke(ctx, "monocle", 2.5)
        px = x1 - 22
        circle(ctx, px, sy - 22, 20)
        _fs(ctx, "#8a5bd0", INK, 4)
        rrect(ctx, px - 6, sy - 62, 12, 24, 3)
        _fs(ctx, "#cfc6dc", INK, 3.5)
        circle(ctx, px - 7, sy - 28, 5)
        core.fill(ctx, (1, 1, 1, 0.55))
    # plank
    rrect(ctx, x0, sy, x1 - x0, 20, 4)
    _fs(ctx, "#6b3f22", INK, 4.5)
    ctx.move_to(x0 + 5, sy + 5)
    ctx.line_to(x1 - 5, sy + 5)
    core.stroke(ctx, "#8c5a33", 3)


# ---------------------------------------------------------------------------
# where the Big Book is: (x, y, s, rot, sx, sy) bottom-centre pose
# ---------------------------------------------------------------------------
def _qbez(a, c, b, u):
    v = 1 - u
    return (v * v * a[0] + 2 * u * v * c[0] + u * u * b[0],
            v * v * a[1] + 2 * u * v * c[1] + u * u * b[1])


def _book_pose(t, T):
    bx, by, bs = BOOK_SHELF
    hx, hy = BOOK_HOLD
    lift = (bx + 8, by - 34)
    if t < T.pull0:
        rot = 0.0
        if t >= T.curl1:              # the tail takes up the slack: a little tug
            rot = -0.035 * math.sin((t - T.curl1) * 2 * math.pi * 3.2)
        return bx, by, bs, rot, 1.0, 1.0
    if t < T.swing0:                  # yanked up off the plank
        u = ease_out(seg(t, T.pull0, T.swing0))
        return lerp(bx, lift[0], u), lerp(by, lift[1], u), bs, -0.14 * u, 1.0, 1.0
    if t < T.swing1:                  # swung down past Snake, in front of him
        u = ease_in_out(seg(t, T.swing0, T.swing1))
        x, y = _qbez(lift, SWING_C, (hx, hy), u)
        s = lerp(bs, BOOK_S, smoothstep(u))
        rot = lerp(-0.14, 0.0, u) + 0.38 * math.sin(math.pi * u)
        return x, y, s, rot, 1.0, 1.0
    if t < T.book:                    # arrives (squash + settle), hovers, is taken
        u = t - T.swing1
        dy = -14 * math.exp(-u * 9) * math.sin(u * 22)
        sx = sy = 1.0
        if u < 0.125:
            sx, sy = 1.08, 0.92
        hover = 1 - smoothstep(seg(t, T.take - 0.15, T.take + 0.05))
        dy += 3.0 * math.sin(u * 7.0) * hover * smoothstep(seg(u, 0.2, 0.4))
        dy -= 8 * _bump(t, T.take, 0.45, 0.12)          # "takes" it: a tiny lift
        return hx, hy + dy, BOOK_S, 0.0, sx, sy
    # set down on the desk (heavy: small lift, then plop), squash, settle
    if t < T.land:
        u = seg(t, T.book, T.land)
        return hx, lerp(hy, BOOK_Y, ease_in(u)) - 26 * math.sin(math.pi * u), BOOK_S, 0.0, 1, 1
    sx = sy = 1.0
    if t < T.land + 0.125:
        sx, sy = 1.12, 0.88
    elif t < T.land + 0.3:
        u = seg(t, T.land + 0.125, T.land + 0.3)
        sx, sy = lerp(1.12, 1.0, ease_out_back(u)), lerp(0.88, 1.0, ease_out_back(u))
    return BOOK_X, BOOK_Y, BOOK_S, 0.0, sx, sy


def _book_pt(bp, lx, ly):
    """World point of book-local (lx, ly) (unscaled cover units, bottom-centre origin)."""
    x, y, s, rot, sx, sy = bp
    c, sn = math.cos(rot), math.sin(rot)
    px, py = lx * s * sx, ly * s * sy
    return (x + c * px - sn * py, y + sn * px + c * py)


# ---------------------------------------------------------------------------
# Snake's reaching TAIL. The rig draws the coil; during the gag its front part
# is swapped (temporarily, see shot_lair) for one that peels off at TAIL_J and
# runs out along a spline to the book. The hook over the book's top edge is
# drawn again after the book so the tail visibly wraps it.
# ---------------------------------------------------------------------------
HOOK_UP = [(0, -16), (4, -82), (12, -144), (22, -200)]       # tip searching, pointing up
HOOK_CURL = [(4, -20), (30, -44), (56, -30), (58, 6)]        # up from behind, curled onto the cover
HOOK_DRAPE = [(-2, -40), (28, -36), (50, -12), (50, 22)]     # carried: over the top like a handle
HOOK_REL = [(-10, -60), (8, -84), (32, -90), (48, -76)]      # let go: tip lifts off, uncurls
_TAIL = {}


def _to_world(p, dy, lean):
    c, s = math.cos(lean), math.sin(lean)
    return (MX + MS * (c * p[0] - s * p[1]), MY + dy + MS * (s * p[0] + c * p[1]))


def _resample(pts, n):
    d = [0.0]
    for a, b in zip(pts, pts[1:]):
        d.append(d[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    L = d[-1] or 1.0
    out, j = [], 0
    for i in range(n):
        s = L * i / (n - 1)
        while j < len(d) - 2 and d[j + 1] < s:
            j += 1
        u = (s - d[j]) / max(1e-6, d[j + 1] - d[j])
        out.append((lerp(pts[j][0], pts[j + 1][0], u), lerp(pts[j][1], pts[j + 1][1], u)))
    return out


def _tail_params(t, T):
    """(ext, curl, rel, over) or None. ext 0 rest coil .. 1 reaching; curl: hook
    over the book; rel: let go; over: from 'up behind the shelf book' to
    'carrying it by the top edge' (once it is off the shelf)."""
    if t < T.reach0 or t >= T.ret1:
        return None
    ext = ease_out(seg(t, T.reach0, T.reach1))
    if t >= T.ret0:
        ext = 1 - ease_in_out(seg(t, T.ret0, T.ret1))
    curl = smoothstep(seg(t, T.reach1 - 0.05, T.curl1))
    rel = smoothstep(seg(t, T.unhook0, T.unhook1))
    over = smoothstep(seg(t, T.pull0, T.swing0 + 0.12))
    return ext, curl, rel, over


def _tail_ctrl(t, T, J, rest, bp, prm):
    """World control points of the tail (J = where it leaves the coil)."""
    ext, curl, rel, over = prm
    ax, ay = _book_pt(bp, -110, -300)                  # top edge, left of the title
    c, s = math.cos(bp[3]), math.sin(bp[3])

    def off(ox, oy):
        return (ax + c * ox - s * oy, ay + s * ox + c * oy)
    # approach: on the shelf from below, behind the plank and the book; once it
    # is off the shelf, from above-left, draped over the top edge
    b0, b1 = _book_pt(bp, -110, 40), _book_pt(bp, -110, -150)
    a0, a1 = off(-62, -96), off(-26, -62)
    hk0 = (lerp(b0[0], a0[0], over), lerp(b0[1], a0[1], over))
    hk1 = (lerp(b1[0], a1[0], over), lerp(b1[1], a1[1], over))
    hook = []
    for p_up, p_c, p_d, p_r in zip(HOOK_UP, HOOK_CURL, HOOK_DRAPE, HOOK_REL):
        ox = lerp(lerp(lerp(p_up[0], p_c[0], curl), p_d[0], over), p_r[0], rel)
        oy = lerp(lerp(lerp(p_up[1], p_c[1], curl), p_d[1], over), p_r[1], rel)
        hook.append(off(ox, oy))
    # route J -> book: out under his left arm, up the gap between Snake's head
    # and his face, then on to the book (kept visible the whole way)
    A, G = (262, 992), (278, 862)
    M = (lerp(G[0], hk0[0], 0.5) + 18 * (1 - over), lerp(G[1], hk0[1], 0.5) - 26 * over)
    reach = [J, A, G, M, hk0, hk1] + hook
    # life: a travelling wiggle while it searches
    wig = 9.0 * (1 - smoothstep(seg(t, T.reach1, T.curl1)))
    for i in (1, 2, 3, 4):
        a, b = reach[i - 1], reach[i + 1]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        w = wig * math.sin(t * 10.0 - i * 1.4)
        reach[i] = (reach[i][0] - dy / L * w, reach[i][1] + dx / L * w)
    return [(lerp(r[0], q[0], ext), lerp(r[1], q[1], ext)) for r, q in zip(rest, reach)]


def _tail_front(ctx, P, split, W, fp):
    """Stand-in for villain._snake_front while the tail is out (villain-local ctx)."""
    st = _TAIL
    t, T, dy, lean = st["t"], st["T"], st["dy"], st["lean"]
    Pw = [_to_world(p, dy, lean) for p in P]
    rest = _resample(Pw[TAIL_J:], 10)
    rest[0] = Pw[TAIL_J]
    ctrl = _tail_ctrl(t, T, Pw[TAIL_J], rest, st["bp"], st["prm"])
    tail = SN.coil_points([Pw[TAIL_J - 5]] + ctrl, TAIL_NPER)[TAIL_NPER:]
    ext = st["prm"][0]
    base = W[TAIL_J]
    n = len(tail)
    nr = len(P) - 1 - TAIL_J
    tw = []
    for i in range(n):
        u = i / (n - 1)
        w_rest = W[TAIL_J + min(nr, int(round(u * nr)))]
        w_reach = base if u < 0.4 else lerp(base, 12.0, ((u - 0.4) / 0.6) ** 1.1)
        tw.append(lerp(w_rest, w_reach, ext))
    # back to villain-local coords for the rig pass
    c, s = math.cos(lean), math.sin(lean)
    loc = []
    for (x, y) in tail:
        lx, ly = (x - MX) / MS, (y - MY - dy) / MS
        loc.append((c * lx + s * ly, -s * lx + c * ly))
    loc[0] = P[TAIL_J]
    P2 = list(P[:TAIL_J]) + loc
    W2 = list(W[:TAIL_J]) + tw
    if st["prm"][1] <= 0.01:
        # still searching: the whole tail stays behind the book / plank
        SN.draw_tube(ctx, P2, W2, split, len(P2) - 1, cap0=False, cap1=True, belly_side=-1,
                     spot_phase=30)
        st["wrap"] = None
        return P2[-1]
    k = TAIL_J + TAIL_K * TAIL_NPER
    SN.draw_tube(ctx, P2, W2, split, k, cap0=False, cap1=False, belly_side=-1, spot_phase=30)
    st["wrap"] = ([_to_world(p, dy, lean) for p in P2], [w * MS for w in W2], k)
    return P2[-1]


def _draw_tail_hook(ctx):
    """The hook part of the tail, over the book (world coords)."""
    wrap = _TAIL.get("wrap")
    if not wrap:
        return
    Pw, Ww, k = wrap
    SN.draw_tube(ctx, Pw, Ww, k, len(Pw) - 1, cap0=False, cap1=True, belly_side=-1,
                 spot_phase=14, line_w=6.0 * MS)


def _overlay_arms(ctx, t, ex, arms, dy, lean):
    """Redraw the rig's two arms exactly (same pose maths) on top of the book."""
    p = V.resolve_expr(ex)
    A, B, a_shy, _, _ = V.resolve_arms(arms, t)
    breath = math.sin(t * 2 * math.pi / 3.6 + 1 * 1.3)
    shy = p["shy"] + a_shy - breath * 2.5
    with saved(ctx, MX, MY + dy, MS, lean) as c:
        c.set_tolerance(0.3)
        V._draw_arm(c, (-V.SHOULDER[0], V.SHOULDER[1] + shy), A)
        V._draw_arm(c, (V.SHOULDER[0], V.SHOULDER[1] + shy), B)


# ---------------------------------------------------------------------------
# state tables (Malvo, Hissy, AI in the lair)
# ---------------------------------------------------------------------------
def _malvo_state(t, T):
    w3, w4, w6, w8 = T.w[3], T.w[4], T.w[6], T.w[8]
    ex = keyed(t, [
        (0.0, "evil_grin"),
        (T.monopop, "shocked", 0.08),
        (T.movie + 0.12, "hopeful", 0.3),          # "Classic movie!" - flattered
        (T.learned, "sheepish", 0.3),              # "...actually learned from it." uh-oh
        (T.meme1, "thinking", 0.01),
        (T.L[3].start, "shocked", 0.1),
        (w3[3], "excited", 0.15),
        (w3[4], "evil_grin", 0.22),
        (T.stand, "smug", 0.2),
        (T.evil, "sneaky", 0.1), (T.evil + 0.15, "smug", 0.1),
        (T.evil + 0.30, "sneaky", 0.1), (T.evil + 0.45, "smug", 0.1),
        (T.thunder, "evil_grin", 0.1),
        (T.L[6].start, "excited", 0.15),
        (T.L6.end, "thinking", 0.3),               # still searching, oblivious
        (T.ah - 0.06, "excited", 0.1),             # "Ah!"
        (T.take, "s02_polite", 0.25),              # "Thank you..."
        (T.snk, "s02_nod", 0.18),                  # "...my minion." little nod
        (T.minion + 0.3, "s02_polite", 0.3),
        (T.book, "happy", 0.25),                   # pats it lovingly
        (T.cu1, "sheepish", 0.01),
        (T.me, "hopeful", 0.2),
        (T.whistle - 0.12, "s02_whistle", 0.2),    # lips pursed as the whistle starts
    ])
    look = keyed_v(t, [
        (0.0, (0.5, -0.6)),
        (T.monopop, (0.8, -0.5), 0.1),
        (T.movie + 0.12, (-0.1, 0.9), 0.3),        # down at his fallen prop
        (T.learned, (0.75, -0.35), 0.3),           # ...and back at the AI
        (T.meme1, (0.4, -0.2), 0.01),
        (T.L[3].start, (0.9, -0.6), 0.1),
        (w3[4], (0.0, 0.0), 0.25),
        (T.stand, (0.1, -0.3), 0.25),
        (T.thunder, (0.0, -0.5), 0.2),
        (T.hissy, (0.3, -0.8), 0.4),
        # "Where's my Big Book...?" looks around: left, right, up-right
        (T.L[6].start, (-1.0, 0.1), 0.15),
        (w6[2], (1.0, -0.15), 0.22),
        (w6[5], (0.75, -0.8), 0.25),
        (T.L6.end, (0.55, -0.35), 0.3),
        (T.swing1 + 0.05, (0.35, 0.95), 0.12),     # it's there! eyes drop to it
        (T.take, (-0.72, 0.12), 0.22),             # turns to Snake
        (T.book, (0.55, 0.85), 0.15),              # loving look at the book
        (T.cu1, (0.0, 0.1), 0.01),
        (T.hide + 0.05, (0.6, 0.9), 0.12),
        (T.hide + 0.45, (0.0, 0.1), 0.2),
        (T.me, (0.55, -0.35), 0.2),
        (T.whistle, (-0.5, -0.8), 0.3),
    ])
    # arms (partial "present" keeps the glove inside the frame under the push-in)
    if t < T.movie:
        arms = "point"
    elif t < T.meme0:
        arms = ("point", "rest", smoothstep(seg(t, T.movie, T.movie + 0.55)))
    elif t < w3[3]:
        arms = "rest"
    elif t < w3[4]:
        arms = ("rest", "point", smoothstep(seg(t, w3[3], w3[3] + 0.15)))
    elif t < T.stand:
        arms = ("point", "rub", smoothstep(seg(t, w3[4], w3[4] + 0.22)))
    elif t < T.L[4].start + 0.05:
        arms = ("rub", "rest", smoothstep(seg(t, T.stand, T.stand + 0.2)))
    elif t < T.thunder - 0.12:
        arms = ("rest", "present", PRESENT_K * ease_out_back(seg(t, T.L[4].start + 0.05,
                                                          T.L[4].start + 0.4)))
    elif t < T.thunder:
        arms = ("rest", "present", PRESENT_K * (1 - smoothstep(seg(t, T.thunder - 0.12, T.thunder))))
    elif t < T.hissy:
        arms = ("rest", "fist", smoothstep(seg(t, T.thunder, T.thunder + 0.15)))
    elif t < T.L[6].start:
        arms = ("fist", "rest", smoothstep(seg(t, T.hissy, T.hissy + 0.45)))
    elif t < T.ah:                                  # palms up: "where is it?"
        arms = ("rest", "s02_where", ease_out_back(seg(t, T.L[6].start + 0.05,
                                                         T.L[6].start + 0.35)))
    elif t < T.take - 0.05:                         # "Ah!" hands come in for it
        arms = ("s02_where", "s02_reach", smoothstep(seg(t, T.ah, T.ah + 0.25)))
    elif t < T.book:                                # takes it
        arms = ("s02_reach", "s02_hold", smoothstep(seg(t, T.take - 0.05, T.take + 0.12)))
    elif t < T.land + 0.1:                          # sets it down, right hand to the top
        arms = ("s02_hold", "s02_pat", smoothstep(seg(t, T.book, T.land + 0.1)))
    elif t < T.cu1:                                 # loving pats
        pat = max(0.0, math.sin((t - T.land - 0.1) * 2 * math.pi * 2.2))
        arms = ("s02_pat", "s02_patup", pat)
    elif t < T.me:
        arms = "rest"
    elif t < T.whistle:
        arms = ("rest", "shrug", 0.72 * ease_out_back(seg(t, T.me, T.me + 0.25)))
    else:
        arms = ("rest", "shrug", 0.72 * (1 - smoothstep(seg(t, T.whistle, T.whistle + 0.4))))
    # blink overrides
    blink = None
    if t < T.monopop:
        blink = 0.0                                   # frozen freeze-frame
    elif T.swing1 <= t < T.book:
        # wide-eyed "Ah!" and a warm look at Snake (no stray auto-blink that
        # would read as a wink), then eyes gently closed for the little nod
        blink = slow_blink(t, T.snk, close=0.1, hold=0.26, open_=0.14) or 0.0
    elif T.land <= t < T.cu0:
        blink = 0.42                                  # loving half lids
    elif T.cu1 <= t < T.whistle:
        for b0 in (T.w[8][1] + 0.05, T.w[8][1] + 0.17, T.w[8][1] + 0.29):
            if b0 <= t < b0 + 0.07:
                blink = 1.0
    # body: stand up / lean / laugh bob / shrink
    dy = 0.0
    dy -= 22 * ease_out_back(seg(t, T.stand, T.stand + 0.3)) * (
        1 - smoothstep(seg(t, T.hissy + 0.2, T.hissy + 0.7)))
    lean = -0.05 * ease_out_back(seg(t, T.stand, T.stand + 0.3)) * (
        1 - smoothstep(seg(t, T.hissy + 0.2, T.hissy + 0.7)))
    if T.L[5].start <= t < T.L[5].end:
        lean += 0.03 * math.sin((t - T.L[5].start) * 2 * math.pi * 4)
    if t >= T.cu1:
        dy += 10
    return ex, look, arms, blink, dy, lean


def _hissy_state(t, T):
    ex = keyed(t, [
        (0.0, "smug"),
        (T.monopop, "shocked", 0.08),
        (T.real, "side_eye", 0.3),
        (T.meme1, "unimpressed", 0.01),
        (T.thunder, "shocked", 0.06),
        (T.thunder + 0.55, "unimpressed", 0.3),
        (T.hissy, "side_eye", 0.3),
        (T.L[6].start + 0.35, "unimpressed", 0.25),   # sigh... he means the book
        (T.reach0 - 0.05, "idle", 0.25),               # watches its own tail go get it
        (T.curl1 - 0.1, "smug", 0.25),                 # got it
        (T.take, "happy", 0.2),                        # "Thank you, my minion."
        (T.bow0, "s02_bow", 0.2),                      # polite little bow back
        (T.bow0 + 0.38, "happy", 0.25),
        (T.cu1, "side_eye", 0.01),
    ])
    look = keyed_v(t, [
        (0.0, (0.5, -0.5)),
        (T.monopop, (0.6, -0.2), 0.1),
        (T.real, (0.0, 0.0), 0.3),
        (T.meme1, (0.8, -0.25), 0.01),
        (T.thunder, (-0.2, -0.4), 0.06),
        (T.thunder + 0.55, (0.8, -0.25), 0.3),
        (T.hissy, (-0.05, 0.0), 0.01),
        (T.hissy + 0.02, (-1.15, 0.05), 0.4),
        (T.L[6].start + 0.35, (0.0, -1.0), 0.25),
        (T.reach0 - 0.05, (-0.45, -1.0), 0.3),         # up at the shelf
        (T.take, (0.9, 0.0), 0.2),                     # at him
        (T.cu1, (0.0, 0.0), 0.01),
        (T.me, (-1.15, 0.05), 0.35),
    ])
    if T.pull0 <= t < T.take + 0.25:
        # eyes ride along with the book on the swing
        bp = _book_pose(t, T)
        cx, cy = _book_pt(bp, 0, -150)
        k = smoothstep(seg(t, T.pull0, T.pull0 + 0.2)) * (1 - smoothstep(seg(t, T.take,
                                                                            T.take + 0.25)))
        tgt = (clamp((cx - 160) / 220, -1.0, 1.0), clamp((cy - 800) / 260, -1.0, 1.0))
        look = (lerp(look[0], tgt[0], k), lerp(look[1], tgt[1], k))
    tongue = None
    if T.hissy + 0.42 <= t < T.hissy + 0.67 or T.me + 0.5 <= t < T.me + 0.75:
        tongue = True
    elif t < T.monopop + 0.6 or T.take <= t < T.cu0:
        tongue = False
    return {"expr": ex, "look": look, "mouth": 0.0, "tongue": tongue}


def _ai_lair_state(t, T):
    ex = keyed(t, [
        (0.0, "happy"),                            # rises beaming at the fallen classic
        (T.real, "warm", 0.3),                     # "Real AI actually learned from it."
        (T.meme1, "amused", 0.01),
        (T.w[3][3], "skeptical", 0.2),
        (T.w[3][4] + 0.25, "amused", 0.3),
        (T.stand + 0.15, "skeptical", 0.25),
        (T.evil, "half", 0.3),
        (T.evil + 0.4, "unimpressed", 0.4),
        (T.L[5].start + 0.45, "stare", 0.3),
        (T.hissy + 0.3, "unimpressed", 0.3),
        (T.hissy + 0.6, "amused", 0.25),
        (T.L[6].start + 0.6, "skeptical", 0.25),
        (T.reach0 + 0.25, "alert", 0.12),          # oh - the tail
        (T.curl1, "amused", 0.3),                  # Snake's got it
        (T.take + 0.1, "warm", 0.3),               # aww, manners
        (T.land, "alert", 0.08),                   # ...a book of EVIL PLOTS
        (T.land + 0.35, "thinking", 0.3),
        (T.cu1, "unimpressed", 0.01),
        (T.whistle + 0.15, "stare", 0.3),
    ])
    look = keyed_v(t, [
        (0.0, (-0.6, 0.65)),                       # fondly down at the toppled cutout
        (T.real, (0.0, 0.0), 0.3),                 # to camera: "Real AI..."
        (T.from_, (-0.55, 0.6), 0.25),             # "...learned from it." credit to it
        (T.meme1, (-0.8, 0.3), 0.01),
        (T.evil, (-0.8, 0.35), 0.3),
        (T.L[5].start + 0.45, (0.0, 0.0), 0.3),
        (T.hissy + 0.3, (-1.0, 0.45), 0.3),
        (T.L[6].start + 0.6, (-0.8, 0.3), 0.25),
        (T.reach0 + 0.25, (-1.0, -0.6), 0.25),     # up at the shelf
        (T.take, (-0.9, 0.35), 0.3),               # at the pair
        (T.land, (-0.6, 0.85), 0.12),
        (T.cu1, (-0.8, 0.4), 0.01),
        (T.hide + 0.05, (-0.55, 0.95), 0.15),
        (T.hide + 0.5, (-0.8, 0.35), 0.25),
        (T.whistle + 0.15, (0.0, 0.0), 0.3),
    ])
    if T.pull0 <= t < T.take + 0.3:
        # follows the swinging book
        cx, cy = _book_pt(_book_pose(t, T), 0, -150)
        k = smoothstep(seg(t, T.pull0, T.pull0 + 0.25)) * (1 - smoothstep(seg(t, T.take,
                                                                             T.take + 0.3)))
        tgt = (clamp((cx - AX) / 420, -1.0, 1.0), clamp((cy - AY) / 380, -1.0, 1.0))
        look = (lerp(look[0], tgt[0], k), lerp(look[1], tgt[1], k))
    # a fond slow blink inside the respectful nod on "movie!"
    blink = (slow_blink(t, T.movie + 0.12, 0.1, 0.14, 0.12) or slow_blink(t, T.evil + 1.25)
             or slow_blink(t, T.me + 0.2))
    shake = 0.0
    nod = (0.5 * _bump(t, T.movie, 0.6, 0.1) + 0.3 * _bump(t, T.from_ + 0.1, 0.5, 0.1)
           + 0.5 * _bump(t, T.hissy + 0.6, 0.7, 0.1)
           + 0.4 * _bump(t, T.snk + 0.1, 0.6, 0.1))
    think = 0.55 * smoothstep(seg(t, T.land + 0.35, T.land + 0.6)) if T.land <= t < T.cu0 else 0.0
    hands = "idle"
    if T.movie <= t < T.meme0:
        # a thumbs up for the classic, held through "...learned", lowered as
        # its eyes go back to the cutout on "from it" (with a small nod)
        if t < T.from_ + 0.1:
            hands = ("idle", "thumbs_up", smoothstep(seg(t, T.movie, T.movie + 0.25)))
        else:
            hands = ("thumbs_up", "idle", smoothstep(seg(t, T.from_ + 0.1, T.from_ + 0.45)))
    elif T.w[3][4] <= t < T.stand:
        hands = ("idle", "shrug", smoothstep(seg(t, T.w[3][4] + 0.2, T.w[3][4] + 0.5)))
    elif T.stand <= t < T.stand + 0.4:
        hands = ("shrug", "idle", smoothstep(seg(t, T.stand, T.stand + 0.3)))
    return ex, look, blink, shake, nod, think, hands


# ---------------------------------------------------------------------------
# camera for the lair shots
# ---------------------------------------------------------------------------
def _lair_cam(t, T):
    face = (MX, MY - 518 * MS)
    hiss_c = (300, 790)
    if t < T.meme0 or t < T.stand:
        return face, 1.0
    if t < T.hissy:
        return face, 1.0 + 0.05 * ease_in_out(seg(t, T.stand, T.stand + 0.45))
    if t < T.L[6].start:
        k = ease_in_out(seg(t, T.hissy, T.hissy + 0.4))
        c = (lerp(face[0], hiss_c[0], k), lerp(face[1], hiss_c[1], k))
        return c, lerp(1.05, 1.12, k)
    if t < T.L6b.start:
        # hard cut back to the wide on the line: shelf, tail and AI all in view
        return face, 1.0
    if t < T.cu0:
        # gentle push-in on the two of them for the thank-you
        k = ease_in_out(seg(t, T.L6b.start, T.L6b.end))
        pair = (300, 840)
        return (lerp(face[0], pair[0], k), lerp(face[1], pair[1], k)), 1.0 + 0.06 * k
    # final shot: tighter framing, cut in and static (bitrate: no zoom after a cut)
    return (MX - 10, MY - 500 * MS), 1.10


# ---------------------------------------------------------------------------
# SHOT: the lair (two-shot with the AI hologram)
# ---------------------------------------------------------------------------
def shot_lair(ctx, t, info, T):
    (cx, cy), cs = _lair_cam(t, T)
    # one-off impact bump when the cutout slaps down (not a shake)
    u = t - T.slap
    bump_y = 7.0 * math.exp(-u * 18) * math.cos(u * 40) if 0 <= u < 0.25 else 0.0
    flash_k = 0.0
    if T.thunder <= t < T.thunder + 0.3:
        # stepped cartoon strobe (3 held levels) instead of a smooth fade:
        # same hit, far fewer full-frame changes for the encoder
        u = t - T.thunder
        flash_k = 1.0 if u < 0.085 else (0.55 if u < 0.17 else 0.22)

    ctx.save()
    ctx.translate(cx, cy + bump_y)
    ctx.scale(cs, cs)
    ctx.translate(-cx, -cy)

    P.lair_bg(ctx, t, flash=flash_k, bolt_seed=1)
    science_photo(ctx, *PHOTO)
    shelf(ctx)

    # --- Malvo + Hissy ---------------------------------------------------------
    ex, look, arms, blink, dy, lean = _malvo_state(t, T)
    snake = _hissy_state(t, T)
    flare = 0.0
    if t >= T.stand:
        flare = ease_out_back(seg(t, T.stand, T.stand + 0.35))
        flare *= 1 - 0.75 * smoothstep(seg(t, T.hissy, T.hissy + 0.8))
        if t >= T.L[6].start:
            flare *= 1 - smoothstep(seg(t, T.L[6].start, T.L[6].start + 0.4))
        if T.thunder <= t < T.thunder + 0.4:
            flare *= 1 + 0.12 * _bump(t, T.thunder, 0.4, 0.05)
    if flare > 0.01 and t < T.cu0:
        with saved(ctx, MX, MY + dy, MS, lean) as c:
            cape_flare(c, flare)
    # During the laugh his raised fist would vanish behind the hologram: the AI
    # floats back out of his way (deadpan) and sits BEHIND his arm meanwhile.
    rise_k = seg(t, T.rise0, T.rise1)
    ai_behind = T.thunder - 0.15 <= t < T.hissy + 0.8
    if ai_behind:
        _draw_lair_ai(ctx, t, info, T, rise_k)
    mouth = info.mouth("villain", t)
    if t >= T.whistle - 0.12:
        # innocent whistle: small round pursed lips (formed as the sound
        # starts), pulsing on each whistled note; relaxes when the tune ends
        u = t - T.whistle
        wk = smoothstep(seg(u, -0.12, 0.0)) * (1 - smoothstep(seg(u, WHISTLE_LEN, WHISTLE_LEN + 0.2)))
        pulse = max(_bump(u, o, 0.2, 0.03) for o in WHISTLE_ONSETS)
        pk = (0.06 + 0.04 * pulse, -1.0)                              # stays < teeth threshold
        mouth = (lerp(mouth[0], pk[0], wk), lerp(mouth[1], pk[1], wk))
    bp = _book_pose(t, T)
    prm = _tail_params(t, T)
    _TAIL.clear()
    if prm is not None:
        # Snake's tail is out: swap the rig's front-coil drawer for ours for
        # this one call only (restored straight after, nothing else is touched)
        _TAIL.update(t=t, T=T, dy=dy, lean=lean, bp=bp, prm=prm)
        orig = V._snake_front
        V._snake_front = _tail_front
        try:
            draw_villain(ctx, MX, MY + dy, MS, t, expr=ex, look=look,
                         mouth=mouth, arms=arms, lean=lean, blink=blink,
                         snake=snake)
        finally:
            V._snake_front = orig
    else:
        draw_villain(ctx, MX, MY + dy, MS, t, expr=ex, look=look,
                     mouth=mouth, arms=arms, lean=lean, blink=blink,
                     snake=snake)

    # cool light from the AI on Malvo's face side
    ai_on = t >= T.rise0 + 0.1
    if ai_on:
        radial_glow(ctx, MX + 150, MY - 520 * MS, 380, "ai_rim",
                    0.12 * smoothstep(seg(t, T.rise0, T.rise1)))

    # --- desk, computer, book -------------------------------------------------------
    comp_glow = 1.0 + 0.6 * _bump(t, T.rise0 - 0.05, 0.7, 0.1)
    P.desk(ctx, *DESK, lamp=False, emblem=False)
    P.skull_lamp(ctx, 104, DESK[1] - 12, 0.8)
    P.computer(ctx, *COMP, view="side", facing=-1, t=t, glow=comp_glow)

    if prm is not None and t < T.swing0 + 0.12:
        shelf(ctx, plank_only=True)               # the tail goes up behind the plank
    if t < T.hide + 0.35:
        _draw_book(ctx, t, T, bp)
    _draw_tail_hook(ctx)
    if T.swing1 <= t < T.cu0:
        _overlay_arms(ctx, t, ex, arms, dy, lean)  # his hands are in front of the book
    if T.land <= t < T.cu0 and t >= T.land + 0.1:
        P.emote(ctx, "heart", MX + 150, MY - 690 * MS, 1.0, t, T.land + 0.15)

    # --- the cardboard robot (standing until the slap, then lying flat) --------------
    _draw_cutout(ctx, t, T)

    # --- the AI hologram ------------------------------------------------------------
    if t >= T.rise0 and not ai_behind:
        _draw_lair_ai(ctx, t, info, T, rise_k)

    # --- tags & emotes ----------------------------------------------------------
    _draw_tags(ctx, t, T)
    _draw_classic(ctx, t, T)
    if T.whistle <= t:
        # beside the whistling mouth's corner (rig mouth ~ (0, -384) + expr offsets)
        music_notes(ctx, MX - 30, MY + dy - 384 * MS, t, T.whistle)

    if flash_k > 0:
        P.flash(ctx, 0.2 * flash_k)
    ctx.restore()


CUT_FLAT = 0.13      # lying flat on its face: a thin slab of brown back on the floor


def _draw_cutout(ctx, t, T):
    """Wobble, then it tips FORWARD (toward camera): the face squashes to the
    base line and the brown cardboard back sweeps down toward us; on the slap
    it lies flat on its face - a thin slab of cardboard back on the floor at
    the very bottom of the frame (below the caption band) for the l01 beat."""
    if t >= T.meme0:
        return                          # (it stays down there, out of shot from here on)
    base_y = CUT_BASE
    rot, sy = 0.0, 1.0
    if t < T.wob1:
        u = seg(t, T.tip, T.wob1)
        rot = 0.06 * math.sin(u * 2 * math.pi * 1.5) * (0.5 + 0.5 * u)
    elif t < T.slap:
        u = seg(t, T.wob1, T.slap)
        sy = 1.0 - 2.6 * ease_in(u)
        rot = 0.04 * (1 - u)
    else:
        # flattens onto the floor, a little cardboard flap, then still
        u = t - T.slap
        k = ease_out(seg(u, 0.0, 0.1))
        sy = lerp(-1.6, -CUT_FLAT, k) * (1 + 0.3 * math.exp(-u * 14) * math.sin(u * 40) * k)
    with saved(ctx, CUT_X, base_y, 1.0, rot) as c:
        if sy >= 0.0:
            c.scale(CUT_S, CUT_S * max(sy, 0.02))
            c.translate(0, -970)
            draw_robot(c, t, glow=1.0, look=(0.0, 0.0), ring_rot=1.1, cutout=True,
                       lights=(0, 0))
        else:
            # back side (seen as it falls toward us): plain cardboard
            c.scale(CUT_S * (1 - 0.25 * sy), CUT_S * -sy)
            c.translate(0, 970)
            c.scale(1, -1)
            _robot_silhouette(c)
            core.fill_stroke(c, CARD, INK, 6)
            if t < T.slap:              # the kickstand folds flat when it lands
                core.poly(c, [(150, 520), (330, 970), (150, 970)])
                _fs(c, CARD_DK, INK, 5)
                for yy in (420, 640, 860):
                    c.move_to(-200, yy)
                    c.line_to(200, yy + 6)
                core.stroke(c, CARD_DK, 4)
    if t >= T.slap:
        dust_puff(ctx, CUT_X, base_y + 60, 600, t, T.slap, n=6, seed=3)


def _draw_book(ctx, t, T, bp):
    """Shelf -> tail -> his hands -> desk (pose from _book_pose); slides away on l08."""
    x, y, s, rot, sx, sy = bp
    flutter = (_bump(t, T.pull0, 0.45, 0.03) + 0.6 * _bump(t, T.swing1, 0.4, 0.03)
               + _bump(t, T.land, 0.5, 0.02))
    if t < T.book:
        if t < T.pull0 + 0.45 and t >= T.pull0:
            dust_puff(ctx, BOOK_SHELF[0], SHELF[2], 150, t, T.pull0, n=6, seed=11, big=0.6)
        with saved(ctx, x, y, 1.0, rot) as c:
            big_book(c, 0, 0, s, t, sx, sy, flutter)
        if T.take <= t < T.take + 0.6:
            P.sparkles(ctx, x - 20, y - 150 * s, 130, t, n=4, seed=6, color="white", size=0.9)
        return
    y = BOOK_Y if t >= T.land else y
    if t >= T.hide:
        # slide down behind the desk edge
        k = ease_in(seg(t, T.hide, T.hide + 0.3))
        y = BOOK_Y + 430 * BOOK_S * k
        clip_y = lerp(BOOK_Y + 6, DESK_BACK_Y, smoothstep(seg(t, T.hide, T.hide + 0.1)))
        ctx.save()
        ctx.rectangle(-200, -200, W + 400, clip_y + 200)
        ctx.clip()
        big_book(ctx, BOOK_X, y, BOOK_S, t, sx, sy, flutter)
        ctx.restore()
        return
    big_book(ctx, BOOK_X, y, BOOK_S, t, sx, sy, flutter)
    dust_puff(ctx, BOOK_X, BOOK_Y + 8, 320, t, T.land, n=6, seed=8, big=0.7)
    if T.land + 0.1 <= t < T.cu0:
        P.sparkles(ctx, BOOK_X - 40, BOOK_Y - 200 * BOOK_S, 110, t, n=4, seed=4, color="white",
                   size=0.9)


def _draw_lair_ai(ctx, t, info, T, rise_k):
    ex, look, blink, shake, nod, think, hands = _ai_lair_state(t, T)
    k = ease_out_back(rise_k, 1.4)
    x = lerp(AI_SRC[0], AX, ease_out(rise_k))
    y = lerp(AI_SRC[1], AY, k)
    s = lerp(0.08, AS, k)
    # float back from the raised fist during the laugh, return on the Hissy beat
    dodge = (ease_in_out(seg(t, T.thunder - 0.15, T.thunder + 0.2))
             * (1 - ease_in_out(seg(t, T.hissy + 0.25, T.hissy + 0.75))))
    x += 50 * dodge
    y -= 88 * dodge
    # light beam from the monitor while it rises
    if rise_k < 1.0 or t < T.rise1 + 0.3:
        a = 0.35 * (1 - smoothstep(seg(t, T.rise1 - 0.1, T.rise1 + 0.3)))
        if a > 0.01:
            sx0 = COMP[0] - 198 * COMP[2]
            core.poly(ctx, [(sx0, COMP[1] - 360 * COMP[2]), (sx0, COMP[1] - 90 * COMP[2]),
                            (x + 90 * s / AS * 0.5, y + 60), (x - 90 * s / AS * 0.5, y + 60)])
            core.fill(ctx, core.alpha("ai_rim", a))
            for i in range(5):
                u = (rise_k * 1.3 + i * 0.21) % 1.0
                px = lerp(sx0, x, u) + math.sin(i * 2.1 + t * 9) * 18
                py = lerp(COMP[1] - 230 * COMP[2], y, u)
                P._star4(ctx, px, py, 9 * (1 - u) + 4)
                core.fill(ctx, core.alpha("ai_eye", a * 2))
    draw_ai(ctx, x, y, s, t, expr=(_aix(ex[0]), _aix(ex[1]), ex[2]), look=look,
            mouth=info.mouth("ai", t), hands=hands, blink=blink, think=think,
            aura=0.6, shake=shake, nod=nod)


def _tag_scale(t, t_in, t_out):
    if t < t_in:
        return 0.0
    k = ease_out_back(seg(t, t_in, t_in + 0.28), 2.2)
    if t_out is not None and t >= t_out:
        k *= 1 - ease_in(seg(t, t_out, t_out + 0.18))
    return k


CLASSIC_XY = (485, 1242)      # above even a 2-line caption, over the fallen cutout


def _draw_classic(ctx, t, T):
    """'CLASSIC' gold tag pointing down at the toppled cutout (it fell toward
    the camera, out of the bottom of the frame), plus a tiny heart + glints."""
    if not (T.sticker <= t < T.meme0):
        return
    x, y = CLASSIC_XY
    k = _tag_scale(t, T.sticker, None)
    if k <= 0.01:
        return
    with saved(ctx, x, y, k, -0.05) as c:
        w, h = P.label_tag(c, 0, 0, "CLASSIC", color="monocle", size=40, font="comic",
                           pointer="down")
    P.emote(ctx, "heart", x + w / 2 + 6, y - h / 2 - 8, 0.5, t, T.movie)
    if t < T.movie + 0.9:
        # glints kept above the caption band (centre y - 40, r 100 -> y <= ~1300)
        P.sparkles(ctx, x - 20, y - 40, 100, t, n=4, seed=9, color="white", size=0.7)


def _draw_tags(ctx, t, T):
    # name tag slam + "self-described" correction
    k1 = _tag_scale(t, T.tag1, T.hissy)
    if k1 > 0.01:
        slam = 1.0 + 0.6 * (1 - ease_out(seg(t, T.tag1, T.tag1 + 0.14)))
        with saved(ctx, MX + 20, 420, k1 * slam, -0.03) as c:
            P.label_tag(c, 0, 0, "THE EVIL GENIUS", color="bubble_villain", size=52,
                        font="comic")
    k2 = _tag_scale(t, T.evil, T.hissy)
    if k2 > 0.01:
        with saved(ctx, MX + 70, 490, k2, 0.04) as c:
            P.label_tag(c, 0, 0, "(self-described)", color="warn", size=30)
    # HISSY
    k3 = _tag_scale(t, T.hissy + 0.25, T.L[6].start + 0.2)
    if k3 > 0.01:
        hx, hy = MX - 300 * MS + 18, 678
        with saved(ctx, hx, hy, k3, -0.06) as c:
            P.label_tag(c, 0, 0, "SNAKE", color="snake", size=48, font="comic")
            text(c, "(unimpressed)", 0, 70, 30, "white", "round", outline="ink", outline_w=7)


# ---------------------------------------------------------------------------
# SHOT: EXPECTATION vs REALITY
# ---------------------------------------------------------------------------
SPLIT_Y = 720


def _expect_panel(ctx, t, T):
    vgradient(ctx, SKY_TOP, SKY_BOT, 0, 0, W, SPLIT_Y)
    # ridge with a few static robot silhouettes
    for (bx, by, bh) in ((110, 640, 110), (210, 626, 92), (790, 632, 104), (890, 620, 90)):
        with saved(ctx, bx, by, bh / 160.0) as c:
            c.rectangle(-22, -50, 16, 52)
            c.rectangle(6, -50, 16, 52)
            rrect(c, -30, -98, 60, 54, 8)
            _round_poly(c, [(-46, -88), (-40, -112), (40, -112), (46, -88)], 8)
            _round_poly(c, [(-32, -160), (32, -160), (26, -116), (-26, -116)], 12)
            core.fill_stroke(c, "#2a0a12", "#0a0307", 6)
            for exx in (-10, 10):
                circle(c, exx, -140, 4.8)
                core.fill(c, "#ff4a68")
    ctx.move_to(-20, 650)
    ctx.curve_to(200, 610, 420, 640, 560, 630)
    ctx.curve_to(760, 618, 900, 600, 1100, 640)
    ctx.line_to(1100, SPLIT_Y + 20)
    ctx.line_to(-20, SPLIT_Y + 20)
    ctx.close_path()
    core.fill(ctx, "#13050a")
    breathe = 0.5 + 0.12 * math.sin(t * 2 * math.pi / 1.6)
    radial_glow(ctx, 495, 400, 340, "danger", 0.45 * breathe)
    rs = 0.78
    look = (0.55 * math.sin((t - T.meme0) * 1.6), 0.0)
    with saved(ctx, 495, 425, rs) as c:
        draw_robot(c, t, glow=1.0, look=look, ring_rot=t * 1.5,
                   lights=(1.0 if int(t * 1.6) % 2 == 0 else 0.15,
                           1.0 if int(t * 1.6 + 1) % 2 == 0 else 0.15))


def shot_meme(ctx, t, info, T):
    # top panel: the trailer fantasy
    ctx.save()
    ctx.rectangle(0, 0, W, SPLIT_Y)
    ctx.clip()
    _expect_panel(ctx, t, T)
    ctx.restore()
    # bottom panel: the real thing (ai_bg shifted so its glow sits behind the AI)
    ctx.save()
    ctx.rectangle(0, SPLIT_Y, W, H - SPLIT_Y)
    ctx.clip()
    ctx.translate(0, 140)
    P.ai_bg(ctx, t, motes=6)
    ctx.restore()
    ax, ay, s = 495, 1105, 0.72
    ex = keyed(t, [(T.meme0, "amused"), (T.wink, "wink", 0.12), (T.L[2].end + 0.05, "amused", 0.3)])
    look = keyed_v(t, [(T.meme0, (0.0, 0.0)), (T.lab2, (0.15, -0.1), 0.2),
                       (T.wink, (0.05, 0.0), 0.15)])
    an = draw_ai(ctx, ax, ay, s, t, expr=ex, look=look, mouth=info.mouth("ai", t),
                 hands=keyed(t, [(T.meme0 - 1, "present")]), aura=0.8)
    hx, hy = an["handR"]
    P.mug(ctx, hx - 4, hy - 6, 1.1, "HELPFUL", t)
    if t >= T.wink:
        exL = an["eyeL"]
        P.emote(ctx, "sparkle", exL[0] - 70, exL[1] - 60, 0.75, t, T.wink, T.L[2].end + 0.1)
    P.split_divider(ctx, SPLIT_Y, t, top="danger", bottom="ai_rim")
    P.label_tag(ctx, 495, 160, "EXPECTATION", color="danger", size=54, t=t, t_in=T.lab1,
                font="comic", rot=-0.03)
    P.label_tag(ctx, 495, 792, "REALITY", color="safe", size=54, t=t, t_in=T.lab2,
                font="comic", rot=0.03)


# ---------------------------------------------------------------------------
# SHOT: F3 AI close-up (the client's line)
# ---------------------------------------------------------------------------
def shot_aicu(ctx, t, info, T):
    w = T.l7
    cam = 1.0 + 0.04 * ease_in_out(seg(t, T.cu0, T.cu1))
    ctx.save()
    ctx.translate(495, 800)
    ctx.scale(cam, cam)
    ctx.translate(-495, -800)
    P.ai_bg(ctx, t)
    ex = keyed(t, [
        (T.cu0, "warm"),
        (w["just"], "determined", 0.2),
        (w["so"] - 0.3, "neutral", 0.3),
        (w["so"], "half", 0.3),
        (w["no"], "unimpressed", 0.4),
        (w["my"], "stare", 0.22),
    ])
    look = keyed_v(t, [
        (T.cu0, (0.0, 0.0)),
        (w["so"], (-0.75, 0.15), 0.3),
        (w["my"], (0.0, 0.0), 0.22),
    ])
    hands = keyed(t, [
        (T.cu0, "present"),
        (w["not"] - 0.08, "stop", 0.16),         # palm out on "not hurt people"
        (w["people"] + 0.35, "idle", 0.3),
    ])
    blink = slow_blink(t, w["scheme"] + 0.22) or slow_blink(t, w["business"] + 0.08)
    nod = 0.45 * _bump(t, T.cu0 + 0.05, 0.7, 0.1)
    draw_ai(ctx, 495, 800, 1.1, t, expr=(_aix(ex[0]), _aix(ex[1]), ex[2]), look=look,
            mouth=info.mouth("ai", t), hands=hands, blink=blink, nod=nod)
    ctx.restore()


# ---------------------------------------------------------------------------
# render / SFX
# ---------------------------------------------------------------------------
def render(ctx, t, info):
    T = _T(info)
    if T.meme0 <= t < T.meme1:
        shot_meme(ctx, t, info, T)
    elif T.cu0 <= t < T.cu1:
        shot_aicu(ctx, t, info, T)
    else:
        shot_lair(ctx, t, info, T)


def SFX(info):
    T = _T(info)
    return [
        (T.tip, "record_scratch", 0),
        (T.wob1 + 0.05, "paper", -4),
        (T.rise0, "swoosh_up", -8),
        (T.slap, "paper", -6),
        (T.monopop - 0.03, "boing", -10),
        (T.movie, "sparkle", -14),             # heart on the CLASSIC tag
        (T.lab1, "pop", -8),                   # EXPECTATION
        (T.lab2, "pop", -8),                   # REALITY
        (T.wink, "sparkle", -10),
        (T.L[3].start + 0.05, "boing", -8),
        (T.stand, "whoosh", -10),
        (T.tag1, "stamp", -6),
        (T.evil, "pop", -10),
        (T.thunder, "thunder", -3),
        (T.hissy + 0.25, "pop", -10),
        (T.hissy + 0.35, "snake_hiss", -8),
        # the tail fetch
        (T.reach0, "swoosh_up", -8),           # tail reaches up
        (T.curl1 - 0.12, "paper", -8),         # hooks the book
        (T.pull0, "page_flip", -7),            # tugged off the shelf, pages riffle
        (T.swing0 + 0.05, "whoosh", -11),      # swung over
        (T.take, "pop", -7),                   # handed over
        (T.bow0, "sparkle", -12),              # Snake's polite bow
        (T.land, "brick_thud", -6),            # heavy book on the desk
        (T.land + 0.12, "sparkle", -14),
        (T.hide, "whoosh", -12),
        (T.whistle, "whistle", -6),            # starts with the pucker + first note
    ]
