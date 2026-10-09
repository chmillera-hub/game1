"""s12 - New plan: a party for the whole town (and one last try).

Shots (every time is derived from cues / word starts, see _T):

  A  rise..party  F5 lair, morning (rain off, dawn-tinted window). Frame 0
                  picks up s11's REAL SMILE; Malvo springs up (dip, rise with
                  overshoot, cape swish). "Hissy!" -> looks at Hissy, who
                  perks up. "New plan." -> winds up and flings a yellow
                  'PARTY' sticky that slaps over the EVIL of EVIL PLANS (the
                  AI's eyes track it past its face). "We throw the whole town
                  a party!" -> presents toward the window/town, fist pump +
                  hop on "party!"; Hissy nods. l02: the AI goes happy,
                  thumbs-up, a nod on "THAT", 5 sparkles; Malvo clasps his
                  hands, delighted.
  B  party..end   THE TOWN SQUARE at dusk (wide, cached static layer):
                  banner, string lights, cardboard robot in a party hat with
                  a balloon, Hissy in shawl + glasses 'reading' THE GENTLE
                  DRAGON to 3 kids, Malvo behind the table (cake + sparkler,
                  red balloon, scroll, popper), every chair in front full
                  and clapping, the neighbor dancing in teal headphones, the
                  AI lantern above. Popper fires (confetti <= 28, 1.2 s).
                  l03: push-in 1 -> 1.35 on Malvo (hand on heart, glistening
                  eyes, monocle fogs, one happy tear on "ME?").
                  l04: the AI lantern (screen space) WINKs on "stats.".
                  lean: paranoid glances, lean toward the AI, SNEAKY SQUINT +
                  steeple; 'NICE TRIES: 10?' chip blinks in.
                  l05 whisper. l06 "Malvo.": instant 😒 (no blend), red strike
                  through "10?", Hissy facepalms (tail over his glasses).
                  l07 "Kidding! Kidding!" shrug, sheepish -> happy; then they
                  both laugh, the chip pops out, ~12 confetti bits drift down
                  while the camera eases back out to the party.
"""
import math

import cairocffi as cairo

from engine import core
from engine.core import (W, H, text, text_width, saved, seg, clamp, ease_out_back,
                         ease_in_out, ease_out, ease_in, rrect, fill_stroke, circle, lerp,
                         smoothstep, ellipse, hash01, noise1, poly, smooth_path,
                         radial_glow, hexc)
from engine import props as P
from engine import captions as _CAPTIONS
from engine import ai_char as AI
from engine.ai_char import draw_ai
from engine import villain as V
from engine.villain import draw_villain
from engine import snake as S
from engine.snake import draw_snake_head

INK = "ink"

# ---------------------------------------------------------------------------
# layout (logical px)
# ---------------------------------------------------------------------------
# shot A: F5 lair
MX, MS = 400.0, 0.92
MY_SIT, MY_UP = 1250.0, 1215.0
AX, AY, AS = 770.0, 640.0, 0.45
DESK = (495, 1250, 1000)
COMP = (1010, 1218, 0.7)                 # pushed to the edge, as s11 left it
PHOTO = (770, 300, 130, 100, 0.05)       # science-fair photo on the corkboard (as s02)
STICKY = (801.0, 213.0, -0.08)           # 'PARTY' sticky over the EVIL of EVIL PLANS
STICKY_WH = (94.0, 62.0)

# shot B: town square (world coords at zoom 1)
VX, VY, VS = 480.0, 1015.0, 0.6          # Malvo behind the table
FOCUS = (480.0, 704.0)                   # Malvo's face (push-in pivot)
TGT = (482.0, 660.0)                     # where his face sits on screen after the push
Z1 = 1.6
AI_W = (760.0, 450.0, 0.32)              # AI lantern in the wide shot
AI_S = (760.0, 330.0, 0.42)              # AI lantern pinned in screen space (push-in)
TABLE = (292.0, 688.0, 1008.0, 1232.0)   # x0, x1, top, cloth bottom (long party cloth)
CAKE = (402.0, 1010.0, 0.6)
BALLOON_W = (642.0, 800.0, 0.75)
BAL_KNOT = (668.0, 1012.0)
POPPER = (618.0, 1010.0, 0.55)
SCROLL = (552.0, 994.0, 0.32)
HISSY_B = (276.0, 872.0, 0.6)          # coiled on the table's left end, rising behind the book
COIL_B = (316.0, 990.0)
BOOK_B = (282.0, 962.0, 0.4)
BENCH = (8.0, 300.0, 1150.0)
ROBOT = (92.0, 994.0, 0.27, -0.09)       # base x, base y, scale, lean
ROBOT_BAL = (176.0, 548.0, 0.6)
NEIGH = (826.0, 1300.0, 0.8)
ROW_A, ROW_B = 1380.0, 1500.0             # audience seat lines (in front of the table)
LAPEL = (100.0, -318.0)

TEAR = "#8fd8ff"
BALLOON, BALLOON_DK = "#ef3346", "#b81f30"
YBAL, YBAL_DK = "#ffd166", "#d9a514"
CAKE_C, CAKE_DK, CAKE_TOP = "#ff8fb8", "#e0679a", "#ffb7d2"
GOLD, GOLD_DK = "#ffcf3a", "#d99a12"
STICKY_C, STICKY_DK = "#ffe066", "#f2cf3a"
BOOK, BOOK_DK, DRAGON = "#3f74d6", "#2a52a6", "#7cd35c"
SHAWL, SHAWL_DK = "#b79ad6", "#8f72b4"
CHAIR, CHAIR_DK = "#8d8798", "#6c6678"
CONF_COLS = ["ai_accent", "danger", "safe", "bubble_villain", "ai_rim", "#ff8fb8"]

SKINS = ["#f1c7a0", "#c68a5e", "#8d5a3b", "#e0a878"]
SHIRTS = ["#ff9ec4", "#9ad7ff", "#ffd166", "#a7e8a0", "#c9a7ff", "#ffb38a", "#7fe0d0"]
HAIRS = ["#3a2618", "#6b3f22", "#1a1420", "#d9a441", "#a33a2a", "#e8e0d0"]

# ---------------------------------------------------------------------------
# custom rig states (unique names; registered once)
# ---------------------------------------------------------------------------
_HAPPY = V.VILLAIN_EXPR["happy"]
V.VILLAIN_EXPR.setdefault("s12_real", dict(
    _HAPPY, ul1=0.42, ul2=0.4, ll1=0.42, ll2=0.4, mc=1.05, mo=0.22, blush=0.6,
    by1=-10, by2=-10, shine=0.4))
V.VILLAIN_EXPR.setdefault("s12_moved", dict(
    _HAPPY, shine=1.0, es=1.06, ul1=0.1, ul2=0.08, ll1=0.3, ll2=0.28, by1=-26, by2=-26,
    ba1=-0.26, ba2=-0.26, bc1=0.5, bc2=0.5, blush=0.75, mc=0.82, mo=0.28, tilt=-0.04))
V.VILLAIN_EXPR.setdefault("s12_me", dict(
    V.VILLAIN_EXPR["hopeful"], shine=1.0, es=1.1, ps=1.25, mc=0.55, mo=0.18, blush=0.7,
    by1=-36, by2=-38, ba1=-0.32, ba2=-0.32, tilt=-0.08))
V.VILLAIN_EXPR.setdefault("s12_eager", dict(
    V.VILLAIN_EXPR["excited"], ba1=0.14, ba2=0.1, by1=-12, by2=-18, mc=1.05, mw=1.25, mo=0.32,
    es=1.04, ul1=0.1, ul2=0.06))
V.VILLAIN_EXPR.setdefault("s12_caught", dict(
    V.VILLAIN_EXPR["shocked"], mono=0.0, hair=0.35, es=1.12, ps=0.6, mo=0.2, mc=-0.2, mw=0.6,
    sweat=0.9, hy=-8, shy=-8, blush=0.3))
V.VILLAIN_EXPR.setdefault("s12_startle", dict(
    V.VILLAIN_EXPR["excited"], es=1.14, ps=0.7, hair=0.8, by1=-40, by2=-42, mo=0.5, mc=0.5,
    mw=0.95, hy=-14))
V.VILLAIN_EXPR.setdefault("s12_laugh", dict(
    _HAPPY, ul1=0.64, ul2=0.62, ll1=0.52, ll2=0.5, mc=1.15, mw=1.25, mo=0.4, mt=0.65,
    blush=0.8, hy=-10, tilt=-0.06, by1=-20, by2=-20, shine=0.2))

_REST_A = V.ARM_POSES["rest"]["a"]
_HEART_B = V._arm(214, -128, 118, -196, -2.75, cu=0.12, th=0.25, sp=0.45, hs=1.0, tf=-1)
V.ARM_POSES.setdefault("s12_heart", V._pose(_REST_A, _HEART_B, shy=-8, hdy=2))
V.ARM_POSES.setdefault("s12_wind", V._pose(
    _REST_A, V._arm(318, -330, 236, -500, -1.95, cu=0.85, th=0.2, sp=0.2, tf=-1), shy=-6))
V.ARM_POSES.setdefault("s12_throw", V._pose(
    _REST_A, V._arm(332, -322, 384, -414, -0.92, cu=0.05, th=-0.1, sp=0.9, tf=-1), shy=-4))


def _ax(name, **kw):
    d = dict(AI.EXPR[name])
    d.update(kw)
    return d


AIX = {
    "laugh": _ax("happy", lL=0.5, lR=0.5, lc=0.5, tL=0.12, tR=0.12, mo=0.7, mc=1.1,
                 blush=1.0, tilt=-0.05),
    "listen": _ax("neutral", bLy=10, bRy=16, ps=1.1, mc=0.4, tilt=-0.06),
    "lantern": _ax("happy", mo=0.3, ps=1.1),
}


# ---------------------------------------------------------------------------
# timing
# ---------------------------------------------------------------------------
def _wt(info, lid, k):
    """Scene time word k of line `lid` starts (fallback: even split)."""
    L = info.line(lid)
    ws = info._lip.get(lid, {}).get("word_starts", [])
    if k < len(ws):
        return L.start + ws[k]
    n = max(1, len(L.caption.split()))
    return L.start + L.dur * min(k, n - 1) / n


class _NS:
    pass


_TCACHE = {}


def _T(info):
    key = (info.id, info.dur, info.cues.get("end"), info.cues.get("party"))
    T = _TCACHE.get(key)
    if T is not None:
        return T
    T = _NS()
    c = info.cue
    T.L = {k: info.line(f"s12_l0{k}") for k in range(1, 8)}
    T.w = {}
    for k in range(1, 8):
        lid = f"s12_l0{k}"
        n = len(info.line(lid).caption.split())
        T.w[k] = [_wt(info, lid, i) for i in range(n)]
    T.rise = c("rise")
    T.up0 = T.rise + 0.12                    # spring up
    T.up1 = T.rise + 0.46
    T.hissy = T.w[1][0]
    T.new = T.w[1][1]
    T.wind = T.new - 0.16                    # wind-up
    T.flick = T.new                          # flick
    T.release = T.new + 0.06
    T.slap = max(T.w[1][2] + 0.04, T.release + 0.2)   # lands on "plan."
    T.we = T.w[1][3]
    T.whole = T.w[1][6]
    T.party_w = T.w[1][9]
    T.l2 = T.L[2]
    T.that = T.w[2][1]
    T.party = c("party")
    T.pop = T.party + 0.3                    # popper fires
    T.l3 = T.L[3]
    T.cheer = T.w[3][1]
    T.me = T.w[3][3]
    T.l4 = T.L[4]
    T.stats = T.w[4][3]
    T.lean = c("lean")
    T.chip_in = T.lean + 0.15
    T.l5 = T.L[5]
    T.l6 = T.L[6]
    T.malvo = T.w[6][0]
    T.l7 = T.L[7]
    T.kid2 = T.w[7][1]
    T.laugh = c("laugh")
    T.lol = T.l7.end                         # both start laughing
    T.chip_out = T.kid2 + 0.08
    T.end = info.dur
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
    return prev, cur, smoothstep(seg(t, start, start + max(tr, 1e-4)))


def keyed_v(t, keys, trans=0.2):
    """Numeric / tuple version of keyed()."""
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


def _bump(t, t0, dur, rise=0.05):
    if t < t0 or t > t0 + dur:
        return 0.0
    if t < t0 + rise:
        return smoothstep((t - t0) / rise)
    return 1.0 - smoothstep((t - t0 - rise) / max(1e-6, dur - rise))


def _pulses(t, times, dur=0.1, amt=0.6):
    out = None
    for t0 in times:
        if t0 <= t <= t0 + dur * 2:
            v = amt * math.sin(math.pi * (t - t0) / (dur * 2))
            out = v if out is None else max(out, v)
    return out


def _first(*vals):
    for v in vals:
        if v is not None:
            return v
    return None


def _col(c, a=1.0):
    return P.C(c, a)


def _fs(ctx, fc, sc=INK, w=5.0, a=1.0):
    P._fs(ctx, fc, sc, w, a)


def _f(ctx, fc, a=1.0):
    P._f(ctx, fc, a)


def _s(ctx, sc, w, a=1.0):
    P._s(ctx, sc, w, a)


# ---------------------------------------------------------------------------
# rig-following helpers (replicate the rigs' transforms so props can ride on them)
# ---------------------------------------------------------------------------
def _vstate(t, expr, arms, mouth, seed=1):
    p = V.resolve_expr(expr)
    _a, _b, a_shy, a_hdy, a_tilt = V.resolve_arms(arms, t)
    mo_lip = float(mouth[0]) if isinstance(mouth, (tuple, list)) else float(mouth)
    talk = clamp(mo_lip * 3)
    breath = math.sin(t * 2 * math.pi / 3.6 + seed * 1.3)
    shy = p["shy"] + a_shy - breath * 2.5
    head_dy = p["hy"] + a_hdy - breath * 3.0 + shy * 0.5 - mo_lip * 5
    head_rot = (p["tilt"] + a_tilt + noise1(t * 0.35, seed + 5) * 0.025
                + noise1(t * 2.2, seed + 6) * 0.03 * talk)
    return dict(p=p, shy=shy, head_dy=head_dy, head_rot=head_rot)


def _face_xf(c, x, y, s, lean, st):
    c.translate(x, y)
    c.scale(s, s)
    if lean:
        c.rotate(lean)
    c.translate(V.NECK[0], V.NECK[1] + st["head_dy"])
    c.rotate(st["head_rot"])
    c.translate(0, V.FACE_OFF)


def _villain_hand(x, y, s, t, arms, side="b", lean=0.0, reach=0.62):
    """World position + angle of a villain hand (palm/finger zone)."""
    A, B, _shy, _hdy, _tilt = V.resolve_arms(arms, t)
    h = A if side == "a" else B
    hs = V.HAND_SCALE * h["hs"]
    d = 34 + 60 * (reach - 0.5)
    px = h["wx"] + math.cos(h["ha"]) * d * hs
    py = h["wy"] + math.sin(h["ha"]) * d * hs
    if lean:
        cc, sn = math.cos(lean), math.sin(lean)
        px, py = px * cc - py * sn, px * sn + py * cc
    return x + px * s, y + py * s, h["ha"] + lean


def _snake_head_xf(ctx, x, y, s, t, expr, seed=5):
    """Apply Hissy's head transform (as draw_snake_head does) to ctx."""
    p = S.resolve_expr(expr)
    nod = p["nod"]
    nod_phase = math.sin(t * 2 * math.pi * 1.6)
    nod_dy = nod * (max(0.0, nod_phase) * 16 - 3)
    nod_rot = nod * 0.09 * max(0.0, nod_phase)
    bob = math.sin(t * 2 * math.pi * 0.45 + seed) * 2.5
    sway = noise1(t * 0.6, seed + 3) * 0.035
    wob = p["wob"] * math.sin(t * 2 * math.pi * 7) * 0.02
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.translate(0, p["hy"] + bob + nod_dy)
    ctx.rotate(p["tilt"] + sway + nod_rot + wob)
    sq = p["sq"]
    if sq != 1.0:
        ctx.scale(1 / math.sqrt(sq), sq)
    return p


# ---------------------------------------------------------------------------
# bespoke props (prop bible §6, same designs as the earlier scenes)
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


# THE ROBOT, cutout version (prop bible 6.1). Local origin = head centre.
R_CHROME, R_SH, R_DK, R_HI, R_SHOULDER = "#9aa3b5", "#6b7385", "#5d6474", "#c7cdd9", "#7d8496"
R_BEZEL, R_SLOT, R_VISOR, R_CORE = "#262a35", "#1a1d26", "#ff3b5c", "#ffd0d8"
R_CARD, R_CARD_DK = "#a5754a", "#7d5432"
R_HEAD = [(-210, -190), (210, -190), (165, 190), (-165, 190)]
R_SHP = [(-310, 385), (-306, 268), (-205, 232), (205, 232), (306, 268), (310, 385)]


def _robot_sil(ctx, dx=0.0, dy=0.0):
    rrect(ctx, -235 + dx, 330 + dy, 470, 640, 40)
    _round_poly(ctx, [(x + dx, y + dy) for x, y in R_SHP], 46)
    _round_poly(ctx, [(x + dx, y + dy) for x, y in R_HEAD], 60)
    for sx in (-1, 1):
        circle(ctx, sx * 202 + dx, -8 + dy, 46)
        circle(ctx, sx * 128 + dx, -250 + dy, 17)
        ctx.rectangle(sx * 128 - 12 + dx, -244 + dy, 24, 64)


def draw_robot_cutout(ctx):
    core.poly(ctx, [(150, 520), (330, 970), (150, 970)])          # kickstand
    _fs(ctx, R_CARD_DK)
    _robot_sil(ctx, 12, 12)
    core.fill(ctx, R_CARD)
    _robot_sil(ctx, 12, 12)
    core.stroke(ctx, INK, 5)
    rrect(ctx, -235, 330, 470, 640, 40)
    _fs(ctx, R_DK)
    ctx.move_to(0, 400)
    ctx.line_to(0, 900)
    core.stroke(ctx, INK, 4)
    for sx in (-1, 1):
        circle(ctx, sx * 150, 450, 11)
        _fs(ctx, R_SH, INK, 3)
    rrect(ctx, -86, 170, 172, 90, 14)
    _fs(ctx, R_SH)
    _round_poly(ctx, R_SHP, 46)
    _fs(ctx, R_SHOULDER)
    with saved(ctx, -205, 352, 1.0, -0.05) as c:
        text(c, "PROP", 0, 0, 62, (0.12, 0.1, 0.14, 0.72), "black")
    for sx in (-1, 1):
        rrect(ctx, sx * 128 - 12, -244, 24, 64, 6)
        _fs(ctx, R_SH, INK, 4)
        circle(ctx, sx * 128, -250, 17)
        _fs(ctx, R_CHROME, INK, 4)
    for sx in (-1, 1):
        circle(ctx, sx * 202, -8, 46)
        _fs(ctx, R_SHOULDER)
        circle(ctx, sx * 202, -8, 22)
        _fs(ctx, R_SH, INK, 3.5)
    _round_poly(ctx, R_HEAD, 60)
    core.fill(ctx, R_CHROME)
    ctx.save()
    _round_poly(ctx, R_HEAD, 60)
    ctx.clip()
    ctx.move_to(-260, 26)
    ctx.curve_to(-120, 44, 120, 44, 260, 26)
    ctx.line_to(260, 260)
    ctx.line_to(-260, 260)
    ctx.close_path()
    core.fill(ctx, R_SH)
    ctx.restore()
    _round_poly(ctx, R_HEAD, 60)
    core.stroke(ctx, INK, 5.5)
    rrect(ctx, -100, 62, 200, 78, 18)
    _fs(ctx, R_SH, INK, 4)
    for k in range(5):
        rrect(ctx, -64 + k * 32 - 9, 76, 18, 50, 9)
        core.fill(ctx, R_SLOT)
    _capsule(ctx, 0, -30, 344, 106)
    _fs(ctx, R_BEZEL, INK, 5)
    ctx.save()
    _capsule(ctx, 0, -30, 300, 70)
    ctx.clip()
    core.bg(ctx, R_VISOR)
    ctx.move_to(-118, -30)
    ctx.line_to(118, -30)
    core.stroke(ctx, R_CORE, 7)
    circle(ctx, 0, -30, 40)
    core.fill(ctx, "#c41f3d")
    circle(ctx, 0, -30, 12)
    core.fill(ctx, "white")
    ctx.restore()
    _capsule(ctx, 0, -30, 300, 70)
    core.stroke(ctx, INK, 4)
    ctx.save()
    _round_poly(ctx, R_HEAD, 60)
    ctx.clip()
    brow = [(-215, -124), (-24, -92), (24, -92), (215, -124), (215, -100), (26, -70),
            (-26, -70), (-215, -100)]
    _round_poly(ctx, brow, 8)
    _fs(ctx, R_SH, INK, 4.5)
    ctx.restore()
    # price tag
    ctx.move_to(128, -250)
    ctx.curve_to(190, -250, 230, -200, 252, -150)
    core.stroke(ctx, INK, 3)
    with saved(ctx, 262, -118, 1.0, 0.32) as c:
        _round_poly(c, [(-62, -30), (50, -30), (66, 0), (50, 30), (-62, 30)], 8)
        _fs(c, "#f6ecd6", INK, 4)
        text(c, "$19.99", -6, 11, 30, "ink", "round")


def draw_party_hat(c, x, y, k=1.0, rot=-0.25):
    """Striped party cone with a pom-pom (6.19). (x, y) = centre of its base."""
    with saved(c, x, y, k, rot):
        cone = [(-36, 0), (36, 0), (0, -96)]
        poly(c, cone)
        _f(c, "#ff8fb8")
        c.save()
        poly(c, cone)
        c.clip()
        for j, col in enumerate(("#ffd166", "#5ee7ff", "#ffd166", "#5ee7ff")):
            yy = -12 - j * 24
            poly(c, [(-60, yy), (60, yy - 26), (60, yy - 14), (-60, yy + 12)])
            _f(c, col)
        c.restore()
        poly(c, cone)
        _fs(c, None, INK, 5)
        circle(c, 0, -100, 14)
        _fs(c, "#ffffff", INK, 4)
        ellipse(c, 0, 2, 40, 7)
        _fs(c, "#ffd166", INK, 4)


def draw_balloon(c, x, y, s=1.0, rot=0.0, col=BALLOON, dk=BALLOON_DK):
    """Party balloon (6.4). (x, y) = centre; knot at (0, 58)*s."""
    with saved(c, x, y, s, rot):
        poly(c, [(0, 52), (-11, 68), (11, 68)])
        _fs(c, dk, INK, 4)
        ellipse(c, 0, 0, 45, 55)
        _fs(c, col, INK, 5)
        c.save()
        ellipse(c, 0, 0, 45, 55)
        c.clip()
        ellipse(c, 16, 18, 40, 48)
        _f(c, dk, 0.55)
        c.restore()
        ellipse(c, -16, -22, 11, 17, 0.45)
        c.set_source_rgba(1, 1, 1, 0.6)
        c.fill()
        circle(c, -8, -38, 4)
        c.fill()


def draw_string(c, x0, y0, x1, y1, t, curls=3.0, amp=10.0, phase=0.0, w=1.0):
    n = 28
    pts = []
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L, dx / L
    for i in range(n + 1):
        u = i / n
        ww = math.sin(u * curls * 2 * math.pi + phase + t * 2.2) * amp * math.sin(math.pi * min(1, u * 1.4))
        pts.append((x0 + dx * u + nx * ww, y0 + dy * u + ny * ww))
    for layer in (0, 1):
        smooth_path(c, pts)
        _s(c, INK if layer == 0 else "#f6f2ff", (6.5 if layer == 0 else 3.0) * w)


def draw_cake(c, x, y, s, t):
    """Two-tier pink birthday cake with one fizzing sparkler (6.4). bottom-centre."""
    with saved(c, x, y, s) as cc:
        ellipse(cc, 0, -4, 98, 13)
        _fs(cc, "#f4f1fb", INK, 4)
        rrect(cc, -80, -64, 160, 60, 12)
        _fs(cc, CAKE_C, INK, 5)
        cc.save()
        rrect(cc, -80, -64, 160, 60, 12)
        cc.clip()
        cc.rectangle(-90, -20, 180, 30)
        _f(cc, CAKE_DK, 0.7)
        cc.restore()
        cc.move_to(-80, -52)
        for j in range(8):
            xa = -80 + j * 20
            dl = 14 + 10 * ((j * 7) % 3)
            cc.line_to(xa + 4, -52)
            cc.curve_to(xa + 4, -52 + dl, xa + 16, -52 + dl, xa + 16, -52)
        cc.line_to(80, -52)
        cc.line_to(80, -64)
        cc.line_to(-80, -64)
        cc.close_path()
        _fs(cc, "#ffffff", INK, 3.5)
        rrect(cc, -54, -108, 108, 46, 10)
        _fs(cc, CAKE_TOP, INK, 5)
        cc.move_to(-54, -98)
        for j in range(5):
            xa = -54 + j * 21.6
            dl = 10 + 8 * ((j * 5) % 3)
            cc.line_to(xa + 4, -98)
            cc.curve_to(xa + 4, -98 + dl, xa + 17, -98 + dl, xa + 17, -98)
        cc.line_to(54, -98)
        cc.line_to(54, -108)
        cc.line_to(-54, -108)
        cc.close_path()
        _fs(cc, "#ffffff", INK, 3.5)
        for j, (sx, sy) in enumerate(((-30, -36), (10, -30), (44, -40), (-12, -84), (24, -88))):
            circle(cc, sx, sy, 4)
            _f(cc, ("#5ee7ff", "#ffd166", "#3ddc84", "#7b3fbf", "#5ee7ff")[j])
        cc.move_to(0, -108)
        cc.line_to(0, -164)
        _s(cc, INK, 10)
        cc.move_to(0, -110)
        cc.line_to(0, -162)
        _s(cc, "#b9c0d0", 4.5)
        f = 1 + 0.25 * math.sin(t * 37) + 0.15 * noise1(t * 18, 4)
        P._star4(cc, 0, -170, 20 * f, t * 5)
        P._fs(cc, "ai_accent", INK, 3)
        P._star4(cc, 0, -170, 9 * f, -t * 5)
        P._f(cc, "#fff3c4")
        P.sparkles(cc, 0, -172, 40, t, n=4, seed=17, color="ai_accent", size=0.45)


def draw_dragon_book(ctx, x, y, s, rot=0.0):
    """THE GENTLE DRAGON storybook (6.4): 150x190 at s=1, centred."""
    with saved(ctx, x, y, s, rot) as c:
        rrect(c, -72, -92, 154, 192, 12)
        c.set_source_rgba(0.03, 0.02, 0.06, 0.3)
        c.fill()
        rrect(c, -70, -91, 150, 186, 10)
        _fs(c, "#f3ead2", INK, 4)
        rrect(c, -75, -95, 150, 190, 12)
        _fs(c, BOOK, INK, 5)
        rrect(c, -75, -95, 24, 190, 10)
        _fs(c, BOOK_DK, INK, 4)
        rrect(c, -44, -84, 110, 168, 9)
        _s(c, "gold", 4)
        text(c, "THE GENTLE", 11, -58, 19, P.C("gold"), "title")
        text(c, "DRAGON", 11, -31, 29, P.C("gold"), "title")
        fx, fy = 11, 30
        for sx in (-1, 1):
            poly(c, [(fx + sx * 30, fy - 4), (fx + sx * 56, fy - 26), (fx + sx * 50, fy - 6),
                     (fx + sx * 58, fy + 4), (fx + sx * 34, fy + 14)])
            _fs(c, "#a6e88a", INK, 3.5)
        circle(c, fx, fy, 38)
        _fs(c, DRAGON, INK, 4)
        ellipse(c, fx, fy + 16, 22, 14)
        _f(c, "#c8f0a8")
        for sx in (-1, 1):
            c.move_to(fx + sx * 14 - 8, fy - 6)
            c.curve_to(fx + sx * 14 - 4, fy - 14, fx + sx * 14 + 4, fy - 14, fx + sx * 14 + 8, fy - 6)
            _s(c, INK, 3.5)
            ellipse(c, fx + sx * 24, fy + 6, 6, 4)
            _f(c, "#ff8fb0", 0.85)
        c.move_to(fx - 9, fy + 20)
        c.curve_to(fx - 4, fy + 26, fx + 4, fy + 26, fx + 9, fy + 20)
        _s(c, INK, 3.2)


def draw_popper(c, x, y, s, t, fired=False, squash=0.0, rot=0.0):
    """Confetti popper (6.4). (x, y) = bottom tip."""
    with saved(c, x, y, s, rot):
        if squash:
            c.scale(1 + 0.6 * squash, 1 - squash)
        if not fired:                                 # pull string + ring
            c.move_to(0, -2)
            c.curve_to(12, 10, -10, 18, 6, 30)
            _s(c, INK, 4)
            circle(c, 8, 38, 8)
            _s(c, INK, 4)
        cone = [(-31, -110), (31, -110), (5, -2), (-5, -2)]
        poly(c, cone)
        _f(c, "#ff7ab8")
        c.save()
        poly(c, cone)
        c.clip()
        for k in range(-4, 6):
            poly(c, [(-40, -20 - k * 24), (40, -60 - k * 24), (40, -46 - k * 24),
                     (-40, -6 - k * 24)])
        _f(c, "#ffd84a")
        c.restore()
        poly(c, cone)
        _fs(c, None, INK, 5)
        if not fired:
            pts = []
            for j in range(24):
                a = j / 24 * 2 * math.pi
                rr = 1.0 if j % 2 == 0 else 0.86
                pts.append((math.cos(a) * 36 * rr, -112 + math.sin(a) * 11 * rr))
            poly(c, pts)
            _fs(c, "gold", INK, 4)
        else:
            ellipse(c, 0, -110, 30, 9)
            _fs(c, "#3a2340", INK, 4)
            for k, col in enumerate(("ai_rim", "safe", "ai_accent")):
                c.move_to(-14 + k * 14, -112)
                c.curve_to(-20 + k * 14, -130, -6 + k * 14, -140, -12 + k * 14, -156)
                _s(c, INK, 8)
                c.move_to(-14 + k * 14, -112)
                c.curve_to(-20 + k * 14, -130, -6 + k * 14, -140, -12 + k * 14, -156)
                _s(c, col, 4)


def draw_headphones(c, x, y, s, rot=0.0):
    """Loose teal headphones (s03 gift). (x, y) = band centre."""
    with saved(c, x, y, s, rot):
        for col, w in ((INK, 17), ("bubble_ai", 9)):
            c.new_sub_path()
            c.arc(0, 22, 56, math.pi * 1.05, math.pi * 1.95)
            _s(c, col, w)
        for sx in (-1, 1):
            ellipse(c, sx * 50, 24, 19, 26)
            _fs(c, "bubble_ai", INK, 4.5)
            ellipse(c, sx * 53, 24, 9, 15)
            _f(c, "#0b6f6a")


def draw_rolled_scroll(ctx, x, y, s, rot=0.0):
    """THE CHEMIST story scroll, rolled and tied (as s04)."""
    with saved(ctx, x, y, s, rot) as c:
        rrect(c, -74, -22, 148, 44, 20)
        _fs(c, "parch", INK, 5)
        c.rectangle(-60, 6, 120, 10)
        _f(c, "parch_dk", 0.8)
        for sx in (-1, 1):
            ellipse(c, sx * 74, 0, 11, 22)
            _fs(c, "parch_dk", INK, 4)
            circle(c, sx * 92, 0, 11)
            _fs(c, "gold", INK, 4)
        c.rectangle(-9, -23, 18, 46)
        _fs(c, "cape_in", INK, 3.5)
        for sx in (-1, 1):
            ellipse(c, sx * 15, -27, 14, 9, -0.45 * sx)
            _fs(c, "danger", INK, 3.5)
        circle(c, 0, -25, 6)
        _fs(c, "cape_in", INK, 3)


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


def draw_gold_star(c, x, y, r, rot=0.0, lw=5.0):
    """FOR EFFORT gold star (6.4, as s09)."""
    _star5_path(c, x, y, r, rot)
    c.set_line_join(1)
    fill_stroke(c, GOLD, INK, lw)
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
    core.stroke(c, INK, lw)
    ellipse(c, x - r * 0.2, y - r * 0.3, r * 0.17, r * 0.1, -0.6)
    c.set_source_rgba(1, 1, 1, 0.85)
    c.fill()


LAPEL_S = 0.6                            # lapel gift-star scale (as s09 / s11)


def draw_lapel_star(c, st):
    """The FOR EFFORT gift on his lapel, drawn exactly like s09/s11 (star r 40 +
    'FOR EFFORT' tag, at LAPEL_S). `c` must be in villain-local coords (s=1)."""
    with saved(c, LAPEL[0], LAPEL[1] + st["shy"] * 0.5, LAPEL_S) as cc:
        with saved(cc, 0, 58, 1.0, -0.04) as c2:
            P.label_tag(c2, 0, 0, "FOR EFFORT", color="ai_accent", size=24)
        draw_gold_star(cc, 0, 0, 40, 0.0, 5.0)


def science_photo(ctx, x, y, w, h, rot):
    """Science-fair photo, small corkboard version (6.9, as s02)."""
    with saved(ctx, x, y, 1.0, rot) as c:
        rrect(c, -w / 2 + 5, -h / 2 + 6, w, h, 3)
        core.fill(c, (0, 0, 0, 0.3))
        rrect(c, -w / 2, -h / 2, w, h, 3)
        _fs(c, "#f3efe6", INK, 3)
        px0, py0, pw, ph = -w / 2 + 7, -h / 2 + 7, w - 14, h - 24
        c.save()
        c.rectangle(px0, py0, pw, ph)
        c.clip()
        core.bg(c, "#b9b0c2")
        c.rectangle(px0, py0 + ph * 0.52, pw, ph)
        core.fill(c, "#a59c90")
        kx, ky = px0 + pw * 0.33, py0 + ph * 0.36
        core.poly(c, [(kx - 11, ky + 6), (kx + 11, ky + 6), (kx + 14, ky + 24), (kx - 14, ky + 24)])
        core.fill(c, "#6f5a7c")
        circle(c, kx, ky, 8)
        _fs(c, "#e6cdb6", "#4a3a44", 1.5)
        circle(c, kx + 3, ky - 1, 2.6)
        core.stroke(c, "#c9a84f", 1.4)
        rx_, ry_ = px0 + pw * 0.62, py0 + ph * 0.36
        c.rectangle(rx_ - 7, ry_ - 2, 14, 16)
        _fs(c, "#9aa0a8", "#4a4650", 1.5)
        circle(c, rx_, ry_ - 7, 4)
        _fs(c, "#f2e6a0", "#4a4650", 1.2)
        c.rectangle(px0 + pw * 0.14, py0 + ph * 0.52, pw * 0.66, 5)
        _fs(c, "#8a7f74", "#4a4650", 1.2)
        circle(c, px0 + pw * 0.47, py0 + ph * 0.52 + 9, 3.2)
        core.fill(c, "#7f9bc4")
        for row in range(3):
            yy = py0 + ph * (0.7 + row * 0.12)
            for k in range(6):
                xx = px0 + 9 + k * (pw - 18) / 5 + (row % 2) * 4
                c.rectangle(xx - 4, yy - 7, 8, 6)
                c.rectangle(xx - 4, yy, 8, 2)
                core.fill(c, "#7d7a84")
        c.restore()
        c.move_to(-w / 2 + 14, h / 2 - 9)
        c.line_to(-w / 2 + 60, h / 2 - 10)
        core.stroke(c, "#8a8494", 2)
        circle(c, 0, -h / 2 + 6, 7)
        _fs(c, "danger", INK, 2.5)


def cape_flare(ctx, k):
    """Extra cape 'wings' behind Malvo (villain-local coords, as s02)."""
    if k <= 0.01:
        return
    for sx in (-1, 1):
        tip = (sx * (330 + 190 * k), -330 - 80 * k)
        mid = (sx * (360 + 150 * k), -60)
        bot = (sx * (330 + 120 * k), 150)
        pts = [(sx * 120, -350), tip, (sx * (300 + 120 * k), -250), mid,
               (sx * (340 + 110 * k), 40), bot, (sx * 200, 150)]
        smooth_path(ctx, pts, closed=True, tension=0.35)
        _fs(ctx, "cape", INK, 6)
        inner = [(sx * 140, -330), (sx * (310 + 160 * k), -300 - 60 * k),
                 (sx * (290 + 110 * k), -230), (sx * (330 + 130 * k), -60),
                 (sx * (310 + 100 * k), 40), (sx * (300 + 100 * k), 140), (sx * 210, 140)]
        smooth_path(ctx, inner, closed=True, tension=0.35)
        _fs(ctx, "cape_in", INK, 4)


def draw_sticky(ctx, x, y, s, rot, sx=1.0, sy=1.0):
    """Yellow 'PARTY' sticky note. (x, y) = centre."""
    w, h = STICKY_WH
    with saved(ctx, x, y, s, rot) as c:
        if sx != 1.0 or sy != 1.0:
            c.scale(sx, sy)
        # same design as s13's corkboard close-up: square yellow note, darker
        # glue strip, "PARTY" in ink (comic)
        c.rectangle(-w / 2 + 4, -h / 2 + 5, w, h)
        _f(c, INK, 0.3)
        c.rectangle(-w / 2, -h / 2, w, h)
        _f(c, STICKY_C)
        c.rectangle(-w / 2, -h / 2, w, 11)
        _f(c, STICKY_DK)
        c.rectangle(-w / 2, -h / 2, w, h)
        _s(c, INK, 3.0)
        text(c, "PARTY", 0, 19, 37, "ink", "comic")


# ---------------------------------------------------------------------------
# people (prop bible 6.3)
# ---------------------------------------------------------------------------
_PEAR = [(0, -136), (-26, -131), (-40, -100), (-48, -52), (-40, -16), (0, -10),
         (40, -16), (48, -52), (40, -100), (26, -131)]


def _hair(c, style, hy, col):
    if style == 0:                                   # curl on top
        c.move_to(-14, hy - 44)
        c.curve_to(-8, hy - 66, 18, hy - 64, 14, hy - 50)
        _s(c, INK, 10)
        c.move_to(-14, hy - 44)
        c.curve_to(-8, hy - 66, 18, hy - 64, 14, hy - 50)
        _s(c, col, 5)
    elif style == 1:                                 # bob cap
        c.new_sub_path()
        c.arc(0, hy - 2, 49, math.pi * 1.02, math.pi * 1.98)
        c.curve_to(30, hy - 30, -30, hy - 30, -48, hy - 6)
        c.close_path()
        _fs(c, col, INK, 4.5)
    elif style == 2:                                 # two buns
        for sx in (-1, 1):
            circle(c, sx * 38, hy - 38, 17)
            _fs(c, col, INK, 4)
        c.new_sub_path()
        c.arc(0, hy - 2, 48, math.pi * 1.08, math.pi * 1.92)
        c.curve_to(20, hy - 34, -20, hy - 34, -45, hy - 18)
        c.close_path()
        _fs(c, col, INK, 4)
    elif style == 3:                                 # flat-top
        rrect(c, -40, hy - 58, 80, 30, 10)
        _fs(c, col, INK, 4.5)


def draw_person_front(c, x, y, s, t, i, arms="cheer", look=(0.0, 0.0), mouth="smile",
                      bounce=6.0, eyes="happy", energy=1.0):
    """Bouncing townsperson facing camera. (x, y) = between the feet."""
    skin = SKINS[i % len(SKINS)]
    shirt = SHIRTS[(i * 3 + 1) % len(SHIRTS)]
    hair = HAIRS[(i * 5 + 2) % len(HAIRS)]
    ph = hash01(i, 61) * 6.28
    b = abs(math.sin(t * 2 * math.pi * 1.0 + ph))      # 2 hops / s
    dy = -b * bounce * energy
    sq = 1.0 + (0.05 * (1 - b) - 0.02) * energy
    with saved(c, x, y + dy * s, s) as cc:
        cc.scale(1 / math.sqrt(sq), sq)
        for sx in (-1, 1):                          # little shoes
            ellipse(cc, sx * 20, -6, 18, 9)
            _fs(cc, "#3a2f4a", INK, 4)
        smooth_path(cc, _PEAR, closed=True)
        _fs(cc, shirt, INK, 5)
        cc.save()
        smooth_path(cc, _PEAR, closed=True)
        cc.clip()
        ellipse(cc, 36, -60, 26, 70)
        _f(cc, INK, 0.12)
        cc.restore()
        # arms
        for k, sx in enumerate((-1, 1)):
            sh = (sx * 30, -112)
            if arms == "cheer":
                w = math.sin(t * 2 * math.pi * 1.6 + ph + k * 2.2) * energy
                hand = (sx * (66 + 10 * w), -196 - 12 * w)
                el = (sx * 58, -150)
            elif arms == "clap":
                u = max(0.0, math.sin(t * 2 * math.pi * 2.3 + ph)) * energy
                hand = (sx * (8 + 22 * u), -98)
                el = (sx * 50, -88)
            else:                                   # at sides
                hand = (sx * 56, -48)
                el = (sx * 50, -80)
            cc.move_to(*sh)
            cc.curve_to(el[0], el[1], el[0], el[1], hand[0], hand[1])
            _s(cc, INK, 17)
            cc.move_to(*sh)
            cc.curve_to(el[0], el[1], el[0], el[1], hand[0], hand[1])
            _s(cc, shirt, 9)
            circle(cc, hand[0], hand[1], 10)
            _fs(cc, skin, INK, 3.5)
        hy = -178
        for sx in (-1, 1):
            circle(cc, sx * 45, hy + 2, 11)
            _fs(cc, skin, INK, 4)
        circle(cc, 0, hy, 46)
        _fs(cc, skin, INK, 5)
        _hair(cc, i % 4, hy, hair)
        ex, ey = look[0] * 5, look[1] * 4
        for sx in (-1, 1):
            if eyes == "happy":
                cc.move_to(sx * 17 - 8 + ex, hy - 2 + ey)
                cc.curve_to(sx * 17 - 4 + ex, hy - 11 + ey, sx * 17 + 4 + ex, hy - 11 + ey,
                            sx * 17 + 8 + ex, hy - 2 + ey)
                _s(cc, INK, 4.5)
            else:
                ellipse(cc, sx * 16 + ex, hy - 4 + ey, 5.5, 7)
                _f(cc, INK)
            ellipse(cc, sx * 28, hy + 12, 9, 5)
            _f(cc, "#ff7a9a", 0.5)
        if mouth == "o":
            ellipse(cc, ex * 0.5, hy + 20, 7, 8)
            _fs(cc, "#7a2a3a", INK, 3.5)
        else:
            cc.move_to(-15, hy + 15)
            cc.curve_to(-8, hy + 32, 8, hy + 32, 15, hy + 15)
            cc.close_path()
            _fs(cc, "#7a2a3a", INK, 4)


def draw_person_back(c, x, y, s, t, i, dark=0.0, clap_amp=1.0, energy=1.0):
    """Seated audience member seen from behind, clapping over their head.
    (x, y) = seat top centre. Chair back is drawn separately (in front)."""
    skin = SKINS[(i + 1) % len(SKINS)]
    shirt = SHIRTS[(i * 2 + 3) % len(SHIRTS)]
    hair = HAIRS[(i * 3) % len(HAIRS)]
    if dark > 0:
        shirt = core.mixc(shirt, "#2a1838", dark)
        skin = core.mixc(skin, "#2a1838", dark * 0.85)
        hair = core.mixc(hair, "#1c1026", dark * 0.8)
    ph = hash01(i, 71) * 6.28
    u = max(0.0, math.sin(t * 2 * math.pi * 2.4 + ph)) * (0.25 + 0.75 * energy)  # clap open
    bob = -abs(math.sin(t * 2 * math.pi * 1.2 + ph)) * 3 * energy
    with saved(c, x, y + bob * s, s) as cc:
        body = [(0, -128), (-30, -124), (-50, -96), (-56, -50), (-50, -6), (0, 0),
                (50, -6), (56, -50), (50, -96), (30, -124)]
        smooth_path(cc, body, closed=True)
        _fs(cc, shirt, INK, 5)
        hand_y = -236 + 8 * u
        for sx in (-1, 1):
            sh = (sx * 36, -108)
            hx = sx * (6 + 26 * u * clap_amp)
            cc.move_to(*sh)
            cc.curve_to(sx * 66, -150, sx * 40, -200, hx, hand_y)
            _s(cc, INK, 17)
            cc.move_to(*sh)
            cc.curve_to(sx * 66, -150, sx * 40, -200, hx, hand_y)
            _s(cc, shirt, 9)
            ellipse(cc, hx, hand_y, 9, 12)
            _fs(cc, skin, INK, 3.5)
        hy = -168
        for sx in (-1, 1):
            circle(cc, sx * 44, hy + 4, 10)
            _fs(cc, skin, INK, 4)
        rrect(cc, -16, hy + 26, 32, 22, 6)
        _fs(cc, skin, INK, 3.5)
        circle(cc, 0, hy, 44)
        _fs(cc, hair, INK, 5)
        cc.move_to(-20, hy - 26)
        cc.curve_to(-6, hy - 34, 8, hy - 30, 18, hy - 20)
        _s(cc, "#ffffff", 4, 0.18)


def draw_chair_back(c, x, y, s, dark=0.0):
    """Grey folding chair seen from behind (the science-fair chairs, now full)."""
    col = core.mixc(CHAIR, "#2a1838", dark)
    dk = core.mixc(CHAIR_DK, "#1c1026", dark)
    with saved(c, x, y, s) as cc:
        for sx in (-1, 1):
            cc.rectangle(sx * 44 - 5, -60, 10, 120)
            _fs(cc, dk, INK, 3.5)
        rrect(cc, -56, -64, 112, 40, 8)
        _fs(cc, col, INK, 4.5)
        cc.move_to(-44, -34)
        cc.line_to(44, -34)
        _s(cc, dk, 3)


def draw_neighbor(c, x, y, s, t, lean=0.0, squash=1.0):
    """THE NEIGHBOR (6.3, as s03) dancing in his teal headphones, eyes closed."""
    NB_SKIN, NB_SKIN_SH = "#c68a5e", "#a8714a"
    NB_PJ, NB_PJ_ST = "#a9c9f2", "#7ea4da"
    NB_SLIP = "#ff9ec4"
    with saved(c, x, y, s) as c:
        c.rotate(lean)
        c.scale(1 / math.sqrt(squash), squash)
        for sx in (-1, 1):
            for k in range(5):
                circle(c, sx * 26 + (k - 2) * 9, -18 + abs(k - 2) * 2, 8)
            _f(c, NB_SLIP)
            ellipse(c, sx * 26, -9, 29, 13)
            _fs(c, NB_SLIP, INK, 4)
        smooth_path(c, _PEAR, closed=True)
        _f(c, NB_PJ)
        c.save()
        smooth_path(c, _PEAR, closed=True)
        c.clip()
        for k in range(-3, 4):
            c.rectangle(k * 18 - 4, -140, 8, 140)
        _f(c, NB_PJ_ST)
        ellipse(c, 36, -60, 26, 70)
        _f(c, "#5d7fb8", 0.35)
        c.restore()
        smooth_path(c, _PEAR, closed=True)
        _fs(c, None, INK, 5)
        poly(c, [(-18, -132), (0, -112), (18, -132)], closed=False)
        _s(c, INK, 4)
        hy = -178
        for sx in (-1, 1):
            circle(c, sx * 45, hy + 2, 11)
            _fs(c, NB_SKIN, INK, 4)
        circle(c, 0, hy, 46)
        _fs(c, NB_SKIN, INK, 5)
        ellipse(c, 16, hy + 12, 26, 26)
        _f(c, NB_SKIN_SH, 0.35)
        c.move_to(-14, hy - 44)
        c.curve_to(-8, hy - 66, 18, hy - 64, 14, hy - 50)
        c.curve_to(10, hy - 42, 0, hy - 46, 4, hy - 54)
        _s(c, INK, 6)
        for sx in (-1, 1):
            c.move_to(sx * 17 - 8, hy - 2)
            c.curve_to(sx * 17 - 4, hy - 10, sx * 17 + 4, hy - 10, sx * 17 + 8, hy - 2)
            _s(c, INK, 4.5)
            ellipse(c, sx * 28, hy + 12, 9, 5)
            _f(c, "#ff7a9a", 0.5)
        c.move_to(-16, hy + 16)
        c.curve_to(-8, hy + 32, 8, hy + 32, 16, hy + 16)
        c.close_path()
        _fs(c, "#7a2a3a", INK, 4)
        # arms up, grooving (tiny trumpet in one hand)
        sw = math.sin(t * 2 * math.pi * 1.6)
        for sx in (-1, 1):
            hand = (sx * (62 + 8 * sw * sx), -186 + 10 * sw * sx)
            c.move_to(sx * 30, -112)
            c.curve_to(sx * 64, -130, sx * 70, -150, hand[0], hand[1])
            _s(c, INK, 19)
            c.move_to(sx * 30, -112)
            c.curve_to(sx * 64, -130, sx * 70, -150, hand[0], hand[1])
            _s(c, NB_PJ, 11)
            circle(c, hand[0], hand[1], 9)
            _fs(c, NB_SKIN, INK, 3.5)
            if sx == 1:
                with saved(c, hand[0] + 4, hand[1] - 6, 1.0, -0.9 + 0.2 * sw):
                    c.move_to(-4, 10)
                    c.line_to(0, -24)
                    _s(c, INK, 11)
                    c.move_to(-4, 10)
                    c.line_to(0, -24)
                    _s(c, "gold", 5)
                    poly(c, [(-8, -24), (8, -24), (14, -40), (-14, -40)])
                    _fs(c, "gold", INK, 3)
        # headphones
        c.new_sub_path()
        c.arc(0, hy, 56, math.pi * 1.05, math.pi * 1.95)
        _s(c, INK, 17)
        c.new_sub_path()
        c.arc(0, hy, 56, math.pi * 1.05, math.pi * 1.95)
        _s(c, "bubble_ai", 9)
        for sx in (-1, 1):
            ellipse(c, sx * 50, hy + 2, 19, 26)
            _fs(c, "bubble_ai", INK, 4.5)
            ellipse(c, sx * 53, hy + 2, 9, 15)
            _f(c, "#0b6f6a")


def _note(c, x, y, s, a=1.0, rot=0.0):
    """Little eighth note (music from the headphones)."""
    with saved(c, x, y, s, rot):
        for layer in (0, 1):
            c.move_to(9, 0)
            c.line_to(9, -38)
            c.curve_to(16, -30, 24, -26, 22, -14)
            c.set_source_rgba(*(hexc(INK, a) if layer == 0 else (1, 0.82, 0.4, a)))
            c.set_line_width(12 if layer == 0 else 6)
            c.stroke()
        ellipse(c, 0, 0, 11, 8, -0.4)
        c.set_source_rgba(1, 0.82, 0.4, a)
        c.fill_preserve()
        c.set_source_rgba(*hexc(INK, a))
        c.set_line_width(3)
        c.stroke()


# ---------------------------------------------------------------------------
# Hissy accessories (6.6): granny glasses + knitted shawl (as s06)
# ---------------------------------------------------------------------------
def _glasses(ctx):
    """Round granny glasses in Hissy's head-local coords (eyes at (+-40,-18))."""
    c = ctx
    r = 29
    for sx in (-1, 1):
        c.move_to(sx * (40 + r), -22)
        c.line_to(sx * 92, -34)
        _s(c, INK, 6)
        c.move_to(sx * (40 + r), -22)
        c.line_to(sx * 92, -34)
        _s(c, "gold", 3)
    for sx in (-1, 1):
        circle(c, sx * 40, -18, r)
        c.set_source_rgba(0.82, 0.92, 1.0, 0.28)
        c.fill_preserve()
        _s(c, INK, 7.5)
        circle(c, sx * 40, -18, r)
        _s(c, "gold", 4)
        c.new_sub_path()
        c.arc(sx * 40, -18, r - 9, math.pi * 1.1, math.pi * 1.45)
        _s(c, "white", 3.5, 0.75)
    c.move_to(-11, -24)
    c.curve_to(-6, -34, 6, -34, 11, -24)
    _s(c, INK, 7)
    c.move_to(-11, -24)
    c.curve_to(-6, -34, 6, -34, 11, -24)
    _s(c, "gold", 3.5)


def _shawl(ctx, top_y):
    """Lavender knitted shawl over Hissy's neck (snake-local coords)."""
    ctx.move_to(-46, top_y + 4)
    ctx.curve_to(-16, top_y - 6, 16, top_y - 6, 46, top_y + 4)
    ctx.line_to(104, top_y + 116)
    ctx.curve_to(40, top_y + 132, -40, top_y + 132, -104, top_y + 116)
    ctx.close_path()
    _fs(ctx, SHAWL, INK, 5)
    ctx.move_to(-46, top_y + 4)
    ctx.curve_to(-24, top_y + 30, -4, top_y + 60, 8, top_y + 124)
    _s(ctx, SHAWL_DK, 4)
    for r in range(4):
        yy = top_y + 22 + r * 22
        half = 44 + (yy - top_y) * 0.5
        n = int(half * 2 / 16)
        for i in range(n + 1):
            xx = -half + i * (2 * half / max(1, n)) + (8 if r % 2 else 0)
            if abs(xx) > half - 6:
                continue
            ctx.move_to(xx - 4, yy - 3)
            ctx.line_to(xx, yy + 3)
            ctx.line_to(xx + 4, yy - 3)
    _s(ctx, SHAWL_DK, 2.6)
    circle(ctx, 0, top_y + 20, 10)
    _fs(ctx, "gold", INK, 3.5)
    circle(ctx, 0, top_y + 20, 4.5)
    _f(ctx, "danger")


def draw_hissy_reader(ctx, t, st):
    """Hissy on the bench: coiled, rising like a storyteller, shawl + glasses.
    st = dict(expr, look, mouth, tongue, blink)."""
    x, y, s = HISSY_B
    cx, cy = (COIL_B[0] - x) / s, (COIL_B[1] - y) / s          # coil centre, head-local
    sway = math.sin(t * 2 * math.pi * 0.45 + 5) * 4
    pts = [(cx + 100 * math.cos(a), cy + 26 * math.sin(a))
           for a in [math.pi * (0.1 + 0.22 * i) for i in range(9)]]
    pts += [(cx + 60, cy - 46), (cx + 10 + sway * 0.3, cy - 110), (8 + sway, 110), (2, 40)]
    with saved(ctx, x, y, s) as c:
        Pp = S.coil_points(pts, 5)
        n = len(Pp)
        Wd = [lerp(12, 54, smoothstep(min(1.0, i / (n * 0.4)))) for i in range(n)]
        S.draw_tube(c, Pp, Wd, cap0=True, cap1=False, belly_side=-1, spot_phase=7)
    draw_snake_head(ctx, x, y, s, t, st["expr"], st["look"], st["mouth"], st["tongue"],
                    st.get("blink"), seed=5, neck=False)
    with saved(ctx, x + sway * s * 0.5, y, s) as c:
        _shawl(c, 62)
    ctx.save()
    p = _snake_head_xf(ctx, x, y, s, t, st["expr"])
    _glasses(ctx)
    if p["fp"] > 0.02:                               # facepalm: tail back over the glasses
        S._tail_over_eyes(ctx, p["fp"], None, t)
    ctx.restore()


# ---------------------------------------------------------------------------
# THE TOWN SQUARE (6.18) static layer
# ---------------------------------------------------------------------------
HOUSES = [  # x0, x1, top, gable, wall, roof
    (-40, 196, 560, True, "#a9dcc9", "#4f7f8a"),
    (186, 404, 610, False, "#f6b8c8", "#a04a72"),
    (394, 640, 540, True, "#b8c2f4", "#5a4a9a"),
    (630, 852, 596, False, "#f9dc8c", "#b0663a"),
    (842, 1120, 520, True, "#f6b48c", "#8e4a5a"),
]
HOUSE_BASE = 990.0
DUSK = "#6a3d8f"


def _lights_curve(x0, y0, x1, y1, sag):
    def at(u):
        return (lerp(x0, x1, u), lerp(y0, y1, u) + sag * 4 * u * (1 - u))
    return at


def _string_lights(c, at, n, seed):
    pts = [at(i / 40) for i in range(41)]
    poly(c, pts, closed=False)
    _s(c, INK, 4)
    cols = ["#ffd166", "#ff8fb8", "#5ee7ff", "#a7e8a0"]
    for i in range(n):
        u = (i + 0.5) / n
        bx, by = at(u)
        col = cols[(i + seed) % len(cols)]
        circle(c, bx, by + 12, 22)
        _f(c, col, 0.22)
        c.move_to(bx, by)
        c.line_to(bx, by + 6)
        _s(c, INK, 3)
        ellipse(c, bx, by + 13, 8, 10)
        _fs(c, col, INK, 3)
        circle(c, bx - 2, by + 10, 2.5)
        _f(c, "#ffffff", 0.8)


def _house(c, x0, x1, top, gable, wall, roof, idx):
    w = x1 - x0
    wall_c = core.mixc(wall, DUSK, 0.18)
    roof_c = core.mixc(roof, DUSK, 0.15)
    shade = core.mixc(wall, DUSK, 0.42)
    c.rectangle(x0, top, w, HOUSE_BASE - top + 8)
    _fs(c, wall_c, INK, 5)
    c.rectangle(x1 - w * 0.16, top + 4, w * 0.16 - 3, HOUSE_BASE - top)
    _f(c, shade)
    if gable:
        peak = top - 92
        poly(c, [(x0 - 18, top + 6), ((x0 + x1) / 2, peak), (x1 + 18, top + 6)])
        _fs(c, roof_c, INK, 5)
        circle(c, (x0 + x1) / 2, top - 36, 18)
        _fs(c, "#ffe08a", INK, 4)
    else:
        rrect(c, x0 - 12, top - 26, w + 24, 34, 6)
        _fs(c, roof_c, INK, 5)
    # windows (lit)
    cols = 2 if w < 260 else 3
    for r in range(2):
        for k in range(cols):
            wx = x0 + w * (k + 0.5) / cols - 28
            wy = top + 60 + r * 150
            if wy + 80 > HOUSE_BASE - 110:
                continue
            rrect(c, wx, wy, 56, 76, 6)
            lit = hash01(idx * 7 + r * 3 + k, 33) < 0.8
            _fs(c, "#ffe08a" if lit else core.mixc(wall, "#2a1838", 0.55), INK, 4)
            if lit:
                rrect(c, wx + 8, wy + 8, 40, 30, 4)
                _f(c, "#fff3c0", 0.85)
            c.move_to(wx + 28, wy + 2)
            c.line_to(wx + 28, wy + 74)
            c.move_to(wx + 2, wy + 40)
            c.line_to(wx + 54, wy + 40)
            _s(c, INK, 3)
            rrect(c, wx - 6, wy + 74, 68, 10, 3)
            _fs(c, roof_c, INK, 3)
    # door
    dx = x0 + w * (0.3 if idx % 2 else 0.62) - 34
    rrect(c, dx, HOUSE_BASE - 128, 68, 132, 10)
    _fs(c, roof_c, INK, 4.5)
    circle(c, dx + 54, HOUSE_BASE - 62, 5)
    _fs(c, "gold", INK, 2.5)


def _town_static(c):
    # dusk sky (static gradient)
    g = cairo.LinearGradient(0, 0, 0, HOUSE_BASE)
    for off, col in ((0.0, "#4a2a78"), (0.45, "#9a4f92"), (0.8, "#f08a84"), (1.0, "#ff9e7a")):
        g.add_color_stop_rgba(off, *hexc(col))
    c.rectangle(-40, -40, W + 80, HOUSE_BASE + 60)
    c.set_source(g)
    c.fill()
    radial_glow(c, 330, 980, 520, "#ffd28a", 0.3)
    for i in range(14):                                   # first stars
        sx, sy = 40 + hash01(i, 5) * 1000, 30 + hash01(i, 6) * 330
        circle(c, sx, sy, 1.6 + 1.6 * hash01(i, 7))
        _f(c, "#fff4d8", 0.55 + 0.3 * hash01(i, 8))
    # far rooftops
    c.move_to(-20, 760)
    for k in range(12):
        xa = -20 + k * 100
        c.line_to(xa + 20, 700 + 40 * hash01(k, 21))
        c.line_to(xa + 70, 700 + 40 * hash01(k, 21))
        c.line_to(xa + 100, 760 + 30 * hash01(k, 22))
    c.line_to(1100, HOUSE_BASE)
    c.line_to(-20, HOUSE_BASE)
    c.close_path()
    _f(c, "#8a5a98")
    # top string lights + the banner hanging from them
    top = _lights_curve(-30, 92, 1110, 92, 80)
    _string_lights(c, top, 18, 0)
    for bx in (162.0, 828.0):
        _, ly = top((bx + 30) / 1140)
        c.move_to(bx, ly)
        c.line_to(bx + (8 if bx < 500 else -8), 194)
        _s(c, INK, 4)
    bx0, bx1, by0, by1 = 150.0, 840.0, 186.0, 278.0
    pts = [(bx0 - 26, by0), (bx1 + 26, by0), (bx1, (by0 + by1) / 2), (bx1 + 26, by1),
           (bx0 - 26, by1), (bx0, (by0 + by1) / 2)]
    poly(c, [(x + 6, y + 8) for x, y in pts])
    _f(c, INK, 0.3)
    poly(c, pts)
    _fs(c, "#d23a4a", INK, 5)
    for xx in (bx0 + 10, bx1 - 10):
        c.move_to(xx, by0 + 4)
        c.line_to(xx, by1 - 4)
        _s(c, "#a12536", 4)
    c.rectangle(bx0 + 14, by1 - 16, bx1 - bx0 - 28, 8)
    _f(c, "#a12536")
    text(c, "SNEAKWORTH'S BLOCK PARTY", (bx0 + bx1) / 2, by0 + 68, 54, "#ffe9a8", "comic",
         outline=INK, outline_w=9)
    # houses
    for i, hs in enumerate(HOUSES):
        _house(c, *hs, i)
    # lower string lights across the house fronts
    low = _lights_curve(-30, 430, 1110, 410, 92)
    _string_lights(c, low, 16, 2)
    # plaza: kerb + cobbles
    c.rectangle(-40, HOUSE_BASE, W + 80, 28)
    _fs(c, "#9b7488", INK, 4)
    g2 = cairo.LinearGradient(0, HOUSE_BASE + 28, 0, H)
    g2.add_color_stop_rgba(0.0, *hexc("#b98a96"))
    g2.add_color_stop_rgba(0.45, *hexc("#94677f"))
    g2.add_color_stop_rgba(1.0, *hexc("#5e3d5c"))
    c.rectangle(-40, HOUSE_BASE + 28, W + 80, H - HOUSE_BASE)
    c.set_source(g2)
    c.fill()
    y = HOUSE_BASE + 50
    row = 0
    while y < H + 40:                                 # soft, sparse cobbles (cheap to encode)
        hgt = 16 + (y - HOUSE_BASE) * 0.07
        wdt = 46 + (y - HOUSE_BASE) * 0.16
        x = -20 + (row % 2) * wdt * 0.5
        while x < W + 40:
            ellipse(c, x, y, wdt * 0.4, hgt * 0.32)
            x += wdt
        _f(c, "#5e3d5c", 0.13)
        y += hgt * 1.1
        row += 1
    # the cardboard robot cutout, leaning at the far left, in a party hat
    rx, ry, rs, rl = ROBOT
    with saved(c, rx, ry, rs, rl) as cc:
        cc.translate(0, -970)
        draw_robot_cutout(cc)
        draw_party_hat(cc, 30, -232, 2.6, 0.3)
    # bench
    b0, b1, by = BENCH
    for lx in (b0 + 34, b1 - 34):
        c.rectangle(lx - 6, by - 64, 12, 70)          # backrest posts
        _fs(c, "#5a3826", INK, 3.5)
    rrect(c, b0 + 6, by - 72, b1 - b0 - 12, 20, 5)     # backrest
    _fs(c, "#8a5a3b", INK, 4)
    ellipse(c, (b0 + b1) / 2, by + 88, (b1 - b0) / 2 + 10, 10)
    _f(c, "#4a2c48", 0.35)
    for lx in (b0 + 30, b1 - 30):
        c.rectangle(lx - 7, by + 10, 14, 76)
        _fs(c, "#5a3826", INK, 4)
    rrect(c, b0, by - 6, b1 - b0, 20, 5)               # seat plank
    _fs(c, "#8a5a3b", INK, 4.5)


def _robot_world(px, py):
    rx, ry, rs, rl = ROBOT
    lx, ly = px * rs, (py - 970) * rs
    cc, sn = math.cos(rl), math.sin(rl)
    return rx + lx * cc - ly * sn, ry + lx * sn + ly * cc


# ---------------------------------------------------------------------------
# camera for shot B
# ---------------------------------------------------------------------------
def _cam(t, T):
    """-> (z, ox, oy): screen = FOCUS + (world - FOCUS) * z + (ox, oy)."""
    k1 = ease_in_out(seg(t, T.l3.start, T.l3.start + 0.6))
    z = lerp(1.0, Z1, k1)
    ox = lerp(0.0, TGT[0] - FOCUS[0], k1)
    oy = lerp(0.0, TGT[1] - FOCUS[1], k1)
    return z, ox, oy, k1


def _to_screen(cam, x, y):
    z, ox, oy, _ = cam
    return FOCUS[0] + (x - FOCUS[0]) * z + ox, FOCUS[1] + (y - FOCUS[1]) * z + oy


# ---------------------------------------------------------------------------
# SHOT A: the lair, morning
# ---------------------------------------------------------------------------
def _malvo_a(t, T, info):
    L1 = T.L[1]
    ex = keyed(t, [
        (0.0, "s12_real"),
        (T.rise + 0.04, "excited", 0.14),
        (T.wind, "s12_eager", 0.12),
        (T.slap + 0.05, "excited", 0.15),
        (T.party_w, "excited"),
        (T.l2.start + 0.15, "hopeful", 0.25),
        (T.that + 0.3, "happy", 0.3),
    ])
    look = keyed_v(t, [
        (0.0, (0.0, 0.7)),                            # still admiring the gift pile
        (T.rise + 0.05, (0.3, -0.2)),
        (T.hissy - 0.04, (-0.95, 0.4)),               # "Hissy!"
        (T.wind - 0.05, (0.75, -0.9)),                # eyes on the board
        (T.slap + 0.2, (0.05, 0.0)),                  # to camera: "New plan."
        (T.we, (-0.85, -0.35)),                       # out the window: the town
        (T.party_w, (0.15, -0.1)),
        (T.l2.start - 0.05, (0.95, -0.3)),            # to the AI
    ], 0.12)
    arms = keyed(t, [
        (0.0, "rest"),
        (T.up0, "rest"),
        (T.wind, "s12_wind", 0.18),
        (T.flick, "s12_throw", 0.08),
        (T.slap + 0.35, "point", 0.25),
        (T.we + 0.05, "present", 0.3),
        (T.party_w - 0.1, "fist", 0.14),
        (T.party_w + 0.75, "rest", 0.35),
        (T.l2.start + 0.1, "beg", 0.3),
    ])
    blink = _first(_pulses(t, [T.slap - 0.02], 0.06, 0.8),
                   0.3 if t < T.rise + 0.04 else None)
    # body: dip, spring up with overshoot, hop on "party!"
    dip = 9.0 * _bump(t, T.rise + 0.01, T.up0 - T.rise + 0.02, 0.06)
    up = ease_out_back(seg(t, T.up0, T.up1), 2.2)
    y = lerp(MY_SIT, MY_UP, up) + dip
    y -= 18.0 * math.sin(math.pi * seg(t, T.party_w - 0.04, T.party_w + 0.3))
    lean = (-0.035 * _bump(t, T.up0, 0.35, 0.12) + 0.03 * _bump(t, T.flick, 0.3, 0.06)
            - 0.025 * _bump(t, T.we + 0.05, 0.6, 0.25))
    flare = ease_out(seg(t, T.up0, T.up0 + 0.2)) * (1 - smoothstep(seg(t, T.up0 + 0.3, T.up0 + 0.95)))
    return dict(expr=ex, look=look, arms=arms, blink=blink, y=y, lean=lean, flare=flare,
                mouth=info.mouth("villain", t))


def _hissy_a(t, T):
    ex = keyed(t, [
        (0.0, "happy"),
        (T.hissy + 0.05, "shocked", 0.08),            # perks up at his name
        (T.hissy + 0.32, "idle", 0.2),
        (T.we + 0.1, "nod", 0.2),                     # agrees: party!
        (T.l2.start + 0.2, "happy", 0.3),
    ])
    look = keyed_v(t, [
        (0.0, (0.6, -0.3)),
        (T.hissy + 0.05, (0.9, -0.5)),
        (T.release, (0.7, -1.0)),                     # tracks the sticky
        (T.slap + 0.3, (0.9, -0.5)),
        (T.l2.start, (1.0, -0.6)),
    ], 0.12)
    tongue = True if T.slap + 0.4 <= t < T.slap + 0.7 else None
    return {"expr": ex, "look": look, "tongue": tongue}


def _sticky_flight(t, T, hand):
    """-> (x, y, s, rot, sx, sy) of the sticky, or None before it appears."""
    if t < T.wind - 0.05:
        return None
    if t < T.release:
        hx, hy, ha = hand
        return (hx + math.cos(ha) * 6, hy + math.sin(ha) * 6, 0.55, ha + 1.2, 1.0, 1.0)
    x1, y1, r1 = STICKY
    if t < T.slap:
        u = seg(t, T.release, T.slap)
        x0, y0, _ = T.rel_pos
        cxp, cyp = 470.0, 360.0
        x = (1 - u) ** 2 * x0 + 2 * (1 - u) * u * cxp + u * u * x1
        y = (1 - u) ** 2 * y0 + 2 * (1 - u) * u * cyp + u * u * y1
        return (x, y, lerp(0.55, 1.08, u), lerp(1.4, r1 - 2 * math.pi, ease_out(u)), 1.0, 1.0)
    k = seg(t, T.slap, T.slap + 0.28)
    sq = 0.22 * math.exp(-k * 5) * math.cos(k * 14)
    return (x1, y1, 1.0, r1, 1 + sq, 1 - sq)


def _ai_a(t, T, info):
    ex = keyed(t, [
        (0.0, "warm"),
        (T.release - 0.04, "alert", 0.08),            # whoosh past its face
        (T.slap + 0.12, "amused", 0.25),
        (T.party_w, "happy", 0.25),
        (T.l2.start, "happy"),
    ])
    look = keyed_v(t, [
        (0.0, (-1.0, 0.35)),
        (T.release - 0.02, (-0.6, 0.6)),
        (T.release + 0.1, (-0.5, -0.6)),
        (T.slap - 0.05, (0.2, -1.0)),                 # up at the board
        (T.slap + 0.55, (-1.0, 0.3)),                 # back to Malvo
    ], 0.08)
    hands = keyed(t, [
        (0.0, "idle"),
        (T.release - 0.03, "stop_both", 0.06),        # flinch
        (T.slap + 0.25, "idle", 0.3),
        (T.l2.start - 0.12, "thumbs_up", 0.2),
        (T.l2.end + 0.1, "thumbs_up"),
    ])
    nod = 0.55 * _bump(t, T.that - 0.02, 0.45, 0.08)
    blink = _pulses(t, [T.release - 0.02], 0.05, 1.0)
    return dict(expr=ex, look=look, hands=hands, nod=nod, blink=blink,
                mouth=info.mouth("ai", t))


def _dawn_window(ctx):
    """The next morning: dawn sky in the lair window (replaces the night glass:
    sun rising over the hills, pink clouds, no moon), then the window frame and
    the candle (snuffed out) redrawn on top, as lair_bg layers them."""
    ctx.save()
    P._lair_glass_path(ctx)
    ctx.clip()
    g = cairo.LinearGradient(0, 200, 0, 900)
    for off, col in ((0.0, "#7d8fd6"), (0.42, "#c9a3d8"), (0.72, "#ffb59a"), (1.0, "#ffd88a")):
        g.add_color_stop_rgba(off, *hexc(col))
    ctx.rectangle(60, 150, 330, 770)
    ctx.set_source(g)
    ctx.fill()
    radial_glow(ctx, 226, 792, 230, "#fff1b8", 0.55)
    circle(ctx, 226, 796, 64)                          # the sun, half over the hills
    _f(ctx, "#fff4c6")
    circle(ctx, 226, 796, 50)
    _f(ctx, "#ffe08a")
    for (cx, cy, s) in ((150, 560, 0.9), (330, 610, 0.72), (190, 690, 0.95)):
        for (dx, dy, r) in ((-60, 10, 34), (-20, -10, 46), (30, -2, 40), (70, 14, 28),
                            (0, 20, 36)):
            circle(ctx, cx + dx * s, cy + dy * s, r * s)
        _f(ctx, "#ffc4c4", 0.85)
    hill = "#8c5d8f"
    ctx.move_to(40, 820)
    ctx.curve_to(150, 760, 200, 770, 250, 800)
    ctx.curve_to(300, 770, 340, 760, 410, 790)
    ctx.line_to(410, 920)
    ctx.line_to(40, 920)
    ctx.close_path()
    _f(ctx, hill)
    ctx.rectangle(300, 700, 24, 100)                    # the spooky tower, now just a tower
    poly(ctx, [(294, 702), (312, 666), (330, 702)])
    _f(ctx, hill)
    ctx.restore()
    P._lair_window_frame(ctx)
    P._lair_candle_static(ctx)
    cx, cy = P._CANDLE[0] + 1, P._CANDLE[1] - 96          # a thin wisp from the snuffed wick
    ctx.move_to(cx, cy)
    ctx.curve_to(cx + 10, cy - 14, cx - 8, cy - 26, cx + 4, cy - 42)
    _s(ctx, "#e8e2f0", 3.5, 0.55)


def shot_lair(ctx, t, info, T):
    P.lair_bg(ctx, t, rain=False, candle=False)       # morning: candle's out
    P._cached_layer(ctx, "s12_dawn2", _dawn_window, rect=P._WIN_RECT)
    science_photo(ctx, *PHOTO)

    m = _malvo_a(t, T, info)
    hs = _hissy_a(t, T)
    # sticky: hand position (release position cached for the flight)
    hand = _villain_hand(MX, m["y"], MS, t, m["arms"], "b", m["lean"], reach=0.55)
    if not hasattr(T, "rel_pos"):
        rel_hand = _villain_hand(MX, MY_UP, MS, T.release, ("s12_wind", "s12_throw", 1.0),
                                 "b", 0.0, reach=0.55)
        T.rel_pos = rel_hand
    stick = _sticky_flight(t, T, hand)
    landed = t >= T.slap

    if landed:                                        # on the board (behind the AI)
        x, y, s, r, sx, sy = stick
        draw_sticky(ctx, x, y, s, r, sx, sy)
        k = seg(t, T.slap, T.slap + 0.22)
        if k < 1:                                     # slap ticks
            for i in range(6):
                a = i / 6 * 2 * math.pi + 0.3
                r0, r1 = 80 + 30 * k, 96 + 46 * k
                ctx.move_to(x + math.cos(a) * r0, y + math.sin(a) * r0 * 0.7)
                ctx.line_to(x + math.cos(a) * r1, y + math.sin(a) * r1 * 0.7)
            _s(ctx, "#fff3c4", 6, 1 - k)

    if m["flare"] > 0.01:
        with saved(ctx, MX, m["y"], MS, m["lean"]) as c:
            cape_flare(c, m["flare"])
    snake = dict(hs)
    draw_villain(ctx, MX, m["y"], MS, t, expr=m["expr"], look=m["look"], mouth=m["mouth"],
                 arms=m["arms"], lean=m["lean"], blink=m["blink"], snake=snake)
    # FOR EFFORT star on his lapel (worn since s09; s11 ends with it on)
    with saved(ctx, MX, m["y"], MS, m["lean"]) as c:
        draw_lapel_star(c, _vstate(t, m["expr"], m["arms"], m["mouth"]))
    if stick is not None and t < T.release:
        x, y, s, r, sx, sy = stick
        draw_sticky(ctx, x, y, s, r)

    # cool light from the AI on Malvo's face side
    radial_glow(ctx, MX + 150, m["y"] - 520 * MS, 380, "ai_rim", 0.12)

    # desk + last night's gift pile (where s11 left it), computer at the edge
    P.desk(ctx, *DESK, lamp=False, emblem=False)
    P.computer(ctx, *COMP, view="side", facing=-1, t=t)
    draw_string(ctx, 622 + math.sin(t * 1.7) * 4, 1037 + math.sin(t * 2 * math.pi * 0.55) * 7,
                576, 1226, t, amp=8)
    draw_popper(ctx, 200, 1240, 0.88, t, False, 0.0, -0.3)
    draw_rolled_scroll(ctx, 280, 1212, 0.95, -0.12)
    draw_headphones(ctx, 528, 1206, 1.12, 0.12)
    draw_cake(ctx, 628, 1242, 0.85, t)
    draw_dragon_book(ctx, 404, 1192, 0.62, 0.05)
    draw_balloon(ctx, 622 + math.sin(t * 1.7) * 4, 985 + math.sin(t * 2 * math.pi * 0.55) * 7,
                 0.9, 0.12 + math.sin(t * 1.3) * 0.06)

    # the AI hologram
    a = _ai_a(t, T, info)
    anc = draw_ai(ctx, AX, AY, AS, t, expr=a["expr"], look=a["look"], mouth=a["mouth"],
                  hands=a["hands"], blink=a["blink"], nod=a["nod"], aura=0.6)
    if t >= T.that - 0.05:
        k = smoothstep(seg(t, T.that - 0.05, T.that + 0.2)) * (1 - smoothstep(seg(t, T.party - 0.4, T.party)))
        if k > 0.01:
            with saved(ctx, alpha_=k) as c:
                P.sparkles(c, AX, AY - 20, 175, t, n=5, seed=12, size=0.9)
    if T.party_w + 0.02 <= t:
        P.emote(ctx, "sparkle", MX + 175, m["y"] - 690 * MS, 0.8, t, T.party_w + 0.05,
                t_out=T.l2.start + 0.3)

    # in flight: in front of everything (whizzes past the AI)
    if stick is not None and T.release <= t < T.slap:
        x, y, s, r, sx, sy = stick
        u = seg(t, T.release, T.slap)
        x0, y0, _ = T.rel_pos
        trail = []
        for j in range(8):                            # whoosh trail behind it
            uu = max(0.0, u - 0.035 * j)
            trail.append(((1 - uu) ** 2 * x0 + 2 * (1 - uu) * uu * 470 + uu * uu * STICKY[0],
                          (1 - uu) ** 2 * y0 + 2 * (1 - uu) * uu * 360 + uu * uu * STICKY[1]))
        for off, a in ((-14, 0.75), (14, 0.75)):
            pts = []
            for j, (px, py) in enumerate(trail):
                if j + 1 < len(trail):
                    dx, dy = trail[j][0] - trail[j + 1][0], trail[j][1] - trail[j + 1][1]
                else:
                    dx, dy = trail[j - 1][0] - trail[j][0], trail[j - 1][1] - trail[j][1]
                L = math.hypot(dx, dy) or 1.0
                pts.append((px - dy / L * off * (1 - j / 8), py + dx / L * off * (1 - j / 8)))
            smooth_path(ctx, pts[1:])
            _s(ctx, "#fff3c4", 5, a)
        draw_sticky(ctx, x, y, s, r)


# ---------------------------------------------------------------------------
# SHOT B: the town square
# ---------------------------------------------------------------------------
def _malvo_b(t, T, info):
    P0 = T.party
    L3 = T.l3
    ex = keyed(t, [
        (0.0, "excited"),
        (P0 + 0.32, "s12_startle", 0.06),             # the popper!
        (P0 + 0.85, "excited", 0.25),
        (L3.start - 0.05, "s12_moved", 0.3),
        (T.w[3][2] - 0.08, "s12_me", 0.25),           # "for ME?"
        (L3.end + 0.3, "s12_moved", 0.35),
        (T.lean + 0.12, "sneaky", 0.18),
        (T.l5.start + 0.08, "smug", 0.1),             # brow waggle
        (T.l5.start + 0.23, "sneaky", 0.1),
        (T.l5.start + 0.38, "smug", 0.1),
        (T.l5.start + 0.53, "sneaky", 0.1),
        (T.malvo + 0.28, "s12_caught", 0.08),         # caught
        (T.l7.start - 0.06, "sheepish", 0.2),
        (T.kid2 - 0.05, "happy", 0.25),
        (T.lol, "s12_laugh", 0.2),
    ])
    look = keyed_v(t, [
        (0.0, (-0.75, 0.15)),
        (P0 + 0.32, (0.55, 0.0)),
        (P0 + 0.9, (0.75, 0.2)),
        (P0 + 1.45, (-0.6, 0.35)),
        (L3.start, (0.0, 0.25)),
        (T.cheer, (-0.7, 0.3)),
        (T.cheer + 0.4, (0.6, 0.3)),
        (T.w[3][2] - 0.08, (0.0, 0.05)),              # to camera
        (L3.end + 0.15, (-0.2, 0.55)),                # sniff, eyes down
        (T.l4.start - 0.05, (0.85, -0.75)),           # up at the AI
        (T.lean, (-0.95, 0.05)),                      # paranoid glance left
        (T.lean + 0.22, (0.95, 0.05)),                # ... right
        (T.lean + 0.44, (0.9, -0.7)),                 # at the AI
        (T.malvo + 0.05, (0.8, -0.65)),
        (T.l7.start, (0.7, -0.6)),
        (T.lol, (0.3, -0.2)),
    ], 0.1)
    arms = keyed(t, [
        (0.0, "shrug"),
        (L3.start - 0.1, "s12_heart", 0.3),
        (T.lean + 0.05, "steeple", 0.25),
        (T.l7.start - 0.08, "shrug", 0.15),
        (T.lol + 0.15, "s12_heart", 0.35),
    ])
    lean = 0.08 * ease_in_out(seg(t, T.lean + 0.35, T.lean + 0.7))
    lean *= 1 - ease_in_out(seg(t, T.malvo + 0.4, T.malvo + 0.8))
    blink = _first(_pulses(t, [P0 + 0.3, L3.end + 0.12, L3.end + 0.3], 0.06, 0.9),
                   slow_blink(t, T.l4.start + 0.35))
    if T.malvo + 0.28 <= t < T.l7.start - 0.06:      # caught: frozen, wide-eyed
        blink = 0.0
    mouth = info.mouth("villain", t)
    y = VY
    if t >= T.lol:
        k = smoothstep(seg(t, T.lol, T.lol + 0.15))
        ph = (t - T.lol) * 2 * math.pi * 4.0
        mouth = (k * 0.5 * (0.55 + 0.45 * math.sin(ph)), 0.35)
        y -= k * 4.0 * abs(math.sin(ph * 0.5))
    if t < T.l3.start:                                # little bounces at the party
        y -= 5.0 * abs(math.sin((t - P0) * 2 * math.pi * 1.0)) * smoothstep(seg(t, P0 + 0.9, P0 + 1.2))
        y -= 12.0 * _bump(t, P0 + 0.3, 0.4, 0.06)       # startle hop
    tear = smoothstep(seg(t, T.me + 0.05, T.me + 0.45)) * (1 - smoothstep(seg(t, T.lean, T.lean + 0.3)))
    fog = smoothstep(seg(t, T.cheer, T.me + 0.3)) * (1 - smoothstep(seg(t, T.lean, T.lean + 0.4)))
    return dict(expr=ex, look=look, arms=arms, lean=lean, blink=blink, mouth=mouth, y=y,
                tear=tear, fog=fog)


def _hissy_b(t, T):
    ex = keyed(t, [
        (0.0, "happy"),
        (T.l3.start + 0.3, "idle", 0.25),
        (T.me, "happy", 0.3),                         # aww
        (T.l4.start + 0.2, "nod", 0.2),
        (T.l4.end + 0.15, "happy", 0.3),
        (T.lean + 0.2, "side_eye", 0.2),              # he knows that face
        (T.malvo + 0.08, "facepalm", 0.2),
        (T.kid2 + 0.05, "happy", 0.3),
    ])
    look = keyed_v(t, [
        (0.0, (-0.3, 0.9)),                           # reading the book
        (T.l3.start + 0.3, (1.0, -0.2)),              # at Malvo
        (T.lean + 0.2, (1.0, 0.0)),
        (T.kid2 + 0.05, (0.8, -0.2)),
    ], 0.15)
    mouth = 0.0
    if t < T.l3.start - 0.1:                          # 'reading' aloud (no dialogue here)
        mouth = 0.2 * max(0.0, math.sin((t - T.party) * 2 * math.pi * 2.6))
    tongue = True if T.lean + 0.62 <= t < T.lean + 0.9 else (False if t < T.l3.start else None)
    return dict(expr=ex, look=look, mouth=mouth, tongue=tongue)


def _ai_b(t, T, info):
    L4 = T.l4
    ex = keyed(t, [
        (0.0, AIX["lantern"]),
        (T.l3.start + 0.2, "warm", 0.3),
        (L4.start, "warm"),
        (T.stats + 0.04, "wink", 0.08),
        (T.stats + 0.6, "happy", 0.25),
        (T.lean + 0.4, AIX["listen"], 0.3),
        (T.l6.start, "unimpressed", 0.0),             # instantly 😒
        (T.kid2 + 0.08, "amused", 0.3),
        (T.lol - 0.25, AIX["laugh"], 0.25),
    ])
    look = keyed_v(t, [
        (0.0, (-0.6, 0.7)),
        (T.l3.start, (-0.85, 0.6)),
        (T.stats + 0.6, (-0.8, 0.55)),
        (T.l6.start, (-1.0, 0.4)),                    # locked on Malvo
        (T.lol - 0.25, (-0.4, 0.2)),
    ], 0.12)
    if T.l6.start <= t < T.kid2 + 0.08:
        look = (-1.0, 0.4)
    hands = keyed(t, [
        (0.0, "present_both"),
        (T.party + 1.3, "idle", 0.4),
        (L4.start, "present_l", 0.25),
        (T.stats + 0.5, "idle", 0.35),
        (T.lol - 0.2, "idle"),
    ])
    blink = _first(slow_blink(t, T.l3.end + 0.05), slow_blink(t, T.l6.start + 0.62))
    if T.l6.start <= t < T.l6.start + 0.6 or (T.l6.start + 0.94 < t < T.kid2):
        blink = 0.0 if blink is None else blink       # deadpan: no stray auto-blinks
    mouth = info.mouth("ai", t)
    nod = 0.0
    if t >= T.lol - 0.25:
        k = smoothstep(seg(t, T.lol - 0.25, T.lol))
        ph = (t - T.lol) * 2 * math.pi * 4.0
        mouth = (k * 0.35 * (0.5 + 0.5 * math.sin(ph + 1.0)), 0.3)
        nod = 0.35 * k
    nod = max(nod, 0.45 * _bump(t, L4.start + 0.05, 0.5, 0.1))
    return dict(expr=ex, look=look, hands=hands, blink=blink, mouth=mouth, nod=nod)


def _kids(ctx, t, T):
    # three kids on the bench, rapt (look at Hissy / the book)
    for k, (kx, kind) in enumerate(((50.0, 2), (102.0, 0), (152.0, 1))):
        ky = BENCH[2] - 2
        lk = (1.0, -0.7)
        draw_person_front(ctx, kx, ky, 0.48, t, 11 + k * 3, arms="side", look=lk,
                          mouth="o" if k != 1 else "smile", bounce=3.0, eyes="dots")


def _confetti_burst(ctx, t, t0, origin, n=28, dur=1.2):
    if t < t0 or t > t0 + dur:
        return
    tt = t - t0
    fade = 1 - smoothstep(seg(tt, dur - 0.3, dur))
    for i in range(n):
        ang = -math.pi / 2 + 0.3 + (hash01(i, 71) - 0.5) * 1.9
        sp = 560 + 460 * hash01(i, 72)
        drag = 1 - math.exp(-tt * 2.2)
        x = origin[0] + math.cos(ang) * sp * drag / 2.2
        y = origin[1] + math.sin(ang) * sp * drag / 2.2 + 420 * tt * tt
        rot = hash01(i, 73) * 6 + tt * (6 + 8 * hash01(i, 74))
        col = _col(CONF_COLS[i % len(CONF_COLS)])
        with saved(ctx, x, y, 1.0, rot):
            rrect(ctx, -11, -6, 22, 12, 3)
            ctx.set_source_rgba(col[0], col[1], col[2], fade)
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexc(INK, 0.9 * fade))
            ctx.set_line_width(2.5)
            ctx.stroke()


def _confetti_drift(ctx, t, t0, n=12):
    """~12 bits drifting down over the final hold (screen space)."""
    if t < t0:
        return
    tt = t - t0
    for i in range(n):
        x0 = 80 + (i + 0.5) / n * 820 + (hash01(i, 81) - 0.5) * 60
        start = hash01(i, 82) * 0.6
        if tt < start:
            continue
        u = tt - start
        y = -30 + u * (300 + 120 * hash01(i, 83)) + hash01(i, 84) * 140
        x = x0 + math.sin(u * 3.2 + i) * 28
        rot = math.sin(u * 4 + i * 1.7) * 1.2
        sqx = abs(math.cos(u * 5 + i))
        col = _col(CONF_COLS[i % len(CONF_COLS)])
        with saved(ctx, x, y, (0.35 + 0.65 * sqx, 1.0), rot):
            rrect(ctx, -12, -7, 24, 14, 3)
            ctx.set_source_rgba(*col)
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexc(INK, 0.9))
            ctx.set_line_width(2.5)
            ctx.stroke()


def _villain_overlays(ctx, t, m):
    """FOR EFFORT star on the lapel, monocle fog, the happy tear."""
    st = _vstate(t, m["expr"], m["arms"], m["mouth"])
    # lapel star (rides the torso)
    with saved(ctx, VX, m["y"], VS, m["lean"]) as c:
        draw_lapel_star(c, st)
    if m["fog"] <= 0.01 and m["tear"] <= 0.01:
        return
    p = st["p"]
    lx = clamp(m["look"][0] + p["ex"], -1.2, 1.2)
    turn = lx * 9.0
    ctx.save()
    _face_xf(ctx, VX, m["y"], VS, m["lean"], st)
    if m["fog"] > 0.01:
        cx2, cy2 = V.EYE_DX + turn, V.EYE_DY + p["by2"] * 0.08
        r = 52 * p["es"] ** 0.5 + 2 - 7
        circle(ctx, cx2, cy2, r)
        ctx.set_source_rgba(1, 1, 1, 0.4 * m["fog"])
        ctx.fill()
        for j in range(2):
            ctx.move_to(cx2 - r * 0.5 + j * 18, cy2 + r * 0.25 - j * 12)
            ctx.line_to(cx2 - r * 0.1 + j * 18, cy2 - r * 0.15 - j * 12)
        _s(ctx, "#ffffff", 5, 0.5 * m["fog"])
    if m["tear"] > 0.01:
        es = p["es"]
        cx, cy = -V.EYE_DX + turn, V.EYE_DY
        y0 = cy + V.EYE_RY * es * 0.8
        Lt = 96 * m["tear"]
        pts = []
        for i in range(8):
            u = i / 7
            pts.append((cx - (16 + 10 * u) + 3 * math.sin(u * 5 + t * 8) * u, y0 + Lt * u))
        for w, col in ((10, INK), (5.5, TEAR)):
            smooth_path(ctx, pts)
            _s(ctx, col, w)
        exx, eyy = pts[-1]
        rr = 5.5 + 2.0 * m["tear"]
        for r2, col in ((rr + 2.2, INK), (rr, TEAR)):
            ellipse(ctx, exx, eyy + 2, r2 * 0.86, r2)
            _f(ctx, col)
        circle(ctx, exx - 2, eyy, 1.8)
        ctx.set_source_rgba(1, 1, 1, 0.9)
        ctx.fill()
    ctx.restore()


def _table(ctx, t, T):
    x0, x1, top, bot = TABLE
    ctx.move_to(x0 - 4, top + 6)
    ctx.line_to(x1 + 4, top + 6)
    ctx.line_to(x1 + 12, bot - 12)
    n = 10
    for k in range(n + 1):                            # scalloped hem
        xa = x1 + 12 - (x1 - x0 + 24) * k / n
        ctx.line_to(xa, bot - 12 + (10 if k % 2 else 0))
    ctx.close_path()
    _fs(ctx, "#13a8a0", INK, 5)
    ctx.save()
    ctx.move_to(x0 - 4, top + 6)
    ctx.line_to(x1 + 4, top + 6)
    ctx.line_to(x1 + 12, bot)
    ctx.line_to(x0 - 12, bot)
    ctx.close_path()
    ctx.clip()
    ctx.rectangle(x1 - 64, top, 80, bot - top)        # one shadow tone
    _f(ctx, "#0b7f79", 0.6)
    for r in range(4):
        for k in range(8):
            cx = x0 + 26 + k * 50 + (25 if r % 2 else 0)
            circle(ctx, cx, top + 34 + r * 50, 7)
    _f(ctx, "#ffffff", 0.7)
    ctx.move_to(x0 - 12, bot - 16)
    ctx.line_to(x1 + 12, bot - 16)
    _s(ctx, "#ffffff", 8, 0.85)
    ctx.restore()
    rrect(ctx, x0 - 10, top - 10, x1 - x0 + 20, 20, 6)  # table top edge
    _fs(ctx, "#f4efe6", INK, 5)
    ellipse(ctx, (x0 + x1) / 2, bot + 4, (x1 - x0) / 2 + 20, 9)
    _f(ctx, "#3a2240", 0.3)


def _crowd(t, T):
    """Background crowd clock + energy. The crowd animates on twos while it
    cheers and settles (on threes, smaller moves) while Malvo and the AI talk,
    then livens up again for the laugh. Keeps the bitrate in check."""
    calm = smoothstep(seg(t, T.l3.start + 0.5, T.l3.start + 1.4))
    calm *= 1 - smoothstep(seg(t, T.l7.start + 0.3, T.l7.start + 0.8))
    energy = 1.0 - 0.6 * calm
    fps = 8.0 if calm > 0.5 else 12.0
    return math.floor(t * fps) / fps, energy


def shot_party(ctx, t, info, T):
    cam = _cam(t, T)
    tc, en = _crowd(t, T)
    z, ox, oy, k1 = cam
    m = _malvo_b(t, T, info)
    ctx.save()
    ctx.translate(FOCUS[0] + ox, FOCUS[1] + oy)
    ctx.scale(z, z)
    ctx.translate(-FOCUS[0], -FOCUS[1])

    P._cached_layer(ctx, "s12_town", _town_static, rect=(-40, -40, W + 80, H + 80),
                    opaque=True)
    # robot's balloon (string from its shoulder plate)
    bx, by, bs = ROBOT_BAL
    sway = math.sin(tc * 1.3) * 0.06
    kx, ky = _robot_world(250, 300)
    draw_string(ctx, bx + math.sin(sway) * 60 * bs, by + 58 * bs, kx, ky, tc, amp=7, phase=1.0)
    draw_balloon(ctx, bx, by, bs, sway, YBAL, YBAL_DK)

    # standing townsfolk behind the table (right)
    draw_person_front(ctx, 712, 1004, 0.6, tc, 2, arms="cheer", energy=en)
    if k1 < 0.5:                                      # (off-screen once pushed in)
        draw_person_front(ctx, 804, 990, 0.56, tc, 5, arms="clap", energy=en)
        draw_person_front(ctx, 892, 1008, 0.6, tc, 8, arms="cheer", energy=en)

    # Malvo behind the table
    draw_villain(ctx, VX, m["y"], VS, t, expr=m["expr"], look=m["look"], mouth=m["mouth"],
                 arms=m["arms"], lean=m["lean"], blink=m["blink"])
    _villain_overlays(ctx, t, m)

    # the red balloon tied to the table
    bx, by, bs = BALLOON_W
    sw = math.sin(tc * 1.1 + 0.5) * 0.05
    draw_string(ctx, bx + math.sin(sw) * 50 * bs, by + 58 * bs, BAL_KNOT[0], BAL_KNOT[1], tc,
                amp=8)
    draw_balloon(ctx, bx, by, bs, sw)

    _table(ctx, t, T)
    draw_cake(ctx, *CAKE, t)
    draw_rolled_scroll(ctx, *SCROLL, -0.1)
    fired = t >= T.pop
    sq = 0.3 * _bump(t, T.pop, 0.25, 0.04)
    rec = -0.3 * _bump(t, T.pop, 0.3, 0.04)
    draw_popper(ctx, POPPER[0], POPPER[1], POPPER[2], t, fired, sq, 0.18 + rec)

    # Hissy + kids on the bench (left)
    _kids(ctx, tc, T)
    draw_hissy_reader(ctx, t, _hissy_b(t, T))
    draw_dragon_book(ctx, *BOOK_B, -0.06)

    # audience: back row then front row (each person, then the chair in front)
    rowA = [(338.0, 0), (436.0, 1), (534.0, 2), (632.0, 3)]
    for x, i in rowA:
        draw_person_back(ctx, x, ROW_A, 0.64, tc, i, dark=0.22, energy=en)
    for x, i in rowA:
        draw_chair_back(ctx, x, ROW_A, 0.64, dark=0.22)
    rowB = [(272.0, 4), (396.0, 5), (520.0, 6), (644.0, 7), (768.0, 8)]
    for x, i in rowB:
        draw_person_back(ctx, x, ROW_B, 0.8, tc, i, dark=0.55, clap_amp=0.8, energy=en)
    for x, i in rowB:
        draw_chair_back(ctx, x, ROW_B, 0.8, dark=0.55)

    # the neighbor dancing (front right) + notes from his headphones
    nx, ny, ns = NEIGH
    beat = tc * 2 * math.pi * 1.6
    draw_neighbor(ctx, nx, ny - 8 * en * abs(math.sin(beat)), ns, tc,
                  lean=0.14 * en * math.sin(beat), squash=1.0 + 0.05 * en * math.cos(beat * 2))
    for j in range(2):
        u = ((tc * 0.7) + j * 0.5) % 1.0
        _note(ctx, nx + 40 + j * 30 + u * 40, ny - 230 - u * 120, 0.85,
              a=math.sin(u * math.pi), rot=0.2 * math.sin(tc * 3 + j))

    # the popper's confetti
    _confetti_burst(ctx, t, T.pop, (POPPER[0] + 12, POPPER[1] - 62))
    ctx.restore()

    # --- the AI lantern (screen space during the push-in) --------------------------
    a = _ai_b(t, T, info)
    wx, wy = _to_screen(cam, AI_W[0], AI_W[1])
    ws = AI_W[2] * z
    lean_k = ease_in_out(seg(t, T.lean + 0.3, T.lean + 0.8)) * (1 - ease_in_out(seg(t, T.malvo + 0.5, T.malvo + 0.9)))
    fx_, fy_, fs_ = AI_S[0], AI_S[1] - 6 * lean_k, AI_S[2]
    ax = lerp(wx, fx_, k1)
    ay = lerp(wy, fy_, k1)
    as_ = lerp(ws, fs_, k1)
    radial_glow(ctx, ax, ay, 230 * as_ / 0.4, "ai_accent", 0.13)
    anc = draw_ai(ctx, ax, ay, as_, t, expr=a["expr"], look=a["look"], mouth=a["mouth"],
                  hands=a["hands"], blink=a["blink"], nod=a["nod"], aura=0.0, glow=1.1)
    if t >= T.stats:
        ex_, ey_ = anc["eyeL"]
        P.emote(ctx, "sparkle", ex_ - 52 * as_ / 0.4, ey_ - 40 * as_ / 0.4, 0.62, t,
                T.stats + 0.04, t_out=T.stats + 0.75)

    # --- 'NICE TRIES: 10?' ghost chip ----------------------------------------------
    _chip(ctx, t, T)
    _confetti_drift(ctx, t, T.lol - 0.1)


def _chip(ctx, t, T):
    t_in = T.chip_in
    if t < t_in or t > T.chip_out + 0.25:
        return
    # blinks back in: on, off, on
    on = not (t_in + 0.08 <= t < t_in + 0.16)
    if not on:
        return
    k = ease_out_back(seg(t, t_in, t_in + 0.25)) if t < t_in + 0.08 else \
        ease_out_back(seg(t, t_in + 0.16, t_in + 0.4))
    if t >= T.chip_out:
        k *= 1 - ease_in(seg(t, T.chip_out, T.chip_out + 0.22))
        k *= 1 + 0.25 * _bump(t, T.chip_out, 0.1, 0.04)
    if k < 0.01:
        return
    rot = 0.05 * math.sin((t - t_in) * 2 * math.pi * 1.7)
    txt = "NICE TRIES: 10?"
    size = 32
    with saved(ctx, 205, 168, k, rot) as c:
        P.label_tag(c, 0, 0, txt, color="warn", size=size, font="round")
        if t >= T.malvo:
            tw = text_width(c, txt, "round", size)
            pre = text_width(c, "NICE TRIES: ", "round", size)
            xa = -tw / 2 + pre - 6
            xb = tw / 2 + 8
            u = ease_out(seg(t, T.malvo, T.malvo + 0.14))
            ya, yb = 12, -16
            xe, ye = lerp(xa, xb, u), lerp(ya, yb, u)
            c.move_to(xa, ya)
            c.line_to(xe, ye)
            _s(c, INK, 13)
            c.move_to(xa, ya)
            c.line_to(xe, ye)
            _s(c, "danger", 7)


# ---------------------------------------------------------------------------
def render(ctx, t, info):
    T = _T(info)
    if t < T.party:
        shot_lair(ctx, t, info, T)
    else:
        shot_party(ctx, t, info, T)


def caption_y(t, info):
    """Engine default, except: the l02 caption's 0.35 s reading hold must not
    ride across the hard cut into the (caption-free) party wide shot."""
    T = _T(info)
    if T.party <= t < T.l3.start:
        return None
    return _CAPTIONS.DEFAULT_Y


def SFX(info):
    T = _T(info)
    return [
        (T.up0, "whoosh", -6),                        # cape swish as he springs up
        (T.release - 0.02, "swoosh_up", -12),         # sticky flung
        (T.slap, "paper", -6),                        # slap on the board
        (T.that, "sparkle", -8),
        (T.pop, "pop", -4),
        (T.party + 0.4, "ta_da", -6),
        (T.party + 0.7, "crowd_laugh", -12),
        (T.stats + 0.04, "sparkle", -10),             # the wink
        (T.lean, "tiptoe", -12),
        (T.chip_in, "tick", -10),
        (T.malvo, "whoosh", -14),                     # strike through '10?'
        (T.malvo + 0.1, "snake_hiss", -14),           # Hissy's facepalm sigh
        (T.l7.start + 0.5, "crowd_laugh", -12),
        (T.chip_out, "pop", -14),
    ]
