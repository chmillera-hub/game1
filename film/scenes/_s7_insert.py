"""_s7_insert.py -- Scene 7's insert A3: TINY HAND, HUGE CLAW (private helper of s7_bread.py).

The image the whole scene turns on, laid out on its own as a feature insert is: the dragon's
great open palm comes in from the right (his coat sleeve, the plum cuff), the golden half-loaf
lies in it, and the grandmother's tiny hand comes in from the upper left (her lavender
cardigan sleeve, the knit cuff): she lowers the bread into his palm, lets go, slides her hand
onto his claw-fingers, pats them twice -- and leaves it there. A held moment. Then she lifts it
away and his great fingers begin, very carefully, to close round the bread.

Everything is the library's own parts at their TRUE relative size -- base.hand with each
creature's hand build (his: 56 long, claws, sand palm pads; hers: 20 long, plump), their
materials, the props loaf -- drawn in shared body units (one scale for both), so his hand is
2.8 times hers. Light: the low golden sun from the left (rims on the left edges, the loaf's torn
face lit, the steam glowing), over a soft, defocused plate of the bench seat between them (the
coloring book on the seat lies blurred under their hands: the bread passes over the stone).

draw_insert(cr, t, st, T, light) paints the frame (before the scene's light layer and post);
insert_light(lc, t, st, T) adds its light. T is a dict of the scene's times (see s7_bread.py).
"""

import math

from film.lib import core, fx
from film.lib import props as P
from film.lib import characters as ch
from film.lib.characters import base as B

# the composition, in body units (1 unit = 1 px of the cast at scale 1.0) about the screen
# point ORIGIN, at K screen px per unit (the insert is ~11.5x the bench plane's 0.78)
ORIGIN = (1000.0, 590.0)
K = 12.5
D_WR = (17.5, 6.3)              # his wrist (the hand points left, toward her)
D_ANG = math.pi + 0.13          # ... fingers rising a little toward her
D_SLEEVE = [(100.0, 30.0), (60.0, 15.0), (D_WR[0] + 2.0, D_WR[1] + 0.5)]
G_SHOULDER = (-84.0, -26.0)     # her shoulder, just off the left edge (her whole arm is only 41 long)
BREAD_C = (6.0, -9.5)           # the half's centre resting on his palm
BREAD_SIZE = ch.GNOME_LOAF * 0.94
BREAD_TILT = -0.2               # lying back a little in his palm, its torn face up toward her and the sun
# where her hand rests on his claw-fingers (wrist) and how it lies
G_REST_WR = (-42.0, -9.5)
G_REST_ANG = 0.3
STEAM_FROM = (-4.0, -16.0)      # the torn crumb face (toward her, toward the sun)
D_HAND = ch.REGISTRY["dragon"].HAND_LEN     # 56: wrist to fingertip, his rig's own hand
G_HAND = ch.REGISTRY["gnome"].HAND_LEN      # 20: hers


def _pt(x, y):
    return ORIGIN[0] + x * K, ORIGIN[1] + y * K


def _r(t, a, b, e="inout_sine"):
    return core.ramp(t, a, b, e)


def _lerp2(a, b, u):
    return (core.lerp(a[0], b[0], u), core.lerp(a[1], b[1], u))


# ----------------------------------------------------------------------------------------
# the plate: the bench seat between them, soft (built once)
# ----------------------------------------------------------------------------------------

def build_plate(g, L, book_draw, kind="golden"):
    """A defocused plate of the set behind the hands: the garden + the bench seen at seat level
    between them, the coloring book lying on the seat, her mossy lap at the left and his dark
    coat at the right -- all soft (fx.Layer blur), so only colour and light remain."""
    cam = core.Camera(926.0, 806.0, 6.2)

    def draw(cr):
        g.paint_back(cr, cam, 0.0, kind)
        with cam.view(cr, 1.0):
            g.draw_bench(cr, 0.0, L, part="back", sag=0.3, sag_u=0.83)
            g.draw_bench(cr, 0.0, L, part="front", sag=0.3, sag_u=0.83)
            book_draw(cr)
            # her lap (mossy skirt) and cardigan at the left, his coat and knee at the right:
            # soft masses (this plate is heavily out of focus)
            for (x, y, rx, ry, c, a) in ((812.0, 856.0, 40.0, 22.0, ch.GNOME_COLORS["skirt"], 0.85),
                                          (802.0, 806.0, 20.0, 30.0, ch.GNOME_COLORS["sleeve"], 0.8),
                                          (1030.0, 846.0, 64.0, 40.0, ch.DRAGON_COLORS["coat"], 0.95),
                                          (1062.0, 790.0, 40.0, 56.0, ch.DRAGON_COLORS["coat"], 0.9)):
                core.src(cr, core.mul(core.col(c), L.key), a)
                core.ellipse(cr, x, y, rx, ry)
                cr.fill()
        # the low sun from the left: a warm wash on the left of the plate, cooler shade right
        cr.set_source(core.linear(0.0, 0.0, core.W, 0.0, [(0.0, core.alpha("#ffd596", 0.42)),
                                                          (0.5, core.alpha("#ffcf8a", 0.12)),
                                                          (1.0, core.alpha("#2a1c2a", 0.28))]))
        cr.paint()
        cr.set_source(core.radial(-60.0, 80.0, 1300.0, [(0.0, core.alpha("#fff0c8", 0.35)), (1.0, core.alpha("#fff0c8", 0.0))]))
        cr.paint()

    return fx.Layer(draw, blur=26.0, res=0.5, opaque=True)


# ----------------------------------------------------------------------------------------
# the hands
# ----------------------------------------------------------------------------------------

def _dragon_arm(cr, t, T, L, lw, curl):
    """His sleeve, cuff and great open hand, palm up (the pads show), fingers toward her."""
    M = ch.dragon_mats()
    dip = 0.9 * B.wobble(t, T["give"], 5.0, 6.0) / 1.35            # the bread lands: a tiny give
    rise = -1.2 * (1.0 - _r(t, T["cut"], T["give"] - 0.05))        # (the match: still settling down)
    br = B.breathing(t, 0.2, 6) * 0.35
    wr = (D_WR[0], D_WR[1] + dip + rise + br)
    sl = [(x, y + (dip + rise + br) * (i / 2.0)) for i, (x, y) in enumerate(D_SLEEVE)]
    sl[-1] = (wr[0] + 2.0, wr[1] + 0.5)
    sleeve, out = B.tube_paths(cr, sl, [17.0, 14.5, 12.8], lw, samples=5, tension=0.7)
    B.shade(cr, sleeve, M["coat"], L, lw, outline=out, size=30.0)
    fdx, fdy = math.cos(D_ANG), math.sin(D_ANG)
    cuff, cout = B.ellipse_paths(cr, wr[0] - fdx * 3.0, wr[1] - fdy * 3.0, 8.5, 15.0, lw, D_ANG)
    B.shade(cr, cuff, M["lining"], L, lw, outline=cout, size=14.0, rim=0.5)
    pose = dict(B.HAND_POSES["offer"])
    # her touch: his fingers give a small involuntary flex as her hand lands on them (he is not
    # used to being touched), then hold very still -- and his great thumb curls in a little
    # toward her hand, as if to hold it
    flex = 0.07 * B.wobble(t, T["pat1"] + 0.03, 4.0, 5.0) / 1.35
    tremble = 0.01 * math.sin(t * 13.0) * core.window(t, T["pat1"], T["let"], 0.2, 0.2) + flex
    k = core.window(t, T["pat1"] + 0.25, T["let"] + 0.15, 0.35, 0.3)
    th0 = pose["thumb"]
    pose["thumb"] = (core.lerp(th0[0], -0.45, k), core.lerp(th0[1], 0.3, k))
    return B.hand(cr, wr[0] + fdx * 5.0, wr[1] + fdy * 5.0, D_ANG, D_HAND, pose, M["scales"], L, lw, flip=True,
                  claw=ch.DRAGON_COLORS["claw"], claw_len=0.08, pad=ch.DRAGON_COLORS["belly"], show_palm=True,
                  finger_w=1.05, curl_add=curl + tremble, detail=2)


def gnome_hand_state(t, T):
    """Her wrist (body units), finger angle, hand pose name and curl, through the insert:
    holding the bread as she lowers it -> lifting off it -> onto his fingers (two pats, then
    resting, a small squeeze) -> lifting away."""
    hold_wr = (BREAD_C[0] - 27.0, BREAD_C[1] - 4.0)               # gripping the half's left side
    hold_ang = 0.12
    lower = 1.0 - _r(t, T["cut"], T["give"], "out_sine")          # 1 -> 0 as she lowers it
    if t < T["give"] + 0.02:
        return (hold_wr[0], hold_wr[1] - 7.0 * lower), hold_ang, "grip", 0.0
    if t < T["pat1"]:
        u = _r(t, T["give"] + 0.02, T["pat1"], "inout_sine")
        p = _lerp2(hold_wr, G_REST_WR, u)
        arc = 7.0 * math.sin(math.pi * u)
        return (p[0], p[1] - arc), core.lerp(hold_ang, G_REST_ANG, u), "relaxed" if u < 0.6 else "flat", 0.0
    if t < T["let"]:
        ph = t - T["pat1"]
        lift = 2.4 * abs(math.sin(min(ph, 0.5) / 0.5 * 2.0 * math.pi)) if ph < 0.5 else 0.0
        squeeze = 0.16 * core.window(t, T["pat1"] + 0.55, T["let"], 0.15, 0.2)
        return (G_REST_WR[0], G_REST_WR[1] - lift), G_REST_ANG, "flat", squeeze
    u = _r(t, T["let"], T["let"] + 0.3, "inout_sine")
    away = (G_REST_WR[0] - 14.0, G_REST_WR[1] - 12.0)
    p = _lerp2(G_REST_WR, away, u)
    return (p[0], p[1] - 3.0 * math.sin(math.pi * u)), G_REST_ANG - 0.2 * u, "relaxed", 0.0


def _gnome_arm(cr, t, T, L, lw):
    M = ch.gnome_mats()
    wr, ang, pose, curl = gnome_hand_state(t, T)
    # her short arm: the elbow just off the left edge follows the wrist a little (two-bone
    # lengths kept: upper arm 21, forearm 20), the upper arm up toward her shoulder off frame
    fdx, fdy = math.cos(ang), math.sin(ang)
    end = (wr[0] - fdx * 0.5, wr[1] - fdy * 0.5)
    sh = (G_SHOULDER[0] + 0.25 * (wr[0] - G_REST_WR[0]), G_SHOULDER[1] + 0.3 * (wr[1] - G_REST_WR[1]))
    ex, ey, _wx, _wy = B.ik2(sh[0], sh[1], end[0], end[1], 21.0 * 1.12, 20.0 * 1.12, 1.0)
    el = (ex, ey)
    sleeve, out = B.tube_paths(cr, [sh, el, end], [8.6, 7.6, 6.4], lw, samples=5, tension=0.7)
    B.shade(cr, sleeve, M["sleeve"], L, lw, outline=out, size=15.0, rim=0.6)
    cx_, cy_ = wr[0] - fdx * 1.5, wr[1] - fdy * 1.5
    cuff, cout = B.ellipse_paths(cr, cx_, cy_, 4.4, 7.4, lw, ang)
    pal = B.shade(cr, cuff, M["cuff"], L, lw, outline=cout, size=8.0, rim=0.5)
    nx, ny = -fdy, fdx
    B.detail_lines(cr, [[(cx_ + nx * 5.2 * k2 - fdx * 2.5, cy_ + ny * 5.2 * k2 - fdy * 2.5),
                         (cx_ + nx * 5.2 * k2 + fdx * 2.5, cy_ + ny * 5.2 * k2 + fdy * 2.5)]
                        for k2 in (-0.6, 0.0, 0.6)], lw * 0.5, pal.line, 0.45)
    return B.hand(cr, wr[0] + fdx * 2.0, wr[1] + fdy * 2.0, ang, G_HAND, pose, M["skin"], L, lw,
                  flip=False, claw=None, show_palm=False, pad=ch.GNOME_COLORS["nose"], finger_w=1.32,
                  finger_len=0.84, palm_w=1.2, curl_add=curl, detail=2)


def bread_pos(t, T):
    """The half's centre (body units) and its little landing squash."""
    lower = 1.0 - _r(t, T["cut"], T["give"], "out_sine")
    c = (BREAD_C[0], BREAD_C[1] - 7.0 * lower)
    sq = 0.035 * B.wobble(t, T["give"], 5.0, 6.0) / 1.35
    return c, sq


def _bread(cr, t, T, L):
    (x, y), sq = bread_pos(t, T)
    cr.save()
    cr.translate(x, y + BREAD_SIZE * 0.33)          # squash about its base
    cr.rotate(BREAD_TILT)
    cr.scale(1.0 + sq * 0.6, 1.0 - sq)
    cr.translate(0.0, -BREAD_SIZE * 0.33)
    P.draw_bread(cr, 0.0, 0.0, BREAD_SIZE, L, t, state="half", face=-1.0, seed=2)
    cr.restore()


# ----------------------------------------------------------------------------------------
# the frame
# ----------------------------------------------------------------------------------------

def push(t, T):
    """The insert's slow push-in (hands plane) and its drift."""
    u = core.clamp((t - T["cut"]) / max(1e-6, T["end"] - T["cut"]))
    z = 1.0 + 0.045 * core.inout_sine(u)
    dx = 3.0 * core.noise1(t * 0.35, 71)
    dy = 2.0 * core.noise1(t * 0.3, 72)
    return z, dx, dy


def draw_insert(cr, t, st, T, L):
    """Paint the whole insert frame (the scene adds its light layer and post afterwards)."""
    z, dx, dy = push(t, T)
    # the plate (a slower push: it is far behind the hands)
    zp = 1.0 + 0.3 * (z - 1.0)
    cr.save()
    cr.translate(ORIGIN[0], ORIGIN[1])
    cr.scale(zp, zp)
    cr.translate(-ORIGIN[0] + dx * 0.3, -ORIGIN[1] + dy * 0.3)
    st["insert_plate"].paint(cr)
    cr.restore()
    # the hands plane
    cr.save()
    cr.translate(ORIGIN[0] + dx, ORIGIN[1] + dy)
    cr.scale(z * K, z * K)
    lw_d = B.line_for(ch.DRAGON_LINE, z * K)
    lw_g = B.line_for(B.LINE, z * K)
    # contact shadow of her hand on his fingers / the bread on his palm (soft, under)
    curl = 0.32 * _r(t, T["let"] + 0.05, T["end"], "inout_sine")
    _dragon_arm(cr, t, T, L, lw_d, curl)
    (bx, by), _sq = bread_pos(t, T)
    B.occlusion(cr, bx + 1.0, by + BREAD_SIZE * 0.3, BREAD_SIZE * 0.42, 3.4, "#3a2316", 0.35)
    _bread(cr, t, T, L)
    gw, _ga, _gp, _gc = gnome_hand_state(t, T)
    if T["give"] + 0.1 < t < T["let"] + 0.2:
        k = core.window(t, T["give"] + 0.1, T["let"] + 0.2, 0.15, 0.15)
        B.occlusion(cr, gw[0] + 8.0, gw[1] + 6.0, 9.0, 3.0, "#2a2a26", 0.3 * k)
    _gnome_arm(cr, t, T, L, lw_g)
    # warm steam from the torn crumb, lit by the sun
    sx, sy = bread_pos(t, T)[0]
    sx, sy = sx + (STEAM_FROM[0] - BREAD_C[0]), sy + (STEAM_FROM[1] - BREAD_C[1])
    for i, t0 in enumerate((T["snap"], T["snap"] + 0.5, T["snap"] + 1.0, T["snap"] + 1.5, T["snap"] + 2.0)):
        fx.smoke(cr, t, t0, sx + 1.5 * (i % 3) - 2.0, sy, n=8, dur=1.9, rise=48.0, drift=(-7.0 + 2.5 * (i % 3), -4.0),
                 size=2.9, color="#fff3e2", alpha=0.42, seed=120 + i, scale=1.0, spread=0.35)
    cr.restore()
    # sunlit motes drifting through the shot
    fx.dust(cr, t, (0.0, 0.0, core.W, core.H * 0.8), n=26, color="#ffe2b0", alpha=0.32, size=(1.2, 3.4),
            seed=33, drift=(9.0, -4.0), twinkle=0.7)


def insert_light(lc, t, st, T):
    """The insert's light: the low sun spilling in from the upper left, the loaf's warm glow."""
    z, dx, dy = push(t, T)
    # the low sun just off the upper left: a broad warm spill and soft shafts across the frame
    fx.glow(lc, -160.0, 60.0, 1700.0, "#ffc27a", 0.3)
    fx.god_rays(lc, -120.0, -60.0, 0.5, 0.5, 2300.0, "#ffd49a", t, n=7, width=(40.0, 260.0), alpha=0.06, seed=14,
                shimmer=0.25)
    (bx, by), _sq = bread_pos(t, T)
    px = ORIGIN[0] + dx + bx * K * z
    py = ORIGIN[1] + dy + by * K * z
    fx.glow(lc, px - 30.0, py, 320.0 * z, "#ffbe6a", 0.3)
    fx.glow(lc, px - 70.0, py - 30.0, 130.0 * z, "#fff0c8", 0.22)
    # her hand on his: a small warm glow where they touch (the heart of the shot)
    if T["pat1"] - 0.1 < t < T["let"] + 0.3:
        k = core.window(t, T["pat1"] - 0.1, T["let"] + 0.3, 0.25, 0.3)
        gx, gy = ORIGIN[0] + dx + (G_REST_WR[0] + 7.0) * K * z, ORIGIN[1] + dy + (G_REST_WR[1] + 6.0) * K * z
        fx.glow(lc, gx, gy, 200.0 * z, "#ffcf90", 0.14 * k)
