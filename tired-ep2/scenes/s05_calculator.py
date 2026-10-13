"""s05 -- the pocket calculator ("awkward").  Revision 3.

Continues s04: the creature waited for him a little way down the dark side tunnel (to SHAFT A);
Embarrassment, coming up the tunnel from the other end, ran into it and yelled ("Oh my God! What
IS that thing?!"); Tiredness sighed, got up and walked in after the voice. The whole scene plays
INSIDE that dark side tunnel (set B, drawn here: ribbed concrete vault side-on, SHAFT A <- stencil,
the corridor mouth off screen-right), lit only by Curiosity's glow, his teal eyes, a little warm
spill from the mouth and Embarrassment's flashlight.

Shot list (every time derives from cues / line timings, see K() / shots()):
  C1  catch .. steps       two-shot: Emb backed flat against the tunnel wall, terrified, his beam
                           shaking on the creature; it is crouched low, ears flat, wary (not
                           aggressive). Slow push-in.
  B2  steps .. l01 "What"  wide: footsteps from the dark (right); ears twitch, it looks back over its
                           shoulder; Tiredness walks in (hands in the hoodie pocket); the beam swings
                           onto his face (squint); it is him: Emb's jolt, "Tiredness?!"; the creature
                           relaxes (ears up, hopeful) and rises.
  E3  .. l01.end+.4        Emb medium: "What are you doing down here?": relief (exhale, shoulders
                           drop), he peels off the wall and steps up to him; glance back on "down".
  T4  .. "I'm"-.15         Tiredness medium in the beam, squinting: "Oh, hey. Yeah." (one lazy wave)
  W5  .. "horrible"-.1     two-shot: "I'm helping my creature take down a massive..." the creature
                           trots over and sits by his leg (the beam follows it); a little shrug; a
                           glance down at it on "my creature"; Emb's eyes follow it, baffled
  T5b .. l02.end+.2        Tiredness close: "...horrible corporation that's doing shady things."
                           matter-of-fact; a flat look on "shady things"; lip press
  E5c .. notice+.5         Emb CU: "oh no, that's MY company": frozen, blush + sweat rise; "Ha... ha.
                           Cool. Cool cool cool." hand behind his head (scratch), strained grin, eyes
                           darting, sliding down to the recorder in his pocket; notice: his eyes go
                           to the creature
  W5d .. l03.end+.35       two-shot push-in: the beam drifts onto the creature; "Is that one of the
                           creatures from the lab I work at?" he leans in, squints, pushes his glasses
                           up; its ears sink on "lab"; Tiredness's brow lifts a hair on "I work at"
  W5e .. l03c "Your"-.15   two-shot: "You shouldn't be around that. We should bring it back." points
                           back down the tunnel (thumb up); it presses behind Tiredness's leg; he
                           steps half in front of it; "Buddy."
  T5f .. l03c "That's"-.15 Tiredness medium: "Your company is locking these creatures up." calm, firm
  E5g .. l03d-.17          Emb CU: "That's not cool." guilt: eyes down, then away
  W5h .. l03d "dude"+.35   two-shot: "We gotta save them. Okay, dude?" his open hand; Emb conflicted
  E6  .. l04 "glowing"     Emb close: a small swallow, eyes down at it; then up to Tiredness's eyes:
                           "And why are your eyes glowing?!"
  T7  .. l05 "I"           Tiredness close, SUPER chill (hands in pocket, flat, lazy pocket shrug):
                           "Oh, yeah. A critter bit me,"
  W8  .. l05.end+.25       two-shot: "...I fell out of a building, and now I can see in the dark."
                           he stays flat; Emb escalates: eyes, jaw, glasses slip, hands to his head
  E9  .. l05b.end+.3       Emb CU FREAKING OUT: hands on his head, blush 0.9, glasses askew, sweat
                           flying: "You fell out of a WHAT?!"
  T10 .. l05c.end+.3       Tiredness CU: a beat, "It's been a day." lazy shrug, slow blink
  E11 .. led               Emb CU: the long slow blink; hands come down, he pushes his glasses straight
  W12 .. conflict+.95      three-shot: the red LED blinks in his pocket; eyes slide down to it one by
                           one; he pinches the recorder out and holds it in his palm
  R14 .. conflict+2.3      INSERT: the CalmCorp recorder in his palm: blinking "REC", running counter,
                           mic grille, logo, a little level meter listening
  E15 .. click-.1          Emb CU: at Tiredness, down at the creature behind his legs, back at the
                           recorder; blush; a breath
  R16 .. l06 "Huh."+.12    INSERT: his thumb presses pause: click, "PAUSED", LED off, meter flat
  E17 .. wink+.62          Emb close: "Huh. My "pocket calculator"... just stopped working." -- dry,
                           knowing; then the WINK with a small knowing smile (slow push-in)
  T18 .. l07-.25           Tiredness + Curiosity: his faintest smile back; it looks up and grins
  W19 .. l07.end           two-shot: "The control room is on level nine. Take my keycard." handoff
  K20 .. l08               insert: the keycard (LVL 9) in his bandaged hand, a glint
  E21 .. l08.end+.35       Emb close: "And Tiredness? Be careful." sincere, slow
  W22 .. end               two-shot: a small nod; he turns toward CONTROL (the mouth) and sets off,
                           Curiosity trots after him; Emb watches them go

Hands: Tiredness keeps his hands IN the hoodie's kangaroo pocket (rig reach targets on the pocket
plus a redraw of the pocket's front panel over the wrists, see tired_pocket()/pocket_overlay()), so
no frame shows an arm ending in nothing.
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
XT = 790                 # Tiredness (facing left, toward the deep end) from his protective half-step on
XT0 = 845                # where he first stops after walking in
T_WALK = 1.25            # his walk-in (s; ends on a contact)
XE = 325                 # Embarrassment (facing right)
XW, YW, SW = 372, 1345, 0.62     # Embarrassment backed flat against the far wall, on a rib (catch)
CC = 600                 # Curiosity crouched in the beam (catch)
CS = 668                 # sitting by his (front) leg (l02)
CH = 785                 # pressed behind his legs (head peeks out on the left)
C1 = 640                 # out again, sitting by his front foot (after the click)
TK = dict(outfit="sewer", bandage=True, headphones=None, hood=0.0, power=0.6)
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
    """CalmCorp voice recorder (~240 x 150 at s=1, centre anchor): mic grille, a small LCD
    ("REC" + running counter + level meter, or "PAUSED"), three face buttons (rec / pause /
    stop), the logo + CALMCORP wordmark, a red LED top-left."""
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
            props.spaced_text(c, "CALMCORP", -44, 51, 10.5, "#2fd1c5", "ui", 0.3)
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
    for n in ("catch", "steps", "notice", "blink", "led", "conflict", "click", "wink", "smile", "card", "nod"):
        k[n] = c(n)
    for tag, lid in (("l1", "s05_l01"), ("l2", "s05_l02"), ("l2b", "s05_l02b"), ("l3", "s05_l03"),
                     ("l3b", "s05_l03b"), ("l3c", "s05_l03c"), ("l3d", "s05_l03d"), ("l4", "s05_l04"),
                     ("l5", "s05_l05"), ("l5b", "s05_l05b"), ("l5c", "s05_l05c"), ("l6", "s05_l06"),
                     ("l7", "s05_l07"), ("l8", "s05_l08")):
        ln = L(lid)
        k[tag], k[tag + "e"] = ln.start, ln.end
    k["l1_what"] = w("s05_l01", 1)
    k["l1_down"] = w("s05_l01", 5)
    for name, i in (("oh", 0), ("hey", 1), ("yeah", 2), ("im", 3), ("my", 5), ("creature", 6), ("take", 7),
                    ("massive", 10), ("horrible", 11), ("corp", 12), ("shady", 15), ("things", 16)):
        k["l2_" + name] = w("s05_l02", i)
    for name, i in (("ha", 0), ("ha2", 1), ("cool", 2), ("cool2", 3), ("cool3", 4), ("cool4", 5)):
        k["l2b_" + name] = w("s05_l02b", i)
    for name, i in (("one", 2), ("creat", 5), ("lab", 8), ("work", 10)):
        k["l3_" + name] = w("s05_l03", i)
    for name, i in (("that", 4), ("we", 5), ("bring", 7), ("back", 9)):
        k["l3b_" + name] = w("s05_l03b", i)
    for name, i in (("buddy", 0), ("your", 1), ("locking", 4), ("up", 7), ("thats", 8), ("cool", 10)):
        k["l3c_" + name] = w("s05_l03c", i)
    for name, i in (("save", 2), ("okay", 4), ("dude", 5)):
        k["l3d_" + name] = w("s05_l03d", i)
    k["l4_eyes"] = w("s05_l04", 4)
    k["l4_glow"] = w("s05_l04", 5)
    k["l5_yeah"] = w("s05_l05", 1)
    k["l5_critter"] = w("s05_l05", 3)   # "creature"
    k["l5_I"] = w("s05_l05", 6)
    k["l5_fell"] = w("s05_l05", 7)
    k["l5_build"] = w("s05_l05", 11)
    k["l5_and"] = w("s05_l05", 12)
    k["l5_see"] = w("s05_l05", 16)
    k["l5_dark"] = w("s05_l05", 19)
    k["l5b_fell"] = w("s05_l05b", 1)
    k["l5b_what"] = w("s05_l05b", 5)
    k["l5c_day"] = w("s05_l05c", 3)
    # rev 4 line: "Oh, look at that. My recorder just stopped working." (keys keep their old names)
    k["l6_huh"] = w("s05_l06", 0)        # "Oh"
    k["l6_pocket"] = w("s05_l06", 4)     # "My"
    k["l6_calc"] = w("s05_l06", 5)       # "recorder"
    k["l6_just"] = w("s05_l06", 6)
    k["l6_stop"] = w("s05_l06", 7)
    k["l7_nine"] = w("s05_l07", 6)
    k["l7_take"] = w("s05_l07", 7)
    k["l7_card"] = w("s05_l07", 9)
    k["l8_be"] = w("s05_l08", 2)
    st = k["steps"]
    # ---- catch / steps: Emb against the wall; Tiredness walks in from the dark (right)
    k["vT"] = abs(human.cycle_speed("tired", "walk", -0.7, "sewer")) * S
    k["t_in0"] = st + 0.05
    k["t_stop"] = k["t_in0"] + T_WALK
    k["swing0"], k["swing1"] = st + 0.62, st + 0.98          # the beam swings off it, onto his face
    k["jolt"] = st + 1.6                                      # it's HIM: Emb's take
    k["c_ear"], k["c_look"] = st + 0.12, st + 0.3             # the creature hears him, looks back
    k["c_relief"] = k["t_stop"]                               # ...it's him: ears up, hopeful
    k["c_rise"] = k["c_relief"] + 0.4
    # ---- l01 relief: Emb peels off the wall and steps up to his mark
    k["e_exhale"] = k["l1_what"] - 0.14
    k["e_step0"] = k["l1_what"] + 0.1
    k["e_step1"] = k["e_step0"] + 1.0
    # ---- l02: the creature trots over and sits by his leg; the beam follows it
    k["c_trot0"] = k["l2_im"] + 0.05
    k["c_trot1"] = k["c_trot0"] + 0.85
    k["c_emb"] = k["c_trot1"] + 0.9                           # it looks back at Emb
    # ---- l02b: hand behind his head
    k["hbh0"] = k["l2b"] - 0.3
    k["hbh1"] = k["notice"] + 0.12
    # ---- notice / l03: the beam back on it; lean in, squint, push the glasses up
    k["c_found"] = k["notice"] + 0.62
    k["lean0"] = k["l3"] - 0.05
    k["gl0"] = k["l3_creat"] - 0.12
    k["gl_push"] = k["gl0"] + 0.32
    k["gl1"] = k["gl_push"] + 0.4
    # ---- l03b: the point back down the tunnel; it presses behind his leg; his half-step
    k["pt0"] = k["l3b_bring"] - 0.28
    k["pt1"] = k["l3b_back"] + 0.75
    k["c_back0"] = k["l3b_bring"] + 0.1
    k["c_back1"] = k["c_back0"] + 0.7
    k["t_step0"] = k["l3be"] + 0.15
    k["t_step1"] = k["t_step0"] + 0.55
    # ---- l03c guilt, l03d open hand, the swallow
    k["g_down"] = k["l3c_thats"] + 0.12
    k["g_away"] = k["l3c_cool"] + 0.45
    k["oh0"] = k["l3d"] - 0.15
    k["oh1"] = k["l3d_okay"] + 0.3
    k["gulp"] = k["l3de"] + 0.08
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
    k["r_look_c"] = cf + 2.95                  # down to the creature behind his legs
    k["r_look_b"] = cf + 3.5                   # back to the recorder
    k["r_breath"] = cf + 3.57
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
    k["C1"] = 0.0
    k["B2"] = st + 0.05
    k["E3"] = k["l1_what"] - 0.07
    k["T4"] = k["l1e"] + 0.4
    k["W5"] = k["l2_im"] - 0.15
    k["T5b"] = k["l2_horrible"] - 0.1
    k["E5c"] = k["l2e"] + 0.2
    k["W5d"] = k["notice"] + 0.5
    k["W5e"] = k["l3e"] + 0.35
    k["T5f"] = k["l3c_your"] - 0.15
    k["E5g"] = k["l3c_thats"] - 0.15
    k["W5h"] = k["l3d"] - 0.17
    k["E6"] = k["l3d_dude"] + 0.35
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
        ("C1", 0.0, "B", lambda t: tw(t, [(0.0, (452, 1150, 1.48)), (k["B2"], (446, 1140, 1.58))])),
        ("B2", k["B2"], "B", lambda t: tw(t, [(k["B2"], (560, 1110, 1.2)), (k["E3"], (556, 1106, 1.24))])),
        ("E3", k["E3"], "B", lambda t: tw(t, [(k["e_step0"], (448, 862, 2.42)), (k["e_step1"] + 0.2, (470, 882, 2.5))])),
        ("T4", k["T4"], "B", lambda t: (790, 1010, 2.3)),
        ("W5", k["W5"], "B", lambda t: tw(t, [(k["W5"], (606, 1140, 1.42)), (k["T5b"], (612, 1134, 1.47))])),
        ("T5b", k["T5b"], "B", lambda t: tw(t, [(k["T5b"], (767, 985, 2.45)), (k["E5c"], (767, 980, 2.56))])),
        ("E5c", k["E5c"], "B", lambda t: (392, 880, 2.3)),
        ("W5d", k["W5d"], "B", lambda t: tw(t, [(k["W5d"], (585, 1140, 1.45)), (k["l3e"], (455, 1040, 1.9))])),
        ("W5e", k["W5e"], "B", lambda t: tw(t, [(k["W5e"], (522, 1150, 1.24)), (k["T5f"], (530, 1146, 1.28))])),
        ("T5f", k["T5f"], "B", lambda t: (735, 1010, 2.3)),
        ("E5g", k["E5g"], "B", lambda t: (445, 890, 2.5)),
        ("W5h", k["W5h"], "B", lambda t: (572, 1138, 1.46)),
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
class PD(dict):
    """A pose dict that also says which of Tiredness's hands are in the hoodie pocket (`pk`)."""
    pk = ""


def pdict(pk, **kw):
    d = PD(kw)
    d.pk = pk
    return d


HIDE_PK = 0.53    # a pocketed hand is hidden only while (almost) all the way in (blend k < 0.06)
# facing left (turn -0.7) the far (l) arm stays BEHIND the body all the time (no layer pops)
_FIST = dict(al_h="fist", ar_h="fist", al_hide=HIDE_PK, ar_hide=HIDE_PK, al_layer="back")

# both hands in the kangaroo pocket (the reach targets + panel overlay put them really IN it)
POCK = pdict("lr", base="hands_pockets", ar_layer="mid", **_FIST)
POCKET_T = POCK
# walking with both hands in the pocket (the walk-in; the exit faces right: the r arm is far)
WALK_PK = pdict("lr", base="walk", ar_layer="mid", **_FIST)
POCK_M = pdict("lr", base="hands_pockets", al_h="fist", ar_h="fist", al_hide=HIDE_PK, ar_hide=HIDE_PK,
               al_layer="mid", ar_layer="mid")
WALK_PKR = pdict("lr", base="walk", al_h="fist", ar_h="fist", al_hide=HIDE_PK, ar_hide=HIDE_PK,
                 al_layer="mid", ar_layer="back")
# a lazy hello: the near hand comes out of the hoodie pocket for one small bent-elbow wave,
# the other hand stays in the pocket (wave_small's arm on top of hands_pockets)
WAVE_T = pdict("l", base="hands_pockets", period=0.7, ar_p=0.35, ar_o=1.2, ar_e=2.3,
               ar_eo=human.W(-1.1, 0.12, 0.0), ar_w=human.W(0.0, 0.16, 0.1), ar_h="open",
               ar_tf=-1.0, ar_hide=0.0, hunch=0.3, al_h="fist", al_hide=HIDE_PK, al_layer="back")
WAVE_MID = pdict("l", base="hands_pockets", ar_p=0.25, ar_o=1.0, ar_e=1.4, ar_eo=-0.6,
                 ar_h="open", ar_tf=-1.0, ar_hide=0.0, hunch=0.3, al_h="fist", al_hide=HIDE_PK, al_layer="back")
# "We gotta save them.": the near hand comes out, open palm up toward Emb (soft appeal)
OPEN_T = pdict("l", base="hands_pockets", ar_p=0.8, ar_o=0.22, ar_e=0.62, ar_eo=-0.1, ar_w=-0.1,
               ar_h="open", ar_tf=-1.0, ar_hide=0.0, lean=0.04, hunch=0.35, al_h="fist", al_hide=HIDE_PK,
               al_layer="back")
# taking the keycard: only the near hand comes out of the pocket (the other stays in: chill)
CARD_T = pdict("l", base="hands_pockets", ar_hide=0.0, ar_h="relaxed", al_h="fist", al_hide=HIDE_PK,
               al_layer="back")


def shrug_pose(a):
    """A lazy, nonchalant shrug with his hands staying in the hoodie pocket: shoulders up,
    elbows out a little, head tilt (a = 0..1)."""
    return pdict("lr", base="hands_pockets", hunch=0.6 + 0.8 * a, neck=-0.5 * a, tilt=0.12 * a,
                 lift=8 * a, ar_layer="mid", **_FIST)


def pocket_w(pose, side):
    """0..1: how far `side`'s hand is in the hoodie pocket for this pose / blend."""
    def one(p):
        return 1.0 if isinstance(p, PD) and side in p.pk else 0.0
    if isinstance(pose, tuple):
        return lerp(one(pose[0]), one(pose[1]), pose[2])
    return one(pose)


def tired_pocket(T, t):
    """Pocket geometry for this frame (rig-local, from the rig's own torso solve): the hand
    targets inside the kangaroo pocket and what pocket_overlay() needs. None = no hand in it."""
    pose = T["pose"]
    w = {s_: pocket_w(pose, s_) for s_ in "lr"}
    if max(w.values()) < 0.01:
        return None
    C = human._char("tired", "sewer")
    pt = t if T["pose_t"] is None else T["pose_t"]
    Q = human.resolve_pose(pose, "tired", pt)
    pw_ = Q["posture"]
    for key, v in C["posture"].items():
        Q[key] = Q[key] + v * pw_
    J = human._solve(C, Q, "tired", T["turn"], t, {"head_turn": 0.0, "head_tilt": 0.0, "head_nod": 0.0},
                     0.0, None, None)
    J["t"] = t
    lv = human._torso_geom(C, J)
    aw = C["tw"]["waist"][0]
    x, y, s = T["x"], T["y"], S
    turn = T["turn"]
    targets = {}
    for side, sgn in (("l", -1.0), ("r", 1.0)):
        if w[side] < 0.01:
            continue
        far = smoothstep((-sgn * turn - 0.1) / 0.4)          # this hand is on the far side
        inx = lerp(0.22, 0.04, far)
        g = human._front(lv, "hem", sgn * aw * inx, 56)
        e = human._front(lv, "hem", sgn * aw * 0.7, 62)
        targets[side] = (x + s * g[0], y + s * g[1], w[side], math.atan2(g[1] - e[1], g[0] - e[0]))
    return dict(C=C, J=J, lv=lv, w=w, targets=targets)


def pocket_overlay(ctx, T, pk, a):
    """Redraw the kangaroo pocket's front panel over the pocketed hands (clipped to the torso
    and to small discs round those hands), so the wrists go INTO the pocket."""
    C, J, lv = pk["C"], pk["J"], pk["lv"]
    aw = C["tw"]["waist"][0]
    x, y, s = T["x"], T["y"], S
    discs = []
    for side in "lr":
        if pk["w"][side] > 0.01:
            for key in ("hand_", "wrist_"):
                px, py = a[key + side][:2]
                discs.append(((px - x) / s, (py - y) / s))
    if not discs:
        return
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    human._smooth(ctx, human._torso_pts(C, J, lv), True, 0.5)
    ctx.clip()
    for (px, py) in discs:
        ctx.new_sub_path()
        ctx.arc(px, py, 58, 0, 2 * math.pi)
    ctx.clip()
    p = [human._front(lv, "hem", -aw * 0.62, 20), human._front(lv, "hem", aw * 0.62, 20),
         human._front(lv, "hem", aw * 0.44, 88), human._front(lv, "hem", -aw * 0.44, 88)]
    human._shape(ctx, p, human._dk(C["col"]["top"], 0.08), human.INK_W * 0.7, 0.0)
    ctx.restore()


def shrug_amt(t, k):
    """0..1 lazy shrugs: a little one on "I'm helping", on "Oh, yeah.", on "...in the dark." and on
    "It's been a day."."""
    a = 0.0
    for t0, amp in ((k["l2_im"] - 0.1, 0.6), (k["l5"] - 0.08, 1.0), (k["l5_dark"] - 0.1, 0.65),
                    (k["l5c_day"] - 0.12, 1.0)):
        a = max(a, amp * tw(t, [(t0, 0.0), (t0 + 0.38, 1.0), (t0 + 0.72, 1.0), (t0 + 1.25, 0.0)]))
    return a


def t_x(t, k):
    """Tiredness's x: walks in from the dark (right) to XT0, half a step in front of it to XT."""
    if t < k["t_stop"]:
        return XT0 + k["vT"] * (k["t_stop"] - max(t, k["t_in0"]))
    if t < k["t_step0"]:
        return XT0
    return lerp(XT0, XT, smoothstep(seg(t, k["t_step0"], k["t_step1"])))


def t_face(t, k):
    """His face (the beam's target)."""
    return (t_x(t, k) - 64, 912)


def tired_state(t, k):
    st = k["steps"]
    d = dict(x=t_x(t, k), y=FY, turn=-0.7, pose=POCK, pose_t=None, expr="bored", look=(0, 0),
             blink=None, face={}, reach=None, drift=True, card=False, squint=0.0)
    # ---- body poses
    hey = k["l2_hey"]
    tst = k["t_stop"]
    keys = [(-1, WALK_PK), (tst - 0.05, POCK),
            (hey - 0.32, WAVE_MID), (hey - 0.14, WAVE_T), (hey + 0.56, WAVE_MID), (hey + 0.74, POCK),
            (k["oh0"], OPEN_T), (k["oh1"], POCK)]
    keys += [(k["k_take0"] - 0.12, CARD_T), (k["go_turn"], POCK_M)]
    keys += [(k["go_walk"], WALK_PKR)]
    pose = state_at(t, keys, 0.3)
    if pose[1] in (WAVE_T, WAVE_MID) or pose[0] in (WAVE_T, WAVE_MID):
        pose = state_at(t, keys, 0.18)
        d["pose_t"] = max(0.0, t - (hey - 0.14))
    elif t < tst + 0.4:
        d["pose_t"] = min(t, tst) - k["t_in0"] + 0.25          # the walk-in ends on a contact
    elif pose[1] is WALK_PKR and t >= k["go_walk"]:
        d["pose_t"] = t - k["go_walk"]
    if pose[1] is OPEN_T or pose[0] is OPEN_T:
        pose = state_at(t, keys, 0.4)
    # the protective half-step (l03b -> l03c): half a walk stride, feet kept planted
    if k["t_step0"] <= t < k["t_step1"]:
        u = seg(t, k["t_step0"], k["t_step1"])
        pose = (POCK, WALK_PK, math.sin(math.pi * u) ** 2)
        d["pose_t"] = 0.5 + (XT0 - XT) / k["vT"] * smoothstep(u)
    sa = shrug_amt(t, k)
    if sa > 0.001 and pose[1] is POCK and pose[2] >= 1.0:
        pose = shrug_pose(sa)
    d["pose"] = pose
    # the open hand goes out toward Emb, palm up
    if OPEN_T in (pose[0], pose[1]) if isinstance(pose, tuple) else pose is OPEN_T:
        wo = 1.0 - pocket_w(pose, "r")
        d["reach"] = {"r": (d["x"] - 178, 1112 + 6 * math.sin(t * 2.2), wo, math.pi - 0.12)}
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
    d["expr"] = state_at(t, [(0, "bored"), (k["l2"] - 0.2, "deadpan"), (k["l3d"] - 0.3, "bored"),
                             (k["E6"], "bored"), (k["T18"] - 0.05, "soft_smile"), (k["W19"], "bored")], 0.3)
    if t < k["l4"] - 0.2:
        look, f = tired_opening(t, k, d)
    else:
        # what the opening leaves on his face from here on (the rev-2 values at l04)
        look = (-0.85, 0.05)
        f = {"head_turn": -0.15, "lid": 0.02, "press": 0.12, "brow_r": 0.05}
        look, f = tired_rest(t, k, d, look, f)
    d["look"] = look
    d["face"] = f
    return d


def tired_opening(t, k, d):
    """catch .. l03d: walks in chill, squints in the beam, "Oh, hey. Yeah. I'm helping my
    creature...", a brow at "the lab I work at", protective half-step, calm/firm, soft appeal."""
    st = k["steps"]
    tst = k["t_stop"]
    f = {}
    # walk-in: eyes on the two of them (left), then the beam: squint, head away a touch
    look = tw(t, [(st, (-0.9, 0.1)), (k["swing0"], (-0.9, 0.1)), (k["swing1"] + 0.1, (-0.95, -0.05)),
                  (tst + 0.3, (-0.95, -0.1)), (k["jolt"] + 0.1, (-0.9, -0.05))])
    f.update(fk(t, {
        "head_turn": [(tst - 0.2, -0.05), (tst + 0.25, -0.15)],
        "head_nod": [(st, 0.05), (tst, 0.0)],
        "lid": [(tst, 0.0), (tst + 0.4, -0.03)],
    }))
    # the beam in his face (swing .. it follows the creature on "I'm helping"): squint, flinch
    b_on = smoothstep(seg(t, k["swing1"] - 0.08, k["swing1"] + 0.12)) * \
        (1 - smoothstep(seg(t, k["c_trot0"] + 0.05, k["c_trot0"] + 0.45)))
    d["squint"] = b_on
    if b_on > 0:
        f["lower"] = f.get("lower", 0) + 0.24 * b_on
        f["lid"] = f.get("lid", 0) + 0.03 * b_on
        f["brow"] = f.get("brow", 0) - 0.18 * b_on
        f["head_turn"] = f.get("head_turn", 0) + 0.12 * b_on
        f["head_nod"] = f.get("head_nod", 0) + 0.04 * b_on
    # l01: Emb steps off the wall toward him: his eyes follow, unbothered
    if t >= k["l1"]:
        look = tw(t, [(k["l1"], (-0.9, -0.05)), (k["e_step1"], (-0.8, 0.1)), (k["l2"], (-0.75, 0.15))])
    # l02 "Oh, hey. Yeah.": flat; a chin lift on "hey", a tiny nod on "Yeah"
    hey = k["l2_hey"]
    if t >= k["l2"] - 0.3:
        f = addf(f, fk(t, {
            "head_nod": [(hey - 0.05, 0.0), (hey + 0.12, -0.1), (hey + 0.5, 0.0),
                         (k["l2_yeah"] - 0.02, 0.0), (k["l2_yeah"] + 0.14, 0.06), (k["l2_yeah"] + 0.4, 0.0)],
            "lid": [(k["l2"], 0.0), (k["l2"] + 0.3, 0.05)],
        }))
        # "...my creature": a glance down at it (it is trotting up to his leg), back to Emb
        my = k["l2_my"]
        look = tw(t, [(k["l2"] - 0.3, (-0.75, 0.15)), (my - 0.08, (-0.8, 0.1)), (my + 0.1, (-0.4, 0.85)),
                      (k["l2_take"] + 0.1, (-0.4, 0.85)), (k["l2_take"] + 0.28, (-0.85, 0.05))])
        f = addf(f, fk(t, {"head_nod": [(my, 0.0), (my + 0.22, 0.1), (k["l2_take"] + 0.12, 0.1),
                                        (k["l2_take"] + 0.35, 0.0)]}))
        sa_ = shrug_amt(t, k)
        f = addf(f, {"brow": 0.18 * sa_, "frown": 0.22 * sa_, "head_tilt": 0.05 * sa_})
        # "...doing shady things.": a flat look (lid drop, brows flatten, chin down a hair); lip press
        sh = k["l2_shady"]
        f = addf(f, fk(t, {
            "lid": [(sh - 0.12, 0.0), (sh + 0.18, 0.07), (k["l2e"] + 0.6, 0.05)],
            "brow": [(sh - 0.12, 0.0), (sh + 0.18, -0.07), (k["l2e"] + 0.6, -0.03)],
            "head_nod": [(sh - 0.1, 0.0), (sh + 0.2, 0.04), (k["l2e"] + 0.5, 0.02)],
            "press": [(k["l2e"], 0.0), (k["l2e"] + 0.25, 0.3), (k["notice"], 0.15)],
        }))
    # notice / l03: the beam back on it: a glance down; a brow lifts a hair at "the lab I work at"
    nt = k["notice"]
    if t >= nt:
        cf_ = k["c_found"]
        look = tw(t, [(nt, (-0.85, 0.05)), (cf_ - 0.1, (-0.85, 0.05)), (cf_ + 0.08, (-0.45, 0.85)),
                      (cf_ + 0.55, (-0.45, 0.85)), (cf_ + 0.72, (-0.9, 0.0))])
        lw = k["l3_work"]
        f = addf(f, fk(t, {
            "head_nod": [(cf_, 0.0), (cf_ + 0.2, 0.08), (cf_ + 0.55, 0.08), (cf_ + 0.8, 0.0)],
            "brow_r": [(lw - 0.15, 0.0), (lw + 0.15, 0.2), (k["l3e"] + 0.5, 0.12), (k["l3b"] + 0.6, 0.05)],
            "lid": [(lw - 0.1, 0.0), (lw + 0.2, 0.04), (k["l3b"], 0.02)],
        }))
    # l03b: it presses behind his leg: he looks down at it, back up at Emb; the half-step
    if t >= k["l3b"]:
        cb0 = k["c_back0"]
        look = tw(t, [(k["l3b"], (-0.9, 0.0)), (k["l3b_that"], (-0.9, 0.0)), (k["l3b_that"] + 0.15, (-0.9, 0.12)),
                      (cb0 + 0.12, (-0.9, 0.12)), (cb0 + 0.3, (-0.25, 0.9)), (k["t_step0"] - 0.05, (-0.25, 0.9)),
                      (k["t_step0"] + 0.15, (-0.9, 0.03))])
        f = addf(f, fk(t, {
            "head_nod": [(cb0 + 0.25, 0.0), (cb0 + 0.45, 0.08), (k["t_step0"], 0.08), (k["t_step0"] + 0.3, 0.0)],
            "head_turn": [(cb0 + 0.25, 0.0), (cb0 + 0.45, 0.05), (k["t_step0"], 0.05), (k["t_step0"] + 0.3, 0.0)],
        }))
    # l03c: calm and firm, a steady look at Emb (no blinks through the line), lips set after
    if t >= k["l3c"] - 0.3:
        c0 = k["l3c"]
        f = addf(f, fk(t, {
            "brow": [(c0 - 0.3, 0.0), (c0, -0.07), (k["l3ce"] + 0.3, -0.06), (k["l3d"], 0.0)],
            "brow_ang": [(c0 - 0.3, 0.0), (c0, -0.08), (k["l3ce"] + 0.3, -0.06), (k["l3d"], 0.0)],
            "lid": [(c0 - 0.3, 0.0), (c0, -0.03), (k["l3ce"], -0.03), (k["l3d"], 0.0)],
            "head_nod": [(k["l3c_locking"] - 0.05, 0.0), (k["l3c_locking"] + 0.15, 0.05),
                         (k["l3c_locking"] + 0.45, 0.0), (k["l3c_cool"] - 0.05, 0.0),
                         (k["l3c_cool"] + 0.15, 0.05), (k["l3c_cool"] + 0.5, 0.0)],
        }))
        if c0 <= t < k["l3c_thats"]:
            d["blink"] = 0.0
            d["drift"] = False
    # l03d: softer: brows ease up, a small head tilt, the open hand (pose); eyes on Emb's face
    if t >= k["l3d"] - 0.3:
        d0 = k["l3d"]
        f = addf(f, fk(t, {
            "brow_ang": [(d0 - 0.3, 0.0), (d0 + 0.1, 0.16), (k["l3de"] + 0.3, 0.1), (k["l4"] - 0.3, 0.0)],
            "head_tilt": [(d0 - 0.3, 0.0), (d0 + 0.2, 0.05), (k["l3de"] + 0.3, 0.03), (k["l4"] - 0.3, 0.0)],
            "lid": [(d0 - 0.3, 0.0), (d0 + 0.2, 0.03), (k["l4"] - 0.3, 0.02)],
            "curve": [(k["l3d_okay"], 0.0), (k["l3d_okay"] + 0.25, 0.06), (k["l3de"] + 0.4, 0.0)],
            "press": [(k["l3de"], 0.0), (k["l3de"] + 0.3, 0.12)],
        }))
        look = tw(t, [(d0 - 0.3, (-0.9, 0.03)), (k["l4"] - 0.3, (-0.85, 0.05))])
    # converge onto the rev-2 face for l04 (head_turn -0.15, lid .02, press .12, brow_r .05)
    if t >= k["E6"]:
        u = smoothstep(seg(t, k["E6"], k["l4"] - 0.2))
        tgt = {"head_turn": -0.15, "lid": 0.02, "press": 0.12, "brow_r": 0.05}
        for key in set(f) | set(tgt):
            f[key] = lerp(f.get(key, 0.0), tgt.get(key, 0.0), u)
        look = (lerp(look[0], -0.85, u), lerp(look[1], 0.05, u))
    return look, f


def tired_rest(t, k, d, look, f):
    """l04 .. end: the rev-2 acting, unchanged."""
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
    return look, f


# =========================================================================== Embarrassment (B)
_E = {"ar_h": "grip", "ar_layer": "mid", "ar_hide": 1.0, "al_layer": "front"}


def _ep(**kw):
    d = dict(_E)
    d["base"] = "stand"
    d["al_h"] = "relaxed"
    d.update(kw)
    return d


EMB_BASE = _ep()
# (the far arm holds the torch out in front by reach: it only swings forward. The walk's back
# swing pushed that upper arm (mid layer) across his chest; the forward half is unchanged)
EMB_WALK = dict(_E, base="walk", ar_p=human.W(0.02, 0.36, 0.0, r=1))
EMB_JOLT = _ep(al_h="open", hunch=0.75, lean=-0.12, lift=14)
EMB_NERV = _ep(hunch=0.25)
EMB_WIDE = _ep(al_h="open", hunch=0.35, lean=-0.07)
EMB_HEAD = _ep(al_h="splay", hunch=0.9, lean=-0.04)
EMB_PINCH = _ep(al_h="pinch")
EMB_CUP = _ep(al_h="cup", al_tf=-1)
EMB_CUPB = _ep(al_h="cup", al_tf=-1, hunch=0.22)
EMB_POINT = _ep(al_h="point")
# rev 3
EMB_WALL = _ep(al_h="splay", lean=-0.14, chest=-0.12, neck=-0.1, hunch=0.95)   # backed flat against the wall
EMB_WJOLT = _ep(al_h="splay", lean=-0.13, chest=-0.1, hunch=1.15, lift=12)
# "Ha... ha. Cool.": the near hand behind his head, elbow out, scratching (forearm in front of
# the shoulder, the hand itself behind the head: layer mid = under the head)
EMB_HBH = _ep(**dict(human.HK("l", 95, -50, "claw", layer="mid", bend=1.0, wa=-2.0, wabs=0.7),
                     al_hy=human.W(-50.0, 5.0, 0.0), al_fing=human.W(0.3, 0.45, 0.15)),
              hunch=0.7, tilt=-0.1, period=0.42)
# on the way up / down: the hand beside the back of his head, elbow out (never across his face)
# (the near arm one layer down while it travels to / from behind his head: invisible at his side)
EMB_BASEM = _ep(al_layer="mid")
EMB_LEAN = _ep(lean=0.13, neck=0.08, hunch=0.3)                          # leaning in, squinting
EMB_LEANP = _ep(lean=0.13, neck=0.08, hunch=0.3, al_h="point")           # ... pushing his glasses up
# "We should bring it back.": points back down the tunnel (screen-left), thumb up, arm out sideways
EMB_PTB = _ep(al_p=0.4, al_o=1.15, al_e=0.42, al_eo=0.0, al_w=0.0, al_h="point", al_tf=1.0, twist=-0.12,
              hunch=0.3)
EMB_GUILT = _ep(hunch=0.5, nod=0.05)

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


def e_pos(t, k):
    """Embarrassment's ground point and scale: flat against the far wall, then (relief) two
    steps forward to his mark."""
    u = smoothstep(seg(t, k["e_step0"], k["e_step1"]))
    return lerp(XW, XE, u), lerp(YW, FY, u), lerp(SW, S, u)


def emb_aim_open(t, k):
    """Where the beam points, catch .. l03c (then the rev-2 keys take over)."""
    cr_x = cur_x(t, k)
    # shaking on the creature (his hands tremble); calmer once it's Tiredness
    tr = 1.0 - 0.75 * smoothstep(seg(t, k["e_exhale"], k["e_exhale"] + 0.6))
    shake = (22 * tr * core.noise1(t * 6.5, 31), 16 * tr * core.noise1(t * 7.3, 32))
    cre = (CC + 5 + shake[0], 1405 + shake[1])
    face = t_face(t, k)
    if t < k["swing0"]:
        return cre
    if t < k["swing1"]:
        return tuple(lerp(a, b, ease_in_out(seg(t, k["swing0"], k["swing1"]))) for a, b in zip(cre, face))
    face = (face[0] + shake[0] * 0.3, face[1] + shake[1] * 0.3)
    if t < k["c_trot0"]:
        return face
    if t < k["l2b"]:                 # follows the creature as it trots over to his leg
        p = (cr_x + 10, 1412)
        return tuple(lerp(a, b, smoothstep(seg(t, k["c_trot0"], k["c_trot0"] + 0.4))) for a, b in zip(face, p))
    if t < k["notice"]:              # distracted (hand behind his head): it droops to the floor
        return tw(t, [(k["l2b"], (CS + 10, 1412)), (k["l2b"] + 0.5, (CS - 110, 1478))])
    if t < k["c_back0"]:             # notice: onto it again
        return tw(t, [(k["notice"], (CS - 110, 1478)), (k["c_found"], (CS - 72, 1330))])
    if t < k["l3c_thats"]:           # it presses behind his leg: the beam follows its eye
        return tw(t, [(k["c_back0"], (CS - 72, 1330)), (k["c_back1"], (CUR_EYE[0] + 8, CUR_EYE[1] + 8))])
    return tw(t, [(k["l3c_thats"], (CUR_EYE[0] + 8, CUR_EYE[1] + 8)), (k["g_down"] + 0.4, (610, 1478))])


def embar_state(t, k):
    st = k["steps"]
    x, y, s = e_pos(t, k)
    d = dict(x=x, y=y, s=s, turn=0.7, pose=EMB_BASE, pose_t=None, expr="neutral", look=(0.9, 0.0),
             blink=None, blush=0.1, face={}, reach={}, drift=True, glasses_dy=0.0, glasses_tilt=0.0,
             visible=True, aim=None, rec=None, card=None, led=None, led_glow=0.55, sweat=0.0, aim_ang=0.0)
    sc = s / S
    # terrified tremble against the wall (eases off with the relief)
    trem = 1.0 - smoothstep(seg(t, k["e_exhale"], k["e_exhale"] + 0.5))
    if trem > 0:
        d["x"] = x + 1.3 * trem * math.sin(t * 43.0)
    # ---- body poses
    jt = k["jolt"]
    pose_keys = [(-1, EMB_WALL), (jt, EMB_WJOLT), (jt + 0.16, EMB_WALL),
                 (k["e_step0"] - 0.12, EMB_WALK), (k["e_step1"], EMB_BASE),
                 (k["hbh0"] - 0.3, EMB_BASEM), (k["hbh0"], EMB_HBH), (k["hbh1"], EMB_BASEM),
                 (k["hbh1"] + 0.5, EMB_BASE),
                 (k["lean0"], EMB_LEAN), (k["gl0"], EMB_LEANP), (k["gl1"], EMB_LEAN), (k["l3e"] + 0.1, EMB_BASE),
                 (k["pt0"], EMB_PTB), (k["pt1"], EMB_NERV),
                 (k["l3c_locking"], EMB_GUILT), (k["l3d"] + 0.3, EMB_NERV), (k["l4"] - 0.3, EMB_BASE),
                 (k["l5_fell"], EMB_WIDE), (k["fr_up0"], EMB_HEAD), (k["fr_dn0"], EMB_NERV),
                 (k["fr_dn1"], EMB_BASE)]
    cf = k["conflict"]
    pose_keys += [(k["r_reach"], EMB_PINCH), (k["r_grab"] + 0.15, EMB_CUP),
                  (k["r_breath"], EMB_CUPB), (k["r_breath"] + 0.55, EMB_CUP),
                  (k["r_pocket"], EMB_PINCH), (k["r_gone"] + 0.1, EMB_BASE),
                  (k["k_reach"], EMB_PINCH), (k["k_have"] + 0.1, EMB_CUP), (k["k_back"], EMB_BASE)]
    p = state_at(t, pose_keys, 0.22)
    if t < jt + 0.3 and (p[1] is EMB_WJOLT or p[0] is EMB_WJOLT):
        p = (p[0], p[1], smoothstep(seg(t, jt, jt + 0.07)) if p[1] is EMB_WJOLT else p[2])
    if p[0] is EMB_WALL and p[1] is EMB_WALK:
        p = (p[0], p[1], smoothstep(seg(t, k["e_step0"] - 0.12, k["e_step0"] + 0.15)))
    if p[1] in (EMB_HBH, EMB_BASEM) or p[0] in (EMB_HBH, EMB_BASEM):
        p = state_at(t, pose_keys, 0.3)
    if p[1] is EMB_PTB or p[0] is EMB_PTB:
        p = state_at(t, pose_keys, 0.26)
    if EMB_WALK in (p[0], p[1]):
        d["pose_t"] = max(0.0, min(t, k["e_step1"]) - k["e_step0"])     # two steps, then stands
    d["pose"] = p
    d["turn"] = tw(t, [(0.0, 0.36), (k["e_step0"], 0.4), (k["e_step1"], 0.7),
                       (cf, 0.7), (cf + 0.35, 0.55),
                       (k["press"] + 0.45, 0.55), (k["press"] + 0.75, 0.7)])
    # ---- the flashlight (far hand) and where the beam points
    floor_aim = (610, 1478)
    gdn = k["g_down"] + 0.4
    if t < gdn:
        aim = emb_aim_open(t, k)
    else:
        aim = tw(t, [(gdn, floor_aim), (k["fr_up0"], floor_aim), (k["fr_up1"], (140, 330), ease_out),
                     (k["fr_dn0"], (150, 340)), (k["fr_dn1"], floor_aim),
                     (cf, floor_aim), (cf + 0.35, (520, 1495)), (k["press"] + 0.5, (520, 1495)),
                     (k["press"] + 0.8, (470, 1498))])
    j = t - jt
    if 0 <= j < 0.6:
        aim = (aim[0], aim[1] + 34 * math.sin(j * 30) * (1 - j / 0.6) ** 2)
    head = emb_probe("head", EMB_HEAD, 0.7)
    hx0, hy0 = head["head"]
    if t < k["l4"]:
        # body-relative (S units), so it follows him off the wall
        ox, oy = tw(t, [(0.0, (100, -385)), (k["swing0"], (100, -385)), (k["swing1"], (112, -470)),
                        (k["e_step1"], (112, -478)), (k["c_trot0"], (112, -478)), (k["c_trot1"], (100, -400)),
                        (k["l2b"], (100, -400)), (k["l2b"] + 0.5, (96, -385)), (k["notice"], (96, -385)),
                        (k["c_found"], (104, -420)), (k["l3c_thats"], (104, -422)), (gdn, (98, -382))])
        hand_r = (x + ox * sc, y + oy * sc)
    else:
        hand_r = tw(t, [(k["l4"], (XE + 98, 1118)),
                        (k["fr_up0"], (XE + 100, 1125)), (k["fr_up1"], (hx0 + 62, hy0 - 112), ease_out),
                        (k["fr_dn0"], (hx0 + 62, hy0 - 112)), (k["fr_dn1"], (XE + 98, 1118)),
                        (cf, (XE + 98, 1118)), (cf + 0.35, (XE + 90, 1130))])
    gx, gy = hand_r
    if trem > 0:
        gx += 2.5 * trem * math.sin(t * 37)
        gy += 2.0 * trem * math.sin(t * 29 + 1)
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
    # ---- near hand: flat on the wall; glasses; (rev 2:) on his head, glasses, recorder, keycard
    pocket = (XE - 15 + 4, FY - 502 + 6)
    if t < k["e_exhale"] + 0.6:
        wl = 1.0 - smoothstep(seg(t, k["e_exhale"] + 0.05, k["e_exhale"] + 0.5))
        hop = 14 * bump(t, jt, jt + 0.35)
        d["reach"]["l"] = (d["x"] - 92 * sc, y - 455 * sc - hop, wl, 2.2)
    # "We should bring it back.": the point, held to a world spot so it stays in frame
    if p[1] is EMB_PTB or p[0] is EMB_PTB:
        wpt = p[2] if p[1] is EMB_PTB else 1.0 - p[2]
        d["reach"]["l"] = (XE - 168, 1036 + 4 * math.sin(t * 3.0), wpt, math.pi + 0.12)
    # the hand up to / down from behind his head along an arc out at his side (elbow out, never
    # across his face or body)
    for a0, up in ((k["hbh0"], True), (k["hbh1"], False)):
        if a0 <= t < a0 + 0.34:
            rest = emb_probe("base", EMB_BASE, 0.7)["hand_l"]
            hp_ = emb_probe("hbh", EMB_HBH, 0.7)
            top, hd_ = hp_["hand_l"], hp_["head"]
            u = smoothstep(seg(t, a0, a0 + 0.3))
            if not up:
                u = 1.0 - u
            p1 = (min(rest[0], top[0]) - 38, hd_[1] + 120)
            bx = (1 - u) ** 2 * rest[0] + 2 * u * (1 - u) * p1[0] + u * u * top[0]
            by = (1 - u) ** 2 * rest[1] + 2 * u * (1 - u) * p1[1] + u * u * top[1]
            d["reach"]["l"] = (bx, by, 1.0 - smoothstep(seg(t, a0 + 0.28, a0 + 0.34)) if up else
                               smoothstep(seg(t, a0, a0 + 0.06)) * (1.0 - smoothstep(seg(t, a0 + 0.28, a0 + 0.34))))
    if k["gl0"] - 0.05 <= t < k["gl1"] + 0.45:
        lp = emb_probe("lean", EMB_LEAN, 0.7)
        el_ = lp["eye_l"]
        gl = (el_[0] - 30, el_[1] + 14)
        p_ = tw(t, [(k["gl0"], (gl[0], gl[1] + 12)), (k["gl_push"], (gl[0], gl[1] + 6)),
                    (k["gl_push"] + 0.18, (gl[0], gl[1] - 4), ease_out), (k["gl1"], (gl[0], gl[1] - 4))])
        w_ = tw(t, [(k["gl0"], 0.0), (k["gl0"] + 0.3, 1.0, ease_out), (k["gl1"], 1.0), (k["gl1"] + 0.42, 0.0)])
        d["reach"]["l"] = (p_[0], p_[1], w_, -1.45)
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
    d["expr"] = state_at(t, [(0, "terrified"), (jt, "surprised"), (k["e_exhale"], "relieved"),
                             (k["l1_down"] + 0.5, "neutral"), (k["l2_my"] - 0.15, "surprised"),
                             (k["l2_take"] + 0.3, "neutral"), (k["l2_corp"] + 0.25, "alarmed"),
                             (k["E5c"], "frozen_shock"), (k["l2b_ha"] - 0.12, "nervous_smile"),
                             (k["notice"] + 0.1, "neutral"), (k["lean0"] + 0.1, "squint"),
                             (k["l3_lab"] - 0.05, "alarmed"), (k["l3e"] + 0.1, "neutral"),
                             (k["l3c_locking"], "guilty"), (k["l3d_save"], "sad"),
                             (k["E6"] + 0.1, "neutral"), (k["l4"] - 0.05, "curious"),
                             (k["l5"] + 0.3, "neutral"),
                             (k["l5_fell"], "surprised"), (k["l5_build"], "alarmed"),
                             (k["fr_up0"] + 0.1, "panic"), (k["l5b_what"] - 0.04, "scream"),
                             (k["l5be"] + 0.15, "frozen_shock"), (k["blink"], "deadpan"),
                             (k["led"], "neutral"), (k["led_off"] + 0.35, "deadpan"),
                             (k["l6e"] + 0.2, "neutral"), (k["E21"], "neutral"), (k["nod0"] + 0.4, "soft_smile")],
                         0.18)
    if k["E5c"] <= t < k["l2b_ha"] - 0.12:
        d["expr"] = "frozen_shock"
    d["blush"] = tw(t, [(0.0, 0.12), (jt, 0.12), (jt + 0.35, 0.45), (k["l1e"] + 0.4, 0.32),
                        (k["l2_corp"], 0.3), (k["E5c"], 0.38), (k["l2b_ha"], 0.62), (k["l2b_cool"], 0.74),
                        (k["l2be"], 0.72), (k["notice"] + 0.4, 0.5), (k["l3_lab"], 0.45), (k["l3e"], 0.42),
                        (k["l3b"], 0.36), (k["l3c_locking"], 0.42), (k["g_away"], 0.6), (k["l3d"], 0.5),
                        (k["l4"], 0.42), (k["l5"], 0.3),
                        (k["l5_build"], 0.55), (k["fr_up1"], 0.8), (k["l5b_what"], 0.92), (k["l5be"] + 0.3, 0.9),
                        (k["blink"], 0.75), (k["led"], 0.3),
                        (k["r_look_t"], 0.25), (k["r_look_t"] + 0.4, 0.6), (k["r_look_b"] + 0.2, 0.58),
                        (k["press"], 0.3), (k["l6"], 0.12), (k["E21"], 0.12)])
    d["sweat"] = tw(t, [(0.0, 0.7), (jt, 0.6), (k["l1e"], 0.15), (k["l2_corp"], 0.15), (k["E5c"] + 0.25, 0.55),
                        (k["l2b_cool"], 0.75), (k["notice"], 0.5), (k["l3e"], 0.3), (k["l3c_thats"], 0.3),
                        (k["g_away"], 0.45), (k["l4"], 0.22),
                        (k["l4e"], 0.15), (k["l5_build"], 0.3),
                        (k["fr_up1"], 0.8), (k["l5b_what"], 1.0), (k["blink"] + 0.4, 0.6), (k["led"] + 0.6, 0.0)])
    d["glasses_dy"] = tw(t, [(0.0, 3.0), (jt, 3.0), (jt + 0.06, 8.0), (jt + 0.45, 4.0), (k["l1e"], 0.0),
                             (k["lean0"], 0.0), (k["lean0"] + 0.4, 5.0), (k["gl_push"], 5.0),
                             (k["gl_push"] + 0.18, 0.0),
                             (k["l5_build"], 0.0), (k["l5_build"] + 0.12, 4.0), (k["fr_up1"], 7.0),
                             (k["l5b_what"] + 0.08, 11.0), (k["fr_glass"], 11.0), (k["fr_glass"] + 0.18, 0.0)])
    d["glasses_tilt"] = tw(t, [(0.0, 0.06), (jt, 0.06), (jt + 0.06, 0.1), (k["l1e"], 0.0),
                               (k["lean0"], 0.0), (k["lean0"] + 0.4, 0.05), (k["gl_push"], 0.05),
                               (k["gl_push"] + 0.18, 0.0),
                               (k["l5_build"], 0.0), (k["l5_build"] + 0.12, 0.12, ease_out),
                               (k["fr_up1"], 0.2), (k["l5b_what"] + 0.08, 0.3, ease_out),
                               (k["fr_glass"], 0.3), (k["fr_glass"] + 0.18, 0.0)])
    f = {}
    look = (0.9, -0.05)
    if t < k["l4"]:
        look, f = embar_opening(t, k, d)
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
        lc = k["r_look_c"]
        look = tw(t, [(led, (0.9, -0.05)), (led + 0.25, (0.9, -0.05)), (led + 0.42, (-0.2, 1.15)),
                      (k["r_up"] - 0.1, (-0.1, 1.1)), (k["r_up"] + 0.15, (0.25, 1.05)),
                      (k["r_look_t"], (0.25, 1.05)), (k["r_look_t"] + 0.15, (1.0, -0.05)),
                      (lc - 0.02, (1.0, -0.05)), (lc + 0.17, (0.62, 0.95)),          # down at the creature
                      (k["r_look_b"], (0.62, 0.95)), (k["r_look_b"] + 0.15, (0.25, 1.05)),
                      (k["press"] + 0.4, (0.25, 1.05)), (k["press"] + 0.58, (1.0, -0.05))])
        f.update(fk(t, {
            "head_nod": [(led + 0.3, 0.0), (led + 0.55, 0.2), (k["r_look_t"] + 0.1, 0.2),
                         (k["r_look_t"] + 0.3, 0.02), (lc + 0.1, 0.02), (lc + 0.32, 0.14),
                         (k["r_look_b"] + 0.1, 0.14), (k["r_look_b"] + 0.3, 0.18),
                         (k["press"] + 0.5, 0.18), (k["press"] + 0.75, 0.0)],
            "head_turn": [(k["r_look_t"] + 0.1, 0.0), (k["r_look_t"] + 0.3, 0.15),
                          (lc + 0.1, 0.15), (lc + 0.32, 0.08),
                          (k["r_look_b"] + 0.1, 0.08), (k["r_look_b"] + 0.3, 0.0)],
            "brow_ang": [(k["r_up"], 0.0), (k["r_up"] + 0.4, 0.3), (k["r_look_t"] + 0.3, 0.45),
                         (lc + 0.32, 0.56), (k["r_breath"], 0.42),
                         (k["r_breath"] + 0.5, 0.05), (k["press"] + 0.5, 0.0)],
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
    d["look"] = look
    d["face"] = f
    return d


def embar_opening(t, k, d):
    """catch .. l04: terrified at the wall; footsteps; it's Tiredness: surprise, relief; the
    creature goes over to him; "oh no, that's MY company" laugh; recognition; the company man;
    guilt; conflicted swallow. Returns (look, face deltas)."""
    st = k["steps"]
    jt = k["jolt"]
    f = {}
    # ---- catch: eyes locked on the creature (down-right), shallow fast breaths
    look = tw(t, [(0.0, (0.82, 0.55)), (st + 0.18, (0.82, 0.55)), (st + 0.32, (1.15, -0.05)),     # the steps!
                  (k["swing0"], (1.15, -0.05)), (k["swing1"], (1.05, -0.12)), (jt, (1.0, -0.1)),
                  (k["l1"], (0.95, -0.08))])
    f.update(fk(t, {
        "head_turn": [(0.0, 0.25), (st + 0.4, 0.25), (st + 0.6, 0.4), (jt + 0.2, 0.4), (k["e_step0"], 0.25),
                      (k["e_step1"], 0.0)],
        "head_nod": [(0.0, -0.06), (jt, -0.06), (k["e_exhale"], -0.04), (k["e_exhale"] + 0.25, 0.08),
                     (k["e_exhale"] + 0.6, 0.02)],
        "squash": [(jt, 0.0), (jt + 0.06, -0.08), (jt + 0.3, 0.0)],
        "brow": [(jt, 0.0), (jt + 0.1, 0.35), (k["l1e"], 0.25), (k["l1e"] + 0.5, 0.1)],
        "brow_ang": [(jt, 0.2), (jt + 0.2, 0.25), (k["l1e"] + 0.5, 0.25), (k["l2"], 0.1)],
    }))
    if t < k["e_exhale"]:
        f["head_tilt"] = 0.015 * math.sin(t * 19.0)
        f["wobble"] = 0.35
        tf_ = 1.0 - smoothstep(seg(t, jt, jt + 0.3))
        f["pupil"] = -0.32 * tf_
        f["eye_size"] = 0.1 * tf_
        f["open"] = 0.12 * tf_
        f["head_nod"] = f.get("head_nod", 0.0) + 0.012 * math.sin(t * 2 * math.pi * 2.6)
    # ---- l01: "Tiredness?!" ... relief ... "What are you doing down here?" (glance back on "down")
    if k["l1"] - 0.1 <= t < k["l2"]:
        look = tw(t, [(k["l1"] - 0.1, (0.95, -0.08)), (k["l1_down"] - 0.12, (0.95, -0.05)),
                      (k["l1_down"], (-1.25, 0.1)), (k["l1_down"] + 0.42, (-1.25, 0.1)),
                      (k["l1_down"] + 0.6, (0.95, -0.05))])
        f = addf(f, fk(t, {
            "head_turn": [(k["l1_down"] + 0.05, 0.0), (k["l1_down"] + 0.2, -0.75), (k["l1_down"] + 0.5, -0.75),
                          (k["l1_down"] + 0.72, 0.0)],
            "head_nod": [(k["l1_what"] - 0.1, 0.0), (k["l1_what"] + 0.2, 0.06), (k["l1e"], 0.04),
                         (k["l2"], 0.0)],
        }))
    # ---- l02: the creature trots over to Tiredness and sits by his leg: his eyes follow it, baffled
    if k["l2"] <= t < k["E5c"]:
        tr0, tr1 = k["c_trot0"], k["c_trot1"]
        look = tw(t, [(k["l2"], (0.95, -0.05)), (tr0 - 0.05, (0.95, -0.05)), (tr0 + 0.12, (0.7, 0.55)),
                      (tr1, (0.85, 0.6)), (k["l2_take"] + 0.3, (0.85, 0.6)), (k["l2_take"] + 0.48, (0.95, -0.06)),
                      (k["l2_corp"], (0.95, -0.06)), (k["l2_corp"] + 0.2, (0.92, 0.0))])
        f = addf(f, fk(t, {
            "brow": [(k["l2"], 0.1), (tr0 + 0.1, 0.1), (tr0 + 0.35, 0.28), (k["l2_take"] + 0.5, 0.12)],
            "brow_ang": [(k["l2"], 0.1), (k["l2_corp"], 0.12), (k["l2_corp"] + 0.3, 0.35)],
            "head_nod": [(tr0, 0.0), (tr0 + 0.3, 0.08), (k["l2_take"] + 0.4, 0.08), (k["l2_take"] + 0.65, 0.0)],
            "head_turn": [(tr0, 0.0), (tr0 + 0.3, 0.08), (k["l2_take"] + 0.4, 0.08), (k["l2_take"] + 0.65, 0.0)],
            "pupil": [(k["l2_corp"], 0.0), (k["l2_corp"] + 0.3, -0.2)],
        }))
    # ---- l02b: frozen ("oh no, that's MY company"), then the awkward laugh, hand behind his head,
    #      eyes darting; on "Cool." they slide down to the recorder in his pocket
    if k["E5c"] <= t < k["notice"] + 0.1:
        ha, ha2, c1, c2, c3, c4 = (k["l2b_ha"], k["l2b_ha2"], k["l2b_cool"], k["l2b_cool2"], k["l2b_cool3"],
                                   k["l2b_cool4"])
        look = tw(t, [(k["E5c"], (0.92, 0.0)), (ha - 0.1, (0.92, 0.0)), (ha + 0.04, (0.15, -0.15)),
                      (ha2 - 0.08, (0.15, -0.15)), (ha2 + 0.04, (1.0, -0.06)), (c1 - 0.1, (1.0, -0.06)),
                      (c1 + 0.08, (-0.3, 1.12)), (c1 + 0.5, (-0.3, 1.12)),                  # the recorder
                      (c2 + 0.08, (1.0, -0.06)), (c3 + 0.05, (0.3, -0.2)), (c4 + 0.05, (1.0, -0.06)),
                      (k["l2be"] + 0.25, (1.0, -0.06)), (k["l2be"] + 0.38, (-0.15, 0.25)),
                      (k["l2be"] + 0.75, (-0.15, 0.25)), (k["l2be"] + 0.88, (1.0, -0.06)),
                      (k["notice"], (1.0, -0.06))])
        bob = 0.0
        for tt in (c2, c3, c4):
            bob += 0.06 * bump(t, tt - 0.03, tt + 0.2)
        f = addf(f, fk(t, {
            "eye_size": [(k["E5c"], 0.06), (ha - 0.1, 0.06), (ha + 0.1, 0.02)],
            "head_nod": [(k["E5c"], 0.0), (ha - 0.15, 0.0), (ha, -0.06), (ha2 + 0.3, 0.0),
                         (c1 + 0.08, 0.12), (c1 + 0.5, 0.12), (c2 + 0.08, 0.0)],
            "head_tilt": [(ha - 0.2, 0.0), (ha + 0.1, -0.05), (k["l2be"], -0.05), (k["notice"], 0.0)],
            "brow_ang": [(k["E5c"], 0.35), (ha, 0.5), (k["notice"], 0.4)],
        }))
        f["head_nod"] = f.get("head_nod", 0.0) + bob
        if k["E5c"] <= t < ha - 0.1:
            d["blink"] = 0.0
            d["drift"] = False
    # ---- notice / l03: eyes to the creature again (connecting the dots); leans in, squints,
    #      pushes his glasses up; "...the lab I work at?" it sinks in
    if k["notice"] <= t < k["l3e"] + 0.35:
        nt = k["notice"]
        look = tw(t, [(nt, (1.0, -0.06)), (nt + 0.12, (1.0, -0.06)), (nt + 0.32, (0.78, 0.85)),
                      (k["l3_lab"], (0.78, 0.85)), (k["l3_work"] + 0.15, (0.78, 0.85)),
                      (k["l3_work"] + 0.32, (1.0, -0.05)), (k["l3e"] + 0.35, (1.0, -0.05))])
        lw = k["l3_lab"]
        f = addf(f, fk(t, {
            "brow_ang": [(nt, 0.4), (nt + 0.3, 0.05), (lw, 0.05), (lw + 0.25, 0.4)],
            "brow": [(nt, 0.0), (nt + 0.35, -0.08), (k["lean0"] + 0.3, -0.12), (lw, -0.1), (lw + 0.25, 0.18),
                     (k["l3e"] + 0.3, 0.1)],
            "lid": [(nt + 0.2, 0.0), (nt + 0.5, 0.08), (lw, 0.08), (lw + 0.2, -0.04)],
            "head_nod": [(nt + 0.2, 0.0), (nt + 0.5, 0.12), (lw + 0.1, 0.12), (k["l3e"] + 0.3, 0.02)],
            "head_turn": [(nt + 0.2, 0.0), (nt + 0.5, 0.08), (lw + 0.1, 0.08), (k["l3e"] + 0.3, 0.0)],
            "eye_size": [(lw, 0.0), (lw + 0.2, 0.06), (k["l3e"] + 0.3, 0.02)],
        }))
    # ---- l03b: nervous, well-meaning company man: a glance at it on "that"; points back down
    #      the tunnel (looks that way); Tiredness's half-step in front of it
    if k["l3e"] + 0.35 <= t < k["l3c_your"]:
        th, p0, p1 = k["l3b_that"], k["pt0"], k["pt1"]
        look = tw(t, [(k["l3e"] + 0.35, (1.0, -0.05)), (th - 0.1, (1.0, -0.05)), (th + 0.05, (0.78, 0.85)),
                      (th + 0.35, (0.78, 0.85)), (th + 0.5, (1.0, -0.05)), (p0 + 0.05, (1.0, -0.05)),
                      (p0 + 0.2, (-1.2, 0.05)), (p0 + 0.7, (-1.2, 0.05)), (p0 + 0.88, (1.0, -0.04)),
                      (k["t_step0"], (1.0, -0.04)), (k["t_step0"] + 0.2, (0.85, 0.3)),
                      (k["t_step1"] + 0.15, (1.0, -0.05))])
        f = addf(f, fk(t, {
            "brow_ang": [(k["l3b"] - 0.3, 0.1), (k["l3b"], 0.45), (k["l3be"], 0.4), (k["l3c_buddy"], 0.3)],
            "curve": [(k["l3b"] - 0.3, 0.0), (k["l3b"], 0.08), (k["l3be"], 0.06), (k["t_step0"], 0.0)],
            "head_turn": [(p0 + 0.1, 0.0), (p0 + 0.3, -0.4), (p0 + 0.75, -0.4), (p0 + 0.95, 0.0)],
            "head_nod": [(th - 0.05, 0.0), (th + 0.15, 0.08), (th + 0.45, 0.0)],
            "brow": [(k["t_step0"], 0.0), (k["t_step0"] + 0.25, 0.15), (k["l3c_buddy"] + 0.2, 0.18),
                     (k["l3c_your"], 0.1)],
        }))
    # ---- l03c: "...Your company is locking these creatures up. That's not cool." guilt: eyes
    #      down, then away (expr guilty)
    if k["l3c_your"] <= t < k["l3d"] - 0.2:
        gd, ga = k["g_down"], k["g_away"]
        look = tw(t, [(k["l3c_your"], (1.0, -0.05)), (k["l3c_locking"], (1.0, -0.05)),
                      (k["l3c_locking"] + 0.3, (0.9, 0.12)),
                      (gd - 0.05, (0.9, 0.12)), (gd + 0.15, (0.45, 1.0)), (ga - 0.05, (0.45, 1.0)),
                      (ga + 0.18, (-0.75, 0.45)), (k["l3d"] - 0.2, (-0.75, 0.45))])
        f = addf(f, fk(t, {
            "head_nod": [(gd, 0.0), (gd + 0.25, 0.1), (ga, 0.1), (ga + 0.3, 0.06)],
            "head_turn": [(ga, 0.0), (ga + 0.3, -0.16)],
            "press": [(gd, 0.0), (gd + 0.3, 0.35), (k["l3d"], 0.3)],
            "brow_ang": [(k["l3c_locking"], 0.2), (gd + 0.3, 0.42)],
        }))
    # ---- l03d: back to Tiredness, to his open hand, his face again: conflicted
    if k["l3d"] - 0.2 <= t < k["l4"]:
        d0 = k["l3d"]
        look = tw(t, [(d0 - 0.2, (-0.75, 0.45)), (d0 + 0.05, (1.0, -0.04)), (k["oh0"] + 0.45, (1.0, -0.04)),
                      (k["oh0"] + 0.6, (0.92, 0.32)), (k["l3d_okay"] - 0.1, (0.92, 0.32)),
                      (k["l3d_okay"] + 0.05, (1.0, -0.05)), (k["gulp"] + 0.3, (1.0, -0.05)),
                      (k["gulp"] + 0.48, (0.75, 0.95)), (k["l4"], (0.75, 0.95))])
        gp = k["gulp"]
        f = addf(f, fk(t, {
            "head_turn": [(d0 - 0.2, -0.16), (d0 + 0.1, 0.0), (gp + 0.35, 0.0), (gp + 0.6, 0.1)],
            "head_nod": [(d0 - 0.2, 0.06), (d0 + 0.1, 0.02), (gp - 0.05, 0.02), (gp + 0.12, 0.08),
                         (gp + 0.32, 0.02), (gp + 0.6, 0.18)],
            "press": [(d0 - 0.2, 0.3), (k["l3d_okay"], 0.42), (gp - 0.05, 0.5), (gp + 0.15, 0.1),
                      (gp + 0.5, 0.25), (k["l4"], 0.0)],
            "squash": [(gp - 0.05, 0.0), (gp + 0.1, 0.03), (gp + 0.3, 0.0)],
            "brow_ang": [(d0 - 0.2, 0.42), (k["l3d_okay"], 0.5), (gp + 0.4, 0.45), (k["l4"], 0.2)],
            "wobble": [(k["l3d_okay"], 0.0), (k["l3d_okay"] + 0.3, 0.25), (gp, 0.25), (gp + 0.3, 0.0)],
        }))
    # converge onto the rev-2 face at l04 (eyes down at it, chin down 0.18, head turned 0.1)
    u = smoothstep(seg(t, k["l4"] - 0.45, k["l4"]))
    if u > 0:
        tgt = {"head_nod": 0.18, "head_turn": 0.1}
        for key in set(f) | set(tgt):
            f[key] = lerp(f.get(key, 0.0), tgt.get(key, 0.0), u)
    return look, f


# =========================================================================== Curiosity (B)
def cur_x(t, k):
    """Curiosity's x through the opening (crouched in the beam -> by his leg -> behind it)."""
    if t < k["c_trot0"]:
        return CC
    if t < k["c_trot1"]:
        return lerp(CC, CS, seg(t, k["c_trot0"], k["c_trot1"]))
    if t < k["c_back0"]:
        return CS
    if t < k["c_back1"]:
        return lerp(CS, CH, seg(t, k["c_back0"], k["c_back1"]))
    return CH


def cur_opening(t, k, d):
    """catch .. E6: crouched and wary in Emb's beam; hears Tiredness, looks back, relief; trots
    over and sits by his leg ("my creature"); the beam finds it again; "the lab": ears sink;
    "bring it back": presses behind his leg; comforted a little by "Buddy..." / "save them"."""
    st = k["steps"]
    d["x"] = cur_x(t, k)
    d["tail_curl"] = 0.0
    d["glow"] = 0.95
    if t < k["T4"]:
        # ---- crouched low facing Emb (left), ears flat, eyes wide: wary, not aggressive
        d["flip"] = True
        cr_mix = 0.55 + 0.1 * bump(t, 0.9, 1.9)                 # shrinks a little lower as the beam jitters
        d.update(pose="crouch", pose_from="stand", pose_mix=cr_mix, expr="wide", tilt=0.1)
        d["ears"] = tw(t, [(0.0, 0.04), (k["c_ear"], 0.04), (k["c_ear"] + 0.16, 0.32, ease_out_back),
                           (k["c_relief"], 0.32), (k["c_relief"] + 0.3, 0.66, ease_out_back)])
        if t < k["c_ear"]:
            d["ears"] += 0.015 * math.sin(t * 23.0)                # a nervous quiver
            d["blink"] = 0.0                                       # eyes locked wide on him
        d["face"] = tw(t, [(k["c_look"], 1.0), (k["c_look"] + 0.3, -1.0)])
        d["look"] = tw(t, [(0.0, (-0.85, -0.4)), (k["c_look"], (-0.85, -0.4)), (k["c_look"] + 0.2, (0.85, -0.25)),
                           (k["c_relief"], (0.8, -0.45))])
        if t >= k["c_relief"]:
            d["expr"] = "hopeful"
            d["tilt"] = tw(t, [(k["c_relief"], 0.1), (k["c_relief"] + 0.3, 0.0)])
            d["tail_curl"] = tw(t, [(k["c_relief"], 0.0), (k["c_relief"] + 0.5, 0.3)])
        if t >= k["c_rise"]:
            # rise from the crouch it is holding (crouch<-stand at cr_mix == stand<-crouch at 1-cr_mix),
            # not from a full crouch: that restart was a one-frame drop just before the rise
            d.update(pose="stand", pose_from="crouch",
                     pose_mix=lerp(1.0 - cr_mix, 1.0, smoothstep(seg(t, k["c_rise"], k["c_rise"] + 0.4))))
        return
    # ---- T4 cut: it has turned to him (faces right), standing, hopeful; trots to his leg, sits
    if t < k["W5d"]:
        d["flip"] = False
        d["expr"] = "hopeful"
        d["face"] = 1.0
        d["tilt"] = 0.0
        tr0, tr1 = k["c_trot0"], k["c_trot1"]
        rate = (CS - CC) / (tr1 - tr0) / (creatures.SPEC_WALK_SPEED * SC)
        if t < tr0:
            d.update(pose="stand")
        elif t < tr1:
            d.update(pose="walk", pose_from="stand", pose_mix=seg(t, tr0, tr0 + 0.1), pose_t=(t - tr0) * rate)
        else:
            d.update(pose="sit", pose_from="walk", pose_mix=seg(t, tr1, tr1 + 0.3), pose_t=(tr1 - tr0) * rate)
        d["ears"] = tw(t, [(k["T4"], 0.66), (tr1, 0.7), (tr1 + 0.25, 0.8, ease_out_back), (k["c_emb"], 0.8),
                           (k["c_emb"] + 0.3, 0.55)])
        d["tail_curl"] = tw(t, [(k["T4"], 0.3), (tr1, 0.3), (tr1 + 0.5, 0.55), (k["c_emb"], 0.55),
                                (k["c_emb"] + 0.5, 0.3)])
        d["look"] = tw(t, [(k["T4"], (0.5, -0.8)), (tr0, (0.6, -0.4)), (tr1, (0.55, -0.85))])
        if tr1 + 0.15 <= t < k["c_emb"]:
            d["expr"] = "proud"                                    # "...my creature": that's me
        if t >= k["c_emb"]:                                        # looks back over its shoulder at Emb
            d["expr"] = "curious"
            d["face"] = tw(t, [(k["c_emb"], 1.0), (k["c_emb"] + 0.3, -1.0)])
            d["look"] = tw(t, [(k["c_emb"], (0.55, -0.85)), (k["c_emb"] + 0.2, (-0.9, -0.35))])
        return
    # ---- W5d cut: sitting by his leg facing Emb; the beam finds it; "the lab": ears sink;
    #      "bring it back": backs up behind his leg; comforted a little later
    d["flip"] = True
    d["face"] = 1.0
    cf = k["c_found"]
    cb0, cb1 = k["c_back0"], k["c_back1"]
    d["expr"] = "wide" if t < k["l3c_locking"] else "curious"
    d["ears"] = tw(t, [(k["W5d"], 0.55), (cf, 0.55), (cf + 0.25, 0.36, ease_out), (k["l3_lab"], 0.36),
                       (k["l3_lab"] + 0.25, 0.15, ease_out), (k["l3b_bring"], 0.15),
                       (k["l3b_bring"] + 0.15, 0.04, ease_out), (k["t_step1"], 0.04), (k["l3c_up"], 0.22),
                       (k["l3d"], 0.25), (k["l3d_save"] + 0.3, 0.45)])
    d["look"] = tw(t, [(k["W5d"], (-0.88, -0.42)), (k["l3c_locking"], (-0.88, -0.42)),
                       (k["l3c_locking"] + 0.2, (0.3, -1.0)), (k["l3c_up"] + 0.35, (0.3, -1.0)),
                       (k["l3c_up"] + 0.55, (-0.88, -0.45))])
    d["tilt"] = tw(t, [(k["l3_lab"], 0.0), (k["l3_lab"] + 0.3, 0.08), (cb0, 0.08), (cb1, 0.04),
                       (k["l3d"], 0.0)])
    d["glow"] = tw(t, [(cf - 0.1, 0.95), (cf + 0.05, 1.2), (cf + 0.8, 1.0)])
    if t >= cf:
        d["glint"] = cf
    rate = (CH - CS) / (cb1 - cb0) / (creatures.SPEC_WALK_SPEED * SC)
    if t < cb0:
        d.update(pose="sit")
    elif t < cb1:                                                 # backs away, still facing Emb
        if t < cb0 + 0.12:
            d.update(pose="stand", pose_from="sit", pose_mix=seg(t, cb0 - 0.04, cb0 + 0.12))
        else:
            d.update(pose="walk", pose_from="stand", pose_mix=seg(t, cb0 + 0.12, cb0 + 0.2),
                     pose_t=-(t - cb0 - 0.12) * rate * (cb1 - cb0) / (cb1 - cb0 - 0.12))
    else:
        d.update(pose="sit", pose_from="walk", pose_mix=seg(t, cb1, cb1 + 0.28),
                 pose_t=-(cb1 - cb0 - 0.12) * rate * (cb1 - cb0) / (cb1 - cb0 - 0.12))


def cur_state(t, k):
    d = dict(x=CH, pose="sit", pose_from=None, pose_mix=1.0, pose_t=None, face=1.0, expr="curious",
             ears=0.45, look=(-0.85, -0.45), tilt=0.0, tail_curl=0.0, blink=None, glow=1.0, glint=None)
    if t < k["E6"]:
        cur_opening(t, k, d)
        return d
    # ---- hiding behind his legs (peeking left at Emb), watching (rev 2 from here on)
    d["x"] = CH
    d["face"] = 1.0
    d["tail_curl"] = 0.0
    d["expr"] = "curious"
    d["ears"] = tw(t, [(k["E6"], 0.45), (k["l5b_what"], 0.45), (k["l5b_what"] + 0.12, 0.2, ease_out),
                       (k["press"] + 0.15, 0.3), (k["press"] + 0.4, 0.62, ease_out_back)])
    cr = k["l5_critter"]
    d["look"] = tw(t, [(k["E6"], (-0.85, -0.45)),
                       (cr, (-0.85, -0.45)), (cr + 0.2, (0.3, -1.0)),            # "a critter": me?
                       (cr + 0.9, (0.3, -1.0)), (cr + 1.1, (-0.85, -0.4)),
                       (k["led"] + 0.95, (-0.85, -0.4)), (k["led"] + 1.1, (-0.95, -0.55))])
    d["tilt"] = tw(t, [(cr + 0.15, 0.0), (cr + 0.35, -0.12), (cr + 0.9, -0.12), (cr + 1.1, 0.0),
                       (k["led"] + 1.05, 0.0), (k["led"] + 1.25, -0.1)])
    d["glint"] = k["c_found"]
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
MOVING = ("C1", "B2", "E3", "W5", "T5b", "W5d", "W5e", "W8", "E9", "E15", "E17", "W22")     # camera moves


def draw_B(ctx, t, k, cam, shot_name, info):
    T = tired_state(t, k)
    E = embar_state(t, k)
    Cr = cur_state(t, k)
    b_bg(ctx)
    lens = {}
    anchors = {}
    vr = view_rect(cam, pad=30)
    # the torch's spill on the wall right behind him while he is backed against it (the wall reads)
    wl = 1.0 - smoothstep(seg(t, k["e_step0"], k["e_step1"] - 0.2))
    if wl > 0.01:
        wx_, wy_, wr_ = XW + 10, YW - 330, 330
        ctx.save()
        ctx.rectangle(wx_ - wr_, wy_ - wr_, 2 * wr_, 2 * wr_)     # (keeps the group small: cheap mask)
        ctx.clip()
        ctx.push_group()
        sets.layer_blit(ctx, "s05_tunB_lit", BX0, BY0, BX1 - BX0, BY1 - BY0, b_static,
                        clip=(wx_ - wr_, wy_ - wr_, 2 * wr_, 2 * wr_))
        ctx.pop_group_to_source()
        g = cairo.RadialGradient(wx_, wy_, 0, wx_, wy_, wr_)
        g.add_color_stop_rgba(0.0, 0, 0, 0, 0.42 * wl)
        g.add_color_stop_rgba(0.5, 0, 0, 0, 0.2 * wl)
        g.add_color_stop_rgba(1.0, 0, 0, 0, 0.0)
        ctx.mask(g)
        ctx.restore()
        core.radial_glow(ctx, wx_, wy_ + 40, wr_, WARM, 0.07 * wl)
        # his shadow on the wall right behind him (light from the creature / the torch pool, low right)
        ctx.save()
        ctx.rectangle(E["x"] - 280, E["y"] - 1100 * E["s"], 460, 1150 * E["s"])
        ctx.clip()
        ctx.push_group()
        human.draw_person(ctx, "embar", E["x"] - 30, E["y"] - 16, E["s"] * 1.03, t, pose=E["pose"],
                          expr=E["expr"], look=E["look"], face=E["face"], turn=E["turn"], blink=0.0,
                          reach={kk: ((v[0] - 30, v[1] - 16) + tuple(v[2:])) for kk, v in E["reach"].items()},
                          drift=False, pose_t=E["pose_t"], shadow=False, pocket_side="near")
        sh_ = ctx.pop_group()
        ctx.set_source_rgba(0.0, 0.0, 0.02, 0.5 * wl)
        ctx.mask(sh_)
        ctx.restore()
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

    pk = tired_pocket(T, t)
    reach_t = dict(T["reach"] or {})
    if pk is not None:
        for side, tg in pk["targets"].items():
            if side in reach_t:          # a card / gesture reach on a hand leaving the pocket: blend the two
                cx_, cy_, cw_ = reach_t[side][:3]
                u_ = cw_ / max(1e-6, cw_ + tg[2])
                rt_ = (lerp(tg[0], cx_, u_), lerp(tg[1], cy_, u_), max(cw_, tg[2]))
                if len(reach_t[side]) > 3:
                    rt_ += (reach_t[side][3],)
                reach_t[side] = rt_
            else:
                reach_t[side] = tg

    def draw_tired():
        with _no_fringe_drips():
            anchors["tired"] = human.draw_person(
                ctx, "tired", T["x"], T["y"], S, t, pose=T["pose"], expr=T["expr"], look=T["look"],
                mouth=info.mouth("tired", t), face=T["face"], turn=T["turn"], blink=T["blink"],
                pose_t=T["pose_t"], reach=reach_t, drift=T["drift"], **TK)
        if pk is not None:
            pocket_overlay(ctx, T, pk, anchors["tired"])
        if T["card"]:
            hx, hy, _ = anchors["tired"]["hand_r"]
            props.keycard(ctx, hx - 6, hy - 6, 0.19, rot=tw(t, [(k["k_take"], 0.08), (k["k_take"] + 0.45, -0.18)]))

    # torch state
    pw = 1.0 if E["visible"] else 0.0
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
                      exact=shot_name not in MOVING)
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
        draw_B(ctx, t, k, cam, name, info)
    fx.vignette(ctx, 0.35, inner=0.6)


# =========================================================================== sound
def SFX(info):
    k = keys_for(info)
    ev = []
    st = k["steps"]
    # catch: pressed against the wall
    ev.append((0.12, "cloth_rustle", -13, -0.4))
    # steps: his slippers coming up the dark tunnel from the mouth (right), walk contacts every 0.5 s
    for i, g in enumerate((-17, -14, -12)):
        tt = k["t_in0"] + 0.25 + 0.5 * i
        ev.append((tt, "footstep", g, 0.55 - 0.15 * i))
    ev.append((k["c_ear"], "ears_perk", -6, -0.1))
    ev.append((k["jolt"], "cloth_rustle", -6, -0.4))
    # l01: Emb steps off the wall (two steps)
    for i in range(2):
        ev.append((k["e_step0"] + 0.25 + 0.5 * i, "footstep", -15, -0.35))
    # l02: it trots over to his leg, a happy little chitter
    ev.append((k["c_trot0"] + 0.05, "scurry", -16, 0.1))
    ev.append((k["c_trot1"] + 0.25, "creature_chitter", -14, 0.15))
    # l02b: hand up behind his head
    ev.append((k["hbh0"] + 0.08, "cloth_rustle", -13, -0.4))
    # notice / l03: the beam finds it; the glasses
    ev.append((k["c_found"] + 0.02, "critter_squeak", -12, 0.05))
    ev.append((k["gl_push"] + 0.05, "latch_click", -26, -0.4))
    # l03b: the point; it scurries behind his leg; his half-step
    ev.append((k["pt0"] + 0.1, "cloth_rustle", -12, -0.4))
    ev.append((k["c_back0"] + 0.02, "creature_chirp_sad", -15, 0.2))
    ev.append((k["c_back0"] + 0.1, "scurry", -19, 0.2))
    ev.append((k["t_step0"] + 0.3, "footstep", -15, 0.3))
    # l03d: his hand out of the pocket; Emb's swallow
    ev.append((k["oh0"] + 0.08, "cloth_rustle", -15, 0.3))
    ev.append((k["gulp"] + 0.04, "gulp", -9, -0.3))
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
