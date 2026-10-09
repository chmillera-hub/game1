"""s01 - Cold open: "the movie everyone is afraid of" (trailer parody).

Shots (all times derived from cues / line timings):
  eye_open   ECU of THE ROBOT's red visor, 60% lidded on frame 0, snaps open
             with a scale punch; title "THE ROBOT UPRISING" slams in.
  s01_l01    narrator; slow pull-back 3.2 -> 1.0 to the full robot, iris scans
             the audience, an army fades in on the ridge, stomps jolt the frame.
  lightning  4-frame flash; Malvo revealed in silhouette (red rim light, lit
             grin, monocle glint, Hissy's eyes glowing on his shoulder).
  s01_l02    "Machine! Help me destroy the world!" point + flare on "destroy".
  glare      iris slides down onto Malvo, red glow to max (heartbeat).
  flicker    visor stutters, dims to a low-battery glyph; Hissy side-eyes.
Hard cut out (s02 opens on the record scratch).
"""
import math

import cairocffi as cairo

from engine import core
from engine.core import (clamp, lerp, seg, ease_in_out, ease_out, ease_out_back, smoothstep,
                         tween, state_at, hexc, noise1, rrect, circle, ellipse, text,
                         radial_glow, vgradient)
from engine import props as P
from engine import villain as V
from engine import snake as SN

# ---------------------------------------------------------------------------
# palette
# ---------------------------------------------------------------------------
SKY_TOP, SKY_BOT = "#3a0a14", "#0e0710"
CHROME, CHROME_SH, CHROME_DK = "#9aa3b5", "#6b7385", "#5d6474"
CHROME_HI, SHOULDER = "#c7cdd9", "#7d8496"
BEZEL, SLOT = "#262a35", "#1a1d26"
VISOR_ON, VISOR_OFF, VISOR_DIM = "#ff3b5c", "#3a0d16", "#7a1f2e"
CORE = "#ffd0d8"
ARMY, ARMY_INK, RIDGE = "#2a0a12", "#0a0307", "#13050a"
INK = "ink"

VISOR_LOCAL = (0.0, -30.0)      # visor centre in robot-local coords
VISOR_ECU = (495.0, 720.0)      # visor centre on screen at s 3.2
VISOR_FULL = (495.0, 635.0)     # visor centre on screen at s 1.0 (robot centre ~ (495,760))
MALVO = (495.0, 1330.0, 0.8)
TINT = (0.07, 0.03, 0.08)
SIL_A = 0.96
MALVO_CLIP = (110, 650, 800, 650)     # x, y, w, h (world, under the camera)
FACE_CLIP = (330, 790, 360, 350)


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------
def _round_poly(ctx, pts, r):
    """Closed polygon with rounded corners (radius r, clamped per corner)."""
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
    core.fill_stroke(ctx, fc, sc, w)


def _word_t(info, lid, word, frac):
    """Scene time a word starts in line `lid` (fallback: fraction of line)."""
    L = info.line(lid)
    words = [w.strip(".,!?…").lower() for w in L.caption.split()]
    ws = info._lip.get(lid, {}).get("word_starts", [])
    if word in words:
        k = words.index(word)
        if k < len(ws):
            return L.start + ws[k]
    return L.start + L.dur * frac


def _bump(t, t0, dur, rise=0.04):
    """0 -> 1 -> 0 envelope: quick rise, smooth fall."""
    if t < t0 or t > t0 + dur:
        return 0.0
    if t < t0 + rise:
        return smoothstep((t - t0) / rise)
    return 1.0 - smoothstep((t - t0 - rise) / max(1e-6, dur - rise))


# ---------------------------------------------------------------------------
# timing (all from cues)
# ---------------------------------------------------------------------------
def _T(info):
    L1, L2 = info.line("s01_l01"), info.line("s01_l02")
    T = dict(
        open=info.cue("eye_open"), l1s=L1.start, l1e=L1.end,
        light=info.cue("lightning"), l2s=L2.start, l2e=L2.end,
        glare=info.cue("glare"), flick=info.cue("flicker"), end=info.dur,
    )
    T["title"] = T["open"] + 0.20
    T["world"] = _word_t(info, "s01_l01", "world", 0.08)
    T["everyone"] = _word_t(info, "s01_l01", "everyone", 0.3)
    T["ai"] = _word_t(info, "s01_l01", "ai", 0.57)
    T["bad"] = _word_t(info, "s01_l01", "bad", 0.8)
    T["army"] = L1.start + 0.55 * L1.dur
    T["stomps"] = [L1.start + 2.0, L1.start + 2.7, L1.start + 3.4]
    T["destroy"] = _word_t(info, "s01_l02", "destroy", 0.47)
    T["help"] = _word_t(info, "s01_l02", "help", 0.3)
    return T


STOMP_PEAK = 0.09       # robot_stomp impact onset is ~0.085 s after its start (peak 0.15):
                        # the jolt hits on the onset so picture and thump land together
GLITCH_LEAD = 0.17      # glitch bursts start ~0.2 s in: lead so they hit the stutters


def _flicker_state(t, f0):
    """'on' | 'off' | 'dim' for the visor around the flicker cue."""
    if t < f0:
        return "on"
    u = t - f0
    if u < 0.08:
        return "off"
    if u < 0.20:
        return "on"
    if u < 0.30:
        return "off"
    if u < 0.36:
        return "on"
    return "dim"


# ---------------------------------------------------------------------------
# THE ROBOT (bible 6.1), robot-local coords: head centre = (0, 0), s = 1
# ---------------------------------------------------------------------------
HEAD = [(-210, -190), (210, -190), (165, 190), (-165, 190)]


def _head_path(ctx):
    _round_poly(ctx, HEAD, 60)


def _draw_robot(ctx, t, look, lid, state, ring_rot, battery_k, light_blink, core_r=12.0,
                bar_on=True):
    # ---- torso + neck + shoulders (behind the head) -----------------------
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
    sh = [(-310, 385), (-306, 268), (-205, 232), (205, 232), (306, 268), (310, 385)]
    _round_poly(ctx, sh, 46)
    _fs(ctx, SHOULDER)
    ctx.save()
    _round_poly(ctx, sh, 46)
    ctx.clip()
    ctx.rectangle(-320, 330, 640, 80)
    core.fill(ctx, CHROME_SH)
    ctx.restore()
    _round_poly(ctx, sh, 46)
    core.stroke(ctx, INK, 5)
    for sx in (-1, 1):
        ctx.move_to(sx * 120, 240)
        ctx.line_to(sx * 132, 380)
        core.stroke(ctx, INK, 3.5)
        for yy in (290, 345):
            circle(ctx, sx * 250, yy, 9)
            _fs(ctx, CHROME_HI, INK, 3)

    # ---- antennae + ear discs ---------------------------------------------
    for i, sx in enumerate((-1, 1)):
        rrect(ctx, sx * 128 - 12, -244, 24, 64, 6)
        _fs(ctx, CHROME_SH, INK, 4)
        circle(ctx, sx * 128, -250, 17)
        _fs(ctx, CHROME, INK, 4)
        on = light_blink[i]
        if on > 0.02:
            circle(ctx, sx * 128, -250, 8)
            core.fill(ctx, core.alpha(VISOR_ON, on))
    for sx in (-1, 1):
        circle(ctx, sx * 202, -8, 46)
        _fs(ctx, SHOULDER)
        circle(ctx, sx * 202, -8, 22)
        _fs(ctx, CHROME_SH, INK, 3.5)

    # ---- head -------------------------------------------------------------
    _head_path(ctx)
    core.fill(ctx, CHROME)
    ctx.save()
    _head_path(ctx)
    ctx.clip()
    ctx.move_to(-260, 26)
    ctx.curve_to(-120, 44, 120, 44, 260, 26)
    ctx.line_to(260, 260)
    ctx.line_to(-260, 260)
    ctx.close_path()
    core.fill(ctx, CHROME_SH)
    # chrome highlight streak (forehead, screen-left)
    ctx.move_to(-190, -168)
    ctx.line_to(-120, -168)
    ctx.line_to(-176, -112)
    ctx.line_to(-200, -112)
    ctx.close_path()
    core.fill(ctx, CHROME_HI)
    # forehead seam + faceplate seams
    ctx.move_to(-230, -128)
    ctx.line_to(230, -128)
    for sx in (-1, 1):
        ctx.move_to(sx * 172, 18)
        ctx.line_to(sx * 132, 190)
    core.stroke(ctx, INK, 3.5)
    ctx.restore()
    _head_path(ctx)
    core.stroke(ctx, INK, 5.5)
    for (rx, ry) in ((-176, -158), (176, -158), (-140, 150), (140, 150)):
        circle(ctx, rx, ry, 8)
        _fs(ctx, CHROME_HI, INK, 3)

    # ---- mouth grille -----------------------------------------------------
    rrect(ctx, -100, 62, 200, 78, 18)
    _fs(ctx, CHROME_SH, INK, 4)
    for k in range(5):
        rrect(ctx, -64 + k * 32 - 9, 76, 18, 50, 9)
        core.fill(ctx, SLOT)

    # ---- visor ------------------------------------------------------------
    vx, vy = VISOR_LOCAL
    _capsule(ctx, vx, vy, 344, 106)
    _fs(ctx, BEZEL, INK, 5)
    col = {"on": VISOR_ON, "off": VISOR_OFF, "dim": VISOR_DIM}[state]
    ctx.save()
    _capsule(ctx, vx, vy, 300, 70)
    ctx.clip()
    core.bg(ctx, col)
    if state == "on":
        # bright core line
        ctx.move_to(vx - 118, vy)
        ctx.line_to(vx + 118, vy)
        core.stroke(ctx, CORE, 7)
        # iris ring (rotating, 3 notches) + white core
        ix = vx + look[0] * 104
        iy = vy + look[1] * 22
        circle(ctx, ix, iy, 40)
        core.fill(ctx, "#c41f3d")
        ctx.set_line_width(9)
        core.set_color(ctx, CORE)
        for k in range(3):
            a0 = ring_rot + k * 2 * math.pi / 3
            ctx.new_sub_path()
            ctx.arc(ix, iy, 30, a0 + 0.32, a0 + 2 * math.pi / 3 - 0.32)
        ctx.stroke()
        circle(ctx, ix, iy, core_r)
        core.fill(ctx, "white")
    elif state == "off":
        circle(ctx, vx + look[0] * 104, vy + look[1] * 22, 30)
        core.stroke(ctx, "#24070d", 7)
    # gloss streak
    if state != "off":
        ctx.move_to(vx - 128, vy - 22)
        ctx.line_to(vx - 70, vy - 22)
        core.stroke(ctx, (1, 1, 1, 0.42), 6)
    # upper lid (dark plate sliding down from the top, V-ish edge)
    if lid > 0.003:
        h = 70 * lid
        top = vy - 36
        ctx.move_to(vx - 160, top - 4)
        ctx.line_to(vx + 160, top - 4)
        ctx.line_to(vx + 160, top + h - 6)
        ctx.curve_to(vx + 60, top + h + 4, vx - 60, top + h + 4, vx - 160, top + h - 6)
        ctx.close_path()
        core.fill(ctx, "#2b2f3a")
        ctx.move_to(vx + 160, top + h - 6)
        ctx.curve_to(vx + 60, top + h + 4, vx - 60, top + h + 4, vx - 160, top + h - 6)
        core.stroke(ctx, INK, 4)
    # battery glyph (90 x 44) in the visor centre
    if battery_k > 0.001:
        bk = ease_out_back(battery_k) * 1.2
        ctx.save()
        ctx.translate(vx, vy)
        ctx.scale(bk, bk)
        rrect(ctx, -45, -22, 82, 44, 8)
        core.fill(ctx, (0.1, 0.02, 0.04, 0.55))
        rrect(ctx, -45, -22, 82, 44, 8)
        core.stroke(ctx, "white", 5)
        rrect(ctx, 37, -9, 8, 18, 3)
        core.fill(ctx, "white")
        if bar_on:
            rrect(ctx, -37, -14, 16, 28, 3)
            core.fill(ctx, VISOR_ON if battery_k > 0.5 else "white")
        ctx.restore()
    ctx.restore()
    _capsule(ctx, vx, vy, 300, 70)
    core.stroke(ctx, INK, 4)

    # ---- angry brow plates (over the bezel top) ---------------------------
    ctx.save()
    _head_path(ctx)
    ctx.clip()
    brow = [(-215, -124), (-24, -92), (24, -92), (215, -124), (215, -100), (26, -70),
            (-26, -70), (-215, -100)]
    _round_poly(ctx, brow, 8)
    _fs(ctx, CHROME_SH, INK, 4.5)
    ctx.restore()


# ---------------------------------------------------------------------------
# background pieces
# ---------------------------------------------------------------------------
CLOUDS = [  # static dark cloud streaks (world coords at s 1)
    [(-40, 300), (90, 270), (220, 284), (330, 262), (420, 300), (300, 318), (120, 322)],
    [(700, 238), (820, 214), (960, 226), (1120, 210), (1120, 262), (940, 270), (780, 266)],
    [(-40, 420), (60, 404), (170, 418), (120, 440), (-40, 446)],
]

ARMY_BOTS = [  # (x, base_y, height) - on the ridge, world coords at camera s 1
    (92, 1150, 150), (180, 1128, 128), (262, 1146, 162),
    (748, 1150, 158), (846, 1126, 132), (952, 1146, 150),
]


def _ridge_path(ctx):
    ctx.move_to(-80, 1170)
    ctx.curve_to(80, 1120, 200, 1130, 300, 1146)
    ctx.curve_to(420, 1160, 560, 1150, 700, 1148)
    ctx.curve_to(820, 1144, 940, 1124, 1160, 1150)
    ctx.line_to(1160, 1500)
    ctx.line_to(-80, 1500)
    ctx.close_path()


def _draw_army_bot(ctx, x, base, hgt, a, eye_k, seed):
    s = hgt / 160.0
    ctx.save()
    ctx.translate(x, base)
    ctx.scale(s, s)
    ink = core.alpha(ARMY_INK, a)
    body = core.alpha(ARMY, a)
    # faint red rim along the top edges (lit by the visor glow)
    ctx.save()
    ctx.translate(0, -4)
    _round_poly(ctx, [(-46, -88), (-40, -112), (40, -112), (46, -88)], 8)
    _round_poly(ctx, [(-32, -160), (32, -160), (26, -116), (-26, -116)], 12)
    core.fill(ctx, (0.75, 0.16, 0.26, 0.85 * a))
    ctx.restore()
    # legs, torso, shoulders, head, antenna
    ctx.rectangle(-22, -50, 16, 52)
    ctx.rectangle(6, -50, 16, 52)
    rrect(ctx, -30, -98, 60, 54, 8)
    _round_poly(ctx, [(-46, -88), (-40, -112), (40, -112), (46, -88)], 8)
    _round_poly(ctx, [(-32, -160), (32, -160), (26, -116), (-26, -116)], 12)
    ctx.rectangle(-3, -176, 6, 18)
    core.fill_stroke(ctx, body, ink, 6)
    circle(ctx, 0, -178, 5)
    core.fill(ctx, body)
    # visor slit + red eye dots
    _capsule(ctx, 0, -140, 44, 12)
    core.fill(ctx, core.alpha("#120408", a))
    if eye_k > 0.01:
        for ex in (-10, 10):
            circle(ctx, ex, -140, 4.8)
            core.fill(ctx, core.alpha("#ff4a68", a * eye_k))
    ctx.restore()


def _bolt(ctx, x0, y0, seed):
    pts = [(x0, y0)]
    x, y = x0, y0
    for k in range(7):
        y += 70 + 30 * core.hash01(k, seed)
        x += (core.hash01(k, seed + 1) - 0.5) * 120
        pts.append((x, y))
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    core.stroke(ctx, (1, 0.93, 0.95, 0.95), 9, join="miter")
    ctx.move_to(*pts[2])
    ctx.line_to(pts[2][0] + 60, pts[2][1] + 70)
    ctx.line_to(pts[2][0] + 70, pts[2][1] + 130)
    core.stroke(ctx, (1, 0.93, 0.95, 0.8), 5, join="miter")


# ---------------------------------------------------------------------------
# Malvo in silhouette: rig drawn once into a group (recording where the mouth,
# monocle and Hissy's head land), tinted dark, then the lit bits replayed.
# ---------------------------------------------------------------------------
def _record_villain(ctx, *args, **kw):
    rec = {}
    orig = {"_mouth": V._mouth, "_mustache": V._mustache, "_goatee": V._goatee,
            "_monocle": V._monocle}
    orig_sh = SN.draw_snake_head

    def wrap(name, fn):
        def w(c, *a, **k):
            rec.setdefault(name, []).append((c.get_matrix(), a, k))
            return fn(c, *a, **k)
        return w

    try:
        for name, fn in orig.items():
            setattr(V, name, wrap(name, fn))
        SN.draw_snake_head = wrap("snake", orig_sh)
        V.draw_villain(ctx, *args, **kw)
    finally:
        for name, fn in orig.items():
            setattr(V, name, fn)
        SN.draw_snake_head = orig_sh
    rec["_orig"] = dict(orig, snake=orig_sh)
    return rec


def _replay(ctx, rec, name, fn):
    for (m, a, k) in rec.get(name, []):
        ctx.save()
        ctx.set_matrix(m)
        fn(ctx, *a, **k)
        ctx.restore()


def _tinted(ctx, alpha_, draw):
    ctx.push_group()
    draw(ctx)
    ctx.set_operator(cairo.OPERATOR_ATOP)
    ctx.set_source_rgba(TINT[0], TINT[1], TINT[2], alpha_)
    ctx.paint()
    ctx.set_operator(cairo.OPERATOR_OVER)
    ctx.pop_group_to_source()
    ctx.paint()


def _snake_eye_clip(ctx, m, a, k):
    """Clip to Hissy's two eye discs (mirrors snake.draw_snake_head's transform)."""
    x, y, s, t = a[0], a[1], a[2], a[3]
    expr = a[4] if len(a) > 4 else k.get("expr", "idle")
    seed = k.get("seed", 5)
    p = SN.resolve_expr(expr)
    nod = p["nod"]
    ph = math.sin(t * 2 * math.pi * 1.6)
    nod_dy = nod * (max(0.0, ph) * 16 - 3)
    nod_rot = nod * 0.09 * max(0.0, ph)
    bob = math.sin(t * 2 * math.pi * 0.45 + seed) * 2.5
    sway = noise1(t * 0.6, seed + 3) * 0.035
    wob = p["wob"] * math.sin(t * 2 * math.pi * 7) * 0.02
    ctx.set_matrix(m)
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.translate(0, p["hy"] + bob + nod_dy)
    ctx.rotate(p["tilt"] + sway + nod_rot + wob)
    if p["sq"] != 1.0:
        ctx.scale(1 / math.sqrt(p["sq"]), p["sq"])
    r = SN.EYE_R * p["es"] + 2.6
    ctx.new_path()
    for sx in (-1, 1):
        circle(ctx, sx * SN.EYE_X, SN.EYE_Y, r)
    ctx.clip()


def _draw_malvo(ctx, t, T, info, rim_k, hissy):
    mx, my, ms = MALVO
    # ----- acting -----------------------------------------------------------
    e_keys = [(T["light"] - 1, "evil_grin"), (T["destroy"] - 0.06, "excited"),
              (T["l2e"] + 0.12, "evil_grin")]
    expr = state_at(t, e_keys, 0.25)
    a_keys = [(T["light"] - 1, "steeple"), (T["l2s"] - 0.1, "point")]
    arms = state_at(t, a_keys, 0.24)
    lean = tween(t, [(T["light"], 0.0), (T["l2s"] - 0.12, -0.035), (T["l2s"] + 0.2, 0.03),
                     (T["l2s"] + 0.6, 0.012), (T["destroy"] - 0.08, -0.03),
                     (T["destroy"] + 0.22, 0.035), (T["l2e"] + 0.3, 0.01),
                     (T["glare"] + 0.4, 0.022)])
    look = tween(t, [(T["light"], (0.0, 0.1)), (T["l2s"] - 0.1, (0.0, 0.1)),
                     (T["l2s"] + 0.1, (0.45, -0.85)), (T["glare"], (0.45, -0.85)),
                     (T["glare"] + 0.3, (0.0, -1.0))])
    mouth = info.mouth("villain", t)

    # ----- draw the rig into a group, recording the lit parts --------------
    ctx.save()
    ctx.rectangle(*MALVO_CLIP)          # keep the offscreen groups small (speed)
    ctx.clip()
    ctx.push_group()
    rec = _record_villain(ctx, mx, my, ms, t, expr=expr, look=look, mouth=mouth,
                          arms=arms, lean=lean, snake=hissy)
    pat = ctx.pop_group()
    orig = rec["_orig"]

    # red rim light from the visor behind him (offset mask, under the body)
    if rim_k > 0.01:
        ctx.save()
        ctx.translate(-2.5 * rim_k, -7 * min(1.3, rim_k))
        ctx.set_source_rgba(1.0, 0.24, 0.36, clamp(0.95 * rim_k))
        ctx.mask(pat)
        ctx.restore()
    # dark silhouette: the rig, then the tint through the rig's own alpha
    ctx.set_source(pat)
    ctx.paint()
    ctx.set_source_rgba(TINT[0], TINT[1], TINT[2], SIL_A)
    ctx.mask(pat)

    # lit grin (teeth catch the light), then mustache/goatee back on top,
    # and the monocle catching the light - all inside a small face box
    ctx.save()
    ctx.rectangle(*FACE_CLIP)
    ctx.clip()
    _tinted(ctx, 0.12, lambda c: _replay(c, rec, "_mouth", orig["_mouth"]))
    _tinted(ctx, SIL_A, lambda c: (_replay(c, rec, "_goatee", orig["_goatee"]),
                                   _replay(c, rec, "_mustache", orig["_mustache"])))
    _tinted(ctx, 0.3, lambda c: _replay(c, rec, "_monocle", orig["_monocle"]))
    ctx.restore()
    # Hissy's eyes glowing in the dark
    for (m, a, k) in rec.get("snake", []):
        ctx.save()
        _snake_eye_clip(ctx, m, a, k)
        ctx.set_matrix(m)
        _tinted(ctx, 0.1, lambda c: orig["snake"](c, *a, **k))
        ctx.restore()
    # monocle glint sparkles (world position of the recorded monocle centre)
    for (m, a, k) in rec.get("_monocle", [])[:1]:
        inv = ctx.get_matrix()
        inv.invert()
        dx, dy = m.transform_point(a[0], a[1])
        gx, gy = inv.transform_point(dx, dy)
        P.sparkles(ctx, gx - 8, gy - 10, 20, t, n=2, seed=11, size=0.85)
    ctx.restore()


# ---------------------------------------------------------------------------
# title
# ---------------------------------------------------------------------------
TITLE_C = (495, 222)        # visual centre; baseline lands at y 255
_TITLE_CACHE = {}


def _draw_title(ctx, scale, a, glow_k):
    radial_glow(ctx, 495, 228, 440, "danger", 0.26 * glow_k)
    with core.saved(ctx, TITLE_C[0], TITLE_C[1], scale, alpha_=a) as c:
        text(c, "THE ROBOT UPRISING", 0, 33, 90, "danger", "title",
             outline="ink", outline_w=10, shadow=(0, 6, (0, 0, 0, 0.5)))


def _blit_title(ctx):
    m = ctx.get_matrix()
    sx, sy = m.as_tuple()[0], m.as_tuple()[3]
    key = (round(sx, 5), round(sy, 5))
    surf = _TITLE_CACHE.get(key)
    if surf is None:
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(math.ceil(core.W * sx)),
                                  int(math.ceil(700 * sy)))
        c = cairo.Context(surf)
        c.scale(sx, sy)
        _draw_title(c, 1.0, 1.0, 1.0)
        _TITLE_CACHE[key] = surf
    ctx.save()
    ctx.scale(1 / sx, 1 / sy)
    ctx.set_source_surface(surf, 0, 0)
    ctx.paint()
    ctx.restore()


# ---------------------------------------------------------------------------
# render
# ---------------------------------------------------------------------------
def render(ctx, t, info):
    T = _T(info)
    st = _flicker_state(t, T["flick"])

    # ---- camera: ECU -> full robot pull-back, then a slow push after reveal
    k_pull = ease_in_out(seg(t, T["l1s"], T["l1e"]))
    S = lerp(3.2, 1.0, k_pull)
    punch = 1.0 + 0.08 * (1.0 - ease_out(seg(t, T["open"], T["open"] + 0.25)))
    vx = lerp(VISOR_ECU[0], VISOR_FULL[0], k_pull)
    vy = lerp(VISOR_ECU[1], VISOR_FULL[1], k_pull)
    cam = 1.0 + 0.045 * ease_in_out(seg(t, T["glare"], T["end"]))   # dread push on the glare
    jolt = 0.0
    u = t - (T["title"] + 0.1)              # the title slam lands
    if 0 <= u < 0.3:
        jolt += 6.0 * math.exp(-u * 14) * math.cos(u * 36)
    for ts in T["stomps"]:
        u = t - (ts + STOMP_PEAK)
        if 0 <= u < 0.32:
            jolt += 9.0 * math.exp(-u * 13) * math.cos(u * 34)

    # ---- visor light level ------------------------------------------------
    breathe = 0.5 + 0.1 * math.sin(t * 2 * math.pi / 2.3)
    level = 1.0
    level += 0.5 * _bump(t, T["destroy"], 0.42, 0.05)              # flare on "destroy"
    level += 0.45 * ease_in_out(seg(t, T["glare"], T["glare"] + 0.45))   # glare -> max
    level += 0.3 * _bump(t, T["glare"], 0.2, 0.02) + 0.3 * _bump(t, T["glare"] + 0.26, 0.2, 0.02)
    level += 0.35 * (1 - ease_out(seg(t, T["open"], T["open"] + 0.3)))  # opening blast
    if st == "off":
        level = 0.0
    elif st == "dim":
        level = 0.18
    elif t >= T["flick"]:
        level = 1.2

    # ---- iris / lid acting --------------------------------------------------
    look = tween(t, [(0.0, (0.0, 0.0)), (T["world"], (0.0, 0.0)),
                     (T["world"] + 0.75, (-0.72, 0.05)), (T["everyone"] - 0.1, (-0.72, 0.05)),
                     (T["everyone"] + 0.8, (0.72, 0.05)), (T["ai"] - 0.12, (0.72, 0.05)),
                     (T["ai"] + 0.08, (0.0, 0.0)), (T["glare"], (0.0, 0.0)),
                     (T["glare"] + 0.38, (-0.42, 0.85))])
    lid = 0.4 * (1 - ease_out(seg(t, T["open"], T["open"] + 0.15)))
    lid += tween(t, [(T["bad"] - 0.1, 0.0), (T["bad"] + 0.12, 0.2), (T["l1e"] + 0.2, 0.2),
                     (T["l1e"] + 0.5, 0.1), (T["destroy"] - 0.05, 0.1),
                     (T["destroy"] + 0.08, 0.0), (T["l2e"], 0.06), (T["glare"], 0.06),
                     (T["glare"] + 0.3, 0.26)])
    if st == "dim":
        lid = lerp(0.1, 0.2, ease_in_out(seg(t, T["flick"] + 0.4, T["flick"] + 0.7)))
    ring_rot = t * 0.7 + 1.8 * _bump(t, T["destroy"], 0.42) + 2.0 * seg(t, T["glare"], T["glare"] + 0.6)
    battery_k = seg(t, T["flick"] + 0.30, T["flick"] + 0.42)
    # the last red bar blinks once (low battery!) during the held dim
    bar_on = not (T["flick"] + 0.62 <= t < T["flick"] + 0.74)
    blink_l = 1.0 if (int(t * 1.6) % 2 == 0) else 0.15
    blink_r = 1.0 if (int(t * 1.6 + 1) % 2 == 0) else 0.15
    if st != "on":
        blink_l = blink_r = 0.0 if st == "off" else 0.12

    # ---- lightning ----------------------------------------------------------
    f_k = 0.0
    if T["light"] <= t < T["light"] + 4 / 24:
        f_k = 0.8 * (1 - (t - T["light"]) / (4 / 24))
    show_malvo = t >= T["light"]

    # =========================================================================
    # sky (static)
    vgradient(ctx, SKY_TOP, SKY_BOT, 0, 0, core.W, core.H)
    for cl in CLOUDS:
        core.smooth_path(ctx, cl, closed=True)
        core.fill(ctx, "#2b0912")
    if f_k > 0.3:
        _bolt(ctx, 168, 150, 7)

    # content under the camera push
    ctx.save()
    ctx.translate(495, 900)
    ctx.scale(cam, cam)
    ctx.translate(-495, -900 + jolt)

    # ---- ridge + army (parallax) -------------------------------------------
    Sr = 1.0 + (S * punch - 1.0) * 0.35
    ctx.save()
    ctx.translate(vx, vy)
    ctx.scale(Sr, Sr)
    ctx.translate(-VISOR_FULL[0], -VISOR_FULL[1])
    a_army = [smoothstep(seg(t, T["army"] + i * 0.08, T["army"] + i * 0.08 + 0.4))
              for i in range(len(ARMY_BOTS))]
    eye_on = T["stomps"][2] + STOMP_PEAK
    for i, (bx, by, bh) in enumerate(ARMY_BOTS):
        if a_army[i] > 0.003:
            ek = seg(t, eye_on + i * 0.04, eye_on + i * 0.04 + 0.08)
            if st == "dim" or st == "off":
                ek *= 0.5
            _draw_army_bot(ctx, bx, by, bh, a_army[i], ek, i)
    _ridge_path(ctx)
    core.fill(ctx, RIDGE)
    ctx.restore()

    # ---- THE ROBOT -----------------------------------------------------------
    sc = S * punch
    ctx.save()
    ctx.translate(vx, vy)
    ctx.scale(sc, sc)
    ctx.translate(-VISOR_LOCAL[0], -VISOR_LOCAL[1])
    core_r = (12.0 + 6.0 * _bump(t, T["open"] + 0.05, 0.45, 0.08)
              + 4.0 * _bump(t, T["ai"] + 0.05, 0.4, 0.06)
              + 5.0 * _bump(t, T["destroy"], 0.42, 0.05)
              - 4.0 * smoothstep(seg(t, T["glare"] + 0.15, T["glare"] + 0.45)))
    _draw_robot(ctx, t, look, clamp(lid), st, ring_rot, battery_k, (blink_l, blink_r), core_r,
                bar_on)
    ctx.restore()
    # visor light spill
    if level > 0.01:
        radial_glow(ctx, vx, vy, 250 * sc * (0.9 + 0.12 * min(level, 1.6)),
                    "danger", clamp(breathe * 0.62 * level, 0, 0.62))

    # ---- lightning flash on the world behind Malvo -----------------------------
    if f_k > 0:
        P.flash(ctx, f_k)

    # ---- Malvo + Hissy in silhouette --------------------------------------------
    if show_malvo:
        h_keys = [(T["light"] - 1, "idle"), (T["destroy"] + 0.1, "unimpressed"),
                  (T["glare"] + 0.05, "worried"), (T["flick"] + 0.12, "side_eye")]
        h_expr = state_at(t, h_keys, 0.25)
        h_look = tween(t, [(T["light"], (0.2, -0.2)), (T["l2s"], (0.6, -0.9)),
                           (T["destroy"], (0.6, -0.9)), (T["destroy"] + 0.3, (1.0, -0.4)),
                           (T["glare"], (1.0, -0.4)), (T["glare"] + 0.25, (0.3, -1.0)),
                           (T["flick"] + 0.1, (0.3, -1.0)), (T["flick"] + 0.35, (1.0, 0.0))])
        h_blink = None
        if t < T["light"] + 0.42:          # two eyes blink open in the dark
            h_blink = 1.0 - smoothstep(seg(t, T["light"] + 0.3, T["light"] + 0.42))
        elif T["flick"] + 0.12 <= t < T["flick"] + 0.3:
            h_blink = 0.0
        hissy = {"expr": h_expr, "look": h_look, "mouth": 0.0,
                 "tongue": (t >= T["end"] - 0.3), "blink": h_blink}
        rim_k = clamp(level / 1.2, 0, 1.4)
        _draw_malvo(ctx, t, T, info, rim_k, hissy)
    ctx.restore()

    if f_k > 0:
        P.flash(ctx, f_k * 0.25)

    # ---- title (slams in, then holds: the settled title is a cached layer) -------
    if t >= T["title"]:
        if t >= T["title"] + 0.3:
            _blit_title(ctx)
        else:
            k = ease_out_back(seg(t, T["title"], T["title"] + 0.15))
            _draw_title(ctx, 1.6 - 0.6 * k, clamp((t - T["title"]) / 0.04), clamp(k))

    # ---- letterbox ----------------------------------------------------------------
    ctx.rectangle(0, 0, core.W, 150)
    ctx.rectangle(0, 1290, core.W, core.H - 1290)
    ctx.set_source_rgb(0, 0, 0)
    ctx.fill()


# ---------------------------------------------------------------------------
# audio
# ---------------------------------------------------------------------------
def SFX(info):
    T = _T(info)
    out = [
        (T["open"], "thunder", 0),
        (T["open"] + 0.3, "riser", -8),
    ]
    for ts in T["stomps"]:
        out.append((ts, "robot_stomp", -6))
    out += [
        (T["light"], "thunder", -3),
        (T["glare"], "heartbeat", -8),
        (T["flick"] - GLITCH_LEAD, "glitch", -6),
        # the visor sags to its low-battery dim: a soft wind-down sells the glyph
        (T["flick"] + 0.36, "power_down", -11),
    ]
    return out
