"""s05 -- the pocket calculator ("awkward").

Continues s04: Curiosity walked off into the dark side tunnel (to SHAFT A) and WAITED there;
Tiredness follows it in. The whole scene plays INSIDE that dark side tunnel, lit only by
Curiosity's glow, his teal eyes, a little warm spill from the corridor mouth (screen-right)
and, once he arrives, Embarrassment's flashlight. Embarrassment comes up the tunnel from the
dark (screen-left, from the shaft). Two custom views of the tunnel (drawn here):
  * A: the reverse view from inside, looking back out at the bright arched mouth (the same
       arch we saw in s04) -- the opening shot;
  * B: the tunnel interior side-on (ribbed concrete vault, SHAFT A <- stencil), mouth off right.

Shot list (every time derives from cues / line timings, see shots()):
  A1  0 .. steps          reverse view, slow push: Curiosity sits alone in the dark, ears low, its
                          glow the only light; Tiredness steps in through the bright arch and walks
                          up to it; it hears him, looks back, hopeful; he stops, glances down at
                          it: a tiny "fine" (lid drop, small nod, exhale). It perks a notch.
  B2  .. l01 "What"       side-on wide: echoing footsteps from the dark: ears shoot up, both look
                          left; torchlight bobs in; Curiosity scrambles behind his legs; Emb walks
                          in with the flashlight, stops, the beam swings up onto Tiredness's face:
                          jolt (blush 0.5). "Tiredness?!"
  E3  .. l01.end+.4       Emb medium: "What are you doing down here?" (whisper-shout, glance back)
  T4  .. l02.end+.35      Tiredness medium in the beam, squinting, hands in the pocket: "Oh. Hey."
                          (flat; one lazy little wave)
  W5  .. l03.end+.1       two-shot: the beam drifts down and finds one big eye peeking out; Emb
                          freezes. "Is that... Thing One?"
  E6  .. l04 "glowing"    Emb close: eyes climb from the creature to Tiredness's eyes
  T7  .. l05 "I"          Tiredness close, SUPER chill (hands in pocket, flat, lazy pocket shrug):
                          "Oh, yeah. A critter bit me,"
  W8  .. l05.end+.25      two-shot: "...I fell out of a building, and now I can see in the dark."
                          he stays flat; Emb escalates: eyes, jaw, glasses slip, hands to his head
  E9  .. l05b.end+.3      Emb CU FREAKING OUT: hands on his head, blush 0.9, glasses askew, sweat
                          flying: "You fell out of a WHAT?!"
  T10 .. l05c.end+.3      Tiredness CU: a beat, "It's been a day." lazy shrug, slow blink
  E11 .. led              Emb CU: the long slow blink; hands come down, he pushes his glasses straight
  W12 .. conflict+.95     three-shot: the red LED blinks in his pocket; eyes slide down to it one by
                          one; he pinches the recorder out and holds it in his palm
  R14 .. conflict+2.3     INSERT: the HushCorp recorder in his palm: blinking "REC", running counter,
                          mic grille, logo, a little level meter listening
  E15 .. click-.1         Emb CU: at Tiredness, at the recorder; blush; a breath
  R16 .. l06 "Huh."+.12   INSERT: his thumb presses pause: click, "PAUSED", LED off, meter flat
  E17 .. wink+.62         Emb close: "Huh. My "pocket calculator"... just stopped working." -- dry,
                          knowing; then the WINK with a small knowing smile (slow push-in)
  T18 .. l07-.25          Tiredness + Curiosity: his faintest smile back; it looks up and grins
  W19 .. l07.end          two-shot: "The control room is on level nine. Take my keycard." handoff
  K20 .. l08              insert: the keycard (LVL 9) in his bandaged hand, a glint
  E21 .. l08.end+.35      Emb close: "And Tiredness? Be careful." sincere, slow
  W22 .. end              two-shot: a small nod; he turns toward CONTROL (the mouth) and sets off,
                          Curiosity trots after him; Emb watches them go
"""
import math

import cairocffi as cairo

from engine import core, human, creatures, sets, fx, props
from engine.core import seg, clamp, lerp, smoothstep, ease_in_out, ease_out, ease_out_back, state_at
from engine.props import fs, rect, ell, polyf, line, curve

INK = core.PAL["ink"]
S = 0.75                 # people in the tunnel world (same as s04's service tunnel)
SC = 0.74                # Curiosity
FY = 1500                # feet line
XT = 790                 # Tiredness (facing left, toward the deep end)
XE = 325                 # Embarrassment (facing right)
C0 = 610                 # Curiosity at the start (beside him, a little ahead)
CH = 785                 # hiding behind his legs (head peeks out on the left)
C1 = 640                 # out again, sitting by his front foot
TK = dict(outfit="sewer", bandage=True, headphones=None, hood=0.0, power=0.6)
T_FACE = (XT - 64, 912)          # Tiredness's face (beam target)
CUR_EYE = (CH - 82, 1318)        # Curiosity's peeking (visible) eye
FLASH_S = 0.5
REC_S = 0.25                     # the recorder in his hand
WARM = "#ffe9c4"
DARKC = "#04070b"


# =========================================================================== small helpers
def tw(t, keys):
    """Keyframes [(t, v[, ease]), ...]; the ease of a key applies to the segment ending
    there (default ease_in_out). Values may be tuples."""
    if t <= keys[0][0]:
        return keys[0][1]
    for a, b in zip(keys, keys[1:]):
        if t < b[0]:
            e = b[2] if len(b) > 2 else ease_in_out
            u = e((t - a[0]) / (b[0] - a[0])) if b[0] > a[0] else 1.0
            if isinstance(a[1], (tuple, list)):
                return tuple(lerp(p, q, u) for p, q in zip(a[1], b[1]))
            return lerp(a[1], b[1], u)
    return keys[-1][1]


def fk(t, table):
    return {key: tw(t, ks) for key, ks in table.items()}


def addf(*ds):
    out = {}
    for d in ds:
        for key, v in d.items():
            out[key] = out.get(key, 0.0) + v
    return out


def bump(t, t0, t1, amp=1.0):
    if t <= t0 or t >= t1:
        return 0.0
    return amp * math.sin(math.pi * (t - t0) / (t1 - t0)) ** 2


class _no_fringe_drips:
    """The "sewer" outfit hangs little blue drips from Tiredness's damp fringe; on his
    face they read as SWEAT (the user's note: he must look super chill, no sweat). Skip
    just those drops while he is drawn (scoped swap, restored right after)."""
    def __enter__(self):
        self.f = getattr(human, "_drop", None)
        if self.f is not None:
            f = self.f

            def drop(ctx, x, y, r, c, inkw):
                if c == "#a9dff0":
                    ctx.new_path()
                    return None
                return f(ctx, x, y, r, c, inkw)
            human._drop = drop
        return self

    def __exit__(self, *a):
        if self.f is not None:
            human._drop = self.f


# =========================================================================== set B: side-on
BX0, BX1, BY0, BY1 = -900, 2700, -500, 2500
B_BASE = 1300          # far wall meets the floor
B_SPRING = 610         # wall -> vault
B_CEIL = 300           # vault edge (nearest the camera) at the top
B_RIBS = [-460, -40, 380, 800, 1220]
B_MOUTH = 1520         # the tunnel end (opens onto the lit corridor, screen-right)


def b_static(c):
    x0, x1, y0, y1 = BX0, BX1, BY0, BY1
    c.rectangle(x0, y0, x1 - x0, B_CEIL - y0 + 4)
    core.fill(c, "#1e1e24")
    g = cairo.LinearGradient(0, B_CEIL, 0, B_SPRING)
    g.add_color_stop_rgb(0, *core.hexc("#2c2c33")[:3])
    g.add_color_stop_rgb(1, *core.hexc("#46464e")[:3])
    c.rectangle(x0, B_CEIL, x1 - x0, B_SPRING - B_CEIL)
    c.set_source(g)
    c.fill()
    for i_, yy in enumerate((380, 470, 545)):
        line(c, [(x0, yy), (x1, yy)], core.alpha("#55555e", 0.35 + 0.15 * i_), 3)
    # far wall
    c.rectangle(x0, B_SPRING, x1 - x0, B_BASE - B_SPRING)
    core.fill(c, "#55555d")
    c.rectangle(x0, 1010, x1 - x0, B_BASE - 1010)
    core.fill(c, "#4d4d55")
    rect(c, x0, 996, x1 - x0, 16, core.PAL["hush_dk"], 0)
    line(c, [(x0, B_SPRING), (x1, B_SPRING)], "#5f5f68", 8)
    for i_ in range(int((x1 - x0) / 210) + 1):
        xx = x0 + i_ * 210
        line(c, [(xx, B_SPRING + 6), (xx, B_BASE)], "#4b4b53", 3)
        for yy in (700, 880, 1120, 1230):
            core.circle(c, xx + 105, yy, 4.5)
    core.fill(c, "#45454c")
    for i_ in range(10):
        sx = x0 + core.hash01(i_, 51) * (x1 - x0)
        h = 160 + 260 * core.hash01(i_, 52)
        polyf(c, [(sx - 14, B_SPRING + 10), (sx + 14, B_SPRING + 10), (sx + 22, B_SPRING + 10 + h),
                  (sx - 22, B_SPRING + 10 + h)], (0.16, 0.17, 0.2, 0.32), 0)
    # conduit along the wall
    rect(c, x0, 676, x1 - x0, 18, "#5e666a", 3.5)
    line(c, [(x0, 681), (x1, 681)], "#737c80", 4)
    rect(c, x0, 724, x1 - x0, 10, "#3f4448", 2.5)
    # ribs: concrete rings, vertical on the far wall, curving overhead toward the camera
    for rx in B_RIBS:
        c.move_to(rx - 44, B_BASE + 6)
        c.line_to(rx - 44, B_SPRING)
        c.curve_to(rx - 46, B_SPRING - 120, rx - 70, B_CEIL + 80, rx - 120, B_CEIL - 20)
        c.line_to(rx + 120, B_CEIL - 20)
        c.curve_to(rx + 70, B_CEIL + 80, rx + 46, B_SPRING - 120, rx + 44, B_SPRING)
        c.line_to(rx + 44, B_BASE + 6)
        c.close_path()
        fs(c, "#606069", 5)
        line(c, [(rx + 30, B_BASE), (rx + 30, B_SPRING + 4)], "#4e4e56", 6)
        curve(c, [(rx - 34, B_SPRING), (rx - 50, B_SPRING - 160), (rx - 96, B_CEIL)], "#6c6c75", 5)
        for yy in (690, 900, 1150):
            core.circle(c, rx, yy, 6)
            fs(c, "#4a4a52", 2.5)
        rect(c, rx - 16, 668, 32, 34, "#3e4648", 3.5, r=4)
    # stencil: <- SHAFT A (the deep end is screen-left)
    sx, sy = 590, 900
    sc_ = core.alpha("#36363e", 0.95)
    core.text(c, "SHAFT A", sx, sy, 50, sc_, "black")
    polyf(c, [(sx - 196, sy - 18), (sx - 164, sy - 38), (sx - 164, sy + 2)], sc_, 0)
    rect(c, sx - 166, sy - 25, 30, 14, sc_, 0)
    core.text(c, "S-14A", 1010, 1170, 44, core.alpha("#3e3e46", 0.9), "black")
    props.cage_lamp(c, 1010, 760, 0.8, on=0.0, halo=False)          # dead lamp: no power in here
    rect(c, 140, 1060, 90, 120, "#4a4e52", 4.5, r=8)
    line(c, [(160, 1100), (210, 1100)], "#7a6a3a", 5)
    # the tunnel end (right): the mouth frame onto the corridor
    mx = B_MOUTH
    c.rectangle(mx, B_CEIL - 40, x1 - mx, y1 - B_CEIL + 40)
    core.fill(c, "#6d6458")
    polyf(c, [(mx + 40, 1300), (x1, 1300), (x1, y1), (mx + 40, y1)], "#5d564e", 0)
    rect(c, mx + 20, 940, x1 - mx, 22, core.PAL["hush_dk"], 0)
    polyf(c, [(mx - 70, B_BASE + 40), (mx + 60, B_BASE + 40), (mx + 60, B_CEIL - 20), (mx - 70, B_CEIL - 20)],
          "#66666e", 6)
    line(c, [(mx + 30, B_BASE), (mx + 30, B_CEIL)], "#52525a", 8)
    # floor
    c.rectangle(x0, B_BASE, x1 - x0, y1 - B_BASE)
    core.fill(c, "#45454b")
    rect(c, x0, B_BASE - 2, x1 - x0, 34, "#3a3a40", 3.5)
    for i_ in range(int((x1 - x0) / 40)):
        line(c, [(x0 + i_ * 40, B_BASE + 4), (x0 + i_ * 40 + 20, B_BASE + 26)], "#2e2e34", 2.5)
    for i_ in range(-12, 22):
        xx = i_ * 230
        line(c, [(xx, B_BASE + 32), (700 + (xx - 700) * 2.6, y1)], "#3c3c42", 4)
    for yy in (1420, 1560, 1760, 2050):
        line(c, [(x0, yy), (x1, yy)], "#3c3c42", 4)
    ell(c, 420, 1610, 150, 20, "#3a3d46", 0)
    ell(c, 395, 1606, 60, 5, (0.6, 0.65, 0.75, 0.25), 0)
    ell(c, 1150, 1700, 90, 13, "#3a3d46", 0)


def b_dark(c):
    """Dark version: the tunnel under a near-black wash; the corridor's warm light spills
    in at the right end."""
    b_static(c)
    x0, x1, y0, y1 = BX0, BX1, BY0, BY1
    c.rectangle(x0, y0, x1 - x0, y1 - y0)
    core.fill(c, core.alpha(DARKC, 0.86))
    g = cairo.LinearGradient(B_MOUTH + 200, 0, 650, 0)
    g.add_color_stop_rgba(0, 1.0, 0.72, 0.42, 0.5)
    g.add_color_stop_rgba(0.35, 1.0, 0.66, 0.36, 0.13)
    g.add_color_stop_rgba(1, 1.0, 0.6, 0.3, 0.0)
    c.save()
    c.set_operator(cairo.OPERATOR_ADD)
    c.rectangle(650, y0, x1 - 650, y1 - y0)
    c.set_source(g)
    c.fill()
    c.restore()
    c.save()
    c.rectangle(B_MOUTH + 60, B_CEIL - 40, x1 - B_MOUTH, y1)
    c.clip()
    b_static(c)
    c.rectangle(x0, y0, x1 - x0, y1 - y0)
    core.fill(c, core.alpha("#ff9a40", 0.18))
    c.restore()


def b_bg(ctx):
    sets._overscan(ctx, BX0, BY0, BX1, BY1, "#030508", "#060709", "#030508", "#2a2420")
    sets.layer_blit(ctx, "s05_tunB_dark", BX0, BY0, BX1 - BX0, BY1 - BY0, b_dark)


# =========================================================================== set A: reverse view
AF = 1853.0          # focal length (px per unit at depth 1)
AHY = 760.0          # horizon (camera height) on screen
ACX = 540.0
AZC = 680.0          # camera height (units; a person is ~955)
AW2 = 330.0          # tunnel half width
AH = 990.0           # tunnel height
AR = 280.0           # top corner radius
AD_M = 3380.0        # the mouth
AD_C = 4500.0        # the corridor's far wall
A_RIBS = [3380.0, 2930.0, 2480.0, 2030.0, 1580.0, 1130.0]
A_TD0, A_TD1, A_TX0, A_TX1 = 3000.0, 2180.0, 60.0, 112.0   # his walk: depth / lateral
A_CD, A_CX = 1850.0, -150.0                                 # Curiosity sits here


def ap(X, Z, D):
    return (ACX + AF * X / D, AHY - AF * (Z - AZC) / D)


def a_section(c, D, w2=AW2, h=AH, r=AR, inset=0.0, closed=True):
    w2 -= inset
    h -= inset
    r = max(1.0, r - inset)
    x0, y0 = ap(-w2, 0, D)
    x1, _ = ap(w2, 0, D)
    _, yt = ap(0, h, D)
    rr = AF * r / D
    c.move_to(x0, y0)
    c.line_to(x0, yt + rr)
    c.curve_to(x0, yt + rr * 0.45, x0 + rr * 0.45, yt, x0 + rr, yt)
    c.line_to(x1 - rr, yt)
    c.curve_to(x1 - rr * 0.45, yt, x1, yt + rr * 0.45, x1, yt + rr)
    c.line_to(x1, y0)
    if closed:
        c.close_path()


def a_static(c):
    W, H = 1080, 1920
    g = cairo.RadialGradient(ACX, 640, 150, ACX, 900, 1500)
    g.add_color_stop_rgb(0, *core.hexc("#5a5a62")[:3])
    g.add_color_stop_rgb(1, *core.hexc("#3c3c44")[:3])
    c.rectangle(-300, -300, W + 600, H + 600)
    c.set_source(g)
    c.fill()
    for sgn in (-1, 1):
        a1, a2 = ap(sgn * AW2, 480, AD_M), ap(sgn * AW2, 510, AD_M)
        b1, b2 = ap(sgn * AW2, 480, 400), ap(sgn * AW2, 510, 400)
        polyf(c, [a1, a2, b2, b1], "#0f6f6a", 0)
        for Z in (700, 300):
            line(c, [ap(sgn * AW2, Z, AD_M), ap(sgn * AW2, Z, 500)], "#4a4a52", 3)
    line(c, [ap(-AW2 + 40, AH - 60, AD_M), ap(-AW2 + 40, AH - 60, 400)], INK, 20)
    line(c, [ap(-AW2 + 40, AH - 60, AD_M), ap(-AW2 + 40, AH - 60, 400)], "#5e666a", 13)
    W3 = AW2 + 30
    polyf(c, [ap(-W3, 0, AD_M), ap(W3, 0, AD_M), ap(W3, 0, 300), ap(-W3, 0, 300)], "#43434a", 0)
    for X in (-AW2 * 0.45, AW2 * 0.45):
        line(c, [ap(X, 0, AD_M), ap(X, 0, 400)], "#38383e", 3.5)
    for D in (3100, 2700, 2300, 1900, 1500, 1100):
        line(c, [ap(-AW2, 0, D), ap(AW2, 0, D)], "#38383e", 3.5)
    for sgn in (-1, 1):
        polyf(c, [ap(sgn * W3, 0, AD_M), ap(sgn * (AW2 - 40), 0, AD_M), ap(sgn * (AW2 - 40), 0, 400),
                  ap(sgn * W3, 0, 400)], "#36363c", 0)
        line(c, [ap(sgn * (AW2 - 40), 0, AD_M), ap(sgn * (AW2 - 40), 0, 400)], "#2c2c32", 3)
    ell(c, *ap(-120, 0, 2600), 70, 9, "#3a3d46", 0)
    # beyond the mouth: the corridor's far wall (warm lamp light) + its floor
    c.save()
    a_section(c, AD_M)
    c.clip()
    wx0, wy0 = ap(-2400, 1500, AD_C)
    wx1, wb = ap(2400, 0, AD_C)
    c.rectangle(wx0, wy0, wx1 - wx0, wb - wy0)
    core.fill(c, "#7d7468")
    _, ys = ap(0, 480, AD_C)
    _, ys2 = ap(0, 510, AD_C)
    c.rectangle(wx0, ys2, wx1 - wx0, ys - ys2)
    core.fill(c, "#2a8a80")
    for X in (-900, -500, -100, 300, 700):
        xa, ya = ap(X, 0, AD_C)
        _, yb = ap(X, 1400, AD_C)
        line(c, [(xa, ya), (xa, yb)], "#6f675c", 3)
    lx, ly = ap(-150, 1100, AD_C)
    core.radial_glow(c, lx, ly, 420, "#ffcf8a", 0.55)
    fx0, fy0 = ap(-2400, 0, AD_C)
    c.rectangle(fx0, fy0, 3000, 600)
    core.fill(c, "#6a6258")
    line(c, [ap(-2400, 0, AD_C), ap(2400, 0, AD_C)], "#4e483f", 4)
    c.restore()
    for i_, D in enumerate(A_RIBS):
        k = i_ / (len(A_RIBS) - 1)
        lw = AF * 60 / D
        a_section(c, D, inset=-30, closed=False)
        core.stroke(c, INK, lw + 6, cap="butt")
        a_section(c, D, inset=-30, closed=False)
        core.stroke(c, mixc_("#6a6a72", "#4a4a52", k), lw, cap="butt")
        a_section(c, D, inset=-4, closed=False)
        core.stroke(c, core.alpha("#7a7a84", 0.5), lw * 0.18, cap="butt")
    a_section(c, AD_M, inset=-8, closed=False)
    core.stroke(c, INK, 8, cap="butt")


def mixc_(a, b, k):
    return core.mixc(a, b, k)


def a_dark(c):
    a_static(c)
    W, H = 1080, 1920
    c.save()
    c.push_group()
    c.rectangle(-300, -300, W + 600, H + 600)
    core.fill(c, core.alpha(DARKC, 0.87))
    c.set_operator(cairo.OPERATOR_DEST_OUT)
    a_section(c, AD_M)
    core.fill(c, (0, 0, 0, 0.92))
    mx, my = ap(0, 300, AD_M)
    g = cairo.RadialGradient(mx, my + 120, 0, mx, my + 120, 620)
    g.add_color_stop_rgba(0, 0, 0, 0, 0.5)
    g.add_color_stop_rgba(0.5, 0, 0, 0, 0.2)
    g.add_color_stop_rgba(1, 0, 0, 0, 0.0)
    c.rectangle(-300, -300, W + 600, H + 600)
    c.set_source(g)
    c.fill()
    c.pop_group_to_source()
    c.paint()
    c.restore()
    p0, p1 = ap(-AW2, 0, AD_M), ap(AW2, 0, AD_M)
    q0, q1 = ap(-AW2 * 1.4, 0, 1900), ap(AW2 * 1.4, 0, 1900)
    g = cairo.LinearGradient(0, p0[1], 0, q0[1])
    g.add_color_stop_rgba(0, 1.0, 0.7, 0.42, 0.26)
    g.add_color_stop_rgba(1, 1.0, 0.7, 0.42, 0.0)
    c.move_to(*p0)
    c.line_to(*p1)
    c.line_to(*q1)
    c.line_to(*q0)
    c.close_path()
    c.set_source(g)
    c.fill()


# =========================================================================== lighting
def soft_layer(rect_, fn, res=(150, 270)):
    """Render fn(c) (in world coords over rect_) into a small low-res surface and return a
    bilinear pattern for the current user space: soft light is smooth, so this costs a
    fraction of full-res gradient fills."""
    x0, y0, w, h = rect_
    mw, mh = res
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, mw, mh)
    c = cairo.Context(surf)
    c.scale(mw / w, mh / h)
    c.translate(-x0, -y0)
    fn(c)
    surf.flush()
    pat = cairo.SurfacePattern(surf)
    pat.set_matrix(cairo.Matrix(mw / w, 0, 0, mh / h, -x0 * mw / w, -y0 * mh / h))
    pat.set_filter(cairo.FILTER_BILINEAR)
    pat.set_extend(cairo.EXTEND_PAD)
    return pat


def light_chars(ctx, rect_, base, holes, tints=(), beam=None):
    """Light what is already in the current group (the characters), ATOP: a darkness wash
    of strength `base` with soft holes [(x, y, r, strength)] where light falls, coloured
    tints [(x, y, r, colour, alpha)] and the warm torch cone (lens, ang, L, spread, amt).
    All of it is one low-res light map painted once."""
    x0, y0, w, h = rect_

    def fn(c):
        c.rectangle(x0, y0, w, h)
        core.fill(c, core.alpha(DARKC, base))
        c.set_operator(cairo.OPERATOR_DEST_OUT)
        for (hx, hy, r, a) in holes:
            if a <= 0.005:
                continue
            g = cairo.RadialGradient(hx, hy, 0, hx, hy, r)
            g.add_color_stop_rgba(0, 0, 0, 0, a)
            g.add_color_stop_rgba(0.55, 0, 0, 0, a * 0.55)
            g.add_color_stop_rgba(1, 0, 0, 0, 0)
            c.set_source(g)
            core.circle(c, hx, hy, r)
            c.fill()
        c.set_operator(cairo.OPERATOR_OVER)
        for (hx, hy, r, col, a) in tints:
            if a <= 0.005:
                continue
            c_ = core.hexc(col)
            g = cairo.RadialGradient(hx, hy, 0, hx, hy, r)
            g.add_color_stop_rgba(0, c_[0], c_[1], c_[2], a)
            g.add_color_stop_rgba(1, c_[0], c_[1], c_[2], 0)
            c.set_source(g)
            core.circle(c, hx, hy, r)
            c.fill()
        if beam is not None and beam[4] > 0.01:
            (x, y), ang, L, spread, amt = beam
            col = core.hexc(WARM)
            for sp, a in ((1.0, 0.07), (0.72, 0.07), (0.45, 0.08)):
                g = cairo.RadialGradient(x, y, 0, x, y, L)
                g.add_color_stop_rgba(0.0, col[0], col[1], col[2], a * amt * 1.3)
                g.add_color_stop_rgba(0.55, col[0], col[1], col[2], a * amt)
                g.add_color_stop_rgba(1.0, col[0], col[1], col[2], 0.0)
                _cone_path(c, x, y, ang, L, spread * sp)
                c.set_source(g)
                c.fill()
    pat = soft_layer(rect_, fn)
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_ATOP)
    ctx.set_source(pat)
    ctx.paint()
    ctx.restore()


def _cone_path(c, x, y, ang, L, spread):
    a0, a1 = ang - spread / 2, ang + spread / 2
    c.move_to(x, y)
    c.line_to(x + L * math.cos(a0), y + L * math.sin(a0))
    c.arc(x, y, L, a0, a1)
    c.close_path()


def beam_on_chars(c, lens, ang, L, spread, amt):
    """Warm torchlight ATOP on the characters inside the cone (three nested soft cones)."""
    if amt <= 0.01:
        return
    x, y = lens
    col = core.hexc(WARM)
    c.save()
    c.set_operator(cairo.OPERATOR_ATOP)
    for sp, a in ((1.0, 0.07), (0.72, 0.07), (0.45, 0.08)):
        g = cairo.RadialGradient(x, y, 0, x, y, L)
        g.add_color_stop_rgba(0.0, col[0], col[1], col[2], a * amt * 1.3)
        g.add_color_stop_rgba(0.55, col[0], col[1], col[2], a * amt)
        g.add_color_stop_rgba(1.0, col[0], col[1], col[2], 0.0)
        _cone_path(c, x, y, ang, L, spread * sp)
        c.set_source(g)
        c.fill()
    c.restore()


# =========================================================================== the recorder (custom)
def rec_counter(t):
    s_ = int(2832 + t)
    return "00:%02d:%02d" % (s_ // 60 % 60, s_ % 60)


def draw_recorder(c, x, y, s, t, rot=0.0, rec=True, led=1.0, level=0.0, button=0.0, frozen=None,
                  detail=True):
    """HushCorp voice recorder (~240 x 150 at s=1, centre anchor): mic grille, a small LCD
    ("REC" + running counter + level meter, or "PAUSED"), three face buttons (rec / pause /
    stop), the logo + HUSHCORP wordmark, a red LED top-left."""
    with core.saved(c, x, y, s, rot):
        rect(c, -120, -75, 240, 150, "#26242f", 6, r=26)
        rect(c, -110, -66, 220, 132, "#302d3b", 0, r=20)
        line(c, [(-104, -60), (104, -60)], "#46425a", 3)
        # mic grille
        core.circle(c, -70, -14, 36)
        fs(c, "#1c1a24", 4)
        if detail:
            for i_ in range(-2, 3):
                for j in range(-2, 3):
                    if i_ * i_ + j * j <= 5:
                        core.circle(c, -70 + i_ * 11.5, -14 + j * 11.5, 3.6)
            core.fill(c, "#57536a")
        # LCD screen
        lcd = "#1b2a26" if rec else "#18201e"
        rect(c, -22, -56, 128, 70, lcd, 4, r=8)
        if detail:
            if rec:
                on = (t % 1.0) < 0.6
                core.circle(c, -6, -38, 7)
                core.fill(c, "#ff3b5c" if on else "#5a2430")
                core.text(c, "REC", 24, -30, 21, "#ff6f86" if on else "#8a3a48", "ui")
                core.text(c, rec_counter(t), 42, -9, 16, "#8ff5d0", "mono")
                # level meter: 10 bars along the bottom of the screen
                for i_ in range(10):
                    v_ = level * (1.0 - 0.06 * i_) + 0.22 * core.noise1(t * 8 + i_ * 1.7, 5) * (0.3 + level)
                    hgt = 3 + 15 * clamp(v_)
                    rect(c, -14 + i_ * 12, 10 - hgt, 9, hgt, "#5fe8b0" if hgt > 5 else "#3b5e52", 0, r=1.5)
                core.radial_glow(c, 42, -22, 100, "#8ff5d0", 0.10)
            else:
                rect(c, -10, -46, 7, 22, "#8ff5d0", 0, r=1)
                rect(c, 2, -46, 7, 22, "#8ff5d0", 0, r=1)
                core.text(c, "PAUSED", 58, -27, 19, "#8ff5d0", "ui")
                core.text(c, frozen or rec_counter(t), 42, -5, 14, "#5f9c86", "mono")
                for i_ in range(10):
                    rect(c, -14 + i_ * 12, 7, 9, 3, "#2e4a40", 0, r=1)
        # face buttons: rec / pause / stop
        for bx, kind in ((22, "rec"), (58, "pause"), (94, "stop")):
            dy = 3.0 * button if kind == "pause" else 0.0
            core.circle(c, bx, 44 + dy, 13)
            fs(c, "#3d394c" if kind != "rec" else "#4a2a36", 3.5)
            if kind == "rec":
                core.circle(c, bx, 44, 5)
                core.fill(c, "#ff4f6d")
            elif kind == "pause":
                rect(c, bx - 6, 38 + dy, 4, 12, "#c9c6d4", 0)
                rect(c, bx + 2, 38 + dy, 4, 12, "#c9c6d4", 0)
            else:
                rect(c, bx - 5, 39, 10, 10, "#c9c6d4", 0, r=1.5)
        # logo + wordmark
        props.hush_logo(c, -98, 46, 11, lw=0, ring=False, hole="#26242f")
        if detail:
            props.spaced_text(c, "HUSHCORP", -44, 51, 10.5, "#2fd1c5", "ui", 0.3)
        # LED
        if led > 0.05:
            core.radial_glow(c, -100, -54, 30, core.PAL["danger"], 0.6 * led)
        core.circle(c, -100, -54, 5.5)
        core.fill(c, core.mixc("#4a1620", "#ff3b5c", led))
        if led > 0.5:
            core.circle(c, -102, -56, 1.8)
            core.fill(c, "#ffd0d8")


# =========================================================================== timing
def K(info):
    c = info.cue
    L = info.line
    w = info.word_time
    k = dict(dur=info.dur)
    for n in ("steps", "notice", "blink", "led", "conflict", "click", "wink", "smile", "card", "nod"):
        k[n] = c(n)
    for tag, lid in (("l1", "s05_l01"), ("l2", "s05_l02"), ("l3", "s05_l03"), ("l4", "s05_l04"),
                     ("l5", "s05_l05"), ("l5b", "s05_l05b"), ("l5c", "s05_l05c"), ("l6", "s05_l06"),
                     ("l7", "s05_l07"), ("l8", "s05_l08")):
        ln = L(lid)
        k[tag], k[tag + "e"] = ln.start, ln.end
    k["l1_what"] = w("s05_l01", 1)
    k["l1_down"] = w("s05_l01", 5)
    k["l2_oh"] = w("s05_l02", 0)
    k["l2_hey"] = w("s05_l02", 1)
    k["l3_thing"] = w("s05_l03", 2)
    k["l4_eyes"] = w("s05_l04", 4)
    k["l4_glow"] = w("s05_l04", 5)
    k["l5_yeah"] = w("s05_l05", 1)
    k["l5_critter"] = w("s05_l05", 3)
    k["l5_I"] = w("s05_l05", 6)
    k["l5_fell"] = w("s05_l05", 7)
    k["l5_build"] = w("s05_l05", 11)
    k["l5_and"] = w("s05_l05", 12)
    k["l5_see"] = w("s05_l05", 16)
    k["l5_dark"] = w("s05_l05", 19)
    k["l5b_fell"] = w("s05_l05b", 1)
    k["l5b_what"] = w("s05_l05b", 5)
    k["l5c_day"] = w("s05_l05c", 3)
    k["l6_huh"] = w("s05_l06", 0)
    k["l6_pocket"] = w("s05_l06", 2)
    k["l6_calc"] = w("s05_l06", 3)
    k["l6_just"] = w("s05_l06", 4)
    k["l6_stop"] = w("s05_l06", 5)
    k["l7_nine"] = w("s05_l07", 6)
    k["l7_take"] = w("s05_l07", 7)
    k["l7_card"] = w("s05_l07", 9)
    k["l8_be"] = w("s05_l08", 2)
    st = k["steps"]
    # ---- A: the walk-in and the "fine" glance
    k["a_stop"] = st - 1.15
    k["a_look"] = k["a_stop"] + 0.12
    k["a_fine"] = k["a_stop"] + 0.5
    k["a_away"] = st - 0.22
    k["c_hear"] = 0.35
    k["c_turn"] = 0.62
    k["c_hope"] = 0.95
    # ---- B: Embarrassment walks up the tunnel out of the dark
    k["e0"] = st + 0.15
    k["e1"] = st + 1.45
    k["e_turn"] = k["e1"] - 0.05
    k["swing0"], k["swing1"] = k["e1"] + 0.1, k["e1"] + 0.38
    k["jolt"] = k["swing1"] + 0.05
    k["c_up"] = st + 0.42
    k["c_mv0"], k["c_mv1"] = st + 0.54, st + 1.0
    k["c_sit"] = st + 1.0
    k["c_found"] = k["notice"] + 0.72
    # ---- l05 escalation / l05b freak-out / blink recovery
    k["fr_up0"] = k["l5_see"] - 0.35          # anticipation dip, then hands fly to his head
    k["fr_up1"] = k["fr_up0"] + 0.3
    k["fr_dn0"] = k["blink"] + 0.42            # hands come down (eyes shut), to the glasses
    k["fr_glass"] = k["fr_dn0"] + 0.4          # pushes them straight
    k["fr_dn1"] = k["fr_glass"] + 0.35
    # ---- the recorder
    cf = k["conflict"]
    k["r_reach"] = cf + 0.1
    k["r_grab"] = cf + 0.45
    k["r_up"] = cf + 0.85
    k["r_look_t"] = cf + 2.42                  # eyes to Tiredness
    k["r_look_b"] = cf + 2.88                  # back to the recorder
    k["r_breath"] = cf + 2.95
    k["press"] = k["click"] + 0.22
    k["led_off"] = k["press"] + 0.05
    k["r_pocket"] = k["smile"] + 0.25
    k["r_gone"] = k["r_pocket"] + 0.38
    k["wk0"] = k["wink"] + 0.08                # the wink
    # ---- keycard
    k["k_reach"] = k["l7_take"] - 0.6
    k["k_have"] = k["k_reach"] + 0.35
    k["k_out"] = k["k_have"] + 0.5
    k["k_take0"] = k["k_out"] + 0.18
    k["k_take"] = k["k_take0"] + 0.36
    k["k_back"] = k["k_take"] + 0.12
    # ---- Curiosity comes out after the click
    k["c_out0"] = k["wink"] - 0.1
    k["c_out1"] = k["c_out0"] + 1.0
    # ---- the end
    k["nod0"] = k["nod"] + 0.22
    k["go_turn"] = k["nod"] + 1.0
    k["go_walk"] = k["go_turn"] + 0.32
    # ---- shots
    k["B2"] = st + 0.05
    k["E3"] = k["l1_what"] - 0.07
    k["T4"] = k["l1e"] + 0.4
    k["W5"] = k["l2e"] + 0.35
    k["E6"] = k["l3e"] + 0.1
    k["T7"] = k["l4_glow"] - 0.05
    k["W8"] = k["l5_I"] - 0.1
    k["E9"] = k["l5e"] + 0.25
    k["T10"] = k["l5be"] + 0.3
    k["E11"] = k["l5ce"] + 0.3
    k["W12"] = k["led"]
    k["R14"] = cf + 0.95
    k["E15"] = cf + 2.3
    k["R16"] = k["click"] - 0.1
    k["E17"] = k["l6_huh"] + 0.12
    k["T18"] = k["wink"] + 0.62
    k["W19"] = k["l7"] - 0.25
    k["K20"] = k["l7e"] - 0.05
    k["E21"] = k["l8"] - 0.05
    k["W22"] = k["l8e"] + 0.35
    return k


_KC = {}


def keys_for(info):
    sig = (info.id, round(info.dur, 4), round(info.cue("steps"), 4))
    if sig not in _KC:
        _KC.clear()
        _KC[sig] = K(info)
    return _KC[sig]


# =========================================================================== shots / cameras
def shots(k):
    return [
        ("A1", 0.0, "A", lambda t: tw(t, [(0.0, (540, 960, 1.0)), (k["a_stop"] + 0.3, (566, 990, 1.14)),
                                          (k["B2"], (578, 1006, 1.2))])),
        ("B2", k["B2"], "B", lambda t: tw(t, [(k["B2"], (505, 1090, 1.22)), (k["E3"], (515, 1092, 1.27))])),
        ("E3", k["E3"], "B", lambda t: (470, 950, 2.3)),
        ("T4", k["T4"], "B", lambda t: (735, 1010, 2.3)),
        ("W5", k["W5"], "B", lambda t: (565, 1135, 1.46)),
        ("E6", k["E6"], "B", lambda t: (450, 905, 2.6)),
        ("T7", k["T7"], "B", lambda t: (712, 985, 2.5)),
        ("W8", k["W8"], "B", lambda t: tw(t, [(k["W8"], (560, 1112, 1.55)), (k["E9"], (548, 1104, 1.6))])),
        ("E9", k["E9"], "B", lambda t: tw(t, [(k["E9"], (436, 860, 2.35)), (k["l5b_what"] - 0.05, (436, 860, 2.35)),
                                              (k["l5b_what"] + 0.12, (430, 852, 2.5), ease_out)])),
        ("T10", k["T10"], "B", lambda t: (712, 975, 2.7)),
        ("E11", k["E11"], "B", lambda t: (448, 880, 2.6)),
        ("W12", k["W12"], "B", lambda t: (562, 1108, 1.7)),
        ("R14", k["R14"], "R", None),
        ("E15", k["E15"], "B", lambda t: tw(t, [(k["E15"], (410, 900, 2.7)), (k["R16"], (405, 895, 2.85))])),
        ("R16", k["R16"], "R", None),
        ("E17", k["E17"], "B", lambda t: tw(t, [(k["E17"], (420, 905, 2.55)), (k["wk0"] - 0.2, (395, 865, 2.9))])),
        ("T18", k["T18"], "B", lambda t: (712, 1095, 2.3)),
        ("W19", k["W19"], "B", lambda t: (570, 1230, 1.6)),
        ("K20", k["K20"], "K", None),
        ("E21", k["E21"], "B", lambda t: (450, 905, 2.6)),
        ("W22", k["W22"], "B", lambda t: tw(t, [(k["W22"], (580, 1170, 1.5)), (k["dur"], (600, 1166, 1.56))])),
    ]


_SH = {}


def shot_list(k):
    key = round(k["dur"], 4)
    if key not in _SH:
        _SH.clear()
        _SH[key] = shots(k)
    return _SH[key]


def shot_at(t, k):
    sh = shot_list(k)
    cur = sh[0]
    for s_ in sh:
        if t >= s_[1]:
            cur = s_
    return cur


def view_rect(cam, pad=60):
    cx, cy, z = cam
    return (cx - 540 / z - pad, cy - 960 / z - pad, 1080 / z + 2 * pad, 1920 / z + 2 * pad)


_SR = {}


def shot_rect(k, name):
    """World rect covering a shot's whole framing (camera start .. end)."""
    key = (round(k["dur"], 4), name)
    if key not in _SR:
        sh = shot_list(k)
        i = [s_[0] for s_ in sh].index(name)
        t0 = sh[i][1]
        t1 = sh[i + 1][1] - 0.01 if i + 1 < len(sh) else k["dur"]
        rs = [view_rect(sh[i][3](tt), pad=40) for tt in (t0, (t0 + t1) / 2, t1)]
        x0 = min(r[0] for r in rs)
        y0 = min(r[1] for r in rs)
        x1 = max(r[0] + r[2] for r in rs)
        y1 = max(r[1] + r[3] for r in rs)
        _SR[key] = (x0, y0, x1 - x0, y1 - y0)
    return _SR[key]


# =========================================================================== Tiredness (B)
POCKET_T = "hands_pockets"


def shrug_pose(a):
    """A lazy, nonchalant shrug with his hands staying in the hoodie pocket: shoulders up,
    elbows out a little, head tilt (a = 0..1)."""
    return {"base": "hands_pockets", "hunch": 0.6 + 0.8 * a, "neck": -0.5 * a, "tilt": 0.12 * a,
            "lift": 8 * a}


# a lazy hello: the near hand comes out of the hoodie pocket for one small bent-elbow wave,
# the other hand stays in the pocket (wave_small's arm on top of hands_pockets)
WAVE_T = {"base": "hands_pockets", "period": 0.7, "ar_p": 0.35, "ar_o": 1.2, "ar_e": 2.3,
          "ar_eo": human.W(-1.1, 0.12, 0.0), "ar_w": human.W(0.0, 0.16, 0.1), "ar_h": "open",
          "ar_tf": -1.0, "ar_hide": 0.0, "hunch": 0.3}
WAVE_MID = {"base": "hands_pockets", "ar_p": 0.25, "ar_o": 1.35, "ar_e": 1.25, "ar_eo": -0.6,
            "ar_h": "open", "ar_tf": -1.0, "ar_hide": 0.0, "hunch": 0.3}


# taking the keycard: only the near hand comes out of the pocket (the other stays in: chill)
CARD_T = {"base": "hands_pockets", "ar_hide": 0.0, "ar_h": "relaxed"}
# walking off with the far hand still in the pocket
WALK_T = {"base": "walk", "al_p": 0.32, "al_o": 0.2, "al_e": 0.95, "al_eo": -1.05, "al_w": 0.0,
          "al_hide": 1.0, "ar_p": 0.32, "ar_o": 0.2, "ar_e": 0.95, "ar_eo": -1.05, "ar_w": 0.0,
          "ar_hide": 1.0}


def shrug_amt(t, k):
    """0..1 lazy shrugs: on "Oh, yeah.", on "...in the dark." and on "It's been a day."."""
    a = 0.0
    for t0, amp in ((k["l5"] - 0.08, 1.0), (k["l5_dark"] - 0.1, 0.65), (k["l5c_day"] - 0.12, 1.0)):
        a = max(a, amp * tw(t, [(t0, 0.0), (t0 + 0.38, 1.0), (t0 + 0.72, 1.0), (t0 + 1.25, 0.0)]))
    return a


def tired_state(t, k):
    st = k["steps"]
    d = dict(x=XT, y=FY, turn=-0.7, pose=POCKET_T, pose_t=None, expr="bored", look=(0, 0),
             blink=None, face={}, reach=None, drift=True, card=False, squint=0.0)
    # ---- body poses
    hey = k["l2_hey"]
    keys = [(-1, POCKET_T), (hey - 0.32, WAVE_MID), (hey - 0.14, WAVE_T), (hey + 0.56, WAVE_MID),
            (hey + 0.74, POCKET_T)]
    keys += [(k["k_take0"] - 0.12, CARD_T), (k["go_turn"], POCKET_T)]
    keys += [(k["go_walk"], WALK_T)]
    pose = state_at(t, keys, 0.3)
    if pose[1] in (WAVE_T, WAVE_MID) or pose[0] in (WAVE_T, WAVE_MID):
        pose = state_at(t, keys, 0.18)
        d["pose_t"] = max(0.0, t - (hey - 0.14))
    elif pose[1] is WALK_T and t >= k["go_walk"]:
        d["pose_t"] = t - k["go_walk"]
    sa = shrug_amt(t, k)
    if sa > 0.001 and pose[1] == POCKET_T and pose[2] >= 1.0:
        pose = shrug_pose(sa)
    d["pose"] = pose
    # ---- leaving at the end: turn toward CONTROL (the mouth, screen-right), set off
    if t >= k["go_turn"]:
        d["turn"] = tw(t, [(k["go_turn"], -0.7), (k["go_walk"], 0.85)])
        if t >= k["go_walk"]:
            vr = abs(human.cycle_speed("tired", "walk", 0.85, "sewer")) * S
            d["x"] = XT + vr * smoothstep(seg(t, k["go_walk"], k["go_walk"] + 0.3)) * (t - k["go_walk"])
    # ---- the keycard: reach, take, hold it up to read it
    kt0, kt = k["k_take0"], k["k_take"]
    if kt0 - 0.1 <= t:
        ch = emb_card_hand(kt0 + 0.02, k)
        hold_pt = (XT - 85, 1095)
        if t < kt:
            w = smoothstep(seg(t, kt0, kt))
            d["reach"] = {"r": (ch[0] + 22, ch[1] - 2, w)}
        elif t < k["go_turn"]:
            p = tw(t, [(kt, (ch[0] + 22, ch[1] - 2)), (kt + 0.45, hold_pt)])
            d["reach"] = {"r": (p[0], p[1], 1.0)}
        else:               # slips the card into his hoodie pocket as he turns to go
            w = 1 - smoothstep(seg(t, k["go_turn"] - 0.1, k["go_turn"] + 0.2))
            d["reach"] = {"r": (hold_pt[0], hold_pt[1], w)}
        d["card"] = kt <= t < k["go_turn"] + 0.12
    # ---- expression: bored / deadpan all the way (super chill); the faintest smile
    d["expr"] = state_at(t, [(0, "bored"), (k["l2"] - 0.2, "deadpan"), (k["E6"], "bored"),
                             (k["T18"] - 0.05, "soft_smile"), (k["W19"], "bored")], 0.3)
    f = {}
    # B start: still on Curiosity, then the footsteps: to the tunnel (left)
    look = tw(t, [(st, (-0.55, 0.8)), (st + 0.18, (-0.55, 0.8)), (st + 0.32, (-1.0, 0.0)),
                  (st + 0.75, (-0.95, 0.05)), (st + 0.9, (-0.3, 0.9)),            # glance down: it hides
                  (st + 1.15, (-0.35, 0.9)), (st + 1.3, (-0.95, 0.0)),
                  (k["jolt"] - 0.1, (-0.95, -0.05)), (k["jolt"] + 0.1, (-0.8, 0.2))])
    f.update(fk(t, {
        "head_turn": [(st + 0.4, -0.05), (st + 0.6, -0.15)],
        "head_nod": [(st, 0.1), (st + 0.4, 0.0)],
        "lid": [(st + 0.2, 0.0), (st + 0.35, -0.06), (st + 1.0, -0.03)],
    }))
    # the beam in his face: squint, flinch, head away (until the beam drifts down)
    b_on = smoothstep(seg(t, k["swing1"] - 0.08, k["swing1"] + 0.1)) * \
        (1 - smoothstep(seg(t, k["notice"] + 0.25, k["notice"] + 0.65)))
    d["squint"] = b_on
    if b_on > 0:
        f["lower"] = f.get("lower", 0) + 0.24 * b_on
        f["lid"] = f.get("lid", 0) + 0.03 * b_on
        f["brow"] = f.get("brow", 0) - 0.18 * b_on
        f["head_turn"] = f.get("head_turn", 0) + 0.12 * b_on
        f["head_nod"] = f.get("head_nod", 0) + 0.04 * b_on
    if t >= k["jolt"]:
        look = (-0.75, 0.15)
    # l02 "Oh. Hey.": flat; a chin lift on "Hey.", lip press after
    if t >= k["l2"] - 0.3:
        look = tw(t, [(k["l2"] - 0.3, (-0.75, 0.15)), (k["l2e"] + 0.2, (-0.8, 0.1))])
        f = addf(f, fk(t, {
            "head_nod": [(hey - 0.05, 0.0), (hey + 0.12, -0.1), (hey + 0.5, 0.0)],
            "lid": [(k["l2"], 0.0), (k["l2"] + 0.3, 0.05)],
            "press": [(k["l2e"], 0.0), (k["l2e"] + 0.25, 0.3), (k["W5"] + 0.4, 0.12)],
        }))
    # notice: follows the beam down to it, back up at Emb: "uh-oh"
    nt = k["notice"]
    if t >= nt:
        th = k["l3_thing"]
        look = tw(t, [(nt, (-0.8, 0.1)), (nt + 0.35, (-0.75, 0.3)), (nt + 0.75, (-0.15, 1.0)),
                      (nt + 1.25, (-0.15, 1.0)), (nt + 1.45, (-0.85, 0.05)),
                      (th, (-0.85, 0.05)), (th + 0.15, (-0.15, 0.95)),
                      (th + 0.55, (-0.15, 0.95)), (th + 0.7, (-0.85, 0.05))])
        f = addf(f, fk(t, {
            "head_nod": [(nt + 0.45, 0.0), (nt + 0.8, 0.12), (nt + 1.3, 0.12), (nt + 1.6, 0.0)],
            "brow_r": [(nt + 1.3, 0.0), (nt + 1.6, 0.14), (k["l4"], 0.05)],
        }))
    # l04 / l05: unbothered, steady on Emb; lazy shrug; "critter" -> a glance down at it
    if t >= k["l4"] - 0.2:
        cr = k["l5_critter"]
        look = tw(t, [(k["l4"] - 0.2, (-0.85, 0.05)), (cr - 0.12, (-0.85, 0.05)), (cr + 0.04, (-0.25, 0.9)),
                      (cr + 0.42, (-0.25, 0.9)), (cr + 0.58, (-0.85, 0.05)),
                      (k["l5e"] + 0.2, (-0.85, 0.05))])
        f = addf(f, fk(t, {
            "lid": [(k["l4e"], 0.0), (k["l4e"] + 0.35, -0.05)],
            "head_nod": [(cr - 0.05, 0.0), (cr + 0.15, 0.06), (cr + 0.5, 0.06), (cr + 0.7, 0.0)],
        }))
        sa_ = shrug_amt(t, k)
        f = addf(f, {"brow": 0.18 * sa_, "frown": 0.22 * sa_, "head_tilt": 0.05 * sa_})
    # l05b / l05c: watches Emb freak out, unmoved; a slow blink after "a day."
    if t >= k["l5e"] + 0.2:
        look = tw(t, [(k["l5e"] + 0.2, (-0.85, 0.05)), (k["l5b"] + 0.1, (-0.85, -0.05)),
                      (k["l5ce"] + 0.2, (-0.85, -0.02)), (k["blink"], (-0.85, 0.05))])
        b0 = k["l5ce"] + 0.08
        if b0 <= t < b0 + 1.0:
            d["blink"] = tw(t, [(b0, 0.0), (b0 + 0.3, 1.0), (b0 + 0.55, 1.0), (b0 + 0.95, 0.0)])
        f = addf(f, fk(t, {"lid": [(k["l5c"] - 0.3, 0.0), (k["l5c"], 0.03), (k["led"], 0.07)]}))
    # led: eyes slide down to the pocket (after Emb's)
    led = k["led"]
    if t >= led:
        look = tw(t, [(led, (-0.85, 0.05)), (led + 0.62, (-0.85, 0.05)), (led + 0.8, (-1.0, 0.45))])
        f = addf(f, fk(t, {"head_turn": [(led + 0.75, 0.0), (led + 0.95, -0.1)],
                            "head_nod": [(led + 0.75, 0.0), (led + 0.95, 0.07)]}))
    # conflict / click / l06: watching (the recorder, his face); a brow on "calculator": he gets it
    if t >= k["conflict"]:
        look = tw(t, [(k["conflict"], (-1.0, 0.45)), (k["press"] + 0.4, (-1.0, 0.42)),
                      (k["press"] + 0.65, (-0.9, 0.05))])
        f = addf(f, fk(t, {
            "head_turn": [(k["press"] + 0.5, 0.0), (k["press"] + 0.75, 0.1)],
            "head_nod": [(k["press"] + 0.5, 0.0), (k["press"] + 0.75, -0.07)],
            "brow_r": [(k["l6_calc"], 0.0), (k["l6_calc"] + 0.25, 0.28), (k["T18"], 0.1)],
            "brow_l": [(k["l6_calc"], 0.0), (k["l6_calc"] + 0.25, 0.06), (k["T18"], 0.0)],
            "lid": [(k["l6_calc"], 0.0), (k["l6_calc"] + 0.25, -0.05), (k["T18"], 0.03)],
        }))
    # T18: the faintest smile back (soft_smile expr + small deltas), then a glance down at it
    s18 = k["T18"]
    if t >= s18 - 0.6:
        f = addf(f, fk(t, {
            "curve": [(s18 - 0.6, -0.15), (s18 + 0.05, -0.15), (s18 + 0.5, 0.12)],
            "smirk": [(s18 + 0.05, 0.0), (s18 + 0.45, -0.4), (k["W19"], -0.3), (k["W19"] + 0.4, 0.0)],
            "lower": [(s18 + 0.1, 0.0), (s18 + 0.5, 0.12), (k["W19"], 0.08), (k["W19"] + 0.4, 0.0)],
            "lid": [(s18, 0.0), (s18 + 0.5, 0.04)],
        }))
        if t < k["W19"]:
            look = tw(t, [(s18 - 0.6, (-0.9, 0.05)), (s18 + 0.8, (-0.9, 0.05)),
                          (s18 + 0.95, (-0.45, 0.75)), (k["W19"], (-0.45, 0.75))])
            f = addf(f, fk(t, {"head_nod": [(s18 + 0.85, 0.0), (s18 + 1.05, 0.06)]}))
    # l07: on Emb, then on the card he takes; reads it
    if t >= k["W19"]:
        look = tw(t, [(k["W19"], (-0.9, 0.05)), (k["k_out"], (-0.9, 0.1)), (k["k_out"] + 0.2, (-0.9, 0.5)),
                      (k["k_take"] + 0.1, (-0.85, 0.55)), (k["k_take"] + 0.35, (-0.6, 0.85)),
                      (k["l8"] - 0.1, (-0.6, 0.85)), (k["l8"] + 0.1, (-0.9, 0.05))])
        f = addf(f, fk(t, {
            "head_nod": [(k["k_take"], 0.0), (k["k_take"] + 0.35, 0.12), (k["l8"] - 0.1, 0.12),
                         (k["l8"] + 0.15, 0.0)],
            "lid": [(k["l8_be"], 0.0), (k["l8_be"] + 0.3, -0.05), (k["nod"], -0.03)],
        }))
    # nod, then off toward CONTROL
    n0 = k["nod0"]
    if t >= k["nod"] - 0.2:
        look = tw(t, [(k["nod"] - 0.2, (-0.9, 0.05)), (k["go_turn"] - 0.05, (-0.9, 0.1)),
                      (k["go_turn"] + 0.15, (0.6, 0.0))])
        f = addf(f, fk(t, {
            "head_nod": [(n0, 0.0), (n0 + 0.24, 0.24), (n0 + 0.66, 0.02)],
            "curve": [(n0 + 0.3, 0.0), (n0 + 0.6, 0.1)],
        }))
    d["look"] = look
    d["face"] = f
    return d


# =========================================================================== Embarrassment (B)
_E = {"ar_h": "grip", "ar_layer": "mid", "ar_hide": 1.0, "al_layer": "front"}


def _ep(**kw):
    d = dict(_E)
    d["base"] = "stand"
    d["al_h"] = "relaxed"
    d.update(kw)
    return d


EMB_BASE = _ep()
EMB_WALK = dict(_E, base="walk")
EMB_JOLT = _ep(al_h="open", hunch=0.75, lean=-0.12, lift=14)
EMB_NERV = _ep(hunch=0.25)
EMB_WIDE = _ep(al_h="open", hunch=0.35, lean=-0.07)
EMB_HEAD = _ep(al_h="splay", hunch=0.9, lean=-0.04)
EMB_PINCH = _ep(al_h="pinch")
EMB_CUP = _ep(al_h="cup", al_tf=-1)
EMB_CUPB = _ep(al_h="cup", al_tf=-1, hunch=0.22)
EMB_POINT = _ep(al_h="point")

_PROBE = [None]
_PC = {}


def emb_probe(name, pose, turn):
    """Anchors of Emb at his spot for a pose (cached): hand targets for 'hands on his head'."""
    key = (name, round(turn, 3))
    if key not in _PC:
        if _PROBE[0] is None:
            _PROBE[0] = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 2, 2))
        _PC[key] = human.draw_person(_PROBE[0], "embar", XE, FY, S, 0.0, pose=pose, turn=turn, drift=False,
                                     blink=0.0)
    return _PC[key]


def emb_card_hand(t, k):
    """World point of his left (near) palm while handing over the card."""
    return tw(t, [(k["k_have"], (300, 1000)), (k["k_out"], (583, 1068))])


def mouth_amt(info, t):
    m = 0.0
    for who in ("tired", "embar"):
        m = max(m, info.mouth(who, t)[0])
    return m


def embar_state(t, k):
    st = k["steps"]
    d = dict(x=XE, y=FY, s=S, turn=0.7, pose=EMB_BASE, pose_t=None, expr="neutral", look=(0.9, 0.0),
             blink=None, blush=0.1, face={}, reach={}, drift=True, glasses_dy=0.0, glasses_tilt=0.0,
             visible=True, aim=None, rec=None, card=None, led=None, led_glow=0.55, sweat=0.0, aim_ang=0.0)
    v = abs(human.cycle_speed("embar", "walk", 0.75)) * S
    # ---- walking up the tunnel out of the dark (screen-left), torch forward-down
    if t < k["e1"]:
        x = XE - v * (k["e1"] - max(t, k["e0"]))
        d.update(x=x, turn=0.75, pose=EMB_WALK, pose_t=max(0.0, t - k["e0"]))
        d["look"] = tw(t, [(k["e0"], (0.7, 0.4)), (k["e0"] + 0.8, (0.8, 0.35)), (k["e1"], (0.7, 0.2))])
        d["face"] = {"brow_ang": 0.25, "press": 0.2}
        bob = 6 * math.sin((t - k["e0"]) * 2 * math.pi)
        gx, gy = x + 98, 1135 + bob
        aim = (x + 420, 1480 + 20 * math.sin((t - k["e0"]) * 3.1))
        ang = math.atan2(aim[1] - gy, aim[0] - gx)
        d["reach"] = {"r": (gx, gy, 1.0, ang)}
        d["aim"] = aim
        d["aim_ang"] = ang
        d["visible"] = t >= k["e0"] - 0.6
        return d
    # ---- body poses
    jt = k["jolt"]
    pose_keys = [(-1, EMB_WALK), (k["e1"], EMB_BASE), (jt, EMB_JOLT), (jt + 0.16, EMB_NERV),
                 (k["l1e"] + 0.3, EMB_BASE),
                 (k["l5_fell"], EMB_WIDE), (k["fr_up0"], EMB_HEAD), (k["fr_dn0"], EMB_NERV),
                 (k["fr_dn1"], EMB_BASE)]
    cf = k["conflict"]
    pose_keys += [(k["r_reach"], EMB_PINCH), (k["r_grab"] + 0.15, EMB_CUP),
                  (k["r_breath"], EMB_CUPB), (k["r_breath"] + 0.55, EMB_CUP),
                  (k["r_pocket"], EMB_PINCH), (k["r_gone"] + 0.1, EMB_BASE),
                  (k["k_reach"], EMB_PINCH), (k["k_have"] + 0.1, EMB_CUP), (k["k_back"], EMB_BASE)]
    p = state_at(t, pose_keys, 0.22)
    if t < jt + 0.3 and (p[1] is EMB_JOLT or p[0] is EMB_JOLT):
        p = (p[0], p[1], smoothstep(seg(t, jt, jt + 0.07)) if p[1] is EMB_JOLT else p[2])
    if p[0] is EMB_WALK:
        d["pose_t"] = 0.0            # walk frozen on a contact while it blends out
    d["pose"] = p
    d["turn"] = tw(t, [(k["e_turn"], 0.75), (k["e_turn"] + 0.3, 0.7), (cf, 0.7), (cf + 0.35, 0.55),
                       (k["press"] + 0.45, 0.55), (k["press"] + 0.75, 0.7)])
    # ---- the flashlight (far hand) and where the beam points
    face_aim = T_FACE
    floor_aim = (610, 1478)
    nt = k["notice"]
    aim = tw(t, [(k["swing0"], (560, 1420)), (k["swing1"], face_aim), (nt + 0.12, face_aim),
                 (k["c_found"], CUR_EYE), (k["l4"] + 0.05, CUR_EYE), (k["l4"] + 0.65, floor_aim),
                 (k["fr_up0"], floor_aim), (k["fr_up1"], (140, 330), ease_out), (k["fr_dn0"], (150, 340)),
                 (k["fr_dn1"], floor_aim),
                 (cf, floor_aim), (cf + 0.35, (520, 1495)), (k["press"] + 0.5, (520, 1495)),
                 (k["press"] + 0.8, (470, 1498))])
    j = t - jt
    if 0 <= j < 0.6:
        aim = (aim[0], aim[1] + 34 * math.sin(j * 30) * (1 - j / 0.6) ** 2)
    head = emb_probe("head", EMB_HEAD, 0.7)
    hx0, hy0 = head["head"]
    hand_r = tw(t, [(k["e1"], (XE + 92, 1165)), (k["swing0"], (XE + 95, 1150)), (k["swing1"], (XE + 112, 1022)),
                    (nt + 0.12, (XE + 112, 1022)), (k["c_found"], (XE + 105, 1070)),
                    (k["l4"] + 0.05, (XE + 105, 1070)), (k["l4"] + 0.65, (XE + 98, 1118)),
                    (k["fr_up0"], (XE + 100, 1125)), (k["fr_up1"], (hx0 + 62, hy0 - 112), ease_out),
                    (k["fr_dn0"], (hx0 + 62, hy0 - 112)), (k["fr_dn1"], (XE + 98, 1118)),
                    (cf, (XE + 98, 1118)), (cf + 0.35, (XE + 90, 1130))])
    gx, gy = hand_r
    # freak-out tremble (hands on his head)
    fr = smoothstep(seg(t, k["fr_up0"], k["fr_up1"])) * (1 - smoothstep(seg(t, k["fr_dn0"], k["fr_dn0"] + 0.3)))
    if fr > 0:
        tr = 2.5 * fr * (1 + 1.2 * bump(t, k["l5b_what"] - 0.1, k["l5b_what"] + 0.6))
        gx += tr * math.sin(t * 37)
        gy += tr * math.sin(t * 29 + 1)
    ang = math.atan2(aim[1] - gy, aim[0] - gx)
    d["aim"] = aim
    d["aim_ang"] = ang
    d["reach"] = {"r": (gx, gy, 1.0, ang)}
    # ---- near hand: jolt to the chest, on his head, glasses, the recorder, the keycard
    pocket = (XE - 15 + 4, FY - 502 + 6)
    wl = tw(t, [(jt, 0.0), (jt + 0.1, 1.0, ease_out), (jt + 0.5, 1.0), (jt + 0.9, 0.0)])
    if wl > 0:
        d["reach"]["l"] = (XE + 30, 1012, wl)
    # hands fly to his head; down to the glasses during the blink; push them straight; down
    eyel = head["eye_l"]
    glass = (eyel[0] - 30, eyel[1] + 14)          # the near side of the frame (not over his face)
    if k["fr_up0"] - 0.05 <= t < k["fr_dn1"] + 0.45:
        hl = (hx0 - 46 + 3 * math.sin(t * 33) * fr, hy0 - 82 + 3 * math.sin(t * 27) * fr)
        p_ = tw(t, [(k["fr_dn0"], hl), (k["fr_glass"], (glass[0], glass[1] + 6)),
                    (k["fr_glass"] + 0.18, (glass[0], glass[1] - 4)),
                    (k["fr_dn1"], (glass[0], glass[1] - 4))])
        w_ = tw(t, [(k["fr_up0"] + 0.02, 0.0), (k["fr_up1"], 1.0, ease_out), (k["fr_dn1"], 1.0),
                    (k["fr_dn1"] + 0.42, 0.0)])
        if t >= k["fr_dn0"] + 0.15:
            d["reach"]["l"] = (p_[0], p_[1], w_, -1.45)
        else:
            d["reach"]["l"] = (p_[0], p_[1], w_)
        if t >= k["fr_dn0"] + 0.2:
            d["pose"] = state_at(t, [(-1, EMB_NERV), (k["fr_dn0"] + 0.2, EMB_POINT), (k["fr_dn1"], EMB_BASE)], 0.2)
    if k["r_reach"] - 0.05 <= t < k["r_gone"] + 0.45:
        palm = tw(t, [(k["r_grab"], pocket), (k["r_up"], (XE + 24, 1002)),
                      (k["press"] + 0.4, (XE + 26, 1000)), (k["l6_pocket"] - 0.1, (XE + 70, 985)),
                      (k["l6_stop"], (XE + 76, 990)), (k["r_pocket"], (XE + 76, 990)),
                      (k["r_gone"], (pocket[0] + 2, pocket[1] - 6))])
        w = tw(t, [(k["r_reach"], 0.0), (k["r_grab"], 1.0), (k["r_gone"], 1.0), (k["r_gone"] + 0.4, 0.0)])
        ha = tw(t, [(k["r_grab"], -1.2), (k["r_up"], -0.25), (k["r_pocket"], -0.25), (k["r_gone"], -1.2)])
        d["reach"]["l"] = (palm[0], palm[1], w, ha)
        if k["r_grab"] <= t < k["r_gone"]:
            rot = tw(t, [(k["r_grab"], -0.9), (k["r_up"], -0.12), (k["l6_stop"], -0.12),
                         (k["l6_stop"] + 0.3, -0.3), (k["r_pocket"], -0.28), (k["r_gone"], -1.2)])
            d["rec"] = dict(rot=rot, rec=t < k["led_off"], led=(1.0 if (t % 1.0) < 0.45 else 0.15)
                            if t < k["led_off"] else 0.0,
                            button=tw(t, [(k["press"], 0.0), (k["press"] + 0.08, 1.0, ease_out),
                                          (k["press"] + 0.32, 1.0), (k["press"] + 0.5, 0.25)]))
    if k["k_reach"] - 0.05 <= t < k["k_back"] + 0.6:
        palm = tw(t, [(k["k_reach"], (pocket[0], pocket[1] + 4)), (k["k_have"], (pocket[0], pocket[1] + 4)),
                      (k["k_out"], (583, 1068)), (k["k_take"], (583, 1068)), (k["k_back"] + 0.5, (XE + 20, 1150))])
        w = tw(t, [(k["k_reach"], 0.0), (k["k_reach"] + 0.3, 1.0), (k["k_take"] + 0.1, 1.0), (k["k_back"] + 0.5, 0.0)])
        ha = tw(t, [(k["k_have"], -1.2), (k["k_out"], -0.15)])
        d["reach"]["l"] = (palm[0], palm[1], w, ha)
        if k["k_have"] <= t < k["k_take"]:
            d["card"] = dict(rot=tw(t, [(k["k_have"], -1.0), (k["k_out"], 0.08)]),
                             s=tw(t, [(k["k_have"], 0.12), (k["k_have"] + 0.25, 0.19)]))
    # ---- the LED through his chest pocket (blinks until he takes the recorder out)
    if t < k["r_grab"]:
        hot = smoothstep(seg(t, k["led"], k["led"] + 0.25))
        d["led"] = 1.0 if (t % 1.0) < 0.45 else 0.12 - 0.07 * hot
        d["led_glow"] = 0.55 + 0.9 * hot
        d["led_s"] = 0.9 + 0.3 * hot
    # ---- expression, blush, sweat, glasses
    d["expr"] = state_at(t, [(0, "neutral"), (jt, "surprised"), (k["l1e"] + 0.3, "neutral"),
                             (k["c_found"] + 0.02, "frozen_shock"), (k["l3"] - 0.08, "awe"),
                             (k["l4"] - 0.05, "curious"), (k["l5"] + 0.3, "neutral"),
                             (k["l5_fell"], "surprised"), (k["l5_build"], "alarmed"),
                             (k["fr_up0"] + 0.1, "panic"), (k["l5b_what"] - 0.04, "scream"),
                             (k["l5be"] + 0.15, "frozen_shock"), (k["blink"], "deadpan"),
                             (k["led"], "neutral"), (k["led_off"] + 0.35, "deadpan"),
                             (k["l6e"] + 0.2, "neutral"), (k["E21"], "neutral"), (k["nod0"] + 0.4, "soft_smile")],
                         0.18)
    if k["c_found"] <= t < k["l3"] - 0.08:
        d["expr"] = "frozen_shock"
    d["blush"] = tw(t, [(jt, 0.12), (jt + 0.35, 0.5), (k["l1e"] + 0.4, 0.45), (k["l2e"], 0.35),
                        (k["c_found"], 0.35), (k["l3e"], 0.42), (k["l5"], 0.3),
                        (k["l5_build"], 0.55), (k["fr_up1"], 0.8), (k["l5b_what"], 0.92), (k["l5be"] + 0.3, 0.9),
                        (k["blink"], 0.75), (k["led"], 0.3),
                        (k["r_look_t"], 0.25), (k["r_look_t"] + 0.4, 0.6), (k["r_look_b"] + 0.2, 0.58),
                        (k["press"], 0.3), (k["l6"], 0.12), (k["E21"], 0.12)])
    d["sweat"] = tw(t, [(k["c_found"], 0.0), (k["c_found"] + 0.4, 0.25), (k["l4e"], 0.15), (k["l5_build"], 0.3),
                        (k["fr_up1"], 0.8), (k["l5b_what"], 1.0), (k["blink"] + 0.4, 0.6), (k["led"] + 0.6, 0.0)])
    d["glasses_dy"] = tw(t, [(jt, 0.0), (jt + 0.06, 7.0), (jt + 0.45, 2.0), (k["l1e"], 0.0),
                             (k["l5_build"], 0.0), (k["l5_build"] + 0.12, 4.0), (k["fr_up1"], 7.0),
                             (k["l5b_what"] + 0.08, 11.0), (k["fr_glass"], 11.0), (k["fr_glass"] + 0.18, 0.0)])
    d["glasses_tilt"] = tw(t, [(k["l5_build"], 0.0), (k["l5_build"] + 0.12, 0.12, ease_out),
                               (k["fr_up1"], 0.2), (k["l5b_what"] + 0.08, 0.3, ease_out),
                               (k["fr_glass"], 0.3), (k["fr_glass"] + 0.18, 0.0)])
    f = {}
    look = (0.9, -0.05)
    if t < k["l1e"] + 0.3:
        look = tw(t, [(k["e1"], (0.6, 0.2)), (k["swing0"], (0.8, 0.35)), (k["swing1"], (0.95, -0.1)),
                      (k["l1_down"] - 0.12, (0.95, -0.05)), (k["l1_down"], (-1.25, 0.1)),
                      (k["l1_down"] + 0.42, (-1.25, 0.1)), (k["l1_down"] + 0.6, (0.95, -0.05))])
        f.update(fk(t, {
            "head_turn": [(k["l1_down"] + 0.05, 0.0), (k["l1_down"] + 0.2, -0.75), (k["l1_down"] + 0.5, -0.75),
                          (k["l1_down"] + 0.72, 0.0)],
            "brow": [(jt, 0.0), (jt + 0.1, 0.35), (k["l1e"], 0.25), (k["l1e"] + 0.5, 0.1)],
            "brow_ang": [(jt, 0.0), (jt + 0.2, 0.25), (k["l1e"] + 0.5, 0.25)],
            "squash": [(jt, 0.0), (jt + 0.06, -0.08), (jt + 0.3, 0.0)],
            "head_nod": [(k["l1_what"] - 0.1, 0.0), (k["l1_what"] + 0.2, 0.06), (k["l1e"], 0.04)],
        }))
    nt = k["notice"]
    if k["l1e"] + 0.3 <= t < k["l4"]:
        look = tw(t, [(k["l1e"] + 0.3, (0.95, -0.05)), (nt + 0.05, (0.95, -0.05)),
                      (nt + 0.3, (0.8, 0.55)), (k["c_found"], (0.75, 0.95)), (k["l4"], (0.75, 0.95))])
        f.update(fk(t, {
            "brow_r": [(k["l2_hey"], 0.0), (k["l2_hey"] + 0.3, 0.3), (nt, 0.25), (nt + 0.3, 0.0)],
            "press": [(k["l2e"], 0.0), (k["l2e"] + 0.25, 0.3), (nt, 0.25), (nt + 0.3, 0.0)],
            "brow_ang": [(k["l1e"] + 0.3, 0.25), (k["l2"], 0.1)],
            "head_nod": [(nt + 0.15, 0.0), (nt + 0.45, 0.14), (k["l3"], 0.14), (k["l3e"], 0.18)],
            "head_turn": [(nt + 0.15, 0.0), (nt + 0.45, 0.1)],
        }))
    if k["l4"] <= t < k["l5b"]:
        cr = k["l5_critter"]
        look = tw(t, [(k["l4"], (0.75, 0.95)), (k["l4"] + 0.12, (0.75, 0.95)), (k["l4"] + 0.32, (0.95, -0.12)),
                      (cr + 0.1, (0.95, -0.1)), (cr + 0.28, (0.75, 0.9)), (cr + 0.7, (0.75, 0.9)),  # the critter!
                      (cr + 0.88, (0.95, -0.1)), (k["l5b"], (0.95, -0.12))])
        f.update(fk(t, {
            "head_nod": [(k["l4"] + 0.2, 0.18), (k["l4"] + 0.48, 0.0), (cr + 0.2, 0.0), (cr + 0.4, 0.1),
                         (cr + 0.8, 0.1), (cr + 1.0, 0.0), (k["fr_up0"], 0.0), (k["fr_up0"] + 0.1, 0.06),
                         (k["fr_up1"], -0.08)],
            "head_turn": [(k["l4"] + 0.2, 0.1), (k["l4"] + 0.48, 0.0)],
            "brow_l": [(k["l4_eyes"], 0.0), (k["l4_eyes"] + 0.25, 0.2), (k["l5"], 0.1)],
            "pupil": [(k["l5_fell"], 0.0), (k["l5_fell"] + 0.2, -0.25), (k["fr_up1"], -0.35)],
            "eye_size": [(k["l5_fell"], 0.0), (k["l5_fell"] + 0.2, 0.08), (k["fr_up1"], 0.14)],
            "open": [(k["l5_build"], 0.0), (k["l5_build"] + 0.2, 0.25), (k["fr_up0"], 0.3), (k["fr_up1"], 0.55)],
            "squash": [(k["fr_up0"], 0.0), (k["fr_up0"] + 0.1, 0.06), (k["fr_up1"], -0.06), (k["fr_up1"] + 0.3, 0.0)],
        }))
    if k["l5b"] - 0.4 <= t < k["led"]:
        wt = k["l5b_what"]
        look = tw(t, [(k["l5b"] - 0.4, (0.95, -0.12)), (k["l5be"], (0.95, -0.1)),
                      (k["blink"], (0.9, -0.05))])
        f.update(fk(t, {
            "head_nod": [(k["l5b"] - 0.4, -0.08), (k["l5b"] - 0.15, 0.03), (wt - 0.05, 0.06), (wt + 0.12, -0.14),
                         (k["l5be"] + 0.2, -0.06), (k["blink"] + 0.2, 0.02)],
            "squash": [(wt - 0.08, 0.05), (wt + 0.06, -0.16, ease_out), (wt + 0.45, -0.06), (k["l5be"] + 0.3, 0.0)],
            "pupil": [(k["l5b"] - 0.4, -0.35), (wt, -0.45), (k["l5be"] + 0.3, -0.5), (k["blink"], -0.3),
                      (k["led"], 0.0)],
            "eye_size": [(k["l5b"] - 0.4, 0.14), (wt + 0.05, 0.22), (k["blink"], 0.08), (k["led"], 0.0)],
            "open": [(k["l5b"] - 0.4, 0.3), (k["l5b"] - 0.1, 0.0), (k["l5be"] + 0.1, 0.0), (k["l5be"] + 0.35, 0.12),
                     (k["blink"], 0.12), (k["fr_dn0"], 0.0)],
            "head_tilt": [(k["blink"] + 0.1, 0.0), (k["blink"] + 0.9, 0.06), (k["led"], 0.03)],
        }))
        # the long slow blink while he processes
        b0 = k["blink"] + 0.16
        if b0 <= t < b0 + 1.0:
            d["blink"] = tw(t, [(b0, 0.0), (b0 + 0.3, 1.0), (b0 + 0.62, 1.0), (b0 + 0.98, 0.0)])
        if k["l5b"] - 0.4 <= t < k["l5be"] + 0.6:
            d["drift"] = False
    led = k["led"]
    if led <= t < k["E17"]:
        look = tw(t, [(led, (0.9, -0.05)), (led + 0.25, (0.9, -0.05)), (led + 0.42, (-0.2, 1.15)),
                      (k["r_up"] - 0.1, (-0.1, 1.1)), (k["r_up"] + 0.15, (0.25, 1.05)),
                      (k["r_look_t"], (0.25, 1.05)), (k["r_look_t"] + 0.15, (1.0, -0.05)),
                      (k["r_look_b"], (1.0, -0.05)), (k["r_look_b"] + 0.15, (0.25, 1.05)),
                      (k["press"] + 0.4, (0.25, 1.05)), (k["press"] + 0.58, (1.0, -0.05))])
        f.update(fk(t, {
            "head_nod": [(led + 0.3, 0.0), (led + 0.55, 0.2), (k["r_look_t"] + 0.1, 0.2),
                         (k["r_look_t"] + 0.3, 0.02), (k["r_look_b"] + 0.1, 0.02), (k["r_look_b"] + 0.3, 0.18),
                         (k["press"] + 0.5, 0.18), (k["press"] + 0.75, 0.0)],
            "head_turn": [(k["r_look_t"] + 0.1, 0.0), (k["r_look_t"] + 0.3, 0.15),
                          (k["r_look_b"] + 0.1, 0.15), (k["r_look_b"] + 0.3, 0.0)],
            "brow_ang": [(k["r_up"], 0.0), (k["r_up"] + 0.4, 0.3), (k["r_look_t"] + 0.3, 0.45),
                         (k["r_breath"], 0.35), (k["r_breath"] + 0.5, 0.05), (k["press"] + 0.5, 0.0)],
            "press": [(k["r_look_b"] + 0.1, 0.0), (k["r_look_b"] + 0.3, 0.45), (k["press"] - 0.1, 0.45),
                      (k["press"] + 0.3, 0.0)],
            "brow": [(k["r_breath"], 0.0), (k["r_breath"] + 0.3, 0.12), (k["press"] + 0.4, 0.0)],
            "lid": [(k["press"], 0.0), (k["press"] + 0.3, 0.08)],
        }))
        if k["r_look_t"] <= t < k["r_look_b"]:
            d["drift"] = False
    # l06: dry, knowing; a brow and a glance at the dead "calculator"; then the WINK
    if k["E17"] <= t < k["l7"] - 0.3:
        pk, ca, ju = k["l6_pocket"], k["l6_calc"], k["l6_just"]
        look = tw(t, [(k["E17"], (1.0, -0.05)), (pk - 0.05, (1.0, -0.05)), (pk + 0.1, (0.55, 0.6)),
                      (ju - 0.1, (0.55, 0.6)), (ju + 0.05, (1.0, -0.06))])
        wk = k["wk0"]
        f.update(fk(t, {
            "brow_l": [(pk - 0.1, 0.0), (pk + 0.15, 0.32), (ju, 0.3), (k["l6e"], 0.12), (wk - 0.1, 0.06)],
            "smirk": [(k["l6_stop"], 0.0), (k["l6e"], 0.25), (wk - 0.1, 0.32), (wk + 0.12, 0.62), (wk + 0.9, 0.5)],
            "curve": [(wk - 0.1, 0.04), (wk + 0.12, 0.3), (wk + 0.9, 0.22)],
            "head_turn": [(wk - 0.15, 0.0), (wk + 0.05, -0.16), (wk + 0.8, -0.1)],
            "lid": [(k["E17"], 0.08), (k["l6e"], 0.1), (wk - 0.1, 0.04)],
            "head_tilt": [(ca, 0.0), (k["l6_stop"], 0.05), (wk - 0.05, 0.05), (wk + 0.1, 0.1), (wk + 0.6, 0.06)],
            "head_nod": [(wk - 0.05, 0.0), (wk + 0.1, 0.07), (wk + 0.5, 0.02)],
        }))
        # the wink: the near eye (the big one we see) shuts, the cheek pushes up, the other
        # eye stays open on Tiredness
        if wk <= t < wk + 0.7:
            ww = tw(t, [(wk, 0.0), (wk + 0.1, 1.0), (wk + 0.44, 1.0), (wk + 0.66, 0.0)])
            f["lid_l"] = f.get("lid_l", 0.0) + 1.15 * ww
            f["lower_l"] = f.get("lower_l", 0.0) + 0.55 * ww
            f["brow_l"] = f.get("brow_l", 0.0) - 0.3 * ww
            f["brow_r"] = f.get("brow_r", 0.0) + 0.12 * ww
            d["blink"] = 0.0
        if wk - 0.6 <= t < wk + 0.62:
            d["blink"] = 0.0
        d["drift"] = False
    if t >= k["l7"] - 0.3:
        look = tw(t, [(k["l7"] - 0.3, (1.0, -0.05)), (k["l7_nine"] - 0.3, (1.0, -0.05)),
                      (k["l7_nine"] - 0.15, (1.15, -0.25)), (k["l7_nine"] + 0.25, (1.15, -0.25)),
                      (k["l7_nine"] + 0.4, (1.0, -0.05)), (k["k_reach"], (1.0, -0.05)),
                      (k["k_reach"] + 0.12, (-0.2, 1.0)), (k["k_have"], (-0.2, 1.0)),
                      (k["k_have"] + 0.15, (1.0, -0.02)), (k["go_turn"] + 0.1, (1.0, -0.02)),
                      (k["go_turn"] + 0.4, (1.15, 0.05))])
        f.update(fk(t, {
            "head_turn": [(k["l7_nine"] - 0.2, 0.0), (k["l7_nine"], 0.12), (k["l7_nine"] + 0.4, 0.0)],
            "head_nod": [(k["k_reach"], 0.0), (k["k_reach"] + 0.2, 0.12), (k["k_have"] + 0.1, 0.12),
                         (k["k_have"] + 0.3, 0.0), (k["l8_be"], 0.0), (k["l8_be"] + 0.25, 0.07),
                         (k["l8e"] + 0.2, 0.0)],
            "brow_ang": [(k["l8"] - 0.4, 0.0), (k["l8"], 0.3), (k["l8e"] + 0.6, 0.25), (k["nod0"] + 0.4, 0.05)],
            "brow": [(k["l8"] - 0.4, 0.0), (k["l8"], 0.1)],
            "lid": [(k["l8"] - 0.4, 0.0), (k["l8"], -0.04)],
        }))
        if t >= k["l8"] - 0.4:
            d["drift"] = False
            sb = k["l8e"] + 0.25
            if sb <= t < sb + 1.0:
                d["blink"] = tw(t, [(sb, 0.0), (sb + 0.3, 1.0), (sb + 0.5, 1.0), (sb + 0.85, 0.0)])
    # the freeze: no blinks, no saccades
    if k["c_found"] <= t < k["l3"] + 0.2:
        d["blink"] = 0.0
        d["drift"] = False
    d["look"] = look
    d["face"] = f
    return d


# =========================================================================== Curiosity (B)
def cur_state(t, k):
    st = k["steps"]
    d = dict(x=C0, pose="sit", pose_from=None, pose_mix=1.0, pose_t=None, face=-1.0, expr="hopeful",
             ears=0.76, look=(0.45, -0.85), tilt=0.06, tail_curl=0.3, blink=None, glow=0.95, glint=None)
    # ---- B start: still looking back up at him; the footsteps: ears shoot up, looks left
    if t < k["c_up"]:
        d["face"] = tw(t, [(st + 0.1, -1.0), (st + 0.3, 1.0, ease_out)])
        d["expr"] = "hopeful" if t < st + 0.2 else "wide"
        d["ears"] = tw(t, [(st + 0.08, 0.76), (st + 0.24, 1.0, ease_out_back)])
        d["look"] = tw(t, [(st + 0.05, (0.45, -0.85)), (st + 0.25, (-0.9, 0.0))])
        d["tilt"] = tw(t, [(st, 0.06), (st + 0.2, -0.04)])
        d["tail_curl"] = tw(t, [(st, 0.3), (st + 0.3, 0.0)])
        d["blink"] = 0.0
        return d
    # ---- the scramble backwards behind his legs
    if t < k["c_sit"] + 0.3:
        mv0, mv1 = k["c_mv0"], k["c_mv1"]
        rate = (CH - C0) / (mv1 - mv0) / (creatures.SPEC_WALK_SPEED * SC)
        d["expr"] = "wide"
        d["face"] = 1.0
        d["tail_curl"] = 0.0
        d["tilt"] = 0.0
        d["ears"] = tw(t, [(k["c_up"], 1.0), (k["c_up"] + 0.4, 0.3)])
        d["look"] = (-0.9, -0.1)
        if t < mv0:
            d.update(pose="stand", pose_from="sit", pose_mix=seg(t, k["c_up"], mv0))
        elif t < mv1:
            d.update(pose="walk", pose_from="stand", pose_mix=seg(t, mv0, mv0 + 0.08),
                     pose_t=-(t - mv0) * rate)
            d["x"] = C0 + (CH - C0) * seg(t, mv0, mv1)
        else:
            d.update(x=CH, pose="sit", pose_from="walk", pose_mix=seg(t, mv1, mv1 + 0.28),
                     pose_t=-(mv1 - mv0) * rate)
        return d
    # ---- hiding (peeking left at Emb), found by the beam, watching
    d["x"] = CH
    d["face"] = 1.0
    d["tail_curl"] = 0.0
    d["expr"] = "wide" if t < k["E6"] else "curious"
    cf = k["c_found"]
    d["ears"] = tw(t, [(k["c_sit"], 0.3), (cf, 0.32), (cf + 0.25, 0.06, ease_out), (k["E6"], 0.1),
                       (k["E6"] + 0.01, 0.45), (k["l5b_what"], 0.45), (k["l5b_what"] + 0.12, 0.2, ease_out),
                       (k["press"] + 0.15, 0.3), (k["press"] + 0.4, 0.62, ease_out_back)])
    cr = k["l5_critter"]
    d["look"] = tw(t, [(k["c_sit"], (-0.9, -0.2)), (cf - 0.2, (-0.9, -0.25)), (cf, (-0.85, -0.45)),
                       (k["l3_thing"] + 0.15, (-0.85, -0.45)), (k["l3_thing"] + 0.32, (0.3, -1.0)),
                       (k["l3e"] - 0.05, (0.3, -1.0)), (k["l3e"] + 0.12, (-0.85, -0.45)),
                       (cr, (-0.85, -0.45)), (cr + 0.2, (0.3, -1.0)),            # "a critter": me?
                       (cr + 0.9, (0.3, -1.0)), (cr + 1.1, (-0.85, -0.4)),
                       (k["led"] + 0.95, (-0.85, -0.4)), (k["led"] + 1.1, (-0.95, -0.55))])
    d["tilt"] = tw(t, [(cr + 0.15, 0.0), (cr + 0.35, -0.12), (cr + 0.9, -0.12), (cr + 1.1, 0.0),
                       (k["led"] + 1.05, 0.0), (k["led"] + 1.25, -0.1)])
    if cf - 0.05 <= t < k["l3e"] + 0.2:
        d["blink"] = 0.0
    d["glow"] = tw(t, [(cf - 0.1, 0.9), (cf + 0.05, 1.2), (cf + 0.8, 1.0)])
    if t >= cf:
        d["glint"] = cf
    # ---- after the click: creeps out to his front foot, sits; then the grin
    o0, o1 = k["c_out0"], k["c_out1"]
    if t >= k["press"] + 0.3:
        d["expr"] = "hopeful"
        d["ears"] = tw(t, [(k["press"] + 0.3, 0.55), (k["l6_calc"], 0.6), (k["l6_calc"] + 0.3, 0.66)])
        d["look"] = tw(t, [(k["press"] + 0.3, (-0.9, -0.45)), (o1, (-0.9, -0.5))])
        d["tilt"] = tw(t, [(k["l6_calc"], 0.0), (k["l6_calc"] + 0.3, -0.14), (k["l6e"] + 0.3, -0.05)])
        if t < o0:
            pass
        elif t < o1:
            rate = (CH - C1) / (o1 - o0) / (creatures.SPEC_WALK_SPEED * SC)
            if t < o0 + 0.15:
                d.update(pose="stand", pose_from="sit", pose_mix=seg(t, o0 - 0.05, o0 + 0.15))
            else:
                d.update(pose="walk", pose_from="stand", pose_mix=seg(t, o0 + 0.15, o0 + 0.25),
                         pose_t=(t - o0 - 0.15) * rate)
            d["x"] = CH - (CH - C1) * smoothstep(seg(t, o0 + 0.05, o1)) if t < o0 + 0.15 else \
                CH - (CH - C1) * seg(t, o0 + 0.05, o1)
        else:
            d.update(x=C1, pose="sit", pose_from="walk", pose_mix=seg(t, o1, o1 + 0.3),
                     pose_t=(o1 - o0 - 0.15) * (CH - C1) / (o1 - o0) / (creatures.SPEC_WALK_SPEED * SC))
    if t >= k["T18"]:
        s18 = k["T18"]
        d["face"] = 0.25
        d["look"] = tw(t, [(s18, (-0.6, -0.6)), (s18 + 0.35, (-0.6, -0.6)), (s18 + 0.52, (0.55, -0.85))])
        d["tilt"] = 0.0
        grin = s18 + 0.8
        if t < grin + 0.3:
            d["blink"] = 0.0
        d["expr"] = "proud" if t >= grin else "hopeful"
        d["ears"] = tw(t, [(s18, 0.66), (grin, 0.66), (grin + 0.22, 0.86, ease_out_back)])
        d["tail_curl"] = tw(t, [(grin, 0.0), (grin + 0.5, 0.75)])
    if t >= k["W19"]:
        d["expr"] = "curious"
        d["face"] = 0.3
        d["ears"] = tw(t, [(k["W19"], 0.6), (k["k_out"], 0.6), (k["k_out"] + 0.2, 0.78, ease_out_back),
                           (k["k_take"] + 0.6, 0.66)])
        d["tail_curl"] = tw(t, [(k["W19"], 0.5), (k["W19"] + 1.0, 0.25)])
        d["look"] = tw(t, [(k["W19"], (-0.85, -0.55)), (k["k_out"], (-0.85, -0.55)),
                           (k["k_out"] + 0.15, (0.05, -1.0)), (k["k_take"] + 0.2, (0.05, -1.0)),
                           (k["k_take"] + 0.45, (0.55, -0.85)), (k["l8"], (-0.85, -0.55)),
                           (k["nod0"] + 0.2, (-0.85, -0.55)), (k["nod0"] + 0.35, (0.6, -0.8))])
        # off after him (it turns round and trots toward the mouth, tail up)
        g0 = k["go_turn"] + 0.12
        if t >= g0:
            d["expr"] = "hopeful"
            d["ears"] = tw(t, [(g0, 0.66), (g0 + 0.25, 0.85, ease_out_back)])
            d["tail_curl"] = tw(t, [(g0, 0.25), (g0 + 0.5, 0.6)])
            d["flip"] = False
            d["face"] = 1.0
            d["look"] = (0.8, -0.3)
            g1 = g0 + 0.25
            if t < g1:
                d.update(pose="stand", pose_from="sit", pose_mix=seg(t, g0, g1))
            else:
                vr = creatures.SPEC_WALK_SPEED * SC * 1.6
                d.update(pose="walk", pose_from="stand", pose_mix=seg(t, g1, g1 + 0.12),
                         pose_t=(t - g1) * 1.6)
                d["x"] = C1 + vr * (t - g1)
    return d


# =========================================================================== flashlight grip
def _flash_cb(state, lens_out):
    """The torch in his far hand, gripped properly: palm + thumb BEHIND the barrel, four
    fingers wrapped round the FRONT of it (the rig's own far hand is hidden: ar_hide)."""
    ang = state["aim_ang"]
    sc = state["s"] / S
    k = FLASH_S * sc
    skin, skin_sh = core.PAL["e_skin"], core.PAL["e_skin_sh"]
    lw = 9.0

    def hold(c, side, x, y, a):
        if side != "r":
            return
        ca, sa = math.cos(ang), math.sin(ang)
        fx_, fy_ = x - 8 * sc * ca, y - 8 * sc * sa          # fist centre (a touch toward the wrist)
        ox, oy = fx_ + 50 * k * ca, fy_ + 50 * k * sa          # torch origin: its knurl in the fist
        with core.saved(c, ox, oy, k, ang):
            # behind the barrel: the palm / heel of the hand and the thumb (tip over the top edge)
            ell(c, -64, 22, 48, 27, skin_sh, lw)
            c.set_line_cap(cairo.LINE_CAP_ROUND)
            for wdt, col in ((30 + 2 * lw, INK), (30, skin_sh)):
                c.move_to(-58, 6)
                c.line_to(-14, -26)
                core.set_color(c, col)
                c.set_line_width(wdt)
                c.stroke()
        r = props.flashlight(c, ox, oy, k, rot=ang, on=1.0)
        lens_out["lens"] = r["lens"]
        lens_out["angle"] = ang
        with core.saved(c, ox, oy, k, ang):
            # in front: four fingers wrapping round the barrel, knuckles below it
            for i_, fxx in enumerate((-86, -68, -50, -32)):
                rect(c, fxx - 9.5, -15, 19, 50, skin if i_ % 2 == 0 else core.mixc(skin, skin_sh, 0.35), lw * 0.75,
                     r=9.5)
            line(c, [(-94, 30), (-24, 30)], core.alpha(skin_sh, 0.9), 4)
    return hold


# =========================================================================== drawing (B)
def draw_B(ctx, t, k, cam, shot_name, info):
    T = tired_state(t, k)
    E = embar_state(t, k)
    Cr = cur_state(t, k)
    b_bg(ctx)
    lens = {}
    anchors = {}
    vr = view_rect(cam, pad=30)
    # Curiosity's glow on the tunnel around it
    cx_glow = Cr["x"] + (-40 if Cr.get("flip", True) else 40)
    gl = Cr["glow"]

    def glow_fn(c):
        core.radial_glow(c, cx_glow, FY - 120, 420, "power", 0.10 * gl)
        core.radial_glow(c, cx_glow, FY + 10, 240, "power", 0.07 * gl)
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_ADD)
    ctx.set_source(soft_layer(vr, glow_fn))
    ctx.paint()
    ctx.restore()

    def draw_cur():
        anchors["cur"] = creatures.draw_specimen(
            ctx, Cr["x"], FY, SC, t, form=1.0, pose=Cr["pose"], expr=Cr["expr"], look=Cr["look"],
            glow=Cr["glow"], blink=Cr["blink"], flip=Cr.get("flip", True), pose_t=Cr["pose_t"], face=Cr["face"],
            tilt=Cr["tilt"], ears=Cr["ears"], tail_curl=Cr["tail_curl"], pose_from=Cr["pose_from"],
            pose_mix=Cr["pose_mix"])

    def draw_emb():
        if not E["visible"]:
            return
        hold = _flash_cb(E, lens)
        anchors["emb"] = human.draw_person(
            ctx, "embar", E["x"], E["y"], E["s"], t, pose=E["pose"], expr=E["expr"], look=E["look"],
            mouth=info.mouth("embar", t), face=E["face"], turn=E["turn"], blink=E["blink"],
            blush=E["blush"], sweat=E["sweat"], hold=hold, hold_sides="r", hold_layer="front",
            reach=E["reach"], pocket_side="near", drift=E["drift"], glasses_dy=E["glasses_dy"],
            glasses_tilt=E["glasses_tilt"], pose_t=E["pose_t"])
        a = anchors["emb"]
        hx, hy, ha = a["hand_l"]
        if E["rec"] is not None:
            r = E["rec"]
            draw_recorder(ctx, hx + 2, hy - 10, REC_S, t, rot=r["rot"], rec=r["rec"], led=r["led"],
                          button=r["button"], detail=False)
            _thumb(ctx, hx, hy, r, t, k)
        if E["card"] is not None:
            props.keycard(ctx, hx + 4, hy - 7, E["card"]["s"], rot=E["card"]["rot"])

    def draw_tired():
        with _no_fringe_drips():
            anchors["tired"] = human.draw_person(
                ctx, "tired", T["x"], T["y"], S, t, pose=T["pose"], expr=T["expr"], look=T["look"],
                mouth=info.mouth("tired", t), face=T["face"], turn=T["turn"], blink=T["blink"],
                pose_t=T["pose_t"], reach=T["reach"], drift=T["drift"], **TK)
        if T["card"]:
            hx, hy, _ = anchors["tired"]["hand_r"]
            props.keycard(ctx, hx - 6, hy - 6, 0.19, rot=tw(t, [(k["k_take"], 0.08), (k["k_take"] + 0.45, -0.18)]))

    # torch state
    pw = smoothstep(seg(t, k["steps"], k["steps"] + 0.5)) if E["visible"] else 0.0
    # characters: Curiosity's group (lighter: it glows) and the people's group
    ctx.push_group()
    draw_cur()
    ctx.push_group()
    draw_emb()
    draw_tired()
    beam = None
    if "lens" in lens and E["aim"] is not None:
        lx, ly = lens["lens"]
        ax, ay = E["aim"]
        L = clamp(math.hypot(ax - lx, ay - ly) * 1.22, 320, 1100)
        beam = (lx, ly, lens["angle"], L, 0.5, pw)
    holes = [(Cr["x"] - 30, FY - 140, 330, 0.42)]
    holes.append((B_MOUTH, 1100, 1100, 0.3))
    if beam is not None:
        lx, ly, ang, L, sp, pw_ = beam
        ax, ay = E["aim"]
        holes.append((ax, min(ay, 1460), 520, 0.5 * pw_))
        holes.append((lx, ly, 520, 0.45 * pw_))
    base = 0.6 - 0.1 * pw
    bm = (beam[:2], beam[2], beam[3], 0.56, beam[5]) if beam is not None else None
    light_chars(ctx, vr, base, holes, tints=[(Cr["x"] - 30, FY - 140, 380, "power", 0.12)], beam=bm)
    pat = ctx.pop_group()
    # Curiosity: half the darkness (its own glow keeps it readable)
    light_chars(ctx, vr, base * 0.5, holes, beam=bm)
    pat_c = ctx.pop_group()
    if beam is not None:
        lx, ly, ang, L, sp, pw_ = beam
        fx.flashlight(ctx, lx, ly, ang, L, sp, t, b_static, key=("s05_litB", shot_name),
                      rect=shot_rect(k, shot_name), power=pw_, warm=0.35, haze=0.05, lens=False,
                      exact=shot_name not in ("B2", "W8", "E9", "E15", "E17", "W22"))
    ctx.set_source(pat_c)
    ctx.paint()
    ctx.set_source(pat)
    ctx.paint()
    # emissive bits on top: the pocket LED, his teal eyes, the torch lens, Curiosity's eyeshine
    if E["visible"] and E.get("led") is not None and "emb" in anchors:
        px, py = anchors["emb"]["pocket"]
        props.recorder(ctx, px + 6, py + 10, E.get("led_s", 0.9) * E["s"] / S, t, led=E["led"],
                       glow=E["led_glow"], only_led=True)
    if "tired" in anchors:
        a = anchors["tired"]
        op = (1 - a["blink"]) * (1 - 0.7 * T["squint"])
        if op > 0.02:
            for e_ in ("eye_l", "eye_r"):
                ex, ey = a[e_]
                core.radial_glow(ctx, ex, ey, 30, core.PAL["power"], 0.2 * op)
    if beam is not None:
        hd_ = anchors["emb"]["head"] if "emb" in anchors else (-9999, -9999)
        occl = 1.0 - smoothstep(seg(math.hypot(beam[0] - hd_[0], beam[1] - hd_[1]), 70, 120))
        core.radial_glow(ctx, beam[0], beam[1], 46, "#fff0c8", 0.55 * pw * (1 - occl))
    jt = k["jolt"]
    if jt <= t < jt + 0.8 and "emb" in anchors:
        tx_, ty_ = anchors["emb"]["top"]
        fx.emote(ctx, "exclaim", tx_ + 42, ty_ - 62, 0.85, t, jt, dur=0.75)
    # sweat flying off him while he freaks out
    if "emb" in anchors and k["fr_up0"] <= t < k["l5be"] + 0.9:
        a = anchors["emb"]
        ex, ey = a["eye_l"]
        for i_, t0 in enumerate((k["fr_up1"] - 0.05, k["l5b"] + 0.05, k["l5b_what"] + 0.02, k["l5be"] + 0.1)):
            if t0 <= t < t0 + 0.7:
                fx.sweat_fly(ctx, ex - 30, ey - 40, 0.8, t, t0, seed=11 + i_, n=4, dur=0.65, side=0)
    if Cr["glint"] is not None and "cur" in anchors:
        ex, ey = anchors["cur"]["eye_l"]
        fx.eye_glint(ctx, ex, ey, 0.7, t, Cr["glint"], dur=0.5)
    return anchors


def _thumb(ctx, hx, hy, r, t, k):
    """His thumb coming over the recorder's pause button for the off click (custom shape)."""
    p0 = k["press"] - 0.35
    if not (p0 <= t < k["press"] + 0.75):
        return
    u = tw(t, [(p0, 0.0), (k["press"] - 0.05, 1.0), (k["press"] + 0.45, 1.0), (k["press"] + 0.75, 0.0)])
    dn = tw(t, [(k["press"] - 0.05, 0.0), (k["press"] + 0.06, 1.0, ease_out), (k["press"] + 0.32, 1.0),
                (k["press"] + 0.5, 0.0)])
    rs = REC_S
    rot = r["rot"]
    bx, by = 58, 44
    cx, cy = hx + 2, hy - 10
    ca, sa = math.cos(rot), math.sin(rot)

    def L(px, py):
        return (cx + (px * ca - py * sa) * rs, cy + (px * sa + py * ca) * rs)
    tip = L(bx, by - 8 + 8 * dn)
    base = L(-150, 70)
    tx, ty = lerp(base[0], tip[0], u), lerp(base[1], tip[1], u)
    ctx.save()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for w, col in ((52 * rs + 6, INK), (52 * rs, core.PAL["e_skin"])):
        ctx.move_to(*base)
        ctx.line_to(tx, ty)
        core.set_color(ctx, col)
        ctx.set_line_width(w)
        ctx.stroke()
    ctx.restore()


# =========================================================================== drawing (A)
def a_tired_state(t, k):
    stop = k["a_stop"]
    v = 590.0
    D = A_TD1 + v * max(0.0, stop - t)
    u = clamp((A_TD0 - D) / (A_TD0 - A_TD1))
    X = lerp(A_TX0, A_TX1, smoothstep(u))
    kpk = smoothstep(seg(t, stop + 0.2, stop + 0.55))
    pose = ("walk", "stand", smoothstep(seg(t, stop - 0.02, stop + 0.3)))
    if t >= stop + 0.2:
        pose = ("stand", POCKET_T, kpk)
    al = k["a_look"]
    fi = k["a_fine"]
    aw = k["a_away"]
    look = tw(t, [(0.0, (0.0, 0.25)), (stop - 0.3, (-0.1, 0.3)), (al, (-0.25, 0.4)),
                  (al + 0.16, (-0.85, 0.85)), (aw, (-0.85, 0.85)), (aw + 0.18, (0.15, 0.1))])
    face = fk(t, {
        "head_turn": [(al + 0.12, 0.0), (al + 0.32, -0.32), (aw + 0.1, -0.32), (aw + 0.35, -0.08)],
        "head_nod": [(al + 0.12, 0.05), (al + 0.32, 0.14), (fi, 0.14), (fi + 0.18, 0.22), (fi + 0.45, 0.12),
                     (aw + 0.1, 0.12), (aw + 0.35, 0.04)],
        "lid": [(fi - 0.05, 0.0), (fi + 0.2, 0.12), (fi + 0.6, 0.06), (aw + 0.2, 0.0)],
        "press": [(fi, 0.0), (fi + 0.2, 0.32), (aw + 0.2, 0.18)],
        "smirk": [(fi + 0.1, 0.0), (fi + 0.35, -0.1), (aw + 0.2, -0.04)],
        "brow_ang": [(al + 0.2, 0.0), (al + 0.45, 0.12), (fi + 0.4, 0.04)],
    })
    turn = tw(t, [(stop - 0.1, 0.1), (stop + 0.35, -0.25)])
    return dict(D=D, X=X, pose=pose, pose_t=t * 1.0 + 0.25, look=look, face=face, turn=turn)


def a_cur_state(t, k):
    ch, ct, cho = k["c_hear"], k["c_turn"], k["c_hope"]
    fi = k["a_fine"]
    face = tw(t, [(ct, 0.15), (ct + 0.32, 1.0)])
    look = tw(t, [(0.0, (-0.2, 0.55)), (ch, (-0.15, 0.55)), (ch + 0.12, (0.35, 0.2)),
                  (ct + 0.2, (0.6, -0.55)), (k["a_stop"], (0.55, -0.8))])
    ears = tw(t, [(0.0, 0.1), (ch, 0.1), (ch + 0.12, 0.24, ease_out), (cho, 0.26),
                  (cho + 0.28, 0.62, ease_out_back), (fi + 0.2, 0.62), (fi + 0.45, 0.78, ease_out_back)])
    tilt = tw(t, [(0.0, 0.14), (ct, 0.12), (ct + 0.3, 0.02), (fi + 0.2, 0.02), (fi + 0.5, 0.08)])
    expr = "sad" if t < cho else "hopeful"
    tail = tw(t, [(fi + 0.2, 0.0), (fi + 0.7, 0.32)])
    blink = 0.0 if (cho - 0.2 < t < cho + 0.6) else None
    return dict(face=face, look=look, ears=ears, tilt=tilt, expr=expr, tail=tail, blink=blink)


def draw_A(ctx, t, k, info):
    core.cached(ctx, "s05_tunA_dark", -300, -300, 1680, 2520, a_dark)
    T = a_tired_state(t, k)
    Cs = a_cur_state(t, k)
    cxs, cys = ap(A_CX, 0, A_CD)
    s_c = (SC / S) * AF / A_CD
    # Curiosity's glow on the floor and walls around it
    ra = (-100, -100, 1280, 2120)

    def glow_fn(c):
        core.radial_glow(c, cxs, cys - 160, 520, "power", 0.11)
        core.radial_glow(c, cxs, cys + 10, 300, "power", 0.08)
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_ADD)
    ctx.set_source(soft_layer(ra, glow_fn))
    ctx.paint()
    ctx.restore()
    D = T["D"]
    tx, ty = ap(T["X"], 0, D)
    s_t = AF / D
    anchors = {}
    ctx.push_group()
    with _no_fringe_drips():
        anchors["tired"] = human.draw_person(
            ctx, "tired", tx, ty, s_t, t, pose=T["pose"], pose_t=T["pose_t"], expr="bored", look=T["look"],
            face=T["face"], turn=T["turn"], mouth=(0.0, 0.0), **TK)
    anchors["cur"] = creatures.draw_specimen(
        ctx, cxs, cys, s_c, t, form=1.0, pose="sit", expr=Cs["expr"], look=Cs["look"], glow=1.0,
        blink=Cs["blink"], face=Cs["face"], tilt=Cs["tilt"], ears=Cs["ears"], tail_curl=Cs["tail"])
    # light: dark, a teal pool from Curiosity, a little warm light from the mouth behind him
    mx, my = ap(0, 500, AD_M)
    light_chars(ctx, ra, 0.62,
                [(cxs + 20, cys - 180, 560, 0.5), (mx, my, 520, 0.3)],
                tints=[(cxs + 20, cys - 160, 600, "power", 0.14), (mx, my - 100, 420, "#ffb070", 0.12)])
    ctx.pop_group_to_source()
    ctx.paint()
    a = anchors["tired"]
    for e_ in ("eye_l", "eye_r"):
        ex, ey = a[e_]
        core.radial_glow(ctx, ex, ey, 34 * s_t / 0.85, core.PAL["power"], 0.2 * (1 - a["blink"]))
    return anchors


# =========================================================================== inserts
def _capsule(ctx, p0, p1, w, fillc, ink, lw):
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for ww, col in ((w + 2 * lw, ink), (w, fillc)):
        ctx.move_to(*p0)
        ctx.line_to(*p1)
        core.set_color(ctx, col)
        ctx.set_line_width(ww)
        ctx.stroke()


def draw_rec_insert(ctx, t, k, info):
    """R14 / R16: the recorder in his palm, close. Screen space."""
    name = shot_at(t, k)[0]
    t0 = k[name]
    t1 = k["E15"] if name == "R14" else k["E17"]
    u = seg(t, t0, t1)
    core.vgradient(ctx, "#15161c", "#07080b")
    core.radial_glow(ctx, 900, 1500, 900, "#ffcf8a", 0.10)         # the torch pool, off right/below
    core.radial_glow(ctx, 200, 500, 700, "#dfe6ee", 0.05)          # his lab coat, out of focus
    rec = t < k["led_off"]
    led = (1.0 if (t % 1.0) < 0.45 else 0.15) if rec else 0.0
    lvl = 0.0
    if rec:
        lvl = 0.12 + 0.18 * max(0.0, core.noise1(t * 3.1, 9)) + 0.9 * mouth_amt(info, t)
    btn = tw(t, [(k["press"], 0.0), (k["press"] + 0.08, 1.0, ease_out), (k["press"] + 0.32, 1.0),
                 (k["press"] + 0.5, 0.3)])
    cx, cy = 482 + 10 * u, 790 - 8 * u
    s_ = 3.2 + 0.12 * u
    rot = -0.07
    skin, skin_sh = core.PAL["e_skin"], core.PAL["e_skin_sh"]
    ink = INK
    lwl = 6.0 / s_
    # behind: his coat sleeve, the wrist, the palm under the device
    with core.saved(ctx, cx, cy, s_, rot):
        _capsule(ctx, (-230, 230), (-128, 112), 92, core.PAL["e_coat"], ink, lwl)
        _capsule(ctx, (-140, 120), (-70, 72), 62, skin, ink, lwl)
        core.ellipse(ctx, 0, 62, 118, 40, 0.0)
        core.fill_stroke(ctx, skin_sh, ink, lwl)
    frozen = rec_counter(k["led_off"])
    draw_recorder(ctx, cx, cy, s_, t, rot=rot, rec=rec, led=led, level=lvl, button=btn, frozen=frozen)
    with core.saved(ctx, cx, cy, s_, rot):
        # fingertips curled over the right edge (in front)
        for i_, fy_ in enumerate((-50, -24, 2, 28)):
            core.ellipse(ctx, 124, fy_, 17, 11.5, 0.25)
            core.fill_stroke(ctx, skin if i_ % 2 == 0 else core.mixc(skin, skin_sh, 0.3), ink, lwl * 0.85)
            ctx.move_to(118, fy_ - 2)
            ctx.line_to(131, fy_ + 1)
            core.stroke(ctx, core.alpha(skin_sh, 0.9), 1.0)
        # the thumb: resting along the bottom-left edge; in R16 it comes over the PAUSE button
        uu, dn = 0.0, 0.0
        if name == "R16":
            p0 = k["R16"] + 0.05
            uu = tw(t, [(p0, 0.0), (k["press"] - 0.04, 1.0), (k["press"] + 0.55, 1.0), (k["press"] + 0.95, 0.45)])
            dn = tw(t, [(k["press"] - 0.04, 0.0), (k["press"] + 0.05, 1.0, ease_out), (k["press"] + 0.32, 1.0),
                        (k["press"] + 0.5, 0.0)])
        root = (-98, 66)
        tip = (lerp(-46, 58, uu), lerp(70, 41 + 3 * dn, uu))
        knk = (lerp(root[0], tip[0], 0.48), lerp(root[1], tip[1], 0.48) + 6 * uu)
        core.ellipse(ctx, root[0] - 4, root[1] + 6, 30, 24, 0.3)            # the ball of the thumb
        core.fill_stroke(ctx, skin, ink, lwl * 0.85)
        _capsule(ctx, root, knk, 30, skin, ink, lwl * 0.85)
        _capsule(ctx, knk, tip, 25 - 2 * dn, skin, ink, lwl * 0.85)
        _capsule(ctx, (root[0] + 2, root[1]), knk, 27, skin, skin, 0.0)
        core.ellipse(ctx, root[0] - 4, root[1] + 6, 27, 21, 0.3)
        core.fill(ctx, skin)
        ang_ = math.atan2(tip[1] - knk[1], tip[0] - knk[0])
        ex_, ey_ = tip[0] - 4 * math.cos(ang_), tip[1] - 4 * math.sin(ang_) - 2
        core.ellipse(ctx, ex_, ey_, 8, 6, ang_)
        core.fill_stroke(ctx, core.mixc(skin, "#ffffff", 0.45), core.alpha(ink, 0.55), 0.5)
    # the LED's red light spill + a click flash on the button
    fx.vignette(ctx, 0.7, inner=0.4)


def draw_card_insert(ctx, t, k):
    """K20: the keycard in his (bandaged) hand, close. Screen space: a dim, defocused
    tunnel wall behind, a custom big hand (the rig's hands are not built for this size)."""
    t0 = k["K20"]
    u = seg(t, t0, k["E21"])
    with core.camera(ctx, 820, 1000, 3.1 + 0.15 * u):
        b_bg(ctx)
    ctx.rectangle(0, 0, core.W, core.H)
    core.fill(ctx, core.alpha("#0b0b12", 0.35))
    fx.vignette(ctx, 0.75, inner=0.35)
    core.radial_glow(ctx, 160, 1250, 760, "#ffcf8a", 0.12)      # Emb's torch on the floor, off left
    core.radial_glow(ctx, 560, 780, 700, "#ffe2b8", 0.08)
    bob = 3 * math.sin((t - t0) * 2.4)
    cx, cy = 470 + 12 * u, 770 + bob - 16 * u
    rot = tw(t, [(t0, -0.16), (t0 + 0.6, -0.08), (k["E21"], -0.06)])
    cs = 1.72 + 0.06 * u
    ink = INK
    skin, skin_sh = core.PAL["t_skin"], core.PAL["t_skin_sh"]
    lw = 6
    with core.saved(ctx, cx, cy, 1.0, rot):
        wr, el = (372, 238), (760, 1060)
        ang = math.atan2(el[1] - wr[1], el[0] - wr[0])
        _capsule(ctx, wr, el, 176, skin, ink, lw)
        for i in range(3):
            a_ = 0.24 + 0.15 * i
            px, py = lerp(wr[0], el[0], a_), lerp(wr[1], el[1], a_)
            with core.saved(ctx, px, py, 1.0, ang + math.pi / 2):
                core.rrect(ctx, -100, -38, 200, 80, 22)
                core.fill_stroke(ctx, "#f3f1ea" if i != 1 else "#e6e3da", ink, 5)
                ctx.move_to(-70, -8)
                ctx.line_to(60, 12)
                core.stroke(ctx, core.alpha("#b8b2a4", 0.8), 4)
        with core.saved(ctx, lerp(wr[0], el[0], 0.9), lerp(wr[1], el[1], 0.9), 1.0, ang + math.pi / 2):
            core.rrect(ctx, -128, -90, 256, 240, 46)
            core.fill_stroke(ctx, core.mixc(core.PAL["t_hoodie"], "#000000", 0.1), ink, lw)
            ctx.move_to(-110, -40)
            ctx.line_to(110, -50)
            core.stroke(ctx, core.PAL["t_hoodie_dk"], 6)
        core.ellipse(ctx, 338, 118, 112, 142, -0.35)
        core.fill_stroke(ctx, skin, ink, lw)
        for i, fy_ in enumerate((-118, -52, 14)):
            core.ellipse(ctx, 318, fy_, 62, 34, 0.12)
            core.fill_stroke(ctx, skin_sh if i % 2 else skin, ink, 5)
    props.keycard(ctx, cx, cy, cs, rot=rot, glint=smoothstep(seg(t, t0 + 0.35, t0 + 1.05)))
    with core.saved(ctx, cx, cy, 1.0, rot):
        base, tip = (402, 262), (276, 158)
        _capsule(ctx, base, tip, 74, skin, ink, lw)
        core.ellipse(ctx, tip[0] + 6, tip[1] + 4, 24, 17, math.atan2(tip[1] - base[1], tip[0] - base[0]))
        core.fill_stroke(ctx, core.mixc(skin, "#ffffff", 0.38), core.alpha(ink, 0.6), 3)
        ctx.move_to(300, 168)
        ctx.curve_to(285, 150, 280, 140, 268, 132)
        core.stroke(ctx, core.alpha(ink, 0.5), 4)


# =========================================================================== render
def render(ctx, t, info):
    k = keys_for(info)
    name, t0, kind, camf = shot_at(t, k)
    if kind == "R":
        draw_rec_insert(ctx, t, k, info)
        return
    if kind == "K":
        draw_card_insert(ctx, t, k)
        return
    cam = camf(t)
    with core.camera(ctx, *cam):
        if kind == "A":
            draw_A(ctx, t, k, info)
        else:
            draw_B(ctx, t, k, cam, name, info)
    fx.vignette(ctx, 0.35, inner=0.6)


# =========================================================================== sound
def SFX(info):
    k = keys_for(info)
    ev = []
    st = k["steps"]
    # A: his slippers on the tunnel floor (walk contacts every 0.5 s), stop; the "fine" exhale
    pt0 = 0.25
    n = 0
    while True:
        tt = (0.5 * n + 0.27) - pt0
        n += 1
        if tt < 0:
            continue
        if tt > k["a_stop"] + 0.05:
            break
        ev.append((tt, "footstep", -11, 0.1))
    ev.append((k["a_stop"] + 0.25, "footstep", -15, 0.1))
    ev.append((k["c_hear"], "ears_perk", -9, -0.2))
    ev.append((k["c_hope"] + 0.05, "creature_chitter", -14, -0.2))
    ev.append((k["a_fine"] + 0.05, "sigh", -12, 0.05))
    # B: his footsteps coming up the dark tunnel (echoing, getting closer), from the left
    e0, e1 = k["e0"], k["e1"]
    tt = st - 0.05
    while tt < e1 + 0.05:
        g = lerp(-20, -8, seg(tt, st - 0.05, e1))
        ev.append((tt, "footstep", g, -0.6))
        tt += 0.5
    ev.append((st + 0.2, "ears_perk", -3, -0.2))
    ev.append((k["c_mv0"] + 0.05, "scurry", -10, 0.1))
    ev.append((k["jolt"], "cloth_rustle", -6, -0.4))
    ev.append((k["c_found"] + 0.02, "critter_squeak", -12, 0.05))
    # the freak-out: hands to his head, the sweat
    ev.append((k["fr_up0"] + 0.05, "cloth_rustle", -7, -0.4))
    ev.append((k["l5b_what"] - 0.05, "cloth_rustle", -12, -0.4))
    ev.append((k["fr_glass"], "latch_click", -24, -0.4))
    # recorder: out of the pocket, the decision, the click
    ev.append((k["r_reach"] + 0.15, "cloth_rustle", -8, -0.3))
    ev.append((k["press"] + 0.02, "recorder_click", 2, -0.1))
    ev.append((k["r_pocket"] + 0.1, "cloth_rustle", -13, -0.3))
    # Curiosity creeps out; grins
    ev.append((k["c_out0"] + 0.2, "scurry", -20, 0.0))
    ev.append((k["T18"] + 0.8, "creature_chitter", -6, 0.0))
    # keycard out of the coat, handed over
    ev.append((k["k_reach"] + 0.1, "cloth_rustle", -9, -0.3))
    # off toward CONTROL
    gw = k["go_walk"]
    for i in range(3):
        if gw + 0.5 * i < info.dur - 0.1:
            ev.append((gw + 0.5 * i, "footstep", -11 - 2 * i, 0.35))
    # a slow drip somewhere deep in the dark tunnel
    tt = 1.4
    while tt < info.dur:
        ev.append((tt, "drip", -21, -0.5))
        tt += 6.3
    return ev
