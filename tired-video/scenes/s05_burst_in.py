"""s05 -- "Bursting in on Tiredness" (music: sneaky).

Shot list (all times derived from cues / lines, never hard-coded):

  1  music   bedroom, slow push from the room onto Tiredness gaming at the desk
             (back to the door), headphones on, notes leaking from the cup.
  2  crawl   hallway: Emb scurries up the stairs on all fours (cage handle in his
             teeth), camera tracking; a violet tail slips under the glowing door
             gap; his head snaps to it; he scrambles to the door.
  3  burst   bedroom side of the door: it bangs open, Emb lunges in.
  4  freeze  snap-in: white flash, shock lines, hair on end, beet red, tiny pupils.
     notice  his pupils slide toward Tiredness ...
  5          ... insert: Tiredness, headphones on, oblivious, notes leaking.
  6  l01     back on Emb: relief (lids drop, blush 1 -> .5, shoulders drop),
             whispered "He can't hear me. Perfect." + a sly glasses glint.
  7  search  bed (head under, butt up) -> laundry lift; camera pans along.
  8          closet close-up: panel slides, rummage, a few clothes fly out.
  9  reveal  pull back: Tiredness RIGHT behind him, arms crossed, squinting,
             headphones round his neck; the empty gaming chair still spinning.
 10  tap     tighter two-shot: tap-tap on the shoulder; Emb stiffens, eyes slide.
 11  l02     wide: squash -> leap -> BONK on the ceiling (plaster) -> fall ->
             butt landing, dizzy stars; Tiredness's pupils track up and down.
 12  l03     two-shot: "Hi."  then footTap: foot tapping, one brow lifts.
"""
import math

import cairocffi as cairo

from engine import core, sets, props, fx, human
from engine.core import seg, tween, state_at, clamp, lerp, ease_out_back, ease_in, ease_out, ease_in_out
from engine.human import A, IK, L

BM = sets.BEDROOM_MARKS
HM = sets.HALL_MARKS
S = 0.75                      # character scale in both sets
BEAT = 60.0 / 104.0           # "sneaky" tempo (head bob)
CAGE_S = 0.42                 # cage scale next to a person at S
TH = 955.0                    # Tiredness height (s=1)
EH = 1045.0                   # Embarrassment height (s=1)

# --- stage positions (world px)
T_SEAT = BM["chair_seat"]
T_GAME = (T_SEAT[0], human.ground_from_seat("tired", T_SEAT[1], S))
E_DOOR = (360, 1452)          # Emb one step into the room
E_BED = (1170, 1548)          # kneeling at the bed
E_LAUNDRY = (1105, 1540)
E_CLOSET = (745, 1536)
T_BEHIND = (1010, 1538)        # Tiredness right behind him
E_FLOOR = (705, 1552)         # Emb's landing spot (butt)
CAGE_FLOOR = (520, 1548)      # where the cage sits once he puts it down
CHAIR_DX = -300               # he rolled the chair back when he got up


# ---------------------------------------------------------------------------
# timing
# ---------------------------------------------------------------------------
class _T:
    pass


def cues(info):
    c = _T()
    c.music = info.cue("music")
    c.crawl = info.cue("crawl")
    c.burst = info.cue("burst")
    c.freeze = info.cue("freeze")
    c.notice = info.cue("notice")
    c.l1 = info.line("s05_l01")
    c.search = info.cue("search")
    c.reveal = info.cue("reveal")
    c.tap = info.cue("tap")
    c.l2 = info.line("s05_l02")
    c.ceil = info.cue("ceiling")
    c.land = info.cue("land")
    c.l3 = info.line("s05_l03")
    c.foot = info.cue("footTap")
    c.end = info.dur
    # derived beats
    c.pov0 = c.notice + 0.32                    # cut to the headphones insert
    c.pov1 = c.l1.start + 0.05                  # back on Emb
    c.srch_b = c.search + 1.62                  # cut to the closet close-up
    c.tap1 = c.tap + 0.42                       # first fingertip tap (tap_tap SFX)
    c.launch = c.l2.start + 0.12                # squash done, he leaves the floor
    c.hang = 0.12                               # stuck to the ceiling
    c.hi0 = c.l3.start - 0.28                   # cut to the "Hi." two-shot
    c.t_up = c.srch_b + 0.1                     # (unseen) Tiredness gets up -> chair spins
    return c


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------
def slow_blink(t, t0, close=0.3, hold=0.18, open_=0.38):
    """None outside the blink (auto blinks), else 0..1."""
    if t < t0 or t > t0 + close + hold + open_:
        return None
    return tween(t, [(t0, 0.0), (t0 + close, 1.0), (t0 + close + hold, 1.0),
                     (t0 + close + hold + open_, 0.0)])


def ik_target(who, s, ground, target, side, turn, tz=0.2):
    """Ground-IK (tx, ty, tz) so a hand lands on a screen point (front-ish arm)."""
    H = human.CHARS[who]["height"]
    phi = clamp(turn, -1.6, 1.6) * human.TURN_RAD
    sgn = -1.0 if side == "l" else 1.0
    X = (target[0] - ground[0]) / s
    tx = (X - tz * H * math.sin(phi)) / (sgn * H * math.cos(phi))
    ty = (ground[1] - target[1]) / (s * H)
    return tx, ty, tz


def chair_spin(t, c):
    """Empty chair: spun hard when he got up, still slowly turning later."""
    if t < c.t_up:
        return 0.0
    tau = 1.7
    return -4.5 * tau * (1 - math.exp(-(t - c.t_up) / tau))


def cage(ctx, x, y, t, rot=0.0, s=CAGE_S, swing=0.0):
    """Open, empty carrier (handle top at x, y); the door hangs and swings."""
    door = 0.72 + 0.12 * math.sin(t * 5.0) * swing
    props.cage(ctx, x, y, s, t, door=door, latch="open", empty=True, rot=rot)


def hair_spikes(ctx, top, head, s, k, t):
    """Ginger hair standing on end (drawn BEHIND the head)."""
    if k <= 0.01:
        return
    hx, hy = head
    tx, ty = top
    base_r = math.hypot(tx - hx, ty - hy) * 0.78
    col = core.PAL["e_hair"]
    for i in range(9):
        a = -math.pi / 2 + (i - 4) * 0.27
        wig = 0.06 * math.sin(t * 31 + i * 1.7)
        a += wig
        r0 = base_r * 0.75
        L_ = (95 + 30 * core.hash01(i, 5)) * s * k
        bx, by = hx + math.cos(a) * r0, hy + math.sin(a) * r0
        w = 30 * s
        nx, ny = -math.sin(a), math.cos(a)
        tipx, tipy = hx + math.cos(a) * (r0 + base_r * 0.5 + L_), hy + math.sin(a) * (r0 + base_r * 0.5 + L_)
        ctx.move_to(bx + nx * w, by + ny * w)
        ctx.line_to(tipx, tipy)
        ctx.line_to(bx - nx * w, by - ny * w)
        ctx.close_path()
    core.set_color(ctx, col)
    ctx.fill_preserve()
    core.stroke(ctx, "ink", 5.5 * s)


def with_behind(ctx, draw_fn, behind_fn):
    """Draw draw_fn into a group (returns anchors), paint behind_fn(anchors) first."""
    ctx.push_group()
    a = draw_fn()
    pat = ctx.pop_group()
    behind_fn(a)
    ctx.set_source(pat)
    ctx.paint()
    return a


# ---------------------------------------------------------------------------
# shot 1 + 5: Tiredness gaming at the desk
# ---------------------------------------------------------------------------
def draw_room_gaming(ctx, t, c, notes=0.9):
    sets.bedroom(ctx, t, layer="bg")
    return draw_gamer(ctx, t, notes)


def draw_gamer(ctx, t, notes=0.9):
    bob = math.sin(2 * math.pi * t / BEAT)
    face = {"head_nod": 0.03 * bob, "head_tilt": 0.015 * bob, "curve": 0.12, "lower": 0.12}
    a = human.draw_person(ctx, "tired", T_GAME[0], T_GAME[1], S, t, pose="game", expr="bored",
                          turn=1.0, headphones="on", face=face, look=(0.62, -0.02))
    sets.bedroom(ctx, t, layer="fg", parts=("desk", "chair"))
    hx, hy = a["head"]
    cup = (hx - 112 * S, hy + 10 * S)
    fx.music_notes(ctx, cup[0], cup[1] - 30 * S, 1.25, t, notes, direction=-1, seed=5)
    return a


def shot_music(ctx, t, info, c):
    k = ease_in_out(seg(t, c.music, c.crawl))
    cx, cy, z = lerp(1330, 1590, k), lerp(995, 975, k), lerp(0.74, 1.05, k)
    with core.cache_steps(2):
        with core.camera(ctx, cx, cy, z):
            draw_room_gaming(ctx, t, c)


def shot_pov(ctx, t, info, c):
    k = ease_out(seg(t, c.pov0, c.pov1 + 0.3))
    with core.camera(ctx, lerp(1560, 1580, k), lerp(1010, 995, k), lerp(1.42, 1.5, k)):
        draw_room_gaming(ctx, t, c, notes=1.0)


# ---------------------------------------------------------------------------
# shot 2: hallway crawl
# ---------------------------------------------------------------------------
SLOPE = HM["stair_slope"]


def stair_y(x):
    """Smoothed stair profile (tread centres), landing at the top."""
    top_x = HM["stair_top"][0]
    if x >= top_x + 30:
        return HM["floor_y"] + 4
    y = 1365 + (top_x - x) * math.tan(SLOPE)
    if x > top_x - 40:
        k = smoothstep_((x - (top_x - 40)) / 70.0)
        y = lerp(y, HM["floor_y"] + 4, k)
    return y


def smoothstep_(u):
    return core.smoothstep(clamp(u))


def tail_slip(ctx, t, t0, dur=0.42):
    """A thin violet tail poking out from under the door gap, whipping, then sucked in."""
    if t < t0 - 0.3 or t > t0 + dur:
        return
    gx = HM["tail_slip"][0]
    gy = HM["floor_y"] - 7
    vis = 1.0 - ease_in(seg(t, t0, t0 + dur))
    if vis <= 0.02:
        return
    L_ = 225 * vis
    n = 12
    pts = []
    for i in range(n + 1):
        u = i / n
        d = u * L_
        wav = math.sin(t * 24 - u * 5.5) * 30 * u * (0.45 + 0.55 * vis)
        pts.append((gx - d * 0.7 + wav * 0.3, gy + d * 0.42 + wav * 0.5))
    # tapered body: offset the centre line both ways
    left, right = [], []
    for i, (px, py) in enumerate(pts):
        j0, j1 = max(0, i - 1), min(n, i + 1)
        dx, dy = pts[j1][0] - pts[j0][0], pts[j1][1] - pts[j0][1]
        dl = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / dl, dx / dl
        w = lerp(11.0, 3.0, i / n)
        left.append((px + nx * w, py + ny * w))
        right.append((px - nx * w, py - ny * w))
    core.poly(ctx, left + right[::-1])
    core.fill_stroke(ctx, core.PAL["thing_fur"], "ink", 4)
    # a little fuzzy tuft at the tip
    ex, ey = pts[-1]
    core.circle(ctx, ex, ey, 8)
    core.fill_stroke(ctx, core.PAL["thing_dk"], "ink", 3.5)
    # the root disappears into the glowing gap under the door
    x, y, w, h = HM["light_gap"]
    ctx.rectangle(gx - 40, y, 80, h)
    core.fill(ctx, "#fff3c4")
    ctx.rectangle(gx - 40, y + 3, 80, 5)
    core.fill(ctx, "#ffffff")
    # whip ticks
    if vis > 0.35:
        for j in range(3):
            ctx.move_to(ex - 24 - j * 6, ey - 16 + j * 14)
            ctx.line_to(ex - 50 - j * 8, ey - 22 + j * 16)
        core.stroke(ctx, core.alpha("ink", 0.55 * vis), 4)


def shot_hall(ctx, t, info, c):
    t0 = c.crawl
    tl = t - t0
    D = c.burst - c.crawl
    t_land = 0.95            # reaches the landing
    t_tail = 0.92            # tail slips (absolute: t0 + t_tail)
    t_see = 1.06             # his head snaps to it
    t_go = 1.36              # scramble up and dash
    rate = 2.0               # scurry: crawl cycle at double speed
    sp = human.cycle_speed("embar", "crawl", 0.95) * S * rate
    # path: along the stairs (rotated), then the landing
    x0 = 330.0
    if tl < t_land:
        x = x0 + sp * math.cos(SLOPE) * tl
    else:
        x = x0 + sp * math.cos(SLOPE) * t_land + sp * 0.55 * (min(tl, t_go) - t_land)
    rot = -0.2 * (1 - smoothstep_((x - 640) / 120.0))
    gy = stair_y(x - 70)
    # scramble to the door
    kgo = seg(tl, t_go, D)
    if tl > t_go:
        x += 420 * ease_in(kgo) * kgo + 120 * kgo
    # camera tracks
    cx = lerp(520, 845, ease_in_out(seg(tl, 0.0, 1.05)))
    cy = lerp(1390, 1170, ease_in_out(seg(tl, 0.0, 1.05)))
    with core.camera(ctx, cx, cy, 1.15):
        sets.hallway_upstairs(ctx, t, layer="back")
        sets.hallway_upstairs(ctx, t, layer="hall")
        sets.hallway_upstairs(ctx, t, layer="fg", parts=("railing",))
        tail_slip(ctx, t, t0 + t_tail)
        see = seg(tl, t_see, t_see + 0.12)
        if tl < t_go:
            pose = {"base": "crawl", "rot": rot, "lean": 1.5, "neck": -0.85 + 0.55 * see, "nod": -0.25 - 0.15 * see}
            pose_t = rate * tl
            expr = state_at(tl, [(0, "whisper"), (t_see, "alarmed")], 0.12)
            look = tween(tl, [(0, (0.4, -0.25)), (t_tail + 0.02, (0.4, -0.25)),
                              (t_tail + 0.1, (0.9, 0.15))])
            face = {"teeth": 1.0, "open": 0.06, "lip_up": 0.25, "width": 0.25, "pupil": -0.35 * see,
                    "eye_size": 0.12 * see, "squash": -0.06 * see}
            blush = 0.35
        else:
            pose = ({"base": "crawl", "rot": 0.0, "neck": -0.3, "nod": -0.4}, "run_panic",
                    smoothstep_(seg(tl, t_go, t_go + 0.22)))
            pose_t = tl - t_go
            expr = "panic"
            look = (0.85, 0.0)
            face = {"teeth": 1.0, "open": 0.06, "lip_up": 0.25, "width": 0.25, "pupil": -0.3}
            blush = 0.5
        a = human.draw_person(ctx, "embar", x, gy, S, t, pose=pose, pose_t=pose_t, expr=expr,
                              look=look, face=face, turn=0.8, blush=blush, sweat=0.4,
                              shadow=tl >= t_land)
        # cage handle clenched in his teeth, hanging under his chin
        mx, my = a["mouth"]
        sway = 0.12 * math.sin(t * 7.0)
        cage(ctx, mx + 2, my - 10, t, rot=sway, swing=1.0, s=0.34)
        if tl > t_see and tl < t_see + 0.5:
            fx.emote(ctx, "exclaim", a["top"][0] + 40, a["top"][1] - 70, 0.75, t, t0 + t_see, 0.5)
        if tl > t_go:
            fx.motion_lines(ctx, a["hip"][0] - 60, a["hip"][1] - 60, 0.0, 260, t, kgo, seed=2)


# ---------------------------------------------------------------------------
# shots 3/4/6: the doorway (burst, freeze, relief + line)
# ---------------------------------------------------------------------------
FREEZE_POSE = {"base": "stand", **A("l", 0.25, 0.72, 0.25, h="splay"), **A("r", 0.22, 0.6, 0.2, h="splay"),
               **L("l", o=0.12, k=0.0), **L("r", o=0.12, k=0.0),
               "hunch": 1.0, "posture": 0.0, "chest": -0.12, "nod": -0.12, "sway": 0.0, "breath": 0.0,
               "lift": 10.0}
RELIEF_POSE = {"base": "stand", **A("l", 0.04, 0.12, 0.22), **A("r", 0.06, 0.14, 0.18, h="grip"),
               "hunch": -0.1, "lean": 0.06, "nod": 0.12, "neck": 0.1, "breath": 1.4}


def emb_doorway(ctx, t, c, info):
    """Emb at the doorway from the burst to the end of his line."""
    tf = c.freeze
    x, y = E_DOOR
    # ---- body
    if t < tf:
        k = ease_out(seg(t, c.burst + 0.04, c.burst + 0.26))
        x = lerp(300, E_DOOR[0], k)
        y = lerp(1338, E_DOOR[1], k)
        pose = ("catch", "run_panic", 0.35)
        pose_t = 0.12
        expr = "panic"
        blush = 0.55
        look = (0.6, 0.0)
        face = {"open": 0.15}
        turn = 0.55
    else:
        rel0 = c.pov1 - 0.05
        pose = state_at(t, [(tf, FREEZE_POSE), (rel0, RELIEF_POSE)], 0.4)
        pose_t = None
        turn = 0.3
        # face
        if t < c.pov1 - 0.1:
            expr = "frozen_shock"
            look = tween(t, [(c.notice, (0.0, 0.0)), (c.notice + 0.22, (1.05, 0.08))])
            face = {"head_turn": 0.2 * ease_in_out(seg(t, c.notice + 0.16, c.notice + 0.42))}
        else:
            # relief: lids drop, a big exhale, then the sly whisper ... "Perfect."
            w = info.word_at(t, "s05_l01")
            t_perf = c.l1.end - 0.5
            if w >= 4:
                t_perf = min(t_perf, t)
            expr = state_at(t, [(rel0, "frozen_shock"), (rel0 + 0.02, "relieved"), (t_perf, "fake_cool")], 0.3)
            look = tween(t, [(rel0, (1.0, 0.05)), (rel0 + 0.35, (0.7, 0.12)), (c.l1.start + 0.75, (0.2, 0.05)),
                             (c.l1.start + 1.0, (0.85, 0.0))])
            exhale = math.sin(math.pi * seg(t, rel0, rel0 + 0.7))
            face = {"head_turn": 0.14, "lid": 0.12 * (1 - seg(t, c.l1.start + 0.6, c.l1.start + 0.9)),
                    "cheek": 0.35 * exhale, "head_nod": 0.08 * exhale}
            if t >= t_perf:
                face.update({"smirk": 0.3, "brow_l": 0.15})
        blush = tween(t, [(tf, 1.0), (rel0, 1.0), (rel0 + 0.7, 0.5)])
    frozen = tf <= t < c.pov1 - 0.1
    blink = 0.0 if frozen else None
    spike = 0.0
    if t >= tf:
        spike = ease_out_back(seg(t, tf, tf + 0.12)) * (1 - ease_in(seg(t, c.pov1 - 0.05, c.pov1 + 0.3)))
    jit = 0.0
    if tf <= t < tf + 0.7:
        jit = 3.0 * math.sin(t * 95) * (1 - seg(t, tf, tf + 0.7))
    glint = 0.0
    w = info.word_at(t, "s05_l01") if t >= c.l1.start else -1
    if w >= 4:
        glint = 1.0 - seg(t, c.l1.end - 0.45, c.l1.end + 0.1)

    def draw():
        a = human.draw_person(ctx, "embar", x + jit, y, S, t, pose=pose, pose_t=pose_t, expr=expr,
                              look=look, face=face, turn=turn, blush=blush, blink=blink,
                              drift=not frozen, sweat=0.5 if t >= tf else 0.3,
                              mouth=info.mouth("embar", t), glint=glint)
        hx, hy, ang = a["hand_r"]
        cage(ctx, hx, hy - 6, t, rot=0.0, swing=1.0 if t < tf + 1.2 else 0.3)
        return a

    if spike > 0.01:
        a = with_behind(ctx, draw, lambda an: hair_spikes(ctx, an["top"], an["head"], S, spike, t))
    else:
        a = draw()
    if t >= tf:
        fx.heat_squiggles(ctx, a["top"][0], a["top"][1] - 10, 0.8, t, amount=clamp((blush - 0.6) / 0.4))
    return a


def shot_door(ctx, t, info, c):
    """Burst (wide-ish) then snap to the freeze close-up; also the relief shot."""
    if t < c.freeze:
        dx, dy = core.shake(t, c.burst + 0.05, 0.3, 14, seed=4)
        cam = (395 + dx, 1020 + dy, 1.15)
        k = seg(t, c.burst, c.burst + 0.13)
        door = clamp(ease_out_back(k, 3.0) * 0.98) if t >= c.burst else 0.0
        door += 0.04 * math.sin((t - c.burst) * 30) * (1 - seg(t, c.burst + 0.13, c.burst + 0.45)) * (k >= 1)
    else:
        if t < c.pov0:
            cam = (370, 985, 1.5)
        else:
            k = ease_in_out(seg(t, c.pov1, c.search))
            cam = (lerp(372, 380, k), lerp(840, 828, k), lerp(1.95, 2.05, k))
        door = 0.98
    with core.camera(ctx, *cam):
        sets.bedroom(ctx, t, layer="bg", door_open=clamp(door))
        sets.bedroom(ctx, t, layer="fg", parts=("door",), door_open=clamp(door))
        a = emb_doorway(ctx, t, c, info)
        if c.burst <= t < c.freeze:
            fx.motion_lines(ctx, a["hip"][0] - 40, a["hip"][1] - 120, 0.35, 260, t,
                            1.0 - seg(t, c.burst + 0.15, c.burst + 0.4), seed=4)
        if t >= c.freeze:
            fx.shock_lines(ctx, a["hip"][0], a["hip"][1] - 90, S, t, c.freeze, dur=1.05, rx=300, ry=560, seed=2)
    fx.flash(ctx, t, c.freeze, frames=2)


# ---------------------------------------------------------------------------
# shots 7/8: the search
# ---------------------------------------------------------------------------
CLOTHES = [  # (launch dt from srch_b, kind, colour, landing x, rot)
    (0.32, "shirt", "#ff8a4f", 905, 0.4),
    (0.55, "sock", "#ffffff", 1010, 1.2),
    (0.74, "shirt", "#7cc96a", 1095, -0.5),
    (0.95, "sock", "#f2c14e", 850, -0.9),
    (1.12, "shirt", "#9fd8f7", 1180, 0.2),
]


def draw_clothes(ctx, t, c):
    for i, (dt, kind, col, lx, rr) in enumerate(CLOTHES):
        t0 = c.srch_b + dt
        if t < t0:
            continue
        u = seg(t, t0, t0 + 0.62)
        sx, sy = 650, 1010
        x = lerp(sx, lx, u)
        y = lerp(sy, 1548, u) - 420 * math.sin(math.pi * u) * (1 - 0.25 * u)
        rot = rr + (1 - u) * 6.0 * (1 if i % 2 else -1)
        if u >= 1:
            y = 1548 - 6 * math.sin(math.pi * seg(t, t0 + 0.62, t0 + 0.75))
        if kind == "shirt":
            props.shirt(ctx, x, y - 30, 0.42, rot * (1 if u < 1 else 0.15), col, flap=1 - u, t=t,
                        print_=(i == 0))
        else:
            props.sock(ctx, x, y - 12, 0.75, rot if u < 1 else rr, col)


def emb_search_pose(t, c):
    """Returns (x, y, pose, pose_t, turn, expr, look, face, extra) for the search shots."""
    ts = c.search
    tb = c.srch_b
    if t < ts + 0.8:
        # dives head-first under the bed, butt up in the air, wiggling
        dive = ease_out_back(seg(t, ts, ts + 0.22))
        wig = math.sin((t - ts) * 15) * seg(t, ts + 0.2, ts + 0.3)
        under = {"base": "stand", **L("l", 0.15, 0.12, 0.6), **L("r", 0.25, 0.12, 0.65),
                 "lean": 2.4, "neck": 0.0, "nod": 0.4, "rot": 0.45,
                 **A("l", 0.85, 0.05, 0.1, h="flat"), **A("r", 0.95, 0.1, 0.05, h="flat"),
                 "dx": 7 * wig, "hip_roll": 0.07 * wig, "sway": 0.0}
        pose = ("crouch", under, clamp(dive))
        x = lerp(E_BED[0] - 90, E_BED[0], ease_out(seg(t, ts, ts + 0.2)))
        return (x, E_BED[1], pose, None, 1.1, "panic", (0.9, 0.3), {"open": 0.12}, "bed")
    if t < ts + 0.98:
        u = seg(t, ts + 0.8, ts + 0.98)
        x = lerp(E_BED[0], E_LAUNDRY[0], ease_in_out(u))
        return (x, E_LAUNDRY[1], "run_panic", (t - ts) * 1.4, -1.0, "panic", (-0.8, 0.3), {}, "run")
    if t < tb:
        lift = laundry_lift(t, c)
        crouch = {"base": "pick_up", **IK("l", 0.18, 0.12, 0.3, "grip", wa=0.0, wabs=0.0),
                  **IK("r", 0.18, 0.12, 0.3, "grip")}
        up = {"base": "pick_up", **IK("l", 0.18, 0.46, 0.3, "grip", wa=0.0, wabs=0.0),
              **IK("r", 0.18, 0.46, 0.3, "grip"), "lean": 0.62, "neck": -0.25, "nod": 0.2}
        pose = (crouch, up, lift)
        look = (-0.75, 0.95) if lift > 0.5 else (-0.7, 0.55)
        face = {"pupil": -0.15, "head_turn": -0.1 * lift}
        return (E_LAUNDRY[0], E_LAUNDRY[1], pose, None, -1.0, "panic", look, face, "laundry")
    # closet rummage
    dig = math.sin((t - tb) * 13)
    dig2 = math.sin((t - tb) * 13 + 1.9)
    pose = {"base": "lean_in", **A("l", 1.35 + 0.35 * dig, 0.15, 0.5 + 0.3 * dig2, h="claw"),
            **A("r", 1.6 + 0.3 * dig2, 0.1, 0.35 + 0.3 * dig, h="claw"),
            "lean": 0.62, "neck": 0.1, "nod": 0.05 + 0.04 * dig, "dx": 4 * dig}
    return (E_CLOSET[0], E_CLOSET[1], pose, None, -1.25, "panic", (-0.9, 0.0), {"open": 0.1}, "closet")


def laundry_lift(t, c):
    ts = c.search
    return tween(t, [(ts + 1.04, 0.0), (ts + 1.24, 1.0), (ts + 1.48, 1.0), (ts + 1.58, 0.0)])


def under_bed_shadow(ctx):
    bx, by, bw, bh = BM["bed"]
    ctx.rectangle(bx + 40, 1386, bw - 60, 74)
    core.fill(ctx, (0.13, 0.09, 0.08, 0.74))


def bed_rail(ctx):
    bx, by, bw, bh = BM["bed"]
    props.rect(ctx, bx + 40, 1352, bw - 60, 34, sets.C["wood"], 4.5, r=8)


def chair_state(t, c):
    """(empty, spin, dx): he is in it until he (unseen) gets up during the search."""
    if t < c.t_up:
        return False, 0.0, 0.0
    return True, chair_spin(t, c), CHAIR_DX


def shot_search(ctx, t, info, c):
    ts, tb = c.search, c.srch_b
    if t < tb:
        k = ease_in_out(seg(t, ts + 0.6, ts + 1.1))
        cam = (lerp(1375, 1045, k), lerp(1215, 1190, k), 1.25)
    else:
        k = ease_in_out(seg(t, tb, c.reveal))
        cam = (lerp(705, 625, k), lerp(1010, 975, k), lerp(1.5, 1.95, k))
    x, y, pose, pose_t, turn, expr, look, face, what = emb_search_pose(t, c)
    closet = ease_out_back(seg(t, tb, tb + 0.22)) if t >= tb else 0.0
    empty, spin, cdx = chair_state(t, c)
    with core.camera(ctx, *cam):
        sets.bedroom(ctx, t, layer="bg", laundry=laundry_lift(t, c), closet_open=clamp(closet),
                     chair_empty=empty, chair_spin=spin, chair_dx=cdx)
        if not empty:
            draw_gamer(ctx, t, notes=0.7)
        draw_clothes(ctx, t, c)
        cage(ctx, CAGE_FLOOR[0], CAGE_FLOOR[1] - CAGE_S * 300, t, swing=0.0)
        a = human.draw_person(ctx, "embar", x, y, S, t, pose=pose, pose_t=pose_t, expr=expr, look=look,
                              face=face, turn=turn, blush=0.45, sweat=0.6)
        if what == "bed":
            # his head is in the dark under the bed
            under_bed_shadow(ctx)
            bed_rail(ctx)
        if what == "run":
            fx.motion_lines(ctx, a["hip"][0] + 80, a["hip"][1] - 40, math.pi, 200, t, 1.0, seed=7)
        if what == "laundry":
            fx.emote(ctx, "question", a["top"][0] - 20, a["top"][1] - 60, 0.7, t, ts + 1.28, 0.34)


# ---------------------------------------------------------------------------
# shots 9-12: reveal, tap, leap, "Hi."
# ---------------------------------------------------------------------------
_MEAS = {}


def _measure_top():
    """Head-top height of Emb's leap pose at lift 0 (s=1), measured once."""
    if "top" not in _MEAS:
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 4, 4)
        cc = cairo.Context(surf)
        a = human.draw_person(cc, "embar", 0, 0, 1.0, 0.0, pose={"base": "leap_scared", "lift": 0.0},
                              expr="scream", shadow=False)
        _MEAS["top"] = -a["top"][1]
    return _MEAS["top"]


def emb_late(t, c, info):
    """Emb from the reveal to the end: rummage -> tap freeze -> leap -> floor."""
    tb = c.srch_b
    mouth = info.mouth("embar", t)
    if t < c.tap1:
        x, y, pose, pose_t, turn, expr, look, face, _ = emb_search_pose(t, c)
        return dict(x=x, y=y, pose=pose, pose_t=pose_t, turn=turn, expr=expr, look=look, face=face,
                    blush=0.45, mode="rummage")
    if t < c.launch:
        # stiffen on the first tap, eyes slide back over his shoulder
        tt = c.tap1
        dig = math.sin((tt - tb) * 13)
        dig2 = math.sin((tt - tb) * 13 + 1.9)
        base = {"base": "lean_in", **A("l", 1.35 + 0.35 * dig, 0.15, 0.5 + 0.3 * dig2, h="splay"),
                **A("r", 1.6 + 0.3 * dig2, 0.1, 0.35 + 0.3 * dig, h="splay"),
                "lean": 0.62, "neck": 0.1, "nod": 0.05, "hunch": 0.0}
        stiff = dict(base, lean=0.42, hunch=1.0, nod=-0.05, neck=0.0,
                     **A("l", 0.75, 0.3, 1.85, h="splay"), **A("r", 0.85, 0.25, 1.75, h="splay"))
        pose = (base, stiff, ease_out(seg(t, tt, tt + 0.12)))
        look = tween(t, [(tt + 0.12, (-0.9, 0.0)), (tt + 0.3, (1.0, -0.05))])
        face = {"pupil": -0.3 * seg(t, tt, tt + 0.1), "head_turn": 0.25 * ease_in_out(seg(t, tt + 0.3, tt + 0.5)),
                "press": 0.5}
        expr = "terrified" if t > c.l2.start - 0.05 else "alarmed"
        sq = seg(t, c.l2.start, c.launch)
        if sq > 0:
            # anticipation squash: knees bend, whirl toward Tiredness
            squat = dict(stiff, **L("l", 0.7, 0.2, 1.2), **L("r", 0.6, 0.2, 1.2), lean=0.2, hunch=1.0)
            pose = (stiff, squat, ease_out(sq))
            face = {"pupil": -0.4, "head_turn": 0.6, "squash": 0.12 * sq}
        turn = lerp(-1.25, -0.2, ease_in_out(sq))
        return dict(x=E_CLOSET[0], y=E_CLOSET[1], pose=pose, pose_t=None, turn=turn, expr=expr, look=look,
                    face=face, blush=0.45 + 0.3 * sq, mode="tap", mouth=mouth)
    top0 = _measure_top()
    ceil_lift = (E_CLOSET[1] - BM["ceiling_y"] - top0 * S) / S - 4
    if t < c.ceil:
        u = seg(t, c.launch, c.ceil)
        lift = ceil_lift * (0.25 * u + 0.75 * ease_out(u)) if u < 1 else ceil_lift
        lift = min(lift, ceil_lift)
        pose = {"base": "leap_scared", "lift": lift}
        return dict(x=E_CLOSET[0] - 10, y=E_CLOSET[1], pose=pose, pose_t=None, turn=-0.15, expr="scream",
                    look=(0.4, -0.2), face={"squash": -0.12}, blush=0.8, mode="up", mouth=mouth,
                    stretch=1.0 - u * 0.4)
    if t < c.ceil + c.hang:
        pose = {"base": "leap_scared", "lift": ceil_lift + 4}
        return dict(x=E_CLOSET[0] - 10, y=E_CLOSET[1], pose=pose, pose_t=None, turn=-0.15, expr="pain",
                    look=(0, 0), face={"squash": 0.25}, blush=0.8, mode="bonk")
    if t < c.land:
        u = seg(t, c.ceil + c.hang, c.land)
        lift = (ceil_lift + 4) * (1 - u * u) - 120 * u * u
        pose = ({"base": "fall", "lift": lift}, {"base": "sit_floor", "lift": lift}, smoothstep_(seg(u, 0.55, 1.0)))
        x = lerp(E_CLOSET[0] - 10, E_FLOOR[0], u)
        y = lerp(E_CLOSET[1], E_FLOOR[1], u)
        return dict(x=x, y=y, pose=pose, pose_t=t - c.ceil, turn=-0.1, expr="dazed", look=(0, -0.3),
                    face={"squash": -0.08}, blush=0.7, mode="fall")
    # on the floor, dazed -> coming to
    land = seg(t, c.land, c.land + 0.3)
    sq = (1 - ease_out_back(land, 2.5)) * 0.18
    wob = math.sin((t - c.land) * 5.5)
    expr = state_at(t, [(c.land, "dazed"), (c.foot + 0.75, "sheepish")], 0.3)
    look = tween(t, [(c.foot + 0.75, (0.0, -0.2)), (c.foot + 1.0, (0.65, -0.55))])
    face = {"head_tilt": 0.08 * wob * (1 - seg(t, c.foot + 0.5, c.foot + 0.9)), "squash": sq}
    blush = tween(t, [(c.land, 0.7), (c.foot + 0.6, 0.5)])
    return dict(x=E_FLOOR[0], y=E_FLOOR[1], pose="sit_floor", pose_t=None, turn=-0.1, expr=expr, look=look,
                face=face, blush=blush, mode="floor", squash_body=sq)


def emb_anchor_at(tq, c, info):
    """Emb's anchors at time tq (drawn into a dummy surface; cached, deterministic)."""
    key = ("anch", round(tq, 4))
    if key not in _MEAS:
        e = emb_late(tq, c, info)
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 4, 4)
        cc = cairo.Context(surf)
        _MEAS[key] = human.draw_person(cc, "embar", e["x"], e["y"], S, tq, pose=e["pose"], pose_t=e["pose_t"],
                                       expr=e["expr"], look=e["look"], face=e["face"], turn=e["turn"],
                                       shadow=False)
    return _MEAS[key]


def tired_late(t, c, info, emb_shoulder):
    """Tiredness from the reveal to the end."""
    x, y = T_BEHIND
    turn = -0.62
    expr = "squint"
    face = {"lid": 0.04, "press": 0.15}
    look = (-0.55, 0.12)
    blink = slow_blink(t, c.reveal + 0.8)
    pose = "arms_crossed"
    pose_t = None
    # --- tap
    if c.tap <= t < c.l2.start + 0.25:
        reach0, reach1 = c.tap + 0.1, c.tap1 - 0.02
        tx, ty, tz = ik_target("tired", S, (x, y), emb_shoulder, "l", turn, tz=0.18)
        tapz = 0.0
        for tk in (c.tap1, c.tap1 + 0.14):
            q = seg(t, tk - 0.06, tk + 0.06)
            tapz += math.sin(math.pi * q) * 0.035
        reach = {"base": "arms_crossed", **IK("l", tx - tapz, ty + 0.012, tz, "point", wa=0.0, wabs=0.0,
                                              layer="front"), "lean": 0.16, "neck": 0.1}
        k = ease_in_out(seg(t, reach0, reach1)) * (1 - ease_in_out(seg(t, c.l2.start, c.l2.start + 0.22)))
        pose = ("arms_crossed", reach, k)
        look = (-0.6, 0.05)
        expr = state_at(t, [(c.tap, "squint"), (c.tap + 0.2, "unamused")], 0.3)
    if t >= c.l2.start:
        expr = "unamused"
    # --- pupils track the leap (head does not move)
    if t >= c.launch:
        look = tween(t, [(c.launch, (-0.55, 0.0)), (c.launch + 0.3, (-0.45, -1.2)),
                         (c.ceil + c.hang + 0.05, (-0.45, -1.2)), (c.land - 0.02, (-0.55, 0.3))],
                     ease=ease_in_out)
        face = {"lid": 0.02, "press": 0.2}
    if t >= c.land:
        look = (-0.55, 0.3)
        face = {"lid": -0.04, "press": 0.2}
    # --- "Hi." and the foot tap
    if t >= c.hi0:
        expr = "deadpan"
        look = (-0.62, 0.3)
        face = {"head_nod": 0.05, "lid": -0.05}
        blink = slow_blink(t, c.l3.end + 0.05, 0.22, 0.1, 0.3)
    if t >= c.foot:
        pose = "tap_foot"
        pose_t = t - c.foot
        b = ease_in_out(seg(t, c.foot + 0.35, c.foot + 0.7))
        face = {"head_nod": 0.05, "lid": -0.05 - 0.03 * b, "brow_r": 0.42 * b, "brow_out_r": 0.15 * b,
                "press": 0.25}
    return dict(x=x, y=y, pose=pose, pose_t=pose_t, turn=turn, expr=expr, face=face, look=look, blink=blink)


def draw_late(ctx, t, info, c):
    """Everything in the bedroom from the reveal on (world space)."""
    sets.bedroom(ctx, t, layer="bg", closet_open=1.0, chair_empty=True, chair_spin=chair_spin(t, c),
                 chair_dx=CHAIR_DX)
    draw_clothes(ctx, t, c)
    cage(ctx, CAGE_FLOOR[0], CAGE_FLOOR[1] - CAGE_S * 300, t, swing=0.0)
    e = emb_late(t, c, info)
    mode = e["mode"]
    # Emb (with squash & stretch on the leap)
    sx = sy = 1.0
    if mode == "up":
        st = e.get("stretch", 1.0)
        sx, sy = 1.0 - 0.08 * st, 1.0 + 0.12 * st
    elif mode == "bonk":
        sx, sy = 1.12, 0.88
    elif mode == "floor":
        q = e.get("squash_body", 0.0)
        sx, sy = 1.0 + q * 0.6, 1.0 - q
    ex, ey = e["x"], e["y"]
    star_xy = None
    if mode == "floor" and t < c.foot + 0.9:
        top = emb_anchor_at(c.land + 0.6, c, info)["top"]
        star_xy = (top[0] + 4, top[1] + 8)
        fx.dizzy_stars(ctx, star_xy[0], star_xy[1], 0.75, t, t0=c.land + 0.08, dur=c.foot + 0.9 - c.land - 0.08,
                       layer="back")
    pivot_y = BM["ceiling_y"] if mode == "bonk" else ey
    ctx.save()
    ctx.translate(ex, pivot_y)
    ctx.scale(sx, sy)
    ctx.translate(-ex, -pivot_y)
    ea = human.draw_person(ctx, "embar", ex, ey, S, t, pose=e["pose"], pose_t=e["pose_t"], expr=e["expr"],
                           look=e["look"], face=e["face"], turn=e["turn"], blush=e["blush"], sweat=0.6,
                           mouth=e.get("mouth", (0, 0)))
    ctx.restore()
    if star_xy is not None:
        fx.dizzy_stars(ctx, star_xy[0], star_xy[1], 0.75, t, t0=c.land + 0.08, dur=c.foot + 0.9 - c.land - 0.08,
                       layer="front")
    # shoulder point for the tap (his back shoulder: screen-right)
    if mode in ("rummage", "tap") and t < c.l2.start:
        shp = ea["shoulder_r"]
    else:
        shp = emb_anchor_at(c.l2.start - 0.02, c, info)["shoulder_r"]
    tgt = (shp[0] + 6, shp[1] + 18)
    ta = tired_late(t, c, info, tgt)
    human.draw_person(ctx, "tired", ta["x"], ta["y"], S, t, pose=ta["pose"], pose_t=ta["pose_t"],
                      expr=ta["expr"], look=ta["look"], face=ta["face"], turn=ta["turn"], headphones="neck",
                      blink=ta["blink"], mouth=info.mouth("tired", t))
    # fx in world space
    fx.tap_marks(ctx, tgt[0] + 6, tgt[1] - 10, 0.8, t, c.tap1, taps=2, gap=0.14, angle=-math.pi * 0.62,
                 label="tap")
    if c.ceil - 0.01 <= t:
        fx.plaster_dust(ctx, E_CLOSET[0] - 10, BM["ceiling_y"] + 12, 0.85, t, c.ceil, seed=5, width=240, fall=900)
        fx.impact_star(ctx, E_CLOSET[0] - 10, BM["ceiling_y"] + 40, 0.75, t, c.ceil, word="BONK!", seed=3)
    if c.land - 0.02 <= t:
        fx.dust_puff(ctx, E_FLOOR[0], E_FLOOR[1] + 4, 0.9, t, c.land, seed=6)
    if mode == "up":
        fx.motion_lines(ctx, ea["hip"][0], ea["hip"][1] + 160, math.pi * 1.5, 300, t, 1.0, seed=11)


def shot_late(ctx, t, info, c):
    if t < c.tap:
        k = ease_in_out(seg(t, c.reveal + 0.1, c.reveal + 1.2))
        cam = (lerp(625, 1000, k), lerp(975, 1020, k), lerp(1.95, 0.9, k))
    elif t < c.launch:
        k = ease_out(seg(t, c.tap, c.launch))
        cam = (lerp(840, 850, k), lerp(1000, 990, k), lerp(1.22, 1.26, k))
    elif t < c.hi0:
        cam = (870, 930, 0.96)
    else:
        k = ease_in_out(seg(t, c.l3.end, c.end))
        cam = (lerp(860, 900, k), lerp(1070, 1010, k), lerp(1.38, 1.58, k))
    with core.cache_steps(2):
        with core.camera(ctx, *cam):
            draw_late(ctx, t, info, c)


# ---------------------------------------------------------------------------
# entry points
# ---------------------------------------------------------------------------
def render(ctx, t, info):
    c = cues(info)
    if t < c.crawl:
        shot_music(ctx, t, info, c)
    elif t < c.burst:
        shot_hall(ctx, t, info, c)
    elif t < c.pov0:
        shot_door(ctx, t, info, c)
    elif t < c.pov1:
        shot_pov(ctx, t, info, c)
    elif t < c.search:
        shot_door(ctx, t, info, c)
    elif t < c.reveal:
        shot_search(ctx, t, info, c)
    else:
        shot_late(ctx, t, info, c)


def SFX(info):
    from audio import sfx
    c = cues(info)
    ev = []
    # headphone leak while his headphones are on (bedroom shots only)
    ev += sfx.loop_events("game_music_leak", 0.0, c.crawl, -1)
    ev += sfx.loop_events("game_music_leak", c.burst, c.search + 0.6, -5)
    ev.append((0.35, "game_blips", -9, 0.4))
    # hallway
    ev.append((c.crawl + 0.05, "cloth_rustle", -6, -0.3))
    ev.append((c.crawl + 0.9, "scurry", -5, 0.4))
    ev.append((c.crawl + 1.36, "footsteps_run", -7, 0.2))
    # burst + freeze
    ev.append((c.burst + 0.04, "door_bang", 0, -0.4))
    ev.append((c.freeze, "stinger_shock", -1))
    ev.append((c.freeze, "lightning_zap", 0))
    # search
    ev.append((c.search + 0.05, "cloth_rustle", -2, 0.2))
    ev.append((c.search + 1.0, "cloth_rustle", 0, 0.0))
    ev.append((c.srch_b, "drawer_open", -4, -0.3))
    ev.append((c.srch_b + 0.3, "cloth_rustle", 0, -0.3))
    ev.append((c.srch_b + 0.8, "cloth_rustle", -2, -0.2))
    # reveal: the empty chair creaks round
    ev.append((c.reveal + 0.55, "chair_creak", -8, 0.5))
    # tap, scream, bonk, landing
    ev.append((c.tap1, "tap_tap", 3, 0.1))
    ev.append((c.launch, "whoosh", -8, 0.0))
    ev.append((c.ceil, "ceiling_thud", 0, -0.1))
    ev.append((c.land, "body_thud", 0, -0.1))
    # impatient foot
    for k in range(3):
        ev.append((c.foot + 0.06 + k * 0.5, "foot_tap", 2, 0.15))
    return ev
