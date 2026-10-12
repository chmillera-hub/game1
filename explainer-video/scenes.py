"""Scene-by-scene animation. Each function draws one full frame of its scene."""
import math

import cairo

import props as P
from draw import (INK, WHITE, W, H, clamp, ease_in, ease_out, ease_out_back, ellipse,
                  fill_stroke, font, glow, keyed, lerp, mix, ramp, rgba, rrect, shade, smooth,
                  star, text, text_block, text_w, vgrad, wrap)
from engine import cam, walk_x
from script import LENS_LIST

GROUND = 1290


def dim(ctx, a):
    if a > 0:
        ctx.rectangle(0, 0, W, H)
        rgba(ctx, (0.1, 0.08, 0.2), a)
        ctx.fill()


def alpha_group(ctx, a, fn):
    if a <= 0.001:
        return
    if a >= 0.999:
        fn()
        return
    ctx.push_group()
    fn()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def scaled(ctx, x, y, s, fn):
    if s <= 0.001:
        return
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.translate(-x, -y)
    fn()
    ctx.restore()


def motion_lines(ctx, x, y, n=3, length=90, a=0.6, dirx=-1):
    for i in range(n):
        yy = y - 60 + i * 50
        ctx.move_to(x + dirx * 40, yy)
        ctx.line_to(x + dirx * (40 + length - i * 15), yy)
    rgba(ctx, INK, a)
    ctx.set_line_width(6)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.stroke()


def title_slam(ctx, s, x, y, size, k, color=(1, 0.8, 0.25), sub=None):
    if k <= 0:
        return
    sc = lerp(1.8, 1.0, ease_out_back(k, 2.2)) if k < 1 else 1.0
    a = clamp(k * 3)
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(sc, sc)
    text(ctx, s, 0, 0, size, color, outline=INK, olw=size * 0.22, a=a,
         shadow=(8, 10, (0, 0, 0), 0.25))
    ctx.restore()


# =================================================================== HOOK
def cold_open(S):
    ctx, lt, t = S.ctx, S.lt, S.t
    t_pic, t_drop, t_laugh, t_run = S.tb("picture"), S.tb("drop"), S.tb("ned_laugh"), S.tb("run")
    t_door = t_run + 1.1
    door_k = ramp(lt, t_door, t_door + 0.4)
    zoom = 1.13 + 0.07 * ramp(lt, S.tb("explain1"), S.te("explain2"))
    sh = S.shake(S.te("title") + 0.05, 0.4, 14)
    ctx.save()
    ctx.translate(*sh)
    cam(ctx, zoom, 540, 1050)
    P.sky(ctx)
    P.sun(ctx, 1000, 330, 55, t)
    P.clouds(ctx, t, ys=(250, 120, 300))
    bell = 0.0
    tb_ = t_drop + 0.85
    if tb_ <= lt <= tb_ + 1.2:
        bell = 1 - (lt - tb_) / 1.2
    frame = P.house(ctx, door_k, t, bell)
    # Sam in the doorway (behind the door panel)
    if door_k > 0:
        look = keyed(lt, [(t_door, (0.0, 0.1)), (t_door + 0.5, (0.0, 0.9)),
                          (S.tb("sam_door") + 1.1, (0.1, 0.9)), (S.tb("hello"), (1.0, 0.0)),
                          (S.te("hello") + 0.4, (0.6, 0.2)), (S.tb("explain2"), (0.0, 0.5))])
        arms = [(0, "down"), (S.tb("sam_door") + 0.6, "shrug"), (S.te("sam_door"), "down"),
                (S.tb("hello"), "hold")]
        S.char("sam", 540 + 18 * ramp(lt, S.tb("hello"), S.tb("hello") + 0.4), 1225, 1.0,
               look=look, arms=arms, extra_emo=[(t_door, "surprised")])
    P.door_panel(ctx, frame, door_k)
    P.doorstep(ctx)
    ctx.rectangle(0, 1268, W, 70)
    rgba(ctx, (0.82, 0.8, 0.82))
    ctx.fill()
    P.ground(ctx, 1336, (0.55, 0.8, 0.45))
    P.pot_plant(ctx, 255, 1232, 0.85, t)
    P.pot_plant(ctx, 828, 1232, 0.85, t)
    # bag + mess on the doorstep
    drop_at = t_drop + 0.35
    if lt >= drop_at:
        P.banana_peel(ctx, 655, 1242, 0.8)
        P.crumpled(ctx, 590, 1246, 1.0)
        squash = 1 + 0.15 * math.exp(-(lt - drop_at) * 10) * math.cos((lt - drop_at) * 30)
        ctx.save()
        ctx.translate(462, 1236)
        ctx.scale(1 / squash, squash)
        P.trash_bag(ctx, 0, 0, 0.95)
        ctx.restore()
    # Ned sneaks in, drops the bag, rings, laughs and runs
    keys = [(0, 125), (t_pic + 0.1, 125), (t_drop + 0.05, 430), (t_run, 430), (t_run + 0.85, 1350)]
    x, ph, amt = walk_x(lt, keys)
    run = lt >= t_run
    if run:
        ph = (lt - t_run) * 22
    peek = 1 - ramp(lt, t_pic - 0.2, t_pic + 0.2)
    ny = GROUND - 30 + peek * 120
    carrying = lt < drop_at

    def carry_bag(c, hands, bw, bh):
        if carrying:
            hx = (hands[0][0] + hands[1][0]) / 2
            hy = (hands[0][1] + hands[1][1]) / 2
            P.trash_bag(c, hx + 10, hy + 80, 0.75)

    if x < 1300:
        arms = [(0, "carry"), (drop_at, "down"), (t_drop + 0.6, ((110, 10), (14, 4))),
                (t_laugh, "cover"), (t_run, "run")]
        ned_look = keyed(lt, [(0, (1.0, 0.0)), (t_drop + 0.6, (-1.0, -0.3)),
                              (t_laugh, (0.3, 0.1)), (t_run, (-1.0, 0.0))])
        S.char("ned", x, ny, 0.95, arms=arms, look=ned_look, walk=ph * (2.0 if run else 1.0),
               walk_amt=amt * (1.4 if run else 0.7), hold_item=carry_bag,
               extra_emo=[(t_run, "laugh")])
        if run:
            motion_lines(ctx, x - 80, ny - 140, a=0.5)
    P.bush(ctx, 95, 1345, 1.15)
    ctx.restore()
    # Title at the very first frame (so the video never opens on black)
    k_out = ramp(lt, t_pic - 0.1, t_pic + 0.45)
    if k_out < 1:
        y = 230 - 260 * ease_in(k_out)
        a = 1 - k_out
        title_slam(ctx, "THE HIT-AND-HIDE", 540, y, 96, 1.0)
        P.pill(ctx, "when someone hurts you... then blocks your reply", 540, y + 92, 34,
               WHITE, a=a)
    # Lumi narrates
    lx, ly, ls = 925, 480, 0.72
    if lt > S.tb("step1") - 0.5:
        k = ramp(lt, S.tb("step1") - 0.5, S.tb("step1"))
        lx, ly, ls = lerp(925, 900, k), lerp(480, 1020, k), lerp(0.72, 0.62, k)
    S.lumi(lx, ly, ls, look=(-0.4, 0.3) if lt < S.tb("explain1") else (-0.2, 0.2))
    # Title slam + the two steps
    k_title = ramp(lt, S.te("title") - 0.02, S.te("title") + 0.2)
    k_steps = ramp(lt, S.tb("step1") - 0.3, S.tb("step1") + 0.2)
    dim(ctx, 0.35 * k_steps)
    if k_title > 0:
        ty = lerp(560, 300, smooth(k_steps))
        title_slam(ctx, "THE HIT-AND-HIDE", 540, ty, lerp(116, 96, k_steps), k_title)
    for i, tag in enumerate(("step1", "step2")):
        s = S.pop(S.tb(tag), 0.5)
        if s <= 0:
            continue
        cx = 300 + i * 480
        cy = 650

        def draw_card(i=i, cx=cx, cy=cy):
            P.card(ctx, cx - 215, cy - 210, 430, 420, WHITE, 36)
            P.pill(ctx, f"STEP {i + 1}", cx, cy - 150, 34, (1, 0.8, 0.3) if i == 0 else (0.6, 0.8, 1))
            text(ctx, "THE HIT" if i == 0 else "THE HIDE", cx, cy + 165, 58, INK)
            if i == 0:
                P.heart(ctx, cx + 30, cy + 20, 140, crack=ramp(lt, S.tb(tag) + 0.6, S.tb(tag) + 0.9))
                fall = ramp(lt, S.tb(tag) + 0.1, S.tb(tag) + 0.6)
                P.trash_bag(ctx, cx - 95 + 40 * fall, cy - 60 + 50 * ease_in(fall), 0.45,
                            tilt=-0.4 + 0.5 * fall)
            else:
                P.bubble(ctx, cx - 30, cy - 10, 220, 130, tail=(-1, 1))
                text(ctx, "...", cx - 30, cy + 8, 60, (0.6, 0.6, 0.7))
                ls_ = S.pop(S.te(tag) - 0.4, 0.35)
                if ls_ > 0:
                    scaled(ctx, cx + 80, cy + 30, ls_, lambda: P.lock(ctx, cx + 80, cy + 30, 120))

        scaled(ctx, cx, cy, s, draw_card)


# =================================================================== ONLINE
COMMENTS = ["This is awful.", "Nobody wants you here.", "Worst post ever.", "Go away.",
            "Just quit already."]


def online(S):
    ctx, lt, t = S.ctx, S.lt, S.t
    ctx.set_source(vgrad(ctx, 0, H, [(0, (0.78, 0.74, 1.0)), (1, (1.0, 0.82, 0.88))]))
    ctx.paint()
    for i in range(10):  # drifting background icons
        x = (i * 173 + t * 14) % (W + 100) - 50
        y = (i * 317) % 1300 + 150 - (t * 10 + i * 40) % 60
        if i % 2:
            P.heart(ctx, x, y, 50, (1, 1, 1), lw=0.01)
        else:
            rrect(ctx, x - 30, y - 20, 60, 40, 14)
            rgba(ctx, WHITE, 0.5)
            ctx.fill()
    blocked = lt >= S.tb("blocked") + 0.15
    sh = S.shake(S.tb("blocked") + 0.15, 0.3, 8)
    ctx.save()
    ctx.translate(*sh)
    px, py, pw, ph = 150, 190, 780, 1110
    P.phone(ctx, px, py, pw, ph)
    ctx.save()
    rrect(ctx, px + 22, py + 22, pw - 44, ph - 44, 42)
    ctx.clip()
    P.avatar(ctx, 250, 320, 42, (0.27, 0.76, 0.69))
    text(ctx, "Sam", 310, 315, 40, INK, align="left")
    text(ctx, "@sam_paints", 310, 352, 28, (0.5, 0.5, 0.6), align="left", bold=False)
    text(ctx, "Finished my first painting!", 210, 430, 42, INK, align="left")
    P.painting(ctx, 210, 460, 660, 210)
    P.heart(ctx, 240, 715, 40)
    text(ctx, "24", 275, 728, 34, INK, align="left")
    ctx.move_to(200, 760)
    ctx.line_to(880, 760)
    rgba(ctx, (0.85, 0.85, 0.9))
    ctx.set_line_width(3)
    ctx.stroke()
    ping_times = [S.tb("comments") + d for d in (0.4, 1.1, 1.8, 2.5, 3.2)]
    for i, (tp, msg) in enumerate(zip(ping_times, COMMENTS)):
        s = S.pop(tp, 0.35)
        if s <= 0:
            continue
        cy = 820 + i * 84
        grey = 0.5 * ramp(lt, S.tb("blocked") + 0.15, S.tb("blocked") + 0.5)

        def draw_comment(cy=cy, msg=msg, grey=grey):
            P.avatar(ctx, 225, cy, 26, (0.64, 0.84, 0.32), -0.6)
            font(ctx, 32)
            w = max(text_w(ctx, msg), 230) + 40
            rrect(ctx, 262, cy - 34, w, 68, 24)
            fill_stroke(ctx, mix((1, 0.9, 0.9), (0.9, 0.9, 0.92), grey * 2), INK, 3)
            text(ctx, "@NoReplyNed", 282, cy - 8, 22, (0.35, 0.55, 0.15), align="left")
            text(ctx, msg, 282, cy + 22, 30, mix(INK, (0.55, 0.55, 0.6), grey * 2), align="left")

        scaled(ctx, 225, cy, s, draw_comment)
    # reply bar
    deny = S.tb("cant_reply") + 1.6
    rs = S.shake(deny, 0.4, 12)
    ry = 1222
    flash = math.exp(-max(0, lt - deny) * 4) if lt >= deny else 0
    rrect(ctx, 200 + rs[0], ry - 38, 680, 76, 38)
    col = mix((0.95, 0.96, 1.0), (0.88, 0.88, 0.9), 1.0 if blocked else 0)
    col = mix(col, (1, 0.6, 0.6), flash)
    fill_stroke(ctx, col, INK, 4)
    if blocked:
        text(ctx, "Replies are turned off", 540 + rs[0] + 20, ry + 12, 32, (0.5, 0.5, 0.58))
        P.lock(ctx, 260 + rs[0], ry + 2, 44)
    else:
        text(ctx, "Write a reply...", 240, ry + 12, 32, (0.6, 0.6, 0.68), align="left", bold=False)
    ctx.restore()
    # "blocked" banner
    bs = S.pop(S.tb("blocked") + 0.15, 0.45)
    if bs > 0:
        def banner():
            P.card(ctx, 190, 560, 700, 170, (0.25, 0.25, 0.32), 30)
            P.lock(ctx, 280, 650, 90)
            text(ctx, "You've been blocked", 590, 630, 44, WHITE)
            text(ctx, "You can't reply to this.", 590, 685, 34, (0.85, 0.85, 0.9), bold=False)
        scaled(ctx, 540, 645, bs, banner)
    ctx.restore()
    # Ned pops up beside the phone, smug
    ned_in = ramp(lt, S.tb("comments") + 0.2, S.tb("comments") + 0.6)
    ned_out = ramp(lt, S.te("blocked") + 0.5, S.te("blocked") + 0.9)
    k = ned_in * (1 - ned_out)
    if k > 0:
        arms = [(0, "down"), (S.tb("blocked"), ((14, 4), (70, 60))), (S.te("blocked") - 0.4, "cross")]
        S.char("ned", 905, 1300 + (1 - k) * 380, 0.72, arms=arms, look=(-0.8, 0.2))
    # Sam reacts bottom-left
    arms = [(0, "down"), (S.tb("cant_reply") + 0.8, "point"), (S.te("cant_reply") + 0.3, "hold")]
    look = (0.9, -0.3) if lt < S.tb("blocked") else (0.6, -0.5)
    S.char("sam", 190, 1310, 0.72, arms=arms, look=look)
    # one-way sign
    ss = S.pop(S.tb("oneway") + 0.8, 0.5)
    if ss > 0:
        dim(ctx, 0.25 * clamp(ss))
        scaled(ctx, 540, 900, ss, lambda: P.road_sign(ctx, 540, 900, 1.1, "ONE WAY ONLY", "one",
                                                     (0.85, 0.3, 0.3)))
    S.lumi(975, 205, 0.55, look=(-0.5, 0.4))


# =================================================================== ADVICE
def advice(S):
    ctx, lt, t = S.ctx, S.lt, S.t
    P.sky(ctx, (0.58, 0.82, 1.0), (0.95, 0.97, 0.9), 1100)
    P.clouds(ctx, t, ys=(300, 180, 420))
    P.ground(ctx, 1060, (0.55, 0.8, 0.45))
    for x, s in ((80, 1.0), (330, 0.8), (980, 1.1)):
        P.tree(ctx, x, 1090, s, t)
    ctx.move_to(0, 1200)
    ctx.curve_to(400, 1150, 700, 1230, W, 1180)
    ctx.line_to(W, 1330)
    ctx.curve_to(700, 1360, 400, 1290, 0, 1330)
    ctx.close_path()
    rgba(ctx, (0.92, 0.85, 0.7))
    ctx.fill()
    P.bench(ctx, 820, 1150, 0.8)
    # Ned walks in, gives "advice", puts on headphones and leaves
    t_adv = S.tb("advice")
    t_resp = S.wt("advice", "respond", end=True)
    t_leave = S.te("advice") + 0.05
    keys = [(0, -220), (min(1.6, t_adv - 0.2), 330), (t_leave, 330), (t_leave + 0.9, -260)]
    x, ph, amt = walk_x(lt, keys)
    if x > -250:
        arms = [(0, "down"), (t_adv, "open"), (S.wt("advice", "therapy"), "point"),
                (S.wt("advice", "pottery"), "cheer"), (S.wt("advice", "Anyway"), "down"),
                (S.wt("advice", "please") - 0.3, "headphones"), (t_resp + 0.35, "down"),
                (S.wt("advice", "Bye"), "wave"), (t_leave, "run")]
        props = ("headphones",) if lt > t_resp + 0.2 else ()
        S.char("ned", x, GROUND - 20, 0.95, arms=arms, walk=ph, walk_amt=amt,
               look=(0.9, -0.1) if lt < t_leave else (-1, 0), props=props)
        if lt > t_leave:
            motion_lines(ctx, x + 90, GROUND - 160, dirx=1)
    # Sam
    look = (-0.8, -0.1) if x > -100 else (-0.3, 0.2)
    if lt > S.tb("twoway"):
        look = (0.0, -0.6)
    arms = [(0, "down"), (S.tb("okay"), "shrug"), (S.te("okay") + 0.6, "down")]
    S.char("sam", 760, GROUND - 10, 1.0, look=look, arms=arms)
    # two-way / one-way sign
    s2 = S.pop(S.tb("twoway") + 1.6, 0.5)
    if s2 > 0:
        flip = ramp(lt, S.tb("oneway") - 0.1, S.tb("oneway") + 0.35)
        if flip < 0.5:
            P.road_sign(ctx, 540, 640, 1.05 * s2, "TWO-WAY STREET", "two", flip=flip)
        else:
            P.road_sign(ctx, 540, 640, 1.05, "ONE-WAY STREET", "one", (0.85, 0.3, 0.3), flip=flip)
    S.lumi(930, 330, 0.68, look=(-0.6, 0.4))


# =================================================================== MEETING
def meeting(S):
    ctx, lt, t = S.ctx, S.lt, S.t
    ctx.save()
    cam(ctx, 1.2, 540, 1080)
    P.office_wall(ctx)
    P.city_window(ctx, 90, 250, 900, 380, t)
    P.whiteboard(ctx, 70, 700, 330, 230)
    ctx.arc(690, 735, 62, 0, 2 * math.pi)  # wall clock
    fill_stroke(ctx, WHITE, INK, 6)
    for a in (t * 0.5, t * 6):
        ctx.move_to(690, 735)
        ctx.line_to(690 + math.cos(a) * 40, 735 + math.sin(a) * 40)
        rgba(ctx, INK)
        ctx.set_line_width(6)
        ctx.stroke()
    speaker = S.current_speaker()
    t_dis = S.tb("dismiss")
    t_moving = S.wt("dismiss", "Moving")

    def look_from(x):
        if speaker == "sam":
            return (clamp((400 - x) / 250, -1, 1), 0.0)
        if speaker == "marsh":
            return (clamp((880 - x) / 250, -1, 1), -0.1)
        return (0.0, 0.2)

    nervous_t = t_moving
    S.char("extra1", 150, 1215, 0.9, look=look_from(150),
           extra_emo=[(0, "neutral"), (nervous_t, "nervous")])
    S.char("extra3", 640, 1215, 0.9, look=look_from(640),
           extra_emo=[(0, "neutral"), (nervous_t, "nervous")])
    sam_arms = [(0, "down"), (S.tb("idea") - 0.3, "wave"), (S.tb("idea") + 0.7, "present"),
                (t_moving, "down")]
    S.char("sam", 400, 1215, 0.95, arms=sam_arms,
           look=(0.9, -0.2) if lt < S.tb("brushed") else (0.2, 0.5), props=("badge",))
    m_look = (0.0, 0.7)
    if t_dis - 0.2 < lt < t_moving:
        m_look = (-1.0, 0.0)
    elif lt >= t_moving:
        m_look = (0.6, -0.3)
    m_arms = [(0, "cross"), (t_moving - 0.1, ((14, 4), (75, 70))), (S.te("dismiss") + 0.3, "cross")]
    S.char("marsh", 870, 1225, 0.92, arms=m_arms, look=m_look)
    P.table(ctx, 1080)
    P.mug(ctx, 250, 1105)
    P.mug(ctx, 560, 1100, (0.45, 0.6, 0.95))
    P.laptop(ctx, 860, 1105, 0.75)
    for x in (360, 700):
        rrect(ctx, x, 1085, 120, 16, 4)
        fill_stroke(ctx, WHITE, INK, 3)
    # the idea bulb: lights up, then gets brushed off
    bs = S.pop(S.tb("idea") + 0.3, 0.45)
    if bs > 0:
        fall = ramp(lt, t_moving + 0.2, t_moving + 1.2)
        on = 1 - ramp(lt, t_moving, t_moving + 0.3)
        bx = 400 + 240 * fall
        by = 760 + 420 * ease_in(fall)
        a = 1 - ramp(lt, t_moving + 0.9, t_moving + 1.3)
        alpha_group(ctx, a, lambda: scaled(ctx, bx, by, bs * 0.9, lambda: P.bulb(ctx, bx, by, 1.0, on)))
    ctx.restore()
    S.lumi(950, 300, 0.6, look=(-0.6, 0.6))


# =================================================================== DOOR
def door(S):
    ctx, lt, t = S.ctx, S.lt, S.t
    ctx.save()
    cam(ctx, 1.12, 540, 1150)
    ctx.set_source(vgrad(ctx, 0, H, [(0, (0.97, 0.92, 0.84)), (1, (0.9, 0.84, 0.76))]))
    ctx.paint()
    ctx.rectangle(0, 1000, W, 260)
    rgba(ctx, (0.8, 0.68, 0.55))
    ctx.fill()
    ctx.move_to(0, 1000)
    ctx.line_to(W, 1000)
    rgba(ctx, INK)
    ctx.set_line_width(5)
    ctx.stroke()
    P.framed_picture(ctx, 70, 520, 200, 160, 0)
    P.framed_picture(ctx, 320, 470, 150, 200, 1)
    P.ground(ctx, 1258, (0.62, 0.5, 0.42))
    t_close1 = S.te("notnow") + 0.15
    t_open2 = S.tb("attitude") - 0.5
    t_back = S.te("attitude") + 0.05
    t_close2 = S.tb("example") - 0.2
    open_k = 1 - ramp(lt, t_close1, t_close1 + 0.3)
    open_k = max(open_k, ramp(lt, t_open2, t_open2 + 0.3) * (1 - ramp(lt, t_close2, t_close2 + 0.3)))
    out_k = ramp(lt, t_open2 + 0.15, t_open2 + 0.5) * (1 - ramp(lt, t_back, t_back + 0.3))
    inside_marsh = out_k < 0.5

    def inside(c):
        ctx.rectangle(600, 690, 300, 570)
        rgba(ctx, (0.88, 0.85, 0.95))
        ctx.fill()
        P.framed_picture(ctx, 640, 760, 110, 90, 2)
        if inside_marsh:
            arms = "type" if lt < S.tb("attitude") - 1 else "down"
            look = (0.9, 0.3) if lt < S.tb("notnow") + 0.5 else (-0.3, 0.1)
            S.char("marsh", 760, 1250, 0.78, arms=arms, look=look, props=("headphones",))
        P.monitor(ctx, 860, 1130, 0.6, back=True)
        rrect(ctx, 610, 1120, 300, 30, 6)
        fill_stroke(ctx, (0.6, 0.45, 0.32), INK, 4)
        ctx.rectangle(630, 1150, 260, 110)
        rgba(ctx, (0.5, 0.36, 0.26))
        ctx.fill()

    P.office_door(ctx, 600, 690, 300, 568, open_k, inside)
    # Sam walks up
    sx, ph, amt = walk_x(lt, [(0, -120), (1.0, 290)])
    arms = [(0, "down"), (S.tb("ask"), "wave"), (S.tb("ask") + 0.8, "down"),
            (S.tb("example"), "shrug"), (S.te("example") + 0.5, "down")]
    look = (1.0, -0.1)
    S.char("sam", sx, 1262, 1.0, arms=arms, walk=ph, walk_amt=amt, look=look, props=("badge",))
    if not inside_marsh:
        mx = lerp(760, 560, out_k)
        S.char("marsh", mx, 1262, 0.95, arms=[(0, "down"), (S.tb("attitude"), "point_l")],
               look=(-1.0, 0.0))
    # floating question marks around Sam
    qk = ramp(lt, S.tb("vague") - 0.3, S.tb("vague") + 0.3)
    for i in range(3):
        a = qk * (0.6 + 0.4 * math.sin(t * 3 + i))
        P.qmark(ctx, sx - 130 + i * 130, 830 - 30 * math.sin(t * 2 + i * 2), 90, a=a)
    ctx.restore()
    S.lumi(140, 380, 0.62, look=(0.6, 0.5))


# =================================================================== FEAR
def fear(S):
    ctx, lt, t = S.ctx, S.lt, S.t
    ctx.set_source(vgrad(ctx, 0, H, [(0, (0.16, 0.18, 0.34)), (1, (0.28, 0.25, 0.42))]))
    ctx.paint()
    P.city_window(ctx, 90, 240, 520, 360, t, night=True)
    # looming shadow of the manager on the wall
    sk = ramp(lt, S.tb("power") + 0.8, S.tb("power") + 1.8) * (1 - ramp(lt, S.tb("fear") + 1.5,
                                                                         S.tb("fear") + 2.5))
    if sk > 0:
        glow(ctx, 790, 700, 520, (0.55, 0.6, 0.9), 0.35 * sk)
        ctx.save()
        ctx.push_group()
        from draw import bean_path
        ctx.translate(790 + math.sin(t * 0.8) * 10, 1120)
        ctx.scale(1.45, 1.45)
        bean_path(ctx, 250, 430)
        rgba(ctx, (0.05, 0.05, 0.12))
        ctx.fill()
        for s in (-1, 1):
            ellipse(ctx, s * 50, -300, 22, 28)
            rgba(ctx, (0.9, 0.85, 1.0), 0.8)
            ctx.fill()
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(0.8 * sk)
        ctx.restore()
    # lamp light
    glow(ctx, 260, 1000, 420, (1, 0.85, 0.5), 0.35)
    beat = 0
    if S.during("think", 0.5):
        d = (lt - S.tb("think")) % 0.9
        beat = math.exp(-d * 8) * 0.25
    S.char("sam", 540, 1230, 1.0, look=(0.0, -0.4) if lt < S.tb("cost") else (0.2, -0.6),
           arms=[(0, "down"), (S.tb("think"), "heart")])
    P.table(ctx, 1110, c=(0.45, 0.35, 0.3))
    ctx.move_to(260, 1110)
    ctx.line_to(230, 980)
    ctx.line_to(330, 930)
    rgba(ctx, (0.3, 0.3, 0.35))
    ctx.set_line_width(10)
    ctx.stroke()
    ctx.move_to(290, 900)
    ctx.line_to(400, 900)
    ctx.line_to(360, 960)
    ctx.line_to(320, 960)
    ctx.close_path()
    fill_stroke(ctx, (0.95, 0.8, 0.4), INK, 4)
    P.laptop(ctx, 830, 1135, 0.8)
    glow(ctx, 830, 1050, 160, (0.6, 0.8, 1), 0.3)
    # thought cloud with what's at stake
    tk = S.pop(S.tb("think") - 0.1, 0.5) * (1 - ramp(lt, S.tb("fear"), S.tb("fear") + 0.3))
    if tk > 0:
        def cloud():
            P.thought(ctx, 540, 600, 760, 380, toward=(0, 1))
            items = [(S.tb("cost") + 0.9, "SHIFTS"), (S.tb("cost") + 1.9, "REVIEWS"),
                     (S.tb("cost") + 3.1, "MY JOB")]
            if lt < items[0][0]:
                P.qmark(ctx, 540, 650, 160)
            for i, (at, lab) in enumerate(items):
                s = S.pop(at, 0.4)
                if s <= 0:
                    continue
                cx = 330 + i * 210
                scaled(ctx, cx, 590, s, lambda cx=cx, i=i, lab=lab: stake_icon(ctx, cx, 590, i, lab))
        scaled(ctx, 540, 650, tk, cloud)
    # "the block button is fear": a big BLOCK button that turns into a lock on Sam's voice
    bk = S.pop(S.wt("fear", "block") - 0.1, 0.4)
    lk = ramp(lt, S.wt("fear", "fear") - 0.15, S.wt("fear", "fear") + 0.15)
    if bk > 0:
        def button():
            P.bubble(ctx, 540, 640, 460, 210, tail=(0, 1), c=(0.95, 0.95, 1))
            text(ctx, "...", 540, 670, 90, (0.6, 0.6, 0.7))
            if lk < 1:
                rrect(ctx, 360, 570, 360, 120, 60)
                fill_stroke(ctx, (0.9, 0.3, 0.35), INK, 6, 1 - lk)
                text(ctx, "BLOCK", 540, 650, 64, WHITE, a=1 - lk)
            if lk > 0:
                scaled(ctx, 540, 650, ease_out_back(lk), lambda: P.lock(ctx, 540, 650, 170))
        scaled(ctx, 540, 640, bk, button)
    if beat > 0:
        vign = cairo.RadialGradient(540, 960, 300, 540, 960, 1100)
        vign.add_color_stop_rgba(0, 0.8, 0.1, 0.2, 0)
        vign.add_color_stop_rgba(1, 0.8, 0.1, 0.2, beat)
        ctx.set_source(vign)
        ctx.paint()
    S.lumi(150, 330, 0.6, look=(0.6, 0.5))


def stake_icon(ctx, x, y, i, label):
    if i == 0:  # calendar
        P.card(ctx, x - 70, y - 70, 140, 130, WHITE, 16, shadow=False)
        ctx.rectangle(x - 70, y - 70, 140, 36)
        rgba(ctx, (0.9, 0.35, 0.35))
        ctx.fill()
        for r in range(2):
            for c in range(3):
                ctx.rectangle(x - 50 + c * 38, y - 22 + r * 36, 24, 24)
                rgba(ctx, (0.75, 0.78, 0.85))
                ctx.fill()
    elif i == 1:  # star rating dropping
        for k in range(3):
            star(ctx, x - 50 + k * 50, y - 10, 28, (1, 0.8, 0.2) if k == 0 else (0.75, 0.75, 0.8),
                 points=5)
        P.arrow(ctx, x, y + 20, x, y + 60, (0.9, 0.3, 0.3), 8, 20)
    else:  # briefcase
        rrect(ctx, x - 75, y - 45, 150, 105, 16)
        fill_stroke(ctx, (0.6, 0.42, 0.3), INK, 5)
        rrect(ctx, x - 30, y - 70, 60, 30, 10)
        rgba(ctx, INK)
        ctx.set_line_width(7)
        ctx.stroke()
    text(ctx, label, x, y + 105, 32, INK)


# =================================================================== SYSTEM
def system(S):
    ctx, lt, t = S.ctx, S.lt, S.t
    warm = ramp(lt, S.tb("isnt") - 0.1, S.tb("isnt") + 0.6)
    P.corridor(ctx, t)
    spots = P.corridor_doors(ctx, ["HELP", "HR", "SUPPORT", "COMPLAINTS", "FEEDBACK", "OPEN?"])
    for (x, y, k) in spots:
        P.lock(ctx, x, y, 90 * k, open_k=warm)
    if warm > 0:
        glow(ctx, 540, 640, 900 * warm, (1, 0.9, 0.55), 0.6 * warm)
    # list items, timed to the words
    t1 = S.wt("list", "Complaint")
    t2 = S.wt("list", "Phone")
    t3 = S.wt("list", "Places")
    fade = 1 - ramp(lt, S.tb("believe"), S.tb("believe") + 0.4)
    if lt > t1 and fade > 0:
        def vortex():
            for i in range(5):
                ctx.arc(250, 820, 30 + i * 22, t * 4 + i, t * 4 + i + 4.2)
                rgba(ctx, (0.3, 0.2, 0.45), 0.8 - i * 0.12)
                ctx.set_line_width(10)
                ctx.stroke()
            k = clamp((lt - t1) / 1.6)
            px = lerp(500, 250, ease_in(k))
            py = lerp(1000, 820, ease_in(k))
            s = 1 - ease_in(k)
            if s > 0.02:
                ctx.save()
                ctx.translate(px, py)
                ctx.rotate(k * 8)
                ctx.scale(s, s)
                P.card(ctx, -55, -70, 110, 140, WHITE, 10, shadow=False)
                text(ctx, "FORM", 0, -30, 26, INK)
                for j in range(3):
                    ctx.rectangle(-35, -5 + j * 24, 70, 8)
                    rgba(ctx, (0.7, 0.72, 0.8))
                    ctx.fill()
                ctx.restore()
        alpha_group(ctx, fade * S.pop(t1, 0.3), vortex)
    if lt > t2 and fade > 0:
        def hold():
            P.card(ctx, 640, 700, 360, 220, WHITE, 26)
            text(ctx, "ON HOLD", 820, 760, 40, (0.85, 0.3, 0.35))
            secs = int(2 * 3600 + 47 * 60 + (lt - t2) * 397)
            text(ctx, f"{secs // 3600}:{secs // 60 % 60:02d}:{secs % 60:02d}", 820, 830, 56, INK)
            text(ctx, "your call is important to us", 820, 885, 22, (0.5, 0.5, 0.6), bold=False)
            for i in range(3):
                ny = 690 - ((t * 60 + i * 40) % 120)
                text(ctx, "~", 700 + i * 110, ny, 50, (0.55, 0.45, 0.95), a=0.8)
        scaled(ctx, 820, 810, S.pop(t2, 0.4) * fade, hold)
    if lt > t3 and fade > 0:
        def warn():
            P.bubble(ctx, 540, 470, 320, 170, tail=(0, 1), c=(1, 0.95, 0.85))
            ctx.move_to(540, 400)
            ctx.line_to(600, 520)
            ctx.line_to(480, 520)
            ctx.close_path()
            fill_stroke(ctx, (1, 0.75, 0.2), INK, 5)
            text(ctx, "!", 540, 510, 70, INK)
        sh = S.shake(t3 + 0.3, 0.6, 6)
        scaled(ctx, 540 + sh[0], 470, S.pop(t3, 0.4) * fade, warn)
    # Sam walking down the corridor
    walking = lt < S.tb("believe")
    S.char("sam", 540, 1300, 0.9, walk=t * 7, walk_amt=0.6 if walking else 0.0,
           look=(0.0, -0.5) if walking else (0.0, 0.3), arms=[(0, "down"), (S.tb("isnt"), "open")])
    # "Is it me?"
    bk = S.pop(S.tb("believe") + 1.2, 0.4) * (1 - ramp(lt, S.tb("isnt"), S.tb("isnt") + 0.2))
    if bk > 0:
        scaled(ctx, 540, 720, bk, lambda: (P.thought(ctx, 540, 720, 400, 230),
                                           text(ctx, "Is it me?", 540, 740, 56, INK)))
    ik = S.pop(S.tb("isnt") + 0.1, 0.5)
    if ik > 0:
        scaled(ctx, 540, 720, ik, lambda: P.pill(ctx, "It's not you.", 540, 720, 70, (1, 0.85, 0.35)))
    S.lumi(930, 290, 0.6, look=(-0.5, 0.6))


# =================================================================== WHY
def why(S):
    ctx, lt, t = S.ctx, S.lt, S.t
    ctx.set_source(vgrad(ctx, 0, H, [(0, (0.98, 0.84, 0.86)), (1, (0.9, 0.82, 0.96))]))
    ctx.paint()
    for i in range(6):
        ctx.arc((i * 211) % W, (i * 337) % 1300 + 200, 90 + i * 15, 0, 2 * math.pi)
        rgba(ctx, WHITE, 0.18)
        ctx.fill()
    tk = ramp(lt, S.tb("target") + 1.5, S.tb("target") + 2.5)
    if tk > 0:
        alpha_group(ctx, 0.55 * tk, lambda: P.target(ctx, 540, 1050, 420))
    fade = 1 - ramp(lt, S.tb("target") + 0.6, S.tb("target") + 1.2)
    for i, tag in enumerate(("harm1", "harm2")):
        s = S.pop(S.tb(tag), 0.5) * fade
        if s <= 0:
            continue
        cx = 290 + i * 500

        def panel(i=i, cx=cx, tag=tag):
            P.card(ctx, cx - 230, 230, 460, 400, WHITE, 36)
            P.pill(ctx, f"HARM #{i + 1}", cx, 290, 34, (1, 0.8, 0.3) if i == 0 else (0.6, 0.8, 1))
            text(ctx, "The hit" if i == 0 else "The silence", cx, 590, 56, INK)
            if i == 0:
                P.heart(ctx, cx, 450, 150, crack=ramp(lt, S.tb(tag) + 0.3, S.tb(tag) + 0.6))
            else:
                P.bubble(ctx, cx - 20, 430, 230, 130, tail=(-1, 1))
                text(ctx, "...", cx - 20, 450, 60, (0.6, 0.6, 0.7))
                scaled(ctx, cx + 80, 470, S.pop(S.tb(tag) + 0.4, 0.35),
                       lambda: P.lock(ctx, cx + 80, 470, 110))
        scaled(ctx, cx, 430, s, panel)
    feel_k = ramp(lt, S.wt("harm2", "You're"), S.wt("harm2", "You're") + 0.6)

    def feelings(c, hands, bw, bh):
        if feel_k > 0:
            hx = (hands[0][0] + hands[1][0]) / 2
            hy = (hands[0][1] + hands[1][1]) / 2
            P.scribble_ball(c, hx, hy - 30, 90 * feel_k * (1 + 0.05 * math.sin(t * 5)), t)

    arms = [(0, "down"), (S.wt("harm2", "You're") - 0.2, "hold"), (S.tb("target") + 0.5, "down")]
    S.char("sam", 540, 1290, 1.05, arms=arms, look=(0, 0.3), hold_item=feelings)
    S.lumi(130, 800, 0.58, look=(0.6, 0.3))


# =================================================================== FLIP
def flip(S):
    ctx, lt, t = S.ctx, S.lt, S.t
    ctx.set_source(vgrad(ctx, 0, H, [(0, (0.25, 0.2, 0.4)), (1, (0.45, 0.32, 0.55))]))
    ctx.paint()
    for x, a in ((280, 0.18), (820, 0.18)):
        ctx.move_to(x - 60, 0)
        ctx.line_to(x + 60, 0)
        ctx.line_to(x + 260, 1300)
        ctx.line_to(x - 260, 1300)
        ctx.close_path()
        rgba(ctx, (1, 0.95, 0.75), a)
        ctx.fill()
    P.ground(ctx, 1220, (0.35, 0.28, 0.45))
    gone = ramp(lt, S.tb("confession") - 0.6, S.tb("confession") - 0.1)
    if gone < 1:
        a = 1 - gone
        ned_s = S.wt("why", "prankster")
        alpha_group(ctx, a, lambda: S.char("ned", 290, 1215, 0.85, walk=t * 16, walk_amt=1.2,
                                            arms="run", look=(1.0, -0.1)))
        if a > 0:
            motion_lines(ctx, 290 + 80, 1060, dirx=1, a=0.5 * a)
        # Marsh hiding behind a door
        def marsh_door():
            S.char("marsh", 860, 1215, 0.8, look=(-1.0, 0.0), arms="hold")
            rrect(ctx, 650, 640, 170, 580, 8)
            fill_stroke(ctx, (0.62, 0.45, 0.32), INK, 6)
            ctx.arc(680, 940, 13, 0, 2 * math.pi)
            fill_stroke(ctx, (1, 0.82, 0.3), INK, 4)
        alpha_group(ctx, a, marsh_door)
        for at, lab, x in ((ned_s, "Why run?", 290), (S.wt("why", "troll"), "Why hide?", 790)):
            s = S.pop(at, 0.4) * a
            if s > 0:
                scaled(ctx, x, 760, s, lambda lab=lab, x=x: P.pill(ctx, lab, x, 760, 50, WHITE))
    k1 = S.pop(S.tb("strength"), 0.45) * (1 - ramp(lt, S.tb("worth") - 0.1, S.tb("worth") + 0.2))
    if k1 > 0:
        def strength():
            P.card(ctx, 120, 420, 840, 220, WHITE, 36)
            text(ctx, "HIDING IS NOT", 540, 510, 70, INK)
            text(ctx, "STRENGTH", 540, 600, 84, (0.85, 0.3, 0.35))
        scaled(ctx, 540, 530, k1, strength)
    k2 = S.pop(S.tb("worth"), 0.45) * (1 - ramp(lt, S.tb("confession") - 0.3, S.tb("confession")))
    if k2 > 0:
        def worth():
            P.card(ctx, 120, 400, 840, 270, WHITE, 36)
            text(ctx, "Says a lot about THEM.", 540, 490, 52, INK)
            text(ctx, "Nothing about", 540, 570, 52, INK)
            text(ctx, "YOUR WORTH.", 540, 640, 62, (0.95, 0.6, 0.15))
        scaled(ctx, 540, 535, k2, worth)
    if lt > S.tb("confession") - 0.4:
        s = S.pop(S.tb("confession") - 0.4, 0.5)
        S.char("sam", 540, 1215, 1.05 * s, look=(0.0, -0.3), arms=[(0, "down"), (S.tb("confession") + 0.6, "think")])
        bs = S.pop(S.wt("confession", "confession") - 0.2, 0.4)
        if bs > 0:
            scaled(ctx, 540, 640, bs, lambda: P.bulb(ctx, 540, 640, 1.0, 1.0))
    lx = 540 if lt < S.tb("confession") - 0.5 else lerp(540, 880, ramp(lt, S.tb("confession") - 0.5, S.tb("confession")))
    ly = 320 if lt < S.tb("confession") - 0.5 else lerp(320, 420, ramp(lt, S.tb("confession") - 0.5, S.tb("confession")))
    S.lumi(lx, ly, 0.8, look=(0, 0.6))
    if lt < S.tb("strength"):
        mag_x = 540 + math.sin(t * 1.4) * 260
        ctx.save()
        ctx.translate(mag_x, 560)
        ctx.arc(0, 0, 70, 0, 2 * math.pi)
        rgba(ctx, (0.85, 0.95, 1), 0.35)
        ctx.fill_preserve()
        rgba(ctx, INK)
        ctx.set_line_width(10)
        ctx.stroke()
        ctx.move_to(50, 50)
        ctx.line_to(110, 110)
        ctx.set_line_width(22)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()
        ctx.restore()


# =================================================================== TOOLKIT
LENS_COLORS = [(1.0, 0.85, 0.45), (0.62, 0.86, 0.95), (0.98, 0.72, 0.62), (0.72, 0.9, 0.62),
               (0.85, 0.75, 0.98), (1.0, 0.75, 0.82), (0.6, 0.88, 0.8)]


def rays(ctx, cx, cy, t, c=(1, 1, 1), a=0.25, n=16):
    for i in range(n):
        ang = t * 0.15 + i * 2 * math.pi / n
        ctx.move_to(cx, cy)
        ctx.arc(cx, cy, 2400, ang, ang + math.pi / n)
        ctx.close_path()
    rgba(ctx, c, a)
    ctx.fill()


def toolkit(S):
    ctx, lt, t = S.ctx, S.lt, S.t
    ctx.set_source(vgrad(ctx, 0, H, [(0, (1.0, 0.86, 0.6)), (1, (1.0, 0.95, 0.8))]))
    ctx.paint()
    rays(ctx, 540, 1000, t)
    open_k = ramp(lt, S.tb("reveal"), S.tb("reveal") + 0.5)
    P.ground(ctx, 1240, (0.98, 0.82, 0.55))
    P.toolbox(ctx, 540, 1180, 1.0, open_k, t)
    n = len(LENS_LIST)
    for i in range(n):
        at = S.tb("lenses") + 0.2 + i * 0.22
        k = ease_out(clamp((lt - at) / 0.6))
        if k <= 0:
            continue
        row, col = divmod(i, 5)
        tx, ty = 150 + col * 195, 560 + row * 165
        x, y = lerp(540, tx, k), lerp(1060, ty, k) - math.sin(k * math.pi) * 120
        P.lens_icon(ctx, x, y, 58 * (0.4 + 0.6 * k), i + 1, LENS_COLORS[i % len(LENS_COLORS)])
    if open_k > 0:
        for i in range(10):
            ang = i * 0.63 + t
            d = 160 + 60 * math.sin(t * 2 + i)
            star(ctx, 540 + math.cos(ang) * d, 980 + math.sin(ang) * d * 0.5, 16, (1, 1, 0.8),
                 open_k)
    k = S.pop(S.tb("reveal") + 0.1, 0.5)
    if k > 0:
        scaled(ctx, 540, 330, k, lambda: (title_slam(ctx, "YOUR DIGNITY", 540, 300, 92, 1.0),
                                          title_slam(ctx, "TOOLKIT", 540, 410, 110, 1.0,
                                                     (0.3, 0.8, 0.72))))
    lift = ramp(lt, S.tb("lenses"), S.tb("lenses") + 0.5)
    S.char("sam", 870, 1250, 0.9, look=(-0.6, -0.3),
           arms=[(0, "think"), (S.tb("reveal"), "cover"), (S.tb("lenses"), "cheer")])
    S.lumi(190 - 40 * lift, 820 + 260 * lift, 0.7, look=(0.5, 0.2))


# =================================================================== LENSES
def lens_base(S, n, title, color):
    ctx, lt, t = S.ctx, S.lt, S.t
    ctx.set_source(vgrad(ctx, 0, H, [(0, shade(color, 0.35)), (1, color)]))
    ctx.paint()
    for i in range(14):  # soft floating dots
        x = (i * 157 + t * (8 + i % 3 * 4)) % (W + 120) - 60
        y = (i * 263) % 1250 + 120
        ctx.arc(x, y, 18 + (i % 4) * 10, 0, 2 * math.pi)
        rgba(ctx, WHITE, 0.25)
        ctx.fill()
    ctx.rectangle(0, GROUND, W, H - GROUND)
    rgba(ctx, shade(color, -0.12))
    ctx.fill()
    ctx.move_to(0, GROUND)
    ctx.line_to(W, GROUND)
    rgba(ctx, INK, 0.5)
    ctx.set_line_width(4)
    ctx.stroke()
    k = S.pop(0.15, 0.5)
    if k > 0:
        def header():
            P.lens_icon(ctx, 160, 245, 52, n, WHITE)
            text(ctx, f"LENS {n}", 250, 232, 46, INK, align="left")
            text(ctx, "of 15", 250, 276, 30, shade(color, -0.55), align="left")
            font(ctx, 86)
            lines = wrap(ctx, title, 900)
            if len(lines) > 1:
                font(ctx, 74)
                lines = wrap(ctx, title, 940)
            for i, ln in enumerate(lines):
                text(ctx, ln, 540, (390 if len(lines) == 1 else 372) + i * 80,
                     86 if len(lines) == 1 else 74, WHITE, outline=INK,
                     olw=15, shadow=(6, 8, (0, 0, 0), 0.2))
        scaled(ctx, 540, 320, k, header)
    font(ctx, 86)
    return len(wrap(ctx, title, 900))


def lens1(S, color):
    ctx, lt, t = S.ctx, S.lt, S.t
    clear = ramp(lt, S.wt("fog", "Naming"), S.wt("fog", "fog", end=True))
    tag = S.pop(S.tb("fog") + 0.2, 0.5)
    if tag > 0:
        def nametag():
            P.card(ctx, 250, 560, 580, 330, WHITE, 30)
            rrect(ctx, 250, 560, 580, 100, 30)
            rgba(ctx, (0.9, 0.3, 0.35))
            ctx.fill()
            ctx.rectangle(250, 620, 580, 40)
            ctx.fill()
            rrect(ctx, 250, 560, 580, 330, 30)
            rgba(ctx, INK)
            ctx.set_line_width(5)
            ctx.stroke()
            text(ctx, "THAT WAS A", 540, 630, 50, WHITE)
            text(ctx, "HIT-AND-HIDE", 540, 790, 74, INK)
        scaled(ctx, 540, 725, tag, nametag)
    for i in range(6):
        ang = i * 1.05
        d = 60 + 600 * ease_in(clear)
        x = 540 + math.cos(ang) * d + math.sin(t + i) * 15
        y = 730 + math.sin(ang) * d * 0.4
        P.cloud(ctx, x, y, 1.5 + 0.3 * (i % 2), a=0.92 * (1 - clear) * clamp(tag * 2),
                c=(0.82, 0.84, 0.9))
    if clear > 0.9:
        for i in range(5):
            star(ctx, 300 + i * 120, 560 + 30 * math.sin(t * 3 + i), 18, (1, 1, 0.7), 1 - ramp(lt, S.te("fog"), S.te("fog") + 1))
    S.char("sam", 220, GROUND, 0.85, look=(1.0, -0.4),
           arms=[(0, "think"), (S.tb("sam"), "point")])


def lens2(S, color):
    ctx, lt, t = S.ctx, S.lt, S.t
    t_in = S.wt("breathe", "in")
    t_hold = S.wt("breathe", "hold")
    t_out = S.wt("breathe", "out")
    t_end = S.wt("breathe", "Feel")
    r = keyed(lt, [(t_in - 0.2, 150), (t_hold, 250), (t_out, 250), (t_end, 150)])
    r += 4 * math.sin(t * 2)
    label = ""
    if t_in - 0.2 <= lt < t_hold:
        label = "Breathe in"
    elif t_hold <= lt < t_out:
        label = "Hold"
    elif t_out <= lt < t_end + 0.3:
        label = "Breathe out"
    cs = S.pop(S.tb("breathe") - 0.3, 0.5) * (1 - ramp(lt, S.tb("shield") - 0.2, S.tb("shield") + 0.3))
    if cs > 0:
        def circle():
            for k in range(3):
                ctx.arc(540, 760, r + k * 26, 0, 2 * math.pi)
                rgba(ctx, WHITE, 0.25 - k * 0.07)
                ctx.fill()
            ctx.arc(540, 760, r, 0, 2 * math.pi)
            fill_stroke(ctx, (0.75, 0.9, 1.0), INK, 5)
            if label:
                text(ctx, label, 540, 776, 46, INK)
        scaled(ctx, 540, 760, cs, circle)
    feet = ramp(lt, S.wt("breathe", "feet") - 0.1, S.wt("breathe", "feet") + 0.2) * (1 - ramp(lt, S.te("breathe"), S.te("breathe") + 0.6))
    if feet > 0:
        glow(ctx, 540, GROUND - 10, 170, (1, 1, 0.7), 0.8 * feet)
    closed = 0.0
    if t_in - 0.2 <= lt < t_end + 0.2:
        closed = 0.85
    S.char("sam", 540, GROUND, 0.95, look=(0, 0.1), blink=closed,
           arms=[(0, "down"), (t_in - 0.2, "open"), (t_end, "down"), (S.tb("shield"), "hips")])
    sk = S.pop(S.wt("shield", "shield") - 0.3, 0.5)
    if sk > 0:
        for i in range(3):
            pk = ((lt - S.tb("shield")) * 0.9 + i * 0.33) % 1.0
            px = lerp(1150, 760, ease_in(pk) if pk < 0.7 else 1) + (0 if pk < 0.7 else (pk - 0.7) * 600)
            py = 800 + i * 110 + (0 if pk < 0.7 else -(pk - 0.7) * 300)
            P.arrow(ctx, px + 120, py, px, py, (0.85, 0.3, 0.35), 9, 26)
        scaled(ctx, 700, 980, sk, lambda: P.shield(ctx, 700, 980, 230, a=0.95, glow_k=1.0))


def lens3(S, color):
    ctx, lt, t = S.ctx, S.lt, S.t
    lines = ["Date: Mon, 9:14 am", "What: idea cut off", "Said: \"Don't waste", "   our time\"",
             "Who saw: Jo, Kim, Priya", "Felt: embarrassed"]
    rev = clamp((lt - S.tb("write") - 0.3) / (S.te("write") - S.tb("write") + 0.5))
    nk = S.pop(S.tb("title") + 0.4, 0.5)
    if nk > 0:
        scaled(ctx, 420, 760, nk, lambda: P.notebook(ctx, 90, 520, 650, 500, lines, rev))
    sk = S.pop(S.wt("solid", "personal"), 0.4)
    if sk > 0:
        scaled(ctx, 680, 560, sk, lambda: (P.lock(ctx, 690, 575, 90),
                                           P.pill(ctx, "PERSONAL", 690, 650, 28, (1, 0.85, 0.35))))
    mk = ramp(lt, S.wt("solid", "blurry"), S.wt("solid", "solid", end=True))
    if lt > S.wt("solid", "blurry") - 0.3:
        bx, by = 880, 820
        a = S.pop(S.wt("solid", "blurry") - 0.3, 0.4)
        if mk < 1:
            for i in range(4):
                P.cloud(ctx, bx + math.sin(t * 2 + i) * 20, by + math.cos(t * 2 + i) * 10, 0.8,
                        a=0.5 * (1 - mk) * clamp(a), c=(0.7, 0.72, 0.82))
        if mk > 0:
            scaled(ctx, bx, by, ease_out_back(mk), lambda: (
                P.card(ctx, bx - 95, by - 85, 190, 170, (0.45, 0.75, 0.95), 18),
                text(ctx, "FACTS", bx, by + 14, 46, WHITE, outline=INK, olw=8)))
    S.char("sam", 900, GROUND, 0.82, look=(-0.8, -0.3), arms=[(0, "down"), (S.tb("write"), "hold")],
           hold_item=pencil)


def pencil(ctx, hands, bw, bh):
    hx, hy = hands[0]
    ctx.save()
    ctx.translate(hx, hy)
    ctx.rotate(-0.8)
    rrect(ctx, -10, -80, 20, 90, 4)
    fill_stroke(ctx, (1, 0.8, 0.3), INK, 4)
    ctx.move_to(-10, 10)
    ctx.line_to(10, 10)
    ctx.line_to(0, 32)
    ctx.close_path()
    fill_stroke(ctx, (0.95, 0.85, 0.7), INK, 3)
    ctx.restore()


def lens4(S, color):
    ctx, lt, t = S.ctx, S.lt, S.t
    words = S.tags["email"]["words"]
    n_shown = sum(1 for w in words if w[1] - S.t0 <= lt)
    body = " ".join(w[0] for w in words[:n_shown])
    send_t = S.te("email") + 0.1
    fly = ramp(lt, send_t + 0.2, send_t + 0.8)
    ck = S.pop(S.tb("after") - 0.2, 0.5)
    if ck > 0 and fly < 1:
        def email():
            ctx.save()
            ctx.translate(lerp(0, 600, ease_in(fly)), lerp(0, -500, ease_in(fly)))
            s = 1 - 0.7 * fly
            ctx.translate(540, 760)
            ctx.scale(s, s)
            ctx.translate(-540, -760)
            P.card(ctx, 100, 500, 880, 560, WHITE, 30)
            rrect(ctx, 100, 500, 880, 80, 30)
            rgba(ctx, (0.35, 0.55, 0.9))
            ctx.fill()
            ctx.rectangle(100, 550, 880, 30)
            ctx.fill()
            text(ctx, "New message", 140, 554, 36, WHITE, align="left")
            text(ctx, "To: Mr. Marsh", 140, 630, 32, (0.4, 0.4, 0.5), align="left", bold=False)
            text(ctx, "Subject: Quick follow-up", 140, 675, 32, (0.4, 0.4, 0.5), align="left", bold=False)
            ctx.move_to(140, 700)
            ctx.line_to(940, 700)
            rgba(ctx, (0.85, 0.85, 0.9))
            ctx.set_line_width(3)
            ctx.stroke()
            font(ctx, 36, bold=False)
            lines = wrap(ctx, body, 780)
            for i, ln in enumerate(lines[:6]):
                text(ctx, ln, 140, 755 + i * 46, 36, INK, align="left", bold=False)
            pressed = 0.9 if send_t - 0.1 < lt < send_t + 0.2 else 1.0
            ctx.save()
            ctx.translate(860, 1010)
            ctx.scale(pressed, pressed)
            P.pill(ctx, "Send", 0, 0, 38, (0.35, 0.75, 0.5))
            ctx.restore()
            ctx.restore()
        scaled(ctx, 540, 760, ck, email)
    sk = S.pop(send_t + 0.7, 0.45)
    if sk > 0:
        def sent():
            P.card(ctx, 260, 600, 560, 300, WHITE, 36)
            P.checkbox(ctx, 540, 700, 110, clamp((lt - send_t - 0.8) / 0.4))
            text(ctx, "Sent. Now it's visible.", 540, 840, 44, INK)
        scaled(ctx, 540, 750, sk, sent)
    S.char("sam", 180, GROUND, 0.8, look=(0.8, -0.5),
           arms=[(0, "down"), (S.tb("email"), "type"), (send_t, "fist"), (send_t + 1.2, "hips")])


def lens5(S, color):
    ctx, lt, t = S.ctx, S.lt, S.t
    sk = S.pop(S.tb("questions") + 0.4, 0.5)
    if sk > 0:
        P.road_sign(ctx, 540, 640, 0.95 * sk, "TWO-WAY STREET", "two")
    qk = S.pop(S.tb("sam"), 0.4) * (1 - ramp(lt, S.te("sam") + 0.8, S.te("sam") + 1.1))
    if qk > 0:
        scaled(ctx, 300, 780, qk, lambda: (P.bubble(ctx, 300, 780, 180, 150, tail=(0, 1)),
                                           P.qmark(ctx, 300, 830, 120)))
    S.char("sam", 290, GROUND, 0.9, look=(1.0, -0.2), arms=[(0, "down"), (S.tb("sam"), "open"),
                                                          (S.te("sam"), "down")])
    S.char("marsh", 800, GROUND, 0.82, look=(-1.0, -0.1),
           arms=[(0, "cross"), (S.tb("marsh_thinks") - 0.3, "think")])
    bk = S.pop(S.tb("marsh_thinks") + 0.5, 0.4)
    if bk > 0:
        scaled(ctx, 820, 800, bk, lambda: P.bulb(ctx, 820, 800, 0.7, 0.7))


def lens6(S, color):
    ctx, lt, t = S.ctx, S.lt, S.t
    parts = [("What happened", 0), ("How I felt", 1), ("What I need", 2), ("One clear request", 3)]
    pops = [S.tb("parts") + d for d in (0.0, 1.0, 1.9, 2.9)]
    hl = [S.wt("sam", "When"), S.wt("sam", "felt"), S.wt("sam", "because"), S.wt("sam", "Could")]
    cur = -1
    if S.tb("sam") - 0.1 <= lt <= S.te("sam") + 0.3:
        for i, h in enumerate(hl):
            if lt >= h - 0.1:
                cur = i
    for i, (lab, icon) in enumerate(parts):
        s = S.pop(pops[i], 0.45)
        if s <= 0:
            continue
        cx = 300 + (i % 2) * 480
        cy = 640 + (i // 2) * 245
        big = 1.08 if i == cur else 1.0

        def c(i=i, cx=cx, cy=cy, lab=lab, icon=icon):
            if i == cur:
                glow(ctx, cx, cy, 300, (1, 1, 0.7), 0.7)
            P.card(ctx, cx - 215, cy - 105, 430, 210, WHITE if i != cur else (1, 0.97, 0.8), 30)
            ctx.arc(cx - 140, cy - 10, 48, 0, 2 * math.pi)
            fill_stroke(ctx, LENS_COLORS[i], INK, 4)
            text(ctx, str(i + 1), cx - 140, cy + 6, 50, INK)
            font(ctx, 40)
            ls = wrap(ctx, lab, 240)
            for j, ln in enumerate(ls):
                text(ctx, ln, cx + 50, cy - 5 + (j - (len(ls) - 1) / 2) * 46 + 14, 40, INK)
            if lt > S.tb("clear"):
                P.checkbox(ctx, cx + 175, cy - 70, 54, clamp((lt - S.tb("clear") - i * 0.15) / 0.3))
        scaled(ctx, cx, cy, s * big, c)
    S.char("sam", 540, GROUND + 30, 0.72, look=(0, -0.6),
           arms=[(0, "down"), (S.tb("sam"), "open"), (S.tb("clear"), "hips")])


def lens7(S, color):
    ctx, lt, t = S.ctx, S.lt, S.t
    px, ph, amt = walk_x(lt, [(0, 1250), (S.tb("priya") - 0.2, 760)])
    tog = ramp(lt, S.tb("together") + 0.3, S.tb("together") + 1.0)
    if lt < S.tb("together") + 1.0:
        a = 1 - tog
        if lt > S.tb("title"):
            alpha_group(ctx, a, lambda: (P.bubble(ctx, 320, 760, 160, 110, tail=(0, 1)),
                                         text(ctx, "...", 320, 778, 54, (0.6, 0.6, 0.7))))
        if lt > S.tb("priya"):
            alpha_group(ctx, a, lambda: (P.bubble(ctx, px, 740, 160, 110, tail=(0, 1)),
                                         text(ctx, "...", px, 758, 54, (0.6, 0.6, 0.7))))
    if tog > 0:
        s = ease_out_back(tog)

        def big():
            for k in range(3):
                ctx.arc(540, 700, 230 + k * 40 + (t * 60) % 40, -0.6, 0.6)
                rgba(ctx, INK, 0.4 - k * 0.12)
                ctx.set_line_width(6)
                ctx.stroke()
                ctx.arc(540, 700, 230 + k * 40 + (t * 60) % 40, math.pi - 0.6, math.pi + 0.6)
                ctx.stroke()
            P.bubble(ctx, 540, 700, 420, 190, tail=(0, 1), tail_x=0.5)
            text(ctx, "Together", 540, 720, 70, INK)
        scaled(ctx, 540, 700, s, big)
    S.char("sam", 330, GROUND, 0.92, look=(1.0, 0.0) if lt < S.tb("together") else (0.3, 0.0),
           arms=[(0, "down"), (S.tb("together") + 0.3, "fist")])
    S.char("priya", px, GROUND, 0.92, walk=ph, walk_amt=amt,
           look=(-1.0, 0.0) if lt < S.tb("together") else (-0.3, 0.0),
           arms=[(0, "down"), (S.tb("priya"), "cover"), (S.tb("remind"), "point_l"),
                 (S.tb("together") + 0.3, ((40, 120), (14, 4)))])


OUTLETS = [("handbook", "Handbook"), ("Human", "HR"), ("manager's", "Manager's manager"),
           ("union", "Union / worker rep"), ("assistance", "Employee assistance"),
           ("Outside", "Worker rights groups"), ("lawyer", "Employment lawyer")]


def lens8(S, color):
    ctx, lt, t = S.ctx, S.lt, S.t
    mk = S.pop(S.tb("title") + 0.5, 0.5)
    pts = [(220, 640), (520, 590), (820, 650), (760, 790), (430, 790), (220, 900), (600, 940)]
    if mk > 0:
        def board():
            P.card(ctx, 70, 520, 940, 500, (0.98, 0.93, 0.8), 30)
            ctx.move_to(*pts[0])
            for p in pts[1:]:
                ctx.line_to(*p)
            rgba(ctx, (0.75, 0.55, 0.35))
            ctx.set_line_width(6)
            ctx.set_dash([4, 16])
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.stroke()
            ctx.set_dash([])
            for i, ((w, lab), (x, y)) in enumerate(zip(OUTLETS, pts)):
                at = S.wt("list", w) - 0.1
                s = S.pop(at, 0.4)
                if s <= 0:
                    continue
                scaled(ctx, x, y, s, lambda x=x, y=y, lab=lab, i=i: (
                    P.pin(ctx, x, y, 0.75, LENS_COLORS[i % 7] if i else (0.95, 0.4, 0.4)),
                    P.pill(ctx, lab, x, y + 30, 26, WHITE)))
        scaled(ctx, 540, 770, mk, board)
    lk = S.pop(S.tb("law") + 0.3, 0.45) * (1 - ramp(lt, S.tb("check") - 0.2, S.tb("check")))
    if lk > 0:
        def law():
            P.card(ctx, 130, 610, 820, 300, WHITE, 36)
            P.shield(ctx, 270, 760, 150, (0.5, 0.8, 0.6))
            P.scales_icon(ctx, 270, 765, 0.55)
            text_block(ctx, "Retaliation for good-faith reports is often against the rules", 640, 720,
                       42, 520, INK)
        scaled(ctx, 540, 760, lk, law)
    ck = S.pop(S.tb("check"), 0.4)
    if ck > 0:
        scaled(ctx, 540, 1080, ck, lambda: P.pill(ctx, "Not legal advice: check your local rules", 540,
                                                 1085, 32, (1, 0.9, 0.5)))
    S.char("sam", 150, GROUND, 0.72, look=(0.8, -0.6), arms=[(0, "down"), (S.tb("list"), "think")])


def lens9(S, color):
    ctx, lt, t = S.ctx, S.lt, S.t
    qs = ["Is it safe?", "Is it worth it?", "Do I have a record?", "What's the smallest step?"]
    words = ["safe", "worth", "record", "smallest"]
    ck = S.pop(S.tb("title") + 0.4, 0.5)
    if ck > 0:
        def lst():
            P.card(ctx, 90, 540, 900, 500, WHITE, 36)
            for i, (q, w) in enumerate(zip(qs, words)):
                at = S.wt("qs", w)
                y = 625 + i * 112
                a = ramp(lt, at - 0.3, at)
                text(ctx, q, 230, y + 16, 46, INK if a > 0.5 else (0.75, 0.75, 0.8), align="left")
                P.checkbox(ctx, 160, y, 64, clamp((lt - at - 0.2) / 0.3))
        scaled(ctx, 540, 790, ck, lst)
    S.char("sam", 900, GROUND, 0.7, look=(-0.8, -0.5), arms=[(0, "think"), (S.te("qs"), "hips")])


def lens10(S, color):
    ctx, lt, t = S.ctx, S.lt, S.t
    vk = S.pop(S.tb("vent") - 0.2, 0.45)
    pk = S.pop(S.wt("plan", "plan") - 0.2, 0.45)
    if vk > 0:
        def vent():
            P.card(ctx, 60, 545, 460, 450, WHITE, 32)
            P.pill(ctx, "VENT SAFELY", 290, 600, 36, (1, 0.75, 0.75))
            items = [("friend", "A friend"), ("journal", "A journal"), ("therapist", "A therapist")]
            for i, (w, lab) in enumerate(items):
                s = S.pop(S.wt("vent", w) - 0.1, 0.35)
                if s <= 0:
                    continue
                y = 695 + i * 100
                scaled(ctx, 150, y, s, lambda y=y, i=i: vent_icon(ctx, 150, y, i))
                text(ctx, lab, 210, y + 14, 40, INK, align="left", a=clamp(s))
        scaled(ctx, 290, 755, vk, vent)
    if pk > 0:
        def plan():
            P.card(ctx, 560, 545, 460, 450, WHITE, 32)
            P.pill(ctx, "PLAN CLEARLY", 790, 600, 36, (0.65, 0.88, 0.7))
            for i, lab in enumerate(["Facts", "Options", "Next step"]):
                y = 695 + i * 100
                P.checkbox(ctx, 640, y, 56, clamp((lt - S.wt("plan", "plan") - 0.3 - i * 0.4) / 0.3))
                text(ctx, lab, 690, y + 14, 40, INK, align="left")
        scaled(ctx, 790, 755, pk, plan)
    storm = 1 - ramp(lt, S.wt("plan", "plan") - 0.3, S.wt("plan", "plan") + 0.5)
    if storm > 0.02 and lt > S.tb("title") + 0.3:
        P.weather_cloud(ctx, 540, 1035 - 20, 0.55, t, rain=storm)
    S.char("sam", 540, GROUND + 25, 0.72, look=(0, -0.3),
           arms=[(0, "down"), (S.wt("plan", "plan"), "hips")])


def vent_icon(ctx, x, y, i):
    if i == 0:
        P.avatar(ctx, x, y, 38, (0.98, 0.6, 0.46))
    elif i == 1:
        rrect(ctx, x - 34, y - 42, 68, 84, 8)
        fill_stroke(ctx, (0.55, 0.45, 0.85), INK, 4)
        ctx.rectangle(x - 20, y - 25, 40, 8)
        rgba(ctx, WHITE, 0.8)
        ctx.fill()
    else:
        P.bubble(ctx, x, y - 6, 80, 64, tail=(-1, 1))
        P.heart(ctx, x, y, 40, lw=3)


def lens11(S, color):
    ctx, lt, t = S.ctx, S.lt, S.t
    tags = [("polite", "Polite"), ("brief", "Brief"), ("professional", "Professional")]
    for i, (w, lab) in enumerate(tags):
        s = S.pop(S.wt("polite", w) - 0.1, 0.4)
        if s > 0:
            y = 620 + i * 100
            scaled(ctx, 270, y, s, lambda y=y, lab=lab: P.pill(ctx, lab, 270, y, 44, WHITE))
    gk = S.pop(S.tb("title") + 0.5, 0.5)
    if gk > 0:
        val = 0.08 + 0.05 * math.sin(t * 3)
        if lt < S.tb("noted"):
            val = 0.35 + 0.1 * math.sin(t * 2)
        scaled(ctx, 770, 640, gk, lambda: (P.card(ctx, 600, 520, 340, 240, WHITE, 30),
                                           P.gauge(ctx, 770, 680, 120, val, ""),
                                           text(ctx, "DRAMA METER", 770, 740, 30, INK)))
    fl = 1 - ramp(lt, S.tb("fuel") + 0.3, S.tb("fuel") + 1.2)
    if lt > S.tb("title") + 0.5:
        P.flame(ctx, 600, GROUND - 10, 0.7 * fl * S.pop(S.tb("title") + 0.5, 0.4), t)
        if fl < 1:
            for i in range(3):
                k = (lt - S.tb("fuel") - 0.5 - i * 0.2)
                if 0 < k < 1.5:
                    ctx.arc(600 + math.sin(k * 4 + i) * 20, GROUND - 60 - k * 160, 20 + k * 20, 0, 2 * math.pi)
                    rgba(ctx, (0.7, 0.7, 0.75), 0.5 * (1 - k / 1.5))
                    ctx.fill()
    S.char("sam", 270, GROUND, 0.88, look=(1.0, 0.0), arms=[(0, "down"), (S.tb("noted"), "relax")])
    S.char("marsh", 830, GROUND, 0.8, look=(-1.0, 0.0),
           arms=[(0, "hips"), (S.tb("marsh_confused"), "shrug"), (S.tb("fuel") + 0.5, "down")])


def lens12(S, color):
    ctx, lt, t = S.ctx, S.lt, S.t
    ck = S.pop(S.wt("weather", "weather") - 0.2, 0.45)
    if ck > 0:
        def forecast():
            P.card(ctx, 470, 545, 540, 300, WHITE, 30)
            text(ctx, "MOOD FORECAST", 740, 610, 40, (0.35, 0.5, 0.85))
            text(ctx, "Grumpy: 80%", 740, 680, 40, INK)
            text(ctx, "Scattered criticism", 740, 740, 36, INK, bold=False)
            text(ctx, "Not a measure of YOU", 740, 810, 34, (0.85, 0.3, 0.35))
        scaled(ctx, 740, 670, ck, forecast)
    P.weather_cloud(ctx, 270, 720, 0.85, t, rain=1 - ramp(lt, S.tb("leave") + 1.0, S.tb("leave") + 2))
    S.char("marsh", 270, GROUND, 0.75, look=(0.5, 0.0), emo="annoyed", arms="cross")
    lk = ramp(lt, S.tb("leave"), S.te("leave") + 0.8)
    if lt > S.tb("leave"):
        for i in range(5):
            k = clamp(lk * 1.3 - i * 0.08)
            if i == 0:
                x = lerp(300, 780, smooth(k))
                y = lerp(860, 1030, smooth(k)) - math.sin(k * math.pi) * 150
                glow(ctx, x, y, 70, (1, 1, 0.6), 0.8)
                P.card(ctx, x - 50, y - 35, 100, 70, (1, 0.95, 0.6), 10, shadow=False)
                star(ctx, x, y, 22, (1, 0.75, 0.2), points=5)
            else:
                x = lerp(300, 1300, ease_in(k)) + i * 30
                y = 860 + i * 40 - k * 200 + math.sin(t * 5 + i) * 10
                ctx.save()
                ctx.translate(x, y)
                ctx.rotate(k * 6 + i)
                P.card(ctx, -45, -30, 90, 60, (0.9, 0.9, 0.95), 8, shadow=False)
                ctx.restore()
        if lk > 0.3:
            P.pill(ctx, "KEEP", 790, 900, 34, (1, 0.9, 0.5), a=clamp((lk - 0.3) * 4))
    S.char("sam", 790, GROUND, 0.85, look=(-0.7, -0.4),
           arms=[(0, "down"), (S.tb("leave") + 0.5, "hold")])


def lens13(S, color):
    ctx, lt, t = S.ctx, S.lt, S.t
    rk = S.pop(S.tb("title") + 0.4, 0.5)
    if rk > 0:
        def board():
            P.card(ctx, 70, 540, 940, 500, (0.75, 0.9, 1.0), 30)
            ctx.save()
            rrect(ctx, 70, 540, 940, 500, 30)
            ctx.clip()
            ctx.rectangle(70, 800, 940, 260)
            rgba(ctx, (0.55, 0.8, 0.5))
            ctx.fill()
            # exit ramp curving up and away to the right
            ctx.move_to(430, 935)
            ctx.curve_to(640, 930, 760, 860, 1020, 760)
            ctx.line_to(1020, 840)
            ctx.curve_to(790, 920, 690, 960, 560, 965)
            ctx.close_path()
            fill_stroke(ctx, (0.5, 0.51, 0.57), INK, 4)
            # main road
            ctx.rectangle(60, 935, 960, 80)
            fill_stroke(ctx, (0.45, 0.46, 0.52), INK, 4)
            for x in range(90, 1010, 110):
                ctx.rectangle(x, 970, 55, 9)
            rgba(ctx, (1, 0.9, 0.4))
            ctx.fill()
            ctx.restore()
            rrect(ctx, 70, 540, 940, 500, 30)
            rgba(ctx, INK)
            ctx.set_line_width(5)
            ctx.stroke()
            label = "YOUR CHOICE" if lt > S.wt("choice", "choice") - 0.2 else "EXIT: OPTIONS"
            rrect(ctx, 834, 700, 12, 140, 4)
            fill_stroke(ctx, (0.6, 0.62, 0.68), INK, 3)
            rrect(ctx, 700, 630, 280, 86, 14)
            fill_stroke(ctx, (0.2, 0.55, 0.35), INK, 5)
            text(ctx, label, 840, 687, 34, WHITE)
        scaled(ctx, 540, 790, rk, board)
        items = [(0.0, "Resume"), (1.4, "People"), (2.9, "Savings")]
        for i, (d, lab) in enumerate(items):
            s = S.pop(S.tb("steps") + d, 0.4)
            if s <= 0:
                continue
            x = 185 + i * 165
            y = 650

            def it(i=i, x=x, y=y, lab=lab):
                ctx.arc(x, y, 64, 0, 2 * math.pi)
                fill_stroke(ctx, WHITE, INK, 4)
                if i == 0:
                    P.doc_icon(ctx, x, y - 4, 0.44)
                elif i == 1:
                    P.network_icon(ctx, x, y + 4, 0.6, t)
                else:
                    P.piggy(ctx, x - 6, y + 6, 0.5)
                text(ctx, lab, x, y + 100, 32, INK)
            scaled(ctx, x, y, s, it)
    S.char("sam", 210, GROUND, 0.8, look=(0.8, -0.4),
           arms=[(0, "down"), (S.tb("steps"), "present"), (S.wt("choice", "choice"), "hips")])


def lens14(S, color):
    ctx, lt, t = S.ctx, S.lt, S.t
    t0 = S.tb("steps")
    steps = [(t0 + 0.2, "Screenshot"), (t0 + 1.3, "Report"), (t0 + 2.4, "Mute / block"),
             (S.wt("steps", "trust") - 0.2, "Tell someone")]
    pk = S.pop(S.tb("title") + 0.4, 0.5)
    if pk > 0:
        def ph():
            ctx.save()
            ctx.translate(0, 40)
            P.phone(ctx, 300, 500, 420, 640, (1, 1, 1))
            P.avatar(ctx, 390, 640, 36, (0.64, 0.84, 0.32), -0.6)
            text(ctx, "@NoReplyNed", 440, 632, 26, (0.35, 0.55, 0.15), align="left")
            rrect(ctx, 350, 690, 320, 110, 24)
            fill_stroke(ctx, (1, 0.9, 0.9), INK, 3)
            text(ctx, "lol go away", 510, 758, 36, INK)
            if lt > steps[1][0]:
                s = S.pop(steps[1][0], 0.3)
                scaled(ctx, 640, 690, s, lambda: P.flag_icon(ctx, 640, 690, 0.5))
            if lt > steps[2][0]:
                s = S.pop(steps[2][0], 0.35)

                def stamp():
                    ctx.save()
                    ctx.translate(510, 900)
                    ctx.rotate(-0.15)
                    rrect(ctx, -150, -45, 300, 90, 14)
                    rgba(ctx, (0.9, 0.25, 0.3))
                    ctx.set_line_width(8)
                    ctx.stroke()
                    text(ctx, "BLOCKED", 0, 22, 58, (0.9, 0.25, 0.3))
                    ctx.restore()
                scaled(ctx, 510, 900, lerp(2, 1, s) if s < 1 else 1, stamp)
            if steps[0][0] < lt < steps[0][0] + 0.35:
                rrect(ctx, 322, 522, 376, 596, 40)
                rgba(ctx, WHITE, 1 - (lt - steps[0][0]) / 0.35)
                ctx.fill()
            ctx.restore()
        scaled(ctx, 510, 860, pk, ph)
    for i, (at, lab) in enumerate(steps):
        s = S.pop(at, 0.35)
        if s <= 0:
            continue
        y = 610 + i * 150
        x = 870

        def ic(i=i, x=x, y=y, lab=lab):
            ctx.arc(x, y, 58, 0, 2 * math.pi)
            fill_stroke(ctx, WHITE, INK, 4)
            if i == 0:
                P.camera_icon(ctx, x, y, 0.55)
            elif i == 1:
                P.flag_icon(ctx, x + 6, y, 0.5)
            elif i == 2:
                P.mute_icon(ctx, x - 4, y, 0.55)
            else:
                P.heart(ctx, x, y + 6, 60)
            text(ctx, lab, x, y + 88, 28, INK)
        scaled(ctx, x, y, s, ic)
    if lt > S.tb("argue"):
        k = clamp((lt - S.tb("argue")) / 2.5)
        S.char("ned", lerp(560, 1150, k), GROUND - 4, 0.38, walk=t * 18, walk_amt=1.2, arms="run",
               look=(1, 0), emo="scared")
    S.char("sam", 150, GROUND, 0.75, look=(0.8, -0.3),
           arms=[(0, "down"), (S.tb("steps"), "point"), (S.tb("argue"), "shrug"),
                 (S.te("argue"), "relax")])


def lens15(S, color):
    ctx, lt, t = S.ctx, S.lt, S.t
    ok = ramp(lt, S.tb("title") + 0.6, S.tb("title") + 2.0)
    P.open_door_light(ctx, 390, 560, 300, 520, ok, t)
    px, ph, amt = walk_x(lt, [(0, -150), (S.tb("listen"), 230)])
    S.char("priya", px, GROUND, 0.85, walk=ph, walk_amt=amt, look=(1.0, -0.1),
           arms=[(0, "down"), (S.tb("human"), "wave")])
    S.char("sam", 860, GROUND, 0.88, look=(-1.0, -0.1),
           arms=[(0, "down"), (S.tb("title") + 1.0, "present"), (S.tb("human"), "wave2")])
    if lt > S.tb("listen") + 1.0:
        k = clamp((lt - S.tb("listen") - 1.0) / 0.5)
        P.arrow(ctx, 330, 860, 760, 860, (0.3, 0.7, 0.55), 12 * k + 0.1, 34)
        P.arrow(ctx, 760, 940, 330, 940, (0.95, 0.5, 0.45), 12 * k + 0.1, 34)
    hk = ramp(lt, S.tb("human"), S.tb("human") + 0.5)
    if hk > 0:
        S.char("extra1", 90, GROUND + 40, 0.55 * ease_out_back(hk), emo="happy", arms="wave2",
               look=(0.5, -0.3))
        S.char("extra2", 1000, GROUND + 40, 0.55 * ease_out_back(hk), emo="happy", arms="cheer",
               look=(-0.5, -0.3))
        for i in range(6):
            k = ((lt - S.tb("human")) * 0.5 + i / 6) % 1
            P.heart(ctx, 200 + i * 140 + math.sin(t * 2 + i) * 20, 1100 - k * 500, 50,
                    a_col(i), lw=4)


def a_col(i):
    return ((0.95, 0.4, 0.5), (1, 0.6, 0.4), (0.95, 0.5, 0.7))[i % 3]


LENS_FN = {1: lens1, 2: lens2, 3: lens3, 4: lens4, 5: lens5, 6: lens6, 7: lens7, 8: lens8,
           9: lens9, 10: lens10, 11: lens11, 12: lens12, 13: lens13, 14: lens14, 15: lens15}


def lens_scene(S):
    n, title = S.sc["lens"]
    color = LENS_COLORS[(n - 1) % len(LENS_COLORS)]
    lens_base(S, n, title, color)
    LENS_FN[n](S, color)
    # Lumi narrates every lens from the top-right corner
    S.lumi(965, 250, 0.5, look=(-0.6, 0.3))


# =================================================================== OUTRO
def outro(S):
    ctx, lt, t = S.ctx, S.lt, S.t
    ctx.set_source(vgrad(ctx, 0, H, [(0, (0.55, 0.6, 0.95)), (0.45, (1.0, 0.7, 0.65)),
                                     (0.75, (1.0, 0.88, 0.62)), (1, (1.0, 0.95, 0.8))]))
    ctx.paint()
    rise = ramp(lt, 0, 6)
    P.sun(ctx, 230, lerp(1180, 900, rise), 100, t)
    ctx.move_to(-50, 1300)
    ctx.curve_to(250, 1120, 830, 1120, W + 50, 1300)
    ctx.line_to(W + 50, H)
    ctx.line_to(-50, H)
    ctx.close_path()
    fill_stroke(ctx, (0.5, 0.78, 0.48), INK, 6)
    end = S.tb("end")
    grow = ramp(lt, S.wt("person", "person") - 0.4, S.wt("person", "person") + 0.3)
    sam_s = lerp(0.55, 1.0, ease_out_back(grow))
    end_k = ramp(lt, end, end + 0.6)
    S.char("sam", lerp(540, 330, end_k), lerp(1225, 1300, end_k), sam_s * lerp(1, 0.72, end_k),
           look=(0, 0.0),
           arms=[(0, "down"), (S.tb("person"), "open"), (S.tb("sam"), "hips"),
                 (S.tb("share"), "wave"), (end, "wave2")])
    affs = [("feelings", "Your feelings make sense."), ("voice", "Your voice matters."),
            ("next", "There's always a next step.")]
    fade = 1 - ramp(lt, S.tb("crisis") - 0.3, S.tb("crisis"))
    for i, (w, s_) in enumerate(affs):
        k = S.pop(S.wt("next", w) - 0.2, 0.45) * fade
        if k > 0:
            y = 330 + i * 120
            scaled(ctx, 540, y, k, lambda s_=s_, y=y, i=i: P.pill(ctx, s_, 540, y, 50,
                                                               (WHITE, (1, 0.9, 0.5), (0.75, 0.92, 0.85))[i]))
    ck = S.pop(S.tb("crisis"), 0.45) * (1 - ramp(lt, S.tb("share") - 0.3, S.tb("share")))
    if ck > 0:
        def crisis():
            P.card(ctx, 90, 280, 900, 380, WHITE, 40)
            P.heart(ctx, 540, 370, 90)
            text(ctx, "Feeling unsafe or hopeless?", 540, 480, 50, INK)
            text_block(ctx, "Reach out to someone you trust, or a local crisis line.", 540, 550, 40,
                       780, (0.3, 0.3, 0.42), bold=False)
        scaled(ctx, 540, 470, ck, crisis)
    sk = S.pop(S.tb("share") + 0.2, 0.45) * (1 - ramp(lt, end - 0.2, end + 0.2))
    if sk > 0:
        scaled(ctx, 540, 420, sk, lambda: (P.pill(ctx, "SAVE IT", 340, 420, 52, (1, 0.85, 0.35)),
                                           P.pill(ctx, "SHARE IT", 740, 420, 52, (0.6, 0.85, 1))))
    lumi_x, lumi_y = lerp(925, 545, end_k), lerp(780, 1200, end_k)
    # end card
    ek = S.pop(end, 0.55)
    if ek > 0:
        def endcard():
            P.card(ctx, 70, 170, 940, 900, WHITE, 44)
            text(ctx, "THE HIT-AND-HIDE", 540, 270, 70, (1, 0.78, 0.2), outline=INK, olw=14)
            text(ctx, "15 lenses for keeping your dignity", 540, 328, 36, (0.35, 0.35, 0.48))
            for i, (n, title) in enumerate(LENS_LIST):
                y = 398 + i * 44
                ctx.arc(150, y - 12, 19, 0, 2 * math.pi)
                fill_stroke(ctx, LENS_COLORS[i % 7], INK, 3)
                text(ctx, str(n), 150, y - 1, 24, INK)
                text(ctx, title, 190, y, 34, INK, align="left")
        scaled(ctx, 540, 620, ek, endcard)
    if lt > end:
        k = ramp(lt, end + 0.4, end + 1.0)
        S.char("priya", lerp(1250, 760, k), 1300, 0.68, emo="happy", arms="wave2", look=(-0.5, -0.2),
               walk=lt * 6, walk_amt=1 - k if k < 1 else 0)
    S.lumi(lumi_x, lumi_y, 0.72, look=(-0.4, 0.3))


SCENE_FN = {"cold_open": cold_open, "online": online, "advice": advice, "meeting": meeting,
            "door": door, "fear": fear, "system": system, "why": why, "flip": flip,
            "toolkit": toolkit, "outro": outro}


def draw_scene(S):
    fn = SCENE_FN.get(S.sc["id"])
    if fn is None and S.sc.get("lens"):
        fn = lens_scene
    fn(S)
