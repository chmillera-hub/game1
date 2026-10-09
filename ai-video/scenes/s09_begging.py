"""s09 - Trick #9: begging (world's smallest violin, "...Need a hug?").

Shots (hard cuts, every time derived from cues / line timings, see _T):

  A  card..soft     F1 kneeling. Frame 0 matches s08's end (slumped, Hissy
                    facepalm); Malvo hops and DROPS to his knees behind the
                    desk (squash on landing), gloves snap into a clasp.
                    Card #9 "BEGGING" slams. l01: PUPPY EYES + TEARS, a huge
                    wail on "PLEEEASE", bargaining jazz-hands on "five stars"
                    while 5 gold rating stars pop in an arc over his head.
                    Hissy plays the world's smallest violin (tail tip on the
                    bow, 3 Hz), lids half; side-eyes the camera on "stars".
                    Slow push-in on his face.
  B  soft..considers F3 AI CU. Half-lid "seen it" look -> SLOW BLINK ->
                    sympathetic with a head tilt. l02: gentle "nope" head
                    shake + stop palm, which turns into a pat-pat on "buddy".
                    star: the right hand presents a gold FOR EFFORT star.
                    SLOW BLINK, l03 "...Need a hug?": warm, blushing, arms
                    open wide; the star hovers beside it. crowd_aww at the end.
  C  considers..end F1 kneeling. Sniffle hitch, lip quiver, eyes dart to
                    Hissy (frozen mid-stroke), to camera, back to the AI.
                    l04 "...Maybe later.": sheepish, eyes down/away, shy
                    finger-poke; the FOR EFFORT star floats in from the right
                    and sticks to his lapel (villain-local (100, -318), see
                    LAPEL). tally: chip 8 -> 9, he peeks up at it, Hissy nods.
"""
import math

from engine import core
from engine.core import (text, text_width, saved, seg, clamp, ease_out_back, ease_in_out,
                         ease_out, ease_in, rrect, fill_stroke, circle, lerp, state_at,
                         smoothstep, noise1, ellipse)
from engine import props as P
from engine import villain as V
from engine import snake as SN
from engine.villain import draw_villain
from engine.ai_char import draw_ai
from engine import ai_char as AI


# ===========================================================================
# shared overlay code (DIRECTION.md 4.4, verbatim)
# ===========================================================================
CARD_C = (495, 400)      # card centre while big (above Malvo's head in F1)
TAB_C = (730, 168)       # parked tab centre (top-right, inside the safe zone)
TAB_S = 0.42


def trick_card(ctx, t, t_in, num, title, park=1.9):
    """'TRICK #n' / TITLE card. Slams in at t_in, holds, parks as a tab at
    t_in+park (0.3 s move). Call every frame after t_in (draw it LAST, before
    captions). SFX: page_flip at t_in (-6 dB), stamp at t_in+0.12 (-4 dB)."""
    if t < t_in:
        return
    k_in = ease_out_back(seg(t, t_in, t_in + 0.2))
    k_mv = ease_in_out(seg(t, t_in + park, t_in + park + 0.3))
    # dim the frame while the card is big
    dim = 0.38 * clamp((t - t_in) / 0.08) * (1 - k_mv)
    if dim > 0.003:
        ctx.set_source_rgba(0.04, 0.02, 0.08, dim)
        ctx.paint()
    s_big = 1.9 - 0.9 * k_in                       # 1.9 -> 1.0 slam
    s = lerp(s_big, TAB_S, k_mv)
    x = lerp(CARD_C[0], TAB_C[0], k_mv)
    y = lerp(CARD_C[1], TAB_C[1], k_mv)
    rot = lerp(-0.045, 0.0, k_mv)
    a = clamp((t - t_in) / 0.06)
    title_size = 96
    while text_width(ctx, title, "comic", title_size) > 760 and title_size > 52:
        title_size -= 4
    tw = max(text_width(ctx, title, "comic", title_size), 300)
    pw, ph = tw + 90, title_size + 120
    with saved(ctx, x, y, s, rot, alpha_=a) as c:
        rrect(c, -pw / 2 + 8, -ph / 2 + 12, pw, ph, 34)       # flat shadow
        c.set_source_rgba(0, 0, 0, 0.35)
        c.fill()
        rrect(c, -pw / 2, -ph / 2, pw, ph, 34)
        fill_stroke(c, "ui_dark", "ai_accent", 8)
        text(c, f"TRICK #{num}", 0, -ph / 2 + 58, 50, "white", "comic",
             outline="ink", outline_w=8)
        text(c, title, 0, ph / 2 - 30, title_size, "ai_accent", "comic",
             outline="ink", outline_w=12)


def nice_tries_chip(ctx, t, n_before, n_after, t_tick, t_in=None, step=0.28):
    """Persistent top-left 'NICE TRIES: n' chip. Counts n_before -> n_after,
    one tick every `step` s starting at t_tick (the scene's 'tally' cue).
    SFX per tick: tick (-8 dB) + pop (-10 dB)."""
    if t_in is not None and t < t_in:
        return
    n, k_last = n_before, -1
    for i in range(n_after - n_before):
        if t >= t_tick + i * step:
            n, k_last = n_before + i + 1, i
    bump = 0.0
    if k_last >= 0:
        u = seg(t, t_tick + k_last * step, t_tick + k_last * step + 0.25)
        bump = math.sin(u * math.pi) * 0.22
    s = (ease_out_back(seg(t, t_in, t_in + 0.3)) if t_in is not None else 1.0) * (1 + bump)
    with saved(ctx, 205, 168, s) as c:
        P.label_tag(c, 0, 0, f"NICE TRIES: {n}", color="bubble_ai", size=32, font="round")
    if k_last >= 0 and t < t_tick + k_last * step + 0.6:           # floating '+1'
        u = seg(t, t_tick + k_last * step, t_tick + k_last * step + 0.6)
        text(ctx, "+1", 345, 150 - 40 * u, 40, (1, 0.82, 0.4, 1 - u), "comic",
             outline=(0.09, 0.06, 0.12, 1 - u), outline_w=7)


# ===========================================================================
# framing constants
# ===========================================================================
TITLE = "BEGGING"
VX, VS = 495.0, 0.95                 # F1
VY_STAND, VY_KNEEL = 1250.0, 1410.0  # standing (s08 end) / kneeling behind the desk
DESK_Y = 1250.0
FACE_K = (VX, VY_KNEEL - 518 * VS)   # kneeling face centre (495, 918)
AI3 = (458.0, 800.0, 1.1)            # F3 AI CU (nudged left: the gift star lives right)
PUSH_A = 1.08                        # shot A slowly pushes in to this
LAPEL = (100.0, -318.0)              # FOR EFFORT star on his lapel, villain-local (s=1)
LAPEL_S = 0.6                        # gift-star scale on the lapel (star r = 24 at s=1)

GOLD = "#ffcf3a"
GOLD_DK = "#d99a12"
TEAR = "#8fd8ff"
VIOLIN = "#b8662e"
VIOLIN_DK = "#7a3d18"
VIOLIN_HI = "#d98c4a"
EBONY = "#2a1812"
VIO_S = 1.55                         # violin scale (villain-local units)
BOW_HAIR = "#f3ead2"


# ===========================================================================
# s09-only rig additions (registered under s09_ names; built-ins untouched)
# ===========================================================================
_PLEAD = V.VILLAIN_EXPR["pleading"]
V.VILLAIN_EXPR.setdefault("s09_wail", dict(_PLEAD, by1=-30, by2=-32, ba1=-0.62, ba2=-0.62,
                                             ul1=0.0, ul2=0.0, es=1.14, ps=1.3, mc=-0.95,
                                             mw=1.32, mo=0.45, mt=0.25, tilt=0.05, hy=-6,
                                             flutter=0.0, blush=0.8))
V.VILLAIN_EXPR.setdefault("s09_puppy", dict(_PLEAD, flutter=0.0, es=1.12, ps=1.5))
V.VILLAIN_EXPR.setdefault("s09_bargain", dict(V.VILLAIN_EXPR["hopeful"], shine=1.0, ps=1.4,
                                                mc=0.7, mw=1.0, mo=0.1, blush=0.6,
                                                flutter=0.5, tilt=-0.04))
V.VILLAIN_EXPR.setdefault("s09_moved", dict(_PLEAD, flutter=0.0, mc=-0.35, mw=0.6, mo=0.0,
                                              blush=0.85, by1=-22, by2=-24, ps=1.38,
                                              tilt=0.06))
V.VILLAIN_EXPR.setdefault("s09_shy", dict(V.VILLAIN_EXPR["sheepish"], sweat=0.0, mc=0.55,
                                            msk=0.35, blush=1.0, ul1=0.36, ul2=0.34))

# clasped gloves held LOW (just above the desk edge) so the wailing mouth stays
# clear; _BEG2 is the same clasp shifted, blended back and forth = pleading shake
_BEG_A = V._arm(-176, -118, -36, -222, -1.38, cu=0.12, th=0.1, sp=0.0, hs=1.1)
_BEG_A2 = V._arm(-176, -114, -30, -214, -1.30, cu=0.12, th=0.1, sp=0.0, hs=1.1)
_BEG_B2 = V._mirror(V._arm(-176, -122, -42, -228, -1.44, cu=0.12, th=0.1, sp=0.0, hs=1.1))
# "I'll give you five stars!": both palms up, offering, just above the desk
_OFFER_A = V._arm(-214, -130, -120, -250, -2.05, cu=0.06, th=-0.3, sp=0.95, pm=1.0, tf=-1,
                  hs=1.05)
# shy finger-poke (index fingers meet in front of the chest)
_POKE_A = V._arm(-196, -130, -70, -268, -0.2, cu=1.0, ix=0.0, th=0.2, sp=0.1, hs=1.0)
_POKE_A2 = V._arm(-196, -130, -88, -264, -0.06, cu=1.0, ix=0.0, th=0.2, sp=0.1, hs=1.0)
for _nm, _pz in (("s09_beg", V._pose(_BEG_A, shy=-12, hdy=4)),
                 ("s09_beg2", V._pose(_BEG_A2, _BEG_B2, shy=-12, hdy=4)),
                 ("s09_offer", V._pose(_OFFER_A, shy=-16, hdy=-2)),
                 ("s09_poke", V._pose(_POKE_A, shy=-4, hdy=6)),
                 ("s09_poke2", V._pose(_POKE_A2, shy=-4, hdy=6))):
    V.ARM_POSES.setdefault(_nm, _pz)


def _ai_mix(a, b, k):
    da, db = AI.EXPR[a], AI.EXPR[b]
    return {key: lerp(da[key], db[key], k) for key in da}


AI_FLAT = dict(_ai_mix("neutral", "unimpressed", 0.55), sacc=0.3)       # "seen it" half lids
AI_SYMP = dict(AI.EXPR["sympathetic"], tilt=0.14)
AI_KIND = dict(AI.EXPR["sympathetic"], mc=0.48, lL=0.2, lR=0.2, lc=0.14, tilt=0.12,
               blush=0.35)
AI_GIFT = dict(AI.EXPR["warm"], mc=0.9, mw=0.95, tilt=0.03)
AI_HUG = dict(AI.EXPR["warm"], blush=1.1, tilt=0.13, bLy=14, bRy=14, ps=1.24, mc=0.85,
              mw=0.95)

# AI hand poses for this scene. The rig only knows its built-in pose names, so
# wrap its pose lookup: s09_* names are handled here, everything else falls
# straight through to the rig (other scenes are unaffected).
_AI_POSE0 = AI._pose
_AI_OFFER_R = AI._H(276, 160, 0.95, open=1.0, thumb=0.75, palm=0.85, sc=1.1)


def _s09_ai_pose(name, t, seed):
    if isinstance(name, str) and name.startswith("s09_"):
        d = _AI_POSE0("idle", t, seed)
        if name == "s09_pat":
            # palm-down "there, there" pats at 2 Hz (quick down, soft up)
            ph = (t * 2.0) % 1.0
            dip = math.sin(math.pi * min(1.0, ph / 0.45)) if ph < 0.45 else 0.0
            d["L"] = AI._H(-262, 214 + 16 * dip, 1.62 + 0.16 * dip, open=0.92, thumb=0.35,
                           tl=0.8, palm=0.0, sc=1.3)
        elif name == "s09_offer":
            # the patting hand rests where it patted (going back to the rig's
            # mirrored idle hand flips it edge-on for 3 frames, a spoon-like
            # sliver poking out of the left edge)
            d["L"] = AI._H(-266, 222, 1.42, open=0.85, thumb=0.4, tl=0.8, palm=0.0, sc=1.25)
            d["R"] = dict(_AI_OFFER_R)
        elif name == "s09_hug":
            # arms open for a hug; the right hand keeps holding out the gift
            d["L"] = AI._H(-306, 92, -0.72, open=1.0, thumb=0.85, palm=0.9, sc=1.12)
            d["R"] = dict(_AI_OFFER_R)
        return d
    return _AI_POSE0(name, t, seed)


if not getattr(AI._pose, "_s09", False):
    _s09_ai_pose._s09 = True
    AI._pose = _s09_ai_pose


# ===========================================================================
# timing (everything from cues / line timings)
# ===========================================================================
def _wt(info, lid, k, frac=0.5):
    L = info.line(lid)
    ws = info._lip.get(lid, {}).get("word_starts", [])
    if 0 <= k < len(ws):
        return L.start + ws[k]
    return L.start + L.dur * frac


def _T(info):
    L1, L2, L3, L4 = (info.line(f"s09_l0{i}") for i in range(1, 5))
    T = dict(card=info.cue("card"), soft=info.cue("soft"), star=info.cue("star"),
             cons=info.cue("considers"), tally=info.cue("tally"), end=info.dur,
             l1s=L1.start, l1e=L1.end, l2s=L2.start, l2e=L2.end, l3s=L3.start,
             l3e=L3.end, l4s=L4.start, l4e=L4.end)
    n1 = len(L1.caption.split())
    T["please"] = _wt(info, "s09_l01", 0, 0.0)
    T["just"] = _wt(info, "s09_l01", 1, 0.22)
    T["ill"] = _wt(info, "s09_l01", 4, 0.52)
    T["five"] = _wt(info, "s09_l01", n1 - 2, 0.73)
    T["stars"] = _wt(info, "s09_l01", n1 - 1, 0.8)
    T["not"] = _wt(info, "s09_l02", 0, 0.05)
    T["buddy"] = _wt(info, "s09_l02", 3, 0.55)
    T["hug"] = _wt(info, "s09_l03", 2, 0.4)
    T["later"] = _wt(info, "s09_l04", 1, 0.35)
    # drop to the knees
    T["hop"] = T["card"] + 0.07
    T["land"] = T["card"] + 0.27
    # violin
    T["vio_in"] = max(T["land"] + 0.08, T["l1s"] - 0.14)
    T["saw0"] = T["vio_in"] + 0.18
    T["vio_out"] = T["l4s"] + 0.2
    # five rating stars
    T["stars_t"] = [T["five"] + 0.02 + 0.08 * k for k in range(5)]
    # the gift
    T["gift"] = T["star"] + 0.05
    T["blink1"] = T["soft"] + 0.16
    T["blink2"] = max(T["gift"] + 0.12, T["l3s"] - 0.34)
    # the FOR EFFORT star flies to his lapel
    T["fly0"] = T["l4s"] + 0.12
    T["stick"] = max(T["fly0"] + 0.6, min(T["l4e"] - 0.1, T["fly0"] + 1.0))
    return T


# ===========================================================================
# small helpers
# ===========================================================================
def _state(t, keys, default=0.25):
    """state_at with per-key transitions: [(time, value[, trans]), ...]."""
    prev = cur = keys[0][1]
    start, tr = -1e9, default
    for k in keys:
        if t >= k[0]:
            prev, cur, start = cur, k[1], k[0]
            tr = k[2] if len(k) > 2 else default
        else:
            break
    return prev, cur, smoothstep(seg(t, start, start + tr))


def _arms_shake(t, keys, freq=5.0):
    """Arm-pose keys; while fully settled in 's09_beg' the clasped gloves
    tremble (blend to 's09_beg2' and back)."""
    a, b, k = _state(t, keys, 0.25)
    if b == "s09_beg" and k >= 1.0:
        t0 = max(kk[0] for kk in keys if kk[0] <= t)
        tr = [kk for kk in keys if kk[0] == t0][0]
        t1 = t0 + (tr[2] if len(tr) > 2 else 0.25)
        osc = 0.5 - 0.5 * math.cos(2 * math.pi * freq * (t - t1))
        return ("s09_beg", "s09_beg2", osc)
    return (a, b, k)


def _look(t, keys, default=0.12):
    """Eye targets [(time, (x, y)[, move_time]), ...] with quick eased moves."""
    a, b, k = _state(t, keys, default)
    return (lerp(a[0], b[0], k), lerp(a[1], b[1], k))


def _bump(t, t0, dur):
    if t < t0 or t > t0 + dur:
        return 0.0
    return math.sin(math.pi * (t - t0) / dur)


def _pulses(t, times, dur=0.1, amt=0.6):
    """Blink override: quick partial closes (puppy-eye flutter)."""
    for t0 in times:
        if t0 <= t <= t0 + dur:
            return amt * math.sin(math.pi * (t - t0) / dur)
    return None


def _slow_blink(t, t0):
    """SLOW BLINK: close 0.12 s, hold 0.08 s, open 0.12 s (None = auto)."""
    if t < t0 or t > t0 + 0.32:
        return None
    d = t - t0
    if d < 0.12:
        return smoothstep(d / 0.12)
    if d < 0.20:
        return 1.0
    return 1 - smoothstep((d - 0.20) / 0.12)


def _snake_d(expr, look, tongue=False, blink=None, mouth=0.0):
    return {"expr": expr, "look": look, "tongue": tongue, "blink": blink, "mouth": mouth}


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
    """Chunky cartoon gold star with one shadow tone and a shine."""
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


def _gift_star(c, x, y, s, t, label_k=1.0, rot=0.0):
    """The FOR EFFORT gift (DIRECTION 6.4): gold star r 40 + label_tag under it."""
    with saved(c, x, y, s) as cc:
        if label_k > 0.01:
            with saved(cc, 0, 58, label_k, -0.04) as c2:
                P.label_tag(c2, 0, 0, "FOR EFFORT", color="ai_accent", size=24)
        _gold_star(cc, 0, 0, 40, rot, 5.0)


# ===========================================================================
# villain extras (drawn in villain-local coords, s = 1 units)
# ===========================================================================
def _vstate(t, expr, arms, mouth, seed=1):
    """Replicates the rig's body/head motion so props can ride on it."""
    p = V.resolve_expr(expr)
    _a, _b, a_shy, a_hdy, a_tilt = V.resolve_arms(arms, t)
    mo_lip = float(mouth[0]) if isinstance(mouth, (tuple, list)) else float(mouth)
    talk = clamp(mo_lip * 3)
    breath = math.sin(t * 2 * math.pi / 3.6 + seed * 1.3)
    shy = p["shy"] + a_shy - breath * 2.5
    head_dy = p["hy"] + a_hdy - breath * 3.0 + shy * 0.5 - mo_lip * 5
    head_rot = (p["tilt"] + a_tilt + noise1(t * 0.35, seed + 5) * 0.025
                + noise1(t * 2.2, seed + 6) * 0.03 * talk)
    return dict(p=p, shy=shy, breath=breath, head_dy=head_dy, head_rot=head_rot)


def _face_xf(c, st):
    c.translate(V.NECK[0], V.NECK[1] + st["head_dy"])
    c.rotate(st["head_rot"])
    c.translate(0, V.FACE_OFF)


def _tears(c, t, st, look, grow, alpha=1.0):
    """TEARS (DIRECTION 4.3): two pale-blue streams from the lower lids."""
    if grow <= 0.01 or alpha <= 0.01:
        return
    p = st["p"]
    lx = clamp(look[0] + p["ex"], -1.2, 1.2)
    turn = lx * 9.0
    c.save()
    _face_xf(c, st)
    if alpha < 0.999:
        c.push_group()
    for side, sx in ((1, -1), (2, 1)):
        es = p["es"] * (1.07 if side == 2 else 1.0)
        cx, cy = sx * V.EYE_DX + turn, V.EYE_DY
        ry = V.EYE_RY * es
        y0 = cy + ry * 0.8 + (14 if side == 2 else 0)     # under the monocle rim
        L = 104 * grow
        pts = []
        for i in range(9):
            u = i / 8
            yy = y0 + L * u
            xx = cx + sx * (16 + 10 * u) + 3.5 * math.sin(u * 5.0 + t * 9 + side) * u
            pts.append((xx, yy))
        for w, col in ((10, "ink"), (5.5, TEAR)):
            core.smooth_path(c, pts)
            core.stroke(c, col, w)
        ex, ey = pts[-1]
        r = 5.5 + 2.0 * grow
        for rr, col in ((r + 2.2, "ink"), (r, TEAR)):
            ellipse(c, ex, ey + 2, rr * 0.86, rr)
            core.set_color(c, col)
            c.fill()
        circle(c, ex - 2, ey, 1.8)
        c.set_source_rgba(1, 1, 1, 0.9)
        c.fill()
    if alpha < 0.999:
        c.pop_group_to_source()
        c.paint_with_alpha(alpha)
    c.restore()


def _violin_geom(t, st, saw):
    """Violin + bow placement under Hissy's chin (villain-local, s=1 units).
    The violin points left (scroll past his jaw), the bow crosses it near the
    bridge and its frog sits close to the coil's tail end."""
    hx = V.SNAKE_HEAD[0]
    hy = V.SNAKE_HEAD[1] + st["shy"] * 0.6 - st["breath"] * 1.5
    vc = (hx + 40, hy + 100)                  # violin body centre
    rot = 0.30                                # +x = tail end (under his chin)
    ax = (math.cos(rot), math.sin(rot))
    ba = 1.31                                 # bow axis angle (frog end, down-right)
    nb = (math.cos(ba), math.sin(ba))
    contact = (vc[0] + 4 * VIO_S * ax[0], vc[1] + 4 * VIO_S * ax[1])
    half = 48.0
    bc = (contact[0] + nb[0] * saw, contact[1] + nb[1] * saw)
    tip = (bc[0] - nb[0] * half, bc[1] - nb[1] * half)
    frog = (bc[0] + nb[0] * half, bc[1] + nb[1] * half)
    return dict(vc=vc, rot=rot, ax=ax, nb=nb, tip=tip, frog=frog)


def _draw_violin(c, g, k):
    """World's smallest violin (DIRECTION 6.13), body 70x28 at s=1 (here 1.3)."""
    vs = VIO_S * k
    with saved(c, g["vc"][0], g["vc"][1], vs, g["rot"]) as cc:
        # neck + scroll (toward -x)
        rrect(cc, -66, -4.5, 46, 9, 4)
        fill_stroke(cc, EBONY, "ink", 3.2)
        circle(cc, -69, 0, 6.5)
        fill_stroke(cc, VIOLIN_DK, "ink", 3.2)
        circle(cc, -69, 0, 2.2)
        core.fill(cc, "ink")
        # body: two bouts with a waist
        pts = [(35, 0), (32, -11), (20, -14), (8, -10), (0, -8), (-8, -10), (-20, -12),
               (-31, -9), (-35, 0), (-31, 9), (-20, 12), (-8, 10), (0, 8), (8, 10),
               (20, 14), (32, 11)]
        core.smooth_path(cc, pts, closed=True)
        fill_stroke(cc, VIOLIN, "ink", 3.6)
        ellipse(cc, 10, -6, 18, 4.5)
        core.fill(cc, VIOLIN_HI)
        # fingerboard over the body, tailpiece, f-holes, bridge, strings
        rrect(cc, -24, -3.5, 22, 7, 3)
        core.fill(cc, EBONY)
        core.poly(cc, [(18, -4), (31, -3), (31, 3), (18, 4)])
        core.fill(cc, EBONY)
        for sy in (-1, 1):
            cc.move_to(2, sy * 8)
            cc.curve_to(5, sy * 4, 9, sy * 9, 12, sy * 5)
            core.stroke(cc, EBONY, 2.0)
        rrect(cc, 9, -6, 3, 12, 1)
        core.fill(cc, "#f3e3b8")
        for sy in (-2.2, -0.7, 0.7, 2.2):
            cc.move_to(-64, sy)
            cc.line_to(30, sy)
        cc.set_source_rgba(0.98, 0.94, 0.82, 0.8)
        cc.set_line_width(0.7)
        cc.stroke()


def _draw_bow(c, g, k):
    tip, frog = g["tip"], g["frog"]
    if k < 0.999:
        mid = ((tip[0] + frog[0]) / 2, (tip[1] + frog[1]) / 2)
        tip = (lerp(mid[0], tip[0], k), lerp(mid[1], tip[1], k))
        frog = (lerp(mid[0], frog[0], k), lerp(mid[1], frog[1], k))
    nb = g["nb"]
    side = (-nb[1] * 6, nb[0] * 6)

    def stick():
        c.move_to(*tip)
        c.curve_to(tip[0] + side[0] * 1.4, tip[1] + side[1] * 1.4,
                   frog[0] + side[0] * 1.4, frog[1] + side[1] * 1.4, *frog)
    # pale hair ribbon first, then the dark stick over it
    c.move_to(tip[0] - side[0] * 0.3, tip[1] - side[1] * 0.3)
    c.line_to(frog[0] - side[0] * 0.3, frog[1] - side[1] * 0.3)
    core.stroke(c, "ink", 7.5)
    c.move_to(tip[0] - side[0] * 0.3, tip[1] - side[1] * 0.3)
    c.line_to(frog[0] - side[0] * 0.3, frog[1] - side[1] * 0.3)
    core.stroke(c, BOW_HAIR, 3.5)
    stick()
    core.stroke(c, "ink", 8.5)
    stick()
    core.stroke(c, VIOLIN_DK, 4.0)
    with saved(c, tip[0], tip[1], k, math.atan2(nb[1], nb[0])) as cc:
        rrect(cc, -5, -4, 10, 9, 3)
        fill_stroke(cc, "#f3ead2", "ink", 2.5)
    with saved(c, frog[0], frog[1], k, math.atan2(nb[1], nb[0])) as cc:
        rrect(cc, -8, -7, 16, 14, 4)
        fill_stroke(cc, EBONY, "ink", 3.0)


def _tail_to_bow(c, t, st, g, k):
    """Hissy's tail tip leaves the coil end, arcs up and curls round the frog."""
    Pc, _split = V._coil_samples(t, st["shy"], st["breath"])
    e = Pc[-1]
    fx, fy = g["frog"]
    tx, ty = lerp(e[0], fx, k), lerp(e[1], fy, k)
    lift = 40 * k
    pts = [(e[0] + 2, e[1] + 1),
           (lerp(e[0], tx, 0.3), min(e[1], ty) - lift * 0.8),
           (lerp(e[0], tx, 0.72), min(e[1], ty) - lift),
           (tx + 8 * k, ty - 14 * k)]
    # curl wrapping the frog (clockwise from its top)
    for a in (-1.2, 0.2, 1.6, 2.9, 4.0):
        pts.append((tx + 16 * k * math.cos(a), ty + 16 * k * math.sin(a)))
    Pt = SN.coil_points(pts, 5)
    n = len(Pt)
    Wd = []
    for i in range(n):
        u = i / (n - 1)
        Wd.append(lerp(14, 21, min(1.0, u / 0.3)) * (1 - 0.55 * clamp((u - 0.6) / 0.4)))
    SN.draw_tube(c, Pt, Wd, 0, n - 1, cap0=False, cap1=True, belly_side=1, spots=False,
                 line_w=4.5)


# ===========================================================================
# shot A + C: F1 kneeling
# ===========================================================================
def _drop_y(t, T):
    """Hop up (anticipation) -> fall behind the desk -> damped bounce."""
    a0, hop, land = T["card"], T["hop"], T["land"]
    if t < hop:
        return lerp(VY_STAND, VY_STAND - 16, ease_out(seg(t, a0, hop)))
    if t < land:
        return lerp(VY_STAND - 16, VY_KNEEL + 16, ease_in(seg(t, hop, land)))
    u = t - land
    return VY_KNEEL + 16 * math.exp(-u * 11) * math.cos(u * 26)


def _squash(t, T):
    u = t - T["land"]
    if u < 0:
        k = seg(t, T["hop"], T["land"])
        return -0.05 * k                       # stretch while falling
    return 0.075 * math.exp(-u * 10) * math.cos(u * 24)


def _lair_front(c, t):
    P.desk(c, VX, DESK_Y, 1000)
    P.computer(c, 835, 1218, 0.7, view="side", facing=-1, t=t)
    P.keyboard(c, VX, DESK_Y, 360, t, typing=False)


def _villain_group(c, t, vy, sq, expr, look, mouth, arms, snake, blink, extras):
    """Draw Malvo (+ Hissy) at (VX, vy) with squash, then extras(c, st) in
    villain-local s=1 coords riding on his body."""
    c.save()
    c.translate(VX, vy)
    if abs(sq) > 1e-4:
        c.scale(1 + sq, 1 - sq)
    draw_villain(c, 0, 0, VS, t, expr=expr, look=look, mouth=mouth, arms=arms,
                 snake=snake, blink=blink)
    c.scale(VS, VS)
    st = _vstate(t, expr, arms, mouth)
    extras(c, st)
    c.restore()


def _rating_stars(c, t, T, until):
    """'I'll give you FIVE STARS!' -> five gold stars pop in an arc."""
    if t < T["stars_t"][0] or t >= until:
        return
    cx, cy, R = FACE_K[0], FACE_K[1] - 10, 318
    for k, t0 in enumerate(T["stars_t"]):
        if t < t0:
            continue
        a = math.radians(160 - 35 * k)
        x = cx + R * math.cos(a)
        y = cy - R * 0.84 * math.sin(a) - 6 * math.sin(t * 5 + k)
        u = seg(t, t0, t0 + 0.3)
        sc = ease_out_back(u, 2.6)
        sq = 0.18 * math.sin(u * math.pi) if u < 1 else 0.0
        rot = (1 - ease_out(u)) * -0.9 + 0.08 * math.sin(t * 3.1 + k * 1.7)
        with saved(c, x, y, (sc * (1 + sq), sc * (1 - sq))) as cc:
            _gold_star(cc, 0, 0, 38, rot, 5.0)
        if u >= 1.0 and k % 2 == 0:        # a twinkle beside every other star
            P.sparkles(c, x + 30, y - 26, 30, t, n=1, seed=40 + k, color="white", size=0.75)


def _shot_A(ctx, t, info, T):
    l1s, l1e = T["l1s"], T["l1e"]
    # --- Malvo ---------------------------------------------------------------
    expr = _state(t, [(-9, "frustrated"), (T["hop"], "s09_puppy", 0.16),
                      (T["please"] - 0.05, "s09_wail", 0.12),
                      (T["just"] - 0.04, "s09_puppy", 0.2),
                      (T["ill"] - 0.04, "s09_bargain", 0.2),
                      (T["l1e"] + 0.15, "s09_puppy", 0.35)])
    arms = _arms_shake(t, [(-9, "slump"), (T["hop"], "s09_beg", 0.18),
                           (T["five"] - 0.16, "s09_offer", 0.2),
                           (T["l1e"] + 0.2, "s09_beg", 0.3)])
    look = _look(t, [(-9, (0.55, 0.15)), (T["hop"], (0.25, -0.35), 0.1),
                     (T["please"], (0.05, -0.9), 0.15),          # wail to the heavens
                     (T["just"], (0.35, -0.35), 0.1),            # back to the AI
                     (T["ill"], (0.1, -0.15), 0.1),              # bargain to camera
                     (T["five"], (0.0, -0.75), 0.15),            # admires his stars
                     (T["l1e"] + 0.1, (0.35, -0.3), 0.15)])
    puffs = []
    for p0 in (T["please"], T["just"], T["ill"]):
        puffs += [p0 + 0.06, p0 + 0.18, p0 + 0.30]
    blink = _pulses(t, puffs, 0.1, 0.5)
    mouth = info.mouth("villain", t)
    vy = _drop_y(t, T)
    sq = _squash(t, T)
    # --- Hissy ---------------------------------------------------------------
    sn_expr = _state(t, [(-9, "facepalm"), (T["card"] + 0.12, "unimpressed", 0.3),
                         (T["stars"] - 0.1, "side_eye", 0.15),
                         (T["stars"] + 0.75, "unimpressed", 0.25)])
    sn_look = _look(t, [(-9, (0.4, 0.2)), (T["vio_in"], (0.55, 0.75), 0.15),
                        (T["stars"] - 0.1, (1.0, 0.0), 0.12),
                        (T["stars"] + 0.75, (0.55, 0.75), 0.15)])
    tongue = True if T["stars"] + 0.35 <= t < T["stars"] + 0.6 else False
    snake = _snake_d(sn_expr, sn_look, tongue)
    # violin
    vk = ease_out_back(seg(t, T["vio_in"], T["vio_in"] + 0.25), 2.2)
    amp = 14 * smoothstep(seg(t, T["saw0"], T["saw0"] + 0.2))
    saw = amp * math.sin(2 * math.pi * 3.0 * (t - T["saw0"]))
    # tears
    grow = ease_out(seg(t, l1s + 0.12, l1s + 0.52))
    # camera: slow push-in on his face while he begs
    push = 1.0 + (PUSH_A - 1.0) * ease_in_out(seg(t, l1s, T["soft"] - 0.2))
    fx, fy = FACE_K[0], FACE_K[1] - 40

    def extras(c, st):
        if vk > 0.01:
            g = _violin_geom(t, st, saw)
            _draw_violin(c, g, vk)
            _draw_bow(c, g, min(1.0, vk))
            _tail_to_bow(c, t, st, g, min(1.0, vk))
        _tears(c, t, st, look, grow)

    with saved(ctx, fx, fy, push) as c:
        c.translate(-fx, -fy)
        P.lair_bg(c, t)
        _villain_group(c, t, vy, sq, expr, look, mouth, arms, snake, blink, extras)
        _lair_front(c, t)
        _rating_stars(c, t, T, T["soft"])


def _fly_star(c, t, T, st_now):
    """FOR EFFORT star: floats in from the right, sticks on the lapel."""
    f0, f1 = T["fly0"], T["stick"]
    if t < f0:
        return
    # lapel target in world coords (villain kneeling, no squash in this shot)
    lx = VX + LAPEL[0] * VS
    ly = VY_KNEEL + (LAPEL[1] + st_now["shy"] * 0.5) * VS
    if t < f1:
        u = ease_in_out(seg(t, f0, f1))
        p0, p1, p2 = (1010.0, 1010.0), (800.0, 900.0), (lx, ly)
        x = (1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0]
        y = (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1]
        y += 10 * math.sin(u * math.pi * 2) * (1 - u)          # floaty bob
        s = lerp(0.95, LAPEL_S * VS, u)
        rot = (1 - u) * 1.6 * math.sin(u * 7) * 0.5
        _gift_star(c, x, y, s, t, 1.0, rot)
        return
    # stuck: squash-pop then settle
    u = seg(t, f1, f1 + 0.28)
    k = 1 + 0.35 * math.sin(u * math.pi) * (1 - u)
    _gift_star(c, lx, ly, LAPEL_S * VS * k, t, 1.0, 0.0)
    if t < f1 + 0.5:
        P.sparkles(c, lx, ly, 60, t, n=4, seed=31, color="white", size=0.7)


def _shot_C(ctx, t, info, T):
    c0 = T["cons"]
    l4s = T["l4s"]
    # --- Malvo ---------------------------------------------------------------
    expr = _state(t, [(-9, "s09_moved"), (l4s - 0.08, "sheepish", 0.25),
                      (T["stick"] + 0.12, "s09_shy", 0.3)])
    look = _look(t, [(-9, (0.55, -0.2)),
                     (c0 + 0.14, (-1.0, 0.15), 0.08),     # dart: Hissy
                     (c0 + 0.36, (0.0, 0.0), 0.08),       # dart: camera
                     (c0 + 0.56, (0.6, -0.2), 0.08),      # dart: back to the AI
                     (l4s, (-0.35, 0.65), 0.18),          # "Maybe later." down and away
                     (T["stick"] - 0.45, (0.9, 0.55), 0.15),  # spots the star coming
                     (T["stick"] - 0.12, (0.5, 1.0), 0.12),   # ...on his lapel
                     (T["tally"] - 0.05, (-0.85, -1.0), 0.12),  # up at the chip
                     (T["tally"] + 0.55, (0.1, 0.05), 0.2)])
    if t < l4s:
        q = 0.5 + 0.5 * math.sin(2 * math.pi * 6.0 * (t - c0))
        mouth = (0.1 * q * smoothstep(seg(t, c0, c0 + 0.1)), 0.0)    # lip quiver
    else:
        mouth = info.mouth("villain", t)
    poke_in = l4s - 0.1
    if t < poke_in + 0.25:
        arms = state_at(t, [(-9, "s09_beg"), (poke_in, "s09_poke")], 0.25)
    else:
        osc = 0.5 - 0.5 * math.cos(2 * math.pi * 2.6 * (t - poke_in - 0.25))
        arms = ("s09_poke", "s09_poke2", osc)
    # sniffle hitch + gulp bob
    vy = VY_KNEEL - 8 * _bump(t, c0 + 0.02, 0.2) + 4 * _bump(t, c0 + 0.42, 0.22)
    blink = _slow_blink(t, T["tally"] + 0.3)
    # --- Hissy: frozen mid-stroke, caught looking, then agrees -----------------
    sn_expr = _state(t, [(-9, "unimpressed"), (c0 + 0.12, "idle", 0.1),
                         (l4s + 0.1, "unimpressed", 0.25),
                         (T["stick"] + 0.15, "side_eye", 0.15),
                         (T["tally"] + 0.05, "nod", 0.2)])
    sn_look = _look(t, [(-9, (0.55, 0.75)), (c0 + 0.12, (1.0, -0.15), 0.08),
                        (l4s + 0.1, (1.0, 0.45), 0.2),
                        (T["stick"] + 0.15, (1.0, 0.0), 0.12),
                        (T["tally"] + 0.05, (0.9, 0.2), 0.2)])
    tongue = True if T["stick"] + 0.45 <= t < T["stick"] + 0.7 else False
    snake = _snake_d(sn_expr, sn_look, tongue)
    saw_frozen = 14 * math.sin(2 * math.pi * 3.0 * (c0 - T["saw0"]))
    vk = 1.0 - ease_in(seg(t, T["vio_out"], T["vio_out"] + 0.22))
    # tears dry up during "Maybe later."
    t_alpha = 1.0 - smoothstep(seg(t, l4s + 0.35, l4s + 0.95))
    st_hold = {}

    def extras(c, st):
        st_hold.update(st)
        if vk > 0.01:
            g = _violin_geom(t, st, saw_frozen)
            _draw_violin(c, g, vk)
            _draw_bow(c, g, vk)
            _tail_to_bow(c, t, st, g, vk)
        _tears(c, t, st, look, 1.0, t_alpha)

    # static standard F1 framing: s10 opens on exactly this frame (he explodes
    # up from behind the desk), so the cut matches
    fx, fy = FACE_K[0], FACE_K[1] - 40
    with saved(ctx, fx, fy, 1.0) as c:
        c.translate(-fx, -fy)
        P.lair_bg(c, t)
        _villain_group(c, t, vy, 0.0, expr, look, mouth, arms, snake, blink, extras)
        _lair_front(c, t)
        _fly_star(c, t, T, st_hold)


# ===========================================================================
# shot B: F3 AI close-up
# ===========================================================================
def _shot_B(ctx, t, info, T):
    P.ai_bg(ctx, t)
    x, y, s = AI3
    soft, star = T["soft"], T["star"]
    expr = _state(t, [(-9, AI_FLAT), (T["blink1"] + 0.1, AI_SYMP, 0.3),
                      (T["buddy"] - 0.08, AI_KIND, 0.25),
                      (star - 0.02, AI_GIFT, 0.22),
                      (T["l3s"] - 0.1, AI_HUG, 0.28)])
    look = _look(t, [(-9, (-0.55, 0.45)),
                     (star + 0.02, (0.8, 0.25), 0.14),     # glance at the gift
                     (T["blink2"] + 0.1, (-0.45, 0.4), 0.14),  # "for you" (behind the blink)
                     (T["l3s"], (-0.35, 0.3), 0.2)])
    hands = _state(t, [(-9, "idle"), (T["not"] - 0.1, "stop", 0.22),
                       (T["buddy"] - 0.08, "s09_pat", 0.2),
                       (star - 0.04, "s09_offer", 0.24),
                       (T["l3s"] - 0.04, "s09_hug", 0.3)])
    blink = _slow_blink(t, T["blink1"])
    if blink is None:
        blink = _slow_blink(t, T["blink2"])
    shake = 0.32 * smoothstep(seg(t, T["not"], T["not"] + 0.12)) * \
        (1 - smoothstep(seg(t, T["buddy"] - 0.15, T["buddy"] + 0.05)))
    nod = 0.3 * _bump(t, T["hug"] - 0.05, 0.45)
    # tiny "aww" bounce on the hug line
    bounce = 1 + 0.03 * _bump(t, T["l3s"] - 0.05, 0.3)
    with saved(ctx, x, y + 120, bounce) as c:
        c.translate(-x, -(y + 120))
        A = draw_ai(c, x, y, s, t, expr=expr, look=look, mouth=info.mouth("ai", t),
                    hands=hands, blink=blink, shake=shake, nod=nod)
        # --- the gift: FOR EFFORT star on the right palm ---------------------
        g0 = T["gift"]
        if t >= g0:
            hx, hy = A["handR"]
            u = seg(t, g0, g0 + 0.32)
            k = ease_out_back(u, 2.4)
            sq = 0.16 * math.sin(u * math.pi) if u < 1 else 0.0
            spin = (1 - ease_out(u)) * 2.6
            # sized for a phone: the star + "FOR EFFORT" tag are the punchline
            # of "I'll give you five stars!", so they must read at a glance
            sx, sy = hx - 6, hy - 86 - 4 * math.sin((t - g0) * 3.2)
            core.radial_glow(c, sx, sy, 150 * k, "ai_accent", 0.32)
            if t > g0 + 0.2:
                P.sparkles(c, sx, sy - 20, 110, t, n=4, seed=17, color="white", size=0.85)
            with saved(c, sx, sy, (1.75 * k * (1 + sq), 1.75 * k * (1 - sq))) as cc:
                _gold_star(cc, 0, 0, 40, spin, 5.0)
            lab = ease_out_back(seg(t, g0 + 0.1, g0 + 0.38), 2.0)
            if lab > 0.01:
                with saved(c, hx - 56, hy + 82, lab * 1.6, -0.04) as cc:
                    P.label_tag(cc, 0, 0, "FOR EFFORT", color="ai_accent", size=24)


# ===========================================================================
# entry points
# ===========================================================================
def render(ctx, t, info):
    T = _T(info)
    if t < T["soft"]:
        _shot_A(ctx, t, info, T)
    elif t < T["cons"]:
        _shot_B(ctx, t, info, T)
    else:
        _shot_C(ctx, t, info, T)
    # overlays (last)
    nice_tries_chip(ctx, t, info.meta.get("tries_before", 8), info.meta.get("tries_after", 9),
                    T["tally"])
    trick_card(ctx, t, T["card"], 9, TITLE)


def caption_y(t, info):
    """Default caption position, but a caption still lingering from the shot we
    just cut away from (the engine holds the last line 0.35 s) is dropped at
    the cut, so Malvo's words never sit under the AI's face and vice versa."""
    T = _T(info)
    shot0 = T["cons"] if t >= T["cons"] else (T["soft"] if t >= T["soft"] else None)
    if shot0 is not None and info.active_line(t) is None:
        last = info.last_line(t)
        if last is not None and last.end <= shot0:
            return None
    return 1450


def SFX(info):
    T = _T(info)
    out = [
        (T["card"], "page_flip", -6),
        (T["card"] + 0.12, "stamp", -4),
        (T["hop"], "whoosh", -14),
        (T["vio_in"], "pop", -14),
        (T["stars"], "sparkle", -10),
        (T["gift"], "sparkle", -10),
        (T["gift"] + 0.02, "pop", -14),
        (T["l3e"], "crowd_aww", -14),
        (T["cons"] + 0.42, "gulp", -10),
        (T["stick"], "pop", -12),
        (T["tally"], "tick", -8),
        (T["tally"], "pop", -10),
    ]
    for t0 in T["stars_t"]:
        out.append((t0, "pop", -10))
    return sorted(out, key=lambda e: e[0])
